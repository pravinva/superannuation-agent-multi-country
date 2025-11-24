"""
Unit tests for shared.progress_tracker module.

Tests cover:
- PhaseMetrics dataclass functionality
- ProgressTracker multi-phase tracking
- track_phase context manager
- Duration formatting
- Summary logging
- Error handling

Author: Refactoring Team
Date: 2024-11-24
"""

import pytest
import logging
import time
from unittest.mock import Mock, MagicMock, patch

from shared.progress_tracker import (
    PhaseMetrics,
    ProgressTracker,
    track_phase,
    format_duration,
    log_phase_summary,
)


class TestPhaseMetrics:
    """Test suite for PhaseMetrics dataclass."""

    def test_create_phase_metrics(self):
        """Test creating PhaseMetrics instance."""
        start_time = time.time()
        metrics = PhaseMetrics(phase_name="Test Phase", start_time=start_time)

        assert metrics.phase_name == "Test Phase"
        assert metrics.start_time == start_time
        assert metrics.end_time is None
        assert metrics.duration is None
        assert metrics.success is True
        assert metrics.error_message is None

    def test_complete_successful_phase(self):
        """Test completing phase successfully."""
        metrics = PhaseMetrics(phase_name="Test", start_time=time.time())
        time.sleep(0.01)  # Small delay

        metrics.complete(success=True)

        assert metrics.end_time is not None
        assert metrics.duration is not None
        assert metrics.duration > 0
        assert metrics.success is True
        assert metrics.error_message is None

    def test_complete_failed_phase(self):
        """Test completing phase with failure."""
        metrics = PhaseMetrics(phase_name="Test", start_time=time.time())
        time.sleep(0.01)

        error_msg = "Something went wrong"
        metrics.complete(success=False, error_message=error_msg)

        assert metrics.end_time is not None
        assert metrics.duration is not None
        assert metrics.duration > 0
        assert metrics.success is False
        assert metrics.error_message == error_msg

    def test_to_dict(self):
        """Test converting metrics to dictionary."""
        start_time = time.time()
        metrics = PhaseMetrics(phase_name="Test Phase", start_time=start_time)
        metrics.complete(success=True)

        result = metrics.to_dict()

        assert result["phase_name"] == "Test Phase"
        assert result["start_time"] == start_time
        assert result["end_time"] is not None
        assert result["duration"] is not None
        assert result["success"] is True
        assert result["error_message"] is None

    def test_to_dict_with_error(self):
        """Test to_dict includes error message."""
        metrics = PhaseMetrics(phase_name="Test", start_time=time.time())
        metrics.complete(success=False, error_message="Error occurred")

        result = metrics.to_dict()

        assert result["success"] is False
        assert result["error_message"] == "Error occurred"


class TestProgressTracker:
    """Test suite for ProgressTracker class."""

    def test_create_progress_tracker(self):
        """Test creating ProgressTracker instance."""
        tracker = ProgressTracker(name="Test Operation")

        assert tracker.name == "Test Operation"
        assert len(tracker.phases) == 0
        assert tracker.current_phase is None

    def test_start_phase(self):
        """Test starting a new phase."""
        tracker = ProgressTracker(name="Test")

        metrics = tracker.start_phase("Phase 1")

        assert tracker.current_phase is not None
        assert tracker.current_phase.phase_name == "Phase 1"
        assert metrics is tracker.current_phase

    def test_start_phase_while_active_raises_error(self):
        """Test that starting phase while one is active raises error."""
        tracker = ProgressTracker(name="Test")
        tracker.start_phase("Phase 1")

        with pytest.raises(RuntimeError, match="phase .* is still active"):
            tracker.start_phase("Phase 2")

    def test_end_phase(self):
        """Test ending a phase."""
        tracker = ProgressTracker(name="Test")
        tracker.start_phase("Phase 1")
        time.sleep(0.01)

        completed = tracker.end_phase(success=True)

        assert completed is not None
        assert completed.phase_name == "Phase 1"
        assert completed.duration is not None
        assert tracker.current_phase is None
        assert len(tracker.phases) == 1
        assert tracker.phases[0] is completed

    def test_end_phase_with_no_active_raises_error(self):
        """Test ending phase when none is active raises error."""
        tracker = ProgressTracker(name="Test")

        with pytest.raises(RuntimeError, match="no phase is active"):
            tracker.end_phase()

    def test_end_phase_with_error(self):
        """Test ending phase with error."""
        tracker = ProgressTracker(name="Test")
        tracker.start_phase("Phase 1")
        time.sleep(0.01)

        completed = tracker.end_phase(success=False, error_message="Failed")

        assert completed.success is False
        assert completed.error_message == "Failed"
        assert len(tracker.phases) == 1

    def test_multiple_phases_sequential(self):
        """Test tracking multiple phases sequentially."""
        tracker = ProgressTracker(name="Test")

        # Phase 1
        tracker.start_phase("Phase 1")
        time.sleep(0.01)
        tracker.end_phase()

        # Phase 2
        tracker.start_phase("Phase 2")
        time.sleep(0.01)
        tracker.end_phase()

        # Phase 3
        tracker.start_phase("Phase 3")
        time.sleep(0.01)
        tracker.end_phase()

        assert len(tracker.phases) == 3
        assert tracker.phases[0].phase_name == "Phase 1"
        assert tracker.phases[1].phase_name == "Phase 2"
        assert tracker.phases[2].phase_name == "Phase 3"

    def test_get_total_duration(self):
        """Test calculating total duration."""
        tracker = ProgressTracker(name="Test")

        tracker.start_phase("Phase 1")
        time.sleep(0.01)
        tracker.end_phase()

        tracker.start_phase("Phase 2")
        time.sleep(0.01)
        tracker.end_phase()

        total = tracker.get_total_duration()

        assert total > 0
        assert total >= (tracker.phases[0].duration + tracker.phases[1].duration)

    def test_get_summary(self):
        """Test getting operation summary."""
        tracker = ProgressTracker(name="Test Operation")

        tracker.start_phase("Phase 1")
        tracker.end_phase(success=True)

        tracker.start_phase("Phase 2")
        tracker.end_phase(success=False, error_message="Error")

        summary = tracker.get_summary()

        assert summary["name"] == "Test Operation"
        assert summary["total_phases"] == 2
        assert summary["successful_phases"] == 1
        assert summary["failed_phases"] == 1
        assert summary["total_duration"] > 0
        assert len(summary["phases"]) == 2


class TestTrackPhaseContextManager:
    """Test suite for track_phase context manager."""

    def test_track_phase_successful(self, capsys):
        """Test tracking successful phase."""
        logger = logging.getLogger("test")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        with track_phase("Test Phase", logger) as metrics:
            time.sleep(0.01)
            assert metrics.phase_name == "Test Phase"
            assert metrics.start_time is not None

        # Phase should be completed
        assert metrics.end_time is not None
        assert metrics.duration is not None
        assert metrics.success is True

        # Check output
        captured = capsys.readouterr()
        assert "Starting phase: Test Phase" in captured.err or "Starting phase: Test Phase" in captured.out
        assert "Completed Test Phase" in captured.err or "Completed Test Phase" in captured.out

    def test_track_phase_with_exception(self, capsys):
        """Test tracking phase that raises exception."""
        logger = logging.getLogger("test")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        with pytest.raises(ValueError, match="Test error"):
            with track_phase("Failing Phase", logger) as metrics:
                raise ValueError("Test error")

        # Metrics should show failure
        assert metrics.success is False
        assert metrics.error_message == "Test error"
        assert metrics.duration is not None

        # Check error was logged
        captured = capsys.readouterr()
        output = captured.err + captured.out
        assert "Failed Failing Phase" in output or "Failing Phase" in output

    def test_track_phase_without_logger(self, capsys):
        """Test track_phase creates default logger if none provided."""
        with track_phase("Test Phase") as metrics:
            time.sleep(0.01)

        assert metrics.duration is not None
        assert metrics.success is True

    def test_track_phase_custom_log_level(self):
        """Test track_phase with custom log level."""
        logger = Mock(spec=logging.Logger)

        with track_phase("Test Phase", logger, log_level=logging.DEBUG):
            pass

        # Should use custom log level
        logger.log.assert_called()
        call_args = [call[0] for call in logger.log.call_args_list]
        assert any(logging.DEBUG in call for call in call_args)

    def test_track_phase_with_streamlit(self):
        """Test track_phase with Streamlit container."""
        logger = logging.getLogger("test")
        st_container = Mock()

        with track_phase("Test Phase", logger, streamlit_container=st_container):
            pass

        # Streamlit methods should be called
        st_container.info.assert_called_once()
        st_container.success.assert_called_once()

    def test_track_phase_with_streamlit_error(self):
        """Test track_phase handles Streamlit errors gracefully."""
        logger = logging.getLogger("test")
        st_container = Mock()
        st_container.info.side_effect = Exception("Streamlit error")

        # Should not raise exception
        with track_phase("Test Phase", logger, streamlit_container=st_container):
            pass

    def test_track_phase_with_streamlit_failure(self):
        """Test track_phase updates Streamlit on failure."""
        logger = logging.getLogger("test")
        st_container = Mock()

        with pytest.raises(ValueError):
            with track_phase("Test Phase", logger, streamlit_container=st_container):
                raise ValueError("Test error")

        # Error should be shown in Streamlit
        st_container.error.assert_called_once()


class TestFormatDuration:
    """Test suite for format_duration function."""

    def test_format_seconds(self):
        """Test formatting duration in seconds."""
        assert format_duration(0.5) == "0.50s"
        assert format_duration(1.0) == "1.00s"
        assert format_duration(30.25) == "30.25s"
        assert format_duration(59.99) == "59.99s"

    def test_format_minutes(self):
        """Test formatting duration in minutes."""
        assert format_duration(60.0) == "1m 0.00s"
        assert format_duration(90.5) == "1m 30.50s"
        assert format_duration(150.75) == "2m 30.75s"
        assert format_duration(3599.0) == "59m 59.00s"

    def test_format_hours(self):
        """Test formatting duration in hours."""
        assert format_duration(3600.0) == "1h 0m 0.00s"
        assert format_duration(3665.0) == "1h 1m 5.00s"
        assert format_duration(7325.5) == "2h 2m 5.50s"

    def test_format_edge_cases(self):
        """Test formatting edge cases."""
        assert format_duration(0.0) == "0.00s"
        assert format_duration(0.001) == "0.00s"


class TestLogPhaseSummary:
    """Test suite for log_phase_summary function."""

    def test_log_summary_single_phase(self, capsys):
        """Test logging summary with single phase."""
        logger = logging.getLogger("test")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        tracker = ProgressTracker(name="Test Operation")
        tracker.start_phase("Phase 1")
        time.sleep(0.01)
        tracker.end_phase(success=True)

        log_phase_summary(tracker, logger)

        captured = capsys.readouterr()
        output = captured.err + captured.out

        assert "Operation Summary: Test Operation" in output
        assert "Total Phases: 1" in output
        assert "Successful: 1" in output
        assert "Failed: 0" in output
        assert "Phase 1" in output

    def test_log_summary_multiple_phases(self, capsys):
        """Test logging summary with multiple phases."""
        logger = logging.getLogger("test")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        tracker = ProgressTracker(name="Complex Operation")

        tracker.start_phase("Phase 1")
        tracker.end_phase(success=True)

        tracker.start_phase("Phase 2")
        tracker.end_phase(success=False, error_message="Test error")

        tracker.start_phase("Phase 3")
        tracker.end_phase(success=True)

        log_phase_summary(tracker, logger)

        captured = capsys.readouterr()
        output = captured.err + captured.out

        assert "Total Phases: 3" in output
        assert "Successful: 2" in output
        assert "Failed: 1" in output
        assert "Phase 1" in output
        assert "Phase 2" in output
        assert "Phase 3" in output
        assert "Test error" in output

    def test_log_summary_custom_level(self):
        """Test logging summary with custom log level."""
        logger = Mock(spec=logging.Logger)
        tracker = ProgressTracker(name="Test")

        tracker.start_phase("Phase 1")
        tracker.end_phase()

        log_phase_summary(tracker, logger, log_level=logging.DEBUG)

        # Should use DEBUG level
        logger.log.assert_called()
        call_args = [call[0] for call in logger.log.call_args_list]
        assert any(logging.DEBUG in call for call in call_args)


class TestIntegration:
    """Integration tests for complete tracking workflow."""

    def test_end_to_end_tracking(self, capsys):
        """Test complete tracking workflow."""
        logger = logging.getLogger("integration_test")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        tracker = ProgressTracker(name="Agent Query")

        # Phase 1: Planning
        with track_phase("Planning", logger) as metrics:
            time.sleep(0.01)

        tracker.phases.append(metrics)

        # Phase 2: Tool Execution
        with track_phase("Tool Execution", logger) as metrics:
            time.sleep(0.01)

        tracker.phases.append(metrics)

        # Phase 3: Response Generation
        with track_phase("Response Generation", logger) as metrics:
            time.sleep(0.01)

        tracker.phases.append(metrics)

        # Log summary
        log_phase_summary(tracker, logger)

        # Verify all phases completed
        assert len(tracker.phases) == 3
        assert all(phase.success for phase in tracker.phases)
        assert tracker.get_total_duration() > 0

        # Check output
        captured = capsys.readouterr()
        output = captured.err + captured.out

        assert "Planning" in output
        assert "Tool Execution" in output
        assert "Response Generation" in output
        assert "Operation Summary" in output

    def test_mixed_success_failure(self, capsys):
        """Test tracking with both successful and failed phases."""
        logger = logging.getLogger("test")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        tracker = ProgressTracker(name="Mixed Operation")

        # Successful phase
        with track_phase("Success Phase", logger) as metrics:
            pass
        tracker.phases.append(metrics)

        # Failed phase
        try:
            with track_phase("Failure Phase", logger) as metrics:
                raise ValueError("Intentional error")
        except ValueError:
            pass
        tracker.phases.append(metrics)

        # Another successful phase
        with track_phase("Recovery Phase", logger) as metrics:
            pass
        tracker.phases.append(metrics)

        summary = tracker.get_summary()

        assert summary["total_phases"] == 3
        assert summary["successful_phases"] == 2
        assert summary["failed_phases"] == 1
