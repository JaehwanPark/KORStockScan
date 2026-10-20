"""Exact-route, source-first probe before a zero-base candidate may be watched."""

from __future__ import annotations

import time
import uuid
import os
import threading
import math
import re
import bisect
from copy import deepcopy
from types import SimpleNamespace
from datetime import datetime
from urllib.parse import urlsplit
from concurrent.futures import TimeoutError as FutureTimeoutError

from src.engine.scalping.entry_candle_context import (
    build_entry_candle_context,
    completed_ws_candle_source_issue,
    fetch_entry_candles_with_meta,
    resolve_entry_candle_request_code,
    resolve_entry_candle_session,
)
from src.utils import kiwoom_utils
from src.utils.kiwoom_read_request_control import REQUEST_CLASS_SOURCE_ONLY
from src.engine.scalping_feature_packet import _select_recent_ticks_with_source


RESULT_SCHEMA = "zero_base_probe_result_v2"
LEGACY_RESULT_SCHEMA = "zero_base_probe_result_v1"
_SOURCE_WAIT_LOCK = threading.Lock()
_SOURCE_WAITERS = {}


class _ExactProbeSourceWait:
    """Coalesce quote wakes for a probe actually waiting on this transport."""

    def __init__(self, ws_manager, item):
        self.manager_id = id(ws_manager)
        self.item = item
        self.key = None

    def __enter__(self):
        return self

    def sequence(self, transport_epoch, *, active):
        from src.engine.scalping.reversal_source_diagnostics import observation_sequence

        # The manager's snapshot lock is never acquired under this lock. Ingress
        # may therefore publish under its own lock before taking this one.
        with _SOURCE_WAIT_LOCK:
            if active and self.key is None and type(transport_epoch) is int and transport_epoch > 0:
                self.key = (self.manager_id, self.item, transport_epoch)
                row = _SOURCE_WAITERS.setdefault(self.key, {"count": 0, "pending": False})
                row["count"] += 1
            if self.key is not None:
                _SOURCE_WAITERS[self.key]["pending"] = False
            return observation_sequence(self.item)

    def __exit__(self, *_exc):
        with _SOURCE_WAIT_LOCK:
            if self.key is not None:
                row = _SOURCE_WAITERS[self.key]
                row["count"] -= 1
                if not row["count"]:
                    del _SOURCE_WAITERS[self.key]


def notify_exact_probe_source(ws_manager, *, item, transport_epoch):
    """Notify published 0D only for an active exact probe; never run its FSM."""
    if type(transport_epoch) is not int or transport_epoch <= 0:
        return False
    key = (id(ws_manager), item, transport_epoch)
    with _SOURCE_WAIT_LOCK:
        row = _SOURCE_WAITERS.get(key)
        if row is None or row["pending"]:
            return False
        from src.engine.scalping.reversal_source_diagnostics import notify_observation

        row["pending"] = True
        notify_observation(item)
    return True


def native_history_summary(receipt):
    """Historical coverage is diagnostic; current freshness owns execution."""
    counts = receipt.get('selected_lifecycle_counts') or {}
    totals = {key: sum(v.get(key, 0) for v in counts.values()
                      if isinstance(v, dict) and type(v.get(key, 0)) is int and v.get(key, 0) >= 0)
              for key in ('TRUE', 'FALSE', 'UNKNOWN')}
    return dict(schema='probe_history_and_current_source_v1',
                historical_evaluations=totals, historical_known_count=totals['TRUE']+totals['FALSE'],
                source_censored_count=receipt.get('source_censored_count'),
                observed_seconds=receipt.get('observed_seconds'),
                current_native_source=receipt.get('native_source_current'),
                execution_authority=False, historical_observation_allows_order=False)


def native_wait_result(receipt, readiness):
    """A censored observation is neither a source error nor a failed pattern."""
    if receipt.get('reason')=='scope_or_generation_mismatch':
        return 'policy_unavailable','scope_or_generation_mismatch'
    if receipt.get('native_source_current') is False or receipt.get('reason')=='state_absent':
        if native_history_summary(receipt)['historical_known_count']:
            return 'observation_incomplete','native_history_observed_current_source_stale'
        return 'source_unavailable','native_source_stale_or_absent'
    if receipt.get('selected_pending_count',0):
        return 'observation_incomplete','confirmation_pending_at_residence_end'
    counts=receipt.get('selected_lifecycle_counts') or {}
    if any(v.get('TRUE',0)>0 for v in counts.values()):
        return 'observation_incomplete','native_confirmation_not_consumed_before_expiry'
    if receipt.get('source_censored_count',0):
        if native_history_summary(receipt)['historical_known_count']:
            return 'observation_incomplete','native_history_observed_with_source_gap'
        return 'source_unavailable','native_observation_source_censored'
    truth=receipt.get('selected_branch_truth') or {}
    if truth and all(v=='FALSE' and counts.get(b,{}).get('FALSE',0)>0 for b,v in truth.items()):
        return 'pattern_not_matched','native_observation_no_matching_pattern'
    if any(v.get('missing_inputs') for v in (readiness.get('branch_descriptors') or {}).values()):
        return 'required_feature_insufficient','required_branch_feature_missing'
    return 'observation_incomplete','feature_window_incomplete'
_ROUTE_ITEM = {
    "krx_only": lambda code: code,
    "nxt_only": lambda code: code + "_NX",
    "krx_nxt_integrated": lambda code: code + "_AL",
}
_ROUTE_VENUE = {"krx_only": "KRX", "nxt_only": "NXT", "krx_nxt_integrated": "SOR"}
_ROUTE_KEY = {"krx_only": "KRX|krx_only", "nxt_only": "_NX|nxt_only",
              "krx_nxt_integrated": "_AL|krx_nxt_integrated"}


def probe_item(code: str, route: str) -> str:
    builder = _ROUTE_ITEM.get(route)
    return builder(code) if builder and len(code) == 6 and code.isdigit() else ""


def probe_registration_receipt(ws_manager, *, code: str, item: str) -> str:
    """Check the local send receipt; it is not a broker subscription ACK."""
    registered = getattr(ws_manager, "_registered_items_by_code", None)
    if not isinstance(registered, dict):
        return "ws_registration_receipt_missing"
    lock = getattr(ws_manager, "lock", None)

    def inspect() -> str:
        if item not in (registered.get(code) or ()) or code not in (
            getattr(ws_manager, "subscribed_codes", ()) or ()
        ):
            return "ws_registration_not_recorded"
        transport = getattr(ws_manager, "_market_data_transport_epoch", None)
        epochs = getattr(ws_manager, "_registered_item_epochs", None)
        if (type(transport) is not int or transport <= 0
                or not isinstance(epochs, dict) or epochs.get(item) != transport):
            return "ws_registration_transport_mismatch"
        types = getattr(ws_manager, "_registered_item_types", None)
        if not isinstance(types, dict) or not {"0B", "0D"}.issubset(types.get(item) or ()):
            return "ws_registration_types_missing"
        return ""

    if lock is None:
        return inspect()
    with lock:
        return inspect()


def sent_probe_registration_receipt(ws_manager, *, code, item, lease_id,
                                    now_epoch, send_deadline_epoch, residence_deadline_epoch):
    """Recover only a timely local send whose async completion was delayed.

    This is not a broker ACK or a source-ready receipt. The original lease,
    exact 0B/0D validation and native deadline still govern the source wait.
    """
    times = (now_epoch, send_deadline_epoch, residence_deadline_epoch)
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in times):
        return None
    if now_epoch >= residence_deadline_epoch:
        return None
    lock = getattr(ws_manager, 'lock', None)
    if lock is None:
        return None
    try:
        acquired = lock.acquire(blocking=False)
    except (AttributeError, TypeError):
        return None
    if not acquired:
        return None
    try:
        ready = getattr(ws_manager, '_session_ready', None)
        stopped = getattr(ws_manager, '_stop_event', None)
        if (not getattr(ws_manager, 'websocket', None) or ready is None or not ready.is_set()
                or stopped is None or stopped.is_set()):
            return None
        epoch = getattr(ws_manager, '_market_data_transport_epoch', None)
        lease = getattr(ws_manager, '_exact_probe_item_leases', {}).get(item) or {}
        proof = (getattr(ws_manager, '_micro_reversion_registration_receipt', {}).get('items') or {}).get(item) or {}
        started, sent = lease.get('interval_started_epoch'), proof.get('registration_sent_at_epoch')
        if (type(epoch) is not int or epoch <= 0 or lease.get('lease_id') != lease_id
                or any(type(v) is not int or v != epoch for v in (
                    lease.get('epoch'), proof.get('registration_transport_epoch'),
                    getattr(ws_manager, '_registered_item_epochs', {}).get(item)))
                or lease.get('adopted') or lease.get('removing')
                or item not in getattr(ws_manager, '_micro_reversion_observation_only_items', ())
                or code not in getattr(ws_manager, 'subscribed_codes', ())
                or item not in getattr(ws_manager, '_registered_items_by_code', {}).get(code, ())
                or not {'0B', '0D'}.issubset(getattr(ws_manager, '_registered_item_types', {}).get(item, ()))
                or proof.get('source') != 'zero_base_exact_probe'
                or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in (started, sent))
                or not started <= sent <= min(now_epoch, send_deadline_epoch)):
            return None
        return dict(item=item, lease_id=lease_id, transport_epoch=epoch,
                    created=True, registered=True, interval_started_epoch=started,
                    registration_sent_at_epoch=sent,
                    registration_basis='local_sent_registry_not_broker_ack',
                    reason='exact_probe_timely_send_completion_pending')
    except (AttributeError, TypeError, ValueError):
        return None
    finally:
        lock.release()


def exact_probe_ws_data(
    snapshot: dict, *, code: str, route: str, after_epoch: float,
    now_epoch: float | None = None, max_age_sec: float = 3.0,
) -> tuple[dict, str]:
    """Reject stale or cross-route aggregate data before any machine call."""
    item = probe_item(code, route)
    if not item or not isinstance(snapshot, dict):
        return {}, "invalid_probe_identity"
    route_key = _ROUTE_KEY[route]
    route_snapshots = snapshot.get("realtime_type_snapshots_by_route") or {}
    typed = route_snapshots.get(route_key) if isinstance(route_snapshots, dict) else None
    if not isinstance(typed, dict):
        return {}, "route_snapshot_missing"
    transport = snapshot.get("market_data_transport_epoch")
    if type(transport) is not int or transport <= 0:
        return {}, "transport_epoch_missing"
    for realtime_type in ("0B", "0D"):
        source = typed.get(realtime_type)
        if not isinstance(source, dict):
            return {}, f"{realtime_type}_missing"
        if (
            source.get("item") != item
            or source.get("market_route") != route
            or source.get("transport_epoch") != transport
            or not isinstance(source.get("observed_epoch"), (int, float))
            or source["observed_epoch"] < after_epoch
        ):
            return {}, f"{realtime_type}_stale_or_route_conflict"
        if now_epoch is not None and not 0 <= now_epoch - source["observed_epoch"] <= max_age_sec:
            return {}, f"{realtime_type}_age_exceeded"
    latest_items = snapshot.get("last_realtime_type_item") or {}
    latest_routes = snapshot.get("last_realtime_type_market_route") or {}
    if any(
        latest_items.get(kind) != item or latest_routes.get(kind) != route
        for kind in ("0B", "0D")
    ):
        return {}, "aggregate_route_conflict"
    trade = typed["0B"]
    depth = typed["0D"]
    orderbook = depth.get("orderbook") or {}
    if (
        int(trade.get("current_price") or 0) <= 0
        or not orderbook.get("asks")
        or not orderbook.get("bids")
    ):
        return {}, "required_bbo_trade_missing"
    result = dict(snapshot)
    route_buffers = snapshot.get("recent_trade_ticks_by_route")
    route_ticks = route_buffers.get(route_key) if isinstance(route_buffers, dict) else None
    route_ticks = route_ticks if isinstance(route_ticks, (list, tuple)) else ()
    # The aggregate buffer can contain an earlier item/route from this code.
    # Bind the machine feature window to the same subscription as the 0B/0D
    # readiness receipt. A short, quiet tape remains an honest short window.
    exact_ticks = []
    expected_suffix = route_key.split("|", 1)[0]
    rejected = {"item_or_route": 0, "transport_epoch": 0, "before_registration": 0}
    for tick in route_ticks:
        if (not isinstance(tick, dict) or tick.get("item") != item
            or tick.get("market_route") != route
            or (tick.get("market_suffix") is not None
                and (tick.get("market_suffix") or "KRX") != expected_suffix)):
            rejected["item_or_route"] += 1
        elif tick.get("transport_epoch") != transport:
            rejected["transport_epoch"] += 1
        elif (not isinstance(tick.get("received_at_ms"), (int, float))
              or tick["received_at_ms"] < after_epoch * 1000):
            rejected["before_registration"] += 1
        else:
            exact_ticks.append(tick)
    result["recent_trade_ticks"] = exact_ticks
    result["zero_base_probe_exact_tick_filter"] = {
        "source_row_count": len(route_ticks), "accepted_row_count": len(exact_ticks),
        "rejected_counts": rejected,
    }
    result["zero_base_probe_exact_tick_source"] = route_key
    result["zero_base_probe_registered_epoch"] = after_epoch
    result["curr"] = int(trade["current_price"])
    result["orderbook"] = orderbook
    result["effective_venue"] = _ROUTE_VENUE[route]
    result["market_data_route"] = route
    result["zero_base_probe_trade_epoch"] = trade["observed_epoch"]
    result["zero_base_probe_depth_epoch"] = depth["observed_epoch"]
    return result, "ready"


def probe_ws_observation(snapshot: dict, *, code: str, route: str,
                         after_epoch: float, now_epoch=None) -> dict:
    """Describe exact-route arrivals without promoting them to decision evidence."""
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    key = _ROUTE_KEY[route]
    route_snapshots = snapshot.get("realtime_type_snapshots_by_route")
    typed = route_snapshots.get(key) if isinstance(route_snapshots, dict) else None
    typed = typed if isinstance(typed, dict) else {}
    transport = snapshot.get("market_data_transport_epoch")
    transport = transport if type(transport) is int and transport > 0 else None
    item = probe_item(code, route)
    stamp = time.time() if now_epoch is None else now_epoch
    observed = {}
    for kind in ("0B", "0D"):
        source = typed.get(kind)
        source = source if isinstance(source, dict) else {}
        epoch = source.get("observed_epoch")
        observed[kind] = (
            round((epoch - after_epoch) * 1000)
            if type(epoch) in (int, float) and math.isfinite(epoch) and after_epoch <= epoch <= stamp
            and source.get("item") == item
            and source.get("market_route") == route
            and transport is not None and source.get("transport_epoch") == transport
            else None
        )
    arrival_quality={}
    def arrivals(buffer_name):
        buffers = snapshot.get(buffer_name)
        rows = buffers.get(key) if isinstance(buffers, dict) else None
        rows = rows if isinstance(rows, (list, tuple)) else []
        count, first, signed_first = 0, [], []
        signed_count = 0
        unique={};conflicts=set();missing=0;duplicates=0
        for row in rows:
            if not isinstance(row, dict):
                continue
            received = row.get('received_at_ms')
            if (type(received) not in (int, float) or not math.isfinite(received)
                    or not after_epoch*1000 <= received <= stamp*1000
                    or row.get('item') != item or row.get('market_route') != route
                    or transport is None or row.get('transport_epoch') != transport):
                continue
            sequence=row.get('route_sequence')
            if type(sequence) is not int or sequence<=0:
                missing+=1;continue
            if sequence in unique:
                duplicates+=1
                if unique[sequence]!=row:conflicts.add(sequence)
                continue
            unique[sequence]=row
        arrival_quality[buffer_name]=dict(identity_missing=missing,duplicates=duplicates,conflicts=len(conflicts))
        for sequence,row in unique.items():
            if sequence in conflicts:continue
            received=row['received_at_ms']
            count += 1
            delay = int(received-after_epoch*1000)
            bisect.insort(first, delay)
            del first[5:]
            if (row.get('aggressor_source') == 'kiwoom_0b_signed_trade_volume'
                    and row.get('aggressor_side') in {'BUY', 'SELL'}):
                signed_count += 1
                bisect.insort(signed_first, delay)
                del signed_first[5:]
        return count, first, signed_count, signed_first
    trades = arrivals("recent_trade_ticks_by_route")
    depths = arrivals("recent_depth_ticks_by_route")
    clocks = {}
    for kind in ('0B', '0D'):
        source = typed.get(kind) or {}
        exact = (source.get('item') == item and source.get('market_route') == route
                 and transport is not None and source.get('transport_epoch') == transport
                 and observed[kind] is not None)
        latency = source.get('market_source_latency') or {}
        bound = exact and all(latency.get(k) == source.get(k)
                              for k in ('item', 'transport_epoch', 'route_sequence'))
        def number(value):
            return value if type(value) in (int, float) and math.isfinite(value) else None
        received = number(source.get('observed_epoch')) if exact else None
        clocks[kind] = dict(item=item, route=route, transport_epoch=transport,
            route_sequence=source.get('route_sequence') if exact else None,
            provider_epoch=number(source.get('provider_trade_epoch')) if exact else None,
            received_epoch=received, read_epoch=stamp,
            age_ms=round((stamp-received)*1000, 3) if received is not None else None,
            packet_received_epoch=number(latency.get('packet_received_epoch')) if bound else None,
            callback_started_epoch=number(latency.get('dispatch_started_epoch')) if bound else None,
            normalized_epoch=number(latency.get('normalized_epoch')) if bound else None,
            native_ingest_returned_epoch=number(latency.get('native_ingest_returned_epoch')) if bound else None,
            first_unobserved_boundary=('exact_normalized_snapshot' if not exact else
                'packet_receive_clock' if not bound or number(latency.get('packet_received_epoch')) is None else
                'native_ingest_receipt' if kind == '0B' else None),
            cause='unobservable' if not exact else 'exact_normalized_source_observed')
    return {
        'source_clocks': clocks,
        'arrival_quality':arrival_quality,
        'first_data_basis': 'earliest_retained_exact_interval_row_not_guaranteed_first_packet',
        "first_0b_ms": trades[1][0] if trades[1] else None,
        "first_0d_ms": depths[1][0] if depths[1] else None,
        "latest_0b_ms": observed["0B"],
        "latest_0d_ms": observed["0D"],
        "exact_0b_count": trades[0],
        "exact_0d_count": depths[0],
        "signed_0b_count": trades[2],
        "fifth_0b_ms": trades[1][4] if len(trades[1]) >= 5 else None,
        "fifth_signed_0b_ms": trades[3][4] if len(trades[3]) >= 5 else None,
    }


def wait_for_exact_probe_ws_data(ws_manager, *, code: str, route: str,
                                 after_epoch: float, now=time.time,
                                 timeout_sec: float = 10.0,
                                 empty_timeout_sec: float = 5.0,
                                 min_warmup_sec: float = 0.0,
                                 partial_extension_sec: float = 0.0,
                                 poll_interval_sec: float = 0.05,
                                 min_exact_0b_count: int = 0,
                                 residence_deadline_epoch: float | None = None,
                                 required_window_sec: float = 0.0,
                                 readiness_guard=None) -> tuple[dict, dict, str]:
    """Use one bounded lease for fresh 0B/0D and the machine's WS tick floor."""
    started = time.monotonic()
    deadline = started + max(0.0, timeout_sec)
    empty_deadline = started + min(max(0.0, timeout_sec), max(0.0, empty_timeout_sec))
    snapshot = {}
    source_reason = "route_snapshot_missing"
    partial_extension_applied = False
    empty_source_flushed = False
    residence_wait = False
    residence_deadline = (started + max(0., residence_deadline_epoch-now())
                          if residence_deadline_epoch is not None else None)
    if residence_deadline is not None:
        deadline = min(deadline, residence_deadline)
        empty_deadline = min(empty_deadline, residence_deadline)
    expected_transport=getattr(ws_manager,'_market_data_transport_epoch',None)
    item = probe_item(code, route)
    with _ExactProbeSourceWait(ws_manager, item) as source_wait:
        while True:
            sequence = source_wait.sequence(expected_transport, active=residence_wait)
            issue=readiness_guard() if readiness_guard is not None else ''
            if issue:
                ws_data={};source_reason=issue
                break
            snapshot = probe_ws_snapshot(ws_manager, code=code, route=route)
            transport=snapshot.get('market_data_transport_epoch')
            if expected_transport is None and type(transport) is int:
                expected_transport = transport
                if residence_wait:
                    # Bind the notification scope before checking this learned
                    # transport again; a packet can arrive after this snapshot.
                    continue
            if expected_transport is not None and transport not in (None,expected_transport):
                ws_data={};source_reason='transport_changed_during_source_wait'
                break
            ws_data, source_reason = exact_probe_ws_data(
                snapshot, code=code, route=route, after_epoch=after_epoch,
                now_epoch=now(),
            )
            observation = probe_ws_observation(
                snapshot, code=code, route=route, after_epoch=after_epoch, now_epoch=now(),
            )
            if (ws_data and observation["exact_0b_count"] >= min_exact_0b_count
                    and time.monotonic() - started >= min_warmup_sec):
                break
            if (
                not observation["exact_0b_count"]
                and not observation["exact_0d_count"]
                and observation["latest_0b_ms"] is None
                and observation["latest_0d_ms"] is None
                and time.monotonic() >= empty_deadline
            ):
                empty_source_flushed = True
                break
            if time.monotonic() >= deadline:
                first_ms = observation.get('first_0b_ms')
                # Native ingestion already observes real prints during source wait;
                # never restart its history at the fifth print or borrow a lease.
                covered = (max(0., now()-after_epoch-first_ms/1000)
                           if first_ms is not None else 0.)
                window_left = max(0., required_window_sec-covered)
                if (not residence_wait and residence_deadline is not None
                        and (observation['exact_0b_count'] or observation['exact_0d_count'])
                        and time.monotonic()+window_left < residence_deadline):
                    deadline = residence_deadline
                    residence_wait = True
                    continue
                one_sided = bool(observation["exact_0b_count"]) != bool(observation["exact_0d_count"])
                if (not residence_wait and not partial_extension_applied
                        and partial_extension_sec > 0 and one_sided):
                    deadline = started + max(0.0, timeout_sec) + min(2.0, partial_extension_sec)
                    if residence_deadline is not None:
                        deadline = min(deadline, residence_deadline)
                    partial_extension_applied = True
                else:
                    break
            remaining = deadline - time.monotonic()
            if (not observation['exact_0b_count'] and not observation['exact_0d_count']
                    and observation['latest_0b_ms'] is None and observation['latest_0d_ms'] is None):
                remaining=min(remaining,empty_deadline-time.monotonic())
            if remaining > 0:
                if residence_wait:
                    from src.engine.scalping.reversal_source_diagnostics import wait_observation
                    wait_observation(item, sequence, min(1., remaining))
                else:
                    time.sleep(min(max(0.01, poll_interval_sec), remaining))
    elapsed = time.monotonic() - started
    observation = probe_ws_observation(snapshot,code=code,route=route,after_epoch=after_epoch,now_epoch=now())
    if ws_data and elapsed < max(0.0, min_warmup_sec):
        ws_data, source_reason = {}, "warmup_timeout"
    observation["wait_ms"] = round(elapsed * 1000)
    observation["base_wait_budget_ms"] = round(max(0.0, timeout_sec) * 1000)
    observation["effective_wait_budget_ms"] = round(
        (min(max(0.0, timeout_sec), max(0.0, empty_timeout_sec))
         if empty_source_flushed else
         max(0.0, timeout_sec) +
         (min(2.0, partial_extension_sec) if partial_extension_applied else 0.0)) * 1000
    )
    observation["wait_reason"] = source_reason
    observation["sample_target"] = min_exact_0b_count
    observation["min_warmup_ms"] = round(max(0.0, min_warmup_sec) * 1000)
    observation["sample_target_met"] = observation["exact_0b_count"] >= min_exact_0b_count
    observation["partial_extension_applied"] = partial_extension_applied
    observation["empty_source_flushed"] = empty_source_flushed
    observation['residence_wait_applied'] = residence_wait
    observation['residence_deadline_epoch'] = residence_deadline_epoch
    if residence_wait:
        observation['effective_wait_budget_ms'] = round((deadline-started)*1000)
    return ws_data, observation, source_reason


def probe_ws_snapshot(ws_manager, *, code: str, route: str) -> dict:
    """Read the exact registered item, including an existing observation view."""
    item = probe_item(code, route)
    reader = getattr(ws_manager, "get_exact_item_data", None)
    if callable(reader):
        return reader(code, item) or {}
    return ws_manager.get_latest_data(code) or {}


def _wait_for_probe_quote_retry(ws_manager, *, pending, code, route,
                               after_epoch, budget, readiness_guard, now):
    """Await one post-failure 0D within the original observed signal budget."""
    from src.engine.scalping.entry_machine_source_recovery import observer_quote_refresh
    from src.engine.scalping.reversal_source_diagnostics import wait_observation

    item = probe_item(code, route)
    with _ExactProbeSourceWait(ws_manager, item) as source_wait:
        while True:
            sequence = source_wait.sequence(pending["transport_epoch"], active=True)
            issue = readiness_guard()
            if issue:
                return {}, {"allowed": False, "reason": issue}
            if budget.remaining() <= 0:
                return {}, {"allowed": False, "reason": "original_native_deadline_expired"}
            snapshot = probe_ws_snapshot(ws_manager, code=code, route=route)
            refresh = observer_quote_refresh(pending, snapshot, now=now())
            if refresh.get("clear"):
                return {}, refresh
            if refresh.get("allowed"):
                data, reason = exact_probe_ws_data(
                    snapshot, code=code, route=route, after_epoch=after_epoch,
                    now_epoch=now(),
                )
                if data and budget.remaining() > 0:
                    return data, refresh
                if not data:
                    return {}, {**refresh, "allowed": False, "reason": reason}
            remaining = budget.remaining()
            if remaining <= 0:
                return {}, {**refresh, "allowed": False, "reason": "original_native_deadline_expired"}
            wait_observation(item, sequence, min(1.0, remaining))


def exact_probe_rest_sources(ticks, candle_meta, *, request_code, now_epoch,
                             allow_empty_ticks=False):
    """Keep REST feature rows on the requested venue and bounded receive clock."""
    return not exact_probe_rest_source_issue(
        ticks, candle_meta, request_code=request_code, now_epoch=now_epoch,
        allow_empty_ticks=allow_empty_ticks,
    )


def exact_probe_rest_source_issue(ticks, candle_meta, *, request_code, now_epoch,
                                  allow_empty_ticks=False, transport_epoch=None):
    """Identify the failed source field without retaining market data or credentials."""
    if (not isinstance(ticks, list) or (not ticks and not allow_empty_ticks)
        or not isinstance(candle_meta, dict)):
        return "source_shape_invalid"
    if candle_meta.get("request_code") != request_code:
        return "candle_route_mismatch"
    if candle_meta.get('api_id') == 'WS_0B_completed_1m':
        source = candle_meta.get('completed_bar_source') or {}
        if candle_meta.get("decision_input_profile") == "reduced_completed_v1":
            issue = completed_ws_candle_source_issue(source, request_code=request_code,
                transport_epoch=transport_epoch, now_epoch=now_epoch)
            if issue:
                return issue
        generated = source.get('generated_at_epoch')
        available = source.get('available_at_epoch')
        if (source.get('request_code') != request_code
                or source.get('adjustment') != 'raw_same_day'
                or type(transport_epoch) is not int or transport_epoch <= 0
                or source.get('transport_epoch') != transport_epoch
                or not re.fullmatch(r'[0-9a-f]{64}', str(source.get('content_sha256', '')))):
            return 'candle_ws_provenance_invalid'
        if (candle_meta.get("decision_input_profile") != "reduced_completed_v1"
                and (type(generated) not in (int, float) or not 0 <= now_epoch - generated <= 20
                or type(available) not in (int, float) or not 0 < available <= now_epoch)):
            return 'candle_ws_clock_invalid'
    else:
        candle_received = candle_meta.get("rest_received_ts_ms")
        if not isinstance(candle_received, int) or not 0 <= now_epoch - candle_received / 1000 <= 120:
            return "candle_receive_clock_invalid"
    for tick in ticks:
        if not isinstance(tick, dict) or tick.get("request_code") != request_code:
            return "tick_route_mismatch"
        received = tick.get("rest_received_ts_ms")
        if not isinstance(received, int) or not 0 <= now_epoch - received / 1000 <= 10:
            return "tick_receive_clock_invalid"
    return ""


_READINESS_LOCK = threading.Lock()
_READINESS_IDENTITY = None
_READINESS_GENERATION = None


def consumer_readiness(*, ws_manager, ai_engine, token, enabled, family_sha256,
                       now_epoch=None):
    """Inspect existing normalized runtime state; no auth or WS operation."""
    ready_event = getattr(ws_manager, '_session_ready', None)
    stopped = getattr(ws_manager, '_stop_event', None)
    epoch = getattr(ws_manager, '_market_data_transport_epoch', 0)
    from src.engine.scalping.reversal_source_diagnostics import _PROCESS_START_TICKS
    from src.trading.market import session_contract as S
    stamp = time.time() if now_epoch is None else now_epoch
    session = S.resolve_market_session(datetime.fromtimestamp(stamp, S.KST)).session_regime
    route = ('nxt_only' if session == S.MARKET_SESSION_REGIME_LEGACY_PREMARKET else
             'krx_nxt_integrated' if session in {S.MARKET_SESSION_REGIME_KRX_REGULAR,
                 S.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET} else None)
    # Compare existing configuration only, without reading or refreshing auth.
    rest_host = urlsplit(kiwoom_utils.KIWOOM_BASE_URL).hostname
    ws_host = urlsplit(str(getattr(ws_manager, 'uri', ''))).hostname
    environment_matches = rest_host == ws_host and rest_host in {'api.kiwoom.com', 'mockapi.kiwoom.com'}
    checks = (
        ('runtime_disabled', bool(enabled)),
        ('ws_manager_missing', ws_manager is not None),
        ('ws_session_not_ready', bool(getattr(ws_manager, 'websocket', None))
            and ready_event is not None and ready_event.is_set()
            and not (stopped is not None and stopped.is_set())),
        ('ws_epoch_missing', type(epoch) is int and epoch > 0),
        ('machine_consumer_missing', bool(family_sha256)),
        ('ai_consumer_missing', ai_engine is not None),
        ('auth_missing', bool(token)),
        ('auth_environment_mismatch', environment_matches),
        ('market_session_closed', route is not None),
    )
    reason = next((name for name, valid in checks if not valid), 'ready')
    day = str(datetime.fromtimestamp(stamp, S.KST).date())
    # References are compared locally; no credential or credential digest leaves
    # this owner. One generation per process, never an expanding auth ledger.
    identity = (os.getpid(), day, session, route, epoch, family_sha256,
                ws_manager, getattr(ws_manager, 'websocket', None),
                ai_engine, token, getattr(ws_manager, 'token', None), reason)
    global _READINESS_IDENTITY, _READINESS_GENERATION
    with _READINESS_LOCK:
        if identity != _READINESS_IDENTITY:
            _READINESS_IDENTITY = identity
            _READINESS_GENERATION = uuid.uuid4().hex
        generation = _READINESS_GENERATION
    return dict(schema='zero_base_consumer_readiness_v2', ready=reason == 'ready',
        reason=reason, first_missing_dependency=None if reason == 'ready' else reason,
        runtime_generation=generation, process_pid=os.getpid(), process_start_ticks=_PROCESS_START_TICKS,
        date=day, session=session, route=route, transport_epoch=epoch,
        consumer_open=not bool(stopped and stopped.is_set()), ws_manager_present=ws_manager is not None,
        ws_session_ready=checks[2][1], ai_engine_present=ai_engine is not None,
        token_present=bool(token), auth_environment_matches=environment_matches,
        machine_policy_ready=bool(family_sha256),
        machine_family_sha256=family_sha256, auth_present=bool(token),
        observed_epoch=stamp, runtime_effect=False)


def readiness_issue(expected, current):
    if current.get('ready') is not True:
        return current.get('reason') or 'consumer_not_ready'
    if not isinstance(expected, dict) or not expected.get('runtime_generation'):
        return 'consumer_readiness_receipt_missing'
    if any(expected.get(k) != current.get(k) for k in (
            'runtime_generation', 'process_pid', 'process_start_ticks', 'date',
            'session', 'route', 'transport_epoch', 'machine_family_sha256')):
        return 'consumer_readiness_generation_changed'
    return ''


def run_zero_base_probe(
    request: dict,
    *,
    ws_manager,
    ai_engine,
    token: str,
    now=time.time,
    tick_fetcher=None,
    candle_fetcher=None,
    context_builder=None,
    release_ws=None,
    ws_wait_timeout_sec: float = 10.0,
    ws_wait_empty_timeout_sec: float = 5.0,
    ws_min_warmup_sec: float = 0.0,
    ws_wait_partial_extension_sec: float = 0.0,
    ws_wait_min_exact_0b_count: int = 5,
    retain_ws_on_recheck: bool = False,
    ws_lease_id: str | None = None,
    native_wait_deadline_epoch: float | None = None,
) -> dict:
    """Observe one candidate. The caller owns bounded WS REG/REMOVE leases."""
    claim = dict(request.get("claim") or {})
    residence_perf = (time.perf_counter() + max(0, native_wait_deadline_epoch-now())
                      if native_wait_deadline_epoch is not None else None)
    candidate = dict(request.get("candidate") or {})
    code, route = claim.get("code"), claim.get("route")
    result = {
        "schema": RESULT_SCHEMA,
        "observation_requirements": claim.get('observation_requirements'),
        "consumer_readiness": request.get('consumer_readiness'),
        "residence_reserved_epoch": claim.get('last_claim_epoch'),
        "residence_deadline_epoch": native_wait_deadline_epoch,
        "claim": claim,
        "candidate": candidate,
        "result": "source_unavailable",
        "reason": "unknown",
        "machine_action": "",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    item = probe_item(code or "", route or "")
    descriptor_candidate = SimpleNamespace(code=code, route=route,
        discovery_price=candidate.get('discovery_price') or 0)
    if not item or candidate.get("code") != code or candidate.get("route") != route:
        result["reason"] = "candidate_claim_identity_mismatch"
        return result
    observed_epoch = float(claim.get("observed_epoch") or 0)
    if observed_epoch <= 0 or now() - observed_epoch > 120 or observed_epoch > now():
        result["reason"] = "discovery_observation_stale"
        return result
    if ws_manager is None or ai_engine is None or not token:
        result["result"] = "policy_unavailable"
        result["reason"] = "runtime_dependency_missing"
        return result
    exact_lease = callable(getattr(ws_manager, "execute_acquire_exact_probe_item", None))
    lease_id = ws_lease_id or uuid.uuid4().hex
    lease_requested = False

    def cleanup():
        if exact_lease:
            return ws_manager.execute_release_exact_probe_item(item, lease_id)
        if callable(release_ws):
            return release_ws(code, item)

    def release():
        if exact_lease and callable(release_ws):
            return release_ws(code, item, lease_id)
        return cleanup()

    subscribed_codes = getattr(ws_manager, "subscribed_codes", set())
    registered_items = getattr(ws_manager, "_registered_items_by_code", {})
    if code in subscribed_codes and hasattr(ws_manager, "_registered_items_by_code"):
        if item not in registered_items.get(code, ()) and not exact_lease:
            result["reason"] = "exact_route_subscription_conflict"
            return result
        was_subscribed = item in registered_items.get(code, ())
    else:
        was_subscribed = code in subscribed_codes and item == code
    registered_epoch = now()
    deferred_release = False
    try:
        if not exact_lease and was_subscribed and hasattr(ws_manager, "_registered_item_epochs"):
            registration_reason = probe_registration_receipt(
                ws_manager, code=code, item=item,
            )
            if registration_reason:
                result["reason"] = registration_reason
                return result
        if exact_lease or not was_subscribed:
            lease_requested = exact_lease
            registration = ws_manager.execute_acquire_exact_probe_item(item, lease_id) if exact_lease else ws_manager.execute_subscribe(
                [item], source="zero_base_probe", observation_only=True,
                required_realtime_types=("0B", "0D"), realtime_types=("0B", "0D"),
            )
            if registration is None:
                result["reason"] = "ws_registration_not_dispatched"
                return result
            try:
                lease_receipt = registration.result(timeout=3.0)
                if exact_lease:
                    result["ws_registration"] = lease_receipt
                    if not isinstance(lease_receipt, dict) or lease_receipt.get("registered") is not True:
                        result["reason"] = (lease_receipt.get("reason", "ws_registration_unconfirmed")
                                            if isinstance(lease_receipt, dict) else "ws_registration_unconfirmed")
                        return result
                    if lease_receipt.get("server_registration_rejected") is True:
                        result["reason"] = "exact_probe_registration_rejected"
                        return result
                    if lease_receipt.get('interval_started_epoch'):
                        registered_epoch = float(lease_receipt['interval_started_epoch'])
            except FutureTimeoutError:
                sent_receipt = (sent_probe_registration_receipt(
                    ws_manager, code=code, item=item, lease_id=lease_id, now_epoch=now(),
                    send_deadline_epoch=registered_epoch + 3.0,
                    residence_deadline_epoch=native_wait_deadline_epoch,
                ) if exact_lease else None)
                if sent_receipt:
                    # The wire send finished in its original budget. Continue
                    # source validation; cleanup remains owned by this probe.
                    result['ws_registration'] = sent_receipt
                    registered_epoch = sent_receipt['interval_started_epoch']
                else:
                    if exact_lease or callable(release_ws):
                        registration.add_done_callback(
                            lambda _future: release()
                        )
                        deferred_release = True
                        result["_ws_cleanup_deferred"] = True
                    result["reason"] = "ws_registration_timeout"
                    return result
            except Exception as exc:
                result["reason"] = "ws_registration_failed:" + type(exc).__name__
                return result
            registration_reason = probe_registration_receipt(
                ws_manager, code=code, item=item,
            )
            if registration_reason:
                result["reason"] = registration_reason
                return result
        # Registration is not route provenance. The shared candle resolver
        # needs actual exact-route WS rows before choosing an integrated chart.
        ws_data = probe_ws_snapshot(ws_manager, code=code, route=route) or {}
        tick_fetcher = tick_fetcher or kiwoom_utils.get_tick_history_ka10003
        candle_fetcher = candle_fetcher or fetch_entry_candles_with_meta
        context_builder = context_builder or build_entry_candle_context
        venue = _ROUTE_VENUE[route]
        session = resolve_entry_candle_session()
        request_code = resolve_entry_candle_request_code(
            code, venue=venue, session=session, ws_data=ws_data,
        )
        ticks, candles, candle_meta, context = [], [], {}, {}
        try:
            def source_readiness_guard():
                control_failure = getattr(ws_manager, "exact_probe_control_failure", None)
                if exact_lease and callable(control_failure):
                    rejection = control_failure(item, lease_id)
                    if rejection:
                        return rejection
                expected=request.get('consumer_readiness')
                if expected is None:return ''  # Explicit legacy fixture surface.
                from src.engine.scalping.reversal_current_backend import backend
                current=consumer_readiness(ws_manager=ws_manager,ai_engine=ai_engine,
                    token=token,enabled=True,family_sha256=backend()._GENERATION,now_epoch=now())
                return readiness_issue(expected,current)
            ws_data, observation, source_reason = wait_for_exact_probe_ws_data(
                ws_manager, code=code, route=route, after_epoch=registered_epoch,
                now=now, timeout_sec=ws_wait_timeout_sec,
                empty_timeout_sec=ws_wait_empty_timeout_sec,
                min_warmup_sec=max(0, ws_min_warmup_sec-(now()-registered_epoch)),
                partial_extension_sec=ws_wait_partial_extension_sec,
                min_exact_0b_count=ws_wait_min_exact_0b_count,
                residence_deadline_epoch=native_wait_deadline_epoch,
                required_window_sec=(claim.get('observation_requirements') or {}).get('any_branch_minimum_seconds') or 0,
                readiness_guard=source_readiness_guard,
            )
            result["ws_observation"] = observation
            if not ws_data:
                registration_reason = (
                    probe_registration_receipt(ws_manager, code=code, item=item)
                    if source_reason == "route_snapshot_missing"
                    and hasattr(ws_manager, "_registered_item_epochs")
                    else ""
                )
                result["reason"] = registration_reason or source_reason
                if source_reason.startswith('consumer_readiness_'):
                    result['result']='policy_unavailable'
                return result
            if native_wait_deadline_epoch is not None:
                from src.engine.scalping.reversal_source_diagnostics import branch_readiness
                result['first_data_branch_readiness'] = branch_readiness(descriptor_candidate,
                    now=now(), deadline=native_wait_deadline_epoch,
                    original_requirements=claim.get('observation_requirements'))
            if native_wait_deadline_epoch is None:
                candles, candle_meta = candle_fetcher(
                    token, code, ws_data, venue=venue, session=session, limit=40,
                    now_ts=now(), allow_integrated_sor_execution_view=True, reduced_inputs=True,
                    request_owner="zero_base_machine_probe",
                    request_class=REQUEST_CLASS_SOURCE_ONLY,
                )
                if not candles:
                    result["result"] = "required_feature_insufficient"
                    result["reason"] = "candle_source_missing"
                    result["machine_source_gap_kind"] = "candle_source_missing"
                    result["rest_source_gap_detail"] = str((candle_meta or {}).get(
                        "read_rate_control_reason") or (candle_meta or {}).get(
                        "source_error") or "candle_rows_missing")[:160]
                    return result
                candle_issue = exact_probe_rest_source_issue(
                    [], candle_meta, request_code=request_code, now_epoch=now(),
                    allow_empty_ticks=True, transport_epoch=ws_data.get("market_data_transport_epoch"),
                )
                if candle_issue:
                    result["reason"] = "rest_route_or_receive_clock_invalid"
                    result["rest_source_gap_detail"] = candle_issue
                    return result
                # Reuse exactly the machine feature owner's selection rule. Refresh
                # after the chart read; a pre-read WS window may have aged/reconnected.
                ws_data, source_reason = exact_probe_ws_data(
                    probe_ws_snapshot(ws_manager, code=code, route=route),
                    code=code, route=route, after_epoch=registered_epoch, now_epoch=now(),
                )
                if not ws_data:
                    result["reason"] = "pre_tick_" + source_reason
                    return result
                _, tick_source, tick_selection_reason = _select_recent_ticks_with_source(
                    ws_data, [], now=now(),
                )
                result["tick_read_source"] = tick_source
                result["tick_read_selection_reason"] = tick_selection_reason
                # The tick clock has a 10-second bound. Fetch it last so a slow
                # candle response cannot age a fresh tick before validation.
                ticks = [] if tick_source == "ws_exact_route" else tick_fetcher(
                    token, request_code, limit=10,
                    request_owner="zero_base_machine_probe",
                    request_class=REQUEST_CLASS_SOURCE_ONLY,
                    explicit_request_code=True,
                )
        except Exception as exc:
            result["reason"] = "required_rest_source_failed:" + type(exc).__name__
            return result
        if native_wait_deadline_epoch is None:
            exact_ws_ticks = ws_data.get("recent_trade_ticks") or []
            if (not ticks and not exact_ws_ticks) or not candles:
                result["result"] = "required_feature_insufficient"
                result["reason"] = "tick_or_candle_missing"
                return result
            rest_source_issue = exact_probe_rest_source_issue(
                ticks, candle_meta, request_code=request_code, now_epoch=now(),
                allow_empty_ticks=bool(exact_ws_ticks), transport_epoch=ws_data.get("market_data_transport_epoch"),
            )
            if rest_source_issue:
                result["reason"] = "rest_route_or_receive_clock_invalid"
                result["rest_source_gap_detail"] = rest_source_issue
                return result
            # The probe owns only these two source-only REST reads. Do not let the
            # shared context helper fan out into auxiliary index/investor requests.
            probe_candle_meta = dict(candle_meta)
            probe_candle_meta["multi_timeframe_auxiliary_fetch"] = False
            try:
                context = context_builder(
                    token, code, ws_data, venue=venue, session=session, limit=40,
                    model_bar_limit=20, now_ts=now(), recent_candles=candles,
                    source_meta=probe_candle_meta, include_investor_source=False,
                )
            except Exception as exc:
                result["reason"] = "candle_context_failed:" + type(exc).__name__
                return result
            if not isinstance(context, dict):
                result["result"] = "required_feature_insufficient"
                result["reason"] = "candle_context_missing"
                return result
        native_budget = None
        if native_wait_deadline_epoch is not None:
            from src.engine.scalping.reversal_source_diagnostics import (
                observe_snapshot, observation_sequence, wait_observation, branch_readiness)
            from src.engine.scalping.reversal_current_backend import backend
            absolute_perf = residence_perf
            while True:
                issue=source_readiness_guard()
                if issue:
                    result['result']='policy_unavailable';result['reason']=issue
                    return result
                sequence = observation_sequence(item)
                family = backend()._GENERATION
                native_snapshot, native_receipt = observe_snapshot(code,
                    'NXT' if route == 'nxt_only' else 'SOR', session,
                    now=now(), item=item, family_sha256=family)
                result['native_observation_receipt'] = native_receipt
                result['native_history_summary'] = native_history_summary(native_receipt)
                result['residence_remaining_seconds'] = max(0, native_wait_deadline_epoch-now())
                if native_snapshot is not None:
                    from src.engine.scalping.entry_deadline import EntryDeadline
                    native_budget = EntryDeadline.create(caller_epoch=native_snapshot[0]['epoch']+5)
                    break
                remaining = min(native_wait_deadline_epoch-now(), absolute_perf-time.perf_counter())
                if remaining <= 0:
                    result['branch_readiness'] = branch_readiness(descriptor_candidate, now=now(),
                        deadline=native_wait_deadline_epoch, original_requirements=claim.get('observation_requirements'))
                    readiness = result['branch_readiness'] or {}
                    result['result'],result['reason']=native_wait_result(native_receipt,readiness)
                    return result
                wait_observation(item, sequence, min(remaining, 1.0))
        refreshed_snapshot = probe_ws_snapshot(ws_manager, code=code, route=route)
        result["ws_observation_pre_machine"] = probe_ws_observation(
            refreshed_snapshot or {}, code=code, route=route,
            after_epoch=registered_epoch, now_epoch=now(),
        )
        if native_wait_deadline_epoch is not None:
            result['branch_readiness'] = branch_readiness(descriptor_candidate, now=now(),
                deadline=native_wait_deadline_epoch, original_requirements=claim.get('observation_requirements'))
            clock = result['ws_observation_pre_machine']['source_clocks']['0B']
            native = result.get('native_observation_receipt') or {}
            clock['native_last_sequence'] = native.get('native_sequence')
            clock['native_observed_epoch'] = native.get('observed_epoch')
            clock['native_sequence_matches'] = (clock['route_sequence'] is not None
                and native.get('native_epoch') == clock['transport_epoch']
                and native.get('native_sequence') == clock['route_sequence'])
            if clock['native_sequence_matches'] and clock['first_unobserved_boundary'] == 'native_ingest_receipt':
                clock['first_unobserved_boundary'] = None
        ws_data, source_reason = exact_probe_ws_data(
            refreshed_snapshot, code=code, route=route,
            after_epoch=registered_epoch, now_epoch=now(),
        )
        if not ws_data:
            result["reason"] = "pre_machine_" + source_reason
            return result
        if native_budget is not None:
            # Residence may span several minutes. Keep the event's original
            # five-second budget when refreshing the prepared chart/context.
            try:
                with kiwoom_utils.entry_source_budget(native_budget):
                    native_budget.require()
                    candles, candle_meta = candle_fetcher(
                        token, code, ws_data, venue=venue, session=session, limit=40,
                        now_ts=now(), allow_integrated_sor_execution_view=True, reduced_inputs=True,
                        request_owner='zero_base_machine_probe',
                        request_class=REQUEST_CLASS_SOURCE_ONLY)
                    source_issue = exact_probe_rest_source_issue([], candle_meta,
                        request_code=request_code, now_epoch=now(), allow_empty_ticks=True,
                        transport_epoch=ws_data.get("market_data_transport_epoch"))
                    if not candles or source_issue:
                        result['reason'] = source_issue or 'candle_refresh_empty'
                        return result
                    ws_data, source_reason = exact_probe_ws_data(
                        probe_ws_snapshot(ws_manager, code=code, route=route),
                        code=code, route=route, after_epoch=registered_epoch, now_epoch=now())
                    if not ws_data:
                        result['reason'] = 'post_candle_' + source_reason
                        return result
                    _, tick_source, tick_reason = _select_recent_ticks_with_source(
                        ws_data, [], now=now())
                    result['tick_read_source'] = tick_source
                    result['tick_read_selection_reason'] = tick_reason
                    ticks = [] if tick_source == 'ws_exact_route' else tick_fetcher(
                        token, request_code, limit=10,
                        request_owner='zero_base_machine_probe',
                        request_class=REQUEST_CLASS_SOURCE_ONLY, explicit_request_code=True)
                    source_issue = exact_probe_rest_source_issue(ticks, candle_meta,
                        request_code=request_code, now_epoch=now(),
                        allow_empty_ticks=bool(ws_data.get('recent_trade_ticks')),
                        transport_epoch=ws_data.get('market_data_transport_epoch'))
                    if source_issue or (not ticks and not ws_data.get('recent_trade_ticks')):
                        result['reason'] = source_issue or 'trusted_tape_source_insufficient'
                        return result
                    context = context_builder(token, code, ws_data, venue=venue,
                        session=session, limit=40, model_bar_limit=20, now_ts=now(),
                        recent_candles=candles, source_meta=dict(candle_meta,
                            multi_timeframe_auxiliary_fetch=False), include_investor_source=False)
                    native_budget.require()
            except Exception as exc:
                result['reason'] = 'native_context_refresh_failed:' + type(exc).__name__
                return result
        if result.get("tick_read_source") == "ws_exact_route":
            _, current_tick_source, _ = _select_recent_ticks_with_source(
                ws_data, [], now=now(),
            )
            if current_tick_source != "ws_exact_route":
                result["result"] = "required_feature_insufficient"
                result["reason"] = "ws_tick_source_changed_before_machine"
                result["machine_source_gap_kind"] = "trusted_tape_source_insufficient"
                return result
        observation_context = None
        if native_budget is not None:
            from src.engine.scalping.reversal_source_diagnostics import _PROCESS_START_TICKS
            observation_context = dict(
                schema="entry_source_quote_observer_v1", snapshot=deepcopy(native_snapshot),
                family_sha256=family, deadline_epoch=native_budget.epoch,
                deadline_perf=native_budget.perf, observer_pid=os.getpid(),
                observer_start_ticks=_PROCESS_START_TICKS,
            )
        try:
            for calculation_index in range(2):
                machine = ai_engine.analyze_target(
                    candidate.get("name") or code, ws_data, ticks, candles,
                    strategy="SCALPING", prompt_profile="watching", machine_only=True,
                    **({'entry_input_deadline_epoch': native_budget.epoch,
                        'entry_input_deadline_perf': native_budget.perf,
                        'entry_source_recovery_observation': observation_context}
                       if native_budget is not None else {}),
                    metadata_extra={
                        "position_tag": "SCANNER",
                        "source_event_stage": "zero_base_probe_machine_only_v1",
                        "zero_base_source_sha256": claim.get("source_sha256"),
                        "zero_base_route": route,
                    },
                    candle_context=context,
                ) or {}
                if calculation_index or observation_context is None:
                    break
                from src.engine.scalping.entry_machine_source_recovery import (
                    probe_quote_retry_pending, observer_quote_context,
                )
                pending = probe_quote_retry_pending(
                    machine, observation_context, ws_data, now=now(),
                )
                if pending is None:
                    break
                result["quote_recovery_parent"] = {
                    key: deepcopy(machine.get(key)) for key in (
                        "evaluation_attempt_id", "machine_observation_sha256",
                        "machine_evaluation_status", "machine_capture_status",
                    )
                }
                refreshed, retry = _wait_for_probe_quote_retry(
                    ws_manager, pending=pending, code=code, route=route,
                    after_epoch=registered_epoch, budget=native_budget,
                    readiness_guard=source_readiness_guard, now=now,
                )
                result["quote_recovery_delivery"] = retry
                if not refreshed:
                    break
                # Rebuild the canonical view over the same candle/tape inputs.
                # The context builder cannot fetch auxiliary sources here.
                with kiwoom_utils.entry_source_budget(native_budget):
                    native_budget.require()
                    context = context_builder(
                        token, code, refreshed, venue=venue, session=session,
                        limit=40, model_bar_limit=20, now_ts=now(), recent_candles=candles,
                        source_meta=dict(candle_meta, multi_timeframe_auxiliary_fetch=False),
                        include_investor_source=False,
                    )
                    native_budget.require()
                if not isinstance(context, dict):
                    raise ValueError("quote_recovery_candle_context_missing")
                ws_data = refreshed
                observation_context = observer_quote_context(pending)
                result["quote_recovery_retry_attempt_count"] = 1
            if calculation_index and machine.get("machine_evaluation_status") == "assessed":
                result["quote_recovery_recalculation_count"] = 1
        except Exception as exc:
            result["result"] = "policy_unavailable"
            result["reason"] = "machine_exception:" + type(exc).__name__
            return result
        action = str(machine.get("entry_mechanistic_action") or "").upper()
        # Preserve the producer's exact receipt even when preflight prevented
        # assessment. These fields never admit a candidate or change retries.
        for field in ("evaluation_attempt_id", "native_observation", "machine_evaluation_status",
                      "machine_capture_status", "machine_observation_sha256",
                      "machine_bundle_sha256"):
            if machine.get(field) is not None:
                result[field] = machine[field]
        # Keep the engine's measured input boundary on rejected assessments too.
        # Missing timings stay absent; this projection cannot admit or retry.
        machine_input_trace = {
            field: deepcopy(machine[field]) for field in (
                "entry_machine_input_as_of", "entry_machine_input_preparation_ms",
                "entry_machine_input_preparation_stages_ms",
                "entry_machine_input_feature_build_ms", "entry_local_stage_timings_ms",
                "response_ms",
            ) if machine.get(field) is not None
        }
        if machine_input_trace:
            result["machine_input_trace"] = machine_input_trace
        if machine.get("ai_input_runtime_preflight_artifact_status") is not None:
            result["machine_preflight_artifact_status"] = machine[
                "ai_input_runtime_preflight_artifact_status"]
        if machine.get("machine_evaluation_status") != "assessed":
            contract_error = machine.get("machine_contract_error")
            if contract_error:
                result["machine_contract_error"] = str(contract_error)[:160]
            for field in ("machine_feature_source_receipt", "machine_feature_tick_window",
                          "machine_source_gap_kind"):
                if field in machine:
                    result[field] = machine[field]
            if not result.get("machine_source_gap_kind"):
                status = machine.get("machine_evaluation_status")
                primary = (machine.get("entry_source_invalid_primary_blocker")
                           if status == "source_quality_blocked_before_assessment" else None)
                if status == "required_feature_blocked_before_assessment":
                    blockers = machine.get("entry_required_feature_blockers")
                    if isinstance(blockers, list) and blockers:
                        primary = blockers[0]
                if isinstance(primary, str) and primary.strip():
                    result["machine_source_gap_kind"] = primary.strip()
            result["result"] = (
                "required_feature_insufficient"
                if machine.get("ai_result_source") == "input_preflight_blocked"
                or contract_error == "strategy_tape_score_source_missing"
                else "policy_unavailable"
            )
            result["reason"] = str(machine.get("machine_evaluation_status") or "machine_not_assessed")
        elif action == "SOURCE_INVALID":
            result["reason"] = "machine_source_invalid"
            result["machine_action"] = action
            result["machine_capture_status"] = machine.get("machine_capture_status")
            result["machine_observation_sha256"] = machine.get("machine_observation_sha256")
            result["machine_observation_id"] = machine.get("machine_observation_sha256")
        elif action in {"ENTER_NOW", "RECHECK", "BLOCK"}:
            result["result"] = "assessed"
            result["reason"] = str((machine.get("mechanistic_entry_assessment") or {}).get("reason") or "machine_assessed")
            result["machine_action"] = action
            result["machine_bundle_sha256"] = machine.get("machine_bundle_sha256")
            result["machine_capture_status"] = machine.get("machine_capture_status")
            result["machine_observation_sha256"] = machine.get("machine_observation_sha256")
            result["machine_observation_id"] = machine.get("machine_observation_sha256")
            result["probe_price"] = ws_data["curr"]
            result["probe_trade_epoch"] = ws_data["zero_base_probe_trade_epoch"]
            result["probe_depth_epoch"] = ws_data["zero_base_probe_depth_epoch"]
        else:
            result["result"] = "policy_unavailable"
            result["reason"] = "machine_action_unknown"
    finally:
        # Reuse the last exact read with its original clocks. Only failures
        # before that boundary need a terminal memory read. Never skip cleanup.
        try:
            source_trace = getattr(ws_manager, 'exact_probe_source_trace', None)
            if callable(source_trace):
                result['ws_source_trace'] = source_trace(item, lease_id)
        except Exception as exc:
            result['source_trace_error'] = type(exc).__name__
        try:
            result['ws_observation_terminal'] = result.get('ws_observation_pre_machine') or probe_ws_observation(
                    probe_ws_snapshot(ws_manager, code=code, route=route), code=code,
                    route=route, after_epoch=registered_epoch, now_epoch=now())
        except Exception as exc:
            result['source_diagnostic_error'] = type(exc).__name__
        if (lease_requested or not was_subscribed) and not deferred_release and (exact_lease or callable(release_ws)):
            if (retain_ws_on_recheck and result["result"] == "assessed"
                    and result["machine_action"] in {"RECHECK", "ENTER_NOW"}):
                result["_ws_lease_retained"] = True
            else:
                release()
    return result
