import json
from datetime import datetime, timedelta, timezone

import boto3
from moto import mock_aws

import ecr_cleanup

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


def img(digest, days_old, tags=None):
    return {"imageDigest": digest, "imagePushedAt": NOW - timedelta(days=days_old), "imageTags": tags or []}


def test_selects_old_unprotected_images():
    images = [
        img("sha256:new", 1, ["v3"]),
        img("sha256:old-tagged", 60, ["v1"]),
        img("sha256:old-latest", 90, ["latest"]),
        img("sha256:old-untagged", 45),
    ]
    doomed = ecr_cleanup.select_for_deletion(images, NOW, days=30, keep_tags={"latest"}, keep_last=1)
    # newest first: the 45-day-old image comes before the 60-day-old one
    assert [i["imageDigest"] for i in doomed] == ["sha256:old-untagged", "sha256:old-tagged"]


def test_keep_last_protects_even_old_images():
    images = [img("sha256:a", 100), img("sha256:b", 200)]
    assert ecr_cleanup.select_for_deletion(images, NOW, days=30, keep_tags=set(), keep_last=2) == []


def test_nothing_old():
    assert ecr_cleanup.select_for_deletion([img("sha256:a", 1)], NOW, 30, set(), 0) == []


@mock_aws
def test_fetch_and_delete_against_moto():
    ecr = boto3.client("ecr", region_name="ap-south-1")
    ecr.create_repository(repositoryName="app")
    for n in range(3):
        # distinct layers -> distinct image digests (moto derives the digest from the manifest layers)
        layer = {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": 1,
                 "digest": f"sha256:{n:064d}"}
        manifest = {"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": {"digest": f"sha256:{n:064d}"}, "layers": [layer]}
        ecr.put_image(repositoryName="app", imageManifest=json.dumps(manifest), imageTag=f"v{n}")

    images = ecr_cleanup.fetch_images(ecr, "app")
    assert len(images) == 3

    assert ecr_cleanup.delete_images(ecr, "app", images[:2]) == 0
    assert len(ecr_cleanup.fetch_images(ecr, "app")) == 1


@mock_aws
def test_main_dry_run_deletes_nothing():
    ecr = boto3.client("ecr", region_name="ap-south-1")
    ecr.create_repository(repositoryName="app")
    assert ecr_cleanup.main(["--repo", "app", "--days", "0", "--keep-last", "0"], ecr=ecr) == 0
