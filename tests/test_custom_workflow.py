import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.agents.compiler import compile_standard_report
from src.graph.workflow import route_after_research, STANDARD_MODULES
from src.models.inputs import ValidationState, StartupSubmission

async def test_workflow_routing_respects_custom_modules():
    """
    Test that route_after_research returns ONLY the custom modules
    when tier is 'custom'.
    """
    state = {
        "inputs": StartupSubmission(
            detailed_description="Test",
            tier="custom"
        ),
        "custom_modules": ["mod_bmc", "mod_market"]
    }
    
    # Act
    next_nodes = route_after_research(state)
    
    # Assert
    print(f"DEBUG: Next nodes: {next_nodes}")
    assert isinstance(next_nodes, list)
    assert "mod_bmc" in next_nodes
    assert "mod_market" in next_nodes
    assert len(next_nodes) == 2, f"Expected 2 modules, got {len(next_nodes)}: {next_nodes}"
    assert "mod_finance" not in next_nodes

async def test_compiler_respects_custom_tier():
    """
    Test that compiler only includes data for requested custom modules
    even if other data exists in state (simulating dirty state or previous runs).
    """
    state: ValidationState = {
        "inputs": StartupSubmission(
            detailed_description="Test Idea",
            tier="custom"
        ),
        "custom_modules": ["mod_bmc", "mod_market"],
        "bmc_data": {"customer_segments": ["Seg A"]},
        "market_data": {"tam": "1B"},
        # Extra data that should be filtered out if we are strict
        "financial_data": {"revenue": "1M"},
        # Mock other required fields
        "stored_go_no_go_score": 80,
        "stored_score_breakdown": {},
        "stored_scoring_research": {},
        "generated_title": "Test"
    }
    
    # Mock LLM calls to avoid real API
    # We rely on compiler logic, not LLM output for this test structure check
    from src.agents import compiler
    
    # Use AsyncMock for async functions
    compiler.LLMService = MagicMock()
    compiler.LLMService.invoke = AsyncMock(return_value={"business_opportunity": "test"})
    compiler.verify_cross_module_consistency = AsyncMock(return_value={"pass": True})
    compiler.send_report_webhook = AsyncMock()

    # Act
    result = await compile_standard_report(state)
    report = result["final_report"]
    
    # Assert
    modules = report["modules"]
    assert report["tier"] == "custom"
    
    # Should exist
    assert modules.get("business_model_canvas") is not None
    assert modules.get("market_analysis") is not None
    
    # Validation logic: 'financials' should be explicitly None or missing
    # In my implementation of _filter_modules_for_tier, I set excluded modules to None.
    assert modules.get("financials") is None, f"Financials should be None/missing, got {modules.get('financials')}"

    # OPTIMIZATION VERIFICATION:
    # Ensure consistency check was skipped for custom tier
    compiler.verify_cross_module_consistency.assert_not_called()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_workflow_routing_respects_custom_modules())
        loop.run_until_complete(test_compiler_respects_custom_tier())
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    else:
        print("✅ All Tests Passed")
