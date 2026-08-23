"""Modal settings dialog exposing every user-editable configuration
option: resolution, check interval, history size, theme, language,
autostart, wallpaper mode, retry count, and retry delay.
"""

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

_LANGUAGE_DISPLAY_NAMES: dict[Language, str] = {
    Language.EN: "English",
    Language.RU: "Русский",
}
_LANGUAGE_NAME_TO_VALUE = {name: lang.value for lang, name in _LANGUAGE_DISPLAY_NAMES.items()}


class SettingsDialog(ctk.CTkToplevel):
    """A modal dialog for editing :class:`AppConfig`."""

    def __init__(
        self,
        master: ctk.CTk,
        controller: AppController,
        translator: Translator,
        on_language_changed: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the dialog with the controller's current config.

        Args:
            master: The parent window.
            controller: Application-layer facade used to load/save config.
            translator: Active Translator, for localized labels.
            on_language_changed: Optional callback invoked after a
                successful save if the language selection changed, so the
                main window can refresh its own labels without a restart.
        """
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._on_language_changed = on_language_changed
        self._config = controller.get_config()

        self.title(self._tr.get("settings.title"))
        self.geometry("420x620")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BACKGROUND)

        self._build_widgets()

    def _build_widgets(self) -> None:
        """Construct and lay out every settings control."""
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=theme.PADDING, pady=theme.PADDING)

        self._resolution_var = ctk.StringVar(value=self._config.grid_size.value)
        self._add_option_menu(
            container,
            label=self._tr.get("settings.resolution"),
            variable=self._resolution_var,
            values=[g.value for g in GridSize],
        )

        self._interval_var = ctk.StringVar(value=str(self._config.check_interval_hours))
        self._add_entry(
            container, label=self._tr.get("settings.check_interval"), variable=self._interval_var
        )

        self._history_var = ctk.StringVar(value=str(self._config.history_size))
        self._add_entry(
            container, label=self._tr.get("settings.history_size"), variable=self._history_var
        )

        self._theme_display = {t: self._tr.get(f"theme.{t.value}") for t in Theme}
        self._theme_name_to_value = {
            name: theme_member.value for theme_member, name in self._theme_display.items()
        }
        self._theme_var = ctk.StringVar(value=self._theme_display[self._config.theme])
        self._add_option_menu(
            container,
            label=self._tr.get("settings.theme"),
            variable=self._theme_var,
            values=list(self._theme_display.values()),
        )

        self._language_var = ctk.StringVar(
            value=_LANGUAGE_DISPLAY_NAMES[self._config.language]
        )
        self._add_option_menu(
            container,
            label=self._tr.get("settings.language"),
            variable=self._language_var,
            values=list(_LANGUAGE_DISPLAY_NAMES.values()),
        )

        self._autostart_var = ctk.BooleanVar(value=self._controller.is_autostart_enabled())
        self._add_switch(
            container, label=self._tr.get("settings.autostart"), variable=self._autostart_var
        )

        self._wallpaper_mode_display = {
            m: self._tr.get(f"wallpaper_mode.{m.value}") for m in WallpaperMode
        }
        self._wallpaper_mode_name_to_value = {
            name: mode.value for mode, name in self._wallpaper_mode_display.items()
        }
        self._wallpaper_mode_var = ctk.StringVar(
            value=self._wallpaper_mode_display[self._config.wallpaper_mode]
        )
        self._add_option_menu(
            container,
            label=self._tr.get("settings.wallpaper_mode"),
            variable=self._wallpaper_mode_var,
            values=list(self._wallpaper_mode_display.values()),
        )

        self._retry_count_var = ctk.StringVar(value=str(self._config.retry_count))
        self._add_entry(
            container, label=self._tr.get("settings.retry_count"), variable=self._retry_count_var
        )

        self._retry_delay_var = ctk.StringVar(value=str(self._config.retry_delay_seconds))
        self._add_entry(
            container, label=self._tr.get("settings.retry_delay"), variable=self._retry_delay_var
        )

        self._error_label = ctk.CTkLabel(
            self,
            text="",
            text_color=theme.COLOR_ERROR,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
        )
        self._error_label.pack(padx=theme.PADDING)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=theme.PADDING, pady=theme.PADDING)

        save_button = ctk.CTkButton(
            button_frame,
            text=self._tr.get("button.save"),
            command=self._on_save_clicked,
            fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER,
        )
        save_button.pack(side="right", padx=(8, 0))

        cancel_button = ctk.CTkButton(
            button_frame,
            text=self._tr.get("button.cancel"),
            command=self.destroy,
            fg_color=theme.COLOR_SURFACE_ALT,
            hover_color=theme.COLOR_SURFACE,
        )
        cancel_button.pack(side="right")

    def _add_option_menu(
        self, parent: ctk.CTkBaseClass, label: str, variable: ctk.StringVar, values: list[str]
    ) -> None:
        """Add a labeled dropdown option menu row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkLabel(
            row, text=label, text_color=theme.COLOR_TEXT_SECONDARY, anchor="w"
        ).pack(fill="x")
        ctk.CTkOptionMenu(row, variable=variable, values=values).pack(fill="x", pady=(4, 0))

    def _add_entry(self, parent: ctk.CTkBaseClass, label: str, variable: ctk.StringVar) -> None:
        """Add a labeled text entry row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkLabel(
            row, text=label, text_color=theme.COLOR_TEXT_SECONDARY, anchor="w"
        ).pack(fill="x")
        ctk.CTkEntry(row, textvariable=variable).pack(fill="x", pady=(4, 0))

    def _add_switch(self, parent: ctk.CTkBaseClass, label: str, variable: ctk.BooleanVar) -> None:
        """Add a labeled on/off switch row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkSwitch(row, text=label, variable=variable).pack(fill="x")

    def _on_save_clicked(self) -> None:
        """Validate all fields, build a new AppConfig, and persist it via
        the controller. Displays an inline error message instead of
        closing if validation fails.
        """
        try:
            grid_size = GridSize.from_string(self._resolution_var.get())
            theme_value = Theme.from_string(
                self._theme_name_to_value[self._theme_var.get()]
            )
            wallpaper_mode = WallpaperMode.from_string(
                self._wallpaper_mode_name_to_value[self._wallpaper_mode_var.get()]
            )
            language_value = Language.from_string(
                _LANGUAGE_NAME_TO_VALUE[self._language_var.get()]
            )
            check_interval_hours = float(self._interval_var.get())
            history_size = int(self._history_var.get())
            retry_count = int(self._retry_count_var.get())
            retry_delay_seconds = float(self._retry_delay_var.get())

            if check_interval_hours <= 0:
                raise ValueError("Check interval must be greater than zero.")
            if history_size < 1:
                raise ValueError("History size must be at least 1.")
            if retry_count < 0:
                raise ValueError("Retry count cannot be negative.")
            if retry_delay_seconds < 0:
                raise ValueError("Retry delay cannot be negative.")

        except ValueError as exc:
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
