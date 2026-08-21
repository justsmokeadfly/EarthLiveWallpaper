"""Wallpaper history gallery dialog.

Shows a thumbnail for every wallpaper still present in history, each with
an "Apply" button to make it the current wallpaper again, plus a
"Create timelapse (GIF)" action that stitches the whole history into an
animated GIF.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, UnidentifiedImageError

from application.app_controller import AppController
from logger import get_logger
from ui import theme
from ui.i18n import Translator

_logger = get_logger(__name__)
_THUMBNAIL_SIZE = (160, 90)


class HistoryDialog(ctk.CTkToplevel):
    """Modal dialog showing the wallpaper history as a thumbnail gallery."""

    def __init__(self, master: ctk.CTk, controller: AppController, translator: Translator) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._thumbnail_refs: list[ctk.CTkImage] = []
        self.title(self._tr.get("history.title"))
        self.geometry("560x520")
        self.resizable(True, True)
        self.minsize(520, 420)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self.transient(master)
        self.grab_set()
        self._build_widgets()

    def _build_widgets(self) -> None:
        self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_frame.pack(fill="both", expand=True, padx=theme.PADDING, pady=theme.PADDING)

        self._status_label = ctk.CTkLabel(
            self, text="", font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
            text_color=theme.COLOR_TEXT_SECONDARY, wraplength=500,
        )
        self._status_label.pack(pady=(0, 4), padx=theme.PADDING)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=theme.PADDING, pady=(0, theme.PADDING))

        self._timelapse_button = ctk.CTkButton(
            button_frame, text=self._tr.get("history.create_timelapse"),
            command=self._on_create_timelapse_clicked,
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
            corner_radius=theme.CORNER_RADIUS,
        )
        self._timelapse_button.pack(fill="x", pady=4)

        close_button = ctk.CTkButton(
            button_frame, text=self._tr.get("history.close"), command=self.destroy,
            fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        close_button.pack(fill="x", pady=4)
        self._populate_gallery()

    def _populate_gallery(self) -> None:
        history = self._controller.get_history()
        if not history:
            ctk.CTkLabel(
                self._scroll_frame, text=self._tr.get("history.empty"),
                text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(pady=theme.PADDING)
            self._timelapse_button.configure(state="disabled")
            return
        for file_path in history:
            self._add_history_row(file_path)

    def _add_history_row(self, file_path: Path) -> None:
        row = ctk.CTkFrame(
            self._scroll_frame, fg_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        row.pack(fill="x", pady=6)
        thumbnail = self._load_thumbnail(file_path)
        if thumbnail is not None:
            self._thumbnail_refs.append(thumbnail)
            ctk.CTkLabel(row, image=thumbnail, text="").pack(
                side="left", padx=theme.PADDING, pady=theme.PADDING
            )
        ctk.CTkLabel(
            row, text=file_path.stem, font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
            text_color=theme.COLOR_TEXT_SECONDARY, anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(0, theme.PADDING))
        apply_button = ctk.CTkButton(
            row, text=self._tr.get("history.apply"), width=90,
            command=lambda p=file_path, btn_row=row: self._on_apply_clicked(p, btn_row),
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
        )
        apply_button.pack(side="right", padx=theme.PADDING)
        row._apply_button = apply_button

    def _load_thumbnail(self, file_path: Path) -> ctk.CTkImage | None:
        try:
            with Image.open(file_path) as opened:
                opened.load()
                img = opened.convert("RGB")
                img.thumbnail(_THUMBNAIL_SIZE, Image.LANCZOS)
                return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        except (UnidentifiedImageError, OSError) as exc:
            _logger.warning("Failed to load thumbnail for %s: %s", file_path, exc)
            return None

    def _on_apply_clicked(self, file_path: Path, row: ctk.CTkFrame) -> None:
        button = row._apply_button
        button.configure(state="disabled")
        self._status_label.configure(text="", text_color=theme.COLOR_TEXT_SECONDARY)
        self.update_idletasks()
        success = self._controller.reapply_from_history(file_path)
        button.configure(state="normal")
        if success:
            button.configure(text=self._tr.get("history.applied"))
            self._status_label.configure(
                text=self._tr.get("history.applied"), text_color=theme.COLOR_SUCCESS
            )
            self.after(2000, lambda: button.configure(text=self._tr.get("history.apply")))
        else:
            _logger.warning("Failed to reapply wallpaper: %s", file_path)
            self._status_label.configure(
                text=f"Could not apply: {file_path.name}", text_color=theme.COLOR_ERROR
            )

    def _on_create_timelapse_clicked(self) -> None:
        output_path_str = filedialog.asksaveasfilename(
            defaultextension=".gif", filetypes=[("GIF", "*.gif")],
            initialfile="earthlive_timelapse.gif",
        )
        if not output_path_str:
            return
        output_path = Path(output_path_str)
        self._timelapse_button.configure(
            state="disabled", text=self._tr.get("history.creating_timelapse")
        )
        self._status_label.configure(text="")
        self.update_idletasks()
        success = self._controller.create_timelapse(output_path)
        self._timelapse_button.configure(
            state="normal", text=self._tr.get("history.create_timelapse")
        )
        if success:
            self._status_label.configure(
                text=self._tr.get("history.timelapse_success", path=str(output_path)),
                text_color=theme.COLOR_SUCCESS,
            )
        else:
            self._status_label.configure(
                text=self._tr.get("history.timelapse_failed"), text_color=theme.COLOR_ERROR
            )
