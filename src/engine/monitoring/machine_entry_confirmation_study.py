"""Same-population causal feature ablations; never a policy selection owner."""

from __future__ import annotations

from collections import Counter
from datetime import date
import math
import statistics
from typing import Any, Callable

from src.trading.market.confirmation_window import FEATURE_VERSION
from src.trading.market.micro_confirmation import (
    _checkpoint_status,
    build_dynamic_micro_confirmation_checkpoints,
    dynamic_policy_for_scope,
)

ARMS = ("baseline", "bid_rebound", "depletion_flow", "combined")


def _decisions(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    policy = dynamic_policy_for_scope(
        owner=str(row.get("owner") or ""),
        scope_id=str(row.get("scope_id") or ""),
        symbol=str(row.get("symbol") or ""),
    )
    points = build_dynamic_micro_confirmation_checkpoints(
        anchor_bbo=row.get("entry_confirmation_bbo_anchor"),
        future_bbo=row.get("entry_confirmation_bbo_horizons"),
        checkpoint_ask_depletion=row.get("entry_confirmation_checkpoint_ask_depletion"),
        anchor_id=row.get("anchor_id"),
        signal_decision_at=row.get("anchor_at"),
        symbol=row.get("symbol"),
        expected_venues=row.get("expected_venues"),
        expected_session_buckets=row.get("expected_session_buckets"),
        owner=str(row.get("owner") or ""),
        baseline_fill_price=row.get("anchor_price"),
        owner_entry_limit_price=row.get("owner_entry_limit_price"),
        owner_target_price=row.get("owner_target_price"),
        round_trip_cost_pct=row.get("owner_round_trip_cost_pct"),
        widget_take_profit=(
            row.get("owner_outcome")
            if isinstance(row.get("owner_outcome"), dict)
            else {}
        ).get("exit_reason")
        == "take_profit_fill",
    )
    decisions = {}
    for arm in ARMS:
        observed = []
        for checkpoint in policy.checkpoints_sec:
            raw = points[checkpoint]
            point = _checkpoint_status(raw, checkpoint_sec=checkpoint, policy=policy)
            velocity = raw.get("best_ask_depletion_velocity_qty_per_sec")
            valid = (
                point["source_quality_eligible"]
                and raw.get("feature_version") == FEATURE_VERSION
                and isinstance(velocity, (int, float))
                and not isinstance(velocity, bool)
                and math.isfinite(velocity)
                and velocity >= 0
            )
            # All arms use identical source/cost/owner guards. They remove
            # feature groups only; no new tunable threshold or live axis.
            action = "WAIT"
            if valid:
                bid_support = (
                    point["bid_return_bps"] >= policy.minimum_bid_return_bps
                    or point["bid_recovery_from_low_bps"]
                    >= policy.minimum_rebound_from_low_bps
                )
                bid_adverse = (
                    point["bid_return_bps"] <= policy.adverse_bid_return_bps
                    and point["bid_recovery_from_low_bps"]
                    < policy.minimum_rebound_from_low_bps
                )
                flow_support = (
                    velocity > 0
                    and point["aggressive_buy_trade_backed_ratio"]
                    >= policy.minimum_trade_backed_ratio
                    and point["refill_ratio"] < policy.maximum_supportive_refill_ratio
                )
                flow_adverse = point["refill_ratio"] >= policy.adverse_refill_ratio
                adverse = (arm in {"bid_rebound", "combined"} and bid_adverse) or (
                    arm in {"depletion_flow", "combined"} and flow_adverse
                )
                support = (
                    arm == "baseline"
                    or (arm == "bid_rebound" and bid_support)
                    or (arm == "depletion_flow" and flow_support)
                    or (arm == "combined" and bid_support and flow_support)
                )
                if arm == "baseline":
                    action = "ENTER"
                elif adverse:
                    action = "REJECT"
                elif (
                    support
                    and point["net_edge_after_cost_bps"] > 0
                    and point["owner_price_feasible"] is True
                ):
                    action = "ENTER"
            observed.append({**point, "action": action, "study_source_eligible": valid})
            if action in {"ENTER", "REJECT"}:
                break
            if arm == "baseline" or checkpoint == policy.checkpoints_sec[-1]:
                action = (
                    "REJECT"
                    if all(p["study_source_eligible"] for p in observed)
                    else "INSUFFICIENT_DATA"
                )
                observed[-1]["action"] = action
                break
        eligible = (
            action != "INSUFFICIENT_DATA" and observed[-1]["study_source_eligible"]
        )
        decisions[arm] = {
            "terminal_action": action,
            "selected_delay_sec": (
                observed[-1]["checkpoint_sec"] if action == "ENTER" else None
            ),
            "checkpoint_decisions": observed,
            "source_quality_status": "eligible" if eligible else "source_gap",
        }
    return decisions


def build_study(
    *,
    cohort_rows: list[tuple[date, dict[str, Any]]],
    economic_observer: Callable[..., dict[str, Any] | None],
) -> dict[str, Any]:
    """Pair all four arms before aggregating; hold out the latest source date.

    Real fills provide the baseline only. Alternate entries/exits remain
    cost-modeled counterfactuals, and unfilled/missing outcomes are not zero.
    """
    identities = Counter(
        (day, str(row.get("lifecycle_id") or "")) for day, row in cohort_rows
    )
    paired = []
    gaps = Counter()
    traces = []
    for day, row in cohort_rows:
        identity = (day, str(row.get("lifecycle_id") or ""))
        if not identity[1] or identities[identity] != 1:
            gaps["missing_or_duplicate_lifecycle"] += 1
            continue
        decisions = _decisions(row)
        observations = {}
        for arm, decision in decisions.items():
            observation = (
                economic_observer(source_date=day, row=row, replay=decision)
                if decision["source_quality_status"] == "eligible"
                else None
            )
            if observation is None:
                gaps[f"{arm}:source_or_executable_outcome_gap"] += 1
            observations[arm] = observation
        complete = all(value is not None for value in observations.values())
        traces.append(
            {
                "source_date": day.isoformat(),
                "anchor_id": row.get("anchor_id"),
                "lifecycle_id": identity[1],
                "common_economic_pair": complete,
                "arms": {
                    arm: {
                        key: value[key]
                        for key in (
                            "terminal_action",
                            "selected_delay_sec",
                            "source_quality_status",
                        )
                    }
                    for arm, value in decisions.items()
                },
            }
        )
        if complete:
            paired.append((day, observations))
    days = sorted({day for day, _ in cohort_rows})
    holdout_day = days[-1] if len(days) >= 2 else None
    outcome_census = Counter()
    for _, row in cohort_rows:
        outcome = row.get("owner_outcome")
        outcome = outcome if isinstance(outcome, dict) else {}

        def quantity(value):
            return (
                value
                if isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value >= 0
                else None
            )

        purchased = quantity(outcome.get("purchased_quantity"))
        residual = quantity(outcome.get("right_censored_residual_quantity"))
        filled = (
            purchased if purchased is not None else quantity(outcome.get("quantity"))
        )
        if row.get("actual_order_submitted") is not True:
            outcome_census["not_submitted_or_unknown"] += 1
        elif outcome.get("entry_fill_status") == "unfilled" or purchased == 0:
            outcome_census["submitted_unfilled"] += 1
        elif residual is not None and residual > 0:
            outcome_census[
                (
                    "held_partial_fill_or_partial_exit"
                    if outcome.get("realization_scope")
                    == "partial_manual_exit_cashflow"
                    or filled != row.get("owner_requested_quantity")
                    else "held_full_entry_fill"
                )
            ] += 1
        elif outcome.get("realized") is not True:
            outcome_census[
                (
                    "filled_terminal_unknown"
                    if filled is not None and filled > 0
                    else "submitted_fill_and_terminal_unknown"
                )
            ] += 1
        elif outcome.get("quantity") != row.get("owner_requested_quantity"):
            outcome_census["realized_partial_or_quantity_unreconciled"] += 1
        else:
            outcome_census["realized_full_quantity_cost_validation_separate"] += 1

    def aggregate(rows: list[tuple[date, dict[str, Any]]], arm: str) -> dict[str, Any]:
        values = [observations[arm] for _, observations in rows]
        net = [value["candidate_net_pct"] for value in values]
        profit = sum(value["candidate_modeled_net_profit_krw"] for value in values)
        capital = sum(value["candidate_capital_krw_minutes"] for value in values)
        baseline_profit = sum(
            value["baseline_modeled_net_profit_krw"] for value in values
        )
        ordered = sorted(net)
        return {
            "paired_count": len(values),
            "net_ev_pct": statistics.mean(net) if net else None,
            "p10_net_pct": ordered[int((len(ordered) - 1) * 0.1)] if ordered else None,
            "modeled_net_profit_krw": profit if values else None,
            "modeled_profit_uplift_krw": profit - baseline_profit if values else None,
            "capital_krw_minutes": capital if values else None,
            "net_profit_per_capital_minute_pct": (
                profit / capital * 100 if capital > 0 else None
            ),
            "entry_count": sum(value["terminal_action"] == "ENTER" for value in values),
            "rejected_positive_baseline_count": sum(
                value["terminal_action"] == "REJECT" and value["baseline_net_pct"] > 0
                for value in values
            ),
            "negative_entry_count": sum(
                value["terminal_action"] == "ENTER" and value["candidate_net_pct"] < 0
                for value in values
            ),
        }

    return {
        "schema": "machine_entry_confirmation_four_arm_study_v1",
        "feature_version": FEATURE_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
        "actual_order_submitted": False,
        "decision": "research_only_no_policy_selection",
        "input_signal_count": len(cohort_rows),
        "actual_submitted_signal_count": sum(
            row.get("actual_order_submitted") is True for _, row in cohort_rows
        ),
        "not_submitted_or_unknown_signal_count": sum(
            row.get("actual_order_submitted") is not True for _, row in cohort_rows
        ),
        "common_paired_count": len(paired),
        "gap_counts": dict(sorted(gaps.items())),
        "outcome_census": dict(sorted(outcome_census.items())),
        "holdout_date": holdout_day.isoformat() if holdout_day else None,
        "holdout_policy": "latest_source_day_not_chosen_by_outcome_no_arm_optimization",
        "arms": {
            arm: {
                "all": aggregate(paired, arm),
                "training": aggregate(
                    [
                        (day, obs)
                        for day, obs in paired
                        if holdout_day is not None and day < holdout_day
                    ],
                    arm,
                ),
                "holdout": aggregate(
                    [(day, obs) for day, obs in paired if day == holdout_day], arm
                ),
            }
            for arm in ARMS
        },
        "traces": traces,
        "limitations": [
            "counterfactual_entries_are_not_real_broker_fill_quality",
            "unsubmitted_and_partial_or_open_outcomes_excluded_from_economics_not_zero",
            "velocity_positive_is_observed_depletion_not_an_optimized_speed_threshold",
        ],
    }
