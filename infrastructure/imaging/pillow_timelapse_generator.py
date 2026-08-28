"""Pillow-based implementation of :class:`TimelapseGenerator`.

Builds an animated GIF from the wallpaper history, downscaling each frame
to keep the output file a reasonable size (full-disk Himawari images at
higher grid sizes can be several thousand pixels wide).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from domain.interfaces import TimelapseGenerator
from logger import get_logger

_logger = get_logger(__name__)

# Frames are downscaled so their width never exceeds this, keeping the
# resulting GIF file size and memory usage reasonable even when built
# from 8x8/16x16 grid history images.
_MAX_FRAME_WIDTH = 800


class PillowTimelapseGenerator(TimelapseGenerator):
    """Creates an animated GIF timelapse from a list of image files."""

    def create(
        self,
        image_paths: list[Path],
        output_path: Path,
        frame_duration_ms: int = 200,
    ) -> bool:
        """Build an animated GIF from the given images.

        Args:
            image_paths: Ordered list of image file paths, oldest first.
            output_path: Path to write the resulting ``.gif`` file to.
            frame_duration_ms: Duration each frame is displayed, in
                milliseconds.

        Returns:
            ``True`` on success, ``False`` if fewer than 2 usable frames
            could be loaded or the file could not be written.
        """
        frames: list[Image.Image] = []

        for path in image_paths:
            if not path.exists():
                _logger.warning("Skipping missing timelapse frame: %s", path)
                continue
            try:
                with Image.open(path) as opened:
                    opened.load()
                    frame = opened.convert("RGB")
            except (UnidentifiedImageError, OSError) as exc:
                _logger.warning("Skipping unreadable timelapse frame %s: %s", path, exc)
                continue

            if frame.width > _MAX_FRAME_WIDTH:
                ratio = _MAX_FRAME_WIDTH / frame.width
                new_size = (_MAX_FRAME_WIDTH, max(1, int(frame.height * ratio)))
                frame = frame.resize(new_size, Image.LANCZOS)

            frames.append(frame)

        if len(frames) < 2:
            _logger.error(
                "Cannot create timelapse: only %d usable frame(s) found (need at least 2).",
                len(frames),
            )
            for frame in frames:
                frame.close()
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")

        try:
            first, *rest = frames
            first.save(
                tmp_path,
                format="GIF",
                save_all=True,
                append_images=rest,
                duration=frame_duration_ms,
                loop=0,
                optimize=True,
            )
            tmp_path.replace(output_path)
        except OSError:
            _logger.exception("Failed to write timelapse GIF to %s.", output_path)
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            return False
        finally:
            for frame in frames:
                frame.close()

        _logger.info(
            "Timelapse created: %s (%d frames, %dms/frame).",
            output_path.name,
            len(frames),
            frame_duration_ms,
        )
        return True
