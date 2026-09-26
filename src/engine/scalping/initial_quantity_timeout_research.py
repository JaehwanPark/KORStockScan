"""Source-only EV search for quantity-type entry bundle wait budgets.

The replay assumes sequential leg activation and a fixed actual exit. A price
cross is a conditional fill, not broker execution or cancel terminal proof.
"""

from __future__ import annotations

import argparse
import json
import math
import resource
import time
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any

from src.engine.scalping.initial_quantity_policy import (
    BASELINE, _SHAPES, _block_io_wait_ms, _digest, _exit_at, _quantity_parts,
    _type_from_decision_receipt, _write_immutable_json,
    _paired_candidate, completed_trade_fact_census, join_post_fill_paths,
)
from src.engine.scalping.initial_quantity_timeout import build_bundle_timeout_schedule
from src.engine.scalping.initial_quantity_type import QUANTITY_TYPES, kst_timestamp
from src.engine.trade_profit import get_trade_cost_rate
from src.trading.order.split_execution_math import pct_price_offset
from src.trading.order.tick_utils import get_tick_size, move_price_by_ticks
from src.utils.constants import DATA_DIR

HORIZONS_SEC = (30, 60, 90, 120, 180, 240, 300, 420, 600, 900, 1200)
CANCEL_CONFIRM_RESERVES_SEC = (5, 10)
SCHEMA = "initial_quantity_timeout_ev_research_v1"


def _unique_fills(path: dict[str, Any]) -> list[dict[str, Any]]:
    unique = {}
    for fill in path.get("fills") or []:
        key = ((fill.get("order_no"), fill.get("execution_no"))
               if fill.get("order_no") and fill.get("execution_no") else
               (fill["at"].isoformat(), fill.get("price"), fill.get("qty")))
        unique[key] = fill
    return sorted(unique.values(), key=lambda row: row["at"])


def _fill_latest_possible_at(fill: dict[str, Any]):
    """Preserve the interval represented by a second-precision broker clock."""
    precision = fill.get("clock_precision_sec", 0)
    if precision not in (0, 1):
        return None
    latest = fill["at"] + timedelta(seconds=precision)
    emitted = fill.get("emitted_at")
    if emitted is not None:
        if emitted < fill["at"]:
            return None
        latest = min(latest, emitted)
    return latest


def _decision_before_fill(path: dict[str, Any], first: dict[str, Any]) -> dict[str, Any] | None:
    latest_fill_at = _fill_latest_possible_at(first)
    if latest_fill_at is None:
        return None
    eligible = [row for row in path.get("decisions") or []
                if row["at"] <= latest_fill_at
                and (latest_fill_at - row["at"]).total_seconds() <= 3600
                and (kst_timestamp(row["fields"].get("reference_time")) is None
                     or kst_timestamp(row["fields"]["reference_time"]) <= latest_fill_at)]
    sizing = [row for row in eligible if row["stage"] == "entry_execution_sizing_plan"]
    return max(sizing or eligible, key=lambda row: row["at"]) if eligible else None


def _order_start_before_fill(
    path: dict[str, Any], first: dict[str, Any], decision: dict[str, Any],
) -> dict[str, Any] | None:
    """Use the frozen submission clock for the same broker order, if present."""
    order_no = str(first.get("order_no") or "")
    latest_fill_at = _fill_latest_possible_at(first)
    if not order_no or latest_fill_at is None:
        return None
    eligible = [row for row in path.get("order_starts") or []
                if str(row.get("order_no") or "") == order_no
                and decision["at"] <= row["at"] <= latest_fill_at
                and row.get("latest_at", row["at"]) <=
                first.get("emitted_at", latest_fill_at)]
    if not eligible:
        return None
    direct = [row for row in eligible
              if row["source"] == "entry_cancel_wait_submission_context_frozen_at"]
    selected = direct or eligible
    return selected[0] if len(selected) == 1 else None


def _prices(anchor: int, shape: str) -> list[float]:
    offsets = _SHAPES[shape][1]
    if "tick" in shape:
        return [float(move_price_by_ticks(anchor, -int(offset))) for offset in offsets]
    return [float(pct_price_offset(anchor, offset)) for offset in offsets]


def _first_lower_from_decision(
    trade: dict[str, Any], path: dict[str, Any], first: dict[str, Any],
    decision: dict[str, Any],
) -> tuple[float, bool] | None:
    """Measure the post-fill low from decision even when order start is absent."""
    latest_fill_at = _fill_latest_possible_at(first)
    exit_at = _exit_at(trade)
    if latest_fill_at is None or exit_at is None:
        return None
    fields = decision["fields"]
    venue = str(fields.get("effective_venue") or fields.get("sizing_venue_at_allocation") or "")
    route = str(fields.get("classifier_route_key") or fields.get("ws_route") or "")
    epoch = str(fields.get("classifier_transport_epoch")
                or fields.get("market_data_transport_epoch") or "")
    end = min(exit_at, decision["at"] + timedelta(seconds=1200))
    lower = min((row for row in path.get("prices") or []
                 if latest_fill_at < row["at"] <= end
                 and row["venue"] == venue and row["price"] < first["price"]),
                key=lambda row: row["at"], default=None)
    if lower is None:
        return None
    return (round((lower["at"] - decision["at"]).total_seconds(), 3),
            bool(route and epoch and lower["route"] == route and lower["epoch"] == epoch))


def _net(legs: list[tuple[int, float]], sell_price: float, cost_rate: float) -> float:
    if not legs:
        return 0.0
    buy = sum(qty * price for qty, price in legs)
    sell = sell_price * sum(qty for qty, _ in legs)
    return sell - buy - cost_rate * (buy + sell)


def _timeout_case(
    trade: dict[str, Any], path: dict[str, Any], *, shape: str,
    horizon_sec: int, reserve_sec: int, policy_sha256: str,
) -> dict[str, Any]:
    if path.get("source_gap"):
        return {"status": "path_source_gap"}
    fills = _unique_fills(path)
    if not fills:
        return {"status": "broker_fill_clock_missing"}
    first = fills[0]
    latest_fill_at = _fill_latest_possible_at(first)
    if latest_fill_at is None:
        return {"status": "broker_fill_clock_invalid"}
    if sum(int(row["qty"]) for row in fills) != trade["buy_qty"]:
        return {"status": "fill_quantity_mismatch"}
    if first["at"].date().isoformat() != trade["entry_date"]:
        return {"status": "fill_entry_date_mismatch"}
    decision = _decision_before_fill(path, first)
    if decision is None:
        return {"status": "decision_clock_missing"}
    order_start = _order_start_before_fill(path, first, decision)
    if order_start is None:
        return {"status": "order_start_receipt_missing"}
    start_window_sec = round((order_start.get("latest_at", order_start["at"])
                              - order_start["at"]).total_seconds(), 6)
    if shape not in _SHAPES or shape == "parent":
        return {"status": "shape_not_supported"}
    probe_applied = bool(order_start.get("probe_applied"))
    if probe_applied and first["qty"] != 1:
        return {"status": "probe_first_fill_quantity_mismatch"}
    parts = ([1, *_quantity_parts(trade["buy_qty"] - 1, shape)]
             if probe_applied and trade["buy_qty"] > 1 else
             _quantity_parts(trade["buy_qty"], shape))
    if min(parts) <= 0:
        return {"status": "quantity_too_small"}
    if horizon_sec / len(parts) <= reserve_sec:
        return {"status": "leg_slot_shorter_than_confirmation_reserve"}
    anchor = first["price"]
    if not float(anchor).is_integer() or int(anchor) % get_tick_size(anchor):
        return {"status": "anchor_tick_invalid"}
    offsets = ([float(anchor), *_prices(int(anchor), shape)]
               if probe_applied else _prices(int(anchor), shape))
    if any(price <= 0 for price in offsets) or any(
            later > earlier or (later == earlier and not (probe_applied and index == 0))
            for index, (earlier, later) in enumerate(zip(offsets, offsets[1:]))):
        return {"status": "price_offset_invalid"}
    schedule = build_bundle_timeout_schedule(
        quantity_type=_type_from_decision_receipt(decision["fields"],
                                                   decision_at=decision["at"],
                                                   entry_at=latest_fill_at),
        policy_sha256=policy_sha256, decision_at=decision["at"].isoformat(),
        order_start_at=order_start["at"].isoformat(),
        total_wait_sec=horizon_sec, leg_count=len(parts),
        cancel_confirm_reserve_sec=reserve_sec,
    )
    exit_at = _exit_at(trade)
    if exit_at is None or exit_at <= latest_fill_at:
        return {"status": "exit_clock_unsupported"}
    quality = (first.get("clock_source") == "broker_execution_observed_at"
               and bool(first.get("order_no")) and bool(first.get("execution_no")))
    first_slot = schedule["slots"][0]
    if latest_fill_at.timestamp() >= first_slot["cancel_request_by_epoch"]:
        modeled_pnl = 0.0
        return {"status": "modeled", "fill_state": "primary_missed",
                "quantity_type": schedule["quantity_type"],
                "decision_at": decision["at"].isoformat(),
                "order_start_at": order_start["at"].isoformat(),
                "order_start_clock_source": order_start["source"],
                "order_start_window_sec": start_window_sec,
                "probe_included_in_leg_count": probe_applied,
                "modeled_leg_count": len(parts),
                "first_fill_clock_source": first.get("clock_source"),
                "broker_clock_verified": quality,
                "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
                "parent_net_pct": trade["profit_rate"],
                "candidate_net_pnl_krw": modeled_pnl,
                "conservative_net_pnl_krw": modeled_pnl,
                "candidate_net_pct": 0.0, "conservative_net_pct": 0.0,
                "conditional_crossed_leg_count": 0,
                "verified_route_epoch_price_cross_count": 0,
                "first_post_fill_lower_elapsed_sec": None}
    fields = decision["fields"]
    venue = str(fields.get("effective_venue") or fields.get("sizing_venue_at_allocation") or "")
    route = str(fields.get("classifier_route_key") or fields.get("ws_route") or "")
    epoch = str(fields.get("classifier_transport_epoch")
                or fields.get("market_data_transport_epoch") or "")
    observations = sorted((row for row in path.get("prices") or []
                           if latest_fill_at < row["at"] <= exit_at
                           and row["at"].timestamp() <= schedule["bundle_deadline_epoch"]
                           and row["venue"] == venue), key=lambda row: row["at"])
    if not observations:
        return {"status": "post_fill_path_missing"}
    first_lower = next((row for row in observations if row["price"] < anchor), None)
    lower_elapsed = (round((first_lower["at"] - decision["at"]).total_seconds(), 3)
                     if first_lower else None)
    crossed = [(parts[0], offsets[0])]
    touched = []
    verified_cross = 0
    for index, (qty, limit) in enumerate(zip(parts[1:], offsets[1:]), start=1):
        slot = schedule["slots"][index]
        if exit_at.timestamp() <= slot["slot_start_epoch"]:
            break
        available = [row for row in observations
                     if slot["slot_start_epoch"] <= row["at"].timestamp()
                     < min(slot["cancel_request_by_epoch"], exit_at.timestamp())]
        if not available:
            return {"status": "leg_window_source_gap", "leg_index": index,
                    "quantity_type": schedule["quantity_type"]}
        crossing = [row for row in available if row["price"] < limit]
        if crossing:
            crossed.append((qty, limit))
            if (quality and venue in {"KRX", "NXT"} and first["venue"] == venue
                    and route and epoch and any(row["route"] == route
                                                and row["epoch"] == epoch
                                                for row in crossing)):
                verified_cross += 1
        elif any(row["price"] == limit for row in available):
            touched.append((qty, limit))
    cost = get_trade_cost_rate()
    one_leg_pnl = _net(crossed[:1], trade["sell_price"], cost)
    candidate_pnl = _net(crossed, trade["sell_price"], cost)
    touched_pnl = _net(crossed + touched, trade["sell_price"], cost)
    conservative_pnl = min(one_leg_pnl, candidate_pnl, touched_pnl)
    notional = trade["buy_price"] * trade["buy_qty"]
    return {"status": "modeled", "fill_state": (
                "price_cross_conditional" if len(crossed) > 1 else
                "price_touch_only" if touched else "no_cross_observed"),
            "quantity_type": schedule["quantity_type"],
            "decision_at": decision["at"].isoformat(),
            "order_start_at": order_start["at"].isoformat(),
            "order_start_clock_source": order_start["source"],
            "order_start_window_sec": start_window_sec,
            "probe_included_in_leg_count": probe_applied,
            "modeled_leg_count": len(parts),
            "first_fill_clock_source": first.get("clock_source"),
            "broker_clock_verified": quality,
            "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
            "parent_net_pct": trade["profit_rate"],
            "candidate_net_pnl_krw": round(candidate_pnl, 3),
            "conservative_net_pnl_krw": round(conservative_pnl, 3),
            "candidate_net_pct": round(100 * candidate_pnl / notional, 6),
            "conservative_net_pct": round(100 * conservative_pnl / notional, 6),
            "conditional_crossed_leg_count": len(crossed) - 1,
            "verified_route_epoch_price_cross_count": verified_cross,
            "first_post_fill_lower_elapsed_sec": lower_elapsed,
            "cancel_confirmation_model": "assumed_within_reserve_not_broker_verified"}


def build_timeout_research(
    as_of: str, *, data_dir: Path = DATA_DIR,
    fact_rows: list[dict[str, Any]] | None = None,
    horizons: tuple[int, ...] = HORIZONS_SEC,
    reserves: tuple[int, ...] = CANCEL_CONFIRM_RESERVES_SEC,
    performance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Scan the whole completed-trade manifest once for all timeout arms."""
    started = time.perf_counter()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    wait_start = _block_io_wait_ms()
    trades, census = completed_trade_fact_census(as_of, fact_rows=fact_rows,
                                                  data_dir=data_dir)
    eligible = [trade for trade in trades
                if census["source_quality_by_entry_date"][trade["entry_date"]]
                ["tuning_input_allowed"]
                and census["source_quality_by_exit_date"][trade["exit_date"]]
                ["tuning_input_allowed"]]
    scan_seconds: dict[str, float] = {}
    sources: dict[str, Any] = {}
    paths = join_post_fill_paths(eligible, data_dir=data_dir,
                                 scan_seconds=scan_seconds, source_receipts=sources,
                                 price_horizon_seconds=max(horizons))
    case_seconds = []
    counts = Counter()
    paired: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    first_lower_by_type: dict[str, list[float]] = defaultdict(list)
    winning_first_lower_by_type: dict[str, list[tuple[float, float]]] = defaultdict(list)
    verified_lower_by_type = Counter()
    decision_to_start_by_type: dict[str, list[float]] = defaultdict(list)
    type_counts = Counter()
    classifier_mismatch_trade_ids = []
    type_trades: dict[str, list[dict[str, Any]]] = defaultdict(list)
    policy_hash = "0" * 64  # fixed research identity; never an active policy hash
    for trade in trades:
        path = paths.get(trade["trade_id"])
        quality_allowed = bool(
            census["source_quality_by_entry_date"][trade["entry_date"]]["tuning_input_allowed"]
            and census["source_quality_by_exit_date"][trade["exit_date"]]["tuning_input_allowed"])
        actual_type = "SAFE_UNKNOWN"
        if path:
            actual_type = _paired_candidate(trade, path, "parent")["quantity_type"]
            fills = _unique_fills(path)
            decision = _decision_before_fill(path, fills[0]) if fills else None
            if decision:
                latest_fill_at = _fill_latest_possible_at(fills[0])
                replay_type = _type_from_decision_receipt(
                    decision["fields"], decision_at=decision["at"],
                    entry_at=latest_fill_at)
                if replay_type != actual_type:
                    classifier_mismatch_trade_ids.append(trade["trade_id"])
                if quality_allowed and not path.get("source_gap"):
                    lower = _first_lower_from_decision(trade, path, fills[0], decision)
                    if lower is not None:
                        first_lower_by_type[actual_type].append(lower[0])
                        verified_lower_by_type[actual_type] += lower[1]
                        if trade["realized_net_pnl_krw"] > 0 and trade["profit_rate"] > 0:
                            winning_first_lower_by_type[actual_type].append((
                                lower[0], trade["realized_net_pnl_krw"]))
                    order_start = _order_start_before_fill(path, fills[0], decision)
                    if order_start is not None:
                        decision_to_start_by_type[actual_type].append(round(
                            (order_start["at"] - decision["at"]).total_seconds(), 3))
        type_counts[actual_type] += 1
        type_trades[actual_type].append(trade)
        for shape in _SHAPES:
            if shape == "parent":
                continue
            for reserve in reserves:
                for horizon in horizons:
                    key = f"{shape}:{reserve}:{horizon}"
                    case_started = time.perf_counter()
                    result = (_timeout_case(trade, path, shape=shape,
                                            horizon_sec=horizon, reserve_sec=reserve,
                                            policy_sha256=policy_hash)
                              if path else {"status": (
                                  "path_join_missing" if quality_allowed else
                                  "source_quality_blocked")})
                    case_seconds.append(time.perf_counter() - case_started)
                    counts[f"{key}:{result['status']}"] += 1
                    if (result["status"] == "modeled"
                            and result["quantity_type"] == actual_type):
                        paired[actual_type][key].append({**result,
                                                         "trade_id": trade["trade_id"]})
    selections = {}
    for quantity_type in QUANTITY_TYPES:
        source_rows = type_trades[quantity_type]
        # Type counts are assigned before model support; no candidate may
        # quietly replace that denominator with only crossed-price trades.
        parent_net = sum(trade["realized_net_pnl_krw"] for trade in source_rows)
        parent_ev = (sum(trade["profit_rate"] for trade in source_rows) / len(source_rows)
                     if source_rows else None)
        winners = [trade for trade in source_rows
                   if trade["realized_net_pnl_krw"] > 0 and trade["profit_rate"] > 0]
        winner_weights = {trade["trade_id"]: trade["realized_net_pnl_krw"]
                          for trade in winners}
        winner_weight = sum(winner_weights.values())
        winner_parent_ev = (sum(trade["profit_rate"] * trade["realized_net_pnl_krw"]
                                for trade in winners) / winner_weight
                            if winner_weight else None)
        candidates = {}
        for shape in _SHAPES:
            if shape == "parent":
                continue
            for reserve in reserves:
                for horizon in horizons:
                    key = f"{shape}:{reserve}:{horizon}"
                    values = paired[quantity_type][key]
                    delta_net = sum(row["candidate_net_pnl_krw"] - row["parent_net_pnl_krw"]
                                    for row in values)
                    delta_conservative_net = sum(
                        row["conservative_net_pnl_krw"] - row["parent_net_pnl_krw"]
                        for row in values)
                    delta_ev = sum(row["candidate_net_pct"] - row["parent_net_pct"]
                                   for row in values)
                    delta_conservative_ev = sum(
                        row["conservative_net_pct"] - row["parent_net_pct"]
                        for row in values)
                    weighted_winner_delta = sum(
                        winner_weights[row["trade_id"]] * (
                            row["conservative_net_pct"] - row["parent_net_pct"])
                        for row in values if row["trade_id"] in winner_weights)
                    # Parent profit_rate is the canonical costed rate. PnL
                    # delta is reported separately to avoid false EV claims.
                    candidates[key] = {
                        "modeled_count": len(values),
                        "winner_modeled_count": sum(
                            row["trade_id"] in winner_weights for row in values),
                        "winner_weighted_conservative_ev_pct": (
                            round(winner_parent_ev + weighted_winner_delta /
                                  winner_weight, 6) if winner_weight else None),
                        "probe_first_modeled_count": sum(
                            row["probe_included_in_leg_count"] for row in values),
                        "order_start_source_counts": dict(sorted(Counter(
                            row["order_start_clock_source"] for row in values).items())),
                        "max_order_start_window_sec": (
                            max(row["order_start_window_sec"] for row in values)
                            if values else None),
                        "coverage_of_all_completed": (round(len(values) / len(trades), 6)
                                                      if trades else 0.0),
                        "conditional_cross_count": sum(
                            row["conditional_crossed_leg_count"] > 0 for row in values),
                        "verified_cross_count": sum(
                            row["verified_route_epoch_price_cross_count"] > 0
                            for row in values),
                        "primary_missed_count": sum(
                            row["fill_state"] == "primary_missed" for row in values),
                        "estimated_net_pnl_krw": round(parent_net + delta_net, 3),
                        "conservative_net_pnl_krw": round(
                            parent_net + delta_conservative_net, 3),
                        "estimated_ev_pct": (round(parent_ev + delta_ev / len(source_rows), 6)
                                             if source_rows and parent_ev is not None else None),
                        "conservative_ev_pct": (
                            round(parent_ev + delta_conservative_ev / len(source_rows), 6)
                            if source_rows and parent_ev is not None else None),
                    }
        ranked = [(value["estimated_ev_pct"], key) for key, value in candidates.items()
                  if value["estimated_ev_pct"] is not None and value["modeled_count"] > 0]
        best_key = max(ranked)[1] if ranked else None
        conservative_ranked = [
            (value["conservative_ev_pct"], key) for key, value in candidates.items()
            if value["conservative_ev_pct"] is not None and value["modeled_count"] > 0]
        conservative_best_key = max(conservative_ranked)[1] if conservative_ranked else None
        lower_times = sorted(first_lower_by_type[quantity_type])
        winning_lower = winning_first_lower_by_type[quantity_type]
        winning_lower_weight = sum(weight for _, weight in winning_lower)
        start_lags = sorted(decision_to_start_by_type[quantity_type])
        selections[quantity_type] = {
            "all_completed_type_count": type_counts[quantity_type],
            "parent_costed_ev_pct": round(parent_ev, 6) if parent_ev is not None else None,
            "winner_weight_kind": "positive_realized_net_pnl_krw",
            "winner_count": len(winners),
            "winner_weight_sum_krw": round(winner_weight, 3),
            "winner_weighted_parent_ev_pct": (
                round(winner_parent_ev, 6) if winner_parent_ev is not None else None),
            "winner_first_post_fill_lower_count": len(winning_lower),
            "winner_weighted_first_post_fill_lower_sec": (
                round(sum(elapsed * weight for elapsed, weight in winning_lower) /
                      winning_lower_weight, 3) if winning_lower_weight else None),
            "modeled_best_arm": best_key,
            "modeled_best_ev_pct": candidates[best_key]["estimated_ev_pct"] if best_key else None,
            "modeled_conservative_best_arm": conservative_best_key,
            "modeled_conservative_best_ev_pct": (
                candidates[conservative_best_key]["conservative_ev_pct"]
                if conservative_best_key else None),
            "policy_selected_total_wait_sec": None,
            "policy_status": "source_only_cancel_terminal_and_fill_proof_missing",
            "first_post_fill_lower_count": len(lower_times),
            "first_post_fill_lower_verified_route_epoch_count": (
                verified_lower_by_type[quantity_type]),
            "first_post_fill_lower_p50_sec": (
                lower_times[len(lower_times) // 2] if lower_times else None),
            "first_post_fill_lower_p95_sec": (
                lower_times[math.ceil(len(lower_times) * .95) - 1]
                if lower_times else None),
            "decision_to_order_start_count": len(start_lags),
            "decision_to_order_start_p50_sec": (
                start_lags[len(start_lags) // 2] if start_lags else None),
            "decision_to_order_start_p95_sec": (
                start_lags[math.ceil(len(start_lags) * .95) - 1]
                if start_lags else None),
            "candidate_metrics": candidates,
        }
    body = {"schema": SCHEMA, "source_date": as_of,
            "entry_on_or_after": BASELINE.isoformat(),
            "generation_kind": "initial_completed_trade_timeout_research",
            "runtime_effect": False, "runtime_apply_allowed": False,
            "broker_order_forbidden": True, "actual_order_submitted": False,
            "decision_clock_origin": "entry_execution_sizing_plan_pre_fill",
            "timeout_clock_origin": "same_order_submission_context_frozen_at_proxy",
            "probe_included_in_leg_count": True, "sequential_activation": True,
            "max_bundle_wait_sec": 1200,
            "horizons_sec": list(horizons), "cancel_confirm_reserves_sec": list(reserves),
            "cancel_confirmation_evidence": "hypothetical_reserve_only_no_broker_terminal",
            "fixed_exit_assumption": True,
            "census": census, "pipeline_source_receipts": sources,
            "case_counts": dict(sorted(counts.items())),
            "quantity_type_counts": dict(sorted(type_counts.items())),
            "classifier_mismatch_trade_ids": sorted(classifier_mismatch_trade_ids),
            "selections": selections}
    if performance is not None:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        wait_end = _block_io_wait_ms()
        ordered = sorted(case_seconds)
        performance.update({
            "wall_seconds": round(time.perf_counter() - started, 3),
            "cpu_user_seconds": round(usage.ru_utime - usage_start.ru_utime, 3),
            "cpu_system_seconds": round(usage.ru_stime - usage_start.ru_stime, 3),
            "peak_rss_kb": usage.ru_maxrss,
            "swap_operations": usage.ru_nswap - usage_start.ru_nswap,
            "read_blocks": usage.ru_inblock - usage_start.ru_inblock,
            "write_blocks": usage.ru_oublock - usage_start.ru_oublock,
            "block_io_wait_ms": (round(wait_end - wait_start, 3)
                                 if wait_start is not None and wait_end is not None else None),
            "case_evaluation_p95_ms": (round(ordered[math.ceil(len(ordered)*.95)-1]*1000, 3)
                                       if ordered else None),
            "case_evaluation_p99_ms": (round(ordered[math.ceil(len(ordered)*.99)-1]*1000, 3)
                                       if ordered else None),
            "candidate_case_count": len(case_seconds),
            "date_scan_seconds": scan_seconds,
        })
    return {**body, "report_content_sha256": _digest(body)}


def timeout_research_valid(report: Any) -> bool:
    """Reject incomplete or self-inconsistent source-only timeout research."""
    if not isinstance(report, dict):
        return False
    try:
        body = {key: value for key, value in report.items()
                if key != "report_content_sha256"}
        census = report["census"]
        total = census["all_completed_initial_trades"]
        shapes = [shape for shape in _SHAPES if shape != "parent"]
        horizons = report["horizons_sec"]
        reserves = report["cancel_confirm_reserves_sec"]
        if (report.get("schema") != SCHEMA
                or report.get("report_content_sha256") != _digest(body)
                or report.get("runtime_effect") is not False
                or report.get("runtime_apply_allowed") is not False
                or report.get("broker_order_forbidden") is not True
                or report.get("actual_order_submitted") is not False
                or report.get("max_bundle_wait_sec") != 1200
                or report.get("timeout_clock_origin") !=
                "same_order_submission_context_frozen_at_proxy"
                or type(total) is not int or total <= 0
                or not isinstance(horizons, list) or not horizons
                or not isinstance(reserves, list) or not reserves
                or any(type(value) is not int or not 1 <= value <= 1200
                       for value in horizons)
                or any(type(value) is not int or value <= 0 for value in reserves)
                or census["input_manifest_sha256"] != _digest(census["input_fact_rows"])
                or set(report["selections"]) != set(QUANTITY_TYPES)
                or sum(report["quantity_type_counts"].values()) != total):
            return False
        mismatches = report["classifier_mismatch_trade_ids"]
        if (not isinstance(mismatches, list) or len(mismatches) != len(set(mismatches))
                or len(mismatches) > total):
            return False
        for shape in shapes:
            for reserve in reserves:
                for horizon in horizons:
                    key = f"{shape}:{reserve}:{horizon}"
                    counted = sum(value for name, value in report["case_counts"].items()
                                  if name.startswith(f"{key}:"))
                    if counted != total:
                        return False
                    for quantity_type in QUANTITY_TYPES:
                        selection = report["selections"][quantity_type]
                        metric = selection["candidate_metrics"][key]
                        modeled = metric["modeled_count"]
                        if (type(modeled) is not int or not 0 <= modeled <=
                                selection["all_completed_type_count"]
                                or not 0 <= selection["first_post_fill_lower_verified_route_epoch_count"]
                                <= selection["first_post_fill_lower_count"]
                                <= selection["all_completed_type_count"]
                                or not 0 <= selection["decision_to_order_start_count"]
                                <= selection["all_completed_type_count"]
                                or sum(metric["order_start_source_counts"].values()) != modeled
                                or any(source not in {
                                    "entry_cancel_wait_submission_context_frozen_at",
                                    "order_leg_request_to_sent_bracket"}
                                       for source in metric["order_start_source_counts"])
                                or type(metric["probe_first_modeled_count"]) is not int
                                or not 0 <= metric["probe_first_modeled_count"] <= modeled
                                or (metric["max_order_start_window_sec"] is None) !=
                                (modeled == 0)
                                or (modeled > 0 and not
                                    0 <= metric["max_order_start_window_sec"] <= 120)
                                or type(metric["verified_cross_count"]) is not int
                                or not 0 <= metric["verified_cross_count"] <=
                                metric["conditional_cross_count"] <= modeled
                                or abs(metric["coverage_of_all_completed"] -
                                       round(modeled / total, 6)) > 1e-6
                                or selection["policy_selected_total_wait_sec"] is not None):
                            return False
        return True
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    performance: dict[str, Any] = {}
    report = build_timeout_research(args.as_of, performance=performance)
    if not timeout_research_valid(report):
        raise ValueError("timeout_research_self_validation_failed")
    path = args.output_dir / (f"initial_quantity_timeout_research_{args.as_of}_"
                              f"{report['report_content_sha256'][:12]}.json")
    file_sha = _write_immutable_json(path, report)
    print(json.dumps({"path": str(path.resolve()), "file_sha256": file_sha,
                      "report_content_sha256": report["report_content_sha256"],
                      "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
                      "performance": performance}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
