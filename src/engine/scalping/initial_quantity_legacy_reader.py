"""Frozen v1 economic reader for already sealed quantity ancestors.

This version cannot produce a new refresh selection. Keep v1 semantics when
validating old pinned evidence; v2 producers use the repaired contracts.
Ownership: offline SCALPING quantity evidence compatibility, no order authority.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Any
from collections import Counter, defaultdict
from src.engine.scalping.initial_quantity_policy import (
    _SHAPES, _CAP_MODES, _TYPES, _number, _timestamp, _digest, _file_sha256,
    _cap_target_qty, _costed_fixed_exit_pnl, _select_initial_winner_shape,
    REPORT_SCHEMA, COST_MODEL, CAP_FILL_MODEL, get_trade_cost_rate,
    calculate_net_realized_pnl, calculate_net_profit_rate, get_tick_size,
)
def _cap_candidate_trade(
    trade: dict[str, Any], source: dict[str, Any], mode: str,
    cost_rate: float,
) -> dict[str, Any]:
    """Use exact fills first; require bound depth and later prints for extras."""
    context = source.get("context")
    target = _cap_target_qty(context, mode)
    if target is None:
        return {"status": "allocator_context_missing_or_invalid"}
    if target == 0:
        return {"status": "zero_quantity_action_change_forbidden"}
    fills = source.get("fills")
    if not isinstance(fills, list) or not fills:
        return {"status": "broker_fill_ledger_missing"}
    ordered = sorted(fills, key=lambda item: str(item.get("at") or ""))
    if (any(type(fill.get("qty")) is not int or fill["qty"] <= 0
            or _number(fill.get("price")) is None or fill["price"] <= 0
            or _timestamp(fill.get("at")) is None for fill in ordered)
            or sum(fill["qty"] for fill in ordered) != trade["buy_qty"]
            or abs(sum(fill["qty"] * fill["price"] for fill in ordered)
                   / trade["buy_qty"] - trade["buy_price"]) > 1.0
            or context["actual_effective_qty"] < trade["buy_qty"]):
        return {"status": "broker_fill_ledger_fact_mismatch"}
    remaining = target
    candidate_legs: list[tuple[int, float]] = []
    for fill in ordered:
        taken = min(remaining, fill["qty"])
        if taken:
            candidate_legs.append((taken, fill["price"]))
            remaining -= taken
    extra_source = "not_needed"
    if remaining:
        depth = context.get("ask_depth_source")
        ticks = source.get("following_ticks")
        first_at = _timestamp(ordered[0]["at"])
        if (isinstance(depth, dict) and isinstance(ticks, list)
                and depth.get("source_type") == "ws_0D_bound_snapshot"
                and depth.get("market_route") in {"KRX", "NXT"}
                and type(depth.get("transport_epoch")) is int
                and _number(depth.get("observed_epoch")) is not None
                and isinstance(depth.get("levels"), list)
                and all(fill.get("venue") == depth.get("market_route")
                        for fill in ordered)
                and first_at is not None
                and 0 <= first_at.timestamp() - float(depth["observed_epoch"]) <= 120):
            identity = (source.get("attempt_id"), source.get("plan_sha256"))
            unique_ticks = {(_number(tick.get("observed_epoch")),
                             tick.get("price_krw"), tick.get("quantity"),
                             tick.get("item")): tick for tick in ticks
                            if isinstance(tick, dict)
                            and (tick.get("attempt_id"), tick.get("plan_sha256"))
                            == identity
                            and tick.get("depth_item") == depth.get("item")
                            and tick.get("market_route") == depth.get("market_route")
                            and tick.get("transport_epoch") ==
                            depth.get("transport_epoch")
                            and type(tick.get("observed_epoch")) in (int, float)
                            and math.isfinite(tick["observed_epoch"])
                            and type(tick.get("price_krw")) is int
                            and type(tick.get("quantity")) is int
                            and tick["quantity"] > 0}
            previous_level_price = 0
            for level in depth["levels"][:5]:
                if (not isinstance(level, dict)
                        or type(level.get("price_krw")) is not int
                        or type(level.get("quantity")) is not int
                        or level["price_krw"] <= 0 or level["quantity"] < 0):
                    break
                price = level["price_krw"]
                if (price <= previous_level_price or price % get_tick_size(price)
                        or candidate_legs and price <
                        min(fill_price for _, fill_price in candidate_legs)):
                    break
                previous_level_price = price
                observed_buy = sum(tick["quantity"] for tick in unique_ticks.values()
                                   if tick["price_krw"] == price
                                   and first_at.timestamp() <
                                   tick["observed_epoch"] <=
                                   first_at.timestamp() + 1200)
                already_filled = sum(qty for qty, fill_price in candidate_legs
                                     if fill_price == price)
                available = max(0, min(level["quantity"], observed_buy)
                                - already_filled)
                taken = min(remaining, available)
                if taken:
                    candidate_legs.append((taken, price))
                    remaining -= taken
                if remaining == 0:
                    break
            extra_source = ("bound_depth_and_following_0b" if remaining == 0
                            else "insufficient_bound_depth_or_following_0b")
        else:
            extra_source = "bound_depth_or_following_0b_missing"
    pnl = _costed_fixed_exit_pnl(candidate_legs, trade["sell_price"], cost_rate)
    if target == trade["buy_qty"] and remaining == 0:
        pnl = trade["realized_net_pnl_krw"]
    denominator = trade["buy_price"] * trade["buy_qty"]
    return {"status": "paired" if remaining == 0 else "partial_unfilled",
            "target_qty": target, "modeled_filled_qty": target - remaining,
            "unfilled_qty": remaining, "extra_fill_source": extra_source,
            "candidate_net_pnl_krw": round(pnl, 3),
            "candidate_net_pct_on_parent_notional": round(pnl / denominator * 100, 6),
            "parent_net_pnl_krw": trade["realized_net_pnl_krw"]}

def initial_replay_economics_valid(report: Any) -> bool:
    """Check parent conservation and ordering of conditional EV bounds."""
    def metric(value: Any) -> bool:
        return type(value) in (int, float) and math.isfinite(value)

    if not isinstance(report, dict):
        return False
    if (report.get("generation_kind") == "refresh_post_apply_replay"
            and (report.get("cost_model") != COST_MODEL
                 or report.get("cap_fill_model") != CAP_FILL_MODEL)):
        return False
    if report.get("cost_model") not in (None, COST_MODEL):
        return False
    rows = report.get("trades")
    census = report.get("census") or {}
    if (not isinstance(rows, list)
            or len(rows) != census.get("all_completed_initial_trades")):
        return False
    seen: set[str] = set()
    facts_by_id = {str(fact.get("recommendation_id")): fact
                   for fact in census.get("input_fact_rows") or []
                   if isinstance(fact, dict) and fact.get("recommendation_id") is not None}
    counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    paired_by_type: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list))
    rows_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("shapes"), dict):
            return False
        trade_id = str(row.get("trade_id") or "")
        if not trade_id or trade_id in seen or set(row["shapes"]) != set(_SHAPES):
            return False
        seen.add(trade_id)
        quantity_type = row.get("quantity_type")
        if quantity_type not in _TYPES:
            return False
        type_counts[quantity_type] += 1
        rows_by_type[quantity_type].append(row)
        parent = row["shapes"]["parent"]
        if (not isinstance(parent, dict)
                or not metric(row.get("actual_profit_rate"))
                or not metric(row.get("actual_net_pnl_krw"))):
            return False
        if parent.get("status") == "paired" and (
            not metric(parent.get("candidate_net_pct"))
            or not metric(parent.get("candidate_net_pnl_krw"))
            or abs(parent["candidate_net_pct"] - row["actual_profit_rate"]) > 1e-6
            or abs(parent["candidate_net_pnl_krw"] - row["actual_net_pnl_krw"]) > 1e-3
        ):
            return False
        if report.get("generation_kind") == "refresh_post_apply_replay":
            fact = facts_by_id.get(str(row.get("record_id") or ""))
            source = row.get("cap_source")
            candidates = row.get("cap_candidates")
            if (not isinstance(fact, dict) or not isinstance(source, dict)
                    or not isinstance(candidates, dict)
                    or set(candidates) != set(_CAP_MODES)
                    or source.get("context") !=
                    row.get("applied_cap_research_context")
                    or source.get("attempt_id") !=
                    parent.get("applied_cap_attempt_id")
                    or source.get("plan_sha256") !=
                    parent.get("applied_cap_plan_sha256")):
                return False
            trade = {"buy_qty": fact.get("buy_qty"),
                     "buy_price": fact.get("buy_price"),
                     "sell_price": fact.get("sell_price"),
                     "realized_net_pnl_krw": row["actual_net_pnl_krw"]}
            if any(candidates[mode] != _cap_candidate_trade(
                    trade, source, mode, census['cost_rate'])
                    for mode in _CAP_MODES):
                return False
        for shape, result in row["shapes"].items():
            if not isinstance(result, dict):
                return False
            status = result.get("status")
            counts[f"{shape}:{status}"] += 1
            if status == "paired":
                paired_by_type[quantity_type][shape].append(result)
            if status != "paired" or shape == "parent":
                continue
            if result.get("quantity_type") != row.get("quantity_type"):
                return False
            for key in ("conservative_net_pct", "candidate_net_pct", "upper_net_pct",
                        "conservative_net_pnl_krw", "candidate_net_pnl_krw",
                        "upper_net_pnl_krw", "parent_net_pnl_krw"):
                if not metric(result.get(key)):
                    return False
            if (result["conservative_net_pct"] > result["candidate_net_pct"] + 1e-6
                    or result["candidate_net_pct"] > result["upper_net_pct"] + 1e-6
                    or result["conservative_net_pnl_krw"] > result["candidate_net_pnl_krw"] + 0.001
                    or result["candidate_net_pnl_krw"] > result["upper_net_pnl_krw"] + 0.001):
                return False
            if result.get("fill_state") == "quantity_too_small_parent_fallback":
                if abs(result["candidate_net_pnl_krw"] - row["actual_net_pnl_krw"]) > 0.001:
                    return False
            else:
                original_notional = _number(result.get("candidate_notional_denominator_krw"))
                if (not original_notional or original_notional <= 0
                        or abs(result["candidate_net_pct"] -
                               result["candidate_net_pnl_krw"] / original_notional * 100) > 0.001):
                    return False
    if (dict(sorted(counts.items())) != report.get("replay_counts")
            or dict(sorted(type_counts.items())) != report.get("quantity_type_counts")):
        return False
    selections = report.get("selections")
    if not isinstance(selections, dict) or set(selections) != set(_TYPES):
        return False
    for quantity_type in _TYPES:
        selection = selections[quantity_type]
        if not isinstance(selection, dict):
            return False
        metrics = selection.get("candidate_metrics")
        if not isinstance(metrics, dict) or set(metrics) != set(_SHAPES):
            return False
        parent = paired_by_type[quantity_type]["parent"]
        parent_ev = sum(x["candidate_net_pct"] for x in parent) / len(parent) if parent else None
        parent_net = sum(x["parent_net_pnl_krw"] for x in parent)
        if selection.get("winner_weight_kind") is not None:
            winners = [row for row in rows_by_type[quantity_type]
                       if row["actual_net_pnl_krw"] > 0
                       and row["actual_profit_rate"] > 0]
            weight = sum(row["actual_net_pnl_krw"] for row in winners)
            weighted_parent = (sum(row["actual_profit_rate"] * row["actual_net_pnl_krw"]
                                   for row in winners) / weight if weight else None)
            if (selection.get("winner_weight_kind") != "positive_realized_net_pnl_krw"
                    or selection.get("winner_count") != len(winners)
                    or not metric(selection.get("winner_weight_sum_krw"))
                    or abs(selection["winner_weight_sum_krw"] - weight) > 0.002
                    or ((weighted_parent is None) !=
                        (selection.get("winner_weighted_parent_ev_pct") is None))
                    or weighted_parent is not None and abs(
                        selection["winner_weighted_parent_ev_pct"] - weighted_parent) > 1e-6):
                return False
            for shape in _SHAPES:
                comparable = [row for row in winners
                              if row["shapes"][shape].get("status") == "paired"]
                ids = {row["trade_id"] for row in comparable}
                weighted = (sum(row["actual_net_pnl_krw"] * (
                    row["shapes"][shape].get("conservative_net_pct",
                                              row["actual_profit_rate"])
                    if row["trade_id"] in ids else row["actual_profit_rate"])
                    for row in winners) / weight if weight else None)
                metric_row = metrics[shape]
                if (metric_row.get("winner_comparable_count") != len(comparable)
                        or ((weighted is None) !=
                            (metric_row.get("winner_weighted_conservative_ev_pct") is None))
                        or weighted is not None and abs(
                            metric_row["winner_weighted_conservative_ev_pct"] - weighted) > 1e-6):
                    return False
        if ((parent_ev is None) != (selection.get("parent_ev_pct") is None)
                or parent_ev is not None and abs(parent_ev - selection["parent_ev_pct"]) > 1e-6):
            return False
        for shape in _SHAPES:
            values = paired_by_type[quantity_type][shape]
            metric_row = metrics[shape]
            if not isinstance(metric_row, dict) or metric_row.get("paired_count") != len(values):
                return False
            if not values:
                if metric_row.get("state") != "no_comparable_trade":
                    return False
                continue
            expected_modeled = sum(value.get("fill_state") in {
                "price_cross_conditional", "price_touch_only", "no_cross_observed"}
                for value in values)
            expected_crossed = sum(value.get("fill_state") == "price_cross_conditional"
                                   for value in values)
            expected_verified = sum(
                value.get("verified_route_epoch_price_cross_count", 0) > 0
                and value.get("verified_route_epoch_price_cross_count", 0)
                == value.get("conditional_crossed_leg_count", 0)
                for value in values)
            if (metric_row.get("modeled_count") != expected_modeled
                    or metric_row.get("price_cross_count") != expected_crossed
                    or metric_row.get("verified_route_epoch_price_cross_count") != expected_verified
                    or metric_row.get("price_touch_only_count") != sum(
                        value.get("fill_state") == "price_touch_only" for value in values)
                    or metric_row.get("no_cross_observed_count") != sum(
                        value.get("fill_state") == "no_cross_observed" for value in values)):
                return False
            expected_coverage = len(values) / type_counts[quantity_type]
            expected_global_coverage = len(values) / len(rows)
            expected_net = parent_net + sum(
                value["candidate_net_pnl_krw"] - value["parent_net_pnl_krw"]
                for value in values)
            expected_conservative_net = parent_net + sum(
                value.get("conservative_net_pnl_krw", value["candidate_net_pnl_krw"])
                - value["parent_net_pnl_krw"]
                for value in values)
            expected_ev = parent_ev + sum(
                value["candidate_net_pct"] - value.get("parent_net_pct", value["candidate_net_pct"])
                for value in values) / len(parent)
            expected_conservative_ev = parent_ev + sum(
                value.get("conservative_net_pct", value["candidate_net_pct"])
                - value.get("parent_net_pct", value["candidate_net_pct"])
                for value in values) / len(parent)
            if (not metric(metric_row.get("coverage_of_type"))
                    or abs(metric_row["coverage_of_type"] - expected_coverage) > 1e-6
                    or not metric(metric_row.get("coverage_of_all_completed"))
                    or abs(metric_row["coverage_of_all_completed"] - expected_global_coverage) > 1e-6
                    or not metric(metric_row.get("estimated_net_pnl_krw"))
                    or abs(metric_row["estimated_net_pnl_krw"] - expected_net) > 0.002
                    or not metric(metric_row.get("conservative_net_pnl_krw"))
                    or abs(metric_row["conservative_net_pnl_krw"] - expected_conservative_net) > 0.002
                    or not metric(metric_row.get("estimated_ev_pct"))
                    or abs(metric_row["estimated_ev_pct"] - expected_ev) > 1e-6
                    or not metric(metric_row.get("conservative_ev_pct"))
                    or abs(metric_row["conservative_ev_pct"] - expected_conservative_ev) > 1e-6):
                return False
        selected = selection.get("selected_shape")
        if (selected not in _SHAPES
                or selected != _select_initial_winner_shape(
                    quantity_type, metrics)
                or selection.get("selection_reason") != (
                    "initial_winner_weighted_shape" if selected != "parent"
                    else "parent_or_source_gap")):
            return False
    return True

def _eligible_refresh_total_wait(
    report: dict[str, Any], timeout_research: dict[str, Any] | None,
    quantity_type: str, shape: str, minimum_count: int,
) -> int | None:
    """Choose a bounded T only with exact start clocks and dated EV support."""
    if shape == "parent" or not isinstance(timeout_research, dict):
        return None
    selection = (timeout_research.get("selections") or {}).get(quantity_type) or {}
    source_rows = [row for row in report.get("trades") or []
                   if row.get("quantity_type") == quantity_type]
    parent_net = sum(row["actual_net_pnl_krw"] for row in source_rows)
    parent_ev = _number(selection.get("parent_costed_ev_pct"))
    parent_winner = _number(selection.get("winner_weighted_parent_ev_pct"))
    if parent_ev is None or len(source_rows) < minimum_count:
        return None
    ranked = []
    for horizon in timeout_research.get("horizons_sec") or []:
        if (type(horizon) is not int or horizon > 1200
                or horizon < 6 * (3 if shape.startswith("three_leg") else 2)):
            continue
        metric = (selection.get("candidate_metrics") or {}).get(
            f"{shape}:5:{horizon}") or {}
        modeled = metric.get("modeled_count")
        daily = metric.get("daily_conservative_delta_net_pnl_krw") or {}
        ev = _number(metric.get("conservative_ev_pct"))
        net = _number(metric.get("conservative_net_pnl_krw"))
        winner = _number(metric.get("winner_weighted_conservative_ev_pct"))
        if (type(modeled) is not int or modeled < minimum_count
                or modeled / len(source_rows) < 0.8
                or (metric.get("order_start_source_counts") or {}) != {
                    "initial_quantity_bundle_order_start_at": modeled}
                or metric.get("verified_cross_count", 0) <
                    max(3, math.ceil(modeled * 0.05))
                or ev is None or ev <= parent_ev + 0.10
                or parent_winner is None or winner is None
                or winner <= parent_winner + 1e-6
                or net is None or net <= parent_net
                or not isinstance(daily, dict) or len(daily) < 3
                or min(daily.values()) < 0
                or daily[max(daily)] <= 0):
            continue
        ranked.append((winner, ev, net, -horizon, horizon))
    return max(ranked)[-1] if ranked else None

def _refresh_cap_decision(
    rows: list[dict[str, Any]], parent_mode: str, minimum_count: int,
) -> tuple[str, dict[str, Any]]:
    """Rank bounded caps on paired full-cost trades; retain every loss."""
    if not rows or parent_mode not in {"parent_5stage", *_CAP_MODES}:
        return parent_mode, {}
    dates = sorted({row["entry_date"] for row in rows})
    holdout_date = dates[-1]
    train_rows = [row for row in rows if row["entry_date"] < holdout_date]
    holdout_rows = [row for row in rows if row["entry_date"] == holdout_date]
    parent_net = sum(row["actual_net_pnl_krw"] for row in rows)
    winner_weight = sum(row["actual_net_pnl_krw"] for row in rows
                        if row["actual_net_pnl_krw"] > 0
                        and row["actual_profit_rate"] > 0)
    parent_weighted = (sum(
        row["actual_net_pnl_krw"] * row["actual_profit_rate"]
        for row in rows if row["actual_net_pnl_krw"] > 0
        and row["actual_profit_rate"] > 0) / winner_weight
        if winner_weight else None)
    metrics: dict[str, Any] = {}
    selected = parent_mode
    best_rank = (-math.inf, 0.0)
    for mode in _CAP_MODES:
        valid = [row for row in rows if (row.get("cap_candidates") or {}).get(
            mode, {}).get("status") == "paired"]
        valid_ids = {row["trade_id"] for row in valid}
        candidate_net = parent_net + sum(
            row["cap_candidates"][mode]["candidate_net_pnl_krw"]
            - row["actual_net_pnl_krw"] for row in valid)
        weighted = (sum(
            row["actual_net_pnl_krw"] * (
                row["cap_candidates"][mode]["candidate_net_pct_on_parent_notional"]
                if row["trade_id"] in valid_ids else row["actual_profit_rate"])
            for row in rows if row["actual_net_pnl_krw"] > 0
            and row["actual_profit_rate"] > 0) / winner_weight
            if winner_weight else None)
        daily: dict[str, float] = defaultdict(float)
        for row in rows:
            daily[row["entry_date"]] += (
                row["cap_candidates"][mode]["candidate_net_pnl_krw"]
                - row["actual_net_pnl_krw"] if row["trade_id"] in valid_ids
                else 0.0)
        coverage = len(valid) / len(rows)
        delta = candidate_net - parent_net
        train_valid = [row for row in train_rows if row["trade_id"] in valid_ids]
        holdout_valid = [row for row in holdout_rows if row["trade_id"] in valid_ids]
        train_delta = sum(daily[day] for day in dates[:-1])
        holdout_delta = daily[holdout_date]
        train_winner_weight = sum(row["actual_net_pnl_krw"] for row in train_rows
                                  if row["actual_net_pnl_krw"] > 0
                                  and row["actual_profit_rate"] > 0)
        train_parent_weighted = (sum(
            row["actual_net_pnl_krw"] * row["actual_profit_rate"]
            for row in train_rows if row["actual_net_pnl_krw"] > 0
            and row["actual_profit_rate"] > 0) / train_winner_weight
            if train_winner_weight else None)
        train_candidate_weighted = (sum(
            row["actual_net_pnl_krw"] * (
                row["cap_candidates"][mode]["candidate_net_pct_on_parent_notional"]
                if row["trade_id"] in valid_ids else row["actual_profit_rate"])
            for row in train_rows if row["actual_net_pnl_krw"] > 0
            and row["actual_profit_rate"] > 0) / train_winner_weight
            if train_winner_weight else None)
        train_coverage = len(train_valid) / len(train_rows) if train_rows else 0.0
        holdout_coverage = len(holdout_valid) / len(holdout_rows)
        enough = (len(dates) >= 3 and len(train_valid) >= minimum_count
                  and train_coverage >= 0.8 and holdout_coverage >= 0.8
                  and min(daily.values()) >= -0.001
                  and train_delta > 0 and holdout_delta >= 0 and delta > 0
                  and parent_weighted is not None and weighted is not None
                  and weighted > parent_weighted + 1e-6
                  and train_parent_weighted is not None
                  and train_candidate_weighted is not None
                  and train_candidate_weighted > train_parent_weighted + 1e-6)
        metrics[mode] = {
            "paired_count": len(valid), "type_count": len(rows),
            "coverage": round(coverage, 6),
            "parent_net_pnl_krw": round(parent_net, 3),
            "candidate_net_pnl_krw": round(candidate_net, 3),
            "delta_net_pnl_krw": round(delta, 3),
            "winner_weighted_net_pct": (round(weighted, 6)
                                         if weighted is not None else None),
            "parent_winner_weighted_net_pct": (
                round(parent_weighted, 6)
                if parent_weighted is not None else None),
            "daily_delta_net_pnl_krw": {
                day: round(value, 3) for day, value in sorted(daily.items())},
            "train_dates": dates[:-1], "holdout_date": holdout_date,
            "train_paired_count": len(train_valid),
            "train_coverage": round(train_coverage, 6),
            "holdout_paired_count": len(holdout_valid),
            "holdout_coverage": round(holdout_coverage, 6),
            "train_delta_net_pnl_krw": round(train_delta, 3),
            "holdout_delta_net_pnl_krw": round(holdout_delta, 3),
            "train_winner_weighted_net_pct": (
                round(train_candidate_weighted, 6)
                if train_candidate_weighted is not None else None),
            "train_parent_winner_weighted_net_pct": (
                round(train_parent_weighted, 6)
                if train_parent_weighted is not None else None),
            "selection_eligible": enough,
        }
        rank = (train_candidate_weighted
                if train_candidate_weighted is not None else -math.inf,
                train_delta)
        if enough and mode != parent_mode and rank > best_rank:
            selected, best_rank = mode, rank
    return selected, metrics

def evaluate_refresh_quantity_candidate(
    report: dict[str, Any], *, parent_policy: dict[str, Any],
    pid_receipt: dict[str, Any] | None = None,
    terminal_receipt: dict[str, Any] | None = None,
    following_bars: dict[str, Any] | None = None,
    timeout_research: dict[str, Any] | None = None,
    parent_policy_file_sha256: str | None = None,
    enforce_trade_lineage: bool = True,
) -> dict[str, Any]:
    """Apply stronger post-activation gates without reusing the seed sample."""
    from src.engine.scalping.initial_quantity_activation import (
        RUNTIME_REFRESH_SCHEMA, baseline_policy_valid,
        refresh_parent_policy_valid,
    )

    if not isinstance(parent_policy, dict) or not isinstance(report, dict):
        raise ValueError("refresh_parent_or_replay_contract_invalid")
    parent_body = {key: value for key, value in parent_policy.items()
                   if key != "policy_content_sha256"}
    report_body = {key: value for key, value in report.items()
                   if key != "report_content_sha256"}
    is_initial_baseline = baseline_policy_valid(parent_policy)
    is_v2_parent = (refresh_parent_policy_valid(parent_policy)
                    and not is_initial_baseline)
    is_legacy_parent = (
        parent_policy.get("policy_content_sha256") == _digest(parent_body)
        and parent_policy.get("runtime_apply_allowed") is True
        and parent_policy.get("runtime_effect") is True
        and parent_policy.get("activation_state") == "reviewed_active"
        and isinstance(parent_policy.get("type_policies"), dict)
        and set(parent_policy["type_policies"]) == set(_TYPES)
        and all(type(row) is dict and type(row.get("paired_count")) is int
                and row["paired_count"] >= 0
                for row in parent_policy["type_policies"].values())
    )
    if (not (is_initial_baseline or is_v2_parent or is_legacy_parent)
            or report.get("report_content_sha256") != _digest(report_body)
            or report.get("generation_kind") != "refresh_post_apply_replay"
            or report.get("schema_version") != REPORT_SCHEMA
            or not initial_replay_economics_valid(report)
            or (report.get("census") or {}).get("entry_on_or_after")
            != parent_policy.get("effective_from")
            or len(report.get("trades") or [])
            != (report.get("census") or {}).get("all_completed_initial_trades")
            or any(str(row.get("entry_date") or "") < str(parent_policy.get("effective_from") or "")
                   for row in report.get("trades") or [])
            or (report.get("census") or {}).get("input_manifest_sha256")
            != _digest((report.get("census") or {}).get("input_fact_rows"))):
        raise ValueError("refresh_parent_or_replay_contract_invalid")
    if following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import (
            following_bar_source_valid,
        )
        if not following_bar_source_valid(following_bars, report):
            raise ValueError("refresh_following_source_invalid")
    if timeout_research is not None:
        from src.engine.scalping.initial_quantity_timeout_research import (
            timeout_research_valid,
        )
        if (not timeout_research_valid(timeout_research)
                or timeout_research.get("source_date") != report.get("source_date")
                or timeout_research.get("census") != report.get("census")):
            raise ValueError("refresh_timeout_source_invalid")
    parent_hash = parent_policy["policy_content_sha256"]
    entry_dates = sorted({row["entry_date"] for row in report.get("trades") or []})
    blockers = []
    expected_parent_status = (
        "initial_policy_refresh_loaded"
        if parent_policy.get("schema_version") == RUNTIME_REFRESH_SCHEMA else
        "initial_policy_v2_loaded" if is_v2_parent else
        "initial_policy_loaded")
    daily_pid_rows = (pid_receipt.get("daily_pid_receipts")
                      if isinstance(pid_receipt, dict) else None)
    pid_by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pid_row in daily_pid_rows if isinstance(daily_pid_rows, list) else []:
        if isinstance(pid_row, dict):
            pid_by_day[str(pid_row.get("entry_date") or "")].append(pid_row)
    pid_days_valid = (set(pid_by_day) == set(entry_dates)
                      and all(type(item.get("pid")) is int
                              and item["pid"] > 0
                              and _timestamp(item.get("verified_at")) is not None
                              for rows in pid_by_day.values() for item in rows))
    policy_bound_trades = sum(
        row.get("applied_policy_status") == expected_parent_status
        and row.get("applied_policy_file_sha256") == parent_policy_file_sha256
        and row.get("policy_decision_stage") == "entry_execution_sizing_plan"
        and (decision_at := _timestamp(row.get("policy_decision_at"))) is not None
        and (entry_at := _timestamp(row.get("entry_fill_at"))) is not None
        and decision_at <= entry_at
        and (not pid_receipt or pid_days_valid and any(
            str(row.get("applied_policy_runtime_pid") or "") ==
            str(pid_row["pid"])
            and _timestamp(pid_row["verified_at"]) <= decision_at
            for pid_row in pid_by_day[row["entry_date"]]))
        for row in report.get("trades") or [])
    if (enforce_trade_lineage and report.get("trades")
            and policy_bound_trades != len(report["trades"])):
        blockers.append("parent_trade_policy_binding_missing")
    if following_bars is None and any(
            row["actual_net_pnl_krw"] > 0 and row["actual_profit_rate"] > 0
            for row in report["trades"]):
        blockers.append("winner_following_source_missing")
    if len(entry_dates) < 3:
        blockers.append("independent_post_apply_dates_below_three")
    if not (isinstance(pid_receipt, dict)
            and pid_receipt.get("actual_pid_consumed") is True
            and pid_receipt.get("policy_content_sha256") == parent_hash
            and pid_days_valid
            and str(pid_receipt.get("first_consumed_date") or "") <= (entry_dates[0] if entry_dates else "")):
        blockers.append("parent_pid_consumption_missing")
    if not (isinstance(terminal_receipt, dict)
            and terminal_receipt.get("terminal") is True
            and terminal_receipt.get("costed_completed_trade_count")
            == (report.get("census") or {}).get("all_completed_initial_trades")
            and terminal_receipt.get("report_content_sha256") == report["report_content_sha256"]):
        blockers.append("post_apply_terminal_cost_binding_missing")
    type_decisions = {}
    for quantity_type in _TYPES:
        selection = (report.get("selections") or {}).get(quantity_type) or {}
        incumbent = (selection.get("candidate_metrics") or {}).get("parent") or {}
        parent_count = incumbent.get("paired_count", 0)
        seeded_count = ((parent_policy.get("type_policies") or {}).get(quantity_type) or {}).get(
            "paired_count", 0)
        # The active first baseline intentionally stores no per-type training
        # count. Never turn that absent count into the five-trade refresh floor.
        minimum_count = (30 if is_initial_baseline or is_v2_parent else
                         max(5, min(30, math.ceil(seeded_count * 0.2))))
        incumbent_shape = str((parent_policy.get("type_policies") or {}).get(
            quantity_type, {}).get("selected_shape") or "parent")
        best = incumbent_shape
        parent_winner = _number(selection.get("winner_weighted_parent_ev_pct"))
        parent_ev = _number(selection.get("parent_ev_pct"))
        best_rank = (parent_winner if parent_winner is not None else -math.inf,
                     parent_ev if parent_ev is not None else -math.inf)
        reasons = []
        for shape, metric in (selection.get("candidate_metrics") or {}).items():
            if shape == incumbent_shape or shape not in _SHAPES:
                continue
            if shape == "parent":
                # In the replay, the parent arm is the actual applied trade.
                # It cannot be treated as an independent counterfactual that
                # justifies reverting an already active non-parent shape.
                continue
            if (type(metric.get("paired_count")) is not int
                    or metric["paired_count"] < minimum_count
                    or _number(metric.get("coverage_of_type")) is None
                    or metric["coverage_of_type"] < 0.8
                    or metric.get("verified_route_epoch_price_cross_count", 0) < 1
                    or _number(metric.get("conservative_ev_pct")) is None
                    or _number(selection.get("parent_ev_pct")) is None
                    or metric["conservative_ev_pct"] <= selection["parent_ev_pct"] + 0.10
                    or parent_winner is None
                    or _number(metric.get("winner_weighted_conservative_ev_pct")) is None
                    or metric["winner_weighted_conservative_ev_pct"] <=
                    parent_winner + 1e-6):
                continue
            rows = [row for row in report.get("trades") or []
                    if row.get("quantity_type") == quantity_type]
            daily_delta: dict[str, float] = defaultdict(float)
            for row in rows:
                daily_delta[row["entry_date"]] += 0.0
                result = (row.get("shapes") or {}).get(shape) or {}
                if result.get("status") == "paired":
                    daily_delta[row["entry_date"]] += (
                        result["candidate_net_pnl_krw"] - result["parent_net_pnl_krw"])
            if len(daily_delta) < 3 or min(daily_delta.values()) < 0 or daily_delta[max(daily_delta)] <= 0:
                continue
            rank = (metric["winner_weighted_conservative_ev_pct"],
                    metric["conservative_ev_pct"])
            if rank > best_rank:
                best = shape
                best_rank = rank
        if best == incumbent_shape:
            reasons.append("refresh_hurdles_or_evidence_not_met")
        elif following_bars is not None:
            following = (following_bars.get("weighted_by_type") or {}).get(
                quantity_type) or {}
            winner_count = selection.get("winner_count", 0)
            observed = following.get("observed_minute_lower_count", 0)
            if (type(winner_count) is not int or winner_count <= 0
                    or type(observed) is not int
                    or observed / winner_count < 0.8):
                best = incumbent_shape
                reasons.append("winner_following_lower_coverage_below_80pct")
        selected_wait = _eligible_refresh_total_wait(
            report, timeout_research, quantity_type, best, minimum_count)
        parent_row = parent_policy["type_policies"][quantity_type]
        cap_rows = [row for row in report.get("trades") or []
                    if row.get("quantity_type") == quantity_type]
        selected_ratio, cap_metrics = _refresh_cap_decision(
            cap_rows, parent_row.get("ratio_mode", "parent_5stage"),
            minimum_count)
        if quantity_type == "SAFE_UNKNOWN":
            selected_ratio = "parent_5stage"
        if (selected_wait is not None
                and parent_row.get("timeout_mode") == "selected_total_wait_sec"
                and parent_row.get("selected_total_wait_sec") == selected_wait):
            selected_wait = None
        type_decisions[quantity_type] = {"selected_shape": best,
                                         "selected_ratio_mode": selected_ratio,
                                         "cap_candidate_metrics": cap_metrics,
                                         "selected_total_wait_sec": selected_wait,
                                         "minimum_completed_count": minimum_count,
                                         "observed_completed_count": parent_count,
                                         "reason": reasons[0] if reasons else "post_apply_hurdles_passed"}
    state = ("eligible_source_only" if not blockers and any(
        row["selected_shape"] != (parent_policy["type_policies"][name].get(
            "selected_shape") or "parent")
        or row["selected_ratio_mode"] != parent_policy["type_policies"][name].get(
            "ratio_mode", "parent_5stage")
        or row["selected_total_wait_sec"] is not None
        for name, row in type_decisions.items())
             else "carry_parent")
    return {"schema_version": "initial_entry_quantity_refresh_evaluation_v1",
            "generation_kind": "refresh", "source_date": report["source_date"],
            "parent_policy_content_sha256": parent_hash,
            "report_content_sha256": report["report_content_sha256"],
            "state": state, "global_blockers": blockers,
            **({"parent_policy_bound_trade_count": policy_bound_trades}
               if enforce_trade_lineage else {}),
            "type_decisions": type_decisions,
            "runtime_apply_allowed": False, "runtime_effect": False}

def _natural_refresh_pid_receipt(
    report: dict[str, Any], parent_policy: dict[str, Any],
    parent_policy_path: Path, data_dir: Path,
) -> dict[str, Any] | None:
    """Read each entry day's verified Main PID/environment handoff.

    A selected release or a PREOPEN manifest alone is insufficient. Missing
    daily PID proof leaves the refresh evaluator's existing blocker in place.
    """
    from src.engine.scalping.initial_quantity_activation import ENV_FILE, ENV_SHA

    days = sorted({row["entry_date"] for row in report.get("trades") or []})
    if not days:
        return None
    parent_file_sha = _file_sha256(parent_policy_path)
    bootstrap_dir = data_dir / "runtime" / "policy_bootstrap"
    receipts = []
    for day in days:
        archived = []
        archive_dir = bootstrap_dir / "verified_initial_quantity_pid" / day
        for archive_path in sorted(archive_dir.glob("initial_quantity_pid_*.json")):
            try:
                archive = json.loads(archive_path.read_text(encoding="utf-8"))
                archive_sha = _file_sha256(archive_path)
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(archive, dict):
                continue
            archive_body = {key: value for key, value in archive.items()
                            if key != "receipt_content_sha256"}
            verify = archive.get("verification") or {}
            verified_at = _timestamp(archive.get("verified_at"))
            if (archive.get("schema_version") !=
                    "initial_quantity_pid_verification_v1"
                    or archive.get("receipt_content_sha256") !=
                    _digest(archive_body)
                    or archive_path.name !=
                    f"initial_quantity_pid_{archive.get('pid')}_"
                    f"{archive['receipt_content_sha256'][:12]}.json"
                    or archive.get("target_date") != day
                    or verified_at is None or verified_at.date().isoformat() != day
                    or archive.get("policy_file_sha256") != parent_file_sha
                    or archive.get("policy_content_sha256") !=
                    parent_policy["policy_content_sha256"]
                    or Path(str(archive.get("policy_file") or "")).resolve()
                    != parent_policy_path.resolve()
                    or not isinstance(verify, dict)
                    or verify.get("pid_passed") is not True
                    or verify.get("status") != "pass"
                    or verify.get("passed") is not True
                    or verify.get("pid_env_available") is not True
                    or verify.get("pid") != archive.get("pid")
                    or verify.get("target_date") != day
                    or verify.get("verified_at") != archive.get("verified_at")
                    or verify.get("manifest_sha256") !=
                    archive.get("manifest_sha256")
                    or verify.get("findings") != []
                    or verify.get("pid_mismatches") != []):
                continue
            archived.append({"entry_date": day, "pid": archive["pid"],
                             "verified_at": archive["verified_at"],
                             "archive_path": str(archive_path.resolve()),
                             "archive_file_sha256": archive_sha})
        if archived:
            receipts.extend(archived)
            continue
        manifest_path = bootstrap_dir / f"runtime_policy_bootstrap_{day}.json"
        verify_path = bootstrap_dir / f"runtime_policy_bootstrap_verify_{day}.json"
        env_path = bootstrap_dir / f"runtime_policy_bootstrap_{day}.env"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            verify = json.loads(verify_path.read_text(encoding="utf-8"))
            env_sha = _file_sha256(env_path)
            manifest_file_sha = _file_sha256(manifest_path)
            verify_file_sha = _file_sha256(verify_path)
        except (OSError, ValueError, TypeError):
            return None
        if not isinstance(manifest, dict) or not isinstance(verify, dict):
            return None
        manifest_body = {key: value for key, value in manifest.items()
                         if key != "manifest_sha256"}
        policy_receipt = manifest.get("initial_quantity_policy_receipt") or {}
        env = manifest.get("env_overrides") or {}
        if (manifest.get("target_date") != day
                or manifest.get("manifest_sha256") != _digest(manifest_body)
                or Path(str(manifest.get("env_file") or "")).resolve()
                != env_path.resolve()
                or manifest.get("env_sha256") != env_sha
                or not isinstance(policy_receipt, dict)
                or policy_receipt.get("policy_file_sha256") != parent_file_sha
                or env.get(ENV_FILE) != str(parent_policy_path.resolve())
                or env.get(ENV_SHA) != parent_file_sha
                or verify.get("target_date") != day
                or verify.get("manifest_sha256") != manifest["manifest_sha256"]
                or Path(str(verify.get("manifest_file") or "")).resolve()
                != manifest_path.resolve()
                or Path(str(verify.get("env_file") or "")).resolve()
                != env_path.resolve()
                or (_timestamp(verify.get("verified_at")) is None
                    or _timestamp(verify["verified_at"]).date().isoformat() != day)
                or verify.get("status") != "pass"
                or verify.get("passed") is not True
                or verify.get("pid_passed") is not True
                or verify.get("pid_env_available") is not True
                or type(verify.get("pid")) is not int
                or verify["pid"] <= 0
                or verify.get("findings") != []
                or verify.get("pid_mismatches") != []):
            return None
        receipts.append({"entry_date": day, "pid": verify["pid"],
                         "verified_at": verify["verified_at"],
                         "manifest_file_sha256": manifest_file_sha,
                         "verify_file_sha256": verify_file_sha,
                         "env_file_sha256": env_sha})
    return {"actual_pid_consumed": True,
            "policy_content_sha256": parent_policy["policy_content_sha256"],
            "policy_file_sha256": parent_file_sha,
            "first_consumed_date": days[0], "daily_pid_receipts": receipts,
            "data_root": str(data_dir.resolve()),
            "source": "verified_daily_preopen_main_pid_env"}
