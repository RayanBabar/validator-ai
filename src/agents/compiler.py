"""
Report Compiler Agent.
Compiles standard/premium modules into a final report.
Calculates dynamic Go/No-Go score using internet research.
Includes quality verification for cross-module consistency.
Uses LLMService for LLM invocations with automatic Claude fallback.
"""

import logging

from src.agents.base import LLMService
from src.models.inputs import ValidationState
from src.utils.scoring import calculate_go_no_go_score
from src.config.prompts import COMPILER_SCORING_PROMPT, EXECUTIVE_SUMMARY_PROMPT
from src.config.constants import RESEARCH_CONTENT_LIMIT, MODULE_DATA_KEYS
from src.agents.quality_checker import (
    verify_cross_module_consistency,
    attempt_fix_for_inconsistency,
)
from src.utils.webhook import send_report_webhook
from src.agents.search.research import conduct_scoring_research
from src.models.outputs import InvestorPitchDeck, SlideContent

logger = logging.getLogger(__name__)





async def _compile_module_summaries(state: ValidationState) -> str:
    """
    Compile module summaries from state data.
    
    PERFORMANCE: Uses asyncio.gather for parallel summarization.

    Args:
        state: Current validation state with module data

    Returns:
        Formatted string of all module summaries
    """
    import asyncio
    
    # Configuration for summarization
    from src.config.prompts import EXEC_SUMMARY_MODULE_PROMPT
    from src.agents.base import LLMService

    custom_modules = state.get("custom_modules") or []

    async def summarize_module(module_key: str, data_key: str):
        """Summarize a single module (for parallel execution)."""
        if custom_modules and module_key not in custom_modules:
            return None  # Skip unselected modules
            
        data = state.get(data_key)
        if data is None:
            return None
            
        module_name = data_key.replace("_data", "").upper()
        
        try:
            data_str = str(data)
            # User Requirement: Currency is ALWAYS Euro (EUR)
            from src.config.constants import DEFAULT_CURRENCY
            currency = DEFAULT_CURRENCY
            summary = await LLMService.invoke(
                EXEC_SUMMARY_MODULE_PROMPT,
                {"module_name": module_name, "module_data": data_str, "currency": currency},
                use_complex=False,
                parse_json=False
            )
            return f"### {module_name}:\n{summary}"
        except Exception as e:
            logger.warning(f"Failed to summarize {module_name}: {e}")
            if len(data_str) > 2000:
                data_str = data_str[:2000] + "... (truncated)"
            return f"### {module_name} (Fallback):\n{data_str}"
    
    # Execute all summarizations in parallel
    tasks = [
        summarize_module(module_key, data_key)
        for module_key, data_key in MODULE_DATA_KEYS.items()
    ]
    results = await asyncio.gather(*tasks)
    
    # Filter out None results and join
    summaries = [r for r in results if r is not None]
    return "\n".join(summaries)


async def _generate_pitch_deck(report_data: object) -> InvestorPitchDeck:
    """
    Generate a 12-slide Investor Pitch Deck based on the full report data.
    """
    from src.config.prompts import PITCH_DECK_PROMPT
    
    # Serialize the report to JSON for the prompt
    # If report_data is a Pydantic model, use model_dump_json()
    if hasattr(report_data, "model_dump_json"):
        report_json = report_data.model_dump_json()
    else:
        import json
        report_json = json.dumps(report_data, default=str)

    try:
        logger.info("Generating Investor Pitch Deck (Premium Feature)...")
        deck = await LLMService.invoke_structured(
            InvestorPitchDeck,
            PITCH_DECK_PROMPT,
            {"report_json": report_json},
            use_complex=False,
            provider="openai"
        )
        return deck
    except Exception as e:
        logger.error(f"Failed to generate Pitch Deck: {e}")
        # Return empty/fallback deck structure if needed, or re-raise
        # For now, return a basic error deck to avoid crashing the whole report
        return InvestorPitchDeck(
            slides=[
                SlideContent(
                    slide_number=i+1, 
                    title="Error Generating Slide", 
                    content_bullets=["Generation failed."], 
                    visual_suggestion="None", 
                    speaker_notes="Error."
                ) for i in range(12)
            ],
            strategic_narrative="Error generation pitch deck."
        )


def _build_final_report(
    state: ValidationState,
    final_score: float,
    scores: dict,
    executive_summary: str = "",
    title: str = "Startup Idea",
) -> dict:
    """
    Build the final report structure.

    Args:
        state: Current validation state
        final_score: Calculated Go/No-Go score
        scores: Score breakdown by dimension
        executive_summary: Cohesive executive summary (5 pages)
        title: Generated title for the business idea

    Returns:
        Complete report dictionary
    """
    return {
        "tier": state["inputs"].tier,
        "title": title,
        "go_no_go_score": final_score,
        "score_breakdown": scores,
        "executive_summary": executive_summary,
        "executive_summary": executive_summary,
        "modules": _filter_modules_for_tier(state, {
            "business_model_canvas": state.get("bmc_data"),
            "market_analysis": state.get("market_data"),
            "competitive_intelligence": state.get("competitor_data"),
            "financials": state.get("financial_data"),
            "technical_requirements": state.get("tech_data"),
            "regulatory": state.get("reg_data"),
            "gtm_strategy": state.get("gtm_data"),
            "risks": state.get("risk_data"),
            "roadmap": state.get("roadmap_data"),
            "funding": state.get("funding_data"),
        }),
    }

def _filter_modules_for_tier(state: ValidationState, all_modules: dict) -> dict:
    """Filter modules based on tier and requested custom modules."""
    tier = state["inputs"].tier
    
    custom_modules = state.get("custom_modules")
    if not custom_modules:
        return all_modules
    
    # helper map: internal module key -> node name
    # We need to control what shows up based on "custom_modules" list which contains node names like "mod_bmc"
    # But here we have report keys like "business_model_canvas"
    
    # Map report keys to node names
    report_key_to_node = {
        "business_model_canvas": "mod_bmc",
        "market_analysis": "mod_market",
        "competitive_intelligence": "mod_comp",
        "financials": "mod_finance",
        "technical_requirements": "mod_tech",
        "regulatory": "mod_reg",
        "gtm_strategy": "mod_gtm",
        "risks": "mod_risk",
        "roadmap": "mod_roadmap",
        "funding": "mod_funding"
    }
    
    custom_modules = state.get("custom_modules") or []
    filtered = {}
    
    for report_key, data in all_modules.items():
        node_name = report_key_to_node.get(report_key)
        if node_name and node_name in custom_modules:
            filtered[report_key] = data
        else:
            # Explicitly exclude if not requested
            filtered[report_key] = None
            
    return filtered


async def compile_standard_report(state: ValidationState) -> dict:
    """
    Compile the final report from all standard modules.

    Uses:
    1. Module summaries from all 10 standard modules
    2. Fresh internet research for data-driven Go/No-Go scoring
    3. OpenAI with Claude fallback
    4. Auto-fix loop for cross-module consistency

    Args:
        state: Current validation state with all module data

    Returns:
        Dictionary with final_report containing complete analysis
    """
    logger.info("Compiling Standard/Premium Report")

    desc = state["inputs"].detailed_description

    # === QUALITY VERIFICATION & AUTO-FIX ===
    logger.info("Conducting quality verification and auto-fix loop")

    # SKIP FOR CUSTOM TIER to save time/cost
    if state["inputs"].tier == "custom":
        logger.info("Custom tier detected: Skipping cross-module consistency checks for performance.")
    else:
        # Map simple names to state keys for fixing e.g. "Market" -> "market_data"
        simple_to_key = {v.replace("_data", ""): v for k, v in MODULE_DATA_KEYS.items()}
        # Robust mappings for LLM variations
        simple_to_key.update({
            "Customer": "bmc_data",
            "Financials": "financial_data",
            "Competition": "competitor_data", 
            "Competitors": "competitor_data",
            "Market": "market_data",
            "Tech": "tech_data",
            "Risks": "risk_data"
        })

        # PERFORMANCE: Single pass - consistency checks are expensive
        # (each attempt = 10+ parallel LLM calls + 1 check + 2 fix calls)
        for attempt in range(1):
            # 1. Gather modules
            modules_for_check = {
                key.replace("_data", ""): state.get(key)
                for key in MODULE_DATA_KEYS.values()
                if state.get(key)
            }
            
            # If custom modules selected, filter the check list to ONLY selected modules
            # This prevents checking against stale data in the state from previous runs
            custom_modules = state.get("custom_modules")
            if custom_modules:
                # Helper: map friendly name (Market) to node name (mod_market)
                # We need to filter `modules_for_check` where keys are like "market", "financial"
                # But `custom_modules` has "mod_market"
                # Reverse lookup or direct check if we have the mapping
                
                # Simplified filter: Check if the data key's corresponding node is in custom_modules
                filtered_check = {}
                for simple_name, content in modules_for_check.items():
                    # Find the data key for this simple name
                    data_key = simple_to_key.get(simple_name)
                    # report_key_map maps data_key -> node_name directly (e.g., "bmc_data" -> "mod_bmc")
                    report_key_map = {v: k for k, v in MODULE_DATA_KEYS.items()}  # data_key -> node_name
                    
                    if data_key:
                        node_name = report_key_map.get(data_key)  # e.g., "bmc_data" -> "mod_bmc"
                        
                        if node_name and node_name in custom_modules:
                            filtered_check[simple_name] = content
                
                modules_for_check = filtered_check

            # SKIP if fewer than 2 modules (cannot have inconsistency with 1 module)
            if len(modules_for_check) < 2:
                logger.info(f"Skipping consistency check: too few modules selected ({len(modules_for_check)})")
                break
            # Add derived modules
            if state.get("bmc_data"):
                modules_for_check["Customer"] = state["bmc_data"].get("customer_segments")

            # 2. Verify
            try:
                consistency_check = await verify_cross_module_consistency(
                    description=desc, modules=modules_for_check
                )

                if consistency_check.get("pass", False):
                    logger.info(f"Consistency check passed on attempt {attempt + 1}!")
                    break

                # 3. Fix
                inconsistencies = consistency_check.get("inconsistencies", [])
                if not inconsistencies:
                    break

                logger.info(
                    f"Attempt {attempt + 1}: Found {len(inconsistencies)} inconsistencies. Attempting fixes..."
                )

                # Take the first 2 inconsistencies to fix (don't try all at once)
                fixes_applied = 0
                for issue in inconsistencies[:2]:
                    fix_result = await attempt_fix_for_inconsistency(
                        description=desc, inconsistency=issue, all_modules=modules_for_check
                    )

                    if fix_result:
                        target_mod = fix_result["target_module"]
                        fixed_content = fix_result["fixed_content"]

                        # Update state
                        state_key = simple_to_key.get(target_mod)
                        if state_key:
                            if target_mod == "Customer" and state_key == "bmc_data":
                                # Specific patch for BMC customer segments
                                if state.get("bmc_data"):
                                    state["bmc_data"]["customer_segments"] = fixed_content
                                    fixes_applied += 1
                            elif state_key in state:
                                # Full module aupdate
                                state[state_key] = fixed_content
                                fixes_applied += 1
                                logger.info(f"Applied fix to {state_key}")

                if fixes_applied == 0:
                    logger.info("No fixes could be applied, stopping loop.")
                    break

            except Exception as e:
                logger.warning(f"Verification loop check failed: {e}")
                break

    # Gather module summaries (re-compile after fixes)
    module_summaries = await _compile_module_summaries(state)

    # Conduct fresh internet research for scoring
    # CHECK FOR PERSISTED SCORE & RESEARCH
    stored_score = state.get("stored_go_no_go_score")
    stored_breakdown = state.get("stored_score_breakdown")
    stored_research = state.get("stored_scoring_research")

    scoring_research = {}
    
    if stored_score is not None and stored_breakdown and stored_research:
        logger.info("Using persisted Go/No-Go score and research (skipping fresh analysis)")
        scoring_research = stored_research
        final_score = stored_score
        adjusted_scores = stored_breakdown
    else:
        # COST OPTIMIZATION: Reuse comprehensive_research if available (eliminates 20+ Tavily calls)
        comprehensive = state.get("comprehensive_research")
        if comprehensive:
            logger.info(f"Reusing comprehensive research for scoring ({len(comprehensive)} chars)")
            # Extract scoring-relevant context from comprehensive research
            scoring_research = {
                "market_demand": comprehensive[:2000] if len(comprehensive) > 2000 else comprehensive,
                "competition": comprehensive[2000:4000] if len(comprehensive) > 4000 else comprehensive,
                "timing": comprehensive[4000:6000] if len(comprehensive) > 6000 else comprehensive,
                "regulatory": comprehensive[6000:8000] if len(comprehensive) > 8000 else comprehensive,
                "scalability": comprehensive[8000:10000] if len(comprehensive) > 10000 else comprehensive,
            }
        else:
            logger.info("Comprehensive research not found, conducting internet research for Go/No-Go scoring")
            scoring_research = await conduct_scoring_research(state)

        # Gather interview Q&A data from state for more informed analysis
        questions_asked = state.get("questions_asked", [])
        user_answers = state.get("user_answers", [])
        qa_pairs = (
            "\n".join(
                [
                    f"Q{i + 1}: {q}\nA{i + 1}: {a}"
                    for i, (q, a) in enumerate(zip(questions_asked, user_answers))
                ]
            )
            if questions_asked
            else "No interview Q&A available"
        )

        # Format research for prompt (includes interview data)
        research_context = f"""
    FOUNDER INTERVIEW INSIGHTS:
    {qa_pairs}
    
    LIVE MARKET RESEARCH (from Internet):
    - Market Demand Signals: {scoring_research.get("market_demand", "N/A")}
    - Competitive Landscape: {scoring_research.get("competition", "N/A")}
    - Timing & Trends: {scoring_research.get("timing", "N/A")}
    - Regulatory Environment: {scoring_research.get("regulatory", "N/A")}
    - Scalability Indicators: {scoring_research.get("scalability", "N/A")}
    """

        # Prepare strategic directive string or default
        strat_dir_obj = state.get("strategic_directive")
        if strat_dir_obj:
            strat_txt = f"Strategic Decisions:\n- Pricing: {strat_dir_obj.pricing_strategy}\n- Target: {strat_dir_obj.target_customer_segment}\n- Constraints: {', '.join(strat_dir_obj.key_strategic_constraints)}"
        else:
            strat_txt = "No specific strategic directive provided. Rely on research context."

        invoke_args = {
            "title": desc,  # LLM will extract/generate title from description
            "summaries": module_summaries,
            "research_context": research_context,
            "geography": state.get("extracted_geography", "Global"),
            "industry": state.get("extracted_industry", ""),
            "regulatory_context": state.get(
                "extracted_regulatory_context", "general compliance"
            ),
            "strategic_directive": strat_txt
        }

        # Use LLMService for scoring with automatic fallback
        scores = await LLMService.invoke(
            COMPILER_SCORING_PROMPT,
            invoke_args,
            use_complex=False,
            parse_json=True,
            provider="openai",  # Use fast model only
        )

        final_score, adjusted_scores = calculate_go_no_go_score(scores)
        logger.info(f"Go/No-Go score calculated: {final_score}")

    # Ensure research_context is available for Executive Summary even if we skipped scoring
    if not 'research_context' in locals():
         # Re-construct context for Executive Summary if we skipped scoring block
         # (We need the QA pairs again)
        questions_asked = state.get("questions_asked", [])
        user_answers = state.get("user_answers", [])
        qa_pairs = (
            "\n".join(
                [
                    f"Q{i + 1}: {q}\nA{i + 1}: {a}"
                    for i, (q, a) in enumerate(zip(questions_asked, user_answers))
                ]
            )
            if questions_asked
            else "No interview Q&A available"
        )
        research_context = f"""
    FOUNDER INTERVIEW INSIGHTS:
    {qa_pairs}
    
    LIVE MARKET RESEARCH (from Internet):
    - Market Demand Signals: {scoring_research.get("market_demand", "N/A")}
    - Competitive Landscape: {scoring_research.get("competition", "N/A")}
    - Timing & Trends: {scoring_research.get("timing", "N/A")}
    - Regulatory Environment: {scoring_research.get("regulatory", "N/A")}
    - Scalability Indicators: {scoring_research.get("scalability", "N/A")}
    """

    # Generate Executive Summary for cohesive report flow
    logger.info("Generating Executive Summary for report cohesion")
    exec_summary_args = {
        "title": desc,
        "go_no_go_score": final_score,
        "module_summaries": module_summaries,
        "research_context": research_context,
        "geography": state.get("extracted_geography", "Global"),
        "currency": "EUR", # DEFAULT_CURRENCY import might be needed or just string
    }

    try:
        # Use LLMService for executive summary with automatic fallback
        executive_summary = await LLMService.invoke(
            EXECUTIVE_SUMMARY_PROMPT,
            exec_summary_args,
            use_complex=False,
            parse_json=True,
            provider="openai",  # Use fast model only
        )
    except Exception as exec_error:
        logger.warning(f"Executive summary generation failed: {exec_error}")
        # Schema-compliant fallback
        executive_summary = {
            "business_opportunity": {
                "problem_summary": "Summary generation failed.",
                "solution_overview": f"Analysis for startup idea",
                "target_market": "See detailed market analysis.",
                "value_proposition": "See detailed modules.",
            },
            "market_insights": {
                "market_opportunity": "See market analysis module.",
                "competitive_landscape": "See competitor intelligence module.",
                "key_differentiators": ["See details in report"],
            },
            "financial_execution": {
                "revenue_model": "See financial feasibility module.",
                "financial_projections": "See financial feasibility module.",
                "critical_milestones": ["See implementation roadmap"],
            },
            "recommendation": {
                "go_no_go_verdict": "Review Data",
                "rating_justification": f"Go/No-Go Score: {final_score}/100",
                "immediate_action_items": ["Review detailed report modules"],
            },
        }

    logger.info(f"Executive summary generated (structured object)")

    # Use title from state (generated in free tier)
    generated_title = state.get("generated_title") or "Startup Idea"

    # Build report structure with executive summary and title (using adjusted integer scores)
    report = _build_final_report(
        state, final_score, adjusted_scores, executive_summary, title=generated_title
    )

    # 6. Generate Pitch Deck (Optional Custom Module or Premium Tier)
    # Check if 'investor_pitch_deck' is in custom_modules OR if tier is 'premium'
    custom_modules = state.get("custom_modules") or []
    
    if "investor_pitch_deck" in custom_modules or state["inputs"].tier == "premium":
        pitch_deck = await _generate_pitch_deck(report)
        report["investor_pitch_deck"] = pitch_deck.model_dump()

    # Send webhook with report data
    thread_id = state.get("thread_id")
    if thread_id:
        await send_report_webhook(
            thread_id=thread_id, report_score=final_score, report_metadata=report
        )

    return {
        "final_report": report,
        "stored_go_no_go_score": final_score,
        "stored_score_breakdown": adjusted_scores,
        "stored_scoring_research": scoring_research
    }


async def admin_approval_node(state: ValidationState) -> dict:
    """
    Admin approval placeholder node.

    Sets workflow phase to waiting for admin review.

    Args:
        state: Current validation state

    Returns:
        Updated state with workflow_phase set to waiting_for_admin
    """
    logger.info("Report ready for admin approval")
    return {"workflow_phase": "waiting_for_admin"}
