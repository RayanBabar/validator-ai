"""
Scoring functions for startup validation.
Calculates viability scores (free tier) and Go/No-Go scores (paid tiers).
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# ===========================================
# VIABILITY SCORE WEIGHTS (Free Tier)
# ===========================================
VIABILITY_WEIGHTS = {
    "problem_severity": 0.30,      # 30%
    "market_opportunity": 0.25,    # 25%
    "competition_intensity": 0.20, # 20%
    "execution_complexity": 0.15,  # 15%
    "founder_alignment": 0.10      # 10%
}

# ===========================================
# GO/NO-GO SCORE WEIGHTS (Paid Tiers)
# ===========================================
GO_NO_GO_WEIGHTS = {
    "market_demand": 0.25,          # 25%
    "financial_viability": 0.20,    # 20%
    "competition_analysis": 0.15,   # 15%
    "founder_market_fit": 0.10,     # 10%
    "technical_feasibility": 0.10,  # 10%
    "regulatory_compliance": 0.10,  # 10%
    "timing_assessment": 0.05,      # 5%
    "scalability_potential": 0.05   # 5%
}

# ===========================================
# SCORING THRESHOLDS
# ===========================================
# 0-35:   quit
# 36-60:  premium
# 61-85:  standard
# 86-100: basic
SCORE_QUIT_THRESHOLD = 35
SCORE_PREMIUM_THRESHOLD = 60
SCORE_STANDARD_THRESHOLD = 85
GAUGE_PROMISING_THRESHOLD = 70

# ===========================================
# INVERSE SCORED METRICS (high = bad)
# These metrics should be inverted: 10 - score
# ===========================================
INVERSE_SCORED_METRICS = {
    # Free tier metrics where high score = bad outcome
    "competition_intensity",    # High competition is bad
    "execution_complexity",     # High complexity is bad
    # Paid tier metrics where high score = bad outcome
    "competition_analysis",     # High competition is bad
}


# ===========================================
# DIMENSION QUALITY MAPPING
# Maps interview quality dimensions to viability score dimensions
# ===========================================
DIMENSION_QUALITY_MAP = {
    "problem_severity": "problem_understanding",
    "market_opportunity": "market_knowledge",
    "competition_intensity": "competitive_awareness",
    "execution_complexity": "execution_readiness",
    "founder_alignment": "founder_credibility",
}


def calculate_viability_score(
    scores: Dict[str, float],
    clarity_score: float = None,
    answer_quality_score: float = None,
    dimension_quality: Dict[str, float] = None
) -> tuple[float, Dict[str, int]]:
    """
    Calculate FREE TIER 'AI Viability Score' (0-100).
    
    Based on 5 Quick-Assessment Dimensions:
    - Problem Severity (30%) - high = good
    - Market Opportunity (25%) - high = good
    - Competition Intensity (20%) - high = BAD (inverted)
    - Execution Complexity (15%) - high = BAD (inverted)
    - Founder Alignment (10%) - high = good
    
    NEW: Interview quality adjusts INDIVIDUAL dimension scores BEFORE weighted calculation.
    Each dimension is scaled by its corresponding interview quality factor:
    - Quality 0/10 → dimension score × 0.7 (30% penalty)
    - Quality 5/10 → dimension score × 0.85 (15% penalty)
    - Quality 10/10 → dimension score × 1.0 (no penalty)
    
    Mapping:
    - problem_severity ← problem_understanding quality
    - market_opportunity ← market_knowledge quality
    - competition_intensity ← competitive_awareness quality
    - execution_complexity ← execution_readiness quality
    - founder_alignment ← founder_credibility quality
    
    Args:
        scores: Dictionary with dimension names and scores (0-10 scale)
        clarity_score: Optional business idea clarity score (0-10) - for logging only
        answer_quality_score: Optional answer quality score (0-10) - for logging only
        dimension_quality: Optional dict of dimension-specific quality scores (0-10)
                          Keys: problem_understanding, market_knowledge, competitive_awareness,
                                execution_readiness, founder_credibility
        
    Returns:
        Tuple of (final_score, adjusted_scores):
        - final_score: Final viability score (0-100 scale, rounded to 1 decimal)
        - adjusted_scores: Dictionary of adjusted integer scores (0-10 scale) for each dimension
    """
    # Default dimension quality to neutral if not provided
    if dimension_quality is None:
        dimension_quality = {
            "problem_understanding": 5.0,
            "market_knowledge": 5.0,
            "competitive_awareness": 5.0,
            "execution_readiness": 5.0,
            "founder_credibility": 5.0,
        }
    
    # FLOW: LLM scores → penalty → round (display) → invert display → calculate
    adjustments_log = []
    display_scores = {}   # Scores shown in report: raw + quality penalty, rounded
    calc_scores = {}      # Scores for calculation: display inverted where needed
    
    for dimension, weight in VIABILITY_WEIGHTS.items():
        # Helper to extract score whether it's int/float or Dict
        raw_val = scores.get(dimension)
        raw_score = 5.0
        reasoning = ""
        
        if isinstance(raw_val, (int, float)):
            raw_score = float(raw_val)
        elif isinstance(raw_val, dict):
            raw_score = float(raw_val.get("score", 5))
            reasoning = raw_val.get("reasoning", "")
        # Handle object case if needed (though usually passed as dict here)
        elif hasattr(raw_val, "score"):
            raw_score = float(raw_val.score)
            reasoning = getattr(raw_val, "reasoning", "")

        # Get corresponding quality factor for this dimension
        quality_key = DIMENSION_QUALITY_MAP.get(dimension)
        quality_factor = float(dimension_quality.get(quality_key, 5.0))
        
        # Calculate quality adjustment multiplier: 0.7 to 1.0 based on quality (0-10)
        # Quality 0 → 0.7 (30% penalty)
        # Quality 5 → 0.85 (15% penalty) 
        # Quality 10 → 1.0 (no penalty)
        quality_multiplier = 0.7 + (0.3 * quality_factor / 10.0)
        
        # apply specific context penalties?
        context_score = float(dimension_quality.get("context_specificity_score", 10.0)) # Default to 10 if not present (legacy compat)
        if context_score < 5.0 and dimension in ["market_opportunity", "problem_severity"]:
             # If context (geography/industry) is vague, penalize market and problem scores
             # Vague context makes market sizing and problem validation unreliable
             logger.warning(f"Applying context penalty to {dimension} due to low specificity ({context_score})")
             quality_multiplier *= 0.85  # Additional 15% penalty
        
        # Step 1 & 2: Apply quality penalty to raw score
        quality_adjusted = raw_score * quality_multiplier
        
        # Step 3: Round and clamp for DISPLAY (this goes in the report)
        final_display_score = int(round(min(max(quality_adjusted, 0), 10)))
        display_scores[dimension] = {"score": final_display_score, "reasoning": reasoning}
        
        # Step 4: Invert DISPLAY score for calculation (where high = bad)
        if dimension in INVERSE_SCORED_METRICS:
            calc_scores[dimension] = 10 - final_display_score  # Invert the display score
        else:
            calc_scores[dimension] = final_display_score
        
        adjustments_log.append(f"{dimension}: raw={raw_score:.0f} → display={final_display_score} → calc={calc_scores[dimension]}")
    
    # Step 5: Calculate total from calc_scores (with inversion applied to display values)
    total = 0.0
    for dimension, weight in VIABILITY_WEIGHTS.items():
        total += calc_scores[dimension] * weight
    
    # Scale to 0-100
    final_score = round(min(max(total * 10, 0), 100), 1)
    
    logger.debug(f"Viability score: {final_score}")
    logger.debug(f"Score adjustments: {', '.join(adjustments_log)}")
    if clarity_score is not None:
        logger.debug(f"Interview quality context: clarity={clarity_score}, answer_quality={answer_quality_score}")
    
    # Return display_scores for report output
    return final_score, display_scores


def calculate_go_no_go_score(scores: Dict[str, float]) -> tuple[float, Dict[str, int]]:
    """
    Calculate PAID TIER 'Go/No-Go Recommendation Score' (0-100).
    
    FLOW: LLM scores → round (display) → invert display → calculate
    
    Based on 8 Scoring Dimensions:
    - Market Demand (25%) - high = good
    - Financial Viability (20%) - high = good
    - Competition Analysis (15%) - high = BAD (inverted internally)
    - Founder-Market Fit (10%) - high = good
    - Technical Feasibility (10%) - high = good
    - Regulatory Compliance (10%) - high = good
    - Timing Assessment (5%) - high = good
    - Scalability Potential (5%) - high = good
    
    Args:
        scores: Dictionary with dimension names and scores (0-10 scale)
        
    Returns:
        Tuple of (final_score, display_scores):
        - final_score: Final Go/No-Go score (0-100 scale, rounded to 1 decimal)
        - display_scores: Dictionary of integer scores for report (NOT inverted)
    """
    # FLOW: LLM scores → round (display) → invert display → calculate
    display_scores = {}  # Scores shown in report: rounded, NOT inverted
    calc_scores = {}     # Scores for calculation: display inverted where needed
    
    for dimension, weight in GO_NO_GO_WEIGHTS.items():
        # Helper to extract score whether it's int/float or Dict
        raw_val = scores.get(dimension)
        raw_score = 5.0
        reasoning = ""
        
        if isinstance(raw_val, (int, float)):
            raw_score = float(raw_val)
        elif isinstance(raw_val, dict):
            raw_score = float(raw_val.get("score", 5))
            reasoning = raw_val.get("reasoning", "")
        elif hasattr(raw_val, "score"):
            raw_score = float(raw_val.score)
            reasoning = getattr(raw_val, "reasoning", "")
        
        # Step 1: Round raw score for DISPLAY (this goes in the report)
        final_display_score = int(round(min(max(raw_score, 0), 10)))
        display_scores[dimension] = {"score": final_display_score, "reasoning": reasoning}
        
        # Step 2: Invert DISPLAY score for calculation (where high = bad)
        if dimension in INVERSE_SCORED_METRICS:
            calc_scores[dimension] = 10 - final_display_score  # Invert the display score
        else:
            calc_scores[dimension] = final_display_score
    
    # Step 3: Calculate total from calc_scores (with inversion applied to display values)
    total = 0.0
    for dimension, weight in GO_NO_GO_WEIGHTS.items():
        total += calc_scores[dimension] * weight
    
    # Scale to 0-100 and round to 1 decimal place
    final_score = round(min(total * 10, 100), 1)
    
    logger.debug(f"Go/No-Go score calculated: {final_score} from {scores} (with inverse scoring for negative metrics)")
    # Return display_scores for report output
    return final_score, display_scores


def get_package_recommendation(viability_score: float) -> str:
    """
    Determine package recommendation based on viability score.
    
    Scoring Rules:
    - 0-35:   quit
    - 36-60:  premium
    - 61-85:  standard
    - 86-100: basic
    
    Args:
        viability_score: The calculated viability score (0-100)
        
    Returns:
        Recommended package tier: 'quit', 'premium', 'standard', or 'basic'
    """
    if viability_score <= SCORE_QUIT_THRESHOLD:
        return "quit"
    elif viability_score <= SCORE_PREMIUM_THRESHOLD:
        return "premium"
    elif viability_score <= SCORE_STANDARD_THRESHOLD:
        return "standard"
    else:
        return "basic"


def get_gauge_status(viability_score: float) -> str:
    """
    Determine gauge status based on viability score.
    
    Args:
        viability_score: The calculated viability score (0-100)
        
    Returns:
        Gauge status: 'Promising' or 'Needs Work'
    """
    return "Promising" if viability_score > GAUGE_PROMISING_THRESHOLD else "Needs Work"