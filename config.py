"""Application configuration loading, validation, and persistence.

Configuration is stored as JSON (via orjson) under the platform-appropriate
user config directory, resolved through ``platformdirs``. This module is
part of the composition root layer: it knows about concrete storage
mechanisms, but the resulting :class:`AppConfig` dataclass it produces is
a pure domain object.
"""

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
    """Resolves all filesystem locations used by EarthLive.

    Centralizing path resolution here means every other module asks this
    class for a location rather than calling ``platformdirs`` directly,
    which keeps path logic (and any future overrides via environment
    variables) in exactly one place.
    """

    def __init__(
        self,
        override_config_path: Path | None = None,
        portable: bool = False,
    ) -> None:
        """Initialize path resolution.

        Args:
            override_config_path: If provided, this exact path is used for
                the config file instead of the platform default (used by
                the ``--config`` CLI flag).
            portable: If ``True``, all application data (config, state,
                cache, wallpapers, logs) is stored in a single ``data``
                folder next to the running executable/script instead of
                the platform's per-user app data location. Useful for
                running EarthLive from a USB drive or a folder you fully
                control, with no traces left in ``%APPDATA%``.
        """
        self._override_config_path = override_config_path
        self._portable = portable

    @property
    def _portable_root(self) -> Path:
        """Root folder used for all data when running in portable mode.

        Resolves next to the frozen executable (PyInstaller build) or
        next to this source file when running from source, then adds a
        ``data`` subfolder so it doesn't mix with the application's own
        code files.
        """
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent
        return base / "data"

    @property
    def data_dir(self) -> Path:
        """Root directory for persistent application data."""
        if self._portable:
            return self._portable_root
        return Path(platformdirs.user_data_dir(_APP_NAME, _APP_AUTHOR))

    @property
    def config_dir(self) -> Path:
        """Directory containing the configuration file."""
        if self._override_config_path is not None:
            return self._override_config_path.parent
        if self._portable:
            return self._portable_root
        return Path(platformdirs.user_config_dir(_APP_NAME, _APP_AUTHOR))

    @property
    def config_file(self) -> Path:
        """Full path to the configuration JSON file."""
        if self._override_config_path is not None:
            return self._override_config_path
        return self.config_dir / _CONFIG_FILENAME

    @property
    def state_file(self) -> Path:
        """Full path to the persisted application state JSON file."""
        return self.data_dir / "state.json"

    @property
    def cache_dir(self) -> Path:
        """Directory used to store downloaded tile files."""
        return self.data_dir / "cache"

    @property
    def wallpapers_dir(self) -> Path:
        """Directory used to store assembled wallpaper history."""
        return self.data_dir / "wallpapers"

    @property
    def logs_dir(self) -> Path:
        """Directory used to store rotating log files."""
        return self.data_dir / "logs"

    def ensure_directories(self) -> None:
        """Create every directory this application needs, if missing."""
        for directory in (
            self.config_dir,
            self.data_dir,
            self.cache_dir,
            self.wallpapers_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def _config_to_dict(config: AppConfig) -> dict[str, Any]:
    """Convert an AppConfig into a JSON-serializable dict."""
    raw = asdict(config)
    raw["grid_size"] = config.grid_size.value
    raw["theme"] = config.theme.value
    raw["wallpaper_mode"] = config.wallpaper_mode.value
    raw["language"] = config.language.value
    return raw


def _dict_to_config(raw: dict[str, Any]) -> AppConfig:
    """Build an AppConfig from a raw dict, falling back to defaults for any
    missing or invalid field rather than raising.

    Args:
        raw: The parsed JSON content.

    Returns:
        A fully populated, validated AppConfig.
    """
    defaults = AppConfig()

    def _get(key: str, fallback: Any) -> Any:
        return raw.get(key, fallback)

    try:
        grid_size = GridSize.from_string(str(_get("grid_size", defaults.grid_size.value)))
    except ValueError:
        _logger.warning("Invalid grid_size in config; using default.")
        grid_size = defaults.grid_size

    try:
        theme = Theme.from_string(str(_get("theme", defaults.theme.value)))
    except ValueError:
        _logger.warning("Invalid theme in config; using default.")
        theme = defaults.theme

    try:
        wallpaper_mode = WallpaperMode.from_string(
            str(_get("wallpaper_mode", defaults.wallpaper_mode.value))
        )
    except ValueError:
        _logger.warning("Invalid wallpaper_mode in config; using default.")
        wallpaper_mode = defaults.wallpaper_mode

    try:
        language = Language.from_string(str(_get("language", defaults.language.value)))
    except ValueError:
        _logger.warning("Invalid language in config; using default.")
        language = defaults.language

    return AppConfig(
        provider=str(_get("provider", defaults.provider)),
        grid_size=grid_size,
        check_interval_hours=float(
            _get("check_interval_hours", defaults.check_interval_hours)
        ),
        history_size=int(_get("history_size", defaults.history_size)),
        theme=theme,
        autostart=bool(_get("autostart", defaults.autostart)),
        wallpaper_mode=wallpaper_mode,
        retry_count=int(_get("retry_count", defaults.retry_count)),
        retry_delay_seconds=float(
            _get("retry_delay_seconds", defaults.retry_delay_seconds)
        ),
        max_cache_age_hours=float(
            _get("max_cache_age_hours", defaults.max_cache_age_hours)
        ),
        max_cache_size_mb=int(_get("max_cache_size_mb", defaults.max_cache_size_mb)),
        language=language,
        paused=bool(_get("paused", defaults.paused)),
    )


def load_config(paths: ConfigPaths) -> AppConfig:
    """Load configuration from disk, creating a default file if absent.

    Args:
        paths: Resolved application paths.

    Returns:
        The loaded (or newly created default) AppConfig. Malformed
        individual fields fall back to defaults rather than failing the
        whole load.
    """
    config_file = paths.config_file
    if not config_file.exists():
        _logger.info("No existing config found at %s; creating defaults.", config_file)
        default_config = AppConfig()
        save_config(paths, default_config)
        return default_config

    try:
        raw_bytes = config_file.read_bytes()
        raw = orjson.loads(raw_bytes)
        if not isinstance(raw, dict):
            raise ValueError("Config file does not contain a JSON object.")
        return _dict_to_config(raw)
    except Exception:
        _logger.exception(
            "Failed to read config at %s; falling back to defaults.", config_file
        )
        return AppConfig()


def save_config(paths: ConfigPaths, config: AppConfig) -> None:
    """Persist configuration to disk atomically.

    Args:
        paths: Resolved application paths.
        config: The configuration to persist.
    """
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
