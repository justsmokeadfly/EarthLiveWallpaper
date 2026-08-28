"""Real winreg round-trip smoke test for AutostartManager.

Unlike the fakes used elsewhere in this suite, this test exercises the
actual HKEY_CURRENT_USER\\...\\Run registry key via the real winreg
module. It only runs on Windows (see tests/README.md for why every
other test avoids this), and cleans up after itself regardless of
outcome so it never leaves a stray autostart entry behind.
"""

from __future__ import annotations

import sys

import pytest

if sys.platform != "win32":
    pytest.skip(
        "AutostartManager requires the stdlib winreg module (Windows-only).",
        allow_module_level=True,
    )

import winreg  # noqa: E402 - must follow the platform guard above

from infrastructure.system.autostart import AutostartManager  # noqa: E402

_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "EarthLive Wallpaper"


def _read_run_value() -> str | None:
    """Read the raw registry value directly (bypassing AutostartManager)
    so the test verifies real registry state, not just the manager's
    own report of it.
    """
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH, 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE_NAME)
            return str(value)
    except FileNotFoundError:
        return None


class TestAutostartManagerRealRegistry:
    """End-to-end round trip against the real Windows registry."""

    def test_enable_writes_a_readable_run_value(self) -> None:
        manager = AutostartManager(executable_path=None)
        try:
            assert manager.enable() is True
            assert manager.is_enabled() is True
            raw_value = _read_run_value()
            assert raw_value is not None
            assert "--headless" in raw_value
        finally:
            manager.disable()

    def test_disable_removes_the_run_value(self) -> None:
        manager = AutostartManager(executable_path=None)
        manager.enable()

        result = manager.disable()

        assert result is True
        assert manager.is_enabled() is False
        assert _read_run_value() is None

    def test_disable_is_idempotent_when_already_absent(self) -> None:
        manager = AutostartManager(executable_path=None)
        manager.disable()  # ensure a clean slate regardless of prior state

        result = manager.disable()

        assert result is True
        assert manager.is_enabled() is False
