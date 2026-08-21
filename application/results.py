"""Result value objects returned by application-layer use cases.

Using a single typed result object (rather than raising exceptions across
the use-case boundary) lets the scheduler and UI layers react to every
outcome - success, no-op, deferred, or failure - without wrapping every
call site in try/except. This is central to the "never crash" and
"keep current wallpaper on failure" requirements.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities import AssembledImage
from domain.enums import UpdateOutcome


@dataclass(frozen=True)
class UpdateResult:
    """Outcome of a single :class:`UpdateWallpaperUseCase` execution.

    Attributes:
        outcome: The categorical result of the update attempt.
        message: A short, human-readable summary suitable for display in
            the UI status area.
        assembled_image: The resulting AssembledImage, present only when
            ``outcome`` is ``UpdateOutcome.SUCCESS``.
        duration_seconds: Wall-clock time the update cycle took, for
            diagnostics/UI display.
    """

    outcome: UpdateOutcome
    message: str
    assembled_image: AssembledImage | None = None
    duration_seconds: float = 0.0

    @property
    def is_success(self) -> bool:
        """Whether a new wallpaper was actually applied."""
        return self.outcome == UpdateOutcome.SUCCESS

    @property
    def is_actionable_failure(self) -> bool:
        """Whether this outcome represents a real failure (as opposed to
        an expected no-op like already-up-to-date or duplicate content).
        """
        return self.outcome in (
            UpdateOutcome.NETWORK_UNAVAILABLE,
            UpdateOutcome.PROVIDER_UNAVAILABLE,
            UpdateOutcome.DOWNLOAD_FAILED,
            UpdateOutcome.ASSEMBLY_FAILED,
            UpdateOutcome.WALLPAPER_APPLY_FAILED,
            UpdateOutcome.UNEXPECTED_ERROR,
        )
