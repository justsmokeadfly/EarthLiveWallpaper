"""Thread-safe progress reporting for an in-flight update cycle.

The update use case runs on the scheduler's background thread and writes
progress here as it moves through stages (checking, downloading,
assembling, applying, pruning). The UI polls it from the Tk main thread
to drive a progress bar and status label, without the application layer
needing to know anything about Tkinter/CustomTkinter.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum


class ProgressStage(str, Enum):
    """Stages an update cycle passes through, in order."""

    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    ASSEMBLING = "assembling"
    APPLYING = "applying"
    PRUNING = "pruning"


@dataclass(frozen=True)
class ProgressSnapshot:
    """An immutable point-in-time read of the current progress state.

    Attributes:
        stage: The current stage of the update cycle.
        current: Progress within the current stage (e.g. tiles
            downloaded so far). Meaningless (0) for stages without a
            concrete count, such as assembling or applying.
        total: Total units expected for the current stage. Zero means
            "indeterminate" - the stage has no meaningful progress count.
    """

    stage: ProgressStage
    current: int
    total: int

    @property
    def fraction(self) -> float:
        """Progress as a 0.0-1.0 fraction, or 0.0 if indeterminate."""
        if self.total <= 0:
            return 0.0
        return max(0.0, min(1.0, self.current / self.total))

    @property
    def is_determinate(self) -> bool:
        """Whether this stage has a meaningful current/total count."""
        return self.total > 0


class ProgressTracker:
    """Holds the current progress of an in-flight update cycle.

    A single instance is shared (via dependency injection) between the
    :class:`UpdateWallpaperUseCase`, which calls :meth:`set` as it works,
    and the UI, which calls :meth:`get` on a polling timer.
    """

    def __init__(self) -> None:
        """Initialize the tracker in the idle state."""
        self._lock = threading.Lock()
        self._stage = ProgressStage.IDLE
        self._current = 0
        self._total = 0

    def set(self, stage: ProgressStage, current: int = 0, total: int = 0) -> None:
        """Update the current progress state.

        Args:
            stage: The stage now in progress.
            current: Progress within this stage, if applicable.
            total: Total units expected for this stage, or 0 if the
                stage has no meaningful count (indeterminate).
        """
        with self._lock:
            self._stage = stage
            self._current = current
            self._total = total

    def reset(self) -> None:
        """Return the tracker to the idle state (no update in progress)."""
        self.set(ProgressStage.IDLE, 0, 0)

    def get(self) -> ProgressSnapshot:
        """Return an immutable snapshot of the current progress state."""
        with self._lock:
            return ProgressSnapshot(self._stage, self._current, self._total)
