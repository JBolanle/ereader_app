"""Tests for EPUBBook class."""

import zipfile
from pathlib import Path

import pytest

from ereader.exceptions import CorruptedEPUBError, InvalidEPUBError
from ereader.models.epub import EPUBBook


class TestEPUBBookInit:
    """Test EPUBBook initialization and validation."""

    def test_init_with_valid_epub(self, tmp_path: Path) -> None:
        """Test initialization with a valid EPUB file (ZIP archive)."""
        # Create a minimal valid EPUB (ZIP with container.xml and content.opf)
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        book = EPUBBook(epub_file)
        assert book.filepath == epub_file

    def test_init_with_string_path(self, tmp_path: Path) -> None:
        """Test initialization with a string path (not Path object)."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        # Pass string instead of Path object
        book = EPUBBook(str(epub_file))
        assert book.filepath == epub_file

    def test_init_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test initialization with a file that doesn't exist."""
        nonexistent_file = tmp_path / "does_not_exist.epub"

        with pytest.raises(FileNotFoundError) as exc_info:
            EPUBBook(nonexistent_file)

        assert "not found" in str(exc_info.value).lower()

    def test_init_with_directory(self, tmp_path: Path) -> None:
        """Test initialization with a directory path instead of a file."""
        directory = tmp_path / "not_a_file"
        directory.mkdir()

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(directory)

        assert "not a file" in str(exc_info.value).lower()

    def test_init_with_non_zip_file(self, tmp_path: Path) -> None:
        """Test initialization with a non-ZIP file."""
        text_file = tmp_path / "not_an_epub.epub"
        text_file.write_text("This is just a text file, not a ZIP archive")

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(text_file)

        assert "not a valid" in str(exc_info.value).lower()
        assert "zip" in str(exc_info.value).lower()

    def test_init_with_empty_file(self, tmp_path: Path) -> None:
        """Test initialization with an empty file."""
        empty_file = tmp_path / "empty.epub"
        empty_file.touch()

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(empty_file)

        assert "not a valid" in str(exc_info.value).lower()

    def test_init_with_special_characters_in_path(self, tmp_path: Path) -> None:
        """Test initialization with special characters in the file path."""
        epub_file = tmp_path / "test book (2023) - author's name.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        book = EPUBBook(epub_file)
        assert book.filepath == epub_file

    def test_init_with_unicode_in_path(self, tmp_path: Path) -> None:
        """Test initialization with unicode characters in the file path."""
        epub_file = tmp_path / "书名-作者.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        book = EPUBBook(epub_file)
        assert book.filepath == epub_file

    def test_init_with_zip_without_container_xml(self, tmp_path: Path) -> None:
        """Test initialization with a ZIP file missing META-INF/container.xml."""
        zip_file = tmp_path / "not_an_epub.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("some_file.txt", "random content")

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(zip_file)

        assert "container.xml" in str(exc_info.value).lower()


class TestEPUBMetadataExtraction:
    """Test metadata extraction from EPUB files."""

    def _create_epub_with_metadata(
        self,
        tmp_path: Path,
        title: str | None = None,
        authors: list[str] | None = None,
        language: str | None = None,
        manifest: list[tuple[str, str, str]] | None = None,
        spine: list[str] | None = None,
    ) -> Path:
        """Helper to create a minimal EPUB with specified metadata.

        Args:
            tmp_path: Temporary directory from pytest fixture.
            title: Book title (omit to test missing title).
            authors: List of authors (omit to test missing authors).
            language: Language code (omit to test missing language).
            manifest: List of (id, href, media-type) tuples (omit for minimal manifest).
            spine: List of item IDs for spine (omit for minimal spine).

        Returns:
            Path to the created EPUB file.
        """
        epub_file = tmp_path / "test.epub"

        # Create container.xml pointing to content.opf
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        # Build OPF XML with metadata
        opf_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">',
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
        ]

        if title:
            opf_parts.append(f"<dc:title>{title}</dc:title>")

        if authors:
            for author in authors:
                opf_parts.append(f"<dc:creator>{author}</dc:creator>")

        if language:
            opf_parts.append(f"<dc:language>{language}</dc:language>")

        opf_parts.append("</metadata>")

        # Add manifest - use provided or create minimal default
        if manifest is not None:
            opf_parts.append("<manifest>")
            for item_id, href, media_type in manifest:
                opf_parts.append(
                    f'<item id="{item_id}" href="{href}" media-type="{media_type}"/>'
                )
            opf_parts.append("</manifest>")
        else:
            # Add minimal manifest for tests that don't specify one
            opf_parts.append("<manifest>")
            opf_parts.append(
                '<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>'
            )
            opf_parts.append("</manifest>")

        # Add spine - use provided or create minimal default
        if spine is not None:
            opf_parts.append('<spine toc="ncx">')
            for idref in spine:
                opf_parts.append(f'<itemref idref="{idref}"/>')
            opf_parts.append("</spine>")
        else:
            # Add minimal spine for tests that don't specify one
            opf_parts.append('<spine toc="ncx">')
            opf_parts.append('<itemref idref="ch1"/>')
            opf_parts.append("</spine>")

        opf_parts.append("</package>")
        opf_xml = "\n".join(opf_parts)

        # Create the EPUB ZIP file
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        return epub_file

    def test_extract_complete_metadata(self, tmp_path: Path) -> None:
        """Test extraction of complete metadata (title, authors, language)."""
        epub_file = self._create_epub_with_metadata(
            tmp_path,
            title="The Great Gatsby",
            authors=["F. Scott Fitzgerald"],
            language="en",
        )

        book = EPUBBook(epub_file)

        assert book.title == "The Great Gatsby"
        assert book.authors == ["F. Scott Fitzgerald"]
        assert book.language == "en"

    def test_extract_multiple_authors(self, tmp_path: Path) -> None:
        """Test extraction of multiple authors."""
        epub_file = self._create_epub_with_metadata(
            tmp_path,
            title="Good Omens",
            authors=["Terry Pratchett", "Neil Gaiman"],
            language="en",
        )

        book = EPUBBook(epub_file)

        assert book.title == "Good Omens"
        assert book.authors == ["Terry Pratchett", "Neil Gaiman"]
        assert len(book.authors) == 2

    def test_missing_title_uses_default(self, tmp_path: Path) -> None:
        """Test that missing title defaults to 'Unknown Title'."""
        epub_file = self._create_epub_with_metadata(
            tmp_path, authors=["Some Author"], language="en"
        )

        book = EPUBBook(epub_file)

        assert book.title == "Unknown Title"
        assert book.authors == ["Some Author"]

    def test_missing_authors_uses_default(self, tmp_path: Path) -> None:
        """Test that missing authors defaults to ['Unknown Author']."""
        epub_file = self._create_epub_with_metadata(
            tmp_path, title="Test Book", language="en"
        )

        book = EPUBBook(epub_file)

        assert book.title == "Test Book"
        assert book.authors == ["Unknown Author"]

    def test_missing_language_uses_default(self, tmp_path: Path) -> None:
        """Test that missing language defaults to 'en'."""
        epub_file = self._create_epub_with_metadata(
            tmp_path, title="Test Book", authors=["Test Author"]
        )

        book = EPUBBook(epub_file)

        assert book.title == "Test Book"
        assert book.language == "en"

    def test_all_metadata_missing_uses_defaults(self, tmp_path: Path) -> None:
        """Test that all missing metadata defaults to appropriate values."""
        epub_file = self._create_epub_with_metadata(tmp_path)

        book = EPUBBook(epub_file)

        assert book.title == "Unknown Title"
        assert book.authors == ["Unknown Author"]
        assert book.language == "en"

    def test_metadata_with_whitespace(self, tmp_path: Path) -> None:
        """Test that metadata with whitespace is properly trimmed."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>  Whitespace Title  </dc:title>
<dc:creator>  Whitespace Author  </dc:creator>
<dc:language>  en  </dc:language>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        book = EPUBBook(epub_file)

        assert book.title == "Whitespace Title"
        assert book.authors == ["Whitespace Author"]
        assert book.language == "en"

    def test_malformed_opf_xml_raises_error(self, tmp_path: Path) -> None:
        """Test that malformed OPF XML raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        # Malformed XML - missing closing tag
        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Title
</metadata>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "malformed" in str(exc_info.value).lower()

    def test_malformed_container_xml_raises_error(self, tmp_path: Path) -> None:
        """Test that malformed container.xml raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        # Malformed XML - missing closing tag
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
</container>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "malformed" in str(exc_info.value).lower()

    def test_missing_rootfile_element_raises_error(self, tmp_path: Path) -> None:
        """Test that missing rootfile element raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        # Container.xml without rootfile element
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
  </rootfiles>
</container>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "rootfile" in str(exc_info.value).lower()

    def test_missing_full_path_attribute_raises_error(self, tmp_path: Path) -> None:
        """Test that missing full-path attribute raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        # Container.xml with rootfile but no full-path attribute
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "full-path" in str(exc_info.value).lower()

    def test_missing_opf_file_raises_error(self, tmp_path: Path) -> None:
        """Test that missing OPF file raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        # Container.xml points to non-existent OPF file
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            # Note: NOT writing OEBPS/content.opf

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "not found" in str(exc_info.value).lower()


class TestEPUBManifestAndSpineParsing:
    """Test manifest and spine parsing from EPUB files."""

    def _create_epub_with_structure(
        self,
        tmp_path: Path,
        manifest: list[tuple[str, str, str]] | None = None,
        spine: list[str] | None = None,
    ) -> Path:
        """Helper to create an EPUB with manifest and spine structure.

        Args:
            tmp_path: Temporary directory from pytest fixture.
            manifest: List of (id, href, media-type) tuples.
            spine: List of item IDs for spine.

        Returns:
            Path to the created EPUB file.
        """
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">',
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
            "<dc:title>Test Book</dc:title>",
            "</metadata>",
        ]

        # Add manifest
        if manifest is not None:
            opf_parts.append("<manifest>")
            for item_id, href, media_type in manifest:
                opf_parts.append(
                    f'<item id="{item_id}" href="{href}" media-type="{media_type}"/>'
                )
            opf_parts.append("</manifest>")

        # Add spine
        if spine is not None:
            opf_parts.append('<spine toc="ncx">')
            for idref in spine:
                opf_parts.append(f'<itemref idref="{idref}"/>')
            opf_parts.append("</spine>")

        opf_parts.append("</package>")
        opf_xml = "\n".join(opf_parts)

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        return epub_file

    def test_parse_manifest_with_multiple_items(self, tmp_path: Path) -> None:
        """Test parsing manifest with multiple items of different types."""
        manifest = [
            ("ch1", "chapter1.xhtml", "application/xhtml+xml"),
            ("ch2", "chapter2.xhtml", "application/xhtml+xml"),
            ("cover", "cover.jpg", "image/jpeg"),
            ("css", "style.css", "text/css"),
            ("ncx", "toc.ncx", "application/x-dtbncx+xml"),
        ]
        spine = ["ch1", "ch2"]

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)
        book = EPUBBook(epub_file)

        # Check manifest was parsed correctly
        assert hasattr(book, "_manifest")
        assert len(book._manifest) == 5
        assert book._manifest["ch1"] == "chapter1.xhtml"
        assert book._manifest["ch2"] == "chapter2.xhtml"
        assert book._manifest["cover"] == "cover.jpg"
        assert book._manifest["css"] == "style.css"
        assert book._manifest["ncx"] == "toc.ncx"

    def test_parse_spine_in_correct_order(self, tmp_path: Path) -> None:
        """Test that spine preserves reading order."""
        manifest = [
            ("ch1", "chapter1.xhtml", "application/xhtml+xml"),
            ("ch2", "chapter2.xhtml", "application/xhtml+xml"),
            ("ch3", "chapter3.xhtml", "application/xhtml+xml"),
        ]
        spine = ["ch1", "ch2", "ch3"]

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)
        book = EPUBBook(epub_file)

        # Check spine was parsed in correct order
        assert hasattr(book, "_spine")
        assert len(book._spine) == 3
        assert book._spine[0] == "ch1"
        assert book._spine[1] == "ch2"
        assert book._spine[2] == "ch3"

    def test_manifest_maps_id_to_href_correctly(self, tmp_path: Path) -> None:
        """Test that manifest correctly maps item IDs to file paths."""
        manifest = [
            ("item1", "content/chapter_1.html", "application/xhtml+xml"),
            ("item2", "content/chapter_2.html", "application/xhtml+xml"),
        ]
        spine = ["item1", "item2"]

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)
        book = EPUBBook(epub_file)

        # Verify ID to href mapping
        assert book._manifest["item1"] == "content/chapter_1.html"
        assert book._manifest["item2"] == "content/chapter_2.html"

    def test_spine_references_manifest_items(self, tmp_path: Path) -> None:
        """Test that all spine items reference valid manifest items."""
        manifest = [
            ("ch1", "chapter1.xhtml", "application/xhtml+xml"),
            ("ch2", "chapter2.xhtml", "application/xhtml+xml"),
            ("img1", "image.jpg", "image/jpeg"),  # Not in spine
        ]
        spine = ["ch1", "ch2"]

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)
        book = EPUBBook(epub_file)

        # All spine items should be in manifest
        for spine_id in book._spine:
            assert spine_id in book._manifest

        # Manifest can have items not in spine (like images)
        assert "img1" in book._manifest
        assert "img1" not in book._spine

    def test_missing_manifest_raises_error(self, tmp_path: Path) -> None:
        """Test that missing manifest element raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        # OPF without manifest
        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "manifest" in str(exc_info.value).lower()

    def test_missing_spine_raises_error(self, tmp_path: Path) -> None:
        """Test that missing spine element raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        # OPF without spine
        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
</package>"""

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "spine" in str(exc_info.value).lower()

    def test_empty_spine_raises_error(self, tmp_path: Path) -> None:
        """Test that empty spine (no chapters) raises CorruptedEPUBError."""
        manifest = [
            ("css", "style.css", "text/css"),
            ("cover", "cover.jpg", "image/jpeg"),
        ]
        spine = []  # Empty spine

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            EPUBBook(epub_file)

        assert "spine" in str(exc_info.value).lower()

    def test_spine_with_invalid_idref_skips_item(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that spine with invalid idref logs warning and skips that item."""
        manifest = [
            ("ch1", "chapter1.xhtml", "application/xhtml+xml"),
            ("ch3", "chapter3.xhtml", "application/xhtml+xml"),
        ]
        spine = ["ch1", "ch2", "ch3"]  # ch2 doesn't exist in manifest

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)

        import logging

        with caplog.at_level(logging.WARNING):
            book = EPUBBook(epub_file)

        # Should have logged a warning about ch2
        assert any("ch2" in record.message for record in caplog.records)
        assert any("non-existent" in record.message.lower() for record in caplog.records)

        # Spine should only contain valid items
        assert len(book._spine) == 2
        assert book._spine == ["ch1", "ch3"]
        assert "ch2" not in book._spine

    def test_manifest_with_different_media_types(self, tmp_path: Path) -> None:
        """Test that manifest parses items with various media types."""
        manifest = [
            ("ch1", "chapter1.xhtml", "application/xhtml+xml"),
            ("ch2", "chapter2.html", "text/html"),
            ("img1", "cover.jpg", "image/jpeg"),
            ("img2", "diagram.png", "image/png"),
            ("css1", "style.css", "text/css"),
            ("font1", "font.ttf", "application/font-sfnt"),
            ("ncx", "toc.ncx", "application/x-dtbncx+xml"),
        ]
        spine = ["ch1", "ch2"]

        epub_file = self._create_epub_with_structure(tmp_path, manifest, spine)
        book = EPUBBook(epub_file)

        # All items should be in manifest regardless of media type
        assert len(book._manifest) == 7
        assert all(item_id in book._manifest for item_id, _, _ in manifest)


class TestEPUBChapterContent:
    """Test reading chapter content from EPUB files."""

    def _create_epub_with_content(
        self,
        tmp_path: Path,
        chapters: dict[str, str] | None = None,
    ) -> Path:
        """Helper to create an EPUB with chapter content.

        Args:
            tmp_path: Temporary directory from pytest fixture.
            chapters: Dict mapping chapter IDs to their content (XHTML/HTML strings).

        Returns:
            Path to the created EPUB file.
        """
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        # Build OPF with manifest and spine from chapters
        opf_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">',
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
            "<dc:title>Test Book</dc:title>",
            "</metadata>",
            "<manifest>",
        ]

        if chapters:
            for chapter_id in chapters:
                opf_parts.append(
                    f'<item id="{chapter_id}" href="{chapter_id}.xhtml" '
                    'media-type="application/xhtml+xml"/>'
                )

        opf_parts.append("</manifest>")
        opf_parts.append('<spine toc="ncx">')

        if chapters:
            for chapter_id in chapters:
                opf_parts.append(f'<itemref idref="{chapter_id}"/>')

        opf_parts.append("</spine>")
        opf_parts.append("</package>")

        opf_xml = "\n".join(opf_parts)

        # Create the EPUB ZIP file
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)

            # Write chapter content files
            if chapters:
                for chapter_id, content in chapters.items():
                    zf.writestr(f"OEBPS/{chapter_id}.xhtml", content)

        return epub_file

    def test_get_chapter_count(self, tmp_path: Path) -> None:
        """Test getting the total number of chapters."""
        chapters = {
            "ch1": "<html><body><h1>Chapter 1</h1></body></html>",
            "ch2": "<html><body><h1>Chapter 2</h1></body></html>",
            "ch3": "<html><body><h1>Chapter 3</h1></body></html>",
        }

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        assert book.get_chapter_count() == 3

    def test_get_chapter_content_first_chapter(self, tmp_path: Path) -> None:
        """Test reading content of the first chapter."""
        chapter_content = "<html><body><h1>Chapter 1</h1><p>This is the first chapter.</p></body></html>"
        chapters = {
            "ch1": chapter_content,
            "ch2": "<html><body><h1>Chapter 2</h1></body></html>",
        }

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        content = book.get_chapter_content(0)
        assert content == chapter_content

    def test_get_chapter_content_middle_chapter(self, tmp_path: Path) -> None:
        """Test reading content of a middle chapter."""
        chapter2_content = "<html><body><h1>Chapter 2</h1><p>Middle chapter content.</p></body></html>"
        chapters = {
            "ch1": "<html><body><h1>Chapter 1</h1></body></html>",
            "ch2": chapter2_content,
            "ch3": "<html><body><h1>Chapter 3</h1></body></html>",
        }

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        content = book.get_chapter_content(1)
        assert content == chapter2_content

    def test_get_chapter_content_last_chapter(self, tmp_path: Path) -> None:
        """Test reading content of the last chapter."""
        chapter3_content = "<html><body><h1>Chapter 3</h1><p>Final chapter.</p></body></html>"
        chapters = {
            "ch1": "<html><body><h1>Chapter 1</h1></body></html>",
            "ch2": "<html><body><h1>Chapter 2</h1></body></html>",
            "ch3": chapter3_content,
        }

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        content = book.get_chapter_content(2)
        assert content == chapter3_content

    def test_get_chapter_content_with_utf8_encoding(self, tmp_path: Path) -> None:
        """Test reading chapter content with UTF-8 encoding (special characters)."""
        chapter_content = "<html><body><h1>Chaptér 1</h1><p>Tëst with spëcial chäracters: 你好, مرحبا</p></body></html>"
        chapters = {"ch1": chapter_content}

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        content = book.get_chapter_content(0)
        assert content == chapter_content
        assert "你好" in content
        assert "مرحبا" in content

    def test_get_chapter_content_negative_index_raises_error(self, tmp_path: Path) -> None:
        """Test that negative chapter index raises IndexError."""
        chapters = {"ch1": "<html><body><h1>Chapter 1</h1></body></html>"}

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        with pytest.raises(IndexError) as exc_info:
            book.get_chapter_content(-1)

        assert "out of range" in str(exc_info.value).lower()

    def test_get_chapter_content_index_too_large_raises_error(self, tmp_path: Path) -> None:
        """Test that chapter index >= chapter count raises IndexError."""
        chapters = {
            "ch1": "<html><body><h1>Chapter 1</h1></body></html>",
            "ch2": "<html><body><h1>Chapter 2</h1></body></html>",
        }

        epub_file = self._create_epub_with_content(tmp_path, chapters)
        book = EPUBBook(epub_file)

        with pytest.raises(IndexError) as exc_info:
            book.get_chapter_content(2)  # Only 2 chapters (indices 0-1)

        assert "out of range" in str(exc_info.value).lower()

    def test_get_chapter_content_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Test that missing chapter file raises CorruptedEPUBError."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        # Create EPUB without the actual chapter file
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            # NOT writing OEBPS/chapter1.xhtml

        book = EPUBBook(epub_file)

        with pytest.raises(CorruptedEPUBError) as exc_info:
            book.get_chapter_content(0)

        assert "not found" in str(exc_info.value).lower()

    def test_get_chapter_content_with_nested_directory(self, tmp_path: Path) -> None:
        """Test reading chapter content from nested directory structure."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="content/chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        chapter_content = "<html><body><h1>Chapter 1</h1><p>Nested content.</p></body></html>"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/content/chapter1.xhtml", chapter_content)

        book = EPUBBook(epub_file)
        content = book.get_chapter_content(0)

        assert content == chapter_content

    def test_get_chapter_content_with_opf_at_root(self, tmp_path: Path) -> None:
        """Test reading chapter content when OPF is at root level (not in subdirectory)."""
        epub_file = tmp_path / "test.epub"

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        opf_xml = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Test Book</dc:title>
</metadata>
<manifest>
<item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        chapter_content = "<html><body><h1>Chapter 1</h1><p>Root level chapter.</p></body></html>"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("content.opf", opf_xml)
            zf.writestr("chapter1.xhtml", chapter_content)

        book = EPUBBook(epub_file)
        content = book.get_chapter_content(0)

        assert content == chapter_content
