"""GitHub Action: bump a semantic version.

Inputs  (env): INPUT_CURRENT, INPUT_PART (major|minor|patch)
Outputs:       new-version (written to $GITHUB_OUTPUT)
"""
import os
import re
import sys

SEMVER = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def bump(version: str, part: str = "patch") -> str:
    match = SEMVER.fullmatch(version.strip())
    if not match:
        raise ValueError(f"not a semantic version: {version!r}")
    major, minor, patch = (int(x) for x in match.groups())
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"part must be major, minor or patch, got {part!r}")


def set_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")
    else:  # running locally
        print(f"{name}={value}")


def write_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def main() -> int:
    current = os.environ.get("INPUT_CURRENT", "")
    part = os.environ.get("INPUT_PART", "patch")
    try:
        new_version = bump(current, part)
    except ValueError as exc:
        print(f"::error title=semver-bump::{exc}")
        return 1
    set_output("new-version", new_version)
    write_summary(f"### Version bump\n`{current}` → `{new_version}` ({part})")
    print(f"Bumped {current} -> {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
