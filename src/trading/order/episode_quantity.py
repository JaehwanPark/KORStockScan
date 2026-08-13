"""Quantity contract shared by independent episode trading machines."""

from __future__ import annotations

LEGACY_EPISODE_LEG_QUANTITY = 1
EPISODE_LEG_QUANTITY = 10
EPISODE_LEG_COUNT = 2
EPISODE_TOTAL_QUANTITY = EPISODE_LEG_QUANTITY * EPISODE_LEG_COUNT
SUPPORTED_OWNED_LEG_QUANTITIES = frozenset(
    {LEGACY_EPISODE_LEG_QUANTITY, EPISODE_LEG_QUANTITY}
)


def validate_owned_leg_quantity(quantity: int) -> int:
    """Accept current 10-share legs and legacy 1-share owned state only."""

    if isinstance(quantity, bool) or int(quantity) != quantity:
        raise ValueError("invalid_episode_leg_quantity")
    quantity = int(quantity)
    if quantity not in SUPPORTED_OWNED_LEG_QUANTITIES:
        raise ValueError("unsupported_episode_leg_quantity")
    return quantity


def validate_position_quantity(quantity: int, *, maximum: int) -> int:
    """Validate a confirmed position/target quantity within one owned leg."""

    if isinstance(quantity, bool) or int(quantity) != quantity:
        raise ValueError("invalid_episode_position_quantity")
    quantity = int(quantity)
    if quantity < 0 or quantity > int(maximum):
        raise ValueError("episode_position_quantity_out_of_range")
    return quantity
