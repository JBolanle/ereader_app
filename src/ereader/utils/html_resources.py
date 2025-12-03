"""HTML resource resolution utilities for EPUB content.

This module provides functions to resolve and embed resources (images, CSS, etc.)
referenced in EPUB HTML content.
"""

import base64
import logging
import re
from typing import TYPE_CHECKING

from ereader.exceptions import CorruptedEPUBError

if TYPE_CHECKING:
    from ereader.models.epub import EPUBBook

logger = logging.getLogger(__name__)

# MIME type mapping for common image formats
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def resolve_images_in_html(html: str, epub_book: "EPUBBook") -> str:
    """Resolve image references in HTML by embedding them as base64 data URLs.

    Finds all <img> tags in the HTML content and replaces relative src attributes
    with base64-encoded data URLs, loading the image data from the EPUB file.

    Args:
        html: The HTML content containing image references.
        epub_book: The EPUBBook instance to load image resources from.

    Returns:
        Modified HTML with images embedded as data URLs.

    Example:
        >>> html = '<img src="images/cover.jpg" />'
        >>> resolved_html = resolve_images_in_html(html, book)
        >>> # Result: '<img src="data:image/jpeg;base64,/9j/4AAQ..." />'
    """
    # Pattern to match <img> tags and capture the src attribute
    # Handles various quote styles and whitespace
    img_pattern = re.compile(
        r'<img\s+([^>]*?)src=(["\'])([^"\']+?)\2([^>]*?)>',
        re.IGNORECASE
    )

    def replace_image(match: re.Match[str]) -> str:
        """Replace a single image src with a data URL."""
        before_src = match.group(1)  # Attributes before src
        src_value = match.group(3)   # The actual src value
        after_src = match.group(4)   # Attributes after src

        # Skip if already a data URL or absolute URL
        if src_value.startswith(('data:', 'http://', 'https://')):
            logger.debug("Skipping absolute/data URL: %s", src_value)
            return match.group(0)  # Return original

        logger.debug("Resolving image: %s", src_value)

        try:
            # Load image data from EPUB
            image_data = epub_book.get_resource(src_value)

            # Determine MIME type from extension
            mime_type = _get_mime_type(src_value)

            # Encode as base64
            base64_data = base64.b64encode(image_data).decode('ascii')

            # Build data URL
            data_url = f"data:{mime_type};base64,{base64_data}"

            logger.debug(
                "Resolved image %s (%d bytes, %s)",
                src_value,
                len(image_data),
                mime_type
            )

            # Reconstruct the img tag with data URL
            return f'<img {before_src}src="{data_url}"{after_src}>'

        except CorruptedEPUBError:
            # Image not found - log warning but keep original reference
            logger.warning("Image not found in EPUB: %s", src_value)
            return match.group(0)  # Return original tag

    # Replace all image tags
    resolved_html = img_pattern.sub(replace_image, html)

    return resolved_html


def _get_mime_type(filename: str) -> str:
    """Get MIME type for a file based on its extension.

    Args:
        filename: The filename or path.

    Returns:
        MIME type string (defaults to 'image/jpeg' if unknown).
    """
    # Extract extension (lowercase)
    ext = None
    if '.' in filename:
        ext = '.' + filename.rsplit('.', 1)[-1].lower()

    # Look up MIME type, default to JPEG
    return MIME_TYPES.get(ext, "image/jpeg")
