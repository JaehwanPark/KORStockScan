import json

import pytest

from src.engine.monitoring import scalping_pyramid_quality_calibration as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
        },
    )


def _row(record_id, label, *, max_profit_seen=None, final_profit_rate=None):
    row = {
        "record_id": str(record_id),
        "pyramid_feedback_label": label,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_pyramid_intraday_feedback_no_runtime_mutation",
        "forbidden_uses": ["intraday_threshold_mutation"],
    }
    if max_profit_seen is not None:
        row["max_profit_seen"] = max_profit_seen
    if final_profit_rate is not None:
        row["final_profit_rate"] = final_profit_rate
    return row


def _feedback(
    path,
    rows,
    *,
    source_quality="pass",
    one_share_rows=None,
    normal_winner_expansion_rows=None,
    real_scale_in_performance_rows=None,
    post_probe_real_outcome_contract=False,
    pyramid_min_profit_pct=1.5,
    winner_recovery_runtime_funnel=None,
    threshold_replay_rows=None,
):
    payload = {
        "schema_version": 5,
        "report_type": "scalping_pyramid_intraday_feedback",
        "target_date": path.stem.rsplit("_", 1)[-1],
        "source_quality": {"status": source_quality},
        "pyramid_feedback_rows": rows,
    }
    if pyramid_min_profit_pct is not None:
        payload["pyramid_threshold_provenance"] = {
            "ambiguous": False,
            "observed_min_profit_pct_values": [pyramid_min_profit_pct],
            "configured_v2_min_profit_pct_values": [pyramid_min_profit_pct],
            "configured_threshold_contract_valid": True,
            "selected_min_profit_pct": pyramid_min_profit_pct,
            "selection_source": "same_day_unique_runtime_pyramid_evaluation",
        }
    if one_share_rows is not None:
        payload["one_share_pyramid_opportunity_rows"] = one_share_rows
    if normal_winner_expansion_rows is not None:
        payload["normal_winner_expansion_rows"] = normal_winner_expansion_rows
    if real_scale_in_performance_rows is not None:
        payload["real_scale_in_performance_rows"] = real_scale_in_performance_rows
        payload["real_scale_in_performance_metric_contract"] = {
            "metric_role": "real_scale_in_execution_outcome_attribution"
        }
    if post_probe_real_outcome_contract:
        payload["post_probe_real_outcome_metric_contract"] = {
            "metric_role": "multi_leg_post_probe_real_outcome_attribution"
        }
    if winner_recovery_runtime_funnel is not None:
        payload["winner_recovery_runtime_funnel_metric_contract"] = {
            "metric_role": "winner_recovery_runtime_funnel_attribution"
        }
        payload["summary"] = {
            "winner_recovery_runtime_funnel": winner_recovery_runtime_funnel
        }
    if threshold_replay_rows is not None:
        payload["pyramid_threshold_replay_metric_contract"] = {
            "contract_version": "pyramid_gate_replay_source_v1",
            "metric_role": "bounded_tunable_threshold_gate_counterfactual",
            "decision_authority": (
                "source_only_fixed_observed_exit_pyramid_gate_replay"
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
        }
        payload["pyramid_threshold_replay_rows"] = threshold_replay_rows
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _replay_row(
    record_id,
    *,
    profit_rate=1.0,
    entry_price=10000,
    sell_price=10400,
    configured_min_profit_pct=1.1,
    observed_gate_selected=None,
):
    if observed_gate_selected is None:
        observed_gate_selected = profit_rate >= configured_min_profit_pct
    return {
        "pyramid_evaluation_id": f"record:{record_id}:event",
        "position_key": f"record:{record_id}",
        "source_event_ts": f"2026-09-04T10:{record_id % 60:02d}:00+09:00",
        "profit_rate": profit_rate,
        "pyramid_evaluation_schema": "pyramid_gate_observation_v2",
        "configured_min_profit_pct": configured_min_profit_pct,
        "effective_min_profit_pct": configured_min_profit_pct,
        "observed_gate_selected": observed_gate_selected,
        "strong_continuation_min_profit_pct": 0.9,
        "strong_continuation_allowed": False,
        "drawdown_from_peak": 0.0,
        "is_new_high": True,
        "current_ai_score": 75,
        "ai_score_available": True,
        "min_ai_score": 70,
        "buy_pressure_10t": 70,
        "min_buy_pressure": 60,
        "tick_acceleration_ratio": 1.2,
        "min_tick_accel": 0.5,
        "large_sell_print_detected": False,
        "curr_vs_micro_vwap_bp": 20,
        "max_micro_vwap_bps": 60,
        "micro_vwap_available": True,
        "reversal_feature_stale": False,
        "tick_context_stale": False,
        "tick_aggressor_trusted_count": 5,
        "tick_aggressor_pressure_usable": True,
        "quote_stale": False,
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "executable_best_ask": entry_price + 10,
        "executable_best_bid": entry_price,
        "pyramid_price_resolver_observed": True,
        "pyramid_price_resolver_allowed": True,
        "pyramid_price_resolver_reason": "scale_in_price_resolved",
        "pyramid_price_resolver_price_source": "best_bid",
        "pyramid_price_resolver_order_price": entry_price,
        "pyramid_price_resolver_best_ask": entry_price + 10,
        "pyramid_price_resolver_best_bid": entry_price,
        "replay_entry_price": entry_price,
        "sell_price": sell_price,
        "price_evidence_level": "fresh_quote_existing_resolver_limit_price",
        "gate_replay_source_quality_valid": True,
        "fixed_exit_economic_replay_ready": True,
        "source_quality_reasons": [],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": ("source_only_fixed_observed_exit_pyramid_gate_replay"),
        "forbidden_uses": ["intraday_threshold_mutation"],
    }


def _write_verified_runtime_env(runtime_dir, target_date, min_profit_pct):
    runtime_dir.mkdir(parents=True, exist_ok=True)
    manifest = runtime_dir / f"threshold_runtime_env_{target_date}.json"
    verify = runtime_dir / f"threshold_runtime_env_verify_{target_date}.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": target_date,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": str(min_profit_pct)
                },
            }
        ),
        encoding="utf-8",
    )
    verify.write_text(
        json.dumps(
            {
                "target_date": target_date,
                "passed": True,
                "pid_passed": True,
                "status": "pass",
                "manifest_path": str(manifest),
            }
        ),
        encoding="utf-8",
    )


def test_current_min_profit_uses_same_day_runtime_feedback_observation(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [
            _row(
                1,
                "pyramid_correctly_blocked",
                max_profit_seen=1.5,
                final_profit_rate=1.2,
            )
        ],
        pyramid_min_profit_pct=1.1,
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["runtime_baseline_gate"] == "pass"
    assert candidate["current_values"]["min_profit_pct"] == 1.1
    assert (
        candidate["current_value_provenance"]["field_sources"]["min_profit_pct"]
        == "same_day_runtime_feedback_observation"
    )
    assert (
        candidate["source_metrics"]["profit_threshold_grid_decision"][
            "current_min_profit_pct"
        ]
        == 1.1
    )


def test_current_min_profit_falls_back_to_pid_verified_runtime_env(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    _write_verified_runtime_env(mod.RUNTIME_ENV_DIR, "2026-09-04", 1.1)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [_row(1, "pyramid_correctly_blocked")],
        pyramid_min_profit_pct=None,
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["runtime_baseline_gate"] == "pass"
    assert candidate["current_values"]["min_profit_pct"] == 1.1
    assert (
        candidate["current_value_provenance"]["field_sources"]["min_profit_pct"]
        == "verified_runtime_env_pid"
    )


def test_current_min_profit_conflict_fails_closed_runtime_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    _write_verified_runtime_env(mod.RUNTIME_ENV_DIR, "2026-09-04", 1.1)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [_row(index, "pyramid_would_have_helped") for index in range(20)],
        pyramid_min_profit_pct=1.5,
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold_runtime_baseline"
    assert candidate["runtime_baseline_gate"] == "blocked"
    assert (
        "feedback_runtime_env_min_profit_conflict"
        in candidate["runtime_baseline_blockers"]
    )
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []


def test_missing_current_min_profit_runtime_provenance_fails_closed(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [_row(index, "pyramid_would_have_helped") for index in range(20)],
        pyramid_min_profit_pct=None,
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold_runtime_baseline"
    assert candidate["runtime_baseline_gate"] == "blocked"
    assert candidate["allowed_runtime_apply"] is False


@pytest.mark.parametrize("verified_runtime_present", [False, True])
def test_static_feedback_fallback_is_not_observed_runtime(
    tmp_path, verified_runtime_present
):
    if verified_runtime_present:
        _write_verified_runtime_env(mod.RUNTIME_ENV_DIR, "2026-09-04", 1.1)
    resolution = mod._resolve_current_values(
        "2026-09-04",
        [
            {
                "target_date": "2026-09-04",
                "pyramid_threshold_provenance": {
                    "ambiguous": False,
                    "observed_min_profit_pct_values": [],
                    "selected_min_profit_pct": 1.5,
                    "selection_source": "static_fallback_no_unique_runtime_threshold",
                },
            }
        ],
    )
    if verified_runtime_present:
        assert resolution["status"] == "pass"
        assert resolution["values"]["min_profit_pct"] == 1.1
        assert (
            resolution["field_sources"]["min_profit_pct"] == "verified_runtime_env_pid"
        )
    else:
        assert resolution["status"] == "blocked"
        assert "current_min_profit_runtime_provenance_missing" in resolution["blockers"]


def test_pyramid_quality_calibration_holds_when_sample_floor_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [_row(i, "pyramid_overheat_or_reversal_risk") for i in range(3)],
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert (
        "pyramid_threshold_replay_contract_missing" in candidate["calibration_reason"]
    )


def test_pyramid_quality_calibration_excludes_blocked_source_date(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    allowed = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-02.json",
        [_row(1, "pyramid_correctly_blocked")],
    )
    blocked = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [_row(2, "pyramid_would_have_helped")],
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "pass" if source_date == "2026-07-02" else "fail",
            "tuning_input_allowed": source_date == "2026-07-02",
            "allowed_runtime_apply": source_date == "2026-07-02",
            "source_quality_gate": (
                "pass" if source_date == "2026-07-02" else "blocked_contract_gap"
            ),
            "blocked_reason": (
                None if source_date == "2026-07-02" else "blocked_contract_gap"
            ),
        },
    )

    report = mod.build_report(
        "2026-07-03", input_paths=[allowed, blocked], generated_at="fixed"
    )
    candidate = report["calibration_candidates"][0]

    assert candidate["sample_count"] == 1
    assert candidate["cumulative_quality_window"]["source_dates"] == ["2026-07-02"]
    assert (
        candidate["cumulative_quality_window"]["source_quality_excluded_date_count"]
        == 1
    )
    assert report["source_quality"]["input_paths"] == [str(allowed)]


def test_pyramid_quality_calibration_reversal_labels_cannot_change_quality_env(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_overheat_or_reversal_risk") for i in range(14)]
    rows.extend(_row(100 + i, "pyramid_correctly_blocked") for i in range(6))
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["recommended_values"] == candidate["current_values"]
    assert "SCALPING_PYRAMID_MAX_ADD_QTY_RATIO" not in candidate["target_env_keys"]


def test_pyramid_quality_calibration_recovery_labels_cannot_change_quality_env(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(14)]
    rows.extend(_row(100 + i, "pyramid_correctly_blocked") for i in range(6))
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["recommended_values"] == candidate["current_values"]
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True


def test_pyramid_quality_calibration_blocks_pressure_provenance_missing_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in rows:
        row.update(
            {
                "buy_pressure_10t": 55.0,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="pressure_provenance_missing",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert (
        "pyramid_threshold_replay_contract_missing" in candidate["calibration_reason"]
    )
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["source_quality_status"] == "blocked"
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "pressure_provenance_invalid": 20
    }


def test_pyramid_quality_calibration_blocks_pressure_provenance_unusable_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in rows:
        row.update(
            {
                "buy_pressure_10t": 55.0,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="pressure_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "pressure_provenance_invalid": 20
    }


def test_pyramid_quality_calibration_blocks_micro_vwap_provenance_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in rows:
        row.update(
            {
                "curr_vs_micro_vwap_bp": 12.0,
                "micro_vwap_available": False,
                "minute_candle_window_fresh": False,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="micro_vwap_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "micro_vwap_provenance_invalid": 20
    }


def test_pyramid_quality_calibration_keeps_valid_rows_from_mixed_quality_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    invalid_rows = [_row(100 + i, "pyramid_would_have_helped") for i in range(2)]
    for row in invalid_rows:
        row.update(
            {
                "curr_vs_micro_vwap_bp": 15.0,
                "micro_vwap_available": False,
                "minute_candle_window_fresh": False,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows + invalid_rows,
        source_quality="micro_vwap_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "pass_with_row_exclusions"
    assert candidate["sample_count"] == 20
    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["source_metrics"]["source_quality_excluded_row_count"] == 2
    assert report["runtime_update_contract"]["max_runtime_apply_count"] == 1
    assert (
        report["runtime_update_contract"]["quality_update_id"]
        == candidate["quality_update_id"]
    )


def test_different_anchor_normal_winner_ev_is_diagnostic_and_isolates_bad_receipt(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [
        _row(i, "pyramid_would_have_helped", max_profit_seen=2.0, final_profit_rate=2.0)
        for i in range(20)
    ]
    normal_rows = [
        {
            "record_id": f"normal-{index}",
            "normal_winner_expansion_label": "correctly_not_expanded_or_reversal",
            "normal_winner_expansion_source_quality_valid": True,
            "normal_winner_expansion_incremental_final_profit_pct": -0.3,
            "normal_winner_expansion_candidate_notional_krw": 100_000,
            "effective_venue": "KRX",
            "venue_source_quality_valid": True,
            "market_session_bucket": "krx_regular",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
            ),
            "forbidden_uses": ["intraday_runtime_apply"],
        }
        for index in range(20)
    ]
    invalid_receipt_row = {
        "record_id": "invalid-receipt",
        "scale_in_outcome_cohort": "normal_pyramid",
        "closed": True,
        "source_quality_valid": False,
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        source_quality="real_scale_in_receipt_source_quality_incomplete",
        one_share_rows=one_share_rows,
        normal_winner_expansion_rows=normal_rows,
        real_scale_in_performance_rows=[invalid_receipt_row],
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "pass_with_row_exclusions"
    assert candidate["calibration_state"] == "source_quality_blocked"
    assert (
        "pyramid_threshold_replay_contract_missing" in candidate["calibration_reason"]
    )
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert (
        candidate["source_metrics"]["normal_winner_expansion_loosen_veto_applied"]
        is False
    )
    assert candidate["source_metrics"]["source_quality_excluded_row_count"] == 1
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "real_scale_in_receipt_source_quality_incomplete": 1
    }


def test_pyramid_quality_calibration_uses_all_one_share_rows_for_thresholds(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    legacy_rows = [_row(i, "pyramid_overheat_or_reversal_risk") for i in range(20)]
    one_share_rows = [_row(1000 + i, "pyramid_would_have_helped") for i in range(14)]
    one_share_rows.extend(_row(2000 + i, "pyramid_correctly_blocked") for i in range(6))
    for index, row in enumerate(one_share_rows):
        row["max_profit_seen"] = 2.0
        row["final_profit_rate"] = 2.0
        row["stock_code"] = f"{index:06d}"
        row["one_share_event"] = True
        row["pyramid_opportunity_cost_pct"] = 0.5 + index / 10
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        legacy_rows,
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["sample_count"] == 20
    assert (
        candidate["source_metrics"]["calibration_source_scope"]
        == "timestamped_pyramid_gate_fixed_exit_replay"
    )
    assert candidate["source_metrics"]["one_share_event_source_present"] is True
    assert candidate["source_metrics"]["one_share_closed_pyramid_row_count"] == 20
    assert candidate["source_metrics"]["profit_threshold_grid"] == []
    assert len(candidate["source_metrics"]["legacy_peak_threshold_proxy_grid"]) > 0
    assert (
        candidate["recommended_values"]["min_ai_score"]
        == candidate["current_values"]["min_ai_score"]
    )


def test_pyramid_quality_calibration_excludes_invalid_probe_attribution_rows(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in one_share_rows:
        row.update(
            {
                "probe_residual_observation_seen": True,
                "residual_fill_attribution_valid": True,
                "venue_source_quality_valid": True,
            }
        )
    one_share_rows[0]["residual_fill_attribution_valid"] = False
    one_share_rows[1]["venue_source_quality_valid"] = False
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["sample_count"] == 18
    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["source_metrics"]["one_share_closed_pyramid_row_count"] == 18


def test_pyramid_quality_calibration_consumes_normal_winner_expansion_as_source_only(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    normal_rows = [
        {
            "record_id": str(index),
            "normal_winner_expansion_label": "realized_incremental_winner",
            "normal_winner_expansion_source_quality_valid": True,
            "normal_winner_expansion_incremental_final_profit_pct": 0.4,
            "normal_winner_expansion_candidate_notional_krw": 100_000,
            "effective_venue": "KRX",
            "venue_source_quality_valid": True,
            "market_session_bucket": "krx_regular",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
            ),
            "forbidden_uses": ["intraday_runtime_apply"],
        }
        for index in range(20)
    ]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        normal_winner_expansion_rows=normal_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    observation = report["normal_winner_expansion_observation"]

    assert observation["state"] == "positive_ev_profile_candidate"
    assert observation["sample_count"] == 20
    assert observation["ev_eligible_sample_count"] == 20
    assert observation["notional_weighted_ev_pct"] == 0.4
    assert observation["provenance_rejected_count"] == 0
    assert observation["by_effective_venue"][0]["effective_venue"] == "KRX"
    assert observation["by_effective_venue"][0]["ev_eligible_sample_count"] == 20
    assert observation["by_effective_venue"][0]["sample_floor_met"] is True
    assert observation["allowed_runtime_apply"] is False
    assert observation["runtime_effect"] is False
    assert (
        observation["decision_authority"]
        == "rolling_source_only_normal_winner_expansion_observation"
    )


def test_normal_winner_ev_floor_requires_positive_parseable_notional(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    normal_rows = [
        {
            "record_id": str(index),
            "normal_winner_expansion_label": "realized_incremental_winner",
            "normal_winner_expansion_source_quality_valid": True,
            "normal_winner_expansion_incremental_final_profit_pct": 0.4,
            "normal_winner_expansion_candidate_notional_krw": (
                "nan" if index == 0 else "malformed" if index == 1 else 100_000
            ),
            "effective_venue": "KRX",
            "venue_source_quality_valid": True,
            "market_session_bucket": "krx_regular",
            "normal_winner_expansion_blocker_reason": (
                mod.WINNER_RECOVERY_EXACT_BLOCKER if index < 10 else "other_blocker"
            ),
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
            ),
            "forbidden_uses": ["intraday_runtime_apply"],
        }
        for index in range(21)
    ]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        normal_winner_expansion_rows=normal_rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["normal_winner_expansion_observation"]
    exact = report["winner_recovery_bounded_canary_observation"]

    assert observation["sample_count"] == 21
    assert observation["ev_eligible_sample_count"] == 19
    assert observation["sample_floor_met"] is False
    assert observation["state"] == "hold_sample"
    assert exact["by_effective_venue"][0]["sample_count"] == 10
    assert exact["by_effective_venue"][0]["ev_eligible_sample_count"] == 8
    assert exact["by_effective_venue"][0]["sample_floor_met"] is False


def test_pyramid_quality_calibration_rejects_normal_winner_authority_leak(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    leaked_row = {
        "record_id": "leaked",
        "normal_winner_expansion_label": "realized_incremental_winner",
        "normal_winner_expansion_source_quality_valid": True,
        "normal_winner_expansion_incremental_final_profit_pct": 1.0,
        "normal_winner_expansion_candidate_notional_krw": 100_000,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "decision_authority": "live_runtime",
        "forbidden_uses": [],
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        normal_winner_expansion_rows=[leaked_row],
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    observation = report["normal_winner_expansion_observation"]

    assert observation["state"] == "hold_sample"
    assert observation["sample_count"] == 0
    assert observation["provenance_rejected_count"] == 1
    assert observation["allowed_runtime_apply"] is False


def test_winner_recovery_counterfactual_isolates_exact_blocker_by_venue(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    normal_rows = []
    for index in range(10):
        normal_rows.append(
            {
                "record_id": str(index),
                "normal_winner_expansion_label": "realized_incremental_winner",
                "normal_winner_expansion_source_quality_valid": True,
                "normal_winner_expansion_incremental_final_profit_pct": 0.5,
                "normal_winner_expansion_candidate_notional_krw": 100_000,
                "normal_winner_expansion_blocker_reason": (
                    mod.WINNER_RECOVERY_EXACT_BLOCKER
                ),
                "effective_venue": "KRX",
                "venue_source_quality_valid": True,
                "market_session_bucket": "krx_regular",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": (
                    "source_only_one_share_pyramid_opportunity_backtest_"
                    "no_runtime_mutation"
                ),
                "forbidden_uses": ["intraday_runtime_apply"],
            }
        )
    normal_rows.append(
        {
            **normal_rows[0],
            "record_id": "mixed-negative",
            "normal_winner_expansion_blocker_reason": (
                "rising_missed_scout_pyramid_bridge_blocked:"
                "buy_pressure_severe_below_min"
            ),
            "normal_winner_expansion_label": ("correctly_not_expanded_or_reversal"),
            "normal_winner_expansion_incremental_final_profit_pct": -5.0,
        }
    )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        normal_winner_expansion_rows=normal_rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_bounded_canary_observation"]

    assert observation["state"] == "bounded_one_share_canary_evidence_ready"
    assert observation["sample_count"] == 10
    assert observation["ready_venue_count"] == 1
    assert observation["operator_action_required"] is False
    assert observation["next_preopen_auto_apply_candidate"] is True
    assert observation["auto_apply_mode"] == "next_preopen_auto_bounded_live"
    assert observation["allowed_runtime_apply"] is False
    assert observation["initial_real_qty_cap"] == 1
    assert observation["by_effective_venue"] == [
        {
            "effective_venue": "KRX",
            "state": "bounded_one_share_canary_evidence_ready",
            "sample_count": 10,
            "ev_eligible_sample_count": 10,
            "sample_floor": 10,
            "sample_floor_met": True,
            "realized_incremental_winner_count": 10,
            "notional_weighted_ev_pct": 0.5,
            "initial_real_qty_cap": 1,
            "runtime_env_key": (
                "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_KRX_ENABLED"
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    ]
    assert len(report["normal_winner_expansion_observation"]["by_blocker_reason"]) == 2


def test_winner_recovery_candidate_is_blocked_by_unisolatable_report_quality(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    row = {
        "normal_winner_expansion_label": "realized_incremental_winner",
        "normal_winner_expansion_source_quality_valid": True,
        "normal_winner_expansion_incremental_final_profit_pct": 0.5,
        "normal_winner_expansion_candidate_notional_krw": 100_000,
        "normal_winner_expansion_blocker_reason": mod.WINNER_RECOVERY_EXACT_BLOCKER,
        "effective_venue": "KRX",
        "venue_source_quality_valid": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_valid",
        "forbidden_uses": ["runtime_apply"],
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        source_quality="unisolatable_contract_failure",
        normal_winner_expansion_rows=[{**row, "record_id": str(i)} for i in range(10)],
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_bounded_canary_observation"]

    assert observation["state"] == "source_quality_blocked"
    assert observation["evidence_state_before_source_quality_gate"] == (
        "bounded_one_share_canary_evidence_ready"
    )
    assert observation["operator_action_required"] is False
    assert observation["allowed_runtime_apply"] is False


def test_winner_recovery_real_execution_requires_positive_fee_aware_ev_and_floor(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [
        {
            "record_id": str(index),
            "scale_in_outcome_cohort": "winner_recovery",
            "closed": True,
            "fill_qty": 1,
            "fill_notional_krw": 100_000,
            "scale_in_leg_net_pnl_proxy_krw": 400,
            "source_quality_valid": True,
            "entry_effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": ("real_scale_in_execution_outcome_observation_only"),
            "forbidden_uses": ["runtime_threshold_apply"],
        }
        for index in range(20)
    ]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        real_scale_in_performance_rows=rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_real_execution_observation"]

    assert observation["state"] == "first_planned_residual_leg_candidate_ready"
    assert observation["source_quality_valid_closed_count"] == 20
    assert observation["source_quality_adjusted_ev_pct"] == 0.4
    assert observation["scale_in_leg_net_pnl_proxy_krw_sum"] == 8000
    assert observation["diagnostic_win_rate"] == 1.0
    assert observation["recommended_next_qty_stage"] == (
        "first_planned_residual_leg_from_current_position_sizing_owner"
    )
    assert observation["operator_action_required"] is True
    assert observation["allowed_runtime_apply"] is False


def test_winner_recovery_real_execution_holds_below_floor_and_rejects_bad_source(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    valid = {
        "scale_in_outcome_cohort": "winner_recovery",
        "closed": True,
        "fill_qty": 1,
        "fill_notional_krw": 100_000,
        "scale_in_leg_net_pnl_proxy_krw": 300,
        "source_quality_valid": True,
        "entry_effective_venue": "NXT",
        "market_session_bucket": "nxt_regular",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "real_scale_in_execution_outcome_observation_only",
        "forbidden_uses": ["runtime_threshold_apply"],
    }
    rows = [{**valid, "record_id": str(index)} for index in range(19)]
    rows.append({**valid, "record_id": "bad-source", "source_quality_valid": False})
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        real_scale_in_performance_rows=rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_real_execution_observation"]

    assert observation["state"] == "observe_one_share_canary"
    assert observation["execution_count"] == 20
    assert observation["closed_count"] == 20
    assert observation["source_quality_valid_closed_count"] == 19
    assert observation["source_quality_rejected_count"] == 1
    assert observation["operator_action_required"] is False
    assert observation["allowed_runtime_apply"] is False


def test_pyramid_quality_calibration_consumes_post_probe_real_outcomes_source_only(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    post_probe_rows = []
    for index in range(20):
        winner = index < 12
        profit_pct = 0.4 if winner else -0.2
        post_probe_rows.append(
            {
                **_row(
                    index,
                    "pyramid_correctly_blocked",
                    final_profit_rate=profit_pct,
                ),
                "post_probe_real_outcome_label": (
                    "profitable_zero_fill_confirmation_ready"
                    if winner
                    else "loss_or_flat_zero_fill_confirmation_ready"
                ),
                "post_probe_real_outcome_source_quality_valid": True,
                "post_probe_real_outcome_profit_pct": profit_pct,
                "post_probe_real_confirmation_ready": True,
                "post_probe_counterfactual_source_quality_valid": True,
                "post_probe_probe_actual_order_submitted": True,
                "post_probe_residual_actual_order_submitted": False,
                "post_probe_counterfactual_first_leg_notional_krw": 100_000,
                "post_probe_reprice_observed": True,
                "post_probe_reprice_outcome_source_quality_valid": True,
                "post_probe_reprice_profiles": ["normal"],
                "post_probe_reprice_avg_passive_improvement_bps": 30.0,
                "effective_venue": "NXT",
                "venue_source_quality_valid": True,
                "market_session_bucket": "nxt",
                "allowed_runtime_apply": False,
                "decision_authority": (
                    "source_only_one_share_pyramid_opportunity_backtest_"
                    "no_runtime_mutation"
                ),
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-29.json",
        [],
        one_share_rows=post_probe_rows,
        post_probe_real_outcome_contract=True,
    )

    report = mod.build_report("2026-07-29", input_paths=[path], generated_at="fixed")
    observation = report["post_probe_real_outcome_observation"]

    assert observation["state"] == "positive_ev_profile_candidate"
    assert observation["closed_real_outcome_count"] == 20
    assert observation["confirmation_ready_count"] == 20
    assert observation["confirmation_ready_winner_count"] == 12
    assert observation["confirmation_ready_loss_or_flat_count"] == 8
    assert observation["diagnostic_win_rate"] == 0.6
    assert observation["notional_weighted_ev_pct"] == 0.16
    assert observation["sample_floor_met"] is True
    assert observation["cumulative_judgment_quality"] == {
        "learning_sample_floor": 1,
        "learning_sample_count": 20,
        "learning_updated": True,
        "learning_update_policy": (
            "one_mature_post_probe_outcome_updates_cumulative_judgment_quality"
        ),
        "notional_weighted_ev_pct": 0.16,
        "runtime_promotion_sample_floor": 20,
        "learning_floor_grants_runtime_promotion": False,
    }
    assert observation["by_effective_venue"][0]["effective_venue"] == "NXT"
    reprice = report["post_probe_reprice_observation"]
    assert reprice["learning_updated"] is True
    assert reprice["learning_sample_count"] == 20
    assert reprice["equal_weight_avg_profit_pct"] == 0.16
    assert reprice["profile_quality"][0] == {
        "reprice_profile": "normal",
        "sample_count": 20,
        "equal_weight_avg_profit_pct": 0.16,
        "avg_passive_improvement_bps": 30.0,
    }
    assert reprice["metric_role"] == "execution_quality_real_only"
    assert reprice["window_policy"] == (
        "clean_baseline_cumulative_closed_real_post_probe_reprice_outcomes"
    )
    assert reprice["sample_floor"] == {
        "cumulative_learning": 1,
        "runtime_promotion_real": 20,
    }
    assert reprice["primary_decision_metric"] == "equal_weight_avg_profit_pct"
    assert "complete_post_probe_resolver" in reprice["source_quality_gate"]
    assert observation["runtime_effect"] is False
    assert observation["allowed_runtime_apply"] is False
    assert (
        observation["decision_authority"]
        == "rolling_source_only_post_probe_real_outcome_no_runtime_mutation"
    )
    output_json = tmp_path / "post_probe_calibration.json"
    output_md = tmp_path / "post_probe_calibration.md"
    mod.write_outputs(report, output_json=output_json, output_md=output_md)
    markdown = output_md.read_text(encoding="utf-8")
    assert "- post_probe_confirmation_ready_winner_count: 12" in markdown
    assert (
        "- post_probe_confirmation_ready_notional_weighted_ev_pct: 0.1600" in markdown
    )


def test_runtime_confirmation_quality_dispute_is_observed_but_excluded_from_ev(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    disputed = {
        **_row(1, "pyramid_correctly_blocked", final_profit_rate=0.38),
        "post_probe_real_outcome_label": "profitable_zero_fill_no_confirmation",
        "post_probe_real_outcome_source_quality_valid": True,
        "post_probe_real_outcome_profit_pct": 0.38,
        "post_probe_real_confirmation_ready": False,
        "post_probe_runtime_confirmation_ready": True,
        "post_probe_confirmation_contract_alignment": (
            "runtime_confirmed_source_quality_disputed"
        ),
        "post_probe_counterfactual_source_quality_valid": True,
        "post_probe_probe_actual_order_submitted": True,
        "post_probe_residual_actual_order_submitted": False,
        "post_probe_counterfactual_first_leg_notional_krw": 146_600,
        "effective_venue": "KRX",
        "venue_source_quality_valid": True,
        "market_session_bucket": "krx_regular",
        "allowed_runtime_apply": False,
        "decision_authority": (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        ),
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-31.json",
        [],
        one_share_rows=[disputed],
        post_probe_real_outcome_contract=True,
    )

    report = mod.build_report("2026-07-31", input_paths=[path], generated_at="fixed")
    observation = report["post_probe_real_outcome_observation"]

    assert observation["closed_real_outcome_count"] == 1
    assert observation["confirmation_ready_count"] == 0
    assert observation["runtime_confirmation_source_quality_disputed_count"] == 1
    assert observation["cumulative_judgment_quality"]["learning_sample_count"] == 0
    assert observation["notional_weighted_ev_pct"] == 0.0


def test_pyramid_quality_calibration_profit_grid_sets_one_step_min_profit(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [
        _row(i, "pyramid_would_have_helped", max_profit_seen=1.4, final_profit_rate=2.0)
        for i in range(24)
    ]
    one_share_rows.extend(
        _row(
            100 + i,
            "pyramid_overheat_or_reversal_risk",
            max_profit_seen=2.0,
            final_profit_rate=0.2,
        )
        for i in range(6)
    )
    for row in one_share_rows:
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        one_share_rows=one_share_rows,
        threshold_replay_rows=[
            _replay_row(
                5000 + index,
                profit_rate=1.4,
                configured_min_profit_pct=1.5,
            )
            for index in range(24)
        ],
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]
    grid_decision = candidate["source_metrics"]["profit_threshold_grid_decision"]
    grid = candidate["source_metrics"]["profit_threshold_grid"]

    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["calibration_reason"] == "grid_loosen_profit_threshold_one_step"
    assert (
        candidate["recommended_values"]["min_profit_pct"]
        == grid_decision["selected_min_profit_pct"]
    )
    assert grid_decision["exploratory_selected_min_profit_pct"] == 1.4
    assert grid_decision["selected_min_profit_pct"] == 1.4
    assert (
        grid_decision["selected_min_profit_pct"]
        < candidate["current_values"]["min_profit_pct"]
    )
    assert grid_decision["selected_row"]["eligible_count"] >= 20
    assert grid_decision["objective"] == (
        "maximize_fee_aware_expected_net_profit_contribution"
    )
    assert (
        grid_decision["selected_equal_weight_expected_net_profit_contribution_pct"]
        > grid_decision["current_equal_weight_expected_net_profit_contribution_pct"]
    )
    assert grid[0]["min_profit_pct"] == 0.2
    assert grid[0]["trade_cost_pct"] == 0.23
    assert grid[0]["cost_application"] == (
        "calculate_net_profit_rate_once_on_sell_notional"
    )
    assert "equal_weight_expected_net_profit_contribution_pct" in grid[0]


def test_threshold_replay_blocks_episode_when_observed_gate_does_not_match():
    row = _replay_row(
        7001,
        profit_rate=1.2,
        configured_min_profit_pct=1.1,
        observed_gate_selected=False,
    )

    result = mod._threshold_replay_episode_result([row], 1.0)

    assert result["status"] == "source_quality_blocked"
    assert result["source_quality_reasons"] == ["observed_gate_replay_mismatch"]


def test_threshold_replay_recomputes_strong_min_when_base_threshold_is_lowered():
    row = _replay_row(
        7002,
        profit_rate=0.85,
        configured_min_profit_pct=1.1,
        observed_gate_selected=False,
    )
    row["strong_continuation_allowed"] = True

    result = mod._threshold_replay_episode_result([row], 0.8)

    assert result["status"] == "evaluated"
    assert result["selected"] is True


def test_threshold_replay_rows_fail_closed_on_prior_or_owner_authority():
    row = _replay_row(7003)
    row["runtime_prior_action_applied"] = True
    report = {
        "schema_version": 5,
        "target_date": "2026-09-04",
        "pyramid_threshold_replay_metric_contract": {
            "contract_version": "pyramid_gate_replay_source_v1",
            "metric_role": "bounded_tunable_threshold_gate_counterfactual",
            "decision_authority": (
                "source_only_fixed_observed_exit_pyramid_gate_replay"
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
        },
        "pyramid_threshold_replay_rows": [row],
    }

    normalized = mod._threshold_replay_rows([report])[0]

    assert normalized["gate_replay_source_quality_valid"] is False
    assert "runtime_prior_action_applied" in normalized["source_quality_reasons"]


def test_threshold_replay_rows_reject_forged_resolver_price_evidence():
    row = _replay_row(7004)
    row["pyramid_price_resolver_order_price"] = 10010
    report = {
        "schema_version": 5,
        "target_date": "2026-09-04",
        "pyramid_threshold_replay_metric_contract": {
            "contract_version": "pyramid_gate_replay_source_v1",
            "metric_role": "bounded_tunable_threshold_gate_counterfactual",
            "decision_authority": (
                "source_only_fixed_observed_exit_pyramid_gate_replay"
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
        },
        "pyramid_threshold_replay_rows": [row],
    }

    normalized = mod._threshold_replay_rows([report])[0]

    assert normalized["gate_replay_source_quality_valid"] is False
    assert (
        "threshold_replay_resolver_price_mismatch"
        in normalized["source_quality_reasons"]
    )


def test_threshold_replay_grid_uses_same_complete_episode_set_for_every_threshold():
    complete = _replay_row(7101, profit_rate=1.0)
    missing_low_threshold_price = _replay_row(7102, profit_rate=1.0)
    complete["source_target_date"] = "2026-09-04"
    missing_low_threshold_price["source_target_date"] = "2026-09-04"
    missing_low_threshold_price.update(
        {
            "replay_entry_price": None,
            "fixed_exit_economic_replay_ready": False,
            "source_quality_reasons": ["fresh_executable_bbo_missing"],
        }
    )

    grid = mod._pyramid_threshold_replay_grid(
        [complete, missing_low_threshold_price], 1.1
    )

    assert {row["comparable_episode_count"] for row in grid} == {1}
    assert {row["source_quality_excluded_episode_count"] for row in grid} == {1}
    assert {row["comparison_alignment"] for row in grid} == {
        "same_complete_episode_set_all_thresholds"
    }


def test_nxt_only_replay_cannot_change_common_pyramid_runtime_axis(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    replay_rows = [_replay_row(7200 + index) for index in range(20)]
    for row in replay_rows:
        row["effective_venue"] = "NXT"
        row["market_session_bucket"] = "nxt_entry_window"
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [],
        pyramid_min_profit_pct=1.1,
        threshold_replay_rows=replay_rows,
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold_runtime_scope"
    assert candidate["runtime_scope_blockers"] == [
        "common_runtime_axis_krx_evidence_missing"
    ]
    assert candidate["condition_feasibility"]["state"] == (
        "runtime_scope_not_supported"
    )
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []


def test_profit_grid_holds_when_better_next_step_is_still_net_negative():
    rows = [
        {
            "max_profit_seen": 1.2,
            "final_profit_rate": 0.9,
            "pyramid_feedback_label": "pyramid_overheat_or_reversal_risk",
        }
        for _ in range(20)
    ]

    decision = mod._profit_grid_decision(
        {"min_profit_pct": 1.1}, mod._profit_threshold_grid(rows)
    )

    assert decision["status"] == "hold"
    assert decision["reason"] == "grid_next_step_net_contribution_non_positive"
    assert decision["selected_min_profit_pct"] == 1.1
    assert decision["recommended_next_min_profit_pct"] == 1.1
    assert decision["candidate_next_min_profit_pct"] == 1.0
    assert (
        decision["candidate_next_equal_weight_expected_net_profit_contribution_pct"]
        > decision["current_equal_weight_expected_net_profit_contribution_pct"]
    )
    assert (
        decision["candidate_next_equal_weight_expected_net_profit_contribution_pct"]
        < 0.0
    )
    assert decision["selected_row"] == decision["current_row"]


def test_calibration_reason_exposes_net_negative_grid_hold(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [
        _row(
            i,
            (
                "pyramid_would_have_helped"
                if i % 2
                else "pyramid_overheat_or_reversal_risk"
            ),
            max_profit_seen=1.2,
            final_profit_rate=0.9,
        )
        for i in range(20)
    ]
    for row in one_share_rows:
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [],
        one_share_rows=one_share_rows,
        pyramid_min_profit_pct=1.1,
        threshold_replay_rows=[
            _replay_row(
                6000 + index,
                profit_rate=1.0,
                entry_price=10000,
                sell_price=10010,
            )
            for index in range(20)
        ],
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold"
    assert candidate["calibration_reason"] == (
        "grid_next_step_net_contribution_not_improved"
    )
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["recommended_values"]["min_profit_pct"] == 1.1


def test_profit_grid_holds_when_current_threshold_is_outside_grid():
    rows = [
        {
            "max_profit_seen": 1.0,
            "final_profit_rate": 1.5,
            "pyramid_feedback_label": "pyramid_would_have_helped",
        }
        for _ in range(20)
    ]

    decision = mod._profit_grid_decision(
        {"min_profit_pct": 3.0}, mod._profit_threshold_grid(rows)
    )

    assert decision["status"] == "hold"
    assert decision["reason"] == "current_threshold_outside_profit_grid"
    assert decision["selected_min_profit_pct"] == 3.0
    assert decision["candidate_next_min_profit_pct"] is None


@pytest.mark.parametrize("bad_profit", [None, "malformed", "NaN", "inf", -101])
def test_profit_grid_excludes_invalid_terminal_returns(bad_profit):
    rows = [{"max_profit_seen": 2.0, "final_profit_rate": bad_profit}]
    assert mod._profit_threshold_grid(rows) == []


def _feasibility_grid(values):
    return [
        {
            "min_profit_pct": threshold,
            "eligible_count": count,
            "equal_weight_expected_net_profit_contribution_pct": net,
        }
        for threshold, count, net in values
    ]


@pytest.mark.parametrize(
    "values,expected_state",
    [
        ([(0.9, 30, -0.1), (1.0, 25, -0.2), (1.1, 20, -0.3)], "no_economic_candidate"),
        (
            [(0.9, 30, 0.1), (1.0, 25, -0.2), (1.1, 20, -0.3)],
            "positive_candidate_unreachable_in_one_step",
        ),
        ([(0.9, 30, 0.2), (1.0, 25, 0.1), (1.1, 20, -0.3)], "bounded_candidate_ready"),
    ],
)
def test_feasibility_distinguishes_no_edge_unreachable_path_and_ready(
    values, expected_state
):
    decision = mod._profit_grid_decision(
        {"min_profit_pct": 1.1}, _feasibility_grid(values)
    )
    feasibility = mod._condition_feasibility(
        decision, source_blockers=[], runtime_baseline_blockers=[]
    )
    assert feasibility["state"] == expected_state
    assert feasibility["allowed_runtime_apply"] is False
    assert feasibility["future_success_probability"] is None
    if expected_state != "bounded_candidate_ready":
        assert feasibility["indefinite_wait_appropriate"] is False
        assert decision["selected_min_profit_pct"] == 1.1


def test_next_step_needs_own_eligible_sample_floor():
    decision = mod._profit_grid_decision(
        {"min_profit_pct": 1.1},
        _feasibility_grid([(0.9, 30, 0.2), (1.0, 5, 0.1), (1.1, 0, 0)]),
    )
    assert decision["status"] == "hold"
    assert decision["reason"] == "grid_next_step_eligible_rows_lt_20"


def test_positive_candidate_changes_only_profit_threshold(tmp_path):
    path = _feedback(
        tmp_path / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [
            _row(
                i,
                "pyramid_overheat_or_reversal_risk",
                max_profit_seen=2.0,
                final_profit_rate=2.0,
            )
            for i in range(20)
        ],
        pyramid_min_profit_pct=1.1,
        threshold_replay_rows=[_replay_row(7000 + index) for index in range(20)],
    )
    candidate = mod.build_report("2026-09-04", input_paths=[path])[
        "calibration_candidates"
    ][0]
    changed = {
        key
        for key, value in candidate["recommended_values"].items()
        if value != candidate["current_values"][key]
    }
    assert changed == {"min_profit_pct"}
    assert candidate["recommended_values"]["min_profit_pct"] == 1.0
    assert candidate["target_env_keys"] == ["SCALPING_PYRAMID_MIN_PROFIT_PCT"]
    assert candidate["condition_feasibility"]["state"] == "bounded_candidate_ready"
    assert candidate["source_sample_count"] == 20
    assert candidate["decision_sample_count"] == 20


def test_pyramid_quality_calibration_does_not_fallback_when_one_share_floor_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    legacy_rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    one_share_rows = [_row(3000 + i, "pyramid_would_have_helped") for i in range(5)]
    for row in one_share_rows:
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        legacy_rows,
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["sample_count"] == 5
    assert (
        "pyramid_threshold_replay_contract_missing" in candidate["calibration_reason"]
    )


def test_quality_calibration_rolls_up_winner_recovery_runtime_funnel(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    funnel = {
        "runtime_gate_evaluation_count": 10,
        "runtime_gate_selected_count": 2,
        "runtime_gate_blocked_count": 8,
        "runtime_gate_block_reason_counts": [
            {"reason": "recovery_confirmation_not_ready", "count": 7},
            {"reason": "existing_pyramid_guard:micro_vwap_overheat", "count": 1},
        ],
        "selected_downstream_guard_blocked_count": 1,
        "selected_order_submitted_count": 0,
        "selected_executed_count": 0,
        "selected_open_or_unresolved_count": 0,
        "selected_closed_without_submit_count": 1,
        "invalid_timestamp_event_count": 0,
        "source_quality_status": "pass",
        "downstream_guard_block_reason_counts": [
            {"reason": "real_pyramid_ai_score_no_submit_authority", "count": 1}
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": (
            "source_only_winner_recovery_runtime_funnel_attribution"
        ),
        "forbidden_uses": ["intraday_runtime_apply"],
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-09-04.json",
        [_row(1, "pyramid_correctly_blocked")],
        pyramid_min_profit_pct=1.1,
        winner_recovery_runtime_funnel=funnel,
    )

    report = mod.build_report("2026-09-04", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_runtime_funnel_observation"]

    assert observation["state"] == "selected_downstream_guard_blocked"
    assert observation["runtime_gate_evaluation_count"] == 10
    assert observation["runtime_gate_selected_count"] == 2
    assert observation["selected_downstream_guard_blocked_count"] == 1
    assert observation["selected_closed_without_submit_count"] == 1
    assert observation["selected_order_submitted_count"] == 0
    assert observation["dominant_non_execution_layer"] == (
        "winner_recovery_runtime_gate"
    )
    assert observation["downstream_guard_block_reason_counts"] == [
        {"reason": "real_pyramid_ai_score_no_submit_authority", "count": 1}
    ]
    assert observation["runtime_effect"] is False
