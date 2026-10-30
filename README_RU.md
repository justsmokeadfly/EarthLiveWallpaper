# 🌍 EarthLive Wallpaper

Приложение для Windows: живые обои Земли со спутников Himawari и фотографии NASA APOD.

[English README](README.md) · [Скачать установщик](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

## Актуальные возможности

- 🌍 Снимки Земли Himawari-8/9: ручное и автоматическое обновление, настройка разрешения.
- 🚀 NASA Astronomy Picture of the Day (APOD): последняя доступная фотография дня (с откатом на предыдущий день, если опубликовано видео), описание, перевод, предпросмотр, поиск, избранное и скачивание.
- ⏰ Автоматическая установка NASA APOD с настраиваемым интервалом; есть кнопка ручного запуска. Используется только источник NASA APOD.
- 🖥️ Разные сохранённые обои для каждого монитора Windows, режимы Fill/Fit/Stretch/Tile/Center/Span.
- 🖼️ Галерея сохранённых обоев, история, GIF-таймлапс, управление кэшем.
- 🇷🇺🇬🇧 Русский и английский интерфейс, автозапуск, portable- и headless-режимы.

**Интеграция с Flickr удалена.** Приложение больше не загружает фотографии Уэбба и Хаббла через Flickr. Сохранённые ранее изображения останутся на диске и не удаляются этим обновлением.

## Установка в Windows

Скачать [EarthLive-Setup-Latest.exe](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe). Установка Python не требуется. Папка по умолчанию: `C:\Program Files\EarthLive Wallpaper`.

Для NASA APOD можно указать личный бесплатный ключ с [api.nasa.gov](https://api.nasa.gov/) в настройках. Общий DEMO_KEY ограничен по числу запросов.

## Проверки разработчика

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff check . --select S
python -m mypy --ignore-missing-imports --follow-imports=skip .
python -m pytest -q
```

Релизный workflow собирает portable-приложение через PyInstaller и установщик через Inno Setup. Исходники во время проверок не изменяются. Готовые Windows-файлы пока не подписаны цифровой подписью.

## Структура проекта

- `domain/` — сущности и интерфейсы
- `application/` — обновление обоев и планировщики
- `infrastructure/` — Himawari, NASA APOD, хранилище, Windows API
- `ui/` — окно CustomTkinter, диалоги и трей
- `tests/` — автоматические проверки

Автор: [justsmokeadfly](https://github.com/justsmokeadfly) · Лицензия MIT
