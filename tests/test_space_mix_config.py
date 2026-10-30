"""Tests for Cosmic Mix configuration persistence and validation."""

from __future__ import annotations

from pathlib import Path

from config import ConfigPaths, load_config, save_config
from domain.entities import AppConfig


def test_space_mix_settings_round_trip(tmp_path: Path) -> None:
    paths = ConfigPaths(override_config_path=tmp_path / "config.json")
    config = AppConfig(space_mix_enabled=True, space_mix_interval_hours=6.0)

    save_config(paths, config)
    loaded = load_config(paths)

    assert loaded.space_mix_enabled is True
    assert loaded.space_mix_interval_hours == 6.0


def test_invalid_space_mix_interval_uses_default(tmp_path: Path) -> None:
    paths = ConfigPaths(override_config_path=tmp_path / "config.json")
    paths.config_file.write_text(
        '{"space_mix_enabled": true, "space_mix_interval_hours": 0}',
        encoding="utf-8",
    )

    loaded = load_config(paths)

    assert loaded.space_mix_enabled is True
    assert loaded.space_mix_interval_hours == AppConfig().space_mix_interval_hours

def test_nonfinite_interval_uses_default(tmp_path: Path) -> None:
    paths = ConfigPaths(override_config_path=tmp_path / "config.json")
    paths.config_file.write_text(
        '{"check_interval_hours": "nan", "space_mix_interval_hours": "Infinity"}',
        encoding="utf-8",
    )
    loaded = load_config(paths)
    assert loaded.check_interval_hours == AppConfig().check_interval_hours
    assert loaded.space_mix_interval_hours == AppConfig().space_mix_interval_hours


def _read_version_value(path: Path, prefix: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split('"')[1]
    raise AssertionError(f"Missing {prefix!r} in {path}")


def test_app_installer_and_downloader_versions_match() -> None:
    root = Path(__file__).resolve().parents[1]
    version = _read_version_value(root / "pyproject.toml", "version = ")
    about = _read_version_value(root / "ui" / "about_dialog.py", "APP_VERSION = ")
    installer = _read_version_value(root / "installer" / "EarthLive.iss", "#define MyAppVersion ")
    downloader = (root / "infrastructure" / "download" / "http_tile_downloader.py").read_text(
        encoding="utf-8"
    )

    assert version == about == installer
    assert f"EarthLiveWallpaper/{version}" in downloader
