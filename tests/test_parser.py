"""Tests for driftcheck.parser."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from driftcheck.parser import parse_plan, PlannedResource


SAMPLE_PLAN = {
    "format_version": "1.0",
    "planned_values": {
        "root_module": {
            "resources": [
                {
                    "address": "aws_instance.web",
                    "type": "aws_instance",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "values": {
                        "ami": "ami-0c55b159cbfafe1f0",
                        "instance_type": "t2.micro",
                        "tags": {"Name": "web-server"},
                    },
                }
            ],
            "child_modules": [
                {
                    "resources": [
                        {
                            "address": "module.db.aws_db_instance.main",
                            "type": "aws_db_instance",
                            "name": "main",
                            "provider_name": "registry.terraform.io/hashicorp/aws",
                            "values": {"engine": "postgres", "engine_version": "14.3"},
                        }
                    ],
                    "child_modules": [],
                }
            ],
        }
    },
}


@pytest.fixture()
def plan_file(tmp_path: Path) -> Path:
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(SAMPLE_PLAN))
    return p


def test_parse_plan_returns_resources(plan_file: Path) -> None:
    resources = parse_plan(plan_file)
    assert len(resources) == 2


def test_parse_plan_root_resource(plan_file: Path) -> None:
    resources = parse_plan(plan_file)
    root = next(r for r in resources if r.address == "aws_instance.web")
    assert isinstance(root, PlannedResource)
    assert root.resource_type == "aws_instance"
    assert root.name == "web"
    assert root.values["instance_type"] == "t2.micro"


def test_parse_plan_child_module_resource(plan_file: Path) -> None:
    resources = parse_plan(plan_file)
    child = next(r for r in resources if r.address == "module.db.aws_db_instance.main")
    assert child.resource_type == "aws_db_instance"
    assert child.values["engine"] == "postgres"


def test_parse_plan_file_not_found() -> None:
    with pytest.raises(FileNotFoundError, match="Plan file not found"):
        parse_plan("/nonexistent/plan.json")


def test_parse_plan_invalid_plan(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"format_version": "1.0"}))
    with pytest.raises(ValueError, match="Invalid Terraform plan"):
        parse_plan(bad)
