#!/usr/bin/env python3
"""Quick exploration script to test real EPUB files."""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ereader.models.epub import EPUBBook
from ereader.exceptions import EReaderError

EPUB_DIR = Path(__file__).parent / "EPUBS"

epub_files = [
    "1984 (George Orwell) (Z-Library).epub",
    "The Body Keeps The Score Mind, Brain and Body In The Transformation Of Trauma (Bessel van Der Kolk) (Z-Library).epub",
    "The Mamba Mentality How I Play (Bryant, Kobe) (Z-Library).epub",
]

print("=" * 80)
print("TESTING REAL EPUB FILES")
print("=" * 80)

for epub_file in epub_files:
    epub_path = EPUB_DIR / epub_file
    print(f"\n{'=' * 80}")
    print(f"Testing: {epub_file}")
    print(f"Size: {epub_path.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 80)

    try:
        # Initialize EPUBBook
        book = EPUBBook(epub_path)

        # Test metadata extraction
        print(f"\n📚 METADATA:")
        print(f"  Title: {book.title}")
        print(f"  Authors: {', '.join(book.authors)}")
        print(f"  Language: {book.language}")

        # Test chapter count
        chapter_count = book.get_chapter_count()
        print(f"\n📖 STRUCTURE:")
        print(f"  Chapters: {chapter_count}")
        print(f"  Manifest items: {len(book._manifest)}")

        # Test reading first chapter
        if chapter_count > 0:
            print(f"\n📄 FIRST CHAPTER (first 500 chars):")
            first_chapter = book.get_chapter_content(0)
            print(f"  Length: {len(first_chapter)} bytes")
            print(f"  Preview: {first_chapter[:500]}...")

        # Test reading last chapter
        if chapter_count > 1:
            print(f"\n📄 LAST CHAPTER (first 500 chars):")
            last_chapter = book.get_chapter_content(chapter_count - 1)
            print(f"  Length: {len(last_chapter)} bytes")
            print(f"  Preview: {last_chapter[:500]}...")

        print(f"\n✅ SUCCESS: {epub_file} loaded successfully!")

    except EReaderError as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'=' * 80}")
print("TESTING COMPLETE")
print("=" * 80)
