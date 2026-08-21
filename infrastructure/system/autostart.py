"""Manages launching EarthLive Wallpaper automatically at Windows login.

Uses the per-user ``HKEY_CURRENT_USER\\...\\Run`` registry key rather than
a Scheduled Task or Startup-folder shortcut: it requires no elevated
privileges, is trivially inspectable/removable by the user (or an
uninstaller) via the registry, and is the standard mechanism most
lightweight Windows utilities use.
"""

from __future__ import annotations

import sys
import winreg
from pathlib import Path

from logger import get_logger

_logger = get_logger(__name__)

_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "EarthLive Wallpaper"


class AutostartManager:
    """Enables/disables/checks EarthLive Wallpaper's Windows login autostart entry."""

    def __init__(self, executable_path: Path | None = None) -> None:
        """Initialize the manager.

        Args:
            executable_path: Path to the executable (or script) to launch
                at login. Defaults to the currently running interpreter
                plus this package's entry point, which is correct both for
                a frozen PyInstaller build (``sys.executable`` is the
                .exe itself) and for running from source.
        """
        self._executable_path = executable_path or self._default_command()

    def is_enabled(self) -> bool:
        """Return whether the autostart registry entry currently exists."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH, 0, winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, _VALUE_NAME)
                return True
        except FileNotFoundError:
            return False
        except OSError:
            _logger.exception("Failed to read autostart registry entry.")
            return False

    def enable(self) -> bool:
        """Create the autostart registry entry.

        Returns:
            ``True`` on success, ``False`` on failure.
        """
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key, _VALUE_NAME, 0, winreg.REG_SZ, self._executable_path
                )
            _logger.info("Autostart enabled: %s", self._executable_path)
            return True
        except OSError:
            _logger.exception("Failed to enable autostart.")
            return False

    def disable(self) -> bool:
        """Remove the autostart registry entry, if present.

        Returns:
            ``True`` on success or if the entry was already absent,
            ``False`` on failure.
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, _VALUE_NAME)
            _logger.info("Autostart disabled.")
            return True
        except FileNotFoundError:
            return True
        except OSError:
            _logger.exception("Failed to disable autostart.")
            return False

    @staticmethod
    def _default_command() -> str:
        """Build the default launch command for the current run mode."""
        if getattr(sys, "frozen", False):
            # Running as a PyInstaller-built executable.
            return f'"{sys.executable}" --headless'
        # Running from source: launch via the same interpreter.
        entry_point = Path(__file__).resolve().parents[2] / "main.py"
        return f'"{sys.executable}" "{entry_point}" --headless'
