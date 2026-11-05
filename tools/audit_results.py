#!/usr/bin/env python3
"""Audit the selected reactor after Maven success. Missing reports/classes fail closed."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

from quality_gate import PolicyError, evaluate


def audit(root, modules, compile_only=False):
    results = []
    for name in modules:
        module = root / name
        quality = evaluate(root, module)
        if quality["errors"]:
            raise PolicyError(f"Unresolved quality errors in {name}")
        counts = None
        if not compile_only:
            reports = list((module/"target/surefire-reports").glob("TEST-*.xml"))
            if not reports:
                raise PolicyError(f"Missing test reports: {name}")
            counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
            for report in reports:
                suite = ET.parse(report).getroot()
                if suite.tag != "testsuite":
                    raise PolicyError(f"Unexpected test report root: {report}")
                for key in counts:
                    counts[key] += int(suite.get(key, "0"))
            if counts["tests"] <= 0 or any(counts[key] for key in ("failures", "errors", "skipped")):
                raise PolicyError(f"Incomplete/failed/skipped tests in {name}: {counts}")
        classes = list((module/"target/classes").rglob("*.class"))
        test_classes = list((module/"target/test-classes").rglob("*.class"))
        if not classes:
            raise PolicyError(f"Missing production class files: {name}")
        if not test_classes:
            raise PolicyError(f"Missing compiled test class files: {name}")
        classes.extend(test_classes)
        versions = set()
        for path in classes:
            data = path.read_bytes()
            if len(data) < 8 or data[:4] != b"\xca\xfe\xba\xbe":
                raise PolicyError(f"Invalid class: {path}")
            versions.add(struct.unpack(">H", data[6:8])[0])
        maximum = 52
        if max(versions) > maximum:
            raise PolicyError(f"Bytecode target exceeded in {name}: {versions}, maximum {maximum}")
        results.append({"module": name, "quality": {k: quality[k] for k in ("errors", "warnings", "status")},
                        "tests": counts, "classFileVersions": sorted(versions)})
    summary = {"schemaVersion": 1, "status": "compiled" if compile_only else "passed", "generatedAt": datetime.now(timezone.utc).isoformat(),
               "modules": results, "note": "Compile-only mode does not prove runtime compatibility or passing tests." if compile_only else "Java 8 runtime CI lane remains mandatory."}
    target = root/"target/lab-summary.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--modules", nargs="+", default=["domain-core", "app"])
    parser.add_argument("--compile-only", action="store_true", help="Audit compiled Java 8 bytecode without requiring test reports")
    args = parser.parse_args()
    try:
        if not set(args.modules).issubset({"domain-core", "app"}):
            raise PolicyError("Unknown module selection")
        audit(args.root.resolve(), args.modules, compile_only=args.compile_only)
        return 0
    except (PolicyError, OSError, ET.ParseError, ValueError) as error:
        print(f"AUDIT FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
