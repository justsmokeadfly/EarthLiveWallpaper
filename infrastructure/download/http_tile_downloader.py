"""Concurrent tile downloader implementation using httpx and a thread pool.

Tiles already present in the cache directory (from a previous partial or
successful run for the same timestamp/grid) are never re-downloaded. Each
missing tile is retried independently with exponential backoff, so a
single flaky tile never blocks or wastes retries on tiles that already
succeeded.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from domain.entities import TileSpec
from domain.interfaces import TileDownloader
from logger import get_logger

_logger = get_logger(__name__)

_HTTP_TIMEOUT_SECONDS = 15.0
_MAX_CONCURRENT_DOWNLOADS = 8
_MIN_VALID_TILE_BYTES = 100  # guards against saving empty/error responses


class HttpTileDownloader(TileDownloader):
    """Downloads tiles concurrently over HTTP with retry and caching."""

    def __init__(self, max_workers: int = _MAX_CONCURRENT_DOWNLOADS) -> None:
        """Initialize the downloader.

        Args:
            max_workers: Maximum number of tiles downloaded concurrently.
        """
        self._max_workers = max_workers

    def fetch_missing(
        self,
        tiles: tuple[TileSpec, ...],
        cache_dir: Path,
        retry_count: int,
        retry_delay_seconds: float,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[TileSpec, Path]:
        """Download only the tiles not already present in the cache.

        Args:
            tiles: All tiles required for the current image.
            cache_dir: Directory used to store/read cached tile files.
            retry_count: Maximum retry attempts per failing tile.
            retry_delay_seconds: Base delay for exponential backoff.
            on_progress: Optional callback invoked as
                ``on_progress(completed_count, total_count)`` after each
                tile is resolved (from cache or freshly downloaded).

        Returns:
            Mapping of TileSpec to local file path for every tile that is
            available (either already cached or freshly downloaded).
        """
        cache_dir.mkdir(parents=True, exist_ok=True)
        results: dict[TileSpec, Path] = {}
        to_download: list[TileSpec] = []
        total = len(tiles)

        for tile in tiles:
            local_path = cache_dir / tile.cache_key
            if local_path.exists() and local_path.stat().st_size >= _MIN_VALID_TILE_BYTES:
                results[tile] = local_path
            else:
                to_download.append(tile)

        already_cached = len(results)
        if already_cached and on_progress is not None:
            on_progress(already_cached, total)

        if not to_download:
            _logger.info("All %d tile(s) already cached; skipping downloads.", len(tiles))
            return results

        _logger.info(
            "Downloading %d/%d missing tile(s) with up to %d concurrent workers.",
            len(to_download),
            len(tiles),
            self._max_workers,
        )

        with httpx.Client(timeout=_HTTP_TIMEOUT_SECONDS) as client:
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                future_to_tile = {
                    executor.submit(
                        self._download_with_retry,
                        client,
                        tile,
                        cache_dir / tile.cache_key,
                        retry_count,
                        retry_delay_seconds,
                    ): tile
                    for tile in to_download
                }

                completed = already_cached
                for future in as_completed(future_to_tile):
                    tile = future_to_tile[future]
                    completed += 1
                    try:
                        local_path = future.result()
                    except Exception:
                        _logger.exception(
                            "Unexpected error downloading tile %s.", tile.cache_key
                        )
                        local_path = None

                    if local_path is not None:
                        results[tile] = local_path
                        _logger.debug(
                            "Tile %d/%d downloaded: %s",
                            completed,
                            total,
                            tile.cache_key,
                        )
                    else:
                        _logger.warning(
                            "Tile %d/%d permanently failed: %s",
                            completed,
                            total,
                            tile.cache_key,
                        )

                    if on_progress is not None:
                        on_progress(completed, total)

        _logger.info(
            "Tile download complete: %d/%d tile(s) available.", len(results), len(tiles)
        )
        return results

    def _download_with_retry(
        self,
        client: httpx.Client,
        tile: TileSpec,
        destination: Path,
        retry_count: int,
        retry_delay_seconds: float,
    ) -> Path | None:
        """Attempt to download a single tile, retrying on failure.

        Args:
            client: Shared httpx client for this batch of downloads.
            tile: The tile to download.
            destination: Local path to save the tile to.
            retry_count: Maximum number of attempts beyond the first.
            retry_delay_seconds: Base delay for exponential backoff.

        Returns:
            The destination path on success, or ``None`` if every attempt
            failed.
        """
        attempt = 0
        while attempt <= retry_count:
            try:
                response = client.get(tile.url)
                response.raise_for_status()
                content = response.content
                if len(content) < _MIN_VALID_TILE_BYTES:
                    raise ValueError(
                        f"Tile response too small ({len(content)} bytes), "
                        "likely an error placeholder image."
                    )

                tmp_path = destination.with_suffix(destination.suffix + ".tmp")
                tmp_path.write_bytes(content)
                tmp_path.replace(destination)
                return destination

            except (httpx.HTTPError, ValueError, OSError) as exc:
                attempt += 1
                if attempt > retry_count:
                    _logger.warning(
                        "Tile %s failed after %d attempt(s): %s",
                        tile.cache_key,
                        attempt,
                        exc,
                    )
                    return None

                delay = retry_delay_seconds * (2 ** (attempt - 1))
                _logger.debug(
                    "Tile %s attempt %d failed (%s); retrying in %.1fs.",
                    tile.cache_key,
                    attempt,
                    exc,
                    delay,
                )
                time.sleep(delay)

        return None
