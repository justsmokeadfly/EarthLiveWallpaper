"""EarthLive entry point.

Usage:
    python main.py                # launch with UI + tray icon
    python main.py --headless     # run as a background updater only
    python main.py --update-now   # force an immediate update, then continue
    python main.py --config PATH  # use a specific config file location
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from app import build_app_controller
from logger import get_logger

_logger = get_logger(__name__)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (excluding the program name).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="EarthLive",
        description="Automatically download the latest Himawari satellite "
        "image and set it as the Windows desktop wallpaper.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without any GUI or tray icon, as a pure background updater.",
    )
    parser.add_argument(
        "--update-now",
        action="store_true",
        help="Force an immediate update check on startup, in addition to normal operation.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a specific config.json file to use instead of the default location.",
    )
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Store all data (config, state, cache, wallpapers, logs) in a "
        "'data' folder next to the executable instead of %%APPDATA%%.",
    )
    return parser.parse_args(argv)


def _run_headless(controller, update_now: bool) -> None:
    """Run EarthLive with no UI: start the scheduler and block until
    interrupted (Ctrl+C or SIGTERM).

    Args:
        controller: A fully wired AppController.
        update_now: If ``True``, force an immediate update cycle right
            after the scheduler starts, in addition to its normal
            startup check.
    """
    _logger.info("Running in headless mode.")
    controller.start()
    if update_now:
        _logger.info("--update-now specified: triggering forced immediate update.")
        controller.trigger_update_now()

    stop_requested = False

    def _handle_signal(signum: int, frame: object) -> None:
        nonlocal stop_requested
        _logger.info("Received signal %s; shutting down.", signum)
        stop_requested = True

    signal.signal(signal.SIGINT, _handle_signal)
    try:
        signal.signal(signal.SIGTERM, _handle_signal)
    except (ValueError, AttributeError):
        pass  # SIGTERM not available on this platform/thread context

    try:
        while not stop_requested:
            time.sleep(1.0)
    finally:
        controller.stop()
        _logger.info("EarthLive headless mode stopped.")


def _run_with_ui(controller, update_now: bool) -> None:
    """Run EarthLive with the full CustomTkinter UI and system tray icon.

    Args:
        controller: A fully wired AppController.
        update_now: If ``True``, force an immediate update cycle right
            after the scheduler starts.
    """
    from ui.main_window import MainWindow
    from ui.tray_icon import TrayIcon

    controller.start()
    if update_now:
        _logger.info("--update-now specified: triggering forced immediate update.")
        controller.trigger_update_now()

    window = MainWindow(controller)

    def _show_window() -> None:
        window.after(0, window.deiconify)
        window.after(0, window.lift)

    def _quit() -> None:
        window.after(0, window.destroy)

    tray = TrayIcon(
        controller, window.translator, on_show_window=_show_window, on_quit=_quit
    )
    tray.start()

    def _notify_result(result) -> None:
        from domain.enums import UpdateOutcome

        # Only notify for outcomes the user would actually care about:
        # a real change, or a real failure. Routine no-ops (already up to
        # date, paused, duplicate content) stay silent to avoid spam.
        if result.outcome == UpdateOutcome.SUCCESS or result.is_actionable_failure:
            tray.notify(window.translator.get("notification.title"), result.message)

    controller.set_notifier(_notify_result)

    def _on_close() -> None:
        # Hide to tray instead of exiting, matching typical Windows
        # utility behavior for this kind of background application.
        window.withdraw()

    window.protocol("WM_DELETE_WINDOW", _on_close)

    try:
        window.mainloop()
    finally:
        tray.stop()
        controller.stop()
        _logger.info("EarthLive UI mode stopped.")


def main(argv: list[str] | None = None) -> int:
    """Application entry point.

    Args:
        argv: Command-line arguments (excluding program name). Defaults
            to ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    try:
        controller = build_app_controller(
            config_override_path=args.config, portable=args.portable
        )
    except Exception:
        _logger.exception("Fatal error during startup.")
        return 1

    try:
        if args.headless:
            _run_headless(controller, update_now=args.update_now)
        else:
            _run_with_ui(controller, update_now=args.update_now)
    except Exception:
        _logger.exception("Fatal error during execution.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
