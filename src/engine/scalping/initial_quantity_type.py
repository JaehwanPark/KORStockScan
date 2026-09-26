"""Decision-time, source-bound classification for initial scalp quantity."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.order.tick_utils import get_tick_size

KST = ZoneInfo("Asia/Seoul")
CLASSIFIER_VERSION = "initial_quantity_type_v1"
QUANTITY_TYPES = (
    "SAFE_UNKNOWN", "KRX_THIN_HIGH_TICK", "KRX_LIQUID_FLOW_SUPPORT",
    "KRX_LIQUID_FLOW_ADVERSE", "KRX_VOLATILE_EXTENSION", "KRX_PARENT",
)


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def kst_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)


def classify_quantity_type(fields: dict[str, Any]) -> str:
    """Classify only predecision fields; stale or mismatched features are ignored."""
    from src.engine.scalping.position_sizing_allocator import normalize_source_tokens

    venue = str(fields.get("effective_venue") or "").upper()
    source_tokens = normalize_source_tokens(fields.get("source_signature"))
    decision_at = kst_timestamp(fields.get("reference_time") or fields.get("emitted_at"))
    session = str(fields.get("market_session_bucket") or "").lower()
    if venue != "KRX" or not source_tokens or decision_at is None:
        return "SAFE_UNKNOWN"
    if not (session == "krx_regular" or session.startswith("krx_regular_")):
        return "KRX_PARENT"
    price = finite_number(fields.get("price_krw") or fields.get("current_price")
                          or fields.get("latest_price"))
    tick_bps = 10000.0 * get_tick_size(price) / price if price and price > 0 else None
    feature_at = kst_timestamp(fields.get("feature_snapshot_at"))
    decision_route = str(fields.get("classifier_route_key") or "")
    decision_epoch = str(fields.get("classifier_transport_epoch") or "")
    feature_verified = bool(
        feature_at is not None
        and 0 <= (decision_at - feature_at).total_seconds() <= 1
        and decision_route and decision_epoch
        and str(fields.get("feature_route_key") or "") == decision_route
        and str(fields.get("feature_transport_epoch") or "") == decision_epoch
    )
    liquidity = str(fields.get("liquidity_band") or "UNKNOWN").upper() if feature_verified else "UNKNOWN"
    volatility = str(fields.get("volatility_band") or "UNKNOWN").upper() if feature_verified else "UNKNOWN"
    if (tick_bps is not None and tick_bps >= 10.0) or liquidity == "FRAGILE":
        return "KRX_THIN_HIGH_TICK"
    if volatility == "HIGH" or (feature_verified and fields.get("extension_band") == "GE_1PCT"):
        return "KRX_VOLATILE_EXTENSION"
    flow = str(fields.get("trusted_flow_state") or "UNKNOWN").upper()
    if feature_verified and fields.get("trusted_flow_fresh") is True and liquidity == "SUPPORTIVE":
        if flow == "BUY_DOMINANT" and tick_bps is not None and tick_bps < 10.0:
            return "KRX_LIQUID_FLOW_SUPPORT"
        if flow == "SELL_DOMINANT":
            return "KRX_LIQUID_FLOW_ADVERSE"
    return "KRX_PARENT"


def type_from_decision_receipt(fields: dict[str, Any], *, decision_at: datetime,
                               entry_at: datetime) -> str:
    receipt_type = str(fields.get("quantity_type") or fields.get("scalping_sizing_quantity_type") or "")
    receipt_version = str(fields.get("quantity_type_classifier_version")
                          or fields.get("scalping_sizing_quantity_type_classifier_version") or "")
    reference_at = kst_timestamp(fields.get("reference_time"))
    if decision_at > entry_at or reference_at is not None and reference_at > entry_at:
        return "SAFE_UNKNOWN"
    if receipt_version == CLASSIFIER_VERSION and receipt_type in QUANTITY_TYPES:
        return receipt_type
    return classify_quantity_type(fields)
