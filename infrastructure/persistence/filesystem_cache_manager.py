"""Filesystem-backed implementation of :class:`CacheManager`.

Manages the directory of downloaded raw tile files (not the wallpaper
history, which is managed separately by the application layer's history
retention logic). Pruning considers both an age cutoff and a total-size
soft cap, always removing the oldest files first.
"""

from __future__ import annotations

import time
from pathlib import Path

from domain.interfaces import CacheManager
from logger import get_logger

_logger = get_logger(__name__)

_BYTES_PER_MB = 1024 * 1024


class FilesystemCacheManager(CacheManager):
    """Prunes and measures a directory of cached tile files."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Directory containing cached tile files. Created if
                it does not already exist.
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def prune(self, max_age_hours: float, max_size_mb: int) -> int:
        """Remove files older than ``max_age_hours``, then remove the
        oldest remaining files until total size is under ``max_size_mb``.

        Args:
            max_age_hours: Maximum allowed file age, in hours.
            max_size_mb: Soft cap on total cache size, in megabytes.

        Returns:
            Total number of files removed.
        """
        if not self._cache_dir.exists():
            return 0

        removed_count = 0
        now = time.time()
        max_age_seconds = max_age_hours * 3600

        files = [p for p in self._cache_dir.iterdir() if p.is_file()]

        remaining: list[tuple[Path, float, int]] = []
        for file_path in files:
            try:
                stat = file_path.stat()
            except OSError:
                continue

            age_seconds = now - stat.st_mtime
            if age_seconds > max_age_seconds:
                try:
                    file_path.unlink()
                    removed_count += 1
                    _logger.debug("Pruned expired cache file: %s", file_path.name)
                except OSError:
                    _logger.warning("Could not remove cache file: %s", file_path.name)
                continue

            remaining.append((file_path, stat.st_mtime, stat.st_size))

        max_size_bytes = max_size_mb * _BYTES_PER_MB
        total_size = sum(size for _, _, size in remaining)

        if total_size > max_size_bytes:
            remaining.sort(key=lambda item: item[1])  # oldest first
            for file_path, _mtime, size in remaining:
                if total_size <= max_size_bytes:
                    break
                try:
                    file_path.unlink()
                    total_size -= size
                    removed_count += 1
                    _logger.debug(
                        "Pruned cache file to enforce size cap: %s", file_path.name
                    )
                except OSError:
                    _logger.warning("Could not remove cache file: %s", file_path.name)

        if removed_count:
            _logger.info("Cache pruning removed %d file(s).", removed_count)

        return removed_count

    def get_cache_size_bytes(self) -> int:
        """Return total size in bytes of all files in the cache directory."""
        if not self._cache_dir.exists():
            return 0

        total = 0
        for file_path in self._cache_dir.iterdir():
            if file_path.is_file():
                try:
                    total += file_path.stat().st_size
                except OSError:
                    continue
        return total
