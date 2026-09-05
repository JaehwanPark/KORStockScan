"""Bounded, source-only inputs for the existing AVG_DOWN postclose replay.

Owns observation state only, never target selection, broker calls or AI calls.
The existing observation cadence polls its cache even after the real leg exits;
loss of a subscription/quote is an explicit gap, not a fabricated price path.
"""

from __future__ import annotations

import os
import gzip
import base64
import json
import threading
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.engine.lifecycle.avg_down_policy_replay import (
    SNAPSHOT_SCHEMA,
    _json_value,
    implementation_identity,
    snapshot_version,
    loaded_code_identity,
)
from src.engine.lifecycle.avg_down_replay import FRAME_SCHEMA, canonical_digest
from src.utils.constants import DATA_DIR

STATE_SCHEMA = "avg_down_holding_state_v1"
MAX_ACTIVE = 8
MAX_FRAMES_PER_EPISODE = 7200
FRAME_INTERVAL_SEC = 1.0
MAX_FRAME_GAP_SEC = 5.0
MAX_SNAPSHOT_BYTES = 2_000_000
MAX_FRAME_BYTES = 64_000
MAX_EPISODE_BYTES = 32_000_000
MAX_DAILY_FRAME_BYTES = 256_000_000
_KST = timezone(timedelta(hours=9))
_LOCK = threading.RLock()
_ACTIVE: dict[str, dict] = {}
_SEEN: set[str] = set()
_DAY = ""
_DAILY_FRAME_BYTES = 0
_MARKET_INPUTS: dict[str, dict] = {}
_IMPLEMENTATION: dict | None = None
_POLICY_CACHE: dict = {}
_AI_STATE: dict[str, dict] = {}
AI_STATE_FIELDS = (
    "ai_disabled",
    "consecutive_failures",
    "max_consecutive_failures",
    "current_model_name",
    "model_tier1_fast",
    "model_tier2_balanced",
    "model_tier3_deep",
)
GLOBALS = (
    "COOLDOWNS",
    "ALERTED_STOCKS",
    "HIGHEST_PRICES",
    "LAST_AI_CALL_TIMES",
    "LAST_LOG_TIMES",
)
AUTHORITY = {
    "decision_authority": "source_only_paired_exit_replay",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "metric_role": "independent_exit_replay_source",
    "window_policy": "first_decision_same_episode_bounded_continuous_frames",
    "sample_floor": "all_compared_arms_complete",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "frozen_policy_state_and_fresh_conflict_free_quotes",
    "forbidden_uses": "real_order|real_fill_quality|standalone_runtime_promotion|safety_override",
}


def policy_environment() -> dict:
    return {
        key: value
        for key, value in os.environ.items()
        if key.startswith("KORSTOCKSCAN_")
        and not key.endswith("_TOKEN")
        and not any(
            part in key for part in ("SECRET", "PASSWORD", "CREDENTIAL", "API_KEY")
        )
    }


def record_ai_state(code, engine) -> None:
    """Capture policy state only; clients, keys and transport locks stay private."""
    if engine is None:
        return
    try:
        state = {name: _json_value(getattr(engine, name)) for name in AI_STATE_FIELDS}
        with _LOCK:
            _AI_STATE[str(code)[:6]] = state
            while len(_AI_STATE) > 64:
                _AI_STATE.pop(next(iter(_AI_STATE)))
    except Exception:
        with _LOCK:
            _AI_STATE.pop(str(code)[:6], None)


def _file_snapshot(paths: set[Path]) -> dict:
    files = {}
    for path in paths:
        key = str(path.absolute())
        try:
            before = path.stat()
            if before.st_size > 32_000_000:
                raise ValueError("policy_file_too_large")
            content = path.read_text(encoding="utf-8")
            after = path.stat()
            if (before.st_mtime_ns, before.st_size, before.st_ino) != (
                after.st_mtime_ns,
                after.st_size,
                after.st_ino,
            ):
                raise ValueError("policy_file_changed_during_snapshot")
            files[key] = {
                "content_gzip_b64": base64.b64encode(
                    gzip.compress(content.encode(), mtime=0)
                ).decode("ascii"),
                "size": before.st_size,
                "mtime": before.st_mtime,
                "mtime_ns": before.st_mtime_ns,
            }
        except FileNotFoundError:
            files[key] = None
    return files


def policy_snapshot(handlers, now_ts: float) -> dict:
    """Freeze loaded rules plus selected external files, never credentials."""
    global _IMPLEMENTATION
    if _IMPLEMENTATION is None:
        _IMPLEMENTATION = implementation_identity()
    if handlers.TRADING_RULES is None:
        raise ValueError("runtime_rules_not_loaded")
    rules = vars(handlers.TRADING_RULES)
    # Only application policy env; credential-like keys never enter telemetry.
    environment = policy_environment()
    paths = {
        DATA_DIR / "config" / "manual_control_excluded_codes.txt",
        DATA_DIR / "runtime" / "trade_pause_state.json",
        DATA_DIR.parent / "pause.flag",
        DATA_DIR
        / "runtime"
        / "symbol_owner_policy"
        / (
            "symbol_owner_policy_"
            + datetime.fromtimestamp(now_ts, tz=_KST).date().isoformat()
            + ".json"
        ),
    }
    for key, value in {**rules, **environment}.items():
        if (
            isinstance(value, str)
            and value
            and (key.endswith("_POLICY_FILE") or key.endswith("_EXCLUDED_CODES_FILE"))
        ):
            paths.add(Path(value))
    # Freeze the same selectors the live matrix adapters use, including absence.
    from src.engine import holding_exit_matrix_runtime as adm
    from src.engine import lifecycle_decision_matrix_runtime as ldm

    now = datetime.fromtimestamp(now_ts, tz=_KST).replace(tzinfo=None)
    selectors = {}
    for module in (adm, ldm):
        selected = module._latest_matrix_path_on_or_before(
            module._session_cutoff_source_date(now)
        )
        if selected is not None:
            paths.add(selected)
        selectors[module.__name__] = (
            str(selected.absolute()) if selected is not None else None
        )
    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "rules": _json_value(rules),
        "environment": environment,
        "files": _file_snapshot(paths),
        "implementation": deepcopy(_IMPLEMENTATION),
        "loaded_code": loaded_code_identity(handlers),
        "adapter_scope": "existing_holding_policy_quote_counterfactual",
        "matrix_selection": selectors,
    }
    rule_blobs, module_rules = {}, {}
    for name, module in list(sys.modules.items()):
        if (
            not name.startswith(("src.engine.", "src.trading.", "src.utils."))
            or module is None
        ):
            continue
        loaded = getattr(module, "TRADING_RULES", None)
        if loaded is None:
            continue
        value = _json_value(vars(loaded))
        digest = canonical_digest(value)
        rule_blobs[digest] = value
        module_rules[name] = digest
    snapshot.update(rule_blobs=rule_blobs, module_rules=module_rules)
    if len(str(snapshot).encode()) > MAX_SNAPSHOT_BYTES:
        raise ValueError("full_policy_snapshot_too_large")
    canonical_digest(snapshot)
    return snapshot


def holding_state(handlers, stock: dict) -> dict:
    budget = handlers.DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET
    with budget._lock:
        budget_state = {
            "window_sec": budget.window_sec,
            "total_cap": budget.total_cap,
            "group_cap": budget.group_cap,
            "events": {
                key: _json_value(list(rows)) for key, rows in budget._events.items()
            },
        }
    # Stock is copied under its normal owner lock by the caller. An unsupported
    # object is a snapshot gap; stringifying it would erase decision semantics.
    from src.engine import lifecycle_decision_matrix_runtime as ldm

    with _LOCK:
        ai_state = deepcopy(_AI_STATE.get(str(stock.get("code", ""))[:6]))
    return {
        "schema": STATE_SCHEMA,
        "stock": _json_value(stock),
        "globals": {name: _json_value(getattr(handlers, name)) for name in GLOBALS},
        "ai_budget": budget_state,
        "filled_add_qty": 0,
        "ldm_promote_counter": _json_value(ldm._PROMOTE_COUNTER),
        "ai_engine_state": ai_state,
    }


def micro_state(handlers, code: str) -> dict:
    store = handlers._SCALPING_MICRO_ESTIMATOR_STORE
    with store._lock:
        state = store._states.get(code)
        return {
            "config": _json_value(vars(store.config)),
            "state": _json_value(vars(state)) if state is not None else None,
        }


def warm_policy_cache(handlers, *, now_ts: float) -> None:
    """Compression/large policy reads belong to the observation thread, not BUY latency."""
    with _LOCK:
        if now_ts - _POLICY_CACHE.get("warmed_at", 0) < 30:
            return
    snapshot = policy_snapshot(handlers, now_ts)
    with _LOCK:
        _POLICY_CACHE.update(
            snapshot=snapshot,
            warmed_at=now_ts,
            rules_identity=id(handlers.TRADING_RULES),
        )


def _cached_policy(handlers, now_ts):
    with _LOCK:
        cache = dict(_POLICY_CACHE)
    if (
        not cache.get("snapshot")
        or now_ts - cache.get("warmed_at", 0) > 60
        or cache.get("rules_identity") != id(handlers.TRADING_RULES)
    ):
        raise ValueError("policy_cache_not_ready")
    snapshot = cache["snapshot"]
    environment = policy_environment()
    if environment != snapshot["environment"]:
        raise ValueError("policy_environment_changed_since_snapshot")
    if _json_value(vars(handlers.TRADING_RULES)) != snapshot["rules"]:
        raise ValueError("loaded_rules_changed_since_snapshot")
    # A newly published matrix can change selection without changing the old
    # file's mtime. Check the selector, not just captured file metadata.
    now = datetime.fromtimestamp(now_ts, tz=_KST).replace(tzinfo=None)
    for name, path in snapshot.get("matrix_selection", {}).items():
        module = sys.modules[name]
        selected = module._latest_matrix_path_on_or_before(
            module._session_cutoff_source_date(now)
        )
        if (str(selected.absolute()) if selected is not None else None) != path:
            raise ValueError("matrix_selection_changed_since_snapshot")
    for name, row in snapshot["files"].items():
        try:
            stat = Path(name).stat()
            if row is None or (stat.st_mtime_ns, stat.st_size) != (
                row["mtime_ns"],
                row["size"],
            ):
                raise ValueError("policy_file_changed_since_snapshot")
        except FileNotFoundError:
            if row is not None:
                raise ValueError("policy_file_removed_since_snapshot") from None
    return snapshot


def prepare(handlers, stock: dict, code: str, episode: str, *, now_ts: float) -> dict:
    """Prepare before emitting the first decision; do not replace a failed first opportunity."""
    global _DAY, _DAILY_FRAME_BYTES
    day = datetime.fromtimestamp(now_ts, tz=_KST).date().isoformat()
    with _LOCK:
        if day != _DAY:
            _ACTIVE.clear()
            _SEEN.clear()
            _DAY = day
            _DAILY_FRAME_BYTES = 0
        if episode in _SEEN:
            return {"replay_capture_state": "first_episode_decision_already_registered"}
        if len(_ACTIVE) >= MAX_ACTIVE or _DAILY_FRAME_BYTES >= MAX_DAILY_FRAME_BYTES:
            return {"replay_capture_state": "capture_capacity_gap"}
    with handlers.ENTRY_LOCK:
        state = holding_state(handlers, stock)
        peak = (handlers.HIGHEST_PRICES or {}).get(
            handlers._price_tracking_key(stock, code)
        )
    snapshot = _cached_policy(handlers, now_ts)
    return {
        "policy_snapshot": snapshot,
        "exit_policy_version": snapshot_version(snapshot),
        "initial_policy_state": state,
        "replay_peak_price": peak,
        "replay_start_sequence": 0,
        "replay_capture_state": "armed_source_only",
        "replay_max_frame_gap_sec": MAX_FRAME_GAP_SEC,
    }


def register(
    *,
    episode: str,
    source_id: str,
    decision_id: str,
    code: str,
    venue: str,
    now_ts: float,
    fields: dict,
) -> None:
    with _LOCK:
        if episode in _SEEN:
            return
        _SEEN.add(episode)
        if fields.get("replay_capture_state") != "armed_source_only":
            return
        _ACTIVE[episode] = {
            "position_episode_id": episode,
            "source_observation_id": source_id,
            "scale_in_decision_id": decision_id,
            "stock_code": code,
            "venue": venue,
            "exit_policy_version": fields["exit_policy_version"],
            "sequence": 0,
            "last_ts": now_ts,
            "started_at": now_ts,
            "captured_bytes": 0,
        }


def observe_cycle(*, now_ts: float, snapshot_provider, market_builder, emit) -> int:
    """Existing cached snapshots only; bounded append failure is visible via sequence gaps."""
    global _DAILY_FRAME_BYTES
    emitted_count = 0
    due = []
    with _LOCK:
        for episode, row in list(_ACTIVE.items()):
            if now_ts - row["last_ts"] < FRAME_INTERVAL_SEC:
                continue
            row["sequence"] += 1
            timestamp = datetime.fromtimestamp(now_ts, tz=_KST).isoformat()
            frame = {
                key: value
                for key, value in row.items()
                if key not in {"last_ts", "started_at", "captured_bytes"}
            }
            gap = now_ts - row["last_ts"] > MAX_FRAME_GAP_SEC
            row["last_ts"] = now_ts
            frame.update(
                replay_frame_schema=FRAME_SCHEMA,
                replay_observed_at=timestamp,
                full_policy_decisions={},
                external_results={},
                **AUTHORITY,
            )
            stop = (
                row["sequence"] >= MAX_FRAMES_PER_EPISODE
                or datetime.fromtimestamp(now_ts, tz=_KST).hour >= 20
            )
            due.append(
                (frame, gap, stop, deepcopy(_MARKET_INPUTS.get(row["stock_code"], {})))
            )
            if stop:
                _ACTIVE.pop(episode, None)
    # Do not hold the registry lock across WS locks, JSON serialization or log
    # I/O: a source-only append must never stall a live ADD decision.
    for frame, gap, stop, recorded_inputs in due:
        try:
            code = frame["stock_code"]
            market = market_builder(code, snapshot_provider(code) or {}, now_ts)
            frame["market"] = _json_value(market)
            frame["market"]["recorded_inputs"] = recorded_inputs
            if gap:
                frame["capture_gap"] = "observer_cadence_gap"
            if stop:
                frame["capture_end"] = "bounded_capture_window_end"
            if len(str(frame).encode()) > MAX_FRAME_BYTES:
                raise ValueError("replay_frame_size_limit")
        except Exception as exc:
            frame["market"] = {"source_quality": "unavailable"}
            frame["capture_gap"] = "replay_snapshot_error:" + type(exc).__name__
        frame_bytes = len(json.dumps(frame, ensure_ascii=True).encode())
        with _LOCK:
            _DAILY_FRAME_BYTES += frame_bytes
            active = _ACTIVE.get(frame["position_episode_id"])
            if active is not None:
                active["captured_bytes"] += frame_bytes
                if (
                    active["captured_bytes"] >= MAX_EPISODE_BYTES
                    or _DAILY_FRAME_BYTES >= MAX_DAILY_FRAME_BYTES
                ):
                    frame["capture_end"] = "capture_byte_budget_exhausted"
                    _ACTIVE.pop(frame["position_episode_id"], None)
        frame["source_event_id"] = "avgdn-frame-" + canonical_digest(frame)
        try:
            result = emit(frame)
            if (
                isinstance(result, dict)
                and result.get("structured_append_succeeded") is True
            ):
                emitted_count += 1
        except Exception:
            # Never retry the old frame with a later market. The next sequence
            # exposes the lost append to the offline validator.
            pass
    return emitted_count


def record_market_inputs(code: str, *, now_ts: float, **values) -> None:
    """Observe values the live owner already acquired; never fetch new inputs."""
    try:
        normalized = _json_value(values)
        prepared = {}
        for key, value in normalized.items():
            encoded = json.dumps(
                value, ensure_ascii=True, separators=(",", ":")
            ).encode()
            if len(encoded) > 1_000_000:
                prepared[key] = {
                    "observed_at": float(now_ts),
                    "input_gap": "market_input_size_limit",
                }
                continue
            prepared[key] = {
                "observed_at": float(now_ts),
                **(
                    {
                        "value_gzip_b64": base64.b64encode(
                            gzip.compress(encoded, mtime=0)
                        ).decode("ascii"),
                        "value_sha256": canonical_digest(value),
                    }
                    if len(encoded) > 1024
                    else {"value": value}
                ),
            }
        with _LOCK:
            row = _MARKET_INPUTS.setdefault(str(code)[:6], {})
            row.update(prepared)
            # A bounded process-local source cache, not a second market feed.
            while len(_MARKET_INPUTS) > 64:
                _MARKET_INPUTS.pop(next(iter(_MARKET_INPUTS)))
    except Exception:
        pass
