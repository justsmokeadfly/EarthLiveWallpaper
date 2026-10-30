"""Keep the project, application, installer and HTTP versions synchronized."""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def _quoted_value(path: Path, prefix: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split('"')[1]
    raise AssertionError(f"Missing {prefix!r} in {path}")


def test_version_consistency() -> None:
    version = _quoted_value(_ROOT / "pyproject.toml", "version = ")
    about = _quoted_value(_ROOT / "ui" / "about_dialog.py", "APP_VERSION = ")
    installer = _quoted_value(_ROOT / "installer" / "EarthLive.iss", "#define MyAppVersion ")
    downloader = (_ROOT / "infrastructure" / "download" / "http_tile_downloader.py").read_text(
        encoding="utf-8"
    )

    assert version == about == installer
    assert f"EarthLiveWallpaper/{version}" in downloader
