#!/usr/bin/env python3
"""Delete old, unprotected images from an ECR repository (dry run by default).

Rules: keep the newest --keep-last images, keep any image carrying a --keep-tag,
and delete the remaining images pushed more than --days ago.
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

log = logging.getLogger("ecr-cleanup")
BATCH = 100  # batch_delete_image accepts at most 100 image IDs per call


def fetch_images(ecr, repo: str) -> list[dict]:
    paginator = ecr.get_paginator("describe_images")
    images = []
    for page in paginator.paginate(repositoryName=repo):
        images.extend(page["imageDetails"])
    return images


def select_for_deletion(images: list[dict], now: datetime, days: int,
                        keep_tags: set[str], keep_last: int) -> list[dict]:
    """Pure decision logic (no AWS calls), so it is trivial to unit test."""
    newest_first = sorted(images, key=lambda i: i["imagePushedAt"], reverse=True)
    protected = {i["imageDigest"] for i in newest_first[:keep_last]}
    cutoff = now - timedelta(days=days)
    doomed = []
    for img in newest_first:
        tags = set(img.get("imageTags", []))
        if img["imageDigest"] in protected or tags & keep_tags:
            continue
        if img["imagePushedAt"] < cutoff:
            doomed.append(img)
    return doomed


def delete_images(ecr, repo: str, images: list[dict]) -> int:
    failures = 0
    ids = [{"imageDigest": i["imageDigest"]} for i in images]
    for start in range(0, len(ids), BATCH):
        resp = ecr.batch_delete_image(repositoryName=repo, imageIds=ids[start:start + BATCH])
        for failure in resp.get("failures", []):
            failures += 1
            log.error("failed to delete %s: %s", failure.get("imageId"), failure.get("failureReason"))
    return failures


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True)
    p.add_argument("--region", default=None)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--keep-last", type=int, default=10)
    p.add_argument("--keep-tag", action="append", default=["latest"], help="repeatable")
    p.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    return p.parse_args(argv)


def main(argv=None, ecr=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    ecr = ecr or boto3.client("ecr", region_name=args.region)
    try:
        images = fetch_images(ecr, args.repo)
        doomed = select_for_deletion(images, datetime.now(timezone.utc), args.days,
                                     set(args.keep_tag), args.keep_last)
        log.info("%d images total, %d selected for deletion", len(images), len(doomed))
        for img in doomed:
            log.info("%s %s %s", "DELETE" if args.apply else "WOULD DELETE",
                     img["imageDigest"][:19], img.get("imageTags", ["<untagged>"]))
        if args.apply and doomed:
            return 1 if delete_images(ecr, args.repo, doomed) else 0
        return 0
    except (ClientError, BotoCoreError) as exc:
        log.error("AWS error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
