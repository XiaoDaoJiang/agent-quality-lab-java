#!/usr/bin/env python3
"""Run real Checkstyle against isolated negative/positive fixtures; do not modify app sources."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from lab import ROOT, maven_command


def checker_version(pom, profile=None):
    namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
    parent = ET.parse(pom)
    prefix = f"m:profiles/m:profile[m:id='{profile}']/" if profile else ""
    value = parent.find(prefix + "m:properties/m:checkstyle.version", namespace)
    if value is None or not value.text:
        raise RuntimeError("Missing explicit Checkstyle version for profile: " + str(profile))
    return value.text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("modern-toolchain",))
    args = parser.parse_args()
    version = checker_version(ROOT / "pom.xml", args.profile)
    work = ROOT / "target/fixture-checkstyle"
    if work.exists():
        shutil.rmtree(work)
    source = work/"src/main/java/fixtures"
    source.mkdir(parents=True)
    for path in (ROOT/"experiments/checkstyle").glob("*.java.txt"):
        shutil.copyfile(path, source/path.name.removesuffix(".txt"))
    expectations = json.loads((ROOT/"experiments/checkstyle/expectations.json").read_text(encoding="utf-8"))
    # Reuse the real config and pinned checker. Use XML builders, not string interpolation of paths.
    project = ET.Element("project", xmlns="http://maven.apache.org/POM/4.0.0")
    for key,value in (("modelVersion","4.0.0"),("groupId","dev.agentlab.fixtures"),
                      ("artifactId","checkstyle-regression"),("version","1")):
        ET.SubElement(project,key).text=value
    plugin = ET.SubElement(ET.SubElement(ET.SubElement(project,"build"),"plugins"),"plugin")
    for key,value in (("groupId","org.apache.maven.plugins"),("artifactId","maven-checkstyle-plugin"),("version","3.6.0")):
        ET.SubElement(plugin,key).text=value
    dependency=ET.SubElement(ET.SubElement(plugin,"dependencies"),"dependency")
    for key,value in (("groupId","com.puppycrawl.tools"),("artifactId","checkstyle"),("version",version)):
        ET.SubElement(dependency,key).text=value
    config=ET.SubElement(plugin,"configuration")
    for key,value in (("configLocation",str(ROOT/"config/checkstyle/checkstyle.xml")),
                      ("outputFileFormat","xml"),("outputFile",str(work/"target/checkstyle-result.xml")),
                      ("includeResources","false"),("includeTestResources","false"),
                      ("linkXRef","false"),("failsOnError","false")):
        ET.SubElement(config,key).text=value
    ET.indent(project)
    ET.ElementTree(project).write(work/"pom.xml",encoding="utf-8",xml_declaration=True)
    command=maven_command()+["-B","-f",str(work/"pom.xml"),"checkstyle:checkstyle"]
    outcome=subprocess.run(command,cwd=ROOT,check=False)
    if outcome.returncode:
        print("Fixture tool execution FAILED; this is not an expected lint failure",file=sys.stderr)
        return 1
    report=work/"target/checkstyle-result.xml"
    if not report.exists():
        raise RuntimeError("Missing real Checkstyle fixture report")
    actual={}
    for node in ET.parse(report).getroot().findall("file"):
        name=Path(node.get("name")).name
        actual[name]={e.get("source").rsplit(".",1)[-1].removesuffix("Check"):e.get("severity")
                      for e in node.findall("error")}
    for name,wanted in expectations.items():
        if actual.get(name) != wanted:
            raise RuntimeError(f"Fixture {name}: expected {wanted}, got {actual.get(name)}")
    if set(actual) != set(expectations):
        raise RuntimeError("Fixture report source coverage mismatch")
    print(f"REAL CHECKSTYLE FIXTURES PASSED: {len(expectations)}; engine={version}; profile={args.profile}")
    # --release must reject APIs that were introduced after Java 8.
    with tempfile.TemporaryDirectory(prefix="agentlab-release8-") as folder:
        path=Path(folder)/"UsesJava9Api.java"
        shutil.copyfile(ROOT/"experiments/compatibility/UsesJava9Api.java.txt",path)
        javac=shutil.which("javac")
        if not javac:
            raise RuntimeError("javac not found")
        javac_version=subprocess.run([javac,"-version"],capture_output=True,text=True,check=False)
        version_text=(javac_version.stdout+javac_version.stderr).strip()
        match=__import__("re").search(r"(?:javac )?(\d+)(?:\.(\d+))?",version_text)
        if not match:
            raise RuntimeError("Cannot determine javac version: "+version_text)
        major=int(match.group(1))
        if major == 1:
            major=int(match.group(2) or 0)
        compile_args=[javac,"--release","8"] if major >= 9 else [javac,"-source","1.8","-target","1.8"]
        compile_result=subprocess.run(compile_args+[str(path)],capture_output=True)
        if compile_result.returncode == 0 or b"of" not in compile_result.stderr:
            raise RuntimeError("Java 9 API rejection was not observed; inspect compiler output: "
                               + compile_result.stderr.decode(errors="replace"))
    print("JAVA 8 API NEGATIVE FIXTURE PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError,ValueError,RuntimeError,ET.ParseError) as error:
        print(f"FIXTURE FAILED: {error}",file=sys.stderr)
        sys.exit(1)
