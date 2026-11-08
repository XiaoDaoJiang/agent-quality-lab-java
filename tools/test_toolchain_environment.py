import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from toolchain_environment import collect_environment, validate_environment, save_environment


class ToolchainEnvironmentTest(unittest.TestCase):
    def environment(self):
        return {"compileRelease": "8", "java": {"version": "21.0.11", "major": "21", "home": "/jdk"},
                "javac": {"version": "21.0.11", "major": "21"},
                "maven": {"version": "3.9.11", "javaMajor": "21"},
                "python": {"version": "3.12.0"}, "variables": {"JAVA_HOME": "/jdk"}}

    def test_wrong_runtime_is_rejected(self):
        data = self.environment()
        self.assertIn("Java", " ".join(validate_environment(data, {"LAB_EXPECTED_JAVA": "8"})))

    def test_older_build_jdk_cannot_pass_without_explicit_expectations(self):
        data = self.environment()
        data["java"].update(version="17.0.10", major="17")
        self.assertIn("Build tools require JDK 21+", "; ".join(validate_environment(data, {})))

    def test_explicit_smoke_java_can_differ_from_build_environment(self):
        data = self.environment()
        data["explicitJava"] = True
        data["java"] = {"version": "1.8.0_472", "major": "8", "home": "/runtime8"}
        self.assertEqual([], validate_environment(data, {"LAB_EXPECTED_JAVA": "8"}, require_build=False))

    def test_maven_using_other_jvm_is_rejected(self):
        data = self.environment()
        data["maven"]["javaMajor"] = "8"
        self.assertIn("Maven JVM", " ".join(validate_environment(data, {})))

    def test_wrong_java_home_and_compiler_are_rejected(self):
        data = self.environment()
        data["variables"]["JAVA_HOME"] = "/other-jdk"
        data["javac"]["major"] = "25"
        errors = " ".join(validate_environment(data, {}))
        self.assertIn("JAVA_HOME", errors)
        self.assertIn("javac", errors)

    def test_expected_versions_match(self):
        self.assertEqual([], validate_environment(self.environment(), {
            "LAB_EXPECTED_JAVA": "21", "LAB_EXPECTED_JAVA_VERSION": "21.0.11",
            "LAB_EXPECTED_MAVEN": "3.9.11", "LAB_EXPECTED_PYTHON": "3.12.0"}))

    def test_python_series_accepts_stable_patches_only(self):
        for version in ("3.12.0", "3.12.16", "3.12.99"):
            with self.subTest(version=version):
                data = self.environment()
                data["python"]["version"] = version
                self.assertEqual([], validate_environment(data, {"LAB_EXPECTED_PYTHON": "3.12"}))
        for version in ("3.11.16", "3.13.1", "3.120.1", "3.12", "3.12.16rc1", None):
            with self.subTest(version=version):
                data = self.environment()
                data["python"]["version"] = version
                self.assertIn("python mismatch", " ".join(
                    validate_environment(data, {"LAB_EXPECTED_PYTHON": "3.12"})))

    def test_python_exact_patch_expectation_stays_exact(self):
        data = self.environment()
        data["python"]["version"] = "3.12.16"
        self.assertEqual([], validate_environment(data, {"LAB_EXPECTED_PYTHON": "3.12.16"}))
        self.assertIn("python mismatch", " ".join(
            validate_environment(data, {"LAB_EXPECTED_PYTHON": "3.12.0"})))

    def test_release_change_and_failed_tool_cannot_pass(self):
        data = self.environment()
        data["compileRelease"] = "17"
        data["maven"]["exitCode"] = 1
        errors = " ".join(validate_environment(data, {}))
        self.assertIn("release", errors)
        self.assertIn("maven", errors)

    def test_failure_is_persisted_without_secret_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("toolchain_environment.collect_environment", return_value=self.environment()), \
                 patch.dict("os.environ", {"LAB_EXPECTED_JAVA": "8", "API_TOKEN": "secret-value"}):
                with self.assertRaises(RuntimeError):
                    save_environment(root, "test")
            text = (root / ".lab/runs/test/environment.json").read_text(encoding="utf-8")
            self.assertEqual("failed", json.loads(text)["status"])
            self.assertNotIn("secret-value", text)

    def test_snapshot_only_records_allowed_environment_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "pom.xml").write_text('<project xmlns="http://maven.apache.org/POM/4.0.0">'
                '<properties><maven.compiler.release>8</maven.compiler.release></properties></project>', encoding="utf-8")
            def fake_probe(command):
                output = {"java": "java.version = 17.0.10\njava.home = /jdk\njava.vendor = Vendor",
                          "javac": "javac 17.0.10", "mise": "2026.11.2"}
                return {"path": "/tool", "exitCode": 0,
                        "output": output.get(command[0], "Apache Maven 3.9.11\nJava version: 17.0.10, vendor: Vendor")}
            with patch("toolchain_environment.probe", side_effect=fake_probe), \
                 patch.dict("os.environ", {"API_TOKEN": "secret-token", "MAVEN_OPTS": "-Dpassword=secret-password"}):
                data = collect_environment(root)
            self.assertEqual("8", data["compileRelease"])
            self.assertEqual("17.0.10", data["java"]["version"])
            self.assertNotIn("secret-token", json.dumps(data))
            self.assertNotIn("secret-password", json.dumps(data))

    def test_smoke_hashes_the_selected_jar(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "pom.xml").write_text('<project xmlns="http://maven.apache.org/POM/4.0.0">'
                '<properties><maven.compiler.release>8</maven.compiler.release></properties></project>', encoding="utf-8")
            jar = root / "selected.jar"
            jar.write_bytes(b"selected artifact")
            with patch("toolchain_environment.probe", return_value={"path": None, "output": "", "exitCode": None}):
                data = collect_environment(root, jar=jar)
            self.assertEqual(hashlib.sha256(jar.read_bytes()).hexdigest(), data["jarSha256"])


if __name__ == "__main__":
    unittest.main()
