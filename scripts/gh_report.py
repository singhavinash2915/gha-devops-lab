#!/usr/bin/env python3
"""Report failed GitHub Actions runs and optionally delete old artifacts.

Usage:
  GITHUB_TOKEN=... python scripts/gh_report.py --repo owner/name --days 7
  GITHUB_TOKEN=... python scripts/gh_report.py --repo owner/name --cleanup-older-than 14 --apply
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
log = logging.getLogger("gh-report")


def make_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET", "DELETE"])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def paginate(session, url: str, key: str, params: dict | None = None) -> Iterator[dict]:
    """Yield items across all pages by following the Link: rel="next" header."""
    params = {"per_page": 100, **(params or {})}
    while url:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        yield from resp.json()[key]
        url = resp.links.get("next", {}).get("url")
        params = None  # the next URL already contains the query string


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def failed_runs(session, repo: str, since: datetime) -> list[dict]:
    url = f"{API}/repos/{repo}/actions/runs"
    params = {"status": "failure", "created": f">={since:%Y-%m-%d}"}
    return [
        {"name": r["name"], "branch": r["head_branch"], "created": r["created_at"], "url": r["html_url"]}
        for r in paginate(session, url, "workflow_runs", params)
    ]


def old_artifacts(artifacts: list[dict], now: datetime, days: int) -> list[dict]:
    """Pure function: pick non-expired artifacts older than `days`."""
    cutoff = now - timedelta(days=days)
    return [a for a in artifacts if not a.get("expired") and parse_ts(a["created_at"]) < cutoff]


def write_summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    text = "\n".join(lines) + "\n"
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
    print(text)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"), help="owner/name")
    p.add_argument("--days", type=int, default=7, help="look back this many days for failed runs")
    p.add_argument("--cleanup-older-than", type=int, help="delete artifacts older than N days")
    p.add_argument("--apply", action="store_true", help="really delete (default is dry run)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(levelname)s %(message)s")
    args = parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    if not token or not args.repo:
        log.error("GITHUB_TOKEN and --repo (or GITHUB_REPOSITORY) are required")
        return 2

    session = make_session(token)
    now = datetime.now(timezone.utc)

    runs = failed_runs(session, args.repo, now - timedelta(days=args.days))
    lines = [f"## Failed runs in the last {args.days} days: {len(runs)}", "",
             "| Workflow | Branch | Created |", "| --- | --- | --- |"]
    lines += [f"| [{r['name']}]({r['url']}) | {r['branch']} | {r['created']} |" for r in runs]

    if args.cleanup_older_than is not None:
        artifacts = list(paginate(session, f"{API}/repos/{args.repo}/actions/artifacts", "artifacts"))
        doomed = old_artifacts(artifacts, now, args.cleanup_older_than)
        freed_mb = sum(a["size_in_bytes"] for a in doomed) / 1_048_576
        mode = "Deleted" if args.apply else "Would delete (dry run)"
        lines += ["", f"## {mode}: {len(doomed)} artifacts, {freed_mb:.1f} MB"]
        for a in doomed:
            if args.apply:
                resp = session.delete(f"{API}/repos/{args.repo}/actions/artifacts/{a['id']}", timeout=30)
                resp.raise_for_status()
            log.info("%s artifact %s (%s)", "deleted" if args.apply else "would delete", a["name"], a["id"])

    write_summary(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
