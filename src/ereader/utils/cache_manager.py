"""Cache coordination utilities for managing multiple cache layers.

This module provides the CacheManager class for coordinating multiple
caches with a shared memory budget.
"""

import logging
from typing import Any

from ereader.utils.cache import ChapterCache
from ereader.utils.image_cache import ImageCache
from ereader.utils.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


class CacheManager:
    """Coordinate multiple caches with shared memory budget.

    Manages three cache layers:
    1. Rendered chapters (ChapterCache): Full HTML with embedded images
    2. Raw chapters (ChapterCache): Raw HTML content before image resolution
    3. Images (ImageCache): Processed/decoded images

    Each cache operates independently but is monitored as part of a
    shared memory budget.

    Args:
        rendered_maxsize: Max rendered chapters to cache (default: 10)
        raw_maxsize: Max raw chapters to cache (default: 20)
        image_max_memory_mb: Max memory for images in MB (default: 50)
        total_memory_threshold_mb: Total memory threshold in MB (default: 150)

    Example:
        >>> manager = CacheManager()
        >>> manager.rendered_chapters.set("book:0", "<html>...")
        >>> manager.raw_chapters.set("book:0", "<body>...")
        >>> manager.images.set("images/photo.jpg", base64_data)
        >>> stats = manager.get_combined_stats()
        >>> print(f"Total memory: {stats['total_memory_mb']:.1f} MB")
    """

    def __init__(
        self,
        rendered_maxsize: int = 10,
        raw_maxsize: int = 20,
        image_max_memory_mb: int = 50,
        total_memory_threshold_mb: int = 150,
    ) -> None:
        """Initialize the cache manager.

        Args:
            rendered_maxsize: Maximum rendered chapters to cache.
            raw_maxsize: Maximum raw chapters to cache.
            image_max_memory_mb: Maximum memory for images in MB.
            total_memory_threshold_mb: Total memory threshold for monitoring.

        Raises:
            ValueError: If any size parameter is not positive.
        """
        if rendered_maxsize < 1:
            raise ValueError("rendered_maxsize must be at least 1")
        if raw_maxsize < 1:
            raise ValueError("raw_maxsize must be at least 1")
        if image_max_memory_mb <= 0:
            raise ValueError("image_max_memory_mb must be positive")
        if total_memory_threshold_mb <= 0:
            raise ValueError("total_memory_threshold_mb must be positive")

        # Initialize cache layers
        self.rendered_chapters = ChapterCache(maxsize=rendered_maxsize)
        self.raw_chapters = ChapterCache(maxsize=raw_maxsize)
        self.images = ImageCache(max_memory_mb=image_max_memory_mb)

        # Initialize memory monitor
        self.memory_monitor = MemoryMonitor(threshold_mb=total_memory_threshold_mb)

        logger.info(
            "CacheManager initialized: rendered=%d, raw=%d, images=%dMB, threshold=%dMB",
            rendered_maxsize,
            raw_maxsize,
            image_max_memory_mb,
            total_memory_threshold_mb,
        )

    def clear_all(self) -> None:
        """Clear all cache layers.

        Useful when opening a new book or resetting application state.
        """
        logger.info("Clearing all cache layers")
        self.rendered_chapters.clear()
        self.raw_chapters.clear()
        self.images.clear()

    def get_combined_stats(self) -> dict[str, Any]:
        """Get combined statistics from all caches.

        Returns:
            Dictionary with combined metrics:
            - rendered_stats: Stats from rendered chapters cache
            - raw_stats: Stats from raw chapters cache
            - image_stats: Stats from image cache
            - memory_stats: Stats from memory monitor
            - total_memory_mb: Combined estimated memory usage
            - total_items: Total items across all caches
        """
        rendered_stats = self.rendered_chapters.stats()
        raw_stats = self.raw_chapters.stats()
        image_stats = self.images.stats()
        memory_stats = self.memory_monitor.get_stats()

        # Calculate totals
        total_memory_mb = (
            rendered_stats.get("estimated_memory_mb", 0)
            + raw_stats.get("estimated_memory_mb", 0)
            + image_stats.get("memory_mb", 0)
        )

        total_items = (
            rendered_stats["size"] + raw_stats["size"] + image_stats["size"]
        )

        return {
            "rendered_stats": rendered_stats,
            "raw_stats": raw_stats,
            "image_stats": image_stats,
            "memory_stats": memory_stats,
            "total_memory_mb": total_memory_mb,
            "total_items": total_items,
        }

    def check_memory_threshold(self) -> bool:
        """Check if total memory exceeds threshold.

        Returns:
            True if memory exceeds threshold, False otherwise.
        """
        return self.memory_monitor.check_threshold()

    def log_stats(self) -> None:
        """Log combined cache statistics at DEBUG level.

        Useful for debugging and monitoring cache behavior.
        """
        stats = self.get_combined_stats()

        logger.debug(
            "Cache stats: rendered=%d/%d, raw=%d/%d, images=%d (%.1f/%.1f MB)",
            stats["rendered_stats"]["size"],
            stats["rendered_stats"]["maxsize"],
            stats["raw_stats"]["size"],
            stats["raw_stats"]["maxsize"],
            stats["image_stats"]["size"],
            stats["image_stats"]["memory_mb"],
            stats["image_stats"]["max_memory_mb"],
        )

        logger.debug(
            "Cache performance: rendered hit_rate=%.1f%%, raw hit_rate=%.1f%%, images hit_rate=%.1f%%",
            stats["rendered_stats"]["hit_rate"],
            stats["raw_stats"]["hit_rate"],
            stats["image_stats"]["hit_rate"],
        )

        logger.debug(
            "Memory: total_cache=%.1f MB, process=%.1f MB, threshold=%d MB",
            stats["total_memory_mb"],
            stats["memory_stats"]["current_usage_mb"],
            stats["memory_stats"]["threshold_mb"],
        )
