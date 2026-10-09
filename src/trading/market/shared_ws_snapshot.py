"""Bounded shared WS comparison and explicit collector market-input selection."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import threading
import copy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR

SNAPSHOT_PATH = DATA_DIR / "runtime" / "kiwoom_ws_snapshot" / "latest.json"
CONTRACT = "shared_ws_transport_comparison_v2"
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


_FRAME_CACHE_LOCK = threading.Lock()
_FRAME_CACHE = None


def _reset_frame_cache_after_fork():
    global _FRAME_CACHE_LOCK, _FRAME_CACHE
    _FRAME_CACHE_LOCK = threading.Lock()
    _FRAME_CACHE = None


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_frame_cache_after_fork)


def _frame_generation(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def _read_shared_frame(path):
    """One parsed frame per process and file generation, not a validity cache."""
    global _FRAME_CACHE
    with _FRAME_CACHE_LOCK:
        generation = _frame_generation(path.stat())
        key = (str(path.absolute()), generation)
        if _FRAME_CACHE is not None and _FRAME_CACHE[0] == key:
            return _FRAME_CACHE[1], _FRAME_CACHE[2]
        with path.open("rb") as handle:
            opened = _frame_generation(os.fstat(handle.fileno()))
            raw = handle.read(8 * 1024 * 1024 + 1)
            after = _frame_generation(os.fstat(handle.fileno()))
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("snapshot_size_exceeded")
        if generation != opened or opened != after or after != _frame_generation(path.stat()):
            raise ValueError("snapshot_changed_during_read")
        frame = json.loads(raw)
        digest = hashlib.sha256(raw).hexdigest()
        _FRAME_CACHE = (key, frame, digest)
        return frame, digest














COMPLETED_BARS_ROOT = DATA_DIR / "runtime" / "shared_ws_completed_bars"


def completed_bar_mode(request_code, *, consumer="main"):
    """Separate explicit bar rollout; quote selection never promotes bars."""
    if consumer != "main":
        raise ValueError("completed_bar_consumer_invalid")
    mode = os.getenv("KORSTOCKSCAN_MAIN_BAR_SOURCE", "ws_when_ready").strip().lower()
    if mode not in {"rest", "ws", "ws_when_ready"}:
        raise ValueError("completed_bar_source_invalid")
    members = os.getenv("KORSTOCKSCAN_MAIN_BAR_WS_SYMBOLS", "005930,034020,036930,196170,403870")
    if mode == "rest":
        return mode
    codes = members.split(",")
    if any(not re.fullmatch(r"[0-9]{6}", c) for c in codes) or len(set(codes)) != len(codes):
        raise ValueError("completed_bar_scope_invalid")
    return mode if re.fullmatch(r"[0-9]{6}_AL", request_code) and request_code[:6] in codes else "rest"


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


def selected_completed_bar_payload(request_code, *, now, consumer="main", seed_fetch=None, minimum_bars=1, history_scope="rolling", selection_receipt=None, required_adjustment=None):
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
        if now.tzinfo is None:
            raise ValueError("completed_bar_identity_invalid")
        # This projection owns one same-day session only. Reject an unsupported
        # consumer window before consulting a potentially retired writer. This
        # is source selection, not permission to reuse invalid WS evidence.
        session_capacity = {"SOR_PREMARKET": 50, "SOR_REGULAR": 390,
                            "SOR_AFTERMARKET": 240}[_bar_session(now)]
        if mode == "ws_when_ready" and minimum_bars > session_capacity:
            selection.update(status="rest_retained",
                             reason="requested_history_exceeds_projection_scope",
                             maximum_session_bars=session_capacity)
            return None
        # The current writer is explicitly raw_same_day. No approved same-day
        # adjusted-price equivalence exists, so do not consult it for that view.
        if required_adjustment not in {None, 'raw_same_day'}:
            if mode == 'ws_when_ready':
                selection.update(status='rest_retained', reason='price_basis_equivalence_unproven')
                return None
            raise ValueError('price_basis_equivalence_unproven')
        partial = False if consumer == "main" else observed_completed_bar_history_enabled()
        result = read_shared_completed_bars(item, now=now, **({"allow_partial_history": True} if partial else {}))
        if (required_adjustment is not None
                and result['_completed_bar_source'].get('adjustment') != required_adjustment):
            if mode == 'ws_when_ready':
                selection.update(status='rest_retained', reason='price_basis_equivalence_unproven')
                return None
            raise ValueError('price_basis_equivalence_unproven')
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
