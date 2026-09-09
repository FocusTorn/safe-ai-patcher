import subprocess
import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.core import Change, PatchError, apply_changes


class TransactionTests(unittest.TestCase):
    def test_applies_multiple_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.txt").write_text("old", encoding="utf-8")

            apply_changes(
                root,
                [
                    Change("one.txt", "new"),
                    Change("two.txt", "created"),
                ],
            )

            self.assertEqual(
                (root / "one.txt").read_text(encoding="utf-8"),
                "new",
            )
            self.assertEqual(
                (root / "two.txt").read_text(encoding="utf-8"),
                "created",
            )

    def test_failed_test_rolls_back_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.txt").write_text("original", encoding="utf-8")

            with self.assertRaises(PatchError):
                apply_changes(
                    root,
                    [
                        Change("one.txt", "changed"),
                        Change("two.txt", "temporary"),
                    ],
                    test_command=[
                        "python",
                        "-c",
                        "raise SystemExit(1)",
                    ],
                )

            self.assertEqual(
                (root / "one.txt").read_text(encoding="utf-8"),
                "original",
            )
            self.assertFalse((root / "two.txt").exists())

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PatchError):
                apply_changes(
                    tmp,
                    [Change("../escape.txt", "nope")],
                )

    def test_rejects_dirty_git_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            subprocess.run(
                ["git", "-C", str(root), "init", "-q"],
                check=True,
            )

            target = root / "hello.txt"
            target.write_text("original\n", encoding="utf-8")

            subprocess.run(
                ["git", "-C", str(root), "add", "hello.txt"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "initial"],
                check=True,
            )

            target.write_text("local change\n", encoding="utf-8")

            with self.assertRaises(PatchError):
                apply_changes(
                    root,
                    [Change("hello.txt", "patch\n")],
                )

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "local change\n",
            )

    def test_allows_dirty_git_target_with_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            subprocess.run(
                ["git", "-C", str(root), "init", "-q"],
                check=True,
            )

            target = root / "hello.txt"
            target.write_text("original\n", encoding="utf-8")

            subprocess.run(
                ["git", "-C", str(root), "add", "hello.txt"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "initial"],
                check=True,
            )

            target.write_text("local change\n", encoding="utf-8")

            apply_changes(
                root,
                [Change("hello.txt", "patch\n")],
                allow_dirty=True,
            )

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "patch\n",
            )

    def test_rejects_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PatchError):
                apply_changes(
                    tmp,
                    [
                        Change("same.txt", "one"),
                        Change("same.txt", "two"),
                    ],
                )


if __name__ == "__main__":
    unittest.main()
