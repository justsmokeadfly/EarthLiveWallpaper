"""Lightweight UI localization for EarthLive.

Avoids a full gettext/babel dependency for just two languages: a single
flat dictionary per language, looked up by string key. Every UI-facing
string used anywhere in ``ui/`` goes through :func:`Translator.get`
rather than being hard-coded, so adding a third language later is purely
a matter of adding another dict here.
"""

from __future__ import annotations

from domain.enums import Language

_STRINGS: dict[Language, dict[str, str]] = {
    Language.EN: {
        "app_title": "EarthLive",
        "app_header": "🌍  EarthLive",
        "status_checking": "Checking status...",
        "status_waiting": "Waiting for first check",
        "outcome.success": "Success",
        "outcome.already_up_to_date": "Already up to date",
        "outcome.duplicate_content": "Duplicate content",
        "outcome.network_unavailable": "No internet connection",
        "outcome.provider_unavailable": "Satellite server unavailable",
        "outcome.download_failed": "Download failed",
        "outcome.assembly_failed": "Image assembly failed",
        "outcome.wallpaper_apply_failed": "Failed to apply wallpaper",
        "outcome.unexpected_error": "Unexpected error",
        "outcome.paused": "Updates paused",
        "label.last_image_time": "Last image time",
        "label.last_update": "Last update",
        "label.next_update": "Next update",
        "label.cache_size": "Cache size",
        "label.resolution": "Resolution",
        "label.total_updates": "Total updates applied",
        "label.never": "Never",
        "button.update_now": "Update now",
        "button.updating": "Updating...",
        "button.open_folder": "Open wallpapers folder",
        "button.settings": "Settings",
        "button.about": "About",
        "button.save": "Save",
        "button.cancel": "Cancel",
        "button.pause": "Pause updates",
        "button.resume": "Resume updates",
        "button.history": "Wallpaper history",
        "history.title": "Wallpaper history",
        "history.empty": "No wallpapers in history yet.",
        "history.apply": "Apply",
        "history.applied": "Applied!",
        "history.create_timelapse": "Create timelapse (GIF)",
        "history.creating_timelapse": "Creating timelapse...",
        "history.timelapse_success": "Timelapse saved to {path}",
        "history.timelapse_failed": "Failed to create timelapse. Need at least 2 images in history.",
        "history.close": "Close",
        "notification.title": "EarthLive",
        "progress.checking": "Checking for a new image...",
        "progress.downloading": "Downloading tiles: {current}/{total}",
        "progress.assembling": "Assembling image...",
        "progress.applying": "Applying wallpaper...",
        "progress.pruning": "Cleaning up cache...",
        "settings.title": "Settings",
        "settings.resolution": "Resolution",
        "settings.check_interval": "Check interval (hours)",
        "settings.history_size": "History size",
        "settings.theme": "Theme",
        "settings.language": "Language",
        "settings.autostart": "Launch at Windows login",
        "settings.wallpaper_mode": "Wallpaper mode",
        "settings.retry_count": "Retry count",
        "settings.retry_delay": "Retry delay (seconds)",
        "settings.invalid_value": "Invalid value: {error}",
        "settings.save_failed": "Failed to save settings. Check logs.",
        "about.title": "About EarthLive",
        "about.description": (
            "EarthLive automatically downloads the latest full-disk Earth "
            "image from the Himawari satellite and sets it as your desktop "
            "wallpaper."
        ),
        "about.author": "Author",
        "about.version": "Version",
        "about.license": "License",
        "about.source": "Source code",
        "about.close": "Close",
        "tray.open": "Open EarthLive",
        "tray.update_now": "Update now",
        "tray.quit": "Quit",
    },
    Language.RU: {
        "app_title": "EarthLive",
        "app_header": "🌍  EarthLive",
        "status_checking": "Проверка статуса...",
        "status_waiting": "Ожидание первой проверки",
        "outcome.success": "Успешно обновлено",
        "outcome.already_up_to_date": "Уже актуально",
        "outcome.duplicate_content": "Дублирующееся изображение",
        "outcome.network_unavailable": "Нет подключения к интернету",
        "outcome.provider_unavailable": "Сервер спутника недоступен",
        "outcome.download_failed": "Ошибка загрузки",
        "outcome.assembly_failed": "Ошибка сборки изображения",
        "outcome.wallpaper_apply_failed": "Не удалось установить обои",
        "outcome.unexpected_error": "Непредвиденная ошибка",
        "outcome.paused": "Обновления приостановлены",
        "label.last_image_time": "Время последнего снимка",
        "label.last_update": "Последнее обновление",
        "label.next_update": "Следующее обновление",
        "label.cache_size": "Размер кэша",
        "label.resolution": "Разрешение",
        "label.total_updates": "Всего обновлений",
        "label.never": "Никогда",
        "button.update_now": "Обновить сейчас",
        "button.updating": "Обновление...",
        "button.open_folder": "Открыть папку с обоями",
        "button.settings": "Настройки",
        "button.about": "О программе",
        "button.save": "Сохранить",
        "button.cancel": "Отмена",
        "button.pause": "Приостановить обновления",
        "button.resume": "Возобновить обновления",
        "button.history": "История обоев",
        "history.title": "История обоев",
        "history.empty": "В истории пока нет обоев.",
        "history.apply": "Применить",
        "history.applied": "Применено!",
        "history.create_timelapse": "Создать таймлапс (GIF)",
        "history.creating_timelapse": "Создание таймлапса...",
        "history.timelapse_success": "Таймлапс сохранён: {path}",
        "history.timelapse_failed": "Не удалось создать таймлапс. Нужно минимум 2 изображения в истории.",
        "history.close": "Закрыть",
        "notification.title": "EarthLive",
        "progress.checking": "Проверка наличия нового снимка...",
        "progress.downloading": "Загрузка тайлов: {current}/{total}",
        "progress.assembling": "Сборка изображения...",
        "progress.applying": "Применение обоев...",
        "progress.pruning": "Очистка кэша...",
        "settings.title": "Настройки",
        "settings.resolution": "Разрешение",
        "settings.check_interval": "Интервал проверки (часы)",
        "settings.history_size": "Размер истории",
        "settings.theme": "Тема",
        "settings.language": "Язык",
        "settings.autostart": "Запускать при входе в Windows",
        "settings.wallpaper_mode": "Режим обоев",
        "settings.retry_count": "Число повторных попыток",
        "settings.retry_delay": "Задержка между попытками (сек)",
        "settings.invalid_value": "Некорректное значение: {error}",
        "settings.save_failed": "Не удалось сохранить настройки. См. логи.",
        "about.title": "О программе EarthLive",
        "about.description": (
            "EarthLive автоматически скачивает последний снимок Земли со "
            "спутника Himawari и устанавливает его в качестве обоев рабочего "
            "стола."
        ),
        "about.author": "Автор",
        "about.version": "Версия",
        "about.license": "Лицензия",
        "about.source": "Исходный код",
        "about.close": "Закрыть",
        "tray.open": "Открыть EarthLive",
        "tray.update_now": "Обновить сейчас",
        "tray.quit": "Выход",
    },
}

_OUTCOME_KEY_PREFIX = "outcome."


class Translator:
    """Resolves string keys to localized text for the active language."""

    def __init__(self, language: Language) -> None:
        """Initialize the translator.

        Args:
            language: The language to translate into.
        """
        self._language = language

    @property
    def language(self) -> Language:
        """The language this translator is currently configured for."""
        return self._language

    def set_language(self, language: Language) -> None:
        """Change the active language.

        Args:
            language: The new language to translate into.
        """
        self._language = language

    def get(self, key: str, **format_args: str) -> str:
        """Look up a translated string by key.

        Args:
            key: The string key (e.g. ``"button.update_now"``).
            **format_args: Optional ``str.format`` substitutions applied
                to the resolved string.

        Returns:
            The translated (and formatted) string. Falls back to English
            if the key is missing from the active language, and to the
            raw key itself if missing from both.
        """
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
        """Translate an UpdateOutcome value into a display label.

        Args:
            outcome_value: The ``.value`` of an UpdateOutcome enum member.

        Returns:
            The localized label for that outcome.
        """
        return self.get(f"{_OUTCOME_KEY_PREFIX}{outcome_value}")
