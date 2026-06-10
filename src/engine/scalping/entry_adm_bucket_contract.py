from __future__ import annotations

from datetime import datetime
from typing import Any


ENTRY_ADM_BUCKET_SCHEMA_VERSION = "entry_adm_bucket_v2"

ENTRY_ADM_BUCKET_DIMENSIONS = (
    "score_bucket",
    "risk_context_bucket",
    "market_regime_continuous_bucket",
    "stale_bucket",
    "price_resolution_bucket",
    "liquidity_bucket",
    "overbought_bucket",
    "time_bucket",
)


def entry_adm_time_bucket(value: Any) -> str:
    raw = str(value or "").strip()
    hour = -1
    try:
        hour = datetime.fromisoformat(raw).hour
    except Exception:
        if len(raw) >= 2 and raw[:2].isdigit() and not raw.startswith("20"):
            hour = int(raw[:2])
    if hour < 0:
        return "time_unknown"
    if hour < 10:
        return "time_0900_1000"
    if hour < 12:
        return "time_1000_1200"
    if hour < 14:
        return "time_1200_1400"
    return "time_1400_close"


def entry_adm_market_regime_continuous_bucket(
    *,
    bucket: Any = None,
    label: Any = None,
    score: Any = None,
) -> str:
    raw = str(bucket or "").strip()
    if raw:
        return raw
    normalized_label = str(label or "").strip().upper()
    if normalized_label in {"RISK_ON", "NEUTRAL", "RISK_OFF"}:
        return f"market_regime_{normalized_label.lower()}"
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return "-"
    if numeric_score >= 65:
        return "market_regime_risk_on"
    if numeric_score >= 45:
        return "market_regime_neutral"
    return "market_regime_risk_off"


def entry_adm_bucket_token(row: dict[str, Any]) -> str:
    return "|".join(str(row.get(key) or "-") for key in ENTRY_ADM_BUCKET_DIMENSIONS)
