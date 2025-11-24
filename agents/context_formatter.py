"""
agents.context_formatter
=========================

Context formatting and building for agent responses.

This module provides:
- Member profile context building with anonymization
- Tool results formatting
- Member name anonymization and restoration
- Country-specific context additions

Extracted from agent.py to reduce duplication and improve maintainability.

Usage:
    >>> from agents.context_formatter import ContextFormatter
    >>>
    >>> formatter = ContextFormatter()
    >>>
    >>> # Build base context from member profile
    >>> context_data = formatter.build_base_context(member_profile, anonymize=True)
    >>>
    >>> # Format tool results
    >>> formatted = formatter.format_tool_results(tool_results, country="AU")

Author: Refactoring Team
Date: 2024-11-24
"""

import hashlib
import re
from typing import Dict, Any, Optional, List, Tuple

from utils.formatting import get_currency, get_currency_symbol, safe_float
from country_config import get_authority
from shared.logging_config import get_logger


class ContextFormatter:
    """
    Context formatter for building and formatting agent contexts.

    Attributes:
        logger: Logger instance for structured logging
    """

    def __init__(self, logger=None):
        """
        Initialize context formatter.

        Args:
            logger: Optional logger instance (creates default if None)
        """
        self.logger = logger or get_logger(__name__)

    def anonymize_member_name(self, name: str) -> str:
        """
        Anonymize member name for privacy using MD5 hash.

        Args:
            name: Member's real name

        Returns:
            Anonymized name (e.g., "Member_a3f5b2")

        Examples:
            >>> formatter = ContextFormatter()
            >>> anon = formatter.anonymize_member_name("John Smith")
            >>> assert anon.startswith("Member_")
            >>> assert len(anon) == 13  # Member_ + 6 hex chars
        """
        if not name or name == "Unknown Member":
            return "Member_unknown"

        name_hash = hashlib.md5(name.encode()).hexdigest()[:6]
        anonymized = f"Member_{name_hash}"

        self.logger.debug(f"Anonymized '{name}' → '{anonymized}'")
        return anonymized

    def restore_member_name(
        self,
        text: str,
        anonymized_name: Optional[str],
        real_name: str
    ) -> str:
        """
        Restore real name in response text.

        Args:
            text: Response text with anonymized name
            anonymized_name: The anonymized name to replace
            real_name: The real name to restore

        Returns:
            Text with real name restored

        Examples:
            >>> formatter = ContextFormatter()
            >>> text = "Hi Member_a3f5b2, your balance is $500,000"
            >>> restored = formatter.restore_member_name(
            ...     text, "Member_a3f5b2", "John Smith"
            ... )
            >>> assert "John Smith" in restored
        """
        if not anonymized_name or not real_name:
            return text

        if anonymized_name in text:
            text = text.replace(anonymized_name, real_name)
            self.logger.debug(f"Restored name: {anonymized_name} → {real_name}")

        return text

    def add_personalized_greeting(
        self,
        text: str,
        member_name: str
    ) -> str:
        """
        Add personalized greeting to response if not already present.

        Args:
            text: Response text
            member_name: Member's name for greeting

        Returns:
            Text with greeting prepended if needed

        Examples:
            >>> formatter = ContextFormatter()
            >>> text = "Your balance is $500,000"
            >>> greeted = formatter.add_personalized_greeting(text, "John")
            >>> assert greeted.startswith("Hi John,")
        """
        if not member_name or member_name == "Unknown Member":
            return text

        # Check if greeting already exists
        if text.strip().startswith(("Hi", "Hello", "Dear")):
            return text

        greeting = f"Hi {member_name},\n\n{text}"
        self.logger.debug(f"Added personalized greeting for {member_name}")

        return greeting

    def get_country_from_context(self, context: str) -> str:
        """
        Extract country code from context string.

        Args:
            context: Context string containing country information

        Returns:
            Country code (e.g., "AU", "US", "UK", "IN"), defaults to "AU"

        Examples:
            >>> formatter = ContextFormatter()
            >>> context = "Member Profile:\\n- Country: US\\n- Age: 55"
            >>> country = formatter.get_country_from_context(context)
            >>> assert country == "US"
        """
        country_match = re.search(r"Country: ([A-Z]{2})", context)

        if country_match:
            country = country_match.group(1)
            self.logger.debug(f"Extracted country: {country}")
            return country

        self.logger.debug("No country found in context, defaulting to AU")
        return "AU"

    def build_base_context(
        self,
        member_profile: Dict[str, Any],
        anonymize: bool = True
    ) -> Dict[str, Any]:
        """
        Build base context from member profile.

        Args:
            member_profile: Dictionary containing member information
            anonymize: Whether to anonymize member name (default: True)

        Returns:
            Dictionary with keys:
                - text: Formatted context string
                - real_name: Member's real name
                - anonymized_name: Anonymized name (if anonymize=True)

        Examples:
            >>> formatter = ContextFormatter()
            >>> profile = {
            ...     "name": "John Smith",
            ...     "age": 55,
            ...     "country": "AU",
            ...     "employment_status": "Employed",
            ...     "super_balance": 500000,
            ...     "preservation_age": 60
            ... }
            >>> context_data = formatter.build_base_context(profile)
            >>> assert "Member_" in context_data["text"]
            >>> assert context_data["real_name"] == "John Smith"
        """
        real_name = member_profile.get("name", "Unknown Member")

        if anonymize:
            display_name = self.anonymize_member_name(real_name)
            self.logger.info(f"🔒 Privacy Mode: Anonymized '{real_name}' → '{display_name}'")
        else:
            display_name = real_name

        country = member_profile.get("country", "AU")
        age = member_profile.get("age", "Unknown")
        balance_raw = member_profile.get("super_balance", 0)
        balance = safe_float(balance_raw)
        employment = member_profile.get("employment_status", "Unknown")

        currency = get_currency(country)

        context = f"""Member Profile:
- Name: {display_name}
- Age: {age}
- Country: {country}
- Employment: {employment}
- Retirement Corpus: {balance:,.2f} {currency}
"""

        # Add country-specific fields
        if country == "AU":
            pres_age = member_profile.get("preservation_age", "Unknown")
            context += f"- Preservation Age: {pres_age}\n"

        context_data = {
            "text": context,
            "real_name": real_name,
            "anonymized_name": display_name if anonymize else None
        }

        self.logger.debug(f"Built base context for {country} member")
        return context_data

    def format_tool_results(
        self,
        tool_results: Dict[str, Any],
        country: str = "AU"
    ) -> str:
        """
        Format tool results for context display.

        Handles special formatting for India (EPF/NPS split display).

        Args:
            tool_results: Dictionary of tool results
            country: Country code for authority lookup

        Returns:
            Formatted tool results string

        Examples:
            >>> formatter = ContextFormatter()
            >>> results = {
            ...     "tax": {
            ...         "tool_name": "ATO Tax Calculator",
            ...         "authority": "ATO",
            ...         "calculation": "12500"
            ...     }
            ... }
            >>> formatted = formatter.format_tool_results(results, "AU")
            >>> assert "ATO Tax Calculator" in formatted
            >>> assert "12500" in formatted
        """
        if not tool_results:
            return ""

        result_lines = ["=" * 70]
        result_lines.append("UC FUNCTION RESULTS:")
        result_lines.append("=" * 70)

        for tool_name, results in tool_results.items():
            result_lines.append(f"\n{tool_name.upper()} RESULTS:")
            result_lines.append("-" * 40)

            if isinstance(results, dict):
                if "error" in results:
                    result_lines.append(f"❌ Error: {results['error']}")
                    self.logger.warning(f"Tool {tool_name} returned error: {results['error']}")
                    continue

                tool_name_display = results.get("tool_name", f"Unknown {tool_name} Tool")
                authority = results.get("authority", "")
                calculation = results.get("calculation", "")

                if not authority:
                    authority = get_authority(country, tool_name)

                result_lines.append(f"Tool: {tool_name_display}")
                result_lines.append(f"Authority: {authority}")

                # Special handling for India balance split
                if "balance_split" in results:
                    split = results["balance_split"]
                    result_lines.append(f"Total Balance: {split['total_balance']:,.2f} INR")
                    result_lines.append(f"EPF Balance: {split['epf_balance']:,.2f} INR (75%)")
                    result_lines.append(f"NPS Balance: {split['nps_balance']:,.2f} INR (25%)")
                    self.logger.debug("Added India EPF/NPS balance split to formatting")

                if "calculation_note" in results:
                    result_lines.append(f"Note: {results['calculation_note']}")

                result_lines.append(f"Calculation: {str(calculation)[:300]}")
            else:
                result_lines.append(f"Result: {str(results)[:200]}")

        result_lines.append("=" * 70)

        formatted = "\n".join(result_lines)
        self.logger.debug(f"Formatted {len(tool_results)} tool results")

        return formatted

    def build_full_context(
        self,
        base_context: str,
        tool_results: Dict[str, Any],
        country: str = "AU"
    ) -> str:
        """
        Build full context combining base context and tool results.

        Args:
            base_context: Base member profile context
            tool_results: Tool execution results
            country: Country code

        Returns:
            Combined context string

        Examples:
            >>> formatter = ContextFormatter()
            >>> base = "Member Profile:\\n- Name: John\\n- Age: 55"
            >>> tools = {"tax": {"tool_name": "Tax Calc", "calculation": "5000"}}
            >>> full = formatter.build_full_context(base, tools, "AU")
            >>> assert "Member Profile" in full
            >>> assert "Tax Calc" in full
        """
        tool_context = self.format_tool_results(tool_results, country)

        if tool_context:
            full_context = f"{base_context}\n\n{tool_context}"
        else:
            full_context = base_context

        self.logger.debug("Built full context with tool results")
        return full_context


# Singleton instance for global access
_global_formatter: Optional[ContextFormatter] = None


def get_context_formatter(logger=None) -> ContextFormatter:
    """
    Get or create the global context formatter instance.

    Args:
        logger: Optional logger instance

    Returns:
        ContextFormatter instance

    Examples:
        >>> formatter = get_context_formatter()
        >>> context = formatter.build_base_context(member_profile)
    """
    global _global_formatter

    if _global_formatter is None:
        _global_formatter = ContextFormatter(logger=logger)

    return _global_formatter


if __name__ == "__main__":
    # Test context formatting when run directly
    logger.info("=" * 70)
    logger.info("Context Formatter - Test Suite")
    logger.info("=" * 70)

    formatter = ContextFormatter()

    logger.info("\nTesting name anonymization:")
    anon1 = formatter.anonymize_member_name("John Smith")
    anon2 = formatter.anonymize_member_name("Jane Doe")
    logger.info(f"  John Smith → {anon1}")
    logger.info(f"  Jane Doe → {anon2}")

    logger.info("\nTesting name restoration:")
    text = f"Hi {anon1}, your balance is $500,000"
    restored = formatter.restore_member_name(text, anon1, "John Smith")
    logger.info(f"  Before: {text}")
    logger.info(f"  After: {restored}")

    logger.info("\nTesting personalized greeting:")
    text = "Your balance is $500,000"
    greeted = formatter.add_personalized_greeting(text, "John")
    logger.info(f"  Before: {text}")
    logger.info(f"  After: {greeted}")

    logger.info("\nTesting base context building:")
    profile = {
        "name": "John Smith",
        "age": 55,
        "country": "AU",
        "employment_status": "Employed",
        "super_balance": 500000,
        "preservation_age": 60
    }
    context_data = formatter.build_base_context(profile)
    logger.info(f"  Context length: {len(context_data['text'])} chars")
    logger.info(f"  Real name: {context_data['real_name']}")
    logger.info(f"  Anonymized name: {context_data['anonymized_name']}")

    logger.info("\nTesting tool results formatting:")
    tool_results = {
        "tax": {
            "tool_name": "ATO Tax Calculator",
            "authority": "Australian Taxation Office",
            "calculation": "12500"
        },
        "benefit": {
            "tool_name": "Age Pension Calculator",
            "authority": "Centrelink",
            "calculation": "25000"
        }
    }
    formatted = formatter.format_tool_results(tool_results, "AU")
    logger.info(f"  Formatted length: {len(formatted)} chars")

    logger.info("\n" + "=" * 70)
