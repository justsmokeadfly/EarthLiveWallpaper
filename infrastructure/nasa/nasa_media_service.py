"""NASA APOD, James Webb, and Hubble photo sources."""

from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

import httpx
from defusedxml import ElementTree as ET

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
_APOD_MAX_LOOKBACK_DAYS = 3
# Flickr's RSS feed always serves the "Medium" size in <media:content>, never
# the original. Flickr's CDN serves other sizes of the same photo by
# swapping the size suffix in the URL (same id/secret/server) - these are
# derived sizes generated from the true original, so probing for the
# largest one that exists gets us very close to "Original" without needing
# a separate Flickr API key (which would require its own signup).
_FLICKR_URL_RE = re.compile(
    r"^(?P<base>https?://[^/]+/[^/]+/\d+_[0-9a-fA-F]+)(?:_\w+)?\.(?P<ext>jpg|jpeg|png|gif)(?:\?.*)?$",
    re.IGNORECASE,
)
_FLICKR_SIZE_SUFFIXES: tuple[tuple[str, int], ...] = (
    ("6k", 6144),
    ("5k", 5120),
    ("4k", 4096),
    ("3k", 3072),
    ("k", 2048),
    ("h", 1600),
    ("b", 1024),
)
# Only used by the explicit size picker, not the automatic silent upgrade:
# "Original" (max_dim=0) has an unknown true resolution without downloading
# it, which would make the automatic upgrade's resolution label wrong.
_FLICKR_PICKER_SUFFIXES: tuple[tuple[str, int], ...] = (
    ("o", 0),
    *_FLICKR_SIZE_SUFFIXES,
)
WEBB_FEED_URL = (
    "https://api.flickr.com/services/feeds/photoset.gne"
    "?set=72177720331299130&nsid=50785054@N03&lang=en-us&format=rss_200"
)
WEBB_FEED_FALLBACK_URL = (
    "https://www.flickr.com/services/feeds/photoset.gne"
    "?set=72177720331299130&nsid=50785054@N03&lang=en-us&format=rss_200"
)
HUBBLE_FEED_URL = (
    "https://api.flickr.com/services/feeds/photoset.gne"
    "?set=72157667717916603&nsid=144614754@N02&lang=en-us&format=rss_200"
)
HUBBLE_FEED_FALLBACK_URL = (
    "https://www.flickr.com/services/feeds/photoset.gne"
    "?set=72157667717916603&nsid=144614754@N02&lang=en-us&format=rss_200"
)
_MYMEMORY_URL = "https://api.mymemory.translated.net/get"
_MYMEMORY_MAX_BYTES = 450
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class FlickrSize:
    """One selectable download size for a Flickr-hosted photo."""

    label: str
    width: int
    height: int
    url: str


_FLICKR_SIZE_NAMES: dict[str, str] = {
    "o": "Original",
    "6k": "XX-Large 6K",
    "5k": "XX-Large 5K",
    "4k": "X-Large 4K",
    "3k": "Large 3K",
    "k": "Large 2048",
    "h": "Large 1600",
    "b": "Large 1024",
}


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
    """Fetch NASA APOD plus official Webb and Hubble Flickr galleries."""

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

    def get_webb_photos(self, limit: int = 24) -> list[NASAPhoto]:
        return self._get_flickr_photos(
            (WEBB_FEED_URL, WEBB_FEED_FALLBACK_URL), "webb", limit
        )

    def get_hubble_photos(self, limit: int = 24) -> list[NASAPhoto]:
        return self._get_flickr_photos(
            (HUBBLE_FEED_URL, HUBBLE_FEED_FALLBACK_URL), "hubble", limit
        )

    def list_flickr_sizes(self, photo: NASAPhoto) -> list[FlickrSize]:
        """Return every download size actually available for a Flickr photo.

        Unlike the automatic upgrade applied when the photo list loads
        (which stops at the first, largest size it finds), this probes
        every known suffix so the user can see and pick from the same
        ladder of sizes Flickr's own "View all sizes" page shows.
        Largest first; always includes at least the current image_url.
        """
        match = _FLICKR_URL_RE.match(photo.image_url)
        if match is None:
            return [FlickrSize("Текущий размер", photo.width, photo.height, photo.image_url)]
        base, ext = match.group("base"), match.group("ext")
        base_width, base_height = photo.width, photo.height
        sizes: list[FlickrSize] = []
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            for suffix, max_dim in _FLICKR_PICKER_SUFFIXES:
                candidate = f"{base}_{suffix}.{ext}"
                if not _flickr_url_exists(client, candidate):
                    continue
                width, height = base_width, base_height
                if max_dim and width and height:
                    if width >= height:
                        width, height = max_dim, round(max_dim * height / width)
                    else:
                        width, height = round(max_dim * width / height), max_dim
                elif not max_dim:
                    width, height = 0, 0
                name = _FLICKR_SIZE_NAMES.get(suffix, suffix.upper())
                label = f"{name} ({width} × {height})" if width and height else name
                sizes.append(FlickrSize(label, width, height, candidate))
        medium_url = f"{base}.{ext}"
        medium_label = f"Medium ({base_width} × {base_height})" if base_width and base_height else "Medium"
        if not any(s.url == medium_url for s in sizes):
            sizes.append(FlickrSize(medium_label, base_width, base_height, medium_url))
        return sizes or [FlickrSize("Текущий размер", photo.width, photo.height, photo.image_url)]

    def _get_flickr_photos(
        self, feed_urls: tuple[str, str], source: str, limit: int
    ) -> list[NASAPhoto]:
        response_content: bytes | None = None
        last_error: Exception | None = None
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            for feed_url in feed_urls:
                try:
                    response = client.get(feed_url)
                    response.raise_for_status()
                    response_content = response.content
                    break
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = exc

        if response_content is None:
            raise RuntimeError(f"Failed to load Flickr {source} feed.") from last_error

        root = ET.fromstring(response_content)
        photos: list[NASAPhoto] = []
        ns = {"media": "http://search.yahoo.com/mrss/"}
        for item in root.findall(".//item")[:limit]:
            title = html.unescape((item.findtext("title") or "").strip())
            description = html.unescape(_strip_html(item.findtext("description") or ""))
            media = item.find("media:content", ns)
            thumbnail = item.find("media:thumbnail", ns)
            image_url = media.attrib.get("url", "") if media is not None else ""
            thumbnail_url = thumbnail.attrib.get("url", "") if thumbnail is not None else ""
            width = _parse_int(media.attrib.get("width")) if media is not None else 0
            height = _parse_int(media.attrib.get("height")) if media is not None else 0
            source_url = item.findtext("link") or image_url
            if not title or not image_url:
                continue
            photos.append(
                NASAPhoto(
                    title=title,
                    description_en=description,
                    image_url=image_url,
                    source_url=source_url,
                    thumbnail_url=thumbnail_url,
                    source=source,
                    width=width,
                    height=height,
                )
            )
        if not photos:
            raise RuntimeError(f"Flickr {source} feed contained no usable photos.")
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            photos = [_upgrade_flickr_photo(photo, client) for photo in photos]
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


def _flickr_url_exists(client: httpx.Client, url: str) -> bool:
    """Check if a Flickr-derived-size URL actually resolves.

    Flickr generates non-default sizes on demand at the origin; a HEAD
    request only reflects what's already cached at the CDN edge (Amazon
    CloudFront) and can wrongly report "not found" for a size that would
    succeed on a real GET (which forwards to origin and triggers
    generation). A "Range" header on the *first* request for a
    not-yet-generated size can also get rejected by that on-demand
    pipeline even though a plain GET would succeed, so this sends a
    normal GET - exactly what a browser tab would do - and closes the
    stream immediately after reading the status line, without ever
    reading the (potentially multi-megabyte) body.
    """
    try:
        with client.stream("GET", url) as response:
            return bool(response.status_code == 200)
    except httpx.HTTPError:
        return False


def _upgrade_flickr_photo(photo: NASAPhoto, client: httpx.Client) -> NASAPhoto:
    """Probe Flickr's CDN for the largest available derived size.

    Flickr's RSS feed always links the "Medium" size. The same photo is
    also served at larger sizes from the same URL with a different size
    suffix (e.g. ..._4k.jpg), generated by Flickr from the true original.
    Try the largest suffixes first and stop at the first one that exists.
    """
    match = _FLICKR_URL_RE.match(photo.image_url)
    if match is None:
        return photo
    base, ext = match.group("base"), match.group("ext")
    for suffix, max_dim in _FLICKR_SIZE_SUFFIXES:
        candidate = f"{base}_{suffix}.{ext}"
        if not _flickr_url_exists(client, candidate):
            continue
        width, height = photo.width, photo.height
        if width and height:
            if width >= height:
                width, height = max_dim, round(max_dim * height / width)
            else:
                width, height = round(max_dim * width / height), max_dim
        return replace(photo, image_url=candidate, width=width, height=height)
    return photo


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


def _parse_int(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def _strip_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()
