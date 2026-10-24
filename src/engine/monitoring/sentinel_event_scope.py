"""Pure market/session interpretation shared by BUY and holding sentinels.

Observation routes do not establish actual execution venue. Each caller owns
its field precedence; Mapping access preserves lazy compact-field reads.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time
from typing import Any

EXPLICIT_TRADABLE_VENUES = {
    "KRX",
    "NXT",
    "KRX_NXT_INTEGRATED",
    "PREMARKET_KRX_LIKE",
}


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def canonical_venue(value: Any) -> str | None:
    text = _text(value).upper()
    if text in {"KRX_NXT_INTEGRATED", "KRX_NXT", "KRX+NXT", "SOR"}:
        return "KRX_NXT_INTEGRATED"
    if text in {"NXT_ONLY", "NXT"}:
        return "NXT"
    if text in {"KRX_ONLY", "KRX"}:
        return "KRX"
    if text in EXPLICIT_TRADABLE_VENUES:
        return text
    if text in {"_NX", "NXT_PREMARKET", "NXT_AFTERMARKET", "NXT_REGULAR"}:
        return "NXT"
    if text in {"KRX_REGULAR", "KRX"}:
        return "KRX"
    return None


def canonical_session(value: Any) -> str | None:
    text = _text(value).upper()
    if not text:
        return None
    if text in {
        "KRX_NXT_AFTERMARKET",
        "KRX_NXT_AFTERMARKET_CLOSE_ONLY",
        "KRX_NXT_AFTERMARKET_TERMINAL_EXIT",
        "NXT_AFTERMARKET_SOLO",
        "SESSION_TRANSITION",
        "CLOSED",
    }:
        return text
    if "PREMARKET_KRX_LIKE" in text or "KRX_LIKE_PREMARKET" in text:
        return "PREMARKET_KRX_LIKE"
    if "NXT" in text and "PRE" in text:
        return "NXT_PREMARKET"
    if "NXT" in text and ("AFTER" in text or "POST" in text):
        return "NXT_AFTERMARKET"
    if "NXT" in text:
        return "NXT_REGULAR"
    if "KRX" in text:
        return "KRX_REGULAR"
    return None


def session_for_venue(venue: str, emitted_at: datetime) -> str:
    if venue == "PREMARKET_KRX_LIKE":
        return "PREMARKET_KRX_LIKE"
    if venue == "KRX":
        return "KRX_REGULAR"
    if venue == "KRX_NXT_INTEGRATED":
        if emitted_at.date() < date(2026, 9, 14):
            return "UNKNOWN"
        if time(16, 0) <= emitted_at.time() < time(19, 40):
            return "KRX_NXT_AFTERMARKET"
        if time(19, 40) <= emitted_at.time() < time(19, 45):
            return "KRX_NXT_AFTERMARKET_CLOSE_ONLY"
        if time(19, 45) <= emitted_at.time() < time(20, 0):
            return "KRX_NXT_AFTERMARKET_TERMINAL_EXIT"
        return "UNKNOWN"
    if emitted_at.time() < time(9, 0):
        return "NXT_PREMARKET"
    if emitted_at.time() > time(15, 30):
        return "NXT_AFTERMARKET"
    return "NXT_REGULAR"


def explicit_event_scope(
    fields: Mapping[str, Any],
    emitted_at: datetime,
    *,
    venue_keys: tuple[str, ...],
    session_keys: tuple[str, ...],
) -> tuple[str, str, str] | None:
    venue = next(
        (
            venue
            for key in venue_keys[:-1]
            if (venue := canonical_venue(fields.get(key))) is not None
        ),
        None,
    )
    fallback_venue = canonical_venue(fields.get(venue_keys[-1]))
    session = next(
        (
            session
            for key in session_keys[:-1]
            if (session := canonical_session(fields.get(key))) is not None
        ),
        None,
    )
    fallback_session = canonical_session(fields.get(session_keys[-1]))
    venue = venue or fallback_venue
    session = session or fallback_session
    if venue is None and session is not None:
        if session.startswith("KRX_NXT_AFTERMARKET"):
            venue = "KRX_NXT_INTEGRATED"
        else:
            venue = (
                "PREMARKET_KRX_LIKE"
                if session == "PREMARKET_KRX_LIKE"
                else ("NXT" if session.startswith("NXT_") else "KRX")
            )
    if venue is None:
        return None
    if session is None:
        session = session_for_venue(venue, emitted_at)
    elif (
        venue == "NXT"
        and session == "NXT_REGULAR"
        and (emitted_at.time() < time(9, 0) or emitted_at.time() > time(15, 30))
    ):
        session = session_for_venue(venue, emitted_at)
    if (
        (venue == "NXT" and not session.startswith("NXT_"))
        or (venue == "KRX" and session != "KRX_REGULAR")
        or (
            venue == "KRX_NXT_INTEGRATED"
            and not session.startswith("KRX_NXT_AFTERMARKET")
        )
        or (venue == "PREMARKET_KRX_LIKE" and session != "PREMARKET_KRX_LIKE")
    ):
        return "CONFLICT", "CONFLICT", "conflict"
    return venue, session, "pass"


def actual_execution_venue(fields: Mapping[str, Any]) -> str:
    value = _text(fields.get("actual_execution_venue")).upper()
    return value if value in {"KRX", "NXT"} else "UNKNOWN"
