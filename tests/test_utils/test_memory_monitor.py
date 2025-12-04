"""Tests for memory monitoring functionality."""

import time
from unittest.mock import MagicMock, patch

import pytest

from ereader.utils.memory_monitor import MemoryMonitor


class TestMemoryMonitorInit:
    """Test MemoryMonitor initialization."""

    def test_init_default_threshold(self) -> None:
        """Test initialization with default threshold."""
        monitor = MemoryMonitor()
        assert monitor._threshold_mb == 150
        assert monitor._threshold_exceeded is False
        assert monitor._last_milestone_logged is None

    def test_init_custom_threshold(self) -> None:
        """Test initialization with custom threshold."""
        monitor = MemoryMonitor(threshold_mb=200)
        assert monitor._threshold_mb == 200

    def test_init_invalid_threshold_zero(self) -> None:
        """Test initialization fails with zero threshold."""
        with pytest.raises(ValueError, match="threshold_mb must be positive"):
            MemoryMonitor(threshold_mb=0)

    def test_init_invalid_threshold_negative(self) -> None:
        """Test initialization fails with negative threshold."""
        with pytest.raises(ValueError, match="threshold_mb must be positive"):
            MemoryMonitor(threshold_mb=-10)


class TestMemoryMonitorGetCurrentUsage:
    """Test get_current_usage method."""

    @patch("psutil.Process")
    def test_get_current_usage_returns_mb(self, mock_process_class: MagicMock) -> None:
        """Test get_current_usage returns memory in MB."""
        # Mock memory info: 100 MB in bytes
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024  # 100 MB

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()
        usage = monitor.get_current_usage()

        assert usage == pytest.approx(100.0, rel=0.01)
        mock_process.memory_info.assert_called_once()

    @patch("psutil.Process")
    def test_get_current_usage_fractional_mb(self, mock_process_class: MagicMock) -> None:
        """Test get_current_usage with fractional MB values."""
        # Mock memory info: 50.5 MB in bytes
        mock_mem_info = MagicMock()
        mock_mem_info.rss = int(50.5 * 1024 * 1024)

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()
        usage = monitor.get_current_usage()

        assert usage == pytest.approx(50.5, rel=0.01)


class TestMemoryMonitorCheckThreshold:
    """Test check_threshold method."""

    @patch("psutil.Process")
    def test_check_threshold_below(self, mock_process_class: MagicMock) -> None:
        """Test check_threshold returns False when below threshold."""
        # Mock memory info: 100 MB (below 150 MB threshold)
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)
        result = monitor.check_threshold()

        assert result is False
        assert monitor._threshold_exceeded is False

    @patch("psutil.Process")
    def test_check_threshold_exceeded(self, mock_process_class: MagicMock) -> None:
        """Test check_threshold returns True when threshold exceeded."""
        # Mock memory info: 200 MB (above 150 MB threshold)
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 200 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)
        result = monitor.check_threshold()

        assert result is True
        assert monitor._threshold_exceeded is True

    @patch("psutil.Process")
    def test_check_threshold_logs_warning_once(
        self, mock_process_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test check_threshold logs warning only once when threshold exceeded."""
        # Mock memory info: 200 MB (above 150 MB threshold)
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 200 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)

        # First call - should log warning
        with caplog.at_level("WARNING"):
            monitor.check_threshold()
        assert "exceeds threshold" in caplog.text
        warning_count = caplog.text.count("exceeds threshold")

        # Second call - should not log another warning
        caplog.clear()
        with caplog.at_level("WARNING"):
            monitor.check_threshold()
        assert "exceeds threshold" not in caplog.text
        assert warning_count == 1

    @patch("psutil.Process")
    def test_check_threshold_logs_recovery(
        self, mock_process_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test check_threshold logs when memory drops below threshold."""
        mock_mem_info = MagicMock()
        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)

        # First: exceed threshold
        mock_mem_info.rss = 200 * 1024 * 1024
        monitor.check_threshold()
        assert monitor._threshold_exceeded is True

        # Second: drop below threshold
        mock_mem_info.rss = 100 * 1024 * 1024
        with caplog.at_level("INFO"):
            result = monitor.check_threshold()

        assert result is False
        assert monitor._threshold_exceeded is False
        assert "dropped below threshold" in caplog.text


class TestMemoryMonitorMilestones:
    """Test milestone logging functionality."""

    @patch("psutil.Process")
    def test_milestone_logged_at_100mb(
        self, mock_process_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test milestone is logged when reaching 100MB."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()

        with caplog.at_level("INFO"):
            monitor.check_threshold()

        assert "Memory milestone reached: 100 MB" in caplog.text

    @patch("psutil.Process")
    def test_milestone_logged_only_once(
        self, mock_process_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test milestone is logged only once."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()

        # First call - should log
        with caplog.at_level("INFO"):
            monitor.check_threshold()
        assert "Memory milestone reached: 100 MB" in caplog.text

        # Second call - should not log again
        caplog.clear()
        with caplog.at_level("INFO"):
            monitor.check_threshold()
        assert "Memory milestone reached" not in caplog.text

    @patch("psutil.Process")
    def test_multiple_milestones_in_sequence(
        self, mock_process_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test multiple milestones are logged as memory increases."""
        mock_mem_info = MagicMock()
        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()

        # Reach 100 MB
        mock_mem_info.rss = 100 * 1024 * 1024
        with caplog.at_level("INFO"):
            monitor.check_threshold()
        assert "Memory milestone reached: 100 MB" in caplog.text

        # Reach 125 MB
        caplog.clear()
        mock_mem_info.rss = 125 * 1024 * 1024
        with caplog.at_level("INFO"):
            monitor.check_threshold()
        assert "Memory milestone reached: 125 MB" in caplog.text

        # Reach 150 MB
        caplog.clear()
        mock_mem_info.rss = 150 * 1024 * 1024
        with caplog.at_level("INFO"):
            monitor.check_threshold()
        assert "Memory milestone reached: 150 MB" in caplog.text

    @patch("psutil.Process")
    def test_no_milestone_below_100mb(
        self, mock_process_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test no milestone logged for memory below 100MB."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 50 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()

        with caplog.at_level("INFO"):
            monitor.check_threshold()

        assert "Memory milestone reached" not in caplog.text


class TestMemoryMonitorGetAgeSeconds:
    """Test get_age_seconds method."""

    @patch("psutil.Process")
    def test_get_age_seconds_initial(self, mock_process_class: MagicMock) -> None:
        """Test age is approximately 0 immediately after creation."""
        mock_process_class.return_value = MagicMock()

        monitor = MemoryMonitor()
        age = monitor.get_age_seconds()

        assert age < 0.1  # Should be very close to 0

    @patch("psutil.Process")
    def test_get_age_seconds_after_delay(self, mock_process_class: MagicMock) -> None:
        """Test age increases with time."""
        mock_process_class.return_value = MagicMock()

        monitor = MemoryMonitor()
        time.sleep(0.1)  # Wait 100ms
        age = monitor.get_age_seconds()

        assert age >= 0.1  # At least 100ms has passed


class TestMemoryMonitorGetStats:
    """Test get_stats method."""

    @patch("psutil.Process")
    def test_get_stats_structure(self, mock_process_class: MagicMock) -> None:
        """Test get_stats returns correct structure."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)
        stats = monitor.get_stats()

        assert "current_usage_mb" in stats
        assert "threshold_mb" in stats
        assert "threshold_exceeded" in stats
        assert "age_seconds" in stats
        assert "last_milestone" in stats

    @patch("psutil.Process")
    def test_get_stats_values(self, mock_process_class: MagicMock) -> None:
        """Test get_stats returns correct values."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 100 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)
        stats = monitor.get_stats()

        assert stats["current_usage_mb"] == pytest.approx(100.0, rel=0.01)
        assert stats["threshold_mb"] == 150
        assert stats["threshold_exceeded"] is False
        assert stats["age_seconds"] >= 0
        assert stats["last_milestone"] is None

    @patch("psutil.Process")
    def test_get_stats_with_milestone(self, mock_process_class: MagicMock) -> None:
        """Test get_stats includes last milestone when logged."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 125 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()
        monitor.check_threshold()  # Trigger milestone logging
        stats = monitor.get_stats()

        assert stats["last_milestone"] == 125

    @patch("psutil.Process")
    def test_get_stats_threshold_exceeded(self, mock_process_class: MagicMock) -> None:
        """Test get_stats reflects threshold exceeded state."""
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 200 * 1024 * 1024

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(threshold_mb=150)
        monitor.check_threshold()  # Trigger threshold check
        stats = monitor.get_stats()

        assert stats["threshold_exceeded"] is True
        assert stats["current_usage_mb"] > stats["threshold_mb"]
