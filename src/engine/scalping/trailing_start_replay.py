"""Source-bound, report-only paired replay for three-market trailing starts.

The incumbent outcome is a real completed fill. A challenger SELL is only a
best-bid model and never an order or an actual realized PnL claim.
"""

from __future__ import annotations

import json
import math
import random
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.market import session_contract
from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit
from src.engine.scalping.trailing_threshold_policy import (
    GRID_VERSION,
    START_GRID_PCT,
    START_MARKETS,
    market_type_at,
)

KST = ZoneInfo("Asia/Seoul")
START_REPLAY_VERSION = "scalp_trailing_start_paired_v1"
MIN_TRAIN_POSITIONS = 30
MIN_HOLDOUT_POSITIONS = 10
MIN_TRAIN_DAYS = 5
MIN_HOLDOUT_DAYS = 2


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _epoch(value: Any) -> float | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return _number(value)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.timestamp()


def _flag(value: Any) -> bool | None:
    if value is True or str(value).lower() in {"true", "1"}:
        return True
    if value is False or str(value).lower() in {"false", "0"}:
        return False
    return None


def _grid_state(row: dict) -> dict[str, tuple[bool, bool]] | None:
    raw = row.get("tuning_grid_state")
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
        state = {
            str(key): (bool(armed), bool(triggered))
            for key, armed, triggered in values
        }
    except (TypeError, ValueError):
        return None
    if set(state) != {str(value) for value in START_GRID_PCT}:
        return None
    return state


def _validated_events(rows: list[dict]) -> tuple[list[dict], str | None]:
    if not rows:
        return [], "source_gap_no_trailing_evaluations"
    result: list[dict] = []
    position_keys = set()
    policy_shas = set()
    last_at = float("-inf")
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or row.get("observation_grid_version") != GRID_VERSION:
            return [], "source_gap_grid_version"
        if row.get("tuning_start_grid_version") != "start_0p3_to_1p2_step_0p1_v1":
            return [], "source_gap_start_grid_version"
        sequence = _number(row.get("event_sequence"))
        if sequence is None or not sequence.is_integer() or int(sequence) != index:
            return [], "source_gap_event_sequence"
        if _flag(row.get("observation_coverage_exhausted")) is not False:
            return [], "source_gap_sample_cap_or_coverage"
        if _flag(row.get("observation_telemetry_gap")) is not False:
            return [], "source_gap_observation_telemetry"
        if _flag(row.get("tuning_grid_source_complete")) is not True:
            return [], "source_gap_tuning_input_quality"
        evaluations = _number(row.get("tuning_grid_evaluations_since_event"))
        max_gap = _number(row.get("tuning_grid_max_evaluation_gap_sec"))
        if (evaluations is None or evaluations < 1 or not evaluations.is_integer()
                or max_gap is None or max_gap < 0 or max_gap > 2.0):
            return [], "source_gap_evaluation_coverage"
        at = _number(row.get("evaluation_at_epoch"))
        bid_at = _number(row.get("bid_source_received_at_epoch"))
        if at is None or bid_at is None or at < last_at or not 0 < bid_at <= at:
            return [], "source_gap_evaluation_or_bid_clock"
        market = market_type_at(at)
        if market is None or market != row.get("tuning_market_type"):
            return [], "source_gap_market_session_binding"
        session = session_contract.resolve_market_session(
            datetime.fromtimestamp(at, KST)
        )
        if (not session.exit_allowed_by_clock
                or _flag(row.get("tuning_exit_allowed_by_clock")) is not True
                or row.get("tuning_session_contract_version")
                    != session.contract_version):
            return [], "source_gap_market_exit_clock_blocked"
        peak = _number(row.get("peak_price"))
        peak_profit = _number(row.get("peak_profit_pct"))
        bid = _number(row.get("executable_bid"))
        bid_qty = _number(row.get("executable_bid_qty"))
        strong = _flag(row.get("strong"))
        limit = _number(row.get("trailing_limit_pct"))
        if (peak is None or peak <= 0 or peak_profit is None or bid is None
                or bid <= 0 or strong is None or limit is None or limit <= 0):
            return [], "source_gap_replay_decision_input"
        if bid_qty is None or bid_qty <= 0 or not bid_qty.is_integer():
            return [], "source_gap_executable_bid_depth"
        logged = _grid_state(row)
        if logged is None:
            return [], "source_gap_grid_state_missing"
        for start in START_GRID_PCT:
            decision = evaluate_trailing_take_profit(
                peak_price=peak, executable_bid=bid,
                peak_profit_pct=peak_profit, start_pct=start,
                strong=strong, weak_limit_pct=limit, strong_limit_pct=limit,
            )
            if logged[str(start)] != (decision.armed, decision.triggered):
                return [], "source_gap_grid_state_mismatch"
        position_keys.add(str(row.get("position_key") or ""))
        policy_shas.add(str(row.get("scalp_trailing_policy_value_sha256") or ""))
        result.append({**row, "_at": at, "_market": market,
                       "_peak": peak, "_peak_profit": peak_profit,
                       "_bid": bid, "_strong": strong, "_limit": limit})
        last_at = at
    if len(position_keys) != 1 or "" in position_keys:
        return [], "source_gap_position_identity"
    if len(policy_shas) != 1 or policy_shas == {""}:
        return [], "source_gap_policy_generation"
    return result, None


def _first_signal(
    rows: list[dict], *, target_market: str, start_pct: float,
    incumbent_by_market: dict[str, float],
) -> tuple[dict | None, float | None]:
    armed = False
    first_arm_at: float | None = None
    for row in rows:
        start = (start_pct if row["_market"] == target_market
                 else incumbent_by_market[row["_market"]])
        decision = evaluate_trailing_take_profit(
            peak_price=row["_peak"], executable_bid=row["_bid"],
            peak_profit_pct=row["_peak_profit"], start_pct=start,
            strong=row["_strong"], weak_limit_pct=row["_limit"],
            strong_limit_pct=row["_limit"],
        )
        if decision.armed and not armed:
            armed = True
            first_arm_at = row["_at"]
        if armed and decision.price_usable and decision.drawdown_pct + 1e-9 >= row["_limit"]:
            return row, first_arm_at
    return None, first_arm_at


def _candidate_pnl(trade: dict, row: dict) -> tuple[float | None, str | None]:
    """Price one full residual SELL only when fill cost and top bid depth exist."""

    at = row["_at"]
    buys = trade.get("buy_fill_legs")
    sells = trade.get("sell_fill_legs")
    cost = _number(trade.get("effective_cost_rate"))
    if not isinstance(buys, list) or not buys or not isinstance(sells, list):
        return None, "source_gap_fill_leg_path"
    if any(not isinstance(leg, dict) for leg in buys + sells):
        return None, "source_gap_fill_leg_shape"
    if cost is None or not 0 < cost <= 0.05:
        return None, "source_gap_cost_rate"
    if any(_epoch(leg.get("at")) is None for leg in buys + sells):
        return None, "source_gap_fill_leg_clock"
    if any(_epoch(leg["at"]) > at for leg in buys):
        return None, "source_gap_future_buy_leg_counterfactual"
    if any(_epoch(leg["at"]) <= at for leg in sells):
        return None, "source_gap_prior_partial_sell_counterfactual"
    qty = _number(trade.get("buy_filled_qty"))
    buy_amount = _number(trade.get("buy_fill_amount"))
    bid_qty = _number(row.get("executable_bid_qty"))
    if qty is None or qty <= 0 or buy_amount is None or buy_amount <= 0:
        return None, "source_gap_buy_fill_cost"
    if bid_qty is None or bid_qty < qty:
        return None, "source_gap_executable_bid_depth"
    leg_qty = [_number(leg.get("qty")) for leg in buys]
    leg_amount = [_number(leg.get("amount_krw")) for leg in buys]
    if any(value is None or value <= 0 for value in leg_qty + leg_amount):
        return None, "source_gap_buy_leg_value"
    if abs(sum(leg_qty) - qty) > 1e-9:
        return None, "source_gap_buy_leg_quantity"
    if abs(sum(leg_amount) - buy_amount) > max(1, qty):
        return None, "source_gap_buy_leg_cost"
    return round(row["_bid"] * qty * (1.0 - cost) - buy_amount, 2), None


def replay_start_grid(
    trade: dict, transitions: list[dict], *,
    actual_exit_rule: str, actual_exit_signal: dict,
    incumbent_start_pct: float = 0.6,
    incumbent_by_market: dict[str, float] | None = None,
) -> dict:
    """Calculate paired source-only outcomes, preserving unobserved futures."""

    rows, gap = _validated_events(transitions)
    base = {
        "schema": START_REPLAY_VERSION,
        "decision_authority": "report_only_counterfactual_no_threshold_apply",
        "start_grid_pct": list(START_GRID_PCT),
        "markets": {},
        "source_gap": gap,
    }
    if gap:
        return base
    incumbents = incumbent_by_market or {
        market: incumbent_start_pct for market in START_MARKETS
    }
    if (set(incumbents) != set(START_MARKETS)
            or any(_number(incumbents[market]) is None
                   or not 0 < float(incumbents[market]) <= 100
                   for market in START_MARKETS)):
        return {**base, "source_gap": "source_gap_incumbent_market_values"}
    base["incumbent_by_market"] = {
        market: float(incumbents[market]) for market in START_MARKETS
    }
    signal_at = _epoch(actual_exit_signal.get("timestamp"))
    if actual_exit_signal.get("inferred") or signal_at is None:
        return {**base, "source_gap": "source_gap_direct_exit_signal_missing"}
    rows = [row for row in rows if row["_at"] <= signal_at + 1.0]
    if not rows or signal_at - rows[-1]["_at"] > 15.0:
        return {**base, "source_gap": "source_gap_exit_signal_coverage"}
    buys = trade.get("buy_fill_legs")
    if (not isinstance(buys, list) or not buys
            or any(not isinstance(leg, dict) or _epoch(leg.get("at")) is None
                   for leg in buys)):
        return {**base, "source_gap": "source_gap_buy_fill_clock"}
    if rows[0]["_at"] < max(_epoch(leg["at"]) for leg in buys) - 1.0:
        return {**base, "source_gap": "source_gap_pre_full_buy_observation"}
    sells = trade.get("sell_fill_legs")
    if (not isinstance(sells, list) or not sells
            or any(not isinstance(leg, dict) or _epoch(leg.get("at")) is None
                   for leg in sells)):
        return {**base, "source_gap": "source_gap_sell_fill_clock"}
    if min(_epoch(leg["at"]) for leg in sells) < signal_at - 1.0:
        return {**base, "source_gap": "source_gap_sell_before_exit_signal"}
    actual_pnl = _number(trade.get("realized_pnl_krw"))
    buy_amount = _number(trade.get("buy_fill_amount"))
    if actual_pnl is None or buy_amount is None or buy_amount <= 0:
        return {**base, "source_gap": "source_gap_exact_completed_economics"}
    actual_tp = actual_exit_rule == "scalp_trailing_take_profit"
    incumbent, _ = _first_signal(
        rows, target_market="REGULAR", start_pct=incumbents["REGULAR"],
        incumbent_by_market=incumbents,
    )
    if actual_tp and (incumbent is None
                      or abs(incumbent["_at"] - signal_at) > 1.0):
        return {**base, "source_gap": "source_gap_incumbent_trigger_not_reproduced"}
    if not actual_tp and incumbent is not None and incumbent["_at"] < signal_at - 1.0:
        return {**base, "source_gap": "source_gap_incumbent_competing_exit_order"}
    base["incumbent_actual_pnl_krw"] = actual_pnl
    base["incumbent_first_trigger_at_epoch"] = (
        incumbent["_at"] if incumbent else None
    )
    base["exposure_markets"] = sorted({row["_market"] for row in rows})
    def predecision_context(row: dict) -> dict:
        ai_usable = _flag(row.get("ai_score_usable"))
        return {
            "ai_class": (
                "strong" if ai_usable and row["_strong"] else
                "weak" if ai_usable else "unusable"
            ),
            "quote_state": str(row.get("quote_consistency_state") or "missing"),
            "spread_bps": _number(row.get("executable_spread_bps")),
            "bid_source": str(row.get("bid_source") or "missing"),
        }
    base["predecision_context"] = predecision_context(rows[0])
    base["predecision_context_by_market"] = {
        market: predecision_context(next(row for row in rows
                                         if row["_market"] == market))
        for market in base["exposure_markets"]
    }
    for market in START_MARKETS:
        results = {}
        for start in START_GRID_PCT:
            first, arm_at = _first_signal(
                rows, target_market=market, start_pct=start,
                incumbent_by_market=incumbents,
            )
            status = "same_observed_exit"
            modeled_pnl = actual_pnl
            gap_reason = None
            if first is not None and first["_at"] < signal_at - 1.0:
                modeled_pnl, gap_reason = _candidate_pnl(trade, first)
                status = "modeled_earlier_full_sell" if gap_reason is None else "source_gap"
            elif first is not None and abs(first["_at"] - signal_at) <= 1.0:
                if not actual_tp:
                    status = "same_time_competing_exit_priority"
            elif actual_tp:
                status = "censored_after_actual_take_profit"
                modeled_pnl = None
            first_signal_pnl = (
                modeled_pnl if status == "modeled_earlier_full_sell"
                else _candidate_pnl(trade, first)[0] if first else None
            )
            results[str(start)] = {
                "status": status,
                "source_gap": gap_reason,
                "start_minus_active_limit_pct": (
                    round(start - first["_limit"], 6) if first else None
                ),
                "first_arm_at_epoch": arm_at,
                "first_trigger_at_epoch": first["_at"] if first else None,
                "first_trigger_bid": first["_bid"] if first else None,
                "first_trigger_market": first["_market"] if first else None,
                "first_trigger_modeled_net_pct": (
                    round(100.0 * first_signal_pnl / buy_amount, 6)
                    if first_signal_pnl is not None else None
                ),
                "modeled_or_observed_pnl_krw": modeled_pnl,
                "paired_delta_pnl_krw": (
                    round(modeled_pnl - actual_pnl, 2)
                    if modeled_pnl is not None else None
                ),
                "fill_model": (
                    "best_bid_full_qty_configured_cost"
                    if status == "modeled_earlier_full_sell" else None
                ),
            }
        base["markets"][market] = results
    return base


def _weighted_ev(rows: list[tuple[dict, dict]]) -> float | None:
    capital = sum(float(outcome["buy_fill_amount"]) for outcome, _ in rows)
    if capital <= 0:
        return None
    delta = sum(float(candidate["paired_delta_pnl_krw"]) for _, candidate in rows)
    return round(100.0 * delta / capital, 6)


def _outcome_available_day(outcome: dict) -> str:
    """Split by the date a completed outcome became available, when known."""

    return str(outcome.get("completion_observed_date") or outcome.get("rec_date") or "")[:10]


def _day_bootstrap_interval(rows: list[tuple[dict, dict]]) -> list[float] | None:
    groups: dict[str, list[tuple[dict, dict]]] = {}
    for outcome, candidate in rows:
        day = _outcome_available_day(outcome)
        groups.setdefault(day, []).append((outcome, candidate))
    if len(groups) < MIN_HOLDOUT_DAYS:
        return None
    days = sorted(groups)
    rng = random.Random(91725)
    samples = []
    for _ in range(1000):
        sampled = [item for _ in days for item in groups[rng.choice(days)]]
        ev = _weighted_ev(sampled)
        if ev is not None:
            samples.append(ev)
    if len(samples) != 1000:
        return None
    samples.sort()
    return [samples[25], samples[974]]


def summarize_start_grid(
    outcomes: list[dict], *, population_complete: bool = True
) -> dict:
    """Select research-only market values on a common source-qualified cohort."""

    by_id = {str(row["record_id"]): row for row in outcomes}
    result = {
        "schema": "scalp_trailing_start_market_tuning_v1",
        "decision_authority": "report_only_no_runtime_apply",
        "metric_role": "primary_ev",
        "primary_decision_metric": "modeled_paired_notional_weighted_delta_ev_pct",
        "window_policy": "clean_entry_day_train_latest_day_holdout",
        "sample_floor": {
            "train_positions": MIN_TRAIN_POSITIONS,
            "holdout_positions": MIN_HOLDOUT_POSITIONS,
            "train_days": MIN_TRAIN_DAYS,
            "holdout_days": MIN_HOLDOUT_DAYS,
        },
        "source_quality_gate": "strict_completed_and_full_candidate_first_crossing",
        "forbidden_uses": "live_apply|actual_candidate_fill_claim|stop_delay",
        "strict_completed_position_ids": sorted(by_id),
        "population_complete": bool(population_complete),
        "holdout_date_basis": "completion_observed_date_with_entry_date_fallback",
        "entry_date_fallback_ids": sorted(
            trade_id for trade_id, row in by_id.items()
            if not row.get("completion_observed_date")
        ),
        "markets": {},
    }
    for market in START_MARKETS:
        exposed = {
            trade_id for trade_id, outcome in by_id.items()
            if market in (outcome.get("trailing_start_market_replay") or {})
                .get("exposure_markets", [])
        }
        source_gaps = sorted(
            trade_id for trade_id, outcome in by_id.items()
            if (outcome.get("trailing_start_market_replay") or {}).get("source_gap")
        )
        eligible: dict[str, set[str]] = {}
        rows_by_start: dict[str, dict[str, tuple[dict, dict]]] = {}
        for start in START_GRID_PCT:
            key = str(start)
            candidate_rows = {}
            for trade_id in exposed:
                outcome = by_id[trade_id]
                candidate = (outcome.get("trailing_start_market_replay") or {}) \
                    .get("markets", {}).get(market, {}).get(key)
                if (isinstance(candidate, dict)
                        and candidate.get("paired_delta_pnl_krw") is not None
                        and _number(outcome.get("buy_fill_amount")) is not None
                        and float(outcome["buy_fill_amount"]) > 0):
                    candidate_rows[trade_id] = (outcome, candidate)
            for trade_id in set(by_id) - exposed - set(source_gaps):
                outcome = by_id[trade_id]
                amount = _number(outcome.get("buy_fill_amount"))
                if amount is not None and amount > 0:
                    candidate_rows[trade_id] = (
                        outcome,
                        {"status": "not_exposed_zero_effect",
                         "paired_delta_pnl_krw": 0.0},
                    )
            rows_by_start[key] = candidate_rows
            eligible[key] = set(candidate_rows)
        common = set.intersection(*eligible.values()) if eligible else set()
        dates = sorted({_outcome_available_day(by_id[trade_id])
                        for trade_id in common})
        holdout_days = max(MIN_HOLDOUT_DAYS, math.ceil(len(dates) * 0.2))
        holdout = set(dates[-holdout_days:]) if len(dates) > holdout_days else set()
        candidate_metrics = {}
        for start in START_GRID_PCT:
            key = str(start)
            selected = [rows_by_start[key][trade_id] for trade_id in sorted(common)]
            train_rows = [pair for pair in selected
                          if _outcome_available_day(pair[0]) not in holdout]
            holdout_rows = [pair for pair in selected
                            if _outcome_available_day(pair[0]) in holdout]
            context = {}
            for field in ("ai_class", "quote_state"):
                buckets: dict[str, list[tuple[dict, dict]]] = {}
                for pair in selected:
                    replay = pair[0].get("trailing_start_market_replay") or {}
                    market_context = (replay.get("predecision_context_by_market")
                                      or {}).get(market) or {}
                    label = str(market_context.get(field) or "not_exposed")
                    buckets.setdefault(label, []).append(pair)
                context[field] = {
                    label: {"n": len(group),
                            "modeled_paired_notional_weighted_delta_ev_pct":
                                _weighted_ev(group)}
                    for label, group in sorted(buckets.items())
                }
            candidate_metrics[key] = {
                "pairable_ids": sorted(eligible[key]),
                "common_grid_ids": sorted(common),
                "train_n": len(train_rows),
                "holdout_n": len(holdout_rows),
                "train_ev_pct": _weighted_ev(train_rows),
                "holdout_ev_pct": _weighted_ev(holdout_rows),
                "holdout_day_bootstrap_95pct_interval":
                    _day_bootstrap_interval(holdout_rows),
                "worst_paired_delta_ev_pct": min(
                    (
                        100.0 * float(pair[1]["paired_delta_pnl_krw"])
                        / float(pair[0]["buy_fill_amount"])
                        for pair in selected
                    ),
                    default=None,
                ),
                "incremental_loss_worsened_ids": sorted(
                    str(pair[0]["record_id"])
                    for pair in selected
                    if (pair[1].get("status") == "modeled_earlier_full_sell"
                        and float(pair[1]["modeled_or_observed_pnl_krw"]) < 0
                        and float(pair[1]["paired_delta_pnl_krw"]) < 0)
                ),
                "predecision_interactions": context,
            }
        enough = bool(
            population_complete and common
            and len(dates) - len(holdout) >= MIN_TRAIN_DAYS
            and len(holdout) >= MIN_HOLDOUT_DAYS
            and all(
                row["train_n"] >= MIN_TRAIN_POSITIONS
                and row["holdout_n"] >= MIN_HOLDOUT_POSITIONS
                for row in candidate_metrics.values()
            )
        )
        incumbent_values = {
            (by_id[trade_id].get("trailing_start_market_replay") or {})
                .get("incumbent_by_market", {}).get(market)
            for trade_id in common
        }
        incumbent_value = (
            float(next(iter(incumbent_values)))
            if len(incumbent_values) == 1 and None not in incumbent_values
            else None
        )
        if incumbent_value is None or incumbent_value not in START_GRID_PCT:
            enough = False
        ranked = sorted(
            START_GRID_PCT,
            key=lambda start: (
                -float(candidate_metrics[str(start)]["train_ev_pct"]),
                abs(start - incumbent_value), start,
            ),
        ) if enough else []
        winner = ranked[0] if ranked else None
        winner_metric = candidate_metrics.get(str(winner)) if winner is not None else None
        interval = (winner_metric or {}).get("holdout_day_bootstrap_95pct_interval")
        research_value = (
            winner if winner != incumbent_value and interval and interval[0] > 0
            and winner_metric["holdout_ev_pct"] is not None
            and winner_metric["holdout_ev_pct"] > 0 else None
        )
        tail_review_required = bool(
            research_value is not None
            and winner_metric["incremental_loss_worsened_ids"]
        )
        result["markets"][market] = {
            "incumbent_value_pct": incumbent_value,
            "exposed_ids": sorted(exposed),
            "common_grid_ids": sorted(common),
            "excluded_ids": sorted(set(by_id) - common),
            "excluded_count": len(set(by_id) - common),
            "strict_completed_count": len(by_id),
            "source_gap_ids": source_gaps,
            "candidate_metrics": candidate_metrics,
            "research_candidate_value_pct": research_value,
            "tail_safety_review_required": tail_review_required,
            "runtime_candidate_value_pct": None,
            "eligible_for_live_review": False,
            "status": (
                "hold_tail_safety_review" if tail_review_required
                else "research_candidate_holdout_positive" if research_value is not None
                else "hold_source_or_sample" if not enough
                else "hold_no_independent_edge"
            ),
        }
    return result
