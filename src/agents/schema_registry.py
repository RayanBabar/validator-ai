"""
Schema Registry for module validation and consistency fixes.
Provides Pydantic model schemas and validation utilities.
"""

from typing import Type, Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, ValidationError
import copy
import logging

from src.models.outputs import (
    BMCModule,
    MarketModule,
    CompetitorModule,
    FinancialsModule,
    TechModule,
    RegulatoryModule,
    GTMModule,
    RiskModule,
    RoadmapModule,
    FundingModule,
)

logger = logging.getLogger(__name__)

# State key → Pydantic model mapping
STATE_KEY_TO_MODEL: Dict[str, Type[BaseModel]] = {
    "bmc_data": BMCModule,
    "market_data": MarketModule,
    "competitor_data": CompetitorModule,
    "financial_data": FinancialsModule,
    "tech_data": TechModule,
    "reg_data": RegulatoryModule,
    "gtm_data": GTMModule,
    "risk_data": RiskModule,
    "roadmap_data": RoadmapModule,
    "funding_data": FundingModule,
}

# LLM-friendly name → (state_key, subsection_path)
MODULE_NAME_MAP: Dict[str, Tuple[str, Optional[str]]] = {
    "bmc": ("bmc_data", None),
    "business_model_canvas": ("bmc_data", None),
    "customer": ("bmc_data", "customer_segments"),
    "customer_segments": ("bmc_data", "customer_segments"),
    "market": ("market_data", None),
    "market_analysis": ("market_data", None),
    "competition": ("competitor_data", None),
    "competitors": ("competitor_data", None),
    "competitive_intelligence": ("competitor_data", None),
    "finance": ("financial_data", None),
    "financials": ("financial_data", None),
    "financial_feasibility": ("financial_data", None),
    "tech": ("tech_data", None),
    "technical_requirements": ("tech_data", None),
    "technical": ("tech_data", None),
    "regulatory": ("reg_data", None),
    "compliance": ("reg_data", None),
    "gtm": ("gtm_data", None),
    "go_to_market": ("gtm_data", None),
    "risk": ("risk_data", None),
    "risks": ("risk_data", None),
    "roadmap": ("roadmap_data", None),
    "implementation_roadmap": ("roadmap_data", None),
    "funding": ("funding_data", None),
    "funding_strategy": ("funding_data", None),
}


# ===========================================
# MODULE AUTHORITY RULES
# ===========================================
# Module authority hierarchy: modules that OTHER modules should yield to
# When there's a conflict, the module with higher authority "wins"
# and the other module should be adapted

MODULE_AUTHORITY_RULES: Dict[str, List[str]] = {
    "market_data": ["financial_data", "roadmap_data", "gtm_data", "bmc_data"],
    "competitor_data": ["market_data", "gtm_data", "financial_data"],
    "tech_data": ["roadmap_data", "financial_data", "bmc_data", "funding_data"],
    "bmc_data": ["market_data", "gtm_data", "financial_data", "roadmap_data"],
    "reg_data": ["bmc_data", "financial_data", "tech_data", "roadmap_data"],
    "risk_data": ["roadmap_data", "financial_data", "bmc_data"],
    "financial_data": [],  # Usually adapts to other modules
    "roadmap_data": [],  # Usually adapts to tech complexity
    "gtm_data": [],  # Usually adapts to customer segments
    "funding_data": [
        "financial_data",
        "roadmap_data",
    ],  # Funding goals can drive financial projections
}

# Field-level authority: specific fields in target module that can be overridden
# when source_module is the authority
FIELD_AUTHORITY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "financial_data": {
        "projected_revenue": "market_data",
        "revenue_projections": "market_data",
        "timeline": "tech_data",
        "development_cost": "tech_data",
        "team_size": "bmc_data",
    },
    "roadmap_data": {
        "milestones": "tech_data",
        "timeline": "tech_data",
        "development_phases": "tech_data",
    },
    "gtm_data": {
        "target_segments": "bmc_data",
        "customer_acquisition": "bmc_data",
        "pricing": "financial_data",
        "sales_strategy": "competitor_data",
    },
    "bmc_data": {
        "customer_segments": "market_data",
        "value_propositions": "competitor_data",
    },
}


def determine_fix_target(
    module_a: str,
    module_b: str,
    issue_type: str = "",
) -> Tuple[Optional[str], str]:
    """
    Determine which module should be fixed based on authority rules.
    """
    key_a, _ = resolve_module_name(module_a)
    key_b, _ = resolve_module_name(module_b)

    key_a = key_a or module_a
    key_b = key_b or module_b

    authority_a = MODULE_AUTHORITY_RULES.get(key_a, [])
    authority_b = MODULE_AUTHORITY_RULES.get(key_b, [])

    # Authority check: A over B or B over A
    if key_b in authority_a:
        return key_b, f"{key_a} is authoritative source"
    if key_a in authority_b:
        return key_a, f"{key_b} is authoritative source"

    return key_b, "default fallback"


def get_allowed_fields_to_modify(
    target_module: str,
    source_module: str,
) -> List[str]:
    """
    Get list of fields that can be safely modified in target module.
    """
    overrides = FIELD_AUTHORITY_OVERRIDES.get(target_module, {})

    allowed = [
        field
        for field, authority in overrides.items()
        if authority in source_module or source_module in authority
    ]

    return allowed if allowed else ["*"]


def get_authority_context_string(
    target_module: str,
    source_module: str,
) -> str:
    """
    Generate human-readable authority context for prompts.

    Args:
        target_module: Module being fixed
        source_module: Authority module

    Returns:
        Formatted string for prompt
    """
    allowed = get_allowed_fields_to_modify(target_module, source_module)

    if "*" in allowed:
        return f"Target: {target_module}. Source of truth: {source_module}. You may modify any fields to align with {source_module}."

    allowed_str = ", ".join(allowed)
    return f"Target: {target_module}. Source of truth: {source_module}. You may ONLY modify these fields: {allowed_str}. Preserve all other fields exactly."


class IssueSeverity:
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


CRITICAL_PATTERNS = [
    "b2b",
    "b2c",
    "enterprise",
    "consumer",  # Business model mismatch
    "magnitude",
    "order of",
    "10x",
    "100x",  # Order of magnitude
    "billion",
    "trillion",  # Scale mismatches
    "contradict",
    "conflict",
    "opposite",  # Direct contradictions
    "impossible",
    "invalid",  # Invalid data
]

MAJOR_PATTERNS = [
    "missing",
    "required",
    "not found",  # Moved from CRITICAL — too common in LLM issue text
    "error",  # Moved from CRITICAL — too broad
    "30%",
    "40%",
    "50%",  # Large variance
    "timeline",
    "schedule",
    "delay",  # Timeline issues
    "customer",
    "segment",
    "target",  # Customer mismatch
    "revenue",
    "cost",
    "profit",  # Financial variance
]


def get_schema_for_module(state_key: str) -> Optional[Dict[str, Any]]:
    """Get JSON schema for a state key."""
    model = STATE_KEY_TO_MODEL.get(state_key)
    return model.model_json_schema() if model else None


def validate_module_data(
    state_key: str, data: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Strictly validate module data against Pydantic schema.

    Returns:
        (is_valid, error_message or None)
    """
    model = STATE_KEY_TO_MODEL.get(state_key)
    if not model:
        return False, f"Unknown state key: {state_key}"

    try:
        model.model_validate(data)
        return True, None
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            errors.append(f"{loc}: {err['msg']}")
        return False, "; ".join(errors)


def resolve_module_name(name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve LLM-returned module name to state key and subsection.

    Returns:
        (state_key, subsection_path or None)
    """
    name_lower = name.lower().strip()

    # Direct lookup
    if name_lower in MODULE_NAME_MAP:
        return MODULE_NAME_MAP[name_lower]

    # Case-insensitive search
    for key, value in MODULE_NAME_MAP.items():
        if key.lower() == name_lower:
            return value

    # Fuzzy match - try to find containing key
    for key, value in MODULE_NAME_MAP.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return value

    return None, None


def classify_issue_severity(issue_description: str) -> str:
    """Classify issue severity based on description keywords."""
    issue_lower = issue_description.lower()

    for pattern in CRITICAL_PATTERNS:
        if pattern in issue_lower:
            return IssueSeverity.CRITICAL

    for pattern in MAJOR_PATTERNS:
        if pattern in issue_lower:
            return IssueSeverity.MAJOR

    return IssueSeverity.MINOR


def get_nested_value(data: Dict, path: str) -> Any:
    """Get value at dot-notation path (e.g., 'customer_segments.primary')."""
    if not path:
        return data

    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None

    return current


def set_nested_value(data: Dict, path: str, value: Any) -> Dict:
    """Set value at dot-notation path, returning deep copy."""
    result = copy.deepcopy(data)
    if not path:
        return result

    keys = path.split(".")
    current = result

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
    return result


def flatten_dict_keys(data: Dict, parent: str = "") -> List[str]:
    """Flatten nested dict to dot-notation keys."""
    keys = []
    for k, v in data.items():
        full_key = f"{parent}.{k}" if parent else k
        if isinstance(v, dict) and v:  # Only recurse into non-empty dicts
            keys.extend(flatten_dict_keys(v, full_key))
        else:
            keys.append(full_key)
    return keys


def extract_field_path_from_issue(issue: str, content: Dict) -> Optional[str]:
    """
    Extract likely field path from issue description.

    Args:
        issue: Issue description from consistency check
        content: Module content to validate against

    Returns:
        Dot-notation field path or None
    """
    import re

    # Look for quoted field names
    quoted = re.findall(r'"([^"]+)"', issue)
    for q in quoted:
        if len(q) > 2:  # Avoid single chars
            # Check if it's a valid path in content
            if get_nested_value(content, q) is not None:
                return q

    # Look for common field patterns
    flat_keys = flatten_dict_keys(content)
    issue_lower = issue.lower()

    # Prioritize longer matches (more specific)
    flat_keys.sort(key=len, reverse=True)

    for key in flat_keys:
        key_lower = key.lower()
        # Check if key or parent mentioned in issue
        key_parts = key_lower.split(".")
        for part in key_parts:
            if part in issue_lower:
                return key
        if key_lower.replace("_", " ") in issue_lower:
            return key

    # Return first available field as fallback
    if flat_keys:
        # Prefer top-level fields
        top_level = [k for k in flat_keys if "." not in k]
        if top_level:
            return top_level[0]
        return flat_keys[0]

    return None
