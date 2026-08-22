"""Unit tests for JsonStateRepository."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from domain.entities import AppState
from domain.enums import UpdateOutcome
from infrastructure.persistence.json_state_repository import JsonStateRepository


class TestJsonStateRepository:
    """Tests for load()/save() round-tripping and failure handling."""

    def test_load_returns_default_when_file_missing(self, tmp_path: Path) -> None:
        repo = JsonStateRepository(tmp_path / "state.json")

        state = repo.load()

        assert state.last_timestamp is None
        assert state.total_updates_applied == 0
        assert state.history == []

    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        repo = JsonStateRepository(tmp_path / "state.json")
        original = AppState(
            last_timestamp=datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC),
            last_content_hash="abc123",
            last_update_at=datetime(2026, 7, 29, 12, 1, 0, tzinfo=UTC),
            last_successful_update_at=datetime(2026, 7, 29, 12, 1, 0, tzinfo=UTC),
            last_outcome=UpdateOutcome.SUCCESS,
            history=["a.png", "b.png"],
            total_updates_applied=5,
        )

        repo.save(original)
        loaded = repo.load()

        assert loaded.last_timestamp == original.last_timestamp
        assert loaded.last_content_hash == original.last_content_hash
        assert loaded.last_outcome == UpdateOutcome.SUCCESS
        assert loaded.history == ["a.png", "b.png"]
        assert loaded.total_updates_applied == 5

    def test_load_returns_default_on_corrupt_json(self, tmp_path: Path) -> None:
        state_file = tmp_path / "state.json"
        state_file.write_text("{not valid json", encoding="utf-8")
        repo = JsonStateRepository(state_file)

        state = repo.load()

        assert state.last_timestamp is None

    def test_save_is_atomic_no_partial_file_left(self, tmp_path: Path) -> None:
        state_file = tmp_path / "state.json"
        repo = JsonStateRepository(state_file)

        repo.save(AppState(total_updates_applied=1))

        assert state_file.exists()
        assert not state_file.with_suffix(".tmp").exists()
