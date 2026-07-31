from __future__ import annotations

import json

from src.engine import scalp_sim_ai_deferred_review as mod


def test_deferred_review_preserves_ai_budget_critical_attribution(
    tmp_path, monkeypatch
):
    data_dir = tmp_path / "data"
    event_dir = data_dir / "pipeline_events"
    event_dir.mkdir(parents=True)
    target_date = "2026-05-11"
    path = event_dir / f"pipeline_events_{target_date}.jsonl"
    row = {
        "stage": "scalp_sim_ai_holding_deferred",
        "stock_name": "Alpha",
        "stock_code": "111111",
        "emitted_at": "2026-05-11T10:00:00",
        "fields": {
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": "False",
            "defer_reason": "sim_ai_budget_exhausted",
            "critical_class": "soft_critical",
            "critical_reason": "soft_loss,feature_signature_changed",
            "soft_critical_deferred": "True",
            "hard_critical_bypass": "False",
            "loss_bucket": "(-0.20,0)",
            "drawdown_pct": "0.15",
            "profit_rate": "-0.05",
            "peak_profit": "0.10",
        },
    }
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "DATA_DIR", data_dir)

    report = mod.build_report(target_date)

    assert report["summary"]["deferred_count"] == 1
    assert report["summary"]["critical_class_counts"] == {"soft_critical": 1}
    assert report["summary"]["critical_reason_counts"] == {
        "feature_signature_changed": 1,
        "soft_loss": 1,
    }
    assert report["rows"][0]["critical_class"] == "soft_critical"
    assert report["rows"][0]["loss_bucket"] == "(-0.20,0)"


def test_build_report_streams_and_retains_only_deferred_rows(monkeypatch):
    events = iter(
        [
            {"stage": "unrelated", "fields": {"large": "ignored"}},
            {
                "stage": "scalp_sim_ai_holding_deferred",
                "stock_code": "005930",
                "fields": {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "defer_reason": "budget_exhausted",
                    "source_stage": "holding",
                    "critical_class": "soft",
                    "critical_reason": "drawdown,stale_feature",
                },
            },
            {
                "stage": "scalp_sim_ai_holding_deferred",
                "fields": {
                    "simulation_book": "other",
                    "actual_order_submitted": False,
                },
            },
        ]
    )
    monkeypatch.setattr(mod, "_iter_events", lambda _target_date: events)

    report = mod.build_report("2026-07-31")

    assert report["summary"]["deferred_count"] == 1
    assert report["summary"]["defer_reason_counts"] == {"budget_exhausted": 1}
    assert report["summary"]["critical_reason_counts"] == {
        "drawdown": 1,
        "stale_feature": 1,
    }
    assert [row["stock_code"] for row in report["rows"]] == ["005930"]
    assert report["source_read_contract"] == {
        "read_mode": "streaming_stage_filter",
        "full_source_materialized": False,
        "retained_scope": "scalp_sim_ai_holding_deferred_rows_only",
    }
