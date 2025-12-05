"""HTML resource resolution utilities for EPUB content.

This module provides functions to resolve and embed resources (images, CSS, etc.)
referenced in EPUB HTML content.
"""

import base64
import logging
import re
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

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

# Responsive image styling to prevent horizontal and vertical scrolling
# max-width: 100% prevents images from exceeding viewport width
# max-height: 90vh prevents images from exceeding viewport height (90vh leaves margin for UI chrome)
# width/height: auto maintains aspect ratio
# object-fit: contain scales image to fit within bounds
RESPONSIVE_IMAGE_STYLE = 'max-width: 100%; max-height: 90vh; width: auto; height: auto; object-fit: contain;'


def downscale_image(image_data: bytes, max_width: int = 1920, max_height: int = 1080) -> bytes:
    """Downscale image if it exceeds maximum dimensions.

    Reduces memory footprint of large images by downscaling before base64 encoding
    while maintaining aspect ratio and visual quality.

    Args:
        image_data: Raw image bytes
        max_width: Maximum width in pixels (default: 1920)
        max_height: Maximum height in pixels (default: 1080)

    Returns:
        Downscaled image bytes (or original if within limits or on error)

    Example:
        >>> original = load_image_bytes("large_photo.jpg")  # 4000x3000
        >>> downscaled = downscale_image(original, max_width=1920, max_height=1080)
        >>> # Result: 1440x1080 (maintains aspect ratio)
    """
    try:
        # Open image with Pillow
        img = Image.open(BytesIO(image_data))

        # Get original format (preserve it if possible)
        original_format = img.format

        # Skip if already small enough
        if img.width <= max_width and img.height <= max_height:
            logger.debug(
                "Image within limits (%dx%d <= %dx%d), skipping downscale",
                img.width,
                img.height,
                max_width,
                max_height
            )
            return image_data

        # Calculate new size maintaining aspect ratio
        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))

        logger.info(
            "Downscaling image from %dx%d to %dx%d (%.1f%% reduction)",
            img.width,
            img.height,
            new_size[0],
            new_size[1],
            (1 - ratio) * 100
        )

        # Downscale using high-quality resampling
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        # Preserve original format, default to JPEG if unknown
        save_format = original_format if original_format else 'JPEG'
        img_resized.save(output, format=save_format)
        result = output.getvalue()

        logger.info(
            "Image downscaled: %d bytes -> %d bytes (%.1f%% reduction)",
            len(image_data),
            len(result),
            (1 - len(result) / len(image_data)) * 100
        )

        return result

    except Exception as e:
        # Broad exception catch is intentional here:
        # Pillow can raise many exception types (PIL.UnidentifiedImageError,
        # OSError, ValueError, etc.) and we want graceful fallback for all.
        # Better to show original image than crash the app.
        # This handles corrupted images, unsupported formats, etc.
        logger.warning("Failed to downscale image: %s. Using original.", str(e))
        return image_data


def resolve_images_in_html(
    html: str,
    epub_book: "EPUBBook",
    chapter_href: str | None = None
) -> str:
    """Resolve image references in HTML by embedding them as base64 data URLs.

    Finds all <img> tags in the HTML content and replaces relative src attributes
    with base64-encoded data URLs, loading the image data from the EPUB file.

    Args:
        html: The HTML content containing image references.
        epub_book: The EPUBBook instance to load image resources from.
        chapter_href: Optional href of the chapter HTML file (e.g., "text/chapter1.html").
                     If provided, image paths are resolved relative to this file.
                     If None, paths are resolved relative to the OPF file.

    Returns:
        Modified HTML with images embedded as data URLs.

    Example:
        >>> html = '<img src="images/cover.jpg" />'
        >>> resolved_html = resolve_images_in_html(html, book)
        >>> # Result: '<img src="data:image/jpeg;base64,/9j/4AAQ..." />'
        >>> # With chapter context
        >>> html = '<img src="../images/photo.jpg" />'
        >>> resolved_html = resolve_images_in_html(html, book, chapter_href="text/chapter1.html")
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
            # Pass chapter context if available for correct path resolution
            image_data = epub_book.get_resource(src_value, relative_to=chapter_href)

            # Determine MIME type from extension
            mime_type = _get_mime_type(src_value)

            # Downscale image if it's not SVG (vector-based)
            # SVG images scale perfectly and don't need downscaling
            if mime_type != "image/svg+xml":
                image_data = downscale_image(image_data)

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

            # Reconstruct the img tag with data URL and responsive styling
            # Note: If original <img> tag has style attribute in before_src or after_src,
            # browsers will ignore our injected style (uses first style attribute only).
            # This is acceptable as: (1) rare in EPUBs, (2) image still displays, just not responsive.
            # TODO: Parse and merge style attributes if user feedback indicates need.
            return f'<img {before_src}src="{data_url}" style="{RESPONSIVE_IMAGE_STYLE}"{after_src}>'

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
