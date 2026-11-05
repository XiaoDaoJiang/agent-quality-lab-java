#!/usr/bin/env python3
"""Small report/policy adapter. Checkstyle finds defects; this code does not parse Java.

The repository is NOT a security boundary against someone allowed to edit the CI.
Server-side protections and human policy review are required. Python >= 3.10, stdlib only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import xml.etree.ElementTree as ET


class PolicyError(ValueError):
    """Invalid policy, report or approval scope: always fails closed."""


def read_json(path: Path) -> dict[str, Any]:
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PolicyError(f"Duplicate JSON key: {key} in {path}")
            result[key] = value
        return result
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PolicyError(f"Cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise PolicyError(f"Expected JSON object: {path}")
    return value


def inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise PolicyError(f"Expected non-empty POSIX-relative path: {relative!r}")
    if Path(relative).is_absolute() or any(p in ("..", ".") for p in relative.split("/")):
        raise PolicyError(f"Unsafe path: {relative}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise PolicyError(f"Path escapes root: {relative}")
    return path


def sha256(path: Path) -> str:
    # All Java sources must use LF; CRLF is rejected, never silently normalized here.
    return hashlib.sha256(path.read_bytes()).hexdigest()


def java_sources(module: Path) -> list[Path]:
    return sorted(p.resolve() for directory in ("src/main/java", "src/test/java")
                  for p in (module / directory).rglob("*.java") if p.is_file())


def load_policy(root: Path, today: date | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    today = today or datetime.now(timezone.utc).date()
    policy = read_json(root / "config/quality/policy.json")
    required = {"schemaVersion", "modules", "advisoryRules", "waivableRules", "limits"}
    if set(policy) != required or policy["schemaVersion"] != 1:
        raise PolicyError("Unknown policy fields or schemaVersion")
    for key in ("modules", "advisoryRules", "waivableRules"):
        values = policy[key]
        if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
            raise PolicyError(f"{key} must be a list of non-empty strings")
        if len(set(values)) != len(values):
            raise PolicyError(f"Duplicate values in {key}")
    if not policy["modules"]:
        raise PolicyError("No registered Java modules")
    for module in policy["modules"]:
        folder = inside(root, module)
        if not (folder / "pom.xml").is_file() or not java_sources(folder):
            raise PolicyError(f"Missing module or all Java sources: {module}")
    limits = policy["limits"]
    if not isinstance(limits, dict) or set(limits) != {"waiverDays", "baselineDays", "activeWaivers", "activeBaseline"}:
        raise PolicyError("Invalid limits")
    if any(type(n) is not int or n < 0 for n in limits.values()):
        raise PolicyError("Limits must be nonnegative integers")
    if not 1 <= limits["waiverDays"] <= 30 or not 1 <= limits["baselineDays"] <= 90:
        raise PolicyError("Maximum waiver TTL=30 days; maximum baseline TTL=90 days")
    allowed = {"MemberName", "MethodName", "TypeName", "ConstantName", "ParameterName", "LocalVariableName"}
    if not set(policy["waivableRules"]).issubset(allowed):
        raise PolicyError("Only naming rules may be waived in MVP; safety/test/architecture checks cannot")
    if not set(policy["advisoryRules"]).issubset({"MethodLength"}):
        raise PolicyError("Only MethodLength may be globally advisory in MVP")
    entries: list[dict[str, Any]] = []
    for filename, kind, count_key in (("waivers.json", "waiver", "activeWaivers"),
                                      ("baseline.json", "baseline", "activeBaseline")):
        document = read_json(root / "config/quality" / filename)
        if set(document) != {"schemaVersion", "entries"} or document["schemaVersion"] != 1:
            raise PolicyError(f"Invalid {filename} schema")
        values = document["entries"]
        if not isinstance(values, list) or len(values) > limits[count_key]:
            raise PolicyError(f"{filename}: invalid entries or budget exceeded")
        for entry in values:
            if not isinstance(entry, dict):
                raise PolicyError("Entry must be an object")
            fields = {"id", "kind", "engine", "file", "rule", "line", "sourceSha256", "owner",
                      "reason", "issue", "created", "expires"}
            if set(entry) != fields or entry["kind"] != kind or entry["engine"] != "checkstyle":
                raise PolicyError(f"Unknown entry fields/kind/engine: {entry}")
            if not re.fullmatch(r"[A-Z][A-Z0-9-]{2,63}", str(entry["id"])):
                raise PolicyError("Entry id must be stable, e.g. BASE-001")
            if entry["rule"] not in policy["waivableRules"]:
                raise PolicyError(f"Rule is not waivable: {entry['rule']}")
            source = inside(root, entry["file"])
            if not source.is_file() or source.suffix != ".java":
                raise PolicyError(f"Missing Java file: {entry['file']}")
            registered = any(source in java_sources(root / m) for m in policy["modules"])
            if not registered:
                raise PolicyError("Waiver target is outside registered main/test source directories")
            if sha256(source) != entry["sourceSha256"]:
                raise PolicyError(f"{entry['id']}: source changed; fix/remove or re-review the exact exemption")
            if type(entry["line"]) is not int or not 1 <= entry["line"] <= len(source.read_text(encoding="utf-8").splitlines()):
                raise PolicyError("Invalid exemption line")
            if not isinstance(entry["owner"], str) or not entry["owner"].strip():
                raise PolicyError("Exemption requires an owner (not proof of approval)")
            if not isinstance(entry["reason"], str) or len(entry["reason"].strip()) < 20:
                raise PolicyError("Exemption requires a meaningful reason (20+ characters)")
            if not isinstance(entry["issue"], str) or not entry["issue"].startswith("docs/issues/"):
                raise PolicyError("Exemption must reference a versioned docs/issues/ record")
            if not inside(root, entry["issue"]).is_file():
                raise PolicyError("Missing issue record")
            try:
                created, expires = date.fromisoformat(entry["created"]), date.fromisoformat(entry["expires"])
            except (ValueError, TypeError) as error:
                raise PolicyError("Use YYYY-MM-DD for created/expires") from error
            duration = (expires - created).days
            ttl = limits["waiverDays" if kind == "waiver" else "baselineDays"]
            if created > today or not 0 < duration <= ttl or today >= expires:
                raise PolicyError(f"{entry['id']}: expired, future-dated or TTL exceeded (expiry is exclusive, UTC)")
            entries.append(entry)
    identifiers = [e["id"] for e in entries]
    scopes = [(e["file"], e["rule"], e["line"]) for e in entries]
    if len(set(identifiers)) != len(identifiers) or len(set(scopes)) != len(scopes):
        raise PolicyError("Duplicate exemption id or overlapping scope")
    return policy, entries


def parse_report(root: Path, module: Path, report: Path) -> list[dict[str, Any]]:
    expected = set(java_sources(module))
    if not expected:
        raise PolicyError(f"No Java sources in {module}")
    if not report.is_file():
        raise PolicyError(f"Missing Checkstyle report: {report}; run Maven, do not fabricate a report")
    content = report.read_bytes()
    if len(content) > 20_000_000 or b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise PolicyError("Report is too large or contains disallowed XML declarations")
    try:
        tree = ET.fromstring(content)
    except ET.ParseError as error:
        raise PolicyError(f"Malformed Checkstyle report: {error}") from error
    if tree.tag != "checkstyle" or any(child.tag != "file" for child in tree):
        raise PolicyError("Unknown report root or report-level processing error")
    seen: set[Path] = set()
    findings: list[dict[str, Any]] = []
    for file_node in tree:
        filename = file_node.get("name", "")
        path = Path(filename)
        path = path.resolve() if path.is_absolute() else (module / path).resolve()
        if path not in expected or path in seen:
            raise PolicyError(f"Duplicate or unexpected report source: {filename}")
        seen.add(path)
        file_hash = sha256(path)
        for event in file_node:
            if event.tag != "error":
                raise PolicyError("Unknown Checkstyle event")
            severity = event.get("severity")
            if severity not in ("error", "warning"):
                raise PolicyError(f"Unknown/ignored severity: {severity}")
            source = event.get("source", "")
            if not source.startswith("com.puppycrawl.tools.checkstyle.checks."):
                raise PolicyError(f"Unrecognized Checkstyle source: {source}")
            rule = source.rsplit(".", 1)[-1].removesuffix("Check")
            try:
                line = int(event.get("line", "0"))
                column = int(event.get("column", "0"))
            except ValueError as error:
                raise PolicyError("Invalid location in report") from error
            if line < 1:
                raise PolicyError("Checkstyle parse/tool error is never waivable")
            findings.append({"engine": "checkstyle", "file": path.relative_to(root).as_posix(),
                             "rule": rule, "line": line, "column": column,
                             "sourceSha256": file_hash, "originalSeverity": severity,
                             "message": event.get("message", "")})
    if seen != expected:
        missing = sorted(str(p.relative_to(root)) for p in expected - seen)
        raise PolicyError(f"Incomplete report: {len(missing)} Java files were not scanned: {missing[:10]}")
    return findings


def apply_policy(findings: list[dict[str, Any]], policy: dict[str, Any],
                 entries: list[dict[str, Any]], module: str) -> dict[str, Any]:
    relevant = [e for e in entries if e["file"].startswith(module + "/")]
    by_scope = {(e["file"], e["rule"], e["line"]): e for e in relevant}
    used: Counter[str] = Counter()
    resolved: list[dict[str, Any]] = []
    for finding in findings:
        item = dict(finding)
        item["effectiveSeverity"] = "warning" if finding["rule"] in policy["advisoryRules"] else "error"
        entry = by_scope.get((finding["file"], finding["rule"], finding["line"]))
        if entry is not None:
            if finding["sourceSha256"] != entry["sourceSha256"]:
                raise PolicyError("Source hash mismatch")
            used[entry["id"]] += 1
            if used[entry["id"]] > 1:
                raise PolicyError("An exemption cannot cover multiple findings")
            item["effectiveSeverity"] = "warning"
            item["exemption"] = {key: entry[key] for key in ("id", "kind", "owner", "reason", "issue", "expires")}
        resolved.append(item)
    unused = sorted(e["id"] for e in relevant if not used[e["id"]])
    if unused:
        raise PolicyError(f"Unused/stale exemptions must be removed: {unused}")
    errors = sum(i["effectiveSeverity"] == "error" for i in resolved)
    warnings = len(resolved) - errors
    return {"schemaVersion": 1, "module": module, "status": "failed" if errors else "passed",
            "errors": errors, "warnings": warnings, "findings": resolved,
            "generatedAt": datetime.now(timezone.utc).isoformat()}


def source_hygiene(root: Path, module: Path) -> None:
    forbidden = re.compile(r"spotless\s*:\s*off|CHECKSTYLE\s*[.:]\s*OFF|@formatter\s*:\s*off|"
                           r"@SuppressWarnings\s*\([^)]*\b(?:checkstyle|PMD|all)\b", re.I)
    for path in java_sources(module):
        data = path.read_bytes()
        if b"\r" in data:
            raise PolicyError(f"Source must use LF: {path.relative_to(root)}")
        if forbidden.search(data.decode("utf-8")):
            raise PolicyError(f"Inline broad suppression is not enabled: {path.relative_to(root)}")


def evaluate(root: Path, module: Path) -> dict[str, Any]:
    root, module = root.resolve(), module.resolve()
    policy, entries = load_policy(root)
    if module == root:
        # Root POM has no Java. Validate all policy records; children evaluate their own reports.
        return {"schemaVersion": 1, "module": ".", "status": "passed", "errors": 0,
                "warnings": 0, "findings": [], "message": "Policy metadata valid; child modules must still run"}
    try:
        name = module.relative_to(root).as_posix()
    except ValueError as error:
        raise PolicyError("Module is outside project") from error
    if name not in policy["modules"]:
        raise PolicyError(f"Unregistered module: {name}")
    source_hygiene(root, module)
    findings = parse_report(root, module, module / "target/checkstyle-result.xml")
    result = apply_policy(findings, policy, entries, name)
    result["sourceHashes"] = {p.relative_to(root).as_posix(): sha256(p) for p in java_sources(module)}
    output = module / "target/quality-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evaluate", "metadata", "propose"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--module", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "metadata":
            _, entries = load_policy(root)
            print(f"POLICY OK: {len(entries)} scoped, expiring exemption(s); approval is checked outside this file")
            return 0
        if args.module is None:
            raise PolicyError("--module is required")
        module = args.module.resolve()
        if args.command == "propose":
            # Read-only suggestions: never edits waivers/baseline, never invents an approver.
            policy = read_json(root / "config/quality/policy.json")
            for item in parse_report(root, module, module / "target/checkstyle-result.xml"):
                if item["rule"] in policy["waivableRules"]:
                    draft = {key: item[key] for key in ("engine", "file", "rule", "line", "sourceSha256")}
                    draft.update({"id": "DRAFT-REQUIRES-REVIEW", "kind": "waiver", "owner": "",
                                  "reason": "", "issue": "", "created": "", "expires": ""})
                    print(json.dumps(draft, ensure_ascii=False, indent=2))
            return 0
        result = evaluate(root, module)
        for item in result["findings"]:
            suffix = f" [{item['exemption']['id']}; expires={item['exemption']['expires']}]" if "exemption" in item else ""
            print(f"{item['effectiveSeverity'].upper()}: {item['file']}:{item['line']} {item['rule']}: {item['message']}{suffix}")
        print(f"QUALITY {result['status'].upper()}: {result['module']}; errors={result['errors']}, warnings={result['warnings']}")
        return 1 if result["errors"] else 0
    except (PolicyError, OSError, UnicodeError) as error:
        print(f"POLICY ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
