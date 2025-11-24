"""
config.config_loader
====================

Configuration management system for the superannuation agent application.

This module provides:
- YAML configuration loading with caching
- Environment variable overrides (AGENT_{SECTION}_{KEY})
- Type-safe configuration access using dataclasses
- Configuration validation on load
- Support for multiple configuration files

Usage:
    >>> from config.config_loader import load_config, get_config
    >>>
    >>> # Load configuration (do once at startup)
    >>> config = load_config("config/config.yaml")
    >>>
    >>> # Access configuration anywhere
    >>> config = get_config()
    >>> endpoint = config.llm.endpoint
    >>> temperature = config.llm.temperature

Author: Refactoring Team
Date: 2024-11-24
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class LLMConfig:
    """LLM configuration settings."""

    endpoint: str
    temperature: float
    max_tokens: int
    timeout: int = 120
    max_retries: int = 3


@dataclass
class ValidationLLMConfig:
    """Validation LLM configuration settings."""

    endpoint: str
    temperature: float
    max_tokens: int
    confidence_threshold: float = 0.70


@dataclass
class CountryConfig:
    """Country-specific configuration."""

    code: str
    name: str
    enabled: bool = True


@dataclass
class AgentConfig:
    """Agent behavior configuration."""

    max_iterations: int = 10
    enable_reflection: bool = True
    enable_validation: bool = True
    verbose_logging: bool = False


@dataclass
class UIConfig:
    """UI configuration settings."""

    theme: str = "light"
    show_debug_info: bool = False
    page_title: str = "Superannuation Agent"
    page_icon: str = "💰"


@dataclass
class PerformanceConfig:
    """Performance and optimization settings."""

    cache_enabled: bool = True
    cache_ttl: int = 3600
    batch_size: int = 10
    parallel_execution: bool = True


@dataclass
class AppConfig:
    """
    Main application configuration.

    Attributes:
        llm: Main LLM configuration
        validation_llm: Validation LLM configuration
        countries: List of country configurations
        agent: Agent behavior settings
        ui: UI configuration
        performance: Performance settings
    """

    llm: LLMConfig
    validation_llm: ValidationLLMConfig
    countries: List[CountryConfig]
    agent: AgentConfig
    ui: UIConfig
    performance: PerformanceConfig


# Global configuration instance
_config: Optional[AppConfig] = None


def _apply_env_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.

    Environment variables should be prefixed with AGENT_ and use underscores
    to separate sections and keys. For example:
        - AGENT_LLM_TEMPERATURE=0.5
        - AGENT_AGENT_MAX_ITERATIONS=15

    Args:
        config_dict: Original configuration dictionary

    Returns:
        Configuration dictionary with environment overrides applied

    Examples:
        >>> os.environ['AGENT_LLM_TEMPERATURE'] = '0.5'
        >>> config = {'llm': {'temperature': 0.2}}
        >>> result = _apply_env_overrides(config)
        >>> result['llm']['temperature']
        0.5
    """
    prefix = "AGENT_"

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        # Parse environment variable name
        parts = env_key[len(prefix):].lower().split("_")

        if len(parts) < 2:
            continue

        section = parts[0]
        key = "_".join(parts[1:])

        if section not in config_dict:
            continue

        # Convert string value to appropriate type
        current_value = config_dict[section].get(key)

        if current_value is not None:
            try:
                if isinstance(current_value, bool):
                    # Handle boolean values
                    config_dict[section][key] = env_value.lower() in ("true", "1", "yes")
                elif isinstance(current_value, int):
                    config_dict[section][key] = int(env_value)
                elif isinstance(current_value, float):
                    config_dict[section][key] = float(env_value)
                else:
                    config_dict[section][key] = env_value
            except (ValueError, TypeError):
                # Keep original value if conversion fails
                pass

    return config_dict


def _validate_config(config_dict: Dict[str, Any]) -> None:
    """
    Validate configuration dictionary.

    Args:
        config_dict: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate required sections
    required_sections = ["llm", "validation_llm", "agent"]
    for section in required_sections:
        if section not in config_dict:
            raise ValueError(f"Missing required configuration section: {section}")

    # Validate LLM configuration
    llm_config = config_dict.get("llm", {})
    if not llm_config.get("endpoint"):
        raise ValueError("LLM endpoint cannot be empty")

    if not 0 <= llm_config.get("temperature", 0.2) <= 1.0:
        raise ValueError("LLM temperature must be between 0 and 1")

    if llm_config.get("max_tokens", 4000) <= 0:
        raise ValueError("LLM max_tokens must be positive")

    # Validate validation LLM
    val_llm = config_dict.get("validation_llm", {})
    if not val_llm.get("endpoint"):
        raise ValueError("Validation LLM endpoint cannot be empty")

    threshold = val_llm.get("confidence_threshold", 0.7)
    if not 0 <= threshold <= 1.0:
        raise ValueError("Confidence threshold must be between 0 and 1")

    # Validate agent configuration
    agent_config = config_dict.get("agent", {})
    if agent_config.get("max_iterations", 10) <= 0:
        raise ValueError("Agent max_iterations must be positive")


@lru_cache(maxsize=1)
def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from YAML file with environment overrides.

    This function is cached - subsequent calls with the same path
    return the cached instance. Call _config_cache_clear() to invalidate.

    Args:
        config_path: Path to YAML config file (default: config/config.yaml)

    Returns:
        Loaded and validated AppConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
        yaml.YAMLError: If YAML is malformed

    Examples:
        >>> config = load_config("config/config.yaml")
        >>> config.llm.endpoint
        'databricks-claude-sonnet-4'
    """
    global _config

    if config_path is None:
        # Default to config/config.yaml in project root
        config_path = str(Path(__file__).parent / "config.yaml")

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML
    try:
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}") from e

    if config_dict is None:
        raise ValueError("Configuration file is empty")

    # Apply environment variable overrides
    config_dict = _apply_env_overrides(config_dict)

    # Validate configuration
    _validate_config(config_dict)

    # Build typed configuration
    _config = AppConfig(
        llm=LLMConfig(**config_dict["llm"]),
        validation_llm=ValidationLLMConfig(**config_dict["validation_llm"]),
        countries=[
            CountryConfig(**country) for country in config_dict.get("countries", [])
        ],
        agent=AgentConfig(**config_dict.get("agent", {})),
        ui=UIConfig(**config_dict.get("ui", {})),
        performance=PerformanceConfig(**config_dict.get("performance", {})),
    )

    return _config


def get_config() -> AppConfig:
    """
    Get the current application configuration.

    Call load_config() first to initialize configuration.

    Returns:
        Current AppConfig instance

    Raises:
        RuntimeError: If configuration not loaded

    Examples:
        >>> load_config()  # Call once at startup
        >>> config = get_config()  # Use anywhere
        >>> config.llm.temperature
        0.2
    """
    global _config

    if _config is None:
        raise RuntimeError(
            "Configuration not loaded. Call load_config() first."
        )

    return _config


def reload_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Reload configuration from file.

    Clears cache and reloads configuration. Useful for testing
    or dynamic configuration updates.

    Args:
        config_path: Path to YAML config file (default: config/config.yaml)

    Returns:
        Newly loaded AppConfig instance

    Examples:
        >>> config = reload_config()
        >>> # Configuration is reloaded from disk
    """
    global _config

    # Clear cache
    load_config.cache_clear()
    _config = None

    # Reload
    return load_config(config_path)


def get_enabled_countries() -> List[CountryConfig]:
    """
    Get list of enabled countries from configuration.

    Returns:
        List of enabled CountryConfig instances

    Examples:
        >>> enabled = get_enabled_countries()
        >>> [c.code for c in enabled]
        ['AU', 'US', 'UK', 'NZ']
    """
    config = get_config()
    return [country for country in config.countries if country.enabled]


def is_country_enabled(country_code: str) -> bool:
    """
    Check if a country is enabled in configuration.

    Args:
        country_code: Country code (e.g., 'AU', 'US')

    Returns:
        True if country is enabled, False otherwise

    Examples:
        >>> is_country_enabled('AU')
        True
        >>> is_country_enabled('FR')
        False
    """
    enabled_countries = get_enabled_countries()
    return any(c.code == country_code for c in enabled_countries)


def get_config_dict() -> Dict[str, Any]:
    """
    Get configuration as dictionary.

    Useful for debugging or serialization.

    Returns:
        Configuration as dictionary

    Examples:
        >>> config_dict = get_config_dict()
        >>> config_dict['llm']['endpoint']
        'databricks-claude-sonnet-4'
    """
    config = get_config()

    return {
        "llm": {
            "endpoint": config.llm.endpoint,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
            "timeout": config.llm.timeout,
            "max_retries": config.llm.max_retries,
        },
        "validation_llm": {
            "endpoint": config.validation_llm.endpoint,
            "temperature": config.validation_llm.temperature,
            "max_tokens": config.validation_llm.max_tokens,
            "confidence_threshold": config.validation_llm.confidence_threshold,
        },
        "countries": [
            {"code": c.code, "name": c.name, "enabled": c.enabled}
            for c in config.countries
        ],
        "agent": {
            "max_iterations": config.agent.max_iterations,
            "enable_reflection": config.agent.enable_reflection,
            "enable_validation": config.agent.enable_validation,
            "verbose_logging": config.agent.verbose_logging,
        },
        "ui": {
            "theme": config.ui.theme,
            "show_debug_info": config.ui.show_debug_info,
            "page_title": config.ui.page_title,
            "page_icon": config.ui.page_icon,
        },
        "performance": {
            "cache_enabled": config.performance.cache_enabled,
            "cache_ttl": config.performance.cache_ttl,
            "batch_size": config.performance.batch_size,
            "parallel_execution": config.performance.parallel_execution,
        },
    }
