"""
ui.theme_config
===============

Country-specific theme configurations for the superannuation agent UI.

This module centralizes all country theme definitions that were previously
scattered across multiple UI files. It preserves ALL existing color values,
gradients, and styling exactly to maintain direct compatibility.

Extracted from:
- ui_components.py (lines 66-91, 123-129, 133-158)
- ui_dashboard.py (country-specific styling)

Usage:
    >>> from ui.theme_config import COUNTRY_COLORS, COUNTRY_WELCOME_COLORS
    >>>
    >>> # Use exactly like before
    >>> colors = COUNTRY_COLORS.get(country, COUNTRY_COLORS["Australia"])
    >>> print(colors['flag'])  # "🇦🇺"
    >>> print(colors['primary'])  # "#FFD700"
    >>>
    >>> welcome = COUNTRY_WELCOME_COLORS.get(country, COUNTRY_WELCOME_COLORS["Australia"])
    >>> print(welcome['gradient'])  # "linear-gradient(...)"

Author: Refactoring Team
Date: 2024-11-24
"""

from typing import Dict, List


# ============================================================================ #
# COUNTRY COLORS - Basic theme (for member cards, financial displays)
# ============================================================================ #
# From ui_components.py lines 66-91
# Preserves EXACT values - do NOT modify without verifying visual compatibility

COUNTRY_COLORS: Dict[str, Dict[str, str]] = {
    "Australia": {
        "flag": "🇦🇺",
        "primary": "#FFD700",      # Gold
        "secondary": "#00843D",    # Green
        "currency": "A$"
    },
    "USA": {
        "flag": "🇺🇸",
        "primary": "#B22234",      # Red
        "secondary": "#3C3B6E",    # Navy Blue
        "currency": "$"
    },
    "United Kingdom": {
        "flag": "🇬🇧",
        "primary": "#C8102E",      # Red
        "secondary": "#012169",    # Blue
        "currency": "£"
    },
    "India": {
        "flag": "🇮🇳",
        "primary": "#FF9933",      # Saffron
        "secondary": "#138808",    # Green
        "currency": "₹"
    }
}


# ============================================================================ #
# COUNTRY WELCOME COLORS - Extended theme (for welcome banners)
# ============================================================================ #
# From ui_components.py lines 133-158
# Includes gradients and rich styling for country-specific welcome cards

COUNTRY_WELCOME_COLORS: Dict[str, Dict[str, str]] = {
    "Australia": {
        "gradient": "linear-gradient(135deg, #00843D 0%, #FFD700 50%, #FFA500 100%)",
        "border": "#FFD700",
        "text": "#0f172a",
        "text_bg": "rgba(255, 255, 255, 0.85)"
    },
    "USA": {
        "gradient": "linear-gradient(135deg, #B22234 0%, #FFFFFF 25%, #3C3B6E 50%, #FFFFFF 75%, #B22234 100%)",
        "border": "#FFD700",
        "text": "#0f172a",
        "text_bg": "rgba(255, 255, 255, 0.9)"
    },
    "United Kingdom": {
        "gradient": "linear-gradient(135deg, #C8102E 0%, #FFFFFF 30%, #012169 60%, #FFFFFF 85%, #C8102E 100%)",
        "border": "#FFD700",
        "text": "#0f172a",
        "text_bg": "rgba(255, 255, 255, 0.9)"
    },
    "India": {
        "gradient": "linear-gradient(135deg, #FF9933 0%, #FFFFFF 40%, #138808 80%, #138808 100%)",
        "border": "#FF9933",
        "text": "#0f172a",
        "text_bg": "rgba(255, 255, 255, 0.85)"
    }
}


# ============================================================================ #
# COUNTRY FLAGS - Simple lookup dictionary
# ============================================================================ #
# From ui_components.py lines 123-129

COUNTRY_FLAGS: Dict[str, str] = {
    "Australia": "🇦🇺",
    "USA": "🇺🇸",
    "United Kingdom": "🇬🇧",
    "India": "🇮🇳"
}


# List of supported countries
SUPPORTED_COUNTRIES: List[str] = list(COUNTRY_COLORS.keys())


# ============================================================================ #
# MODULE TEST (run when executed directly)
# ============================================================================ #

if __name__ == "__main__":
    print("=" * 60)
    print("Country Theme Config Test")
    print("=" * 60)

    # Test dictionaries
    print("\nTesting COUNTRY_COLORS:")
    for country in SUPPORTED_COUNTRIES:
        colors = COUNTRY_COLORS[country]
        print(f"  {colors['flag']} {country}: {colors['primary']} / {colors['currency']}")

    print("\nTesting COUNTRY_WELCOME_COLORS:")
    for country in SUPPORTED_COUNTRIES:
        welcome = COUNTRY_WELCOME_COLORS[country]
        gradient = welcome['gradient'][:40] + "..."
        print(f"  {country}: {gradient}")

    print("\n" + "=" * 60)
    print("✅ All dictionaries accessible")
    print("=" * 60)
