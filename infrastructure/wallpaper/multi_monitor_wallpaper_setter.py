"""Per-monitor wallpaper control using Windows IDesktopWallpaper COM."""

from __future__ import annotations

import sys
from ctypes import HRESULT, POINTER, pointer
from ctypes.wintypes import LPCWSTR, LPWSTR, UINT
from pathlib import Path
from typing import Any, cast

from logger import get_logger

_logger = get_logger(__name__)
_CLSID = "{C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD}"
_IID = "{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}"


def get_monitor_count() -> int:
    """Return the number of monitors known to Windows."""
    if sys.platform != "win32":
        return 0
    import comtypes

    comtypes.CoInitialize()
    try:
        desktop_wallpaper = _create_desktop_wallpaper()
        return int(desktop_wallpaper.GetMonitorDevicePathCount())
    finally:
        comtypes.CoUninitialize()


def set_wallpapers_per_monitor(wallpapers: dict[int, Path]) -> bool:
    """Apply one image to each requested zero-based monitor index."""
    if sys.platform != "win32" or not wallpapers:
        return False
    import comtypes

    comtypes.CoInitialize()
    try:
        desktop_wallpaper = _create_desktop_wallpaper()
        count = int(desktop_wallpaper.GetMonitorDevicePathCount())
        if any(index < 0 or index >= count for index in wallpapers):
            return False
        for index, path in wallpapers.items():
            if not path.exists():
                _logger.error("Wallpaper does not exist: %s", path)
                return False
            monitor_id = desktop_wallpaper.GetMonitorDevicePathAt(index)
            desktop_wallpaper.SetWallpaper(monitor_id, str(path.resolve()))
        return True
    except (OSError, RuntimeError):
        _logger.exception("Failed to set per-monitor wallpapers.")
        return False
    finally:
        comtypes.CoUninitialize()


def _create_desktop_wallpaper() -> Any:
    if sys.platform != "win32":
        raise RuntimeError("Per-monitor wallpapers require Windows.")

    import comtypes
    from comtypes import COMMETHOD, GUID, IUnknown

    class DesktopWallpaper(IUnknown):
        _iid_ = GUID(_IID)
        _methods_ = [
            COMMETHOD(
                [],
                HRESULT,
                "SetWallpaper",
                (["in"], LPCWSTR, "monitorID"),
                (["in"], LPCWSTR, "wallpaper"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "GetMonitorDevicePathAt",
                (["in"], UINT, "monitorIndex"),
                (["out", "string"], POINTER(LPWSTR), "monitorID"),
            ),
            COMMETHOD(
                [],
                HRESULT,
                "GetMonitorDevicePathCount",
                (["out"], POINTER(UINT), "count"),
            ),
        ]

        def SetWallpaper(self, monitor_id: str, wallpaper: str) -> None:
            self.__com_SetWallpaper(LPCWSTR(monitor_id), LPCWSTR(wallpaper))

        def GetMonitorDevicePathAt(self, monitor_index: int) -> str:
            monitor_id = LPWSTR()
            self.__com_GetMonitorDevicePathAt(UINT(monitor_index), pointer(monitor_id))
            return str(monitor_id.value or "")

        def GetMonitorDevicePathCount(self) -> int:
            count = UINT()
            self.__com_GetMonitorDevicePathCount(pointer(count))
            return int(count.value)

    return cast(Any, comtypes.CoCreateInstance(GUID(_CLSID), interface=DesktopWallpaper))
