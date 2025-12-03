"""Caching utilities for improving performance.

This module provides caching implementations for reducing redundant operations
and memory usage during book reading.
"""

import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)


class ChapterCache:
    """LRU cache for rendered chapter HTML.

    Uses OrderedDict to track access order. When cache is full,
    removes the least recently used item.

    Args:
        maxsize: Maximum number of chapters to cache (default: 10)

    Example:
        >>> cache = ChapterCache(maxsize=5)
        >>> cache.set("book.epub:0", "<html>...</html>")
        >>> html = cache.get("book.epub:0")
        >>> print(cache.stats())
        {'size': 1, 'maxsize': 5, 'hits': 1, 'misses': 0, 'hit_rate': 100.0}
    """

    def __init__(self, maxsize: int = 10) -> None:
        """Initialize the chapter cache.

        Args:
            maxsize: Maximum number of chapters to cache (must be at least 1).

        Raises:
            ValueError: If maxsize is less than 1.
        """
        if maxsize < 1:
            raise ValueError("maxsize must be at least 1")

        self._cache: OrderedDict[str, str] = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

        logger.info("ChapterCache initialized with maxsize=%d", maxsize)

    def get(self, key: str) -> str | None:
        """Retrieve cached HTML by key.

        If key exists, marks it as recently used by moving to end.

        Args:
            key: Cache key (typically "book_id:chapter_index")

        Returns:
            Cached HTML string, or None if not found
        """
        if key in self._cache:
            self._cache.move_to_end(key)  # Mark as recently used
            self._hits += 1
            logger.debug(
                "Cache HIT: %s (hits=%d, misses=%d)", key, self._hits, self._misses
            )
            return self._cache[key]

        self._misses += 1
        logger.debug(
            "Cache MISS: %s (hits=%d, misses=%d)", key, self._hits, self._misses
        )
        return None

    def set(self, key: str, value: str) -> None:
        """Store HTML in cache.

        If cache is full, evicts least recently used item.

        Args:
            key: Cache key (typically "book_id:chapter_index")
            value: Rendered HTML string
        """
        if key in self._cache:
            # Update existing entry and mark as recently used
            self._cache.move_to_end(key)
            self._cache[key] = value
            logger.debug("Cache UPDATE: %s", key)
        else:
            # Add new entry
            self._cache[key] = value

            # Evict oldest if necessary
            if len(self._cache) > self._maxsize:
                evicted_key = next(iter(self._cache))
                self._cache.popitem(last=False)  # Remove oldest (first item)
                logger.info(
                    "Cache EVICTION: %s (cache full: %d/%d)",
                    evicted_key,
                    len(self._cache),
                    self._maxsize,
                )
            else:
                logger.debug(
                    "Cache SET: %s (size: %d/%d)", key, len(self._cache), self._maxsize
                )

    def clear(self) -> None:
        """Remove all cached entries."""
        size = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache CLEARED: removed %d entries", size)

    def stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dictionary with cache metrics:
            - size: Current number of cached items
            - maxsize: Maximum cache capacity
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Percentage of requests that hit cache
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    def __len__(self) -> int:
        """Return number of items in cache."""
        return len(self._cache)
