"""Compares planned resource attributes against live state to detect drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from driftcheck.fetcher import LiveResource
from driftcheck.parser import PlannedResource


@dataclass
class DriftResult:
    """Holds the drift comparison result for a single resource."""

    resource_type: str
    resource_id: str
    drifted: bool
    differences: list[dict[str, Any]] = field(default_factory=list)

    def __repr__(self) -> str:
        status = "DRIFTED" if self.drifted else "OK"
        return f"DriftResult({status}, type={self.resource_type!r}, id={self.resource_id!r})"


def compare(planned: PlannedResource, live: LiveResource) -> DriftResult:
    """Compare a planned resource against its live counterpart.

    Only attributes present in the plan are checked; extra live attributes
    are ignored to avoid noise from provider-computed fields.
    """
    differences: list[dict[str, Any]] = []

    for key, planned_value in planned.attributes.items():
        live_value = live.attributes.get(key)
        if live_value != planned_value:
            differences.append(
                {
                    "attribute": key,
                    "planned": planned_value,
                    "live": live_value,
                }
            )

    return DriftResult(
        resource_type=planned.resource_type,
        resource_id=planned.resource_id,
        drifted=bool(differences),
        differences=differences,
    )


def compare_all(planned_resources: list[PlannedResource], live_resources: list[LiveResource]) -> list[DriftResult]:
    """Compare a list of planned resources against a list of live resources.

    Matches resources by (resource_type, resource_id). Unmatched planned
    resources are reported as fully drifted (resource missing live).
    """
    live_index = {(r.resource_type, r.resource_id): r for r in live_resources}
    results: list[DriftResult] = []

    for planned in planned_resources:
        key = (planned.resource_type, planned.resource_id)
        live = live_index.get(key)
        if live is None:
            results.append(
                DriftResult(
                    resource_type=planned.resource_type,
                    resource_id=planned.resource_id,
                    drifted=True,
                    differences=[{"attribute": "*", "planned": "<exists>", "live": "<not found>"}],
                )
            )
        else:
            results.append(compare(planned, live))

    return results
