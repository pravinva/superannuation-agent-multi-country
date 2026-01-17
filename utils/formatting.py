#!/usr/bin/env python3
"""
Formatting Utilities
Currency formatting, number parsing, and other formatting helpers.
"""

from country_config import get_currency_info


def get_currency(country: str) -> str:
    """
    Get currency code for a country.
    
    Args:
        country: Country code (AU, US, UK, IN)
        
    Returns:
        Currency code (AUD, USD, GBP, INR)
    """
    currency_info = get_currency_info(country)
    return currency_info["code"]  # "AUD", "USD", "GBP", "INR"


def get_currency_symbol(country: str) -> str:
    """
    Get currency symbol for a country.
    
    Args:
        country: Country code (AU, US, UK, IN)
        
    Returns:
        Currency symbol ("$", "£", "₹")
    """
    currency_info = get_currency_info(country)
    return currency_info["symbol"]  # "$", "£", "₹"


def safe_float(value, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert (can be str, int, float, or None)
        default: Default value if conversion fails
        
    Returns:
        Float value or default if conversion fails
    """
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        if not value or str(value).lower() == "none":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def format_currency_amount(amount: float, country: str, include_symbol: bool = True) -> str:
    """
    Format currency amount with proper symbol and formatting.
    
    Args:
        amount: Amount to format
        country: Country code (AU, US, UK, IN)
        include_symbol: Whether to include currency symbol
        
    Returns:
        Formatted currency string (e.g., "$1,234.56 AUD" or "1,234.56 AUD")
    """
    symbol = get_currency_symbol(country) if include_symbol else ""
    code = get_currency(country)
    
    formatted_amount = f"{amount:,.2f}"
    
    if include_symbol:
        # Different countries have different symbol placement
        if country in ["AU", "US"]:
            return f"{symbol}{formatted_amount} {code}"
        elif country == "UK":
            return f"{symbol}{formatted_amount} {code}"
        elif country == "IN":
            return f"{symbol}{formatted_amount} {code}"
        else:
            return f"{symbol}{formatted_amount} {code}"
    else:
        return f"{formatted_amount} {code}"

