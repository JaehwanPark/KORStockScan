"""Main entry source recovery; no provider, subscription or order authority.

Owned by scalping because this selects already received Main entry inputs and
schedules a fresh machine calculation. It does not change admission policy.
"""

from copy import deepcopy
import math
import re

from src.engine.scalping.ai_market_snapshot import route_partitioned_ws_view

STATE_KEY = "entry_machine_source_recovery"
_STATUSES = {
    "source_quality_blocked_before_assessment",
    "required_feature_blocked_before_assessment",
}


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
    return {
        "schema": "entry_machine_source_recovery_v1", "scope": scope,
        "stock_code": code,
        "parent_attempt_id": attempt, "parent_observation_sha256": observation,
        "machine_bundle_sha256": bundle, "failed_at": now, "expires_at": until,
        "retry_count": retry_count,
        "selected_key": f"{suffix or 'KRX'}|{route}", "item": item,
        "tape_observed_at": _number(tape.get("observed_epoch")),
        "source_timing": deepcopy(decision.get("ai_input_preflight_source_timing") or {}),
    }


def recovery_refresh(stock, ws, *, now):
    """New exact 0B + fresh 0D permits a new calculation, never a cached BUY."""
    pending = stock.get(STATE_KEY)
    if not isinstance(pending, dict):
        return None
    key = pending.get("selected_key")
    if (pending.get("schema") != "entry_machine_source_recovery_v1"
            or not isinstance(key, str) or len(key.split("|")) != 2
            or not all(key.split("|")) or not isinstance(pending.get("item"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", str(pending.get("parent_observation_sha256") or ""))):
        return {"allowed": False, "reason": "machine_source_recovery_invalid", "clear": True}
    ws = ws if isinstance(ws, dict) else {}
    now = _number(now)
    until = _number(pending.get("expires_at"))
    if now is None or until is None or now >= until or pending.get("scope") != _scope(stock):
        return {"allowed": False, "reason": "machine_source_recovery_expired", "clear": True}
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
