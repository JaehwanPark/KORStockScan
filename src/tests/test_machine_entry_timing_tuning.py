from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from src.engine.automation.machine_entry_timing_tuning import (
    _ask_horizon_ready,
    _candidate_observation,
    _evaluate_cohort,
    _same_stage_owner_guard,
    build_applied_policy,
    build_report,
)
from src.trading.config.machine_entry_timing_policy import (
    AUTHORITY,
    policy_hash,
    resolve_entry_confirmation_delay,
    scope_key,
    validate_applied_policy,
)
from src.utils.market_day import is_krx_trading_day


def _trading_dates(through: date, count: int) -> list[date]:
    result: list[date] = []
    candidate = through
    while len(result) < count:
        if is_krx_trading_day(candidate):
            result.append(candidate)
        candidate -= timedelta(days=1)
    return sorted(result)


def _entry_row(source_date: date, index: int) -> dict:
    anchor_at = datetime.fromisoformat(f"{source_date.isoformat()}T09:30:00+09:00")
    return {
        "anchor_id": f"episode:{index}",
        "lifecycle_id": f"episode-lifecycle:{index}",
        "owner": "episode",
        "scope_id": "samsung_heavy_midday",
        "entry_timing_scope_id": "samsung_heavy_midday",
        "symbol": "005930",
        "session": "KRX_REGULAR",
        "entry_state": "UNSPECIFIED",
        "anchor_at": anchor_at.isoformat(),
        "anchor_price": 100.0,
        "owner_entry_limit_price": 100.0,
        "owner_target_price": 101.0,
        "anchor_role": "episode_signal_decision_leg",
        "classification": "supportive_confirmation_candidate",
        "owner_policy_tuning_eligible": True,
        "actual_order_submitted": True,
        "owner_round_trip_cost_pct": 0.23,
        "owner_outcome": {
            "realized": True,
            "exit_at": (anchor_at + timedelta(seconds=30)).isoformat(),
            "exit_price": 101.0,
            "gross_no_slippage_return_pct": 1.0,
            "cost_aware_net_return_pct": 0.77,
        },
        "entry_confirmation_bbo_horizons": {
            "1": {"observed": True, "best_ask": 99.0, "depth_backed": True},
            "3": {"observed": True, "best_ask": 99.5, "depth_backed": True},
            "5": {"observed": True, "best_ask": 100.5, "depth_backed": True},
        },
        "entry_ask_depletion": {
            "horizons": [
                {
                    "horizon_ms": delay * 1000,
                    "eligible_for_feature_ablation": True,
                }
                for delay in (1, 3, 5)
            ]
        },
    }


def test_cumulative_tuning_selects_one_exact_scope_and_runtime_loads_it(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    policy_dir = tmp_path / "policy"
    target_date = date(2026, 8, 27)
    for index, source_date in enumerate(_trading_dates(target_date, 20), start=1):
        payload = {
            "schema": "machine_microstructure_attribution_v1",
            "target_date": source_date.isoformat(),
            "clean_tuning_baseline_date": "2026-06-05",
            "clean_baseline_allowed": True,
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "micro_entry_confirmation": {
                "entry_anchors": [_entry_row(source_date, index)]
            },
        }
        path = source_dir / f"machine_microstructure_attribution_{source_date}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(
        target_date=target_date,
        source_dir=source_dir,
        low_price_candidate_dir=tmp_path / "low-price-candidates",
        samsung_candidate_dir=tmp_path / "samsung-candidates",
        widget_policy_dir=tmp_path / "widget-policies",
    )
    source_report_path = (
        tmp_path / f"machine_entry_timing_tuning_{target_date.isoformat()}.json"
    )
    source_report_path.write_text(json.dumps(report), encoding="utf-8")
    applied = build_applied_policy(report, source_report_path=source_report_path)

    assert report["decision"] == "select_one_next_session_entry_confirmation_delay"
    assert report["winner"]["selected"]["entry_confirmation_delay_sec"] == 1
    assert len(applied["scopes"]) == 1
    effective_date = date.fromisoformat(applied["target_date"])
    assert validate_applied_policy(applied, target_date=effective_date) == (
        True,
        "ready",
    )
    policy_dir.mkdir(parents=True)
    (policy_dir / f"machine_entry_timing_policy_{effective_date}.json").write_text(
        json.dumps(applied), encoding="utf-8"
    )
    delay, provenance = resolve_entry_confirmation_delay(
        target_date=effective_date,
        owner="episode",
        scope_id="samsung_heavy_midday",
        symbol="005930",
        session="KRX_REGULAR",
        entry_state="UNSPECIFIED",
        policy_dir=policy_dir,
        source_report_dir=source_report_path.parent,
    )
    assert delay == 1
    assert provenance["status"] == "applied"

    source_report_path.write_text(json.dumps({**report, "decision": "tampered"}))
    delay, provenance = resolve_entry_confirmation_delay(
        target_date=effective_date,
        owner="episode",
        scope_id="samsung_heavy_midday",
        symbol="005930",
        session="KRX_REGULAR",
        entry_state="UNSPECIFIED",
        policy_dir=policy_dir,
        source_report_dir=source_report_path.parent,
    )
    assert delay == 0
    assert provenance["status"] == "entry_timing_source_report_contract_invalid"


def test_policy_rejects_multiple_same_stage_selected_scopes() -> None:
    target_date = date(2026, 8, 28)
    evidence = {
        "ready": True,
        "entry_confirmation_delay_sec": 1,
        "observed_trading_days": 20,
        "unique_decision_lifecycles": 20,
        "completed_outcome_count": 20,
        "latest_completed_observation_date": "2026-08-27",
        "target_date_in_completed_observations": True,
        "source_quality_adjusted_ev_pct": 0.1,
        "absolute_ev_uplift_pct": 0.01,
        "baseline_p10_pct": 0.0,
        "candidate_p10_pct": 0.01,
        "bbo_complete_rate_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "paired_completed_coverage_rate_pct": 100.0,
        "delayed_entry_feasibility_rate_pct": 100.0,
        "right_censored_rate_pct": 0.0,
        "rolling_windows": {
            str(window): {"complete": True, "positive_and_improved": True}
            for window in (5, 10, 20)
        },
    }
    scopes = {}
    for symbol in ("005930", "034020"):
        key = scope_key(
            owner="widget",
            scope_id=f"{symbol}:KRX_REGULAR",
            symbol=symbol,
            session="KRX_REGULAR",
            entry_state="ENTRY_READY",
        )
        scopes[key] = {
            "owner": "widget",
            "scope_id": f"{symbol}:KRX_REGULAR",
            "symbol": symbol,
            "session": "KRX_REGULAR",
            "entry_state": "ENTRY_READY",
            "axis": "entry_confirmation_delay_sec",
            "entry_confirmation_delay_sec": 1,
            "evidence": evidence,
            "quantity_effect": False,
            "price_effect": False,
            "target_effect": False,
            "exit_effect": False,
        }
    payload = {
        "schema": "machine_entry_timing_policy_applied_v1",
        "target_date": target_date.isoformat(),
        "source_date": "2026-08-27",
        "clean_tuning_baseline_date": "2026-06-05",
        "decision_authority": AUTHORITY,
        "source_report": "unused.json",
        "source_report_canonical_sha256": "a" * 64,
        "scopes": scopes,
        "policy_hash": policy_hash(scopes),
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
    }

    assert validate_applied_policy(payload, target_date=target_date) == (
        False,
        "entry_timing_policy_same_stage_multi_scope_forbidden",
    )


def test_policy_rejects_malformed_integer_evidence_without_raising() -> None:
    target_date = date(2026, 8, 28)
    key = scope_key(
        owner="widget",
        scope_id="005930:KRX_REGULAR",
        symbol="005930",
        session="KRX_REGULAR",
        entry_state="ENTRY_READY",
    )
    evidence = {
        "ready": True,
        "entry_confirmation_delay_sec": 1,
        "observed_trading_days": 20,
        "unique_decision_lifecycles": 20,
        "completed_outcome_count": 20,
        "latest_completed_observation_date": "2026-08-27",
        "target_date_in_completed_observations": True,
        "source_quality_adjusted_ev_pct": 0.1,
        "absolute_ev_uplift_pct": 0.01,
        "baseline_p10_pct": 0.0,
        "candidate_p10_pct": 0.01,
        "bbo_complete_rate_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "paired_completed_coverage_rate_pct": 100.0,
        "right_censored_rate_pct": 0.0,
        "rolling_windows": {
            str(window): {"complete": True, "positive_and_improved": True}
            for window in (5, 10, 20)
        },
    }
    scopes = {
        key: {
            "owner": "widget",
            "scope_id": "005930:KRX_REGULAR",
            "symbol": "005930",
            "session": "KRX_REGULAR",
            "entry_state": "ENTRY_READY",
            "axis": "entry_confirmation_delay_sec",
            "entry_confirmation_delay_sec": 1,
            "evidence": evidence,
            "quantity_effect": False,
            "price_effect": False,
            "target_effect": False,
            "exit_effect": False,
        }
    }
    payload = {
        "schema": "machine_entry_timing_policy_applied_v1",
        "target_date": target_date.isoformat(),
        "source_date": "2026-08-27",
        "clean_tuning_baseline_date": "2026-06-05",
        "decision_authority": AUTHORITY,
        "source_report": "unused.json",
        "source_report_canonical_sha256": "a" * 64,
        "scopes": scopes,
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
    }
    for field in (
        "observed_trading_days",
        "unique_decision_lifecycles",
        "completed_outcome_count",
    ):
        malformed = json.loads(json.dumps(payload))
        malformed["scopes"][key]["evidence"][field] = "not-an-integer"
        malformed["policy_hash"] = policy_hash(malformed["scopes"])
        assert validate_applied_policy(malformed, target_date=target_date) == (
            False,
            "entry_timing_policy_evidence_floor_invalid",
        )

    malformed = json.loads(json.dumps(payload))
    malformed["scopes"][key]["evidence"]["observed_trading_days"] = 20.5
    malformed["policy_hash"] = policy_hash(malformed["scopes"])
    assert validate_applied_policy(malformed, target_date=target_date) == (
        False,
        "entry_timing_policy_evidence_floor_invalid",
    )


def test_policy_rejects_out_of_range_percentage_evidence() -> None:
    target_date = date(2026, 8, 28)
    key = scope_key(
        owner="widget",
        scope_id="005930:KRX_REGULAR",
        symbol="005930",
        session="KRX_REGULAR",
        entry_state="ENTRY_READY",
    )
    evidence = {
        "ready": True,
        "entry_confirmation_delay_sec": 1,
        "observed_trading_days": 20,
        "unique_decision_lifecycles": 20,
        "completed_outcome_count": 20,
        "latest_completed_observation_date": "2026-08-27",
        "target_date_in_completed_observations": True,
        "source_quality_adjusted_ev_pct": 0.1,
        "absolute_ev_uplift_pct": 0.01,
        "baseline_p10_pct": 0.0,
        "candidate_p10_pct": 0.01,
        "bbo_complete_rate_pct": 101.0,
        "depth_coverage_pct": 100.0,
        "paired_completed_coverage_rate_pct": 100.0,
        "delayed_entry_feasibility_rate_pct": 100.0,
        "right_censored_rate_pct": 0.0,
        "rolling_windows": {
            str(window): {"complete": True, "positive_and_improved": True}
            for window in (5, 10, 20)
        },
    }
    scopes = {
        key: {
            "owner": "widget",
            "scope_id": "005930:KRX_REGULAR",
            "symbol": "005930",
            "session": "KRX_REGULAR",
            "entry_state": "ENTRY_READY",
            "axis": "entry_confirmation_delay_sec",
            "entry_confirmation_delay_sec": 1,
            "evidence": evidence,
            "quantity_effect": False,
            "price_effect": False,
            "target_effect": False,
            "exit_effect": False,
        }
    }
    payload = {
        "schema": "machine_entry_timing_policy_applied_v1",
        "target_date": target_date.isoformat(),
        "source_date": "2026-08-27",
        "clean_tuning_baseline_date": "2026-06-05",
        "decision_authority": AUTHORITY,
        "source_report": "unused.json",
        "source_report_canonical_sha256": "a" * 64,
        "scopes": scopes,
        "policy_hash": policy_hash(scopes),
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "selection_status": "select_one_next_session_entry_confirmation_delay",
    }

    assert validate_applied_policy(payload, target_date=target_date) == (
        False,
        "entry_timing_policy_evidence_floor_invalid",
    )


def test_source_report_requires_explicit_clean_baseline_contract(
    tmp_path: Path,
) -> None:
    target_date = date(2026, 8, 27)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    payload = {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": target_date.isoformat(),
        "clean_tuning_baseline_date": "2026-06-05",
        "clean_baseline_allowed": False,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "micro_entry_confirmation": {"entry_anchors": []},
    }
    source_path = source_dir / f"machine_microstructure_attribution_{target_date}.json"
    source_path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(
        target_date=target_date,
        source_dir=source_dir,
        low_price_candidate_dir=tmp_path / "low-price-candidates",
        samsung_candidate_dir=tmp_path / "samsung-candidates",
        widget_policy_dir=tmp_path / "widget-policies",
    )

    assert report["target_source_ready"] is False
    assert report["rejected_source_artifacts"] == [
        {"source_date": target_date.isoformat(), "path": str(source_path)}
    ]
    assert report["status"] == "source_quality_blocked"
    assert report["sample_floor_assessment"]["state"] == "source_contract_blocked"


def test_report_classifies_blocked_actual_anchors_as_join_gap(
    tmp_path: Path,
) -> None:
    target_date = date(2026, 8, 27)
    source_dir = tmp_path / "source"
    blocked = _entry_row(target_date, 1)
    blocked["anchor_role"] = "episode_signal_bar"
    blocked["classification"] = "source_quality_blocked"
    blocked["source_gap_reasons"] = [
        "actual_signal_decision_timestamp_missing",
        "canonical_0b_market_anchor_within_1s_missing",
    ]
    payload = {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": target_date.isoformat(),
        "clean_tuning_baseline_date": "2026-06-05",
        "clean_baseline_allowed": True,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "micro_entry_confirmation": {"entry_anchors": [blocked]},
    }
    source_dir.mkdir()
    (source_dir / f"machine_microstructure_attribution_{target_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    report = build_report(
        target_date=target_date,
        source_dir=source_dir,
        low_price_candidate_dir=tmp_path / "low-price-candidates",
        samsung_candidate_dir=tmp_path / "samsung-candidates",
        widget_policy_dir=tmp_path / "widget-policies",
    )

    assert report["winner"] is None
    assert report["status"] == "source_quality_blocked"
    assessment = report["sample_floor_assessment"]
    assert assessment["state"] == "instrumentation_or_join_gap"
    assert assessment["shortage_classification_status"] == "classified"
    assert assessment["shortage_class"] == "structural_population_exhaustion"
    assert assessment["target_actual_entry_anchor_count"] == 1
    assert assessment["target_source_quality_blocked_anchor_count"] == 1
    assert assessment["target_source_gap_reasons"] == [
        "actual_signal_decision_timestamp_missing",
        "canonical_0b_market_anchor_within_1s_missing",
    ]
    assert assessment["next_action"] == (
        "repair_exact_entry_anchor_market_join_and_rerun"
    )
    assert assessment["runtime_effect"] is False
    assert assessment["allowed_runtime_apply"] is False


def test_cohort_sample_projection_uses_all_source_days_since_first_seen(
    tmp_path: Path,
) -> None:
    target_date = date(2026, 8, 27)
    source_dir = tmp_path / "source"
    source_dates = _trading_dates(target_date, 5)
    for index, source_date in enumerate(source_dates, start=1):
        rows = [_entry_row(source_date, index)] if index in {1, 5} else []
        payload = {
            "schema": "machine_microstructure_attribution_v1",
            "target_date": source_date.isoformat(),
            "clean_tuning_baseline_date": "2026-06-05",
            "clean_baseline_allowed": True,
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "micro_entry_confirmation": {"entry_anchors": rows},
        }
        path = source_dir / f"machine_microstructure_attribution_{source_date}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(
        target_date=target_date,
        source_dir=source_dir,
        low_price_candidate_dir=tmp_path / "low-price-candidates",
        samsung_candidate_dir=tmp_path / "samsung-candidates",
        widget_policy_dir=tmp_path / "widget-policies",
    )

    assessment = report["cohorts"][0]["sample_floor_assessment"]
    assert assessment["state"] == "natural_sample_wait"
    assert assessment["shortage_class"] == "time_resolvable_shortage"
    assert assessment["source_report_day_count_since_scope_first_seen"] == 5
    assert assessment["completed_outcomes_per_source_day"] == 0.4
    assert assessment["remaining_completed_outcome_count"] == 18
    assert assessment["projected_additional_trading_days_at_observed_yield"] == 45


def test_worse_delayed_ask_is_included_as_negative_paired_uplift() -> None:
    source_date = date(2026, 8, 27)
    row = _entry_row(source_date, 1)
    row.update(
        {
            "owner": "widget",
            "scope_id": "005930:KRX_REGULAR",
            "entry_timing_scope_id": "005930:KRX_REGULAR",
            "entry_state": "ENTRY_READY",
            "anchor_role": "actual_widget_entry_signal",
        }
    )
    row["owner_outcome"]["exit_reason"] = "final_exit_fill"
    row["entry_confirmation_bbo_horizons"]["1"]["best_ask"] = 101.0

    observation = _candidate_observation(
        source_date=source_date,
        row=row,
        delay_sec=1,
    )

    assert observation is not None
    assert observation["candidate_net_pct"] < observation["baseline_net_pct"]


def test_episode_worse_delayed_fill_is_excluded_even_within_original_limit() -> None:
    source_date = date(2026, 8, 27)
    row = _entry_row(source_date, 1)
    row["anchor_price"] = 99.0
    row["owner_entry_limit_price"] = 100.0
    row["owner_target_price"] = 100.0
    row["owner_outcome"].update(
        {
            "exit_price": 100.0,
            "gross_no_slippage_return_pct": (100.0 / 99.0 - 1.0) * 100.0,
        }
    )
    row["entry_confirmation_bbo_horizons"]["1"]["best_ask"] = 99.5

    observation = _candidate_observation(
        source_date=source_date,
        row=row,
        delay_sec=1,
    )

    assert observation is None


def test_episode_better_delayed_fill_preserves_target_tick_count() -> None:
    source_date = date(2026, 8, 27)
    row = _entry_row(source_date, 1)
    row["anchor_price"] = 50_000.0
    row["owner_entry_limit_price"] = 50_000.0
    row["owner_target_price"] = 50_200.0
    row["owner_outcome"].update(
        {
            "exit_price": 50_200.0,
            "gross_no_slippage_return_pct": (50_200.0 / 50_000.0 - 1.0) * 100.0,
        }
    )
    row["entry_confirmation_bbo_horizons"]["1"]["best_ask"] = 49_950.0

    observation = _candidate_observation(
        source_date=source_date,
        row=row,
        delay_sec=1,
    )

    assert observation is not None
    # 50,000 -> 50,200 is two ticks. From 49,950, the same two ticks end at
    # 50,100 across the KRX 50,000-won tick-size boundary, never at 50,150.
    expected_gross_pct = (50_100.0 / 49_950.0 - 1.0) * 100.0
    assert observation["candidate_net_pct"] == expected_gross_pct - 0.23


def test_manual_stop_loss_uses_same_exit_price_and_remains_negative_tuning_input():
    source_date = date(2026, 8, 27)
    row = _entry_row(source_date, 1)
    row["owner_outcome"].update(
        {
            "exit_price": 90.0,
            "gross_no_slippage_return_pct": -10.0,
            "cost_aware_net_return_pct": -10.23,
            "exit_execution_class": "manual_operator_exit",
            "exit_fill_source": "broker_verified_manual_sell_receipt",
            "manual_exit_realized": True,
            "autonomous_target_filled": False,
            "realized_loss": True,
        }
    )
    row["entry_confirmation_bbo_horizons"]["1"]["best_ask"] = 99.0

    observation = _candidate_observation(
        source_date=source_date,
        row=row,
        delay_sec=1,
    )

    assert observation is not None
    assert observation["exit_execution_class"] == "manual_operator_exit"
    assert observation["outcome_basis"] == (
        "manual_operator_exit_same_realized_exit_price"
    )
    assert observation["baseline_realized_loss"] is True
    assert observation["baseline_net_pct"] == -10.23
    assert observation["candidate_net_pct"] == (90.0 / 99.0 - 1.0) * 100.0 - 0.23
    assert observation["candidate_net_pct"] < 0
    assert observation["candidate_net_pct"] > observation["baseline_net_pct"]

    cohort = _evaluate_cohort(
        cohort_rows=[(source_date, row)],
        delay_sec=1,
        target_date=source_date,
    )
    assert cohort["completed_outcome_count"] == 1
    assert cohort["machine_target_fill_outcome_count"] == 0
    assert cohort["manual_operator_exit_outcome_count"] == 1
    assert cohort["manual_operator_exit_loss_outcome_count"] == 1
    assert cohort["baseline_source_quality_adjusted_ev_pct"] == -10.23
    assert cohort["source_quality_adjusted_ev_pct"] < 0
    assert cohort["ready"] is False


def test_widget_take_profit_ratio_is_rounded_up_to_executable_krx_tick() -> None:
    source_date = date(2026, 8, 27)
    row = _entry_row(source_date, 1)
    row.update(
        {
            "owner": "widget",
            "scope_id": "005930:KRX_REGULAR",
            "entry_timing_scope_id": "005930:KRX_REGULAR",
            "entry_state": "ENTRY_READY",
            "anchor_role": "actual_widget_entry_signal",
            "anchor_price": 50_000.0,
            "owner_target_price": 50_100.0,
        }
    )
    row["owner_outcome"].update(
        {
            "exit_reason": "take_profit_fill",
            "exit_price": 50_100.0,
            "gross_no_slippage_return_pct": (50_100.0 / 50_000.0 - 1.0) * 100.0,
        }
    )
    row["entry_confirmation_bbo_horizons"]["1"]["best_ask"] = 49_950.0

    observation = _candidate_observation(
        source_date=source_date,
        row=row,
        delay_sec=1,
    )

    assert observation is not None
    # The raw ratio target is 50,049.9, which is not executable. The widget
    # contract submits the first valid tick at or above that target: 50,100.
    expected_gross_pct = (50_100.0 / 49_950.0 - 1.0) * 100.0
    assert observation["candidate_net_pct"] == expected_gross_pct - 0.23


def test_malformed_ask_horizon_is_not_treated_as_ready() -> None:
    row = _entry_row(date(2026, 8, 27), 1)
    row["entry_ask_depletion"]["horizons"][0]["horizon_ms"] = "invalid"

    assert _ask_horizon_ready(row, 1) is False


def test_unfillable_completed_rows_block_paired_coverage_floor() -> None:
    target_date = date(2026, 8, 27)
    rows = [
        (source_date, _entry_row(source_date, index))
        for index, source_date in enumerate(_trading_dates(target_date, 20), start=1)
    ]
    for _, row in rows[:2]:
        row["entry_confirmation_bbo_horizons"]["1"]["best_ask"] = 101.0

    evaluated = _evaluate_cohort(
        cohort_rows=rows,
        delay_sec=1,
        target_date=target_date,
    )

    assert evaluated["paired_completed_coverage_rate_pct"] == 90.0
    assert evaluated["ready"] is False


def test_stale_completed_cohort_cannot_be_selected_for_next_session() -> None:
    target_date = date(2026, 8, 27)
    rows = [
        (source_date, _entry_row(source_date, index))
        for index, source_date in enumerate(
            _trading_dates(date(2026, 8, 26), 20), start=1
        )
    ]

    evaluated = _evaluate_cohort(
        cohort_rows=rows,
        delay_sec=1,
        target_date=target_date,
    )

    assert evaluated["target_date_in_completed_observations"] is False
    assert evaluated["latest_completed_observation_date"] == "2026-08-26"
    assert evaluated["ready"] is False


def test_existing_regular_entry_mutation_blocks_timing_winner(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    low_price_dir = tmp_path / "low-price"
    target_date = date(2026, 8, 27)
    for index, source_date in enumerate(_trading_dates(target_date, 20), start=1):
        payload = {
            "schema": "machine_microstructure_attribution_v1",
            "target_date": source_date.isoformat(),
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "micro_entry_confirmation": {
                "entry_anchors": [_entry_row(source_date, index)]
            },
        }
        path = source_dir / f"machine_microstructure_attribution_{source_date}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    low_price_dir.mkdir(parents=True)
    (
        low_price_dir / f"low_price_two_leg_policy_candidate_{target_date}.json"
    ).write_text(
        json.dumps(
            {
                "source_date": target_date.isoformat(),
                "policy_mutations": [
                    {
                        "profile_id": "example",
                        "axis": "rolling_high_drawdown_pct",
                        "before": 1.0,
                        "after": 1.25,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        target_date=target_date,
        source_dir=source_dir,
        low_price_candidate_dir=low_price_dir,
        samsung_candidate_dir=tmp_path / "samsung",
        widget_policy_dir=tmp_path / "widget-policies",
    )

    assert report["winner"] is None
    assert report["same_stage_owner_guard"]["mutation_present"] is True
    assert report["decision"] == "baseline_immediate_entry_carry_forward"


def test_widget_entry_policy_change_is_a_same_stage_conflict(tmp_path: Path) -> None:
    policy_dir = tmp_path / "widget-policy"
    target_date = date(2026, 8, 27)
    effective_date = date(2026, 8, 28)

    def policy(day: date, *, cap: int) -> dict:
        return {
            "schema": "widget_auto_trade_policy_v1",
            "effective_date": day.isoformat(),
            "runtime_effect": True,
            "symbols": {
                "005930": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "enabled": True,
                            "allowed_entry_states": ["ENTRY_READY"],
                            "allowed_entry_sessions": ["KRX_REGULAR"],
                            "allowed_entry_venues": ["KRX"],
                            "max_completed_entries_per_day": cap,
                            "reentry_cooldown_minutes": 5,
                            "new_entry_cutoff_time": "14:30:00",
                            "leg_quantity_each": 10,
                        }
                    }
                }
            },
        }

    policy_dir.mkdir(parents=True)
    (policy_dir / f"widget_auto_trade_policy_{target_date}.json").write_text(
        json.dumps(policy(target_date, cap=1)), encoding="utf-8"
    )
    (policy_dir / f"widget_auto_trade_policy_{effective_date}.json").write_text(
        json.dumps(policy(effective_date, cap=2)), encoding="utf-8"
    )

    guard = _same_stage_owner_guard(
        target_date=target_date,
        low_price_candidate_dir=tmp_path / "low-price",
        samsung_candidate_dir=tmp_path / "samsung",
        widget_policy_dir=policy_dir,
    )

    assert guard["mutation_present"] is True
    assert guard["owners"][0]["changed_scopes"] == ["005930|KRX_REGULAR"]


def test_malformed_next_widget_policy_fails_closed(tmp_path: Path) -> None:
    policy_dir = tmp_path / "widget-policy"
    target_date = date(2026, 8, 27)
    effective_date = date(2026, 8, 28)
    policy_dir.mkdir(parents=True)
    (policy_dir / f"widget_auto_trade_policy_{effective_date}.json").write_text(
        "{malformed", encoding="utf-8"
    )

    guard = _same_stage_owner_guard(
        target_date=target_date,
        low_price_candidate_dir=tmp_path / "low-price",
        samsung_candidate_dir=tmp_path / "samsung",
        widget_policy_dir=policy_dir,
    )

    assert guard["mutation_present"] is True
    assert guard["owners"] == [
        {
            "path": str(policy_dir / f"widget_auto_trade_policy_{effective_date}.json"),
            "schema": None,
            "policy_mutation_count": 0,
            "reason": "next_exact_date_widget_entry_contract_invalid",
        }
    ]
