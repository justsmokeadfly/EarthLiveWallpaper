"""Unit tests for HimawariProvider."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from domain.enums import GridSize
from infrastructure.providers.himawari_provider import HimawariProvider


def _make_mock_client(json_payload: dict | None, raise_error: bool = False) -> httpx.Client:
    """Build an httpx.Client backed by a MockTransport for testing."""

    def handler(request: httpx.Request) -> httpx.Response:
        if raise_error:
            raise httpx.ConnectError("simulated connection failure", request=request)
        return httpx.Response(200, json=json_payload)

    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


class TestGetLatestAvailableTimestamp:
    """Tests for HimawariProvider.get_latest_available_timestamp."""

    def test_parses_valid_response(self) -> None:
        client = _make_mock_client({"date": "2026-07-29 12:30:00", "file": "x"})
        provider = HimawariProvider(http_client=client)

        result = provider.get_latest_available_timestamp()

        assert result == datetime(2026, 7, 29, 12, 30, 0, tzinfo=UTC)

    def test_returns_none_on_network_error(self) -> None:
        client = _make_mock_client(None, raise_error=True)
        provider = HimawariProvider(http_client=client)

        assert provider.get_latest_available_timestamp() is None

    def test_returns_none_on_missing_date_field(self) -> None:
        client = _make_mock_client({"file": "x"})
        provider = HimawariProvider(http_client=client)

        assert provider.get_latest_available_timestamp() is None

    def test_returns_none_on_malformed_date(self) -> None:
        client = _make_mock_client({"date": "not-a-date"})
        provider = HimawariProvider(http_client=client)

        assert provider.get_latest_available_timestamp() is None


class TestBuildImageRequest:
    """Tests for HimawariProvider.build_image_request."""

    def test_builds_correct_number_of_tiles(self) -> None:
        provider = HimawariProvider()
        timestamp = datetime(2026, 7, 29, 12, 34, 56, tzinfo=UTC)

        image = provider.build_image_request(timestamp, GridSize.GRID_4X4)

        assert len(image.tiles) == 16
        assert image.grid_size == GridSize.GRID_4X4
        assert image.provider_name == "himawari"

    def test_rounds_timestamp_down_to_ten_minutes(self) -> None:
        provider = HimawariProvider()
        timestamp = datetime(2026, 7, 29, 12, 37, 42, tzinfo=UTC)

        image = provider.build_image_request(timestamp, GridSize.GRID_2X2)

        assert image.timestamp == datetime(2026, 7, 29, 12, 30, 0, tzinfo=UTC)

    def test_tile_cache_keys_are_unique(self) -> None:
        provider = HimawariProvider()
        timestamp = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)

        image = provider.build_image_request(timestamp, GridSize.GRID_8X8)

        cache_keys = [tile.cache_key for tile in image.tiles]
        assert len(cache_keys) == len(set(cache_keys))
