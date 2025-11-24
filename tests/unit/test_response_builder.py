"""
Unit tests for agents.response_builder module.

Tests cover:
- ResponseBuilder initialization
- Response generation with token tracking
- Cost calculation
- Error handling and fallback responses
- Template integration
- Context terminology updates
- Singleton pattern

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from dataclasses import dataclass
import time

from agents.response_builder import (
    ResponseBuilder,
    get_response_builder,
    ResponseResult,
    ResponseGenerationError,
    _global_builder
)


class TestResponseResult:
    """Test suite for ResponseResult dataclass."""

    def test_response_result_creation(self):
        """Test creating ResponseResult instance."""
        result = ResponseResult(
            text="Test response",
            input_tokens=100,
            output_tokens=50,
            cost=0.005,
            duration=1.2
        )

        assert result.text == "Test response"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.cost == 0.005
        assert result.duration == 1.2
        assert result.error is None

    def test_response_result_with_error(self):
        """Test ResponseResult with error."""
        result = ResponseResult(
            text="Error response",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            duration=0.5,
            error="Test error"
        )

        assert result.error == "Test error"


class TestResponseBuilderInitialization:
    """Test suite for ResponseBuilder initialization."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_init_default_parameters(self, mock_context_formatter, mock_get_template, mock_workspace_client):
        """Test ResponseBuilder initialization with default parameters."""
        mock_workspace = Mock()
        mock_workspace_client.return_value = mock_workspace
        mock_template = Mock()
        mock_get_template.return_value = mock_template

        builder = ResponseBuilder()

        assert builder.workspace_client == mock_workspace
        assert builder.model_type == "claude-sonnet-4"
        assert builder.temperature == 0.1  # MAIN_LLM_TEMPERATURE from config
        assert builder.max_tokens == 2000  # MAIN_LLM_MAX_TOKENS from config

    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_init_custom_parameters(self, mock_context_formatter, mock_get_template):
        """Test ResponseBuilder initialization with custom parameters."""
        mock_workspace = Mock()
        mock_logger = Mock()
        mock_template = Mock()
        mock_get_template.return_value = mock_template

        builder = ResponseBuilder(
            workspace_client=mock_workspace,
            llm_endpoint="custom-endpoint",
            model_type="claude-opus-4-1",
            temperature=0.5,
            max_tokens=1000,
            logger=mock_logger
        )

        assert builder.workspace_client == mock_workspace
        assert builder.llm_endpoint == "custom-endpoint"
        assert builder.model_type == "claude-opus-4-1"
        assert builder.temperature == 0.5
        assert builder.max_tokens == 1000
        assert builder.logger == mock_logger


class TestModelTypeDetection:
    """Test suite for model type detection."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_determine_model_type_opus(self, mock_context_formatter, mock_get_template, mock_workspace_client):
        """Test model type detection for Opus."""
        builder = ResponseBuilder()
        model_type = builder._determine_model_type("databricks-claude-opus-4")

        assert model_type == "claude-opus-4-1"

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_determine_model_type_sonnet(self, mock_context_formatter, mock_get_template, mock_workspace_client):
        """Test model type detection for Sonnet."""
        builder = ResponseBuilder()
        model_type = builder._determine_model_type("databricks-claude-sonnet-4")

        assert model_type == "claude-sonnet-4"

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_determine_model_type_haiku(self, mock_context_formatter, mock_get_template, mock_workspace_client):
        """Test model type detection for Haiku."""
        builder = ResponseBuilder()
        model_type = builder._determine_model_type("databricks-claude-haiku-4")

        assert model_type == "claude-haiku-4"

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_determine_model_type_unknown(self, mock_context_formatter, mock_get_template, mock_workspace_client):
        """Test model type detection for unknown model (defaults to sonnet)."""
        builder = ResponseBuilder()
        model_type = builder._determine_model_type("unknown-model")

        assert model_type == "claude-sonnet-4"


class TestSystemPromptBuilding:
    """Test suite for system prompt building."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_build_system_prompt(self, mock_context_formatter, mock_get_template, mock_workspace_client):
        """Test building system prompt."""
        mock_template_manager = Mock()
        mock_template_manager.render_system_prompt.return_value = "Base system prompt"
        mock_get_template.return_value = mock_template_manager

        builder = ResponseBuilder()
        system_prompt = builder._build_system_prompt(
            country="AU",
            context="Member Profile: Age 55",
            user_query="How much can I withdraw?"
        )

        assert "Base system prompt" in system_prompt
        assert "MEMBER CONTEXT:" in system_prompt
        assert "Member Profile: Age 55" in system_prompt
        assert "USER QUESTION:" in system_prompt
        assert "How much can I withdraw?" in system_prompt


class TestContextTerminology:
    """Test suite for context terminology updates."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    @patch('agents.response_builder.get_country_config')
    @patch('agents.response_builder.get_balance_terminology')
    def test_update_context_terminology(
        self, mock_get_balance, mock_get_config, mock_context_formatter,
        mock_get_template, mock_workspace_client
    ):
        """Test updating context terminology for country."""
        mock_config = Mock()
        mock_config.retirement_account_term = "superannuation"
        mock_get_config.return_value = mock_config
        mock_get_balance.return_value = "super balance"

        builder = ResponseBuilder()

        context = "Your superbalance is $500,000"
        updated = builder._update_context_terminology(context, "AU")

        assert "super balance" in updated
        assert "superbalance" not in updated
        assert "superannuation balance" in updated


class TestTokenExtraction:
    """Test suite for token extraction and estimation."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_extract_token_usage_from_response(
        self, mock_context_formatter, mock_get_template, mock_workspace_client
    ):
        """Test extracting token usage from LLM response."""
        builder = ResponseBuilder()

        # Mock response with usage
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 200
        mock_response.usage = mock_usage

        input_tokens, output_tokens = builder._extract_token_usage(mock_response)

        assert input_tokens == 500
        assert output_tokens == 200

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_extract_token_usage_no_usage(
        self, mock_context_formatter, mock_get_template, mock_workspace_client
    ):
        """Test token extraction when usage not available."""
        builder = ResponseBuilder()

        # Mock response without usage
        mock_response = Mock()
        mock_response.usage = None

        input_tokens, output_tokens = builder._extract_token_usage(mock_response)

        assert input_tokens == 0
        assert output_tokens == 0

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_estimate_tokens(
        self, mock_context_formatter, mock_get_template, mock_workspace_client
    ):
        """Test token estimation when not available from API."""
        builder = ResponseBuilder()

        system_prompt = "A" * 400  # 400 chars
        full_context = "B" * 600  # 600 chars

        input_tokens, output_tokens = builder._estimate_tokens(system_prompt, full_context)

        # 1000 chars / 4 = 250 tokens
        assert input_tokens == 250
        assert output_tokens == 150  # Default estimate


class TestResponseTextExtraction:
    """Test suite for response text extraction."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_extract_response_text_with_choices(
        self, mock_context_formatter, mock_get_template, mock_workspace_client
    ):
        """Test extracting response text with choices."""
        builder = ResponseBuilder()

        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Test response text"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        text = builder._extract_response_text(mock_response)

        assert text == "Test response text"

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    def test_extract_response_text_no_choices(
        self, mock_context_formatter, mock_get_template, mock_workspace_client
    ):
        """Test extracting response text without choices (fallback to str)."""
        builder = ResponseBuilder()

        mock_response = "Direct response string"

        text = builder._extract_response_text(mock_response)

        assert text == "Direct response string"


class TestResponseGeneration:
    """Test suite for response generation."""

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    @patch('agents.response_builder.calculate_llm_cost')
    @patch('time.time')
    def test_generate_response_success(
        self, mock_time, mock_calculate_cost, mock_context_formatter_cls,
        mock_get_template, mock_workspace_client
    ):
        """Test successful response generation."""
        # Setup mocks
        mock_time.side_effect = [0, 1.5]  # Start and end times
        mock_calculate_cost.return_value = 0.005

        mock_workspace = Mock()
        mock_workspace_client.return_value = mock_workspace

        # Mock LLM response
        mock_llm_response = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 200
        mock_llm_response.usage = mock_usage

        mock_message = Mock()
        mock_message.content = "This is the AI response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_llm_response.choices = [mock_choice]

        mock_workspace.serving_endpoints.query.return_value = mock_llm_response

        # Mock template manager
        mock_template_manager = Mock()
        mock_template_manager.render_system_prompt.return_value = "System prompt"
        mock_get_template.return_value = mock_template_manager

        # Mock context formatter
        mock_formatter = Mock()
        mock_formatter.format_tool_results.return_value = "Formatted tools"
        mock_context_formatter_cls.return_value = mock_formatter

        # Create builder and generate response
        builder = ResponseBuilder(workspace_client=mock_workspace)
        result = builder.generate_response(
            user_query="Test query",
            context="Test context",
            tool_results={"tax": {"calculation": "5000"}},
            country="AU"
        )

        # Assertions
        assert isinstance(result, ResponseResult)
        assert result.text == "This is the AI response"
        assert result.input_tokens == 500
        assert result.output_tokens == 200
        assert result.cost == 0.005
        assert result.duration == 1.5
        assert result.error is None

    @patch('agents.response_builder.WorkspaceClient')
    @patch('agents.response_builder.get_template_manager')
    @patch('agents.response_builder.ContextFormatter')
    @patch('time.time')
    def test_generate_response_error_handling(
        self, mock_time, mock_context_formatter_cls,
        mock_get_template, mock_workspace_client
    ):
        """Test response generation error handling."""
        mock_time.side_effect = [0, 0.5]  # Start and end times

        mock_workspace = Mock()
        mock_workspace_client.return_value = mock_workspace

        # Mock LLM error
        mock_workspace.serving_endpoints.query.side_effect = Exception("API Error")

        # Mock template manager
        mock_template_manager = Mock()
        mock_template_manager.render_system_prompt.return_value = "System prompt"
        mock_get_template.return_value = mock_template_manager

        # Mock context formatter
        mock_formatter = Mock()
        mock_formatter.format_tool_results.return_value = ""
        mock_context_formatter_cls.return_value = mock_formatter

        # Create builder and generate response
        builder = ResponseBuilder(workspace_client=mock_workspace)
        result = builder.generate_response(
            user_query="Test query",
            context="Test context",
            tool_results={},
            country="AU"
        )

        # Should return error response
        assert isinstance(result, ResponseResult)
        assert "error generating your response" in result.text.lower()
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.cost == 0.0
        assert result.error is not None


class TestSingletonPattern:
    """Test suite for singleton pattern."""

    def test_get_response_builder_returns_builder(self):
        """Test that get_response_builder returns ResponseBuilder instance."""
        with patch('agents.response_builder.WorkspaceClient'), \
             patch('agents.response_builder.get_template_manager'), \
             patch('agents.response_builder.ContextFormatter'):
            builder = get_response_builder()
            assert isinstance(builder, ResponseBuilder)

    def test_get_response_builder_singleton(self):
        """Test that get_response_builder returns same instance."""
        with patch('agents.response_builder.WorkspaceClient'), \
             patch('agents.response_builder.get_template_manager'), \
             patch('agents.response_builder.ContextFormatter'):

            # Reset global singleton
            import agents.response_builder as rb_module
            rb_module._global_builder = None

            builder1 = get_response_builder()
            builder2 = get_response_builder()

            # Should be same instance
            assert builder1 is builder2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
