"""
Currency Conversion Utility using Frankfurter API (European Central Bank rates).
No API key required. Default base is EUR.
"""
import httpx
import re
from typing import Optional, Union
from functools import lru_cache

# Frankfurter API - Free, no auth required, ECB rates
FRANKFURTER_API = "https://api.frankfurter.dev/v1"



@lru_cache(maxsize=32)
def get_exchange_rate(from_currency: str, to_currency: str = "EUR") -> Optional[float]:
    """
    Get exchange rate from one currency to another (default to EUR).
    Results are cached for performance.
    
    Args:
        from_currency: Source currency ISO code (e.g., "USD", "GBP")
        to_currency: Target currency ISO code (default: "EUR")
    
    Returns:
        Exchange rate as float, or None if failed
    """
    if from_currency.upper() == to_currency.upper():
        return 1.0
    
    try:
        url = f"{FRANKFURTER_API}/latest?from={from_currency.upper()}&to={to_currency.upper()}"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return data["rates"].get(to_currency.upper())
    except Exception as e:
        print(f"Currency conversion error: {e}")
        return None


async def get_exchange_rate_async(from_currency: str, to_currency: str = "EUR") -> Optional[float]:
    """Async version of get_exchange_rate."""
    if from_currency.upper() == to_currency.upper():
        return 1.0
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"{FRANKFURTER_API}/latest?from={from_currency.upper()}&to={to_currency.upper()}"
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data["rates"].get(to_currency.upper())
    except Exception as e:
        print(f"Currency conversion error: {e}")
        return None


def convert_to_euro(amount: Union[int, float], from_currency: str) -> Optional[float]:
    """
    Convert an amount to Euro.
    
    Args:
        amount: The amount to convert
        from_currency: Source currency ISO code
    
    Returns:
        Amount in Euro, rounded to 2 decimal places
    """
    rate = get_exchange_rate(from_currency, "EUR")
    if rate is None:
        return None
    return round(amount * rate, 2)


async def convert_to_euro_async(amount: Union[int, float], from_currency: str) -> Optional[float]:
    """Async version of convert_to_euro."""
    rate = await get_exchange_rate_async(from_currency, "EUR")
    if rate is None:
        return None
    return round(amount * rate, 2)


def detect_and_convert_currency(text: str) -> str:
    """
    Detect currency values in text and convert them to Euro.
    Handles formats like: $100, USD 100, 100 USD, £50, etc.
    
    Args:
        text: Input text containing currency values
    
    Returns:
        Text with all currency values converted to Euro
    """
    # Pattern to match currency values: $100, USD 100, 100 USD, £50, €100
    patterns = [
        # $100 or $100.50 or $100,000.50
        (r'\$\s*([\d,]+(?:\.\d{2})?)', 'USD'),
        # £100
        (r'£\s*([\d,]+(?:\.\d{2})?)', 'GBP'),
        # ¥100
        (r'¥\s*([\d,]+(?:\.\d{2})?)', 'JPY'),
        # USD 100 or USD100
        (r'\b(USD)\s*([\d,]+(?:\.\d{2})?)', 'USD'),
        # 100 USD
        (r'([\d,]+(?:\.\d{2})?)\s*(USD)\b', 'USD'),
        # GBP 100
        (r'\b(GBP)\s*([\d,]+(?:\.\d{2})?)', 'GBP'),
        # 100 GBP
        (r'([\d,]+(?:\.\d{2})?)\s*(GBP)\b', 'GBP'),
    ]
    
    result = text
    
    for pattern, currency in patterns:
        matches = re.finditer(pattern, result, re.IGNORECASE)
        for match in matches:
            try:
                # Extract the numeric value
                groups = match.groups()
                amount_str = groups[0] if len(groups) == 1 else (groups[1] if groups[0] in ('USD', 'GBP', 'JPY') else groups[0])
                amount = float(amount_str.replace(',', ''))
                
                # Convert to Euro
                euro_amount = convert_to_euro(amount, currency)
                if euro_amount:
                    # Replace the match with Euro value
                    result = result.replace(match.group(), f"EUR {euro_amount:,.2f}")
            except (ValueError, IndexError):
                continue
    
    return result


def convert_dict_values_to_euro(data: dict, currency_fields: list = None) -> dict:
    """
    Recursively convert monetary values in a dictionary to Euro.
    
    Args:
        data: Dictionary possibly containing monetary values
        currency_fields: List of field names that contain currency (auto-detect if None)
    
    Returns:
        Dictionary with values converted to Euro
    """
    # Common field names that typically contain monetary values
    default_currency_fields = [
        'value', 'amount', 'price', 'cost', 'revenue', 'expenses', 'net_income',
        'initial_investment', 'TAM', 'SAM', 'SOM', 'budget', 'funding',
        'salary', 'valuation', 'investment'
    ]
    fields_to_check = currency_fields or default_currency_fields
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = convert_dict_values_to_euro(value, fields_to_check)
            elif isinstance(value, list):
                result[key] = [
                    convert_dict_values_to_euro(item, fields_to_check) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Check if string contains currency values
                result[key] = detect_and_convert_currency(value)
            elif isinstance(value, (int, float)) and any(f in key.lower() for f in fields_to_check):
                # This is likely a USD value, convert to EUR
                # Assume USD if no currency specified
                converted = convert_to_euro(value, "USD")
                result[key] = converted if converted else value
            else:
                result[key] = value
        return result
    return data



