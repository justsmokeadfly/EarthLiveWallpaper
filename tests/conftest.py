"""Shared pytest fixtures for the EarthLive test suite."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from domain.entities import SatelliteImage, TileSpec
from domain.enums import GridSize


@pytest.fixture
def sample_timestamp() -> datetime:
    """A fixed UTC timestamp used across multiple tests."""
    return datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_tiles() -> tuple[TileSpec, ...]:
    """A minimal 2x2 grid of tile specs for assembler/downloader tests."""
    return tuple(
        TileSpec(
            url=f"https://example.invalid/tile_{col}_{row}.png",
            column=col,
            row=row,
            cache_key=f"tile_{col}_{row}.png",
        )
        for row in range(2)
        for col in range(2)
    )


@pytest.fixture
def sample_satellite_image(
    sample_timestamp: datetime, sample_tiles: tuple[TileSpec, ...]
) -> SatelliteImage:
    """A minimal SatelliteImage built from ``sample_tiles``."""
    return SatelliteImage(
        provider_name="testprovider",
        timestamp=sample_timestamp,
        grid_size=GridSize.GRID_2X2,
        tiles=sample_tiles,
    )


@pytest.fixture
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    """A set of temporary directories mimicking the app's runtime layout."""
    dirs = {
        "cache": tmp_path / "cache",
        "wallpapers": tmp_path / "wallpapers",
        "logs": tmp_path / "logs",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    return dirs
