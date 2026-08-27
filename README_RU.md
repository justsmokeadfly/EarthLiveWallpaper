# 🌍 EarthLive Wallpaper v1.7.0

> Лёгкое приложение для Windows, которое превращает свежие спутниковые снимки Himawari-8/9 в живые обои рабочего стола и добавляет галереи NASA и James Webb.

**🇬🇧 [English](README.md) · 🇷🇺 Русская версия**

[![⬇ Скачать установщик](https://img.shields.io/badge/⬇_Скачать-установщик-2ea44f?style=for-the-badge&logo=windows)](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

EarthLive Wallpaper автоматически получает самый свежий доступный снимок Himawari, собирает его в полноценное изображение Земли и устанавливает как обои Windows.

## ✨ Что нового в v1.7.0

### 🚀 NASA Fotos
- NASA Picture of the Day (APOD).
- 🔎 Поиск по названию и описанию.
- ⭐ Избранное с локальным сохранением.
- Превью, название и описание фотографии.
- Переключение описания **RU / EN**, русский выбран по умолчанию.
- Скачивание с индикатором прогресса.
- Установка выбранной фотографии как обоев.

### 🔭 James Webb Fotos
- Свежие изображения из официального Flickr-альбома NASA Webb Telescope.
- 🔎 Поиск по названию и описанию.
- ⭐ Избранное с локальным сохранением.
- Лёгкие миниатюры вместо загрузки оригиналов при просмотре галереи.
- Описания фотографий из Flickr.
- Переключение **RU / EN**, русский выбран по умолчанию.
- Перевод выполняется асинхронно, поэтому интерфейс не зависает.
- Скачивание с прогрессом и установка фотографии как обоев.

### 🛰️ Основные функции EarthLive
- Свежие спутниковые снимки Himawari-8/9.
- Автоматическое и ручное обновление обоев.
- История обоев и управление кэшем.
- Галерея сохранённых обоев.
- Создание GIF-таймлапсов.
- Тёмная, светлая и системная тема.
- Русский и английский интерфейс.
- Автозапуск вместе с Windows.
- Portable и headless-режимы.

## ⬇️ Скачать для Windows

Для готовых сборок Python устанавливать не нужно.

**[⬇️ Скачать установщик](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)** — рекомендуется. Устанавливает EarthLive Wallpaper в `C:\Program Files\EarthLive Wallpaper`.

Сборки создаются автоматически через GitHub Actions из семантических тегов, например `v1.7.0`. Перед выпуском проходят Ruff, security-правила Ruff, mypy, pytest, PyInstaller и проверку установщика.

## 🖼️ Режимы установки обоев

Для фотографий NASA и James Webb можно выбрать:

- **Заполнить (Fill)** — заполнить экран, при необходимости обрезав края.
- **Вписать (Fit)** — показать всё изображение без обрезки.
- **Растянуть (Stretch)** — растянуть изображение на экран.
- **Замостить (Tile)** — повторять изображение.
- **По центру (Center)** — оставить исходный размер и расположить по центру.
- **На все мониторы (Span)** — растянуть на все мониторы.

## 🌐 Источники фотографий

- **NASA APOD:** NASA Picture of the Day API.
- **James Webb:** официальный Flickr-альбом NASA Webb Telescope.

## 🔎 Инструменты галереи

Галереи NASA и Webb поддерживают поиск по названию и описанию, а также фильтр **⭐ Избранное**. Избранные фотографии сохраняются локально и не требуют аккаунта или облачного сервиса.

## 🏗️ Архитектура

```text
EarthLiveWallpaper/
├── domain/             # Основные сущности и интерфейсы
├── application/        # Сценарии работы и планирование
├── infrastructure/    # Спутниковые источники, NASA/Webb, избранное, загрузка и Win32
├── ui/                 # Интерфейс CustomTkinter и системный трей
├── app.py              # Сборка и внедрение зависимостей
├── main.py             # Точка входа
└── tests/              # Автоматические тесты
```

## 🧪 Проверки для разработки

```powershell
pip install -r requirements-dev.txt
python -m ruff check .
python -m mypy --ignore-missing-imports --follow-imports=skip .
python -m pytest -q
```

## ℹ️ Примечание о выпуске

Windows-сборки пока не имеют цифровой подписи, поэтому SmartScreen может показывать предупреждение «Неизвестный издатель».

## 👤 Автор

**justsmokeadfly**

- GitHub: https://github.com/justsmokeadfly
- Project: https://github.com/justsmokeadfly/EarthLiveWallpaper

---

<p align="center">Для тех, кто хочет видеть Землю и космос прямо на рабочем столе 🌍✨</p>
