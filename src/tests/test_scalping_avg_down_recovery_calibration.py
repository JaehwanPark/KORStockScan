"""Operator retirement: no historical raw scan, replay or report publication."""
import json
from src.engine.monitoring import scalping_avg_down_recovery_calibration as module


def test_retired_report_is_explicit_and_cannot_produce_candidates():
    report = module.build_report("2026-09-17")
    assert report["status"] == "retired"
    assert report["allowed_runtime_apply"] is False
    assert report["calibration_candidates"] == []


def test_retired_cli_does_not_publish_or_load_sources(capsys, monkeypatch):
    monkeypatch.setattr(module, "build_report", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no source work")))
    assert module.main(["--target-date", "2026-09-17", "--force"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "retired"
