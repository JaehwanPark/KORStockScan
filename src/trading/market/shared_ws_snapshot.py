"""Bounded shared WS comparison and explicit collector market-input selection."""

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
CONTRACT = "widget_shared_ws_transport_comparison_v2"
KST = ZoneInfo("Asia/Seoul")
METRIC_CONTRACT = {
    "metric_role": "market_data_transport_quality",
    "decision_authority": "source_quality_only",
    "window_policy": "consumer_session_windows_with_explicit_ws_source_items",
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
        live_clock = now_ts is None
        if live_clock:
            now_ts = time.time()
        result["evaluated_at_epoch"] = now_ts
        now = datetime.fromtimestamp(now_ts, KST)
        if not context.active or not context.start <= now.time().replace(tzinfo=None) < context.end:
            raise ValueError("consumer_session_inactive")
        item = context.request_code
        if not re.fullmatch(r"[0-9]{6}(?:_AL|_NX)?", item):
            raise ValueError("request_item_invalid")
        with path.open("rb") as handle:
            raw = handle.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("snapshot_size_exceeded")
        snapshot = json.loads(raw)
        if live_clock:
            # A live multi-symbol cycle may start long before this atomic read.
            # Observe after I/O; never rewrite the producer or field clocks.
            now_ts = time.time()
            now = datetime.fromtimestamp(now_ts, KST)
            if not context.start <= now.time().replace(tzinfo=None) < context.end:
                raise ValueError("consumer_session_inactive")
        result["evaluated_at_epoch"] = now_ts
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
        registered = producer.get("registered_items")
        if (not isinstance(registered, list)
                or any(not isinstance(code, str) for code in registered)):
            raise ValueError("registration_items_invalid")
        # Widget transport validation accepts the same symbol's integrated
        # source. Preserve its actual route; never relabel it as KRX/NXT.
        # This reader is comparison-only, not an execution quote resolver.
        integrated_item = item[:6] + "_AL"
        if integrated_item in registered:
            item = integrated_item
        route = "krx_nxt_integrated" if item.endswith("_AL") else "nxt_only" if item.endswith("_NX") else "krx_only"
        venue = "" if item.endswith("_AL") else "NXT" if item.endswith("_NX") else "KRX"
        result.update(ws_request_code=item, market_data_route=route,
                      source_selection="integrated_symbol" if item.endswith("_AL") else "exact_request")
        if item not in registered:
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
            facts = result.setdefault("field_validation", {})
            numeric = type(stamp) in (int, float) and math.isfinite(stamp)
            facts[kind] = {
                "observed_epoch": stamp, "age_sec": now_ts - stamp if numeric else None,
                "source_epoch": row.get("transport_epoch"), "producer_epoch": epoch,
                "source_item": row.get("item"),
                "age_exceeded": numeric and now_ts - stamp > 20,
                "prior_or_conflicting_epoch": row.get("transport_epoch") != epoch,
                "field_after_publication": numeric and stamp > generated,
                "recovery_authority": "none_field_age_is_not_connection_failure",
            }
        for kind in ("0B", "0D"):
            row = types[kind]
            stamp = row["observed_epoch"]
            observed = datetime.fromtimestamp(stamp, KST)
            if (type(stamp) not in (int, float) or not math.isfinite(stamp)
                    or not 0 <= now_ts - stamp <= 20 or stamp > generated
                    or observed.date() != now.date()
                    or not context.start <= observed.time().replace(tzinfo=None) < context.end
                    or row.get("realtime_type") != kind or row.get("market_route") != route
                    or row.get("market_suffix") != item[6:]
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
        result["widget_quote_fields"] = types["0B"].get("widget_quote_fields", {})
        selected = next(r for r in stock["machine_confirmation_routes"].values()
                        if r.get("realtime_types", {}).get("0B", {}).get("item") == item)
        result["recent_trades"] = list(selected.get("recent_trades") or ())[:3]
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError, AttributeError, RecursionError) as exc:
        result["reason"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__ + ":" + str(exc)
    result["reader_elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
    return result


def validate_widget_ws_receipt(receipt, *, context, now_ts):
    """Recheck original field clocks after slow auxiliary/REST work."""
    if receipt.get("status") != "valid_ws_comparison_input":
        reason = str(receipt.get("reason") or "source_gap")
        if not re.fullmatch(r"[A-Za-z0-9_:-]+", reason):
            reason = "source_gap"
        raise ValueError("widget_ws_source_unavailable:" + reason)
    if (receipt.get("request_code") != context.request_code
            or receipt.get("session") != context.name
            or receipt["producer"]["process"] != process_generation(receipt["producer"]["process"]["pid"])):
        raise ValueError("widget_ws_receipt_binding_invalid")
    clocks = receipt["source_clocks"]
    if not isinstance(clocks, dict) or set(clocks) != {"0B", "0D"}:
        raise ValueError("widget_ws_source_clocks_incomplete")
    for stamp in clocks.values():
        if type(stamp) not in (int, float) or not math.isfinite(stamp) or not 0 <= now_ts - stamp <= 20:
            raise ValueError("widget_ws_source_stale_or_future")


def widget_market_data_source(context):
    """Explicit rollout membership; no automatic registration-based promotion."""
    mode = os.getenv("KORSTOCKSCAN_WIDGET_MARKET_DATA_SOURCE", "rest").strip().lower()
    if mode not in {"rest", "ws"}:
        raise RuntimeError("widget_market_data_source_invalid")
    members = os.getenv("KORSTOCKSCAN_WIDGET_WS_SYMBOLS")
    if mode == "ws" and members is not None:
        codes = [code.strip() for code in members.split(",")]
        if not codes or any(not re.fullmatch(r"[0-9]{6}", code) for code in codes) or len(set(codes)) != len(codes):
            raise RuntimeError("widget_ws_rollout_scope_invalid")
        if context.request_code[:6] not in codes:
            return "rest"
    return mode


def select_widget_ws_inputs(context, transport, *, now_ts, require_trade_veto=False,
                            require_day_low=True):
    """Existing collector input selector. No request, recovery or order authority."""
    mode = widget_market_data_source(context)
    if mode == "rest":
        return None
    if mode != "ws":
        raise RuntimeError("widget_market_data_source_invalid")
    try:
        validate_widget_ws_receipt(transport, context=context, now_ts=now_ts)
        values = transport["values"]
        quote = {"cur_prc": values["current_price"],
                 "source": "kiwoom_ws_0B", "source_item": transport["ws_request_code"]}
        fields = transport.get("widget_quote_fields") or {}
        if require_day_low:
            low_raw = fields["low_price"]
            if not isinstance(low_raw, str) or not re.fullmatch(r"[+-]?[0-9]+", low_raw.strip()):
                raise ValueError("widget_ws_low_price_missing_or_invalid")
            low = abs(int(low_raw))
            if not 0 < low <= values["current_price"]:
                raise ValueError("widget_ws_low_price_conflict")
            quote["low_pric"] = low
        trade_payload = {}
        if require_trade_veto:
            change_raw = fields["change_pct"]
            if not isinstance(change_raw, str) or not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", change_raw.strip()):
                raise ValueError("widget_ws_change_pct_missing_or_invalid")
            change = float(change_raw)
            if not math.isfinite(change):
                raise ValueError("widget_ws_change_pct_invalid")
            quote["flu_rt"] = change
            trades = transport["recent_trades"]
            if len(trades) != 3:
                raise ValueError("widget_ws_trade_veto_history_missing")
            seq = transport["source_sequences"]["0B"]
            for i, row in enumerate(trades):
                if (row.get("item") != transport["ws_request_code"]
                        or row.get("transport_epoch") != transport["producer"]["transport_epoch"]
                        or row.get("route_sequence") != seq - i
                        or type(row.get("price")) is not int or row["price"] <= 0
                        or type(row.get("received_at_ms")) is not int
                        or row["received_at_ms"] > transport["source_clocks"]["0B"] * 1000 + 1
                        or not 0 <= now_ts - row["received_at_ms"] / 1000 <= 20):
                    raise ValueError("widget_ws_trade_veto_history_invalid")
            if (abs(trades[0]["received_at_ms"] - transport["source_clocks"]["0B"] * 1000) > 1
                    or any(a["received_at_ms"] < b["received_at_ms"] for a, b in zip(trades, trades[1:]))):
                raise ValueError("widget_ws_trade_veto_endpoint_invalid")
            trade_payload = {"cntr_infr": [{"cur_prc": r["price"]} for r in trades],
                             "source": "kiwoom_ws_0B", "source_item": transport["ws_request_code"]}
        qt = datetime.fromtimestamp(transport["source_clocks"]["0B"], KST)
        bt = datetime.fromtimestamp(transport["source_clocks"]["0D"], KST)
        receipt = {k: v for k, v in transport.items() if k not in {"census", "recent_trades"}}
        receipt.update(mode="ws_input", selected_input="shared_ws_snapshot", input_adopted=True,
                       comparison_status="ws_selected")
        bbo = {k: values[k] for k in ("best_bid", "best_ask", "best_bid_qty", "best_ask_qty")}
        bbo.update(source="kiwoom_ws_0D", received_at=bt.isoformat(),
                   age_sec=now_ts - bt.timestamp(), ws_source_receipt=receipt)
        transport.update(mode="ws_input", selected_input="shared_ws_snapshot", input_adopted=True,
                         comparison_status="ws_selected", same_observation_proven=False)
        return quote, qt, bbo, bt, trade_payload
    except (ValueError, KeyError, TypeError, OSError, IndexError, OverflowError, AttributeError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        transport.update(selection_reason=reason, selected_input="none", input_adopted=False)
        raise RuntimeError("widget_ws_input_unavailable:" + reason) from exc


def compare_widget_rest(transport, *, current_price, bbo, quote_received_at, bbo_received_at):
    """Same-field diagnostics, with no freshening or automatic source promotion."""
    if transport.get("status") != "valid_ws_comparison_input":
        return
    clocks = {"0B": quote_received_at.timestamp(), "0D": bbo_received_at.timestamp()}
    deltas = {t: clocks[t] - transport["source_clocks"][t] for t in clocks}
    transport["rest_source_clocks"] = clocks
    transport["clock_deltas_sec"] = deltas
    rest = {"current_price": current_price, **{k: bbo.get(k) for k in
            ("best_bid", "best_ask", "best_bid_qty", "best_ask_qty")}}
    transport["rest_values"] = rest
    transport["different_fields"] = [k for k, v in transport["values"].items() if rest.get(k) != v]
    transport["same_observation_proven"] = False
    transport["same_market_data_scope"] = transport["ws_request_code"] == transport["request_code"]
    if any(not 0 <= delta <= 20 for delta in deltas.values()):
        transport["comparison_status"] = "not_comparable_clock_gap"
        return
    if not transport["same_market_data_scope"]:
        # KRX/NXT REST and integrated WS are valid but distinct observations.
        # Neither matching nor differing values establish route equivalence.
        transport["comparison_status"] = "different_market_data_scope"
        return
    transport["comparison_status"] = "different_observations" if transport["different_fields"] else "matched_fields"
    transport["same_observation_proven"] = False  # REST supplies no common exchange sequence.


def attach_transport_census(owner, payload):
    """Bounded per-process comparison denominator, including failed REST cycles."""
    transport = getattr(owner, "_transport_comparison", None)
    if not transport:
        return
    # collect_once and its failure publisher can both attach this same read
    # after a recorder/write error. Count the evaluation once, even if failure
    # reporting crosses a window/date boundary. A fork remains a new consumer.
    if (getattr(owner, "_transport_census_last_sample", None) is transport
            and getattr(owner, "_transport_census_last_pid", None) == os.getpid()):
        payload["market_data_transport"] = transport
        return
    # Count a reader evaluation in its own window. Failed slow cycles may
    # publish with an older cycle timestamp; later republishes are not reads.
    evaluated = transport.get("evaluated_at_epoch")
    now = (datetime.fromtimestamp(evaluated, KST) if evaluated is not None
           else datetime.fromisoformat(payload["observed_at_kst"]))
    # A fork inherits the owner object, not the parent's comparison receipt.
    # Use PID even when /proc provenance is temporarily unavailable, so a
    # provenance read failure cannot erase this process's failed denominator.
    key = (now.date().isoformat(), transport["request_code"], transport["session"], os.getpid())
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
        "ws_selected": 0,
        "ws_selection_gap": 0,
        "not_comparable_clock_gap": 0,
        "different_market_data_scope": 0, "ws_source_items": {},
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
    if transport.get("selection_reason"):
        bucket["ws_selection_gap"] += 1
    source_item = transport.get("ws_request_code", "unresolved")
    source_counts = bucket["ws_source_items"].setdefault(source_item, {"valid_ws": 0, "ws_source_gap": 0})
    source_counts["valid_ws" if transport["status"] == "valid_ws_comparison_input" else "ws_source_gap"] += 1
    while len(owner._transport_census) > 4:
        owner._transport_census.pop(min(owner._transport_census))
    try:
        consumer_process = process_generation(os.getpid())
    except (OSError, ValueError, IndexError):
        consumer_process = {"status": "process_provenance_unavailable"}
    transport["census"] = {"scope": ("process_local_ws_input" if transport.get("input_adopted") else "process_local_comparison_not_adopted_input"),
        "schema": "widget_transport_census_source_bound_v3",
        "evaluation_count_basis": "once_per_reader_result",
        "consumer_process": consumer_process,
        "windows": {str(k): {**v, "ws_source_items": {item: dict(counts)
                    for item, counts in v["ws_source_items"].items()}}
                    for k, v in owner._transport_census.items()}}
    payload["market_data_transport"] = transport
    owner._transport_census_last_sample = transport
    owner._transport_census_last_pid = os.getpid()


COMPLETED_BARS_ROOT = DATA_DIR / "runtime" / "shared_ws_completed_bars"


def completed_bar_mode(request_code, *, consumer="widget"):
    """Separate explicit bar rollout; quote selection never promotes bars."""
    if consumer not in {"widget", "episode"}:
        raise ValueError("completed_bar_consumer_invalid")
    mode = os.getenv(f"KORSTOCKSCAN_{consumer.upper()}_BAR_SOURCE", "rest").strip().lower()
    if mode not in {"rest", "ws", "ws_when_ready"}:
        raise ValueError("completed_bar_source_invalid")
    members = os.getenv(f"KORSTOCKSCAN_{consumer.upper()}_BAR_WS_SYMBOLS", "")
    if mode == "rest":
        return mode
    codes = members.split(",")
    if any(not re.fullmatch(r"[0-9]{6}", c) for c in codes) or len(set(codes)) != len(codes):
        raise ValueError("completed_bar_scope_invalid")
    return mode if re.fullmatch(r"[0-9]{6}(?:_AL)?", request_code) and request_code[:6] in codes else "rest"


def completed_bar_cache_requires_revalidation(request_code, cached):
    mode = completed_bar_mode(request_code)
    source = (cached.get("_completed_bar_source") or {}).get("source", "") if isinstance(cached, dict) else ""
    return mode == "ws" or (mode == "ws_when_ready" and source == "kiwoom_ws_AL_completed_1m")


def _bounded_json(path, limit=2 * 1024 * 1024):
    with Path(path).open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("completed_bar_artifact_size_exceeded")
    return json.loads(raw)


def _bar_session(now):
    clock = now.astimezone(KST).strftime("%H:%M")
    if "08:00" <= clock < "08:50":
        return "SOR_PREMARKET"
    if "09:00" <= clock < "15:30":
        return "SOR_REGULAR"
    if "16:00" <= clock < "20:00":
        return "SOR_AFTERMARKET"
    raise ValueError("completed_bar_session_inactive")


def observed_completed_bar_history_enabled():
    """Explicit operator-approved row exclusions; unrelated consumers stay strict."""
    return os.getenv("KORSTOCKSCAN_WS_COMPLETED_BAR_GAP_POLICY", "strict") == "observed_valid_rows"


def completed_bar_window_usable(bars):
    """Policy windows may use validated observed rows without inventing minutes."""
    observed = bool(bars) and all(getattr(bar, "history_basis", "") == "observed_valid_rows" for bar in bars)
    return bool(bars) and all(
        current.timestamp.date() == previous.timestamp.date()
        and (current.timestamp > previous.timestamp if observed
             else (current.timestamp - previous.timestamp).total_seconds() == 60)
        for previous, current in zip(bars, bars[1:])
    )


def read_shared_completed_bars(request_code, *, now, root=None, snapshot_path=None, allow_partial_history=False):
    """Historical bar clocks are causal; no quote-age TTL and no recovery I/O."""
    from src.engine.scalping.micro_reversion.completed_bars import SCHEMA, digest, item_integrity
    if now.tzinfo is None or not re.fullmatch(r"[0-9]{6}_AL", request_code):
        raise ValueError("completed_bar_identity_invalid")
    now = now.astimezone(KST)
    session = _bar_session(now)
    snapshot = _bounded_json(snapshot_path or SNAPSHOT_PATH, 8 * 1024 * 1024)
    producer = snapshot["shared_transport_producer"]
    try:
        live_process = process_generation(producer["process"]["pid"])
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        # /proc absence is a dead producer, not a missing native artifact
        # that authorizes seed/fallback REST in the caller.
        raise ValueError("completed_bar_live_binding_invalid") from exc
    snapshot_age = now.timestamp() - snapshot["generated_at_epoch"]
    if (not math.isfinite(snapshot_age) or snapshot_age < 0
            or (not allow_partial_history and snapshot_age > 20)
            or producer["connection_available"] is not True
            or producer["process"] != live_process
            or request_code not in producer["registered_items"]):
        raise ValueError("completed_bar_live_binding_invalid")
    payload = _bounded_json(Path(root or COMPLETED_BARS_ROOT) / now.date().isoformat() / request_code / (session + ".json"))
    expected = payload.pop("content_sha256")
    if (digest(payload) != expected or payload["schema"] != SCHEMA
            or payload["trade_date"] != now.date().isoformat()
            or payload["source_item"] != request_code or payload["session"] != session
            or payload["adjustment"] != "raw_same_day"
            or payload["market_data_route"] != "krx_nxt_integrated"
            or payload["producer"] != producer["process"]
            or payload["source_commit"] != producer["source_commit"]
            or payload["integrity"] != item_integrity(producer["completed_bar_integrity"], request_code)
            or type(producer["transport_epoch"]) is not int or producer["transport_epoch"] <= 0
            or payload["integrity"].get("transport_epoch") != producer["transport_epoch"]
            or payload["source_epoch"] != payload["integrity"]["observer_epoch"]
            or not payload["generated_at_epoch"] <= now.timestamp()
            or payload["actual_order_submitted"] is not False
            or payload["runtime_effect"] is not False):
        raise ValueError("completed_bar_source_contract_invalid")
    rows, previous, excluded, accepted = [], None, [], {}
    for bar in payload["bars"]:
        minute = bar["minute_epoch"]
        stamp = datetime.fromtimestamp(minute, KST)
        if (type(minute) is not int or minute % 60 or stamp.date() != now.date()
                or _bar_session(stamp) != session or (previous is not None and minute <= previous)):
            raise ValueError("completed_bar_order_or_session_invalid")
        previous = minute
        if bar["status"] == "gap":
            excluded.append({"minute_epoch": minute, "reason": "source_gap", "issues": bar["issues"]})
            if not allow_partial_history:
                rows = []
            continue
        if bar["status"] == "pending":
            continue
        if bar["source_item"] != request_code:
            raise ValueError("completed_bar_identity_invalid")
        try:
            values = [bar[k] for k in ("open", "high", "low", "close", "volume")]
            invalid = (bar["status"] != "complete" or bar["issues"] or bar["source_item"] != request_code
                    or type(bar.get("source_epoch")) is not int or bar["source_epoch"] <= 0
                    or not all(type(v) is int and v >= 0 for v in values)
                    or min(values[:4]) <= 0 or bar["high"] < max(values[:4])
                    or bar["low"] > min(values[:4]) or bar["available_at_epoch"] is None
                    or not minute + 60 <= bar["available_at_epoch"] <= now.timestamp()
                    or minute + 61 > payload["watermark_epoch"]
                    or bar["source_time"] != stamp.strftime("%Y%m%d%H%M%S"))
        except (KeyError, TypeError, ValueError, OverflowError):
            invalid = True
        if invalid:
            if not allow_partial_history:
                raise ValueError("completed_bar_ohlcv_or_clock_invalid")
            excluded.append({"minute_epoch": minute, "reason": "completed_bar_ohlcv_or_clock_invalid"})
            continue
        rows.append({"cntr_tm": bar["source_time"], "open_pric": str(bar["open"]),
                     "high_pric": str(bar["high"]), "low_pric": str(bar["low"]),
                     "cur_prc": str(bar["close"]), "trde_qty": str(bar["volume"])})
        accepted[bar["source_time"]] = bar
    invalid_from = payload.get("invalid_from_minute")
    if invalid_from is not None:
        rows = [row for row in rows if (
            datetime.strptime(row["cntr_tm"], "%Y%m%d%H%M%S").replace(tzinfo=KST).timestamp() != invalid_from
            if allow_partial_history else
            datetime.strptime(row["cntr_tm"], "%Y%m%d%H%M%S").replace(tzinfo=KST).timestamp() > invalid_from)]
    session_open = {"SOR_PREMARKET": "080000", "SOR_REGULAR": "090000", "SOR_AFTERMARKET": "160000"}[session]
    coverage = payload.get("session_coverage")
    covered = False
    if coverage is not None:
        expected_open = datetime.strptime(now.strftime("%Y%m%d") + session_open, "%Y%m%d%H%M%S").replace(tzinfo=KST)
        if (not isinstance(coverage, dict) or coverage["start_epoch"] != int(expected_open.timestamp())
                or coverage["source_epoch"] != payload["source_epoch"]
                or any(type(coverage[k]) is not int or coverage[k] < 0 for k in ("first_cumulative", "prior_cumulative"))
                or type(coverage["first_quantity"]) is not int or coverage["first_quantity"] <= 0
                or coverage["first_cumulative"] - coverage["prior_cumulative"] != coverage["first_quantity"]
                or coverage["basis"] not in {"first_premarket_print_cumulative_equals_quantity",
                                             "same_generation_prior_session_cumulative_continuity",
                                             "same_generation_session_boundary_cumulative_continuity"}):
            raise ValueError("completed_bar_session_coverage_invalid")
        first_event = datetime.fromisoformat(coverage["first_event"])
        if (first_event.tzinfo is None or first_event.date() != now.date()
                or _bar_session(first_event) != session
                or not expected_open <= first_event <= now
                or (coverage["basis"] == "first_premarket_print_cumulative_equals_quantity"
                    and (session != "SOR_PREMARKET" or coverage["prior_cumulative"] != 0))
                or (coverage["basis"] != "first_premarket_print_cumulative_equals_quantity"
                    and not re.fullmatch(r"[0-9a-f]{64}", str(coverage.get("prior_content_sha256", ""))))):
            raise ValueError("completed_bar_session_coverage_invalid")
        covered = True
    # A quiet opening minute need not contain a candle. Its absence alone is
    # not a gap when the first print's cumulative boundary is proven.
    complete_session_prefix = bool(rows) and covered and not excluded and not payload.get("history_truncated", False) and not any(b["status"] == "gap" for b in payload["bars"]) and invalid_from is None
    accepted_bars = [accepted[row["cntr_tm"]] for row in rows]
    receipt = {"source": "kiwoom_ws_AL_completed_1m", "request_code": request_code,
               "adjustment": payload["adjustment"], "source_epoch": payload["source_epoch"],
               "complete_session_prefix": complete_session_prefix,
               "session_coverage": coverage,
               "transport_epoch": producer["transport_epoch"], "producer": payload["producer"],
               "revision": payload["revision"], "content_sha256": expected,
               "available_at_epoch": max((b["available_at_epoch"] for b in accepted_bars), default=0),
               "generated_at_epoch": payload["generated_at_epoch"], "session": session,
               "cursor": payload["cursor"], "durable_cursor": payload.get("durable_cursor"),
               "historical_source_epochs": sorted({b["source_epoch"] for b in accepted_bars}),
               "rest_request_count": 0,
               "missing_range": next((
                   {"from_minute": b["minute_epoch"], "to_minute": b["minute_epoch"] + 60,
                    "source_epoch": payload["source_epoch"]}
                   for b in reversed(payload["bars"]) if b["status"] == "gap"
                   and any(issue != "startup_or_reconnect_partial_minute" for issue in b["issues"])
               ), "initial_session_history"),
               "empty_minute_policy": payload["empty_minute_policy"]}
    if allow_partial_history:
        for row in rows:
            row["_history_basis"] = "observed_valid_rows"
        receipt.update(history_basis="observed_valid_rows", excluded_bars=excluded,
                       invalid_minute_excluded=invalid_from,
                       observed_from=rows[0]["cntr_tm"] if rows else None,
                       observed_to=rows[-1]["cntr_tm"] if rows else None,
                       full_session_claimed=False)
    return {"stk_min_pole_chart_qry": rows, "_completed_bar_source": receipt}


def selected_completed_bar_payload(request_code, *, now, consumer="widget", seed_fetch=None, minimum_bars=1, history_scope="rolling", selection_receipt=None):
    mode = completed_bar_mode(request_code, consumer=consumer)
    selection = selection_receipt if selection_receipt is not None else {}
    selection.update(mode=mode, minimum_bars=minimum_bars, history_scope=history_scope)
    if mode == "rest":
        return None
    item = request_code[:6] + "_AL"
    try:
        if history_scope not in {"rolling", "session"}:
            raise ValueError("completed_bar_history_scope_invalid")
        if type(minimum_bars) is not int or minimum_bars < 1:
            raise ValueError("completed_bar_history_floor_invalid")
        partial = observed_completed_bar_history_enabled()
        result = read_shared_completed_bars(item, now=now, **({"allow_partial_history": True} if partial else {}))
        selection.update(available_bars=len(result["stk_min_pole_chart_qry"]),
                         source_content_sha256=result["_completed_bar_source"].get("content_sha256"))
        if history_scope == "session" and not partial and not result["_completed_bar_source"]["complete_session_prefix"]:
            if mode == "ws_when_ready":
                selection.update(status="rest_retained", reason="session_anchor_history_incomplete")
                return None  # Retain the existing homogeneous REST/cache path.
            if seed_fetch is None:
                raise ValueError("session_anchor_history_incomplete")
            seed = shared_completed_bar_seed(item, now=now, fetch=seed_fetch)
            seed["_completed_bar_source"]["ws_selection_blocker"] = "session_anchor_history_incomplete"
            return seed
        if len(result["stk_min_pole_chart_qry"]) >= minimum_bars:
            selection.update(status="ws_selected", reason="observed_valid_history_ready" if partial else "required_native_history_ready")
            return result
        if mode == "ws_when_ready":
            selection.update(status="rest_retained", reason="completed_bar_history_insufficient")
            return None
        if seed_fetch is None:
            raise ValueError("completed_bar_history_insufficient")
        # A homogeneous bootstrap seed may cover startup, never be spliced
        # into raw WS candles. Later WS gaps reuse it without repeated calls.
        return shared_completed_bar_seed(item, now=now, fetch=seed_fetch,
                                         missing_range=result["_completed_bar_source"]["missing_range"])
    except FileNotFoundError as exc:
        if mode == "ws_when_ready":
            selection.update(status="rest_retained", reason="native_artifact_not_yet_available")
            return None
        if seed_fetch is not None:
            return shared_completed_bar_seed(item, now=now, fetch=seed_fetch)
        raise RuntimeError("completed_ws_bars_unavailable:missing_artifact") from exc
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[A-Za-z0-9_:-]+", str(exc)) else type(exc).__name__
        raise RuntimeError("completed_ws_bars_unavailable:" + reason) from exc


def annotate_completed_bar_rest(payload, request_code, selection):
    """Keep actual REST provenance and the bounded native-readiness decision."""
    if selection.get("mode") != "ws_when_ready":
        return payload
    return {**payload, "_completed_bar_source": {
        "source": "kiwoom_rest_ka10080", "request_code": request_code,
        "adjustment": "adjusted_1", "selection": dict(selection)}}


def _read_seed_receipt(path, key):
    """Malformed existing receipts fail closed; absence alone allows a seed."""
    from src.engine.scalping.micro_reversion.completed_bars import digest
    try:
        cached = _bounded_json(path)
    except FileNotFoundError:
        return None
    try:
        if not isinstance(cached, dict):
            raise ValueError("shape")
        expected = cached.pop("content_sha256")
        if digest(cached) != expected or cached["key"] != key:
            raise ValueError("binding")
        if cached["status"] not in {"complete", "inflight"}:
            raise ValueError("status")
        for field in ("requested_at_epoch", "retry_after_epoch"):
            value = cached[field]
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("clock")
        if cached["retry_after_epoch"] < cached["requested_at_epoch"]:
            raise ValueError("clock_order")
        if cached["status"] == "complete":
            value = cached["received_at_epoch"]
            result = cached["result"]
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or value < cached["requested_at_epoch"]
                    or not isinstance(result, dict)
                    or not isinstance(result.get("stk_min_pole_chart_qry"), list)
                    or not isinstance(result.get("_completed_bar_source"), dict)):
                raise ValueError("result")
        return cached
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("completed_bar_seed_receipt_invalid") from exc


def shared_completed_bar_seed(request_code, *, now, fetch, root=None, missing_range="initial_session_history"):
    """One successful homogeneous REST seed per exact session across processes.

    flock is released on process death; contenders do not wait or issue calls.
    Failures retain a bounded retry receipt and the existing client admission
    policy still owns rate limits. Quiet WS history never enters this helper.
    """
    import fcntl
    from src.engine.scalping.micro_reversion.completed_bars import atomic_json, digest
    if now.tzinfo is None:
        raise ValueError("completed_bar_seed_clock_invalid")
    now = now.astimezone(KST)
    session = _bar_session(now)
    if not re.fullmatch(r"[0-9]{6}_AL", request_code):
        raise ValueError("completed_bar_seed_scope_invalid")
    key = {"date": now.date().isoformat(), "item": request_code, "session": session,
           "adjustment": "adjusted_1", "missing_range": missing_range}
    folder = Path(root or COMPLETED_BARS_ROOT) / ".seed" / now.date().isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (digest(key) + ".json")
    # Different missing ranges share one session admission lease as well.
    lease_key = {k: v for k, v in key.items() if k != "missing_range"}
    with (folder / (digest(lease_key) + ".lock")).open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("completed_bar_seed_lease_busy") from exc
        cached = _read_seed_receipt(path, key)
        if cached is not None:
            if cached["status"] == "complete":
                if not cached["received_at_epoch"] <= now.timestamp():
                    raise ValueError("completed_bar_seed_future")
                result = cached["result"]
                result["_completed_bar_source"] = {**result["_completed_bar_source"], "rest_request_count": 0, "seed_reused": True}
                return result
            if time.time() < cached["retry_after_epoch"]:
                raise RuntimeError("completed_bar_seed_retry_deferred")
        # The admission clock must share the lock's session scope. Otherwise
        # alternating missing ranges bypass a failed request's cooldown.
        admission_path = folder / (digest(lease_key) + ".admission.json")
        admission = _read_seed_receipt(admission_path, lease_key)
        if admission is not None and time.time() < admission["retry_after_epoch"]:
            raise RuntimeError("completed_bar_seed_retry_deferred")
        started = time.time()
        receipt = {"key": key, "owner": process_generation(os.getpid()), "status": "inflight",
                   "requested_at_epoch": started, "retry_after_epoch": started + 60,
                   "requested_range_end": now.replace(second=0,microsecond=0).isoformat()}
        receipt["content_sha256"] = digest(receipt)
        admission = {**receipt, "key": lease_key}
        admission.pop("content_sha256")
        admission["content_sha256"] = digest(admission)
        atomic_json(admission_path, admission)
        atomic_json(path, receipt)
        try:
            result = fetch(request_code)
            if not isinstance(result, dict) or not isinstance(result.get("stk_min_pole_chart_qry"), list):
                raise ValueError("completed_bar_seed_result_invalid")
            received = time.time()
            if datetime.fromtimestamp(received,KST).date() != now.date() or _bar_session(datetime.fromtimestamp(received,KST)) != session:
                raise ValueError("completed_bar_seed_session_changed")
            # Never combine adjusted REST and raw WS price bases.
            result = {**result, "_completed_bar_source": {
                "source": "kiwoom_ka10080_AL_seed", "request_code": request_code,
                "adjustment": "adjusted_1", "session": session,
                "available_at_epoch": received, "received_at_epoch": received,
                "content_sha256": digest(result), "rest_request_count": 1,
                "missing_range": key["missing_range"], "merge_policy": "homogeneous_only"}}
            receipt.pop("content_sha256")
            receipt.update(status="complete", received_at_epoch=received, result=result)
            receipt["content_sha256"] = digest(receipt)
            atomic_json(path, receipt)
            return result
        except Exception:
            # The inflight receipt supplies crash/failure cooldown. No cached
            # success is fabricated and no recursive retry is issued here.
            raise
