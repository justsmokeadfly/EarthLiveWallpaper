"""Concurrent tile downloader using httpx with retries and validation."""

from __future__ import annotations

import io
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
from PIL import Image, UnidentifiedImageError

from domain.entities import TileSpec
from domain.interfaces import TileDownloader
from logger import get_logger

_logger = get_logger(__name__)

_HTTP_TIMEOUT_SECONDS = 15.0
_MAX_CONCURRENT_DOWNLOADS = 8
_MIN_VALID_TILE_BYTES = 100
_MAX_TILE_BYTES = 20 * 1024 * 1024
_VALID_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class HttpTileDownloader(TileDownloader):
    """Downloads tiles concurrently over HTTP with retry and caching."""

    def __init__(self, max_workers: int = _MAX_CONCURRENT_DOWNLOADS) -> None:
        self._max_workers = max_workers

    def fetch_missing(
        self,
        tiles: tuple[TileSpec, ...],
        cache_dir: Path,
        retry_count: int,
        retry_delay_seconds: float,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[TileSpec, Path]:
        cache_dir.mkdir(parents=True, exist_ok=True)
        results: dict[TileSpec, Path] = {}
        to_download: list[TileSpec] = []
        total = len(tiles)

        for tile in tiles:
            local_path = cache_dir / tile.cache_key
            if local_path.exists() and self._is_valid_image_file(local_path):
                results[tile] = local_path
            else:
                if local_path.exists():
                    try:
                        local_path.unlink()
                    except OSError:
                        _logger.warning("Unable to remove invalid cached tile %s", local_path)
                to_download.append(tile)

        already_cached = len(results)
        if already_cached and on_progress is not None:
            on_progress(already_cached, total)

        if not to_download:
            _logger.info("All %d tile(s) already cached; skipping downloads.", len(tiles))
            return results

        _logger.info(
            "Downloading %d/%d missing tile(s) with up to %d concurrent workers.",
            len(to_download), total, self._max_workers,
        )

        headers = {"User-Agent": "EarthLiveWallpaper/1.3.0 (+https://github.com/justsmokeadfly/EarthLiveWallpaper)"}
        with (
            httpx.Client(timeout=_HTTP_TIMEOUT_SECONDS, headers=headers, follow_redirects=True) as client,
            ThreadPoolExecutor(max_workers=self._max_workers) as executor,
        ):
            future_to_tile = {
                executor.submit(
                    self._download_with_retry,
                    client, tile, cache_dir / tile.cache_key,
                    retry_count, retry_delay_seconds,
                ): tile
                for tile in to_download
            }

            completed = already_cached
            for future in as_completed(future_to_tile):
                tile = future_to_tile[future]
                completed += 1
                downloaded_path: Path | None
                try:
                    downloaded_path = future.result()
                except Exception:
                    _logger.exception("Unexpected error downloading tile %s", tile.cache_key)
                    downloaded_path = None

                if downloaded_path is not None:
                    results[tile] = downloaded_path
                else:
                    _logger.warning("Tile %d/%d permanently failed: %s", completed, total, tile.cache_key)

                if on_progress is not None:
                    on_progress(completed, total)

        _logger.info("Tile download complete: %d/%d tile(s) available.", len(results), len(tiles))
        return results

    @staticmethod
    def _is_valid_image_bytes(content: bytes) -> bool:
        if not _MIN_VALID_TILE_BYTES <= len(content) <= _MAX_TILE_BYTES:
            return False
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
            return True
        except (UnidentifiedImageError, OSError, ValueError):
            return False

    @classmethod
    def _is_valid_image_file(cls, path: Path) -> bool:
        try:
            return cls._is_valid_image_bytes(path.read_bytes())
        except OSError:
            return False

    def _download_with_retry(
        self,
        client: httpx.Client,
        tile: TileSpec,
        destination: Path,
        retry_count: int,
        retry_delay_seconds: float,
    ) -> Path | None:
        attempt = 0
        while attempt <= retry_count:
            try:
                response = client.get(tile.url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                content = response.content

                if content_type not in _VALID_IMAGE_TYPES:
                    raise ValueError(f"Unexpected tile Content-Type: {content_type or 'missing'}")
                if not self._is_valid_image_bytes(content):
                    raise ValueError("Tile response is not a valid supported image or exceeds size limits")

                tmp_path = destination.with_suffix(destination.suffix + ".tmp")
                tmp_path.write_bytes(content)
                tmp_path.replace(destination)
                return destination

            except (httpx.HTTPError, ValueError, OSError) as exc:
                attempt += 1
                if attempt > retry_count:
                    _logger.warning("Tile %s failed after %d attempt(s): %s", tile.cache_key, attempt, exc)
                    return None

                delay = retry_delay_seconds * (2 ** (attempt - 1))
                _logger.debug("Tile %s attempt %d failed (%s); retrying in %.1fs.", tile.cache_key, attempt, exc, delay)
                time.sleep(delay)

        return None
