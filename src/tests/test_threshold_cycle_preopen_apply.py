import json

import pytest
from src.engine import lifecycle_bucket_discovery as discovery_mod
from src.engine import runtime_apply_bridge as bridge_mod
from src.engine import scalp_sim_scale_in_window_approval as scale_in_approval_mod
from src.engine import threshold_cycle_preopen_apply as mod
from src.engine.scalping import (
    scalp_sim_auto_approval_control_tower as scalp_sim_auto_mod,
)
from src.engine.swing import sim_auto_approval_control_tower as swing_sim_mod


def _entry_ai_cumulative_window():
    return {
        "window_policy": "clean_baseline_cumulative",
        "start_date": "2026-06-05",
        "end_date": "2026-07-03",
        "clean_tuning_baseline_date": "2026-06-05",
        "source_date_count": 2,
        "source_dates": ["2026-06-05", "2026-07-03"],
        "excluded_date_count": 0,
    }


def _entry_ai_runtime_contract(*, candidate_count=1, allowed_count=1):
    return {
        "schema_version": 1,
        "update_mode": "single_cumulative_quality_update",
        "owner_family": "entry_opportunity_recheck_runtime",
        "max_runtime_apply_count": 1,
        "runtime_apply_candidate_count": candidate_count,
        "allowed_runtime_apply_count": allowed_count,
        "quality_update_id": "entry-quality-update-1" if allowed_count else "",
        "cumulative_quality_window": _entry_ai_cumulative_window(),
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "pass",
        "post_apply_attribution_required": True,
        "runtime_effect": False,
    }


def _entry_ai_candidate_runtime_fields():
    return {
        "quality_update_id": "entry-quality-update-1",
        "runtime_update_mode": "single_cumulative_quality_update",
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": _entry_ai_cumulative_window(),
        "post_apply_attribution_required": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    monkeypatch.setattr(
        mod, "source_quality_preflight_blocked", lambda preflight: False
    )


def test_entry_cancel_wait_standalone_defaults_on(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_CANCEL_WAIT_TUNING_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    decision, env = mod._entry_cancel_wait_standalone_decision(
        "2026-06-12", "2026-06-15", []
    )
    assert decision["selected"] is True
    assert decision["automatic_off_allowed"] is False
    assert env["KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALPING_ENTRY_TIMEOUT_SEC"] == "60"
    assert env["KORSTOCKSCAN_SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC"] == "120"
    assert env["KORSTOCKSCAN_SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC"] == "600"
    assert env["KORSTOCKSCAN_SCALPING_RESERVE_ENTRY_TIMEOUT_SEC"] == "1200"


def test_entry_cancel_wait_only_explicit_operator_lock_turns_off(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "ENTRY_CANCEL_WAIT_TUNING_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    locks = [
        {
            "family": "entry_cancel_wait_runtime",
            "lock_id": "operator-off",
            "env_overrides": {
                "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED": "false"
            },
        }
    ]
    decision, env = mod._entry_cancel_wait_standalone_decision(
        "2026-06-12", "2026-06-15", locks
    )
    assert decision["selected"] is False
    assert decision["decision_reason"] == "explicit_operator_off:operator-off"
    assert env["KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED"] == "false"


def test_entry_cancel_wait_is_written_to_runtime_selected_families(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    decision, env = mod._entry_cancel_wait_standalone_decision(
        "2026-06-12", "2026-06-15", []
    )
    manifest = {
        "source_date": "2026-06-12",
        "source_report": "source.json",
        "generated_at": "2026-06-12T18:00:00+09:00",
        "auto_apply_selected": [],
        "entry_cancel_wait_runtime": decision,
    }
    mod._write_runtime_env("2026-06-15", manifest, env)
    runtime_manifest = json.loads(
        mod.runtime_env_manifest_path("2026-06-15").read_text(encoding="utf-8")
    )
    assert "entry_cancel_wait_runtime" in runtime_manifest["selected_families"]
    assert runtime_manifest["report_type"] == "threshold_runtime_env"
    assert (
        runtime_manifest["env_overrides"][
            "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED"
        ]
        == "true"
    )


def test_profit_stagnation_lock_env_includes_low_profit_hard_exit_candidate():
    env = mod._lock_env_overrides(
        {
            "family": mod.PROFIT_STAGNATION_EXIT_FAMILY,
            "env_overrides": {
                "KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_EXIT_ENABLED": "true",
                "KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_SEC": "180",
            },
        }
    )

    assert env["KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_EXIT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_HARD_EXIT_ENABLED"] == "true"
    assert (
        env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT"]
        == "0.20"
    )
    assert (
        env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MAX_ADJUSTED_PROFIT_PCT"]
        == "1.00"
    )
    assert env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC"] == "1800"
    assert (
        env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_ASSUMED_EXIT_SLIPPAGE_BPS"]
        == "15"
    )


def test_profit_stagnation_carry_forward_env_includes_low_profit_hard_exit_candidate():
    env = mod._previous_runtime_env_overrides_for_family(
        {
            "env_overrides": {
                "KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_EXIT_ENABLED": "true",
                "KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_SEC": "180",
            },
        },
        mod.PROFIT_STAGNATION_EXIT_FAMILY,
    )

    assert env["KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_EXIT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_HARD_EXIT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC"] == "1800"


def test_protect_trailing_smoothing_candidate_emits_runtime_env_overrides():
    env = mod._env_overrides_for_candidate(
        {
            "family": "protect_trailing_smoothing",
            "calibration_state": "adjust_down",
            "target_env_keys": [
                "SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC",
                "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC",
                "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES",
                "SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO",
                "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT",
                "SCALP_PROTECT_TRAILING_EMERGENCY_PCT",
            ],
            "current_values": {
                "window_sec": 20,
                "min_span_sec": 8,
                "min_samples": 3,
                "below_ratio": 0.67,
                "buffer_pct": 1.0,
                "emergency_pct": -2.0,
            },
            "recommended_values": {
                "window_sec": 12,
                "min_span_sec": 12,
                "min_samples": 3,
                "below_ratio": 0.67,
                "buffer_pct": 0.8,
                "emergency_pct": -2.0,
            },
        }
    )

    assert env == {
        "KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC": "12",
        "KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC": "12",
        "KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT": "0.8",
    }


def test_rising_missed_first_touch_avgdown_candidate_emits_runtime_env_overrides():
    env = mod._env_overrides_for_candidate(
        {
            "family": "rising_missed_first_touch_avgdown_decision_gate",
            "calibration_state": "adjust_up",
            "target_env_keys": [
                "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_SUPPORT",
                "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE",
                "SCALP_FIRST_TOUCH_AVGDOWN_MIN_PRIOR_PEAK_PCT",
                "SCALP_FIRST_TOUCH_AVGDOWN_MAX_REPEATED_BLOCKERS_WITHOUT_SUPPORT",
                "SCALP_FIRST_TOUCH_AVGDOWN_LOW_AI_BLOCK",
                "SCALP_FIRST_TOUCH_AVGDOWN_MAX_SPREAD_BPS",
            ],
            "current_values": {
                "min_ai_support": 70.0,
                "min_ai_moderate": 60.0,
                "min_prior_peak_pct": 0.3,
                "max_repeated_blockers_without_support": 8,
                "low_ai_block": 50.0,
                "max_spread_bps": 80.0,
            },
            "recommended_values": {
                "min_ai_support": 75.0,
                "min_ai_moderate": 65.0,
                "min_prior_peak_pct": 0.4,
                "max_repeated_blockers_without_support": 7,
                "low_ai_block": 55.0,
                "max_spread_bps": 70.0,
            },
        }
    )

    assert env == {
        "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_LOW_AI_BLOCK": "55",
        "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_MAX_REPEATED_BLOCKERS_WITHOUT_SUPPORT": "7",
        "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_MAX_SPREAD_BPS": "70",
        "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE": "65",
        "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_SUPPORT": "75",
        "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_MIN_PRIOR_PEAK_PCT": "0.4",
    }


def test_rising_missed_first_touch_avgdown_candidate_ai_guard_reject_blocks_env(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    candidate = {
        "family": "rising_missed_first_touch_avgdown_decision_gate",
        "stage": "scale_in",
        "priority": 38,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "target_env_keys": ["SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE"],
        "current_values": {"min_ai_moderate": 60.0},
        "recommended_values": {"min_ai_moderate": 65.0},
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={
            "items_by_family": {
                "rising_missed_first_touch_avgdown_decision_gate": {
                    "guard_decision": "reject",
                    "guard_reject_reason": "ai_guard_rejected_test",
                }
            }
        },
        require_ai=True,
        target_date="2026-07-04",
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "ai_guard_rejected_test"


def test_preopen_apply_blocks_candidate_with_nested_source_quality_failure():
    candidate = {
        "family": "rising_missed_first_touch_avgdown_decision_gate",
        "stage": "scale_in",
        "priority": 38,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "target_env_keys": ["SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE"],
        "current_values": {"min_ai_moderate": 60.0},
        "recommended_values": {"min_ai_moderate": 65.0},
        "source_metrics": {
            "source_quality_pass": False,
            "provenance_present": True,
        },
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={"items_by_family": {}},
        require_ai=False,
        target_date="2026-07-04",
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "source_quality_blocked"


def test_preopen_apply_blocks_candidate_with_missing_order_provenance():
    candidate = {
        "family": "scalping_pyramid_quality_gate",
        "stage": "scale_in",
        "priority": 39,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "target_env_keys": ["SCALPING_PYRAMID_MIN_PROFIT_PCT"],
        "current_values": {"min_profit_pct": 1.5},
        "recommended_values": {"min_profit_pct": 1.3},
        "source_metrics": {
            "source_quality_pass": True,
            "provenance_present": False,
        },
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={"items_by_family": {}},
        require_ai=False,
        target_date="2026-07-04",
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "source_quality_blocked"


def test_scalping_pyramid_quality_gate_candidate_emits_runtime_env_overrides():
    env = mod._env_overrides_for_candidate(
        {
            "family": "scalping_pyramid_quality_gate",
            "calibration_state": "adjust_down",
            "target_env_keys": [
                "SCALPING_PYRAMID_MIN_PROFIT_PCT",
                "SCALPING_PYRAMID_MIN_AI_SCORE",
                "SCALPING_PYRAMID_MIN_BUY_PRESSURE",
                "SCALPING_PYRAMID_MIN_TICK_ACCEL",
                "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS",
                "SCALPING_PYRAMID_MAX_SPREAD_BPS",
                "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED",
                "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT",
                "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT",
            ],
            "current_values": {
                "min_profit_pct": 1.5,
                "min_ai_score": 70.0,
                "min_buy_pressure": 60.0,
                "min_tick_accel": 0.5,
                "max_micro_vwap_bps": 60.0,
                "max_spread_bps": 80.0,
                "strong_continuation_enabled": False,
                "strong_continuation_min_profit_pct": 0.9,
                "strong_continuation_max_drawdown_pct": 0.2,
            },
            "recommended_values": {
                "min_profit_pct": 1.3,
                "min_ai_score": 65.0,
                "min_buy_pressure": 55.0,
                "min_tick_accel": 0.4,
                "max_micro_vwap_bps": 70.0,
                "max_spread_bps": 90.0,
                "strong_continuation_enabled": True,
                "strong_continuation_min_profit_pct": 0.8,
                "strong_continuation_max_drawdown_pct": 0.3,
            },
        }
    )

    assert env == {
        "KORSTOCKSCAN_SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS": "70",
        "KORSTOCKSCAN_SCALPING_PYRAMID_MAX_SPREAD_BPS": "90",
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_AI_SCORE": "65",
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_BUY_PRESSURE": "55",
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": "1.3",
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_TICK_ACCEL": "0.4",
        "KORSTOCKSCAN_SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED": "true",
        "KORSTOCKSCAN_SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT": "0.3",
        "KORSTOCKSCAN_SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT": "0.8",
    }


def test_post_probe_winner_recovery_auto_candidate_emits_dated_venue_env():
    payload = {
        "winner_recovery_bounded_canary_observation": {
            "state": "bounded_one_share_canary_evidence_ready",
            "sample_floor": 10,
            "by_effective_venue": [
                {
                    "effective_venue": "KRX",
                    "state": "bounded_one_share_canary_evidence_ready",
                    "sample_count": 12,
                    "ev_eligible_sample_count": 12,
                    "sample_floor": 10,
                    "sample_floor_met": True,
                    "notional_weighted_ev_pct": 0.1142,
                },
                {
                    "effective_venue": "NXT",
                    "state": "hold_sample",
                    "sample_count": 1,
                    "ev_eligible_sample_count": 1,
                    "sample_floor": 10,
                    "sample_floor_met": False,
                    "notional_weighted_ev_pct": 0.2898,
                },
            ],
        },
        "winner_recovery_real_execution_observation": {
            "state": "observe_one_share_canary",
            "sample_floor": 20,
            "by_entry_effective_venue": [],
        },
    }

    candidate, status = mod._winner_recovery_auto_apply_candidate(
        payload,
        target_date="2026-08-24",
    )

    assert candidate is not None
    assert status["eligible_venues"] == ["KRX"]
    assert candidate["operator_action_required"] is False
    assert candidate["initial_real_qty_cap"] == 1
    assert candidate["automatic_quantity_increase_above_one_share_allowed"] is False
    assert candidate["operator_authorization_provenance"].startswith(
        "explicit_operator_direction_2026-08-21"
    )
    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={"items_by_family": {}},
        require_ai=True,
        target_date="2026-08-24",
    )
    assert [item["family"] for item in selected] == [
        mod.POST_PROBE_WINNER_RECOVERY_FAMILY
    ]
    assert decisions[0]["decision_reason"] == "deterministic_policy_handoff"
    assert env == {
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ACTIVE_DATE": ("2026-08-24"),
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_KRX_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_NXT_ENABLED": "false",
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_PREMARKET_ENABLED": "false",
    }


def test_post_probe_winner_recovery_auto_candidate_rolls_back_non_positive_real_ev():
    payload = {
        "winner_recovery_bounded_canary_observation": {
            "state": "bounded_one_share_canary_evidence_ready",
            "sample_floor": 10,
            "by_effective_venue": [
                {
                    "effective_venue": "KRX",
                    "state": "bounded_one_share_canary_evidence_ready",
                    "sample_count": 20,
                    "ev_eligible_sample_count": 20,
                    "sample_floor": 10,
                    "sample_floor_met": True,
                    "notional_weighted_ev_pct": 0.2,
                }
            ],
        },
        "winner_recovery_real_execution_observation": {
            "state": "non_positive_ev_hold",
            "sample_floor": 20,
            "by_entry_effective_venue": [
                {
                    "entry_effective_venue": "KRX",
                    "source_quality_valid_closed_count": 20,
                    "source_quality_adjusted_ev_pct": -0.01,
                }
            ],
        },
    }

    candidate, status = mod._winner_recovery_auto_apply_candidate(
        payload,
        target_date="2026-08-24",
    )

    assert candidate is None
    assert status["state"] == "no_eligible_venue"
    assert status["blocked_venues"]["KRX"] == [
        "real_execution_ev_non_positive_rollback"
    ]


def test_entry_split_order_plan_allows_deterministic_ai_unavailable(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    policy_file = "/tmp/entry_split_order_policy_2026-07-07.json"
    candidate = {
        "family": "entry_split_order_plan",
        "stage": "submit",
        "priority": 9,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "target_env_keys": [
            "ENTRY_SPLIT_ORDER_POLICY_ENABLED",
            "ENTRY_SPLIT_ORDER_POLICY_FILE",
            "ENTRY_SPLIT_ORDER_POLICY_VERSION",
        ],
        "current_values": {
            "enabled": False,
            "policy_file": "",
            "policy_version": "",
        },
        "recommended_values": {
            "enabled": True,
            "policy_file": policy_file,
            "policy_version": "entry_split_order_plan:2026-07-07:test",
        },
        "source_metrics": {
            "source_quality_status": "pass",
            "primary_sample_book": "real_submit_post_submit_observed_low",
        },
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={
            "status": "unavailable",
            "items_by_family": {
                "entry_split_order_plan": {
                    "family": "entry_split_order_plan",
                    "ai_review_state": "unavailable",
                    "guard_accepted": False,
                    "guard_reject_reason": "ai_unavailable",
                    "guard_decision": {
                        "guard_accepted": False,
                        "guard_reject_reason": "ai_unavailable",
                        "route_action": "deterministic_only",
                    },
                }
            },
        },
        require_ai=False,
        target_date="2026-07-08",
    )

    assert selected[0]["family"] == "entry_split_order_plan"
    assert decisions[0]["selected"] is True
    assert decisions[0]["decision_reason"] == "deterministic_policy_handoff"
    assert env == {
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE": policy_file,
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION": "entry_split_order_plan:2026-07-07:test",
    }


def test_split_order_plans_do_not_require_ai_review_when_require_ai_true(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    entry_policy_file = "/tmp/entry_split_order_policy_2026-07-07.json"
    scale_policy_file = "/tmp/scale_in_split_order_policy_2026-07-07.json"
    candidates = [
        {
            "family": "entry_split_order_plan",
            "stage": "submit",
            "priority": 9,
            "calibration_state": "adjust_up",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "target_env_keys": [
                "ENTRY_SPLIT_ORDER_POLICY_ENABLED",
                "ENTRY_SPLIT_ORDER_POLICY_FILE",
                "ENTRY_SPLIT_ORDER_POLICY_VERSION",
            ],
            "current_values": {
                "enabled": True,
                "policy_file": entry_policy_file,
                "policy_version": "entry_split_order_plan:2026-07-07:test",
            },
            "recommended_values": {
                "enabled": True,
                "policy_file": entry_policy_file,
                "policy_version": "entry_split_order_plan:2026-07-07:test",
            },
        },
        {
            "family": "scale_in_split_order_plan",
            "stage": "scale_in",
            "priority": 9,
            "calibration_state": "adjust_up",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "target_env_keys": [
                "SCALE_IN_SPLIT_ORDER_POLICY_ENABLED",
                "SCALE_IN_SPLIT_ORDER_POLICY_FILE",
                "SCALE_IN_SPLIT_ORDER_POLICY_VERSION",
            ],
            "current_values": {
                "enabled": True,
                "policy_file": scale_policy_file,
                "policy_version": "scale_in_split_order_plan:2026-07-07:test",
            },
            "recommended_values": {
                "enabled": True,
                "policy_file": scale_policy_file,
                "policy_version": "scale_in_split_order_plan:2026-07-07:test",
            },
        },
    ]

    selected, decisions, env = mod._select_auto_apply_candidates(
        candidates,
        ai_review={
            "status": "unavailable",
            "items_by_family": {
                "entry_split_order_plan": {
                    "guard_accepted": False,
                    "guard_reject_reason": "ai_unavailable",
                    "guard_decision": {
                        "guard_reject_reason": "ai_unavailable",
                        "route_action": "deterministic_only",
                    },
                },
                "scale_in_split_order_plan": {
                    "guard_accepted": False,
                    "guard_reject_reason": "ai_unavailable",
                    "guard_decision": {
                        "guard_reject_reason": "ai_unavailable",
                        "route_action": "deterministic_only",
                    },
                },
            },
        },
        require_ai=True,
        target_date="2026-07-08",
    )

    assert [item["family"] for item in selected] == [
        "entry_split_order_plan",
        "scale_in_split_order_plan",
    ]
    assert [item["decision_reason"] for item in decisions] == [
        "deterministic_policy_handoff",
        "deterministic_policy_handoff",
    ]
    assert env["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"] == entry_policy_file
    assert env["KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE"] == scale_policy_file


def test_scale_in_split_order_plan_does_not_close_pyramid_quality_guard(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    split_policy_file = "/tmp/scale_in_split_order_policy_2026-07-07.json"
    selected = [
        {
            "family": mod.REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY,
            "stage": "scale_in",
            "calibration_state": "operator_locked",
        },
        {
            "family": "scale_in_split_order_plan",
            "stage": "scale_in",
            "calibration_state": "adjust_up",
        },
    ]
    decisions = [
        {
            "family": mod.REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY,
            "selected": True,
            "decision_reason": "operator_runtime_env_lock_preserved",
            "env_overrides": {
                "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED": "true",
            },
        },
        {
            "family": "scale_in_split_order_plan",
            "selected": True,
            "decision_reason": "deterministic_policy_handoff",
            "env_overrides": {
                "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
                "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": split_policy_file,
            },
        },
    ]
    env = {
        "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": split_policy_file,
    }

    owner = mod._scale_in_live_owner_family(selected)
    next_selected, next_decisions, next_env = (
        mod._close_real_pyramid_scale_in_quality_guard_for_live_owner(
            selected=selected,
            decisions=decisions,
            env_overrides=env,
            owner_family=owner,
        )
    )

    assert owner == ""
    assert [item["family"] for item in next_selected] == [
        mod.REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY,
        "scale_in_split_order_plan",
    ]
    assert next_decisions == decisions
    assert next_env == env


@pytest.mark.parametrize(
    "owner_family",
    [
        "scalping_pyramid_quality_gate",
        "scalping_avg_down_recovery_quality_gate",
    ],
)
def test_cumulative_scale_in_quality_update_keeps_downstream_pyramid_guard(
    owner_family,
):
    selected = [
        {
            "family": mod.REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY,
            "stage": "scale_in",
        },
        {"family": owner_family, "stage": "scale_in"},
    ]
    decisions = [
        {
            "family": mod.REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY,
            "selected": True,
        },
        {"family": owner_family, "selected": True},
    ]
    env = {
        "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_AI_SCORE": "65",
    }

    next_selected, next_decisions, next_env = (
        mod._close_real_pyramid_scale_in_quality_guard_for_live_owner(
            selected=selected,
            decisions=decisions,
            env_overrides=env,
            owner_family=owner_family,
        )
    )

    assert next_selected == selected
    assert next_decisions == decisions
    assert next_env == env


def test_scalping_pyramid_quality_gate_candidate_ai_guard_reject_blocks_env(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    candidate = {
        "family": "scalping_pyramid_quality_gate",
        "stage": "scale_in",
        "priority": 39,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "target_env_keys": ["SCALPING_PYRAMID_MIN_AI_SCORE"],
        "current_values": {"min_ai_score": 70.0},
        "recommended_values": {"min_ai_score": 65.0},
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={
            "items_by_family": {
                "scalping_pyramid_quality_gate": {
                    "guard_decision": "reject",
                    "guard_reject_reason": "ai_guard_rejected_test",
                }
            }
        },
        require_ai=True,
        target_date="2026-07-04",
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "ai_guard_rejected_test"


def test_scale_in_selects_only_one_cumulative_quality_update_beside_split_plan(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", tmp_path / "runtime_env")
    split_candidate = {
        "family": "scale_in_split_order_plan",
        "stage": "scale_in",
        "priority": 9,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "target_env_keys": ["SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"],
        "current_values": {"enabled": False},
        "recommended_values": {"enabled": True},
    }
    cumulative_window = {
        "window_policy": "clean_baseline_cumulative",
        "clean_tuning_baseline_date": "2026-06-05",
        "start_date": "2026-06-05",
        "end_date": "2026-07-03",
        "source_dates": ["2026-07-03"],
        "source_date_count": 1,
    }
    pyramid_candidate = {
        "family": "scalping_pyramid_quality_gate",
        "stage": "scale_in",
        "priority": 39,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "source_quality_gate": "pass",
        "target_env_keys": ["SCALPING_PYRAMID_MIN_AI_SCORE"],
        "current_values": {"min_ai_score": 70.0},
        "recommended_values": {"min_ai_score": 65.0},
        "quality_update_id": "pyramid-quality-1",
        "runtime_update_mode": "single_cumulative_quality_update",
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": cumulative_window,
        "post_apply_attribution_required": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    avg_down_candidate = {
        "family": "scalping_avg_down_recovery_quality_gate",
        "stage": "scale_in",
        "priority": 37,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "source_quality_gate": "pass",
        "target_env_keys": ["SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION"],
        "current_values": {"shallow_max_per_position": 1},
        "recommended_values": {"shallow_max_per_position": 2},
        "quality_update_id": "avg-down-quality-1",
        "runtime_update_mode": "single_cumulative_quality_update",
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": cumulative_window,
        "post_apply_attribution_required": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [split_candidate, pyramid_candidate, avg_down_candidate],
        ai_review={},
        require_ai=False,
        target_date="2026-07-04",
    )

    assert [item["family"] for item in selected] == [
        "scale_in_split_order_plan",
        "scalping_avg_down_recovery_quality_gate",
    ]
    assert decisions[2]["selected"] is False
    assert decisions[2]["decision_reason"] == (
        "single_cumulative_quality_update_conflict:"
        "scalping_avg_down_recovery_quality_gate"
    )
    assert env["KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION"] == "2"
    assert "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_AI_SCORE" not in env


def test_cumulative_quality_contract_rejects_quality_update_id_mismatch():
    quality_window = {
        "window_policy": "clean_baseline_cumulative",
        "clean_tuning_baseline_date": "2026-06-05",
        "start_date": "2026-06-05",
        "end_date": "2026-07-03",
        "source_dates": ["2026-07-03"],
        "source_date_count": 1,
    }
    candidate = {
        "family": "scalping_pyramid_quality_gate",
        "stage": "scale_in",
        "quality_update_id": "candidate-id",
        "runtime_update_mode": "single_cumulative_quality_update",
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": quality_window,
        "post_apply_attribution_required": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    payload = {
        "target_date": "2026-07-03",
        "runtime_update_contract": {
            "update_mode": "single_cumulative_quality_update",
            "owner_family": "scalping_pyramid_quality_gate",
            "owner_stage": "scale_in",
            "max_runtime_apply_count": 1,
            "runtime_apply_candidate_count": 1,
            "allowed_runtime_apply_count": 0,
            "quality_update_id": "different-id",
            "cumulative_quality_window": quality_window,
            "post_apply_attribution_required": True,
            "runtime_effect": False,
        },
    }

    assert (
        mod._cumulative_quality_update_contract_error(
            payload,
            [candidate],
            owner_family="scalping_pyramid_quality_gate",
            owner_stage="scale_in",
        )
        == "candidate_quality_update_id_mismatch"
    )


def test_entry_ai_gate_backtest_entry_recheck_candidate_emits_runtime_env(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        mod,
        "ENTRY_AI_GATE_BACKTEST_DIR",
        tmp_path / "entry_ai_gate_backtest",
    )
    path = mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "entry_ai_gate_backtest",
                "target_date": "2026-07-03",
                "summary": {"allowed_runtime_apply_candidate_count": 1},
                "runtime_update_contract": _entry_ai_runtime_contract(),
                "calibration_candidates": [
                    {
                        **_entry_ai_candidate_runtime_fields(),
                        "family": "entry_opportunity_recheck_runtime",
                        "stage": "entry",
                        "priority": 42,
                        "calibration_state": "adjust_down",
                        "allowed_runtime_apply": True,
                        "sample_floor_passed": True,
                        "source_quality_gate": "pass",
                        "target_env_keys": [
                            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
                            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
                            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
                        ],
                        "current_values": {
                            "enabled": False,
                            "min_ai_score": 75,
                            "max_ai_score": 100,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "min_ai_score": 68,
                            "max_ai_score": 74,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    candidates, status = mod._load_entry_ai_gate_backtest_candidates("2026-07-03")
    selected, decisions, env = mod._select_auto_apply_candidates(
        candidates,
        ai_review={},
        require_ai=False,
        target_date="2026-07-04",
    )

    assert status["status"] == "loaded"
    assert status["runtime_update_contract_blocked"] is False
    assert status["runtime_update_contract"]["max_runtime_apply_count"] == 1
    assert len(candidates) == 1
    assert selected[0]["family"] == "entry_opportunity_recheck_runtime"
    assert decisions[0]["selected"] is True
    assert decisions[0]["quality_update_id"] == "entry-quality-update-1"
    assert decisions[0]["runtime_update_mode"] == ("single_cumulative_quality_update")
    assert decisions[0]["post_apply_attribution_required"] is True
    assert env == {
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": "68",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE": "74",
    }


def test_entry_ai_gate_loader_blocks_missing_cumulative_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod,
        "ENTRY_AI_GATE_BACKTEST_DIR",
        tmp_path / "entry_ai_gate_backtest",
    )
    path = mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "entry_ai_gate_backtest",
                "target_date": "2026-07-03",
                "calibration_candidates": [
                    {
                        "family": "entry_opportunity_recheck_runtime",
                        "allowed_runtime_apply": True,
                        "calibration_state": "adjust_down",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    candidates, status = mod._load_entry_ai_gate_backtest_candidates("2026-07-03")

    assert status["runtime_update_contract_blocked"] is True
    assert status["runtime_update_contract_error"] == (
        "missing_runtime_update_contract"
    )
    assert candidates[0]["allowed_runtime_apply"] is False
    assert candidates[0]["calibration_state"] == "freeze"


def test_entry_ai_gate_loader_preserves_zero_candidate_source_contract_status(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        mod,
        "ENTRY_AI_GATE_BACKTEST_DIR",
        tmp_path / "entry_ai_gate_backtest",
    )
    path = mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "entry_ai_gate_backtest",
                "target_date": "2026-07-03",
                "allowed_runtime_apply": False,
                "calibration_state": "source_contract_not_evaluable",
                "summary": {
                    "diagnostic_conflict_detected": True,
                    "supported_wait_recovery_source_contract_status": (
                        "source_contract_not_evaluable"
                    ),
                },
                "runtime_update_contract": _entry_ai_runtime_contract(
                    candidate_count=0, allowed_count=0
                ),
                "calibration_candidates": [],
            }
        ),
        encoding="utf-8",
    )

    candidates, status = mod._load_entry_ai_gate_backtest_candidates("2026-07-03")

    assert candidates == []
    assert status["runtime_update_contract_blocked"] is False
    assert status["allowed_runtime_apply"] is False
    assert status["calibration_state"] == "source_contract_not_evaluable"
    assert (
        status["supported_wait_recovery_source_contract_status"]
        == "source_contract_not_evaluable"
    )


def test_entry_ai_gate_contract_rejects_multiple_runtime_updates():
    candidate = {
        **_entry_ai_candidate_runtime_fields(),
        "family": "entry_opportunity_recheck_runtime",
        "allowed_runtime_apply": True,
    }
    contract = _entry_ai_runtime_contract(candidate_count=2, allowed_count=2)

    error = mod._entry_ai_gate_cumulative_contract_error(
        {"runtime_update_contract": contract}, [candidate, dict(candidate)]
    )

    assert error == "multiple_runtime_update_candidates"


def test_entry_ai_gate_backtest_root_source_quality_blocks_runtime_env(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        mod,
        "ENTRY_AI_GATE_BACKTEST_DIR",
        tmp_path / "entry_ai_gate_backtest",
    )
    path = mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "entry_ai_gate_backtest",
                "target_date": "2026-07-03",
                "source_quality_gate": "source_quality_blocked",
                "summary": {"allowed_runtime_apply_candidate_count": 1},
                "runtime_update_contract": _entry_ai_runtime_contract(),
                "calibration_candidates": [
                    {
                        **_entry_ai_candidate_runtime_fields(),
                        "family": "entry_opportunity_recheck_runtime",
                        "stage": "entry",
                        "priority": 42,
                        "calibration_state": "adjust_down",
                        "allowed_runtime_apply": True,
                        "sample_floor_passed": True,
                        "source_quality_gate": "pass",
                        "target_env_keys": [
                            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
                            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
                            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
                        ],
                        "current_values": {
                            "enabled": False,
                            "min_ai_score": 75,
                            "max_ai_score": 100,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "min_ai_score": 68,
                            "max_ai_score": 74,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    candidates, status = mod._load_entry_ai_gate_backtest_candidates("2026-07-03")
    selected, decisions, env = mod._select_auto_apply_candidates(
        candidates,
        ai_review={},
        require_ai=False,
        target_date="2026-07-04",
    )

    assert status["source_quality_blocked"] is True
    assert candidates[0]["allowed_runtime_apply"] is False
    assert candidates[0]["source_quality_gate"] == "source_quality_blocked"
    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "runtime_apply_not_allowed"


def test_direct_scale_in_calibration_loaders_block_source_quality_preflight(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        mod,
        "SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR",
        tmp_path / "scalping_pyramid_quality_calibration",
    )
    monkeypatch.setattr(
        mod,
        "SCALPING_AVG_DOWN_RECOVERY_CALIBRATION_DIR",
        tmp_path / "scalping_avg_down_recovery_calibration",
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "required_field_missing",
            "hard_blocking_contract_gap_count": 2,
            "clean_baseline_enforced": True,
        },
    )
    monkeypatch.setattr(mod, "source_quality_preflight_blocked", lambda preflight: True)
    pyramid_path = (
        mod.SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR
        / "scalping_pyramid_quality_calibration_2026-07-03.json"
    )
    avg_down_path = (
        mod.SCALPING_AVG_DOWN_RECOVERY_CALIBRATION_DIR
        / "scalping_avg_down_recovery_calibration_2026-07-03.json"
    )
    pyramid_path.parent.mkdir(parents=True)
    avg_down_path.parent.mkdir(parents=True)
    pyramid_path.write_text(
        json.dumps(
            {
                "calibration_candidates": [
                    {
                        "family": "scalping_pyramid_quality_gate",
                        "stage": "scale_in",
                        "calibration_state": "adjust_down",
                        "allowed_runtime_apply": True,
                        "sample_floor_passed": True,
                        "source_quality_gate": "pass",
                        "target_env_keys": ["SCALPING_PYRAMID_MIN_PROFIT_PCT"],
                        "recommended_values": {"min_profit_pct": 1.1},
                    }
                ],
                "winner_recovery_bounded_canary_observation": {
                    "state": "bounded_one_share_canary_evidence_ready",
                    "sample_floor": 10,
                    "by_effective_venue": [
                        {
                            "effective_venue": "KRX",
                            "state": "bounded_one_share_canary_evidence_ready",
                            "sample_count": 12,
                            "ev_eligible_sample_count": 12,
                            "sample_floor": 10,
                            "sample_floor_met": True,
                            "notional_weighted_ev_pct": 0.2,
                        }
                    ],
                },
                "winner_recovery_real_execution_observation": {
                    "state": "observe_one_share_canary",
                    "sample_floor": 20,
                    "by_entry_effective_venue": [],
                },
            }
        ),
        encoding="utf-8",
    )
    avg_down_path.write_text(
        json.dumps(
            {
                "calibration_candidates": [
                    {
                        "family": "scalping_avg_down_recovery_quality_gate",
                        "stage": "scale_in",
                        "calibration_state": "adjust_up",
                        "allowed_runtime_apply": True,
                        "sample_floor_passed": True,
                        "source_quality_gate": "pass",
                        "target_env_keys": [
                            "SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION"
                        ],
                        "recommended_values": {"shallow_max_per_position": 2},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    pyramid_candidates, pyramid_status = (
        mod._load_scalping_pyramid_quality_calibration_candidates(
            "2026-07-03",
            target_date="2026-07-04",
        )
    )
    avg_down_candidates, avg_down_status = (
        mod._load_scalping_avg_down_recovery_calibration_candidates("2026-07-03")
    )

    assert pyramid_status["source_quality_blocked"] is True
    assert avg_down_status["source_quality_blocked"] is True
    assert len(pyramid_candidates) == 2
    assert all(item["allowed_runtime_apply"] is False for item in pyramid_candidates)
    assert avg_down_candidates[0]["allowed_runtime_apply"] is False
    assert all(
        item["source_quality_gate"] == "source_quality_blocked"
        for item in pyramid_candidates
    )
    assert avg_down_candidates[0]["source_quality_gate"] == "source_quality_blocked"


def test_scalping_avg_down_recovery_quality_gate_emits_runtime_env_overrides():
    candidate = {
        "family": "scalping_avg_down_recovery_quality_gate",
        "calibration_state": "adjust_up",
        "current_values": {
            "shallow_max_per_position": 2,
            "deep_enabled": True,
            "deep_pnl_min": -4.0,
        },
        "recommended_values": {
            "shallow_max_per_position": 2,
            "deep_enabled": True,
            "deep_pnl_min": -4.0,
        },
        "target_env_keys": [
            "SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION",
            "DEEP_RECOVERY_AVG_DOWN_ENABLED",
            "DEEP_RECOVERY_AVG_DOWN_PNL_MIN",
        ],
    }

    overrides = mod._env_overrides_for_candidate(candidate)

    assert overrides["KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION"] == "2"
    assert overrides["KORSTOCKSCAN_DEEP_RECOVERY_AVG_DOWN_ENABLED"] == "true"
    assert overrides["KORSTOCKSCAN_DEEP_RECOVERY_AVG_DOWN_PNL_MIN"] == "-4"


def test_scalping_avg_down_recovery_carry_forward_filters_to_avg_down_env():
    env = mod._previous_runtime_env_overrides_for_family(
        {
            "env_overrides": {
                "KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION": "2",
                "KORSTOCKSCAN_DEEP_RECOVERY_AVG_DOWN_PNL_MIN": "-4",
                "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_STANDARD_SEC": "25",
                "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": "1.1",
            }
        },
        "scalping_avg_down_recovery_quality_gate",
    )

    assert env == {
        "KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION": "2",
        "KORSTOCKSCAN_DEEP_RECOVERY_AVG_DOWN_PNL_MIN": "-4",
    }


def test_entry_ai_gate_loader_blocks_source_quality_preflight(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod,
        "ENTRY_AI_GATE_BACKTEST_DIR",
        tmp_path / "entry_ai_gate_backtest",
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "raw_row_exclusion_missing",
            "hard_blocking_contract_gap_count": 1,
            "clean_baseline_enforced": True,
        },
    )
    monkeypatch.setattr(mod, "source_quality_preflight_blocked", lambda preflight: True)
    path = mod.ENTRY_AI_GATE_BACKTEST_DIR / "entry_ai_gate_backtest_2026-07-03.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "entry_ai_gate_backtest",
                "target_date": "2026-07-03",
                "source_quality_gate": "pass",
                "summary": {"allowed_runtime_apply_candidate_count": 1},
                "runtime_update_contract": _entry_ai_runtime_contract(),
                "calibration_candidates": [
                    {
                        **_entry_ai_candidate_runtime_fields(),
                        "family": "entry_opportunity_recheck_runtime",
                        "stage": "entry",
                        "priority": 42,
                        "calibration_state": "adjust_down",
                        "allowed_runtime_apply": True,
                        "sample_floor_passed": True,
                        "source_quality_gate": "pass",
                        "target_env_keys": [
                            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
                            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
                            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
                        ],
                        "current_values": {
                            "enabled": False,
                            "min_ai_score": 75,
                            "max_ai_score": 100,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "min_ai_score": 68,
                            "max_ai_score": 74,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    candidates, status = mod._load_entry_ai_gate_backtest_candidates("2026-07-03")
    selected, decisions, env = mod._select_auto_apply_candidates(
        candidates,
        ai_review={},
        require_ai=False,
        target_date="2026-07-04",
    )

    assert status["source_quality_blocked"] is True
    assert candidates[0]["allowed_runtime_apply"] is False
    assert candidates[0]["source_quality_gate"] == "source_quality_blocked"
    assert selected == []
    assert env == {}
    assert decisions[0]["decision_reason"] == "runtime_apply_not_allowed"


def test_auto_apply_selector_rejects_source_quality_blocked_candidate():
    candidate = {
        "family": "entry_opportunity_recheck_runtime",
        "stage": "entry",
        "priority": 10,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "sample_floor_passed": True,
        "source_quality_gate": "source_quality_blocked",
        "target_env_keys": [
            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
        ],
        "current_values": {"enabled": False, "min_ai_score": 75, "max_ai_score": 100},
        "recommended_values": {"enabled": True, "min_ai_score": 68, "max_ai_score": 74},
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "source_quality_blocked"


def test_auto_apply_selector_does_not_preserve_lock_on_source_quality_blocked_candidate():
    candidate = {
        "family": "entry_opportunity_recheck_runtime",
        "stage": "entry",
        "priority": 10,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "sample_floor_passed": True,
        "source_quality_gate": "source_quality_blocked",
        "target_env_keys": [
            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
        ],
        "current_values": {"enabled": False, "min_ai_score": 75, "max_ai_score": 100},
        "recommended_values": {"enabled": True, "min_ai_score": 68, "max_ai_score": 74},
    }
    lock = {
        "lock_id": "entry_opportunity_recheck_operator_override",
        "family": "entry_opportunity_recheck_runtime",
        "stage": "entry",
        "env_overrides": {
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "true",
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": "69",
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE": "74",
        },
        "allowed_close_reason_keywords": [
            "same_stage_owner_conflict",
            "tuning_override",
        ],
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
        operator_locks=[lock],
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "source_quality_blocked"


def test_auto_apply_selector_rejects_forbidden_use_violation_candidate():
    candidate = {
        "family": "entry_opportunity_recheck_runtime",
        "stage": "entry",
        "priority": 10,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "sample_floor_passed": True,
        "source_quality_gate": "pass",
        "forbidden_use_violation": "broker_guard_bypass",
        "target_env_keys": [
            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
        ],
        "current_values": {"enabled": False, "min_ai_score": 75, "max_ai_score": 100},
        "recommended_values": {"enabled": True, "min_ai_score": 68, "max_ai_score": 74},
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "forbidden_use_blocked"


def test_auto_apply_selector_consumes_postclose_runtime_handoff_contract():
    candidate = {
        "family": "entry_opportunity_recheck_runtime",
        "stage": "entry",
        "priority": 10,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "source_quality_gate": "pass",
        "target_env_keys": [
            "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
            "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
            "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
        ],
        "current_values": {"enabled": False, "min_ai_score": 75, "max_ai_score": 100},
        "recommended_values": {"enabled": True, "min_ai_score": 68, "max_ai_score": 74},
        "runtime_handoff_contract": {
            "decision_authority": "next_preopen_bounded_candidate_only",
            "runtime_effect": False,
            "preopen_selection_state": "pending_not_applied",
            "same_stage_max_selected": 1,
            "post_apply_attribution_required": True,
        },
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
    )

    assert len(selected) == 1
    assert env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED"] == "true"
    assert decisions[0]["preopen_selection_state"] == "selected_for_runtime_env"
    assert (
        decisions[0]["postclose_runtime_handoff_contract"]
        == candidate["runtime_handoff_contract"]
    )


def test_auto_apply_selector_rejects_incomplete_runtime_handoff_contract():
    candidate = {
        "family": "entry_opportunity_recheck_runtime",
        "stage": "entry",
        "priority": 10,
        "calibration_state": "adjust_down",
        "allowed_runtime_apply": True,
        "source_quality_gate": "pass",
        "target_env_keys": ["ENTRY_OPPORTUNITY_RECHECK_ENABLED"],
        "current_values": {"enabled": False},
        "recommended_values": {"enabled": True},
        "runtime_handoff_contract": {
            "decision_authority": "next_preopen_bounded_candidate_only",
            "runtime_effect": False,
            "preopen_selection_state": "pending_not_applied",
            "same_stage_max_selected": 1,
            "post_apply_attribution_required": False,
        },
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
    )

    assert selected == []
    assert env == {}
    assert (
        decisions[0]["decision_reason"]
        == "runtime_handoff_post_apply_attribution_missing"
    )
    assert decisions[0]["preopen_selection_state"] == "not_selected"


def test_auto_apply_selector_rejects_missing_required_runtime_handoff_contract():
    candidate = {
        "family": "scale_in_split_order_plan",
        "stage": "scale_in",
        "priority": 9,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "target_env_keys": ["SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"],
        "current_values": {"enabled": False},
        "recommended_values": {"enabled": True},
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
        target_date="2026-08-04",
        runtime_handoff_contract_required_families={"scale_in_split_order_plan"},
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "runtime_handoff_contract_missing"
    assert decisions[0]["runtime_handoff_contract_required"] is True


def test_auto_apply_selector_rejects_runtime_handoff_contract_version_mismatch():
    candidate = {
        "family": "entry_split_order_plan",
        "stage": "submit",
        "priority": 9,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "target_env_keys": ["ENTRY_SPLIT_ORDER_POLICY_ENABLED"],
        "current_values": {"enabled": False},
        "recommended_values": {"enabled": True},
        "runtime_handoff_contract": {
            "decision_authority": "next_preopen_bounded_candidate_only",
            "runtime_effect": False,
            "preopen_selection_state": "pending_not_applied",
            "same_stage_max_selected": 1,
            "post_apply_attribution_required": True,
        },
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
        target_date="2026-08-04",
        runtime_handoff_contract_required_families={"entry_split_order_plan"},
        runtime_handoff_contract_source_version=0,
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["decision_reason"] == (
        "runtime_handoff_contract_version_mismatch"
    )


def test_required_runtime_handoff_contract_does_not_replace_operator_lock_authority():
    candidate = {
        "family": "score65_74_recovery_probe",
        "stage": "entry",
        "priority": 10,
        "calibration_state": "adjust_up",
        "allowed_runtime_apply": True,
        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
        "current_values": {"enabled": False},
        "recommended_values": {"enabled": True},
    }
    lock = {
        "family": "score65_74_recovery_probe",
        "stage": "entry",
        "lock_id": "explicit-operator-lock",
        "env_overrides": {"KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED": "true"},
    }

    selected, decisions, env = mod._select_auto_apply_candidates(
        [candidate],
        ai_review={},
        require_ai=False,
        target_date="2026-08-04",
        operator_locks=[lock],
        runtime_handoff_contract_required_families={"score65_74_recovery_probe"},
    )

    assert [item["family"] for item in selected] == ["score65_74_recovery_probe"]
    assert decisions[0]["decision_reason"].startswith(
        "operator_runtime_env_lock_preserved:"
    )
    assert decisions[0]["runtime_handoff_contract_required"] is False
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"] == "true"


def test_calibration_candidate_dedupe_prefers_first_source():
    first = {
        "family": "scalping_pyramid_quality_gate",
        "threshold_version": "same",
        "target_env_keys": ["SCALPING_PYRAMID_MIN_PROFIT_PCT"],
        "recommended_values": {"min_profit_pct": 1.1},
        "source": "direct",
    }
    duplicate = {**first, "source": "entry_ai_gate_backtest"}
    different = {
        **first,
        "threshold_version": "different",
        "recommended_values": {"min_profit_pct": 1.3},
        "source": "next",
    }

    deduped = mod._dedupe_calibration_candidates([first, duplicate, different])

    assert deduped == [first, different]


def _bounded_real_canary_tier2_contract() -> dict:
    return {
        "state": "bounded_real_canary_auto_approved",
        "tier2_status": "parsed",
        "tier2_policy": "fail_closed",
        "tier2_fail_closed": False,
        "primary_ev_uplift_threshold_pct": 1.0,
        "final_user_approval_boundary": "full_live_only",
    }


def test_preopen_apply_rejects_panic_lifecycle_standalone_env_candidate():
    selected, decisions, env = mod._select_auto_apply_candidates(
        [
            {
                "family": "panic_lifecycle_actuator",
                "family_type": "sim_lifecycle_source",
                "stage": "entry",
                "calibration_state": "adjust_up",
                "allowed_runtime_apply": True,
                "safety_revert_required": False,
                "target_env_keys": ["LIFECYCLE_DECISION_MATRIX_ENABLED"],
                "recommended_values": {"enabled": True},
            }
        ],
        ai_review={"items_by_family": {}},
        require_ai=False,
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "non_live_selectable_sim_lifecycle_source"


def test_build_preopen_apply_manifest_uses_latest_prior_report(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)

    (report_dir / "threshold_cycle_2026-04-29.json").write_text(
        json.dumps({"date": "2026-04-29", "apply_candidate_list": [{"family": "old"}]}),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-04-30.json").write_text(
        json.dumps(
            {
                "date": "2026-04-30",
                "apply_candidate_list": [
                    {"family": "bad_entry_block", "stage": "holding_exit"}
                ],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "calibration_state": "adjust_up",
                        "safety_revert_required": False,
                    }
                ],
                "threshold_snapshot": {"bad_entry_block": {"apply_ready": True}},
                "post_apply_attribution": {"status": "pending_applied_cohort"},
                "safety_guard_pack": [{"family": "soft_stop_whipsaw_confirmation"}],
                "calibration_trigger_pack": [
                    {"family": "soft_stop_whipsaw_confirmation"}
                ],
                "rollback_guard_pack": [{"family": "bad_entry_block"}],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["source_date"] == "2026-04-30"
    assert manifest["candidates"] == [
        {"family": "bad_entry_block", "stage": "holding_exit"}
    ]
    assert (
        manifest["calibration_candidates"][0]["family"]
        == "soft_stop_whipsaw_confirmation"
    )
    assert (
        manifest["calibration_policy"]["condition_miss_action"] == "calibration_trigger"
    )
    saved = json.loads(
        (apply_dir / "threshold_apply_2026-05-04.json").read_text(encoding="utf-8")
    )
    assert saved["source_date"] == "2026-04-30"


def test_score65_74_entry_unlock_candidate_accepts_score60_74_alias_metrics():
    assert (
        mod._score65_74_entry_unlock_candidate(
            {
                "family": "score65_74_recovery_probe",
                "sample_count": 24,
                "sample_floor": 20,
                "source_metrics": {
                    "score60_74_avg_expected_ev_pct": 3.1,
                    "score60_74_avg_close_10m_pct": 1.4,
                    "order_bundle_submitted": 0,
                },
            }
        )
        is True
    )


def test_build_preopen_apply_manifest_accepts_calibrated_apply_candidate(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)

    (report_dir / "threshold_cycle_2026-05-07.json").write_text(
        json.dumps(
            {
                "date": "2026-05-07",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "apply_mode": "calibrated_apply_candidate",
                        "safety_revert_required": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-08",
        source_date="2026-05-07",
        apply_mode="calibrated_apply_candidate",
    )

    assert manifest["status"] == "calibrated_manifest_ready"
    assert manifest["runtime_change"] is False
    assert (
        manifest["calibration_candidates"][0]["apply_mode"]
        == "calibrated_apply_candidate"
    )
    assert manifest["calibration_policy"]["rollback_policy"] == "safety_breach_only"


def test_build_preopen_apply_manifest_blocks_legacy_candidate_without_handoff_contract(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)

    (report_dir / "threshold_cycle_2099-01-02.json").write_text(
        json.dumps(
            {
                "date": "2099-01-02",
                "calibration_candidates": [
                    {
                        "family": "scale_in_split_order_plan",
                        "stage": "scale_in",
                        "priority": 9,
                        "calibration_state": "adjust_up",
                        "allowed_runtime_apply": True,
                        "target_env_keys": ["SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2099-01-03",
        source_date="2099-01-02",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = next(
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "scale_in_split_order_plan"
    )
    assert decision["selected"] is False
    assert decision["decision_reason"] == (
        "runtime_handoff_contract_missing," "runtime_handoff_contract_version_mismatch"
    )
    assert manifest["runtime_handoff_contract_audit"] == {
        "required_from_target_date": "2026-08-04",
        "expected_version": 1,
        "source_version": 0,
        "version_match": False,
        "required_families": ["scale_in_split_order_plan"],
        "missing_families": ["scale_in_split_order_plan"],
    }
    assert (
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_build_preopen_apply_manifest_accepts_efficient_tradeoff_candidate(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-07.json").write_text(
        json.dumps(
            {
                "date": "2026-05-07",
                "apply_candidate_list": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "apply_mode": "efficient_tradeoff_canary_candidate",
                    }
                ],
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "apply_mode": "efficient_tradeoff_canary_candidate",
                        "calibration_state": "adjust_up",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-08",
        source_date="2026-05-07",
        apply_mode="efficient_tradeoff_canary_candidate",
    )

    assert manifest["status"] == "efficient_tradeoff_manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"][0]["family"] == "score65_74_recovery_probe"
    assert (
        manifest["calibration_policy"]["sample_shortfall_action"]
        == "cap_reduce_or_hold_sample_or_max_step_shrink"
    )


def test_auto_bounded_live_writes_runtime_env_with_ai_guard_and_stage_priority(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED",
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC",
                        ],
                        "recommended_values": {"enabled": True, "confirm_sec": 45},
                        "threshold_version": "soft_stop_whipsaw_confirmation:test",
                    },
                    {
                        "family": "bad_entry_refined_canary",
                        "stage": "holding_exit",
                        "priority": 20,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED"],
                        "recommended_values": {"enabled": True},
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "min_buy_pressure": 65.0,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "ai_model": "tier2-plus",
                "items": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    },
                    {
                        "family": "bad_entry_refined_canary",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_change"] is True
    selected = {item["family"] for item in manifest["auto_apply_selected"]}
    assert selected == {"soft_stop_whipsaw_confirmation", "score65_74_recovery_probe"}
    blocked = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "bad_entry_refined_canary"
    ][0]
    assert blocked["selected"] is False
    assert (
        blocked["decision_reason"]
        == "same_stage_owner_conflict:soft_stop_whipsaw_confirmation"
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=45" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65" in env_text


def test_auto_bounded_live_writes_dynamic_entry_price_resolver_env(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "dynamic_entry_price_resolver",
                        "stage": "entry",
                        "priority": 9,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALPING_ENTRY_PRICE_RESOLVER_ENABLED",
                            "SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS",
                            "SCALPING_NORMAL_DEFENSIVE_TICKS",
                            "SCALPING_NORMAL_DEFENSIVE_BPS",
                            "SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS",
                            "SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS",
                            "SCALPING_NORMAL_WEAK_DEFENSIVE_BPS",
                            "SCALPING_CONDITIONAL_1TICK_REAL_ENABLED",
                        ],
                        "current_values": {
                            "enabled": True,
                            "max_below_bid_bps": 80,
                            "normal_defensive_ticks": 3,
                            "normal_defensive_bps": 45,
                            "conditional_strong_defensive_bps": 20,
                            "normal_favorable_defensive_bps": 40,
                            "normal_weak_defensive_bps": 80,
                            "conditional_1tick_real_enabled": True,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "max_below_bid_bps": 70,
                            "normal_defensive_ticks": 2,
                            "normal_defensive_bps": 25,
                            "conditional_strong_defensive_bps": 10,
                            "normal_favorable_defensive_bps": 15,
                            "normal_weak_defensive_bps": 40,
                            "conditional_1tick_real_enabled": False,
                        },
                        "threshold_version": "dynamic_entry_price_resolver:test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "dynamic_entry_price_resolver",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-09",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_change"] is True
    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS"] == "70"
    assert env["KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_TICKS"] == "2"
    assert env["KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS"] == "25"
    assert env["KORSTOCKSCAN_SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS"] == "10"
    assert env["KORSTOCKSCAN_SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS"] == "15"
    assert env["KORSTOCKSCAN_SCALPING_NORMAL_WEAK_DEFENSIVE_BPS"] == "40"
    assert env["KORSTOCKSCAN_SCALPING_CONDITIONAL_1TICK_REAL_ENABLED"] == "false"


def test_preopen_apply_consumes_lifecycle_bucket_auto_apply_without_human_artifact(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    bridge_dir = tmp_path / "bridge"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim_auto"
    swing_sim_approval_dir = tmp_path / "swing_sim_auto"
    swing_sim_policy_dir = tmp_path / "swing_sim_policy"
    report_dir.mkdir(parents=True)
    bridge_dir.mkdir(parents=True)
    catalog_dir.mkdir(parents=True)
    sim_dir.mkdir(parents=True)
    swing_sim_approval_dir.mkdir(parents=True)
    swing_sim_policy_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(bridge_mod, "REPORT_DIR", bridge_dir)
    monkeypatch.setattr(discovery_mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(discovery_mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    monkeypatch.setattr(
        discovery_mod, "REPORT_DIR", report_dir / "lifecycle_bucket_discovery"
    )
    monkeypatch.setattr(swing_sim_mod, "SIM_AUTO_APPROVAL_DIR", swing_sim_approval_dir)
    monkeypatch.setattr(swing_sim_mod, "SWING_SIM_POLICY_DIR", swing_sim_policy_dir)

    (report_dir / "threshold_cycle_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "apply_candidate_list": [],
                "calibration_candidates": [],
            }
        ),
        encoding="utf-8",
    )
    (bridge_dir / "runtime_apply_bridge_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "candidates": [
                    {
                        "candidate_id": "scale_in_bucket_runtime_policy_v1:2026-05-22",
                        "family": bridge_mod.SCALE_IN_BRIDGE_FAMILY,
                        "stage": "scale_in",
                        "priority": 39,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "target_env_keys": [
                            "REVERSAL_ADD_MIN_AI_SCORE",
                            "REVERSAL_ADD_MIN_BUY_PRESSURE",
                        ],
                        "recommended_values": {
                            "reversal_add_min_ai_score": 65,
                            "reversal_add_min_buy_pressure": 60.0,
                        },
                        "current_values": {
                            "reversal_add_min_ai_score": 60,
                            "reversal_add_min_buy_pressure": 55.0,
                        },
                        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
                        "lifecycle_bucket_discovery_bucket_id": "scale_in:arm:AVG_DOWN",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {
                            "tier2_status": "parsed",
                            "tier2_policy": "fail_closed",
                        },
                        "source_bucket_keys": ["score=score_66_69"],
                        "source_buckets": [
                            {
                                "bucket_type": "scale_in_arm",
                                "bucket_key": "score=score_66_69",
                                "source_quality_gate": "pass",
                                "source_quality_adjusted_ev_pct": 1.25,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").write_text(
        "{}", encoding="utf-8"
    )
    (sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").write_text(
        json.dumps(
            {
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_bucket_ids": ["entry:combo:test"],
                "approved_bucket_count": 1,
            }
        ),
        encoding="utf-8",
    )
    (swing_sim_policy_dir / "swing_sim_policy_catalog_2026-05-22.json").write_text(
        json.dumps(
            {
                "schema_version": "swing_sim_policy_catalog_v1",
                "active_arm_priority_policies": [],
            }
        ),
        encoding="utf-8",
    )
    (swing_sim_approval_dir / "swing_sim_auto_approval_2026-05-22.json").write_text(
        json.dumps(
            {
                "report_type": "swing_sim_auto_approval",
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_source_ids": [
                    "swing_lifecycle_bucket_discovery",
                    "bottom_rebound_policy_auto_loop",
                ],
                "approved_policy_count": 2,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-23",
        source_date="2026-05-22",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_apply_bridge"]["approved"] == 1
    assert (
        manifest["runtime_apply_bridge"]["selected"][0]["family"]
        == bridge_mod.SCALE_IN_BRIDGE_FAMILY
    )
    assert manifest["lifecycle_bucket_discovery"]["approved"] == 1
    assert (
        manifest["lifecycle_bucket_discovery"]["selected"][0]["recommended_values"][
            "live_auto_apply_enabled"
        ]
        is False
    )
    assert manifest["swing_sim_auto_approval"]["approved"] == 1
    assert manifest["swing_sim_auto_approval"]["selected"][0][
        "approved_source_ids"
    ] == [
        "swing_lifecycle_bucket_discovery",
        "bottom_rebound_policy_auto_loop",
    ]


def test_preopen_apply_blocks_empty_lifecycle_bucket_sim_auto_approval(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "reports"
    runtime_dir = tmp_path / "runtime_env"
    bridge_dir = report_dir / "runtime_apply_bridge"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim_auto"
    apply_dir = tmp_path / "apply"
    for path in (report_dir, runtime_dir, bridge_dir, catalog_dir, sim_dir, apply_dir):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(bridge_mod, "REPORT_DIR", bridge_dir)
    monkeypatch.setattr(discovery_mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(discovery_mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    monkeypatch.setattr(
        discovery_mod, "REPORT_DIR", report_dir / "lifecycle_bucket_discovery"
    )

    (report_dir / "threshold_cycle_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "apply_candidate_list": [],
                "calibration_candidates": [],
            }
        ),
        encoding="utf-8",
    )
    (bridge_dir / "runtime_apply_bridge_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "candidates": []}),
        encoding="utf-8",
    )
    (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").write_text(
        "{}", encoding="utf-8"
    )
    (sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").write_text(
        json.dumps(
            {
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_bucket_ids": [],
                "approved_bucket_count": 0,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-23",
        source_date="2026-05-22",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["lifecycle_bucket_discovery"]["approved"] == 0
    assert manifest["lifecycle_bucket_discovery"]["selected"] == []
    assert (
        "sim_auto_approval_empty" in manifest["lifecycle_bucket_discovery"]["blocked"]
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-23.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE" not in env_text
    assert "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED=true" not in env_text


def test_auto_bounded_live_imports_latency_classifier_recommendation(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    latency_dir = report_dir / "latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    latency_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "apply_candidate_list": [],
                "calibration_candidates": [],
            }
        ),
        encoding="utf-8",
    )
    (latency_dir / "latency_classifier_recommendation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "latency_block_count": 24,
                "selected_profile_id": "balanced_1200_1500_0100",
                "calibration_candidates": [
                    {
                        "family": "latency_classifier_runtime_profile",
                        "stage": "entry_latency_classifier",
                        "priority": 6,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION",
                            "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION",
                            "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION",
                        ],
                        "current_values": {
                            "max_ws_age_ms_for_caution": 700,
                            "max_ws_jitter_ms_for_caution": 300,
                            "max_spread_ratio_for_caution": 0.005,
                        },
                        "recommended_values": {
                            "max_ws_age_ms_for_caution": 1200,
                            "max_ws_jitter_ms_for_caution": 1500,
                            "max_spread_ratio_for_caution": 0.01,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["latency_classifier_recommendation"]["status"] == "loaded"
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION"
        ]
        == "1200"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION"
        ]
        == "1500"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION"
        ]
        == "0.01"
    )
    assert not any(
        key.startswith("KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY")
        for key in manifest["runtime_env_overrides"]
    )


def test_auto_bounded_live_writes_lifecycle_decision_matrix_policy_env(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    policy_file = "data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-08.json"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "stage": "lifecycle",
                        "priority": 31,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "LIFECYCLE_DECISION_MATRIX_ENABLED",
                            "LIFECYCLE_DECISION_MATRIX_POLICY_FILE",
                            "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION",
                            "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED",
                            "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY",
                            "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "policy_file": policy_file,
                            "policy_version": "lifecycle_decision_matrix_v1_2026-05-08",
                            "promote_enabled": True,
                            "max_promotes_per_day": 3,
                            "min_stage_confidence": 0.6,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_FILE"
        ]
        == policy_file
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY"
        ]
        == "3"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE"
        ]
        == "0.6"
    )


def test_auto_bounded_live_writes_lifecycle_context_and_bias_off_env(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    context_file = (
        "data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-08.json"
    )
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "stage": "lifecycle",
                        "priority": 31,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_FILE",
                            "LIFECYCLE_AI_CONTEXT_VERSION",
                            "SCALP_ENTRY_ADM_ADVISORY_ENABLED",
                            "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED",
                            "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED",
                        ],
                        "recommended_values": {
                            "runtime_effect_enabled": False,
                            "lifecycle_ai_context_enabled": True,
                            "lifecycle_ai_context_file": context_file,
                            "lifecycle_ai_context_version": "lifecycle_ai_context_v1_2026-05-08",
                            "entry_adm_advisory_enabled": True,
                            "entry_adm_runtime_bias_enabled": False,
                            "holding_exit_matrix_advisory_enabled": True,
                            "holding_exit_matrix_runtime_bias_enabled": False,
                            "holding_exit_matrix_scale_in_bias_enabled": False,
                        },
                        "current_values": {
                            "runtime_effect_enabled": True,
                            "lifecycle_ai_context_enabled": False,
                            "lifecycle_ai_context_file": "",
                            "lifecycle_ai_context_version": "",
                            "entry_adm_advisory_enabled": True,
                            "entry_adm_runtime_bias_enabled": True,
                            "holding_exit_matrix_advisory_enabled": True,
                            "holding_exit_matrix_runtime_bias_enabled": True,
                            "holding_exit_matrix_scale_in_bias_enabled": True,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    env = manifest["runtime_env_overrides"]
    assert (
        env["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED"] == "false"
    )
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_FILE"] == context_file
    assert env["KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_ADVISORY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED"] == "false"


def test_lifecycle_context_overlay_bypasses_same_stage_runtime_selection(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    context_file = (
        "data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-08.json"
    )
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "bad_entry_refined_canary",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED"],
                        "recommended_values": {"enabled": True},
                        "current_values": {"enabled": False},
                    },
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "stage": "holding_exit",
                        "priority": 31,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "LIFECYCLE_DECISION_MATRIX_ENABLED",
                            "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_FILE",
                            "LIFECYCLE_AI_CONTEXT_VERSION",
                            "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "runtime_effect_enabled": False,
                            "lifecycle_ai_context_enabled": True,
                            "lifecycle_ai_context_file": context_file,
                            "lifecycle_ai_context_version": "lifecycle_ai_context_v1_2026-05-08",
                            "entry_adm_advisory_enabled": True,
                            "entry_adm_runtime_bias_enabled": False,
                            "holding_exit_matrix_advisory_enabled": True,
                            "holding_exit_matrix_runtime_bias_enabled": False,
                            "holding_exit_matrix_scale_in_bias_enabled": False,
                        },
                        "current_values": {
                            "enabled": False,
                            "runtime_effect_enabled": False,
                            "lifecycle_ai_context_enabled": False,
                            "lifecycle_ai_context_file": "",
                            "lifecycle_ai_context_version": "",
                            "entry_adm_runtime_bias_enabled": False,
                            "holding_exit_matrix_runtime_bias_enabled": False,
                            "holding_exit_matrix_scale_in_bias_enabled": False,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {"family": "bad_entry_refined_canary", "guard_accepted": True},
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "guard_accepted": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    selected_families = {item["family"] for item in manifest["auto_apply_selected"]}
    assert "lifecycle_decision_matrix_runtime" not in selected_families
    assert manifest["lifecycle_ai_context_overlay"]["selected"] is True
    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_FILE"] == context_file
    assert (
        env["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED"] == "false"
    )
    assert env["KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED"] == "false"


def test_auto_bounded_live_excludes_ai_instrumentation_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "ai_anomaly_route": "instrumentation_gap",
                        "route_action": "exclude_from_threshold_candidate_review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_blocked"
    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_file"] == str(
        runtime_dir / "threshold_runtime_env_2026-05-11.env"
    )
    assert (
        manifest["auto_apply_decisions"][0]["decision_reason"]
        == "ai_route_excluded_from_threshold_candidate"
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text


def test_latest_preopen_source_ignores_intraday_only_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (
        calibration_dir / "threshold_cycle_calibration_2026-05-18_intraday.json"
    ).write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "run_phase": "intraday",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_intraday.json").write_text(
        json.dumps({"ai_status": "parsed", "items": []}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "missing_source_report"
    assert manifest["runtime_change"] is False


def test_intraday_source_phase_blocks_auto_apply_even_when_candidate_ready(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    ai_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)

    (
        calibration_dir / "threshold_cycle_calibration_2026-05-18_intraday.json"
    ).write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "run_phase": "intraday",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
                        ],
                        "recommended_values": {"enabled": True},
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "sample_count": 50,
                        "sample_floor": 20,
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW",
                            "AI_WAIT6579_PROBE_CANARY_MAX_QTY",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "max_budget_krw": 50000,
                            "max_qty": 1,
                        },
                        "source_metrics": {
                            "entry_unlock_probe_ready": True,
                            "panic_state": "NORMAL",
                            "panic_regime_mode": "NORMAL",
                            "score65_74_avg_expected_ev_pct": 4.5,
                            "score65_74_avg_close_10m_pct": 5.2,
                            "order_bundle_submitted": 0,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_intraday.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "guard_decision": {
                            "anomaly_route": "instrumentation_gap",
                            "route_action": "exclude_from_threshold_candidate_review",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-18",
        source_date="2026-05-18",
        source_phase="intraday",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        include_families={"score65_74_recovery_probe"},
    )

    assert manifest["status"] == "auto_bounded_live_blocked"
    assert manifest["runtime_change"] is False
    assert manifest["source_phase_auto_apply_blocked"] is True
    assert manifest["warnings"] == ["intraday_source_phase_auto_apply_blocked"]
    assert manifest["auto_apply_decisions"] == []
    assert manifest["runtime_env_overrides"] == {}
    assert not (runtime_dir / "threshold_runtime_env_2026-05-18.env").exists()


def test_preopen_apply_does_not_fallback_to_intraday_when_postclose_ai_unavailable(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
                        ],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "unavailable",
                "parse_warnings": ["ai correction response not provided"],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_intraday.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        source_date="2026-05-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["ai_correction_review"]["status"] == "unavailable"
    assert manifest["ai_correction_review"]["phase"] == "postclose"
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "ai_review_missing"


def test_operator_runtime_env_lock_preserves_score65_probe_through_sample_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": False,
                        "safety_revert_required": False,
                        "calibration_state": "hold_sample",
                        "calibration_reason": "sample_shortfall_no_applied_probe_gap",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "ai_anomaly_route": "instrumentation_gap",
                        "route_action": "exclude_from_threshold_candidate_review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-05-18.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_entry_unlock_operator_override_2026-05-18",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-05-18",
                "min_observation_until_date": "2026-05-18",
                "allowed_close_reason_keywords": [
                    "safety_revert",
                    "severe_loss",
                    "stale_quote",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        source_date="2026-05-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is True
    assert decision["decision_reason"] == (
        "operator_runtime_env_lock_preserved:score65_74_entry_unlock_operator_override_2026-05-18"
    )
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"
        ]
        == "true"
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-19.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true" in env_text


def test_operator_runtime_env_lock_does_not_preserve_score65_probe_on_safety_revert(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": True,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {"family": "score65_74_recovery_probe", "guard_accepted": True}
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-05-18.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_entry_unlock_operator_override_2026-05-18",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-05-18",
                "min_observation_until_date": "2026-05-18",
                "allowed_close_reason_keywords": [
                    "safety_revert",
                    "severe_loss",
                    "stale_quote",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        source_date="2026-05-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "safety_revert_required"
    assert decision["operator_runtime_env_lock"]["allowed_close"] is True
    assert (
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_operator_runtime_env_lock_until_explicit_close_survives_observation_date(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-06-20.json").write_text(
        json.dumps(
            {
                "date": "2026-06-20",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-06-11.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_recovery_probe_real_operator_override_2026-06-11",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-06-11",
                "min_observation_until_date": "2026-06-12",
                "lock_until_explicit_close": True,
                "allowed_close_reason_keywords": [
                    "safety_revert",
                    "severe_loss",
                    "stale_quote",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-21",
        source_date="2026-06-20",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is True
    assert decision["decision_reason"] == (
        "operator_runtime_env_lock_preserved:score65_74_recovery_probe_real_operator_override_2026-06-11"
    )
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"
        ]
        == "true"
    )


def test_operator_runtime_env_lock_applies_when_target_date_reaches_active_from(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-06-11.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_recovery_probe_real_operator_override_2026-06-11",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-06-11",
                "min_observation_until_date": "2026-06-12",
                "explicit_close_required": True,
                "allowed_close_reason_keywords": [
                    "safety_revert",
                    "severe_loss",
                    "stale_quote",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is True
    assert decision["decision_reason"] == (
        "operator_runtime_env_lock_preserved:score65_74_recovery_probe_real_operator_override_2026-06-11"
    )
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"
        ]
        == "true"
    )


def test_operator_runtime_env_lock_supports_env_overrides_without_env_key(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-19.json").write_text(
        json.dumps({"date": "2026-05-19", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "scalp_sim_ai_budget_manager_2026-05-19.json").write_text(
        json.dumps(
            {
                "lock_id": "scalp_sim_ai_budget_manager_continuous",
                "enabled": True,
                "family": "scalp_sim_ai_budget_manager",
                "stage": "sim_holding_ai_budget",
                "active_from_date": "2026-05-19",
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_AI_MAX_CALLS_PER_MIN": "10",
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-20",
        source_date="2026-05-19",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "scalp_sim_ai_budget_manager"
    ][0]
    assert decision["selected"] is True
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED"]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AI_MAX_CALLS_PER_MIN"]
        == "10"
    )


def test_quote_consistency_operator_lock_enables_next_preopen(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (lock_dir / "quote_consistency_normalization_2026-06-29.json").write_text(
        json.dumps(
            {
                "lock_id": "quote_consistency_normalization_operator_apply_2026_06_29",
                "enabled": True,
                "family": "quote_consistency_normalization",
                "stage": "cross_lifecycle_quote_normalization",
                "active_from_date": "2026-06-29",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED": "true",
                    "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS": "700",
                    "KORSTOCKSCAN_QUOTE_CONSISTENCY_BLOCK_ENTRY_ON_DIVERGENCE": "true",
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-29",
        source_date="2026-06-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=True,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "quote_consistency_normalization"
    ][0]
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS"
        ]
        == "700"
    )


def test_sell_side_open_time_operator_lock_enables_next_preopen(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "sell_side_open_time_block_2026-06-19.json").write_text(
        json.dumps(
            {
                "lock_id": "sell_side_open_time_block_operator_override_2026-06-19",
                "enabled": True,
                "family": "sell_side_open_time_block_runtime",
                "stage": "exit_submit_time_guard",
                "active_from_date": "2026-06-19",
                "target_date": "2026-06-19",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED": "true",
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_UNTIL_HHMM": "09:05",
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_SCOPE": "all",
                    "KORSTOCKSCAN_SELL_WINDOWS": "08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00",
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-19",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "sell_side_open_time_block_runtime"
    ][0]
    assert decision["selected"] is True
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_UNTIL_HHMM"
        ]
        == "09:05"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_SCOPE"
        ]
        == "all"
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SELL_WINDOWS"]
        == "08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00"
    )


def test_operator_lock_preserved_when_source_report_missing(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (lock_dir / "sell_side_open_time_block_2026-06-19.json").write_text(
        json.dumps(
            {
                "lock_id": "sell_side_open_time_block_operator_override_2026-06-19",
                "enabled": True,
                "family": "sell_side_open_time_block_runtime",
                "stage": "exit_submit_time_guard",
                "active_from_date": "2026-06-19",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED": "true",
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_UNTIL_HHMM": "09:05",
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_SCOPE": "all",
                    "KORSTOCKSCAN_SELL_WINDOWS": "08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00",
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-19",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=True,
    )

    assert manifest["status"] == "operator_runtime_env_lock_ready_missing_source_report"
    assert manifest["runtime_change"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SELL_WINDOWS"]
        == "08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00"
    )
    assert (
        manifest["auto_apply_decisions"][0]["operator_runtime_env_lock"]["applied"]
        is True
    )
    assert manifest["runtime_env_handoff_verification"]["status"] == "pass"
    env_path = runtime_dir / "threshold_runtime_env_2026-06-19.env"
    env_manifest_path = runtime_dir / "threshold_runtime_env_2026-06-19.json"
    verify_path = runtime_dir / "threshold_runtime_env_verify_2026-06-19.json"
    assert env_path.exists()
    assert env_manifest_path.exists()
    assert verify_path.exists()
    env_text = env_path.read_text(encoding="utf-8")
    assert "export KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED=true" in env_text
    assert (
        "export KORSTOCKSCAN_SELL_WINDOWS=08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00"
        in env_text
    )


def test_weak_pullback_operator_lock_closes_for_same_stage_live_bucket(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-14.json").write_text(
        json.dumps(
            {
                "date": "2026-06-14",
                "calibration_candidates": [
                    {
                        "family": "future_live_submit_bucket",
                        "stage": "entry_pre_submit",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "weak_pullback_entry_block_2026-06-13.json").write_text(
        json.dumps(
            {
                "lock_id": "weak_pullback_entry_block_real_operator_override_2026-06-13",
                "enabled": True,
                "family": "weak_pullback_entry_block_runtime",
                "stage": "entry_pre_submit",
                "priority": 900,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-14",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["future_live_submit_bucket"]["selected"] is True
    weak_lock = decisions["weak_pullback_entry_block_runtime"]
    assert weak_lock["selected"] is False
    assert (
        weak_lock["decision_reason"]
        == "same_stage_owner_conflict:future_live_submit_bucket"
    )
    assert weak_lock["operator_runtime_env_lock"]["allowed_close"] is True
    assert (
        "KORSTOCKSCAN_SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_aggressive_entry_price_operator_lock_is_retired_without_formal_entry_price_candidate(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-14.json").write_text(
        json.dumps({"date": "2026-06-14", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "aggressive_entry_price_override_2026-06-13.json").write_text(
        json.dumps(
            {
                "lock_id": "aggressive_entry_price_override_real_operator_override_2026-06-13",
                "enabled": True,
                "family": "aggressive_entry_price_override_runtime",
                "stage": "entry",
                "priority": 900,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES": "defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
                    "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS": "35",
                    "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_TARGET_MODE": "best_bid_near",
                    "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS": "1",
                    "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS": "0",
                    "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS": "20",
                    "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_TARGET_MODE": "best_bid_near",
                    "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS": "1",
                    "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS": "0",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "dynamic_entry_price_resolver",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-14",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "aggressive_entry_price_override_runtime"
    ][0]
    assert decision["selected"] is False
    assert decision["decision_reason"].startswith("retired_runtime_family:")
    assert decision["operator_runtime_env_lock"]["applied"] is False
    assert (
        "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS"
        not in manifest["runtime_env_overrides"]
    )


def test_scalping_scanner_real_source_guard_operator_lock_applies(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-14.json").write_text(
        json.dumps({"date": "2026-06-14", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "scalping_scanner_real_source_guard_2026-06-14.json").write_text(
        json.dumps(
            {
                "lock_id": "scalping_scanner_real_source_guard_operator_override_2026-06-14",
                "enabled": True,
                "family": "scalping_scanner_real_source_guard_runtime",
                "stage": "entry",
                "priority": 900,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT": "0.0",
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP": "10",
                    "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE": "80",
                    "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE": "80",
                    "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_CNTR_STR": "110",
                    "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_SEC": "30",
                    "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MAX_SEC": "300",
                    "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT": "0.15",
                    "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT": "0.30",
                    "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_TIERING_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_DEMOTE_REALTIME_RANK_ONLY": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_DEMOTE_BID_IMBALANCE_ONLY": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_DEMOTE_OPEN_PRICE_JUMP_WITHOUT_VOLUME": "true",
                    "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_TAGS": "VWAP_RECLAIM,DRYUP_SQUEEZE,PRECLOSE",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-14",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "scalping_scanner_real_source_guard_runtime"
    ][0]
    assert decision["selected"] is True
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP"
        ]
        == "10"
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SCANNER_PROBE_MAX_SEC"]
        == "300"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_TIERING_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_DEMOTE_REALTIME_RANK_ONLY"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_DEMOTE_BID_IMBALANCE_ONLY"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_DEMOTE_OPEN_PRICE_JUMP_WITHOUT_VOLUME"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_ENABLED"
        ]
        == "true"
    )


def test_scalping_scanner_real_source_guard_coexists_with_score65_operator_lock(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-12.json").write_text(
        json.dumps({"date": "2026-06-12", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-06-11.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_recovery_probe_real_operator_override_2026-06-11",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-06-11",
                "explicit_close_required": True,
                "allowed_close_reason_keywords": [
                    "safety_revert",
                    "severe_loss",
                    "stale_quote",
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "scalping_scanner_real_source_guard_2026-06-14.json").write_text(
        json.dumps(
            {
                "lock_id": "scalping_scanner_real_source_guard_operator_override_2026-06-14",
                "enabled": True,
                "family": "scalping_scanner_real_source_guard_runtime",
                "stage": "entry",
                "priority": 900,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP": "10",
                    "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT": "0.15",
                    "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-12",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["score65_74_recovery_probe"]["selected"] is True
    assert decisions["scalping_scanner_real_source_guard_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP"
        ]
        == "10"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT"
        ]
        == "0.15"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_ENABLED"
        ]
        == "true"
    )


def test_score65_74_strong_micro_override_operator_lock_coexists_with_score65(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-15.json").write_text(
        json.dumps({"date": "2026-06-15", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-06-15.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_recovery_probe_real_operator_override_2026-06-15",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "allowed_close_reason_keywords": ["safety_revert_required"],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_strong_micro_override_2026-06-15.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_strong_micro_operator_override_2026-06-15",
                "enabled": True,
                "family": "score65_74_recovery_probe_strong_micro_override_runtime",
                "stage": "entry",
                "priority": 901,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED": "true",
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_BUY_PRESSURE": "85.0",
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_MICRO_VWAP_BP": "30.0",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "early_accel_recheck_2026-06-15.json").write_text(
        json.dumps(
            {
                "lock_id": "early_accel_recheck_operator_override_2026-06-15",
                "enabled": True,
                "family": "early_accel_recheck_runtime",
                "stage": "entry",
                "priority": 905,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED": "true",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED": "true",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE": "74",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-15",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["score65_74_recovery_probe"]["selected"] is True
    strong = decisions["score65_74_recovery_probe_strong_micro_override_runtime"]
    assert strong["selected"] is True
    early_accel = decisions["early_accel_recheck_runtime"]
    assert early_accel["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED"
        ]
        == "true"
    )


def test_score65_74_strong_micro_override_closes_for_entry_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-06-15.json").write_text(
        json.dumps(
            {
                "date": "2026-06-15",
                "calibration_candidates": [
                    {
                        "family": "dynamic_entry_price_resolver",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALPING_NORMAL_DEFENSIVE_BPS"],
                        "current_values": {"normal_defensive_bps": 50},
                        "recommended_values": {"normal_defensive_bps": 25},
                        "threshold_version": "dynamic_entry_price_resolver:test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-06-15_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "dynamic_entry_price_resolver",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_strong_micro_override_2026-06-15.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_strong_micro_operator_override_2026-06-15",
                "enabled": True,
                "family": "score65_74_recovery_probe_strong_micro_override_runtime",
                "stage": "entry",
                "priority": 901,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED": "true",
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_BUY_PRESSURE": "85.0",
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_MICRO_VWAP_BP": "30.0",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-15",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["dynamic_entry_price_resolver"]["selected"] is True
    strong = decisions["score65_74_recovery_probe_strong_micro_override_runtime"]
    assert strong["selected"] is False
    assert (
        strong["decision_reason"]
        == "same_stage_owner_conflict:dynamic_entry_price_resolver"
    )
    assert strong["operator_runtime_env_lock"]["allowed_close"] is True
    assert (
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_ENTRY_STAGE_LIVE_TUNING_SELECTED"
        ]
        == "true"
    )


def test_early_accel_recheck_operator_lock_emits_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-15.json").write_text(
        json.dumps({"date": "2026-06-15", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "early_accel_recheck_2026-06-15.json").write_text(
        json.dumps(
            {
                "lock_id": "early_accel_recheck_operator_override_2026-06-15",
                "enabled": True,
                "family": "early_accel_recheck_runtime",
                "stage": "entry",
                "priority": 905,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED": "true",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MAX_COUNT": "2",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC": "20",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MAX_AGE_SEC": "180",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL": "1.10",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP": "0.0",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_ALLOW_LIQUIDITY_BLOCKED": "true",
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_ALLOW_STRENGTH_BLOCKED": "true",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED": "true",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE": "60",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE": "74",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_BUY_MIN_SCORE": "75",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT": "2",
                    "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL": "1",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-15",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["early_accel_recheck_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MAX_COUNT"]
        == "2"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC"
        ]
        == "20"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE"
        ]
        == "74"
    )


def test_early_accel_recheck_operator_lock_closes_for_entry_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-14.json").write_text(
        json.dumps(
            {
                "date": "2026-06-14",
                "calibration_candidates": [
                    {
                        "family": "future_entry_live_bucket",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALPING_NORMAL_DEFENSIVE_BPS"],
                        "current_values": {"normal_defensive_bps": 50},
                        "recommended_values": {"normal_defensive_bps": 45},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "early_accel_recheck_2026-06-15.json").write_text(
        json.dumps(
            {
                "lock_id": "early_accel_recheck_operator_override_2026-06-15",
                "enabled": True,
                "family": "early_accel_recheck_runtime",
                "stage": "entry",
                "priority": 905,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-14",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["future_entry_live_bucket"]["selected"] is True
    lock_decision = decisions["early_accel_recheck_runtime"]
    assert lock_decision["selected"] is False
    assert (
        lock_decision["decision_reason"]
        == "same_stage_owner_conflict:future_entry_live_bucket"
    )
    assert (
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_ai_numeric_consistency_recheck_operator_lock_emits_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "ai_numeric_consistency_recheck_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "ai_numeric_consistency_recheck_operator_override_2026-06-18",
                "enabled": True,
                "family": "ai_numeric_consistency_recheck_runtime",
                "stage": "entry",
                "priority": 906,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED": "true",
                    "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_MIN_SCORE": "60",
                    "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_BUY_MIN_SCORE": "75",
                    "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_MIN_FEATURE_PASS_COUNT": "3",
                    "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_MAX_PER_SYMBOL": "1",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["ai_numeric_consistency_recheck_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_BUY_MIN_SCORE"
        ]
        == "75"
    )


def test_pre_submit_liquidity_relief_operator_lock_emits_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "pre_submit_liquidity_relief_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "pre_submit_liquidity_relief_operator_override_2026-06-18",
                "enabled": True,
                "family": "pre_submit_liquidity_relief_runtime",
                "stage": "entry",
                "priority": 907,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED": "true",
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_AI_SCORE": "75",
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_TICK_ACCEL": "1.10",
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_BUY_PRESSURE": "68",
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_MICRO_VWAP_BP": "0.0",
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MAX_PER_SYMBOL": "1",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["pre_submit_liquidity_relief_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_BUY_PRESSURE"
        ]
        == "68"
    )


def test_entry_opportunity_recheck_operator_lock_emits_next_preopen_env(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-07-02.json").write_text(
        json.dumps({"date": "2026-07-02", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-06-11.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_recovery_probe_real_operator_override_2026-06-11",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "priority": 900,
                "active_from_date": "2026-06-11",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "entry_opportunity_recheck_2026-07-03.json").write_text(
        json.dumps(
            {
                "lock_id": "entry_opportunity_recheck_operator_override_2026-07-03",
                "enabled": True,
                "family": "entry_opportunity_recheck_runtime",
                "stage": "entry",
                "priority": 908,
                "active_from_date": "2026-07-03",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": "69",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE": "74.999",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_RECHECK_PER_SYMBOL": "1",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_DAILY_RECHECK": "10",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_DAILY_BUY_RECOVERY": "3",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_WS_AGE_MS": "1500",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_FORBID_DANGER": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_FRESH_QUOTE": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_INTRADAY_ESCALATION_ENABLED": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_STEP_RECHECK": "10",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_STEP_BUY_RECOVERY": "2",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MAX_DAILY_RECHECK": "30",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MAX_DAILY_BUY_RECOVERY": "7",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MIN_SUCCESSFUL_RECOVERIES": "2",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MIN_AVG_PROFIT_PCT": "0.0",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MIN_PEAK_PROFIT_PCT": "0.3",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MAX_WORST_PROFIT_PCT": "-0.6",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "entry_live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-07-03",
        source_date="2026-07-02",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["entry_opportunity_recheck_runtime"]["selected"] is True
    assert (
        decisions["entry_opportunity_recheck_runtime"]["operator_runtime_env_lock"][
            "applied"
        ]
        is True
    )
    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE"] == "69"
    assert env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE"] == "74.999"
    assert env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_DAILY_BUY_RECOVERY"] == "3"
    assert (
        env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_INTRADAY_ESCALATION_ENABLED"]
        == "true"
    )
    assert (
        env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MAX_DAILY_RECHECK"]
        == "30"
    )
    assert (
        env["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ESCALATION_MAX_DAILY_BUY_RECOVERY"]
        == "7"
    )


def test_score69_74_recovery_probe_operator_lock_preserves_micro_source_quality_env():
    env = mod._lock_env_overrides(
        {
            "family": "score65_74_recovery_probe",
            "env_overrides": {
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED": "true",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE": "69",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MAX_SCORE": "74",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE": "65.0",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL": "1.2",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP": "0.0",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP": "10.0",
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION": (
                    "score69_74_recovery_probe:operator_override:2026-07-04"
                ),
            },
        }
    )

    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE"] == "69"
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MAX_SCORE"] == "74"
    assert (
        env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP"]
        == "10.0"
    )


def test_weak_context_late_entry_guard_operator_lock_emits_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "weak_context_late_entry_guard_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "weak_context_late_entry_guard_operator_override_2026-06-18",
                "enabled": True,
                "family": "weak_context_late_entry_guard_runtime",
                "stage": "entry",
                "priority": 910,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_LOOKBACK_SEC": "900",
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_BLOCK_COUNT": "2",
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_TICK_ACCEL": "1.10",
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_BUY_PRESSURE": "0.0",
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_MICRO_VWAP_BP": "0.0",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "dynamic_entry_price_resolver",
                    "entry_live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["weak_context_late_entry_guard_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_BLOCK_COUNT"
        ]
        == "2"
    )


def test_weak_context_and_liquidity_relief_operator_locks_coexist(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "pre_submit_liquidity_relief_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "pre_submit_liquidity_relief_operator_override_2026-06-18",
                "enabled": True,
                "family": "pre_submit_liquidity_relief_runtime",
                "stage": "entry",
                "priority": 907,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED": "true",
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_AI_SCORE": "75",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "weak_context_late_entry_guard_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "weak_context_late_entry_guard_operator_override_2026-06-18",
                "enabled": True,
                "family": "weak_context_late_entry_guard_runtime",
                "stage": "entry",
                "priority": 908,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_BLOCK_COUNT": "2",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["pre_submit_liquidity_relief_runtime"]["selected"] is True
    assert decisions["weak_context_late_entry_guard_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED"
        ]
        == "true"
    )


def test_weak_context_late_entry_guard_operator_lock_closes_for_entry_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-17.json").write_text(
        json.dumps(
            {
                "date": "2026-06-17",
                "calibration_candidates": [
                    {
                        "family": "future_entry_live_bucket",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALPING_NORMAL_DEFENSIVE_BPS"],
                        "current_values": {"normal_defensive_bps": 25},
                        "recommended_values": {"normal_defensive_bps": 20},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "weak_context_late_entry_guard_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "weak_context_late_entry_guard_operator_override_2026-06-18",
                "enabled": True,
                "family": "weak_context_late_entry_guard_runtime",
                "stage": "entry",
                "priority": 910,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-17",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["future_entry_live_bucket"]["selected"] is True
    lock_decision = decisions["weak_context_late_entry_guard_runtime"]
    assert lock_decision["selected"] is False
    assert (
        lock_decision["decision_reason"]
        == "same_stage_owner_conflict:future_entry_live_bucket"
    )
    assert (
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_ENTRY_STAGE_LIVE_TUNING_SELECTED"
        ]
        == "true"
    )


def test_pre_submit_liquidity_relief_operator_lock_closes_for_entry_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-17.json").write_text(
        json.dumps(
            {
                "date": "2026-06-17",
                "calibration_candidates": [
                    {
                        "family": "future_entry_live_bucket",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALPING_NORMAL_DEFENSIVE_BPS"],
                        "current_values": {"normal_defensive_bps": 25},
                        "recommended_values": {"normal_defensive_bps": 20},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "pre_submit_liquidity_relief_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "pre_submit_liquidity_relief_operator_override_2026-06-18",
                "enabled": True,
                "family": "pre_submit_liquidity_relief_runtime",
                "stage": "entry",
                "priority": 907,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-17",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["future_entry_live_bucket"]["selected"] is True
    lock_decision = decisions["pre_submit_liquidity_relief_runtime"]
    assert lock_decision["selected"] is False
    assert (
        lock_decision["decision_reason"]
        == "same_stage_owner_conflict:future_entry_live_bucket"
    )
    assert (
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_ENTRY_STAGE_LIVE_TUNING_SELECTED"
        ]
        == "true"
    )


def test_never_green_defer_clamp_operator_lock_emits_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "never_green_defer_clamp_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "never_green_defer_clamp_operator_override_2026-06-18",
                "enabled": True,
                "family": "never_green_defer_clamp_runtime",
                "stage": "holding_exit",
                "priority": 901,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_ENABLED": "true",
                    "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MAX_PEAK_PROFIT_PCT": "0.05",
                    "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MIN_DEFER_COUNT": "2",
                    "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MAX_MICRO_VWAP_BP": "0.0",
                    "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MIN_LOSS_PCT": "0.0",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "holding_exit_matrix_runtime",
                    "soft_stop_whipsaw_confirmation",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["never_green_defer_clamp_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MIN_DEFER_COUNT"
        ]
        == "2"
    )


def test_never_green_defer_clamp_operator_lock_closes_for_holding_exit_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-17.json").write_text(
        json.dumps(
            {
                "date": "2026-06-17",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding_exit",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "never_green_defer_clamp_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "never_green_defer_clamp_operator_override_2026-06-18",
                "enabled": True,
                "family": "never_green_defer_clamp_runtime",
                "stage": "holding_exit",
                "priority": 901,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "soft_stop_whipsaw_confirmation",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-17",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["soft_stop_whipsaw_confirmation"]["selected"] is True
    lock_decision = decisions["never_green_defer_clamp_runtime"]
    assert lock_decision["selected"] is False
    assert (
        lock_decision["decision_reason"]
        == "same_stage_owner_conflict:soft_stop_whipsaw_confirmation"
    )
    assert (
        "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_HOLDING_EXIT_LIVE_TUNING_SELECTED"
        ]
        == "true"
    )


def test_real_pyramid_scale_in_quality_guard_operator_lock_applies_without_formal_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-18.json").write_text(
        json.dumps({"date": "2026-06-18", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "real_pyramid_scale_in_quality_guard_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "real_pyramid_scale_in_quality_guard_operator_override_2026-06-18",
                "enabled": True,
                "family": "real_pyramid_scale_in_quality_guard_runtime",
                "stage": "scale_in",
                "priority": 901,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_CANCEL_ENABLED": "true",
                    "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_AI_SCORE": "66",
                    "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_TICK_ACCEL": "1.10",
                    "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_BUY_PRESSURE": "60",
                    "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_MICRO_VWAP_BP": "0.0",
                    "KORSTOCKSCAN_RECENT_EXIT_CANDIDATE_PYRAMID_BLOCK_ENABLED": "true",
                    "KORSTOCKSCAN_RECENT_EXIT_CANDIDATE_PYRAMID_BLOCK_SEC": "180",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "scale_in_runtime_bridge",
                    "holding_exit_matrix_runtime",
                    "live_auto_apply_ready",
                    "tuning_override",
                    "safety_revert_required",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["real_pyramid_scale_in_quality_guard_runtime"]["selected"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_RECENT_EXIT_CANDIDATE_PYRAMID_BLOCK_SEC"
        ]
        == "180"
    )


def test_real_pyramid_scale_in_quality_guard_operator_lock_closes_for_scale_in_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)
    monkeypatch.setattr(
        mod, "_scale_in_live_owner_family", lambda *args: "scale_in_runtime_bridge"
    )

    (report_dir / "threshold_cycle_2026-06-17.json").write_text(
        json.dumps(
            {
                "date": "2026-06-17",
                "calibration_candidates": [
                    {
                        "family": "scale_in_runtime_bridge",
                        "stage": "scale_in",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "KORSTOCKSCAN_SCALE_IN_LIVE_TUNING_SELECTED"
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "real_pyramid_scale_in_quality_guard_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "real_pyramid_scale_in_quality_guard_operator_override_2026-06-18",
                "enabled": True,
                "family": "real_pyramid_scale_in_quality_guard_runtime",
                "stage": "scale_in",
                "priority": 901,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "scale_in_runtime_bridge",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-17",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    lock_decision = decisions["real_pyramid_scale_in_quality_guard_runtime"]
    assert lock_decision["selected"] is False
    assert (
        lock_decision["decision_reason"]
        == "same_stage_owner_conflict:scale_in_runtime_bridge"
    )
    assert (
        "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALE_IN_LIVE_TUNING_SELECTED"]
        == "true"
    )


def test_ai_numeric_consistency_recheck_operator_lock_closes_for_entry_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-17.json").write_text(
        json.dumps(
            {
                "date": "2026-06-17",
                "calibration_candidates": [
                    {
                        "family": "future_entry_live_bucket",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALPING_NORMAL_DEFENSIVE_BPS"],
                        "current_values": {"normal_defensive_bps": 50},
                        "recommended_values": {"normal_defensive_bps": 45},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "ai_numeric_consistency_recheck_2026-06-18.json").write_text(
        json.dumps(
            {
                "lock_id": "ai_numeric_consistency_recheck_operator_override_2026-06-18",
                "enabled": True,
                "family": "ai_numeric_consistency_recheck_runtime",
                "stage": "entry",
                "priority": 906,
                "active_from_date": "2026-06-18",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-18",
        source_date="2026-06-17",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["future_entry_live_bucket"]["selected"] is True
    lock_decision = decisions["ai_numeric_consistency_recheck_runtime"]
    assert lock_decision["selected"] is False
    assert (
        lock_decision["decision_reason"]
        == "same_stage_owner_conflict:future_entry_live_bucket"
    )
    assert (
        "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_scalping_scanner_real_source_guard_closes_for_same_stage_live_owner(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-14.json").write_text(
        json.dumps(
            {
                "date": "2026-06-14",
                "calibration_candidates": [
                    {
                        "family": "future_entry_live_bucket",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALPING_NORMAL_DEFENSIVE_BPS"],
                        "current_values": {"normal_defensive_bps": 50},
                        "recommended_values": {"normal_defensive_bps": 45},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "scalping_scanner_real_source_guard_2026-06-14.json").write_text(
        json.dumps(
            {
                "lock_id": "scalping_scanner_real_source_guard_operator_override_2026-06-14",
                "enabled": True,
                "family": "scalping_scanner_real_source_guard_runtime",
                "stage": "entry",
                "priority": 900,
                "active_from_date": "2026-06-15",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN": "true",
                    "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP": "10",
                    "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_TIERING_ENABLED": "true",
                },
                "allowed_close_reason_keywords": [
                    "same_stage_owner_conflict",
                    "tuning_override",
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-14",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    assert decisions["future_entry_live_bucket"]["selected"] is True
    scanner_decision = decisions["scalping_scanner_real_source_guard_runtime"]
    assert scanner_decision["selected"] is False
    assert (
        scanner_decision["decision_reason"]
        == "same_stage_owner_conflict:future_entry_live_bucket"
    )
    assert (
        "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_TIERING_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_retired_runtime_families_are_never_selected_even_with_operator_locks(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-14.json").write_text(
        json.dumps(
            {
                "date": "2026-06-14",
                "calibration_candidates": [
                    {
                        "family": "late_entry_price_drift_guard_runtime",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_LATE_ENTRY_PRICE_DRIFT_GUARD_ENABLED"
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    retired_locks = {
        "aggressive_entry_price_override_2026-06-13.json": (
            "aggressive_entry_price_override_runtime",
            "entry",
            {"KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED": "true"},
        ),
        "soft_stop_dynamic_grace_2026-06-13.json": (
            "soft_stop_dynamic_grace_runtime",
            "holding_exit",
            {"KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED": "true"},
        ),
        "preset_tp_soft_stop_2026-06-15.json": (
            "preset_tp_soft_stop_runtime",
            "holding_exit",
            {"KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_OVERRIDE_ENABLED": "true"},
        ),
    }
    for name, (family, stage, overrides) in retired_locks.items():
        (lock_dir / name).write_text(
            json.dumps(
                {
                    "lock_id": f"{family}_legacy_lock",
                    "enabled": True,
                    "family": family,
                    "stage": stage,
                    "priority": 20,
                    "active_from_date": "2026-06-15",
                    "explicit_close_required": True,
                    "env_overrides": overrides,
                    "allowed_close_reason_keywords": ["same_stage_owner_conflict"],
                }
            ),
            encoding="utf-8",
        )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-15",
        source_date="2026-06-14",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decisions = {item["family"]: item for item in manifest["auto_apply_decisions"]}
    env = manifest["runtime_env_overrides"]
    for family in (
        "aggressive_entry_price_override_runtime",
        "soft_stop_dynamic_grace_runtime",
        "preset_tp_soft_stop_runtime",
        "late_entry_price_drift_guard_runtime",
    ):
        assert decisions[family]["selected"] is False
        assert decisions[family]["decision_reason"].startswith(
            "retired_runtime_family:"
        )
    assert "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED" not in env
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED" not in env
    assert "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_OVERRIDE_ENABLED" not in env
    assert "KORSTOCKSCAN_SCALP_LATE_ENTRY_PRICE_DRIFT_GUARD_ENABLED" not in env


def test_scalp_sim_candidate_window_operator_lock_applies_240_daily_quota(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-29.json").write_text(
        json.dumps({"date": "2026-05-29", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "scalp_sim_candidate_window_expansion_2026-05-19.json").write_text(
        json.dumps(
            {
                "lock_id": "scalp_sim_candidate_window_expansion_continuous_2026-05-19",
                "enabled": True,
                "family": "scalp_sim_candidate_window_expansion",
                "stage": "sim_entry_candidate_window",
                "active_from_date": "2026-05-19",
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY": "240",
                    "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY": (
                        "09:00-10:00=84,10:00-12:00=48,12:00-14:00=60,14:00-15:30=48"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-29",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "scalp_sim_candidate_window_expansion"
    ][0]
    assert decision["selected"] is True
    assert decision["operator_runtime_env_lock"]["applied"] is True
    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY"] == "240"
    assert env["KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY"] == (
        "09:00-10:00=84,10:00-12:00=48,12:00-14:00=60,14:00-15:30=48"
    )


def test_swing_approval_required_request_does_not_auto_apply_without_artifact(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    report_dir.mkdir(parents=True)
    swing_request_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0",
                    "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                    "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    "blocked_real_order_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                },
                "approval_requests": [
                    {
                        "approval_id": "swing_runtime_approval:2026-05-08:swing_model_floor",
                        "family": "swing_model_floor",
                        "stage": "selection",
                        "target_env_keys": ["SWING_FLOOR_BULL"],
                        "current_values": {"floor_bull": 0.35},
                        "recommended_values": {"floor_bull": 0.30},
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["swing_runtime_approval"]["requested"] == 1
    assert manifest["swing_runtime_approval"]["approved"] == 0
    assert "approval_artifact_missing" in manifest["swing_runtime_approval"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SWING_FLOOR_BULL" not in env_text


def test_swing_user_approval_artifact_applies_env_and_keeps_dry_run(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_runtime_approval:2026-05-08:swing_model_floor"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0",
                    "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                    "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    "blocked_real_order_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "family": "swing_model_floor",
                        "stage": "selection",
                        "target_env_keys": ["SWING_FLOOR_BULL", "SWING_FLOOR_BEAR"],
                        "current_values": {"floor_bull": 0.35, "floor_bear": 0.40},
                        "recommended_values": {"floor_bull": 0.30, "floor_bear": 0.35},
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_runtime_approvals_2026-05-08.json").write_text(
        json.dumps(
            {"approved_requests": [{"approval_id": approval_id, "approved": True}]}
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert manifest["swing_runtime_approval"]["approved"] == 1
    assert "real_canary_policy" not in manifest["swing_runtime_approval"]
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_FLOOR_BULL"] == "0.3"
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"
        ]
        == "true"
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SWING_FLOOR_BULL=0.3" in env_text
    assert "KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true" in env_text


def test_swing_scale_in_real_canary_auto_approves_without_separate_artifact(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_scale_in_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "scale_in_real_canary_policy": {
                    "policy_id": "swing_scale_in_real_canary_phase0"
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_scale_in_real_canary_phase0",
                        "family": "swing_scale_in_real_canary_phase0",
                        "stage": "scale_in",
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": [
                            "SWING_SCALE_IN_REAL_CANARY_ENABLED",
                            "SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_QTY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION",
                            "SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT",
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {
                            "enabled": True,
                            "max_order_qty": 1,
                            "max_orders_per_day": 1,
                            "max_orders_per_position": 1,
                            "require_approval_artifact": False,
                        },
                        "dry_run_required": False,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert (
        manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    )
    assert (
        "blocked_legacy_real_canary_removed:swing_scale_in_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["approved"] == 0
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY" not in env_text


def test_swing_one_share_real_canary_auto_approves_without_separate_artifact(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_one_share_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0"
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "family": "swing_one_share_real_canary_phase0",
                        "stage": "real_canary_entry",
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "target_env_keys": [
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_QTY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW",
                            "SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT",
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {
                            "enabled": True,
                            "allowed_codes": "123456",
                            "max_order_qty": 1,
                            "max_new_entries_per_day": 1,
                            "max_open_positions": 3,
                            "max_total_notional_krw": 300000,
                            "require_approval_artifact": False,
                        },
                        "candidate_codes": ["123456"],
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert (
        manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    )
    assert (
        "blocked_legacy_real_canary_removed:swing_one_share_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["approved"] == 0
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY" not in env_text


def test_swing_scale_in_real_canary_rejects_qty_cap_above_phase0(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_scale_in_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "scale_in_real_canary_policy": {
                    "policy_id": "swing_scale_in_real_canary_phase0"
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_scale_in_real_canary_phase0",
                        "family": "swing_scale_in_real_canary_phase0",
                        "stage": "scale_in",
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": [
                            "SWING_SCALE_IN_REAL_CANARY_ENABLED",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_QTY",
                        ],
                        "recommended_values": {"enabled": True, "max_order_qty": 2},
                        "dry_run_required": False,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert (
        "blocked_legacy_real_canary_removed:swing_scale_in_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ENABLED" not in env_text


def test_swing_real_canary_does_not_auto_apply_without_auto_approval_state(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_one_share_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0"
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "family": "swing_one_share_real_canary_phase0",
                        "stage": "real_canary_entry",
                        "calibration_state": "approval_required",
                        "target_env_keys": [
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "allowed_codes": "123456",
                        },
                        "candidate_codes": ["123456"],
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert (
        "blocked_legacy_real_canary_removed:swing_one_share_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED" not in env_text


def test_swing_one_share_real_canary_artifact_applies_env_and_keeps_dry_run(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_one_share_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0"
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "family": "swing_one_share_real_canary_phase0",
                        "stage": "real_canary_entry",
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "target_env_keys": [
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_QTY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW",
                            "SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT",
                        ],
                        "current_values": {
                            "enabled": False,
                            "allowed_codes": "",
                            "max_order_qty": 1,
                            "max_new_entries_per_day": 1,
                            "max_open_positions": 3,
                            "max_total_notional_krw": 300000,
                            "require_approval_artifact": True,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "allowed_codes": "123456",
                            "max_order_qty": 1,
                            "max_new_entries_per_day": 1,
                            "max_open_positions": 3,
                            "max_total_notional_krw": 300000,
                            "require_approval_artifact": True,
                        },
                        "candidate_codes": ["123456"],
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_one_share_real_canary_2026-05-08.json").write_text(
        json.dumps(
            {
                "policy_id": "swing_one_share_real_canary_phase0",
                "approved": True,
                "target_date": "2026-05-11",
                "allowed_codes": ["123456"],
                "max_order_qty": 1,
                "max_new_entries_per_day": 1,
                "max_open_positions": 3,
                "max_total_notional_krw": 300000,
                "approval_source_report": "data/report/swing_runtime_approval/swing_runtime_approval_2026-05-08.json",
                "approved_request_ids": [approval_id],
                "expires_after_target_date": True,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_overrides"] == {}
    assert (
        manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    )
    assert (
        "blocked_legacy_real_canary_removed:swing_one_share_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["selected"] == []


def test_swing_scale_in_real_canary_artifact_applies_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_scale_in_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "scale_in_real_canary_policy": {
                    "policy_id": "swing_scale_in_real_canary_phase0"
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_scale_in_real_canary_phase0",
                        "family": "swing_scale_in_real_canary_phase0",
                        "stage": "scale_in",
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": [
                            "SWING_SCALE_IN_REAL_CANARY_ENABLED",
                            "SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_QTY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION",
                        ],
                        "current_values": {
                            "enabled": False,
                            "allowed_arms": "",
                            "max_order_qty": 1,
                            "max_orders_per_day": 1,
                            "max_orders_per_position": 1,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "allowed_arms": "PYRAMID,AVG_DOWN",
                            "max_order_qty": 1,
                            "max_orders_per_day": 1,
                            "max_orders_per_position": 1,
                        },
                        "dry_run_required": False,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_scale_in_real_canary_2026-05-08.json").write_text(
        json.dumps(
            {
                "policy_id": "swing_scale_in_real_canary_phase0",
                "approved": True,
                "target_date": "2026-05-11",
                "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                "max_order_qty": 1,
                "max_orders_per_day": 1,
                "max_orders_per_position": 1,
                "approval_source_report": "data/report/swing_runtime_approval/swing_runtime_approval_2026-05-08.json",
                "approved_request_ids": [approval_id],
                "expires_after_target_date": True,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_overrides"] == {}
    assert (
        manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    )
    assert (
        "blocked_legacy_real_canary_removed:swing_scale_in_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["selected"] == []


def test_build_preopen_apply_manifest_reports_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", tmp_path / "apply_plans")

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "missing_source_report"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"] == []


def test_scalp_sim_scale_in_window_approval_writes_runtime_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    approval_dir = tmp_path / "approvals"
    report_dir.mkdir(parents=True)
    approval_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(
        mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency"
    )

    (report_dir / "threshold_cycle_2026-05-19.json").write_text(
        json.dumps({"date": "2026-05-19", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-19.json").write_text(
        json.dumps(
            {
                "policy_id": "scalp_sim_scale_in_window_expansion",
                "family": "scalp_sim_scale_in_window_expansion",
                "approved": True,
                "approval_state": "sim_auto_approved",
                "human_approval_required": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality_status": "pass",
                "target_env_keys": [
                    "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED",
                    "SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS",
                    "SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT",
                    "SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT",
                    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION",
                    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY",
                ],
                "recommended_values": {
                    "enabled": True,
                    "allowed_arms": "PYRAMID,AVG_DOWN",
                    "min_profit_pct": -2.5,
                    "max_profit_pct": 2.5,
                    "max_orders_per_position": 1,
                    "max_orders_per_day": 30,
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-20",
        source_date="2026-05-19",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS"
        ]
        == "PYRAMID,AVG_DOWN"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY"
        ]
        == "30"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_EXECUTION_OBSERVATION_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_EXECUTION_ARMS"
        ]
        == "PASSIVE_BASELINE,MARKETABLE_OBSERVATION"
    )
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"][0]["family"] == (
        "scalp_sim_scale_in_window_expansion"
    )
    assert manifest["scalp_sim_scale_in_window_approval"]["decisions"][0][
        "decision_reason"
    ] == ("sim_auto_approval_artifact_accepted")
    assert manifest["calibration_candidates"] == []


def test_scalp_sim_scale_in_window_artifact_is_sim_auto_approved(tmp_path, monkeypatch):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)

    (report_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text(
        json.dumps(
            {
                "summary": {"status": "pass"},
                "sources": {
                    "scalp_sim_scale_in": {
                        "rows": 3,
                        "filled_events": 1,
                        "unfilled_events": 2,
                    }
                },
                "policy_entries": [
                    {
                        "stage": "scale_in",
                        "sample": 3,
                        "joined_sample": 3,
                        "source_quality_gate": "hold_sample",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval(
        "2026-05-22"
    )

    assert artifact["approved"] is True
    assert artifact["approval_state"] == "sim_auto_approved"
    assert artifact["human_approval_required"] is False
    assert artifact["decision_authority"] == "sim_auto_approval_only"
    assert artifact["runtime_effect"] is False
    assert artifact["allowed_runtime_apply"] is True
    assert artifact["actual_order_submitted"] is False
    assert artifact["broker_order_forbidden"] is True
    assert artifact["source_quality_status"] == "pass"
    assert artifact["blocked_reasons"] == []
    assert artifact["recommended_values"]["execution_observation_enabled"] is True
    assert artifact["recommended_values"]["execution_arms"] == (
        "PASSIVE_BASELINE,MARKETABLE_OBSERVATION"
    )
    assert (
        "SCALP_SIM_SCALE_IN_EXECUTION_OBSERVATION_ENABLED"
        in artifact["target_env_keys"]
    )
    assert (
        artifact["approval_contract"]["operator_action"]
        == "none_required_for_sim_policy"
    )
    saved = json.loads(
        (
            approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-22.json"
        ).read_text(encoding="utf-8")
    )
    assert saved["approval_state"] == "sim_auto_approved"


def test_scalp_sim_scale_in_window_artifact_blocks_missing_source_report(
    tmp_path, monkeypatch
):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval(
        "2026-05-22"
    )

    assert artifact["approved"] is False
    assert artifact["approval_state"] == "source_quality_blocked"
    assert artifact["source_quality_status"] == "source_report_missing"
    assert artifact["blocked_reasons"] == ["source_report_missing"]


def test_scalp_sim_scale_in_window_artifact_blocks_unreadable_source_report(
    tmp_path, monkeypatch
):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)
    (report_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text(
        "{not-json", encoding="utf-8"
    )

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval(
        "2026-05-22"
    )

    assert artifact["approved"] is False
    assert artifact["approval_state"] == "source_quality_blocked"
    assert artifact["source_quality_status"] == "source_report_unreadable"
    assert artifact["blocked_reasons"] == ["source_report_unreadable"]


def test_scalp_sim_scale_in_window_artifact_blocks_unknown_matrix_status(
    tmp_path, monkeypatch
):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)
    (report_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text(
        json.dumps({"summary": {"status": "warning"}}), encoding="utf-8"
    )

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval(
        "2026-05-22"
    )

    assert artifact["approved"] is False
    assert artifact["allowed_runtime_apply"] is False
    assert artifact["source_quality_status"] == "warning"
    assert artifact["blocked_reasons"] == ["warning"]


def test_scalp_sim_scale_in_window_artifact_blocks_source_quality_blocked_matrix(
    tmp_path, monkeypatch
):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)
    (report_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text(
        json.dumps({"summary": {"status": "source_quality_blocked"}}), encoding="utf-8"
    )

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval(
        "2026-05-22"
    )

    assert artifact["approved"] is False
    assert artifact["approval_state"] == "source_quality_blocked"
    assert artifact["blocked_reasons"] == ["source_quality_blocked"]


def test_scalp_sim_scale_in_window_preopen_rejects_source_quality_blocked_artifact(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    approval_dir = tmp_path / "approvals"
    report_dir.mkdir(parents=True)
    approval_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(
        mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency"
    )

    (report_dir / "threshold_cycle_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-22.json").write_text(
        json.dumps(
            {
                "policy_id": "scalp_sim_scale_in_window_expansion",
                "family": "scalp_sim_scale_in_window_expansion",
                "approved": False,
                "approval_state": "source_quality_blocked",
                "human_approval_required": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality_status": "source_report_missing",
                "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
                "recommended_values": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-26",
        source_date="2026-05-22",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert (
        manifest["runtime_env_overrides"].get(
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
        )
        is None
    )
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"] == []
    assert (
        "sim_auto_approval_not_approved"
        in manifest["scalp_sim_scale_in_window_approval"]["blocked"]
    )


def _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    approval_dir = tmp_path / "sim_auto_approvals"
    policy_dir = tmp_path / "scalp_sim_policies"
    legacy_approval_dir = tmp_path / "approvals"
    for directory in (report_dir, approval_dir, policy_dir, legacy_approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", legacy_approval_dir)
    monkeypatch.setattr(
        mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency"
    )
    monkeypatch.setattr(scalp_sim_auto_mod, "SIM_AUTO_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scalp_sim_auto_mod, "SCALP_SIM_POLICY_DIR", policy_dir)
    (report_dir / "threshold_cycle_2026-05-26.json").write_text(
        json.dumps({"date": "2026-05-26", "calibration_candidates": []}),
        encoding="utf-8",
    )
    return runtime_dir, approval_dir, policy_dir, legacy_approval_dir


def _scalp_sim_policy_catalog_payload(**extra):
    payload = {
        "schema_version": "scalp_sim_policy_catalog_v1",
        "generated_at": "2026-05-26T15:40:00+09:00",
        "generator_provenance": {
            "hash_algorithm": "sha256",
            "files": mod._generator_hashes(mod.SCALP_SIM_POLICY_STALENESS_CHECK_FILES),
        },
    }
    payload.update(extra)
    return payload


def test_scalp_sim_auto_approval_writes_sim_policy_env(tmp_path, monkeypatch):
    runtime_dir, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    lifecycle_catalog_dir = tmp_path / "lifecycle_bucket_catalog"
    lifecycle_sim_dir = tmp_path / "lifecycle_sim_auto"
    lifecycle_report_dir = tmp_path / "lifecycle_bucket_discovery"
    lifecycle_catalog_dir.mkdir(parents=True)
    lifecycle_sim_dir.mkdir(parents=True)
    lifecycle_report_dir.mkdir(parents=True)
    monkeypatch.setattr(discovery_mod, "CATALOG_DIR", lifecycle_catalog_dir)
    monkeypatch.setattr(discovery_mod, "SIM_AUTO_APPROVAL_DIR", lifecycle_sim_dir)
    monkeypatch.setattr(discovery_mod, "REPORT_DIR", lifecycle_report_dir)
    catalog_path = policy_dir / "scalp_sim_policy_catalog_2026-05-26.json"
    lifecycle_catalog_path = (
        lifecycle_catalog_dir / "lifecycle_bucket_catalog_2026-05-26.json"
    )
    catalog_path.write_text(
        json.dumps(
            _scalp_sim_policy_catalog_payload(
                active_sim_priority_seeds=[
                    {
                        "active_seed_id": "active_seed_preopen",
                        "source_parent_bucket_id": "parent_positive",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_blocked_ai_score",
                        },
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    lifecycle_catalog_path.write_text(
        json.dumps({"schema_version": "lifecycle_bucket_catalog_v1"}), encoding="utf-8"
    )
    (
        lifecycle_sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-26.json"
    ).write_text(
        json.dumps(
            {
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_bucket_ids": ["entry:combo:test"],
                "approved_bucket_count": 1,
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": [
                    "lifecycle_bucket_discovery",
                    "scalp_sim_scale_in_window_approval",
                ],
                "approved_policy_count": 2,
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_scale_in_window_expansion",
                        "target_env_keys": [
                            "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
                        ],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED"]
        == "true"
    )
    assert manifest["runtime_env_overrides"][
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE"
    ] == str(catalog_path)
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_VERSION"]
        == "scalp_sim_auto_approval:2026-05-26"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE"
        ]
        == "2026-05-26"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED"
        ]
        == "true"
    )
    assert manifest["runtime_env_overrides"][
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE"
    ] == str(lifecycle_catalog_path)
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION"
        ]
        == "lifecycle_bucket_discovery:2026-05-26"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED"
        ]
        == "false"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["scalp_sim_auto_approval"]["selected"][0]["family"]
        == "scalp_sim_auto_approval"
    )
    assert manifest["scalp_sim_auto_approval"]["selected"][0][
        "active_sim_priority_seed_ids"
    ] == ["active_seed_preopen"]
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"] == []
    assert (
        manifest["lifecycle_bucket_discovery"]["selected"][0]["family"]
        == "lifecycle_bucket_discovery_sim_auto_approval"
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-27.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE=2026-05-26" in env_text
    assert "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE=" in env_text


def test_scalp_sim_auto_approval_missing_keeps_legacy_scale_in_fallback(
    tmp_path, monkeypatch
):
    _, _, _, legacy_approval_dir = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (
        legacy_approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-26.json"
    ).write_text(
        json.dumps(
            {
                "policy_id": "scalp_sim_scale_in_window_expansion",
                "family": "scalp_sim_scale_in_window_expansion",
                "approved": True,
                "approval_state": "sim_auto_approved",
                "human_approval_required": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality_status": "pass",
                "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
                "recommended_values": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"][0]["family"] == (
        "scalp_sim_scale_in_window_expansion"
    )
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
        ]
        == "true"
    )


def test_scalp_sim_auto_approval_blocks_pre_clean_baseline_embedded_plan(
    tmp_path, monkeypatch
):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(
            _scalp_sim_policy_catalog_payload(
                hypothesis_observation_plan={
                    "schema_version": "ldm_hypothesis_observation_plan_v1",
                    "source_report_date": "2026-06-01",
                    "hypotheses": [{"soft_hypothesis_id": "archive_only"}],
                }
            )
        ),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["lifecycle_bucket_discovery"],
                "approved_policy_count": 1,
                "approved_policies": [{"policy_id": "source_only"}],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "scalp_sim_policy_catalog_hypothesis_plan_clean_baseline_invalid"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )


def test_scalp_sim_auto_approval_blocked_does_not_write_env(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        "{}", encoding="utf-8"
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_scalp_sim_auto_approval_rejects_empty_policy_artifact(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(_scalp_sim_policy_catalog_payload()),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": [],
                "approved_policy_count": 0,
                "approved_policies": [],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "scalp_sim_auto_approval_empty"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_scalp_sim_auto_approval_rejects_active_priority_posterior_prefix(
    tmp_path, monkeypatch
):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(
            _scalp_sim_policy_catalog_payload(
                active_sim_priority_seeds=[
                    {
                        "active_seed_id": "active_seed_bad",
                        "source_parent_bucket_id": "parent_positive",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_action_decision",
                            "exit_outcome_parent": "posterior_positive",
                        },
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "runtime_effect": False,
                    }
                ],
            )
        ),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["lifecycle_bucket_discovery"],
                "approved_policy_count": 1,
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_candidate_window_expansion",
                        "target_env_keys": [
                            "SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED"
                        ],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "active_sim_priority_seed_observable_prefix_forbidden_dimension"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )
    assert (
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_scalp_sim_auto_approval_rejects_malformed_policy_count(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(_scalp_sim_policy_catalog_payload()),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["scalp_sim_scale_in_window_approval"],
                "approved_policy_count": "not-a-number",
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_scale_in_window_expansion",
                        "target_env_keys": [
                            "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
                        ],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "scalp_sim_auto_approval_empty"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )


def test_scalp_sim_auto_approval_blocks_catalog_stale_after_generator_change(
    tmp_path, monkeypatch
):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    generator_file = tmp_path / "lifecycle_bucket_discovery.py"
    generator_file.write_text("# newer generator\n", encoding="utf-8")
    monkeypatch.setattr(
        mod, "SCALP_SIM_POLICY_STALENESS_CHECK_FILES", (generator_file,)
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "generated_at": "2026-05-26T15:40:00+09:00",
                "generator_provenance": {
                    "hash_algorithm": "sha256",
                    "files": {"lifecycle_bucket_discovery.py": "old_hash"},
                },
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_old",
                        "source_parent_bucket_id": "parent_old",
                        "status": "cooldown",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["lifecycle_bucket_discovery"],
                "approved_policy_count": 1,
                "approved_policies": [
                    {
                        "source_id": "lifecycle_bucket_discovery",
                        "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "scalp_sim_policy_catalog_stale_after_generator_change"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )


def test_scalp_sim_auto_approval_blocks_catalog_missing_generator_provenance(
    tmp_path, monkeypatch
):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps({"schema_version": "scalp_sim_policy_catalog_v1"}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["lifecycle_bucket_discovery"],
                "approved_policy_count": 1,
                "approved_policies": [
                    {
                        "source_id": "lifecycle_bucket_discovery",
                        "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert (
        "scalp_sim_policy_catalog_generated_at_missing"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )
    assert (
        "scalp_sim_policy_catalog_generator_provenance_missing"
        in manifest["scalp_sim_auto_approval"]["blocked"]
    )


def test_scalp_sim_auto_approval_ignores_non_scalp_nested_env_keys(
    tmp_path, monkeypatch
):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(
        tmp_path, monkeypatch
    )
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(_scalp_sim_policy_catalog_payload()),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["scalp_sim_scale_in_window_approval"],
                "approved_policy_count": 1,
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_scale_in_window_expansion",
                        "target_env_keys": [
                            "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                        ],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
        ]
        == "true"
    )
    assert (
        "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED"
        not in manifest["runtime_env_overrides"]
    )


def test_runtime_apply_bridge_blocks_source_quality_blocked_live_candidate(
    tmp_path, monkeypatch
):
    runtime_dir, bridge_dir, _approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = bridge_mod.SCALE_IN_BRIDGE_FAMILY
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "scale_in",
                        "priority": 39,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {
                            "tier2_status": "parsed",
                            "tier2_policy": "fail_closed",
                        },
                        "target_env_keys": ["REVERSAL_ADD_MIN_AI_SCORE"],
                        "recommended_values": {"reversal_add_min_ai_score": 55},
                        "current_values": {"reversal_add_min_ai_score": 60},
                        "source_bucket_keys": ["scale_in:blocked"],
                        "source_buckets": [
                            {
                                "bucket_type": "scale_in_arm",
                                "bucket_key": "scale_in:blocked",
                                "source_quality_gate": "source_quality_blocked",
                                "source_quality_adjusted_ev_pct": 1.7,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["runtime_apply_bridge"]["approved"] == 0
    assert (
        "source_bucket_source_quality_blocked:scale_in_bucket_runtime_policy_v1"
        in manifest["runtime_apply_bridge"]["blocked"]
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-06-01.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_REVERSAL_ADD_MIN_AI_SCORE" not in env_text


def _install_runtime_bridge_test_dirs(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    bridge_dir = tmp_path / "runtime_apply_bridge"
    approval_dir = tmp_path / "approvals"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    for directory in (report_dir, bridge_dir, approval_dir, swing_request_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(
        mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency"
    )
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(bridge_mod, "REPORT_DIR", bridge_dir)
    monkeypatch.setattr(bridge_mod, "APPROVAL_DIR", approval_dir)
    (report_dir / "threshold_cycle_2026-05-30.json").write_text(
        json.dumps({"date": "2026-05-30", "calibration_candidates": []}),
        encoding="utf-8",
    )
    return runtime_dir, bridge_dir, approval_dir


def test_runtime_apply_bridge_ignores_retired_entry_family(tmp_path, monkeypatch):
    runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = "entry_wait6579_score66_69_recovery_gate_v1"
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "entry_only_bridge_metadata",
                        "allowed_runtime_apply": False,
                        "live_auto_apply": False,
                        "metadata_only": True,
                        "bridge_exclusion_reason": "entry_only_bridge_metadata_not_live_candidate",
                        "target_env_keys": [],
                        "recommended_values": {"enabled": False},
                        "current_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "ldm_entry_runtime_bridge_2026-05-30.json").write_text(
        json.dumps({"approved": True, "family": family, "candidate_id": candidate_id}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["runtime_apply_bridge"]["blocked"] == []
    assert "metadata" not in manifest["runtime_apply_bridge"]
    assert manifest["runtime_apply_bridge"]["selected"] == []
    env_text = (runtime_dir / "threshold_runtime_env_2026-06-01.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text


def test_runtime_apply_bridge_does_not_reactivate_retired_entry_live_candidate(
    tmp_path, monkeypatch
):
    runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = "entry_wait6579_score66_69_recovery_gate_v1"
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "bounded_entry_probe_recovery_live_auto",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {
                            "tier2_status": "parsed",
                            "tier2_policy": "fail_closed",
                        },
                        "target_env_keys": [],
                        "recommended_values": {
                            "enabled": True,
                            "min_score": 66,
                            "max_score": 69,
                            "threshold_version": candidate_id,
                        },
                        "current_values": {
                            "enabled": False,
                            "min_score": 65,
                            "max_score": 74,
                            "threshold_version": "runtime_default",
                        },
                        "source_bucket_keys": [
                            "score=score_66_69|source=wait6579_ev_cohort"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert manifest["runtime_change"] is False
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env
    assert manifest["runtime_apply_bridge"]["selected"] == []
    assert "metadata" not in manifest["runtime_apply_bridge"]
    env_manifest = json.loads(
        (runtime_dir / "threshold_runtime_env_2026-06-01.json").read_text(
            encoding="utf-8"
        )
    )
    assert family not in env_manifest["selected_families"]


def test_runtime_apply_bridge_greenfield_live_auto_writes_full_lifecycle_env(
    tmp_path, monkeypatch
):
    runtime_dir, bridge_dir, _approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = bridge_mod.GREENFIELD_REAL_ENV_FAMILY
    policy_file = tmp_path / "greenfield_real_env_policy_2026-05-30.json"
    candidate_id = f"{family}:2026-05-30"
    policy_file.write_text(
        json.dumps(
            {
                "policy_id": family,
                "policy_version": candidate_id,
                "scope": "full_lifecycle",
                "allowlist": [
                    {
                        "bucket_id": "entry:score_66_69",
                        "family": "entry_bucket_runtime_policy_v1",
                        "stage": "entry",
                        "action": "BUY",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                    {
                        "bucket_id": "submit:allow_submit:thin_ok",
                        "family": "submit_bucket_runtime_policy_v1",
                        "stage": "submit",
                        "action": "ALLOW_SUBMIT",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                    {
                        "bucket_id": "holding:flow:baseline_hold",
                        "family": "holding_bucket_runtime_policy_v1",
                        "stage": "holding",
                        "action": "HOLD",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                    {
                        "bucket_id": "exit:rule:baseline_exit",
                        "family": "exit_bucket_runtime_policy_v1",
                        "stage": "exit",
                        "action": "SELL",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "greenfield_real_env",
                        "priority": 7,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "full_lifecycle_greenfield_real_env_authority",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "target_env_keys": [
                            "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
                            "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION",
                            "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "scope": "full_lifecycle",
                            "policy_file": str(policy_file),
                            "policy_version": candidate_id,
                            "telegram_enabled": True,
                        },
                        "current_values": {
                            "enabled": False,
                            "scope": "inactive",
                            "policy_file": "",
                            "policy_version": "runtime_default",
                            "telegram_enabled": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert manifest["runtime_change"] is True
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_SCOPE"] == "full_lifecycle"
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE"] == str(
        policy_file
    )
    assert (
        env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION"] == candidate_id
    )
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_TELEGRAM_ENABLED"] == "true"
    env_manifest = json.loads(
        (runtime_dir / "threshold_runtime_env_2026-06-01.json").read_text(
            encoding="utf-8"
        )
    )
    assert family in env_manifest["selected_families"]


def test_runtime_apply_bridge_greenfield_blocks_missing_policy_file(
    tmp_path, monkeypatch
):
    _runtime_dir, bridge_dir, _approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = bridge_mod.GREENFIELD_REAL_ENV_FAMILY
    policy_file = tmp_path / "missing_greenfield_real_env_policy_2026-05-30.json"
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "greenfield_real_env",
                        "priority": 7,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "full_lifecycle_greenfield_real_env_authority",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "target_env_keys": [
                            "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
                            "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION",
                            "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "scope": "full_lifecycle",
                            "policy_file": str(policy_file),
                            "policy_version": candidate_id,
                            "telegram_enabled": True,
                        },
                        "current_values": {
                            "enabled": False,
                            "scope": "inactive",
                            "policy_file": "",
                            "policy_version": "runtime_default",
                            "telegram_enabled": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert (
        "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED"
        not in manifest["runtime_env_overrides"]
    )
    assert (
        f"greenfield_policy_file_missing:{family}"
        in manifest["runtime_apply_bridge"]["blocked"]
    )


def test_runtime_apply_bridge_ignores_retired_entry_approval_artifact(
    tmp_path, monkeypatch
):
    runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = "entry_wait6579_score66_69_recovery_gate_v1"
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "ready_for_approval",
                        "allowed_runtime_apply": True,
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                        "current_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "ldm_entry_runtime_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "approved": True,
                "family": family,
                "candidate_id": candidate_id,
                "approval_id": "entry-approve",
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["runtime_apply_bridge"]["blocked"] == []
    assert "metadata" not in manifest["runtime_apply_bridge"]
    assert manifest["runtime_apply_bridge"]["selected"] == []
    env_text = (runtime_dir / "threshold_runtime_env_2026-06-01.env").read_text(
        encoding="utf-8"
    )
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text


def test_runtime_apply_bridge_scale_live_auto_writes_tighten_env_without_guard_bypass(
    tmp_path, monkeypatch
):
    _runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = bridge_mod.SCALE_IN_BRIDGE_FAMILY
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "scale_in",
                        "priority": 39,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {
                            "tier2_status": "parsed",
                            "tier2_policy": "fail_closed",
                        },
                        "target_env_keys": [
                            "SCALPING_ENABLE_PYRAMID",
                            "REVERSAL_ADD_MIN_AI_SCORE",
                            "REVERSAL_ADD_MIN_BUY_PRESSURE",
                            "REVERSAL_ADD_MIN_TICK_ACCEL",
                        ],
                        "recommended_values": {
                            "effective_qty_cap": 1,
                            "scalping_enable_pyramid": False,
                            "reversal_add_min_ai_score": 65,
                            "reversal_add_min_buy_pressure": 60.0,
                            "reversal_add_min_tick_accel": 1.05,
                        },
                        "current_values": {
                            "effective_qty_cap": 1,
                            "scalping_enable_pyramid": True,
                            "reversal_add_min_ai_score": 60,
                            "reversal_add_min_buy_pressure": 55.0,
                            "reversal_add_min_tick_accel": 0.95,
                        },
                        "source_buckets": [
                            {
                                "bucket_type": "scale_in_arm",
                                "bucket_key": "pyramid:tighten",
                                "source_quality_gate": "pass",
                                "source_quality_adjusted_ev_pct": -1.4,
                            }
                        ],
                        "forbidden_uses": [
                            "scale_in_safety_guard_bypass",
                            "sizing_formula_runtime_apply_without_guard",
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert manifest["runtime_change"] is True
    assert env["KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID"] == "false"
    assert env["KORSTOCKSCAN_REVERSAL_ADD_MIN_AI_SCORE"] == "65"
    assert env["KORSTOCKSCAN_REVERSAL_ADD_MIN_BUY_PRESSURE"] == "60"
    assert env["KORSTOCKSCAN_REVERSAL_ADD_MIN_TICK_ACCEL"] == "1.05"
    assert (
        "scale_in_safety_guard_bypass"
        in manifest["runtime_apply_bridge"]["selected"][0]["forbidden_uses"]
    )


def test_runtime_apply_bridge_partial_scale_arm_emits_only_ready_arm_env(
    tmp_path, monkeypatch
):
    _runtime_dir, bridge_dir, _approval_dir = _install_runtime_bridge_test_dirs(
        tmp_path, monkeypatch
    )
    family = bridge_mod.SCALE_IN_BRIDGE_FAMILY
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": f"{family}:2026-05-30",
                        "family": family,
                        "stage": "scale_in",
                        "priority": 39,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {
                            "tier2_status": "parsed",
                            "tier2_policy": "fail_closed",
                        },
                        "target_env_keys": ["SCALPING_ENABLE_PYRAMID"],
                        "recommended_values": {
                            "scalping_enable_pyramid": False,
                            "reversal_add_min_ai_score": 65,
                            "reversal_add_min_buy_pressure": 60.0,
                            "reversal_add_min_tick_accel": 1.05,
                        },
                        "current_values": {"scalping_enable_pyramid": True},
                        "source_buckets": [
                            {
                                "bucket_type": "scale_in_arm",
                                "bucket_key": "pyramid:tighten",
                                "source_quality_gate": "pass",
                                "source_quality_adjusted_ev_pct": -0.8,
                            }
                        ],
                        "forbidden_uses": ["scale_in_safety_guard_bypass"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID"] == "false"
    assert "KORSTOCKSCAN_REVERSAL_ADD_MIN_AI_SCORE" not in env
    assert "KORSTOCKSCAN_REVERSAL_ADD_MIN_BUY_PRESSURE" not in env
    assert "KORSTOCKSCAN_REVERSAL_ADD_MIN_TICK_ACCEL" not in env


# ── hold separation tests ──


def test_hold_carry_forward_previously_enabled_no_blockers(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-10.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-10",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC": "20",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is True
    assert decision["decision_reason"].startswith(
        "hold_carry_forward_previous_runtime:"
    )
    assert decision["hold_carry_forward"]["previous_selected"] is True
    assert decision["selection_change_class"] == "carried_forward_unchanged"
    assert (
        decision["env_overrides"][
            "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
        ]
        == "true"
    )
    assert (
        decision["env_overrides"][
            "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC"
        ]
        == "20"
    )
    runtime_manifest = json.loads(
        (runtime_dir / "threshold_runtime_env_2026-06-11.json").read_text(
            encoding="utf-8"
        )
    )
    assert runtime_manifest["selection_change_summary"][
        "carried_forward_or_unchanged"
    ] == ["soft_stop_whipsaw_confirmation"]


def test_pyramid_ev_hold_preserves_explicit_operator_lock(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    lock_dir.mkdir(parents=True)
    (lock_dir / "scalping_pyramid_min_profit.json").write_text(
        json.dumps(
            {
                "lock_id": "scalping_pyramid_min_profit_explicit_lock",
                "enabled": True,
                "family": "scalping_pyramid_quality_gate",
                "stage": "scale_in",
                "active_from_date": "2026-08-20",
                "explicit_close_required": True,
                "env_overrides": {
                    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": "1.1",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-08-20.json").write_text(
        json.dumps(
            {
                "date": "2026-08-20",
                "calibration_candidates": [
                    {
                        "family": "scalping_pyramid_quality_gate",
                        "stage": "scale_in",
                        "priority": 39,
                        "allowed_runtime_apply": False,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "calibration_reason": (
                            "normal_winner_expansion_non_positive_ev_hold"
                        ),
                        "source_quality_gate": "pass_with_row_exclusions",
                        "source_quality_blocked": None,
                        "target_env_keys": [],
                        "recommended_values": {"min_profit_pct": 1.5},
                        "current_values": {"min_profit_pct": 1.5},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-08-21",
        source_date="2026-08-20",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = next(
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "scalping_pyramid_quality_gate"
    )

    assert decision["selected"] is True
    assert decision["selection_change_class"] == "operator_lock_preserved"
    assert decision["decision_reason"].startswith(
        "operator_runtime_env_lock_preserved:"
    )
    assert decision["env_overrides"] == {
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": "1.1"
    }
    assert (
        manifest["runtime_env_overrides"][
            "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT"
        ]
        == "1.1"
    )


def test_previous_runtime_env_uses_latest_manifest_across_calendar_gap(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)

    (runtime_dir / "threshold_runtime_env_2026-06-12.json").write_text(
        json.dumps(
            {
                "target_date": "2026-06-12",
                "selected_families": ["scale_in_split_order_plan"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_PLAN_ENABLED": "true"
                },
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "threshold_runtime_env_2026-06-14.json").write_text(
        "{}",
        encoding="utf-8",
    )
    # Verify artifacts must not be mistaken for runtime manifests.
    (runtime_dir / "threshold_runtime_env_verify_2026-06-14.json").write_text(
        json.dumps({"target_date": "2026-06-14", "selected_families": ["wrong"]}),
        encoding="utf-8",
    )

    families, manifest = mod._load_previous_runtime_env_selected_families("2026-06-15")

    assert families == {"scale_in_split_order_plan"}
    assert manifest["target_date"] == "2026-06-12"


def test_sell_side_window_hold_carry_forward_keeps_window_keys(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-30.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-30",
                "selected_families": ["sell_side_open_time_block_runtime"],
                "env_overrides": {
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED": "true",
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_UNTIL_HHMM": "09:05",
                    "KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_SCOPE": "all",
                    "KORSTOCKSCAN_SELL_WINDOWS": "08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-30.json").write_text(
        json.dumps(
            {
                "date": "2026-06-30",
                "calibration_candidates": [
                    {
                        "family": "sell_side_open_time_block_runtime",
                        "stage": "exit_submit_time_guard",
                        "priority": 906,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-07-01",
        source_date="2026-06-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_UNTIL_HHMM"] == "09:05"
    assert env["KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_SCOPE"] == "all"
    assert (
        env["KORSTOCKSCAN_SELL_WINDOWS"]
        == "08:05:00-08:49:00,09:05:00-15:19:00,16:05:00-19:49:00"
    )


def test_hold_not_previously_enabled_rejects(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "hold_not_previously_enabled"


def test_hold_sample_always_blocks_even_when_previously_enabled(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-10.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-10",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold_sample",
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "calibration_state_blocked:hold_sample"


def test_hold_carry_forward_blocked_by_safety_revert_required(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-10.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-10",
                "selected_families": ["score65_74_recovery_probe"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": True,
                        "calibration_state": "hold",
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "safety_revert_required"


def test_hold_carry_forward_blocked_by_source_quality(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-10.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-10",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "source_quality_blocked": "hard gap in pipeline events",
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert "hold_carry_forward_blocked" in decision["decision_reason"]
    assert "source_quality_hard_block" in decision["decision_reason"]


def test_verify_runtime_env_handoff_pass(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    result = mod.verify_runtime_env_handoff("2026-06-11")
    assert result["status"] == "pass"
    assert result["passed"] is True
    assert result["findings"] == []
    assert result["missing_family_count"] == 0


def test_verify_runtime_env_handoff_rejects_retired_operator_overrides(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED=true",
                "export KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED=true",
                "export KORSTOCKSCAN_SCALP_LATE_ENTRY_PRICE_DRIFT_GUARD_ENABLED=true",
                "export KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED=true",
                "export KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE=2026-07-20",
                "export KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC=2",
                "export KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC=5",
                "export KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS=10",
            ]
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-20")

    assert result["status"] == "fail"
    assert result["fail_reason"] == "retired_runtime_selection_or_override_present"
    assert result["operator_runtime_override_keys"] == []
    assert result["retired_operator_override_keys_blocked"] == [
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC",
        "KORSTOCKSCAN_SCALP_LATE_ENTRY_PRICE_DRIFT_GUARD_ENABLED",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED",
        "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED",
    ]
    assert {item["severity"] for item in result["findings"]} == {
        "retired_runtime_override_present"
    }


def test_verify_runtime_env_handoff_rejects_retired_manifest_overrides(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-20.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-20",
                "selected_families": [],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_LATE_ENTRY_PRICE_DRIFT_GUARD_ENABLED": "true",
                    "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED": "true",
                    "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE": "2026-07-20",
                    "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC": "2",
                    "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC": "5",
                    "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS": "10",
                },
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-20")

    assert result["status"] == "fail"
    assert result["retired_manifest_override_keys_blocked"] == [
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC",
        "KORSTOCKSCAN_SCALP_LATE_ENTRY_PRICE_DRIFT_GUARD_ENABLED",
    ]
    assert result["findings"][0]["source"] == "threshold_runtime_env_manifest"


def test_verify_runtime_env_handoff_rejects_retired_selected_family(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-20.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-20",
                "selected_families": ["soft_stop_dynamic_grace_runtime"],
                "env_overrides": {},
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-20")

    assert result["status"] == "fail"
    assert result["fail_reason"] == "retired_runtime_selection_or_override_present"
    assert result["retired_selected_families_blocked"] == [
        "soft_stop_dynamic_grace_runtime"
    ]
    assert result["findings"][0]["severity"] == "retired_runtime_family_selected"


def test_verify_runtime_env_handoff_verifies_selected_pyramid_quality_gate(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-20.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-20",
                "selected_families": ["scalping_pyramid_quality_gate"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": "1.1"
                },
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-20")

    assert result["status"] == "pass"
    assert result["unverified_selected_families"] == []


def test_write_runtime_env_strips_all_retired_runtime_keys(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime_env"
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    retired_overrides = {key: "true" for key in mod.RETIRED_RUNTIME_ENV_KEYS}

    mod._write_runtime_env(
        "2026-07-20",
        {"source_date": "2026-07-16", "generated_at": "2026-07-20T08:00:00+09:00"},
        retired_overrides,
    )

    rendered = (runtime_dir / "threshold_runtime_env_2026-07-20.env").read_text(
        encoding="utf-8"
    )
    assert not any(key in rendered for key in mod.RETIRED_RUNTIME_ENV_KEYS)


def test_verify_runtime_env_handoff_missing_key(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {},
            }
        ),
        encoding="utf-8",
    )
    result = mod.verify_runtime_env_handoff("2026-06-11")
    assert result["status"] == "fail"
    assert result["passed"] is False
    assert len(result["findings"]) == 1
    assert result["findings"][0]["severity"] == "runtime_env_handoff_missing"
    assert result["missing_family_count"] == 1


def test_verify_runtime_env_handoff_rejects_stale_operator_split_policy(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    policy_file = tmp_path / "entry_split_order_policy_2026-07-07.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "entry-split-stale",
                "source_date": "2026-07-07",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "threshold_runtime_env_2026-07-14.json").write_text(
        json.dumps(
            {"target_date": "2026-07-14", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=true",
                f"export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE={policy_file}",
                "export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION=entry-split-stale",
            ]
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-14")

    assert result["status"] == "fail"
    assert result["runtime_policy_fail_count"] == 1
    assert result["runtime_policy_audits"][0]["reason"] == "stale_policy"
    assert result["findings"][0]["severity"] == "runtime_policy_unusable"


def test_split_runtime_policy_audit_accepts_current_entry_and_scale_in_policies(
    tmp_path,
):
    entry_policy = tmp_path / "entry.json"
    entry_policy.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "entry-current",
                "source_date": "2026-07-13",
                "runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    scale_policy = tmp_path / "scale.json"
    scale_policy.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale-current",
                "generated_at": "2026-07-13T20:28:03+09:00",
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": {
                    "runtime_policy_refresh_allowed": True,
                    "blockers": [],
                },
                "buckets": {"default": {}},
            }
        ),
        encoding="utf-8",
    )
    env = {
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE": "2026-07-14",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE": str(entry_policy),
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION": "entry-current",
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE": "2026-07-14",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": str(scale_policy),
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION": "scale-current",
    }

    audits = mod._split_runtime_policy_audits("2026-07-14", env)

    assert [audit["status"] for audit in audits] == ["pass", "pass"]
    assert [audit["reason"] for audit in audits] == ["policy_usable", "policy_usable"]
    assert audits[0]["operator_fallback_authorized"] is True


def test_split_runtime_policy_audit_accepts_scale_in_policy_across_krx_holiday_weekend(
    tmp_path,
):
    scale_policy = tmp_path / "scale.json"
    scale_policy.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale-holiday-handoff",
                "generated_at": "2026-07-16T20:28:37+09:00",
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": {
                    "runtime_policy_refresh_allowed": True,
                    "blockers": [],
                },
                "buckets": {"default": {}},
            }
        ),
        encoding="utf-8",
    )
    env = {
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": str(scale_policy),
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION": "scale-holiday-handoff",
    }

    audits = mod._split_runtime_policy_audits("2026-07-20", env)

    scale_audit = next(
        item for item in audits if item["family"] == "scale_in_split_order_plan"
    )
    assert scale_audit["status"] == "pass"
    assert scale_audit["reason"] == "policy_usable"
    assert scale_audit["freshness_age_trading_days"] == 1


def test_split_runtime_policy_audit_rejects_entry_authority_union_mismatch(
    tmp_path,
):
    entry_policy = tmp_path / "entry.json"
    entry_policy.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "entry-invalid-authority",
                "source_date": "2026-07-20",
                "runtime_apply_allowed": True,
                "runtime_apply_compatibility_semantics": (
                    "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed"
                ),
                "exploration_seed_allowed": False,
                "ev_validated_runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    env = {
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE": "2026-07-20",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE": str(entry_policy),
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION": "entry-invalid-authority",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "false",
    }

    audits = mod._split_runtime_policy_audits("2026-07-20", env)

    entry_audit = next(
        item for item in audits if item["family"] == "entry_split_order_plan"
    )
    assert entry_audit["status"] == "fail"
    assert entry_audit["reason"] == "runtime_apply_authority_contract_invalid"
    assert entry_audit["runtime_apply_authority_contract"] == {
        "runtime_apply_allowed": True,
        "exploration_seed_allowed": False,
        "ev_validated_runtime_apply_allowed": False,
        "valid": False,
        "reason": "runtime_apply_authority_union_mismatch",
    }


def test_split_runtime_policy_audit_rejects_scale_policy_without_refresh_evidence(
    tmp_path,
):
    scale_policy = tmp_path / "scale.json"
    scale_policy.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale-legacy",
                "generated_at": "2026-07-16T20:28:37+09:00",
                "runtime_apply_allowed": True,
                "buckets": {"default": {}},
            }
        ),
        encoding="utf-8",
    )
    env = {
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": str(scale_policy),
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION": "scale-legacy",
    }

    audits = mod._split_runtime_policy_audits("2026-07-20", env)

    scale_audit = next(
        item for item in audits if item["family"] == "scale_in_split_order_plan"
    )
    assert scale_audit["status"] == "fail"
    assert scale_audit["reason"] == "runtime_refresh_evidence_missing"


def test_split_runtime_policy_audit_rejects_scale_in_policy_after_three_trading_days(
    tmp_path,
):
    scale_policy = tmp_path / "scale.json"
    scale_policy.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale-stale-trading-days",
                "generated_at": "2026-07-13T20:28:37+09:00",
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": {
                    "runtime_policy_refresh_allowed": True,
                    "blockers": [],
                },
                "buckets": {"default": {}},
            }
        ),
        encoding="utf-8",
    )
    env = {
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": str(scale_policy),
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION": "scale-stale-trading-days",
    }

    audits = mod._split_runtime_policy_audits("2026-07-20", env)

    scale_audit = next(
        item for item in audits if item["family"] == "scale_in_split_order_plan"
    )
    assert scale_audit["status"] == "fail"
    assert scale_audit["reason"] == "stale_policy"
    assert scale_audit["freshness_age_trading_days"] == 4


def test_preopen_drops_selected_scale_policy_when_source_file_version_changed(
    tmp_path,
):
    scale_policy = tmp_path / "scale.json"
    scale_policy.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "regenerated-blocked-version",
                "generated_at": "2026-08-05T08:00:00+09:00",
                "runtime_apply_allowed": False,
                "runtime_refresh_evidence": {
                    "runtime_policy_refresh_allowed": False,
                    "blockers": ["real_outcome_refresh_missing"],
                },
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    selected = [{"family": "scale_in_split_order_plan", "stage": "scale_in"}]
    decisions = [
        {
            "family": "scale_in_split_order_plan",
            "selected": True,
            "decision_reason": "deterministic_policy_handoff",
            "env_overrides": {},
        }
    ]
    env = {
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": str(scale_policy),
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION": "report-version-before-regeneration",
        "KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED": "true",
    }

    next_selected, next_decisions, next_env = (
        mod._drop_unusable_selected_split_policies(
            "2026-08-05", selected, decisions, env
        )
    )

    assert next_selected == []
    assert next_decisions[0]["selected"] is False
    assert (
        next_decisions[0]["decision_reason"]
        == "runtime_policy_preflight_failed:policy_version_mismatch"
    )
    assert next_decisions[0]["runtime_policy_preflight"]["policy_version"] == (
        "regenerated-blocked-version"
    )
    assert not any("SCALE_IN_SPLIT_ORDER_POLICY" in key for key in next_env)
    assert next_env["KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED"] == "true"


def test_verify_runtime_env_handoff_rejects_selected_disabled_split_policy(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-14.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-14",
                "selected_families": ["scale_in_split_order_plan"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "false",
                    "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE": "unused.json",
                    "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION": "disabled",
                },
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-14")

    assert result["status"] == "fail"
    assert result["findings"][0]["severity"] == "runtime_policy_unusable"
    assert result["findings"][0]["policy_reason"] == "selected_policy_disabled"


def test_verify_runtime_env_handoff_rejects_market_first_inactive_date(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-14.json").write_text(
        json.dumps(
            {"target_date": "2026-07-14", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED=true",
                "export KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE=2026-07-13",
            ]
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-14")

    assert result["status"] == "fail"
    finding = next(
        item
        for item in result["findings"]
        if item["policy_reason"] == "market_first_inactive_date"
    )
    assert finding["active_date"] == "2026-07-13"


def test_verify_runtime_env_handoff_rejects_probe_first_value_mismatch(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-20.json").write_text(
        json.dumps(
            {"target_date": "2026-07-20", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=true",
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE=2026-07-20",
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY=1",
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_TIMEOUT_SEC=4",
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES=5",
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_SLIPPAGE_BPS=50",
                "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_ANCHOR_MODE=fill_clamped_to_fresh_bbo",
                "export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=false",
            ]
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-20")

    mismatch = next(
        finding
        for finding in result["findings"]
        if finding.get("policy_reason") == "probe_first_value_mismatch"
    )
    assert mismatch["missing_env_keys"] == [
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_TIMEOUT_SEC"
    ]


def test_verify_runtime_env_handoff_rejects_post_probe_resolver_without_probe_first(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-21.json").write_text(
        json.dumps(
            {"target_date": "2026-07-21", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "export KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED=true\n"
        "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=false\n",
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-21")

    finding = next(
        item
        for item in result["findings"]
        if item.get("policy_reason")
        == "post_probe_resolver_probe_first_dependency_disabled"
    )
    assert finding["family"] == "dynamic_entry_price_resolver"


def test_verify_runtime_env_handoff_rejects_recheck_without_probe_dependencies(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-21.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-21",
                "selected_families": ["entry_opportunity_recheck_runtime"],
                "env_overrides": {
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION": "false",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT": "true",
                    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT": "true",
                    "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED": "false",
                    "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY": "2",
                    "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED": "false",
                },
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-21")

    finding = next(
        item
        for item in result["findings"]
        if item.get("policy_reason")
        == "entry_recheck_probe_dependency_contract_invalid"
    )
    assert finding["family"] == "entry_opportunity_recheck_runtime"
    assert "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED" in finding["missing_env_keys"]
    assert "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY" in finding["missing_env_keys"]


def test_entry_split_daily_operator_contract_accepts_recurring_stale_policy(
    tmp_path,
):
    policy_path = tmp_path / "entry_split_policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "entry-split-daily",
                "source_date": "2026-07-01",
                "runtime_apply_allowed": True,
                "baseline_runtime_defaults_enabled": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    audits = mod._split_runtime_policy_audits(
        "2026-08-03",
        {
            "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED": "false",
            "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED": "true",
            "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE": str(policy_path),
            "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_VERSION": (
                "entry-split-daily"
            ),
            "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE": "DAILY",
            "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "false",
        },
    )

    entry_audit = next(
        audit for audit in audits if audit["family"] == "entry_split_order_plan"
    )
    assert entry_audit["status"] == "pass"
    assert entry_audit["reason"] == "policy_usable"
    assert entry_audit["stale_policy_operator_authorized"] is True


def test_entry_split_daily_contract_does_not_authorize_stale_standard_policy(
    tmp_path,
):
    policy_path = tmp_path / "entry_split_policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "entry-split-standard-stale",
                "source_date": "2026-07-01",
                "runtime_apply_allowed": True,
                "baseline_runtime_defaults_enabled": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    audits = mod._split_runtime_policy_audits(
        "2026-08-03",
        {
            "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED": "true",
            "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE": str(policy_path),
            "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION": (
                "entry-split-standard-stale"
            ),
            "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE": "2026-08-03",
            "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED": "true",
            "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED": "false",
        },
    )

    entry_audit = next(
        audit for audit in audits if audit["family"] == "entry_split_order_plan"
    )
    assert entry_audit["status"] == "fail"
    assert entry_audit["reason"] == "stale_policy"
    assert "stale_policy_operator_authorized" not in entry_audit


def test_dated_runtime_override_audits_require_current_date_and_dependency():
    target_date = "2026-07-15"
    env = {
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "false",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ACTIVE_DATE": "",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_PROBABILITY_BAND_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_PROBABILITY_BAND_ACTIVE_DATE": (
            "2026-07-14"
        ),
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ACTIVE_DATE": "2026-07-14",
    }

    audits = mod._dated_runtime_override_audits(target_date, env)
    by_family = {audit["family"]: audit for audit in audits}

    assert by_family["rising_missed_tp1_selector"]["status"] == "disabled"
    assert (
        by_family["rising_missed_tp1_source_gap_relief"]["reason"]
        == "dependency_disabled"
    )
    assert (
        by_family["latency_true_ofi_direct_canary_extended_spread"]["reason"]
        == "active_date_missing"
    )
    assert by_family["rising_missed_nxt_post_block_sampler"]["reason"] == (
        "runtime_inactive_date"
    )
    assert by_family["latency_true_ofi_nxt_probability_band"]["reason"] == (
        "runtime_inactive_date"
    )


def test_dated_runtime_auto_renew_projects_only_enabled_members_to_target_date():
    target_date = "2026-08-03"
    source = {
        mod.DATED_RUNTIME_AUTO_RENEW_ENABLED_KEY: "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-07-31",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED": "false",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE": ("2026-07-31"),
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ACTIVE_DATE": "2026-07-31",
    }

    expected, expected_keys = mod._dated_runtime_auto_renew_expected_env(
        target_date,
        source,
    )

    assert expected == {
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE": target_date,
    }
    assert expected_keys == sorted(expected)
    assert "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED" not in expected
    assert "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED" not in expected


def test_verify_runtime_env_handoff_accepts_explicit_dated_auto_renew_contract(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(
        mod, "authoritative_ai_context_runtime_env", lambda *_args, **_kwargs: {}
    )
    target_date = "2026-08-03"
    (runtime_dir / f"threshold_runtime_env_{target_date}.json").write_text(
        json.dumps(
            {"target_date": target_date, "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                f"export {mod.DATED_RUNTIME_AUTO_RENEW_ENABLED_KEY}=true",
                "export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED=true",
                (
                    "export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE="
                    "2026-07-31"
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff(target_date)

    assert result["status"] == "pass"
    assert result["dated_runtime_auto_renew_enabled"] is True
    assert result["dated_runtime_override_fail_count"] == 0
    selector = next(
        audit
        for audit in result["dated_runtime_override_audits"]
        if audit["family"] == "rising_missed_tp1_selector"
    )
    assert selector["status"] == "pass"
    assert selector["active_date"] == target_date


def test_dated_source_gap_relief_requires_its_own_active_date():
    target_date = "2026-07-31"
    audits = mod._dated_runtime_override_audits(
        target_date,
        {
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": target_date,
            "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED": "true",
        },
    )
    finding = next(
        item
        for item in audits
        if item["family"] == "rising_missed_tp1_source_gap_relief"
    )

    assert finding["status"] == "fail"
    assert finding["reason"] == "active_date_missing"
    assert finding["active_date_key"] == (
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE"
    )


def test_verify_runtime_env_handoff_rejects_stale_dated_operator_runtime(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-15.json").write_text(
        json.dumps(
            {"target_date": "2026-07-15", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ENABLED=true",
                "export KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ACTIVE_DATE=2026-07-14",
            ]
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-15")

    assert result["status"] == "fail"
    assert result["dated_runtime_override_fail_count"] == 1
    finding = next(
        item
        for item in result["findings"]
        if item["family"] == "rising_missed_nxt_post_block_sampler"
    )
    assert finding["policy_reason"] == "runtime_inactive_date"
    assert finding["active_date"] == "2026-07-14"


def test_dated_runtime_override_audits_accept_current_runtime_bundle():
    target_date = "2026-07-15"
    env = {
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_PROBABILITY_BAND_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_PROBABILITY_BAND_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_REST_FALLBACK_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_REST_FALLBACK_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_NXT_PRICE_JUMP_RECOVERY_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_NXT_PRICE_JUMP_RECOVERY_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_PARTIAL_RUNNER_ENABLED": "true",
        "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_PARTIAL_RUNNER_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_NXT_RISING_MISSED_PARTIAL_FILL_REPRICE_ENABLED": "true",
        "KORSTOCKSCAN_NXT_RISING_MISSED_PARTIAL_FILL_REPRICE_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_CONTEXT_REFRESH_ENABLED": "true",
        "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_CONTEXT_REFRESH_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SHALLOW_SOURCE_GAP_RECHECK_ENABLED": "true",
        "KORSTOCKSCAN_SHALLOW_SOURCE_GAP_RECHECK_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_POST_AI_HARD_NEGATIVE_BLOCK_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_POST_AI_HARD_NEGATIVE_BLOCK_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SCALP_TRAILING_LOSS_CONVERSION_RECHECK_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_TRAILING_LOSS_CONVERSION_RECHECK_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_TP1_STRONG_MICRO_SOURCE_GAP_RELIEF_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TP1_STRONG_MICRO_SOURCE_GAP_RELIEF_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_TICK_ABSOLUTE_THROUGHPUT_RELIEF_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_TICK_ABSOLUTE_THROUGHPUT_RELIEF_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ENABLED": "true",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ACTIVE_DATE": target_date,
    }

    audits = mod._dated_runtime_override_audits(target_date, env)

    assert all(audit["status"] == "pass" for audit in audits)
    assert all(audit["reason"] == "active_date_matches_target" for audit in audits)
    assert not any(
        audit["family"] == "latency_true_ofi_direct_canary_recheck" for audit in audits
    )


def test_verify_runtime_env_handoff_requires_scalp_sim_policy_source_date(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["scalp_sim_auto_approval"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE": "data/runtime/scalp_sim_policy_catalog.json",
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_VERSION": "scalp_sim_auto_approval:2026-06-10",
                },
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-06-11")

    assert result["status"] == "fail"
    assert result["passed"] is False
    assert any(
        finding.get("family") == "scalp_sim_auto_approval"
        and "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE"
        in finding.get("missing_env_keys", [])
        for finding in result["findings"]
    )


def test_scalp_sim_policy_audit_uses_lifecycle_when_direct_file_is_missing(
    tmp_path,
):
    catalog_path = tmp_path / "lifecycle_bucket_catalog_2026-08-20.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "lifecycle_bucket_catalog_v1",
                "buckets": [],
            }
        ),
        encoding="utf-8",
    )

    audit = mod._scalp_sim_auto_runtime_policy_audit(
        {
            "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "true",
            "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED": "true",
            "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE": str(catalog_path),
        }
    )

    assert audit["status"] == "pass"
    assert audit["reason"] == "direct_policy_file_missing_lifecycle_handoff"
    assert audit["policy_source"] == "lifecycle_bucket_discovery_catalog_handoff"
    assert audit["lifecycle_handoff_enabled"] is True


def test_scalp_sim_policy_audit_rejects_enabled_policy_without_any_file():
    audit = mod._scalp_sim_auto_runtime_policy_audit(
        {"KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "true"}
    )

    assert audit["status"] == "fail"
    assert audit["reason"] == "enabled_policy_file_missing"
    assert audit["required_env_keys"] == ["KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE"]


def test_scalp_sim_policy_audit_ignores_incomplete_lifecycle_handoff_when_direct_disabled():
    audit = mod._scalp_sim_auto_runtime_policy_audit(
        {
            "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "false",
            "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED": "true",
        },
        operator_overrides={"KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "false"},
    )

    assert audit["status"] == "disabled"
    assert audit["reason"] == "operator_lock_disabled"
    assert audit["direct_requested"] is False
    assert audit["direct_operator_lock_disabled"] is True
    assert audit["lifecycle_requested"] is True
    assert audit["lifecycle_contract_complete"] is False
    assert audit["lifecycle_handoff_enabled"] is False


def test_verify_runtime_env_handoff_allows_selected_scalp_sim_operator_lock_disable(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    policy_path = tmp_path / "scalp_sim_policy_catalog.json"
    (runtime_dir / "threshold_runtime_env_2026-09-01.json").write_text(
        json.dumps(
            {
                "target_date": "2026-09-01",
                "selected_families": ["scalp_sim_auto_approval"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE": str(policy_path),
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_VERSION": (
                        "scalp_sim_auto_approval:2026-08-31"
                    ),
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE": "2026-08-31",
                    "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "export KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=false\n",
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-09-01")

    assert result["status"] == "pass"
    audit = next(
        item
        for item in result["runtime_policy_audits"]
        if item["family"] == "scalp_sim_auto_approval"
    )
    assert audit["status"] == "disabled"
    assert audit["reason"] == "operator_lock_disabled"
    assert audit["direct_operator_lock_disabled"] is True


def test_verify_runtime_env_handoff_rejects_pre_clean_baseline_embedded_plan(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    policy_path = tmp_path / "scalp_sim_policy_catalog.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "hypothesis_observation_plan": {
                    "schema_version": "ldm_hypothesis_observation_plan_v1",
                    "source_report_date": "2026-06-01",
                    "hypotheses": [{"soft_hypothesis_id": "archive_only"}],
                },
            }
        ),
        encoding="utf-8",
    )
    runtime_dir.joinpath("threshold_runtime_env_2026-08-13.json").write_text(
        json.dumps(
            {
                "target_date": "2026-08-13",
                "selected_families": ["scalp_sim_auto_approval"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE": str(policy_path),
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_VERSION": (
                        "scalp_sim_auto_approval:2026-08-12"
                    ),
                    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE": "2026-08-12",
                },
            }
        ),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-08-13")

    assert result["status"] == "fail"
    assert any(
        finding.get("policy_reason")
        == "hypothesis_plan_pre_clean_baseline_archive_only"
        for finding in result["findings"]
    )


def test_build_runtime_gap_provenance_artifact_preserves_raw(tmp_path):
    artifact = mod.build_runtime_gap_provenance_artifact("2026-06-11")
    assert artifact["raw_preserved"] is True
    assert artifact["active_gap_count"] >= 2
    assert any(g["family"] == "score65_74_recovery_probe" for g in artifact["gaps"])
    assert any(
        g["family"] == "lifecycle_bucket_discovery_sim_auto_approval"
        for g in artifact["gaps"]
    )


def test_classify_postclose_interpretation_scope_during_gap():
    result = mod.classify_postclose_interpretation_scope(
        "2026-06-11T09:00:00+09:00",
        target_date="2026-06-11",
    )
    assert result["scope"] == "gap_affected"
    assert len(result["active_gaps"]) >= 1
    assert any(
        "real_probe_attribution_missing" in g["gap_type"] for g in result["active_gaps"]
    )


def test_classify_postclose_interpretation_scope_after_restore():
    result = mod.classify_postclose_interpretation_scope(
        "2026-06-11T11:00:00+09:00",
        target_date="2026-06-11",
    )
    assert result["scope"] == "normal_runtime"
    assert result["active_gaps"] == []


def test_verify_runtime_env_handoff_pid_missing_key(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )

    def _fake_empty_environ(pid):
        return {}

    monkeypatch.setattr(mod, "_read_pid_environ", _fake_empty_environ)

    result = mod.verify_runtime_env_handoff("2026-06-11", pid=12345)
    assert result["status"] == "fail"
    assert result["fail_reason"] == "runtime_env_pid_missing"
    assert len(result["pid_missing"]) == 1
    assert (
        result["pid_missing"][0]["env_key"]
        == "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
    )
    assert result["pid_missing"][0]["severity"] == "runtime_env_pid_missing"


def test_verify_runtime_env_handoff_distinguishes_unreadable_pid_env(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "_read_pid_environ",
        lambda pid: mod._PidEnviron(
            read_error={
                "status": "unreadable",
                "path": f"/proc/{pid}/environ",
                "error_type": "PermissionError",
                "errno": 13,
            }
        ),
    )

    result = mod.verify_runtime_env_handoff("2026-06-11", pid=12345)

    assert result["status"] == "fail"
    assert result["fail_reason"] == "runtime_env_pid_unreadable"
    assert result["pid_passed"] is False
    assert result["pid_missing"] == []
    assert result["pid_mismatches"] == []
    assert result["pid_env_read_error"] == {
        "status": "unreadable",
        "path": "/proc/12345/environ",
        "error_type": "PermissionError",
        "errno": 13,
    }


def test_verify_runtime_env_handoff_pid_uses_operator_runtime_overrides(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["swing_sim_auto_approval"],
                "env_overrides": {
                    "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED": "true",
                    "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE": "/tmp/swing_policy.json",
                    "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_VERSION": "swing_sim_auto_approval:2026-06-10",
                },
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=false",
                "export KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE=",
                "export KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_VERSION=",
            ]
        ),
        encoding="utf-8",
    )

    def _fake_pid_environ(pid):
        return {
            "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED": "false",
            "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE": "",
            "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_VERSION": "",
        }

    monkeypatch.setattr(mod, "_read_pid_environ", _fake_pid_environ)

    result = mod.verify_runtime_env_handoff("2026-06-11", pid=12345)

    assert result["status"] == "pass"
    assert result["pid_mismatches"] == []
    assert result["operator_runtime_override_keys"] == [
        "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED",
        "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE",
        "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_VERSION",
    ]


def test_launcher_pid_expected_env_disables_expired_guard():
    expected, disabled = mod._launcher_pid_expected_env(
        "2026-07-28",
        {
            "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ACTIVE_DATE": "2026-07-24",
        },
    )

    assert expected["KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED"] == "false"
    assert disabled == ["KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED"]


def test_verify_runtime_env_handoff_uses_target_date_operator_overlay(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-21.json").write_text(
        json.dumps(
            {"target_date": "2026-07-21", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ENABLED=true",
                "export KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ACTIVE_DATE=2026-07-20",
            ]
        ),
        encoding="utf-8",
    )
    overlay_path = runtime_dir / "operator_runtime_overrides_2026-07-21.env"
    overlay_path.write_text(
        "export KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ACTIVE_DATE=2026-07-21\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "_read_pid_environ",
        lambda pid: {
            "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ENABLED": "true",
            "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ACTIVE_DATE": "2026-07-21",
        },
    )

    result = mod.verify_runtime_env_handoff("2026-07-21", pid=12345)

    assert result["status"] == "pass"
    assert result["pid_mismatches"] == []
    assert result["dated_operator_runtime_override_path"] == str(overlay_path)
    assert result["dated_operator_runtime_override_keys"] == [
        "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ACTIVE_DATE"
    ]


def test_verify_runtime_env_handoff_committed_context_promotion_owns_pid_values(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    exact_env = {
        "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE": "exact_v2",
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED": "true",
    }
    manifest_path = runtime_dir / "threshold_runtime_env_2026-07-29.json"
    manifest_path.write_text(
        json.dumps(
            {
                "target_date": "2026-07-29",
                "selected_families": [],
                "env_overrides": exact_env,
                "ai_multi_timeframe_context_promotion": str(
                    tmp_path / "promotion.json"
                ),
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides_2026-07-29.env").write_text(
        "export KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE=baseline_v1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "authoritative_ai_context_runtime_env",
        lambda *_args, **_kwargs: dict(exact_env),
    )
    monkeypatch.setattr(
        mod,
        "_read_pid_environ",
        lambda _pid: {
            "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE": "baseline_v1",
            "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED": "true",
        },
    )

    result = mod.verify_runtime_env_handoff("2026-07-29", pid=12345)

    assert result["status"] == "fail"
    assert result["pid_mismatches"] == [
        {
            "family": "ai_multi_timeframe_context_promotion",
            "env_key": "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE",
            "manifest_value": "exact_v2",
            "pid_value": "baseline_v1",
            "expected_value_source": "ai_multi_timeframe_context_promotion",
        }
    ]
    assert result["authoritative_ai_context_runtime_env_keys"] == sorted(exact_env)


def test_verify_runtime_env_handoff_uses_catalog_context_without_manifest_pointer(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    exact_env = {
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE": "2026-07-31",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED": "true",
    }
    (runtime_dir / "threshold_runtime_env_2026-07-31.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-31",
                "selected_families": ["holding_decision_context_v1"],
                "env_overrides": {
                    "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE": ("2026-07-24"),
                    "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "authoritative_ai_context_runtime_env",
        lambda *_args, **_kwargs: dict(exact_env),
    )
    monkeypatch.setattr(mod, "_read_pid_environ", lambda _pid: dict(exact_env))

    result = mod.verify_runtime_env_handoff("2026-07-31", pid=12345)

    assert result["pid_mismatches"] == []
    assert result["authoritative_ai_context_runtime_env_keys"] == sorted(exact_env)


def test_verify_runtime_env_handoff_validates_holding_and_persistent_overlays(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(
        mod, "authoritative_ai_context_runtime_env", lambda *_args, **_kwargs: {}
    )
    holding_env = {
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE": "2026-07-23",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_KRX_ENABLED": "false",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_NXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_PREMARKET_ENABLED": "false",
        "KORSTOCKSCAN_HOLDING_SCORE_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_FLOW_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_OVERNIGHT_CONTEXT_ENABLED": "false",
    }
    persistent_env = {
        "KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE": "22",
        "KORSTOCKSCAN_SCALP_SIM_AI_MAX_CALLS_PER_MIN": "4",
    }
    manifest_env = {**holding_env, **persistent_env}
    (runtime_dir / "threshold_runtime_env_2026-07-28.json").write_text(
        json.dumps(
            {
                "target_date": "2026-07-28",
                "selected_families": [
                    "holding_decision_context_v1",
                    "persistent_operator_overrides_2026_06_26",
                ],
                "env_overrides": manifest_env,
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "".join(f"export {key}={value}\n" for key, value in persistent_env.items()),
        encoding="utf-8",
    )

    result = mod.verify_runtime_env_handoff("2026-07-28")

    assert result["status"] == "pass"
    assert result["unverified_selected_family_count"] == 0
    audits = {audit["family"]: audit for audit in result["runtime_policy_audits"]}
    assert audits["holding_decision_context_v1"]["status"] == "pass"
    assert (
        audits["holding_decision_context_v1"]["reason"]
        == "activation_start_date_valid_atomic_promotion_required"
    )
    assert audits["holding_decision_context_v1"]["requested_cohorts"] == ["NXT"]
    assert audits["holding_decision_context_v1"][
        "effective_cohorts_without_atomic_promotion"
    ] == ["NXT"]
    assert (
        audits["persistent_operator_overrides_2026_06_26"][
            "operator_override_key_count"
        ]
        == 2
    )
    assert audits["persistent_operator_overrides_2026_06_26"]["status"] == "pass"


def test_verify_runtime_env_handoff_rolls_probe_first_into_target_date_overlay(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    policy_path = tmp_path / "entry-split-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "entry-split-rollover-test",
                "source_date": "2026-07-20",
                "runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "threshold_runtime_env_2026-07-21.json").write_text(
        json.dumps(
            {"target_date": "2026-07-21", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    persistent_env = {
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE": str(policy_path),
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION": "entry-split-rollover-test",
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE": "2026-07-20",
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE": "2026-07-20",
        "KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED": "false",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE": "2026-07-20",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY": "1",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_TIMEOUT_SEC": "3",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES": "5",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_SLIPPAGE_BPS": "50",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_ANCHOR_MODE": "fill_clamped_to_fresh_bbo",
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED": "true",
    }
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "".join(f"export {key}={value}\n" for key, value in persistent_env.items()),
        encoding="utf-8",
    )
    dated_env = {
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE": "2026-07-21",
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE": "2026-07-21",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE": "2026-07-21",
    }
    (runtime_dir / "operator_runtime_overrides_2026-07-21.env").write_text(
        "".join(f"export {key}={value}\n" for key, value in dated_env.items()),
        encoding="utf-8",
    )
    effective_pid_env = dict(persistent_env)
    effective_pid_env.update(dated_env)
    monkeypatch.setattr(mod, "_read_pid_environ", lambda pid: effective_pid_env)

    result = mod.verify_runtime_env_handoff("2026-07-21", pid=12345)

    assert result["status"] == "pass"
    assert result["pid_passed"] is True
    assert result["pid_missing"] == []
    assert result["pid_mismatches"] == []
    entry_audit = next(
        audit
        for audit in result["runtime_policy_audits"]
        if audit["family"] == "entry_split_order_plan"
    )
    assert entry_audit["status"] == "pass"
    assert entry_audit["active_date"] == "2026-07-21"
    assert entry_audit["operator_fallback_active_date"] == "2026-07-21"


def test_verify_runtime_env_handoff_pid_rejects_stale_dated_override(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    (runtime_dir / "threshold_runtime_env_2026-07-15.json").write_text(
        json.dumps(
            {"target_date": "2026-07-15", "selected_families": [], "env_overrides": {}}
        ),
        encoding="utf-8",
    )
    (runtime_dir / "operator_runtime_overrides.env").write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ENABLED=true",
                "export KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ACTIVE_DATE=2026-07-15",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        mod,
        "_read_pid_environ",
        lambda pid: {
            "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ACTIVE_DATE": "2026-07-14",
        },
    )

    result = mod.verify_runtime_env_handoff("2026-07-15", pid=12345)

    assert result["passed"] is True
    assert result["pid_passed"] is False
    assert result["status"] == "fail"
    assert result["fail_reason"] == "runtime_env_pid_mismatch"
    assert result["pid_mismatches"] == [
        {
            "family": "rising_missed_nxt_post_block_sampler",
            "env_key": "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ACTIVE_DATE",
            "manifest_value": "2026-07-15",
            "pid_value": "2026-07-14",
            "expected_value_source": "operator_runtime_overrides",
        }
    ]


def test_verify_runtime_env_handoff_lifecycle_bucket_missing_live_auto_apply(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    manifest = runtime_dir / "threshold_runtime_env_2026-06-11.json"
    manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-11",
                "selected_families": ["lifecycle_bucket_discovery_sim_auto_approval"],
                "env_overrides": {
                    "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED": "true",
                    "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE": "/some/path.json",
                    "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION": "v1",
                },
            }
        ),
        encoding="utf-8",
    )
    result = mod.verify_runtime_env_handoff("2026-06-11")
    assert result["status"] == "fail"
    assert result["fail_reason"] == "runtime_env_handoff_missing"
    assert result["missing_family_count"] == 1
    assert any(
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED"
        in finding.get("missing_env_keys", [])
        for finding in result["findings"]
    )


def test_gap_provenance_empty_for_wrong_target_date(tmp_path):
    artifact = mod.build_runtime_gap_provenance_artifact("2026-06-12")
    assert artifact["active_gap_count"] == 0
    assert artifact["gaps"] == []


def test_classify_postclose_interpretation_scope_empty_for_wrong_target_date():
    result = mod.classify_postclose_interpretation_scope(
        "2026-06-11T09:00:00+09:00",
        target_date="2026-06-12",
    )
    assert result["scope"] == "normal_runtime"
    assert result["active_gaps"] == []


def test_hold_carry_forward_blocked_by_direct_severe_loss_guard(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-10.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-10",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "severe_loss_guard": True,
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert "hold_carry_forward_blocked" in decision["decision_reason"]
    assert "severe_loss_guard" in decision["decision_reason"]


def test_hold_carry_forward_blocked_by_direct_provenance_breach(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    prev_manifest = runtime_dir / "threshold_runtime_env_2026-06-10.json"
    prev_manifest.write_text(
        json.dumps(
            {
                "target_date": "2026-06-10",
                "selected_families": ["soft_stop_whipsaw_confirmation"],
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "hold",
                        "order_provenance_breach": True,
                        "target_env_keys": [],
                        "recommended_values": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert "hold_carry_forward_blocked" in decision["decision_reason"]
    assert "order_provenance_breach" in decision["decision_reason"]


def test_gap_provenance_written_during_auto_apply(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    gap_dir = tmp_path / "runtime_gap_provenance"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    report_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "RUNTIME_GAP_PROVENANCE_DIR", gap_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)
    (report_dir / "threshold_cycle_calibration_2026-06-10_postclose.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 5,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"
                        ],
                        "recommended_values": {"enabled": True},
                        "current_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    mod.build_preopen_apply_manifest(
        "2026-06-11",
        source_date="2026-06-10",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    gap_path = mod.runtime_gap_provenance_artifact_path("2026-06-11")
    assert gap_path.exists()
    gap_artifact = json.loads(gap_path.read_text(encoding="utf-8"))
    assert gap_artifact["raw_preserved"] is True
    assert gap_artifact["active_gap_count"] == 2


def test_main_fails_when_runtime_change_handoff_verification_fails(monkeypatch):
    monkeypatch.setattr(
        mod,
        "build_preopen_apply_manifest",
        lambda *args, **kwargs: {
            "target_date": "2026-07-22",
            "status": "auto_bounded_live_ready",
            "runtime_change": True,
            "runtime_env_handoff_verification": {"status": "fail"},
        },
    )

    assert mod.main(["--target-date", "2026-07-22", "--auto-apply"]) == 2


def test_main_accepts_runtime_change_only_after_handoff_verification_passes(
    monkeypatch,
):
    monkeypatch.setattr(
        mod,
        "build_preopen_apply_manifest",
        lambda *args, **kwargs: {
            "target_date": "2026-07-22",
            "status": "auto_bounded_live_ready",
            "runtime_change": True,
            "runtime_env_handoff_verification": {"status": "pass"},
        },
    )

    assert mod.main(["--target-date", "2026-07-22", "--auto-apply"]) == 0
