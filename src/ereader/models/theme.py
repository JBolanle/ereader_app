"""Theme definitions for the e-reader application.

This module provides the Theme dataclass and predefined themes (Light, Dark)
for the reading interface.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Represents a visual theme for the e-reader.

    A theme defines the color palette for the reading interface, including
    background, text, and status bar colors.

    Attributes:
        name: Display name for the theme (e.g., "Light", "Dark").
        background: Background color as hex string (e.g., "#ffffff").
        text: Text color as hex string (e.g., "#1a1a1a").
        status_bg: Status bar background color as hex string (e.g., "#f5f5f5").
    """

    name: str
    background: str
    text: str
    status_bg: str


# Predefined theme: Light (default)
LIGHT_THEME = Theme(
    name="Light",
    background="#ffffff",
    text="#1a1a1a",
    status_bg="#f5f5f5",
)

# Predefined theme: Dark
DARK_THEME = Theme(
    name="Dark",
    background="#1e1e1e",
    text="#e0e0e0",
    status_bg="#252526",
)

# Registry of all available themes
AVAILABLE_THEMES: dict[str, Theme] = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}

# Default theme
DEFAULT_THEME = LIGHT_THEME
