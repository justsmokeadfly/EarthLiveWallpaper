"""Centralized logging configuration for EarthLive.

A single call to :func:`configure_logging` from the composition root sets
up both a rotating file handler and a console handler. All other modules
simply do ``logger = logging.getLogger(__name__)`` and inherit this
configuration - no module-level handler setup happens anywhere else in
the codebase.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-32s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES = 2 * 1024 * 1024  # 2 MB per log file
_BACKUP_COUNT = 5


def configure_logging(log_dir: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure the root EarthLive logger with file + console handlers.

    Safe to call more than once; existing EarthLive handlers are removed
    before new ones are attached, so repeated calls (e.g. after a config
    reload) never produce duplicate log lines.

    Args:
        log_dir: Directory in which to write the rotating log file. It is
            created if it does not already exist.
        level: Minimum logging level to emit.

    Returns:
        The configured root application logger, named ``"earthlive"``.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "earthlive.log"

    root_logger = logging.getLogger("earthlive")
    root_logger.setLevel(level)
    root_logger.propagate = False

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``"earthlive"`` namespace.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A logger instance that inherits handlers configured by
        :func:`configure_logging`.
    """
    return logging.getLogger(f"earthlive.{name}")
