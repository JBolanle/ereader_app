"""Tests for the theme data model."""

import pytest

from ereader.models.theme import (
    AVAILABLE_THEMES,
    DEFAULT_THEME,
    DARK_THEME,
    LIGHT_THEME,
    Theme,
)


class TestTheme:
    """Tests for Theme dataclass."""

    def test_theme_creation(self) -> None:
        """Test creating a Theme instance."""
        theme = Theme(
            name="Test Theme",
            background="#000000",
            text="#ffffff",
            status_bg="#333333",
        )

        assert theme.name == "Test Theme"
        assert theme.background == "#000000"
        assert theme.text == "#ffffff"
        assert theme.status_bg == "#333333"

    def test_theme_immutable(self) -> None:
        """Test that Theme instances are immutable (frozen)."""
        theme = Theme(
            name="Test",
            background="#000000",
            text="#ffffff",
            status_bg="#333333",
        )

        with pytest.raises(AttributeError):
            theme.name = "Modified"  # type: ignore[misc]

    def test_theme_equality(self) -> None:
        """Test that identical themes are equal."""
        theme1 = Theme(
            name="Test",
            background="#000000",
            text="#ffffff",
            status_bg="#333333",
        )
        theme2 = Theme(
            name="Test",
            background="#000000",
            text="#ffffff",
            status_bg="#333333",
        )

        assert theme1 == theme2

    def test_theme_inequality(self) -> None:
        """Test that different themes are not equal."""
        theme1 = Theme(
            name="Light",
            background="#ffffff",
            text="#000000",
            status_bg="#f5f5f5",
        )
        theme2 = Theme(
            name="Dark",
            background="#1e1e1e",
            text="#e0e0e0",
            status_bg="#252526",
        )

        assert theme1 != theme2


class TestPredefinedThemes:
    """Tests for predefined theme constants."""

    def test_light_theme_properties(self) -> None:
        """Test Light theme has correct properties."""
        assert LIGHT_THEME.name == "Light"
        assert LIGHT_THEME.background == "#ffffff"
        assert LIGHT_THEME.text == "#1a1a1a"
        assert LIGHT_THEME.status_bg == "#f5f5f5"

    def test_dark_theme_properties(self) -> None:
        """Test Dark theme has correct properties."""
        assert DARK_THEME.name == "Dark"
        assert DARK_THEME.background == "#1e1e1e"
        assert DARK_THEME.text == "#e0e0e0"
        assert DARK_THEME.status_bg == "#252526"

    def test_default_theme_is_light(self) -> None:
        """Test that default theme is Light."""
        assert DEFAULT_THEME == LIGHT_THEME

    def test_available_themes_registry(self) -> None:
        """Test AVAILABLE_THEMES contains all predefined themes."""
        assert "light" in AVAILABLE_THEMES
        assert "dark" in AVAILABLE_THEMES
        assert AVAILABLE_THEMES["light"] == LIGHT_THEME
        assert AVAILABLE_THEMES["dark"] == DARK_THEME

    def test_available_themes_count(self) -> None:
        """Test AVAILABLE_THEMES has expected number of themes."""
        assert len(AVAILABLE_THEMES) == 2
