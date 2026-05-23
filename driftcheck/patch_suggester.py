"""Generate human-readable Terraform patch suggestions from attribute diffs."""

from __future__ import annotations

from typing import List

from driftcheck.differ import AttributeDiff


_SEVERITY_EMOJI = {
    "change": "~",
    "added": "+",
    "removed": "-",
}


def _format_value(value: object) -> str:
    """Return a Terraform-style string representation of *value*."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def suggest_patch(resource_address: str, diffs: List[AttributeDiff]) -> str:
    """Produce a textual patch suggestion for the given resource.

    Args:
        resource_address: Terraform resource address, e.g. ``aws_s3_bucket.example``.
        diffs: List of :class:`~driftcheck.differ.AttributeDiff` objects.

    Returns:
        A multi-line string describing the recommended changes, or an empty
        string when *diffs* is empty.
    """
    if not diffs:
        return ""

    lines: List[str] = [
        f"# Suggested corrections for: {resource_address}",
        f"resource \"...\" \"{resource_address}\" {{",
    ]

    for diff in diffs:
        symbol = _SEVERITY_EMOJI.get(diff.severity, "?")
        if diff.severity == "change":
            lines.append(
                f"  {symbol} {diff.attribute} = {_format_value(diff.planned)}"
                f"  # live value: {_format_value(diff.live)}"
            )
        elif diff.severity == "removed":
            lines.append(
                f"  {symbol} {diff.attribute} = {_format_value(diff.planned)}"
                f"  # missing from live state"
            )
        else:  # added — key exists live but not in plan
            lines.append(
                f"  {symbol} # remove or import: {diff.attribute} = {_format_value(diff.live)}"
            )

    lines.append("}")
    return "\n".join(lines)


def batch_suggestions(
    resource_address: str,
    diffs: List[AttributeDiff],
    max_diffs: int = 20,
) -> List[str]:
    """Return individual patch suggestion strings, one per diff, up to *max_diffs*."""
    truncated = diffs[:max_diffs]
    return [
        suggest_patch(resource_address, [d])
        for d in truncated
    ]
