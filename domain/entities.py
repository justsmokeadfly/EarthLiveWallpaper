"""Core domain entities for EarthLive."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from domain.enums import GridSize, Language, Theme, UpdateOutcome, WallpaperMode


@dataclass(frozen=True)
class TileSpec:
    url: str
    column: int
    row: int
    cache_key: str


@dataclass(frozen=True)
class SatelliteImage:
    provider_name: str
    timestamp: datetime
    grid_size: GridSize
    tiles: tuple[TileSpec, ...]


@dataclass(frozen=True)
class AssembledImage:
    source: SatelliteImage
    file_path: Path
    content_hash: str
    width: int
    height: int


@dataclass
class AppState:
    last_timestamp: datetime | None = None
    last_content_hash: str | None = None
    last_update_at: datetime | None = None
    last_successful_update_at: datetime | None = None
    last_outcome: UpdateOutcome | None = None
    history: list[str] = field(default_factory=list)
    total_updates_applied: int = 0


@dataclass
class AppConfig:
    provider: str = "himawari"
    grid_size: GridSize = GridSize.GRID_4X4
    check_interval_hours: float = 24.0
    history_size: int = 10
    theme: Theme = Theme.DARK
    autostart: bool = False
    wallpaper_mode: WallpaperMode = WallpaperMode.FIT
    retry_count: int = 3
    retry_delay_seconds: float = 5.0
    max_cache_age_hours: float = 48.0
    max_cache_size_mb: int = 500
    language: Language = Language.RU
    paused: bool = False
    space_mix_enabled: bool = False
    space_mix_interval_hours: float = 24.0
