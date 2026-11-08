#!/usr/bin/env python3
"""A fixed entry point for humans and coding agents. No skip/ignore-failure switches."""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from toolchain_environment import save_environment, probe, match, major
from runtime_java import resolve_runtime

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def maven_command():
    settings = Path(os.environ.get("LAB_MAVEN_SETTINGS", str(ROOT / "config/maven/settings.xml"))).resolve()
    if not settings.is_file():
        raise RuntimeError("Maven settings file is missing: " + str(settings))
    wrapper = ROOT / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    if wrapper.exists():
        return [str(wrapper), "--settings", str(settings)]
    executable = shutil.which("mvn.cmd" if os.name == "nt" else "mvn")
    if not executable:
        raise RuntimeError("Install Maven 3.9.11+ (<4); see README. No fabricated mvnw launcher is bundled.")
    return [executable, "--settings", str(settings)]


def run(command, env=None):
    print("RUN:", subprocess.list2cmdline([str(x) for x in command]), flush=True)
    start = time.monotonic()
    interrupted = False
    try:
        code = subprocess.run(command, cwd=ROOT, env=env, check=False).returncode
    except KeyboardInterrupt:
        code, interrupted = 130, True
    record = {"command": [str(x) for x in command], "exitCode": code,
              "environment": "environment.json",
              "elapsedSeconds": round(time.monotonic()-start, 3),
              "finishedAt": datetime.now(timezone.utc).isoformat()}
    target = ROOT/".lab/runs"/RUN_ID
    target.mkdir(parents=True, exist_ok=True)
    with (target/"command-evidence.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(record)+"\n")
    if interrupted:
        raise KeyboardInterrupt
    if code:
        raise subprocess.CalledProcessError(code, command)


def check_runtime(runtime):
    executable, version = resolve_runtime(runtime)
    run([sys.executable, "tools/lab.py", "doctor"])
    run([sys.executable, "tools/lab.py", "verify", "--test-java", executable])
    run([sys.executable, "tools/lab.py", "fixtures"])
    runtime_env = dict(os.environ, LAB_EXPECTED_JAVA=runtime, LAB_EXPECTED_JAVA_VERSION=version)
    run([sys.executable, "tools/http_smoke.py", "--java", executable,
         "--jar", "app/target/app-0.2.0-SNAPSHOT.jar"], env=runtime_env)
    # Each lane cleans target; retain its reports before the next lane starts.
    target = ROOT / ".lab/runs" / RUN_ID
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "target/lab-summary.json", target / "lab-summary.json")
    for module in ("domain-core", "app"):
        destination = target / module
        destination.mkdir(exist_ok=True)
        for name in ("checkstyle-result.xml", "quality-summary.json"):
            shutil.copy2(ROOT / module / "target" / name, destination / name)
        shutil.copytree(ROOT / module / "target/surefire-reports", destination / "surefire-reports")
    evidence = {"runtime": runtime, "java": executable, "version": version,
                "jarSha256": hashlib.sha256((ROOT / "app/target/app-0.2.0-SNAPSHOT.jar").read_bytes()).hexdigest()}
    (target / "runtime.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "selftest", "format", "verify", "fixtures", "compile", "start", "check"))
    parser.add_argument("--test-java", type=Path, help="Fork verify tests with this Java 8/11/17/21 executable")
    parser.add_argument("--runtime", choices=("8", "11", "17", "21"), help="Runtime lane for check; build JVM remains 21+")
    args = parser.parse_args()
    if args.test_java and args.command != "verify":
        parser.error("--test-java is only valid for verify")
    if (args.command == "check") != bool(args.runtime):
        parser.error("check requires --runtime; --runtime is only valid for check")
    try:
        snapshot = save_environment(ROOT, RUN_ID, require_build=args.command != "start", offline=args.command == "selftest")
        if args.command == "verify" and not args.test_java:
            build_major = json.loads(snapshot.read_text(encoding="utf-8"))["java"]["major"]
            if build_major != "21":
                raise RuntimeError("Default verify tests require Java 21; newer build hosts use compile or an explicit supported --test-java")
        if args.command == "check":
            check_runtime(args.runtime)
            return 0
        if args.command == "start":
            jar = ROOT / "app/target/app-0.2.0-SNAPSHOT.jar"
            if not jar.is_file():
                raise RuntimeError("Build the JAR first: " + str(jar))
            run(["java", "-jar", str(jar), "--server.address=127.0.0.1", "--server.port=8080"])
            return 0
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
        if args.test_java:
            executable = str(args.test_java.resolve())
            test_jvm = probe([executable, "-XshowSettings:properties", "-version"])
            version = major(match(test_jvm["output"], r"java.version = (.+)"))
            if test_jvm["exitCode"] != 0 or version not in ("8", "11", "17", "21"):
                raise RuntimeError("Test runtime must be an executable Java 8/11/17/21 JVM")
            run([executable, "-version"])
            command += ["-Djvm=" + executable, "-Dlab.expectedJava=" + version]
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
    except KeyboardInterrupt:
        print("LAB STOPPED", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, subprocess.CalledProcessError, ET.ParseError) as error:
        print(f"LAB FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
