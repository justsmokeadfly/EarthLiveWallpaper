"""Lightweight UI localization for EarthLive."""
from __future__ import annotations

from domain.enums import Language

_STRINGS: dict[Language, dict[str, str]] = {
    Language.EN: {
        "app_title": "EarthLive", "app_header": "🌍  EarthLive", "app_subtitle": "Live Earth wallpaper",
        "status_checking": "Checking status...", "status_waiting": "Waiting for first check",
        "outcome.success": "Success", "outcome.already_up_to_date": "Already up to date", "outcome.duplicate_content": "Duplicate content",
        "outcome.network_unavailable": "No internet connection", "outcome.provider_unavailable": "Satellite server unavailable", "outcome.download_failed": "Download failed",
        "outcome.assembly_failed": "Image assembly failed", "outcome.wallpaper_apply_failed": "Failed to apply wallpaper", "outcome.unexpected_error": "Unexpected error", "outcome.paused": "Updates paused",
        "label.last_image_time": "Last image time", "label.last_update": "Last update", "label.next_update": "Next update", "label.cache_size": "Cache size", "label.resolution": "Resolution", "label.total_updates": "Total updates applied", "label.never": "Never",
        "button.update_now": "Update now", "button.updating": "Updating...", "button.open_folder": "Open wallpapers folder", "button.settings": "Settings", "button.about": "About", "button.save": "Save", "button.cancel": "Cancel", "button.pause": "Pause updates", "button.resume": "Resume updates", "button.wallpapers": "Wallpapers",
        "wallpapers.title": "Wallpapers", "wallpapers.empty": "No wallpapers saved yet.", "wallpapers.apply": "Apply", "wallpapers.applied": "Applied!", "wallpapers.apply_failed": "Could not apply: {name}", "wallpapers.delete": "Delete", "wallpapers.delete_confirm": "Confirm delete", "wallpapers.deleted": "Deleted.", "wallpapers.delete_failed": "Could not delete: {name}", "wallpapers.create_timelapse": "Create timelapse (GIF)", "wallpapers.creating_timelapse": "Creating timelapse...", "wallpapers.timelapse_success": "Timelapse saved to {path}", "wallpapers.timelapse_failed": "Failed to create timelapse. Need at least 2 images in history.", "wallpapers.close": "Close",
        "wallpaper_mode.fill": "Fill", "wallpaper_mode.fit": "Fit", "wallpaper_mode.stretch": "Stretch", "wallpaper_mode.tile": "Tile", "wallpaper_mode.center": "Center", "wallpaper_mode.span": "Span (all monitors)", "theme.dark": "Dark", "theme.light": "Light", "theme.system": "System",
        "notification.title": "EarthLive", "progress.checking": "Checking for a new image...", "progress.downloading": "Downloading tiles: {current}/{total}", "progress.assembling": "Assembling image...", "progress.applying": "Applying wallpaper...", "progress.pruning": "Cleaning up cache...",
        "settings.title": "Settings", "settings.resolution": "Resolution", "settings.check_interval": "Check interval (hours)", "settings.history_size": "History size", "settings.theme": "Theme", "settings.language": "Language", "settings.autostart": "Launch at Windows login", "settings.wallpaper_mode": "Wallpaper mode", "settings.retry_count": "Retry count", "settings.retry_delay": "Retry delay (seconds)", "settings.space_mix": "Automatic Cosmic Mix", "settings.space_mix_interval": "Cosmic Mix interval (hours)", "settings.nasa_api_key": "NASA API key (optional, leave blank for DEMO_KEY)", "settings.invalid_value": "Invalid value: {error}", "settings.save_failed": "Failed to save settings. Check logs.",
        "monitors.title": "Different wallpapers per monitor", "monitors.unsupported": "Per-monitor wallpapers require Windows 10/11.", "monitors.no_wallpapers": "Download at least one wallpaper first.", "monitors.apply": "Apply to monitors", "monitors.applied": "Wallpapers assigned to monitors.", "monitors.failed": "Could not apply monitor wallpapers.",
        "about.title": "About EarthLive", "about.description": "EarthLive brings fresh Earth imagery plus NASA, James Webb and Hubble space photos to your Windows desktop.", "about.version": "Version", "about.author": "Author", "about.license": "License", "about.source": "Source code", "about.open_github": "Open on GitHub ↗", "about.close": "Close",
        "tray.open": "Open EarthLive", "tray.update_now": "Update now", "tray.quit": "Quit",
    },
    Language.RU: {
        "app_title": "EarthLive", "app_header": "🌍  EarthLive", "app_subtitle": "Живые обои Земли",
        "status_checking": "Проверка статуса...", "status_waiting": "Ожидание первой проверки",
        "outcome.success": "Успешно обновлено", "outcome.already_up_to_date": "Уже актуально", "outcome.duplicate_content": "Дублирующееся изображение", "outcome.network_unavailable": "Нет подключения к интернету", "outcome.provider_unavailable": "Сервер спутника недоступен", "outcome.download_failed": "Ошибка загрузки", "outcome.assembly_failed": "Ошибка сборки изображения", "outcome.wallpaper_apply_failed": "Не удалось установить обои", "outcome.unexpected_error": "Непредвиденная ошибка", "outcome.paused": "Обновления приостановлены",
        "label.last_image_time": "Время последнего снимка", "label.last_update": "Последнее обновление", "label.next_update": "Следующее обновление", "label.cache_size": "Размер кэша", "label.resolution": "Разрешение", "label.total_updates": "Всего обновлений", "label.never": "Никогда",
        "button.update_now": "Обновить сейчас", "button.updating": "Обновление...", "button.open_folder": "Открыть папку с обоями", "button.settings": "Настройки", "button.about": "О программе", "button.save": "Сохранить", "button.cancel": "Отмена", "button.pause": "Приостановить обновления", "button.resume": "Возобновить обновления", "button.wallpapers": "Обои",
        "wallpapers.title": "Обои", "wallpapers.empty": "Пока нет сохранённых обоев.", "wallpapers.apply": "Применить", "wallpapers.applied": "Применено!", "wallpapers.apply_failed": "Не удалось применить: {name}", "wallpapers.delete": "Удалить", "wallpapers.delete_confirm": "Точно удалить?", "wallpapers.deleted": "Удалено.", "wallpapers.delete_failed": "Не удалось удалить: {name}", "wallpapers.create_timelapse": "Создать таймлапс (GIF)", "wallpapers.creating_timelapse": "Создание таймлапса...", "wallpapers.timelapse_success": "Таймлапс сохранён: {path}", "wallpapers.timelapse_failed": "Не удалось создать таймлапс. Нужно минимум 2 изображения в истории.", "wallpapers.close": "Закрыть",
        "wallpaper_mode.fill": "Заполнение", "wallpaper_mode.fit": "По размеру экрана", "wallpaper_mode.stretch": "Растянуть", "wallpaper_mode.tile": "Плитка", "wallpaper_mode.center": "По центру", "wallpaper_mode.span": "На весь экран (все мониторы)", "theme.dark": "Тёмная", "theme.light": "Светлая", "theme.system": "Системная",
        "notification.title": "EarthLive", "progress.checking": "Проверка наличия нового снимка...", "progress.downloading": "Загрузка тайлов: {current}/{total}", "progress.assembling": "Сборка изображения...", "progress.applying": "Применение обоев...", "progress.pruning": "Очистка кэша...",
        "settings.title": "Настройки", "settings.resolution": "Разрешение", "settings.check_interval": "Интервал проверки (часы)", "settings.history_size": "Размер истории", "settings.theme": "Тема", "settings.language": "Язык", "settings.autostart": "Запускать при входе в Windows", "settings.wallpaper_mode": "Режим обоев", "settings.retry_count": "Число повторных попыток", "settings.retry_delay": "Задержка между попытками (сек)", "settings.space_mix": "Автоматический «Космический микс»", "settings.space_mix_interval": "Интервал «Космического микса» (часы)", "settings.nasa_api_key": "API-ключ NASA (необязательно, пусто = DEMO_KEY)", "settings.invalid_value": "Некорректное значение: {error}", "settings.save_failed": "Не удалось сохранить настройки. См. логи.",
        "monitors.title": "Разные обои для мониторов", "monitors.unsupported": "Разные обои для мониторов доступны только в Windows 10/11.", "monitors.no_wallpapers": "Сначала скачайте хотя бы одни обои.", "monitors.apply": "Применить к мониторам", "monitors.applied": "Обои назначены мониторам.", "monitors.failed": "Не удалось установить обои на мониторы.",
        "about.title": "О программе EarthLive", "about.description": "EarthLive добавляет на рабочий стол свежие снимки Земли, NASA, James Webb и Hubble.", "about.version": "Версия", "about.author": "Автор", "about.license": "Лицензия", "about.source": "Исходный код", "about.open_github": "Открыть на GitHub ↗", "about.close": "Закрыть",
        "tray.open": "Открыть EarthLive", "tray.update_now": "Обновить сейчас", "tray.quit": "Выход",
    },
}

_OUTCOME_KEY_PREFIX = "outcome."


class Translator:
    """Resolves string keys to localized text for the active language."""

    def __init__(self, language: Language) -> None:
        self._language = language

    @property
    def language(self) -> Language:
        return self._language

    def set_language(self, language: Language) -> None:
        self._language = language

    def get(self, key: str, **format_args: str) -> str:
        strings = _STRINGS.get(self._language, {})
        text = strings.get(key)
        if text is None:
            text = _STRINGS[Language.EN].get(key, key)
        if format_args:
            try:
                return text.format(**format_args)
            except (KeyError, IndexError):
                return text
        return text

    def outcome_label(self, outcome_value: str) -> str:
        return self.get(f"{_OUTCOME_KEY_PREFIX}{outcome_value}")
