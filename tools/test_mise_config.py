from copy import deepcopy
import unittest

from check_mise import validate


class MiseConfigTest(unittest.TestCase):
    def config(self):
        versions = {"8": ("zulu-8.94.0.17", "1.8.0_492"), "11": ("temurin-11.0.24+8", "11.0.24"),
                    "17": ("temurin-17.0.10+7", "17.0.10"), "21": ("zulu-21.54.109.0", "21.0.13.0.3")}
        tasks = {"check:" + v: {"run": "python tools/lab.py check --runtime " + v,
                               "env": {"LAB_RUNTIME_JAVA": tool, "LAB_RUNTIME_JAVA_VERSION": version}}
                 for v, (tool, version) in versions.items()}
        tasks["matrix"] = {"run": [{"task": "check:" + v} for v in ("8", "11", "17", "21")] + [{"task": "compile:25"}]}
        tasks["verify"] = {"run": "python tools/lab.py verify"}
        return {"tools": {"python": "3.12", "java": [tool for tool, _ in versions.values()]},
                "env": {"LAB_EXPECTED_JAVA": "21", "LAB_EXPECTED_PYTHON": "3.12"}, "tasks": tasks}

    def lock(self):
        return {"lockfile_version": 4, "tools": {name: [{"version": "3.12.16" if name == "python" else version,
                                  "specifiers": [version], "platforms": {
            p: {"url": "https://example.org/python.tar.gz", "checksum": "sha256:" + "a" * 64,
                "provenance": "github-attestations" if name == "python" else "checksum"}
            for p in ("windows-x64", "linux-x64")}} for version in (value if isinstance(value, list) else [value])]
            for name, value in self.config()["tools"].items()}}

    def test_complete_declarations_are_accepted(self):
        self.assertEqual([], validate(self.config(), self.lock()))

    def test_https_tool_options_are_not_machine_paths(self):
        config = self.config()
        config["tools"]["python"] = {"version": "3.12", "url": "https://example.org/python.tar.gz"}
        self.assertEqual([], validate(config, self.lock()))

    def test_missing_platform_or_checksum_fails(self):
        lock = self.lock()
        del lock["tools"]["python"][0]["platforms"]["linux-x64"]["checksum"]
        self.assertTrue(validate(self.config(), lock))

    def test_local_alias_and_path_are_rejected(self):
        for value in ("agentlab-3.12.0", {"version": "3.12.0", "path": "C:/Python"}, "latest", "3", "3.11", "3.13", "3.120"):
            config = deepcopy(self.config())
            config["tools"]["python"] = value
            self.assertTrue(validate(config, self.lock()))

    def test_python_series_requires_one_exact_patch_with_matching_specifier(self):
        for version in ("3.12", "3.11.16", "3.13.1", "3.120.1", "3.12.16rc1"):
            with self.subTest(version=version):
                lock = self.lock()
                lock["tools"]["python"][0]["version"] = version
                self.assertTrue(validate(self.config(), lock))
        lock = self.lock()
        del lock["tools"]["python"][0]["specifiers"]
        self.assertTrue(validate(self.config(), lock))
        lock = self.lock()
        lock["tools"]["python"].append(deepcopy(lock["tools"]["python"][0]))
        self.assertTrue(validate(self.config(), lock))

    def test_python_series_requires_a_lock_format_that_binds_specifiers(self):
        lock = self.lock()
        del lock["lockfile_version"]
        self.assertTrue(validate(self.config(), lock))

    def test_python_attestation_provenance_must_be_preserved(self):
        for platform in ("windows-x64", "linux-x64"):
            lock = self.lock()
            del lock["tools"]["python"][0]["platforms"][platform]["provenance"]
            self.assertTrue(validate(self.config(), lock))

    def test_python_expectation_must_match_shared_request(self):
        config = self.config()
        config["env"]["LAB_EXPECTED_PYTHON"] = "3.12.0"
        self.assertTrue(validate(config, self.lock()))

    def test_non_python_tools_still_require_exact_versions(self):
        config = self.config()
        config["tools"]["java"] = ["3.12"]
        self.assertTrue(validate(config, self.lock()))

    def test_python_series_requires_both_platforms_and_checksums(self):
        for platform in ("windows-x64", "linux-x64"):
            lock = self.lock()
            del lock["tools"]["python"][0]["platforms"][platform]
            self.assertTrue(validate(self.config(), lock))

    def test_dotted_platform_tables_are_accepted(self):
        lock = self.lock()
        entry = lock["tools"]["python"][0]
        for platform, info in entry.pop("platforms").items():
            entry["platforms." + platform] = info
        self.assertEqual([], validate(self.config(), lock))

    def test_incomplete_or_reordered_matrix_fails(self):
        config = self.config()
        config["tasks"]["check:21"]["run"] = "python tools/lab.py verify"
        self.assertTrue(validate(config, self.lock()))

    def test_runtime_lane_cannot_replace_the_build_jdk(self):
        config = self.config()
        config["tasks"]["check:8"]["tools"] = {"java": "zulu-8.94.0.17"}
        self.assertTrue(validate(config, self.lock()))

    def test_runtime_lane_cannot_depend_on_an_undeclared_or_floating_tool(self):
        config = self.config()
        config["tasks"]["check:8"]["env"]["LAB_RUNTIME_JAVA"] = "latest"
        self.assertTrue(validate(config, self.lock()))

    def test_default_build_expectation_cannot_fall_back_to_java17(self):
        config = self.config()
        config["env"]["LAB_EXPECTED_JAVA"] = "17"
        self.assertTrue(validate(config, self.lock()))
        config = self.config()
        config["tasks"]["matrix"]["run"].reverse()
        self.assertTrue(validate(config, self.lock()))

    def test_replacing_real_verification_with_success_echo_fails(self):
        config = self.config()
        config["tasks"]["verify"]["run"] = "echo passed"
        self.assertTrue(validate(config, self.lock()))


if __name__ == "__main__":
    unittest.main()
