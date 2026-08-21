# 🌍 EarthLive Wallpaper v1.1.0

> A lightweight Windows desktop application that turns near-real-time Himawari-8/9 satellite imagery into a live Earth wallpaper.

**🇬🇧 English · 🇷🇺 [Русская версия](README_RU.md)**

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

EarthLive Wallpaper automatically downloads the latest available Himawari satellite tiles, assembles them into a full-disk Earth image, and sets it as your Windows wallpaper.

It is designed to stay lightweight, unobtrusive, and easy to configure while running quietly in the system tray.

## ⬇️ Download for Windows

**No Python installation is required for the packaged releases.**

Download **EarthLive Wallpaper v1.1.0** from the [GitHub Releases](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases) page.

- **Portable ZIP** — extract it anywhere and run `EarthLive.exe`.
- **Windows Installer** — install EarthLive with Start Menu, optional desktop shortcut, and optional Windows startup integration.

Releases are built automatically by GitHub Actions from version tags.

## ✨ Features

- 🛰️ Near-real-time **Himawari-8/9** satellite imagery
- 🖥️ Automatic Windows wallpaper updates
- ⚙️ Configurable image resolution: `2x2`, `4x4`, `8x8`, `16x16`
- ⏱️ Configurable update interval
- 🗂️ Wallpaper history with cache management
- 🖼️ Thumbnail gallery for previous wallpapers
- 🎞️ GIF timelapse generation from wallpaper history
- 🌗 Dark, light, and system themes
- 🌍 English and Russian interface
- 🚀 Optional Windows startup
- 📦 Portable mode
- 📴 Headless/background mode
- 🔄 Retry handling with exponential backoff
- 📝 Rotating application logs
- 🧩 Provider-based architecture for adding other satellite sources

## 🛰️ How it works

1. EarthLive Wallpaper checks the configured update interval.
2. It obtains the latest available Himawari image timestamp.
3. Image tiles are downloaded concurrently.
4. The tiles are assembled into a complete wallpaper.
5. The new image is applied to the Windows desktop.
6. Older wallpapers are retained according to the configured history size.
7. The process repeats automatically.

## 🏗️ Architecture

```text
EarthLiveWallpaper/
├── domain/             # Core entities and interfaces
├── application/        # Use cases and scheduling
├── infrastructure/    # Satellite providers, downloader, image assembly, Win32
├── ui/                 # CustomTkinter interface and system tray
├── app.py              # Dependency-injection composition root
├── main.py             # Application entry point
└── tests/              # Automated tests
```

### Main layers

- **`domain/`** — pure interfaces and contracts.
- **`application/`** — orchestrates wallpaper updates and scheduling.
- **`infrastructure/`** — satellite provider, downloading, image assembly, Windows integration, and persistence.
- **`ui/`** — CustomTkinter desktop interface, settings, dialogs, and system tray.
- **`app.py`** — wires concrete implementations into the application layer.
- **`main.py`** — application entry point.

## 💻 Requirements

For the packaged Windows releases:

- Windows 10 or Windows 11
- No Python installation required

For running from source:

- Windows 10 or Windows 11
- Python 3.11 or newer

## 📦 Installation

### Recommended: packaged release

Download either the Portable ZIP or Windows Installer from [Releases](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases).

### From source

```powershell
git clone https://github.com/justsmokeadfly/EarthLiveWallpaper.git
cd EarthLiveWallpaper
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

### Portable data mode

```powershell
python main.py --portable
```

Portable mode stores configuration, state, cache, wallpapers, and logs in a `data` directory next to the application.

## 🚀 Usage

Start EarthLive Wallpaper normally:

```powershell
python main.py
```

Available options:

```text
--headless       Run as a background updater without opening the main window.
--update-now     Force an immediate update, then continue normally.
--config <path>  Use a custom config.json file.
--portable       Store application data next to the application.
```

## ⚙️ Configuration

The default configuration file is:

```text
%APPDATA%\\EarthLive\\config.json
```

| Setting | Description | Default |
|---|---|---|
| `resolution` | Tile grid: `2x2`, `4x4`, `8x8`, `16x16` | `4x4` |
| `check_interval_hours` | Hours between automatic checks | `24` |
| `history_size` | Number of wallpapers retained | `10` |
| `theme` | `dark`, `light`, or `system` | `dark` |
| `language` | `en` or `ru` | `ru` |
| `autostart` | Launch EarthLive Wallpaper with Windows | `false` |
| `wallpaper_mode` | `fill`, `fit`, `stretch`, `tile`, `center`, or `span` | `fill` |
| `retry_count` | Maximum retries per tile | `3` |
| `retry_delay_seconds` | Base retry delay in seconds | `5` |
| `max_cache_age_hours` | Maximum cache age before cleanup | `168` |
| `max_cache_size_mb` | Maximum cache size in MB | `1024` |
| `paused` | Pause automatic updates | `false` |
| `provider` | Image provider | `himawari` |

## 📝 Logging

Logs are stored at `%APPDATA%\\EarthLive\\logs\\earthlive.log`.

## 🧩 Image providers

The provider registry is designed to support additional satellite sources. Currently available provider: `himawari`.

## 🏭 Building

```powershell
pip install -r requirements-dev.txt
pyinstaller --clean --noconfirm EarthLive.spec
```

The application is generated under `dist\\EarthLive\\EarthLive.exe`.

The Windows installer script is located in `installer\\EarthLive.iss`.

## 🧪 Testing

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

## 📄 License

EarthLive Wallpaper is released under the **MIT License**. See [LICENSE](LICENSE).

## ℹ️ Disclaimer

Himawari-8/9 imagery is provided by the Japan Meteorological Agency (JMA) / National Institute of Information and Communications Technology (NICT) for near-real-time public viewing.

EarthLive Wallpaper is an independent project and is **not affiliated with or endorsed by JMA or NICT**.

## 👤 Author

**justzef**

- GitHub: https://github.com/justzef
- Project: https://github.com/justsmokeadfly/EarthLiveWallpaper

---

<p align="center">Made for anyone who wants a living view of Earth on their desktop 🌍</p>
