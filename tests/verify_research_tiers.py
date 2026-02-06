import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

# Set dummy env vars BEFORE importing src modules to avoid Pydantic validation errors
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["TAVILY_API_KEY"] = "tvly-dummy"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy"

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.search.research import conduct_dynamic_research, conduct_scoring_research
from src.models.inputs import ValidationState, StartupSubmission

async def test_tiered_research():
    print("Testing Research Tier Logic...")
    
    # Mock generate_llm_queries to simply return a list of "query" * num_queries
    with patch('src.agents.search.research.generate_llm_queries') as mock_gen_queries, \
         patch('src.agents.search.research.search_with_tavily_detailed') as mock_search:
        
        mock_gen_queries.side_effect = lambda desc, obj, num_queries: [f"q{i}" for i in range(num_queries)]
        mock_search.return_value = [{"content": "test", "url": "http://test.com"}]
        
        # Test Case 1: Basic Tier (Expecting 2 queries)
        print("\n--- Test Case 1: Basic Tier ---")
        await conduct_dynamic_research("idea", {"obj": "test"}, tier="basic")
        call_args = mock_gen_queries.call_args_list[-1]
        num_queries_arg = call_args.kwargs['num_queries']
        print(f"Basic Tier num_queries: {num_queries_arg}")
        assert num_queries_arg == 2, f"Expected 2 queries for basic, got {num_queries_arg}"
        
        # Test Case 2: Standard Tier (Expecting 4 queries)
        print("\n--- Test Case 2: Standard Tier ---")
        await conduct_dynamic_research("idea", {"obj": "test"}, tier="standard")
        call_args = mock_gen_queries.call_args_list[-1]
        num_queries_arg = call_args.kwargs['num_queries']
        print(f"Standard Tier num_queries: {num_queries_arg}")
        assert num_queries_arg == 4, f"Expected 4 queries for standard, got {num_queries_arg}"
        
        # Test Case 3: Premium Tier (Expecting 6 queries)
        print("\n--- Test Case 3: Premium Tier ---")
        await conduct_dynamic_research("idea", {"obj": "test"}, tier="premium")
        call_args = mock_gen_queries.call_args_list[-1]
        num_queries_arg = call_args.kwargs['num_queries']
        print(f"Premium Tier num_queries: {num_queries_arg}")
        assert num_queries_arg == 6, f"Expected 6 queries for premium, got {num_queries_arg}"
        
        # Test Case 4: Scoring Research (Unified Baseline - Expecting 4 queries regardless of tier)
        print("\n--- Test Case 4: Scoring Research (Unified Baseline) ---")
        dummy_state = {
            "inputs": MagicMock(detailed_description="startup"),
            "extracted_geography": "global",
            "extracted_industry": "tech"
        }
        # Note: conduct_scoring_research internally calls conduct_dynamic_research with tier="scoring_baseline"
        await conduct_scoring_research(dummy_state)
        
        # We need to find the call where tier="scoring_baseline"
        # conduct_scoring_research calls conduct_dynamic_research which calls dynamic_research
        # dynamic_research calls generate_llm_queries
        
        # Check the last call to generate_llm_queries (there will be 5 calls for the 5 objectives, so check one)
        call_args = mock_gen_queries.call_args_list[-1]
        num_queries_arg = call_args.kwargs['num_queries']
        print(f"Scoring Research num_queries: {num_queries_arg}")
        assert num_queries_arg == 4, f"Expected 4 queries for scoring baseline, got {num_queries_arg}"

    print("\n✅ All Tier Logic Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_tiered_research())
