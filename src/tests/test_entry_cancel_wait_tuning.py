import json

from src.engine.automation import entry_cancel_wait_tuning as mod


def test_hold_preserves_thresholds_without_samples(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    payload = mod.build_report("2026-06-12")
    assert payload["recommended_thresholds"] == mod.DEFAULT_THRESHOLDS
    assert payload["enabled"] is True
    assert payload["automatic_off_allowed"] is False
    assert all(
        item["calibration_state"] == "hold_sample"
        for item in payload["profiles"].values()
    )


def test_deterministic_ev_applies_daily_step(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    rows = []
    for idx in range(5):
        for timeout, ev in ((60, -1.0), (90, 1.0)):
            rows.append(
                {
                    "stage": "entry_cancel_wait_counterfactual_completed",
                    "fields": {
                        "runtime_family": "entry_cancel_wait_runtime",
                        "wait_profile": "standard",
                        "timeout_sec": timeout,
                        "counterfactual_ev_pct": ev,
                    },
                }
            )
    (event_dir / "pipeline_events_2026-06-12.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    payload = mod.build_report("2026-06-12")
    assert payload["recommended_thresholds"]["standard"] == 90
    assert payload["profiles"]["standard"]["calibration_state"] == "adjust"
