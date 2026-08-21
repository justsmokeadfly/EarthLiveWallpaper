"""Unit tests for UpdateWallpaperUseCase, using fake implementations of
every injected interface so these tests run anywhere (no network, no
Windows API, no real filesystem tile downloads).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from application.update_wallpaper_use_case import UpdateWallpaperUseCase
from domain.entities import AppConfig, AppState, AssembledImage, SatelliteImage, TileSpec
from domain.enums import GridSize, UpdateOutcome, WallpaperMode
from domain.interfaces import (
    CacheManager,
    ImageAssembler,
    ImageProvider,
    NetworkProbe,
    StateRepository,
    TileDownloader,
    WallpaperSetter,
)


class FakeNetworkProbe(NetworkProbe):
    def __init__(self, online: bool = True) -> None:
        self.online = online

    def is_online(self) -> bool:
        return self.online


class FakeProvider(ImageProvider):
    def __init__(self, latest_timestamp: datetime | None) -> None:
        self.latest_timestamp = latest_timestamp

    @property
    def name(self) -> str:
        return "fakeprovider"

    @property
    def supported_grid_sizes(self) -> tuple[GridSize, ...]:
        return (GridSize.GRID_2X2,)

    def get_latest_available_timestamp(self) -> datetime | None:
        return self.latest_timestamp

    def build_image_request(self, timestamp: datetime, grid_size: GridSize) -> SatelliteImage:
        tiles = tuple(
            TileSpec(url=f"http://x/{i}", column=i, row=0, cache_key=f"tile_{i}")
            for i in range(grid_size.tile_count)
        )
        return SatelliteImage(
            provider_name=self.name, timestamp=timestamp, grid_size=grid_size, tiles=tiles
        )


class FakeDownloader(TileDownloader):
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed
        self.progress_calls: list[tuple[int, int]] = []

    def fetch_missing(self, tiles, cache_dir, retry_count, retry_delay_seconds, on_progress=None):
        if not self.succeed:
            return {}
        results = {}
        total = len(tiles)
        for i, tile in enumerate(tiles, start=1):
            results[tile] = cache_dir / tile.cache_key
            if on_progress is not None:
                on_progress(i, total)
            self.progress_calls.append((i, total))
        return results


class FakeAssembler(ImageAssembler):
    def __init__(self, content_hash: str = "hash1", succeed: bool = True) -> None:
        self.content_hash = content_hash
        self.succeed = succeed

    def assemble(self, image, tile_paths, output_dir):
        if not self.succeed:
            return None
        return AssembledImage(
            source=image,
            file_path=output_dir / "assembled.png",
            content_hash=self.content_hash,
            width=100,
            height=100,
        )


class FakeWallpaperSetter(WallpaperSetter):
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed
        self.applied_paths: list[Path] = []

    def apply(self, image_path: Path, mode: WallpaperMode) -> bool:
        if self.succeed:
            self.applied_paths.append(image_path)
        return self.succeed


class FakeStateRepository(StateRepository):
    def __init__(self, initial_state: AppState | None = None) -> None:
        self.state = initial_state or AppState()

    def load(self) -> AppState:
        return self.state

    def save(self, state: AppState) -> None:
        self.state = state


class FakeCacheManager(CacheManager):
    def prune(self, max_age_hours: float, max_size_mb: int) -> int:
        return 0

    def get_cache_size_bytes(self) -> int:
        return 0


def _build_use_case(
    tmp_path: Path,
    provider: ImageProvider,
    downloader: TileDownloader | None = None,
    assembler: ImageAssembler | None = None,
    wallpaper_setter: WallpaperSetter | None = None,
    state_repository: StateRepository | None = None,
    network_probe: NetworkProbe | None = None,
) -> UpdateWallpaperUseCase:
    return UpdateWallpaperUseCase(
        provider=provider,
        downloader=downloader or FakeDownloader(),
        assembler=assembler or FakeAssembler(),
        wallpaper_setter=wallpaper_setter or FakeWallpaperSetter(),
        state_repository=state_repository or FakeStateRepository(),
        cache_manager=FakeCacheManager(),
        network_probe=network_probe or FakeNetworkProbe(),
        cache_dir=tmp_path / "cache",
        wallpapers_dir=tmp_path / "wallpapers",
    )


def _default_config() -> AppConfig:
    return AppConfig(grid_size=GridSize.GRID_2X2, retry_count=1, retry_delay_seconds=0.01)


class TestUpdateWallpaperUseCase:
    """End-to-end (within the application layer) tests of one update cycle."""

    def test_success_path_applies_wallpaper_and_updates_state(self, tmp_path: Path) -> None:
        timestamp = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path, FakeProvider(timestamp), wallpaper_setter=wallpaper_setter
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.SUCCESS
        assert len(wallpaper_setter.applied_paths) == 1

    def test_offline_returns_network_unavailable_and_does_not_touch_wallpaper(
        self, tmp_path: Path
    ) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(datetime.now(timezone.utc)),
            wallpaper_setter=wallpaper_setter,
            network_probe=FakeNetworkProbe(online=False),
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.NETWORK_UNAVAILABLE
        assert wallpaper_setter.applied_paths == []

    def test_provider_unavailable_keeps_current_wallpaper(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path, FakeProvider(latest_timestamp=None), wallpaper_setter=wallpaper_setter
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.PROVIDER_UNAVAILABLE
        assert wallpaper_setter.applied_paths == []

    def test_already_up_to_date_is_a_noop(self, tmp_path: Path) -> None:
        timestamp = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        state_repo = FakeStateRepository(AppState(last_timestamp=timestamp))
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(timestamp),
            wallpaper_setter=wallpaper_setter,
            state_repository=state_repo,
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.ALREADY_UP_TO_DATE
        assert wallpaper_setter.applied_paths == []

    def test_duplicate_content_skips_wallpaper_but_updates_timestamp(
        self, tmp_path: Path
    ) -> None:
        old_timestamp = datetime(2026, 7, 29, 11, 0, 0, tzinfo=timezone.utc)
        new_timestamp = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        state_repo = FakeStateRepository(
            AppState(last_timestamp=old_timestamp, last_content_hash="samehash")
        )
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(new_timestamp),
            assembler=FakeAssembler(content_hash="samehash"),
            wallpaper_setter=wallpaper_setter,
            state_repository=state_repo,
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.DUPLICATE_CONTENT
        assert wallpaper_setter.applied_paths == []
        assert state_repo.state.last_timestamp == new_timestamp

    def test_download_failure_keeps_current_wallpaper(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(datetime.now(timezone.utc)),
            downloader=FakeDownloader(succeed=False),
            wallpaper_setter=wallpaper_setter,
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.DOWNLOAD_FAILED
        assert wallpaper_setter.applied_paths == []

    def test_assembly_failure_keeps_current_wallpaper(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(datetime.now(timezone.utc)),
            assembler=FakeAssembler(succeed=False),
            wallpaper_setter=wallpaper_setter,
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.ASSEMBLY_FAILED
        assert wallpaper_setter.applied_paths == []

    def test_wallpaper_apply_failure_is_reported(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter(succeed=False)
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(datetime.now(timezone.utc)),
            wallpaper_setter=wallpaper_setter,
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.WALLPAPER_APPLY_FAILED

    def test_force_bypasses_already_up_to_date(self, tmp_path: Path) -> None:
        timestamp = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        state_repo = FakeStateRepository(AppState(last_timestamp=timestamp))
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(timestamp),
            wallpaper_setter=wallpaper_setter,
            state_repository=state_repo,
        )

        result = use_case.execute(_default_config(), force=True)

        assert result.outcome == UpdateOutcome.SUCCESS
        assert len(wallpaper_setter.applied_paths) == 1

    def test_never_raises_on_unexpected_provider_exception(self, tmp_path: Path) -> None:
        class ExplodingProvider(FakeProvider):
            def get_latest_available_timestamp(self) -> datetime | None:
                raise RuntimeError("boom")

        use_case = _build_use_case(tmp_path, ExplodingProvider(None))

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.UNEXPECTED_ERROR

    def test_paused_config_skips_update_entirely(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(datetime.now(timezone.utc)),
            wallpaper_setter=wallpaper_setter,
        )
        config = AppConfig(grid_size=GridSize.GRID_2X2, paused=True)

        result = use_case.execute(config)

        assert result.outcome == UpdateOutcome.PAUSED
        assert wallpaper_setter.applied_paths == []

    def test_force_bypasses_pause(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path,
            FakeProvider(datetime.now(timezone.utc)),
            wallpaper_setter=wallpaper_setter,
        )
        config = AppConfig(grid_size=GridSize.GRID_2X2, paused=True)

        result = use_case.execute(config, force=True)

        assert result.outcome == UpdateOutcome.SUCCESS
        assert len(wallpaper_setter.applied_paths) == 1


class TestReapply:
    """Tests for UpdateWallpaperUseCase.reapply()."""

    def test_reapply_applies_existing_file(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path, FakeProvider(None), wallpaper_setter=wallpaper_setter
        )
        existing_file = tmp_path / "old_wallpaper.png"
        existing_file.write_bytes(b"fake png bytes")

        result = use_case.reapply(existing_file, WallpaperMode.FILL)

        assert result is True
        assert wallpaper_setter.applied_paths == [existing_file]

    def test_reapply_returns_false_for_missing_file(self, tmp_path: Path) -> None:
        wallpaper_setter = FakeWallpaperSetter()
        use_case = _build_use_case(
            tmp_path, FakeProvider(None), wallpaper_setter=wallpaper_setter
        )
        missing_file = tmp_path / "does_not_exist.png"

        result = use_case.reapply(missing_file, WallpaperMode.FILL)

        assert result is False
        assert wallpaper_setter.applied_paths == []


class TestProgressReporting:
    """Tests that the use case reports progress via a ProgressTracker."""

    def test_progress_passes_through_stages_and_resets_to_idle(self, tmp_path: Path) -> None:
        from application.progress import ProgressStage, ProgressTracker

        tracker = ProgressTracker()
        downloader = FakeDownloader()
        use_case = UpdateWallpaperUseCase(
            provider=FakeProvider(datetime.now(timezone.utc)),
            downloader=downloader,
            assembler=FakeAssembler(),
            wallpaper_setter=FakeWallpaperSetter(),
            state_repository=FakeStateRepository(),
            cache_manager=FakeCacheManager(),
            network_probe=FakeNetworkProbe(),
            cache_dir=tmp_path / "cache",
            wallpapers_dir=tmp_path / "wallpapers",
            progress_tracker=tracker,
        )

        # Idle before running.
        assert tracker.get().stage == ProgressStage.IDLE

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.SUCCESS
        # Downloader's on_progress callback was invoked with increasing counts.
        assert downloader.progress_calls == [(1, 4), (2, 4), (3, 4), (4, 4)]
        # Tracker returns to idle once the cycle fully completes.
        assert tracker.get().stage == ProgressStage.IDLE

    def test_progress_resets_to_idle_even_on_failure(self, tmp_path: Path) -> None:
        from application.progress import ProgressStage, ProgressTracker

        tracker = ProgressTracker()
        use_case = UpdateWallpaperUseCase(
            provider=FakeProvider(datetime.now(timezone.utc)),
            downloader=FakeDownloader(succeed=False),
            assembler=FakeAssembler(),
            wallpaper_setter=FakeWallpaperSetter(),
            state_repository=FakeStateRepository(),
            cache_manager=FakeCacheManager(),
            network_probe=FakeNetworkProbe(),
            cache_dir=tmp_path / "cache",
            wallpapers_dir=tmp_path / "wallpapers",
            progress_tracker=tracker,
        )

        result = use_case.execute(_default_config())

        assert result.outcome == UpdateOutcome.DOWNLOAD_FAILED
        assert tracker.get().stage == ProgressStage.IDLE
