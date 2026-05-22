"""Aggregate DriftResults into a human-readable DriftReport."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from driftcheck.comparator import DriftResult


@dataclass
class DriftReport:
    """Collection of DriftResults with summary helpers."""

    results: List[DriftResult] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Summary properties
    # ------------------------------------------------------------------

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def drifted(self) -> List[DriftResult]:
        return [r for r in self.results if r.drifted]

    @property
    def clean(self) -> List[DriftResult]:
        return [r for r in self.results if not r.drifted]

    @property
    def drift_count(self) -> int:
        return len(self.drifted)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def summary_text(self) -> str:
        """Return a short human-readable summary string."""
        return (
            f"DriftReport: {self.total} resource(s) checked — "
            f"{self.drift_count} drifted, {self.total - self.drift_count} clean."
        )

    def detailed_text(self) -> str:
        """Return a multi-line report listing every drifted field."""
        lines = [self.summary_text()]
        for result in self.drifted:
            lines.append(
                f"  [{result.resource_type}] {result.resource_id}:"
            )
            for diff in result.diffs:
                lines.append(
                    f"    - {diff.field}: planned={diff.planned!r} "
                    f"actual={diff.actual!r}"
                )
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DriftReport(total={self.total}, drift_count={self.drift_count})"
        )
