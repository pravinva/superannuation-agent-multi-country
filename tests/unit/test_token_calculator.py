"""
Unit tests for validation.token_calculator module.

Tests cover:
- TokenCalculator initialization
- Token extraction from LLM responses
- Token estimation when not available
- Cost calculation
- Token metrics building
- Zero metrics for fallback scenarios
- Singleton pattern

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from validation.token_calculator import (
    TokenCalculator,
    get_token_calculator,
    _global_calculator
)


class TestTokenCalculatorInitialization:
    """Test suite for TokenCalculator initialization."""

    def test_init_creates_calculator(self):
        """Test TokenCalculator initialization."""
        calculator = TokenCalculator()
        assert calculator is not None

    def test_init_without_args(self):
        """Test TokenCalculator can be initialized without arguments."""
        calculator = TokenCalculator()
        assert calculator is not None


class TestTokenExtraction:
    """Test suite for token extraction from responses."""

    def test_extract_tokens_with_usage(self):
        """Test extracting tokens from response with usage attribute."""
        calculator = TokenCalculator()

        # Mock response with usage
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 200
        mock_response.usage = mock_usage

        input_tokens, output_tokens = calculator.extract_tokens(mock_response)

        assert input_tokens == 500
        assert output_tokens == 200

    def test_extract_tokens_without_usage(self):
        """Test token extraction when response has no usage attribute."""
        calculator = TokenCalculator()

        # Mock response without usage
        mock_response = Mock()
        mock_response.usage = None

        input_tokens, output_tokens = calculator.extract_tokens(mock_response)

        assert input_tokens == 0
        assert output_tokens == 0

    def test_extract_tokens_with_partial_usage(self):
        """Test token extraction with partial usage data."""
        calculator = TokenCalculator()

        # Mock response with partial usage
        mock_response = Mock()
        mock_usage = Mock(spec=[])  # Empty spec means no attributes
        mock_response.usage = mock_usage

        input_tokens, output_tokens = calculator.extract_tokens(mock_response)

        # Should fall back to 0
        assert input_tokens == 0
        assert output_tokens == 0

    def test_extract_tokens_with_zero_values(self):
        """Test token extraction with zero token values."""
        calculator = TokenCalculator()

        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 0
        mock_usage.completion_tokens = 0
        mock_response.usage = mock_usage

        input_tokens, output_tokens = calculator.extract_tokens(mock_response)

        assert input_tokens == 0
        assert output_tokens == 0


class TestTokenEstimation:
    """Test suite for token estimation."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        calculator = TokenCalculator()

        text = "A" * 400  # 400 chars
        input_tokens, output_tokens = calculator.estimate_tokens(text)

        # 400 chars / 4 = 100 tokens
        assert input_tokens == 100
        assert output_tokens == 100  # Default

    def test_estimate_tokens_custom_output(self):
        """Test token estimation with custom output estimate."""
        calculator = TokenCalculator()

        text = "A" * 800  # 800 chars
        input_tokens, output_tokens = calculator.estimate_tokens(text, output_estimate=250)

        assert input_tokens == 200  # 800 / 4
        assert output_tokens == 250

    def test_estimate_tokens_empty_string(self):
        """Test token estimation with empty string."""
        calculator = TokenCalculator()

        input_tokens, output_tokens = calculator.estimate_tokens("")

        assert input_tokens == 0
        assert output_tokens == 100  # Default

    def test_estimate_tokens_short_text(self):
        """Test token estimation with short text."""
        calculator = TokenCalculator()

        text = "Hello"  # 5 chars
        input_tokens, output_tokens = calculator.estimate_tokens(text)

        assert input_tokens == 1  # 5 / 4 = 1
        assert output_tokens == 100


class TestCostCalculation:
    """Test suite for cost calculation."""

    @patch('validation.token_calculator.calculate_llm_cost')
    def test_calculate_cost_basic(self, mock_calculate_cost):
        """Test basic cost calculation."""
        mock_calculate_cost.return_value = 0.005

        calculator = TokenCalculator()
        cost = calculator.calculate_cost(500, 200, "claude-sonnet-4")

        assert cost == 0.005
        mock_calculate_cost.assert_called_once_with(500, 200, "claude-sonnet-4")

    @patch('validation.token_calculator.calculate_llm_cost')
    def test_calculate_cost_opus(self, mock_calculate_cost):
        """Test cost calculation for Opus model."""
        mock_calculate_cost.return_value = 0.015

        calculator = TokenCalculator()
        cost = calculator.calculate_cost(500, 200, "claude-opus-4-1")

        assert cost == 0.015
        mock_calculate_cost.assert_called_once_with(500, 200, "claude-opus-4-1")

    @patch('validation.token_calculator.calculate_llm_cost')
    def test_calculate_cost_haiku(self, mock_calculate_cost):
        """Test cost calculation for Haiku model."""
        mock_calculate_cost.return_value = 0.001

        calculator = TokenCalculator()
        cost = calculator.calculate_cost(500, 200, "claude-haiku-4")

        assert cost == 0.001
        mock_calculate_cost.assert_called_once_with(500, 200, "claude-haiku-4")

    @patch('validation.token_calculator.calculate_llm_cost')
    def test_calculate_cost_zero_tokens(self, mock_calculate_cost):
        """Test cost calculation with zero tokens."""
        mock_calculate_cost.return_value = 0.0

        calculator = TokenCalculator()
        cost = calculator.calculate_cost(0, 0, "claude-sonnet-4")

        assert cost == 0.0
        mock_calculate_cost.assert_called_once_with(0, 0, "claude-sonnet-4")


class TestTokenMetrics:
    """Test suite for token metrics building."""

    def test_build_token_metrics_basic(self):
        """Test building basic token metrics."""
        calculator = TokenCalculator()

        metrics = calculator.build_token_metrics(
            input_tokens=500,
            output_tokens=200,
            cost=0.005,
            model_type="claude-sonnet-4",
            duration=1.5
        )

        assert metrics['input_tokens'] == 500
        assert metrics['output_tokens'] == 200
        assert metrics['total_tokens'] == 700
        assert metrics['cost'] == 0.005
        assert metrics['model'] == "claude-sonnet-4"
        assert metrics['duration'] == 1.5

    def test_build_token_metrics_zero_values(self):
        """Test building token metrics with zero values."""
        calculator = TokenCalculator()

        metrics = calculator.build_token_metrics(
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            model_type="deterministic",
            duration=0.0
        )

        assert metrics['input_tokens'] == 0
        assert metrics['output_tokens'] == 0
        assert metrics['total_tokens'] == 0
        assert metrics['cost'] == 0.0
        assert metrics['model'] == "deterministic"
        assert metrics['duration'] == 0.0

    def test_build_token_metrics_structure(self):
        """Test token metrics structure has all required fields."""
        calculator = TokenCalculator()

        metrics = calculator.build_token_metrics(100, 50, 0.002, "claude-sonnet-4", 0.8)

        # Check all required fields exist
        assert 'input_tokens' in metrics
        assert 'output_tokens' in metrics
        assert 'total_tokens' in metrics
        assert 'cost' in metrics
        assert 'model' in metrics
        assert 'duration' in metrics


class TestZeroMetrics:
    """Test suite for zero metrics building."""

    def test_build_zero_metrics_default(self):
        """Test building zero metrics with default model."""
        calculator = TokenCalculator()

        metrics = calculator.build_zero_metrics()

        assert metrics['input_tokens'] == 0
        assert metrics['output_tokens'] == 0
        assert metrics['total_tokens'] == 0
        assert metrics['cost'] == 0.0
        assert metrics['model'] == "none"
        assert metrics['duration'] == 0.0

    def test_build_zero_metrics_custom_model(self):
        """Test building zero metrics with custom model type."""
        calculator = TokenCalculator()

        metrics = calculator.build_zero_metrics("deterministic")

        assert metrics['input_tokens'] == 0
        assert metrics['output_tokens'] == 0
        assert metrics['total_tokens'] == 0
        assert metrics['cost'] == 0.0
        assert metrics['model'] == "deterministic"
        assert metrics['duration'] == 0.0

    def test_build_zero_metrics_structure(self):
        """Test zero metrics has same structure as regular metrics."""
        calculator = TokenCalculator()

        zero_metrics = calculator.build_zero_metrics()
        regular_metrics = calculator.build_token_metrics(100, 50, 0.002, "test", 1.0)

        # Should have same keys
        assert set(zero_metrics.keys()) == set(regular_metrics.keys())


class TestSingletonPattern:
    """Test suite for singleton pattern."""

    def test_get_token_calculator_returns_calculator(self):
        """Test that get_token_calculator returns TokenCalculator instance."""
        calculator = get_token_calculator()

        assert isinstance(calculator, TokenCalculator)

    def test_get_token_calculator_singleton(self):
        """Test that get_token_calculator returns same instance."""
        # Reset global singleton
        import validation.token_calculator as tc_module
        tc_module._global_calculator = None

        calculator1 = get_token_calculator()
        calculator2 = get_token_calculator()

        # Should be same instance
        assert calculator1 is calculator2


class TestIntegration:
    """Integration tests for TokenCalculator."""

    @patch('validation.token_calculator.calculate_llm_cost')
    def test_full_workflow_with_response(self, mock_calculate_cost):
        """Test full workflow: extract tokens, calculate cost, build metrics."""
        mock_calculate_cost.return_value = 0.005

        calculator = TokenCalculator()

        # Mock response
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 200
        mock_response.usage = mock_usage

        # Extract tokens
        input_tokens, output_tokens = calculator.extract_tokens(mock_response)

        # Calculate cost
        cost = calculator.calculate_cost(input_tokens, output_tokens, "claude-sonnet-4")

        # Build metrics
        metrics = calculator.build_token_metrics(
            input_tokens, output_tokens, cost, "claude-sonnet-4", 1.5
        )

        assert metrics['input_tokens'] == 500
        assert metrics['output_tokens'] == 200
        assert metrics['total_tokens'] == 700
        assert metrics['cost'] == 0.005
        assert metrics['model'] == "claude-sonnet-4"
        assert metrics['duration'] == 1.5

    @patch('validation.token_calculator.calculate_llm_cost')
    def test_full_workflow_with_estimation(self, mock_calculate_cost):
        """Test full workflow with token estimation fallback."""
        mock_calculate_cost.return_value = 0.003

        calculator = TokenCalculator()

        # Mock response without usage
        mock_response = Mock()
        mock_response.usage = None

        # Extract tokens (will be 0)
        input_tokens, output_tokens = calculator.extract_tokens(mock_response)

        # Estimate tokens if extraction failed
        if input_tokens == 0 and output_tokens == 0:
            validation_prompt = "A" * 800
            input_tokens, output_tokens = calculator.estimate_tokens(validation_prompt)

        # Calculate cost
        cost = calculator.calculate_cost(input_tokens, output_tokens, "claude-sonnet-4")

        # Build metrics
        metrics = calculator.build_token_metrics(
            input_tokens, output_tokens, cost, "claude-sonnet-4", 1.2
        )

        assert metrics['input_tokens'] == 200  # 800 / 4
        assert metrics['output_tokens'] == 100  # Default
        assert metrics['total_tokens'] == 300
        assert metrics['cost'] == 0.003
        assert metrics['model'] == "claude-sonnet-4"
        assert metrics['duration'] == 1.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
