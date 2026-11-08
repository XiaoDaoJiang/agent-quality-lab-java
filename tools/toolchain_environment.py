"""Capture the effective toolchain after task-level environment selection."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


def major(version):
    match = re.match(r"(?:1\.)?(\d+)", version or "")
    return match.group(1) if match else None


def probe(command):
    executable = shutil.which(command[0])
    if not executable:
        return {"path": None, "output": "", "exitCode": None}
    try:
        result = subprocess.run([executable] + command[1:], capture_output=True,
                                text=True, errors="replace", timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"path": str(Path(executable).resolve()), "output": "", "exitCode": None}
    return {"path": str(Path(executable).resolve()), "stdout": re.sub(r"\x1b\[[0-9;]*m", "", result.stdout),
            "output": re.sub(r"\x1b\[[0-9;]*m", "", result.stdout + result.stderr),
            "exitCode": result.returncode}


def match(text, pattern):
    found = re.search(pattern, text)
    return found.group(1).strip() if found else None


def jdk_home(value):
    home = Path(value).resolve()
    return home.parent if home.name.lower() == "jre" else home


def collect_environment(root, java="java", jar=None):
    jre = probe([java, "-XshowSettings:properties", "-version"])
    compiler = probe(["javac", "-version"])
    maven = probe(["mvn.cmd" if os.name == "nt" else "mvn", "-version"])
    mise = probe(["mise", "--version"])
    java_version = match(jre["output"], r"java.version = (.+)")
    javac_version = match(compiler["output"], r"javac ([^\s]+)")
    variables = {name: os.environ.get(name) for name in ("JAVA_HOME", "MAVEN_HOME", "M2_HOME", "PYTHONUTF8", "LAB_MAVEN_SETTINGS")}
    # JVM options can contain credentials; their presence is useful, their values are not logged.
    for name in ("MAVEN_ARGS", "MAVEN_OPTS", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS"):
        variables[name] = "[set; contents withheld]" if os.environ.get(name) else None
    configs = {}
    for name in ("mise.toml", "mise.lock", "mise.local.toml", "pom.xml", "config/maven/settings.xml"):
        path = root / name
        if path.is_file():
            configs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    jar = Path(jar).resolve() if jar is not None else root / "app/target/app-0.2.0-SNAPSHOT.jar"
    head = probe(["git", "-C", str(root), "rev-parse", "HEAD"])
    diff = probe(["git", "-C", str(root), "diff", "--binary", "HEAD"])
    release = ET.parse(root / "pom.xml").findtext(
        "{http://maven.apache.org/POM/4.0.0}properties/{http://maven.apache.org/POM/4.0.0}maven.compiler.release")
    return {"generatedAt": datetime.now(timezone.utc).isoformat(), "cwd": str(Path.cwd()),
            "root": str(root), "os": platform.system(), "architecture": platform.machine(),
            "task": os.environ.get("MISE_TASK_NAME"), "compileRelease": release, "explicitJava": java != "java",
            "mise": {"path": mise["path"], "version": match(mise["output"], r"^(\S+)")},
            "java": {"path": jre["path"], "exitCode": jre["exitCode"], "version": java_version, "major": major(java_version),
                     "home": match(jre["output"], r"java.home = (.+)"),
                     "vendor": match(jre["output"], r"java.vendor = (.+)")},
            "javac": {"path": compiler["path"], "exitCode": compiler["exitCode"], "version": javac_version, "major": major(javac_version)},
            "maven": {"path": maven["path"], "exitCode": maven["exitCode"], "version": match(maven["output"], r"Apache Maven ([^\s]+)"),
                      "home": match(maven["output"], r"Maven home: (.+)"),
                      "javaMajor": major(match(maven["output"], r"Java version: ([^,\s]+)"))},
            "python": {"path": str(Path(sys.executable).resolve()), "version": platform.python_version()},
            "gitCommit": head["output"].strip() if head["exitCode"] == 0 else None,
            "trackedDiffSha256": hashlib.sha256(diff["output"].encode()).hexdigest() if diff["exitCode"] == 0 else None,
            "variables": variables, "configurationSha256": configs,
            "jarSha256": hashlib.sha256(jar.read_bytes()).hexdigest() if jar.is_file() else None}


def validate_environment(data, expected, require_build=True):
    errors = []
    if require_build and (not data["java"]["major"] or int(data["java"]["major"]) < 21):
        errors.append("Build tools require JDK 21+; application/test target remains Java 8")
    if data.get("compileRelease") != "8":
        errors.append("Compile release must remain 8")
    for tool in (("java", "javac", "maven") if require_build else ("java",)):
        if not data[tool]["version"] or data[tool].get("exitCode", 0) != 0:
            errors.append("Cannot determine " + tool + " version")
    for key, tool, field in (("LAB_EXPECTED_JAVA", "java", "major"),
                             ("LAB_EXPECTED_JAVA_VERSION", "java", "version"),
                             ("LAB_EXPECTED_MAVEN", "maven", "version"),
                             ("LAB_EXPECTED_PYTHON", "python", "version")):
        actual = data[tool][field]
        matches = actual == expected.get(key)
        if key == "LAB_EXPECTED_PYTHON" and expected.get(key) == "3.12":
            matches = bool(re.fullmatch(r"3\.12\.\d+", actual or ""))
        if expected.get(key) and not matches:
            errors.append(f"{'Java' if tool == 'java' else tool} mismatch: expected {expected[key]}, actual {data[tool][field]}")
    home = data["variables"].get("JAVA_HOME")
    actual_home = data["java"].get("home")
    if not data.get("explicitJava") and home and actual_home and jdk_home(home) != jdk_home(actual_home):
        errors.append("JAVA_HOME does not match the effective Java JVM")
    if require_build and data["java"]["major"] != data["javac"]["major"]:
        errors.append("javac does not match the Java runtime")
    if require_build and data["maven"].get("javaMajor") and data["maven"]["javaMajor"] != data["java"]["major"]:
        errors.append("Maven JVM does not match the effective Java runtime")
    if require_build and data["maven"].get("home"):
        for name in ("MAVEN_HOME", "M2_HOME"):
            value = data["variables"].get(name)
            if value and Path(value).resolve() != Path(data["maven"]["home"]).resolve():
                errors.append(name + " does not match the effective Maven installation")
    return errors


def save_environment(root, run_id, java="java", require_build=True, offline=False, jar=None):
    data = collect_environment(root, java, jar)
    expected = {key: value for key, value in os.environ.items() if key in (
        "LAB_EXPECTED_JAVA", "LAB_EXPECTED_JAVA_VERSION", "LAB_EXPECTED_MAVEN", "LAB_EXPECTED_PYTHON")}
    errors = [] if offline else validate_environment(data, expected, require_build)
    data.update(expected=expected, errors=errors, status="failed" if errors else "observed" if offline else "passed")
    target = root / ".lab/runs" / run_id / "environment.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOOLCHAIN status={data['status']} task={data.get('task')} release={data.get('compileRelease')} "
          f"os={data.get('os')} arch={data.get('architecture')}", flush=True)
    for tool in ("mise", "java", "javac", "maven", "python"):
        if tool in data:
            print(" ", tool, json.dumps(data[tool], ensure_ascii=False), flush=True)
    print("  expected:", json.dumps(expected), "\n  variables:", json.dumps(data["variables"], ensure_ascii=False), flush=True)
    print("  snapshot:", target, flush=True)
    if errors:
        raise RuntimeError("Toolchain validation failed: " + "; ".join(errors))
    return target
