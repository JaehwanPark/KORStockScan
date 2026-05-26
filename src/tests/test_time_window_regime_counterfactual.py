import json
from pathlib import Path

from src.engine.automation import time_window_regime_counterfactual as mod


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_time_window_regime_joins_entry_event_and_keeps_metrics_separate(tmp_path, monkeypatch):
    post_sell = tmp_path / "post_sell"
    threshold = tmp_path / "threshold_cycle"
    report = tmp_path / "report"
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", threshold)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", report / "monitor_snapshots")
    monkeypatch.setattr(mod, "REPORT_BASE_DIR", report / "time_window_regime_counterfactual")
    monkeypatch.setattr(mod, "SYSTEM_METRIC_SAMPLE_PATH", tmp_path / "missing-system-metrics.jsonl")

    _write_jsonl(
        post_sell / "sim_post_sell_candidates_2026-05-26.jsonl",
        [
            {
                "post_sell_id": "P1",
                "stock_code": "000001",
                "stock_name": "A",
                "candidate_id": "ADM-1",
                "entry_adm_candidate_id": "ADM-1",
                "sim_parent_record_id": "101",
                "buy_price": 10000,
                "sell_price": 9900,
                "buy_qty": 3,
                "profit_rate": -1.0,
                "exit_rule": "scalp_preset_hard_stop_pct",
                "sell_time": "09:25:00",
            },
            {
                "post_sell_id": "P2",
                "stock_code": "000002",
                "stock_name": "B",
                "candidate_id": "ADM-MISSING",
                "buy_price": 10000,
                "sell_price": 10100,
                "buy_qty": 2,
                "profit_rate": 1.0,
                "exit_rule": "take_profit",
                "sell_time": "09:15:00",
            },
        ],
    )
    _write_jsonl(
        threshold / "date=2026-05-26" / "family=scalp_entry_action_decision_matrix" / "part-000001.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "record_id": 101,
                "stock_code": "000001",
                "emitted_at": "2026-05-26T09:12:00+09:00",
                "fields": {"candidate_id": "ADM-1", "entry_adm_candidate_id": "ADM-1"},
            }
        ],
    )
    _write_json(
        report / "monitor_snapshots" / "wait6579_ev_cohort_2026-05-26.json",
        {
            "rows": [
                {
                    "signal_time": "09:18:00",
                    "stock_code": "000003",
                    "stock_name": "C",
                    "ai_score": 68,
                    "expected_ev_pct": 2.5,
                    "expected_ev_krw": 7000,
                    "terminal_blocker": "blocked_ai_score",
                }
            ]
        },
    )

    built = mod.build_time_window_regime_counterfactual_report("2026-05-26", max_rows=1000, max_seconds=100)

    assert built["runtime_effect"] is False
    assert built["allowed_runtime_apply"] is False
    assert built["actual_order_submitted"] is False
    assert built["broker_order_forbidden"] is True
    assert built["operator_seed_cutoffs"] == [{"cutoff": "09:30", "operator_seed_cutoff": True, "hard_gate": False}]
    assert built["summary"]["entry_time_join_rate"] == 0.5
    assert built["summary"]["unjoined_rate"] == 0.5
    assert built["summary"]["sell_time_fallback_rate"] == 0.0
    assert built["summary"]["completed_counterfactual_netting_allowed"] is False
    daily = next(item for item in built["rolling_windows"] if item["rolling_window"] == "daily")
    assert daily["completed_rows"] == 1
    assert daily["counterfactual_rows"] == 1
    before_0930 = next(item for item in daily["window_comparisons"] if item["window_id"] == "before_0930")
    assert before_0930["operator_seed_cutoff"] is True
    exception_policy = before_0930["policies"]["block_general_allow_exception_in_window"]
    assert exception_policy["combined_ev_netting_allowed"] is False
    assert exception_policy["blocked_completed_profit_krw_sum"] == -300
    assert exception_policy["counterfactual_expected_ev_krw_sum"] == 7000


def test_time_window_regime_io_guard_partial_resume_required(tmp_path, monkeypatch):
    post_sell = tmp_path / "post_sell"
    report = tmp_path / "report"
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", report / "monitor_snapshots")
    monkeypatch.setattr(mod, "REPORT_BASE_DIR", report / "time_window_regime_counterfactual")
    monkeypatch.setattr(mod, "SYSTEM_METRIC_SAMPLE_PATH", tmp_path / "missing-system-metrics.jsonl")
    _write_jsonl(
        post_sell / "sim_post_sell_candidates_2026-05-26.jsonl",
        [
            {
                "post_sell_id": "P1",
                "stock_code": "000001",
                "buy_price": 10000,
                "sell_price": 9900,
                "buy_qty": 1,
                "profit_rate": -1.0,
                "exit_rule": "hard_stop",
            }
        ],
    )

    built = mod.build_time_window_regime_counterfactual_report("2026-05-26", max_rows=1, max_seconds=100)

    assert built["status"] == "partial"
    assert built["summary"]["resume_required"] is True
    assert "max_rows_reached" in built["summary"]["paused_reason"]

    resumed = mod.build_time_window_regime_counterfactual_report(
        "2026-05-26",
        max_rows=1000,
        max_seconds=100,
        resume=True,
    )
    assert resumed["status"] == "warning"
    assert resumed["summary"]["resume_mode_requested"] is True
    assert resumed["summary"]["resume_cache_hits"] == ["2026-05-26"]
