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
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


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
        "tick_context_quality": "fresh_computed",
        "tick_accel_source": "computed_10ticks",
        "quote_age_ms": 100,
        "quote_age_source": "last_ws_update_ts",
        "tick_acceleration_ratio": 1.25,
        "curr_vs_micro_vwap_bp": 12.0,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "minute_candle_context_quality": "fresh_completed_bars",
        "decision_quality_contract_status": "pass",
        "edge_state": "EDGE",
        "entry_probe_intent": True,
        "entry_probe_intent_status": "eligible_wait_probe",
        "evidence_trigger": "recovery_required",
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
        "tick_context_quality": "fresh_computed",
        "tick_accel_source": "computed_10ticks",
        "quote_age_ms": 100,
        "quote_age_source": "last_ws_update_ts",
        "minute_candle_source_quality_gate": minute_candle_source_quality_gate,
        "tick_acceleration_ratio": 1.25,
        "curr_vs_micro_vwap_bp": 12.0,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "minute_candle_context_quality": "fresh_completed_bars",
        "decision_quality_contract_status": "pass",
        "edge_state": "EDGE",
        "entry_probe_intent": True,
        "entry_probe_intent_status": "eligible_wait_probe",
        "evidence_trigger": "recovery_required",
        "minute_candle_source_quality_reason": (
            "no_ka10080_bars_in_forward_10m_window"
            if minute_candle_source_quality_gate == "source_quality_insufficient"
            else (
                "ka10080_truncated_window"
                if minute_candle_source_quality_gate == "source_quality_warning"
                else "ka10080_forward_window_available"
            )
        ),
    }


def test_supported_wait_contract_missing_reasons_are_instrumentation_only():
    row = {"_score": 66, "ai_action": "WAIT"}

    reasons = mod._supported_wait_contract_missing_reasons(row)

    assert "decision_quality_contract_status_missing" in reasons
    assert "edge_state_missing" in reasons
    assert "entry_probe_intent_missing" in reasons
    assert "recovery_trigger_missing" in reasons
    assert "tick_pressure_provenance_missing" in reasons
    assert "micro_vwap_provenance_missing" in reasons
    assert mod._canonical_supported_wait_action(row) == "WAIT"


def test_entry_ai_gate_micro_context_rejects_not_evaluated_quality():
    assert not mod._micro_context_usable(
        {
            "tick_context_quality": "not_evaluated",
            "tick_accel_source": "not_evaluated",
            "quote_age_source": "not_evaluated",
        }
    )
    assert not mod._micro_context_usable(
        {
            "tick_context_quality": "not_evaluated_pre_contract",
            "tick_accel_source": "not_evaluated",
            "quote_age_source": "not_evaluated_pre_contract",
        }
    )


def test_entry_ai_gate_backtest_excludes_pre_baseline_and_separates_metrics(
    tmp_path, monkeypatch
):
    adm_dir = tmp_path / "adm"
    missed_dir = tmp_path / "missed"
    out_dir = tmp_path / "out"
    monkeypatch.setattr(mod, "SCALP_ENTRY_ADM_DIR", adm_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "REPORT_DIR", out_dir)
    runtime_env_dir = tmp_path / "runtime_env"
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_env_dir)
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
        lambda dates, policy: (
            [d for d in dates if d >= "2026-06-04"],
            [d for d in dates if d < "2026-06-04"],
        ),
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
    realized_rows = [
        _realized_row(66, profit=1.2) for _ in range(mod.REALIZED_SAMPLE_FLOOR)
    ]
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
        _counterfactual_row(66, close_10m=1.5)
        for _ in range(mod.COUNTERFACTUAL_SAMPLE_FLOOR)
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
    _write_json(
        adm_dir / "scalp_entry_action_decision_matrix_2026-06-05.json",
        {"rows": realized_rows},
    )
    _write_json(
        missed_dir / "missed_entry_counterfactual_2026-06-05.json",
        {"full_rows": counterfactual_rows},
    )
    _write_json(
        runtime_env_dir / "threshold_runtime_env_2026-06-05.json",
        {
            "env_overrides": {
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "false",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": "70",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE": "74.999",
            }
        },
    )

    report = mod.build_report(
        "2026-06-05", start_date="2026-06-03", end_date="2026-06-05"
    )

    assert report["source_dates"] == ["2026-06-04", "2026-06-05"]
    assert "2026-06-03" in report["excluded_dates"]
    assert report["summary"]["best_policy"] == "supported_wait_recovery"
    assert report["summary"]["best_threshold"] <= 66
    assert report["summary"]["sample_floor_passed"] is True
    assert report["allowed_runtime_apply"] is True
    assert report["summary"]["best_apply_policy"] == "supported_wait_recovery"
    assert report["summary"]["best_apply_threshold"] <= 66
    assert report["best_candidate"]["realized"]["sample"] == mod.REALIZED_SAMPLE_FLOOR
    assert (
        report["best_candidate"]["counterfactual"]["sample"]
        == mod.COUNTERFACTUAL_SAMPLE_FLOOR
    )
    assert (
        report["best_candidate"]["counterfactual"]["missed_upside_close_10m_pct"] == 1.5
    )
    assert report["best_apply_candidate"]["policy"] == "supported_wait_recovery"
    assert report["summary"]["bounded_calibration_candidate_count"] == 1
    runtime_update = report["runtime_update_contract"]
    assert runtime_update["update_mode"] == "single_cumulative_quality_update"
    assert runtime_update["max_runtime_apply_count"] == 1
    assert runtime_update["runtime_apply_candidate_count"] == 1
    assert runtime_update["allowed_runtime_apply_count"] == 1
    assert runtime_update["cumulative_quality_window"]["start_date"] == ("2026-06-04")
    calibration = report["calibration_candidates"][0]
    assert calibration["family"] == "entry_opportunity_recheck_runtime"
    assert calibration["allowed_runtime_apply"] is True
    assert calibration["recommended_values"]["min_ai_score"] <= 66
    assert calibration["recommended_values"]["allow_wait_probe_intent"] is True
    assert calibration["recommended_values"]["require_explicit_buy_action"] is False
    assert calibration["current_values"]["enabled"] is False
    assert calibration["runtime_update_mode"] == ("single_cumulative_quality_update")
    assert calibration["max_runtime_apply_count"] == 1
    assert calibration["quality_update_id"] == runtime_update["quality_update_id"]
    assert calibration["post_apply_attribution_required"] is True
    assert "broad_buy_score_threshold_relaxation" in calibration["forbidden_uses"]
    markdown = mod.render_markdown(report)
    assert "runtime_update_mode: `single_cumulative_quality_update`" in markdown
    assert "runtime_apply_candidate_count: `1`" in markdown

    diagnostic = next(
        item
        for item in report["policy_results"]
        if item["policy"] == "diagnostic_score_only" and item["threshold"] == 66
    )
    strict = next(
        item
        for item in report["policy_results"]
        if item["policy"] == "strict_buy" and item["threshold"] == 80
    )
    assert diagnostic["allowed_runtime_apply"] is False
    assert (
        diagnostic["counterfactual"]["sample"]
        > report["best_candidate"]["counterfactual"]["sample"]
    )
    assert (
        report["best_diagnostic_score_only_candidate"]["allowed_runtime_apply"] is False
    )
    assert report["summary"]["best_diagnostic_score_only_threshold"] <= 66
    assert (
        report["best_positive_realized_diagnostic_candidate"]["allowed_runtime_apply"]
        is False
    )
    assert report["summary"]["best_positive_realized_diagnostic_threshold"] >= 66
    assert report["summary"]["best_positive_realized_diagnostic_ev_pct"] > 0
    assert strict["realized"]["sample"] == 1
    assert strict["counterfactual"]["sample"] == 1


def test_entry_ai_gate_role_gate_and_threshold_helper(monkeypatch):
    rules = replace(gate.TRADING_RULES, BUY_SCORE_THRESHOLD=70)
    monkeypatch.setattr(gate, "TRADING_RULES", rules)

    assert gate.entry_buy_decision_allowed("BUY", 72)
    assert gate.entry_buy_decision_allowed("BUY", 69.9)
    assert gate.entry_buy_decision_allowed("BUY", 68, {"BUY_SCORE_THRESHOLD": 65})
    assert not gate.entry_buy_decision_allowed("WAIT", 90)

    low_prior = gate.evaluate_ai_score_prior("BUY", 69.9)
    assert low_prior["score_gate_converted_to_prior"] is True
    assert low_prior["hard_gate_veto"] is False
    assert low_prior["score_prior_band"] == "low"

    usable = gate.evaluate_entry_score_role_gate(
        {"action": "BUY", "score": 72, "ai_result_source": "live", "ai_parse_ok": True},
        ws_data={"quote_stale": False},
    )
    assert usable["entry_score_usable_for_entry_submit"] is True
    assert usable["entry_score_usable_for_recheck"] is False

    valid_wait_recheck = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 72,
            "ai_result_source": "live",
            "ai_parse_ok": True,
            "decision_quality_contract_status": "pass",
            "edge_state": "EDGE",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "evidence": {"trigger": "recovery_required"},
        },
        ws_data={"quote_stale": False},
    )
    assert valid_wait_recheck["entry_score_usable_for_recheck"] is True

    stale_wait_recheck = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 72,
            "ai_result_source": "live",
            "ai_parse_ok": True,
            "decision_quality_contract_status": "pass",
            "edge_state": "EDGE",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "evidence": {"trigger": "recovery_required"},
        },
        ws_data={"quote_stale": True},
    )
    assert stale_wait_recheck["entry_score_usable_for_entry_submit"] is False
    assert stale_wait_recheck["entry_score_usable_for_recheck"] is True
    assert stale_wait_recheck["entry_recheck_source_usable"] is True
    assert stale_wait_recheck["entry_recheck_freshness_refresh_required"] is True
    assert stale_wait_recheck["entry_score_excluded_reason"] == (
        "stale_quote_or_context"
    )
    assert stale_wait_recheck["entry_recheck_excluded_reason"] == "-"

    blocking_adverse_wait = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 72,
            "ai_result_source": "live",
            "ai_parse_ok": True,
            "decision_quality_contract_status": "pass",
            "edge_state": "EDGE",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "evidence": {
                "trigger": "recovery_required",
                "adverse_risk": "blocking",
            },
        },
        ws_data={"quote_stale": True},
    )
    assert blocking_adverse_wait["entry_score_usable_for_entry_submit"] is False
    assert blocking_adverse_wait["entry_score_usable_for_recheck"] is False
    assert blocking_adverse_wait["entry_recheck_adverse_risk"] == "blocking"

    normalized_wait_recheck = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 72,
            "ai_result_source": "live",
            "ai_parse_ok": True,
            "decision_quality_contract_status": "pass",
            "decision_quality_model_edge_state": "EDGE",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "evidence": {"trigger": "recovery_required"},
        },
        ws_data={"quote_stale": False},
    )
    assert normalized_wait_recheck["entry_score_usable_for_recheck"] is True
    assert normalized_wait_recheck["entry_recheck_edge_state"] == "EDGE"

    stale = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 68,
            "ai_result_source": "live",
            "ai_parse_ok": True,
        },
        ws_data={"quote_stale": True},
    )
    assert stale["entry_score_usable_for_entry_submit"] is False
    assert stale["entry_score_excluded_reason"] == "stale_quote_or_context"

    fallback = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 50,
            "ai_result_source": "fallback_score_50",
            "ai_fallback_score_50": True,
        }
    )
    assert fallback["entry_score_usable_for_recheck"] is False
    assert fallback["entry_recheck_source_usable"] is False
    assert fallback["entry_recheck_freshness_refresh_required"] is False
    assert fallback["entry_recheck_excluded_reason"] == "fallback_score_50"
    assert fallback["entry_score_excluded_reason"] == "fallback_score_50"

    lock_contention = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 68,
            "ai_result_source": "live_lock_contention_rejected",
        }
    )
    assert lock_contention["entry_score_usable_for_entry_submit"] is False
    assert (
        lock_contention["entry_score_excluded_reason"]
        == "unusable_source:live_lock_contention_rejected"
    )

    insufficient = gate.evaluate_entry_score_role_gate(
        {
            "action": "WAIT",
            "score": 68,
            "ai_result_source": "source_quality_insufficient",
        }
    )
    assert insufficient["entry_score_usable_for_recheck"] is False

    stale_parse_token = gate.evaluate_entry_score_role_gate(
        {
            "action": "BUY",
            "score": 72,
            "ai_result_source": "live",
            "ai_parse_ok": "stale",
        },
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
    fully_confirmed = {
        **micro_vwap_with_provenance,
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 2,
        "tick_context_quality": "fresh_computed",
        "tick_accel_source": "computed_10ticks",
        "tick_acceleration_ratio": 1.2,
    }

    assert mod._micro_support(untrusted_pressure_only) is False
    assert mod._micro_support(trusted_pressure) is False
    assert mod._micro_support(independent_tick_accel) is False
    assert mod._micro_support(independent_tick_accel_with_source) is False
    assert mod._micro_support(micro_vwap_without_provenance) is False
    assert mod._micro_support(micro_vwap_without_minute_quality) is False
    assert mod._micro_support(micro_vwap_with_provenance) is False
    assert mod._micro_support(fully_confirmed) is True
    assert mod._micro_support(stale_micro_vwap) is False
    assert mod._micro_support(stale_pressure_flag) is False


def test_entry_ai_gate_backtest_blocks_non_positive_primary_ev_apply_candidate():
    realized_rows = [
        {
            **_realized_row(66, action="WAIT", profit=-0.2),
            "_score": 66,
            "_realized_profit_pct": -0.2,
        }
        for _ in range(mod.REALIZED_SAMPLE_FLOOR)
    ]
    counterfactual_rows = [
        {
            **_counterfactual_row(66, action="WAIT", close_10m=0.5),
            "_score": 66,
            "_close_10m_pct": 0.5,
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


def test_entry_ai_gate_backtest_blocks_non_positive_counterfactual_opportunity(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    _write_json(
        runtime_dir / "threshold_runtime_env_2026-06-05.json",
        {
            "env_overrides": {
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "false",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": "70",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE": "74.999",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION": "true",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT": "false",
                "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT": "true",
            }
        },
    )
    realized_rows = [
        {
            **_realized_row(66, action="WAIT", profit=0.5),
            "_score": 66,
            "_realized_profit_pct": 0.5,
        }
        for _ in range(mod.REALIZED_SAMPLE_FLOOR)
    ]
    counterfactual_rows = [
        {
            **_counterfactual_row(66, action="WAIT", close_10m=-0.3),
            "_score": 66,
            "_close_10m_pct": -0.3,
            "_mfe_10m_pct": -0.1,
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
    assert result["primary_ev_positive"] is True
    assert result["counterfactual_opportunity_positive"] is False
    assert result["allowed_runtime_apply"] is False
    assert result["apply_block_reason"] == ("non_positive_counterfactual_opportunity")

    candidate = mod._entry_recheck_calibration_candidates(
        result,
        target_date="2026-06-05",
        cumulative_quality_window={
            "start_date": "2026-06-05",
            "end_date": "2026-06-05",
        },
    )
    assert candidate[0]["allowed_runtime_apply"] is False
    assert candidate[0]["counterfactual_opportunity_positive"] is False
    assert candidate[0]["apply_block_reason"] == (
        "non_positive_counterfactual_opportunity"
    )


def test_entry_ai_gate_backtest_realized_join_uses_real_post_sell_once(
    tmp_path, monkeypatch
):
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
    _write_json(
        missed_dir / "missed_entry_counterfactual_2026-06-05.json", {"full_rows": []}
    )
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
    strict = next(
        item
        for item in report["policy_results"]
        if item["policy"] == "strict_buy" and item["threshold"] == 75
    )

    assert report["summary"]["realized_joined_rows"] == 1
    assert strict["realized"]["sample"] == 1
    assert strict["realized"]["equal_weight_avg_profit_pct"] == 2.5


def test_entry_ai_gate_backtest_joins_counterfactual_to_entry_snapshot(
    tmp_path, monkeypatch
):
    adm_dir = tmp_path / "adm"
    missed_dir = tmp_path / "missed"
    monkeypatch.setattr(mod, "SCALP_ENTRY_ADM_DIR", adm_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    _write_json(
        adm_dir / "scalp_entry_action_decision_matrix_2026-06-05.json",
        {
            "rows": [
                {
                    **_realized_row(66, action="WAIT", profit=1.0),
                    "record_id": "R1",
                    "candidate_id": "ADM-R1",
                    "stage": "scalp_entry_action_decision_snapshot",
                    "ai_action": "not_evaluated",
                    "chosen_action": "WAIT_REQUOTE",
                }
            ]
        },
    )
    _write_json(
        missed_dir / "missed_entry_counterfactual_2026-06-05.json",
        {
            "full_rows": [
                {
                    "record_id": "R1",
                    "candidate_id": "MISSED-R1",
                    "anchor_stage": "scalp_entry_action_decision_snapshot",
                    "ai_score": 66,
                    "close_10m_pct": 1.25,
                    "mfe_10m_pct": 1.5,
                    "mae_10m_pct": -0.2,
                    "minute_candle_source_quality_gate": "pass",
                    "minute_candle_source_quality_reason": (
                        "ka10080_forward_window_available"
                    ),
                }
            ]
        },
    )

    report = mod.build_report("2026-06-05")
    supported = next(
        item
        for item in report["policy_results"]
        if item["policy"] == "supported_wait_recovery" and item["threshold"] == 66
    )

    assert supported["counterfactual"]["sample"] == 1
    assert (
        mod._canonical_supported_wait_action(
            {
                "ai_action": "not_evaluated",
                "chosen_action": "WAIT_REQUOTE",
            }
        )
        == "WAIT_REQUOTE"
    )
    assert report["summary"]["counterfactual_context_joined_count"] == 1
    assert report["summary"]["counterfactual_context_not_joined_count"] == 0
    assert (
        report["summary"]["supported_wait_recovery_source_contract_status"]
        == "evaluable"
    )
    assert (
        report["summary"]["supported_wait_recovery_realized_policy_eligible_rows"] == 1
    )
    assert (
        report["summary"]["supported_wait_recovery_counterfactual_policy_eligible_rows"]
        == 1
    )
    assert report["source_consumption"]["effective_source_dates"] == ["2026-06-05"]
    assert report["runtime_update_contract"]["cumulative_quality_window"][
        "source_dates"
    ] == ["2026-06-05"]


def test_entry_ai_gate_backtest_excludes_invalid_json_source_date(
    tmp_path, monkeypatch
):
    adm_dir = tmp_path / "adm"
    missed_dir = tmp_path / "missed"
    monkeypatch.setattr(mod, "SCALP_ENTRY_ADM_DIR", adm_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    _write_json(
        adm_dir / "scalp_entry_action_decision_matrix_2026-06-05.json",
        {"rows": [_realized_row(66, action="WAIT", profit=1.0)]},
    )
    corrupt = missed_dir / "missed_entry_counterfactual_2026-06-05.json"
    corrupt.parent.mkdir(parents=True, exist_ok=True)
    corrupt.write_text('{"full_rows": [', encoding="utf-8")

    report = mod.build_report("2026-06-05")

    missing = next(
        item
        for item in report["missing_artifacts"]
        if item["artifact"] == "missed_entry_counterfactual"
    )
    window = report["runtime_update_contract"]["cumulative_quality_window"]
    assert missing["status"] == "invalid_json"
    assert missing["error"].startswith("JSONDecodeError:")
    assert report["source_consumption"]["effective_source_dates"] == []
    assert report["source_consumption"]["artifact_excluded_dates"] == ["2026-06-05"]
    assert window["source_date_count"] == 0
    assert window["artifact_excluded_dates"] == ["2026-06-05"]
    assert report["calibration_state"] == "source_contract_not_evaluable"
    assert report["allowed_runtime_apply"] is False


def test_entry_ai_gate_backtest_source_quality_preflight_blocks_apply(
    tmp_path, monkeypatch
):
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
        {
            "rows": [
                _realized_row(66, profit=1.0) for _ in range(mod.REALIZED_SAMPLE_FLOOR)
            ]
        },
    )
    _write_json(
        missed_dir / "missed_entry_counterfactual_2026-06-05.json",
        {
            "full_rows": [
                _counterfactual_row(66, close_10m=1.0)
                for _ in range(mod.COUNTERFACTUAL_SAMPLE_FLOOR)
            ]
        },
    )

    report = mod.build_report("2026-06-05")

    assert report["status"] == "source_quality_blocked"
    assert report["allowed_runtime_apply"] is False
    assert report["calibration_state"] == "source_quality_blocked"
    assert report["source_quality_gate"] == "blocked_contract_gap"
    assert report["summary"]["allowed_runtime_apply"] is False
    assert report["summary"]["calibration_state"] == "source_quality_blocked"
    assert report["best_apply_candidate"] == {}
    assert report["summary"]["source_quality_excluded_date_count"] == 1
    assert (
        report["source_consumption"]["source_quality_excluded_dates"][0]["source_date"]
        == "2026-06-05"
    )
    assert report["calibration_candidates"] == []
    assert report["runtime_update_contract"]["runtime_apply_candidate_count"] == 0
    assert report["runtime_update_contract"]["allowed_runtime_apply_count"] == 0
