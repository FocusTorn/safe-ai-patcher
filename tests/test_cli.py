import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from safe_ai_patcher.changes import Change
from safe_ai_patcher.cli import main
from safe_ai_patcher.core import apply_changes


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
