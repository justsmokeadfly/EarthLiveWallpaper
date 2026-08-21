"""Application configuration loading, validation, and persistence."""

from __future__ import annotations

import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import orjson
import platformdirs

from domain.entities import AppConfig
from domain.enums import GridSize, Language, Theme, WallpaperMode
from logger import get_logger

_logger = get_logger(__name__)

_APP_NAME = "EarthLive"
_APP_AUTHOR = "EarthLive"
_CONFIG_FILENAME = "config.json"


class ConfigPaths:
    """Resolves all filesystem locations used by EarthLive."""

    def __init__(self, override_config_path: Path | None = None, portable: bool = False) -> None:
        self._override_config_path = override_config_path
        self._portable = portable

    @property
    def _portable_root(self) -> Path:
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent
        return base / "data"

    @property
    def data_dir(self) -> Path:
        if self._portable:
            return self._portable_root
        return Path(platformdirs.user_data_dir(_APP_NAME, _APP_AUTHOR))

    @property
    def config_dir(self) -> Path:
        if self._override_config_path is not None:
            return self._override_config_path.parent
        if self._portable:
            return self._portable_root
        return Path(platformdirs.user_config_dir(_APP_NAME, _APP_AUTHOR))

    @property
    def config_file(self) -> Path:
        if self._override_config_path is not None:
            return self._override_config_path
        return self.config_dir / _CONFIG_FILENAME

    @property
    def state_file(self) -> Path:
        return self.data_dir / "state.json"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def wallpapers_dir(self) -> Path:
        return self.data_dir / "wallpapers"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    def ensure_directories(self) -> None:
        for directory in (
            self.config_dir,
            self.data_dir,
            self.cache_dir,
            self.wallpapers_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def _config_to_dict(config: AppConfig) -> dict[str, Any]:
    raw = asdict(config)
    raw["grid_size"] = config.grid_size.value
    raw["theme"] = config.theme.value
    raw["wallpaper_mode"] = config.wallpaper_mode.value
    raw["language"] = config.language.value
    return raw


def _safe_number(raw: dict[str, Any], key: str, fallback: float, minimum: float) -> float:
    try:
        value = float(raw.get(key, fallback))
    except (TypeError, ValueError):
        _logger.warning("Invalid %s in config; using default.", key)
        return fallback
    if value < minimum:
        _logger.warning("Invalid %s=%s in config; using default.", key, value)
        return fallback
    return value


def _safe_int(raw: dict[str, Any], key: str, fallback: int, minimum: int) -> int:
    try:
        value = int(raw.get(key, fallback))
    except (TypeError, ValueError):
        _logger.warning("Invalid %s in config; using default.", key)
        return fallback
    if value < minimum:
        _logger.warning("Invalid %s=%s in config; using default.", key, value)
        return fallback
    return value


def _safe_bool(raw: dict[str, Any], key: str, fallback: bool) -> bool:
    value = raw.get(key, fallback)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    _logger.warning("Invalid %s in config; using default.", key)
    return fallback


def _dict_to_config(raw: dict[str, Any]) -> AppConfig:
    """Build a validated AppConfig, falling back per field when needed."""
    defaults = AppConfig()

    try:
        grid_size = GridSize.from_string(str(raw.get("grid_size", defaults.grid_size.value)))
    except ValueError:
        _logger.warning("Invalid grid_size in config; using default.")
        grid_size = defaults.grid_size

    try:
        theme = Theme.from_string(str(raw.get("theme", defaults.theme.value)))
    except ValueError:
        _logger.warning("Invalid theme in config; using default.")
        theme = defaults.theme

    try:
        wallpaper_mode = WallpaperMode.from_string(str(raw.get("wallpaper_mode", defaults.wallpaper_mode.value)))
    except ValueError:
        _logger.warning("Invalid wallpaper_mode in config; using default.")
        wallpaper_mode = defaults.wallpaper_mode

    try:
        language = Language.from_string(str(raw.get("language", defaults.language.value)))
    except ValueError:
        _logger.warning("Invalid language in config; using default.")
        language = defaults.language

    return AppConfig(
        provider=str(raw.get("provider", defaults.provider)),
        grid_size=grid_size,
        check_interval_hours=_safe_number(raw, "check_interval_hours", defaults.check_interval_hours, 0.01),
        history_size=_safe_int(raw, "history_size", defaults.history_size, 1),
        theme=theme,
        autostart=_safe_bool(raw, "autostart", defaults.autostart),
        wallpaper_mode=wallpaper_mode,
        retry_count=_safe_int(raw, "retry_count", defaults.retry_count, 0),
        retry_delay_seconds=_safe_number(raw, "retry_delay_seconds", defaults.retry_delay_seconds, 0.0),
        max_cache_age_hours=_safe_number(raw, "max_cache_age_hours", defaults.max_cache_age_hours, 0.01),
        max_cache_size_mb=_safe_int(raw, "max_cache_size_mb", defaults.max_cache_size_mb, 1),
        language=language,
        paused=_safe_bool(raw, "paused", defaults.paused),
    )


def load_config(paths: ConfigPaths) -> AppConfig:
    config_file = paths.config_file
    if not config_file.exists():
        _logger.info("No existing config found at %s; creating defaults.", config_file)
        default_config = AppConfig()
        save_config(paths, default_config)
        return default_config

    try:
        raw = orjson.loads(config_file.read_bytes())
        if not isinstance(raw, dict):
            raise ValueError("Config file does not contain a JSON object.")
        return _dict_to_config(raw)
    except Exception:
        _logger.exception("Failed to read config at %s; falling back to defaults.", config_file)
        return AppConfig()


def save_config(paths: ConfigPaths, config: AppConfig) -> None:
    """Persist configuration to disk atomically."""
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    config_file = paths.config_file
    tmp_file = config_file.with_suffix(".tmp")
    try:
        payload = orjson.dumps(_config_to_dict(config), option=orjson.OPT_INDENT_2)
        tmp_file.write_bytes(payload)
        os.replace(tmp_file, config_file)
    except Exception:
        _logger.exception("Failed to save config to %s.", config_file)
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except OSError:
                pass
