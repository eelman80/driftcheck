"""Fetches live infrastructure state from AWS using boto3."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


@dataclass
class LiveResource:
    """Represents the live state of a single AWS resource."""

    resource_type: str
    resource_id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"LiveResource(type={self.resource_type!r}, id={self.resource_id!r})"


def fetch_s3_bucket(bucket_name: str, session: boto3.Session | None = None) -> LiveResource:
    """Fetch live attributes for an S3 bucket."""
    s3 = (session or boto3).client("s3")
    try:
        versioning = s3.get_bucket_versioning(Bucket=bucket_name)
        tagging_resp = s3.get_bucket_tagging(Bucket=bucket_name) if _has_tags(s3, bucket_name) else {}
        attributes = {
            "bucket": bucket_name,
            "versioning": versioning.get("Status", "Disabled"),
            "tags": {t["Key"]: t["Value"] for t in tagging_resp.get("TagSet", [])},
        }
        return LiveResource(resource_type="aws_s3_bucket", resource_id=bucket_name, attributes=attributes)
    except ClientError as exc:
        logger.error("Failed to fetch S3 bucket %s: %s", bucket_name, exc)
        raise


def _has_tags(s3_client: Any, bucket_name: str) -> bool:
    """Return True if the bucket has tags, suppressing NoSuchTagSet errors."""
    try:
        s3_client.get_bucket_tagging(Bucket=bucket_name)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchTagSet":
            return False
        raise


def fetch_resource(resource_type: str, resource_id: str, session: boto3.Session | None = None) -> LiveResource:
    """Dispatch to the appropriate fetcher based on resource_type."""
    fetchers = {
        "aws_s3_bucket": lambda rid: fetch_s3_bucket(rid, session),
    }
    if resource_type not in fetchers:
        raise NotImplementedError(f"No live fetcher implemented for resource type: {resource_type!r}")
    return fetchers[resource_type](resource_id)
