"""Unit tests for PillowImageAssembler."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from domain.entities import SatelliteImage
from infrastructure.imaging.pillow_assembler import PillowImageAssembler


def _write_solid_tile(path: Path, color: tuple[int, int, int], size: int = 10) -> None:
    """Write a small solid-color PNG tile to disk."""
    img = Image.new("RGB", (size, size), color=color)
    img.save(path)
    img.close()


class TestPillowImageAssembler:
    """Tests for the assemble() method."""

    def test_assembles_all_tiles_successfully(
        self, tmp_path: Path, sample_satellite_image: SatelliteImage
    ) -> None:
        tile_paths = {}
        for i, tile in enumerate(sample_satellite_image.tiles):
            path = tmp_path / tile.cache_key
            _write_solid_tile(path, color=(i * 50, 0, 0))
            tile_paths[tile] = path

        assembler = PillowImageAssembler()
        output_dir = tmp_path / "output"

        result = assembler.assemble(sample_satellite_image, tile_paths, output_dir)

        assert result is not None
        assert result.file_path.exists()
        assert result.width == 20  # 2 tiles * 10px
        assert result.height == 20
        assert len(result.content_hash) == 64  # sha256 hex digest length

    def test_returns_none_when_too_many_tiles_missing(
        self, tmp_path: Path, sample_satellite_image: SatelliteImage
    ) -> None:
        # Only provide 1 of 4 tiles - exceeds the missing-tile tolerance.
        first_tile = sample_satellite_image.tiles[0]
        path = tmp_path / first_tile.cache_key
        _write_solid_tile(path, color=(255, 0, 0))
        tile_paths = {first_tile: path}

        assembler = PillowImageAssembler()
        result = assembler.assemble(sample_satellite_image, tile_paths, tmp_path / "output")

        assert result is None

    def test_skips_corrupt_tile_file(
        self, tmp_path: Path, sample_satellite_image: SatelliteImage
    ) -> None:
        tile_paths = {}
        tiles = sample_satellite_image.tiles

        for i, tile in enumerate(tiles):
            path = tmp_path / tile.cache_key
            if i == 0:
                path.write_bytes(b"not a real image")
            else:
                _write_solid_tile(path, color=(10, 20, 30))
            tile_paths[tile] = path

        assembler = PillowImageAssembler()
        result = assembler.assemble(sample_satellite_image, tile_paths, tmp_path / "output")

        # 1 of 4 tiles corrupt (25%) is within the tolerance threshold.
        assert result is not None
        assert result.file_path.exists()

    def test_content_hash_is_deterministic(
        self, tmp_path: Path, sample_satellite_image: SatelliteImage
    ) -> None:
        tile_paths = {}
        for tile in sample_satellite_image.tiles:
            path = tmp_path / tile.cache_key
            _write_solid_tile(path, color=(1, 2, 3))
            tile_paths[tile] = path

        assembler = PillowImageAssembler()
        result_a = assembler.assemble(sample_satellite_image, tile_paths, tmp_path / "out_a")
        result_b = assembler.assemble(sample_satellite_image, tile_paths, tmp_path / "out_b")

        assert result_a is not None and result_b is not None
        assert result_a.content_hash == result_b.content_hash
