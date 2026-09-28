"""Exact-route, source-first probe before a zero-base candidate may be watched."""

from __future__ import annotations

import time
from concurrent.futures import TimeoutError as FutureTimeoutError

from src.engine.scalping.entry_candle_context import (
    build_entry_candle_context,
    fetch_entry_candles_with_meta,
    resolve_entry_candle_request_code,
    resolve_entry_candle_session,
)
from src.utils import kiwoom_utils
from src.utils.kiwoom_read_request_control import REQUEST_CLASS_SOURCE_ONLY


RESULT_SCHEMA = "zero_base_probe_result_v1"
_ROUTE_ITEM = {
    "krx_only": lambda code: code,
    "nxt_only": lambda code: code + "_NX",
    "krx_nxt_integrated": lambda code: code + "_AL",
}
_ROUTE_VENUE = {"krx_only": "KRX", "nxt_only": "NXT", "krx_nxt_integrated": "SOR"}


def probe_item(code: str, route: str) -> str:
    builder = _ROUTE_ITEM.get(route)
    return builder(code) if builder and len(code) == 6 and code.isdigit() else ""


def exact_probe_ws_data(
    snapshot: dict, *, code: str, route: str, after_epoch: float,
    now_epoch: float | None = None, max_age_sec: float = 2.0,
) -> tuple[dict, str]:
    """Reject stale or cross-route aggregate data before any machine call."""
    item = probe_item(code, route)
    if not item or not isinstance(snapshot, dict):
        return {}, "invalid_probe_identity"
    route_key = {
        "krx_only": "KRX|krx_only",
        "nxt_only": "_NX|nxt_only",
        "krx_nxt_integrated": "_AL|krx_nxt_integrated",
    }[route]
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
    result["curr"] = int(trade["current_price"])
    result["orderbook"] = orderbook
    result["effective_venue"] = _ROUTE_VENUE[route]
    result["market_data_route"] = route
    result["zero_base_probe_trade_epoch"] = trade["observed_epoch"]
    result["zero_base_probe_depth_epoch"] = depth["observed_epoch"]
    return result, "ready"


def exact_probe_rest_sources(ticks, candle_meta, *, request_code, now_epoch):
    """Keep REST feature rows on the requested venue and bounded receive clock."""
    if not isinstance(ticks, list) or not ticks or not isinstance(candle_meta, dict):
        return False
    if candle_meta.get("request_code") != request_code:
        return False
    candle_received = candle_meta.get("rest_received_ts_ms")
    if not isinstance(candle_received, int) or not 0 <= now_epoch - candle_received / 1000 <= 120:
        return False
    for tick in ticks:
        if not isinstance(tick, dict) or tick.get("request_code") != request_code:
            return False
        received = tick.get("rest_received_ts_ms")
        if not isinstance(received, int) or not 0 <= now_epoch - received / 1000 <= 10:
            return False
    return True


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
) -> dict:
    """Observe one candidate. The caller owns bounded WS REG/REMOVE leases."""
    claim = dict(request.get("claim") or {})
    candidate = dict(request.get("candidate") or {})
    code, route = claim.get("code"), claim.get("route")
    result = {
        "schema": RESULT_SCHEMA,
        "claim": claim,
        "candidate": candidate,
        "result": "source_unavailable",
        "reason": "unknown",
        "machine_action": "",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    item = probe_item(code or "", route or "")
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
    was_subscribed = code in getattr(ws_manager, "subscribed_codes", set())
    registered_epoch = now()
    deferred_release = False
    try:
        registration = ws_manager.execute_subscribe(
            [item], source="zero_base_probe", observation_only=True,
            required_realtime_types=("0B", "0D"), realtime_types=("0B", "0D"),
        )
        if not was_subscribed:
            if registration is None:
                result["reason"] = "ws_registration_not_dispatched"
                return result
            try:
                registration.result(timeout=3.0)
            except FutureTimeoutError:
                if callable(release_ws):
                    registration.add_done_callback(
                        lambda _future: release_ws(code, item)
                    )
                    deferred_release = True
                    result["_ws_cleanup_deferred"] = True
                result["reason"] = "ws_registration_timeout"
                return result
            except Exception as exc:
                result["reason"] = "ws_registration_failed:" + type(exc).__name__
                return result
        snapshot = ws_manager.wait_for_data(code, timeout=3.0, require_trade=True)
        ws_data, source_reason = exact_probe_ws_data(
            snapshot, code=code, route=route, after_epoch=registered_epoch,
            now_epoch=now(),
        )
        if not ws_data:
            result["reason"] = source_reason
            return result
        tick_fetcher = tick_fetcher or kiwoom_utils.get_tick_history_ka10003
        candle_fetcher = candle_fetcher or fetch_entry_candles_with_meta
        context_builder = context_builder or build_entry_candle_context
        venue = _ROUTE_VENUE[route]
        session = resolve_entry_candle_session()
        request_code = resolve_entry_candle_request_code(
            code, venue=venue, session=session, ws_data=ws_data,
        )
        try:
            ticks = tick_fetcher(
                token, request_code, limit=10,
                request_owner="zero_base_machine_probe",
                request_class=REQUEST_CLASS_SOURCE_ONLY,
                explicit_request_code=True,
            )
            candles, candle_meta = candle_fetcher(
                token, code, ws_data, venue=venue, session=session, limit=40,
                now_ts=now(), allow_integrated_sor_execution_view=True,
                request_owner="zero_base_machine_probe",
                request_class=REQUEST_CLASS_SOURCE_ONLY,
            )
        except Exception as exc:
            result["reason"] = "required_rest_source_failed:" + type(exc).__name__
            return result
        if not ticks or not candles:
            result["result"] = "required_feature_insufficient"
            result["reason"] = "tick_or_candle_missing"
            return result
        if not exact_probe_rest_sources(
            ticks, candle_meta, request_code=request_code, now_epoch=now(),
        ):
            result["reason"] = "rest_route_or_receive_clock_invalid"
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
        refreshed_snapshot = ws_manager.get_latest_data(code)
        ws_data, source_reason = exact_probe_ws_data(
            refreshed_snapshot, code=code, route=route,
            after_epoch=registered_epoch, now_epoch=now(),
        )
        if not ws_data:
            result["reason"] = "pre_machine_" + source_reason
            return result
        try:
            machine = ai_engine.analyze_target(
                candidate.get("name") or code, ws_data, ticks, candles,
                strategy="SCALPING", prompt_profile="watching", machine_only=True,
                metadata_extra={
                    "position_tag": "SCANNER",
                    "source_event_stage": "zero_base_probe_machine_only_v1",
                    "zero_base_source_sha256": claim.get("source_sha256"),
                    "zero_base_route": route,
                },
                candle_context=context,
            ) or {}
        except Exception as exc:
            result["result"] = "policy_unavailable"
            result["reason"] = "machine_exception:" + type(exc).__name__
            return result
        action = str(machine.get("entry_mechanistic_action") or "").upper()
        if machine.get("machine_evaluation_status") != "assessed":
            result["result"] = (
                "required_feature_insufficient"
                if machine.get("ai_result_source") == "input_preflight_blocked"
                else "policy_unavailable"
            )
            result["reason"] = str(machine.get("machine_evaluation_status") or "machine_not_assessed")
        elif action == "SOURCE_INVALID":
            result["reason"] = "machine_source_invalid"
        elif action in {"ENTER_NOW", "RECHECK", "BLOCK"}:
            result["result"] = "assessed"
            result["reason"] = str((machine.get("mechanistic_entry_assessment") or {}).get("reason") or "machine_assessed")
            result["machine_action"] = action
            result["machine_bundle_sha256"] = machine.get("machine_bundle_sha256")
            result["machine_observation_id"] = machine.get("machine_observation_id")
            result["probe_price"] = ws_data["curr"]
            result["probe_trade_epoch"] = ws_data["zero_base_probe_trade_epoch"]
            result["probe_depth_epoch"] = ws_data["zero_base_probe_depth_epoch"]
        else:
            result["result"] = "policy_unavailable"
            result["reason"] = "machine_action_unknown"
    finally:
        if not was_subscribed and not deferred_release and callable(release_ws):
            release_ws(code, item)
    return result
