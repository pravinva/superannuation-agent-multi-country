"""
agents.response_builder
=======================

Response generation and building for agent responses.

This module provides:
- AI response generation with Databricks serving endpoints
- Token tracking and cost calculation
- Integration with prompts template system
- Error handling and fallback responses

Extracted from agent.py to reduce duplication and improve maintainability.

Usage:
    >>> from agents.response_builder import ResponseBuilder
    >>> from databricks.sdk import WorkspaceClient
    >>>
    >>> w = WorkspaceClient()
    >>> builder = ResponseBuilder(
    ...     workspace_client=w,
    ...     llm_endpoint="databricks-claude-sonnet-4",
    ...     model_type="claude-sonnet-4"
    ... )
    >>>
    >>> # Generate response
    >>> result = builder.generate_response(
    ...     user_query="How much can I withdraw?",
    ...     context="Member Profile...",
    ...     tool_results={"tax": {...}},
    ...     country="AU"
    ... )

Author: Refactoring Team
Date: 2024-11-24
"""

import time
import traceback
from typing import Dict, Any, Optional
from dataclasses import dataclass

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from config import (
    MAIN_LLM_ENDPOINT,
    MAIN_LLM_TEMPERATURE,
    MAIN_LLM_MAX_TOKENS,
    calculate_llm_cost
)
from country_config import get_country_config, get_balance_terminology
from prompts.template_manager import get_template_manager
from agents.context_formatter import ContextFormatter
from shared.logging_config import get_logger


@dataclass
class ResponseResult:
    """Result from response generation."""
    text: str
    input_tokens: int
    output_tokens: int
    cost: float
    duration: float
    error: Optional[str] = None


class ResponseGenerationError(Exception):
    """Raised when response generation fails."""
    pass


class ResponseBuilder:
    """
    Response builder for generating AI responses.

    Attributes:
        workspace_client: Databricks WorkspaceClient instance
        llm_endpoint: LLM serving endpoint name
        model_type: Model type for cost calculation
        logger: Logger instance for structured logging
        template_manager: Template manager for prompts
        context_formatter: Context formatter for tool results
    """

    def __init__(
        self,
        workspace_client: Optional[WorkspaceClient] = None,
        llm_endpoint: Optional[str] = None,
        model_type: str = "claude-sonnet-4",
        temperature: float = MAIN_LLM_TEMPERATURE,
        max_tokens: int = MAIN_LLM_MAX_TOKENS,
        logger=None
    ):
        """
        Initialize response builder.

        Args:
            workspace_client: Databricks WorkspaceClient (creates if None)
            llm_endpoint: LLM endpoint name (uses config default if None)
            model_type: Model type for cost calculation
            temperature: LLM temperature setting
            max_tokens: Maximum tokens for response
            logger: Optional logger instance (creates default if None)
        """
        self.workspace_client = workspace_client or WorkspaceClient()
        self.llm_endpoint = llm_endpoint or MAIN_LLM_ENDPOINT
        self.model_type = model_type
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = logger or get_logger(__name__)

        # Initialize template manager and context formatter
        self.template_manager = get_template_manager()
        self.context_formatter = ContextFormatter(logger=self.logger)

        self.logger.info(
            f"ResponseBuilder initialized: endpoint={self.llm_endpoint}, "
            f"model={self.model_type}, temp={self.temperature}"
        )

    def _determine_model_type(self, endpoint: str) -> str:
        """
        Determine model type from endpoint name.

        Args:
            endpoint: LLM endpoint name

        Returns:
            Model type string for cost calculation
        """
        endpoint_lower = endpoint.lower()

        if "opus" in endpoint_lower:
            return "claude-opus-4-1"
        elif "sonnet" in endpoint_lower:
            return "claude-sonnet-4"
        elif "haiku" in endpoint_lower:
            return "claude-haiku-4"
        else:
            return "claude-sonnet-4"  # Default

    def _build_system_prompt(
        self,
        country: str,
        context: str,
        user_query: str
    ) -> str:
        """
        Build system prompt with template integration.

        Args:
            country: Country code
            context: Member context
            user_query: User's query

        Returns:
            Complete system prompt string
        """
        # Get system prompt from template
        system_prompt_base = self.template_manager.render_system_prompt(country)

        # Build complete system prompt
        system_prompt = f"""{system_prompt_base}

MEMBER CONTEXT:
{context}

USER QUESTION:
{user_query}
"""

        return system_prompt

    def _update_context_terminology(
        self,
        context: str,
        country: str
    ) -> str:
        """
        Update context with country-specific terminology.

        Args:
            context: Original context string
            country: Country code

        Returns:
            Updated context with proper terminology
        """
        config = get_country_config(country)
        balance_term = get_balance_terminology(country)

        # Replace generic terms with country-specific
        if "superbalance" in context:
            context = context.replace("superbalance", balance_term)
            context += f"\nNote: {balance_term} refers to the member's {config.retirement_account_term} balance."

        return context

    def _extract_response_text(self, response: Any) -> str:
        """
        Extract response text from LLM response object.

        Args:
            response: LLM response object

        Returns:
            Response text string
        """
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content
        else:
            return str(response)

    def _extract_token_usage(self, response: Any) -> tuple[int, int]:
        """
        Extract token usage from LLM response.

        Args:
            response: LLM response object

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)
            self.logger.info(
                f"📊 Token usage: {input_tokens} input + {output_tokens} output = "
                f"{input_tokens + output_tokens} total"
            )
            return input_tokens, output_tokens
        else:
            # Estimate tokens if not available
            self.logger.warning("Token usage not available, using estimates")
            return 0, 0  # Will be estimated by caller

    def _estimate_tokens(
        self,
        system_prompt: str,
        full_context: str
    ) -> tuple[int, int]:
        """
        Estimate token usage when not available from API.

        Args:
            system_prompt: System prompt text
            full_context: Full context text

        Returns:
            Tuple of (estimated_input_tokens, estimated_output_tokens)
        """
        # Rough estimate: 1 token ≈ 4 characters
        input_tokens = len(system_prompt + full_context) // 4
        output_tokens = 150  # Default estimate

        self.logger.debug(f"Estimated tokens: {input_tokens} input + {output_tokens} output")
        return input_tokens, output_tokens

    def generate_response(
        self,
        user_query: str,
        context: str,
        tool_results: Dict[str, Any],
        country: str,
        validation_history: Optional[list] = None
    ) -> ResponseResult:
        """
        Generate AI response using ChatMessage objects with token tracking.

        Args:
            user_query: User's query
            context: Member context string
            tool_results: Dictionary of tool execution results
            country: Country code (AU, US, UK, IN)
            validation_history: Optional validation history (not currently used)

        Returns:
            ResponseResult with response text, tokens, cost, and duration

        Examples:
            >>> builder = ResponseBuilder()
            >>> result = builder.generate_response(
            ...     user_query="How much tax will I pay?",
            ...     context="Member Profile...",
            ...     tool_results={"tax": {"calculation": "5000"}},
            ...     country="AU"
            ... )
            >>> print(result.text)
            >>> logger.info(f"Cost: ${result.cost:.6f}")
        """
        start_time = time.time()

        try:
            # Update context with country-specific terminology
            context = self._update_context_terminology(context, country)

            # Build system prompt
            system_prompt = self._build_system_prompt(country, context, user_query)

            # Format tool results and build full context
            tool_context = self.context_formatter.format_tool_results(tool_results, country)
            full_context = f"{context}\n\n{tool_context}"

            # Build messages
            messages = [
                ChatMessage(role=ChatMessageRole.SYSTEM, content=system_prompt),
                ChatMessage(role=ChatMessageRole.USER, content=full_context)
            ]

            self.logger.debug(f"Generating response for {country} query")

            # Query LLM endpoint
            response = self.workspace_client.serving_endpoints.query(
                name=self.llm_endpoint,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            elapsed = time.time() - start_time

            # Extract token usage
            input_tokens, output_tokens = self._extract_token_usage(response)

            # Estimate if not available
            if input_tokens == 0 and output_tokens == 0:
                input_tokens, output_tokens = self._estimate_tokens(system_prompt, full_context)

            # Calculate cost
            synthesis_cost = calculate_llm_cost(input_tokens, output_tokens, self.model_type)
            self.logger.info(f"💰 Synthesis cost: ${synthesis_cost:.6f} ({self.model_type})")

            # Extract response text
            response_text = self._extract_response_text(response)

            self.logger.info(f"✅ LLM response: {len(response_text)} chars in {elapsed:.2f}s")

            return ResponseResult(
                text=response_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=synthesis_cost,
                duration=elapsed
            )

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Error generating response: {e}"
            self.logger.error(f"❌ {error_msg}")
            traceback.print_exc()

            # Return error response
            return ResponseResult(
                text="I apologize, but I encountered an error generating your response. Please try again.",
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                duration=elapsed,
                error=error_msg
            )


# Singleton instance for global access
_global_builder: Optional[ResponseBuilder] = None


def get_response_builder(
    workspace_client: Optional[WorkspaceClient] = None,
    llm_endpoint: Optional[str] = None,
    model_type: str = "claude-sonnet-4",
    logger=None
) -> ResponseBuilder:
    """
    Get or create the global response builder instance.

    Args:
        workspace_client: Databricks WorkspaceClient
        llm_endpoint: LLM endpoint name
        model_type: Model type for cost calculation
        logger: Optional logger instance

    Returns:
        ResponseBuilder instance

    Examples:
        >>> builder = get_response_builder()
        >>> result = builder.generate_response(...)
    """
    global _global_builder

    if _global_builder is None:
        _global_builder = ResponseBuilder(
            workspace_client=workspace_client,
            llm_endpoint=llm_endpoint,
            model_type=model_type,
            logger=logger
        )

    return _global_builder


if __name__ == "__main__":
    # Test response builder when run directly
    logger.info("=" * 70)
    logger.info("Response Builder - Test Suite")
    logger.info("=" * 70)

    logger.info("\nNote: Full testing requires Databricks workspace connection")
    logger.info("Creating ResponseBuilder instance...")

    try:
        builder = ResponseBuilder(model_type="claude-sonnet-4")
        logger.info(f"✓ ResponseBuilder created")
        logger.info(f"  Endpoint: {builder.llm_endpoint}")
        logger.info(f"  Model: {builder.model_type}")
        logger.info(f"  Temperature: {builder.temperature}")
        logger.info(f"  Max tokens: {builder.max_tokens}")

        logger.info("\nTesting system prompt building:")
        system_prompt = builder._build_system_prompt(
            country="AU",
            context="Member Profile:\n- Age: 55\n- Balance: $500,000",
            user_query="How much can I withdraw?"
        )
        logger.info(f"  System prompt length: {len(system_prompt)} chars")

        logger.info("\nTesting context terminology update:")
        context = "Your superbalance is $500,000"
        updated = builder._update_context_terminology(context, "AU")
        logger.info(f"  Updated: {updated[:100]}...")

        logger.info("\nTesting token estimation:")
        input_est, output_est = builder._estimate_tokens(
            "System prompt here",
            "Context here"
        )
        logger.info(f"  Estimated: {input_est} input + {output_est} output")

    except Exception as e:
        logger.info(f"✗ Error: {e}")
        traceback.print_exc()

    logger.info("\n" + "=" * 70)
