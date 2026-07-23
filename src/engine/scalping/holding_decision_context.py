"""Bounded, venue-aware context for scalping holding and exit confirmation.

This module may confirm an existing HOLD/TRIM preference only when its critical
sources are fresh and consistent.  It cannot create an exit, choose order
price/quantity, defer hard safety, mutate thresholds, or change provider route.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, time as dt_time
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.scalping.entry_candle_context import build_session_candle_source
from src.engine.scalping.market_data_enrichment import (
    rest_signed_tape_tick_freshness,
)

SCHEMA = "holding_decision_context_v1"
KST = ZoneInfo("Asia/Seoul")
OBSERVATION_CONTRACT = {
    "metric_role": "holding_context_feature_bundle",
    "decision_authority": "bounded_holding_confirmation",
    "window_policy": "current_session_1m_3m_5m_10m_20m_60m",
    "sample_floor": "session_and_decision_kind_aware",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "fresh_venue_consistent_candles_quote_and_position",
    "forbidden_uses": [
        "hard_protect_emergency_exit_deferral",
        "direct_order_price_or_quantity",
        "broker_guard_bypass",
        "cross_venue_evidence",
        "provider_or_threshold_mutation",
    ],
}

_STAGE_ENV = {
    "holding_score": "KORSTOCKSCAN_HOLDING_SCORE_CONTEXT_ENABLED",
    "holding_flow": "KORSTOCKSCAN_HOLDING_FLOW_CONTEXT_ENABLED",
    "overnight": "KORSTOCKSCAN_OVERNIGHT_CONTEXT_ENABLED",
}
_UNUSABLE_TAPE_STATES = {"missing", "insufficient", "stale", "conflicted"}
_KNOWN_OFI_STATES = {
    "stable_bullish",
    "stable_bearish",
    "transition",
    "neutral",
    "bullish",
    "bearish",
}
_REST_TAPE_TTL_SEC = 3.0
_REST_TAPE_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_REST_TAPE_CACHE_LOCK = threading.Lock()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    parsed = _safe_float(value, float(default))
    return int(parsed if parsed is not None else default)


def _first_present(source: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in source and source.get(key) not in (None, ""):
            return source.get(key)
    return default


def _now_kst(now_ts: Any = None) -> datetime:
    if isinstance(now_ts, datetime):
        if now_ts.tzinfo is None:
            return now_ts.replace(tzinfo=KST)
        return now_ts.astimezone(KST)
    if now_ts is None:
        return datetime.now(KST)
    return datetime.fromtimestamp(float(now_ts), tz=KST)


def _cohort(venue: str, session: str) -> str:
    venue_value = str(venue or "").upper()
    session_value = str(session or "").lower()
    if "PREMARKET" in venue_value or "premarket" in session_value:
        return "PREMARKET"
    if "NXT" in venue_value or session_value.startswith("nxt_"):
        return "NXT"
    return "KRX"


def holding_decision_context_enabled(
    *,
    venue: str,
    session: str,
    decision_kind: str,
    now_ts: Any = None,
) -> bool:
    if not _env_bool("KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED", False):
        return False
    active_date = str(
        os.getenv("KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE", "")
    ).strip()
    if active_date and _now_kst(now_ts).date().isoformat() != active_date:
        return False
    cohort = _cohort(venue, session)
    if not _env_bool(f"KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_{cohort}_ENABLED", False):
        return False
    stage = (
        "overnight"
        if "overnight" in str(decision_kind or "").lower()
        else (
            "holding_score"
            if "score" in str(decision_kind or "").lower()
            else "holding_flow"
        )
    )
    return _env_bool(_STAGE_ENV[stage], False)


def _age_ms_from_epoch(value: Any, now_epoch: float) -> float | None:
    parsed = _safe_float(value, None)
    if parsed is None or parsed <= 0:
        return None
    if parsed > 10_000_000_000:
        parsed /= 1000.0
    return max(0.0, (now_epoch - parsed) * 1000.0)


def _quote_age_ms(
    ws_data: dict[str, Any], now_epoch: float
) -> tuple[float | None, str]:
    for key in ("last_ws_update_ts", "received_at", "received_ts", "timestamp", "ts"):
        if key in ws_data:
            age = _age_ms_from_epoch(ws_data.get(key), now_epoch)
            if age is not None:
                return age, f"absolute_timestamp:{key}"
    for key in ("quote_age_ms", "ws_age_ms", "pre_ai_ws_snapshot_refresh_age_ms"):
        parsed = _safe_float(ws_data.get(key), None)
        if parsed is not None and parsed >= 0:
            return parsed, f"reported_age:{key}"
    return None, "missing"


def _best_levels(ws_data: dict[str, Any]) -> dict[str, int]:
    orderbook = (
        ws_data.get("orderbook") if isinstance(ws_data.get("orderbook"), dict) else {}
    )
    asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
    bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
    ask_row = asks[0] if asks and isinstance(asks[0], dict) else {}
    bid_row = bids[0] if bids and isinstance(bids[0], dict) else {}
    return {
        "best_ask": abs(
            _safe_int(
                ws_data.get("best_ask")
                or ws_data.get("ask_price")
                or ask_row.get("price"),
                0,
            )
        ),
        "best_bid": abs(
            _safe_int(
                ws_data.get("best_bid")
                or ws_data.get("bid_price")
                or bid_row.get("price"),
                0,
            )
        ),
        "best_ask_qty": abs(
            _safe_int(
                ws_data.get("best_ask_qty")
                or ws_data.get("ask_qty")
                or ask_row.get("qty")
                or ask_row.get("volume"),
                0,
            )
        ),
        "best_bid_qty": abs(
            _safe_int(
                ws_data.get("best_bid_qty")
                or ws_data.get("bid_qty")
                or bid_row.get("qty")
                or bid_row.get("volume"),
                0,
            )
        ),
    }


def _request_suffix(request_code: str) -> str:
    upper = str(request_code or "").upper()
    if upper.endswith("_NX"):
        return "_NX"
    if upper.endswith("_AL"):
        return "_AL"
    return ""


def _tick_route_compatible(
    tick: dict[str, Any], *, request_suffix: str, ws_route: str
) -> bool:
    tick_suffix = str(tick.get("market_suffix") or "").upper()
    tick_route = str(tick.get("market_route") or "").lower()
    if request_suffix and not tick_suffix:
        return False
    if ws_route and not tick_route:
        return False
    if request_suffix and tick_suffix and tick_suffix != request_suffix:
        if not (
            request_suffix == "_NX"
            and tick_suffix == "_AL"
            and ws_route == "krx_nxt_integrated"
        ):
            return False
    if not request_suffix and tick_suffix:
        return False
    if ws_route and tick_route and tick_route != ws_route:
        return False
    return True


def _tick_age_ms(tick: dict[str, Any], now_epoch: float) -> float | None:
    for key in (
        "received_at_ms",
        "received_timestamp_ms",
        "received_at",
        "received_ts",
        "timestamp",
        "ts",
    ):
        age = _age_ms_from_epoch(tick.get(key), now_epoch)
        if age is not None:
            return age
    return None


def _trusted_ws_tape(
    ticks: list[dict[str, Any]],
    *,
    request_suffix: str,
    ws_route: str,
    now_epoch: float,
    max_age_ms: float = 3000.0,
) -> dict[str, Any]:
    buy_volume = sell_volume = buy_count = sell_count = 0
    ages: list[float] = []
    route_conflicts = 0
    for tick in ticks:
        if not isinstance(tick, dict):
            continue
        if not _tick_route_compatible(
            tick, request_suffix=request_suffix, ws_route=ws_route
        ):
            route_conflicts += 1
            continue
        source = str(
            tick.get("aggressor_source") or tick.get("side_source") or ""
        ).lower()
        if source == "price_change_heuristic":
            continue
        side = str(tick.get("aggressor_side") or tick.get("side") or "").upper()
        if side not in {"BUY", "SELL"}:
            continue
        age = _tick_age_ms(tick, now_epoch)
        if age is None or age > max_age_ms:
            continue
        qty = abs(
            _safe_int(
                tick.get("aggressor_volume")
                or tick.get("volume")
                or tick.get("qty")
                or tick.get("signed_trade_volume"),
                0,
            )
        )
        if qty <= 0:
            continue
        ages.append(age)
        if side == "BUY":
            buy_count += 1
            buy_volume += qty
        else:
            sell_count += 1
            sell_volume += qty
    sample_count = buy_count + sell_count
    total_volume = buy_volume + sell_volume
    buy_ratio = (
        round(buy_volume / total_volume * 100.0, 3) if total_volume > 0 else None
    )
    if sample_count < 3:
        state = "insufficient" if sample_count else "missing"
    elif buy_volume > sell_volume:
        state = "buy_dominated"
    elif sell_volume > buy_volume:
        state = "sell_dominated"
    else:
        state = "mixed"
    return {
        "state": state,
        "source": "ws_trusted_aggressor" if sample_count else "missing",
        "sample_count": sample_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "buy_ratio_pct": buy_ratio,
        "age_ms": round(max(ages), 3) if ages else None,
        "route_conflict_count": route_conflicts,
    }


def _rest_tape_summary(
    ticks: list[dict[str, Any]], *, now_epoch: float, max_age_ms: float = 3000.0
) -> dict[str, Any]:
    buy_volume = sell_volume = buy_count = sell_count = 0
    ages: list[float] = []
    stale_count = 0
    for tick in ticks:
        if not isinstance(tick, dict):
            continue
        fresh, age_ms, _basis = rest_signed_tape_tick_freshness(
            tick, now_ts=now_epoch, max_age_ms=max_age_ms
        )
        if not fresh:
            stale_count += 1
            continue
        side = str(tick.get("aggressor_side") or tick.get("side") or "").upper()
        raw_qty = (
            tick.get("aggressor_aux_raw_15")
            or tick.get("signed_trade_volume")
            or tick.get("signed_volume")
            or tick.get("volume")
            or tick.get("qty")
        )
        qty = abs(_safe_int(raw_qty, 0))
        if side not in {"BUY", "SELL"}:
            text = str(raw_qty or "").strip()
            if text.startswith("+"):
                side = "BUY"
            elif text.startswith("-"):
                side = "SELL"
        if side == "BUY" and qty > 0:
            buy_count += 1
            buy_volume += qty
        elif side == "SELL" and qty > 0:
            sell_count += 1
            sell_volume += qty
        else:
            continue
        if age_ms is not None:
            ages.append(float(age_ms))
    sample_count = buy_count + sell_count
    total_volume = buy_volume + sell_volume
    buy_ratio = (
        round(buy_volume / total_volume * 100.0, 3) if total_volume > 0 else None
    )
    if sample_count < 3:
        state = "stale" if stale_count and not sample_count else "insufficient"
    elif buy_volume > sell_volume:
        state = "buy_dominated"
    elif sell_volume > buy_volume:
        state = "sell_dominated"
    else:
        state = "mixed"
    return {
        "state": state,
        "source": "ka10084_signed_tape" if sample_count else "missing",
        "sample_count": sample_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "buy_ratio_pct": buy_ratio,
        "age_ms": round(max(ages), 3) if ages else None,
        "stale_or_unknown_count": stale_count,
    }


def _bounded_rest_signed_tape(
    token: str,
    request_code: str,
    *,
    now_epoch: float,
) -> tuple[list[dict[str, Any]], bool]:
    cache_key = str(request_code or "")
    with _REST_TAPE_CACHE_LOCK:
        for stale_key, (cached_at, _rows) in list(_REST_TAPE_CACHE.items()):
            if now_epoch - cached_at > _REST_TAPE_TTL_SEC:
                _REST_TAPE_CACHE.pop(stale_key, None)
        cached = _REST_TAPE_CACHE.get(cache_key)
        if cached and 0.0 <= now_epoch - cached[0] <= _REST_TAPE_TTL_SEC:
            return list(cached[1]), True
        try:
            from src.utils import kiwoom_utils

            rows = list(
                kiwoom_utils.get_recent_signed_trades_ka10084(
                    token, cache_key, limit=10
                )
                or []
            )
        except Exception:
            rows = []
        _REST_TAPE_CACHE[cache_key] = (now_epoch, list(rows))
        return rows, False


def _session_phase(now: datetime, session: str) -> tuple[str, int | None]:
    current = now.time()
    session_value = str(session or "").lower()
    if "premarket" in session_value:
        close_time = dt_time(9, 0)
        phase = "premarket"
    elif session_value.startswith("nxt_") and "aftermarket" in session_value:
        close_time = dt_time(20, 0)
        phase = "nxt_aftermarket"
    elif session_value.startswith("nxt_"):
        close_time = dt_time(20, 0)
        phase = "nxt_overlap"
    elif dt_time(15, 20) <= current <= dt_time(15, 30):
        close_time = dt_time(15, 30)
        phase = "krx_closing"
    else:
        close_time = dt_time(15, 30)
        phase = "krx_regular"
    now_minutes = current.hour * 60 + current.minute
    close_minutes = close_time.hour * 60 + close_time.minute
    return phase, max(0, close_minutes - now_minutes)


def _flow_signature(context: dict[str, Any]) -> dict[str, Any]:
    candle = context.get("candle") if isinstance(context.get("candle"), dict) else {}
    tape = (
        context.get("signed_tape")
        if isinstance(context.get("signed_tape"), dict)
        else {}
    )
    micro = (
        context.get("microstructure")
        if isinstance(context.get("microstructure"), dict)
        else {}
    )
    execution = (
        context.get("execution_pnl")
        if isinstance(context.get("execution_pnl"), dict)
        else {}
    )
    quality = (
        context.get("source_quality")
        if isinstance(context.get("source_quality"), dict)
        else {}
    )
    return {
        "executable_pnl_pct": execution.get("executable_pnl_pct"),
        "candle_regime": candle.get("regime"),
        "candle_slope_3m": (
            (candle.get("structure") or {}).get("slopes_pct_per_bar", {}).get("3")
            if isinstance(candle.get("structure"), dict)
            else None
        ),
        "signed_tape_state": tape.get("state"),
        "ofi_regime": micro.get("ofi_regime"),
        "source_quality_status": quality.get("status"),
    }


def count_holding_context_changes(
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
    *,
    price_trigger_pct: float = 0.35,
) -> tuple[int, list[str]]:
    previous = previous if isinstance(previous, dict) else {}
    current = current if isinstance(current, dict) else {}
    groups: list[str] = []
    old_pnl = _safe_float(previous.get("executable_pnl_pct"), None)
    new_pnl = _safe_float(current.get("executable_pnl_pct"), None)
    if (
        old_pnl is not None
        and new_pnl is not None
        and abs(new_pnl - old_pnl) + 1e-9 >= max(0.0, price_trigger_pct)
    ):
        groups.append("price_pnl")
    old_regime = str(previous.get("candle_regime") or "")
    new_regime = str(current.get("candle_regime") or "")
    old_slope = _safe_float(previous.get("candle_slope_3m"), None)
    new_slope = _safe_float(current.get("candle_slope_3m"), None)
    if (old_regime and new_regime and old_regime != new_regime) or (
        old_slope is not None and new_slope is not None and old_slope * new_slope < 0
    ):
        groups.append("candle")
    for key, group in (
        ("signed_tape_state", "signed_tape"),
        ("ofi_regime", "orderbook_ofi"),
        ("source_quality_status", "source_quality"),
    ):
        old_value = str(previous.get(key) or "")
        new_value = str(current.get(key) or "")
        if old_value and new_value and old_value != new_value:
            groups.append(group)
    unique = list(dict.fromkeys(groups))
    return len(unique), unique


def build_holding_decision_context(
    token: str | None,
    code: str,
    ws_data: dict[str, Any] | None,
    stock: dict[str, Any] | None,
    venue: str | None,
    session: str | None,
    decision_kind: str,
    limit: int = 60,
    model_bar_limit: int = 20,
    now_ts: Any = None,
    *,
    recent_candles: list[dict[str, Any]] | None = None,
    candle_meta: dict[str, Any] | None = None,
    recent_ticks: list[dict[str, Any]] | None = None,
    rest_signed_ticks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    now = _now_kst(now_ts)
    now_epoch = now.timestamp()
    ws = ws_data if isinstance(ws_data, dict) else {}
    position = stock if isinstance(stock, dict) else {}
    candle = build_session_candle_source(
        token,
        code,
        ws,
        venue,
        session,
        limit=limit,
        model_bar_limit=model_bar_limit,
        now_ts=now,
        recent_candles=recent_candles,
        source_meta=candle_meta,
    )
    enabled = holding_decision_context_enabled(
        venue=str(candle.get("venue") or ""),
        session=str(candle.get("session") or ""),
        decision_kind=decision_kind,
        now_ts=now,
    )
    request_suffix = _request_suffix(str(candle.get("request_code") or ""))
    ws_route = str(candle.get("ws_route") or "").lower()
    ws_ticks = [
        tick
        for tick in (
            list(ws.get("recent_trade_ticks") or []) + list(recent_ticks or [])
        )
        if isinstance(tick, dict)
    ]
    tape = _trusted_ws_tape(
        ws_ticks,
        request_suffix=request_suffix,
        ws_route=ws_route,
        now_epoch=now_epoch,
    )
    tape_fetch_ms = 0
    fetched_rest_tape = False
    rest_tape_cache_hit = False
    rest_ticks = list(rest_signed_ticks or [])
    if enabled and tape["sample_count"] < 3 and not rest_ticks and token:
        fetch_started = time.perf_counter()
        rest_ticks, rest_tape_cache_hit = _bounded_rest_signed_tape(
            token,
            str(candle.get("request_code") or code),
            now_epoch=now_epoch,
        )
        fetched_rest_tape = not rest_tape_cache_hit
        tape_fetch_ms = int((time.perf_counter() - fetch_started) * 1000)
    if tape["sample_count"] < 3 and rest_ticks:
        rest_tape = _rest_tape_summary(rest_ticks, now_epoch=now_epoch)
        if rest_tape["sample_count"] >= tape["sample_count"]:
            tape = rest_tape
    tape["fallback_fetched"] = fetched_rest_tape
    tape["fallback_cache_hit"] = rest_tape_cache_hit

    levels = _best_levels(ws)
    quote_age_ms, quote_age_basis = _quote_age_ms(ws, now_epoch)
    best_bid = levels["best_bid"]
    best_ask = levels["best_ask"]
    bbo_fresh = bool(
        best_bid > 0
        and best_ask >= best_bid
        and quote_age_ms is not None
        and quote_age_ms <= 3000.0
        and not bool(ws.get("quote_stale") or ws.get("stale_quote"))
    )
    spread_bps = (
        round((best_ask - best_bid) / best_bid * 10000.0, 3)
        if best_bid > 0 and best_ask >= best_bid
        else None
    )
    ask_total = abs(_safe_int(ws.get("ask_tot"), 0))
    bid_total = abs(_safe_int(ws.get("bid_tot"), 0))
    depth_total = ask_total + bid_total
    imbalance = (
        round((bid_total - ask_total) / depth_total, 4) if depth_total > 0 else None
    )
    ofi_regime = str(
        position.get("holding_flow_ofi_regime")
        or position.get("ofi_regime")
        or position.get("orderbook_micro_regime")
        or ""
    ).lower()
    ofi_age_ms = _safe_float(
        position.get("holding_flow_ofi_snapshot_age_ms")
        or position.get("orderbook_micro_snapshot_age_ms"),
        None,
    )
    orderbook_micro_fresh = bool(
        bbo_fresh
        and (
            depth_total > 0
            or (
                ofi_regime in _KNOWN_OFI_STATES
                and ofi_age_ms is not None
                and ofi_age_ms <= 3000.0
            )
        )
    )

    avg_price = (
        _safe_float(
            _first_present(position, "avg_price", "buy_price", default=0.0),
            0.0,
        )
        or 0.0
    )
    memory_qty = max(
        0,
        _safe_int(
            _first_present(
                position,
                "remaining_qty",
                "buy_qty",
                "qty",
                default=0,
            ),
            0,
        ),
    )
    broker_qty_raw = _first_present(
        position,
        "broker_holding_qty",
        "verified_holding_qty",
        "broker_qty",
        default=None,
    )
    broker_qty_present = broker_qty_raw is not None
    broker_qty = _safe_int(
        broker_qty_raw,
        0,
    )
    broker_snapshot_age_sec = _safe_float(
        position.get("broker_snapshot_age_sec")
        or position.get("holding_snapshot_age_sec"),
        None,
    )
    curr_price = abs(_safe_int(ws.get("curr") or position.get("curr_price"), 0))
    mark_pnl_pct = (
        round((curr_price / avg_price - 1.0) * 100.0, 4)
        if avg_price > 0 and curr_price > 0
        else None
    )
    executable_pnl_pct = (
        round((best_bid / avg_price - 1.0) * 100.0, 4)
        if avg_price > 0 and best_bid > 0
        else None
    )
    estimated_fee_tax_pct = _safe_float(position.get("estimated_fee_tax_pct"), None)
    estimated_slippage_bps = _safe_float(position.get("estimated_slippage_bps"), None)
    estimated_net_executable_pnl_pct = (
        round(
            executable_pnl_pct
            - float(estimated_fee_tax_pct or 0.0)
            - float(estimated_slippage_bps or 0.0) / 100.0,
            4,
        )
        if executable_pnl_pct is not None
        else None
    )
    active_exit_token = bool(
        position.get("exit_token")
        or position.get("fast_exit_token")
        or position.get("exit_claimed")
        or position.get("exit_decided_at")
    )
    quantity_mismatch = bool(broker_qty_present and broker_qty != memory_qty)
    order_conflict = bool(
        position.get("broker_order_conflict")
        or position.get("quantity_mismatch")
        or quantity_mismatch
        or position.get("reconciliation_conflict")
        or position.get("cancel_fill_conflict")
    )
    position_valid = bool(avg_price > 0 and memory_qty > 0)
    signed_tape_fresh = bool(
        tape.get("source") == "ws_trusted_aggressor"
        and tape.get("state") not in _UNUSABLE_TAPE_STATES
    )
    rest_signed_tape_advisory_fresh = bool(
        tape.get("source") == "ka10084_signed_tape"
        and tape.get("state") not in _UNUSABLE_TAPE_STATES
    )
    microstructure_fresh = bool(signed_tape_fresh or orderbook_micro_fresh)
    candle_quality = (
        candle.get("source_quality")
        if isinstance(candle.get("source_quality"), dict)
        else {}
    )
    candle_fresh = candle_quality.get("status") == "fresh_consistent"
    blockers: list[str] = []
    if not candle_fresh:
        blockers.append("candle_source_quality")
    if not bbo_fresh:
        blockers.append("executable_bbo")
    if not position_valid:
        blockers.append("position_invalid")
    if not microstructure_fresh:
        blockers.append("microstructure_missing_or_stale")
    if active_exit_token:
        blockers.append("active_exit_token")
    if order_conflict:
        blockers.append("order_or_quantity_conflict")
    hold_defer_allowed = bool(enabled and not blockers)
    quality_status = (
        "fresh_consistent"
        if hold_defer_allowed
        else ("disabled" if not enabled else "blocked")
    )
    phase, minutes_to_close = _session_phase(now, str(candle.get("session") or ""))
    context = {
        "schema": SCHEMA,
        "enabled": enabled,
        "decision_kind": decision_kind,
        "venue": candle.get("venue"),
        "session": candle.get("session"),
        "rest_route": candle.get("rest_route"),
        "ws_route": candle.get("ws_route"),
        "request_code": candle.get("request_code"),
        "candle": {
            key: candle.get(key)
            for key in (
                "current_session_bar_count",
                "previous_session_bar_count",
                "completed_bar_count",
                "forming_bar_present",
                "latest_bar_age_sec",
                "sample_mode",
                "bars",
                "structure",
                "regime",
                "alignment",
                "risk_flags",
                "route_equivalence",
                "route_equivalence_proven",
            )
        },
        "signed_tape": tape,
        "microstructure": {
            **levels,
            "execution_strength": _safe_float(ws.get("v_pw"), None),
            "buy_ratio": _safe_float(ws.get("buy_ratio"), None),
            "buy_exec_volume": (
                _safe_int(ws.get("buy_exec_volume"), 0)
                if ws.get("buy_exec_volume") not in (None, "")
                else None
            ),
            "sell_exec_volume": (
                _safe_int(ws.get("sell_exec_volume"), 0)
                if ws.get("sell_exec_volume") not in (None, "")
                else None
            ),
            "quote_age_ms": (
                round(quote_age_ms, 3) if quote_age_ms is not None else None
            ),
            "quote_age_basis": quote_age_basis,
            "bbo_fresh": bbo_fresh,
            "spread_bps": spread_bps,
            "ask_total_depth": ask_total,
            "bid_total_depth": bid_total,
            "depth_imbalance": imbalance,
            "ofi_regime": ofi_regime or None,
            "ofi_snapshot_age_ms": ofi_age_ms,
            "orderbook_or_ofi_fresh": orderbook_micro_fresh,
        },
        "execution_pnl": {
            "mark_price": curr_price,
            "executable_sell_price": best_bid,
            "average_entry_price": avg_price,
            "mark_pnl_pct": mark_pnl_pct,
            "executable_pnl_pct": executable_pnl_pct,
            "estimated_fee_tax_pct": estimated_fee_tax_pct,
            "spread_cost_bps": spread_bps,
            "estimated_slippage_bps": estimated_slippage_bps,
            "estimated_net_executable_pnl_pct": (estimated_net_executable_pnl_pct),
            "remaining_qty": memory_qty,
            "best_bid_qty": levels["best_bid_qty"],
            "estimated_market_impact": (
                "depth_shortfall"
                if levels["best_bid_qty"] > 0 and memory_qty > levels["best_bid_qty"]
                else (
                    "within_best_bid_depth" if levels["best_bid_qty"] > 0 else "unknown"
                )
            ),
        },
        "position_lifecycle": {
            "memory_qty": memory_qty,
            "broker_qty": broker_qty if broker_qty_present else None,
            "broker_qty_present": broker_qty_present,
            "average_entry_price": avg_price,
            "peak_basis_qty": position.get("peak_basis_qty"),
            "peak_basis_avg_price": position.get("peak_basis_avg_price"),
            "peak_profit_pct": position.get("peak_profit"),
            "mfe_pct": position.get("mfe_pct", position.get("peak_profit")),
            "mae_pct": position.get("mae_pct"),
            "peak_at": position.get("peak_at") or position.get("peak_profit_at"),
            "seconds_since_peak": position.get("seconds_since_peak"),
            "never_green": bool(position.get("never_green")),
            "drawdown_velocity_pct_per_sec": position.get(
                "drawdown_velocity_pct_per_sec"
            ),
            "last_scale_in_at": position.get("last_scale_in_at"),
            "last_scale_in_price": position.get("last_scale_in_price"),
            "last_scale_in_type": position.get("last_scale_in_type"),
            "scale_in_filled_qty": position.get("scale_in_filled_qty"),
            "avg_down_count": position.get("avg_down_count"),
            "pyramid_count": position.get("pyramid_count"),
            "partial_tp_realized_qty": _first_present(
                position,
                "partial_tp_realized_qty",
                "early_volatility_tp_filled_qty",
                "nxt_rising_missed_tp1_partial_filled_qty",
                default=0,
            ),
            "partial_tp_remaining_qty": _first_present(
                position,
                "partial_tp_remaining_qty",
                "remaining_qty",
                "buy_qty",
                default=0,
            ),
        },
        "order_reconciliation": {
            "broker_snapshot_age_sec": broker_snapshot_age_sec,
            "open_buy_qty": position.get("open_buy_qty"),
            "open_sell_qty": position.get("open_sell_qty"),
            "partial_fill_qty": position.get("partial_fill_qty"),
            "cancel_pending": bool(position.get("cancel_pending")),
            "exit_token_active": active_exit_token,
            "quantity_mismatch": quantity_mismatch,
            "order_or_quantity_conflict": order_conflict,
        },
        "market_session": {
            "phase": phase,
            "minutes_to_close": minutes_to_close,
            "vi_state": position.get("vi_state") or ws.get("vi_state"),
            "halted": bool(position.get("halted") or ws.get("halted")),
            "limit_state": position.get("limit_state") or ws.get("limit_state"),
            "market_regime": position.get("market_regime"),
            "sector_relative_trend": position.get("sector_relative_trend"),
        },
        "source_quality": {
            "status": quality_status,
            "hold_defer_allowed": hold_defer_allowed,
            "blockers": blockers,
            "candle_status": candle_quality.get("status"),
            "candle_blockers": candle_quality.get("blockers", []),
            "bbo_fresh": bbo_fresh,
            "signed_tape_fresh": signed_tape_fresh,
            "rest_signed_tape_advisory_fresh": rest_signed_tape_advisory_fresh,
            "orderbook_or_ofi_fresh": orderbook_micro_fresh,
            "position_valid": position_valid,
            "order_consistent": not order_conflict,
        },
        "timing": {
            "candle_fetch_ms": (candle.get("timing") or {}).get("fetch_ms", 0),
            "signed_tape_fetch_ms": tape_fetch_ms,
            "build_ms": int((time.perf_counter() - started) * 1000),
        },
        "observation_contract": OBSERVATION_CONTRACT,
    }
    context["flow_signature"] = _flow_signature(context)
    return context


def holding_decision_context_model_payload(
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    source = context if isinstance(context, dict) else {}
    if source.get("schema") != SCHEMA:
        return {}

    def _prune(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: pruned
                for key, item in value.items()
                if (pruned := _prune(item)) not in (None, {}, [])
            }
        if isinstance(value, list):
            return [
                pruned
                for item in value
                if (pruned := _prune(item)) not in (None, {}, [])
            ]
        return value

    def _pick(mapping: Any, keys: tuple[str, ...]) -> dict[str, Any]:
        source_mapping = mapping if isinstance(mapping, dict) else {}
        return {key: source_mapping.get(key) for key in keys}

    candle = dict(source.get("candle") or {})
    structure = dict(candle.get("structure") or {})
    structure.pop("regime", None)
    structure.pop("alignment", None)
    candle["structure"] = structure
    candle.pop("route_equivalence", None)
    candle.pop("route_equivalence_proven", None)
    bars = []
    for bar in candle.get("bars") or []:
        if not isinstance(bar, dict):
            continue
        bars.append(
            {
                "minute": bar.get("t"),
                "open": bar.get("o"),
                "high": bar.get("h"),
                "low": bar.get("l"),
                "close": bar.get("c"),
                "volume": bar.get("v"),
                "is_forming": bool(bar.get("forming")),
                "volume_is_partial": bool(bar.get("partial_volume")),
            }
        )
    candle["bar_schema"] = {
        "sequence": "oldest_to_latest",
        "timezone": "Asia/Seoul",
        "interval": "1m",
        "price_unit": "KRW",
        "volume_unit": "shares",
    }
    candle["model_bar_count"] = len(bars)
    candle["bars"] = bars
    payload = {
        key: source.get(key)
        for key in (
            "schema",
            "enabled",
            "decision_kind",
            "venue",
            "session",
            "rest_route",
            "ws_route",
        )
    }
    payload.update(
        {
            "candle": candle,
            "signed_tape": _pick(
                source.get("signed_tape"),
                (
                    "state",
                    "source",
                    "sample_count",
                    "buy_volume",
                    "sell_volume",
                    "buy_ratio_pct",
                    "age_ms",
                    "route_conflict_count",
                ),
            ),
            "microstructure": _pick(
                source.get("microstructure"),
                (
                    "best_ask",
                    "best_bid",
                    "best_ask_qty",
                    "best_bid_qty",
                    "execution_strength",
                    "buy_ratio",
                    "buy_exec_volume",
                    "sell_exec_volume",
                    "quote_age_ms",
                    "bbo_fresh",
                    "spread_bps",
                    "ask_total_depth",
                    "bid_total_depth",
                    "depth_imbalance",
                    "ofi_regime",
                    "ofi_snapshot_age_ms",
                ),
            ),
            "execution_pnl": _pick(
                source.get("execution_pnl"),
                (
                    "mark_price",
                    "executable_sell_price",
                    "average_entry_price",
                    "mark_pnl_pct",
                    "executable_pnl_pct",
                    "estimated_fee_tax_pct",
                    "spread_cost_bps",
                    "estimated_slippage_bps",
                    "estimated_net_executable_pnl_pct",
                    "remaining_qty",
                    "best_bid_qty",
                    "estimated_market_impact",
                ),
            ),
            "position_lifecycle": _pick(
                source.get("position_lifecycle"),
                (
                    "memory_qty",
                    "broker_qty",
                    "average_entry_price",
                    "peak_basis_qty",
                    "peak_basis_avg_price",
                    "peak_profit_pct",
                    "mfe_pct",
                    "mae_pct",
                    "peak_at",
                    "seconds_since_peak",
                    "never_green",
                    "drawdown_velocity_pct_per_sec",
                    "last_scale_in_at",
                    "last_scale_in_price",
                    "last_scale_in_type",
                    "scale_in_filled_qty",
                    "avg_down_count",
                    "pyramid_count",
                    "partial_tp_realized_qty",
                    "partial_tp_remaining_qty",
                ),
            ),
            "order_reconciliation": _pick(
                source.get("order_reconciliation"),
                (
                    "broker_snapshot_age_sec",
                    "open_buy_qty",
                    "open_sell_qty",
                    "partial_fill_qty",
                    "cancel_pending",
                    "exit_token_active",
                    "quantity_mismatch",
                    "order_or_quantity_conflict",
                ),
            ),
            "market_session": _pick(
                source.get("market_session"),
                (
                    "phase",
                    "minutes_to_close",
                    "vi_state",
                    "halted",
                    "limit_state",
                    "market_regime",
                    "sector_relative_trend",
                ),
            ),
            "source_quality": _pick(
                source.get("source_quality"),
                (
                    "status",
                    "hold_defer_allowed",
                    "blockers",
                    "candle_status",
                    "bbo_fresh",
                    "signed_tape_fresh",
                    "rest_signed_tape_advisory_fresh",
                    "orderbook_or_ofi_fresh",
                    "position_valid",
                    "order_consistent",
                ),
            ),
        }
    )
    return _prune(payload)


def holding_decision_context_log_fields(
    context: dict[str, Any] | None,
    *,
    observation_contract_prefix: str = "",
) -> dict[str, Any]:
    context = context if isinstance(context, dict) else {}
    candle = context.get("candle") if isinstance(context.get("candle"), dict) else {}
    tape = (
        context.get("signed_tape")
        if isinstance(context.get("signed_tape"), dict)
        else {}
    )
    micro = (
        context.get("microstructure")
        if isinstance(context.get("microstructure"), dict)
        else {}
    )
    execution = (
        context.get("execution_pnl")
        if isinstance(context.get("execution_pnl"), dict)
        else {}
    )
    lifecycle = (
        context.get("position_lifecycle")
        if isinstance(context.get("position_lifecycle"), dict)
        else {}
    )
    reconciliation = (
        context.get("order_reconciliation")
        if isinstance(context.get("order_reconciliation"), dict)
        else {}
    )
    market_session = (
        context.get("market_session")
        if isinstance(context.get("market_session"), dict)
        else {}
    )
    quality = (
        context.get("source_quality")
        if isinstance(context.get("source_quality"), dict)
        else {}
    )
    timing = context.get("timing") if isinstance(context.get("timing"), dict) else {}
    contract_fields = {
        f"{observation_contract_prefix}{key}": value
        for key, value in OBSERVATION_CONTRACT.items()
    }
    return {
        "holding_context_schema": context.get("schema", SCHEMA),
        "holding_context_enabled": bool(context.get("enabled", False)),
        "holding_context_decision_kind": context.get("decision_kind"),
        "holding_context_venue": context.get("venue"),
        "holding_context_session": context.get("session"),
        "holding_context_rest_route": context.get("rest_route"),
        "holding_context_ws_route": context.get("ws_route"),
        "holding_context_candle_bar_count": candle.get("current_session_bar_count", 0),
        "holding_context_candle_latest_age_sec": candle.get("latest_bar_age_sec"),
        "holding_context_candle_regime": candle.get("regime"),
        "holding_context_candle_risk_flags": candle.get("risk_flags", []),
        "holding_context_tape_state": tape.get("state"),
        "holding_context_tape_source": tape.get("source"),
        "holding_context_tape_sample_count": tape.get("sample_count", 0),
        "holding_context_tape_age_ms": tape.get("age_ms"),
        "holding_context_bbo_fresh": bool(micro.get("bbo_fresh", False)),
        "holding_context_best_bid": micro.get("best_bid"),
        "holding_context_best_ask": micro.get("best_ask"),
        "holding_context_quote_age_ms": micro.get("quote_age_ms"),
        "holding_context_spread_bps": micro.get("spread_bps"),
        "holding_context_ofi_regime": micro.get("ofi_regime"),
        "holding_context_mark_pnl_pct": execution.get("mark_pnl_pct"),
        "holding_context_executable_pnl_pct": execution.get("executable_pnl_pct"),
        "holding_context_estimated_net_executable_pnl_pct": execution.get(
            "estimated_net_executable_pnl_pct"
        ),
        "holding_context_memory_qty": lifecycle.get("memory_qty"),
        "holding_context_broker_qty": lifecycle.get("broker_qty"),
        "holding_context_peak_basis_qty": lifecycle.get("peak_basis_qty"),
        "holding_context_peak_basis_avg_price": lifecycle.get("peak_basis_avg_price"),
        "holding_context_partial_tp_realized_qty": lifecycle.get(
            "partial_tp_realized_qty"
        ),
        "holding_context_partial_tp_remaining_qty": lifecycle.get(
            "partial_tp_remaining_qty"
        ),
        "holding_context_broker_snapshot_age_sec": reconciliation.get(
            "broker_snapshot_age_sec"
        ),
        "holding_context_open_buy_qty": reconciliation.get("open_buy_qty"),
        "holding_context_open_sell_qty": reconciliation.get("open_sell_qty"),
        "holding_context_exit_token_active": bool(
            reconciliation.get("exit_token_active", False)
        ),
        "holding_context_order_conflict": bool(
            reconciliation.get("order_or_quantity_conflict", False)
        ),
        "holding_context_market_phase": market_session.get("phase"),
        "holding_context_minutes_to_close": market_session.get("minutes_to_close"),
        "holding_context_source_quality_status": quality.get("status"),
        "holding_context_hold_defer_allowed": bool(
            quality.get("hold_defer_allowed", False)
        ),
        "holding_context_position_valid": bool(quality.get("position_valid", False)),
        "holding_context_order_consistent": bool(
            quality.get("order_consistent", False)
        ),
        "holding_context_blockers": quality.get("blockers", []),
        "holding_context_candle_fetch_ms": timing.get("candle_fetch_ms", 0),
        "holding_context_signed_tape_fetch_ms": timing.get("signed_tape_fetch_ms", 0),
        "holding_context_build_ms": timing.get("build_ms", 0),
        **contract_fields,
    }
