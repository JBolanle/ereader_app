"""Image caching utilities for memory-efficient image storage.

This module provides the ImageCache class for caching processed images
with memory-based LRU eviction.
"""

import logging
import sys
import threading
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)


class ImageCache:
    """LRU cache for processed images with memory-based eviction.

    Unlike ChapterCache which uses count-based eviction, ImageCache
    evicts based on total memory usage. This is more appropriate for
    images which can vary significantly in size.

    Thread-safe: All operations are protected by an RLock to allow
    concurrent access from UI thread and background loader threads.

    Args:
        max_memory_mb: Maximum memory budget in MB (default: 50)

    Example:
        >>> cache = ImageCache(max_memory_mb=50)
        >>> cache.set("images/photo.jpg", base64_data)
        >>> data = cache.get("images/photo.jpg")
        >>> print(cache.stats())
        {'size': 1, 'memory_mb': 2.5, 'max_memory_mb': 50, ...}
    """

    def __init__(self, max_memory_mb: int = 50) -> None:
        """Initialize the image cache.

        Args:
            max_memory_mb: Maximum memory budget in MB (must be positive).

        Raises:
            ValueError: If max_memory_mb is not positive.
        """
        if max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")

        self._cache: OrderedDict[str, str] = OrderedDict()
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._max_memory_mb = max_memory_mb
        self._current_memory_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._last_eviction_time: float | None = None
        self._creation_time = time.time()
        self._lock = threading.RLock()  # Reentrant lock for thread safety

        logger.info("ImageCache initialized with max_memory=%d MB", max_memory_mb)

    def get(self, key: str) -> str | None:
        """Retrieve cached image data by key.

        If key exists, marks it as recently used by moving to end.

        Thread-safe: Protected by lock for concurrent access.

        Args:
            key: Cache key (typically the resource path like "images/photo.jpg")

        Returns:
            Cached base64-encoded image string, or None if not found
        """
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)  # Mark as recently used
                self._hits += 1
                logger.debug(
                    "ImageCache HIT: %s (hits=%d, misses=%d)", key, self._hits, self._misses
                )
                return self._cache[key]

            self._misses += 1
            logger.debug(
                "ImageCache MISS: %s (hits=%d, misses=%d)", key, self._hits, self._misses
            )
            return None

    def set(self, key: str, value: str) -> None:
        """Store image data in cache.

        Evicts least recently used items if necessary to stay within memory budget.

        Thread-safe: Protected by lock for concurrent access.

        Args:
            key: Cache key (typically the resource path)
            value: Base64-encoded image data string
        """
        with self._lock:
            # Calculate size of the new value
            value_size = sys.getsizeof(value)

            if key in self._cache:
                # Update existing entry - first remove old size, then add new
                old_value = self._cache[key]
                old_size = sys.getsizeof(old_value)
                self._current_memory_bytes -= old_size
                self._cache.move_to_end(key)
                self._cache[key] = value
                self._current_memory_bytes += value_size
                logger.debug("ImageCache UPDATE: %s (size: %d bytes)", key, value_size)
            else:
                # Add new entry - evict old entries if needed
                # Evict until we have space for the new value
                while self._current_memory_bytes + value_size > self._max_memory_bytes and self._cache:
                    evicted_key, evicted_value = self._cache.popitem(last=False)
                    evicted_size = sys.getsizeof(evicted_value)
                    self._current_memory_bytes -= evicted_size
                    self._evictions += 1
                    self._last_eviction_time = time.time()
                    logger.info(
                        "ImageCache EVICTION: %s (size: %d bytes, memory: %.2f/%.2f MB)",
                        evicted_key,
                        evicted_size,
                        self._current_memory_bytes / (1024 * 1024),
                        self._max_memory_mb,
                    )

                # Add new entry
                self._cache[key] = value
                self._current_memory_bytes += value_size
                logger.debug(
                    "ImageCache SET: %s (size: %d bytes, memory: %.2f/%.2f MB)",
                    key,
                    value_size,
                    self._current_memory_bytes / (1024 * 1024),
                    self._max_memory_mb,
                )

    def clear(self) -> None:
        """Remove all cached entries.

        Thread-safe: Protected by lock for concurrent access.
        """
        with self._lock:
            size = len(self._cache)
            memory_mb = self._current_memory_bytes / (1024 * 1024)
            self._cache.clear()
            self._current_memory_bytes = 0
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            logger.info(
                "ImageCache CLEARED: removed %d entries (%.2f MB freed)", size, memory_mb
            )

    def stats(self) -> dict[str, Any]:
        """Return image cache statistics.

        Thread-safe: Protected by lock for concurrent access.

        Returns:
            Dictionary with cache metrics:
            - size: Current number of cached images
            - memory_mb: Current memory usage in MB
            - max_memory_mb: Maximum memory budget in MB
            - hits: Number of cache hits
            - misses: Number of cache misses
            - evictions: Number of evictions performed
            - hit_rate: Percentage of requests that hit cache
            - memory_utilization: Percentage of memory budget used
            - avg_item_size_kb: Average size of cached items in KB
            - time_since_last_eviction: Seconds since last eviction (or None)
            - cache_age_seconds: Seconds since cache creation
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0

            memory_mb = self._current_memory_bytes / (1024 * 1024)
            memory_utilization = (
                (self._current_memory_bytes / self._max_memory_bytes * 100)
                if self._max_memory_bytes > 0
                else 0.0
            )

            avg_item_size_kb = (
                (self._current_memory_bytes / len(self._cache) / 1024)
                if len(self._cache) > 0
                else 0.0
            )

            cache_age = time.time() - self._creation_time
            time_since_eviction = (
                (time.time() - self._last_eviction_time)
                if self._last_eviction_time is not None
                else None
            )

            return {
                "size": len(self._cache),
                "memory_mb": memory_mb,
                "max_memory_mb": self._max_memory_mb,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "memory_utilization": memory_utilization,
                "avg_item_size_kb": avg_item_size_kb,
                "time_since_last_eviction": time_since_eviction,
                "cache_age_seconds": cache_age,
            }

    def __len__(self) -> int:
        """Return number of items in cache.

        Thread-safe: Protected by lock for concurrent access.
        """
        with self._lock:
            return len(self._cache)
