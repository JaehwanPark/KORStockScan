"""Shared stagnation arithmetic, not order authority or a policy publisher.

The main adapter owns its existing eligibility/profit gates and state writes.
Independent owners may use ``positive_net_stagnation`` with their own frozen
identity and executable-price inputs; they still own cancel/sell reconciliation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal, localcontext


def stagnation_window(
    *,
    profit: float,
    peak: float,
    now: float,
    started: float,
    anchor_profit: float,
    anchor_peak: float,
    min_sec: int,
    max_profit_move: float,
    max_peak_improve: float,
) -> dict:
    """Preserve the main's absolute-move/peak-improvement reset semantics."""
    move = abs(profit - anchor_profit)
    improvement = peak - anchor_peak
    if started <= 0 or move > max_profit_move or improvement > max_peak_improve:
        return {
            "should_exit": False,
            "reason": "anchor_reset",
            "elapsed_sec": 0,
            "anchor_profit": float(profit),
            "anchor_peak": float(peak),
            "profit_move": 0.0,
            "peak_improve": 0.0,
        }
    elapsed = max(0, int(float(now) - started))
    result = {
        "should_exit": elapsed >= min_sec,
        "elapsed_sec": elapsed,
        "anchor_profit": anchor_profit,
        "anchor_peak": anchor_peak,
        "profit_move": move,
        "peak_improve": max(0.0, improvement),
    }
    if elapsed >= min_sec:
        result.update(
            min_sec=min_sec,
            max_profit_move=max_profit_move,
            max_peak_improve=max_peak_improve,
        )
    else:
        result["reason"] = "waiting"
    return result


def _finite(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def positive_net_stagnation(
    *,
    identity: str,
    now: float,
    quote_at: float,
    quote_id: str,
    entry_price: float,
    executable_bid: float,
    quantity: int,
    available_quantity: int,
    round_trip_cost_pct: float,
    slippage_bps: float,
    previous: Mapping | None,
    min_sec: int = 180,
    max_profit_move: float = 0.15,
    max_peak_improve: float = 0.10,
    max_quote_age_sec: float = 2.0,
    max_observation_gap_sec: float = 5.0,
) -> tuple[dict, dict]:
    """Return (candidate, next state); no I/O and no live enable default.

    Identity must bind owner/episode, venue/session, policy/cost generation,
    quantity and average entry price. Executable bid is the WORST price that
    covers the entire remaining quantity, not midpoint/VWAP/last trade. Costs
    are an explicit entry-notional percentage; slippage is an additional sell
    price haircut. This estimate is never a broker-realized profit guarantee.
    A missing input clears the continuous observation window, not custody.
    """

    def blocked(reason):
        return {"should_exit": False, "reason": reason}, {}

    if (
        not isinstance(identity, str)
        or not identity
        or not isinstance(quote_id, str)
        or not quote_id
    ):
        return blocked("identity_missing")
    if (
        not all(
            _finite(v)
            for v in (
                now,
                quote_at,
                entry_price,
                executable_bid,
                round_trip_cost_pct,
                slippage_bps,
                max_profit_move,
                max_peak_improve,
                max_quote_age_sec,
                max_observation_gap_sec,
            )
        )
        or type(quantity) is not int
        or quantity <= 0
        or type(available_quantity) is not int
        or available_quantity < quantity
        or type(min_sec) is not int
        or min_sec <= 0
        or entry_price <= 0
        or executable_bid <= 0
        or not 0 <= round_trip_cost_pct < 100
        or not 0 <= slippage_bps < 10000
        or min(max_profit_move, max_peak_improve) < 0
        or min(max_quote_age_sec, max_observation_gap_sec) <= 0
        or not 0 < quote_at <= now
        or now - quote_at > max_quote_age_sec
    ):
        return blocked("invalid_or_stale_executable_input")
    # Compare proceeds against cost before dividing. Binary cancellation at
    # exact break-even must not turn zero net into a tiny positive candidate.
    with localcontext() as ctx:
        ctx.prec = 50
        entry = Decimal(str(entry_price))
        proceeds = Decimal(str(executable_bid)) * (
            1 - Decimal(str(slippage_bps)) / 10000
        )
        margin = proceeds - entry * (1 + Decimal(str(round_trip_cost_pct)) / 100)
        net = float(margin / entry * 100)
    if not math.isfinite(net):
        return blocked("invalid_net_estimate")
    if net <= 0:
        return {
            "should_exit": False,
            "reason": "nonpositive_net",
            "net_return_pct": net,
        }, {}
    # These fields are included even if a caller accidentally keeps its outer
    # identity constant across a partial fill or a cost/parameter change.
    binding = [
        identity,
        entry_price,
        quantity,
        round_trip_cost_pct,
        slippage_bps,
        min_sec,
        max_profit_move,
        max_peak_improve,
        max_quote_age_sec,
        max_observation_gap_sec,
    ]
    old = previous if isinstance(previous, Mapping) else {}
    valid_prior = (
        old.get("binding") == binding
        and all(
            _finite(old.get(k))
            for k in (
                "started",
                "anchor_profit",
                "anchor_peak",
                "peak",
                "last_at",
                "quote_at",
            )
        )
        and 0 < old["started"] <= old["last_at"] <= now
        and 0 < old["quote_at"] <= old["last_at"]
        and now - old["last_at"] <= max_observation_gap_sec
        and quote_at >= old["quote_at"]
        and old["peak"] >= old["anchor_peak"] >= old["anchor_profit"] > 0
        and isinstance(old.get("quote_id"), str)
        and bool(old["quote_id"])
    )
    if valid_prior and (quote_id == old.get("quote_id") or quote_at == old["quote_at"]):
        # Polling the same quote is not a new observation and cannot advance
        # the duration. Do not update last_at to bridge a source outage.
        return {
            "should_exit": False,
            "reason": "duplicate_quote",
            "net_return_pct": net,
        }, dict(old)
    if not valid_prior:
        old = {}
    peak = max(net, old.get("peak", net))
    result = stagnation_window(
        profit=net,
        peak=peak,
        now=now,
        started=old.get("started", 0.0),
        anchor_profit=old.get("anchor_profit", net),
        anchor_peak=old.get("anchor_peak", peak),
        min_sec=min_sec,
        max_profit_move=max_profit_move,
        max_peak_improve=max_peak_improve,
    )
    result.update(
        net_return_pct=net, reason=result.get("reason", "positive_net_stagnation")
    )
    return result, {
        "binding": binding,
        "started": now if result["reason"] == "anchor_reset" else old["started"],
        "anchor_profit": result["anchor_profit"],
        "anchor_peak": result["anchor_peak"],
        "peak": peak,
        "last_at": now,
        "quote_at": quote_at,
        "quote_id": quote_id,
    }
