"""Wallpapers gallery dialog.

Shows a thumbnail for every wallpaper still present in history, each with
an "Apply" button to make it the current wallpaper again and a "Delete"
button to permanently remove it, plus a "Create timelapse (GIF)" action
that stitches the whole history into an animated GIF.
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


class WallpapersDialog(ctk.CTkToplevel):
    """Modal dialog showing saved wallpapers as a thumbnail gallery."""

    def __init__(self, master: ctk.CTk, controller: AppController, translator: Translator) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._thumbnail_refs: list[ctk.CTkImage] = []
        self.title(self._tr.get("wallpapers.title"))
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
            button_frame, text=self._tr.get("wallpapers.create_timelapse"),
            command=self._on_create_timelapse_clicked,
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
            corner_radius=theme.CORNER_RADIUS,
        )
        self._timelapse_button.pack(fill="x", pady=4)

        close_button = ctk.CTkButton(
            button_frame, text=self._tr.get("wallpapers.close"), command=self.destroy,
            fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        close_button.pack(fill="x", pady=4)
        self._populate_gallery()

    def _populate_gallery(self) -> None:
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._thumbnail_refs.clear()

        history = self._controller.get_history()
        if not history:
            ctk.CTkLabel(
                self._scroll_frame, text=self._tr.get("wallpapers.empty"),
                text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(pady=theme.PADDING)
            self._timelapse_button.configure(state="disabled")
            return
        self._timelapse_button.configure(state="normal")
        for file_path in history:
            self._add_wallpaper_row(file_path)

    def _add_wallpaper_row(self, file_path: Path) -> None:
        row = ctk.CTkFrame(
            self._scroll_frame, fg_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        row.pack(fill="x", pady=6)
        row._delete_armed = False  # type: ignore[attr-defined]

        thumbnail = self._load_thumbnail(file_path)
        if thumbnail is not None:
            self._thumbnail_refs.append(thumbnail)
            ctk.CTkLabel(row, image=thumbnail, text="").pack(
                side="left", padx=theme.PADDING, pady=theme.PADDING
            )
        ctk.CTkLabel(
            row, text=file_path.stem, font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
            text_color=theme.COLOR_TEXT_SECONDARY, anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        delete_button = ctk.CTkButton(
            row, text=self._tr.get("wallpapers.delete"), width=80,
            fg_color="transparent", border_width=1, border_color=theme.COLOR_ERROR,
            text_color=theme.COLOR_ERROR, hover_color=theme.COLOR_SURFACE_ALT,
        )
        delete_button.configure(command=lambda p=file_path, btn_row=row: self._on_delete_clicked(p, btn_row))
        delete_button.pack(side="right", padx=(4, theme.PADDING))

        apply_button = ctk.CTkButton(
            row, text=self._tr.get("wallpapers.apply"), width=90,
            command=lambda p=file_path, btn_row=row: self._on_apply_clicked(p, btn_row),
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
        )
        apply_button.pack(side="right", padx=(theme.PADDING, 0))
        row._apply_button = apply_button  # type: ignore[attr-defined]
        row._delete_button = delete_button  # type: ignore[attr-defined]

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
        button = row._apply_button  # type: ignore[attr-defined]
        button.configure(state="disabled")
        self._status_label.configure(text="", text_color=theme.COLOR_TEXT_SECONDARY)
        self.update_idletasks()
        success = self._controller.reapply_from_history(file_path)
        button.configure(state="normal")
        if success:
            button.configure(text=self._tr.get("wallpapers.applied"))
            self._status_label.configure(
                text=self._tr.get("wallpapers.applied"), text_color=theme.COLOR_SUCCESS
            )
            self.after(2000, lambda: button.configure(text=self._tr.get("wallpapers.apply")))
        else:
            _logger.warning("Failed to reapply wallpaper: %s", file_path)
            self._status_label.configure(
                text=self._tr.get("wallpapers.apply_failed", name=file_path.name),
                text_color=theme.COLOR_ERROR,
            )

    def _on_delete_clicked(self, file_path: Path, row: ctk.CTkFrame) -> None:
        """Two-step delete: the first click arms a confirmation state on
        that row's own button, and a second click on the same button
        actually deletes. This avoids an extra modal dialog while still
        preventing an accidental single click from destroying a
        wallpaper permanently.
        """
        button = row._delete_button  # type: ignore[attr-defined]

        if not row._delete_armed:  # type: ignore[attr-defined]
            row._delete_armed = True  # type: ignore[attr-defined]
            button.configure(
                text=self._tr.get("wallpapers.delete_confirm"),
                fg_color=theme.COLOR_ERROR, text_color=theme.COLOR_TEXT_PRIMARY,
            )
            return

        button.configure(state="disabled")
        self.update_idletasks()
        success = self._controller.delete_from_history(file_path)
        if success:
            self._status_label.configure(
                text=self._tr.get("wallpapers.deleted"), text_color=theme.COLOR_SUCCESS
            )
            self._populate_gallery()
        else:
            _logger.warning("Failed to delete wallpaper: %s", file_path)
            row._delete_armed = False  # type: ignore[attr-defined]
            button.configure(
                state="normal", text=self._tr.get("wallpapers.delete"),
                fg_color="transparent", text_color=theme.COLOR_ERROR,
            )
            self._status_label.configure(
                text=self._tr.get("wallpapers.delete_failed", name=file_path.name),
                text_color=theme.COLOR_ERROR,
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
            state="disabled", text=self._tr.get("wallpapers.creating_timelapse")
        )
        self._status_label.configure(text="")
        self.update_idletasks()
        success = self._controller.create_timelapse(output_path)
        self._timelapse_button.configure(
            state="normal", text=self._tr.get("wallpapers.create_timelapse")
        )
        if success:
            self._status_label.configure(
                text=self._tr.get("wallpapers.timelapse_success", path=str(output_path)),
                text_color=theme.COLOR_SUCCESS,
            )
        else:
            self._status_label.configure(
                text=self._tr.get("wallpapers.timelapse_failed"), text_color=theme.COLOR_ERROR
            )
