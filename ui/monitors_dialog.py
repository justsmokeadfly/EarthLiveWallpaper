"""UI for assigning different saved wallpapers to individual monitors."""

from __future__ import annotations

import customtkinter as ctk

from application.app_controller import AppController
from ui import theme
from ui.i18n import Translator


class MonitorsDialog(ctk.CTkToplevel):
    """Assign one local wallpaper history item to each monitor."""

    def __init__(self, master: ctk.CTk, controller: AppController, translator: Translator) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self.title(self._tr.get("monitors.title"))
        self.geometry("620x520")
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self.transient(master)
        self.grab_set()
        self._history = controller.get_history()
        self._choices: list[ctk.StringVar] = []
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="🖥️ " + self._tr.get("monitors.title"),
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_TITLE, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=theme.PADDING, pady=theme.PADDING)
        count = self._controller.get_monitor_count()
        if count <= 0:
            ctk.CTkLabel(self, text=self._tr.get("monitors.unsupported"), text_color=theme.COLOR_ERROR).pack(padx=theme.PADDING, pady=20)
        elif not self._history:
            ctk.CTkLabel(self, text=self._tr.get("monitors.no_wallpapers"), text_color=theme.COLOR_TEXT_SECONDARY).pack(padx=theme.PADDING, pady=20)
        else:
            frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=theme.PADDING)
            values = [str(path) for path in self._history]
            for index in range(count):
                ctk.CTkLabel(frame, text=f"Monitor {index + 1}", text_color=theme.COLOR_TEXT_PRIMARY).pack(fill="x", pady=(8, 2))
                var = ctk.StringVar(value=values[min(index, len(values) - 1)])
                self._choices.append(var)
                ctk.CTkOptionMenu(frame, variable=var, values=values).pack(fill="x", pady=(0, 6))
        self._status = ctk.CTkLabel(self, text="", text_color=theme.COLOR_TEXT_SECONDARY)
        self._status.pack(padx=theme.PADDING, pady=8)
        ctk.CTkButton(
            self,
            text=self._tr.get("monitors.apply"),
            command=self._apply,
            fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER,
        ).pack(fill="x", padx=theme.PADDING, pady=(0, theme.PADDING))

    def _apply(self) -> None:
        if not self._choices:
            return
        mapping = {index: __import__('pathlib').Path(var.get()) for index, var in enumerate(self._choices)}
        if self._controller.apply_wallpapers_per_monitor(mapping):
            self._status.configure(text=self._tr.get("monitors.applied"), text_color=theme.COLOR_SUCCESS)
        else:
            self._status.configure(text=self._tr.get("monitors.failed"), text_color=theme.COLOR_ERROR)
