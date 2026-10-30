"""NASA APOD retrieval, video fallback and download tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest

from infrastructure.nasa.nasa_media_service import NASAMediaService, NASAPhoto


def test_apod_rate_limit_gives_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "rate limit"})

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()

    with pytest.raises(RuntimeError, match="rate limit"):
        service.get_apod()


def test_apod_returns_todays_image(monkeypatch: pytest.MonkeyPatch) -> None:
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        assert "date" not in request.url.params
        return httpx.Response(
            200,
            json={
                "media_type": "image",
                "url": "https://apod.nasa.gov/apod/today.jpg",
                "title": "Today's Sky",
                "explanation": "A lovely nebula.",
                "date": "2026-08-31",
            },
        )

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()
    photo = service.get_apod()

    assert photo.image_url.endswith("today.jpg")
    assert photo.title == "Today's Sky"


def test_apod_falls_back_when_today_is_a_video(monkeypatch: pytest.MonkeyPatch) -> None:
    real_client = httpx.Client
    calls: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_date = request.url.params.get("date")
        calls.append(requested_date)
        if requested_date is None:
            return httpx.Response(
                200,
                json={"media_type": "video", "url": "https://youtube.com/watch?v=x"},
            )
        return httpx.Response(
            200,
            json={
                "media_type": "image",
                "url": "https://apod.nasa.gov/apod/yesterday.jpg",
                "title": "Yesterday's Sky",
                "date": requested_date,
            },
        )

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()
    photo = service.get_apod()

    assert photo.image_url.endswith("yesterday.jpg")
    assert calls[0] is None
    assert calls[1] is not None


def test_apod_raises_if_no_image_found_within_lookback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"media_type": "video", "url": "https://youtube.com/watch?v=x"}
        )

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()

    with pytest.raises(RuntimeError, match="did not return an image"):
        service.get_apod()

def test_download_preserves_existing_file_on_http_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    @contextmanager
    def fake_stream(*args: Any, **kwargs: Any) -> Iterator[httpx.Response]:
        with (
            httpx.Client(
                transport=httpx.MockTransport(lambda request: httpx.Response(500))
            ) as client,
            client.stream(*args, **kwargs) as response,
        ):
            yield response
    monkeypatch.setattr(httpx, "stream", fake_stream)
    target = tmp_path / "image.jpg"
    target.write_bytes(b"existing wall")
    photo = NASAPhoto(
        title="test", description_en="", image_url="https://apod.nasa.gov/test.jpg",
        source_url="",
    )
    with pytest.raises(httpx.HTTPStatusError):
        NASAMediaService().download(photo, target)
    assert target.read_bytes() == b"existing wall"
    assert sorted(tmp_path.iterdir()) == [target]

def test_successful_download_replaces_file_atomically(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    @contextmanager
    def fake_stream(*args: Any, **kwargs: Any) -> Iterator[httpx.Response]:
        with (
            httpx.Client(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, content=b"new image", headers={"content-length": "9"})
                )
            ) as client,
            client.stream(*args, **kwargs) as response,
        ):
            yield response

    monkeypatch.setattr(httpx, "stream", fake_stream)
    target = tmp_path / "image.jpg"
    target.write_bytes(b"previous image")
    photo = NASAPhoto(
        title="test", description_en="", image_url="https://apod.nasa.gov/test.jpg",
        source_url="",
    )
    progress: list[tuple[int, int]] = []
    NASAMediaService().download(
        photo, target, lambda current, total: progress.append((current, total))
    )
    assert target.read_bytes() == b"new image"
    assert sorted(tmp_path.iterdir()) == [target]
    assert progress == [(9, 9)]
