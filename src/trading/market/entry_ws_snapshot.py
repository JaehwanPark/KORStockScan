"""Exact-route WS inputs for existing entry guards; no broker I/O or authority.

Location owner: market-data adapters, not order policy or a new collector.
REST recovery is deliberately not started on this bounded path: existing REST
helpers cannot bound their complete admission/retry time to the entry deadline.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.trading.market.micro_confirmation import _live_snapshot_path
from src.trading.market.shared_ws_snapshot import process_generation

SOURCE_ENV = "KORSTOCKSCAN_ENTRY_MARKET_DATA_SOURCE"
ITEMS_ENV = "KORSTOCKSCAN_ENTRY_WS_ITEMS"
SCHEMA = "entry_ws_source_receipt_v1"
KST = ZoneInfo("Asia/Seoul")
_CACHE = None


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("ws_clock_invalid")
    return value


def _integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("ws_integer_invalid")
    return value


def _load(path):
    global _CACHE
    # Atomic writer generation, never TTL-only reuse; fork gets a new cache.
    with Path(path).open("rb") as stream:
        stat = os.fstat(stream.fileno())
        key = (os.getpid(), str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        if _CACHE is not None and _CACHE[0] == key:
            return _CACHE[1], _CACHE[2]
        raw = stream.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("ws_snapshot_size_exceeded")
    data = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    _CACHE = key, data, digest
    return data, digest


def validate_receipt(meta, *, symbol, route, now_ts):
    """Recheck cached inputs at consumption, including producer liveness."""
    from src.trading.order.entry_liquidity_guard import entry_liquidity_request_code
    if (meta.get("schema") != SCHEMA or meta.get("item") != entry_liquidity_request_code(symbol, route)
            or meta.get("process") != process_generation(meta["process"]["pid"])
            or not re.fullmatch(r"[0-9a-f]{64}", meta.get("snapshot_sha256", ""))):
        raise ValueError("ws_receipt_binding_invalid")
    received = _number(meta["received_ts_ms"])
    age = _number(now_ts) * 1000 - received
    if age < 0 or datetime.fromtimestamp(received / 1000, KST).date() != datetime.fromtimestamp(now_ts, KST).date():
        raise ValueError("ws_receive_clock_invalid")
    return math.ceil(age)


def read_entry_snapshot(*, symbol, route, kind, path=None, now_ts=None):
    from src.trading.order.entry_liquidity_guard import (
        EntryLiquiditySnapshot, EntryExecutionVelocitySnapshot,
        entry_liquidity_request_code, MAX_SNAPSHOT_AGE_MS, MAX_LATEST_PRINT_AGE_MS,
        REQUIRED_RECENT_PRINT_COUNT,
    )
    cls = EntryLiquiditySnapshot if kind == "0D" else EntryExecutionVelocitySnapshot
    source = "kiwoom_ws_orderbook" if kind == "0D" else "kiwoom_ws_trade_prints"
    item = ""
    try:
        if kind not in {"0B", "0D"}:
            raise ValueError("ws_kind_invalid")
        item = entry_liquidity_request_code(symbol, route)
        data, digest = _load(path or _live_snapshot_path())
        now = time.time() if now_ts is None else now_ts  # after file I/O
        authority = data["machine_confirmation_input_contract"]
        if (data.get("schema_version") != "kiwoom_ws_dashboard_snapshot_v1"
                or data.get("decision_authority") != "source_quality_only"
                or data.get("runtime_effect") is not False
                or authority.get("schema") != "machine_entry_confirmation_ws_snapshot_v1"
                or authority.get("decision_authority") != "market_data_input_only_no_order_authority"
                or any(authority.get(k) is not True for k in ("exact_route_required", "causal_past_only", "broker_order_forbidden"))
                or any(authority.get(k) is not False for k in ("runtime_effect", "actual_order_submitted"))):
            raise ValueError("ws_authority_invalid")
        producer = data["shared_transport_producer"]
        epoch = _integer(producer["transport_epoch"], 1)
        registered = producer["registered_items"]
        if (producer.get("schema") != "shared_ws_transport_producer_v1"
                or producer.get("connection_available") is not True
                or not re.fullmatch(r"[0-9a-f]{40}", producer.get("source_commit", ""))
                or not isinstance(registered, list) or any(not isinstance(x, str) for x in registered)
                or item not in registered):
            raise ValueError("ws_producer_or_registration_invalid")
        stock = data["stocks"][symbol]
        if _integer(stock["market_data_transport_epoch"], 1) != epoch:
            raise ValueError("ws_epoch_conflict")
        matches = [r for r in stock["machine_confirmation_routes"].values()
                   if r.get("realtime_types", {}).get(kind, {}).get("item") == item]
        if len(matches) != 1:
            raise ValueError("ws_exact_route_missing_or_duplicate")
        selected = matches[0]; row = selected["realtime_types"][kind]
        suffix = item[6:]
        market_route, venue = {"": ("krx_only", "KRX"), "_NX": ("nxt_only", "NXT"), "_AL": ("krx_nxt_integrated", "")}[suffix]
        if (row.get("realtime_type") != kind or row.get("market_suffix") != suffix
                or row.get("market_route") != market_route or row.get("effective_venue") != venue
                or _integer(row["transport_epoch"], 1) != epoch):
            raise ValueError("ws_route_or_epoch_invalid")
        stamp = _number(row["observed_epoch"])
        sequence = _integer(row["route_sequence"], 1)
        generated = _number(data["generated_at_epoch"])
        if not stamp <= generated <= now:
            raise ValueError("ws_publication_clock_invalid")
        meta = dict(schema=SCHEMA, item=item, process=producer["process"], transport_epoch=epoch,
                    source_commit=producer["source_commit"], snapshot_sha256=digest,
                    received_ts_ms=stamp * 1000, observed_at_epoch=now, realtime_type=kind,
                    route_sequence=sequence, market_data_route=market_route)
        age = validate_receipt(meta, symbol=symbol, route=route, now_ts=now)
        if age > (MAX_SNAPSHOT_AGE_MS if kind == "0D" else MAX_LATEST_PRINT_AGE_MS):
            raise ValueError("ws_source_stale")
        if kind == "0D":
            bid, ask = row["orderbook"]["bids"][0], row["orderbook"]["asks"][0]
            bp, ap = _integer(bid["price"], 1), _integer(ask["price"], 1)
            if bp > ap: raise ValueError("ws_crossed_book")
            return cls(True, symbol, route, item, source=source, best_bid=bp, best_ask=ap,
                       best_bid_qty=_integer(bid["volume"]), best_ask_qty=_integer(ask["volume"]),
                       age_ms=age, received_ts_ms=math.floor(stamp * 1000), source_meta=meta)
        rows = selected["recent_trades"]
        if not isinstance(rows, list) or len(rows) < REQUIRED_RECENT_PRINT_COUNT:
            raise ValueError("ws_trade_history_insufficient")
        rows = sorted(rows, key=lambda r: _integer(r["route_sequence"], 1), reverse=True)[:REQUIRED_RECENT_PRINT_COUNT]
        times, receives, quantities, accumulated = [], [], [], []
        for offset, trade in enumerate(rows):
            received = _integer(trade["received_at_ms"], 1)
            event = _number(trade["provider_trade_epoch"])
            if (trade.get("item") != item or _integer(trade["transport_epoch"], 1) != epoch
                    or trade["route_sequence"] != sequence - offset
                    or trade.get("provider_trade_time_precision_ms") != 1000
                    or trade.get("provider_trade_date_basis") != "local_receive_calendar_date_not_provider_date"
                    or not event * 1000 <= received <= stamp * 1000 + 1
                    or datetime.fromtimestamp(event, KST).date() != datetime.fromtimestamp(now, KST).date()):
                raise ValueError("ws_trade_history_contract_gap")
            _integer(trade["price"], 1)
            times.append(event); receives.append(received); quantities.append(_integer(trade["volume"], 1))
            accumulated.append(_integer(trade["cum_volume"], 1))
        if (abs(receives[0] - stamp * 1000) > 1
                or any(a < b for a, b in zip(times, times[1:]))
                or any(a < b for a, b in zip(receives, receives[1:]))
                or any(a <= b for a, b in zip(accumulated, accumulated[1:]))):
            raise ValueError("ws_trade_endpoint_or_order_invalid")
        meta.update(provider_latest_epoch=times[0], local_sequence_contiguous=True,
                    exchange_completeness_proven=False)
        return cls(True, symbol, route, item, source=source, print_count=len(rows),
                   recent_print_span_ms=round((times[0] - times[-1]) * 1000),
                   latest_print_age_ms=math.ceil((now - times[0]) * 1000), recent_volume=sum(quantities),
                   observed_at_kst=datetime.fromtimestamp(now, KST).isoformat(),
                   print_times=tuple(datetime.fromtimestamp(t, KST).strftime("%H%M%S") for t in times),
                   source_meta=meta)
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        return cls(False, symbol, route, item, source=source, error="entry_ws_source_unavailable:" + reason)


def selected_entry_snapshot(*, symbol, route, kind):
    """None preserves the legacy REST path; WS failures remain explicit."""
    mode = os.getenv(SOURCE_ENV, "rest").strip().lower()
    if mode == "rest":
        return None
    if mode != "ws":
        from src.trading.order.entry_liquidity_guard import unavailable_entry_liquidity_snapshot, unavailable_entry_execution_velocity_snapshot
        unavailable = unavailable_entry_liquidity_snapshot if kind == "0D" else unavailable_entry_execution_velocity_snapshot
        return unavailable(symbol=symbol, route=route, error="entry_market_data_source_invalid")
    items = os.getenv(ITEMS_ENV, "").strip()
    if items:
        from src.trading.order.entry_liquidity_guard import entry_liquidity_request_code, unavailable_entry_liquidity_snapshot, unavailable_entry_execution_velocity_snapshot
        values = items.split(",")
        if any(not re.fullmatch(r"[0-9]{6}(?:_AL|_NX)?", value) for value in values):
            unavailable = unavailable_entry_liquidity_snapshot if kind == "0D" else unavailable_entry_execution_velocity_snapshot
            return unavailable(symbol=symbol, route=route, error="entry_ws_items_invalid")
        if entry_liquidity_request_code(symbol, route) not in values:
            return None  # Unselected exact items retain the original source.
    return read_entry_snapshot(symbol=symbol, route=route, kind=kind)
