"""JSON-file-backed implementation of :class:`StateRepository`.

State is persisted independently of the user config file (see
``config.py``) because state is machine-managed data (timestamps, hashes,
history) whereas config is user-editable preferences. Writes are atomic
(temp file + ``os.replace``) so a crash or power loss mid-write cannot
corrupt the state file, and all access is guarded by a lock so the UI
thread and the scheduler thread never race.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import orjson

from domain.entities import AppState
from domain.enums import UpdateOutcome
from domain.interfaces import StateRepository
from logger import get_logger

_logger = get_logger(__name__)


class JsonStateRepository(StateRepository):
    """Persists :class:`AppState` as a single JSON file on disk."""

    def __init__(self, state_file: Path) -> None:
        """Initialize the repository.

        Args:
            state_file: Full path to the JSON file used for storage.
        """
        self._state_file = state_file
        self._lock = threading.Lock()

    def load(self) -> AppState:
        """Load state from disk, returning a default AppState on any
        failure (missing file, corrupt JSON, unexpected schema)."""
        with self._lock:
            if not self._state_file.exists():
                _logger.info("No existing state file; starting fresh.")
                return AppState()

            try:
                raw_bytes = self._state_file.read_bytes()
                raw = orjson.loads(raw_bytes)
                if not isinstance(raw, dict):
                    raise ValueError("State file does not contain a JSON object.")
                return self._deserialize(raw)
            except Exception:
                _logger.exception(
                    "Failed to read state file at %s; starting fresh.",
                    self._state_file,
                )
                return AppState()

    def save(self, state: AppState) -> None:
        """Persist state to disk atomically."""
        with self._lock:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = self._state_file.with_suffix(".tmp")
            try:
                payload = orjson.dumps(
                    self._serialize(state), option=orjson.OPT_INDENT_2
                )
                tmp_file.write_bytes(payload)
                os.replace(tmp_file, self._state_file)
            except Exception:
                _logger.exception("Failed to save state to %s.", self._state_file)
                if tmp_file.exists():
                    try:
                        tmp_file.unlink()
                    except OSError:
                        pass

    @staticmethod
    def _serialize(state: AppState) -> dict[str, Any]:
        return {
            "last_timestamp": (
                state.last_timestamp.isoformat() if state.last_timestamp else None
            ),
            "last_content_hash": state.last_content_hash,
            "last_update_at": (
                state.last_update_at.isoformat() if state.last_update_at else None
            ),
            "last_successful_update_at": (
                state.last_successful_update_at.isoformat()
                if state.last_successful_update_at
                else None
            ),
            "last_outcome": state.last_outcome.value if state.last_outcome else None,
            "history": list(state.history),
            "total_updates_applied": state.total_updates_applied,
        }

    @staticmethod
    def _deserialize(raw: dict[str, Any]) -> AppState:
        def _parse_dt(value: Any) -> datetime | None:
            if not value:
                return None
            try:
                return datetime.fromisoformat(str(value))
            except ValueError:
                return None

        outcome_raw = raw.get("last_outcome")
        outcome: UpdateOutcome | None = None
        if outcome_raw:
            try:
                outcome = UpdateOutcome(outcome_raw)
            except ValueError:
                outcome = None

        history_raw = raw.get("history", [])
        history = [str(item) for item in history_raw] if isinstance(history_raw, list) else []

        return AppState(
            last_timestamp=_parse_dt(raw.get("last_timestamp")),
            last_content_hash=raw.get("last_content_hash"),
            last_update_at=_parse_dt(raw.get("last_update_at")),
            last_successful_update_at=_parse_dt(raw.get("last_successful_update_at")),
            last_outcome=outcome,
            history=history,
            total_updates_applied=int(raw.get("total_updates_applied", 0)),
        )
