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
    ) -> Path:
        """Helper to create a minimal EPUB with specified metadata.

        Args:
            tmp_path: Temporary directory from pytest fixture.
            title: Book title (omit to test missing title).
            authors: List of authors (omit to test missing authors).
            language: Language code (omit to test missing language).

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

        opf_parts.extend(["</metadata>", "</package>"])
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
