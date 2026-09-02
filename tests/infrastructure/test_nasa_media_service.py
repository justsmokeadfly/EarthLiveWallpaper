"""Tests for NASA, Webb, and Hubble photo sources."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from infrastructure.nasa.nasa_media_service import NASAMediaService

_FLICKR_XML = b"""
<rss xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <item>
      <title>Test Space Image</title>
      <description>&lt;p&gt;A beautiful galaxy.&lt;/p&gt;</description>
      <link>https://www.flickr.com/photos/example/1/</link>
      <media:content url="https://live.staticflickr.com/original.jpg" />
      <media:thumbnail url="https://live.staticflickr.com/thumb.jpg" />
    </item>
  </channel>
</rss>
"""


def _mock_client(monkeypatch: pytest.MonkeyPatch) -> None:
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_FLICKR_XML)

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)


def test_webb_uses_flickr_thumbnail_and_source(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(monkeypatch)
    service = NASAMediaService()
    photos = service.get_webb_photos(limit=1)

    assert len(photos) == 1
    assert photos[0].source == "webb"
    assert photos[0].image_url.endswith("original.jpg")
    assert photos[0].thumbnail_url.endswith("thumb.jpg")
    assert photos[0].source_url.endswith("/1/")
    assert photos[0].width == 0
    assert photos[0].height == 0


def test_flickr_feed_parses_width_and_height(monkeypatch: pytest.MonkeyPatch) -> None:
    xml_with_dims = b"""
<rss xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <item>
      <title>Test Space Image</title>
      <description>A beautiful galaxy.</description>
      <link>https://www.flickr.com/photos/example/1/</link>
      <media:content url="https://live.staticflickr.com/original.jpg" width="4096" height="2731" />
      <media:thumbnail url="https://live.staticflickr.com/thumb.jpg" />
    </item>
  </channel>
</rss>
"""
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=xml_with_dims)

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()
    photos = service.get_webb_photos(limit=1)

    assert photos[0].width == 4096
    assert photos[0].height == 2731


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


def test_flickr_photo_upgraded_to_largest_available_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    xml_realistic_url = b"""
<rss xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <item>
      <title>Test Space Image</title>
      <description>A beautiful galaxy.</description>
      <link>https://www.flickr.com/photos/example/1/</link>
      <media:content url="https://live.staticflickr.com/65535/123456789_abc123def0.jpg" width="800" height="600" />
      <media:thumbnail url="https://live.staticflickr.com/65535/123456789_abc123def0_m.jpg" />
    </item>
  </channel>
</rss>
"""
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, content=xml_realistic_url)
        # Simulate only the "4k" derived size existing for this photo.
        if request.url.path.endswith("_4k.jpg"):
            return httpx.Response(200)
        return httpx.Response(404)

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()
    photos = service.get_webb_photos(limit=1)

    assert photos[0].image_url.endswith("_4k.jpg")
    assert photos[0].width == 4096
    assert photos[0].height == 3072
    # The small preview thumbnail is left untouched for fast loading.
    assert photos[0].thumbnail_url.endswith("_m.jpg")


def test_flickr_photo_keeps_medium_url_when_no_larger_size_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    xml_realistic_url = b"""
<rss xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <item>
      <title>Test Space Image</title>
      <description>A beautiful galaxy.</description>
      <link>https://www.flickr.com/photos/example/1/</link>
      <media:content url="https://live.staticflickr.com/65535/123456789_abc123def0.jpg" width="800" height="600" />
    </item>
  </channel>
</rss>
"""
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, content=xml_realistic_url)
        return httpx.Response(404)

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", make_client)
    service = NASAMediaService()
    photos = service.get_webb_photos(limit=1)

    assert photos[0].image_url.endswith("123456789_abc123def0.jpg")
    assert photos[0].width == 800
    assert photos[0].height == 600


def test_hubble_uses_same_flickr_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(monkeypatch)
    service = NASAMediaService()
    photos = service.get_hubble_photos(limit=1)

    assert len(photos) == 1
    assert photos[0].source == "hubble"
    assert photos[0].thumbnail_url.endswith("thumb.jpg")


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
