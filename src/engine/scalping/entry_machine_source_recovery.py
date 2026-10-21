"""Main entry source recovery; no provider, subscription or order authority.

Owned by scalping because this selects already received Main entry inputs and
schedules a fresh machine calculation. It does not change admission policy.
"""

from copy import deepcopy
from collections import OrderedDict
import hashlib
import json
import math
import re
import threading
import time


STATE_KEY = "entry_machine_source_recovery"
_STATUSES = {
    "source_quality_blocked_before_assessment",
    "required_feature_blocked_before_assessment",
}
QUOTE_SCHEMA = "entry_source_quote_recovery_v2"
_QUOTE_BLOCKERS = frozenset({
    "bbo_missing", "bbo_stale", "bbo_invalid",
    "0d_missing", "0d_stale_or_missing_timestamp",
    "0d_executable_bbo_missing_or_invalid", "valid_bbo_missing",
})
_PENDING_TARGETS = OrderedDict()
_PENDING_LOCK = threading.Lock()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _lease(ws, item, epoch):
    receipt = ws.get("source_recovery_lease")
    if (not isinstance(receipt, dict) or receipt.get("schema") != "entry_source_lease_v1"
            or receipt.get("item") != item or type(epoch) is not int or epoch <= 0
            or type(receipt.get("transport_epoch")) is not int
            or receipt["transport_epoch"] != epoch
            or receipt.get("registration_epoch") != epoch
            or not {"0B", "0D"}.issubset(receipt.get("realtime_types") or ())
            or _number(receipt.get("registration_sent_at_epoch")) is None
            or receipt["registration_sent_at_epoch"] <= 0
            or receipt.get("physical_probe_lease_removing") is True
            or receipt.get("physical_probe_lease_id") is not None
               and receipt.get("physical_probe_lease_epoch") != epoch):
        return None
    return deepcopy(receipt)


def capture_quote_failure(preflight, ws, claim, *, deadline_perf=None, observation=None):
    """Copy exact source custody on an unevaluated quote-only preflight.

    The private result is used only for bounded scheduling. It is never an AI
    input, a native event rewrite, a cached verdict or a provider authority.
    """
    blockers = preflight.get("blockers") or []
    if (not isinstance(blockers, list) or not blockers
            or not all(isinstance(b, str) and b in _QUOTE_BLOCKERS for b in blockers)
            or preflight.get("feature_blockers")
            or not isinstance(claim, dict) and not isinstance(observation, dict)):
        return {}
    try:
        if not isinstance(claim, dict):
            validated_observer_snapshot(observation, now=time.time())
        event = (claim if isinstance(claim, dict) else observation)["snapshot"][0]
        epoch, item = event["native_epoch"], event["source_item"]
        lease = _lease(ws, item, epoch)
        if lease is None:
            return {}
        if lease["registration_sent_at_epoch"] > time.time():
            return {}
        from src.trading.market.session_contract import market_source_partition_venue
        if event["venue"] != market_source_partition_venue(item):
            return {}
        route = {"SOR": "krx_nxt_integrated", "NXT": "nxt_only", "KRX": "krx_only"}.get(event["venue"])
        suffix = item[len(event["symbol"]):]
        key = f"{suffix or 'KRX'}|{route}"
        rows = (ws.get("realtime_type_snapshots_by_route") or {}).get(key) or {}
        tape, quote = rows.get("0B"), rows.get("0D")
        if (not isinstance(tape, dict) or quote is not None and not isinstance(quote, dict)
                or any(row.get("item") != item or row.get("market_route") != route
                       or type(row.get("transport_epoch")) is not int or row["transport_epoch"] != epoch
                       or type(row.get("route_sequence")) is not int or row["route_sequence"] <= 0
                       for row in (tape, quote) if isinstance(row, dict))):
            return {}
        if _number(deadline_perf) is None:
            deadline_perf = time.perf_counter() + max(0., event["epoch"] + 5 - time.time())
        return {"_entry_source_recovery": dict(
            schema=QUOTE_SCHEMA, claim=deepcopy(claim) if isinstance(claim, dict) else None,
            observer=deepcopy(observation) if not isinstance(claim, dict) else None, lease=lease,
            rows={kind: deepcopy(rows[kind]) for kind in ("0B", "0D") if kind in rows},
            blockers=deepcopy(blockers), deadline_perf=deadline_perf,
            failed_at=time.time())}
    except (KeyError, TypeError, IndexError, ValueError):
        return {}


def register_pending_target(stock, pending):
    """Keep bounded same-process references only while a quote retry is live."""
    with _PENDING_LOCK:
        _PENDING_TARGETS.pop(id(stock), None)
        if isinstance(pending, dict) and pending.get("schema") == QUOTE_SCHEMA:
            _PENDING_TARGETS[id(stock)] = (stock, pending, False)
            while len(_PENDING_TARGETS) > 128:
                _PENDING_TARGETS.popitem(last=False)


def notify_pending_quote(code, item, ws_snapshot, *, now):
    """Wake an exact WATCHING target once, without native-ready statistics."""
    wake = []
    with _PENDING_LOCK:
        for identity, (stock, pending, notified) in tuple(_PENDING_TARGETS.items()):
            if (stock.get(STATE_KEY) is not pending or _number(pending.get("expires_at")) is None
                    or now >= pending["expires_at"] or pending.get("scope") != _scope(stock)
                    or stock.get("status") != "WATCHING" or (_number(stock.get("buy_qty")) or 0) > 0):
                _PENDING_TARGETS.pop(identity, None)
                continue
            if notified or pending.get("stock_code") != code or pending.get("item") != item:
                continue
            ready = recovery_refresh(stock, ws_snapshot, now=now)
            if ready and ready.get("allowed") and ready.get("quote_only"):
                _PENDING_TARGETS[identity] = (stock, pending, True)
                wake.append((code, pending["native_claim"]["snapshot"][0]["epoch"]))
    if wake:
        from src.engine.monitoring.runtime_performance import notify_source_recovery_target
        return any(notify_source_recovery_target(symbol, original_epoch=epoch, now=now)
                   for symbol, epoch in wake)
    return False


def trace_fields(stock):
    pending = stock.get(STATE_KEY)
    if not isinstance(pending, dict):
        return {}
    return {
        "machine_source_recovery_parent_sha256": pending.get("parent_observation_sha256"),
        "machine_source_recovery_parent_attempt_id": pending.get("parent_attempt_id"),
    }


def _number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def select_prepared_route(code, ws, context):
    """Project route rows before validating aggregate price; never invent rows."""
    # Inventory readers hash this module without initializing live collectors.
    from src.engine.scalping.ai_market_snapshot import route_partitioned_ws_view
    view, partition = route_partitioned_ws_view(ws, context)
    if not partition.get("used"):
        return ws
    suffix, route = partition["selected_key"].split("|", 1)
    item = str(code) + ("" if suffix == "KRX" else suffix)
    epoch = ws.get("market_data_transport_epoch")
    rows = ws["realtime_type_snapshots_by_route"][partition["selected_key"]]
    if type(epoch) is not int or epoch <= 0 or any(
        type(row.get("transport_epoch")) is not int
        or row["transport_epoch"] != epoch
        for row in (rows["0B"], rows["0D"])
    ):
        raise ValueError("prepared_entry_route_partition_epoch_invalid")
    if any(row.get("item") != item or row.get("market_route") != route
           for row in (rows["0B"], rows["0D"])):
        raise ValueError("prepared_entry_route_partition_identity_invalid")
    return view


def _scope(stock):
    # Preserve watch ownership, generation, venue and session. A new promotion
    # must not inherit an earlier failed attempt's recovery lease.
    return [str(stock.get(key) or "") for key in (
        "code", "id", "scanner_promotion_id", "scanner_generation_id",
        "watch_generation_id", "effective_venue", "venue", "market_session_bucket",
        "session_bucket", "position_tag", "pos_tag",
    )]


def pending_after_failure(stock, decision, *, now, cooldown_sec, stock_code=None):
    """Return a bounded lease only for a captured, unevaluated machine input."""
    if (decision.get("provider_called") is not False
            or decision.get("machine_evaluation_expected") is not True
            or decision.get("machine_evaluation_status") not in _STATUSES
            or decision.get("machine_capture_status") != "captured"
            or not (decision.get("machine_source_invalid_receipt") is True
                    or decision.get("machine_required_feature_receipt") is True)):
        return None
    observation = str(decision.get("machine_observation_sha256") or "")
    bundle = str(decision.get("machine_bundle_sha256") or "")
    attempt = str(decision.get("evaluation_attempt_id") or "")
    if not (re.fullmatch(r"[0-9a-f]{64}", observation)
            and re.fullmatch(r"[0-9a-f]{64}", bundle) and attempt):
        return None
    now = _number(now)
    cooldown = _number(cooldown_sec)
    if now is None or cooldown is None or cooldown <= 0:
        return None
    provenance = decision.get("ai_input_preflight_realtime_type_provenance") or {}
    if not isinstance(provenance, dict):
        return None
    tape, quote = provenance.get("0B"), provenance.get("0D")
    captured = decision.get("_entry_source_recovery")
    quote_only_capture = isinstance(captured, dict) and captured.get("schema") == QUOTE_SCHEMA
    if quote_only_capture:
        tape = (captured.get("rows") or {}).get("0B")
        quote = (captured.get("rows") or {}).get("0D")
        if quote is None:
            # Missing 0D carries no invented sequence, timestamp or quote.
            # Its item/route scope comes only from the unchanged native root.
            quote = {key: tape.get(key) for key in ("item", "market_route", "market_suffix")} if isinstance(tape, dict) else None
    if not isinstance(tape, dict) or not isinstance(quote, dict):
        return None
    item, route = tape.get("item"), tape.get("market_route")
    if not item or not route or quote.get("item") != item or quote.get("market_route") != route:
        return None
    suffix = str(tape.get("market_suffix") or "").upper()
    if str(quote.get("market_suffix") or "").upper() != suffix:
        return None
    code = str(stock_code or stock.get("code") or stock.get("stock_code") or "")
    if not re.fullmatch(r"[0-9]{6}", code) or item != code + suffix:
        return None
    scope = _scope(stock)
    previous = stock.get(STATE_KEY) or {}
    until = now + cooldown
    retry_count = 0
    if (isinstance(previous, dict) and previous.get("scope") == scope
            and _number(previous.get("expires_at")) is not None
            and now < previous["expires_at"]):
        until = previous["expires_at"]
        retry_count = 1
    pending = {
        "schema": "entry_machine_source_recovery_v1", "scope": scope,
        "stock_code": code,
        "parent_attempt_id": attempt, "parent_observation_sha256": observation,
        "machine_bundle_sha256": bundle, "failed_at": now, "expires_at": until,
        "retry_count": retry_count,
        "selected_key": f"{suffix or 'KRX'}|{route}", "item": item,
        "tape_observed_at": _number(tape.get("observed_epoch")),
        "source_timing": deepcopy(decision.get("ai_input_preflight_source_timing") or {}),
    }
    if isinstance(captured, dict) and captured.get("schema") == QUOTE_SCHEMA:
        try:
            claim = captured["claim"]
            event = claim["snapshot"][0]
            original_deadline = _number(event["epoch"]) + 5
            perf_deadline = _number(captured.get("deadline_perf"))
            failure_at = _number(captured.get("failed_at"))
            if (now >= original_deadline or perf_deadline is None or time.perf_counter() >= perf_deadline
                    or failure_at is None or not event["epoch"] <= failure_at <= now
                    or event["source_item"] != item or event["symbol"] != code
                    or not event.get("signal_id") or not claim.get("token")
                    or not captured.get("blockers") or any(b not in _QUOTE_BLOCKERS for b in captured["blockers"])):
                return pending
            epoch = event["native_epoch"]
            if type(epoch) is not int or epoch <= 0:
                return pending
            rows = captured["rows"]
            if not isinstance(rows.get("0B"), dict):
                return pending
            pending.update(schema=QUOTE_SCHEMA, native_claim=deepcopy(claim),
                native_snapshot_sha256=_digest(claim["snapshot"]), transport_epoch=epoch,
                lease=deepcopy(captured["lease"]), original_deadline_epoch=original_deadline,
                deadline_perf=perf_deadline, source_rows=deepcopy(rows),
                quote_sequence=(rows.get("0D") or {}).get("route_sequence", 0),
                tape_sequence=rows["0B"]["route_sequence"],
                failed_at=failure_at,
                expires_at=min(until, original_deadline), blockers=deepcopy(captured["blockers"]))
            # The same signal cannot obtain a second quote retry by returning
            # another source rejection. Preserve its original parent and clock.
            if (isinstance(previous, dict) and previous.get("schema") == QUOTE_SCHEMA
                    and previous.get("native_claim", {}).get("token") == claim["token"]):
                pending.update(retry_count=1, expires_at=previous["expires_at"],
                    parent_attempt_id=previous["parent_attempt_id"],
                    parent_observation_sha256=previous["parent_observation_sha256"],
                    failed_at=previous["failed_at"])
        except (KeyError, TypeError, ValueError, IndexError):
            return pending
    return pending


def _quote_refresh(pending, ws, *, now):
    result = dict(allowed=False, reason="machine_source_wait_exact_quote", quote_only=True,
        suppress_normal_refresh=True, signature={},
        parent_observation_sha256=pending.get("parent_observation_sha256"),
        parent_attempt_id=pending.get("parent_attempt_id"))
    try:
        if (now >= pending["original_deadline_epoch"] or time.perf_counter() >= pending["deadline_perf"]
                or _digest((pending.get("native_claim") or pending.get("native_observation"))["snapshot"])
                    != pending["native_snapshot_sha256"]):
            return {**result, "reason": "machine_source_recovery_expired", "clear": True}
        if pending.get("retry_count") != 0:
            return {**result, "reason": "machine_source_recovery_retry_spent"}
        epoch = pending["transport_epoch"]
        if (type(ws.get("market_data_transport_epoch")) is not int
                or ws["market_data_transport_epoch"] != epoch
                or _lease(ws, pending["item"], epoch) != pending["lease"]):
            return result
        rows = (ws.get("realtime_type_snapshots_by_route") or {}).get(pending["selected_key"]) or {}
        route = pending["selected_key"].split("|", 1)[1]
        timing = pending["source_timing"]
        limits = [_number(timing[name]["freshness_limit_ms"]) for name in ("current_price", "bbo", "tape")]
        if any(limit is None or limit <= 0 for limit in limits):
            return result
        for kind in ("0B", "0D"):
            row = rows[kind]
            observed = _number(row.get("observed_epoch"))
            if (row.get("item") != pending["item"] or row.get("market_route") != route
                    or type(row.get("transport_epoch")) is not int or row["transport_epoch"] != epoch
                    or type(row.get("route_sequence")) is not int or row["route_sequence"] <= 0
                    or observed is None or not 0 <= (now - observed) * 1000 <= min(limits)):
                return result
        # A newer trade belongs to the existing 0B recovery path. This lane
        # must retain the very same valid trade/feature source as the failure.
        if (rows["0B"]["route_sequence"] != pending["tape_sequence"]
                or rows["0B"] != pending["source_rows"]["0B"]):
            return result
        quote = rows["0D"]
        latency = quote.get("market_source_latency") or {}
        packet = _number(latency.get("packet_received_epoch"))
        if (quote["route_sequence"] <= pending["quote_sequence"] or packet is None
                or not pending["failed_at"] < packet <= quote["observed_epoch"] <= now
                or latency.get("schema") != "market_source_latency_v1"
                or latency.get("item") != pending["item"]
                or type(latency.get("transport_epoch")) is not int or latency["transport_epoch"] != epoch
                or latency.get("route_sequence") != quote["route_sequence"]):
            return result
        provider = _number(rows["0B"].get("provider_trade_epoch"))
        precision = _number(rows["0B"].get("provider_trade_time_precision_ms"))
        if (precision not in (None, 0, 1000) or provider is not None
                and (provider > now or (now - provider) * 1000 - (precision or 0) > min(limits))):
            return result
        book = quote["orderbook"]
        bid, ask = (_number(book[side][0]["price"]) for side in ("bids", "asks"))
        if bid is None or ask is None or not 0 < bid <= ask:
            return result
        if any(_number(book[side][0].get("volume", book[side][0].get("quantity"))) is None
               or _number(book[side][0].get("volume", book[side][0].get("quantity"))) <= 0
               for side in ("bids", "asks")):
            return result
        return {**result, "allowed": True, "suppress_normal_refresh": False,
            "reason": "machine_source_quote_fresh_retry", "source_observed_at": quote["observed_epoch"],
            "packet_received_epoch": packet, "quote_sequence": quote["route_sequence"],
            "decision_authority": "fresh_machine_calculation_only", "actual_order_submitted": False,
            "broker_order_forbidden": True}
    except (KeyError, TypeError, ValueError, IndexError):
        return result


def recovery_refresh(stock, ws, *, now):
    """New exact 0B + fresh 0D permits a new calculation, never a cached BUY."""
    pending = stock.get(STATE_KEY)
    if not isinstance(pending, dict):
        return None
    key = pending.get("selected_key")
    if (pending.get("schema") not in {"entry_machine_source_recovery_v1", QUOTE_SCHEMA}
            or not isinstance(key, str) or len(key.split("|")) != 2
            or not all(key.split("|")) or not isinstance(pending.get("item"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", str(pending.get("parent_observation_sha256") or ""))):
        return {"allowed": False, "reason": "machine_source_recovery_invalid", "clear": True}
    ws = ws if isinstance(ws, dict) else {}
    now = _number(now)
    until = _number(pending.get("expires_at"))
    if now is None or until is None or now >= until or pending.get("scope") != _scope(stock):
        return {"allowed": False, "reason": "machine_source_recovery_expired", "clear": True}
    if pending.get("schema") == QUOTE_SCHEMA:
        quote_result = _quote_refresh(pending, ws, now=now)
        if quote_result.get("allowed") or quote_result.get("clear") or pending.get("retry_count") != 0:
            return quote_result
        # Preserve the existing new-0B recovery path and its independent native
        # claim admission when a quote-only retry has not been used.
    result = {
        "allowed": False, "reason": "machine_source_wait_new_tape",
        "suppress_normal_refresh": True, "signature": {},
        "parent_observation_sha256": pending.get("parent_observation_sha256"),
        "parent_attempt_id": pending.get("parent_attempt_id"),
    }
    if pending.get("retry_count") != 0:
        result["reason"] = "machine_source_recovery_retry_spent"
        return result
    epoch = ws.get("market_data_transport_epoch")
    partitions = ws.get("realtime_type_snapshots_by_route")
    rows = partitions.get(pending["selected_key"]) if isinstance(partitions, dict) else None
    if type(epoch) is not int or epoch <= 0 or not isinstance(rows, dict):
        return result
    timing = pending.get("source_timing")
    if not isinstance(timing, dict):
        return result
    limits = [_number((timing.get(name) or {}).get("freshness_limit_ms"))
              for name in ("current_price", "bbo", "tape")
              if isinstance(timing.get(name), dict)]
    if len(limits) != 3 or any(v is None or v <= 0 for v in limits):
        return result
    route = pending["selected_key"].split("|", 1)[1]
    for kind in ("0B", "0D"):
        row = rows.get(kind)
        if not isinstance(row, dict):
            return result
        at = _number(row.get("observed_epoch"))
        if (row.get("item") != pending["item"] or row.get("market_route") != route
                or type(row.get("transport_epoch")) is not int
                or row["transport_epoch"] != epoch or at is None
                or not 0 <= (now - at) * 1000 <= min(limits)):
            return result
    tape_at = rows["0B"]["observed_epoch"]
    baseline = _number(pending.get("tape_observed_at"))
    failed_at = _number(pending.get("failed_at"))
    if failed_at is None or tape_at <= (baseline if baseline is not None else failed_at):
        return result
    provider_at = _number(rows["0B"].get("provider_trade_epoch"))
    precision = _number(rows["0B"].get("provider_trade_time_precision_ms"))
    if precision not in (None, 0, 1000):
        return result
    if provider_at is not None and (
        provider_at > now or (now - provider_at) * 1000 - (precision or 0) > min(limits)
    ):
        result["reason"] = "machine_source_wait_current_provider_tape"
        return result
    result.update(allowed=True, suppress_normal_refresh=False,
                  reason="machine_source_fresh_retry", source_observed_at=tape_at,
                  decision_authority="fresh_machine_calculation_only",
                  actual_order_submitted=False, broker_order_forbidden=True)
    return result


def quote_retry_claim(stock, refresh, *, now):
    """Consume one same-signal retry after native validation, with no new claim."""
    pending = stock.get(STATE_KEY) or {}
    if (pending.get("schema") != QUOTE_SCHEMA or pending.get("retry_count") != 0
            or refresh.get("quote_only") is not True or not refresh.get("allowed")):
        raise ValueError("machine_source_quote_retry_invalid")
    from src.engine.scalping.reversal_source_diagnostics import validate_claim_with_receipt
    from src.engine.scalping.reversal_current_backend import backend
    claim = deepcopy(pending["native_claim"])
    validate_claim_with_receipt(claim, backend()._GENERATION, now=now, live_clock=True)
    # The native snapshot is immutable. The versioned source proof lives beside
    # it, with the old ask and actual calculation ask represented independently.
    claim["entry_quote_recovery_parent"] = deepcopy(pending)
    pending["retry_count"] = 1
    register_pending_target(stock, None)
    return claim


def validated_observer_snapshot(observation, *, now, receipt_out=None,
                                evaluation_attempt_id=None, machine_bundle_sha256=None):
    """Read the existing native observer without a claim or ready counter."""
    from src.engine.scalping.reversal_source_diagnostics import observation_binding_valid, observe_snapshot
    if (not isinstance(observation, dict) or observation.get("schema") != "entry_source_quote_observer_v1"
            or not observation_binding_valid(observation, now=now)):
        raise ValueError("machine_source_quote_observer_expired_or_invalid")
    root = observation["snapshot"][0]
    current, selection = observe_snapshot(root["symbol"], root["venue"], root["market"], now=now,
        item=root["source_item"], family_sha256=observation["family_sha256"], live_clock=True,
        original_root=root)
    if (not current or any(current[0].get(key) != root.get(key) for key in
            ("event_id", "signal_id", "epoch", "native_epoch", "native_sequence", "source_item", "entry_ask"))
            or not set(current[0].get("branch_signals") or {}) <= set(root.get("branch_signals") or {})
            or any(signal != root["branch_signals"][bid] for bid, signal in (current[0].get("branch_signals") or {}).items())):
        # The rejection is also reached during the initial observer assessment.
        # Keep both native roots and the same-lock selection reason in the
        # existing rejected-source trace; a bare exception cannot distinguish
        # source loss from a valid FIRST/ready lifecycle transition.
        keys = ("symbol", "venue", "market", "event_id", "signal_id", "epoch",
                "native_epoch", "native_sequence", "source_item", "entry_ask", "branch_signals",
                "registry_generation", "confirmation_price")
        receipt = dict(schema="entry_source_quote_observer_rejection_v1", status="observed",
            failure_cause="machine_source_quote_observer_native_root_changed",
            evaluation_attempt_id=evaluation_attempt_id, machine_bundle_sha256=machine_bundle_sha256,
            process_pid=observation["observer_pid"], process_start_ticks=observation["observer_start_ticks"],
            family_sha256=observation["family_sha256"], observed_epoch=selection.get("observed_epoch"),
            original_deadline_epoch=observation["deadline_epoch"],
            original_root={key:deepcopy(root.get(key)) for key in keys},
            current_root={key:deepcopy(current[0].get(key)) for key in keys} if current else None,
            native_selection=deepcopy(selection), runtime_effect=False,
            allowed_runtime_apply=False, actual_order_submitted=False, broker_order_forbidden=True)
        receipt["sha256"] = _digest(receipt)
        error = ValueError("machine_source_quote_observer_native_root_changed")
        error.reversal_source_receipt = receipt
        raise error
    if receipt_out is not None:
        receipt_out.update(selection)
    return current


def probe_quote_retry_pending(decision, observation, ws, *, now):
    """One observer-only recalculation; no synthetic Main claim or token."""
    captured = decision.get("_entry_source_recovery")
    if (decision.get("provider_called") is not False
            or decision.get("machine_evaluation_expected") is not True
            or decision.get("machine_evaluation_status") not in _STATUSES
            or decision.get("machine_capture_status") != "captured"
            or not isinstance(captured, dict) or captured.get("schema") != QUOTE_SCHEMA
            or captured.get("observer") != observation
            or observation.get("recovery_parent") is not None
            or not re.fullmatch("[0-9a-f]{64}", str(decision.get("machine_observation_sha256") or ""))
            or not decision.get("evaluation_attempt_id")):
        return None
    try:
        validated_observer_snapshot(observation, now=now)
        event = observation["snapshot"][0]
        rows = captured["rows"]
        tape = rows["0B"]
        suffix = tape.get("market_suffix") or "KRX"
        return dict(schema=QUOTE_SCHEMA, stock_code=event["symbol"], item=event["source_item"],
            selected_key=f"{suffix}|{tape['market_route']}", native_observation=deepcopy(observation),
            native_snapshot_sha256=_digest(observation["snapshot"]),
            parent_attempt_id=decision["evaluation_attempt_id"],
            parent_observation_sha256=decision["machine_observation_sha256"],
            original_deadline_epoch=observation["deadline_epoch"], expires_at=observation["deadline_epoch"],
            deadline_perf=observation["deadline_perf"], transport_epoch=event["native_epoch"],
            failed_at=captured["failed_at"], source_rows=deepcopy(rows), lease=deepcopy(captured["lease"]),
            source_timing=deepcopy(decision.get("ai_input_preflight_source_timing") or {}),
            quote_sequence=(rows.get("0D") or {}).get("route_sequence", 0),
            tape_sequence=tape["route_sequence"], retry_count=0)
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def observer_quote_refresh(pending, ws, *, now):
    if not isinstance(pending, dict) or pending.get("schema") != QUOTE_SCHEMA:
        return {"allowed": False, "reason": "machine_source_quote_observer_pending_invalid"}
    try:
        validated_observer_snapshot(pending["native_observation"], now=now)
    except (KeyError, TypeError, ValueError, IndexError):
        return {"allowed": False, "clear": True, "reason": "machine_source_quote_observer_expired_or_changed"}
    return _quote_refresh(pending, ws if isinstance(ws, dict) else {}, now=now)


def observer_quote_context(pending):
    if pending.get("retry_count") != 0:
        raise ValueError("machine_source_quote_observer_retry_spent")
    context = deepcopy(pending["native_observation"])
    context["recovery_parent"] = deepcopy(pending)
    pending["retry_count"] = 1
    return context


def evaluation_quote_receipt(claim, ws, *, now, evaluation_attempt_id, observation=None):
    """Bind a fresh calculation quote to its unchanged native root snapshot."""
    owner = claim or observation or {}
    pending = owner.get("entry_quote_recovery_parent") or owner.get("recovery_parent")
    if pending is None:
        return None
    pending = deepcopy(pending)
    # The retry was consumed at scheduling; this is the one admitted worker.
    pending["retry_count"] = 0
    ready = _quote_refresh(pending, ws, now=now)
    if not ready.get("allowed") or not evaluation_attempt_id:
        raise ValueError("machine_source_quote_evaluation_source_changed_or_expired")
    root = owner["snapshot"][0]
    if _digest(owner["snapshot"]) != pending["native_snapshot_sha256"]:
        raise ValueError("machine_source_quote_native_root_changed")
    rows = ws["realtime_type_snapshots_by_route"][pending["selected_key"]]
    book = rows["0D"]["orderbook"]
    receipt = dict(schema=QUOTE_SCHEMA,
        evaluation_role="main_live" if claim else "probe_observation", parent_attempt_id=pending["parent_attempt_id"],
        parent_observation_sha256=pending["parent_observation_sha256"],
        evaluation_attempt_id=evaluation_attempt_id, native_snapshot_sha256=pending["native_snapshot_sha256"],
        native_signal_id=root["signal_id"], native_event_id=root["event_id"],
        native_root_event=deepcopy(root),
        native_epoch=root["epoch"], native_entry_ask=root["entry_ask"],
        original_deadline_epoch=pending["original_deadline_epoch"], failed_at=pending["failed_at"],
        source_item=pending["item"], selected_key=pending["selected_key"], transport_epoch=pending["transport_epoch"],
        source_lease=deepcopy(pending["lease"]), original_quote_sequence=pending["quote_sequence"],
        tape_sequence=pending["tape_sequence"], quote_sequence=ready["quote_sequence"],
        quote_packet_received_epoch=ready["packet_received_epoch"],
        quote_observed_epoch=ready["source_observed_at"], evaluated_at=now,
        calculation_best_bid=book["bids"][0]["price"], calculation_best_ask=book["asks"][0]["price"],
        native_snapshot_rewritten=False, provider_called_before_recovery=False,
        decision_authority="fresh_machine_calculation_only")
    receipt["sha256"] = _digest(receipt)
    return receipt


def _spread_matches(definition, signal, spread):
    """Recheck quote-dependent filters; existing native trade facts stay fixed."""
    from src.engine.scalping import reversal_extended_catalog as catalog
    filters = definition.get("filters") or {}
    result = True
    if "when" in filters:
        from src.engine.scalping.reversal_cumulative_catalog import condition
        features = dict(signal.get("branch_features") or {}, spread=spread)
        result = condition(features, filters) is not False
    for name, bound in filters.items():
        if not name.startswith("spread_"):
            continue
        op = name[len("spread_"):]
        match = (spread < bound if op == "max_exclusive" else spread <= bound if op == "max"
                 else spread > bound if op == "min_exclusive" else spread >= bound if op == "min" else None)
        if match is not True:
            result = False
    reference = definition.get("original_definition_ref")
    if isinstance(reference, dict) and reference.get("branch_id"):
        result = result and _spread_matches(catalog.definition(reference["branch_id"]), signal, spread)
    return result


def _branch_spread(signal, receipt):
    # Legacy reversal quotes use bid as denominator; registered typed path
    # quotes use the unchanged confirmation trade. Preserve each owner unit.
    denominator = (signal["confirmation_price"]
                   if signal.get("extended_definition_id")
                   or signal.get("decision_phase") not in {"FIRST_UPTICK", "CONFIRMED_UPTICK"}
                   else receipt["calculation_best_bid"])
    return 100 * (receipt["calculation_best_ask"] - receipt["calculation_best_bid"]) / denominator


def calculation_snapshot(snapshot, receipt):
    """Explicit filtered calculation view, retaining the immutable native root.

    Only existing confirmed branches can remain. Narrower spread never adds a
    signal; widened spread can invalidate an original branch before a provider.
    """
    if receipt is None:
        return snapshot
    from src.engine.scalping import reversal_extended_catalog as catalog
    event, source = deepcopy(snapshot)
    signals = event.get("branch_signals")
    if not isinstance(signals, dict):
        raise ValueError("machine_source_quote_legacy_calculation_contract_missing")
    spread = 100 * (receipt["calculation_best_ask"] - receipt["calculation_best_bid"]) / event["confirmation_price"]
    branch_spreads = {bid: _branch_spread(signal, receipt) for bid, signal in signals.items()}
    retained = [bid for bid, signal in signals.items() if _spread_matches(catalog.definition(bid), signal, branch_spreads[bid])]
    native_root = receipt["native_root_event"].get("branch_signals", signals)
    receipt.update(native_branch_ids=sorted(native_root), current_native_branch_ids=sorted(signals),
                   calculation_branch_ids=sorted(retained),
                   excluded_quote_branch_ids=sorted(set(signals) - set(retained)), calculation_spread_pct=spread,
                   calculation_branch_spreads=branch_spreads)
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    if not retained:
        raise ValueError("current_quote_invalidates_native_branches")
    event["branch_signals"] = {bid: signals[bid] for bid in retained}
    source["branch_inputs"] = {bid: source["branch_inputs"][bid] for bid in retained}
    return event, source


def validate_evaluation_quote_receipt(receipt, event, raw):
    """Offline consumer contract; original and calculation asks cannot alias."""
    if receipt is None:
        if raw.get("entry_source_quote_recovery") is not None:
            raise ValueError("machine_source_quote_evaluation_receipt_missing")
        return
    try:
        if (receipt.get("schema") != QUOTE_SCHEMA
                or receipt["sha256"] != _digest({k: v for k, v in receipt.items() if k != "sha256"})
                or receipt["evaluation_attempt_id"] != raw["evaluation_attempt_id"]
                or receipt["native_signal_id"] != event["signal_id"]
                or receipt["native_event_id"] != event["event_id"]
                or receipt["native_entry_ask"] != event["entry_ask"]
                or receipt["native_epoch"] != event["epoch"]
                or receipt["source_item"] != event["source_item"]
                or receipt["transport_epoch"] != event["native_epoch"]
                or not event["epoch"] < receipt["original_deadline_epoch"] <= event["epoch"] + 5
                or not event["epoch"] <= receipt["failed_at"] < receipt["quote_packet_received_epoch"]
                    <= receipt["quote_observed_epoch"] <= receipt["evaluated_at"] < receipt["original_deadline_epoch"]
                or type(receipt["quote_sequence"]) is not int
                or not receipt["original_quote_sequence"] < receipt["quote_sequence"]
                or receipt["native_snapshot_rewritten"] is not False
                or receipt["provider_called_before_recovery"] is not False
                or not 0 < receipt["calculation_best_bid"] <= receipt["calculation_best_ask"]
                or (raw.get("quote") or {}).get("best_bid") != receipt["calculation_best_bid"]
                or (raw.get("quote") or {}).get("best_ask") != receipt["calculation_best_ask"]
                or raw.get("entry_source_quote_recovery") != receipt):
            raise ValueError("machine_source_quote_evaluation_receipt_invalid")
        root_event = receipt.get("native_root_event")
        if not isinstance(root_event, dict) or any(root_event.get(key) != event.get(key) for key in
                ("event_id", "signal_id", "epoch", "native_epoch", "native_sequence", "entry_ask", "confirmation_price", "source_item")):
            raise ValueError("machine_source_quote_evaluation_root_identity_invalid")
        if receipt.get("calculation_branch_ids") is not None:
            from src.engine.scalping import reversal_extended_catalog as catalog
            root = receipt["native_root_event"]["branch_signals"]
            current = receipt["current_native_branch_ids"]
            spreads = {bid: _branch_spread(root[bid], receipt) for bid in current}
            eligible = sorted(bid for bid in current if _spread_matches(catalog.definition(bid), root[bid], spreads[bid]))
            if (sorted(root) != receipt["native_branch_ids"]
                    or sorted(event["branch_signals"]) != receipt["calculation_branch_ids"]
                    or any(event["branch_signals"][bid] != root[bid] for bid in event["branch_signals"])
                    or not set(receipt["current_native_branch_ids"]) <= set(root)
                    or receipt["calculation_branch_spreads"] != spreads
                    or receipt["calculation_branch_ids"] != eligible
                    or sorted(set(receipt["current_native_branch_ids"]) - set(event["branch_signals"])) != receipt["excluded_quote_branch_ids"]):
                raise ValueError("machine_source_quote_calculation_branch_binding_invalid")
    except (KeyError, TypeError, IndexError, OverflowError) as exc:
        raise ValueError("machine_source_quote_evaluation_receipt_invalid") from exc


def _calculation_request(root_request, receipt):
    """Recompute quote-dependent facts; native confirmation facts stay rooted.

    No new trade has arrived in this lane. Every trade-derived feature remains
    bound to the existing valid 0B prefix; only actual new 0D quote facts change.
    """
    request = deepcopy(root_request)
    inp = request["input"]
    ask, bid = receipt["calculation_best_ask"], receipt["calculation_best_bid"]
    setup = inp["entry_setup_evidence_v1"]
    trade = setup["facts"]["confirmation_price"]
    spread = 100 * (ask - bid) / trade
    from src.engine.scalping import continuous_reversal as policy
    target = ask * (1 + policy.TARGET) / (1 - policy.COST)
    stop = ask * (1 + policy.STOP) / (1 - policy.COST)

    def update_quote_fields(value):
        if isinstance(value, dict):
            if "entry_ask" in value:
                value["entry_ask"] = ask
            if "spread_pct" in value:
                value["spread_pct"] = spread
            if "target_price" in value and "soft_stop_price" in value:
                value.update(target_price=target, soft_stop_price=stop)
                if "ask_premium_to_trade_pct" in value:
                    value["ask_premium_to_trade_pct"] = 100 * (ask / trade - 1)
                if "target_gap_from_trade_pct" in value:
                    value["target_gap_from_trade_pct"] = 100 * (target / trade - 1)
            for key, child in value.items():
                # These are immutable native proofs, including original ask.
                if key not in {"observed_signal", "signal_proof", "observation_phase"}:
                    update_quote_fields(child)
        elif isinstance(value, list):
            for child in value:
                update_quote_fields(child)

    update_quote_fields(inp)
    roles = ("positive_facts", "context_facts", "contradicting_facts")
    for signal in inp.get("signals", []):
        signal["facts"]["spread_pct"] = receipt.get("calculation_branch_spreads", {}).get(signal["policy_id"], spread)
    spread_names = {"observed_spread", "observable_wide_spread"}
    removed = set()
    for role in roles:
        removed.update(fact["id"] for fact in setup.get(role, [])
                       if fact["id"].rsplit("/", 1)[-1] in spread_names)
        setup[role] = [fact for fact in setup.get(role, [])
                       if fact["id"].rsplit("/", 1)[-1] not in spread_names]
    setup["risk_fact_bindings"] = {code: [fid for fid in ids if fid not in removed]
        for code, ids in setup["risk_fact_bindings"].items() if any(fid not in removed for fid in ids)}
    sources = [(signal["ref"] + "/", signal.get("observed_signal") is not None,
                signal["facts"].get("spread_pct", spread)) for signal in inp.get("signals", [])]
    if not sources:
        typed = inp.get("observed_signal") is not None
        actual_spread = spread if typed else 100 * (ask - bid) / bid
        setup["facts"]["spread_pct"] = actual_spread
        sources = [("", typed, actual_spread)]
    for prefix, typed, value in sources:
        name, code, threshold = (("observed_spread", "ENTRY_SPREAD_CONCERN", 0)
                                 if typed else ("observable_wide_spread", "LIQUIDITY_FRAGILE", .3))
        if value > threshold:
            fid = prefix + name
            setup["contradicting_facts"].append(dict(id=fid, value=value, unit="percent"))
            setup["risk_fact_bindings"].setdefault(code, []).append(fid)
    inp["entry_source_quote_recovery"] = dict(schema=QUOTE_SCHEMA,
        native_entry_ask=receipt["native_entry_ask"], calculation_entry_ask=ask,
        calculation_best_bid=bid, quote_observed_epoch=receipt["quote_observed_epoch"],
        original_deadline_epoch=receipt["original_deadline_epoch"], source_receipt_sha256=receipt["sha256"])
    schema = request["response_schema"]
    if inp.get("schema") == "continuous_reversal_union_auxiliary_v3":
        from src.engine.scalping.reversal_extended_union import response_schema
    elif inp.get("schema") == "continuous_reversal_union_auxiliary_v2":
        from src.engine.scalping.reversal_operating_auxiliary import response_schema
    else:
        from src.engine.scalping.reversal_auxiliary_contract import response_schema as legacy_schema
        complete = "INSUFFICIENT" not in schema["properties"]["risk_verdict"].get("enum", [])
        response_schema = lambda value: legacy_schema(value, complete_source_only=complete)
    request["response_schema"] = response_schema(inp)
    if schema["properties"]["risk_codes"].get("minItems") == 1:
        request["response_schema"]["properties"]["risk_codes"]["minItems"] = 1
    return request


def _validate_native_quote_request(request, receipt):
    """Fields overwritten by repricing must already match the native proof."""
    try:
        root = receipt["native_root_event"]
        inp = request["input"]
        facts = inp["entry_setup_evidence_v1"]["facts"]
        if (facts.get("entry_ask") != root["entry_ask"]
                or facts.get("confirmation_price") != root["confirmation_price"]):
            raise ValueError("machine_source_quote_native_request_quote_invalid")
        if "common_context" in inp and any(inp["common_context"].get(key) != root[key]
                for key in ("epoch", "source_item", "native_epoch", "native_sequence", "entry_ask", "confirmation_price")):
            raise ValueError("machine_source_quote_native_request_quote_invalid")
        for projected in inp.get("signals", []):
            signal = root["branch_signals"][projected["policy_id"]]
            if any(projected["facts"].get(key) != signal.get(key)
                   for key in ("entry_ask", "confirmation_price", "spread_pct")):
                raise ValueError("machine_source_quote_native_request_quote_invalid")
        if not inp.get("signals") and facts.get("spread_pct") != root.get("spread_pct"):
            raise ValueError("machine_source_quote_native_request_quote_invalid")
        from src.engine.scalping import continuous_reversal as policy

        def validate_geometry(value, signal):
            if isinstance(value, dict):
                ask, trade = signal["entry_ask"], signal["confirmation_price"]
                expected = dict(target_price=ask * (1 + policy.TARGET) / (1 - policy.COST),
                    soft_stop_price=ask * (1 + policy.STOP) / (1 - policy.COST),
                    ask_premium_to_trade_pct=100 * (ask / trade - 1),
                    target_gap_from_trade_pct=100 * (ask * (1 + policy.TARGET) / (1 - policy.COST) / trade - 1))
                if any(key in value and value[key] != number for key, number in expected.items()):
                    raise ValueError("machine_source_quote_native_request_geometry_invalid")
                for key, child in value.items():
                    if key not in {"signals", "observed_signal", "signal_proof", "observation_phase"}:
                        validate_geometry(child, signal)
            elif isinstance(value, list):
                for child in value:
                    validate_geometry(child, signal)

        validate_geometry(inp, root)
        expected_spread = {}
        projections = [(p["ref"] + "/", p.get("observed_signal") is not None,
                        root["branch_signals"][p["policy_id"]]) for p in inp.get("signals", [])]
        if not projections:
            projections = [("", inp.get("observed_signal") is not None, root)]
        for prefix, typed, signal in projections:
            value = signal.get("spread_pct")
            name, code, threshold = (("observed_spread", "ENTRY_SPREAD_CONCERN", 0)
                                     if typed else ("observable_wide_spread", "LIQUIDITY_FRAGILE", .3))
            if value is not None and value > threshold:
                fact = (dict(id=prefix + name, value=value, unit="percent") if typed
                        else dict(id=prefix + name, value=value, source_feature="spread_pct",
                                  disposition="research_context_not_proven_invalidation"))
                expected_spread[prefix + name] = (fact, code)
        setup = inp["entry_setup_evidence_v1"]
        actual_spread = [(role, fact) for role in
            ("positive_facts", "context_facts", "contradicting_facts") for fact in setup.get(role, [])
            if fact["id"].rsplit("/", 1)[-1] in {"observed_spread", "observable_wide_spread"}]
        expected_facts = [("contradicting_facts", fact) for fact, _ in expected_spread.values()]
        if sorted(actual_spread, key=lambda pair: pair[1]["id"]) != sorted(expected_facts, key=lambda pair: pair[1]["id"]):
            raise ValueError("machine_source_quote_native_request_spread_facts_invalid")
        for fid, (_, owner) in expected_spread.items():
            if [code for code, ids in setup["risk_fact_bindings"].items() if fid in ids] != [owner]:
                raise ValueError("machine_source_quote_native_request_spread_binding_invalid")
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError("machine_source_quote_native_request_quote_invalid") from exc


def apply_quote_calculation(result, receipt, *, data_root=None):
    """Use current quote facts in this new calculation without changing roots."""
    if receipt is None or result[1] is None:
        return result
    assessment, inp, prompt, schema = result
    root_request = dict(input=inp, prompt=prompt, response_schema=schema)
    _validate_native_quote_request(root_request, receipt)
    request = _calculation_request(root_request, receipt)
    assessment = deepcopy(assessment)
    assessment["entry_source_quote_calculation"] = dict(schema=QUOTE_SCHEMA,
        root_request=deepcopy(root_request), source_receipt_sha256=receipt["sha256"],
        root_request_sha256=_digest(root_request),
        root_signal_set_hash=assessment.get("signal_set_hash"),
        calculation_request_sha256=_digest(request))
    if "signal_set_hash" in assessment:
        assessment["signal_set_hash"] = _digest(request["input"]["signals"])
    if assessment.get("auxiliary_wire_contract"):
        if data_root is None:
            raise ValueError("machine_source_quote_wire_owner_missing")
        from src.engine.scalping import reversal_auxiliary_registry as registry
        value = registry.load(data_root, assessment["auxiliary_registry_sha256"])
        envelope = registry.envelope(request["input"], value)
        assessment["auxiliary_wire_contract"] = envelope["contract"]
        assessment["auxiliary_wire_hashes"] = envelope["hashes"]
    return assessment, request["input"], request["prompt"], request["response_schema"]


def audit_quote_calculation(assessment, request):
    """Verify new quote facts, then return the original native comparison view."""
    proof = assessment.get("entry_source_quote_calculation")
    receipt = assessment.get("entry_source_quote_recovery")
    if receipt is None and proof is None:
        return assessment, request
    if (not isinstance(receipt, dict) or not isinstance(proof, dict) or proof.get("schema") != QUOTE_SCHEMA
            or proof.get("source_receipt_sha256") != receipt.get("sha256")
            or proof.get("root_request_sha256") != _digest(proof.get("root_request"))
            or proof.get("calculation_request_sha256") != _digest(request)
            or _calculation_request(proof["root_request"], receipt) != request):
        raise ValueError("machine_source_quote_calculation_request_invalid")
    _validate_native_quote_request(proof["root_request"], receipt)
    native = dict(assessment)
    if "signal_set_hash" in native:
        native["signal_set_hash"] = proof["root_signal_set_hash"]
    return native, deepcopy(proof["root_request"])


def quote_label_reference(raw, assessment):
    """The new evaluation labels its actual ask/time, never the native root ask."""
    receipt = raw.get("entry_source_quote_recovery")
    if receipt is None:
        return None
    if assessment.get("entry_source_quote_recovery") != receipt:
        raise ValueError("machine_source_quote_label_assessment_binding_invalid")
    validate_evaluation_quote_receipt(receipt, assessment.get("event"), raw)
    return dict(schema=QUOTE_SCHEMA, evaluation_attempt_id=receipt["evaluation_attempt_id"],
        reference_price_type="executable_ask", reference_price=receipt["calculation_best_ask"],
        decision_epoch=receipt["evaluated_at"], source_receipt_sha256=receipt["sha256"],
        native_signal_id=receipt["native_signal_id"], native_entry_ask=receipt["native_entry_ask"])
