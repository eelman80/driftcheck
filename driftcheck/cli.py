"""CLI entry point for driftcheck."""

import argparse
import sys
from typing import List, Optional

from driftcheck.parser import parse_plan
from driftcheck.fetcher import fetch_s3_bucket, fetch_ec2_instance
from driftcheck.comparator import compare
from driftcheck.reporter import DriftReport
from driftcheck.exporter import export_to_file
from driftcheck.notifier import NotificationConfig, dispatch


FETCHERS = {
    "aws_s3_bucket": fetch_s3_bucket,
    "aws_instance": fetch_ec2_instance,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="driftcheck",
        description="Compare live infrastructure against Terraform plans.",
    )
    p.add_argument("plan", help="Path to terraform show -json output")
    p.add_argument(
        "--output", "-o",
        help="Export results to file (.json or .csv)",
        default=None,
    )
    p.add_argument(
        "--notify",
        choices=["console", "slack", "webhook"],
        nargs="*",
        default=[],
        help="Notification channels to use on drift",
    )
    p.add_argument(
        "--webhook-url",
        default=None,
        help="Webhook URL for slack/webhook notifications",
    )
    p.add_argument(
        "--min-drift",
        type=int,
        default=1,
        help="Minimum drift count before sending notifications (default: 1)",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if drift is detected",
    )
    return p


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        planned = parse_plan(args.plan)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    results = []
    for resource in planned:
        fetcher = FETCHERS.get(resource.resource_type)
        if fetcher is None:
            continue
        live = fetcher(resource.resource_id)
        results.append(compare(resource, live))

    report = DriftReport(results=results)

    if args.output:
        export_to_file(report, args.output)
        print(f"Results written to {args.output}")

    if args.notify:
        configs = [
            NotificationConfig(
                channel=ch,
                webhook_url=args.webhook_url,
                min_drift_count=args.min_drift,
            )
            for ch in args.notify
        ]
        dispatch(report, configs)

    print(f"Checked {report.total} resource(s): {report.drift_count} drifted.")

    if args.exit_code and report.drift_count > 0:
        return 1
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
