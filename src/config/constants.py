"""
Application constants and configuration values.
Centralizes magic numbers and configuration for better maintainability.
"""
from enum import Enum
from typing import Literal
from src.config.constants_pricing import MODEL_PRICING, TAVILY_COST_PER_QUERY

# ===========================================
# TIER CONFIGURATION
# ===========================================
class TierType(str, Enum):
    """Supported tier types for validation."""
    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    CUSTOM = "custom"



# ===========================================
# INTERVIEW CONFIGURATION
# ===========================================
MIN_INTERVIEW_QUESTIONS = 5   # Minimum clarifying questions
MAX_INTERVIEW_QUESTIONS = 10  # Maximum clarifying questions based on complexity

# ===========================================
# SEARCH CONFIGURATION
# ===========================================
TAVILY_MAX_RESULTS = 5  # Maximum search results from Tavily
RESEARCH_CONTENT_LIMIT = 6000  # Character limit for research context
BASIC_RESEARCH_LIMIT = 3000  # Lighter limit for basic tier



# ===========================================
# STANDARD MODULES CONFIGURATION
# ===========================================
STANDARD_MODULE_NAMES = [
    "mod_bmc", "mod_market", "mod_comp", "mod_finance", "mod_tech",
    "mod_reg", "mod_gtm", "mod_risk", "mod_roadmap", "mod_funding"
]

# Module to data key mapping
MODULE_DATA_KEYS = {
    "mod_bmc": "bmc_data",
    "mod_market": "market_data",
    "mod_comp": "competitor_data",
    "mod_finance": "financial_data",
    "mod_tech": "tech_data",
    "mod_reg": "reg_data",
    "mod_gtm": "gtm_data",
    "mod_risk": "risk_data",
    "mod_roadmap": "roadmap_data",
    "mod_funding": "funding_data"
}

# ===========================================
# OUTPUT LENGTH CONSTRAINTS (Per Tiers.docx)
# ===========================================
# Approximate word counts for each tier output

# Free Tier: Half A4 page (~250-300 words)
FREE_TIER_MAX_WORDS = 300
FREE_VALUE_PROP_MAX_WORDS = 20  # 1 sentence
FREE_CUSTOMER_PROFILE_MAX_WORDS = 60  # 2-3 sentences
FREE_WHAT_IF_MAX_WORDS = 60  # 2-3 sentences
FREE_NEXT_STEP_MAX_WORDS = 40  # 1-2 sentences

# Basic Tier: 2-3 A4 pages (~1000-1500 words)
BASIC_TIER_MIN_WORDS = 1000
BASIC_TIER_MAX_WORDS = 1500
BASIC_EXEC_SUMMARY_WORDS = 500  # 2 paragraphs
BASIC_BMC_WORDS_PER_BLOCK = 80  # ~80 words per block = ~720 total for 9 blocks
DEFAULT_CURRENCY = "EUR"

# Standard/Premium Tier: 40-50 A4 pages (~20,000-25,000 words)
STANDARD_TIER_MIN_WORDS = 20000
STANDARD_TIER_MAX_WORDS = 25000
STANDARD_EXEC_SUMMARY_WORDS = 2500  # 5-page executive summary

# Standard Module Page Targets (for prompt guidance)
STANDARD_MODULE_PAGES = {
    "bmc": 2,           # 1-2 pages
    "market": 6,        # 5-7 pages
    "competitor": 5,    # 4-6 pages
    "finance": 6,       # 5-6 pages
    "tech": 4,          # 3-4 pages
    "regulatory": 4,    # 3-4 pages
    "gtm": 5,           # 4-5 pages
    "risk": 3,          # 2-3 pages
    "roadmap": 4,       # 3-4 pages
    "funding": 4        # 3-4 pages
}
