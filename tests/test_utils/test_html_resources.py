"""Tests for HTML resource resolution utilities."""

import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from ereader.models.epub import EPUBBook
from ereader.utils.html_resources import downscale_image, resolve_images_in_html


class TestResolveImagesInHTML:
    """Test resolve_images_in_html function."""

    def test_resolve_simple_image(self, tmp_path: Path) -> None:
        """Test resolving a simple image reference."""
        # Create a minimal EPUB with an image
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
<item id="img1" href="images/test.png" media-type="image/png"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        # PNG header
        image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            zf.writestr("OEBPS/images/test.png", image_data)

        book = EPUBBook(epub_file)

        html = '<img src="images/test.png" />'
        resolved_html = resolve_images_in_html(html, book)

        # Check that it's now a data URL with responsive styling
        assert "data:image/png;base64," in resolved_html
        assert "images/test.png" not in resolved_html
        assert 'style="max-width: 100%; max-height: 90vh; width: auto; height: auto; object-fit: contain;"' in resolved_html

    def test_resolve_multiple_images(self, tmp_path: Path) -> None:
        """Test resolving multiple image references in same HTML."""
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
<item id="img1" href="images/img1.png" media-type="image/png"/>
<item id="img2" href="images/img2.jpg" media-type="image/jpeg"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        png_data = b"\x89PNG"
        jpg_data = b"\xff\xd8\xff\xe0"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            zf.writestr("OEBPS/images/img1.png", png_data)
            zf.writestr("OEBPS/images/img2.jpg", jpg_data)

        book = EPUBBook(epub_file)

        html = '''
        <html>
        <body>
        <img src="images/img1.png" alt="First" />
        <p>Some text</p>
        <img src="images/img2.jpg" alt="Second" />
        </body>
        </html>
        '''

        resolved_html = resolve_images_in_html(html, book)

        # Both images should be resolved with responsive styling
        assert resolved_html.count("data:image/png;base64,") == 1
        assert resolved_html.count("data:image/jpeg;base64,") == 1
        assert "images/img1.png" not in resolved_html
        assert "images/img2.jpg" not in resolved_html
        assert resolved_html.count('style="max-width: 100%; max-height: 90vh; width: auto; height: auto; object-fit: contain;"') == 2

    def test_preserve_image_attributes(self, tmp_path: Path) -> None:
        """Test that image attributes (alt, class, etc.) are preserved."""
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
<item id="img1" href="cover.jpg" media-type="image/jpeg"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        image_data = b"\xff\xd8\xff\xe0"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            zf.writestr("OEBPS/cover.jpg", image_data)

        book = EPUBBook(epub_file)

        html = '<img class="cover" alt="Book Cover" src="cover.jpg" width="300" />'
        resolved_html = resolve_images_in_html(html, book)

        # Attributes should be preserved and responsive style added
        assert 'class="cover"' in resolved_html
        assert 'alt="Book Cover"' in resolved_html
        assert 'width="300"' in resolved_html
        assert "data:image/jpeg;base64," in resolved_html
        assert 'style="max-width: 100%; max-height: 90vh; width: auto; height: auto; object-fit: contain;"' in resolved_html

    def test_skip_absolute_urls(self, tmp_path: Path) -> None:
        """Test that absolute URLs (http, https) are not modified."""
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
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")

        book = EPUBBook(epub_file)

        html = '''
        <img src="http://example.com/image1.jpg" />
        <img src="https://example.com/image2.png" />
        '''

        resolved_html = resolve_images_in_html(html, book)

        # URLs should be unchanged
        assert 'src="http://example.com/image1.jpg"' in resolved_html
        assert 'src="https://example.com/image2.png"' in resolved_html
        assert "data:image" not in resolved_html

    def test_skip_existing_data_urls(self, tmp_path: Path) -> None:
        """Test that existing data URLs are not modified."""
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
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")

        book = EPUBBook(epub_file)

        original_data_url = "data:image/png;base64,iVBORw0KGgo="
        html = f'<img src="{original_data_url}" />'

        resolved_html = resolve_images_in_html(html, book)

        # Data URL should be unchanged
        assert original_data_url in resolved_html

    def test_missing_image_keeps_original_reference(self, tmp_path: Path) -> None:
        """Test that missing images don't break HTML (keeps original reference)."""
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
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            # NOT creating the image file

        book = EPUBBook(epub_file)

        html = '<img src="nonexistent.jpg" alt="Missing" />'
        resolved_html = resolve_images_in_html(html, book)

        # Original reference should be kept (graceful degradation)
        assert 'src="nonexistent.jpg"' in resolved_html
        assert 'alt="Missing"' in resolved_html

    def test_responsive_style_added_to_images(self, tmp_path: Path) -> None:
        """Test that responsive styling is added to make images fit viewport in both dimensions."""
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
<item id="img1" href="large.jpg" media-type="image/jpeg"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        image_data = b"\xff\xd8\xff\xe0"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            zf.writestr("OEBPS/large.jpg", image_data)

        book = EPUBBook(epub_file)

        # Test with a large image that would exceed viewport
        html = '<img src="large.jpg" alt="Large Image" />'
        resolved_html = resolve_images_in_html(html, book)

        # Should have responsive style to prevent horizontal and vertical scrolling
        assert 'style="max-width: 100%; max-height: 90vh; width: auto; height: auto; object-fit: contain;"' in resolved_html
        # Style prevents images from exceeding viewport dimensions
        assert "max-width: 100%" in resolved_html
        assert "max-height: 90vh" in resolved_html
        # width/height: auto maintains aspect ratio
        assert "width: auto" in resolved_html
        assert "height: auto" in resolved_html
        # object-fit: contain scales image to fit within bounds
        assert "object-fit: contain" in resolved_html

    def test_image_with_existing_inline_style(self, tmp_path: Path) -> None:
        """Test behavior when image already has inline style attribute.

        This test documents a known limitation: if the original <img> tag
        has a style attribute, browsers will use only the first style attribute
        and ignore our injected responsive style. This is acceptable because:
        1. It's rare in EPUBs for images to have inline styles
        2. The image still displays, just not with responsive sizing
        3. Manual testing hasn't revealed any actual issues

        This test verifies current behavior (no style merging) and serves
        as documentation of the limitation.
        """
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
<item id="img1" href="test.jpg" media-type="image/jpeg"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        image_data = b"\xff\xd8\xff\xe0"

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            zf.writestr("OEBPS/test.jpg", image_data)

        book = EPUBBook(epub_file)

        # Image with existing style attribute
        html = '<img style="border: 1px solid red;" src="test.jpg" />'
        resolved_html = resolve_images_in_html(html, book)

        # Document current behavior: both style attributes present (browsers use first)
        # The original style will be preserved (border will render)
        assert 'style="border: 1px solid red;"' in resolved_html
        # Our responsive style is also added (but browsers will ignore it)
        assert 'style="max-width: 100%' in resolved_html
        # Image is still resolved to data URL
        assert 'data:image/jpeg;base64,' in resolved_html

    def test_svg_images_not_downscaled(self, tmp_path: Path) -> None:
        """Test that SVG images are not downscaled (they're vector-based)."""
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
<item id="img1" href="diagram.svg" media-type="image/svg+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="ch1"/>
</spine>
</package>"""

        # Minimal SVG image
        svg_data = b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'

        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_xml)
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")
            zf.writestr("OEBPS/diagram.svg", svg_data)

        book = EPUBBook(epub_file)

        html = '<img src="diagram.svg" alt="Diagram" />'
        resolved_html = resolve_images_in_html(html, book)

        # SVG should be embedded but not downscaled (vector graphics scale perfectly)
        assert "data:image/svg+xml;base64," in resolved_html
        assert "diagram.svg" not in resolved_html

    def test_html_without_images_unchanged(self, tmp_path: Path) -> None:
        """Test that HTML without images passes through unchanged."""
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
            zf.writestr("OEBPS/chapter1.xhtml", "<html></html>")

        book = EPUBBook(epub_file)

        html = '''
        <html>
        <body>
        <h1>Chapter 1</h1>
        <p>This is some text without any images.</p>
        </body>
        </html>
        '''

        resolved_html = resolve_images_in_html(html, book)

        # HTML should be unchanged
        assert resolved_html == html


class TestDownscaleImage:
    """Test downscale_image function."""

    def _create_test_image(self, width: int, height: int, format: str = 'JPEG') -> bytes:
        """Helper to create a test image of specified dimensions.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            format: Image format (JPEG, PNG, etc.)

        Returns:
            Image bytes
        """
        img = Image.new('RGB', (width, height), color='red')
        output = BytesIO()
        img.save(output, format=format)
        return output.getvalue()

    def test_image_within_limits_unchanged(self) -> None:
        """Test that images within size limits are not downscaled."""
        # Create a 1000x800 image (within 1920x1080 limits)
        original = self._create_test_image(1000, 800)

        result = downscale_image(original, max_width=1920, max_height=1080)

        # Should be identical (no downscaling)
        assert result == original

    def test_image_exceeds_width_only(self) -> None:
        """Test downscaling when image exceeds only width."""
        # Create a 3000x1000 image (width exceeds, height ok)
        original = self._create_test_image(3000, 1000)

        result = downscale_image(original, max_width=1920, max_height=1080)

        # Should be downscaled
        assert len(result) < len(original)

        # Verify new dimensions
        img = Image.open(BytesIO(result))
        assert img.width == 1920
        assert img.height == 640  # Maintains aspect ratio: 1000 * (1920/3000)

    def test_image_exceeds_height_only(self) -> None:
        """Test downscaling when image exceeds only height."""
        # Create a 1000x2000 image (height exceeds, width ok)
        original = self._create_test_image(1000, 2000)

        result = downscale_image(original, max_width=1920, max_height=1080)

        # Should be downscaled
        assert len(result) < len(original)

        # Verify new dimensions
        img = Image.open(BytesIO(result))
        assert img.width == 540  # Maintains aspect ratio: 1000 * (1080/2000)
        assert img.height == 1080

    def test_image_exceeds_both_dimensions(self) -> None:
        """Test downscaling when image exceeds both width and height."""
        # Create a 4000x3000 image (both dimensions exceed)
        original = self._create_test_image(4000, 3000)

        result = downscale_image(original, max_width=1920, max_height=1080)

        # Should be downscaled significantly
        assert len(result) < len(original)

        # Verify new dimensions (constrained by height in this case)
        img = Image.open(BytesIO(result))
        assert img.width == 1440  # 4000 * (1080/3000)
        assert img.height == 1080

    def test_aspect_ratio_preserved(self) -> None:
        """Test that aspect ratio is maintained during downscaling."""
        # Create images with various aspect ratios
        test_cases = [
            (4000, 2000),  # 2:1 landscape
            (2000, 4000),  # 1:2 portrait
            (3000, 3000),  # 1:1 square
            (4800, 3200),  # 3:2 landscape
        ]

        for width, height in test_cases:
            original = self._create_test_image(width, height)
            original_ratio = width / height

            result = downscale_image(original, max_width=1920, max_height=1080)

            # Verify aspect ratio preserved
            img = Image.open(BytesIO(result))
            result_ratio = img.width / img.height
            # Allow small floating point error
            assert abs(result_ratio - original_ratio) < 0.01

    def test_various_image_formats(self) -> None:
        """Test downscaling works with different image formats."""
        formats_to_test = [
            ('JPEG', 2400, 1800),
            ('PNG', 2400, 1800),
            ('BMP', 2400, 1800),
        ]

        for format_name, width, height in formats_to_test:
            original = self._create_test_image(width, height, format=format_name)

            result = downscale_image(original, max_width=1920, max_height=1080)

            # Should be downscaled
            img = Image.open(BytesIO(result))
            assert img.width <= 1920
            assert img.height <= 1080

    def test_custom_max_dimensions(self) -> None:
        """Test downscaling with custom maximum dimensions."""
        original = self._create_test_image(2000, 1500)

        # Use smaller max dimensions
        result = downscale_image(original, max_width=800, max_height=600)

        img = Image.open(BytesIO(result))
        assert img.width == 800
        assert img.height == 600

    def test_very_large_image(self) -> None:
        """Test downscaling extremely large images (like high-res photos)."""
        # Create an 8000x6000 image (simulating high-res camera photo)
        original = self._create_test_image(8000, 6000)

        result = downscale_image(original, max_width=1920, max_height=1080)

        # Should be significantly smaller
        assert len(result) < len(original) * 0.25  # At least 75% reduction

        img = Image.open(BytesIO(result))
        assert img.width == 1440
        assert img.height == 1080

    def test_corrupted_image_returns_original(self) -> None:
        """Test that corrupted image data returns original bytes."""
        corrupted_data = b"this is not a valid image"

        result = downscale_image(corrupted_data)

        # Should return original when processing fails
        assert result == corrupted_data

    def test_empty_image_data(self) -> None:
        """Test handling of empty image data."""
        empty_data = b""

        result = downscale_image(empty_data)

        # Should return original (graceful failure)
        assert result == empty_data

    def test_very_small_image(self) -> None:
        """Test that very small images are not upscaled."""
        # Create a tiny 100x100 image
        small = self._create_test_image(100, 100)

        result = downscale_image(small, max_width=1920, max_height=1080)

        # Should be unchanged (no upscaling)
        assert result == small

    def test_edge_case_exact_max_dimensions(self) -> None:
        """Test image exactly at max dimensions."""
        # Create image exactly at max size
        original = self._create_test_image(1920, 1080)

        result = downscale_image(original, max_width=1920, max_height=1080)

        # Should be unchanged
        assert result == original

    def test_format_preservation(self) -> None:
        """Test that original image format is preserved."""
        # Test JPEG preservation
        jpeg_img = self._create_test_image(2400, 1800, format='JPEG')
        jpeg_result = downscale_image(jpeg_img)
        jpeg_out = Image.open(BytesIO(jpeg_result))
        assert jpeg_out.format == 'JPEG'

        # Test PNG preservation
        png_img = self._create_test_image(2400, 1800, format='PNG')
        png_result = downscale_image(png_img)
        png_out = Image.open(BytesIO(png_result))
        assert png_out.format == 'PNG'
