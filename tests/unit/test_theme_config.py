"""
Unit tests for ui.theme_config module.

Tests cover:
- COUNTRY_COLORS dictionary structure and values
- COUNTRY_WELCOME_COLORS dictionary structure and values
- COUNTRY_FLAGS dictionary
- Exact color value preservation from original ui_components.py
- All 4 supported countries (Australia, USA, United Kingdom, India)

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
from ui.theme_config import (
    COUNTRY_COLORS,
    COUNTRY_WELCOME_COLORS,
    COUNTRY_FLAGS,
    SUPPORTED_COUNTRIES
)


class TestCountryColors:
    """Test suite for COUNTRY_COLORS dictionary."""

    def test_all_countries_present(self):
        """Test that all 4 countries are in COUNTRY_COLORS."""
        assert len(COUNTRY_COLORS) == 4
        assert "Australia" in COUNTRY_COLORS
        assert "USA" in COUNTRY_COLORS
        assert "United Kingdom" in COUNTRY_COLORS
        assert "India" in COUNTRY_COLORS

    def test_australia_colors(self):
        """Test Australia colors match ui_components.py lines 67-71."""
        colors = COUNTRY_COLORS["Australia"]
        assert colors['flag'] == "🇦🇺"
        assert colors['primary'] == "#FFD700"    # Gold
        assert colors['secondary'] == "#00843D"  # Green
        assert colors['currency'] == "A$"

    def test_usa_colors(self):
        """Test USA colors match ui_components.py lines 73-77."""
        colors = COUNTRY_COLORS["USA"]
        assert colors['flag'] == "🇺🇸"
        assert colors['primary'] == "#B22234"    # Red
        assert colors['secondary'] == "#3C3B6E"  # Navy Blue
        assert colors['currency'] == "$"

    def test_uk_colors(self):
        """Test UK colors match ui_components.py lines 79-83."""
        colors = COUNTRY_COLORS["United Kingdom"]
        assert colors['flag'] == "🇬🇧"
        assert colors['primary'] == "#C8102E"    # Red
        assert colors['secondary'] == "#012169"  # Blue
        assert colors['currency'] == "£"

    def test_india_colors(self):
        """Test India colors match ui_components.py lines 85-89."""
        colors = COUNTRY_COLORS["India"]
        assert colors['flag'] == "🇮🇳"
        assert colors['primary'] == "#FF9933"    # Saffron
        assert colors['secondary'] == "#138808"  # Green
        assert colors['currency'] == "₹"

    def test_all_colors_have_required_keys(self):
        """Test each country has all required keys."""
        required_keys = {'flag', 'primary', 'secondary', 'currency'}

        for country, colors in COUNTRY_COLORS.items():
            assert set(colors.keys()) == required_keys, f"{country} missing keys"
            assert colors['flag']  # Not empty
            assert colors['primary'].startswith('#')  # Valid hex color
            assert colors['secondary'].startswith('#')  # Valid hex color
            assert colors['currency']  # Not empty


class TestCountryWelcomeColors:
    """Test suite for COUNTRY_WELCOME_COLORS dictionary."""

    def test_all_countries_present(self):
        """Test that all 4 countries are in COUNTRY_WELCOME_COLORS."""
        assert len(COUNTRY_WELCOME_COLORS) == 4
        assert "Australia" in COUNTRY_WELCOME_COLORS
        assert "USA" in COUNTRY_WELCOME_COLORS
        assert "United Kingdom" in COUNTRY_WELCOME_COLORS
        assert "India" in COUNTRY_WELCOME_COLORS

    def test_australia_welcome_colors(self):
        """Test Australia welcome colors match ui_components.py line 135."""
        colors = COUNTRY_WELCOME_COLORS["Australia"]
        assert colors['gradient'] == "linear-gradient(135deg, #00843D 0%, #FFD700 50%, #FFA500 100%)"
        assert colors['border'] == "#FFD700"
        assert colors['text'] == "#0f172a"
        assert colors['text_bg'] == "rgba(255, 255, 255, 0.85)"

    def test_usa_welcome_colors(self):
        """Test USA welcome colors match ui_components.py line 141."""
        colors = COUNTRY_WELCOME_COLORS["USA"]
        expected_gradient = "linear-gradient(135deg, #B22234 0%, #FFFFFF 25%, #3C3B6E 50%, #FFFFFF 75%, #B22234 100%)"
        assert colors['gradient'] == expected_gradient
        assert colors['border'] == "#FFD700"
        assert colors['text'] == "#0f172a"
        assert colors['text_bg'] == "rgba(255, 255, 255, 0.9)"

    def test_uk_welcome_colors(self):
        """Test UK welcome colors match ui_components.py line 147."""
        colors = COUNTRY_WELCOME_COLORS["United Kingdom"]
        expected_gradient = "linear-gradient(135deg, #C8102E 0%, #FFFFFF 30%, #012169 60%, #FFFFFF 85%, #C8102E 100%)"
        assert colors['gradient'] == expected_gradient
        assert colors['border'] == "#FFD700"
        assert colors['text'] == "#0f172a"
        assert colors['text_bg'] == "rgba(255, 255, 255, 0.9)"

    def test_india_welcome_colors(self):
        """Test India welcome colors match ui_components.py line 153."""
        colors = COUNTRY_WELCOME_COLORS["India"]
        expected_gradient = "linear-gradient(135deg, #FF9933 0%, #FFFFFF 40%, #138808 80%, #138808 100%)"
        assert colors['gradient'] == expected_gradient
        assert colors['border'] == "#FF9933"
        assert colors['text'] == "#0f172a"
        assert colors['text_bg'] == "rgba(255, 255, 255, 0.85)"

    def test_all_welcome_colors_have_required_keys(self):
        """Test each country has all required welcome color keys."""
        required_keys = {'gradient', 'border', 'text', 'text_bg'}

        for country, colors in COUNTRY_WELCOME_COLORS.items():
            assert set(colors.keys()) == required_keys, f"{country} missing keys"
            assert "linear-gradient" in colors['gradient']
            assert colors['border'].startswith('#') or colors['border'].startswith('rgba')
            assert colors['text'].startswith('#')
            assert 'rgba' in colors['text_bg']


class TestCountryFlags:
    """Test suite for COUNTRY_FLAGS dictionary."""

    def test_all_countries_present(self):
        """Test that all 4 countries are in COUNTRY_FLAGS."""
        assert len(COUNTRY_FLAGS) == 4
        assert "Australia" in COUNTRY_FLAGS
        assert "USA" in COUNTRY_FLAGS
        assert "United Kingdom" in COUNTRY_FLAGS
        assert "India" in COUNTRY_FLAGS

    def test_flag_values(self):
        """Test flag emoji values match ui_components.py lines 123-129."""
        assert COUNTRY_FLAGS["Australia"] == "🇦🇺"
        assert COUNTRY_FLAGS["USA"] == "🇺🇸"
        assert COUNTRY_FLAGS["United Kingdom"] == "🇬🇧"
        assert COUNTRY_FLAGS["India"] == "🇮🇳"


class TestSupportedCountries:
    """Test suite for SUPPORTED_COUNTRIES list."""

    def test_supported_countries_list(self):
        """Test SUPPORTED_COUNTRIES has all 4 countries."""
        assert len(SUPPORTED_COUNTRIES) == 4
        assert "Australia" in SUPPORTED_COUNTRIES
        assert "USA" in SUPPORTED_COUNTRIES
        assert "United Kingdom" in SUPPORTED_COUNTRIES
        assert "India" in SUPPORTED_COUNTRIES

    def test_supported_countries_matches_colors(self):
        """Test SUPPORTED_COUNTRIES matches COUNTRY_COLORS keys."""
        assert set(SUPPORTED_COUNTRIES) == set(COUNTRY_COLORS.keys())


class TestBackwardCompatibility:
    """Test suite for backward compatibility with original code patterns."""

    def test_get_with_fallback_pattern(self):
        """Test the .get(country, fallback) pattern works."""
        # This is the pattern used in ui_components.py
        colors = COUNTRY_COLORS.get("Australia", COUNTRY_COLORS["Australia"])
        assert colors['flag'] == "🇦🇺"

        # Unknown country falls back to Australia
        colors = COUNTRY_COLORS.get("Unknown", COUNTRY_COLORS["Australia"])
        assert colors['flag'] == "🇦🇺"

    def test_direct_access_pattern(self):
        """Test direct dictionary access works."""
        colors = COUNTRY_COLORS["Australia"]
        assert colors['primary'] == "#FFD700"

        # Test nested access
        flag = COUNTRY_COLORS["USA"]['flag']
        assert flag == "🇺🇸"

    def test_iteration_pattern(self):
        """Test iteration over countries works."""
        for country in SUPPORTED_COUNTRIES:
            colors = COUNTRY_COLORS[country]
            assert colors['flag']
            assert colors['primary']

    def test_welcome_colors_access(self):
        """Test welcome colors access pattern."""
        welcome = COUNTRY_WELCOME_COLORS.get("Australia", COUNTRY_WELCOME_COLORS["Australia"])
        assert "linear-gradient" in welcome['gradient']


class TestExactColorValuePreservation:
    """Test suite to ensure exact color values are preserved from original code."""

    def test_australia_exact_hex_values(self):
        """Test Australia hex colors are exactly preserved."""
        colors = COUNTRY_COLORS["Australia"]
        # From ui_components.py lines 69-70
        assert colors['primary'] == "#FFD700"   # Not #ffd700 or #FFD701
        assert colors['secondary'] == "#00843D" # Not #00843d or #00843E

    def test_usa_exact_hex_values(self):
        """Test USA hex colors are exactly preserved."""
        colors = COUNTRY_COLORS["USA"]
        # From ui_components.py lines 75-76
        assert colors['primary'] == "#B22234"   # Not #b22234 or #B22235
        assert colors['secondary'] == "#3C3B6E" # Not #3c3b6e or #3C3B6F

    def test_uk_exact_hex_values(self):
        """Test UK hex colors are exactly preserved."""
        colors = COUNTRY_COLORS["United Kingdom"]
        # From ui_components.py lines 81-82
        assert colors['primary'] == "#C8102E"   # Not #c8102e or #C8102F
        assert colors['secondary'] == "#012169" # Not #012168 or #01216A

    def test_india_exact_hex_values(self):
        """Test India hex colors are exactly preserved."""
        colors = COUNTRY_COLORS["India"]
        # From ui_components.py lines 87-88
        assert colors['primary'] == "#FF9933"   # Not #ff9933 or #FF9934
        assert colors['secondary'] == "#138808" # Not #138807 or #138809

    def test_gradient_exact_strings(self):
        """Test gradient strings are exactly preserved (spacing, percentages, etc)."""
        # Australia gradient from line 135
        aus_gradient = COUNTRY_WELCOME_COLORS["Australia"]['gradient']
        assert aus_gradient == "linear-gradient(135deg, #00843D 0%, #FFD700 50%, #FFA500 100%)"

        # Check no extra spaces or formatting changes
        assert "135deg, " in aus_gradient  # Space after comma
        assert " 0%" in aus_gradient       # Space before percentage
        assert " 50%" in aus_gradient
        assert " 100%)" in aus_gradient    # Closing paren

    def test_rgba_exact_strings(self):
        """Test rgba strings are exactly preserved."""
        aus_bg = COUNTRY_WELCOME_COLORS["Australia"]['text_bg']
        assert aus_bg == "rgba(255, 255, 255, 0.85)"

        usa_bg = COUNTRY_WELCOME_COLORS["USA"]['text_bg']
        assert usa_bg == "rgba(255, 255, 255, 0.9)"

        # Check exact spacing and decimal precision
        assert "255, 255, 255, " in aus_bg
        assert ", 0.85)" in aus_bg  # Not 0.850 or .85
        assert ", 0.9)" in usa_bg   # Not 0.90


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_case_sensitive_country_names(self):
        """Test that country names are case-sensitive."""
        # Exact match works
        assert "Australia" in COUNTRY_COLORS

        # Wrong case should not match (KeyError or needs .get())
        with pytest.raises(KeyError):
            _ = COUNTRY_COLORS["australia"]

        with pytest.raises(KeyError):
            _ = COUNTRY_COLORS["AUSTRALIA"]

    def test_unknown_country_handling(self):
        """Test accessing unknown country with .get() fallback."""
        # Using .get() with fallback (the recommended pattern)
        colors = COUNTRY_COLORS.get("Unknown", COUNTRY_COLORS["Australia"])
        assert colors['flag'] == "🇦🇺"

        # Direct access raises KeyError (expected behavior)
        with pytest.raises(KeyError):
            _ = COUNTRY_COLORS["Unknown Country"]

    def test_dictionary_immutability_intent(self):
        """Test that we can detect if someone tries to modify (not prevented, but testable)."""
        # Note: Python dicts are mutable, but we can test the structure
        original_primary = COUNTRY_COLORS["Australia"]['primary']
        assert original_primary == "#FFD700"

        # If someone modifies it (which they shouldn't), it would change
        # This test documents the expected immutability intent
        assert COUNTRY_COLORS["Australia"]['primary'] == "#FFD700"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
