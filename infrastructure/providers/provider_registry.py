"""Registry mapping provider names to :class:`ImageProvider` factories.

This is the single point of extension for adding new satellite image
providers. To add GOES or Meteosat support in the future:

1. Implement ``ImageProvider`` in a new module under
   ``infrastructure/providers/``.
2. Register a factory for it via :func:`register_provider`, or add it to
   :data:`_DEFAULT_FACTORIES` below.

No other module needs to change - ``config.py``, ``app.py``, and the
application layer only ever ask this registry for "the provider named X".
"""

from __future__ import annotations

from collections.abc import Callable

from domain.interfaces import ImageProvider
from infrastructure.providers.himawari_provider import HimawariProvider
from logger import get_logger

_logger = get_logger(__name__)

_ProviderFactory = Callable[[], ImageProvider]


class ProviderRegistry:
    """Looks up and instantiates :class:`ImageProvider` implementations by
    name.
    """

    def __init__(self) -> None:
        """Initialize the registry with the built-in default providers."""
        self._factories: dict[str, _ProviderFactory] = {}
        for provider_name, factory in _DEFAULT_FACTORIES.items():
            self.register(provider_name, factory)

    def register(self, name: str, factory: _ProviderFactory) -> None:
        """Register a provider factory under the given name.

        Args:
            name: Unique provider identifier (matches ``config.provider``).
            factory: A zero-argument callable returning a new
                :class:`ImageProvider` instance.
        """
        normalized = name.strip().lower()
        if normalized in self._factories:
            _logger.debug("Overwriting existing provider registration: %s", normalized)
        self._factories[normalized] = factory

    def create(self, name: str) -> ImageProvider:
        """Instantiate the provider registered under ``name``.

        Args:
            name: The provider identifier to look up.

        Returns:
            A new instance of the requested provider.

        Raises:
            KeyError: If no provider is registered under that name.
        """
        normalized = name.strip().lower()
        if normalized not in self._factories:
            available = ", ".join(sorted(self._factories))
            raise KeyError(
                f"No image provider registered as '{name}'. Available: {available}"
            )
        return self._factories[normalized]()

    def available_providers(self) -> tuple[str, ...]:
        """Return the names of all currently registered providers."""
        return tuple(sorted(self._factories))


_DEFAULT_FACTORIES: dict[str, _ProviderFactory] = {
    "himawari": lambda: HimawariProvider(),
}
