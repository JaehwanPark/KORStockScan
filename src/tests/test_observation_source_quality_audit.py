import gzip
import fcntl
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.engine import observation_source_quality_audit as audit
from src.engine.scalping.smoothing_source_only_path_journal import (
    arm_source_only_path,
    observe_source_only_paths,
)


def test_main_fails_closed_when_heavy_analysis_lock_is_busy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lock_path = tmp_path / "intraday_heavy_analysis.lock"
    monkeypatch.setenv("KORSTOCKSCAN_INTRADAY_HEAVY_ANALYSIS_LOCK_FILE", str(lock_path))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "observation_source_quality_audit",
            "--target-date",
            "2026-07-31",
            "--write",
        ],
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_fp:
        fcntl.flock(lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        exit_code = audit.main()

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 75
    assert payload["status"] == "skipped_heavy_analysis_busy"
    assert payload["runtime_effect"] is False


def test_iter_events_deduplicates_repeated_json_strings_without_changing_values(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pipeline_events_2026-07-27.jsonl"
    repeated_fields = {
        "decision_authority": "source_quality_only",
        "venue_resolution": {
            "effective_venue": "KRX",
            "source": "realtime_provenance",
        },
    }
    rows = [
        {
            "event_type": "pipeline_event",
            "stage": "stage_a",
            "fields": repeated_fields,
        },
        {
            "event_type": "pipeline_event",
            "stage": "stage_b",
            "fields": repeated_fields,
        },
    ]
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    loaded = audit._iter_events(path)

    assert loaded == rows
    assert (
        loaded[0]["fields"]["decision_authority"]
        is loaded[1]["fields"]["decision_authority"]
    )
    assert next(iter(loaded[0]["fields"])) is next(iter(loaded[1]["fields"]))
    assert (
        loaded[0]["fields"]["venue_resolution"]["source"]
        is loaded[1]["fields"]["venue_resolution"]["source"]
    )


def test_build_audit_streams_source_without_materializing_event_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True)
    path = pipeline_dir / "pipeline_events_2026-07-31.jsonl"
    rows = [
        {
            "event_type": "pipeline_event",
            "stage": "streaming_memory_regression_stage",
            "emitted_at": f"2026-07-31T20:00:{index:02d}",
            "fields": {
                "source_quality_gate": "diagnostic_only",
                "opaque_payload": "x" * 10_000,
            },
        }
        for index in range(50)
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        audit,
        "_iter_events",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("materialized event list must not be used")
        ),
    )

    report = audit.build_observation_source_quality_audit("2026-07-31")

    assert report["summary"]["event_count"] == 50
    assert report["source"]["read_mode"] == "streaming_contract_aggregate"
    assert report["source"]["full_source_materialized"] is False


def _event(stage: str, fields: dict, *, record_id: int = 1) -> dict:
    return {
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_name": "TEST",
        "stock_code": "123456",
        "record_id": record_id,
        "fields": fields,
        "emitted_at": "2026-05-15T10:00:00",
        "emitted_date": "2026-05-15",
    }


def _write_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{target_date}.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_events_gzip(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(
        event_dir / f"pipeline_events_{target_date}.jsonl.gz",
        "wt",
        encoding="utf-8",
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_market_halt_window_artifact_is_not_gitignored():
    path = Path("data/source_quality/market_halt_windows/windows/2026-06-08.json")
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
    )

    assert result.returncode == 1


def test_nxt_post_block_sampler_stages_have_source_quality_contracts():
    stages = {
        "rising_missed_nxt_post_block_sampler_registered",
        "rising_missed_nxt_post_block_sampler_registration_skipped",
        "rising_missed_nxt_post_block_price_sample",
        "rising_missed_nxt_post_block_price_sampler_completed",
    }

    assert stages.issubset(audit.STAGE_CONTRACTS)
    assert all(
        audit.STAGE_CONTRACTS[stage].decision_authority
        == "source_only_nxt_post_block_price_observation"
        for stage in stages
    )


def test_low_profit_stagnation_confirmation_has_source_quality_contract():
    contract = audit.STAGE_CONTRACTS["low_profit_stagnation_confirmation"]

    assert (
        contract.decision_authority
        == "profit_stagnation_exit_runtime_confirmation_only"
    )
    assert {
        "runtime_effect",
        "allowed_runtime_apply",
        "actual_order_submitted",
        "broker_order_forbidden",
        "confirmation_sec",
        "anchor_profit",
        "anchor_peak",
    }.issubset(contract.required_fields)


def test_opening_rotation_price_conflict_has_fail_closed_source_quality_contract():
    contract = audit.STAGE_CONTRACTS["opening_rotation_1pct_source_quality_blocked"]

    assert (
        contract.decision_authority == "operator_requested_real_opening_rotation_1pct"
    )
    assert {
        "scanner_promotion_price_consistency_state",
        "scanner_promotion_price_consistency_reason",
        "scanner_promotion_price_conflict",
        "scanner_promotion_price",
        "scanner_promotion_price_source",
        "scanner_promotion_price_lineage_id",
        "scanner_promotion_price_initial_validation_reused",
        "scanner_promotion_price_boot_restore",
        "scanner_promotion_price_ws_curr",
        "scanner_promotion_price_gap_pct",
        "scanner_promotion_price_gap_max_pct",
        "scanner_promotion_price_ws_fresh",
        "allowed_runtime_apply",
        "actual_order_submitted",
        "broker_order_forbidden",
    }.issubset(contract.required_fields)


def test_low_profit_stagnation_confirmation_contract_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "low_profit_stagnation_confirmation",
                {
                    "metric_role": "bounded_tunable_exit_confirmation",
                    "decision_authority": "profit_stagnation_exit_runtime_confirmation_only",
                    "window_policy": "same_position_runtime_state",
                    "sample_floor": "existing_preopen_selected_stagnation_thresholds",
                    "primary_decision_metric": "confirmed_low_profit_stagnation_duration_sec",
                    "source_quality_gate": "holding_quote_freshness_and_profit_peak_state",
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "hard_stop_bypass",
                    "reason": "confirmation_started",
                    "profit_rate": "+0.38",
                    "peak_profit": "+0.40",
                    "adjusted_profit_pct": "+0.23",
                    "elapsed_sec": 0,
                    "confirmation_sec": 180,
                    "anchor_profit": 0.38,
                    "anchor_peak": 0.40,
                    "max_profit_move": 0.15,
                    "max_peak_improve": 0.10,
                    "quote_stale": False,
                    "quote_age_ms": 2288,
                    "quote_age_source": "last_ws_update_ts",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert (
        report["stage_contracts"]["low_profit_stagnation_confirmation"]["status"]
        == "pass"
    )


def test_scalp_trailing_continuation_recheck_contract_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-15",
        [
            _event(
                "scalp_trailing_continuation_recheck",
                {
                    "metric_role": "bounded_tunable",
                    "decision_authority": "operator_runtime_override_scalp_trailing_continuation_recheck",
                    "window_policy": "same_trailing_candidate_bounded_recheck",
                    "sample_floor": "positive_profit_with_fresh_trusted_ws_composite_micro",
                    "primary_decision_metric": "post_recheck_mfe_before_trailing_exit",
                    "source_quality_gate": "fresh_trusted_ws_and_composite_micro_support",
                    "runtime_effect": True,
                    "allowed_runtime_apply": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "hard_stop_bypass",
                    "threshold_family": "scalp_trailing_continuation_recheck",
                    "recheck_state": "armed",
                    "recheck_enabled": True,
                    "recheck_active": True,
                    "recheck_ttl_sec": "15.000",
                    "profit_rate": "+0.13",
                    "peak_profit": "+0.83",
                    "trailing_peak_worsen": "0.70",
                    "current_ai_score": "71",
                    "reversal_feature_context_usable": True,
                    "large_sell_print_detected": False,
                    "micro_source_state": "fresh_ws_order_flow_delta",
                    "micro_source_trusted_ws": True,
                    "composite_micro_supported": True,
                    "recheck_contract_version": "bounded_one_shot_attribution_v2",
                    "recheck_id": "scr-test",
                    "recheck_position_key": "record:123",
                    "counterfactual_profit_rate": "+0.1300",
                    "counterfactual_executable_sell_price": 10000,
                    "recheck_min_profit_rate": "+0.1300",
                    "recheck_max_profit_rate": "+0.1300",
                    "recheck_profit_delta_pct": "+0.0000",
                    "recheck_deadline_lag_sec": "0.000",
                    "second_extension_forbidden": True,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    assert (
        report["stage_contracts"]["scalp_trailing_continuation_recheck"]["status"]
        == "pass"
    )


def test_fast_exit_quote_envelope_stages_have_source_quality_contracts():
    stages = {
        "scalp_fast_exit_quote_envelope_blocked",
        "scalp_fast_exit_quote_envelope_trigger_cleared",
    }

    assert stages.issubset(audit.STAGE_CONTRACTS)
    assert all(
        audit.STAGE_CONTRACTS[stage].decision_authority
        == "real_scalping_fast_exit_guard"
        for stage in stages
    )
    assert all(
        "exit_quote_envelope_id" in audit.STAGE_CONTRACTS[stage].required_fields
        for stage in stages
    )


def test_protect_trailing_smooth_hold_contract_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-15",
        [
            _event(
                "protect_trailing_smooth_hold",
                {
                    "metric_role": "runtime_exit_confirmation_guard_attribution",
                    "decision_authority": "real_scalping_protect_trailing_confirmation_guard",
                    "window_policy": "same_position_recent_price_samples_with_emergency_bypass",
                    "sample_floor": "configured_protect_trailing_min_samples_and_span",
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "protect_trailing_smooth_hold_contract_fields_present",
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "standalone_order_submit/runtime_threshold_apply/provider_route_change/bot_restart/hard_stop_bypass/emergency_stop_bypass",
                    "threshold_family": "protect_trailing_smoothing",
                    "exit_rule_candidate": "protect_trailing_stop",
                    "curr_price": 10000,
                    "trailing_stop_price": "9950",
                    "buffered_stop_price": "9940",
                    "median_price": "9960",
                    "sample_count": 4,
                    "sample_span_sec": 6,
                    "below_ratio": "0.50",
                    "min_below_ratio": "0.80",
                    "window_sec": 10,
                    "min_span_sec": 5,
                    "min_samples": 3,
                    "buffer_pct": "0.10",
                    "profit_rate": "+0.42",
                    "peak_profit": "+0.88",
                    "emergency_pct": "-3.00",
                },
            ),
            _event(
                "protect_trailing_smooth_confirmed",
                {
                    "metric_role": "runtime_exit_confirmation_guard_attribution",
                    "decision_authority": "real_scalping_protect_trailing_confirmation_guard",
                    "window_policy": "same_position_recent_price_samples_with_emergency_bypass",
                    "sample_floor": "configured_protect_trailing_min_samples_and_span",
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "protect_trailing_smooth_confirmed_contract_fields_present",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "standalone_order_submit/runtime_threshold_apply/provider_route_change/bot_restart/hard_stop_bypass/emergency_stop_bypass",
                    "threshold_family": "protect_trailing_smoothing",
                    "exit_rule_candidate": "protect_trailing_stop",
                    "curr_price": 9900,
                    "trailing_stop_price": "9950",
                    "buffered_stop_price": "9850",
                    "median_price": "9840",
                    "sample_count": 4,
                    "sample_span_sec": 8,
                    "below_ratio": "0.75",
                    "min_below_ratio": "0.67",
                    "window_sec": 20,
                    "min_span_sec": 8,
                    "min_samples": 3,
                    "buffer_pct": "1.00",
                    "profit_rate": "+0.20",
                    "peak_profit": "+1.20",
                    "emergency_pct": "-2.00",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    assert report["stage_contracts"]["protect_trailing_smooth_hold"]["status"] == "pass"
    assert (
        report["stage_contracts"]["protect_trailing_smooth_confirmed"]["status"]
        == "pass"
    )
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_smoothing_source_only_path_contracts_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    state, armed = arm_source_only_path(
        None,
        family="holding_flow_ofi_smoothing",
        position_key="record:1",
        trace_id="trace-1",
        snapshot_id="snapshot-1",
        alternative_action="HOLD",
        control_action="EXIT",
        now_ts=1000.0,
        effective_price=10000,
        effective_profit_rate=-0.5,
        reference_buy_price=10100,
        effective_price_source="ws",
        effective_price_quality="single_source",
        runtime_family_enabled=False,
        alternative_executed=False,
        source_reason="runtime_disabled",
    )
    state, horizon_events = observe_source_only_paths(
        state,
        position_key="record:1",
        now_ts=1010.0,
        effective_price=10010,
        effective_profit_rate=-0.4,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=False,
    )
    _state, close_events = observe_source_only_paths(
        state,
        position_key="record:1",
        now_ts=1015.0,
        effective_price=9800,
        effective_profit_rate=-2.1,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=True,
    )
    generated = [armed, *horizon_events, *close_events]
    _write_events(
        tmp_path,
        "2026-07-15",
        [_event(item["stage"], item["fields"]) for item in generated if item],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    for stage in (
        "smoothing_source_only_path_armed",
        "smoothing_source_only_path_horizon",
        "smoothing_source_only_path_closed",
    ):
        assert report["stage_contracts"][stage]["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_smoothing_source_only_path_contract_rejects_nonpositive_buy_price():
    contract = audit.STAGE_CONTRACTS["smoothing_source_only_path_armed"]
    violations = audit._row_contract_violations(
        "smoothing_source_only_path_armed",
        {"fields": {"reference_buy_price": 0}},
        contract,
    )

    assert "reference_buy_price_positive_contract" in violations["invalid_fields"]


def test_smoothing_v2_path_quality_contract_requires_gap_provenance():
    contract = audit.STAGE_CONTRACTS["smoothing_source_only_path_horizon"]
    violations = audit._row_contract_violations(
        "smoothing_source_only_path_horizon",
        {"fields": {"path_quality_contract_version": "fresh_observation_gap_v2"}},
        contract,
    )
    legacy_violations = audit._row_contract_violations(
        "smoothing_source_only_path_horizon",
        {"fields": {}},
        contract,
    )

    assert "path_max_valid_observation_gap_sec" in violations["missing_fields"]
    assert "path_max_allowed_observation_gap_sec" in violations["missing_fields"]
    assert (
        "path_max_valid_observation_gap_sec" not in legacy_violations["missing_fields"]
    )


def test_market_halt_session_events_artifact_is_gitignored():
    path = Path(
        "data/source_quality/market_halt_windows/session_events/2026-06-08.json"
    )
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
    )

    assert result.returncode == 0


def test_observation_source_quality_audit_flags_missing_ai_fields(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "ai_confirmed",
                {
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "computed_10ticks",
                    "tick_context_quality": "fresh_computed",
                    "quote_age_source": "missing",
                    "latest_strength": "120.0",
                    "buy_pressure_10t": "61.0",
                    "distance_from_day_high_pct": "-1.0",
                    "intraday_range_pct": "4.0",
                },
            ),
            _event(
                "blocked_ai_score",
                {
                    "latest_strength": "120.0",
                    "buy_pressure_10t": "61.0",
                    "distance_from_day_high_pct": "0.0",
                    "intraday_range_pct": "0.0",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["status"] == "warning"
    blocked = report["stage_contracts"]["blocked_ai_score"]
    assert blocked["status"] == "warning"
    assert "tick_accel_source" in blocked["missing_violations"]
    assert blocked["zero_violations"]["intraday_range_pct"] == 1.0
    assert report["summary"]["tuning_input_allowed"] is False
    assert "blocked_ai_score" in report["summary"]["hard_blocking_stages"]
    assert report["summary"]["blocked_reason"] == "blocked_contract_gap"


def _early_accel_contract_fields(*, include_provenance=True):
    fields = {
        "metric_role": "funnel_count",
        "decision_authority": "operator_runtime_observation_retry_only",
        "window_policy": "intraday_operator_runtime_retry",
        "sample_floor": "not_applicable_operator_runtime_retry",
        "primary_decision_metric": "funnel_count",
        "source_quality_gate": "early_accel_recheck_contract_fields_present",
        "runtime_effect": True,
        "forbidden_uses": "threshold_mutation|provider_route_change|bot_restart|broker_guard_bypass",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "scanner_promotion_reason": "probe_acceleration_confirmed",
        "promotion_price": 12280,
        "current_price": 12430,
        "promotion_age_sec": "30.0",
        "recheck_count": 0,
        "last_ai_elapsed_sec": "25.0",
        "skip_reason": "allowed",
        "tick_accel": "1.250",
        "micro_vwap_bp": "12.00",
        "quote_stale": False,
    }
    if include_provenance:
        fields.update(
            {
                "tick_accel_source": "computed_10ticks",
                "tick_context_quality": "fresh_computed",
                "tick_context_stale": False,
                "tick_accel_usable": True,
                "micro_vwap_available": True,
                "minute_candle_context_quality": "fresh_bar_window",
                "minute_candle_window_fresh": True,
                "minute_candle_latest_age_ms": 8000,
                "micro_vwap_usable": True,
            }
        )
    return fields


def test_observation_source_quality_audit_flags_missing_early_accel_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "early_accel_recheck_evaluated",
                _early_accel_contract_fields(include_provenance=False),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["early_accel_recheck_evaluated"]
    assert contract["status"] == "fail"
    assert "tick_accel_source" in contract["missing_violations"]
    assert "micro_vwap_usable" in contract["missing_violations"]
    assert report["summary"]["tuning_input_allowed"] is False
    assert "early_accel_recheck_evaluated" in report["summary"]["hard_blocking_stages"]


def test_observation_source_quality_audit_accepts_early_accel_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [_event("early_accel_recheck_evaluated", _early_accel_contract_fields())],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["early_accel_recheck_evaluated"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_observation_source_quality_audit_accepts_fail_closed_early_accel_gap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = _early_accel_contract_fields()
    fields.update(
        {
            "skip_reason": "micro_vwap_unusable",
            "micro_vwap_available": False,
            "minute_candle_context_quality": "unavailable",
            "minute_candle_window_fresh": False,
            "minute_candle_latest_age_ms": 0,
            "micro_vwap_usable": False,
        }
    )
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event("early_accel_recheck_evaluated", fields),
            _event("early_accel_recheck_skipped", fields),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert (
        report["stage_contracts"]["early_accel_recheck_evaluated"]["status"] == "pass"
    )
    assert report["stage_contracts"]["early_accel_recheck_skipped"]["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_observation_source_quality_accepts_early_accel_pre_feature_skip(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = _early_accel_contract_fields()
    fields.update(
        {
            "skip_reason": "scanner_promotion_reason_not_early_accel",
            "tick_accel_source": "unknown",
            "tick_context_quality": "unknown",
            "tick_accel_usable": False,
            "micro_vwap_available": False,
            "minute_candle_context_quality": "unknown",
            "minute_candle_window_fresh": False,
            "minute_candle_latest_age_ms": 0,
            "micro_vwap_usable": False,
        }
    )
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event("early_accel_recheck_evaluated", fields),
            _event("early_accel_recheck_skipped", fields),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert (
        report["stage_contracts"]["early_accel_recheck_evaluated"]["status"] == "pass"
    )
    assert report["stage_contracts"]["early_accel_recheck_skipped"]["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_ai_confirmed_terminal_no_budget_contract_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "ai_confirmed_terminal_no_budget",
                {
                    "metric_role": "funnel_count",
                    "decision_authority": "ai_confirmed_terminal_attribution_only",
                    "window_policy": "same_day_intraday_events",
                    "sample_floor": 1,
                    "primary_decision_metric": "funnel_count",
                    "source_quality_gate": "terminal_reason_contract_fields_present",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "allowed_runtime_apply": False,
                    "terminal_reason": "blocked_ai_score_below_buy_score_threshold",
                    "source_stage": "blocked_ai_score",
                    "ai_score": "71.0",
                    "ai_action": "WAIT",
                    "entry_score_threshold": "75.0",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["ai_confirmed_terminal_no_budget"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_observation_source_quality_audit_detects_high_volume_contract_gap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "strength_momentum_observed",
                {"reason": "below_strength_base"},
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    gaps = {item["stage"]: item for item in report["high_volume_no_source_fields"]}
    assert gaps["strength_momentum_observed"]["event_count"] == 60
    assert report["policy"]["decision_authority"] == "source_quality_only"
    assert report["summary"]["tuning_input_allowed"] is False
    assert report["summary"]["hard_blocking_contract_gap_count"] == 1


def test_partial_fill_reconciled_metric_contract_prevents_high_volume_hard_block(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "partial_fill_reconciled",
                {
                    "requested_qty": 10,
                    "filled_qty": 3,
                    "fill_ratio": "0.300",
                    "metric_role": "ops_reconciliation_diagnostic",
                    "decision_authority": "diagnostic_only_no_tuning_authority",
                    "window_policy": "same_day_reconciliation_diagnostic",
                    "sample_floor": "not_applicable_diagnostic",
                    "primary_decision_metric": "none_diagnostic_only",
                    "source_quality_gate": "partial_fill_reconciled_contract_fields_present",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "forbidden_uses": (
                        "EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval/"
                        "broker_order_authority/provider_route_change/bot_restart/threshold_mutation"
                    ),
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    gaps = {item["stage"]: item for item in report["high_volume_no_source_fields"]}
    assert "partial_fill_reconciled" not in gaps
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_warns_on_high_rate_unknown_tokens(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "candidate_id": f"ADM-{idx}",
                    "entry_adm_candidate_id": f"ADM-{idx}",
                    "ai_score": "62.0",
                    "ai_action": "WAIT",
                    "chosen_action": "NO_BUY_AI",
                    "eligible_actions": "NO_BUY_AI",
                    "rejected_actions": "BUY_NOW",
                    "source_stage": "ai_confirmed",
                    "entry_adm_score_bucket": "score_unknown",
                    "entry_adm_stale_bucket": "stale_unknown",
                    "entry_adm_overbought_bucket": "overbought_unknown",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "computed_10ticks",
                    "tick_context_quality": "fresh_computed",
                    "quote_age_source": "last_ws_update_ts",
                    "tick_acceleration_ratio": "1.250",
                    "tick_acceleration_ratio_raw": "1.250",
                    "recent_5tick_seconds": "2.000",
                    "prev_5tick_seconds": "2.500",
                    "tick_accel_effective_recent_5tick_seconds": "2.000",
                    "buy_pressure_10t": "70.000",
                    "curr_vs_micro_vwap_bp": "8.000",
                    "curr_vs_ma5_bp": "5.000",
                    "micro_vwap_available": True,
                    "minute_candle_context_quality": "fresh_bar_window",
                    "minute_candle_window_fresh": True,
                    "minute_candle_latest_age_ms": 12000,
                    "latest_strength": "120.0",
                    "distance_from_day_high_pct": "-0.50",
                    "intraday_range_pct": "2.10",
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["status"] == "warning"
    assert report["summary"]["unknown_token_stage_count"] == 1
    finding = report["unknown_token_findings"][0]
    assert finding["stage"] == "scalp_entry_action_decision_snapshot"
    fields = {item["field"]: item for item in finding["fields"]}
    assert fields["entry_adm_score_bucket"]["rate"] == 1.0
    assert fields["entry_adm_stale_bucket"]["rate"] == 1.0
    assert finding["decision_authority"] == "source_quality_only"
    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["review_warning_count"] == 1
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert finding["runtime_effect"] is False


def test_entry_latency_block_accepts_explicit_fail_closed_candle_gap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-23",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "unavailable_fail_closed",
                    "tick_context_quality": "unavailable_fail_closed",
                    "quote_age_source": "unavailable_fail_closed",
                    "candidate_id": "ADM-LATENCY-BLOCK",
                    "entry_adm_candidate_id": "ADM-LATENCY-BLOCK",
                    "ai_score": "50",
                    "ai_action": "WAIT",
                    "chosen_action": "SKIP_PRE_SUBMIT_SAFETY",
                    "eligible_actions": "SKIP_PRE_SUBMIT_SAFETY",
                    "rejected_actions": "BUY_NOW",
                    "source_stage": "latency_block",
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "tick_acceleration_ratio": "not_evaluated",
                    "tick_acceleration_ratio_raw": "not_evaluated",
                    "recent_5tick_seconds": "not_evaluated",
                    "prev_5tick_seconds": "not_evaluated",
                    "tick_accel_effective_recent_5tick_seconds": "not_evaluated",
                    "buy_pressure_10t": "not_evaluated_runtime_block",
                    "curr_vs_micro_vwap_bp": 0.0,
                    "curr_vs_ma5_bp": 0.0,
                    "micro_vwap_available": False,
                    "minute_candle_context_quality": "unavailable_fail_closed",
                    "minute_candle_window_fresh": False,
                    "minute_candle_latest_age_ms": -1.0,
                    "minute_candle_evaluation_state": "unavailable_fail_closed",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    contract = report["stage_contracts"]["scalp_entry_action_decision_snapshot"]
    assert contract["status"] == "pass"
    assert contract["invalid_label_violations"] == {}


def test_entry_preflight_block_accepts_explicit_fail_closed_candle_gap():
    fields = {
        "source_stage": "ai_confirmed",
        "ai_input_preflight_status": "blocked",
        "ai_input_preflight_allowed": False,
        "provider_called": False,
        "minute_candle_evaluation_state": "unavailable_fail_closed",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    assert audit._blocked_observation_records_fail_closed_source_gap(
        "scalp_entry_action_decision_snapshot",
        fields,
        source="minute_candle",
    )

    fields["provider_called"] = True
    assert not audit._blocked_observation_records_fail_closed_source_gap(
        "scalp_entry_action_decision_snapshot",
        fields,
        source="minute_candle",
    )


def test_entry_transport_timeout_accepts_explicit_fail_closed_candle_gap():
    fields = {
        "source_stage": "ai_confirmed",
        "provider_called": True,
        "openai_transport_fail_closed_reason": "request timed out",
        "ai_decision_evaluation_status": "not_evaluated_transport_timeout",
        "minute_candle_evaluation_state": "unavailable_fail_closed",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    assert audit._blocked_observation_records_fail_closed_source_gap(
        "scalp_entry_action_decision_snapshot",
        fields,
        source="minute_candle",
    )


def test_entry_final_source_quality_block_accepts_explicit_fail_closed_candle_gap():
    fields = {
        "source_stage": "real_weak_ai_micro_entry_block",
        "entry_action_final_blocked": True,
        "entry_action_final_block_reason": "source_quality_unknown",
        "minute_candle_evaluation_state": "unavailable_fail_closed",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    assert audit._blocked_observation_records_fail_closed_source_gap(
        "scalp_entry_action_decision_snapshot",
        fields,
        source="minute_candle",
    )


def test_explicit_fail_closed_rows_keep_provenance_but_allow_unevaluated_values():
    pyramid_contract = audit.STAGE_CONTRACTS["pyramid_blocked_reason"]
    pyramid_fields = {field: "observed" for field in pyramid_contract.required_fields}
    pyramid_fields.update(
        {
            "curr_vs_micro_vwap_bp": "-",
            "tick_aggressor_trusted_count": 4,
            "tick_aggressor_pressure_usable": True,
            "micro_vwap_available": False,
            "minute_candle_context_quality": "missing",
            "minute_candle_window_fresh": False,
            "minute_candle_latest_age_ms": -1.0,
            "minute_candle_evaluation_state": "unavailable_fail_closed",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "allowed_runtime_apply": False,
        }
    )
    pyramid_violations = audit._row_contract_violations(
        "pyramid_blocked_reason",
        {"fields": pyramid_fields},
        pyramid_contract,
    )

    assert "curr_vs_micro_vwap_bp" not in pyramid_violations["missing_fields"]
    assert (
        "minute_candle_window_fresh_contract"
        not in pyramid_violations["invalid_fields"]
    )

    submitted_pyramid_fields = {
        **pyramid_fields,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
    }
    submitted_pyramid_violations = audit._row_contract_violations(
        "pyramid_blocked_reason",
        {"fields": submitted_pyramid_fields},
        pyramid_contract,
    )
    assert "curr_vs_micro_vwap_bp" in submitted_pyramid_violations["missing_fields"]

    adverse_contract = audit.STAGE_CONTRACTS["adverse_fill_observed"]
    adverse_fields = {field: "observed" for field in adverse_contract.required_fields}
    adverse_fields.update(
        {
            "feature_valid": False,
            "micro_context_usable": "-",
            "tick_aggressor_trusted_count": 0,
            "tick_aggressor_pressure_usable": False,
            "micro_vwap_available": False,
            "minute_candle_context_quality": "missing",
            "minute_candle_window_fresh": False,
            "minute_candle_latest_age_ms": -1.0,
        }
    )
    adverse_violations = audit._row_contract_violations(
        "adverse_fill_observed",
        {"fields": adverse_fields},
        adverse_contract,
    )

    assert "micro_context_usable" not in adverse_violations["missing_fields"]
    assert adverse_violations["invalid_fields"] == []


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source_stage", "entry_candidate"),
        ("minute_candle_evaluation_state", "available"),
        ("actual_order_submitted", True),
        ("broker_order_forbidden", False),
    ),
)
def test_entry_candle_gap_exemption_rejects_authoritative_or_non_block_rows(
    field, value
):
    fields = {
        "source_stage": "latency_block",
        "minute_candle_evaluation_state": "unavailable_fail_closed",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    fields[field] = value

    assert not audit._blocked_observation_records_fail_closed_source_gap(
        "scalp_entry_action_decision_snapshot",
        fields,
        source="minute_candle",
    )


def test_observation_source_quality_audit_reviews_entry_block_source_quality_unknown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "scalp_entry_action_decision_snapshot",
            {
                "block_reason": "source_quality_unknown",
                "metric_role": "action_decision_matrix",
                "decision_authority": "entry_advisory_prompt_context_only",
                "source_quality_gate": "source_quality_review_warning",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            record_id=1,
        ),
        _event(
            "real_weak_ai_micro_entry_block",
            {
                "reason": "source_quality_unknown",
                "block_reason": "source_quality_unknown",
                "metric_role": "entry_block_observation",
                "decision_authority": "real_buy_submit_source_quality_guard",
                "source_quality_gate": "weak_ai_micro_context_contract",
                "runtime_effect": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            record_id=2,
        ),
    ]
    _write_events(tmp_path, "2026-05-15", rows)

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: item for item in report["reviewed_unknown_token_findings"]
    }
    snapshot_fields = {
        item["field"]: item
        for item in reviewed["scalp_entry_action_decision_snapshot"]["fields"]
    }
    weak_fields = {
        item["field"]: item
        for item in reviewed["real_weak_ai_micro_entry_block"]["fields"]
    }
    assert snapshot_fields["block_reason"]["reviewed_reason"] == (
        "reviewed_entry_block_source_quality_unknown_provenance"
    )
    assert (
        weak_fields["reason"]["reviewed_reason"]
        == "reviewed_entry_block_source_quality_unknown_provenance"
    )
    assert (
        weak_fields["block_reason"]["reviewed_reason"]
        == "reviewed_entry_block_source_quality_unknown_provenance"
    )
    assert report["summary"]["review_warning_count"] == 0


def test_observation_source_quality_audit_reviews_live_liquidity_would_unknown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "latency_pass",
                {
                    "reason": "caution_normal_entry_allowed",
                    "latency_state": "CAUTION",
                    "policy_decision": "ALLOW_NORMAL",
                    "effective_decision": "ALLOW_NORMAL",
                    "ws_age_ms": "69",
                    "ws_jitter_ms": "0",
                    "spread_ratio": "0.004505",
                    "quote_stale": False,
                    "signal_price": "17760",
                    "latest_price": "17760",
                    "latency_canary_applied": False,
                    "latency_canary_reason": "",
                    "latency_strategy_id": "SCALPING",
                    "latency_position_tag": "SCANNER",
                    "latency_spread_relief_tag": "SCANNER",
                    "latency_spread_relief_signal_score": "0.0",
                    "latency_spread_relief_configured_min_signal_score": "60.0",
                    "latency_spread_relief_effective_min_signal_score": "80.0",
                    "latency_spread_relief_block_reason": "",
                    "latency_spread_relief_signal_score_source": "input_signal_strength_zero",
                    "latency_spread_relief_signal_source_quality_state": "missing",
                    "latency_spread_relief_candidate_ai_score": "0.0",
                    "latency_spread_relief_candidate_ai_score_source": "",
                    "latency_spread_relief_source_quality_gap": "signal_strength_missing",
                    "latency_spread_block_bucket": "spread_not_above_caution",
                    "latency_spread_block_price_bucket": "spread_not_above_caution",
                    "latency_spread_block_signal_context_bucket": "signal_missing",
                    "latency_spread_block_spread_bps": "45.05",
                    "latency_spread_block_spread_ticks": "3",
                    "threshold_family": "latency_classifier_runtime_profile",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": False,
                    "liquidity_guard_action": "WOULD_UNKNOWN",
                    "liquidity_guard_reason": "liquidity_not_available",
                    "pre_submit_liquidity_guard_action": "NOT_AVAILABLE",
                    "pre_submit_liquidity_reason": "liquidity_not_available",
                    "pre_submit_liquidity_value": "not_available",
                    "pre_submit_min_liquidity": "0",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["unknown_token_findings"] == []
    reviewed = report["reviewed_unknown_token_findings"]
    assert reviewed[0]["stage"] == "latency_pass"
    fields = {item["field"]: item for item in reviewed[0]["fields"]}
    assert (
        fields["liquidity_guard_action"]["reviewed_reason"]
        == "reviewed_pre_submit_liquidity_not_available"
    )
    assert report["summary"]["review_warning_count"] == 0


def test_observation_source_quality_audit_reviews_sell_order_exchange_resolution_unknown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-02",
        [
            _event(
                "sell_order_sent",
                {
                    "metric_role": "real_execution_diagnostic",
                    "decision_authority": "order_execution_observation_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                    "forbidden_uses": "threshold_mutation/provider_route_change/bot_restart",
                    "order_id": f"ORD-{idx}",
                    "order_type": "market",
                    "order_type_code": "3",
                    "market": "KRX",
                    "exchange": "NXT",
                    "sell_order_exchange_resolution_reason": "nxt_session_nxt_enabled_or_unknown",
                },
                record_id=idx,
            )
            for idx in range(20)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-02")

    assert report["unknown_token_findings"] == []
    reviewed = report["reviewed_unknown_token_findings"]
    assert reviewed
    fields = {item["field"]: item for item in reviewed[0]["fields"]}
    assert (
        fields["sell_order_exchange_resolution_reason"]["reviewed_reason"]
        == "reviewed_sell_order_exchange_resolution_not_available"
    )
    assert report["summary"]["review_warning_count"] == 0


def test_observation_source_quality_audit_reviews_entry_adm_price_unknown_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "candidate_id": "ADM-1",
                    "entry_adm_candidate_id": "ADM-1",
                    "entry_adm_status": "advisory_prompt_applied",
                    "entry_adm_version": "scalp_entry_adm_v1_2026-05-14",
                    "entry_adm_source_date": "2026-05-14",
                    "entry_adm_application_mode": "operator_override_advisory_prompt",
                    "entry_adm_loaded_from": "/tmp/scalp_entry_action_decision_matrix_2026-05-14.json",
                    "entry_adm_cache_token": (
                        "entry_adm:scalp_entry_adm_v1_2026-05-14:"
                        "score50_64|neutral_strength_momentum|-|stale_high|price_unknown|"
                        "liquidity_high|overbought_ok|time_0900_1000"
                    ),
                    "entry_adm_bucket_token": (
                        "score50_64|neutral_strength_momentum|-|stale_high|price_unknown|"
                        "liquidity_high|overbought_ok|time_0900_1000"
                    ),
                    "entry_adm_price_resolution_bucket": "price_unknown",
                    "entry_adm_score_bucket": "score50_64",
                    "entry_adm_risk_context_bucket": "neutral_strength_momentum",
                    "entry_adm_stale_bucket": "stale_high",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "entry_adm_overbought_bucket": "overbought_ok",
                    "entry_adm_time_bucket": "time_0900_1000",
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "computed_10ticks",
                    "tick_context_quality": "fresh_computed",
                    "quote_age_source": "last_ws_update_ts",
                    "tick_acceleration_ratio": "1.250",
                    "tick_acceleration_ratio_raw": "1.250",
                    "recent_5tick_seconds": "2.000",
                    "prev_5tick_seconds": "2.500",
                    "tick_accel_effective_recent_5tick_seconds": "2.000",
                    "buy_pressure_10t": "70.000",
                    "curr_vs_micro_vwap_bp": "8.000",
                    "curr_vs_ma5_bp": "5.000",
                    "micro_vwap_available": True,
                    "minute_candle_context_quality": "fresh_bar_window",
                    "minute_candle_window_fresh": True,
                    "minute_candle_latest_age_ms": 12000,
                    "latest_strength": "120.0",
                    "distance_from_day_high_pct": "-0.50",
                    "intraday_range_pct": "2.10",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["unknown_token_findings"] == []
    reviewed = next(
        item
        for item in report["reviewed_unknown_token_findings"]
        if item["stage"] == "scalp_entry_action_decision_snapshot"
    )
    fields = {item["field"]: item for item in reviewed["fields"]}
    assert (
        fields["entry_adm_cache_token"]["reviewed_reason"]
        == "reviewed_entry_adm_bucket_provenance_recorded"
    )
    assert (
        fields["entry_adm_bucket_token"]["reviewed_reason"]
        == "reviewed_entry_adm_bucket_provenance_recorded"
    )
    assert (
        fields["entry_adm_price_resolution_bucket"]["reviewed_reason"]
        == "reviewed_entry_adm_bucket_provenance_recorded"
    )


def test_observation_source_quality_audit_surfaces_ai_numeric_consistency_findings(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-18",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "candidate_id": "ADM-123456-1",
                    "entry_adm_candidate_id": "ADM-123456-1",
                    "ai_score": "62.0",
                    "ai_action": "WAIT",
                    "chosen_action": "NO_BUY_AI",
                    "eligible_actions": "NO_BUY_AI",
                    "rejected_actions": "BUY_NOW",
                    "source_stage": "ai_confirmed",
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "source_quality_gate": "ai_numeric_consistency_review_required",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "EV/live-auto/runtime-apply/threshold mutation",
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "same_second_burst_10ticks",
                    "tick_context_quality": "fresh_computed",
                    "quote_age_source": "last_ws_update_ts",
                    "tick_acceleration_ratio": "24.000",
                    "tick_acceleration_ratio_raw": "0.000",
                    "recent_5tick_seconds": "0.000",
                    "prev_5tick_seconds": "24.000",
                    "tick_accel_effective_recent_5tick_seconds": "1.000",
                    "buy_pressure_10t": "71.200",
                    "curr_vs_micro_vwap_bp": "11.400",
                    "curr_vs_ma5_bp": "9.800",
                    "micro_vwap_available": True,
                    "minute_candle_context_quality": "fresh_bar_window",
                    "minute_candle_window_fresh": True,
                    "minute_candle_latest_age_ms": 12000,
                    "latest_strength": "130.0",
                    "distance_from_day_high_pct": "-0.40",
                    "intraday_range_pct": "2.10",
                    "ai_reason_numeric_inconsistency": True,
                    "ai_reason_numeric_inconsistency_field": "tick_acceleration_ratio",
                    "ai_reason_numeric_inconsistency_reason": "tick_acceleration_pass_described_as_fail",
                    "ai_reason_numeric_inconsistency_detected_value": "24.0",
                    "ai_reason_numeric_inconsistency_excerpt": "tick_acceleration_ratio = 24.0 fails < 1.10",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-18")

    assert report["status"] == "warning"
    assert report["summary"]["numeric_consistency_stage_count"] == 1
    assert report["summary"]["review_warning_count"] == 1
    finding = report["numeric_consistency_findings"][0]
    assert finding["stage"] == "scalp_entry_action_decision_snapshot"
    assert finding["allowed_runtime_apply"] is False
    assert finding["examples"][0]["field"] == "tick_acceleration_ratio"


def test_observation_source_quality_audit_warns_on_any_unknown_token_field(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "arbitrary_source_stage",
            {
                "source_id": f"SRC-{idx}",
                "custom_context_state": (
                    "custom_unknown_placeholder" if idx == 7 else "observed"
                ),
            },
            record_id=idx,
        )
        for idx in range(100)
    ]
    _write_events(tmp_path, "2026-06-04", rows)

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["status"] == "warning"
    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["review_warning_count"] == 1
    assert report["summary"]["tuning_input_allowed"] is True
    finding = report["unknown_token_findings"][0]
    assert finding["stage"] == "arbitrary_source_stage"
    fields = {item["field"]: item for item in finding["fields"]}
    assert fields["custom_context_state"]["count"] == 1
    assert fields["custom_context_state"]["rate"] == 0.01


def test_observation_source_quality_audit_separates_reviewed_unknown_tokens(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "orderbook_stability_observed",
            {
                "orderbook_micro_ofi_bucket_key": "spread=unknown|price=unknown|depth=unknown|sample=insufficient",
                "custom_context_state": "observed",
            },
            record_id=1,
        ),
        _event(
            "orderbook_stability_observed",
            {
                "orderbook_micro_ofi_bucket_key": "spread=known|price=known|depth=known|sample=ok",
                "custom_context_state": "custom_unknown_placeholder",
            },
            record_id=2,
        ),
    ]
    _write_events(tmp_path, "2026-06-04", rows)

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    finding = report["unknown_token_findings"][0]
    assert {field["field"] for field in finding["fields"]} == {"custom_context_state"}
    reviewed = report["reviewed_unknown_token_findings"][0]
    reviewed_fields = {field["field"]: field for field in reviewed["fields"]}
    assert (
        reviewed_fields["orderbook_micro_ofi_bucket_key"]["reviewed_reason"]
        == "reviewed_insufficient_sample"
    )


def test_observation_source_quality_audit_reviews_legacy_orderbook_micro_unknown_bucket(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_scale_in_micro_context_observed",
                {
                    "orderbook_micro_ofi_threshold_bucket_key": (
                        "spread=unknown|price=high|depth=normal|sample=normal"
                    ),
                    "orderbook_micro_ofi_calibration_bucket": (
                        "spread=unknown|price=high|depth=normal|sample=normal"
                    ),
                    "orderbook_micro_ofi_bucket_key": (
                        "spread=unknown|price=high|depth=normal|sample=normal"
                    ),
                    "custom_context_state": "observed",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed = report["reviewed_unknown_token_findings"][0]
    fields = {item["field"]: item for item in reviewed["fields"]}
    assert fields["orderbook_micro_ofi_bucket_key"]["reviewed_reason"] == (
        "reviewed_orderbook_micro_legacy_not_available_bucket"
    )


def test_observation_source_quality_audit_reviews_stale_flag_unknown_when_age_not_available(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-03",
        [
            _event(
                "stat_action_decision_snapshot",
                {
                    "tick_context_stale": "unknown",
                    "tick_latest_age_ms": "-",
                    "tick_context_quality": "missing_ticks",
                    "quote_stale": "unknown",
                    "quote_age_ms": "-",
                    "quote_age_source": "missing",
                },
                record_id=1,
            ),
            _event(
                "scale_in_qty_block",
                {
                    "tick_context_stale": "unknown",
                    "tick_latest_age_ms": "-",
                    "tick_context_quality": "missing_tick_time",
                    "quote_stale": "unknown",
                    "quote_age_ms": "-",
                    "quote_age_source": "missing",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-03")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 2
    reviewed_by_stage = {
        item["stage"]: {field["field"]: field for field in item["fields"]}
        for item in report["reviewed_unknown_token_findings"]
    }
    for stage in ("stat_action_decision_snapshot", "scale_in_qty_block"):
        assert reviewed_by_stage[stage]["tick_context_stale"]["reviewed_reason"] == (
            "reviewed_stale_flag_not_available"
        )
        assert reviewed_by_stage[stage]["quote_stale"]["reviewed_reason"] == (
            "reviewed_stale_flag_not_available"
        )


def test_observation_source_quality_audit_warns_on_new_orderbook_micro_unknown_bucket(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    row = _event(
        "swing_scale_in_micro_context_observed",
        {
            "orderbook_micro_ofi_bucket_key": "spread=unknown|price=high|depth=normal|sample=normal",
            "custom_context_state": "observed",
        },
        record_id=1,
    )
    row["emitted_at"] = "2026-06-09T10:00:00"
    row["emitted_date"] = "2026-06-09"
    _write_events(tmp_path, "2026-06-09", [row])

    report = audit.build_observation_source_quality_audit("2026-06-09")

    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 0
    finding = report["unknown_token_findings"][0]
    fields = {item["field"]: item for item in finding["fields"]}
    assert fields["orderbook_micro_ofi_bucket_key"]["count"] == 1


def test_observation_source_quality_audit_reviews_missing_risk_regime_context(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "risk_regime_context": {
                        "panic_context_status": "MISSING",
                        "panic_level_reason": "context_not_ok",
                        "panic_epoch_id": "2026-06-04|NORMAL|NORMAL|L0|unknown",
                        "market_risk_state": "UNKNOWN",
                    },
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed = report["reviewed_unknown_token_findings"][0]
    assert reviewed["stage"] == "scalp_entry_action_decision_snapshot"
    assert (
        reviewed["fields"][0]["reviewed_reason"]
        == "reviewed_missing_risk_regime_context"
    )
    assert reviewed["runtime_effect"] is False


def test_observation_source_quality_audit_reviews_panic_context_warning_unknown_fields(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_sim_panic_context_warning",
                {
                    "panic_epoch_id": "2026-06-04|NORMAL|NORMAL|L0|unknown",
                    "market_risk_state": "UNKNOWN",
                    "liquidity_state": "UNKNOWN",
                    "risk_regime_epoch_id": "2026-06-04|NORMAL|NORMAL|L0|unknown",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed_fields = {
        item["field"]: item
        for item in report["reviewed_unknown_token_findings"][0]["fields"]
    }
    assert (
        reviewed_fields["panic_epoch_id"]["reviewed_reason"]
        == "reviewed_missing_risk_regime_context"
    )
    assert (
        reviewed_fields["market_risk_state"]["reviewed_reason"]
        == "reviewed_missing_risk_regime_context"
    )


def test_observation_source_quality_audit_reviews_runtime_skip_context_unknown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-06",
        [
            _event(
                "scalping_scanner_watching_runtime_skip",
                {
                    "decision_authority": "real_scalping_scanner_runtime_watchlist_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "skip_reason": "entry_cooldown_active",
                    "tick_context_quality": "unknown",
                    "minute_candle_context_quality": "unknown",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-06")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = report["reviewed_unknown_token_findings"][0]
    fields = {item["field"]: item for item in reviewed["fields"]}
    assert (
        fields["tick_context_quality"]["reviewed_reason"]
        == "reviewed_runtime_skip_context_not_evaluated"
    )
    assert (
        fields["minute_candle_context_quality"]["reviewed_reason"]
        == "reviewed_runtime_skip_context_not_evaluated"
    )


def test_observation_source_quality_audit_reviews_score_and_micro_context_unknowns(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-06",
        [
            _event(
                "early_accel_recheck_evaluated",
                {
                    "decision_authority": "operator_runtime_observation_retry_only",
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "skip_reason": "micro_vwap_unusable",
                    "tick_accel_usable": False,
                    "micro_vwap_usable": False,
                    "minute_candle_window_fresh": False,
                    "tick_accel_source": "unknown",
                    "tick_context_quality": "unknown",
                    "minute_candle_context_quality": "unknown",
                },
                record_id=1,
            ),
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "entry_score_source": "unknown",
                    "entry_score_excluded_reason": "unusable_source:unknown",
                    "entry_recheck_excluded_reason": "unusable_source:unknown",
                    "score_prior_band": "neutral_or_unknown",
                    "score_prior_confidence": "unknown",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-06")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = {
        item["stage"]: {field["field"]: field for field in item["fields"]}
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["early_accel_recheck_evaluated"]["tick_accel_source"][
        "reviewed_reason"
    ] == ("reviewed_unusable_micro_context_not_available")
    assert reviewed["scalp_entry_action_decision_snapshot"]["entry_score_source"][
        "reviewed_reason"
    ] == ("reviewed_entry_score_source_not_available")
    assert reviewed["scalp_entry_action_decision_snapshot"][
        "entry_recheck_excluded_reason"
    ]["reviewed_reason"] == ("reviewed_entry_score_source_not_available")
    assert reviewed["scalp_entry_action_decision_snapshot"]["score_prior_confidence"][
        "reviewed_reason"
    ] == ("reviewed_score_prior_neutral_unknown_not_decision_input")


def test_observation_source_quality_audit_reviews_rising_missed_nxt_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-15",
        [
            _event(
                "rising_missed_one_share_entry",
                {
                    "rising_missed_nxt_eligible": "unknown",
                    "rising_missed_nxt_observation_only": True,
                    "rising_missed_nxt_metric_role": "source_quality_gate",
                    "rising_missed_nxt_decision_authority": "observe_only_no_runtime_mutation",
                    "rising_missed_nxt_source_quality_gate": (
                        "absolute_type_receive_ts_and_actual_ws_item_route"
                    ),
                    "rising_missed_effective_venue": "NXT_ELIGIBILITY_UNKNOWN",
                    "latency_true_ofi_nxt_probability_band_effective_venue": (
                        "NXT_ELIGIBILITY_UNKNOWN"
                    ),
                    "latency_true_ofi_nxt_probability_band_context": False,
                    "latency_true_ofi_nxt_probability_band_applied": False,
                },
            ),
            _event(
                "rising_missed_nxt_post_block_price_sample",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "source_only_nxt_post_block_price_observation",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_quality_gate": "fresh_absolute_0b_receive_ts_and_actual_nxt_item_route",
                    "rising_missed_nxt_post_block_ws_0b_route": "unknown",
                },
                record_id=2,
            ),
            _event(
                "rising_missed_one_share_entry",
                {
                    "rising_missed_nxt_eligible": "unknown",
                    "rising_missed_nxt_observation_only": True,
                    "rising_missed_nxt_metric_role": "source_quality_gate",
                    "rising_missed_nxt_decision_authority": "observe_only_no_runtime_mutation",
                    "rising_missed_nxt_source_quality_gate": (
                        "absolute_type_receive_ts_and_actual_ws_item_route"
                    ),
                    "rising_missed_effective_venue": "OFF_SESSION",
                },
                record_id=3,
            ),
            _event(
                "budget_pass",
                {
                    "rising_missed_nxt_eligible": "unknown",
                    "rising_missed_effective_venue": "OFF_SESSION",
                    "rising_missed_nxt_micro_state_role": (
                        "ws_transport_activity_not_positive_evidence"
                    ),
                    "rising_missed_nxt_positive_micro_authority": (
                        "trusted_signed_ws_0b_existing_tp1_contract"
                    ),
                },
                record_id=4,
            ),
            _event(
                "probe_submitted",
                {
                    "rising_missed_nxt_eligible": "unknown",
                    "rising_missed_nxt_observation_only": True,
                    "rising_missed_nxt_metric_role": "source_quality_gate",
                    "rising_missed_nxt_decision_authority": (
                        "observe_only_no_runtime_mutation"
                    ),
                    "rising_missed_nxt_source_quality_gate": (
                        "absolute_type_receive_ts_and_actual_ws_item_route"
                    ),
                    "rising_missed_effective_venue": "PREMARKET_KRX_LIKE",
                },
                record_id=5,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = {
        item["stage"]: {field["field"]: field for field in item["fields"]}
        for item in report["reviewed_unknown_token_findings"]
    }
    nxt_reviewed = reviewed["rising_missed_one_share_entry"]
    assert nxt_reviewed["rising_missed_nxt_eligible"]["reviewed_reason"] == (
        "reviewed_rising_missed_nxt_eligibility_not_available"
    )
    assert nxt_reviewed["rising_missed_effective_venue"]["reviewed_reason"] == (
        "reviewed_rising_missed_nxt_eligibility_not_available"
    )
    assert nxt_reviewed["latency_true_ofi_nxt_probability_band_effective_venue"][
        "reviewed_reason"
    ] == ("reviewed_rising_missed_nxt_eligibility_not_available")
    assert (
        reviewed["rising_missed_nxt_post_block_price_sample"][
            "rising_missed_nxt_post_block_ws_0b_route"
        ]["reviewed_reason"]
        == "reviewed_rising_missed_nxt_post_block_route_not_available"
    )
    assert reviewed["budget_pass"]["rising_missed_nxt_eligible"]["reviewed_reason"] == (
        "reviewed_rising_missed_nxt_eligibility_not_available"
    )


def test_observation_source_quality_audit_does_not_review_applied_nxt_probability_band_unknown(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-15",
        [
            _event(
                "latency_pass",
                {
                    "rising_missed_nxt_eligible": "unknown",
                    "rising_missed_nxt_observation_only": True,
                    "rising_missed_nxt_metric_role": "source_quality_gate",
                    "rising_missed_nxt_decision_authority": (
                        "observe_only_no_runtime_mutation"
                    ),
                    "rising_missed_nxt_source_quality_gate": (
                        "absolute_type_receive_ts_and_actual_ws_item_route"
                    ),
                    "rising_missed_effective_venue": "NXT_ELIGIBILITY_UNKNOWN",
                    "latency_true_ofi_nxt_probability_band_effective_venue": (
                        "NXT_ELIGIBILITY_UNKNOWN"
                    ),
                    "latency_true_ofi_nxt_probability_band_context": True,
                    "latency_true_ofi_nxt_probability_band_applied": True,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    finding = next(
        item
        for item in report["unknown_token_findings"]
        if item["stage"] == "latency_pass"
    )
    assert any(
        field["field"] == "latency_true_ofi_nxt_probability_band_effective_venue"
        for field in finding["fields"]
    )


def test_observation_source_quality_audit_reviews_explicit_sim_liquidity_unknown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-12",
        [
            _event(
                "scalp_sim_pre_submit_liquidity_guard_unknown",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_submit_path_observation_only",
                    "runtime_effect": False,
                    "sim_record_id": "SIM-1",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "sim_pre_submit_liquidity_guard_action": "WOULD_UNKNOWN",
                    "sim_pre_submit_liquidity_reason": "liquidity_not_available",
                    "sim_liquidity_value": "not_available",
                    "sim_min_liquidity": 500_000_000,
                    "sim_parent_record_id": 1,
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-12")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed = report["reviewed_unknown_token_findings"][0]
    fields = {item["field"]: item for item in reviewed["fields"]}
    assert fields["sim_pre_submit_liquidity_guard_action"]["reviewed_reason"] == (
        "reviewed_sim_liquidity_not_available"
    )
    assert (
        fields["__stage"]["reviewed_reason"]
        == "reviewed_explicit_sim_liquidity_unknown_stage"
    )


def test_observation_source_quality_audit_warns_on_uncontracted_liquidity_unknown(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-12",
        [
            _event(
                "scalp_sim_pre_submit_liquidity_guard_unknown",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "unexpected_authority",
                    "runtime_effect": False,
                    "sim_record_id": "SIM-1",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "sim_pre_submit_liquidity_guard_action": "WOULD_UNKNOWN",
                    "sim_pre_submit_liquidity_reason": "producer_placeholder_unknown",
                    "sim_liquidity_value": "UNKNOWN",
                    "sim_min_liquidity": 500_000_000,
                    "sim_parent_record_id": 1,
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-12")

    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 0
    finding = report["unknown_token_findings"][0]
    fields = {item["field"]: item for item in finding["fields"]}
    assert "sim_pre_submit_liquidity_guard_action" in fields
    assert "__stage" in fields


def test_observation_source_quality_audit_reviews_propagated_sim_liquidity_unknown(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common = {
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "sim_pre_submit_liquidity_guard_action": "WOULD_UNKNOWN",
        "sim_pre_submit_liquidity_reason": "liquidity_not_available",
        "sim_liquidity_value": "not_available",
        "sim_min_liquidity": 350_000_000,
        "sim_parent_record_id": 1,
    }
    _write_events(
        tmp_path,
        "2026-06-12",
        [
            _event(
                "scalp_sim_entry_armed",
                {
                    **common,
                    "decision_authority": "sim_observation_only",
                },
                record_id=1,
            ),
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    **common,
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "source_stage": "scalp_sim_entry_armed",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-12")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 2
    reviewed = {
        item["stage"]: {field["field"]: field for field in item["fields"]}
        for item in report["reviewed_unknown_token_findings"]
    }
    assert (
        reviewed["scalp_sim_entry_armed"]["sim_pre_submit_liquidity_guard_action"][
            "reviewed_reason"
        ]
        == "reviewed_sim_liquidity_not_available"
    )
    assert (
        reviewed["scalp_entry_action_decision_snapshot"][
            "sim_pre_submit_liquidity_guard_action"
        ]["reviewed_reason"]
        == "reviewed_sim_liquidity_not_available"
    )


def test_observation_source_quality_audit_reviews_rising_missed_submit_backoff_reason(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-10",
        [
            _event(
                "real_weak_ai_micro_entry_block",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "source_quality_only",
                    "runtime_effect": False,
                    "rising_missed_submit_safety_backoff_reason": "source_quality_missing_or_unknown",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-10")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed = report["reviewed_unknown_token_findings"][0]
    assert reviewed["stage"] == "real_weak_ai_micro_entry_block"
    assert reviewed["runtime_effect"] is False
    fields = {item["field"]: item for item in reviewed["fields"]}
    assert fields["rising_missed_submit_safety_backoff_reason"]["reviewed_reason"] == (
        "reviewed_rising_missed_submit_safety_backoff_source_quality_provenance"
    )


def test_observation_source_quality_audit_accepts_rising_missed_tp1_source_gap_relief(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-14",
        [
            _event(
                "rising_missed_tp1_source_gap_relief_applied",
                {
                    "metric_role": "bounded_tunable",
                    "decision_authority": (
                        "operator_runtime_override_rising_missed_tp1_source_gap_relief"
                    ),
                    "window_policy": "same_day_intraday_runtime_state",
                    "sample_floor": (
                        "fresh_tp1_support_reversal_with_three_supports_and_momentum"
                    ),
                    "primary_decision_metric": "post_relief_submit_and_tp1_first_hit_outcome",
                    "source_quality_gate": (
                        "fresh_tp1_contract_replaces_missing_legacy_weak_ai_micro_context"
                    ),
                    "runtime_effect": True,
                    "allowed_runtime_apply": True,
                    "forbidden_uses": "standalone_buy,submit_safety_bypass,broker_guard_bypass",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": False,
                    "threshold_family": "rising_missed_tp1_source_gap_relief",
                    "rising_missed_tp1_source_gap_relief_applied": True,
                    "rising_missed_tp1_source_gap_relief_support_count": 3,
                    "rising_missed_tp1_source_gap_relief_min_support_count": 3,
                    "rising_missed_tp1_source_gap_relief_support_momentum": True,
                    "rising_missed_tp1_source_gap_relief_trusted_ws_micro": True,
                    "rising_missed_tp1_source_gap_relief_evaluation_id": "eval-1",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-14")

    contract = report["stage_contracts"]["rising_missed_tp1_source_gap_relief_applied"]
    assert contract["status"] == "pass"
    assert contract["missing_violations"] == {}
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0


def test_observation_source_quality_audit_reviews_20260713_unknown_provenance_gaps(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common_entry_context = {
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "entry_order_flow_status": "unknown",
        "entry_context_quality": "partial",
        "entry_context_missing_features": "order_flow_pressure",
    }
    _write_events(
        tmp_path,
        "2026-07-13",
        [
            _event(
                "rising_missed_scout_quality_guard_blocked",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "operator_runtime_override_rising_missed_scout_quality_guard",
                    "runtime_effect": True,
                    "source_quality_gate": "rising_missed_scout_quality_context_present",
                    "rising_missed_submit_safety_backoff_reason": "source_quality_missing_or_unknown",
                },
                record_id=1,
            ),
            _event(
                "rising_missed_tick_speed_entry_block",
                {
                    **common_entry_context,
                    "decision_authority": "real_scalping_rising_missed_tick_speed_guard",
                    "runtime_effect": True,
                    "source_quality_gate": "rising_missed_tick_context_present",
                },
                record_id=2,
            ),
            _event(
                "rising_missed_tick_absolute_throughput_relief_applied",
                {
                    **common_entry_context,
                    "decision_authority": (
                        "operator_runtime_override_tick_absolute_throughput_relief"
                    ),
                    "runtime_effect": True,
                    "source_quality_gate": "rising_missed_tick_context_present",
                },
                record_id=5,
            ),
            _event(
                "order_bundle_failed",
                {
                    **common_entry_context,
                    "decision_authority": "real_scalping_submit_fail_closed",
                    "runtime_effect": False,
                    "source_quality_gate": "entry_context_source_quality",
                },
                record_id=6,
            ),
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "runtime_effect": False,
                    "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
                    "entry_action_final_block_reason": "source_quality_unknown",
                    "entry_action_final_reason": "source_quality_unknown",
                },
                record_id=4,
            ),
            _event(
                "stat_action_decision_snapshot",
                {
                    "decision_authority": "sim_observation_only",
                    "source_quality_gate": "stat_action_snapshot_source_only",
                    "tick_context_quality": "-",
                    "tick_latest_age_ms": "-",
                    "quote_age_source": "missing",
                    "quote_age_ms": "-",
                    "shallow_tick_context_stale": "unknown",
                    "shallow_quote_stale": "unknown",
                },
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-13")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = {
        item["stage"]: {field["field"]: field for field in item["fields"]}
        for item in report["reviewed_unknown_token_findings"]
    }
    assert (
        reviewed["rising_missed_scout_quality_guard_blocked"][
            "rising_missed_submit_safety_backoff_reason"
        ]["reviewed_reason"]
        == "reviewed_rising_missed_submit_safety_backoff_source_quality_provenance"
    )
    assert (
        reviewed["rising_missed_tick_speed_entry_block"]["entry_order_flow_status"][
            "reviewed_reason"
        ]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["rising_missed_tick_absolute_throughput_relief_applied"][
            "entry_order_flow_status"
        ]["reviewed_reason"]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["order_bundle_failed"]["entry_order_flow_status"][
            "reviewed_reason"
        ]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["scalp_entry_action_decision_snapshot"][
            "entry_action_final_block_reason"
        ]["reviewed_reason"]
        == "reviewed_entry_block_source_quality_unknown_provenance"
    )
    assert (
        reviewed["scalp_entry_action_decision_snapshot"]["entry_action_final_reason"][
            "reviewed_reason"
        ]
        == "reviewed_entry_block_source_quality_unknown_provenance"
    )
    assert (
        reviewed["stat_action_decision_snapshot"]["shallow_tick_context_stale"][
            "reviewed_reason"
        ]
        == "reviewed_shallow_stale_flag_not_available"
    )
    assert (
        reviewed["stat_action_decision_snapshot"]["shallow_quote_stale"][
            "reviewed_reason"
        ]
        == "reviewed_shallow_stale_flag_not_available"
    )


def test_observation_source_quality_audit_reviews_20260729_explicit_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    entry_context = {
        "entry_order_flow_status": "unknown",
        "entry_context_quality": "partial",
        "entry_context_missing_features": "order_flow_pressure",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-07-29",
        [
            _event(
                "rising_missed_async_commit_phase",
                {
                    **entry_context,
                    "decision_authority": "scanner_async_two_phase_commit_transport_only",
                    "runtime_effect": False,
                },
                record_id=1,
            ),
            _event(
                "rising_missed_tp1_candidate_deferred",
                {
                    **entry_context,
                    "decision_authority": (
                        "operator_runtime_override_rising_missed_tp1_candidate_selector"
                    ),
                    "runtime_effect": True,
                },
                record_id=2,
            ),
            _event(
                "reversal_add_blocked_reason",
                {
                    "shallow_tick_context_stale": "unknown",
                    "tick_latest_age_ms": "-",
                    "tick_context_quality": "-",
                    "shallow_quote_stale": "unknown",
                    "quote_age_ms": "-",
                    "quote_age_source": "missing",
                    "decision_authority": "scale_in_attribution_source_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=3,
            ),
            _event(
                "probe_continuation_deferred",
                {
                    "post_probe_direction_state": "UNKNOWN",
                    "post_probe_direction_reason": (
                        "post_probe_nxt_wait_fast_tape_required"
                    ),
                    "post_probe_continuation_action": "DEFER",
                    "decision_authority": (
                        "dynamic_entry_price_resolver_p1_post_probe"
                    ),
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
            _event(
                "scalping_scanner_ws_prewarm_selected",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_session_clock:outside_supported_session"
                    ),
                    "market_session_bucket": "outside_supported_session",
                    "decision_authority": (
                        "scanner_ws_prewarm_observation_only_no_entry_authority"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=5,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-29")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert (
        reviewed["rising_missed_async_commit_phase"]["entry_order_flow_status"]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["rising_missed_tp1_candidate_deferred"]["entry_order_flow_status"]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["reversal_add_blocked_reason"]["shallow_tick_context_stale"]
        == "reviewed_shallow_stale_flag_not_available"
    )
    assert (
        reviewed["reversal_add_blocked_reason"]["shallow_quote_stale"]
        == "reviewed_shallow_stale_flag_not_available"
    )
    assert (
        reviewed["probe_continuation_deferred"]["post_probe_direction_state"]
        == "reviewed_post_probe_direction_source_gap"
    )
    assert (
        reviewed["scalping_scanner_ws_prewarm_selected"]["venue"]
        == "reviewed_scanner_venue_fail_closed_provenance"
    )
    assert (
        reviewed["scalping_scanner_ws_prewarm_selected"]["effective_venue"]
        == "reviewed_scanner_venue_fail_closed_provenance"
    )


def test_observation_source_quality_audit_reviews_20260722_explicit_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-22",
        [
            _event(
                "budget_pass",
                {
                    "formula_version": "entry_type_5stage_cap25_v1",
                    "tier": 1,
                    "tier_reason": "unknown_venue_fallback",
                    "venue": "UNKNOWN",
                    "reference_time": "2026-07-22T10:00:00+09:00",
                },
                record_id=1,
            ),
            _event(
                "rising_missed_nxt_post_block_price_sample",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "source_only_nxt_post_block_price_observation",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_quality_gate": "fresh_absolute_nxt_ws_route_or_bounded_ka10004_receive_observation",
                    "rising_missed_nxt_post_block_selector_reason": "downstream_block:real_weak_ai_micro_entry_block:source_quality_unknown",
                    "rising_missed_nxt_post_block_source_block_reason": "source_quality_unknown",
                    "rising_missed_nxt_post_block_ws_0b_route": "unknown",
                    "rising_missed_nxt_post_block_ws_0d_route": "unknown",
                },
                record_id=2,
            ),
            _event(
                "probe_continuation_deferred",
                {
                    "decision_authority": "dynamic_entry_price_resolver_p1_post_probe",
                    "post_probe_direction_state": "UNKNOWN",
                    "post_probe_continuation_action": "DEFER",
                    "post_probe_direction_reason": "post_probe_direction_source_gap",
                    "post_probe_direction_group_count": 1,
                    "post_probe_directional_group_count": 1,
                    "allowed_runtime_apply": False,
                },
                record_id=3,
            ),
            _event(
                "probe_continuation_deferred",
                {
                    "decision_authority": "dynamic_entry_price_resolver_p1_post_probe",
                    "post_probe_direction_state": "UNKNOWN",
                    "post_probe_continuation_action": "DEFER",
                    "post_probe_direction_reason": (
                        "post_probe_wait_positive_confirmation_required"
                    ),
                    "post_probe_direction_group_count": 2,
                    "post_probe_directional_group_count": 1,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=6,
            ),
            _event(
                "scalp_trailing_continuation_recheck",
                {
                    "quote_recovery_large_sell_state": "unknown",
                    "quote_recovery_fetch_state": "not_requested",
                    "quote_recovery_candidate": False,
                    "quote_recovery_eligible": False,
                    "reversal_feature_context_usable": False,
                    "large_sell_print_detected": False,
                    "micro_source_trusted_ws": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
            _event(
                "entry_ai_price_canary_applied",
                {
                    "entry_order_flow_status": "unknown",
                    "entry_context_quality": "partial",
                    "entry_context_missing_features": "order_flow_pressure",
                },
                record_id=5,
            ),
            _event(
                "entry_ai_price_feature_packet_source_block",
                {
                    "entry_order_flow_status": "unknown",
                    "entry_context_quality": "stale",
                    "entry_context_missing_features": (
                        "quote_freshness,order_flow_pressure"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": (
                        "entry_price_input_source_quality_fail_closed"
                    ),
                    "runtime_effect": True,
                },
                record_id=7,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-22")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["budget_pass"]["venue"] == (
        "reviewed_explicit_sizing_unknown_venue_fallback"
    )
    assert (
        reviewed["rising_missed_nxt_post_block_price_sample"][
            "rising_missed_nxt_post_block_source_block_reason"
        ]
        == "reviewed_nxt_post_block_source_gap_provenance"
    )
    assert reviewed["probe_continuation_deferred"]["post_probe_direction_state"] == (
        "reviewed_post_probe_direction_source_gap"
    )
    assert (
        reviewed["scalp_trailing_continuation_recheck"][
            "quote_recovery_large_sell_state"
        ]
        == "reviewed_quote_recovery_large_sell_not_available"
    )
    assert reviewed["entry_ai_price_canary_applied"]["entry_order_flow_status"] == (
        "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["entry_ai_price_feature_packet_source_block"][
            "entry_order_flow_status"
        ]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "entry_ai_price_feature_packet_source_block",
            "entry_order_flow_status",
            "unknown",
            {
                "entry_context_quality": "stale",
                "entry_context_missing_features": "order_flow_pressure",
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
            },
        )
        is None
    )
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "order_bundle_failed",
            "entry_order_flow_status",
            "unknown",
            {
                "entry_context_quality": "stale",
                "entry_context_missing_features": "order_flow_pressure",
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
            },
        )
        is None
    )
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "order_bundle_failed",
            "entry_order_flow_status",
            "unknown",
            {
                "entry_context_quality": "stale",
                "entry_context_missing_features": "order_flow_pressure",
                "actual_order_submitted": False,
                "broker_order_forbidden": False,
                "broker_submission_reconciliation_required": True,
            },
        )
        is None
    )


def test_observation_source_quality_audit_reviews_new_provenance_unknown_contracts():
    cases = [
        (
            "budget_pass",
            "pre_submit_parent_ai_result_source",
            "unknown",
            {
                "pre_submit_parent_ai_action": "NOT_EVALUATED",
                "pre_submit_parent_ai_decision_trace_id": "-",
                "pre_submit_parent_ai_attempt_trace_id": "-",
                "pre_submit_parent_ai_lineage_status": "missing_ai_trace",
                "pre_submit_parent_ai_lineage_runtime_effect": False,
            },
            "reviewed_pre_submit_ai_not_evaluated",
        ),
        (
            "budget_pass",
            "pre_submit_parent_ai_result_source",
            "unknown",
            {
                "pre_submit_parent_ai_action": "NOT_EVALUATED",
                "pre_submit_parent_ai_decision_trace_id": "-",
                "pre_submit_parent_ai_attempt_trace_id": "attempt-1",
                "pre_submit_parent_ai_attempt_trusted": False,
                "pre_submit_parent_ai_source_fresh": False,
                "pre_submit_parent_ai_lineage_status": "missing_ai_trace",
                "pre_submit_parent_ai_lineage_runtime_effect": False,
            },
            "reviewed_pre_submit_ai_not_evaluated",
        ),
        (
            "rising_missed_tp1_candidate_blocked",
            "venue",
            "UNKNOWN",
            {
                "effective_venue": "UNKNOWN",
                "venue_resolution": (
                    "conflicting_explicit:venue,rising_missed_effective_venue"
                ),
                "rising_missed_effective_venue": "KRX",
                "actual_order_submitted": False,
            },
            "reviewed_rising_missed_explicit_venue_conflict",
        ),
        (
            "scalping_scanner_watch_budget_reallocated",
            "venue",
            "UNKNOWN",
            {
                "effective_venue": "UNKNOWN",
                "venue_resolution": "missing_tradable_explicit_venue",
                "decision_authority": "scanner_observation_budget_only",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "reviewed_scanner_budget_venue_not_available",
        ),
    ]
    for stage, key, value, normalized, expected in cases:
        assert (
            audit._reviewed_unknown_reason_for_stage_field(
                stage, key, value, normalized
            )
            == expected
        )


def test_observation_source_quality_audit_reviews_legacy_observation_only_unknowns(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-27",
        [
            _event(
                "budget_pass",
                {
                    "formula_version": "entry_type_5stage_cap25_v1",
                    "tier": 1,
                    "tier_reason": "unknown_venue_fallback",
                    "venue": "PREMARKET_KRX_LIKE",
                    "effective_venue": "PREMARKET_KRX_LIKE",
                    "reference_time": "2026-07-27T08:10:00+09:00",
                },
                record_id=1,
            ),
            _event(
                "rising_missed_watch_not_rising_skipped",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "NXT",
                    "venue_resolution": (
                        "rising_missed_initial_gate:session_explicit_conflict:"
                        "consistent_explicit:stock.effective_venue"
                    ),
                    "decision_authority": "rising_missed_watch_budget_fast_reject",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "scalping_scanner_watch_eviction",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_runtime_event:explicit_target_venue_missing"
                    ),
                    "decision_authority": (
                        "real_scalping_scanner_watch_eviction_pool_management_only"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=3,
            ),
            _event(
                "scalping_scanner_scheduler_generation_rejected",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": "scanner_scheduler_boot_promotion_ttl_expired",
                    "decision_authority": (
                        "scanner_runtime_scheduler_only_no_order_authority"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
            _event(
                "rising_missed_tp1_counterfactual_submit_safety",
                {
                    "rising_missed_ws_0d_route": "unknown",
                    "rising_missed_effective_venue": "KRX",
                    "rising_missed_nxt_observation_only": True,
                    "rising_missed_nxt_metric_role": "source_quality_gate",
                    "rising_missed_nxt_decision_authority": (
                        "observe_only_no_runtime_mutation"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=5,
            ),
            _event(
                "scalping_scanner_async_result_rejected",
                {
                    "scanner_async_transport_namespace": "unknown",
                    "scanner_async_result_status": "preparation_deadline_expired",
                    "decision_authority": "scanner_async_observation_only_reject",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=6,
            ),
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "latency_true_ofi_direct_canary_signed_tape_event_time_latest_side": (
                        "UNKNOWN"
                    ),
                    "entry_action_final_block_reason": "tick_window_span_sec_ge_60",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=7,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-27")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["budget_pass"]["tier_reason"] == (
        "reviewed_explicit_sizing_unknown_venue_fallback"
    )
    assert reviewed["rising_missed_watch_not_rising_skipped"]["venue"] == (
        "reviewed_observation_only_venue_not_available"
    )
    assert reviewed["scalping_scanner_watch_eviction"]["effective_venue"] == (
        "reviewed_observation_only_venue_not_available"
    )
    assert reviewed["scalping_scanner_scheduler_generation_rejected"]["venue"] == (
        "reviewed_scanner_venue_fail_closed_provenance"
    )
    assert (
        reviewed["rising_missed_tp1_counterfactual_submit_safety"][
            "rising_missed_ws_0d_route"
        ]
        == "reviewed_rising_missed_ws_route_not_available"
    )
    assert (
        reviewed["scalping_scanner_async_result_rejected"][
            "scanner_async_transport_namespace"
        ]
        == "reviewed_scanner_async_transport_not_available"
    )
    assert (
        reviewed["scalp_entry_action_decision_snapshot"][
            "latency_true_ofi_direct_canary_signed_tape_event_time_latest_side"
        ]
        == "reviewed_signed_tape_event_side_not_available"
    )


def test_observation_source_quality_audit_reviews_20260724_fail_closed_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    order_forbidden = {
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-07-24",
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                {
                    **order_forbidden,
                    "decision_authority": (
                        "real_scalping_scanner_runtime_watchlist_handoff_only"
                    ),
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": "missing_tradable_explicit_venue",
                },
                record_id=1,
            ),
            _event(
                "scalping_scanner_watching_runtime_skip",
                {
                    **order_forbidden,
                    "decision_authority": (
                        "real_scalping_scanner_runtime_watchlist_observation_only"
                    ),
                    "scanner_observed_venue": "UNKNOWN",
                    "scanner_observed_venue_resolution": (
                        "missing_tradable_explicit_venue"
                    ),
                },
                record_id=7,
            ),
            _event(
                "scalp_fast_exit_quote_blocked",
                {
                    **order_forbidden,
                    "fast_exit_ws_0d_route": "unknown",
                    "fast_exit_rest_nxt_route_ready": True,
                    "fast_exit_route_guard_reason": "nxt_rest_route_proven",
                },
                record_id=2,
            ),
            _event(
                "ai_holding_review",
                {
                    "holding_context_ws_route": "unknown",
                    "holding_context_ai_market_snapshot": {
                        "market_data_route": "unknown",
                    },
                    "holding_context_source_quality_status": "blocked",
                    "holding_context_blockers": ["ai_preflight:bbo_unknown_age"],
                    "ai_result_source": "input_preflight_blocked",
                },
                record_id=3,
            ),
            _event(
                "holding_flow_override_review",
                {
                    "flow_state": "unknown_flow_state",
                    "flow_score": 0,
                },
                record_id=4,
            ),
            _event(
                "probe_filled",
                {
                    "probe_confirmation_last_state": "UNKNOWN",
                    "probe_confirmation_count": 0,
                    "decision_authority": (
                        "dynamic_entry_price_resolver_p1_post_probe"
                    ),
                    "allowed_runtime_apply": False,
                },
                record_id=5,
            ),
            _event(
                "probe_continuation_deferred",
                {
                    **order_forbidden,
                    "post_probe_direction_state": "UNKNOWN",
                    "post_probe_continuation_action": "DEFER",
                    "post_probe_direction_reason": (
                        "post_probe_stale_wait_positive_confirmation_required"
                    ),
                    "post_probe_direction_group_count": 2,
                    "post_probe_directional_group_count": 1,
                    "decision_authority": (
                        "dynamic_entry_price_resolver_p1_post_probe"
                    ),
                    "allowed_runtime_apply": False,
                },
                record_id=6,
            ),
            _event(
                "scalp_fast_exit_quote_blocked",
                {
                    **order_forbidden,
                    "fast_exit_ws_0d_route": "unknown",
                    "fast_exit_rest_nxt_route_ready": False,
                    "fast_exit_route_guard_reason": (
                        "nxt_executable_quote_route_unproven"
                    ),
                    "rest_check_state": "timeout",
                },
                record_id=8,
            ),
            _event(
                "scalp_trailing_continuation_recheck",
                {
                    **order_forbidden,
                    "quote_recovery_large_sell_state": "unknown",
                    "quote_recovery_fetch_state": "timeout",
                    "quote_recovery_candidate": True,
                    "quote_recovery_eligible": False,
                    "reversal_feature_context_usable": False,
                    "large_sell_print_detected": False,
                },
                record_id=9,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-24")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["scalping_scanner_runtime_target_attach"]["venue"] == (
        "reviewed_scanner_venue_fail_closed_provenance"
    )
    assert (
        reviewed["scalping_scanner_watching_runtime_skip"]["scanner_observed_venue"]
        == "reviewed_scanner_venue_fail_closed_provenance"
    )
    assert reviewed["scalp_fast_exit_quote_blocked"]["fast_exit_ws_0d_route"] == (
        "reviewed_legacy_fast_exit_route_provenance"
    )
    assert reviewed["ai_holding_review"]["holding_context_ws_route"] == (
        "reviewed_holding_input_preflight_blocked_provenance"
    )
    assert reviewed["holding_flow_override_review"]["flow_state"] == (
        "reviewed_canonical_unknown_flow_state"
    )
    assert reviewed["probe_filled"]["probe_confirmation_last_state"] == (
        "reviewed_probe_confirmation_not_evaluated"
    )
    assert reviewed["probe_continuation_deferred"]["post_probe_direction_state"] == (
        "reviewed_post_probe_direction_source_gap"
    )
    assert (
        reviewed["scalp_trailing_continuation_recheck"][
            "quote_recovery_large_sell_state"
        ]
        == "reviewed_quote_recovery_large_sell_not_available"
    )


def test_observation_source_quality_audit_does_not_review_unproven_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-22",
        [
            _event(
                "budget_pass",
                {
                    "formula_version": "entry_type_5stage_cap25_v1",
                    "tier": 1,
                    "tier_reason": "unknown_venue_fallback",
                    "venue": "UNKNOWN",
                    "reference_time": "missing",
                },
                record_id=1,
            ),
            _event(
                "rising_missed_nxt_post_block_price_sample",
                {
                    "decision_authority": "source_only_nxt_post_block_price_observation",
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "rising_missed_nxt_post_block_selector_reason": "downstream_block:source_quality_unknown",
                    "rising_missed_nxt_post_block_source_block_reason": "source_quality_unknown",
                },
                record_id=2,
            ),
            _event(
                "probe_continuation_deferred",
                {
                    "decision_authority": "dynamic_entry_price_resolver_p1_post_probe",
                    "post_probe_direction_state": "UNKNOWN",
                    "post_probe_continuation_action": "DEFER",
                    "post_probe_direction_reason": "post_probe_direction_source_gap",
                    "post_probe_direction_group_count": 2,
                    "post_probe_directional_group_count": 2,
                    "allowed_runtime_apply": False,
                },
                record_id=3,
            ),
            _event(
                "scalp_trailing_continuation_recheck",
                {
                    "quote_recovery_large_sell_state": "unknown",
                    "quote_recovery_fetch_state": "not_requested",
                    "quote_recovery_candidate": True,
                    "quote_recovery_eligible": False,
                    "reversal_feature_context_usable": False,
                    "large_sell_print_detected": False,
                    "micro_source_trusted_ws": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-22")

    assert {item["stage"] for item in report["unknown_token_findings"]} == {
        "budget_pass",
        "probe_continuation_deferred",
        "rising_missed_nxt_post_block_price_sample",
        "scalp_trailing_continuation_recheck",
    }


def test_observation_source_quality_audit_reviews_explicit_fail_closed_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-23",
        [
            _event(
                "reversal_add_blocked_reason",
                _reversal_add_blocked_fields(state="reversal_state_unknown"),
                record_id=1,
            ),
            _event(
                "probe_continuation_deferred",
                {
                    "decision_authority": "dynamic_entry_price_resolver_p1_post_probe",
                    "post_probe_direction_state": "UNKNOWN",
                    "post_probe_continuation_action": "DEFER",
                    "post_probe_direction_reason": "post_probe_ai_action_not_fresh",
                    "post_probe_direction_group_count": 2,
                    "post_probe_directional_group_count": 2,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "scalp_trailing_continuation_recheck",
                {
                    "quote_recovery_large_sell_state": "unknown",
                    "quote_recovery_fetch_state": "ok",
                    "quote_recovery_candidate": True,
                    "quote_recovery_eligible": True,
                    "reversal_feature_context_usable": False,
                    "large_sell_print_detected": False,
                    "micro_source_trusted_ws": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=3,
            ),
            _event(
                "scalp_fast_exit_quote_blocked",
                {
                    "fast_exit_route_resolution_reason": (
                        "nxt_session_nxt_enabled_or_unknown"
                    ),
                    "fast_exit_execution_cohort": "UNKNOWN",
                    "fast_exit_broker_route": "NXT",
                    "fast_exit_nxt_enabled": True,
                    "fast_exit_nxt_flag_source": "daily_stock_quotes.is_nxt",
                    "fast_exit_route_guard_reason": "nxt_ws_route_proven",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["reversal_add_blocked_reason"]["state"] == (
        "reviewed_reversal_state_not_initialized"
    )
    assert reviewed["probe_continuation_deferred"]["post_probe_direction_state"] == (
        "reviewed_post_probe_direction_source_gap"
    )
    assert (
        reviewed["scalp_trailing_continuation_recheck"][
            "quote_recovery_large_sell_state"
        ]
        == "reviewed_quote_recovery_large_sell_not_available"
    )
    assert (
        reviewed["scalp_fast_exit_quote_blocked"]["fast_exit_route_resolution_reason"]
        == "reviewed_legacy_fast_exit_route_provenance"
    )
    assert (
        reviewed["scalp_fast_exit_quote_blocked"]["fast_exit_execution_cohort"]
        == "reviewed_legacy_fast_exit_route_provenance"
    )


def test_observation_source_quality_audit_reviews_unknown_fill_quality_without_requested_qty(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-12",
        [
            _event(
                "position_rebased_after_fill",
                {
                    "metric_role": "execution_quality_real_only",
                    "decision_authority": "broker_receipt_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                    "requested_qty": 0,
                    "fill_quality": "UNKNOWN",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-12")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed = report["reviewed_unknown_token_findings"][0]
    assert reviewed["stage"] == "position_rebased_after_fill"
    assert reviewed["fields"][0]["field"] == "fill_quality"
    assert (
        reviewed["fields"][0]["reviewed_reason"]
        == "reviewed_fill_quality_pre_contract_no_requested_qty"
    )


def test_observation_source_quality_audit_warns_on_unknown_fill_quality_with_missing_requested_qty(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-12",
        [
            _event(
                "position_rebased_after_fill",
                {
                    "metric_role": "execution_quality_real_only",
                    "decision_authority": "broker_receipt_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                    "fill_quality": "UNKNOWN",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-12")

    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 0
    finding = report["unknown_token_findings"][0]
    assert finding["stage"] == "position_rebased_after_fill"
    assert finding["fields"][0]["field"] == "fill_quality"


def test_observation_source_quality_audit_warns_on_top_level_and_all_unknown_fields(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {f"custom_unknown_field_{idx}": "value_unknown" for idx in range(25)}
    rows = [
        {
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "stage": "unknown_custom_stage",
            "stock_name": "TEST",
            "stock_code": "123456",
            "record_id": 1,
            "fields": fields,
            "emitted_at": "2026-06-04T10:00:00",
            "emitted_date": "2026-06-04",
        }
    ]
    _write_events(tmp_path, "2026-06-04", rows)

    report = audit.build_observation_source_quality_audit("2026-06-04")

    finding = report["unknown_token_findings"][0]
    found_fields = {item["field"] for item in finding["fields"]}
    assert "__stage" in found_fields
    for idx in range(25):
        assert f"custom_unknown_field_{idx}" in found_fields


def test_observation_source_quality_audit_has_entry_micro_context_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "swing_entry_micro_context_observed",
                {
                    "orderbook_micro_ready": False,
                    "orderbook_micro_state": "insufficient",
                    "orderbook_micro_reason": "missing_snapshot",
                    "orderbook_micro_snapshot_age_ms": 0,
                    "orderbook_micro_observer_healthy": False,
                    "swing_micro_runtime_effect": False,
                    "swing_micro_observe_only": True,
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["swing_entry_micro_context_observed"]
    assert contract["status"] == "pass"
    assert contract["decision_authority"] == "source_quality_only"
    assert contract["runtime_effect"] is False


def test_observation_source_quality_audit_accepts_high_volume_contract_labels(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "strength_momentum_observed",
                {
                    "reason": "below_strength_base",
                    "metric_role": "ops_volume_diagnostic",
                    "decision_authority": "source_quality_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []


def test_observation_source_quality_audit_accepts_order_failure_diagnostic_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "order_bundle_failed",
                {"reason": "broker_receipt_missing"},
                record_id=idx,
            )
            for idx in range(60)
        ]
        + [
            _event("order_leg_fail", {"reason": "leg_rejected"}, record_id=idx + 100)
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    assert report["field_presence_top"]["order_bundle_failed"]["metric_role"] == 60
    assert report["field_presence_top"]["order_leg_fail"]["metric_role"] == 60


def test_observation_source_quality_audit_enforces_sim_authority_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_sim_duplicate_buy_signal",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_observation_only",
                    "sim_record_id": "SIM-1",
                    "threshold_family": "entry_mechanical_momentum",
                    "sim_parent_record_id": 101,
                },
            ),
            _event(
                "swing_probe_discarded",
                {
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "in_memory_probe_only",
                    "evidence_quality": "quota_observation",
                    "source_record_id": "SRC-1",
                    "probe_origin_stage": "blocked_swing_score_vpw",
                    "discard_reason": "max_per_symbol_reached",
                    "blocker_authority": "probe_capacity_only",
                    "quota_observation_scope": "symbol_probe_quota",
                    "allowed_runtime_apply": False,
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert (
        report["stage_contracts"]["scalp_sim_duplicate_buy_signal"]["status"]
        == "warning"
    )
    assert (
        report["stage_contracts"]["scalp_sim_duplicate_buy_signal"][
            "missing_violations"
        ]["runtime_effect"]
        == 1.0
    )
    assert report["stage_contracts"]["swing_probe_discarded"]["status"] == "warning"
    assert (
        report["stage_contracts"]["swing_probe_discarded"]["missing_violations"][
            "decision_authority"
        ]
        == 1.0
    )


def test_observation_source_quality_audit_accepts_complete_sim_authority_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_sim_duplicate_buy_signal",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "sim_observation_skipped",
                    "decision_authority": "sim_observation_only",
                    "sim_record_id": "SIM-1",
                    "threshold_family": "entry_mechanical_momentum",
                    "sim_parent_record_id": 101,
                },
            ),
            _event(
                "scalp_sim_entry_submit_revalidation_warning",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "sim_entry_pre_submit_warning_only",
                    "decision_authority": "sim_observation_only",
                    "sim_record_id": "SIM-2",
                    "threshold_family": "pre_submit_price_guard",
                    "sim_parent_record_id": 102,
                    "entry_submit_revalidation_warning": "stale_context_or_quote",
                    "quote_age_at_submit_ms": 1500,
                    "submitted_order_price": 10000,
                    "mark_price_at_submit": 9990,
                },
                record_id=2,
            ),
            _event(
                "swing_probe_discarded",
                {
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "in_memory_probe_only",
                    "decision_authority": "swing_sim_exploration_only",
                    "evidence_quality": "quota_observation",
                    "source_record_id": "SRC-1",
                    "probe_origin_stage": "blocked_swing_score_vpw",
                    "discard_reason": "max_per_symbol_reached",
                    "blocker_authority": "probe_capacity_only",
                    "quota_observation_scope": "symbol_probe_quota",
                    "allowed_runtime_apply": False,
                },
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert (
        report["stage_contracts"]["scalp_sim_duplicate_buy_signal"]["status"] == "pass"
    )
    assert (
        report["stage_contracts"]["scalp_sim_entry_submit_revalidation_warning"][
            "status"
        ]
        == "pass"
    )
    assert report["stage_contracts"]["swing_probe_discarded"]["status"] == "pass"


def test_observation_source_quality_audit_accepts_score65_74_recovery_probe_block_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "score65_74_recovery_probe_blocked",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "score65_74_recovery_probe_block_observation_only",
                    "window_policy": "same_day_intraday_events",
                    "sample_floor": 1,
                    "primary_decision_metric": "source_quality_gate",
                    "source_quality_gate": "score65_74_recovery_probe_block_contract_fields_present",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "threshold_family": "score65_74_recovery_probe",
                    "score65_74_recovery_probe_skip_reason": "tick_accel_below_min",
                    "ai_score": "62.0",
                    "buy_pressure": "70.0",
                    "tick_accel": "0.900",
                    "micro_vwap_bp": "2.00",
                    "tick_aggressor_trusted_count": 3,
                    "tick_aggressor_pressure_usable": True,
                    "micro_vwap_available": True,
                    "minute_candle_context_quality": "fresh_bar_window",
                    "minute_candle_window_fresh": True,
                    "minute_candle_latest_age_ms": 12000,
                    "score65_74_recovery_probe_min_buy_pressure": "65.00",
                    "score65_74_recovery_probe_min_tick_accel": "1.200",
                    "score65_74_recovery_probe_min_micro_vwap_bp": "0.00",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert (
        report["stage_contracts"]["score65_74_recovery_probe_blocked"]["status"]
        == "pass"
    )
    assert report["status"] == "pass"


def test_observation_source_quality_audit_accepts_explicit_fail_closed_probe_source_gap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "metric_role": "source_quality_gate",
        "decision_authority": "score65_74_recovery_probe_block_observation_only",
        "window_policy": "same_day_intraday_events",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_gate",
        "source_quality_gate": "score65_74_recovery_probe_block_contract_fields_present",
        "runtime_effect": False,
        "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "threshold_family": "score65_74_recovery_probe",
        "score65_74_recovery_probe_skip_reason": "source_quality_hard_block",
        "ai_score": "62.0",
        "buy_pressure": "50.0",
        "tick_accel": "0.0",
        "micro_vwap_bp": "2.0",
        "tick_aggressor_trusted_count": 0,
        "tick_aggressor_pressure_usable": False,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 12000,
        "score65_74_recovery_probe_min_buy_pressure": "65.0",
        "score65_74_recovery_probe_min_tick_accel": "1.2",
        "score65_74_recovery_probe_min_micro_vwap_bp": "0.0",
    }
    _write_events(
        tmp_path,
        "2026-07-23",
        [_event("score65_74_recovery_probe_blocked", fields)],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    contract = report["stage_contracts"]["score65_74_recovery_probe_blocked"]
    assert contract["status"] == "pass"
    assert (
        "tick_aggressor_pressure_usable_contract"
        not in contract["invalid_label_violations"]
    )


def test_observation_source_quality_audit_accepts_observed_zero_distance_from_high(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "tick_source_quality_fields_sent": True,
        "tick_accel_source": "computed_10ticks",
        "tick_context_quality": "fresh_computed",
        "quote_age_source": "ws_realtime_quote",
        "latest_strength": "105.0",
        "buy_pressure_10t": "70.0",
        "distance_from_day_high_pct": "0.000",
        "distance_from_day_high_pct_observation_state": "observed_ws_high",
        "intraday_range_pct": "2.500",
    }
    _write_events(
        tmp_path,
        "2026-07-23",
        [_event("blocked_ai_score", fields)],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    contract = report["stage_contracts"]["blocked_ai_score"]
    assert contract["status"] == "pass"
    assert contract["zero_rates"]["distance_from_day_high_pct"] == 0.0


def test_observation_source_quality_audit_accepts_score65_74_recovery_probe_success_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "tick_source_quality_fields_sent": True,
        "tick_accel_source": "computed_10ticks",
        "tick_context_quality": "fresh_computed",
        "quote_age_source": "ws_realtime_quote",
        "metric_role": "bounded_tunable",
        "decision_authority": "score65_74_recovery_probe_entry_unlock_only",
        "window_policy": "same_day_intraday_events",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_gate",
        "source_quality_gate": "score65_74_recovery_probe_contract_fields_present",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": (
            "runtime_threshold_apply/order_submit/provider_route_change/"
            "bot_restart/score_threshold_change/broker_guard_bypass/stale_submit_bypass"
        ),
        "threshold_family": "score65_74_recovery_probe",
        "ai_score": "74.0",
        "buy_pressure": "88.14",
        "tick_accel": "1.200",
        "micro_vwap_bp": "74.95",
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 12000,
        "score65_74_recovery_probe_min_buy_pressure": "70.00",
        "score65_74_recovery_probe_min_tick_accel": "1.100",
        "score65_74_recovery_probe_min_micro_vwap_bp": "0.00",
    }
    _write_events(tmp_path, "2026-06-15", [_event("score65_74_recovery_probe", fields)])

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert report["stage_contracts"]["score65_74_recovery_probe"]["status"] == "pass"
    assert report["status"] == "pass"


def test_observation_source_quality_audit_blocks_score65_74_probe_without_trusted_pressure(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "tick_source_quality_fields_sent": True,
        "tick_accel_source": "computed_10ticks",
        "tick_context_quality": "fresh_computed",
        "quote_age_source": "ws_realtime_quote",
        "metric_role": "bounded_tunable",
        "decision_authority": "score65_74_recovery_probe_entry_unlock_only",
        "window_policy": "same_day_intraday_events",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_gate",
        "source_quality_gate": "score65_74_recovery_probe_contract_fields_present",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": (
            "runtime_threshold_apply/order_submit/provider_route_change/"
            "bot_restart/score_threshold_change/broker_guard_bypass/stale_submit_bypass"
        ),
        "threshold_family": "score65_74_recovery_probe",
        "ai_score": "74.0",
        "buy_pressure": "88.14",
        "tick_accel": "1.200",
        "micro_vwap_bp": "74.95",
        "tick_aggressor_trusted_count": 0,
        "tick_aggressor_pressure_usable": False,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 12000,
        "score65_74_recovery_probe_min_buy_pressure": "70.00",
        "score65_74_recovery_probe_min_tick_accel": "1.100",
        "score65_74_recovery_probe_min_micro_vwap_bp": "0.00",
    }
    _write_events(tmp_path, "2026-06-15", [_event("score65_74_recovery_probe", fields)])

    report = audit.build_observation_source_quality_audit("2026-06-15")

    contract = report["stage_contracts"]["score65_74_recovery_probe"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["tick_aggressor_pressure_usable_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "score65_74_recovery_probe"
    assert exclusion["invalid_fields"] == ["tick_aggressor_pressure_usable_contract"]


def test_observation_source_quality_audit_blocks_score65_74_probe_without_micro_vwap_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "tick_source_quality_fields_sent": True,
        "tick_accel_source": "computed_10ticks",
        "tick_context_quality": "fresh_computed",
        "quote_age_source": "ws_realtime_quote",
        "metric_role": "bounded_tunable",
        "decision_authority": "score65_74_recovery_probe_entry_unlock_only",
        "window_policy": "same_day_intraday_events",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_gate",
        "source_quality_gate": "score65_74_recovery_probe_contract_fields_present",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": (
            "runtime_threshold_apply/order_submit/provider_route_change/"
            "bot_restart/score_threshold_change/broker_guard_bypass/stale_submit_bypass"
        ),
        "threshold_family": "score65_74_recovery_probe",
        "ai_score": "74.0",
        "buy_pressure": "88.14",
        "tick_accel": "1.200",
        "micro_vwap_bp": "74.95",
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "score65_74_recovery_probe_min_buy_pressure": "70.00",
        "score65_74_recovery_probe_min_tick_accel": "1.100",
        "score65_74_recovery_probe_min_micro_vwap_bp": "0.00",
    }
    _write_events(tmp_path, "2026-06-15", [_event("score65_74_recovery_probe", fields)])

    report = audit.build_observation_source_quality_audit("2026-06-15")

    contract = report["stage_contracts"]["score65_74_recovery_probe"]
    assert contract["status"] == "fail"
    assert contract["missing_violations"]["micro_vwap_available"] == 1.0
    assert contract["missing_violations"]["minute_candle_window_fresh"] == 1.0
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "score65_74_recovery_probe"
    assert "minute_candle_window_fresh_contract" in exclusion["invalid_fields"]


def test_observation_source_quality_audit_blocks_zero_micro_vwap_when_unavailable(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "tick_source_quality_fields_sent": True,
        "tick_accel_source": "computed_10ticks",
        "tick_context_quality": "fresh_computed",
        "quote_age_source": "ws_realtime_quote",
        "metric_role": "bounded_tunable",
        "decision_authority": "score65_74_recovery_probe_entry_unlock_only",
        "window_policy": "same_day_intraday_events",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_gate",
        "source_quality_gate": "score65_74_recovery_probe_contract_fields_present",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        "threshold_family": "score65_74_recovery_probe",
        "ai_score": "74.0",
        "buy_pressure": "88.14",
        "tick_accel": "1.200",
        "micro_vwap_bp": "0.0",
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "micro_vwap_available": False,
        "minute_candle_context_quality": "missing_candles",
        "minute_candle_window_fresh": False,
        "minute_candle_latest_age_ms": "not_evaluated",
        "score65_74_recovery_probe_min_buy_pressure": "70.00",
        "score65_74_recovery_probe_min_tick_accel": "1.100",
        "score65_74_recovery_probe_min_micro_vwap_bp": "0.00",
    }
    _write_events(
        tmp_path,
        "2026-07-23",
        [_event("score65_74_recovery_probe", fields)],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    contract = report["stage_contracts"]["score65_74_recovery_probe"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )


def test_observation_source_quality_audit_flags_score65_74_recovery_probe_success_contract_gap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "score65_74_recovery_probe",
                {
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "computed_10ticks",
                    "tick_context_quality": "fresh_computed",
                    "quote_age_source": "ws_realtime_quote",
                    "metric_role": "bounded_tunable",
                    "window_policy": "same_day_intraday_events",
                    "sample_floor": 1,
                    "primary_decision_metric": "source_quality_gate",
                    "source_quality_gate": "score65_74_recovery_probe_contract_fields_present",
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "threshold_family": "score65_74_recovery_probe",
                    "ai_score": "74.0",
                    "buy_pressure": "88.14",
                    "tick_accel": "1.200",
                    "micro_vwap_bp": "74.95",
                    "score65_74_recovery_probe_min_buy_pressure": "70.00",
                    "score65_74_recovery_probe_min_tick_accel": "1.100",
                    "score65_74_recovery_probe_min_micro_vwap_bp": "0.00",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    contract = report["stage_contracts"]["score65_74_recovery_probe"]
    assert contract["status"] == "fail"
    assert contract["missing_violations"]["decision_authority"] == 1.0
    assert contract["missing_violations"]["broker_order_forbidden"] == 1.0
    assert contract["missing_violations"]["tick_aggressor_trusted_count"] == 1.0
    assert contract["missing_violations"]["tick_aggressor_pressure_usable"] == 1.0
    assert contract["missing_violations"]["micro_vwap_available"] == 1.0
    assert contract["missing_violations"]["minute_candle_window_fresh"] == 1.0
    assert (
        contract["invalid_label_violations"]["tick_aggressor_pressure_usable_contract"]
        == 1.0
    )
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False


def _pyramid_blocked_fields(**overrides):
    fields = {
        "scale_in_arm": "PYRAMID",
        "scale_in_blocker_namespace": "PYRAMID_QUALITY_GATE",
        "scale_in_blocker_reason": "buy_pressure_not_enough",
        "blocked_reason": "buy_pressure_not_enough",
        "gate_reason": "buy_pressure_not_enough",
        "profit_rate": "+1.20",
        "peak_profit": "+1.45",
        "ai_score": "72",
        "ai_score_source": "live",
        "held_sec": 95,
        "buy_pressure_10t": "61.5",
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "tick_acceleration_ratio": "0.80",
        "curr_vs_micro_vwap_bp": "42.0",
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 12000,
        "min_profit_pct": "1.10",
        "min_ai_score": "70",
        "min_buy_pressure": "60",
        "min_tick_accel": "0.50",
        "max_micro_vwap_bps": "60",
        "metric_role": "funnel_count",
        "decision_authority": "scale_in_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_quality_gate": "scale_in_arm_and_blocker_namespace_present",
        "forbidden_uses": "real_scale_in_submit|intraday_threshold_mutation|cap_release",
    }
    fields.update(overrides)
    return fields


def test_observation_source_quality_audit_accepts_pyramid_blocked_reason_pressure_contract(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [_event("pyramid_blocked_reason", _pyramid_blocked_fields())],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert report["stage_contracts"]["pyramid_blocked_reason"]["status"] == "pass"
    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["hard_blocking_excluded_row_count"] == 0


def test_observation_source_quality_audit_blocks_pyramid_pressure_without_trusted_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "pyramid_blocked_reason",
                _pyramid_blocked_fields(
                    tick_aggressor_trusted_count=0,
                    tick_aggressor_pressure_usable=False,
                ),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    contract = report["stage_contracts"]["pyramid_blocked_reason"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["tick_aggressor_pressure_usable_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    assert report["summary"]["hard_blocking_excluded_row_count"] == 1
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "pyramid_blocked_reason"
    assert exclusion["invalid_fields"] == ["tick_aggressor_pressure_usable_contract"]
    assert "invalid_label" in exclusion["exclusion_reasons"]


def test_observation_source_quality_audit_accepts_fail_closed_pyramid_source_gap(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-23",
        [
            _event(
                "pyramid_blocked_reason",
                _pyramid_blocked_fields(
                    tick_aggressor_trusted_count=0,
                    tick_aggressor_pressure_usable=False,
                    tick_pressure_evaluation_state="unavailable_fail_closed",
                    reversal_feature_source_quality="stale",
                    reversal_feature_stale_reason="tick_aggressor_pressure_unusable",
                ),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    contract = report["stage_contracts"]["pyramid_blocked_reason"]
    assert contract["status"] == "pass"
    assert (
        "tick_aggressor_pressure_usable_contract"
        not in contract["invalid_label_violations"]
    )


def test_observation_source_quality_audit_blocks_pyramid_micro_vwap_without_fresh_candle_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "pyramid_blocked_reason",
                _pyramid_blocked_fields(
                    micro_vwap_available=False,
                    minute_candle_context_quality="stale_bar_window",
                    minute_candle_window_fresh=False,
                    minute_candle_latest_age_ms=600000,
                ),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    contract = report["stage_contracts"]["pyramid_blocked_reason"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "pyramid_blocked_reason"
    assert exclusion["invalid_fields"] == ["minute_candle_window_fresh_contract"]


def test_observation_source_quality_audit_blocks_fresh_candle_without_numeric_age(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-23",
        [
            _event(
                "pyramid_blocked_reason",
                _pyramid_blocked_fields(
                    minute_candle_latest_age_ms="not_evaluated_missing_candle_age"
                ),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-23")

    contract = report["stage_contracts"]["pyramid_blocked_reason"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )


def _reversal_add_blocked_fields(**overrides):
    fields = {
        "state": "REVERSAL_CANDIDATE",
        "scale_in_arm": "AVG_DOWN",
        "scale_in_blocker_namespace": "AVG_DOWN_REVERSAL_ADD",
        "scale_in_blocker_reason": "supply_conditions_not_met(2/4)",
        "blocked_reason": "supply_conditions_not_met(2/4)",
        "profit_rate": "-0.32",
        "ai_score": "65",
        "current_ai_score": 65,
        "ai_score_source": "live",
        "buy_pressure_10t": "58.0",
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "tick_acceleration_ratio": "0.80",
        "curr_vs_micro_vwap_bp": "-2.0",
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 12000,
        "supply_pass_count": 2,
        "reversal_feature_source_quality": "usable",
        "reversal_feature_stale_reason": "-",
        "metric_role": "funnel_count",
        "decision_authority": "scale_in_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_quality_gate": "avg_down_reversal_features_and_blocker_present",
        "forbidden_uses": "real_scale_in_submit|intraday_threshold_mutation|broker_guard_bypass|cap_release",
    }
    fields.update(overrides)
    return fields


def test_observation_source_quality_audit_accepts_reversal_add_blocked_pressure_contract(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event("reversal_add_blocked_reason", _reversal_add_blocked_fields()),
            _event(
                "reversal_add_gate_blocked",
                _reversal_add_blocked_fields(
                    gate_reason="scale_in_cooldown",
                    scale_in_blocker_reason="scale_in_cooldown",
                    blocked_reason="scale_in_cooldown",
                ),
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert report["stage_contracts"]["reversal_add_blocked_reason"]["status"] == "pass"
    assert report["stage_contracts"]["reversal_add_gate_blocked"]["status"] == "pass"
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_accepts_shallow_source_gap_recheck_contract(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-15",
        [
            _event(
                "shallow_source_gap_recheck",
                {
                    "threshold_family": "shallow_avg_down_source_gap_recheck",
                    "recheck_state": "recovered",
                    "metric_role": "bounded_tunable",
                    "decision_authority": "bounded_shallow_avg_down_recheck_runtime",
                    "window_policy": "same_position_10_to_20_second_recheck",
                    "sample_floor": "one_source_gap_candidate_with_fresh_recovery",
                    "primary_decision_metric": "rebound_with_trusted_ws_micro_before_ttl",
                    "source_quality_gate": "fresh_quote_and_trusted_signed_ws_micro_required",
                    "runtime_effect": True,
                    "allowed_runtime_apply": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": False,
                    "forbidden_uses": (
                        "stale_or_unknown_pressure_as_positive|rest_positive_micro|"
                        "hard_safety_bypass"
                    ),
                    "recheck_enabled": True,
                    "recheck_active": True,
                    "recheck_active_date": "2026-07-15",
                    "recheck_current_date": "2026-07-15",
                    "recheck_observed_at": 1_784_077_200.0,
                    "recheck_max_quote_age_ms": 1500.0,
                    "recheck_max_ws_micro_age_ms": 3000.0,
                    "recheck_min_trusted_ticks": 3,
                    "quote_fresh": True,
                    "quote_age_ms": 420.0,
                    "quote_age_source": "absolute_timestamp:last_ws_update_ts",
                    "reversal_feature_consumption_age_basis": (
                        "feature_extracted_at_plus_snapshot_age"
                    ),
                    "reversal_feature_consumption_elapsed_ms": 200.0,
                    "tick_aggressor_pressure_usable": True,
                    "tick_aggressor_trusted_count": 5,
                    "tick_aggressor_source": "kiwoom_0b_signed_trade_volume",
                    "trusted_ws_micro_latest_age_ms": 180.0,
                    "buy_pressure_10t": 72.0,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    assert report["stage_contracts"]["shallow_source_gap_recheck"]["status"] == "pass"
    reviewed = {
        item["stage"]: {field["field"]: field for field in item["fields"]}
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["shallow_source_gap_recheck"]["forbidden_uses"][
        "reviewed_reason"
    ] == ("reviewed_forbidden_uses_unknown_literal_not_source_value")
    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_accepts_shallow_recheck_armed_without_micro(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-15",
        [
            _event(
                "shallow_source_gap_recheck",
                {
                    "threshold_family": "shallow_avg_down_source_gap_recheck",
                    "recheck_state": "armed",
                    "metric_role": "bounded_tunable",
                    "decision_authority": "bounded_shallow_avg_down_recheck_runtime",
                    "window_policy": "same_position_10_to_20_second_recheck",
                    "sample_floor": "one_source_gap_candidate_with_fresh_recovery",
                    "primary_decision_metric": "rebound_with_trusted_ws_micro_before_ttl",
                    "source_quality_gate": "fresh_quote_and_trusted_signed_ws_micro_required",
                    "runtime_effect": False,
                    "allowed_runtime_apply": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": "rest_positive_micro|hard_safety_bypass",
                    "recheck_enabled": True,
                    "recheck_active": True,
                    "recheck_active_date": "2026-07-15",
                    "recheck_current_date": "2026-07-15",
                    "recheck_observed_at": 1_784_077_190.0,
                    "recheck_max_quote_age_ms": 1500.0,
                    "recheck_max_ws_micro_age_ms": 3000.0,
                    "recheck_min_trusted_ticks": 3,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    assert report["stage_contracts"]["shallow_source_gap_recheck"]["status"] == "pass"
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_blocks_shallow_recheck_rest_positive_micro(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "threshold_family": "shallow_avg_down_source_gap_recheck",
        "recheck_state": "recovered",
        "metric_role": "bounded_tunable",
        "decision_authority": "bounded_shallow_avg_down_recheck_runtime",
        "window_policy": "same_position_10_to_20_second_recheck",
        "sample_floor": "one_source_gap_candidate_with_fresh_recovery",
        "primary_decision_metric": "rebound_with_trusted_ws_micro_before_ttl",
        "source_quality_gate": "fresh_quote_and_trusted_signed_ws_micro_required",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "forbidden_uses": "rest_positive_micro|hard_safety_bypass",
        "recheck_enabled": True,
        "recheck_active": True,
        "recheck_active_date": "2026-07-15",
        "recheck_current_date": "2026-07-15",
        "recheck_observed_at": 1_784_077_200.0,
        "recheck_max_quote_age_ms": 1500.0,
        "recheck_max_ws_micro_age_ms": 3000.0,
        "recheck_min_trusted_ticks": 3,
        "quote_fresh": True,
        "quote_age_ms": 420.0,
        "quote_age_source": "ka10004_rest_orderbook",
        "reversal_feature_consumption_age_basis": "feature_extracted_at_plus_snapshot_age",
        "reversal_feature_consumption_elapsed_ms": 200.0,
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 5,
        "tick_aggressor_source": "kiwoom_rest_ka10084_signed_trade_qty",
        "trusted_ws_micro_latest_age_ms": 180.0,
        "buy_pressure_10t": 72.0,
    }
    _write_events(
        tmp_path, "2026-07-15", [_event("shallow_source_gap_recheck", fields)]
    )

    report = audit.build_observation_source_quality_audit("2026-07-15")

    stage = report["stage_contracts"]["shallow_source_gap_recheck"]
    assert stage["status"] == "fail"
    assert stage["invalid_label_counts"]["shallow_recheck_ws_micro_contract"] == 1
    assert report["summary"]["tuning_input_allowed"] is False


def test_observation_source_quality_audit_blocks_reversal_add_pressure_without_trusted_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "reversal_add_blocked_reason",
                _reversal_add_blocked_fields(
                    tick_aggressor_trusted_count=0,
                    tick_aggressor_pressure_usable=False,
                ),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    contract = report["stage_contracts"]["reversal_add_blocked_reason"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["tick_aggressor_pressure_usable_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    assert (
        report["hard_blocking_row_exclusions"][0]["stage"]
        == "reversal_add_blocked_reason"
    )


def _first_touch_fields(**overrides):
    fields = {
        "threshold_family": "deep_recovery_avg_down",
        "decision_source": "DEEP_RECOVERY_AVG_DOWN",
        "decision_authority": "real_scalping_deep_recovery_intercept",
        "metric_role": "bounded_tunable",
        "window_policy": "same_day_intraday_runtime",
        "sample_floor": "postclose_rolling_real_deep_recovery_required",
        "primary_decision_metric": "post_add_mfe_30m_pct",
        "source_quality_gate": "real_holding_stop_line_touch_and_scale_in_guards_present",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "forbidden_uses": (
            "entry_threshold_relaxation|provider_route_change|broker_guard_bypass|"
            "quantity_cap_release|protect_or_emergency_bypass|max_per_position_bypass|hard_stop_threshold_relaxation"
        ),
        "profit_rate": "-3.42",
        "peak_profit": "-0.23",
        "current_ai_score": "65",
        "held_sec": 1494,
        "gate_allowed": True,
        "gate_reason": "ok",
        "add_type": "AVG_DOWN",
        "add_reason": "deep_recovery_avg_down",
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "first_touch_avgdown_decision_allowed": True,
        "first_touch_avgdown_decision_reason": "ai_score_moderate_with_context_support",
        "first_touch_avgdown_decision_authority": "real_scalping_first_touch_avgdown_decision_gate",
    }
    fields.update(overrides)
    return fields


def test_observation_source_quality_audit_accepts_first_touch_avgdown_contracts(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "stop_line_touch_mandatory_avg_down_candidate", _first_touch_fields()
            ),
            _event(
                "stop_line_touch_mandatory_avg_down_submitted",
                _first_touch_fields(
                    actual_order_submitted=True, ord_no="A1", retry_count=1
                ),
                record_id=2,
            ),
            _event(
                "stop_line_touch_first_touch_avgdown_decision_blocked",
                _first_touch_fields(
                    gate_allowed=False,
                    gate_reason="repeated_blockers_without_recovery",
                    block_reason="repeated_blockers_without_recovery",
                    actual_order_submitted=False,
                    broker_order_forbidden=True,
                    first_touch_avgdown_decision_allowed=False,
                    first_touch_avgdown_decision_reason="repeated_blockers_without_recovery",
                ),
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert (
        report["stage_contracts"]["stop_line_touch_mandatory_avg_down_candidate"][
            "status"
        ]
        == "pass"
    )
    assert (
        report["stage_contracts"]["stop_line_touch_mandatory_avg_down_submitted"][
            "status"
        ]
        == "pass"
    )
    assert (
        report["stage_contracts"][
            "stop_line_touch_first_touch_avgdown_decision_blocked"
        ]["status"]
        == "pass"
    )
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_reviews_first_touch_quote_stale_unknown(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "stop_line_touch_first_touch_avgdown_decision_blocked",
                _first_touch_fields(
                    gate_allowed=False,
                    gate_reason="repeated_blockers_without_recovery",
                    block_reason="repeated_blockers_without_recovery",
                    actual_order_submitted=False,
                    broker_order_forbidden=True,
                    first_touch_avgdown_decision_allowed=False,
                    first_touch_avgdown_decision_reason="repeated_blockers_without_recovery",
                    first_touch_reversal_feature_source_quality="missing",
                    first_touch_reversal_feature_stale=False,
                    first_touch_reversal_feature_stale_reason="-",
                    first_touch_quote_stale="unknown",
                    first_touch_quote_age_ms="-",
                    first_touch_quote_age_source="missing",
                ),
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert report["unknown_token_findings"] == []
    reviewed = report["reviewed_unknown_token_findings"]
    fields = {item["field"]: item for item in reviewed[0]["fields"]}
    assert fields["first_touch_quote_stale"]["reviewed_reason"] == (
        "reviewed_first_touch_quote_stale_not_available"
    )


def test_observation_source_quality_audit_accepts_scanner_source_guard_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common_fields = {
        "metric_role": "source_quality_gate",
        "window_policy": "intraday_operational_guard",
        "sample_floor": "not_applicable_runtime_guard",
        "primary_decision_metric": "funnel_count",
        "runtime_effect": True,
        "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "scalping_scanner_real_source_guard_block",
                {
                    **common_fields,
                    "decision_authority": "real_scalping_scanner_source_guard_only",
                    "source_quality_gate": "scalping_scanner_real_source_guard",
                    "scanner_real_source_guard_applied": True,
                    "scanner_real_source_guard_skip_reason": (
                        "value_top_only_repeat_deteriorating_without_strength"
                    ),
                    "scanner_real_source_guard_block_event_emitted": True,
                    "source_signature": "VALUE_TOP",
                    "first_seen_flu_rate": "8.40",
                    "current_flu_rate": "0.00",
                    "last_promoted_at": "1000.0",
                },
            ),
            _event(
                "condition_unmatch_guard",
                {
                    **common_fields,
                    "decision_authority": "real_scalping_condition_unmatch_guard_only",
                    "source_quality_gate": "condition_unmatch_guard",
                    "condition_unmatch_guard_applied": True,
                    "condition_unmatch_guard_action": "pending_unmatched",
                    "condition_unmatch_guard_reason": "unmatched_only_guard_hold",
                    "condition_unmatch_age_sec": "40",
                    "condition_name": "scalp_vwap_reclaim_01",
                    "position_tag": "VWAP_RECLAIM",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert (
        report["stage_contracts"]["scalping_scanner_real_source_guard_block"]["status"]
        == "pass"
    )
    assert report["stage_contracts"]["condition_unmatch_guard"]["status"] == "pass"
    assert report["status"] == "pass"


def test_observation_source_quality_audit_accepts_first_seen_scanner_block_without_repeat_fields(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_real_source_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "window_policy": "intraday_operational_guard",
                    "sample_floor": "not_applicable_runtime_guard",
                    "primary_decision_metric": "funnel_count",
                    "runtime_effect": True,
                    "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "real_scalping_scanner_source_guard_only",
                    "source_quality_gate": "scalping_scanner_real_source_guard",
                    "scanner_real_source_guard_applied": True,
                    "scanner_real_source_guard_skip_reason": "late_confirmation_first_seen_probe",
                    "scanner_real_source_guard_block_event_emitted": True,
                    "source_signature": "PRICE_JUMP_START",
                    "current_flu_rate": "2.10",
                    "scanner_source_guard_context": "normal_first_seen_block",
                    "scanner_source_guard_first_seen_required": False,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_real_source_guard_block"]
    assert contract["status"] == "pass"
    assert "first_seen_flu_rate" not in contract["missing_violations"]
    assert "last_promoted_at" not in contract["missing_violations"]


def test_observation_source_quality_audit_requires_repeat_scanner_guard_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_real_source_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "window_policy": "intraday_operational_guard",
                    "sample_floor": "not_applicable_runtime_guard",
                    "primary_decision_metric": "funnel_count",
                    "runtime_effect": True,
                    "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "real_scalping_scanner_source_guard_only",
                    "source_quality_gate": "scalping_scanner_real_source_guard",
                    "scanner_real_source_guard_applied": True,
                    "scanner_real_source_guard_skip_reason": (
                        "value_top_only_repeat_deteriorating_without_strength"
                    ),
                    "scanner_real_source_guard_block_event_emitted": True,
                    "source_signature": "VALUE_TOP",
                    "current_flu_rate": "0.00",
                    "scanner_source_guard_context": "repeat_guard_with_provenance",
                    "scanner_source_guard_first_seen_required": True,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_real_source_guard_block"]
    assert contract["status"] == "warning"
    assert contract["conditional_required_fields"] == [
        "first_seen_flu_rate",
        "last_promoted_at",
    ]
    assert contract["missing_violations"]["first_seen_flu_rate"] == 1.0
    assert contract["missing_violations"]["last_promoted_at"] == 1.0


def test_observation_source_quality_audit_requires_repeat_scanner_guard_provenance_from_reason_fallback(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_real_source_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "window_policy": "intraday_operational_guard",
                    "sample_floor": "not_applicable_runtime_guard",
                    "primary_decision_metric": "funnel_count",
                    "runtime_effect": True,
                    "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "real_scalping_scanner_source_guard_only",
                    "source_quality_gate": "scalping_scanner_real_source_guard",
                    "scanner_real_source_guard_applied": True,
                    "scanner_real_source_guard_skip_reason": (
                        "value_top_only_repeat_deteriorating_without_strength"
                    ),
                    "scanner_real_source_guard_block_event_emitted": True,
                    "source_signature": "VALUE_TOP",
                    "current_flu_rate": "0.00",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_real_source_guard_block"]
    assert contract["status"] == "warning"
    assert contract["conditional_required_fields"] == [
        "first_seen_flu_rate",
        "last_promoted_at",
    ]
    assert contract["missing_violations"]["first_seen_flu_rate"] == 1.0
    assert contract["missing_violations"]["last_promoted_at"] == 1.0


def test_observation_source_quality_audit_does_not_require_repeat_fields_for_late_confirmation_reason_only(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_real_source_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "window_policy": "intraday_operational_guard",
                    "sample_floor": "not_applicable_runtime_guard",
                    "primary_decision_metric": "funnel_count",
                    "runtime_effect": True,
                    "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "real_scalping_scanner_source_guard_only",
                    "source_quality_gate": "scalping_scanner_real_source_guard",
                    "scanner_real_source_guard_applied": True,
                    "scanner_real_source_guard_skip_reason": "late_confirmation_probe_waiting",
                    "scanner_real_source_guard_block_event_emitted": True,
                    "source_signature": "PRICE_JUMP_START",
                    "current_flu_rate": "2.00",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_real_source_guard_block"]
    assert contract["status"] == "pass"
    assert contract["conditional_required_fields"] == []
    assert contract["missing_violations"] == {}


def _runtime_attach_rank_sign_fields(**overrides):
    fields = {
        "metric_role": "runtime_handoff_observation",
        "decision_authority": "real_scalping_scanner_runtime_watchlist_handoff_only",
        "window_policy": "intraday_runtime_handoff",
        "sample_floor": "not_applicable_runtime_handoff",
        "primary_decision_metric": "funnel_count",
        "source_quality_gate": "scalping_scanner_runtime_target_attach_contract",
        "runtime_effect": True,
        "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_target_attach_outcome": "attached",
        "runtime_target_attach_reason": "scanner_runtime_target_attach",
        "scanner_promotion_id": "SCANPROM-005930-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "source_signature": "REALTIME_RANK_START",
        "target_status": "WATCHING",
        "target_strategy": "SCALPING",
        "target_position_tag": "SCANNER",
        "rank_change": "12",
        "rank_change_sign": "+",
        "rank_change_sign_authority": "raw_unverified_not_decision_input",
        "rank_change_sign_state": "positive",
        "rank_change_sign_consistency": "consistent",
        "rank_change_score_input": "12",
        "rank_change_score_policy": "positive_signed_rank_delta_only_raw_rank_sign_unverified",
    }
    fields.update(overrides)
    return fields


def test_observation_source_quality_audit_accepts_scanner_rank_sign_consistency(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                _runtime_attach_rank_sign_fields(),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_runtime_target_attach"]
    assert contract["status"] == "pass"
    assert contract["invalid_label_violations"] == {}


def test_observation_source_quality_audit_contracts_all_scheduler_events(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "metric_role": "runtime_scheduler_latency",
        "decision_authority": ("scanner_runtime_scheduler_only_no_order_authority"),
        "window_policy": "per_scanner_generation_action_timestamps",
        "sample_floor": "one_valid_scanner_generation",
        "primary_decision_metric": "attach_to_first_precheck_sec",
        "source_quality_gate": ("canonical_generation_and_venue_provenance_required"),
        "runtime_effect": True,
        "forbidden_uses": "standalone_buy,broker_submit",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "scheduler_version": "scanner_deadline_scheduler_v1",
        "scheduler_action": "test_action",
        "scanner_scheduler_action_epoch": 1_750_000_000.0,
        "effective_venue": "KRX",
        "venue_resolution": "consistent_explicit:payload.effective_venue",
    }
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            *[_event(stage, fields) for stage in audit.SCANNER_SCHEDULER_STAGES],
            _event(
                "scalping_scanner_scheduler_pre_submit_rejected",
                {
                    **fields,
                    "decision_authority": (
                        "scanner_generation_consistency_pre_submit_safety_veto"
                    ),
                    "metric_role": "safety_veto",
                    "scanner_generation_submit_allowed": False,
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    for stage in audit.SCANNER_SCHEDULER_STAGES:
        contract = report["stage_contracts"][stage]
        assert contract["status"] == "pass"
        assert contract["missing_violations"] == {}
    submit_contract = report["stage_contracts"][
        "scalping_scanner_scheduler_pre_submit_rejected"
    ]
    assert submit_contract["status"] == "pass"
    assert submit_contract["missing_violations"] == {}


def test_observation_source_quality_allows_expired_boot_restore_unknown_venue(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_scheduler_boot_restore_expired",
                {
                    "metric_role": "runtime_scheduler_latency",
                    "decision_authority": (
                        "scanner_runtime_scheduler_only_no_order_authority"
                    ),
                    "window_policy": ("per_scanner_generation_action_timestamps"),
                    "sample_floor": "one_valid_scanner_generation",
                    "primary_decision_metric": "attach_to_first_precheck_sec",
                    "source_quality_gate": (
                        "canonical_generation_and_venue_provenance_required"
                    ),
                    "runtime_effect": True,
                    "forbidden_uses": "standalone_buy,broker_submit",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "scheduler_version": "scanner_deadline_scheduler_v1",
                    "scheduler_action": "invalid_boot_restore_expired",
                    "scanner_scheduler_action_epoch": 1_750_000_000.0,
                    "effective_venue": "UNKNOWN",
                    "venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_scheduler_boot_persisted_venue_missing"
                    ),
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"][
        "scalping_scanner_scheduler_boot_restore_expired"
    ]
    assert contract["status"] == "pass"
    assert contract["invalid_label_violations"] == {}


def test_observation_source_quality_audit_keeps_rank_sign_fields_rollout_compatible(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = _runtime_attach_rank_sign_fields()
    fields.pop("rank_change_sign_state")
    fields.pop("rank_change_sign_consistency")
    _write_events(
        tmp_path,
        "2026-06-17",
        [_event("scalping_scanner_runtime_target_attach", fields)],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_runtime_target_attach"]
    assert contract["status"] == "pass"
    assert "rank_change_sign_consistency" not in contract["missing_violations"]
    assert contract["invalid_label_violations"] == {}


def test_observation_source_quality_audit_flags_scanner_rank_sign_mismatch(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                _runtime_attach_rank_sign_fields(
                    rank_change="-12",
                    rank_change_sign="+",
                    rank_change_sign_state="positive",
                    rank_change_sign_consistency="mismatch",
                ),
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_runtime_target_attach"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["rank_change_sign_consistency_mismatch"]
        == 1.0
    )


def test_observation_source_quality_audit_flags_scanner_source_guard_rank_sign_unknown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-17",
        [
            _event(
                "scalping_scanner_real_source_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "real_scalping_scanner_source_guard_only",
                    "window_policy": "intraday_operational_guard",
                    "sample_floor": "not_applicable_runtime_guard",
                    "primary_decision_metric": "funnel_count",
                    "source_quality_gate": "scalping_scanner_real_source_guard",
                    "runtime_effect": True,
                    "forbidden_uses": "score_threshold_change,provider_route_change,order_price_change",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "scanner_real_source_guard_applied": True,
                    "scanner_real_source_guard_skip_reason": "source_quality_rank_sign_unknown",
                    "scanner_real_source_guard_block_event_emitted": True,
                    "source_signature": "REALTIME_RANK_START",
                    "current_flu_rate": "1.20",
                    "rank_change": "1",
                    "rank_change_sign": "X",
                    "rank_change_sign_authority": "raw_unverified_not_decision_input",
                    "rank_change_sign_state": "unknown",
                    "rank_change_sign_consistency": "unknown",
                    "rank_change_score_input": "1",
                    "rank_change_score_policy": "positive_signed_rank_delta_only_raw_rank_sign_unverified",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-17")

    contract = report["stage_contracts"]["scalping_scanner_real_source_guard_block"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["rank_change_sign_consistency_unknown"]
        == 1.0
    )


def test_observation_source_quality_audit_accepts_early_accel_recheck_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common_fields = {
        "metric_role": "funnel_count",
        "window_policy": "intraday_operator_runtime_retry",
        "sample_floor": "not_applicable_operator_runtime_retry",
        "primary_decision_metric": "funnel_count",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": "EV|rolling|MTD|cumulative_tuning|live_auto_promotion|runtime_apply_bridge",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "operator_runtime_observation_retry_only",
        "source_quality_gate": "early_accel_recheck_contract_fields_present",
        "scanner_promotion_reason": "probe_acceleration_confirmed",
        "promotion_price": 12280,
        "current_price": 12430,
        "promotion_age_sec": "45.0",
        "recheck_count": 0,
        "last_ai_elapsed_sec": "25.0",
        "skip_reason": "allowed",
        "tick_accel": "1.250",
        "micro_vwap_bp": "12.00",
        "quote_stale": False,
    }
    common_fields.update(
        {
            "tick_accel_source": "computed_10ticks",
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "tick_accel_usable": True,
            "micro_vwap_available": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": True,
            "minute_candle_latest_age_ms": 8000,
            "micro_vwap_usable": True,
        }
    )
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event("early_accel_recheck_evaluated", common_fields),
            _event("early_accel_recheck_ai_call_allowed", common_fields),
            _event(
                "early_accel_recheck_skipped",
                {
                    **common_fields,
                    "skip_reason": "tick_accel_below_min",
                    "tick_accel": "0.900",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    assert (
        report["stage_contracts"]["early_accel_recheck_evaluated"]["status"] == "pass"
    )
    assert (
        report["stage_contracts"]["early_accel_recheck_ai_call_allowed"]["status"]
        == "pass"
    )
    assert report["stage_contracts"]["early_accel_recheck_skipped"]["status"] == "pass"
    assert report["status"] == "pass"


def test_observation_source_quality_audit_accepts_ai_numeric_consistency_recheck_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common_fields = {
        "metric_role": "funnel_count",
        "window_policy": "intraday_operator_runtime_retry",
        "sample_floor": "not_applicable_operator_runtime_retry",
        "primary_decision_metric": "funnel_count",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": "EV|rolling|MTD|cumulative_tuning|live_auto_promotion|runtime_apply_bridge",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "operator_runtime_decision_recheck_only",
        "source_quality_gate": "ai_numeric_consistency_recheck_contract_fields_present",
        "original_action": "WAIT",
        "original_score": "72.0",
        "original_reason_excerpt": "tick_acceleration_ratio described as failed",
        "inconsistency_field": "tick_acceleration_ratio",
        "inconsistency_reason": "tick_acceleration_pass_described_as_fail",
        "position_pass": True,
        "speed_pass": True,
        "supply_pass": True,
        "feature_pass_count": 3,
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 9000,
        "recheck_count": 0,
        "recheck_action": "BUY",
        "recheck_score": "78.0",
        "recheck_reason_excerpt": "speed and supply confirmed",
        "skip_reason": "allowed",
        "quote_stale": False,
    }
    _write_events(
        tmp_path,
        "2026-06-18",
        [
            _event("ai_numeric_consistency_recheck_evaluated", common_fields),
            _event("ai_numeric_consistency_recheck_allowed", common_fields),
            _event(
                "ai_numeric_consistency_recheck_failed",
                {
                    **common_fields,
                    "recheck_action": "WAIT",
                    "recheck_score": "70.0",
                    "recheck_reason_excerpt": "still contradictory",
                    "skip_reason": "recheck_still_contradictory",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-18")

    assert (
        report["stage_contracts"]["ai_numeric_consistency_recheck_evaluated"]["status"]
        == "pass"
    )
    assert (
        report["stage_contracts"]["ai_numeric_consistency_recheck_allowed"]["status"]
        == "pass"
    )
    assert (
        report["stage_contracts"]["ai_numeric_consistency_recheck_failed"]["status"]
        == "pass"
    )
    assert report["status"] == "pass"


def test_observation_source_quality_audit_accepts_early_accel_strong_bundle_recheck_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common_fields = {
        "metric_role": "funnel_count",
        "window_policy": "intraday_operator_runtime_retry",
        "sample_floor": "not_applicable_operator_runtime_retry",
        "primary_decision_metric": "funnel_count",
        "runtime_effect": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": "EV|rolling|MTD|cumulative_tuning|live_auto_promotion|runtime_apply_bridge",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "operator_runtime_decision_recheck_only",
        "source_quality_gate": "early_accel_strong_bundle_recheck_contract_fields_present",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "strong_bundle_pass_count": 4,
        "price_delta_since_first_seen_pct": "0.62",
        "comparable_flu_delta_since_first_seen": "0.58",
        "cntr_str_available": True,
        "cntr_str": "118.0",
        "tick_acceleration_ratio": "1.220",
        "curr_vs_micro_vwap_bp": "8.50",
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 12000,
        "buy_pressure_10t": "71.20",
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "original_action": "WAIT",
        "original_score": "62.0",
        "recheck_action": "BUY",
        "recheck_score": "76.0",
        "recheck_reason_excerpt": "strong bundle confirmed",
        "recheck_failure_class": "not_applicable",
        "recheck_count": 1,
        "quote_stale": False,
        "skip_reason": "allowed",
    }
    _write_events(
        tmp_path,
        "2026-06-18",
        [
            _event("early_accel_strong_bundle_recheck_evaluated", common_fields),
            _event("early_accel_strong_bundle_recheck_allowed", common_fields),
            _event(
                "early_accel_strong_bundle_recheck_failed",
                {
                    **common_fields,
                    "recheck_action": "WAIT",
                    "recheck_score": "73.0",
                    "recheck_reason_excerpt": "wait for confirmation",
                    "recheck_failure_class": "wait_below_min_score",
                    "skip_reason": "recheck_wait_or_buy_below_min_score",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-18")

    assert (
        report["stage_contracts"]["early_accel_strong_bundle_recheck_evaluated"][
            "status"
        ]
        == "pass"
    )
    assert (
        report["stage_contracts"]["early_accel_strong_bundle_recheck_allowed"]["status"]
        == "pass"
    )
    assert (
        report["stage_contracts"]["early_accel_strong_bundle_recheck_failed"]["status"]
        == "pass"
    )
    assert report["status"] == "pass"


def test_observation_source_quality_audit_accepts_s15_fast_track_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    common_fields = {
        "metric_role": "source_quality_gate",
        "decision_authority": "real_s15_fast_track_runtime_only",
        "source_quality_gate": "s15_fast_track_contract",
        "window_policy": "intraday_operational_guard",
        "sample_floor": "not_applicable_runtime_guard",
        "primary_decision_metric": "funnel_count",
        "runtime_effect": True,
        "forbidden_uses": "score_threshold_change,provider_route_change,hard_safety_change",
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "s15_fast_track_contract_version": "s15_fast_track_v1",
    }
    _write_events(
        tmp_path,
        "2026-06-15",
        [
            _event(
                "s15_candidate_armed",
                {
                    **common_fields,
                    "s15_condition_role": "candidate_arm",
                    "base_condition": "s15_scan_base_01",
                    "armed_at": "1000.0",
                    "expires_at": "1180.0",
                    "ttl_sec": "180",
                },
            ),
            _event(
                "s15_trigger_received",
                {
                    **common_fields,
                    "s15_condition_role": "trigger_break",
                    "condition_name": "s15_trigger_break_01",
                    "armed": True,
                    "reentry_blocked": False,
                    "existing_fast_state": False,
                    "trigger_price": "10000",
                },
            ),
            _event(
                "s15_trigger_blocked",
                {
                    **common_fields,
                    "s15_condition_role": "fast_track_submit",
                    "s15_block_reason": "ai_score_below_80",
                },
            ),
            _event(
                "s15_fast_track_submitted",
                {
                    **common_fields,
                    "actual_order_submitted": True,
                    "s15_condition_role": "fast_track_submit",
                    "shadow_id": "10",
                    "requested_qty": "1",
                    "order_price": "10000",
                    "broker_order_no": "B1",
                },
            ),
            _event(
                "s15_fast_track_cancelled",
                {
                    **common_fields,
                    "s15_condition_role": "fast_track_submit",
                    "shadow_id": "10",
                    "s15_cancel_reason": "no_fill_after_20s",
                },
            ),
            _event(
                "s15_fast_track_holding",
                {
                    **common_fields,
                    "s15_condition_role": "fast_track_holding",
                    "shadow_id": "10",
                    "avg_buy_price": "10000",
                    "buy_qty": "1",
                    "target_price": "10180",
                    "stop_price": "9930",
                },
            ),
            _event(
                "s15_fast_track_completed",
                {
                    **common_fields,
                    "s15_condition_role": "fast_track_exit",
                    "shadow_id": "10",
                    "buy_price": "10000",
                    "sell_price": "10180",
                    "buy_qty": "1",
                    "profit_rate": "1.8",
                },
            ),
            _event(
                "s15_fast_track_failed",
                {
                    **common_fields,
                    "s15_condition_role": "fast_track_submit",
                    "s15_block_reason": "exception",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-15")

    for stage in (
        "s15_candidate_armed",
        "s15_trigger_received",
        "s15_trigger_blocked",
        "s15_fast_track_submitted",
        "s15_fast_track_cancelled",
        "s15_fast_track_holding",
        "s15_fast_track_completed",
        "s15_fast_track_failed",
    ):
        assert report["stage_contracts"][stage]["status"] == "pass"
    assert report["status"] == "pass"


def test_observation_source_quality_audit_normalizes_pre_contract_ai_and_latency(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-21",
        [
            _event(
                "ai_confirmed",
                {
                    "latest_strength": "120.0",
                    "buy_pressure_10t": "61.0",
                    "distance_from_day_high_pct": "-1.0",
                    "intraday_range_pct": "4.0",
                },
                record_id=1,
            ),
            _event(
                "latency_block",
                {
                    "reason": "latency_fallback_deprecated",
                    "latency_state": "CAUTION",
                    "effective_decision": "WAIT_REQUOTE",
                    "quote_stale": False,
                    "signal_price": 10000,
                    "latest_price": 10010,
                    "latency_canary_applied": False,
                    "threshold_family": "latency_classifier_runtime_profile",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "latency_pass",
                {
                    "reason": "safe",
                    "latency_state": "SAFE",
                    "policy_decision": "ALLOW_SUBMIT",
                    "effective_decision": "ALLOW_SUBMIT",
                    "ws_age_ms": 10,
                    "ws_jitter_ms": 2,
                    "spread_ratio": "0.001",
                    "quote_stale": False,
                    "signal_price": 10000,
                    "latest_price": 10000,
                    "latency_canary_applied": False,
                    "threshold_family": "latency_classifier_runtime_profile",
                    "runtime_effect": False,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-21")

    assert report["stage_contracts"]["ai_confirmed"]["status"] == "pass"
    assert report["stage_contracts"]["latency_block"]["status"] == "pass"
    assert report["stage_contracts"]["latency_pass"]["status"] == "pass"


def test_observation_source_quality_audit_accepts_real_execution_diagnostic_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-21",
        [
            _event(
                "holding_started", {"strategy": "SCALPING", "buy_qty": 1}, record_id=idx
            )
            for idx in range(60)
        ]
        + [
            _event(
                "scale_in_executed",
                {"add_type": "PYRAMID", "new_buy_qty": 2},
                record_id=100 + idx,
            )
            for idx in range(60)
        ]
        + [
            _event(
                "same_symbol_loss_reentry_cooldown",
                {
                    "exit_rule": "scalp_soft_stop_pct",
                    "profit_rate": "-1.0",
                    "cooldown_sec": 3600,
                },
                record_id=200 + idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-21")

    assert report["high_volume_no_source_fields"] == []
    assert report["stage_contracts"]["holding_started"]["status"] == "pass"
    assert report["stage_contracts"]["scale_in_executed"]["status"] == "pass"
    assert (
        report["stage_contracts"]["same_symbol_loss_reentry_cooldown"]["status"]
        == "pass"
    )


def test_observation_source_quality_audit_blocks_swing_loss_reentry_placeholder_source(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    contract = report["stage_contracts"]["swing_same_symbol_loss_reentry_cooldown"]
    assert contract["status"] == "warning"
    assert contract["missing_violations"]["source_probe_id"] == 1.0
    assert contract["missing_violations"]["source_record_id"] == 1.0
    assert report["summary"]["tuning_input_allowed"] is False
    assert report["summary"]["hard_blocking_excluded_row_count"] == 1
    assert (
        report["hard_blocking_row_exclusions"][0]["stage"]
        == "swing_same_symbol_loss_reentry_cooldown"
    )


def test_observation_source_quality_write_excludes_bad_rows_instead_of_blocking_full_date(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    valid_id = "swing_dry_run:2026-06-04:KOSPI_ML:004710:exit:1780556300"
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
                record_id=1,
            ),
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": valid_id,
                    "source_record_id": valid_id,
                    "source_stage": "exit",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.write_report("2026-06-04")
    raw_path = tmp_path / "pipeline_events" / "pipeline_events_2026-06-04.jsonl"
    rows = [
        json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()
    ]

    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["hard_blocking_excluded_row_count"] == 1
    assert report["summary"]["pre_exclusion_hard_blocking_excluded_row_count"] == 1
    assert report["summary"]["current_scan_hard_blocking_excluded_row_count"] == 0
    assert report["summary"]["post_exclusion_hard_blocking_excluded_row_count"] == 0
    assert report["summary"]["raw_row_exclusion_applied"] is True
    assert report["summary"]["raw_row_exclusion_deferred_writer_active"] is False
    assert report["summary"]["raw_row_exclusion_revalidation_required"] is False
    assert report["raw_row_exclusion"]["excluded_row_count"] == 1
    assert report["raw_row_exclusion"]["application_state"] == "applied"
    assert len(rows) == 1
    assert rows[0]["record_id"] == 2
    manifest = Path(report["raw_row_exclusion"]["manifest_path"])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["policy"] == "exclude_defective_rows_not_full_day_raw"
    assert payload["excluded_row_count"] == 1
    assert payload["stage_counts"] == {"swing_same_symbol_loss_reentry_cooldown": 1}
    assert payload["field_gap_counts"] == {
        "missing_fields:source_probe_id": 1,
        "missing_fields:source_record_id": 1,
    }
    assert payload["exclusion_reasons"]["required_field_missing"] == 1
    assert payload["exclusion_reasons"]["provenance_missing"] == 1
    assert (
        payload["producer_hint"][0]["stage"]
        == "swing_same_symbol_loss_reentry_cooldown"
    )
    assert payload["sample_rows"][0]["gap_fields"]["missing_fields"] == [
        "source_probe_id",
        "source_record_id",
    ]
    backup_path = Path(payload["backup_path"])
    assert backup_path.exists()
    assert backup_path.suffix == ".gz"
    with gzip.open(backup_path, "rt", encoding="utf-8") as handle:
        backup_rows = [json.loads(line) for line in handle if line.strip()]
    assert [row["record_id"] for row in backup_rows] == [1, 2]

    repeated = audit.write_report("2026-06-04")
    assert repeated["summary"]["tuning_input_allowed"] is True
    assert repeated["summary"]["hard_blocking_excluded_row_count"] == 1
    assert repeated["summary"]["raw_row_exclusion_applied"] is True
    assert repeated["raw_row_exclusion"]["manifest_path"] == str(manifest)


def test_legacy_applied_exclusion_blocks_tuning_until_revalidated(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    target_date = "2026-06-04"
    _write_events(
        tmp_path,
        target_date,
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
                record_id=1,
            )
        ],
    )
    applied = audit.write_report(target_date)
    report_path, _ = audit.report_paths(target_date)
    manifest_path = Path(applied["raw_row_exclusion"]["manifest_path"])
    prior_report = json.loads(report_path.read_text(encoding="utf-8"))
    prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior_report["raw_row_exclusion"].pop("audit_contract_version", None)
    prior_manifest.pop("audit_contract_version", None)
    report_path.write_text(
        json.dumps(prior_report, ensure_ascii=False), encoding="utf-8"
    )
    manifest_path.write_text(
        json.dumps(prior_manifest, ensure_ascii=False), encoding="utf-8"
    )

    repeated = audit.write_report(target_date)

    assert repeated["summary"]["raw_row_exclusion_revalidation_required"] is True
    assert repeated["summary"]["tuning_input_allowed"] is False
    assert repeated["summary"]["blocked_reason"] == (
        "raw_row_exclusion_revalidation_required"
    )


def test_observation_source_quality_defers_raw_mutation_while_writer_is_active(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    monkeypatch.setattr(audit, "_raw_source_writer_active", lambda *_args: True)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
                record_id=1,
            )
        ],
    )
    raw_path = tmp_path / "pipeline_events" / "pipeline_events_2026-06-04.jsonl"
    before = raw_path.read_bytes()

    report = audit.write_report("2026-06-04")

    assert raw_path.read_bytes() == before
    assert report["status"] == "warning"
    assert report["summary"]["tuning_input_allowed"] is False
    assert report["summary"]["hard_blocking_excluded_row_count"] == 1
    assert report["summary"]["pre_exclusion_hard_blocking_excluded_row_count"] == 1
    assert report["summary"]["current_scan_hard_blocking_excluded_row_count"] == 1
    assert report["summary"]["post_exclusion_hard_blocking_excluded_row_count"] == 1
    assert report["summary"]["raw_row_exclusion_applied"] is False
    assert report["summary"]["raw_row_exclusion_deferred_writer_active"] is True
    assert report["raw_row_exclusion"]["application_state"] == (
        "deferred_writer_active"
    )
    assert report["raw_row_exclusion"]["backup_path"] is None
    manifest = json.loads(
        Path(report["raw_row_exclusion"]["manifest_path"]).read_text(encoding="utf-8")
    )
    assert manifest["raw_mutation_applied"] is False
    assert manifest["excluded_row_count"] == 1


def test_raw_exclusion_aborts_when_source_changes_during_backup(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    target_date = "2026-06-04"
    invalid_event = _event(
        "swing_same_symbol_loss_reentry_cooldown",
        {
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "source_book": "swing_dry_run",
            "source_probe_id": "-",
            "source_record_id": "-",
            "source_stage": "exit",
        },
        record_id=1,
    )
    appended_event = _event(
        "swing_same_symbol_loss_reentry_cooldown",
        {
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "source_book": "swing_dry_run",
            "source_probe_id": "append-race",
            "source_record_id": "append-race",
            "source_stage": "exit",
        },
        record_id=2,
    )
    _write_events(tmp_path, target_date, [invalid_event])
    report = audit.build_observation_source_quality_audit(target_date)
    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    original_copyfileobj = audit.shutil.copyfileobj

    def copy_and_append(source, target, *args, **kwargs):
        result = original_copyfileobj(source, target, *args, **kwargs)
        with raw_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(appended_event, ensure_ascii=False) + "\n")
        return result

    monkeypatch.setattr(audit.shutil, "copyfileobj", copy_and_append)

    manifest = audit._exclude_hard_blocking_rows_from_raw(target_date, report)

    rows = [
        json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()
    ]
    assert manifest is None
    assert [row["record_id"] for row in rows] == [1, 2]
    assert not raw_path.with_suffix(".jsonl.tmp_row_exclusion").exists()
    assert not list(
        (tmp_path / "source_quality" / audit.RAW_ROW_EXCLUSION_DIRNAME).glob(
            f"{target_date}_*/*.gz"
        )
    )


def test_repeated_writer_defer_preserves_prior_applied_exclusion_history(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    target_date = "2026-06-04"
    valid_id = "swing_dry_run:2026-06-04:KOSPI_ML:004710:exit:1780556300"
    valid_event = _event(
        "swing_same_symbol_loss_reentry_cooldown",
        {
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "source_book": "swing_dry_run",
            "source_probe_id": valid_id,
            "source_record_id": valid_id,
            "source_stage": "exit",
        },
        record_id=2,
    )
    invalid_event = _event(
        "swing_same_symbol_loss_reentry_cooldown",
        {
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "source_book": "swing_dry_run",
            "source_probe_id": "-",
            "source_record_id": "-",
            "source_stage": "exit",
        },
        record_id=1,
    )
    _write_events(tmp_path, target_date, [invalid_event, valid_event])

    applied = audit.write_report(target_date)
    applied_manifest = applied["raw_row_exclusion"]["manifest_path"]
    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    with raw_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(invalid_event, ensure_ascii=False) + "\n")

    monkeypatch.setattr(audit, "_raw_source_writer_active", lambda *_args: True)
    first_deferred = audit.write_report(target_date)
    second_deferred = audit.write_report(target_date)

    assert first_deferred["raw_row_exclusion"]["application_state"] == (
        "deferred_writer_active"
    )
    assert first_deferred["raw_row_exclusion_history"][0]["manifest_path"] == (
        applied_manifest
    )
    assert second_deferred["raw_row_exclusion"]["application_state"] == (
        "deferred_writer_active"
    )
    assert second_deferred["raw_row_exclusion_history"][0]["manifest_path"] == (
        applied_manifest
    )


def test_observation_source_quality_excludes_raw_rows_from_gzip_source(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    valid_id = "swing_dry_run:2026-06-04:KOSPI_ML:004710:exit:1780556300"
    _write_events_gzip(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
                record_id=1,
            ),
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": valid_id,
                    "source_record_id": valid_id,
                    "source_stage": "exit",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.write_report("2026-06-04")
    raw_path = tmp_path / "pipeline_events" / "pipeline_events_2026-06-04.jsonl.gz"
    with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    manifest = json.loads(
        Path(report["raw_row_exclusion"]["manifest_path"]).read_text(encoding="utf-8")
    )
    with gzip.open(manifest["backup_path"], "rt", encoding="utf-8") as handle:
        backup_rows = [json.loads(line) for line in handle if line.strip()]

    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["raw_row_exclusion_applied"] is True
    assert manifest["source_path"] == str(raw_path)
    assert [row["record_id"] for row in rows] == [2]
    assert [row["record_id"] for row in backup_rows] == [1, 2]


def test_observation_source_quality_raw_row_exclusion_summary_is_stage_generic(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    monkeypatch.setitem(
        audit.STAGE_CONTRACTS,
        "custom_runtime_context_stage",
        audit.StageContract(
            required_fields=("source_record_id", "risk_context"),
            zero_sensitive_fields=("risk_context",),
            max_zero_rate=0.0,
        ),
    )
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "custom_runtime_context_stage",
                {
                    "source_quality_route": "source_quality_blocker_or_workorder_only",
                    "source_quality_blocker": "context_not_ready",
                    "risk_context": "0",
                    "reason": "insufficient_history",
                },
                record_id=1,
            ),
            _event(
                "custom_runtime_context_stage",
                {
                    "source_record_id": "SRC-2",
                    "risk_context": "5",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.write_report("2026-06-04")
    manifest = json.loads(
        Path(report["raw_row_exclusion"]["manifest_path"]).read_text(encoding="utf-8")
    )

    assert manifest["stage_counts"] == {"custom_runtime_context_stage": 1}
    assert manifest["field_gap_counts"]["missing_fields:source_record_id"] == 1
    assert manifest["field_gap_counts"]["zero_fields:risk_context"] == 1
    assert manifest["exclusion_reasons"]["source_quality_blocker"] == 1
    assert manifest["exclusion_reasons"]["insufficient_history"] == 1
    assert manifest["exclusion_reasons"]["provenance_missing"] == 1
    assert manifest["producer_hint"][0]["stage"] == "custom_runtime_context_stage"


def test_observation_source_quality_raw_row_exclusion_marks_market_halt_overlap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    market_halt_dir = tmp_path / "source_quality" / "market_halt_windows" / "windows"
    market_halt_dir.mkdir(parents=True, exist_ok=True)
    (market_halt_dir / "2026-06-08.json").write_text(
        json.dumps(
            {
                "report_type": "market_halt_windows",
                "target_date": "2026-06-08",
                "windows": [
                    {
                        "context_type": "market_halt_or_circuit_window",
                        "source": "operator_confirmed_intraday_circuit_breaker",
                        "halt_started_at": "2026-06-08T09:03:42",
                        "continuous_trading_halted_until": "2026-06-08T09:23:42",
                        "single_price_order_acceptance_until": "2026-06-08T09:33:42",
                        "normal_flow_check_after": "2026-06-08T09:35:00",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rows = []
    base_fields = {
        "latest_strength": "0.0",
        "buy_pressure_10t": "0.00",
        "distance_from_day_high_pct": "0.000",
        "intraday_range_pct": "0.000",
        "metric_role": "risk_context",
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
        "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        "threshold_family": "strength_momentum_soft_gate_p1",
        "gate_action": "source_quality_block",
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "reason": "insufficient_history",
        "quote_age_ms": 500.0,
        "tick_latest_age_ms": 1000.0,
        "tick_sample_count": 3,
        "tick_window_sample_count": 3,
        "tick_window_span_sec": 5.0,
        "sample_count": 3,
        "window_span_sec": 5.0,
        "snapshot_source": "ws_snapshot_input",
        "refresh_applied": False,
        "refresh_reason": "not_attempted_no_refresh_fields",
        "refresh_age_ms": "not_available_refresh_age_ms",
        "stability_window_result": "window_available",
        "stability_window_reason": "window_samples_present",
        "stability_sample_count": 3,
        "blocked_gate_quality_stage": "strength_momentum",
        "window_buy_value": 0,
        "window_buy_ratio": "0.00",
        "window_exec_buy_ratio": "0.00",
        "window_net_buy_qty": 0,
        "strength_momentum_reason": "insufficient_history",
    }
    for idx in range(10):
        row = _event("blocked_strength_momentum", dict(base_fields), record_id=idx + 1)
        row["emitted_at"] = f"2026-06-08T09:{6 + idx:02d}:00"
        row["emitted_date"] = "2026-06-08"
        rows.append(row)
    good_row = _event(
        "blocked_strength_momentum",
        {**base_fields, "intraday_range_pct": "5.000"},
        record_id=99,
    )
    good_row["emitted_at"] = "2026-06-08T09:40:00"
    good_row["emitted_date"] = "2026-06-08"
    rows.append(good_row)
    _write_events(tmp_path, "2026-06-08", rows)

    report = audit.write_report("2026-06-08")
    manifest = json.loads(
        Path(report["raw_row_exclusion"]["manifest_path"]).read_text(encoding="utf-8")
    )

    assert manifest["market_halt_or_circuit_window_overlap"] is True
    context = manifest["market_halt_or_circuit_context"]
    assert context["classification"] == "market_halt_or_circuit_window_overlap"
    assert context["overlap_excluded_row_count"] == 10
    assert context["after_normal_flow_excluded_row_count"] == 0
    assert report["raw_row_exclusion"]["market_halt_or_circuit_window_overlap"] is True


def test_observation_source_quality_does_not_exclude_rows_when_contract_passes_tolerance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    monkeypatch.setitem(
        audit.STAGE_CONTRACTS,
        "tolerated_contract_stage",
        audit.StageContract(required_fields=("source_id",), max_missing_rate=0.5),
    )
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event("tolerated_contract_stage", {"source_id": "SRC-1"}, record_id=1),
            _event("tolerated_contract_stage", {}, record_id=2),
        ],
    )

    report = audit.write_report("2026-06-04")
    raw_path = tmp_path / "pipeline_events" / "pipeline_events_2026-06-04.jsonl"
    rows = [
        json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()
    ]

    assert report["stage_contracts"]["tolerated_contract_stage"]["status"] == "pass"
    assert report["summary"]["raw_row_exclusion_applied"] is False
    assert report["summary"]["hard_blocking_excluded_row_count"] == 0
    assert len(rows) == 2


def test_observation_source_quality_accepts_scalping_scanner_watching_runtime_skip(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-19",
        [
            _event(
                "scalping_scanner_watching_runtime_skip",
                {
                    "metric_role": "funnel_count",
                    "decision_authority": "real_scalping_scanner_runtime_watchlist_observation_only",
                    "window_policy": "intraday_runtime_watchlist",
                    "sample_floor": "not_applicable_runtime_observation",
                    "primary_decision_metric": "skip_reason",
                    "source_quality_gate": "scalping_scanner_watching_runtime_skip_contract",
                    "source_quality_route": "runtime_watchlist_skip_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "skip_reason": "ws_snapshot_missing_or_zero",
                    "scanner_promotion_id": "SCANPROM-000037-1000000",
                    "scanner_promotion_emitted_epoch": "1000.000",
                    "source_signature": "PRICE_JUMP_START",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                    "runtime_record_id": 77,
                    "entry_armed_at_epoch": 1000.0,
                    "ws_curr": "not_applicable_ws_curr",
                },
            )
        ],
    )

    report = audit.write_report("2026-06-19")

    contract = report["stage_contracts"]["scalping_scanner_watching_runtime_skip"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_accepts_scanner_skip_without_promotion_id_when_armed(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-19",
        [
            _event(
                "scalping_scanner_watching_runtime_skip",
                {
                    "metric_role": "funnel_count",
                    "decision_authority": "real_scalping_scanner_runtime_watchlist_observation_only",
                    "window_policy": "intraday_runtime_watchlist",
                    "sample_floor": "not_applicable_runtime_observation",
                    "primary_decision_metric": "skip_reason",
                    "source_quality_gate": "scalping_scanner_watching_runtime_skip_contract",
                    "source_quality_route": "runtime_watchlist_skip_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "skip_reason": "ws_snapshot_missing_or_zero",
                    "scanner_promotion_id": "not_applicable_scanner_promotion_id",
                    "scanner_promotion_emitted_epoch": "not_applicable_scanner_promotion_emitted_epoch",
                    "source_signature": "not_applicable_source_signature",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                    "runtime_record_id": 78,
                    "entry_armed_at_epoch": 1000.0,
                    "ws_curr": "not_applicable_ws_curr",
                },
            )
        ],
    )

    report = audit.write_report("2026-06-19")

    contract = report["stage_contracts"]["scalping_scanner_watching_runtime_skip"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_accepts_scalping_scanner_watch_eviction(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-22",
        [
            _event(
                "scalping_scanner_watch_eviction",
                {
                    "metric_role": "runtime_watchlist_pool_management",
                    "decision_authority": "real_scalping_scanner_watch_eviction_pool_management_only",
                    "window_policy": "intraday_runtime_watchlist",
                    "sample_floor": "not_applicable_runtime_pool_management",
                    "primary_decision_metric": "eviction_reason",
                    "source_quality_gate": "scalping_scanner_watch_eviction_contract",
                    "source_quality_route": "runtime_watchlist_eviction_pool_management_only",
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "eviction_reason": "terminal_blocker_repeated",
                    "eviction_policy_version": "scalping_scanner_watch_eviction_v3",
                    "eviction_attempt_count": 2,
                    "terminal_stage": "blocked_strength_momentum",
                    "terminal_reason": "below_window_buy_value",
                    "fresh_input_confirmed": True,
                    "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
                    "stale_age_sec": "not_applicable_stale_age_sec",
                    "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
                    "cooldown_remaining_sec": "not_applicable_cooldown_remaining_sec",
                    "runtime_record_id": 77,
                    "stock_code": "123456",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                },
            ),
            _event(
                "scalping_scanner_watch_eviction",
                {
                    "metric_role": "runtime_watchlist_pool_management",
                    "decision_authority": "real_scalping_scanner_watch_eviction_pool_management_only",
                    "window_policy": "intraday_runtime_watchlist",
                    "sample_floor": "not_applicable_runtime_pool_management",
                    "primary_decision_metric": "eviction_reason",
                    "source_quality_gate": "scalping_scanner_watch_eviction_contract",
                    "source_quality_route": "runtime_watchlist_eviction_pool_management_only",
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "eviction_reason": "source_quality_unresolved",
                    "eviction_policy_version": "scalping_scanner_watch_eviction_v3",
                    "eviction_attempt_count": 3,
                    "terminal_stage": "not_applicable_terminal_stage",
                    "terminal_reason": "insufficient_history",
                    "fresh_input_confirmed": False,
                    "stale_first_seen_epoch": "1792650000.000",
                    "stale_age_sec": 91.0,
                    "ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery",
                    "cooldown_remaining_sec": "not_applicable_cooldown_remaining_sec",
                    "runtime_record_id": 78,
                    "stock_code": "654321",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                },
            ),
        ],
    )

    report = audit.write_report("2026-06-22")

    contract = report["stage_contracts"]["scalping_scanner_watch_eviction"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_accepts_scanner_ws_backoff_watch_retention(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-07-24",
        [
            _event(
                "scalping_scanner_ws_backoff_watch_retained",
                {
                    "metric_role": "runtime_source_quality_recovery_guard",
                    "decision_authority": (
                        "real_scalping_scanner_ws_backoff_watch_retention_only"
                    ),
                    "window_policy": "same_watch_bounded_ws_recovery",
                    "sample_floor": "not_applicable_runtime_recovery_guard",
                    "primary_decision_metric": "ws_backoff_retention_age_sec",
                    "source_quality_gate": (
                        "scalping_scanner_ws_backoff_watch_retention_contract"
                    ),
                    "source_quality_route": (
                        "runtime_watch_retained_without_entry_evaluation"
                    ),
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "stale_submit_bypass,heavy_eval_bypass,score_threshold_change,"
                        "provider_route_change,order_price_change,quantity_or_cap_change,"
                        "broker_guard_change,real_execution_quality_approval"
                    ),
                    "retention_reason": ("scanner_ws_stale_backoff_bounded_recovery"),
                    "retention_first_epoch": "1000.000",
                    "retention_age_sec": 0.0,
                    "retention_min_sec": 15.0,
                    "retention_max_sec": 30.0,
                    "retention_attempt_count": 1,
                    "retention_min_count": 2,
                    "ws_backoff_until": "1120.000",
                    "fast_precheck_result": "budget_reallocated",
                    "fast_precheck_reason": "scanner_ws_stale_backoff_active",
                    "runtime_record_id": 77,
                    "stock_code": "047920",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                    "effective_venue": "KRX",
                    "venue_resolution": ("consistent_explicit:target.effective_venue"),
                },
            )
        ],
    )

    report = audit.write_report("2026-07-24")

    contract = report["stage_contracts"]["scalping_scanner_ws_backoff_watch_retained"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_accepts_krx_open_watchlist_reset(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-24",
        [
            _event(
                "krx_open_watchlist_reset",
                {
                    "metric_role": "runtime_watchlist_pool_management",
                    "decision_authority": "krx_open_watchlist_reset_pool_management_only",
                    "window_policy": "krx_open_once_per_trading_day",
                    "sample_floor": "not_applicable_runtime_pool_management",
                    "primary_decision_metric": "krx_open_reprice_watchlist_reset",
                    "source_quality_gate": "krx_open_watchlist_reset_contract",
                    "source_quality_route": "runtime_watchlist_reset_pool_management_only",
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "reset_policy_version": "krx_open_watchlist_reset_v1",
                    "reset_reason": "krx_open_reprice_watchlist_reset",
                    "reset_scope": "watching_without_position_or_order",
                    "runtime_record_id": 77,
                    "stock_code": "123456",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                },
            )
        ],
    )

    report = audit.write_report("2026-06-24")

    contract = report["stage_contracts"]["krx_open_watchlist_reset"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_accepts_scanner_promotion_latency_trace(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-24",
        [
            _event(
                "scalping_scanner_promotion_latency_trace",
                {
                    "metric_role": "funnel_count",
                    "decision_authority": "real_scalping_scanner_latency_observation_only",
                    "window_policy": "same_day_intraday_light",
                    "sample_floor": "not_applicable_runtime_observation",
                    "primary_decision_metric": "promotion_to_trace_sec",
                    "source_quality_gate": "scalping_scanner_promotion_latency_trace_contract",
                    "source_quality_route": "runtime_scanner_latency_trace_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "trace_phase": "fast_precheck",
                    "scanner_promotion_id": "SCANPROM-123456-1000",
                    "scanner_promotion_emitted_epoch": "1000.000",
                    "source_signature": "REALTIME_RANK_START",
                    "runtime_record_id": 77,
                    "stock_code": "123456",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                    "promotion_anchor_epoch": "1000.000",
                    "trace_observed_epoch": "1005.000",
                    "promotion_to_trace_sec": 5.0,
                    "promotion_to_last_0b_sec": 2.5,
                    "last_0b_to_trace_sec": 2.5,
                    "promotion_to_strength_history_sec": 3.0,
                    "strength_history_to_trace_sec": 2.0,
                    "heavy_queue_enter_epoch": "1004.000",
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "fast_precheck_reason": "fast_precheck_pass",
                    "ws_curr": 10000,
                },
            )
        ],
    )

    report = audit.write_report("2026-06-24")

    contract = report["stage_contracts"]["scalping_scanner_promotion_latency_trace"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_accepts_scalping_scanner_runtime_queue_lag(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-19",
        [
            _event(
                "scalping_scanner_runtime_queue_lag",
                {
                    "metric_role": "funnel_count",
                    "decision_authority": "real_scalping_scanner_runtime_watchlist_observation_only",
                    "window_policy": "intraday_runtime_watchlist",
                    "sample_floor": "not_applicable_runtime_observation",
                    "primary_decision_metric": "queue_lag_sec",
                    "source_quality_gate": "scalping_scanner_runtime_queue_lag_contract",
                    "source_quality_route": "runtime_watchlist_queue_lag_observation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_runtime_event:explicit_target_venue_missing"
                    ),
                    "forbidden_uses": (
                        "score_threshold_change,provider_route_change,order_price_change,"
                        "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
                    ),
                    "queue_rank": 2,
                    "scanner_queue_rank": 1,
                    "watching_count": 72,
                    "scanner_watching_count": 52,
                    "real_holding_count": 3,
                    "non_real_holding_count": 28,
                    "pre_scanner_runtime_count": 5,
                    "queue_lag_sec": 12.345,
                    "anchor_to_loop_sec": 10.0,
                    "loop_to_emit_sec": 2.345,
                    "pre_emit_delay_sec": 2.345,
                    "loop_started_epoch": "1010.000",
                    "queue_emit_epoch": "1012.345",
                    "scanner_promotion_id": "SCANPROM-000039-1000000",
                    "scanner_promotion_emitted_epoch": "1000.000",
                    "source_signature": "PRICE_JUMP_START",
                    "target_status": "WATCHING",
                    "target_strategy": "SCALPING",
                    "target_position_tag": "SCANNER",
                    "runtime_record_id": 79,
                    "entry_armed_at_epoch": 1000.0,
                    "added_time": 990.0,
                },
            )
        ],
    )

    report = audit.write_report("2026-06-19")

    contract = report["stage_contracts"]["scalping_scanner_runtime_queue_lag"]
    assert contract["status"] == "pass"
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = report["reviewed_unknown_token_findings"]
    queue_lag = next(
        item
        for item in reviewed
        if item["stage"] == "scalping_scanner_runtime_queue_lag"
    )
    assert {field["field"] for field in queue_lag["fields"]} >= {
        "venue",
        "effective_venue",
    }
    assert {field["reviewed_reason"] for field in queue_lag["fields"]} == {
        "reviewed_scanner_venue_fail_closed_provenance"
    }


def test_observation_source_quality_reviews_explicit_scanner_derived_venue_gaps(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-19",
        [
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "scanner_promotion_reanchor_effective_venue": "UNKNOWN",
                    "scanner_stale_backoff_canonical_effective_venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_runtime_event:explicit_target_venue_missing"
                    ),
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-19")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = next(
        item
        for item in report["reviewed_unknown_token_findings"]
        if item["stage"] == "scalping_scanner_fast_precheck"
    )
    assert {field["field"] for field in reviewed["fields"]} == {
        "venue",
        "effective_venue",
        "scanner_promotion_reanchor_effective_venue",
        "scanner_stale_backoff_canonical_effective_venue",
    }
    assert {field["reviewed_reason"] for field in reviewed["fields"]} == {
        "reviewed_scanner_venue_fail_closed_provenance"
    }


def test_observation_source_quality_reviews_target_attach_missing_venue_bucket(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-19",
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "market_session_bucket": "UNKNOWN",
                    "venue_resolution": "missing_tradable_explicit_venue",
                    "decision_authority": (
                        "real_scalping_scanner_runtime_watchlist_handoff_only"
                    ),
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-19")

    assert report["summary"]["unknown_token_stage_count"] == 0
    reviewed = next(
        item
        for item in report["reviewed_unknown_token_findings"]
        if item["stage"] == "scalping_scanner_runtime_target_attach"
    )
    assert {field["field"] for field in reviewed["fields"]} == {
        "venue",
        "effective_venue",
        "market_session_bucket",
    }


def test_observation_source_quality_accepts_scanner_fast_precheck_and_heavy_eval_lag(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    base_contract = {
        "metric_role": "funnel_count",
        "window_policy": "intraday_runtime_watchlist",
        "sample_floor": "not_applicable_runtime_observation",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
        ),
        "scanner_promotion_id": "SCANPROM-000081-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "source_signature": "PRICE_JUMP_START",
        "target_status": "WATCHING",
        "target_strategy": "SCALPING",
        "target_position_tag": "SCANNER",
        "runtime_record_id": 81,
    }
    _write_events(
        tmp_path,
        "2026-06-19",
        [
            _event(
                "scalping_scanner_fast_precheck",
                {
                    **base_contract,
                    "decision_authority": "real_scalping_scanner_fast_precheck_observation_only",
                    "primary_decision_metric": "fast_precheck_lag_sec",
                    "source_quality_gate": "scalping_scanner_fast_precheck_contract",
                    "source_quality_route": "runtime_watchlist_fast_precheck_observation_only",
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "fast_precheck_reason": "fast_precheck_pass",
                    "fast_precheck_seen_epoch": "1012.000",
                    "fast_precheck_lag_sec": 12.0,
                    "heavy_queue_enter_epoch": "1012.000",
                    "queue_rank": 2,
                    "scanner_queue_rank": 1,
                    "watching_count": 10,
                    "scanner_watching_count": 3,
                    "quote_age_ms": 100.0,
                    "snapshot_source": "ws_manager_latest_data",
                },
            ),
            _event(
                "scalping_scanner_heavy_eval_lag",
                {
                    **base_contract,
                    "decision_authority": "real_scalping_scanner_heavy_eval_observation_only",
                    "primary_decision_metric": "heavy_queue_wait_sec",
                    "source_quality_gate": "scalping_scanner_heavy_eval_lag_contract",
                    "source_quality_route": "runtime_watchlist_heavy_eval_lag_observation_only",
                    "heavy_queue_enter_epoch": "1012.000",
                    "heavy_eval_started_epoch": "1012.200",
                    "heavy_queue_wait_sec": 0.2,
                },
            ),
            _event(
                "scalping_scanner_heavy_eval_completion",
                {
                    **base_contract,
                    "decision_authority": "real_scalping_scanner_heavy_eval_completion_observation_only",
                    "primary_decision_metric": "heavy_handler_duration_sec",
                    "source_quality_gate": "scalping_scanner_heavy_eval_completion_contract",
                    "source_quality_route": "runtime_watchlist_heavy_eval_completion_observation_only",
                    "heavy_queue_enter_epoch": "1012.000",
                    "heavy_eval_started_epoch": "1012.200",
                    "heavy_eval_completed_epoch": "1012.550",
                    "heavy_queue_wait_sec": 0.2,
                    "heavy_handler_duration_sec": 0.35,
                    "heavy_end_to_end_sec": 0.55,
                    "heavy_eval_outcome": "WATCHING",
                    "heavy_eval_ws_snapshot_refreshed": False,
                    "heavy_eval_ws_snapshot_refresh_status": "not_applied",
                    "heavy_eval_ws_snapshot_apply_phase": "not_applied",
                },
            ),
        ],
    )

    report = audit.write_report("2026-06-19")

    assert (
        report["stage_contracts"]["scalping_scanner_fast_precheck"]["status"] == "pass"
    )
    assert (
        report["stage_contracts"]["scalping_scanner_heavy_eval_lag"]["status"] == "pass"
    )
    assert (
        report["stage_contracts"]["scalping_scanner_heavy_eval_completion"]["status"]
        == "pass"
    )
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_accepts_swing_loss_reentry_fallback_source(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fallback_id = "swing_dry_run:2026-06-04:KOSPI_ML:004710:exit:1780556300"
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": fallback_id,
                    "source_record_id": fallback_id,
                    "source_stage": "exit",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    contract = report["stage_contracts"]["swing_same_symbol_loss_reentry_cooldown"]
    assert contract["status"] == "pass"
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_routes_entry_arm_and_loss_diagnostics_by_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(60):
        rows.extend(
            [
                _event(
                    "entry_armed",
                    {
                        "ai_score": "82.0",
                        "ratio": "0.1000",
                        "target_buy_price": 12000,
                        "current_vpw": "110.0",
                        "reason": "dynamic_entry",
                        "ttl_sec": 90,
                    },
                    record_id=idx * 4 + 1,
                ),
                _event(
                    "entry_armed_expired_after_wait",
                    {
                        "waited_sec": "91.0",
                        "resume_count": 1,
                        "reason": "dynamic_entry",
                    },
                    record_id=idx * 4 + 2,
                ),
                _event(
                    "loss_fallback_probe",
                    {
                        "gate_allowed": False,
                        "gate_reason": "fallback_disabled",
                        "fallback_candidate": True,
                        "fallback_reason": "loss_recovery",
                        "profit_rate": "-0.2",
                        "peak_profit": "0.1",
                    },
                    record_id=idx * 4 + 3,
                ),
                _event(
                    "soft_stop_whipsaw_confirmation",
                    {
                        "threshold_family": "soft_stop_whipsaw_confirmation",
                        "threshold_version": "v1",
                        "threshold_calibration_state": "selected",
                        "profit_rate": "-0.3",
                        "flow_state": "recovery",
                        "exit_rule_candidate": "soft_stop",
                    },
                    record_id=idx * 4 + 4,
                ),
            ]
        )
    _write_events(tmp_path, "2026-05-15", rows)

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    assert report["stage_contracts"]["entry_armed"]["status"] == "pass"
    assert (
        report["stage_contracts"]["entry_armed_expired_after_wait"]["status"] == "pass"
    )
    assert report["stage_contracts"]["loss_fallback_probe"]["status"] == "pass"
    assert (
        report["stage_contracts"]["soft_stop_whipsaw_confirmation"]["status"] == "pass"
    )


def test_observation_source_quality_audit_normalizes_optional_holding_context(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "loss_fallback_probe",
            {
                "gate_allowed": False,
                "gate_reason": "add_judgment_locked",
                "fallback_candidate": False,
                "fallback_reason": "-",
                "profit_rate": "-1.0",
                "peak_profit": "0.0",
            },
        ),
        _event(
            "soft_stop_whipsaw_confirmation",
            {
                "threshold_family": "soft_stop_whipsaw_confirmation",
                "threshold_version": "runtime_default",
                "threshold_calibration_state": "runtime_default",
                "profit_rate": "-1.5",
                "flow_state": "-",
                "exit_rule_candidate": "scalp_soft_stop_pct",
            },
            record_id=2,
        ),
    ]
    _write_events(tmp_path, "2026-05-15", rows)

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["stage_contracts"]["loss_fallback_probe"]["status"] == "pass"
    assert (
        report["stage_contracts"]["soft_stop_whipsaw_confirmation"]["status"] == "pass"
    )


def test_observation_source_quality_audit_normalizes_legacy_flow_state_label():
    normalized = audit._normalized_fields_for_contract(
        "soft_stop_whipsaw_confirmation",
        {
            "threshold_family": "soft_stop_whipsaw_confirmation",
            "threshold_version": "runtime_default",
            "threshold_calibration_state": "runtime_default",
            "profit_rate": "-1.5",
            "flow_state": "흡수",
            "exit_rule_candidate": "scalp_soft_stop_pct",
        },
    )

    assert normalized["flow_state"] == "absorption"
    assert normalized["raw_flow_state"] == "흡수"
    assert (
        normalized["flow_state_source"] == "audit_normalized_legacy_runtime_flow_state"
    )


def test_observation_source_quality_audit_accepts_score_vpw_prior_sentinel():
    normalized = audit._normalized_fields_for_contract(
        "swing_probe_entry_candidate",
        {
            "gatekeeper_action": "NOT_EVALUATED_SCORE_VPW_PRIOR",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
    )

    assert normalized["action_key"] == "not_evaluated_score_vpw_prior"
    assert "invalid_gatekeeper_action_label" not in normalized
    assert normalized["actual_order_submitted"] is False
    assert normalized["broker_order_forbidden"] is True
    assert normalized["runtime_effect"] is False


def test_observation_source_quality_audit_accepts_canonical_unknown_flow_state():
    normalized = audit._normalized_fields_for_contract(
        "holding_flow_override_review",
        {
            "flow_state": "unknown_flow_state",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
    )

    assert normalized["flow_state"] == "unknown_flow_state"
    assert "invalid_flow_state_label" not in normalized
    assert "source_quality_blocker" not in normalized


def test_observation_source_quality_audit_fails_unknown_flow_state_label(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "soft_stop_whipsaw_confirmation",
                {
                    "threshold_family": "soft_stop_whipsaw_confirmation",
                    "threshold_version": "runtime_default",
                    "threshold_calibration_state": "runtime_default",
                    "profit_rate": "-1.5",
                    "flow_state": "confirming",
                    "exit_rule_candidate": "scalp_soft_stop_pct",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["soft_stop_whipsaw_confirmation"]
    assert report["status"] == "fail"
    assert contract["status"] == "fail"
    assert contract["invalid_label_violations"] == {"flow_state": 1.0}
    assert report["invalid_label_findings"][0]["field"] == "flow_state"
    assert report["summary"]["tuning_input_allowed"] is False
    assert "soft_stop_whipsaw_confirmation" in report["summary"]["hard_blocking_stages"]


def test_observation_source_quality_audit_fails_unknown_gatekeeper_action_label(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "blocked_gatekeeper_reject",
                {
                    "action": "ambiguous_chase",
                    "cooldown_policy": "pullback_wait",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["blocked_gatekeeper_reject"]
    assert report["status"] == "fail"
    assert contract["status"] == "fail"
    assert contract["invalid_label_violations"] == {"action": 1.0}
    assert report["invalid_label_findings"][0]["field"] == "gatekeeper_action"


def test_observation_source_quality_audit_fails_unknown_labels_on_uncontracted_stage(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "holding_flow_override_review",
                {
                    "flow_state": "confirming",
                    "flow_action": "HOLD",
                },
            ),
            _event(
                "swing_probe_entry_candidate",
                {
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "in_memory_probe_only",
                    "probe_origin_stage": "blocked_gatekeeper_reject",
                    "gatekeeper_action": "None",
                    "curr_price": "1000",
                    "assumed_fill_price": "1000",
                    "score": "50",
                    "v_pw": "120",
                    "virtual_budget_override": True,
                    "budget_authority": "sim_virtual_not_real_orderable_amount",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["status"] == "fail"
    assert report["invalid_label_findings"] == [
        {
            "stage": "holding_flow_override_review",
            "field": "flow_state",
            "count": 1,
            "examples": ["confirming"],
            "routing": "source_quality_blocker",
        }
    ]


def test_observation_source_quality_audit_routes_holding_diagnostics_by_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "ai_holding_fast_reuse_band",
            {
                "metric_role": "ops_volume_diagnostic",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                "source_quality_route": "source_quality_blocker_or_workorder_only",
                "telemetry_only": True,
                "action": "skip",
            },
        ),
        _event(
            "soft_stop_expert_shadow",
            {
                "metric_role": "ops_volume_diagnostic",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                "source_quality_route": "source_quality_blocker_or_workorder_only",
                "shadow_only": True,
                "hierarchy": "mae_mfe_quantile|recovery_probability|partial_de_risk",
            },
        ),
        _event(
            "adverse_fill_observed",
            {
                "observe_only": True,
                "feature_valid": True,
                "buy_pressure_10t": 62.0,
                "net_aggressive_delta_10t": 300,
                "large_sell_print_detected": False,
                "curr_vs_micro_vwap_bp": -2.0,
                "tick_aggressor_trusted_count": 4,
                "tick_aggressor_pressure_usable": True,
                "micro_vwap_available": True,
                "minute_candle_context_quality": "fresh_bar_window",
                "minute_candle_window_fresh": True,
                "minute_candle_latest_age_ms": 12000,
                "micro_context_usable": True,
                "reversal_feature_source_quality": "usable",
                "reversal_feature_stale_reason": "-",
            },
        ),
        _event(
            "soft_stop_absorption_probe",
            {
                "profit_rate": "-1.83",
                "soft_stop_pct": "-1.50",
                "absorption_score": 3,
                "exclusion_reason": "-",
                "should_extend": True,
                "hierarchy": "stop_arbitration|thesis_invalidation|orderbook_absorption",
                "curr_vs_micro_vwap_bp": -2.0,
                "tick_aggressor_trusted_count": 4,
                "tick_aggressor_pressure_usable": True,
                "micro_vwap_available": True,
                "minute_candle_context_quality": "fresh_bar_window",
                "minute_candle_window_fresh": True,
                "minute_candle_latest_age_ms": 12000,
                "micro_context_usable": True,
                "reversal_feature_source_quality": "usable",
                "reversal_feature_stale_reason": "-",
            },
        ),
        _event(
            "holding_flow_override_candidate_cleared",
            {
                "metric_role": "funnel_count",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                "source_quality_route": "source_quality_blocker_or_workorder_only",
                "reason": "exit_rule_changed",
                "previous_key": "ABC:1",
            },
        ),
    ]
    _write_events(
        tmp_path,
        "2026-05-15",
        [dict(row, record_id=idx) for idx, row in enumerate(rows * 55)],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    assert report["stage_contracts"]["ai_holding_fast_reuse_band"]["status"] == "pass"
    assert report["stage_contracts"]["soft_stop_expert_shadow"]["status"] == "pass"
    assert report["stage_contracts"]["adverse_fill_observed"]["status"] == "pass"
    assert report["stage_contracts"]["soft_stop_absorption_probe"]["status"] == "pass"
    assert (
        report["stage_contracts"]["holding_flow_override_candidate_cleared"]["status"]
        == "pass"
    )
    assert report["status"] == "pass"


def test_observation_source_quality_audit_blocks_soft_stop_absorption_without_micro_vwap_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "soft_stop_absorption_probe",
                {
                    "profit_rate": "-1.83",
                    "soft_stop_pct": "-1.50",
                    "absorption_score": 3,
                    "should_extend": True,
                    "hierarchy": "stop_arbitration|thesis_invalidation|orderbook_absorption",
                    "curr_vs_micro_vwap_bp": "10.0",
                    "tick_aggressor_trusted_count": 4,
                    "tick_aggressor_pressure_usable": True,
                    "micro_vwap_available": False,
                    "minute_candle_context_quality": "stale_bar_window",
                    "minute_candle_window_fresh": False,
                    "minute_candle_latest_age_ms": 600000,
                    "micro_context_usable": False,
                    "reversal_feature_source_quality": "stale",
                    "reversal_feature_stale_reason": "micro_vwap_unavailable",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["soft_stop_absorption_probe"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "soft_stop_absorption_probe"
    assert exclusion["invalid_fields"] == ["minute_candle_window_fresh_contract"]


def test_observation_source_quality_audit_blocks_soft_stop_dynamic_grace_without_micro_vwap_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "soft_stop_dynamic_grace",
                {
                    "soft_stop_final_action": "confirm_20s",
                    "soft_stop_extension_source": "dynamic_modifier",
                    "soft_stop_extension_sec": 20,
                    "soft_stop_extension_veto_reasons": "-",
                    "soft_stop_absorption_score": 3,
                    "soft_stop_thesis_invalidated": False,
                    "soft_stop_dynamic_modifier_applied": True,
                    "soft_stop_dynamic_modifier_skip_reason": "-",
                    "soft_stop_dynamic_grace_applied": True,
                    "soft_stop_dynamic_grace_reason": "base_micro_confirmed_soft_stop_dynamic_grace",
                    "soft_stop_dynamic_grace_sec": 45,
                    "soft_stop_dynamic_grace_ai_score_usable": True,
                    "soft_stop_dynamic_grace_ai_score_source": "live",
                    "soft_stop_dynamic_grace_ai_score_data_quality": "fresh",
                    "curr_vs_micro_vwap_bp": "12.0",
                    "tick_aggressor_trusted_count": 4,
                    "tick_aggressor_pressure_usable": True,
                    "micro_vwap_available": False,
                    "minute_candle_context_quality": "stale_bar_window",
                    "minute_candle_window_fresh": False,
                    "minute_candle_latest_age_ms": 600000,
                    "micro_context_usable": False,
                    "reversal_feature_source_quality": "stale",
                    "exit_rule_candidate": "scalp_soft_stop_pct",
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["soft_stop_dynamic_grace"]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "soft_stop_dynamic_grace"
    assert exclusion["invalid_fields"] == ["minute_candle_window_fresh_contract"]


def test_observation_source_quality_audit_blocks_never_green_clamp_without_micro_vwap_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "holding_flow_override_clamped_never_green_loss",
                {
                    "exit_rule": "scalp_soft_stop_pct",
                    "flow_action": "HOLD",
                    "flow_state": "watch",
                    "flow_score": 55,
                    "defer_reason": "review_interval_hold",
                    "holding_flow_override_defer_count": 2,
                    "curr_vs_micro_vwap_bp": "-4.00",
                    "previous_defer_micro_vwap_bp": "-1.00",
                    "micro_vwap_available": False,
                    "minute_candle_context_quality": "stale_bar_window",
                    "minute_candle_window_fresh": False,
                    "minute_candle_latest_age_ms": 600000,
                    "micro_context_usable": False,
                    "reversal_feature_source_quality": "stale",
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "decision_authority": "real_scalping_holding_defer_clamp",
                    "threshold_family": "never_green_defer_clamp_runtime",
                    "source_quality_gate": "never_green_defer_clamp_contract",
                    "forbidden_uses": "threshold_mutation/order_guard_bypass/provider_route_change/bot_restart",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"][
        "holding_flow_override_clamped_never_green_loss"
    ]
    assert contract["status"] == "fail"
    assert (
        contract["invalid_label_violations"]["minute_candle_window_fresh_contract"]
        == 1.0
    )
    assert report["summary"]["tuning_input_allowed"] is False
    exclusion = report["hard_blocking_row_exclusions"][0]
    assert exclusion["stage"] == "holding_flow_override_clamped_never_green_loss"
    assert exclusion["invalid_fields"] == ["minute_candle_window_fresh_contract"]


def test_observation_source_quality_audit_routes_probe_state_persisted_by_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "swing_probe_state_persisted",
                {
                    "simulation_book": "swing_intraday_probe",
                    "simulation_owner": "owner",
                    "reason": "probe_scale_in",
                    "active_count": 1,
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    persisted = report["stage_contracts"]["swing_probe_state_persisted"]
    assert persisted["status"] == "warning"
    assert "metric_role" in persisted["missing_violations"]


def test_observation_source_quality_audit_accepts_pre_ai_and_pre_submit_gate_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    gate_quality = {
        "quote_age_ms": 500.0,
        "tick_latest_age_ms": 1000.0,
        "tick_sample_count": 3,
        "tick_window_sample_count": 3,
        "tick_window_span_sec": 5.0,
        "sample_count": 3,
        "window_span_sec": 5.0,
        "snapshot_source": "ws_manager_latest_data",
        "refresh_applied": True,
        "refresh_reason": "latest_ws_snapshot_fresh",
        "refresh_age_ms": 300.0,
        "stability_window_result": "window_available",
        "stability_window_reason": "window_samples_present",
        "stability_sample_count": 3,
        "blocked_gate_quality_stage": "liquidity",
    }
    overlap = {
        "latest_strength": "105.0",
        "buy_pressure_10t": "0.600",
        "distance_from_day_high_pct": "0.50",
        "intraday_range_pct": "2.00",
    }
    risk_context = {
        "metric_role": "risk_context",
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
        "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        "threshold_family": "liquidity_pre_submit_guard_p1",
        "gate_action": "risk_context_only",
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-05-18",
        [
            _event(
                "blocked_liquidity",
                {
                    **risk_context,
                    **gate_quality,
                    "liquidity_value": 100_000_000,
                    "min_liquidity": 500_000_000,
                    "ask_tot": 10_000,
                    "bid_tot": 12_000,
                    "liquidity_orderbook_source_quality": "valid_orderbook_totals",
                },
            ),
            _event(
                "blocked_strength_momentum",
                {
                    **risk_context,
                    **overlap,
                    **{
                        **gate_quality,
                        "blocked_gate_quality_stage": "strength_momentum",
                    },
                    "threshold_family": "strength_momentum_soft_gate_p1",
                    "window_buy_value": 100_000_000,
                    "window_buy_ratio": "55.00",
                    "window_exec_buy_ratio": "52.00",
                    "window_net_buy_qty": 1000,
                    "strength_momentum_reason": "below_window_buy_value",
                },
            ),
            _event(
                "strength_momentum_stability_recheck_pending",
                {
                    **risk_context,
                    **{
                        **gate_quality,
                        "blocked_gate_quality_stage": "strength_momentum",
                    },
                    "threshold_family": "strength_momentum_soft_gate_p1",
                    "gate_action": "stability_recheck_pending",
                    "window_buy_value": 0,
                    "window_buy_ratio": "0.00",
                    "window_exec_buy_ratio": "0.00",
                    "window_net_buy_qty": 0,
                    "strength_momentum_reason": "insufficient_history",
                    "recheck_reason": "transient_strength_window_unstable",
                    "recheck_after_epoch": "1002.000",
                    "recheck_delay_sec": 2,
                    "recheck_attempt_count": 1,
                    "recheck_max_attempts": 1,
                },
            ),
            _event(
                "blocked_vpw",
                {
                    **risk_context,
                    **overlap,
                    **{**gate_quality, "blocked_gate_quality_stage": "vpw"},
                    "threshold_family": "strength_momentum_soft_gate_p1",
                },
            ),
            _event(
                "blocked_overbought",
                {
                    **risk_context,
                    **overlap,
                    **{**gate_quality, "blocked_gate_quality_stage": "overbought"},
                    "threshold_family": "overbought_pullback_guard_p1",
                },
            ),
            _event(
                "pre_submit_liquidity_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "order_safety_pre_submit_only",
                    "runtime_effect": "pre_submit_block",
                    "forbidden_uses": "provider_route_change/bot_restart/runtime_threshold_apply_without_approval",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "gate_action": "pre_submit_block",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "liquidity_value": 100_000_000,
                    "min_liquidity": 500_000_000,
                },
                record_id=2,
            ),
            _event(
                "caution_weak_liquidity_entry_block",
                {
                    "metric_role": "safety_veto",
                    "decision_authority": "real_scalping_pre_submit_quality_guard",
                    "runtime_effect": True,
                    "forbidden_uses": "provider_route_change/bot_restart/runtime_threshold_apply_without_approval",
                    "threshold_family": "caution_weak_liquidity_entry_block",
                    "gate_action": "pre_submit_block",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "block_reason": "caution_weak_liquidity_not_available",
                    "rising_missed_entry_lineage": True,
                    "caution_weak_liquidity_block_latency_state": "CAUTION",
                    "caution_weak_liquidity_block_entry_price_gap_profile": "weak_liquidity_wide_spread",
                    "caution_weak_liquidity_block_liquidity_action": "NOT_AVAILABLE",
                    "caution_weak_liquidity_block_liquidity_reason": "liquidity_not_available",
                },
                record_id=3,
            ),
            _event(
                "pre_submit_entry_ai_authority_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "real_buy_submit_source_quality_guard",
                    "runtime_effect": True,
                    "forbidden_uses": "score_threshold_mutation,provider_route_change,broker_guard_bypass",
                    "threshold_family": "pre_submit_entry_ai_authority_guard",
                    "source_quality_gate": "pre_submit_entry_ai_authority_contract",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "block_reason": "entry_ai_score_unavailable",
                    "entry_ai_submit_authority_score": "0.0",
                    "entry_ai_submit_authority_action": "not_evaluated",
                    "entry_ai_submit_authority_reason": "entry_ai_score_unavailable",
                    "entry_ai_submit_authority_result_source": "not_available",
                },
                record_id=4,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-18")

    assert report["stage_contracts"]["blocked_liquidity"]["status"] == "pass"
    assert report["stage_contracts"]["blocked_strength_momentum"]["status"] == "pass"
    assert (
        report["stage_contracts"]["strength_momentum_stability_recheck_pending"][
            "status"
        ]
        == "pass"
    )
    assert report["stage_contracts"]["blocked_vpw"]["status"] == "pass"
    assert report["stage_contracts"]["blocked_overbought"]["status"] == "pass"
    assert (
        report["stage_contracts"]["pre_submit_liquidity_guard_block"]["status"]
        == "pass"
    )
    assert (
        report["stage_contracts"]["caution_weak_liquidity_entry_block"]["status"]
        == "pass"
    )
    assert (
        report["stage_contracts"]["pre_submit_entry_ai_authority_guard_block"]["status"]
        == "pass"
    )


def test_observation_source_quality_audit_fails_pre_ai_broker_authority_contract(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    gate_quality = {
        "quote_age_ms": 500.0,
        "tick_latest_age_ms": 1000.0,
        "tick_sample_count": 3,
        "tick_window_sample_count": 3,
        "tick_window_span_sec": 5.0,
        "sample_count": 3,
        "window_span_sec": 5.0,
        "snapshot_source": "ws_snapshot_input",
        "refresh_applied": False,
        "refresh_reason": "not_attempted_no_refresh_fields",
        "refresh_age_ms": "not_available_refresh_age_ms",
        "stability_window_result": "window_available",
        "stability_window_reason": "window_samples_present",
        "stability_sample_count": 3,
        "blocked_gate_quality_stage": "strength_momentum",
    }
    _write_events(
        tmp_path,
        "2026-05-18",
        [
            _event(
                "blocked_strength_momentum",
                {
                    "metric_role": "risk_context",
                    "decision_authority": "source_quality_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "threshold_family": "strength_momentum_soft_gate_p1",
                    "gate_action": "risk_context_only",
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": False,
                    "latest_strength": "105.0",
                    "buy_pressure_10t": "0.600",
                    "distance_from_day_high_pct": "0.50",
                    "intraday_range_pct": "2.00",
                    "window_buy_value": 100_000_000,
                    "window_buy_ratio": "55.00",
                    "window_exec_buy_ratio": "52.00",
                    "window_net_buy_qty": 1000,
                    "strength_momentum_reason": "below_window_buy_value",
                    **gate_quality,
                },
            )
        ],
    )

    pre_exclusion = audit.build_observation_source_quality_audit("2026-05-18")
    contract = pre_exclusion["stage_contracts"]["blocked_strength_momentum"]

    assert contract["status"] == "fail"
    assert contract["invalid_label_violations"] == {
        "pre_ai_broker_order_forbidden_contract": 1.0
    }

    report = audit.write_report("2026-05-18")
    assert report["summary"]["raw_row_exclusion_applied"] is True
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_accepts_scalp_sim_stage_contracts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": False,
        "sim_record_id": "SIM-1",
    }
    liquidity_guard_fields = {
        **fields,
        "decision_authority": "sim_submit_path_observation_only",
        "threshold_family": "liquidity_pre_submit_guard_p1",
        "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
        "sim_pre_submit_liquidity_reason": "below_min_liquidity",
        "sim_liquidity_value": 100_000_000,
        "sim_min_liquidity": 500_000_000,
        "sim_parent_record_id": 1,
    }
    overbought_guard_fields = {
        **fields,
        "decision_authority": "sim_submit_path_observation_only",
        "threshold_family": "overbought_pullback_guard_p1",
        "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
        "sim_pre_submit_overbought_reason": "overbought_ok",
        "sim_overbought_risk_state": "pullback_observed",
        "sim_parent_record_id": 1,
    }
    overbought_block_fields = {
        **overbought_guard_fields,
        "sim_pre_submit_overbought_guard_action": "WOULD_BLOCK",
        "sim_pre_submit_overbought_reason": "pullback_or_rebreak_not_confirmed",
        "sim_overbought_risk_state": "pullback_required",
    }
    _write_events(
        tmp_path,
        "2026-05-20",
        [
            _event("scalp_sim_entry_armed", fields, record_id=1),
            _event(
                "scalp_sim_pre_submit_liquidity_guard_would_block",
                liquidity_guard_fields,
                record_id=11,
            ),
            _event(
                "scalp_sim_pre_submit_liquidity_guard_would_pass",
                {
                    **liquidity_guard_fields,
                    "sim_pre_submit_liquidity_guard_action": "WOULD_PASS",
                    "sim_pre_submit_liquidity_reason": "liquidity_ok",
                    "sim_liquidity_value": 800_000_000,
                },
                record_id=12,
            ),
            _event(
                "scalp_sim_pre_submit_liquidity_guard_unknown",
                {
                    **liquidity_guard_fields,
                    "sim_pre_submit_liquidity_guard_action": "WOULD_UNKNOWN",
                    "sim_pre_submit_liquidity_reason": "liquidity_unknown",
                    "sim_liquidity_value": "UNKNOWN",
                },
                record_id=15,
            ),
            _event(
                "scalp_sim_pre_submit_overbought_guard_would_block",
                overbought_block_fields,
                record_id=13,
            ),
            _event(
                "scalp_sim_pre_submit_overbought_guard_would_pass",
                overbought_guard_fields,
                record_id=14,
            ),
            _event("scalp_sim_buy_order_virtual_pending", fields, record_id=2),
            _event("scalp_sim_buy_order_assumed_filled", fields, record_id=3),
            _event("scalp_sim_entry_ai_price_skip_order", fields, record_id=4),
            _event("scalp_sim_holding_started", fields, record_id=5),
            _event("scalp_sim_sell_order_assumed_filled", fields, record_id=6),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-20")

    for stage in (
        "scalp_sim_entry_armed",
        "scalp_sim_pre_submit_liquidity_guard_would_block",
        "scalp_sim_pre_submit_liquidity_guard_would_pass",
        "scalp_sim_pre_submit_liquidity_guard_unknown",
        "scalp_sim_pre_submit_overbought_guard_would_block",
        "scalp_sim_pre_submit_overbought_guard_would_pass",
        "scalp_sim_buy_order_virtual_pending",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_entry_ai_price_skip_order",
        "scalp_sim_holding_started",
        "scalp_sim_sell_order_assumed_filled",
    ):
        assert report["stage_contracts"][stage]["status"] == "pass"


def test_observation_source_quality_audit_fails_mismatched_sim_submit_guard_stage_action(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-20",
        [
            _event(
                "scalp_sim_pre_submit_liquidity_guard_would_pass",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_submit_path_observation_only",
                    "runtime_effect": False,
                    "sim_record_id": "SIM-1",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
                    "sim_pre_submit_liquidity_reason": "below_min_liquidity",
                    "sim_liquidity_value": 100_000_000,
                    "sim_min_liquidity": 500_000_000,
                    "sim_parent_record_id": 1,
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-20")
    contract = report["stage_contracts"][
        "scalp_sim_pre_submit_liquidity_guard_would_pass"
    ]

    assert contract["status"] == "fail"
    assert contract["invalid_label_counts"]["sim_submit_guard_action_contract"] == 1


def test_observation_source_quality_audit_contracts_sim_budget_and_risk_context(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    budget_fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": "sim_ai_live_call_only",
        "sim_record_id": "SIM-1",
        "entry_adm_candidate_id": "ADM-1",
    }
    risk_fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": "sim_panic_action_deduped",
        "threshold_family": "panic_lifecycle_actuator",
        "source_stage": "scalp_sim_holding_started",
        "sim_record_id": "SIM-1",
    }
    _write_events(
        tmp_path,
        "2026-05-20",
        [
            _event("scalp_sim_ai_holding_live_call", budget_fields, record_id=1),
            _event("scalp_sim_ai_holding_deferred", budget_fields, record_id=2),
            _event("sim_ai_budget_exhausted", budget_fields, record_id=3),
            _event("sim_ai_critical_bypass", budget_fields, record_id=4),
            _event("scalp_sim_panic_action_deduped", risk_fields, record_id=5),
            _event("scalp_sim_panic_scale_in_blocked", risk_fields, record_id=6),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-20")

    for stage in (
        "scalp_sim_ai_holding_live_call",
        "scalp_sim_ai_holding_deferred",
        "sim_ai_budget_exhausted",
        "sim_ai_critical_bypass",
        "scalp_sim_panic_action_deduped",
        "scalp_sim_panic_scale_in_blocked",
    ):
        assert report["stage_contracts"][stage]["status"] == "pass"


def test_observation_source_quality_audit_writes_json_and_markdown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "swing_probe_entry_candidate",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                    "simulated_order": True,
                    "evidence_quality": "counterfactual_after_gap",
                    "source_record_id": "1",
                    "virtual_budget_override": True,
                    "budget_authority": "sim_virtual_not_real_orderable_amount",
                },
            )
        ],
    )

    report = audit.write_report("2026-05-15")
    json_path, md_path = audit.report_paths("2026-05-15")

    assert report["stage_contracts"]["swing_probe_entry_candidate"]["status"] == "pass"
    assert json_path.exists()
    assert md_path.exists()


def test_stdout_summary_omits_large_stage_contracts():
    report = {
        "report_type": "observation_source_quality_audit",
        "target_date": "2026-07-30",
        "status": "pass",
        "summary": {"event_count": 10, "tuning_input_allowed": True},
        "stage_contracts": {"large": {"rows": list(range(100))}},
    }

    payload = audit._stdout_report_payload(report, summary_only=True)

    assert payload["summary"]["event_count"] == 10
    assert "stage_contracts" not in payload
    assert audit._stdout_report_payload(report, summary_only=False) is report


def _write_threshold_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "threshold_cycle"
    event_dir.mkdir(parents=True)
    with (event_dir / f"threshold_events_{target_date}.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_observation_source_quality_backfill_quarantines_only_derived_bucket_interpretation(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-18",
        [
            _event(
                "scalp_sim_buy_order_assumed_filled",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_observation_only",
                    "profit_rate": "0.4",
                },
            )
        ],
    )
    _write_events(
        tmp_path,
        "2026-05-19",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "entry_adm_score_bucket": "score_unknown",
                    "entry_adm_stale_bucket": "stale_unknown",
                    "lifecycle_matrix_entry_bucket": "entry_unknown",
                },
            ),
            _event(
                "scalp_sim_pre_submit_overbought_guard_would_pass",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "sim_pre_submit_overbought_reason": "overbought_unknown",
                    "sim_overbought_context_source": "unknown",
                    "sim_overbought_source_quality": "unknown",
                },
                record_id=2,
            ),
        ],
    )
    _write_threshold_events(
        tmp_path,
        "2026-05-19",
        [
            _event(
                "scalp_sim_buy_order_assumed_filled",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_observation_only",
                },
                record_id=3,
            )
        ],
    )
    stale_report = (
        tmp_path
        / "report"
        / "scalp_entry_action_decision_matrix"
        / "scalp_entry_action_decision_matrix_2026-05-19.json"
    )
    stale_report.parent.mkdir(parents=True)
    stale_report.write_text("{}", encoding="utf-8")

    report = audit.build_observation_source_quality_backfill_audit(
        "2026-05-19",
        start_date="2026-05-18",
    )

    by_date = {item["date"]: item for item in report["date_impacts"]}
    assert by_date["2026-05-18"]["raw_sim_preserved"] is True
    assert by_date["2026-05-18"]["bucket_interpretation_quarantined"] is False
    assert by_date["2026-05-19"]["raw_sim_preserved"] is True
    assert by_date["2026-05-19"]["bucket_interpretation_quarantined"] is True
    assert set(by_date["2026-05-19"]["quarantine_scope"]) == {
        "entry_adm_bucket_dimensions",
        "ldm_bucket_attribution",
        "sim_overbought_context_provenance",
    }
    assert (
        by_date["2026-05-19"]["recommended_action"]
        == "regenerate_derived_reports_with_source_quality_gate"
    )
    assert report["summary"]["first_entry_adm_unknown_date"] == "2026-05-19"
    assert report["summary"]["first_ldm_unknown_date"] == "2026-05-19"
    assert report["summary"]["first_sim_overbought_unknown_date"] == "2026-05-19"
    assert report["summary"]["operator_action_required"] is False
    assert report["policy"]["runtime_effect"] is False
    assert (
        by_date["2026-05-19"]["stale_derived_reports"][0]["report_type"]
        == "scalp_entry_action_decision_matrix"
    )


def test_observation_source_quality_backfill_writes_json_and_markdown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-19",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "entry_adm_score_bucket": "score_unknown",
                },
            )
        ],
    )

    report = audit.write_backfill_report("2026-05-19", start_date="2026-05-19")
    json_path, md_path = audit.backfill_report_paths("2026-05-19")

    assert report["status"] == "warning"
    assert json_path.exists()
    assert md_path.exists()
    assert "Raw SIM rows and fill/outcome labels are preserved" in md_path.read_text(
        encoding="utf-8"
    )


def test_observation_source_quality_reviews_explicit_unavailable_route_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    observation_only = {
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-07-28",
        [
            _event(
                "scalping_scanner_fast_precheck",
                {
                    **observation_only,
                    "decision_authority": (
                        "real_scalping_scanner_fast_precheck_observation_only"
                    ),
                    "source_quality_gate": ("scalping_scanner_fast_precheck_contract"),
                    "ws_received_types": "0D,0F",
                    "ws_last_0b_age_ms": "not_available_realtime_type_age_ms",
                    "scanner_stale_backoff_raw_0b_route": "unknown",
                },
                record_id=1,
            ),
            _event(
                "rising_missed_one_share_entry_blocked",
                {
                    **observation_only,
                    "venue": "UNKNOWN",
                    "effective_venue": "NXT",
                    "venue_resolution": (
                        "rising_missed_initial_gate:session_explicit_conflict:"
                        "payload.venue=KRX,target.effective_venue=NXT"
                    ),
                    "block_reason": "entry_ai_action_not_evaluated",
                },
                record_id=2,
            ),
            _event(
                "rising_missed_adverse_micro_recovery_checkpoint",
                {
                    **observation_only,
                    "rising_missed_adverse_micro_recovery_price_fresh": False,
                    "rising_missed_adverse_micro_recovery_price_source": "unavailable",
                    "rising_missed_adverse_micro_recovery_source_reason": (
                        "price_missing"
                    ),
                    "rising_missed_adverse_micro_recovery_ws_0b_raw_route": "unknown",
                },
                record_id=3,
            ),
            _event(
                "ai_holding_review",
                {
                    "holding_context_entry_time_context": (
                        "{'entry_order_flow_status': 'unknown'}"
                    ),
                    "holding_context_ai_market_snapshot": (
                        "{'market_data_route': 'unknown', "
                        "'ai_input_preflight_v1': {'status': 'blocked'}}"
                    ),
                    "holding_context_ws_route": "unknown",
                    "holding_context_source_quality_status": "disabled",
                    "holding_context_enabled": False,
                    "holding_context_blockers": "[]",
                    "ai_result_source": "input_preflight_blocked",
                },
                record_id=4,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-07-28")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert (
        reviewed["scalping_scanner_fast_precheck"]["scanner_stale_backoff_raw_0b_route"]
        == "reviewed_scanner_stale_backoff_route_not_available"
    )
    assert reviewed["rising_missed_one_share_entry_blocked"]["venue"] == (
        "reviewed_observation_only_venue_not_available"
    )
    assert (
        reviewed["rising_missed_adverse_micro_recovery_checkpoint"][
            "rising_missed_adverse_micro_recovery_ws_0b_raw_route"
        ]
        == "reviewed_adverse_micro_recovery_route_not_available"
    )
    assert reviewed["ai_holding_review"]["holding_context_ws_route"] == (
        "reviewed_holding_input_preflight_blocked_provenance"
    )


def test_observation_source_quality_reviews_explicit_postclose_unknown_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-08-03",
        [
            _event(
                "opening_rotation_entry_owner_handoff",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_runtime_event:explicit_target_venue_missing"
                    ),
                    "venue_source_quality_status": "reviewed_fail_closed",
                    "venue_unknown_reviewed_reason": (
                        "scanner_runtime_event:explicit_target_venue_missing"
                    ),
                    "runtime_effect": True,
                },
                record_id=1,
            ),
            _event(
                "residual_blocked",
                {
                    "post_probe_direction_state": "UNKNOWN",
                    "prior_probe_residual_direction_state": "UNKNOWN",
                    "prior_probe_residual_failure_signature": (
                        "residual_revalidation_timeout|UNKNOWN|"
                        "post_probe_ai_action_not_fresh|orderbook|0/2"
                    ),
                    "prior_probe_residual_continuation_action": "DEFER",
                    "prior_probe_residual_decision_authority": (
                        "causal_attribution_only"
                    ),
                    "prior_probe_residual_direction_reason": (
                        "post_probe_ai_action_not_fresh"
                    ),
                    "prior_probe_residual_source_quality_gate": (
                        "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
                    ),
                    "prior_probe_residual_scale_in_recheck_authority": (
                        "evaluation_only_full_scale_in_guards_required"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "pre_submit_micro_unavailable_block",
                {
                    "entry_order_flow_status": "unknown",
                    "entry_context_quality": "partial",
                    "entry_context_missing_features": "quote_freshness",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=3,
            ),
            _event(
                "scale_in_ai_authority_retry",
                {
                    "ai_market_snapshot_route_partition_selected_key": "KRX|unknown",
                    "ai_market_snapshot_route_partition_used": False,
                    "ai_market_snapshot_route_partition_reason": (
                        "route_snapshots_unavailable"
                    ),
                    "holding_context_source_quality_status": "blocked",
                    "holding_context_blockers": "['realtime_type_provenance_missing']",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
            _event(
                "stat_action_decision_snapshot",
                {
                    "prior_probe_residual_direction_state": "UNKNOWN",
                    "prior_probe_residual_continuation_action": "DEFER",
                    "prior_probe_residual_decision_authority": (
                        "causal_attribution_only"
                    ),
                    "prior_probe_residual_direction_reason": (
                        "post_probe_ai_action_not_fresh"
                    ),
                    "prior_probe_residual_source_quality_gate": (
                        "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
                    ),
                    "prior_probe_residual_scale_in_recheck_authority": (
                        "evaluation_only_full_scale_in_guards_required"
                    ),
                    "source_quality_gate": "stat_action_snapshot_source_only",
                },
                record_id=5,
            ),
            _event(
                "residual_blocked",
                {
                    "prior_probe_residual_failure_signature": (
                        "residual_revalidation_timeout|NOT_UNKNOWN|"
                        "post_probe_ai_action_not_fresh|orderbook|0/2"
                    ),
                    "prior_probe_residual_continuation_action": "DEFER",
                    "prior_probe_residual_decision_authority": (
                        "causal_attribution_only"
                    ),
                    "prior_probe_residual_direction_reason": (
                        "post_probe_ai_action_not_fresh"
                    ),
                    "prior_probe_residual_source_quality_gate": (
                        "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
                    ),
                    "prior_probe_residual_scale_in_recheck_authority": (
                        "evaluation_only_full_scale_in_guards_required"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=6,
            ),
            _event(
                "unexplained_unknown_stage",
                {"unexplained_source": "UNKNOWN"},
                record_id=7,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-03")

    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert set(reviewed["opening_rotation_entry_owner_handoff"].values()) == {
        "reviewed_scanner_venue_fail_closed_provenance"
    }
    assert set(reviewed["residual_blocked"].values()) == {
        "reviewed_prior_probe_residual_source_gap"
    }
    assert set(reviewed["stat_action_decision_snapshot"].values()) == {
        "reviewed_prior_probe_residual_source_gap"
    }
    assert (
        reviewed["pre_submit_micro_unavailable_block"]["entry_order_flow_status"]
        == "reviewed_entry_order_flow_not_available"
    )
    assert (
        reviewed["scale_in_ai_authority_retry"][
            "ai_market_snapshot_route_partition_selected_key"
        ]
        == "reviewed_holding_route_partition_not_available"
    )
    unknown_by_stage = {
        item["stage"]: {field["field"] for field in item["fields"]}
        for item in report["unknown_token_findings"]
    }
    assert unknown_by_stage == {
        "residual_blocked": {"prior_probe_residual_failure_signature"},
        "unexplained_unknown_stage": {"__stage", "unexplained_source"},
    }


def test_observation_source_quality_reviews_terminal_causal_and_route_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    causal = {
        "prior_probe_residual_direction_state": "UNKNOWN",
        "prior_probe_residual_direction_reason": "post_probe_wait_negative_group",
        "prior_probe_residual_continuation_action": "DEFER",
        "prior_probe_residual_abort_reason": "residual_revalidation_timeout",
        "prior_probe_residual_decision_authority": "causal_attribution_only",
        "prior_probe_residual_source_quality_gate": (
            "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
        ),
        "prior_probe_residual_scale_in_recheck_authority": (
            "evaluation_only_full_scale_in_guards_required"
        ),
    }
    _write_events(
        tmp_path,
        "2026-08-04",
        [
            _event(
                "scale_in_order_submitted",
                {
                    **causal,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
                record_id=1,
            ),
            _event(
                "scale_in_feature_context_refresh",
                {
                    **causal,
                    "prior_probe_residual_direction_reason": "-",
                    "prior_probe_residual_continuation_action": "BLOCK",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "scale_in_executed",
                {
                    **causal,
                    "prior_probe_residual_continuation_action": None,
                    "decision_authority": "broker_receipt_observation_only",
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
                record_id=3,
            ),
            _event(
                "residual_blocked",
                {
                    **causal,
                    "entry_split_probe_terminal_failure_signature": (
                        "residual_revalidation_timeout|UNKNOWN|"
                        "post_probe_wait_negative_group|orderbook|0/2"
                    ),
                    "entry_split_probe_terminal_abort_reason": (
                        "residual_revalidation_timeout"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=4,
            ),
            _event(
                "scalping_scanner_ws_backoff_watch_retained",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": "missing_tradable_explicit_venue",
                    "venue_source_quality_status": "reviewed_fail_closed",
                    "venue_unknown_reviewed_reason": (
                        "scanner_runtime_event:explicit_target_venue_missing"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": True,
                },
                record_id=5,
            ),
            _event(
                "prev_close_gainer_entry_ai_handoff",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "NXT",
                    "venue_resolution": (
                        "rising_missed_initial_gate:session_explicit_conflict:"
                        "consistent_explicit:stock.effective_venue"
                    ),
                    "block_reason": "not_rising_missed_candidate",
                    "decision_authority": (
                        "source_routing_to_existing_exact_v2_entry_ai"
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": False,
                },
                record_id=6,
            ),
            _event(
                "scalp_fast_exit_claimed",
                {
                    "fast_exit_ws_0d_route": "unknown",
                    "fast_exit_broker_route": "SOR",
                    "fast_exit_route_guard_reason": "krx_sor_route_resolved",
                    "fast_exit_route_source_quality_blocked": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": False,
                },
                record_id=7,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-04")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["scale_in_order_submitted"] == {
        "prior_probe_residual_direction_state": (
            "reviewed_prior_probe_residual_source_gap"
        )
    }
    assert (
        reviewed["residual_blocked"]["entry_split_probe_terminal_failure_signature"]
        == "reviewed_probe_terminal_failure_signature_source_gap"
    )
    assert reviewed["scalping_scanner_ws_backoff_watch_retained"]["venue"] == (
        "reviewed_scanner_venue_fail_closed_provenance"
    )
    assert reviewed["prev_close_gainer_entry_ai_handoff"]["venue"] == (
        "reviewed_observation_only_venue_not_available"
    )
    assert reviewed["scalp_fast_exit_claimed"]["fast_exit_ws_0d_route"] == (
        "reviewed_legacy_fast_exit_route_provenance"
    )


def test_observation_source_quality_reviews_explicit_no_call_and_venue_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    no_call_fields = {
        "ai_result_source": "unknown",
        "ai_decision_evaluation_status": "not_evaluated_provider_or_preflight",
        "ai_decision_trace_id": "-",
        "recheck_action": "not_evaluated",
        "recheck_score": "not_evaluated",
        "decision_authority": "operator_runtime_decision_recheck_only",
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    historical_sizing_fields = {
        "tier_reason": "unknown_venue_fallback",
        "formula_version": "entry_type_5stage_cap25_v1",
        "tier": 1,
        "reference_time": "2026-08-12T09:04:00+09:00",
        "venue": "KRX",
        "effective_venue": "KRX",
        "actual_order_submitted": False,
    }
    explicit_sizing_fields = {
        **historical_sizing_fields,
        "sizing_tier_reason_at_allocation": "unknown_venue_fallback",
        "sizing_venue_at_allocation": "UNKNOWN",
        "sizing_venue_resolution_at_allocation": ("missing_tradable_explicit_venue"),
    }
    _write_events(
        tmp_path,
        "2026-08-12",
        [
            _event(
                "ai_numeric_consistency_recheck_evaluated",
                no_call_fields,
                record_id=1,
            ),
            _event(
                "early_accel_strong_bundle_recheck_allowed",
                no_call_fields,
                record_id=2,
            ),
            _event(
                "scalping_scanner_watching_runtime_skip",
                explicit_sizing_fields,
                record_id=3,
            ),
            _event(
                "rising_missed_one_share_entry",
                historical_sizing_fields,
                record_id=4,
            ),
            _event(
                "scalping_scanner_ws_prewarm_filtered",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "venue_resolution": (
                        "scanner_session_clock:outside_supported_session"
                    ),
                    "market_session_bucket": "outside_supported_session",
                    "decision_authority": (
                        "scanner_ws_prewarm_source_filter_no_entry_authority"
                    ),
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=5,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-12")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["ai_numeric_consistency_recheck_evaluated"] == {
        "ai_result_source": "reviewed_recheck_result_not_evaluated"
    }
    assert reviewed["early_accel_strong_bundle_recheck_allowed"] == {
        "ai_result_source": "reviewed_recheck_result_not_evaluated"
    }
    assert reviewed["scalping_scanner_watching_runtime_skip"] == {
        "sizing_venue_at_allocation": (
            "reviewed_explicit_sizing_unknown_venue_fallback"
        ),
        "sizing_tier_reason_at_allocation": (
            "reviewed_explicit_sizing_unknown_venue_fallback"
        ),
        "tier_reason": "reviewed_explicit_sizing_unknown_venue_fallback",
    }
    assert reviewed["rising_missed_one_share_entry"] == {
        "tier_reason": "reviewed_explicit_sizing_unknown_venue_fallback"
    }
    assert reviewed["scalping_scanner_ws_prewarm_filtered"] == {
        "effective_venue": "reviewed_scanner_venue_fail_closed_provenance",
        "venue": "reviewed_scanner_venue_fail_closed_provenance",
    }


def test_observation_source_quality_accepts_explicit_non_evaluated_source_rows():
    order_forbidden = {
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
    }
    assert audit._blocked_observation_records_fail_closed_source_gap(
        "early_accel_strong_bundle_recheck_skipped",
        {
            **order_forbidden,
            "skip_reason": "tick_aggressor_pressure_unusable",
        },
        source="tick",
    )
    assert audit._blocked_observation_records_fail_closed_source_gap(
        "score65_74_recovery_probe_blocked",
        {
            **order_forbidden,
            "score65_74_recovery_probe_skip_reason": (
                "ai_blocking_adverse_risk_observation_only"
            ),
        },
        source="tick",
    )
    assert audit._blocked_observation_records_fail_closed_source_gap(
        "scalp_entry_action_decision_snapshot",
        {
            **order_forbidden,
            "source_stage": "ai_confirmed",
            "provider_called": True,
            "openai_transport_fail_closed_reason": "request timed out",
            "ai_decision_evaluation_status": ("not_evaluated_provider_or_preflight"),
            "minute_candle_evaluation_state": "unavailable_fail_closed",
        },
        source="minute_candle",
    )


def test_observation_source_quality_reviews_blocked_route_unknown_provenance():
    holding = {
        "ai_result_source": "input_preflight_blocked",
        "holding_context_source_quality_status": "blocked",
        "holding_context_blockers": ["ai_preflight:current_price_unknown_age"],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "holding_flow_override_review",
            "holding_context_ws_route",
            "unknown",
            holding,
        )
        == "reviewed_holding_input_preflight_blocked_provenance"
    )
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "holding_flow_override_review",
            "flow_evidence",
            "bbo_missing|current_price_unknown_age",
            holding,
        )
        == "reviewed_holding_input_preflight_blocked_provenance"
    )

    scale_in = {
        "ai_market_snapshot_route_partition_used": False,
        "ai_market_snapshot_route_partition_reason": ("candle_route_snapshot_missing"),
        "holding_context_source_quality_status": "blocked",
        "holding_context_blockers": ["candle_source_quality"],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "scale_in_ai_authority_retry",
            "ai_market_snapshot_route_partition_selected_key",
            "KRX|unknown",
            scale_in,
        )
        == "reviewed_holding_route_partition_not_available"
    )

    fast_exit = {
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "fast_exit_route_source_quality_blocked": True,
        "fast_exit_route_guard_reason": "nxt_executable_quote_route_unproven",
        "fast_exit_ws_0d_route_provenance_state": "not_available",
    }
    assert (
        audit._reviewed_unknown_reason_for_stage_field(
            "scalp_fast_exit_quote_blocked",
            "fast_exit_ws_0d_route",
            "unknown",
            fast_exit,
        )
        == "reviewed_legacy_fast_exit_route_provenance"
    )


def test_observation_source_quality_reviews_probe_and_holding_not_available_provenance(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    probe_fields = {
        "post_probe_direction_orderbook_state": "unknown",
        "prior_probe_residual_orderbook_state": "unknown",
        "prior_probe_residual_continuation_action": "BLOCK",
        "prior_probe_residual_abort_reason": "probe_runtime_quantity_invariant",
        "prior_probe_residual_decision_authority": "causal_attribution_only",
        "prior_probe_residual_source_quality_gate": (
            "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
        ),
        "prior_probe_residual_scale_in_recheck_authority": (
            "evaluation_only_full_scale_in_guards_required"
        ),
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    holding_fields = {
        "holding_context_selected_route_partition": {
            "used": False,
            "reason": "route_snapshots_unavailable",
            "selected_key": "KRX|unknown",
        },
        "holding_context_source_quality_status": "blocked",
        "holding_context_blockers": "['ai_preflight:tape_missing']",
        "ai_result_source": "input_preflight_blocked",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-08-13",
        [
            _event("residual_blocked", probe_fields, record_id=1),
            _event(
                "post_probe_terminal_abort_recovery_observed",
                {
                    **probe_fields,
                    "decision_authority": (
                        "source_only_post_terminal_abort_recovery_observation_no_runtime_mutation"
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                },
                record_id=2,
            ),
            _event("ai_holding_review", holding_fields, record_id=3),
            _event(
                "scale_in_ai_authority_retry",
                {
                    **holding_fields,
                    "scale_in_ai_authority_input_retry_result_source": (
                        "input_preflight_blocked"
                    ),
                },
                record_id=4,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-13")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["residual_blocked"] == {
        "post_probe_direction_orderbook_state": (
            "reviewed_prior_probe_residual_source_gap"
        ),
        "prior_probe_residual_orderbook_state": (
            "reviewed_prior_probe_residual_source_gap"
        ),
    }
    assert reviewed["post_probe_terminal_abort_recovery_observed"] == {
        "post_probe_direction_orderbook_state": (
            "reviewed_prior_probe_residual_source_gap"
        ),
        "prior_probe_residual_orderbook_state": (
            "reviewed_prior_probe_residual_source_gap"
        ),
    }
    for stage in ("ai_holding_review", "scale_in_ai_authority_retry"):
        assert reviewed[stage] == {
            "holding_context_selected_route_partition": (
                "reviewed_holding_input_preflight_blocked_provenance"
            )
        }


def test_observation_source_quality_reviews_hard_negative_probe_terminal_gap(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    terminal_fields = {
        "prior_probe_residual_direction_state": "HARD_NEGATIVE",
        "prior_probe_residual_direction_reason": "-",
        "prior_probe_residual_continuation_action": "HARD_NEGATIVE",
        "prior_probe_residual_abort_reason": "probe_fill_slippage_above_cap",
        "prior_probe_residual_orderbook_state": "unknown",
        "prior_probe_residual_signed_pressure_source": "unavailable",
        "prior_probe_residual_route_source_allowed": False,
        "prior_probe_residual_decision_authority": "causal_attribution_only",
        "prior_probe_residual_source_quality_gate": (
            "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
        ),
        "prior_probe_residual_scale_in_recheck_authority": (
            "evaluation_only_full_scale_in_guards_required"
        ),
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _write_events(
        tmp_path,
        "2026-08-20",
        [
            _event("residual_blocked", terminal_fields, record_id=1),
            _event("stat_action_decision_snapshot", terminal_fields, record_id=2),
            _event(
                "post_probe_terminal_abort_recovery_observed",
                terminal_fields,
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-20")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    for stage in (
        "residual_blocked",
        "stat_action_decision_snapshot",
        "post_probe_terminal_abort_recovery_observed",
    ):
        assert reviewed[stage] == {
            "prior_probe_residual_orderbook_state": (
                "reviewed_prior_probe_residual_source_gap"
            )
        }


def test_observation_source_quality_does_not_review_hard_negative_probe_gap_on_unowned_stage(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-08-20",
        [
            _event(
                "unowned_probe_diagnostic",
                {
                    "prior_probe_residual_direction_state": "HARD_NEGATIVE",
                    "prior_probe_residual_direction_reason": "-",
                    "prior_probe_residual_continuation_action": "HARD_NEGATIVE",
                    "prior_probe_residual_abort_reason": (
                        "probe_fill_slippage_above_cap"
                    ),
                    "prior_probe_residual_orderbook_state": "unknown",
                    "prior_probe_residual_signed_pressure_source": "unavailable",
                    "prior_probe_residual_route_source_allowed": False,
                    "prior_probe_residual_decision_authority": (
                        "causal_attribution_only"
                    ),
                    "prior_probe_residual_source_quality_gate": (
                        "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
                    ),
                    "prior_probe_residual_scale_in_recheck_authority": (
                        "evaluation_only_full_scale_in_guards_required"
                    ),
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-20")

    assert report["reviewed_unknown_token_findings"] == []
    assert report["unknown_token_findings"][0]["stage"] == ("unowned_probe_diagnostic")
    assert report["unknown_token_findings"][0]["fields"][0]["field"] == (
        "prior_probe_residual_orderbook_state"
    )


def test_observation_source_quality_does_not_review_used_unknown_route_partition(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-08-13",
        [
            _event(
                "ai_holding_review",
                {
                    "holding_context_selected_route_partition": {
                        "used": True,
                        "reason": "route_snapshots_unavailable",
                        "selected_key": "KRX|unknown",
                    },
                    "holding_context_source_quality_status": "blocked",
                    "holding_context_blockers": "['ai_preflight:tape_missing']",
                    "ai_result_source": "input_preflight_blocked",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-13")

    assert report["reviewed_unknown_token_findings"] == []
    assert report["unknown_token_findings"][0]["fields"][0]["field"] == (
        "holding_context_selected_route_partition"
    )


def test_observation_source_quality_reviews_aug18_unknown_provenance_variants(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    events = [
        _event(
            "ai_holding_review",
            {
                "holding_context_selected_route_partition": {
                    "used": False,
                    "reason": "candle_route_snapshot_missing",
                    "selected_key": "KRX|unknown",
                },
                "holding_context_source_quality_status": "blocked",
                "holding_context_blockers": ["ai_preflight:tape_missing"],
                "ai_result_source": "input_preflight_blocked",
            },
            record_id=1,
        ),
        _event(
            "scalp_fast_exit_venue_blocked",
            {
                "fast_exit_ws_0d_route": "unknown",
                "fast_exit_route_guard_reason": (
                    "outside_supported_sell_execution_session"
                ),
                "fast_exit_execution_session_blocked": True,
                "fast_exit_broker_route_blocked": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            record_id=2,
        ),
        _event(
            "real_weak_ai_micro_entry_block",
            {
                "entry_order_flow_status": "unknown",
                "entry_context_quality": "stale",
                "entry_context_missing_features": (
                    "quote_freshness,order_flow_pressure"
                ),
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            record_id=3,
        ),
    ]
    for record_id, stage in enumerate(
        (
            "holding_started",
            "position_rebased_after_fill",
            "scale_in_executed",
            "sell_completed",
            "sell_partial_fill_progress",
        ),
        start=4,
    ):
        events.append(
            _event(
                stage,
                {
                    "broker_actual_execution_venue": "UNKNOWN",
                    "broker_actual_execution_venue_source": (
                        "official_exchange_fields_ambiguous_or_missing"
                    ),
                    "broker_actual_exchange_code": "0",
                    "broker_actual_exchange_name": "SOR",
                    "broker_sor_flag": "Y",
                    "broker_execution_provenance_complete": False,
                },
                record_id=record_id,
            )
        )
    _write_events(tmp_path, "2026-08-18", events)

    report = audit.build_observation_source_quality_audit("2026-08-18")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["ai_holding_review"] == {
        "holding_context_selected_route_partition": (
            "reviewed_holding_input_preflight_blocked_provenance"
        )
    }
    assert reviewed["scalp_fast_exit_venue_blocked"] == {
        "fast_exit_ws_0d_route": "reviewed_legacy_fast_exit_route_provenance"
    }
    assert reviewed["real_weak_ai_micro_entry_block"] == {
        "entry_order_flow_status": "reviewed_entry_order_flow_not_available"
    }
    for stage in (
        "holding_started",
        "position_rebased_after_fill",
        "scale_in_executed",
        "sell_completed",
        "sell_partial_fill_progress",
    ):
        assert reviewed[stage] == {
            "broker_actual_execution_venue": (
                "reviewed_broker_actual_venue_not_available"
            )
        }


def test_observation_source_quality_reviews_explicit_20260821_provenance_gaps(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    lifecycle_base = {
        "main_lifecycle_venue": "UNKNOWN",
        "main_lifecycle_decision_authority": "source_only_lifecycle_observation",
        "main_lifecycle_order_authority": False,
        "main_lifecycle_provider_authority": False,
    }
    _write_events(
        tmp_path,
        "2026-08-21",
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                {
                    "venue": "UNKNOWN",
                    "effective_venue": "UNKNOWN",
                    "market_session_bucket": "UNKNOWN",
                    "venue_resolution": (
                        "conflicting_explicit_market_session_bucket:"
                        "payload.market_session_bucket=krx_regular,"
                        "target.market_session_bucket=nan"
                    ),
                    "venue_source_quality_status": "reviewed_fail_closed",
                    "venue_unknown_reviewed_reason": (
                        "conflicting_explicit_market_session_bucket:"
                        "payload.market_session_bucket=krx_regular,"
                        "target.market_session_bucket=nan"
                    ),
                    "decision_authority": (
                        "real_scalping_scanner_runtime_watchlist_handoff_only"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=1,
            ),
            _event(
                "krx_direct_canary_live_ai_wait_submit_block",
                {
                    "entry_order_flow_status": "unknown",
                    "entry_context_quality": "stale",
                    "entry_context_missing_features": (
                        "quote_freshness,order_flow_pressure"
                    ),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "stat_action_decision_snapshot",
                {
                    **lifecycle_base,
                    "main_lifecycle_session_bucket": "nan",
                    "main_lifecycle_source_stage": ("stat_action_decision_snapshot"),
                },
                record_id=3,
            ),
            _event(
                "exit_signal",
                {
                    **lifecycle_base,
                    "main_lifecycle_session_bucket": "unknown",
                    "main_lifecycle_source_stage": "exit_signal",
                    "main_lifecycle_venue_source": (
                        "not_available_explicit_tradable_venue"
                    ),
                    "main_lifecycle_venue_provenance_status": (
                        "not_available_explicit_source"
                    ),
                    "main_lifecycle_session_bucket_source": (
                        "not_available_explicit_session_bucket"
                    ),
                    "main_lifecycle_session_provenance_status": (
                        "not_available_explicit_source"
                    ),
                },
                record_id=4,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-08-21")

    assert report["unknown_token_findings"] == []
    reviewed = {
        item["stage"]: {
            field["field"]: field["reviewed_reason"] for field in item["fields"]
        }
        for item in report["reviewed_unknown_token_findings"]
    }
    assert reviewed["scalping_scanner_runtime_target_attach"] == {
        "effective_venue": "reviewed_scanner_venue_fail_closed_provenance",
        "market_session_bucket": "reviewed_scanner_venue_fail_closed_provenance",
        "venue": "reviewed_scanner_venue_fail_closed_provenance",
    }
    assert reviewed["krx_direct_canary_live_ai_wait_submit_block"] == {
        "entry_order_flow_status": "reviewed_entry_order_flow_not_available"
    }
    assert reviewed["stat_action_decision_snapshot"] == {
        "main_lifecycle_venue": "reviewed_main_lifecycle_venue_not_available"
    }
    assert reviewed["exit_signal"] == {
        "main_lifecycle_session_bucket": (
            "reviewed_main_lifecycle_session_not_available"
        ),
        "main_lifecycle_venue": "reviewed_main_lifecycle_venue_not_available",
    }
