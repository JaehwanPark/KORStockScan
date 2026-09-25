"""Source-bound four-axis trailing TP research over completed positions.

The report owner supplies strict completed trades. Modeled bids are never fills.
This module has no policy write or live order authority.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit
from src.engine.scalping.trailing_start_replay import (
    _candidate_pnl, _epoch, _flag, _number, _validated_events,
)
from src.engine.scalping.trailing_threshold_policy import (
    START_GRID_PCT, START_MARKETS, THRESHOLD_KEYS, closed_exit_gap, market_values_hash,
    normalize_values, value_hash,
)

SCHEMA = "scalp_trailing_four_axis_market_replay_v1"
GRID = {
    THRESHOLD_KEYS[0]: START_GRID_PCT,
    THRESHOLD_KEYS[2]: tuple(round(i / 10, 1) for i in range(2, 9)),
    THRESHOLD_KEYS[3]: tuple(round(i / 10, 1) for i in range(4, 13)),
}
DEFAULT_VECTOR = {
    THRESHOLD_KEYS[0]: 0.6,
    THRESHOLD_KEYS[1]: 75,
    THRESHOLD_KEYS[2]: 0.4,
    THRESHOLD_KEYS[3]: 0.8,
}
SLIPPAGE_SENSITIVITY_BPS = (0, 30, 100)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _signal(rows: list[dict], vectors: dict[str, dict]) -> tuple[dict | None, float | None]:
    armed = False
    arm_at = None
    for row in rows:
        vector = vectors[row["_market"]]
        usable = _flag(row.get("ai_score_usable"))
        score = _number(row.get("ai_score"))
        strong = bool(usable and score is not None
                      and score >= vector[THRESHOLD_KEYS[1]])
        decision = evaluate_trailing_take_profit(
            peak_price=row["_peak"], executable_bid=row["_bid"],
            peak_profit_pct=row["_peak_profit"],
            start_pct=vector[THRESHOLD_KEYS[0]], strong=strong,
            weak_limit_pct=vector[THRESHOLD_KEYS[2]],
            strong_limit_pct=vector[THRESHOLD_KEYS[3]],
            already_armed=armed,
        )
        if decision.armed and not armed:
            armed, arm_at = True, row["_at"]
        if decision.triggered:
            return row, arm_at
    return None, arm_at


def prepare_position(trade: dict) -> dict:
    """Validate an ordered, same-generation source path once per position."""

    if (trade.get("trailing_event_source_status") != "structured_partition_read"
            or not trade.get("trailing_event_source_sha256")):
        return {"rows": [], "source_gap": "source_gap_structured_event_provenance",
                "evidence_grade": None}
    holding_starts = [event for event in trade.get("timeline") or []
                      if isinstance(event, dict)
                      and event.get("stage") == "holding_started"
                      and (event.get("fields") or {}).get(
                          "pipeline_lifecycle_population_scope") == "real_record_bound"
                      and _epoch(event.get("timestamp")) is not None]
    if len(holding_starts) != 1:
        return {"rows": [], "source_gap": "source_gap_holding_start_identity",
                "evidence_grade": None}
    events = [event.get("fields") or {} for event in trade.get("timeline") or []
              if isinstance(event, dict)
              and event.get("stage") == "scalp_trailing_input_transition"]
    rows, gap = _validated_events(events)
    result = {"rows": rows, "source_gap": gap, "evidence_grade": None}
    if gap:
        return result
    trade_id = str(trade.get("id") or "").strip()
    expected_position_key = f"record:{trade_id}" if trade_id else ""
    if (not expected_position_key
            or any(row.get("position_key") != expected_position_key for row in rows)):
        result.update(rows=[], source_gap="source_gap_position_trade_identity")
        return result
    if rows[0]["_at"] < _epoch(holding_starts[0]["timestamp"]):
        result.update(rows=[], source_gap="source_gap_pre_holding_observation")
        return result
    for earlier, later in zip(rows, rows[1:]):
        if (later["_at"] - earlier["_at"] > 2
                and _number(later.get("tuning_grid_evaluations_since_event")) <= 1
                and not closed_exit_gap(earlier["_at"], later["_at"])):
            result.update(rows=[], source_gap="source_gap_live_evaluation_interval")
            return result
    if any(row.get("tuning_four_axis_bin_version") !=
           "start_0p1_width_0p1_score_5_v1" for row in rows):
        if any(_number(row.get("tuning_grid_evaluations_since_event")) != 1
               for row in rows):
            result.update(rows=[], source_gap="source_gap_four_axis_crossing_coverage")
            return result
    first = events[0]
    scalar = first.get("scalp_trailing_policy_values")
    vector = first.get("scalp_trailing_market_values")
    try:
        if not isinstance(scalar, dict) or value_hash(scalar) != first.get(
            "scalp_trailing_policy_value_sha256"
        ):
            raise ValueError("scalar_policy_hash")
        scalar = normalize_values(scalar)
        if isinstance(vector, dict):
            digest = market_values_hash(vector)
            if any(event.get("scalp_trailing_market_values_sha256") != digest
                   or event.get("scalp_trailing_market_values") != vector
                   for event in events):
                raise ValueError("market_vector_generation")
            grade = "historical_direct"
        else:
            starts = first.get("scalp_trailing_start_by_market")
            if not isinstance(starts, dict) or set(starts) != set(START_MARKETS):
                raise ValueError("historical_market_start_missing")
            vector = {market: {**scalar, THRESHOLD_KEYS[0]: float(starts[market])}
                      for market in START_MARKETS}
            market_values_hash(vector)
            if any(event.get("scalp_trailing_start_by_market") != starts
                   or event.get("scalp_trailing_policy_value_sha256") != value_hash(scalar)
                   for event in events):
                raise ValueError("reconstructed_policy_generation")
            grade = "historical_reconstructed"
        for row in rows:
            incumbent = vector[row["_market"]]
            usable = _flag(row.get("ai_score_usable"))
            score = _number(row.get("ai_score"))
            if usable is None or usable and (score is None or not 0 <= score <= 100):
                raise ValueError("score_path")
            strong = bool(usable and score >= incumbent[THRESHOLD_KEYS[1]])
            limit = incumbent[THRESHOLD_KEYS[3] if strong else THRESHOLD_KEYS[2]]
            logged_start = _number(row.get("trailing_start_pct"))
            logged_score_threshold = _number(row.get("strong_score_threshold"))
            if (strong != row["_strong"] or abs(float(limit) - row["_limit"]) > 1e-8
                    or logged_start is None
                    or abs(float(incumbent[THRESHOLD_KEYS[0]]) - logged_start) > 1e-8
                    or logged_score_threshold is None
                    or abs(float(incumbent[THRESHOLD_KEYS[1]]) - logged_score_threshold) > 1e-8):
                raise ValueError("incumbent_score_or_width_mismatch")
            if usable:
                age = _number(row.get("ai_score_age_sec"))
                ttl = _number(row.get("ai_score_ttl_sec"))
                score_at = _number(row.get("ai_score_effective_at_epoch"))
                source = str(row.get("ai_score_source") or "").strip().lower()
                quality = str(row.get("ai_score_data_quality") or "").strip().lower()
                if (age is None or ttl is None or not 0 <= age <= ttl
                        or score_at is None or abs((row["_at"] - score_at) - age) > 1
                        or source in {"", "-", "none", "missing", "fallback_score_50"}
                        or quality != "fresh"):
                    raise ValueError("score_ttl_path")
        signal = trade.get("exit_signal") or {}
        if signal.get("inferred") or _epoch(signal.get("timestamp")) is None:
            grade = "source_path_terminal_unproven"
        result.update({"incumbent": vector, "evidence_grade": grade,
                       "policy_sha256": market_values_hash(vector)})
    except (KeyError, TypeError, ValueError) as exc:
        result["source_gap"] = f"source_gap_four_axis_{exc}"
        result["rows"] = []
    return result


def replay_vector(
    trade: dict, prepared: dict, candidate: dict[str, dict],
    *, actual_exit_rule: str,
) -> dict:
    """Replay one full three-market vector against the same realized exit."""

    if prepared.get("source_gap"):
        return {"status": "source_gap", "source_gap": prepared["source_gap"]}
    try:
        market_values_hash(candidate)
    except (KeyError, TypeError, ValueError):
        return {"status": "source_gap", "source_gap": "source_gap_candidate_vector"}
    signal = trade.get("exit_signal") or {}
    signal_at = _epoch(signal.get("timestamp")) if not signal.get("inferred") else None
    terminal_grade = prepared["evidence_grade"]
    if signal_at is None:
        # A preserved order-send event can reconstruct the terminal clock only
        # when its rule is explicit and the completed SELL follows that order.
        sent = [event for event in trade.get("timeline") or []
                if isinstance(event, dict) and event.get("stage") == "sell_order_sent"
                and not event.get("is_inferred")
                and (event.get("fields") or {}).get("exit_rule") == actual_exit_rule
                and _epoch(event.get("timestamp")) is not None]
        sells = trade.get("sell_fill_legs")
        if len(sent) == 1 and isinstance(sells, list) and sells:
            order_at = _epoch(sent[0]["timestamp"])
            order_no = str((sent[0].get("fields") or {}).get("ord_no") or "").strip()
            fill_order_nos = {str(leg.get("order_no") or leg.get("ord_no") or "").strip()
                              for leg in sells if isinstance(leg, dict)}
            sell_ats = [_epoch(leg.get("at")) for leg in sells
                        if isinstance(leg, dict)]
            if (order_no and fill_order_nos == {order_no}
                    and len(sell_ats) == len(sells)
                    and all(at is not None and at >= order_at
                            for at in sell_ats)):
                signal_at = order_at
                terminal_grade = "historical_reconstructed"
    if signal_at is None:
        return {"status": "source_gap", "source_gap": "source_gap_direct_or_order_signal_missing"}
    cache_key = (actual_exit_rule, signal_at)
    if prepared.get("_terminal_key") != cache_key:
        prepared["_terminal_rows"] = [
            row for row in prepared["rows"] if row["_at"] <= signal_at + 1
        ]
        prepared["_terminal_key"] = cache_key
        prepared.pop("_incumbent_signal", None)
    rows = prepared["_terminal_rows"]
    if not rows or signal_at - rows[-1]["_at"] > 15:
        return {"status": "source_gap", "source_gap": "source_gap_exit_signal_coverage"}
    buys = trade.get("buy_fill_legs")
    sells = trade.get("sell_fill_legs")
    if (not isinstance(buys, list) or not buys
            or any(not isinstance(leg, dict) or _epoch(leg.get("at")) is None
                   for leg in buys)
            or max(_epoch(leg["at"]) for leg in buys) > rows[0]["_at"] + 1):
        return {"status": "source_gap", "source_gap": "source_gap_buy_fill_clock"}
    if (not isinstance(sells, list) or not sells
            or any(not isinstance(leg, dict) or _epoch(leg.get("at")) is None
                   for leg in sells)
            or min(_epoch(leg["at"]) for leg in sells) < signal_at - 1):
        return {"status": "source_gap", "source_gap": "source_gap_sell_before_exit_signal"}
    if "_incumbent_signal" not in prepared:
        prepared["_incumbent_signal"] = _signal(rows, prepared["incumbent"])[0]
    incumbent = prepared["_incumbent_signal"]
    is_tp = actual_exit_rule == "scalp_trailing_take_profit"
    if is_tp and (incumbent is None or abs(incumbent["_at"] - signal_at) > 1):
        return {"status": "source_gap", "source_gap": "source_gap_incumbent_trigger_not_reproduced"}
    if not is_tp and incumbent and incumbent["_at"] < signal_at - 1:
        return {"status": "source_gap", "source_gap": "source_gap_competing_exit_order"}
    actual_pnl = _number(trade.get("realized_pnl_krw"))
    amount = _number(trade.get("buy_fill_amount"))
    if actual_pnl is None or amount is None or amount <= 0:
        return {"status": "source_gap", "source_gap": "source_gap_actual_cost_economics"}
    first, arm_at = _signal(rows, candidate)
    state = "same_observed_exit"
    modeled = actual_pnl
    gap = None
    censor_reason = None
    candidate_execution: dict[str, Any] | None = None
    modeled_slippage_pnl: tuple[float, ...] = ()
    if first is not None and first["_at"] < signal_at - 1:
        qty = _number(trade.get("buy_filled_qty"))
        bid_qty = _number(first.get("executable_bid_qty"))
        cost = _number(trade.get("effective_cost_rate"))
        candidate_execution = {
            "model": "first_crossing_top_bid",
            "slippage_sensitivity_bps": list(SLIPPAGE_SENSITIVITY_BPS),
        }
        if bid_qty is None or bid_qty <= 0:
            modeled, gap, state = None, "source_gap_executable_bid_depth_missing", "source_gap"
        elif qty is not None and qty > 0 and bid_qty < qty:
            fillable_qty = max(0.0, min(qty, bid_qty))
            fillable_fraction = fillable_qty / qty
            candidate_execution.update({
                "fillable_qty_at_trigger_bid": fillable_qty,
                "required_qty": qty,
                "fillable_fraction": round(fillable_fraction, 6),
                "residual_qty": qty - fillable_qty,
                "identified_partial_proceeds_after_cost_krw": (
                    round(first["_bid"] * fillable_qty * (1.0 - cost), 2)
                    if cost is not None and 0 < cost <= 0.05 else None
                ),
                "identified_partial_buy_basis_krw": (
                    round(float(trade["buy_fill_amount"]) * fillable_fraction, 2)
                    if _number(trade.get("buy_fill_amount")) is not None else None
                ),
            })
            modeled, state = None, "censored_insufficient_trigger_bid_depth"
            censor_reason = "observed_top_bid_depth_covers_only_part_of_position"
        else:
            modeled, gap = _candidate_pnl(trade, first)
            state = "source_gap" if gap else "modeled_earlier_full_sell"
            if gap is None and modeled is not None and qty is not None and cost is not None:
                gross_proceeds = first["_bid"] * qty
                modeled_slippage_pnl = tuple(
                    round(
                        modeled - gross_proceeds * (1.0 - cost) * bps / 10000.0,
                        2,
                    )
                    for bps in SLIPPAGE_SENSITIVITY_BPS
                )
                candidate_execution.update({
                    "required_qty": qty,
                    "observed_top_bid_qty": bid_qty,
                    "full_quantity_depth_supported": True,
                    "modeled_pnl_by_slippage_bps": modeled_slippage_pnl,
                })
    elif is_tp and (first is None or first["_at"] > signal_at + 1):
        modeled, state = None, "censored_after_actual_take_profit"
        censor_reason = "candidate_trigger_after_observed_take_profit_or_not_observed"
    elif first is not None and not is_tp:
        state = "same_time_competing_exit_priority"
        candidate_execution = {
            "model": "observed_competing_exit_priority",
            "competing_exit_rule": actual_exit_rule,
        }
    score = _number(first.get("ai_score")) if first else None
    usable = _flag(first.get("ai_score_usable")) if first else False
    active = None
    if first:
        chosen = candidate[first["_market"]]
        active = chosen[THRESHOLD_KEYS[3] if usable and score is not None
                        and score >= chosen[THRESHOLD_KEYS[1]] else THRESHOLD_KEYS[2]]
    first_quote_pnl = _candidate_pnl(trade, first)[0] if first else None
    paired_delta = round(modeled - actual_pnl, 2) if modeled is not None else None
    if paired_delta is None:
        paired_delta_by_slippage: tuple[float, ...] | None = None
    elif modeled_slippage_pnl:
        paired_delta_by_slippage = tuple(
            round(value - actual_pnl, 2) for value in modeled_slippage_pnl
        )
    else:
        paired_delta_by_slippage = tuple(
            paired_delta for _ in SLIPPAGE_SENSITIVITY_BPS
        )
    result = {
        "status": state, "source_gap": gap,
        "evidence_grade": terminal_grade,
        "first_arm_at_epoch": arm_at,
        "first_trigger_at_epoch": first["_at"] if first else None,
        "first_trigger_market": first["_market"] if first else None,
        "first_trigger_bid": first["_bid"] if first else None,
        "start_minus_active_limit_pct": (
            round(candidate[first["_market"]][THRESHOLD_KEYS[0]] - active, 6)
            if first else None
        ),
        "modeled_or_observed_pnl_krw": modeled,
        "paired_delta_pnl_krw": paired_delta,
        "paired_delta_pnl_by_slippage_bps": paired_delta_by_slippage,
        "candidate_execution": candidate_execution,
        "first_trigger_modeled_net_pct": (
            round(100 * first_quote_pnl / amount, 6)
            if first_quote_pnl is not None else None
        ),
        "fill_model": "best_bid_full_qty_configured_cost"
        if state == "modeled_earlier_full_sell" else None,
    }
    if censor_reason:
        result["censor_reason"] = censor_reason
    if candidate_execution is not None:
        result["candidate_execution"] = candidate_execution
    return result


def score_grid(train_scores: list[float]) -> tuple[int, ...]:
    """Freeze a five-point score grid from training observations only."""

    if not train_scores:
        return (75,)
    ordered = sorted(train_scores)
    lo = ordered[int((len(ordered) - 1) * .10)]
    hi = ordered[int((len(ordered) - 1) * .90)]
    return tuple(sorted({75, *(value for value in range(5, 101, 5)
                               if lo <= value <= hi)}))


def _metric(rows: list[tuple[dict, dict]]) -> dict:
    capital = sum(float(trade["buy_fill_amount"]) for trade, _ in rows)
    delta = sum(float(replay["paired_delta_pnl_krw"]) for _, replay in rows)
    sensitivity = {}
    for bps in SLIPPAGE_SENSITIVITY_BPS:
        key = str(bps)
        slippage_index = SLIPPAGE_SENSITIVITY_BPS.index(bps)
        eligible = [
            (trade, replay, (replay.get("paired_delta_pnl_by_slippage_bps") or ())[slippage_index]
             if len(replay.get("paired_delta_pnl_by_slippage_bps") or ())
             > slippage_index else None)
            for trade, replay in rows
        ]
        eligible = [(trade, replay, delta) for trade, replay, delta in eligible
                    if delta is not None]
        scenario_capital = sum(float(trade["buy_fill_amount"]) for trade, _, _ in eligible)
        scenario_delta = sum(float(delta) for _, _, delta in eligible)
        sensitivity[key] = {
            "n": len(eligible),
            "delta_net_krw": round(scenario_delta, 2),
            "paired_ev_pct": (
                round(100 * scenario_delta / scenario_capital, 6)
                if scenario_capital > 0 else None
            ),
        }
    signs = {
        1 if row["paired_ev_pct"] > 0 else -1 if row["paired_ev_pct"] < 0 else 0
        for row in sensitivity.values() if row["paired_ev_pct"] is not None
    }
    return {
        "n": len(rows), "delta_net_krw": round(delta, 2),
        "paired_ev_pct": round(100 * delta / capital, 6) if capital > 0 else None,
        "execution_slippage_sensitivity": sensitivity,
        "slippage_sign_reversal": -1 in signs and 1 in signs,
        "large_loss_worsened_ids": sorted(str(trade.get("id")) for trade, replay in rows
            if replay["paired_delta_pnl_krw"] < 0
            and replay["modeled_or_observed_pnl_krw"] < 0),
    }


def summarize_four_axis(
    trades: list[dict], outcomes: list[dict], *, population_complete: bool,
) -> dict:
    """Report bounded single and pair sensitivities; never select live policy."""

    trade_ids = [str(trade.get("id")) for trade in trades]
    outcome_ids = [str(row.get("record_id")) for row in outcomes]
    by_id = {str(trade.get("id")): trade for trade in trades}
    outcome_by_id = {str(row.get("record_id")): row for row in outcomes}
    identity_complete = bool(
        len(by_id) == len(trades) and len(outcome_by_id) == len(outcomes)
        and set(trade_ids) == set(outcome_ids) and "None" not in by_id
    )
    all_ids = sorted(set(by_id) & set(outcome_by_id))
    valid_dates = {}
    entry_date_fallback_ids = []
    completion_clock_mismatch_ids = []
    for trade_id in all_ids:
        completion_day = outcome_by_id[trade_id].get("completion_observed_date")
        sell_legs = by_id[trade_id].get("sell_fill_legs") or []
        sell_epochs = [_epoch(leg.get("at")) for leg in sell_legs
                       if isinstance(leg, dict)]
        final_fill_day = (
            datetime.fromtimestamp(max(sell_epochs), ZoneInfo("Asia/Seoul"))
            .date().isoformat()
            if sell_epochs and len(sell_epochs) == len(sell_legs)
            and all(epoch is not None for epoch in sell_epochs)
            else None
        )
        raw = str(completion_day or final_fill_day
                  or outcome_by_id[trade_id].get("rec_date") or "")
        if completion_day and final_fill_day and completion_day != final_fill_day:
            completion_clock_mismatch_ids.append(trade_id)
        if not completion_day and not final_fill_day:
            entry_date_fallback_ids.append(trade_id)
        try:
            if date.fromisoformat(raw).isoformat() != raw:
                raise ValueError("date_format")
            valid_dates[trade_id] = raw
        except ValueError:
            valid_dates[trade_id] = None
    days = sorted({day for day in valid_dates.values() if day is not None})
    holdout_days = set(days[-max(2, math.ceil(len(days) * .2)):]) if len(days) >= 3 else set()
    prepared = {trade_id: prepare_position(by_id[trade_id]) for trade_id in all_ids}
    for trade_id, day in valid_dates.items():
        if day is None and not prepared[trade_id].get("source_gap"):
            prepared[trade_id]["source_gap"] = "source_gap_completed_outcome_date"
        if (trade_id in completion_clock_mismatch_ids
                and not prepared[trade_id].get("source_gap")):
            prepared[trade_id]["source_gap"] = "source_gap_completion_fill_day_mismatch"
    for trade_id, item in prepared.items():
        if item.get("source_gap"):
            continue
        baseline = replay_vector(
            by_id[trade_id], item, item["incumbent"],
            actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
        )
        if baseline.get("source_gap"):
            item["source_gap"] = baseline["source_gap"]
        else:
            item["evidence_grade"] = baseline["evidence_grade"]
    usable = {trade_id: item for trade_id, item in prepared.items()
              if not item.get("source_gap")}
    result = {
        "schema": SCHEMA, "decision_authority": "report_only_no_runtime_apply",
        "strict_completed_position_ids": sorted(set(trade_ids)),
        "position_identity_census_complete": identity_complete,
        "population_complete": bool(population_complete),
        "source_gap_by_id": {trade_id: item["source_gap"] for trade_id, item in prepared.items()
                             if item.get("source_gap")},
        "evidence_grade_counts": dict(Counter(item["evidence_grade"] for item in usable.values())),
        "evidence_grade_by_id": {trade_id: item["evidence_grade"]
                                 for trade_id, item in usable.items()},
        "holdout_date_basis": "completion_observed_date_or_final_sell_fill_day",
        "entry_date_fallback_ids": sorted(entry_date_fallback_ids),
        "completion_clock_mismatch_ids": sorted(completion_clock_mismatch_ids),
        "holdout_days": sorted(holdout_days), "markets": {},
        "research_candidate": None, "runtime_selected": None,
    }
    for trade_id in set(by_id) - set(outcome_by_id):
        result["source_gap_by_id"][trade_id] = "source_gap_position_outcome_missing"
    if not population_complete or not all_ids or not identity_complete:
        result["status"] = (
            "hold_position_identity_census" if not identity_complete
            else "hold_population_census_or_empty"
        )
        return result
    scores = [float(row["ai_score"]) for trade_id, item in usable.items()
              if valid_dates[trade_id] not in holdout_days
              for row in item["rows"] if _flag(row.get("ai_score_usable"))
              and _number(row.get("ai_score")) is not None]
    grids = {**GRID, THRESHOLD_KEYS[1]: score_grid(scores)}
    result["grid"] = {key: list(values) for key, values in grids.items()}
    result["grid_sha256"] = _digest(result["grid"])
    for market in START_MARKETS:
        exposed = {trade_id for trade_id, item in usable.items()
                   if any(row["_market"] == market for row in item["rows"])}
        market_result = {"exposed_ids": sorted(exposed), "axes": {},
                         "pairs": {}, "common_support_ids": [],
                         "source_eligible_ids": sorted(usable),
                         "research_candidate": None, "runtime_selected": None}
        result["markets"][market] = market_result
        if not exposed:
            market_result.update({
                "common_support_ids": sorted(usable),
                "excluded_ids": sorted(set(all_ids) - set(usable)),
                "grid_censored_or_gap_ids": [], "combinations": {},
                "status": "unidentified_no_market_exposure",
            })
            continue
        market_grids = {
            axis: tuple(sorted(set(grids[axis]) | {
                item["incumbent"][market][axis] for item in usable.values()
            }))
            for axis in THRESHOLD_KEYS
        }
        market_result["grid"] = {axis: list(values)
                                 for axis, values in market_grids.items()}
        market_result["grid_sha256"] = _digest(market_result["grid"])
        cache: dict[tuple, dict[str, dict]] = {}
        invalid_vector_candidates = []
        def valid_market_change(changes: dict[str, float | int]) -> bool:
            for trade_id, item in usable.items():
                if trade_id not in exposed:
                    continue
                vector = {**item["incumbent"][market], **changes}
                if vector[THRESHOLD_KEYS[3]] < vector[THRESHOLD_KEYS[2]]:
                    return False
            return True
        def evaluate(changes: dict[str, float | int]) -> dict[str, dict]:
            key = tuple(sorted(changes.items()))
            if key not in cache:
                rows = {}
                for trade_id, item in usable.items():
                    if trade_id not in exposed:
                        rows[trade_id] = {
                            "status": "not_exposed_zero_effect", "source_gap": None,
                            "modeled_or_observed_pnl_krw": by_id[trade_id].get("realized_pnl_krw"),
                            "paired_delta_pnl_krw": 0.0,
                        }
                        continue
                    candidate = {session: dict(values) for session, values in item["incumbent"].items()}
                    candidate[market].update(changes)
                    rows[trade_id] = replay_vector(
                        by_id[trade_id], item, candidate,
                        actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
                    )
                cache[key] = rows
            return cache[key]
        for axis in THRESHOLD_KEYS:
            axis_rows = {}
            for value in market_grids[axis]:
                if not valid_market_change({axis: value}):
                    invalid_vector_candidates.append(f"{axis}={value}")
                    continue
                axis_rows[str(value)] = evaluate({axis: value})
            market_result["axes"][axis] = axis_rows
        for left, right in itertools.combinations(THRESHOLD_KEYS, 2):
            if (left, right) == (THRESHOLD_KEYS[0], THRESHOLD_KEYS[1]):
                continue  # Arm and score have no direct width interaction hypothesis.
            pair_name = f"{left}×{right}"
            pair_rows = {}
            for a, b in itertools.product(market_grids[left], market_grids[right]):
                if not valid_market_change({left: a, right: b}):
                    invalid_vector_candidates.append(f"{pair_name}={a}|{b}")
                    continue
                pair_rows[f"{a}|{b}"] = evaluate({left: a, right: b})
            market_result["pairs"][pair_name] = pair_rows
        market_result["invalid_vector_candidates"] = invalid_vector_candidates
        all_candidates = [candidate for axis in market_result["axes"].values()
                          for candidate in axis.values()]
        all_candidates.extend(candidate for pair in market_result["pairs"].values()
                              for candidate in pair.values())
        common = set(usable)
        for candidate in all_candidates:
            common.intersection_update(trade_id for trade_id, row in candidate.items()
                                      if row.get("paired_delta_pnl_krw") is not None)
        market_result["common_support_ids"] = sorted(common)
        market_result["excluded_ids"] = sorted(set(all_ids) - set(usable))
        market_result["grid_censored_or_gap_ids"] = sorted(set(usable) - common)
        for collection in (market_result["axes"], market_result["pairs"]):
            for name, candidates in collection.items():
                collection[name] = {
                    key: {
                        "train": _metric([(by_id[trade_id], row) for trade_id, row in rows.items()
                                          if trade_id in common
                                          and valid_dates[trade_id] not in holdout_days]),
                        "holdout": _metric([(by_id[trade_id], row) for trade_id, row in rows.items()
                                            if trade_id in common
                                            and valid_dates[trade_id] in holdout_days]),
                        "comparison_support_ids": sorted(common),
                        "pairable_ids": sorted(trade_id for trade_id, row in rows.items()
                                               if row.get("paired_delta_pnl_krw") is not None),
                        "censored_ids": sorted(trade_id for trade_id, row in rows.items()
                                               if str(row.get("status") or "").startswith("censored_")),
                        "censor_reason_by_id": {
                            trade_id: row["censor_reason"]
                            for trade_id, row in rows.items()
                            if row.get("censor_reason")
                        },
                        "source_gap_ids": sorted(trade_id for trade_id, row in rows.items()
                                                 if row.get("status") == "source_gap"),
                    } for key, rows in candidates.items()
                }
        for pair_name in market_result["pairs"]:
            left, right = pair_name.split("×")
            for label, metric in market_result["pairs"][pair_name].items():
                a, b = label.split("|")
                left_metric = market_result["axes"][left].get(a)
                right_metric = market_result["axes"][right].get(b)
                pair_ev = metric["train"]["paired_ev_pct"]
                left_ev = (left_metric or {}).get("train", {}).get("paired_ev_pct")
                right_ev = (right_metric or {}).get("train", {}).get("paired_ev_pct")
                same_support = (
                    metric["comparison_support_ids"]
                    == (left_metric or {}).get("comparison_support_ids")
                    == (right_metric or {}).get("comparison_support_ids")
                )
                metric["train_interaction_ev_pct"] = (
                    round(pair_ev - left_ev - right_ev, 6)
                    if same_support and None not in (pair_ev, left_ev, right_ev)
                    else None
                )
        market_result["combinations"] = {}
        if len(days) >= 7 and len(usable) >= 40 and exposed:
            latest_id = max(usable, key=lambda trade_id: (
                valid_dates[trade_id], trade_id
            ))
            baseline = usable[latest_id]["incumbent"][market]
            pools: dict[str, tuple] = {}
            for axis in THRESHOLD_KEYS:
                choices = []
                for value, metric in market_result["axes"][axis].items():
                    ev = metric["train"]["paired_ev_pct"]
                    if ev is not None and float(value) != float(baseline[axis]):
                        choices.append((ev, float(value)))
                for pair_name, metrics in market_result["pairs"].items():
                    pair_axes = pair_name.split("×")
                    if axis not in pair_axes:
                        continue
                    axis_index = pair_axes.index(axis)
                    for label, metric in metrics.items():
                        ev = metric["train_interaction_ev_pct"]
                        value = float(label.split("|")[axis_index])
                        if ev is not None and value != float(baseline[axis]):
                            choices.append((ev, value))
                ranked = sorted(choices, key=lambda row: (-row[0], row[1]))
                two = []
                for _, value in ranked:
                    if value not in two:
                        two.append(value)
                    if len(two) == 2:
                        break
                pools[axis] = (baseline[axis], *two)
            market_result["train_frozen_axis_pools"] = {
                axis: list(values) for axis, values in pools.items()
            }
            market_result["train_frozen_pool_sha256"] = _digest(
                market_result["train_frozen_axis_pools"]
            )
            for values in itertools.product(*(pools[axis] for axis in THRESHOLD_KEYS)):
                changes = dict(zip(THRESHOLD_KEYS, values))
                if changes[THRESHOLD_KEYS[3]] < changes[THRESHOLD_KEYS[2]]:
                    continue
                rows = evaluate(changes)
                train_rows = [(by_id[trade_id], row) for trade_id, row in rows.items()
                              if trade_id in common
                              and valid_dates[trade_id] not in holdout_days]
                holdout_rows = [(by_id[trade_id], row) for trade_id, row in rows.items()
                                if trade_id in common
                                and valid_dates[trade_id] in holdout_days]
                label = "|".join(str(value) for value in values)
                market_result["combinations"][label] = {
                    "values": changes, "train": _metric(train_rows),
                    "holdout": _metric(holdout_rows),
                    "comparison_support_ids": sorted(common),
                    "pairable_ids": sorted(trade_id for trade_id, row in rows.items()
                                           if row.get("paired_delta_pnl_krw") is not None),
                        "censored_ids": sorted(trade_id for trade_id, row in rows.items()
                                               if str(row.get("status") or "").startswith("censored_")),
                        "censor_reason_by_id": {
                            trade_id: row["censor_reason"]
                            for trade_id, row in rows.items()
                            if row.get("censor_reason")
                        },
                }
        market_result["status"] = "research_only_no_live_candidate"
    if len(days) >= 7 and len(usable) >= 40:
        market_choices = {}
        for market in START_MARKETS:
            latest_id = max(usable, key=lambda trade_id: (
                valid_dates[trade_id], trade_id
            ))
            incumbent = usable[latest_id]["incumbent"][market]
            if not result["markets"][market]["exposed_ids"]:
                market_choices[market] = [incumbent]
                continue
            combos = result["markets"][market]["combinations"]
            ranked = sorted(
                (row for row in combos.values()
                 if row["train"]["n"] >= 30
                 and row["train"]["paired_ev_pct"] is not None
                 and row["values"] != incumbent),
                key=lambda row: (-row["train"]["paired_ev_pct"],
                                 sum(row["values"][axis] != incumbent[axis]
                                     for axis in THRESHOLD_KEYS),
                                 _digest(row["values"])),
            )
            market_choices[market] = [incumbent, *(row["values"] for row in ranked[:2])]
        joint = {}
        joint_replays = {}
        for vectors in itertools.product(*(market_choices[market] for market in START_MARKETS)):
            candidate = dict(zip(START_MARKETS, vectors))
            digest = market_values_hash(candidate)
            replayed = {
                trade_id: replay_vector(
                    by_id[trade_id], item, candidate,
                    actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
                ) for trade_id, item in usable.items()
            }
            joint_replays[digest] = replayed
            joint[digest] = {"values": candidate}
        joint_common = set(usable)
        for replayed in joint_replays.values():
            joint_common.intersection_update(
                trade_id for trade_id, row in replayed.items()
                if row.get("paired_delta_pnl_krw") is not None
            )
        result["joint_common_support_ids"] = sorted(joint_common)
        result["joint_grid_censored_or_gap_ids"] = sorted(set(usable) - joint_common)
        for digest, replayed in joint_replays.items():
            paired = {trade_id: row for trade_id, row in replayed.items()
                      if row.get("paired_delta_pnl_krw") is not None}
            train = [(by_id[trade_id], replayed[trade_id]) for trade_id in joint_common
                     if valid_dates[trade_id] not in holdout_days]
            holdout = [(by_id[trade_id], replayed[trade_id]) for trade_id in joint_common
                       if valid_dates[trade_id] in holdout_days]
            joint[digest].update({
                "train": _metric(train), "holdout": _metric(holdout),
                "comparison_support_ids": sorted(joint_common),
                "pairable_ids": sorted(paired),
                "excluded_ids": sorted(set(all_ids) - joint_common),
                "censored_ids": sorted(trade_id for trade_id, row in replayed.items()
                                       if str(row.get("status") or "").startswith("censored_")),
                "censor_reason_by_id": {
                    trade_id: row["censor_reason"]
                    for trade_id, row in replayed.items()
                    if row.get("censor_reason")
                },
                "source_gap_ids": sorted(trade_id for trade_id, row in replayed.items()
                                        if row.get("status") == "source_gap"),
                "evidence_grade_counts": dict(Counter(
                    replayed[trade_id].get("evidence_grade") for trade_id in joint_common
                )),
            })
        result["joint_three_market"] = joint
        result["joint_candidate_count"] = len(joint)
        result["joint_train_ranked_sha256"] = [
            digest for digest, row in sorted(
                joint.items(), key=lambda item: (
                    -(item[1]["train"]["paired_ev_pct"]
                      if item[1]["train"]["paired_ev_pct"] is not None
                      else float("-inf")),
                    sum(
                        item[1]["values"][market][axis]
                        != usable[latest_id]["incumbent"][market][axis]
                        for market in START_MARKETS for axis in THRESHOLD_KEYS
                    ),
                    item[0]
                )
            )
        ]
        if result["joint_train_ranked_sha256"]:
            winner_sha = result["joint_train_ranked_sha256"][0]
            winner = joint[winner_sha]
            holdout_pairs = [(by_id[trade_id], replay_vector(
                by_id[trade_id], usable[trade_id], winner["values"],
                actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
            )) for trade_id in winner["comparison_support_ids"]
                if valid_dates[trade_id] in holdout_days]
            day_metrics = [
                _metric([pair for pair in holdout_pairs
                         if valid_dates[str(pair[0]["id"])] == day])["paired_ev_pct"]
                for day in holdout_days
            ]
            day_min = min(day_metrics) if day_metrics and all(
                value is not None for value in day_metrics
            ) else None
            slippage_day_metrics = {
                str(bps): [
                    _metric([pair for pair in holdout_pairs
                             if valid_dates[str(pair[0]["id"])] == day])[
                        "execution_slippage_sensitivity"][str(bps)]["paired_ev_pct"]
                    for day in holdout_days
                ]
                for bps in SLIPPAGE_SENSITIVITY_BPS
            }
            worst_slippage_day_ev = [
                value for values in slippage_day_metrics.values() for value in values
            ]
            worst_slippage_day_min = (
                min(worst_slippage_day_ev)
                if worst_slippage_day_ev and all(
                    value is not None for value in worst_slippage_day_ev
                ) else None
            )
            excluded_notional = sum(
                float(by_id[trade_id].get("buy_fill_amount") or 0)
                for trade_id in set(all_ids) - joint_common
            )
            excluded_holdout_notional = sum(
                float(by_id[trade_id].get("buy_fill_amount") or 0)
                for trade_id in set(all_ids) - joint_common
                if valid_dates[trade_id] in holdout_days
            )
            conservative_holdout_delta = (
                winner["holdout"]["delta_net_krw"] - excluded_holdout_notional
            )
            slippage_delta_sensitivity = {
                str(bps): round(
                    winner["holdout"]["execution_slippage_sensitivity"][str(bps)][
                        "delta_net_krw"
                    ] - excluded_holdout_notional,
                    2,
                )
                for bps in SLIPPAGE_SENSITIVITY_BPS
            }
            conservative_slippage_delta = min(slippage_delta_sensitivity.values())
            result["joint_selection_evidence"] = {
                "winner_sha256": winner_sha,
                "holdout_min_day_ev_pct": day_min,
                "holdout_min_day_ev_by_slippage_bps": slippage_day_metrics,
                "holdout_worst_slippage_min_day_ev_pct": worst_slippage_day_min,
                "unpaired_worst_case_notional_krw": excluded_notional,
                "unpaired_holdout_worst_case_notional_krw": excluded_holdout_notional,
                "holdout_conservative_delta_krw": conservative_holdout_delta,
                "holdout_conservative_delta_by_slippage_bps": slippage_delta_sensitivity,
                "holdout_conservative_worst_slippage_delta_krw": conservative_slippage_delta,
                "tail_review_required": bool(
                    winner["train"]["large_loss_worsened_ids"]
                    or winner["holdout"]["large_loss_worsened_ids"]
                ),
                "multiple_comparison_candidate_count": len(joint),
            }
            if (winner["train"]["n"] >= 30 and winner["holdout"]["n"] >= 10
                    and len(holdout_days) >= 2 and day_min is not None and day_min > 0
                    and conservative_holdout_delta > 0
                    and worst_slippage_day_min is not None
                    and worst_slippage_day_min > 0
                    and conservative_slippage_delta > 0
                    and not result["joint_selection_evidence"]["tail_review_required"]
                    and winner["values"] != {
                        market: usable[latest_id]["incumbent"][market]
                        for market in START_MARKETS
                    }):
                result["research_candidate"] = {
                    "values": winner["values"], "market_values_sha256": winner_sha,
                    "evidence_grade_counts": winner["evidence_grade_counts"],
                    "decision_authority": "research_candidate_requires_policy_selection",
                }
                result["status"] = "research_candidate_holdout_positive_review_required"
    result.setdefault("status", "research_only_no_live_candidate")
    return result
