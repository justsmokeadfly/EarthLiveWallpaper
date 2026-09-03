"""NASA, James Webb, and Hubble photo browser dialog."""
from __future__ import annotations

import threading
import webbrowser
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import customtkinter as ctk
from PIL import Image

from application.app_controller import AppController
from domain.enums import WallpaperMode
from infrastructure.nasa.nasa_media_service import FlickrSize, NASAPhoto
from logger import get_logger
from ui import theme
from ui.clipboard_fix import enable_clipboard_shortcuts
from ui.i18n import Translator

_logger = get_logger(__name__)

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
    def __init__(self, master: ctk.CTk, controller: AppController, translator: Translator, webb: bool = False, source: str | None = None) -> None:
        super().__init__(master)
        self._controller = controller
        self._tr = translator
        self._source = source or ("webb" if webb else "nasa")
        self._photos: list[NASAPhoto] = []
        self._refs: list[ctk.CTkImage] = []
        self._descriptions: dict[str, str] = {}
        self._description_labels: dict[str, ctk.CTkLabel] = {}
        self._resolution_labels: dict[str, ctk.CTkLabel] = {}
        self._favorite_buttons: dict[str, ctk.CTkButton] = {}
        self._busy = 0
        titles = {"nasa": "NASA Fotos", "webb": "James Webb Fotos", "hubble": "Hubble Fotos"}
        self.title(titles.get(self._source, "Space Fotos"))
        self.geometry("1040x800")
        self.minsize(860, 660)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self.transient(master)
        self.grab_set()
        self._build()
        enable_clipboard_shortcuts(self)
        self._load_async()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PADDING, pady=theme.PADDING)
        heading = {"nasa": "🚀 NASA Fotos", "webb": "🔭 James Webb Fotos", "hubble": "🛰️ Hubble Fotos"}
        ctk.CTkLabel(header, text=heading.get(self._source, "🌌 Space Fotos"), font=(theme.FONT_FAMILY, theme.FONT_SIZE_TITLE, "bold"), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
        self._search = ctk.CTkEntry(header, placeholder_text="Поиск по названию и описанию…")
        self._search.pack(side="left", fill="x", expand=True, padx=12)
        self._search.bind("<KeyRelease>", self._search_changed)
        self._favorites_only = ctk.CTkCheckBox(header, text="⭐ Избранное", command=self._search_changed)
        self._favorites_only.pack(side="left", padx=(0, 12))
        self._language = ctk.CTkSegmentedButton(header, values=["RU", "EN"], command=self._language_changed)
        self._language.set("RU")
        self._language.pack(side="right")
        self._progress = ctk.CTkProgressBar(self, mode="indeterminate", corner_radius=theme.CORNER_RADIUS)
        self._progress.start()
        self._progress.pack(fill="x", padx=theme.PADDING, pady=(0, 6))
        self._status = ctk.CTkLabel(self, text="Загрузка фотографий…", text_color=theme.COLOR_TEXT_SECONDARY)
        self._status.pack(pady=(0, 6))
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=theme.PADDING, pady=(0, theme.PADDING))

    def _load_async(self) -> None:
        self._set_busy(True)
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self) -> None:
        try:
            if self._source == "nasa":
                photos = [self._controller.get_nasa_apod()]
            elif self._source == "webb":
                photos = self._controller.get_webb_photos()
            else:
                photos = self._controller.get_hubble_photos()
            self.after(0, lambda: self._loaded(photos))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda message=message: self._failed(message))

    def _loaded(self, photos: list[NASAPhoto]) -> None:
        self._progress.stop()
        self._photos = photos
        self._populate()
        self._set_busy(False)
        self._load_descriptions_async()

    def _failed(self, message: str) -> None:
        self._progress.stop()
        self._set_busy(False)
        self._status.configure(text=f"Ошибка загрузки: {message}", text_color=theme.COLOR_ERROR)

    def _language_changed(self, value: str) -> None:
        for photo in self._photos:
            label = self._description_labels.get(photo.title)
            if label is not None:
                label.configure(text=photo.description_en if value == "EN" else self._descriptions.get(photo.title, photo.description_en))

    def _search_changed(self, _event: Any = None) -> None:
        self._populate()

    def _populate(self) -> None:
        query = self._search.get().strip().lower()
        favorites_only = bool(self._favorites_only.get())
        filtered: list[NASAPhoto] = []
        for photo in self._photos:
            text = f"{photo.title} {photo.description_en}".lower()
            is_favorite = self._controller.is_nasa_favorite(photo)
            if query and query not in text:
                continue
            if favorites_only and not is_favorite:
                continue
            filtered.append(photo)
        for child in self._scroll.winfo_children():
            child.destroy()
        self._refs.clear()
        self._description_labels.clear()
        self._resolution_labels.clear()
        self._favorite_buttons.clear()
        for photo in filtered:
            self._add_card(photo)
        self._status.configure(text=f"Показано: {len(filtered)} из {len(self._photos)}")

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
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(title_row, text=photo.title, anchor="w", justify="left", wraplength=430, font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left", fill="x", expand=True)
        favorite = ctk.CTkButton(title_row, text="★" if self._controller.is_nasa_favorite(photo) else "☆", width=42, command=lambda p=photo: self._toggle_favorite(p))
        favorite.pack(side="right")
        self._favorite_buttons[photo.title] = favorite
        resolution_label = ctk.CTkLabel(
            info,
            text=_format_resolution(photo.width, photo.height),
            anchor="w",
            text_color=theme.COLOR_TEXT_SECONDARY,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL),
        )
        resolution_label.pack(fill="x", pady=(0, 4))
        self._resolution_labels[photo.title] = resolution_label
        links_row = ctk.CTkFrame(info, fg_color="transparent")
        links_row.pack(fill="x", pady=(0, 6))
        image_link = ctk.CTkLabel(
            links_row,
            text="🔗 Открыть изображение",
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL, "bold"),
            text_color=theme.COLOR_ACCENT,
            cursor="hand2",
        )
        image_link.pack(side="left")
        image_link.bind("<Button-1>", lambda _e, url=photo.image_url: self._open_url(url))
        if photo.source_url and photo.source_url != photo.image_url:
            source_link = ctk.CTkLabel(
                links_row,
                text="  ·  Источник",
                font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL, "bold"),
                text_color=theme.COLOR_ACCENT,
                cursor="hand2",
            )
            source_link.pack(side="left")
            source_link.bind("<Button-1>", lambda _e, url=photo.source_url: self._open_url(url))
        description = photo.description_en if self._language.get() == "EN" else self._descriptions.get(photo.title, photo.description_en)
        description_label = ctk.CTkLabel(info, text=description, anchor="nw", justify="left", wraplength=460, text_color=theme.COLOR_TEXT_SECONDARY)
        description_label.pack(fill="both", expand=True)
        self._description_labels[photo.title] = description_label
        self._add_actions(info, photo)

    def _add_actions(self, parent: ctk.CTkFrame, photo: NASAPhoto) -> None:
        mode = ctk.CTkComboBox(parent, values=list(_MODES))
        mode.set("Заполнить (Fill)")
        mode.pack(fill="x", pady=(8, 5))
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x")
        ctk.CTkButton(actions, text="Скачать", command=lambda p=photo: self._download(p)).pack(side="left", padx=(0, 5))
        ctk.CTkButton(actions, text="Установить как обои", command=lambda p=photo, m=mode: self._install(p, m.get())).pack(side="left")

    def _open_url(self, url: str) -> None:
        if not url:
            return
        try:
            webbrowser.open(url)
        except Exception:
            _logger.exception("Failed to open URL: %s", url)

    def _toggle_favorite(self, photo: NASAPhoto) -> None:
        favorite = self._controller.toggle_nasa_favorite(photo)
        button = self._favorite_buttons.get(photo.title)
        if button is not None:
            button.configure(text="★" if favorite else "☆")
        if self._favorites_only.get():
            self._populate()

    def _load_descriptions_async(self) -> None:
        if self._language.get() != "RU":
            return
        for photo in self._photos:
            if photo.description_en:
                threading.Thread(target=self._translate_worker, args=(photo,), daemon=True).start()

    def _translate_worker(self, photo: NASAPhoto) -> None:
        try:
            translated = self._controller.translate_nasa_description(photo.description_en)
        except Exception:
            translated = photo.description_en
        self.after(0, lambda p=photo, text=translated: self._description_ready(p, text))

    def _description_ready(self, photo: NASAPhoto, text: str) -> None:
        self._descriptions[photo.title] = text
        if self._language.get() == "RU":
            label = self._description_labels.get(photo.title)
            if label is not None:
                label.configure(text=text)

    def _load_preview(self, photo: NASAPhoto, label: ctk.CTkLabel) -> None:
        try:
            preview_url = photo.thumbnail_url or photo.image_url
            preview_name = "preview_" + _safe_name(photo.title) + ".jpg"
            path = self._controller.wallpapers_dir / ".previews" / preview_name
            if not path.exists():
                self._controller.download_nasa_photo(photo, path, image_url=preview_url)
            with Image.open(path) as image:
                if not photo.width or not photo.height:
                    self.after(0, lambda size=image.size: self._set_resolution(photo, size))
                image.thumbnail(_THUMB, Image.LANCZOS)
                img = ctk.CTkImage(light_image=image.copy(), dark_image=image.copy(), size=image.size)
            self.after(0, lambda: self._set_preview(label, img))
        except Exception:
            self.after(0, lambda: label.configure(text="Превью недоступно"))

    def _set_resolution(self, photo: NASAPhoto, size: tuple[int, int]) -> None:
        label = self._resolution_labels.get(photo.title)
        if label is not None:
            label.configure(text=_format_resolution(*size))

    def _set_preview(self, label: ctk.CTkLabel, image: ctk.CTkImage) -> None:
        self._refs.append(image)
        label.configure(text="", image=image)

    def _download(self, photo: NASAPhoto) -> None:
        def proceed(chosen: NASAPhoto) -> None:
            path = self._unique_path(chosen)
            self._run_transfer(chosen, path, success_text=f"Сохранено: {path.name}")

        self._choose_size(photo, proceed)

    def _install(self, photo: NASAPhoto, selected_mode: str) -> None:
        mode = _MODES.get(selected_mode, WallpaperMode.FILL)

        def proceed(chosen: NASAPhoto) -> None:
            path = self._unique_path(chosen)

            def completed() -> None:
                if self._controller.apply_external_wallpaper(path, mode):
                    self._status.configure(text="Обои установлены!", text_color=theme.COLOR_SUCCESS)
                else:
                    self._status.configure(text="Не удалось установить обои.", text_color=theme.COLOR_ERROR)

            self._run_transfer(chosen, path, success_callback=completed)

        self._choose_size(photo, proceed)

    def _choose_size(self, photo: NASAPhoto, callback: Callable[[NASAPhoto], None]) -> None:
        if photo.source == "nasa":
            # NASA APOD already uses NASA's best available (hdurl) - no
            # Flickr size ladder to choose from.
            callback(photo)
            return
        self._set_busy(True)
        self._status.configure(text="Определяю доступные размеры…", text_color=theme.COLOR_TEXT_SECONDARY)

        def worker() -> None:
            try:
                sizes = self._controller.list_flickr_sizes(photo)
            except Exception:
                _logger.exception("Failed to list Flickr sizes for %s", photo.title)
                sizes = []
            self.after(0, lambda: self._sizes_ready(photo, sizes, callback))

        threading.Thread(target=worker, daemon=True).start()

    def _sizes_ready(
        self,
        photo: NASAPhoto,
        sizes: list[FlickrSize],
        callback: Callable[[NASAPhoto], None],
    ) -> None:
        self._set_busy(False)
        self._status.configure(text="")
        if len(sizes) <= 1:
            callback(photo)
            return
        _SizePickerDialog(self, photo, sizes, callback)

    def _run_transfer(self, photo: NASAPhoto, destination: Path, success_text: str | None = None, success_callback: Callable[[], None] | None = None) -> None:
        self._set_busy(True)
        self._progress.configure(mode="determinate")
        self._progress.set(0.0)
        self._progress.stop()
        self._status.configure(text="Скачивание…", text_color=theme.COLOR_TEXT_SECONDARY)

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

    def _transfer_done(self, success_text: str | None, success_callback: Callable[[], None] | None) -> None:
        self._set_busy(False)
        self._progress.set(1.0)
        if success_callback is not None:
            success_callback()
        elif success_text:
            self._status.configure(text=success_text, text_color=theme.COLOR_SUCCESS)

    def _transfer_failed(self, message: str) -> None:
        self._set_busy(False)
        self._progress.set(0.0)
        self._status.configure(text=f"Ошибка скачивания: {message}", text_color=theme.COLOR_ERROR)

    def _set_busy(self, busy: bool) -> None:
        self._busy = max(0, self._busy + (1 if busy else -1))
        state = "disabled" if self._busy else "normal"
        self._language.configure(state=state)
        self._search.configure(state=state)
        self._favorites_only.configure(state=state)

    def _unique_path(self, photo: NASAPhoto) -> Path:
        suffix = ".png" if ".png" in photo.image_url.lower() else ".jpg"
        return self._controller.wallpapers_dir / f"{photo.source}_{_safe_name(photo.title)}{suffix}"


class _SizePickerDialog(ctk.CTkToplevel):
    """Lets the user pick which available Flickr size to download."""

    def __init__(
        self,
        master: ctk.CTkToplevel,
        photo: NASAPhoto,
        sizes: list[FlickrSize],
        callback: Callable[[NASAPhoto], None],
    ) -> None:
        super().__init__(master)
        self._photo = photo
        self._callback = callback
        self._by_label = {size.label: size for size in sizes}
        self.title("Выбор разрешения")
        self.geometry("380x460")
        self.minsize(340, 320)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self.transient(master)
        self.grab_set()
        ctk.CTkLabel(
            self,
            text=photo.title,
            font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
            wraplength=340,
            justify="left",
        ).pack(padx=16, pady=(16, 4), anchor="w")
        ctk.CTkLabel(
            self,
            text="Доступные размеры на Flickr:",
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(padx=16, anchor="w", pady=(0, 8))
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16)
        self._selected = ctk.StringVar(value=sizes[0].label)
        for size in sizes:
            ctk.CTkRadioButton(scroll, text=size.label, variable=self._selected, value=size.label).pack(
                anchor="w", pady=5
            )
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=16)
        ctk.CTkButton(buttons, text="Отмена", fg_color=theme.COLOR_SURFACE, command=self._cancel).pack(
            side="left"
        )
        ctk.CTkButton(buttons, text="Продолжить", command=self._confirm).pack(side="right")
        enable_clipboard_shortcuts(self)

    def _confirm(self) -> None:
        size = self._by_label[self._selected.get()]
        chosen = replace(self._photo, image_url=size.url, width=size.width, height=size.height)
        self.destroy()
        self._callback(chosen)

    def _cancel(self) -> None:
        self.destroy()


def _safe_name(value: str) -> str:
    value = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)
    return value[:100] or "photo"


def _format_resolution(width: int, height: int) -> str:
    if not width or not height:
        return "Разрешение: определяется…"
    megapixels = (width * height) / 1_000_000
    return f"Разрешение: {width} × {height} ({megapixels:.1f} Мп)"
