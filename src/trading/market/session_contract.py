"""Pure market-session contract resolver for AM-S01.

This module intentionally contains only contract inference logic and data
containers without touching downstream order/consumer behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time as dt_time
from zoneinfo import ZoneInfo
from typing import Any


KST = ZoneInfo("Asia/Seoul")


MARKET_SESSION_CONTRACT_VERSION_V1 = "market_session_contract_v1"
MARKET_SESSION_CONTRACT_VERSION_V2 = "market_session_contract_v2"
MARKET_SESSION_EFFECTIVE_DATE = date(2026, 9, 14)

SOURCE_QUALITY_VALID = "VALID"
SOURCE_QUALITY_PARTIAL = "PARTIAL"
SOURCE_QUALITY_UNKNOWN = "UNKNOWN"

MARKET_SESSION_REGIME_KRX_REGULAR = "KRX_REGULAR"
MARKET_SESSION_REGIME_SESSION_TRANSITION = "SESSION_TRANSITION"
MARKET_SESSION_REGIME_NXT_AFTERMARKET_SOLO = "NXT_AFTERMARKET_SOLO"
MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET = "KRX_NXT_AFTERMARKET"
MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY = "KRX_NXT_AFTERMARKET_CLOSE_ONLY"
MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_TERMINAL_EXIT = (
    "KRX_NXT_AFTERMARKET_TERMINAL_EXIT"
)
MARKET_SESSION_REGIME_CLOSED = "CLOSED"

MARKET_SESSION_REGIME_LEGACY_KRX_ONLY = "krx_regular"
MARKET_SESSION_REGIME_LEGACY_NXT_ONLY = "nxt_aftermarket"
MARKET_SESSION_REGIME_LEGACY_PREMARKET = "krx_like_premarket"
MARKET_SESSION_REGIME_LEGACY_TRANSITION = "session_transition"


MARKET_DATA_ROUTE_KRX_ONLY = "krx_only"
MARKET_DATA_ROUTE_NXT_ONLY = "nxt_only"
MARKET_DATA_ROUTE_KRX_NXT_INTEGRATED = "krx_nxt_integrated"
MARKET_DATA_ROUTE_UNKNOWN = "unknown"

ACTUAL_EXECUTION_VENUE_KRX = "KRX"
ACTUAL_EXECUTION_VENUE_NXT = "NXT"
ACTUAL_EXECUTION_VENUE_UNKNOWN = "UNKNOWN"

VENDOR_BLOCKER = "market_session_observed_at_timezone_missing"
VENDOR_INVALID_INPUT_BLOCKER = "market_session_input_invalid"
VENDOR_INVALID_CONTRACT_VERSION = "market_session_contract_version_invalid"
VENDOR_LEGACY_UNSUPPORTED_TIME_BLOCKER = "market_session_unsupported_time"
VENDOR_SOURCE_MISSING = "symbol_venue_eligibility_source_snapshot_missing"
VENDOR_SOURCE_INVALID = "symbol_venue_eligibility_source_snapshot_invalid"
VENDOR_STOCK_CODE_MISSING = "symbol_venue_eligibility_stock_code_missing"
VENDOR_TRADE_DATE_INVALID = "symbol_venue_eligibility_trade_date_invalid"

BROKER_ORDER_ROUTE_KRX = "KRX"
BROKER_ORDER_ROUTE_NXT = "NXT"
BROKER_ORDER_ROUTE_SOR = "SOR"

ORDER_TYPE_NORMAL = "0"
ORDER_TYPE_NORMAL_LEGACY = "00"
ORDER_TYPE_MARKET = "3"
ORDER_TYPE_BEST_LIMIT = "6"

ORDER_TYPE_PREFLIGHT_ALLOWED = "allowed"
ORDER_TYPE_PREFLIGHT_REMAP_MARKET_TO_BEST = "market_to_best_limit"
ORDER_TYPE_PREFLIGHT_SESSION_BLOCKED = "session_blocked"
ORDER_TYPE_PREFLIGHT_BUY_WINDOW_CLOSED = "buy_window_closed"
ORDER_TYPE_PREFLIGHT_EXISTING_HOLDING_REQUIRED = "existing_holding_required"
ORDER_TYPE_PREFLIGHT_ROUTE_UNSUPPORTED = "route_unsupported"
ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED = "order_type_unsupported"
ORDER_TYPE_PREFLIGHT_ELIGIBILITY_UNKNOWN = "eligibility_unknown"
ORDER_TYPE_PREFLIGHT_ROUTE_INELIGIBLE = "route_ineligible"


@dataclass(frozen=True)
class MarketSessionContext:
    contract_version: str
    observed_at_kst: datetime
    trade_date: date
    session_regime: str
    open_venues: tuple[str, ...]
    decision_market_scope: str
    preferred_market_data_route: str
    entry_allowed_by_clock: bool
    exit_allowed_by_clock: bool
    source_quality: str
    blocker: str | None


@dataclass(frozen=True)
class SymbolVenueEligibility:
    trade_date: date
    stock_code: str
    krx_regular_eligible: bool | None
    nxt_eligible: bool | None
    krx_aftermarket_eligible: bool | None
    eligible_venues: tuple[str, ...]
    source_id: str
    source_sha256: str | None
    observed_at_kst: datetime | None
    quality_state: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class OrderTypePreflight:
    allowed: bool
    requested_route: str
    effective_route: str | None
    side: str
    requested_order_type: str
    effective_order_type: str | None
    remapped: bool
    reason: str


def resolve_market_session(
    observed_at_kst: datetime,
    *,
    contract_version: str | None = None,
) -> MarketSessionContext:
    """Resolve market session context from an aware datetime.

    The resolver does not mutate any producer/consumer state and never infers
    live execution venue from source snapshots.
    """

    session_observed_at, blocker = _coerce_observed_at(observed_at_kst)

    if contract_version is not None and contract_version not in {
        MARKET_SESSION_CONTRACT_VERSION_V1,
        MARKET_SESSION_CONTRACT_VERSION_V2,
    }:
        return _invalid_market_session(
            session_observed_at,
            MARKET_SESSION_EFFECTIVE_DATE,
            VENDOR_INVALID_CONTRACT_VERSION,
        )

    if session_observed_at is None or blocker:
        return _invalid_market_session(
            session_observed_at,
            MARKET_SESSION_EFFECTIVE_DATE,
            blocker or VENDOR_INVALID_INPUT_BLOCKER,
        )

    resolved_version = (
        contract_version
        if contract_version is not None
        else _contract_version_for_date(session_observed_at.date())
    )
    if resolved_version == MARKET_SESSION_CONTRACT_VERSION_V1:
        return _resolve_legacy_session(session_observed_at, resolved_version)
    return _resolve_post_effective_session(session_observed_at, resolved_version)


def resolve_symbol_venue_eligibility(
    stock_code: str,
    trade_date: date,
    source_snapshot: dict[str, Any] | None,
) -> SymbolVenueEligibility:
    if not isinstance(stock_code, str) or not stock_code.strip():
        return _invalid_symbol_eligibility(
            stock_code if isinstance(stock_code, str) else "",
            trade_date if isinstance(trade_date, date) else _fallback_trade_date(),
            (VENDOR_STOCK_CODE_MISSING,),
        )
    if not isinstance(trade_date, date):
        return _invalid_symbol_eligibility(
            stock_code,
            _fallback_trade_date(),
            (VENDOR_TRADE_DATE_INVALID,),
        )
    if not isinstance(source_snapshot, dict):
        return _invalid_symbol_eligibility(
            stock_code,
            trade_date,
            (
                VENDOR_SOURCE_MISSING
                if source_snapshot is None
                else VENDOR_SOURCE_INVALID,
            ),
        )

    raw_blockers = _coerce_blockers(source_snapshot)
    krx_regular_eligible = _coerce_nullable_bool(
        source_snapshot.get("krx_regular_eligible")
    )
    nxt_eligible = _coerce_nullable_bool(source_snapshot.get("nxt_eligible"))
    krx_aftermarket_eligible = _coerce_nullable_bool(
        source_snapshot.get("krx_aftermarket_eligible")
    )

    venue_candidates = _derive_eligible_venues(
        krx_regular_eligible=krx_regular_eligible,
        nxt_eligible=nxt_eligible,
        krx_aftermarket_eligible=krx_aftermarket_eligible,
        listed_venues=source_snapshot.get("eligible_venues_json"),
    )
    source_sha256 = _coerce_text(source_snapshot.get("source_sha256")) or _coerce_text(
        source_snapshot.get("payload_sha256")
    )
    observed_at_snapshot = _coerce_observed_at(
        source_snapshot.get("observed_at_kst")
    )[0]
    quality_state = _coerce_text(
        source_snapshot.get("quality_state")
    ) or SOURCE_QUALITY_UNKNOWN
    source_id = _coerce_text(source_snapshot.get("source_id")) or source_snapshot.get(
        "source", ""
    ).strip() or stock_code

    return SymbolVenueEligibility(
        trade_date=trade_date,
        stock_code=stock_code.strip(),
        krx_regular_eligible=krx_regular_eligible,
        nxt_eligible=nxt_eligible,
        krx_aftermarket_eligible=krx_aftermarket_eligible,
        eligible_venues=venue_candidates,
        source_id=source_id,
        source_sha256=source_sha256,
        observed_at_kst=observed_at_snapshot,
        quality_state=quality_state,
        blockers=tuple(_dedupe_strings(raw_blockers)),
    )


def resolve_market_data_route(session_context: MarketSessionContext, purpose: str) -> str:
    """Return market data route for context.

    Purpose currently does not alter resolution in AM-S01; it is reserved for AM-S02+
    where route semantics are split by purpose.
    """

    if session_context.blocker is not None:
        return MARKET_DATA_ROUTE_UNKNOWN
    return session_context.preferred_market_data_route


def resolve_broker_order_route(
    session_context: MarketSessionContext,
    eligibility: SymbolVenueEligibility | None = None,
    authority: Any | None = None,
    side: str = "buy",
) -> str:
    """Resolve default broker route for the market session.

    `authority` and `eligibility` are intentionally read for future policy
    evolution and not interpreted here.
    """

    if session_context.blocker is not None:
        return MARKET_DATA_ROUTE_UNKNOWN
    if session_context.session_regime in {
        MARKET_SESSION_REGIME_SESSION_TRANSITION,
        MARKET_SESSION_REGIME_CLOSED,
    }:
        return MARKET_DATA_ROUTE_UNKNOWN
    route = session_context.preferred_market_data_route
    if session_context.session_regime == MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY:
        return route
    if side == "sell":
        return route
    return route


def resolve_order_type_preflight(
    session_context: MarketSessionContext,
    requested_route: str,
    side: str,
    order_type: str | int | None,
    *,
    eligibility: SymbolVenueEligibility | None = None,
    existing_holding: bool = False,
) -> OrderTypePreflight:
    """Resolve a broker-call-free order type decision.

    The post-effective after-market policy is deliberately narrower than the
    complete Kiwoom ``trde_tp`` enum: normal limit (0/00) and best limit (6)
    are allowed, while market (3) is remapped to best limit before submission.
    Every other type fails closed.  Regular and legacy sessions retain their
    pre-AM-S07 pass-through behavior.
    """

    route = str(requested_route or "").strip().upper()
    normalized_side = str(side or "").strip().lower()
    requested_type = "" if order_type is None else str(order_type).strip().upper()

    def decision(
        allowed: bool,
        reason: str,
        *,
        effective_type: str | None = None,
    ) -> OrderTypePreflight:
        return OrderTypePreflight(
            allowed=allowed,
            requested_route=route,
            effective_route=route if allowed else None,
            side=normalized_side,
            requested_order_type=requested_type,
            effective_order_type=effective_type if allowed else None,
            remapped=bool(allowed and effective_type != requested_type),
            reason=reason,
        )

    if session_context.blocker is not None:
        return decision(False, ORDER_TYPE_PREFLIGHT_SESSION_BLOCKED)
    if normalized_side not in {"buy", "sell"}:
        return decision(False, ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED)
    if session_context.session_regime in {
        MARKET_SESSION_REGIME_SESSION_TRANSITION,
        MARKET_SESSION_REGIME_NXT_AFTERMARKET_SOLO,
        MARKET_SESSION_REGIME_CLOSED,
    }:
        return decision(False, ORDER_TYPE_PREFLIGHT_SESSION_BLOCKED)
    if route not in {
        BROKER_ORDER_ROUTE_KRX,
        BROKER_ORDER_ROUTE_NXT,
        BROKER_ORDER_ROUTE_SOR,
    }:
        return decision(False, ORDER_TYPE_PREFLIGHT_ROUTE_UNSUPPORTED)
    if not requested_type:
        return decision(False, ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED)

    after_market_regimes = {
        MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
        MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY,
        MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_TERMINAL_EXIT,
    }
    if session_context.session_regime not in after_market_regimes:
        return decision(
            True,
            ORDER_TYPE_PREFLIGHT_ALLOWED,
            effective_type=requested_type,
        )

    if normalized_side == "buy":
        if not session_context.entry_allowed_by_clock:
            return decision(False, ORDER_TYPE_PREFLIGHT_BUY_WINDOW_CLOSED)
        eligibility_reason = _aftermarket_buy_eligibility_blocker(
            session_context,
            route,
            eligibility,
        )
        if eligibility_reason is not None:
            return decision(False, eligibility_reason)
    elif not session_context.entry_allowed_by_clock and not existing_holding:
        return decision(False, ORDER_TYPE_PREFLIGHT_EXISTING_HOLDING_REQUIRED)

    if requested_type in {ORDER_TYPE_NORMAL, ORDER_TYPE_NORMAL_LEGACY}:
        return decision(
            True,
            ORDER_TYPE_PREFLIGHT_ALLOWED,
            effective_type=requested_type,
        )
    if requested_type == ORDER_TYPE_BEST_LIMIT:
        return decision(
            True,
            ORDER_TYPE_PREFLIGHT_ALLOWED,
            effective_type=ORDER_TYPE_BEST_LIMIT,
        )
    if requested_type == ORDER_TYPE_MARKET:
        return decision(
            True,
            ORDER_TYPE_PREFLIGHT_REMAP_MARKET_TO_BEST,
            effective_type=ORDER_TYPE_BEST_LIMIT,
        )
    return decision(False, ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED)


def validate_order_type_for_session(
    session_context: MarketSessionContext,
    requested_route: str,
    side: str,
    order_type: str | int | None,
    *,
    eligibility: SymbolVenueEligibility | None = None,
    existing_holding: bool = False,
) -> bool:
    """Compatibility boolean wrapper for the detailed pure preflight."""

    return resolve_order_type_preflight(
        session_context,
        requested_route,
        side,
        order_type,
        eligibility=eligibility,
        existing_holding=existing_holding,
    ).allowed


def _aftermarket_buy_eligibility_blocker(
    session_context: MarketSessionContext,
    route: str,
    eligibility: SymbolVenueEligibility | None,
) -> str | None:
    if (
        eligibility is None
        or eligibility.trade_date != session_context.trade_date
        or eligibility.quality_state != SOURCE_QUALITY_VALID
        or eligibility.blockers
    ):
        return ORDER_TYPE_PREFLIGHT_ELIGIBILITY_UNKNOWN
    if route == BROKER_ORDER_ROUTE_KRX:
        route_eligibility = (eligibility.krx_aftermarket_eligible,)
    elif route == BROKER_ORDER_ROUTE_NXT:
        route_eligibility = (eligibility.nxt_eligible,)
    else:
        route_eligibility = (
            eligibility.krx_aftermarket_eligible,
            eligibility.nxt_eligible,
        )
    if any(value is None for value in route_eligibility):
        return ORDER_TYPE_PREFLIGHT_ELIGIBILITY_UNKNOWN
    if not all(route_eligibility):
        return ORDER_TYPE_PREFLIGHT_ROUTE_INELIGIBLE
    return None


def classify_actual_execution_venue(broker_receipt: dict[str, Any]) -> str:
    if not isinstance(broker_receipt, dict):
        return ACTUAL_EXECUTION_VENUE_UNKNOWN
    requested_route = str(
        broker_receipt.get("broker_route_requested") or broker_receipt.get("route") or ""
    ).strip().upper()
    if requested_route == "SOR":
        return ACTUAL_EXECUTION_VENUE_UNKNOWN
    for field in ("actual_execution_venue", "execution_venue", "market"):
        raw = str(broker_receipt.get(field) or "").strip().upper()
        if raw in {ACTUAL_EXECUTION_VENUE_KRX, ACTUAL_EXECUTION_VENUE_NXT}:
            return raw
        if raw in {"0", "통합", "", "UNKNOWN"}:
            return ACTUAL_EXECUTION_VENUE_UNKNOWN
    return ACTUAL_EXECUTION_VENUE_UNKNOWN


def _coerce_observed_at(
    observed_at_kst: datetime | Any,
) -> tuple[datetime | None, str | None]:
    if not isinstance(observed_at_kst, datetime):
        return None, VENDOR_INVALID_INPUT_BLOCKER
    if observed_at_kst.tzinfo is None:
        return None, VENDOR_BLOCKER
    return observed_at_kst.astimezone(KST), None


def _coerce_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_nullable_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value in {0, 1}:
            return bool(int(value))
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "y", "yes", "on"}:
            return True
        if text in {"false", "0", "n", "no", "off"}:
            return False
    return None


def _coerce_blockers(source_snapshot: dict[str, Any]) -> list[str]:
    raw_blockers = source_snapshot.get("blocked_reasons_json") or source_snapshot.get(
        "blockers"
    )
    blockers: list[str] = []
    if isinstance(raw_blockers, (list, tuple)):
        for item in raw_blockers:
            if isinstance(item, str) and item.strip():
                blockers.append(item.strip())
    elif isinstance(raw_blockers, str):
        text = raw_blockers.strip()
        if text:
            blockers.append(text)
    return blockers


def _derive_eligible_venues(
    *,
    krx_regular_eligible: bool | None,
    nxt_eligible: bool | None,
    krx_aftermarket_eligible: bool | None,
    listed_venues: Any,
) -> tuple[str, ...]:
    venues: list[str] = []
    listed = _coerce_venue_list(listed_venues)
    if listed:
        venues.extend(listed)
    else:
        if krx_regular_eligible is True or krx_aftermarket_eligible is True:
            venues.append(ACTUAL_EXECUTION_VENUE_KRX)
        if nxt_eligible is True:
            venues.append(ACTUAL_EXECUTION_VENUE_NXT)
    if krx_regular_eligible is False and nxt_eligible is False:
        venues = []
    # Normalize to deterministic ordering and dedupe.
    normalized: list[str] = []
    for venue in venues:
        upper = venue.upper()
        if upper in (ACTUAL_EXECUTION_VENUE_KRX, ACTUAL_EXECUTION_VENUE_NXT) and upper not in normalized:
            normalized.append(upper)
    if not normalized and (
        krx_regular_eligible is None and nxt_eligible is None and krx_aftermarket_eligible is None
    ):
        # Preserve explicit unknown state; caller should use quality/blockers to decide.
        pass
    return tuple(normalized)


def _coerce_venue_list(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []
    normalized = []
    for value in values:
        if not isinstance(value, str):
            continue
        value_upper = value.strip().upper()
        if value_upper in (ACTUAL_EXECUTION_VENUE_KRX, ACTUAL_EXECUTION_VENUE_NXT):
            if value_upper not in normalized:
                normalized.append(value_upper)
    return normalized


def _contract_version_for_date(target_date: date) -> str:
    return (
        MARKET_SESSION_CONTRACT_VERSION_V2
        if target_date >= MARKET_SESSION_EFFECTIVE_DATE
        else MARKET_SESSION_CONTRACT_VERSION_V1
    )


def _fallback_trade_date() -> date:
    return MARKET_SESSION_EFFECTIVE_DATE


def _invalid_market_session(
    observed_at_kst: datetime | None,
    trade_date: date,
    blocker: str,
) -> MarketSessionContext:
    fallback_observed_at = observed_at_kst or datetime(1970, 1, 1, tzinfo=KST)
    return MarketSessionContext(
        contract_version=MARKET_SESSION_CONTRACT_VERSION_V1,
        observed_at_kst=fallback_observed_at,
        trade_date=fallback_observed_at.date(),
        session_regime=MARKET_SESSION_REGIME_LEGACY_TRANSITION,
        open_venues=tuple(),
        decision_market_scope="UNKNOWN",
        preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
        entry_allowed_by_clock=False,
        exit_allowed_by_clock=False,
        source_quality=SOURCE_QUALITY_UNKNOWN,
        blocker=blocker,
    )


def _invalid_symbol_eligibility(
    stock_code: str,
    trade_date: date,
    blockers: tuple[str, ...],
) -> SymbolVenueEligibility:
    return SymbolVenueEligibility(
        trade_date=trade_date,
        stock_code=stock_code.strip() if stock_code else "",
        krx_regular_eligible=None,
        nxt_eligible=None,
        krx_aftermarket_eligible=None,
        eligible_venues=tuple(),
        source_id=stock_code.strip() if stock_code else "",
        source_sha256=None,
        observed_at_kst=None,
        quality_state=SOURCE_QUALITY_UNKNOWN,
        blockers=tuple(_dedupe_strings(blockers)),
    )


def _dedupe_strings(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in seen:
            seen.append(text)
    return tuple(seen)


def _resolve_legacy_session(
    observed_at_kst: datetime, contract_version: str
) -> MarketSessionContext:
    clock = observed_at_kst.time()
    if dt_time(8, 0) <= clock < dt_time(9, 0):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_LEGACY_PREMARKET,
            open_venues=("KRX",),
            decision_market_scope="KRX",
            preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
            entry_allowed_by_clock=False,
            exit_allowed_by_clock=False,
            source_quality=SOURCE_QUALITY_PARTIAL,
            blocker=None,
        )

    if dt_time(9, 0) <= clock < dt_time(15, 30):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_LEGACY_KRX_ONLY,
            open_venues=(ACTUAL_EXECUTION_VENUE_KRX,),
            decision_market_scope="KRX",
            preferred_market_data_route=MARKET_DATA_ROUTE_KRX_ONLY,
            entry_allowed_by_clock=True,
            exit_allowed_by_clock=True,
            source_quality=SOURCE_QUALITY_VALID,
            blocker=None,
        )

    if dt_time(16, 0) <= clock < dt_time(20, 0):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_LEGACY_NXT_ONLY,
            open_venues=(ACTUAL_EXECUTION_VENUE_NXT,),
            decision_market_scope="NXT",
            preferred_market_data_route=MARKET_DATA_ROUTE_NXT_ONLY,
            entry_allowed_by_clock=True,
            exit_allowed_by_clock=True,
            source_quality=SOURCE_QUALITY_VALID,
            blocker=None,
        )

    if dt_time(15, 30) <= clock < dt_time(16, 0):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_LEGACY_TRANSITION,
            open_venues=tuple(),
            decision_market_scope="NXT",
            preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
            entry_allowed_by_clock=False,
            exit_allowed_by_clock=False,
            source_quality=SOURCE_QUALITY_PARTIAL,
            blocker=VENDOR_LEGACY_UNSUPPORTED_TIME_BLOCKER,
        )

    return MarketSessionContext(
        contract_version=contract_version,
        observed_at_kst=observed_at_kst,
        trade_date=observed_at_kst.date(),
        session_regime=MARKET_SESSION_REGIME_CLOSED,
        open_venues=tuple(),
        decision_market_scope="UNKNOWN",
        preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
        entry_allowed_by_clock=False,
        exit_allowed_by_clock=False,
        source_quality=SOURCE_QUALITY_PARTIAL,
        blocker=None,
    )


def _resolve_post_effective_session(
    observed_at_kst: datetime, contract_version: str
) -> MarketSessionContext:
    clock = observed_at_kst.time()
    if dt_time(8, 0) <= clock < dt_time(9, 0):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_LEGACY_PREMARKET,
            open_venues=(ACTUAL_EXECUTION_VENUE_KRX,),
            decision_market_scope="KRX",
            preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
            entry_allowed_by_clock=False,
            exit_allowed_by_clock=False,
            source_quality=SOURCE_QUALITY_PARTIAL,
            blocker=None,
        )
    if dt_time(9, 0) <= clock < dt_time(15, 30):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_KRX_REGULAR,
            open_venues=(ACTUAL_EXECUTION_VENUE_KRX,),
            decision_market_scope="KRX",
            preferred_market_data_route=MARKET_DATA_ROUTE_KRX_ONLY,
            entry_allowed_by_clock=True,
            exit_allowed_by_clock=True,
            source_quality=SOURCE_QUALITY_VALID,
            blocker=None,
        )
    if dt_time(15, 30) <= clock < dt_time(16, 0):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_SESSION_TRANSITION,
            open_venues=tuple(),
            decision_market_scope="KRX_NXT_TRANSITION",
            preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
            entry_allowed_by_clock=False,
            exit_allowed_by_clock=False,
            source_quality=SOURCE_QUALITY_PARTIAL,
            blocker=None,
        )
    if dt_time(16, 0) <= clock < dt_time(19, 40):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
            open_venues=(ACTUAL_EXECUTION_VENUE_KRX, ACTUAL_EXECUTION_VENUE_NXT),
            decision_market_scope="KRX_NXT",
            preferred_market_data_route=MARKET_DATA_ROUTE_KRX_NXT_INTEGRATED,
            entry_allowed_by_clock=True,
            exit_allowed_by_clock=True,
            source_quality=SOURCE_QUALITY_VALID,
            blocker=None,
        )
    if dt_time(19, 40) <= clock < dt_time(19, 45):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY,
            open_venues=(ACTUAL_EXECUTION_VENUE_KRX, ACTUAL_EXECUTION_VENUE_NXT),
            decision_market_scope="KRX_NXT",
            preferred_market_data_route=MARKET_DATA_ROUTE_KRX_NXT_INTEGRATED,
            entry_allowed_by_clock=False,
            exit_allowed_by_clock=True,
            source_quality=SOURCE_QUALITY_VALID,
            blocker=None,
        )
    if dt_time(19, 45) <= clock < dt_time(20, 0):
        return MarketSessionContext(
            contract_version=contract_version,
            observed_at_kst=observed_at_kst,
            trade_date=observed_at_kst.date(),
            session_regime=MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_TERMINAL_EXIT,
            open_venues=(ACTUAL_EXECUTION_VENUE_KRX, ACTUAL_EXECUTION_VENUE_NXT),
            decision_market_scope="KRX_NXT",
            preferred_market_data_route=MARKET_DATA_ROUTE_KRX_NXT_INTEGRATED,
            entry_allowed_by_clock=False,
            exit_allowed_by_clock=True,
            source_quality=SOURCE_QUALITY_VALID,
            blocker=None,
        )
    return MarketSessionContext(
        contract_version=contract_version,
        observed_at_kst=observed_at_kst,
        trade_date=observed_at_kst.date(),
        session_regime=MARKET_SESSION_REGIME_CLOSED,
        open_venues=tuple(),
        decision_market_scope="UNKNOWN",
        preferred_market_data_route=MARKET_DATA_ROUTE_UNKNOWN,
        entry_allowed_by_clock=False,
        exit_allowed_by_clock=False,
        source_quality=SOURCE_QUALITY_PARTIAL,
        blocker=None,
    )
