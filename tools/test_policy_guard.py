import unittest
from policy_guard import protected


class PolicyGuardTest(unittest.TestCase):
    def test_mise_environment_and_tasks_are_policy_files(self):
        for name in ("mise.toml", "mise.lock", "mise.ci.toml", ".mise.toml",
                     "mise-tasks/check", ".mise/tasks/check"):
            with self.subTest(name=name):
                self.assertTrue(protected(name))

    def test_rule_and_workflow_files_are_protected(self):
        for name in ("pom.xml", "app/pom.xml", "config/quality/waivers.json", "tools/quality_gate.py",
                     ".github/workflows/quality.yml", "AGENTS.md", "agents.md", ".mvn/jvm.config",
                     "domain-core/src/test/java/demo/BusinessTest.java", "experiments/cases/task.md"):
            with self.subTest(name=name):
                self.assertTrue(protected(name))

    def test_ordinary_business_sources_are_not_policy_files(self):
        self.assertFalse(protected("domain-core/src/main/java/dev/agentlab/core/domain/Task.java"))


if __name__ == "__main__":
    unittest.main()
