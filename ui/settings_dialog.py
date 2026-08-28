"""Modal settings dialog exposing user-editable EarthLive configuration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import customtkinter as ctk

from application.app_controller import AppController
from domain.enums import GridSize, Language, Theme, WallpaperMode
from logger import get_logger
from ui import theme
from ui.i18n import Translator

_logger = get_logger(__name__)
_LANGUAGE_DISPLAY_NAMES: dict[Language, str] = {Language.EN: "English", Language.RU: "Русский"}
_LANGUAGE_NAME_TO_VALUE = {name: lang.value for lang, name in _LANGUAGE_DISPLAY_NAMES.items()}


class SettingsDialog(ctk.CTkToplevel):
    """A modal dialog for editing :class:`AppConfig`."""

    def __init__(self, master: ctk.CTk, controller: AppController, translator: Translator, on_language_changed: Callable[[], None] | None = None) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._on_language_changed = on_language_changed
        self._config = controller.get_config()
        self.title(self._tr.get("settings.title"))
        self.geometry("430x720")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self._build_widgets()

    def _build_widgets(self) -> None:
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=theme.PADDING, pady=theme.PADDING)

        self._resolution_var = ctk.StringVar(value=self._config.grid_size.value)
        self._add_option_menu(container, self._tr.get("settings.resolution"), self._resolution_var, [g.value for g in GridSize])
        self._interval_var = ctk.StringVar(value=str(self._config.check_interval_hours))
        self._add_entry(container, self._tr.get("settings.check_interval"), self._interval_var)
        self._history_var = ctk.StringVar(value=str(self._config.history_size))
        self._add_entry(container, self._tr.get("settings.history_size"), self._history_var)
        self._theme_display = {t: self._tr.get(f"theme.{t.value}") for t in Theme}
        self._theme_name_to_value = {name: member.value for member, name in self._theme_display.items()}
        self._theme_var = ctk.StringVar(value=self._theme_display[self._config.theme])
        self._add_option_menu(container, self._tr.get("settings.theme"), self._theme_var, list(self._theme_display.values()))
        self._language_var = ctk.StringVar(value=_LANGUAGE_DISPLAY_NAMES[self._config.language])
        self._add_option_menu(container, self._tr.get("settings.language"), self._language_var, list(_LANGUAGE_DISPLAY_NAMES.values()))
        self._autostart_var = ctk.BooleanVar(value=self._controller.is_autostart_enabled())
        self._add_switch(container, self._tr.get("settings.autostart"), self._autostart_var)
        self._wallpaper_mode_display = {m: self._tr.get(f"wallpaper_mode.{m.value}") for m in WallpaperMode}
        self._wallpaper_mode_name_to_value = {name: mode.value for mode, name in self._wallpaper_mode_display.items()}
        self._wallpaper_mode_var = ctk.StringVar(value=self._wallpaper_mode_display[self._config.wallpaper_mode])
        self._add_option_menu(container, self._tr.get("settings.wallpaper_mode"), self._wallpaper_mode_var, list(self._wallpaper_mode_display.values()))
        self._retry_count_var = ctk.StringVar(value=str(self._config.retry_count))
        self._add_entry(container, self._tr.get("settings.retry_count"), self._retry_count_var)
        self._retry_delay_var = ctk.StringVar(value=str(self._config.retry_delay_seconds))
        self._add_entry(container, self._tr.get("settings.retry_delay"), self._retry_delay_var)
        self._space_mix_var = ctk.BooleanVar(value=self._config.space_mix_enabled)
        self._add_switch(container, self._tr.get("settings.space_mix"), self._space_mix_var)
        self._space_mix_interval_var = ctk.StringVar(value=str(self._config.space_mix_interval_hours))
        self._add_entry(container, self._tr.get("settings.space_mix_interval"), self._space_mix_interval_var)

        self._error_label = ctk.CTkLabel(self, text="", text_color=theme.COLOR_ERROR, font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL))
        self._error_label.pack(padx=theme.PADDING)
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=theme.PADDING, pady=theme.PADDING)
        ctk.CTkButton(button_frame, text=self._tr.get("button.save"), command=self._on_save_clicked, fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER).pack(side="right", padx=(8, 0))
        ctk.CTkButton(button_frame, text=self._tr.get("button.cancel"), command=self.destroy, fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_SURFACE).pack(side="right")

    def _add_option_menu(self, parent: ctk.CTkBaseClass, label: str, variable: ctk.StringVar, values: list[str]) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkLabel(row, text=label, text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(fill="x")
        ctk.CTkOptionMenu(row, variable=variable, values=values).pack(fill="x", pady=(4, 0))

    def _add_entry(self, parent: ctk.CTkBaseClass, label: str, variable: ctk.StringVar) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkLabel(row, text=label, text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(fill="x")
        ctk.CTkEntry(row, textvariable=variable).pack(fill="x", pady=(4, 0))

    def _add_switch(self, parent: ctk.CTkBaseClass, label: str, variable: ctk.BooleanVar) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkSwitch(row, text=label, variable=variable).pack(fill="x")

    def _on_save_clicked(self) -> None:
        try:
            grid_size = GridSize.from_string(self._resolution_var.get())
            theme_value = Theme.from_string(self._theme_name_to_value[self._theme_var.get()])
            wallpaper_mode = WallpaperMode.from_string(self._wallpaper_mode_name_to_value[self._wallpaper_mode_var.get()])
            language_value = Language.from_string(_LANGUAGE_NAME_TO_VALUE[self._language_var.get()])
            check_interval_hours = float(self._interval_var.get())
            history_size = int(self._history_var.get())
            retry_count = int(self._retry_count_var.get())
            retry_delay_seconds = float(self._retry_delay_var.get())
            space_mix_interval_hours = float(self._space_mix_interval_var.get())
            if check_interval_hours <= 0 or space_mix_interval_hours <= 0:
                raise ValueError("Intervals must be greater than zero.")
            if history_size < 1:
                raise ValueError("History size must be at least 1.")
            if retry_count < 0 or retry_delay_seconds < 0:
                raise ValueError("Retry values cannot be negative.")
        except (KeyError, ValueError) as exc:
            self._error_label.configure(text=self._tr.get("settings.invalid_value", error=str(exc)))
            return

        language_changed = language_value != self._config.language
        new_config = replace(
            self._config,
            grid_size=grid_size,
            check_interval_hours=check_interval_hours,
            history_size=history_size,
            theme=theme_value,
            autostart=self._autostart_var.get(),
            wallpaper_mode=wallpaper_mode,
            retry_count=retry_count,
            retry_delay_seconds=retry_delay_seconds,
            language=language_value,
            space_mix_enabled=self._space_mix_var.get(),
            space_mix_interval_hours=space_mix_interval_hours,
        )
        try:
            self._controller.update_config(new_config)
        except Exception:
            _logger.exception("Failed to save settings.")
            self._error_label.configure(text=self._tr.get("settings.save_failed"))
            return
        if language_changed and self._on_language_changed is not None:
            self._on_language_changed()
        self.destroy()
