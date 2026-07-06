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
from src.config.constants import MODULE_DATA_KEYS
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
                {
                    "module_name": module_name,
                    "module_data": data_str,
                    "currency": currency,
                },
                use_complex=False,
                parse_json=False,
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
            use_complex=True,
            provider="claude",
        )
        return deck
    except Exception as e:
        logger.error(f"Failed to generate Pitch Deck: {e}")
        # Return empty/fallback deck structure if needed, or re-raise
        # For now, return a basic error deck to avoid crashing the whole report
        return InvestorPitchDeck(
            slides=[
                SlideContent(
                    slide_number=i + 1,
                    title="Error Generating Slide",
                    content_bullets=["Generation failed."],
                    visual_suggestion="None",
                    speaker_notes="Error.",
                )
                for i in range(12)
            ],
            strategic_narrative="Error generation pitch deck.",
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
        "modules": _filter_modules_for_tier(
            state,
            {
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
            },
        ),
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
        "funding": "mod_funding",
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

    # === SMART CASCADE CONSISTENCY FIXING ===
    logger.info("Starting Smart Cascade consistency fixing")

    if state["inputs"].tier == "custom":
        logger.info("Custom tier: Skipping consistency checks for performance")
    else:
        from src.agents.schema_registry import (
            classify_issue_severity,
            IssueSeverity,
            validate_module_data,
        )
        from src.agents.fix_history import FixHistory
        from src.agents.dependency_analyzer import (
            execute_parallel_fixes,
            get_dependency_info,
        )

        # Build module lookup
        simple_to_key = {v.replace("_data", ""): v for k, v in MODULE_DATA_KEYS.items()}
        simple_to_key.update(
            {
                "Customer": "bmc_data",
                "Financials": "financial_data",
                "Competition": "competitor_data",
                "Competitors": "competitor_data",
                "Market": "market_data",
                "Tech": "tech_data",
                "Risks": "risk_data",
            }
        )

        MAX_FIX_CYCLES = 1   # One cycle is sufficient with paid model quality
        MAX_LLM_CALLS = 8   # Tightened budget for single-cycle run
        MAX_PARALLEL_FIXES = 3
        llm_calls_used = 0

        # Initialize fix history tracker
        fix_history = FixHistory(max_module_fixes=3)

        # Summary cache: persists across cycles, invalidated per fixed module
        summary_cache: dict = {}

        for cycle in range(MAX_FIX_CYCLES):
            logger.info(f"=== Consistency Check Cycle {cycle + 1}/{MAX_FIX_CYCLES} ===")

            # Gather current modules
            modules_for_check = {
                key.replace("_data", ""): state.get(key)
                for key in MODULE_DATA_KEYS.values()
                if state.get(key)
            }

            # Filter for custom modules
            custom_modules = state.get("custom_modules")
            if custom_modules:
                filtered = {}
                report_key_map = {v: k for k, v in MODULE_DATA_KEYS.items()}

                for simple_name, content in modules_for_check.items():
                    data_key = simple_to_key.get(simple_name)
                    if data_key:
                        node_name = report_key_map.get(data_key)
                        if node_name and node_name in custom_modules:
                            filtered[simple_name] = content

                modules_for_check = filtered

            if len(modules_for_check) < 2:
                logger.info("Too few modules for consistency check")
                break

            # Add derived data
            if state.get("bmc_data"):
                modules_for_check["Customer"] = state["bmc_data"].get(
                    "customer_segments"
                )

            # Run consistency check (with cached summaries)
            consistency_check = await verify_cross_module_consistency(
                description=desc,
                modules=modules_for_check,
                summary_cache=summary_cache,
            )
            # Update cache from result
            summary_cache = consistency_check.get("summary_cache", summary_cache)

            if consistency_check.get("pass", True):
                logger.info("✓ All modules consistent!")
                break

            # Get and classify issues
            all_issues = consistency_check.get("inconsistencies", [])
            if not all_issues:
                logger.info("No specific inconsistencies found")
                break

            # Classify by severity
            classified_issues = []
            for issue in all_issues:
                severity = classify_issue_severity(issue.get("issue", ""))
                classified_issues.append(
                    {
                        **issue,
                        "severity": severity,
                        "severity_priority": {
                            IssueSeverity.CRITICAL: 0,
                            IssueSeverity.MAJOR: 1,
                            IssueSeverity.MINOR: 2,
                        }[severity],
                    }
                )

            # Sort by severity
            classified_issues.sort(key=lambda x: x["severity_priority"])

            critical_count = sum(
                1 for i in classified_issues if i["severity"] == IssueSeverity.CRITICAL
            )
            major_count = sum(
                1 for i in classified_issues if i["severity"] == IssueSeverity.MAJOR
            )
            minor_count = sum(
                1 for i in classified_issues if i["severity"] == IssueSeverity.MINOR
            )

            logger.info(
                f"Found {len(classified_issues)} issues: {critical_count} critical, {major_count} major, {minor_count} minor"
            )

            # Group by severity for batch processing
            critical_issues = [
                i for i in classified_issues if i["severity"] == IssueSeverity.CRITICAL
            ]
            major_issues = [
                i for i in classified_issues if i["severity"] == IssueSeverity.MAJOR
            ]
            minor_issues = [
                i for i in classified_issues if i["severity"] == IssueSeverity.MINOR
            ]

            fixes_applied = 0
            fixes_failed = 0

            # Process critical (all) - with history tracking and parallel execution
            if critical_issues:
                # Check which issues should be skipped (history-based)
                issues_to_fix = []
                skipped_count = 0

                for issue in critical_issues:
                    target = issue.get("modules", [""])[-1]
                    should_skip, skip_reason = fix_history.should_skip_issue(
                        issue, target
                    )

                    if should_skip:
                        logger.info(f"Skipping issue: {skip_reason}")
                        skipped_count += 1
                    else:
                        issues_to_fix.append(issue)

                if skipped_count > 0:
                    logger.info(
                        f"Skipped {skipped_count} issues due to history tracking"
                    )

                # Group into parallel batches
                dep_info = get_dependency_info(issues_to_fix)
                logger.info(
                    f"Dependency analysis: {dep_info['batches']} batches, parallelism: {dep_info.get('parallelism_factor', 1):.1f}x"
                )

                # Execute critical fixes in parallel batches
                if issues_to_fix:
                    # Use parallel execution for critical issues
                    fix_results = await execute_parallel_fixes(
                        issues=issues_to_fix,
                        attempt_fix_func=attempt_fix_for_inconsistency,
                        state_modules=modules_for_check,
                        description=desc,
                        max_parallel=MAX_PARALLEL_FIXES,
                    )

                    # Process results
                    for result in fix_results:
                        if result.get("success"):
                            fix_result = result.get("result")
                            is_valid, error = validate_module_data(
                                fix_result["target_state_key"],
                                fix_result["fixed_content"],
                            )

                            if is_valid:
                                state[fix_result["target_state_key"]] = fix_result[
                                    "fixed_content"
                                ]
                                fixes_applied += 1
                                llm_calls_used += 2

                                # Invalidate summary cache for the fixed module
                                fixed_simple = fix_result["target_state_key"].replace("_data", "")
                                summary_cache.pop(fixed_simple, None)

                                # Record in history
                                fix_history.record_fix(
                                    issue=result.get("issue", {}),
                                    target_module=fix_result["target_module"],
                                    target_state_key=fix_result["target_state_key"],
                                    field_path=fix_result.get("field_path", ""),
                                    fix_type=fix_result.get("fix_type", "unknown"),
                                    cycle=cycle,
                                )

                                logger.info(
                                    f"Applied {fix_result['fix_type']} fix to {fix_result['target_state_key']}"
                                )
                            else:
                                fixes_failed += 1
                                logger.error(f"Fix validation failed: {error}")
                        else:
                            fixes_failed += 1
                            if result.get("error"):
                                logger.error(f"Fix error: {result.get('error')}")

            # If critical fixes resolved everything, skip major/minor
            if fixes_applied > 0 and cycle < MAX_FIX_CYCLES - 1:
                # Quick re-check before continuing (with cached summaries)
                quick_check = await verify_cross_module_consistency(
                    desc,
                    modules_for_check,
                    summary_cache=summary_cache,
                )
                summary_cache = quick_check.get("summary_cache", summary_cache)
                if quick_check.get("pass", False):
                    logger.info("Critical fixes resolved all issues!")
                    break

            # Process major (up to 3) - with history tracking
            for issue in major_issues[:3]:
                if llm_calls_used >= MAX_LLM_CALLS:
                    break

                # Check history
                target = issue.get("modules", [""])[-1]
                should_skip, skip_reason = fix_history.should_skip_issue(issue, target)
                if should_skip:
                    logger.info(f"Skipping major issue: {skip_reason}")
                    continue

                fix_result = await attempt_fix_for_inconsistency(
                    desc, issue, modules_for_check
                )
                llm_calls_used += 2

                if fix_result and fix_result.get("fix_type") != "failed":
                    is_valid, error = validate_module_data(
                        fix_result["target_state_key"], fix_result["fixed_content"]
                    )

                    if is_valid:
                        state[fix_result["target_state_key"]] = fix_result[
                            "fixed_content"
                        ]
                        fixes_applied += 1

                        # Invalidate summary cache for the fixed module
                        fixed_simple = fix_result["target_state_key"].replace("_data", "")
                        summary_cache.pop(fixed_simple, None)

                        # Record in history
                        fix_history.record_fix(
                            issue=issue,
                            target_module=fix_result.get("target_module", ""),
                            target_state_key=fix_result["target_state_key"],
                            field_path=fix_result.get("field_path", ""),
                            fix_type=fix_result.get("fix_type", "unknown"),
                            cycle=cycle,
                        )

            # Only process minor if no critical/major and we have budget
            if (
                not critical_issues
                and not major_issues
                and llm_calls_used < MAX_LLM_CALLS - 5
            ):
                for issue in minor_issues[:2]:  # Max 2 minor
                    # Check history
                    target = issue.get("modules", [""])[-1]
                    should_skip, skip_reason = fix_history.should_skip_issue(
                        issue, target
                    )
                    if should_skip:
                        continue

                    fix_result = await attempt_fix_for_inconsistency(
                        desc, issue, modules_for_check
                    )
                    llm_calls_used += 2

                    if fix_result and fix_result.get("fix_type") != "failed":
                        is_valid, error = validate_module_data(
                            fix_result["target_state_key"], fix_result["fixed_content"]
                        )

                        if is_valid:
                            state[fix_result["target_state_key"]] = fix_result[
                                "fixed_content"
                            ]
                            fixes_applied += 1

                            # Invalidate summary cache for the fixed module
                            fixed_simple = fix_result["target_state_key"].replace("_data", "")
                            summary_cache.pop(fixed_simple, None)

            logger.info(
                f"Cycle {cycle + 1} complete: {fixes_applied} fixes applied, {fixes_failed} failed, {llm_calls_used} LLM calls used"
            )

            # Early exit if all critical issues resolved
            if not critical_issues and not major_issues:
                logger.info("No more critical or major issues, stopping cascade")
                break

        logger.info(f"Smart Cascade complete: {llm_calls_used} total LLM calls")

        # Log fix history summary
        history_summary = fix_history.get_fix_summary()
        logger.info(
            f"Fix history: {history_summary['total_fixes']} fixes applied, "
            f"modules: {history_summary['modules_affected']}"
        )

    # Gather module summaries (re-compile after fixes)
    module_summaries = await _compile_module_summaries(state)

    # Conduct fresh internet research for scoring
    # CHECK FOR PERSISTED SCORE & RESEARCH
    stored_score = state.get("stored_go_no_go_score")
    stored_breakdown = state.get("stored_score_breakdown")
    stored_research = state.get("stored_scoring_research")

    scoring_research = {}

    if stored_score is not None and stored_breakdown and stored_research:
        logger.info(
            "Using persisted Go/No-Go score and research (skipping fresh analysis)"
        )
        scoring_research = stored_research
        final_score = stored_score
        adjusted_scores = stored_breakdown
    else:
        # COST OPTIMIZATION: Reuse comprehensive_research if available (eliminates 20+ Tavily calls)
        comprehensive = state.get("comprehensive_research")
        if comprehensive:
            logger.info(
                f"Reusing comprehensive research for scoring ({len(comprehensive)} chars)"
            )
            # Extract scoring-relevant context from comprehensive research
            scoring_research = {
                "market_demand": comprehensive[:2000]
                if len(comprehensive) > 2000
                else comprehensive,
                "competition": comprehensive[2000:4000]
                if len(comprehensive) > 4000
                else comprehensive,
                "timing": comprehensive[4000:6000]
                if len(comprehensive) > 6000
                else comprehensive,
                "regulatory": comprehensive[6000:8000]
                if len(comprehensive) > 8000
                else comprehensive,
                "scalability": comprehensive[8000:10000]
                if len(comprehensive) > 10000
                else comprehensive,
            }
        else:
            logger.info(
                "Comprehensive research not found, conducting internet research for Go/No-Go scoring"
            )
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
            strat_txt = (
                "No specific strategic directive provided. Rely on research context."
            )

        invoke_args = {
            "title": desc,  # LLM will extract/generate title from description
            "summaries": module_summaries,
            "research_context": research_context,
            "geography": state.get("extracted_geography", "Global"),
            "industry": state.get("extracted_industry", ""),
            "regulatory_context": state.get(
                "extracted_regulatory_context", "general compliance"
            ),
            "strategic_directive": strat_txt,
        }

        # Use LLMService for scoring with automatic fallback
        scores = await LLMService.invoke(
            COMPILER_SCORING_PROMPT,
            invoke_args,
            use_complex=True,
            parse_json=True,
            provider="claude-opus",  # Opus 4.5 for critical scoring reasoning
        )

        final_score, adjusted_scores = calculate_go_no_go_score(scores)
        logger.info(f"Go/No-Go score calculated: {final_score}")

    # Ensure research_context is available for Executive Summary even if we skipped scoring
    if "research_context" not in locals():
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
        "currency": "EUR",  # DEFAULT_CURRENCY import might be needed or just string
    }

    try:
        # Use LLMService for executive summary with automatic fallback
        executive_summary = await LLMService.invoke(
            EXECUTIVE_SUMMARY_PROMPT,
            exec_summary_args,
            use_complex=True,
            parse_json=True,
            provider="claude-opus",  # Opus 4.5 for high-quality executive summary
        )
        # with_structured_output can silently return None when the LLM outputs prose
        if executive_summary is None:
            raise ValueError("LLM returned None for executive summary (likely non-JSON response)")
    except Exception as exec_error:
        logger.warning(f"Executive summary generation failed: {exec_error}")
        # Schema-compliant fallback
        executive_summary = {
            "problem_summary": "Executive summary generation encountered an issue. See detailed module reports below.",
            "proposed_solution": "Review the detailed analysis modules for full startup assessment.",
            "report_highlights": [
                "Full analysis available in detailed modules",
                f"Go/No-Go Score: {final_score}/100",
                "See Business Model Canvas, Market Analysis, and Financial modules for details",
            ],
            "recommendation": {
                "go_no_go_verdict": "Conditional-Go" if final_score >= 35 else "No-Go",
                "rating_justification": f"Score of {final_score}/100. Review detailed modules for full context.",
                "key_strengths": ["See detailed report modules"],
                "key_risks": ["See risk assessment module"],
                "immediate_action_items": ["Review all report modules for actionable insights"],
            },
        }

    logger.info("Executive summary generated (structured object)")

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
        "stored_scoring_research": scoring_research,
    }


from src.utils.supabase import update_session_status


async def admin_approval_node(state: ValidationState) -> dict:
    """
    Admin approval node.
    This runs AFTER the admin hits the approve endpoint and resumes the graph.
    Sets workflow phase and updates database status to ready.
    """
    thread_id = state.get("thread_id")
    inputs = state.get("inputs")
    
    # Robust tier extraction
    if hasattr(inputs, 'tier'):
        tier = inputs.tier
    elif isinstance(inputs, dict):
        tier = inputs.get("tier", "premium")
    else:
        tier = "premium"
    
    if thread_id:
        logger.info(f"Admin approved thread {thread_id}, setting to {tier}_report_ready")
        await update_session_status(thread_id, f"{tier}_report_ready")
    
    logger.info("Report approved by admin")
    return {"workflow_phase": "completed"}
