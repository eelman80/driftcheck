"""Render human-readable reports for snapshot deltas."""

from __future__ import annotations

from typing import List

from driftcheck.snapshot import SnapshotDelta

_RESET = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"


def _colour(text: str, code: str, use_colour: bool) -> str:
    return f"{code}{text}{_RESET}" if use_colour else text


def format_delta(delta: SnapshotDelta, use_colour: bool = True) -> str:
    if not delta.has_changes:
        label = _colour("NO CHANGES", _GREEN, use_colour)
        return f"  {delta.resource_id}: {label}\n"

    lines = [f"  {_colour(delta.resource_id, _BOLD, use_colour)}:"]

    for key, val in sorted(delta.added.items()):
        lines.append(
            f"    {_colour('+', _GREEN, use_colour)} {key}: {val!r}"
        )
    for key, val in sorted(delta.removed.items()):
        lines.append(
            f"    {_colour('-', _RED, use_colour)} {key}: {val!r}"
        )
    for key, info in sorted(delta.changed.items()):
        old = _colour(repr(info['old']), _RED, use_colour)
        new = _colour(repr(info['new']), _GREEN, use_colour)
        lines.append(f"    {_colour('~', _YELLOW, use_colour)} {key}: {old} -> {new}")

    return "\n".join(lines) + "\n"


def render_snapshot_report(
    deltas: List[SnapshotDelta], use_colour: bool = True
) -> str:
    if not deltas:
        return "No snapshot deltas to report.\n"

    changed = [d for d in deltas if d.has_changes]
    header = _colour(
        f"Snapshot Delta Report — {len(changed)}/{len(deltas)} resources changed",
        _BOLD,
        use_colour,
    )
    lines = [header, ""]
    for delta in deltas:
        lines.append(format_delta(delta, use_colour=use_colour))
    return "\n".join(lines)


def print_snapshot_report(
    deltas: List[SnapshotDelta], use_colour: bool = True
) -> None:
    print(render_snapshot_report(deltas, use_colour=use_colour))
