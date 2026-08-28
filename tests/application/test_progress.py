"""Unit tests for application.progress."""

from __future__ import annotations

from application.progress import ProgressSnapshot, ProgressStage, ProgressTracker


class TestProgressSnapshot:
    """Tests for the ProgressSnapshot value object."""

    def test_fraction_computes_ratio(self) -> None:
        snapshot = ProgressSnapshot(ProgressStage.DOWNLOADING, current=3, total=10)
        assert snapshot.fraction == 0.3

    def test_fraction_is_zero_when_total_is_zero(self) -> None:
        snapshot = ProgressSnapshot(ProgressStage.CHECKING, current=0, total=0)
        assert snapshot.fraction == 0.0

    def test_fraction_is_clamped_to_one(self) -> None:
        snapshot = ProgressSnapshot(ProgressStage.DOWNLOADING, current=15, total=10)
        assert snapshot.fraction == 1.0

    def test_is_determinate_true_when_total_positive(self) -> None:
        snapshot = ProgressSnapshot(ProgressStage.DOWNLOADING, current=1, total=4)
        assert snapshot.is_determinate is True

    def test_is_determinate_false_when_total_zero(self) -> None:
        snapshot = ProgressSnapshot(ProgressStage.ASSEMBLING, current=0, total=0)
        assert snapshot.is_determinate is False


class TestProgressTracker:
    """Tests for the thread-safe ProgressTracker."""

    def test_starts_idle(self) -> None:
        tracker = ProgressTracker()
        snapshot = tracker.get()
        assert snapshot.stage == ProgressStage.IDLE
        assert snapshot.current == 0
        assert snapshot.total == 0

    def test_set_updates_state(self) -> None:
        tracker = ProgressTracker()
        tracker.set(ProgressStage.DOWNLOADING, current=2, total=8)
        snapshot = tracker.get()
        assert snapshot.stage == ProgressStage.DOWNLOADING
        assert snapshot.current == 2
        assert snapshot.total == 8

    def test_reset_returns_to_idle(self) -> None:
        tracker = ProgressTracker()
        tracker.set(ProgressStage.APPLYING)
        tracker.reset()
        snapshot = tracker.get()
        assert snapshot.stage == ProgressStage.IDLE
        assert snapshot.current == 0
        assert snapshot.total == 0

    def test_set_without_counts_defaults_to_zero(self) -> None:
        tracker = ProgressTracker()
        tracker.set(ProgressStage.ASSEMBLING)
        snapshot = tracker.get()
        assert snapshot.current == 0
        assert snapshot.total == 0
