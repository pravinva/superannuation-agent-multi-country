"""
ui
==

UI component refactoring package for superannuation agent.

This package provides centralized UI utilities:
- theme_config: Country-specific themes and color schemes
- html_builder: Reusable HTML component builders (coming soon)
- tab_base: Base class for monitoring tabs (coming soon)

Modules:
    theme_config: Country theme definitions

Usage:
    >>> from ui.theme_config import get_country_theme
    >>> theme = get_country_theme("Australia")
    >>> print(theme.primary)  # "#FFD700"

Author: Refactoring Team
Date: 2024-11-24
"""

from ui.theme_config import (
    COUNTRY_COLORS,
    COUNTRY_WELCOME_COLORS,
    COUNTRY_FLAGS,
    SUPPORTED_COUNTRIES
)

__all__ = [
    'COUNTRY_COLORS',
    'COUNTRY_WELCOME_COLORS',
    'COUNTRY_FLAGS',
    'SUPPORTED_COUNTRIES',
]
