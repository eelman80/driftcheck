"""Attribute-level diff utilities for highlighting specific changes between
planned and live resource configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AttributeDiff:
    """Represents a single attribute-level difference."""

    attribute: str
    planned: Any
    live: Any
    severity: str = "change"  # 'change', 'added', 'removed'

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AttributeDiff(attribute={self.attribute!r}, "
            f"planned={self.planned!r}, live={self.live!r}, "
            f"severity={self.severity!r})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "planned": self.planned,
            "live": self.live,
            "severity": self.severity,
        }


def diff_attributes(
    planned: Dict[str, Any],
    live: Dict[str, Any],
    ignore_keys: Optional[List[str]] = None,
) -> List[AttributeDiff]:
    """Compare two attribute dicts and return a list of AttributeDiff objects.

    Args:
        planned: Attributes from the Terraform plan.
        live:    Attributes fetched from the live infrastructure.
        ignore_keys: Optional list of keys to skip during comparison.

    Returns:
        A list of :class:`AttributeDiff` instances for every divergent key.
    """
    ignore = set(ignore_keys or [])
    diffs: List[AttributeDiff] = []

    all_keys = set(planned.keys()) | set(live.keys())

    for key in sorted(all_keys):
        if key in ignore:
            continue

        planned_val = planned.get(key)
        live_val = live.get(key)

        if key not in planned and key in live:
            diffs.append(AttributeDiff(key, None, live_val, severity="added"))
        elif key in planned and key not in live:
            diffs.append(AttributeDiff(key, planned_val, None, severity="removed"))
        elif planned_val != live_val:
            diffs.append(AttributeDiff(key, planned_val, live_val, severity="change"))

    return diffs


def summarise_diffs(diffs: List[AttributeDiff]) -> Dict[str, int]:
    """Return a count of each severity level present in *diffs*."""
    summary: Dict[str, int] = {"change": 0, "added": 0, "removed": 0}
    for d in diffs:
        summary[d.severity] = summary.get(d.severity, 0) + 1
    return summary
