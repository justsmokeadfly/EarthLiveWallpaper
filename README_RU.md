# 🌍 EarthLive Wallpaper v1.3.0

> Лёгкое приложение для Windows, которое превращает свежие спутниковые снимки Himawari-8/9 в живые обои рабочего стола.

**🇬🇧 [English](README.md) · 🇷🇺 Русская версия**

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

**EarthLive Wallpaper v1.3.0** автоматически получает самый свежий доступный снимок Himawari, проверяет скачанные тайлы, собирает их в полноценное изображение диска Земли и устанавливает его как обои Windows.

## ✨ Что улучшено в v1.3.0

- 🔒 Скачанные тайлы проверяются на корректность изображения, Content-Type и безопасный размер.
- ⚙️ Некорректные значения конфигурации автоматически заменяются безопасными значениями по умолчанию.
- 🧵 Ручные обновления планировщика стали потокобезопасными; одновременные запросы корректно объединяются.
- 🧪 CI теперь проверяет Ruff, mypy и pytest.
- 📦 Windows-релизы полностью привязаны к Git tag — версии EXE, ZIP и Installer больше не расходятся.
- 🪟 Метаданные Installer и ссылки на проект исправлены и синхронизированы с текущим репозиторием.
- 💾 Конфигурация и состояние сохраняются атомарно.

## ⬇️ Скачать для Windows

Для готовых сборок **Python устанавливать не нужно**.

Скачайте **EarthLive Wallpaper v1.3.0** на странице [GitHub Releases](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases).

- **Portable ZIP** — распакуйте архив в любую папку и запустите `EarthLive.exe`.
- **Windows Installer** — обычная установка с меню «Пуск», дополнительным ярлыком на рабочем столе и возможностью автозапуска Windows.

Релизы автоматически собираются GitHub Actions из семантических тегов, например `v1.3.0`. Перед публикацией выполняются lint, type-check, pytest, проверка PyInstaller и проверка Installer.

## 👤 Автор

**justsmokeadfly**

- GitHub: https://github.com/justsmokeadfly
- Проект: https://github.com/justsmokeadfly/EarthLiveWallpaper

---

<p align="center">Сделано для всех, кто хочет видеть живую Землю прямо на рабочем столе 🌍</p>
