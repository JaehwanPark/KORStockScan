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


def test_quote_consistency_missing_required_fields_are_warning_when_ev_blocked(monkeypatch, tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    pipeline_dir.mkdir()
    threshold_dir.mkdir()
    path = pipeline_dir / "pipeline_events_2026-06-29.jsonl"
    (threshold_dir / "threshold_events_2026-06-29.jsonl").write_text("", encoding="utf-8")
    row = {
        "event_type": "pipeline_event",
        "pipeline": "SCALE_IN_PIPELINE",
        "stage": "scale_in_price_guard_block",
        "stock_code": "005930",
        "fields": {
            "quote_consistency_family": "quote_consistency_normalization",
            "quote_consistency_state": "stale",
            "canonical_mark_price": 10000,
            "executable_buy_price": 9990,
            "executable_sell_price": 9990,
            "normalization_runtime_effect": True,
        },
    }
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", threshold_dir)

    report = mod.build_quote_consistency_report("2026-06-29")

    assert report["summary"]["missing_required_fields"] == 1
    assert report["summary"]["missing_required_fields_ev_blocked_count"] == 1
    assert report["summary"]["ev_input_blocked_count"] == 1
    assert report["verifier_findings"] == [
        {
            "severity": "warning",
            "code": "quote_consistency_required_fields_excluded",
            "count": 1,
            "ev_blocked_count": 1,
            "message": "Rows with missing quote consistency required fields were excluded from EV input.",
        }
    ]


def test_quote_consistency_partitioned_threshold_events_satisfy_source_contract(monkeypatch, tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    pipeline_dir.mkdir()
    partition_dir = threshold_dir / "date=2026-06-30" / "family=quote_consistency_normalization"
    partition_dir.mkdir(parents=True)
    (pipeline_dir / "pipeline_events_2026-06-30.jsonl").write_text("", encoding="utf-8")
    (partition_dir / "part-000001.jsonl").write_text(
        json.dumps(
            {
                "event_type": "pipeline_event",
                "stage": "entry_submit_revalidation_block",
                "stock_code": "005930",
                "fields": {
                    "quote_consistency_family": "quote_consistency_normalization",
                    "quote_consistency_state": "ok",
                    "canonical_mark_price": 10000,
                    "executable_buy_price": 9990,
                    "executable_sell_price": 9990,
                    "price_source": "ws_rest_mid",
                    "normalization_runtime_effect": True,
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", threshold_dir)

    report = mod.build_quote_consistency_report("2026-06-30")

    assert report["summary"]["observed_count"] == 1
    assert not any(item["code"] == "quote_consistency_source_missing" for item in report["verifier_findings"])
    assert report["sources"]["threshold_events"] is None
    assert len(report["sources"]["threshold_events_partitioned"]) == 1


def test_quote_consistency_report_backfills_blank_ws_price_source(monkeypatch, tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    pipeline_dir.mkdir()
    threshold_dir.mkdir()
    (threshold_dir / "threshold_events_2026-06-30.jsonl").write_text("", encoding="utf-8")
    (pipeline_dir / "pipeline_events_2026-06-30.jsonl").write_text(
        json.dumps(
            {
                "stage": "scale_in_price_guard_block",
                "stock_code": "005930",
                "fields": {
                    "quote_consistency_family": "quote_consistency_normalization",
                    "quote_consistency_state": "single_source",
                    "quote_consistency_reason": "ws_only_fresh",
                    "canonical_mark_price": 10000,
                    "executable_buy_price": 10010,
                    "executable_sell_price": 10000,
                    "price_source": "",
                    "normalization_runtime_effect": True,
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", threshold_dir)

    report = mod.build_quote_consistency_report("2026-06-30")

    assert report["summary"]["observed_count"] == 1
    assert report["summary"]["missing_required_fields"] == 0
    assert report["source_counts"] == {"ws": 1}
    assert report["verifier_findings"] == []
