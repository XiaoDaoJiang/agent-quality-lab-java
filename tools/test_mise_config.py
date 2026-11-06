from copy import deepcopy
import unittest

from check_mise import validate


class MiseConfigTest(unittest.TestCase):
    def config(self):
        lane = ["python tools/lab.py doctor", "python tools/lab.py verify", "python tools/lab.py fixtures",
                "python tools/http_smoke.py --jar app/target/app-0.2.0-SNAPSHOT.jar"]
        tasks = {"check:" + v: {"run": list(lane)} for v in ("8", "11", "17", "21")}
        tasks["matrix"] = {"run": [{"task": "check:" + v} for v in ("8", "11", "17", "21")] + [{"task": "compile:25"}]}
        tasks["verify"] = {"run": "python tools/lab.py verify"}
        return {"tools": {"python": "3.12.0"}, "tasks": tasks}

    def lock(self):
        return {"tools": {"python": [{"version": "3.12.0", "platforms": {
            p: {"url": "https://example.org/python.tar.gz", "checksum": "sha256:" + "a" * 64}
            for p in ("windows-x64", "linux-x64")}}]}}

    def test_complete_declarations_are_accepted(self):
        self.assertEqual([], validate(self.config(), self.lock()))

    def test_https_tool_options_are_not_machine_paths(self):
        config = self.config()
        config["tools"]["python"] = {"version": "3.12.0", "url": "https://example.org/python.tar.gz"}
        self.assertEqual([], validate(config, self.lock()))

    def test_missing_platform_or_checksum_fails(self):
        lock = self.lock()
        del lock["tools"]["python"][0]["platforms"]["linux-x64"]["checksum"]
        self.assertTrue(validate(self.config(), lock))

    def test_local_alias_and_path_are_rejected(self):
        for value in ("agentlab-3.12.0", {"version": "3.12.0", "path": "C:/Python"}, "latest", "3.12"):
            config = deepcopy(self.config())
            config["tools"]["python"] = value
            self.assertTrue(validate(config, self.lock()))

    def test_incomplete_or_reordered_matrix_fails(self):
        config = self.config()
        config["tasks"]["check:21"]["run"].pop(1)
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
