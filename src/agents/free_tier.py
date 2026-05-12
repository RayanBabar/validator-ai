"""
Free Tier Node Logic.
Generates a quick 5-dimension viability score report.
Uses LLMService for LLM invocations with automatic Claude fallback.
"""

import logging

from src.agents.base import LLMService
from src.models.inputs import ValidationState
from src.models.outputs import FreeReportOutput, ViabilityScores
from src.utils.scoring import (
    calculate_viability_score,
    get_package_recommendation,
    get_gauge_status,
)
from src.utils.date_utils import get_current_date
from src.config.prompts import FREE_TIER_VIABILITY_PROMPT

logger = logging.getLogger(__name__)


async def free_tier_scan(state: ValidationState) -> dict:
    """
    Generate 5-dimension viability score and free report.

    Uses LLMService with automatic Claude fallback.

    Args:
        state: Current validation state with inputs and context

    Returns:
        Dictionary with final_report containing FreeReportOutput data
    """
    logger.info("Starting free tier viability scan")

    desc = state["inputs"].detailed_description

    # Format Q&A history if available
    questions = state.get("questions_asked", [])
    answers = state.get("user_answers", [])

    qa_history = "No interview conducted."
    if questions and answers:
        qa_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])

    # Append synthesized context if available
    enriched_ctx = state.get("enriched_context", "")
    if enriched_ctx:
        qa_history += f"\n\nSYNTHESIZED INTELLIGENCE:\n{enriched_ctx}"

    # Extract dynamic context for scoring (now available after synthesis fix)
    geography = state.get("extracted_geography", "global market")
    industry = state.get("extracted_industry", "")
    regulatory_context = state.get("extracted_regulatory_context", "general compliance")

    # User Requirement: Currency is ALWAYS Euro (EUR)
    from src.config.constants import DEFAULT_CURRENCY
    currency = DEFAULT_CURRENCY

    invoke_args = {
        "title": desc,
        "desc": qa_history,
        "context": state.get("search_context", ""),
        "current_date": get_current_date(),
        "currency": currency,
        "geography": geography,
        "industry": industry,
        "regulatory_context": regulatory_context,
    }

    # Use LLMService with automatic fallback
    res = await LLMService.invoke(
        FREE_TIER_VIABILITY_PROMPT,
        invoke_args,
        use_complex=False,
        parse_json=True,
        provider="claude",
    )

    # Get interview quality scores from state (set by researcher after interview)
    clarity_score = state.get("clarity_score")
    answer_quality_score = state.get("answer_quality_score")
    dimension_quality = state.get(
        "dimension_quality",
        {
            "problem_understanding": 5.0,
            "market_knowledge": 5.0,
            "competitive_awareness": 5.0,
            "execution_readiness": 5.0,
            "founder_credibility": 5.0,
        },
    )

    # Add context specificity to dimension quality for scoring penalty
    dimension_quality["context_specificity_score"] = float(
        state.get("context_specificity_score", 5.0)
    )

    # Calculate viability score and get adjusted integer scores
    score, adjusted_scores = calculate_viability_score(
        res["scores"],
        clarity_score=clarity_score,
        answer_quality_score=answer_quality_score,
        dimension_quality=dimension_quality,
    )
    package_rec = get_package_recommendation(score)
    gauge_status = get_gauge_status(score)

    # Extract the generated title from LLM response (to be used by all other tiers)
    generated_title = res.get("startup_title", "Startup Idea")

    logger.info(
        f"Free tier scan complete: score={score}, recommendation={package_rec}, title={generated_title}"
    )

    # --- Key aliasing: handle LLM variations ---
    # Some models return "value_proposition" instead of "value_prop", etc.
    value_prop = (
        res.get("value_prop")
        or res.get("value_proposition")
        or res.get("killer_value_proposition")
        or ""
    )
    customer_profile = (
        res.get("customer_profile")
        or res.get("ideal_customer")
        or res.get("target_customer")
        or ""
    )
    what_if_scenario = (
        res.get("what_if_scenario")
        or res.get("pivot_scenario")
        or res.get("scenario_analysis")
        or ""
    )
    personalized_next_step = (
        res.get("personalized_next_step")
        or res.get("next_step")
        or res.get("recommended_action")
        or ""
    )

    # Log any missing fields so we can debug model responses
    missing = [k for k, v in {
        "value_prop": value_prop,
        "customer_profile": customer_profile,
        "what_if_scenario": what_if_scenario,
        "personalized_next_step": personalized_next_step,
    }.items() if not v]
    if missing:
        logger.warning(f"Free tier LLM response missing fields: {missing}. Raw keys: {list(res.keys())}")

    report = FreeReportOutput(
        tier="free",
        title=generated_title,
        viability_score=score,
        gauge_status=gauge_status,
        scores=ViabilityScores(**adjusted_scores),  # Use adjusted integer scores
        value_proposition=value_prop or "Value proposition not generated — please re-run.",
        customer_profile=customer_profile or "Customer profile not generated — please re-run.",
        what_if_scenario=what_if_scenario or "Scenario analysis not generated — please re-run.",
        package_recommendation=package_rec,
        personalized_next_step=personalized_next_step or "Begin market validation with 5 customer interviews.",
    )

    # Send webhook with report data
    thread_id = state.get("thread_id")
    if thread_id:
        from src.utils.webhook import send_report_webhook
        from src.utils.supabase import update_session_status
        
        await send_report_webhook(
            thread_id=thread_id, report_score=score, report_metadata=report.model_dump()
        )
        await update_session_status(thread_id, "free_report_ready")

    # Return both the report and the generated title (stored in state for other tiers)
    return {"final_report": report.model_dump(), "generated_title": generated_title}
