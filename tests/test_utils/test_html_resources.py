"""Tests for HTML resource resolution utilities."""

import zipfile
from pathlib import Path

from ereader.models.epub import EPUBBook
from ereader.utils.html_resources import resolve_images_in_html


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
        assert 'style="max-width: 100%; height: auto;"' in resolved_html

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
        assert resolved_html.count('style="max-width: 100%; height: auto;"') == 2

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
        assert 'style="max-width: 100%; height: auto;"' in resolved_html

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
        """Test that responsive styling is added to make images fit viewport."""
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

        # Should have responsive style to prevent horizontal scrolling
        assert 'style="max-width: 100%; height: auto;"' in resolved_html
        # Style prevents images from exceeding viewport width
        assert "max-width: 100%" in resolved_html
        # height: auto maintains aspect ratio
        assert "height: auto" in resolved_html

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
