"""Bounded cross-process WS transport comparison; never an order input selector."""

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

from src.utils.constants import DATA_DIR

SNAPSHOT_PATH = DATA_DIR / "runtime" / "kiwoom_ws_snapshot" / "latest.json"
CONTRACT = "widget_shared_ws_transport_comparison_v1"
KST = ZoneInfo("Asia/Seoul")
METRIC_CONTRACT = {
    "metric_role": "market_data_transport_quality",
    "decision_authority": "source_quality_only",
    "window_policy": "exact_consumer_route_session_matched_windows",
    "sample_floor": "three_consecutive_15_minute_windows_for_each_rollout_cohort",
    "primary_decision_metric": "consumer_valid_market_data_ratio",
    "source_quality_gate": "exact_route_original_timestamps_epoch_required_fields",
    "forbidden_uses": ["order_authority", "threshold_relaxation", "profit_claim", "retired_strategy_activation"],
}


def process_generation(pid):
    if type(pid) is not int or pid <= 0:
        raise ValueError("producer_pid_invalid")
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    if fields[0] in {"Z", "X", "x"}:
        raise ValueError("producer_not_running")
    return {"pid": pid, "start_ticks": int(fields[19]),
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def producer_provenance():
    return {"schema": "shared_ws_transport_producer_v1", "process": process_generation(os.getpid()),
            "source_commit": os.getenv("KORSTOCKSCAN_RUNTIME_GIT_COMMIT", ""),
            "source_root": str(Path(__file__).resolve().parents[3])}


def read_shared_widget_quote(context, *, now_ts, path=None):
    """Read one atomic checkpoint, preserving each original field clock.

    P1 returns evidence only. Missing producer/epoch/route or partial/stale
    fields cannot silently select REST-looking WS data or start recovery I/O.
    """
    started = time.monotonic()
    result = {"schema": CONTRACT, "status": "source_gap", "mode": "compare_only",
              "selected_input": "existing_rest", "runtime_effect": False,
              "request_code": context.request_code, "session": context.name,
              "metric_contract": METRIC_CONTRACT, "comparison_status": "rest_not_observed"}
    try:
        path = Path(path or SNAPSHOT_PATH)
        now = datetime.fromtimestamp(now_ts, KST)
        if not context.active or not context.start <= now.time().replace(tzinfo=None) < context.end:
            raise ValueError("consumer_session_inactive")
        item = context.request_code
        if not re.fullmatch(r"[0-9]{6}(?:_AL|_NX)?", item):
            raise ValueError("request_item_invalid")
        route = "krx_nxt_integrated" if item.endswith("_AL") else "nxt_only" if item.endswith("_NX") else "krx_only"
        venue = "" if item.endswith("_AL") else "NXT" if item.endswith("_NX") else "KRX"
        with path.open("rb") as handle:
            raw = handle.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("snapshot_size_exceeded")
        snapshot = json.loads(raw)
        authority = snapshot["machine_confirmation_input_contract"]
        if (snapshot.get("schema_version") != "kiwoom_ws_dashboard_snapshot_v1"
                or snapshot.get("decision_authority") != "source_quality_only"
                or snapshot.get("runtime_effect") is not False
                or authority.get("schema") != "machine_entry_confirmation_ws_snapshot_v1"
                or authority.get("decision_authority") != "market_data_input_only_no_order_authority"
                or authority.get("runtime_effect") is not False
                or authority.get("actual_order_submitted") is not False
                or authority.get("exact_route_required") is not True
                or authority.get("causal_past_only") is not True
                or authority.get("broker_order_forbidden") is not True):
            raise ValueError("snapshot_authority_invalid")
        generated = float(snapshot["generated_at_epoch"])
        if not math.isfinite(generated) or not 0 <= now_ts - generated <= 20:
            raise ValueError("snapshot_stale_or_future")
        producer = snapshot["shared_transport_producer"]
        if (producer.get("schema") != "shared_ws_transport_producer_v1"
                or producer.get("connection_available") is not True
                or not re.fullmatch(r"[0-9a-f]{40}", producer.get("source_commit", ""))
                or producer.get("process") != process_generation(producer["process"]["pid"])):
            raise ValueError("producer_generation_invalid")
        result["producer"] = producer
        if item not in producer.get("registered_items", []):
            raise ValueError("item_not_registered")
        stock = snapshot["stocks"][item[:6]]
        matches = [r["realtime_types"] for r in stock["machine_confirmation_routes"].values()
                   if all(r.get("realtime_types", {}).get(t, {}).get("item") == item for t in ("0B", "0D"))]
        if len(matches) != 1:
            raise ValueError("exact_route_missing_or_duplicate")
        types = matches[0]
        epoch = producer["transport_epoch"]
        if (type(epoch) is not int or epoch <= 0
                or type(stock.get("market_data_transport_epoch")) is not int
                or stock["market_data_transport_epoch"] != epoch):
            raise ValueError("connection_epoch_conflict")
        for kind, row in types.items():
            if kind not in ("0B", "0D"):
                continue
            stamp = row["observed_epoch"]
            observed = datetime.fromtimestamp(stamp, KST)
            if (type(stamp) not in (int, float) or not math.isfinite(stamp)
                    or not 0 <= now_ts - stamp <= 20 or stamp > generated
                    or observed.date() != now.date()
                    or not context.start <= observed.time().replace(tzinfo=None) < context.end
                    or row.get("realtime_type") != kind or row.get("market_route") != route
                    or row.get("effective_venue") != venue
                    or type(row.get("transport_epoch")) is not int or row["transport_epoch"] != epoch
                    or type(row.get("route_sequence")) is not int or row["route_sequence"] <= 0):
                raise ValueError("field_clock_route_or_epoch_invalid:" + kind)
        book = types["0D"]["orderbook"]
        values = {"current_price": types["0B"]["trade_price"],
                  "best_bid": book["bids"][0]["price"], "best_ask": book["asks"][0]["price"],
                  "best_bid_qty": book["bids"][0]["volume"], "best_ask_qty": book["asks"][0]["volume"]}
        if any(type(v) is not int or v <= 0 for v in values.values()) or values["best_bid"] > values["best_ask"]:
            raise ValueError("partial_or_crossed_quote")
        result.update(status="valid_ws_comparison_input", values=values,
                      trade_date=now.date().isoformat(), market_data_route=route,
                      source_clocks={t: types[t]["observed_epoch"] for t in ("0B", "0D")},
                      source_sequences={t: types[t]["route_sequence"] for t in ("0B", "0D")},
                      provider_trade_clock={k: types["0B"].get(k) for k in
                          ("provider_trade_epoch", "provider_trade_time_precision_ms", "provider_trade_date_basis")},
                      source_sha256=hashlib.sha256(json.dumps(types, sort_keys=True).encode()).hexdigest(),
                      snapshot_sha256=hashlib.sha256(raw).hexdigest(), snapshot_generated_at=generated)
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError, AttributeError, RecursionError) as exc:
        result["reason"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__ + ":" + str(exc)
    result["reader_elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
    return result


def compare_widget_rest(transport, *, current_price, bbo, quote_received_at, bbo_received_at):
    """Same-field diagnostics, with no freshening or automatic source promotion."""
    if transport.get("status") != "valid_ws_comparison_input":
        return
    clocks = {"0B": quote_received_at.timestamp(), "0D": bbo_received_at.timestamp()}
    deltas = {t: clocks[t] - transport["source_clocks"][t] for t in clocks}
    transport["rest_source_clocks"] = clocks
    transport["clock_deltas_sec"] = deltas
    if any(not 0 <= delta <= 20 for delta in deltas.values()):
        transport["comparison_status"] = "not_comparable_clock_gap"
        return
    rest = {"current_price": current_price, **{k: bbo.get(k) for k in
            ("best_bid", "best_ask", "best_bid_qty", "best_ask_qty")}}
    transport["rest_values"] = rest
    transport["different_fields"] = [k for k, v in transport["values"].items() if rest.get(k) != v]
    transport["comparison_status"] = "different_observations" if transport["different_fields"] else "matched_fields"
    transport["same_observation_proven"] = False  # REST supplies no common exchange sequence.


def attach_transport_census(owner, payload):
    """Bounded per-process comparison denominator, including failed REST cycles."""
    transport = getattr(owner, "_transport_comparison", None)
    if not transport:
        return
    now = datetime.fromisoformat(payload["observed_at_kst"])
    key = (now.date().isoformat(), transport["request_code"], transport["session"])
    if getattr(owner, "_transport_census_key", None) != key:
        owner._transport_census_key, owner._transport_census = key, {}
    window = int(now.timestamp()) // 900 * 900
    producer = transport.get("producer") or {}
    # Keep failures in the denominator, but never attest a mixed/unknown
    # producer window using only the latest snapshot's provenance.
    generation = {
        "process": dict(producer.get("process") or {}),
        "source_commit": producer.get("source_commit"),
        "transport_epoch": producer.get("transport_epoch"),
    } if producer else None
    bucket = owner._transport_census.setdefault(window, {
        "expected_comparisons": 0, "valid_ws": 0, "ws_source_gap": 0,
        "rest_not_observed": 0, "matched_fields": 0, "different_observations": 0,
        "not_comparable_clock_gap": 0,
        "producer_generation": generation, "producer_generation_mixed": False,
        "producer_generation_missing": generation is None,
        "first_observed_at": now.isoformat(),
    })
    if bucket["producer_generation"] != generation:
        bucket["producer_generation_mixed"] = True
    if generation is None:
        bucket["producer_generation_missing"] = True
    bucket["last_observed_at"] = now.isoformat()
    bucket["expected_comparisons"] += 1
    bucket["valid_ws" if transport["status"] == "valid_ws_comparison_input" else "ws_source_gap"] += 1
    bucket[transport["comparison_status"]] += 1
    while len(owner._transport_census) > 4:
        owner._transport_census.pop(min(owner._transport_census))
    try:
        consumer_process = process_generation(os.getpid())
    except (OSError, ValueError, IndexError):
        consumer_process = {"status": "process_provenance_unavailable"}
    transport["census"] = {"scope": "process_local_comparison_not_adopted_input",
        "schema": "widget_transport_census_generation_bound_v2",
        "consumer_process": consumer_process,
        "windows": {str(k): dict(v) for k, v in owner._transport_census.items()}}
    payload["market_data_transport"] = transport
