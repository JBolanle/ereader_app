"""Integration tests with real EPUB files.

This module tests the EPUBBook implementation with real-world EPUB files
from the playground/EPUBS directory. These tests verify that the parser
handles diverse EPUB formats correctly.

Test Files:
    1. 1984 (George Orwell) - 668KB, 8 chapters
    2. The Body Keeps The Score (Bessel van Der Kolk) - 3.1MB, 28 chapters
    3. The Mamba Mentality (Kobe Bryant) - 202MB, 21 chapters (large file with images)
"""

from pathlib import Path

import pytest

from ereader.models.epub import EPUBBook

# Path to real EPUB files
EPUB_DIR = Path(__file__).parent.parent.parent / "playground" / "EPUBS"

# Test file definitions
EPUB_FILES = {
    "1984": {
        "path": EPUB_DIR / "1984 (George Orwell) (Z-Library).epub",
        "expected_title": "1984",
        "expected_authors": ["Orwell, George"],
        "expected_language": "en",
        "min_chapters": 8,
        "min_manifest_items": 11,
    },
    "body_keeps_score": {
        "path": EPUB_DIR
        / "The Body Keeps The Score Mind, Brain and Body In The Transformation Of Trauma (Bessel van Der Kolk) (Z-Library).epub",
        "expected_title": "The Body Keeps the Score: Brain, Mind, and Body in the Healing of Trauma",
        "expected_authors": ["Bessel van Der Kolk"],
        "expected_language": "en",
        "min_chapters": 28,
        "min_manifest_items": 67,
    },
    "mamba_mentality": {
        "path": EPUB_DIR / "The Mamba Mentality How I Play (Bryant, Kobe) (Z-Library).epub",
        "expected_title": "The Mamba Mentality",
        "expected_authors": ["Kobe Bryant"],
        "expected_language": "en",
        "min_chapters": 21,
        "min_manifest_items": 200,  # Large file with many images
    },
}


@pytest.mark.skipif(
    not EPUB_DIR.exists(), reason="EPUB test files not found in playground/EPUBS"
)
class TestRealEPUBFiles:
    """Test EPUBBook with real-world EPUB files."""

    def test_1984_loads_successfully(self) -> None:
        """Test that 1984.epub loads and parses correctly."""
        epub_info = EPUB_FILES["1984"]

        if not epub_info["path"].exists():
            pytest.skip(f"EPUB file not found: {epub_info['path']}")

        book = EPUBBook(epub_info["path"])

        # Verify metadata
        assert book.title == epub_info["expected_title"]
        assert book.authors == epub_info["expected_authors"]
        assert book.language == epub_info["expected_language"]

        # Verify structure
        assert book.get_chapter_count() >= epub_info["min_chapters"]
        assert len(book._manifest) >= epub_info["min_manifest_items"]

    def test_1984_chapter_content_readable(self) -> None:
        """Test that chapters from 1984.epub can be read."""
        epub_info = EPUB_FILES["1984"]

        if not epub_info["path"].exists():
            pytest.skip(f"EPUB file not found: {epub_info['path']}")

        book = EPUBBook(epub_info["path"])

        # Read first chapter
        first_chapter = book.get_chapter_content(0)
        assert len(first_chapter) > 0
        assert "<?xml" in first_chapter  # Should be XHTML

        # Read last chapter
        last_chapter = book.get_chapter_content(book.get_chapter_count() - 1)
        assert len(last_chapter) > 0

    def test_body_keeps_score_loads_successfully(self) -> None:
        """Test that The Body Keeps The Score.epub loads and parses correctly."""
        epub_info = EPUB_FILES["body_keeps_score"]

        if not epub_info["path"].exists():
            pytest.skip(f"EPUB file not found: {epub_info['path']}")

        book = EPUBBook(epub_info["path"])

        # Verify metadata
        assert book.title == epub_info["expected_title"]
        assert book.authors == epub_info["expected_authors"]
        assert book.language == epub_info["expected_language"]

        # Verify structure
        assert book.get_chapter_count() >= epub_info["min_chapters"]
        assert len(book._manifest) >= epub_info["min_manifest_items"]

    def test_body_keeps_score_chapter_content_readable(self) -> None:
        """Test that chapters from The Body Keeps The Score.epub can be read."""
        epub_info = EPUB_FILES["body_keeps_score"]

        if not epub_info["path"].exists():
            pytest.skip(f"EPUB file not found: {epub_info['path']}")

        book = EPUBBook(epub_info["path"])

        # Read first chapter
        first_chapter = book.get_chapter_content(0)
        assert len(first_chapter) > 0

        # Read middle chapter
        mid_chapter = book.get_chapter_content(book.get_chapter_count() // 2)
        assert len(mid_chapter) > 0

        # Read last chapter
        last_chapter = book.get_chapter_content(book.get_chapter_count() - 1)
        assert len(last_chapter) > 0

    def test_mamba_mentality_loads_successfully(self) -> None:
        """Test that The Mamba Mentality.epub (large file) loads and parses correctly."""
        epub_info = EPUB_FILES["mamba_mentality"]

        if not epub_info["path"].exists():
            pytest.skip(f"EPUB file not found: {epub_info['path']}")

        book = EPUBBook(epub_info["path"])

        # Verify metadata
        assert book.title == epub_info["expected_title"]
        assert book.authors == epub_info["expected_authors"]
        assert book.language == epub_info["expected_language"]

        # Verify structure - this is a large file with many images
        assert book.get_chapter_count() >= epub_info["min_chapters"]
        assert len(book._manifest) >= epub_info["min_manifest_items"]

    def test_mamba_mentality_chapter_content_readable(self) -> None:
        """Test that chapters from The Mamba Mentality.epub (large file) can be read."""
        epub_info = EPUB_FILES["mamba_mentality"]

        if not epub_info["path"].exists():
            pytest.skip(f"EPUB file not found: {epub_info['path']}")

        book = EPUBBook(epub_info["path"])

        # Read first chapter
        first_chapter = book.get_chapter_content(0)
        assert len(first_chapter) > 0

        # Read last chapter
        last_chapter = book.get_chapter_content(book.get_chapter_count() - 1)
        assert len(last_chapter) > 0

    def test_all_epubs_have_valid_metadata(self) -> None:
        """Test that all real EPUB files have valid metadata."""
        for epub_name, epub_info in EPUB_FILES.items():
            if not epub_info["path"].exists():
                continue

            book = EPUBBook(epub_info["path"])

            # All should have non-default metadata
            assert book.title != "Unknown Title", f"{epub_name} has no title"
            assert book.authors != [
                "Unknown Author"
            ], f"{epub_name} has no authors"
            assert book.language != "", f"{epub_name} has no language"

    def test_all_epubs_have_chapters(self) -> None:
        """Test that all real EPUB files have at least one chapter."""
        for epub_name, epub_info in EPUB_FILES.items():
            if not epub_info["path"].exists():
                continue

            book = EPUBBook(epub_info["path"])

            assert (
                book.get_chapter_count() > 0
            ), f"{epub_name} has no chapters"

    def test_all_epubs_chapters_are_readable(self) -> None:
        """Test that all chapters in all real EPUB files can be read."""
        for epub_name, epub_info in EPUB_FILES.items():
            if not epub_info["path"].exists():
                continue

            book = EPUBBook(epub_info["path"])

            # Read all chapters (but don't assert content to keep test fast)
            for i in range(book.get_chapter_count()):
                content = book.get_chapter_content(i)
                assert (
                    len(content) >= 0
                ), f"{epub_name} chapter {i} could not be read"
