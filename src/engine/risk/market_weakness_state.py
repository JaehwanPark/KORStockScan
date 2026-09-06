"""Shared, side-effect-free weakness latch and freshness semantics.

Owned by risk, not a new strategy or report producer. Runtime consumers and
source-only policy hypotheses must use the same transition and TTL functions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

MAX_HEALTHY_OBSERVATION_AGE_SEC = 300
MAX_FUTURE_CLOCK_SKEW_SEC = 30
STATE_REPLAY_CONTRACT = "market_weakness_fresh300_source_hypothesis_v1"
LEGACY_STATE_REPLAY_CONTRACT = "market_weakness_legacy_session_latch_v1"


def observation_freshness(observed_at: datetime, now: datetime) -> tuple[bool, float]:
    if observed_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("market_weakness_timezone_required")
    age = (now - observed_at).total_seconds()
    return -MAX_FUTURE_CLOCK_SKEW_SEC <= age <= MAX_HEALTHY_OBSERVATION_AGE_SEC, age


def advance_market_latch(
    previous: Mapping[str, Any],
    classification: str,
    *,
    activation: int,
    release: int,
) -> dict[str, Any]:
    """Advance one uniquely spaced observation; UNKNOWN resets streaks only."""

    state = dict(previous)
    active = state.get("active") is True
    last_class = state.get("last_class")
    weak = recovery = 0
    if classification == "weak":
        weak = int(state.get("weak_streak") or 0) + 1 if last_class == "weak" else 1
        active = active or weak >= activation
    elif classification == "recovery":
        recovery = (
            int(state.get("recovery_streak") or 0) + 1
            if active and last_class == "recovery"
            else int(active)
        )
        active = active and recovery < release
    state.update(
        active=active,
        weak_streak=weak,
        recovery_streak=recovery,
        last_class=classification,
    )
    return state
