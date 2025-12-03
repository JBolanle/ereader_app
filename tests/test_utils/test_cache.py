"""Tests for caching utilities."""

import pytest

from ereader.utils.cache import ChapterCache


class TestChapterCache:
    """Test suite for ChapterCache LRU implementation."""

    def test_initialization_default_maxsize(self) -> None:
        """Cache should initialize with default maxsize of 10."""
        cache = ChapterCache()
        stats = cache.stats()
        assert stats["maxsize"] == 10
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_initialization_custom_maxsize(self) -> None:
        """Cache should initialize with custom maxsize."""
        cache = ChapterCache(maxsize=5)
        assert cache.stats()["maxsize"] == 5

    def test_initialization_invalid_maxsize(self) -> None:
        """Cache should raise ValueError for maxsize < 1."""
        with pytest.raises(ValueError, match="maxsize must be at least 1"):
            ChapterCache(maxsize=0)

        with pytest.raises(ValueError, match="maxsize must be at least 1"):
            ChapterCache(maxsize=-1)

    def test_cache_miss(self) -> None:
        """Getting non-existent key should return None and record miss."""
        cache = ChapterCache()
        result = cache.get("missing_key")

        assert result is None
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.0

    def test_cache_hit(self) -> None:
        """Getting existing key should return value and record hit."""
        cache = ChapterCache()
        cache.set("key1", "<html>content</html>")

        result = cache.get("key1")

        assert result == "<html>content</html>"
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 100.0

    def test_cache_set_and_get(self) -> None:
        """Basic set and get operations should work."""
        cache = ChapterCache()

        cache.set("book1:0", "<html>Chapter 1</html>")
        cache.set("book1:1", "<html>Chapter 2</html>")

        assert cache.get("book1:0") == "<html>Chapter 1</html>"
        assert cache.get("book1:1") == "<html>Chapter 2</html>"
        assert len(cache) == 2

    def test_cache_update_existing_key(self) -> None:
        """Updating existing key should replace value."""
        cache = ChapterCache()

        cache.set("key1", "original")
        cache.set("key1", "updated")

        assert cache.get("key1") == "updated"
        assert len(cache) == 1

    def test_lru_eviction(self) -> None:
        """Cache should evict least recently used item when full."""
        cache = ChapterCache(maxsize=3)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert len(cache) == 3

        # Add one more - should evict key1 (oldest)
        cache.set("key4", "value4")

        assert len(cache) == 3
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_access_order(self) -> None:
        """Accessing a key should mark it as recently used."""
        cache = ChapterCache(maxsize=3)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to mark it as recently used
        _ = cache.get("key1")

        # Add key4 - should evict key2 (now oldest), not key1
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_update_order(self) -> None:
        """Updating a key should mark it as recently used."""
        cache = ChapterCache(maxsize=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Update key1 to mark it as recently used
        cache.set("key1", "updated1")

        # Add key4 - should evict key2 (now oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "updated1"  # Still present, updated
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_clear_cache(self) -> None:
        """Clear should remove all entries and reset stats."""
        cache = ChapterCache()

        # Add some data and access it
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        _ = cache.get("key1")
        _ = cache.get("missing")

        assert len(cache) == 2
        assert cache.stats()["hits"] == 1
        assert cache.stats()["misses"] == 1

        # Clear cache
        cache.clear()

        assert len(cache) == 0
        assert cache.get("key1") is None
        stats = cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 1  # From get above after clear

    def test_stats_calculation(self) -> None:
        """Stats should correctly calculate hit rate."""
        cache = ChapterCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # 2 hits, 1 miss = 66.67% hit rate
        _ = cache.get("key1")  # Hit
        _ = cache.get("key2")  # Hit
        _ = cache.get("key3")  # Miss

        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(66.67, abs=0.01)

    def test_stats_empty_cache(self) -> None:
        """Stats should handle empty cache correctly."""
        cache = ChapterCache()
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["maxsize"] == 10
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_len_operator(self) -> None:
        """len() should return number of cached items."""
        cache = ChapterCache(maxsize=5)

        assert len(cache) == 0

        cache.set("key1", "value1")
        assert len(cache) == 1

        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache) == 3

    def test_maxsize_one(self) -> None:
        """Cache with maxsize=1 should work correctly."""
        cache = ChapterCache(maxsize=1)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.set("key2", "value2")
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert len(cache) == 1

    def test_cache_key_format(self) -> None:
        """Cache should work with realistic key formats."""
        cache = ChapterCache()

        # Realistic cache keys: "filepath:chapter_index"
        cache.set("/path/to/book.epub:0", "<html>Chapter 0</html>")
        cache.set("/path/to/book.epub:5", "<html>Chapter 5</html>")
        cache.set("/different/book.epub:0", "<html>Different Chapter 0</html>")

        assert cache.get("/path/to/book.epub:0") == "<html>Chapter 0</html>"
        assert cache.get("/path/to/book.epub:5") == "<html>Chapter 5</html>"
        assert cache.get("/different/book.epub:0") == "<html>Different Chapter 0</html>"
        assert len(cache) == 3

    def test_large_html_content(self) -> None:
        """Cache should handle large HTML strings."""
        cache = ChapterCache()

        # Simulate large chapter with embedded images (base64)
        large_html = "<html><body>" + ("x" * 1000000) + "</body></html>"

        cache.set("large_chapter", large_html)
        result = cache.get("large_chapter")

        assert result == large_html
        assert len(result) > 1000000

    def test_sequential_reading_pattern(self) -> None:
        """Cache should handle sequential reading efficiently."""
        cache = ChapterCache(maxsize=5)

        # Simulate reading chapters 0-9 sequentially
        for i in range(10):
            cache.set(f"book:chapter{i}", f"<html>Chapter {i}</html>")

        # Last 5 chapters should be cached
        assert cache.get("book:chapter0") is None  # Evicted
        assert cache.get("book:chapter4") is None  # Evicted
        assert cache.get("book:chapter5") == "<html>Chapter 5</html>"
        assert cache.get("book:chapter9") == "<html>Chapter 9</html>"
        assert len(cache) == 5

    def test_backward_navigation_pattern(self) -> None:
        """Cache should handle backward navigation efficiently."""
        cache = ChapterCache(maxsize=5)

        # Read chapters 0-4
        for i in range(5):
            cache.set(f"book:{i}", f"Chapter {i}")

        # Navigate backward (4, 3, 2)
        assert cache.get("book:4") == "Chapter 4"
        assert cache.get("book:3") == "Chapter 3"
        assert cache.get("book:2") == "Chapter 2"

        # All should still be cached (no evictions yet)
        assert len(cache) == 5
        stats = cache.stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 0
