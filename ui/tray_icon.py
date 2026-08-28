"""System tray icon integration using ``pystray``.

Runs in its own daemon thread (pystray's ``Icon.run()`` is blocking), and
communicates back to the main Tkinter thread exclusively through
thread-safe calls on the injected :class:`AppController` plus
``CTk.after()`` for anything that must touch Tk widgets, since Tkinter is
not thread-safe.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

import pystray
from PIL import Image

from application.app_controller import AppController
from logger import get_logger
from ui.i18n import Translator

_logger = get_logger(__name__)

_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icon.png"


class TrayIcon:
    """Wraps a ``pystray.Icon`` running on a dedicated background thread."""

    def __init__(
        self,
        controller: AppController,
        translator: Translator,
        on_show_window: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        """Initialize the tray icon.

        Args:
            controller: Application-layer facade for triggering updates.
            translator: Active Translator, for localized menu items.
            on_show_window: Called (via the Tk thread) when the user
                chooses "Open EarthLive" or double-clicks the icon.
            on_quit: Called when the user chooses "Quit" from the menu.
        """
        self._controller = controller
        self._tr = translator
        self._on_show_window = on_show_window
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the tray icon on a background thread."""
        image = self._load_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem(self._tr.get("tray.open"), self._handle_show, default=True),
            pystray.MenuItem(self._tr.get("tray.update_now"), self._handle_update_now),
            pystray.MenuItem(self._tr.get("tray.quit"), self._handle_quit),
        )
        self._icon = pystray.Icon("EarthLive", image, self._tr.get("app_title"), menu)

        self._thread = threading.Thread(
            target=self._icon.run, name="EarthLiveTray", daemon=True
        )
        self._thread.start()
        _logger.info("Tray icon started.")

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon is not None:
            self._icon.stop()
        _logger.info("Tray icon stopped.")

    def notify(self, title: str, message: str) -> None:
        """Show a system tray notification (Windows toast), if supported.

        Args:
            title: Notification title.
            message: Notification body text.
        """
        if self._icon is None:
            return
        try:
            self._icon.notify(message, title)
        except NotImplementedError:
            _logger.debug("Tray notifications not supported on this backend.")
        except Exception:
            _logger.exception("Failed to show tray notification.")

    def _handle_show(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle "Open EarthLive" selection."""
        self._on_show_window()

    def _handle_update_now(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle "Update now" selection."""
        self._controller.trigger_update_now()

    def _handle_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle "Quit" selection."""
        self._on_quit()

    @staticmethod
    def _load_icon_image() -> Image.Image:
        """Load the tray icon image, falling back to a generated
        placeholder if the asset file is missing.
        """
        if _ICON_PATH.exists():
            try:
                return Image.open(_ICON_PATH).convert("RGBA")
            except OSError:
                _logger.warning("Failed to load icon asset; using placeholder.")

        placeholder = Image.new("RGBA", (64, 64), (13, 17, 23, 255))
        return placeholder
