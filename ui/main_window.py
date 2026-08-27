"""Main application window for EarthLive."""
from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

import customtkinter as ctk

from application.app_controller import AppController, StatusSnapshot
from application.progress import ProgressSnapshot, ProgressStage
from domain.enums import UpdateOutcome
from logger import get_logger
from ui import theme
from ui.about_dialog import AboutDialog
from ui.i18n import Translator
from ui.nasa_photos_dialog import NASAPhotosDialog
from ui.settings_dialog import SettingsDialog
from ui.wallpapers_dialog import WallpapersDialog

_logger = get_logger(__name__)
_STATUS_REFRESH_MS = 1000
_OUTCOME_COLORS = {
    UpdateOutcome.SUCCESS: theme.COLOR_SUCCESS,
    UpdateOutcome.ALREADY_UP_TO_DATE: theme.COLOR_TEXT_SECONDARY,
    UpdateOutcome.DUPLICATE_CONTENT: theme.COLOR_TEXT_SECONDARY,
    UpdateOutcome.NETWORK_UNAVAILABLE: theme.COLOR_WARNING,
    UpdateOutcome.PROVIDER_UNAVAILABLE: theme.COLOR_WARNING,
    UpdateOutcome.DOWNLOAD_FAILED: theme.COLOR_ERROR,
    UpdateOutcome.ASSEMBLY_FAILED: theme.COLOR_ERROR,
    UpdateOutcome.WALLPAPER_APPLY_FAILED: theme.COLOR_ERROR,
    UpdateOutcome.UNEXPECTED_ERROR: theme.COLOR_ERROR,
    UpdateOutcome.PAUSED: theme.COLOR_TEXT_SECONDARY,
}
_INFO_ROW_KEYS = (
    "last_image_time",
    "last_update",
    "next_update",
    "cache_size",
    "resolution",
    "total_updates",
)


def _format_datetime(value: datetime | None, never_label: str) -> str:
    if value is None:
        return never_label
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


class MainWindow(ctk.CTk):
    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self._controller = controller
        self._tr = Translator(controller.get_config().language)
        ctk.set_appearance_mode(controller.get_config().theme.value)
        ctk.set_default_color_theme("blue")
        self.title(self._tr.get("app_title"))
        self.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}")
        self.minsize(theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self._build_widgets()
        self._refresh_status()
        self.after(_STATUS_REFRESH_MS, self._schedule_refresh)

    @property
    def translator(self) -> Translator:
        return self._tr

    def _build_widgets(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PADDING, pady=(theme.PADDING, 4))
        ctk.CTkLabel(
            header,
            text="🌍",
            font=(theme.FONT_FAMILY, 30),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(side="left", padx=(0, 10))
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_frame,
            text=self._tr.get("app_header"),
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_TITLE, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            title_frame,
            text=self._tr.get("app_subtitle"),
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
            text_color=theme.COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x")
        self._status_dot = ctk.CTkLabel(
            self,
            text=f"●  {self._tr.get('status_checking')}",
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"),
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self._status_dot.pack(pady=(2, theme.PADDING))
        info = ctk.CTkFrame(
            self,
            fg_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        info.pack(fill="x", padx=theme.PADDING, pady=(0, 10))
        self._info_labels = {}
        self._info_titles = {}
        for i, key in enumerate(_INFO_ROW_KEYS):
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.grid(row=i // 2, column=i % 2, sticky="ew", padx=10, pady=7)
            info.grid_columnconfigure(i % 2, weight=1)
            title = ctk.CTkLabel(
                row,
                text=self._tr.get(f"label.{key}"),
                font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
                text_color=theme.COLOR_TEXT_SECONDARY,
                anchor="w",
            )
            title.pack(fill="x")
            self._info_titles[key] = title
            value = ctk.CTkLabel(
                row,
                text="—",
                font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"),
                text_color=theme.COLOR_TEXT_PRIMARY,
                anchor="w",
            )
            value.pack(fill="x", pady=(1, 0))
            self._info_labels[key] = value
        self._message_label = ctk.CTkLabel(
            self,
            text="",
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
            text_color=theme.COLOR_TEXT_SECONDARY,
            wraplength=theme.WINDOW_WIDTH - 2 * theme.PADDING,
        )
        self._message_label.pack(padx=theme.PADDING, pady=(0, 5))
        self._progress_bar = ctk.CTkProgressBar(
            self,
            progress_color=theme.COLOR_ACCENT,
            corner_radius=theme.CORNER_RADIUS,
        )
        self._progress_bar.set(0.0)
        self._progress_bar.pack(fill="x", padx=theme.PADDING, pady=(0, 3))
        self._progress_label = ctk.CTkLabel(
            self,
            text="",
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self._progress_label.pack(pady=(0, 8))
        self._update_button = ctk.CTkButton(
            self,
            text=self._tr.get("button.update_now"),
            command=self._on_update_now_clicked,
            height=42,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"),
            fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER,
            corner_radius=theme.CORNER_RADIUS,
        )
        self._update_button.pack(fill="x", padx=theme.PADDING, pady=(0, 8))
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=theme.PADDING, pady=(0, 8))
        for column in range(5):
            actions.grid_columnconfigure(column, weight=1)
        self._wallpapers_button = self._make_action_button(
            actions, "button.wallpapers", self._on_wallpapers_clicked, 0
        )
        self._nasa_button = self._make_literal_action_button(
            actions, "NASA Fotos", self._on_nasa_clicked, 1
        )
        self._webb_button = self._make_literal_action_button(
            actions, "James Webb Fotos", self._on_webb_clicked, 2
        )
        self._settings_button = self._make_action_button(
            actions, "button.settings", self._on_settings_clicked, 3
        )
        self._about_button = self._make_action_button(
            actions, "button.about", self._on_about_clicked, 4
        )
        secondary = ctk.CTkFrame(self, fg_color="transparent")
        secondary.pack(fill="x", padx=theme.PADDING, pady=(0, theme.PADDING))
        secondary.grid_columnconfigure(0, weight=1)
        secondary.grid_columnconfigure(1, weight=1)
        self._open_folder_button = self._make_secondary_button(
            secondary, "button.open_folder", self._on_open_folder_clicked, 0
        )
        self._pause_button = self._make_secondary_button(
            secondary, "button.pause", self._on_pause_toggle_clicked, 1
        )
        self._pause_button.configure(text=self._pause_button_text())

    def _make_action_button(
        self,
        parent: Any,
        key: str,
        command: Callable[[], None],
        column: int,
    ) -> Any:
        button = ctk.CTkButton(
            parent,
            text=self._tr.get(key),
            command=command,
            fg_color=theme.COLOR_SURFACE_ALT,
            hover_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        button.grid(row=0, column=column, sticky="ew", padx=3)
        return button

    def _make_literal_action_button(
        self,
        parent: Any,
        text: str,
        command: Callable[[], None],
        column: int,
    ) -> Any:
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=theme.COLOR_SURFACE_ALT,
            hover_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        button.grid(row=0, column=column, sticky="ew", padx=3)
        return button

    def _make_secondary_button(
        self,
        parent: Any,
        key: str,
        command: Callable[[], None],
        column: int,
    ) -> Any:
        button = ctk.CTkButton(
            parent,
            text=self._tr.get(key),
            command=command,
            fg_color="transparent",
            border_width=1,
            border_color=theme.COLOR_SURFACE_ALT,
            hover_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        button.grid(row=0, column=column, sticky="ew", padx=3)
        return button

    def _schedule_refresh(self) -> None:
        self._refresh_status()
        self.after(_STATUS_REFRESH_MS, self._schedule_refresh)

    def _refresh_status(self) -> None:
        try:
            self._apply_snapshot(self._controller.get_status_snapshot())
            self._apply_progress(self._controller.get_progress())
        except Exception:
            _logger.exception("Failed to refresh main-window status.")

    def _apply_progress(self, progress: ProgressSnapshot) -> None:
        if progress.stage == ProgressStage.IDLE:
            self._progress_bar.configure(mode="determinate")
            self._progress_bar.stop()
            self._progress_bar.set(0.0)
            self._progress_label.configure(text="")
            if self._update_button.cget("state") == "disabled":
                self._update_button.configure(
                    state="normal", text=self._tr.get("button.update_now")
                )
            return
        self._update_button.configure(
            state="disabled", text=self._tr.get("button.updating")
        )
        key = f"progress.{progress.stage.value}"
        if progress.stage == ProgressStage.DOWNLOADING:
            self._progress_label.configure(
                text=self._tr.get(
                    key, current=str(progress.current), total=str(progress.total)
                )
            )
        else:
            self._progress_label.configure(text=self._tr.get(key))
        if progress.is_determinate:
            self._progress_bar.configure(mode="determinate")
            self._progress_bar.stop()
            self._progress_bar.set(progress.fraction)
        elif self._progress_bar.cget("mode") != "indeterminate":
            self._progress_bar.configure(mode="indeterminate")
            self._progress_bar.start()

    def _apply_snapshot(self, snapshot: StatusSnapshot) -> None:
        outcome = snapshot.last_outcome
        color = (
            _OUTCOME_COLORS.get(outcome, theme.COLOR_TEXT_SECONDARY)
            if outcome
            else theme.COLOR_TEXT_SECONDARY
        )
        label = (
            self._tr.outcome_label(outcome.value)
            if outcome
            else self._tr.get("status_waiting")
        )
        self._status_dot.configure(text=f"●  {label}", text_color=color)
        self._message_label.configure(text=snapshot.last_message)
        never = self._tr.get("label.never")
        values = {
            "last_image_time": _format_datetime(snapshot.last_image_timestamp, never),
            "last_update": _format_datetime(snapshot.last_update_at, never),
            "next_update": _format_datetime(snapshot.next_update_at, never),
            "cache_size": _format_size(snapshot.cache_size_bytes),
            "resolution": snapshot.resolution,
            "total_updates": str(snapshot.total_updates_applied),
        }
        for key, value in values.items():
            self._info_labels[key].configure(text=value)

    def _on_update_now_clicked(self) -> None:
        self._update_button.configure(
            state="disabled", text=self._tr.get("button.updating")
        )
        self._controller.trigger_update_now()

    def _on_open_folder_clicked(self) -> None:
        folder = self._controller.wallpapers_dir
        folder.mkdir(parents=True, exist_ok=True)
        try:
            # Windows Explorer hand-off; the path is a trusted local application directory.
            os.startfile(str(folder))  # noqa: S606
        except OSError:
            _logger.exception("Failed to open wallpapers folder: %s", folder)

    def _on_settings_clicked(self) -> None:
        SettingsDialog(
            self,
            self._controller,
            self._tr,
            on_language_changed=self._refresh_ui_language,
        ).grab_set()

    def _on_about_clicked(self) -> None:
        AboutDialog(self, self._tr).grab_set()

    def _on_wallpapers_clicked(self) -> None:
        WallpapersDialog(self, self._controller, self._tr).grab_set()

    def _on_nasa_clicked(self) -> None:
        NASAPhotosDialog(self, self._controller, self._tr, webb=False)

    def _on_webb_clicked(self) -> None:
        NASAPhotosDialog(self, self._controller, self._tr, webb=True)

    def _pause_button_text(self) -> str:
        return self._tr.get(
            "button.resume" if self._controller.is_paused() else "button.pause"
        )

    def _on_pause_toggle_clicked(self) -> None:
        self._controller.set_paused(not self._controller.is_paused())
        self._pause_button.configure(text=self._pause_button_text())

    def _refresh_ui_language(self) -> None:
        self._tr.set_language(self._controller.get_config().language)
        self.title(self._tr.get("app_title"))
        self._update_button.configure(text=self._tr.get("button.update_now"))
        self._open_folder_button.configure(text=self._tr.get("button.open_folder"))
        self._wallpapers_button.configure(text=self._tr.get("button.wallpapers"))
        self._pause_button.configure(text=self._pause_button_text())
        self._settings_button.configure(text=self._tr.get("button.settings"))
        self._about_button.configure(text=self._tr.get("button.about"))
        self._refresh_status()
