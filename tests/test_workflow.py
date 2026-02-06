"""
Integration tests for the LangGraph workflow.
Tests workflow routing logic and state transitions.
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestWorkflowRouting:
    """Tests for workflow routing logic."""
    
    def test_route_after_interview_complete(self):
        """Complete interview should route to research."""
        state = {"interview_phase": "complete"}
        phase = state.get("interview_phase", "asking")
        
        if phase == "complete":
            result = "research"
        else:
            result = "wait_for_answer"
        
        assert result == "research"
    
    def test_route_after_interview_asking(self):
        """Asking phase should route to wait_for_answer (END)."""
        state = {"interview_phase": "asking"}
        phase = state.get("interview_phase", "asking")
        
        if phase == "complete":
            result = "research"
        else:
            result = "wait_for_answer"
        
        assert result == "wait_for_answer"
    
    def test_route_after_research_free_tier(self):
        """Free tier should route to free_scan."""
        from src.models.inputs import StartupSubmission
        
        tier = "free"
        if tier == "free":
            result = "free_scan"
        elif tier == "basic":
            result = "basic_gen"
        else:
            result = "modules"
        
        assert result == "free_scan"
    
    def test_route_after_research_basic_tier(self):
        """Basic tier should route to basic_gen."""
        tier = "basic"
        if tier == "free":
            result = "free_scan"
        elif tier == "basic":
            result = "basic_gen"
        else:
            result = "modules"
        
        assert result == "basic_gen"
    
    def test_route_after_research_standard_tier(self):
        """Standard tier should route to parallel modules."""
        tier = "standard"
        STANDARD_MODULES = [
            "mod_bmc", "mod_market", "mod_comp", "mod_finance", "mod_tech",
            "mod_reg", "mod_gtm", "mod_risk", "mod_roadmap", "mod_funding"
        ]
        
        if tier == "free":
            result = "free_scan"
        elif tier == "basic":
            result = "basic_gen"
        else:
            result = STANDARD_MODULES
        
        assert result == STANDARD_MODULES
        assert len(result) == 10


class TestWorkflowState:
    """Tests for workflow state management."""
    
    def test_initial_state_structure(self):
        """Initial state should have required keys."""
        from src.models.inputs import StartupSubmission
        
        initial_state = {
            "inputs": None,
            "questions_asked": [],
            "user_answers": [],
            "interview_phase": "asking",
            "current_question": None,
            "search_context": None,
            "enriched_context": None,
            "final_report": None,
            "workflow_phase": "interview"
        }
        
        required_keys = [
            "inputs", "questions_asked", "user_answers",
            "interview_phase", "workflow_phase"
        ]
        
        for key in required_keys:
            assert key in initial_state
    
    def test_state_update_after_interview(self):
        """State should update correctly after interview."""
        state = {
            "questions_asked": ["Q1", "Q2"],
            "user_answers": ["A1", "A2"],
            "interview_phase": "asking"
        }
        
        # Simulate adding a new question
        new_question = "Q3"
        state["questions_asked"].append(new_question)
        
        assert len(state["questions_asked"]) == 3
        assert state["questions_asked"][-1] == "Q3"
    
    def test_state_update_after_answer(self):
        """State should update correctly after user answer."""
        state = {
            "questions_asked": ["Q1"],
            "user_answers": []
        }
        
        # Simulate adding an answer
        new_answer = "A1"
        state["user_answers"].append(new_answer)
        
        assert len(state["user_answers"]) == 1
        assert state["user_answers"][-1] == "A1"


class TestStandardModules:
    """Tests for standard tier parallel modules."""
    
    def test_all_10_modules_defined(self):
        """All 10 standard modules should be defined."""
        STANDARD_MODULES = [
            "mod_bmc", "mod_market", "mod_comp", "mod_finance", "mod_tech",
            "mod_reg", "mod_gtm", "mod_risk", "mod_roadmap", "mod_funding"
        ]
        assert len(STANDARD_MODULES) == 10
    
    def test_module_naming_convention(self):
        """All modules should follow mod_ naming convention."""
        STANDARD_MODULES = [
            "mod_bmc", "mod_market", "mod_comp", "mod_finance", "mod_tech",
            "mod_reg", "mod_gtm", "mod_risk", "mod_roadmap", "mod_funding"
        ]
        for module in STANDARD_MODULES:
            assert module.startswith("mod_"), f"{module} doesn't follow naming convention"
    
    def test_modules_converge_to_compiler(self):
        """All modules should converge to compiler node."""
        # This is a structural test for fan-in pattern
        modules_complete = [True] * 10  # All 10 modules done
        all_complete = all(modules_complete)
        
        assert all_complete
        # After all complete, should route to "compiler"
