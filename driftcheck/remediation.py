"""Remediation hints: maps drift fields to suggested AWS CLI / Terraform commands."""

from dataclasses import dataclass, field
from typing import List, Optional

from driftcheck.comparator import DriftResult, FieldDiff


@dataclass
class RemediationHint:
    resource_id: str
    resource_type: str
    field: str
    expected: object
    actual: object
    terraform_snippet: Optional[str] = None
    aws_cli_command: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "terraform_snippet": self.terraform_snippet,
            "aws_cli_command": self.aws_cli_command,
        }


_TF_TEMPLATES = {
    "aws_s3_bucket": {
        "tags": 'resource "aws_s3_bucket" "{id}" {{\n  tags = {expected}\n}}',
        "versioning": 'resource "aws_s3_bucket_versioning" "{id}" {{\n  versioning_configuration {{\n    status = "{expected}"\n  }}\n}}',
    },
    "aws_instance": {
        "instance_type": 'resource "aws_instance" "{id}" {{\n  instance_type = "{expected}"\n}}',
        "tags": 'resource "aws_instance" "{id}" {{\n  tags = {expected}\n}}',
    },
}

_CLI_TEMPLATES = {
    "aws_s3_bucket": {
        "tags": "aws s3api put-bucket-tagging --bucket {id} --tagging 'TagSet={expected}'",
        "versioning": "aws s3api put-bucket-versioning --bucket {id} --versioning-configuration Status={expected}",
    },
    "aws_instance": {
        "instance_type": "aws ec2 modify-instance-attribute --instance-id {id} --instance-type Value={expected}",
        "tags": "aws ec2 create-tags --resources {id} --tags {expected}",
    },
}


def _render(template: str, resource_id: str, expected: object) -> str:
    return template.format(id=resource_id, expected=expected)


def build_hints(result: DriftResult) -> List[RemediationHint]:
    """Return a list of RemediationHint objects for every drifted field in *result*."""
    if not result.drifted:
        return []

    hints: List[RemediationHint] = []
    rtype = result.resource_type
    rid = result.resource_id

    for diff in result.diffs:
        tf_tmpl = _TF_TEMPLATES.get(rtype, {}).get(diff.field)
        cli_tmpl = _CLI_TEMPLATES.get(rtype, {}).get(diff.field)

        hints.append(
            RemediationHint(
                resource_id=rid,
                resource_type=rtype,
                field=diff.field,
                expected=diff.expected,
                actual=diff.actual,
                terraform_snippet=_render(tf_tmpl, rid, diff.expected) if tf_tmpl else None,
                aws_cli_command=_render(cli_tmpl, rid, diff.expected) if cli_tmpl else None,
            )
        )

    return hints


def batch_hints(results: List[DriftResult]) -> List[RemediationHint]:
    """Collect hints across multiple DriftResult objects."""
    out: List[RemediationHint] = []
    for r in results:
        out.extend(build_hints(r))
    return out
