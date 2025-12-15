"""Cover image extraction from EPUB files.

This module provides the CoverExtractor utility for extracting cover images
from EPUB files using multiple detection strategies (EPUB 3, EPUB 2, heuristics).
"""

import logging
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from ereader.exceptions import InvalidEPUBError
from ereader.models.epub import EPUBBook

logger = logging.getLogger(__name__)


class CoverExtractor:
    """Extract cover images from EPUB files.

    This utility tries multiple extraction strategies in order:
    1. EPUB 3: properties="cover-image" in manifest
    2. EPUB 2: <meta name="cover"> referencing manifest item
    3. Filename heuristic: image with "cover" in filename

    All methods are static as this is a stateless utility class.
    """

    @staticmethod
    def extract_cover(epub_path: str | Path) -> tuple[bytes, str] | None:
        """Extract cover image from EPUB.

        Tries multiple extraction strategies in order of specificity.
        Returns the first successfully extracted cover.

        Args:
            epub_path: Path to EPUB file.

        Returns:
            Tuple of (image_bytes, file_extension) or None if no cover found.
            Example: (b'\\xff\\xd8\\xff...', 'jpg')

        Raises:
            FileNotFoundError: If EPUB doesn't exist.
            InvalidEPUBError: If file is not a valid EPUB.
        """
        logger.debug("Extracting cover from: %s", epub_path)

        try:
            # Create EPUBBook instance to access structure
            epub = EPUBBook(epub_path)

            # Try EPUB 3 method first (most specific)
            cover = CoverExtractor._try_epub3_cover(epub)
            if cover:
                logger.info("Extracted cover using EPUB 3 method")
                return cover

            # Try EPUB 2 method
            cover = CoverExtractor._try_epub2_cover(epub)
            if cover:
                logger.info("Extracted cover using EPUB 2 method")
                return cover

            # Try filename heuristic
            cover = CoverExtractor._try_filename_heuristic(epub)
            if cover:
                logger.info("Extracted cover using filename heuristic")
                return cover

            logger.warning("No cover found in EPUB: %s", epub_path)
            return None

        except FileNotFoundError:
            logger.error("EPUB file not found: %s", epub_path)
            raise
        except InvalidEPUBError as e:
            logger.error("Invalid EPUB file %s: %s", epub_path, e)
            raise

    @staticmethod
    def _try_epub3_cover(epub: EPUBBook) -> tuple[bytes, str] | None:
        """Try EPUB 3 properties='cover-image' method.

        EPUB 3 specifies covers via properties attribute in manifest:
        <item id="cover" href="images/cover.jpg" properties="cover-image"/>

        Args:
            epub: EPUBBook instance.

        Returns:
            Tuple of (image_bytes, extension) or None.
        """
        logger.debug("Trying EPUB 3 cover detection")

        try:
            with zipfile.ZipFile(epub.filepath) as zf:
                # Parse OPF to access manifest
                opf_path = epub._get_opf_path()
                opf_data = zf.read(opf_path)
                opf_root = ET.fromstring(opf_data)

                # Find manifest
                manifest = opf_root.find(".//{*}manifest")
                if manifest is None:
                    logger.debug("No manifest found in OPF")
                    return None

                # Find item with properties="cover-image"
                for item in manifest.findall(".//{*}item"):
                    properties = item.get("properties", "")
                    if "cover-image" in properties:
                        href = item.get("href")
                        media_type = item.get("media-type", "")

                        if href:
                            logger.debug("Found EPUB 3 cover: %s", href)

                            # Resolve href relative to OPF location
                            opf_dir = str(Path(opf_path).parent)
                            if opf_dir and opf_dir != ".":
                                cover_path = f"{opf_dir}/{href}"
                            else:
                                cover_path = href

                            # Read cover image
                            try:
                                cover_bytes = zf.read(cover_path)
                                extension = CoverExtractor._get_image_extension(
                                    media_type, href
                                )
                                logger.debug(
                                    "Successfully extracted EPUB 3 cover: %s (%d bytes)",
                                    cover_path,
                                    len(cover_bytes),
                                )
                                return (cover_bytes, extension)
                            except KeyError:
                                logger.warning("Cover file not found in ZIP: %s", cover_path)
                                return None

                logger.debug("No EPUB 3 cover-image property found")
                return None

        except ET.ParseError as e:
            logger.warning("Failed to parse OPF for EPUB 3 cover: %s", e)
            return None
        except Exception as e:
            logger.warning("Unexpected error extracting EPUB 3 cover: %s", e)
            return None

    @staticmethod
    def _try_epub2_cover(epub: EPUBBook) -> tuple[bytes, str] | None:
        """Try EPUB 2 <meta name='cover'> method.

        EPUB 2 uses two-step reference:
        1. <meta name="cover" content="cover-id"/> in metadata
        2. Manifest item with id="cover-id" has the cover href

        Args:
            epub: EPUBBook instance.

        Returns:
            Tuple of (image_bytes, extension) or None.
        """
        logger.debug("Trying EPUB 2 cover detection")

        try:
            with zipfile.ZipFile(epub.filepath) as zf:
                # Parse OPF
                opf_path = epub._get_opf_path()
                opf_data = zf.read(opf_path)
                opf_root = ET.fromstring(opf_data)

                # Find <meta name="cover"> in metadata
                cover_meta = None
                for meta in opf_root.findall(".//{*}meta"):
                    if meta.get("name") == "cover":
                        cover_meta = meta
                        break

                if cover_meta is None:
                    logger.debug("No <meta name='cover'> found")
                    return None

                # Get cover item ID from content attribute
                cover_id = cover_meta.get("content")
                if not cover_id:
                    logger.debug("<meta name='cover'> has no content attribute")
                    return None

                logger.debug("Found EPUB 2 cover meta, id: %s", cover_id)

                # Find manifest item with this ID
                manifest = opf_root.find(".//{*}manifest")
                if manifest is None:
                    logger.debug("No manifest found in OPF")
                    return None

                for item in manifest.findall(".//{*}item"):
                    if item.get("id") == cover_id:
                        href = item.get("href")
                        media_type = item.get("media-type", "")

                        if href:
                            logger.debug("Found EPUB 2 cover item: %s", href)

                            # Resolve href relative to OPF location
                            opf_dir = str(Path(opf_path).parent)
                            if opf_dir and opf_dir != ".":
                                cover_path = f"{opf_dir}/{href}"
                            else:
                                cover_path = href

                            # Read cover image
                            try:
                                cover_bytes = zf.read(cover_path)
                                extension = CoverExtractor._get_image_extension(
                                    media_type, href
                                )
                                logger.debug(
                                    "Successfully extracted EPUB 2 cover: %s (%d bytes)",
                                    cover_path,
                                    len(cover_bytes),
                                )
                                return (cover_bytes, extension)
                            except KeyError:
                                logger.warning("Cover file not found in ZIP: %s", cover_path)
                                return None

                logger.debug("Manifest item with id=%s not found", cover_id)
                return None

        except ET.ParseError as e:
            logger.warning("Failed to parse OPF for EPUB 2 cover: %s", e)
            return None
        except Exception as e:
            logger.warning("Unexpected error extracting EPUB 2 cover: %s", e)
            return None

    @staticmethod
    def _try_filename_heuristic(epub: EPUBBook) -> tuple[bytes, str] | None:
        """Try finding image with 'cover' in filename.

        Searches for images in the manifest with filenames containing "cover"
        (case-insensitive). Examples: "cover.jpg", "Cover.png", "images/cover-front.jpeg"

        Args:
            epub: EPUBBook instance.

        Returns:
            Tuple of (image_bytes, extension) or None.
        """
        logger.debug("Trying filename heuristic for cover")

        try:
            with zipfile.ZipFile(epub.filepath) as zf:
                # Parse OPF
                opf_path = epub._get_opf_path()
                opf_data = zf.read(opf_path)
                opf_root = ET.fromstring(opf_data)

                # Find manifest
                manifest = opf_root.find(".//{*}manifest")
                if manifest is None:
                    logger.debug("No manifest found in OPF")
                    return None

                # Search for image items with "cover" in filename
                for item in manifest.findall(".//{*}item"):
                    media_type = item.get("media-type", "")
                    href = item.get("href", "")

                    # Check if it's an image
                    if media_type.startswith("image/"):
                        # Check if filename contains "cover" (case-insensitive)
                        filename = Path(href).name.lower()
                        if "cover" in filename:
                            logger.debug("Found cover candidate by filename: %s", href)

                            # Resolve href relative to OPF location
                            opf_dir = str(Path(opf_path).parent)
                            if opf_dir and opf_dir != ".":
                                cover_path = f"{opf_dir}/{href}"
                            else:
                                cover_path = href

                            # Read cover image
                            try:
                                cover_bytes = zf.read(cover_path)
                                extension = CoverExtractor._get_image_extension(
                                    media_type, href
                                )
                                logger.debug(
                                    "Successfully extracted cover via filename heuristic: %s (%d bytes)",
                                    cover_path,
                                    len(cover_bytes),
                                )
                                return (cover_bytes, extension)
                            except KeyError:
                                logger.warning("Cover file not found in ZIP: %s", cover_path)
                                continue  # Try next candidate

                logger.debug("No image with 'cover' in filename found")
                return None

        except ET.ParseError as e:
            logger.warning("Failed to parse OPF for filename heuristic: %s", e)
            return None
        except Exception as e:
            logger.warning("Unexpected error in filename heuristic: %s", e)
            return None

    @staticmethod
    def _get_image_extension(media_type: str, href: str) -> str:
        """Get file extension from media-type or href.

        Args:
            media_type: MIME type (e.g., "image/jpeg").
            href: File path (e.g., "images/cover.jpg").

        Returns:
            File extension without dot (e.g., "jpg", "png").
            Defaults to "jpg" if cannot be determined.
        """
        # Try to get extension from media-type first
        if media_type:
            type_to_ext = {
                "image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/png": "png",
                "image/gif": "gif",
                "image/webp": "webp",
                "image/svg+xml": "svg",
            }
            ext = type_to_ext.get(media_type.lower())
            if ext:
                return ext

        # Fall back to extension from href
        if href:
            path_ext = Path(href).suffix.lstrip(".")
            if path_ext:
                # Normalize common variants
                if path_ext.lower() in ["jpeg", "jpg"]:
                    return "jpg"
                return path_ext.lower()

        # Default to jpg if cannot determine
        logger.debug(
            "Could not determine image extension from media_type=%s, href=%s, defaulting to jpg",
            media_type,
            href,
        )
        return "jpg"
