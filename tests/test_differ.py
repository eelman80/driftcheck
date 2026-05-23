"""Tests for driftcheck.differ."""

import pytest

from driftcheck.differ import AttributeDiff, diff_attributes, summarise_diffs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def planned() -> dict:
    return {
        "bucket": "my-bucket",
        "region": "us-east-1",
        "versioning": True,
        "acl": "private",
    }


@pytest.fixture()
def live_same(planned) -> dict:
    return dict(planned)


@pytest.fixture()
def live_changed() -> dict:
    return {
        "bucket": "my-bucket",
        "region": "eu-west-1",   # changed
        "versioning": False,      # changed
        # 'acl' removed from live
        "extra_tag": "surprise",  # added in live
    }


# ---------------------------------------------------------------------------
# diff_attributes
# ---------------------------------------------------------------------------

def test_no_diffs_when_equal(planned, live_same):
    result = diff_attributes(planned, live_same)
    assert result == []


def test_detects_changed_values(planned, live_changed):
    diffs = diff_attributes(planned, live_changed)
    changed = {d.attribute: d for d in diffs if d.severity == "change"}
    assert "region" in changed
    assert changed["region"].planned == "us-east-1"
    assert changed["region"].live == "eu-west-1"
    assert "versioning" in changed


def test_detects_added_key(planned, live_changed):
    diffs = diff_attributes(planned, live_changed)
    added = [d for d in diffs if d.severity == "added"]
    assert len(added) == 1
    assert added[0].attribute == "extra_tag"
    assert added[0].planned is None


def test_detects_removed_key(planned, live_changed):
    diffs = diff_attributes(planned, live_changed)
    removed = [d for d in diffs if d.severity == "removed"]
    assert len(removed) == 1
    assert removed[0].attribute == "acl"
    assert removed[0].live is None


def test_ignore_keys_skipped(planned, live_changed):
    diffs = diff_attributes(planned, live_changed, ignore_keys=["region", "versioning"])
    attributes = {d.attribute for d in diffs}
    assert "region" not in attributes
    assert "versioning" not in attributes


def test_empty_dicts():
    assert diff_attributes({}, {}) == []


def test_to_dict():
    d = AttributeDiff("region", "us-east-1", "eu-west-1", severity="change")
    result = d.to_dict()
    assert result["attribute"] == "region"
    assert result["planned"] == "us-east-1"
    assert result["live"] == "eu-west-1"
    assert result["severity"] == "change"


# ---------------------------------------------------------------------------
# summarise_diffs
# ---------------------------------------------------------------------------

def test_summarise_empty():
    summary = summarise_diffs([])
    assert summary == {"change": 0, "added": 0, "removed": 0}


def test_summarise_counts(planned, live_changed):
    diffs = diff_attributes(planned, live_changed)
    summary = summarise_diffs(diffs)
    assert summary["change"] == 2
    assert summary["added"] == 1
    assert summary["removed"] == 1
