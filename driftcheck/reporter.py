"""Reporter module for formatting and outputting drift results."""

from __future__ import annotations

from typing import List
from dataclasses import dataclass

from driftcheck.comparator import DriftResult


@dataclass
class DriftReport:
    """Aggregated report of all drift results."""

    results: List[DriftResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def drifted(self) -> List[DriftResult]:
        return [r for r in self.results if r.has_drift]

    @property
    def clean(self) -> List[DriftResult]:
        return [r for r in self.results if not r.has_drift]

    @property
    def drift_count(self) -> int:
        return len(self.drifted)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DriftReport(total={self.total}, drifted={self.drift_count}, "
            f"clean={len(self.clean)})"
        )


def format_text(report: DriftReport) -> str:
    """Return a human-readable text summary of the drift report."""
    lines: List[str] = []
    lines.append(f"DriftCheck Report — {report.total} resource(s) evaluated")
    lines.append("=" * 50)

    if not report.results:
        lines.append("No resources to report.")
        return "\n".join(lines)

    for result in report.results:
        status = "DRIFT" if result.has_drift else "OK"
        lines.append(f"[{status}] {result.resource_id} ({result.resource_type})")
        for field, (planned, live) in result.diffs.items():
            lines.append(f"       {field}: planned={planned!r}  live={live!r}")

    lines.append("=" * 50)
    lines.append(
        f"Summary: {report.drift_count} drifted, {len(report.clean)} clean"
    )
    return "\n".join(lines)


def format_json(report: DriftReport) -> dict:
    """Return a JSON-serialisable dict representation of the drift report."""
    return {
        "summary": {
            "total": report.total,
            "drifted": report.drift_count,
            "clean": len(report.clean),
        },
        "resources": [
            {
                "resource_id": r.resource_id,
                "resource_type": r.resource_type,
                "has_drift": r.has_drift,
                "diffs": {
                    field: {"planned": planned, "live": live}
                    for field, (planned, live) in r.diffs.items()
                },
            }
            for r in report.results
        ],
    }
