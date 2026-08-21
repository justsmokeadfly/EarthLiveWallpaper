"""Windows desktop wallpaper setter using the Win32 API directly via
``ctypes`` (no dependency on pywin32 for the core call, keeping this
module portable and simple to unit-test by mocking ``ctypes.windll``).

Wallpaper *positioning* (fill/fit/stretch/tile/center/span) is controlled
by two registry values (``WallpaperStyle`` and ``TileWallpaper``) under
``HKEY_CURRENT_USER\\Control Panel\\Desktop``, which must be set *before*
calling ``SystemParametersInfoW`` for the new mode to take effect.
"""

from __future__ import annotations

import ctypes
import sys
import winreg
from pathlib import Path

from domain.enums import WallpaperMode
from domain.interfaces import WallpaperSetter
from logger import get_logger

_logger = get_logger(__name__)

_SPI_SETDESKWALLPAPER = 0x0014
_SPIF_UPDATEINIFILE = 0x01
_SPIF_SENDWININICHANGE = 0x02

_REGISTRY_KEY_PATH = r"Control Panel\Desktop"

# Maps our domain-level WallpaperMode to the (WallpaperStyle, TileWallpaper)
# registry value pair Windows expects.
_MODE_TO_REGISTRY_VALUES: dict[WallpaperMode, tuple[str, str]] = {
    WallpaperMode.FILL: ("10", "0"),
    WallpaperMode.FIT: ("6", "0"),
    WallpaperMode.STRETCH: ("2", "0"),
    WallpaperMode.TILE: ("0", "1"),
    WallpaperMode.CENTER: ("0", "0"),
    WallpaperMode.SPAN: ("22", "0"),
}


class WindowsWallpaperSetter(WallpaperSetter):
    """Applies a wallpaper image using the native Windows API."""

    def apply(self, image_path: Path, mode: WallpaperMode) -> bool:
        """Set the desktop wallpaper and its positioning mode.

        Args:
            image_path: Path to the image file to apply. Must be an
                absolute path; Windows requires this for
                ``SystemParametersInfoW`` to resolve it correctly.
            mode: Desired wallpaper positioning mode.

        Returns:
            ``True`` if the wallpaper was applied successfully, ``False``
            on any failure (never raises).
        """
        if sys.platform != "win32":
            _logger.error("Wallpaper setting is only supported on Windows.")
            return False

        if not image_path.exists():
            _logger.error("Cannot set wallpaper: file does not exist: %s", image_path)
            return False

        try:
            self._apply_registry_style(mode)
        except OSError:
            _logger.exception("Failed to write wallpaper style to registry.")
            return False

        try:
            absolute_path = str(image_path.resolve())
            result = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
                _SPI_SETDESKWALLPAPER,
                0,
                absolute_path,
                _SPIF_UPDATEINIFILE | _SPIF_SENDWININICHANGE,
            )
            if not result:
                _logger.error(
                    "SystemParametersInfoW reported failure for %s.", absolute_path
                )
                return False
        except OSError:
            _logger.exception("Failed to call SystemParametersInfoW for %s.", image_path)
            return False

        _logger.info("Wallpaper applied: %s (mode=%s).", image_path.name, mode.value)
        return True

    @staticmethod
    def _apply_registry_style(mode: WallpaperMode) -> None:
        """Write the WallpaperStyle/TileWallpaper registry values for the
        given mode.

        Args:
            mode: The desired wallpaper positioning mode.

        Raises:
            OSError: If the registry key cannot be opened or written.
        """
        style_value, tile_value = _MODE_TO_REGISTRY_VALUES[mode]
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REGISTRY_KEY_PATH, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style_value)
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, tile_value)
