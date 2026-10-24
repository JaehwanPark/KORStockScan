"""Operator market defaults, separate from native venue and quote proof."""
from datetime import datetime
from zoneinfo import ZoneInfo

SOR_KRX_AUTHORITY = "user_2026_10_16_sor_execution_venue_krx"
SOR_KRX_EFFECTIVE_DATE = "2026-10-16"
MARKET_DEFAULT_AUTHORITY = "user_2026_10_21_unresolved_venue_krx_route_sor"
MARKET_DEFAULT_EFFECTIVE_DATE = "2026-10-21"
VENUE_ASSIGNMENT_AUTHORITIES = frozenset({SOR_KRX_AUTHORITY, MARKET_DEFAULT_AUTHORITY})
UNRESOLVED_MARKET_VALUES = frozenset({"", "-", "UNKNOWN", "NONE", "NULL", "AUTO", "NOT_AVAILABLE"})


def market_defaults_active(observed_at):
    """Use the event date, never the replay process clock, for attribution."""
    try:
        at = observed_at if isinstance(observed_at, datetime) else datetime.fromisoformat(str(observed_at))
        return bool(at.tzinfo and at.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
                    >= MARKET_DEFAULT_EFFECTIVE_DATE)
    except (TypeError, ValueError):
        return False


def operational_venue(value, *, observed_at):
    """Default an unresolved operating cohort; conflicts remain invalid."""
    venue = str(value or "").strip().upper()
    if venue in {"KRX", "NXT"}:
        return venue
    if venue in UNRESOLVED_MARKET_VALUES and market_defaults_active(observed_at):
        return "KRX"
    return "UNKNOWN"


def broker_route_fields(value, *, observed_at, recorded=None):
    """Resolve a requested route without claiming a historical transmission."""
    raw = str(value or "").strip().upper()
    if (raw == "SOR" and isinstance(recorded, dict)
            and recorded.get("broker_route_override") == MARKET_DEFAULT_AUTHORITY
            and str(recorded.get("broker_route_requested_raw") or "").strip().upper()
                in UNRESOLVED_MARKET_VALUES):
        raw = str(recorded.get("broker_route_requested_raw") or "").strip().upper()
    assigned = raw in UNRESOLVED_MARKET_VALUES and market_defaults_active(observed_at)
    return {
        "broker_route_requested": "SOR" if assigned else raw or "UNKNOWN",
        "broker_route_requested_raw": raw or "UNKNOWN",
        "broker_route_override": MARKET_DEFAULT_AUTHORITY if assigned else None,
    }


def execution_venue_fields(source, *, observed_at=None):
    """Assign an operating venue while retaining unverified broker truth."""
    broker = str(source.get("broker_actual_execution_venue")
                 or source.get("actual_execution_venue") or "UNKNOWN").upper()
    broker_source = str(source.get("broker_actual_execution_venue_source")
                        or source.get("actual_execution_venue_source")
                        or "official_exchange_fields_ambiguous_or_missing")
    at = observed_at or source.get("broker_execution_observed_at")
    try:
        at = at if isinstance(at, datetime) else datetime.fromisoformat(str(at))
        day = at.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat() if at.tzinfo else ""
    except (ValueError, TypeError):
        day = ""
    # An explicit exchange reported by the broker takes precedence. A route
    # alone, a stale prior assignment or a conflicting packet cannot assign it.
    if broker in {"KRX", "NXT"}:
        override = (broker_source if broker_source in VENUE_ASSIGNMENT_AUTHORITIES
                    and source.get("execution_venue_override") == broker_source
                    and day >= (SOR_KRX_EFFECTIVE_DATE if broker_source == SOR_KRX_AUTHORITY
                                else MARKET_DEFAULT_EFFECTIVE_DATE)
                    and broker == "KRX" else None)
        return dict(actual_execution_venue=broker,
                    actual_execution_venue_source=broker_source,
                    actual_execution_venue_verified=broker_source == "official_fid_2134_2135",
                    execution_venue_override=override)
    integrated = (str(source.get("broker_actual_exchange_code") or "") == "0"
                  and str(source.get("broker_actual_exchange_name") or "").upper() in {"SOR", "통합"}
                  and str(source.get("broker_sor_flag") or "").upper() == "Y")
    assigned = (integrated and broker in {"", "UNKNOWN"}
                and broker_source == "official_exchange_fields_ambiguous_or_missing"
                and day >= SOR_KRX_EFFECTIVE_DATE)
    authority = SOR_KRX_AUTHORITY if assigned else None
    if (broker in UNRESOLVED_MARKET_VALUES
            and market_defaults_active(at)
            and broker_source in {"official_exchange_fields_ambiguous_or_missing", *VENUE_ASSIGNMENT_AUTHORITIES}
            and str(source.get("broker_actual_exchange_code") or "").upper() not in {"2", "NXT"}
            and str(source.get("broker_actual_exchange_name") or "").upper() != "NXT"):
        authority = (SOR_KRX_AUTHORITY if assigned and source.get("execution_venue_override")
                     == SOR_KRX_AUTHORITY else MARKET_DEFAULT_AUTHORITY)
    return dict(actual_execution_venue="KRX" if authority else "UNKNOWN",
                actual_execution_venue_source=authority or broker_source,
                actual_execution_venue_verified=False,
                execution_venue_override=authority)
