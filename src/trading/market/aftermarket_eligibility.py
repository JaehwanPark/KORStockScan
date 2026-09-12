"""Pure, date-bound venue eligibility contract for aftermarket trading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from src.trading.market.session_contract import KST


QUALITY_VALID = "VALID"
QUALITY_PARTIAL = "PARTIAL"
QUALITY_UNKNOWN = "UNKNOWN"
QUALITY_CONFLICT = "CONFLICT"

VENUE_KRX = "KRX"
VENUE_NXT = "NXT"

BLOCKER_STOCK_CODE_INVALID = "aftermarket_eligibility_stock_code_invalid"
BLOCKER_TRADE_DATE_INVALID = "aftermarket_eligibility_trade_date_invalid"
BLOCKER_SOURCE_MISSING = "aftermarket_eligibility_source_missing"
BLOCKER_SOURCE_INVALID = "aftermarket_eligibility_source_invalid"
BLOCKER_SOURCE_DATE_MISSING = "aftermarket_eligibility_source_date_missing"
BLOCKER_SOURCE_STALE = "aftermarket_eligibility_source_stale"
BLOCKER_SOURCE_CONFLICT = "aftermarket_eligibility_source_conflict"
BLOCKER_SOURCE_INCOMPLETE = "aftermarket_eligibility_source_incomplete"
BLOCKER_ELIGIBILITY_UNKNOWN = "aftermarket_eligibility_unknown"
BLOCKER_PROVENANCE_PARTIAL = "aftermarket_eligibility_provenance_partial"


@dataclass(frozen=True)
class SymbolVenueEligibility:
    trade_date: date | None
    source_trade_date: date | None
    stock_code: str
    krx_regular_eligible: bool | None
    nxt_eligible: bool | None
    krx_aftermarket_eligible: bool | None
    eligible_venues: tuple[str, ...]
    audit_info: str
    stock_state: str
    order_warning: str
    market_code: str
    source_api_id: str
    source_revision: str
    observed_at_kst: datetime | None
    payload_sha256: str | None
    quality_state: str
    blockers: tuple[str, ...]


def resolve_symbol_venue_eligibility(
    stock_code: str,
    trade_date: date,
    source_snapshot: dict[str, Any] | None,
) -> SymbolVenueEligibility:
    """Resolve one symbol without calling providers, databases, or wall clocks."""

    normalized_code = _normalize_stock_code(stock_code)
    normalized_trade_date = _coerce_date(trade_date)
    if normalized_code is None:
        return _invalid_result("", normalized_trade_date, BLOCKER_STOCK_CODE_INVALID)
    if normalized_trade_date is None:
        return _invalid_result(normalized_code, None, BLOCKER_TRADE_DATE_INVALID)
    if source_snapshot is None:
        return _invalid_result(
            normalized_code,
            normalized_trade_date,
            BLOCKER_SOURCE_MISSING,
        )
    if not isinstance(source_snapshot, dict):
        return _invalid_result(
            normalized_code,
            normalized_trade_date,
            BLOCKER_SOURCE_INVALID,
        )

    blockers = list(_coerce_blockers(source_snapshot))
    raw_quality = str(source_snapshot.get("quality_state") or "").strip().upper()
    conflict = raw_quality == QUALITY_CONFLICT
    quality_token_invalid = raw_quality not in {
        "",
        QUALITY_VALID,
        QUALITY_PARTIAL,
        QUALITY_UNKNOWN,
        QUALITY_CONFLICT,
    }
    source_code_raw = source_snapshot.get("stock_code") or source_snapshot.get("code")
    source_code = (
        _normalize_stock_code(source_code_raw) if source_code_raw is not None else None
    )
    if source_code_raw is not None and source_code != normalized_code:
        conflict = True

    source_trade_date = _coerce_date(
        source_snapshot.get("trade_date", source_snapshot.get("source_date"))
    )
    stale = source_trade_date is not None and source_trade_date != normalized_trade_date
    if source_trade_date is None:
        blockers.append(BLOCKER_SOURCE_DATE_MISSING)
    if stale:
        blockers.append(BLOCKER_SOURCE_STALE)

    krx_regular, krx_regular_invalid = _coerce_nullable_bool(
        source_snapshot.get("krx_regular_eligible")
    )
    nxt_source = (
        source_snapshot.get("nxt_eligible")
        if "nxt_eligible" in source_snapshot
        else source_snapshot.get("nxtEnable")
    )
    nxt, nxt_invalid = _coerce_nullable_bool(nxt_source)
    krx_aftermarket, krx_aftermarket_invalid = _coerce_nullable_bool(
        source_snapshot.get("krx_aftermarket_eligible")
    )
    malformed = (
        krx_regular_invalid
        or nxt_invalid
        or krx_aftermarket_invalid
        or quality_token_invalid
    )

    listed_venues, listed_present, listed_invalid = _coerce_venues(
        source_snapshot.get("eligible_venues_json")
    )
    malformed = malformed or listed_invalid
    derived_venues = tuple(
        venue
        for venue, eligible in (
            (VENUE_KRX, krx_aftermarket),
            (VENUE_NXT, nxt),
        )
        if eligible is True
    )
    if listed_present:
        for venue, eligible in (
            (VENUE_KRX, krx_aftermarket),
            (VENUE_NXT, nxt),
        ):
            if eligible is not None and ((venue in listed_venues) is not eligible):
                conflict = True
        eligible_venues = listed_venues
    else:
        eligible_venues = derived_venues

    if conflict:
        blockers.append(BLOCKER_SOURCE_CONFLICT)
    if malformed:
        blockers.append(BLOCKER_SOURCE_INVALID)
    incomplete = source_snapshot.get("complete") is False or str(
        source_snapshot.get("status") or ""
    ).strip().lower() == "partial"
    if incomplete:
        blockers.append(BLOCKER_SOURCE_INCOMPLETE)

    observed_at_kst, observed_invalid = _coerce_observed_at(
        source_snapshot.get("observed_at_kst")
    )
    if observed_invalid:
        blockers.append(BLOCKER_SOURCE_INVALID)
    source_api_id = _text(
        source_snapshot.get("source_api_id", source_snapshot.get("api_id"))
    )
    source_revision = _text(
        source_snapshot.get(
            "source_revision", source_snapshot.get("official_upstream_commit")
        )
    )
    payload_sha256 = (
        _text(
            source_snapshot.get(
                "payload_sha256", source_snapshot.get("source_sha256")
            )
        )
        or None
    )
    if not source_api_id or not source_revision or not payload_sha256 or observed_at_kst is None:
        blockers.append(BLOCKER_PROVENANCE_PARTIAL)

    aftermarket_unknown = nxt is None and krx_aftermarket is None
    if aftermarket_unknown:
        blockers.append(BLOCKER_ELIGIBILITY_UNKNOWN)

    if conflict:
        quality_state = QUALITY_CONFLICT
        eligible_venues = tuple()
    elif (
        stale
        or malformed
        or incomplete
        or source_trade_date is None
        or raw_quality == QUALITY_UNKNOWN
        or aftermarket_unknown
    ):
        quality_state = QUALITY_UNKNOWN
        eligible_venues = tuple()
    elif (
        raw_quality == QUALITY_PARTIAL
        or BLOCKER_SOURCE_INCOMPLETE in blockers
        or BLOCKER_PROVENANCE_PARTIAL in blockers
        or krx_regular is None
        or nxt is None
        or krx_aftermarket is None
    ):
        quality_state = QUALITY_PARTIAL
    else:
        quality_state = QUALITY_VALID

    return SymbolVenueEligibility(
        trade_date=normalized_trade_date,
        source_trade_date=source_trade_date,
        stock_code=normalized_code,
        krx_regular_eligible=krx_regular,
        nxt_eligible=nxt,
        krx_aftermarket_eligible=krx_aftermarket,
        eligible_venues=eligible_venues,
        audit_info=_text(
            source_snapshot.get("audit_info", source_snapshot.get("auditInfo"))
        ),
        stock_state=_text(
            source_snapshot.get("stock_state", source_snapshot.get("state"))
        ),
        order_warning=_text(
            source_snapshot.get("order_warning", source_snapshot.get("orderWarning"))
        ),
        market_code=_text(
            source_snapshot.get("market_code", source_snapshot.get("marketCode"))
        ),
        source_api_id=source_api_id,
        source_revision=source_revision,
        observed_at_kst=observed_at_kst,
        payload_sha256=payload_sha256,
        quality_state=quality_state,
        blockers=_dedupe(blockers),
    )


def _invalid_result(
    stock_code: str,
    trade_date: date | None,
    blocker: str,
) -> SymbolVenueEligibility:
    return SymbolVenueEligibility(
        trade_date=trade_date,
        source_trade_date=None,
        stock_code=stock_code,
        krx_regular_eligible=None,
        nxt_eligible=None,
        krx_aftermarket_eligible=None,
        eligible_venues=tuple(),
        audit_info="",
        stock_state="",
        order_warning="",
        market_code="",
        source_api_id="",
        source_revision="",
        observed_at_kst=None,
        payload_sha256=None,
        quality_state=QUALITY_UNKNOWN,
        blockers=(blocker,),
    )


def _normalize_stock_code(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    for suffix in ("_AL", "_NX"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    if len(text) == 7 and text.startswith("A"):
        text = text[1:]
    return text if len(text) == 6 and text.isdigit() else None


def _coerce_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _coerce_nullable_bool(value: Any) -> tuple[bool | None, bool]:
    if value is None:
        return None, False
    if isinstance(value, bool):
        return value, False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value), False
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in {"Y", "YES", "TRUE", "1"}:
            return True, False
        if normalized in {"N", "NO", "FALSE", "0"}:
            return False, False
    return None, True


def _coerce_venues(value: Any) -> tuple[tuple[str, ...], bool, bool]:
    if value is None:
        return tuple(), False, False
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return tuple(), True, True
    if not isinstance(parsed, (list, tuple)):
        return tuple(), True, True
    venues: list[str] = []
    for item in parsed:
        venue = str(item or "").strip().upper()
        if venue not in {VENUE_KRX, VENUE_NXT}:
            return tuple(), True, True
        if venue not in venues:
            venues.append(venue)
    return tuple(venues), True, False


def _coerce_observed_at(value: Any) -> tuple[datetime | None, bool]:
    if value is None:
        return None, False
    observed = value
    if isinstance(value, str):
        try:
            observed = datetime.fromisoformat(value.strip())
        except ValueError:
            return None, True
    if not isinstance(observed, datetime) or observed.tzinfo is None:
        return None, True
    return observed.astimezone(KST), False


def _coerce_blockers(snapshot: dict[str, Any]) -> tuple[str, ...]:
    raw = snapshot.get("blocked_reasons_json", snapshot.get("blocked_reasons", ()))
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return tuple()
    return _dedupe(str(item).strip() for item in raw if str(item).strip())


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _dedupe(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
