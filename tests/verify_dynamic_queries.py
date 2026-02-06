import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

# Set dummy env vars to bypass Pydantic validation
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["TAVILY_API_KEY"] = "tvly-dummy"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy"

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.inputs import ValidationState, StartupSubmission
from src.agents.interviewer import synthesize_context

async def run_verification():
    print("🚀 Starting Dynamic Query Verification...")

    # Mock State
    mock_input = StartupSubmission(
        detailed_description="I want to build a marketplace for used construction equipment in Germany.",
        industry="Construction",
        geography="Germany"
    )
    
    mock_state = ValidationState(
        inputs=mock_input,
        questions_asked=["Who is the target?"],
        user_answers=["Construction companies"],
        interview_phase="complete"
    )

    # Mock Results
    mock_extraction_result = {
        "primary_geography": "Germany",
        "primary_industry": "Construction",
        "refined_industry_context": "Heavy Equipment Marketplace",
        "optimized_search_keywords": ["excavator sales", "construction machinery market"],
        "context_confidence": 9.0
    }

    mock_query_result = {
        "market_research": "Germany construction equipment market size 2024 resale trends",
        "competitor_research": "used machinery marketplaces Germany vs Mascus vs Ritchie Bros",
        "industry_research": "German construction industry digitalization trends 2025"
    }

    mock_search_result = {
        "market_research": "Market is growing...",
        "competitor_research": "Strong competition...",
        "industry_research": "Digital adoption rising..."
    }

    # Patch dependencies
    with patch('src.agents.interviewer.LLMService.invoke') as mock_llm, \
         patch('src.agents.interviewer.conduct_dynamic_research') as mock_search:

        # Setup Mock Side Effects
        def llm_side_effect(prompt, *args, **kwargs):
            prompt_str = str(prompt)
            if "INITIAL_CONTEXT_EXTRACTION_PROMPT" in str(prompt) or "extract" in str(prompt).lower():
                return mock_extraction_result
            elif "DYNAMIC_RESEARCH_OBJECTIVES_PROMPT" in str(prompt) or "Request for Information" in str(prompt):
                 print("\n✅ dynamic query prompt detected!")
                 return mock_query_result
            else:
                return {} # Synthesis prompt fallback

        mock_llm.side_effect = llm_side_effect
        mock_search.return_value = mock_search_result

        # Run Synthesis
        print("\nrunning synthesize_context()...")
        await synthesize_context(mock_state)

        # Verify LLM Call for Dynamic Queries
        # We check if LLMService.invoke was called with the Dynamic Prompt
        dynamic_prompt_called = False
        for call in mock_llm.call_args_list:
            args, _ = call
            if "DYNAMIC_RESEARCH_OBJECTIVES_PROMPT" in str(args[0]) or "Request for Information" in str(args[0]):
                dynamic_prompt_called = True
                print(f"\n✨ Verified Call to Dynamic Prompt:")
                print(f"   Input Context: {args[1]}")
                break
        
        if dynamic_prompt_called:
            print("\nSUCCESS: Dynamic Query Generation Logic executed correctly.")
        else:
            print("\nFAILURE: Dynamic Query Prompt was NOT called.")

        # Verify Search Agent received dynamic queries
        search_call_args = mock_search.call_args[1]
        objectives = search_call_args['research_objectives']
        print(f"\n🔍 Search Agent Objectives Received:")
        print(f"   Market: {objectives['market_research']}")
        print(f"   Competitor: {objectives['competitor_research']}")
        print(f"   Trends: {objectives['industry_research']}")

        assert objectives['market_research'] == mock_query_result['market_research']
        print("\n✅ Verification PASSED: Search queries match dynamic output.")

if __name__ == "__main__":
    asyncio.run(run_verification())
