"""The retired compatibility CLI cannot scan raw data or publish policy."""

import json
from pathlib import Path
import pytest
import src.engine.scalp_sim_ev_midcheck as midcheck


def test_retired_midcheck_does_not_scan_or_publish(monkeypatch):
    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "open", lambda *a, **k: pytest.fail("retired IO"))
        report = midcheck.build_report("2026-05-11")
        output = midcheck.write_outputs(report, force=True)
    assert report == output
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["decision_authority"] == "archive_only"
    assert "scale_in_analysis" not in report


def test_retired_midcheck_cli_cannot_force_reactivation(monkeypatch, capsys):
    monkeypatch.setattr(
        midcheck, "build_report", lambda *a, **k: pytest.fail("retired scan")
    )
    monkeypatch.setattr(
        midcheck, "write_outputs", lambda *a, **k: pytest.fail("retired publication")
    )
    assert midcheck.main(["--target-date", "2026-05-11", "--force"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "retired"
    assert result["allowed_runtime_apply"] is False
