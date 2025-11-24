"""
prompts.template_manager
========================

Template management system for prompts using Jinja2.

This module provides:
- Template loading and rendering with Jinja2
- Caching for improved performance
- Integration with country_config for country-specific variables
- Error handling and validation
- Structured logging

Eliminates hard-coded prompts, enabling easy modification via templates.

Usage:
    >>> from prompts.template_manager import get_template_manager
    >>>
    >>> manager = get_template_manager()
    >>>
    >>> # Render system prompt for a country
    >>> system_prompt = manager.render_system_prompt(country="AU")
    >>>
    >>> # Render welcome message
    >>> welcome = manager.render_welcome_message(country="US")
    >>>
    >>> # Render off-topic decline
    >>> decline = manager.render_off_topic_decline(
    ...     real_name="John",
    ...     classification="vacation planning"
    ... )

Author: Refactoring Team
Date: 2024-11-24
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
from functools import lru_cache

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from jinja2.exceptions import TemplateError

from country_config import get_country_config, get_special_instructions
from shared.logging_config import get_logger


class TemplateLoadError(Exception):
    """Raised when template loading fails."""
    pass


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""
    pass


class TemplateManager:
    """
    Template manager for loading and rendering Jinja2 templates.

    Attributes:
        templates_dir: Path to templates directory
        env: Jinja2 Environment instance
        logger: Logger instance for structured logging
        cache: Dictionary cache for rendered templates
    """

    def __init__(
        self,
        templates_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        enable_cache: bool = True
    ):
        """
        Initialize template manager.

        Args:
            templates_dir: Path to templates directory (auto-detected if None)
            logger: Logger instance (creates default if None)
            enable_cache: Enable template caching for performance

        Raises:
            TemplateLoadError: If templates directory not found
        """
        self.logger = logger or get_logger(__name__)
        self.enable_cache = enable_cache
        self.cache: Dict[str, str] = {}

        # Determine templates directory
        if templates_dir is None:
            templates_dir = str(Path(__file__).parent / "templates")

        self.templates_dir = Path(templates_dir)

        if not self.templates_dir.exists():
            raise TemplateLoadError(
                f"Templates directory not found: {self.templates_dir}"
            )

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,  # No HTML escaping needed for prompts
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.logger.debug(f"TemplateManager initialized with templates from {self.templates_dir}")

    def _load_template(self, template_name: str) -> Template:
        """
        Load Jinja2 template by name.

        Args:
            template_name: Name of template file (e.g., "system_prompt.j2")

        Returns:
            Loaded Jinja2 Template object

        Raises:
            TemplateLoadError: If template not found or invalid
        """
        try:
            template = self.env.get_template(template_name)
            self.logger.debug(f"Loaded template: {template_name}")
            return template
        except TemplateNotFound as e:
            raise TemplateLoadError(
                f"Template '{template_name}' not found in {self.templates_dir}"
            ) from e
        except Exception as e:
            raise TemplateLoadError(
                f"Failed to load template '{template_name}': {e}"
            ) from e

    def _render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        cache_key: Optional[str] = None
    ) -> str:
        """
        Render template with given context.

        Args:
            template_name: Name of template file
            context: Dictionary of variables for template
            cache_key: Optional cache key for rendered output

        Returns:
            Rendered template string

        Raises:
            TemplateRenderError: If rendering fails
        """
        # Check cache if enabled and cache_key provided
        if self.enable_cache and cache_key and cache_key in self.cache:
            self.logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]

        try:
            template = self._load_template(template_name)
            rendered = template.render(**context)

            # Cache result if enabled and cache_key provided
            if self.enable_cache and cache_key:
                self.cache[cache_key] = rendered
                self.logger.debug(f"Cached result for {cache_key}")

            return rendered
        except TemplateError as e:
            raise TemplateRenderError(
                f"Failed to render template '{template_name}': {e}"
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                f"Unexpected error rendering '{template_name}': {e}"
            ) from e

    def _get_country_context(self, country: str) -> Dict[str, Any]:
        """
        Get country-specific context for templates.

        Args:
            country: Country code (AU, US, UK, IN)

        Returns:
            Dictionary with country-specific variables
        """
        config = get_country_config(country)
        special_instructions = get_special_instructions(country) or ""

        return {
            "country": country,
            "advisor_title": config.advisor_title,
            "regulatory_context": config.regulatory_context,
            "retirement_account_term": config.retirement_account_term,
            "balance_term": config.balance_term,
            "currency": config.currency,
            "currency_symbol": config.currency_symbol,
            "special_instructions": special_instructions
        }

    def render_system_prompt(self, country: str) -> str:
        """
        Render system prompt for response synthesis.

        Args:
            country: Country code (AU, US, UK, IN)

        Returns:
            Rendered system prompt string

        Examples:
            >>> manager = TemplateManager()
            >>> prompt = manager.render_system_prompt("AU")
            >>> assert "Australian Superannuation Advisor" in prompt
        """
        cache_key = f"system_prompt:{country}"
        context = self._get_country_context(country)

        self.logger.debug(f"Rendering system prompt for {country}")
        return self._render_template("system_prompt.j2", context, cache_key)

    def render_welcome_message(self, country: str) -> str:
        """
        Render welcome message for country portal.

        Args:
            country: Country code or name (AU/Australia, US/USA, UK/United Kingdom, IN/India)

        Returns:
            Rendered welcome message string

        Examples:
            >>> manager = TemplateManager()
            >>> message = manager.render_welcome_message("AU")
            >>> assert "superannuation portal" in message.lower()
        """
        cache_key = f"welcome:{country}"
        context = {"country": country}

        self.logger.debug(f"Rendering welcome message for {country}")
        return self._render_template("welcome_message.j2", context, cache_key)

    def render_advisor_context(self, country: str) -> str:
        """
        Render advisor-specific context for agents.

        Args:
            country: Country code (AU, US, UK, IN)

        Returns:
            Rendered advisor context string

        Examples:
            >>> manager = TemplateManager()
            >>> context = manager.render_advisor_context("US")
            >>> assert "401(k)" in context
        """
        cache_key = f"advisor_context:{country}"
        context = {"country": country}

        self.logger.debug(f"Rendering advisor context for {country}")
        return self._render_template("advisor_context.j2", context, cache_key)

    def render_off_topic_decline(
        self,
        real_name: str,
        classification: str
    ) -> str:
        """
        Render off-topic decline message.

        Args:
            real_name: Member's real name
            classification: Classification result (e.g., "vacation planning")

        Returns:
            Rendered decline message string

        Examples:
            >>> manager = TemplateManager()
            >>> message = manager.render_off_topic_decline("John", "vacation planning")
            >>> assert "retirement planning" in message.lower()
        """
        # Format classification for readability
        formatted_classification = classification.replace("_", " ")

        context = {
            "real_name": real_name,
            "classification": formatted_classification
        }

        self.logger.debug(f"Rendering off-topic decline for {real_name}")
        return self._render_template("off_topic_decline.j2", context)

    def render_validation_prompt(
        self,
        user_query: str,
        member_info: str,
        tool_info: str,
        tool_status: str,
        response_text: str,
        response_length: int
    ) -> str:
        """
        Render validation prompt for LLM judge.

        Args:
            user_query: User's original query
            member_info: Formatted member profile information
            tool_info: Formatted tool calculations and results
            tool_status: Tool execution status message
            response_text: AI generated response to validate
            response_length: Length of response in characters

        Returns:
            Rendered validation prompt string

        Examples:
            >>> manager = TemplateManager()
            >>> prompt = manager.render_validation_prompt(
            ...     user_query="How much tax?",
            ...     member_info="Age: 65",
            ...     tool_info="Tax: $5000",
            ...     tool_status="Success",
            ...     response_text="You will pay $5000 tax",
            ...     response_length=25
            ... )
            >>> assert "VALIDATION CRITERIA" in prompt
        """
        context = {
            "user_query": user_query,
            "member_info": member_info,
            "tool_info": tool_info,
            "tool_status": tool_status,
            "response_text": response_text,
            "response_length": response_length
        }

        self.logger.debug("Rendering validation prompt")
        return self._render_template("validation_prompt.j2", context)

    def render_ai_classify_query(self, user_query: str) -> str:
        """
        Render SQL query for ai_classify function.

        Args:
            user_query: User's query to classify

        Returns:
            Rendered SQL query string

        Examples:
            >>> manager = TemplateManager()
            >>> query = manager.render_ai_classify_query("How much can I withdraw?")
            >>> assert "ai_classify" in query
            >>> assert "retirement_planning" in query
        """
        # Escape single quotes for SQL
        user_query_escaped = user_query.replace("'", "''")

        context = {
            "user_query_escaped": user_query_escaped
        }

        self.logger.debug("Rendering ai_classify query")
        return self._render_template("ai_classify_query.j2", context)

    def clear_cache(self):
        """Clear all cached templates."""
        self.cache.clear()
        self.logger.info("Template cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache info (size, keys)
        """
        return {
            "enabled": self.enable_cache,
            "size": len(self.cache),
            "keys": list(self.cache.keys())
        }


# Singleton instance for global access
_global_manager: Optional[TemplateManager] = None


def get_template_manager(
    templates_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    enable_cache: bool = True
) -> TemplateManager:
    """
    Get or create the global template manager instance.

    Args:
        templates_dir: Path to templates directory (auto-detected if None)
        logger: Logger instance (creates default if None)
        enable_cache: Enable template caching

    Returns:
        TemplateManager instance

    Examples:
        >>> manager = get_template_manager()
        >>> system_prompt = manager.render_system_prompt("AU")
    """
    global _global_manager

    if _global_manager is None:
        _global_manager = TemplateManager(
            templates_dir=templates_dir,
            logger=logger,
            enable_cache=enable_cache
        )

    return _global_manager


@lru_cache(maxsize=128)
def render_system_prompt_cached(country: str) -> str:
    """
    Cached function to render system prompt.

    Uses LRU cache for additional performance optimization.

    Args:
        country: Country code (AU, US, UK, IN)

    Returns:
        Rendered system prompt string
    """
    manager = get_template_manager()
    return manager.render_system_prompt(country)


if __name__ == "__main__":
    # Test template rendering when run directly
    logger.info("=" * 70)
    logger.info("Template Manager - Jinja2 Template System")
    logger.info("=" * 70)

    manager = TemplateManager(enable_cache=True)

    logger.info("\nTesting system prompt rendering:")
    for country in ["AU", "US", "UK", "IN"]:
        try:
            prompt = manager.render_system_prompt(country)
            logger.info(f"  ✓ {country}: {len(prompt)} chars")
        except Exception as e:
            logger.info(f"  ✗ {country}: {e}")

    logger.info("\nTesting welcome message rendering:")
    for country in ["Australia", "USA", "United Kingdom", "India"]:
        try:
            message = manager.render_welcome_message(country)
            logger.info(f"  ✓ {country}: {len(message)} chars")
        except Exception as e:
            logger.info(f"  ✗ {country}: {e}")

    logger.info("\nTesting advisor context rendering:")
    for country in ["AU", "US", "UK", "IN"]:
        try:
            context = manager.render_advisor_context(country)
            logger.info(f"  ✓ {country}: {len(context)} chars")
        except Exception as e:
            logger.info(f"  ✗ {country}: {e}")

    logger.info("\nTesting off-topic decline rendering:")
    try:
        decline = manager.render_off_topic_decline("John Smith", "vacation_planning")
        logger.info(f"  ✓ Off-topic decline: {len(decline)} chars")
    except Exception as e:
        logger.info(f"  ✗ Off-topic decline: {e}")

    logger.info("\nTesting validation prompt rendering:")
    try:
        validation = manager.render_validation_prompt(
            user_query="How much tax will I pay?",
            member_info="Age: 65, Balance: $500,000",
            tool_info="Tax calculated: $75,000",
            tool_status="✓ All tools executed successfully",
            response_text="You will pay $75,000 in tax on this withdrawal.",
            response_length=52
        )
        logger.info(f"  ✓ Validation prompt: {len(validation)} chars")
    except Exception as e:
        logger.info(f"  ✗ Validation prompt: {e}")

    logger.info("\nTesting ai_classify query rendering:")
    try:
        query = manager.render_ai_classify_query("Can I withdraw from my 401k?")
        logger.info(f"  ✓ AI classify query: {len(query)} chars")
    except Exception as e:
        logger.info(f"  ✗ AI classify query: {e}")

    logger.info("\nCache info:")
    cache_info = manager.get_cache_info()
    logger.info(f"  Cache enabled: {cache_info['enabled']}")
    logger.info(f"  Cached items: {cache_info['size']}")

    logger.info("\n" + "=" * 70)
