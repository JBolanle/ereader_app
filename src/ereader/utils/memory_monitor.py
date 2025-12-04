"""Memory monitoring utilities for tracking application memory usage.

This module provides the MemoryMonitor class for tracking process memory usage
and alerting when configurable thresholds are exceeded.
"""

import logging
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage and alert when thresholds exceeded.

    Tracks the current process's memory usage using psutil and logs warnings
    when memory exceeds configured thresholds. Also logs informational milestones
    at regular intervals (100MB, 125MB, 150MB, etc.).

    Args:
        threshold_mb: Memory threshold in MB. Warnings logged when exceeded (default: 150).

    Example:
        >>> monitor = MemoryMonitor(threshold_mb=150)
        >>> usage = monitor.get_current_usage()
        >>> print(f"Current memory: {usage:.1f} MB")
        >>> if monitor.check_threshold():
        ...     print("Memory threshold exceeded!")
    """

    # Memory milestones for INFO logging (in MB)
    _MILESTONES = [100, 125, 150, 175, 200, 250, 300]

    def __init__(self, threshold_mb: int = 150) -> None:
        """Initialize the memory monitor.

        Args:
            threshold_mb: Memory threshold in MB (must be positive).

        Raises:
            ValueError: If threshold_mb is not positive.
        """
        if threshold_mb <= 0:
            raise ValueError("threshold_mb must be positive")

        self._threshold_mb = threshold_mb
        self._process = psutil.Process()
        self._last_milestone_logged: int | None = None
        self._threshold_exceeded = False
        self._creation_time = time.time()

        logger.info("MemoryMonitor initialized with threshold=%d MB", threshold_mb)

    def get_current_usage(self) -> float:
        """Get current process memory usage in MB.

        Returns:
            Current memory usage in megabytes (RSS - Resident Set Size).
        """
        # Get memory info and convert bytes to MB
        mem_info = self._process.memory_info()
        usage_mb = mem_info.rss / (1024 * 1024)

        logger.debug("Current memory usage: %.2f MB", usage_mb)
        return usage_mb

    def check_threshold(self) -> bool:
        """Check if memory exceeds threshold.

        Logs a WARNING if memory exceeds the configured threshold (only once
        until memory drops below threshold again). Also logs INFO messages
        when passing memory milestones.

        Returns:
            True if memory exceeds threshold, False otherwise.
        """
        current_usage = self.get_current_usage()

        # Check and log milestones
        self._check_milestones(current_usage)

        # Check threshold
        if current_usage > self._threshold_mb:
            if not self._threshold_exceeded:
                # First time exceeding threshold - log warning
                logger.warning(
                    "Memory usage (%.1f MB) exceeds threshold (%d MB)",
                    current_usage,
                    self._threshold_mb,
                )
                self._threshold_exceeded = True
            return True
        else:
            # Memory dropped below threshold - reset flag
            if self._threshold_exceeded:
                logger.info(
                    "Memory usage (%.1f MB) dropped below threshold (%d MB)",
                    current_usage,
                    self._threshold_mb,
                )
                self._threshold_exceeded = False
            return False

    def _check_milestones(self, current_usage: float) -> None:
        """Check and log memory milestones.

        Logs INFO messages when passing configured memory milestones
        (100MB, 125MB, 150MB, etc.). Only logs each milestone once.

        Args:
            current_usage: Current memory usage in MB.
        """
        # Find the highest milestone we've passed
        current_milestone = None
        for milestone in self._MILESTONES:
            if current_usage >= milestone:
                current_milestone = milestone
            else:
                break  # Milestones are sorted, no need to check further

        # Log if we've reached a new milestone
        if current_milestone is not None and current_milestone != self._last_milestone_logged:
            logger.info("Memory milestone reached: %d MB (current: %.1f MB)", current_milestone, current_usage)
            self._last_milestone_logged = current_milestone

    def get_age_seconds(self) -> float:
        """Get monitor age since creation.

        Returns:
            Time in seconds since monitor was created.
        """
        return time.time() - self._creation_time

    def get_stats(self) -> dict[str, Any]:
        """Get memory monitor statistics.

        Returns:
            Dictionary with monitoring metrics:
            - current_usage_mb: Current memory usage in MB
            - threshold_mb: Configured threshold in MB
            - threshold_exceeded: Whether threshold is currently exceeded
            - age_seconds: Time since monitor creation
            - last_milestone: Last milestone logged (or None)
        """
        return {
            "current_usage_mb": self.get_current_usage(),
            "threshold_mb": self._threshold_mb,
            "threshold_exceeded": self._threshold_exceeded,
            "age_seconds": self.get_age_seconds(),
            "last_milestone": self._last_milestone_logged,
        }
