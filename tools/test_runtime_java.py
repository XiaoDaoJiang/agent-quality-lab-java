import os
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from runtime_java import resolve_runtime
from lab import check_runtime, maven_command, main


class RuntimeJavaTest(unittest.TestCase):
    def probe(self, version):
        return {"path": "/java", "output": "java.version = " + version, "exitCode": 0}

    def test_local_runtime_has_priority_and_must_match_major_and_patch(self):
        env = {"LAB_RUNTIME_JAVA_HOME": "/installed8", "LAB_RUNTIME_JAVA_VERSION": "1.8.0_202"}
        with patch.dict(os.environ, env, clear=True), patch("runtime_java.probe", return_value=self.probe("1.8.0_202")):
            executable, version = resolve_runtime("8")
            self.assertEqual("1.8.0_202", version)
            self.assertEqual(Path("/installed8/bin/java.exe" if os.name == "nt" else "/installed8/bin/java").resolve(), Path(executable))
        for wrong in ("21.0.11", "1.8.0_401"):
            with patch.dict(os.environ, env, clear=True), patch("runtime_java.probe", return_value=self.probe(wrong)):
                with self.assertRaises(RuntimeError):
                    resolve_runtime("8")

    def test_missing_or_floating_runtime_never_falls_back_to_path(self):
        for env in ({}, {"LAB_RUNTIME_JAVA": "latest"}):
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(RuntimeError):
                    resolve_runtime("8")
        with patch.dict(os.environ, {"LAB_RUNTIME_JAVA": "zulu-8.94.0.17"}, clear=True), \
             patch("runtime_java.probe", return_value={"output": "", "exitCode": 1}):
            with self.assertRaises(RuntimeError):
                resolve_runtime("8")

    def test_mise_diagnostics_are_not_part_of_the_runtime_path(self):
        with patch.dict(os.environ, {"LAB_RUNTIME_JAVA": "zulu-8.94.0.17"}, clear=True), \
             patch("runtime_java.probe", side_effect=[
                 {"stdout": "/installed8\n", "output": "/installed8\nwarning on stderr", "exitCode": 0},
                 self.probe("1.8.0_492")]):
            executable, _ = resolve_runtime("8")
            self.assertNotIn("warning", executable)

    def test_failed_verify_prevents_fixtures_and_http(self):
        with patch("lab.resolve_runtime", return_value=("/java8", "1.8.0_202")), \
             patch("lab.run", side_effect=[None, subprocess.CalledProcessError(1, "verify")]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                check_runtime("8")
            self.assertEqual(2, run.call_count)
            self.assertIn("verify", run.call_args.args[0])

    def test_missing_custom_maven_settings_cannot_fall_back_to_global_settings(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.dict(os.environ, {"LAB_MAVEN_SETTINGS": str(Path(folder) / "missing.xml")}):
            with self.assertRaisesRegex(RuntimeError, "settings file is missing"):
                maven_command()

    def test_java25_cannot_become_the_implicit_test_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / "environment.json"
            snapshot.write_text(json.dumps({"java": {"major": "25"}}), encoding="utf-8")
            with patch("sys.argv", ["lab.py", "verify"]), patch("lab.save_environment", return_value=snapshot), \
                 patch("lab.run") as run:
                self.assertEqual(1, main())
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
