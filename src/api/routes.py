from __future__ import annotations
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from uuid import uuid4
from typing import Dict, Any, List, Union
import logging
import json
from src.models.inputs import (
    StartupSubmission,
    AdminUpdate,
    SubmitInput,
    AnswerInput,
    UpgradeInput,
)
from src.models.outputs import (
    FreeReportOutput,
    BasicReportOutput,
    StandardReportOutput,
    PremiumReportOutput,
)
from src.api.middleware import limiter
from src.config.constants import MAX_INTERVIEW_QUESTIONS, STANDARD_MODULE_NAMES
from src.utils.webhook import send_report_webhook
import src.graph.workflow as wf_module

validation = APIRouter(tags=["Validation"])
logger = logging.getLogger(__name__)

# ============================================
# PHASE 1: SUBMIT (Start Interview)
# ============================================


@validation.post("/submit")
@limiter.limit("10/minute")
async def submit_idea(request: Request, payload: SubmitInput):
    """
    Start the validation journey.
    Returns first clarifying question from the interview agent.
    """
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "inputs": StartupSubmission(
            detailed_description=payload.detailed_description,
            tier="free",
        ),
        "thread_id": thread_id,
        "interview_phase": "asking",
        "questions_asked": [],
        "user_answers": [],
        "workflow_phase": "interview",
        "error": False,
        "error_message": None,
        "error_node": None,
    }

    try:
        async for _ in wf_module.app_graph.astream(initial_state, config):
            pass
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Submit failed for {thread_id}: {error_msg}")
        return {
            "thread_id": thread_id,
            "status": "failed",
            "error": error_msg,
        }

    snapshot = await wf_module.app_graph.aget_state(config)
    state = snapshot.values

    return {
        "thread_id": thread_id,
        "status": "question_pending",
        "question": state.get("current_question"),
        "question_number": len(state.get("questions_asked", [])),
        "questions_remaining": MAX_INTERVIEW_QUESTIONS - len(state.get("questions_asked", [])),
    }


# ============================================
# PHASE 1: SUBMIT ANSWER
# ============================================


@validation.post("/answer/{thread_id}")
@limiter.limit("30/minute")
async def submit_answer(request: Request, thread_id: str, payload: AnswerInput, bg_tasks: BackgroundTasks):
    """
    Submit answer to clarifying question.
    Returns next question or shows interview complete (free tier runs in background).
    """
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await wf_module.app_graph.aget_state(config)

    if not snapshot.values:
        raise HTTPException(404, "Journey not found")

    state = snapshot.values
    user_answers = state.get("user_answers", [])
    user_answers.append(payload.answer)

    try:
        # Update state with the new answer
        await wf_module.app_graph.aupdate_state(
            config, {"user_answers": user_answers}, as_node="process_answer"
        )

        # Stream through interviewer node only (will stop at END if more questions needed)
        async for _ in wf_module.app_graph.astream(None, config):
            pass
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Answer processing failed for {thread_id}: {error_msg}")
        try:
            await wf_module.app_graph.aupdate_state(
                config,
                {
                    "error": True,
                    "error_message": error_msg,
                    "error_node": "answer_processing",
                    "workflow_phase": "failed",
                },
                as_node="process_answer",
            )
        except Exception:
            pass
        return {
            "thread_id": thread_id,
            "status": "failed",
            "error": error_msg,
        }

    new_snapshot = await wf_module.app_graph.aget_state(config)
    new_state = new_snapshot.values

    # Check if workflow encountered an error
    if new_state.get("error"):
        return {
            "thread_id": thread_id,
            "status": "failed",
            "error": new_state.get("error_message", "An unknown error occurred"),
        }

    # Check if interview is now complete
    if new_state.get("interview_phase") == "complete":
        if new_snapshot.next:
            return {
                "thread_id": thread_id,
                "status": "interview_complete",
                "message": "Interview complete. Generating your free viability report...",
                "poll_endpoint": f"/report/{thread_id}",
            }
        else:
            return {
                "thread_id": thread_id,
                "status": "free_report_ready",
                "message": "Your free viability report is ready!",
                "report_endpoint": f"/report/{thread_id}",
            }
    else:
        return {
            "thread_id": thread_id,
            "status": "question_pending",
            "question": new_state.get("current_question"),
            "question_number": len(new_state.get("questions_asked", [])),
            "questions_remaining": MAX_INTERVIEW_QUESTIONS - len(new_state.get("questions_asked", [])),
        }


# ============================================
# PHASE 3: UPGRADE
# ============================================


@validation.post("/upgrade/{thread_id}")
@limiter.limit("5/minute")
async def upgrade_tier(
    request: Request, thread_id: str, payload: UpgradeInput, bg_tasks: BackgroundTasks
):
    """
    Upgrade to paid tier and trigger deep analysis.
    """
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await wf_module.app_graph.aget_state(config)

    if not snapshot.values:
        raise HTTPException(404, "Journey not found")

    state = snapshot.values

    valid_tiers = ["basic", "standard", "premium", "custom"]
    if payload.tier not in valid_tiers:
        raise HTTPException(400, f"Invalid tier. Must be one of: {valid_tiers}")

    # Validate custom modules if provided
    if payload.custom_modules:
        invalid_modules = [m for m in payload.custom_modules if m not in STANDARD_MODULE_NAMES and m != "investor_pitch_deck"]
        if invalid_modules:
             raise HTTPException(400, f"Invalid custom modules: {invalid_modules}. Must be one of: {STANDARD_MODULE_NAMES + ['investor_pitch_deck']}")

    inputs = state.get("inputs")
    if inputs:
        updated_inputs = StartupSubmission(
            detailed_description=inputs.detailed_description,
            tier=payload.tier,
            custom_modules=payload.custom_modules
        )

        update_payload = {
            "inputs": updated_inputs, 
            "workflow_phase": "paid_analysis", 
            "error": False, 
            "error_message": None
        }
        
        if payload.custom_modules:
            logger.info(f"Custom modules selected for {payload.tier} tier: {payload.custom_modules}")
            update_payload["custom_modules"] = payload.custom_modules

        await wf_module.app_graph.aupdate_state(
            config,
            update_payload,
            as_node="research",
        )

    async def run_paid_workflow():
        try:
            async for _ in wf_module.app_graph.astream(None, config):
                pass
        except Exception as e:
            # Capture error in state
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Paid workflow failed for {thread_id}: {error_msg}")
            try:
                await wf_module.app_graph.aupdate_state(
                    config,
                    {
                        "error": True,
                        "error_message": error_msg,
                        "error_node": "paid_workflow",
                        "workflow_phase": "failed",
                    },
                    as_node="research",
                )
            except Exception as update_error:
                logger.error(f"Failed to update error state: {update_error}")
            
            # Send failure webhook notification
            try:
                await send_report_webhook(
                    thread_id=thread_id,
                    report_score=0.0,
                    report_metadata={"error": error_msg}
                )
            except Exception as webhook_error:
                logger.error(f"Failed to send failure webhook for {thread_id}: {webhook_error}")

    bg_tasks.add_task(run_paid_workflow)

    return {
        "thread_id": thread_id,
        "status": "upgrade_initiated",
        "tier": payload.tier,
        "message": f"Deep analysis started for {payload.tier} tier. Poll /report/{thread_id} for results.",
    }


# ============================================
# REPORT ENDPOINT
# ============================================


class ReportResponse(BaseModel):
    """Response model for report endpoint with typed report_data"""

    thread_id: str
    status: str
    tier: str
    interview_summary: Dict[str, Any]
    report_data: Union[
        FreeReportOutput,
        BasicReportOutput,
        StandardReportOutput,
        PremiumReportOutput,
        Dict[str, Any],
        None,
    ]
    error: Union[str, None] = None  # Error message if status is 'failed'


@validation.get("/report/{thread_id}")
async def get_report(thread_id: str) -> ReportResponse:
    """Get current report status and data."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await wf_module.app_graph.aget_state(config)

    if not snapshot.values:
        raise HTTPException(404, "Report not found")

    state = snapshot.values
    inputs = state.get("inputs")
    tier = inputs.tier if inputs else "free"

    # Check for error state first
    if state.get("error"):
        return {
            "thread_id": thread_id,
            "status": "failed",
            "tier": tier,
            "interview_summary": {
                "questions_asked": len(state.get("questions_asked", [])),
                "interview_complete": state.get("interview_phase") == "complete",
            },
            "report_data": state.get("final_report"),
            "error": state.get("error_message", "An unknown error occurred"),
        }

    status = "processing"

    if not snapshot.next:
        if tier == "free" and state.get("final_report"):
            status = "free_report_complete"
        elif state.get("final_report"):
            status = "completed"
        else:
            status = "paused_for_upgrade"
    elif "admin_approve" in snapshot.next:
        status = "waiting_for_admin"

    return {
        "thread_id": thread_id,
        "status": status,
        "tier": tier,
        "interview_summary": {
            "questions_asked": len(state.get("questions_asked", [])),
            "interview_complete": state.get("interview_phase") == "complete",
        },
        "report_data": state.get("final_report"),
        "error": None,
    }


# ============================================
# ADMIN APPROVAL
# ============================================


@validation.post("/admin/approve/{thread_id}")
async def admin_approve(thread_id: str, payload: AdminUpdate = None):
    """Admin reviews and approves the final report."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await wf_module.app_graph.aget_state(config)

    if not snapshot.next:
        return {"status": "error", "message": "Workflow not active or already finished"}

    current_node = list(snapshot.next)[0]

    if payload and payload.edited_report:
        await wf_module.app_graph.aupdate_state(
            config, {"final_report": payload.edited_report}, as_node=current_node
        )

    async for _ in wf_module.app_graph.astream(None, config):
        pass

    return {
        "status": "approved",
        "message": f"Report finalized from node '{current_node}'. View at /report/{thread_id}",
    }


# ============================================
# HTML GENERATION
# ============================================

# HTML GENERATION
# ============================================

templates = Jinja2Templates(directory="src/templates")

def replace_em_dashes(obj):
    """Recursively replace em dashes with regular dashes in all strings."""
    if isinstance(obj, str):
        return obj.replace('—', ' - ').replace('–', ' - ')
    elif isinstance(obj, dict):
        return {k: replace_em_dashes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_em_dashes(item) for item in obj]
    return obj

@validation.post("/generate-html", response_class=HTMLResponse)
async def generate_html_report(request: Request, payload: Dict[str, Any]):
    """
    Convert JSON report data to HTML.
    Payload should match the JSON returned by /report/{thread_id}.
    """
    cleaned_payload = replace_em_dashes(payload)
    return templates.TemplateResponse("report.html", {"request": request, "data": cleaned_payload})

# Rebuild model to ensure forward references (like recursive Union types) are resolved
ReportResponse.model_rebuild()
