"""Tests for driftcheck.cli."""

import json
import pytest
from unittest.mock import patch, MagicMock

from driftcheck.cli import run, build_parser
from driftcheck.parser import PlannedResource
from driftcheck.fetcher import LiveResource
from driftcheck.comparator import DriftResult, FieldDiff


PLANNED_BUCKET = PlannedResource(
    resource_id="my-bucket",
    resource_type="aws_s3_bucket",
    attributes={"region": "us-east-1"},
)

LIVE_BUCKET_OK = LiveResource(
    resource_id="my-bucket",
    resource_type="aws_s3_bucket",
    attributes={"region": "us-east-1"},
)

LIVE_BUCKET_DRIFTED = LiveResource(
    resource_id="my-bucket",
    resource_type="aws_s3_bucket",
    attributes={"region": "eu-west-1"},
)


@pytest.fixture
def plan_file(tmp_path):
    data = {
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_s3_bucket.my-bucket",
                        "type": "aws_s3_bucket",
                        "name": "my-bucket",
                        "values": {"region": "us-east-1"},
                    }
                ]
            }
        }
    }
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_run_no_drift(plan_file, capsys):
    with patch("driftcheck.cli.fetch_s3_bucket", return_value=LIVE_BUCKET_OK):
        code = run([plan_file])
    assert code == 0
    out = capsys.readouterr().out
    assert "0 drifted" in out


def test_run_with_drift(plan_file, capsys):
    with patch("driftcheck.cli.fetch_s3_bucket", return_value=LIVE_BUCKET_DRIFTED):
        code = run([plan_file])
    assert code == 0  # no --exit-code flag
    out = capsys.readouterr().out
    assert "1 drifted" in out


def test_run_exit_code_on_drift(plan_file):
    with patch("driftcheck.cli.fetch_s3_bucket", return_value=LIVE_BUCKET_DRIFTED):
        code = run([plan_file, "--exit-code"])
    assert code == 1


def test_run_exit_code_no_drift(plan_file):
    with patch("driftcheck.cli.fetch_s3_bucket", return_value=LIVE_BUCKET_OK):
        code = run([plan_file, "--exit-code"])
    assert code == 0


def test_run_file_not_found(capsys):
    code = run(["nonexistent_plan.json"])
    assert code == 2
    assert "ERROR" in capsys.readouterr().err


def test_run_with_output(plan_file, tmp_path):
    out_file = str(tmp_path / "results.json")
    with patch("driftcheck.cli.fetch_s3_bucket", return_value=LIVE_BUCKET_OK):
        with patch("driftcheck.cli.export_to_file") as mock_export:
            run([plan_file, "--output", out_file])
    mock_export.assert_called_once()


def test_run_with_notify_console(plan_file, capsys):
    with patch("driftcheck.cli.fetch_s3_bucket", return_value=LIVE_BUCKET_DRIFTED):
        code = run([plan_file, "--notify", "console"])
    assert code == 0
    out = capsys.readouterr().out
    assert "my-bucket" in out


def test_build_parser_defaults():
    p = build_parser()
    args = p.parse_args(["plan.json"])
    assert args.plan == "plan.json"
    assert args.output is None
    assert args.notify == []
    assert args.min_drift == 1
    assert args.exit_code is False
