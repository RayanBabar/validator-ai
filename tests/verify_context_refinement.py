import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

# Set dummy env vars
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["TAVILY_API_KEY"] = "tvly-dummy"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy"

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.inputs import ValidationState, StartupSubmission
from src.agents.interviewer import synthesize_context

async def test_smart_refinement():
    print("Testing Smart Context Refinement...")

    # Mock State
    mock_state = ValidationState(
        inputs=StartupSubmission(detailed_description="I want to build an AI app"),
        questions_asked=["What does it do?"],
        user_answers=["It writes blog posts."]
    )

    # Mock LLM Response for Extract Initial Context
    mock_extraction_response = {
        "primary_geography": "Global",
        "primary_industry": "AI",
        "refined_industry_context": "Generative AI for Content Marketing",
        "optimized_search_keywords": [
            "Generative AI content marketing market size 2024",
            "AI copywriting tools competitors",
            "LLM content generation trends"
        ],
        "regulatory_context": [],
        "context_confidence": 8.0
    }

    # Mock LLM Response for Synthesis (not crucial for this test but needed to prevent errors)
    mock_synthesis_response = {
        "idea_title": "GenAI Writer",
        "problem_statement": "Writing is hard",
        "detailed_description": "A refined AI writer tool."
    }

    # Helper side_effect to return different mocks for different calls
    async def mock_llm_invoke(prompt, *args, **kwargs):
        # Identify which prompt is being called by checking prompt content or attributes
        # Since prompt objects are hard to compare directly, we'll assume:
        # First call is extraction, Second is synthesis
        return mock_extraction_response

    # We need to patch LLMService.invoke AND conduct_dynamic_research
    with patch("src.agents.base.LLMService.invoke") as mock_invoke, \
         patch("src.agents.search_agent.conduct_dynamic_research") as mock_research:
        
        # Setup mocks
        mock_invoke.side_effect = [mock_extraction_response, mock_synthesis_response]
        mock_research.return_value = {
            "market_research": "Huge market",
            "competitor_research": "Many competitors",
            "industry_research": "Growing fast"
        }

        # Run synthesis
        await synthesize_context(mock_state)

        # VERIFY: Did conduct_dynamic_research receive the OPTIMIZED queries?
        call_args = mock_research.call_args
        if not call_args:
            print("❌ conduct_dynamic_research was NOT called!")
            return

        kwargs = call_args.kwargs
        research_objectives = kwargs.get("research_objectives", {})
        
        print("\n--- Research Objectives Generated ---")
        for key, query in research_objectives.items():
            print(f"{key}: {query}")

        # Assertions
        expected_keywords = "Generative AI content marketing market size 2024"
        market_query = research_objectives.get("market_research", "")
        
        if expected_keywords in market_query:
            print("\n✅ SUCCESS: Research objectives contain optimized keywords!")
        else:
            print(f"\n❌ FAILURE: Expected '{expected_keywords}' in query, but got:\n{market_query}")

        expected_refined = "Generative AI for Content Marketing"
        if expected_refined in market_query:
             print("✅ SUCCESS: Refined industry context used!")
        else:
             print(f"❌ FAILURE: Expected '{expected_refined}' in query.")

if __name__ == "__main__":
    asyncio.run(test_smart_refinement())
