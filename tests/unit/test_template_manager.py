"""
Unit tests for prompts.template_manager module.

Tests cover:
- Template initialization and loading
- Template rendering for all countries
- Cache functionality
- Error handling
- Integration with country_config

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from prompts.template_manager import (
    TemplateManager,
    TemplateLoadError,
    TemplateRenderError,
    get_template_manager,
    render_system_prompt_cached
)


class TestTemplateManagerInitialization:
    """Tests for TemplateManager initialization."""

    def test_init_default_templates_dir(self):
        """Test initialization with default templates directory."""
        manager = TemplateManager()
        assert manager.templates_dir.exists()
        assert manager.templates_dir.name == "templates"
        assert manager.enable_cache is True

    def test_init_custom_templates_dir(self):
        """Test initialization with custom templates directory."""
        custom_dir = Path(__file__).parent.parent.parent / "prompts" / "templates"
        manager = TemplateManager(templates_dir=str(custom_dir))
        assert manager.templates_dir == custom_dir

    def test_init_with_logger(self):
        """Test initialization with custom logger."""
        mock_logger = Mock()
        manager = TemplateManager(logger=mock_logger)
        assert manager.logger == mock_logger

    def test_init_cache_disabled(self):
        """Test initialization with cache disabled."""
        manager = TemplateManager(enable_cache=False)
        assert manager.enable_cache is False
        assert isinstance(manager.cache, dict)

    def test_init_invalid_templates_dir(self):
        """Test initialization with non-existent templates directory."""
        with pytest.raises(TemplateLoadError, match="Templates directory not found"):
            TemplateManager(templates_dir="/nonexistent/path")

    def test_jinja_environment_configured(self):
        """Test Jinja2 environment is properly configured."""
        manager = TemplateManager()
        assert manager.env is not None
        assert manager.env.autoescape is False
        assert manager.env.trim_blocks is True
        assert manager.env.lstrip_blocks is True


class TestTemplateLoading:
    """Tests for template loading functionality."""

    def test_load_template_success(self):
        """Test successful template loading."""
        manager = TemplateManager()
        template = manager._load_template("system_prompt.j2")
        assert template is not None
        assert hasattr(template, 'render')

    def test_load_template_not_found(self):
        """Test loading non-existent template."""
        manager = TemplateManager()
        with pytest.raises(TemplateLoadError, match="not found"):
            manager._load_template("nonexistent.j2")

    def test_load_all_required_templates(self):
        """Test loading all required template files."""
        manager = TemplateManager()
        required_templates = [
            "system_prompt.j2",
            "welcome_message.j2",
            "advisor_context.j2",
            "off_topic_decline.j2",
            "validation_prompt.j2",
            "ai_classify_query.j2"
        ]

        for template_name in required_templates:
            template = manager._load_template(template_name)
            assert template is not None, f"Failed to load {template_name}"


class TestSystemPromptRendering:
    """Tests for system prompt template rendering."""

    def test_render_system_prompt_australia(self):
        """Test rendering system prompt for Australia."""
        manager = TemplateManager()
        prompt = manager.render_system_prompt("AU")

        assert "Australian Superannuation Advisor" in prompt
        assert "superannuation" in prompt.lower()
        assert "AUD" in prompt
        assert "preservation age (60)" in prompt.lower()

    def test_render_system_prompt_usa(self):
        """Test rendering system prompt for USA."""
        manager = TemplateManager()
        prompt = manager.render_system_prompt("US")

        assert "U.S. Retirement Advisor" in prompt
        assert "401(k)" in prompt or "IRA" in prompt.lower()
        assert "USD" in prompt

    def test_render_system_prompt_uk(self):
        """Test rendering system prompt for UK."""
        manager = TemplateManager()
        prompt = manager.render_system_prompt("UK")

        assert "UK Pension Advisor" in prompt
        assert "pension" in prompt.lower()
        assert "GBP" in prompt

    def test_render_system_prompt_india(self):
        """Test rendering system prompt for India."""
        manager = TemplateManager()
        prompt = manager.render_system_prompt("IN")

        assert "Indian Provident Fund Advisor" in prompt
        assert "EPF" in prompt or "NPS" in prompt
        assert "INR" in prompt

    def test_system_prompt_contains_response_format(self):
        """Test system prompt contains required formatting instructions."""
        manager = TemplateManager()
        prompt = manager.render_system_prompt("AU")

        assert "RESPONSE FORMAT" in prompt
        assert "Direct Answer" in prompt
        assert "Key Considerations" in prompt
        assert "Recommendation" in prompt

    def test_system_prompt_contains_important_rules(self):
        """Test system prompt contains important rules."""
        manager = TemplateManager()
        prompt = manager.render_system_prompt("US")

        assert "IMPORTANT RULES" in prompt
        assert "Do NOT use emoji" in prompt
        assert "DO use simple, clear English" in prompt


class TestWelcomeMessageRendering:
    """Tests for welcome message template rendering."""

    def test_render_welcome_australia(self):
        """Test rendering welcome message for Australia."""
        manager = TemplateManager()
        message = manager.render_welcome_message("Australia")

        assert "superannuation portal" in message.lower()
        assert "Australian" in message

    def test_render_welcome_usa(self):
        """Test rendering welcome message for USA."""
        manager = TemplateManager()
        message = manager.render_welcome_message("USA")

        assert "401(k)" in message
        assert "IRA" in message or "Social Security" in message

    def test_render_welcome_uk(self):
        """Test rendering welcome message for UK."""
        manager = TemplateManager()
        message = manager.render_welcome_message("United Kingdom")

        assert "pension" in message.lower()
        assert "UK" in message

    def test_render_welcome_india(self):
        """Test rendering welcome message for India."""
        manager = TemplateManager()
        message = manager.render_welcome_message("India")

        assert "EPF" in message or "NPS" in message
        assert "India" in message

    def test_welcome_message_country_code(self):
        """Test welcome message with country code (AU, US, UK, IN)."""
        manager = TemplateManager()

        for country_code in ["AU", "US", "UK", "IN"]:
            message = manager.render_welcome_message(country_code)
            assert len(message) > 0


class TestAdvisorContextRendering:
    """Tests for advisor context template rendering."""

    def test_render_advisor_context_australia(self):
        """Test rendering advisor context for Australia."""
        manager = TemplateManager()
        context = manager.render_advisor_context("AU")

        assert "Australian Superannuation Fund Advisor" in context
        assert "ATO" in context
        assert "superannuation" in context.lower()

    def test_render_advisor_context_usa(self):
        """Test rendering advisor context for USA."""
        manager = TemplateManager()
        context = manager.render_advisor_context("US")

        assert "U.S. Retirement Advisor" in context
        assert "401(k)" in context
        assert "IRS" in context

    def test_render_advisor_context_uk(self):
        """Test rendering advisor context for UK."""
        manager = TemplateManager()
        context = manager.render_advisor_context("UK")

        assert "UK Pension Advisor" in context
        assert "HMRC" in context

    def test_render_advisor_context_india(self):
        """Test rendering advisor context for India."""
        manager = TemplateManager()
        context = manager.render_advisor_context("IN")

        assert "Indian Provident Fund Advisor" in context
        assert "EPF" in context
        assert "EPFO" in context


class TestOffTopicDeclineRendering:
    """Tests for off-topic decline message rendering."""

    def test_render_off_topic_decline_basic(self):
        """Test basic off-topic decline rendering."""
        manager = TemplateManager()
        message = manager.render_off_topic_decline("John Smith", "vacation_planning")

        assert "Hi John Smith" in message
        assert "vacation planning" in message.lower()
        assert "retirement planning" in message.lower()

    def test_off_topic_decline_formatting(self):
        """Test classification formatting (underscore to space)."""
        manager = TemplateManager()
        message = manager.render_off_topic_decline("Jane Doe", "cooking_recipes")

        assert "cooking recipes" in message
        assert "cooking_recipes" not in message

    def test_off_topic_decline_contains_capabilities(self):
        """Test decline message contains advisor capabilities."""
        manager = TemplateManager()
        message = manager.render_off_topic_decline("Test User", "sports")

        assert "Retirement savings" in message
        assert "Withdrawal rules" in message
        assert "Tax implications" in message

    def test_off_topic_decline_polite_tone(self):
        """Test decline message has polite tone."""
        manager = TemplateManager()
        message = manager.render_off_topic_decline("User", "weather")

        assert "Thank you" in message
        assert "I can help you with" in message


class TestValidationPromptRendering:
    """Tests for validation prompt template rendering."""

    def test_render_validation_prompt_basic(self):
        """Test basic validation prompt rendering."""
        manager = TemplateManager()

        prompt = manager.render_validation_prompt(
            user_query="How much tax will I pay?",
            member_info="Age: 65, Balance: $500,000",
            tool_info="Tax calculated: $75,000",
            tool_status="✓ All tools executed successfully",
            response_text="You will pay $75,000 in tax.",
            response_length=32
        )

        assert "How much tax will I pay?" in prompt
        assert "Age: 65" in prompt
        assert "Tax calculated: $75,000" in prompt
        assert "32 CHARACTERS" in prompt

    def test_validation_prompt_contains_criteria(self):
        """Test validation prompt contains all criteria."""
        manager = TemplateManager()

        prompt = manager.render_validation_prompt(
            user_query="Test query",
            member_info="Test info",
            tool_info="Test tools",
            tool_status="Success",
            response_text="Test response",
            response_length=13
        )

        assert "VALIDATION CRITERIA" in prompt
        assert "TOOL EXECUTION" in prompt
        assert "QUESTION ANSWERING" in prompt
        assert "SPECIFICITY" in prompt
        assert "ACCURACY" in prompt

    def test_validation_prompt_json_format(self):
        """Test validation prompt specifies JSON format."""
        manager = TemplateManager()

        prompt = manager.render_validation_prompt(
            user_query="Test",
            member_info="Info",
            tool_info="Tools",
            tool_status="Status",
            response_text="Response",
            response_length=8
        )

        assert "JSON FORMAT REQUIREMENTS" in prompt
        assert '"passed": true/false' in prompt
        assert '"confidence":' in prompt
        assert '"violations"' in prompt


class TestAIClassifyQueryRendering:
    """Tests for ai_classify SQL query rendering."""

    def test_render_ai_classify_query_basic(self):
        """Test basic ai_classify query rendering."""
        manager = TemplateManager()
        query = manager.render_ai_classify_query("Can I withdraw from my 401k?")

        assert "SELECT ai_classify(" in query
        assert "Can I withdraw from my 401k?" in query
        assert "ARRAY(" in query

    def test_ai_classify_query_contains_categories(self):
        """Test query contains all classification categories."""
        manager = TemplateManager()
        query = manager.render_ai_classify_query("Test query")

        assert "retirement_planning" in query
        assert "401k" in query or "401(k)" in query
        assert "EPF" in query
        assert "NPS" in query
        assert "SIPP" in query
        assert "off_topic" in query

    def test_ai_classify_query_escapes_quotes(self):
        """Test single quotes are escaped for SQL."""
        manager = TemplateManager()
        query = manager.render_ai_classify_query("What's my balance?")

        assert "What''s my balance?" in query
        assert "What's my balance?" not in query.replace("What''s", "What's")


class TestCacheFunctionality:
    """Tests for template caching."""

    def test_cache_enabled_by_default(self):
        """Test cache is enabled by default."""
        manager = TemplateManager()
        assert manager.enable_cache is True

    def test_cache_stores_rendered_templates(self):
        """Test rendered templates are cached."""
        manager = TemplateManager(enable_cache=True)

        # First render
        prompt1 = manager.render_system_prompt("AU")
        assert len(manager.cache) > 0

        # Second render should use cache
        prompt2 = manager.render_system_prompt("AU")
        assert prompt1 == prompt2

    def test_cache_disabled_no_storage(self):
        """Test cache disabled doesn't store templates."""
        manager = TemplateManager(enable_cache=False)

        manager.render_system_prompt("AU")
        assert len(manager.cache) == 0

    def test_clear_cache(self):
        """Test cache clearing."""
        manager = TemplateManager(enable_cache=True)

        manager.render_system_prompt("AU")
        assert len(manager.cache) > 0

        manager.clear_cache()
        assert len(manager.cache) == 0

    def test_get_cache_info(self):
        """Test cache info retrieval."""
        manager = TemplateManager(enable_cache=True)

        manager.render_system_prompt("AU")
        manager.render_welcome_message("US")

        info = manager.get_cache_info()
        assert info["enabled"] is True
        assert info["size"] >= 2
        assert isinstance(info["keys"], list)

    def test_cache_uses_unique_keys(self):
        """Test cache uses unique keys for different templates."""
        manager = TemplateManager(enable_cache=True)

        manager.render_system_prompt("AU")
        manager.render_system_prompt("US")
        manager.render_welcome_message("AU")

        info = manager.get_cache_info()
        assert info["size"] == 3
        assert "system_prompt:AU" in info["keys"]
        assert "system_prompt:US" in info["keys"]
        assert "welcome:AU" in info["keys"]


class TestErrorHandling:
    """Tests for error handling."""

    def test_template_load_error_missing_file(self):
        """Test error when template file is missing."""
        manager = TemplateManager()

        with pytest.raises(TemplateLoadError, match="not found"):
            manager._load_template("missing_template.j2")

    def test_template_render_error_invalid_context(self):
        """Test error when rendering with invalid context."""
        # Create temporary template with undefined variable
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "templates"
            template_dir.mkdir()

            template_file = template_dir / "test.j2"
            template_file.write_text("{{ undefined_variable }}")

            manager = TemplateManager(templates_dir=str(template_dir))

            # Should render but leave variable undefined (Jinja2 default)
            result = manager._render_template("test.j2", {})
            assert result == ""

    def test_get_country_context_integration(self):
        """Test country context retrieval integration."""
        manager = TemplateManager()

        context = manager._get_country_context("AU")
        assert "country" in context
        assert "advisor_title" in context
        assert "regulatory_context" in context
        assert "currency" in context
        assert context["country"] == "AU"


class TestGlobalSingleton:
    """Tests for global singleton instance."""

    def test_get_template_manager_creates_singleton(self):
        """Test get_template_manager creates singleton instance."""
        manager1 = get_template_manager()
        manager2 = get_template_manager()

        assert manager1 is manager2

    def test_cached_render_function(self):
        """Test cached render function."""
        prompt1 = render_system_prompt_cached("AU")
        prompt2 = render_system_prompt_cached("AU")

        assert prompt1 == prompt2
        assert "Australian Superannuation Advisor" in prompt1


class TestIntegrationWithCountryConfig:
    """Tests for integration with country_config module."""

    def test_system_prompt_uses_country_config(self):
        """Test system prompt integrates with country_config."""
        manager = TemplateManager()

        au_prompt = manager.render_system_prompt("AU")
        us_prompt = manager.render_system_prompt("US")

        # Different prompts for different countries
        assert au_prompt != us_prompt

        # AU-specific content
        assert "superannuation" in au_prompt.lower()
        assert "AUD" in au_prompt

        # US-specific content
        assert "401(k)" in us_prompt or "IRA" in us_prompt.lower()
        assert "USD" in us_prompt

    def test_special_instructions_integrated(self):
        """Test special instructions are integrated when present."""
        manager = TemplateManager()

        # Australia has special instructions about preservation age
        au_prompt = manager.render_system_prompt("AU")
        assert "preservation age (60)" in au_prompt.lower()


# Performance and edge case tests
class TestPerformanceAndEdgeCases:
    """Tests for performance and edge cases."""

    def test_render_multiple_templates_performance(self):
        """Test rendering multiple templates is performant."""
        manager = TemplateManager(enable_cache=True)

        # First render (uncached)
        for country in ["AU", "US", "UK", "IN"]:
            manager.render_system_prompt(country)
            manager.render_welcome_message(country)
            manager.render_advisor_context(country)

        # Second render (cached) should be instant
        for country in ["AU", "US", "UK", "IN"]:
            manager.render_system_prompt(country)
            manager.render_welcome_message(country)
            manager.render_advisor_context(country)

    def test_special_characters_in_query(self):
        """Test handling special characters in queries."""
        manager = TemplateManager()

        query = manager.render_ai_classify_query("What's my 401(k) balance?")
        assert "What''s my 401(k) balance?" in query

    def test_empty_values_handled(self):
        """Test empty values are handled gracefully."""
        manager = TemplateManager()

        decline = manager.render_off_topic_decline("", "")
        assert "Hi " in decline

    def test_long_response_text_validation(self):
        """Test validation prompt with long response text."""
        manager = TemplateManager()

        long_response = "This is a test response. " * 100

        prompt = manager.render_validation_prompt(
            user_query="Test",
            member_info="Info",
            tool_info="Tools",
            tool_status="Success",
            response_text=long_response,
            response_length=len(long_response)
        )

        assert long_response in prompt
        assert str(len(long_response)) in prompt
