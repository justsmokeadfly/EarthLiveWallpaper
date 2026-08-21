"""Background scheduling service.

Wraps the ``schedule`` library's polling loop inside a dedicated daemon
thread, so it can run alongside a CustomTkinter mainloop (or headless,
with no UI at all) without blocking anything. Also exposes a thread-safe
"trigger immediate update" mechanism for the UI's "Update now" button and
the ``--update-now`` CLI flag.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import schedule

from application.results import UpdateResult
from logger import get_logger

_logger = get_logger(__name__)

_POLL_INTERVAL_SECONDS = 1.0


class SchedulerService:
    """Runs an update callback on a recurring interval in a background
    thread, plus supports on-demand immediate triggers.
    """

    def __init__(self, update_callback: Callable[[bool], UpdateResult]) -> None:
        """Initialize the scheduler.

        Args:
            update_callback: Called to perform one update cycle. Receives
                a single ``force: bool`` argument (``True`` for manual
                triggers) and returns an UpdateResult.
        """
        self._update_callback = update_callback
        self._scheduler = schedule.Scheduler()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._trigger_event = threading.Event()
        self._lock = threading.Lock()
        self._next_run_at: datetime | None = None
        self._last_result: UpdateResult | None = None
        self._pending_force: bool = False

    def start(self, check_interval_hours: float, run_immediately: bool = False) -> None:
        """Start the background scheduling thread.

        Args:
            check_interval_hours: Hours between automatic update checks.
            run_immediately: If ``True``, perform one update cycle right
                away instead of waiting for the first interval to elapse.
                The default is ``False`` so launching EarthLive never
                changes the wallpaper automatically.
        """
        if self._thread is not None and self._thread.is_alive():
            _logger.warning("Scheduler already running; ignoring start() call.")
            return

        self._scheduler.clear()
        self._scheduler.every(check_interval_hours).hours.do(self._run_scheduled_update)
        self._update_next_run()

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="EarthLiveScheduler", daemon=True
        )
        self._thread.start()
        _logger.info(
            "Scheduler started (interval=%.1fh, immediate=%s).",
            check_interval_hours,
            run_immediately,
        )

        if run_immediately:
            self.trigger_now(force=False)

    def stop(self) -> None:
        """Stop the background scheduling thread and wait for it to exit."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        _logger.info("Scheduler stopped.")

    def trigger_now(self, force: bool = True) -> None:
        """Request an immediate update cycle, independent of the schedule.

        Args:
            force: Passed through to the update callback; ``True`` bypasses
                the "already up to date" short-circuit.
        """
        self._pending_force = force
        self._trigger_event.set()

    def get_next_run_at(self) -> datetime | None:
        """Return the UTC time of the next scheduled automatic run."""
        with self._lock:
            return self._next_run_at

    def get_last_result(self) -> UpdateResult | None:
        """Return the result of the most recently completed update cycle."""
        with self._lock:
            return self._last_result

    def _loop(self) -> None:
        """Main background loop: polls both the schedule and manual
        trigger requests until :meth:`stop` is called.
        """
        while not self._stop_event.is_set():
            if self._trigger_event.is_set():
                self._trigger_event.clear()
                self._run_update(force=self._pending_force)
            else:
                self._scheduler.run_pending()

            self._update_next_run()
            self._stop_event.wait(_POLL_INTERVAL_SECONDS)

    def _run_scheduled_update(self) -> None:
        """Callback invoked by the ``schedule`` library on its own cadence."""
        self._run_update(force=False)

    def _run_update(self, force: bool) -> None:
        """Execute the injected update callback and store its result."""
        try:
            result = self._update_callback(force)
        except Exception:  # noqa: BLE001 - scheduler must never die
            _logger.exception("Update callback raised unexpectedly.")
            return

        with self._lock:
            self._last_result = result

    def _update_next_run(self) -> None:
        """Refresh the cached "next run" time from the underlying
        ``schedule`` library state.
        """
        next_run = self._scheduler.next_run
        with self._lock:
            if next_run is not None:
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=timezone.utc)
                self._next_run_at = next_run
            else:
                self._next_run_at = None
