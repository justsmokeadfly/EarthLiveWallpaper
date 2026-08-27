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
_MYMEMORY_URL = "https://api.mymemory.translated.net/get"
_MYMEMORY_MAX_BYTES = 450
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class NASAPhoto:
    title: str
    description_en: str
    image_url: str
    source_url: str
    date: str = ""
    copyright: str = ""
    thumbnail_url: str = ""


class NASAMediaService:
    """Fetch NASA APOD and the official NASA Webb Flickr album."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._translation_cache: dict[str, str] = {}

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
            thumbnail = item.find("media:thumbnail", ns)
            image_url = media.attrib.get("url", "") if media is not None else ""
            thumbnail_url = thumbnail.attrib.get("url", "") if thumbnail is not None else ""
            source = item.findtext("link") or image_url
            if not title or not image_url:
                continue
            photos.append(
                NASAPhoto(
                    title=title,
                    description_en=description,
                    image_url=image_url,
                    source_url=source,
                    thumbnail_url=thumbnail_url,
                )
            )
        return photos

    def download(
        self,
        photo: NASAPhoto,
        destination: Path,
        progress: ProgressCallback | None = None,
        image_url: str | None = None,
    ) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = image_url or photo.image_url
        with httpx.stream(
            "GET", url, timeout=self._timeout, follow_redirects=True
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
        """Translate English text to Russian in API-safe chunks with caching."""
        normalized = text.strip()
        if not normalized:
            return ""
        cached = self._translation_cache.get(normalized)
        if cached is not None:
            return cached

        chunks = _split_for_translation(normalized, _MYMEMORY_MAX_BYTES)
        translated_chunks: list[str] = []
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                for chunk in chunks:
                    response = client.get(
                        _MYMEMORY_URL,
                        params={
                            "q": chunk,
                            "langpair": "en|ru",
                            "mt": "1",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    translated = payload.get("responseData", {}).get("translatedText", "")
                    if not translated:
                        raise ValueError("MyMemory returned an empty translation.")
                    translated_chunks.append(str(translated).strip())
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            return normalized

        result = " ".join(translated_chunks).strip() or normalized
        self._translation_cache[normalized] = result
        return result


def _split_for_translation(text: str, max_bytes: int) -> list[str]:
    """Split text into UTF-8 chunks below the translation API byte limit."""
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = word
        if len(current.encode("utf-8")) > max_bytes:
            encoded = current.encode("utf-8")
            for start in range(0, len(encoded), max_bytes):
                piece = encoded[start : start + max_bytes].decode("utf-8", errors="ignore").strip()
                if piece:
                    chunks.append(piece)
            current = ""
    if current:
        chunks.append(current)
    return chunks


def _strip_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()
