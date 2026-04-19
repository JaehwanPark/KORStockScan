import json

from src.engine.split_entry_followup_audit import (
    summarize_latency_canary,
    summarize_split_entry_soft_stop,
)


def test_summarize_latency_canary_counts_reasons(tmp_path):
    path = tmp_path / "pipeline_events.jsonl"
    rows = [
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "latency_block",
            "fields": {
                "quote_stale": "False",
                "latency_canary_reason": "low_signal",
            },
        },
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "latency_block",
            "fields": {
                "quote_stale": "True",
                "latency_canary_reason": "quote_stale",
            },
        },
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "latency_pass",
            "fields": {
                "quote_stale": "False",
                "latency_canary_applied": "True",
                "latency_canary_reason": "canary_applied",
            },
        },
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    summary = summarize_latency_canary(path)

    assert summary["stage_counts"] == {"latency_block": 2, "latency_pass": 1}
    assert summary["latency_block_quote_not_stale"] == 1
    assert summary["latency_canary_applied"] == 1
    assert summary["latency_canary_reasons"] == {
        "low_signal": 1,
        "quote_stale": 1,
        "canary_applied": 1,
    }


def test_summarize_split_entry_soft_stop_detects_integrity_and_repeats(tmp_path):
    path = tmp_path / "pipeline_events.jsonl"
    rows = [
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "position_rebased_after_fill",
            "record_id": 1,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:00:00.000000",
            "fields": {"fill_quality": "PARTIAL_FILL", "cum_filled_qty": "1", "requested_qty": "9"},
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "position_rebased_after_fill",
            "record_id": 1,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:00:00.500000",
            "fields": {"fill_quality": "FULL_FILL", "cum_filled_qty": "12", "requested_qty": "9"},
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "holding_started",
            "record_id": 1,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:00:01.000000",
            "fields": {"buy_qty": "12"},
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "exit_signal",
            "record_id": 1,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:01:00.000000",
            "fields": {"exit_rule": "scalp_soft_stop_pct", "held_sec": "59", "profit_rate": "-1.50", "peak_profit": "-0.10"},
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "position_rebased_after_fill",
            "record_id": 2,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:10:00.000000",
            "fields": {"fill_quality": "PARTIAL_FILL", "cum_filled_qty": "1", "requested_qty": "8"},
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "holding_started",
            "record_id": 2,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:10:01.000000",
            "fields": {"buy_qty": "1"},
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "exit_signal",
            "record_id": 2,
            "stock_name": "테스트A",
            "emitted_at": "2026-04-17T09:11:00.000000",
            "fields": {"exit_rule": "scalp_soft_stop_pct", "held_sec": "59", "profit_rate": "-1.60", "peak_profit": "0.05"},
        },
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    summary = summarize_split_entry_soft_stop(path)

    assert summary["case_count"] == 2
    assert summary["expanded_after_partial_count"] == 1
    assert summary["partial_only_count"] == 1
    assert summary["held_le_180_count"] == 2
    assert summary["integrity_issue_count"] == 1
    assert summary["peak_le_zero_count"] == 1
    assert summary["peak_lt_point2_count"] == 1
    assert summary["same_symbol_repeats"] == {"테스트A": 2}
    assert summary["cases"][0]["integrity_flags"] == ["cum_gt_requested", "same_ts_multi_rebase"]
