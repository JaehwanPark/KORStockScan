import json
from pathlib import Path

from src.engine import runtime_approval_summary as summary_mod
from src.engine import verify_threshold_cycle_postclose_chain as mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed(monkeypatch, tmp_path: Path, target: str):
    data = tmp_path / "data"
    report = data / "report"
    monkeypatch.setattr(summary_mod, "DATA_DIR", data)
    monkeypatch.setattr(summary_mod, "REPORT_DIR", report / "runtime_approval_summary")
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", report)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report / "threshold_cycle_postclose_verification")
    for owner, path in summary_mod._paths(target).items():
        if owner in summary_mod.REQUIRED_DIRECT_OWNERS:
            _write(path, {"report_type": owner, "target_date": target, "status": "pass"})
    summary = summary_mod.build_runtime_approval_summary(target)
    status_path = report / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json"
    _write(status_path, {"target_date": target, "status": "succeeded"})
    return summary


def test_verifier_passes_without_retired_daily_ev_or_generic_preopen(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "pass"
    assert report["issues"] == []
    assert report["retired_common_layers"] == [
        "daily_threshold_cycle_report",
        "threshold_cycle_ev_report",
        "threshold_cycle_preopen_apply",
    ]


def test_verifier_recomputes_direct_source_hash(monkeypatch, tmp_path):
    target = "2026-09-19"
    summary = _seed(monkeypatch, tmp_path, target)
    Path(summary["sources"]["entry_split"]["path"]).write_text("{}", encoding="utf-8")

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "fail"
    assert "direct_source_hash_mismatch:entry_split" in report["issues"]


def test_optional_direct_receipt_may_be_absent(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)

    report = mod.build_threshold_cycle_postclose_verification(target)

    optional = next(row for row in report["direct_source_checks"] if row["owner"] == "entry_split_policy")
    assert optional["exists"] is False
    assert optional["required"] is False
    assert report["status"] == "pass"


def test_missing_postclose_terminal_fails_closed(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    (mod.REPORT_DIR / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json").unlink()

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "fail"
    assert "postclose_terminal_status_missing" in report["issues"]
