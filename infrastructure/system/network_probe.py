"""Lightweight internet connectivity probe.

Deliberately avoids making an HTTP request to the actual image provider
just to check connectivity - a raw TCP connect to a well-known, highly
available host/port is cheaper and distinguishes "no internet at all"
from "provider is down" (the latter is handled separately by the
provider's own timestamp-fetch failure path).
"""

from __future__ import annotations

import socket

from domain.interfaces import NetworkProbe
from logger import get_logger

_logger = get_logger(__name__)

# A small set of well-known, highly-available hosts. Trying more than one
# avoids a false "offline" reading if a single host happens to be
# unreachable (e.g. due to regional DNS/CDN issues) while the internet is
# otherwise fine.
_PROBE_TARGETS: tuple[tuple[str, int], ...] = (
    ("1.1.1.1", 53),
    ("8.8.8.8", 53),
)
_TIMEOUT_SECONDS = 3.0


class SocketNetworkProbe(NetworkProbe):
    """Checks connectivity via raw TCP connections to well-known hosts."""

    def is_online(self) -> bool:
        """Return ``True`` if at least one probe target is reachable.

        Returns:
            ``True`` if connectivity appears available, ``False``
            otherwise.
        """
        for host, port in _PROBE_TARGETS:
            try:
                with socket.create_connection((host, port), timeout=_TIMEOUT_SECONDS):
                    return True
            except OSError as exc:
                _logger.debug("Network probe to %s:%d failed: %s", host, port, exc)
                continue

        _logger.warning("All network probe targets unreachable; assuming offline.")
        return False
