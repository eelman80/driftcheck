"""Export scored drift results to JSON or CSV."""

import csv
import json
from io import StringIO
from typing import List

from driftcheck.scorer import ScoredResult


def scored_to_dict(scored: ScoredResult) -> dict:
    return {
        "resource_id": scored.result.resource_id,
        "resource_type": scored.result.resource_type,
        "score": scored.score,
        "severity": scored.severity,
        "drifted_fields": [d.field for d in scored.result.diffs],
        "reasons": scored.reasons,
    }


def export_scores_json(scored_results: List[ScoredResult]) -> str:
    """Return a JSON string of all scored results."""
    data = {
        "total_resources": len(scored_results),
        "total_score": sum(s.score for s in scored_results),
        "results": [scored_to_dict(s) for s in scored_results],
    }
    return json.dumps(data, indent=2)


def export_scores_csv(scored_results: List[ScoredResult]) -> str:
    """Return a CSV string of all scored results."""
    buf = StringIO()
    fieldnames = ["resource_id", "resource_type", "score", "severity", "drifted_fields"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for s in scored_results:
        writer.writerow({
            "resource_id": s.result.resource_id,
            "resource_type": s.result.resource_type,
            "score": s.score,
            "severity": s.severity,
            "drifted_fields": "|".join(d.field for d in s.result.diffs),
        })
    return buf.getvalue()


def export_scores_to_file(scored_results: List[ScoredResult], path: str, fmt: str = "json") -> None:
    """Write scored results to a file in the given format ('json' or 'csv')."""
    if fmt == "json":
        content = export_scores_json(scored_results)
    elif fmt == "csv":
        content = export_scores_csv(scored_results)
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Use 'json' or 'csv'.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
