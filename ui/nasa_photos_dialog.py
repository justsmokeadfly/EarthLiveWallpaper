"""NASA APOD and James Webb photo browser dialog."""
from __future__ import annotations

import re
import threading
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from application.app_controller import AppController
from domain.enums import WallpaperMode
from infrastructure.nasa.nasa_media_service import NASAPhoto
from ui import theme
from ui.i18n import Translator

_THUMB = (360, 210)
_MODES = {
    "Заполнить (Fill)": WallpaperMode.FILL,
    "Вписать (Fit)": WallpaperMode.FIT,
    "Растянуть (Stretch)": WallpaperMode.STRETCH,
    "Замостить (Tile)": WallpaperMode.TILE,
    "По центру (Center)": WallpaperMode.CENTER,
    "На все мониторы (Span)": WallpaperMode.SPAN,
}


class NASAPhotosDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk,
        controller: AppController,
        translator: Translator,
        webb: bool = False,
    ) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._webb = webb
        self._photos: list[NASAPhoto] = []
        self._refs: list[ctk.CTkImage] = []
        self._descriptions: dict[str, str] = {}
        self._description_labels: dict[str, ctk.CTkLabel] = {}
        self._busy = 0
        self.title("James Webb Fotos" if webb else "NASA Fotos")
        self.geometry("980x760")
        self.minsize(820, 640)
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
        self._language = ctk.CTkSegmentedButton(
            header,
            values=["RU", "EN"],
            command=self._language_changed,
        )
        self._language.set("RU")
        self._language.pack(side="right")
        self._progress = ctk.CTkProgressBar(
            self,
            mode="indeterminate",
            corner_radius=theme.CORNER_RADIUS,
        )
        self._progress.start()
        self._progress.pack(fill="x", padx=theme.PADDING, pady=(0, 6))
        self._status = ctk.CTkLabel(
            self,
            text="Загрузка фотографий…",
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self._status.pack(pady=(0, 6))
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(
            fill="both",
            expand=True,
            padx=theme.PADDING,
            pady=(0, theme.PADDING),
        )

    def _load_async(self) -> None:
        self._set_busy(True)
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self) -> None:
        try:
            photos = (
                [self._controller.get_nasa_apod()]
                if not self._webb
                else self._controller.get_webb_photos()
            )
            self.after(0, lambda: self._loaded(photos))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda message=message: self._failed(message))

    def _loaded(self, photos: list[NASAPhoto]) -> None:
        self._progress.stop()
        self._photos = photos
        self._status.configure(text=f"Найдено фотографий: {len(photos)}")
        self._populate()
        self._set_busy(False)
        self._load_descriptions_async()

    def _failed(self, message: str) -> None:
        self._progress.stop()
        self._set_busy(False)
        self._status.configure(
            text=f"Ошибка загрузки: {message}",
            text_color=theme.COLOR_ERROR,
        )

    def _language_changed(self, value: str) -> None:
        if value == "EN":
            for photo in self._photos:
                label = self._description_labels.get(photo.title)
                if label is not None:
                    label.configure(text=photo.description_en)
            return
        for photo in self._photos:
            label = self._description_labels.get(photo.title)
            if label is not None:
                label.configure(text=self._descriptions.get(photo.title, photo.description_en))

    def _populate(self) -> None:
        for child in self._scroll.winfo_children():
            child.destroy()
        self._refs.clear()
        self._description_labels.clear()
        for photo in self._photos:
            self._add_card(photo)

    def _add_card(self, photo: NASAPhoto) -> None:
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=theme.COLOR_SURFACE,
            corner_radius=theme.CORNER_RADIUS,
        )
        card.pack(fill="x", pady=7)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=10)

        preview = ctk.CTkLabel(body, text="Превью…", width=360, height=210)
        preview.pack(side="left", padx=(0, 12))
        threading.Thread(
            target=self._load_preview,
            args=(photo, preview),
            daemon=True,
        ).start()

        info = ctk.CTkFrame(body, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            info,
            text=photo.title,
            anchor="w",
            justify="left",
            wraplength=460,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(fill="x", pady=(0, 6))

        description = (
            photo.description_en
            if self._language.get() == "EN"
            else self._descriptions.get(photo.title, photo.description_en)
        )
        description_label = ctk.CTkLabel(
            info,
            text=description,
            anchor="nw",
            justify="left",
            wraplength=460,
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        description_label.pack(fill="both", expand=True)
        self._description_labels[photo.title] = description_label
        self._add_actions(info, photo)

    def _add_actions(self, parent: ctk.CTkFrame, photo: NASAPhoto) -> None:
        mode = ctk.CTkComboBox(parent, values=list(_MODES))
        mode.set("Заполнить (Fill)")
        mode.pack(fill="x", pady=(8, 5))
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x")
        ctk.CTkButton(
            actions,
            text="Скачать",
            command=lambda p=photo: self._download(p),
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            actions,
            text="Установить как обои",
            command=lambda p=photo, m=mode: self._install(p, m.get()),
        ).pack(side="left")

    def _load_descriptions_async(self) -> None:
        if self._language.get() != "RU":
            return
        for photo in self._photos:
            if not photo.description_en:
                continue
            threading.Thread(
                target=self._translate_worker,
                args=(photo,),
                daemon=True,
            ).start()

    def _translate_worker(self, photo: NASAPhoto) -> None:
        try:
            translated = self._controller.translate_nasa_description(photo.description_en)
        except Exception:
            translated = photo.description_en
        self.after(0, lambda p=photo, text=translated: self._description_ready(p, text))

    def _description_ready(self, photo: NASAPhoto, text: str) -> None:
        self._descriptions[photo.title] = text
        if self._language.get() != "RU":
            return
        label = self._description_labels.get(photo.title)
        if label is not None:
            label.configure(text=text)

    def _load_preview(self, photo: NASAPhoto, label: ctk.CTkLabel) -> None:
        try:
            preview_url = _preview_url(photo.image_url, self._webb)
            preview_name = "preview_" + _safe_name(photo.title) + ".jpg"
            path = self._controller.wallpapers_dir / ".previews" / preview_name
            if not path.exists():
                self._controller.download_nasa_photo(photo, path, image_url=preview_url)
            with Image.open(path) as image:
                image.thumbnail(_THUMB, Image.LANCZOS)
                img = ctk.CTkImage(
                    light_image=image.copy(),
                    dark_image=image.copy(),
                    size=image.size,
                )
            self.after(0, lambda: self._set_preview(label, img))
        except Exception:
            self.after(0, lambda: label.configure(text="Превью недоступно"))

    def _set_preview(self, label: ctk.CTkLabel, image: ctk.CTkImage) -> None:
        self._refs.append(image)
        label.configure(text="", image=image)

    def _download(self, photo: NASAPhoto) -> None:
        path = self._unique_path(photo)
        self._run_transfer(
            photo,
            path,
            success_text=f"Сохранено: {path.name}",
        )

    def _install(self, photo: NASAPhoto, selected_mode: str) -> None:
        path = self._unique_path(photo)
        mode = _MODES.get(selected_mode, WallpaperMode.FILL)

        def completed() -> None:
            if self._controller.apply_external_wallpaper(path, mode):
                self._status.configure(
                    text="Обои установлены!",
                    text_color=theme.COLOR_SUCCESS,
                )
            else:
                self._status.configure(
                    text="Не удалось установить обои.",
                    text_color=theme.COLOR_ERROR,
                )

        self._run_transfer(photo, path, success_callback=completed)

    def _run_transfer(
        self,
        photo: NASAPhoto,
        destination: Path,
        success_text: str | None = None,
        success_callback: Callable[[], None] | None = None,
    ) -> None:
        self._set_busy(True)
        self._progress.configure(mode="determinate")
        self._progress.set(0.0)
        self._progress.stop()
        self._status.configure(
            text="Скачивание…",
            text_color=theme.COLOR_TEXT_SECONDARY,
        )

        def worker() -> None:
            try:
                def progress(current: int, total: int) -> None:
                    fraction = current / total if total > 0 else 0.0
                    self.after(0, lambda value=fraction: self._set_transfer_progress(value))

                self._controller.download_nasa_photo(photo, destination, progress)
                self.after(0, lambda: self._transfer_done(success_text, success_callback))
            except Exception as exc:
                message = str(exc)
                self.after(0, lambda message=message: self._transfer_failed(message))

        threading.Thread(target=worker, daemon=True).start()

    def _set_transfer_progress(self, fraction: float) -> None:
        self._progress.set(max(0.0, min(1.0, fraction)))

    def _transfer_done(
        self,
        success_text: str | None,
        success_callback: Callable[[], None] | None,
    ) -> None:
        self._set_busy(False)
        self._progress.set(1.0)
        if success_callback is not None:
            success_callback()
        elif success_text:
            self._status.configure(
                text=success_text,
                text_color=theme.COLOR_SUCCESS,
            )

    def _transfer_failed(self, message: str) -> None:
        self._set_busy(False)
        self._progress.set(0.0)
        self._status.configure(
            text=f"Ошибка скачивания: {message}",
            text_color=theme.COLOR_ERROR,
        )

    def _set_busy(self, busy: bool) -> None:
        self._busy = max(0, self._busy + (1 if busy else -1))
        state = "disabled" if self._busy else "normal"
        self._language.configure(state=state)

    def _unique_path(self, photo: NASAPhoto) -> Path:
        suffix = ".png" if ".png" in photo.image_url.lower() else ".jpg"
        return self._controller.wallpapers_dir / f"nasa_{_safe_name(photo.title)}{suffix}"


def _preview_url(image_url: str, webb: bool) -> str:
    if not webb or "flickr" not in image_url.lower():
        return image_url
    return re.sub(
        r"(_[a-z])(?=\.[a-z0-9]+$)",
        "_z",
        image_url,
        flags=re.IGNORECASE,
    )


def _safe_name(value: str) -> str:
    value = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)
    return value[:100] or "photo"
