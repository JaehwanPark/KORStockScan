"""Effective-dated comparison costs for widget source-only research.

This module owns only normalized research/report economics.  It does not read
broker accounts, estimate an actual receipt, or change any live order path.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

SCHEMA = "widget_comparison_cost_policy_v1"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
CURRENT_EFFECTIVE_DATE = date(2026, 8, 18)
KST = ZoneInfo("Asia/Seoul")

_WINDOWS: tuple[dict[str, Any], ...] = (
    {
        "policy_id": "widget_legacy_comparison_cost_20bps",
        "effective_from": CLEAN_BASELINE_DATE.isoformat(),
        "effective_to": "2026-08-17",
        "buy_fee_bps": None,
        "sell_fee_bps": None,
        "statutory_sell_tax_bps": None,
        "round_trip_cost_bps": 20.0,
        "source": "legacy_widget_report_comparison_assumption",
    },
    {
        "policy_id": "widget_effective_dated_comparison_cost_23bps_v1",
        "effective_from": CURRENT_EFFECTIVE_DATE.isoformat(),
        "effective_to": None,
        "buy_fee_bps": 1.5,
        "sell_fee_bps": 1.5,
        "statutory_sell_tax_bps": 20.0,
        "round_trip_cost_bps": 23.0,
        "source": "operator_effective_dated_r0_r3_cost_contract_2026_08_18",
    },
)

METRIC_CONTRACT = {
    "metric_role": "source_only_comparison_economics",
    "decision_authority": "widget_postclose_comparison_cost_only",
    "window_policy": "effective_dated_by_entry_or_signal_trade_date",
    "sample_floor": "one_cost_policy_covered_clean_baseline_row",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "clean_baseline_date_and_unique_effective_cost_window_with_contract_hash"
    ),
    "forbidden_uses": [
        "actual_broker_receipt_cost_claim",
        "live_order_or_exit_decision",
        "quantity_target_cooldown_or_cap_mutation",
        "provider_bot_broker_guard_or_hard_safety_change",
    ],
}


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _as_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return (
            value.astimezone(KST).date() if value.tzinfo is not None else value.date()
        )
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def comparison_cost_contract(value: date | datetime | str) -> dict[str, Any]:
    """Resolve one unique immutable comparison-cost window."""

    target = _as_date(value)
    if target < CLEAN_BASELINE_DATE:
        raise ValueError("widget_comparison_cost_pre_clean_baseline")
    matches = []
    for row in _WINDOWS:
        effective_from = date.fromisoformat(str(row["effective_from"]))
        effective_to = (
            date.fromisoformat(str(row["effective_to"]))
            if row.get("effective_to")
            else None
        )
        if effective_from <= target and (
            effective_to is None or target <= effective_to
        ):
            matches.append(row)
    if len(matches) != 1:
        raise ValueError("widget_comparison_cost_window_not_unique")
    selected = dict(matches[0])
    payload = {
        "schema": SCHEMA,
        "trade_date": target.isoformat(),
        **selected,
        "round_trip_cost_pct": round(float(selected["round_trip_cost_bps"]) / 100.0, 8),
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "trading_runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**payload, "contract_sha256": _canonical_sha256(payload)}


def round_trip_cost_pct(value: date | datetime | str) -> float:
    return float(comparison_cost_contract(value)["round_trip_cost_pct"])


def cost_aware_return_pct(
    gross_return_pct: float, *, trade_date: date | datetime | str
) -> float:
    if isinstance(gross_return_pct, bool):
        raise ValueError("widget_comparison_gross_return_invalid")
    parsed = float(gross_return_pct)
    if not math.isfinite(parsed):
        raise ValueError("widget_comparison_gross_return_invalid")
    return parsed - round_trip_cost_pct(trade_date)


def modeled_execution_economics(
    *, buy_notional_krw: float, sell_notional_krw: float, trade_date: date | str
) -> dict[str, Any]:
    """Return comparison-model costs without claiming broker receipt exactness."""

    if isinstance(buy_notional_krw, bool) or isinstance(sell_notional_krw, bool):
        raise ValueError("widget_comparison_execution_notional_invalid")
    buy_notional_krw = float(buy_notional_krw)
    sell_notional_krw = float(sell_notional_krw)
    if (
        not math.isfinite(buy_notional_krw)
        or not math.isfinite(sell_notional_krw)
        or buy_notional_krw <= 0
        or sell_notional_krw < 0
    ):
        raise ValueError("widget_comparison_execution_notional_invalid")
    contract = comparison_cost_contract(trade_date)
    buy_fee_bps = contract.get("buy_fee_bps")
    sell_fee_bps = contract.get("sell_fee_bps")
    sell_tax_bps = contract.get("statutory_sell_tax_bps")
    if any(value is None for value in (buy_fee_bps, sell_fee_bps, sell_tax_bps)):
        total_cost = buy_notional_krw * float(contract["round_trip_cost_pct"]) / 100
        cost_basis = "legacy_round_trip_entry_notional_proxy"
        buy_fee = sell_fee = sell_tax = None
    else:
        buy_fee = buy_notional_krw * float(buy_fee_bps) / 10_000.0
        sell_fee = sell_notional_krw * float(sell_fee_bps) / 10_000.0
        sell_tax = sell_notional_krw * float(sell_tax_bps) / 10_000.0
        total_cost = buy_fee + sell_fee + sell_tax
        cost_basis = "effective_dated_notional_component_model"
    gross_profit = sell_notional_krw - buy_notional_krw
    net_profit = gross_profit - total_cost
    return {
        "gross_profit_krw": round(gross_profit, 6),
        "modeled_buy_fee_krw": None if buy_fee is None else round(buy_fee, 6),
        "modeled_sell_fee_krw": None if sell_fee is None else round(sell_fee, 6),
        "modeled_sell_tax_krw": None if sell_tax is None else round(sell_tax, 6),
        "modeled_total_cost_krw": round(total_cost, 6),
        "modeled_net_profit_krw": round(net_profit, 6),
        "modeled_net_return_pct": (
            round(net_profit / buy_notional_krw * 100.0, 8)
            if buy_notional_krw > 0
            else None
        ),
        "cost_basis": cost_basis,
        "broker_receipt_exact": False,
        "cost_contract": contract,
    }


__all__ = [
    "CURRENT_EFFECTIVE_DATE",
    "METRIC_CONTRACT",
    "SCHEMA",
    "comparison_cost_contract",
    "cost_aware_return_pct",
    "modeled_execution_economics",
    "round_trip_cost_pct",
]
