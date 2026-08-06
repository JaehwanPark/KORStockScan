"""Read-only Hanwha Ocean advisory endpoint backed by the AWS snapshot."""

from __future__ import annotations

import hmac
import os
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, jsonify, request

from src.engine.monitoring import hanwha_ocean_widget_contract as contract
from src.engine.monitoring.samsung_widget_advisory import (
    KiwoomReadOnlyClient,
    _positive_int,
)
from src.engine.monitoring.samsung_widget_contract import (
    ADVISORY_AUTHORITY,
    KST,
    snapshot_observed_at,
)
from src.engine.sniper_config import CONF
from src.utils import kiwoom_utils

hanwha_ocean_price_widget_bp = Blueprint("hanwha_ocean_price_widget", __name__)

_ACCESS_KEY_ENV = "KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_ACCESS_KEY"
_SHARED_ACCESS_KEY_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY"
_ACCESS_KEY_FILE_ENV = "KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_ACCESS_KEY_FILE"
_SHARED_ACCESS_KEY_FILE_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE"
_ACCESS_KEY_HEADER = "X-KORStockScan-Widget-Key"
_SNAPSHOT_PATH_ENV = "KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_SNAPSHOT_PATH"


def _now_kst() -> datetime:
    return datetime.now(KST)


def _read_key_file(path_value: str) -> str:
    if not path_value:
        return ""
    try:
        return Path(path_value).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _widget_access_key() -> str:
    direct = os.getenv(_ACCESS_KEY_ENV, "").strip()
    if direct:
        return direct
    dedicated_file = _read_key_file(os.getenv(_ACCESS_KEY_FILE_ENV, "").strip())
    if dedicated_file:
        return dedicated_file
    shared_direct = os.getenv(_SHARED_ACCESS_KEY_ENV, "").strip()
    if shared_direct:
        return shared_direct
    return _read_key_file(os.getenv(_SHARED_ACCESS_KEY_FILE_ENV, "").strip())


def _authorized_request() -> bool:
    expected = _widget_access_key()
    supplied = request.headers.get(_ACCESS_KEY_HEADER, "").strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def _snapshot_path() -> Path:
    configured = os.getenv(_SNAPSHOT_PATH_ENV, "").strip()
    return Path(configured) if configured else contract.DEFAULT_SNAPSHOT_PATH


def _response(payload: dict, status_code: int = 200):
    result = jsonify(payload)
    result.status_code = status_code
    result.headers["Cache-Control"] = "no-store"
    return result


def _fresh_snapshot(observed_at: datetime) -> dict | None:
    payload = contract.load_snapshot(_snapshot_path())
    if not contract.snapshot_is_fresh(payload, now=observed_at, require_ok=False):
        return None
    if (
        payload.get("schema_version") != contract.SNAPSHOT_SCHEMA_VERSION
        or payload.get("symbol") != contract.HANWHA_OCEAN_CODE
        or (
            payload.get("status") == "ok"
            and _positive_int(payload.get("current_price")) is None
        )
        or payload.get("token_mode") != "shared_cache_only"
        or payload.get("quote_request_code") != contract.HANWHA_OCEAN_CODE
        or payload.get("market_venue") != "KRX"
        or payload.get("market_cohort") != "KRX"
        or payload.get("strategy_profile") != contract.STRATEGY_PROFILE
    ):
        return None
    result = deepcopy(payload)
    if payload.get("status") == "closed":
        result["entry_event"] = None
        result["exit_event"] = None
        return result
    context = contract.session_context(observed_at)
    persisted = snapshot_observed_at(payload)
    if not context.active or persisted is None:
        return None
    if not contract.advisory_contract_is_valid(
        payload.get("advisory"),
        snapshot_time=persisted,
        context=context,
        evaluated_at=observed_at,
    ):
        return None
    if not contract.exit_advisory_contract_is_valid(
        payload.get("exit_advisory"),
        snapshot_time=persisted,
        context=context,
        evaluated_at=observed_at,
    ):
        return None
    for key, expected_type in (("entry_event", "ENTRY"), ("exit_event", "EXIT")):
        event = result.get(key)
        if event is not None and not contract.advisory_event_contract_is_valid(
            event, expected_type=expected_type, evaluated_at=observed_at
        ):
            result[key] = None
    return result


def _fallback_advisory(observed_at: datetime, reason: str) -> dict:
    valid_until = (observed_at + timedelta(seconds=20)).isoformat()
    return {
        "state": "DATA_WAIT",
        "raw_state": "DATA_WAIT",
        "session": contract.session_context(observed_at).name,
        "entry_price_low": None,
        "entry_price_high": None,
        "reasons": [],
        "unmet_conditions": [reason],
        "observed_at": observed_at.isoformat(),
        "valid_until": valid_until,
        "source_quality": {"status": "BLOCKED", "issues": [reason]},
        "strategy_profile": contract.STRATEGY_PROFILE,
        "authority": ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": contract.METRIC_CONTRACT,
    }


@hanwha_ocean_price_widget_bp.get("/api/widget/hanwha-ocean-price")
def get_hanwha_ocean_price():
    """Return a fresh advisory snapshot or a quote-only safe fallback."""
    if not _authorized_request():
        return _response(
            {
                "status": "unavailable",
                "reason": "unauthorized",
                "token_mode": "shared_cache_only",
            },
            401,
        )
    observed_at = _now_kst()
    snapshot = _fresh_snapshot(observed_at)
    if snapshot is not None:
        return _response(snapshot)

    token = kiwoom_utils.get_cached_kiwoom_token(CONF)
    if not token:
        return _response(
            {
                "status": "unavailable",
                "reason": "shared_token_unavailable",
                "token_mode": "shared_cache_only",
            },
            503,
        )
    try:
        quote = KiwoomReadOnlyClient(token).post(
            "/api/dostk/stkinfo",
            "ka10001",
            {"stk_cd": contract.HANWHA_OCEAN_CODE},
        )
    except Exception:
        return _response(
            {
                "status": "unavailable",
                "reason": "kiwoom_quote_rejected",
                "token_mode": "shared_cache_only",
            },
            503,
        )
    current_price = _positive_int(quote.get("cur_prc"))
    if current_price is None:
        return _response(
            {
                "status": "unavailable",
                "reason": "kiwoom_price_missing",
                "token_mode": "shared_cache_only",
            },
            503,
        )
    advisory = _fallback_advisory(observed_at, "collector_snapshot_missing_or_stale")
    return _response(
        {
            "schema_version": contract.SNAPSHOT_SCHEMA_VERSION,
            "status": "ok",
            "symbol": contract.HANWHA_OCEAN_CODE,
            "name": contract.HANWHA_OCEAN_NAME,
            "current_price": current_price,
            "day_low_price": _positive_int(quote.get("low_pric")),
            "observed_at_kst": observed_at.isoformat(),
            "market_venue": "KRX",
            "market_cohort": "KRX",
            "market_session": "quote_only",
            "quote_request_code": contract.HANWHA_OCEAN_CODE,
            "source": "kiwoom_ka10001_krx_quote_only_fallback",
            "token_mode": "shared_cache_only",
            "strategy_profile": contract.STRATEGY_PROFILE,
            "advisory": advisory,
            "exit_advisory": {
                **advisory,
                "reference_exit_price": None,
                "holding_independent": True,
                "future_prediction": False,
            },
            "entry_event": None,
            "exit_event": None,
        }
    )
