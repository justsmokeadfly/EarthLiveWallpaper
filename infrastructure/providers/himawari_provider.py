"""Himawari-8/9 image provider implementation.

Talks to NICT's public Himawari real-time image service
(https://himawari8.nict.go.jp/) to determine the latest available
full-disk image timestamp and to build the tile URL grid for a given
resolution. Encodes every Himawari-specific quirk (URL scheme, timestamp
rounding to 10-minute intervals, latest.json format) so that nothing
outside this module needs to know about them.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from domain.entities import SatelliteImage, TileSpec
from domain.enums import GridSize
from domain.interfaces import ImageProvider
from logger import get_logger

_logger = get_logger(__name__)

_LATEST_JSON_URL = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json"
_TILE_URL_TEMPLATE = (
    "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/{grid_dim}d/{tile_px}/"
    "{year:04d}/{month:02d}/{day:02d}/{hour:02d}{minute:02d}{second:02d}_{col}_{row}.png"
)

# Himawari serves images on a 10-minute cadence.
_INTERVAL_MINUTES = 10

# Pixel size of each individual tile, as served by NICT for every grid size.
_TILE_PIXEL_SIZE = 550

_HTTP_TIMEOUT_SECONDS = 10.0


class HimawariProvider(ImageProvider):
    """:class:`ImageProvider` implementation for the Himawari satellite."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        """Initialize the provider.

        Args:
            http_client: Optional pre-configured httpx client, primarily
                for testing. If omitted, a client is created per-call with
                a sane timeout.
        """
        self._http_client = http_client

    @property
    def name(self) -> str:
        """Unique identifier for this provider."""
        return "himawari"

    @property
    def supported_grid_sizes(self) -> tuple[GridSize, ...]:
        """All grid sizes NICT serves for the Himawari D531106 dataset."""
        return (
            GridSize.GRID_2X2,
            GridSize.GRID_4X4,
            GridSize.GRID_8X8,
            GridSize.GRID_16X16,
        )

    def get_latest_available_timestamp(self) -> datetime | None:
        """Fetch and parse NICT's ``latest.json`` to determine the newest
        available image timestamp.

        Returns:
            The UTC timestamp of the latest image, rounded down to the
            nearest 10-minute interval, or ``None`` if the request failed
            or the response could not be parsed.
        """
        try:
            client = self._http_client or httpx.Client(timeout=_HTTP_TIMEOUT_SECONDS)
            owns_client = self._http_client is None
            try:
                response = client.get(_LATEST_JSON_URL)
                response.raise_for_status()
                payload = response.json()
            finally:
                if owns_client:
                    client.close()
        except (httpx.HTTPError, ValueError) as exc:
            _logger.warning("Failed to fetch Himawari latest.json: %s", exc)
            return None

        raw_date = payload.get("date") if isinstance(payload, dict) else None
        if not raw_date:
            _logger.warning("Himawari latest.json missing 'date' field: %r", payload)
            return None

        try:
            # NICT format: "YYYY-MM-DD HH:MM:SS"
            naive = datetime.strptime(str(raw_date), "%Y-%m-%d %H:%M:%S")
            return naive.replace(tzinfo=UTC)
        except ValueError:
            _logger.warning("Could not parse Himawari timestamp: %r", raw_date)
            return None

    def build_image_request(
        self, timestamp: datetime, grid_size: GridSize
    ) -> SatelliteImage:
        """Build the full tile list for the given timestamp and grid size.

        The timestamp is rounded down to the nearest 10-minute boundary,
        matching Himawari's actual publishing cadence, before URLs are
        constructed.

        Args:
            timestamp: Desired UTC timestamp (need not be pre-rounded).
            grid_size: Desired tile grid resolution.

        Returns:
            A SatelliteImage with every TileSpec populated.
        """
        rounded = self._round_down_to_interval(timestamp)
        dim = grid_size.dimension

        tiles: list[TileSpec] = []
        for row in range(dim):
            for col in range(dim):
                url = _TILE_URL_TEMPLATE.format(
                    grid_dim=dim,
                    tile_px=_TILE_PIXEL_SIZE,
                    year=rounded.year,
                    month=rounded.month,
                    day=rounded.day,
                    hour=rounded.hour,
                    minute=rounded.minute,
                    second=rounded.second,
                    col=col,
                    row=row,
                )
                cache_key = (
                    f"himawari_{grid_size.value}_"
                    f"{rounded.strftime('%Y%m%d_%H%M%S')}_{col}_{row}.png"
                )
                tiles.append(TileSpec(url=url, column=col, row=row, cache_key=cache_key))

        return SatelliteImage(
            provider_name=self.name,
            timestamp=rounded,
            grid_size=grid_size,
            tiles=tuple(tiles),
        )

    @staticmethod
    def _round_down_to_interval(timestamp: datetime) -> datetime:
        """Round a timestamp down to the nearest 10-minute boundary (UTC)."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        else:
            timestamp = timestamp.astimezone(UTC)

        discard_minutes = timestamp.minute % _INTERVAL_MINUTES
        rounded = timestamp - timedelta(
            minutes=discard_minutes,
            seconds=timestamp.second,
            microseconds=timestamp.microsecond,
        )
        return rounded
