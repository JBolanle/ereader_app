"""EPUB book parsing and representation.

This module provides the EPUBBook class for parsing and accessing EPUB files.
EPUBs are ZIP archives containing structured content in XML and XHTML formats.
"""

import logging
import zipfile
from pathlib import Path

from ereader.exceptions import InvalidEPUBError

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
