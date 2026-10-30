"""Guard consistency of the version shown and shipped in Windows builds."""

from __future__ import annotations

import re
from pathlib import Path

from ui.about_dialog import APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


def test_version_is_consistent() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    installer = (ROOT / "installer" / "EarthLive.iss").read_text(encoding="utf-8")
    downloader = (ROOT / "infrastructure" / "download" / "http_tile_downloader.py").read_text(
        encoding="utf-8"
    )
    project_version = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert project_version is not None
    assert project_version.group(1) == APP_VERSION
    match = re.search(r'#define MyAppVersion "([^"]+)"', installer)
    assert match is not None
    assert match.group(1) == APP_VERSION
    assert f"EarthLiveWallpaper/{APP_VERSION}" in downloader
