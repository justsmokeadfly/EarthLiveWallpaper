"""Tests for NASA, Webb, and Hubble photo sources."""

from __future__ import annotations

import httpx

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


def test_webb_uses_flickr_thumbnail_and_source(monkeypatch) -> None:
    service = NASAMediaService()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_FLICKR_XML)

    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: httpx.Client(transport=httpx.MockTransport(handler)))
    photos = service.get_webb_photos(limit=1)

    assert len(photos) == 1
    assert photos[0].source == "webb"
    assert photos[0].image_url.endswith("original.jpg")
    assert photos[0].thumbnail_url.endswith("thumb.jpg")
    assert photos[0].source_url.endswith("/1/")


def test_hubble_uses_same_flickr_parser(monkeypatch) -> None:
    service = NASAMediaService()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_FLICKR_XML)

    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: httpx.Client(transport=httpx.MockTransport(handler)))
    photos = service.get_hubble_photos(limit=1)

    assert len(photos) == 1
    assert photos[0].source == "hubble"
    assert photos[0].thumbnail_url.endswith("thumb.jpg")
