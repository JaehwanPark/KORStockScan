from __future__ import annotations


def get_tick_size(price: int | float) -> int:
    """Return the Korean stock tick size for a price."""

    p = int(price)
    if p < 2_000:
        return 1
    if p < 5_000:
        return 5
    if p < 20_000:
        return 10
    if p < 50_000:
        return 50
    if p < 200_000:
        return 100
    if p < 500_000:
        return 500
    return 1_000


def clamp_price_to_tick(price: int | float) -> int:
    """Clamp a raw price down to the nearest valid tick boundary."""

    p = max(1, int(price))
    tick = get_tick_size(p)
    return max(tick, (p // tick) * tick)


def move_price_by_ticks(price: int | float, ticks: int) -> int:
    """Move a price by a signed number of Korean market ticks."""

    moved = clamp_price_to_tick(price)
    if ticks == 0:
        return moved

    step = 1 if ticks > 0 else -1
    remaining = abs(ticks)
    for _ in range(remaining):
        if step > 0:
            moved += get_tick_size(moved)
            moved = clamp_price_to_tick(moved)
        else:
            previous = max(1, moved - 1)
            moved = clamp_price_to_tick(previous)
    return moved


def move_price_down_by_bps(
    price: int | float, bps: int, *, floor_ticks: int = 1
) -> int:
    """Move price down by bps (1 bps = 0.01%), clamp to tick, enforce minimum tick floor.

    Returns int price at least floor_ticks below the original price.
    """

    p = int(price)
    tick = get_tick_size(p)
    discount = max(1, p) * bps // 10000
    target = max(tick, p - discount)
    target_clamped = clamp_price_to_tick(target)

    tick_below = move_price_by_ticks(p, -floor_ticks)
    if target_clamped >= p:
        return tick_below
    if target_clamped > tick_below:
        return max(tick_below, clamp_price_to_tick(target_clamped))
    return target_clamped
