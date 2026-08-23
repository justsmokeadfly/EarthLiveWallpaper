"""Unit tests for AppController.delete_from_history.

These tests construct a bare AppController instance (bypassing __init__,
which wires up config loading, the scheduler, and several infrastructure
singletons that aren't relevant here) and inject only the one
collaborator delete_from_history actually touches: the state repository.
This mirrors how the rest of the suite favors small, focused fakes over
heavyweight object graphs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

if sys.platform != "win32":
    pytest.skip(
        "application.app_controller imports infrastructure.system.autostart, "
        "which requires the stdlib winreg module (Windows-only).",
        allow_module_level=True,
    )

from application.app_controller import AppController
from domain.entities import AppState
from domain.interfaces import StateRepository


class FakeStateRepository(StateRepository):
    """In-memory StateRepository fake with an optional counter."""

    def __init__(self, initial_state: AppState) -> None:
        self._state = initial_state
        self.save_count = 0

    def load(self) -> AppState:
        return self._state

    def save(self, state: AppState) -> None:
        self._state = state
        self.save_count += 1


def _make_bare_controller(state_repository: StateRepository) -> AppController:
    """Build an AppController with only `_state_repository` wired up,
    skipping the full constructor (config loading, scheduler, cache
    manager, autostart manager, etc.) that delete_from_history never
    touches.
    """
    controller = AppController.__new__(AppController)
    controller._state_repository = state_repository  # type: ignore[attr-defined]
    return controller


class TestDeleteFromHistory:
    """Tests for AppController.delete_from_history."""

    def test_deletes_file_and_removes_history_entry(self, tmp_path: Path) -> None:
        wallpaper = tmp_path / "earth_20260101_0000.png"
        wallpaper.write_bytes(b"fake png bytes")
        state = AppState(history=[str(wallpaper), "other.png"])
        repo = FakeStateRepository(state)
        controller = _make_bare_controller(repo)

        result = controller.delete_from_history(wallpaper)

        assert result is True
        assert not wallpaper.exists()
        assert str(wallpaper) not in repo.load().history
        assert "other.png" in repo.load().history
        assert repo.save_count == 1

    def test_missing_file_still_cleans_up_stale_history_entry(self, tmp_path: Path) -> None:
        wallpaper = tmp_path / "already_gone.png"
        state = AppState(history=[str(wallpaper)])
        repo = FakeStateRepository(state)
        controller = _make_bare_controller(repo)

        result = controller.delete_from_history(wallpaper)

        assert result is True
        assert repo.load().history == []

    def test_unlink_failure_leaves_history_untouched(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wallpaper = tmp_path / "locked.png"
        wallpaper.write_bytes(b"fake png bytes")
        state = AppState(history=[str(wallpaper)])
        repo = FakeStateRepository(state)
        controller = _make_bare_controller(repo)

        def _raise_os_error(self: Path) -> None:
            raise OSError("file is in use")

        monkeypatch.setattr(Path, "unlink", _raise_os_error)

        result = controller.delete_from_history(wallpaper)

        assert result is False
        assert str(wallpaper) in repo.load().history
        assert repo.save_count == 0

    def test_no_op_history_entry_still_reports_success_without_saving(
        self, tmp_path: Path
    ) -> None:
        """Deleting a file that was never tracked in history at all
        should still succeed (the file is gone) without triggering an
        unnecessary state save.
        """
        wallpaper = tmp_path / "untracked.png"
        wallpaper.write_bytes(b"fake png bytes")
        state = AppState(history=[])
        repo = FakeStateRepository(state)
        controller = _make_bare_controller(repo)

        result = controller.delete_from_history(wallpaper)

        assert result is True
        assert not wallpaper.exists()
        assert repo.save_count == 0
