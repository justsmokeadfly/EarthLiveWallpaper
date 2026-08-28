# 🌍 EarthLive Wallpaper v1.8.0

> A lightweight Windows desktop application that turns near-real-time Himawari-8/9 satellite imagery into live Earth wallpaper, with NASA, James Webb, Hubble, Cosmic Mix and per-monitor wallpaper controls.

**🇬🇧 English · 🇷🇺 [Русская версия](README_RU.md)**

[![Download Installer](https://img.shields.io/badge/⬇_Download-Installer-2ea44c?style=for-the-badge&logo=windows)](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

EarthLive Wallpaper downloads the latest available Himawari satellite tiles, validates them, assembles a full-disk Earth image, and applies it as Windows wallpaper.

## ✨ What's new in v1.8.0

### 🚀 NASA Fotos
- NASA Picture of the Day (APOD).
- Search by title and description.
- ⭐ Local favorites.
- Preview, title and description.
- RU / EN descriptions, Russian selected by default.
- Real download progress.
- Set photos as wallpaper.

### 🔭 James Webb Fotos
- Fresh images from the official NASA Webb Telescope Flickr album.
- Official Flickr thumbnails for the gallery, with originals downloaded only on demand.
- Search and ⭐ Favorites.
- Photo descriptions from Flickr.
- RU / EN descriptions with asynchronous translation.
- Download progress and wallpaper installation.

### 🛰️ Hubble Fotos
- Hubble photos from the official NASA Hubble Flickr collection.
- Same preview, search, favorites, translation and wallpaper workflow as NASA/Webb.

### 🌌 Cosmic Mix
- Optional automatic wallpaper rotation across NASA APOD, James Webb and Hubble.
- Configurable interval.
- Random selection from the available space-photo sources.
- Manual **Cosmic Mix** trigger is also available from the main window.

### 🖥️ Per-monitor wallpapers
- Assign different saved wallpapers to individual Windows monitors.
- Uses the native Windows desktop wallpaper COM interface.
- Configure monitor 1, monitor 2, and additional monitors independently.

### 🛰️ Existing EarthLive features
- Near-real-time Himawari-8/9 imagery.
- Automatic and manual Earth updates.
- Wallpaper history and cache management.
- Wallpapers gallery.
- GIF timelapse creation.
- Dark, light and system themes.
- English and Russian UI.
- Windows startup integration.
- Portable and headless modes.

## ⬇️ Download for Windows

No Python installation is required for packaged releases.

**[⬇️ Download Installer](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)** — recommended. Installs to `C:\Program Files\EarthLive Wallpaper`.

Releases are built automatically from semantic version tags such as `v1.8.0`. Each release runs Ruff, security rules, mypy, pytest, PyInstaller and installer verification.

## 🖼️ Wallpaper modes

NASA, James Webb and Hubble photos support:

- **Fill** — fill the screen, cropping when necessary.
- **Fit** — show the full image without cropping.
- **Stretch** — stretch to the screen.
- **Tile** — repeat the image.
- **Center** — keep the original size and center it.
- **Span** — span across all monitors.

## 🌐 Photo sources

- **NASA APOD:** NASA Picture of the Day API.
- **James Webb:** official NASA Webb Telescope Flickr album.
- **Hubble:** official NASA Hubble Flickr collection.

## 🔎 Gallery tools

NASA, Webb and Hubble galleries include search, local favorites, lightweight previews, bilingual descriptions and wallpaper actions.

## 🏗️ Architecture

```text
EarthLiveWallpaper/
├── domain/             # Core entities and interfaces
├── application/        # Use cases, scheduling and Cosmic Mix
├── infrastructure/    # Providers, NASA/Webb/Hubble, downloads, storage and Win32
├── ui/                 # CustomTkinter UI and system tray
├── app.py              # Dependency wiring
├── main.py             # Entry point
└── tests/              # Automated tests
```

## 🧪 Development checks

```powershell
pip install -r requirements-dev.txt
python -m ruff check .
python -m mypy --ignore-missing-imports --follow-imports=skip .
python -m pytest -q
```

## ℹ️ Release note

Windows binaries are currently unsigned. SmartScreen may therefore show an “unknown publisher” warning for the installer.

## 👤 Author

**justsmokeadfly**

- GitHub: https://github.com/justsmokeadfly
- Project: https://github.com/justsmokeadfly/EarthLiveWallpaper

---

<p align="center">Made for anyone who wants a living view of Earth and space on their desktop 🌍✨</p>
