# 🌍 EarthLive Wallpaper v1.5.0

> Лёгкое приложение для Windows, которое превращает свежие спутниковые снимки Земли Himawari-8/9 в живые обои рабочего стола.

**🇬🇧 [English](README.md) · 🇷🇺 Русская версия**

[![⬇ Скачать установщик](https://img.shields.io/badge/⬇_Скачать-установщик-2ea44f?style=for-the-badge&logo=windows)](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)

[![CI](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/justsmokeadfly/EarthLiveWallpaper/actions/workflows/ci.yml)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=flat-square)](https://github.com/justsmokeadfly/EarthLiveWallpaper)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

**EarthLive Wallpaper v1.5.0** автоматически получает самый свежий доступный снимок Himawari, проверяет скачанные тайлы, собирает их в полноценное изображение диска Земли и устанавливает его как обои Windows.

Программа работает в фоновом режиме и может находиться в системном трее, практически не мешая работе пользователя.

## ✨ Что улучшено в v1.5.0

- 🖼️ Новая вкладка **«Обои»**: галерея миниатюр всех ранее скачанных обоев — можно повторно применить любую из них на рабочий стол или удалить конкретную обоину навсегда (с двухшаговым подтверждением, чтобы не удалить случайно).
- 🌐 Исправлены строки интерфейса, которые оставались на английском независимо от выбранного языка: список режимов обоев (Fill/Fit/Stretch/Tile/Center/Span), список тем (Dark/Light/System), подзаголовок приложения, подписи «Version»/«Author»/«Open on GitHub» в окне «О программе», а также сообщение об ошибке при неудачном применении обоев.
- 🧹 Убрана задвоенная строка «Author» в окне «О программе».
- 📌 Версия метаданных проекта синхронизирована с **1.5.0**.

## Что было в v1.4.0

- 🧹 **Ruff проверяет весь репозиторий**, а не только выборочные изменённые файлы.
- 🔎 Добавлены **security-правила Ruff (`S`)** для поиска распространённых небезопасных паттернов Python-кода.
- 🧠 **mypy проверяет весь репозиторий**, а не только выборочные файлы.
- 🧪 CI продолжает проверять Ruff, mypy и pytest на Windows.
- 🖼️ Режим отображения обоев **FIT остаётся режимом по умолчанию**, поэтому изображение Земли показывается полностью без обрезки.
- 📁 **Windows Installer устанавливает EarthLive Wallpaper в `C:\Program Files\EarthLive Wallpaper`**.
- 🔒 Скачанные тайлы проверяются на корректность изображения, Content-Type и безопасный размер.
- ⚙️ Некорректные значения конфигурации автоматически заменяются безопасными значениями по умолчанию.
- 🧵 Ручные обновления планировщика потокобезопасны, а одновременные запросы корректно объединяются.
- 💾 Конфигурация и состояние сохраняются атомарно.

> **Важно:** Windows-сборки пока **не имеют цифровой подписи**. Поэтому Microsoft Defender SmartScreen может показывать предупреждение «Неизвестный издатель» для установщика. Это ожидаемо для текущих unsigned open-source сборок.

## ⬇️ Скачать для Windows

Для готовых сборок **Python устанавливать не нужно**.

**[⬇️ Скачать установщик](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases/latest/download/EarthLive-Setup-Latest.exe)** — рекомендуется. Устанавливает EarthLive Wallpaper в `C:\Program Files\EarthLive Wallpaper`.

Перейдите на страницу [GitHub Releases](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases) и скачайте нужный вариант.

- **Windows Installer** — рекомендуется. Устанавливает EarthLive Wallpaper в `C:\Program Files\EarthLive Wallpaper`, добавляет программу в меню «Пуск» и позволяет создать ярлык на рабочем столе и включить автозапуск.
- **Portable ZIP** — распакуйте архив в любую папку и запустите `EarthLive.exe` без установки.
- **Standalone EXE** — отдельный готовый `EarthLive.exe`, который можно запустить напрямую.

Сборки и релизы создаются автоматически через GitHub Actions из семантических тегов, например `v1.5.0`. Каждая Windows-сборка проходит полную проверку Ruff, mypy, pytest, PyInstaller и установщика.

## ✨ Возможности

- 🛰️ Свежие спутниковые снимки **Himawari-8/9**
- 🖥️ Автоматическая смена обоев Windows
- 🖼️ Режим отображения обоев: **FIT** по умолчанию
- ⚙️ Разрешение изображения: `2x2`, `4x4`, `8x8`, `16x16`
- ⏱️ Настраиваемый интервал обновления
- 🗂️ История предыдущих обоев и управление кэшем
- 🖼️ Галерея миниатюр сохранённых изображений
- 🎞️ Создание GIF-таймлапсов из истории обоев
- 🌗 Тёмная, светлая и системная тема
- 🌍 Русский и английский интерфейс
- 🚀 Автозапуск вместе с Windows
- 📦 Портативный режим
- 📴 Фоновый/headless-режим
- 🔄 Повторные попытки загрузки при сетевых ошибках
- 📝 Ротация логов приложения
- 🧩 Архитектура с поддержкой дополнительных спутниковых источников

## 🛰️ Как это работает

1. EarthLive Wallpaper проверяет, наступило ли время обновления.
2. Получает время последнего доступного снимка Himawari.
3. Параллельно скачивает необходимые изображения-тайлы.
4. Проверяет размер, Content-Type и фактическую корректность каждого изображения.
5. Собирает тайлы в единое изображение Земли.
6. Устанавливает новое изображение как обои рабочего стола.
7. Удаляет старые данные согласно настройкам истории и кэша.
8. Повторяет процесс автоматически.

## 🎛️ Управление

Из графического интерфейса можно:

- посмотреть состояние последнего обновления;
- запустить обновление вручную;
- поставить автоматические обновления на паузу;
- просматривать историю обоев;
- создавать GIF-таймлапсы;
- выбирать разрешение снимка;
- менять интервал обновления;
- переключать тему интерфейса;
- выбрать русский или английский язык;
- включить автозапуск Windows;
- выбрать режим отображения обоев.

## 💻 Требования

### Готовая Windows-версия

- Windows 10 или Windows 11
- Python не требуется

### Запуск из исходников

- Windows 10 или Windows 11
- Python 3.11 или новее

## 📦 Установка

### Рекомендуемый способ — Windows Installer

Скачайте **Windows Installer** со страницы [Releases](https://github.com/justsmokeadfly/EarthLiveWallpaper/releases) или нажмите кнопку **«Скачать установщик»** вверху README. По умолчанию программа устанавливается в:

```text
C:\Program Files\EarthLive Wallpaper
```

Установщик добавляет EarthLive Wallpaper в меню «Пуск» и по желанию создаёт ярлык на рабочем столе и включает автозапуск вместе с Windows.

### Portable

Скачайте **Portable ZIP**, распакуйте его в любую папку и запустите `EarthLive.exe`.

### Запуск из исходников

```powershell
git clone https://github.com/justsmokeadfly/EarthLiveWallpaper.git
cd EarthLiveWallpaper
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

### Портативный режим

```powershell
python main.py --portable
```

## 🚀 Параметры запуска

Обычный запуск:

```powershell
python main.py
```

Доступны следующие параметры:

```text
--headless       Запуск в фоновом режиме без открытия главного окна.
--update-now     Немедленно выполнить обновление, затем продолжить обычную работу.
--config <path>  Использовать указанный файл config.json.
--portable       Хранить данные приложения рядом с программой.
```

## ⚙️ Настройки

Стандартный файл конфигурации находится здесь:

```text
%APPDATA%\\EarthLive\\config.json
```

| Настройка | Описание | По умолчанию |
|---|---|---|
| `resolution` | Сетка тайлов: `2x2`, `4x4`, `8x8`, `16x16` | `4x4` |
| `check_interval_hours` | Интервал между автоматическими проверками | `24` |
| `history_size` | Количество сохраняемых обоев | `10` |
| `theme` | `dark`, `light` или `system` | `dark` |
| `language` | `en` или `ru` | `ru` |
| `autostart` | Запускать EarthLive Wallpaper вместе с Windows | `false` |
| `wallpaper_mode` | `fill`, `fit`, `stretch`, `tile`, `center` или `span` | `fit` |
| `retry_count` | Максимальное число повторных попыток для тайла | `3` |
| `retry_delay_seconds` | Базовая задержка между повторными попытками | `5` |
| `max_cache_age_hours` | Максимальный возраст кэша | `168` |
| `max_cache_size_mb` | Максимальный размер кэша в МБ | `1024` |
| `paused` | Приостановить автоматические обновления | `false` |
| `provider` | Источник изображений | `himawari` |

Некорректные числовые и логические значения при чтении конфигурации безопасно заменяются значениями по умолчанию.

## 🏗️ Архитектура

```text
EarthLiveWallpaper/
├── domain/             # Основные сущности и интерфейсы
├── application/        # Сценарии работы и планирование обновлений
├── infrastructure/    # Спутниковые источники, загрузка, хранение и Win32
├── ui/                 # Интерфейс CustomTkinter и системный трей
├── app.py              # Сборка и внедрение зависимостей
├── main.py             # Точка входа
└── tests/              # Автоматические тесты
```

## 🛰️ Источники изображений

Сейчас используется провайдер `himawari`.

## 🏭 Сборка

```powershell
pip install -r requirements-dev.txt
pyinstaller --clean --noconfirm EarthLive.spec
```

Готовая программа появится здесь:

```text
dist\\EarthLive\\EarthLive.exe
```

Скрипт установщика находится в `installer\\EarthLive.iss`.

## 🧪 Тестирование

```powershell
pip install -r requirements-dev.txt
python -m ruff check .
python -m mypy --ignore-missing-imports .
python -m pytest -q
```

## 📄 Лицензия

EarthLive Wallpaper распространяется по лицензии **MIT**. Подробности находятся в файле [LICENSE](LICENSE).

## ℹ️ Дисклеймер

Изображения Himawari-8/9 предоставляются Japan Meteorological Agency (JMA) / National Institute of Information and Communications Technology (NICT) для публичного просмотра в режиме, близком к реальному времени.

EarthLive Wallpaper — независимый проект и **не связан с JMA или NICT и не поддерживается ими**.

## 👤 Автор

**justsmokeadfly**

- GitHub: https://github.com/justsmokeadfly
- Проект: https://github.com/justsmokeadfly/EarthLiveWallpaper

---

<p align="center">Сделано для всех, кто хочет видеть живую Землю прямо на рабочем столе 🌍</p>
