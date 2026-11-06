from pathlib import Path
import tempfile
import unittest

from verify_fixtures import checker_version


class FixtureProfileTest(unittest.TestCase):
    def test_unknown_or_incomplete_profile_cannot_silently_test_the_old_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            pom = Path(folder) / "pom.xml"
            pom.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0">'
                           '<properties><checkstyle.version>9.3</checkstyle.version></properties>'
                           '<profiles><profile><id>incomplete</id></profile></profiles></project>', encoding="utf-8")
            self.assertEqual("9.3", checker_version(pom))
            for profile in ("missing", "incomplete"):
                with self.assertRaisesRegex(RuntimeError, "Missing explicit Checkstyle"):
                    checker_version(pom, profile)


if __name__ == "__main__":
    unittest.main()
