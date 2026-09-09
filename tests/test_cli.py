import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from safe_ai_patcher.changes import Change
from safe_ai_patcher.cli import main
from safe_ai_patcher.core import apply_changes


class CLIApplyTests(unittest.TestCase):
    def test_apply_prints_transaction_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname='test'\n")
            target = root / "test.txt"
            target.write_text("original\n")
            change_file = root / "change.json"
            change_file.write_text(
                '{"changes":[{"path":"test.txt","content":"patched\\n"}]}'
            )

            with patch("safe_ai_patcher.cli.detect_project", return_value=type("Project", (), {"root": root})()):
                with patch("sys.stdout") as stdout:
                    result = main(["apply", str(change_file)])

            self.assertEqual(result, 0)
            output = "".join(
                call.args[0] for call in stdout.write.call_args_list
                if call.args
            )
            self.assertIn("Applied safely: 1 change(s)", output)
            self.assertIn("Transaction:", output)


class CLIRollbackTests(unittest.TestCase):
    def test_rollback_succeeds_when_history_recording_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname='test'\n")
            target = root / "test.txt"
            target.write_text("original\n")

            transaction_id = apply_changes(
                root,
                [Change(path="test.txt", content="patched\n")],
            )

            with patch("safe_ai_patcher.history.record_transaction", side_effect=OSError("history unavailable")):
                with patch("safe_ai_patcher.cli.detect_project", return_value=type("Project", (), {"root": root})()):
                    result = main(["rollback", transaction_id])

            self.assertEqual(result, 0)
            self.assertEqual(target.read_text(), "original\n")


if __name__ == "__main__":
    unittest.main()
