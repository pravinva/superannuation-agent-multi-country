from shared.logging_config import get_logger

logger = get_logger(__name__)

"""
validation.token_calculator
============================

Token tracking and cost calculation for validation operations.

This module provides:
- Token extraction from LLM responses
- Token estimation when not available from API
- Cost calculation using config.calculate_llm_cost
- Structured token/cost data for validation results

Extracted from validation.py to improve modularity and testability.

Usage:
    >>> from validation.token_calculator import TokenCalculator
    >>>
    >>> calculator = TokenCalculator()
    >>> tokens = calculator.extract_tokens(response)
    >>> cost = calculator.calculate_cost(input_tokens, output_tokens, "claude-sonnet-4")

Author: Refactoring Team
Date: 2024-11-24
"""

from typing import Any, Dict, Tuple, Optional
from config import calculate_llm_cost


class TokenCalculator:
    """
    Token tracking and cost calculation for validation operations.

    Provides methods for extracting token usage from LLM responses,
    estimating tokens when not available, and calculating costs.
    """

    def __init__(self):
        """Initialize token calculator."""
        pass

    def extract_tokens(self, response: Any) -> Tuple[int, int]:
        """
        Extract token usage from LLM response.

        Args:
            response: LLM response object

        Returns:
            Tuple of (input_tokens, output_tokens)

        Examples:
            >>> calculator = TokenCalculator()
            >>> mock_response = Mock()
            >>> mock_response.usage.prompt_tokens = 500
            >>> mock_response.usage.completion_tokens = 200
            >>> input_tokens, output_tokens = calculator.extract_tokens(mock_response)
            >>> assert input_tokens == 500
            >>> assert output_tokens == 200
        """
        input_tokens = 0
        output_tokens = 0

        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)
            logger.info(f"📊 Token usage: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
        else:
            logger.info(f"⚠️ Token usage not available from response")

        return input_tokens, output_tokens

    def estimate_tokens(self, text: str, output_estimate: int = 100) -> Tuple[int, int]:
        """
        Estimate token usage when not available from API.

        Uses rough heuristic: 1 token ≈ 4 characters for input.

        Args:
            text: Input text to estimate tokens for
            output_estimate: Estimated output tokens (default: 100)

        Returns:
            Tuple of (estimated_input_tokens, estimated_output_tokens)

        Examples:
            >>> calculator = TokenCalculator()
            >>> text = "A" * 400  # 400 chars
            >>> input_tokens, output_tokens = calculator.estimate_tokens(text)
            >>> assert input_tokens == 100  # 400 / 4
            >>> assert output_tokens == 100  # default
        """
        # Rough estimate: 1 token ≈ 4 characters
        input_tokens = len(text) // 4
        output_tokens = output_estimate

        logger.info(f"⚠️ Token usage not available, estimated: {input_tokens} input + {output_tokens} output")

        return input_tokens, output_tokens

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_type: str
    ) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_type: Model type (e.g., "claude-sonnet-4")

        Returns:
            Cost in dollars

        Examples:
            >>> calculator = TokenCalculator()
            >>> cost = calculator.calculate_cost(500, 200, "claude-sonnet-4")
            >>> assert cost > 0
        """
        cost = calculate_llm_cost(input_tokens, output_tokens, model_type)
        logger.info(f"💰 Validation cost: ${cost:.6f} ({model_type})")

        return cost

    def build_token_metrics(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        model_type: str,
        duration: float
    ) -> Dict[str, Any]:
        """
        Build structured token/cost metrics dictionary.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Cost in dollars
            model_type: Model type used
            duration: Operation duration in seconds

        Returns:
            Dictionary with token metrics

        Examples:
            >>> calculator = TokenCalculator()
            >>> metrics = calculator.build_token_metrics(500, 200, 0.005, "claude-sonnet-4", 1.5)
            >>> assert metrics['input_tokens'] == 500
            >>> assert metrics['total_tokens'] == 700
            >>> assert metrics['cost'] == 0.005
        """
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'model': model_type,
            'duration': duration
        }

    def build_zero_metrics(self, model_type: str = "none") -> Dict[str, Any]:
        """
        Build zero token metrics for fallback scenarios.

        Args:
            model_type: Model type (default: "none")

        Returns:
            Dictionary with zero token metrics

        Examples:
            >>> calculator = TokenCalculator()
            >>> metrics = calculator.build_zero_metrics("deterministic")
            >>> assert metrics['input_tokens'] == 0
            >>> assert metrics['cost'] == 0.0
        """
        return {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost': 0.0,
            'model': model_type,
            'duration': 0.0
        }


# Singleton instance for global access
_global_calculator: Optional[TokenCalculator] = None


def get_token_calculator() -> TokenCalculator:
    """
    Get or create the global token calculator instance.

    Returns:
        TokenCalculator instance

    Examples:
        >>> calculator = get_token_calculator()
        >>> tokens = calculator.extract_tokens(response)
    """
    global _global_calculator

    if _global_calculator is None:
        _global_calculator = TokenCalculator()

    return _global_calculator


if __name__ == "__main__":
    # Test token calculator when run directly
    logger.info("=" * 70)
    logger.info("Token Calculator - Test Suite")
    logger.info("=" * 70)

    calculator = TokenCalculator()

    logger.info("\nTesting token estimation:")
    text = "A" * 400  # 400 chars
    input_est, output_est = calculator.estimate_tokens(text)
    logger.info(f"  400 chars → {input_est} input tokens (expected: 100)")

    logger.info("\nTesting cost calculation:")
    cost = calculator.calculate_cost(500, 200, "claude-sonnet-4")
    logger.info(f"  500 input + 200 output → ${cost:.6f}")

    logger.info("\nTesting metrics building:")
    metrics = calculator.build_token_metrics(500, 200, cost, "claude-sonnet-4", 1.5)
    logger.info(f"  Total tokens: {metrics['total_tokens']}")
    logger.info(f"  Cost: ${metrics['cost']:.6f}")
    logger.info(f"  Duration: {metrics['duration']}s")

    logger.info("\nTesting zero metrics:")
    zero_metrics = calculator.build_zero_metrics("deterministic")
    logger.info(f"  Tokens: {zero_metrics['total_tokens']}")
    logger.info(f"  Cost: ${zero_metrics['cost']:.6f}")

    logger.info("\n" + "=" * 70)
