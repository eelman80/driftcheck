"""Human-readable report renderer for scored drift results."""

from typing import List

from driftcheck.scorer import ScoredResult

_SEVERITY_COLOURS = {
    "critical": "\033[91m",  # bright red
    "high": "\033[33m",      # yellow
    "medium": "\033[94m",    # blue
    "low": "\033[37m",       # light grey
    "none": "\033[32m",      # green
}
_RESET = "\033[0m"


def _colour(text: str, severity: str, use_colour: bool) -> str:
    if not use_colour:
        return text
    colour = _SEVERITY_COLOURS.get(severity, "")
    return f"{colour}{text}{_RESET}"


def format_scored(scored: ScoredResult, use_colour: bool = True) -> str:
    lines = []
    header = f"[{scored.severity.upper():8s}] {scored.result.resource_id}  score={scored.score}/100"
    lines.append(_colour(header, scored.severity, use_colour))
    for reason in scored.reasons:
        lines.append(f"    • {reason}")
    return "\n".join(lines)


def render_score_report(scored_results: List[ScoredResult], use_colour: bool = True) -> str:
    if not scored_results:
        return _colour("✔ No drift detected — all resources scored clean.", "none", use_colour)

    total_score = sum(s.score for s in scored_results)
    lines = [
        f"Drift Score Report  ({len(scored_results)} drifted resource(s)  total score={total_score})",
        "-" * 60,
    ]
    for scored in scored_results:
        lines.append(format_scored(scored, use_colour=use_colour))
        lines.append("")
    return "\n".join(lines).rstrip()


def print_score_report(scored_results: List[ScoredResult], use_colour: bool = True) -> None:
    print(render_score_report(scored_results, use_colour=use_colour))
