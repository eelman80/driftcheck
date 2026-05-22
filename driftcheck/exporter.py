"""Export drift reports to various output formats (JSON, CSV)."""

from __future__ import annotations

import csv
import json
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from driftcheck.reporter import DriftReport


def export_json(report: "DriftReport", indent: int = 2) -> str:
    """Serialize a DriftReport to a JSON string."""
    data = {
        "summary": {
            "total": report.total,
            "drifted": report.drift_count,
            "clean": report.total - report.drift_count,
        },
        "results": [
            {
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "drifted": r.drifted,
                "diffs": [
                    {"field": d.field, "planned": d.planned, "actual": d.actual}
                    for d in r.diffs
                ],
            }
            for r in report.results
        ],
    }
    return json.dumps(data, indent=indent, default=str)


def export_csv(report: "DriftReport") -> str:
    """Serialize drifted fields in a DriftReport to a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["resource_type", "resource_id", "field", "planned", "actual"])
    for result in report.results:
        if result.drifted:
            for diff in result.diffs:
                writer.writerow(
                    [
                        result.resource_type,
                        result.resource_id,
                        diff.field,
                        diff.planned,
                        diff.actual,
                    ]
                )
    return output.getvalue()


def export_to_file(report: "DriftReport", path: str, fmt: str = "json") -> None:
    """Write a DriftReport to *path* in the requested format ('json' or 'csv')."""
    fmt = fmt.lower()
    if fmt == "json":
        content = export_json(report)
    elif fmt == "csv":
        content = export_csv(report)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
