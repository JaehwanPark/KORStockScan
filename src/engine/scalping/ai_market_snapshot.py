"""Source-quality contract shared by real scalping AI decision points.

This module is an instrumentation and fail-closed preflight owner.  It cannot
select a provider/model, create BUY/HOLD authority, choose price/quantity, or
bypass deterministic trading guards.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

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
    required source is consistently integrated.  Entry proof is limited to
    regular-session AI context/gatekeeper decisions; post-probe remains
    excluded because it must preserve the probe's exact venue lineage.
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
    rows = [provenance[key] for key in _MARKET_TYPES]
    candle_schema = str(candle_context.get("schema") or "").strip()
    conditions = {
        "supported_stage": holding_stage or entry_stage,
        "stage_position_contract": (
            _active_holding_position(position) if holding_stage else entry_stage
        ),
        "krx_regular_cohort": str(venue or "").strip().upper() == "KRX"
        and session_value == "krx_regular"
        and datetime.strptime("09:00", "%H:%M").time()
        <= clock
        <= datetime.strptime("15:30", "%H:%M").time(),
        "sor_broker_route": str(broker_route or "").strip().upper() == "SOR",
        "integrated_candle_route": (
            candle_schema in {"session_candle_source_v1", "entry_candle_context_v1"}
            and _base_code(candle_context.get("request_code")) == _base_code(stock_code)
            and str(candle_context.get("rest_route") or "").strip().upper() == "_AL"
            and str(candle_context.get("ws_route") or "").strip().lower()
            == "krx_nxt_integrated"
            and candle_quality.get("status") == "fresh_consistent"
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
    return True, "entry_sor_integrated_execution_view"


def _venue_consistency(
    *,
    stock_code: str,
    venue: str,
    session: str,
    provenance: dict[str, dict[str, Any]],
    now_epoch: float,
    integrated_sor_execution_view_proven: bool = False,
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
                and str(row.get("effective_venue") or "").strip().upper() == "NXT"
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
    ws = ws_data if isinstance(ws_data, dict) else {}
    position_ctx = position if isinstance(position, dict) else {}
    candle_ctx = candle_context if isinstance(candle_context, dict) else {}
    now_epoch = float(now_ts if now_ts is not None else time.time())
    normalized_venue, venue_resolution = _normalize_venue_cohort(
        venue=effective_venue,
        session=session_bucket,
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
    open_orders = (
        {
            "open_buy_qty": position_ctx.get("open_buy_qty"),
            "open_sell_qty": position_ctx.get("open_sell_qty"),
        }
        if "open_buy_qty" in position_ctx and "open_sell_qty" in position_ctx
        else None
    )
    sources = {
        "current_price": _source_row(
            value=current_price if current_price and current_price > 0 else None,
            source="ws_0B",
            observed_epoch=tape_epoch,
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
            source="ws_0D",
            observed_epoch=quote_epoch,
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
            value=(
                ws.get("program_context")
                if "program_context" in ws
                else ws.get("program_net_qty")
            ),
            source="runtime_context",
            observed_epoch=_epoch(ws.get("program_observed_ts")),
            now_epoch=now_epoch,
            market_suffix=suffix,
            market_route=route,
            missing_reason="program_source_missing",
        ),
        "investor": _source_row(
            value=ws.get("investor_context") or None,
            source="runtime_context",
            observed_epoch=_epoch(ws.get("investor_observed_ts")),
            now_epoch=now_epoch,
            market_suffix=suffix,
            market_route=route,
            missing_reason="investor_source_missing",
        ),
        "broker_position": _source_row(
            value=broker_qty,
            source="broker_position_snapshot",
            observed_epoch=broker_epoch,
            now_epoch=now_epoch,
            market_suffix=None,
            market_route=str(broker_route or ""),
            missing_reason="broker_position_snapshot_missing",
        ),
        "open_orders": _source_row(
            value=open_orders,
            source="broker_open_order_snapshot",
            observed_epoch=broker_epoch,
            now_epoch=now_epoch,
            market_suffix=None,
            market_route=str(broker_route or ""),
            missing_reason="broker_open_orders_snapshot_missing",
        ),
    }
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
    venue_consistent, venue_blockers = _venue_consistency(
        stock_code=stock_code,
        venue=normalized_venue,
        session=session_bucket,
        provenance=provenance,
        now_epoch=now_epoch,
        integrated_sor_execution_view_proven=integrated_sor_route_proven,
    )
    blockers = list(venue_blockers)
    stage_value = str(decision_stage or "").strip().lower()
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
    venue_value = normalized_venue
    broker_route_value = str(broker_route or "").strip().upper()
    broker_route_matches = _broker_route_matches_cohort(
        broker_route=broker_route_value,
        venue_cohort=venue_value,
        session=session_bucket,
    )
    if require_position_reconciliation and not position_reconciled:
        blockers.append("broker_position_or_open_orders_unreconciled")
    if require_position_reconciliation and not broker_route_matches:
        blockers.append("broker_route_venue_mismatch_or_missing")
    observed_epochs = [
        value for value in (quote_epoch, tape_epoch) if isinstance(value, (int, float))
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
        else ("partial" if missing_sources else "fresh_consistent")
    )
    preflight = {
        "schema": PREFLIGHT_SCHEMA,
        "allowed": not blockers,
        "source_allowed": not source_blockers,
        "status": status,
        "blockers": blockers,
        "source_blockers": source_blockers,
        "missing_sources": missing_sources,
        "venue_consistent": venue_consistent,
        "position_reconciled": position_reconciled,
        "broker_route_matches_venue": broker_route_matches,
        "max_source_skew_ms": max_skew_ms,
    }
    integrated_sor_execution_view_only = bool(
        integrated_sor_route_proven and underlying_event_venue is None
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
                "source_quality_blocked_even_with_event_venue"
                if underlying_event_venue in {"KRX", "NXT"}
                else underlying_event_venue_source
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
        "market_data_route": market_data_route,
        "underlying_event_venue": underlying_event_venue,
        "underlying_event_venue_source": underlying_event_venue_source,
        "integrated_sor_route_proven": integrated_sor_route_proven,
        "integrated_sor_route_proof": integrated_sor_route_proof,
        "integrated_sor_execution_view_only": integrated_sor_execution_view_only,
        "venue_attribution_allowed": venue_attribution_allowed,
        "venue_attribution_reason": venue_attribution_reason,
        "session_bucket": session_bucket,
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
        "market_data_route": market_data_route,
        "underlying_event_venue": underlying_event_venue,
        "underlying_event_venue_source": underlying_event_venue_source,
        "integrated_sor_route_proven": integrated_sor_route_proven,
        "integrated_sor_route_proof": integrated_sor_route_proof,
        "integrated_sor_execution_view_only": integrated_sor_execution_view_only,
        "venue_attribution_allowed": venue_attribution_allowed,
        "venue_attribution_reason": venue_attribution_reason,
        "session_bucket": session_bucket,
        "required_sources": required_sources,
        "realtime_type_provenance": provenance,
        "sources": sources,
        "max_source_skew_ms": max_skew_ms,
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
        "broker_route_matches_venue": False,
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
        "ai_market_snapshot_market_data_route": snapshot.get("market_data_route"),
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
        "ai_market_snapshot_venue_attribution_allowed": bool(
            snapshot.get("venue_attribution_allowed", False)
        ),
        "ai_market_snapshot_venue_attribution_reason": snapshot.get(
            "venue_attribution_reason"
        ),
        "ai_market_snapshot_session_bucket": snapshot.get("session_bucket"),
        "ai_input_preflight_schema": preflight.get("schema", PREFLIGHT_SCHEMA),
        "ai_input_preflight_allowed": bool(preflight.get("allowed", False)),
        "ai_input_preflight_source_allowed": bool(
            preflight.get("source_allowed", False)
        ),
        "ai_input_preflight_status": preflight.get("status"),
        "ai_input_preflight_blockers": preflight.get("blockers", []),
        "ai_input_preflight_missing_sources": preflight.get("missing_sources", []),
        "ai_input_preflight_venue_consistent": bool(
            preflight.get("venue_consistent", False)
        ),
        "ai_input_preflight_position_reconciled": bool(
            preflight.get("position_reconciled", False)
        ),
        "ai_input_preflight_broker_route_matches_venue": bool(
            preflight.get("broker_route_matches_venue", False)
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
