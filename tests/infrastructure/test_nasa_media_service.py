"""Tests for NASA, Webb, and Hubble photo sources."""

from __future__ import annotations

from pathlib import Path
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


def test_hubble_uses_same_flickr_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_client(monkeypatch)
    service = NASAMediaService()
    photos = service.get_hubble_photos(limit=1)

    assert len(photos) == 1
    assert photos[0].source == "hubble"
    assert photos[0].thumbnail_url.endswith("thumb.jpg")
