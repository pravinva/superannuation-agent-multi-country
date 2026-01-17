"""
shared.progress_tracker
========================

Progress tracking context manager for agent operations.

This module provides:
- Context manager for tracking operation phases
- Automatic timing of operations
- Structured logging of progress
- Streamlit-compatible progress display
- Phase hierarchy support

Replaces duplicate printf() functions found across the codebase.

Usage:
    >>> from shared.progress_tracker import track_phase
    >>> from shared.logging_config import setup_logging, get_logger
    >>>
    >>> setup_logging()
    >>> logger = get_logger(__name__)
    >>>
    >>> with track_phase("Tool Execution", logger):
    ...     # Your code here
    ...     perform_operation()

Author: Refactoring Team
Date: 2024-11-24
"""

import time
from contextlib import contextmanager
from typing import Optional, Generator, Any
import logging
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PhaseMetrics:
    """
    Metrics collected during a phase execution.

    Attributes:
        phase_name: Name of the phase
        start_time: When phase started (seconds since epoch)
        end_time: When phase ended (seconds since epoch), None if still running
        duration: Duration in seconds, None if not completed
        success: Whether phase completed successfully
        error_message: Error message if phase failed, None otherwise
    """

    phase_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

    def complete(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """
        Mark phase as completed and calculate duration.

        Args:
            success: Whether phase completed successfully
            error_message: Error message if failed
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> dict:
        """
        Convert metrics to dictionary.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "phase_name": self.phase_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class ProgressTracker:
    """
    Tracks progress across multiple phases.

    Attributes:
        name: Name of the overall operation
        phases: List of completed phase metrics
        current_phase: Currently executing phase, None if none active
    """

    name: str
    phases: list[PhaseMetrics] = field(default_factory=list)
    current_phase: Optional[PhaseMetrics] = None

    def start_phase(self, phase_name: str) -> PhaseMetrics:
        """
        Start tracking a new phase.

        Args:
            phase_name: Name of the phase

        Returns:
            PhaseMetrics object for the new phase

        Raises:
            RuntimeError: If a phase is already active
        """
        if self.current_phase is not None:
            raise RuntimeError(
                f"Cannot start phase '{phase_name}': "
                f"phase '{self.current_phase.phase_name}' is still active"
            )

        self.current_phase = PhaseMetrics(
            phase_name=phase_name,
            start_time=time.time(),
        )
        return self.current_phase

    def end_phase(
        self, success: bool = True, error_message: Optional[str] = None
    ) -> PhaseMetrics:
        """
        End the current phase.

        Args:
            success: Whether phase completed successfully
            error_message: Error message if failed

        Returns:
            Completed PhaseMetrics object

        Raises:
            RuntimeError: If no phase is active
        """
        if self.current_phase is None:
            raise RuntimeError("Cannot end phase: no phase is active")

        self.current_phase.complete(success=success, error_message=error_message)
        self.phases.append(self.current_phase)

        completed_phase = self.current_phase
        self.current_phase = None

        return completed_phase

    def get_total_duration(self) -> float:
        """
        Get total duration of all completed phases.

        Returns:
            Total duration in seconds
        """
        return sum(
            phase.duration for phase in self.phases if phase.duration is not None
        )

    def get_summary(self) -> dict:
        """
        Get summary of all phases.

        Returns:
            Dictionary with operation summary
        """
        return {
            "name": self.name,
            "total_phases": len(self.phases),
            "successful_phases": sum(1 for p in self.phases if p.success),
            "failed_phases": sum(1 for p in self.phases if not p.success),
            "total_duration": self.get_total_duration(),
            "phases": [phase.to_dict() for phase in self.phases],
        }


@contextmanager
def track_phase(
    phase_name: str,
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.INFO,
    streamlit_container: Optional[Any] = None,
) -> Generator[PhaseMetrics, None, None]:
    """
    Context manager for tracking a phase of execution.

    Automatically logs start and completion, measures duration,
    and optionally updates Streamlit UI.

    Args:
        phase_name: Name of the phase to track
        logger: Logger instance for output (if None, creates default)
        log_level: Log level for progress messages (default: INFO)
        streamlit_container: Optional Streamlit container for UI updates

    Yields:
        PhaseMetrics object being tracked

    Raises:
        Exception: Re-raises any exception from the wrapped code block

    Examples:
        >>> logger = get_logger(__name__)
        >>> with track_phase("Data Processing", logger):
        ...     process_data()
        2024-11-24 16:00:00 | INFO | Processing phase: Data Processing
        2024-11-24 16:00:05 | INFO | ✓ Completed Data Processing (5.23s)

        >>> with track_phase("Analysis", logger) as metrics:
        ...     analyze()
        ...     print(f"Elapsed: {time.time() - metrics.start_time:.2f}s")
    """
    # Use default logger if none provided
    if logger is None:
        logger = logging.getLogger(__name__)

    # Create metrics object
    metrics = PhaseMetrics(
        phase_name=phase_name,
        start_time=time.time(),
    )

    # Log phase start
    logger.log(log_level, f"▶ Starting phase: {phase_name}")

    # Update Streamlit UI if container provided
    if streamlit_container is not None:
        try:
            streamlit_container.info(f"▶ {phase_name}")
        except Exception as e:
            logger.warning(f"Failed to update Streamlit UI: {e}")

    try:
        yield metrics

        # Phase completed successfully
        metrics.complete(success=True)

        logger.log(
            log_level,
            f"✓ Completed {phase_name} ({metrics.duration:.2f}s)",
        )

        if streamlit_container is not None:
            try:
                streamlit_container.success(
                    f"✓ {phase_name} ({metrics.duration:.2f}s)"
                )
            except Exception as e:
                logger.warning(f"Failed to update Streamlit UI: {e}")

    except Exception as e:
        # Phase failed
        error_msg = str(e)
        metrics.complete(success=False, error_message=error_msg)

        logger.error(
            f"✗ Failed {phase_name} after {metrics.duration:.2f}s: {error_msg}"
        )

        if streamlit_container is not None:
            try:
                streamlit_container.error(
                    f"✗ {phase_name} failed: {error_msg}"
                )
            except Exception as ui_error:
                logger.warning(f"Failed to update Streamlit UI: {ui_error}")

        # Re-raise the original exception
        raise


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(1.5)
        '1.50s'
        >>> format_duration(65.3)
        '1m 5.30s'
        >>> format_duration(3665.0)
        '1h 1m 5.00s'
    """
    if seconds < 60:
        return f"{seconds:.2f}s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.2f}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{hours}h {remaining_minutes}m {remaining_seconds:.2f}s"


def log_phase_summary(
    tracker: ProgressTracker,
    logger: logging.Logger,
    log_level: int = logging.INFO,
) -> None:
    """
    Log summary of all tracked phases.

    Args:
        tracker: ProgressTracker with completed phases
        logger: Logger instance for output
        log_level: Log level for summary (default: INFO)

    Examples:
        >>> tracker = ProgressTracker("Agent Query")
        >>> # ... execute phases ...
        >>> log_phase_summary(tracker, logger)
    """
    summary = tracker.get_summary()

    logger.log(log_level, "=" * 80)
    logger.log(log_level, f"Operation Summary: {summary['name']}")
    logger.log(log_level, "=" * 80)
    logger.log(log_level, f"Total Phases: {summary['total_phases']}")
    logger.log(log_level, f"Successful: {summary['successful_phases']}")
    logger.log(log_level, f"Failed: {summary['failed_phases']}")
    logger.log(
        log_level,
        f"Total Duration: {format_duration(summary['total_duration'])}",
    )

    logger.log(log_level, "")
    logger.log(log_level, "Phase Breakdown:")

    for phase in summary["phases"]:
        status = "✓" if phase["success"] else "✗"
        duration = format_duration(phase["duration"]) if phase["duration"] else "N/A"

        logger.log(
            log_level,
            f"  {status} {phase['phase_name']}: {duration}",
        )

        if not phase["success"] and phase["error_message"]:
            logger.log(
                log_level,
                f"      Error: {phase['error_message']}",
            )

    logger.log(log_level, "=" * 80)
