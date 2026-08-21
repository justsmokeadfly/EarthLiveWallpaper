"""Core domain entities for EarthLive.

These are plain, immutable-where-possible data structures with no
dependency on any infrastructure library (no httpx, no Pillow, no Win32).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from domain.enums import GridSize, Language, Theme, UpdateOutcome, WallpaperMode


@dataclass(frozen=True)
class TileSpec:
    """Describes a single downloadable tile within a satellite image grid.

    Attributes:
        url: Fully-qualified URL of the tile image.
        column: Zero-based column index within the grid.
        row: Zero-based row index within the grid.
        cache_key: A stable, filesystem-safe identifier used to name the
            cached tile file on disk, unique per (provider, timestamp,
            grid size, column, row).
    """

    url: str
    column: int
    row: int
    cache_key: str


@dataclass(frozen=True)
class SatelliteImage:
    """Represents a full-disk satellite image request/result.

    Attributes:
        provider_name: Name of the provider that produced this image
            (e.g. "himawari").
        timestamp: The UTC timestamp this image represents, as reported by
            the provider.
        grid_size: The tile grid resolution used to assemble this image.
        tiles: The ordered list of tile specifications required to
            assemble the full image.
    """

    provider_name: str
    timestamp: datetime
    grid_size: GridSize
    tiles: tuple[TileSpec, ...]


@dataclass(frozen=True)
class AssembledImage:
    """Represents a fully assembled, saved satellite image.

    Attributes:
        source: The SatelliteImage metadata this was assembled from.
        file_path: Path to the saved PNG file on disk.
        content_hash: SHA-256 hex digest of the assembled image bytes,
            used for duplicate-content detection.
        width: Pixel width of the assembled image.
        height: Pixel height of the assembled image.
    """

    source: SatelliteImage
    file_path: Path
    content_hash: str
    width: int
    height: int


@dataclass
class AppState:
    """Persistent application state, independent of user-editable config.

    Attributes:
        last_timestamp: UTC timestamp of the last image successfully
            considered (may equal the currently applied wallpaper's
            timestamp or a duplicate that was skipped).
        last_content_hash: SHA-256 hash of the last assembled image
            content, used to detect duplicate imagery under a new
            timestamp.
        last_update_at: Wall-clock time of the last update *attempt*
            (successful or not), used to compute "next update" in the UI.
        last_successful_update_at: Wall-clock time of the last update that
            actually resulted in a new wallpaper being applied.
        last_outcome: The outcome of the most recent update cycle.
        history: Ordered list of previously applied wallpaper file paths,
            most recent first, capped at the configured history size.
        total_updates_applied: Lifetime counter of successful wallpaper
            changes, for display/diagnostics.
    """

    last_timestamp: datetime | None = None
    last_content_hash: str | None = None
    last_update_at: datetime | None = None
    last_successful_update_at: datetime | None = None
    last_outcome: UpdateOutcome | None = None
    history: list[str] = field(default_factory=list)
    total_updates_applied: int = 0


@dataclass
class AppConfig:
    """User-editable application configuration.

    Attributes:
        provider: Name of the active image provider (e.g. "himawari").
        grid_size: Selected tile grid resolution.
        check_interval_hours: Hours between automatic update checks.
        history_size: Maximum number of wallpapers retained in history.
        theme: UI color theme.
        autostart: Whether EarthLive should launch on Windows login.
        wallpaper_mode: Desktop wallpaper positioning mode.
        retry_count: Maximum retry attempts per failed tile download.
        retry_delay_seconds: Base delay (seconds) used for exponential
            backoff between tile download retries.
        max_cache_age_hours: Maximum age of cached tiles before they are
            eligible for pruning.
        max_cache_size_mb: Soft cap on total cache directory size in
            megabytes; oldest files are pruned first when exceeded.
        language: UI display language.
        paused: When true, the update use case short-circuits immediately
            (no network/provider check at all) without touching the
            current wallpaper. Toggled from the main window.
    """

    provider: str = "himawari"
    grid_size: GridSize = GridSize.GRID_4X4
    check_interval_hours: float = 24.0
    history_size: int = 10
    theme: Theme = Theme.DARK
    autostart: bool = False
    wallpaper_mode: WallpaperMode = WallpaperMode.FILL
    retry_count: int = 3
    retry_delay_seconds: float = 5.0
    max_cache_age_hours: float = 48.0
    max_cache_size_mb: int = 500
    language: Language = Language.RU
    paused: bool = False
