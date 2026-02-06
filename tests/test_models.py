"""
Unit tests for Pydantic models (inputs and outputs).
Tests validation, defaults, and schema compliance.
"""

import pytest
from pydantic import ValidationError
from src.models.inputs import StartupSubmission, SubmitInput, AnswerInput, UpgradeInput
from src.models.outputs import (
    ViabilityScores,
    GoNoGoScores,
    FreeReportOutput,
    BasicReportOutput,
    BusinessModelCanvas,
    MarketSize,
    Competitor,
)


class TestStartupSubmission:
    """Tests for StartupSubmission input model."""

    def test_valid_submission(self):
        """Valid submission with only required field (detailed_description)."""
        submission = StartupSubmission(
            detailed_description="A detailed description of the startup idea"
        )
        assert (
            submission.detailed_description
            == "A detailed description of the startup idea"
        )
        assert submission.tier == "free"  # Default

    def test_tier_default_is_free(self):
        """Tier should default to 'free'."""
        submission = StartupSubmission(detailed_description="Desc")
        assert submission.tier == "free"

    def test_missing_required_field_raises_error(self):
        """Missing detailed_description should raise ValidationError."""
        with pytest.raises(ValidationError):
            StartupSubmission()


class TestViabilityScores:
    """Tests for ViabilityScores model."""

    def test_valid_scores(self):
        """Valid scores within 0-10 range."""
        scores = ViabilityScores(
            problem_severity=8,
            market_opportunity=7,
            competition_intensity=6,
            execution_complexity=7,
            founder_alignment=9,
        )
        assert scores.problem_severity == 8

    def test_score_above_10_raises_error(self):
        """Score > 10 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ViabilityScores(
                problem_severity=15,  # Invalid
                market_opportunity=7,
                competition_intensity=6,
                execution_complexity=7,
                founder_alignment=9,
            )

    def test_score_below_0_raises_error(self):
        """Score < 0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ViabilityScores(
                problem_severity=-5,  # Invalid
                market_opportunity=7,
                competition_intensity=6,
                execution_complexity=7,
                founder_alignment=9,
            )


class TestGoNoGoScores:
    """Tests for GoNoGoScores model (8 dimensions)."""

    def test_valid_scores(self):
        """Valid Go/No-Go scores."""
        scores = GoNoGoScores(
            market_demand=8,
            financial_viability=7,
            competition_analysis=6,
            founder_market_fit=8,
            technical_feasibility=7,
            regulatory_compliance=6,
            timing_assessment=8,
            scalability_potential=7,
        )
        assert scores.market_demand == 8

    def test_all_8_dimensions_required(self):
        """All 8 dimensions are required."""
        with pytest.raises(ValidationError):
            GoNoGoScores(
                market_demand=8,
                # Missing 7 other dimensions
            )


class TestFreeReportOutput:
    """Tests for FreeReportOutput model."""

    def test_valid_free_report(self):
        """Valid free report output."""
        scores = ViabilityScores(
            problem_severity=8,
            market_opportunity=7,
            competition_intensity=6,
            execution_complexity=7,
            founder_alignment=9,
        )
        report = FreeReportOutput(
            title="My Startup",
            viability_score=75.0,
            gauge_status="Promising",
            scores=scores,
            value_proposition="AI-powered solution",
            customer_profile="Tech-savvy users",
            what_if_scenario="Pivot to B2B",
            package_recommendation="standard",
            personalized_next_step="Launch beta",
        )
        assert report.tier == "free"
        assert report.viability_score == 75.0

    def test_viability_score_capped_at_100(self):
        """Viability score should not exceed 100."""
        scores = ViabilityScores(
            problem_severity=10,
            market_opportunity=10,
            competition_intensity=10,
            execution_complexity=10,
            founder_alignment=10,
        )
        with pytest.raises(ValidationError):
            FreeReportOutput(
                viability_score=150.0,  # Invalid
                gauge_status="Promising",
                scores=scores,
                value_proposition="Test",
                customer_profile="Test",
                what_if_scenario="Test",
                package_recommendation="standard",
                personalized_next_step="Test",
            )


class TestBusinessModelCanvas:
    """Tests for BusinessModelCanvas model."""

    def test_valid_bmc(self):
        """Valid BMC with all 9 blocks."""
        bmc = BusinessModelCanvas(
            customer_segments=["SMBs", "Enterprise"],
            value_propositions=["Cost savings", "Efficiency"],
            channels=["Direct sales", "Partners"],
            customer_relationships=["Self-service", "Dedicated support"],
            revenue_streams=["Subscription", "Transaction fees"],
            key_resources=["Platform", "Team"],
            key_activities=["Development", "Sales"],
            key_partnerships=["Cloud providers", "Integrations"],
            cost_structure=["Hosting", "Salaries"],
        )
        assert len(bmc.customer_segments) == 2

    def test_all_9_blocks_required(self):
        """All 9 BMC blocks are required."""
        with pytest.raises(ValidationError):
            BusinessModelCanvas(
                customer_segments=["Test"],
                # Missing 8 other blocks
            )


class TestMarketSize:
    """Tests for MarketSize nested model."""

    def test_valid_market_size(self):
        """Valid market size with EUR value."""
        ms = MarketSize(
            value="500M EUR",
            details={
                "definition": "Pet owners in EU",
                "estimation_method": "Top-down",
                "cross_check": "Verified with Statista",
            },
            source=["Industry report 2024"],
        )
        assert ms.value == "500M EUR"


class TestCompetitor:
    """Tests for Competitor nested model."""

    def test_valid_competitor(self):
        """Valid competitor analysis."""
        comp = Competitor(
            name="CompetitorX",
            strengths=["Strong brand", "Large user base"],
            weaknesses=["Slow innovation", "High prices"],
            market_position="Market leader",
            pricing="Premium",
        )
        assert comp.name == "CompetitorX"
        assert len(comp.strengths) == 2
