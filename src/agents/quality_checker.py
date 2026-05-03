"""
Quality Checker Module.
Provides self-verification for LLM outputs and cross-module consistency checks.
Ensures highest quality results by validating outputs before returning to user.
"""

import logging
import json
from typing import Dict, Any, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ===========================================
# PYDANTIC SCHEMAS FOR STRUCTURED OUTPUT
# ===========================================

class QualityCheckResult(BaseModel):
    """Schema for quality verification results."""
    quality_score: float = Field(description="Quality score from 1-10")
    issues: List[str] = Field(default_factory=list, description="List of identified issues")
    suggestions: List[str] = Field(default_factory=list, description="List of improvement suggestions")
    pass_: bool = Field(alias="pass", description="Whether quality check passed")

    class Config:
        populate_by_name = True


class Inconsistency(BaseModel):
    """Single inconsistency between modules."""
    modules: List[str] = Field(description="List of module names involved")
    issue: str = Field(description="Description of the inconsistency")


class ConsistencyCheckResult(BaseModel):
    """Schema for cross-module consistency check results."""
    consistency_score: float = Field(description="Consistency score from 1-10")
    inconsistencies: List[Inconsistency] = Field(default_factory=list, description="List of inconsistencies found")
    recommendations: List[str] = Field(default_factory=list, description="List of recommendations")
    pass_: bool = Field(alias="pass", description="Whether consistency check passed")

    class Config:
        populate_by_name = True


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


STRICT_SCHEMA_FIX_PROMPT = ChatPromptTemplate.from_template("""
You are a data consistency engineer fixing validation report data.
Your task: Resolve an inconsistency while PRESERVING the exact JSON structure.

**CRITICAL CONSTRAINTS:**
1. Return VALID JSON that validates against the schema below
2. NEVER add new fields
3. NEVER remove existing fields
4. NEVER change data types
5. ONLY modify values causing the inconsistency
6. Preserve ALL nested structures exactly

**JSON Schema (MUST follow exactly):**
```json
{json_schema}
```

**Original Data (Current State):**
```json
{original_data}
```

**Issue to Resolve:**
- Description: {issue_description}
- Conflicting Module: {other_module}
- Other Module's Data: {other_value}

**Resolution Strategy:**
- Primary source of truth: {primary_source}
- Target field to modify: Look for fields mentioned in the issue

Return ONLY valid JSON matching the schema exactly. No markdown, no explanations.
""")

SURGICAL_FIELD_FIX_PROMPT = ChatPromptTemplate.from_template("""
Schema-level fix failed. Apply surgical field-level fix.

**Target:** {field_path}
**Current Value:** {current_value}
**Should Align With:** {reference_value}
**Issue:** {issue_description}

**Task:**
Return the corrected value for the specific field path.

Return JSON:
{{
    "field_path": "exact.path.to.field",
    "new_value": <corrected_value_of_same_type>
}}
""")


AUTHORITY_AWARE_FIX_PROMPT = ChatPromptTemplate.from_template("""
You are fixing a consistency issue between startup analysis modules.
You MUST respect module authority rules when making changes.

**AUTHORITY RULES:**
{authority_context}

**CONFLICT TO RESOLVE:**
{issue_description}

**Source of Truth Module ({source_module}):**
```json
{source_data}
```

**Module to Fix ({target_module}):**
```json
{target_data}
```

**Task:**
1. Identify which fields in {target_module} conflict with {source_module}
2. ONLY modify fields that are allowed to change (see authority rules)
3. Preserve ALL other fields exactly as they are
4. Ensure the modified values align with {source_module}

**Important:**
- Do NOT change fields where {source_module} is the authority
- Maintain exact JSON structure and types
- Only update values to be consistent with {source_module}

Return ONLY valid JSON matching the target module's schema.
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
        result = await LLMService.invoke_structured(
            QualityCheckResult,
            SELF_VERIFICATION_PROMPT,
            {
                "output_type": output_type,
                "input_context": input_context,
                "generated_output": str(generated_output),
            },
            use_complex=False,  # Use fast LLM for quality checks
            provider="auto",
        )

        quality_score = result.quality_score
        passed = quality_score >= min_score

        logger.info(
            f"Quality check for {output_type}: score={quality_score}, passed={passed}"
        )

        return {
            "quality_score": quality_score,
            "issues": result.issues,
            "suggestions": result.suggestions,
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
    description: str,
    modules: Dict[str, Any],
    min_score: float = 7.0,
    summary_cache: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Verify consistency across multiple modules.

    Args:
        description: Original startup description
        modules: Dictionary of module name -> module data
        min_score: Minimum acceptable consistency score
        summary_cache: Optional cache of previously generated summaries.
                       Keys are module names, values are summary strings.
                       Modules in cache skip re-summarization.

    Returns:
        Consistency check results with updated 'summary_cache' key
    """
    import asyncio

    if summary_cache is None:
        summary_cache = {}

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
                parse_json=False,
            )
            formatted = f"**{name}**:\n{summary}"
            return name, formatted
        except Exception as e:
            logger.warning(f"Failed to summarize {name} for consistency check: {e}")
            formatted = f"**{name}**: {str(data)[:2000]}... (truncated)"
            return name, formatted

    # Only summarize modules not already in cache
    modules_to_summarize = {
        name: data for name, data in modules.items()
        if name not in summary_cache
    }
    cached_count = len(modules) - len(modules_to_summarize)
    if cached_count > 0:
        logger.info(
            f"Reusing cached summaries for {cached_count} modules, "
            f"summarizing {len(modules_to_summarize)} new/changed modules"
        )

    # Execute only needed summarizations with limited concurrency to avoid 429/400 errors
    if modules_to_summarize:
        semaphore = asyncio.Semaphore(2)  # Limit to 2 parallel summarization calls
        
        async def sem_summarize(name, data):
            async with semaphore:
                res = await summarize_for_check(name, data)
                await asyncio.sleep(0.5)  # Small cooldown between calls
                return res

        tasks = [
            sem_summarize(name, data)
            for name, data in modules_to_summarize.items()
        ]
        results = await asyncio.gather(*tasks)

        # Update cache with new summaries
        for result in results:
            if result is not None:
                name, formatted = result
                summary_cache[name] = formatted

    # Build full module data from cache (in original module order)
    module_summaries = []
    for name in modules:
        if name in summary_cache:
            module_summaries.append(summary_cache[name])
        else:
            # Fallback if somehow missing from cache/summarization failed
            logger.warning(f"Module {name} missing from summary cache, using raw truncation")
            module_summaries.append(f"**{name}**: {str(modules[name])[:1000]}...")

    module_data = "\n\n".join(module_summaries)
    if len(module_data) > 5000:  # Reduced limit for stability
        module_data = module_data[:5000] + "... [TRUNCATED FOR LENGTH]"

    try:
        result = await LLMService.invoke_structured(
            ConsistencyCheckResult,
            CROSS_MODULE_PROMPT,
            {
                "description": description,
                "module_data": module_data,
            },
            use_complex=False,
            provider="auto",
        )

        consistency_score = result.consistency_score
        passed = consistency_score >= min_score

        logger.info(
            f"Cross-module consistency check: score={consistency_score}, passed={passed}"
        )

        return {
            "consistency_score": consistency_score,
            "inconsistencies": [{"modules": inc.modules, "issue": inc.issue} for inc in result.inconsistencies],
            "recommendations": result.recommendations,
            "pass": passed,
            "summary_cache": summary_cache,
        }

    except Exception as e:
        logger.warning(f"Cross-module verification failed: {e}")
        return {
            "consistency_score": 7.0,
            "inconsistencies": [],
            "recommendations": [],
            "pass": True,
            "error": str(e),
            "summary_cache": summary_cache,
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
    Attempt to fix a cross-module inconsistency with strict schema validation.

    Uses two-phase approach:
    1. Strict schema fix - Validates against Pydantic model
    2. Surgical field fix - Targets specific field if schema fix fails

    Args:
        description: Startup description
        inconsistency: The issue dict { "modules": ["A", "B"], "issue": "..." }
        all_modules: Dictionary of all module data (key -> content)

    Returns:
        Dict with fix results including validation status, or None if failed
    """
    from src.agents.schema_registry import (
        get_schema_for_module,
        validate_module_data,
        resolve_module_name,
        get_nested_value,
        set_nested_value,
        extract_field_path_from_issue,
        determine_fix_target,
    )

    try:
        modules = inconsistency.get("modules", [])
        issue = inconsistency.get("issue", "")

        if len(modules) < 2:
            logger.warning("Need at least 2 modules to fix inconsistency")
            return None

        name1, name2 = modules[0], modules[1]

        # Resolve to state keys
        state_key1, subsection1 = resolve_module_name(name1)
        state_key2, subsection2 = resolve_module_name(name2)

        if not state_key1 or not state_key2:
            logger.error(f"Cannot resolve module names: {name1}, {name2}")
            return None

        # Lookup using resolved state keys (e.g. "market_data" → "market")
        # The all_modules dict uses simple names like "market", "competitor"
        simple_key1 = state_key1.replace("_data", "")
        simple_key2 = state_key2.replace("_data", "")
        content1 = all_modules.get(simple_key1) or all_modules.get(name1.lower())
        content2 = all_modules.get(simple_key2) or all_modules.get(name2.lower())

        if not content1 or not content2:
            logger.error(
                f"Missing content for: {name1} (tried '{simple_key1}') "
                f"or {name2} (tried '{simple_key2}'). "
                f"Available keys: {list(all_modules.keys())}"
            )
            return None

        # Determine which module to fix using authority rules
        target_name, authority_reason = determine_fix_target(name1, name2, issue)

        # Set source and target based on authority
        if target_name == state_key2:
            source_name = name1
            source_state_key = state_key1
            target_state_key = state_key2
            target_content = content2
            source_content = content1
            subsection2_used = subsection2
        else:
            source_name = name2
            source_state_key = state_key2
            target_state_key = state_key1
            target_content = content1
            source_content = content2
            subsection2_used = subsection1

        logger.info(f"Fixing inconsistency: {name1} ↔ {name2} | Issue: {issue[:50]}...")
        logger.info(f"Authority decision: Fix {target_name} ({authority_reason})")

        # === PHASE 1: Strict Schema Fix ===
        schema = get_schema_for_module(target_state_key)

        if schema:
            try:
                result = await LLMService.invoke(
                    STRICT_SCHEMA_FIX_PROMPT,
                    {
                        "json_schema": json.dumps(schema, indent=2),
                        "original_data": json.dumps(target_content),
                        "issue_description": issue,
                        "other_module": source_name,
                        "other_value": str(source_content)[:1000],
                        "primary_source": source_name,
                        "target_field": "inconsistent_field",
                    },
                    provider="claude",
                    parse_json=True,
                )

                fixed_content = result.get("fixed_content") or result

                # Strict validation
                is_valid, error = validate_module_data(target_state_key, fixed_content)

                if is_valid:
                    logger.info(f"✓ Strict fix successful for {target_name}")
                    return {
                        "target_module": target_name,
                        "target_state_key": target_state_key,
                        "fixed_content": fixed_content,
                        "fix_type": "strict",
                        "subsection": subsection2_used,
                        "field_path": None,
                        "validation_error": None,
                    }
                else:
                    logger.warning(f"Strict fix validation failed: {error}")

            except Exception as e:
                logger.error(f"Strict fix error: {e}")

        # === PHASE 2: Surgical Field Fix ===
        logger.info(f"Attempting surgical fix for {target_name}")

        try:
            # Extract likely field path
            field_path = extract_field_path_from_issue(issue, target_content)

            if not field_path:
                logger.error("Could not identify field path for surgical fix")
                return None

            current_val = get_nested_value(target_content, field_path)

            result = await LLMService.invoke(
                SURGICAL_FIELD_FIX_PROMPT,
                {
                    "field_path": field_path,
                    "current_value": json.dumps(current_val),
                    "reference_value": str(source_content)[:500],
                    "issue_description": issue,
                },
                provider="claude",
                parse_json=True,
            )

            new_field_path = result.get("field_path", field_path)
            new_value = result.get("new_value")

            if new_value is not None:
                # Apply patch
                patched = set_nested_value(target_content, new_field_path, new_value)

                # Validate
                is_valid, error = validate_module_data(target_state_key, patched)

                if is_valid:
                    logger.info(
                        f"✓ Surgical fix successful: {target_name}.{new_field_path}"
                    )
                    return {
                        "target_module": target_name,
                        "target_state_key": target_state_key,
                        "fixed_content": patched,
                        "fix_type": "surgical",
                        "subsection": subsection2,
                        "field_path": new_field_path,
                        "validation_error": None,
                    }
                else:
                    logger.error(f"Surgical fix validation failed: {error}")

        except Exception as e:
            logger.error(f"Surgical fix error: {e}")

        logger.error(f"✗ All fix attempts failed for {target_name}")
        return {
            "target_module": target_name,
            "target_state_key": target_state_key,
            "fixed_content": None,
            "fix_type": "failed",
            "subsection": subsection2,
            "field_path": None,
            "validation_error": "Both strict and surgical fixes failed validation",
        }

    except Exception as e:
        logger.error(f"Smart fix failed with exception: {e}")
        return None
