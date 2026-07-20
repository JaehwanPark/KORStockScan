"""Shared helpers for fee-aware trade profit calculations."""

from __future__ import annotations

from src.utils.constants import TRADING_RULES

DEFAULT_TRADE_COST_RATE = 0.0023


def _resolve_trade_cost_rate(cost_rate: float | None = None) -> float:
    if cost_rate is not None:
        try:
            return max(float(cost_rate), 0.0)
        except Exception:
            return DEFAULT_TRADE_COST_RATE
    try:
        configured = getattr(
            TRADING_RULES,
            "TRADE_COST_RATE",
            getattr(
                TRADING_RULES, "REPORT_REALIZED_PNL_COST_RATE", DEFAULT_TRADE_COST_RATE
            ),
        )
        return max(float(configured), 0.0)
    except Exception:
        return DEFAULT_TRADE_COST_RATE


def get_trade_cost_rate(cost_rate: float | None = None) -> float:
    return _resolve_trade_cost_rate(cost_rate)


def calculate_net_profit_rate(
    buy_price: float | int,
    sell_price: float | int,
    *,
    cost_rate: float | None = None,
    precision: int = 2,
) -> float:
    try:
        buy = float(buy_price or 0)
        sell = float(sell_price or 0)
    except Exception:
        return 0.0
    if buy <= 0 or sell <= 0:
        return 0.0
    rate = _resolve_trade_cost_rate(cost_rate)
    net_return_pct = (((sell * (1.0 - rate)) - buy) / buy) * 100.0
    return round(net_return_pct, precision)


def calculate_net_realized_pnl(
    buy_price: float | int,
    sell_price: float | int,
    qty: float | int,
    *,
    cost_rate: float | None = None,
) -> int:
    try:
        buy = float(buy_price or 0)
        sell = float(sell_price or 0)
        quantity = int(float(qty or 0))
    except Exception:
        return 0
    if buy <= 0 or sell <= 0 or quantity <= 0:
        return 0
    rate = _resolve_trade_cost_rate(cost_rate)
    gross_pnl = (sell - buy) * quantity
    trading_cost = sell * quantity * rate
    return int(round(gross_pnl - trading_cost))
