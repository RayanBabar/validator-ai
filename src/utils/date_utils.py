"""
Date utility functions for consistent date/time handling across the application.
"""
from datetime import datetime


def get_current_year() -> int:
    """Get the current year dynamically."""
    return datetime.now().year


def get_current_date() -> str:
    """Get the current date as a formatted string (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")


def get_date_context() -> dict:
    """
    Get date context for prompt templates.
    
    Returns:
        Dictionary with current_date and current_year keys
    """
    return {
        "current_date": get_current_date(),
        "current_year": get_current_year(),
    }
