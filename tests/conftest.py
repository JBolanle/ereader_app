"""
Pytest configuration and shared fixtures.
"""

from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_epub(test_data_dir: Path) -> Path:
    """Path to a sample EPUB file for testing."""
    return test_data_dir / "sample.epub"


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Temporary directory for test outputs."""
    return tmp_path
