"""Tests for driftcheck.notifier."""

import json
import pytest
from unittest.mock import patch, MagicMock

from driftcheck.notifier import (
    NotificationConfig,
    _build_summary,
    notify_console,
    notify_webhook,
    dispatch,
)
from driftcheck.reporter import DriftReport
from driftcheck.comparator import DriftResult, FieldDiff


@pytest.fixture
def clean_result():
    return DriftResult(
        resource_id="bucket-clean",
        resource_type="aws_s3_bucket",
        drifted=False,
        diffs=[],
    )


@pytest.fixture
def drifted_result():
    return DriftResult(
        resource_id="bucket-drift",
        resource_type="aws_s3_bucket",
        drifted=True,
        diffs=[
            FieldDiff(field="region", planned="us-east-1", live="eu-west-1"),
        ],
    )


@pytest.fixture
def mixed_report(clean_result, drifted_result):
    return DriftReport(results=[clean_result, drifted_result])


@pytest.fixture
def clean_report(clean_result):
    return DriftReport(results=[clean_result])


def test_build_summary_contains_drift_info(mixed_report):
    summary = _build_summary(mixed_report)
    assert "1/2 resources drifted" in summary
    assert "bucket-drift" in summary
    assert "region" in summary
    assert "us-east-1" in summary
    assert "eu-west-1" in summary


def test_build_summary_no_drift(clean_report):
    summary = _build_summary(clean_report)
    assert "0/1 resources drifted" in summary
    assert "DRIFT" not in summary


def test_notify_console_sends(mixed_report, capsys):
    config = NotificationConfig(channel="console", min_drift_count=1)
    sent = notify_console(mixed_report, config)
    assert sent is True
    captured = capsys.readouterr()
    assert "bucket-drift" in captured.out


def test_notify_console_skips_below_threshold(mixed_report, capsys):
    config = NotificationConfig(channel="console", min_drift_count=5)
    sent = notify_console(mixed_report, config)
    assert sent is False
    captured = capsys.readouterr()
    assert captured.out == ""


def test_notify_webhook_missing_url_raises(mixed_report):
    config = NotificationConfig(channel="webhook")
    with pytest.raises(ValueError, match="webhook_url"):
        notify_webhook(mixed_report, config)


def test_notify_webhook_posts_payload(mixed_report):
    config = NotificationConfig(
        channel="webhook",
        webhook_url="http://example.com/hook",
        min_drift_count=1,
    )
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        result = notify_webhook(mixed_report, config)

    assert result is True
    called_req = mock_open.call_args[0][0]
    body = json.loads(called_req.data.decode())
    assert body["drift_count"] == 1
    assert "bucket-drift" in body["text"]


def test_notify_webhook_skips_below_threshold(mixed_report):
    config = NotificationConfig(
        channel="webhook",
        webhook_url="http://example.com/hook",
        min_drift_count=10,
    )
    with patch("urllib.request.urlopen") as mock_open:
        result = notify_webhook(mixed_report, config)
    assert result is False
    mock_open.assert_not_called()


def test_dispatch_console(mixed_report, capsys):
    configs = [NotificationConfig(channel="console", min_drift_count=1)]
    results = dispatch(mixed_report, configs)
    assert results["console"] is True


def test_dispatch_unknown_channel_raises(mixed_report):
    configs = [NotificationConfig(channel="pagerduty")]
    with pytest.raises(ValueError, match="Unknown notification channel"):
        dispatch(mixed_report, configs)
