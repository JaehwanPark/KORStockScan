"""Pure, cash-only TP1 blocked-opportunity replay. No orders or source reads.

The initial broker admission envelope already excludes existing commitments.
Only unchanged original inventory/deposit sources may share this conditional
wallet. Unknown external flows and unsupported partial fills stay censored.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

SCHEMA = "tp1_quantity_capital_source_v2"


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def epoch(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("quantity_source_timezone_missing")
    return dt.timestamp()


def validate_source(source, row):
    if (
        not isinstance(source, dict)
        or source.get("schema") != SCHEMA
        or source.get("sha256")
        != digest({k: v for k, v in source.items() if k != "sha256"})
        or source.get("status") != "complete"
        or source.get("evaluation_id") != row.get("evaluation_id")
        or source.get("stock_code") != row.get("stock_code")
        or source.get("venue") != row.get("effective_venue")
        or source.get("session") != row.get("market_session_bucket")
        or any(
            not re.fullmatch("[0-9a-f]{64}", str(source.get(k)))
            for k in (
                "inventory_sha256",
                "policy_sha256",
                "capacity_source_sha256",
                "account_scope_sha256",
            )
        )
        or not source.get("route")
        or not source.get("transport_epoch")
        or not source.get("other_guards_passed") is True
    ):
        raise ValueError("quantity_capital_identity_or_guard_missing")
    at = epoch(row["candidate_ts"])
    if (
        datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul")).date().isoformat()
        != row["source_date"]
    ):
        raise ValueError("quantity_source_date_invalid")
    if not 0 <= at - epoch(source["observed_at"]) <= 2:
        raise ValueError("quantity_capital_source_stale_or_future")
    for key in (
        "budget_base_krw",
        "available_cash_krw",
        "account_deposit_krw",
        "price_krw",
        "allocation_price_krw",
        "ratio",
        "safety_ratio",
        "absolute_cap_krw",
    ):
        if not finite(source.get(key)) or source[key] < 0:
            raise ValueError("quantity_capital_component_missing")
    if not (
        source["price_krw"] > 0
        and source["allocation_price_krw"] > 0
        and 0.10 <= source["ratio"] <= 0.25
        and 0 < source["safety_ratio"] <= 1
    ):
        raise ValueError("quantity_capital_component_invalid")
    if type(source.get("min_one_share_floor_enabled")) is not bool:
        raise ValueError("quantity_floor_policy_missing")
    caps = source.get("quantity_caps")
    if (
        not isinstance(caps, list)
        or not caps
        or any(type(x) is not int or x < 0 for x in caps)
    ):
        raise ValueError("quantity_capital_caps_missing")
    return source


def quantity(source, available):
    # Same pure formula owner as the live allocator; frozen ratio and caps.
    from src.engine.kiwoom_orders import describe_buy_capacity

    _, _, qty, _ = describe_buy_capacity(
        source["allocation_price_krw"],
        min(source["budget_base_krw"], available),
        source["ratio"],
        safety_ratio=source["safety_ratio"],
        max_budget=source["absolute_cap_krw"],
        allow_min_one_share_over_budget=source["min_one_share_floor_enabled"],
    )
    return min(qty, *source["quantity_caps"])


def replay(rows):
    """Replay a single identified 2->1 relaxation, reserving cash until exit.

    Each unchanged baseline is an explicit blocked, capital-neutral arm. A
    censored candidate's unknown release blocks the remaining day's wallet.
    """
    daily = defaultdict(float)
    details, gaps = [], []
    by_day = defaultdict(list)
    for row in rows:
        by_day[row["source_date"]].append(row)
    for day, population in sorted(by_day.items()):
        wallet = None
        account = None
        active = []
        blocked = False
        for row in sorted(
            population, key=lambda r: (r["candidate_ts"], r["evaluation_id"])
        ):
            try:
                if blocked:
                    raise ValueError("earlier_capital_release_unobservable")
                source = validate_source(row.get("quantity_capital_source"), row)
                identity = (
                    source["account_scope_sha256"],
                    source["account_deposit_krw"],
                    source["inventory_sha256"],
                )
                if wallet is None:
                    wallet, account = source["available_cash_krw"], identity
                if identity != account:
                    raise ValueError("external_flow_or_inventory_change_unreconciled")
                at = epoch(row["candidate_ts"])
                for ending, reserved, proceeds in active[:]:
                    if ending < at:
                        wallet += proceeds
                        active.remove((ending, reserved, proceeds))
                qty = quantity(
                    source, max(0, min(wallet, source["available_cash_krw"]))
                )
                if qty == 0:
                    daily[day] += 0.0
                    details.append(
                        dict(
                            evaluation_id=row["evaluation_id"],
                            quantity=0,
                            baseline_no_trade=True,
                            baseline_net_krw=0.0,
                            challenger_net_krw=0.0,
                            buy_notional_krw=0.0,
                            reserved_krw=0.0,
                            evidence_mode="counterfactual",
                        )
                    )
                    continue
                execution = row.get("counterfactual_execution") or {}
                if (
                    execution.get("status") != "full_depth_model"
                    or execution.get("route") != source["route"]
                    or execution.get("transport_epoch") != source["transport_epoch"]
                    or not re.fullmatch(
                        "[0-9a-f]{64}", str(execution.get("source_sha256"))
                    )
                    or not finite(execution.get("observed_epoch"))
                    or not 0
                    <= epoch(execution["exit_at"]) - execution["observed_epoch"]
                    <= 1
                    or not finite(execution.get("exit_bid_krw"))
                    or execution["exit_bid_krw"] <= 0
                    or type(execution.get("exit_bid_qty")) is not int
                    or execution["exit_bid_qty"] < qty
                    or type(source.get("entry_ask_qty")) is not int
                    or source["entry_ask_qty"] < qty
                    or not finite(execution.get("buy_cost_rate"))
                    or not finite(execution.get("sell_cost_rate"))
                    or not 0 <= execution["buy_cost_rate"] < 1
                    or not 0 <= execution["sell_cost_rate"] < 1
                    or not re.fullmatch(
                        "[0-9a-f]{64}", str(execution.get("cost_source_sha256"))
                    )
                    or epoch(execution["cost_known_at"]) > at
                ):
                    raise ValueError("full_depth_or_cost_model_missing")
                end = epoch(execution["exit_at"])
                if not at < end <= epoch(day + "T23:59:59+09:00"):
                    raise ValueError("exit_time_or_split_boundary_invalid")
                buy = qty * source["price_krw"] * (1 + execution["buy_cost_rate"])
                sell = (
                    qty * execution["exit_bid_krw"] * (1 - execution["sell_cost_rate"])
                )
                if buy > wallet:
                    qty = min(
                        qty,
                        int(
                            wallet
                            // (source["price_krw"] * (1 + execution["buy_cost_rate"]))
                        ),
                    )
                    buy = qty * source["price_krw"] * (1 + execution["buy_cost_rate"])
                    sell = (
                        qty
                        * execution["exit_bid_krw"]
                        * (1 - execution["sell_cost_rate"])
                    )
                wallet -= buy
                active.append((end, buy, sell))
                delta = sell - buy
                daily[day] += delta
                details.append(
                    dict(
                        evaluation_id=row["evaluation_id"],
                        quantity=qty,
                        baseline_no_trade=True,
                        baseline_net_krw=0.0,
                        challenger_net_krw=delta,
                        buy_notional_krw=qty * source["price_krw"],
                        reserved_krw=buy,
                        exit_at=execution["exit_at"],
                        evidence_mode="counterfactual",
                    )
                )
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                gaps.append(dict(evaluation_id=row["evaluation_id"], reason=str(exc)))
                blocked = True
    return dict(
        status="complete" if rows and not gaps else "censored",
        gaps=gaps,
        rows=details,
        daily_net_profit_krw=dict(daily) if rows and not gaps else None,
        baseline_daily_net_profit_krw=(
            {d: 0.0 for d in daily} if rows and not gaps else None
        ),
        actual_profit_verified=False,
    )
