"""High-level watch command wiring scheduler + audit log."""

import logging
from typing import Callable, Optional

from driftcheck.scheduler import DriftScheduler, ScheduleConfig
from driftcheck.audit_log import AuditEntry, append_entry
from driftcheck.reporter import DriftReport

logger = logging.getLogger(__name__)


def _make_check_fn(plan_path: str, resource_ids: list) -> Callable:
    """Build a callable that runs a full drift check and returns a DriftReport."""
    from driftcheck.parser import parse_plan
    from driftcheck.fetcher import fetch_s3_bucket
    from driftcheck.comparator import compare
    from driftcheck.reporter import DriftReport

    def _check() -> DriftReport:
        planned = parse_plan(plan_path)
        results = []
        for res in planned:
            if res.resource_type == "aws_s3_bucket" and res.resource_id in resource_ids:
                live = fetch_s3_bucket(res.resource_id)
                results.append(compare(res, live))
        return DriftReport(results)

    return _check


def watch(
    check_fn: Callable,
    interval: int = 3600,
    max_runs: Optional[int] = None,
    log_path: str = "drift_audit.log",
    on_drift: Optional[Callable] = None,
) -> None:
    """Start a watch loop, logging each run to the audit log."""

    def _log_run(report: DriftReport) -> None:
        entry = AuditEntry.from_report(report)
        append_entry(entry, path=log_path)
        logger.info("Audit entry written: drifted=%s count=%d", entry.drifted, entry.drift_count)

    def _on_drift_wrapper(report: DriftReport) -> None:
        _log_run(report)
        if on_drift:
            on_drift(report)

    def _on_clean(report: DriftReport) -> None:
        _log_run(report)

    def _on_error(exc: Exception) -> None:
        entry = AuditEntry(
            run_at=__import__("datetime").datetime.utcnow().isoformat(),
            drifted=False,
            drift_count=0,
            resources_checked=0,
            error=str(exc),
        )
        append_entry(entry, path=log_path)
        logger.error("Error during drift check: %s", exc)

    config = ScheduleConfig(
        interval_seconds=interval,
        max_runs=max_runs,
        on_drift=_on_drift_wrapper,
        on_clean=_on_clean,
        on_error=_on_error,
    )
    scheduler = DriftScheduler(check_fn, config)
    scheduler.start()
