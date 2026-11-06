#!/usr/bin/env python3
"""Classify protected changes. CI runs the BASE-branch copy, not the PR copy.
This emits a required-review signal; it is not an approval service.
"""
import argparse
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import subprocess
import sys

PROTECTED = (
    "AGENTS.md", "agents.md", "pom.xml", "*/pom.xml", "config/*", "tools/*",
    ".github/*", ".mvn/*", "Jenkinsfile", ".gitlab-ci.yml", "mvnw*", ".gitattributes",
    ".editorconfig", "*/src/test/*", "experiments/*", "docs/adr/*", "docs/issues/*",
    "mise*.toml", "mise*.lock", ".mise*.toml", ".mise*.lock", "mise-tasks/*", ".mise/*",
)


def protected(path):
    return any(fnmatchcase(path, pattern) for pattern in PROTECTED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--fail-on-change", action="store_true")
    args = parser.parse_args()
    try:
        # Resolve to object ids before building commands; no shell interpolation.
        def resolve(ref):
            if ref.startswith("-"):
                raise ValueError("Invalid ref")
            return subprocess.check_output(["git", "rev-parse", "--verify", ref + "^{commit}"], text=True).strip()
        base, head = resolve(args.base), resolve(args.head)
        output = subprocess.check_output(["git", "diff", "--no-renames", "--name-only", "-z", base, head])
        paths = [name.decode("utf-8") for name in output.split(b"\0") if name]
        changed = sorted(path for path in paths if protected(path))
        print(json.dumps({"base": base, "head": head, "reviewRequired": bool(changed), "paths": changed}, indent=2))
        if os.environ.get("GITHUB_OUTPUT"):
            with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
                stream.write("protected=" + str(bool(changed)).lower() + "\n")
        return 1 if changed and args.fail_on_change else 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Cannot determine policy scope: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
