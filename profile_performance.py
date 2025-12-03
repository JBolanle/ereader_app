"""Performance profiling script for EPUB reader.

This script measures:
- EPUB loading time
- Page/chapter loading time
- Memory usage
- Image resolution time

Usage:
    uv run python profile_performance.py [epub_path]

Dependencies:
    Requires psutil: uv add psutil
"""

import argparse
import gc
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    print("ERROR: psutil is required for memory profiling.")
    print("Please install it with: uv add psutil")
    sys.exit(1)

from ereader.models.epub import EPUBBook
from ereader.utils.cache import ChapterCache
from ereader.utils.html_resources import resolve_images_in_html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_memory_usage() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # Convert bytes to MB


def profile_epub_loading(epub_path: str) -> tuple[dict[str, Any], EPUBBook]:
    """Profile EPUB file loading performance.

    Args:
        epub_path: Path to the EPUB file to profile.

    Returns:
        Tuple of (profiling results dictionary, loaded EPUBBook instance).
    """
    results: dict[str, Any] = {
        "file_path": epub_path,
        "file_size_mb": Path(epub_path).stat().st_size / 1024 / 1024,
    }

    # Force garbage collection before measurement
    gc.collect()

    # Measure initial memory
    memory_before = get_memory_usage()

    # Profile EPUB loading
    start_time = time.perf_counter()
    book = EPUBBook(epub_path)
    load_time = time.perf_counter() - start_time

    memory_after_load = get_memory_usage()

    results["load_time_ms"] = load_time * 1000
    results["memory_after_load_mb"] = memory_after_load
    results["memory_increase_mb"] = memory_after_load - memory_before

    # Get book metadata
    results["metadata"] = {
        "title": book.title,
        "authors": book.authors,
        "language": book.language,
        "chapter_count": book.get_chapter_count(),
    }

    return results, book


def profile_chapter_loading(book: EPUBBook, sample_size: int = 10) -> dict[str, Any]:
    """Profile chapter loading performance.

    Args:
        book: The EPUBBook instance.
        sample_size: Number of chapters to sample (default: 10).

    Returns:
        Dictionary with chapter loading profiling results.
    """
    chapter_count = book.get_chapter_count()
    sample_size = min(sample_size, chapter_count)

    # Sample chapters evenly throughout the book
    if chapter_count <= sample_size:
        chapter_indices = list(range(chapter_count))
    else:
        step = chapter_count / sample_size
        chapter_indices = [int(i * step) for i in range(sample_size)]

    results: dict[str, Any] = {
        "total_chapters": chapter_count,
        "sampled_chapters": sample_size,
        "chapter_times_ms": [],
        "chapter_sizes_bytes": [],
    }

    for idx in chapter_indices:
        # Profile getting chapter content
        start_time = time.perf_counter()
        content = book.get_chapter_content(idx)
        chapter_time = time.perf_counter() - start_time

        results["chapter_times_ms"].append(chapter_time * 1000)
        results["chapter_sizes_bytes"].append(len(content))

    # Calculate statistics
    times = results["chapter_times_ms"]
    results["min_time_ms"] = min(times)
    results["max_time_ms"] = max(times)
    results["avg_time_ms"] = sum(times) / len(times)
    results["median_time_ms"] = sorted(times)[len(times) // 2]

    return results


def profile_image_resolution(book: EPUBBook, sample_size: int = 5) -> dict[str, Any]:
    """Profile image resolution performance.

    Args:
        book: The EPUBBook instance.
        sample_size: Number of chapters with images to sample.

    Returns:
        Dictionary with image resolution profiling results.
    """
    chapter_count = book.get_chapter_count()
    results: dict[str, Any] = {
        "chapters_checked": 0,
        "chapters_with_images": 0,
        "total_images": 0,
        "resolution_times_ms": [],
    }

    chapters_with_images_found = 0

    for idx in range(chapter_count):
        if chapters_with_images_found >= sample_size:
            break

        results["chapters_checked"] += 1

        try:
            chapter_href = book.get_chapter_href(idx)
            content = book.get_chapter_content(idx)

            # Check if chapter has images
            if "<img" not in content.lower():
                continue

            results["chapters_with_images"] += 1
            chapters_with_images_found += 1

            # Profile image resolution
            start_time = time.perf_counter()
            _ = resolve_images_in_html(content, book, chapter_href=chapter_href)
            resolution_time = time.perf_counter() - start_time

            results["resolution_times_ms"].append(resolution_time * 1000)

            # Count images
            img_count = len(re.findall(r'<img[^>]+>', content, re.IGNORECASE))
            results["total_images"] += img_count

        except Exception as e:
            logger.warning("Error processing chapter %d: %s", idx, e)
            continue

    # Calculate statistics if we found images
    if results["resolution_times_ms"]:
        times = results["resolution_times_ms"]
        results["min_time_ms"] = min(times)
        results["max_time_ms"] = max(times)
        results["avg_time_ms"] = sum(times) / len(times)

    return results


def profile_memory_over_time(book: EPUBBook, num_chapters: int = 20) -> dict[str, Any]:
    """Profile memory usage over multiple chapter loads.

    Args:
        book: The EPUBBook instance.
        num_chapters: Number of chapters to load sequentially.

    Returns:
        Dictionary with memory profiling results.
    """
    chapter_count = book.get_chapter_count()
    num_chapters = min(num_chapters, chapter_count)

    results: dict[str, Any] = {
        "chapters_loaded": num_chapters,
        "memory_snapshots_mb": [],
    }

    # Take initial memory snapshot
    gc.collect()
    results["memory_snapshots_mb"].append(get_memory_usage())

    # Load chapters and measure memory
    for idx in range(num_chapters):
        try:
            chapter_href = book.get_chapter_href(idx)
            content = book.get_chapter_content(idx)
            # Resolve images to simulate real usage (memory impact)
            _ = resolve_images_in_html(content, book, chapter_href=chapter_href)

            # Take memory snapshot
            results["memory_snapshots_mb"].append(get_memory_usage())

        except Exception as e:
            logger.warning("Error loading chapter %d: %s", idx, e)

    # Calculate statistics
    snapshots = results["memory_snapshots_mb"]
    results["min_memory_mb"] = min(snapshots)
    results["max_memory_mb"] = max(snapshots)
    results["avg_memory_mb"] = sum(snapshots) / len(snapshots)
    results["memory_growth_mb"] = snapshots[-1] - snapshots[0]

    return results


def profile_caching_benefit(book: EPUBBook, num_chapters: int = 20) -> dict[str, Any]:
    """Profile memory usage with caching enabled.

    Simulates realistic reading patterns to measure cache effectiveness.

    Args:
        book: The EPUBBook instance.
        num_chapters: Number of chapters to load in reading pattern.

    Returns:
        Dictionary with caching profiling results.
    """
    chapter_count = book.get_chapter_count()
    num_chapters = min(num_chapters, chapter_count)

    # Initialize cache
    cache = ChapterCache(maxsize=10)

    results: dict[str, Any] = {
        "chapters_accessed": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "memory_snapshots_mb": [],
    }

    # Take initial memory snapshot
    gc.collect()
    results["memory_snapshots_mb"].append(get_memory_usage())

    # Simulate realistic reading pattern:
    # - Read forward through chapters
    # - Occasionally go back to review previous chapter
    for idx in range(num_chapters):
        try:
            # Generate cache key
            cache_key = f"{book.filepath}:{idx}"
            results["chapters_accessed"] += 1

            # Try cache first
            cached_html = cache.get(cache_key)
            if cached_html is not None:
                results["cache_hits"] += 1
                # Use cached content (just access it)
                _ = cached_html
            else:
                results["cache_misses"] += 1
                # Cache miss - render and store
                chapter_href = book.get_chapter_href(idx)
                content = book.get_chapter_content(idx)
                rendered = resolve_images_in_html(content, book, chapter_href=chapter_href)
                cache.set(cache_key, rendered)

            # Take memory snapshot
            results["memory_snapshots_mb"].append(get_memory_usage())

            # Occasionally go back one chapter (simulates review reading)
            if idx > 0 and idx % 5 == 0:
                prev_idx = idx - 1
                prev_key = f"{book.filepath}:{prev_idx}"
                results["chapters_accessed"] += 1

                # This should be a cache hit
                cached = cache.get(prev_key)
                if cached is not None:
                    results["cache_hits"] += 1
                else:
                    results["cache_misses"] += 1

        except Exception as e:
            logger.warning("Error loading chapter %d: %s", idx, e)

    # Calculate statistics
    snapshots = results["memory_snapshots_mb"]
    results["min_memory_mb"] = min(snapshots)
    results["max_memory_mb"] = max(snapshots)
    results["avg_memory_mb"] = sum(snapshots) / len(snapshots)
    results["memory_growth_mb"] = snapshots[-1] - snapshots[0]

    # Calculate hit rate
    total_accesses = results["cache_hits"] + results["cache_misses"]
    results["hit_rate_percent"] = (results["cache_hits"] / total_accesses * 100) if total_accesses > 0 else 0.0

    # Get final cache stats
    cache_stats = cache.stats()
    results["cache_stats"] = cache_stats

    return results


def generate_report(
    epub_results: dict[str, Any],
    chapter_results: dict[str, Any],
    image_results: dict[str, Any],
    memory_results: dict[str, Any],
    cache_results: dict[str, Any] | None = None,
) -> str:
    """Generate a formatted performance report.

    Args:
        epub_results: Results from EPUB loading profiling.
        chapter_results: Results from chapter loading profiling.
        image_results: Results from image resolution profiling.
        memory_results: Results from memory profiling.

    Returns:
        Formatted report string.
    """
    report = []
    report.append("=" * 80)
    report.append("EPUB READER PERFORMANCE REPORT")
    report.append("=" * 80)
    report.append("")

    # EPUB Loading
    report.append("## EPUB Loading Performance")
    report.append(f"File: {epub_results['file_path']}")
    report.append(f"Size: {epub_results['file_size_mb']:.2f} MB")
    report.append(f"Title: {epub_results['metadata']['title']}")
    report.append(f"Authors: {', '.join(epub_results['metadata']['authors'])}")
    report.append(f"Chapters: {epub_results['metadata']['chapter_count']}")
    report.append("")
    report.append(f"Load Time: {epub_results['load_time_ms']:.2f} ms")
    report.append(f"Memory After Load: {epub_results['memory_after_load_mb']:.2f} MB")
    report.append(f"Memory Increase: {epub_results['memory_increase_mb']:.2f} MB")
    report.append("")

    # Target evaluation
    load_status = "✅ PASS" if epub_results['load_time_ms'] < 100 else "⚠️  SLOW"
    memory_status = "✅ PASS" if epub_results['memory_after_load_mb'] < 200 else "⚠️  HIGH"
    report.append(f"Target Check (< 100ms load): {load_status}")
    report.append(f"Target Check (< 200MB memory): {memory_status}")
    report.append("")

    # Chapter Loading
    report.append("## Chapter Loading Performance")
    report.append(f"Sampled: {chapter_results['sampled_chapters']} / {chapter_results['total_chapters']} chapters")
    report.append(f"Min Time: {chapter_results['min_time_ms']:.2f} ms")
    report.append(f"Max Time: {chapter_results['max_time_ms']:.2f} ms")
    report.append(f"Avg Time: {chapter_results['avg_time_ms']:.2f} ms")
    report.append(f"Median Time: {chapter_results['median_time_ms']:.2f} ms")
    report.append("")

    chapter_status = "✅ PASS" if chapter_results['avg_time_ms'] < 100 else "⚠️  SLOW"
    report.append(f"Target Check (< 100ms avg): {chapter_status}")
    report.append("")

    # Image Resolution
    report.append("## Image Resolution Performance")
    report.append(f"Chapters Checked: {image_results['chapters_checked']}")
    report.append(f"Chapters with Images: {image_results['chapters_with_images']}")
    report.append(f"Total Images Found: {image_results['total_images']}")

    if image_results['resolution_times_ms']:
        report.append(f"Min Resolution Time: {image_results['min_time_ms']:.2f} ms")
        report.append(f"Max Resolution Time: {image_results['max_time_ms']:.2f} ms")
        report.append(f"Avg Resolution Time: {image_results['avg_time_ms']:.2f} ms")

        image_status = "✅ PASS" if image_results['avg_time_ms'] < 100 else "⚠️  SLOW"
        report.append(f"Target Check (< 100ms avg): {image_status}")
    else:
        report.append("No images found in sampled chapters")
    report.append("")

    # Memory Over Time
    report.append("## Memory Usage Over Time")
    report.append(f"Chapters Loaded: {memory_results['chapters_loaded']}")
    report.append(f"Min Memory: {memory_results['min_memory_mb']:.2f} MB")
    report.append(f"Max Memory: {memory_results['max_memory_mb']:.2f} MB")
    report.append(f"Avg Memory: {memory_results['avg_memory_mb']:.2f} MB")
    report.append(f"Memory Growth: {memory_results['memory_growth_mb']:.2f} MB")
    report.append("")

    memory_status = "✅ PASS" if memory_results['max_memory_mb'] < 200 else "⚠️  HIGH"
    report.append(f"Target Check (< 200MB max): {memory_status}")
    report.append("")

    # Caching Performance (if available)
    if cache_results:
        report.append("## Caching Performance")
        report.append(f"Chapters Accessed: {cache_results['chapters_accessed']}")
        report.append(f"Cache Hits: {cache_results['cache_hits']}")
        report.append(f"Cache Misses: {cache_results['cache_misses']}")
        report.append(f"Hit Rate: {cache_results['hit_rate_percent']:.1f}%")
        report.append("")
        report.append(f"Min Memory: {cache_results['min_memory_mb']:.2f} MB")
        report.append(f"Max Memory: {cache_results['max_memory_mb']:.2f} MB")
        report.append(f"Avg Memory: {cache_results['avg_memory_mb']:.2f} MB")
        report.append(f"Memory Growth: {cache_results['memory_growth_mb']:.2f} MB")
        report.append("")

        # Compare with non-cached version
        memory_improvement = memory_results['max_memory_mb'] - cache_results['max_memory_mb']
        improvement_percent = (memory_improvement / memory_results['max_memory_mb'] * 100) if memory_results['max_memory_mb'] > 0 else 0

        report.append("## Caching Impact")
        report.append(f"Memory Without Cache: {memory_results['max_memory_mb']:.2f} MB")
        report.append(f"Memory With Cache: {cache_results['max_memory_mb']:.2f} MB")
        report.append(f"Memory Reduction: {memory_improvement:.2f} MB ({improvement_percent:.1f}% improvement)")
        report.append("")

        cache_status = "✅ EFFECTIVE" if cache_results['hit_rate_percent'] > 50 else "⚠️  LOW HIT RATE"
        memory_cache_status = "✅ PASS" if cache_results['max_memory_mb'] < 200 else "⚠️  HIGH"
        report.append(f"Cache Effectiveness: {cache_status}")
        report.append(f"Target Check (< 200MB max with cache): {memory_cache_status}")
        report.append("")

    # Overall Assessment
    report.append("=" * 80)
    report.append("## Overall Assessment")
    report.append("")

    all_pass = (
        epub_results['load_time_ms'] < 100 and
        epub_results['memory_after_load_mb'] < 200 and
        chapter_results['avg_time_ms'] < 100 and
        memory_results['max_memory_mb'] < 200
    )

    if all_pass:
        report.append("✅ ALL PERFORMANCE TARGETS MET")
    else:
        report.append("⚠️  SOME PERFORMANCE TARGETS NOT MET")
        report.append("")
        report.append("Recommendations:")
        if epub_results['load_time_ms'] >= 100:
            report.append("- EPUB loading is slow. Consider lazy loading or caching metadata.")
        if chapter_results['avg_time_ms'] >= 100:
            report.append("- Chapter loading is slow. Consider caching or optimizing XML parsing.")
        if memory_results['max_memory_mb'] >= 200:
            report.append("- Memory usage is high. Consider implementing LRU cache for chapters.")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def main() -> None:
    """Main profiling function."""
    parser = argparse.ArgumentParser(description="Profile EPUB reader performance")
    parser.add_argument(
        "epub_path",
        nargs="?",
        default="scratch/EPUBS/The Mamba Mentality How I Play (Bryant, Kobe) (Z-Library).epub",
        help="Path to EPUB file (default: Mamba Mentality)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for report (default: print to stdout)",
    )

    args = parser.parse_args()

    if not Path(args.epub_path).exists():
        logger.error("EPUB file not found: %s", args.epub_path)
        sys.exit(1)

    logger.info("Profiling: %s", args.epub_path)
    logger.info("File size: %.2f MB", Path(args.epub_path).stat().st_size / 1024 / 1024)
    logger.info("")

    # Run profiling
    logger.info("Phase 1: Profiling EPUB loading...")
    epub_results, book = profile_epub_loading(args.epub_path)

    logger.info("Phase 2: Profiling chapter loading...")
    chapter_results = profile_chapter_loading(book, sample_size=10)

    logger.info("Phase 3: Profiling image resolution...")
    image_results = profile_image_resolution(book, sample_size=5)

    logger.info("Phase 4: Profiling memory usage over time...")
    memory_results = profile_memory_over_time(book, num_chapters=20)

    logger.info("Phase 5: Profiling caching benefit...")
    cache_results = profile_caching_benefit(book, num_chapters=20)

    logger.info("")
    logger.info("Generating report...")
    logger.info("")

    # Generate report
    report = generate_report(epub_results, chapter_results, image_results, memory_results, cache_results)

    # Output report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)
        logger.info("Report written to: %s", args.output)
    else:
        # Print report to stdout (not using logger for report output)
        print(report)


if __name__ == "__main__":
    main()
