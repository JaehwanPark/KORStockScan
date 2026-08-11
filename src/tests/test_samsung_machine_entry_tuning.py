from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.engine.monitoring.samsung_machine_entry_tuning import (
    REPORT_TYPE,
    build_policy_candidate,
    build_report,
    extract_machine_row,
    write_policy_candidate,
    write_report,
)
from src.trading.order.samsung_entry_policy import (
    BASELINE_POLICIES,
    atomic_write_json,
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
    state_path.write_text(json.dumps(_state("midday", "2026-08-11")), encoding="utf-8")

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
    write_report(first, output_dir)

    _write_states(state_dir, "2026-08-11", held_machine="midday")
    _write_source_quality(source_quality_dir, "2026-08-11")
    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=output_dir,
        cost_pct=0.20,
        source_quality_dir=source_quality_dir,
    )

    midday = second["windows"]["cumulative"]["midday"]
    assert midday["summary"]["report_days"] == 2
    assert midday["summary"]["held_legs"] == 1
    assert midday["summary"]["candidate_status"] == "inventory_or_order_unresolved"
    assert midday["summary"]["allowed_runtime_apply"] is False
    assert second["operator_review_gate"]["midday"] == {
        "status": "inventory_or_order_unresolved",
        "cumulative_completed_signal_episodes": 1,
        "rolling10_equal_weight_avg_profit_pct": pytest.approx(0.085714),
        "rolling20_equal_weight_avg_profit_pct": pytest.approx(0.085714),
        "cumulative_equal_weight_avg_profit_pct": pytest.approx(0.085714),
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

    summary = second["windows"]["cumulative"]["midday"]["summary"]
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
        "source_quality_preflight": {"tuning_input_allowed": True},
        "operator_review_gate": {
            "morning": {"status": "collect_sample"},
            "midday": {"status": "operator_review_candidate"},
            "afternoon": {"status": "operator_review_candidate"},
        },
        "windows": {},
    }
    for window in ("rolling10", "rolling20", "cumulative"):
        report["windows"][window] = {
            "morning": {"entry_axis_observations": []},
            "midday": {"entry_axis_observations": [midday_single, midday_combined]},
            "afternoon": {"entry_axis_observations": [afternoon_single]},
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


def test_postclose_wrapper_declares_report_only_producer():
    project_root = Path(__file__).resolve().parents[2]
    wrapper = (project_root / "deploy" / "run_threshold_cycle_postclose.sh").read_text(
        encoding="utf-8"
    )
    assert "THRESHOLD_CYCLE_RUN_SAMSUNG_MACHINE_ENTRY_TUNING" in wrapper
    assert "src.engine.monitoring.samsung_machine_entry_tuning" in wrapper
    assert f"{REPORT_TYPE}_${{TARGET_DATE}}.json" in wrapper
    assert "samsung_machine_entry_policy_candidate_${TARGET_DATE}.json" in wrapper
