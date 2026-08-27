"""NASA APOD and James Webb photo browser dialog."""
from __future__ import annotations

from pathlib import Path
import threading

import customtkinter as ctk
from PIL import Image

from application.app_controller import AppController
from domain.enums import WallpaperMode
from infrastructure.nasa.nasa_media_service import NASAPhoto
from ui import theme
from ui.i18n import Translator

_THUMB = (360, 210)


class NASAPhotosDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, controller: AppController, translator: Translator, webb: bool = False) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._webb = webb
        self._photos: list[NASAPhoto] = []
        self._refs: list[ctk.CTkImage] = []
        self.title("James Webb Fotos" if webb else "NASA Fotos")
        self.geometry("900x720")
        self.minsize(760, 600)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self.transient(master)
        self.grab_set()
        self._build()
        self._load_async()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PADDING, pady=theme.PADDING)
        ctk.CTkLabel(
            header,
            text="🔭 James Webb Fotos" if self._webb else "🚀 NASA Fotos",
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_TITLE, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(side="left")
        self._language = ctk.CTkSegmentedButton(header, values=["RU", "EN"], command=self._language_changed)
        self._language.set("RU")
        self._language.pack(side="right")
        self._progress = ctk.CTkProgressBar(self, mode="indeterminate", corner_radius=theme.CORNER_RADIUS)
        self._progress.pack(fill="x", padx=theme.PADDING, pady=(0, 6))
        self._status = ctk.CTkLabel(self, text="Загрузка фотографий...", text_color=theme.COLOR_TEXT_SECONDARY)
        self._status.pack(pady=(0, 6))
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=theme.PADDING, pady=(0, theme.PADDING))

    def _load_async(self) -> None:
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self) -> None:
        try:
            photos = [self._controller.get_nasa_apod()] if not self._webb else self._controller.get_webb_photos()
            self.after(0, lambda: self._loaded(photos))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda message=message: self._failed(message))

    def _loaded(self, photos: list[NASAPhoto]) -> None:
        self._progress.stop()
        self._photos = photos
        self._status.configure(text=f"{len(photos)}")
        self._populate()

    def _failed(self, message: str) -> None:
        self._progress.stop()
        self._status.configure(text=f"Ошибка загрузки: {message}", text_color=theme.COLOR_ERROR)

    def _language_changed(self, value: str) -> None:
        self._populate()

    def _populate(self) -> None:
        for child in self._scroll.winfo_children():
            child.destroy()
        self._refs.clear()
        for photo in self._photos:
            self._add_card(photo)

    def _add_card(self, photo: NASAPhoto) -> None:
        card = ctk.CTkFrame(self._scroll, fg_color=theme.COLOR_SURFACE, corner_radius=theme.CORNER_RADIUS)
        card.pack(fill="x", pady=7)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=10)
        preview = ctk.CTkLabel(body, text="Превью…", width=360, height=210)
        preview.pack(side="left", padx=(0, 12))
        threading.Thread(target=self._load_preview, args=(photo, preview), daemon=True).start()
        info = ctk.CTkFrame(body, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            info,
            text=photo.title,
            anchor="w",
            justify="left",
            wraplength=420,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(fill="x", pady=(0, 6))
        description = photo.description_en
        if self._language.get() == "RU":
            description = self._controller.translate_nasa_description(description)
        ctk.CTkLabel(
            info,
            text=description,
            anchor="nw",
            justify="left",
            wraplength=420,
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(fill="both", expand=True)
        mode = ctk.CTkComboBox(info, values=["Fill", "Fit", "Stretch", "Tile", "Center", "Span"])
        mode.set("Fill")
        mode.pack(fill="x", pady=(8, 5))
        actions = ctk.CTkFrame(info, fg_color="transparent")
        actions.pack(fill="x")
        ctk.CTkButton(actions, text="Скачать", command=lambda p=photo: self._download(p)).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            actions,
            text="Установить как обои",
            command=lambda p=photo, m=mode: self._install(p, m),
        ).pack(side="left")

    def _load_preview(self, photo: NASAPhoto, label: ctk.CTkLabel) -> None:
        try:
            path = self._controller.wallpapers_dir / ("preview_" + _safe_name(photo.title) + ".jpg")
            self._controller.download_nasa_photo(photo, path)
            with Image.open(path) as image:
                image.thumbnail(_THUMB, Image.LANCZOS)
                img = ctk.CTkImage(light_image=image.copy(), dark_image=image.copy(), size=image.size)
            self.after(0, lambda: self._set_preview(label, img))
        except Exception:
            self.after(0, lambda: label.configure(text="Превью недоступно"))

    def _set_preview(self, label: ctk.CTkLabel, image: ctk.CTkImage) -> None:
        self._refs.append(image)
        label.configure(text="", image=image)

    def _download(self, photo: NASAPhoto) -> None:
        path = self._unique_path(photo)
        self._controller.download_nasa_photo(photo, path, lambda current, total: None)
        self._status.configure(text=f"Сохранено: {path.name}", text_color=theme.COLOR_SUCCESS)

    def _install(self, photo: NASAPhoto, mode_box: ctk.CTkComboBox) -> None:
        path = self._unique_path(photo)
        self._controller.download_nasa_photo(photo, path)
        mode_map = {
            "Fill": WallpaperMode.FILL,
            "Fit": WallpaperMode.FIT,
            "Stretch": WallpaperMode.STRETCH,
            "Tile": WallpaperMode.TILE,
            "Center": WallpaperMode.CENTER,
            "Span": WallpaperMode.SPAN,
        }
        if self._controller.apply_external_wallpaper(path, mode_map[mode_box.get()]):
            self._status.configure(text="Обои установлены!", text_color=theme.COLOR_SUCCESS)
        else:
            self._status.configure(text="Не удалось установить обои.", text_color=theme.COLOR_ERROR)

    def _unique_path(self, photo: NASAPhoto) -> Path:
        return self._controller.wallpapers_dir / f"nasa_{_safe_name(photo.title)}.jpg"


def _safe_name(value: str) -> str:
    value = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)
    return value[:100] or "photo"
