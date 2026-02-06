"""
Shared fixtures and configuration for all tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.models.inputs import StartupSubmission, ValidationState


@pytest.fixture
def sample_startup_input():
    """Sample startup submission for testing."""
    return StartupSubmission(
        detailed_description="Smart collar for dogs that monitors health metrics using AI and IoT sensors to track vital signs and activity levels in the European pet technology market"
    )


@pytest.fixture
def sample_state(sample_startup_input):
    """Sample validation state for testing."""
    return {
        "inputs": sample_startup_input,
        "questions_asked": ["What is your experience?", "What stage is your startup?"],
        "user_answers": ["10 years in veterinary", "MVP stage"],
        "interview_phase": "complete",
        "workflow_phase": "free_report",
        "search_context": "Pet health market is growing at 8% CAGR",
        "enriched_context": "Validated pet tech market with strong founder fit"
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for scoring."""
    return {
        "scores": {
            "problem_severity": 8.0,
            "market_opportunity": 7.5,
            "competition_intensity": 6.0,
            "execution_complexity": 7.0,
            "founder_alignment": 9.0
        },
        "value_prop": "AI-powered pet health monitoring",
        "customer_profile": "Tech-savvy dog owners aged 25-45",
        "what_if_scenario": "Expand to cats and other pets",
        "personalized_next_step": "Launch beta with 50 dog owners"
    }


@pytest.fixture
def mock_go_no_go_scores():
    """Mock Go/No-Go scores for paid tiers."""
    return {
        "market_demand": 8.0,
        "financial_viability": 7.0,
        "competition_analysis": 6.5,
        "founder_market_fit": 8.5,
        "technical_feasibility": 7.5,
        "regulatory_compliance": 6.0,
        "timing_assessment": 8.0,
        "scalability_potential": 7.0
    }


@pytest.fixture
def mock_tavily_search():
    """Mock Tavily search results."""
    async def mock_search(query: str) -> str:
        return f"Search results for: {query}. Market size is $5B growing at 10% CAGR."
    return mock_search
