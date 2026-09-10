"""Quantity contract shared by independent episode trading machines."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

LEGACY_EPISODE_LEG_QUANTITY = 1
EPISODE_LEG_QUANTITY = 10
EPISODE_LEG_COUNT = 2
EPISODE_TOTAL_QUANTITY = EPISODE_LEG_QUANTITY * EPISODE_LEG_COUNT
SUPPORTED_OWNED_LEG_QUANTITIES = frozenset(
    {LEGACY_EPISODE_LEG_QUANTITY, EPISODE_LEG_QUANTITY}
)


def validate_owned_leg_quantity(quantity: int) -> int:
    """Accept baseline 10-share and legacy/operator-approved 1-share lots."""

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


# Explicit operator instruction: new widget/episode entries on this KST date
# only. Baseline and persisted owned quantities above remain unchanged.
ONE_SHARE_ENTRY_DATE = date(2026, 9, 11)
ONE_SHARE_ENTRY_AUTHORITY = "user_one_day_new_entry_quantity_20260911"


def new_entry_quantity(now: datetime, baseline: int = EPISODE_LEG_QUANTITY) -> int:
    """Size a new entry; never use this to resize an owned/submitted order."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("new_entry_quantity_requires_aware_timestamp")
    if isinstance(baseline, bool) or not isinstance(baseline, int) or baseline < 1:
        raise ValueError("new_entry_quantity_invalid_baseline")
    return (
        1
        if now.astimezone(ZoneInfo("Asia/Seoul")).date() == ONE_SHARE_ENTRY_DATE
        else baseline
    )


def new_entry_quantity_receipt(
    now: datetime, baseline: int = EPISODE_LEG_QUANTITY
) -> dict:
    quantity = new_entry_quantity(now, baseline)
    return {
        "authority": (
            ONE_SHARE_ENTRY_AUTHORITY
            if now.astimezone(ZoneInfo("Asia/Seoul")).date() == ONE_SHARE_ENTRY_DATE
            else "baseline"
        ),
        "effective_date": now.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat(),
        "baseline_leg_quantity": baseline,
        "effective_leg_quantity": quantity,
        "override_expires_at": "2026-09-12T00:00:00+09:00",
        "existing_owned_quantities_preserved": True,
    }
