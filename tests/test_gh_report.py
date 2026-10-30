from datetime import datetime, timezone
from unittest import mock

import gh_report


def fake_response(payload, next_url=None):
    resp = mock.Mock()
    resp.json.return_value = payload
    resp.links = {"next": {"url": next_url}} if next_url else {}
    resp.raise_for_status.return_value = None
    return resp


def test_paginate_follows_next_links():
    session = mock.Mock()
    session.get.side_effect = [
        fake_response({"artifacts": [{"id": 1}, {"id": 2}]}, next_url="https://api/page2"),
        fake_response({"artifacts": [{"id": 3}]}),
    ]
    items = list(gh_report.paginate(session, "https://api/page1", "artifacts"))
    assert [i["id"] for i in items] == [1, 2, 3]
    assert session.get.call_count == 2
    # the second call uses the next URL and does not re-send params
    assert session.get.call_args_list[1].kwargs["params"] is None


def test_old_artifacts_selects_by_age_and_skips_expired():
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)
    artifacts = [
        {"id": 1, "created_at": "2026-10-01T00:00:00Z", "expired": False},  # old -> delete
        {"id": 2, "created_at": "2026-10-30T00:00:00Z", "expired": False},  # new -> keep
        {"id": 3, "created_at": "2026-09-01T00:00:00Z", "expired": True},   # already expired
    ]
    assert [a["id"] for a in gh_report.old_artifacts(artifacts, now, days=14)] == [1]


def test_main_requires_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert gh_report.main(["--repo", "o/r"]) == 2
