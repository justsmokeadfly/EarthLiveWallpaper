"""Shared visual constants for the EarthLive UI.

Centralizing colors/fonts here means `main_window.py` and
`settings_dialog.py` never hard-code hex values, keeping the interface
visually consistent and easy to re-theme later.
"""

from __future__ import annotations

# Primary palette (dark theme, evokes space/night-side Earth imagery).
COLOR_BACKGROUND = "#0d1117"
COLOR_SURFACE = "#161b22"
COLOR_SURFACE_ALT = "#1f2733"
COLOR_ACCENT = "#3ba7ff"
COLOR_ACCENT_HOVER = "#2d8ce0"
COLOR_TEXT_PRIMARY = "#e6edf3"
COLOR_TEXT_SECONDARY = "#8b949e"
COLOR_SUCCESS = "#3fb950"
COLOR_WARNING = "#d29922"
COLOR_ERROR = "#f85149"

FONT_FAMILY = "Segoe UI"
FONT_SIZE_TITLE = 20
FONT_SIZE_BODY = 13
FONT_SIZE_SMALL = 11

WINDOW_WIDTH = 480
WINDOW_HEIGHT = 560
WINDOW_TITLE = "EarthLive"

CORNER_RADIUS = 10
PADDING = 16
