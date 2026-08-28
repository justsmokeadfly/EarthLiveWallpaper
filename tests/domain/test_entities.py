"""Unit tests for domain entities and enums."""

from __future__ import annotations

import pytest

from domain.enums import GridSize, Theme, UpdateOutcome, WallpaperMode


class TestGridSize:
    """Tests for the GridSize enum."""

    @pytest.mark.parametrize(
        ("value", "expected_dimension", "expected_tile_count"),
        [
            ("2x2", 2, 4),
            ("4x4", 4, 16),
            ("8x8", 8, 64),
            ("16x16", 16, 256),
        ],
    )
    def test_dimension_and_tile_count(
        self, value: str, expected_dimension: int, expected_tile_count: int
    ) -> None:
        grid = GridSize.from_string(value)
        assert grid.dimension == expected_dimension
        assert grid.tile_count == expected_tile_count

    def test_from_string_case_insensitive(self) -> None:
        assert GridSize.from_string("4X4") == GridSize.GRID_4X4

    def test_from_string_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            GridSize.from_string("not_a_grid")


class TestWallpaperMode:
    """Tests for the WallpaperMode enum."""

    def test_from_string_valid(self) -> None:
        assert WallpaperMode.from_string("fill") == WallpaperMode.FILL
        assert WallpaperMode.from_string("SPAN") == WallpaperMode.SPAN

    def test_from_string_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            WallpaperMode.from_string("bogus_mode")


class TestTheme:
    """Tests for the Theme enum."""

    def test_from_string_valid(self) -> None:
        assert Theme.from_string("dark") == Theme.DARK

    def test_from_string_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            Theme.from_string("neon")


class TestUpdateOutcome:
    """Sanity checks on the UpdateOutcome enum values."""

    def test_all_members_have_unique_values(self) -> None:
        values = [member.value for member in UpdateOutcome]
        assert len(values) == len(set(values))
