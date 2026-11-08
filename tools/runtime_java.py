"""Resolve an explicitly selected runtime independently of the Maven build JVM."""
import os
from pathlib import Path
import re

from toolchain_environment import major, match, probe


def resolve_runtime(expected_major):
    if expected_major not in ("8", "11", "17", "21"):
        raise RuntimeError("Supported application runtimes: 8, 11, 17, 21")
    home = os.environ.get("LAB_RUNTIME_JAVA_HOME")
    if not home:
        request = os.environ.get("LAB_RUNTIME_JAVA", "")
        if not re.fullmatch(r"(?:temurin-\d+\.\d+\.\d+\+\d+|zulu-\d+\.\d+\.\d+\.\d+)", request):
            raise RuntimeError("Set an exact LAB_RUNTIME_JAVA or a local LAB_RUNTIME_JAVA_HOME")
        installed = probe(["mise", "where", "java@" + request])
        if installed["exitCode"] != 0 or not installed["output"].strip():
            raise RuntimeError("Locked runtime is not installed: " + request)
        home = installed.get("stdout", installed["output"]).strip()
    executable = str((Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")).resolve())
    result = probe([executable, "-XshowSettings:properties", "-version"])
    version = match(result["output"], r"java.version = (.+)")
    expected_version = os.environ.get("LAB_RUNTIME_JAVA_VERSION")
    if result["exitCode"] != 0 or major(version) != expected_major or (expected_version and version != expected_version):
        raise RuntimeError(f"Runtime mismatch: expected Java {expected_major} / {expected_version}, actual {version}")
    return executable, version
