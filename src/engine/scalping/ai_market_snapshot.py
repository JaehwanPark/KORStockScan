"""Source-quality contract shared by real scalping AI decision points.

This module is an instrumentation and fail-closed preflight owner.  It cannot
select a provider/model, create BUY/HOLD authority, choose price/quantity, or
bypass deterministic trading guards.
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

from src.utils import kiwoom_utils
from src.engine.scalping.multi_timeframe_context import promotion_activation_state

SCHEMA = "ai_market_snapshot_v1"
PREFLIGHT_SCHEMA = "ai_input_preflight_v1"
KST = ZoneInfo("Asia/Seoul")
OBSERVATION_CONTRACT = {
    "metric_role": "ai_input_source_quality",
    "decision_authority": "provider_call_fail_closed_only",
    "window_policy": "exact_decision_snapshot",
    "sample_floor": "one_exact_provenance_row_per_venue_session_decision_point",
    "primary_decision_metric": "ai_input_preflight_status",
    "source_quality_gate": (
        "fresh_conflict_free_exact_venue_or_bounded_sor_execution_view_provenance"
    ),
    "forbidden_uses": [
        "standalone_buy_hold_or_exit_authority",
        "provider_or_model_change",
        "threshold_price_or_quantity_change",
        "broker_guard_bypass",
        "cross_venue_tuning",
        "underlying_event_venue_inference",
    ],
}

_MARKET_TYPES = ("0B", "0D")
_FRESH_MS = 3000.0
# 0w is an event-driven program-flow source and can legitimately update less
# often than trade/quote realtime types.  Keep a distinct bounded TTL so a
# valid observed zero or unchanged program flow is not mislabeled stale merely
# because no new 0w event arrived within the 0B/0D three-second window.
_PROGRAM_FRESH_MS = 60_000.0
# A one-minute candle is observed from its bar-open timestamp.  Reusing the
# sub-second WS TTL would incorrectly mark a healthy forming bar stale for most
# of its lifetime.  Keep one full interval plus a bounded 30-second delivery
# allowance; the candle producer's own structural quality gate remains active.
_CANDLE_FRESH_MS = 90_000.0
_FUTURE_TOLERANCE_MS = 1000.0
_POSITION_FRESH_SEC = 60.0
_PROCESS_STARTED_AT = time.time()
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PREFLIGHT_REPORT_DIR = (
    _PROJECT_ROOT / "data" / "report" / "entry_context_intraday_probe"
)
_BASELINE_REPORT_DIR = _PROJECT_ROOT / "data" / "report" / "ai_input_quality_baseline"
_ARTIFACT_STATUS_CACHE: dict[tuple[str, str, float, float], dict[str, Any]] = {}
_INTEGRATED_ROUTES = {"krx_nxt_integrated", "integrated", "sor"}
_KRX_ROUTES = {"krx_only", "krx_regular"}
_NXT_ROUTES = {"nxt_only", "nxt_regular"}
_BROKER_ACCOUNT_SNAPSHOT_LOCK = threading.RLock()
_BROKER_ACCOUNT_SNAPSHOT: dict[str, Any] = {}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _epoch(value: Any) -> float | None:
    parsed = _safe_float(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed / 1000.0 if parsed > 10_000_000_000 else parsed


def _iso(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=KST).isoformat()


def _base_code(value: Any) -> str:
    raw = str(value or "").strip().upper().replace(".0", "")
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            raw = raw[:-3]
    if raw.startswith("A") and len(raw) >= 7:
        raw = raw[1:]
    digits = "".join(character for character in raw if character.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def _item_suffix(value: Any) -> str:
    raw = str(value or "").strip().upper()
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            return suffix
    return ""


def _mapping(source: dict[str, Any], key: str) -> dict[str, Any]:
    value = source.get(key)
    return value if isinstance(value, dict) else {}


def publish_broker_account_snapshot(
    *,
    inventory: list[dict[str, Any]] | None,
    successful_exchanges: set[str] | list[str] | tuple[str, ...] | None,
    open_orders: list[dict[str, Any]] | None = None,
    open_orders_request_succeeded: bool = False,
    captured_at: float | None = None,
) -> None:
    """Publish one read-only broker reconciliation snapshot for AI contexts.

    The snapshot only exposes facts already returned by the account sync
    owner.  It does not call the broker, submit/cancel orders, or grant AI any
    order authority.
    """

    captured_epoch = float(captured_at if captured_at is not None else time.time())
    inventory_by_code: dict[str, dict[str, Any]] = {}
    for item in inventory or []:
        if not isinstance(item, dict):
            continue
        code = _base_code(item.get("code") or item.get("stock_code"))
        if code:
            inventory_by_code[code] = dict(item)

    open_qty_by_code: dict[str, dict[str, int]] = {}
    for item in open_orders or []:
        if not isinstance(item, dict):
            continue
        code = _base_code(item.get("code") or item.get("stock_code"))
        if not code:
            continue
        try:
            remaining_qty = max(
                0,
                int(
                    float(str(item.get("remaining_qty") or 0).replace(",", "").strip())
                ),
            )
        except (TypeError, ValueError):
            remaining_qty = 0
        side = str(item.get("side") or "").strip().upper()
        row = open_qty_by_code.setdefault(
            code,
            {"open_buy_qty": 0, "open_sell_qty": 0},
        )
        if side in {"매수", "BUY", "B", "2"}:
            row["open_buy_qty"] += remaining_qty
        elif side in {"매도", "SELL", "S", "1"}:
            row["open_sell_qty"] += remaining_qty

    snapshot = {
        "captured_at": captured_epoch,
        "inventory_by_code": inventory_by_code,
        "successful_exchanges": {
            str(value or "").strip().upper()
            for value in (successful_exchanges or [])
            if str(value or "").strip()
        },
        "open_qty_by_code": open_qty_by_code,
        "open_orders_request_succeeded": bool(open_orders_request_succeeded),
    }
    with _BROKER_ACCOUNT_SNAPSHOT_LOCK:
        _BROKER_ACCOUNT_SNAPSHOT.clear()
        _BROKER_ACCOUNT_SNAPSHOT.update(snapshot)


def _broker_account_context(
    *,
    stock_code: str,
    effective_venue: str,
    session_bucket: str,
    now_ts: float,
) -> dict[str, Any]:
    with _BROKER_ACCOUNT_SNAPSHOT_LOCK:
        snapshot = dict(_BROKER_ACCOUNT_SNAPSHOT)
        snapshot["inventory_by_code"] = dict(
            _BROKER_ACCOUNT_SNAPSHOT.get("inventory_by_code") or {}
        )
        snapshot["open_qty_by_code"] = dict(
            _BROKER_ACCOUNT_SNAPSHOT.get("open_qty_by_code") or {}
        )
        snapshot["successful_exchanges"] = set(
            _BROKER_ACCOUNT_SNAPSHOT.get("successful_exchanges") or set()
        )
    captured_at = _epoch(snapshot.get("captured_at"))
    if captured_at is None or captured_at - float(now_ts) > (
        _FUTURE_TOLERANCE_MS / 1000.0
    ):
        return {}

    code = _base_code(stock_code)
    venue, _resolution = _normalize_venue_cohort(
        venue=effective_venue,
        session=session_bucket,
    )
    expected_exchange = "NXT" if venue in {"NXT", "PREMARKET_KRX_LIKE"} else "KRX"
    inventory_row = (snapshot.get("inventory_by_code") or {}).get(code)
    successful_exchanges = snapshot.get("successful_exchanges") or set()
    position_verified = bool(
        isinstance(inventory_row, dict) or expected_exchange in successful_exchanges
    )
    open_orders_verified = bool(snapshot.get("open_orders_request_succeeded"))
    if not position_verified and not open_orders_verified:
        return {}

    context: dict[str, Any] = {
        "broker_snapshot_at": captured_at,
        "broker_snapshot_source": "account_sync_shared_snapshot",
    }
    if position_verified:
        raw_qty = (inventory_row or {}).get("qty", 0)
        try:
            context["broker_holding_qty"] = max(
                0, int(float(str(raw_qty or 0).replace(",", "").strip()))
            )
        except (TypeError, ValueError):
            context["broker_holding_qty"] = 0
        context["broker_position_verification"] = (
            "present" if isinstance(inventory_row, dict) else "verified_absent"
        )
    if open_orders_verified:
        open_qty = (snapshot.get("open_qty_by_code") or {}).get(
            code,
            {"open_buy_qty": 0, "open_sell_qty": 0},
        )
        context["open_buy_qty"] = int(open_qty.get("open_buy_qty") or 0)
        context["open_sell_qty"] = int(open_qty.get("open_sell_qty") or 0)
        context["broker_open_orders_verification"] = (
            "present"
            if context["open_buy_qty"] or context["open_sell_qty"]
            else "verified_zero"
        )
    return context


def _clear_broker_account_snapshot_for_tests() -> None:
    with _BROKER_ACCOUNT_SNAPSHOT_LOCK:
        _BROKER_ACCOUNT_SNAPSHOT.clear()


def enrich_investor_source(
    *,
    token: str | None,
    stock_code: str,
    request_code: str | None,
    ws_data: dict[str, Any] | None,
    observed_at: float,
) -> dict[str, Any]:
    """Attach one null-aware ka10059 observation without changing AI authority."""

    enriched = dict(ws_data or {})
    if enriched.get("investor_context"):
        return enriched
    if not token:
        enriched["investor_missing_reason"] = "investor_token_missing"
        return enriched

    api_code = str(request_code or stock_code or "").strip()
    try:
        investor_df = kiwoom_utils.get_investor_daily_ka10059_df(token, api_code)
        if investor_df is None or investor_df.empty:
            enriched["investor_missing_reason"] = "ka10059_empty_response"
            return enriched
        investor_context = kiwoom_utils.get_investor_flow_summary_ka10059(
            token,
            api_code,
        )
        latest_index = investor_df.index[-1]
        enriched["investor_context"] = {
            **investor_context,
            "request_code": api_code,
            "source_data_date": (
                latest_index.date().isoformat()
                if hasattr(latest_index, "date")
                else str(latest_index)
            ),
        }
        enriched["investor_observed_ts"] = float(observed_at)
        enriched["investor_source"] = "ka10059_process_cache_or_live"
        suffix = (
            "_NX"
            if api_code.upper().endswith("_NX")
            else ("_AL" if api_code.upper().endswith("_AL") else "")
        )
        enriched["investor_market_suffix"] = suffix
        enriched["investor_market_route"] = (
            "nxt_only"
            if suffix == "_NX"
            else ("krx_nxt_integrated" if suffix == "_AL" else "krx_only")
        )
        enriched["investor_freshness_limit_ms"] = (
            float(
                getattr(
                    kiwoom_utils.TRADING_RULES,
                    "KIWOOM_INVESTOR_CACHE_TTL_SEC",
                    60.0,
                )
                or 60.0
            )
            * 1000.0
        )
    except Exception as exc:
        enriched["investor_missing_reason"] = f"ka10059_error:{type(exc).__name__}"
    return enriched


def _market_data_route(*, suffix: str, route: str) -> str:
    suffix_value = str(suffix or "").strip().upper()
    route_value = str(route or "").strip().lower()
    if suffix_value == "_NX" or route_value in _NXT_ROUTES:
        return "nxt_only"
    if suffix_value == "_AL" or route_value in _INTEGRATED_ROUTES:
        return "krx_nxt_integrated"
    if not suffix_value and route_value in _KRX_ROUTES:
        return "krx_only"
    return route_value or "unknown"


def _underlying_event_venue(
    provenance: dict[str, dict[str, Any]],
) -> tuple[str | None, str]:
    # An integrated ``_AL`` item never identifies its underlying exchange.
    # Ignore any legacy/ad-hoc effective_venue value attached to that route so
    # a consumer cannot accidentally turn execution-view provenance into
    # KRX/NXT attribution authority.
    venues = {
        str(row.get("effective_venue") or "").strip().upper()
        for row in provenance.values()
        if row.get("quality") == "fresh"
        and _market_data_route(
            suffix=str(row.get("market_suffix") or ""),
            route=str(row.get("market_route") or ""),
        )
        != "krx_nxt_integrated"
        and str(row.get("effective_venue") or "").strip().upper() in {"KRX", "NXT"}
    }
    if len(venues) == 1:
        return next(iter(venues)), "exact_per_realtime_type"
    if len(venues) > 1:
        return None, "conflicting_per_realtime_type"
    return None, "not_provided"


def _normalize_venue_cohort(*, venue: str, session: str) -> tuple[str, str]:
    """Keep the market cohort independent from broker and market-data routes."""

    venue_value = str(venue or "").strip().upper()
    session_value = str(session or "").strip().lower()
    if "premarket" in session_value or venue_value == "PREMARKET_KRX_LIKE":
        return "PREMARKET_KRX_LIKE", "session"
    if "nxt" in session_value or venue_value == "NXT":
        return "NXT", "explicit_or_session"
    if venue_value == "KRX":
        return "KRX", "explicit"
    if venue_value in {"SOR", "INTEGRATED", "KRX_NXT_INTEGRATED"}:
        if "krx" in session_value:
            return "KRX", "legacy_route_value_normalized_by_session"
        return "UNKNOWN", "legacy_route_value_without_session"
    return venue_value or "UNKNOWN", "explicit_or_missing"


def realtime_type_provenance(
    ws_data: dict[str, Any] | None,
    *,
    now_ts: float | None = None,
) -> dict[str, dict[str, Any]]:
    """Return exact per-type provenance; aggregate fields are never substituted."""

    ws = ws_data if isinstance(ws_data, dict) else {}
    now_epoch = float(now_ts if now_ts is not None else time.time())
    timestamps = _mapping(ws, "last_realtime_type_ts")
    items = _mapping(ws, "last_realtime_type_item")
    suffixes = _mapping(ws, "last_realtime_type_market_suffix")
    routes = _mapping(ws, "last_realtime_type_market_route")
    effective_venues = _mapping(ws, "last_realtime_type_effective_venue")
    result: dict[str, dict[str, Any]] = {}
    for realtime_type in _MARKET_TYPES:
        observed_epoch = _epoch(timestamps.get(realtime_type))
        age_ms = (
            (now_epoch - observed_epoch) * 1000.0
            if observed_epoch is not None
            else None
        )
        result[realtime_type] = {
            "realtime_type": realtime_type,
            "item": items.get(realtime_type),
            "market_suffix": str(suffixes.get(realtime_type) or "").upper(),
            "market_route": str(routes.get(realtime_type) or "").lower(),
            "effective_venue": str(effective_venues.get(realtime_type) or "").upper(),
            "observed_at": _iso(observed_epoch),
            "observed_epoch": observed_epoch,
            "age_ms": (round(max(0.0, age_ms), 3) if age_ms is not None else None),
            "quality": (
                "missing"
                if observed_epoch is None
                else (
                    "future"
                    if age_ms is not None and age_ms < -_FUTURE_TOLERANCE_MS
                    else (
                        "fresh"
                        if age_ms is not None and age_ms <= _FRESH_MS
                        else "stale"
                    )
                )
            ),
        }
    return result


def preferred_ws_route(
    ws_data: dict[str, Any] | None,
    *,
    now_ts: float | None = None,
) -> tuple[str, str]:
    """Prefer exact fresh 0D/0B provenance over aggregate compatibility fields."""

    provenance = realtime_type_provenance(ws_data, now_ts=now_ts)
    for realtime_type in ("0D", "0B"):
        row = provenance[realtime_type]
        if row["quality"] == "fresh" and (
            row.get("market_suffix") or row.get("market_route")
        ):
            return str(row["market_suffix"]), str(row["market_route"])
    ws = ws_data if isinstance(ws_data, dict) else {}
    suffix = next(
        (
            str(ws.get(key) or "").upper()
            for key in (
                "market_suffix",
                "last_market_suffix",
                "last_ws_market_suffix",
                "realtime_market_suffix",
            )
            if ws.get(key) not in (None, "")
        ),
        "",
    )
    route = next(
        (
            str(ws.get(key) or "").lower()
            for key in (
                "market_route",
                "last_market_route",
                "last_ws_market_route",
                "realtime_market_route",
            )
            if ws.get(key) not in (None, "")
        ),
        "",
    )
    return suffix, route


def route_realtime_partition_status(
    ws_data: dict[str, Any] | None,
    *,
    suffix: str,
    route: str,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Describe whether one exact 0B/0D route is usable now.

    This is an observation-only selector input.  It does not infer an
    underlying venue from an integrated route and does not relax snapshot
    preflight.  Holding context uses it to avoid choosing a stale SOR view
    merely because the eventual broker order route is SOR.
    """

    ws = ws_data if isinstance(ws_data, dict) else {}
    now_epoch = float(now_ts if now_ts is not None else time.time())
    normalized_suffix = str(suffix or "").upper()
    normalized_route = str(route or "").lower()
    route_key = f"{normalized_suffix or 'KRX'}|{normalized_route}"
    partitions = ws.get("realtime_type_snapshots_by_route")
    selected = partitions.get(route_key) if isinstance(partitions, dict) else None
    canonical_orderbook = (
        ws.get("orderbook") if isinstance(ws.get("orderbook"), dict) else {}
    )
    if not canonical_orderbook:
        canonical_orderbook = {
            "bids": [{"price": ws.get("best_bid")}],
            "asks": [{"price": ws.get("best_ask")}],
        }
    source = "route_partition"
    if isinstance(selected, dict):
        rows = {name: selected.get(name) for name in _MARKET_TYPES}
    else:
        source = "canonical_exact_route"
        provenance = realtime_type_provenance(ws, now_ts=now_epoch)
        rows = {
            name: {
                "observed_epoch": provenance[name].get("observed_epoch"),
                "market_suffix": provenance[name].get("market_suffix"),
                "market_route": provenance[name].get("market_route"),
                "quality": provenance[name].get("quality"),
                **(
                    {"current_price": ws.get("curr")}
                    if name == "0B"
                    else {"orderbook": canonical_orderbook}
                ),
            }
            for name in _MARKET_TYPES
        }
        exact_rows_missing = all(
            row.get("observed_epoch") is None for row in rows.values()
        )
        aggregate_suffix, aggregate_route = preferred_ws_route(ws, now_ts=now_epoch)
        aggregate_epoch = _epoch(ws.get("last_ws_update_ts"))
        aggregate_age_ms = (
            max(0.0, (now_epoch - aggregate_epoch) * 1000.0)
            if aggregate_epoch is not None
            else None
        )
        if (
            not isinstance(partitions, dict)
            and exact_rows_missing
            and aggregate_suffix == normalized_suffix
            and aggregate_route == normalized_route
            and aggregate_age_ms is not None
            and aggregate_age_ms <= _FRESH_MS
        ):
            source = "legacy_aggregate_route_current"
            rows = {
                name: {
                    "observed_epoch": aggregate_epoch,
                    "market_suffix": aggregate_suffix,
                    "market_route": aggregate_route,
                    **(
                        {"current_price": ws.get("curr")}
                        if name == "0B"
                        else {"orderbook": canonical_orderbook}
                    ),
                }
                for name in _MARKET_TYPES
            }

    row_status: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for realtime_type, row in rows.items():
        if not isinstance(row, dict):
            blockers.append(f"{realtime_type.lower()}_missing")
            row_status[realtime_type] = {
                "present": False,
                "fresh": False,
                "route_exact": False,
                "age_ms": None,
            }
            continue
        observed_epoch = _epoch(row.get("observed_epoch"))
        age_ms = (
            max(0.0, (now_epoch - observed_epoch) * 1000.0)
            if observed_epoch is not None
            else None
        )
        route_exact = bool(
            str(row.get("market_suffix") or "").upper() == normalized_suffix
            and str(row.get("market_route") or "").lower() == normalized_route
        )
        fresh = bool(
            row.get("quality") == "fresh"
            if source == "canonical_exact_route"
            else age_ms is not None
            and age_ms <= _FRESH_MS
            and observed_epoch <= now_epoch + (_FUTURE_TOLERANCE_MS / 1000.0)
        )
        if not route_exact:
            blockers.append(f"{realtime_type.lower()}_route_mismatch")
        if not fresh:
            blockers.append(f"{realtime_type.lower()}_stale_or_missing_timestamp")
        if realtime_type == "0B":
            current_price = _safe_float(row.get("current_price"))
            if current_price is None or current_price <= 0:
                blockers.append("0b_current_price_missing")
        else:
            orderbook = row.get("orderbook")
            bids = (
                orderbook.get("bids")
                if isinstance(orderbook, dict)
                and isinstance(orderbook.get("bids"), list)
                else []
            )
            asks = (
                orderbook.get("asks")
                if isinstance(orderbook, dict)
                and isinstance(orderbook.get("asks"), list)
                else []
            )
            best_bid = (
                _safe_float(bids[0].get("price"))
                if bids and isinstance(bids[0], dict)
                else None
            )
            best_ask = (
                _safe_float(asks[0].get("price"))
                if asks and isinstance(asks[0], dict)
                else None
            )
            if (
                best_bid is None
                or best_ask is None
                or best_bid <= 0
                or best_ask < best_bid
            ):
                blockers.append("0d_executable_bbo_missing_or_invalid")
        row_status[realtime_type] = {
            "present": True,
            "fresh": fresh,
            "route_exact": route_exact,
            "age_ms": round(age_ms, 3) if age_ms is not None else None,
        }

    blockers = sorted(set(blockers))
    return {
        "ready": not blockers,
        "status": "fresh_exact" if not blockers else "unusable",
        "route_key": route_key,
        "source": source,
        "blockers": blockers,
        "rows": row_status,
        "freshness_limit_ms": _FRESH_MS,
    }


def _route_partitioned_ws_view(
    ws_data: dict[str, Any],
    candle_context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Select one exact 0B/0D route without mixing concurrent subscriptions.

    Kiwoom treats the base, ``_NX``, and ``_AL`` item values as distinct
    exchange routes.  The canonical snapshot keeps the latest observation per
    realtime type for compatibility, so concurrent KRX/SOR subscriptions can
    otherwise leave 0B and 0D on different routes.  Use the route selected by
    the candle owner when both route-owned realtime rows are available.
    """

    ws = ws_data if isinstance(ws_data, dict) else {}
    candle = candle_context if isinstance(candle_context, dict) else {}
    quality = (
        candle.get("source_quality")
        if isinstance(candle.get("source_quality"), dict)
        else {}
    )
    if bool(quality.get("route_partition_used", False)):
        # The empty suffix is the canonical KRX route value, not a missing
        # value.  Using ``or`` here silently replaced it with a concurrent
        # candle-level ``_AL`` compatibility field and reintroduced route
        # mixing after the candle owner had selected exact KRX.
        suffix = str(quality.get("route_partition_selected_suffix") or "").upper()
        route = str(quality.get("route_partition_selected_route") or "").lower()
    else:
        suffix = str(candle.get("ws_suffix") or "").upper()
        route = str(candle.get("ws_route") or "").lower()
    if not route:
        return ws, {
            "used": False,
            "reason": "candle_route_missing",
            "selected_key": None,
        }
    route_key = f"{suffix or 'KRX'}|{route}"
    partitions = ws.get("realtime_type_snapshots_by_route")
    if not isinstance(partitions, dict):
        return ws, {
            "used": False,
            "reason": "route_snapshots_unavailable",
            "selected_key": route_key,
        }
    selected = partitions.get(route_key)
    if not isinstance(selected, dict):
        return ws, {
            "used": False,
            "reason": "candle_route_snapshot_missing",
            "selected_key": route_key,
        }
    rows = {
        realtime_type: selected.get(realtime_type) for realtime_type in _MARKET_TYPES
    }
    if any(not isinstance(row, dict) for row in rows.values()):
        return ws, {
            "used": False,
            "reason": "candle_route_realtime_type_incomplete",
            "selected_key": route_key,
        }

    view = dict(ws)
    field_map = {
        "last_realtime_type_ts": "observed_epoch",
        "last_realtime_type_item": "item",
        "last_realtime_type_market_suffix": "market_suffix",
        "last_realtime_type_market_route": "market_route",
        "last_realtime_type_effective_venue": "effective_venue",
    }
    for target_field, row_field in field_map.items():
        values = dict(_mapping(ws, target_field))
        for realtime_type, row in rows.items():
            values[realtime_type] = row.get(row_field)
        view[target_field] = values

    # Never retain quote fields from the canonical latest snapshot once a
    # candle-owned route partition has been selected.  Those fields can be
    # from the other concurrent subscription; absent selected-route values
    # must reach the preflight as absent and fail closed.
    view["curr"] = 0
    view["orderbook"] = {}
    view["best_bid"] = 0
    view["best_ask"] = 0
    view["ask_tot"] = 0
    view["bid_tot"] = 0
    route_ticks = ws.get("recent_trade_ticks_by_route")
    selected_ticks = (
        route_ticks.get(route_key) if isinstance(route_ticks, dict) else None
    )
    # The shared tape buffer may belong to the other concurrent route.  Once
    # an exact 0B/0D partition is selected, either carry its matching tape or
    # expose an empty tape so preflight can fail closed without cross-route
    # evidence.
    view["recent_trade_ticks"] = [
        dict(tick) for tick in (selected_ticks or []) if isinstance(tick, dict)
    ]

    excluded_optional_sources: list[str] = []
    program_suffix = str(
        _mapping(view, "last_realtime_type_market_suffix").get("0w") or ""
    ).upper()
    program_route = str(
        _mapping(view, "last_realtime_type_market_route").get("0w") or ""
    ).lower()
    if (program_suffix or program_route) and (
        program_suffix != suffix or program_route != route
    ):
        for target_field in field_map:
            values = dict(_mapping(view, target_field))
            values.pop("0w", None)
            view[target_field] = values
        received_types = {
            str(value or "").strip() for value in (view.get("received_types") or [])
        }
        received_types.discard("0w")
        view["received_types"] = received_types
        view["last_prog_update_ts"] = 0.0
        excluded_optional_sources.append("program_route_mismatch")

    tape_row = rows["0B"]
    quote_row = rows["0D"]
    current_price = _safe_float(tape_row.get("current_price"))
    if current_price is not None and current_price > 0:
        view["curr"] = current_price
    orderbook = quote_row.get("orderbook")
    if isinstance(orderbook, dict):
        view["orderbook"] = orderbook
        bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        if bids and isinstance(bids[0], dict):
            view["best_bid"] = bids[0].get("price")
        if asks and isinstance(asks[0], dict):
            view["best_ask"] = asks[0].get("price")
        view["ask_tot"] = quote_row.get("ask_total") or quote_row.get("ask_tot") or 0
        view["bid_tot"] = quote_row.get("bid_total") or quote_row.get("bid_tot") or 0
    observed_epochs = [
        _epoch(row.get("observed_epoch"))
        for row in rows.values()
        if isinstance(row, dict)
    ]
    observed_epochs = [value for value in observed_epochs if value is not None]
    if observed_epochs:
        view["last_ws_update_ts"] = max(observed_epochs)
    view["last_ws_market_suffix"] = suffix
    view["last_ws_market_route"] = route
    return view, {
        "used": True,
        "reason": "candle_route_exact_0b_0d_partition",
        "selected_key": route_key,
        "excluded_optional_sources": excluded_optional_sources,
    }


def route_partitioned_ws_view(
    ws_data: dict[str, Any] | None,
    candle_context: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Public read-only route view shared by holding and AI preflight owners."""

    return _route_partitioned_ws_view(
        ws_data if isinstance(ws_data, dict) else {},
        candle_context if isinstance(candle_context, dict) else {},
    )


def _broker_route_matches_cohort(
    *,
    broker_route: str,
    venue_cohort: str,
    session: str,
) -> bool:
    route = str(broker_route or "").strip().upper()
    cohort = str(venue_cohort or "").strip().upper()
    if not route:
        return False
    if cohort == "KRX":
        return route == "SOR"
    if cohort == "PREMARKET_KRX_LIKE":
        return route == "NXT"
    if cohort == "NXT":
        return route == "NXT"
    return False


def _source_row(
    *,
    value: Any,
    source: str,
    observed_epoch: float | None,
    now_epoch: float,
    market_suffix: str = "",
    market_route: str = "",
    missing_reason: str | None = None,
    freshness_limit_ms: float = _FRESH_MS,
) -> dict[str, Any]:
    raw_age_ms = (
        (now_epoch - observed_epoch) * 1000.0 if observed_epoch is not None else None
    )
    age_ms = round(max(0.0, raw_age_ms), 3) if raw_age_ms is not None else None
    quality = "fresh"
    if value is None:
        quality = "missing"
    elif age_ms is None:
        quality = "unknown_age"
    elif raw_age_ms is not None and raw_age_ms < -_FUTURE_TOLERANCE_MS:
        quality = "future"
    elif age_ms > freshness_limit_ms:
        quality = "stale"
    return {
        "value": value,
        "source": source,
        "observed_at": _iso(observed_epoch),
        "age_ms": age_ms,
        "market_suffix": market_suffix or None,
        "market_route": market_route or None,
        "freshness_limit_ms": freshness_limit_ms,
        "quality": quality,
        "missing_reason": missing_reason if value is None else None,
    }


def _active_holding_position(position: dict[str, Any]) -> bool:
    broker_quantity = next(
        (
            _safe_float(position.get(key))
            for key in (
                "broker_holding_qty",
                "verified_holding_qty",
                "broker_qty",
            )
            if position.get(key) not in (None, "")
        ),
        None,
    )
    memory_quantity = next(
        (
            _safe_float(position.get(key))
            for key in ("remaining_qty", "buy_qty", "qty")
            if position.get(key) not in (None, "")
        ),
        None,
    )
    # A reconciled broker quantity is authoritative, including an explicit
    # zero.  Only fall back to runtime memory when no broker quantity exists.
    quantity = broker_quantity if broker_quantity is not None else memory_quantity
    avg_price = next(
        (
            _safe_float(position.get(key))
            for key in ("avg_price", "buy_price")
            if position.get(key) not in (None, "")
        ),
        None,
    )
    return bool(quantity is not None and quantity > 0 and avg_price and avg_price > 0)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _simulation_position_reconciled(position: dict[str, Any]) -> bool:
    """Validate a simulation-book position without claiming broker inventory."""

    simulation_book = str(position.get("simulation_book") or "").strip()
    simulation_owner = str(position.get("simulation_owner") or "").strip()
    strategy = str(position.get("strategy") or "").strip().upper()
    sim_record_id = str(
        position.get("sim_record_id") or position.get("sim_parent_record_id") or ""
    ).strip()
    decision_authority = str(position.get("decision_authority") or "").strip()
    return bool(
        simulation_book == "scalp_ai_buy_all"
        and simulation_owner
        and strategy in {"SCALPING", "SCALP"}
        and _boolish(position.get("scalp_live_simulator"))
        and sim_record_id
        and decision_authority == "sim_observation_only"
        and _boolish(position.get("simulated_order"))
        and not _boolish(position.get("actual_order_submitted"))
        and _boolish(position.get("broker_order_forbidden"))
        and _active_holding_position(position)
    )


def enrich_position_with_broker_account_snapshot(
    *,
    stock_code: str,
    effective_venue: str,
    session_bucket: str,
    position: dict[str, Any] | None,
    now_ts: float,
) -> dict[str, Any]:
    """Merge only positively confirmed shared broker facts into a holding.

    A shared verified-absent row is useful before entry but is never allowed to
    erase an active in-memory holding.  Explicit caller fields remain
    authoritative and overwrite the shared observation.
    """

    explicit = dict(position) if isinstance(position, dict) else {}
    shared = _broker_account_context(
        stock_code=stock_code,
        effective_venue=effective_venue,
        session_bucket=session_bucket,
        now_ts=now_ts,
    )
    explicit_status = str(explicit.get("status") or "").strip().upper()
    explicit_active = _active_holding_position(explicit) or explicit_status in {
        "HOLDING",
        "SELL_ORDERED",
    }
    shared_positive_holding = bool(
        shared.get("broker_position_verification") == "present"
        and (_safe_float(shared.get("broker_holding_qty")) or 0) > 0
    )
    if explicit_active and not shared_positive_holding:
        return explicit
    merged = dict(shared)
    merged.update(explicit)
    return merged


def _integrated_sor_execution_view_proof(
    *,
    stock_code: str,
    decision_stage: str,
    venue: str,
    session: str,
    broker_route: str,
    candle_context: dict[str, Any],
    position: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
    now_epoch: float,
) -> tuple[bool, str]:
    """Prove a bounded executable SOR view without inventing an event venue.

    ``_AL`` does not identify the underlying exchange.  It can still be the
    executable market view when the planned broker route is SOR and every
    required source is consistently integrated.  Post-probe proof is allowed
    only for an active, filled probe whose frozen execution route is also SOR;
    this proves an executable SOR view, never the underlying event venue.
    """

    stage = str(decision_stage or "").strip().lower()
    session_value = str(session or "").strip().lower()
    clock = datetime.fromtimestamp(now_epoch, tz=KST).time()
    holding_stage = stage in {
        "holding_score",
        "holding_score_submit_authority",
        "holding_flow",
    } or stage.startswith("overnight")
    entry_stage = stage in {"entry_context", "entry_screen", "gatekeeper"}
    post_probe_stage = stage == "post_probe"
    frozen_execution_route = (
        str(
            position.get("entry_execution_broker_route")
            or position.get("broker_route")
            or broker_route
            or ""
        )
        .strip()
        .upper()
    )
    post_probe_position_contract = bool(
        post_probe_stage
        and _active_holding_position(position)
        and frozen_execution_route == "SOR"
        and str(position.get("entry_split_probe_bundle_id") or "").strip()
        and (_safe_float(position.get("entry_split_probe_fill_price")) or 0.0) > 0
        and (_safe_float(position.get("entry_split_probe_filled_at")) or 0.0) > 0
    )
    candle_quality = (
        candle_context.get("source_quality")
        if isinstance(candle_context.get("source_quality"), dict)
        else {}
    )
    rows = [provenance[key] for key in _MARKET_TYPES]
    candle_schema = str(candle_context.get("schema") or "").strip()
    conditions = {
        "supported_stage": holding_stage or entry_stage or post_probe_stage,
        "stage_position_contract": (
            _active_holding_position(position)
            if holding_stage
            else post_probe_position_contract if post_probe_stage else entry_stage
        ),
        "krx_regular_cohort": str(venue or "").strip().upper() == "KRX"
        and session_value == "krx_regular"
        and datetime.strptime("09:00", "%H:%M").time()
        <= clock
        <= datetime.strptime("15:30", "%H:%M").time(),
        "sor_broker_route": str(broker_route or "").strip().upper() == "SOR",
        "integrated_candle_route": (
            post_probe_stage
            or (
                candle_schema in {"session_candle_source_v1", "entry_candle_context_v1"}
                and _base_code(candle_context.get("request_code"))
                == _base_code(stock_code)
                and str(candle_context.get("rest_route") or "").strip().upper() == "_AL"
                and str(candle_context.get("ws_route") or "").strip().lower()
                == "krx_nxt_integrated"
                and candle_quality.get("status") == "fresh_consistent"
            )
        ),
        "integrated_realtime_routes": all(
            row.get("quality") == "fresh"
            and str(row.get("market_suffix") or "").strip().upper() == "_AL"
            and _market_data_route(
                suffix=str(row.get("market_suffix") or ""),
                route=str(row.get("market_route") or ""),
            )
            == "krx_nxt_integrated"
            and str(row.get("effective_venue") or "").strip().upper() in {"", "KRX"}
            for row in rows
        ),
    }
    missing = [name for name, passed in conditions.items() if not passed]
    if missing:
        return False, "missing:" + ",".join(missing)
    if holding_stage:
        return True, "holding_sor_integrated_execution_view"
    if post_probe_stage:
        return True, "post_probe_sor_integrated_execution_view"
    return True, "entry_sor_integrated_execution_view"


def _nxt_aftermarket_integrated_execution_view_proof(
    *,
    stock_code: str,
    decision_stage: str,
    venue: str,
    session: str,
    broker_route: str,
    candle_context: dict[str, Any],
    position: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
    now_epoch: float,
) -> tuple[bool, str]:
    """Accept a bounded NXT execution view without inventing event venue.

    Kiwoom may deliver NXT-aftermarket 0B/0D observations through the
    integrated ``_AL`` route.  The route is usable for an NXT decision only
    when the session candle producer independently proved the closed-KRX
    ``_AL`` -> ``_NX`` equivalence and every required realtime type carries
    the same fresh integrated route.  This proof never grants underlying
    event-venue attribution.
    """

    stage = str(decision_stage or "").strip().lower()
    session_value = str(session or "").strip().lower()
    clock = datetime.fromtimestamp(now_epoch, tz=KST).time()
    holding_stage = stage in {
        "holding_score",
        "holding_score_submit_authority",
        "holding_flow",
    } or stage.startswith("overnight")
    entry_stage = stage in {"entry_context", "entry_screen", "gatekeeper"}
    candle_quality = (
        candle_context.get("source_quality")
        if isinstance(candle_context.get("source_quality"), dict)
        else {}
    )
    route_proof = (
        candle_quality.get("route_equivalence_proof")
        if isinstance(candle_quality.get("route_equivalence_proof"), dict)
        else {}
    )
    rows = [provenance[key] for key in _MARKET_TYPES]
    conditions = {
        "supported_stage": holding_stage or entry_stage,
        "stage_position_contract": (
            _active_holding_position(position) if holding_stage else entry_stage
        ),
        "nxt_aftermarket_cohort": str(venue or "").strip().upper() == "NXT"
        and session_value == "nxt_aftermarket"
        and datetime.strptime("16:00", "%H:%M").time()
        <= clock
        <= datetime.strptime("20:00", "%H:%M").time(),
        "nxt_broker_route": str(broker_route or "").strip().upper() == "NXT",
        "candle_route_equivalence": (
            str(candle_context.get("schema") or "").strip()
            in {"session_candle_source_v1", "entry_candle_context_v1"}
            and _base_code(candle_context.get("request_code")) == _base_code(stock_code)
            and str(candle_context.get("rest_route") or "").strip().upper() == "_NX"
            and str(candle_context.get("ws_route") or "").strip().lower()
            == "krx_nxt_integrated"
            and bool(candle_context.get("route_equivalence_proven", False))
            and str(candle_context.get("route_equivalence") or "").strip()
            == "nxt_aftermarket_integrated_ws_to_nx_rest"
            and candle_quality.get("status") == "fresh_consistent"
        ),
        "candle_route_proof": (
            bool(route_proof.get("proven", False))
            and str(route_proof.get("proof_session") or "").strip() == "nxt_aftermarket"
            and bool(route_proof.get("krx_regular_closed_by_clock", False))
            and str(route_proof.get("required_rest_suffix") or "").strip().upper()
            == "_NX"
            and str(route_proof.get("required_ws_suffix") or "").strip().upper()
            == "_AL"
            and str(route_proof.get("required_ws_route") or "").strip().lower()
            == "krx_nxt_integrated"
        ),
        "integrated_realtime_routes": all(
            row.get("quality") == "fresh"
            and _base_code(row.get("item")) == _base_code(stock_code)
            and str(row.get("market_suffix") or "").strip().upper() == "_AL"
            and _market_data_route(
                suffix=str(row.get("market_suffix") or ""),
                route=str(row.get("market_route") or ""),
            )
            == "krx_nxt_integrated"
            for row in rows
        ),
    }
    missing = [name for name, passed in conditions.items() if not passed]
    if missing:
        return False, "missing:" + ",".join(missing)
    if holding_stage:
        return True, "holding_nxt_aftermarket_integrated_execution_view"
    return True, "entry_nxt_aftermarket_integrated_execution_view"


def _venue_consistency(
    *,
    stock_code: str,
    venue: str,
    session: str,
    provenance: dict[str, dict[str, Any]],
    now_epoch: float,
    integrated_sor_execution_view_proven: bool = False,
    nxt_integrated_execution_view_proven: bool = False,
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    rows = [provenance[key] for key in _MARKET_TYPES]
    fresh_rows = [row for row in rows if row.get("quality") == "fresh"]
    if not fresh_rows:
        return False, ["realtime_type_provenance_missing_or_stale"]
    base = _base_code(stock_code)
    if any(not _base_code(row.get("item")) for row in fresh_rows):
        blockers.append("realtime_type_item_missing")
    if any(_base_code(row.get("item")) not in {"", base} for row in fresh_rows):
        blockers.append("symbol_conflict")
    if any(
        _item_suffix(row.get("item")) != str(row.get("market_suffix") or "")
        for row in fresh_rows
    ):
        blockers.append("item_suffix_conflict")
    pairs = {
        (
            str(row.get("market_suffix") or ""),
            str(row.get("market_route") or ""),
            str(row.get("effective_venue") or ""),
        )
        for row in fresh_rows
    }
    if len(pairs) > 1:
        blockers.append("realtime_type_route_conflict")

    venue_value = str(venue or "").upper()
    session_value = str(session or "").lower()
    now_clock = datetime.fromtimestamp(now_epoch, tz=KST).time()
    if venue_value not in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}:
        blockers.append("effective_venue_unknown_or_unsupported")
    for row in fresh_rows:
        suffix = str(row.get("market_suffix") or "")
        route = str(row.get("market_route") or "")
        data_route = _market_data_route(suffix=suffix, route=route)
        if (
            (suffix == "_NX" and route not in _NXT_ROUTES)
            or (suffix == "_AL" and route not in _INTEGRATED_ROUTES)
            or (not suffix and route and route not in _KRX_ROUTES)
        ):
            blockers.append("market_suffix_route_conflict")
        if venue_value == "KRX":
            if data_route not in {"krx_only", "krx_nxt_integrated"}:
                blockers.append("krx_compatible_market_data_route_required")
            elif (
                data_route == "krx_nxt_integrated"
                and not integrated_sor_execution_view_proven
            ):
                blockers.append("krx_integrated_event_venue_unproven")
        elif venue_value == "NXT" and "aftermarket" in session_value:
            nx_exact = data_route == "nxt_only"
            al_proven = (
                data_route == "krx_nxt_integrated"
                and (
                    str(row.get("effective_venue") or "").strip().upper() == "NXT"
                    or nxt_integrated_execution_view_proven
                )
                and datetime.strptime("16:00", "%H:%M").time()
                <= now_clock
                <= datetime.strptime("20:00", "%H:%M").time()
            )
            if not (nx_exact or al_proven):
                blockers.append("nxt_aftermarket_source_unproven")
        elif venue_value == "NXT":
            if data_route != "nxt_only":
                blockers.append("nxt_overlap_exact_source_required")
        elif venue_value == "PREMARKET_KRX_LIKE":
            within = (
                datetime.strptime("08:00", "%H:%M").time()
                <= now_clock
                < datetime.strptime("09:00", "%H:%M").time()
            )
            route_ok = data_route in {"nxt_only", "krx_nxt_integrated"}
            if not within or not route_ok:
                blockers.append("premarket_actual_route_proof_missing")
    return not blockers, sorted(set(blockers))


def build_ai_market_snapshot(
    *,
    stock_code: str,
    decision_stage: str,
    ws_data: dict[str, Any] | None,
    effective_venue: str,
    session_bucket: str,
    broker_route: str | None = None,
    candle_context: dict[str, Any] | None = None,
    position: dict[str, Any] | None = None,
    now_ts: float | None = None,
    require_position_reconciliation: bool = False,
) -> dict[str, Any]:
    candle_ctx = candle_context if isinstance(candle_context, dict) else {}
    raw_ws = ws_data if isinstance(ws_data, dict) else {}
    ws, route_partition = _route_partitioned_ws_view(raw_ws, candle_ctx)
    now_epoch = float(now_ts if now_ts is not None else time.time())
    normalized_venue, venue_resolution = _normalize_venue_cohort(
        venue=effective_venue,
        session=session_bucket,
    )
    explicit_position_ctx = position if isinstance(position, dict) else {}
    stage_value = str(decision_stage or "").strip().lower()
    require_position_reconciliation = bool(
        require_position_reconciliation
        or any(
            token in stage_value
            for token in ("holding_flow", "overnight", "submit_authority")
        )
    )
    explicit_position_status = (
        str(explicit_position_ctx.get("status") or "").strip().upper()
    )
    explicit_position_is_active = _active_holding_position(
        explicit_position_ctx
    ) or explicit_position_status in {"HOLDING", "SELL_ORDERED"}
    position_ctx = enrich_position_with_broker_account_snapshot(
        stock_code=stock_code,
        effective_venue=normalized_venue,
        session_bucket=session_bucket,
        position=explicit_position_ctx,
        now_ts=now_epoch,
    )
    provenance = realtime_type_provenance(ws, now_ts=now_epoch)
    suffix, route = preferred_ws_route(ws, now_ts=now_epoch)
    market_data_route = _market_data_route(suffix=suffix, route=route)
    underlying_event_venue, underlying_event_venue_source = _underlying_event_venue(
        provenance
    )
    quote_row = provenance["0D"]
    tape_row = provenance["0B"]
    quote_epoch = quote_row.get("observed_epoch")
    tape_epoch = tape_row.get("observed_epoch")
    orderbook = ws.get("orderbook") if isinstance(ws.get("orderbook"), dict) else {}
    bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
    asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
    bid_row = bids[0] if bids and isinstance(bids[0], dict) else {}
    ask_row = asks[0] if asks and isinstance(asks[0], dict) else {}
    current_price = _safe_float(ws.get("curr") or ws.get("price"))
    best_bid = _safe_float(
        ws.get("best_bid") or ws.get("bid_price") or bid_row.get("price")
    )
    best_ask = _safe_float(
        ws.get("best_ask") or ws.get("ask_price") or ask_row.get("price")
    )
    effective_quote_source = str(
        ws.get("market_data_effective_price_source") or ""
    ).strip()
    effective_quote_state = str(ws.get("market_data_freshness_state") or "").strip()
    effective_quote_epoch = _epoch(ws.get("market_data_effective_quote_observed_epoch"))
    rest_quote_reanchor = bool(
        effective_quote_source == "ka10004_rest_orderbook"
        and effective_quote_state == "rest_enriched"
        and effective_quote_epoch is not None
        and 0.0 <= now_epoch - effective_quote_epoch <= (_FRESH_MS / 1000.0)
        and current_price is not None
        and current_price > 0
        and best_bid is not None
        and best_ask is not None
        and best_bid > 0
        and best_ask >= best_bid
    )
    quote_value_epoch = effective_quote_epoch if rest_quote_reanchor else quote_epoch
    price_value_epoch = effective_quote_epoch if rest_quote_reanchor else tape_epoch
    quote_value_source = "ka10004_rest_orderbook" if rest_quote_reanchor else "ws_0D"
    price_value_source = "ka10004_rest_orderbook" if rest_quote_reanchor else "ws_0B"
    candle_quality = (
        candle_ctx.get("source_quality")
        if isinstance(candle_ctx.get("source_quality"), dict)
        else {}
    )
    candle_age_sec = _safe_float(candle_ctx.get("latest_bar_age_sec"))
    candle_epoch = (
        now_epoch - candle_age_sec
        if candle_age_sec is not None and candle_age_sec >= 0
        else None
    )
    broker_snapshot_at = _epoch(position_ctx.get("broker_snapshot_at"))
    if broker_snapshot_at is not None:
        broker_age_sec = now_epoch - broker_snapshot_at
    else:
        broker_age_sec = _safe_float(position_ctx.get("broker_snapshot_age_sec"))
        if broker_age_sec is None:
            broker_age_sec = _safe_float(position_ctx.get("holding_snapshot_age_sec"))
    broker_epoch = (
        broker_snapshot_at
        if broker_snapshot_at is not None
        else (
            now_epoch - broker_age_sec
            if broker_age_sec is not None and broker_age_sec >= 0
            else None
        )
    )
    broker_qty = next(
        (
            position_ctx.get(key)
            for key in ("broker_holding_qty", "verified_holding_qty", "broker_qty")
            if position_ctx.get(key) not in (None, "")
        ),
        None,
    )
    memory_qty = next(
        (
            explicit_position_ctx.get(key)
            for key in ("remaining_qty", "buy_qty", "qty")
            if explicit_position_ctx.get(key) not in (None, "")
        ),
        None,
    )
    broker_qty_value = _safe_float(broker_qty)
    memory_qty_value = _safe_float(memory_qty)
    open_orders = (
        {
            "open_buy_qty": position_ctx.get("open_buy_qty"),
            "open_sell_qty": position_ctx.get("open_sell_qty"),
        }
        if "open_buy_qty" in position_ctx and "open_sell_qty" in position_ctx
        else None
    )
    realtime_type_timestamps = _mapping(ws, "last_realtime_type_ts")
    realtime_type_suffixes = _mapping(ws, "last_realtime_type_market_suffix")
    realtime_type_routes = _mapping(ws, "last_realtime_type_market_route")
    explicit_program_context = "program_context" in ws
    program_epoch = _epoch(
        ws.get("program_observed_ts")
        if explicit_program_context
        else (realtime_type_timestamps.get("0w") or ws.get("last_prog_update_ts"))
    )
    received_types = {
        str(value or "").strip() for value in (ws.get("received_types") or [])
    }
    has_program_source = bool(
        explicit_program_context or "0w" in received_types or program_epoch is not None
    )
    program_value = (
        ws.get("program_context")
        if explicit_program_context
        else (
            {
                "net_qty": ws.get("prog_net_qty"),
                "delta_qty": ws.get("prog_delta_qty"),
                "net_amt": ws.get("prog_net_amt"),
                "delta_amt": ws.get("prog_delta_amt"),
                "buy_qty": ws.get("prog_buy_qty"),
                "sell_qty": ws.get("prog_sell_qty"),
                "buy_amt": ws.get("prog_buy_amt"),
                "sell_amt": ws.get("prog_sell_amt"),
            }
            if has_program_source
            else None
        )
    )
    program_suffix = (
        str(realtime_type_suffixes.get("0w") or "").upper()
        if program_epoch is not None
        else suffix
    )
    program_route = (
        str(realtime_type_routes.get("0w") or "").lower()
        if program_epoch is not None
        else route
    )
    program_freshness_limit_ms = max(
        _FRESH_MS,
        min(
            _safe_float(ws.get("program_freshness_limit_ms")) or _PROGRAM_FRESH_MS,
            300_000.0,
        ),
    )
    program_age_ms = (
        max(0.0, (now_epoch - program_epoch) * 1000.0)
        if program_epoch is not None
        else None
    )
    program_stale = bool(
        program_age_ms is not None and program_age_ms > program_freshness_limit_ms
    )
    program_missing_reason = str(
        "program_source_stale"
        if program_stale
        else (
            ws.get("program_missing_reason")
            or (
                "program_0w_awaiting_first_observation"
                if _epoch(ws.get("program_subscription_requested_at")) is not None
                else "program_source_missing"
            )
        )
    )
    if program_stale:
        # Optional source data must still obey the null-aware contract.  Do not
        # leave a stale numeric program value in the AI payload merely because
        # it is not a provider-call blocker.
        program_value = None
    investor_freshness_limit_ms = (
        _safe_float(ws.get("investor_freshness_limit_ms")) or 60_000.0
    )
    sources = {
        "current_price": _source_row(
            value=current_price if current_price and current_price > 0 else None,
            source=price_value_source,
            observed_epoch=price_value_epoch,
            now_epoch=now_epoch,
            market_suffix=tape_row.get("market_suffix", ""),
            market_route=tape_row.get("market_route", ""),
            missing_reason="current_price_missing_or_nonpositive",
        ),
        "bbo": _source_row(
            value=(
                {"best_bid": best_bid, "best_ask": best_ask}
                if best_bid and best_ask and best_bid > 0 and best_ask >= best_bid
                else None
            ),
            source=quote_value_source,
            observed_epoch=quote_value_epoch,
            now_epoch=now_epoch,
            market_suffix=quote_row.get("market_suffix", ""),
            market_route=quote_row.get("market_route", ""),
            missing_reason="valid_bbo_missing",
        ),
        "tape": _source_row(
            value=(
                {"realtime_type": "0B", "item": tape_row.get("item")}
                if tape_epoch is not None
                else None
            ),
            source="ws_0B",
            observed_epoch=tape_epoch,
            now_epoch=now_epoch,
            market_suffix=tape_row.get("market_suffix", ""),
            market_route=tape_row.get("market_route", ""),
            missing_reason="0B_provenance_missing",
        ),
        "candle": _source_row(
            value=(
                {
                    "schema": candle_ctx.get("schema"),
                    "status": candle_quality.get("status"),
                }
                if candle_ctx
                else None
            ),
            source="session_candle_source",
            observed_epoch=candle_epoch,
            now_epoch=now_epoch,
            market_suffix=suffix,
            market_route=route,
            missing_reason="candle_context_missing",
            freshness_limit_ms=_CANDLE_FRESH_MS,
        ),
        "program": _source_row(
            value=program_value,
            source=(
                str(ws.get("program_source") or "runtime_context")
                if explicit_program_context
                else "ws_0w"
            ),
            observed_epoch=program_epoch,
            now_epoch=now_epoch,
            market_suffix=program_suffix,
            market_route=program_route,
            missing_reason=program_missing_reason,
            freshness_limit_ms=program_freshness_limit_ms,
        ),
        "investor": _source_row(
            value=ws.get("investor_context") or None,
            source=str(ws.get("investor_source") or "runtime_context"),
            observed_epoch=_epoch(ws.get("investor_observed_ts")),
            now_epoch=now_epoch,
            market_suffix=str(
                ws.get("investor_market_suffix")
                if ws.get("investor_market_suffix") is not None
                else suffix
            ),
            market_route=str(ws.get("investor_market_route") or route),
            missing_reason=str(
                ws.get("investor_missing_reason") or "investor_source_missing"
            ),
            freshness_limit_ms=investor_freshness_limit_ms,
        ),
        "broker_position": _source_row(
            value=broker_qty,
            source=str(
                position_ctx.get("broker_snapshot_source") or "broker_position_snapshot"
            ),
            observed_epoch=broker_epoch,
            now_epoch=now_epoch,
            market_suffix=None,
            market_route=str(broker_route or ""),
            missing_reason="broker_position_snapshot_missing",
            freshness_limit_ms=_POSITION_FRESH_SEC * 1000.0,
        ),
        "open_orders": _source_row(
            value=open_orders,
            source=str(
                position_ctx.get("broker_snapshot_source")
                or "broker_open_order_snapshot"
            ),
            observed_epoch=broker_epoch,
            now_epoch=now_epoch,
            market_suffix=None,
            market_route=str(broker_route or ""),
            missing_reason="broker_open_orders_snapshot_missing",
            freshness_limit_ms=_POSITION_FRESH_SEC * 1000.0,
        ),
    }
    sources["broker_position"]["verification"] = position_ctx.get(
        "broker_position_verification"
    )
    sources["open_orders"]["verification"] = position_ctx.get(
        "broker_open_orders_verification"
    )
    integrated_sor_route_proven, integrated_sor_route_proof = (
        _integrated_sor_execution_view_proof(
            stock_code=stock_code,
            decision_stage=decision_stage,
            venue=normalized_venue,
            session=session_bucket,
            broker_route=str(broker_route or ""),
            candle_context=candle_ctx,
            position=position_ctx,
            provenance=provenance,
            now_epoch=now_epoch,
        )
    )
    (
        nxt_integrated_execution_view_proven,
        nxt_integrated_execution_view_proof,
    ) = _nxt_aftermarket_integrated_execution_view_proof(
        stock_code=stock_code,
        decision_stage=decision_stage,
        venue=normalized_venue,
        session=session_bucket,
        broker_route=str(broker_route or ""),
        candle_context=candle_ctx,
        position=position_ctx,
        provenance=provenance,
        now_epoch=now_epoch,
    )
    venue_consistent, venue_blockers = _venue_consistency(
        stock_code=stock_code,
        venue=normalized_venue,
        session=session_bucket,
        provenance=provenance,
        now_epoch=now_epoch,
        integrated_sor_execution_view_proven=integrated_sor_route_proven,
        nxt_integrated_execution_view_proven=(nxt_integrated_execution_view_proven),
    )
    blockers = list(venue_blockers)
    required_sources = ["current_price", "bbo", "tape"]
    if not any(
        token in stage_value for token in ("post_probe", "probe_recheck", "leg_reprice")
    ):
        required_sources.append("candle")
    for required_source in required_sources:
        quality = sources[required_source]["quality"]
        if quality in {"missing", "stale", "unknown_age", "future"}:
            blockers.append(f"{required_source}_{quality}")
    if (
        "candle" in required_sources
        and candle_ctx
        and candle_quality.get("status") != "fresh_consistent"
    ):
        blockers.append("candle_source_quality")
    position_reconciled = bool(
        broker_qty is not None
        and broker_age_sec is not None
        and broker_age_sec >= -(_FUTURE_TOLERANCE_MS / 1000.0)
        and broker_age_sec <= _POSITION_FRESH_SEC
        and open_orders is not None
    )
    simulation_position_reconciled = _simulation_position_reconciled(
        explicit_position_ctx
    )
    position_reconciliation_mode = (
        "simulation_book"
        if simulation_position_reconciled
        else ("broker_account" if require_position_reconciliation else "not_required")
    )
    position_authority_reconciled = bool(
        simulation_position_reconciled or position_reconciled
    )
    quality_warnings: list[str] = []
    optional_holding_reconciliation_advisory = bool(
        not require_position_reconciliation
        and not simulation_position_reconciled
        and explicit_position_is_active
        and stage_value in {"holding_score", "scalping_holding_score"}
    )
    if optional_holding_reconciliation_advisory and not position_reconciled:
        # A plain holding-score observation may remain provider-call eligible,
        # but it must not claim a fully fresh input when the attached broker
        # inventory/open-order snapshot is missing or older than its contract.
        # Submit-authority callers still use the hard blocker below.
        quality_warnings.append("broker_position_or_open_orders_stale_advisory")
    venue_value = normalized_venue
    broker_route_value = str(broker_route or "").strip().upper()
    broker_route_matches = _broker_route_matches_cohort(
        broker_route=broker_route_value,
        venue_cohort=venue_value,
        session=session_bucket,
    )
    broker_route_match_state = (
        "missing"
        if not broker_route_value
        else ("matched" if broker_route_matches else "mismatched")
    )
    if (
        optional_holding_reconciliation_advisory
        and broker_qty_value is not None
        and memory_qty_value is not None
        and broker_qty_value != memory_qty_value
    ):
        quality_warnings.append("broker_position_quantity_mismatch_advisory")
    if optional_holding_reconciliation_advisory and not broker_route_matches:
        quality_warnings.append("broker_route_venue_mismatch_or_missing_advisory")
    if require_position_reconciliation and not position_authority_reconciled:
        blockers.append("broker_position_or_open_orders_unreconciled")
    if (
        require_position_reconciliation
        and not simulation_position_reconciled
        and explicit_position_is_active
        and broker_qty_value is not None
        and memory_qty_value is not None
        and broker_qty_value != memory_qty_value
    ):
        blockers.append("broker_position_quantity_mismatch")
    if (
        require_position_reconciliation
        and not simulation_position_reconciled
        and not broker_route_matches
    ):
        blockers.append("broker_route_venue_mismatch_or_missing")
    observed_epochs = [
        value
        for value in (quote_value_epoch, tape_epoch)
        if isinstance(value, (int, float))
    ]
    max_skew_ms = (
        round((max(observed_epochs) - min(observed_epochs)) * 1000.0, 3)
        if len(observed_epochs) >= 2
        else None
    )
    if max_skew_ms is not None and max_skew_ms > _FRESH_MS:
        blockers.append("source_time_skew")
    source_blockers = sorted(set(blockers))
    preflight_required = runtime_preflight_required()
    preflight_mode = runtime_preflight_mode()
    artifact_status = (
        runtime_preflight_artifact_status(now_ts=now_epoch)
        if preflight_required
        else {
            "ready": False,
            "status": "not_required",
            "mode": preflight_mode,
            "target_date": None,
            "artifact": None,
        }
    )
    if preflight_required and not artifact_status["ready"]:
        blockers.append("runtime_preflight_artifact_not_ready")
    blockers = sorted(set(blockers))
    missing_sources = [
        name for name, row in sources.items() if row.get("value") is None
    ]
    status = (
        "blocked"
        if blockers
        else ("partial" if missing_sources or quality_warnings else "fresh_consistent")
    )
    preflight = {
        "schema": PREFLIGHT_SCHEMA,
        "allowed": not blockers,
        "source_allowed": not source_blockers,
        "status": status,
        "blockers": blockers,
        "source_blockers": source_blockers,
        "quality_warnings": quality_warnings,
        "missing_sources": missing_sources,
        "venue_consistent": venue_consistent,
        "position_reconciled": position_reconciled,
        "position_authority_reconciled": position_authority_reconciled,
        "position_reconciliation_mode": position_reconciliation_mode,
        "simulation_position_reconciled": simulation_position_reconciled,
        "broker_route_matches_venue": broker_route_matches,
        "broker_route_match_state": broker_route_match_state,
        "max_source_skew_ms": max_skew_ms,
    }
    integrated_sor_execution_view_only = bool(
        integrated_sor_route_proven and underlying_event_venue is None
    )
    nxt_integrated_execution_view_only = bool(
        nxt_integrated_execution_view_proven and underlying_event_venue is None
    )
    venue_attribution_allowed = bool(
        underlying_event_venue in {"KRX", "NXT"}
        and venue_consistent
        and not source_blockers
    )
    venue_attribution_reason = (
        "exact_per_realtime_type"
        if venue_attribution_allowed
        else (
            "integrated_sor_execution_view_not_event_venue"
            if integrated_sor_execution_view_only
            else (
                "nxt_integrated_execution_view_not_event_venue"
                if nxt_integrated_execution_view_only
                else (
                    "source_quality_blocked_even_with_event_venue"
                    if underlying_event_venue in {"KRX", "NXT"}
                    else underlying_event_venue_source
                )
            )
        )
    )
    snapshot_identity = {
        "captured_at": _iso(now_epoch),
        "decision_stage": decision_stage,
        "stock_code": _base_code(stock_code),
        "effective_venue": normalized_venue,
        "effective_venue_input": effective_venue,
        "venue_resolution": venue_resolution,
        "broker_route": broker_route_value or None,
        "broker_route_match_state": broker_route_match_state,
        "position_reconciliation_mode": position_reconciliation_mode,
        "simulation_position_reconciled": simulation_position_reconciled,
        "market_data_route": market_data_route,
        "underlying_event_venue": underlying_event_venue,
        "underlying_event_venue_source": underlying_event_venue_source,
        "integrated_sor_route_proven": integrated_sor_route_proven,
        "integrated_sor_route_proof": integrated_sor_route_proof,
        "integrated_sor_execution_view_only": integrated_sor_execution_view_only,
        "nxt_integrated_execution_view_proven": (nxt_integrated_execution_view_proven),
        "nxt_integrated_execution_view_proof": nxt_integrated_execution_view_proof,
        "nxt_integrated_execution_view_only": nxt_integrated_execution_view_only,
        "venue_attribution_allowed": venue_attribution_allowed,
        "venue_attribution_reason": venue_attribution_reason,
        "session_bucket": session_bucket,
        "route_partition": route_partition,
        "provenance": provenance,
    }
    digest = hashlib.sha256(
        json.dumps(snapshot_identity, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:20]
    return {
        "schema": SCHEMA,
        "snapshot_id": f"aims-{digest}",
        "captured_at": _iso(now_epoch),
        "decision_stage": decision_stage,
        "stock_code": _base_code(stock_code),
        "effective_venue": normalized_venue,
        "effective_venue_input": effective_venue,
        "venue_resolution": venue_resolution,
        "broker_route": broker_route_value or None,
        "broker_route_match_state": broker_route_match_state,
        "position_reconciliation_mode": position_reconciliation_mode,
        "simulation_position_reconciled": simulation_position_reconciled,
        "market_data_route": market_data_route,
        "underlying_event_venue": underlying_event_venue,
        "underlying_event_venue_source": underlying_event_venue_source,
        "integrated_sor_route_proven": integrated_sor_route_proven,
        "integrated_sor_route_proof": integrated_sor_route_proof,
        "integrated_sor_execution_view_only": integrated_sor_execution_view_only,
        "nxt_integrated_execution_view_proven": (nxt_integrated_execution_view_proven),
        "nxt_integrated_execution_view_proof": nxt_integrated_execution_view_proof,
        "nxt_integrated_execution_view_only": nxt_integrated_execution_view_only,
        "venue_attribution_allowed": venue_attribution_allowed,
        "venue_attribution_reason": venue_attribution_reason,
        "session_bucket": session_bucket,
        "route_partition": route_partition,
        "required_sources": required_sources,
        "realtime_type_provenance": provenance,
        "sources": sources,
        "max_source_skew_ms": max_skew_ms,
        "executable_quote_reanchor": {
            "applied": rest_quote_reanchor,
            "source": effective_quote_source or "ws",
            "freshness_state": effective_quote_state or "not_provided",
            "observed_epoch": effective_quote_epoch,
            "request_code": str(
                ws.get("market_data_effective_quote_request_code") or ""
            ).strip()
            or None,
            "authority": "quote_and_current_price_only",
            "tape_or_event_venue_authority": False,
        },
        "quality": status,
        "ai_input_preflight_v1": preflight,
        "runtime_preflight_mode": preflight_mode,
        "runtime_preflight_artifact": artifact_status,
        "observation_contract": OBSERVATION_CONTRACT,
    }


def ai_input_preflight(
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    source = context if isinstance(context, dict) else {}
    snapshot = source.get("ai_market_snapshot_v1")
    if not isinstance(snapshot, dict) and source.get("schema") == SCHEMA:
        snapshot = source
    preflight = (
        snapshot.get("ai_input_preflight_v1") if isinstance(snapshot, dict) else None
    )
    if isinstance(preflight, dict):
        return preflight
    return {
        "schema": PREFLIGHT_SCHEMA,
        "allowed": False,
        "source_allowed": False,
        "status": "blocked",
        "blockers": ["ai_market_snapshot_missing"],
        "missing_sources": ["ai_market_snapshot_v1"],
        "venue_consistent": False,
        "position_reconciled": False,
        "position_authority_reconciled": False,
        "position_reconciliation_mode": "missing_snapshot",
        "simulation_position_reconciled": False,
        "broker_route_matches_venue": False,
        "broker_route_match_state": "missing_snapshot",
        "max_source_skew_ms": None,
    }


def ai_market_snapshot_log_fields(
    context: dict[str, Any] | None,
    *,
    observation_contract_prefix: str = "",
) -> dict[str, Any]:
    source = context if isinstance(context, dict) else {}
    snapshot = source.get("ai_market_snapshot_v1")
    if not isinstance(snapshot, dict) and source.get("schema") == SCHEMA:
        snapshot = source
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    preflight = ai_input_preflight(snapshot)
    quote_reanchor = (
        snapshot.get("executable_quote_reanchor")
        if isinstance(snapshot.get("executable_quote_reanchor"), dict)
        else {}
    )
    contract_fields = {
        f"{observation_contract_prefix}{key}": value
        for key, value in OBSERVATION_CONTRACT.items()
    }
    return {
        "ai_market_snapshot_schema": snapshot.get("schema", SCHEMA),
        "ai_market_snapshot_id": snapshot.get("snapshot_id"),
        "ai_market_snapshot_captured_at": snapshot.get("captured_at"),
        "ai_market_snapshot_decision_stage": snapshot.get("decision_stage"),
        "ai_market_snapshot_stock_code": snapshot.get("stock_code"),
        "ai_market_snapshot_effective_venue": snapshot.get("effective_venue"),
        "ai_market_snapshot_effective_venue_input": snapshot.get(
            "effective_venue_input"
        ),
        "ai_market_snapshot_venue_resolution": snapshot.get("venue_resolution"),
        "ai_market_snapshot_broker_route": snapshot.get("broker_route"),
        "ai_market_snapshot_broker_route_match_state": snapshot.get(
            "broker_route_match_state"
        ),
        "ai_market_snapshot_market_data_route": snapshot.get("market_data_route"),
        "ai_market_snapshot_route_partition_used": bool(
            (snapshot.get("route_partition") or {}).get("used", False)
        ),
        "ai_market_snapshot_route_partition_reason": (
            (snapshot.get("route_partition") or {}).get("reason")
        ),
        "ai_market_snapshot_route_partition_selected_key": (
            (snapshot.get("route_partition") or {}).get("selected_key")
        ),
        "ai_market_snapshot_underlying_event_venue": snapshot.get(
            "underlying_event_venue"
        ),
        "ai_market_snapshot_underlying_event_venue_source": snapshot.get(
            "underlying_event_venue_source"
        ),
        "ai_market_snapshot_integrated_sor_route_proven": bool(
            snapshot.get("integrated_sor_route_proven", False)
        ),
        "ai_market_snapshot_integrated_sor_route_proof": snapshot.get(
            "integrated_sor_route_proof"
        ),
        "ai_market_snapshot_integrated_sor_execution_view_only": bool(
            snapshot.get("integrated_sor_execution_view_only", False)
        ),
        "ai_market_snapshot_nxt_integrated_execution_view_proven": bool(
            snapshot.get("nxt_integrated_execution_view_proven", False)
        ),
        "ai_market_snapshot_nxt_integrated_execution_view_proof": snapshot.get(
            "nxt_integrated_execution_view_proof"
        ),
        "ai_market_snapshot_nxt_integrated_execution_view_only": bool(
            snapshot.get("nxt_integrated_execution_view_only", False)
        ),
        "ai_market_snapshot_venue_attribution_allowed": bool(
            snapshot.get("venue_attribution_allowed", False)
        ),
        "ai_market_snapshot_venue_attribution_reason": snapshot.get(
            "venue_attribution_reason"
        ),
        "ai_market_snapshot_session_bucket": snapshot.get("session_bucket"),
        "ai_market_snapshot_executable_quote_reanchor_applied": bool(
            quote_reanchor.get("applied", False)
        ),
        "ai_market_snapshot_executable_quote_reanchor_source": quote_reanchor.get(
            "source"
        ),
        "ai_market_snapshot_executable_quote_reanchor_request_code": (
            quote_reanchor.get("request_code")
        ),
        "ai_market_snapshot_executable_quote_reanchor_authority": (
            quote_reanchor.get("authority")
        ),
        "ai_market_snapshot_executable_quote_reanchor_tape_or_event_venue_authority": bool(
            quote_reanchor.get("tape_or_event_venue_authority", False)
        ),
        "ai_input_preflight_schema": preflight.get("schema", PREFLIGHT_SCHEMA),
        "ai_input_preflight_allowed": bool(preflight.get("allowed", False)),
        "ai_input_preflight_source_allowed": bool(
            preflight.get("source_allowed", False)
        ),
        "ai_input_preflight_status": preflight.get("status"),
        "ai_input_preflight_blockers": preflight.get("blockers", []),
        "ai_input_preflight_quality_warnings": preflight.get("quality_warnings", []),
        "ai_input_preflight_missing_sources": preflight.get("missing_sources", []),
        "ai_input_preflight_venue_consistent": bool(
            preflight.get("venue_consistent", False)
        ),
        "ai_input_preflight_position_reconciled": bool(
            preflight.get("position_reconciled", False)
        ),
        "ai_input_preflight_position_authority_reconciled": bool(
            preflight.get("position_authority_reconciled", False)
        ),
        "ai_input_preflight_position_reconciliation_mode": preflight.get(
            "position_reconciliation_mode"
        ),
        "ai_input_preflight_simulation_position_reconciled": bool(
            preflight.get("simulation_position_reconciled", False)
        ),
        "ai_input_preflight_broker_route_matches_venue": bool(
            preflight.get("broker_route_matches_venue", False)
        ),
        "ai_input_preflight_broker_route_match_state": preflight.get(
            "broker_route_match_state"
        ),
        "ai_input_preflight_max_source_skew_ms": preflight.get("max_source_skew_ms"),
        "ai_input_runtime_preflight_mode": snapshot.get(
            "runtime_preflight_mode", runtime_preflight_mode()
        ),
        "ai_input_runtime_preflight_artifact_status": (
            snapshot.get("runtime_preflight_artifact", {}).get("status")
            if isinstance(snapshot.get("runtime_preflight_artifact"), dict)
            else None
        ),
        "ai_market_snapshot_missing_as_zero": False,
        **contract_fields,
    }


def _legacy_runtime_preflight_required() -> bool:
    return str(
        os.getenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED", "false")
    ).strip().lower() in {"1", "true", "yes", "on"}


def runtime_preflight_mode() -> str:
    explicit = (
        str(os.getenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "")).strip().lower()
    )
    aliases = {
        "": "",
        "0": "off",
        "false": "off",
        "off": "off",
        "baseline": "baseline_v1",
        "baseline_v1": "baseline_v1",
        "exact": "exact_v2",
        "exact_v2": "exact_v2",
    }
    if explicit:
        return aliases.get(explicit, "invalid")
    return "exact_v2" if _legacy_runtime_preflight_required() else "off"


def runtime_preflight_required() -> bool:
    return runtime_preflight_mode() != "off"


def _baseline_artifact_contract_ready(payload: dict[str, Any]) -> bool:
    contract = (
        payload.get("observation_contract")
        if isinstance(payload.get("observation_contract"), dict)
        else {}
    )
    return bool(
        payload.get("schema") == "ai_input_quality_baseline_v1"
        and payload.get("policy_version") == "baseline_v1"
        and payload.get("status") == "ready_baseline_v1"
        and payload.get("allowed_runtime_apply") is True
        and payload.get("runtime_effect") == "protective_fail_closed_only"
        and payload.get("can_open_order_authority") is False
        and payload.get("can_relax_threshold") is False
        and payload.get("can_change_provider") is False
        and contract.get("decision_authority") == "source_quality_fail_closed_only"
    )


def runtime_preflight_artifact_status(
    *,
    now_ts: float | None = None,
) -> dict[str, Any]:
    mode = runtime_preflight_mode()
    if mode == "invalid":
        return {
            "ready": False,
            "status": "runtime_preflight_mode_invalid",
            "mode": mode,
            "target_date": None,
            "artifact": None,
        }
    if mode == "off":
        return {
            "ready": False,
            "status": "not_required",
            "mode": mode,
            "target_date": None,
            "artifact": None,
        }
    date_env_key = (
        "KORSTOCKSCAN_AI_INPUT_BASELINE_ARTIFACT_DATE"
        if mode == "baseline_v1"
        else "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE"
    )
    target_date = str(os.getenv(date_env_key, "")).strip()
    if not target_date:
        target_date = (
            datetime.fromtimestamp(
                float(now_ts if now_ts is not None else time.time()), tz=KST
            )
            .date()
            .isoformat()
        )
    if mode == "exact_v2":
        now_value = float(now_ts if now_ts is not None else time.time())
        activation = promotion_activation_state(
            datetime.fromtimestamp(now_value, tz=KST)
        )
        if (
            activation.get("active") is True
            and activation.get("promotion_mode") == "operator_directed_full_promotion"
            and activation.get("target_date") == target_date
        ):
            return {
                "ready": True,
                "status": "ready_operator_directed_exact_v2",
                "mode": mode,
                "target_date": target_date,
                "artifact": activation.get("promotion_artifact"),
                "promotion_sha256": activation.get("promotion_sha256"),
                "promotion_mode": activation.get("promotion_mode"),
                "validation_gate_bypassed": True,
                "not_ready_rows": [],
            }
    if mode == "baseline_v1":
        path = _BASELINE_REPORT_DIR / f"ai_input_quality_baseline_{target_date}.json"
    else:
        path = (
            _PREFLIGHT_REPORT_DIR / f"entry_context_intraday_probe_{target_date}.json"
        )
    if not path.exists():
        return {
            "ready": False,
            "status": "artifact_missing",
            "mode": mode,
            "target_date": target_date,
            "artifact": str(path),
        }
    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        return {
            "ready": False,
            "status": "artifact_stat_failed",
            "mode": mode,
            "target_date": target_date,
            "artifact": str(path),
            "error": f"{type(exc).__name__}:{str(exc)[:120]}",
        }
    cache_key = (mode, str(path), artifact_mtime, _PROCESS_STARTED_AT)
    cached = _ARTIFACT_STATUS_CACHE.get(cache_key)
    if isinstance(cached, dict):
        return dict(cached)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        result = {
            "ready": False,
            "status": "artifact_invalid",
            "mode": mode,
            "target_date": target_date,
            "artifact": str(path),
            "error": f"{type(exc).__name__}:{str(exc)[:120]}",
        }
        _ARTIFACT_STATUS_CACHE.clear()
        _ARTIFACT_STATUS_CACHE[cache_key] = dict(result)
        return result
    if not isinstance(payload, dict):
        payload = {}
    if mode == "baseline_v1":
        contract_ready = _baseline_artifact_contract_ready(payload)
        status = (
            "ready_baseline_v1" if contract_ready else "baseline_contract_not_ready"
        )
        not_ready_rows: list[Any] = []
    else:
        matrix = (
            payload.get("venue_preflight_matrix")
            if isinstance(payload.get("venue_preflight_matrix"), dict)
            else {}
        )
        status = str(matrix.get("overall_status") or "not_ready")
        contract_ready = status == "ready"
        not_ready_rows = matrix.get("not_ready_rows", [])
    ready_pending_restart = bool(
        contract_ready and artifact_mtime > _PROCESS_STARTED_AT
    )
    result = {
        "ready": contract_ready and not ready_pending_restart,
        "status": "ready_pending_restart" if ready_pending_restart else status,
        "mode": mode,
        "target_date": target_date,
        "artifact": str(path),
        "artifact_mtime": artifact_mtime,
        "process_started_at": _PROCESS_STARTED_AT,
        "not_ready_rows": not_ready_rows,
    }
    _ARTIFACT_STATUS_CACHE.clear()
    _ARTIFACT_STATUS_CACHE[cache_key] = dict(result)
    return result
