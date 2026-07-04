import json
from dataclasses import replace

import pytest

from src.engine.scalping import entry_ai_gate as gate
from src.engine.scalping import entry_ai_gate_backtest as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _realized_row(score, *, action="WAIT", profit=1.0, stale=False, hard_blocked=False):
    return {
        "ai_score": score,
        "ai_action": action,
        "profit_rate": profit,
        "actual_order_submitted": True,
        "broker_order_submitted": True,
        "quote_stale": stale,
        "blocked_reason": "broker_guard_block" if hard_blocked else "",
        "buy_pressure_10t": 75,
        "net_aggressive_delta_10t": 10,
        "tick_aggressor_trusted_count": 2,
        "tick_aggressor_pressure_usable": True,
    }


def _counterfactual_row(
    score,
    *,
    action="WAIT",
    close_10m=1.0,
    stale=False,
    hard_blocked=False,
    minute_candle_source_quality_gate="pass",
):
    return {
        "ai_score": score,
        "ai_action": action,
        "close_10m_pct": close_10m,
        "mfe_10m_pct": close_10m + 0.2,
        "mae_10m_pct": -0.2,
        "quote_stale": stale,
        "blocked_reason": "cooldown_block" if hard_blocked else "",
        "buy_pressure_10t": 74,
        "net_aggressive_delta_10t": 1,
        "tick_aggressor_trusted_count": 2,
        "tick_aggressor_pressure_usable": True,
        "minute_candle_source_quality_gate": minute_candle_source_quality_gate,
        "minute_candle_source_quality_reason": (
            "no_ka10080_bars_in_forward_10m_window"
            if minute_candle_source_quality_gate == "source_quality_insufficient"
            else "ka10080_truncated_window"
            if minute_candle_source_quality_gate == "source_quality_warning"
            else "ka10080_forward_window_available"
        ),
    }


def test_entry_ai_gate_backtest_excludes_pre_baseline_and_separates_metrics(tmp_path, monkeypatch):
    adm_dir = tmp_path / "adm"
    missed_dir = tmp_path / "missed"
    out_dir = tmp_path / "out"
    monkeypatch.setattr(mod, "SCALP_ENTRY_ADM_DIR", adm_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "REPORT_DIR", out_dir)
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {
            "clean_tuning_baseline_date": "2026-06-04",
            "clean_tuning_baseline_ts_kst": "2026-06-04T14:29:09+09:00",
        },
    )
    monkeypatch.setattr(
        mod,
        "filter_allowed_dates",
        lambda dates, policy: ([d for d in dates if d >= "2026-06-04"], [d for d in dates if d < "2026-06-04"]),
    )
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)

    _write_json(
        adm_dir / "scalp_entry_action_decision_matrix_2026-06-03.json",
        {"rows": [_realized_row(66, profit=99.0)]},
    )
    _write_json(
        missed_dir / "missed_entry_counterfactual_2026-06-03.json",
        {"full_rows": [_counterfactual_row(66, close_10m=99.0)]},
    )
    realized_rows = [_realized_row(66, profit=1.2) for _ in range(mod.REALIZED_SAMPLE_FLOOR)]
    realized_rows.extend(
        [
            _realized_row(66, profit=10.0, stale=True),
            _realized_row(66, profit=10.0, hard_blocked=True),
            _realized_row(80, action="BUY", profit=0.4),
            _realized_row(80, action="BUY", profit=20.0, stale=True),
            _realized_row(80, action="BUY", profit=20.0, hard_blocked=True),
        ]
    )
    counterfactual_rows = [
        _counterfactual_row(66, close_10m=1.5) for _ in range(mod.COUNTERFACTUAL_SAMPLE_FLOOR)
    ]
    counterfactual_rows.extend(
        [
            _counterfactual_row(66, close_10m=12.0, stale=True),
            _counterfactual_row(66, close_10m=12.0, hard_blocked=True),
            _counterfactual_row(
                66,
                close_10m=25.0,
                minute_candle_source_quality_gate="source_quality_insufficient",
            ),
            _counterfactual_row(
                66,
                close_10m=30.0,
                minute_candle_source_quality_gate="source_quality_warning",
            ),
            _counterfactual_row(80, action="BUY", close_10m=0.5),
            _counterfactual_row(80, action="BUY", close_10m=20.0, stale=True),
            _counterfactual_row(80, action="BUY", close_10m=20.0, hard_blocked=True),
        ]
    )
    _write_json(adm_dir / "scalp_entry_action_decision_matrix_2026-06-05.json", {"rows": realized_rows})
    _write_json(missed_dir / "missed_entry_counterfactual_2026-06-05.json", {"full_rows": counterfactual_rows})

    report = mod.build_report("2026-06-05", start_date="2026-06-03", end_date="2026-06-05")

    assert report["source_dates"] == ["2026-06-04", "2026-06-05"]
    assert "2026-06-03" in report["excluded_dates"]
    assert report["summary"]["best_policy"] == "supported_wait_recovery"
    assert report["summary"]["best_threshold"] <= 66
    assert report["summary"]["sample_floor_passed"] is True
    assert report["allowed_runtime_apply"] is True
    assert report["summary"]["best_apply_policy"] == "supported_wait_recovery"
    assert report["summary"]["best_apply_threshold"] <= 66
    assert report["best_candidate"]["realized"]["sample"] == mod.REALIZED_SAMPLE_FLOOR
    assert report["best_candidate"]["counterfactual"]["sample"] == mod.COUNTERFACTUAL_SAMPLE_FLOOR
    assert report["best_candidate"]["counterfactual"]["missed_upside_close_10m_pct"] == 1.5
    assert report["best_apply_candidate"]["policy"] == "supported_wait_recovery"

    diagnostic = next(
        item
        for item in report["policy_results"]
        if item["policy"] == "diagnostic_score_only" and item["threshold"] == 66
    )
    strict = next(item for item in report["policy_results"] if item["policy"] == "strict_buy" and item["threshold"] == 80)
    assert diagnostic["allowed_runtime_apply"] is False
    assert diagnostic["counterfactual"]["sample"] > report["best_candidate"]["counterfactual"]["sample"]
    assert report["best_diagnostic_score_only_candidate"]["allowed_runtime_apply"] is False
    assert report["summary"]["best_diagnostic_score_only_threshold"] <= 66
    assert report["best_positive_realized_diagnostic_candidate"]["allowed_runtime_apply"] is False
    assert report["summary"]["best_positive_realized_diagnostic_threshold"] >= 66
    assert report["summary"]["best_positive_realized_diagnostic_ev_pct"] > 0
    assert strict["realized"]["sample"] == 1
    assert strict["counterfactual"]["sample"] == 1


def test_entry_ai_gate_role_gate_and_threshold_helper(monkeypatch):
    rules = replace(gate.TRADING_RULES, BUY_SCORE_THRESHOLD=70)
    monkeypatch.setattr(gate, "TRADING_RULES", rules)

    assert gate.entry_buy_decision_allowed("BUY", 72)
    assert not gate.entry_buy_decision_allowed("BUY", 69.9)
    assert gate.entry_buy_decision_allowed("BUY", 68, {"BUY_SCORE_THRESHOLD": 65})

    usable = gate.evaluate_entry_score_role_gate(
        {"action": "BUY", "score": 72, "ai_result_source": "live", "ai_parse_ok": True},
        ws_data={"quote_stale": False},
    )
    assert usable["entry_score_usable_for_entry_submit"] is True
    assert usable["entry_score_usable_for_recheck"] is True

    stale = gate.evaluate_entry_score_role_gate(
        {"action": "WAIT", "score": 68, "ai_result_source": "live", "ai_parse_ok": True},
        ws_data={"quote_stale": True},
    )
    assert stale["entry_score_usable_for_entry_submit"] is False
    assert stale["entry_score_excluded_reason"] == "stale_quote_or_context"

    fallback = gate.evaluate_entry_score_role_gate(
        {"action": "WAIT", "score": 50, "ai_result_source": "fallback_score_50", "ai_fallback_score_50": True}
    )
    assert fallback["entry_score_usable_for_recheck"] is False
    assert fallback["entry_score_excluded_reason"] == "fallback_score_50"

    lock_contention = gate.evaluate_entry_score_role_gate(
        {"action": "WAIT", "score": 68, "ai_result_source": "live_lock_contention_rejected"}
    )
    assert lock_contention["entry_score_usable_for_entry_submit"] is False
    assert lock_contention["entry_score_excluded_reason"] == "unusable_source:live_lock_contention_rejected"

    insufficient = gate.evaluate_entry_score_role_gate(
        {"action": "WAIT", "score": 68, "ai_result_source": "source_quality_insufficient"}
    )
    assert insufficient["entry_score_usable_for_recheck"] is False

    stale_parse_token = gate.evaluate_entry_score_role_gate(
        {"action": "BUY", "score": 72, "ai_result_source": "live", "ai_parse_ok": "stale"},
        ws_data={"quote_stale": False},
    )
    assert stale_parse_token["entry_score_usable_for_entry_submit"] is False
    assert stale_parse_token["entry_score_excluded_reason"] == "parse_fail_or_not_ok"

    stale_source_flag = gate.evaluate_entry_score_role_gate(
        {"action": "BUY", "score": 72, "ai_result_source": "live", "ai_parse_ok": True},
        ws_data={"quote_stale": "stale"},
    )
    assert stale_source_flag["entry_score_excluded_reason"] == "stale_quote_or_context"


def test_entry_ai_gate_backtest_ignores_untrusted_pressure_micro_support():
    untrusted_pressure_only = {
        "buy_pressure_10t": 95,
        "net_aggressive_delta_10t": 500,
        "tick_aggressor_pressure_usable": False,
        "tick_aggressor_trusted_count": 0,
        "tick_acceleration_ratio": 1.0,
        "curr_vs_micro_vwap_bp": 0.0,
    }
    trusted_pressure = {
        **untrusted_pressure_only,
        "tick_aggressor_pressure_usable": True,
    }
    independent_tick_accel = {
        **untrusted_pressure_only,
        "tick_acceleration_ratio": 1.2,
    }
    independent_tick_accel_with_source = {
        **independent_tick_accel,
        "tick_context_quality": "fresh_computed",
        "tick_accel_source": "computed_10ticks",
    }
    micro_vwap_without_provenance = {
        **untrusted_pressure_only,
        "curr_vs_micro_vwap_bp": 35.0,
        "quote_age_ms": 100,
        "quote_age_source": "last_ws_update_ts",
    }
    micro_vwap_with_provenance = {
        **micro_vwap_without_provenance,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
    }
    micro_vwap_without_minute_quality = {
        **micro_vwap_without_provenance,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
    }
    stale_micro_vwap = {
        **micro_vwap_with_provenance,
        "minute_candle_window_fresh": False,
    }
    stale_pressure_flag = {
        **untrusted_pressure_only,
        "tick_aggressor_pressure_usable": "stale",
    }

    assert mod._micro_support(untrusted_pressure_only) is False
    assert mod._micro_support(trusted_pressure) is True
    assert mod._micro_support(independent_tick_accel) is False
    assert mod._micro_support(independent_tick_accel_with_source) is True
    assert mod._micro_support(micro_vwap_without_provenance) is False
    assert mod._micro_support(micro_vwap_without_minute_quality) is False
    assert mod._micro_support(micro_vwap_with_provenance) is True
    assert mod._micro_support(stale_micro_vwap) is False
    assert mod._micro_support(stale_pressure_flag) is False


def test_entry_ai_gate_backtest_blocks_non_positive_primary_ev_apply_candidate():
    realized_rows = [
        {
            "_score": 66,
            "_realized_profit_pct": -0.2,
            "ai_action": "WAIT",
            "buy_pressure_10t": 75,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        }
        for _ in range(mod.REALIZED_SAMPLE_FLOOR)
    ]
    counterfactual_rows = [
        {
            "_score": 66,
            "_close_10m_pct": 0.5,
            "ai_action": "WAIT",
            "buy_pressure_10t": 75,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        }
        for _ in range(mod.COUNTERFACTUAL_SAMPLE_FLOOR)
    ]

    result = mod._policy_result(
        policy="supported_wait_recovery",
        threshold=66,
        realized_rows=realized_rows,
        counterfactual_rows=counterfactual_rows,
    )

    assert result["sample_floor_passed"] is True
    assert result["primary_ev_positive"] is False
    assert result["allowed_runtime_apply"] is False
    assert result["apply_block_reason"] == "non_positive_primary_ev"


def test_entry_ai_gate_backtest_realized_join_uses_real_post_sell_once(tmp_path, monkeypatch):
    adm_dir = tmp_path / "adm"
    missed_dir = tmp_path / "missed"
    post_sell_dir = tmp_path / "post_sell"
    monkeypatch.setattr(mod, "SCALP_ENTRY_ADM_DIR", adm_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {
            "clean_tuning_baseline_date": "2026-06-04",
            "clean_tuning_baseline_ts_kst": "2026-06-04T14:29:09+09:00",
        },
    )
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)

    _write_json(
        adm_dir / "scalp_entry_action_decision_matrix_2026-06-05.json",
        {
            "rows": [
                {
                    "record_id": "100",
                    "stage": "order_bundle_submitted",
                    "source_stage": "order_bundle_submitted",
                    "score_source_value": 0,
                    "chosen_action": "BUY_NOW",
                    "profit_rate": -99.0,
                    "outcome_joined": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "record_id": "100",
                    "stage": "scalp_entry_action_decision_snapshot",
                    "source_stage": "ai_confirmed",
                    "ai_score": 76,
                    "ai_action": "BUY",
                    "chosen_action": "BUY_NOW",
                    "actual_order_submitted": False,
                },
                {
                    "record_id": "100",
                    "stage": "blocked_ai_score",
                    "source_stage": "blocked_ai_score",
                    "ai_score": 76,
                    "ai_action": "BUY",
                    "chosen_action": "NO_BUY_AI",
                    "actual_order_submitted": False,
                },
            ]
        },
    )
    _write_json(missed_dir / "missed_entry_counterfactual_2026-06-05.json", {"full_rows": []})
    _write_jsonl(
        post_sell_dir / "post_sell_evaluations_2026-06-05.jsonl",
        [
            {
                "recommendation_id": 100,
                "strategy": "SCALPING",
                "stock_code": "005930",
                "profit_rate": 2.5,
                "post_sell_id": "PS1",
                "exit_rule": "take_profit",
            }
        ],
    )

    report = mod.build_report("2026-06-05")
    strict = next(item for item in report["policy_results"] if item["policy"] == "strict_buy" and item["threshold"] == 75)

    assert report["summary"]["realized_joined_rows"] == 1
    assert strict["realized"]["sample"] == 1
    assert strict["realized"]["equal_weight_avg_profit_pct"] == 2.5


def test_entry_ai_gate_backtest_source_quality_preflight_blocks_apply(tmp_path, monkeypatch):
    adm_dir = tmp_path / "adm"
    missed_dir = tmp_path / "missed"
    monkeypatch.setattr(mod, "SCALP_ENTRY_ADM_DIR", adm_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "required_field_missing",
            "hard_blocking_contract_gap_count": 1,
            "clean_baseline_enforced": True,
        },
    )
    _write_json(
        adm_dir / "scalp_entry_action_decision_matrix_2026-06-05.json",
        {"rows": [_realized_row(66, profit=1.0) for _ in range(mod.REALIZED_SAMPLE_FLOOR)]},
    )
    _write_json(
        missed_dir / "missed_entry_counterfactual_2026-06-05.json",
        {"full_rows": [_counterfactual_row(66, close_10m=1.0) for _ in range(mod.COUNTERFACTUAL_SAMPLE_FLOOR)]},
    )

    report = mod.build_report("2026-06-05")

    assert report["status"] == "source_quality_blocked"
    assert report["allowed_runtime_apply"] is False
    assert report["calibration_state"] == "source_quality_blocked"
    assert report["source_quality_gate"] == "blocked_contract_gap"
    assert report["summary"]["allowed_runtime_apply"] is False
    assert report["summary"]["calibration_state"] == "source_quality_blocked"
    assert report["best_apply_candidate"]["allowed_runtime_apply"] is False
