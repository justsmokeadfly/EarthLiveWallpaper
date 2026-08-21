"""The central application use case: check for a new image and, if one
exists, download it, assemble it, apply it as wallpaper, and update
persisted state - all while never letting a failure at any stage crash
the process or disturb the currently-applied wallpaper.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from domain.entities import AppConfig, AppState
from domain.enums import UpdateOutcome, WallpaperMode
from domain.interfaces import (
    CacheManager,
    ImageAssembler,
    ImageProvider,
    NetworkProbe,
    StateRepository,
    TileDownloader,
    WallpaperSetter,
)
from logger import get_logger

from application.progress import ProgressStage, ProgressTracker
from application.results import UpdateResult

_logger = get_logger(__name__)


class UpdateWallpaperUseCase:
    """Orchestrates one complete "check for new image, apply if found"
    cycle, using only interfaces injected by the composition root.
    """

    def __init__(
        self,
        provider: ImageProvider,
        downloader: TileDownloader,
        assembler: ImageAssembler,
        wallpaper_setter: WallpaperSetter,
        state_repository: StateRepository,
        cache_manager: CacheManager,
        network_probe: NetworkProbe,
        cache_dir: Path,
        wallpapers_dir: Path,
        progress_tracker: ProgressTracker | None = None,
    ) -> None:
        """Initialize the use case with all of its collaborators.

        Args:
            provider: Active image provider (e.g. Himawari).
            downloader: Concurrent tile downloader.
            assembler: Tile-to-image assembler.
            wallpaper_setter: Windows wallpaper applier.
            state_repository: Persistent app state storage.
            cache_manager: Tile cache pruning/measurement.
            network_probe: Connectivity checker.
            cache_dir: Directory for raw downloaded tiles.
            wallpapers_dir: Directory for assembled wallpaper history.
            progress_tracker: Optional shared tracker updated as this
                use case moves through stages, for UI progress bars. If
                omitted, progress simply isn't reported anywhere.
        """
        self._provider = provider
        self._downloader = downloader
        self._assembler = assembler
        self._wallpaper_setter = wallpaper_setter
        self._state_repository = state_repository
        self._cache_manager = cache_manager
        self._network_probe = network_probe
        self._cache_dir = cache_dir
        self._wallpapers_dir = wallpapers_dir
        self._progress = progress_tracker or ProgressTracker()

    def execute(self, config: AppConfig, force: bool = False) -> UpdateResult:
        """Run one full update cycle.

        Args:
            config: Current application configuration.
            force: If ``True``, bypass the "already up to date" short
                circuit and re-apply even if the timestamp is unchanged
                (used by the manual "Update now" button).

        Returns:
            An UpdateResult describing what happened. This method never
            raises; every failure path is caught and converted into a
            typed result.
        """
        start_time = time.monotonic()
        state = self._state_repository.load()

        try:
            result = self._execute_inner(config, state, force)
        except Exception as exc:  # noqa: BLE001 - top-level safety net by design
            _logger.exception("Unexpected error during update cycle.")
            result = UpdateResult(
                outcome=UpdateOutcome.UNEXPECTED_ERROR,
                message=f"Unexpected error: {exc}",
            )
        finally:
            self._progress.reset()

        duration = time.monotonic() - start_time
        result = UpdateResult(
            outcome=result.outcome,
            message=result.message,
            assembled_image=result.assembled_image,
            duration_seconds=duration,
        )

        state.last_update_at = datetime.now(timezone.utc)
        state.last_outcome = result.outcome
        self._state_repository.save(state)

        _logger.info(
            "Update cycle finished in %.2fs: %s (%s)",
            duration,
            result.outcome.value,
            result.message,
        )
        return result

    def _execute_inner(
        self, config: AppConfig, state: AppState, force: bool
    ) -> UpdateResult:
        """Core logic, separated from the top-level try/except and the
        state-saving bookkeeping in :meth:`execute` for readability.
        """
        if config.paused and not force:
            _logger.info("Updates are paused; skipping this cycle.")
            return UpdateResult(
                outcome=UpdateOutcome.PAUSED,
                message="Updates are paused.",
            )

        _logger.info("Checking internet connectivity...")
        self._progress.set(ProgressStage.CHECKING)
        if not self._network_probe.is_online():
            _logger.warning("No internet connection available. Will retry later.")
            return UpdateResult(
                outcome=UpdateOutcome.NETWORK_UNAVAILABLE,
                message="No internet connection. Will retry on the next cycle.",
            )

        _logger.info("Checking %s server for the latest image timestamp...", self._provider.name)
        latest_timestamp = self._provider.get_latest_available_timestamp()
        if latest_timestamp is None:
            _logger.warning("Provider unavailable. Keeping current wallpaper.")
            return UpdateResult(
                outcome=UpdateOutcome.PROVIDER_UNAVAILABLE,
                message="Satellite server unavailable. Keeping current wallpaper.",
            )

        if not force and state.last_timestamp is not None:
            if latest_timestamp <= state.last_timestamp:
                _logger.info(
                    "Latest image (%s) is not newer than current (%s). Nothing to do.",
                    latest_timestamp.isoformat(),
                    state.last_timestamp.isoformat(),
                )
                return UpdateResult(
                    outcome=UpdateOutcome.ALREADY_UP_TO_DATE,
                    message="Already up to date.",
                )

        _logger.info("New image found: %s. Preparing download.", latest_timestamp.isoformat())
        image_request = self._provider.build_image_request(latest_timestamp, config.grid_size)

        _logger.info(
            "Downloading %d tile(s) at %s resolution...",
            len(image_request.tiles),
            config.grid_size.value,
        )
        total_tiles = len(image_request.tiles)
        self._progress.set(ProgressStage.DOWNLOADING, 0, total_tiles)
        tile_paths = self._downloader.fetch_missing(
            tiles=image_request.tiles,
            cache_dir=self._cache_dir,
            retry_count=config.retry_count,
            retry_delay_seconds=config.retry_delay_seconds,
            on_progress=lambda current, total: self._progress.set(
                ProgressStage.DOWNLOADING, current, total
            ),
        )

        if not tile_paths:
            _logger.error("No tiles could be downloaded. Keeping current wallpaper.")
            return UpdateResult(
                outcome=UpdateOutcome.DOWNLOAD_FAILED,
                message="Failed to download any tiles. Keeping current wallpaper.",
            )

        _logger.info("Assembling image from %d/%d tile(s)...", len(tile_paths), len(image_request.tiles))
        self._progress.set(ProgressStage.ASSEMBLING)
        assembled = self._assembler.assemble(
            image=image_request,
            tile_paths=tile_paths,
            output_dir=self._wallpapers_dir,
        )

        if assembled is None:
            _logger.error("Image assembly failed. Keeping current wallpaper.")
            return UpdateResult(
                outcome=UpdateOutcome.ASSEMBLY_FAILED,
                message="Failed to assemble image. Keeping current wallpaper.",
            )

        if not force and assembled.content_hash == state.last_content_hash:
            _logger.info(
                "Assembled image content is identical to the last applied image "
                "(hash match). Updating timestamp only; wallpaper left unchanged."
            )
            state.last_timestamp = latest_timestamp
            self._prune_cache(config)
            return UpdateResult(
                outcome=UpdateOutcome.DUPLICATE_CONTENT,
                message="New timestamp but identical image content; wallpaper unchanged.",
            )

        _logger.info("Applying wallpaper (mode=%s)...", config.wallpaper_mode.value)
        self._progress.set(ProgressStage.APPLYING)
        applied = self._wallpaper_setter.apply(assembled.file_path, config.wallpaper_mode)

        if not applied:
            _logger.error("Failed to apply wallpaper. Current wallpaper left unchanged.")
            return UpdateResult(
                outcome=UpdateOutcome.WALLPAPER_APPLY_FAILED,
                message="Failed to apply wallpaper via Windows API.",
            )

        state.last_timestamp = latest_timestamp
        state.last_content_hash = assembled.content_hash
        state.last_successful_update_at = datetime.now(timezone.utc)
        state.total_updates_applied += 1
        self._update_history(state, assembled.file_path, config.history_size)
        self._prune_cache(config)

        _logger.info("Wallpaper updated successfully. Finished.")
        return UpdateResult(
            outcome=UpdateOutcome.SUCCESS,
            message=f"Wallpaper updated to {latest_timestamp.isoformat()}.",
            assembled_image=assembled,
        )

    def reapply(self, file_path: Path, mode: WallpaperMode) -> bool:
        """Re-apply a previously saved wallpaper file (from history).

        Does not touch persisted state (timestamp/hash/history) - this is
        purely "make this old image the current wallpaper again", used by
        the history gallery in the UI.

        Args:
            file_path: Path to a previously assembled wallpaper PNG.
            mode: Desired wallpaper positioning mode.

        Returns:
            ``True`` if the wallpaper was applied successfully.
        """
        if not file_path.exists():
            _logger.warning("Cannot reapply missing wallpaper file: %s", file_path)
            return False
        return self._wallpaper_setter.apply(file_path, mode)

    def _update_history(self, state: AppState, new_path: Path, history_size: int) -> None:
        """Add a newly applied wallpaper to history and prune old entries
        beyond ``history_size``, deleting the corresponding files.
        """
        path_str = str(new_path)
        if path_str in state.history:
            state.history.remove(path_str)
        state.history.insert(0, path_str)

        while len(state.history) > max(history_size, 1):
            old_path_str = state.history.pop()
            old_path = Path(old_path_str)
            if old_path.exists():
                try:
                    old_path.unlink()
                    _logger.debug("Removed old wallpaper history file: %s", old_path.name)
                except OSError:
                    _logger.warning("Could not remove old wallpaper file: %s", old_path.name)

    def _prune_cache(self, config: AppConfig) -> None:
        """Prune the tile cache according to the configured limits."""
        self._progress.set(ProgressStage.PRUNING)
        removed = self._cache_manager.prune(
            max_age_hours=config.max_cache_age_hours,
            max_size_mb=config.max_cache_size_mb,
        )
        if removed:
            _logger.info("Cache cleanup removed %d old tile file(s).", removed)
