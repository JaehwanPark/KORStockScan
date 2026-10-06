"""Permanent new-entry exclusions; historical custody keeps its exit owner.

This registry owns symbol/owner retirement, not broker protocol or policy
quality. Consumers must use the symbol, including for dynamically named lanes.
"""

from __future__ import annotations

RETIRED_SYMBOL_OWNERS = frozenset({("034020", "episode")})


def new_entry_retired(symbol: object, owner: object) -> bool:
    code = str(symbol or "").strip()
    if code.startswith("A"):
        code = code[1:]
    code = code.split("_", 1)[0]
    return (code, str(owner or "").strip().lower()) in RETIRED_SYMBOL_OWNERS


def require_new_entry_owner(symbol: object, owner: object) -> None:
    if new_entry_retired(symbol, owner):
        raise ValueError("symbol_owner_permanently_retired")


# Historical identities only, used to exclude immutable archived lane rows.
RETIRED_EPISODE_PROFILE_IDS = frozenset({
    "doosan_enerbility_morning", "doosan_enerbility_late_morning",
    "doosan_enerbility_afternoon",
})


def episode_profile_retired(profile_id: object) -> bool:
    return str(profile_id or "") in RETIRED_EPISODE_PROFILE_IDS


RETIRED_MACHINE_SCOPE_LABELS = {
    "034020": "doosan_widget_and_episode_independent_owners",
}


def active_entry_owners(symbol: object, owners) -> list[str]:
    return sorted(owner for owner in owners if not new_entry_retired(symbol, owner))


def main_manual_after_episode_retirement(symbol: object, owners) -> bool:
    """Accept the surviving native owners only for a retired episode symbol."""
    return new_entry_retired(symbol, "episode") and set(owners) == {
        "main_scalping", "manual_operator",
    }
