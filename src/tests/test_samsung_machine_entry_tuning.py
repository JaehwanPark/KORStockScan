from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.engine.monitoring.samsung_machine_entry_tuning import (
    CLEAN_WINDOW_NAME,
    REPORT_SCHEMA,
    REPORT_TYPE,
    _aggregate_rows,
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
    load_applied_machine_policy,
    policy_hash,
    policy_mutations_between,
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
        "signal_features": _features(machine),
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
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )


def test_extracts_actual_two_leg_outcome_without_broker_identifiers(tmp_path: Path):
    state_path = tmp_path / "state.json"
    payload = _state("midday", "2026-08-11")
    payload["signal_features"].update(
        {
            "signal_decision_at": "2026-08-11T14:00:01+09:00",
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
    assert row["signal_features"]["signal_decision_at"] == ("2026-08-11T14:00:01+09:00")
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
    assert summary["notional_weighted_ev_pct"] == round(expected_ev, 6)

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
    assert second["operator_review_gate"]["midday"] == {
        "status": "inventory_or_order_unresolved",
        "clean_baseline_completed_signal_episodes": 1,
        "clean_baseline_equal_weight_avg_profit_pct": pytest.approx(0.085714),
        "clean_baseline_notional_weighted_ev_pct": pytest.approx(0.0),
        "rolling_10d_notional_weighted_ev_pct": pytest.approx(0.0),
        "rolling_20d_notional_weighted_ev_pct": pytest.approx(0.0),
        "broker_priced_completed_legs": 0,
        "allowed_runtime_apply": False,
    }
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
        "carry_forward_current_policy_insufficient_evidence"
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
    assert summary["source_gap_days"] == 1
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
        "carry_forward_current_policy_insufficient_evidence"
    )


def test_candidate_carries_prior_tightening_when_new_evidence_is_blocked(
    tmp_path: Path,
):
    state_dir = tmp_path / "runtime"
    report_dir = tmp_path / "reports"
    candidate_dir = tmp_path / "candidates"
    _write_states(state_dir, "2026-08-10")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=report_dir,
        cost_pct=0.20,
        source_quality_dir=tmp_path / "missing-source-quality",
    )
    prior = build_policy_candidate(first)
    prior["machines"]["midday"]["policy"].update(
        {
            "rolling_high_drawdown_pct": 1.50,
        }
    )
    policies = {machine: item["policy"] for machine, item in prior["machines"].items()}
    prior["policy_hash"] = policy_hash(policies)
    prior["policy_mutations"] = policy_mutations_between(BASELINE_POLICIES, policies)
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
        source_quality_dir=tmp_path / "missing-source-quality",
    )
    path = write_policy_candidate(second, candidate_dir)
    next_candidate = json.loads(path.read_text(encoding="utf-8"))

    assert (
        next_candidate["machines"]["midday"]["policy"]
        == prior["machines"]["midday"]["policy"]
    )


def test_candidate_changes_only_highest_ev_single_axis_across_regular_machines():
    def outcome(ev: float) -> dict:
        return {
            "candidate_status": "operator_review_candidate",
            "completed_signal_episodes": 20,
            "completed_legs": 20,
            "broker_priced_completed_legs": 20,
            "notional_weighted_ev_pct": ev,
        }

    def axis(machine: str, *, drawdown: float, near_low: float, ev: float) -> dict:
        return {
            "axis": f"{machine}_{drawdown}_{near_low}",
            "resulting_policy": {
                "rolling_high_drawdown_pct": drawdown,
                "rolling_low_proximity_pct": near_low,
            },
            "current_policy_cohort": {
                "rolling_high_drawdown_pct": 1.25,
                "rolling_low_proximity_pct": 0.20,
            },
            "outcome": outcome(ev),
        }

    midday_single = axis("midday", drawdown=1.50, near_low=0.20, ev=0.10)
    midday_combined = axis("midday", drawdown=1.50, near_low=0.10, ev=0.90)
    afternoon_single = axis("afternoon", drawdown=1.25, near_low=0.10, ev=0.20)
    report = {
        "target_date": "2026-08-11",
        "generated_at_kst": "2026-08-11T20:10:00+09:00",
        "clean_tuning_baseline_date": "2026-06-05",
        "target_date_is_krx_trading_day": True,
        "source_quality_preflight": {"tuning_input_allowed": True},
        "operator_review_gate": {
            "morning": {"status": "collect_sample"},
            "midday": {"status": "operator_review_candidate"},
            "afternoon": {"status": "operator_review_candidate"},
        },
        "windows": {
            CLEAN_WINDOW_NAME: {
                "morning": {"entry_axis_observations": []},
                "midday": {"entry_axis_observations": [midday_single, midday_combined]},
                "afternoon": {"entry_axis_observations": [afternoon_single]},
            },
            "rolling_10d": {
                "morning": {"entry_axis_observations": []},
                "midday": {"entry_axis_observations": [midday_single, midday_combined]},
                "afternoon": {"entry_axis_observations": [afternoon_single]},
            },
            "rolling_20d": {
                "morning": {"entry_axis_observations": []},
                "midday": {"entry_axis_observations": [midday_single, midday_combined]},
                "afternoon": {"entry_axis_observations": [afternoon_single]},
            },
        },
    }

    candidate = build_policy_candidate(report)

    assert candidate["policy_mutations"] == [
        {
            "machine": "afternoon",
            "axis": "rolling_low_proximity_pct",
            "before": 0.20,
            "after": 0.10,
        }
    ]
    assert candidate["machines"]["midday"]["policy"] == BASELINE_POLICIES["midday"]
    assert candidate["machines"]["midday"]["selection_status"] == (
        "carry_forward_same_stage_single_axis_guard"
    )

    rolling_negative = json.loads(json.dumps(report))
    for item in rolling_negative["windows"]["rolling_10d"]["afternoon"][
        "entry_axis_observations"
    ]:
        item["outcome"]["notional_weighted_ev_pct"] = -0.01
    rolling_blocked = build_policy_candidate(rolling_negative)
    assert rolling_blocked["policy_mutations"] == [
        {
            "machine": "midday",
            "axis": "rolling_high_drawdown_pct",
            "before": 1.25,
            "after": 1.5,
        }
    ]


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
