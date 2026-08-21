from io import BytesIO

from PIL import Image

from infrastructure.download.http_tile_downloader import HttpTileDownloader


def _jpeg_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def test_valid_image_bytes_are_accepted() -> None:
    assert HttpTileDownloader._is_valid_image_bytes(_jpeg_bytes()) is True


def test_html_response_is_rejected() -> None:
    assert HttpTileDownloader._is_valid_image_bytes(b"<html>service unavailable</html>") is False
