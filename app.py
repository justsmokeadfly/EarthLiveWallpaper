"""Composition root: builds the full object graph for EarthLive.

This is the only module in the entire codebase that imports concrete
implementations from every layer and wires them together. Nothing here
contains business logic - it is pure dependency injection.
"""

from __future__ import annotations

import logging
from pathlib import Path

from application.app_controller import AppController
from application.progress import ProgressTracker
from application.update_wallpaper_use_case import UpdateWallpaperUseCase
from config import ConfigPaths, load_config
from infrastructure.download.http_tile_downloader import HttpTileDownloader
from infrastructure.imaging.pillow_assembler import PillowImageAssembler
from infrastructure.imaging.pillow_timelapse_generator import PillowTimelapseGenerator
from infrastructure.persistence.filesystem_cache_manager import FilesystemCacheManager
from infrastructure.persistence.json_state_repository import JsonStateRepository
from infrastructure.providers.provider_registry import ProviderRegistry
from infrastructure.system.autostart import AutostartManager
from infrastructure.system.network_probe import SocketNetworkProbe
from infrastructure.wallpaper.windows_wallpaper_setter import WindowsWallpaperSetter
from logger import configure_logging, get_logger

_logger = get_logger(__name__)


def build_app_controller(
    config_override_path: Path | None = None, portable: bool = False
) -> AppController:
    """Construct a fully wired :class:`AppController`.

    Args:
        config_override_path: Optional explicit path to a config JSON
            file, used by the ``--config`` CLI flag. If omitted, the
            platform default user config location is used.
        portable: If ``True``, store all data next to the executable
            instead of the platform's per-user app data location.

    Returns:
        A ready-to-use AppController with every dependency injected.
    """
    paths = ConfigPaths(override_config_path=config_override_path, portable=portable)
    paths.ensure_directories()

    configure_logging(paths.logs_dir, level=logging.INFO)
    _logger.info("EarthLive starting up. Data directory: %s", paths.data_dir)

    config = load_config(paths)

    registry = ProviderRegistry()
    try:
        provider = registry.create(config.provider)
    except KeyError:
        _logger.warning(
            "Configured provider '%s' not found; falling back to 'himawari'.",
            config.provider,
        )
        provider = registry.create("himawari")

    downloader = HttpTileDownloader()
    assembler = PillowImageAssembler()
    timelapse_generator = PillowTimelapseGenerator()
    wallpaper_setter = WindowsWallpaperSetter()
    state_repository = JsonStateRepository(paths.state_file)
    cache_manager = FilesystemCacheManager(paths.cache_dir)
    network_probe = SocketNetworkProbe()
    autostart_manager = AutostartManager()
    progress_tracker = ProgressTracker()

    use_case = UpdateWallpaperUseCase(
        provider=provider,
        downloader=downloader,
        assembler=assembler,
        wallpaper_setter=wallpaper_setter,
        state_repository=state_repository,
        cache_manager=cache_manager,
        network_probe=network_probe,
        cache_dir=paths.cache_dir,
        wallpapers_dir=paths.wallpapers_dir,
        progress_tracker=progress_tracker,
    )

    controller = AppController(
        config_paths=paths,
        use_case=use_case,
        state_repository=state_repository,
        cache_manager=cache_manager,
        autostart_manager=autostart_manager,
        timelapse_generator=timelapse_generator,
        progress_tracker=progress_tracker,
    )

    return controller
