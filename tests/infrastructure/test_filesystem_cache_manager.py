"""Unit tests for FilesystemCacheManager."""

from __future__ import annotations

import os
import time
from pathlib import Path

from infrastructure.persistence.filesystem_cache_manager import FilesystemCacheManager


def _make_file(path: Path, size_bytes: int, age_seconds: float = 0.0) -> None:
    """Create a file of the given size, optionally backdating its mtime."""
    path.write_bytes(b"x" * size_bytes)
    if age_seconds:
        old_time = time.time() - age_seconds
        os.utime(path, (old_time, old_time))


class TestFilesystemCacheManager:
    """Tests for prune() and get_cache_size_bytes()."""

    def test_get_cache_size_bytes_sums_all_files(self, tmp_path: Path) -> None:
        _make_file(tmp_path / "a.png", 100)
        _make_file(tmp_path / "b.png", 200)

        manager = FilesystemCacheManager(tmp_path)

        assert manager.get_cache_size_bytes() == 300

    def test_prune_removes_expired_files_by_age(self, tmp_path: Path) -> None:
        _make_file(tmp_path / "old.png", 100, age_seconds=100 * 3600)
        _make_file(tmp_path / "new.png", 100, age_seconds=1)

        manager = FilesystemCacheManager(tmp_path)
        removed = manager.prune(max_age_hours=48.0, max_size_mb=1000)

        assert removed == 1
        assert not (tmp_path / "old.png").exists()
        assert (tmp_path / "new.png").exists()

    def test_prune_removes_oldest_first_when_over_size_cap(self, tmp_path: Path) -> None:
        one_mb = 1024 * 1024
        _make_file(tmp_path / "oldest.png", one_mb, age_seconds=300)
        _make_file(tmp_path / "middle.png", one_mb, age_seconds=200)
        _make_file(tmp_path / "newest.png", one_mb, age_seconds=100)

        manager = FilesystemCacheManager(tmp_path)
        removed = manager.prune(max_age_hours=1000.0, max_size_mb=2)

        assert removed == 1
        assert not (tmp_path / "oldest.png").exists()
        assert (tmp_path / "middle.png").exists()
        assert (tmp_path / "newest.png").exists()

    def test_prune_returns_zero_when_nothing_to_remove(self, tmp_path: Path) -> None:
        _make_file(tmp_path / "small.png", 100, age_seconds=1)

        manager = FilesystemCacheManager(tmp_path)
        removed = manager.prune(max_age_hours=48.0, max_size_mb=1000)

        assert removed == 0
