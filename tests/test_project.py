import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.project import detect_git, detect_project


class ProjectDetectionTests(unittest.TestCase):
    def test_detects_pyproject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("", encoding="utf-8")
            nested = root / "src" / "package"
            nested.mkdir(parents=True)

            info = detect_project(nested)

            self.assertEqual(info.root, root)
            self.assertEqual(info.marker, "pyproject.toml")

    def test_detects_git_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "src"
            nested.mkdir()

            subprocess_result = __import__("subprocess").run(
                ["git", "init", "-q", str(root)],
                check=True,
            )

            info = detect_project(nested)

            self.assertEqual(info.root, root)
            self.assertIsNone(info.marker)

    def test_git_reports_clean_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            __import__("subprocess").run(
                ["git", "init", "-q", str(root)],
                check=True,
            )

            info = detect_git(root)

            self.assertTrue(info.available)
            self.assertEqual(info.root, root)
            self.assertTrue(info.branch)
            self.assertFalse(info.dirty)

    def test_git_reports_dirty_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            __import__("subprocess").run(
                ["git", "init", "-q", str(root)],
                check=True,
            )

            (root / "change.txt").write_text("changed", encoding="utf-8")

            info = detect_git(root)

            self.assertTrue(info.available)
            self.assertTrue(info.dirty)


if __name__ == "__main__":
    unittest.main()
