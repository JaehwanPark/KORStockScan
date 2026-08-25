from __future__ import annotations

import gzip
import json
from datetime import date

from src.engine.monitoring import widget_mechanical_entry_replay as replay


def _payload(*, best_bid: int = 100_300, best_ask: int = 100_400) -> dict:
    closes = [
        100_000,
        99_900,
        100_100,
        100_000,
        100_200,
        100_100,
        100_300,
        100_200,
        100_400,
        100_400,
    ]
    bars = []
    for index, close in enumerate(closes):
        open_price = close - 100 if index % 2 == 0 else close + 50
        bars.append(
            {
                "t": f"09:{index:02d}",
                "o": open_price,
                "h": max(open_price, close) + 50,
                "l": min(open_price, close) - 50,
                "c": close,
                "v": 1_500 if close > open_price else 1_000,
                "forming": False,
                "partial_volume": False,
            }
        )
    return {
        "endpoint": "analyze_target",
        "request_id": "analyze_target:123456:test",
        "captured_at": "2026-08-04T09:10:05+09:00",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "replay_exact": True,
        "payload_sha256": "a" * 64,
        "sanitized_user_input": {
            "exact_payload": {
                "current": {"price": 100_400},
                "quote": {
                    "quote_stale": False,
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                },
                "orderbook_top1": {
                    "bid": {"price": best_bid, "volume": 10},
                    "ask": {"price": best_ask, "volume": 5},
                },
                "entry_candle_context": {
                    "schema": "entry_candle_context_v1",
                    "venue": "KRX",
                    "session": "krx_regular",
                    "completed_bar_count": 10,
                    "forming_bar_present": False,
                    "bars": bars,
                    "source_quality": {"status": "fresh_consistent"},
                    "multi_timeframe_context": {
                        "captured_at": "2026-08-04T09:10:05+09:00",
                        "previous_day_levels": {
                            "date": "2026-08-03",
                            "high": 102_000,
                            "low": 98_000,
                            "close": 100_000,
                            "source_quality": "pass",
                        },
                    },
                },
            }
        },
    }


def _label() -> dict:
    return {
        "decision_trace_id": "analyze_target:123456:test",
        "decision_stage": "entry_screen",
        "decision_ts": "2026-08-04T09:10:05+09:00",
        "stock_code": "123456",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "action": "WAIT",
        "score": 70,
        "confidence": 65,
        "reference_price": 100_400,
        "label_status": "mature",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "entry_path_first_hit": "target_first",
                "mfe_pct": 0.8,
                "mae_pct": -0.2,
                "end_return_pct": 0.5,
            }
        },
    }


def test_portable_core_replays_exact_widget_axes_without_ready_promotion():
    result = replay.evaluate_portable_widget_core(_payload())

    assert result["state"] == "ENTRY_CAUTION"
    assert result["candidate_before_spread_gate"] is True


def test_portable_core_uses_separate_exact_replay_context():
    payload = _payload()
    exact_replay_context = payload.pop("sanitized_user_input")
    payload.update(
        {
            "sanitized_user_input": {
                "input_schema": "entry_setup_v2_14_live_input",
                "entry_setup_evidence_v1": {"setup_state": "READY"},
            },
            "replay_context_present": True,
            "replay_context_exact": True,
            "sanitized_replay_context": exact_replay_context,
        }
    )

    result = replay.evaluate_portable_widget_core(payload)

    assert result["state"] == "ENTRY_CAUTION"
    assert result["candidate_before_spread_gate"] is True
    assert result["entry_price_low"] <= result["entry_price_high"] < 100_400
    assert "symbol_generic_relative_strength_unavailable" in (
        result["unmet_conditions"]
    )
    assert result["runtime_effect"] is False
    assert result["actual_order_submitted"] is False


def test_wide_spread_remains_blocked_but_is_visible_in_sensitivity():
    payload = _payload(best_bid=99_900, best_ask=100_400)
    result = replay.evaluate_portable_widget_core(payload)

    assert result["state"] == "WATCH"
    assert result["candidate_before_spread_gate"] is True
    assert result["spread_ticks"] > 2
    assert result["unmet_conditions"] == ["spread_within_two_ticks"]


def test_naive_capture_time_is_rejected_as_source_quality_gap():
    payload = _payload()
    context = payload["sanitized_user_input"]["exact_payload"]["entry_candle_context"]
    context["multi_timeframe_context"]["captured_at"] = "2026-08-04T09:10:05"
    payload["captured_at"] = "2026-08-04T09:10:05"

    result = replay.evaluate_portable_widget_core(payload)

    assert result == {"state": "DATA_WAIT", "source_issue": "decision_time_missing"}


def test_report_joins_same_trace_and_keeps_runtime_authority_false():
    report = replay.build_report(
        [_payload()],
        {"analyze_target:123456:test": _label()},
        target_date=date(2026, 8, 4),
    )

    mechanical = report["summary"]["mechanical_signal_executable_comparable"]
    assert mechanical["sample_count"] == 0
    assert report["summary"]["mechanical_signal_raw_count"] == 1
    assert report["summary"]["mechanical_signal_price_noncomparable_count"] == 1
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    symbol = report["summary"]["stock_code_cohorts"]["123456"]
    assert symbol["all_joined_rows"]["sample_count"] == 1
    assert symbol["mechanical_signals"]["sample_count"] == 1
    assert symbol["mechanical_state_counts"] == {"ENTRY_CAUTION": 1}


def test_cli_stdout_is_machine_readable_json(capsys):
    assert replay.main(["--target-date", "2026-08-04"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "widget_mechanical_entry_replay_v1"


def test_same_symbol_range_within_one_minute_is_one_mechanical_episode():
    base = {
        "decision_ts": "2026-08-04T13:23:12+09:00",
        "stock_code": "006340",
        "effective_venue": "KRX",
        "mechanical_entry_price_low": 13_580,
        "mechanical_entry_price_high": 13_590,
    }
    repeated = {**base, "decision_ts": "2026-08-04T13:23:16+09:00"}

    accepted, duplicates = replay._dedupe_mechanical_episodes([base, repeated])

    assert accepted == [base]
    assert duplicates == 1


def test_source_loaders_read_strict_gzip_only_generations(tmp_path):
    payload_path = tmp_path / "ai_decision_payloads_2026-08-04.jsonl"
    label_path = tmp_path / "ai_decision_outcome_labels_2026-08-04.json"
    with gzip.open(
        payload_path.with_suffix(".jsonl.gz"), "wt", encoding="utf-8"
    ) as handle:
        handle.write(json.dumps({"decision_trace_id": "trace-1"}) + "\n")
    with gzip.open(
        label_path.with_suffix(".json.gz"), "wt", encoding="utf-8"
    ) as handle:
        json.dump(
            {"labels": [{"decision_trace_id": "trace-1", "label_status": "mature"}]},
            handle,
        )

    assert replay._load_jsonl(payload_path) == [
        {"decision_trace_id": "trace-1", "_line_number": 1}
    ]
    assert replay._load_labels(label_path)["trace-1"]["label_status"] == "mature"
