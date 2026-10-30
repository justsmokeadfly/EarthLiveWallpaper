"""NASA Astronomy Picture of the Day (APOD) photo source."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx

from logger import get_logger

_logger = get_logger(__name__)
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
_APOD_MAX_LOOKBACK_DAYS = 3
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
    source: str = "nasa"
    width: int = 0
    height: int = 0


class NASAMediaService:
    """Fetch NASA APOD imagery and translate its descriptions."""

    def __init__(self, timeout: float = 30.0, api_key: str = "") -> None:
        self._timeout = timeout
        self._api_key = api_key.strip() or "DEMO_KEY"
        self._translation_cache: dict[str, str] = {}

    def set_api_key(self, api_key: str) -> None:
        """Update the NASA API key used for subsequent APOD requests."""
        self._api_key = api_key.strip() or "DEMO_KEY"

    def get_apod(self) -> NASAPhoto:
        """Fetch NASA's Astronomy Picture of the Day.

        NASA occasionally publishes a video instead of an image (e.g. launch
        footage). When that happens, step backwards day by day until a
        recent image is found instead of failing outright. Uses the shared
        NASA DEMO_KEY, which is rate-limited (30 requests/hour, 50/day per
        IP, shared by every app that uses it) - if that limit is hit, fail
        immediately with a clear explanation instead of burning the rest of
        the quota on further lookback attempts that would also be rejected.
        """
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            last_error: Exception | None = None
            for days_back in range(_APOD_MAX_LOOKBACK_DAYS + 1):
                params = {"api_key": self._api_key}
                if days_back > 0:
                    target_date = date.today() - timedelta(days=days_back)
                    params["date"] = target_date.isoformat()
                try:
                    response = client.get(NASA_APOD_URL, params=params)
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in (403, 429):
                        if self._api_key == "DEMO_KEY":
                            raise RuntimeError(
                                "NASA's shared DEMO_KEY hit its rate limit "
                                "(30 requests/hour, shared by everyone using it). "
                                "Wait a bit and try again, or get a free personal "
                                "key at https://api.nasa.gov/ for a much higher limit."
                            ) from exc
                        raise RuntimeError(
                            "Your personal NASA API key hit its rate limit "
                            "(1000 requests/hour). Wait a bit and try again."
                        ) from exc
                    last_error = exc
                    continue
                data = response.json()
                if data.get("media_type") == "image" and data.get("url"):
                    return NASAPhoto(
                        title=str(data.get("title", "NASA Picture of the Day")),
                        description_en=str(data.get("explanation", "")),
                        image_url=str(data.get("hdurl") or data["url"]),
                        source_url=str(data.get("url", "")),
                        date=str(data.get("date", "")),
                        copyright=str(data.get("copyright", "")),
                        source="nasa",
                    )
        raise RuntimeError("NASA APOD did not return an image.") from last_error

    def download(
        self,
        photo: NASAPhoto,
        destination: Path,
        progress: ProgressCallback | None = None,
        image_url: str | None = None,
    ) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = image_url or photo.image_url
        # A failed download must never destroy an existing wallpaper.
        with NamedTemporaryFile(
            dir=destination.parent, prefix=f".{destination.name}.", suffix=".part",
            delete=False,
        ) as temporary:
            temp_path = Path(temporary.name)
        try:
            with httpx.stream(
                "GET", url, timeout=self._timeout, follow_redirects=True
            ) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", "0") or 0)
                current = 0
                with temp_path.open("wb") as output:
                    for chunk in response.iter_bytes(1024 * 64):
                        output.write(chunk)
                        current += len(chunk)
                        if progress is not None:
                            progress(current, total)
            os.replace(temp_path, destination)
            return destination
        finally:
            temp_path.unlink(missing_ok=True)

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
                        params={"q": chunk, "langpair": "en|ru", "mt": "1"},
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
