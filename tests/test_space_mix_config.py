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
