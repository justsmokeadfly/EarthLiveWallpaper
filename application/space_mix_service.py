"""Optional scheduled NASA APOD wallpaper updates."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path

from domain.enums import WallpaperMode
from infrastructure.nasa.nasa_media_service import NASAMediaService
from infrastructure.wallpaper.windows_wallpaper_setter import WindowsWallpaperSetter
from logger import get_logger

_logger = get_logger(__name__)


class SpaceMixService:
    """Background scheduler for NASA APOD wallpaper updates."""

    def __init__(self, media: NASAMediaService, wallpapers_dir: Path) -> None:
        self._media = media
        self._wallpapers_dir = wallpapers_dir
        self._setter = WindowsWallpaperSetter()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval_hours = 24.0

    def configure(self, enabled: bool, interval_hours: float) -> None:
        interval = max(0.01, interval_hours)
        if not enabled:
            self.stop()
            return
        if self._thread is not None and self._thread.is_alive():
            if interval == self._interval_hours:
                return
            self.stop()
        self._interval_hours = interval
        stop_event = threading.Event()
        self._stop_event = stop_event
        self._thread = threading.Thread(target=self._run, args=(stop_event,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread = None

    def trigger_now(self) -> bool:
        try:
            photo = self._media.get_apod()
            suffix = ".png" if ".png" in photo.image_url.lower() else ".jpg"
            stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            path = self._wallpapers_dir / f"space_mix_{photo.source}_{stamp}{suffix}"
            self._media.download(photo, path)
            return self._setter.apply(path, WallpaperMode.FIT)
        except Exception:
            _logger.exception("NASA APOD wallpaper update failed.")
            return False

    def _run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            if stop_event.wait(self._interval_hours * 3600):
                break
            self.trigger_now()
