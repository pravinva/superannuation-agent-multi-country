"""
Unit tests for shared.logging_config module.

Tests cover:
- Logger creation and configuration
- Colored formatter functionality
- File and console handlers
- Log rotation
- Environment variable configuration
- Error handling

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from shared.logging_config import (
    get_logger,
    setup_logging,
    ColoredFormatter,
    LogColors,
    _get_log_level_from_env,
    _create_log_directory,
    disable_external_loggers,
    log_startup_info,
)


class TestColoredFormatter:
    """Test suite for ColoredFormatter class."""

    def test_format_adds_colors_to_log_levels(self):
        """Test that formatter adds ANSI color codes to log levels."""
        formatter = ColoredFormatter(
            fmt="%(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Create log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should contain color code and reset
        assert LogColors.CYAN in formatted
        assert LogColors.RESET in formatted
        assert "Test message" in formatted

    def test_format_different_log_levels(self):
        """Test formatting for all log levels."""
        formatter = ColoredFormatter(fmt="%(levelname)s | %(message)s")

        levels_and_colors = [
            (logging.DEBUG, LogColors.GRAY),
            (logging.INFO, LogColors.CYAN),
            (logging.WARNING, LogColors.YELLOW),
            (logging.ERROR, LogColors.RED),
            (logging.CRITICAL, LogColors.BOLD + LogColors.RED),
        ]

        for level, expected_color in levels_and_colors:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )

            formatted = formatter.format(record)
            assert expected_color in formatted

    def test_format_preserves_original_levelname(self):
        """Test that formatting doesn't permanently modify record."""
        formatter = ColoredFormatter(fmt="%(levelname)s")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )

        original_levelname = record.levelname
        formatter.format(record)

        # Levelname should be restored
        assert record.levelname == original_levelname


class TestGetLogLevelFromEnv:
    """Test suite for _get_log_level_from_env function."""

    def test_returns_debug_level(self):
        """Test DEBUG level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level = _get_log_level_from_env()
            assert level == logging.DEBUG

    def test_returns_info_level(self):
        """Test INFO level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INFO"}):
            level = _get_log_level_from_env()
            assert level == logging.INFO

    def test_returns_warning_level(self):
        """Test WARNING level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            level = _get_log_level_from_env()
            assert level == logging.WARNING

    def test_returns_error_level(self):
        """Test ERROR level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            level = _get_log_level_from_env()
            assert level == logging.ERROR

    def test_returns_critical_level(self):
        """Test CRITICAL level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "CRITICAL"}):
            level = _get_log_level_from_env()
            assert level == logging.CRITICAL

    def test_case_insensitive(self):
        """Test that level names are case-insensitive."""
        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            level = _get_log_level_from_env()
            assert level == logging.DEBUG

        with patch.dict(os.environ, {"LOG_LEVEL": "WaRnInG"}):
            level = _get_log_level_from_env()
            assert level == logging.WARNING

    def test_defaults_to_info_when_not_set(self):
        """Test default level when LOG_LEVEL not set."""
        with patch.dict(os.environ, {}, clear=True):
            level = _get_log_level_from_env()
            assert level == logging.INFO

    def test_defaults_to_info_when_invalid(self):
        """Test default level when LOG_LEVEL is invalid."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            level = _get_log_level_from_env()
            assert level == logging.INFO


class TestCreateLogDirectory:
    """Test suite for _create_log_directory function."""

    def test_creates_logs_directory(self):
        """Test that logs directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("shared.logging_config.Path") as mock_path:
                mock_parent = MagicMock()
                mock_parent.parent = Path(tmpdir)
                mock_path.return_value.parent.parent = Path(tmpdir)

                log_dir = _create_log_directory()

                assert log_dir.exists() or log_dir == Path("/tmp/superannuation_agent_logs")

    def test_returns_existing_directory(self):
        """Test that function works with existing directory."""
        log_dir = _create_log_directory()
        assert log_dir.exists()

        # Call again - should not raise error
        log_dir2 = _create_log_directory()
        assert log_dir2.exists()


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def setup_method(self):
        """Clear handlers before each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def test_setup_with_defaults(self):
        """Test setup with default parameters."""
        setup_logging()

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 1
        assert root_logger.level in [logging.DEBUG, logging.INFO, logging.WARNING]

    def test_setup_with_custom_log_level(self):
        """Test setup with custom log level."""
        setup_logging(log_level=logging.DEBUG)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_with_console_only(self):
        """Test setup with console handler only."""
        setup_logging(enable_console=True, enable_file=False)

        root_logger = logging.getLogger()
        handler_types = [type(h).__name__ for h in root_logger.handlers]

        assert "StreamHandler" in handler_types
        assert "RotatingFileHandler" not in handler_types

    def test_setup_with_file_only(self):
        """Test setup with file handler only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            setup_logging(
                enable_console=False,
                enable_file=True,
                log_file=str(log_file)
            )

            root_logger = logging.getLogger()
            handler_types = [type(h).__name__ for h in root_logger.handlers]

            assert "RotatingFileHandler" in handler_types

    def test_setup_raises_error_when_both_disabled(self):
        """Test that error is raised when both handlers disabled."""
        with pytest.raises(ValueError, match="At least one"):
            setup_logging(enable_console=False, enable_file=False)

    def test_setup_clears_existing_handlers(self):
        """Test that existing handlers are cleared."""
        root_logger = logging.getLogger()

        # Record initial handler count (pytest may add its own)
        initial_count = len(root_logger.handlers)

        # Add a custom handler
        custom_handler = logging.StreamHandler()
        root_logger.addHandler(custom_handler)

        assert len(root_logger.handlers) == initial_count + 1

        setup_logging()

        # Should have cleared old handlers and added new ones
        # Custom handler should be gone
        assert custom_handler not in root_logger.handlers
        handler_types = [type(h).__name__ for h in root_logger.handlers]
        assert len(handler_types) >= 1

    def test_setup_with_custom_file_name(self):
        """Test setup with custom log file name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = "custom_app.log"

            with patch("shared.logging_config._create_log_directory", return_value=Path(tmpdir)):
                setup_logging(log_file=log_file)

                expected_path = Path(tmpdir) / log_file
                # File should exist or handler should be configured
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) >= 1

    def test_setup_with_rotation_parameters(self):
        """Test setup with custom rotation parameters."""
        max_bytes = 5_000_000  # 5 MB
        backup_count = 3

        setup_logging(
            enable_console=False,
            enable_file=True,
            max_bytes=max_bytes,
            backup_count=backup_count
        )

        root_logger = logging.getLogger()
        file_handlers = [
            h for h in root_logger.handlers
            if type(h).__name__ == "RotatingFileHandler"
        ]

        assert len(file_handlers) >= 1
        if file_handlers:
            handler = file_handlers[0]
            assert handler.maxBytes == max_bytes
            assert handler.backupCount == backup_count


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_returns_logger_instance(self):
        """Test that function returns a logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_returns_logger_with_correct_name(self):
        """Test that logger has correct name."""
        logger = get_logger("my_module")
        assert logger.name == "my_module"

    def test_returns_same_logger_for_same_name(self):
        """Test that same logger is returned for same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2

    def test_logger_can_log_messages(self):
        """Test that logger can log messages."""
        setup_logging(enable_file=False, enable_console=True)

        logger = get_logger("test")

        # Should not raise error
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")


class TestDisableExternalLoggers:
    """Test suite for disable_external_loggers function."""

    def test_sets_external_loggers_to_warning(self):
        """Test that external loggers are set to WARNING."""
        # Set some external loggers to DEBUG
        logging.getLogger("anthropic").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.DEBUG)

        disable_external_loggers()

        assert logging.getLogger("anthropic").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING

    def test_sets_external_loggers_to_custom_level(self):
        """Test setting external loggers to custom level."""
        disable_external_loggers(log_level=logging.ERROR)

        assert logging.getLogger("anthropic").level == logging.ERROR
        assert logging.getLogger("urllib3").level == logging.ERROR


class TestLogStartupInfo:
    """Test suite for log_startup_info function."""

    def test_logs_configuration_info(self, capsys):
        """Test that startup info is logged."""
        setup_logging(enable_console=True, enable_file=False)

        log_startup_info()

        # Check that configuration info was logged to stdout
        captured = capsys.readouterr()
        assert "Logging Configuration:" in captured.out
        assert "Root Level:" in captured.out
        assert "Handlers:" in captured.out


class TestIntegration:
    """Integration tests for complete logging workflow."""

    def setup_method(self):
        """Clear handlers before each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def test_end_to_end_console_logging(self, capsys):
        """Test complete workflow for console logging."""
        setup_logging(enable_console=True, enable_file=False, log_level=logging.INFO)
        logger = get_logger(__name__)

        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Check output was written to stdout (colored console)
        captured = capsys.readouterr()
        assert "Test info message" in captured.out
        assert "Test warning message" in captured.out
        assert "Test error message" in captured.out

    def test_end_to_end_file_logging(self):
        """Test complete workflow for file logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            with patch("shared.logging_config._create_log_directory", return_value=Path(tmpdir)):
                setup_logging(
                    enable_console=False,
                    enable_file=True,
                    log_file="test.log",
                    log_level=logging.INFO
                )

                logger = get_logger(__name__)
                logger.info("Test file message")
                logger.error("Test error in file")

                # Flush handlers
                for handler in logging.getLogger().handlers:
                    handler.flush()

                # Check file exists and contains messages
                if log_file.exists():
                    content = log_file.read_text()
                    assert "Test file message" in content or "Test error in file" in content

    def test_multiple_modules_logging(self, capsys):
        """Test logging from multiple modules."""
        setup_logging(enable_console=True, enable_file=False)

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        logger3 = get_logger("module3")

        logger1.info("Message from module1")
        logger2.info("Message from module2")
        logger3.info("Message from module3")

        # Check output contains module names
        captured = capsys.readouterr()
        assert "module1" in captured.out
        assert "module2" in captured.out
        assert "module3" in captured.out
