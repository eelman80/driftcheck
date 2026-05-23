"""Analyzes drift trends over time using audit log history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from collections import defaultdict

from driftcheck.audit_log import AuditEntry


@dataclass
class ResourceTrend:
    resource_id: str
    occurrences: int
    first_seen: str
    last_seen: str
    drifted_fields: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ResourceTrend(resource_id={self.resource_id!r}, "
            f"occurrences={self.occurrences}, "
            f"drifted_fields={self.drifted_fields})"
        )


@dataclass
class TrendReport:
    total_runs: int
    drifted_runs: int
    clean_runs: int
    most_drifted: List[ResourceTrend] = field(default_factory=list)

    @property
    def drift_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return round(self.drifted_runs / self.total_runs, 4)


def analyze_trends(
    entries: List[AuditEntry],
    top_n: int = 5,
) -> TrendReport:
    """Compute drift trends from a list of audit log entries."""
    total_runs = len(entries)
    drifted_runs = sum(1 for e in entries if e.drifted)
    clean_runs = total_runs - drifted_runs

    resource_counts: dict = defaultdict(lambda: {"count": 0, "fields": set(), "timestamps": []})

    for entry in entries:
        for diff in entry.diffs:
            rid = diff.get("resource_id", "unknown")
            resource_counts[rid]["count"] += 1
            resource_counts[rid]["timestamps"].append(entry.timestamp)
            field_name = diff.get("field")
            if field_name:
                resource_counts[rid]["fields"].add(field_name)

    trends = []
    for rid, data in resource_counts.items():
        timestamps = sorted(data["timestamps"])
        trends.append(
            ResourceTrend(
                resource_id=rid,
                occurrences=data["count"],
                first_seen=timestamps[0] if timestamps else "",
                last_seen=timestamps[-1] if timestamps else "",
                drifted_fields=sorted(data["fields"]),
            )
        )

    trends.sort(key=lambda t: t.occurrences, reverse=True)

    return TrendReport(
        total_runs=total_runs,
        drifted_runs=drifted_runs,
        clean_runs=clean_runs,
        most_drifted=trends[:top_n],
    )


def render_trend_report(report: TrendReport) -> str:
    """Return a human-readable summary of the trend report."""
    lines = [
        "=== Drift Trend Report ===",
        f"Total runs   : {report.total_runs}",
        f"Drifted runs : {report.drifted_runs}",
        f"Clean runs   : {report.clean_runs}",
        f"Drift rate   : {report.drift_rate:.1%}",
        "",
        "Top drifting resources:",
    ]
    if not report.most_drifted:
        lines.append("  (none)")
    else:
        for t in report.most_drifted:
            lines.append(f"  {t.resource_id}  — {t.occurrences}x  fields: {', '.join(t.drifted_fields) or 'n/a'}")
    return "\n".join(lines)
