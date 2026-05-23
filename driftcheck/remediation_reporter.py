"""Formats and renders RemediationHint lists for human-readable output."""

from typing import List

from driftcheck.remediation import RemediationHint


def _section(title: str, content: str) -> str:
    return f"  [{title}]\n    {content}"


def format_hint(hint: RemediationHint) -> str:
    """Return a human-readable block for a single RemediationHint."""
    lines = [
        f"Resource : {hint.resource_type} / {hint.resource_id}",
        f"Field    : {hint.field}",
        f"Expected : {hint.expected}",
        f"Actual   : {hint.actual}",
    ]
    if hint.terraform_snippet:
        lines.append(_section("Terraform fix", hint.terraform_snippet.replace("\n", "\n    ")))
    if hint.aws_cli_command:
        lines.append(_section("AWS CLI fix", hint.aws_cli_command))
    return "\n".join(lines)


def render_report(hints: List[RemediationHint], *, use_color: bool = False) -> str:
    """Render all hints as a printable report string."""
    if not hints:
        return "No remediation hints — infrastructure matches plan.\n"

    sep = "\n" + "-" * 60 + "\n"
    blocks = [format_hint(h) for h in hints]
    header = f"Remediation Hints ({len(hints)} issue(s) found)"
    if use_color:
        header = f"\033[1;33m{header}\033[0m"
    return header + "\n" + sep.join(blocks) + "\n"


def print_report(hints: List[RemediationHint], *, use_color: bool = False) -> None:
    """Print the remediation report to stdout."""
    print(render_report(hints, use_color=use_color))
