import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.core import Change, PatchError
from safe_ai_patcher.snapshots import create_snapshot, restore_snapshot


class SnapshotTests(unittest.TestCase):
    def test_snapshot_restores_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "hello.txt"
            target.write_text("original\n", encoding="utf-8")

            transaction_id = create_snapshot(
                root,
                [Change("hello.txt", "changed\n")],
            )

            target.write_text("changed\n", encoding="utf-8")

            paths = restore_snapshot(root, transaction_id)

            self.assertEqual(paths, ["hello.txt"])
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "original\n",
            )

    def test_snapshot_removes_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            transaction_id = create_snapshot(
                root,
                [Change("new.txt", "created\n")],
            )

            (root / "new.txt").write_text(
                "created\n",
                encoding="utf-8",
            )

            restore_snapshot(root, transaction_id)

            self.assertFalse((root / "new.txt").exists())

    def test_missing_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PatchError):
                restore_snapshot(Path(tmp), "missing")

    def test_rollback_rejects_post_transaction_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "hello.txt"
            target.write_text("original\n", encoding="utf-8")

            transaction_id = create_snapshot(
                root,
                [Change("hello.txt", "patched\n")],
            )
            target.write_text("patched\n", encoding="utf-8")

            target.write_text("manually changed\n", encoding="utf-8")

            with self.assertRaises(PatchError):
                restore_snapshot(root, transaction_id)

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "manually changed\n",
            )

    def test_force_rollback_restores_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "hello.txt"
            target.write_text("original\n", encoding="utf-8")

            transaction_id = create_snapshot(
                root,
                [Change("hello.txt", "patched\n")],
            )
            target.write_text("patched\n", encoding="utf-8")
            target.write_text("manually changed\n", encoding="utf-8")

            restore_snapshot(root, transaction_id, force=True)

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "original\n",
            )


if __name__ == "__main__":
    unittest.main()
