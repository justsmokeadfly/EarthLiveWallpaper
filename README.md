# 🌍 EarthLive Wallpaper

Windows desktop wallpaper application with live Himawari satellite imagery and NASA APOD photos.

[Русская документация](README_RU.md) · [Download installer](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

## Current features

- 🌍 Himawari-8/9 Earth imagery: manual and scheduled wallpaper updates, configurable tile resolution.
- 🚀 NASA Astronomy Picture of the Day (APOD): today's latest available image (with fallback on video days), search, description translation, previews, local favorites and download.
- ⏰ Optional automatic NASA APOD wallpaper updates at a configurable interval, with manual update button. APOD is the only source of this mode.
- 🖥️ Different saved wallpapers per Windows monitor; Fill, Fit, Stretch, Tile, Center and Span modes.
- 🖼️ Saved wallpaper gallery, history, GIF timelapse, cache management.
- 🇷🇺🇬🇧 Russian and English UI, autostart, portable and headless operation.

**Flickr integration has been removed.** The application does not download Webb or Hubble photos from Flickr. Previously saved images remain in their local folders and are not deleted by this change.

## Windows installation

Download [EarthLive-Setup-Latest.exe](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe). No local Python installation is required. Installer default: `C:\Program Files\EarthLive Wallpaper`.

For NASA APOD, an optional free personal key from [api.nasa.gov](https://api.nasa.gov/) can be entered in Settings; the shared DEMO_KEY is rate-limited.

## Development

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff check . --select S
python -m mypy --ignore-missing-imports --follow-imports=skip .
python -m pytest -q
```

The Windows release workflow also builds the PyInstaller portable app and Inno Setup installer. It checks code without automatically modifying sources. Published Windows executables are currently unsigned.

## Project

- `domain/` — entities and interfaces
- `application/` — update and scheduling services
- `infrastructure/` — Himawari provider, NASA APOD, persistence, wallpaper API
- `ui/` — CustomTkinter window, dialogs and tray
- `tests/` — automated checks

Author: [justsmokeadfly](https://github.com/justsmokeadfly) · MIT License
