"""Operator venue assignment for integrated SOR fills, separate from broker fact.

This market attribution boundary never selects an order or quote route. Native
broker provenance remains unresolved when Kiwoom reports only integrated SOR.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

SOR_KRX_AUTHORITY = "user_2026_10_16_sor_execution_venue_krx"
SOR_KRX_EFFECTIVE_DATE = "2026-10-16"


def execution_venue_fields(source, *, observed_at=None):
    """Assign unresolved native SOR fills to KRX from the operator's date."""
    broker = str(source.get("broker_actual_execution_venue")
                 or source.get("actual_execution_venue") or "UNKNOWN").upper()
    broker_source = str(source.get("broker_actual_execution_venue_source")
                        or source.get("actual_execution_venue_source")
                        or "official_exchange_fields_ambiguous_or_missing")
    # An explicit exchange reported by the broker takes precedence. A route
    # alone, a stale prior assignment or a conflicting packet cannot assign it.
    if broker in {"KRX", "NXT"}:
        return dict(actual_execution_venue=broker,
                    actual_execution_venue_source=broker_source,
                    actual_execution_venue_verified=broker_source == "official_fid_2134_2135",
                    execution_venue_override=None)
    at = observed_at or source.get("broker_execution_observed_at")
    try:
        at = at if isinstance(at, datetime) else datetime.fromisoformat(str(at))
        day = at.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat() if at.tzinfo else ""
    except (ValueError, TypeError):
        day = ""
    integrated = (str(source.get("broker_actual_exchange_code") or "") == "0"
                  and str(source.get("broker_actual_exchange_name") or "").upper() in {"SOR", "통합"}
                  and str(source.get("broker_sor_flag") or "").upper() == "Y")
    assigned = (integrated and broker in {"", "UNKNOWN"}
                and broker_source == "official_exchange_fields_ambiguous_or_missing"
                and day >= SOR_KRX_EFFECTIVE_DATE)
    return dict(actual_execution_venue="KRX" if assigned else "UNKNOWN",
                actual_execution_venue_source=SOR_KRX_AUTHORITY if assigned else broker_source,
                actual_execution_venue_verified=False,
                execution_venue_override=SOR_KRX_AUTHORITY if assigned else None)
