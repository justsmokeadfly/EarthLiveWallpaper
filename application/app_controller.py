"""Facade over the application layer, used by both the UI and the CLI."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from application.progress import ProgressSnapshot, ProgressTracker
from application.results import UpdateResult
from application.scheduler_service import SchedulerService
from application.update_wallpaper_use_case import UpdateWallpaperUseCase
from config import ConfigPaths, load_config, save_config
from domain.entities import AppConfig
from domain.enums import UpdateOutcome, WallpaperMode
from domain.interfaces import StateRepository, TimelapseGenerator
from infrastructure.nasa.favorites_repository import FavoritesRepository
from infrastructure.nasa.nasa_media_service import NASAMediaService, NASAPhoto
from infrastructure.persistence.filesystem_cache_manager import FilesystemCacheManager
from infrastructure.system.autostart import AutostartManager
from logger import get_logger

_logger = get_logger(__name__)


@dataclass(frozen=True)
class StatusSnapshot:
    last_image_timestamp: datetime | None
    last_update_at: datetime | None
    last_successful_update_at: datetime | None
    next_update_at: datetime | None
    last_outcome: UpdateOutcome | None
    last_message: str
    cache_size_bytes: int
    resolution: str
    total_updates_applied: int


class AppController:
    """UI/CLI-facing facade coordinating config, scheduler, and use case."""

    def __init__(
        self,
        config_paths: ConfigPaths,
        use_case: UpdateWallpaperUseCase,
        state_repository: StateRepository,
        cache_manager: FilesystemCacheManager,
        autostart_manager: AutostartManager,
        timelapse_generator: TimelapseGenerator,
        progress_tracker: ProgressTracker,
    ) -> None:
        self._config_paths = config_paths
        self._use_case = use_case
        self._state_repository = state_repository
        self._cache_manager = cache_manager
        self._autostart_manager = autostart_manager
        self._timelapse_generator = timelapse_generator
        self._progress_tracker = progress_tracker
        self._config = load_config(config_paths)
        self._scheduler = SchedulerService(update_callback=self._on_scheduled_update)
        self._notifier: Callable[[UpdateResult], None] | None = None
        self._nasa_media = NASAMediaService()
        self._favorites = FavoritesRepository(config_paths.data_dir)

    @property
    def wallpapers_dir(self) -> Path:
        return self._config_paths.wallpapers_dir

    def start(self) -> None:
        self._scheduler.start(
            check_interval_hours=self._config.check_interval_hours,
            run_immediately=False,
        )

    def stop(self) -> None:
        self._scheduler.stop()

    def get_config(self) -> AppConfig:
        return self._config

    def update_config(self, new_config: AppConfig) -> None:
        interval_changed = (
            new_config.check_interval_hours != self._config.check_interval_hours
        )
        self._config = new_config
        save_config(self._config_paths, new_config)
        if new_config.autostart:
            self._autostart_manager.enable()
        else:
            self._autostart_manager.disable()
        if interval_changed:
            self._scheduler.stop()
            self._scheduler.start(
                check_interval_hours=new_config.check_interval_hours,
                run_immediately=False,
            )

    def is_autostart_enabled(self) -> bool:
        return self._autostart_manager.is_enabled()

    def trigger_update_now(self) -> None:
        self._scheduler.trigger_now(force=True)

    def set_notifier(self, notifier: Callable[[UpdateResult], None] | None) -> None:
        self._notifier = notifier

    def is_paused(self) -> bool:
        return self._config.paused

    def set_paused(self, paused: bool) -> None:
        self._config = replace(self._config, paused=paused)
        save_config(self._config_paths, self._config)

    def get_history(self) -> list[Path]:
        state = self._state_repository.load()
        return [Path(p) for p in state.history if Path(p).exists()]

    def reapply_from_history(self, file_path: Path) -> bool:
        return self._use_case.reapply(file_path, self._config.wallpaper_mode)

    def apply_external_wallpaper(self, file_path: Path, mode: WallpaperMode) -> bool:
        return self._use_case.reapply(file_path, mode)

    def delete_from_history(self, file_path: Path) -> bool:
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                _logger.exception("Failed to delete wallpaper file: %s", file_path)
                return False
        state = self._state_repository.load()
        path_str = str(file_path)
        if path_str in state.history:
            state.history.remove(path_str)
            self._state_repository.save(state)
        return True

    def create_timelapse(
        self,
        output_path: Path,
        frame_duration_ms: int = 200,
    ) -> bool:
        return self._timelapse_generator.create(
            list(reversed(self.get_history())),
            output_path,
            frame_duration_ms,
        )

    def get_progress(self) -> ProgressSnapshot:
        return self._progress_tracker.get()

    def get_status_snapshot(self) -> StatusSnapshot:
        state = self._state_repository.load()
        last_result = self._scheduler.get_last_result()
        return StatusSnapshot(
            state.last_timestamp,
            state.last_update_at,
            state.last_successful_update_at,
            self._scheduler.get_next_run_at(),
            last_result.outcome if last_result else state.last_outcome,
            last_result.message if last_result else "",
            self._cache_manager.get_cache_size_bytes(),
            self._config.grid_size.value,
            state.total_updates_applied,
        )

    def get_nasa_apod(self) -> NASAPhoto:
        return self._nasa_media.get_apod()

    def get_webb_photos(self, limit: int = 24) -> list[NASAPhoto]:
        return self._nasa_media.get_webb_photos(limit)

    def download_nasa_photo(
        self,
        photo: NASAPhoto,
        destination: Path,
        progress: Callable[[int, int], None] | None = None,
        image_url: str | None = None,
    ) -> Path:
        return self._nasa_media.download(photo, destination, progress, image_url)

    def translate_nasa_description(self, text: str) -> str:
        return self._nasa_media.translate_to_russian(text)

    def is_nasa_favorite(self, photo: NASAPhoto) -> bool:
        return self._favorites.is_favorite(photo.source_url or photo.image_url)

    def toggle_nasa_favorite(self, photo: NASAPhoto) -> bool:
        return self._favorites.toggle(photo.source_url or photo.image_url)

    def get_nasa_favorites(self) -> set[str]:
        return self._favorites.list_favorites()

    def _on_scheduled_update(self, force: bool) -> UpdateResult:
        result = self._use_case.execute(self._config, force=force)
        if self._notifier is not None:
            try:
                self._notifier(result)
            except Exception:
                _logger.exception("Notifier callback raised unexpectedly.")
        return result
