# 🌍 EarthLive Wallpaper v1.3.2

> A lightweight Windows desktop application that turns near-real-time Himawari-8/9 satellite imagery into a live Earth wallpaper.

**🇬🇧 English · 🇷🇺 [Русская версия](README_RU.md)**

[![Download Installer](https://img.shields.io/badge/⬇_Download-Installer-2ea44f?style=for-the-badge&logo=windows)](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

EarthLive Wallpaper automatically downloads the latest available Himawari satellite tiles, validates them, assembles them into a full-disk Earth image, and sets it as your Windows wallpaper.

It is designed to stay lightweight, unobtrusive, and easy to configure while running quietly in the system tray.

## ✨ What's improved in v1.3.2

- 🖼️ New installations now use **FIT** as the default wallpaper display mode instead of FILL, preserving the complete Earth image without cropping.
- 📁 Windows Installer installs **EarthLive Wallpaper** under `C:\Program Files\EarthLive Wallpaper` instead of the per-user AppData Programs directory.
- 🪟 Installer, Start Menu, desktop shortcut, and startup integration use the **EarthLive Wallpaper** application name consistently.
- 🔒 Downloaded tiles are checked for valid image content, supported Content-Type, and safe size limits.
- ⚙️ Configuration values are validated and invalid values fall back safely to defaults.
- 🧵 Manual scheduler triggers are thread-safe and concurrent requests are safely coalesced.
- 🧪 CI gates changes with Ruff, mypy, and pytest.
- 📦 Windows releases are driven by version tags and validated before publishing.
- 💾 Application state and configuration use atomic writes.

## ⬇️ Download for Windows

**No Python installation is required for the packaged releases.**

**[⬇️ Download Installer](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)** — recommended. Installs EarthLive Wallpaper to `C:\Program Files\EarthLive Wallpaper`.

Download **EarthLive Wallpaper v1.3.2** from the [GitHub Releases](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases) page.

- **Windows Installer** — recommended. Installs EarthLive Wallpaper to `C:\Program Files\EarthLive Wallpaper` with Start Menu integration and optional desktop shortcut/startup integration.
- **Portable ZIP** — extract it anywhere and run `EarthLive.exe` without installation.
- **Standalone EXE** — run the packaged `EarthLive.exe` directly.

Releases are built automatically by GitHub Actions from semantic version tags such as `v1.3.2`. Each release is validated with linting, type checking, tests, PyInstaller, and installer checks.

## 👤 Author

**justsmokeadfly**

- GitHub: https://github.com/justsmokeadfly
- Project: https://github.com/justsmokeadfly/EarthLiveWallpaper

---

<p align="center">Made for anyone who wants a living view of Earth on their desktop 🌍</p>
