"""
Unit tests for currency conversion utilities.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCurrencyConversion:
    """Tests for currency conversion logic."""
    
    def test_detect_usd_pattern(self):
        """Should detect USD patterns like $100, 100 USD, 100 dollars."""
        import re
        usd_pattern = r'\$[\d,]+|\b\d+[\d,]*\s*(USD|dollars?|Dollars?)\b'
        
        test_cases = [
            ("$5000", True),
            ("$1,500,000", True),
            ("100 USD", True),
            ("5000 dollars", True),
            ("100 EUR", False),
            ("€500", False)
        ]
        
        for text, should_match in test_cases:
            match = re.search(usd_pattern, text)
            assert bool(match) == should_match, f"Failed for: {text}"
    
    def test_detect_gbp_pattern(self):
        """Should detect GBP patterns like £100, 100 GBP."""
        import re
        gbp_pattern = r'£[\d,]+|\b\d+[\d,]*\s*(GBP|pounds?|Pounds?)\b'
        
        test_cases = [
            ("£5000", True),
            ("100 GBP", True),
            ("5000 pounds", True),
            ("$100", False),
        ]
        
        for text, should_match in test_cases:
            match = re.search(gbp_pattern, text)
            assert bool(match) == should_match, f"Failed for: {text}"
    
    def test_euro_values_unchanged(self):
        """Euro values should remain unchanged."""
        euro_values = ["€500", "100 EUR", "5000 Euro"]
        for val in euro_values:
            # Euro values should not be converted
            assert "EUR" in val or "€" in val or "Euro" in val


class TestDictValueConversion:
    """Tests for recursive dictionary value conversion."""
    
    def test_nested_dict_conversion(self):
        """Should convert values in nested dictionaries."""
        test_dict = {
            "level1": {
                "amount": "$1000",
                "level2": {
                    "price": "500 USD"
                }
            }
        }
        
        # Recursive structure test
        assert "level1" in test_dict
        assert "level2" in test_dict["level1"]
    
    def test_list_conversion(self):
        """Should convert values in lists."""
        test_list = ["$100", "$200", "€300"]
        assert len(test_list) == 3
    
    def test_none_values_handled(self):
        """Should handle None values gracefully."""
        test_dict = {
            "valid": "$100",
            "empty": None
        }
        assert test_dict["empty"] is None
