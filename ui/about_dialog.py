"""Modern About dialog for EarthLive Wallpaper."""

from __future__ import annotations

import webbrowser

import customtkinter as ctk

from logger import get_logger
from ui import theme
from ui.i18n import Translator

_logger = get_logger(__name__)
APP_VERSION = "1.8.3"
APP_AUTHOR = "@justsmokeadfly"
SOURCE_URL = "https://github.com/justsmokeadfly/EarthLiveWallpaper"
AUTHOR_URL = "https://github.com/justsmokeadfly"


class AboutDialog(ctk.CTkToplevel):
    """Display EarthLive Wallpaper information, credits, and project links."""

    def __init__(self, master: ctk.CTk, translator: Translator) -> None:
        super().__init__(master)
        self._tr = translator
        self.title(self._tr.get("about.title"))
        self.geometry("460x540")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BACKGROUND)
        self.transient(master)
        self.grab_set()
        self._build_widgets()
        self.after(50, self._center_window)

    def _build_widgets(self) -> None:
        header = ctk.CTkFrame(self, fg_color=theme.COLOR_SURFACE, corner_radius=theme.CORNER_RADIUS)
        header.pack(fill="x", padx=18, pady=(18, 10))
        ctk.CTkLabel(header, text="🌍", font=(theme.FONT_FAMILY, 42), text_color=theme.COLOR_TEXT_PRIMARY).pack(pady=(18, 0))
        ctk.CTkLabel(header, text="EarthLive Wallpaper", font=(theme.FONT_FAMILY, 28, "bold"), text_color=theme.COLOR_TEXT_PRIMARY).pack(pady=(0, 2))
        ctk.CTkLabel(header, text=f"{self._tr.get('about.version')} {APP_VERSION}", font=(theme.FONT_FAMILY, theme.FONT_SIZE_SMALL), text_color=theme.COLOR_TEXT_SECONDARY).pack(pady=(0, 18))
        ctk.CTkLabel(self, text=self._tr.get("about.description"), font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY), text_color=theme.COLOR_TEXT_PRIMARY, wraplength=400, justify="center").pack(padx=24, pady=(8, 18))
        info = ctk.CTkFrame(self, fg_color=theme.COLOR_SURFACE, corner_radius=theme.CORNER_RADIUS)
        info.pack(fill="x", padx=18, pady=(0, 14))
        self._add_link_row(info, self._tr.get("about.author"), f"{APP_AUTHOR} ↗", AUTHOR_URL)
        self._add_info_row(info, self._tr.get("about.license"), "MIT")
        self._add_link_row(info, self._tr.get("about.source"), self._tr.get("about.open_github"), SOURCE_URL)
        ctk.CTkLabel(self, text="NASA • James Webb • Hubble • Himawari • Multi-monitor", text_color=theme.COLOR_TEXT_SECONDARY).pack(pady=(0, 12))
        ctk.CTkButton(self, text=self._tr.get("about.close"), command=self.destroy, fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS, height=38).pack(fill="x", padx=18, pady=(0, 18))

    def _add_info_row(self, parent: ctk.CTkBaseClass, label: str, value: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=7)
        ctk.CTkLabel(row, text=label, text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=value, font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"), text_color=theme.COLOR_TEXT_PRIMARY, anchor="e").pack(side="right")

    def _add_link_row(self, parent: ctk.CTkBaseClass, label: str, link_text: str, url: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=7)
        ctk.CTkLabel(row, text=label, text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(side="left")
        link = ctk.CTkLabel(row, text=link_text, font=(theme.FONT_FAMILY, theme.FONT_SIZE_BODY, "bold"), text_color=theme.COLOR_ACCENT, anchor="e", cursor="hand2")
        link.pack(side="right")
        link.bind("<Button-1>", lambda _event: self._open_url(url))

    def _open_url(self, url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception:
            _logger.exception("Failed to open URL: %s", url)

    def _center_window(self) -> None:
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
