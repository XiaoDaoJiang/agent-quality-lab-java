"""Validate shared tool declarations and the two supported platform locks (Python 3.12 task)."""
from pathlib import Path
import re
import subprocess
import sys


def validate(config, lock):
    errors = []
    requested = []
    for name, value in config["tools"].items():
        for entry in value if isinstance(value, list) else [value]:
            version = entry if isinstance(entry, str) else entry.get("version", "")
            if not re.fullmatch(r"(?:temurin-\d+\.\d+\.\d+\+\d+|zulu-\d+\.\d+\.\d+\.\d+|\d+\.\d+\.\d+)", version):
                errors.append("Not an exact downloadable version: " + name + "@" + version)
            if isinstance(entry, dict) and "path" in entry:
                errors.append("Machine paths are not allowed in shared tools: " + name)
            requested.append((name, version))
    shared = str(config)
    if "agentlab-" in shared or re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]|/(?:Users|home|opt|usr|mnt|tmp)/", shared):
        errors.append("Local alias or absolute machine path in shared configuration")
    for name, version in requested:
        entries = lock.get("tools", {}).get(name, [])
        entry = next((item for item in entries if item["version"] == version), {})
        # mise versions serialize platform tables in both nested and dotted-key forms.
        for platform in ("windows-x64", "linux-x64"):
            info = entry.get("platforms", {}).get(platform, entry.get("platforms." + platform, {}))
            if not info.get("url", "").startswith("https://") or not re.fullmatch(
                    r"(?:sha256:[0-9a-f]{64}|sha512:[0-9a-f]{128})", info.get("checksum", "")):
                errors.append("Missing locked HTTPS URL/checksum: " + name + "@" + version + " " + platform)
    for name in ("check:8", "check:11", "check:17", "check:21"):
        task = config["tasks"][name]
        if task["run"] != ["python tools/lab.py doctor", "python tools/lab.py verify",
                           "python tools/lab.py fixtures",
                           "python tools/http_smoke.py --jar app/target/app-0.2.0-SNAPSHOT.jar"]:
            errors.append("Incomplete or reordered runtime lane: " + name)
    if config["tasks"].get("verify", {}).get("run") != "python tools/lab.py verify":
        errors.append("verify must execute the real quality gate")
    if config["tasks"]["matrix"]["run"] != [
            {"task": "check:" + version} for version in ("8", "11", "17", "21")] + [{"task": "compile:25"}]:
        errors.append("Acceptance matrix is incomplete or reordered")
    return errors


def main():
    from datetime import datetime, timezone
    import os
    import tomllib
    from toolchain_environment import save_environment
    root = Path(__file__).resolve().parents[1]
    save_environment(root, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"), require_build=False)
    config = tomllib.loads((root / "mise.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((root / "mise.lock").read_text(encoding="utf-8"))
    errors = validate(config, lock)
    if os.environ.get("CI") and list(root.glob("mise*.local.toml")):
        errors.append("CI must not load local mise overrides")
    tracked = subprocess.check_output(["git", "ls-files", "--", "mise*.local.toml", "mise*.local.lock"], cwd=root)
    if tracked.strip():
        errors.append("Local mise overrides must not be tracked")
    for error in errors:
        print("MISE CONFIG ERROR:", error, file=sys.stderr)
    if not errors:
        print("MISE CONFIG PASSED: exact shared versions and Windows/Linux artifact locks")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
