"""Scheduler for periodic drift checks."""

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    interval_seconds: int = 3600
    max_runs: Optional[int] = None
    on_drift: Optional[Callable] = None
    on_clean: Optional[Callable] = None
    on_error: Optional[Callable] = None


@dataclass
class RunRecord:
    run_at: datetime
    drifted: bool
    drift_count: int
    error: Optional[str] = None

    def __repr__(self) -> str:
        status = "ERROR" if self.error else ("DRIFTED" if self.drifted else "CLEAN")
        return f"RunRecord(at={self.run_at.isoformat()}, status={status}, drifts={self.drift_count})"


class DriftScheduler:
    def __init__(self, check_fn: Callable, config: ScheduleConfig):
        self.check_fn = check_fn
        self.config = config
        self.history: list[RunRecord] = []
        self._running = False

    def _execute_run(self) -> RunRecord:
        run_at = datetime.utcnow()
        try:
            report = self.check_fn()
            record = RunRecord(
                run_at=run_at,
                drifted=report.drifted > 0,
                drift_count=report.drift_count,
            )
            if record.drifted and self.config.on_drift:
                self.config.on_drift(report)
            elif not record.drifted and self.config.on_clean:
                self.config.on_clean(report)
        except Exception as exc:
            logger.error("Drift check failed: %s", exc)
            record = RunRecord(run_at=run_at, drifted=False, drift_count=0, error=str(exc))
            if self.config.on_error:
                self.config.on_error(exc)
        return record

    def run_once(self) -> RunRecord:
        record = self._execute_run()
        self.history.append(record)
        return record

    def start(self) -> None:
        self._running = True
        runs = 0
        logger.info("Scheduler started (interval=%ds)", self.config.interval_seconds)
        while self._running:
            record = self.run_once()
            runs += 1
            logger.info("Run #%d complete: %r", runs, record)
            if self.config.max_runs and runs >= self.config.max_runs:
                break
            time.sleep(self.config.interval_seconds)
        self._running = False

    def stop(self) -> None:
        self._running = False

    def next_run_at(self) -> Optional[datetime]:
        if not self.history:
            return datetime.utcnow()
        last = self.history[-1].run_at
        return last + timedelta(seconds=self.config.interval_seconds)
