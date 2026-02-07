"""
Quality Checker Module.
Provides self-verification for LLM outputs and cross-module consistency checks.
Ensures highest quality results by validating outputs before returning to user.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


# ===========================================
# QUALITY CHECK PROMPTS
# ===========================================

SELF_VERIFICATION_PROMPT = ChatPromptTemplate.from_template("""
You are a quality assurance expert reviewing LLM-generated startup analysis.
Evaluate the following output for quality and consistency.

OUTPUT TYPE: {output_type}
ORIGINAL INPUT: {input_context}

GENERATED OUTPUT:
{generated_output}

CHECK FOR:
1. **Completeness**: Are all required fields filled with substantive content (not placeholders)?
2. **Internal Consistency**: Do numbers and facts align within the output?
3. **Logical Flow**: Does the analysis make logical sense?
4. **Specificity**: Are outputs specific rather than generic?
5. **Accuracy Signals**: Any obvious factual errors or implausible claims?

Return ONLY valid JSON:
{{
    "quality_score": 1-10,
    "issues": ["issue 1", "issue 2"],
    "suggestions": ["suggestion 1", "suggestion 2"],
    "pass": true/false
}}

A score of 7+ passes. Flag issues that would mislead the user.
""")


CROSS_MODULE_PROMPT = ChatPromptTemplate.from_template("""
You are validating consistency across multiple startup analysis modules.

STARTUP IDEA:
{description}

MODULE DATA:
{module_data}

CHECK FOR CROSS-MODULE CONSISTENCY:
1. **Financial vs Market**: Do revenue projections align with market size (SOM should be <= projections)?
2. **GTM vs Customer**: Does go-to-market strategy target the defined customer segments?
3. **Tech vs Roadmap**: Is technical timeline feasible given tech stack complexity?
4. **Financial vs Team**: Are team costs reflected in financial projections?
7. **Risk vs All**: Are identified risks addressed in other modules (mitigation strategies)?
8. **CRITICAL**: Ignore minor differences (e.g. 10% variance in numbers). Focus on MAJOR contradictions (e.g. B2B vs B2C, order of magnitude financial differences).

Return ONLY valid JSON:
{{
    "consistency_score": 1-10,
    "inconsistencies": [
        {{"modules": ["module1", "module2"], "issue": "description"}}
    ],
    "recommendations": ["recommendation 1"],
    "pass": true/false
}}

Score 7+ passes. Flag ONLY major inconsistencies that would actively confuse an investor.
""")


INCONSISTENCY_FIX_PROMPT = ChatPromptTemplate.from_template("""
You are a startup validation expert closing inconsistencies in a report.
We found an issue between modules: {modules}
Issue: {issue}

STARTUP IDEA: {description}

MODULE 1 ({name1}):
{content1}

MODULE 2 ({name2}):
{content2}

DECISION:
Which module needs to change to resolve this? 
Usage Rules:
- Market Analysis is usually the "source of truth" for market size. Financials should adapt.
- Technical Requirements is truth for complexity. Roadmap should adapt.
- Customer Segments is truth for audience. GTM should adapt.

TASK:
Rewrite the data for the module that needs fixing. Ensure it is consistent with the other module.
Return valid JSON with:
{{
    "target_module": "{name1}" or "{name2}",
    "fixed_content": {{ ... same structure as original ... }},
    "reasoning": "Why I chose to fix this module and what I changed"
}}
""")


# ===========================================
# QUALITY CHECK FUNCTIONS
# ===========================================


async def verify_output_quality(
    output_type: str,
    input_context: str,
    generated_output: Dict[str, Any],
    min_score: float = 7.0,
) -> Dict[str, Any]:
    """
    Verify quality of a single LLM output.

    Args:
        output_type: Type of output (e.g., "free_tier_report", "market_analysis")
        input_context: Original input/description
        generated_output: The LLM-generated output to verify
        min_score: Minimum acceptable quality score (default 7.0)

    Returns:
        Quality check results with score, issues, and pass/fail
    """
    try:
        result = await LLMService.invoke(
            SELF_VERIFICATION_PROMPT,
            {
                "output_type": output_type,
                "input_context": input_context,
                "generated_output": str(generated_output),
            },
            provider="auto",
            parse_json=True
        )

        quality_score = float(result.get("quality_score", 5))
        passed = quality_score >= min_score

        logger.info(
            f"Quality check for {output_type}: score={quality_score}, passed={passed}"
        )

        return {
            "quality_score": quality_score,
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
            "pass": passed,
        }

    except Exception as e:
        logger.warning(f"Quality verification failed: {e}")
        # Fail open - return passing result if verification fails
        return {
            "quality_score": 7.0,
            "issues": [],
            "suggestions": [],
            "pass": True,
            "error": str(e),
        }


# Import LLMService for unified access
from src.agents.base import LLMService
from src.config.prompts import CONSISTENCY_CHECK_MODULE_PROMPT

async def verify_cross_module_consistency(
    description: str, modules: Dict[str, Any], min_score: float = 7.0
) -> Dict[str, Any]:
    """
    Verify consistency across multiple modules.

    Args:
        description: Original startup description
        modules: Dictionary of module name -> module data
        min_score: Minimum acceptable consistency score

    Returns:
        Consistency check results
    """
    # Format module data for prompt (summarize each module in PARALLEL)
    import asyncio
    
    async def summarize_for_check(name: str, data):
        """Summarize single module for consistency check."""
        if not data:
            return None
        try:
            data_str = str(data)
            summary = await LLMService.invoke(
                CONSISTENCY_CHECK_MODULE_PROMPT,
                {"module_name": name, "module_data": data_str},
                use_complex=False,
                parse_json=False
            )
            return f"**{name}**:\n{summary}"
        except Exception as e:
            logger.warning(f"Failed to summarize {name} for consistency check: {e}")
            return f"**{name}**: {str(data)[:2000]}... (truncated)"
    
    # Execute all summarizations in parallel
    tasks = [summarize_for_check(name, data) for name, data in modules.items()]
    results = await asyncio.gather(*tasks)
    
    # Filter and join
    module_summaries = [r for r in results if r is not None]

    module_data = "\n\n".join(module_summaries)

    try:
        # Use LLMService for the consistency check itself
        result = await LLMService.invoke(
            CROSS_MODULE_PROMPT,
            {
                "description": description,
                "module_data": module_data,         # No arbitrary limit on summarized data
            },
            use_complex=False,  # Fast model is sufficient for consistency check
            parse_json=True
        )

        consistency_score = float(result.get("consistency_score", 5))
        passed = consistency_score >= min_score

        logger.info(
            f"Cross-module consistency check: score={consistency_score}, passed={passed}"
        )

        return {
            "consistency_score": consistency_score,
            "inconsistencies": result.get("inconsistencies", []),
            "recommendations": result.get("recommendations", []),
            "pass": passed,
        }

    except Exception as e:
        logger.warning(f"Cross-module verification failed: {e}")
        return {
            "consistency_score": 7.0,
            "inconsistencies": [],
            "recommendations": [],
            "pass": True,
            "error": str(e),
        }


# ===========================================
# FIELD VALIDATION HELPERS
# ===========================================


def validate_numeric_consistency(data: Dict[str, Any]) -> List[str]:
    """
    Check for numeric consistency in data.

    Returns list of issues found.
    """
    issues = []

    # Check TAM > SAM > SOM
    if "market_data" in data:
        market = data["market_data"]
        tam = _extract_number(
            market.get("total_addressable_market", {}).get("value", "")
        )
        sam = _extract_number(
            market.get("serviceable_addressable_market", {}).get("value", "")
        )
        som = _extract_number(
            market.get("serviceable_obtainable_market", {}).get("value", "")
        )

        if tam and sam and tam < sam:
            issues.append(f"TAM ({tam}) < SAM ({sam}) - should be TAM > SAM")
        if sam and som and sam < som:
            issues.append(f"SAM ({sam}) < SOM ({som}) - should be SAM > SOM")

    return issues


def _extract_number(text: str) -> Optional[float]:
    """Extract numeric value from text like 'EUR 500M' or '2.5B'."""
    import re

    if not text:
        return None

    # Handle billions, millions, thousands
    multipliers = {"B": 1e9, "M": 1e6, "K": 1e3}

    match = re.search(r"([\d.]+)\s*([BMK])?", text.upper())
    if match:
        value = float(match.group(1))
        suffix = match.group(2)
        if suffix and suffix in multipliers:
            value *= multipliers[suffix]
        return value

    return None


def validate_field_lengths(
    data: Dict[str, Any], min_lengths: Dict[str, int]
) -> List[str]:
    """
    Check that fields meet minimum length requirements.

    Args:
        data: Data dictionary to check
        min_lengths: Dict of field_name -> minimum character count

    Returns:
        List of issues found
    """
    issues = []

    for field, min_len in min_lengths.items():
        value = data.get(field)
        if value and isinstance(value, str) and len(value) < min_len:
            issues.append(
                f"Field '{field}' too short ({len(value)} chars, min {min_len})"
            )

    return issues


async def attempt_fix_for_inconsistency(
    description: str, inconsistency: Dict[str, Any], all_modules: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Attempt to fix a cross-module inconsistency by rewriting one module.

    Args:
        description: Startup description
        inconsistency: The issue dict { "modules": ["A", "B"], "issue": "..." }
        all_modules: Dictionary of all module data (key -> content)

    Returns:
        Dict with "target_module" (key) and "fixed_content" (value), or None if failed
    """
    try:
        involved_modules = inconsistency.get("modules", [])
        issue = inconsistency.get("issue", "Unknown issue")

        if len(involved_modules) < 2:
            return None

        name1 = involved_modules[0]
        name2 = involved_modules[1]

        # Build case-insensitive lookup with aliases
        # LLM may return "customer", "Customer", "gtm", "GTM" etc.
        module_lookup = {k.lower(): v for k, v in all_modules.items()}
        # Add aliases for common LLM outputs
        if "bmc" in module_lookup:
            module_lookup["customer"] = module_lookup["bmc"]
            module_lookup["customer segments"] = module_lookup["bmc"]
        
        content1 = module_lookup.get(name1.lower())
        content2 = module_lookup.get(name2.lower())

        if not content1 or not content2:
            logger.warning(f"Could not find module content for {name1} or {name2}")
            return None

        logger.info(f"Attempting to fix inconsistency between {name1} and {name2}")

        result = await LLMService.invoke(
            INCONSISTENCY_FIX_PROMPT,
            {
                "modules": f"{name1} and {name2}",
                "issue": issue,
                "description": description,
                "name1": name1,
                "content1": str(content1),
                "name2": name2,
                "content2": str(content2),
            },
            provider="openai",  # Claude Sonnet for fix writing
            parse_json=True
        )

        target_mod = result.get("target_module")
        fixed_content = result.get("fixed_content")

        if target_mod and fixed_content:
            logger.info(f"Fix proposed for {target_mod}: {result.get('reasoning')}")
            return {"target_module": target_mod, "fixed_content": fixed_content}

    except Exception as e:
        logger.warning(f"Auto-fix failed: {e}")

    return None
