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
            python_series = name == "python" and version == "3.12"
            if not python_series and not re.fullmatch(r"(?:temurin-\d+\.\d+\.\d+\+\d+|zulu-\d+\.\d+\.\d+\.\d+|\d+\.\d+\.\d+)", version):
                errors.append("Not an exact downloadable version: " + name + "@" + version)
            if isinstance(entry, dict) and "path" in entry:
                errors.append("Machine paths are not allowed in shared tools: " + name)
            requested.append((name, version))
    shared = str(config)
    if "agentlab-" in shared or re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]|/(?:Users|home|opt|usr|mnt|tmp)/", shared):
        errors.append("Local alias or absolute machine path in shared configuration")
    for name, version in requested:
        entries = lock.get("tools", {}).get(name, [])
        if name == "python" and version == "3.12":
            if lock.get("lockfile_version") != 4:
                errors.append("Python series requests require mise lockfile format 4")
            matches = [item for item in entries if version in item.get("specifiers", [])]
            entry = matches[0] if len(matches) == 1 else {}
            if not re.fullmatch(r"3\.12\.\d+", entry.get("version", "")):
                errors.append("Python 3.12 needs one exact 3.12.x lock with specifiers = [\"3.12\"]")
            if config.get("env", {}).get("LAB_EXPECTED_PYTHON") != version:
                errors.append("Python runtime expectation must match the shared 3.12 request")
        else:
            entry = next((item for item in entries if item["version"] == version), {})
        # mise versions serialize platform tables in both nested and dotted-key forms.
        for platform in ("windows-x64", "linux-x64"):
            info = entry.get("platforms", {}).get(platform, entry.get("platforms." + platform, {}))
            if name == "python" and version == "3.12" and info.get("provenance") != "github-attestations":
                errors.append("Missing Python GitHub attestation provenance: " + platform)
            if not info.get("url", "").startswith("https://") or not re.fullmatch(
                    r"(?:sha256:[0-9a-f]{64}|sha512:[0-9a-f]{128})", info.get("checksum", "")):
                errors.append("Missing locked HTTPS URL/checksum: " + name + "@" + version + " " + platform)
    for name in ("check:8", "check:11", "check:17", "check:21"):
        task = config["tasks"][name]
        if task["run"] != "python tools/lab.py check --runtime " + name.split(":")[1]:
            errors.append("Runtime lane must execute the complete check entrypoint: " + name)
        if task.get("tools", {}).get("java"):
            errors.append("Runtime lane must inherit the build JDK: " + name)
        runtime_env = task.get("env", {})
        if ("java", runtime_env.get("LAB_RUNTIME_JAVA")) not in requested or not runtime_env.get("LAB_RUNTIME_JAVA_VERSION"):
            errors.append("Runtime lane needs a declared locked Java version and expected patch: " + name)
    if config.get("env", {}).get("LAB_EXPECTED_JAVA") != "21":
        errors.append("The default build JVM must be JDK 21")
    if any(name.startswith("modern:") for name in config["tasks"]):
        errors.append("The default toolchain must not require modern task aliases")
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
        print("MISE CONFIG PASSED: shared requests and exact Windows/Linux artifact locks")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
