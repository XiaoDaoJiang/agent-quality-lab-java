"""Policy regression tests. Synthetic XML tests the adapter, NOT the Checkstyle engine.
Use verify_fixtures.py to exercise the real Checkstyle engine when Maven is available.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from quality_gate import PolicyError, apply_policy, evaluate, load_policy, parse_report, sha256, source_hygiene


class QualityGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.module = self.root / "domain-core"
        self.source = self.module / "src/main/java/demo/Legacy.java"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b"package demo;\npublic class Legacy {\n    public String bad_name;\n}\n")
        (self.module / "pom.xml").write_text("<project/>", encoding="utf-8")
        (self.root / "docs/issues").mkdir(parents=True)
        (self.root / "docs/issues/TEST.md").write_text("Reviewed scope example", encoding="utf-8")
        (self.root / "config/quality").mkdir(parents=True)
        self.policy = {"schemaVersion": 1, "modules": ["domain-core"], "advisoryRules": ["MethodLength"],
                       "waivableRules": ["MemberName"],
                       "limits": {"waiverDays": 30, "baselineDays": 90, "activeWaivers": 3, "activeBaseline": 1}}
        today = datetime.now(timezone.utc).date()
        self.entry = {"id": "TEST-001", "kind": "waiver", "engine": "checkstyle",
                      "file": self.source.relative_to(self.root).as_posix(), "rule": "MemberName", "line": 3,
                      "sourceSha256": sha256(self.source), "owner": "maintainer",
                      "reason": "Compatibility exception pending an explicit caller migration.",
                      "issue": "docs/issues/TEST.md", "created": str(today), "expires": str(today + timedelta(days=10))}
        self.write_json("policy.json", self.policy)
        self.write_json("waivers.json", {"schemaVersion": 1, "entries": []})
        self.write_json("baseline.json", {"schemaVersion": 1, "entries": []})
        self.report = self.module / "target/checkstyle-result.xml"
        self.report.parent.mkdir()
        self.write_report()

    def write_json(self, name, value):
        (self.root / "config/quality" / name).write_text(json.dumps(value), encoding="utf-8")

    def waiver(self, **changes):
        entry = deepcopy(self.entry)
        entry.update(changes)
        self.write_json("waivers.json", {"schemaVersion": 1, "entries": [entry]})

    def write_report(self, rules=("MemberName",), severity="error", line=3):
        tree = ET.Element("checkstyle", version="test-fixture")
        file_node = ET.SubElement(tree, "file", name=str(self.source))
        for rule in rules:
            ET.SubElement(file_node, "error", line=str(line), column="19", severity=severity,
                          message="synthetic fixture", source="com.puppycrawl.tools.checkstyle.checks.naming." + rule + "Check")
        ET.ElementTree(tree).write(self.report, encoding="utf-8", xml_declaration=True)

    def test_new_error_blocks(self):
        self.assertEqual(evaluate(self.root, self.module)["errors"], 1)

    def test_clean_report_passes(self):
        self.write_report(())
        self.assertEqual(evaluate(self.root, self.module)["status"], "passed")

    def test_advisory_remains_visible(self):
        self.write_report(("MethodLength",), severity="warning")
        self.assertEqual(evaluate(self.root, self.module)["warnings"], 1)

    def test_hard_rule_cannot_be_downgraded_by_xml_severity(self):
        self.write_report(severity="warning")
        self.assertEqual(evaluate(self.root, self.module)["errors"], 1)

    def test_waiver_preserves_original_error(self):
        self.waiver()
        result = evaluate(self.root, self.module)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["warnings"], 1)
        self.assertEqual(result["findings"][0]["originalSeverity"], "error")
        self.assertEqual(result["findings"][0]["exemption"]["id"], "TEST-001")

    def test_baseline_is_warning_not_hidden(self):
        self.entry["kind"] = "baseline"
        self.write_json("baseline.json", {"schemaVersion": 1, "entries": [self.entry]})
        self.assertEqual(evaluate(self.root, self.module)["warnings"], 1)

    def test_missing_report_fails_closed(self):
        self.report.unlink()
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_malformed_report_fails_closed(self):
        self.report.write_text("<checkstyle", encoding="utf-8")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_report_wrong_root_fails(self):
        self.report.write_text("<results/>", encoding="utf-8")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_missing_scanned_file_fails(self):
        self.report.write_text("<checkstyle/>", encoding="utf-8")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_report_cannot_duplicate_file(self):
        tree = ET.parse(self.report)
        tree.getroot().append(deepcopy(tree.getroot()[0]))
        tree.write(self.report)
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_unexpected_scanned_file_fails(self):
        tree = ET.parse(self.report)
        tree.getroot()[0].set("name", "/outside/source.java")
        tree.write(self.report)
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_xml_entities_rejected(self):
        self.report.write_text('<!DOCTYPE checkstyle [<!ENTITY x "x">]><checkstyle/>', encoding="utf-8")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_unknown_engine_error_is_not_suppressible(self):
        tree = ET.parse(self.report)
        tree.getroot()[0][0].set("source", "internal.CheckerException")
        tree.write(self.report)
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_tool_error_line_zero_fails(self):
        self.write_report(line=0)
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_ignored_severity_fails(self):
        self.write_report(severity="ignore")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_expired_entry_fails(self):
        today = datetime.now(timezone.utc).date()
        self.waiver(created=str(today-timedelta(days=10)), expires=str(today))
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_future_entry_fails(self):
        today = datetime.now(timezone.utc).date()
        self.waiver(created=str(today+timedelta(days=1)))
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_excessive_ttl_fails(self):
        self.waiver(expires=str(datetime.now(timezone.utc).date()+timedelta(days=31)))
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_source_change_invalidates_scope(self):
        self.waiver()
        self.source.write_text(self.source.read_text()+"// changed\n", encoding="utf-8")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_removed_finding_requires_removing_waiver(self):
        self.waiver()
        self.write_report(())
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_duplicate_errors_not_hidden_by_one_waiver(self):
        self.waiver()
        self.write_report(("MemberName", "MemberName"))
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_different_rule_remains_blocking(self):
        self.waiver()
        self.write_report(("MemberName", "NeedBraces"))
        result = evaluate(self.root, self.module)
        self.assertEqual((result["errors"], result["warnings"]), (1, 1))

    def test_safety_rule_cannot_be_waived(self):
        self.waiver(rule="EmptyCatchBlock")
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_safety_rule_cannot_be_added_to_allowlist(self):
        self.policy["waivableRules"].append("EmptyCatchBlock")
        self.write_json("policy.json", self.policy)
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_missing_owner_or_reason_or_issue_fails(self):
        for field in ("owner", "reason", "issue"):
            with self.subTest(field=field):
                self.waiver(**{field: ""})
                with self.assertRaises(PolicyError):
                    load_policy(self.root)

    def test_path_traversal_fails(self):
        self.waiver(file="../source.java")
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_duplicate_ids_and_scopes_fail(self):
        self.write_json("waivers.json", {"schemaVersion": 1, "entries": [self.entry, self.entry]})
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_budget_overrun_fails(self):
        self.policy["limits"]["activeWaivers"] = 0
        self.write_json("policy.json", self.policy)
        self.waiver()
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_unknown_policy_keys_fail(self):
        self.policy["skipAll"] = True
        self.write_json("policy.json", self.policy)
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_duplicate_json_keys_fail(self):
        (self.root/"config/quality/waivers.json").write_text('{"schemaVersion":1,"entries":[],"entries":[]}', encoding="utf-8")
        with self.assertRaises(PolicyError):
            load_policy(self.root)

    def test_new_source_missing_from_report_fails(self):
        (self.source.parent/"New.java").write_text("class New {}", encoding="utf-8")
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.module)

    def test_inline_suppression_fails(self):
        self.source.write_bytes(b"// CHECKSTYLE:OFF\nclass Legacy {}")
        with self.assertRaisesRegex(PolicyError, "Inline broad suppression"):
            source_hygiene(self.root, self.module)

    def test_crlf_source_fails(self):
        self.source.write_bytes(b"class Legacy {}\r\n")
        with self.assertRaisesRegex(PolicyError, "Source must use LF"):
            source_hygiene(self.root, self.module)

    def test_root_checks_metadata_without_claiming_children_passed(self):
        self.assertIn("children", evaluate(self.root, self.root)["message"].replace("child modules", "children"))

    def test_unregistered_module_fails(self):
        with self.assertRaises(PolicyError):
            evaluate(self.root, self.root/"arbitrary")

    def test_deleting_all_source_does_not_pass(self):
        self.source.unlink()
        with self.assertRaises(PolicyError):
            load_policy(self.root)


if __name__ == "__main__":
    unittest.main()
