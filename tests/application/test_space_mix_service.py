"""Regression tests for NASA-only scheduled wallpaper updates."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from application.space_mix_service import SpaceMixService
from domain.enums import WallpaperMode
from infrastructure.nasa.nasa_media_service import NASAMediaService, NASAPhoto
from infrastructure.wallpaper.windows_wallpaper_setter import WindowsWallpaperSetter


def test_nasa_apod_update_never_calls_flickr(tmp_path: Path) -> None:
    media = MagicMock(spec=NASAMediaService)
    photo = NASAPhoto(
        title="NASA APOD", description_en="Space image",
        image_url="https://apod.nasa.gov/apod/image.jpg",
        source_url="https://apod.nasa.gov/apod/image.jpg",
        source="nasa",
    )
    media.get_apod.return_value = photo
    setter = MagicMock(spec=WindowsWallpaperSetter)
    setter.apply.return_value = True
    service = SpaceMixService(media, tmp_path)
    service._setter = setter

    assert service.trigger_now() is True
    media.get_apod.assert_called_once_with()
    media.download.assert_called_once()
    assert media.download.call_args.args[0] is photo
    assert media.download.call_args.args[1].parent == tmp_path
    setter.apply.assert_called_once()
    assert setter.apply.call_args.args[1] == WallpaperMode.FIT


def test_changing_nasa_interval_stops_previous_worker(tmp_path: Path) -> None:
    media = MagicMock(spec=NASAMediaService)
    service = SpaceMixService(media, tmp_path)

    try:
        service.configure(enabled=True, interval_hours=24)
        first_event = service._stop_event
        service.configure(enabled=True, interval_hours=12)
        assert first_event.is_set()
        assert service._stop_event is not first_event
    finally:
        service.stop()
