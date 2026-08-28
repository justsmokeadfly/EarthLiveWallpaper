"""Automatic rotation of NASA, Webb, and Hubble wallpapers."""

from __future__ import annotations

import secrets
import threading
from datetime import UTC, datetime
from pathlib import Path

from domain.enums import WallpaperMode
from infrastructure.nasa.nasa_media_service import NASAMediaService
from infrastructure.wallpaper.windows_wallpaper_setter import WindowsWallpaperSetter
from logger import get_logger

_logger = get_logger(__name__)


class SpaceMixService:
    """Background scheduler for a daily/random cosmic wallpaper mix."""

    def __init__(self, media: NASAMediaService, wallpapers_dir: Path) -> None:
        self._media = media
        self._wallpapers_dir = wallpapers_dir
        self._setter = WindowsWallpaperSetter()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval_hours = 24.0

    def configure(self, enabled: bool, interval_hours: float) -> None:
        self._interval_hours = max(0.01, interval_hours)
        if enabled:
            if self._thread is None or not self._thread.is_alive():
                self._stop_event.clear()
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()
        else:
            self.stop()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread = None

    def trigger_now(self) -> bool:
        try:
            photos = [self._media.get_apod()]
            photos.extend(self._media.get_webb_photos(limit=12))
            photos.extend(self._media.get_hubble_photos(limit=12))
            photo = secrets.choice(photos)
            suffix = ".png" if ".png" in photo.image_url.lower() else ".jpg"
            stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            path = self._wallpapers_dir / f"space_mix_{photo.source}_{stamp}{suffix}"
            self._media.download(photo, path)
            return self._setter.apply(path, WallpaperMode.FIT)
        except Exception:
            _logger.exception("Cosmic Mix update failed.")
            return False

    def _run(self) -> None:
        while not self._stop_event.is_set():
            if self._stop_event.wait(self._interval_hours * 3600):
                break
            self.trigger_now()
