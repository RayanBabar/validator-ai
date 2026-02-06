import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Set dummy env vars to bypass Pydantic validation
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["TAVILY_API_KEY"] = "tvly-dummy"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy"

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.search.research import dynamic_research

async def run_verification():
    print("🚀 Starting Search Retry Verification...")

    # Scenario: Specific query returns nothing, triggering Broad Retry
    
    with patch('src.agents.search.research.generate_llm_queries') as mock_gen_queries, \
         patch('src.agents.search.research.search_with_tavily_detailed') as mock_tavily, \
         patch('src.agents.search.research.score_source_credibility') as mock_score:

        # 1. Setup Query Generation
        # First call (Standard): Returns specific query
        # Second call (Retry): Returns broad query
        mock_gen_queries.side_effect = [
            ["specific_query_1"], # Initial specific query
            ["broad_query_1"]     # Fallback broad query
        ]

        # 2. Setup Tavily Search Results
        # First call (Specific): Returns empty list or garbage
        # Second call (Broad): Returns valid content
        mock_tavily.side_effect = [
            [], # Specific query fails
            [{"url": "http://broad.com", "content": "General overview of the topic."}] # Broad query succeeds
        ]

        # 3. Setup Credibility Scoring
        # Always return valid score to pass filters
        mock_score.return_value = (5, "medium")

        print("\nrunning dynamic_research() with forced failure on first attempt...")
        result = await dynamic_research(
            description="Niche startup idea", 
            research_objective="market size of underwater basket weaving in Mars",
            num_queries=1
        )

        # Verification Logic
        print("\n🔍 Execution Analysis:")
        
        # Check if generate_llm_queries was called twice (Initial + Retry)
        if mock_gen_queries.call_count == 2:
            print("✅ SUCCESS: Query generator called twice (Initial + Retry).")
        else:
            print(f"❌ FAILURE: Query generator called {mock_gen_queries.call_count} times (Expected 2).")

        # Check if broader query was executed
        expected_retry_prompt = "Broad overview of market size of underwater basket weaving in Mars (GENERAL TERMS ONLY)"
        retry_call_args = mock_gen_queries.call_args_list[1]
        
        # Args are (description, objective, num_queries)
        actual_retry_prompt = retry_call_args[0][1]
        
        if expected_retry_prompt == actual_retry_prompt:
             print("✅ SUCCESS: Retry prompt matched broad fallback template.")
        else:
             print(f"❌ FAILURE: Retry prompt mismatch.\nExpected: {expected_retry_prompt}\nActual: {actual_retry_prompt}")

        # Check Output
        if "[BROAD RETRY SOURCE]" in result:
             print("✅ SUCCESS: Output contains Broad Retry indicator.")
        else:
             print(f"❌ FAILURE: Output missing retry indicator.\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(run_verification())
