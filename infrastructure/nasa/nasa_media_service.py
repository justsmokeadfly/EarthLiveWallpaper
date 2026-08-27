"""NASA APOD and James Webb Flickr photo sources."""

from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx
from defusedxml import ElementTree as ET

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
WEBB_FEED_URL = (
    "https://www.flickr.com/services/feeds/photoset.gne"
    "?set=72177720331299130&nsid=nasawebbtelescope&lang=en-us&format=rss_200"
)


@dataclass(frozen=True)
class NASAPhoto:
    title: str
    description_en: str
    image_url: str
    source_url: str
    date: str = ""
    copyright: str = ""


class NASAMediaService:
    """Fetch NASA APOD and the official NASA Webb Flickr album."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    def get_apod(self) -> NASAPhoto:
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.get(NASA_APOD_URL, params={"api_key": "DEMO_KEY"})
            response.raise_for_status()
            data = response.json()
        if data.get("media_type") != "image" or not data.get("url"):
            raise RuntimeError("NASA APOD did not return an image.")
        return NASAPhoto(
            title=str(data.get("title", "NASA Picture of the Day")),
            description_en=str(data.get("explanation", "")),
            image_url=str(data.get("hdurl") or data["url"]),
            source_url=str(data.get("url", "")),
            date=str(data.get("date", "")),
            copyright=str(data.get("copyright", "")),
        )

    def get_webb_photos(self, limit: int = 24) -> list[NASAPhoto]:
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.get(WEBB_FEED_URL)
            response.raise_for_status()
        root = ET.fromstring(response.content)
        photos: list[NASAPhoto] = []
        ns = {"media": "http://search.yahoo.com/mrss/"}
        for item in root.findall(".//item")[:limit]:
            title = html.unescape((item.findtext("title") or "").strip())
            description = html.unescape(_strip_html(item.findtext("description") or ""))
            media = item.find("media:content", ns)
            image_url = media.attrib.get("url", "") if media is not None else ""
            source = item.findtext("link") or image_url
            if not title or not image_url:
                continue
            photos.append(NASAPhoto(title, description, image_url, source))
        return photos

    def download(
        self,
        photo: NASAPhoto,
        destination: Path,
        progress: Callable[[int, int], None] | None = None,
    ) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream(
            "GET", photo.image_url, timeout=self._timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", "0") or 0)
            current = 0
            with destination.open("wb") as output:
                for chunk in response.iter_bytes(1024 * 64):
                    output.write(chunk)
                    current += len(chunk)
                    if progress is not None:
                        progress(current, total)
        return destination

    def translate_to_russian(self, text: str) -> str:
        """Translate a short description using MyMemory, with safe fallback."""
        if not text:
            return ""
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": text[:4500], "langpair": "en|ru"},
                )
                response.raise_for_status()
                translated = response.json().get("responseData", {}).get("translatedText", "")
                return str(translated or text)
        except (httpx.HTTPError, ValueError, TypeError):
            return text


def _strip_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()
