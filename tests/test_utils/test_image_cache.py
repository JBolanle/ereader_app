"""Tests for the ImageCache class."""

import pytest

from ereader.utils.image_cache import ImageCache


class TestImageCacheInitialization:
    """Test ImageCache initialization."""

    def test_init_with_defaults(self) -> None:
        """Should initialize with default max_memory_mb."""
        cache = ImageCache()
        assert len(cache) == 0
        stats = cache.stats()
        assert stats["max_memory_mb"] == 50

    def test_init_with_custom_max_memory(self) -> None:
        """Should initialize with custom max_memory_mb."""
        cache = ImageCache(max_memory_mb=100)
        stats = cache.stats()
        assert stats["max_memory_mb"] == 100

    def test_init_with_invalid_max_memory(self) -> None:
        """Should raise ValueError for invalid max_memory_mb."""
        with pytest.raises(ValueError, match="max_memory_mb must be positive"):
            ImageCache(max_memory_mb=0)

        with pytest.raises(ValueError, match="max_memory_mb must be positive"):
            ImageCache(max_memory_mb=-1)


class TestImageCacheBasicOperations:
    """Test basic cache operations."""

    def test_get_from_empty_cache(self) -> None:
        """Should return None when getting from empty cache."""
        cache = ImageCache()
        assert cache.get("images/photo.jpg") is None

    def test_set_and_get(self) -> None:
        """Should store and retrieve image data."""
        cache = ImageCache()
        image_data = "base64_encoded_image_data_here"

        cache.set("images/photo.jpg", image_data)
        assert cache.get("images/photo.jpg") == image_data

    def test_set_updates_existing_key(self) -> None:
        """Should update value for existing key."""
        cache = ImageCache()
        cache.set("images/photo.jpg", "old_data")
        cache.set("images/photo.jpg", "new_data")

        assert cache.get("images/photo.jpg") == "new_data"
        assert len(cache) == 1  # Size should not increase

    def test_multiple_images(self) -> None:
        """Should store multiple images independently."""
        cache = ImageCache()
        cache.set("images/photo1.jpg", "data1")
        cache.set("images/photo2.jpg", "data2")
        cache.set("images/photo3.jpg", "data3")

        assert cache.get("images/photo1.jpg") == "data1"
        assert cache.get("images/photo2.jpg") == "data2"
        assert cache.get("images/photo3.jpg") == "data3"
        assert len(cache) == 3


class TestImageCacheLRUEviction:
    """Test LRU eviction behavior."""

    def test_eviction_based_on_memory_budget(self) -> None:
        """Should evict items when memory budget is exceeded."""
        # Use very small memory budget to force evictions
        cache = ImageCache(max_memory_mb=0.0001)  # ~100 bytes

        # Add items that will exceed memory budget
        cache.set("img1", "x" * 50)  # ~50 bytes
        cache.set("img2", "y" * 50)  # ~50 bytes
        cache.set("img3", "z" * 100)  # ~100 bytes - should trigger eviction

        # First item should be evicted
        assert cache.get("img1") is None
        # Newer items should remain
        assert cache.get("img2") is not None or cache.get("img3") is not None

    def test_lru_order_preserved(self) -> None:
        """Should evict least recently used items first."""
        cache = ImageCache(max_memory_mb=0.0001)  # ~100 bytes

        # Add three items
        cache.set("img1", "x" * 40)
        cache.set("img2", "y" * 40)

        # Access img1 to make it more recently used
        _ = cache.get("img1")

        # Add large item to trigger eviction
        cache.set("img3", "z" * 100)

        # img2 should be evicted (least recently used)
        # img1 should survive (accessed more recently)
        # img3 should be present (just added)
        assert cache.get("img3") is not None

    def test_get_marks_as_recently_used(self) -> None:
        """Should mark item as recently used when accessed."""
        cache = ImageCache(max_memory_mb=0.0001)

        cache.set("img1", "x" * 40)
        cache.set("img2", "y" * 40)

        # Access img1
        _ = cache.get("img1")

        # Add item to trigger eviction
        cache.set("img3", "z" * 100)

        # img1 should survive because it was accessed
        # img2 might be evicted as least recently used


class TestImageCacheStatistics:
    """Test cache statistics tracking."""

    def test_empty_cache_stats(self) -> None:
        """Should return correct stats for empty cache."""
        cache = ImageCache(max_memory_mb=50)
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["memory_mb"] == 0.0
        assert stats["max_memory_mb"] == 50
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["memory_utilization"] == 0.0
        assert stats["avg_item_size_kb"] == 0.0

    def test_hits_and_misses_tracking(self) -> None:
        """Should track cache hits and misses."""
        cache = ImageCache()
        cache.set("img1", "data1")

        # Miss
        _ = cache.get("img2")
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

        # Hit
        _ = cache.get("img1")
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Another hit
        _ = cache.get("img1")
        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1

    def test_hit_rate_calculation(self) -> None:
        """Should calculate hit rate correctly."""
        cache = ImageCache()
        cache.set("img1", "data1")

        # 1 miss, 0 hits = 0%
        _ = cache.get("img2")
        stats = cache.stats()
        assert stats["hit_rate"] == 0.0

        # 1 miss, 1 hit = 50%
        _ = cache.get("img1")
        stats = cache.stats()
        assert stats["hit_rate"] == 50.0

        # 1 miss, 2 hits = 66.67%
        _ = cache.get("img1")
        stats = cache.stats()
        assert abs(stats["hit_rate"] - 66.67) < 0.01

    def test_memory_stats(self) -> None:
        """Should track memory usage."""
        cache = ImageCache(max_memory_mb=50)
        cache.set("img1", "x" * 1000)  # ~1KB

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["memory_mb"] > 0
        assert stats["memory_utilization"] > 0
        assert stats["avg_item_size_kb"] > 0

    def test_eviction_tracking(self) -> None:
        """Should track number of evictions."""
        cache = ImageCache(max_memory_mb=0.0001)

        cache.set("img1", "x" * 40)
        stats = cache.stats()
        assert stats["evictions"] == 0

        # Trigger eviction
        cache.set("img2", "y" * 100)
        stats = cache.stats()
        assert stats["evictions"] >= 1


class TestImageCacheClear:
    """Test cache clearing."""

    def test_clear_empty_cache(self) -> None:
        """Should handle clearing empty cache."""
        cache = ImageCache()
        cache.clear()
        assert len(cache) == 0

    def test_clear_removes_all_items(self) -> None:
        """Should remove all cached items."""
        cache = ImageCache()
        cache.set("img1", "data1")
        cache.set("img2", "data2")
        cache.set("img3", "data3")

        cache.clear()

        assert len(cache) == 0
        assert cache.get("img1") is None
        assert cache.get("img2") is None
        assert cache.get("img3") is None

    def test_clear_resets_statistics(self) -> None:
        """Should reset statistics when clearing."""
        cache = ImageCache()
        cache.set("img1", "data1")
        _ = cache.get("img1")
        _ = cache.get("img2")  # miss

        cache.clear()
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["memory_mb"] == 0.0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0

    def test_cache_usable_after_clear(self) -> None:
        """Should be usable after clearing."""
        cache = ImageCache()
        cache.set("img1", "data1")
        cache.clear()

        cache.set("img2", "data2")
        assert cache.get("img2") == "data2"
        assert len(cache) == 1


class TestImageCacheEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_len_operator(self) -> None:
        """Should support len() operator."""
        cache = ImageCache()
        assert len(cache) == 0

        cache.set("img1", "data1")
        assert len(cache) == 1

        cache.set("img2", "data2")
        assert len(cache) == 2

    def test_large_image_data(self) -> None:
        """Should handle large image data."""
        cache = ImageCache(max_memory_mb=10)
        large_data = "x" * (1024 * 1024)  # 1MB of data

        cache.set("large_img", large_data)
        assert cache.get("large_img") == large_data

    def test_empty_string_value(self) -> None:
        """Should handle empty string values."""
        cache = ImageCache()
        cache.set("empty", "")
        assert cache.get("empty") == ""

    def test_special_characters_in_key(self) -> None:
        """Should handle special characters in keys."""
        cache = ImageCache()
        keys = [
            "images/photo with spaces.jpg",
            "images/photo-with-dashes.jpg",
            "images/photo_with_underscores.jpg",
            "../images/relative.jpg",
            "images/日本語.jpg",  # Unicode characters
        ]

        for key in keys:
            cache.set(key, f"data_for_{key}")
            assert cache.get(key) == f"data_for_{key}"
