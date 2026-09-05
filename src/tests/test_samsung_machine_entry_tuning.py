from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.engine.monitoring.samsung_machine_entry_tuning import (
    CLEAN_WINDOW_NAME,
    POST_APPLY_WINDOW_NAME,
    REPORT_SCHEMA,
    REPORT_TYPE,
    _aggregate_rows,
    _attach_policy_cohort,
    _axis_observations,
    _normalize_historical_machine_row,
    build_policy_candidate,
    build_report,
    extract_machine_row,
    write_policy_candidate,
    write_report,
)
from src.trading.order.samsung_entry_policy import (
    BASELINE_POLICIES,
    OPERATOR_OVERRIDE_RUNTIME_SOURCE,
    atomic_write_json,
    baseline_applied_payload,
    candidate_artifact_hash,
    load_applied_machine_policy,
    policy_hash,
    policy_mutations_between,
    report_artifact_hash,
)


def _features(machine: str) -> dict:
    if machine == "morning":
        return {
            "schema": "samsung_morning_entry_signal_features_v1",
            "strategy": "morning",
            "source": "kiwoom_005930_sor_opening_price",
            "route": "SOR",
            "routes": ["SOR"],
            "signal_bar": "2026-08-11T09:00:00+09:00",
            "opening_price": 70500,
            "opening_prices": {"SOR": 70500},
            "required_drawdown_pct": 0.75,
            "required_drawdown_pct_by_route": {"SOR": 0.75},
            "entry_window_start": "09:00:00",
            "entry_window_deadline": "09:30:00",
            "entry_windows": {"SOR": {"start": "09:00:00", "deadline": "09:30:00"}},
            "target_ticks": 2,
            "runtime_policy_source": "preopen_applied_policy",
            "runtime_policy_hash": "a" * 64,
            "entry_legs": [
                {
                    "leg_id": "base_plus_1tick",
                    "price_role": "aggressive_50pct",
                    "entry_price": 70000,
                    "route": "SOR",
                },
                {
                    "leg_id": "base",
                    "price_role": "conservative_50pct",
                    "entry_price": 69900,
                    "route": "SOR",
                },
            ],
        }
    return {
        "schema": "samsung_regular_entry_signal_features_v1",
        "strategy": machine,
        "source": "kiwoom_ka10080_005930_AL_completed_1m",
        "signal_bar": "2026-08-11T14:00:00+09:00",
        "signal_close": 70000,
        "rolling_high": 71200,
        "rolling_low": 69950,
        "observed_drawdown_pct": 1.6,
        "observed_near_low_pct": 0.08,
        "required_drawdown_pct": 1.25,
        "lookback_bars": 30,
        "max_near_low_pct": 0.20,
        "entry_valid_completed_bars": 5,
        "scan_start": "14:00:00",
        "scan_last_bar": "14:40:00",
        "target_ticks": 2,
        "runtime_policy_source": "preopen_applied_policy",
        "runtime_policy_hash": "b" * 64,
        "entry_legs": [
            {
                "leg_id": "signal_close",
                "price_role": "aggressive_50pct",
                "entry_price": 70000,
            },
            {
                "leg_id": "signal_close_minus_1tick",
                "price_role": "conservative_50pct",
                "entry_price": 69900,
            },
        ],
        "unexpected_order_no": "SECRET-FEATURE-ORDER",
    }


def _state(machine: str, trade_date: str, *, held: bool = False) -> dict:
    features = _features(machine)
    features["signal_bar"] = str(features["signal_bar"]).replace(
        "2026-08-11", trade_date
    )
    schema = f"samsung_{machine}_two_leg_state_v2"
    complete_leg = {
        "leg_id": "base_plus_1tick" if machine == "morning" else "signal_close",
        "price_role": "aggressive_50pct",
        "route": "SOR",
        "quantity": 1,
        "entry_price": 70000,
        "status": "HELD" if held else "COMPLETE",
        "buy_order_no": "SECRET-BUY-1",
        "fill_price": 70000,
        "position_qty": 1 if held else 0,
        "target_order_no": "SECRET-SELL-1",
        "target_price": 70200,
        "target_filled_qty": 0 if held else 1,
        "target_filled_at": None if held else f"{trade_date}T15:00:00+09:00",
    }
    no_fill_leg = {
        "leg_id": "base" if machine == "morning" else "signal_close_minus_1tick",
        "price_role": "conservative_50pct",
        "route": "SOR",
        "quantity": 1,
        "entry_price": 69900,
        "status": "NO_FILL",
        "buy_order_no": "SECRET-BUY-2",
        "fill_price": 0,
        "position_qty": 0,
        "target_order_no": "",
        "target_price": 0,
        "target_filled_qty": 0,
    }
    return {
        "schema": schema,
        "trade_date": trade_date,
        "status": "HELD" if held else "COMPLETE",
        "attempt_consumed": True,
        "signal_features": features,
        "legs": [complete_leg, no_fill_leg],
        "owned_order_nos": ["SECRET-BUY-1", "SECRET-BUY-2", "SECRET-SELL-1"],
        "audit": [{"order_no": "SECRET-AUDIT"}],
    }


def _write_states(state_dir: Path, trade_date: str, *, held_machine: str = "") -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    for machine in ("morning", "midday", "afternoon"):
        path = state_dir / f"samsung_{machine}_one_share_state.json"
        path.write_text(
            json.dumps(_state(machine, trade_date, held=machine == held_machine)),
            encoding="utf-8",
        )


def _write_source_quality(source_quality_dir: Path, trade_date: str) -> None:
    source_quality_dir.mkdir(parents=True, exist_ok=True)
    (
        source_quality_dir / f"observation_source_quality_audit_{trade_date}.json"
    ).write_text(
        json.dumps(
            {
                "report_type": "observation_source_quality_audit",
                "target_date": trade_date,
                "status": "pass",
                "summary": {"tuning_input_allowed": True},
            }
        ),
        encoding="utf-8",
    )


def test_extracts_actual_two_leg_outcome_without_broker_identifiers(tmp_path: Path):
    state_path = tmp_path / "state.json"
    payload = _state("midday", "2026-08-11")
    payload["signal_features"].update(
        {
            "signal_decision_at": "2026-08-11T14:00:01+09:00",
            "source_entry_event_id": "samsung_midday_two_leg:005930:signal-1",
            "entry_confirmation_delay_sec": 3,
            "entry_timing_policy_provenance": {
                "status": "applied",
                "policy_hash": "c" * 64,
            },
        }
    )
    payload["legs"][0].update(
        {
            "buy_filled_at": "2026-08-11T14:00:04+09:00",
            "target_filled_at": "2026-08-11T14:01:00+09:00",
        }
    )
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    row = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-11",
        cost_pct=0.20,
    )

    assert row["source_quality"] == "pass"
    assert row["summary"]["completed_signal_episode"] is True
    assert row["summary"]["completed_legs"] == 1
    serialized = json.dumps(row)
    assert "SECRET" not in serialized
    assert row["legs"][0]["equal_weight_profit_pct"] == pytest.approx(0.085714)
    assert row["legs"][0]["buy_filled_at"] == "2026-08-11T14:00:04+09:00"
    assert row["legs"][0]["target_filled_at"] == "2026-08-11T14:01:00+09:00"
    assert row["legs"][0]["holding_duration_sec"] == 56
    assert _aggregate_rows([row])["avg_realized_holding_minutes"] == pytest.approx(
        0.933
    )
    assert row["signal_features"]["signal_decision_at"] == ("2026-08-11T14:00:01+09:00")
    assert row["signal_features"]["source_entry_event_id"] == (
        "samsung_midday_two_leg:005930:signal-1"
    )
    assert row["signal_features"]["entry_confirmation_delay_sec"] == 3


def test_ten_share_partial_fill_uses_filled_quantity_for_notional_ev(
    tmp_path: Path,
):
    payload = _state("midday", "2026-08-13")
    payload["legs"][0].update(
        {
            "quantity": 10,
            "buy_filled_qty": 4,
            "target_filled_qty": 4,
            "target_fill_price": 70_200,
        }
    )
    payload["legs"][1]["quantity"] = 10
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    row = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-13",
        cost_pct=0.20,
    )
    summary = _aggregate_rows([row])
    completed_profit_pct = (70_200 / 70_000 - 1.0) * 100.0 - 0.20
    expected_ev = 70_000 * 4 * completed_profit_pct / (70_000 * 10 + 69_900 * 10)

    assert row["source_quality"] == "pass"
    assert summary["notional_weighted_ev_pct"] == round(completed_profit_pct, 6)
    assert summary["attempted_notional_return_pct_diagnostic"] == round(expected_ev, 6)

    payload["legs"][1]["quantity"] = 1
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    mixed_row = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-13",
        cost_pct=0.20,
    )
    assert mixed_row["source_quality"] == "gap"
    assert (
        "attempted_episode_two_leg_quantity_contract_invalid"
        in mixed_row["source_quality_reasons"]
    )


def test_exact_date_applied_policy_provenance_and_broker_sell_price(tmp_path: Path):
    applied_dir = tmp_path / "applied"
    applied = baseline_applied_payload(
        target_date=date.fromisoformat("2026-08-14"), reason="test_baseline"
    )
    atomic_write_json(
        applied_dir / "samsung_machine_entry_policy_2026-08-14.json", applied
    )
    _, effective_hash, effective_reason = load_applied_machine_policy(
        "midday", target_date=date(2026, 8, 14), applied_dir=applied_dir
    )
    assert effective_reason == "ready_operator_override"
    payload = _state("midday", "2026-08-14")
    payload["signal_features"].update(
        {
            "signal_bar": "2026-08-14T13:15:00+09:00",
            "target_ticks": 3,
            "runtime_policy_source": OPERATOR_OVERRIDE_RUNTIME_SOURCE,
            "runtime_policy_hash": effective_hash,
        }
    )
    payload["legs"][0].update(
        {"quantity": 10, "buy_filled_qty": 10, "target_filled_qty": 10}
    )
    payload["legs"][1]["quantity"] = 10
    payload["legs"][0]["target_fill_price"] = 70_300
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    row = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )

    assert row["source_quality"] == "pass"
    assert row["legs"][0]["profit_price_source"] == "broker_target_fill_price"
    assert row["legs"][0]["equal_weight_profit_pct"] == pytest.approx(0.228571)
    payload["signal_features"]["runtime_policy_hash"] = "0" * 64
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    mismatched = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert (
        "signal_feature_exact_date_applied_policy_mismatch"
        in mismatched["source_quality_reasons"]
    )
    payload["signal_features"]["runtime_policy_hash"] = effective_hash
    payload["legs"][0]["quantity"] = 1
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    quantity_mismatch = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert (
        "exact_date_applied_quantity_mismatch"
        in quantity_mismatch["source_quality_reasons"]
    )
    payload["legs"][0]["quantity"] = 10
    payload["signal_features"]["signal_bar"] = "2026-08-13T13:15:00+09:00"
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    wrong_signal_date = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert (
        "signal_feature_policy_timestamp_invalid"
        in wrong_signal_date["source_quality_reasons"]
    )


def test_axis_observation_does_not_mix_target_quantity_or_runtime_hash_cohorts(
    tmp_path: Path,
):
    applied_dir = tmp_path / "applied"
    applied = baseline_applied_payload(
        target_date=date(2026, 8, 14), reason="test_baseline"
    )
    atomic_write_json(
        applied_dir / "samsung_machine_entry_policy_2026-08-14.json", applied
    )
    _, effective_hash, _ = load_applied_machine_policy(
        "midday", target_date=date(2026, 8, 14), applied_dir=applied_dir
    )

    old_state_path = tmp_path / "old.json"
    old_state_path.write_text(
        json.dumps(_state("midday", "2026-08-13")), encoding="utf-8"
    )
    old_row = _attach_policy_cohort(
        extract_machine_row(
            machine="midday",
            state_path=old_state_path,
            target_date="2026-08-13",
            cost_pct=0.20,
            applied_dir=applied_dir,
        ),
        "midday",
        applied_dir,
    )

    new_state = _state("midday", "2026-08-14")
    new_state["signal_features"].update(
        {
            "target_ticks": 3,
            "runtime_policy_source": OPERATOR_OVERRIDE_RUNTIME_SOURCE,
            "runtime_policy_hash": effective_hash,
        }
    )
    for leg in new_state["legs"]:
        leg["quantity"] = 10
    new_state_path = tmp_path / "new.json"
    new_state_path.write_text(json.dumps(new_state), encoding="utf-8")
    new_row = _attach_policy_cohort(
        extract_machine_row(
            machine="midday",
            state_path=new_state_path,
            target_date="2026-08-14",
            cost_pct=0.20,
            applied_dir=applied_dir,
        ),
        "midday",
        applied_dir,
    )

    assert old_row["policy_cohort"]["target_ticks"] == 2
    assert old_row["policy_cohort"]["leg_quantity_each"] == 1
    assert new_row["policy_cohort"]["target_ticks"] == 3
    assert new_row["policy_cohort"]["leg_quantity_each"] == 10
    assert old_row["policy_cohort_id"] != new_row["policy_cohort_id"]
    observations = _axis_observations([old_row, new_row], "midday")
    assert observations
    assert {item["policy_cohort_id"] for item in observations} == {
        new_row["policy_cohort_id"]
    }
    assert {item["outcome"]["signal_attempts"] for item in observations} == {1}


def test_samsung_manual_stop_loss_is_retained_as_negative_realized_ev():
    from src.engine.monitoring.samsung_machine_entry_tuning import (
        _sanitize_leg,
        _summarize_legs,
    )

    manual_leg = _sanitize_leg(
        {
            "leg_id": "signal_close",
            "quantity": 10,
            "status": "COMPLETE",
            "entry_price": 100_000,
            "fill_price": 100_000,
            "target_price": 100_500,
            "position_qty": 0,
            "buy_filled_qty": 10,
            "target_filled_qty": 10,
            "target_fill_price": 98_000,
            "exit_fill_source": "broker_verified_manual_sell_receipt",
        },
        0.23,
    )
    no_fill_leg = _sanitize_leg(
        {
            "leg_id": "signal_close_minus_1tick",
            "quantity": 10,
            "status": "NO_FILL",
            "entry_price": 99_900,
            "fill_price": 0,
            "target_price": 0,
            "position_qty": 0,
            "buy_filled_qty": 0,
            "target_filled_qty": 0,
            "target_fill_price": 0,
        },
        0.23,
    )
    legs = [manual_leg, no_fill_leg]
    row = {
        "eligible_for_cumulative_tuning": True,
        "attempted": True,
        "cohort": "two_leg_runtime",
        "source_quality": "pass",
        "legs": legs,
        "summary": _summarize_legs(True, legs),
    }

    summary = _aggregate_rows([row])

    assert manual_leg["exit_execution_class"] == "manual_operator_exit"
    assert manual_leg["manual_exit_realized"] is True
    assert manual_leg["autonomous_target_filled"] is False
    assert manual_leg["realized_loss"] is True
    assert manual_leg["equal_weight_profit_pct"] < 0
    assert row["summary"]["manual_exit_completed_legs"] == 1
    assert row["summary"]["manual_exit_loss_legs"] == 1
    assert row["summary"]["machine_target_completed_legs"] == 0
    assert summary["manual_exit_completed_legs"] == 1
    assert summary["manual_exit_loss_legs"] == 1
    assert summary["machine_target_completed_legs"] == 0
    assert summary["manual_exit_fixed_cost_estimate_net_profit_krw"] < 0
    assert summary["notional_weighted_ev_pct"] < 0


def test_pre_override_morning_signal_keeps_exact_date_base_policy(tmp_path: Path):
    applied_dir = tmp_path / "applied"
    applied = baseline_applied_payload(
        target_date=date(2026, 8, 14), reason="test_baseline"
    )
    atomic_write_json(
        applied_dir / "samsung_machine_entry_policy_2026-08-14.json", applied
    )
    payload = _state("morning", "2026-08-14")
    payload["signal_features"].update(
        {
            "signal_bar": "2026-08-14T09:00:00+09:00",
            "target_ticks": 2,
            "runtime_policy_source": "preopen_applied_policy",
            "runtime_policy_hash": applied["policy_hash"],
        }
    )
    payload["legs"][0]["quantity"] = 10
    payload["legs"][1]["quantity"] = 10
    state_path = tmp_path / "morning_state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    row = extract_machine_row(
        machine="morning",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )

    assert row["source_quality"] == "pass"


def test_extracts_morning_reentry_as_fixed_observation_cohort(tmp_path: Path):
    state = {
        "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
        "trade_date": "2026-08-13",
        "status": "COMPLETE",
        "attempt_consumed": True,
        "signal_features": {
            "schema": "samsung_morning_sor_reentry_signal_features_v1",
            "strategy": "morning_sor_reentry",
            "source": "kiwoom_ka10080_005930_AL_completed_1m",
            "signal_bar": "2026-08-13T09:17:00+09:00",
            "signal_close": 100300,
            "rolling_high": 101000,
            "rolling_low": 100000,
            "observed_drawdown_pct": 0.792079,
            "observed_near_low_pct": 0.2,
            "required_drawdown_pct": 0.75,
            "lookback_bars": 15,
            "max_near_low_pct": 0.35,
            "entry_valid_completed_bars": 3,
            "scan_start": "09:00:00",
            "scan_last_bar": "10:00:00",
            "target_ticks": 2,
            "runtime_policy_source": "user_approved_sor_reentry_2026-08-12",
            "runtime_policy_hash": (
                "6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a"
            ),
            "family": "low_hold_reclaim_passive_split",
            "confirmation_bars": 2,
            "reclaim_ticks": 1,
            "entry_offset_ticks": 1,
            "prerequisite": {
                "first_episode_status": "COMPLETE",
                "first_episode_completed_at": "2026-08-13T09:00:00+09:00",
                "required_completed_leg_count": 2,
            },
            "entry_legs": [
                {
                    "leg_id": "confirmation_close_minus_1tick",
                    "price_role": "aggressive_50pct",
                    "entry_price": 100200,
                },
                {
                    "leg_id": "confirmation_close_minus_2ticks",
                    "price_role": "conservative_50pct",
                    "entry_price": 100100,
                },
            ],
        },
        "legs": [
            {
                "leg_id": "confirmation_close_minus_1tick",
                "price_role": "aggressive_50pct",
                "quantity": 1,
                "entry_price": 100200,
                "status": "COMPLETE",
                "buy_order_no": "SECRET-BUY-1",
                "fill_price": 100200,
                "position_qty": 0,
                "target_order_no": "SECRET-TARGET-1",
                "target_price": 100400,
                "target_filled_qty": 1,
            },
            {
                "leg_id": "confirmation_close_minus_2ticks",
                "price_role": "conservative_50pct",
                "quantity": 1,
                "entry_price": 100100,
                "status": "NO_FILL",
                "buy_order_no": "SECRET-BUY-2",
                "fill_price": 0,
                "position_qty": 0,
                "target_order_no": "",
                "target_price": 0,
                "target_filled_qty": 0,
            },
        ],
    }
    state_path = tmp_path / "reentry.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    row = extract_machine_row(
        machine="morning_reentry",
        state_path=state_path,
        target_date="2026-08-13",
        cost_pct=0.20,
    )

    assert row["source_quality"] == "pass"
    assert row["summary"]["completed_signal_episode"] is True
    assert row["summary"]["completed_legs"] == 1
    assert "SECRET" not in json.dumps(row)

    applied_dir = tmp_path / "applied"
    applied = baseline_applied_payload(
        target_date=date(2026, 8, 14), reason="test_baseline"
    )
    atomic_write_json(
        applied_dir / "samsung_machine_entry_policy_2026-08-14.json", applied
    )
    state["trade_date"] = "2026-08-14"
    state["signal_features"]["signal_bar"] = "2026-08-14T09:17:00+09:00"
    state["signal_features"]["prerequisite"][
        "first_episode_completed_at"
    ] = "2026-08-14T09:00:00+09:00"
    for leg in state["legs"]:
        leg["quantity"] = 10
    state["legs"][0]["target_filled_qty"] = 10
    state["legs"][0]["target_fill_price"] = 100400
    state_path.write_text(json.dumps(state), encoding="utf-8")

    pre_override = extract_machine_row(
        machine="morning_reentry",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert pre_override["source_quality"] == "pass"

    _, effective_hash, effective_reason = load_applied_machine_policy(
        "morning", target_date=date(2026, 8, 14), applied_dir=applied_dir
    )
    assert effective_reason == "ready_operator_override"
    state["signal_features"].update(
        {
            "signal_bar": "2026-08-14T09:22:00+09:00",
            "target_ticks": 3,
            "runtime_policy_source": OPERATOR_OVERRIDE_RUNTIME_SOURCE,
            "runtime_policy_hash": effective_hash,
        }
    )
    state["legs"][0]["target_price"] = 100500
    state["legs"][0]["target_fill_price"] = 100500
    state_path.write_text(json.dumps(state), encoding="utf-8")

    post_override = extract_machine_row(
        machine="morning_reentry",
        state_path=state_path,
        target_date="2026-08-14",
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert post_override["source_quality"] == "pass"


def test_morning_reentry_unmet_prerequisite_is_valid_no_op_observation(
    tmp_path: Path,
):
    state_path = tmp_path / "reentry.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "blocked_reason": "first_episode_both_legs_not_complete",
                "legs": [],
            }
        ),
        encoding="utf-8",
    )

    row = extract_machine_row(
        machine="morning_reentry",
        state_path=state_path,
        target_date="2026-08-13",
        cost_pct=0.20,
    )

    assert row["cohort"] == "prerequisite_not_met"
    assert row["source_quality"] == "pass"
    assert row["source_quality_reasons"] == []
    assert row["eligible_for_cumulative_tuning"] is True
    assert row["no_signal"] is False
    assert row["prerequisite_met"] is False
    assert row["blocked_reason"] == "first_episode_both_legs_not_complete"


def test_legacy_and_date_mismatch_are_excluded(tmp_path: Path):
    legacy = tmp_path / "legacy.json"
    legacy.write_text(
        json.dumps(
            {
                "schema": "samsung_afternoon_one_share_state_v1",
                "trade_date": "2026-08-11",
                "attempt_consumed": True,
                "status": "NO_TRADE",
            }
        ),
        encoding="utf-8",
    )
    row = extract_machine_row(
        machine="afternoon",
        state_path=legacy,
        target_date="2026-08-11",
        cost_pct=0.20,
    )
    assert row["cohort"] == "legacy_one_leg_archive_only"
    assert row["eligible_for_cumulative_tuning"] is False

    mismatch = tmp_path / "mismatch.json"
    mismatch.write_text(json.dumps(_state("midday", "2026-08-10")), encoding="utf-8")
    row = extract_machine_row(
        machine="midday",
        state_path=mismatch,
        target_date="2026-08-11",
        cost_pct=0.20,
    )
    assert row["source_quality_reasons"] == ["state_trade_date_mismatch"]


def test_missing_signal_features_is_source_gap(tmp_path: Path):
    payload = _state("midday", "2026-08-11")
    payload.pop("signal_features")
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    row = extract_machine_row(
        machine="midday",
        state_path=state_path,
        target_date="2026-08-11",
        cost_pct=0.20,
    )

    assert row["source_quality"] == "gap"
    assert (
        "attempted_episode_signal_features_missing_or_invalid"
        in row["source_quality_reasons"]
    )


def test_historical_held_row_is_removed_from_decision_ev() -> None:
    old_row = {
        "attempted": True,
        "eligible_for_cumulative_tuning": True,
        "source_quality": "pass",
        "legs": [
            {"status": "COMPLETE", "completed": True, "target_fill_price": 70_200},
            {"status": "HELD", "completed": False, "held": True},
        ],
    }

    normalized = _normalize_historical_machine_row(old_row)

    assert normalized["source_quality"] == "pass"
    assert normalized["eligible_for_cumulative_tuning"] is False
    assert normalized["outcome_complete_for_ev"] is False
    assert normalized["outcome_exclusion_reasons"] == ["held_or_unresolved_inventory"]


def test_sample_floor_remains_eight_but_state_reports_observation_rate() -> None:
    no_signal_row = {
        "eligible_for_cumulative_tuning": True,
        "attempted": False,
        "no_signal": True,
        "cohort": "two_leg_runtime",
        "source_quality": "pass",
        "legs": [],
        "summary": {
            "attempted_legs": 0,
            "submitted_legs": 0,
            "filled_legs": 0,
            "completed_legs": 0,
            "held_legs": 0,
            "unresolved_legs": 0,
            "completed_signal_episode": False,
        },
    }
    completed = _state("midday", "2026-08-11")
    completed_path_row = {
        **no_signal_row,
        "attempted": True,
        "no_signal": False,
        "legs": [
            {
                "entry_price": 70_000,
                "quantity": 1,
                "fill_price": 70_000,
                "buy_filled_qty": 1,
                "equal_weight_profit_pct": 0.1,
                "profit_price_source": "broker_target_fill_price",
            }
        ],
        "summary": {
            "attempted_legs": 2,
            "submitted_legs": 1,
            "filled_legs": 1,
            "completed_legs": 1,
            "held_legs": 0,
            "unresolved_legs": 0,
            "completed_signal_episode": True,
        },
    }
    assert completed["attempt_consumed"] is True

    zero_rate = _aggregate_rows([dict(no_signal_row) for _ in range(5)])
    low_rate = _aggregate_rows(
        [completed_path_row, *[dict(no_signal_row) for _ in range(9)]]
    )

    assert zero_rate["candidate_status"] == "structural_no_signal_observation"
    assert zero_rate["signal_rate_per_observation_day"] == 0.0
    assert low_rate["completed_signal_episodes"] == 1
    assert low_rate["candidate_status"] == "evidence_accumulating_low_signal_rate"
    assert low_rate["estimated_observation_days_to_sample_floor"] == 70


def test_cumulative_uses_prior_reports_and_held_blocks_readiness(tmp_path: Path):
    state_dir = tmp_path / "runtime"
    output_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source-quality"
    _write_source_quality(source_quality_dir, "2026-08-10")
    _write_states(state_dir, "2026-08-10")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )
    first_json, _ = write_report(first, output_dir)
    legacy = json.loads(first_json.read_text(encoding="utf-8"))
    legacy["schema"] = "samsung_machine_entry_tuning_report_v2"
    first_json.write_text(json.dumps(legacy), encoding="utf-8")

    _write_states(state_dir, "2026-08-11", held_machine="midday")
    _write_source_quality(source_quality_dir, "2026-08-11")
    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )

    midday = second["windows"][CLEAN_WINDOW_NAME]["midday"]
    held_row = second["daily"]["machines"]["midday"]
    assert held_row["source_quality"] == "pass"
    assert held_row["eligible_for_cumulative_tuning"] is False
    assert held_row["outcome_complete_for_ev"] is False
    assert held_row["outcome_exclusion_reasons"] == ["held_or_unresolved_inventory"]
    assert second["schema"] == REPORT_SCHEMA
    assert set(second["windows"]) == {
        CLEAN_WINDOW_NAME,
        POST_APPLY_WINDOW_NAME,
        "rolling_10d",
        "rolling_20d",
    }
    coverage = second["clean_baseline_window"]
    assert coverage["available_actual_observation_dates"] == [
        "2026-08-10",
        "2026-08-11",
    ]
    assert coverage["available_actual_observation_date_count"] == 2
    assert coverage["unobserved_trading_date_count"] > 0
    assert coverage["unobserved_dates_block_candidate"] is False
    assert coverage["candidate_window_uses_only_available_actual_observations"] is True
    assert coverage["missing_dates_imputed_as_outcomes"] is False
    assert coverage["historical_market_replay_included"] is False
    assert midday["summary"]["report_days"] == 2
    assert midday["summary"]["signal_attempts"] == 1
    assert midday["summary"]["observed_signal_attempts"] == 2
    assert midday["summary"]["held_legs"] == 1
    assert midday["summary"]["target_price_proxy_completed_legs"] == 1
    assert midday["summary"]["candidate_status"] == "inventory_or_order_unresolved"
    assert midday["summary"]["allowed_runtime_apply"] is False
    gate = second["operator_review_gate"]["midday"]
    assert gate["status"] == "inventory_or_order_unresolved"
    assert gate["clean_baseline_completed_signal_episodes"] == 1
    assert gate["clean_baseline_equal_weight_avg_profit_pct"] == pytest.approx(0.085714)
    assert gate["clean_baseline_notional_weighted_ev_pct"] is None
    assert gate["rolling_10d_notional_weighted_ev_pct"] is None
    assert gate["rolling_20d_notional_weighted_ev_pct"] is None
    assert gate["broker_priced_completed_legs"] == 0
    assert gate["allowed_runtime_apply"] is False
    assert any(
        item["resulting_policy"]
        == {
            "rolling_high_drawdown_pct": 1.5,
            "rolling_low_proximity_pct": 0.1,
        }
        for item in midday["entry_axis_observations"]
    )
    candidate = build_policy_candidate(second)
    assert candidate["runtime_effect"] is False
    assert candidate["machines"]["midday"]["selection_status"] == (
        "carry_forward_inventory_or_order_unresolved"
    )
    assert candidate["machines"]["midday"]["policy"]["target_ticks"] == 2


def test_clean_baseline_is_enforced(tmp_path: Path):
    with pytest.raises(ValueError, match="clean_tuning_baseline"):
        build_report(
            target_date="2026-06-04",
            state_dir=tmp_path,
            output_dir=tmp_path / "reports",
            cost_pct=0.20,
        )


def test_prior_date_target_completion_reconciles_to_original_machine_day(
    tmp_path: Path,
):
    state_dir = tmp_path / "runtime"
    output_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source-quality"
    _write_states(state_dir, "2026-08-10")
    _write_source_quality(source_quality_dir, "2026-08-10")
    _write_source_quality(source_quality_dir, "2026-08-11")

    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )

    reconciliation = report["prior_state_reconciliations"]["midday"]
    assert reconciliation["source_date"] == "2026-08-10"
    assert reconciliation["state_status"] == "COMPLETE"
    summary = report["windows"][CLEAN_WINDOW_NAME]["midday"]["summary"]
    assert summary["completed_signal_episodes"] == 1
    assert summary["completed_legs"] == 1
    assert summary["held_legs"] == 0
    assert report["daily"]["machines"]["midday"]["attempted"] is False


def test_broker_exit_amendment_persists_across_newer_machine_state(tmp_path: Path):
    state_dir = tmp_path / "runtime"
    output_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source-quality"
    receipt_path = tmp_path / "episode_manual_exit_receipts.json"
    for trade_date in ("2026-08-10", "2026-08-11", "2026-08-12"):
        _write_source_quality(source_quality_dir, trade_date)

    _write_states(state_dir, "2026-08-10", held_machine="midday")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
        applied_dir=tmp_path / "applied",
        manual_exit_receipt_registry_path=receipt_path,
    )
    write_report(first, output_dir)
    receipt_path.write_text(
        json.dumps(
            {
                "schema": "episode_manual_exit_receipt_registry_v1",
                "receipts": [
                    {
                        "entry_trade_date": "2026-08-10",
                        "fill_price": 68_000,
                        "filled_qty": 1,
                        "owner_id": "samsung_midday",
                        "status": "applied",
                        "symbol": "005930",
                        "applied_at_kst": "2026-08-11T09:00:00+09:00",
                        "order_date": "2026-08-11",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
        applied_dir=tmp_path / "applied",
        manual_exit_receipt_registry_path=receipt_path,
    )
    write_report(second, output_dir)
    second_summary = second["windows"][CLEAN_WINDOW_NAME]["midday"]["summary"]
    assert second_summary["held_legs"] == 0
    assert second_summary["manual_exit_loss_legs"] == 1
    assert second_summary["broker_realized_net_profit_krw"] < 0

    _write_states(state_dir, "2026-08-12")
    third = build_report(
        target_date="2026-08-12",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
        applied_dir=tmp_path / "applied",
        manual_exit_receipt_registry_path=receipt_path,
    )
    third_summary = third["windows"][CLEAN_WINDOW_NAME]["midday"]["summary"]
    assert third_summary["completed_signal_episodes"] == 2
    assert third_summary["held_legs"] == 0
    assert third_summary["manual_exit_loss_legs"] == 1
    assert third_summary["broker_realized_net_profit_krw"] < 0
    assert third["outcome_amendment_ledger"]["status"] == "pass"
    assert any(
        item["source_kind"] == "broker_verified_manual_exit_receipt_registry"
        for item in third["outcome_amendment_ledger"]["records"]
    )


def test_nontrading_report_amendment_is_loaded_on_next_trading_day(tmp_path: Path):
    state_dir = tmp_path / "runtime"
    output_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source-quality"
    applied_dir = tmp_path / "applied"
    for trade_date in ("2026-08-07", "2026-08-08", "2026-08-10"):
        _write_source_quality(source_quality_dir, trade_date)

    _write_states(state_dir, "2026-08-07", held_machine="midday")
    friday = build_report(
        target_date="2026-08-07",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
        applied_dir=applied_dir,
    )
    write_report(friday, output_dir)

    _write_states(state_dir, "2026-08-07")
    saturday = build_report(
        target_date="2026-08-08",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
        applied_dir=applied_dir,
    )
    assert saturday["target_date_is_krx_trading_day"] is False
    assert saturday["prior_state_reconciliations"]["midday"]["state_status"] == (
        "COMPLETE"
    )
    write_report(saturday, output_dir)

    _write_states(state_dir, "2026-08-10")
    monday = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
        applied_dir=applied_dir,
    )
    summary = monday["windows"][CLEAN_WINDOW_NAME]["midday"]["summary"]
    assert summary["completed_signal_episodes"] == 2
    assert summary["held_legs"] == 0


def test_prior_report_contract_mismatch_is_counted_and_excluded(tmp_path: Path):
    state_dir = tmp_path / "runtime"
    output_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source-quality"
    _write_source_quality(source_quality_dir, "2026-08-10")
    _write_states(state_dir, "2026-08-10")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )
    json_path, _ = write_report(first, output_dir)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    payload["cost_pct"] = 0.10
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    _write_states(state_dir, "2026-08-11")
    _write_source_quality(source_quality_dir, "2026-08-11")
    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )

    summary = second["windows"][CLEAN_WINDOW_NAME]["midday"]["summary"]
    all_cohorts = second["windows"][CLEAN_WINDOW_NAME]["midday"][
        "all_policy_cohorts_summary_audit_only"
    ]
    assert summary["source_gap_days"] == 0
    assert all_cohorts["source_gap_days"] == 1
    assert summary["eligible_report_days"] == 1
    assert summary["candidate_status"] == "collect_sample"


def test_missing_source_quality_audit_blocks_tuning_candidate(tmp_path: Path):
    state_dir = tmp_path / "runtime"
    _write_states(state_dir, "2026-08-11")

    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        cost_pct=0.20,
        source_quality_dir=tmp_path / "missing-source-quality",
    )
    candidate = build_policy_candidate(report)

    assert report["source_quality_preflight"]["tuning_input_allowed"] is False
    assert report["operator_review_gate"]["midday"]["status"] == (
        "source_quality_blocked"
    )
    assert candidate["machines"]["midday"]["selection_status"] == (
        "carry_forward_source_quality_blocked"
    )


def test_unconsumed_prior_candidate_is_not_runtime_authority(
    tmp_path: Path,
):
    state_dir = tmp_path / "runtime"
    report_dir = tmp_path / "reports"
    candidate_dir = tmp_path / "candidates"
    source_quality_dir = tmp_path / "source-quality"
    _write_states(state_dir, "2026-08-10")
    _write_source_quality(source_quality_dir, "2026-08-10")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=report_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )
    prior = build_policy_candidate(first)
    prior["machines"]["midday"]["policy"].update(
        {
            "rolling_high_drawdown_pct": 1.50,
        }
    )
    policies = {machine: item["policy"] for machine, item in prior["machines"].items()}
    prior["policy_hash"] = policy_hash(policies)
    prior["policy_mutations"] = policy_mutations_between(
        BASELINE_POLICIES, policies, include_kind=True
    )
    prior["candidate_hash"] = candidate_artifact_hash(prior)
    atomic_write_json(
        candidate_dir / "samsung_machine_entry_policy_candidate_2026-08-10.json",
        prior,
    )

    _write_states(state_dir, "2026-08-11")
    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=report_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )
    path = write_policy_candidate(second, candidate_dir)
    next_candidate = json.loads(path.read_text(encoding="utf-8"))

    assert next_candidate["machines"]["midday"]["policy"] == BASELINE_POLICIES["midday"]


def test_subset_even_with_positive_uplift_has_no_new_runtime_authority(tmp_path: Path):
    state_dir = tmp_path / "runtime"
    _write_states(state_dir, "2026-08-11")
    _write_source_quality(tmp_path / "quality", "2026-08-11")
    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        cost_pct=0.20,
        source_quality_dir=tmp_path / "quality",
        applied_dir=tmp_path / "applied",
    )
    for window in report["windows"].values():
        for machine in ("midday", "afternoon"):
            for axis in window[machine]["entry_axis_observations"]:
                axis["outcome"].update(
                    candidate_status="auto_bounded_candidate_ready",
                    eligible_report_days=10,
                    completed_signal_episodes=8,
                    completed_legs=16,
                    broker_priced_completed_legs=16,
                    notional_weighted_ev_pct=0.20,
                    broker_realized_net_profit_krw=2000,
                )
    for machine in ("midday", "afternoon"):
        report["operator_review_gate"][machine][
            "status"
        ] = "auto_bounded_candidate_ready"
    report["artifact_hash"] = report_artifact_hash(report)
    candidate = build_policy_candidate(report)
    assert candidate["policy_mutations"] == []
    assert candidate["runtime_optimization_owner"] == "machine_entry_timing_tuning"
    assert (
        candidate["machines"]["midday"]["evidence"]["subset_new_runtime_authority"]
        is False
    )


def test_rollback_requires_actual_policy_and_contiguous_apply_epoch(tmp_path: Path):
    from copy import deepcopy
    from src.trading.order.samsung_entry_policy import validate_candidate

    applied_dir = tmp_path / "applied"
    applied = baseline_applied_payload(target_date=date(2026, 8, 20), reason="test")
    applied["machines"]["midday"]["policy"]["rolling_high_drawdown_pct"] = 1.50
    applied["policy_hash"] = policy_hash(
        {m: x["policy"] for m, x in applied["machines"].items()}
    )
    atomic_write_json(
        applied_dir / "samsung_machine_entry_policy_2026-08-20.json", applied
    )
    _write_states(tmp_path / "runtime", "2026-08-20")
    _write_source_quality(tmp_path / "quality", "2026-08-20")
    report = build_report(
        target_date="2026-08-20",
        state_dir=tmp_path / "runtime",
        output_dir=tmp_path / "reports",
        cost_pct=0.20,
        source_quality_dir=tmp_path / "quality",
        applied_dir=applied_dir,
    )
    post = report["windows"][POST_APPLY_WINDOW_NAME]["midday"]
    post.update(
        applied_epoch_start="2026-08-14",
        observed_trading_dates=["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"],
    )
    post["summary"].update(
        completed_signal_episodes=4,
        broker_priced_completed_legs=8,
        broker_sell_fill_price_coverage=1.0,
        notional_weighted_ev_pct=-0.10,
        broker_realized_net_profit_krw=-1000,
        held_legs=0,
        unresolved_legs=0,
    )
    report["operator_review_gate"]["midday"]["status"] = "auto_bounded_candidate_ready"
    report["artifact_hash"] = report_artifact_hash(report)
    selected = build_policy_candidate(report)
    assert selected["policy_mutations"] == [
        {
            "machine": "midday",
            "axis": "rolling_high_drawdown_pct",
            "before": 1.50,
            "after": 1.25,
            "kind": "bounded_rollback",
        }
    ]
    assert validate_candidate(selected, source_report=report) == (True, "valid")
    wrong = deepcopy(report)
    wrong["windows"][POST_APPLY_WINDOW_NAME]["midday"]["policy_cohort"][
        "rolling_high_drawdown_pct"
    ] = 1.25
    assert build_policy_candidate(wrong)["policy_mutations"] == []
    wrong = deepcopy(report)
    wrong["windows"][POST_APPLY_WINDOW_NAME]["midday"]["observed_trading_dates"].append(
        "2026-08-13"
    )
    assert build_policy_candidate(wrong)["policy_mutations"] == []
    wrong = deepcopy(report)
    wrong["windows"][POST_APPLY_WINDOW_NAME]["midday"][
        "matches_source_date_applied_policy"
    ] = False
    assert build_policy_candidate(wrong)["policy_mutations"] == []


def test_future_receipt_does_not_backdate_loss(tmp_path: Path):
    state_dir, reports, quality = (
        tmp_path / name for name in ("runtime", "reports", "quality")
    )
    for day in ("2026-08-10", "2026-08-11", "2026-08-12"):
        _write_source_quality(quality, day)
    _write_states(state_dir, "2026-08-10", held_machine="midday")
    receipt_path = tmp_path / "receipts.json"
    atomic_write_json(
        receipt_path,
        {
            "schema": "episode_manual_exit_receipt_registry_v1",
            "receipts": [
                {
                    "entry_trade_date": "2026-08-10",
                    "owner_id": "samsung_midday",
                    "symbol": "005930",
                    "status": "applied",
                    "filled_qty": 1,
                    "fill_price": 68000,
                    "order_date": "2026-08-12",
                    "applied_at_kst": "2026-08-12T09:00:00+09:00",
                }
            ],
        },
    )
    args = dict(
        state_dir=state_dir,
        output_dir=reports,
        source_quality_dir=quality,
        applied_dir=tmp_path / "applied",
        manual_exit_receipt_registry_path=receipt_path,
        cost_pct=0.20,
    )
    first = build_report(target_date="2026-08-11", **args)
    assert not any(
        x["source_kind"] == "broker_verified_manual_exit_receipt_registry"
        for x in first["outcome_amendment_ledger"]["records"]
    )
    write_report(first, reports)
    later = build_report(target_date="2026-08-12", **args)
    manual = [
        x
        for x in later["outcome_amendment_ledger"]["records"]
        if x["source_kind"] == "broker_verified_manual_exit_receipt_registry"
    ]
    assert len(manual) == 1
    assert manual[0]["row"]["legs"][0]["equal_weight_profit_pct"] < 0
    write_report(later, reports)
    atomic_write_json(
        receipt_path,
        {"schema": "episode_manual_exit_receipt_registry_v1", "receipts": []},
    )
    _write_states(state_dir, "2026-08-12")
    repeated = build_report(target_date="2026-08-12", **args)
    assert manual[0]["amendment_id"] in {
        x["amendment_id"] for x in repeated["outcome_amendment_ledger"]["records"]
    }


def test_source_quality_wrong_date_cannot_authorize_report(tmp_path: Path):
    from src.engine.monitoring.samsung_machine_entry_tuning import (
        _source_quality_preflight,
    )

    path = tmp_path / "observation_source_quality_audit_2026-08-12.json"
    atomic_write_json(
        path,
        {
            "report_type": "observation_source_quality_audit",
            "target_date": "2026-08-11",
            "status": "pass",
            "summary": {"tuning_input_allowed": True},
        },
    )
    assert (
        _source_quality_preflight("2026-08-12", tmp_path)["tuning_input_allowed"]
        is False
    )


def test_missing_exit_time_cannot_backdate_mutable_state_completion():
    from src.engine.monitoring.samsung_machine_entry_tuning import (
        _row_known_by_report_date,
    )

    row = {"legs": [{"completed": True, "target_filled_at": None}]}
    assert not _row_known_by_report_date(row, "2026-08-27", require_exit_timestamp=True)
    row["legs"][0]["target_filled_at"] = "2026-08-28T09:00:00+09:00"
    assert not _row_known_by_report_date(row, "2026-08-27", require_exit_timestamp=True)
    assert _row_known_by_report_date(row, "2026-08-28", require_exit_timestamp=True)


def test_sibling_policy_mutation_does_not_reset_machine_cohort(tmp_path: Path):
    from src.engine.monitoring.samsung_machine_entry_tuning import (
        _policy_cohort_contract,
    )

    for day in (date(2026, 8, 17), date(2026, 8, 18)):
        applied = baseline_applied_payload(target_date=day, reason="test")
        if day.day == 18:
            applied["machines"]["midday"]["policy"]["rolling_high_drawdown_pct"] = 1.50
            applied["policy_hash"] = policy_hash(
                {m: x["policy"] for m, x in applied["machines"].items()}
            )
        atomic_write_json(
            tmp_path / f"samsung_machine_entry_policy_{day}.json", applied
        )
    a, _ = _policy_cohort_contract(
        {"target_date": "2026-08-17", "attempted": False}, "afternoon", tmp_path
    )
    b, _ = _policy_cohort_contract(
        {"target_date": "2026-08-18", "attempted": False}, "afternoon", tmp_path
    )
    assert a == b


def test_no_fill_has_no_broker_ev_or_completion_eta():
    row = {
        "attempted": True,
        "eligible_for_cumulative_tuning": True,
        "source_quality": "pass",
        "legs": [{"quantity": 10, "entry_price": 70000, "position_qty": 0}],
        "summary": {"completed_signal_episode": True},
    }
    summary = _aggregate_rows([row])
    assert summary["notional_weighted_ev_pct"] is None
    assert summary["estimated_observation_days_to_sample_floor"] is None
    assert (
        summary["sample_floor_estimate_contract"]["status"]
        == "no_broker_completion_rate_available"
    )


def test_nontrading_target_is_excluded_and_cannot_open_candidate(tmp_path: Path):
    report = build_report(
        target_date="2026-08-09",
        state_dir=tmp_path / "states",
        output_dir=tmp_path / "reports",
        cost_pct=0.20,
        source_quality_dir=tmp_path / "source_quality",
    )
    candidate = build_policy_candidate(report)

    assert report["target_date_is_krx_trading_day"] is False
    assert (
        "2026-08-09"
        not in report["clean_baseline_window"]["available_actual_observation_dates"]
    )
    assert candidate["policy_mutations"] == []


def test_postclose_wrapper_declares_report_only_producer():
    project_root = Path(__file__).resolve().parents[2]
    wrapper = (project_root / "deploy" / "run_threshold_cycle_postclose.sh").read_text(
        encoding="utf-8"
    )
    assert "THRESHOLD_CYCLE_RUN_SAMSUNG_MACHINE_ENTRY_TUNING" in wrapper
    assert "src.engine.monitoring.samsung_machine_entry_tuning" in wrapper
    assert f"{REPORT_TYPE}_${{TARGET_DATE}}.json" in wrapper
    assert "samsung_machine_entry_policy_candidate_${TARGET_DATE}.json" in wrapper
