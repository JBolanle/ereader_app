"""Theme definitions for the e-reader application.

This module provides the Theme dataclass and predefined themes (Light, Dark)
for the reading interface.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Represents a visual theme for the e-reader.

    A theme defines the comprehensive color palette and styling for the reading
    interface, including background, text, UI elements, and generates QSS stylesheets.

    Attributes:
        name: Display name for the theme (e.g., "Light", "Dark").
        background: Main background color as hex string (e.g., "#FAF8F5").
        surface: Surface/content background color as hex string (e.g., "#FFFFFF").
        text: Primary text color as hex string (e.g., "#2B2826").
        text_secondary: Secondary text color as hex string (e.g., "#6B6562").
        accent: Accent color for interactive elements as hex string (e.g., "#8B7355").
        border: Border color as hex string (e.g., "#E8E3DD").
        status_bg: Status bar background color as hex string (e.g., "#F5F1EB").
        shadow_color: Shadow color as hex string (default: "#000000").
        shadow_alpha: Shadow opacity (0-255, default: 15 for ~6% opacity).
        shadow_blur: Shadow blur radius in pixels (default: 8).
        shadow_offset_y: Shadow vertical offset in pixels (default: 2).
    """

    name: str
    background: str
    surface: str
    text: str
    text_secondary: str
    accent: str
    border: str
    status_bg: str
    shadow_color: str = "#000000"
    shadow_alpha: int = 15
    shadow_blur: int = 8
    shadow_offset_y: int = 2

    def get_global_stylesheet(self) -> str:
        """Generate global stylesheet (QSS) for application-wide styling.

        Returns:
            QSS stylesheet string with comprehensive styling for all Qt widgets.
        """
        return f"""
            /* Global widget defaults */
            QWidget {{
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                            "Segoe UI", system-ui, sans-serif;
                font-size: 13px;
                color: {self.text};
            }}

            /* Main window */
            QMainWindow {{
                background-color: {self.background};
            }}

            /* Menu bar */
            QMenuBar {{
                background-color: {self.background};
                color: {self.text};
                border-bottom: 1px solid {self.border};
                padding: 4px 8px;
            }}

            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }}

            QMenuBar::item:selected {{
                background-color: {self.accent};
                color: {self.surface};
            }}

            QMenuBar::item:pressed {{
                background-color: {self.accent};
                color: {self.surface};
            }}

            /* Menus (dropdowns) */
            QMenu {{
                background-color: {self.surface};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 6px;
                padding: 4px;
            }}

            QMenu::item {{
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
            }}

            QMenu::item:selected {{
                background-color: {self.accent};
                color: {self.surface};
            }}

            QMenu::separator {{
                height: 1px;
                background-color: {self.border};
                margin: 4px 8px;
            }}

            /* Status bar */
            QStatusBar {{
                background-color: {self.status_bg};
                color: {self.text};
                border-top: 1px solid {self.border};
                font-size: 13px;
                padding: 6px 12px;
            }}

            QStatusBar::item {{
                border: none;
            }}
        """

    def get_book_viewer_stylesheet(self) -> str:
        """Generate stylesheet for the book content viewer.

        Returns:
            QSS stylesheet string with typography and content styling.
        """
        return f"""
            QTextBrowser {{
                background-color: {self.surface};
                color: {self.text};
                border: none;
                padding: 40px 60px;
                font-family: Georgia, Palatino, "Palatino Linotype", serif;
                font-size: 18px;
                line-height: 1.7;
                selection-background-color: {self.accent};
                selection-color: {self.surface};
            }}

            /* Slim modern scrollbar */
            QTextBrowser QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }}

            QTextBrowser QScrollBar::handle:vertical {{
                background-color: {self.border};
                min-height: 30px;
                border-radius: 4px;
                margin: 2px;
            }}

            QTextBrowser QScrollBar::handle:vertical:hover {{
                background-color: {self.accent};
            }}

            QTextBrowser QScrollBar::add-line:vertical,
            QTextBrowser QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QTextBrowser QScrollBar::add-page:vertical,
            QTextBrowser QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
        """

    def get_navigation_bar_stylesheet(self) -> str:
        """Generate stylesheet for the navigation bar and buttons.

        Returns:
            QSS stylesheet string with button and layout styling.
        """
        return f"""
            NavigationBar {{
                background-color: {self.background};
                border-top: 1px solid {self.border};
            }}

            QPushButton {{
                background-color: transparent;
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }}

            QPushButton:hover:enabled {{
                background-color: {self.accent};
                color: {self.surface};
                border-color: {self.accent};
            }}

            QPushButton:pressed:enabled {{
                background-color: {self.accent};
                color: {self.surface};
            }}

            QPushButton:disabled {{
                color: {self.text_secondary};
                border-color: {self.border};
                background-color: transparent;
            }}

            QPushButton:focus {{
                border: 2px solid {self.accent};
            }}
        """


# Predefined theme: Light (Editorial Elegance - warm cream)
LIGHT_THEME = Theme(
    name="Light",
    background="#FAF8F5",  # Warm cream background
    surface="#FFFFFF",  # Pure white for content
    text="#2B2826",  # Warm charcoal text
    text_secondary="#6B6562",  # Muted brown-gray
    accent="#8B7355",  # Warm bronze
    border="#E8E3DD",  # Subtle warm gray
    status_bg="#F5F1EB",  # Slightly darker cream
)

# Predefined theme: Dark (Editorial Elegance - rich charcoal)
DARK_THEME = Theme(
    name="Dark",
    background="#1C1917",  # Rich charcoal background
    surface="#2B2826",  # Lighter charcoal for content
    text="#F5F1EB",  # Warm off-white text
    text_secondary="#A8A29E",  # Warm mid-gray
    accent="#C9A882",  # Warm gold
    border="#3F3B38",  # Subtle border
    status_bg="#252220",  # Slightly lighter than background
    shadow_alpha=25,  # Slightly stronger shadow for dark theme (~10% opacity)
)

# Registry of all available themes
AVAILABLE_THEMES: dict[str, Theme] = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}

# Default theme
DEFAULT_THEME = LIGHT_THEME
