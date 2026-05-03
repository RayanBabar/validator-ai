"""
Parallel Module Executor for Standard/Premium/Custom Tier Reports.

Runs all selected modules in parallel using asyncio.gather() to reduce
total execution time from 20-30 minutes to 3-5 minutes.
"""

import asyncio
import logging
from typing import Dict, Any

from src.models.inputs import ValidationState
from src.agents.standard_modules import (
    std_bmc,
    std_market,
    std_comp,
    std_finance,
    std_tech,
    std_reg,
    std_gtm,
    std_risk,
    std_roadmap,
    std_funding,
)

logger = logging.getLogger(__name__)

MODULE_MAP = {
    "mod_bmc": std_bmc,
    "mod_market": std_market,
    "mod_comp": std_comp,
    "mod_finance": std_finance,
    "mod_tech": std_tech,
    "mod_reg": std_reg,
    "mod_gtm": std_gtm,
    "mod_risk": std_risk,
    "mod_roadmap": std_roadmap,
    "mod_funding": std_funding,
}


async def run_modules_parallel(state: ValidationState) -> Dict[str, Any]:
    """
    Run selected modules in parallel using asyncio.gather().

    Supports:
    - Standard/Premium tier: Runs all 10 modules in parallel
    - Custom tier: Runs only modules specified in state["custom_modules"]

    Args:
        state: Current validation state with inputs and research data

    Returns:
        Dictionary with merged results from all executed modules
    """
    comprehensive_research = None
    if not state.get("comprehensive_research"):
        logger.info("Comprehensive research missing - gathering for scoring reuse")
        try:
            from src.agents.search.strategy import conduct_comprehensive_research

            inp = state.get("inputs")
            desc = inp.detailed_description if inp else "startup idea"
            geography = state.get("extracted_geography", "global")
            industry = state.get("extracted_industry", "startup")
            tier = inp.tier if inp else "basic"
            custom_mods = state.get("custom_modules")

            comprehensive_research = await conduct_comprehensive_research(
                description=desc,
                geography=geography,
                industry=industry,
                tier=tier,
                requested_modules=custom_mods,
            )

            if comprehensive_research:
                logger.info(
                    f"Gathered comprehensive research: {len(comprehensive_research)} chars"
                )
                state["comprehensive_research"] = comprehensive_research
        except Exception as e:
            logger.warning(f"Failed to gather comprehensive research: {e}")

    if not state.get("strategic_directive"):
        try:
            from src.agents.search.strategy import generate_strategic_directive

            research_ctx = state.get("comprehensive_research", "")

            directive = await generate_strategic_directive(state, research_ctx)
            state["strategic_directive"] = directive

            logger.info("Strategic Directive set in state.")
        except Exception as e:
            logger.warning(f"Failed to generate Strategic Directive: {e}")

    custom_modules = state.get("custom_modules")

    if custom_modules:
        modules_to_run = {k: v for k, v in MODULE_MAP.items() if k in custom_modules}
        logger.info(
            f"Parallel execution: Running {len(modules_to_run)} custom modules: {list(modules_to_run.keys())}"
        )
    else:
        modules_to_run = MODULE_MAP
        logger.info(f"Parallel execution: Running all {len(modules_to_run)} modules")

    async def run_module_safe(name: str, fn):
        """Run a module with error handling."""
        try:
            logger.info(f"Starting module: {name}")
            result = await fn(state)
            logger.info(f"Completed module: {name}")
            return result
        except Exception as e:
            logger.error(f"Module {name} failed: {e}")
            return {}

    tasks = [run_module_safe(name, fn) for name, fn in modules_to_run.items()]
    results = await asyncio.gather(*tasks)

    merged = {}
    for result in results:
        if result:
            merged.update(result)

    if comprehensive_research:
        merged["comprehensive_research"] = comprehensive_research

    logger.info(f"Parallel execution complete. Merged {len(merged)} data keys.")
    return merged
