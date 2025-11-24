"""
tools.tool_executor
===================

Unified tool execution engine for superannuation calculations.

This module provides:
- Configuration-driven tool execution for AU/US/UK
- Automatic parameter resolution from member profiles
- Structured logging and timing
- Citation loading
- Error handling

Eliminates 90% code duplication across country-specific tool functions.

Usage:
    >>> from tools.tool_executor import UnifiedToolExecutor
    >>> from shared.logging_config import get_logger
    >>>
    >>> logger = get_logger(__name__)
    >>> executor = UnifiedToolExecutor(warehouse_id="abc123", logger=logger)
    >>>
    >>> result = executor.execute_tool(
    ...     country="AU",
    ...     tool_id="tax",
    ...     member_id="M001",
    ...     profile={...},
    ...     withdrawal_amount=50000
    ... )

Author: Refactoring Team
Date: 2024-11-24
"""

import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from utils.lakehouse import execute_sql_statement, get_citations
from shared.logging_config import get_logger


class ToolConfigurationError(Exception):
    """Raised when tool configuration is invalid or missing."""
    pass


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


class UnifiedToolExecutor:
    """
    Unified tool executor for AU/US/UK retirement calculations.

    Loads country-specific UC function mappings from YAML configuration
    and provides consistent execution interface.

    Attributes:
        warehouse_id: SQL warehouse ID for UC function execution
        logger: Logger instance for structured logging
        config: Loaded tool configuration dictionary
    """

    def __init__(
        self,
        warehouse_id: str,
        logger: Optional[logging.Logger] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize unified tool executor.

        Args:
            warehouse_id: SQL warehouse ID for execution
            logger: Logger instance (creates default if None)
            config_path: Path to tool_config.yaml (auto-detected if None)

        Raises:
            ToolConfigurationError: If configuration file not found or invalid
        """
        self.warehouse_id = warehouse_id
        self.logger = logger or get_logger(__name__)

        # Load configuration
        if config_path is None:
            config_path = str(Path(__file__).parent / "tool_config.yaml")

        self.config = self._load_config(config_path)
        self.logger.debug(f"UnifiedToolExecutor initialized with config from {config_path}")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load tool configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Parsed configuration dictionary

        Raises:
            ToolConfigurationError: If file not found or invalid YAML
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise ToolConfigurationError(
                f"Tool configuration file not found: {config_path}"
            )

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ToolConfigurationError(
                f"Invalid YAML in tool configuration: {e}"
            ) from e

        if not config or 'countries' not in config:
            raise ToolConfigurationError(
                "Tool configuration missing 'countries' section"
            )

        return config['countries']

    def _resolve_param_value(
        self,
        param_spec: Any,
        profile: Dict[str, Any],
        withdrawal_amount: Optional[float],
        member_id: str
    ) -> Any:
        """
        Resolve parameter value from specification.

        Handles three cases:
        1. Simple string key: lookup in profile (e.g., "age")
        2. Dict with default: lookup with fallback (e.g., {"preservation_age": 60})
        3. Literal value: use as-is (e.g., member_id, withdrawal_amount)

        Args:
            param_spec: Parameter specification from config
            profile: Member profile dictionary
            withdrawal_amount: Withdrawal amount (if applicable)
            member_id: Member ID (if applicable)

        Returns:
            Resolved parameter value

        Raises:
            ToolConfigurationError: If required parameter missing
        """
        # Handle dict with default value
        if isinstance(param_spec, dict):
            # Format: {key: default_value}
            key = list(param_spec.keys())[0]
            default = param_spec[key]

            # Special handling for profile lookups
            if key == "super_balance":
                return profile.get("super_balance", default)
            elif key == "other_assets":
                return profile.get("other_assets", default)
            elif key == "marital_status":
                return profile.get("marital_status", default)
            elif key == "preservation_age":
                return profile.get("preservation_age", default)
            elif key == "ni_qualifying_years":
                return profile.get("ni_qualifying_years", default)
            else:
                return profile.get(key, default)

        # Handle string key (direct profile lookup)
        if isinstance(param_spec, str):
            # Special values
            if param_spec == "member_id":
                return member_id
            elif param_spec == "withdrawal_amount":
                return withdrawal_amount
            elif param_spec == "balance":
                return profile.get("super_balance")
            elif param_spec == "age":
                return profile.get("age")
            else:
                # Generic profile lookup
                if param_spec not in profile:
                    raise ToolConfigurationError(
                        f"Required parameter '{param_spec}' not found in profile"
                    )
                return profile[param_spec]

        # Literal value (int, float, etc.)
        return param_spec

    def _build_query(
        self,
        tool_config: Dict[str, Any],
        member_id: str,
        profile: Dict[str, Any],
        withdrawal_amount: Optional[float]
    ) -> str:
        """
        Build SQL query from template and parameters.

        Args:
            tool_config: Tool configuration dictionary
            member_id: Member identifier
            profile: Member profile data
            withdrawal_amount: Withdrawal amount (may be None)

        Returns:
            Formatted SQL query string

        Raises:
            ToolConfigurationError: If parameter resolution fails
        """
        template = tool_config['query_template']
        params_spec = tool_config.get('params', [])

        # Resolve all parameters
        resolved_params = {}

        for param in params_spec:
            if isinstance(param, dict):
                # Dict format: {key: default}
                key = list(param.keys())[0]
                # Skip member_id as it's passed explicitly in template.format()
                if key != "member_id":
                    resolved_params[key] = self._resolve_param_value(
                        param, profile, withdrawal_amount, member_id
                    )
            elif isinstance(param, str):
                # String format: direct key
                # Skip member_id as it's passed explicitly in template.format()
                if param != "member_id":
                    resolved_params[param] = self._resolve_param_value(
                        param, profile, withdrawal_amount, member_id
                    )

        # Format query template
        try:
            query = template.format(
                member_id=member_id,
                **resolved_params
            )
        except KeyError as e:
            raise ToolConfigurationError(
                f"Missing parameter in query template: {e}"
            ) from e

        return query

    def execute_tool(
        self,
        country: str,
        tool_id: str,
        member_id: str,
        profile: Dict[str, Any],
        withdrawal_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute retirement calculation tool for specified country.

        Args:
            country: Country code (AU, US, UK)
            tool_id: Tool identifier (tax, benefit, projection)
            member_id: Member identifier
            profile: Member profile dictionary
            withdrawal_amount: Withdrawal amount (optional, depends on tool)

        Returns:
            Tool execution result dictionary containing:
                - tool_name: Display name
                - tool_id: Tool identifier
                - uc_function: UC function name
                - authority: Regulatory authority
                - calculation: Result value
                - citations: List of citation dictionaries
                - duration: Execution time in seconds

        Raises:
            ToolConfigurationError: If country/tool not configured
            ToolExecutionError: If tool execution fails

        Examples:
            >>> result = executor.execute_tool(
            ...     country="AU",
            ...     tool_id="tax",
            ...     member_id="M001",
            ...     profile={"age": 65, "super_balance": 500000},
            ...     withdrawal_amount=50000
            ... )
            >>> print(result['calculation'])
            '7500'
        """
        start_time = time.time()

        # Validate country
        country_upper = country.upper()
        if country_upper not in self.config:
            raise ToolConfigurationError(
                f"Country '{country}' not supported. Available: {list(self.config.keys())}"
            )

        country_config = self.config[country_upper]

        # Validate tool
        if 'tools' not in country_config:
            raise ToolConfigurationError(
                f"Country '{country}' configuration missing 'tools' section"
            )

        tools = country_config['tools']
        if tool_id not in tools:
            available_tools = list(tools.keys())
            raise ToolConfigurationError(
                f"Tool '{tool_id}' not found for {country}. Available: {available_tools}"
            )

        tool_config = tools[tool_id]

        # Build query
        self.logger.debug(
            f"Building query for {country}:{tool_id} (member: {member_id})"
        )

        try:
            query = self._build_query(
                tool_config, member_id, profile, withdrawal_amount
            )
        except ToolConfigurationError as e:
            self.logger.error(f"Query building failed: {e}")
            raise

        # Execute query
        self.logger.debug(f"Executing UC function: {tool_config['uc_function']}")

        try:
            result = execute_sql_statement(query, self.warehouse_id)
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"UC function execution failed after {duration:.2f}s: {e}"
            )
            raise ToolExecutionError(
                f"Failed to execute {country}:{tool_id}: {e}"
            ) from e

        # Validate result
        if not result or not result.result or not result.result.data_array:
            duration = time.time() - start_time
            self.logger.error(
                f"No result returned from {tool_config['uc_function']} "
                f"after {duration:.2f}s"
            )
            raise ToolExecutionError(
                f"No result from {country}_{tool_id}"
            )

        calculation = result.result.data_array[0][0]
        duration = time.time() - start_time

        # Load citations
        citations = get_citations(tool_config['citations'], self.warehouse_id)

        # Build result
        result_dict = {
            "tool_name": tool_config['name'],
            "tool_id": tool_id,
            "uc_function": tool_config['uc_function'],
            "authority": tool_config['authority'],
            "calculation": str(calculation),
            "citations": citations,
            "duration": round(duration, 2)
        }

        self.logger.info(
            f"✓ {country}:{tool_id} completed in {duration:.2f}s "
            f"(result: {calculation})"
        )

        return result_dict


def create_executor(
    warehouse_id: str,
    logger: Optional[logging.Logger] = None
) -> UnifiedToolExecutor:
    """
    Factory function to create UnifiedToolExecutor instance.

    Args:
        warehouse_id: SQL warehouse ID
        logger: Optional logger instance

    Returns:
        Configured UnifiedToolExecutor instance

    Examples:
        >>> executor = create_executor("abc123")
        >>> result = executor.execute_tool("AU", "tax", "M001", profile, 50000)
    """
    return UnifiedToolExecutor(warehouse_id=warehouse_id, logger=logger)
