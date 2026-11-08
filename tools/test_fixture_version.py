from pathlib import Path
import tempfile
import unittest

from verify_fixtures import checker_version


class FixtureVersionTest(unittest.TestCase):
    def test_missing_root_version_cannot_silently_fall_back_to_a_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            pom = Path(folder) / "pom.xml"
            pom.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0">'
                           '<profiles><profile><properties><checkstyle.version>9.3</checkstyle.version>'
                           '</properties></profile></profiles></project>', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Missing explicit Checkstyle"):
                checker_version(pom)


if __name__ == "__main__":
    unittest.main()
