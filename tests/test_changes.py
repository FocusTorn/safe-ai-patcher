import json
import tempfile
import unittest
from pathlib import Path

from safe_ai_patcher.changes import generate_diff, load_changes
from safe_ai_patcher.core import PatchError


class ChangeFileTests(unittest.TestCase):
    def test_loads_change_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "change.json"
            path.write_text(
                json.dumps({
                    "changes": [
                        {"path": "hello.txt", "content": "hello"}
                    ]
                }),
                encoding="utf-8",
            )

            result = load_changes(path)

            self.assertEqual(len(result.changes), 1)
            self.assertEqual(result.changes[0].path, "hello.txt")
            self.assertEqual(result.changes[0].content, "hello")

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "change.json"
            path.write_text("{broken", encoding="utf-8")

            with self.assertRaises(PatchError):
                load_changes(path)

    def test_rejects_missing_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "change.json"
            path.write_text("{}", encoding="utf-8")

            with self.assertRaises(PatchError):
                load_changes(path)

    def test_diff_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()

            from safe_ai_patcher.core import Change

            with self.assertRaises(PatchError):
                generate_diff(
                    root,
                    [Change("../outside.txt", "unsafe")],
                )

    def test_generates_diff_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "hello.txt"
            target.write_text("old\n", encoding="utf-8")

            from safe_ai_patcher.core import Change

            diff = generate_diff(
                root,
                [Change("hello.txt", "new\n")],
            )

            self.assertIn("-old", diff)
            self.assertIn("+new", diff)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "old\n",
            )


if __name__ == "__main__":
    unittest.main()
