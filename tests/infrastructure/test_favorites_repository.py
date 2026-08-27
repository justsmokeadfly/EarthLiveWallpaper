"""Tests for persistent NASA and James Webb favorites."""
from __future__ import annotations

from pathlib import Path

from infrastructure.nasa.favorites_repository import FavoritesRepository


def test_toggle_favorite_persists(tmp_path: Path) -> None:
    repository = FavoritesRepository(tmp_path)
    url = "https://example.com/photo.jpg"

    assert repository.list_favorites() == set()
    assert repository.toggle(url) is True
    assert repository.is_favorite(url) is True
    assert FavoritesRepository(tmp_path).is_favorite(url) is True

    assert repository.toggle(url) is False
    assert repository.list_favorites() == set()


def test_invalid_file_falls_back_to_empty(tmp_path: Path) -> None:
    path = tmp_path / "nasa_favorites.json"
    path.write_text("not json", encoding="utf-8")

    assert FavoritesRepository(tmp_path).list_favorites() == set()
