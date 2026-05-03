"""
Dependency analyzer for determining which fixes can run in parallel.
Groups independent issues to maximize concurrent execution.
"""

from typing import Dict, List, Set
from collections import defaultdict
import logging
import asyncio

logger = logging.getLogger(__name__)


# Module dependency graph: what modules affect what other modules
# If A affects B, they cannot be fixed in parallel
MODULE_DEPENDENCIES: Dict[str, Set[str]] = {
    "market_data": {"financial_data", "gtm_data", "roadmap_data", "bmc_data"},
    "competitor_data": {"market_data", "gtm_data", "financial_data"},
    "bmc_data": {"market_data", "gtm_data", "financial_data", "roadmap_data"},
    "tech_data": {"roadmap_data", "financial_data", "funding_data"},
    "reg_data": {"bmc_data", "financial_data", "tech_data", "roadmap_data"},
    "risk_data": {"roadmap_data", "financial_data", "bmc_data"},
    "financial_data": {"roadmap_data", "funding_data"},
    "roadmap_data": set(),  # Usually leaf node
    "gtm_data": set(),  # Usually leaf node
    "funding_data": set(),  # Usually leaf node
}


def normalize_module_name(module: str) -> str:
    """Normalize module name to state key format."""
    # Common variations
    mappings = {
        "customer": "bmc_data",
        "competition": "competitor_data",
        "competitors": "competitor_data",
        "finance": "financial_data",
        "financials": "financial_data",
        "tech": "tech_data",
        "technical": "tech_data",
        "regulatory": "reg_data",
        "compliance": "reg_data",
    }
    return mappings.get(module.lower(), module.lower())


def get_all_affected_modules(modules: Set[str]) -> Set[str]:
    """Get all modules that could be affected by changes to given modules."""
    affected = set(modules)

    for module in modules:
        # Add direct dependencies
        if module in MODULE_DEPENDENCIES:
            affected.update(MODULE_DEPENDENCIES[module])

        # Add reverse dependencies (modules that depend on this one)
        for mod, deps in MODULE_DEPENDENCIES.items():
            if module in deps:
                affected.add(mod)

    return affected


def has_dependency(issue_a: Dict, issue_b: Dict) -> bool:
    """
    Check if two issues have overlapping module dependencies.
    If they share modules or one affects the other, they cannot run in parallel.
    """
    mods_a = {normalize_module_name(m) for m in issue_a.get("modules", [])}
    mods_b = {normalize_module_name(m) for m in issue_b.get("modules", [])}

    # Shared modules means dependency
    if mods_a & mods_b:
        return True

    # Check transitive dependencies
    affected_a = get_all_affected_modules(mods_a)
    if mods_b & affected_a:
        return True

    affected_b = get_all_affected_modules(mods_b)
    return bool(mods_a & affected_b)


def group_independent_fixes(issues: List[Dict]) -> List[List[Dict]]:
    """
    Group issues into batches that can be fixed in parallel.

    Uses graph coloring approach:
    - Issues in the same batch (color) have no dependencies
    - Each batch can run concurrently

    Args:
        issues: List of issue dictionaries with 'modules' key

    Returns:
        List of batches, each batch is a list of issues
    """
    if not issues:
        return []

    n = len(issues)
    if n == 1:
        return [issues]

    # Try to color the graph
    colors = [-1] * n

    for i in range(n):
        # Find first available color
        used_colors = set()
        for j in range(i):
            if has_dependency(issues[i], issues[j]):
                used_colors.add(colors[j])

        # Assign lowest available color
        color = 0
        while color in used_colors:
            color += 1
        colors[i] = color

    # Group by color
    batches = defaultdict(list)
    for i, color in enumerate(colors):
        batches[color].append(issues[i])

    result = list(batches.values())

    logger.debug(
        f"Grouped {n} issues into {len(result)} batches: {[len(b) for b in result]}"
    )

    return result


async def execute_parallel_fixes(
    issues: List[Dict],
    attempt_fix_func,
    state_modules: Dict,
    description: str,
    max_parallel: int = 3,
) -> List[Dict]:
    """
    Execute fixes for multiple issues in parallel where possible.

    Args:
        issues: List of issues to fix
        attempt_fix_func: Function to call for each fix attempt
        state_modules: Current module data
        description: Startup description
        max_parallel: Maximum concurrent fixes

    Returns:
        List of fix results with success status
    """
    if not issues:
        return []

    # Group into independent batches
    batches = group_independent_fixes(issues)

    all_results = []

    for batch_idx, batch in enumerate(batches):
        logger.debug(
            f"Executing batch {batch_idx + 1}/{len(batches)} with {len(batch)} issues"
        )

        # Limit parallel execution per batch
        batch = batch[:max_parallel]

        # Create async task for a single fix
        async def fix_single(issue: Dict) -> Dict:
            try:
                result = await attempt_fix_func(
                    description=description,
                    inconsistency=issue,
                    all_modules=state_modules,
                )
                is_success = result is not None and result.get("fix_type") != "failed"
                return {
                    "issue": issue,
                    "result": result,
                    "success": is_success,
                    "error": None,
                }
            except Exception as err:
                logger.error(f"Fix error: {err}")
                return {
                    "issue": issue,
                    "result": None,
                    "success": False,
                    "error": str(err),
                }

        # Execute batch in parallel
        tasks = [fix_single(issue) for issue in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                all_results.append(
                    {
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                all_results.append(result)

    # Summary
    success_count = sum(1 for r in all_results if r.get("success"))
    logger.debug(
        f"Parallel execution complete: {success_count}/{len(all_results)} successful"
    )

    return all_results


def get_dependency_info(issues: List[Dict]) -> Dict:
    """
    Get dependency information for a list of issues.

    Returns:
        Dict with dependency analysis
    """
    if not issues:
        return {"total": 0, "batches": 0, "can_parallelize": True}

    batches = group_independent_fixes(issues)

    return {
        "total": len(issues),
        "batches": len(batches),
        "batch_sizes": [len(b) for b in batches],
        "can_parallelize": len(batches) > 1,
        "parallelism_factor": len(issues) / len(batches) if batches else 1,
    }
