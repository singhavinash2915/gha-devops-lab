"""Print the services changed between two commits as a JSON list for a GitHub Actions matrix.

Env: BASE_SHA (may be empty or all zeros), HEAD_SHA (default HEAD), SERVICES_ROOT (default 'services').
Writes `services=<json>` to $GITHUB_OUTPUT when it is set.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ZERO_SHA = "0" * 40


def git_lines(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def changed_files(base: str, head: str) -> list[str]:
    if not base or base == ZERO_SHA:
        # new branch, first push or unknown base: treat every tracked file as changed
        return git_lines("ls-files")
    return git_lines("diff", "--name-only", base, head)


def services_from_files(files: list[str], root: str = "services") -> list[str]:
    found = set()
    for f in files:
        parts = Path(f).parts
        if len(parts) >= 3 and parts[0] == root:   # services/<name>/<file>
            found.add(parts[1])
    # ignore services that were deleted in this change
    return sorted(s for s in found if (Path(root) / s).is_dir())


def main() -> int:
    base = os.environ.get("BASE_SHA", "")
    head = os.environ.get("HEAD_SHA", "HEAD")
    root = os.environ.get("SERVICES_ROOT", "services")
    try:
        services = services_from_files(changed_files(base, head), root)
    except subprocess.CalledProcessError as exc:
        print(f"::error::git failed: {exc.stderr.strip()}")
        return 1
    payload = json.dumps(services)
    print(f"Changed services: {payload}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"services={payload}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
