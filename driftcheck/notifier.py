"""Notification module for surfacing drift alerts via multiple channels."""

from dataclasses import dataclass, field
from typing import List, Optional
from driftcheck.reporter import DriftReport


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""
    channel: str  # 'console', 'slack', 'webhook'
    webhook_url: Optional[str] = None
    min_drift_count: int = 1
    mention: Optional[str] = None


def _build_summary(report: DriftReport) -> str:
    lines = [
        f"DriftCheck Summary: {report.drifted}/{report.total} resources drifted",
    ]
    for result in report.results:
        if result.drifted:
            lines.append(f"  [DRIFT] {result.resource_id} ({result.resource_type})")
            for diff in result.diffs:
                lines.append(
                    f"    - {diff.field}: planned={diff.planned!r}, live={diff.live!r}"
                )
    return "\n".join(lines)


def notify_console(report: DriftReport, config: NotificationConfig) -> bool:
    """Print drift summary to stdout. Returns True if notification was sent."""
    if report.drift_count < config.min_drift_count:
        return False
    print(_build_summary(report))
    return True


def notify_webhook(report: DriftReport, config: NotificationConfig) -> bool:
    """POST drift summary to a webhook URL. Returns True if successful."""
    import urllib.request
    import json

    if not config.webhook_url:
        raise ValueError("webhook_url is required for webhook notifications")
    if report.drift_count < config.min_drift_count:
        return False

    payload = {
        "text": _build_summary(report),
        "drift_count": report.drift_count,
        "total": report.total,
    }
    if config.mention:
        payload["mention"] = config.mention

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        config.webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status == 200


def dispatch(report: DriftReport, configs: List[NotificationConfig]) -> dict:
    """Dispatch notifications for all configured channels.

    Returns a dict mapping channel -> bool (sent or not).
    """
    results = {}
    for config in configs:
        if config.channel == "console":
            results["console"] = notify_console(report, config)
        elif config.channel in ("slack", "webhook"):
            results[config.channel] = notify_webhook(report, config)
        else:
            raise ValueError(f"Unknown notification channel: {config.channel!r}")
    return results
