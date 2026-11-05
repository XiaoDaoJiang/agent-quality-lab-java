#!/usr/bin/env python3
"""Dependency-free verification only; does NOT claim the Maven/Spring toolchain passed."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"], cwd=ROOT, check=True)
    java, javac = shutil.which("java"), shutil.which("javac")
    if not java or not javac:
        raise SystemExit("A JDK 8+ is required for this fallback")
    with tempfile.TemporaryDirectory(prefix="agentlab-offline-") as directory:
        classes = Path(directory)/"classes"
        classes.mkdir()
        sources = sorted((ROOT/"domain-core/src/main/java").rglob("*.java"))
        sources.append(ROOT/"tools/offline/DomainSmoke.java")
        version_result = subprocess.run([javac, "-version"], capture_output=True, text=True, check=True)
        version_text = (version_result.stdout + version_result.stderr).strip()
        import re
        match = re.search(r"(?:javac )?(\d+)(?:\.(\d+))?", version_text)
        if not match:
            raise RuntimeError("Cannot determine javac version: " + version_text)
        major = int(match.group(1))
        if major == 1:
            major = int(match.group(2) or 0)
        target_args = ["--release", "8"] if major >= 9 else ["-source", "1.8", "-target", "1.8"]
        subprocess.run([javac] + target_args + ["-Xlint:all,-options", "-Werror", "-d", str(classes)]
                       + [str(path) for path in sources], check=True)
        subprocess.run([java,"-cp",str(classes),"dev.agentlab.offline.DomainSmoke"],check=True)
        source = Path(directory)/"UsesJava9Api.java"
        shutil.copyfile(ROOT/"experiments/compatibility/UsesJava9Api.java.txt",source)
        result = subprocess.run([javac] + target_args + [str(source)],capture_output=True,text=True)
        if not result.returncode or "of" not in result.stderr:
            raise RuntimeError("Did not observe expected Java 9 API rejection: "+result.stderr)
        print("JAVA 9 API REJECTED UNDER --release 8: expected failure observed")
    print("OFFLINE ONLY: Maven, real Checkstyle/Spotless, ArchUnit, HTTP tests, JDK 8/11/17/21 runtime matrix and JDK 25 compile-only lane still need full verification.")


if __name__ == "__main__":
    main()
