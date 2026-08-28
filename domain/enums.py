"""Enumerations shared across the EarthLive domain layer.

These enums represent stable, provider-agnostic concepts. They contain no
third-party imports and no business logic beyond simple conversions.
"""

from __future__ import annotations

from enum import Enum


class GridSize(str, Enum):
    """Supported tile-grid resolutions for full-disk satellite imagery."""

    GRID_2X2 = "2x2"
    GRID_4X4 = "4x4"
    GRID_8X8 = "8x8"
    GRID_16X16 = "16x16"

    @property
    def dimension(self) -> int:
        """Return the number of tiles per side (e.g. 4 for '4x4')."""
        return int(self.value.split("x")[0])

    @property
    def tile_count(self) -> int:
        """Return the total number of tiles in the grid."""
        return self.dimension * self.dimension

    @classmethod
    def from_string(cls, value: str) -> GridSize:
        """Parse a grid size from a string such as '4x4'.

        Args:
            value: The raw string value (case-insensitive).

        Returns:
            The matching GridSize member.

        Raises:
            ValueError: If the value does not match any known grid size.
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown grid size '{value}'. Valid values: {valid}")


class WallpaperMode(str, Enum):
    """Windows desktop wallpaper positioning modes."""

    FILL = "fill"
    FIT = "fit"
    STRETCH = "stretch"
    TILE = "tile"
    CENTER = "center"
    SPAN = "span"

    @classmethod
    def from_string(cls, value: str) -> WallpaperMode:
        """Parse a wallpaper mode from a string.

        Args:
            value: The raw string value (case-insensitive).

        Returns:
            The matching WallpaperMode member.

        Raises:
            ValueError: If the value does not match any known mode.
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown wallpaper mode '{value}'. Valid values: {valid}")


class Theme(str, Enum):
    """UI color theme options."""

    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"

    @classmethod
    def from_string(cls, value: str) -> Theme:
        """Parse a theme from a string.

        Args:
            value: The raw string value (case-insensitive).

        Returns:
            The matching Theme member.

        Raises:
            ValueError: If the value does not match any known theme.
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown theme '{value}'. Valid values: {valid}")


class UpdateOutcome(str, Enum):
    """Possible outcomes of a single update cycle attempt."""

    SUCCESS = "success"
    ALREADY_UP_TO_DATE = "already_up_to_date"
    DUPLICATE_CONTENT = "duplicate_content"
    NETWORK_UNAVAILABLE = "network_unavailable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    DOWNLOAD_FAILED = "download_failed"
    ASSEMBLY_FAILED = "assembly_failed"
    WALLPAPER_APPLY_FAILED = "wallpaper_apply_failed"
    UNEXPECTED_ERROR = "unexpected_error"
    PAUSED = "paused"


class Language(str, Enum):
    """Supported UI display languages."""

    EN = "en"
    RU = "ru"

    @classmethod
    def from_string(cls, value: str) -> Language:
        """Parse a language from a string.

        Args:
            value: The raw string value (case-insensitive).

        Returns:
            The matching Language member.

        Raises:
            ValueError: If the value does not match any known language.
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown language '{value}'. Valid values: {valid}")
