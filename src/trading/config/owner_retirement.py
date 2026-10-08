"""Permanent automatic-owner retirement; historical receipts remain readable.

This registry owns symbol/owner retirement, not broker protocol or policy
quality. Consumers must use the symbol, including for dynamically named lanes.
"""

from __future__ import annotations

RETIRED_AUTOMATIC_OWNERS = frozenset({"episode", "widget_auto_trade"})


def automatic_owner_retired(owner: object) -> bool:
    return str(owner or "").strip().lower() in RETIRED_AUTOMATIC_OWNERS

# Historical identities only. Runtime parameters for these lanes are removed.
RETIRED_EPISODE_PROFILES = {
    "034020": ("doosan_enerbility_morning", "doosan_enerbility_late_morning", "doosan_enerbility_afternoon"),
    "002900": ("tym_morning", "tym_late_morning", "tym_midday", "tym_afternoon"),
    "079160": ("cj_cgv_morning", "cj_cgv_late_morning", "cj_cgv_midday", "cj_cgv_afternoon"),
    "111770": ("youngone_morning", "youngone_midday", "youngone_afternoon"),
    "017670": ("sk_telecom_morning", "sk_telecom_late_morning", "sk_telecom_midday", "sk_telecom_afternoon"),
    "080220": ("jeju_semiconductor_morning",),
    "105630": ("hanse_morning", "hanse_late_morning", "hanse_midday", "hanse_afternoon"),
    "181710": ("nhn_morning", "nhn_late_morning", "nhn_midday", "nhn_afternoon"),
    "035720": ("kakao_morning", "kakao_late_morning", "kakao_midday"),
}
RETIRED_SYMBOL_OWNERS = frozenset((symbol, "episode") for symbol in RETIRED_EPISODE_PROFILES)


def new_entry_retired(symbol: object, owner: object) -> bool:
    code = str(symbol or "").strip()
    if code.startswith("A"):
        code = code[1:]
    code = code.split("_", 1)[0]
    owner_name = str(owner or "").strip().lower()
    if automatic_owner_retired(owner_name):
        return True
    if (code, owner_name) in RETIRED_SYMBOL_OWNERS:
        return True
    if owner_name == "episode":
        from src.engine.scalping.main_fixed_watch import SPECS
        return any(spec.symbol == code and spec.episode_entry_forbidden for spec in SPECS)
    return False


def require_new_entry_owner(symbol: object, owner: object) -> None:
    if new_entry_retired(symbol, owner):
        raise ValueError("symbol_owner_permanently_retired")


# Historical identities only, used to exclude immutable archived lane rows.
RETIRED_EPISODE_PROFILE_IDS = frozenset(profile for profiles in RETIRED_EPISODE_PROFILES.values() for profile in profiles)


def episode_profile_retired(profile_id: object) -> bool:
    return str(profile_id or "") in RETIRED_EPISODE_PROFILE_IDS


RETIRED_MACHINE_SCOPE_LABELS = {
    "034020": "doosan_widget_and_episode_independent_owners",
    "002900": "tym_low_price_two_leg_owner",
    "079160": "cj_cgv_low_price_two_leg_owner",
    "111770": "youngone_low_price_two_leg_owner",
    "017670": "sk_telecom_low_price_two_leg_owner",
    "080220": "jeju_semiconductor_low_price_two_leg_owner",
    "105630": "hanse_low_price_two_leg_owner",
    "181710": "nhn_low_price_two_leg_owner",
    "035720": "kakao_low_price_two_leg_owner",
}


def active_entry_owners(symbol: object, owners) -> list[str]:
    return sorted(owner for owner in owners if not new_entry_retired(symbol, owner))


def main_manual_after_episode_retirement(symbol: object, owners) -> bool:
    """Accept the surviving native owners only for a retired episode symbol."""
    return new_entry_retired(symbol, "episode") and set(owners) == {
        "main_scalping", "manual_operator",
    }
