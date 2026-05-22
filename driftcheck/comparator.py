"""Compare planned resources against live infrastructure state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from driftcheck.parser import PlannedResource
from driftcheck.fetcher import LiveResource


@dataclass
class FieldDiff:
    """A single field that differs between plan and live state."""

    field: str
    planned: object
    actual: object

    def __repr__(self) -> str:  # pragma: no cover
        return f"FieldDiff(field={self.field!r}, planned={self.planned!r}, actual={self.actual!r})"


@dataclass
class DriftResult:
    """Outcome of comparing one planned resource to its live counterpart."""

    resource_type: str
    resource_id: str
    diffs: List[FieldDiff] = field(default_factory=list)

    @property
    def drifted(self) -> bool:
        return bool(self.diffs)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DriftResult(resource_type={self.resource_type!r}, "
            f"resource_id={self.resource_id!r}, drifted={self.drifted})"
        )


def compare(planned: PlannedResource, live: LiveResource) -> DriftResult:
    """Return a DriftResult describing every field that has drifted."""
    diffs: List[FieldDiff] = []

    for key, planned_val in planned.attributes.items():
        actual_val = live.attributes.get(key)
        if actual_val != planned_val:
            diffs.append(FieldDiff(field=key, planned=planned_val, actual=actual_val))

    return DriftResult(
        resource_type=planned.resource_type,
        resource_id=live.resource_id,
        diffs=diffs,
    )


def compare_all(
    planned_resources: List[PlannedResource],
    live_resources: List[LiveResource],
) -> List[DriftResult]:
    """Pair planned resources with live resources by type and id, then compare."""
    live_index = {(r.resource_type, r.resource_id): r for r in live_resources}
    results: List[DriftResult] = []

    for planned in planned_resources:
        key = (planned.resource_type, planned.resource_id)
        live = live_index.get(key)
        if live is None:
            # Resource exists in plan but not live — treat every field as drifted
            diffs = [
                FieldDiff(field=k, planned=v, actual=None)
                for k, v in planned.attributes.items()
            ]
            results.append(
                DriftResult(
                    resource_type=planned.resource_type,
                    resource_id=planned.resource_id,
                    diffs=diffs,
                )
            )
        else:
            results.append(compare(planned, live))

    return results
