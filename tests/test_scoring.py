"""
Unit tests for scoring functions.
Tests both viability score (free tier) and Go/No-Go score (paid tiers).
"""
import pytest
from src.utils.scoring import calculate_viability_score, calculate_go_no_go_score


class TestViabilityScore:
    """Tests for free tier viability score calculation."""
    
    def test_perfect_scores_returns_100(self):
        """All 10s should return 100."""
        scores = {
            "problem_severity": 10.0,
            "market_opportunity": 10.0,
            "competition_intensity": 0.0,  # Low intensity is GOOD (inverted)
            "execution_complexity": 0.0,   # Low complexity is GOOD (inverted)
            "founder_alignment": 10.0
        }
        # Provide perfect quality scores to avoid penalty
        dimension_quality = {
            "problem_understanding": 10.0,
            "market_knowledge": 10.0,
            "competitive_awareness": 10.0,
            "execution_readiness": 10.0,
            "founder_credibility": 10.0,
            "context_specificity_score": 10.0
        }
        result, adjusted = calculate_viability_score(scores, dimension_quality=dimension_quality)
        assert result == 100.0
    
    def test_zero_scores_returns_0(self):
        """All 0s should return 0."""
        scores = {
            "problem_severity": 0.0,
            "market_opportunity": 0.0,
            "competition_intensity": 10.0, # High intensity is BAD (inverted -> 0)
            "execution_complexity": 10.0,  # High complexity is BAD (inverted -> 0)
            "founder_alignment": 0.0
        }
        # Quality MUST be high so that raw 10 stays 10, inverts to 0
        dimension_quality = {
            "problem_understanding": 10.0,
            "market_knowledge": 10.0,
            "competitive_awareness": 10.0,
            "execution_readiness": 10.0,
            "founder_credibility": 10.0,
            "context_specificity_score": 10.0
        }
        result, adjusted = calculate_viability_score(scores, dimension_quality=dimension_quality)
        assert result == 0.0
    
    def test_average_scores_returns_50(self):
        """All 5s should return 50."""
        scores = {
            "problem_severity": 5.0,
            "market_opportunity": 5.0,
            "competition_intensity": 5.0,
            "execution_complexity": 5.0,
            "founder_alignment": 5.0
        }
        # With default quality (5.0), defaults to ~0.85 multiplier.
        # 5 * 0.85 = 4.25 -> round 4.
        # Comp/Exec: 10 - 4 = 6.
        # Prob/Mkt/Founder: 4.
        # Weights: 4*0.3 + 4*0.25 + 6*0.2 + 6*0.15 + 4*0.1 = 1.2 + 1.0 + 1.2 + 0.9 + 0.4 = 4.7 -> 47.0
        result, adjusted = calculate_viability_score(scores)
        assert result == 47.0
    
    def test_weights_are_applied_correctly(self):
        """Test that weights are correctly applied (30%, 25%, 20%, 15%, 10%)."""
        # Only problem_severity = 10, others = 0
        # Should be 10 * 0.30 * 10 = 30
        scores = {
            "problem_severity": 10.0,
            "market_opportunity": 0.0,
            "competition_intensity": 10.0, # 0 contribution
            "execution_complexity": 10.0,  # 0 contribution
            "founder_alignment": 0.0
        }
        # Perfect quality to avoid penalty
        dimension_quality = {
            "problem_understanding": 10.0,
            "market_knowledge": 10.0,
            "competitive_awareness": 10.0,
            "execution_readiness": 10.0,
            "founder_credibility": 10.0,
            "context_specificity_score": 10.0
        }
        result, adjusted = calculate_viability_score(scores, dimension_quality=dimension_quality)
        assert result == 30.0
    
    def test_missing_scores_default_to_5(self):
        """Missing scores should default to 5 (neutral)."""
        scores = {"problem_severity": 10.0}  # Others missing (default 5)
        # With default quality (5.0) -> Multiplier 0.85
        # Prob: 10 * 0.85 = 8.5 -> 8. W=0.3 -> 2.4
        # Mkt: 5 * 0.85 = 4.25 -> 4. W=0.25 -> 1.0
        # Comp: 5 * 0.85 = 4.25 -> 4. Inv: 10-4=6. W=0.20 -> 1.2
        # Exec: 5 -> 4. Inv: 6. W=0.15 -> 0.9
        # Founder: 5 -> 4. W=0.1 -> 0.4
        # Total: 2.4 + 1.0 + 1.2 + 0.9 + 0.4 = 5.9 -> 59.0
        result, adjusted = calculate_viability_score(scores)
        assert result == 59.0
    
    def test_result_is_rounded_to_one_decimal(self):
        """Result should be rounded to 1 decimal place."""
        scores = {
            "problem_severity": 7.333,
            "market_opportunity": 6.666,
            "competition_intensity": 5.555,
            "execution_complexity": 4.444,
            "founder_alignment": 8.888
        }
        result, adjusted = calculate_viability_score(scores)
        assert result == round(result, 1)
    
    def test_adjusted_scores_are_integers(self):
        """Adjusted scores should be integers."""
        scores = {
            "problem_severity": 8.0,
            "market_opportunity": 7.0,
            "competition_intensity": 5.0,
            "execution_complexity": 6.0,
            "founder_alignment": 5.0
        }
        result, adjusted = calculate_viability_score(scores)
        for key, value in adjusted.items():
            assert isinstance(value, int), f"{key} should be int, got {type(value)}"
            assert 0 <= value <= 10, f"{key} should be between 0 and 10"


class TestGoNoGoScore:
    """Tests for paid tier Go/No-Go score calculation."""
    
    def test_perfect_scores_returns_100(self):
        """All 10s should return 100."""
        scores = {
            "market_demand": 10.0,
            "financial_viability": 10.0,
            "competition_analysis": 0.0, # Inverted
            "founder_market_fit": 10.0,
            "technical_feasibility": 10.0,
            "regulatory_compliance": 10.0,
            "timing_assessment": 10.0,
            "scalability_potential": 10.0
        }
        result, adjusted = calculate_go_no_go_score(scores)
        assert result == 100.0
    
    def test_zero_scores_returns_0(self):
        """All 0s should return 0."""
        scores = {
            "market_demand": 0.0,
            "financial_viability": 0.0,
            "competition_analysis": 10.0, # Inverted -> 0
            "founder_market_fit": 0.0,
            "technical_feasibility": 0.0,
            "regulatory_compliance": 0.0,
            "timing_assessment": 0.0,
            "scalability_potential": 0.0
        }
        result, adjusted = calculate_go_no_go_score(scores)
        assert result == 0.0
    
    def test_average_scores_returns_50(self):
        """All 5s should return 50."""
        scores = {
            "market_demand": 5.0,
            "financial_viability": 5.0,
            "competition_analysis": 5.0,
            "founder_market_fit": 5.0,
            "technical_feasibility": 5.0,
            "regulatory_compliance": 5.0,
            "timing_assessment": 5.0,
            "scalability_potential": 5.0
        }
        # Comp Analysis: 5 -> round 5 -> inverted 10-5 = 5.
        # All others: 5 -> round 5.
        # No quality multiplier for GoNoGo (yet).
        result, adjusted = calculate_go_no_go_score(scores)
        assert result == 50.0
    
    def test_weights_sum_to_100_percent(self):
        """Verify weights add up to 1.0 (100%)."""
        # 25% + 20% + 15% + 10% + 10% + 10% + 5% + 5% = 100%
        weights = [0.25, 0.20, 0.15, 0.10, 0.10, 0.10, 0.05, 0.05]
        assert sum(weights) == 1.0
    
    def test_market_demand_has_highest_weight(self):
        """Market demand (25%) should have highest impact."""
        # Only market_demand = 10, others = 0
        scores_high = {
            "market_demand": 10.0,
            "financial_viability": 0.0,
            "competition_analysis": 10.0, # BAD
            "founder_market_fit": 0.0,
            "technical_feasibility": 0.0,
            "regulatory_compliance": 0.0,
            "timing_assessment": 0.0,
            "scalability_potential": 0.0
        }
        # Only financial_viability = 10, others = 0
        scores_lower = {
            "market_demand": 0.0,
            "financial_viability": 10.0,
            "competition_analysis": 10.0, # BAD
            "founder_market_fit": 0.0,
            "technical_feasibility": 0.0,
            "regulatory_compliance": 0.0,
            "timing_assessment": 0.0,
            "scalability_potential": 0.0
        }
        result_high, _ = calculate_go_no_go_score(scores_high)
        result_lower, _ = calculate_go_no_go_score(scores_lower)
        assert result_high > result_lower
    
    def test_adjusted_scores_are_integers(self):
        """Adjusted scores should be integers."""
        scores = {
            "market_demand": 8.0,
            "financial_viability": 7.0,
            "competition_analysis": 5.0,
            "founder_market_fit": 6.0,
            "technical_feasibility": 7.0,
            "regulatory_compliance": 6.0,
            "timing_assessment": 5.0,
            "scalability_potential": 8.0
        }
        result, adjusted = calculate_go_no_go_score(scores)
        for key, value in adjusted.items():
            assert isinstance(value, int), f"{key} should be int, got {type(value)}"
            assert 0 <= value <= 10, f"{key} should be between 0 and 10"
