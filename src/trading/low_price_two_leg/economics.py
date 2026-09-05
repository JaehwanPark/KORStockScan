"""Shared economic contract for low-price two-leg research and runtime gates."""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Iterable

ROUND_TRIP_COST_PCT = 0.23
COST_CONTRACT_VERSION = "low_price_two_leg_round_trip_cost_v1"


def cost_contract() -> dict[str, Any]:
    """Return the canonical contract shared by all low-price cost consumers."""

    return {
        "version": COST_CONTRACT_VERSION,
        "round_trip_cost_pct": ROUND_TRIP_COST_PCT,
        "scope": "low_price_two_leg_research_and_actual_outcome",
    }


def recost_minute_bar_episodes(
    episodes: Iterable[dict[str, Any]],
    *,
    source_cost_pct: float,
    target_cost_pct: float = ROUND_TRIP_COST_PCT,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """Reprice realized minute-bar legs without treating held legs as closed PnL."""

    source_cost = float(source_cost_pct)
    target_cost = float(target_cost_pct)
    if not all(
        math.isfinite(value) and 0.0 <= value < 100.0
        for value in (source_cost, target_cost)
    ):
        raise ValueError("low_price_two_leg_cost_pct_invalid")
    selected: list[dict[str, Any]] = []
    for episode in episodes:
        if not isinstance(episode, dict):
            raise ValueError("low_price_two_leg_episode_invalid")
        try:
            episode_date = date.fromisoformat(str(episode.get("date") or ""))
        except ValueError as exc:
            raise ValueError("low_price_two_leg_episode_date_invalid") from exc
        if start_date is not None and episode_date < start_date:
            continue
        if end_date is not None and episode_date > end_date:
            continue
        selected.append(episode)

    legs = [
        leg
        for episode in selected
        for leg in episode.get("legs", [])
        if isinstance(leg, dict)
    ]
    attempted_notional = 0.0
    completed_notional = 0.0
    realized_profit = 0.0
    completed_legs = 0
    held_legs = 0
    for leg in legs:
        try:
            entry_price = float(leg.get("entry_price") or 0.0)
        except (TypeError, ValueError) as exc:
            raise ValueError("low_price_two_leg_entry_price_invalid") from exc
        if not math.isfinite(entry_price) or entry_price <= 0.0:
            raise ValueError("low_price_two_leg_entry_price_invalid")
        attempted_notional += entry_price
        status = str(leg.get("status") or "")
        if status == "COMPLETE":
            try:
                source_net_pct = float(leg.get("net_profit_pct"))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "low_price_two_leg_complete_net_profit_invalid"
                ) from exc
            if not math.isfinite(source_net_pct):
                raise ValueError("low_price_two_leg_complete_net_profit_invalid")
            target_net_pct = source_net_pct + source_cost - target_cost
            completed_notional += entry_price
            realized_profit += entry_price * target_net_pct / 100.0
            completed_legs += 1
        elif status == "HELD":
            held_legs += 1
        elif status != "NO_FILL":
            raise ValueError("low_price_two_leg_leg_status_invalid")

    ev = realized_profit / attempted_notional * 100.0 if attempted_notional else None
    return {
        "signal_episodes": len(selected),
        "attempted_legs": len(legs),
        "completed_legs": completed_legs,
        "held_legs": held_legs,
        "attempted_notional_krw": round(attempted_notional, 6),
        "completed_notional_krw": round(completed_notional, 6),
        "realized_net_profit_krw": round(realized_profit, 6),
        "notional_weighted_ev_pct": round(ev, 6) if ev is not None else None,
        "source_cost_pct": source_cost,
        "effective_cost_pct": target_cost,
    }
