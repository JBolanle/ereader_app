"""Tests for caching utilities."""

import time

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
        assert stats["estimated_memory_mb"] == 0.0
        assert stats["avg_item_size_kb"] == 0.0
        assert stats["time_since_last_eviction"] is None
        assert stats["cache_age_seconds"] >= 0.0

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


class TestChapterCacheEnhancedStats:
    """Test suite for enhanced cache statistics (Phase 2)."""

    def test_stats_memory_estimation(self) -> None:
        """Stats should estimate memory usage."""
        cache = ChapterCache()

        # Add some content
        cache.set("key1", "<html>Small content</html>")
        cache.set("key2", "<html>More content here</html>")

        stats = cache.stats()

        # Memory should be non-zero
        assert stats["estimated_memory_mb"] > 0.0
        # Average item size should be non-zero
        assert stats["avg_item_size_kb"] > 0.0

    def test_stats_memory_grows_with_content(self) -> None:
        """Stats should show memory growing as content is added."""
        cache = ChapterCache()

        # Add small content
        cache.set("small", "x" * 100)
        small_stats = cache.stats()

        # Add large content
        cache.set("large", "x" * 10000)
        large_stats = cache.stats()

        # Memory should increase
        assert large_stats["estimated_memory_mb"] > small_stats["estimated_memory_mb"]
        assert large_stats["avg_item_size_kb"] > small_stats["avg_item_size_kb"]

    def test_stats_time_since_last_eviction_none(self) -> None:
        """Stats should show None for time_since_last_eviction when no evictions."""
        cache = ChapterCache(maxsize=5)

        # Add items without triggering eviction
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.stats()
        assert stats["time_since_last_eviction"] is None

    def test_stats_time_since_last_eviction_set(self) -> None:
        """Stats should track time since last eviction."""
        cache = ChapterCache(maxsize=2)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Trigger eviction
        cache.set("key3", "value3")

        stats = cache.stats()
        assert stats["time_since_last_eviction"] is not None
        assert stats["time_since_last_eviction"] >= 0.0

    def test_stats_time_since_last_eviction_updates(self) -> None:
        """Stats should update time_since_last_eviction with each eviction."""
        cache = ChapterCache(maxsize=2)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # First eviction
        cache.set("key3", "value3")
        time.sleep(0.05)  # Wait a bit

        # Second eviction
        cache.set("key4", "value4")

        stats = cache.stats()
        # Time should be small (recent eviction)
        assert stats["time_since_last_eviction"] < 0.1

    def test_stats_cache_age_seconds(self) -> None:
        """Stats should track cache age since creation."""
        cache = ChapterCache()

        # Check immediately after creation
        stats1 = cache.stats()
        assert stats1["cache_age_seconds"] < 0.1

        # Wait and check again
        time.sleep(0.1)
        stats2 = cache.stats()
        assert stats2["cache_age_seconds"] >= 0.1
        assert stats2["cache_age_seconds"] > stats1["cache_age_seconds"]

    def test_stats_all_fields_present(self) -> None:
        """Stats should include all expected fields."""
        cache = ChapterCache()
        cache.set("key1", "value1")

        stats = cache.stats()

        # Original fields
        assert "size" in stats
        assert "maxsize" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

        # New Phase 2 fields
        assert "estimated_memory_mb" in stats
        assert "avg_item_size_kb" in stats
        assert "time_since_last_eviction" in stats
        assert "cache_age_seconds" in stats

    def test_stats_avg_item_size_calculation(self) -> None:
        """Stats should correctly calculate average item size."""
        cache = ChapterCache()

        # Add items of similar size
        cache.set("key1", "x" * 1000)
        cache.set("key2", "y" * 1000)

        stats = cache.stats()

        # Average should be approximately 1KB (plus some overhead)
        # sys.getsizeof includes string overhead, so it will be > 1KB
        assert stats["avg_item_size_kb"] > 1.0
        assert stats["avg_item_size_kb"] < 10.0  # Reasonable upper bound
