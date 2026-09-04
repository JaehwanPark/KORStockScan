"""Pure quantity and price math shared by stage-specific split policies.

This module deliberately owns no evidence, policy selection, runtime enablement,
or order authority.  Entry and AVG_DOWN scale-in keep separate producers and
consumers; only their deterministic quantity-conservation and tick math is
shared here.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size


def split_qty(total_qty: int, leg_count: int, first_weight: float) -> list[int]:
    """Split a fixed quantity without increasing it or creating zero-size legs."""

    total_qty = int(total_qty)
    leg_count = min(max(1, int(leg_count)), total_qty)
    if leg_count <= 1:
        return [total_qty]
    first_qty = max(
        1,
        min(
            total_qty - (leg_count - 1),
            int(round(total_qty * float(first_weight))),
        ),
    )
    remaining = total_qty - first_qty
    quantities = [first_qty]
    for index in range(leg_count - 1):
        legs_left = leg_count - 1 - index
        qty = max(1, remaining // legs_left)
        quantities.append(qty)
        remaining -= qty
    if sum(quantities) != total_qty:
        quantities[-1] += total_qty - sum(quantities)
    return quantities


def split_qty_by_weights(
    total_qty: int, leg_count: int, weights: Sequence[float]
) -> list[int]:
    """Split a fixed quantity by normalized weights with deterministic ties."""

    total_qty = int(total_qty)
    leg_count = min(max(1, int(leg_count)), total_qty)
    if leg_count <= 1:
        return [total_qty]
    normalized = [
        max(0.0, float(weight or 0.0)) for weight in list(weights)[:leg_count]
    ]
    while len(normalized) < leg_count:
        normalized.append(0.0)
    weight_sum = sum(normalized)
    if weight_sum <= 0:
        return split_qty(total_qty, leg_count, 0.5)
    normalized = [weight / weight_sum for weight in normalized]
    if leg_count == 2:
        first_qty = max(1, min(total_qty - 1, int(round(total_qty * normalized[0]))))
        return [first_qty, total_qty - first_qty]
    quantities = [1] * leg_count
    remaining = total_qty - leg_count
    raw_allocations = [remaining * weight for weight in normalized]
    floors = [int(value) for value in raw_allocations]
    for index, value in enumerate(floors):
        quantities[index] += value
    leftover = remaining - sum(floors)
    remainders = sorted(
        (
            (raw_allocations[index] - floors[index], index)
            for index in range(leg_count)
        ),
        key=lambda item: (-item[0], item[1]),
    )
    for _remainder, index in remainders[:leftover]:
        quantities[index] += 1
    return quantities


def tick_size(price: int) -> int:
    """Return a defensive positive tick size for a candidate order price."""

    try:
        return max(1, int(get_tick_size(price) or 1))
    except Exception:
        return 1


def pct_price_offset(base_price: int, offset_pct: float) -> int:
    """Apply a non-negative passive percentage offset and clamp to a KRX tick."""

    if base_price <= 0:
        return 0
    raw_price = int(
        round(float(base_price) * max(0.0, 1.0 - (float(offset_pct or 0.0) / 100.0)))
    )
    return clamp_price_to_tick(max(1, raw_price))
