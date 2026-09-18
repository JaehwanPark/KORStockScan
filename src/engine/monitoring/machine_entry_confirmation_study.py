"""Confirmation ablations and native-owner economics for the timing owner."""

from __future__ import annotations

from collections import Counter
from datetime import date
import math
import json
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
                    (arm != "depletion_flow" or velocity > 0)
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


# Operating comparisons deliberately live beside the existing four-arm study.
# They never promote the 300s diagnostic terminal into a live exit.
OPERATING_SCHEMA = "machine_confirmation_operating_v1"
OPERATING_ADAPTER_VERSION = (
    "native_full_fill_market_depth_weighted_target_widget_three_leg_v3"
)
OPERATING_OWNER = "machine_entry_timing_tuning"
OPERATING_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "next_preopen_existing_confirmation",
    "window_policy": "model_calibration_model_holdout_candidate_calibration_candidate_holdout",
    "sample_floor": "existing_machine_timing_dynamic_floors_per_exact_scope",
    "primary_decision_metric": "cost_adjusted_paired_ev_lower_envelope",
    "source_quality_gate": "frozen_owner_plan_cost_exit_ordered_depth_and_independent_model",
    "forbidden_uses": [
        "actual_profit_from_cf",
        "synthetic_horizon_exit",
        "quantity_or_guard_change",
    ],
}


def _seal(value):
    from src.engine.monitoring.policy_research_economics import digest

    body = {k: v for k, v in value.items() if k != "sha256"}
    return {**body, "sha256": digest(body)}


def _sealed(value):
    from src.engine.monitoring.policy_research_economics import digest

    try:
        return isinstance(value, dict) and value.get("sha256") == digest(
            {k: v for k, v in value.items() if k != "sha256"}
        )
    except (TypeError, ValueError):
        return False


def freeze_episode_plan(state, policy, *, owner, scope_id, now):
    """Freeze only a native, not-yet-submitted Samsung two-leg limit plan.

    The order envelope is not an allocation authority. This producer reads no
    broker/API and never changes the native plan, guard or custody.
    """
    from dataclasses import asdict
    from src.engine.trade_profit import get_trade_cost_rate
    from src.trading.market.micro_confirmation import SAMSUNG_CONFIRMATION_SCOPES
    from src.trading.order.episode_quantity import validate_owned_leg_quantity
    from src.engine.monitoring.policy_research_economics import digest
    from datetime import datetime, timedelta

    try:
        if (
            owner != "episode"
            or policy.symbol != "005930"
            or scope_id not in SAMSUNG_CONFIRMATION_SCOPES
        ):
            return None
        features = state.get("signal_features") or {}
        if state.get("timing_native_live_eligible") is not True:
            raise ValueError("native_live_owner_authority_not_confirmed")
        receipt = features.get("new_entry_quantity_receipt") or {}
        if (
            receipt.get("effective_date") != now.date().isoformat()
            or receipt.get("existing_owned_quantities_preserved") is not True
        ):
            raise ValueError("native_quantity_authority_receipt_missing")
        legs = state.get("legs") or []
        stamp = datetime.fromisoformat(
            features.get("signal_decision_at") or now.isoformat()
        )
        bar_id = str(features.get("signal_bar") or state.get("signal_bar"))
        bar = (
            datetime.strptime(bar_id, "%Y%m%d%H%M%S").replace(tzinfo=stamp.tzinfo)
            if len(bar_id) == 14 and bar_id.isdigit()
            else datetime.fromisoformat(bar_id)
        )
        if (
            stamp.utcoffset() is None
            or bar.utcoffset() is None
            or state.get("trade_date") != stamp.date().isoformat()
        ):
            raise ValueError("native_signal_time_missing")
        if not legs or any(
            l.get("buy_order_no") or l.get("buy_filled_qty") for l in legs
        ):
            return None
        plan = [
            {
                "leg_id": str(l["leg_id"]),
                "route": str(
                    l.get("route")
                    or getattr(policy, "route", features.get("route", ""))
                ),
                "quantity": validate_owned_leg_quantity(l["quantity"]),
                "limit_price": int(l["entry_price"]),
            }
            for l in legs
        ]
        if any(l["quantity"] != receipt.get("effective_leg_quantity") for l in plan):
            raise ValueError("native_quantity_authority_plan_mismatch")
        if any(
            l["limit_price"] <= 0 or l["route"] not in {"NXT", "SOR", "KRX"}
            for l in plan
        ):
            raise ValueError("native_plan_invalid")
        serialized = json.loads(
            json.dumps(asdict(policy), default=lambda x: x.isoformat())
        )
        validity = features.get(
            "entry_valid_completed_bars",
            getattr(policy, "entry_valid_completed_bars", None),
        )
        if type(validity) is not int or validity <= 0:
            if scope_id != "morning":
                raise ValueError("native_cancel_contract_missing")
            route = features.get("route") or plan[0]["route"]
            window = policy.nxt if route == "NXT" else policy.sor
            expiry = datetime.combine(
                stamp.date(), window.deadline, tzinfo=stamp.tzinfo
            )
        else:
            expiry = bar + timedelta(minutes=validity + 1)
        provenance = features.get("entry_timing_policy_provenance") or {}
        mode = provenance.get("entry_confirmation_mode", "fixed_delay")
        incumbent = (
            provenance.get("confirmation_feature_arm", "combined")
            if mode == "per_signal_dynamic_0_1_3_5"
            else "baseline"
        )
        if mode == "fixed_delay" and features.get("entry_confirmation_delay_sec", 0):
            raise ValueError("fixed_delay_incumbent_not_in_four_arm_scope")
        result = dict(
            schema=OPERATING_SCHEMA,
            owner=owner,
            scope_id=scope_id,
            symbol="005930",
            operating_adapter_version=OPERATING_ADAPTER_VERSION,
            native_policy_type=type(policy).__module__
            + "."
            + type(policy).__qualname__,
            source_date=stamp.date().isoformat(),
            decision_at=stamp.isoformat(),
            signal_bar=bar_id,
            plan=plan,
            total_quantity=sum(l["quantity"] for l in plan),
            native_policy=serialized,
            native_policy_sha256=digest(serialized),
            native_owner_code_sha256=frozen_native_owner_code(),
            target_ticks=int(policy.target_ticks),
            target_bps=None,
            entry_kind="limit",
            selected_programs=selected_exit_programs(
                now=now,
                owner=owner,
                adaptive_required=bool(state.get("timing_adaptive_services_present")),
            ),
            cancel_at=expiry.isoformat(),
            cancel_basis="native_completed_bar_validity_no_halt_or_session_rollover",
            cost_rate=get_trade_cost_rate(),
            cost_contract=frozen_operating_cost_contract(),
            cost_provenance="frozen_loaded_trade_profit_configuration_not_broker_settlement",
            exit_contract="native_target_until_guard_no_synthetic_terminal",
            incumbent_arm=incumbent,
            allocation_budget_krw=None,
            allocation_role="native_quantity_order_envelope_only",
            order_envelope_krw=sum(l["quantity"] * l["limit_price"] for l in plan),
            quantity_authority=features.get("new_entry_quantity_receipt"),
            runtime_effect=False,
            broker_order_forbidden=True,
            requires_native_guard_admission=True,
        )
        # Existing/selected supplemental exit behavior cannot be silently replaced.
        from src.trading.order.adaptive_exit.owner_loop import SESSION_KEY

        if any(SESSION_KEY in l for l in legs):
            raise ValueError("supplemental_exit_owner_adapter_required")
        return _seal(result)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return _seal(
            dict(
                schema=OPERATING_SCHEMA,
                status="source_gap",
                source_date=now.date().isoformat(),
                decision_at=now.isoformat(),
                signal_bar=(state.get("signal_features") or {}).get("signal_bar"),
                symbol="005930",
                scope_id=scope_id,
                blocker=str(exc),
                owner=owner,
                repair_owner=OPERATING_OWNER,
                plan=state.get("legs") or [],
                route=(state.get("signal_features") or {}).get("route")
                or getattr(policy, "route", "SOR"),
                closure_test="native unsubmitted plan with frozen date/cancel/cost/exit/quantity receipt",
            )
        )


def project_operating_source(contract, depth_rows, *, guard_path=None, actual=None):
    """Projection of the existing normalized 0D path; never a second collector.

    A native exit owner must certify the guard path. An unknown guard is not
    assumed absent. Sparse first-hit labels cannot manufacture an ordered path.
    """
    from datetime import datetime
    from src.engine.scalping.micro_reversion.depth_join import (
        validate_depth_row as validate_canonical_depth_row,
    )

    points = []
    errors = []
    for raw in depth_rows:
        try:
            validate_canonical_depth_row(raw)
            at = datetime.fromisoformat(raw["local_receive_timestamp"])
            if at.utcoffset() is None:
                raise ValueError("naive_depth_time")
            points.append(
                dict(
                    at=at.isoformat(),
                    symbol=raw["symbol"],
                    venue=raw["venue"],
                    session=raw["session_bucket"],
                    epoch=raw["sequence_epoch"],
                    sequence=raw["source_sequence"],
                    bid_levels=[[p, q] for _, p, q in raw["bid_levels"]],
                    ask_levels=[[p, q] for _, p, q in raw["ask_levels"]],
                    item=raw.get("item"),
                    series_sequence=raw.get("series_sequence", raw["source_sequence"]),
                    source_sha256=_seal(raw)["sha256"],
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(str(exc))
    return _seal(
        dict(
            schema=OPERATING_SCHEMA,
            contract=contract,
            points=points,
            projection_errors=errors,
            guard_path=guard_path,
            actual=actual,
            runtime_effect=False,
            broker_order_forbidden=True,
        )
    )


def replay_operating_plan(source, decision, model):
    """Native limit entries and tick targets on fresh ordered depth.

    No SELL from another path and no end-of-window liquidation. Model parameters
    must have independently validated owner witnesses before policy selection.
    """
    from datetime import datetime, timedelta
    from src.engine.monitoring.policy_research_economics import digest
    from src.trading.order.tick_utils import move_price_by_ticks

    result = dict(
        status="source_gap",
        blocker=None,
        net_pnl_krw=None,
        net_ev_pct=None,
        owner=OPERATING_OWNER,
        closure_test="ordered native owner plan/depth/guard/cost plus independent execution-model witnesses",
        actual_broker_profit=False,
        transitions=[],
    )
    try:
        if (
            not _sealed(source)
            or not _sealed(source.get("contract"))
            or source.get("projection_errors")
        ):
            raise ValueError("operating_source_integrity_invalid")
        c = source["contract"]
        if c.get("status") == "source_gap":
            raise ValueError(c["blocker"])
        if c.get("operating_adapter_version") != OPERATING_ADAPTER_VERSION:
            result["status"] = "unsupported_scope"
            raise ValueError("operating_adapter_version_not_supported")
        if model.get("scope_sha256") is not None and model[
            "scope_sha256"
        ] != operating_scope(c):
            raise ValueError("execution_model_scope_mismatch")
        if c.get("exit_contract") != "native_target_until_guard_no_synthetic_terminal":
            result["status"] = "unsupported_scope"
            raise ValueError("operating_exit_adapter_not_supported")
        if c.get("symbol") != "005930" or c.get("owner") not in {"episode", "widget"}:
            result["status"] = "unsupported_scope"
            raise ValueError("owner_scope_not_supported")
        guard = source.get("guard_path")
        if not _sealed(guard) or guard.get("contract_sha256") != c["sha256"]:
            raise ValueError("native_guard_path_missing_or_unbound")
        if (
            isinstance(c.get("selected_programs"), dict)
            and c["selected_programs"].get("status") == "source_gap"
        ):
            raise ValueError(
                c["selected_programs"].get("blocker", "native_guard_program_source_gap")
            )
        if not isinstance(c.get("selected_programs"), dict) or c[
            "selected_programs"
        ].get("status") not in {
            "native_target_only",
            "native_target_with_selected_programs",
        }:
            result["status"] = "unsupported_scope"
            raise ValueError("selected_exit_program_requires_operating_adapter")
        if guard.get("selected_programs") != c["selected_programs"]:
            raise ValueError("native_guard_program_generation_mismatch")
        if guard.get("adapter") != "native_target_with_pinned_programs" or guard.get(
            "interventions"
        ):
            result["status"] = "unsupported_scope"
            raise ValueError("guard_exit_requires_owner_adapter")
        if (
            not _sealed(model)
            or model.get("contract") != "native_marketable_depth_then_target_v1"
        ):
            raise ValueError("execution_model_contract_missing")
        latency = model.get("submit_latency_ms")
        target_latency = model.get("target_ack_latency_ms")
        gap = model.get("maximum_depth_gap_ms")
        if (
            any(type(v) is not int or v < 0 for v in (latency, target_latency))
            or type(gap) is not int
            or gap <= 0
        ):
            raise ValueError("execution_model_clock_invalid")
        part = model.get("depth_participation")
        if type(part) not in (int, float) or not 0 < part <= 1:
            raise ValueError("execution_model_participation_invalid")
        if (
            not math.isfinite(c["cost_rate"])
            or not 0 <= c["cost_rate"] < 1
            or not _sealed(c.get("cost_contract"))
            or c["cost_contract"].get("rate") != c["cost_rate"]
            or c["cost_provenance"]
            != "frozen_loaded_trade_profit_configuration_not_broker_settlement"
        ):
            raise ValueError("frozen_cost_contract_invalid")
        start = datetime.fromisoformat(c["decision_at"])
        expiry = (
            datetime.fromisoformat(c["cancel_at"])
            if c.get("cancel_at")
            else datetime.max.replace(tzinfo=start.tzinfo)
        )
        if start.utcoffset() is None or expiry.utcoffset() is None or expiry <= start:
            raise ValueError("native_cancel_time_invalid")
        points = source["points"]
        prior = None
        epoch = None
        sequence = None
        for point in points:
            at = datetime.fromisoformat(point["at"])
            if (
                at.utcoffset() is None
                or at < start
                or (
                    prior and (at <= prior or (at - prior).total_seconds() * 1000 > gap)
                )
            ):
                raise ValueError("ordered_depth_clock_or_coverage_invalid")
            expected_session = (
                "NXT_PREMARKET"
                if c["plan"][0]["route"] == "NXT" and c["scope_id"] == "morning"
                else c.get(
                    "execution_depth_session", c.get("depth_session", "SOR_REGULAR")
                )
            )
            if point["session"] != expected_session:
                raise ValueError("ordered_depth_session_scope_invalid")
            if (
                point["symbol"] != c["symbol"]
                or (epoch is not None and point["epoch"] != epoch)
                or (sequence is not None and point["sequence"] <= sequence)
            ):
                raise ValueError("ordered_depth_identity_or_epoch_invalid")
            if point["venue"] != c.get(
                "execution_data_venue",
                c.get(
                    "market_data_venue",
                    "NXT" if c["plan"][0]["route"] == "NXT" else "SOR",
                ),
            ):
                raise ValueError("ordered_depth_route_scope_invalid")
            for side in ("bid_levels", "ask_levels"):
                levels = point[side]
                if not levels or any(
                    type(q) is not int or q < 0 or type(p) is not int or p <= 0
                    for p, q in levels
                ):
                    raise ValueError("ordered_depth_levels_invalid")
            if any(
                a[0] <= b[0]
                for a, b in zip(point["bid_levels"], point["bid_levels"][1:])
            ) or any(
                a[0] >= b[0]
                for a, b in zip(point["ask_levels"], point["ask_levels"][1:])
            ):
                raise ValueError("ordered_depth_rank_invalid")
            if point["bid_levels"][0][0] > point["ask_levels"][0][0]:
                raise ValueError("crossed_depth")
            prior = at
            epoch = point["epoch"]
            sequence = point["sequence"]
        if (
            not points
            or (datetime.fromisoformat(points[0]["at"]) - start).total_seconds() * 1000
            > gap
        ):
            raise ValueError("anchor_depth_missing")
        if guard.get("path_sha256") != digest(points):
            raise ValueError("guard_path_generation_mismatch")
        if decision.get("source_quality_status") != "eligible" or decision.get(
            "terminal_action"
        ) not in {"ENTER", "REJECT"}:
            raise ValueError("confirmation_source_not_eligible")
        zero = dict(
            net_pnl_krw=0.0,
            net_ev_pct=0.0,
            capital_krw_minutes=0.0,
            reserve_krw_minutes=0.0,
            fill_participation=0.0,
            exposure_start=None,
            exposure_end=None,
        )
        if decision["terminal_action"] == "REJECT":
            return dict(result, **zero, status="completed", blocker=None)
        delay = decision.get("selected_delay_sec")
        if type(delay) is not int or delay not in (0, 1, 3, 5):
            raise ValueError("confirmation_checkpoint_invalid")
        due = start + timedelta(seconds=delay, milliseconds=latency)
        admission = guard.get("entry_admission")
        if c.get("requires_native_guard_admission"):
            if not isinstance(admission, dict):
                raise ValueError("native_common_entry_admission_missing")
            admitted_at = datetime.fromisoformat(admission["at"])
            if admitted_at.utcoffset() is None or admitted_at < start:
                raise ValueError("native_common_entry_admission_clock_invalid")
            if admission.get("permitted") is not True:
                return dict(
                    result,
                    **zero,
                    status="completed",
                    blocker=None,
                    reason="shared_native_hard_entry_guard_block",
                )
            due = max(due, admitted_at + timedelta(milliseconds=latency))
        if c["owner"] == "widget":
            if len(c["plan"]) > 1 and not guard.get("scale_ticks"):
                raise ValueError("widget_scale_opportunity_timeline_missing")
            return _replay_widget_plan(
                result, c, points, guard, due, model, source=source
            )
        legs = [dict(l, left=l["quantity"], lots=[]) for l in c["plan"]]
        if sum(l["quantity"] for l in legs) != c["total_quantity"] or len(
            {l["leg_id"] for l in legs}
        ) != len(legs):
            raise ValueError("frozen_quantity_or_leg_identity_invalid")
        reserve = capital = buy = sell = filled = 0.0
        first = None
        last = None
        prev_at = start
        programs = _OperatingPrograms(source, model)
        programs.events = result["transitions"]
        for point in points:
            at = datetime.fromisoformat(point["at"])
            dt = (at - prev_at).total_seconds() / 60
            capital += sum(q * p for l in legs for q, p, _, _ in l["lots"]) * dt
            reserve += sum(l["left"] * l["limit_price"] for l in legs) * max(
                0, (min(at, expiry) - max(prev_at, due)).total_seconds() / 60
            )
            bids = [[p, math.floor(q * part)] for p, q in point["bid_levels"]]
            asks = [[p, math.floor(q * part)] for p, q in point["ask_levels"]]
            programs.update(at)
            # One quote's depth is shared by all native legs; no duplicated book.
            for leg in legs:
                for lot in leg["lots"]:
                    q, p, ack, target = lot
                    if not q:
                        continue
                    if at < ack:
                        continue
                    target = programs.target(
                        leg["leg_id"],
                        at=at,
                        quantity=q,
                        entry=p,
                        target=target,
                        route=leg["route"],
                    )
                    lot[3] = target
                    if not programs.fill_ready(
                        leg["leg_id"], at=at, target=target, bids=bids, quantity=q
                    ):
                        continue
                    for level in bids:
                        if level[0] < target:
                            break
                        take = min(lot[0], level[1])
                        lot[0] -= take
                        level[1] -= take
                        sell += take * target
                        if take:
                            result["transitions"].append(
                                dict(
                                    at=at.isoformat(),
                                    action="target",
                                    leg_id=leg["leg_id"],
                                    quantity=take,
                                    price=target,
                                )
                            )
                if due <= at < expiry and leg["left"]:
                    marketable = [
                        level for level in asks if level[0] <= leg["limit_price"]
                    ]
                    available = sum(level[1] for level in marketable)
                    if 0 < available < leg["left"]:
                        return dict(
                            result,
                            status="unsupported_scope",
                            blocker="partial_buy_requires_independently_validated_cancel_model",
                        )
                    if available >= leg["left"]:
                        quantity = leg["left"]
                        notional = 0
                        for level in marketable:
                            take = min(leg["left"], level[1])
                            leg["left"] -= take
                            level[1] -= take
                            notional += take * level[0]
                            if not leg["left"]:
                                break
                        price = notional / quantity
                        # Native target uses the weighted BUY basis, once the
                        # BUY remainder has reached its own terminal state.
                        from src.trading.order.tick_utils import clamp_price_to_tick

                        target_basis = clamp_price_to_tick(price)
                        buy += notional
                        filled += quantity
                        first = first or at
                        leg["lots"].append(
                            [
                                quantity,
                                price,
                                at + timedelta(milliseconds=target_latency),
                                _native_target_price(c, target_basis),
                            ]
                        )
                        result["transitions"].append(
                            dict(
                                at=at.isoformat(),
                                action="buy",
                                leg_id=leg["leg_id"],
                                quantity=quantity,
                                price=price,
                            )
                        )
            prev_at = at
            open_qty = sum(q for l in legs for q, _, _, _ in l["lots"])
            if at >= expiry and any(l["left"] for l in legs):
                return dict(
                    result,
                    status="unsupported_scope",
                    blocker="unfilled_buy_requires_independently_validated_cancel_model",
                )
            if open_qty == 0 and all(l["left"] == 0 for l in legs):
                last = at
                break
        open_qty = sum(q for l in legs for q, _, _, _ in l["lots"])
        if open_qty or any(l["left"] for l in legs) and prev_at < expiry:
            return dict(
                result,
                status="source_gap" if source.get("source_truncated") else "pending",
                blocker="native_target_or_cancel_terminal_pending",
                modeled_filled_qty=filled,
                remaining_qty=open_qty,
            )
        pnl = sell * (1 - c["cost_rate"]) - buy
        denominator = c["order_envelope_krw"]
        if not math.isfinite(denominator) or denominator <= 0:
            raise ValueError("native_order_envelope_invalid")
        return dict(
            result,
            status="completed",
            blocker=None,
            net_pnl_krw=pnl,
            net_ev_pct=pnl / denominator * 100,
            capital_krw_minutes=capital,
            reserve_krw_minutes=reserve,
            fill_participation=filled / c["total_quantity"],
            exposure_start=start.isoformat(),
            exposure_end=(last or prev_at).isoformat(),
            modeled_filled_qty=filled,
            remaining_qty=0,
            buy_notional_krw=buy,
            sell_notional_krw=sell,
            cost_krw=sell * c["cost_rate"],
            cost_provenance=c["cost_provenance"],
            contract_sha256=c["sha256"],
            model_sha256=model["sha256"],
        )
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return dict(result, blocker=str(exc))


def operating_scope(contract):
    from src.engine.monitoring.policy_research_economics import digest

    return digest(
        {
            k: contract.get(k)
            for k in (
                "owner",
                "scope_id",
                "symbol",
                "operating_adapter_version",
                "native_policy_type",
                "native_owner_code_sha256",
                "target_ticks",
                "target_bps",
                "entry_kind",
                "selected_programs",
                "market_data_venue",
                "execution_data_venue",
                "execution_depth_session",
                "depth_session",
                "cost_rate",
                "cost_contract",
                "cost_provenance",
                "exit_contract",
                "total_quantity",
            )
        }
        | {
            "semantic_native_policy": semantic_native_policy(
                contract.get("native_policy") or {}
            ),
            "leg_shapes": [
                {k: l[k] for k in ("leg_id", "route", "quantity")}
                for l in contract.get("plan", [])
            ],
        }
    )


def native_guard_projection(contract, points, *, native_state):
    """Only the native target-only program can certify this supported subset.

    Selected supplemental programs and manual interventions retain their owner;
    they cannot acquire a target-only certificate from a terminal receipt.
    """
    from src.engine.monitoring.policy_research_economics import digest
    from src.trading.order.adaptive_exit.owner_loop import SESSION_KEY

    legs = native_state.get("legs", [])
    widget_state = native_state.get("widget_state") or {}
    interventions = [k for k in ("adaptive_exit_session",) if widget_state.get(k)]
    if native_state.get("post_admission_veto"):
        interventions.append(native_state["post_admission_veto"])

    for leg in legs:
        if any(
            k in leg
            for k in (
                SESSION_KEY,
                "manual_exit_receipt",
                "manual_exit_reconciliation",
            )
        ):
            interventions.append(str(leg.get("leg_id")))
    return _seal(
        dict(
            adapter="native_target_with_pinned_programs",
            contract_sha256=contract.get("sha256"),
            path_sha256=digest(points),
            interventions=interventions,
            selected_programs=contract.get("selected_programs"),
            programme_ticks=native_state.get("programme_ticks", []),
            programme_source_overflow=native_state.get(
                "programme_source_overflow", False
            ),
            entry_admission=native_state.get("entry_admission"),
            scale_ticks=native_state.get("scale_ticks", []),
            scale_source_overflow=native_state.get("scale_source_overflow", False),
            native_state_sha256=digest(native_state),
            applied_policy_hash=(
                native_state.get("confirmation_policy_provenance") or {}
            ).get("policy_hash"),
            owner="native_episode_target_owner",
        )
    )


def model_witness(source, replay):
    """Compare modeled results with exact native-order priced terminal evidence."""
    actual = source.get("actual") or {}
    c = source.get("contract") or {}
    if not _sealed(actual) or replay.get("status") != "completed":
        return None
    if (
        actual.get("status") != "COMPLETED"
        or actual.get("origin") != "real"
        or actual.get("contract_sha256") != c.get("sha256")
        or actual.get("exact_lineage") is not True
        or actual.get("quantity") != c.get("total_quantity")
        or actual.get("cost_provenance") != c.get("cost_provenance")
    ):
        return None
    for k in (
        "net_pnl_krw",
        "capital_krw_minutes",
        "reserve_krw_minutes",
        "filled_quantity",
        "closed_at_ms",
    ):
        if type(actual.get(k)) not in (int, float) or not math.isfinite(actual[k]):
            return None
    from datetime import datetime

    end = replay.get("exposure_end")
    if not end:
        return None
    return dict(
        source_sha256=source["sha256"],
        source_date=c["source_date"],
        scope_sha256=operating_scope(c),
        quantity_error=replay["modeled_filled_qty"] - actual["filled_quantity"],
        net_error_budget_pct=(replay["net_pnl_krw"] - actual["net_pnl_krw"])
        / c["order_envelope_krw"]
        * 100,
        capital_error_minutes=(
            replay["capital_krw_minutes"] - actual["capital_krw_minutes"]
        )
        / c["order_envelope_krw"],
        reserve_error_minutes=(
            replay["reserve_krw_minutes"] - actual["reserve_krw_minutes"]
        )
        / c["order_envelope_krw"],
        receipt_clock_error_sec=datetime.fromisoformat(end).timestamp()
        - actual["closed_at_ms"] / 1000,
    )


def fit_operating_model(cases):
    """Two disjoint chronological native witness dates, never candidate refits."""
    from src.trading.config.machine_entry_timing_policy import MIN_COMPLETED_OUTCOMES

    dates = sorted(
        {s["contract"]["source_date"] for s, _ in cases if _sealed(s.get("actual"))}
    )
    blocked = dict(
        status="insufficient_sample",
        blocker="independent_native_model_witness_floor",
        owner=OPERATING_OWNER,
        closure_test="priced exact-order model calibration and later independent holdout before candidate dates",
    )
    if len(dates) < 2:
        dispositions = Counter(
            s.get("actual_disposition", "source_gap")
            for s, _ in cases
            if not _sealed(s.get("actual"))
        )
        return dict(
            blocked,
            status=(
                "source_gap" if dispositions["source_gap"] else "insufficient_sample"
            ),
            actual_dispositions=dict(dispositions),
        )
    model_dates = []
    witness_count = 0
    for day in dates:
        model_dates.append(day)
        witness_count += sum(
            s["contract"]["source_date"] == day and _sealed(s.get("actual"))
            for s, _ in cases
        )
        if witness_count >= MIN_COMPLETED_OUTCOMES and len(model_dates) >= 2:
            break
    all_witness_dates = dates
    dates = model_dates
    cut = max(1, len(dates) // 2)
    # Extend the chronological MODEL prefix when a new native action gains a
    # later independent witness. The frozen first target-only proof must not
    # permanently prevent newly measured action scopes from becoming usable.
    action_dates = {
        k: sorted(
            {
                s["contract"]["source_date"]
                for s, _ in cases
                if _sealed(s.get("actual"))
                and type(s["actual"].get(k)) is int
                and s["actual"][k] >= 0
            }
        )
        for k in ("target_amend_latency_ms", "profit_replace_latency_ms")
    }
    supported = [ds for ds in action_dates.values() if len(ds) >= 2]
    if supported:
        cal_end = max(dates[cut - 1], *(ds[0] for ds in supported))
        later = [next((d for d in ds if d > cal_end), None) for ds in supported]
        if all(later):
            model_end = max(dates[-1], *later)
            dates = [d for d in all_witness_dates if d <= model_end]
            cut = sum(d <= cal_end for d in dates)
    calibration_dates = dates[:cut]
    model_holdout_dates = dates[cut:]
    calibration = [
        (s, d) for s, d in cases if s["contract"]["source_date"] in calibration_dates
    ]
    holdout = [
        (s, d) for s, d in cases if s["contract"]["source_date"] in model_holdout_dates
    ]
    observed = [s["actual"] for s, _ in calibration if _sealed(s.get("actual"))]
    if not observed:
        return dict(
            blocked,
            status="source_gap",
            blocker="native_execution_latency_receipts_missing",
        )
    if any(
        any(
            type(a.get(k)) is not int or a[k] < 0
            for k in (
                "submit_latency_ms",
                "target_ack_latency_ms",
                "maximum_depth_gap_ms",
            )
        )
        for a in observed
    ):
        return dict(
            blocked,
            status="source_gap",
            blocker="native_execution_clock_provenance_missing",
        )
    model = _seal(
        dict(
            contract="native_marketable_depth_then_target_v1",
            submit_latency_ms=max(a["submit_latency_ms"] for a in observed),
            target_ack_latency_ms=max(a["target_ack_latency_ms"] for a in observed),
            target_touch_latency_ms=max(
                (
                    a["target_touch_latency_ms"]
                    for a in observed
                    if type(a.get("target_touch_latency_ms")) is int
                ),
                default=None,
            ),
            maximum_depth_gap_ms=max(a["maximum_depth_gap_ms"] for a in observed),
            depth_participation=1.0,
            **{
                k: max((a[k] for a in observed if type(a.get(k)) is int), default=None)
                for k in (
                    "maximum_programme_tick_gap_ms",
                    "target_amend_latency_ms",
                    "profit_replace_latency_ms",
                )
            },
            parameter_basis="worst_observed_native_calibration_latency_and_full_marketable_depth_independently_tested",
            scope_sha256=operating_scope(calibration[0][0]["contract"]),
            target_cancel_latency_ms=max(
                (
                    a["target_cancel_latency_ms"]
                    for a in observed
                    if type(a.get("target_cancel_latency_ms")) is int
                ),
                default=None,
            ),
            scale_check_latency_ms=max(
                (
                    a["scale_check_latency_ms"]
                    for a in observed
                    if type(a.get("scale_check_latency_ms")) is int
                ),
                default=None,
            ),
            maximum_scale_tick_gap_ms=max(
                (
                    a["maximum_scale_tick_gap_ms"]
                    for a in observed
                    if type(a.get("maximum_scale_tick_gap_ms")) is int
                ),
                default=None,
            ),
        )
    )
    for k in ("target_amend_latency_ms", "profit_replace_latency_ms"):
        if not any(type((s.get("actual") or {}).get(k)) is int for s, _ in holdout):
            model[k] = None
    model = _seal(model)
    dimensions = (
        "quantity_error",
        "net_error_budget_pct",
        "capital_error_minutes",
        "reserve_error_minutes",
        "receipt_clock_error_sec",
    )
    witnesses = []
    for name, rows in (("calibration", calibration), ("model_holdout", holdout)):
        for source, decisions in rows:
            arm = source["contract"]["incumbent_arm"]
            witness = model_witness(
                source, replay_operating_plan(source, decisions[arm], model)
            )
            if witness:
                witnesses.append(dict(witness, partition=name))
    cal = [r for r in witnesses if r["partition"] == "calibration"]
    held = [r for r in witnesses if r["partition"] == "model_holdout"]
    if not cal or not held or len(witnesses) < MIN_COMPLETED_OUTCOMES:
        missing = Counter(
            s.get("actual_disposition", "source_gap")
            for s, _ in calibration + holdout
            if not _sealed(s.get("actual"))
        )
        return dict(
            blocked,
            status="source_gap" if missing["source_gap"] else "insufficient_sample",
            model=model,
            witnesses=witnesses,
            actual_dispositions=dict(missing),
        )
    coverage = {
        "calibration": len(cal) / len(calibration),
        "model_holdout": len(held) / len(holdout),
    }
    from src.trading.config.machine_entry_timing_policy import (
        DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT,
    )

    if any(
        v * 100 < DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT for v in coverage.values()
    ):
        return dict(
            blocked,
            status=(
                "pending"
                if any(
                    s.get("actual_disposition") == "pending"
                    for s, _ in calibration + holdout
                    if not _sealed(s.get("actual"))
                )
                else "source_gap"
            ),
            blocker="native_model_witness_coverage_below_floor",
            coverage=coverage,
        )
    tolerance = {k: max(abs(r[k]) for r in cal) for k in dimensions}
    if any(r["quantity_error"] != 0 for r in cal) or any(
        r["quantity_error"] != 0
        or any(abs(r[k]) > tolerance[k] + 1e-12 for k in dimensions)
        for r in held
    ):
        return dict(
            blocked,
            status="model_validation_failed",
            blocker="chronological_model_holdout_outside_empirical_tolerance",
            model=model,
            tolerance=tolerance,
            witnesses=witnesses,
        )
    return _seal(
        dict(
            status="validated",
            model=model,
            tolerance=tolerance,
            witnesses=witnesses,
            coverage=coverage,
            available_after_date=max(
                dates[-1],
                max(
                    s["actual"].get("knowledge_date", dates[-1])
                    for s, _ in calibration + holdout
                ),
            ),
            scope_sha256=model["scope_sha256"],
            net_error_envelope_pct=max(
                [0.0] + [r["net_error_budget_pct"] for r in held]
            ),
            calibration_dates=calibration_dates,
            model_holdout_dates=model_holdout_dates,
            model_profit_basis="broker_prices_with_frozen_owner_cost_model_not_settled_account_pnl",
        )
    )


def _operating_aggregate(rows, arm, incumbent, proof):
    if not rows:
        return dict(
            pair_count=0,
            net_ev_pct=None,
            net_pnl_krw=None,
            paired_delta_ev_pct=None,
            robust_lower_bound_pct=None,
        )
    values = [r["arms"][arm] for r in rows]
    base = [r["arms"][incumbent] for r in rows]
    notionals = [r["source"]["contract"]["order_envelope_krw"] for r in rows]
    total = sum(notionals)
    pnl = sum(v["net_pnl_krw"] for v in values)
    delta = [
        (v["net_pnl_krw"] - b["net_pnl_krw"]) / n * 100
        for v, b, n in zip(values, base, notionals)
    ]
    tails = sorted(v["net_ev_pct"] for v in values)
    # Error envelope is deducted on both arms. This is an observed lower
    # envelope, not a confidence interval or a guarantee about future returns.
    lower = min(delta) - 2 * max(
        proof["tolerance"]["net_error_budget_pct"], proof["net_error_envelope_pct"]
    )
    # Native latency stress is replayed, not inferred by subtracting gross EV.
    stressed = [r["stress_arms"][arm] for r in rows]
    stress_base = [r["stress_arms"][incumbent] for r in rows]
    if any(v["status"] != "completed" for v in stressed + stress_base):
        lower = None
    else:
        lower = min(
            lower,
            min(
                (v["net_pnl_krw"] - b["net_pnl_krw"]) / n * 100
                for v, b, n in zip(stressed, stress_base, notionals)
            )
            - 2 * proof["tolerance"]["net_error_budget_pct"],
        )
    return dict(
        pair_count=len(rows),
        net_ev_pct=pnl / total * 100,
        net_pnl_krw=pnl,
        paired_delta_ev_pct=sum(
            v["net_pnl_krw"] - b["net_pnl_krw"] for v, b in zip(values, base)
        )
        / total
        * 100,
        robust_lower_bound_pct=lower,
        p10_net_pct=tails[int((len(tails) - 1) * 0.1)],
        worst_net_pct=tails[0],
        capital_krw_minutes=sum(v["capital_krw_minutes"] for v in values),
        reserve_krw_minutes=sum(v["reserve_krw_minutes"] for v in values),
        fill_participation=statistics.mean(v["fill_participation"] for v in values),
    )


def operating_comparison(cases, *, target_date):
    """One exact owner scope; source gaps and censored arms remain denominators."""
    from datetime import date, datetime
    from src.trading.config.machine_entry_timing_policy import (
        DYNAMIC_MIN_OBSERVED_DAYS,
        DYNAMIC_MIN_UNIQUE_LIFECYCLES,
        DYNAMIC_MIN_COMPLETED_OUTCOMES,
        DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT,
        MIN_ABSOLUTE_EV_UPLIFT_PCT,
        MAX_P10_DETERIORATION_PCT,
    )

    result = dict(
        schema=OPERATING_SCHEMA,
        metric_contract=OPERATING_CONTRACT,
        status="source_gap",
        candidate=None,
        owner=OPERATING_OWNER,
        closure_test="native producer->projection->operating replay->chronological model/candidate holdouts->dated policy reader",
        input_count=len(cases),
        source_dispositions={},
        first_source_gaps=[
            dict(
                blocker=(s.get("contract") or {}).get(
                    "blocker", "native_operating_projection_integrity_invalid"
                ),
                repair_owner=(s.get("contract") or {}).get(
                    "repair_owner", OPERATING_OWNER
                ),
                closure_test=(s.get("contract") or {}).get(
                    "closure_test", "native frozen producer source and exact projection"
                ),
            )
            for s, _ in cases
            if not _sealed(s) or (s.get("contract") or {}).get("status") == "source_gap"
        ],
        model_validation=None,
        candidate_metrics={},
        actual_profit=None,
        primary_ev_pct=None,
        paired_delta_ev_pct=None,
        robust_delta_ev_lower_bound_pct=None,
    )
    valid = []
    dispositions = Counter()
    identities = {}
    conflicts = set()
    all_dates = Counter()
    for source, decisions in cases:
        c = source.get("contract") or {}
        if isinstance(c.get("source_date"), str):
            all_dates[c["source_date"]] += 1
        if not _sealed(source) or not _sealed(c) or c.get("status") == "source_gap":
            dispositions["source_gap"] += 1
            continue
        if c.get("symbol") != "005930":
            dispositions["unsupported_scope"] += 1
            continue
        day = c.get("source_date")
        try:
            if date.fromisoformat(
                day
            ).isoformat() != day or not "2026-06-05" <= day <= str(target_date):
                raise ValueError()
        except (ValueError, TypeError):
            dispositions["source_gap"] += 1
            continue
        key = c["sha256"]
        if key in identities:
            all_dates[day] -= 1
            if identities[key] != (source, decisions):
                conflicts.add(key)
            else:
                dispositions["duplicate_root_removed"] += 1
        identities[key] = (source, decisions)
    valid = [v for k, v in identities.items() if k not in conflicts]
    dispositions["identity_conflict"] += len(conflicts)
    if not valid:
        return dict(result, source_dispositions=dict(dispositions))
    unsupported = [
        s
        for s, _ in valid
        if (s["contract"].get("selected_programs") or {}).get("status")
        == "unsupported_scope"
    ]
    program_gaps = [
        s
        for s, _ in valid
        if (s["contract"].get("selected_programs") or {}).get("status") == "source_gap"
    ]
    if program_gaps and len(program_gaps) == len(valid):
        return dict(
            result,
            source_dispositions={"selected_exit_program_source_gap": len(program_gaps)},
        )
    if unsupported and len(unsupported) == len(valid):
        return dict(
            result,
            status="unsupported_scope",
            source_dispositions={
                "selected_exit_program_requires_operating_adapter": len(unsupported)
            },
        )
    if len({operating_scope(s["contract"]) for s, _ in valid}) != 1:
        latest = max(s["contract"]["source_date"] for s, _ in valid)
        latest_scopes = {
            operating_scope(s["contract"])
            for s, _ in valid
            if s["contract"]["source_date"] == latest
        }
        if len(latest_scopes) != 1:
            return dict(
                result,
                status="unsupported_scope",
                source_dispositions={
                    "conflicting_current_owner_policy_scope": len(valid)
                },
            )
        current_scope = next(iter(latest_scopes))
        kept = [
            (s, d) for s, d in valid if operating_scope(s["contract"]) == current_scope
        ]
        dispositions["different_frozen_operating_scope"] += len(valid) - len(kept)
        valid = kept
        for source, decisions in identities.values():
            if operating_scope(source["contract"]) != current_scope:
                all_dates[source["contract"]["source_date"]] -= 1
        all_dates = Counter({day: n for day, n in all_dates.items() if n > 0})
    proof = fit_operating_model(valid)
    result["model_validation"] = proof
    if proof["status"] != "validated":
        return dict(
            result, status=proof["status"], source_dispositions=dict(dispositions)
        )
    incumbent = max(valid, key=lambda row: row[0]["contract"]["source_date"])[0][
        "contract"
    ]["incumbent_arm"]
    after = [
        (s, d)
        for s, d in valid
        if s["contract"]["source_date"] > proof["available_after_date"]
    ]
    paired = []
    by_day = Counter(
        {day: n for day, n in all_dates.items() if day > proof["available_after_date"]}
    )
    stress_model = _seal(
        {k: v for k, v in proof["model"].items() if k != "sha256"}
        | {
            "submit_latency_ms": proof["model"]["submit_latency_ms"]
            + int(math.ceil(proof["tolerance"]["receipt_clock_error_sec"] * 1000)),
            "target_ack_latency_ms": proof["model"]["target_ack_latency_ms"]
            + int(math.ceil(proof["tolerance"]["receipt_clock_error_sec"] * 1000)),
            **{
                k: proof["model"][k]
                + int(math.ceil(proof["tolerance"]["receipt_clock_error_sec"] * 1000))
                for k in (
                    "target_touch_latency_ms",
                    "target_amend_latency_ms",
                    "profit_replace_latency_ms",
                    "target_cancel_latency_ms",
                )
                if type(proof["model"].get(k)) is int
            },
        }
    )
    for source, decisions in after:
        day = source["contract"]["source_date"]
        arms = {
            a: replay_operating_plan(source, decisions.get(a, {}), proof["model"])
            for a in ARMS
        }
        failed = [v["status"] for v in arms.values() if v["status"] != "completed"]
        if failed:
            first = next(
                (
                    status
                    for status in ("source_gap", "unsupported_scope", "pending")
                    if status in failed
                ),
                failed[0],
            )
            dispositions[first] += 1
        if all(v["status"] == "completed" for v in arms.values()):
            paired.append(
                dict(
                    source=source,
                    day=day,
                    arms=arms,
                    stress_arms={
                        a: replay_operating_plan(source, decisions[a], stress_model)
                        for a in ARMS
                    },
                )
            )
    result.update(
        source_dispositions=dict(dispositions),
        model_validation=proof,
        paired_count=len(paired),
    )
    days = sorted(by_day)
    if len(days) < DYNAMIC_MIN_OBSERVED_DAYS or len(paired) < max(
        DYNAMIC_MIN_UNIQUE_LIFECYCLES, DYNAMIC_MIN_COMPLETED_OUTCOMES
    ):
        return dict(result, status="insufficient_sample")
    if any(
        sum(r["day"] == day for r in paired) / n * 100
        < DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT
        for day, n in by_day.items()
    ):
        return dict(
            result, status="pending" if dispositions["pending"] else "source_gap"
        )
    if dispositions["pending"]:
        # Unknown held/residual outcomes have no loss bound. A completed-only
        # tail cannot certify the entire opportunity population's lower EV.
        return dict(
            result, status="pending", blocker="unbounded_censored_native_outcome"
        )
    # All arms share the same admitted opportunity panel. Capital cannot be
    # reused by overlapping episodes even in independent owner comparisons.
    intervals = sorted(
        (
            datetime.fromisoformat(s["contract"]["decision_at"]),
            max(
                (
                    datetime.fromisoformat(r["arms"][a]["exposure_end"])
                    for a in ARMS
                    if r["arms"][a]["exposure_end"]
                ),
                default=datetime.fromisoformat(s["contract"]["decision_at"]),
            ),
        )
        for r in paired
        for s in [r["source"]]
    )
    if any(left[1] > right[0] for left, right in zip(intervals, intervals[1:])):
        return dict(
            result,
            status="unsupported_scope",
            capital_blocker="overlapping_owner_episodes_require_native_allocation_schedule",
        )
    hold = days[-1]
    cal = [r for r in paired if r["day"] < hold]
    held = [r for r in paired if r["day"] == hold]
    rolling = [r for r in paired if r["day"] in days[-5:]]
    metrics = {
        a: {
            "rolling": _operating_aggregate(rolling, a, incumbent, proof),
            "calibration": _operating_aggregate(cal, a, incumbent, proof),
            "holdout": _operating_aggregate(held, a, incumbent, proof),
            "cumulative": _operating_aggregate(paired, a, incumbent, proof),
        }
        for a in ARMS
    }
    result.update(
        candidate_metrics=metrics, candidate_holdout_date=hold, incumbent_arm=incumbent
    )
    qualified = [
        a
        for a in ARMS
        if a != incumbent
        and metrics[a]["calibration"]["robust_lower_bound_pct"] is not None
        and metrics[a]["calibration"]["robust_lower_bound_pct"]
        >= MIN_ABSOLUTE_EV_UPLIFT_PCT
        and metrics[a]["calibration"]["net_ev_pct"] > 0
        and metrics[a]["calibration"]["p10_net_pct"]
        >= metrics[incumbent]["calibration"]["p10_net_pct"] - MAX_P10_DETERIORATION_PCT
    ]
    if not qualified:
        return dict(
            result,
            status="valid_no_edge",
            primary_ev_pct=metrics[incumbent]["cumulative"]["net_ev_pct"],
        )
    selected = max(
        qualified,
        key=lambda a: (metrics[a]["calibration"]["robust_lower_bound_pct"], a),
    )
    h = metrics[selected]["holdout"]
    roll = metrics[selected]["rolling"]
    if (
        roll["robust_lower_bound_pct"] is None
        or roll["robust_lower_bound_pct"] < MIN_ABSOLUTE_EV_UPLIFT_PCT
        or roll["net_ev_pct"] <= 0
    ):
        return dict(
            result,
            status="rolling_validation_failed",
            calibration_selected_arm=selected,
        )
    if (
        h["robust_lower_bound_pct"] is None
        or h["robust_lower_bound_pct"] < MIN_ABSOLUTE_EV_UPLIFT_PCT
        or h["net_ev_pct"] <= 0
        or h["p10_net_pct"]
        < metrics[incumbent]["holdout"]["p10_net_pct"] - MAX_P10_DETERIORATION_PCT
    ):
        return dict(
            result, status="candidate_holdout_failed", calibration_selected_arm=selected
        )
    return _seal(
        dict(
            result,
            status="candidate_ready",
            candidate=selected,
            observed_dates=days,
            candidate_calibration_dates=days[:-1],
            paired_coverage_pct=len(paired) / sum(by_day.values()) * 100,
            source_case_hashes=[s["sha256"] for s, _ in valid],
            runtime_scope_contract=valid[0][0]["contract"],
            primary_ev_pct=metrics[selected]["cumulative"]["net_ev_pct"],
            paired_delta_ev_pct=metrics[selected]["cumulative"]["paired_delta_ev_pct"],
            robust_delta_ev_lower_bound_pct=metrics[selected]["cumulative"][
                "robust_lower_bound_pct"
            ],
        )
    )


def record_native_source(state, policy, *, owner, scope_id, now, action, fields):
    """Existing machine's durable source writer; preserve original decisions."""
    from copy import deepcopy

    try:
        features = state.setdefault("signal_features", {})
        bar = str(
            fields.get("signal_bar")
            or (state.get("pending_entry_confirmation") or {}).get("signal_bar")
            or features.get("signal_bar")
            or state.get("signal_bar")
            or ""
        )
        opportunity = (state.get("timing_operating_opportunities") or {}).get(
            scope_id + ":" + bar
        )
        contract = (
            opportunity.get("contract")
            if opportunity
            else features.get("timing_operating_contract")
        )
        if contract is None:
            contract = freeze_episode_plan(
                state, policy, owner=owner, scope_id=scope_id, now=now
            )
        if not contract:
            return
        if features.get("signal_bar") == bar:
            features["timing_operating_contract"] = contract
        native = (
            opportunity.setdefault("native_state", {})
            if opportunity
            else features.setdefault("timing_operating_native_state", {})
        )
        receipts = native.setdefault("order_clocks", {})
        if action == "buy_submitted":
            if (native.get("entry_admission") or {}).get("permitted") is not True:
                native["entry_admission"] = dict(
                    at=now.isoformat(),
                    permitted=True,
                    basis="original_native_buy_owner_after_all_common_entry_guards",
                )
        elif "blocked_before_buy" in action:
            if (native.get("entry_admission") or {}).get("permitted") is True:
                native["post_admission_veto"] = action
            else:
                native["entry_admission"] = dict(
                    at=now.isoformat(), permitted=False, basis=action
                )
        if action in {
            "buy_submitted",
            "target_submitted",
            "buy_filled",
            "target_filled",
            "buy_cancel_intent",
            "buy_cancel_submitted",
            "buy_resolved_without_fill",
            "unfilled_buy_leg_resolved_after_sibling_completed",
        }:
            receipts.setdefault(
                str(fields.get("leg_id")) + ":" + action, now.isoformat()
            )
        if state.get("signal_bar") == bar:
            matched = matching_native_legs(
                contract,
                [
                    dict(l, route=l.get("route") or getattr(policy, "route", None))
                    for l in state.get("legs", [])
                ],
            )
            if matched is not None:
                native["legs"] = deepcopy(matched)
        native["observed_at"] = now.isoformat()
        native["confirmed_delay_sec"] = int(
            features.get("entry_confirmation_delay_sec") or 0
        )
        native["entry_guard_features"] = deepcopy(
            {
                k: features.get(k)
                for k in (
                    "market_weakness_entry_guard",
                    "entry_liquidity",
                    "entry_execution_velocity",
                )
            }
        )
        native["confirmation_policy_provenance"] = deepcopy(
            features.get("entry_timing_policy_provenance")
            or (state.get("pending_entry_confirmation") or {}).get("policy_provenance")
            or {}
        )
        if opportunity:
            opportunity["actual_order_submitted"] = any(
                l.get("buy_order_no") for l in native.get("legs", [])
            )
            opportunity["terminal_action"] = action
        else:
            features["timing_operating_native_state"] = native
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        state["timing_operating_source_gap"] = type(exc).__name__ + ":" + str(exc)


def native_actual_projection(contract, native_state, points):
    """No old stop/cost/first-fill clock recovery and no borrowed SELL."""
    from datetime import datetime

    try:
        legs = native_state["legs"]
        clocks = native_state["order_clocks"]
        if matching_native_legs(contract, legs) is None:
            return None
        ids = [l.get(k) for l in legs for k in ("buy_order_no", "target_order_no")]
        if len(set(ids)) != len(ids):
            return None
        buy = sell = capital = reserve = qty = 0
        submit_ms = []
        target_ms = []
        ends = []
        start = datetime.fromisoformat(contract["decision_at"])
        for l in legs:
            q = l["quantity"]
            first = (l.get("adaptive_exit_first_fill_observation") or {}).get(
                "first_observed_at"
            )
            programme_fills = (native_state.get("programme_fills") or {}).get(
                l["leg_id"], []
            )
            programme_closed = (
                bool(programme_fills)
                and sum(r["filled_qty"] for r in programme_fills) == q
                and len({r["order_no"] for r in programme_fills})
                == len(programme_fills)
            )
            if (
                not first
                or l.get("buy_filled_qty") != q
                or not (
                    programme_closed
                    or (
                        l.get("target_filled_qty") == q
                        and l.get("target_fill_price")
                        and l.get("target_filled_at")
                    )
                )
                or not all(
                    l.get(k)
                    for k in (
                        "buy_order_no",
                        "target_order_no",
                        "buy_owner_registry_intent_id",
                        "target_owner_registry_intent_id",
                    )
                )
                or l.get("buy_owner_registry_reconciliation_required")
                or l.get("target_owner_registry_reconciliation_required")
            ):
                return None
            fill = datetime.fromisoformat(first)
            end = (
                max(datetime.fromisoformat(r["at"]) for r in programme_fills)
                if programme_closed
                else datetime.fromisoformat(l["target_filled_at"])
            )
            ack = datetime.fromisoformat(clocks[l["leg_id"] + ":buy_submitted"])
            target = datetime.fromisoformat(clocks[l["leg_id"] + ":target_submitted"])
            if not start <= ack <= fill <= target <= end:
                return None
            buy += q * l["fill_price"]
            sell += (
                sum(r["fill_amount"] for r in programme_fills)
                if programme_closed
                else q * l["target_fill_price"]
            )
            qty += q
            capital += (
                sum(
                    r["filled_qty"]
                    * l["fill_price"]
                    * (datetime.fromisoformat(r["at"]) - fill).total_seconds()
                    / 60
                    for r in programme_fills
                )
                if programme_closed
                else q * l["fill_price"] * (end - fill).total_seconds() / 60
            )
            reserve += q * l["entry_price"] * (fill - ack).total_seconds() / 60
            submit_ms.append(
                int((ack - start).total_seconds() * 1000)
                - 1000 * int(native_state.get("confirmed_delay_sec", 0))
            )
            target_ms.append(int((target - fill).total_seconds() * 1000))
            ends.append(end)
        gaps = [
            int(
                (
                    datetime.fromisoformat(b["at"]) - datetime.fromisoformat(a["at"])
                ).total_seconds()
                * 1000
            )
            for a, b in zip(points, points[1:])
        ]
        if not gaps or min(gaps) <= 0 or min(submit_ms) < 0:
            return None
        return _seal(
            dict(
                status="COMPLETED",
                origin="real",
                contract_sha256=contract["sha256"],
                quantity=qty,
                exact_lineage=True,
                filled_quantity=qty,
                net_pnl_krw=sell * (1 - contract["cost_rate"]) - buy,
                capital_krw_minutes=capital,
                reserve_krw_minutes=reserve,
                closed_at_ms=int(max(ends).timestamp() * 1000),
                knowledge_date=datetime.fromisoformat(native_state["observed_at"])
                .date()
                .isoformat(),
                submit_latency_ms=max(submit_ms),
                target_ack_latency_ms=max(target_ms),
                maximum_depth_gap_ms=max(gaps),
                **programme_clock_parameters(native_state),
                target_touch_latency_ms=native_target_touch_latency(
                    contract, native_state, points
                ),
                cost_provenance=contract["cost_provenance"],
                profit_basis="broker_prices_with_frozen_cost_model_not_account_settlement",
                clock_basis="native_owner_local_reconciliation_observation_not_exchange_or_wire_latency",
            )
        )
    except (KeyError, TypeError, ValueError):
        return None


def project_native_operating_path(
    contract, depth_rows, native_state, *, market_rows=()
):
    entry_venue = contract.get(
        "execution_data_venue",
        contract.get(
            "market_data_venue",
            "NXT" if (contract.get("plan") or [{}])[0].get("route") == "NXT" else "SOR",
        ),
    )
    source = project_operating_source(
        contract, [r for r in depth_rows if r.get("venue") == entry_venue]
    )
    from datetime import datetime

    programme_rows = sorted(
        [dict(r) for r in (*depth_rows, *market_rows)],
        key=lambda r: (
            datetime.fromisoformat(r["local_receive_timestamp"]),
            r.get("source_sequence", 0),
        ),
    )
    source = _seal(source | {"programme_rows": programme_rows})
    if not _sealed(contract) or contract.get("status") == "source_gap":
        return source
    guard = native_guard_projection(
        contract, source["points"], native_state=native_state or {}
    )
    actual = (
        widget_actual_projection
        if contract.get("owner") == "widget"
        else native_actual_projection
    )(contract, native_state or {}, source["points"])
    disposition = "completed" if actual is not None else "source_gap"
    if (
        actual is None
        and ((native_state or {}).get("entry_admission") or {}).get("permitted")
        is False
    ):
        disposition = "valid_no_order"
    statuses = [l.get("status") for l in (native_state or {}).get("legs", [])]
    if contract.get("owner") == "widget":
        statuses = [o.get("status") for o in (native_state or {}).get("orders", [])]
    if not statuses or any(
        status not in {"COMPLETE", "NO_FILL", "FILLED", "CANCELED"}
        for status in statuses
    ):
        if disposition != "valid_no_order":
            disposition = "pending" if actual is None else "completed"
    return _seal(
        {k: v for k, v in source.items() if k != "sha256"}
        | {"guard_path": guard, "actual": actual, "actual_disposition": disposition}
    )


def selected_exit_programs(*, now, owner, adaptive_required=False):
    """Read the same pinned supplemental policies as the original owner.

    Absence is the loader's documented OFF contract. A selected supplement is
    an explicit unsupported scope, never silently a native-target certificate.
    This does not load tokens, call broker APIs, or enable a supplement.
    """
    from src.trading.config import machine_profit_stagnation_policy as profit
    from src.trading.config import machine_target_ratchet_policy as ratchet

    programs = {}
    for name, module in (("profit_stagnation", profit), ("target_ratchet", ratchet)):
        try:
            selected = module.load_policy(
                now=now,
                owner="widget_auto_trade" if owner == "widget" else owner,
                entered_at=now.isoformat() if name == "target_ratchet" else now,
            )
            programs[name] = {
                "selected": selected is not None,
                "pin": selected[1] if selected else None,
                "policy": selected[0] if selected else None,
            }
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return dict(
                status="source_gap", blocker=name + ":" + str(exc), programs=programs
            )
    programs["adaptive_exit"] = {"selected": bool(adaptive_required)}
    return dict(
        status=(
            "unsupported_scope"
            if adaptive_required
            else (
                "native_target_with_selected_programs"
                if any(v["selected"] for v in programs.values())
                else "native_target_only"
            )
        ),
        programs=programs,
    )


def _native_target_price(contract, price):
    if contract.get("target_bps") is not None:
        from src.trading.widget_auto_trade.engine import _take_profit_price

        return _take_profit_price(price, profit_bps=contract["target_bps"])
    from src.trading.order.tick_utils import move_price_by_ticks

    return move_price_by_ticks(price, contract["target_ticks"])


def capture_episode_opportunity(
    state,
    policy,
    *,
    owner,
    scope_id,
    now,
    signal_bar,
    plans,
    quantity,
    quantity_receipt,
    adaptive_required=False,
    live_eligible=False,
):
    """Persist the opportunity BEFORE confirmation; children retain custody.

    Rechecks reuse the original frozen plan. This writes the existing state,
    bounded to the native day's opportunities, not a separate collector.
    """
    from copy import deepcopy
    from src.trading.config.machine_entry_timing_policy import (
        resolve_entry_confirmation_policy,
    )

    route = str(plans[0].get("route") or getattr(policy, "route", "SOR"))
    timing = resolve_entry_confirmation_policy(
        target_date=now.date(),
        owner=owner,
        scope_id=scope_id,
        symbol="005930",
        session="NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR",
        entry_state="UNSPECIFIED",
        native_policy=policy,
        approved_leg_quantity=quantity,
    )
    features = dict(
        signal_bar=signal_bar,
        signal_decision_at=now.isoformat(),
        new_entry_quantity_receipt=quantity_receipt,
        route=route,
        entry_timing_policy_provenance=timing["provenance"],
        entry_confirmation_delay_sec=timing["delay_sec"],
    )
    preview = dict(
        trade_date=state.get("trade_date"),
        timing_native_live_eligible=live_eligible,
        signal_features=features,
        timing_adaptive_services_present=adaptive_required,
        legs=[dict(plan, quantity=quantity) for plan in plans],
    )
    store = state.setdefault("timing_operating_opportunities", {})
    key = scope_id + ":" + signal_bar
    if key not in store:
        if len(store) >= 128:
            state["timing_operating_source_gap"] = (
                "native_opportunity_capacity_exceeded"
            )
            return
        c = freeze_episode_plan(
            preview, policy, owner=owner, scope_id=scope_id, now=now
        )
        if c is not None:
            store[key] = dict(
                contract=c,
                native_state={
                    "legs": deepcopy(preview["legs"]),
                    "order_clocks": {},
                    "observed_at": now.isoformat(),
                },
                terminal_action="pending",
                actual_order_submitted=False,
            )


def operating_cases(cohort_rows):
    """Use producer-rooted projections only; gaps stay in the cohort panel."""
    cases = []
    for _, row in cohort_rows:
        source = row.get("machine_operating_source")
        if isinstance(source, dict):
            if row.get("owner_policy_tuning_eligible") is False or row.get(
                "micro_context_status"
            ) not in (None, "matched"):
                source = _seal(
                    source
                    | {
                        "projection_errors": [
                            *source.get("projection_errors", []),
                            "native_parent_source_quality_not_eligible",
                        ]
                    }
                )
            cases.append((source, _decisions(row)))
        else:
            cases.append(
                (
                    dict(
                        contract={
                            "source_date": str(_),
                            "owner": row.get("owner"),
                            "scope_id": row.get("entry_timing_scope_id"),
                            "blocker": "native_frozen_operating_projection_missing",
                            "repair_owner": OPERATING_OWNER,
                        },
                        status="source_gap",
                    ),
                    {},
                )
            )
    return cases


def native_parent_anchor(opportunity):
    """One frozen opportunity, independent of leg fills or final HOLD state."""
    c = opportunity.get("contract") or {}
    if not _sealed(c):
        return None
    if c.get("status") == "source_gap":
        route = c.get("route", "SOR")
        session = (
            "NXT_PREMARKET"
            if route == "NXT" and c.get("scope_id") == "morning"
            else "KRX_REGULAR"
        )
        price = max(
            (
                int(l.get("entry_price") or l.get("limit_price") or 0)
                for l in c.get("plan", [])
            ),
            default=0,
        )
        return dict(
            anchor_id="native:" + c["sha256"],
            lifecycle_id="native:" + c["sha256"],
            owner=c.get("owner", "episode"),
            scope_id=c.get("scope_id"),
            entry_timing_scope_id=c.get("scope_id"),
            symbol="005930",
            session=session,
            anchor_at=c["decision_at"],
            anchor_price=price or None,
            expected_venues=["NXT" if route == "NXT" else "SOR"],
            expected_session_buckets=[
                "NXT_PREMARKET" if session == "NXT_PREMARKET" else "SOR_REGULAR"
            ],
            anchor_role=(
                "episode_signal_decision_leg"
                if c.get("owner") == "episode"
                else "actual_widget_entry_signal"
            ),
            entry_state="UNSPECIFIED",
            owner_policy_tuning_eligible=False,
            owner_lifecycle_contract_valid=False,
            native_operating_parent=True,
            native_operating_contract=c,
            native_operating_state=opportunity.get("native_state") or {},
            actual_order_submitted=opportunity.get("actual_order_submitted") is True,
            owner_outcome={"realized": False, "cost_aware_net_return_pct": None},
        )
    route = c["plan"][0]["route"]
    session = c.get("owner_session") or (
        "NXT_PREMARKET"
        if route == "NXT" and c["scope_id"] == "morning"
        else "KRX_REGULAR"
    )
    bucket = c.get("depth_session") or (
        "NXT_PREMARKET" if session == "NXT_PREMARKET" else "SOR_REGULAR"
    )
    price = max(l["limit_price"] for l in c["plan"])
    identity = c["sha256"]
    return dict(
        anchor_id="native:" + identity,
        lifecycle_id="native:" + identity,
        owner=c["owner"],
        scope_id=c["scope_id"],
        entry_timing_scope_id=c["scope_id"],
        symbol=c["symbol"],
        session=session,
        expected_venues=sorted(
            {c.get("market_data_venue", "NXT" if route == "NXT" else "SOR"), route}
        ),
        expected_session_buckets=sorted(
            {
                bucket,
                (
                    "NXT_PREMARKET"
                    if session == "NXT_PREMARKET"
                    else route
                    + ("_AFTERMARKET" if "AFTERMARKET" in bucket else "_REGULAR")
                ),
            }
        ),
        anchor_at=c["decision_at"],
        anchor_price=price,
        owner_entry_limit_price=price,
        owner_requested_quantity=c["total_quantity"],
        owner_target_price=_native_target_price(c, price),
        owner_round_trip_cost_pct=c["cost_rate"] * 100,
        lifecycle_stage="entry",
        anchor_role=(
            "episode_signal_decision_leg"
            if c["owner"] == "episode"
            else "actual_widget_entry_signal"
        ),
        entry_state=c.get("entry_state", "UNSPECIFIED"),
        source_entry_event_id=identity,
        owner_lifecycle_contract_valid=True,
        owner_policy_tuning_eligible=True,
        actual_order_submitted=opportunity.get("actual_order_submitted") is True,
        native_operating_parent=True,
        native_operating_contract=c,
        native_operating_state=opportunity.get("native_state") or {},
        owner_outcome={"realized": False, "cost_aware_net_return_pct": None},
    )


def capture_widget_opportunity(
    symbol_state,
    *,
    symbol,
    scope_id,
    session,
    route,
    source_state,
    signal_id,
    reference_price,
    quantity,
    execution_policy,
    now,
    target_bps,
    adaptive_required=False,
):
    """Capture the existing widget market entry before confirmation/transport.

    Scale-in and forced/source exits are separate owner programs. They remain
    explicitly unsupported rather than borrowing the old 1200s close label.
    """
    from src.engine.trade_profit import get_trade_cost_rate
    from src.engine.monitoring.policy_research_economics import digest
    from copy import deepcopy

    if symbol != "005930":
        return
    store = symbol_state.setdefault("timing_operating_opportunities", {})
    if signal_id in store:
        return
    if len(store) >= 128:
        symbol_state["timing_operating_source_gap"] = (
            "native_opportunity_capacity_exceeded"
        )
        return
    policy = deepcopy(execution_policy) or {}
    programs = selected_exit_programs(
        now=now, owner="widget", adaptive_required=adaptive_required
    )
    if (
        policy.get("force_flat_at_session_end")
        or policy.get("source_final_exit_action") != "observe_only_no_forced_sell"
    ):
        programs = dict(
            programs,
            status="unsupported_scope",
            blocker="widget_scale_in_or_source_exit_operating_adapter_required",
        )
    if (
        type(quantity) is not int
        or quantity <= 0
        or type(reference_price) is not int
        or reference_price <= 0
    ):
        c = _seal(
            dict(
                schema=OPERATING_SCHEMA,
                status="source_gap",
                source_date=now.date().isoformat(),
                decision_at=now.isoformat(),
                owner="widget",
                scope_id=scope_id,
                route=route,
                plan=[],
                blocker="native_widget_quantity_or_price_invalid",
                repair_owner=OPERATING_OWNER,
            )
        )
    else:
        c = _seal(
            dict(
                schema=OPERATING_SCHEMA,
                owner="widget",
                scope_id=scope_id,
                symbol=symbol,
                operating_adapter_version=OPERATING_ADAPTER_VERSION,
                native_policy_type="widget_native_execution_policy",
                source_date=now.date().isoformat(),
                decision_at=now.isoformat(),
                signal_bar=signal_id,
                plan=[
                    dict(
                        leg_id="entry" if i == 0 else "add" + str(i),
                        route="NXT" if route == "NXT" else "SOR",
                        quantity=quantity,
                        limit_price=reference_price,
                    )
                    for i in range(
                        1 + len(policy.get("add_trigger_bps_from_initial_fill") or [])
                    )
                ],
                total_quantity=quantity
                * (1 + len(policy.get("add_trigger_bps_from_initial_fill") or [])),
                native_policy=policy,
                native_policy_sha256=digest(policy),
                native_owner_code_sha256=frozen_native_owner_code(),
                target_ticks=None,
                target_bps=target_bps,
                entry_kind="market",
                cancel_at=None,
                cancel_basis="market_order_terminal_no_synthetic_ttl",
                selected_programs=programs,
                owner_session=session,
                market_data_venue=route,
                execution_data_venue="NXT" if route == "NXT" else "SOR",
                execution_depth_session=(
                    "NXT_PREMARKET"
                    if session == "NXT_PREMARKET"
                    else (
                        "SOR_REGULAR" if session == "KRX_REGULAR" else "SOR_AFTERMARKET"
                    )
                ),
                depth_session=(
                    "NXT_PREMARKET"
                    if session == "NXT_PREMARKET"
                    else (
                        route + "_REGULAR"
                        if session == "KRX_REGULAR"
                        else route + "_AFTERMARKET"
                    )
                ),
                cost_rate=get_trade_cost_rate(),
                cost_contract=frozen_operating_cost_contract(),
                cost_provenance="frozen_loaded_trade_profit_configuration_not_broker_settlement",
                exit_contract="native_target_until_guard_no_synthetic_terminal",
                incumbent_arm="baseline",
                allocation_budget_krw=None,
                allocation_role="native_quantity_order_envelope_only",
                order_envelope_krw=quantity
                * (1 + len(policy.get("add_trigger_bps_from_initial_fill") or []))
                * reference_price,
                quantity_authority=dict(
                    owner="widget",
                    quantity=quantity,
                    source="existing_widget_resolved_quantity",
                ),
                entry_state=source_state,
                runtime_effect=False,
                broker_order_forbidden=True,
                requires_native_guard_admission=True,
            )
        )
    from src.trading.config.machine_entry_timing_policy import (
        resolve_entry_confirmation_policy,
    )

    timing = resolve_entry_confirmation_policy(
        target_date=now.date(),
        owner="widget",
        scope_id=scope_id,
        symbol=symbol,
        session=session,
        entry_state=source_state,
        native_policy=policy,
        approved_leg_quantity=quantity,
    )
    c = _seal(
        c
        | {
            "incumbent_arm": (
                timing["provenance"].get("confirmation_feature_arm", "combined")
                if timing["mode"] == "per_signal_dynamic_0_1_3_5"
                else "baseline"
            )
        }
    )
    store[signal_id] = dict(
        contract=c,
        native_state={
            "legs": [],
            "order_clocks": {},
            "observed_at": now.isoformat(),
            "scale_ticks": [],
        },
        actual_order_submitted=False,
        terminal_action="pending",
    )


def record_widget_native(symbol_state, *, event, now):
    """Fold the original widget orders, without recovering another episode."""
    from copy import deepcopy

    signal = event.get("parent_entry_signal_id") or event.get("signal_id")
    store = symbol_state.get("timing_operating_opportunities") or {}
    opportunity = store.get(signal)
    if not opportunity and isinstance(signal, str):
        roots = [root for root in store if signal.startswith(root + ":")]
        if len(roots) == 1:
            signal = roots[0]
            opportunity = store[signal]
    if not opportunity and signal is None:
        signal = symbol_state.get("entry_signal_id")
        opportunity = store.get(signal)
    if not opportunity:
        return None
    orders = [
        deepcopy(o)
        for o in symbol_state.get("orders", [])
        if o.get("signal_id") == signal or o.get("parent_entry_signal_id") == signal
    ]
    native = opportunity["native_state"]
    if (
        event.get("event_type") == "order_submitted"
        and event.get("actual_order_submitted") is True
        and any(o.get("side") == "BUY" and o.get("order_no") for o in orders)
    ):
        if (native.get("entry_admission") or {}).get("permitted") is not True:
            native["entry_admission"] = dict(
                at=now.isoformat(),
                permitted=True,
                basis="original_widget_buy_owner_after_all_common_entry_guards",
            )
    if event.get("actual_order_submitted") is False and (
        "blocked" in str(event.get("event_type"))
        or event.get("market_weakness_blocked") is True
    ):
        if not native.get("entry_admission", {}).get("permitted") and not any(
            o.get("side") == "BUY" and o.get("order_no") for o in orders
        ):
            native["entry_admission"] = dict(
                at=now.isoformat(), permitted=False, basis=event.get("event_type")
            )
        elif not str(event.get("signal_id", "")).startswith(str(signal) + ":ADD"):
            native["post_admission_veto"] = event.get("event_type")
    native.update(
        orders=orders,
        observed_at=now.isoformat(),
        widget_state=deepcopy(
            {
                k: symbol_state.get(k)
                for k in (
                    "entry_route",
                    "entry_session",
                    "entry_signal_id",
                    "take_profit_target_price",
                    "take_profit_basis_fill_price",
                    "scale_in_requested",
                    "adaptive_exit_session",
                    "profit_stagnation_exit",
                    "holding_target_amendment",
                )
            }
        ),
    )
    native["confirmation_policy_provenance"] = deepcopy(
        symbol_state.get("entry_timing_policy_provenance") or {}
    )
    native["confirmed_delay_sec"] = int(
        symbol_state.get("entry_confirmation_delay_sec") or 0
    )
    opportunity["actual_order_submitted"] |= event.get("actual_order_submitted") is True
    opportunity["terminal_action"] = event.get("event_type")
    return deepcopy(opportunity)


def validate_operating_selection(receipt, *, arm):
    """Cheap consumer validation of frozen calculation/model/partition proof."""
    from src.trading.config.machine_entry_timing_policy import (
        MIN_COMPLETED_OUTCOMES,
        DYNAMIC_MIN_OBSERVED_DAYS,
        DYNAMIC_MIN_COMPLETED_OUTCOMES,
        DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT,
        MIN_ABSOLUTE_EV_UPLIFT_PCT,
        MAX_P10_DETERIORATION_PCT,
    )

    try:
        if (
            not _sealed(receipt)
            or receipt.get("status") != "candidate_ready"
            or receipt.get("candidate") != arm
        ):
            return False
        proof = receipt["model_validation"]
        if (
            not _sealed(proof)
            or proof.get("status") != "validated"
            or not _sealed(proof["model"])
        ):
            return False
        if proof["scope_sha256"] != proof["model"].get("scope_sha256") or proof[
            "scope_sha256"
        ] != operating_scope(receipt["runtime_scope_contract"]):
            return False
        if (
            receipt["runtime_scope_contract"].get("operating_adapter_version")
            != OPERATING_ADAPTER_VERSION
        ):
            return False
        model_dates = set(proof["calibration_dates"] + proof["model_holdout_dates"])
        if (
            not proof["calibration_dates"]
            or not proof["model_holdout_dates"]
            or max(proof["calibration_dates"]) >= min(proof["model_holdout_dates"])
        ):
            return False
        candidate_dates = receipt["candidate_calibration_dates"]
        hold = receipt["candidate_holdout_date"]
        if (
            not candidate_dates
            or max(model_dates) > proof["available_after_date"]
            or proof["available_after_date"] >= min(candidate_dates)
            or max(candidate_dates) >= hold
        ):
            return False
        if (
            len(receipt["observed_dates"]) < DYNAMIC_MIN_OBSERVED_DAYS
            or receipt["paired_count"] < DYNAMIC_MIN_COMPLETED_OUTCOMES
            or receipt["paired_coverage_pct"]
            < DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT
        ):
            return False
        witnesses = proof["witnesses"]
        if len(witnesses) < MIN_COMPLETED_OUTCOMES or len(
            {w["source_sha256"] for w in witnesses}
        ) != len(witnesses):
            return False
        if any(
            v * 100 < DYNAMIC_MIN_PAIRED_COMPLETED_COVERAGE_PCT
            for v in proof["coverage"].values()
        ):
            return False
        for w in witnesses:
            expected = (
                proof["calibration_dates"]
                if w["partition"] == "calibration"
                else proof["model_holdout_dates"]
            )
            if (
                w["source_date"] not in expected
                or w["scope_sha256"] != proof["scope_sha256"]
            ):
                return False
            if w["partition"] == "model_holdout" and (
                w["quantity_error"] != 0
                or any(abs(w[k]) > v + 1e-12 for k, v in proof["tolerance"].items())
            ):
                return False
        metrics = receipt["candidate_metrics"]
        for partition in ("calibration", "holdout", "rolling", "cumulative"):
            chosen = metrics[arm][partition]
            base = metrics[receipt["incumbent_arm"]][partition]
            for key in ("net_ev_pct", "robust_lower_bound_pct", "p10_net_pct"):
                if type(chosen.get(key)) not in (int, float) or not math.isfinite(
                    chosen[key]
                ):
                    return False
            if (
                chosen["net_ev_pct"] <= 0
                or chosen["robust_lower_bound_pct"] < MIN_ABSOLUTE_EV_UPLIFT_PCT
                or chosen["p10_net_pct"]
                < base["p10_net_pct"] - MAX_P10_DETERIORATION_PCT
            ):
                return False
        return (
            receipt["robust_delta_ev_lower_bound_pct"]
            == metrics[arm]["cumulative"]["robust_lower_bound_pct"]
            and receipt["primary_ev_pct"] == metrics[arm]["cumulative"]["net_ev_pct"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def operating_policy_evidence(
    receipt, *, target_date, effective_date, owner, scope_id, symbol
):
    """Translate computed economics into the EXISTING timing promotion floors."""
    from src.trading.config.machine_entry_timing_policy import dynamic_observation_lag
    from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract

    if receipt.get("candidate") not in {
        "bid_rebound",
        "depletion_flow",
        "combined",
    } or not validate_operating_selection(receipt, arm=receipt["candidate"]):
        return None
    cost = comparison_cost_contract(effective_date)
    latest = date.fromisoformat(receipt["observed_dates"][-1])
    lag, limit = dynamic_observation_lag(
        latest, target_date, owner=owner, scope_id=scope_id, symbol=symbol
    )
    if lag is None or lag > limit:
        return None
    selected = receipt["candidate"]
    base = receipt["incumbent_arm"]
    metrics = receipt["candidate_metrics"]
    cumulative = metrics[selected]["cumulative"]
    baseline = metrics[base]["cumulative"]
    roll = metrics[selected]["rolling"]
    return dict(
        entry_confirmation_mode="per_signal_dynamic_0_1_3_5",
        feature_arm=selected,
        operating_economics=receipt,
        source_only_candidate_ready=True,
        observed_trading_days=len(receipt["observed_dates"]),
        unique_decision_lifecycles=receipt["paired_count"],
        completed_outcome_count=receipt["paired_count"],
        latest_completed_observation_date=latest.isoformat(),
        latest_observation_fresh_for_bounded_canary=True,
        source_quality_adjusted_ev_pct=cumulative["net_ev_pct"],
        absolute_ev_uplift_pct=cumulative["robust_lower_bound_pct"],
        baseline_p10_pct=baseline["p10_net_pct"],
        candidate_p10_pct=cumulative["p10_net_pct"],
        dynamic_replay_coverage_rate_pct=receipt["paired_coverage_pct"],
        paired_completed_coverage_rate_pct=receipt["paired_coverage_pct"],
        right_censored_rate_pct=100 - receipt["paired_coverage_pct"],
        rolling_windows={
            "5": dict(
                complete=True,
                positive_and_improved=roll["net_ev_pct"] > 0
                and roll["robust_lower_bound_pct"] > 0,
                **roll,
            )
        },
        runtime_round_trip_cost_pct=cost["round_trip_cost_pct"],
        runtime_cost_trade_date=cost["trade_date"],
        runtime_cost_contract_sha256=cost["contract_sha256"],
        actual_order_submitted=False,
        broker_order_forbidden=True,
        runtime_effect=False,
        allowed_runtime_apply=False,
        profit_basis="native_owner_cost_model_not_actual_profit_or_causal_improvement",
    )


def applied_operating_performance(cases, *, model_validation=None):
    """Version-specific deduped rolling/cumulative native priced outcomes."""
    groups = {}
    seen = {}
    conflicts = set()
    for source, _ in cases:
        c = source.get("contract") or {}
        a = source.get("actual") or {}
        if not _sealed(source) or not _sealed(c) or not _sealed(a):
            continue
        if (
            a.get("origin") != "real"
            or a.get("status") != "COMPLETED"
            or a.get("exact_lineage") is not True
            or a.get("contract_sha256") != c["sha256"]
            or a.get("quantity") != c.get("total_quantity")
        ):
            continue
        identity = c["sha256"]
        if identity in seen and seen[identity] != a:
            conflicts.add(identity)
        seen[identity] = a
    for source, _ in cases:
        c = source.get("contract") or {}
        a = source.get("actual") or {}
        identity = c.get("sha256")
        if identity not in seen or identity in conflicts:
            continue
        version = (source.get("guard_path") or {}).get(
            "applied_policy_hash"
        ) or "baseline_unattributed"
        group = groups.setdefault(
            c["owner"]
            + ":"
            + str(c["scope_id"])
            + ":"
            + operating_scope(c)
            + ":"
            + str(version),
            {},
        )
        group[identity] = dict(
            source_date=c["source_date"], budget=c["order_envelope_krw"], **a
        )
    result = {}
    for key, by_id in groups.items():
        rows = list(by_id.values())
        days = sorted({r["source_date"] for r in rows})

        def aggregate(panel):
            net = sum(r["net_pnl_krw"] for r in panel)
            notional = sum(r["budget"] for r in panel)
            values = sorted(r["net_pnl_krw"] / r["budget"] * 100 for r in panel)
            return dict(
                episode_count=len(panel),
                net_pnl_krw=net,
                net_ev_pct=net / notional * 100 if notional else None,
                p10_net_pct=values[int((len(values) - 1) * 0.1)] if values else None,
                capital_krw_minutes=sum(r["capital_krw_minutes"] for r in panel),
                reserve_krw_minutes=sum(r["reserve_krw_minutes"] for r in panel),
                settled_account_profit_krw=None,
                causal_improvement=None,
            )

        errors = []
        if _sealed(model_validation) and model_validation.get("status") == "validated":
            for source, decisions in cases:
                c = source.get("contract") or {}
                if c.get("sha256") not in by_id:
                    continue
                arm = c.get("incumbent_arm")
                replay = replay_operating_plan(
                    source, decisions.get(arm, {}), model_validation["model"]
                )
                witness = model_witness(source, replay)
                if witness:
                    errors.append(witness)
        result[key] = dict(
            cumulative=aggregate(rows),
            rolling_5_source_days=aggregate(
                [r for r in rows if r["source_date"] in days[-5:]]
            ),
            model_error={
                "witness_count": len(errors),
                "maximum_absolute_net_error_budget_pct": max(
                    (abs(r["net_error_budget_pct"]) for r in errors), default=None
                ),
            },
            profit_basis="broker_prices_with_frozen_owner_cost_model_not_account_settlement",
        )
    census = Counter(s.get("actual_disposition", "source_gap") for s, _ in cases)
    return dict(
        versions=result,
        input_row_count=len(cases),
        actual_dispositions=dict(census),
        identity_conflict_count=len(conflicts),
        shared_capital_comparison=False,
        combined_capital_role="demand_exposure_diagnostic_only",
    )


def widget_actual_projection(contract, native_state, points):
    """Native initial/add/target orders, exact parent and terminal quantities."""
    from datetime import datetime

    try:
        orders = native_state["orders"]
        signal = contract["signal_bar"]
        buys = [
            o
            for o in orders
            if o.get("side") == "BUY"
            and (
                o.get("signal_id") == signal
                or o.get("parent_entry_signal_id") == signal
            )
        ]
        targets = [
            o
            for o in orders
            if o.get("side") == "SELL"
            and o.get("parent_entry_signal_id") == signal
            and o.get("order_role") == "TAKE_PROFIT_SELL"
        ]
        if not buys or not targets or len(buys) + len(targets) != len(orders):
            return None
        if len({o.get("order_no") for o in orders}) != len(orders):
            return None
        if any(
            not o.get("owner_registry_bind_confirmed")
            or not o.get("owner_registry_intent_id")
            or not o.get("order_no")
            or o.get("owner_registry_reconciliation_required")
            or o.get("owner_registry_error")
            for o in orders
        ):
            return None
        if any(
            o.get("status") != "FILLED"
            or o.get("filled_qty") != contract["quantity_authority"]["quantity"]
            for o in buys
        ):
            return None
        if any(o.get("status") not in {"FILLED", "CANCELED"} for o in targets):
            return None
        filled = sum(o["filled_qty"] for o in buys)
        if (
            filled != sum(o.get("filled_qty", 0) for o in targets)
            or filled > contract["total_quantity"]
        ):
            return None
        if any(
            o.get("filled_qty", 0)
            and (
                type(o.get("fill_price")) not in (int, float)
                or not math.isfinite(o["fill_price"])
                or o["fill_price"] <= 0
            )
            for o in orders
        ):
            return None
        start = datetime.fromisoformat(contract["decision_at"])
        ends = [
            datetime.fromisoformat(o["timing_terminal_fill_observed_at"])
            for o in targets
            if o.get("filled_qty")
        ]
        if not ends:
            return None
        end = max(ends)
        ack = datetime.fromisoformat(buys[0]["submitted_at"])
        first = datetime.fromisoformat(buys[0]["timing_first_fill_observed_at"])
        first_target = min(datetime.fromisoformat(o["submitted_at"]) for o in targets)
        if not start <= ack <= first <= first_target <= end:
            return None
        buy = sum(o["filled_qty"] * o["fill_price"] for o in buys)
        sell = sum(
            o["filled_qty"] * o["fill_price"] for o in targets if o.get("filled_qty")
        )
        flows = []
        reserve = 0
        for o in buys:
            at = datetime.fromisoformat(o["timing_first_fill_observed_at"])
            sent = datetime.fromisoformat(o["submitted_at"])
            if not start <= sent <= at <= end:
                return None
            flows.append((at, o["filled_qty"], o["filled_qty"] * o["fill_price"]))
            reserve += (
                o["filled_qty"]
                * contract["plan"][0]["limit_price"]
                * (at - sent).total_seconds()
                / 60
            )
        for o in targets:
            if o.get("filled_qty"):
                flows.append(
                    (
                        datetime.fromisoformat(o["timing_terminal_fill_observed_at"]),
                        -o["filled_qty"],
                        0,
                    )
                )
        capital = 0
        previous = start
        open_qty = 0
        basis = 0
        total_qty = 0
        for at, q, notional in sorted(flows):
            capital += (
                basis
                * open_qty
                / max(total_qty, 1)
                * (at - previous).total_seconds()
                / 60
            )
            if q > 0:
                basis += notional
                total_qty += q
            open_qty += q
            if open_qty < 0:
                return None
            previous = at
        gaps = [
            int(
                (
                    datetime.fromisoformat(b["at"]) - datetime.fromisoformat(a["at"])
                ).total_seconds()
                * 1000
            )
            for a, b in zip(points, points[1:])
        ]
        ticks = native_state.get("scale_ticks", [])
        tick_gaps = [
            int(
                (
                    datetime.fromisoformat(b["at"]) - datetime.fromisoformat(a["at"])
                ).total_seconds()
                * 1000
            )
            for a, b in zip(ticks, ticks[1:])
        ]
        if not gaps or min(gaps) <= 0 or open_qty:
            return None
        cancels = [o for o in targets if o.get("status") == "CANCELED"]
        cancel_ms = [
            int(
                (
                    datetime.fromisoformat(o["timing_cancel_terminal_observed_at"])
                    - datetime.fromisoformat(o["cancel_attempted_at"])
                ).total_seconds()
                * 1000
            )
            for o in cancels
        ]
        latency = int((ack - start).total_seconds() * 1000) - 1000 * int(
            native_state.get("confirmed_delay_sec", 0)
        )
        if latency < 0 or any(v < 0 for v in cancel_ms):
            return None
        return _seal(
            dict(
                status="COMPLETED",
                origin="real",
                contract_sha256=contract["sha256"],
                quantity=contract["total_quantity"],
                filled_quantity=filled,
                exact_lineage=True,
                lineage=[
                    {
                        k: o[k]
                        for k in (
                            "order_no",
                            "owner_registry_intent_id",
                            "signal_id",
                            "order_role",
                        )
                    }
                    for o in orders
                ],
                net_pnl_krw=sell * (1 - contract["cost_rate"]) - buy,
                capital_krw_minutes=capital,
                reserve_krw_minutes=reserve,
                closed_at_ms=int(end.timestamp() * 1000),
                knowledge_date=datetime.fromisoformat(native_state["observed_at"])
                .date()
                .isoformat(),
                submit_latency_ms=latency,
                target_ack_latency_ms=int(
                    (first_target - first).total_seconds() * 1000
                ),
                maximum_depth_gap_ms=max(gaps),
                **programme_clock_parameters(native_state),
                target_touch_latency_ms=native_target_touch_latency(
                    contract, native_state, points
                ),
                target_cancel_latency_ms=max(cancel_ms) if cancel_ms else None,
                scale_check_latency_ms=(
                    max(
                        0,
                        int(
                            (
                                datetime.fromisoformat(ticks[0]["at"]) - first
                            ).total_seconds()
                            * 1000
                        ),
                    )
                    if ticks
                    else None
                ),
                maximum_scale_tick_gap_ms=max(tick_gaps) if tick_gaps else None,
                cost_provenance=contract["cost_provenance"],
                profit_basis="broker_prices_with_frozen_cost_model_not_account_settlement",
                clock_basis="native_owner_local_reconciliation_observation_not_exchange_or_wire_latency",
            )
        )
    except (KeyError, TypeError, ValueError):
        return None


def semantic_native_policy(policy):
    """Economically identical dated receipts share model scope, not identity."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(policy):
        policy = json.loads(json.dumps(asdict(policy), default=lambda x: x.isoformat()))
    ignored = {
        "runtime_policy_hash",
        "runtime_policy_source",
        "candidate_revision_sha256",
        "policy_content_sha256",
        "joint_gate_sha256",
        "policy_id",
        "evidence_artifact",
        "evidence_window",
        "research_arm",
        "applied_at_kst",
        "target_date",
        "source_date",
    }
    return {k: v for k, v in policy.items() if k not in ignored}


def operating_runtime_matches(receipt, *, native_policy, leg_quantity):
    """Current approved quantity/native rules must match the evaluated scope."""
    try:
        contract = receipt["runtime_scope_contract"]
        from src.engine.trade_profit import get_trade_cost_rate
        from datetime import datetime
        from zoneinfo import ZoneInfo

        return (
            semantic_native_policy(native_policy)
            == semantic_native_policy(contract["native_policy"])
            and all(l["quantity"] == leg_quantity for l in contract["plan"])
            and get_trade_cost_rate() == contract["cost_rate"]
            and frozen_native_owner_code() == contract["native_owner_code_sha256"]
            and selected_exit_programs(
                now=datetime.now(ZoneInfo("Asia/Seoul")), owner=contract["owner"]
            )
            == contract["selected_programs"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def instrumentation_call(state, function, /, *args, **kwargs):
    """Optional research telemetry has no live execution authority."""
    try:
        return function(*args, **kwargs)
    except Exception as exc:
        state["timing_operating_source_gap"] = type(exc).__name__ + ":" + str(exc)
        return None


def refresh_native_opportunity(state, *, route=None):
    """Fold native mutations saved by supplemental owners, without recursion."""
    from copy import deepcopy

    bar = state.get("signal_bar")
    for opportunity in (state.get("timing_operating_opportunities") or {}).values():
        c = opportunity.get("contract") or {}
        if c.get("signal_bar") == bar:
            matched = matching_native_legs(
                c,
                [dict(l, route=l.get("route") or route) for l in state.get("legs", [])],
            )
            if matched is not None:
                opportunity.setdefault("native_state", {})["legs"] = deepcopy(matched)


def adaptive_new_enrollment_selected(services):
    admission = getattr(services, "admission", None)
    return getattr(admission, "current", admission) is not None


def record_widget_scale_source(
    symbol_state, *, now, current_price, source_status, permitted=None, stage_index=None
):
    """Retain original as-of scale inputs and original guard verdicts only."""
    store = symbol_state.get("timing_operating_opportunities") or {}
    opportunity = store.get(symbol_state.get("entry_signal_id"))
    if not opportunity:
        return
    ticks = opportunity.setdefault("native_state", {}).setdefault("scale_ticks", [])
    at = now.isoformat()
    if ticks and ticks[-1]["at"] == at:
        row = ticks[-1]
    else:
        if len(ticks) >= 30000:
            symbol_state["timing_operating_source_gap"] = (
                "native_scale_tick_capacity_exceeded"
            )
            opportunity["native_state"]["scale_source_overflow"] = True
            return
        row = dict(
            at=at,
            current_price=current_price,
            source_status=source_status,
            stage_index=stage_index,
            permitted=None,
            quantity=(opportunity.get("contract") or {})
            .get("quantity_authority", {})
            .get("quantity"),
        )
        ticks.append(row)
    row.update(current_price=current_price, source_status=source_status)
    if stage_index is not None:
        row["stage_index"] = stage_index
    if permitted is not None:
        row["permitted"] = permitted


def _replay_widget_plan(result, c, points, guard, due, model, *, source):
    """Original market legs and pooled-average target; never a forced close.

    A changed scale trigger requires its own as-of native guard receipt. Missing
    verdicts are unsupported, rather than permission inferred from a later BUY.
    """
    from datetime import datetime, timedelta
    from src.trading.order.tick_utils import clamp_price_to_tick

    ticks = guard.get("scale_ticks", [])
    stages = c["plan"]
    triggers = c["native_policy"].get("add_trigger_bps_from_initial_fill") or []
    if len(stages) != 1 + len(triggers):
        raise ValueError("widget_frozen_leg_contract_invalid")
    if ticks and any(
        datetime.fromisoformat(a["at"]) >= datetime.fromisoformat(b["at"])
        for a, b in zip(ticks, ticks[1:])
    ):
        raise ValueError("widget_native_scale_clock_invalid")
    remaining = quantity = buy = sell = capital = reserve = 0
    filled_stages = 0
    initial = None
    target = None
    target_ack = None
    previous = datetime.fromisoformat(c["decision_at"])
    first = None
    sold_any = False
    consumed_tick = None
    pending_scale = None
    programs = _OperatingPrograms(source, model)
    programs.events = result["transitions"]
    for point in points:
        at = datetime.fromisoformat(point["at"])
        capital += (
            buy * remaining / max(quantity, 1) * (at - previous).total_seconds() / 60
        )
        if filled_stages == 0:
            reserve += (
                stages[0]["quantity"]
                * stages[0]["limit_price"]
                * max(0, (at - max(previous, due)).total_seconds())
                / 60
            )
        bids = [
            [p, math.floor(q * model["depth_participation"])]
            for p, q in point["bid_levels"]
        ]
        asks = [
            [p, math.floor(q * model["depth_participation"])]
            for p, q in point["ask_levels"]
        ]
        if pending_scale and at >= pending_scale:
            target_ack = None
        programs.update(at)
        if remaining and target_ack and at >= target_ack:
            if pending_scale is None:
                target = programs.target(
                    "widget",
                    at=at,
                    quantity=remaining,
                    entry=buy / quantity,
                    target=target,
                    route=stages[0]["route"],
                )
            executable = programs.fill_ready(
                "widget", at=at, target=target, bids=bids, quantity=remaining
            )
            for price, depth in bids if executable else []:
                if price < target:
                    break
                take = min(remaining, depth)
                remaining -= take
                sell += take * target
                if take:
                    if pending_scale and take < remaining + take:
                        return dict(
                            result,
                            status="unsupported_scope",
                            blocker="partial_target_during_scale_cancel_requires_owner_remainder_adapter",
                        )
                    sold_any = True
                    result["transitions"].append(
                        dict(
                            at=at.isoformat(),
                            action="pooled_target",
                            quantity=take,
                            price=target,
                        )
                    )
            if not remaining:
                pnl = sell * (1 - c["cost_rate"]) - buy
                return dict(
                    result,
                    status="completed",
                    blocker=None,
                    net_pnl_krw=pnl,
                    net_ev_pct=pnl / c["order_envelope_krw"] * 100,
                    capital_krw_minutes=capital,
                    reserve_krw_minutes=reserve,
                    fill_participation=quantity / c["total_quantity"],
                    exposure_start=c["decision_at"],
                    exposure_end=at.isoformat(),
                    modeled_filled_qty=quantity,
                    remaining_qty=0,
                    buy_notional_krw=buy,
                    sell_notional_krw=sell,
                    cost_krw=sell * c["cost_rate"],
                    cost_provenance=c["cost_provenance"],
                    contract_sha256=c["sha256"],
                    model_sha256=model["sha256"],
                )
        request = filled_stages == 0 and at >= due
        if (
            filled_stages
            and filled_stages < len(stages)
            and not sold_any
            and pending_scale is None
        ):
            if guard.get("scale_source_overflow"):
                raise ValueError("widget_scale_source_overflow")
            check_latency = model.get("scale_check_latency_ms")
            tick_gap = model.get("maximum_scale_tick_gap_ms")
            if (
                type(check_latency) is not int
                or type(tick_gap) is not int
                or tick_gap <= 0
            ):
                raise ValueError("native_widget_scale_clock_model_missing")
            observations = [r for r in ticks if datetime.fromisoformat(r["at"]) <= at]
            if not observations and (at - first).total_seconds() * 1000 > check_latency:
                raise ValueError("widget_scale_timeline_coverage_missing")
            if observations:
                tick = observations[-1]
                stamp = datetime.fromisoformat(tick["at"])
                if (at - stamp).total_seconds() * 1000 > tick_gap:
                    raise ValueError("widget_scale_timeline_coverage_missing")
                if (
                    consumed_tick != tick["at"]
                    and (at - stamp).total_seconds() * 1000 <= tick_gap
                ):
                    consumed_tick = tick["at"]
                    trigger = clamp_price_to_tick(
                        initial * (1 + triggers[filled_stages - 1] / 10000)
                    )
                    if (
                        tick["source_status"] == "PASS"
                        and tick["current_price"] <= trigger
                    ):
                        if (
                            tick.get("permitted") is not True
                            or tick.get("stage_index") != filled_stages
                            or tick["quantity"] != stages[filled_stages]["quantity"]
                        ):
                            return dict(
                                result,
                                status="unsupported_scope",
                                blocker="changed_widget_add_requires_its_own_native_guard_receipt",
                            )
                        cancel_ms = model.get("target_cancel_latency_ms")
                        if type(cancel_ms) is not int or cancel_ms < 0:
                            return dict(
                                result,
                                status="source_gap",
                                blocker="independent_widget_target_cancel_model_missing",
                            )
                        pending_scale = stamp + timedelta(
                            milliseconds=cancel_ms + model["submit_latency_ms"]
                        )
        if pending_scale and at >= pending_scale:
            request = True
        if request:
            q = stages[filled_stages]["quantity"]
            if sum(depth for _, depth in asks) < q:
                return dict(
                    result,
                    status="unsupported_scope",
                    blocker="partial_market_buy_requires_native_remainder_adapter",
                )
            left = q
            notional = 0
            for price, depth in asks:
                take = min(left, depth)
                left -= take
                notional += take * price
                if not left:
                    break
            if filled_stages == 0:
                initial = notional / q
            # Independent owner quantities do not create a cash allocation.
            # The same frozen demand envelope is used on both arms.
            if buy + notional > c["order_envelope_krw"]:
                return dict(
                    result,
                    status="unsupported_scope",
                    blocker="market_entry_exceeds_frozen_comparison_envelope",
                )
            buy += notional
            quantity += q
            remaining += q
            filled_stages += 1
            first = first or at
            pending_scale = None
            target = _native_target_price(c, buy / quantity)
            target_ack = at + timedelta(milliseconds=model["target_ack_latency_ms"])
            result["transitions"].append(
                dict(
                    at=at.isoformat(),
                    action="market_buy",
                    leg_id=stages[filled_stages - 1]["leg_id"],
                    quantity=q,
                    price=notional / q,
                )
            )
        previous = at
    return dict(
        result,
        status="source_gap" if source.get("source_truncated") else "pending",
        blocker=(
            "bounded_source_prefix_exhausted"
            if source.get("source_truncated")
            else "widget_pooled_target_terminal_pending"
        ),
        modeled_filled_qty=quantity,
        remaining_qty=remaining,
    )


def record_operating_owner_tick(owner, now):
    """Observe the original custody/write guard; bounded native journal only.

    No new guard, broker call or source collector. Run after original lock checks.
    Each original owner tick is retained for counterfactual inventory, including
    opportunities whose incumbent has already closed during this native day.
    """
    from src.trading.order.profit_stagnation_owners import guard
    from datetime import datetime

    owner_type = "episode" if hasattr(owner, "policy") else "widget_auto_trade"
    states = (
        [owner._state]
        if owner_type == "episode"
        else [(owner._state.get("symbols") or {}).get("005930", {})]
    )
    permitted = guard(owner, symbol="005930", owner_type=owner_type, now=now)
    for state in states:
        for opp in (state.get("timing_operating_opportunities") or {}).values():
            c = opp.get("contract") or {}
            if (
                c.get("source_date") != now.date().isoformat()
                or c.get("status") == "source_gap"
            ):
                continue
            native = opp.setdefault("native_state", {})
            rows = native.setdefault("programme_ticks", [])
            row = dict(
                at=now.isoformat(),
                through_at=now.isoformat(),
                permitted=permitted,
                maximum_gap_ms=0,
                sample_count=1,
            )
            if rows:
                prior = datetime.fromisoformat(rows[-1]["through_at"])
                gap = int((now - prior).total_seconds() * 1000)
                if gap < 0:
                    native["programme_source_overflow"] = True
                elif gap == 0:
                    rows[-1]["permitted"] = permitted
                elif rows[-1]["permitted"] == permitted:
                    rows[-1].update(
                        through_at=row["at"],
                        maximum_gap_ms=max(gap, rows[-1]["maximum_gap_ms"]),
                        sample_count=rows[-1]["sample_count"] + 1,
                    )
                elif len(rows) < 128:
                    row["maximum_gap_ms"] = gap
                    rows.append(row)
                else:
                    native["programme_source_overflow"] = True
            else:
                rows.append(row)
            native["observed_at"] = now.isoformat()
            if owner_type == "episode" and c.get("signal_bar") == state.get(
                "signal_bar"
            ):
                from copy import deepcopy

                matched = matching_native_legs(
                    c,
                    [
                        dict(
                            l,
                            route=l.get("route")
                            or getattr(owner.policy, "route", None),
                        )
                        for l in state.get("legs", [])
                    ],
                )
                if matched is None:
                    continue
                native["legs"] = deepcopy(matched)
                fills = {}
                for leg in native["legs"]:
                    history = leg.get("holding_target_history", [])
                    if history:
                        h = history[-1]
                        if h.get("ack_observed_at"):
                            elapsed = int(
                                (
                                    datetime.fromisoformat(h["ack_observed_at"])
                                    - datetime.fromisoformat(h["trigger_observed_at"])
                                ).total_seconds()
                                * 1000
                            )
                            if elapsed >= 0:
                                native.setdefault("programme_action_clocks", {})[
                                    "target_amend_latency_ms"
                                ] = elapsed
                    payload = leg.get("profit_stagnation_exit")
                    if not payload:
                        continue
                    clocks = payload.get("operating_action_clocks") or {}
                    if "profit_replace_latency_ms" in clocks:
                        native.setdefault("programme_action_clocks", {}).update(clocks)
                    from src.trading.order.profit_stagnation_exit import order_history

                    rows = []
                    for record in order_history(payload):
                        if not record.get("filled"):
                            continue
                        key = record["order"]
                        r = bounded_custody_terminal_lookup(
                            owner,
                            order_date=key["trading_date"],
                            broker_order_no=key["order_no"],
                            filled_qty=record["filled"],
                        )
                        expected = owner._episode_owner_context(
                            leg=leg, action="timing-source", ordinal=0
                        )
                        if (
                            r
                            and r.get("symbol") == "005930"
                            and r.get("owner_type") == "episode"
                            and r.get("owner_id") == expected.owner_id
                            and r.get("position_id") == expected.position_id
                            and r.get("side") == "SELL"
                            and r.get("filled_qty") == record["filled"]
                            and type(r.get("fill_amount")) is int
                            and r["fill_amount"] > 0
                            and r.get("fill_observed_at_kst")
                        ):
                            rows.append(
                                dict(
                                    order_no=key["order_no"],
                                    intent_id=r["intent_id"],
                                    filled_qty=r["filled_qty"],
                                    fill_amount=r["fill_amount"],
                                    at=r["fill_observed_at_kst"],
                                )
                            )
                    if rows:
                        fills[leg["leg_id"]] = rows
                native["programme_fills"] = fills
            elif owner_type == "widget_auto_trade":
                from copy import deepcopy

                native["orders"] = [
                    deepcopy(o)
                    for o in state.get("orders", [])
                    if o.get("signal_id") == c["signal_bar"]
                    or o.get("parent_entry_signal_id") == c["signal_bar"]
                ]
                for order in native["orders"]:
                    project_widget_registry_terminal(owner, order)
                for h in state.get("holding_target_history", []):
                    if h.get("ack_observed_at"):
                        elapsed = int(
                            (
                                datetime.fromisoformat(h["ack_observed_at"])
                                - datetime.fromisoformat(h["trigger_observed_at"])
                            ).total_seconds()
                            * 1000
                        )
                        if elapsed >= 0:
                            native.setdefault("programme_action_clocks", {})[
                                "target_amend_latency_ms"
                            ] = elapsed
                for payload in (state.get("profit_stagnation_exit") or {}).values():
                    native.setdefault("programme_action_clocks", {}).update(
                        payload.get("operating_action_clocks") or {}
                    )


class _OperatingPrograms:
    """Pure pinned owner decisions plus independently fitted action clocks.

    An unmeasured action blocks only a path that actually requests that action.
    Missing pressure inputs keep the native target, as the original owner does;
    they do not certify valid pressure or fabricate a realised SELL.
    """

    def __init__(self, source, model):
        from collections import deque

        self.source, self.model = source, model
        self.contract, self.guard = source["contract"], source["guard_path"]
        self.rows = iter(source.get("programme_rows", []))
        self.next = next(self.rows, None)
        self.books, self.trades = {}, {}
        self.deque = deque
        self.ticks = iter(self.guard.get("programme_ticks", []))
        self.next_tick = next(self.ticks, None)
        self.last_tick = None
        self.next_check = None
        self.windows, self.pending, self.touch_started = {}, {}, {}
        self.events = []

    def fill_ready(self, identity, *, at, target, bids, quantity):
        key = (identity, target)
        if sum(q for p, q in bids if p >= target) < quantity:
            self.touch_started.pop(key, None)
            return False
        wait = self.model.get("target_touch_latency_ms")
        if type(wait) is not int or wait < 0:
            raise ValueError("independent_native_target_touch_clock_missing")
        started = self.touch_started.setdefault(key, at)
        return (at - started).total_seconds() * 1000 >= wait

    def update(self, at):
        from datetime import datetime

        while (
            self.next
            and datetime.fromisoformat(self.next["local_receive_timestamp"]) <= at
        ):
            r = self.next
            kind = "0D" if "bid_levels" in r else "0B"
            target = self.books if kind == "0D" else self.trades
            target.setdefault(r["venue"], self.deque(maxlen=120)).append(r)
            self.next = next(self.rows, None)
        self.is_tick = False
        while self.next_tick and datetime.fromisoformat(self.next_tick["at"]) <= at:
            self.last_tick = self.next_tick
            self.next_check = at
            self.next_tick = next(self.ticks, None)
        gap = self.model.get("maximum_programme_tick_gap_ms")
        if self.last_tick and type(gap) is int and gap > 0 and at >= self.next_check:
            from datetime import timedelta

            self.is_tick = True
            self.next_check = at + timedelta(milliseconds=gap)

    def target(self, identity, *, at, quantity, entry, target, route):
        from datetime import datetime, timedelta
        from decimal import Decimal
        from src.trading.market.target_pressure import pressure_from_snapshot
        from src.trading.market.profit_stagnation_quote import executable_quote
        from src.trading.order.profit_stagnation import positive_net_stagnation

        selected = self.contract["selected_programs"]
        if selected["status"] == "native_target_only":
            return target
        if self.guard.get("programme_source_overflow"):
            raise ValueError("native_programme_tick_capacity_gap")
        if self.last_tick is None:
            raise ValueError("native_programme_write_guard_timeline_missing")
        max_gap = self.model.get("maximum_programme_tick_gap_ms")
        if (
            type(max_gap) is not int
            or max_gap <= 0
            or (
                at
                - datetime.fromisoformat(
                    self.last_tick.get("through_at", self.last_tick["at"])
                )
            ).total_seconds()
            * 1000
            > max_gap
            or self.last_tick.get("maximum_gap_ms", max_gap) > max_gap
        ):
            raise ValueError("native_programme_write_guard_timeline_coverage_gap")
        action = self.pending.get(identity)
        if action and at >= action["ack"]:
            if self.last_tick.get("permitted") is not True:
                raise ValueError("programme_guard_changed_during_pending_action")
            self.pending.pop(identity)
            if action["action"] == "profit_replace":
                from src.trading.order.profit_stagnation import positive_net_stagnation

                policy = selected["programs"]["profit_stagnation"]["policy"]
                books = list(self.books.get(route, []))
                if (
                    not books
                    or sum(
                        q
                        for _, p, q in books[-1]["bid_levels"]
                        if p >= action["target"]
                    )
                    < quantity
                ):
                    raise ValueError("profit_replace_full_fill_ack_scope_not_supported")
                worst = next(
                    (p for _, p, q in reversed(books[-1]["bid_levels"]) if q), None
                )
                # Checking the worst visible bid is conservative and cannot authorise a loss.
                if worst is None or Decimal(str(worst)) * (
                    1 - Decimal(str(policy["slippage_bps"])) / 10000
                ) <= Decimal(str(entry)) * (
                    1 + Decimal(str(policy["round_trip_cost_pct"])) / 100
                ):
                    raise ValueError(
                        "profit_replace_native_net_guard_changed_before_ack"
                    )
            self.events.append(
                dict(
                    at=at.isoformat(),
                    action=action["action"],
                    price=action["target"],
                    quantity=quantity,
                )
            )
            return action["target"]
        if action or not self.is_tick or self.last_tick.get("permitted") is not True:
            return target
        depths = list(self.books.get(route, []))
        trades = list(self.trades.get(route, []))
        if not depths:
            # Original executable_quote fails closed and keeps protection.
            return target
        latest = depths[-1]
        epoch = latest["sequence_epoch"]

        def live(r, depth):
            d = dict(
                r,
                received_at_ms=int(
                    datetime.fromisoformat(r["local_receive_timestamp"]).timestamp()
                    * 1000
                ),
                transport_epoch=r["sequence_epoch"],
                route_sequence=r.get("series_sequence", r["source_sequence"]),
            )
            if depth:
                d["ask_levels"] = [
                    dict(price=p, quantity=q) for _, p, q in r["ask_levels"]
                ]
                d["bid_levels"] = [
                    dict(price=p, quantity=q) for _, p, q in r["bid_levels"]
                ]
            else:
                d.update(price=r["trade_price"], volume=r["trade_qty"])
            return d

        receipts = {}
        for kind, rows in (("0D", depths), ("0B", trades)):
            if rows:
                r = rows[-1]
                receipts[kind] = dict(
                    item=r["item"],
                    transport_epoch=r["sequence_epoch"],
                    route_sequence=r.get("series_sequence", r["source_sequence"]),
                    observed_epoch=datetime.fromisoformat(
                        r["local_receive_timestamp"]
                    ).timestamp(),
                    best_bid=r.get("best_bid"),
                    best_ask=r.get("best_ask"),
                )
        snapshot = dict(
            stocks={
                "005930": dict(
                    market_data_transport_epoch=epoch,
                    machine_confirmation_routes={
                        route: dict(
                            realtime_types=receipts,
                            recent_depth=[live(r, True) for r in depths],
                            recent_trades=[live(r, False) for r in trades],
                            source_complete=True,
                            sequence_authority="validated_canonical_local_projection_not_exchange_completeness",
                        )
                    },
                )
            }
        )
        try:
            quote = executable_quote(
                symbol="005930",
                route=route,
                quantity=quantity,
                now=at,
                snapshot=snapshot,
            )
        except (ValueError, KeyError, TypeError):
            self.windows.pop(identity, None)
            return target
        programs = selected["programs"]
        name, price = None, None
        if programs["target_ratchet"]["selected"]:
            policy = programs["target_ratchet"]["policy"]
            try:
                signal = pressure_from_snapshot(
                    snapshot,
                    symbol="005930",
                    route=route,
                    quantity=quantity,
                    target_price=target,
                    now=at,
                )
                if signal["decision"] == "RAISE_ONE_TICK" and Decimal(
                    str(quote["executable_bid"])
                ) * (1 - Decimal(str(policy["slippage_bps"])) / 10000) > Decimal(
                    str(entry)
                ) * (
                    1 + Decimal(str(policy["round_trip_cost_pct"])) / 100
                ):
                    name, price = "target_amend", signal["next_price"]
            except (ValueError, KeyError, TypeError):
                pass  # Exact native KEEP_TARGET source fallback, no pressure claim.
        if (
            name is None
            and programs["profit_stagnation"]["selected"]
            and quote["executable_bid"] < target
        ):
            policy = programs["profit_stagnation"]["policy"]
            decision, window = positive_net_stagnation(
                identity=f"{self.contract['sha256']}:{identity}:{route}:{epoch}:{quantity}:{entry}",
                now=at.timestamp(),
                entry_price=entry,
                quantity=quantity,
                previous=self.windows.get(identity),
                **{
                    k: quote[k]
                    for k in (
                        "quote_at",
                        "quote_id",
                        "executable_bid",
                        "available_quantity",
                    )
                },
                **{
                    k: policy[k]
                    for k in (
                        "round_trip_cost_pct",
                        "slippage_bps",
                        "min_sec",
                        "max_profit_move",
                        "max_peak_improve",
                        "max_observation_gap_sec",
                    )
                },
            )
            self.windows[identity] = window
            if decision["should_exit"]:
                name, price = "profit_replace", int(quote["executable_bid"])
        if name:
            latency = self.model.get(name + "_latency_ms")
            if type(latency) is not int or latency < 0:
                raise ValueError(
                    "independent_" + name + "_action_model_witness_missing"
                )
            # The old target stays protected until its independently measured ack.
            # Full fill before ack wins. Partial races are outside this full-fill adapter.
            self.pending[identity] = dict(
                ack=at + timedelta(milliseconds=latency), target=price, action=name
            )
        return target


def programme_clock_parameters(native_state):
    from datetime import datetime

    ticks = native_state.get("programme_ticks", [])
    gaps = [r.get("maximum_gap_ms", 0) for r in ticks]
    return dict(
        maximum_programme_tick_gap_ms=(
            max(gaps) if gaps and max(gaps) > 0 and min(gaps) >= 0 else None
        ),
        **native_state.get("programme_action_clocks", {}),
    )


def record_programme_transition(payload, *, clock):
    """Local original owner phase clocks; no broker/exchange timing inference."""
    clocks = payload.setdefault("operating_action_clocks", {})
    phase = payload.get("phase")
    if phase == "CANCEL":
        clocks.setdefault("cancel_started_at_ms", clock())
    if phase == "SELL" and type(clocks.get("cancel_started_at_ms")) is int:
        elapsed = clock() - clocks["cancel_started_at_ms"]
        if elapsed >= 0:
            clocks.setdefault("profit_replace_latency_ms", elapsed)
    if phase == "TARGET":
        clocks.pop("cancel_started_at_ms", None)


def native_target_touch_latency(contract, native_state, points):
    """Observed full-marketability to owner-local terminal clock, not queue rank.

    Only unchanged native targets identify this latency. Amend/replacement paths
    are independent action holdout witnesses; they cannot fit their own queue.
    """
    from datetime import datetime

    waits = []
    if contract.get("owner") == "episode":
        for leg in native_state.get("legs", []):
            if leg.get("holding_target_history") or leg.get("profit_stagnation_exit"):
                continue
            if not leg.get("target_filled_at") or not leg.get("target_price"):
                # Contract target is valid only for an unchanged full-fill leg.
                price = _native_target_price(contract, leg.get("fill_price", 0))
            else:
                price = leg["target_price"]
            end = leg.get("target_filled_at")
            qty = leg.get("quantity")
            if not end or not qty:
                continue
            start = (native_state.get("order_clocks") or {}).get(
                leg["leg_id"] + ":target_submitted"
            )
            eligible = [
                p
                for p in points
                if (start is None or p["at"] >= start)
                and p["at"] <= end
                and sum(q for bid, q in p["bid_levels"] if bid >= price) >= qty
            ]
            if eligible:
                waits.append(
                    int(
                        (
                            datetime.fromisoformat(end)
                            - datetime.fromisoformat(eligible[0]["at"])
                        ).total_seconds()
                        * 1000
                    )
                )
    else:
        for order in native_state.get("orders", []):
            if (
                order.get("side") != "SELL"
                or order.get("status") != "FILLED"
                or order.get("profit_stagnation_root")
                or order.get("amendment_parent_order_no")
            ):
                continue
            end = order.get("timing_terminal_fill_observed_at")
            start = order.get("submitted_at")
            price = order.get("limit_price") or order.get("fill_price")
            qty = order.get("filled_qty")
            if not all((end, start, price, qty)):
                continue
            eligible = [
                p
                for p in points
                if start <= p["at"] <= end
                and sum(q for bid, q in p["bid_levels"] if bid >= price) >= qty
            ]
            if eligible:
                waits.append(
                    int(
                        (
                            datetime.fromisoformat(end)
                            - datetime.fromisoformat(eligible[0]["at"])
                        ).total_seconds()
                        * 1000
                    )
                )
    return max(waits) if waits and min(waits) >= 0 else None


def frozen_operating_cost_contract():
    """Numeric loaded owner cost with executable-source hashes; no secrets."""
    from pathlib import Path
    import hashlib
    from src.engine import trade_profit
    from src.utils import constants

    configured = getattr(constants.TRADING_RULES, "TRADE_COST_RATE", None)
    if (
        type(configured) not in (float, int)
        or not math.isfinite(configured)
        or not 0 <= configured < 1
        or trade_profit.get_trade_cost_rate() != configured
    ):
        raise ValueError("loaded_operating_cost_configuration_missing_or_fallback")
    return _seal(
        dict(
            rate=configured,
            calculation="sell_notional_times_rate_once",
            source="src.engine.trade_profit.get_trade_cost_rate / loaded TRADING_RULES",
            source_code_sha256={
                Path(m.__file__)
                .name: hashlib.sha256(Path(m.__file__).read_bytes())
                .hexdigest()
                for m in (trade_profit, constants)
            },
            broker_settlement=False,
            missing_broker_fees_reconstructed=False,
        )
    )


def refresh_completed_operating_actuals(cases, *, target_date, state_dir):
    """Bounded original owner checkpoints refresh ACTUAL terminals only.

    Carry completion is not retrofitted as a counterfactual exit or market path.
    Frozen root identity and as-of knowledge bound this original owner join.
    """
    from pathlib import Path
    from src.engine.monitoring.research_closed_loop import read_object
    from src.engine.monitoring.samsung_machine_entry_tuning import MACHINE_FILES

    fresh = {}
    errors = []
    for name in (*MACHINE_FILES.values(), "widget_signal_auto_trade_state.json"):
        try:
            path = Path(state_dir) / name
            if not path.exists():
                continue
            state = read_object(path, limit=16 * 1024 * 1024)
            states = [state, *((state.get("symbols") or {}).values())]
            for item in states:
                for opp in (
                    *((item.get("timing_operating_opportunities") or {}).values()),
                    *((item.get("timing_operating_terminal_history") or {}).values()),
                ):
                    c = opp.get("contract") or {}
                    native = opp.get("native_state") or {}
                    if _sealed(c) and str(native.get("observed_at", ""))[:10] <= str(
                        target_date
                    ):
                        prior = fresh.get(c["sha256"])
                        if prior and prior != native:
                            errors.append(
                                "native_checkpoint_root_identity_conflict:"
                                + c["sha256"]
                            )
                            fresh[c["sha256"]] = None
                        elif c["sha256"] not in fresh:
                            fresh[c["sha256"]] = native
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(name + ":" + str(exc))
    updated = []
    for source, decisions in cases:
        c = source.get("contract") or {}
        native = fresh.get(c.get("sha256"))
        if c.get("sha256") in fresh and fresh[c["sha256"]] is None and _sealed(source):
            source = _seal(
                source
                | dict(
                    actual=None,
                    actual_disposition="source_gap",
                    actual_refresh_blocker="native_checkpoint_root_identity_conflict",
                )
            )
        if native and _sealed(source) and c.get("source_date", "") <= str(target_date):
            actual = (
                widget_actual_projection
                if c.get("owner") == "widget"
                else native_actual_projection
            )(c, native, source["points"])
            if actual:
                source = _seal(
                    source
                    | dict(
                        actual=actual,
                        actual_disposition="completed",
                        actual_refresh_basis="original_owner_checkpoint_exact_frozen_root_not_cf_exit",
                    )
                )
        updated.append((source, decisions))
    return updated, errors


from functools import lru_cache


def frozen_native_owner_code():
    return dict(_native_owner_code_signature())


@lru_cache(maxsize=1)
def _native_owner_code_signature():
    """Immutable original owner/guard kernels, hashed once per process."""
    import hashlib
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    paths = (
        "src/trading/order/regular_two_leg_machine.py",
        "src/trading/samsung_morning_one_share/machine.py",
        "src/trading/widget_auto_trade/engine.py",
        "src/trading/market/micro_confirmation.py",
        "src/trading/order/target_ratchet.py",
        "src/trading/order/profit_stagnation_owners.py",
        "src/trading/order/profit_stagnation_exit.py",
        "src/engine/risk/manual_control_exclusion.py",
        "src/engine/risk/market_weakness_entry_guard.py",
    )
    return tuple(
        (name, hashlib.sha256((root / name).read_bytes()).hexdigest()) for name in paths
    )


def matching_native_legs(contract, legs):
    shapes = {
        (l["leg_id"], l["route"]): l["quantity"] for l in contract.get("plan", [])
    }
    matched = [l for l in legs if (l.get("leg_id"), l.get("route")) in shapes]
    if (
        len(matched) != len(shapes)
        or len({(l.get("leg_id"), l.get("route")) for l in matched}) != len(shapes)
        or any(l.get("quantity") != shapes[(l["leg_id"], l["route"])] for l in matched)
    ):
        return None
    return matched


def project_widget_registry_terminal(owner, order):
    """Add exact local custody-registry facts to a COPY of the native row."""
    if not order.get("order_no") or not order.get("filled_qty"):
        return
    row = bounded_custody_terminal_lookup(
        owner,
        order_date=order.get("order_date"),
        broker_order_no=order["order_no"],
        filled_qty=order["filled_qty"],
    )
    if not row or any(
        row.get(k) != v
        for k, v in {
            "owner_type": "widget_auto_trade",
            "owner_id": order.get("owner_id"),
            "position_id": order.get("owner_position_id"),
            "symbol": "005930",
            "side": order.get("side"),
            "intent_id": order.get("owner_registry_intent_id"),
            "filled_qty": order.get("filled_qty"),
        }.items()
    ):
        return
    q = row["filled_qty"]
    amount = row.get("fill_amount")
    at = row.get("fill_observed_at_kst")
    if type(amount) is int and amount > 0 and at:
        order.update(
            fill_price=amount / q,
            fill_amount_krw=amount,
            timing_first_fill_observed_at=order.get("timing_first_fill_observed_at")
            or at,
        )
        if q == order.get("requested_qty"):
            order["timing_terminal_fill_observed_at"] = at


def bounded_custody_terminal_lookup(owner, *, order_date, broker_order_no, filled_qty):
    """Reuse exact immutable terminals; no telemetry full-ledger poll loop."""
    registry = owner.owner_registry
    path = getattr(registry, "path", None)
    stamp = None
    if path is not None:
        st = path.stat()
        if st.st_size > 64 * 1024 * 1024:
            raise ValueError(
                "custody_terminal_telemetry_lookup_budget_requires_existing_owner_index"
            )
        stamp = (st.st_size, st.st_mtime_ns)
    cache = getattr(owner, "_timing_terminal_rows", None)
    if cache is None:
        cache = {}
        owner._timing_terminal_rows = cache
    key = (str(order_date), broker_order_no, filled_qty)
    if key in cache:
        previous, row = cache[key]
        if previous == stamp or (
            row
            and row.get("filled_qty") == row.get("quantity")
            and row.get("fill_amount")
            and row.get("fill_observed_at_kst")
        ):
            return row
    row = registry.order_owner(order_date=order_date, broker_order_no=broker_order_no)
    if len(cache) >= 1024:
        cache.clear()
    cache[key] = (stamp, row)
    return row


def retain_native_terminal_history(state):
    """Compact bounded checkpoint history survives the original date reset.

    This records original facts only. Native order state/guards are untouched;
    the existing timing report persists mature exact-root actuals cumulatively.
    """
    from copy import deepcopy

    history = dict(state.get("timing_operating_terminal_history") or {})
    for opportunity in (state.get("timing_operating_opportunities") or {}).values():
        c, native = (
            opportunity.get("contract") or {},
            opportunity.get("native_state") or {},
        )
        legs = native.get("legs") or []
        if _sealed(c) and legs and all(l.get("status") == "COMPLETE" for l in legs):
            history[c["sha256"]] = deepcopy(opportunity)
    return dict(
        sorted(
            history.items(),
            key=lambda item: str(
                item[1].get("native_state", {}).get("observed_at", "")
            ),
        )[-128:]
    )


def read_native_actual_history(report_dir, *, target_date):
    """Read one bounded existing report generation, never raw or another SELL."""
    from pathlib import Path
    from src.engine.monitoring.research_closed_loop import read_object

    names = sorted(
        Path(report_dir).glob("machine_entry_timing_tuning_????-??-??.json"),
        reverse=True,
    )
    for path in names:
        if path.stem[-10:] > str(target_date):
            continue
        try:
            report = read_object(path, limit=64 * 1024 * 1024)
            history = report.get("native_actual_completion_history")
            if history is None:
                return {}, []
            if (
                report.get("target_date") != path.stem[-10:]
                or report.get("schema") != "machine_entry_timing_tuning_report_v3"
                or not _sealed(history)
                or history.get("schema") != "native_actual_completion_history_v1"
            ):
                raise ValueError("native_actual_history_integrity_invalid")
            completed = history.get("completed_by_contract") or {}
            if not isinstance(completed, dict):
                raise ValueError("native_actual_history_mapping_invalid")
            for identity, actual in completed.items():
                if (
                    not isinstance(identity, str)
                    or len(identity) != 64
                    or (
                        actual is not None
                        and (
                            not _sealed(actual)
                            or actual.get("contract_sha256") != identity
                        )
                    )
                ):
                    raise ValueError("native_actual_history_root_invalid")
            return completed, []
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return {}, ["native_actual_history:" + str(exc)]
    return {}, []


def restore_native_actual_history(cases, history, *, target_date):
    """Restore sealed exact-root ACTUAL facts without touching CF source paths."""
    restored = []
    for source, decisions in cases:
        c = source.get("contract") or {}
        actual = history.get(c.get("sha256"))
        if c.get("sha256") in history and actual is None and _sealed(source):
            source = _seal(
                source
                | dict(
                    actual=None,
                    actual_disposition="source_gap",
                    actual_refresh_blocker="native_actual_history_identity_conflict",
                )
            )
        if (
            _sealed(source)
            and _sealed(c)
            and _sealed(actual)
            and actual.get("status") == "COMPLETED"
            and actual.get("origin") == "real"
            and actual.get("exact_lineage") is True
            and actual.get("contract_sha256") == c["sha256"]
            and actual.get("knowledge_date", "9999") <= str(target_date)
            and not source.get("actual_refresh_blocker")
        ):
            current = source.get("actual")
            economic_identity = (
                "contract_sha256",
                "quantity",
                "filled_quantity",
                "net_pnl_krw",
                "capital_krw_minutes",
                "reserve_krw_minutes",
                "closed_at_ms",
                "cost_provenance",
            )
            if _sealed(current) and any(
                current.get(k) != actual.get(k) for k in economic_identity
            ):
                source = _seal(
                    source
                    | dict(
                        actual=None,
                        actual_disposition="source_gap",
                        actual_refresh_blocker="native_actual_history_identity_conflict",
                    )
                )
            elif current is None or actual["knowledge_date"] < current.get(
                "knowledge_date", "9999"
            ):
                source = _seal(
                    source
                    | dict(
                        actual=actual,
                        actual_disposition="completed",
                        actual_refresh_basis="sealed_exact_owner_completion_history_not_cf_exit",
                    )
                )
        restored.append((source, decisions))
    return restored
