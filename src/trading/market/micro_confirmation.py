"""Causal, source-only per-signal micro confirmation decisions.

The evaluator consumes already-normalized checkpoint evidence.  It has no
market-data subscription, broker, order, quantity, price, target, or exit
authority.  Both offline replay and a future reviewed runtime observer can use
the same deterministic state transition without allowing future observations
to leak into an earlier checkpoint.
"""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping

from src.trading.order.tick_utils import get_tick_size, move_price_by_ticks

DYNAMIC_CONFIRMATION_SCHEMA = "machine_dynamic_micro_confirmation_replay_v1"
DYNAMIC_CONFIRMATION_POLICY_ID = "machine_dynamic_micro_confirmation_policy_v1"
CHECKPOINTS_SEC = (0, 1, 3, 5)

DYNAMIC_CONFIRMATION_METRIC_CONTRACT = {
    "metric_role": "per_signal_causal_micro_confirmation_source_only_replay",
    "decision_authority": "source_only_confirmation_replay_no_order_authority",
    "window_policy": "past_only_at_each_0_1_3_5_second_checkpoint",
    "sample_floor": (
        "five_observed_dates_20_unique_lifecycles_20_completed_outcomes_"
        "95pct_paired_coverage_before_any_separate_preopen_review"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "secondary_economic_guards": [
        "notional_weighted_ev_pct",
        "modeled_net_profit_uplift_krw",
        "net_profit_per_capital_minute_pct",
        "candidate_p10_pct",
    ],
    "source_quality_gate": (
        "exact_symbol_venue_session_sequence_epoch;causal_checkpoint_cutoff;"
        "eligible_0b_trade_and_0d_depth;fresh_uncrossed_depth_backed_bbo"
    ),
    "forbidden_uses": [
        "live_or_same_day_order_decision",
        "standalone_signal_creation",
        "broker_order_submit_cancel_or_reprice",
        "price_quantity_target_stop_holding_or_exit_mutation",
        "owner_custody_or_order_identity_sharing",
        "future_first_hit_or_terminal_outcome_as_checkpoint_input",
        "missing_source_imputation",
        "provider_bot_cap_threshold_or_hard_safety_change",
    ],
}


@dataclass(frozen=True, slots=True)
class DynamicConfirmationPolicy:
    minimum_bid_return_bps: float = 0.0
    minimum_trade_backed_ratio: float = 0.5
    maximum_supportive_refill_ratio: float = 0.5
    adverse_bid_return_bps: float = -10.0
    adverse_refill_ratio: float = 1.0
    maximum_quote_age_ms: int = 1_000
    checkpoints_sec: tuple[int, ...] = CHECKPOINTS_SEC
    policy_id: str = DYNAMIC_CONFIRMATION_POLICY_ID

    def __post_init__(self) -> None:
        numeric_values = (
            self.minimum_bid_return_bps,
            self.minimum_trade_backed_ratio,
            self.maximum_supportive_refill_ratio,
            self.adverse_bid_return_bps,
            self.adverse_refill_ratio,
        )
        if any(
            isinstance(value, bool) or not math.isfinite(float(value))
            for value in numeric_values
        ):
            raise ValueError("dynamic confirmation thresholds must be finite")
        if self.checkpoints_sec != CHECKPOINTS_SEC:
            raise ValueError("dynamic confirmation checkpoints must be 0/1/3/5")
        if not 0.0 <= self.minimum_trade_backed_ratio <= 1.0:
            raise ValueError("minimum trade-backed ratio must be within [0, 1]")
        if not 0.0 <= self.maximum_supportive_refill_ratio < 1.0:
            raise ValueError("supportive refill ratio must be within [0, 1)")
        if self.adverse_refill_ratio < 1.0:
            raise ValueError("adverse refill ratio must be at least 1")
        if self.adverse_bid_return_bps >= self.minimum_bid_return_bps:
            raise ValueError("adverse bid threshold must be below supportive bid")
        if (
            isinstance(self.maximum_quote_age_ms, bool)
            or not isinstance(self.maximum_quote_age_ms, int)
            or self.maximum_quote_age_ms <= 0
        ):
            raise ValueError("maximum quote age must be a positive integer")

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checkpoints_sec"] = list(self.checkpoints_sec)
        return payload


DEFAULT_DYNAMIC_CONFIRMATION_POLICY = DynamicConfirmationPolicy()


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def modeled_dynamic_target_price(
    *,
    owner: str,
    baseline_fill_price: Any,
    owner_target_price: Any,
    checkpoint_ask: Any,
    widget_take_profit: bool,
) -> float | None:
    """Preserve the existing owner's target ratio/ticks at a replay entry price."""

    baseline = _finite(baseline_fill_price)
    target = _finite(owner_target_price)
    entry = _finite(checkpoint_ask)
    if (
        owner not in {"widget", "episode"}
        or not isinstance(widget_take_profit, bool)
        or baseline is None
        or baseline <= 0
        or target is None
        or target <= baseline
        or entry is None
        or entry <= 0
    ):
        return None
    if owner == "episode":
        if (
            not baseline.is_integer()
            or not target.is_integer()
            or not entry.is_integer()
        ):
            return None
        current = int(baseline)
        target_ticks: int | None = None
        for ticks in range(1, 101):
            current = move_price_by_ticks(current, 1)
            if current == int(target):
                target_ticks = ticks
                break
            if current > int(target):
                return None
        if target_ticks is None:
            return None
        return float(move_price_by_ticks(int(entry), target_ticks))
    if widget_take_profit:
        if not entry.is_integer():
            return None
        raw_target = entry * (target / baseline)
        integer_target = math.ceil(raw_target)
        tick = get_tick_size(integer_target)
        return float(((integer_target + tick - 1) // tick) * tick)
    return target


def build_dynamic_micro_confirmation_checkpoints(
    *,
    anchor_bbo: Any,
    future_bbo: Any,
    checkpoint_ask_depletion: Any,
    anchor_id: Any,
    signal_decision_at: Any,
    symbol: Any,
    expected_venues: Any,
    expected_session_buckets: Any,
    owner: str,
    baseline_fill_price: Any,
    owner_entry_limit_price: Any,
    owner_target_price: Any,
    round_trip_cost_pct: Any,
    widget_take_profit: bool,
) -> dict[int, dict[str, Any]]:
    """Build causal replay inputs from persisted BBO and 0B/0D parents.

    Both the attribution producer and its postclose consumer call this adapter.
    That makes a self-consistent replay insufficient unless it also matches the
    original source rows at every evaluated checkpoint.
    """

    anchor = anchor_bbo if isinstance(anchor_bbo, Mapping) else {}
    horizons = future_bbo if isinstance(future_bbo, Mapping) else {}
    causal_anchor_bid = _finite(anchor.get("best_bid"))
    causal_anchor_epoch = anchor.get("sequence_epoch")
    entry_limit = _finite(owner_entry_limit_price)
    cost_pct = _finite(round_trip_cost_pct)
    checkpoint_bundle = (
        checkpoint_ask_depletion
        if isinstance(checkpoint_ask_depletion, Mapping)
        else {}
    )
    checkpoint_reports = (
        checkpoint_bundle.get("checkpoint_reports")
        if isinstance(checkpoint_bundle.get("checkpoint_reports"), Mapping)
        else {}
    )
    bundle_contract_valid = bool(
        checkpoint_bundle.get("schema")
        == "machine_entry_confirmation_checkpoint_ask_depletion_v1"
        and checkpoint_bundle.get("causal_past_only") is True
        and checkpoint_bundle.get("future_outcome_input_used") is False
        and checkpoint_bundle.get("runtime_effect") is False
        and checkpoint_bundle.get("allowed_runtime_apply") is False
        and checkpoint_bundle.get("broker_order_forbidden") is True
    )
    anchor_id_text = str(anchor_id or "")
    signal_at_text = str(signal_decision_at or "")
    symbol_text = str(symbol or "")
    venues = {str(value or "") for value in expected_venues or () if str(value or "")}
    sessions = {
        str(value or "") for value in expected_session_buckets or () if str(value or "")
    }
    try:
        signal_at = datetime.fromisoformat(signal_at_text)
    except ValueError:
        signal_at = None
    if signal_at is not None and signal_at.utcoffset() is None:
        signal_at = None

    def ask_horizon(report: Any, checkpoint_sec: int) -> Mapping[str, Any] | None:
        rows = report.get("horizons") if isinstance(report, Mapping) else None
        if not isinstance(rows, list):
            return None
        rows = [row for row in rows if isinstance(row, Mapping)]
        return rows[0] if len(rows) == 1 else None

    checkpoints: dict[int, dict[str, Any]] = {}
    for checkpoint_sec in CHECKPOINTS_SEC:
        bbo = (
            anchor
            if checkpoint_sec == 0
            else (
                horizons.get(str(checkpoint_sec))
                if isinstance(horizons.get(str(checkpoint_sec)), Mapping)
                else {}
            )
        )
        ask_report = checkpoint_reports.get(str(checkpoint_sec))
        ask = ask_horizon(ask_report, checkpoint_sec)
        ask_context = (
            ask_report.get("context")
            if isinstance(ask_report, Mapping)
            and isinstance(ask_report.get("context"), Mapping)
            else {}
        )
        bbo_epoch = bbo.get("sequence_epoch")
        ask_epoch = ask_context.get("sequence_epoch")
        binding = (
            ask_report.get("decision_anchor_binding")
            if isinstance(ask_report, Mapping)
            and isinstance(ask_report.get("decision_anchor_binding"), Mapping)
            else {}
        )
        checkpoint_report_contract_valid = bool(
            bundle_contract_valid
            and isinstance(ask_report, Mapping)
            and ask_report.get("schema") == "scalp_micro_reversion_ask_depletion_v2"
            and ask_report.get("runtime_effect") is False
            and ask_report.get("trading_runtime_effect") is False
            and ask_report.get("trading_decision_effect") is False
            and ask_report.get("actual_order_submitted") is False
            and ask_report.get("broker_order_forbidden") is True
            and anchor_id_text
            and signal_at_text
            and symbol_text
            and venues
            and sessions
            and binding.get("decision_anchor_id") == anchor_id_text
            and binding.get("decision_anchor_at") == signal_at_text
            and binding.get("checkpoint_sec") == checkpoint_sec
            and signal_at is not None
            and binding.get("checkpoint_at")
            == (signal_at + timedelta(seconds=checkpoint_sec)).isoformat()
            and isinstance(ask, Mapping)
            and binding.get("window_horizon_ms") == ask.get("horizon_ms")
            and binding.get("future_outcome_input_used") is False
            and ask_context.get("symbol") == symbol_text
            and ask_context.get("venue") in venues
            and ask_context.get("session_bucket") in sessions
        )
        same_causal_epoch = bool(
            isinstance(causal_anchor_epoch, int)
            and not isinstance(causal_anchor_epoch, bool)
            and causal_anchor_epoch > 0
            and isinstance(bbo_epoch, int)
            and not isinstance(bbo_epoch, bool)
            and bbo_epoch > 0
            and isinstance(ask_epoch, int)
            and not isinstance(ask_epoch, bool)
            and ask_epoch > 0
            and bbo_epoch == causal_anchor_epoch == ask_epoch
        )
        source_eligible = bool(
            bbo.get("observed") is True
            and isinstance(ask, Mapping)
            and ask.get("eligible_for_feature_ablation") is True
            and same_causal_epoch
            and checkpoint_report_contract_valid
            and causal_anchor_bid is not None
            and causal_anchor_bid > 0
        )
        checkpoint_bid = _finite(bbo.get("best_bid"))
        checkpoint_ask = _finite(bbo.get("best_ask"))
        bid_return_bps = (
            round((checkpoint_bid / causal_anchor_bid - 1.0) * 10_000.0, 6)
            if checkpoint_bid is not None
            and causal_anchor_bid is not None
            and causal_anchor_bid > 0
            else None
        )
        modeled_target = modeled_dynamic_target_price(
            owner=owner,
            baseline_fill_price=baseline_fill_price,
            owner_target_price=owner_target_price,
            checkpoint_ask=checkpoint_ask,
            widget_take_profit=widget_take_profit,
        )
        net_edge_after_cost_bps = (
            round(
                (modeled_target / checkpoint_ask - 1.0) * 10_000.0 - cost_pct * 100.0,
                6,
            )
            if modeled_target is not None
            and modeled_target > 0
            and checkpoint_ask is not None
            and checkpoint_ask > 0
            and cost_pct is not None
            and cost_pct >= 0
            else None
        )
        checkpoints[checkpoint_sec] = {
            "checkpoint_sec": checkpoint_sec,
            "causal_past_only": True,
            "future_outcome_input_used": False,
            "source_quality_status": "eligible" if source_eligible else "source_gap",
            "bbo_observed": bbo.get("observed"),
            "depth_backed": bbo.get("depth_backed"),
            "same_sequence_epoch": same_causal_epoch,
            "sequence_epoch": bbo_epoch,
            "best_bid": bbo.get("best_bid"),
            "best_ask": bbo.get("best_ask"),
            "bid_return_bps": bid_return_bps,
            "bid_return_reference": "causal_pre_signal_best_bid",
            "spread_bps": bbo.get("spread_bps"),
            "quote_age_ms": (
                bbo.get("quote_age_from_signal_ms")
                if checkpoint_sec == 0
                else bbo.get("quote_age_from_horizon_ms")
            ),
            "net_edge_after_cost_bps": net_edge_after_cost_bps,
            "modeled_target_price": modeled_target,
            "owner_price_feasible": (
                checkpoint_ask <= entry_limit
                if checkpoint_ask is not None
                and checkpoint_ask > 0
                and entry_limit is not None
                and entry_limit > 0
                else None
            ),
            "aggressive_buy_trade_backed_ratio": (
                ask.get("aggressive_buy_trade_backed_ratio")
                if isinstance(ask, Mapping)
                else None
            ),
            "refill_ratio": (
                ask.get("refill_ratio") if isinstance(ask, Mapping) else None
            ),
            "downward_reprice_observed": (
                ask.get("downward_reprice_observed")
                if isinstance(ask, Mapping)
                else None
            ),
            "ask_depletion_horizon_ms": (
                ask.get("horizon_ms") if isinstance(ask, Mapping) else None
            ),
        }
    return checkpoints


def _checkpoint_status(
    raw: Any, *, checkpoint_sec: int, policy: DynamicConfirmationPolicy
) -> dict[str, Any]:
    reasons: list[str] = []
    row = raw if isinstance(raw, Mapping) else {}
    declared_checkpoint = row.get("checkpoint_sec")
    if (
        isinstance(declared_checkpoint, bool)
        or not isinstance(declared_checkpoint, int)
        or declared_checkpoint != checkpoint_sec
    ):
        reasons.append("checkpoint_identity_invalid")
    if row.get("causal_past_only") is not True:
        reasons.append("causal_past_only_not_proven")
    if row.get("future_outcome_input_used") is not False:
        reasons.append("future_outcome_input_contract_invalid")
    if row.get("source_quality_status") != "eligible":
        reasons.append("checkpoint_source_quality_ineligible")
    if row.get("bbo_observed") is not True:
        reasons.append("checkpoint_bbo_missing")
    if row.get("depth_backed") is not True:
        reasons.append("checkpoint_depth_not_backed")
    if row.get("same_sequence_epoch") is not True:
        reasons.append("checkpoint_sequence_epoch_invalid")
    sequence_epoch = row.get("sequence_epoch")
    if (
        isinstance(sequence_epoch, bool)
        or not isinstance(sequence_epoch, int)
        or sequence_epoch <= 0
    ):
        reasons.append("checkpoint_sequence_epoch_invalid")
    best_bid = _finite(row.get("best_bid"))
    best_ask = _finite(row.get("best_ask"))
    bid_return = _finite(row.get("bid_return_bps"))
    bid_return_reference = row.get("bid_return_reference")
    spread_bps = _finite(row.get("spread_bps"))
    quote_age_ms = _finite(row.get("quote_age_ms"))
    modeled_target_price = _finite(row.get("modeled_target_price"))
    net_edge_after_cost_bps = _finite(row.get("net_edge_after_cost_bps"))
    trade_backed = _finite(row.get("aggressive_buy_trade_backed_ratio"))
    refill = _finite(row.get("refill_ratio"))
    downward_reprice = row.get("downward_reprice_observed")
    owner_price_feasible = row.get("owner_price_feasible")
    if best_bid is None or best_ask is None or best_bid <= 0 or best_ask < best_bid:
        reasons.append("checkpoint_bbo_contract_invalid")
    if bid_return is None:
        reasons.append("checkpoint_bid_return_missing")
    if bid_return_reference != "causal_pre_signal_best_bid":
        reasons.append("checkpoint_bid_return_reference_invalid")
    expected_spread_bps = (
        (best_ask - best_bid) / best_bid * 10_000.0
        if best_bid is not None
        and best_ask is not None
        and best_bid > 0
        and best_ask >= best_bid
        else None
    )
    if (
        spread_bps is None
        or spread_bps < 0
        or expected_spread_bps is None
        or not math.isclose(spread_bps, expected_spread_bps, abs_tol=1e-4)
    ):
        reasons.append("checkpoint_spread_contract_invalid")
    if (
        quote_age_ms is None
        or quote_age_ms < 0
        or quote_age_ms > policy.maximum_quote_age_ms
    ):
        reasons.append("checkpoint_quote_stale_or_invalid")
    if net_edge_after_cost_bps is None:
        reasons.append("checkpoint_net_edge_missing")
    if (
        modeled_target_price is None
        or best_ask is None
        or modeled_target_price <= best_ask
    ):
        reasons.append("checkpoint_modeled_target_invalid")
    if trade_backed is None or not 0.0 <= trade_backed <= 1.0:
        reasons.append("checkpoint_trade_backing_invalid")
    if refill is None or refill < 0.0:
        reasons.append("checkpoint_refill_invalid")
    if not isinstance(downward_reprice, bool):
        reasons.append("checkpoint_reprice_state_invalid")
    if not isinstance(owner_price_feasible, bool):
        reasons.append("checkpoint_owner_price_feasibility_invalid")

    source_eligible = not reasons
    adverse = bool(
        source_eligible
        and (
            float(bid_return) <= policy.adverse_bid_return_bps
            or float(refill) >= policy.adverse_refill_ratio
            or downward_reprice is True
        )
    )
    supportive = bool(
        source_eligible
        and not adverse
        and float(bid_return) >= policy.minimum_bid_return_bps
        and float(trade_backed) >= policy.minimum_trade_backed_ratio
        and float(refill) < policy.maximum_supportive_refill_ratio
        and float(net_edge_after_cost_bps) > 0.0
        and owner_price_feasible is True
    )
    state = (
        "SOURCE_GAP"
        if not source_eligible
        else ("ADVERSE" if adverse else ("SUPPORTIVE" if supportive else "AMBIGUOUS"))
    )
    return {
        "checkpoint_sec": checkpoint_sec,
        "causal_past_only": row.get("causal_past_only") is True,
        "future_outcome_input_used": row.get("future_outcome_input_used") is not False,
        "source_quality_status": row.get("source_quality_status"),
        "bbo_observed": row.get("bbo_observed") is True,
        "depth_backed": row.get("depth_backed") is True,
        "same_sequence_epoch": row.get("same_sequence_epoch") is True,
        "sequence_epoch": sequence_epoch,
        "state": state,
        "source_quality_eligible": source_eligible,
        "source_gap_reasons": sorted(set(reasons)),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "bid_return_bps": bid_return,
        "bid_return_reference": bid_return_reference,
        "spread_bps": spread_bps,
        "quote_age_ms": quote_age_ms,
        "modeled_target_price": modeled_target_price,
        "net_edge_after_cost_bps": net_edge_after_cost_bps,
        "owner_price_feasible": (
            owner_price_feasible if isinstance(owner_price_feasible, bool) else None
        ),
        "aggressive_buy_trade_backed_ratio": trade_backed,
        "refill_ratio": refill,
        "downward_reprice_observed": (
            downward_reprice if isinstance(downward_reprice, bool) else None
        ),
    }


def evaluate_dynamic_micro_confirmation(
    checkpoints: Mapping[int | str, Mapping[str, Any]],
    *,
    policy: DynamicConfirmationPolicy = DEFAULT_DYNAMIC_CONFIRMATION_POLICY,
) -> dict[str, Any]:
    """Replay one signal using only evidence available at each checkpoint."""

    if not isinstance(checkpoints, Mapping):
        checkpoints = {}
    evaluated: list[dict[str, Any]] = []
    terminal_action: str | None = None
    terminal_reason: str | None = None
    selected_delay_sec: int | None = None
    for checkpoint_sec in policy.checkpoints_sec:
        raw = checkpoints.get(checkpoint_sec, checkpoints.get(str(checkpoint_sec)))
        outcome = _checkpoint_status(raw, checkpoint_sec=checkpoint_sec, policy=policy)
        if outcome["state"] == "SUPPORTIVE":
            action = "ENTER"
            terminal_action = action
            terminal_reason = "first_supportive_checkpoint"
            selected_delay_sec = checkpoint_sec
        elif outcome["state"] == "ADVERSE":
            action = "REJECT"
            terminal_action = action
            terminal_reason = "adverse_checkpoint_veto"
        elif checkpoint_sec == policy.checkpoints_sec[-1]:
            if all(item["source_quality_eligible"] for item in [*evaluated, outcome]):
                action = "REJECT"
                terminal_action = action
                terminal_reason = "confirmation_window_expired_without_support"
            else:
                action = "INSUFFICIENT_DATA"
                terminal_action = action
                terminal_reason = "confirmation_window_source_quality_incomplete"
        else:
            action = "WAIT"
        evaluated.append({**outcome, "action": action})
        if terminal_action is not None:
            break

    source_quality_eligible_checkpoint_count = sum(
        item["source_quality_eligible"] for item in evaluated
    )
    return {
        "schema": DYNAMIC_CONFIRMATION_SCHEMA,
        "policy_id": policy.policy_id,
        "policy": policy.as_dict(),
        "terminal_action": terminal_action or "INSUFFICIENT_DATA",
        "terminal_reason": terminal_reason or "checkpoint_evaluation_incomplete",
        "selected_delay_sec": selected_delay_sec,
        "evaluated_checkpoint_count": len(evaluated),
        "source_quality_eligible_checkpoint_count": (
            source_quality_eligible_checkpoint_count
        ),
        "source_quality_status": (
            "eligible"
            if source_quality_eligible_checkpoint_count > 0
            and terminal_action != "INSUFFICIENT_DATA"
            else "source_gap"
        ),
        "checkpoint_decisions": evaluated,
        "metric_contract": deepcopy(DYNAMIC_CONFIRMATION_METRIC_CONTRACT),
        "counterfactual_only": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "trading_decision_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def validate_dynamic_micro_confirmation_replay(
    replay: Any,
    *,
    policy: DynamicConfirmationPolicy = DEFAULT_DYNAMIC_CONFIRMATION_POLICY,
) -> tuple[bool, str | None]:
    """Validate a persisted replay before an EV consumer can trust it."""

    if not isinstance(replay, Mapping):
        return False, "dynamic_replay_not_mapping"
    if replay.get("schema") != DYNAMIC_CONFIRMATION_SCHEMA:
        return False, "dynamic_replay_schema_invalid"
    if replay.get("policy_id") != policy.policy_id:
        return False, "dynamic_replay_policy_id_invalid"
    if replay.get("policy") != policy.as_dict():
        return False, "dynamic_replay_policy_contract_invalid"
    if replay.get("metric_contract") != DYNAMIC_CONFIRMATION_METRIC_CONTRACT:
        return False, "dynamic_replay_metric_contract_invalid"
    required_authority = {
        "counterfactual_only": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "trading_decision_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if any(replay.get(key) is not value for key, value in required_authority.items()):
        return False, "dynamic_replay_authority_invalid"

    decisions = replay.get("checkpoint_decisions")
    if not isinstance(decisions, list) or not decisions:
        return False, "dynamic_replay_checkpoint_decisions_missing"
    if len(decisions) > len(policy.checkpoints_sec) or any(
        not isinstance(row, Mapping) for row in decisions
    ):
        return False, "dynamic_replay_checkpoint_decisions_invalid"
    observed_checkpoints = tuple(row.get("checkpoint_sec") for row in decisions)
    if observed_checkpoints != policy.checkpoints_sec[: len(decisions)]:
        return False, "dynamic_replay_checkpoint_order_invalid"

    reconstructed = evaluate_dynamic_micro_confirmation(
        {int(row["checkpoint_sec"]): row for row in decisions},
        policy=policy,
    )
    canonical_keys = (
        "schema",
        "policy_id",
        "policy",
        "terminal_action",
        "terminal_reason",
        "selected_delay_sec",
        "evaluated_checkpoint_count",
        "source_quality_eligible_checkpoint_count",
        "source_quality_status",
        "checkpoint_decisions",
        "metric_contract",
        "counterfactual_only",
        "runtime_effect",
        "allowed_runtime_apply",
        "trading_decision_effect",
        "actual_order_submitted",
        "broker_order_forbidden",
    )
    if any(replay.get(key) != reconstructed.get(key) for key in canonical_keys):
        return False, "dynamic_replay_reconstruction_mismatch"
    return True, None
