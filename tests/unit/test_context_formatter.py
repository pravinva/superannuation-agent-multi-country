"""
Unit tests for agents.context_formatter module.

Tests cover:
- Name anonymization and restoration
- Base context building
- Tool results formatting
- India EPF/NPS split display
- Country extraction from context
- Personalized greetings
- Singleton pattern

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import hashlib

from agents.context_formatter import (
    ContextFormatter,
    get_context_formatter,
    _global_formatter
)


class TestContextFormatter:
    """Test suite for ContextFormatter class."""

    def test_init_creates_formatter(self):
        """Test ContextFormatter initialization."""
        formatter = ContextFormatter()
        assert formatter is not None
        assert formatter.logger is not None

    def test_init_with_custom_logger(self):
        """Test ContextFormatter initialization with custom logger."""
        mock_logger = Mock()
        formatter = ContextFormatter(logger=mock_logger)
        assert formatter.logger == mock_logger


class TestAnonymization:
    """Test suite for name anonymization methods."""

    def test_anonymize_member_name_creates_hash(self):
        """Test that anonymize_member_name creates consistent MD5 hash."""
        formatter = ContextFormatter()
        name = "John Smith"

        anonymized = formatter.anonymize_member_name(name)

        # Should start with Member_
        assert anonymized.startswith("Member_")

        # Should be consistent (same name = same hash)
        anonymized2 = formatter.anonymize_member_name(name)
        assert anonymized == anonymized2

        # Hash should be 6 characters
        hash_part = anonymized.replace("Member_", "")
        assert len(hash_part) == 6

    def test_anonymize_member_name_different_names(self):
        """Test that different names produce different hashes."""
        formatter = ContextFormatter()

        name1 = "John Smith"
        name2 = "Jane Doe"

        anonymized1 = formatter.anonymize_member_name(name1)
        anonymized2 = formatter.anonymize_member_name(name2)

        assert anonymized1 != anonymized2

    def test_anonymize_member_name_empty_string(self):
        """Test anonymization of empty string."""
        formatter = ContextFormatter()

        anonymized = formatter.anonymize_member_name("")
        assert anonymized == "Member_unknown"

    def test_anonymize_member_name_unknown_member(self):
        """Test anonymization of 'Unknown Member'."""
        formatter = ContextFormatter()

        anonymized = formatter.anonymize_member_name("Unknown Member")
        assert anonymized == "Member_unknown"

    def test_anonymize_member_name_none(self):
        """Test anonymization of None."""
        formatter = ContextFormatter()

        anonymized = formatter.anonymize_member_name(None)
        assert anonymized == "Member_unknown"

    def test_restore_member_name_replaces_correctly(self):
        """Test that restore_member_name replaces anonymized name with real name."""
        formatter = ContextFormatter()

        text = "Hi Member_abc123, your balance is $500,000"
        anonymized_name = "Member_abc123"
        real_name = "John Smith"

        restored = formatter.restore_member_name(text, anonymized_name, real_name)

        assert "John Smith" in restored
        assert "Member_abc123" not in restored

    def test_restore_member_name_no_match(self):
        """Test restore_member_name when anonymized name not in text."""
        formatter = ContextFormatter()

        text = "Your balance is $500,000"
        anonymized_name = "Member_abc123"
        real_name = "John Smith"

        restored = formatter.restore_member_name(text, anonymized_name, real_name)

        # Should return text unchanged
        assert restored == text

    def test_restore_member_name_empty_names(self):
        """Test restore_member_name with empty anonymized or real name."""
        formatter = ContextFormatter()

        text = "Your balance is $500,000"

        # Empty anonymized name
        restored1 = formatter.restore_member_name(text, "", "John")
        assert restored1 == text

        # Empty real name
        restored2 = formatter.restore_member_name(text, "Member_abc", "")
        assert restored2 == text


class TestGreeting:
    """Test suite for personalized greeting methods."""

    def test_add_personalized_greeting_prepends_greeting(self):
        """Test that add_personalized_greeting prepends greeting."""
        formatter = ContextFormatter()

        text = "Your balance is $500,000"
        member_name = "John"

        greeted = formatter.add_personalized_greeting(text, member_name)

        assert greeted.startswith("Hi John,")
        assert "Your balance is $500,000" in greeted

    def test_add_personalized_greeting_no_duplicate(self):
        """Test that greeting is not added if already present."""
        formatter = ContextFormatter()

        text = "Hi John, your balance is $500,000"
        member_name = "John"

        greeted = formatter.add_personalized_greeting(text, member_name)

        # Should not add duplicate greeting
        assert greeted == text
        assert greeted.count("Hi") == 1

    def test_add_personalized_greeting_empty_name(self):
        """Test add_personalized_greeting with empty name."""
        formatter = ContextFormatter()

        text = "Your balance is $500,000"

        greeted = formatter.add_personalized_greeting(text, "")
        assert greeted == text

    def test_add_personalized_greeting_unknown_member(self):
        """Test add_personalized_greeting with Unknown Member."""
        formatter = ContextFormatter()

        text = "Your balance is $500,000"

        greeted = formatter.add_personalized_greeting(text, "Unknown Member")
        assert greeted == text


class TestCountryExtraction:
    """Test suite for country extraction methods."""

    def test_get_country_from_context_au(self):
        """Test extracting AU country code."""
        formatter = ContextFormatter()

        context = "Member Profile:\n- Country: AU\n- Age: 55"
        country = formatter.get_country_from_context(context)

        assert country == "AU"

    def test_get_country_from_context_us(self):
        """Test extracting US country code."""
        formatter = ContextFormatter()

        context = "Member Profile:\n- Country: US\n- Age: 55"
        country = formatter.get_country_from_context(context)

        assert country == "US"

    def test_get_country_from_context_no_country(self):
        """Test default country when not found in context."""
        formatter = ContextFormatter()

        context = "Member Profile:\n- Age: 55"
        country = formatter.get_country_from_context(context)

        # Should default to AU
        assert country == "AU"

    def test_get_country_from_context_invalid_format(self):
        """Test country extraction with invalid format."""
        formatter = ContextFormatter()

        context = "Country is Australia"
        country = formatter.get_country_from_context(context)

        # Should default to AU
        assert country == "AU"


class TestBaseContext:
    """Test suite for base context building."""

    @patch('agents.context_formatter.get_currency')
    @patch('agents.context_formatter.safe_float')
    def test_build_base_context_with_anonymization(self, mock_safe_float, mock_get_currency):
        """Test building base context with anonymization enabled."""
        mock_safe_float.return_value = 500000.0
        mock_get_currency.return_value = "AUD"

        formatter = ContextFormatter()

        member_profile = {
            "name": "John Smith",
            "age": 55,
            "country": "AU",
            "employment_status": "Employed",
            "super_balance": 500000,
            "preservation_age": 60
        }

        context_data = formatter.build_base_context(member_profile, anonymize=True)

        # Check structure
        assert "text" in context_data
        assert "real_name" in context_data
        assert "anonymized_name" in context_data

        # Check values
        assert context_data["real_name"] == "John Smith"
        assert context_data["anonymized_name"].startswith("Member_")

        # Check text content
        text = context_data["text"]
        assert "Member_" in text
        assert "John Smith" not in text
        assert "Age: 55" in text
        assert "Country: AU" in text
        assert "Preservation Age: 60" in text

    @patch('agents.context_formatter.get_currency')
    @patch('agents.context_formatter.safe_float')
    def test_build_base_context_without_anonymization(self, mock_safe_float, mock_get_currency):
        """Test building base context without anonymization."""
        mock_safe_float.return_value = 500000.0
        mock_get_currency.return_value = "AUD"

        formatter = ContextFormatter()

        member_profile = {
            "name": "John Smith",
            "age": 55,
            "country": "AU",
            "employment_status": "Employed",
            "super_balance": 500000
        }

        context_data = formatter.build_base_context(member_profile, anonymize=False)

        # anonymized_name should be None
        assert context_data["anonymized_name"] is None

        # Text should contain real name
        text = context_data["text"]
        assert "John Smith" in text

    @patch('agents.context_formatter.get_currency')
    @patch('agents.context_formatter.safe_float')
    def test_build_base_context_us_member(self, mock_safe_float, mock_get_currency):
        """Test building context for US member (no preservation age)."""
        mock_safe_float.return_value = 500000.0
        mock_get_currency.return_value = "USD"

        formatter = ContextFormatter()

        member_profile = {
            "name": "Jane Doe",
            "age": 60,
            "country": "US",
            "employment_status": "Retired",
            "super_balance": 500000
        }

        context_data = formatter.build_base_context(member_profile, anonymize=False)

        text = context_data["text"]
        # US members should not have preservation age
        assert "Preservation Age" not in text
        assert "Country: US" in text


class TestToolResultsFormatting:
    """Test suite for tool results formatting."""

    def test_format_tool_results_empty(self):
        """Test formatting empty tool results."""
        formatter = ContextFormatter()

        formatted = formatter.format_tool_results({})

        assert formatted == ""

    @patch('agents.context_formatter.get_authority')
    def test_format_tool_results_basic(self, mock_get_authority):
        """Test formatting basic tool results."""
        mock_get_authority.return_value = "Australian Taxation Office"

        formatter = ContextFormatter()

        tool_results = {
            "tax": {
                "tool_name": "ATO Tax Calculator",
                "authority": "Australian Taxation Office",
                "calculation": "12500"
            }
        }

        formatted = formatter.format_tool_results(tool_results, "AU")

        assert "UC FUNCTION RESULTS:" in formatted
        assert "TAX RESULTS:" in formatted
        assert "ATO Tax Calculator" in formatted
        assert "Australian Taxation Office" in formatted
        assert "12500" in formatted

    def test_format_tool_results_with_error(self):
        """Test formatting tool results with error."""
        formatter = ContextFormatter()

        tool_results = {
            "tax": {
                "error": "Calculation failed"
            }
        }

        formatted = formatter.format_tool_results(tool_results, "AU")

        assert "❌ Error: Calculation failed" in formatted

    def test_format_tool_results_india_balance_split(self):
        """Test formatting India tool results with EPF/NPS split."""
        formatter = ContextFormatter()

        tool_results = {
            "withdrawal": {
                "tool_name": "EPFO Withdrawal Calculator",
                "authority": "EPFO",
                "calculation": "2000000",
                "balance_split": {
                    "total_balance": 2000000,
                    "epf_balance": 1500000,
                    "nps_balance": 500000
                }
            }
        }

        formatted = formatter.format_tool_results(tool_results, "IN")

        assert "Total Balance: 2,000,000.00 INR" in formatted
        assert "EPF Balance: 1,500,000.00 INR (75%)" in formatted
        assert "NPS Balance: 500,000.00 INR (25%)" in formatted

    def test_format_tool_results_with_note(self):
        """Test formatting tool results with calculation note."""
        formatter = ContextFormatter()

        tool_results = {
            "tax": {
                "tool_name": "Tax Calculator",
                "authority": "Tax Office",
                "calculation": "10000",
                "calculation_note": "Includes Medicare levy"
            }
        }

        formatted = formatter.format_tool_results(tool_results, "AU")

        assert "Note: Includes Medicare levy" in formatted


class TestFullContext:
    """Test suite for full context building."""

    @patch('agents.context_formatter.get_currency')
    @patch('agents.context_formatter.safe_float')
    def test_build_full_context_with_tools(self, mock_safe_float, mock_get_currency):
        """Test building full context with base context and tool results."""
        mock_safe_float.return_value = 500000.0
        mock_get_currency.return_value = "AUD"

        formatter = ContextFormatter()

        base_context = "Member Profile:\n- Name: John\n- Age: 55"
        tool_results = {
            "tax": {
                "tool_name": "Tax Calculator",
                "authority": "ATO",
                "calculation": "12500"
            }
        }

        full_context = formatter.build_full_context(base_context, tool_results, "AU")

        assert "Member Profile" in full_context
        assert "UC FUNCTION RESULTS" in full_context
        assert "Tax Calculator" in full_context

    def test_build_full_context_no_tools(self):
        """Test building full context without tool results."""
        formatter = ContextFormatter()

        base_context = "Member Profile:\n- Name: John\n- Age: 55"

        full_context = formatter.build_full_context(base_context, {}, "AU")

        # Should just be base context
        assert full_context == base_context


class TestSingletonPattern:
    """Test suite for singleton pattern."""

    def test_get_context_formatter_returns_formatter(self):
        """Test that get_context_formatter returns ContextFormatter instance."""
        formatter = get_context_formatter()

        assert isinstance(formatter, ContextFormatter)

    def test_get_context_formatter_singleton(self):
        """Test that get_context_formatter returns same instance."""
        formatter1 = get_context_formatter()
        formatter2 = get_context_formatter()

        # Should be same instance
        assert formatter1 is formatter2

    def test_get_context_formatter_with_logger(self):
        """Test get_context_formatter with custom logger."""
        mock_logger = Mock()

        # Reset global singleton
        import agents.context_formatter as cf_module
        cf_module._global_formatter = None

        formatter = get_context_formatter(logger=mock_logger)

        assert formatter.logger == mock_logger


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
