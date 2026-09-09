import subprocess
import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.project import (
    detect_git,
    detect_project,
    git_changed_paths,
)


class ProjectDetectionTests(unittest.TestCase):
    def test_detects_pyproject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = 'demo'\n",
                encoding="utf-8",
            )

            info = detect_project(root)

            self.assertEqual(info.root, root)
            self.assertEqual(info.marker, "pyproject.toml")

    def test_detects_git_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()

            subprocess.run(
                ["git", "-C", str(root), "init", "-q"],
                check=True,
            )

            info = detect_project(root / "src")

            self.assertEqual(info.root, root)
            self.assertIsNone(info.marker)

    def test_git_reports_clean_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            subprocess.run(
                ["git", "-C", str(root), "init", "-q"],
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

            subprocess.run(
                ["git", "-C", str(root), "init", "-q"],
                check=True,
            )

            (root / "file.txt").write_text("one", encoding="utf-8")

            info = detect_git(root)

            self.assertTrue(info.available)
            self.assertTrue(info.dirty)

    def test_git_changed_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            subprocess.run(
                ["git", "-C", str(root), "init", "-q"],
                check=True,
            )

            (root / "file.txt").write_text("one", encoding="utf-8")

            paths = git_changed_paths(root)

            self.assertEqual(paths, {"file.txt"})


if __name__ == "__main__":
    unittest.main()
