"""Pillow-based implementation of :class:`ImageAssembler`.

Stitches a grid of tile images into one full-disk PNG, tolerating a
limited number of missing/corrupt tiles by filling their slot with black
rather than failing the whole assembly outright (a single bad tile should
not discard an otherwise-good 4x4 or 8x8 image).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from domain.entities import AssembledImage, SatelliteImage, TileSpec
from domain.interfaces import ImageAssembler
from logger import get_logger

_logger = get_logger(__name__)

# If more than this fraction of tiles are missing/corrupt, abort assembly
# entirely rather than produce a mostly-black image.
_MAX_MISSING_TILE_FRACTION = 0.25


class PillowImageAssembler(ImageAssembler):
    """Assembles satellite image tiles into a single PNG using Pillow."""

    def assemble(
        self,
        image: SatelliteImage,
        tile_paths: dict[TileSpec, Path],
        output_dir: Path,
    ) -> AssembledImage | None:
        """Stitch available tiles into a single image and save as PNG.

        Args:
            image: Metadata describing the expected tile grid.
            tile_paths: Mapping of tile spec to local file path.
            output_dir: Directory in which to save the assembled PNG.

        Returns:
            An AssembledImage on success, or ``None`` if too many tiles
            were missing/corrupt to produce a usable image.
        """
        dim = image.grid_size.dimension
        total_tiles = dim * dim
        missing_count = total_tiles - len(tile_paths)

        if missing_count / total_tiles > _MAX_MISSING_TILE_FRACTION:
            _logger.error(
                "Aborting assembly: %d/%d tiles missing, exceeds tolerance.",
                missing_count,
                total_tiles,
            )
            return None

        tile_size: tuple[int, int] | None = None
        loaded_tiles: dict[tuple[int, int], Image.Image] = {}

        for tile_spec, local_path in tile_paths.items():
            try:
                with Image.open(local_path) as opened:
                    opened.load()
                    tile_img = opened.convert("RGB")
            except (UnidentifiedImageError, OSError) as exc:
                _logger.warning(
                    "Corrupt tile skipped (%s): %s", local_path.name, exc
                )
                continue

            if tile_size is None:
                tile_size = tile_img.size
            loaded_tiles[(tile_spec.column, tile_spec.row)] = tile_img

        if not loaded_tiles or tile_size is None:
            _logger.error("No valid tiles could be loaded; aborting assembly.")
            return None

        effective_missing = total_tiles - len(loaded_tiles)
        if effective_missing / total_tiles > _MAX_MISSING_TILE_FRACTION:
            _logger.error(
                "Aborting assembly: %d/%d tiles unusable after load, exceeds tolerance.",
                effective_missing,
                total_tiles,
            )
            for tile_img in loaded_tiles.values():
                tile_img.close()
            return None

        tile_w, tile_h = tile_size
        canvas = Image.new("RGB", (tile_w * dim, tile_h * dim), color=(0, 0, 0))

        for (col, row), tile_img in loaded_tiles.items():
            canvas.paste(tile_img, (col * tile_w, row * tile_h))
            tile_img.close()

        if effective_missing:
            _logger.warning(
                "Assembled image with %d/%d tile(s) missing (filled black).",
                effective_missing,
                total_tiles,
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{image.provider_name}_{image.grid_size.value}_"
            f"{image.timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        )
        output_path = output_dir / filename

        tmp_path = output_path.with_suffix(".png.tmp")
        try:
            canvas.save(tmp_path, format="PNG", optimize=True)
            tmp_path.replace(output_path)
        except OSError:
            _logger.exception("Failed to save assembled image to %s.", output_path)
            canvas.close()
            return None

        content_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        width, height = canvas.size
        canvas.close()

        _logger.info(
            "Assembled image saved: %s (%dx%d, hash=%s).",
            output_path.name,
            width,
            height,
            content_hash[:12],
        )

        return AssembledImage(
            source=image,
            file_path=output_path,
            content_hash=content_hash,
            width=width,
            height=height,
        )
