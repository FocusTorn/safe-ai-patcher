import json
import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.history import load_history, record_transaction


class HistoryTests(unittest.TestCase):
    def test_records_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            record_transaction(
                root,
                status="committed",
                paths=["hello.txt"],
                test_command=["python", "-m", "unittest"],
            )

            history = root / ".sap" / "history.jsonl"
            self.assertTrue(history.is_file())

            record = json.loads(history.read_text(encoding="utf-8"))

            self.assertTrue(record["id"])
            self.assertTrue(record["timestamp"])
            self.assertEqual(record["status"], "committed")
            self.assertEqual(record["paths"], ["hello.txt"])
            self.assertEqual(
                record["test_command"],
                ["python", "-m", "unittest"],
            )

    def test_records_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            record_transaction(
                root,
                status="rolled_back",
                paths=["hello.txt"],
                error="test failed",
            )

            record = json.loads(
                (root / ".sap" / "history.jsonl").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(record["status"], "rolled_back")
            self.assertEqual(record["error"], "test failed")

    def test_loads_newest_first_with_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            record_transaction(
                root,
                status="committed",
                paths=["first.txt"],
            )
            record_transaction(
                root,
                status="rolled_back",
                paths=["second.txt"],
                error="failed",
            )

            records = load_history(root, limit=1)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["status"], "rolled_back")
            self.assertEqual(records[0]["paths"], ["second.txt"])

    def test_missing_history_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_history(tmp), [])


if __name__ == "__main__":
    unittest.main()
