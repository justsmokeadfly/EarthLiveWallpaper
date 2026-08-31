# 🌍 EarthLive Wallpaper v1.8.1

> Лёгкое приложение для Windows, которое превращает свежие спутниковые снимки Himawari-8/9 в живые обои рабочего стола и добавляет NASA, James Webb, Hubble, «Космический микс» и разные обои для разных мониторов.

**🇬🇧 [English](README.md) · 🇷🇺 Русская версия**

[![⬇ Скачать установщик](https://img.shields.io/badge/⬇_Скачать-установщик-2ea44f?style=for-the-badge&logo=windows)](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

EarthLive Wallpaper автоматически получает самый свежий доступный снимок Himawari, собирает его в полноценное изображение Земли и устанавливает как обои Windows.

## 🔒 Обновление безопасности в v1.8.1

- Обновлена библиотека `Pillow` с `10.3–10.x` до `12.3+` — устранены несколько опубликованных уязвимостей (проблемы с безопасностью памяти и отказом в обслуживании при обработке недоверенных изображений).
- Исправлена необработанная ошибка `comtypes.COMError` в коде установки обоев на разные мониторы, которая раньше могла приводить к падению вместо корректной обработки сбоя.

## ✨ Что нового в v1.8.0

### 🚀 NASA Fotos
- NASA Picture of the Day (APOD).
- 🔎 Поиск по названию и описанию.
- ⭐ Локальное избранное.
- Превью, название и описание.
- Переключение RU / EN, русский выбран по умолчанию.
- Скачивание с реальным индикатором прогресса.
- Установка фотографии как обоев.

### 🔭 James Webb Fotos
- Свежие изображения из официального Flickr-альбома NASA Webb Telescope.
- Настоящие Flickr-миниатюры для быстрой галереи.
- Оригинал загружается только при скачивании или установке как обоев.
- Поиск и ⭐ Избранное.
- Описания фотографий из Flickr.
- RU / EN, русский выбран по умолчанию.
- Асинхронный перевод без зависания интерфейса.

### 🛰️ Hubble Fotos
- Фотографии Hubble из официальной коллекции NASA Hubble.
- Тот же интерфейс превью, поиска, избранного, перевода и установки обоев.

### 🌌 «Космический микс»
- Дополнительный автоматический режим смены обоев.
- Источники: NASA APOD, James Webb и Hubble.
- Настраиваемый интервал.
- Случайный выбор доступного космического изображения.
- Кнопка ручного запуска «Космического микса» есть в главном окне.

### 🖥️ Разные обои для разных мониторов
- Можно назначить отдельную сохранённую фотографию каждому монитору.
- Используется нативный Windows-интерфейс управления обоями.
- Монитор 1, монитор 2 и дополнительные мониторы настраиваются независимо.

### 🛰️ Основные функции EarthLive
- Свежие спутниковые снимки Himawari-8/9.
- Автоматическое и ручное обновление Земли.
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

Сборки создаются автоматически через GitHub Actions из семантических тегов, например `v1.8.0`. Перед выпуском проходят Ruff, security-правила Ruff, mypy, pytest, PyInstaller и проверку установщика.

## 🖼️ Режимы установки обоев

Для фотографий NASA, James Webb и Hubble доступны:

- **Заполнить (Fill)** — заполнить экран, при необходимости обрезав края.
- **Вписать (Fit)** — показать всё изображение без обрезки.
- **Растянуть (Stretch)** — растянуть изображение на экран.
- **Замостить (Tile)** — повторять изображение.
- **По центру (Center)** — оставить исходный размер и расположить по центру.
- **На все мониторы (Span)** — растянуть на все мониторы.

## 🌐 Источники фотографий

- **NASA APOD:** NASA Picture of the Day API.
- **James Webb:** официальный Flickr-альбом NASA Webb Telescope.
- **Hubble:** официальная коллекция NASA Hubble.

## 🔎 Инструменты галереи

Галереи NASA, Webb и Hubble поддерживают поиск, избранное, лёгкие миниатюры, двуязычные описания и установку фотографий как обоев.

## 🏗️ Архитектура

```text
EarthLiveWallpaper/
├── domain/             # Основные сущности и интерфейсы
├── application/        # Сценарии работы, планирование и «Космический микс»
├── infrastructure/    # Спутниковые источники, NASA/Webb/Hubble, загрузка, хранение и Win32
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
