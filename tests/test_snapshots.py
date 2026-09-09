import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.core import Change, PatchError
from safe_ai_patcher.snapshots import cleanup_snapshots, create_snapshot, restore_snapshot


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


    def test_cleanup_keeps_newest_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".sap" / "transactions").mkdir(parents=True)

            for name in ("one", "two", "three"):
                directory = root / ".sap" / "transactions" / name
                directory.mkdir()
                (directory / "metadata.json").write_text('{"paths": []}')

            import os
            os.utime(
                root / ".sap" / "transactions" / "one",
                (1, 1),
            )
            os.utime(
                root / ".sap" / "transactions" / "two",
                (2, 2),
            )
            os.utime(
                root / ".sap" / "transactions" / "three",
                (3, 3),
            )

            removed = cleanup_snapshots(root, keep=2)

            self.assertEqual(removed, ["one"])
            self.assertTrue(
                (root / ".sap" / "transactions" / "two").is_dir()
            )
            self.assertTrue(
                (root / ".sap" / "transactions" / "three").is_dir()
            )

    def test_cleanup_preserves_rollback_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transactions = root / ".sap" / "transactions"
            transactions.mkdir(parents=True)

            for name in ("old", "new"):
                directory = transactions / name
                directory.mkdir()
                (directory / "metadata.json").write_text('{"paths": []}')

            history = root / ".sap" / "history.jsonl"
            history.write_text(
                '{"id":"rollback","status":"rollback",'
                '"paths":[],"rollback_of":"old"}\n'
            )

            import os
            os.utime(transactions / "old", (1, 1))
            os.utime(transactions / "new", (2, 2))

            removed = cleanup_snapshots(root, keep=0)

            self.assertEqual(removed, ["new"])
            self.assertTrue((transactions / "old").is_dir())
            self.assertFalse((transactions / "new").is_dir())


    def test_cleanup_keeps_newest_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".sap" / "transactions").mkdir(parents=True)

            for name in ("one", "two", "three"):
                directory = root / ".sap" / "transactions" / name
                directory.mkdir()
                (directory / "metadata.json").write_text('{"paths": []}')

            import os
            os.utime(
                root / ".sap" / "transactions" / "one",
                (1, 1),
            )
            os.utime(
                root / ".sap" / "transactions" / "two",
                (2, 2),
            )
            os.utime(
                root / ".sap" / "transactions" / "three",
                (3, 3),
            )

            removed = cleanup_snapshots(root, keep=2)

            self.assertEqual(removed, ["one"])
            self.assertTrue(
                (root / ".sap" / "transactions" / "two").is_dir()
            )
            self.assertTrue(
                (root / ".sap" / "transactions" / "three").is_dir()
            )

    def test_cleanup_preserves_rollback_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transactions = root / ".sap" / "transactions"
            transactions.mkdir(parents=True)

            for name in ("old", "new"):
                directory = transactions / name
                directory.mkdir()
                (directory / "metadata.json").write_text('{"paths": []}')

            history = root / ".sap" / "history.jsonl"
            history.write_text(
                '{"id":"rollback","status":"rollback",'
                '"paths":[],"rollback_of":"old"}\n'
            )

            import os
            os.utime(transactions / "old", (1, 1))
            os.utime(transactions / "new", (2, 2))

            removed = cleanup_snapshots(root, keep=0)

            self.assertEqual(removed, ["new"])
            self.assertTrue((transactions / "old").is_dir())
            self.assertFalse((transactions / "new").is_dir())


    def test_cleanup_negative_keep_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".sap" / "transactions").mkdir(parents=True)
            with self.assertRaises(ValueError):
                cleanup_snapshots(root, keep=-1)

    def test_cleanup_missing_transactions_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            removed = cleanup_snapshots(root, keep=5)
            self.assertEqual(removed, [])

    def test_cleanup_ignores_malformed_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transactions = root / ".sap" / "transactions"
            transactions.mkdir(parents=True)

            # Directory without metadata.json should be ignored
            bad_dir = transactions / "not_a_transaction"
            bad_dir.mkdir()

            removed = cleanup_snapshots(root, keep=0)
            self.assertEqual(removed, [])
            self.assertTrue(bad_dir.is_dir())

    def test_cleanup_leaves_unrelated_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sap_dir = root / ".sap"
            sap_dir.mkdir(parents=True)

            # Create an unrelated file inside .sap
            history_file = sap_dir / "history.jsonl"
            history_file.write_text('unrelated data\n')

            removed = cleanup_snapshots(root, keep=0)
            self.assertEqual(removed, [])
            self.assertTrue(history_file.is_file())
