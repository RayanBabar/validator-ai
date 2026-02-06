"""
Basic Tier Agent.
Generates an 8-dimension Go/No-Go analysis with Business Model Canvas.
Uses LLMService for LLM invocations with automatic Claude fallback.
"""

import logging

from src.agents.base import LLMService
from src.models.inputs import ValidationState
from src.models.outputs import (
    BasicReportOutput,
    BusinessModelCanvas,
    BasicTierGeneration,
    GoNoGoScores,
)
from src.utils.scoring import calculate_go_no_go_score
from src.config.prompts import BASIC_BMC_PROMPT, BASIC_EXEC_SUMMARY_PROMPT
from src.utils.webhook import send_report_webhook
from src.config.constants import DEFAULT_CURRENCY
from src.agents.search.research import conduct_scoring_research

logger = logging.getLogger(__name__)


async def basic_tier_gen(state: ValidationState) -> dict:
    """
    Generate Basic Tier Go/No-Go report using 3-step sequential flow:
    1. Business Model Canvas (BMC)
    2. Unified Scoring (using COMPILER_SCORING_PROMPT)
    3. Executive Summary

    Args:
        state: Current validation state

    Returns:
        Dictionary with final_report containing BasicReportOutput data
    """
    logger.info("Starting Basic Tier sequential analysis")

    # 1. SETUP CONTEXT
    desc = state["inputs"].detailed_description
    title = state.get("generated_title") or "Startup Idea"
    geography = state.get("extracted_geography", "global market")
    industry = state.get("extracted_industry", "")
    regulatory_context = state.get("extracted_regulatory_context", "general compliance")

    # Gather research
    research = {}
    stored_score = state.get("stored_go_no_go_score")
    stored_breakdown = state.get("stored_score_breakdown")
    stored_research = state.get("stored_scoring_research")

    if stored_score is not None and stored_breakdown and stored_research:
        logger.info("Basic Tier: Using persisted unified research")
        research = stored_research
    else:
        logger.info("Basic Tier: Conducting fresh unified research")
        research = await conduct_scoring_research(state)

    # Format Q&A
    questions_asked = state.get("questions_asked", [])
    user_answers = state.get("user_answers", [])
    qa_pairs = (
        "\n".join(
            [f"Q{i + 1}: {q}\nA{i + 1}: {a}" for i, (q, a) in enumerate(zip(questions_asked, user_answers))]
        )
        if questions_asked
        else "No interview Q&A available"
    )

    # Shared Research Context
    research_context = f"""
FOUNDER INTERVIEW INSIGHTS:
{qa_pairs}

LIVE MARKET RESEARCH:
- Market Demand: {research.get("market_demand", "N/A")}
- Competition: {research.get("competition", "N/A")}
- Timing & Trends: {research.get("timing", "N/A")}
- Regulatory: {research.get("regulatory", "N/A")}
- Scalability: {research.get("scalability", "N/A")}

SYNTHESIZED INTELLIGENCE:
{state.get("enriched_context", "N/A")}
"""

    # STRATEGIC DIRECTIVE (Option 1+)
    # Generate the "Truth" for Basic Tier to ensure it matches the scoring criteria
    from src.agents.search.strategy import generate_strategic_directive
    
    # We pass the formatted research context we just built
    strategic_directive = await generate_strategic_directive(state, research_context)
    state["strategic_directive"] = strategic_directive # Store for potential upgrade use
    
    # Format directive for injection
    directive_text = f"""
*** STRATEGIC DIRECTIVE (THE TRUTH) ***
You MUST align your analysis with these decided constraints:
- Target Customer: {strategic_directive.target_customer_segment}
- Pricing Strategy: {strategic_directive.pricing_strategy}
- Core Value Prop: {strategic_directive.core_value_proposition}
- Key Constraints: {', '.join(strategic_directive.key_strategic_constraints)}
- Differentiation: {strategic_directive.differentiation_strategy}
"""
    
    # Append directive to research context so prompts see it
    research_context += f"\n{directive_text}"

    invoke_args_base = {
        "title": desc,
        "research_context": research_context,
        "currency": DEFAULT_CURRENCY,
        "geography": geography,
        "industry": industry,
        "regulatory_context": regulatory_context,
    }

    # 2. STEP 1: GENERATE BMC
    logger.info("Step 1: Generating Business Model Canvas")
    bmc_res = await LLMService.invoke_structured(
        BusinessModelCanvas,
        BASIC_BMC_PROMPT,
        invoke_args_base,
        use_complex=True,  # Use smart model for strategy
        provider="claude",
    )

    # 3. STEP 2: CALCULATE SCORES (Using Unified Prompt)
    logger.info("Step 2: Calculating Unified Scores")
    
    # Prepare summary context for scoring (Using BMC as the "module summary" equivalent)
    bmc_summary_text = f"""
    The Business Model Canvas has been generated:
    - Segments: {bmc_res.customer_segments[:3]}
    - Value Prop: {bmc_res.value_propositions[:3]}
    - Revenue: {bmc_res.revenue_streams[:3]}
    - Costs: {bmc_res.cost_structure[:3]}
    """
    
    scoring_args = {
        **invoke_args_base,
        "summaries": bmc_summary_text,
        "strategic_directive": f"Strategic Decisions:\n- Pricing: {strategic_directive.pricing_strategy}\n- Target: {strategic_directive.target_customer_segment}\n- Value: {strategic_directive.core_value_proposition}"
    }

    # Logic to prioritize persisted scores if available
    if stored_score is not None and stored_breakdown:
        score = stored_score
        adjusted_scores = stored_breakdown
        scoring_res = GoNoGoScores(**adjusted_scores) # Rehydrate for context pass-through
        logger.info(f"Using persisted Go/No-Go score: {score}")
    else:
        # Import unified prompt locally to avoid circular imports if any, or just use reference
        from src.config.prompts import COMPILER_SCORING_PROMPT
        
        scoring_res = await LLMService.invoke_structured(
            GoNoGoScores,
            COMPILER_SCORING_PROMPT,
            scoring_args,
            use_complex=True,
            provider="claude",
        )
        score, adjusted_scores = calculate_go_no_go_score(scoring_res.model_dump())
        logger.info(f"Calculated new Go/No-Go score: {score}")

    # 4. STEP 3: EXECUTIVE SUMMARY
    logger.info("Step 3: Generating Executive Summary")
    
    # Serialize BMC and Scores for prompt context
    import json
    bmc_json = json.dumps(bmc_res.model_dump(), indent=2)
    scores_json = json.dumps(adjusted_scores, indent=2)

    exec_args = {
        **invoke_args_base,
        "go_no_go_score": score,
        "bmc_summary": bmc_json,
        "scoring_summary": scores_json
    }

    from src.models.outputs import BasicExecutiveSummary
    from src.config.prompts import BASIC_EXEC_SUMMARY_PROMPT

    exec_res = await LLMService.invoke_structured(
        BasicExecutiveSummary,
        BASIC_EXEC_SUMMARY_PROMPT,
        exec_args,
        use_complex=True,
        provider="claude",
    )

    # 5. ASSEMBLY
    report = BasicReportOutput(
        tier="basic",
        title=title,
        go_no_go_score=score,
        scores=GoNoGoScores(**adjusted_scores),
        executive_summary=exec_res,
        business_model_canvas=bmc_res,
    )

    # Send webhook
    thread_id = state.get("thread_id")
    if thread_id:
        await send_report_webhook(
            thread_id=thread_id, report_score=score, report_metadata=report.model_dump()
        )

    return {
        "final_report": report.model_dump(),
        "stored_go_no_go_score": score,
        "stored_score_breakdown": adjusted_scores,
        "stored_scoring_research": research
    }
