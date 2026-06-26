import json

from src.engine.lifecycle import stop_loss_recovery_backtest as mod


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_stop_loss_recovery_backtest_flags_recoverable_soft_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "SCALE_IN_CF_DIR", tmp_path / "scale_in_cf")

    _write_jsonl(
        tmp_path / "pipeline_events" / "pipeline_events_2026-06-05.jsonl",
        [
            {
                "pipeline": "HOLDING_PIPELINE",
                "stage": "exit_signal",
                "emitted_at": "2026-06-05T10:00:00+09:00",
                "record_id": 1,
                "stock_code": "123456",
                "stock_name": "SOFT",
                "fields": {
                    "exit_rule": "scalp_soft_stop_pct",
                    "sell_reason_type": "LOSS",
                    "profit_rate": "-1.00",
                },
            },
            {
                "pipeline": "HOLDING_PIPELINE",
                "stage": "exit_signal",
                "emitted_at": "2026-06-05T10:05:00+09:00",
                "record_id": 2,
                "stock_code": "234567",
                "stock_name": "HARD",
                "fields": {
                    "exit_rule": "scalp_hard_stop_pct",
                    "sell_reason_type": "LOSS",
                    "profit_rate": "-2.00",
                },
            },
            {
                "pipeline": "HOLDING_PIPELINE",
                "stage": "exit_signal",
                "emitted_at": "2026-06-05T10:10:00+09:00",
                "record_id": 3,
                "stock_code": "345678",
                "stock_name": "MFE",
                "fields": {
                    "exit_rule": "scalp_mfe_protect_exit",
                    "sell_reason_type": "PROFIT_PROTECT",
                    "profit_rate": "-0.20",
                },
            },
            {
                "pipeline": "HOLDING_PIPELINE",
                "stage": "exit_signal",
                "emitted_at": "2026-06-05T10:15:00+09:00",
                "record_id": 4,
                "stock_code": "456789",
                "stock_name": "POSITIVE_PROTECT",
                "fields": {
                    "exit_rule": "protect_trailing_stop",
                    "sell_reason_type": "PROFIT_PROTECT",
                    "profit_rate": "+0.30",
                },
            },
        ],
    )
    _write_jsonl(
        tmp_path / "post_sell" / "post_sell_evaluations_2026-06-05.jsonl",
        [
            {
                "recommendation_id": 1,
                "buy_price": 100,
                "sell_price": 99,
                "metrics_10m": {"mfe_pct": 0.9, "close_ret_pct": 0.2},
                "metrics_30m": {"mfe_pct": 0.4, "close_ret_pct": 0.1},
                "metrics_60m": {"mfe_pct": 0.1, "close_ret_pct": 0.0},
            },
            {
                "recommendation_id": 2,
                "buy_price": 100,
                "sell_price": 98,
                "metrics_10m": {"mfe_pct": 0.1, "close_ret_pct": -0.4},
            },
            {
                "recommendation_id": 3,
                "buy_price": 100,
                "sell_price": 99.8,
                "metrics_10m": {"mfe_pct": 0.3, "close_ret_pct": 0.1},
            },
        ],
    )

    report = mod.build_report("2026-06-05", start_date="2026-06-05", end_date="2026-06-07")

    assert report["source_dates"] == ["2026-06-05"]
    assert report["summary"]["exit_count"] == 3
    soft = report["summary"]["by_exit_family"]["scalp_hard_soft_stop"]
    assert soft["exit_count"] == 2
    assert soft["hard_safety_count"] == 1
    assert soft["recovery_eligible_count"] == 1
    assert soft["avg_down_recovery_possible_count"] == 1
    mfe = report["summary"]["by_exit_family"]["mfe_protect"]
    assert mfe["exit_count"] == 1
    assert mfe["hard_safety_count"] == 0
    assert report["runtime_effect"] is False
    assert report["rows"][0]["avg_down_recovery"]["horizons"]["10m"]["avg_down_recovery_possible"] is True
    assert report["summary"]["post_sell_evaluation_count"] == 3
    assert report["summary"]["recovery_eligible_evaluated_count"] == 2
    recommendations = report["summary"]["stop_line_recommendations_by_family"]
    assert recommendations["scalp_hard_soft_stop"]["evaluated_count"] == 1
    assert recommendations["mfe_protect"]["recommended_runtime_env"] == {
        "KORSTOCKSCAN_SCALP_MFE_PROTECT_TRIGGER_PROFIT_PCT": "-0.3"
    }
