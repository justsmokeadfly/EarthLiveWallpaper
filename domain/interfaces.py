"""Abstract interfaces (ports) that the application layer depends on.

Every concrete implementation lives in `infrastructure/` and is wired into
the application layer by the composition root (`app.py`). Nothing in this
module imports any third-party or infrastructure code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from domain.entities import AppState, AssembledImage, SatelliteImage, TileSpec
from domain.enums import GridSize, WallpaperMode


class ImageProvider(ABC):
    """A source of full-disk satellite imagery (e.g. Himawari, GOES).

    Implementations encode everything specific to one satellite data
    provider: URL schemes, timestamp rounding rules, and available grid
    sizes. Nothing outside `infrastructure/providers/` should need to know
    which concrete provider is active.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique, stable identifier for this provider (e.g. 'himawari')."""

    @property
    @abstractmethod
    def supported_grid_sizes(self) -> tuple[GridSize, ...]:
        """Grid sizes this provider is able to serve."""

    @abstractmethod
    def get_latest_available_timestamp(self) -> datetime | None:
        """Query the provider for the timestamp of its most recent image.

        Returns:
            The UTC timestamp of the latest available image, or ``None``
            if the provider could not be reached or returned no data.
        """

    @abstractmethod
    def build_image_request(
        self, timestamp: datetime, grid_size: GridSize
    ) -> SatelliteImage:
        """Build the tile list required to assemble an image.

        Args:
            timestamp: The UTC timestamp to request.
            grid_size: The desired tile grid resolution.

        Returns:
            A SatelliteImage describing every tile URL needed.
        """


class TileDownloader(ABC):
    """Downloads a set of tiles concurrently, with retry and caching."""

    @abstractmethod
    def fetch_missing(
        self,
        tiles: tuple[TileSpec, ...],
        cache_dir: Path,
        retry_count: int,
        retry_delay_seconds: float,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[TileSpec, Path]:
        """Ensure every tile is present in the cache directory, downloading
        only those that are missing or previously failed.

        Args:
            tiles: All tiles required for the current image.
            cache_dir: Directory used to store/read cached tile files.
            retry_count: Maximum retry attempts per failing tile.
            retry_delay_seconds: Base delay for exponential backoff.
            on_progress: Optional callback invoked as
                ``on_progress(completed_count, total_count)`` each time a
                tile finishes (successfully or not), for UI progress bars.

        Returns:
            A mapping from successfully available TileSpec to its local
            file path. Tiles that could not be downloaded after all
            retries are simply absent from the returned mapping.
        """


class ImageAssembler(ABC):
    """Assembles a set of downloaded tiles into a single PNG image."""

    @abstractmethod
    def assemble(
        self,
        image: SatelliteImage,
        tile_paths: dict[TileSpec, Path],
        output_dir: Path,
    ) -> AssembledImage | None:
        """Stitch tiles into a single image and save it as PNG.

        Args:
            image: Metadata describing the expected tile grid.
            tile_paths: Mapping of tile spec to local file path, as
                returned by :meth:`TileDownloader.fetch_missing`.
            output_dir: Directory in which to save the assembled PNG.

        Returns:
            An AssembledImage describing the result, or ``None`` if
            assembly failed (e.g. too many missing/corrupted tiles).
        """


class WallpaperSetter(ABC):
    """Applies an image file as the Windows desktop wallpaper."""

    @abstractmethod
    def apply(self, image_path: Path, mode: WallpaperMode) -> bool:
        """Set the desktop wallpaper.

        Args:
            image_path: Path to the image file to apply.
            mode: Desired wallpaper positioning mode.

        Returns:
            ``True`` if the wallpaper was applied successfully, ``False``
            otherwise (never raises for expected failure conditions).
        """


class StateRepository(ABC):
    """Thread-safe persistent storage for :class:`AppState`."""

    @abstractmethod
    def load(self) -> AppState:
        """Load the current application state from disk.

        Returns:
            The persisted AppState, or a fresh default AppState if none
            has been saved yet or the stored file is unreadable.
        """

    @abstractmethod
    def save(self, state: AppState) -> None:
        """Persist the given application state atomically.

        Args:
            state: The state to persist.
        """


class CacheManager(ABC):
    """Manages lifecycle of cached tile files."""

    @abstractmethod
    def prune(self, max_age_hours: float, max_size_mb: int) -> int:
        """Remove cached files older than ``max_age_hours`` or beyond the
        ``max_size_mb`` soft cap (oldest first).

        Args:
            max_age_hours: Maximum allowed age of a cached file, in hours.
            max_size_mb: Soft cap on total cache size, in megabytes.

        Returns:
            Number of files removed.
        """

    @abstractmethod
    def get_cache_size_bytes(self) -> int:
        """Return the current total size of the cache directory in bytes."""


class NetworkProbe(ABC):
    """Checks basic internet connectivity."""

    @abstractmethod
    def is_online(self) -> bool:
        """Return ``True`` if outbound internet connectivity appears to
        be available, ``False`` otherwise.
        """


class TimelapseGenerator(ABC):
    """Builds an animated timelapse from a sequence of still images."""

    @abstractmethod
    def create(
        self,
        image_paths: list[Path],
        output_path: Path,
        frame_duration_ms: int = 200,
    ) -> bool:
        """Build an animated GIF from a sequence of images.

        Args:
            image_paths: Ordered list of image file paths, oldest first.
            output_path: Path to write the resulting ``.gif`` file to.
            frame_duration_ms: Duration each frame is displayed, in
                milliseconds.

        Returns:
            ``True`` if the timelapse was created successfully, ``False``
            otherwise (never raises).
        """
