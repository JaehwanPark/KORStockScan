import json

from src.engine.monitoring import quote_consistency_backtest as mod


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_quote_consistency_backtest_blocks_diverged_buy_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", tmp_path / "threshold_cycle")
    _write_jsonl(
        tmp_path / "pipeline_events" / "pipeline_events_2026-06-24.jsonl",
        [
            {
                "stage": "latency_pass",
                "stock_code": "000001",
                "fields": {
                    "pre_submit_ws_snapshot_refresh_latest_price": 10000,
                    "pre_submit_ws_snapshot_refresh_best_bid": 9990,
                    "pre_submit_ws_snapshot_refresh_best_ask": 10010,
                    "pre_submit_ws_snapshot_refresh_age_ms": 10,
                    "pre_submit_rest_orderbook_refresh_best_bid": 9500,
                    "pre_submit_rest_orderbook_refresh_best_ask": 9520,
                    "pre_submit_rest_orderbook_refresh_age_ms": 20,
                    "mark_price_at_submit": 10000,
                },
            }
        ],
    )

    report = mod.build_quote_consistency_backtest(
        start_date="2026-06-24",
        end_date="2026-06-24",
    )

    assert report["summary"]["observed_quote_rows"] == 1
    assert report["summary"]["rest_input_rows"] == 1
    assert report["summary"]["state_counts"]["diverged"] == 1
    assert report["summary"]["would_block_entry_reprice_scale_in"] == 1
    assert report["summary"]["ev_input_excluded_rows"] == 1


def test_quote_consistency_backtest_safety_exit_does_not_block(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", tmp_path / "threshold_cycle")
    _write_jsonl(
        tmp_path / "pipeline_events" / "pipeline_events_2026-06-24.jsonl",
        [
            {
                "stage": "emergency_sell",
                "stock_code": "000002",
                "fields": {
                    "latest_price": 10000,
                    "best_bid_at_submit": 9900,
                    "best_ask_at_submit": 10050,
                    "quote_age_at_submit_ms": 900,
                    "sell_reason": "emergency_stop",
                },
            }
        ],
    )

    report = mod.build_quote_consistency_backtest(
        start_date="2026-06-24",
        end_date="2026-06-24",
    )

    assert report["summary"]["state_counts"]["stale"] == 1
    assert report["summary"]["safety_exit_unblocked"] == 1
    assert report["summary"].get("would_block_entry_reprice_scale_in", 0) == 0
