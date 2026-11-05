#!/usr/bin/env python3
"""A fixed entry point for humans and coding agents. No skip/ignore-failure switches."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def maven_command():
    wrapper = ROOT / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    if wrapper.exists():
        return [str(wrapper)]
    executable = shutil.which("mvn.cmd" if os.name == "nt" else "mvn")
    if not executable:
        raise RuntimeError("Install Maven 3.6.3+ (<4); see README. No fabricated mvnw launcher is bundled.")
    return [executable]


def run(command):
    print("RUN:", subprocess.list2cmdline([str(x) for x in command]), flush=True)
    start = time.monotonic()
    completed = subprocess.run(command, cwd=ROOT, check=False)
    record = {"command": [str(x) for x in command], "exitCode": completed.returncode,
              "elapsedSeconds": round(time.monotonic()-start, 3),
              "finishedAt": datetime.now(timezone.utc).isoformat()}
    target = ROOT/".lab/runs"/RUN_ID
    target.mkdir(parents=True, exist_ok=True)
    with (target/"command-evidence.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(record)+"\n")
    if completed.returncode:
        raise subprocess.CalledProcessError(completed.returncode, command)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "selftest", "format", "verify", "fixtures", "compile"))
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            print("Python:", sys.version, "\nJAVA_HOME:", os.environ.get("JAVA_HOME", "(unset)"))
            run(["java", "-version"])
            run(maven_command()+["-version"])
            run([sys.executable, "tools/quality_gate.py", "metadata"])
            return 0
        if args.command == "selftest":
            run([sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py", "-v"])
            return 0
        if args.command == "fixtures":
            run([sys.executable, "tools/verify_fixtures.py"])
            return 0
        command = maven_command()+["-B", "-Dquality.python="+sys.executable]
        if args.command == "format":
            run(command+["spotless:apply"])
            return 0
        if args.command == "compile":
            run(command+["clean", "package", "-DskipTests"])
            run([sys.executable, "tools/audit_results.py", "--compile-only", "--modules", "domain-core", "app"])
            return 0
        run([sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"])
        # Always clean: never accept an old report from a previous run as evidence.
        run(command+["clean", "verify"])
        modules = ["domain-core", "app"]
        run([sys.executable, "tools/audit_results.py", "--modules"]+modules)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"LAB FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
