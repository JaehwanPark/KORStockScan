from __future__ import annotations

import json

from src.engine.monitoring import quote_consistency_report as mod


def test_quote_consistency_report_flags_defective_rows(monkeypatch, tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    pipeline_dir.mkdir()
    threshold_dir.mkdir()
    path = pipeline_dir / "pipeline_events_2026-06-27.jsonl"
    rows = [
        {
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "stage": "entry_submit_revalidation_block",
            "stock_code": "005930",
            "fields": {
                "quote_consistency_family": "quote_consistency_normalization",
                "quote_consistency_state": "diverged",
                "canonical_mark_price": 10000,
                "executable_buy_price": 9990,
                "executable_sell_price": 9990,
                "ws_rest_gap_bps": 120.5,
                "price_source": "ws_primary_rest_diverged",
                "normalization_runtime_effect": True,
            },
        },
        {
            "event_type": "pipeline_event",
            "pipeline": "HOLDING_PIPELINE",
            "stage": "sell_order_sent",
            "stock_code": "000660",
            "fields": {
                "quote_consistency_family": "quote_consistency_normalization",
                "quote_consistency_state": "ok",
                "canonical_mark_price": 50000,
                "executable_buy_price": 49950,
                "executable_sell_price": 49950,
                "ws_rest_gap_bps": 4.0,
                "price_source": "ws_rest_mid",
                "normalization_runtime_effect": True,
                "quote_consistency_safety_exit": True,
            },
        },
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", threshold_dir)

    report = mod.build_quote_consistency_report("2026-06-27")

    assert report["summary"]["observed_count"] == 2
    assert report["summary"]["ev_input_blocked_count"] == 1
    assert report["summary"]["safety_exit_count"] == 1
    assert report["summary"]["gap_bps"]["max"] == 120.5
    assert report["stage_state_counts"]["entry_submit_revalidation_block"]["diverged"] == 1
    assert report["defective_row_candidates"][0]["quote_consistency_state"] == "diverged"
