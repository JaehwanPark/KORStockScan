import json
import sys

from src.engine import trade_pause_cli as cli_mod


def test_trade_pause_cli_pause_resume_status(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        cli_mod,
        "set_buy_side_pause",
        lambda paused, **kwargs: calls.append((paused, kwargs)) or paused,
    )
    monkeypatch.setattr(cli_mod, "is_buy_side_paused", lambda: True)
    monkeypatch.setattr(cli_mod, "get_pause_state_label", lambda: "신규 매수 및 추가매수 중단 상태")

    monkeypatch.setattr(
        sys,
        "argv",
        ["trade_pause_cli.py", "pause", "--source", "codex_prompt", "--reason", "guard backup"],
    )
    assert cli_mod._main() == 0
    pause_payload = json.loads(capsys.readouterr().out)

    monkeypatch.setattr(sys, "argv", ["trade_pause_cli.py", "resume", "--source", "codex_prompt"])
    assert cli_mod._main() == 0
    resume_payload = json.loads(capsys.readouterr().out)

    monkeypatch.setattr(sys, "argv", ["trade_pause_cli.py", "status"])
    assert cli_mod._main() == 0
    status_payload = json.loads(capsys.readouterr().out)

    assert calls[0] == (True, {"source": "codex_prompt", "reason": "guard backup"})
    assert calls[1] == (False, {"source": "codex_prompt", "reason": None})
    assert pause_payload["command"] == "pause"
    assert resume_payload["command"] == "resume"
    assert status_payload["command"] == "status"
    assert status_payload["paused"] is True
