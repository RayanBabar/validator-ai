
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.models.inputs import ValidationState, StartupSubmission
from src.agents.compiler import compile_standard_report

# Mock Data
MOCK_INPUTS = StartupSubmission(
    detailed_description="A test startup idea.",
    tier="standard"
)

MOCK_RESEARCH_RESULT = {
    "market_demand": "High demand",
    "competition": "Low competition",
    "timing": "Good timing",
    "regulatory": "Low risk",
    "scalability": "High potential"
}

MOCK_SCORE_BREAKDOWN = {
    "market_demand": 9,
    "competition_analysis": 8,
    "financial_viability": 7,
    "technical_feasibility": 8,
    "regulatory_compliance": 9,
    "timing_assessment": 8,
    "founder_market_fit": 9,
    "scalability_potential": 8
}
MOCK_FINAL_SCORE = 82.0

@pytest.mark.asyncio
async def test_compiler_persists_and_reuses_scores():
    # 1. Setup State (Fresh run)
    state = ValidationState(
        inputs=MOCK_INPUTS,
        thread_id="test-thread",
        # No stored scores yet
    )
    
    # Mock dependencies
    with patch("src.agents.compiler.conduct_scoring_research", new_callable=AsyncMock) as mock_research, \
         patch("src.agents.compiler.LLMService.invoke", new_callable=AsyncMock) as mock_llm_invoke, \
         patch("src.agents.compiler.verify_cross_module_consistency", new_callable=AsyncMock) as mock_verify, \
         patch("src.agents.compiler.send_report_webhook", new_callable=AsyncMock) as mock_webhook:
        
        # Configure mocks
        mock_research.return_value = MOCK_RESEARCH_RESULT
        
        # Setup side_effect to return different values for sequential calls:
        # 1. Scoring (dict)
        # 2. Executive Summary (str) - Wait, exec summary might be complex too?
        # Let's check compiler.py: exec summary uses use_complex=True, parse_json=True
        # So it expects a DICT/Object, not a string if successful.
        # But my mock exec summary was just "Exec Summary".
        # Let's clean this up.
        
        # Scoring response
        scoring_response = MOCK_SCORE_BREAKDOWN
        
        # Executive Summary response (mock object)
        exec_summary_response = {
            "business_opportunity": {"problem_summary": "Test Problem"},
            "market_insights": {},
            "financial_execution": {},
            "recommendation": {}
        }

        # Side effect to return scoring first, then exec summary
        # BUT, wait. If stored scores exist (Run 2), scoring is skipped.
        # So we need a smarter side_effect or just distinct return values if possible?
        # No, side_effect is best. 
        # For Run 1: Call 1 (Score), Call 2 (Exec)
        # For Run 2: Call 1 (Exec)
        # This is generic interaction.
        
        # Let's define a side_effect function that checks arguments or just iterates
        mock_llm_invoke.side_effect = [scoring_response, exec_summary_response, exec_summary_response]
        
        mock_verify.return_value = {"pass": True}

        # --- RUN 1: Fresh Compile ---
        result1 = await compile_standard_report(state)
        
        # VERIFY 1: Check that scores are returned in the result keys
        assert "stored_go_no_go_score" in result1
        assert "stored_score_breakdown" in result1
        assert "stored_scoring_research" in result1
        
        # Check research was called
        mock_research.assert_called_once()
        
        saved_score = result1["stored_go_no_go_score"]
        saved_breakdown = result1["stored_score_breakdown"]
        saved_research = result1["stored_scoring_research"]
        
        print(f"\n[Run 1] Generated Score: {saved_score}")
        
        # --- RUN 2: Upgrade Simulation ---
        # Update state with the saved values
        state["stored_go_no_go_score"] = saved_score
        state["stored_score_breakdown"] = saved_breakdown
        state["stored_scoring_research"] = saved_research
        
        # Reset mocks to track calls for second run
        mock_research.reset_mock()
        mock_llm_invoke.reset_mock()
        # Reset side effect for Run 2 (Only one call expected: Exec Summary)
        mock_llm_invoke.side_effect = [exec_summary_response]
        
        # Run compiler again
        result2 = await compile_standard_report(state)
        
        # VERIFY 2: Check consistency and optimization
        
        # Score should be IDENTICAL
        assert result2["stored_go_no_go_score"] == saved_score
        
        # Research should NOT be called again
        mock_research.assert_not_called()
        print("[Run 2] Research skipped (Success)")
        
        # LLM Scoring should NOT be called again
        # Note: We need to distinguish between scoring LLM call and exec summary LLM call.
        # But compile_standard_report logic is: if stored_score: skip research & scoring block.
        # So mocks for scoring should strictly not be called.
        # However, `LLMService.invoke` is patched globally. It WILL be called for Executive Summary.
        # So we can't just `mock_llm_score.assert_not_called()` if it's the same mock.
        # Solution: I patched them as same mock if I didn't specify side_effect or specific targets. 
        # Actually LLMService.invoke is a class method. 
        # Let's patch `conduct_scoring_research` as the main indicator. (Already checked above).
        
        # Also verify the final report contains the same score
        assert result2["final_report"]["go_no_go_score"] == saved_score
        
        print("✅ Test Passed: Persistence keys flow correctly and redundant calculation is skipped.")

if __name__ == "__main__":
    # Allow running directly for debug
    import asyncio
    asyncio.run(test_compiler_persists_and_reuses_scores())
