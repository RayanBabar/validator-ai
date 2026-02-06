
import pytest
from unittest.mock import Mock
from src.config.constants import STANDARD_MODULE_NAMES

# Mocking the route_after_research function functionality for testing
# We are reimplementing the logic here because importing it might be tricky without full context setup
# typically one would import the actual function, but for unit testing logic it's often safer to import
# However, let's try to import it if possible. 
# If import fails, we can replicate the logic to test "what we implemented" 
# but ideally we test the actual function.

# Let's assume we can import it. If not, we will need to adjust the PYTHONPATH or similar.
# For now, I will define a helper that mimics the logic to verify correctness of my DESIGN
# and then I will try to import the actual function in the test.

from src.graph.workflow import route_after_research
from src.models.inputs import StartupSubmission

class TestCustomTierRouting:
    """Tests for custom tier routing logic in workflow."""

    def test_custom_tier_routing_valid_modules(self):
        """Custom tier with valid modules should route to those modules."""
        # Setup state
        custom_modules = ["mod_market", "mod_comp"]
        inputs = Mock()
        inputs.tier = "custom"
        
        state = {
            "inputs": inputs,
            "custom_modules": custom_modules
        }
        
        result = route_after_research(state)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert "mod_market" in result
        assert "mod_comp" in result

    def test_custom_tier_routing_no_modules(self):
        """Custom tier with no modules should fallback to basic_gen."""
        inputs = Mock()
        inputs.tier = "custom"
        
        state = {
            "inputs": inputs,
            "custom_modules": []
        }
        
        result = route_after_research(state)
        assert result == "basic_gen"

    def test_custom_tier_routing_invalid_modules(self):
        """Custom tier with only invalid modules should fallback to basic_gen."""
        inputs = Mock()
        inputs.tier = "custom"
        
        state = {
            "inputs": inputs,
            "custom_modules": ["invalid_mod_A", "invalid_mod_B"]
        }
        
        result = route_after_research(state)
        assert result == "basic_gen"

    def test_custom_tier_routing_mixed_modules(self):
        """Custom tier with mixed modules should filter valid ones."""
        inputs = Mock()
        inputs.tier = "custom"
        
        state = {
            "inputs": inputs,
            "custom_modules": ["mod_market", "invalid_mod"]
        }
        
        result = route_after_research(state)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert "mod_market" in result
        assert "invalid_mod" not in result

    def test_standard_tier_fallback(self):
        """Standard tier should still route to all modules."""
        inputs = Mock()
        inputs.tier = "standard"
        
        state = {
            "inputs": inputs
        }
        
        result = route_after_research(state)
        assert result == STANDARD_MODULE_NAMES

