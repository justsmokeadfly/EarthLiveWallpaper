"""Persistent favorites for NASA and James Webb photos."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


class FavoritesRepository:
    """Store favorite photo source URLs in a small local JSON file."""

    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "nasa_favorites.json"

    def list_favorites(self) -> set[str]:
        if not self._path.exists():
            return set()
        try:
            raw: Any = orjson.loads(self._path.read_bytes())
        except (OSError, orjson.JSONDecodeError):
            return set()
        if not isinstance(raw, list):
            return set()
        return {str(value) for value in raw if isinstance(value, str) and value}

    def is_favorite(self, source_url: str) -> bool:
        return source_url in self.list_favorites()

    def toggle(self, source_url: str) -> bool:
        favorites = self.list_favorites()
        if source_url in favorites:
            favorites.remove(source_url)
            result = False
        else:
            favorites.add(source_url)
            result = True
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_bytes(orjson.dumps(sorted(favorites), option=orjson.OPT_INDENT_2))
        return result
