from safe_ai_patcher.cli import main


def test_cli_exists():
    assert callable(main)
