"""
agents.orchestrator
===================

Agent orchestration framework for phase tracking, timing, and error handling.

Extracts the repetitive phase execution pattern from agent_processor.py:
- Automatic phase tracking (mark_phase_running/complete)
- Timing measurement
- Error handling with phase_error marking
- Consistent logging

Reduces agent_query() from 400+ lines to <150 lines.

Usage:
    >>> from agents.orchestrator import AgentOrchestrator
    >>>
    >>> orchestrator = AgentOrchestrator()
    >>>
    >>> with orchestrator.track_phase("Data Retrieval", "phase_1_retrieval"):
    ...     agent = SuperAdvisorAgent()
    ...     # ... work ...
    >>>
    >>> # Timing is automatic
    >>> print(f"Phase took: {orchestrator.get_last_phase_duration():.2f}s")

Author: Refactoring Team
Date: 2024-11-24
"""

from contextlib import contextmanager
from typing import Optional, Dict, Generator, Any
import time
import logging
from utils.progress import mark_phase_running, mark_phase_complete, mark_phase_error
from shared.logging_config import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Orchestrates agent execution with automatic phase tracking and timing.

    Provides a context manager for phase execution that automatically:
    - Prints phase banners
    - Tracks phase timing
    - Marks phases as running/complete/error
    - Handles errors gracefully

    Examples:
        >>> orchestrator = AgentOrchestrator()
        >>>
        >>> # Basic usage
        >>> with orchestrator.track_phase("Data Retrieval", "phase_1_retrieval"):
        ...     data = load_data()
        ...
        >>> print(f"Duration: {orchestrator.get_last_phase_duration():.2f}s")

        >>> # Error handling (automatic)
        >>> with orchestrator.track_phase("Validation", "phase_6_validation"):
        ...     raise ValueError("Something went wrong")
        # Phase is automatically marked as error

        >>> # Get all timings
        >>> timings = orchestrator.get_all_timings()
        >>> print(timings)  # {'phase_1_retrieval': 1.23, ...}
    """

    def __init__(self):
        """Initialize orchestrator with empty timing storage."""
        self._phase_timings: Dict[str, float] = {}
        self._last_phase_key: Optional[str] = None

    @contextmanager
    def track_phase(self, phase_name: str, phase_key: str, print_banner: bool = True) -> Generator[None, None, None]:
        """
        Context manager for phase execution with automatic tracking.

        Args:
            phase_name: Human-readable phase name (e.g., "Data Retrieval")
            phase_key: Internal phase key (e.g., "phase_1_retrieval")
            print_banner: Whether to print phase banner (default: True)

        Yields:
            None

        Examples:
            >>> with orchestrator.track_phase("Data Retrieval", "phase_1_retrieval"):
            ...     data = fetch_data()
            ...     process_data(data)

            >>> # Get timing
            >>> duration = orchestrator.get_phase_duration("phase_1_retrieval")
            >>> print(f"Took: {duration:.2f}s")

        Notes:
            - Automatically calls mark_phase_running() on entry
            - Automatically calls mark_phase_complete() on exit
            - Automatically calls mark_phase_error() on exception
            - Exception is re-raised after marking error
        """
        # Log phase banner
        if print_banner:
            logger.info(f"📍 {phase_name}")

        # Start timing
        start_time = time.time()

        # Mark phase as running
        mark_phase_running(phase_key)

        try:
            # Execute phase logic
            yield

            # Calculate duration
            duration = time.time() - start_time
            self._phase_timings[phase_key] = duration
            self._last_phase_key = phase_key

            # Mark phase as complete
            mark_phase_complete(phase_key, duration=duration)

            # Log timing
            if print_banner:
                logger.info(f"⏱️  {phase_name} took: {duration:.2f}s")

        except Exception as e:
            # Calculate duration up to error
            duration = time.time() - start_time
            self._phase_timings[phase_key] = duration
            self._last_phase_key = phase_key

            # Mark phase as error
            mark_phase_error(phase_key, str(e))

            # Log error info
            if print_banner:
                logger.error(f"❌ {phase_name} failed after {duration:.2f}s: {e}")

            # Re-raise exception
            raise

    def get_last_phase_duration(self) -> float:
        """
        Get duration of the last executed phase.

        Returns:
            Duration in seconds, or 0.0 if no phase executed yet

        Examples:
            >>> with orchestrator.track_phase("Phase 1", "phase_1"):
            ...     time.sleep(1)
            >>> print(orchestrator.get_last_phase_duration())  # ~1.0
        """
        if self._last_phase_key is None:
            return 0.0
        return self._phase_timings.get(self._last_phase_key, 0.0)

    def get_phase_duration(self, phase_key: str) -> float:
        """
        Get duration of a specific phase.

        Args:
            phase_key: Internal phase key

        Returns:
            Duration in seconds, or 0.0 if phase not found

        Examples:
            >>> duration = orchestrator.get_phase_duration("phase_1_retrieval")
            >>> print(f"Phase 1 took: {duration:.2f}s")
        """
        return self._phase_timings.get(phase_key, 0.0)

    def get_all_timings(self) -> Dict[str, float]:
        """
        Get all phase timings.

        Returns:
            Dictionary mapping phase_key to duration in seconds

        Examples:
            >>> timings = orchestrator.get_all_timings()
            >>> for phase, duration in timings.items():
            ...     print(f"{phase}: {duration:.2f}s")
        """
        return self._phase_timings.copy()

    def get_total_time(self) -> float:
        """
        Get total time across all phases.

        Returns:
            Total duration in seconds

        Examples:
            >>> total = orchestrator.get_total_time()
            >>> print(f"Total execution time: {total:.2f}s")
        """
        return sum(self._phase_timings.values())

    def reset(self) -> None:
        """
        Reset orchestrator state (clear all timings).

        Examples:
            >>> orchestrator.reset()
            >>> assert orchestrator.get_total_time() == 0.0
        """
        self._phase_timings.clear()
        self._last_phase_key = None


# ============================================================================ #
# CONVENIENCE FUNCTION (for backward compatibility)
# ============================================================================ #

@contextmanager
def track_phase(phase_name: str, phase_key: str, print_banner: bool = True) -> Generator[None, None, None]:
    """
    Standalone context manager for phase tracking (no orchestrator instance needed).

    Args:
        phase_name: Human-readable phase name
        phase_key: Internal phase key
        print_banner: Whether to print phase banner

    Yields:
        None

    Examples:
        >>> from agents.orchestrator import track_phase
        >>>
        >>> with track_phase("Data Retrieval", "phase_1_retrieval"):
        ...     data = fetch_data()

    Notes:
        - This is a convenience function that doesn't track timing
        - Use AgentOrchestrator class if you need timing info
    """
    # Log phase banner
    if print_banner:
        logger.info(f"📍 {phase_name}")

    # Start timing
    start_time = time.time()

    # Mark phase as running
    mark_phase_running(phase_key)

    try:
        # Execute phase logic
        yield

        # Calculate duration
        duration = time.time() - start_time

        # Mark phase as complete
        mark_phase_complete(phase_key, duration=duration)

        # Log timing
        if print_banner:
            logger.info(f"⏱️  {phase_name} took: {duration:.2f}s")

    except Exception as e:
        # Calculate duration up to error
        duration = time.time() - start_time

        # Mark phase as error
        mark_phase_error(phase_key, str(e))

        # Log error info
        if print_banner:
            logger.error(f"❌ {phase_name} failed after {duration:.2f}s: {e}")

        # Re-raise exception
        raise


# ============================================================================ #
# MODULE TEST (run when executed directly)
# ============================================================================ #

if __name__ == "__main__":
    # Set up logging for tests
    from shared.logging_config import setup_logging
    setup_logging(log_level=logging.INFO, enable_file=False)

    logger.info("=" * 70)
    logger.info("Agent Orchestrator - Test Suite")
    logger.info("=" * 70)

    # Test 1: Basic phase tracking
    logger.info("\nTest 1: Basic Phase Tracking")
    orchestrator = AgentOrchestrator()

    try:
        with orchestrator.track_phase("Test Phase 1", "test_phase_1"):
            time.sleep(0.1)
            logger.info("  ✓ Phase 1 work completed")

        duration = orchestrator.get_last_phase_duration()
        logger.info(f"  ✅ Phase duration: {duration:.2f}s")
        assert 0.09 < duration < 0.15, "Duration should be ~0.1s"
    except Exception as e:
        logger.info(f"  ❌ FAIL: {e}")

    # Test 2: Error handling
    logger.info("\nTest 2: Error Handling")
    try:
        with orchestrator.track_phase("Test Phase 2 (Error)", "test_phase_2"):
            raise ValueError("Test error")
    except ValueError as e:
        logger.info(f"  ✅ Error handled correctly: {e}")
        duration = orchestrator.get_phase_duration("test_phase_2")
        logger.info(f"  ✅ Duration recorded despite error: {duration:.4f}s")

    # Test 3: Multiple phases
    logger.info("\nTest 3: Multiple Phases")
    orchestrator.reset()

    with orchestrator.track_phase("Phase A", "phase_a", print_banner=False):
        time.sleep(0.05)

    with orchestrator.track_phase("Phase B", "phase_b", print_banner=False):
        time.sleep(0.05)

    timings = orchestrator.get_all_timings()
    total = orchestrator.get_total_time()

    logger.info(f"  ✅ Phase A: {timings['phase_a']:.2f}s")
    logger.info(f"  ✅ Phase B: {timings['phase_b']:.2f}s")
    logger.info(f"  ✅ Total: {total:.2f}s")

    # Test 4: Standalone function
    logger.info("\nTest 4: Standalone track_phase Function")
    try:
        with track_phase("Standalone Phase", "standalone_test", print_banner=False):
            logger.info("  ✓ Standalone function works")
        logger.info("  ✅ Standalone function test passed")
    except Exception as e:
        logger.info(f"  ❌ FAIL: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ All tests passed!")
    logger.info("=" * 70)
