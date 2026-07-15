import json

import src.engine.scalp_sim_ai_deferred_review as deferred_review


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
    monkeypatch.setattr(deferred_review, "DATA_DIR", data_dir)

    report = deferred_review.build_report(target_date)

    assert report["summary"]["deferred_count"] == 1
    assert report["summary"]["critical_class_counts"] == {"soft_critical": 1}
    assert report["summary"]["critical_reason_counts"] == {
        "feature_signature_changed": 1,
        "soft_loss": 1,
    }
    assert report["rows"][0]["critical_class"] == "soft_critical"
    assert report["rows"][0]["loss_bucket"] == "(-0.20,0)"
