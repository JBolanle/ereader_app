"""Tests for the CacheManager class."""

from unittest.mock import MagicMock, patch

import pytest

from ereader.utils.cache_manager import CacheManager


class TestCacheManagerInitialization:
    """Test CacheManager initialization."""

    def test_init_with_defaults(self) -> None:
        """Should initialize with default parameters."""
        manager = CacheManager()

        # Check that all caches are initialized
        assert manager.rendered_chapters is not None
        assert manager.raw_chapters is not None
        assert manager.images is not None
        assert manager.memory_monitor is not None

        # Check cache configurations
        rendered_stats = manager.rendered_chapters.stats()
        assert rendered_stats["maxsize"] == 10

        raw_stats = manager.raw_chapters.stats()
        assert raw_stats["maxsize"] == 20

        image_stats = manager.images.stats()
        assert image_stats["max_memory_mb"] == 50

        memory_stats = manager.memory_monitor.get_stats()
        assert memory_stats["threshold_mb"] == 150

    def test_init_with_custom_parameters(self) -> None:
        """Should initialize with custom parameters."""
        manager = CacheManager(
            rendered_maxsize=5,
            raw_maxsize=10,
            image_max_memory_mb=25,
            total_memory_threshold_mb=100,
        )

        rendered_stats = manager.rendered_chapters.stats()
        assert rendered_stats["maxsize"] == 5

        raw_stats = manager.raw_chapters.stats()
        assert raw_stats["maxsize"] == 10

        image_stats = manager.images.stats()
        assert image_stats["max_memory_mb"] == 25

        memory_stats = manager.memory_monitor.get_stats()
        assert memory_stats["threshold_mb"] == 100

    def test_init_with_invalid_rendered_maxsize(self) -> None:
        """Should raise ValueError for invalid rendered_maxsize."""
        with pytest.raises(ValueError, match="rendered_maxsize must be at least 1"):
            CacheManager(rendered_maxsize=0)

    def test_init_with_invalid_raw_maxsize(self) -> None:
        """Should raise ValueError for invalid raw_maxsize."""
        with pytest.raises(ValueError, match="raw_maxsize must be at least 1"):
            CacheManager(raw_maxsize=0)

    def test_init_with_invalid_image_max_memory(self) -> None:
        """Should raise ValueError for invalid image_max_memory_mb."""
        with pytest.raises(ValueError, match="image_max_memory_mb must be positive"):
            CacheManager(image_max_memory_mb=0)

    def test_init_with_invalid_total_memory_threshold(self) -> None:
        """Should raise ValueError for invalid total_memory_threshold_mb."""
        with pytest.raises(
            ValueError, match="total_memory_threshold_mb must be positive"
        ):
            CacheManager(total_memory_threshold_mb=0)


class TestCacheManagerBasicOperations:
    """Test basic cache manager operations."""

    def test_clear_all_empty_caches(self) -> None:
        """Should handle clearing empty caches."""
        manager = CacheManager()
        manager.clear_all()

        # Verify all caches are empty
        assert len(manager.rendered_chapters) == 0
        assert len(manager.raw_chapters) == 0
        assert len(manager.images) == 0

    def test_clear_all_with_data(self) -> None:
        """Should clear all caches with data."""
        manager = CacheManager()

        # Add data to all caches
        manager.rendered_chapters.set("book:0", "<html>rendered</html>")
        manager.raw_chapters.set("book:0", "<body>raw</body>")
        manager.images.set("images/photo.jpg", "base64data")

        # Verify data is present
        assert len(manager.rendered_chapters) == 1
        assert len(manager.raw_chapters) == 1
        assert len(manager.images) == 1

        # Clear all
        manager.clear_all()

        # Verify all caches are empty
        assert len(manager.rendered_chapters) == 0
        assert len(manager.raw_chapters) == 0
        assert len(manager.images) == 0

    def test_rendered_chapters_cache_operations(self) -> None:
        """Should allow operations on rendered chapters cache."""
        manager = CacheManager()

        manager.rendered_chapters.set("book:0", "<html>chapter 0</html>")
        manager.rendered_chapters.set("book:1", "<html>chapter 1</html>")

        assert manager.rendered_chapters.get("book:0") == "<html>chapter 0</html>"
        assert manager.rendered_chapters.get("book:1") == "<html>chapter 1</html>"
        assert len(manager.rendered_chapters) == 2

    def test_raw_chapters_cache_operations(self) -> None:
        """Should allow operations on raw chapters cache."""
        manager = CacheManager()

        manager.raw_chapters.set("book:0", "<body>raw 0</body>")
        manager.raw_chapters.set("book:1", "<body>raw 1</body>")

        assert manager.raw_chapters.get("book:0") == "<body>raw 0</body>"
        assert manager.raw_chapters.get("book:1") == "<body>raw 1</body>"
        assert len(manager.raw_chapters) == 2

    def test_images_cache_operations(self) -> None:
        """Should allow operations on images cache."""
        manager = CacheManager()

        manager.images.set("images/photo1.jpg", "data1")
        manager.images.set("images/photo2.jpg", "data2")

        assert manager.images.get("images/photo1.jpg") == "data1"
        assert manager.images.get("images/photo2.jpg") == "data2"
        assert len(manager.images) == 2


class TestCacheManagerStatistics:
    """Test cache manager statistics."""

    def test_combined_stats_empty_caches(self) -> None:
        """Should return correct stats for empty caches."""
        manager = CacheManager()
        stats = manager.get_combined_stats()

        assert stats["total_memory_mb"] == 0.0
        assert stats["total_items"] == 0

        assert stats["rendered_stats"]["size"] == 0
        assert stats["raw_stats"]["size"] == 0
        assert stats["image_stats"]["size"] == 0

    def test_combined_stats_with_data(self) -> None:
        """Should aggregate stats from all caches."""
        manager = CacheManager()

        # Add data to all caches
        manager.rendered_chapters.set("book:0", "<html>rendered</html>")
        manager.raw_chapters.set("book:0", "<body>raw</body>")
        manager.raw_chapters.set("book:1", "<body>raw2</body>")
        manager.images.set("images/photo.jpg", "base64data")

        stats = manager.get_combined_stats()

        # Check total items
        assert stats["total_items"] == 4  # 1 rendered + 2 raw + 1 image

        # Check individual cache sizes
        assert stats["rendered_stats"]["size"] == 1
        assert stats["raw_stats"]["size"] == 2
        assert stats["image_stats"]["size"] == 1

        # Check memory is tracked
        assert stats["total_memory_mb"] > 0

    def test_combined_stats_includes_all_cache_stats(self) -> None:
        """Should include stats from all cache layers."""
        manager = CacheManager()

        manager.rendered_chapters.set("book:0", "data")
        _ = manager.rendered_chapters.get("book:0")  # Hit

        stats = manager.get_combined_stats()

        # Check that individual cache stats are included
        assert "rendered_stats" in stats
        assert "raw_stats" in stats
        assert "image_stats" in stats
        assert "memory_stats" in stats

        # Check that rendered cache stats are correct
        assert stats["rendered_stats"]["hits"] == 1
        assert stats["rendered_stats"]["size"] == 1

    def test_combined_stats_memory_calculation(self) -> None:
        """Should calculate total memory correctly."""
        manager = CacheManager()

        # Add data to caches
        manager.rendered_chapters.set("book:0", "x" * 1000)
        manager.raw_chapters.set("book:0", "y" * 1000)
        manager.images.set("img1", "z" * 1000)

        stats = manager.get_combined_stats()

        # Total memory should be sum of all caches
        expected_total = (
            stats["rendered_stats"]["estimated_memory_mb"]
            + stats["raw_stats"]["estimated_memory_mb"]
            + stats["image_stats"]["memory_mb"]
        )

        assert abs(stats["total_memory_mb"] - expected_total) < 0.001


class TestCacheManagerMemoryMonitoring:
    """Test memory monitoring functionality."""

    @patch("ereader.utils.memory_monitor.psutil.Process")
    def test_check_memory_threshold_below(self, mock_process_class: MagicMock) -> None:
        """Should return False when below threshold."""
        # Mock memory usage below threshold
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        manager = CacheManager(total_memory_threshold_mb=150)
        assert manager.check_memory_threshold() is False

    @patch("ereader.utils.memory_monitor.psutil.Process")
    def test_check_memory_threshold_above(self, mock_process_class: MagicMock) -> None:
        """Should return True when above threshold."""
        # Mock memory usage above threshold
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 200 * 1024 * 1024  # 200 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        manager = CacheManager(total_memory_threshold_mb=150)
        # First call should return True and log warning
        assert manager.check_memory_threshold() is True


class TestCacheManagerLogging:
    """Test logging functionality."""

    def test_log_stats_with_empty_caches(self) -> None:
        """Should log stats for empty caches without error."""
        manager = CacheManager()
        # Should not raise any exceptions
        manager.log_stats()

    def test_log_stats_with_data(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should log cache statistics."""
        manager = CacheManager()

        # Add some data
        manager.rendered_chapters.set("book:0", "rendered")
        manager.raw_chapters.set("book:0", "raw")
        manager.images.set("img1", "data")

        # Log stats
        with caplog.at_level("DEBUG"):
            manager.log_stats()

        # Check that stats were logged (looking for any cache-related log)
        # The exact log format may vary, so we just check something was logged
        assert len(caplog.records) > 0


class TestCacheManagerIntegration:
    """Test integration between cache layers."""

    def test_independent_cache_layers(self) -> None:
        """Should maintain independent cache layers."""
        manager = CacheManager()

        # Same key in different caches should store different data
        manager.rendered_chapters.set("book:0", "rendered data")
        manager.raw_chapters.set("book:0", "raw data")

        assert manager.rendered_chapters.get("book:0") == "rendered data"
        assert manager.raw_chapters.get("book:0") == "raw data"

    def test_typical_workflow(self) -> None:
        """Should support typical caching workflow."""
        manager = CacheManager()

        # Simulate loading a chapter for the first time
        # 1. Check rendered cache (miss)
        assert manager.rendered_chapters.get("book:0") is None

        # 2. Check raw cache (miss)
        assert manager.raw_chapters.get("book:0") is None

        # 3. Load raw from book and cache it
        raw_content = "<body>Chapter content</body>"
        manager.raw_chapters.set("book:0", raw_content)

        # 4. Render and cache rendered content
        rendered_content = "<html><body>Chapter content</body></html>"
        manager.rendered_chapters.set("book:0", rendered_content)

        # 5. Load images and cache them
        manager.images.set("images/photo.jpg", "base64data")

        # Verify all caches have data
        assert manager.rendered_chapters.get("book:0") == rendered_content
        assert manager.raw_chapters.get("book:0") == raw_content
        assert manager.images.get("images/photo.jpg") == "base64data"

        # Check stats
        stats = manager.get_combined_stats()
        assert stats["total_items"] == 3

    def test_clear_all_resets_all_layers(self) -> None:
        """Should reset all cache layers and statistics."""
        manager = CacheManager()

        # Populate all caches
        manager.rendered_chapters.set("book:0", "rendered")
        manager.raw_chapters.set("book:0", "raw")
        manager.images.set("img1", "data")

        # Generate some cache hits
        _ = manager.rendered_chapters.get("book:0")
        _ = manager.raw_chapters.get("book:0")
        _ = manager.images.get("img1")

        # Clear all
        manager.clear_all()

        # Verify everything is reset
        stats = manager.get_combined_stats()
        assert stats["total_items"] == 0
        assert stats["total_memory_mb"] == 0.0

        # Verify caches are usable after clear
        manager.rendered_chapters.set("book:1", "new data")
        assert manager.rendered_chapters.get("book:1") == "new data"
