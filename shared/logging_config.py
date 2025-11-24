"""
shared.logging_config
======================

Centralized logging configuration for the superannuation agent application.

This module provides:
- Colored console output for different log levels
- File logging with automatic rotation
- Structured log formatting with timestamps
- Environment-based log level configuration
- Thread-safe logger instances

Usage:
    >>> from shared.logging_config import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")
    >>> logger.error("Error occurred", exc_info=True)

Author: Refactoring Team
Date: 2024-11-24
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import os


# ANSI color codes for terminal output
class LogColors:
    """ANSI color codes for colored console output."""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log output based on log level.

    Colors:
        DEBUG: Gray
        INFO: Cyan
        WARNING: Yellow
        ERROR: Red
        CRITICAL: Bold Red
    """

    COLORS: Dict[int, str] = {
        logging.DEBUG: LogColors.GRAY,
        logging.INFO: LogColors.CYAN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.BOLD + LogColors.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with appropriate colors.

        Args:
            record: LogRecord to format

        Returns:
            Formatted and colored log message
        """
        # Add color to level name
        levelname = record.levelname
        if record.levelno in self.COLORS:
            levelname_color = (
                f"{self.COLORS[record.levelno]}{levelname}{LogColors.RESET}"
            )
            record.levelname = levelname_color

        # Format the message
        formatted = super().format(record)

        # Reset levelname for potential reuse
        record.levelname = levelname

        return formatted


def _get_log_level_from_env() -> int:
    """
    Get log level from environment variable.

    Checks LOG_LEVEL environment variable and returns corresponding
    logging level. Defaults to INFO if not set or invalid.

    Returns:
        Integer log level (e.g., logging.INFO, logging.DEBUG)

    Examples:
        >>> os.environ['LOG_LEVEL'] = 'DEBUG'
        >>> _get_log_level_from_env()
        10  # logging.DEBUG
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()

    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return level_mapping.get(level_name, logging.INFO)


def _create_log_directory() -> Path:
    """
    Create logs directory if it doesn't exist.

    Returns:
        Path to logs directory

    Raises:
        OSError: If directory creation fails
    """
    log_dir = Path(__file__).parent.parent / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    except OSError as e:
        # Fallback to /tmp if can't create in project directory
        fallback_dir = Path("/tmp/superannuation_agent_logs")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir


def setup_logging(
    log_level: Optional[int] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10_485_760,  # 10 MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    Configure root logger with console and file handlers.

    Args:
        log_level: Logging level (default: from LOG_LEVEL env or INFO)
        log_file: Log file name (default: app_YYYYMMDD.log)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        enable_console: Whether to log to console (default: True)
        enable_file: Whether to log to file (default: True)

    Raises:
        ValueError: If both console and file logging are disabled
        OSError: If log directory cannot be created

    Examples:
        >>> setup_logging(log_level=logging.DEBUG)
        >>> setup_logging(log_file="custom.log", max_bytes=5_000_000)
    """
    if not enable_console and not enable_file:
        raise ValueError("At least one of console or file logging must be enabled")

    # Get log level
    if log_level is None:
        log_level = _get_log_level_from_env()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        console_format = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if enable_file:
        log_dir = _create_log_directory()

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = f"app_{timestamp}.log"

        log_path = log_dir / log_file

        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)

        file_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    This is the primary function to use throughout the application.
    Call setup_logging() once at application startup before using this.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.error("Error occurred", exc_info=True)
        >>> logger.debug("Debug information", extra={"user_id": 123})
    """
    return logging.getLogger(name)


def disable_external_loggers(log_level: int = logging.WARNING) -> None:
    """
    Reduce verbosity of external library loggers.

    Many external libraries (e.g., boto3, urllib3, anthropic) can be
    very verbose. This function sets them to WARNING level or higher.

    Args:
        log_level: Minimum log level for external libraries (default: WARNING)

    Examples:
        >>> disable_external_loggers()
        >>> disable_external_loggers(log_level=logging.ERROR)
    """
    external_loggers = [
        "anthropic",
        "httpx",
        "httpcore",
        "urllib3",
        "boto3",
        "botocore",
        "s3transfer",
        "werkzeug",
        "streamlit",
    ]

    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(log_level)


# Module-level logger for logging configuration issues
_config_logger = logging.getLogger(__name__)


def log_startup_info() -> None:
    """
    Log application startup information.

    Logs the current log level, log file location, and configuration.
    Call this after setup_logging() to confirm configuration.

    Examples:
        >>> setup_logging()
        >>> log_startup_info()
    """
    root_logger = logging.getLogger()
    handlers_info = []

    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handlers_info.append(f"Console (level={logging.getLevelName(handler.level)})")
        elif isinstance(handler, RotatingFileHandler):
            handlers_info.append(
                f"File: {handler.baseFilename} "
                f"(level={logging.getLevelName(handler.level)}, "
                f"maxBytes={handler.maxBytes}, "
                f"backupCount={handler.backupCount})"
            )

    _config_logger.info("=" * 80)
    _config_logger.info("Logging Configuration:")
    _config_logger.info(f"  Root Level: {logging.getLevelName(root_logger.level)}")
    _config_logger.info(f"  Handlers: {len(root_logger.handlers)}")
    for handler_info in handlers_info:
        _config_logger.info(f"    - {handler_info}")
    _config_logger.info("=" * 80)
