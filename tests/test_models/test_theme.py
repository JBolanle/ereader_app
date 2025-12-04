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
            surface="#111111",
            text="#ffffff",
            text_secondary="#cccccc",
            accent="#ff0000",
            border="#444444",
            status_bg="#333333",
        )

        assert theme.name == "Test Theme"
        assert theme.background == "#000000"
        assert theme.surface == "#111111"
        assert theme.text == "#ffffff"
        assert theme.text_secondary == "#cccccc"
        assert theme.accent == "#ff0000"
        assert theme.border == "#444444"
        assert theme.status_bg == "#333333"

    def test_theme_immutable(self) -> None:
        """Test that Theme instances are immutable (frozen)."""
        theme = Theme(
            name="Test",
            background="#000000",
            surface="#111111",
            text="#ffffff",
            text_secondary="#cccccc",
            accent="#ff0000",
            border="#444444",
            status_bg="#333333",
        )

        with pytest.raises(AttributeError):
            theme.name = "Modified"  # type: ignore[misc]

    def test_theme_equality(self) -> None:
        """Test that identical themes are equal."""
        theme1 = Theme(
            name="Test",
            background="#000000",
            surface="#111111",
            text="#ffffff",
            text_secondary="#cccccc",
            accent="#ff0000",
            border="#444444",
            status_bg="#333333",
        )
        theme2 = Theme(
            name="Test",
            background="#000000",
            surface="#111111",
            text="#ffffff",
            text_secondary="#cccccc",
            accent="#ff0000",
            border="#444444",
            status_bg="#333333",
        )

        assert theme1 == theme2

    def test_theme_inequality(self) -> None:
        """Test that different themes are not equal."""
        theme1 = Theme(
            name="Light",
            background="#FAF8F5",
            surface="#FFFFFF",
            text="#2B2826",
            text_secondary="#6B6562",
            accent="#8B7355",
            border="#E8E3DD",
            status_bg="#F5F1EB",
        )
        theme2 = Theme(
            name="Dark",
            background="#1C1917",
            surface="#2B2826",
            text="#F5F1EB",
            text_secondary="#A8A29E",
            accent="#C9A882",
            border="#3F3B38",
            status_bg="#252220",
        )

        assert theme1 != theme2


class TestPredefinedThemes:
    """Tests for predefined theme constants."""

    def test_light_theme_properties(self) -> None:
        """Test Light theme has correct Editorial Elegance properties."""
        assert LIGHT_THEME.name == "Light"
        assert LIGHT_THEME.background == "#FAF8F5"  # Warm cream
        assert LIGHT_THEME.surface == "#FFFFFF"  # Pure white
        assert LIGHT_THEME.text == "#2B2826"  # Warm charcoal
        assert LIGHT_THEME.text_secondary == "#6B6562"  # Muted brown-gray
        assert LIGHT_THEME.accent == "#8B7355"  # Warm bronze
        assert LIGHT_THEME.border == "#E8E3DD"  # Subtle warm gray
        assert LIGHT_THEME.status_bg == "#F5F1EB"  # Darker cream

    def test_dark_theme_properties(self) -> None:
        """Test Dark theme has correct Editorial Elegance properties."""
        assert DARK_THEME.name == "Dark"
        assert DARK_THEME.background == "#1C1917"  # Rich charcoal
        assert DARK_THEME.surface == "#2B2826"  # Lighter charcoal
        assert DARK_THEME.text == "#F5F1EB"  # Warm off-white
        assert DARK_THEME.text_secondary == "#A8A29E"  # Warm mid-gray
        assert DARK_THEME.accent == "#C9A882"  # Warm gold
        assert DARK_THEME.border == "#3F3B38"  # Subtle border
        assert DARK_THEME.status_bg == "#252220"  # Slightly lighter than bg

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


class TestThemeStylesheets:
    """Tests for Theme stylesheet generation methods."""

    def test_get_global_stylesheet_returns_string(self) -> None:
        """Test that get_global_stylesheet returns a non-empty string."""
        stylesheet = LIGHT_THEME.get_global_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_get_global_stylesheet_contains_theme_colors(self) -> None:
        """Test that global stylesheet includes theme colors."""
        stylesheet = LIGHT_THEME.get_global_stylesheet()
        assert LIGHT_THEME.background in stylesheet
        assert LIGHT_THEME.text in stylesheet
        assert LIGHT_THEME.accent in stylesheet

    def test_get_book_viewer_stylesheet_returns_string(self) -> None:
        """Test that get_book_viewer_stylesheet returns a non-empty string."""
        stylesheet = LIGHT_THEME.get_book_viewer_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_get_book_viewer_stylesheet_contains_theme_colors(self) -> None:
        """Test that book viewer stylesheet includes theme colors."""
        stylesheet = LIGHT_THEME.get_book_viewer_stylesheet()
        assert LIGHT_THEME.surface in stylesheet
        assert LIGHT_THEME.text in stylesheet

    def test_get_navigation_bar_stylesheet_returns_string(self) -> None:
        """Test that get_navigation_bar_stylesheet returns a non-empty string."""
        stylesheet = LIGHT_THEME.get_navigation_bar_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_get_navigation_bar_stylesheet_contains_theme_colors(self) -> None:
        """Test that navigation bar stylesheet includes theme colors."""
        stylesheet = LIGHT_THEME.get_navigation_bar_stylesheet()
        assert LIGHT_THEME.background in stylesheet
        assert LIGHT_THEME.accent in stylesheet
        assert LIGHT_THEME.border in stylesheet

    def test_dark_theme_stylesheet_different_from_light(self) -> None:
        """Test that Dark theme generates different stylesheets."""
        light_stylesheet = LIGHT_THEME.get_global_stylesheet()
        dark_stylesheet = DARK_THEME.get_global_stylesheet()
        assert light_stylesheet != dark_stylesheet
