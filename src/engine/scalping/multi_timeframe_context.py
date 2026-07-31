"""Shared completed-bar context for scalping AI decision stages.

The bundle supplies inputs only.  It has no standalone action, order, provider,
threshold, or safety authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.scalping.market_context_observation import (
    derive_scalping_market_features,
)

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "scalping_multi_timeframe_context_v1"
SOURCE_BAR_LIMIT = 430
MODEL_MULTI_TIMEFRAME_BAR_LIMIT = 20
REPO_ROOT = Path(__file__).resolve().parents[3]
PROMOTION_DIR = REPO_ROOT / "data" / "runtime"
RUNTIME_ENV_DIR = REPO_ROOT / "data" / "threshold_cycle" / "runtime_env"
PROMOTION_SCHEMA = "ai_multi_timeframe_context_promotion_v1"
PROMOTION_AUTHORITY_ID = "operator_full_market_context_promotion_2026-07-27"
OPERATOR_DIRECTED_PROMOTION_MODE = "operator_directed_full_promotion"
OPERATOR_DIRECTED_AUTHORITY_PREFIX = "operator_directed_full_promotion_"
PROMOTION_ARTIFACT_REQUIRED_FROM_DATE = "2026-07-27"

INPUT_CONTRACT = {
    "metric_role": "ai_input_feature_bundle",
    "decision_authority": "stage_context_input_only_no_standalone_action",
    "window_policy": "exact_timestamp_venue_session_completed_bar",
    "sample_floor": "field_specific_completed_bar_and_source_availability",
    "primary_decision_metric": "required_source_field_availability",
    "source_quality_gate": "fresh_same_basis_conflict_free",
    "runtime_effect": False,
    "standalone_runtime_effect": False,
    "live_payload_inclusion": "promotion_gated_binary_full_market",
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "live_promotion_gate": (
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED_full_market_only"
    ),
    "forbidden_uses": [
        "standalone_buy_hold_exit_authority",
        "runtime_threshold_apply",
        "order_price_or_quantity_decision",
        "provider_route_change",
        "broker_or_safety_guard_bypass",
    ],
}
_PREVIOUS_DAY_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_PREVIOUS_DAY_CACHE_LOCK = threading.Lock()
_PREVIOUS_DAY_CACHE_TTL_SEC = 21_600.0
_PROMOTION_CACHE_LOCK = threading.Lock()
_PROMOTION_CACHE: dict[str, tuple[int, int, dict[str, Any]]] = {}
_ACTIVATION_CACHE_LOCK = threading.Lock()
_ACTIVATION_CACHE: dict[str, tuple[tuple[Any, ...], dict[str, Any]]] = {}


def _operator_directed_exact_v2_env_readback(
    target_date: str,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether this PID actually loaded the complete direct-promotion env.

    An operator-directed marker is an authorization artifact, not a mechanism for
    changing an already-running process environment.  Requiring this readback
    prevents a baseline process from picking up only the marker and then mixing
    baseline preflight with Exact V2 context.
    """

    required = {
        "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE": "exact_v2",
        "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED": "true",
        "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE": target_date,
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_PREMARKET_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_KRX_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_NXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_PREMARKET_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_KRX_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_NXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_SCORE_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_FLOW_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_OVERNIGHT_CONTEXT_ENABLED": "true",
    }
    missing = tuple(
        name
        for name, expected in required.items()
        if str(os.getenv(name, "")).strip().lower() != expected.lower()
    )
    return not missing, missing


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


def _promotion_artifact(target_date: str) -> dict[str, Any]:
    path = PROMOTION_DIR / f"ai_multi_timeframe_context_promotion_{target_date}.json"
    try:
        stat = path.stat()
    except OSError:
        return {}
    cache_key = str(path)
    with _PROMOTION_CACHE_LOCK:
        cached = _PROMOTION_CACHE.get(cache_key)
        if cached and cached[:2] == (stat.st_mtime_ns, stat.st_size):
            return dict(cached[2])
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    artifact = value if isinstance(value, dict) else {}
    with _PROMOTION_CACHE_LOCK:
        _PROMOTION_CACHE[cache_key] = (stat.st_mtime_ns, stat.st_size, artifact)
    return dict(artifact)


def _latest_promotion_artifact(
    target_date: str,
) -> tuple[str, dict[str, Any]]:
    candidates: list[str] = []
    for path in PROMOTION_DIR.glob("ai_multi_timeframe_context_promotion_*.json"):
        artifact_date = path.stem.removeprefix("ai_multi_timeframe_context_promotion_")
        try:
            datetime.strptime(artifact_date, "%Y-%m-%d")
        except ValueError:
            continue
        if artifact_date <= target_date:
            candidates.append(artifact_date)
    for artifact_date in sorted(set(candidates), reverse=True):
        artifact = _promotion_artifact(artifact_date)
        if artifact:
            return artifact_date, artifact
    return "", {}


def _parse_promotion_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _activation_state_at_capture(
    state: dict[str, Any],
    captured_at: datetime,
) -> dict[str, Any]:
    resolved = dict(state)
    promoted_at = _parse_promotion_ts(resolved.get("promoted_at"))
    capture = (
        captured_at.replace(tzinfo=KST)
        if captured_at.tzinfo is None
        else captured_at.astimezone(KST)
    )
    if resolved.get("active") and (promoted_at is None or capture < promoted_at):
        resolved.update(
            {
                "active": False,
                "activation_source": "promotion_not_effective_at_capture",
            }
        )
    return resolved


def promotion_activation_state(captured_at: datetime) -> dict[str, Any]:
    """Resolve the fail-closed env or atomic promotion-marker activation state."""

    capture = (
        captured_at.replace(tzinfo=KST)
        if captured_at.tzinfo is None
        else captured_at.astimezone(KST)
    )
    target_date = capture.date().isoformat()
    promotion_artifact_required = target_date >= PROMOTION_ARTIFACT_REQUIRED_FROM_DATE
    enabled = str(
        os.getenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED", "false")
    ).strip().lower() in {"1", "true", "yes", "on"}
    active_date = str(
        os.getenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE", "")
    ).strip()
    env_date_allowed = not active_date or target_date >= active_date
    if enabled and env_date_allowed and not promotion_artifact_required:
        return {
            "active": True,
            "activation_source": "process_env",
            "target_date": active_date or target_date,
            "promotion_artifact": None,
            "promotion_artifact_required": False,
        }
    promotion_target_date, artifact = _latest_promotion_artifact(target_date)
    promotion_mode = str(artifact.get("promotion_mode") or "")
    validated_authority = (
        promotion_mode in {"", "validated_premarket_full_promotion"}
        and artifact.get("operator_authorization_id") == PROMOTION_AUTHORITY_ID
    )
    operator_directed_authority = (
        promotion_mode == OPERATOR_DIRECTED_PROMOTION_MODE
        and artifact.get("operator_authorization_id")
        == f"{OPERATOR_DIRECTED_AUTHORITY_PREFIX}{promotion_target_date}"
        and isinstance(artifact.get("validation_gate"), dict)
        and artifact["validation_gate"].get("mode") == "operator_directed_bypass"
        and artifact["validation_gate"].get("bypassed") is True
        and bool(str(artifact["validation_gate"].get("operator_reason") or "").strip())
    )
    if (
        artifact.get("schema") != PROMOTION_SCHEMA
        or artifact.get("decision") != "promoted_all_market_sessions_full"
        or artifact.get("runtime_activation") is not True
        or artifact.get("transaction_status") != "committed"
        or not (validated_authority or operator_directed_authority)
        or str(artifact.get("target_date") or "") != promotion_target_date
    ):
        return {
            "active": False,
            "activation_source": (
                "promotion_artifact_required_missing_or_invalid"
                if promotion_artifact_required
                else "none"
            ),
            "target_date": target_date,
            "promotion_artifact": None,
            "promotion_artifact_required": promotion_artifact_required,
        }
    artifact_path = (
        PROMOTION_DIR
        / f"ai_multi_timeframe_context_promotion_{promotion_target_date}.json"
    )
    env_path = RUNTIME_ENV_DIR / f"threshold_runtime_env_{promotion_target_date}.env"
    manifest_path = (
        RUNTIME_ENV_DIR / f"threshold_runtime_env_{promotion_target_date}.json"
    )
    if artifact.get("runtime_env_path") not in (None, str(env_path)) or artifact.get(
        "runtime_manifest_path"
    ) not in (None, str(manifest_path)):
        return {
            "active": False,
            "activation_source": "promotion_artifact_path_mismatch",
            "target_date": target_date,
            "promotion_artifact": str(artifact_path),
            "promotion_target_date": promotion_target_date,
            "promotion_artifact_required": promotion_artifact_required,
        }
    signature = tuple(
        _file_signature(path) for path in (artifact_path, env_path, manifest_path)
    ) + (
        (
            _operator_directed_exact_v2_env_readback(target_date)
            if operator_directed_authority
            else (True, ())
        ),
    )
    with _ACTIVATION_CACHE_LOCK:
        cached = _ACTIVATION_CACHE.get(target_date)
        if cached and cached[0] == signature:
            return _activation_state_at_capture(cached[1], capture)
    try:
        hash_ok = _file_sha256(env_path) == artifact.get(
            "runtime_env_sha256"
        ) and _file_sha256(manifest_path) == artifact.get("runtime_manifest_sha256")
    except OSError:
        hash_ok = False
    if not hash_ok:
        state = {
            "active": False,
            "activation_source": "promotion_artifact_hash_mismatch",
            "target_date": target_date,
            "promotion_artifact": str(artifact_path),
            "promotion_target_date": promotion_target_date,
            "promotion_artifact_required": promotion_artifact_required,
        }
    elif operator_directed_authority:
        runtime_env_loaded, missing_env = _operator_directed_exact_v2_env_readback(
            target_date
        )
        if not runtime_env_loaded:
            state = {
                "active": False,
                "activation_source": "operator_directed_runtime_env_not_loaded",
                "target_date": target_date,
                "promotion_artifact": str(artifact_path),
                "promotion_target_date": promotion_target_date,
                "promotion_artifact_required": promotion_artifact_required,
                "promotion_mode": promotion_mode,
                "missing_runtime_env": list(missing_env),
            }
        else:
            state = {
                "active": True,
                "activation_source": "atomic_promotion_artifact",
                "target_date": target_date,
                "promotion_artifact": str(artifact_path),
                "promotion_target_date": promotion_target_date,
                "promotion_artifact_required": promotion_artifact_required,
                "promotion_sha256": _file_sha256(artifact_path),
                "promoted_at": artifact.get("promoted_at"),
                "promotion_mode": promotion_mode,
                "promotion_rollover": promotion_target_date != target_date,
                "runtime_env_readback": "complete_exact_v2",
            }
    else:
        state = {
            "active": True,
            "activation_source": "atomic_promotion_artifact",
            "target_date": target_date,
            "promotion_artifact": str(artifact_path),
            "promotion_target_date": promotion_target_date,
            "promotion_artifact_required": promotion_artifact_required,
            "promotion_sha256": _file_sha256(artifact_path),
            "promoted_at": artifact.get("promoted_at"),
            "promotion_mode": promotion_mode or "validated_premarket_full_promotion",
        }
    with _ACTIVATION_CACHE_LOCK:
        _ACTIVATION_CACHE[target_date] = (signature, state)
    return _activation_state_at_capture(state, capture)


def full_market_promotion_active(captured_at: datetime) -> bool:
    return bool(promotion_activation_state(captured_at).get("active"))


def multi_timeframe_ai_input_enabled(captured_at: datetime) -> bool:
    """Return the single global post-validation promotion state."""

    return full_market_promotion_active(captured_at)


def _clean_code(code: str) -> str:
    raw = str(code or "").strip().upper()
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            raw = raw[:-3]
    if raw.startswith("A"):
        raw = raw[1:]
    digits = "".join(char for char in raw if char.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def _daily_request_code(code: str, venue: str) -> tuple[str, str]:
    base = _clean_code(code)
    venue_upper = str(venue or "").upper()
    if venue_upper in {"NXT", "PREMARKET_KRX_LIKE"}:
        return f"{base}_NX", "NXT"
    return base, "KRX"


def _explicit_index_code(ws_data: dict[str, Any], *, sector: bool) -> str:
    keys = (
        ("sector_index_code", "sector_inds_cd", "industry_index_code")
        if sector
        else ("market_index_code", "market_inds_cd")
    )
    for key in keys:
        value = str(ws_data.get(key) or "").strip()
        if value:
            return value
    if sector:
        return ""
    market = str(
        ws_data.get("market_type")
        or ws_data.get("mrkt_tp")
        or ws_data.get("market_code")
        or ws_data.get("market_segment")
        or ws_data.get("market")
        or ws_data.get("strategy")
        or ""
    ).upper()
    if market in {"101", "10", "1"}:
        return "101"
    if market in {"001", "0"}:
        return "001"
    if "KOSDAQ" in market:
        return "101"
    if "KOSPI" in market:
        return "001"
    return ""


def _previous_day_source(
    token: str | None,
    code: str,
    ws_data: dict[str, Any],
    target_date: str,
    venue: str,
) -> dict[str, Any]:
    supplied = ws_data.get("previous_day_levels")
    if isinstance(supplied, dict) and supplied:
        return {**supplied, "source": supplied.get("source") or "runtime_state"}
    request_code, venue_basis = _daily_request_code(code, venue)
    if not token:
        return {
            "source_quality": "missing",
            "reason": "token_missing",
            "request_code": request_code,
            "venue_basis": venue_basis,
        }
    cache_key = (request_code, target_date)
    with _PREVIOUS_DAY_CACHE_LOCK:
        cached = _PREVIOUS_DAY_CACHE.get(cache_key)
        if cached and time.monotonic() - cached[0] <= _PREVIOUS_DAY_CACHE_TTL_SEC:
            return dict(cached[1])
    try:
        from src.utils import kiwoom_utils

        frame = kiwoom_utils.get_daily_data_ka10005_df(token, request_code)
        if frame is None or frame.empty:
            return {
                "source": "kiwoom_ka10005",
                "source_quality": "missing",
                "reason": "daily_rows_missing",
                "request_code": request_code,
                "venue_basis": venue_basis,
            }
        cutoff = datetime.strptime(target_date, "%Y-%m-%d")
        eligible = frame[frame.index < cutoff]
        if eligible.empty:
            return {
                "source": "kiwoom_ka10005",
                "source_quality": "missing",
                "reason": "previous_trading_day_missing",
                "request_code": request_code,
                "venue_basis": venue_basis,
            }
        index = eligible.index[-1]
        row = eligible.iloc[-1]
        result = {
            "date": index.date().isoformat(),
            "high": row.get("High"),
            "low": row.get("Low"),
            "close": row.get("Close"),
            "source": "kiwoom_ka10005",
            "source_quality": "pass",
            "request_code": request_code,
            "venue_basis": venue_basis,
        }
        with _PREVIOUS_DAY_CACHE_LOCK:
            _PREVIOUS_DAY_CACHE[cache_key] = (time.monotonic(), dict(result))
        return result
    except Exception as exc:
        return {
            "source": "kiwoom_ka10005",
            "source_quality": "missing",
            "reason": f"{type(exc).__name__}:{str(exc)[:120]}",
            "request_code": request_code,
            "venue_basis": venue_basis,
        }


def _index_context_source(
    token: str | None,
    index_code: str,
    *,
    source_role: str,
) -> dict[str, Any]:
    if not index_code:
        return {
            "source": "kiwoom_ka20005",
            "source_quality": {"status": "source_unavailable"},
            "reason": f"{source_role}_index_code_missing",
        }
    if not token:
        return {
            "source": "kiwoom_ka20005",
            "index_code": index_code,
            "source_quality": {"status": "source_unavailable"},
            "reason": "token_missing",
        }
    try:
        from src.utils import kiwoom_utils

        rows, meta = kiwoom_utils.get_index_minute_candles_ka20005_with_meta(
            token, index_code, limit=SOURCE_BAR_LIMIT
        )
        return {
            "source": "kiwoom_ka20005",
            "index_code": index_code,
            "minute_rows": rows,
            "source_meta": meta,
        }
    except Exception as exc:
        return {
            "source": "kiwoom_ka20005",
            "index_code": index_code,
            "source_quality": {"status": "source_unavailable"},
            "reason": f"{type(exc).__name__}:{str(exc)[:120]}",
        }


def build_multi_timeframe_context(
    rows: list[dict[str, Any]],
    *,
    token: str | None,
    symbol: str,
    venue: str,
    session: str,
    ws_data: dict[str, Any] | None,
    captured_at: datetime,
    fetch_external_sources: bool = False,
    minute_bar_source_api_id: str | None = None,
) -> dict[str, Any]:
    """Build the shared feature bundle from exact completed source windows."""

    ws = dict(ws_data or {})
    target_date = captured_at.astimezone(KST).date().isoformat()
    previous_day = (
        _previous_day_source(token, symbol, ws, target_date, venue)
        if fetch_external_sources or isinstance(ws.get("previous_day_levels"), dict)
        else {"source_quality": "missing", "reason": "auxiliary_fetch_not_requested"}
    )
    market_code = _explicit_index_code(ws, sector=False)
    sector_code = _explicit_index_code(ws, sector=True)
    market_context = (
        dict(ws.get("market_context") or {})
        if isinstance(ws.get("market_context"), dict)
        else (
            _index_context_source(token, market_code, source_role="market")
            if fetch_external_sources
            else {
                "source_quality": {"status": "source_unavailable"},
                "reason": "auxiliary_fetch_not_requested",
            }
        )
    )
    sector_context = (
        dict(ws.get("sector_context") or {})
        if isinstance(ws.get("sector_context"), dict)
        else (
            _index_context_source(token, sector_code, source_role="sector")
            if fetch_external_sources
            else {
                "source_quality": {"status": "source_unavailable"},
                "reason": "auxiliary_fetch_not_requested",
            }
        )
    )
    derived = derive_scalping_market_features(
        rows,
        symbol=_clean_code(symbol),
        venue=venue,
        session=session,
        target_date=target_date,
        captured_at=captured_at.isoformat(),
        previous_day=previous_day,
        market_context=market_context,
        sector_context=sector_context,
        minute_bar_source_api_id=minute_bar_source_api_id,
    )
    activation = promotion_activation_state(captured_at)
    bundle = {
        "schema": SCHEMA,
        "input_bundle_version": SCHEMA,
        "captured_at": derived.get("captured_at"),
        "multi_timeframe_bars": {
            key: list(rows_for_interval or [])[-MODEL_MULTI_TIMEFRAME_BAR_LIMIT:]
            for key, rows_for_interval in dict(
                derived.get("multi_timeframe_bars") or {}
            ).items()
        },
        "incomplete_multi_timeframe_bars": derived.get(
            "incomplete_multi_timeframe_bars"
        ),
        "session_bar_vwap": derived.get("session_bar_vwap"),
        "opening_range_5m": derived.get("opening_range_5m"),
        "opening_range_15m": derived.get("opening_range_15m"),
        "previous_day_levels": derived.get("previous_day_levels"),
        "market_context": derived.get("market_context"),
        "sector_context": derived.get("sector_context"),
        "source_quality": derived.get("source_quality"),
        "input_contract": INPUT_CONTRACT,
        "ai_input_enabled": bool(activation.get("active")),
        "live_payload_inclusion_effect": (
            "active_full_market"
            if activation.get("active")
            else "source_only_not_promoted"
        ),
        "promotion_activation": activation,
    }
    bundle["payload_hash"] = hashlib.sha256(
        json.dumps(
            bundle,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return bundle
