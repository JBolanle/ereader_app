"""EPUB book parsing and representation.

This module provides the EPUBBook class for parsing and accessing EPUB files.
EPUBs are ZIP archives containing structured content in XML and XHTML formats.
"""

import logging
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from ereader.exceptions import CorruptedEPUBError, InvalidEPUBError

logger = logging.getLogger(__name__)


class EPUBBook:
    """Represents an EPUB book with methods to access its content and metadata.

    An EPUB file is essentially a ZIP archive containing:
    - META-INF/container.xml: Points to the content.opf file
    - content.opf: Contains metadata, manifest, and spine (reading order)
    - XHTML/HTML files: The actual chapter content
    - Additional resources: Images, CSS, fonts, etc.

    This class handles parsing the EPUB structure and provides access to:
    - Book metadata (title, author, language, etc.)
    - Reading order (spine)
    - Chapter content
    - File manifest

    Example:
        >>> book = EPUBBook("path/to/book.epub")
        >>> print(book.filepath)
        path/to/book.epub

    Attributes:
        filepath: Path to the EPUB file.
        title: Book title (defaults to "Unknown Title" if not found).
        authors: List of book authors (defaults to ["Unknown Author"] if not found).
        language: Book language code (defaults to "en" if not found).

    Raises:
        InvalidEPUBError: If the file is not a valid EPUB.
        FileNotFoundError: If the file does not exist.
    """

    def __init__(self, filepath: str | Path) -> None:
        """Initialize an EPUBBook instance.

        Args:
            filepath: Path to the EPUB file to open.

        Raises:
            InvalidEPUBError: If the file is not a valid EPUB.
            FileNotFoundError: If the file does not exist.
        """
        self.filepath = Path(filepath)
        logger.info("Initializing EPUBBook with file: %s", self.filepath)

        # Validate the file exists
        if not self.filepath.exists():
            logger.error("File not found: %s", self.filepath)
            raise FileNotFoundError(f"EPUB file not found: {self.filepath}")

        # Validate it's a readable file
        if not self.filepath.is_file():
            logger.error("Path is not a file: %s", self.filepath)
            raise InvalidEPUBError(f"Path is not a file: {self.filepath}")

        # Validate the file is a ZIP archive (EPUBs are ZIP files)
        if not zipfile.is_zipfile(self.filepath):
            logger.error("File is not a valid ZIP archive: %s", self.filepath)
            raise InvalidEPUBError(
                f"{self.filepath} is not a valid EPUB file (not a ZIP archive)"
            )

        # Validate EPUB structure - must have container.xml
        with zipfile.ZipFile(self.filepath) as zf:
            if "META-INF/container.xml" not in zf.namelist():
                logger.error("Missing META-INF/container.xml in: %s", self.filepath)
                raise InvalidEPUBError(
                    f"{self.filepath} is missing required META-INF/container.xml"
                )

        logger.debug("Successfully validated EPUB file: %s", self.filepath)

        # Initialize metadata attributes with defaults
        self.title: str = "Unknown Title"
        self.authors: list[str] = ["Unknown Author"]
        self.language: str = "en"

        # Initialize structure attributes
        self._manifest: dict[str, str] = {}  # item id -> href
        self._spine: list[str] = []  # ordered list of item ids

        # Extract metadata from the EPUB
        self._extract_metadata()

        # Parse manifest and spine
        self._parse_manifest_and_spine()

    def _get_opf_path(self) -> str:
        """Find the path to the OPF file from container.xml.

        The container.xml file in META-INF/ directory points to the location
        of the content.opf file, which contains all metadata and structure.

        Returns:
            Path to the OPF file within the EPUB archive.

        Raises:
            CorruptedEPUBError: If container.xml is malformed or missing required elements.
        """
        try:
            with zipfile.ZipFile(self.filepath) as zf:
                container_data = zf.read("META-INF/container.xml")
                container_root = ET.fromstring(container_data)

                # Find the rootfile element with the OPF path
                # Using {*} wildcard to handle any namespace
                rootfile = container_root.find(".//{*}rootfile")

                if rootfile is None:
                    logger.error("No rootfile element found in container.xml")
                    raise CorruptedEPUBError(
                        "container.xml missing required rootfile element"
                    )

                opf_path = rootfile.get("full-path")
                if not opf_path:
                    logger.error("rootfile element missing full-path attribute")
                    raise CorruptedEPUBError(
                        "rootfile element missing full-path attribute"
                    )

                logger.debug("Found OPF file at: %s", opf_path)
                return opf_path

        except ET.ParseError as e:
            logger.error("Failed to parse container.xml: %s", e)
            raise CorruptedEPUBError(f"Malformed container.xml: {e}") from e

    def _extract_metadata(self) -> None:
        """Extract book metadata (title, author, language) from the OPF file.

        Reads the content.opf file and extracts Dublin Core metadata elements.
        Uses fallback to default values if metadata is missing.

        The method handles:
        - Multiple authors (stores as list)
        - XML namespace variations (using {*} wildcards)
        - Missing metadata (uses defaults)

        Raises:
            CorruptedEPUBError: If the OPF file is malformed or unreadable.
        """
        opf_path = self._get_opf_path()

        try:
            with zipfile.ZipFile(self.filepath) as zf:
                opf_data = zf.read(opf_path)
                opf_root = ET.fromstring(opf_data)

                # Extract title - look for both dc:title and dcterms:title
                title_elem = opf_root.find(".//{*}title")
                if title_elem is not None and title_elem.text:
                    self.title = title_elem.text.strip()
                    logger.debug("Extracted title: %s", self.title)
                else:
                    logger.warning("No title found, using default")

                # Extract authors - there can be multiple dc:creator elements
                creator_elems = opf_root.findall(".//{*}creator")
                if creator_elems:
                    authors = [
                        elem.text.strip()
                        for elem in creator_elems
                        if elem.text and elem.text.strip()
                    ]
                    if authors:
                        self.authors = authors
                        logger.debug("Extracted authors: %s", self.authors)
                    else:
                        logger.warning("Creator elements found but empty, using default")
                else:
                    logger.warning("No authors found, using default")

                # Extract language
                language_elem = opf_root.find(".//{*}language")
                if language_elem is not None and language_elem.text:
                    self.language = language_elem.text.strip()
                    logger.debug("Extracted language: %s", self.language)
                else:
                    logger.warning("No language found, using default")

        except ET.ParseError as e:
            logger.error("Failed to parse OPF file %s: %s", opf_path, e)
            raise CorruptedEPUBError(f"Malformed OPF file {opf_path}: {e}") from e
        except KeyError:
            logger.error("OPF file not found in EPUB: %s", opf_path)
            raise CorruptedEPUBError(f"OPF file not found in EPUB: {opf_path}") from None

    def _parse_manifest_and_spine(self) -> None:
        """Parse manifest and spine from the OPF file.

        The manifest is a list of all files in the EPUB (ID -> file path mapping).
        The spine is the reading order (ordered list of manifest item IDs).

        This method extracts both structures from the OPF file and stores them
        in _manifest and _spine attributes.

        Raises:
            CorruptedEPUBError: If OPF is malformed or missing required elements.
        """
        opf_path = self._get_opf_path()

        try:
            with zipfile.ZipFile(self.filepath) as zf:
                opf_data = zf.read(opf_path)
                opf_root = ET.fromstring(opf_data)

                # Parse manifest - maps item ID to file href
                manifest_elem = opf_root.find(".//{*}manifest")
                if manifest_elem is None:
                    logger.error("Missing manifest element in OPF")
                    raise CorruptedEPUBError("Missing required manifest element in OPF")

                for item in manifest_elem.findall(".//{*}item"):
                    item_id = item.get("id")
                    href = item.get("href")
                    if item_id and href:
                        # Warn if duplicate IDs found (technically invalid per EPUB spec)
                        if item_id in self._manifest:
                            logger.warning(
                                "Duplicate manifest item ID: %s (previous: %s, new: %s)",
                                item_id,
                                self._manifest[item_id],
                                href,
                            )
                        self._manifest[item_id] = href

                logger.debug("Parsed %d items in manifest", len(self._manifest))

                # Parse spine - ordered list of item IDs for reading order
                spine_elem = opf_root.find(".//{*}spine")
                if spine_elem is None:
                    logger.error("Missing spine element in OPF")
                    raise CorruptedEPUBError("Missing required spine element in OPF")

                for itemref in spine_elem.findall(".//{*}itemref"):
                    idref = itemref.get("idref")
                    if idref:
                        if idref in self._manifest:
                            self._spine.append(idref)
                        else:
                            logger.warning(
                                "Spine references non-existent manifest item: %s", idref
                            )

                if not self._spine:
                    logger.error("Empty spine (no chapters)")
                    raise CorruptedEPUBError(
                        "Empty spine: EPUB must have at least one chapter"
                    )

                logger.debug("Parsed spine with %d chapters", len(self._spine))

        except ET.ParseError as e:
            logger.error("Failed to parse OPF file %s: %s", opf_path, e)
            raise CorruptedEPUBError(f"Malformed OPF file {opf_path}: {e}") from e
        except KeyError:
            logger.error("OPF file not found in EPUB: %s", opf_path)
            raise CorruptedEPUBError(f"OPF file not found in EPUB: {opf_path}") from None

    def get_chapter_count(self) -> int:
        """Get the number of chapters in the book.

        Returns:
            The number of chapters in the reading order (spine).
        """
        return len(self._spine)

    def get_chapter_content(self, chapter_index: int) -> str:
        """Get the content of a chapter by its index in the reading order.

        Args:
            chapter_index: Zero-based index of the chapter in the spine.

        Returns:
            The chapter content as a string (XHTML/HTML).

        Raises:
            IndexError: If chapter_index is out of range.
            CorruptedEPUBError: If the chapter file is missing or unreadable.
        """
        if chapter_index < 0 or chapter_index >= len(self._spine):
            logger.error(
                "Chapter index %d out of range (0-%d)", chapter_index, len(self._spine) - 1
            )
            raise IndexError(
                f"Chapter index {chapter_index} out of range (0-{len(self._spine) - 1})"
            )

        # Get the item ID from spine
        item_id = self._spine[chapter_index]
        logger.debug("Reading chapter %d (item ID: %s)", chapter_index, item_id)

        # Get the file path from manifest
        if item_id not in self._manifest:
            logger.error("Spine item ID %s not found in manifest", item_id)
            raise CorruptedEPUBError(
                f"Spine references item {item_id} that doesn't exist in manifest"
            )

        chapter_href = self._manifest[item_id]
        logger.debug("Chapter file: %s", chapter_href)

        # Resolve the full path within the EPUB
        # Chapter hrefs are relative to the OPF file location
        opf_path = self._get_opf_path()
        opf_dir = str(Path(opf_path).parent)

        # Build the full path within the ZIP
        if opf_dir and opf_dir != ".":
            full_path = f"{opf_dir}/{chapter_href}"
        else:
            full_path = chapter_href

        logger.debug("Full path in EPUB: %s", full_path)

        # Read the chapter content from the ZIP
        try:
            with zipfile.ZipFile(self.filepath) as zf:
                # Read as bytes first
                content_bytes = zf.read(full_path)

                # Decode to string - try UTF-8 first, then fall back to latin-1
                try:
                    content = content_bytes.decode("utf-8")
                    logger.debug("Decoded chapter as UTF-8")
                except UnicodeDecodeError:
                    logger.warning("UTF-8 decode failed, trying latin-1")
                    content = content_bytes.decode("latin-1")

                logger.debug(
                    "Successfully read chapter %d (%d bytes)", chapter_index, len(content)
                )
                return content

        except KeyError:
            logger.error("Chapter file not found in EPUB: %s", full_path)
            raise CorruptedEPUBError(
                f"Chapter file {full_path} not found in EPUB (referenced by item {item_id})"
            ) from None
