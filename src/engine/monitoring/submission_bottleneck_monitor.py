"""Observe Sentinel's exact machine funnel; notification has no trading authority."""

from __future__ import annotations

import argparse
import ast
import copy
import fcntl
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import time
import uuid
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.notify_error_detection_admin import (
    _load_telegram_config,
    _send_telegram,
    _write_state,
)
from src.engine.monitoring import observer_artifact_io as observer_io
from src.utils.constants import PROJECT_ROOT
from src.utils.kiwoom_utils import is_canonical_stock_code

SCHEMA = "submission_bottleneck_monitor_v1"
KST = ZoneInfo("Asia/Seoul")
# Diagnostic persistence only. Never used by a trading policy or guard.
WINDOW_SEC = 1800
GRACE_SEC = 600
PERSIST_SEC = 900
MIN_PROMOTIONS = 10
SOURCE_WINDOW_SEC = 600
SOURCE_TAIL_BYTES = 32 * 1024 * 1024
DELAY_STAGES = frozenset(
    {
        "pre_submit_delay_committed",
        "pre_submit_delay_quote_observed",
        "pre_submit_delay_intent_terminal",
        "pre_submit_delay_recheck_observed",
    }
)
_DELAY_LEGACY_HORIZONS = (0, 30, 60, 120, 180)
_DELAY_RESEARCH_GRID = "legacy_and_short_clock_v1"
_DELAY_RESEARCH_HORIZONS = (0, 1, 3, 5, 30, 60, 120, 180)
DELAY_RAW_BUDGET = 32 * 1024 * 1024
DELAY_WINDOW_SEC = 600
DELAY_SUMMARY_GRACE_SEC = 150
_HEALTH_ACTOR = ContextVar("submission_monitor_health_actor", default=None)
_HEALTH_BIRTH = ContextVar("submission_monitor_health_birth", default=None)

# Report-only reasons emitted by main_fixed_watch.observation_ready. Missing
# quotes and warmup remain source waits, never source-health or order approval.
_FIXED_SOURCE_WAIT_REASONS = frozenset(
    {
        "post_receipt_observation_warmup",
        "fixed_watch_post_receipt_warmup",
        "fixed_watch_warmup",
        "route_snapshot_missing",
        "exact_route_item_missing",
        "exact_0B_missing",
        "exact_0D_missing",
        "post_admission_0B_missing",
        "post_admission_0D_missing",
        "price_missing",
    }
)


def _verified_health_actor_birth(proof, actor, now, generation=None):
    """Validate the additive native birth receipt without I/O or authority."""
    try:
        if (
            not isinstance(proof, dict)
            or proof.get("schema") != "submission_monitor_actor_birth_v1"
            or proof.get("status") != "verified"
            or proof.get("actor") != actor
            or proof.get("runtime_effect") is not False
            or proof.get("allowed_runtime_apply") is not False
            or not isinstance(actor, list)
            or len(actor) != 2
            or any(
                not isinstance(p, str)
                or not p.isdigit()
                or not 0 < len(p) <= 20
                or int(p) <= 0
                for p in actor
            )
        ):
            return None
        epoch, hz, ticks = (
            proof.get(k)
            for k in ("boot_epoch", "clock_ticks_per_second", "start_ticks")
        )
        if (
            any(type(v) is not int or v <= 0 for v in (epoch, hz, ticks))
            or hz > 1000000
            or ticks != int(actor[1])
        ):
            return None
        lower = (
            epoch + ticks / hz - 1.0
        )  # btime has second precision; retain the preceding second.
        if (
            not 0 < lower <= now.timestamp()
            or type(proof.get("birth_lower_bound_epoch")) not in (int, float)
            or proof["birth_lower_bound_epoch"] != lower
            or proof.get("birth_lower_bound_at")
            != datetime.fromtimestamp(lower, KST).isoformat()
            or stamp(proof.get("observed_at")) != now
            or not isinstance(proof.get("process_cwd"), str)
            or not Path(proof["process_cwd"]).is_absolute()
        ):
            return None
        if generation is not None:
            receipt = generation.get("selector_reported_pid_receipt") or {}
            if (
                proof != generation.get("actor_birth_proof")
                or stamp(generation.get("started_at")) != now
                or actor
                != [
                    str(receipt.get("pid") or ""),
                    str(receipt.get("start_ticks") or ""),
                ]
                or proof["process_cwd"] != receipt.get("process_cwd")
                or proof["process_cwd"] != str(Path(generation["release_root"]) / "src")
            ):
                return None
        return lower
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, OSError):
        return None


def _attest_health_actor_birth(generation, now):
    """One bounded local attestation; no broker/source query or order authority."""
    try:
        receipt = generation["selector_reported_pid_receipt"]
        pid, ticks = receipt["pid"], receipt["start_ticks"]
        if (
            type(pid) is not int
            or pid <= 0
            or not isinstance(ticks, str)
            or not ticks.isdigit()
        ):
            raise ValueError("actor_identity_invalid")
        path = Path("/proc") / str(pid)
        before = observer_io.regular_bytes(path / "stat", limit=65536)
        observed_ticks = before.decode().split(") ", 1)[1].split()[19]
        cwd = str((path / "cwd").resolve(strict=True))
        boot = observer_io.regular_bytes(Path("/proc/stat"), limit=256 * 1024).decode()
        epoch = int(
            next(
                line.split()[1]
                for line in boot.splitlines()
                if line.startswith("btime ")
            )
        )
        hz = os.sysconf("SC_CLK_TCK")
        if (
            observed_ticks != ticks
            or cwd != receipt["process_cwd"]
            or cwd != str(Path(generation["release_root"]) / "src")
            or type(hz) is not int
            or hz <= 0
            or observer_io.regular_bytes(path / "stat", limit=65536)
            .decode()
            .split(") ", 1)[1]
            .split()[19]
            != ticks
        ):
            raise ValueError("actor_live_identity_changed")
        lower = epoch + int(ticks) / hz - 1.0
        if not 0 < lower <= now.timestamp():
            raise ValueError("actor_birth_clock_invalid")
        return dict(
            schema="submission_monitor_actor_birth_v1",
            status="verified",
            actor=[str(pid), ticks],
            observed_at=now.isoformat(),
            boot_epoch=epoch,
            clock_ticks_per_second=hz,
            start_ticks=int(ticks),
            birth_lower_bound_epoch=lower,
            birth_lower_bound_at=datetime.fromtimestamp(lower, KST).isoformat(),
            process_cwd=cwd,
            runtime_effect=False,
            allowed_runtime_apply=False,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        StopIteration,
        OverflowError,
    ):
        return dict(
            schema="submission_monitor_actor_birth_v1",
            status="unverified",
            runtime_effect=False,
        )


@contextmanager
def _health_actor_scope(generation):
    receipt = (
        generation.get("selector_reported_pid_receipt")
        if isinstance(generation, dict)
        else None
    )
    actor = None
    if isinstance(receipt, dict):
        parts = [str(receipt.get("pid") or ""), str(receipt.get("start_ticks") or "")]
        if all(p.isdigit() and 0 < len(p) <= 20 and int(p) > 0 for p in parts):
            actor = parts
    token = _HEALTH_ACTOR.set(actor)
    proof = (
        generation.get("actor_birth_proof") if isinstance(generation, dict) else None
    )
    at = stamp(generation.get("started_at")) if isinstance(generation, dict) else None
    birth_token = _HEALTH_BIRTH.set(
        proof
        if at and _verified_health_actor_birth(proof, actor, at, generation) is not None
        else None
    )
    try:
        yield
    finally:
        _HEALTH_ACTOR.reset(token)
        _HEALTH_BIRTH.reset(birth_token)


def _health_cohort(view, actor, now, *, excluded=0):
    result = dict(
        schema="submission_monitor_current_health_cohort_v1",
        as_of=now.isoformat(),
        window_seconds=SOURCE_WINDOW_SEC,
        actor=list(actor),
        view=view,
        excluded_observation_count=excluded,
        excluded_classification="historical_not_current_cohort",
        decision_authority="report_only",
        runtime_effect=False,
        allowed_runtime_apply=False,
    )
    if _HEALTH_BIRTH.get():
        result["actor_birth_proof"] = _HEALTH_BIRTH.get()
    return result


def _row_actor(row):
    native = row.get("continuous_reversal_consumption")
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    receipt = fields.get(
        "native_observation_receipt", fields.get("zero_base_probe_observation_receipt")
    )
    if isinstance(receipt, str) and len(receipt) <= 8192:
        try:
            receipt = json.loads(receipt)
        except (ValueError, TypeError):
            receipt = None
    candidates = [
        row,
        native if isinstance(native, dict) else {},
        fields,
        receipt if isinstance(receipt, dict) else {},
    ]
    identities = set()
    for value in candidates:
        for pid_key, start_key in (
            ("async_producer_pid", "async_producer_start_ticks"),
            ("pid", "process_start_ticks"),
            ("process_pid", "process_start_ticks"),
            ("zero_base_producer_pid", "zero_base_producer_start_ticks"),
        ):
            actor = [str(value.get(pid_key) or ""), str(value.get(start_key) or "")]
            if all(p.isdigit() and 0 < len(p) <= 20 and int(p) > 0 for p in actor):
                identities.add(tuple(actor))
    return list(next(iter(identities))) if len(identities) == 1 else None


def stamp(value):
    try:
        parsed = datetime.fromisoformat(str(value))
        return (
            parsed.replace(tzinfo=KST)
            if parsed.tzinfo is None
            else parsed.astimezone(KST)
        )
    except (ValueError, TypeError, OverflowError):
        return None


def _recent_source_rows(
    path,
    now,
    *,
    time_field,
    tail_bytes=SOURCE_TAIL_BYTES,
    window_sec=SOURCE_WINDOW_SEC,
    allow_adjacent_date=False,
):
    """Read a bounded, complete JSONL suffix; never equate a partial tail to zero gaps."""
    source = {
        "status": "unobservable",
        "tail_truncated": False,
        "window_covered": False,
        "recent_count": 0,
    }
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if not before.st_size:
                source["reason"] = "empty_source"
                return [], source
            start = max(0, before.st_size - tail_bytes)
            stream.seek(start)
            payload = stream.read(before.st_size - start)
            after = path.stat()
        if (before.st_dev, before.st_ino) != (
            after.st_dev,
            after.st_ino,
        ) or after.st_size < before.st_size:
            source["reason"] = "source_generation_changed"
            return [], source
    except OSError as exc:
        source["reason"] = (
            "compressed_archive_not_current_bounded_source"
            if path.with_suffix(path.suffix + ".gz").exists()
            else type(exc).__name__
        )
        return [], source
    if start:
        payload = payload.partition(b"\n")[2]
    lines = payload.split(b"\n")
    incomplete_last_line = bool(lines[-1])
    lines.pop()  # A concurrently appended final line has no complete receipt.
    rows, first_at, malformed, missing_clock = [], None, 0, 0
    for line in lines:
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("source_row_not_object")
            at = stamp(row.get(time_field))
            if at is None:
                missing_clock += 1
                continue
            if (not allow_adjacent_date and at.date() != now.date()) or at > now:
                continue
            first_at = at if first_at is None else min(first_at, at)
            if (now - at).total_seconds() <= window_sec:
                rows.append(row)
        except (ValueError, UnicodeDecodeError, TypeError):
            malformed += 1
    covered = not start or (
        first_at is not None and (now - first_at).total_seconds() >= window_sec
    )
    source.update(
        status=(
            "complete"
            if covered
            and not malformed
            and not missing_clock
            and not incomplete_last_line
            else "partial"
        ),
        tail_truncated=bool(start),
        window_covered=covered,
        recent_count=len(rows),
        malformed_rows=malformed,
        incomplete_last_line=incomplete_last_line,
        missing_timestamp_rows=missing_clock,
        first_read_at=first_at.isoformat() if first_at else None,
    )
    source.update(
        bytes_read=len(payload),
        read_count=1,
        source_size=before.st_size,
        source_identity=dict(device=before.st_dev, inode=before.st_ino),
    )
    return rows, source


def _indexed_entry_trace_rows(
    data_root, path, now, *, tail_bytes, window_sec, pid_identity=None
):
    """Use the native offset/hash index; never rebuild it or widen raw intake."""
    from src.engine.automation import main_trailing_source_store as store

    try:
        generation = store.generation(data_root, path)
    except (OSError, ValueError, sqlite3.Error):
        return None  # Legacy/unindexed sources retain the bounded raw reader.
    source = dict(
        status="partial",
        tail_truncated=False,
        window_covered=False,
        recent_count=0,
        malformed_rows=0,
        missing_timestamp_rows=0,
        incomplete_last_line=False,
        bytes_read=0,
        index_bytes_read=0,
        read_count=0,
        source_size=generation["size"],
        native_index_generation=generation,
        coverage_basis="native_index_projection_or_exact_raw_offset_size_sha256",
    )
    rows = []
    cutoff = (now - timedelta(seconds=window_sec)).isoformat()
    try:
        with path.open("rb") as stream:
            if store.signature(os.fstat(stream.fileno())) != generation["source_stat"]:
                raise ValueError("source_generation_changed")
            for value, reference in store.read_rows(
                data_root,
                path,
                kinds=["entry_trace", "source_gap"],
                after=cutoff,
                include_undated=True,
            ):
                source["index_bytes_read"] += len(store.encode(value))
                if source["index_bytes_read"] + source["bytes_read"] > tail_bytes:
                    raise ValueError("indexed_trace_window_partition_required")
                if value["kind"] != "entry_trace":
                    raise ValueError("indexed_trace_projection_gap")
                at = stamp(value["row"].get("decision_ts"))
                if at is None:
                    source["missing_timestamp_rows"] += 1
                    raise ValueError("indexed_trace_timestamp_missing")
                if (
                    at.date() != now.date()
                    or not 0 <= (now - at).total_seconds() <= window_sec
                ):
                    continue
                native = value["row"].get("continuous_reversal_consumption") or {}
                if (
                    pid_identity is not None
                    and native
                    and [
                        str(native.get(k) or "") for k in ("pid", "process_start_ticks")
                    ]
                    != list(map(str, pid_identity))
                ):
                    continue
                if value.get("lineage_projection_version") == 1:
                    rows.append(value["row"])
                    continue
                size, offset = reference["size"], reference["decoded_offset"]
                if (
                    type(size) is not int
                    or type(offset) is not int
                    or size <= 0
                    or offset < 0
                    or offset + size > generation["size"]
                    or source["index_bytes_read"] + source["bytes_read"] + size
                    > tail_bytes
                ):
                    raise ValueError("indexed_trace_window_partition_required")
                stream.seek(offset)
                raw = stream.read(size)
                source["bytes_read"] += len(raw)
                source["read_count"] += 1
                if (
                    len(raw) != size
                    or hashlib.sha256(raw).hexdigest() != reference["sha256"]
                ):
                    raise ValueError("indexed_trace_raw_hash_changed")
                if not raw.endswith(b"\n"):
                    source["incomplete_last_line"] = True
                    raise ValueError("indexed_trace_incomplete_line")
                row = json.loads(raw)
                if (
                    not isinstance(row, dict)
                    or row.get("schema") != "ai_decision_trace_v1"
                    or row.get("decision_stage") != "entry_screen"
                    or row.get("decision_ts") != value["row"].get("decision_ts")
                    or row.get("decision_trace_id")
                    != value["row"].get("decision_trace_id")
                ):
                    raise ValueError("indexed_trace_projection_binding_invalid")
                rows.append(row)
            if (
                store.signature(os.fstat(stream.fileno())) != generation["source_stat"]
                or store.generation(data_root, path) != generation
            ):
                raise ValueError("source_generation_changed")
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        source.update(reason=str(error)[:160], recent_count=len(rows))
        return rows, source
    source.update(
        status="complete",
        window_covered=True,
        recent_count=len(rows),
        source_identity=dict(
            device=generation["source_stat"][0], inode=generation["source_stat"][1]
        ),
    )
    return rows, source


def _reversal_provider_lineage(
    data_root,
    now,
    observations,
    *,
    tail_bytes,
    window_sec=WINDOW_SEC,
    pid_identity=None,
    _loaded=None,
):
    """Join the observation cohort using exact producer IDs and content hashes.

    A request is preparation, a raw response is reception, and a valid response
    still needs Main execution revalidation. No provider or order is replayed.
    The optional window/identity pins support finite offline receipt audits;
    scheduled execution retains the existing time and byte budgets.
    """
    from src.engine.scalping.ai_decision_trace import _json_bytes

    now = stamp(now)
    if _loaded is None:
        request_rows, requests = _recent_source_rows(
            data_root
            / "ai_decision_requests"
            / f"ai_decision_requests_{now.date()}.jsonl",
            now,
            time_field="captured_at",
            tail_bytes=tail_bytes,
            window_sec=window_sec + 5,
        )
        trace_path = (
            data_root / "ai_decision_trace" / f"ai_decision_trace_{now.date()}.jsonl"
        )
        indexed = _indexed_entry_trace_rows(
            data_root,
            trace_path,
            now,
            tail_bytes=tail_bytes,
            window_sec=window_sec + 5,
            pid_identity=pid_identity,
        )
        trace_rows, traces = (
            indexed
            if indexed is not None
            else _recent_source_rows(
                trace_path,
                now,
                time_field="decision_ts",
                tail_bytes=tail_bytes,
                window_sec=window_sec + 5,
            )
        )
    else:
        request_rows, requests, trace_rows, traces = _loaded
        historical = {}
        for item in observations:
            at = stamp(item.get("captured_at"))
            receipt = item.get("runtime_consumption") or {}
            identity = [
                str(receipt.get("pid") or ""),
                str(receipt.get("process_start_ticks") or ""),
            ]
            digest = item.get("machine_observation_sha256")
            if (
                at is not None
                and (
                    not 0 <= (now - at).total_seconds() <= window_sec
                    or identity != list(map(str, pid_identity))
                )
                and isinstance(digest, str)
                and hashlib.sha256(
                    _json_bytes(
                        {
                            k: v
                            for k, v in item.items()
                            if k != "machine_observation_sha256"
                        }
                    )
                ).hexdigest()
                == digest
            ):
                historical[digest] = identity
        historical_requests = {
            r.get("request_id"): _row_actor(r)
            for r in trace_rows
            if isinstance(r.get("request_id"), str)
            and isinstance(r.get("machine_observation_sha256"), str)
            and r["machine_observation_sha256"] in historical
            and _row_actor(r) == historical[r["machine_observation_sha256"]]
        }
        request_rows = [
            r
            for r in request_rows
            if stamp(r.get("captured_at")) is not None
            and 0 <= (now - stamp(r["captured_at"])).total_seconds() <= window_sec + 5
            and not (
                r.get("request_id") in historical_requests
                and _row_actor(r) == historical_requests[r.get("request_id")]
            )
        ]
        trace_rows = [
            r
            for r in trace_rows
            if stamp(r.get("decision_ts")) is not None
            and 0 <= (now - stamp(r["decision_ts"])).total_seconds() <= window_sec + 5
            and not (
                isinstance(r.get("machine_observation_sha256"), str)
                and r["machine_observation_sha256"] in historical
                and _row_actor(r) == historical[r["machine_observation_sha256"]]
            )
        ]
        # The loaded suffix was read for the outer 30-minute population. Its
        # partial flag does not describe this narrower current-PID window.
        # Retain the original receipt and prove coverage from the same bytes;
        # never reread, infer missing rows, or hide malformed/incomplete input.
        narrowed = []
        for source in (requests, traces):
            source = dict(source)
            first = stamp(source.get("first_read_at"))
            lower = now - timedelta(seconds=window_sec + 5)
            if (
                source.get("status") == "partial"
                and source.get("window_covered") is False
                and source.get("tail_truncated") is True
                and first is not None
                and first <= lower
                and type(source.get("malformed_rows")) is int
                and source["malformed_rows"] == 0
                and type(source.get("missing_timestamp_rows")) is int
                and source["missing_timestamp_rows"] == 0
                and source.get("incomplete_last_line") is False
                and not source.get("reason")
            ):
                source.update(
                    status="complete",
                    window_covered=True,
                    original_window_status="partial",
                    coverage_basis="current_lineage_window_bounded_tail",
                    current_window_start_at=lower.isoformat(),
                    current_window_seconds=window_sec + 5,
                )
            narrowed.append(source)
        requests, traces = narrowed
    issues, gaps, noncall, stops = Counter(), Counter(), Counter(), Counter()

    def mapping(value):
        return value if isinstance(value, dict) else {}

    def identity(row, *, native=False):
        row = mapping(row)
        return (
            str(row.get("pid" if native else "async_producer_pid") or ""),
            str(
                row.get(
                    "process_start_ticks" if native else "async_producer_start_ticks"
                )
                or ""
            ),
        )

    def valid_identity(value):
        return all(part.isdigit() and int(part) > 0 for part in value)

    def digest(value):
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(c in "0123456789abcdef" for c in value)
        )

    def unique(rows, field, kind):
        retained, conflicts = {}, set()
        for row in rows:
            key = row.get(field)
            if not isinstance(key, str) or not key:
                gaps[kind + "_identity_missing"] += 1
                continue
            if key in retained and retained[key] != row:
                conflicts.add(key)
            else:
                retained[key] = row
        for key in conflicts:
            retained.pop(key, None)
            issues[kind + "_identity_conflict"] += 1
        return retained

    cohort = {}
    for row in observations:
        raw_source = mapping(mapping(row.get("source")).get("exact_payload"))
        role = (
            row.get("evaluation_role")
            or raw_source.get("evaluation_role")
            or "unspecified_legacy"
        )
        if role not in {"main_live", "unspecified_legacy"}:
            continue  # Probe/CF evaluations never join the Main provider funnel.
        at = stamp(row.get("captured_at"))
        receipt = mapping(row.get("runtime_consumption"))
        producer = identity(receipt, native=True)
        if (
            at is None
            or at.date() != now.date()
            or not 0 <= (now - at).total_seconds() <= window_sec
            or pid_identity is not None
            and producer != tuple(map(str, pid_identity))
        ):
            continue
        key = row.get("machine_observation_sha256")
        if (
            not digest(key)
            or hashlib.sha256(
                _json_bytes(
                    {k: v for k, v in row.items() if k != "machine_observation_sha256"}
                )
            ).hexdigest()
            != key
        ):
            issues["reversal_observation_hash_invalid"] += 1
            continue
        if key in cohort and cohort[key] != row:
            issues["observation_identity_conflict"] += 1
            cohort[key] = None
        elif key not in cohort:
            cohort[key] = row
    cohort = {key: row for key, row in cohort.items() if row is not None}
    producers = {
        identity(row.get("runtime_consumption") or {}, native=True)
        for row in cohort.values()
    }
    if pid_identity is not None:
        producers.add(tuple(map(str, pid_identity)))
    producers = {value for value in producers if valid_identity(value)}
    bundles = {row.get("bundle_sha256") for row in cohort.values()}
    request_index = unique(request_rows, "request_id", "request")
    trace_index = unique(trace_rows, "decision_trace_id", "trace")
    prepared, responded, transmitted, timeouts = set(), set(), set(), set()
    matched_requests, valid_response, valid_pass, effective_pass = (
        set(),
        set(),
        set(),
        set(),
    )
    raw_verdicts = Counter()
    attempt_ledger = []
    observed_trace_keys = set()
    # Explicit old captures retain their exact observation binding. They do not
    # gain an inferred PID, transport call or response from that preparation.
    for request_id, row in request_index.items():
        binding = mapping(row.get("continuous_reversal_request_binding"))
        key = binding.get("machine_observation_sha256")
        if (
            key in cohort
            and row.get("schema") is None
            and binding.get("binding_status") == "matched"
        ):
            prepared.add(key)
            matched_requests.add(request_id)
            gaps["legacy_request_identity_unverified"] += 1
            if (
                str(cohort[key]["source"]["assessment"].get("action")).upper()
                != "ENTER_NOW"
            ):
                issues["reversal_provider_request_after_nonentry"] += 1

    for trace_id, row in trace_index.items():
        key = row.get("machine_observation_sha256")
        if key is not None and not isinstance(key, str):
            issues["reversal_trace_observation_hash_invalid"] += 1
            continue
        observation = cohort.get(key)
        rejected = mapping(row.get("continuous_reversal_rejected_claim_receipt"))
        native = mapping(row.get("continuous_reversal_consumption"))
        if observation is None:
            # A pre-adjudication terminal has no fabricated machine observation.
            rejected_identity = (
                str(rejected.get("process_pid") or ""),
                str(rejected.get("process_start_ticks") or ""),
            )
            at = stamp(row.get("decision_ts"))
            if (
                key
                or row.get("source_event_stage") == "zero_base_probe_machine_only_v1"
                or rejected_identity not in producers
                or row.get("machine_bundle_sha256") not in bundles
                or at is None
                or not 0 <= (now - at).total_seconds() <= window_sec
            ):
                continue
            if _reversal_lifecycle_diagnostic(row) is None:
                gaps["preadjudication_terminal_unresolved"] += 1
                continue
            attempt = row.get("evaluation_attempt_id")
            producer = rejected_identity
            action = None
            stops["native_signal_invalidated_before_provider"] += 1
        else:
            context = mapping(observation.get("label_context"))
            receipt = mapping(observation.get("runtime_consumption"))
            expected_native = mapping(receipt.get("continuous_reversal"))
            attempt, producer = context.get("evaluation_attempt_id"), identity(
                receipt, native=True
            )
            noncall_source_guard = (
                not expected_native
                and not native
                and row.get("provider_called") is False
                and row.get("machine_bundle_sha256") == observation.get("bundle_sha256")
                and str(row.get("entry_mechanistic_action")).upper()
                == str(observation["source"]["assessment"].get("action")).upper()
            )
            if (
                row.get("schema") != "ai_decision_trace_v1"
                or not attempt
                or row.get("evaluation_attempt_id") != attempt
                or not valid_identity(producer)
                or any(identity(row))
                and identity(row) != producer
                or not noncall_source_guard
                and (
                    identity(native, native=True) != producer
                    or any(
                        native.get(field) != expected_native.get(field)
                        for field in (
                            "family_sha256",
                            "bundle_sha256",
                            "input_sha256",
                            "prompt_sha256",
                        )
                    )
                )
            ):
                issues["reversal_trace_observation_binding_invalid"] += 1
                continue
            action = str(observation["source"]["assessment"].get("action")).upper()
            observed_trace_keys.add(key)
        request_id = row.get("request_id")
        if not isinstance(request_id, str):
            request_id = None
        request = request_index.get(request_id)
        request_valid = False
        if request is not None:
            binding = mapping(request.get("continuous_reversal_request_binding"))
            bound_native = mapping(binding.get("continuous_reversal_consumption"))
            # Synchronous Main calls have no async envelope. Their immutable
            # machine observation, native PID and exact request hashes own the
            # join; never invent an async id or join by symbol/time alone.
            synchronous_identity = (
                not any(identity(request) + identity(row))
                and request.get("async_request_id") is None
                and row.get("async_request_id") is None
                and binding.get("binding_status") == "matched"
                and binding.get("request_id") == request_id
                and binding.get("machine_observation_sha256") == key
                and identity(bound_native, native=True) == producer
                and valid_identity(producer)
                and all(
                    bound_native.get(field) == native.get(field)
                    for field in (
                        "family_sha256",
                        "bundle_sha256",
                        "input_sha256",
                        "prompt_sha256",
                    )
                )
            )
            asynchronous_identity = (
                identity(request) == identity(row) == producer
                and bool(request.get("async_request_id"))
                and request.get("async_request_id") == row.get("async_request_id")
            )
            request_valid = (
                request.get("schema") == "ai_decision_request_provenance_v1"
                and request.get("endpoint") == "analyze_target"
                and (asynchronous_identity or synchronous_identity)
                and all(
                    digest(request.get(field)) and request.get(field) == row.get(field)
                    for field in ("prompt_sha256", "request_envelope_sha256")
                )
                and digest(request.get("sanitized_user_input_sha256"))
                and request.get("sanitized_user_input_sha256")
                == row.get("payload_semantic_sha256")
                and digest(native.get("input_sha256"))
                and native.get("input_sha256")
                == request.get(
                    "sanitized_replay_context_sha256",
                    request.get("sanitized_user_input_sha256"),
                )
            )
            request_at, trace_at = stamp(request.get("captured_at")), stamp(
                row.get("decision_ts")
            )
            observation_at = (
                stamp(observation.get("captured_at"))
                if observation is not None
                else None
            )
            request_valid = (
                request_valid
                and request_at is not None
                and trace_at is not None
                and (
                    request_at <= trace_at
                    and (observation_at is None or observation_at <= request_at)
                )
            )
            binding = request.get("continuous_reversal_request_binding")
            if isinstance(binding, dict):
                request_valid = (
                    request_valid
                    and binding.get("binding_status") == "matched"
                    and binding.get("machine_observation_sha256") == key
                )
            if not request_valid:
                issues["reversal_provider_request_hash_or_identity_mismatch"] += 1
            else:
                prepared.add(key)
                matched_requests.add(request_id)
                if action != "ENTER_NOW":
                    issues["reversal_provider_request_after_nonentry"] += 1
        raw = row.get("entry_ai_raw_risk_verdict")
        recognized_raw = isinstance(raw, str) and raw in {"PASS", "CAUTION", "VETO"}
        response = (
            bool(row.get("provider_response_id"))
            and digest(row.get("response_sha256"))
            and row.get("provider_called") is True
        )
        http_attempt_count = mapping(row.get("transport_timing")).get(
            "openai_http_attempt_count"
        )
        transmitted_fact = row.get("provider_called") is True and (
            response
            or (type(http_attempt_count) in (int, float) and http_attempt_count > 0)
        )
        if transmitted_fact:
            transmitted.add(trace_id)
            if not request_valid and not response:
                gaps["transmission_request_unresolved"] += 1
        if response:
            responded.add(trace_id)
            raw_verdicts[raw if recognized_raw else "UNRECOGNIZED"] += 1
            if not recognized_raw:
                gaps["raw_response_verdict_unrecognized"] += 1
            if not request_valid:
                gaps["response_request_unresolved"] += 1
            if (
                row.get("entry_ai_raw_fields_source") != "decoded_provider_response"
                or not digest(row.get("entry_ai_raw_response_sha256"))
                or row.get("entry_ai_raw_fields_truncated") is not False
                or bool(row.get("entry_ai_raw_fields_invalid_shape"))
                or not isinstance(row.get("entry_ai_raw_fields_present"), dict)
                or not all(
                    isinstance(row.get("entry_ai_raw_" + field), list)
                    for field in (
                        "risk_codes",
                        "supporting_fact_ids",
                        "contradicting_fact_ids",
                    )
                )
                or not all(
                    row["entry_ai_raw_fields_present"].get(field) is True
                    for field in (
                        "risk_verdict",
                        "risk_codes",
                        "supporting_fact_ids",
                        "contradicting_fact_ids",
                    )
                )
            ):
                gaps["raw_response_evidence_arrays_unverified"] += 1
            if row.get("entry_auxiliary_response_contract_valid") is True:
                valid_response.add(trace_id)
                if raw == "PASS":
                    valid_pass.add(trace_id)
                    if (
                        row.get("entry_post_response_execution_valid") is True
                        and row.get("entry_ai_screen_status") == "pass"
                    ):
                        effective_pass.add(trace_id)
            elif row.get("entry_auxiliary_response_contract_valid") is not False:
                gaps["response_validation_unobservable"] += 1
        if row.get("timeout") is True and transmitted_fact and not response:
            timeouts.add(trace_id)
        execution_errors = row.get("entry_ai_contract_errors")
        execution_errors = (
            execution_errors if isinstance(execution_errors, list) else []
        )
        reason = (
            row.get("machine_contract_error")
            or (
                row.get("reason")
                if str(row.get("reason")).startswith("reversal_signal_")
                else None
            )
            or next(
                (
                    error
                    for error in execution_errors
                    if isinstance(error, str) and error.startswith("reversal_signal_")
                ),
                None,
            )
            or row.get("entry_ai_screen_status")
        )
        if action == "SOURCE_INVALID":
            stops[
                "input_"
                + str(
                    row.get("entry_source_invalid_primary_blocker") or "source_invalid"
                )
            ] += 1
        elif action == "ENTER_NOW":
            if row.get("timeout") is True and transmitted_fact:
                stops[
                    (
                        "original_budget_transport_timeout"
                        if mapping(row.get("transport_timing")).get(
                            "openai_http_timeout_budget_exhausted"
                        )
                        is True
                        else "provider_transport_timeout"
                    )
                ] += 1
            elif (
                response and row.get("entry_auxiliary_response_contract_valid") is False
            ):
                stops["auxiliary_response_contract_invalid"] += 1
            elif response and recognized_raw and raw in {"CAUTION", "VETO"}:
                stops["auxiliary_" + raw.lower()] += 1
            elif (
                response
                and raw == "PASS"
                and row.get("entry_auxiliary_response_contract_valid") is True
                and row.get("entry_post_response_execution_valid") is False
            ):
                stops[
                    (
                        "native_signal_invalidated_after_valid_auxiliary_pass"
                        if str(reason).startswith("reversal_signal_")
                        else "post_response_execution_invalid"
                    )
                ] += 1
            elif not transmitted_fact and reason:
                noncall[str(reason)] += 1
                stops[
                    (
                        "native_signal_invalidated_before_provider"
                        if str(reason).startswith("reversal_signal_")
                        else "noncall_" + str(reason)
                    )
                ] += 1
        attempt_ledger.append(
            dict(
                evaluation_attempt_id=attempt,
                machine_observation_sha256=key,
                producer_pid=producer[0],
                producer_start_ticks=producer[1],
                decision_trace_id=trace_id,
                machine_bundle_sha256=(
                    observation.get("bundle_sha256")
                    if observation is not None
                    else row.get("machine_bundle_sha256")
                ),
                effective_venue=(
                    mapping(observation.get("label_context")).get("effective_venue")
                    if observation is not None
                    else row.get("effective_venue")
                ),
                session_bucket=(
                    mapping(observation.get("label_context")).get("session_bucket")
                    if observation is not None
                    else row.get("session_bucket")
                ),
                market_data_route=(
                    mapping(observation.get("label_context")).get("market_data_route")
                    if observation is not None
                    else row.get("market_data_route")
                ),
                request_id=request_id,
                machine_action=action,
                request_prepared=request_valid,
                transmission_attempt_observed=transmitted_fact,
                raw_response_observed=response,
                raw_verdict=raw,
                auxiliary_response_contract_valid=row.get(
                    "entry_auxiliary_response_contract_valid"
                ),
                post_response_execution_valid=row.get(
                    "entry_post_response_execution_valid"
                ),
                effective_screen_status=row.get("entry_ai_screen_status"),
                timeout=row.get("timeout") is True,
                execution_errors=[str(error)[:512] for error in execution_errors[:64]],
                trace_decision_ts=row.get("decision_ts"),
                main_commit_assessed=False,
            )
        )
        if observation is None:
            # Preserve the native pre-assessment terminal proof. No machine
            # observation or provider request exists for this rejected claim.
            attempt_ledger[-1]["native_preassessment_terminal"] = {
                name: row.get(name)
                for name in (
                    "continuous_reversal_rejected_claim_receipt",
                    "provider_called",
                    "actual_order_submitted",
                    "evaluation_attempt_id",
                    "machine_bundle_sha256",
                    "machine_contract_error",
                    "decision_ts",
                    "decision_trace_id",
                    "stock_code",
                    "market_data_route",
                )
            }
    by_producer = {}
    for row in attempt_ledger:
        counts = by_producer.setdefault(
            row["producer_pid"] + ":" + row["producer_start_ticks"],
            dict(
                trace_attempt_count=0,
                request_prepared_count=0,
                raw_response_observed_count=0,
                provider_transmission_attempt_count=0,
                provider_timeout_count=0,
            ),
        )
        counts["trace_attempt_count"] += 1
        counts["request_prepared_count"] += int(row["request_prepared"])
        counts["raw_response_observed_count"] += int(row["raw_response_observed"])
        counts["provider_transmission_attempt_count"] += int(
            row["transmission_attempt_observed"]
        )
        counts["provider_timeout_count"] += int(
            row["timeout"] and row["transmission_attempt_observed"]
        )
    for request_id, row in request_index.items():
        if (
            request_id not in matched_requests
            and identity(row) in producers
            and row.get("endpoint") == "analyze_target"
        ):
            gaps["request_unresolved"] += 1
    missing_trace = len(set(cohort) - observed_trace_keys)
    if missing_trace:
        gaps["observation_trace_unresolved"] += missing_trace
    partial = bool(gaps) or any(
        source.get("status") != "complete" for source in (requests, traces)
    )
    attempt_identities = [
        (row["producer_pid"], row["producer_start_ticks"], row["evaluation_attempt_id"])
        for row in attempt_ledger
    ]
    if len(attempt_identities) != len(set(attempt_identities)):
        issues["reversal_attempt_trace_conflict"] += len(attempt_identities) - len(
            set(attempt_identities)
        )
    result = dict(
        status=(
            "review_required"
            if issues
            else (
                "partial_source_gap"
                if partial
                else "observed" if cohort or prepared or responded else "not_observed"
            )
        ),
        metric_role="funnel_count",
        decision_authority="report_only",
        window_policy="exact_observation_cohort_pid_start_attempt_hash_with_five_second_carry_in",
        sample_floor="none_for_counts",
        primary_decision_metric="exact_attempt_join_gap_count",
        source_quality_gate="bounded_complete_source_exact_pid_attempt_and_content_hashes",
        forbidden_uses=["order_authority", "policy_promotion", "missing_as_zero_ev"],
        observation_window_seconds=window_sec,
        machine_observation_count=len(cohort),
        by_producer=by_producer,
        exact_pid_filter=(
            list(map(str, pid_identity)) if pid_identity is not None else None
        ),
        trace_attempt_count=len(set(attempt_identities)),
        request_prepared_count=len(matched_requests),
        provider_transmission_attempt_count=len(transmitted),
        raw_response_observed_count=len(responded),
        raw_verdict_counts=dict(raw_verdicts),
        auxiliary_response_contract_valid_count=len(valid_response),
        raw_pass_count=raw_verdicts.get("PASS", 0),
        valid_pass_count=len(valid_pass),
        execution_valid_pass_count=len(effective_pass),
        provider_timeout_count=len(timeouts),
        enter_without_request_observed=sum(
            str(row["source"]["assessment"].get("action")).upper() == "ENTER_NOW"
            and key not in prepared
            for key, row in cohort.items()
        ),
        first_stop_counts=dict(stops),
        noncall_reasons=dict(noncall),
        issues=dict(issues),
        exact_attempt_join_gap_count=sum(gaps.values()),
        source_gaps=dict(gaps),
        source_windows=dict(requests=requests, traces=traces),
        attempt_ledger=attempt_ledger[-1024:],
        provider_called_metadata_used_as_fact=False,
        observation_provider_called_metadata_used_as_fact=False,
        actual_order_submitted_assessed=False,
    )
    actor = _HEALTH_ACTOR.get()
    if actor and _loaded is None:
        view = _reversal_provider_lineage(
            data_root,
            now,
            observations,
            tail_bytes=tail_bytes,
            window_sec=SOURCE_WINDOW_SEC,
            pid_identity=actor,
            _loaded=(request_rows, requests, trace_rows, traces),
        )
        view["current_pid_coverage"] = "exact_live_pid"
        result["current_health_cohort"] = _health_cohort(
            view,
            actor,
            now,
            excluded=max(0, len(cohort) - view["machine_observation_count"]),
        )
    return result


def _auxiliary_cost_receipt_valid(row):
    cost = row.get("entry_conservative_execution_cost_pct")
    return (
        row.get("entry_cost_source_status") == "exact_pre_provider_replay"
        and type(cost) in (int, float)
        and math.isfinite(cost)
        and cost >= 0
        and row.get("entry_cost_evaluation_attempt_id")
        == row.get("evaluation_attempt_id")
        and bool(row.get("evaluation_attempt_id"))
        and row.get("entry_cost_scope") == "counterfactual_friction_no_broker_fees"
        and row.get("entry_cost_basis") == "half_spread_plus_bounded_source_age_penalty"
        and all(
            isinstance(row.get(name), str)
            and len(row[name]) == 64
            and all(char in "0123456789abcdef" for char in row[name])
            for name in (
                "entry_cost_contract_sha256",
                "entry_cost_replay_context_sha256",
            )
        )
    )


def _observer_lifecycle_diagnostic(row, receipt):
    """Prove an exact native invalidation; a removed ready alone proves nothing."""
    try:
        from src.engine.scalping.continuous_reversal import good_quote
        from src.engine.scalping.reversal_extended_catalog import cell_key
        from src.engine.scalping.entry_machine_source_recovery import _digest

        root = receipt["original_root"]
        selection = receipt["native_selection"]
        life = selection["original_signal_lifecycle"]
        latest = life["latest_native_observation"]
        at, ended = receipt["observed_epoch"], life["first_ineligible_seen"]
        trace_at = stamp(row["decision_ts"]).timestamp()
        family, bundle = receipt["family_sha256"], receipt["machine_bundle_sha256"]
        actor = [str(receipt[k]) for k in ("process_pid", "process_start_ticks")]
        scope = life["scope"]
        branches, floors = root["branch_signals"], life["branch_hold_floors"]
        route = {
            "KRX": ("", "krx_only"),
            "NXT": ("_NX", "nxt_only"),
            "SOR": ("_AL", "krx_nxt_integrated"),
        }[root["venue"]]
        if (
            not all(
                type(v) in (int, float) and math.isfinite(v) and v > 0
                for v in (
                    at,
                    ended,
                    root["epoch"],
                    latest[0],
                    latest[3],
                    latest[4],
                    latest[5],
                )
            )
            or not all(
                type(v) is int and v >= 0
                for v in (
                    root["native_epoch"],
                    root["native_sequence"],
                    latest[1],
                    latest[2],
                    selection["native_sequence"],
                )
            )
            or receipt["status"] != "observed"
            or receipt["sha256"]
            != _digest({k: v for k, v in receipt.items() if k != "sha256"})
            or not all(
                re.fullmatch("[0-9a-f]{64}", str(v))
                for v in (family, bundle, root["registry_generation"])
            )
            or receipt["failure_cause"] != row.get("machine_contract_error")
            or receipt["failure_cause"]
            != "machine_source_quote_observer_native_root_changed"
            or not row.get("evaluation_attempt_id")
            or receipt["evaluation_attempt_id"] != row["evaluation_attempt_id"]
            or bundle != row.get("machine_bundle_sha256")
            or life["bundle_sha256"] != bundle
            or row.get("provider_called") is not False
            or row.get("actual_order_submitted") is True
            or any(
                receipt.get(k) is not False
                for k in (
                    "runtime_effect",
                    "allowed_runtime_apply",
                    "actual_order_submitted",
                )
            )
            or receipt.get("broker_order_forbidden") is not True
            or not all(v.isdigit() and int(v) > 0 for v in actor)
            or any(
                [str(r.get(k)) for k in ("process_pid", "process_start_ticks")] != actor
                for r in (selection, life)
            )
            or (_row_actor(row) is not None and _row_actor(row) != actor)
            or root["symbol"] != row.get("stock_code")
            or root["source_item"] != root["symbol"] + route[0]
            or row.get("market_data_route") != route[1]
            or scope[:4]
            != [root["symbol"], root["venue"], root["source_item"], root["market"]]
            or scope[4] != stamp(row["decision_ts"]).date().isoformat()
            or scope[5]
            != cell_key(root["symbol"], root["market"], root["confirmation_price"])
            or selection["selected_scope"] != scope[5]
            or life["scope_execution_hash"] != root["registry_generation"]
            or selection["scope_execution_hash"] != root["registry_generation"]
            or selection["family_sha256"] != family
            or life["family_sha256"] != family
            or selection["item"] != root["source_item"]
            or selection["venue"] != root["venue"]
            or selection["observed_epoch"] != at
            or selection["native_source_current"] is not True
            or selection["native_quote_current"] is not True
            or selection["native_epoch"] != root["native_epoch"]
            or not 0 <= at - selection["native_last_received_epoch"] <= 3
            or selection["native_sequence"] < latest[2]
            or not root["epoch"]
            <= life["first_eligible_seen"]
            <= life["last_eligible_seen"]
            <= ended
            <= at
            <= trace_at
            or not at
            < receipt["original_deadline_epoch"]
            == life["original_deadline"]
            == root["epoch"] + 5
            or trace_at - at > 5
            or latest[0] != ended
            or not good_quote(latest)
            or latest[1] != root["native_epoch"]
            or latest[2] <= root["native_sequence"]
            or latest[9] != root["source_item"]
            or life["native_epoch"] != root["native_epoch"]
            or life["native_sequence"] != root["native_sequence"]
            or life["native_event_id"] != root["event_id"]
            or life["signal_id"] != root["signal_id"]
            or life["epoch"] != root["epoch"]
            or life["continuous_ingress"] is not True
            or life["claimed"] is not False
            or life["selector_claimed"] is not False
            or life["terminal"]
            not in {"invalidated_before_claim", "replaced_before_claim"}
            or life["ready_membership_present"] is not False
            or not branches
            or set(branches) != set(life["branch_survival"])
            or any(life["branch_survival"][bid] is not False for bid in branches)
        ):
            return None
        if life["terminal_reason"] == "first_price_hold_breached":
            if (
                not life["first_eligible_seen"] < ended
                or set(branches) != set(floors)
                or any(
                    signal["decision_phase"] != "FIRST_PRICE_HOLD"
                    or type(floors[bid]) not in (int, float)
                    or not math.isfinite(floors[bid])
                    or not 0
                    < latest[3]
                    < floors[bid]
                    == signal["signal_proof"]["price"]
                    for bid, signal in branches.items()
                )
            ):
                return None
            diagnostic = "reversal_first_price_hold_invalidated"
        elif life["terminal_reason"] == "first_turn_invalidated":
            # Native callbacks in one batch may share a receive timestamp.
            # The terminal's advancing sequence, continuous ingress and exact
            # original FIRST anchors prove order without inventing a clock gap.
            if (
                floors
                or not life["first_eligible_seen"] < ended
                or type(root["confirmation_price"]) not in (int, float)
                or set(life["branch_membership"]) != set(branches)
                or any(
                    signal["decision_phase"] != "FIRST_UPTICK"
                    or life["branch_membership"][bid] != root["event_id"]
                    or any(
                        type(signal.get(k)) is not int
                        for k in ("native_epoch", "native_sequence")
                    )
                    or any(
                        signal.get(k) != root[k]
                        for k in (
                            "event_id",
                            "signal_id",
                            "epoch",
                            "native_epoch",
                            "native_sequence",
                            "source_item",
                        )
                    )
                    or type(signal.get("confirmation_price")) not in (int, float)
                    or not math.isfinite(signal["confirmation_price"])
                    or not 0
                    < latest[3]
                    < signal["confirmation_price"]
                    == root["confirmation_price"]
                    for bid, signal in branches.items()
                )
            ):
                return None
            diagnostic = "reversal_first_signal_invalidated"
        else:
            return None
        for pid_key, start_key in (
            ("async_producer_pid", "async_producer_start_ticks"),
            ("process_pid", "process_start_ticks"),
            ("pid", "process_start_ticks"),
        ):
            if (
                any(row.get(k) is not None for k in (pid_key, start_key))
                and [str(row.get(k)) for k in (pid_key, start_key)] != actor
            ):
                return None
        if row.get("stage") == "zero_base_probe_result":
            fields = row["fields"]
            reference = fields["native_observation_reference"]
            if isinstance(reference, str):
                if len(reference) > 65536:
                    return None
                try:
                    reference = json.loads(reference)
                except ValueError:
                    reference = ast.literal_eval(reference)
            if str(fields["zero_base_producer_pid"]) != actor[0]:
                return None
            if reference == {}:
                # Issued rejected probes lost the redundant observer reference.
                # Their original same-lock native selection is already retained;
                # prove its exact root/actor/deadline, never fill the old record.
                original = fields["native_observation_receipt"]
                if isinstance(original, str):
                    if len(original) > 65536:
                        return None
                    try:
                        original = json.loads(original)
                    except ValueError:
                        original = ast.literal_eval(original)
                if (
                    original["schema"] != "native_observation_selection_v1"
                    or original["evaluation_role"] != "probe_observation"
                    or original["reason"] != "ready"
                    or original["runtime_effect"] is not False
                    or [
                        str(original.get(k))
                        for k in ("process_pid", "process_start_ticks")
                    ]
                    != actor
                    or original["family_sha256"] != family
                    or original["scope_execution_hash"] != root["registry_generation"]
                    or original["selected_scope"] != scope[5]
                    or original["item"] != root["source_item"]
                    or original["venue"] != root["venue"]
                    or original["native_event_id"] != root["event_id"]
                    or original["signal_id"] != root["signal_id"]
                    or type(original["selected_ready_count"]) is not int
                    or original["selected_ready_count"] < 1
                    or type(original["raw_ready_count"]) is not int
                    or original["raw_ready_count"] < original["selected_ready_count"]
                    or any(
                        type(original.get(k)) is not int or original[k] != root[k]
                        for k in ("native_epoch", "native_sequence")
                    )
                    or not root["epoch"] <= original["observed_epoch"] <= ended
                    or original["native_deadline_epoch"]
                    != receipt["original_deadline_epoch"]
                    or any(
                        original["selected_branch_truth"].get(bid) != "TRUE"
                        for bid in branches
                    )
                    or original["native_source_current"] is not True
                    or original["native_quote_current"] is not True
                ):
                    return None
            elif (
                [
                    str(reference.get(k))
                    for k in ("observer_pid", "observer_start_ticks")
                ]
                != actor
                or reference["family_sha256"] != family
                or reference["deadline_epoch"] != receipt["original_deadline_epoch"]
            ):
                return None
        current = receipt.get("current_root")
        if current is not None and (
            current.get("signal_id") == root["signal_id"]
            or any(
                current.get(k) != root[k]
                for k in (
                    "symbol",
                    "venue",
                    "market",
                    "source_item",
                    "native_epoch",
                    "registry_generation",
                )
            )
            or not root["native_sequence"]
            < current["native_sequence"]
            <= selection["native_sequence"]
            or not root["epoch"] < current["epoch"] <= at
        ):
            return None
        return diagnostic
    except (
        KeyError,
        TypeError,
        ValueError,
        SyntaxError,
        IndexError,
        AttributeError,
        OverflowError,
    ):
        return None


def _reversal_lifecycle_diagnostic(row):
    """Only exact, intact rejection evidence can classify a normal lifecycle miss."""
    receipt = row.get("continuous_reversal_rejected_claim_receipt")
    if (
        isinstance(receipt, dict)
        and receipt.get("schema") == "entry_source_quote_observer_rejection_v1"
    ):
        return _observer_lifecycle_diagnostic(row, receipt)
    if (
        row.get("provider_called") is not False
        or row.get("actual_order_submitted") is True
        or not isinstance(receipt, dict)
        or receipt.get("status") != "observed"
        or receipt.get("schema")
        not in {
            "continuous_reversal_claim_source_receipt_v1",
            "continuous_reversal_claim_source_receipt_v2",
            "continuous_reversal_claim_source_receipt_v3",
            "continuous_reversal_claim_source_receipt_v4",
        }
        or not row.get("evaluation_attempt_id")
        or receipt.get("evaluation_attempt_id") != row.get("evaluation_attempt_id")
        or not row.get("machine_bundle_sha256")
        or receipt.get("machine_bundle_sha256") != row.get("machine_bundle_sha256")
        or receipt.get("validation_error") != row.get("machine_contract_error")
    ):
        return None
    try:
        registration = receipt.get("source_registration_receipt")
        if (
            receipt.get("claim_token") == "[REDACTED]"
            and isinstance(registration, dict)
            and registration.get("claim_token") == "[REDACTED]"
        ):
            # Older trace writers masked this public content digest. Rebuild it
            # only on local copies and require the original registration hash;
            # no source bytes, native claim or order authority are changed.
            from src.engine.scalping.reversal_source_diagnostics import (
                verified_registration,
            )

            snap = receipt["supplied_snapshot"]
            token = hashlib.sha256(
                json.dumps(
                    [receipt["claim_generation"], snap[0]["signal_id"], snap],
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                    allow_nan=False,
                ).encode()
            ).hexdigest()
            proof = dict(registration, claim_token=token)
            if not verified_registration(
                dict(
                    token=token,
                    generation=receipt["claim_generation"],
                    snapshot=snap,
                    backend=receipt.get("claim_backend"),
                ),
                proof,
            ):
                return None
            receipt = dict(
                receipt, claim_token=token, source_registration_receipt=proof
            )
        snapshot = receipt["snapshot"]
        generation = receipt["stored_generation"]
        expired_registration = False
        if (
            receipt["schema"] == "continuous_reversal_claim_source_receipt_v3"
            and receipt.get("registered_claim_present") is False
        ):
            from src.engine.scalping.reversal_source_diagnostics import (
                verified_registration,
            )

            proof = verified_registration(
                dict(
                    token=receipt["claim_token"],
                    generation=receipt["claim_generation"],
                    snapshot=receipt["supplied_snapshot"],
                    backend=receipt.get("claim_backend"),
                ),
                receipt.get("source_registration_receipt"),
            )
            if (
                not proof
                or snapshot is not None
                or generation is not None
                or receipt["scope"] != proof["scope"]
                or receipt["active_generation"] != receipt["requested_family_sha256"]
                or receipt["validation_epoch"] < proof["observed_epoch"]
                or row["machine_contract_error"] != "reversal_signal_generation_changed"
                or receipt.get("failure_cause") != "reversal_signal_expired"
            ):
                return None
            snapshot, generation = proof["snapshot"], proof["generation"]
            expired_registration = True
        event = snapshot[0]
        scope = receipt["scope"]
        latest = receipt["latest_native_observation"]
        at = receipt["validation_epoch"]
        observed_at = (
            receipt["state_observed_epoch"]
            if receipt["schema"] != "continuous_reversal_claim_source_receipt_v1"
            else at
        )
        age = at - event["epoch"]
        family = receipt["requested_family_sha256"]
        operating = receipt["schema"] == "continuous_reversal_claim_source_receipt_v4"
        if operating:
            from src.engine.scalping.reversal_source_diagnostics import (
                verified_registration,
            )
            from src.engine.scalping.continuous_reversal import good_quote

            proof = verified_registration(
                dict(
                    token=receipt["claim_token"],
                    generation=receipt["claim_generation"],
                    snapshot=receipt["supplied_snapshot"],
                    backend=receipt.get("claim_backend"),
                ),
                receipt.get("source_registration_receipt"),
            )
            if (
                receipt.get("claim_backend") not in {"operating_v5", "operating_v6"}
                or receipt.get("registered_claim_present") is not True
                or not proof
                or scope != proof["scope"]
                or family != receipt.get("active_generation")
                or family != receipt.get("stored_envelope_family_sha256")
                or generation != receipt.get("state_generation")
                or generation != receipt.get("active_scope_execution_hash")
                or generation != event.get("registry_generation")
                or at < proof["observed_epoch"]
                or not good_quote(latest)
            ):
                return None
        encoded = json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
        snapshot_sha = hashlib.sha256(encoded).hexdigest()
        token = hashlib.sha256(
            json.dumps(
                [generation, event["signal_id"], snapshot],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        trace_at = stamp(row["decision_ts"]).timestamp()
        route = {
            "KRX": ("", "krx_only"),
            "NXT": ("_NX", "nxt_only"),
            "SOR": ("_AL", "krx_nxt_integrated"),
        }.get(scope[1])
        if (
            (not operating and family != generation)
            or generation != receipt["claim_generation"]
            or (not expired_registration and snapshot_sha != receipt["snapshot_sha256"])
            or snapshot_sha != receipt["supplied_snapshot_sha256"]
            or token != receipt["claim_token"]
            or age != receipt["signal_age_seconds"]
            or scope[0] != row.get("stock_code")
            or scope[2] != event["source_item"]
            or route is None
            or scope[2] != str(scope[0]) + route[0]
            or row.get("market_data_route") != route[1]
            or latest[9] != scope[2]
            or not latest[8]
            or str(latest[1]) != event["event_id"].rsplit(":", 2)[-2]
            or latest[2] < int(event["event_id"].rsplit(":", 1)[-1])
            or not receipt["price_path_segment_start"] < event["epoch"]
            or not 0 <= observed_at - at <= 5
            or not 0 <= observed_at - latest[0] <= 5
            or not 0 <= trace_at - observed_at <= 5
            or not 0 <= trace_at - at <= 5
        ):
            return None
        cause = receipt.get("failure_cause")
        if (
            operating
            and cause == row["machine_contract_error"] == "reversal_signal_path_changed"
            and 0 <= age <= 5
            and receipt.get("registered_signal_ready") is False
            and event.get("decision_phase") == "FIRST_PRICE_HOLD"
            and event.get("branch_signals")
            and latest[0] > event["epoch"]
            and latest[2] > event["native_sequence"]
        ):
            # The registered-claim path uses the same native held-price owner
            # as the earlier quote-observer path. Prove every branch's actual
            # floor breach; absent ready membership alone is never sufficient.
            from src.engine.scalping.reversal_extended_auxiliary import validate_signal
            from src.engine.scalping.reversal_cumulative_runtime import hold_breached
            from src.engine.scalping.continuous_reversal import connected, good_quote
            from src.engine.scalping.continuous_reversal_postclose import digest

            expected = dict(
                native_state_present=True,
                legacy_last_present=True,
                latest_source_valid=True,
                native_epoch_matches=True,
                first_signal_turn_matches=None,
                scope_generation_matches=True,
                ready_membership_present=False,
            )
            predicates = receipt.get("native_predicates")
            if (
                isinstance(predicates, dict)
                and set(expected) <= set(predicates)
                and all(predicates[k] is v for k, v in expected.items())
                and receipt.get("failed_native_predicates")
                == ["ready_membership_present"]
            ):
                branches = event["branch_signals"]
                first = receipt.get("first_signal_invalidation")
                if "first_signal_invalidation" in receipt and not isinstance(first, dict):
                    return None
                if first is not None:
                    # The native owner retains the actual first breach. A
                    # later recovery cannot restore this claim or erase its
                    # diagnostic cause. No history is inferred from absence.
                    actor = [str(first["pid"]), str(first["process_start_ticks"])]
                    if (
                        first.get("schema") != "native_first_signal_invalidation_v1"
                        or first.get("sha256") != digest({
                            k: v for k, v in first.items() if k != "sha256"
                        })
                        or any(first.get(k) != event[k] for k in (
                            "signal_id", "event_id", "symbol", "venue", "market",
                            "source_item", "native_epoch", "native_sequence", "epoch",
                            "registry_generation",
                        ))
                        or first.get("original_deadline") != event["epoch"] + 5
                        or set(first["branches"]) != set(branches)
                        or not all(v.isdigit() and int(v) > 0 for v in actor)
                        or actor != [str(receipt.get(k)) for k in (
                            "process_pid", "process_start_ticks"
                        )]
                        or _row_actor(row) != actor
                        or _row_actor(first) != actor
                        or any(first.get(k) is not False for k in (
                            "runtime_effect", "allowed_runtime_apply", "actual_order_submitted"
                        ))
                        or first.get("broker_order_forbidden") is not True
                    ):
                        return None
                for bid, signal in branches.items():
                    validate_signal(signal)
                    breach = latest
                    if first is not None:
                        record = first["branches"][bid]
                        breach, previous = record["observation"], record["previous_observation"]
                        if (
                            record.get("reason") != "first_price_hold_breached"
                            or record.get("branch_definition_sha256") != signal["branch_definition_sha256"]
                            or record.get("signal_proof_sha256") != digest(signal["signal_proof"])
                            or len(breach) != 11 or len(previous) != 11
                            or not connected(previous, breach)
                            or not good_quote(previous) or not good_quote(breach)
                            or not all(
                                type(tick[i]) is int
                                for tick in (previous, breach) for i in (1, 2, 8)
                            )
                            or not all(
                                type(tick[i]) in (int, float)
                                and math.isfinite(tick[i]) and tick[i] > 0
                                for tick in (previous, breach) for i in (0, 3, 4, 5)
                            )
                            or previous[8] != 1 or breach[8] != 1
                            or previous[9] != event["source_item"]
                            or breach[9] != event["source_item"]
                            or breach[1] != event["native_epoch"]
                            or not event["native_sequence"] <= previous[2] < breach[2] <= latest[2]
                            or not event["epoch"] <= previous[0] <= breach[0] <= latest[0]
                            or hold_breached(signal, previous)
                        ):
                            break
                    if (
                        signal.get("extended_definition_id") != bid
                        or signal.get("decision_phase") != "FIRST_PRICE_HOLD"
                        or any(
                            signal.get(k) != event[k]
                            for k in (
                                "symbol",
                                "venue",
                                "market",
                                "source_item",
                                "event_id",
                                "signal_id",
                                "epoch",
                                "native_epoch",
                                "native_sequence",
                                "registry_generation",
                            )
                        )
                        or not hold_breached(signal, breach)
                    ):
                        break
                else:
                    return "reversal_first_price_hold_invalidated"
        if (
            operating
            and cause == row["machine_contract_error"] == "reversal_signal_path_changed"
            and 0 <= age <= 5
            and receipt.get("registered_signal_ready") is False
            and event.get("decision_phase") == "FIRST_UPTICK"
            and event.get("branch_signals")
            and all(
                s.get("decision_phase") == "FIRST_UPTICK"
                for s in event["branch_signals"].values()
            )
            and latest[0] > event["epoch"]
        ):
            # The native FIRST owner also retires an anchor when another turn
            # replaces it, or a retreat ends it at/above the original price.
            # Require same-lock state predicates; a missing ready row alone is not
            # evidence of an ordinary lifecycle transition.
            expected = dict(
                native_state_present=True,
                legacy_last_present=True,
                latest_source_valid=True,
                native_epoch_matches=True,
                first_signal_turn_matches=False,
                scope_generation_matches=True,
                ready_membership_present=False,
            )
            predicates = receipt.get("native_predicates")
            turn = receipt.get("current_turn_id")
            valid_turn = turn is None
            if isinstance(turn, str):
                prefix, sequence = turn.rsplit(":", 1)
                old_prefix, old_sequence = event["event_id"].rsplit(":", 1)
                valid_turn = (
                    prefix == old_prefix
                    and sequence.isdecimal()
                    and int(old_sequence) < int(sequence) <= latest[2]
                )
            if (
                isinstance(predicates, dict)
                and all(predicates.get(k) is v for k, v in expected.items())
                and latest[2] > event["native_sequence"]
                and valid_turn
            ):
                return "reversal_first_signal_invalidated"
        if (
            cause == "reversal_signal_expired"
            and age > 5
            and (
                row["machine_contract_error"] == "reversal_signal_expired_or_changed"
                or expired_registration
            )
        ):
            return cause
        if (
            cause == "reversal_first_signal_invalidated"
            and 0 <= age <= 5
            and event.get("decision_phase") == "FIRST_UPTICK"
            and receipt.get("current_turn_id") != event["event_id"]
            and row["machine_contract_error"] == cause
        ):
            return cause
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
        pass
    return None


def _entry_input_deadline_guard(row):
    """A fully identified pre-provider deadline rejection is a latency miss."""
    at = stamp(row.get("decision_ts"))
    captured = stamp(row.get("input_source_clock_captured_at"))
    deadline = row.get("async_origin_deadline_epoch")
    return (
        row.get("schema") == "ai_decision_trace_v1"
        and row.get("decision_stage") == "entry_screen"
        and row.get("machine_evaluation_status") == "assessment_contract_invalid"
        and row.get("machine_contract_error") == "entry_machine_input_deadline_expired"
        and row.get("machine_source_gap_kind")
        in (None, "", "entry_machine_input_deadline_expired")
        and row.get("decision_evaluation_status")
        == "not_evaluated_provider_or_preflight"
        and row.get("result_source") == "mechanistic_pre_adjudication_rejected"
        and row.get("action") == "DROP"
        and row.get("reason") == "mechanistic_input_contract_invalid"
        and all(
            row.get(k) is False
            for k in (
                "provider_called",
                "actual_order_submitted",
                "runtime_effect",
                "allowed_runtime_apply",
            )
        )
        and row.get("broker_order_forbidden") is True
        and row.get("machine_observation_sha256") is None
        and row.get("request_capture_status") == "missing"
        and _row_actor(row) is not None
        and all(
            isinstance(row.get(k), str)
            and 0 < len(row[k]) <= 256
            and row[k].lower() not in {"none", "null", "unknown", "-", "0"}
            for k in (
                "evaluation_attempt_id",
                "decision_trace_id",
                "async_request_id",
                "effective_venue",
                "session_bucket",
                "market_data_route",
            )
        )
        and isinstance(row.get("machine_bundle_sha256"), str)
        and re.fullmatch("[0-9a-f]{64}", row["machine_bundle_sha256"]) is not None
        and type(deadline) in (int, float)
        and math.isfinite(deadline)
        and at is not None
        and captured is not None
        and captured.timestamp() <= deadline <= at.timestamp()
        and 0 <= (at - captured).total_seconds() <= SOURCE_WINDOW_SEC
    )


def _native_preassessment_terminal_valid(row, actor, bundle):
    """Recheck the original rejected claim; missing observations stay missing."""
    proof = row.get("native_preassessment_terminal")
    try:
        if (
            not isinstance(proof, dict)
            or len(json.dumps(proof, allow_nan=False)) > 65536
        ):
            return False
    except (TypeError, ValueError):
        return False
    receipt = proof.get("continuous_reversal_rejected_claim_receipt")
    if not isinstance(receipt, dict):
        return False
    return (
        row.get("machine_observation_sha256") is None
        and row.get("machine_action") is None
        and [str(receipt.get("process_pid")), str(receipt.get("process_start_ticks"))]
        == actor
        and proof.get("machine_bundle_sha256")
        == bundle
        == row.get("machine_bundle_sha256")
        and proof.get("evaluation_attempt_id") == row.get("evaluation_attempt_id")
        and proof.get("decision_trace_id") == row.get("decision_trace_id")
        and proof.get("decision_ts") == row.get("trace_decision_ts")
        and proof.get("market_data_route") == row.get("market_data_route")
        and all(
            row.get(k) is False
            for k in (
                "request_prepared",
                "transmission_attempt_observed",
                "raw_response_observed",
                "timeout",
            )
        )
        and all(
            row.get(k) is None
            for k in (
                "raw_verdict",
                "auxiliary_response_contract_valid",
                "post_response_execution_valid",
                "effective_screen_status",
            )
        )
        and row.get("execution_errors") == []
        and _reversal_lifecycle_diagnostic(proof) is not None
    )


def _probe_identity(row):
    """Use the same native probe identity for census and diagnostic counts."""
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    lease = str(fields.get("physical_probe_lease_id") or "")
    return (
        str(fields.get("zero_base_producer_pid") or ""),
        str(row.get("stock_code")),
        str(fields.get("zero_base_route")),
        (
            lease
            if lease.lower() not in {"", "-", "none", "null"}
            else (
                str(row.get("emitted_at")),
                str(fields.get("zero_base_probe_result") or ""),
                str(fields.get("zero_base_probe_reason") or ""),
            )
        ),
    )


def _probe_verified_no_match(
    row, *, allow_incomplete=False, feature_gap=False, historical=False
):
    """A native FALSE observation proves coverage, never machine/AI acceptance."""
    try:
        fields = row["fields"]
        result = fields.get("zero_base_probe_result")
        allowed = (
            {"required_feature_insufficient"}
            if feature_gap
            else (
                {"observation_incomplete"}
                if allow_incomplete
                else {"required_feature_insufficient", "pattern_not_matched"}
            )
        )
        if (
            feature_gap
            and not allow_incomplete
            or result not in allowed
            or (
                not allow_incomplete
                and fields.get("zero_base_probe_reason")
                not in {
                    "native_observation_residence_exhausted",
                    "native_observation_no_matching_pattern",
                }
            )
            or fields.get("zero_base_ws_wait_reason") != "ready"
        ):
            return False
        receipt = fields.get("native_observation_receipt")
        # Pipeline fields historically serialize dicts as Python literals.
        # Read only this bounded producer field; never evaluate arbitrary code.
        if isinstance(receipt, str):
            if len(receipt) > 8192:
                return False
            try:
                receipt = json.loads(receipt)
            except ValueError:
                receipt = ast.literal_eval(receipt)
        if not isinstance(receipt, dict):
            return False
        # Raw ready rows span price cells; only selected ready rows can refute
        # this cell's no-match. Require the native scope projection when an
        # unselected row exists, rather than treating its count as a failure.
        raw_ready = receipt.get("raw_ready_count")
        if not allow_incomplete and type(raw_ready) is int and raw_ready > 0:
            readiness = fields.get("zero_base_branch_readiness")
            if isinstance(readiness, str):
                if len(readiness) > 65536:
                    return False
                try:
                    readiness = json.loads(readiness)
                except ValueError:
                    readiness = ast.literal_eval(readiness)
            if (
                result != "pattern_not_matched"
                or fields.get("zero_base_probe_result_schema")
                != "zero_base_probe_result_v2"
                or not isinstance(readiness, dict)
                or readiness.get("schema") != "native_branch_residence_requirements_v2"
                or readiness.get("status") != "observed"
                or readiness.get("runtime_effect") is not False
                or readiness.get("decision_authority") != "none"
                or readiness.get("scope_changed") is not False
                or readiness.get("price_basis") != "exact_native_trade"
                or readiness.get("route") != fields.get("zero_base_route")
                or readiness.get("policy_scope") != receipt.get("selected_scope")
                or any(
                    readiness.get(k) != receipt.get(k)
                    for k in (
                        "item",
                        "family_sha256",
                        "scope_execution_hash",
                        "native_epoch",
                        "native_sequence",
                    )
                )
                or not isinstance(readiness.get("branch_descriptors"), dict)
                or {
                    b: d.get("detector_truth") if isinstance(d, dict) else None
                    for b, d in readiness["branch_descriptors"].items()
                }
                != receipt.get("selected_branch_truth")
            ):
                return False
        if result in {"pattern_not_matched", "observation_incomplete"} or feature_gap:
            if not historical and receipt.get("native_source_current") is not True:
                return False
            if not allow_incomplete:
                counts = receipt.get("selected_lifecycle_counts") or {}
                if (
                    not isinstance(counts, dict)
                    or not isinstance(receipt.get("selected_branch_truth"), dict)
                    or set(counts) != set(receipt["selected_branch_truth"])
                    or any(
                        not isinstance(v, dict)
                        or not set(v) <= {"TRUE", "FALSE", "UNKNOWN"}
                        or any(type(n) is not int or n < 0 for n in v.values())
                        for v in counts.values()
                    )
                    or receipt.get("selected_pending_count")
                    or receipt.get("source_censored_count")
                    or any(v.get("TRUE", 0) > 0 for v in counts.values())
                    or any(
                        counts.get(b, {}).get("FALSE", 0) <= 0
                        for b in receipt.get("selected_branch_truth", {})
                    )
                ):
                    return False
        route = fields["zero_base_route"]
        suffix, venue = {
            "krx_only": ("", "KRX"),
            "nxt_only": ("_NX", "NXT"),
            "krx_nxt_integrated": ("_AL", "SOR"),
        }[route]
        code = row["stock_code"]
        truth = receipt.get("selected_branch_truth")
        at = stamp(row.get("emitted_at"))
        epoch = receipt.get("observed_epoch")
        signed_trades = fields.get("zero_base_ws_signed_0b_count")
        return (
            is_canonical_stock_code(code)
            and receipt.get("schema") == "native_observation_selection_v1"
            and receipt.get("evaluation_role") == "probe_observation"
            and receipt.get("runtime_effect") is False
            and (allow_incomplete or receipt.get("reason") == "no_matching_pattern")
            and receipt.get("item") == code + suffix
            and receipt.get("venue") == venue
            and type(receipt.get("process_pid")) is int
            and receipt["process_pid"] > 0
            and str(receipt["process_pid"]) == str(fields.get("zero_base_producer_pid"))
            and str(receipt.get("process_start_ticks") or "").isdigit()
            and int(receipt["process_start_ticks"]) > 0
            and at is not None
            and type(epoch) in (int, float)
            and math.isfinite(epoch)
            and 0 <= at.timestamp() - epoch <= 5
            and all(
                isinstance(receipt.get(k), str)
                and len(receipt[k]) == 64
                and all(c in "0123456789abcdef" for c in receipt[k])
                for k in ("family_sha256", "scope_execution_hash")
            )
            and bool(receipt.get("selected_scope"))
            and isinstance(truth, dict)
            and bool(truth)
            and all(
                isinstance(k, str) and k and (allow_incomplete or v == "FALSE")
                for k, v in truth.items()
            )
            and (
                allow_incomplete
                or (
                    type(raw_ready) is int
                    and raw_ready >= 0
                    and type(receipt.get("selected_ready_count")) is int
                    and receipt["selected_ready_count"] == 0
                )
            )
            and all(
                type(receipt.get(k)) is int and receipt[k] > 0
                for k in ("native_epoch", "native_sequence")
            )
            and type(receipt.get("observed_seconds")) in (int, float)
            and math.isfinite(receipt["observed_seconds"])
            # This clock covers the current continuous segment, not lifetime
            # counts. A reset can leave verified history with a zero interval;
            # it proves neither current coverage nor a complete no-match.
            and (
                receipt["observed_seconds"] >= 0
                if feature_gap or historical
                else receipt["observed_seconds"] > 0
            )
            and int(fields.get("zero_base_ws_exact_0b_count", 0)) > 0
            # A missing-feature receipt may itself lack a signed trade.
            # Require an explicit nonnegative count; ordinary no-match and
            # pending coverage keep their positive signed-trade prerequisite.
            and type(signed_trades) in (int, str)
            and int(signed_trades) >= (0 if feature_gap else 1)
            and int(fields.get("zero_base_ws_exact_0d_count", 0)) > 0
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        SyntaxError,
        RecursionError,
        OverflowError,
    ):
        return False


def _probe_verified_pending(row, *, feature_gap=False):
    """Verify native incomplete outcomes; UNKNOWN never becomes an assessment."""
    if not _probe_verified_no_match(
        row, allow_incomplete=True, feature_gap=feature_gap
    ):
        return None
    try:
        fields = row["fields"]
        reason = fields.get("zero_base_probe_reason")
        allowed_reasons = (
            {"required_branch_feature_missing"}
            if feature_gap
            else {
                "confirmation_pending_at_residence_end",
                "feature_window_incomplete",
                "native_confirmation_not_consumed_before_expiry",
            }
        )
        if reason not in allowed_reasons:
            return None
        receipt = fields["native_observation_receipt"]
        if isinstance(receipt, str):
            try:
                receipt = json.loads(receipt)
            except ValueError:
                receipt = ast.literal_eval(receipt)
        truth, counts = (
            receipt["selected_branch_truth"],
            receipt["selected_lifecycle_counts"],
        )
        if (
            receipt.get("reason")
            not in {"required_window_incomplete", "no_matching_pattern"}
            or any(v not in {"TRUE", "FALSE", "UNKNOWN"} for v in truth.values())
            or set(counts) != set(truth)
            or len(truth) > 512
            or any(
                type(receipt.get(k)) is not int or receipt[k] < 0
                for k in (
                    "selected_pending_count",
                    "source_censored_count",
                    "raw_ready_count",
                    "selected_ready_count",
                )
            )
            or receipt["selected_ready_count"] != 0
        ):
            return None
        # Pending anchors, latest branch truth and cumulative lifecycle counts
        # are different native populations. An earlier TRUE or another cell's
        # raw ready row does not invalidate this selected cell's pending proof.
        unknown = 0
        for values in counts.values():
            if (
                not isinstance(values, dict)
                or not set(values) <= {"TRUE", "FALSE", "UNKNOWN"}
                or any(type(v) is not int or v < 0 for v in values.values())
                or not sum(values.values())
            ):
                return None
            unknown += values.get("UNKNOWN", 0)
        # Match the producer's native_wait_result precedence and populations.
        # Historical TRUE counts can coexist with a current pending anchor;
        # without an anchor they describe an expired, unconsumed confirmation.
        pending = receipt["selected_pending_count"]
        historical_true = sum(values.get("TRUE", 0) for values in counts.values())
        if reason == "confirmation_pending_at_residence_end":
            if pending <= 0 or any(v == "TRUE" for v in truth.values()):
                return None
        elif reason == "native_confirmation_not_consumed_before_expiry":
            if pending != 0 or historical_true <= 0:
                return None
        elif (
            pending != 0
            or historical_true != 0
            or receipt["source_censored_count"] != 0
            or receipt.get("reason") != "required_window_incomplete"
            or not any(v == "UNKNOWN" for v in truth.values())
            or unknown <= 0
        ):
            return None
        if feature_gap:
            readiness = fields.get("zero_base_branch_readiness")
            if isinstance(readiness, str):
                if len(readiness) > 65536:
                    return None
                try:
                    readiness = json.loads(readiness)
                except ValueError:
                    readiness = ast.literal_eval(readiness)
            if not isinstance(readiness, dict):
                return None
            branches = readiness.get("branch_descriptors")
            if (
                fields.get("zero_base_probe_result_schema")
                != "zero_base_probe_result_v2"
                or readiness.get("schema") != "native_branch_residence_requirements_v2"
                or readiness.get("status") != "observed"
                or readiness.get("runtime_effect") is not False
                or readiness.get("decision_authority") != "none"
                or readiness.get("scope_changed") is not False
                or readiness.get("price_basis") != "exact_native_trade"
                or readiness.get("route") != fields.get("zero_base_route")
                or readiness.get("policy_scope") != receipt.get("selected_scope")
                or any(
                    type(readiness.get(k)) is not int
                    for k in ("native_epoch", "native_sequence")
                )
                or any(
                    readiness.get(k) != receipt.get(k)
                    for k in (
                        "item",
                        "family_sha256",
                        "scope_execution_hash",
                        "native_epoch",
                        "native_sequence",
                    )
                )
                or not isinstance(branches, dict)
                or set(branches) != set(truth)
            ):
                return None
            # Native feature availability and detector truth are independent:
            # a FALSE prerequisite can be known before every feature is ready.
            # Keep UNKNOWN and exact receipt binding mandatory for this census.
            missing = 0
            for branch, descriptor in branches.items():
                inputs = (
                    descriptor.get("missing_inputs")
                    if isinstance(descriptor, dict)
                    else None
                )
                if (
                    not isinstance(inputs, list)
                    or len(inputs) > 64
                    or any(
                        not isinstance(v, str)
                        or not re.fullmatch("[A-Za-z0-9_]{1,80}", v)
                        for v in inputs
                    )
                    or descriptor.get("detector_truth") != truth[branch]
                    or descriptor.get("feature_availability")
                    not in ("complete", "incomplete")
                    or bool(inputs)
                    != (descriptor.get("feature_availability") == "incomplete")
                    or inputs
                    and truth[branch] == "TRUE"
                ):
                    return None
                missing += len(inputs)
            if not missing:
                return None
        return dict(
            pending_count=receipt["selected_pending_count"],
            unknown_count=unknown,
            source_censored_count=receipt["source_censored_count"],
        )
    except (KeyError, ValueError, TypeError, SyntaxError, RecursionError):
        return None


def _probe_verified_history(row):
    """Historical evaluations prove neither current executable data nor no-match."""
    if not _probe_verified_no_match(row, allow_incomplete=True, historical=True):
        return None
    try:
        f = row["fields"]
        r = f["native_observation_receipt"]
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except ValueError:
                r = ast.literal_eval(r)
        counts = r["selected_lifecycle_counts"]
        truth = r["selected_branch_truth"]
        if (
            r.get("reason") not in {"no_matching_pattern", "required_window_incomplete"}
            or not isinstance(counts, dict)
            or not 0 < len(counts) <= 512
            or set(counts) != set(truth)
            or any(v not in {"TRUE", "FALSE", "UNKNOWN"} for v in truth.values())
            or any(
                not isinstance(v, dict)
                or not set(v) <= {"TRUE", "FALSE", "UNKNOWN"}
                or any(type(n) is not int or n < 0 for n in v.values())
                for v in counts.values()
            )
            or type(r.get("source_censored_count")) is not int
            or r["source_censored_count"] < 0
        ):
            return None
        known = sum(v.get("TRUE", 0) + v.get("FALSE", 0) for v in counts.values())
        reason = f.get("zero_base_probe_reason")
        if known <= 0 or not (
            reason == "native_history_observed_current_source_stale"
            and r.get("native_source_current") is False
            or reason == "native_history_observed_with_source_gap"
            and r.get("native_source_current") is True
            and r["source_censored_count"] > 0
        ):
            return None
        return {"known_count": known}
    except (KeyError, TypeError, ValueError, SyntaxError, RecursionError):
        return None


def source_gap_semantics(
    data_root, now, *, tail_bytes=SOURCE_TAIL_BYTES, _loaded=None, _actor=None
):
    """Observe source causes before and after machine assessment without trading authority."""
    now = stamp(now)
    day = now.date().isoformat()
    paths = {
        "probe": (
            data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl",
            "emitted_at",
        ),
        "trace": (
            data_root / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl",
            "decision_ts",
        ),
        "pending": (
            data_root / "ai_decision_outcomes" / f"ai_decision_outcomes_{day}.jsonl",
            "decision_ts",
        ),
    }
    sources, issues, diagnostics, observed = {}, Counter(), Counter(), Counter()
    loaded = {} if _loaded is None else _loaded
    excluded_rows = 0
    excluded_prebirth = 0

    def read_source(path, at, *, time_field, **kwargs):
        nonlocal excluded_rows, excluded_prebirth
        if _loaded is None:
            indexed = None
            if path == paths["probe"][0] and tail_bytes == SOURCE_TAIL_BYTES:
                import sqlite3
                from src.engine.monitoring.sentinel_source_window import (
                    read as read_source_window,
                )

                health_actor = _HEALTH_ACTOR.get()
                birth = _HEALTH_BIRTH.get()
                actor_start = (
                    _verified_health_actor_birth(birth, health_actor, at)
                    if health_actor and birth
                    else None
                )
                lower = at.timestamp() - SOURCE_WINDOW_SEC
                if actor_start is not None:
                    lower = max(lower, actor_start)
                try:
                    indexed = read_source_window(data_root, at, lower_epoch=lower)
                    if lower > at.timestamp() - SOURCE_WINDOW_SEC:
                        indexed[1].update(
                            status="partial",
                            window_covered=False,
                            actor_lifetime_bound=True,
                        )
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    sqlite3.DatabaseError,
                ):
                    pass
            rows, receipt = (
                indexed
                if indexed is not None
                else _recent_source_rows(path, at, time_field=time_field, **kwargs)
            )
            loaded[str(path)] = (rows, receipt)
        else:
            rows, receipt = loaded[str(path)]
        if _actor:
            birth = _HEALTH_BIRTH.get()
            lower = _verified_health_actor_birth(birth, _actor, at) if birth else None
            selected = []
            for row in rows:
                identity = _row_actor(row)
                at_row = stamp(row.get(time_field))
                if (
                    identity is None
                    and lower is not None
                    and at_row is not None
                    and at_row.timestamp() < lower
                ):
                    excluded_prebirth += 1
                    continue
                if identity in (None, _actor):
                    selected.append(row)
            excluded_rows += len(rows) - len(selected)
            rows, receipt = selected, dict(receipt, recent_count=len(selected))
            first = stamp(receipt.get("first_read_at"))
            window_start = (
                max(at.timestamp() - SOURCE_WINDOW_SEC, lower)
                if lower is not None
                else None
            )
            if (
                window_start is not None
                and first is not None
                and first.timestamp() <= window_start
                and receipt.get("status") == "partial"
                and receipt.get("window_covered") is False
                and receipt.get("malformed_rows") == 0
                and receipt.get("missing_timestamp_rows") == 0
                and receipt.get("incomplete_last_line") is False
            ):
                receipt.update(
                    status="complete",
                    window_covered=True,
                    original_window_status="partial",
                    coverage_basis=(
                        receipt.get("coverage_basis")
                        if receipt.get("actor_lifetime_bound") is True
                        else "current_actor_lifetime_bounded_tail"
                    ),
                    current_window_start_at=datetime.fromtimestamp(
                        window_start, KST
                    ).isoformat(),
                )
        return rows, receipt

    issue_scopes, diagnostic_scopes, healthy_scopes = Counter(), Counter(), Counter()
    issue_examples, diagnostic_examples = [], []
    seen = set()
    probe_by_route, assessed_by_route = Counter(), Counter()
    covered_by_route, no_match_by_route, seen_probes = Counter(), Counter(), set()

    def record(
        stage, reason, row, *, diagnostic=False, code=None, route=None, attempt=None
    ):
        if stage == "machine_probe" and not attempt:
            fields = row.get("fields")
            probe_attempt = (
                fields.get("evaluation_attempt_id")
                if isinstance(fields, dict)
                else None
            )
            if isinstance(probe_attempt, str):
                normalized_attempt = probe_attempt.strip()
                if normalized_attempt.lower() not in {"", "-", "none", "null"}:
                    attempt = normalized_attempt
        reason = str(reason)
        if (
            len(reason) > 80
            or not reason
            or any(
                char
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:-"
                for char in reason
            )
        ):
            reason = "unclassified_source_gap"
        identity = (
            stage,
            attempt or row.get("decision_trace_id") or row.get("emitted_at"),
            code or row.get("stock_code"),
            route or row.get("market_data_route"),
            reason,
        )
        if stage == "machine_probe":
            identity = (stage, _probe_identity(row), reason)
        if identity in seen:
            return
        seen.add(identity)
        (diagnostics if diagnostic else issues)[f"{stage}:{reason}"] += 1
        scope = scope_for(stage, row, route)
        (diagnostic_scopes if diagnostic else issue_scopes)[
            f"{scope}|{stage}:{reason}"
        ] += 1
        examples = diagnostic_examples if diagnostic else issue_examples
        if len(examples) < 3:
            examples.append(
                {
                    "stage": stage,
                    "reason": reason,
                    "occurred_at": row.get("decision_ts") or row.get("emitted_at"),
                    "stock_code": str(code or row.get("stock_code") or "")[:6],
                    "route": str(route or row.get("market_data_route") or "")[:48],
                    "effective_venue": str(row.get("effective_venue") or "")[:32],
                    "session_bucket": str(row.get("session_bucket") or "")[:48],
                    "evaluation_attempt_id": str(
                        attempt or row.get("evaluation_attempt_id") or ""
                    )[:96],
                }
            )

    def scope_for(stage, row, route=None):
        if stage == "machine_probe":
            return f'route:{route or "UNKNOWN"}'
        return (
            f'{str(row.get("effective_venue") or "UNKNOWN").upper()}|'
            f'{str(row.get("session_bucket") or "UNKNOWN").upper()}|'
            f'route:{str(route or row.get("market_data_route") or "UNKNOWN")[:48]}'
        )

    def healthy(stage, row, route=None):
        healthy_scopes[f"{scope_for(stage, row, route)}|{stage}"] += 1

    probe_rows, sources["probe"] = read_source(
        paths["probe"][0], now, time_field=paths["probe"][1], tail_bytes=tail_bytes
    )
    # These existing raw rows are excluded from the decision population. Keep a
    # bounded census so an actionable fixed-watch wait cannot masquerade as a
    # no-decision window. No additional source read or strategy change occurs.
    from src.trading.market import session_contract
    from src.engine.scalping.main_fixed_watch import (
        SPECS,
        MIN_WARMUP_SEC,
        generation_id,
        session_route,
    )

    fixed_symbols = {spec.symbol for spec in SPECS}
    native_session = session_contract.resolve_market_session(now)
    wait_total = boundary_waits = source_waits = unclassified_waits = 0
    pending_total = pending_verified = pending_unknown = pending_censored = 0
    feature_gap_total = feature_gap_verified = feature_gap_unknown = 0
    history_total = history_verified = history_known = 0
    wait_reasons = Counter()

    def native_watch_claim(fields, symbol, at, route):
        if route is None:
            return False
        admission = fields.get("watch_admission_id")
        return (
            fields.get("venue_resolution") == "main_fixed_watch_session_route"
            and fields.get("watch_generation_id")
            == generation_id(at.timestamp(), route)
            and isinstance(admission, str)
            and re.fullmatch(
                re.escape(
                    f"FIXED-{at.date()}-{symbol}-{route['bucket']}-{route['route']}-"
                )
                + "[0-9a-f]{12}",
                admission,
            )
            is not None
            and fields.get("source_signature") == "MAIN_FIXED_WATCH:" + admission
            and (fields.get("effective_venue"), fields.get("market_session_bucket"))
            == (route["venue"], route["bucket"])
        )

    for row in probe_rows:
        if (
            row.get("pipeline") != "ENTRY_PIPELINE"
            or row.get("stage") != "main_fixed_watch_observation_wait"
        ):
            continue
        wait_total += 1
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        reason = fields.get("source_quality_reason")
        reason = (
            reason
            if isinstance(reason, str) and re.fullmatch("[A-Za-z0-9_]{1,80}", reason)
            else "unclassified"
        )
        wait_reasons[
            reason if reason in wait_reasons or len(wait_reasons) < 16 else "other"
        ] += 1
        row_at = stamp(row.get("emitted_at"))
        context = session_contract.resolve_market_session(row_at) if row_at else None
        # Main fixed watch owns its NXT premarket session; the common KRX
        # clock intentionally disallows entry then. Verify its native generation
        # and admission identity without granting entry or source completeness.
        fixed_route = (
            session_route(row_at.timestamp(), row["stock_code"])
            if row_at
            and isinstance(row.get("stock_code"), str)
            and row["stock_code"] in fixed_symbols
            else None
        )
        current_claim = bool(
            fixed_route
            and native_watch_claim(fields, row["stock_code"], row_at, fixed_route)
        )
        premarket_wait = bool(
            context is not None
            and current_claim
            and context.session_regime
            == session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET
        )
        previous_route = (
            session_route(row_at.timestamp() - MIN_WARMUP_SEC, row["stock_code"])
            if fixed_route
            else None
        )
        rollover_wait = bool(
            previous_route
            and previous_route != fixed_route
            and native_watch_claim(fields, row["stock_code"], row_at, previous_route)
        )
        if (
            reason == "session_generation_mismatch"
            and context is not None
            and (context.entry_allowed_by_clock is False or rollover_wait)
            and fields.get("watch_origin") == "MAIN_FIXED_WATCH"
            and isinstance(row.get("stock_code"), str)
            and row["stock_code"] in fixed_symbols
            and fields.get("venue_source_quality_status") == "pass"
            and isinstance(fields.get("effective_venue"), str)
            and isinstance(fields.get("market_session_bucket"), str)
            and (
                rollover_wait
                or (
                    context.session_regime,
                    fields.get("effective_venue"),
                    fields.get("market_session_bucket"),
                )
                in {
                    (
                        session_contract.MARKET_SESSION_REGIME_SESSION_TRANSITION,
                        "KRX",
                        "krx_regular",
                    ),
                    (
                        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY,
                        "KRX_NXT_INTEGRATED",
                        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
                    ),
                    (
                        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_TERMINAL_EXIT,
                        "KRX_NXT_INTEGRATED",
                        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
                    ),
                }
            )
            and (
                fields.get("actual_order_submitted") is False
                or fields.get("actual_order_submitted") == "False"
            )
            and (
                fields.get("broker_order_forbidden") is True
                or fields.get("broker_order_forbidden") == "True"
            )
        ):
            boundary_waits += 1
        elif (
            reason in _FIXED_SOURCE_WAIT_REASONS
            and context is not None
            and (context.entry_allowed_by_clock is True or premarket_wait)
            and (
                current_claim
                or reason
                in {
                    "post_receipt_observation_warmup",
                    "fixed_watch_post_receipt_warmup",
                    "exact_0B_missing",
                }
            )
            and fields.get("watch_origin") == "MAIN_FIXED_WATCH"
            and isinstance(row.get("stock_code"), str)
            and row["stock_code"] in fixed_symbols
            and fields.get("venue_source_quality_status") == "pass"
            and fixed_route is not None
            and (fields.get("effective_venue"), fields.get("market_session_bucket"))
            == (fixed_route["venue"], fixed_route["bucket"])
            and (
                fields.get("actual_order_submitted") is False
                or fields.get("actual_order_submitted") == "False"
            )
            and (
                fields.get("broker_order_forbidden") is True
                or fields.get("broker_order_forbidden") == "True"
            )
        ):
            source_waits += 1
        else:
            unclassified_waits += 1
    for row in probe_rows:
        if (
            row.get("pipeline") != "ENTRY_PIPELINE"
            or row.get("stage") != "zero_base_probe_result"
        ):
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        result = str(fields.get("zero_base_probe_result") or "")
        reason = str(fields.get("zero_base_probe_reason") or "")
        route = fields.get("zero_base_route")
        identity = _probe_identity(row)
        if identity in seen_probes:
            continue
        seen_probes.add(identity)
        observed["probe_results"] += 1
        if result in {
            "assessed",
            "required_feature_insufficient",
            "source_unavailable",
            "pattern_not_matched",
            "observation_incomplete",
        } or (
            result == "policy_unavailable" and reason != "zero_base_runtime_disabled"
        ):
            probe_by_route[str(route or "UNKNOWN")] += 1
        if result == "assessed":
            observed["probe_assessed"] += 1
            assessed_by_route[str(route or "UNKNOWN")] += 1
            captured = fields.get("machine_capture_status") == "captured"
            observation_hash = str(fields.get("machine_observation_sha256") or "")
            if (
                not captured
                or len(observation_hash) != 64
                or any(char not in "0123456789abcdef" for char in observation_hash)
            ):
                record(
                    "machine_probe",
                    "capture_receipt_missing_or_invalid",
                    row,
                    code=row.get("stock_code"),
                    route=route,
                )
            else:
                covered_by_route[str(route or "UNKNOWN")] += 1
                healthy("machine_probe", row, route)
        elif result == "observation_incomplete" and reason in {
            "native_history_observed_current_source_stale",
            "native_history_observed_with_source_gap",
        }:
            observed["probe_history_only"] += 1
            history_total += 1
            proof = _probe_verified_history(row)
            if proof is not None:
                history_verified += 1
                history_known += proof["known_count"]
            record(
                "machine_probe",
                reason if proof else "native_history_unverified",
                row,
                diagnostic=True,
                code=row.get("stock_code"),
                route=route,
            )
        elif result == "observation_incomplete":
            observed["probe_observation_incomplete"] += 1
            pending_total += 1
            pending = _probe_verified_pending(row)
            if pending is not None:
                pending_verified += 1
                pending_unknown += pending["unknown_count"]
                pending_censored += pending["source_censored_count"]
            if _probe_verified_no_match(row, allow_incomplete=True):
                covered_by_route[str(route or "UNKNOWN")] += 1
            record(
                "machine_probe",
                "native_observation_incomplete",
                row,
                diagnostic=True,
                code=row.get("stock_code"),
                route=route,
            )
        elif result in {"required_feature_insufficient", "pattern_not_matched"}:
            if (
                result == "required_feature_insufficient"
                and reason == "required_branch_feature_missing"
            ):
                feature_gap_total += 1
                observed["probe_feature_missing"] += 1
                proof = _probe_verified_pending(row, feature_gap=True)
                if proof is not None:
                    feature_gap_verified += 1
                    feature_gap_unknown += proof["unknown_count"]
                    record(
                        "machine_probe",
                        "required_branch_feature_missing",
                        row,
                        diagnostic=True,
                        code=row.get("stock_code"),
                        route=route,
                    )
                    # Missing required features never count as covered, assessed
                    # or no-match, even when their source contract is verified.
                    continue
            if _probe_verified_no_match(row):
                covered_by_route[str(route or "UNKNOWN")] += 1
                no_match_by_route[str(route or "UNKNOWN")] += 1
                observed["probe_native_no_match"] += 1
                # This cannot recover a missing machine capture or AI receipt.
                # It contributes only to the route source-coverage numerator.
                record(
                    "machine_probe",
                    "native_no_matching_pattern",
                    row,
                    diagnostic=True,
                    code=row.get("stock_code"),
                    route=route,
                )
                continue
            kind = str(fields.get("zero_base_machine_source_gap_kind") or "").strip(
                "- "
            )
            kind = kind or (
                reason
                if reason
                in {
                    "tick_or_candle_missing",
                    "candle_source_missing",
                    "candle_context_missing",
                    "ws_tick_source_changed_before_machine",
                }
                else "required_feature_insufficient_unclassified"
            )
            record(
                "machine_probe",
                kind,
                row,
                diagnostic=kind
                not in {"source_route_conflict", "feature_tick_selection_gap"},
                code=row.get("stock_code"),
                route=route,
            )
        elif result == "source_unavailable" and reason in {
            "route_snapshot_missing",
            "0B_missing",
            "0B_age_exceeded",
            "0D_missing",
            "0D_age_exceeded",
            "rest_route_or_receive_clock_invalid",
            "exact_route_subscription_conflict",
            "ws_registration_receipt_missing",
        }:
            record(
                "machine_probe",
                reason,
                row,
                diagnostic=reason
                in {
                    "route_snapshot_missing",
                    "0B_missing",
                    "0B_age_exceeded",
                    "0D_missing",
                    "0D_age_exceeded",
                },
                code=row.get("stock_code"),
                route=route,
            )
        elif result == "policy_unavailable" and (
            reason == "assessment_contract_invalid"
            or reason.startswith("machine_exception:")
            or fields.get("zero_base_machine_contract_error") not in (None, "", "-")
        ):
            kind = str(fields.get("zero_base_machine_source_gap_kind") or "").strip(
                "- "
            )
            contract_error = str(
                fields.get("zero_base_machine_contract_error") or ""
            ).strip("- ")
            kind = (
                kind
                or (
                    "machine_source_nonfinite"
                    if contract_error.startswith(
                        "Out of range float values are not JSON compliant:"
                    )
                    else contract_error
                )
                or (
                    "contract_error_receipt_missing"
                    if reason == "assessment_contract_invalid"
                    else reason
                )
            )
            receipt = fields.get("continuous_reversal_rejected_claim_receipt")
            if isinstance(receipt, str) and len(receipt) <= 65536:
                try:
                    receipt = json.loads(receipt)
                except ValueError:
                    try:
                        receipt = ast.literal_eval(receipt)
                    except (ValueError, SyntaxError):
                        receipt = None
            lifecycle = _reversal_lifecycle_diagnostic(
                dict(
                    row,
                    decision_ts=row.get("emitted_at"),
                    evaluation_attempt_id=fields.get("evaluation_attempt_id"),
                    machine_bundle_sha256=fields.get("machine_bundle_sha256"),
                    market_data_route=route,
                    machine_contract_error=contract_error,
                    provider_called=(
                        False
                        if (
                            fields.get("provider_called") is False
                            or fields.get("provider_called") == "False"
                        )
                        else None
                    ),
                    continuous_reversal_rejected_claim_receipt=receipt,
                )
            )
            if lifecycle:
                kind = lifecycle
                # Proven invalidation ends this assessment opportunity. It is
                # neither a missing capture nor a covered/no-match observation.
                probe_by_route[str(route or "UNKNOWN")] -= 1
                observed["probe_native_invalidated"] += 1
            record(
                "machine_probe",
                kind,
                row,
                diagnostic=bool(lifecycle)
                or kind == "trusted_tape_source_insufficient",
                code=row.get("stock_code"),
                route=route,
            )
    for route, count in probe_by_route.items():
        if sources["probe"]["status"] != "complete" or count < 10:
            continue
        if covered_by_route[route] * 5 < count:
            # Source coverage includes validated native FALSE observations.
            # Pattern absence and AI admission are not transport failures.
            issues[f"machine_probe:coverage_degraded:{route}"] += 1
            issue_scopes[f"route:{route}|machine_probe:coverage_degraded"] += 1
        else:
            healthy_scopes[f"route:{route}|machine_probe:coverage_degraded"] += 1

    trace_rows, sources["trace"] = read_source(
        paths["trace"][0], now, time_field=paths["trace"][1], tail_bytes=tail_bytes
    )
    # Only the adjacent partition required by the same bounded observation
    # window is read. Physical append dates never replace occurrence clocks.
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if (now - midnight).total_seconds() < SOURCE_WINDOW_SEC:
        previous = (now - timedelta(days=1)).date().isoformat()
        for kind, rows in (("probe", probe_rows), ("trace", trace_rows)):
            prior_path = paths[kind][0].with_name(
                paths[kind][0].name.replace(day, previous)
            )
            prior_rows, receipt = read_source(
                prior_path,
                now,
                time_field=paths[kind][1],
                tail_bytes=tail_bytes,
                allow_adjacent_date=True,
            )
            rows.extend(prior_rows)
            sources[kind]["adjacent_partition"] = receipt
            if receipt["status"] != "complete":
                sources[kind]["status"] = "partial"
    pass_projection = []
    unmapped_pass_count = 0
    for row in trace_rows:
        if (
            row.get("decision_stage") == "entry_screen"
            and row.get("decision_evaluation_status") == "evaluated"
            and row.get("entry_mechanistic_action") == "ENTER_NOW"
            and row.get("entry_ai_screen_status") == "pass"
            and row.get("entry_ai_risk_verdict") == "PASS"
            and row.get("provider_called") is True
        ):
            if (
                not all(
                    str(row.get(key) or "").strip().lower()
                    not in {"", "-", "none", "null", "unknown", "0"}
                    for key in (
                        "async_request_id",
                        "decision_trace_id",
                        "evaluation_attempt_id",
                        "async_producer_pid",
                        "async_producer_start_ticks",
                    )
                )
                or not str(row.get("stock_code") or "").isdigit()
                or len(str(row.get("stock_code"))) != 6
            ):
                unmapped_pass_count += 1
                continue
            fields = {
                k: row.get(k)
                for k in (
                    "async_request_id",
                    "async_producer_pid",
                    "async_producer_start_ticks",
                    "async_origin_deadline_epoch",
                    "scanner_generation_id",
                    "evaluation_attempt_id",
                    "effective_venue",
                    "async_order_venue",
                    "entry_machine_bundle_sha256",
                    "entry_auxiliary_policy_sha256",
                    "watch_origin",
                    "watch_admission_id",
                    "watch_generation_id",
                    "scanner_promotion_id",
                )
            }
            fields.update(
                ai_decision_trace_id=row["decision_trace_id"],
                async_disposition="validated_pass_trace",
                async_disposition_event_id="pass-trace:" + row["decision_trace_id"],
                async_machine_action="ENTER_NOW",
                async_auxiliary_status="pass",
                async_auxiliary_verdict="PASS",
                async_provider_called=True,
            )
            pass_projection.append(
                dict(
                    emitted_at=row["decision_ts"],
                    stock_code=row["stock_code"],
                    fields=fields,
                )
            )
    for row in trace_rows:
        if row.get("decision_stage") != "entry_screen":
            continue
        observed["entry_traces"] += 1
        status = str(row.get("machine_evaluation_status") or "")
        if status == "assessed":
            observed["machine_assessed"] += 1
            capture_status = row.get("machine_capture_status")
            observation_hash = str(row.get("machine_observation_sha256") or "")
            capture_valid = (
                capture_status == "captured"
                and len(observation_hash) == 64
                and all(char in "0123456789abcdef" for char in observation_hash)
            )
            if not capture_valid:
                record("machine_trace", "capture_receipt_missing_or_invalid", row)
            if row.get("entry_mechanistic_action") == "SOURCE_INVALID":
                record(
                    "machine_trace",
                    str(
                        row.get("entry_source_invalid_primary_blocker")
                        or "source_invalid_unclassified"
                    ),
                    row,
                    diagnostic=True,
                )
            elif capture_valid and not row.get("machine_contract_error"):
                healthy("machine_trace", row)
        elif status in {
            "required_feature_blocked_before_assessment",
            "source_quality_blocked_before_assessment",
        }:
            kind = str(row.get("machine_source_gap_kind") or status)
            record(
                "machine_trace",
                kind,
                row,
                diagnostic=kind
                not in {"source_route_conflict", "feature_tick_selection_gap"},
            )
        elif status == "assessment_contract_invalid":
            kind = str(
                row.get("machine_source_gap_kind")
                or row.get("machine_contract_error")
                or "contract_error_receipt_missing"
            )
            lifecycle = _reversal_lifecycle_diagnostic(row)
            if lifecycle:
                kind = lifecycle
            if kind.startswith("Out of range float values are not JSON compliant:"):
                kind = "machine_source_nonfinite"
            record(
                "machine_trace",
                kind,
                row,
                diagnostic=bool(lifecycle)
                or _entry_input_deadline_guard(row)
                or kind == "trusted_tape_source_insufficient",
            )
        elif row.get("machine_contract_error"):
            kind = str(
                row.get("machine_source_gap_kind") or row["machine_contract_error"]
            )
            record(
                "machine_trace",
                kind,
                row,
                diagnostic=kind
                not in {"source_route_conflict", "feature_tick_selection_gap"},
            )
        if (
            row.get("entry_mechanistic_action") != "ENTER_NOW"
            or row.get("entry_ai_screen_required") is not True
        ):
            continue
        observed["auxiliary_required"] += 1
        if row.get("provider_called") is not True:
            continue  # An uncalled auxiliary has no provider-cost receipt obligation.
        observed["auxiliary_called"] += 1
        reference = row.get("reference_price")
        route_valid = (
            type(reference) in (int, float)
            and math.isfinite(reference)
            and reference > 0
            and row.get("effective_venue")
            and row.get("session_bucket")
            and row.get("market_data_route")
        )
        if not route_valid:
            record("auxiliary_call", "route_or_reference_missing", row)
        if row.get("entry_ai_screen_status") == "not_evaluated_transport":
            observed["auxiliary_transport_unavailable"] += 1
        if row.get("entry_cost_source_status") == "source_gap":
            record("auxiliary_call", "cost_source_gap", row)
        elif row.get("entry_cost_source_status") != "exact_pre_provider_replay":
            record("auxiliary_call", "cost_receipt_missing", row)
        elif not _auxiliary_cost_receipt_valid(row):
            record("auxiliary_call", "cost_receipt_invalid", row)
        elif route_valid:
            observed["auxiliary_cost_bound"] += 1
            healthy("auxiliary_call", row)

    pending_rows, sources["pending"] = read_source(
        paths["pending"][0], now, time_field=paths["pending"][1], tail_bytes=tail_bytes
    )
    pending_by_trace = {}
    for row in pending_rows:
        if (
            row.get("decision_stage") != "entry_screen"
            or row.get("entry_mechanistic_action") != "ENTER_NOW"
            or row.get("entry_ai_screen_required") is not True
            or row.get("entry_ai_screen_status")
            not in {
                "pass",
                "veto",
                "caution",
                "insufficient",
                "response_invalid",
                "not_evaluated_transport",
            }
        ):
            continue
        observed["auxiliary_pending"] += 1
        if row.get("decision_trace_id"):
            prior = pending_by_trace.setdefault(row["decision_trace_id"], row)
            if prior is not row:
                record("auxiliary_pending", "duplicate_trace_identity", row)
        if not row.get("decision_trace_id") or not row.get("evaluation_attempt_id"):
            record("auxiliary_pending", "identity_missing", row)
        reference = row.get("reference_price")
        pending_route_valid = (
            row.get("market_data_route")
            and row.get("effective_venue")
            and row.get("session_bucket")
            and type(reference) in (int, float)
            and math.isfinite(reference)
            and reference > 0
        )
        if not pending_route_valid:
            record("auxiliary_pending", "route_or_reference_missing", row)
        if row.get("entry_ai_screen_status") != "insufficient":
            if row.get("entry_cost_source_status") != "exact_pre_provider_replay":
                record("auxiliary_pending", "cost_receipt_missing", row)
            elif not _auxiliary_cost_receipt_valid(row):
                record("auxiliary_pending", "cost_receipt_invalid", row)
            elif (
                pending_route_valid
                and row.get("decision_trace_id")
                and row.get("evaluation_attempt_id")
            ):
                observed["auxiliary_pending_bound"] += 1
                healthy("auxiliary_pending", row)
    trace_by_id = {
        row["decision_trace_id"]: row
        for row in trace_rows
        if row.get("decision_stage") == "entry_screen" and row.get("decision_trace_id")
    }
    binding_fields = (
        "evaluation_attempt_id",
        "stock_code",
        "effective_venue",
        "session_bucket",
        "market_data_route",
        "reference_price",
        "entry_cost_source_status",
        "entry_conservative_execution_cost_pct",
        "entry_cost_scope",
        "entry_cost_basis",
        "entry_cost_contract_sha256",
        "entry_cost_replay_context_sha256",
        "entry_cost_evaluation_attempt_id",
    )
    for trace_id, pending in pending_by_trace.items():
        trace = trace_by_id.get(trace_id)
        if trace is not None and any(
            pending.get(field) != trace.get(field) for field in binding_fields
        ):
            record("auxiliary_pending", "trace_binding_mismatch", pending)
    if sources["pending"]["status"] == "complete":
        for row in trace_rows:
            if (
                row.get("decision_stage") == "entry_screen"
                and row.get("entry_mechanistic_action") == "ENTER_NOW"
                and row.get("entry_ai_screen_required") is True
                and row.get("outcome_label_eligible") is True
                and row.get("decision_trace_id")
                and (now - stamp(row.get("decision_ts"))).total_seconds() >= 60
            ):
                pending = pending_by_trace.get(row["decision_trace_id"])
                if pending is None:
                    record("auxiliary_pending", "label_receipt_missing", row)
                elif any(
                    pending.get(field) != row.get(field) for field in binding_fields
                ):
                    record("auxiliary_pending", "trace_binding_mismatch", pending)
    elif sources["pending"].get("reason") in {"FileNotFoundError", "empty_source"}:
        for row in trace_rows:
            at = stamp(row.get("decision_ts"))
            if (
                row.get("decision_stage") == "entry_screen"
                and row.get("entry_mechanistic_action") == "ENTER_NOW"
                and row.get("entry_ai_screen_required") is True
                and row.get("outcome_label_eligible") is True
                and row.get("decision_trace_id")
                and at
                and (now - at).total_seconds() >= 60
            ):
                record("auxiliary_pending", "source_file_missing", row)
    remediation = []
    for issue in sorted(issues):
        stage = issue.split(":", 1)[0]
        owner, action = {
            "machine_probe": (
                "zero_base_probe|scalping_feature_packet",
                "compare exact REG/0B/0D route and epoch; use existing queue rotation",
            ),
            "machine_trace": (
                "entry_setup_live_policy|ai_decision_trace",
                "inspect exact feature and decision-source receipt",
            ),
            "auxiliary_call": (
                "ai_engine_openai|ai_decision_trace",
                "repair exact pre-provider cost or route receipt from verified source",
            ),
            "auxiliary_pending": (
                "ai_decision_trace|ai_decision_quality",
                "join exact attempt pending label and completed-bar source",
            ),
        }[stage]
        remediation.append(
            {
                "issue": issue,
                "owner": owner,
                "source_only_action": action,
                "automatic_repair_attempted": False,
                "order_authority": False,
            }
        )
    status = (
        "gap_observed"
        if issues or diagnostics
        else (
            "observed_no_gap"
            if all(s["status"] == "complete" for s in sources.values())
            and any(observed.values())
            else "unobservable"
        )
    )
    result = {
        "schema": "machine_auxiliary_intraday_source_semantics_v1",
        "as_of": now.isoformat(),
        "status": status,
        "metric_role": "source_quality_gate",
        "decision_authority": "report_only",
        "window_policy": "current_10m_bounded_jsonl_tail",
        "sample_floor": "one_exact_stage_receipt",
        "primary_decision_metric": "source_gap_events_by_stage_and_reason",
        "source_quality_gate": "exact_current_date_complete_window_per_source",
        "forbidden_uses": [
            "order_authority",
            "threshold_or_provider_change",
            "missing_as_zero_ev",
            "actual_trade_failure_claim",
            "historical_source_repair_claim",
        ],
        "sources": sources,
        "observed": dict(observed),
        "issues": dict(sorted(issues.items())),
        "fixed_watch_waits": {
            "schema": "submission_monitor_fixed_watch_wait_census_v1",
            "count": wait_total,
            "session_boundary_wait_count": boundary_waits,
            "known_source_wait_count": source_waits,
            "unclassified_or_actionable_wait_count": unclassified_waits,
            "reason_counts": dict(sorted(wait_reasons.items())),
            "native_session_regime": native_session.session_regime,
            "native_entry_allowed_by_clock": native_session.entry_allowed_by_clock,
            "runtime_effect": False,
        },
        "native_pending_observations": {
            "schema": "submission_monitor_native_pending_census_v1",
            "count": pending_total,
            "verified_pending_count": pending_verified,
            "unclassified_count": pending_total - pending_verified,
            "unknown_count": pending_unknown,
            "source_censored_count": pending_censored,
            "runtime_effect": False,
            "machine_admission_proven": False,
            "pattern_no_match_proven": False,
        },
        "native_history_observations": {
            "schema": "submission_monitor_native_history_census_v1",
            "count": history_total,
            "verified_count": history_verified,
            "unclassified_count": history_total - history_verified,
            "known_count": history_known,
            "runtime_effect": False,
            "current_source_coverage_proven": False,
            "machine_admission_proven": False,
            "pattern_no_match_proven": False,
        },
        "native_feature_gap_observations": {
            "schema": "submission_monitor_native_feature_gap_census_v1",
            "count": feature_gap_total,
            "verified_count": feature_gap_verified,
            "unclassified_count": feature_gap_total - feature_gap_verified,
            "unknown_count": feature_gap_unknown,
            "runtime_effect": False,
            "source_coverage_proven": False,
            "machine_admission_proven": False,
            "pattern_no_match_proven": False,
        },
        "async_pass_projection": pass_projection[-128:],
        "async_pass_unmapped_count": unmapped_pass_count,
        "async_transition_projection": [
            dict(
                emitted_at=row.get("emitted_at"),
                stock_code=row.get("stock_code"),
                fields=row.get("fields") or {},
            )
            for row in probe_rows
            if row.get("stage") == "entry_async_disposition"
        ][-1024:],
        "async_transition_projection_coverage": (
            "complete"
            if sources["probe"]["status"] == "complete"
            and sum(row.get("stage") == "entry_async_disposition" for row in probe_rows)
            <= 1024
            else "partial"
        ),
        "async_pass_projection_coverage": (
            "complete"
            if len(pass_projection) <= 128
            and not unmapped_pass_count
            and sources["trace"]["status"] == "complete"
            else "partial"
        ),
        "diagnostics": dict(sorted(diagnostics.items())),
        "issues_by_scope": dict(sorted(issue_scopes.items())),
        "diagnostics_by_scope": dict(sorted(diagnostic_scopes.items())),
        "healthy_by_scope": dict(sorted(healthy_scopes.items())),
        "probe_route_counts": dict(sorted(probe_by_route.items())),
        "probe_route_assessed_counts": dict(sorted(assessed_by_route.items())),
        "probe_route_source_covered_counts": dict(sorted(covered_by_route.items())),
        "probe_route_native_no_match_counts": dict(sorted(no_match_by_route.items())),
        "coverage_alert_floor": "10_same_route_unique_probes_below_20pct_source_covered",
        "coverage_success_contract": "valid_machine_capture_or_exact_native_all_false_receipt",
        "remediation": remediation,
        "examples": issue_examples + diagnostic_examples,
        "runtime_effect": False,
        "next_action": (
            "inspect_exact_attempt_source_then_use_existing_bounded_source_only_repair"
            if issues
            else (
                "retain_sparse_or_source_quality_diagnostic_and_existing_queue_rotation"
                if diagnostics
                else None
            )
        ),
    }
    actor = _HEALTH_ACTOR.get()
    if actor and _loaded is None:
        view = source_gap_semantics(
            data_root, now, tail_bytes=tail_bytes, _loaded=loaded, _actor=actor
        )
        result["current_health_cohort"] = _health_cohort(
            view, actor, now, excluded=view.pop("_excluded_health_rows", 0)
        )
    elif _actor:
        result["_excluded_health_rows"] = excluded_rows
        result["excluded_pre_actor_birth_count"] = excluded_prebirth
    return result


def attach_source_gap_semantics(result, semantics):
    """Persist fresh source incidents; lack of a complete window cannot resolve one."""
    result["source_gap_semantics"] = semantics
    from types import SimpleNamespace

    current = result.get("async_disposition_coverage") or {}
    retained = [
        SimpleNamespace(stage="entry_async_disposition", **row)
        for row in (current.get("attempt_projection") or [])
        + (semantics.get("async_transition_projection") or [])
    ]
    result["async_disposition_coverage"] = async_disposition_coverage(
        retained,
        result["as_of"],
        pass_projections=semantics.get("async_pass_projection") or [],
        source_coverage=semantics.get("async_pass_projection_coverage"),
    )
    health = semantics.get("current_health_cohort")
    if isinstance(health, dict) and isinstance(health.get("view"), dict):
        semantics = health[
            "view"
        ]  # Original all-actor semantic evidence remains in result.
        if health.get("excluded_observation_count", 0) and not semantics.get("issues"):
            key = "machine_auxiliary_intraday_source_gap"
            old = result["incidents"].get(key, {})
            if old.get("status") in {"active", "pending", "historical_unresolved"}:
                result["incidents"][key] = {
                    **old,
                    "status": "historical_unresolved",
                    "current_status": "historical_not_current_cohort",
                }
            return  # No historical recovery or new current alert is inferred.
    key = "machine_auxiliary_intraday_source_gap"
    old = result["incidents"].get(key, {})
    issues = semantics.get("issues") or {}
    now = stamp(result["as_of"])
    if issues:
        recurring = bool(
            set(semantics.get("issues_by_scope") or {})
            & set(old.get("issues_by_scope") or {})
        )
        first = (
            old.get("first_seen", result["as_of"])
            if old.get("status") in {"pending", "active"} and recurring
            else result["as_of"]
        )
        only_coverage = all(
            issue.startswith("machine_probe:coverage_degraded:") for issue in issues
        )
        item = {
            "scope": "machine|auxiliary|exact_current_day",
            "rule": key,
            "category": "review_required" if only_coverage else "structural_evidence",
            "first_seen": first,
            "last_seen": result["as_of"],
            "status": (
                "active" if (now - stamp(first)).total_seconds() >= 240 else "pending"
            ),
            "count": sum(issues.values()),
            "issues": issues,
            "examples": semantics.get("examples", [])[:3],
            "issues_by_scope": semantics.get("issues_by_scope", {}),
            "source_status": {
                name: source.get("status")
                for name, source in semantics.get("sources", {}).items()
            },
            "owner": "zero_base_probe|ai_decision_trace|ai_decision_outcomes",
            "closure_test": "new exact-route machine and auxiliary receipts with complete recent windows",
            "notified_status": (
                old.get("notified_status")
                if recurring and old.get("status") in {"pending", "active"}
                else None
            ),
        }
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") in {"recovered", "historical_unresolved"}:
            item["history"] = (
                list(old.get("history", []))
                + [{k: v for k, v in old.items() if k != "history"}]
            )[-8:]
        result["incidents"][key] = item
    elif old.get("status") in {"pending", "active", "historical_unresolved"}:
        stage_source = {
            "machine_probe": "probe",
            "machine_trace": "trace",
            "auxiliary_call": "trace",
            "auxiliary_pending": "pending",
        }
        stages = {issue.split(":", 1)[0] for issue in old.get("issues", {})}
        prior_scopes = old.get("issues_by_scope") or {}
        healthy_scopes = semantics.get("healthy_by_scope") or {}

        def recovery_key(issue_scope):
            scope, stage_reason = issue_scope.rsplit("|", 1)
            if stage_reason.startswith("machine_probe:coverage_degraded"):
                return issue_scope
            return f'{scope}|{stage_reason.split(":", 1)[0]}'

        if (
            stages
            and stages <= set(stage_source)
            and all(
                (semantics.get("sources", {}).get(stage_source[stage]) or {}).get(
                    "status"
                )
                == "complete"
                for stage in stages
            )
            and prior_scopes
            and all(healthy_scopes.get(recovery_key(scope)) for scope in prior_scopes)
        ):
            result["incidents"][key] = {
                **old,
                "status": "recovered",
                "last_seen": result["as_of"],
                "historical_source_repaired": False,
            }
        elif old.get("status") == "active":
            result["incidents"][key] = {**old, "status": "historical_unresolved"}
    item = result["incidents"].get(key, {})
    if (
        item.get("status") in {"active", "recovered"}
        and item.get("notified_status") != item["status"]
    ):
        result["notification_pending"].append(key)


def _delay_source_number(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _delay_observation_grid(commit):
    """Read only the grid declared by this commit, never the newest default."""
    version = commit.get("observation_grid_version")
    horizons = commit.get("observation_horizons_sec")
    tolerance = commit.get("observation_tolerance_sec")
    if all(value in (None, "", "None") for value in (version, horizons, tolerance)):
        return "legacy_five_horizons_v1", _DELAY_LEGACY_HORIZONS
    if isinstance(horizons, str):
        try:
            horizons = json.loads(horizons)
        except (TypeError, ValueError):
            return None
    if (
        version != _DELAY_RESEARCH_GRID
        or not isinstance(horizons, list)
        or any(isinstance(value, bool) for value in horizons)
        or tuple(horizons) != _DELAY_RESEARCH_HORIZONS
        or _delay_source_number(tolerance) != 0.25
    ):
        return None
    return version, _DELAY_RESEARCH_HORIZONS


def pre_submit_delay_source_semantics(data_root, now, prior_cursor=None):
    """Incremental raw/compact/summary and intent receipts; no order authority."""
    from src.engine.scalping.pre_submit_delay_tuning import expected_route_for_session
    from src.engine.monitoring.ws_receive_expectation import (
        classify_delay_quote_collection,
        DELAY_COLLECTION_SCHEMA,
    )
    from src.engine.pipeline_event_summary import (
        IDENTITY_MODULUS,
        PRODUCER_SUMMARY_STAGES,
        execution_projection_identity,
        load_summary_rows,
        summary_event_from_payload,
    )

    now = stamp(now)
    day = now.date().isoformat()
    data_root = Path(data_root)
    raw_path = data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    prior_today = isinstance(prior_cursor, dict) and prior_cursor.get("date") == day
    previous = prior_cursor if prior_today else {}
    migrated = bool(previous and previous.get("delay_cursor_contract_version") != 5)
    if migrated:
        previous = {}
    if previous and (
        type(previous.get("offset")) is not int
        or not isinstance(previous.get("minutes"), dict)
        or not isinstance(previous.get("delay_events"), list)
        or stamp(previous.get("coverage_started_at")) is None
    ):
        previous = {}
    cursor = {
        "date": day,
        "delay_cursor_contract_version": 5,
        "offset": 0,
        "device": None,
        "inode": None,
        "coverage_started_at": None,
        "minutes": {},
        "delay_events": [],
    }
    issues, diagnostics, healthy, examples = Counter(), Counter(), Counter(), []
    collection_states, quote_eligibility = Counter(), Counter()
    collection_examples = []
    collection_failure_event_ids = set()
    confirmed_collection_failure_ids = set()
    horizon_states, horizon_states_by_grid, recheck_states = (
        Counter(),
        Counter(),
        Counter(),
    )
    policy_states, evidence_states, selected_delays = Counter(), Counter(), Counter()
    submit_latency = {"n": 0, "sum_sec": 0.0, "max_sec": None}
    if migrated:
        diagnostics["raw_cursor_contract_migrated"] += 1
    issue_scopes, healthy_scopes = Counter(), Counter()
    raw_status = "unobservable"
    indexed = None
    import sqlite3

    try:
        from src.engine.automation import main_trailing_source_store as raw_index

        indexed = raw_index.window(
            data_root,
            raw_path,
            cutoff=(
                now - timedelta(seconds=DELAY_WINDOW_SEC + DELAY_SUMMARY_GRACE_SEC + 60)
            ).isoformat(),
        )
    except (OSError, ValueError, sqlite3.Error) as exc:
        diagnostics["raw_native_index_pending:" + type(exc).__name__] += 1
    try:
        if indexed is not None:
            from types import SimpleNamespace

            metadata = indexed["generation"]["source_stat"]
            stat_before = SimpleNamespace(
                st_dev=metadata[0],
                st_ino=metadata[1],
                st_size=metadata[2],
                st_mtime_ns=metadata[3],
                st_ctime_ns=metadata[4],
            )
            same_file = True
            start = end = metadata[2]
            cursor.update(
                offset=metadata[2],
                device=metadata[0],
                inode=metadata[1],
                source_size=metadata[2],
                source_mtime_ns=metadata[3],
                source_ctime_ns=metadata[4],
                coverage_started_at=indexed["coverage_started_at"],
                minutes=indexed["minutes"],
                delay_events=[],
                native_raw_index_generation=indexed["generation"],
            )
            payload = b"".join(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode()
                + b"\n"
                for row in indexed["rows"]
            )
            diagnostics["raw_native_index_used"] += 1
            if indexed["verified_append_after_snapshot"]:
                diagnostics["raw_native_append_after_snapshot"] += 1
        else:
            stat_before = raw_path.stat()
            same_file = (previous.get("device"), previous.get("inode")) == (
                stat_before.st_dev,
                stat_before.st_ino,
            )
            # Inode/size alone do not identify a raw generation. A same-size
            # rewrite (including restored mtime) invalidates retained observations.
            if same_file and (
                previous.get("source_size") is None
                or (
                    stat_before.st_size == previous.get("source_size")
                    and (stat_before.st_mtime_ns, stat_before.st_ctime_ns)
                    != (
                        previous.get("source_mtime_ns"),
                        previous.get("source_ctime_ns"),
                    )
                )
            ):
                same_file = False
                diagnostics["raw_generation_rewritten_or_legacy_cursor"] += 1
            if same_file and 0 <= previous.get("offset", -1) <= stat_before.st_size:
                cursor.update(
                    {
                        key: copy.deepcopy(previous.get(key))
                        for key in (
                            "offset",
                            "coverage_started_at",
                            "minutes",
                            "delay_events",
                        )
                    }
                )
            else:
                reset_generation = prior_today
                cursor["coverage_started_at"] = (
                    f"{day}T00:00:00+09:00"
                    if not reset_generation and stat_before.st_size <= DELAY_RAW_BUDGET
                    else now.isoformat()
                )
                cursor["offset"] = (
                    0
                    if stat_before.st_size <= DELAY_RAW_BUDGET
                    else stat_before.st_size - DELAY_RAW_BUDGET
                )
            cursor.update(
                device=stat_before.st_dev,
                inode=stat_before.st_ino,
                source_size=stat_before.st_size,
                source_mtime_ns=stat_before.st_mtime_ns,
                source_ctime_ns=stat_before.st_ctime_ns,
            )
            start = cursor["offset"]
            end = min(stat_before.st_size, start + DELAY_RAW_BUDGET)
            with raw_path.open("rb") as handle:
                handle.seek(start)
                payload = handle.read(end - start)
            stat_after = raw_path.stat()
            if (stat_before.st_dev, stat_before.st_ino) != (
                stat_after.st_dev,
                stat_after.st_ino,
            ) or stat_after.st_size < end:
                raise ValueError("raw_generation_changed")
            if stat_after.st_size == stat_before.st_size and (
                stat_after.st_mtime_ns,
                stat_after.st_ctime_ns,
            ) != (stat_before.st_mtime_ns, stat_before.st_ctime_ns):
                raise ValueError("raw_generation_changed")
            if start and not same_file:
                if b"\n" not in payload:
                    raise ValueError("raw_tail_boundary_missing")
                payload = payload.partition(b"\n")[2]
                start = end - len(payload)
        complete_bytes = payload.rfind(b"\n") + 1
        malformed = indexed["source_gaps"] if indexed is not None else 0
        for line in payload[:complete_bytes].splitlines():
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("raw_event_not_object")
                at = stamp(row.get("emitted_at"))
                if at is None:
                    raise ValueError("raw_event_time_invalid")
                if at.date() != now.date():
                    continue
                event = summary_event_from_payload(
                    row, summary_stages=PRODUCER_SUMMARY_STAGES
                )
                if event is None:
                    continue
                # Keep every projected physical row before advancing its byte
                # cursor. A concurrent append can be later than this run's
                # as-of; its closed-minute bucket remains dormant until due.
                # Intent analysis below uses only rows visible at this as-of.
                if at > now:
                    diagnostics["raw_future_events_deferred"] += 1
                if indexed is None:
                    minute = event.emitted_at.replace(
                        second=0, microsecond=0
                    ).isoformat()
                    key = f"{minute}|{event.stage}"
                    item = cursor["minutes"].setdefault(
                        key, {"count": 0, "identity_sum": "0" * 64}
                    )
                    item["count"] += 1
                    item["identity_sum"] = (
                        f"{(int(item['identity_sum'], 16) + event.evidence_hash) % IDENTITY_MODULUS:064x}"
                    )
                if event.stage in DELAY_STAGES:
                    fields = (
                        row.get("fields") if isinstance(row.get("fields"), dict) else {}
                    )
                    cursor["delay_events"].append(
                        {
                            "stage": event.stage,
                            "at": at.isoformat(),
                            "event_id": execution_projection_identity(row),
                            "stock_code": str(row.get("stock_code") or ""),
                            "record_id": str(row.get("record_id") or ""),
                            "delay_intent_id": str(fields.get("delay_intent_id") or ""),
                            "anchor_kind": fields.get("anchor_kind") or "price_ready",
                            "anchor_contract_version": fields.get(
                                "anchor_contract_version"
                            ),
                            "situation_key": fields.get("situation_key"),
                            "situation_source_status": fields.get(
                                "situation_source_status"
                            ),
                            "observation_only": fields.get("observation_only"),
                            "observation_grid_version": fields.get(
                                "observation_grid_version"
                            ),
                            "observation_horizons_sec": fields.get(
                                "observation_horizons_sec"
                            ),
                            "observation_tolerance_sec": fields.get(
                                "observation_tolerance_sec"
                            ),
                            "quote_contract_version": fields.get(
                                "quote_contract_version"
                            ),
                            "quote_observed_at_epoch": fields.get(
                                "quote_observed_at_epoch"
                            ),
                            "actual_offset_sec": fields.get("actual_offset_sec"),
                            "quote_offset_sec": fields.get("quote_offset_sec"),
                            "target_due_at_epoch": fields.get("target_due_at_epoch"),
                            "decision_source_sha256": fields.get(
                                "decision_source_sha256"
                            ),
                            "recheck_status": fields.get("recheck_status"),
                            "successor_request_id": fields.get("successor_request_id"),
                            "successor_evaluation_attempt_id": fields.get(
                                "successor_evaluation_attempt_id"
                            ),
                            "recheck_submitted_at_epoch": fields.get(
                                "recheck_submitted_at_epoch"
                            ),
                            "recheck_completed_at_epoch": fields.get(
                                "recheck_completed_at_epoch"
                            ),
                            "recheck_deadline_epoch": fields.get(
                                "recheck_deadline_epoch"
                            ),
                            "due_at_epoch": fields.get("due_at_epoch"),
                            "terminal_reason": fields.get("terminal_reason"),
                            "submit_call_outcome": fields.get("submit_call_outcome"),
                            "target_delay_sec": fields.get("target_delay_sec"),
                            "selected_delay_sec": fields.get("selected_delay_sec"),
                            "delay_policy_status": fields.get("delay_policy_status"),
                            "delay_selection_basis": fields.get(
                                "delay_selection_basis"
                            ),
                            "delay_evidence_verdict": fields.get(
                                "delay_evidence_verdict"
                            ),
                            "submit_finished_at_epoch": fields.get(
                                "submit_finished_at_epoch"
                            ),
                            "route": str(fields.get("route") or ""),
                            "session_bucket": str(
                                fields.get("market_session_bucket") or ""
                            ),
                            "quote_route": str(fields.get("quote_route") or ""),
                            "quote_valid": fields.get("quote_valid"),
                            "quote_source_reason": fields.get("quote_source_reason"),
                            "quote_route_sequence": fields.get("quote_route_sequence"),
                            "quote_collection_evidence": fields.get(
                                "quote_collection_evidence"
                            ),
                            "quote_transport_epoch": fields.get(
                                "quote_transport_epoch"
                            ),
                            "route_depth_source_sha256": fields.get(
                                "route_depth_source_sha256"
                            ),
                            "ws_last_0d_epoch": fields.get("ws_last_0d_epoch"),
                            "ws_last_0d_age_sec": fields.get("ws_last_0d_age_sec"),
                            "decision_committed_at_epoch": fields.get(
                                "decision_committed_at_epoch"
                            ),
                            "terminal_finished_at_epoch": fields.get(
                                "terminal_finished_at_epoch"
                            ),
                        }
                    )
            except (ValueError, TypeError, UnicodeDecodeError, KeyError):
                malformed += 1
        cursor["offset"] = (
            stat_before.st_size if indexed is not None else start + complete_bytes
        )
        cutoff = now - timedelta(
            seconds=DELAY_WINDOW_SEC + DELAY_SUMMARY_GRACE_SEC + 60
        )
        cursor["minutes"] = {
            key: value
            for key, value in cursor["minutes"].items()
            if (stamp(key.split("|", 1)[0]) or now) >= cutoff
        }
        cursor["delay_events"] = [
            row for row in cursor["delay_events"] if stamp(row["at"]) >= cutoff
        ]
        raw_status = (
            "complete"
            if cursor["offset"] == stat_before.st_size
            and not malformed
            and stamp(cursor["coverage_started_at"])
            <= now - timedelta(seconds=DELAY_WINDOW_SEC)
            else "partial"
        )
        if raw_status == "complete":
            healthy["raw_cursor_backlog"] += 1
            healthy["raw_source_unobservable_with_summary"] += 1
            healthy_scopes["raw_cursor_backlog|raw"] += 1
            healthy_scopes["raw_source_unobservable_with_summary|raw"] += 1
        if malformed:
            issues["raw_malformed_event"] += malformed
        if (
            stat_before.st_size - cursor["offset"] > 1024 * 1024
            and end - start >= DELAY_RAW_BUDGET
        ):
            issues["raw_cursor_backlog"] += 1
            issue_scopes["raw_cursor_backlog|raw"] += 1
    except (OSError, ValueError, TypeError) as exc:
        raw_status = "unobservable"
        diagnostics[f"raw_unobservable:{type(exc).__name__}"] += 1
        if str(exc) == "raw_tail_boundary_missing":
            issues["raw_cursor_backlog"] += 1
            issue_scopes["raw_cursor_backlog|raw"] += 1

    summary_status = "unobservable"
    summary_minutes = {}
    manifest = {}
    summary_grace_sec = DELAY_SUMMARY_GRACE_SEC
    summary_dir = data_root / "pipeline_event_summaries"
    summary_path = summary_dir / f"pipeline_event_producer_summary_{day}.jsonl"
    manifest_path = summary_dir / f"pipeline_event_producer_summary_manifest_{day}.json"
    try:
        manifest_before = manifest_path.stat()
        if manifest_before.st_size > 2 * 1024 * 1024:
            raise ValueError("summary_manifest_budget_exceeded")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        before = summary_path.stat()
        if manifest.get("summary_storage_size_bytes") != before.st_size:
            raise ValueError("summary_generation_uncommitted")
        recent = manifest.get("recent_summary")
        if recent is not None:
            if (
                recent.get("schema") != "producer_recent_minutes_v1"
                or not isinstance(recent.get("rows"), list)
                or len(recent["rows"]) > 10000
                or recent.get("body_sha256")
                != hashlib.sha256(
                    json.dumps(
                        recent["rows"], sort_keys=True, separators=(",", ":")
                    ).encode()
                ).hexdigest()
                or stamp(recent.get("lower_bound")) is None
                or stamp(recent["lower_bound"])
                > now - timedelta(seconds=DELAY_WINDOW_SEC)
            ):
                raise ValueError("summary_recent_projection_invalid")
            rows = recent["rows"]
            diagnostics["summary_bounded_projection_used"] += 1
        else:
            if before.st_size > 64 * 1024 * 1024:
                raise ValueError("legacy_summary_read_budget_exceeded")
            rows = load_summary_rows(summary_path, include_samples=False, strict=True)
            diagnostics["summary_legacy_full_validation"] += 1
        after = summary_path.stat()
        manifest_after = manifest_path.stat()
        generation = lambda stat: (
            stat.st_dev,
            stat.st_ino,
            stat.st_size,
            stat.st_mtime_ns,
        )
        if (
            manifest.get("mode") != "shadow"
            or Path(str(manifest.get("summary_path") or "")).resolve()
            != summary_path.resolve()
            or generation(after) != generation(before)
            or generation(manifest_after) != generation(manifest_before)
            or (
                recent is None
                and manifest.get("summary_event_count")
                != sum(row["event_count"] for row in rows)
            )
        ):
            raise ValueError("summary_generation_changed")
        flush_interval = manifest.get("flush_interval_sec")
        if type(flush_interval) is int and flush_interval > 0:
            summary_grace_sec = max(DELAY_SUMMARY_GRACE_SEC, 2 * flush_interval + 30)
            if flush_interval > 120:
                issues["producer_summary_flush_interval_too_long"] += 1
                issue_scopes["producer_summary_flush_interval_too_long|producer"] += 1
            else:
                healthy["producer_summary_flush_interval_too_long"] += 1
                healthy_scopes["producer_summary_flush_interval_too_long|producer"] += 1
        for row in rows:
            if (
                row.get("target_date") != day
                or stamp(row.get("bucket_start")) is None
                or type(row.get("event_count")) is not int
                or row["event_count"] < 0
                or row.get("stage") not in PRODUCER_SUMMARY_STAGES
                or not isinstance(row.get("evidence_hash_sum"), str)
                or len(row["evidence_hash_sum"]) != 64
                or any(c not in "0123456789abcdef" for c in row["evidence_hash_sum"])
            ):
                raise ValueError("summary_projection_row_invalid")
            key = f"{row['bucket_start']}|{row['stage']}"
            item = summary_minutes.setdefault(
                key, {"count": 0, "identity_sum": "0" * 64}
            )
            item["count"] += row["event_count"]
            item["identity_sum"] = (
                f"{(int(item['identity_sum'], 16) + int(row['evidence_hash_sum'], 16)) % IDENTITY_MODULUS:064x}"
            )
        summary_status = "complete"
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        diagnostics[f"summary_unobservable:{type(exc).__name__}"] += 1
        diagnostics["summary_reason:" + str(exc)[:160]] += 1

    compact_status = "complete"
    compact_ids = set()
    compact_recent_ids = set()
    compact_duplicates = 0
    compact_dir = (
        data_root / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
    )
    try:
        total_bytes = 0
        for path in sorted(compact_dir.glob("part-execution-*.jsonl")):
            before = path.stat()
            total_bytes += before.st_size
            if path.is_symlink() or total_bytes > 8 * 1024 * 1024:
                raise ValueError("compact_source_unbounded")
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.endswith("\n"):
                        raise ValueError("compact_partial_line")
                    row = json.loads(line)
                    if (
                        row.get("emitted_date") != day
                        or row.get("family") != "pre_submit_delay"
                    ):
                        raise ValueError("compact_identity_invalid")
                    if row.get("stage") in DELAY_STAGES:
                        identity = str(row.get("execution_source_event_sha256") or "")
                        if identity != execution_projection_identity(row):
                            raise ValueError("compact_projection_identity_invalid")
                        if identity in compact_ids:
                            compact_duplicates += 1
                        compact_ids.add(identity)
                        emitted = stamp(row.get("emitted_at"))
                        if emitted and now - timedelta(
                            seconds=DELAY_WINDOW_SEC
                        ) <= emitted <= now - timedelta(seconds=20):
                            compact_recent_ids.add(identity)
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ValueError("compact_generation_changed")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        compact_status = "unobservable"
        diagnostics[f"compact_unobservable:{type(exc).__name__}"] += 1

    if raw_status == "complete":
        grace = now - timedelta(seconds=summary_grace_sec)
        window = now - timedelta(seconds=DELAY_WINDOW_SEC)
        visible_delay_events = [
            row for row in cursor["delay_events"] if stamp(row["at"]) <= now
        ]
        for key in set(cursor["minutes"]) | (
            set(summary_minutes) if summary_status == "complete" else set()
        ):
            minute = stamp(key.split("|", 1)[0])
            if minute is None or minute < window or minute > grace:
                continue
            raw_item = cursor["minutes"].get(
                key, {"count": 0, "identity_sum": "0" * 64}
            )
            summarized = summary_minutes.get(
                key, {"count": 0, "identity_sum": "0" * 64}
            )
            stage = key.split("|", 1)[1]
            if summary_status != "complete":
                if raw_item["count"]:
                    issues["producer_summary_unobservable_with_raw"] += 1
                    issue_scopes[f"producer_summary_unobservable_with_raw|{stage}"] += 1
                continue
            if raw_item != summarized:
                issues["producer_raw_summary_window_mismatch"] += 1
                issue_scopes[f"producer_raw_summary_window_mismatch|{stage}"] += 1
                if len(examples) < 3:
                    examples.append(
                        {
                            "reason": "producer_raw_summary_window_mismatch",
                            "window_stage": key,
                            "raw_count": raw_item["count"],
                            "summary_count": summarized["count"],
                        }
                    )
            elif raw_item["count"]:
                healthy["producer_raw_summary_window_mismatch"] += 1
                healthy_scopes[f"producer_raw_summary_window_mismatch|{stage}"] += 1
                healthy["producer_summary_unobservable_with_raw"] += 1
                healthy_scopes[f"producer_summary_unobservable_with_raw|{stage}"] += 1
        raw_recent_ids = set()
        raw_recent_identity_counts = Counter()
        commit_by_intent = {
            (
                row.get("stock_code", ""),
                row.get("record_id", ""),
                row["delay_intent_id"],
            ): row
            for row in visible_delay_events
            if row["stage"] == "pre_submit_delay_committed" and row["delay_intent_id"]
        }
        for row in visible_delay_events:
            at = stamp(row["at"])
            if at < window or at > now - timedelta(seconds=20):
                continue
            raw_recent_ids.add(row["event_id"])
            raw_recent_identity_counts[row["event_id"]] += 1
            if compact_status == "complete" and row["event_id"] not in compact_ids:
                issues["raw_compact_event_missing"] += 1
                issue_scopes[f"raw_compact_event_missing|{row['stage']}"] += 1
                if len(examples) < 3:
                    examples.append(
                        {
                            "reason": "raw_compact_event_missing",
                            "stage": row["stage"],
                            "delay_intent_id": row["delay_intent_id"],
                        }
                    )
            elif compact_status == "complete":
                healthy["raw_compact_event_missing"] += 1
                healthy_scopes[f"raw_compact_event_missing|{row['stage']}"] += 1
                healthy["compact_source_unobservable_with_raw"] += 1
                healthy_scopes[
                    f"compact_source_unobservable_with_raw|{row['stage']}"
                ] += 1
            else:
                issues["compact_source_unobservable_with_raw"] += 1
                issue_scopes[
                    f"compact_source_unobservable_with_raw|{row['stage']}"
                ] += 1
            if row["stage"] == "pre_submit_delay_committed":
                if str(row.get("anchor_contract_version")) == "4":
                    if row.get(
                        "situation_source_status"
                    ) != "native_machine_bound" or row.get("situation_key") in (
                        None,
                        "",
                        "UNKNOWN",
                    ):
                        issues["situation_source_unresolved"] += 1
                        issue_scopes[
                            "situation_source_unresolved|"
                            + row.get("anchor_kind", "price_ready")
                        ] += 1
                    else:
                        healthy["situation_source_unresolved"] += 1
                        healthy_scopes[
                            "situation_source_unresolved|"
                            + row.get("anchor_kind", "price_ready")
                        ] += 1
                else:
                    diagnostics["legacy_situation_not_recorded"] += 1
                expected_route = expected_route_for_session(row["session_bucket"])
                if not expected_route:
                    issues["committed_session_missing"] += 1
                    issue_scopes["committed_session_missing|UNKNOWN"] += 1
                elif row["route"] and row["route"].upper() != expected_route:
                    issues["committed_route_session_mismatch"] += 1
                    issue_scopes[
                        f"committed_route_session_mismatch|{row['session_bucket']}"
                    ] += 1
                else:
                    if not row["route"]:
                        diagnostics["committed_route_derived_from_session"] += 1
                    healthy["committed_session_missing"] += 1
                    healthy["committed_route_session_mismatch"] += 1
                    healthy_scopes["committed_session_missing|UNKNOWN"] += 1
                    healthy_scopes[
                        f"committed_route_session_mismatch|{row['session_bucket']}"
                    ] += 1
            if row["stage"] == "pre_submit_delay_quote_observed":
                commit = commit_by_intent.get(
                    (
                        row.get("stock_code", ""),
                        row.get("record_id", ""),
                        row["delay_intent_id"],
                    ),
                    {},
                )
                quote_scope = (
                    expected_route_for_session(commit.get("session_bucket"))
                    or commit.get("route")
                    or row["quote_route"]
                    or row["route"]
                    or "UNKNOWN"
                )
                valid = str(row["quote_valid"]).lower() == "true"
                collection_scope = f"{quote_scope}|{row['stock_code']}|{commit.get('session_bucket') or 'UNKNOWN'}"
                quote_eligibility["valid" if valid else "invalid"] += 1
                collection = classify_delay_quote_collection(
                    row, ledger_complete=raw_status == "complete"
                )
                collection_states[collection["state"]] += 1
                if len(collection_examples) < 8:
                    collection_examples.append(
                        dict(
                            delay_intent_id=row["delay_intent_id"],
                            target_delay_sec=row["target_delay_sec"],
                            stock_code=row["stock_code"],
                            quote_route=row["quote_route"],
                            quote_age_sec=row.get("ws_last_0d_age_sec"),
                            **collection,
                        )
                    )
                recent_loss = bool(collection.get("loss_event_id")) and (
                    0
                    <= now.timestamp() - collection["loss_observed_at_epoch"]
                    <= DELAY_WINDOW_SEC
                )
                fault = recent_loss or collection["state"] in {
                    "contract_invalid",
                    "collection_fault_confirmed",
                }
                stale = row["quote_source_reason"] == "depth_stale_or_clock_invalid"
                issue = (
                    "quote_collection_fault"
                    if fault
                    else (
                        "quote_collection_unobservable"
                        if not valid
                        and stale
                        and collection["state"] != "expected_wait"
                        else "quote_source_invalid" if not valid and not stale else None
                    )
                )
                if issue:
                    failure_id = collection.get("loss_event_id") or row["event_id"]
                    duplicate = failure_id in collection_failure_event_ids
                    collection_failure_event_ids.add(failure_id)
                    if (
                        recent_loss
                        or collection["state"] == "collection_fault_confirmed"
                    ):
                        confirmed_collection_failure_ids.add(failure_id)
                    if not duplicate:
                        issues[issue] += 1
                        issue_scopes[
                            f"{issue}|{quote_scope if issue == 'quote_source_invalid' else collection_scope}"
                        ] += 1
                    if not duplicate and len(examples) < 3:
                        examples.append(
                            {
                                "reason": (
                                    (
                                        "recent_wire_to_normalized_loss"
                                        if recent_loss
                                        else collection["reason"]
                                    )
                                    if issue != "quote_source_invalid"
                                    else row["quote_source_reason"]
                                    or "quote_source_invalid"
                                ),
                                "quote_source_reason": row["quote_source_reason"],
                                "stock_code": row["stock_code"],
                                "quote_route": row["quote_route"],
                                "stage": row["stage"],
                                "delay_intent_id": row["delay_intent_id"],
                                "collection_health": collection,
                                "quote_age_sec": row.get("ws_last_0d_age_sec"),
                            }
                        )
                elif valid:
                    if not row["quote_route"]:
                        diagnostics["quote_route_derived_from_session"] += 1
                    healthy["quote_source_invalid"] += 1
                    healthy_scopes[f"quote_source_invalid|{quote_scope}"] += 1
                    if collection["state"] == "locally_healthy":
                        for name in (
                            "quote_collection_fault",
                            "quote_collection_unobservable",
                        ):
                            healthy_scopes[f"{name}|{collection_scope}"] += 1
                else:
                    diagnostics["quote_stale_expected_wait"] += 1
        if any(count > 1 for count in raw_recent_identity_counts.values()):
            issues["raw_family_duplicate_identity"] += sum(
                count - 1 for count in raw_recent_identity_counts.values() if count > 1
            )
        if compact_status == "complete":
            if compact_duplicates:
                issues["compact_family_duplicate_identity"] += compact_duplicates
            healthy["compact_raw_event_missing"] += len(
                compact_recent_ids & raw_recent_ids
            )
            healthy_scopes["compact_raw_event_missing|pre_submit_delay"] += len(
                compact_recent_ids & raw_recent_ids
            )
            for identity in compact_recent_ids - raw_recent_ids:
                # A settled compact receipt without its raw parent is also a gap.
                issues["compact_raw_event_missing"] += 1
                issue_scopes["compact_raw_event_missing|pre_submit_delay"] += 1
                if len(examples) < 3:
                    examples.append(
                        {"reason": "compact_raw_event_missing", "event_id": identity}
                    )
        by_intent = {}
        for row in visible_delay_events:
            if not row["delay_intent_id"]:
                continue
            identity = (
                row.get("stock_code", ""),
                row.get("record_id", ""),
                row["delay_intent_id"],
            )
            group = by_intent.setdefault(
                identity,
                {"commit": None, "quote_rows": [], "terminals": [], "rechecks": []},
            )
            if row["stage"] == "pre_submit_delay_committed":
                group["commit"] = row
            elif row["stage"] == "pre_submit_delay_quote_observed":
                group["quote_rows"].append(row)
            elif row["stage"] == "pre_submit_delay_intent_terminal":
                group["terminals"].append(row)
            elif row["stage"] == "pre_submit_delay_recheck_observed":
                group["rechecks"].append(row)
        for identity, group in by_intent.items():
            commit = group["commit"]
            if not commit:
                for quote in group["quote_rows"]:
                    if (
                        _delay_source_number(quote.get("target_delay_sec"))
                        not in _DELAY_RESEARCH_HORIZONS
                    ):
                        issues["quote_horizon_invalid"] += 1
                continue
            committed_route = (
                commit["route"]
                or expected_route_for_session(commit["session_bucket"])
                or ""
            )
            scope = committed_route or "UNKNOWN"
            grid = _delay_observation_grid(commit)
            if grid is None:
                issues["observation_grid_contract_invalid"] += 1
                issue_scopes[f"observation_grid_contract_invalid|{scope}"] += 1
            grid_version, expected_horizons = grid or ("invalid", ())
            observation_only = (
                commit.get("anchor_kind") == "signal_ready"
                or str(commit.get("observation_only")).lower() == "true"
            )
            committed_epoch = _delay_source_number(
                commit.get("decision_committed_at_epoch")
            )
            committed_epoch = (
                committed_epoch
                if committed_epoch is not None
                else stamp(commit["at"]).timestamp()
            )
            age = now.timestamp() - committed_epoch
            decision_hash = commit.get("decision_source_sha256")
            bound_terminals, bound_rechecks, quotes = [], [], {}
            for receipt in group["terminals"] + group["rechecks"] + group["quote_rows"]:
                if (
                    decision_hash
                    and receipt.get("decision_source_sha256") != decision_hash
                ):
                    issues["intent_decision_binding_invalid"] += 1
                    issue_scopes[f"intent_decision_binding_invalid|{scope}"] += 1
                    continue
                if receipt["stage"] == "pre_submit_delay_intent_terminal":
                    if not receipt.get("terminal_reason") and receipt.get(
                        "submit_call_outcome"
                    ) not in {
                        "broker_accepted",
                        "returned_true",
                        "returned_false",
                        "returned_other",
                        "raised",
                        "not_returned",
                    }:
                        issues["intent_terminal_receipt_invalid"] += 1
                        issue_scopes[f"intent_terminal_receipt_invalid|{scope}"] += 1
                        continue
                    bound_terminals.append(receipt)
                    continue
                if receipt["stage"] == "pre_submit_delay_recheck_observed":
                    bound_rechecks.append(receipt)
                    continue
                quote = receipt
                if (
                    quote["route"] and quote["route"].upper() != committed_route.upper()
                ) or (
                    quote["quote_route"]
                    and quote["quote_route"].upper() != committed_route.upper()
                ):
                    issues["quote_commit_route_mismatch"] += 1
                    issue_scopes[f"quote_commit_route_mismatch|{scope}"] += 1
                else:
                    healthy["quote_commit_route_mismatch"] += 1
                    healthy_scopes[f"quote_commit_route_mismatch|{scope}"] += 1
                horizon = _delay_source_number(quote.get("target_delay_sec"))
                if horizon not in expected_horizons:
                    issues["quote_horizon_invalid"] += 1
                    issue_scopes[f"quote_horizon_invalid|{scope}"] += 1
                    continue
                observed_epoch = _delay_source_number(
                    quote.get("quote_observed_at_epoch")
                )
                observed_offset = _delay_source_number(quote.get("actual_offset_sec"))
                if observed_offset is None:
                    observed_offset = _delay_source_number(
                        quote.get("quote_offset_sec")
                    )
                short_contract_invalid = horizon in (1, 3, 5) and (
                    str(quote.get("quote_contract_version")) != "2"
                    or quote.get("observation_grid_version") != _DELAY_RESEARCH_GRID
                    or _delay_source_number(quote.get("observation_tolerance_sec"))
                    != 0.25
                    or _delay_source_number(quote.get("target_due_at_epoch"))
                    != committed_epoch + horizon
                    or observed_epoch is None
                    or observed_offset is None
                    or abs((observed_epoch - committed_epoch) - observed_offset) > 0.001
                )
                if short_contract_invalid:
                    issues["short_quote_contract_invalid"] += 1
                    issue_scopes[f"short_quote_contract_invalid|{scope}"] += 1
                if horizon in quotes:
                    issues["quote_horizon_duplicate"] += 1
                    issue_scopes[f"quote_horizon_duplicate|{scope}"] += 1
                else:
                    quotes[horizon] = dict(
                        quote, source_contract_invalid=short_contract_invalid
                    )
            actual_terminals = [
                row
                for row in bound_terminals
                if str(row.get("observation_only")).lower() != "true"
            ]
            observation_terminals = [
                row
                for row in bound_terminals
                if str(row.get("observation_only")).lower() == "true"
            ]
            actual_terminal = actual_terminals[-1] if actual_terminals else None
            if len(actual_terminals) > 1:
                issues["intent_terminal_duplicate"] += len(actual_terminals) - 1
                issue_scopes[f"intent_terminal_duplicate|{scope}"] += (
                    len(actual_terminals) - 1
                )
            # A late shutdown/censor receipt cannot erase already-overdue
            # missing observations. An order terminal does not stop research.
            closure_epoch = min(
                (stamp(row["at"]).timestamp() for row in observation_terminals),
                default=None,
            )
            for horizon in expected_horizons:
                quote = quotes.get(horizon)
                if quote is not None:
                    offset = _delay_source_number(quote.get("actual_offset_sec"))
                    if offset is None:
                        offset = _delay_source_number(quote.get("quote_offset_sec"))
                    observed = _delay_source_number(
                        quote.get("quote_observed_at_epoch")
                    )
                    if observed is not None:
                        # The legacy producer rounded actual_offset_sec to
                        # milliseconds; classify timing from the source clock.
                        offset = observed - committed_epoch
                    tolerance = 0.25 if horizon in (1, 3, 5) else 3.0
                    lower = horizon if horizon in (1, 3, 5) else horizon - tolerance
                    if quote.get("source_contract_invalid"):
                        state = "observed_invalid"
                    elif offset is not None and (
                        offset < lower or offset > horizon + tolerance
                    ):
                        state = "observed_late_or_early"
                        if str(quote.get("quote_valid")).lower() == "true":
                            issues["quote_clock_validity_conflict"] += 1
                            issue_scopes[f"quote_clock_validity_conflict|{scope}"] += 1
                    else:
                        state = (
                            "observed_valid"
                            if str(quote.get("quote_valid")).lower() == "true"
                            else "observed_invalid"
                        )
                    healthy["observation_horizon_missing"] += 1
                    healthy_scopes[
                        f"observation_horizon_missing|{scope}|{grid_version}|{horizon:g}"
                    ] += 1
                elif (
                    closure_epoch is not None
                    and closure_epoch <= committed_epoch + horizon + 30
                ):
                    state = "censored"
                elif age < horizon:
                    state = "not_due"
                elif age < horizon + 30:
                    # Raw evidence alone cannot prove that an absent row is
                    # queued. Keep the established persistence grace explicit.
                    state = "persistence_pending"
                else:
                    state = "missing"
                    if horizon:
                        issues["observation_horizon_missing"] += 1
                        issue_scopes[
                            f"observation_horizon_missing|{scope}|{grid_version}|{horizon:g}"
                        ] += 1
                        if len(examples) < 3:
                            examples.append(
                                dict(
                                    reason="observation_horizon_missing",
                                    delay_intent_id=identity[2],
                                    stock_code=identity[0],
                                    record_id=identity[1],
                                    target_delay_sec=horizon,
                                    observation_grid_version=grid_version,
                                )
                            )
                horizon_states[state] += 1
                horizon_states_by_grid[f"{grid_version}|{horizon:g}|{state}"] += 1
            if (
                grid
                and age >= 30
                and 0 not in quotes
                and not (
                    closure_epoch is not None and closure_epoch <= committed_epoch + 30
                )
            ):
                issues["zero_second_quote_missing"] += 1
                issue_scopes[f"zero_second_quote_missing|{scope}"] += 1
                if len(examples) < 3:
                    examples.append(
                        {
                            "reason": "zero_second_quote_missing",
                            "delay_intent_id": identity[2],
                            "stock_code": identity[0],
                            "record_id": identity[1],
                        }
                    )
            elif 0 in quotes:
                healthy["zero_second_quote_missing"] += 1
                healthy_scopes[f"zero_second_quote_missing|{scope}"] += 1
            observation_complete = bool(expected_horizons) and set(
                expected_horizons
            ) <= set(quotes)
            if observation_complete:
                healthy["observation_completed"] += 1
            if observation_only:
                diagnostics["observation_only_no_order_terminal_required"] += 1
                # Retain the existing healthy key for compatible alert closure;
                # no broker terminal is inferred or manufactured here.
                healthy["intent_terminal_missing"] += 1
                healthy_scopes[f"intent_terminal_missing|{scope}"] += 1
            elif age >= 300 and actual_terminal is None:
                issues["intent_terminal_missing"] += 1
                issue_scopes[f"intent_terminal_missing|{scope}"] += 1
            elif actual_terminal is not None:
                healthy["intent_terminal_missing"] += 1
                healthy_scopes[f"intent_terminal_missing|{scope}"] += 1
            if (
                not observation_only
                and observation_terminals
                and actual_terminal is None
            ):
                diagnostics["observation_terminal_does_not_close_order_intent"] += 1
            selected = _delay_source_number(commit.get("selected_delay_sec"))
            if selected not in _DELAY_RESEARCH_HORIZONS:
                selected = None
                if not observation_only:
                    diagnostics["selected_due_instrumentation_gap"] += 1
            if not observation_only:
                from src.engine.scalping.pre_submit_delay_initial_policy import (
                    selection_evidence,
                )

                policy_states[
                    str(commit.get("delay_policy_status") or "unobserved")
                ] += 1
                evidence = selection_evidence(
                    {
                        "delay_sec": selected,
                        "selection_basis": commit.get("delay_selection_basis"),
                        "runtime_apply_allowed": commit.get("delay_policy_status")
                        == "loaded",
                    }
                )
                evidence_states[evidence] += 1
                if selected is not None:
                    selected_delays[f"{selected:g}"] += 1
                finished = _delay_source_number(
                    (actual_terminal or {}).get("submit_finished_at_epoch")
                )
                if (
                    finished is not None
                    and committed_epoch <= finished <= now.timestamp()
                ):
                    elapsed = finished - committed_epoch
                    submit_latency["n"] += 1
                    submit_latency["sum_sec"] += elapsed
                    submit_latency["max_sec"] = max(
                        submit_latency["max_sec"] or 0, elapsed
                    )
            valid_rechecks = []
            for row in bound_rechecks:
                status = row.get("recheck_status")
                due = _delay_source_number(row.get("due_at_epoch"))
                submitted = _delay_source_number(row.get("recheck_submitted_at_epoch"))
                completed = _delay_source_number(row.get("recheck_completed_at_epoch"))
                deadline = _delay_source_number(row.get("recheck_deadline_epoch"))
                if (
                    not decision_hash
                    or selected in (None, 0)
                    or status not in {"admitted", "completed", "expired", "not_ready"}
                    or due != committed_epoch + selected
                    or (
                        status in {"admitted", "completed"}
                        and (
                            not row.get("successor_request_id")
                            or submitted is None
                            or deadline is None
                            or submitted < due
                            or submitted > deadline
                        )
                    )
                    or (
                        status == "completed"
                        and (completed is None or completed < submitted)
                    )
                ):
                    issues["recheck_receipt_invalid"] += 1
                    issue_scopes[f"recheck_receipt_invalid|{scope}"] += 1
                    continue
                valid_rechecks.append(row)
                recheck_states[status] += 1
            if (
                not observation_only
                and selected
                and age >= selected + 30
                and actual_terminal is None
            ):
                last_recheck = max(
                    valid_rechecks, key=lambda row: stamp(row["at"]), default=None
                )
                deadline = _delay_source_number(
                    (last_recheck or {}).get("recheck_deadline_epoch")
                )
                if (
                    last_recheck
                    and last_recheck.get("recheck_status") == "admitted"
                    and deadline is not None
                    and now.timestamp() <= deadline
                ):
                    diagnostics["selected_due_recheck_pending"] += 1
                else:
                    issues["selected_due_completion_missing"] += 1
                    issue_scopes[f"selected_due_completion_missing|{scope}"] += 1
                    if len(examples) < 3:
                        examples.append(
                            dict(
                                reason="selected_due_completion_missing",
                                delay_intent_id=identity[2],
                                stock_code=identity[0],
                                record_id=identity[1],
                                selected_delay_sec=selected,
                                original_commit_at=commit["at"],
                                source_request_status=(last_recheck or {}).get(
                                    "recheck_status", "instrumentation_gap"
                                ),
                            )
                        )
    elif summary_status == "complete" and any(
        stamp(key.split("|", 1)[0]) >= now - timedelta(seconds=DELAY_WINDOW_SEC)
        for key in summary_minutes
    ):
        if raw_status == "unobservable":
            issues["raw_source_unobservable_with_summary"] += 1
            issue_scopes["raw_source_unobservable_with_summary|raw"] += 1
        else:
            # A new/migrated cursor has not observed a complete window yet.
            # Malformed rows/backlog already have their own explicit findings.
            diagnostics["raw_observation_window_pending"] += 1
    status = (
        "gap_observed"
        if issues
        else (
            "observed_no_gap"
            if raw_status == summary_status == compact_status == "complete"
            else "unobservable"
        )
    )
    return {
        "schema": "pre_submit_delay_intraday_source_semantics_v1",
        "as_of": now.isoformat(),
        "status": status,
        "metric_role": "source_quality_gate",
        "decision_authority": "report_only",
        "window_policy": "current_10m_incremental_raw_closed_minute_configured_flush_grace",
        "summary_grace_sec": summary_grace_sec,
        "sample_floor": "one_exact_stage_receipt",
        "primary_decision_metric": "source_gap_events_by_stage_and_reason",
        "source_quality_gate": "complete_raw_cursor_and_exact_current_day_source_generation",
        "forbidden_uses": [
            "order_authority",
            "threshold_change",
            "missing_as_zero_ev",
            "historical_source_repair_claim",
        ],
        "sources": {
            "raw": raw_status,
            "summary": summary_status,
            "compact": compact_status,
        },
        "issues": dict(sorted(issues.items())),
        "diagnostics": dict(sorted(diagnostics.items())),
        "healthy": dict(sorted(healthy.items())),
        "horizon_states": dict(sorted(horizon_states.items())),
        "collection_classification_version": DELAY_COLLECTION_SCHEMA,
        "collection_health_counts": dict(sorted(collection_states.items())),
        "collection_fault_event_count": len(confirmed_collection_failure_ids),
        "quote_eligibility_counts": dict(sorted(quote_eligibility.items())),
        "collection_examples": collection_examples,
        "collection_failure_event_ids": sorted(collection_failure_event_ids),
        "horizon_states_by_grid": dict(sorted(horizon_states_by_grid.items())),
        "recheck_states": dict(sorted(recheck_states.items())),
        "policy_status_counts": dict(sorted(policy_states.items())),
        "policy_evidence_counts": dict(sorted(evidence_states.items())),
        "selected_delay_counts": dict(sorted(selected_delays.items())),
        "commit_to_submit_return_sec": submit_latency,
        "issues_by_scope": dict(sorted(issue_scopes.items())),
        "healthy_by_scope": dict(sorted(healthy_scopes.items())),
        "examples": examples,
        "summary_last_writer_pid": manifest.get("last_writer_pid"),
        "summary_updated_at": manifest.get("updated_at"),
        "summary_flush_error_count": manifest.get("flush_error_count"),
        "cursor": cursor,
        "runtime_effect": False,
    }


def attach_pre_submit_delay_source_semantics(result, semantics):
    result["pre_submit_delay_source_semantics"] = {
        k: v for k, v in semantics.items() if k != "cursor"
    }
    result["pre_submit_delay_source_cursor"] = semantics["cursor"]
    result["status"] = semantics["status"]
    result["blocker"] = next(iter(semantics["issues"]), None)
    key = "pre_submit_delay_intraday_source_gap"
    old = result["incidents"].get(key, {})
    if semantics["issues"]:
        result["incidents"][key] = {
            "scope": "pre_submit_delay|exact_current_day",
            "rule": key,
            "category": "structural_evidence",
            "status": "active",
            "first_seen": old.get("first_seen", result["as_of"]),
            "last_seen": result["as_of"],
            "count": sum(semantics["issues"].values()),
            "issues": semantics["issues"],
            "issues_by_scope": semantics["issues_by_scope"],
            "evidence_ids": semantics.get("collection_failure_event_ids", []),
            "examples": semantics["examples"],
            "owner": "pipeline_event_logger|pre_submit_delay_tuning",
            "closure_test": "new exact raw_compact_summary and route_bound quote receipts",
            "notified_status": (
                old.get("notified_status")
                if set(semantics["issues"]) <= set(old.get("issues") or {})
                and set(semantics["issues_by_scope"])
                <= set(old.get("issues_by_scope") or {})
                and set(semantics.get("collection_failure_event_ids", []))
                <= set(old.get("evidence_ids") or [])
                and sum(semantics["issues"].values()) <= old.get("count", 0)
                else None
            ),
        }
    elif (
        old.get("status") in {"active", "historical_unresolved"}
        and semantics["status"] == "observed_no_gap"
        and all(
            semantics["healthy_by_scope"].get(scope, 0)
            for scope in old.get("issues_by_scope", {})
        )
        and old.get("issues_by_scope")
        and semantics["sources"]["raw"] == "complete"
        and semantics["sources"]["summary"] == "complete"
        and semantics["sources"]["compact"] == "complete"
    ):
        result["incidents"][key] = {
            **old,
            "status": "recovered",
            "last_seen": result["as_of"],
            "historical_source_repaired": False,
        }
    elif old.get("status") == "active" and semantics["status"] == "observed_no_gap":
        result["incidents"][key] = {
            **old,
            "status": "historical_unresolved",
            "last_seen": result["as_of"],
        }
    item = result["incidents"].get(key, {})
    if (
        item.get("status") in {"active", "recovered"}
        and item.get("notified_status") != item["status"]
    ):
        result["notification_pending"].append(key)


ECONOMIC_STAGES = frozenset(
    {"entry_ai_economic_plan_observed", "entry_ai_economic_source_gap"}
)


def economic_evidence(fields, stock_code=None):
    """Project frozen producer proof, without replay, account reads or inferred values."""
    from src.engine.scalping.strategy_owner_replay import (
        _entry_seed_valid,
        entry_conditional_capital_envelope,
    )
    from src.engine.scalping.strategy_owner_components import digest

    status = fields.get("entry_economic_source_status")
    blocker = str(fields.get("entry_economic_source_blocker") or "")
    result = {
        "status": status,
        "blocker": blocker or None,
        "capacity_blocker": fields.get("entry_economic_capacity_blocker") or None,
        "owner": fields.get("entry_economic_source_owner")
        or "main_entry_execution_owners",
        "closure_test": fields.get("entry_economic_source_closure_test")
        or "exact frozen plan/cost/capital source reaches evaluator",
        "plan_sha256": fields.get("entry_economic_plan_sha256"),
        "valid_economics": False,
    }
    guard = fields.get("entry_economic_guard_receipt")
    if isinstance(guard, str):
        try:
            guard = json.loads(guard)
        except (ValueError, TypeError):
            guard = None
    if isinstance(guard, dict):
        result["observation_guard"] = guard
    if status != "recorded_source_only":
        if (
            blocker.startswith("common_guard_block:")
            or blocker == "owner_sizing_zero_or_invalid"
        ):
            result["status"] = "guard_excluded"
        elif status == "unsupported_scope":
            result["status"] = "unsupported_scope"
        else:
            result["status"] = "source_gap"
            result["blocker"] = blocker or "economic_producer_status_missing"
        return result
    try:
        seed = fields.get("entry_opportunity_replay_seed")
        seed = json.loads(seed) if isinstance(seed, str) else seed
        if (
            isinstance(seed, dict)
            and seed.get("schema") == "entry_probe_conditional_plan_v1"
        ):
            from src.engine.scalping.entry_probe_conditional_replay import (
                valid_seed,
                operating_source_gaps,
            )

            if (
                not valid_seed(seed)
                or seed["plan_sha256"]
                != fields.get("entry_execution_sizing_plan_sha256")
                or seed["plan_sha256"] != fields.get("entry_economic_plan_sha256")
                or seed["plan_sha256"]
                != fields.get("entry_economic_writer_plan_sha256")
                or seed["evaluation_attempt_id"] != fields.get("evaluation_attempt_id")
                or seed["scanner_promotion_id"] != fields.get("scanner_promotion_id")
                or (stock_code and stock_code != seed["stock_code"])
                or seed["effective_venue"] != fields.get("effective_venue")
                or seed["session_bucket"]
                != (fields.get("session_bucket") or fields.get("market_session_bucket"))
            ):
                raise ValueError("economic_conditional_seed_binding_invalid")
            result.update(
                status="recorded_conditional_source_only",
                blocker="conditional_execution_outcome_not_observed",
                seed_sha256=seed["seed_sha256"],
                evaluation_role="frozen_conditional_plan_not_paired_economics",
            )
            result["operating_source_gaps"] = operating_source_gaps(seed)
            return result
        if not _entry_seed_valid(seed) or seed.get("plan_sha256") != fields.get(
            "entry_execution_sizing_plan_sha256"
        ):
            raise ValueError("economic_seed_or_plan_binding_invalid")
        for key, field in (
            ("scanner_promotion_id", "scanner_promotion_id"),
            ("evaluation_attempt_id", "evaluation_attempt_id"),
        ):
            if seed.get(key) != fields.get(field):
                raise ValueError("economic_attempt_binding_invalid:" + key)
        if stock_code and seed.get("stock_code") != stock_code:
            raise ValueError("economic_symbol_binding_invalid")
        if fields.get("entry_economic_plan_sha256") != seed.get("plan_sha256"):
            raise ValueError("economic_published_plan_hash_mismatch")
        context = seed.get("operating_contract") or {}
        if not context or context.get("sha256") != digest(
            {k: v for k, v in context.items() if k != "sha256"}
        ):
            raise ValueError("economic_operating_contract_missing_or_hash_invalid")
        for name in (
            "cost_provenance",
            "cost_policy_version",
            "exit_policy_version",
            "initial_fill_exit_state",
            "order_leg_ttl_sec",
        ):
            if not context.get(name):
                raise ValueError("economic_operating_field_missing:" + name)
        if (
            any(
                type(context.get(k)) not in (int, float)
                or not math.isfinite(context[k])
                for k in ("budget_krw", "cost_rate")
            )
            or not 0 <= context["cost_rate"] < 1
        ):
            raise ValueError("economic_budget_or_cost_invalid")
        if (
            not 0
            < sum(x["qty"] * x["price"] for x in seed["legs"])
            <= context["budget_krw"]
        ):
            raise ValueError("economic_frozen_reserve_budget_invalid")
        capital = context.get("capital_source") or {}
        if capital.get("status") != "recorded_source_only":
            raise ValueError(
                "economic_capital_source:" + str(capital.get("blocker") or "missing")
            )
        if capital.get("sha256") != digest(
            {k: v for k, v in capital.items() if k != "sha256"}
        ):
            raise ValueError("economic_capital_source_hash_invalid")
        entry_conditional_capital_envelope([seed])
        result.update(
            status="recorded_source_only",
            blocker=None,
            seed_sha256=seed["seed_sha256"],
            capital_source_sha256=capital["sha256"],
            evaluation_role="source_contract_only_not_model_validation",
        )
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        result.update(status="source_gap", blocker=str(exc))
    return result


def async_disposition_coverage(
    events, as_of, *, pass_projections=(), source_coverage=None
):
    """Count exact retained PASS attempts per PID/start; never infer missing finals."""
    now = stamp(as_of)
    attempts = {}
    retained = []
    retained_fingerprints = set()
    identity_fields = (
        "evaluation_attempt_id",
        "ai_decision_trace_id",
        "scanner_generation_id",
        "native_event_id",
        "native_signal_id",
        "effective_venue",
        "async_order_venue",
        "async_origin_snapshot_id",
        "entry_machine_bundle_sha256",
        "entry_auxiliary_policy_sha256",
        "watch_origin",
        "watch_admission_id",
        "watch_generation_id",
        "scanner_promotion_id",
        "async_origin_deadline_epoch",
    )
    missing = {"", "-", "none", "null", "unknown"}
    from types import SimpleNamespace

    sources = [(event, False) for event in events] + [
        (
            SimpleNamespace(
                stage="entry_async_disposition",
                emitted_at=p.get("emitted_at"),
                stock_code=p.get("stock_code"),
                fields=p.get("fields") or {},
            ),
            True,
        )
        for p in pass_projections
    ]
    for event, derived in sources:
        emitted = stamp(event.emitted_at)
        if (
            event.stage != "entry_async_disposition"
            or now is None
            or emitted is None
            or emitted > now
        ):
            continue
        f = event.fields
        occurred = f.get("async_disposition_epoch")
        try:
            at = (
                datetime.fromtimestamp(float(occurred), tz=now.tzinfo)
                if occurred not in (None, "")
                else emitted
            )
        except (ValueError, TypeError, OverflowError, OSError):
            continue
        if at > now or (now - at).total_seconds() > SOURCE_WINDOW_SEC:
            continue
        identity = tuple(
            str(f.get(k) or "")
            for k in (
                "async_producer_pid",
                "async_producer_start_ticks",
                "async_request_id",
            )
        )
        if any(
            v.lower().strip() in {"", "-", "none", "null", "unknown", "0"}
            for v in identity
        ):
            continue
        row = attempts.setdefault(
            identity, {"events": {}, "conflict": False, "binding": {}, "post_entry": {}}
        )
        for key in (*identity_fields, "stock_code"):
            value = event.stock_code if key == "stock_code" else f.get(key)
            if str(value or "").strip().lower() in missing:
                continue  # Early unavailable IDs never borrow current stock IDs.
            if key == "async_origin_deadline_epoch":
                try:
                    value = float(value)
                    if not math.isfinite(value):
                        raise ValueError()
                except (ValueError, TypeError):
                    row["conflict"] = True
                    continue
            value = str(value)
            if key in row["binding"] and row["binding"][key] != value:
                row["conflict"] = True
            row["binding"][key] = value
        eid = f.get("async_disposition_event_id")
        content = (
            f.get("async_disposition"),
            f.get("async_disposition_reason"),
            f.get("async_machine_action"),
            f.get("async_auxiliary_status"),
            f.get("async_auxiliary_verdict"),
            f.get("async_provider_called"),
            f.get("async_origin_deadline_epoch"),
            f.get("ai_decision_trace_id"),
            f.get("evaluation_attempt_id"),
            f.get("scanner_generation_id"),
            f.get("async_disposition_epoch"),
            f.get("async_entry_submit_attempt_id"),
            f.get("async_entry_broker_attempts"),
            f.get("async_entry_broker_accepted"),
            f.get("async_entry_submit_outcome"),
            f.get("async_entry_physical_send_blocked"),
            f.get("async_entry_physical_send_attempts"),
            f.get("async_entry_arm_released"),
        )
        if not eid or eid in row["events"] and row["events"][eid] != content:
            row["conflict"] = True
        row["events"][eid] = content
        row["pass"] = row.get("pass", False) or (
            str(f.get("async_machine_action")).upper() == "ENTER_NOW"
            and str(f.get("async_auxiliary_status")).lower() == "pass"
            and str(f.get("async_auxiliary_verdict")).upper() == "PASS"
            and str(f.get("async_provider_called")).lower() == "true"
        )
        row["deadline"] = row["binding"].get("async_origin_deadline_epoch")
        if f.get("async_disposition") == "entry_path_returned":
            post_entry = {
                k: f.get(k)
                for k in (
                    "async_disposition_reason",
                    "async_entry_submit_attempt_id",
                    "async_entry_broker_attempts",
                    "async_entry_broker_accepted",
                    "async_entry_submit_outcome",
                    "async_entry_physical_send_blocked",
                    "async_entry_physical_send_attempts",
                    "async_entry_arm_released",
                )
            }
            if row["post_entry"] and row["post_entry"] != post_entry:
                row["conflict"] = True
            row["post_entry"] = post_entry
        projection = dict(
            emitted_at=event.emitted_at,
            stock_code=event.stock_code,
            fields={
                k: f.get(k)
                for k in (
                    *identity_fields,
                    "async_producer_pid",
                    "async_producer_start_ticks",
                    "async_request_id",
                    "async_disposition_event_id",
                    "async_disposition",
                    "async_disposition_reason",
                    "async_disposition_epoch",
                    "async_machine_action",
                    "async_auxiliary_status",
                    "async_auxiliary_verdict",
                    "async_provider_called",
                    "async_entry_submit_attempt_id",
                    "async_entry_broker_attempts",
                    "async_entry_broker_accepted",
                    "async_entry_submit_outcome",
                    "async_entry_physical_send_blocked",
                    "async_entry_physical_send_attempts",
                    "async_entry_arm_released",
                )
            },
        )
        fingerprint = json.dumps(projection, sort_keys=True, default=str)
        # Derived PASS contributes to the denominator, never native closure.
        if not derived and fingerprint not in retained_fingerprints:
            retained_fingerprints.add(fingerprint)
            retained.append(projection)
    by_producer = {}
    for identity, row in attempts.items():
        if not row.get("pass"):
            continue
        counts = by_producer.setdefault(
            ":".join(identity[:2]),
            dict(
                pass_count=0,
                accepted=0,
                rejected=0,
                pending=0,
                unobservable=0,
                accepted_submit_observed=0,
                accepted_direct_guard=0,
                accepted_post_entry_unobservable=0,
            ),
        )
        states = {entry[0] for entry in row["events"].values()}
        finals = states & {
            "accepted_to_entry_path",
            "rejected",
            "terminal_nonexecution",
        }
        if row["conflict"] or len(finals) > 1:
            status = "unobservable"
        elif finals:
            status = "accepted" if "accepted_to_entry_path" in finals else "rejected"
        else:
            try:
                deadline = float(row["deadline"])
                status = (
                    "pending"
                    if math.isfinite(deadline) and now.timestamp() < deadline
                    else "unobservable"
                )
            except (TypeError, ValueError):
                status = "unobservable"
        counts["pass_count"] += 1
        counts[status] += 1
        if status == "accepted":
            post = row["post_entry"]
            if (
                str(post.get("async_entry_broker_attempts") or "0").isdigit()
                and int(post.get("async_entry_broker_attempts") or 0) > 0
            ):
                counts["accepted_submit_observed"] += 1
            elif post.get("async_disposition_reason") not in (
                None,
                "",
                "entry_path_returned_without_terminal_evidence",
                "entry_execution_exception_or_uncertain",
            ):
                counts["accepted_direct_guard"] += 1
            else:
                counts["accepted_post_entry_unobservable"] += 1
    return dict(
        schema="main_async_disposition_coverage_v1",
        by_producer=by_producer,
        metric_role="source_quality_gate",
        decision_authority="report_only",
        primary_decision_metric="pass_to_main_disposition_coverage",
        window_policy="current_pid_exact_attempt_with_carry_in_out",
        sample_floor="none",
        source_quality_gate="exact_pid_start_request_and_validated_pass",
        coverage=(
            "bounded_trace_projection_complete"
            if source_coverage == "complete" and len(retained) <= 1024
            else "loaded_evidence_only_full_denominator_unobservable"
        ),
        denominator_partial=source_coverage != "complete" or len(retained) > 1024,
        attempt_projection=retained[-1024:],
        forbidden_uses=["order_authority", "policy_promotion", "economics"],
    )


def snapshot(events, as_of):
    """Reuse already loaded events and the existing identity/terminal owner."""
    from src.engine.buy_funnel_sentinel import (
        _machine_primary_entry_funnel,
        _is_machine_primary_event,
        _machine_primary_evaluation_key,
        _machine_primary_identity_components,
        _machine_primary_fixed_watch_identity_components,
        _machine_primary_fixed_watch_identity_valid,
    )

    now = stamp(as_of)
    recent = [
        e for e in events if 0 <= (now - stamp(e.emitted_at)).total_seconds() <= 2700
    ]
    funnel = _machine_primary_entry_funnel(recent)
    missing_rows = []
    historical_samples = []
    identified_clocks = []
    fixed_watch_clocks = []
    fixed_watch_evidence = []
    fixed_watch_attempts = {}

    def identity_evidence_id(event):
        return hashlib.sha256(
            repr(
                (
                    event.emitted_at,
                    event.stage,
                    event.stock_code,
                    event.record_id,
                    sorted(event.fields.items()),
                )
            ).encode()
        ).hexdigest()

    # Reuse already loaded cache rows for legacy incident metadata only; no
    # second raw scan or historical funnel/recovery calculation. Bound output.
    for e in events:
        at = stamp(e.emitted_at)
        if at.date() != now.date() or at > now:
            continue
        if e.pipeline != "ENTRY_PIPELINE" or not _is_machine_primary_event(e):
            continue
        fixed_watch = (
            str(e.fields.get("watch_origin") or "").strip() == "MAIN_FIXED_WATCH"
        )
        if fixed_watch and _machine_primary_fixed_watch_identity_valid(e):
            fixed_watch_evidence.append((at, identity_evidence_id(e)))
            if (now - at).total_seconds() <= 2700:
                fixed_watch_clocks.append(at)
                components = _machine_primary_fixed_watch_identity_components(e)
                attempt_key = tuple(components.items())
                attempt = fixed_watch_attempts.setdefault(
                    attempt_key,
                    dict(
                        **components,
                        first_evaluated_at=at.isoformat(),
                        last_event_at=at.isoformat(),
                        observed_actions=set(),
                    ),
                )
                attempt["first_evaluated_at"] = min(
                    attempt["first_evaluated_at"], at.isoformat()
                )
                attempt["last_event_at"] = max(attempt["last_event_at"], at.isoformat())
                action = str(e.fields.get("entry_mechanistic_action") or "").upper()
                if action:
                    attempt["observed_actions"].add(action)
            continue
        if not fixed_watch and _machine_primary_evaluation_key(e):
            if (now - at).total_seconds() <= 2700:
                identified_clocks.append(at)
            continue
        detail = dict(
            evidence_id=identity_evidence_id(e),
            occurred_at=at.isoformat(),
            stock_code=e.stock_code,
            stage=e.stage,
            record_id=e.record_id,
            missing_fields=[
                k
                for k, v in (
                    _machine_primary_fixed_watch_identity_components(e)
                    if fixed_watch
                    else _machine_primary_identity_components(e)
                ).items()
                if not v or v.lower() in {"none", "null", "unknown", "-", "0"}
            ],
            conflicting_fields=(
                ["scanner_promotion_id"]
                if fixed_watch
                and str(e.fields.get("scanner_promotion_id") or "").strip().lower()
                not in {"", "none", "null", "unknown", "-", "0"}
                else []
            ),
            identity_contract_issues=(
                ["fixed_watch_admission_generation_invalid"]
                if fixed_watch
                and not _machine_primary_fixed_watch_identity_valid(e)
                and all(
                    value and value.lower() not in {"none", "null", "unknown", "-", "0"}
                    for value in _machine_primary_fixed_watch_identity_components(
                        e
                    ).values()
                )
                else []
            ),
        )
        if (now - at).total_seconds() <= 2700:
            missing_rows.append(detail)
        else:
            historical_samples.append(detail)
            # Keep the most recent old receipts even when input is unsorted.
            if len(historical_samples) > 128:
                historical_samples.sort(
                    key=lambda r: (r["occurred_at"], r["evidence_id"])
                )
                historical_samples.pop(0)
    missing_rows.sort(key=lambda row: (row["occurred_at"], row["evidence_id"]))
    retained_missing = [
        r
        for r in missing_rows
        if (now - stamp(r["occurred_at"])).total_seconds() <= WINDOW_SEC
    ]
    current_missing = [
        r
        for r in missing_rows
        if (now - stamp(r["occurred_at"])).total_seconds() < GRACE_SEC
    ]
    current_identified = [
        at for at in identified_clocks if (now - at).total_seconds() < GRACE_SEC
    ]
    identity_observation = dict(
        schema="machine_identity_recency_v1",
        window_sec=GRACE_SEC,
        status=(
            "current_gap"
            if current_missing
            else "no_recurrence_observed" if current_identified else "unobservable"
        ),
        missing_event_count=len(current_missing),
        identified_event_count=len(current_identified),
        current_missing_first_at=(
            current_missing[0]["occurred_at"] if current_missing else None
        ),
        current_missing_last_at=(
            current_missing[-1]["occurred_at"] if current_missing else None
        ),
        latest_identified_at=(
            max(current_identified).isoformat() if current_identified else None
        ),
        missing_first_at=missing_rows[0]["occurred_at"] if missing_rows else None,
        missing_last_at=missing_rows[-1]["occurred_at"] if missing_rows else None,
        examples=current_missing[:3],
    )
    economic = {}
    economic_by_revision = {}
    chain_status = {
        r["evaluation_key"]: r["revision_chain_status"]
        for r in funnel["evaluation_ledger"]
    }
    economic_history = defaultdict(list)
    confirmations = {}
    for e in sorted(recent, key=lambda event: stamp(event.emitted_at)):
        if e.fields.get("entry_machine_confirmation_sha256"):
            confirmation_key = (
                _machine_primary_evaluation_key(e),
                e.fields.get("machine_observation_sha256"),
            )
            if all(confirmation_key):
                confirmations[confirmation_key] = {
                    key: e.fields.get(key)
                    for key in (
                        "entry_machine_confirmation_sha256",
                        "entry_machine_confirmation_recipe_id",
                        "entry_machine_confirmation_source_sha256",
                        "entry_machine_confirmation_policy_sha256",
                    )
                }
        if e.stage not in ECONOMIC_STAGES:
            continue
        if str(e.fields.get("watch_origin") or "").strip() == "MAIN_FIXED_WATCH":
            continue
        key = _machine_primary_evaluation_key(e)
        if key:
            value = e.fields.get("economic_source_monitor_projection")
            value = json.loads(value) if isinstance(value, str) else value
            value = (
                value
                if isinstance(value, dict)
                else economic_evidence(e.fields, e.stock_code)
            )
            # Older slim-cache projections omitted this diagnostic, but the
            # original field was retained. No raw rescan or proof regeneration.
            value = {
                **value,
                "capacity_blocker": e.fields.get("entry_economic_capacity_blocker")
                or value.get("capacity_blocker"),
            }
            observation = {
                "observed_at": stamp(e.emitted_at).isoformat(),
                "stage": e.stage,
                "mechanistic_action": e.fields.get("entry_mechanistic_action"),
                "machine_observation_sha256": e.fields.get(
                    "machine_observation_sha256"
                ),
                "evidence": dict(value),
            }
            if observation not in economic_history[key]:
                economic_history[key].append(observation)
            revision_key = (
                (key, e.fields.get("machine_observation_sha256"))
                if chain_status.get(key) == "valid"
                else (key, None)
            )
            old = economic_by_revision.get(revision_key, {})
            if (
                old.get("blocker") == "economic_observation_conflicting_proofs"
                or old.get("status") == value.get("status") == "recorded_source_only"
                and old.get("seed_sha256") != value.get("seed_sha256")
            ):
                value = {
                    **old,
                    "status": "source_gap",
                    "blocker": "economic_observation_conflicting_proofs",
                }
            economic_by_revision[revision_key] = value
            economic[key] = value
    for row in funnel["evaluation_ledger"]:
        confirmation_hash = (
            (row.get("decision_history") or [{}])[-1].get("machine_observation_sha256")
            if row["revision_chain_status"] in {"valid", "single_revision"}
            else None
        )
        row["recipe_confirmation_evidence"] = confirmations.get(
            (row["evaluation_key"], confirmation_hash)
        )
        row["economic_history"] = economic_history.get(row["evaluation_key"], [])
        feature_guard = (
            row["mechanistic_action"] == "RECHECK"
            and row["ai_screen_status"] == "not_requested_required_feature_insufficient"
            and not row["conflict_reasons"]
        )
        row["economic_source"] = economic.get(
            row["evaluation_key"],
            {
                "status": (
                    "guard_excluded"
                    if feature_guard
                    else (
                        "not_applicable_machine_source_invalid"
                        if row["mechanistic_action"]
                        not in {"ENTER_NOW", "BLOCK", "RECHECK"}
                        else (
                            "source_gap"
                            if stamp(row["first_evaluated_at"]).date().isoformat()
                            >= "2026-09-21"
                            else "historical_not_required"
                        )
                    )
                ),
                "blocker": (
                    "required_feature_input_insufficient"
                    if feature_guard
                    else (
                        "economic_observation_event_missing"
                        if row["mechanistic_action"]
                        in {"ENTER_NOW", "BLOCK", "RECHECK"}
                        else None
                    )
                ),
                "owner": "main_entry_execution_owners->pipeline_event_logger->sentinel_cache",
                "closure_test": "same exact attempt publishes its pre-AI economic observation",
            },
        )
        if row["revision_chain_status"] == "valid":
            missing = {
                "status": "source_gap",
                "blocker": "economic_observation_event_missing",
                "owner": "main_entry_execution_owners->pipeline_event_logger->sentinel_cache",
                "closure_test": "same exact revision publishes its pre-AI economic observation",
            }
            final_hash = row["decision_history"][-1]["machine_observation_sha256"]
            row["economic_source"] = economic_by_revision.get(
                (row["evaluation_key"], final_hash), missing
            )
            # A later revision's success cannot retrospectively repair an
            # earlier ENTER_NOW's missing proof. Guard exclusions are separate.
            for observed in row["decision_history"]:
                proof = economic_by_revision.get(
                    (row["evaluation_key"], observed["machine_observation_sha256"]),
                    missing,
                )
                if (
                    observed["action"] == "ENTER_NOW"
                    and proof.get("status") == "source_gap"
                ):
                    row["economic_source"] = {
                        **proof,
                        "machine_observation_sha256": observed[
                            "machine_observation_sha256"
                        ],
                    }
                    break
    return {
        "schema": SCHEMA,
        "as_of": now.isoformat(),
        "evaluation_cohort": "scanner_promotions",
        "main_machine_observation": {
            "schema": "main_machine_cohort_observation_v1",
            "metric_role": "funnel_count",
            "decision_authority": "report_only",
            "window_policy": "loaded_exact_identity_attempts_current_45_minutes",
            "sample_floor": "none_for_counts",
            "primary_decision_metric": "identified_attempt_count",
            "source_quality_gate": "separate_exact_scanner_and_fixed_watch_identities",
            "forbidden_uses": [
                "order_authority",
                "economic_acceptance",
                "whole_main_zero_from_scanner_zero",
            ],
            "scanner_evaluation_count": funnel["evaluation_count"],
            "fixed_watch_evaluation_count": len(fixed_watch_attempts),
            "all_main_identified_evaluation_count": funnel["evaluation_count"]
            + len(fixed_watch_attempts),
            "coverage": "loaded_evidence_only_pid_consumption_not_assessed",
            "fixed_watch_attempts": [
                {**row, "observed_actions": sorted(row["observed_actions"])}
                for row in list(fixed_watch_attempts.values())[-1024:]
            ],
        },
        "async_disposition_coverage": async_disposition_coverage(events, as_of),
        "latest_event_at": max(
            (stamp(e.emitted_at) for e in recent), default=now - timedelta(days=1)
        ).isoformat(),
        "latest_event_status": (
            "observed_recent_event" if recent else "no_recent_loaded_events"
        ),
        "loaded_recent_event_count": len(recent),
        "auxiliary_ai_semantic_status_counts": funnel.get(
            "auxiliary_ai_semantic_status_counts", {}
        ),
        "auxiliary_ai_semantic_issue_counts": funnel.get(
            "auxiliary_ai_semantic_issue_counts", {}
        ),
        "identity_missing_events": funnel["evaluation_identity_missing_event_count"],
        "fixed_watch_identified_evidence": [
            evidence for _, evidence in sorted(fixed_watch_evidence, reverse=True)[:256]
        ],
        "fixed_watch_identity_observation": {
            "schema": "fixed_watch_source_identity_v1",
            "metric_role": "source_quality_gate",
            "decision_authority": "report_only",
            "window_policy": "current_45_minutes",
            "sample_floor": "none_for_source_identity",
            "primary_decision_metric": "identified_event_count",
            "source_quality_gate": "exact_watch_admission_generation_attempt_scope_bundle",
            "forbidden_uses": [
                "scanner_promotion_denominator",
                "submission_state",
                "order_authority",
                "economic_acceptance",
            ],
            "identified_event_count": len(fixed_watch_clocks),
            "identity_missing_event_count": funnel[
                "fixed_watch_identity_missing_event_count"
            ],
            "latest_identified_at": (
                max(fixed_watch_clocks).isoformat() if fixed_watch_clocks else None
            ),
        },
        "rows": [
            {
                k: r[k]
                for k in (
                    "evaluation_key",
                    "scanner_promotion_id",
                    "stock_code",
                    "effective_venue",
                    "session_bucket",
                    "policy_bundle_hash",
                    "first_evaluated_at",
                    "last_event_at",
                    "mechanistic_action",
                    "ai_screen_status",
                    "auxiliary_ai_semantics",
                    "broker_acceptance_observed",
                    "final_guard_blocked",
                    "final_guard_evidence",
                    "final_state",
                    "conflict_reasons",
                    "source_invalid_decomposition",
                    "economic_source",
                    "decision_history",
                    "initial_observed_action",
                    "latest_observed_action",
                    "enter_now_observed",
                    "economic_history",
                    "revision_chain_status",
                    "recipe_confirmation_evidence",
                )
            }
            for r in funnel["evaluation_ledger"]
        ],
        "missing_identity_evidence": sorted(
            {r["evidence_id"] for r in retained_missing}
        ),
        "missing_identity_examples": retained_missing[:3],
        "missing_identity_first_at": (
            retained_missing[0]["occurred_at"] if retained_missing else None
        ),
        "missing_identity_last_at": (
            retained_missing[-1]["occurred_at"] if retained_missing else None
        ),
        "historical_identity_samples": historical_samples,
        "identity_observation": identity_observation,
    }


def _nonentry_capacity_observation_gap(row):
    """Only explicit no-fetch non-entry misses are coverage, not submit faults."""
    economic = row.get("economic_source") or {}
    return (
        row.get("mechanistic_action") in {"BLOCK", "RECHECK"}
        and row.get("ai_screen_status") == "not_requested_machine_nonentry"
        and not row.get("conflict_reasons")
        and _latest_nonentry_economics(row)
        and not row.get("broker_acceptance_observed")
        and row.get("final_state")
        in {"machine_block_point_drop", "machine_recheck_observation"}
        and economic.get("status") == "source_gap"
        and economic.get("blocker") == "exact_broker_capacity_missing"
        and economic.get("capacity_blocker")
        == "capacity_observation_cache_miss_nonentry"
    )


def _nonentry_downstream_gap(row):
    """An uncalled execution replay is not a machine admission contract."""
    return (
        row.get("mechanistic_action") in {"BLOCK", "RECHECK"}
        and row.get("ai_screen_status") == "not_requested_machine_nonentry"
        and not row.get("conflict_reasons")
        and _latest_nonentry_economics(row)
        and not row.get("broker_acceptance_observed")
        and row.get("final_state")
        in {"machine_block_point_drop", "machine_recheck_observation"}
        and (row.get("economic_source") or {}).get("status") == "source_gap"
    )


def _latest_nonentry_economics(row):
    """A valid later machine revision can supersede an earlier ENTER_NOW."""
    if not row.get("enter_now_observed"):
        return True
    decisions = row.get("decision_history") or []
    economics = row.get("economic_history") or []
    if (
        row.get("revision_chain_status") != "valid"
        or row.get("latest_observed_action") != row.get("mechanistic_action")
        or not decisions
        or not economics
    ):
        return False
    latest_decision, latest_economic = decisions[-1], economics[-1]
    return bool(
        latest_decision.get("action") == row.get("mechanistic_action")
        and latest_economic.get("mechanistic_action") == row.get("mechanistic_action")
        and latest_decision.get("machine_observation_sha256")
        and latest_decision.get("machine_observation_sha256")
        == latest_economic.get("machine_observation_sha256")
        and latest_economic.get("evidence") == row.get("economic_source")
    )


def _small_json(path):
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("semantic_artifact_size_limit")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("semantic_artifact_invalid")
    return value


def _reversal_selection_receipt(bundle, data_root):
    """Read the issued family and its frozen reports, without legacy score gates."""
    from src.engine.scalping.continuous_reversal_policy import validate_sources

    validate_sources(bundle, data_root)
    family = bundle["continuous_reversal"]
    if (
        family.get("effective_date") != bundle.get("target_date")
        or family.get("source_date") != bundle.get("source_date")
        or family.get("publication_date") != bundle.get("publication_date")
    ):
        raise ValueError("reversal_selection_date_binding_invalid")
    selections = {}
    expanded = (
        [
            (key + "|" + route, value)
            for key, cell in family["machine_cells"].items()
            for route, value in cell.get("routes", {}).items()
        ]
        if family["schema"]
        in {
            "continuous_reversal_policy_v3",
            "continuous_reversal_policy_v4",
            "continuous_reversal_policy_v5",
            "continuous_reversal_policy_v6",
        }
        else list(family["machine_cells"].items())
    )
    for key, cell in expanded:
        metrics = cell.get("local_metrics")
        selections[key] = dict(
            version=family["selection_metric"],
            score_contract_valid=True,
            payload=cell["payload"],
            payload_sha256=cell["payload_sha256"],
            inherited_from=cell.get("inherited_from"),
            local_metrics=metrics,
            win_rate_pct=(
                (100 * metrics["wins"] / metrics["resolved"]) if metrics else None
            ),
            realized_pnl=False,
            report_is_activation_receipt=False,
        )
    return selections


def _reversal_observation_receipt(bundle, observation, *, verified_components=None):
    """Validate captured reversal identity, rule and verdict against its family."""
    from src.engine.scalping import continuous_reversal as kernel
    from src.engine.scalping.continuous_reversal_policy import validate_family
    from src.engine.scalping.mechanistic_entry_runtime_policy import digest

    family = bundle["continuous_reversal"]
    if family.get("schema") in {
        "continuous_reversal_policy_v5",
        "continuous_reversal_policy_v6",
    }:
        from src.engine.scalping.reversal_auxiliary_intraday import audit_observation

        return audit_observation(bundle, observation)
    is_v4 = family.get("schema") == "continuous_reversal_policy_v4"
    is_v3 = family.get("schema") in {
        "continuous_reversal_policy_v3",
        "continuous_reversal_policy_v4",
    }
    is_v2 = family.get("schema") in {
        "continuous_reversal_policy_v2",
        "continuous_reversal_policy_v3",
        "continuous_reversal_policy_v4",
    }
    if verified_components is None:
        validate_family(family)
        verified_components = dict(
            machine=digest(family["machine_cells"]),
            auxiliary=digest(family["auxiliary_cells"]),
        )
    context, source = observation["label_context"], observation["source"]
    assessment, receipt = source["assessment"], observation["runtime_consumption"]
    raw = source.get("exact_payload")
    if not isinstance(raw, dict) or not raw:
        raise ValueError("reversal_exact_payload_missing")
    symbol = str(context["stock_code"])
    session = context["session_bucket"]
    captured = stamp(observation["captured_at"])
    if (
        str(raw.get("stock_code")) != symbol
        or kernel.market_bucket(raw.get("session_bucket"))
        != kernel.market_bucket(session)
        or raw.get("evaluation_attempt_id") != context.get("evaluation_attempt_id")
        or not context.get("evaluation_attempt_id")
        or bundle.get("target_date") != captured.date().isoformat()
    ):
        raise ValueError("reversal_observation_identity_invalid")
    observed_epoch = raw.get("entry_machine_input_as_of")
    if (
        not isinstance(observed_epoch, (int, float))
        or not math.isfinite(observed_epoch)
        or observed_epoch > captured.timestamp()
    ):
        raise ValueError("reversal_observation_source_time_invalid")
    if receipt.get("bundle_sha256") != bundle["bundle_sha256"] or any(
        receipt.get(k) is not None
        for k in ("policy_sha256", "selector_leaf", "effective_thresholds")
    ):
        raise ValueError("effective_policy_receipt_mismatch")
    if (
        assessment.get("schema") != "mechanistic_entry_policy_decision_v1"
        or assessment.get("policy_version")
        != (family["schema"] if is_v2 else kernel.VERSION)
        or assessment.get("primary_decision_owner") != "mechanistic_entry_adjudicator"
        or assessment.get("ai_role") != "auxiliary_risk_screen_pass_veto_no_promotion"
    ):
        raise ValueError("reversal_assessment_contract_invalid")
    component = verified_components["machine"]
    native = receipt.get("continuous_reversal")
    if (
        observation.get("capture_contract") == "continuous_reversal_consumption_v1"
        and native is None
    ):
        raise ValueError("reversal_native_consumption_receipt_missing")
    if native is not None:
        from src.engine.scalping.ai_decision_trace import _json_bytes

        expected = dict(
            schema="continuous_reversal_consumption_v1",
            family_sha256=family["family_sha256"],
            bundle_sha256=bundle["bundle_sha256"],
            source_date=family["source_date"],
            publication_date=family["publication_date"],
            effective_date=family["effective_date"],
            machine_component_sha256=component,
            auxiliary_component_sha256=verified_components["auxiliary"],
            event_id=assessment.get("event_id"),
            cell_key=assessment.get("cell_key"),
            rule=assessment.get("rule"),
            pid=receipt.get("pid"),
            process_start_ticks=receipt.get("process_start_ticks"),
            captured_at=observation["captured_at"],
            exact_payload_sha256=hashlib.sha256(_json_bytes(raw)).hexdigest(),
            assessment_sha256=hashlib.sha256(_json_bytes(assessment)).hexdigest(),
        )
        if not isinstance(native, dict) or any(
            native.get(k) != v for k, v in expected.items()
        ):
            raise ValueError("reversal_native_consumption_receipt_mismatch")
        clock = native.get("snapshot_read_at")
        if (
            not isinstance(clock, (int, float))
            or not math.isfinite(clock)
            or not observed_epoch <= clock <= captured.timestamp()
        ):
            raise ValueError("reversal_snapshot_read_clock_invalid")
        key = assessment.get("cell_key")
        if is_v2:
            phase = assessment.get("decision_phase")
            arm = (
                family["auxiliary_cells"][key]["routes"][assessment["route"]][
                    "payload"
                ]["branch_policies"][assessment["primary_branch"]]["arm"]
                if is_v3 and key and assessment.get("primary_branch")
                else (
                    family["auxiliary_cells"][key]["payload"]["phase_policies"][phase][
                        "arm"
                    ]
                    if not is_v3 and key and phase
                    else None
                )
            )
            for field in (
                "primary_branch",
                "matched_branches",
                "signal_id",
                "branch_definition_sha256",
            ):
                if native.get(field) != assessment.get(field):
                    raise ValueError("reversal_branch_receipt_mismatch:" + field)
            if native.get("phase") != assessment.get("decision_phase", "FIRST_UPTICK"):
                raise ValueError("reversal_phase_receipt_mismatch")
        else:
            arm = family["auxiliary_cells"][key]["payload"]["arm"] if key else None
        if native.get("arm") != arm:
            raise ValueError("reversal_auxiliary_arm_receipt_mismatch")
        if assessment.get("action") == "ENTER_NOW":
            from src.engine.scalping.reversal_auxiliary_contract import (
                production_prompt,
                response_schema,
                ARMS,
            )

            if any(
                not isinstance(native.get(k), str) or len(native[k]) != 64
                for k in ("input_sha256", "prompt_sha256", "response_schema_sha256")
            ):
                raise ValueError("reversal_auxiliary_request_hash_missing")
            request = source.get("auxiliary_request")
            if not isinstance(request, dict) or any(
                digest(request.get(k)) != native.get(v)
                for k, v in (
                    ("input", "input_sha256"),
                    ("prompt", "prompt_sha256"),
                    ("response_schema", "response_schema_sha256"),
                )
            ):
                raise ValueError("reversal_auxiliary_request_hash_mismatch")
            inp = request["input"]
            expected_prompt = production_prompt(arm)
            expected_schema = response_schema(inp, complete_source_only=arm == ARMS[-1])
            if is_v2:
                from src.engine.scalping import reversal_auxiliary_phases as phases

                if is_v4:
                    from src.engine.scalping import reversal_path_auxiliary as phases
                expected_prompt = phases.prompt(phase, arm)
                if is_v4 and phase in phases.PHASES:
                    phases.validate_input_signal(inp, assessment["auxiliary_event"])
                    expected_schema["properties"]["risk_codes"]["minItems"] = 1
                    if (
                        inp.get("signal_kind") != phase
                        or inp.get("mechanistic_entry_assessment", {}).get(
                            "machine_signal_confirmed"
                        )
                        is not True
                        or "price_reversal_confirmed"
                        in inp.get("mechanistic_entry_assessment", {})
                    ):
                        raise ValueError("path_auxiliary_signal_contract_mismatch")
                if phase == "CONFIRMED_UPTICK":
                    expected_schema["properties"]["risk_codes"]["minItems"] = 1
                    e = assessment["event"]
                    timeline = inp.get("observation_phase", {})
                    if (
                        timeline.get("stage") != phase
                        or timeline.get("rolling_windows_end") != "AT_CONFIRMATION"
                        or timeline.get("original_first_uptick")
                        != dict(
                            id=e["anchor_event_id"],
                            as_of=e["anchor_epoch"],
                            price=e["anchor_price"],
                        )
                        or timeline.get("additional_higher_trade")
                        != dict(
                            id=e["event_id"],
                            as_of=e["epoch"],
                            price=e["confirmation_price"],
                        )
                    ):
                        raise ValueError("reversal_confirmation_timeline_mismatch")
            if (
                request["prompt"] != expected_prompt
                or request["response_schema"] != expected_schema
                or inp.get("objective")
                != dict(
                    net_target_pct=0.4,
                    net_soft_stop_pct=-3.0,
                    horizon_seconds=1800,
                    cost_rate=0.0023,
                )
            ):
                raise ValueError("reversal_auxiliary_issued_contract_mismatch")
            facts = inp["entry_setup_evidence_v1"]["facts"]
            auxiliary_event = (
                (assessment.get("auxiliary_event") or assessment["event"])
                if is_v2
                else assessment["event"]
            )
            if any(
                facts.get(k) != auxiliary_event.get(k)
                for k in (
                    "confirmation_price",
                    "entry_ask",
                    "low_price",
                    "drop_pct",
                    "drawdown_5m_pct",
                    "down_steps",
                    "spread_pct",
                    "volume_ratio_60s",
                )
            ):
                raise ValueError("reversal_auxiliary_event_input_mismatch")
        elif any(
            native.get(k) is not None
            for k in ("input_sha256", "prompt_sha256", "response_schema_sha256")
        ):
            raise ValueError("reversal_nonentry_provider_receipt_invalid")
    event = assessment.get("event")
    if event is None:
        if (
            assessment.get("action") != "BLOCK"
            or assessment.get("reason")
            != ("no_current_reversal_signal" if is_v2 else "no_current_first_uptick")
            or assessment.get("price_reversal_confirmed") is not False
            or any(
                assessment.get(k) is not None for k in ("cell_key", "rule", "event_id")
            )
        ):
            raise ValueError("reversal_nonturn_receipt_invalid")
        return {}, dict(policy_sha256=component, leaf="NO_CURRENT_FIRST_UPTICK")
    if (
        not isinstance(event, dict)
        or event.get("symbol") != symbol
        or event.get("market") != kernel.market_bucket(session)
        or assessment.get("event_id") != event.get("event_id")
        or (
            assessment.get("machine_signal_confirmed") is not True
            if is_v4
            else assessment.get("price_reversal_confirmed") is not True
        )
    ):
        raise ValueError("reversal_event_identity_invalid")
    if (
        not isinstance(event.get("epoch"), (int, float))
        or not math.isfinite(event["epoch"])
        or event["epoch"]
        > (native["snapshot_read_at"] if native else captured.timestamp())
        or not isinstance(event.get("source_item"), str)
        or event["source_item"].split("_", 1)[0] != symbol
    ):
        raise ValueError("reversal_event_source_invalid")
    key = kernel.cell_key(symbol, session, event["confirmation_price"])
    if is_v3:
        from src.engine.scalping.reversal_registered_catalog import cell_key

        key = cell_key(symbol, session, event["confirmation_price"])
    if is_v2:
        from src.engine.scalping.continuous_reversal_policy_v2 import assess

        if is_v3:
            from src.engine.scalping.continuous_reversal_policy_v3 import assess
        if is_v4:
            from src.engine.scalping.continuous_reversal_policy_v4 import assess
        replay, _, _, _ = assess(
            family, (event, None), symbol=symbol, session=session, build_request=False
        )
        for field in (
            "action",
            "reason",
            "cell_key",
            "event_id",
            "signal_id",
            "matched_branches",
            "branch_states",
            "primary_branch",
            "decision_phase",
            "auxiliary_arm",
            "auxiliary_event",
            "machine_component_sha256",
            "family_sha256",
            "price_reversal_confirmed",
            *(["machine_signal_confirmed", "signal_kind"] if is_v4 else []),
        ):
            if assessment.get(field) != replay.get(field):
                raise ValueError("reversal_v2_branch_verdict_mismatch:" + field)
        return (
            family["machine_cells"][key]["routes"][assessment["route"]]["payload"]
            if is_v3
            else family["machine_cells"][key]["payload"]
        ), dict(policy_sha256=component, leaf=key)
    rule = family["machine_cells"][key]["payload"]["rule"]
    if (
        assessment.get("cell_key") != key
        or assessment.get("rule") != rule
        or assessment.get("machine_component_sha256") != component
    ):
        raise ValueError("reversal_selected_cell_receipt_mismatch")
    if event["entry_ask"] is None:
        action, reason = "RECHECK", "entry_quote_source_missing"
    elif not kernel.conditions(event)[rule]:
        missing = ("VOL" in rule and event["volume_ratio_60s"] is None) or (
            rule.startswith("DD5") and event["drawdown_5m_pct"] is None
        )
        action, reason = (
            ("RECHECK", "required_reversal_feature_missing")
            if missing
            else ("BLOCK", "selected_reversal_condition_not_met")
        )
    else:
        action, reason = "ENTER_NOW", "continuous_reversal_cell_pass"
    if assessment.get("action") != action or assessment.get("reason") != reason:
        raise ValueError("reversal_rule_verdict_mismatch")
    return {"rule": rule}, dict(policy_sha256=component, leaf=key)


def _machine_role_receipt(observation, kind):
    """Compact role facts from a row already hash/frozen-receipt validated."""
    source = observation.get("source") or {}
    exact = source.get("exact_payload") or {}
    assessment = source.get("assessment") or {}
    runtime = observation.get("runtime_consumption") or {}
    native = runtime.get("continuous_reversal") or {}
    role = (
        observation.get("evaluation_role")
        or exact.get("evaluation_role")
        or "unspecified_legacy"
    )
    claims = [
        observation.get("evaluation_role"),
        exact.get("evaluation_role"),
        native.get("evaluation_role"),
    ]
    if any(
        value is not None and (not isinstance(value, str) or not 0 < len(value) <= 64)
        for value in claims
    ):
        raise ValueError("machine_observation_role_claim_invalid")
    return dict(
        observation_sha256=observation.get("machine_observation_sha256"),
        captured_at=observation.get("captured_at"),
        bundle_sha256=observation.get("bundle_sha256"),
        actor=[
            str(runtime.get("pid") or ""),
            str(runtime.get("process_start_ticks") or ""),
        ],
        evaluation_role=role,
        top_role=observation.get("evaluation_role"),
        exact_role=exact.get("evaluation_role"),
        native_role=native.get("evaluation_role"),
        native_provider_state=native.get("provider_state"),
        native_provider_request_observed=native.get("provider_request_observed"),
        decision_class=kind,
        capture_flags={
            k: observation.get(k)
            for k in (
                "runtime_effect",
                "allowed_runtime_apply",
                "actual_order_submitted",
                "broker_order_forbidden",
                "provider_called",
            )
        },
        assessment_flags={
            k: assessment.get(k)
            for k in (
                "runtime_effect",
                "allowed_runtime_apply",
                "actual_order_submitted",
                "broker_order_forbidden",
            )
        },
    )


def _machine_role_partition(records, actor, now, bundle):
    rows = [row[6] for row in records]
    eligible = [
        row
        for row in rows
        if row["evaluation_role"] in ("main_live", "unspecified_legacy")
    ]
    return dict(
        schema="machine_observation_role_partition_v1",
        as_of=now.isoformat(),
        actor=list(actor),
        bundle_sha256=bundle,
        observation_count=len(rows),
        role_counts=dict(Counter(row["evaluation_role"] for row in rows)),
        provider_eligible_count=len(eligible),
        excluded_nonprovider_count=len(rows) - len(eligible),
        provider_eligible_hashes=sorted(row["observation_sha256"] for row in eligible),
        observations=rows,
        runtime_effect=False,
        allowed_runtime_apply=False,
    )


def _verified_machine_role_partition(
    partition, actor, now, bundle, n, invalid, required
):
    """Close the all-role/eligible denominators; unknown roles never disappear."""
    try:

        def count(value):
            return type(value) is int and value >= 0

        def sha(value):
            return (
                isinstance(value, str)
                and re.fullmatch("[0-9a-f]{64}", value) is not None
            )

        rows = partition["observations"]
        if (
            partition.get("schema") != "machine_observation_role_partition_v1"
            or stamp(partition.get("as_of")) != now
            or partition.get("actor") != actor
            or partition.get("bundle_sha256") != bundle
            or partition.get("runtime_effect") is not False
            or partition.get("allowed_runtime_apply") is not False
            or not isinstance(rows, list)
            or len(rows) > 4096
            or len(rows) != n
            or not count(partition.get("observation_count"))
            or partition["observation_count"] != n
        ):
            return None
        seen = set()
        roles = Counter()
        kinds = Counter()
        eligible = []
        eligible_kinds = Counter()
        for row in rows:
            digest = row["observation_sha256"]
            at = stamp(row.get("captured_at"))
            role = row.get("evaluation_role")
            kind = row.get("decision_class")
            if (
                not sha(digest)
                or digest in seen
                or row.get("actor") != actor
                or row.get("bundle_sha256") != bundle
                or at is None
                or not 0 <= (now - at).total_seconds() <= SOURCE_WINDOW_SEC
                or role not in ("main_live", "unspecified_legacy", "probe_observation")
                or kind not in ("matched", "invalid", "required")
                or any(
                    row.get(k) is not None and row.get(k) != role
                    for k in ("top_role", "exact_role", "native_role")
                )
                or (
                    row.get("top_role") or row.get("exact_role") or "unspecified_legacy"
                )
                != role
            ):
                return None
            if role == "probe_observation":
                flags = row.get("capture_flags")
                assessment = row.get("assessment_flags")
                if (
                    row.get("top_role") != role
                    or row.get("exact_role") != role
                    or row.get("native_role") != role
                    or row.get("native_provider_state")
                    != "probe_observation_provider_forbidden"
                    or row.get("native_provider_request_observed") is not False
                    or not isinstance(flags, dict)
                    or not isinstance(assessment, dict)
                    or any(
                        flags.get(k) is not False
                        for k in (
                            "runtime_effect",
                            "allowed_runtime_apply",
                            "actual_order_submitted",
                            "provider_called",
                        )
                    )
                    or flags.get("broker_order_forbidden") is not True
                    or any(
                        assessment.get(k) is not False
                        for k in (
                            "runtime_effect",
                            "allowed_runtime_apply",
                            "actual_order_submitted",
                        )
                    )
                    or assessment.get("broker_order_forbidden") is not True
                ):
                    return None
            else:
                eligible.append(digest)
                eligible_kinds[kind] += 1
            seen.add(digest)
            roles[role] += 1
            kinds[kind] += 1
        if (
            kinds["invalid"] != invalid
            or kinds["required"] != required
            or not isinstance(partition.get("role_counts"), dict)
            or partition["role_counts"] != dict(roles)
            or any(not count(v) for v in partition["role_counts"].values())
            or not count(partition.get("provider_eligible_count"))
            or partition["provider_eligible_count"] != len(eligible)
            or not count(partition.get("excluded_nonprovider_count"))
            or partition["excluded_nonprovider_count"] != n - len(eligible)
            or partition.get("provider_eligible_hashes") != sorted(eligible)
        ):
            return None
        return dict(
            count=len(eligible),
            invalid=eligible_kinds["invalid"],
            required=eligible_kinds["required"],
            hashes=set(eligible),
        )
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def _scanner_observation_identity(observation):
    """Exact native scanner identity; no symbol/time inference or validity claim."""
    from src.engine.monitoring.sentinel_event_scope import canonical_session

    context = observation.get("label_context")
    if not isinstance(context, dict):
        return None
    parts = [
        observation.get("scanner_promotion_id"),
        context.get("evaluation_attempt_id"),
        context.get("stock_code"),
        context.get("effective_venue"),
        context.get("session_bucket"),
        observation.get("bundle_sha256"),
    ]
    if (
        any(
            not isinstance(v, str)
            or not 0 < len(v) <= 256
            or "|" in v
            or v.lower() in {"none", "null", "unknown", "-", "0"}
            for v in parts
        )
        or context.get("scanner_promotion_id") != parts[0]
        or observation.get("watch_origin") == "MAIN_FIXED_WATCH"
    ):
        return None
    parts[3] = parts[3].upper()
    parts[4] = canonical_session(parts[4])
    return "machine:" + "|".join(parts)


def _historical_scanner_incident(
    incident_key, incident, observations, actor, birth, now
):
    """Prove prior-process membership, preserving unresolved source/economics."""
    from src.engine.scalping.ai_decision_trace import _json_bytes

    if (
        not isinstance(incident, dict)
        or not isinstance(observations, dict)
        or len(observations) > 32
        or len(_json_bytes(observations)) > 512 * 1024
        or not actor
        or birth is None
        or now is None
        or incident.get("rule")
        not in {"economic_producer_gap", "source_or_submit_lineage_gap"}
        or incident.get("category") != "structural_evidence"
        or incident.get("status") not in {"active", "pending", "historical_unresolved"}
    ):
        return False
    ids = incident.get("evidence_ids")
    scope = incident.get("scope")
    if (
        not isinstance(scope, str)
        or not isinstance(ids, list)
        or not 0 < len(ids) <= 32
        or any(not isinstance(v, str) for v in ids)
        or len(set(ids)) != len(ids)
        or type(incident.get("count")) is not int
        or incident["count"] != len(ids)
        or hashlib.sha256(f"{scope}|{incident['rule']}".encode()).hexdigest()[:24]
        != incident_key
    ):
        return False
    for key in ids:
        observation = observations.get(key)
        if not isinstance(observation, dict):
            return False
        payload = _json_bytes(observation)
        at = stamp(observation.get("captured_at"))
        receipt = observation.get("runtime_consumption")
        source = observation.get("source")
        exact = source.get("exact_payload") if isinstance(source, dict) else None
        assessment = source.get("assessment") if isinstance(source, dict) else None
        # The dated preflight producer stops before reversal adjudication. Its
        # signed legacy-role receipt still records the exact process and safe
        # nonprovider terminal; it cannot claim native policy consumption.
        legacy_preflight = (
            observation.get("evaluation_role") == "unspecified_legacy"
            and isinstance(exact, dict)
            and exact.get("evaluation_role") in (None, "unspecified_legacy")
            and isinstance(assessment, dict)
            and (
                assessment.get("schema"),
                assessment.get("action"),
                assessment.get("reason"),
            )
            == (
                "mechanistic_entry_source_invalid_v1",
                "source_invalid",
                "ai_input_preflight_blocked",
            )
            and all(
                observation.get(k) is False
                for k in (
                    "provider_called",
                    "actual_order_submitted",
                    "runtime_effect",
                    "allowed_runtime_apply",
                )
            )
            and observation.get("broker_order_forbidden") is True
            and observation.get("capture_contract") is None
            and isinstance(receipt, dict)
            and "continuous_reversal" not in receipt
        )
        if (
            len(payload) > 128 * 1024
            or observation.get("schema") != "mechanistic_entry_observation_v1"
            or observation.get("evaluation_role") != "main_live"
            and not legacy_preflight
            or _scanner_observation_identity(observation) != key
            or "|".join(key.split("|")[-3:]) != scope
            or at is None
            or at.date() != now.date()
            or not at.timestamp() < birth
            or not isinstance(receipt, dict)
        ):
            return False
        old_actor = [str(receipt.get(k) or "") for k in ("pid", "process_start_ticks")]
        if (
            not all(v.isdigit() and 0 < len(v) <= 20 and int(v) > 0 for v in old_actor)
            or old_actor == actor
            or int(old_actor[1]) >= int(actor[1])
            or receipt.get("bundle_sha256") != observation.get("bundle_sha256")
            or stamp(receipt.get("consumed_at")) != at
            or hashlib.sha256(
                _json_bytes(
                    {
                        k: v
                        for k, v in observation.items()
                        if k != "machine_observation_sha256"
                    }
                )
            ).hexdigest()
            != observation.get("machine_observation_sha256")
        ):
            return False
        native = receipt.get("continuous_reversal")
        if isinstance(native, dict) and (
            [str(native.get(k) or "") for k in ("pid", "process_start_ticks")]
            != old_actor
            or stamp(native.get("captured_at")) != at
        ):
            return False
    return True


def machine_semantics(
    data_root,
    now,
    *,
    tail_bytes=8 * 1024 * 1024,
    incident_evidence_ids=(),
    historical_scanner_observations=None,
    historical_scanner_conflicts=(),
):
    """Bounded receipt audit, not a replay, policy publisher or outcome estimator."""
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.monitoring.sentinel_event_scope import canonical_session

    now = stamp(now)
    day = now.date().isoformat()
    result = dict(
        status="unobservable",
        metric_role="source_quality_gate",
        decision_authority="report_only",
        window_policy="recent_30m_bounded_tail",
        sample_floor="none_for_receipt_checks",
        primary_decision_metric="receipt_mismatch_count",
        source_quality_gate="exact_observation_hash_scope_and_frozen_policy",
        forbidden_uses=[
            "automatic_policy_change",
            "realized_pnl",
            "missing_as_zero_ev",
        ],
        selection={},
        scopes={},
        issues={},
        examples=[],
        observation_count=0,
        source_invalid_count=0,
        required_feature_guard_count=0,
        source_invalid_blockers={},
        action_replay_performed=False,
    )
    issues = Counter()
    try:
        current = runtime.load_effective(data_root=data_root, target_date=day)
        if not current:
            raise ValueError("current_policy_missing")
        result["current_bundle_sha256"] = current["bundle_sha256"]
        if current.get("continuous_reversal"):
            result["selection"] = _reversal_selection_receipt(current, data_root)
            result["selection_family"] = "continuous_reversal"
            result["publication"] = dict(
                source_date=current["source_date"],
                publication_date=current["publication_date"],
                effective_date=current["target_date"],
                status="native_frozen_family_verified",
                actual_pid_consumption="see_per_scope_live_pid_receipts",
            )
        else:
            report = _small_json(
                data_root
                / "report/ai_decision_action_outcome_calibration"
                / f"machine_policy_{day}.json"
            )
            digest = runtime.digest(
                {k: v for k, v in report.items() if k != "artifact_content_sha256"}
            )
            if (
                digest != report.get("artifact_content_sha256")
                or report.get("target_date") != day
            ):
                raise ValueError("selection_artifact_invalid")
            for scope, selected in report.get("selections", {}).items():
                economy = (
                    (selected.get("machine_evidence") or {}).get("train") or {}
                ).get("economics") or {}
                score = strategy.machine_support_adjusted_win_rate(economy)
                recorded = economy.get("support_adjusted_win_rate_pct")
                valid = (
                    selected.get("selection_basis")
                    == strategy.MACHINE_SELECTION_VERSION
                )
                if selected.get("promotion_pass"):
                    valid = (
                        valid
                        and score is not None
                        and isinstance(recorded, (int, float))
                        and math.isclose(score, recorded, abs_tol=1e-8)
                    )
                result["selection"][scope] = dict(
                    version=selected.get("selection_basis"),
                    score_contract_valid=valid,
                    promotion_pass=selected.get("promotion_pass"),
                    reasons=selected.get("promotion_errors"),
                    unique_opportunities=economy.get("selected_opportunity_count"),
                    win_rate_pct=economy.get("win_rate_pct"),
                    support_adjusted_score_pct=recorded,
                    mean_net_path_ev_pct=economy.get("selected_path_ev_pct"),
                    realized_pnl=False,
                    report_is_activation_receipt=False,
                )
                if not valid:
                    issues["selection_score_contract_invalid"] += 1
            terminal = _small_json(
                data_root
                / "report/ai_decision_action_outcome_calibration"
                / f"machine_policy_terminal_{day}.json"
            )
            if terminal.get("report_sha256") != report[
                "artifact_content_sha256"
            ] or runtime.digest(
                {k: v for k, v in terminal.items() if k != "artifact_content_sha256"}
            ) != terminal.get(
                "artifact_content_sha256"
            ):
                raise ValueError("selection_terminal_binding_invalid")
            result["publication"] = dict(
                status=terminal.get("status"),
                activation=terminal.get("activation"),
                actual_pid_consumption="see_per_scope_live_pid_receipts",
            )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["selection_status"] = "unobservable:" + str(exc)[:160]
    path = data_root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl"
    generations, seen = {}, set()
    verified_reversal_generations = {}
    reversal_observations = []
    health_records = []
    pid_identities = {}
    # Reuse this bounded native read. Include original signed observations,
    # not an age-only exemption or a fabricated economic recovery receipt.
    wanted = set(incident_evidence_ids) if len(incident_evidence_ids) <= 8192 else set()
    historical, ambiguous = {}, set()
    if (
        isinstance(historical_scanner_conflicts, (list, tuple))
        and len(historical_scanner_conflicts) <= 8192
    ):
        ambiguous = {
            v
            for v in historical_scanner_conflicts
            if isinstance(v, str) and v in wanted
        }
    prior_observations = historical_scanner_observations
    if (
        isinstance(prior_observations, dict)
        and len(prior_observations) <= 32
        and len(_json_bytes(prior_observations)) <= 512 * 1024
    ):
        historical = {
            k: v
            for k, v in prior_observations.items()
            if k in wanted and k not in ambiguous and isinstance(v, dict)
        }
    historical_bytes = len(_json_bytes(historical))
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            size = before.st_size
            start = max(0, size - tail_bytes)
            stream.seek(start)
            if start:
                stream.readline()
            result.update(
                tail_truncated=bool(start),
                source_bytes=size,
                read_limit_bytes=tail_bytes,
            )
            payload = stream.read(max(0, size - stream.tell()))
            after = path.stat()
            if (before.st_dev, before.st_ino) != (
                after.st_dev,
                after.st_ino,
            ) or after.st_size < size:
                raise OSError("machine_source_generation_changed_during_read")
            result.update(
                bytes_read=len(payload),
                read_count=1,
                window_coverage="bounded_suffix" if start else "complete_file_prefix",
            )
            for line in payload.splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    break
                try:
                    observation = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    issues["observation_json_invalid"] += 1
                    continue
                if (
                    not isinstance(observation, dict)
                    or observation.get("schema") != "mechanistic_entry_observation_v1"
                ):
                    continue
                evidence_id = (
                    _scanner_observation_identity(observation) if wanted else None
                )
                if evidence_id in wanted and evidence_id not in ambiguous:
                    previous = historical.get(evidence_id)
                    if previous is not None and previous != observation:
                        historical.pop(evidence_id)
                        ambiguous.add(evidence_id)
                    elif previous is None:
                        added_bytes = len(_json_bytes({evidence_id: observation}))
                        if (
                            len(line) <= 128 * 1024
                            and historical_bytes + added_bytes <= 512 * 1024
                            and len(historical) < 32
                        ):
                            historical[evidence_id] = observation
                            historical_bytes += added_bytes
                        else:
                            ambiguous.add(evidence_id)
                at = stamp(observation.get("captured_at"))
                if not at or not 0 <= (now - at).total_seconds() <= WINDOW_SEC:
                    continue
                observed_hash = observation.get("machine_observation_sha256")
                if observed_hash in seen:
                    continue
                seen.add(observed_hash)
                result["observation_count"] += 1
                try:
                    if (
                        hashlib.sha256(
                            _json_bytes(
                                {
                                    k: v
                                    for k, v in observation.items()
                                    if k != "machine_observation_sha256"
                                }
                            )
                        ).hexdigest()
                        != observed_hash
                    ):
                        raise ValueError("machine_observation_hash_invalid")
                    receipt = observation["runtime_consumption"]
                    bundle_hash = observation["bundle_sha256"]
                    if (
                        not isinstance(bundle_hash, str)
                        or len(bundle_hash) != 64
                        or any(c not in "0123456789abcdef" for c in bundle_hash)
                    ):
                        raise ValueError("bundle_hash_invalid")
                    if bundle_hash not in generations:
                        bundle = _small_json(
                            runtime.root(data_root)
                            / "generations"
                            / f"{bundle_hash}.json"
                        )
                        if (
                            runtime.digest(
                                {
                                    k: v
                                    for k, v in bundle.items()
                                    if k != "bundle_sha256"
                                }
                            )
                            != bundle_hash
                        ):
                            raise ValueError("frozen_bundle_hash_invalid")
                        generations[bundle_hash] = bundle
                    context, source = (
                        observation["label_context"],
                        observation["source"],
                    )
                    assessment = source.get("assessment") or {}
                    identity = (
                        receipt.get("pid"),
                        receipt.get("cwd"),
                        receipt.get("process_start_ticks"),
                    )
                    if identity not in pid_identities:
                        try:
                            proc = Path("/proc") / str(int(receipt["pid"]))
                            live = str((proc / "cwd").resolve()) == receipt.get(
                                "cwd"
                            ) and (proc / "stat").read_text().split(") ", 1)[1].split()[
                                19
                            ] == receipt.get(
                                "process_start_ticks"
                            )
                        except (OSError, ValueError, KeyError, IndexError):
                            live = False
                        pid_identities[identity] = live
                    invalid = (
                        str(assessment.get("action", "")).upper() == "SOURCE_INVALID"
                    )
                    feature_guard = (
                        assessment.get("schema")
                        == "mechanistic_entry_required_feature_v1"
                        and assessment.get("action") == "RECHECK"
                        and assessment.get("reason")
                        == "required_feature_input_insufficient"
                        and (source.get("setup_evidence") or {}).get(
                            "source_quality_status"
                        )
                        == "blocked"
                    )
                    role_receipt = _machine_role_receipt(
                        observation,
                        (
                            "invalid"
                            if invalid
                            else "required" if feature_guard else "matched"
                        ),
                    )
                    if invalid or feature_guard:
                        if generations[bundle_hash].get("continuous_reversal"):
                            reversal_observations.append(observation)
                        result[
                            (
                                "source_invalid_count"
                                if invalid
                                else "required_feature_guard_count"
                            )
                        ] += 1
                        health_records.append(
                            (
                                at,
                                identity,
                                "invalid" if invalid else "required",
                                list(
                                    (source.get("setup_evidence") or {}).get(
                                        "source_quality_blockers", []
                                    )
                                ),
                                None,
                                bundle_hash == result.get("current_bundle_sha256"),
                                role_receipt,
                            )
                        )
                        for blocker in (source.get("setup_evidence") or {}).get(
                            "source_quality_blockers", []
                        ):
                            result["source_invalid_blockers"][blocker] = (
                                result["source_invalid_blockers"].get(blocker, 0) + 1
                            )
                        continue
                    scope = (
                        str(context["effective_venue"]).upper(),
                        canonical_session(context["session_bucket"]),
                    )
                    frozen = generations[bundle_hash]
                    if frozen.get("continuous_reversal"):
                        if bundle_hash not in verified_reversal_generations:
                            _reversal_selection_receipt(frozen, data_root)
                            # Keep verification cache outside the signed bundle.
                            verified_reversal_generations[bundle_hash] = dict(
                                machine=runtime.digest(
                                    frozen["continuous_reversal"]["machine_cells"]
                                ),
                                auxiliary=runtime.digest(
                                    frozen["continuous_reversal"]["auxiliary_cells"]
                                ),
                            )
                        profile, selection = _reversal_observation_receipt(
                            frozen,
                            observation,
                            verified_components=verified_reversal_generations[
                                bundle_hash
                            ],
                        )
                        reversal_observations.append(observation)
                    else:
                        scoped = runtime.for_cohort(generations[bundle_hash], scope)
                        if not scoped:
                            raise ValueError("frozen_policy_scope_missing")
                        setup = source["setup_evidence"]
                        raw = setup.get("strategy_raw_input")
                        if not isinstance(raw, dict):
                            raise ValueError("machine_raw_input_missing")
                        if strategy.digest(raw) != setup.get("strategy_raw_sha256"):
                            raise ValueError("machine_raw_hash_invalid")
                        profile, selection = strategy.select(
                            scoped["machine_policy"], raw, setup
                        )
                        if (
                            receipt.get("bundle_sha256") != bundle_hash
                            or receipt.get("policy_sha256")
                            != selection["policy_sha256"]
                            or receipt.get("selector_leaf") != selection["leaf"]
                            or receipt.get("effective_thresholds") != profile
                        ):
                            raise ValueError("effective_policy_receipt_mismatch")
                    key = "|".join(
                        (
                            *scope,
                            bundle_hash,
                            selection["policy_sha256"],
                            selection["leaf"],
                        )
                    )
                    counts = result["scopes"].setdefault(
                        key,
                        dict(
                            matched_receipts=0,
                            live_pid_receipts=0,
                            effective_thresholds=profile,
                            current_bundle=bundle_hash
                            == result.get("current_bundle_sha256"),
                        ),
                    )
                    counts["matched_receipts"] += 1
                    contract = (
                        "native_reversal_receipt"
                        if receipt.get("continuous_reversal")
                        else (
                            "historical_reversal_capture"
                            if frozen.get("continuous_reversal")
                            else "legacy_strategy_receipt"
                        )
                    )
                    counts[contract] = counts.get(contract, 0) + 1
                    live = pid_identities[identity]
                    counts["live_pid_receipts"] += int(live)
                    health_records.append(
                        (
                            at,
                            identity,
                            "matched",
                            [],
                            key,
                            bundle_hash == result.get("current_bundle_sha256"),
                            role_receipt,
                        )
                    )
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as exc:
                    reason = str(exc)[:160]
                    issues[reason] += 1
                    if len(result["examples"]) < 3:
                        result["examples"].append(
                            dict(observation_sha256=observed_hash, reason=reason)
                        )
    except OSError as exc:
        result["source_status"] = "unobservable:" + (
            "compressed_archive_not_current_bounded_source"
            if path.with_suffix(path.suffix + ".gz").exists()
            else type(exc).__name__
        )
    native_issues = dict(issues)
    if reversal_observations:
        live_identities = [
            identity for identity, live in pid_identities.items() if live
        ]
        live_pid = (
            (live_identities[0][0], live_identities[0][2])
            if len(live_identities) == 1
            else None
        )
        lineage = _reversal_provider_lineage(
            data_root,
            now,
            reversal_observations,
            tail_bytes=tail_bytes,
            pid_identity=live_pid,
        )
        lineage["live_producer_identities"] = [
            dict(pid=identity[0], cwd=identity[1], process_start_ticks=identity[2])
            for identity in live_identities
        ]
        lineage["current_pid_coverage"] = (
            "exact_live_pid"
            if live_pid is not None
            else "unresolved_or_multiple_live_producers"
        )
        result["reversal_provider_lineage"] = lineage
        issues.update(lineage["issues"])
        if lineage.get("status") == "partial_source_gap":
            result["provider_lineage_source_status"] = "partial_source_gap"
    result["pid_identity_read_count"] = len(pid_identities)
    if wanted:
        result["historical_scanner_observations"] = historical
        result["historical_scanner_conflicts"] = sorted(ambiguous)
    result["issues"] = dict(issues)
    if issues:
        result["status"] = "review_required"
    elif result.get("selection_status") or result.get("source_status"):
        result["status"] = "partial_unobservable"
    elif result["source_invalid_count"] or result["required_feature_guard_count"]:
        result["status"] = "source_invalid_observed"
    elif result["observation_count"]:
        result["status"] = "observed_receipts_match"
    actor = _HEALTH_ACTOR.get()
    if actor:
        retained = [
            row
            for row in health_records
            if [str(row[1][0]), str(row[1][2])] == actor
            and 0 <= (now - row[0]).total_seconds() <= SOURCE_WINDOW_SEC
        ]
        invalid_n = sum(row[2] == "invalid" for row in retained)
        required_n = sum(row[2] == "required" for row in retained)
        view = {
            k: v
            for k, v in result.items()
            if k
            not in {
                "current_health_cohort",
                "reversal_provider_lineage",
                "provider_lineage_source_status",
            }
        }
        scoped, blockers = {}, Counter()
        for at, identity, kind, reasons, key, current_bundle, role_receipt in retained:
            blockers.update(reasons)
            if key:
                row = scoped.setdefault(
                    key,
                    dict(
                        matched_receipts=0,
                        live_pid_receipts=0,
                        current_bundle=current_bundle,
                    ),
                )
                row["matched_receipts"] += 1
                row["live_pid_receipts"] += int(pid_identities.get(identity, False))
        view.update(
            observation_count=len(retained),
            source_invalid_count=invalid_n,
            required_feature_guard_count=required_n,
            scopes=scoped,
            source_invalid_blockers=dict(blockers),
            issues=native_issues,
            observation_role_partition=_machine_role_partition(
                retained, actor, now, result.get("current_bundle_sha256")
            ),
        )
        projected = (result.get("reversal_provider_lineage") or {}).get(
            "current_health_cohort"
        )
        if projected:
            view["reversal_provider_lineage"] = projected["view"]
            view["issues"] = dict(
                Counter(native_issues) + Counter(projected["view"]["issues"])
            )
            if projected["view"]["status"] == "partial_source_gap":
                view["provider_lineage_source_status"] = "partial_source_gap"
        view["status"] = (
            "review_required"
            if view["issues"]
            else (
                "partial_unobservable"
                if view.get("selection_status")
                or view.get("source_status")
                or view.get("provider_lineage_source_status")
                else (
                    "source_invalid_observed"
                    if invalid_n + required_n
                    else "observed_receipts_match" if retained else "unobservable"
                )
            )
        )
        # An empty current cohort needs no current provider join. Original30m
        # provider observations, unknown terminals and issues remain untouched.
        if not retained and (
            not projected
            or projected["view"].get("status") == "not_observed"
            and not projected["view"].get("issues")
            and not projected["view"].get("source_gaps")
        ):
            view.pop("reversal_provider_lineage", None)
            view.pop("provider_lineage_source_status", None)
        result["current_health_cohort"] = _health_cohort(
            view, actor, now, excluded=result["observation_count"] - len(retained)
        )
    return result


def _latest_dated_path(directory, prefix, through_date):
    """Select one date without opening a potentially large report."""
    candidates = []
    for path in directory.glob(f"{prefix}????-??-??.json"):
        day = path.name[len(prefix) : -5]
        try:
            if (
                datetime.fromisoformat(day).date().isoformat() == day
                and day <= through_date
            ):
                candidates.append((day, path))
        except ValueError:
            continue
    if not candidates:
        return None, None
    day, path = max(candidates)
    if path.is_symlink():
        raise ValueError("semantic_artifact_symlink_rejected")
    return day, path


def _latest_dated_json(directory, prefix, through_date):
    """Read one exact-date artifact; never scan event/history payloads here."""
    day, path = _latest_dated_path(directory, prefix, through_date)
    return day, _small_json(path) if path is not None else None


def _entry_split_count(value):
    if isinstance(value, (list, dict)):
        return len(value)
    if value is None or type(value) is int and value >= 0:
        return value
    raise ValueError("entry_split_count_invalid")


def entry_execution_tuning_semantics(data_root, now):
    """Audit the independent split/delay postclose receipts without replaying data."""
    now = stamp(now)
    day = now.date().isoformat()
    result = {
        "schema": "entry_execution_tuning_semantics_v1",
        "as_of": now.isoformat(),
        "metric_role": "source_quality_gate",
        "decision_authority": "report_only",
        "axes_are_independent": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "forbidden_uses": [
            "entry_action",
            "split_or_delay_policy_change",
            "missing_as_zero_ev",
        ],
        "bootstrap": {"status": "unobservable"},
        "entry_split": {"status": "unobservable", "runtime_consumption": "not_proven"},
        "pre_submit_delay": {
            "status": "unobservable",
            "runtime_consumption": "not_proven",
        },
        "issues": {},
        "examples": [],
    }
    issues = Counter()
    # The routed cron passes release/data; resolve the trusted deployment
    # mount once. The family reader still rejects symlinks below this root.
    data_root = Path(data_root).resolve()

    bootstrap_path = (
        data_root / "runtime/policy_bootstrap" / f"runtime_policy_bootstrap_{day}.json"
    )
    verify_path = (
        data_root
        / "runtime/policy_bootstrap"
        / f"runtime_policy_bootstrap_verify_{day}.json"
    )
    bootstrap = {}
    bootstrap_valid = False
    try:
        bootstrap = _small_json(bootstrap_path)
        verify = _small_json(verify_path)
        if bootstrap.get("target_date") != day or verify.get("target_date") != day:
            raise ValueError("bootstrap_target_date_mismatch")
        bootstrap_valid = True
        result["bootstrap"] = {
            "status": (
                "verified"
                if verify.get("status") == "pass" and verify.get("passed") is True
                else "verification_not_passed"
            ),
            "verify_status": verify.get("status"),
            "pid_passed": verify.get("pid_passed"),
            "policy_pid_consumption_proven": False,
        }
        if result["bootstrap"]["status"] != "verified":
            issues["entry_execution_bootstrap_verification_failed"] += 1
            result["examples"].append(
                {"axis": "bootstrap", "reason": "same_date_verification_not_passed"}
            )
    except (OSError, ValueError, TypeError) as exc:
        result["bootstrap"] = {"status": "unobservable", "reason": str(exc)[:160]}

    # Entry split: exact report-policy generation, source gap, and the dated
    # incumbent named by the bootstrap are distinct facts. No candidate is not
    # a receipt defect and does not create a synthetic zero-EV result.
    split = result["entry_split"]
    try:
        report_date, report_path = _latest_dated_path(
            data_root / "report/entry_split_order_plan", "entry_split_order_plan_", day
        )
        if report_path is None:
            split.update(
                status="not_yet_observed", blocker="entry_split_report_missing"
            )
        else:
            policy_path = (
                data_root
                / "threshold_cycle/entry_split_order_policy"
                / f"entry_split_order_policy_{report_date}.json"
            )
            binding_status = "missing"
            policy = None
            from src.engine.scalping.entry_split_monitor_projection import (
                manifest_path,
                read_verified_projection,
            )

            pointer = manifest_path(report_path)
            if (
                pointer.exists()
                or pointer.is_symlink()
                or report_path.stat().st_size > 8 * 1024 * 1024
            ):
                report, proof = read_verified_projection(
                    report_path,
                    policy_path,
                    source_date=report_date,
                    role="submission_monitor",
                )
                proof = dict(proof)
                policy = proof.pop("_validated_policy", None)
                if proof.get("verified") is not True or not isinstance(policy, dict):
                    raise ValueError("entry_split_projection_not_verified")
                binding_status = "matched"
                split.update(
                    verification="verified",
                    verification_receipt=proof,
                    read_mode="verified_monitor_projection",
                )
            else:
                report = _small_json(report_path)
                if policy_path.is_symlink():
                    binding_status = "symlink_rejected"
                elif policy_path.exists():
                    policy = _small_json(policy_path)
                    from src.engine.scalping.entry_split_order_plan import (
                        validate_report_policy_generation,
                    )

                    valid, reason = validate_report_policy_generation(report, policy)
                    binding_status = "matched" if valid else reason
                split.update(
                    verification=(
                        "verified" if binding_status == "matched" else "invalid"
                    ),
                    read_mode="bounded_native_report",
                )
            if binding_status != "matched":
                issues["entry_split_report_policy_generation_mismatch"] += 1
                if len(result["examples"]) < 3:
                    result["examples"].append(
                        {
                            "axis": "entry_split",
                            "reason": binding_status,
                            "source_date": report_date,
                        }
                    )
            bootstrap_policy_binding = "unobservable"
            if bootstrap_valid:
                env = bootstrap.get("env_overrides") or {}
                env_file = (
                    env.get("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE")
                    if isinstance(env, dict)
                    else None
                )
                env_version = (
                    env.get("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_VERSION")
                    if isinstance(env, dict)
                    else None
                )
                configured = None
                if env_file:
                    configured_path = Path(str(env_file))
                    try:
                        configured_path.resolve(strict=True).relative_to(
                            data_root.resolve(strict=True)
                        )
                        if configured_path.is_symlink():
                            raise ValueError("bootstrap_policy_symlink_rejected")
                        configured = _small_json(configured_path)
                    except (OSError, ValueError, RuntimeError):
                        configured = None
                        bootstrap_policy_binding = "configured_policy_invalid"
                if (
                    configured is not None
                    and configured.get("policy_version") != env_version
                ):
                    bootstrap_policy_binding = "configured_policy_version_mismatch"
                elif (
                    configured is not None
                    and policy
                    and policy.get("runtime_apply_allowed") is True
                ):
                    same_file = Path(str(env_file)).resolve() == policy_path.resolve()
                    bootstrap_policy_binding = (
                        "candidate_bound"
                        if same_file and env_version == policy.get("policy_version")
                        else "promoted_candidate_not_bound"
                    )
                elif policy and policy.get("runtime_apply_allowed") is True:
                    bootstrap_policy_binding = "promoted_candidate_not_bound"
                elif configured is not None:
                    bootstrap_policy_binding = (
                        "incumbent_preserved_candidate_not_promoted"
                    )
                if bootstrap_policy_binding in {
                    "configured_policy_invalid",
                    "configured_policy_version_mismatch",
                    "promoted_candidate_not_bound",
                }:
                    issue = "entry_split_bootstrap_policy_binding_invalid"
                    issues[issue] += 1
                    if len(result["examples"]) < 3:
                        result["examples"].append(
                            {
                                "axis": "entry_split",
                                "reason": bootstrap_policy_binding,
                                "source_date": report_date,
                            }
                        )
            acceptance = report.get("economic_acceptance") or {}
            candidates = report.get("operating_candidate_grid") or []
            candidate_count = report.get("operating_candidate_count", len(candidates))
            if type(candidate_count) is not int or candidate_count < 0:
                raise ValueError("entry_split_projection_candidate_count_invalid")
            split.update(
                status=(
                    "source_gap"
                    if acceptance.get("blockers")
                    else (
                        "candidate_observed"
                        if candidate_count
                        else "no_candidate_observed"
                    )
                ),
                source_date=report_date,
                report_schema=report.get("schema_version"),
                clean_baseline_date=(report.get("cumulative_state") or {}).get(
                    "clean_tuning_baseline_date"
                ),
                cumulative_source_date_count=len(
                    (report.get("cumulative_state") or {}).get("source_dates") or []
                ),
                economic_status=acceptance.get("status"),
                blockers=list(acceptance.get("blockers") or [])[:12],
                operating_candidate_count=candidate_count,
                primary_operating_ev_pct=acceptance.get("primary_operating_ev_pct"),
                robust_paired_delta_ev_lower_bound_pct=acceptance.get(
                    "robust_paired_delta_ev_lower_bound_pct"
                ),
                paired_model_row_count=_entry_split_count(
                    acceptance.get("model_row_count", acceptance.get("model_rows"))
                ),
                consumed_holdout_count=_entry_split_count(
                    acceptance.get(
                        "consumed_holdout_count", acceptance.get("consumed_holdouts")
                    )
                ),
                policy_generation_binding=binding_status,
                policy_runtime_apply_allowed=bool(
                    policy and policy.get("runtime_apply_allowed")
                ),
                prepared_effective_date=(policy or {}).get("prepared_effective_date"),
                paired_net_ev_delta_pct=acceptance.get("paired_net_ev_delta_pct"),
                bootstrap_policy_binding=bootstrap_policy_binding,
                runtime_consumption=(
                    "bootstrap_manifest_bound_not_pid_proven"
                    if bootstrap_policy_binding
                    in {"candidate_bound", "incumbent_preserved_candidate_not_promoted"}
                    else "not_proven"
                ),
            )
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        split.update(
            status="unobservable", verification="not_verified", reason=str(exc)[:160]
        )

    # The bootstrap's own delay selector is the canonical policy validator.
    # Re-run that bounded small-artifact check and compare it with the frozen
    # manifest; do not read raw pipeline/BBO history or regenerate the tuner.
    delay = result["pre_submit_delay"]
    try:
        delay_report_date, delay_report = _latest_dated_json(
            data_root / "report/pre_submit_delay_tuning",
            "pre_submit_delay_tuning_",
            day,
        )
        from src.engine.scalping.pre_submit_delay_initial_policy import (
            committed_paths,
            REPORT_SCHEMA as DELAY_V2,
            _read as read_initial,
        )

        pointers = sorted(
            (data_root / "threshold_cycle/pre_submit_delay_policy").glob(
                "committed_????-??-??.json"
            ),
            reverse=True,
        )
        if len(pointers) > 370:
            raise ValueError("delay_generation_inventory_unbounded")
        latest = next((p for p in pointers if p.stem[-10:] <= day), None)
        if latest is not None and (
            delay_report_date is None or latest.stem[-10:] >= delay_report_date
        ):
            delay_report_date = latest.stem[-10:]
            report_file, _, _, _ = committed_paths(data_root, delay_report_date)
            delay_report = read_initial(report_file)
        if delay_report is not None:
            report_identity_valid = (
                delay_report.get("schema") in {"pre_submit_delay_tuning_v1", DELAY_V2}
                and delay_report.get("source_date") == delay_report_date
                and delay_report.get("analysis_axis") == "pre_submit_delay"
            )
            if not report_identity_valid:
                issues["pre_submit_delay_report_identity_invalid"] += 1
                if len(result["examples"]) < 3:
                    result["examples"].append(
                        {
                            "axis": "pre_submit_delay",
                            "reason": "report_identity_invalid",
                            "source_date": delay_report_date,
                        }
                    )
            delay_grid = delay_report.get("candidate_grid") or []
            from src.engine.scalping.pre_submit_delay_tuning import (
                price_pattern_projection,
            )

            if delay_report.get("schema") == DELAY_V2:
                price_analysis = {
                    key: delay_report.get(key)
                    for key in (
                        "status",
                        "metric_role",
                        "price_ready_pair_n",
                        "census",
                        "cells",
                        "default_delay_sec",
                        "source_sha256",
                    )
                }
                price_analysis.update(
                    runtime_apply_allowed=False,
                    economic_approval=False,
                    actual_fill_proven=False,
                    analysis_complete=delay_report["status"] != "blocked",
                )
            else:
                price_analysis = price_pattern_projection(delay_report)
            if price_analysis["status"] == "source_invalid":
                issues["pre_submit_delay_price_pattern_invalid"] += 1
            delay.update(
                report_status="observed" if report_identity_valid else "invalid",
                report_date=delay_report_date,
                report_schema=delay_report.get("schema"),
                report_source_date=delay_report.get("source_date"),
                clean_baseline_date=delay_report.get("clean_tuning_baseline_date"),
                source_date_count=(delay_report.get("source") or {}).get(
                    "source_date_count"
                ),
                committed_count=delay_report.get("committed_attempt_count"),
                completed_terminal_count=delay_report.get("terminal_observation_count"),
                submit_call_terminal_count=delay_report.get(
                    "terminal_observation_count"
                ),
                terminal_count_semantics="submit_call_completion_not_fill_or_exit",
                price_pattern_analysis=price_analysis,
                candidate_count=len(delay_grid),
                candidate_delays_sec=[row.get("delay_sec") for row in delay_grid[:8]],
                report_blockers=(
                    [delay_report.get("first_blocker")]
                    if delay_report.get("first_blocker")
                    else []
                ),
                selected_delay_sec=delay_report.get("selected_delay_sec"),
                net_ev_delta_pct=delay_report.get("net_ev_delta_pct"),
            )
        else:
            delay["report_status"] = "not_yet_observed"
        from src.engine.automation import runtime_policy_bootstrap as bootstrap_owner

        expected_env, expected_handoff = bootstrap_owner._pre_submit_delay_handoff(day)
        recorded_handoff = bootstrap.get("pre_submit_delay_handoff")
        env = bootstrap.get("env_overrides") or {}
        if not isinstance(env, dict):
            raise ValueError("bootstrap_env_overrides_invalid")
        # A missing/stale bootstrap is unobservable; do not turn it into a
        # mismatch against today's selector. Only compare same-day receipts.
        handoff_match = (
            recorded_handoff == expected_handoff if bootstrap_valid else None
        )
        env_keys = set(bootstrap_owner.PRE_SUBMIT_DELAY_ENV_KEYS)
        env_match = (
            {key: env.get(key) for key in env_keys if key in env} == expected_env
            if bootstrap_valid
            else None
        )
        if bootstrap_valid and handoff_match is not True:
            issues["pre_submit_delay_bootstrap_handoff_mismatch"] += 1
            if len(result["examples"]) < 3:
                result["examples"].append(
                    {"axis": "pre_submit_delay", "reason": "bootstrap_handoff_mismatch"}
                )
        if bootstrap_valid and env_match is not True:
            issues["pre_submit_delay_bootstrap_env_mismatch"] += 1
            if len(result["examples"]) < 3:
                result["examples"].append(
                    {"axis": "pre_submit_delay", "reason": "bootstrap_env_mismatch"}
                )
        status = expected_handoff.get("status")
        delay.update(
            status=(
                "verified_policy_bound"
                if status
                in {
                    "verified_candidate",
                    "verified_carried_candidate",
                    "verified_initial_timing_policy",
                }
                and env_match is True
                else (
                    "source_gap"
                    if status == "no_validated_candidate_source_gap"
                    else (
                        "not_evaluated"
                        if status == "no_validated_candidate_not_evaluated"
                        else (
                            "unpublished"
                            if status == "not_published"
                            else (
                                "contract_mismatch"
                                if status == "binding_invalid" or handoff_match is False
                                else "unobservable"
                            )
                        )
                    )
                )
            ),
            handoff_status=status,
            source_date=expected_handoff.get("source_date"),
            effective_from=expected_handoff.get("effective_from"),
            policy_sha256=expected_handoff.get("policy_sha256"),
            bootstrap_handoff_match=handoff_match,
            bootstrap_env_match=env_match,
            runtime_consumption=(
                "bootstrap_manifest_bound_not_pid_proven"
                if expected_env and env_match is True
                else "not_proven"
            ),
            runtime_effect=False,
        )
        if status == "binding_invalid":
            issues["pre_submit_delay_policy_binding_invalid"] += 1
            if len(result["examples"]) < 3:
                result["examples"].append(
                    {"axis": "pre_submit_delay", "reason": "policy_binding_invalid"}
                )
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        delay.update(status="unobservable", reason=str(exc)[:160])

    # Postclose artifact_freshness owns cancel-wait incidents. This projection
    # provides the same diagnostics without creating a duplicate intraday alert.
    from src.engine.error_detectors.artifact_freshness import (
        _entry_cancel_wait_result_semantics,
        _cancel_wait_monitor_source_date,
    )

    result["entry_cancel_wait"] = _entry_cancel_wait_result_semantics(
        data_root.parent,
        _cancel_wait_monitor_source_date(data_root.parent, day, data_root=data_root),
        now,
        data_root=data_root,
    )
    result["entry_cancel_wait"]["notification_owner"] = "artifact_freshness"
    result["issues"] = dict(issues)
    if issues:
        result["status"] = "review_required"
    elif (
        result["bootstrap"].get("status") == "verified"
        and split.get("verification") == "verified"
        and delay.get("status") != "unobservable"
    ):
        result["status"] = "observed"
    else:
        result["status"] = "partial_unobservable"
    return result


def observation_health_projection(result):
    """Classify a fully read but unassessed window; no I/O or recovery authority.

    Consumers recompute this projection from the same bounded report and compare
    it exactly. WARNING means current decision coverage is still unknown. It is
    neither valid-empty, source-health PASS, nor a policy/PID/economic receipt.
    Unknown, malformed or contradictory evidence never qualifies. Exact lazy
    journal absence may qualify only before the native morning entry window.
    """
    failed = []

    def require(condition, reason):
        if not condition and reason not in failed:
            failed.append(reason)

    def obj(value):
        return value if isinstance(value, dict) else {}

    def count(value, minimum=0, maximum=2**63 - 1):
        return type(value) is int and minimum <= value <= maximum

    def number(value):
        return (
            type(value) in (int, float)
            and abs(value) <= 10**15
            and math.isfinite(value)
        )

    def clock(value):
        return stamp(value) if isinstance(value, str) and len(value) <= 64 else None

    def sha(value):
        return (
            isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None
        )

    result = obj(result)
    now = clock(result.get("as_of"))
    day = now.date().isoformat() if now else None
    require(
        now is not None
        and result.get("schema") == SCHEMA
        and result.get("date") == day,
        "monitor_identity_invalid",
    )
    report_execution_valid = (
        result.get("execution_mode") == "full"
        and result.get("execution_status") == "completed"
        and result.get("semantic_status") == "partial"
        and result.get("runtime_effect") is False
    )
    require(
        report_execution_valid
        and result.get("status") == "unobservable"
        and result.get("blocker")
        in (
            "missing_stale_or_noncurrent_sentinel_evidence",
            "no_identified_scanner_machine_evaluation",
        )
        and result.get("runtime_effect") is False,
        "monitor_state_not_quiet_full_observation",
    )
    inp = obj(result.get("input_provenance"))
    at, latest = clock(inp.get("snapshot_as_of")), clock(inp.get("latest_event_at"))
    age = (now - at).total_seconds() if now and at else None
    event_age = (now - latest).total_seconds() if now and latest else None
    prior_raw = inp.get("prior_accepted_source_as_of")
    prior = clock(prior_raw)
    order = (
        "initial"
        if prior_raw is None
        else "advancing" if prior and at and at > prior else "invalid"
    )
    # Sentinel's legacy non-null placeholder is exactly snapshot_as_of -1day.
    # It is an absence marker only with this producer-issued population receipt;
    # a genuinely stale event timestamp cannot acquire that interpretation.
    event_marker = (
        inp.get("latest_event_status") == "no_recent_loaded_events"
        and count(inp.get("loaded_recent_event_count"), maximum=0)
        and at is not None
        and latest is not None
        and (at - latest).total_seconds() == 86400
    )
    observed_event = (
        latest is not None
        and latest.date().isoformat() == day
        and (
            inp.get("latest_event_status") is None
            or inp.get("latest_event_status") == "observed_recent_event"
            and count(inp.get("loaded_recent_event_count"), minimum=1)
        )
    )
    input_provenance_valid = (
        inp.get("schema") == "submission_monitor_input_provenance_v1"
        and clock(inp.get("evaluated_at")) == now
        and inp.get("target_date") == day
        and inp.get("dry_run") is False
        and inp.get("snapshot_schema") == SCHEMA
        and at is not None
        and at.date().isoformat() == day
        and age is not None
        and 0 <= age <= 420
        and (observed_event or event_marker)
        and event_age is not None
        and event_age >= age
        and number(inp.get("snapshot_age_seconds"))
        and inp["snapshot_age_seconds"] == age
        and number(inp.get("latest_event_age_seconds"))
        and inp["latest_event_age_seconds"] == event_age
        and count(inp.get("row_count"))
        and count(inp.get("identity_missing_events"), maximum=0)
        and inp.get("auxiliary_ai_semantic_issue_counts") == {}
        and order in {"initial", "advancing"}
        and inp.get("snapshot_order") == order
    )
    require(input_provenance_valid, "current_input_provenance_invalid")
    # A populated scanner cohort is not invalid provenance. Keep its quiet-window
    # limitation separate from source identity, clock and generation failures.
    require(
        count(inp.get("row_count"), maximum=0),
        "scanner_population_not_quiet",
    )

    stages = [
        obj(result.get(k))
        for k in (
            "source_gap_semantics",
            "machine_semantics",
            "entry_execution_tuning_semantics",
        )
    ]
    actor = None
    projections = [obj(stage.get("current_health_cohort")) for stage in stages[:2]]
    if any(projections):
        actor = projections[0].get("actor")
        valid = (
            isinstance(actor, list)
            and len(actor) == 2
            and all(
                isinstance(p, str) and p.isdigit() and 0 < len(p) <= 20 and int(p) > 0
                for p in actor
            )
            and all(
                p.get("schema") == "submission_monitor_current_health_cohort_v1"
                and clock(p.get("as_of")) == now
                and type(p.get("window_seconds")) is int
                and p["window_seconds"] == SOURCE_WINDOW_SEC
                and p.get("actor") == actor
                and p.get("decision_authority") == "report_only"
                and p.get("runtime_effect") is False
                and p.get("allowed_runtime_apply") is False
                and count(p.get("excluded_observation_count"))
                and p.get("excluded_classification") == "historical_not_current_cohort"
                and isinstance(p.get("view"), dict)
                for p in projections
            )
        )
        require(valid, "current_health_cohort_binding_invalid")
        if valid:
            proofs = [p.get("actor_birth_proof") for p in projections]
            generation = result.get("observer_generation")
            if (
                any(p is not None for p in proofs)
                or isinstance(generation, dict)
                and generation.get("actor_birth_proof") is not None
            ):
                require(
                    proofs[0] == proofs[1]
                    and isinstance(generation, dict)
                    and _verified_health_actor_birth(proofs[0], actor, now, generation)
                    is not None,
                    "current_health_actor_birth_invalid",
                )
            stages[:2] = [p["view"] for p in projections]
            receipt = obj(
                obj(result.get("observer_generation")).get(
                    "selector_reported_pid_receipt"
                )
            )
            if result.get("observer_generation") is not None:
                require(
                    actor
                    == [
                        str(receipt.get("pid") or ""),
                        str(receipt.get("start_ticks") or ""),
                    ],
                    "current_health_actor_not_selected_pid",
                )
            projected_lineage = obj(stages[1].get("reversal_provider_lineage"))
            if projected_lineage:
                require(
                    projected_lineage.get("exact_pid_filter") == actor,
                    "current_health_lineage_actor_mismatch",
                )
    require(all(stage for stage in stages), "required_semantic_component_missing")
    require(
        all(
            stage.get("issues") == {}
            and stage.get("issues_by_scope", {}) == {}
            and not any(
                stage.get(k) not in (None, "")
                for k in (
                    "selection_status",
                    "source_status",
                    "provider_lineage_source_status",
                    "error",
                    "errors",
                    "reason",
                )
            )
            for stage in stages
        )
        and result.get("issues", {}) == {}
        and result.get("diagnostics", {}) == {}
        and result.get("notification_pending") == [],
        "current_failure_or_diagnostic_present",
    )
    gap, machine, execution = stages
    # Share the native terminal contract with the closed-PASS guard consumer
    # below; source semantics already verifies the exact rejection receipt.
    native_invalidation = {
        "reversal_signal_expired",
        "reversal_signal_generation_changed",
        "reversal_first_signal_invalidated",
        "reversal_first_price_hold_invalidated",
    }
    allowed_diagnostics = {
        "machine_probe:" + reason
        for reason in (
            "route_snapshot_missing",
            "0B_missing",
            "0B_age_exceeded",
            "0D_missing",
            "0D_age_exceeded",
        )
    }
    allowed_diagnostics.update(
        "machine_trace:" + reason
        for reason in (
            "source_quality_blocked_before_assessment",
            "required_feature_blocked_before_assessment",
        )
    )
    allowed_diagnostics.update(
        "machine_trace:" + reason
        for reason in native_invalidation | {"entry_machine_input_deadline_expired"}
    )
    allowed_diagnostics.update(
        stage + ":reversal_first_price_hold_invalidated"
        for stage in ("machine_probe", "machine_trace")
    )
    allowed_diagnostics.add("machine_probe:reversal_first_signal_invalidated")
    pending = obj(gap.get("native_pending_observations"))
    pending_n = obj(gap.get("observed")).get("probe_observation_incomplete", 0)
    valid_pending = (
        pending.get("schema") == "submission_monitor_native_pending_census_v1"
        and count(pending_n, minimum=1)
        and pending.get("count") == pending_n
        and pending.get("verified_pending_count") == pending_n
        and count(pending.get("count"), minimum=1)
        and count(pending.get("verified_pending_count"), minimum=1)
        and count(pending.get("unclassified_count"), maximum=0)
        and count(pending.get("unknown_count"))
        and count(pending.get("source_censored_count"))
        and pending.get("runtime_effect") is False
        and pending.get("machine_admission_proven") is False
        and pending.get("pattern_no_match_proven") is False
    )
    if valid_pending:
        allowed_diagnostics.add("machine_probe:native_observation_incomplete")
    require(not pending_n or valid_pending, "native_pending_observation_not_verified")
    no_match_n = obj(gap.get("observed")).get("probe_native_no_match", 0)
    no_match_routes = obj(gap.get("probe_route_native_no_match_counts"))
    valid_no_match = (
        count(no_match_n, minimum=1)
        and len(no_match_routes) <= 16
        and all(count(v) for v in no_match_routes.values())
        and sum(no_match_routes.values()) == no_match_n
        and obj(gap.get("diagnostics")).get("machine_probe:native_no_matching_pattern")
        == no_match_n
    )
    if valid_no_match:
        allowed_diagnostics.add("machine_probe:native_no_matching_pattern")
    require(
        not no_match_n or valid_no_match, "native_no_match_observation_not_verified"
    )
    feature_gap = obj(gap.get("native_feature_gap_observations"))
    feature_gap_n = obj(gap.get("observed")).get("probe_feature_missing", 0)
    valid_feature_gap = (
        feature_gap.get("schema") == "submission_monitor_native_feature_gap_census_v1"
        and count(feature_gap_n, minimum=1)
        and count(feature_gap.get("count"), minimum=1)
        and count(feature_gap.get("verified_count"), minimum=1)
        and feature_gap["count"] == feature_gap["verified_count"] == feature_gap_n
        and count(feature_gap.get("unclassified_count"), maximum=0)
        and count(feature_gap.get("unknown_count"), minimum=feature_gap_n)
        and all(
            feature_gap.get(k) is False
            for k in (
                "runtime_effect",
                "source_coverage_proven",
                "machine_admission_proven",
                "pattern_no_match_proven",
            )
        )
        and obj(gap.get("diagnostics")).get(
            "machine_probe:required_branch_feature_missing"
        )
        == feature_gap_n
    )
    if valid_feature_gap:
        allowed_diagnostics.add("machine_probe:required_branch_feature_missing")
    require(
        not feature_gap_n or valid_feature_gap,
        "native_feature_gap_observation_not_verified",
    )
    history = obj(gap.get("native_history_observations"))
    history_n = obj(gap.get("observed")).get("probe_history_only", 0)
    history_reasons = {
        "machine_probe:native_history_observed_current_source_stale",
        "machine_probe:native_history_observed_with_source_gap",
    }
    valid_history = (
        history.get("schema") == "submission_monitor_native_history_census_v1"
        and count(history_n, minimum=1)
        and count(history.get("count"), minimum=1)
        and count(history.get("verified_count"), minimum=1)
        and history["count"] == history["verified_count"] == history_n
        and count(history.get("unclassified_count"), maximum=0)
        and count(history.get("known_count"), minimum=history_n)
        and all(
            history.get(k) is False
            for k in (
                "runtime_effect",
                "current_source_coverage_proven",
                "machine_admission_proven",
                "pattern_no_match_proven",
            )
        )
        and all(count(obj(gap.get("diagnostics")).get(k, 0)) for k in history_reasons)
        and sum(obj(gap.get("diagnostics")).get(k, 0) for k in history_reasons)
        == history_n
    )
    if valid_history:
        allowed_diagnostics.update(history_reasons)
    require(not history_n or valid_history, "native_history_observation_not_verified")
    diagnostics = obj(gap.get("diagnostics"))
    scoped = obj(gap.get("diagnostics_by_scope"))
    totals = Counter()
    scoped_valid = len(scoped) <= 256
    if scoped_valid:
        for key, value in scoped.items():
            reason = next(
                (
                    r
                    for r in allowed_diagnostics
                    if isinstance(key, str)
                    and len(key) <= 512
                    and key.endswith("|" + r)
                ),
                None,
            )
            if reason is None or not count(value, minimum=1):
                scoped_valid = False
                break
            totals[reason] += value
    diagnostics_valid = (
        isinstance(gap.get("diagnostics"), dict)
        and isinstance(gap.get("diagnostics_by_scope"), dict)
        and set(diagnostics) <= allowed_diagnostics
        and all(count(v, minimum=1) for v in diagnostics.values())
        and scoped_valid
        and dict(totals) == diagnostics
    )
    require(
        diagnostics_valid
        and all(
            stage.get("diagnostics", {}) == {}
            and stage.get("diagnostics_by_scope", {}) == {}
            for stage in (machine, execution)
        ),
        "unknown_or_unbound_source_diagnostic",
    )
    observed = obj(gap.get("observed"))
    observed_valid = (
        isinstance(gap.get("observed"), dict)
        and set(observed)
        <= {
            "probe_results",
            "probe_assessed",
            "entry_traces",
            "machine_assessed",
            "auxiliary_required",
            "auxiliary_called",
            "auxiliary_cost_bound",
            "auxiliary_pending",
            "auxiliary_pending_bound",
            "auxiliary_transport_unavailable",
            "probe_observation_incomplete",
            "probe_native_no_match",
            "probe_feature_missing",
            "probe_history_only",
            "probe_native_invalidated",
        }
        and all(count(v) for v in observed.values())
    )
    expected_gap = (
        "gap_observed"
        if diagnostics or gap.get("issues")
        else "observed_no_gap" if any(observed.values()) else "unobservable"
    )
    sources = obj(gap.get("sources"))
    require(
        gap.get("schema") == "machine_auxiliary_intraday_source_semantics_v1"
        and clock(gap.get("as_of")) == now
        and gap.get("status") == expected_gap
        and gap.get("runtime_effect") is False
        and gap.get("decision_authority") == "report_only"
        and observed_valid
        and set(sources) == {"probe", "trace", "pending"}
        and (
            not observed_valid
            or observed.get("probe_assessed", 0) <= observed.get("probe_results", 0)
            and observed.get("machine_assessed", 0) <= observed.get("entry_traces", 0)
        )
        and gap.get("async_transition_projection_coverage") == "complete"
        and gap.get("async_pass_projection_coverage") == "complete"
        and isinstance(gap.get("async_pass_projection"), list)
        and len(gap["async_pass_projection"]) <= 128
        and isinstance(gap.get("async_transition_projection"), list)
        and len(gap["async_transition_projection"]) <= 1024
        and count(gap.get("async_pass_unmapped_count"), maximum=0),
        "source_population_not_unassessed",
    )
    route_counts = [
        obj(gap.get(k))
        for k in (
            "probe_route_counts",
            "probe_route_assessed_counts",
            "probe_route_source_covered_counts",
            "probe_route_native_no_match_counts",
        )
    ]
    require(
        all(
            isinstance(gap.get(k), dict)
            for k in (
                "probe_route_counts",
                "probe_route_assessed_counts",
                "probe_route_source_covered_counts",
                "probe_route_native_no_match_counts",
            )
        )
        and all(
            len(rows) <= 16
            and all(
                isinstance(k, str) and len(k) <= 64 and count(v)
                for k, v in rows.items()
            )
            for rows in route_counts
        )
        and (
            not observed_valid
            or sum(route_counts[0].values()) <= observed.get("probe_results", 0)
        )
        and all(
            sum(rows.values()) <= sum(route_counts[0].values())
            for rows in route_counts[1:]
        ),
        "probe_route_counts_invalid",
    )
    waits = obj(gap.get("fixed_watch_waits"))
    reasons = obj(waits.get("reason_counts"))
    known_waits = waits.get("known_source_wait_count", 0)
    from src.trading.market import session_contract

    context = session_contract.resolve_market_session(now) if now else None
    require(
        waits.get("schema") == "submission_monitor_fixed_watch_wait_census_v1"
        and waits.get("runtime_effect") is False
        and count(waits.get("count"))
        and count(waits.get("session_boundary_wait_count"))
        and count(waits.get("unclassified_or_actionable_wait_count"), maximum=0)
        and count(known_waits)
        and waits.get("count") == waits.get("session_boundary_wait_count") + known_waits
        and len(reasons) <= 16
        and all(count(value, minimum=1) for value in reasons.values())
        and set(reasons) <= _FIXED_SOURCE_WAIT_REASONS | {"session_generation_mismatch"}
        and reasons.get("session_generation_mismatch", 0)
        == waits.get("session_boundary_wait_count")
        and sum(v for k, v in reasons.items() if k != "session_generation_mismatch")
        == known_waits
        and context is not None
        and waits.get("native_session_regime") == context.session_regime
        and waits.get("native_entry_allowed_by_clock")
        is context.entry_allowed_by_clock,
        "excluded_fixed_watch_wait_not_proven_boundary",
    )
    for name in ("probe", "trace", "pending"):
        source = obj(sources.get(name))
        identity = obj(source.get("source_identity"))
        indexed_source = (
            source.get("coverage_basis") == "verified_forward_sentinel_source_window_v1"
        )
        if indexed_source:
            start = clock(source.get("coverage_started_at"))
            lower = clock(source.get("current_window_start_at"))
            cache_generation = source.get("cache_generation")
            lower_epoch = now.timestamp() - SOURCE_WINDOW_SEC if now else None
            if source.get("actor_lifetime_bound") is True:
                birth = (
                    _verified_health_actor_birth(
                        projections[0].get("actor_birth_proof"),
                        actor,
                        now,
                        result.get("observer_generation"),
                    )
                    if actor
                    else None
                )
                lower_epoch = (
                    max(lower_epoch, birth)
                    if birth is not None and lower_epoch is not None
                    else None
                )
            require(
                name == "probe"
                and start is not None
                and lower is not None
                and now is not None
                and start <= lower
                and lower.timestamp() == lower_epoch
                and source.get("cache_schema_version") in (19, 20, 21, 22)
                and isinstance(source.get("projection_contract"), str)
                and re.fullmatch("[0-9a-f]{64}", source["projection_contract"])
                is not None
                and source.get("historical_stage_coverage")
                == "not_backfilled_before_cache_offset"
                and isinstance(cache_generation, list)
                and len(cache_generation) == 5
                and all(count(v) for v in cache_generation)
                and count(source.get("source_size"))
                and count(
                    source.get("indexed_raw_offset"), maximum=source["source_size"]
                )
                and count(source.get("indexed_bytes_read"), maximum=SOURCE_TAIL_BYTES)
                and count(
                    source.get("indexed_identity_bytes_read"), maximum=SOURCE_TAIL_BYTES
                ),
                "indexed_source_window_proof_invalid:" + name,
            )
        if source.get("coverage_basis") == "current_actor_lifetime_bounded_tail":
            proof = projections[0].get("actor_birth_proof") if actor else None
            lower = _verified_health_actor_birth(
                proof, actor, now, result.get("observer_generation")
            )
            first = clock(source.get("first_read_at"))
            start = (
                max(now.timestamp() - SOURCE_WINDOW_SEC, lower)
                if lower is not None and now
                else None
            )
            require(
                start is not None
                and first is not None
                and first.timestamp() <= start
                and source.get("original_window_status") == "partial"
                and source.get("current_window_start_at")
                == datetime.fromtimestamp(start, KST).isoformat(),
                "actor_lifetime_source_coverage_invalid:" + name,
            )
        require(
            source.get("status") == "complete"
            and source.get("window_covered") is True
            and source.get("incomplete_last_line") is False
            and count(source.get("malformed_rows"), maximum=0)
            and count(source.get("missing_timestamp_rows"), maximum=0)
            and count(source.get("recent_count"))
            and count(source.get("read_count"), minimum=1, maximum=1)
            and count(
                source.get("bytes_read"),
                minimum=0 if indexed_source else 1,
                maximum=SOURCE_TAIL_BYTES,
            )
            and count(
                source.get("source_size"),
                minimum=(
                    source.get("bytes_read") if count(source.get("bytes_read")) else 1
                ),
            )
            and count(identity.get("device"))
            and count(identity.get("inode"), minimum=1)
            and not source.get("reason")
            and (
                "adjacent_partition" not in source
                or obj(source.get("adjacent_partition")).get("status") == "complete"
            ),
            "source_window_not_complete:" + name,
        )
    require(
        observed_valid
        and diagnostics_valid
        and count(obj(sources.get("probe")).get("recent_count"))
        and count(obj(sources.get("trace")).get("recent_count"))
        and observed.get("probe_results", 0) <= sources["probe"]["recent_count"]
        and observed.get("entry_traces", 0) <= sources["trace"]["recent_count"]
        and sum(v for k, v in diagnostics.items() if k.startswith("machine_probe:"))
        <= observed.get("probe_results", 0)
        and sum(v for k, v in diagnostics.items() if k.startswith("machine_trace:"))
        <= observed.get("entry_traces", 0),
        "source_observation_counts_invalid",
    )
    require(
        observed_valid
        and observed.get("auxiliary_required", 0) <= observed.get("entry_traces", 0)
        and observed.get("auxiliary_called", 0) <= observed.get("auxiliary_required", 0)
        and observed.get("auxiliary_cost_bound", 0)
        == observed.get("auxiliary_called", 0)
        and observed.get("auxiliary_pending_bound", 0)
        <= observed.get("auxiliary_pending", 0),
        "source_auxiliary_counts_invalid",
    )
    publication = obj(machine.get("publication"))
    selections = obj(machine.get("selection"))
    n, invalid, required = (
        machine.get(k)
        for k in (
            "observation_count",
            "source_invalid_count",
            "required_feature_guard_count",
        )
    )
    counts_valid = all(count(v, maximum=4096) for v in (n, invalid, required))
    scopes = obj(machine.get("scopes"))
    matched = 0
    scopes_valid = isinstance(machine.get("scopes"), dict) and len(scopes) <= 512
    if scopes_valid:
        for row in scopes.values():
            row = obj(row)
            if (
                not count(row.get("matched_receipts"), minimum=1)
                or not count(
                    row.get("live_pid_receipts"), maximum=row["matched_receipts"]
                )
                or row.get("current_bundle") is not True
            ):
                scopes_valid = False
                break
            matched += row["matched_receipts"]
    expected_machine = (
        "source_invalid_observed"
        if counts_valid and invalid + required
        else "observed_receipts_match" if counts_valid and n else "unobservable"
    )
    blockers = obj(machine.get("source_invalid_blockers"))
    require(
        counts_valid
        and invalid + required + matched == n
        and scopes_valid
        and isinstance(machine.get("source_invalid_blockers"), dict)
        and len(blockers) <= 64
        and all(
            isinstance(k, str)
            and 0 < len(k) <= 128
            and count(v, minimum=1, maximum=invalid + required)
            for k, v in blockers.items()
        ),
        "machine_receipt_counts_invalid",
    )
    require(
        machine.get("status") == expected_machine
        and machine.get("decision_authority") == "report_only"
        and machine.get("selection_family") == "continuous_reversal"
        and publication.get("status") == "native_frozen_family_verified"
        and publication.get("effective_date") == day
        and sha(machine.get("current_bundle_sha256"))
        and 0 < len(selections) <= 512
        and all(
            obj(row).get("score_contract_valid") is True for row in selections.values()
        )
        and count(machine.get("read_count"), minimum=1, maximum=1)
        and count(machine.get("read_limit_bytes"), minimum=1, maximum=8 * 1024 * 1024)
        and count(
            machine.get("bytes_read"),
            minimum=1,
            maximum=(
                machine["read_limit_bytes"]
                if count(machine.get("read_limit_bytes"))
                else 0
            ),
        )
        and count(
            machine.get("source_bytes"),
            minimum=(
                machine.get("bytes_read") if count(machine.get("bytes_read")) else 1
            ),
        )
        and machine.get("window_coverage") in ("bounded_suffix", "complete_file_prefix")
        and machine.get("action_replay_performed") is False,
        "machine_selection_or_source_not_verified",
    )
    role_partition = machine.get("observation_role_partition")
    role_proof = (
        _verified_machine_role_partition(
            role_partition,
            actor,
            now,
            machine.get("current_bundle_sha256"),
            n,
            invalid,
            required,
        )
        if role_partition is not None and counts_valid and actor is not None and now
        else None
    )
    require(
        role_partition is None or role_proof is not None,
        "machine_role_partition_invalid",
    )
    provider_n = role_proof["count"] if role_proof is not None else n
    provider_invalid = role_proof["invalid"] if role_proof is not None else invalid
    provider_required = role_proof["required"] if role_proof is not None else required
    async_view = obj(result.get("async_disposition_coverage"))
    attempts = async_view.get("attempt_projection", [])
    if actor and isinstance(attempts, list):
        attempts = [r for r in attempts if _row_actor(obj(r)) in (None, actor)]
    attempts_valid = isinstance(attempts, list) and len(attempts) <= 1024
    async_groups = defaultdict(list)
    if attempts_valid:
        for item in attempts:
            fields = obj(obj(item).get("fields"))
            key = tuple(
                fields.get(k)
                for k in (
                    "async_producer_pid",
                    "async_producer_start_ticks",
                    "evaluation_attempt_id",
                    "ai_decision_trace_id",
                )
            )
            if not fields or not all(
                isinstance(v, str) and 0 < len(v) <= 256 for v in key
            ):
                attempts_valid = False
                break
            async_groups[key].append(item)

    rejection_guards = native_invalidation | {
        "result_deadline_expired",
        "generation_superseded",
        "target_not_watching",
        "state_version_changed",
        "position_or_pending_order_present",
        "cooldown_active",
    }
    nonexecution_guards = {
        "generation_invalidated",
        "coordinator_shutdown",
        "result_retention_overflow",
    }
    direct_guards = {
        "first_ai_wait",
        "entry_machine_source_wait",
        "blocked_big_bite_hard_gate",
        "entry_cooldown_active",
        "buy_side_paused",
        "operator_manual_control_excluded_symbol",
        "before_strategy_start",
        "result_deadline_expired",
        "machine_observation_revision_recheck",
        "original_async_result_already_submitted",
        "pre_submit_delay_pending",
        "pre_submit_delay_due_recheck_blocked",
        "initial_quantity_sequential_plan_block",
        "entry_execution_sizing_plan_block",
        "entry_split_probe_first_deferred",
        "residual_blocked",
    }

    def closed_pass(row):
        key = tuple(
            row.get(k)
            for k in (
                "producer_pid",
                "producer_start_ticks",
                "evaluation_attempt_id",
                "decision_trace_id",
            )
        )
        if (
            not attempts_valid
            or not all(isinstance(v, str) for v in key)
            or async_view.get("coverage") != "bounded_trace_projection_complete"
            or async_view.get("denominator_partial") is not False
        ):
            return False
        selected = async_groups.get(key, [])
        if not selected:
            return False
        bindings, finals, returned, event_ids = set(), set(), [], {}
        for item in selected:
            fields = item["fields"]
            at = clock(item.get("emitted_at"))
            disposition = fields.get("async_disposition")
            request = fields.get("async_request_id")
            event_id = fields.get("async_disposition_event_id")
            if (
                at is None
                or now is None
                or not 0 <= (now - at).total_seconds() <= SOURCE_WINDOW_SEC
                or fields.get("entry_machine_bundle_sha256")
                != row.get("machine_bundle_sha256")
                or not isinstance(request, str)
                or not 0 < len(request) <= 512
                or not sha(event_id)
                or str(fields.get("async_machine_action")).upper() != "ENTER_NOW"
                or str(fields.get("async_auxiliary_verdict")).upper() != "PASS"
                or str(fields.get("async_provider_called")).lower() != "true"
            ):
                return False
            fingerprint = json.dumps(fields, sort_keys=True, default=str)
            if event_id in event_ids and event_ids[event_id] != fingerprint:
                return False
            event_ids[event_id] = fingerprint
            bindings.add(request)
            if disposition in (
                "accepted_to_entry_path",
                "rejected",
                "terminal_nonexecution",
            ):
                reason = fields.get("async_disposition_reason")
                if not isinstance(reason, str) or len(reason) > 128:
                    return False
                finals.add((disposition, reason))
            elif disposition == "entry_path_returned":
                returned.append(fields)
        if len(bindings) != 1 or len(finals) != 1:
            return False
        disposition, reason = next(iter(finals))
        if disposition == "rejected":
            return reason in rejection_guards
        if disposition == "terminal_nonexecution":
            return reason in nonexecution_guards
        if reason != "commit_allowed" or not returned:
            return False
        evidence = {
            (
                r.get("async_disposition_reason"),
                r.get("async_entry_submit_attempt_id"),
                str(r.get("async_entry_broker_attempts")),
                str(r.get("async_entry_broker_accepted")),
                str(r.get("async_entry_submit_outcome")),
                str(r.get("async_entry_physical_send_blocked")),
                str(r.get("async_entry_physical_send_attempts")),
                str(r.get("async_entry_arm_released")),
            )
            for r in returned
            if all(
                r.get(k) is None or isinstance(r.get(k), (str, int, bool))
                for k in (
                    "async_disposition_reason",
                    "async_entry_submit_attempt_id",
                    "async_entry_broker_attempts",
                    "async_entry_broker_accepted",
                    "async_entry_submit_outcome",
                    "async_entry_physical_send_blocked",
                    "async_entry_physical_send_attempts",
                    "async_entry_arm_released",
                )
            )
        }
        if len(evidence) != 1:
            return False
        (
            stop,
            submit,
            broker_attempts,
            accepted,
            outcome,
            physical_blocked,
            physical_attempts,
            arm_released,
        ) = next(iter(evidence))
        if stop in {"latency_block", "entry_physical_send_guard_block"}:
            local_return = (
                isinstance(submit, str)
                and 0 < len(submit) <= 256
                and accepted.lower() == "false"
                and outcome == "returned_false"
                and arm_released.lower() == "true"
            )
            if stop == "latency_block":
                return (
                    local_return
                    and broker_attempts in {"None", "0"}
                    and physical_blocked.lower() in {"none", "false"}
                    and physical_attempts in {"None", "0"}
                )
            return (
                local_return
                and broker_attempts == "0"
                and physical_blocked.lower() == "true"
                and physical_attempts == "0"
            )
        if stop in direct_guards:
            return True
        return (
            stop
            in {
                "order_bundle_submitted",
                "entry_path_returned_without_terminal_evidence",
            }
            and isinstance(submit, str)
            and 0 < len(submit) <= 256
            and broker_attempts.isdigit()
            and 0 < int(broker_attempts) <= 100
            and accepted.lower() == "true"
            and outcome in ("True", "true")
        )

    lineage = obj(machine.get("reversal_provider_lineage"))
    ledger_by_key = {}
    if lineage or counts_valid and provider_n:
        ledger = lineage.get("attempt_ledger")
        exact = lineage.get("exact_pid_filter")
        exact_valid = (
            isinstance(exact, list)
            and len(exact) == 2
            and all(
                isinstance(v, str) and v.isdigit() and 0 < len(v) <= 20 and int(v) > 0
                for v in exact
            )
        )
        ledger_valid = isinstance(ledger, list) and len(ledger) <= 4096
        guard_count = recheck_count = entered = passed = effective_passed = 0
        verdict_counts = Counter()
        hashes = set()
        if ledger_valid:
            for row in ledger:
                row = obj(row)
                captured = clock(row.get("trace_decision_ts"))
                action = row.get("machine_action")
                digest = row.get("machine_observation_sha256")
                screen = row.get("effective_screen_status")
                if (
                    not sha(digest)
                    or digest in hashes
                    or not exact_valid
                    or [row.get("producer_pid"), row.get("producer_start_ticks")]
                    != exact
                    or not isinstance(row.get("evaluation_attempt_id"), str)
                    or not row["evaluation_attempt_id"]
                    or len(row["evaluation_attempt_id"]) > 256
                    or not isinstance(row.get("decision_trace_id"), str)
                    or not 0 < len(row["decision_trace_id"]) <= 256
                    or row.get("machine_bundle_sha256")
                    != machine.get("current_bundle_sha256")
                    or captured is None
                    or now is None
                    or not 0 <= (now - captured).total_seconds() <= WINDOW_SEC
                    or action not in ("SOURCE_INVALID", "RECHECK", "BLOCK", "ENTER_NOW")
                    or not isinstance(screen, str)
                    or len(screen) > 96
                    or row.get("timeout") is not False
                ):
                    ledger_valid = False
                    break
                errors = row.get("execution_errors")
                raw = row.get("raw_verdict")
                if action != "ENTER_NOW":
                    allowed_screens = {
                        "SOURCE_INVALID": ("not_requested_machine_source_invalid",),
                        "BLOCK": ("not_requested_machine_nonentry",),
                        "RECHECK": (
                            "not_requested_machine_nonentry",
                            "not_requested_required_feature_insufficient",
                        ),
                    }
                    valid = (
                        screen in allowed_screens[action]
                        and all(
                            row.get(k) is None
                            for k in (
                                "raw_verdict",
                                "auxiliary_response_contract_valid",
                                "post_response_execution_valid",
                            )
                        )
                        and all(
                            row.get(k) is False
                            for k in (
                                "request_prepared",
                                "transmission_attempt_observed",
                                "raw_response_observed",
                            )
                        )
                        and errors == []
                    )
                else:
                    entered += 1
                    valid = (
                        all(
                            row.get(k) is True
                            for k in (
                                "request_prepared",
                                "transmission_attempt_observed",
                                "raw_response_observed",
                                "auxiliary_response_contract_valid",
                            )
                        )
                        and raw in ("CAUTION", "VETO", "PASS")
                        and type(row.get("post_response_execution_valid")) is bool
                        and isinstance(errors, list)
                        and len(errors) <= 8
                        and all(
                            isinstance(v, str) and v in native_invalidation
                            for v in errors
                        )
                    )
                    if valid and raw == "PASS":
                        passed += 1
                        effective_passed += (
                            row["post_response_execution_valid"] is True
                            and screen == "pass"
                        )
                        valid = closed_pass(row) and (
                            row["post_response_execution_valid"] is False
                            and bool(errors)
                            or row["post_response_execution_valid"] is True
                            and screen == "pass"
                            and not errors
                        )
                    elif valid:
                        valid = (
                            screen == raw.lower()
                            and row["post_response_execution_valid"] is True
                            and not errors
                        )
                    if valid:
                        verdict_counts[raw] += 1
                if not valid:
                    ledger_valid = False
                    break
                hashes.add(digest)
                ledger_by_key[
                    tuple(
                        row.get(k)
                        for k in (
                            "producer_pid",
                            "producer_start_ticks",
                            "evaluation_attempt_id",
                            "decision_trace_id",
                        )
                    )
                ] = row
                guard_count += action == "SOURCE_INVALID"
                recheck_count += action == "RECHECK"
        windows = obj(lineage.get("source_windows"))
        require(
            lineage.get("status")
            in (("observed", "not_observed") if provider_n == 0 else ("observed",))
            and lineage.get("issues") == {}
            and lineage.get("source_gaps") == {}
            and count(lineage.get("exact_attempt_join_gap_count"), maximum=0)
            and lineage.get("decision_authority") == "report_only"
            and lineage.get("current_pid_coverage") == "exact_live_pid"
            and count(lineage.get("machine_observation_count"))
            and lineage["machine_observation_count"] == provider_n
            and count(lineage.get("trace_attempt_count"))
            and ledger_valid
            and len(ledger) == lineage["trace_attempt_count"] == provider_n
            and (role_proof is None or hashes == role_proof["hashes"])
            and counts_valid
            and guard_count == provider_invalid
            and recheck_count >= provider_required
            and set(windows) == {"requests", "traces"}
            and all(
                obj(v).get("status") == "complete"
                and obj(v).get("window_covered") is True
                and count(obj(v).get("malformed_rows"), maximum=0)
                and count(obj(v).get("missing_timestamp_rows"), maximum=0)
                and obj(v).get("incomplete_last_line") is False
                for v in windows.values()
            )
            and all(
                count(lineage.get(k)) and lineage[k] == entered
                for k in (
                    "request_prepared_count",
                    "provider_transmission_attempt_count",
                    "raw_response_observed_count",
                    "auxiliary_response_contract_valid_count",
                )
            )
            and all(
                count(lineage.get(k), maximum=0)
                for k in ("provider_timeout_count", "enter_without_request_observed")
            )
            and count(lineage.get("valid_pass_count"))
            and lineage["valid_pass_count"] == passed
            and count(lineage.get("raw_pass_count"))
            and lineage["raw_pass_count"] == passed
            and count(lineage.get("execution_valid_pass_count"))
            and lineage["execution_valid_pass_count"] == effective_passed
            and lineage.get("raw_verdict_counts") == dict(verdict_counts),
            "machine_provider_lineage_not_recorded_guard_or_nonentry",
        )
        if role_proof is not None:
            rows = lineage.get("attempt_ledger")
            hash_rows_valid = isinstance(rows, list) and all(
                isinstance(row, dict)
                and (
                    row.get("machine_observation_sha256") is None
                    or sha(row.get("machine_observation_sha256"))
                )
                for row in rows
            )
            observed_hashes = (
                {
                    row["machine_observation_sha256"]
                    for row in rows
                    if row.get("machine_observation_sha256") is not None
                }
                if hash_rows_valid
                else set()
            )
            missing = role_proof["hashes"] - observed_hashes
            require(
                hash_rows_valid
                and observed_hashes <= role_proof["hashes"]
                and len(missing)
                == obj(lineage.get("source_gaps")).get(
                    "observation_trace_unresolved", 0
                ),
                "machine_provider_role_hash_partition_mismatch",
            )
    require(
        attempts_valid
        and all(
            (
                str(item["fields"].get("async_machine_action")).upper()
                in ("SOURCE_INVALID", "RECHECK", "BLOCK")
                and str(item["fields"].get("async_provider_called")).lower() == "false"
                and str(item["fields"].get("async_auxiliary_verdict")).upper() != "PASS"
            )
            or key in ledger_by_key
            and ledger_by_key[key].get("machine_action") == "ENTER_NOW"
            and str(item["fields"].get("async_machine_action")).upper() == "ENTER_NOW"
            and str(item["fields"].get("async_auxiliary_verdict")).upper()
            == ledger_by_key[key].get("raw_verdict")
            for key, rows in async_groups.items()
            for item in rows
        ),
        "pending_or_withheld_auxiliary_pass_not_quiet",
    )
    bootstrap = obj(execution.get("bootstrap"))
    split, delay = obj(execution.get("entry_split")), obj(
        execution.get("pre_submit_delay")
    )
    proof = obj(split.get("verification_receipt"))
    native = obj(proof.get("native_validation"))
    split_date = clock(split.get("source_date"))
    require(
        execution.get("schema") == "entry_execution_tuning_semantics_v1"
        and clock(execution.get("as_of")) == now
        and execution.get("status") == "observed"
        and execution.get("decision_authority") == "report_only"
        and execution.get("runtime_effect") is False
        and execution.get("allowed_runtime_apply") is False
        and execution.get("actual_order_submitted") is False
        and bootstrap.get("status") == "verified"
        and bootstrap.get("verify_status") == "pass"
        and bootstrap.get("policy_pid_consumption_proven") is False,
        "execution_or_bootstrap_not_verified",
    )
    require(
        split.get("verification") == "verified"
        and split.get("read_mode") == "verified_monitor_projection"
        and proof.get("verified") is True
        and proof.get("role") == "submission_monitor"
        and proof.get("source_date") == split.get("source_date")
        and isinstance(split.get("source_date"), str)
        and len(split["source_date"]) == 10
        and split_date is not None
        and now is not None
        and split_date <= now
        and split.get("status")
        in ("source_gap", "candidate_observed", "no_candidate_observed")
        and not split.get("reason")
        and not split.get("error")
        and all(
            sha(proof.get(k))
            for k in (
                "generation_id",
                "report_sha256",
                "policy_sha256",
                "manifest_sha256",
            )
        )
        and native
        == {
            "reason": "generation_binding_valid",
            "scope": "full_report_policy_native_contract",
            "status": "verified",
        }
        and count(proof.get("full_report_bytes_read"), maximum=0)
        and count(proof.get("metadata_bytes_read"), minimum=1, maximum=512 * 1024)
        and number(proof.get("consumer_elapsed_ms"))
        and proof["consumer_elapsed_ms"] >= 0
        and split.get("policy_generation_binding") == "matched"
        and split.get("prepared_effective_date") == day
        and split.get("policy_runtime_apply_allowed") is False,
        "split_projection_not_verified",
    )
    require(
        delay.get("status") == "verified_policy_bound"
        and delay.get("bootstrap_handoff_match") is True
        and delay.get("bootstrap_env_match") is True
        and delay.get("runtime_effect") is False
        and delay.get("effective_from") == day
        and delay.get("report_blockers") == [],
        "delay_policy_not_verified",
    )
    incidents = result.get("incidents")
    incidents_valid = isinstance(incidents, dict) and len(incidents) <= 256
    historical_incident_keys = set()
    if incidents_valid:
        for incident_key, incident in incidents.items():
            incident = obj(incident)
            status = incident.get("status")
            last = clock(incident.get("last_seen"))
            scanner_birth = (
                _verified_health_actor_birth(
                    projections[0].get("actor_birth_proof"),
                    actor,
                    now,
                    result.get("observer_generation"),
                )
                if actor and now
                else None
            )
            if (
                last is not None
                and now is not None
                and last <= now
                and _historical_scanner_incident(
                    incident_key,
                    incident,
                    obj(result.get("machine_semantics")).get(
                        "historical_scanner_observations"
                    ),
                    actor,
                    scanner_birth,
                    now,
                )
            ):
                historical_incident_keys.add(incident_key)
                continue
            owner = {
                "machine_auxiliary_intraday_source_gap": 0,
                "machine_policy_receipt_contract": 1,
            }.get(incident_key)
            birth_lower = (
                _verified_health_actor_birth(
                    projections[owner].get("actor_birth_proof"),
                    actor,
                    now,
                    result.get("observer_generation"),
                )
                if actor and owner is not None and now
                else None
            )
            # Incident last_seen is the aggregation clock. An unresolved known
            # owner recorded before this verified process birth cannot become
            # a new-PID failure merely because its aggregation is <10 min old.
            historical_cohort = (
                actor is not None
                and owner is not None
                and obj(projections[owner].get("view")).get("issues") == {}
                and (
                    incident.get("current_status") == "historical_not_current_cohort"
                    and count(
                        projections[owner].get("excluded_observation_count"), minimum=1
                    )
                    or status == "historical_unresolved"
                    and last is not None
                    and birth_lower is not None
                    and last.timestamp() < birth_lower
                )
            )
            # A prior PID's exact delay/bootstrap mismatch is historical only
            # after the current native contracts independently verify. Keep the
            # old incident bytes/status; an empty current issue list alone is
            # never recovery evidence.
            if incident_key == "entry_execution_tuning_receipt_contract":
                birth_lower = (
                    _verified_health_actor_birth(
                        projections[0].get("actor_birth_proof"),
                        actor,
                        now,
                        result.get("observer_generation"),
                    )
                    if actor and now
                    else None
                )
                old_issues = obj(incident.get("issues"))
                historical_cohort = bool(
                    status == "historical_unresolved"
                    and last is not None
                    and birth_lower is not None
                    and last.timestamp() < birth_lower
                    and incident.get("scope") == "entry_split|pre_submit_delay"
                    and incident.get("rule") == incident_key
                    and old_issues
                    and set(old_issues)
                    <= {
                        "pre_submit_delay_bootstrap_handoff_mismatch",
                        "pre_submit_delay_bootstrap_env_mismatch",
                    }
                    and all(count(v, minimum=1) for v in old_issues.values())
                    and execution.get("issues") == {}
                    and bootstrap.get("pid_passed") is True
                    and sha(delay.get("policy_sha256"))
                    and not set(failed)
                    & {
                        "execution_or_bootstrap_not_verified",
                        "split_projection_not_verified",
                        "delay_policy_not_verified",
                    }
                )
            if historical_cohort:
                historical_incident_keys.add(incident_key)
            if (
                status
                not in (
                    "historical_unresolved",
                    "recovered",
                    "superseded_alias",
                    "reclassified",
                )
                or not last
                or not now
                or last > now
                or status == "historical_unresolved"
                and (now - last).total_seconds() <= SOURCE_WINDOW_SEC
                and not historical_cohort
            ):
                incidents_valid = False
                # Finish the bounded scan: later exact old-PID evidence must
                # still be classified for the warning-only quality path.
    require(incidents_valid, "active_current_or_unknown_incident")
    # A completed bounded report can faithfully report incomplete source/AI
    # outcomes. Preserve every original quality failure without relabelling the
    # report's successful publication as an execution failure. This second path
    # grants WARNING only; it cannot validate a decision, PASS or trade.
    soft = {
        "current_failure_or_diagnostic_present",
        "source_population_not_unassessed",
        "source_window_not_complete:probe",
        "source_window_not_complete:trace",
        "source_window_not_complete:pending",
        "machine_selection_or_source_not_verified",
        "machine_provider_lineage_not_recorded_guard_or_nonentry",
        "pending_or_withheld_auxiliary_pass_not_quiet",
        "active_current_or_unknown_incident",
    }
    # Observing scanner rows and in-flight AI/PASS outcomes are a valid bounded
    # report state too. Revalidate publication and provenance before permitting
    # this warning-only path; unknown state, stale input and source defects stay
    # failures. Keep all original diagnostics and never claim full validation.
    active_report_valid = (
        report_execution_valid
        and input_provenance_valid
        and result.get("status") == "observing"
        and result.get("blocker") is None
        and count(inp.get("row_count"), minimum=1)
        and isinstance(result.get("scopes"), dict)
        and 0 < len(result["scopes"]) <= 512
        and all(
            isinstance(key, str) and 0 < len(key) <= 512 and isinstance(value, dict)
            for key, value in result["scopes"].items()
        )
    )
    quiet_report_valid = (
        report_execution_valid
        and input_provenance_valid
        and result.get("status") == "unobservable"
        and result.get("scopes") == {}
        and result.get("blocker")
        in (
            "missing_stale_or_noncurrent_sentinel_evidence",
            "no_identified_scanner_machine_evaluation",
        )
    )
    if active_report_valid or quiet_report_valid:
        soft.update(
            {
                "monitor_state_not_quiet_full_observation",
                "scanner_population_not_quiet",
            }
        )

    # Request/pending journals are created lazily. A complete current-actor
    # trace can prove that every observed attempt stopped before assessment,
    # while those absent journals remain explicitly unobservable. This permits
    # bounded source-quality WARNING only, never source/decision validation.
    preassessment_counts = [
        diagnostics.get("machine_trace:" + reason, 0)
        for reason in (
            "source_quality_blocked_before_assessment",
            "required_feature_blocked_before_assessment",
        )
    ]
    preassessment_traces = (
        sum(preassessment_counts)
        if all(count(v) for v in preassessment_counts)
        else None
    )
    lazy_auxiliary_absence = (
        counts_valid
        and n == provider_n == 0
        and "source_window_not_complete:trace" not in failed
        and count(observed.get("entry_traces"), minimum=1)
        and preassessment_traces == observed["entry_traces"]
        and all(
            count(observed.get(k, 0), maximum=0)
            for k in (
                "auxiliary_required",
                "auxiliary_called",
                "auxiliary_cost_bound",
                "auxiliary_pending",
                "auxiliary_pending_bound",
            )
        )
        and lineage.get("attempt_ledger") == []
        and lineage.get("source_gaps") == {}
        and all(
            count(lineage.get(k), maximum=0)
            for k in (
                "machine_observation_count",
                "trace_attempt_count",
                "request_prepared_count",
                "provider_transmission_attempt_count",
                "raw_response_observed_count",
                "auxiliary_response_contract_valid_count",
                "raw_pass_count",
                "valid_pass_count",
                "execution_valid_pass_count",
                "provider_timeout_count",
                "enter_without_request_observed",
                "exact_attempt_join_gap_count",
            )
        )
    )

    # With no current attempts, every strict health check must already pass
    # except the lazy pending file. The bounded path still verifies actor birth
    # and all native readers, and retains the missing-source condition.
    quiet_pending_absence = (
        counts_valid
        and n == provider_n == 0
        and set(failed) == {"source_window_not_complete:pending"}
        and count(observed.get("entry_traces", 0), maximum=0)
    )

    # These journals are append-created by the first assessment. Before the
    # native morning entry window, their absence is observation-not-due, not
    # a broken reader. This never proves an empty population or source health.
    # The morning bound prevents an afternoon closed window from forgiving
    # sources that should already have existed during regular trading.
    quiet_lazy_population = (
        quiet_report_valid
        and event_marker
        and counts_valid
        and n == provider_n == 0
        and observed_valid
        and not any(observed.values())
        and not diagnostics
        and not lineage
        and attempts == []
        and gap.get("async_pass_projection") == []
        and gap.get("async_transition_projection") == []
        and count(gap.get("async_pass_unmapped_count"), maximum=0)
    )
    pre_entry_absence = (
        quiet_lazy_population
        and inp.get("sentinel_classification") == "NOT_YET_DUE"
        and context is not None
        and context.entry_allowed_by_clock is False
        and now.hour < 9
        and all(not rows for rows in route_counts)
        and all(
            obj(source).get("status") in ("complete", "unobservable")
            for source in sources.values()
        )
        and count(machine.get("source_invalid_count"), maximum=0)
        and count(machine.get("required_feature_guard_count"), maximum=0)
        and machine.get("source_invalid_blockers") == {}
        and any(
            obj(source).get("reason") == "FileNotFoundError"
            for source in sources.values()
        )
    )

    # A complete native probe census may contain only verified fixed-watch
    # waits (warmup/source guard), including after the market opens. No trace
    # or outcome journal has been due for these pre-assessment waits. Require
    # every source row to reconcile; absence of the probe itself never qualifies.
    lazy_wait_trace_absence = (
        quiet_lazy_population
        and count(waits.get("count"), minimum=1)
        and waits["count"] == obj(sources.get("probe")).get("recent_count")
        and "excluded_fixed_watch_wait_not_proven_boundary" not in failed
        and "source_window_not_complete:probe" not in failed
        and "indexed_source_window_proof_invalid:probe" not in failed
    )

    def clean_reader(source, maximum, window=SOURCE_WINDOW_SEC, source_name=None):
        source = obj(source)
        identity = obj(source.get("source_identity"))
        if (
            source_name in ("pending", "requests")
            and lazy_auxiliary_absence
            or source_name == "pending"
            and quiet_pending_absence
            or source_name in ("trace", "pending")
            and lazy_wait_trace_absence
            or source_name in ("probe", "trace", "pending")
            and pre_entry_absence
        ) and source.get("status") == "unobservable":
            return (
                set(source)
                == {
                    "status",
                    "tail_truncated",
                    "window_covered",
                    "recent_count",
                    "reason",
                }
                and source.get("reason") == "FileNotFoundError"
                and source.get("tail_truncated") is False
                and source.get("window_covered") is False
                and count(source.get("recent_count"), maximum=0)
            )
        # A validated native forward index can cover the whole interval without
        # a raw append read. Reuse the exact proof checks above, not bytes>0.
        if (
            source_name == "probe"
            and source.get("coverage_basis")
            == "verified_forward_sentinel_source_window_v1"
            and "indexed_source_window_proof_invalid:probe" not in failed
            and "source_window_not_complete:probe" not in failed
        ):
            return True
        if (
            source_name == "traces"
            and source.get("coverage_basis")
            == "native_index_projection_or_exact_raw_offset_size_sha256"
        ):
            from src.engine.automation.main_trailing_source_store import encode

            generation = obj(source.get("native_index_generation"))
            metadata = generation.get("source_stat")
            raw_bytes, index_bytes, reads = (
                source.get(k) for k in ("bytes_read", "index_bytes_read", "read_count")
            )
            return (
                set(generation)
                == {
                    "schema",
                    "path",
                    "size",
                    "namespace",
                    "source_stat",
                    "catchup_end",
                    "raw_records",
                    "selected_records",
                    "prefix_chain_sha256",
                    "append_chain_sha256",
                    "whole_file_sha256",
                    "sha256",
                }
                and generation.get("schema")
                == "main_trailing_indexed_source_v1:generation"
                and generation.get("path") == f"ai_decision_trace_{day}.jsonl"
                and generation.get("namespace") == "ai_decision_trace"
                and isinstance(metadata, list)
                and len(metadata) == 5
                and all(count(v) for v in metadata)
                and count(metadata[1], minimum=1)
                and count(identity.get("device"))
                and count(identity.get("inode"), minimum=1)
                and identity == {"device": metadata[0], "inode": metadata[1]}
                and count(source.get("source_size"), minimum=1)
                and count(generation.get("size"), minimum=1)
                and generation["size"] == metadata[2] == source["source_size"]
                and count(generation.get("catchup_end"), maximum=generation["size"])
                and count(generation.get("raw_records"))
                and count(
                    generation.get("selected_records"),
                    maximum=generation["raw_records"],
                )
                and count(
                    source.get("recent_count"), maximum=generation["selected_records"]
                )
                and generation.get("whole_file_sha256") is False
                and all(
                    sha(generation.get(k))
                    for k in ("sha256", "prefix_chain_sha256", "append_chain_sha256")
                )
                and generation["sha256"]
                == hashlib.sha256(
                    encode({k: v for k, v in generation.items() if k != "sha256"})
                ).hexdigest()
                and source.get("status") == "complete"
                and source.get("window_covered") is True
                and source.get("tail_truncated") is False
                and source.get("incomplete_last_line") is False
                and count(source.get("malformed_rows"), maximum=0)
                and count(source.get("missing_timestamp_rows"), maximum=0)
                and count(raw_bytes, maximum=maximum)
                and count(index_bytes, maximum=maximum)
                and raw_bytes + index_bytes <= maximum
                and raw_bytes <= generation["size"]
                and count(reads, maximum=source["recent_count"])
                and ((reads == 0) == (raw_bytes == 0))
                and (source["recent_count"] == 0 or index_bytes > 0)
                and not source.get("reason")
                and "adjacent_partition" not in source
            )
        base = (
            source.get("incomplete_last_line") is False
            and count(source.get("malformed_rows"), maximum=0)
            and count(source.get("missing_timestamp_rows"), maximum=0)
            and count(source.get("recent_count"))
            and count(source.get("read_count"), minimum=1, maximum=1)
            and count(source.get("bytes_read"), minimum=1, maximum=maximum)
            and count(
                source.get("source_size"),
                minimum=(
                    source.get("bytes_read") if count(source.get("bytes_read")) else 1
                ),
            )
            and count(identity.get("device"))
            and count(identity.get("inode"), minimum=1)
            and not source.get("reason")
            and (
                "adjacent_partition" not in source
                or obj(source.get("adjacent_partition")).get("status") == "complete"
            )
        )
        if not base:
            return False
        if source.get("coverage_basis") == "current_lineage_window_bounded_tail":
            first, lower = clock(source.get("first_read_at")), clock(
                source.get("current_window_start_at")
            )
            if (
                source.get("original_window_status") != "partial"
                or source.get("tail_truncated") is not True
                or not count(
                    source.get("current_window_seconds"), minimum=window, maximum=window
                )
                or first is None
                or lower is None
                or now is None
                or first > lower
                or (now - lower).total_seconds() != window
            ):
                return False
        if source.get("status") == "complete" and source.get("window_covered") is True:
            return True
        first = clock(source.get("first_read_at"))
        return (
            source.get("status") == "partial"
            and source.get("window_covered") is False
            and source.get("tail_truncated") is True
            and first is not None
            and now is not None
            and first <= now
            and (now - first).total_seconds() < window
            and source["source_size"] > source["bytes_read"]
        )

    bounded = False
    if failed and set(failed) <= soft:
        generation = obj(result.get("observer_generation"))
        birth = obj(generation.get("actor_birth_proof"))
        actor_valid = (
            actor is not None
            and generation.get("status") == "current"
            and generation.get("generation_current") is True
            and generation.get("selector_reported_actual_pid_consumed") is True
            and _verified_health_actor_birth(birth, actor, now, generation) is not None
            and all(p.get("actor_birth_proof") == birth for p in projections)
        )
        # This source-quality aggregate is derived by this producer from exact
        # complete-reader route counts. Keep the issue and its domain alert;
        # it is not a failed artifact publication or a contract exception.
        expected_coverage = {}
        if (
            obj(sources.get("probe")).get("status") == "complete"
            and obj(sources.get("probe")).get("window_covered") is True
        ):
            for route, total in route_counts[0].items():
                covered = route_counts[2].get(route, 0)
                if (
                    route in {"krx_only", "nxt_only", "krx_nxt_integrated"}
                    and count(total, minimum=10)
                    and count(covered)
                    and covered * 5 < total
                ):
                    expected_coverage["machine_probe:coverage_degraded:" + route] = 1
        aggregate = obj(gap.get("issues"))
        scoped_aggregate = obj(gap.get("issues_by_scope"))
        expected_scopes = {
            "route:" + key.rsplit(":", 1)[1] + "|machine_probe:coverage_degraded": 1
            for key in expected_coverage
        }
        route_bounds = set(route_counts[0]) <= {
            "krx_only",
            "nxt_only",
            "krx_nxt_integrated",
        } and all(
            set(rows) <= set(route_counts[0])
            and all(
                count(v, maximum=route_counts[0][route]) for route, v in rows.items()
            )
            for rows in route_counts[1:]
        )
        coverage_quality = (
            route_bounds
            and gap.get("coverage_alert_floor")
            == "10_same_route_unique_probes_below_20pct_source_covered"
            and gap.get("coverage_success_contract")
            == "valid_machine_capture_or_exact_native_all_false_receipt"
            and bool(expected_coverage)
            and aggregate == expected_coverage
            and scoped_aggregate == expected_scopes
            and all(
                count(value, minimum=1, maximum=1)
                for value in (*aggregate.values(), *scoped_aggregate.values())
            )
        )
        stages_clean = (
            (
                gap.get("issues") == {}
                and gap.get("issues_by_scope", {}) == {}
                or coverage_quality
            )
            and all(
                stage.get("issues") == {} and stage.get("issues_by_scope", {}) == {}
                for stage in (machine, execution)
            )
            and all(
                all(
                    stage.get(k) in (None, "")
                    or stage is machine
                    and k == "source_status"
                    and pre_entry_absence
                    and stage[k] == "unobservable:FileNotFoundError"
                    for k in (
                        "selection_status",
                        "source_status",
                        "error",
                        "errors",
                        "reason",
                    )
                )
                for stage in stages
            )
            and result.get("issues", {}) == {}
            and result.get("diagnostics", {}) == {}
            and all(
                stage.get("provider_lineage_source_status") in (None, "")
                for stage in (gap, execution)
            )
            and machine.get("provider_lineage_source_status")
            in (None, "", "partial_source_gap")
            and isinstance(result.get("notification_pending"), list)
            # Pending delivery does not change exact prior-PID membership.
            # Keep the queue and original incident; unknown/current keys fail.
            and all(
                isinstance(key, str)
                and (
                    key == "machine_auxiliary_intraday_source_gap"
                    or key in historical_incident_keys
                )
                for key in result["notification_pending"]
            )
        )
        source_shape = (
            gap.get("schema") == "machine_auxiliary_intraday_source_semantics_v1"
            and clock(gap.get("as_of")) == now
            and gap.get("status") == expected_gap
            and gap.get("runtime_effect") is False
            and gap.get("decision_authority") == "report_only"
            and observed_valid
            and set(sources) == {"probe", "trace", "pending"}
            and gap.get("async_transition_projection_coverage")
            in ("complete", "partial")
            and gap.get("async_pass_projection_coverage") in ("complete", "partial")
            and isinstance(gap.get("async_pass_projection"), list)
            and len(gap["async_pass_projection"]) <= 128
            and isinstance(gap.get("async_transition_projection"), list)
            and len(gap["async_transition_projection"]) <= 1024
            and count(gap.get("async_pass_unmapped_count"))
            and all(
                clean_reader(source, SOURCE_TAIL_BYTES, source_name=name)
                for name, source in sources.items()
            )
        )
        machine_shape = (
            machine.get("status") in (expected_machine, "partial_unobservable")
            and machine.get("decision_authority") == "report_only"
            and machine.get("selection_family") == "continuous_reversal"
            and publication.get("status") == "native_frozen_family_verified"
            and publication.get("effective_date") == day
            and sha(machine.get("current_bundle_sha256"))
            and 0 < len(selections) <= 512
            and all(
                obj(row).get("score_contract_valid") is True
                for row in selections.values()
            )
            and (
                pre_entry_absence
                and machine.get("source_status") == "unobservable:FileNotFoundError"
                and all(
                    k not in machine
                    for k in (
                        "read_count",
                        "bytes_read",
                        "source_bytes",
                        "window_coverage",
                    )
                )
                or count(machine.get("read_count"), minimum=1, maximum=1)
                and count(
                    machine.get("read_limit_bytes"), minimum=1, maximum=8 * 1024 * 1024
                )
                and count(
                    machine.get("bytes_read"),
                    minimum=1,
                    maximum=(
                        machine["read_limit_bytes"]
                        if count(machine.get("read_limit_bytes"))
                        else 0
                    ),
                )
                and count(
                    machine.get("source_bytes"),
                    minimum=(
                        machine.get("bytes_read")
                        if count(machine.get("bytes_read"))
                        else 1
                    ),
                )
                and machine.get("window_coverage")
                in ("bounded_suffix", "complete_file_prefix")
                and (
                    machine.get("window_coverage") != "bounded_suffix"
                    or machine.get("tail_truncated") is True
                    and machine["source_bytes"] > machine["bytes_read"]
                )
            )
            and machine.get("action_replay_performed") is False
        )
        lineage_shape = True
        if lineage:
            windows = obj(lineage.get("source_windows"))
            gaps = obj(lineage.get("source_gaps"))
            allowed_gaps = {
                "observation_trace_unresolved",
                "request_unresolved",
                "request_identity_missing",
                "trace_identity_missing",
                "observation_identity_missing",
            }
            outcome_counts = (
                "machine_observation_count",
                "trace_attempt_count",
                "request_prepared_count",
                "provider_transmission_attempt_count",
                "raw_response_observed_count",
                "auxiliary_response_contract_valid_count",
                "raw_pass_count",
                "valid_pass_count",
                "execution_valid_pass_count",
                "provider_timeout_count",
                "enter_without_request_observed",
                "exact_attempt_join_gap_count",
            )
            ledger = lineage.get("attempt_ledger")
            ledger_shape = isinstance(ledger, list) and len(ledger) <= 4096
            ledger_keys = set()
            ledger_hashes = set()
            if ledger_shape:
                for row in ledger:
                    row = obj(row)
                    digest = row.get("machine_observation_sha256")
                    at = clock(row.get("trace_decision_ts"))
                    key = tuple(
                        row.get(k)
                        for k in ("evaluation_attempt_id", "decision_trace_id")
                    )
                    if (
                        not all(isinstance(v, str) and 0 < len(v) <= 256 for v in key)
                        or key in ledger_keys
                        or [row.get("producer_pid"), row.get("producer_start_ticks")]
                        != actor
                        or row.get("machine_bundle_sha256")
                        != machine.get("current_bundle_sha256")
                        or at is None
                        or now is None
                        or not 0 <= (now - at).total_seconds() <= SOURCE_WINDOW_SEC + 5
                        or digest is not None
                        and (not sha(digest) or digest in ledger_hashes)
                        or digest is None
                        and not _native_preassessment_terminal_valid(
                            row, actor, machine.get("current_bundle_sha256")
                        )
                        and (
                            row.get("machine_action") is not None
                            or lineage.get("status") != "partial_source_gap"
                            or not any(
                                count(gaps.get(k), minimum=1)
                                for k in (
                                    "observation_trace_unresolved",
                                    "trace_identity_missing",
                                    "observation_identity_missing",
                                )
                            )
                        )
                        or row.get("machine_action")
                        not in (None, "SOURCE_INVALID", "RECHECK", "BLOCK", "ENTER_NOW")
                        or row.get("raw_verdict")
                        not in (None, "PASS", "CAUTION", "VETO", "INSUFFICIENT")
                        or row.get("effective_screen_status") is not None
                        and (
                            not isinstance(row["effective_screen_status"], str)
                            or not 0 < len(row["effective_screen_status"]) <= 96
                        )
                        or any(
                            type(row.get(k)) is not bool
                            for k in (
                                "request_prepared",
                                "transmission_attempt_observed",
                                "raw_response_observed",
                                "timeout",
                            )
                        )
                        or any(
                            row.get(k) is not None and type(row[k]) is not bool
                            for k in (
                                "auxiliary_response_contract_valid",
                                "post_response_execution_valid",
                            )
                        )
                        or not isinstance(row.get("execution_errors"), list)
                        or len(row["execution_errors"]) > 64
                        or any(
                            not isinstance(v, str) or not 0 < len(v) <= 256
                            for v in row["execution_errors"]
                        )
                    ):
                        ledger_shape = False
                        break
                    ledger_keys.add(key)
                    if digest is not None:
                        ledger_hashes.add(digest)
            lineage_shape = (
                lineage.get("status")
                in (
                    ("observed", "partial_source_gap", "not_observed")
                    if provider_n == 0
                    else ("observed", "partial_source_gap")
                )
                and lineage.get("issues") == {}
                and lineage.get("decision_authority") == "report_only"
                and lineage.get("exact_pid_filter") == actor
                and lineage.get("current_pid_coverage") == "exact_live_pid"
                and all(count(lineage.get(k)) for k in outcome_counts)
                and isinstance(lineage.get("source_gaps"), dict)
                and set(gaps) <= allowed_gaps
                and all(count(v, minimum=1) for v in gaps.values())
                and sum(gaps.values()) == lineage.get("exact_attempt_join_gap_count")
                and set(windows) == {"requests", "traces"}
                and all(
                    clean_reader(
                        v, 8 * 1024 * 1024, SOURCE_WINDOW_SEC + 5, source_name=name
                    )
                    for name, v in windows.items()
                )
                and ledger_shape
                and len(ledger) == lineage.get("trace_attempt_count")
                and lineage.get("machine_observation_count") == provider_n
                and lineage.get("execution_valid_pass_count", 0)
                <= lineage.get("valid_pass_count", 0)
                <= lineage.get("raw_pass_count", 0)
                <= lineage.get("raw_response_observed_count", 0)
                and lineage.get("auxiliary_response_contract_valid_count", 0)
                <= lineage.get("raw_response_observed_count", 0)
            )
            if provider_n == 0:
                lineage_shape = (
                    lineage_shape
                    and ledger == []
                    and gaps == {}
                    and all(lineage.get(k) == 0 for k in outcome_counts)
                )
        quality_incidents = True
        if not incidents_valid:
            quality_incidents = isinstance(incidents, dict) and len(incidents) <= 256
            if quality_incidents:
                for key, item in incidents.items():
                    item = obj(item)
                    last = clock(item.get("last_seen"))
                    state = item.get("status")
                    if last is None or now is None or last > now:
                        quality_incidents = False
                        break
                    if (
                        key in historical_incident_keys
                        or state in ("recovered", "superseded_alias", "reclassified")
                        or (
                            state == "historical_unresolved"
                            and (now - last).total_seconds() > SOURCE_WINDOW_SEC
                        )
                    ):
                        continue
                    quality = obj(item.get("issues"))
                    if (
                        key != "machine_auxiliary_intraday_source_gap"
                        or state not in ("pending", "active", "historical_unresolved")
                        or not quality
                        or any(
                            k
                            not in {
                                "machine_probe:coverage_degraded:" + route
                                for route in (
                                    "krx_only",
                                    "nxt_only",
                                    "krx_nxt_integrated",
                                )
                            }
                            or not count(v, minimum=1)
                            for k, v in quality.items()
                        )
                    ):
                        quality_incidents = False
                        break
        bounded = bool(
            actor_valid
            and stages_clean
            and source_shape
            and machine_shape
            and lineage_shape
            and quality_incidents
        )
    return {
        "schema": "submission_monitor_observation_health_v1",
        "status": "not_eligible" if failed and not bounded else "warning_pending",
        "severity": "unchanged" if failed and not bounded else "warning",
        "reason": (
            "native_pre_entry_observation_not_due"
            if bounded and pre_entry_absence
            else (
                "bounded_source_quality_observation"
                if bounded
                else (
                    "health_conditions_not_met"
                    if failed
                    else (
                        "recorded_guard_or_cohort_pending"
                        if counts_valid and n or diagnostics or any(observed.values())
                        else "bounded_no_applicable_observations"
                    )
                )
            )
        ),
        "unmet_conditions": failed,
        "current_observation_verified": False,
        "full_coverage_proven": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "assessment_window_seconds": SOURCE_WINDOW_SEC,
        "assessment_actor": actor,
    }


def _incomplete_semantics(semantics):
    statuses = {
        "unobservable",
        "partial_unobservable",
        "partial_source_gap",
        "validation_deferred",
    }
    sources = semantics.get("sources") or {}
    return (
        semantics.get("status") in statuses
        or bool(semantics.get("selection_status") or semantics.get("source_status"))
        or any(
            (value.get("status") if isinstance(value, dict) else value)
            not in {"complete", "valid_empty", "not_applicable"}
            for value in sources.values()
        )
        or any(
            isinstance(semantics.get(key), dict)
            and semantics[key].get("status") in statuses
            for key in (
                "bootstrap",
                "entry_split",
                "pre_submit_delay",
                "reversal_provider_lineage",
            )
        )
    )


def _retain_unobserved_incident(result, semantics, key):
    if not _incomplete_semantics(semantics):
        return False
    old = result["incidents"].get(key, {})
    if semantics.get("issues"):
        # Aggregate incident keys cannot discharge an unobserved old scope.
        semantics["issues"] = {**old.get("issues", {}), **semantics["issues"]}
        return False
    if old.get("status") == "active" and old.get("notified_status") != "active":
        if key not in result["notification_pending"]:
            result["notification_pending"].append(key)
    return True


def attach_entry_execution_tuning_semantics(result, semantics):
    """Persist only contradictory receipt claims; source gaps remain diagnostic."""
    result["entry_execution_tuning_semantics"] = semantics
    key = "entry_execution_tuning_receipt_contract"
    if _retain_unobserved_incident(result, semantics, key):
        return
    old = result["incidents"].get(key, {})
    if semantics.get("issues"):
        now = stamp(result["as_of"])
        first = (
            old.get("first_seen", result["as_of"])
            if old.get("status") in {"pending", "active"}
            else result["as_of"]
        )
        item = dict(
            scope="entry_split|pre_submit_delay",
            rule=key,
            category="structural_evidence",
            first_seen=first,
            last_seen=result["as_of"],
            status=(
                "active" if (now - stamp(first)).total_seconds() >= 240 else "pending"
            ),
            count=sum(semantics["issues"].values()),
            issues=semantics["issues"],
            examples=semantics.get("examples", [])[:3],
            owner="entry_split_order_plan->pre_submit_delay_tuning->runtime_policy_bootstrap",
            closure_test="same-date report/policy generation and bootstrap handoff hashes agree",
            notified_status=(
                old.get("notified_status")
                if old.get("status") in {"pending", "active"}
                else None
            ),
        )
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") == "historical_unresolved":
            item["history"] = (
                list(old.get("history", []))
                + [{k: v for k, v in old.items() if k != "history"}]
            )[-8:]
        result["incidents"][key] = item
    elif old.get("status") == "active":
        result["incidents"][key] = {**old, "status": "historical_unresolved"}
    elif old.get("status") == "pending":
        result["incidents"].pop(key, None)
    item = result["incidents"].get(key, {})
    if item.get("status") == "active" and item.get("notified_status") != item["status"]:
        if key not in result["notification_pending"]:
            result["notification_pending"].append(key)


def attach_machine_semantics(result, semantics):
    """Persistent report-only receipt faults; absence never repairs old evidence."""
    result["machine_semantics"] = semantics
    if "historical_scanner_observations" in semantics:
        result["historical_scanner_observations"] = semantics[
            "historical_scanner_observations"
        ]
        result["historical_scanner_conflicts"] = semantics.get(
            "historical_scanner_conflicts", []
        )
    health = semantics.get("current_health_cohort")
    if isinstance(health, dict) and isinstance(health.get("view"), dict):
        semantics = health["view"]
        if health.get("excluded_observation_count", 0) and not semantics.get("issues"):
            key = "machine_policy_receipt_contract"
            old = result["incidents"].get(key, {})
            if old.get("status") in {"active", "pending", "historical_unresolved"}:
                result["incidents"][key] = {
                    **old,
                    "status": "historical_unresolved",
                    "current_status": "historical_not_current_cohort",
                }
            return
    key = "machine_policy_receipt_contract"
    if _retain_unobserved_incident(result, semantics, key):
        return
    old = result["incidents"].get(key, {})
    if semantics.get("issues"):
        now = stamp(result["as_of"])
        first = (
            old.get("first_seen", result["as_of"])
            if old.get("status") in {"pending", "active"}
            else result["as_of"]
        )
        item = dict(
            scope=semantics.get("current_bundle_sha256", "unbound"),
            rule=key,
            category="structural_evidence",
            first_seen=first,
            last_seen=result["as_of"],
            status=(
                "active" if (now - stamp(first)).total_seconds() >= 240 else "pending"
            ),
            count=sum(semantics["issues"].values()),
            examples=semantics.get("examples", []),
            issues=semantics["issues"],
            owner="machine_observation->frozen_policy->runtime_receipt",
            closure_test="repair exact receipt source; absence does not repair historical observations",
            notified_status=(
                old.get("notified_status")
                if old.get("status") in {"pending", "active"}
                else None
            ),
        )
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") == "historical_unresolved":
            item["history"] = (
                list(old.get("history", []))
                + [{k: v for k, v in old.items() if k != "history"}]
            )[-8:]
        result["incidents"][key] = item
    elif old.get("status") == "active":
        result["incidents"][key] = {**old, "status": "historical_unresolved"}
    elif old.get("status") == "pending":
        result["incidents"].pop(key, None)
    item = result["incidents"].get(key, {})
    if item.get("status") == "active" and item.get("notified_status") != item["status"]:
        if key not in result["notification_pending"]:
            result["notification_pending"].append(key)


def evaluate(report, state, now):
    """Pure state transition. Old/stale evidence never triggers recovery or alerts."""
    now = stamp(now)
    if now is None:
        raise ValueError("monitor_as_of_invalid")
    report = report if isinstance(report, dict) else {}
    state = state if isinstance(state, dict) else {}
    source = report.get("submission_monitor")
    source = source if isinstance(source, dict) else {}
    as_of = stamp(source.get("as_of"))
    latest = stamp(source.get("latest_event_at"))
    today = now.date().isoformat()
    prior = (
        state if state.get("date") == today and state.get("schema") == SCHEMA else {}
    )
    incidents = dict(prior.get("incidents") or {})
    result = {
        "schema": SCHEMA,
        "date": today,
        "as_of": now.isoformat(),
        "async_disposition_coverage": source.get("async_disposition_coverage") or {},
        "runtime_effect": False,
        "status": "unobservable",
        "blocker": None,
        "notification_status": "idle",
        "incidents": incidents,
        "notification_pending": [],
        "scopes": {},
        "source_as_of": prior.get("source_as_of"),
        "identity_observation": {
            "status": "unobservable",
            "reason": "source_not_validated",
        },
        "evaluation_cohort": "scanner_promotions",
        "last_notification_at": prior.get("last_notification_at"),
    }
    # Record this input before any guard returns. source_as_of remains the last
    # accepted snapshot cursor; it must never be mistaken for this input clock.
    prior_clock = stamp(prior.get("source_as_of"))
    result["input_provenance"] = {
        "schema": "submission_monitor_input_provenance_v1",
        "evaluated_at": now.isoformat(),
        "target_date": report.get("target_date"),
        "dry_run": report.get("dry_run"),
        "snapshot_schema": source.get("schema"),
        "snapshot_as_of": as_of.isoformat() if as_of else None,
        "latest_event_at": latest.isoformat() if latest else None,
        "latest_event_status": source.get("latest_event_status"),
        "loaded_recent_event_count": source.get("loaded_recent_event_count"),
        "snapshot_age_seconds": (now - as_of).total_seconds() if as_of else None,
        "sentinel_classification": (report.get("classification") or {}).get("primary"),
        "latest_event_age_seconds": (now - latest).total_seconds() if latest else None,
        "row_count": (
            len(source["rows"]) if isinstance(source.get("rows"), list) else None
        ),
        "identity_missing_events": source.get("identity_missing_events"),
        "auxiliary_ai_semantic_issue_counts": source.get(
            "auxiliary_ai_semantic_issue_counts"
        ),
        "prior_accepted_source_as_of": prior.get("source_as_of"),
        "snapshot_order": (
            "invalid"
            if not as_of or prior.get("source_as_of") and not prior_clock
            else (
                "initial"
                if not prior_clock
                else "advancing" if as_of > prior_clock else "duplicate_or_reversed"
            )
        ),
    }
    result["economic_coverage_contract"] = {
        "metric_role": "funnel_count",
        "decision_authority": "report_only",
        "window_policy": "exact_attempts_current_30_minutes",
        "sample_floor": "none_for_counts_no_quality_acceptance",
        "primary_decision_metric": "economic_gap_action_counts",
        "source_quality_gate": "same_attempt_explicit_nonentry_cache_miss_only",
        "forbidden_uses": [
            "order_authority",
            "missing_as_zero_ev",
            "tuning_population_acceptance",
        ],
    }
    # A quiet machine window cannot prove normal current behavior. It can
    # still correct an old alert when a fresh source snapshot binds every old
    # evidence hash to a valid fixed-watch admission.
    reclassification_source_current = (
        report.get("target_date") == today
        and not report.get("dry_run")
        and source.get("schema") == SCHEMA
        and as_of is not None
        and 0 <= (now - as_of).total_seconds() <= 420
        and (
            not prior.get("source_as_of")
            or (
                stamp(prior["source_as_of"]) is not None
                and as_of > stamp(prior["source_as_of"])
            )
        )
        and (source.get("fixed_watch_identity_observation") or {}).get("schema")
        == "fixed_watch_source_identity_v1"
    )
    old_identity = incidents.get("unbound_machine_identity", {})
    old_evidence = set(old_identity.get("evidence_ids") or [])
    if (
        reclassification_source_current
        and old_identity.get("rule") == "source_identity_missing"
        and old_evidence
        and old_evidence <= set(source.get("fixed_watch_identified_evidence") or [])
    ):
        incidents["unbound_machine_identity_reclassified_fixed_watch"] = {
            **old_identity,
            "status": "reclassified",
            "scope": "fixed_watch",
            "classification": "valid_fixed_watch_non_scanner_identity",
            "correction_basis": "all_prior_evidence_ids_match_valid_fixed_watch_source_events",
            "last_seen": now.isoformat(),
        }
        incidents.pop("unbound_machine_identity", None)
        result["fixed_watch_identity_observation"] = source[
            "fixed_watch_identity_observation"
        ]
    if (
        report.get("target_date") != today
        or report.get("dry_run")
        or source.get("schema") != SCHEMA
        or not as_of
        or not latest
        or not 0 <= (now - as_of).total_seconds() <= 420
        or not 0 <= (now - latest).total_seconds() <= 600
    ):
        result["blocker"] = "missing_stale_or_noncurrent_sentinel_evidence"
        return result
    if prior.get("source_as_of") and as_of <= stamp(prior["source_as_of"]):
        result["blocker"] = "duplicate_or_reversed_source_snapshot"
        return result
    result.update(status="observing", source_as_of=as_of.isoformat())
    result["fixed_watch_identity_observation"] = (
        source.get("fixed_watch_identity_observation") or {}
    )
    result["main_machine_observation"] = source.get("main_machine_observation") or {}
    # Preserve the original incident as superseded evidence, without reporting
    # alias normalization as recovery or double-counting its exact attempts.
    for old_key, old in list(incidents.items()):
        parts = str(old.get("scope", "")).split("|")
        if (
            len(parts) != 3
            or parts[1] != "KRX_LIKE_PREMARKET"
            or old.get("superseded_by")
        ):
            continue
        parts[1] = "PREMARKET_KRX_LIKE"
        scope = "|".join(parts)
        key = hashlib.sha256(f"{scope}|{old['rule']}".encode()).hexdigest()[:24]

        def normalized_identity(value):
            fields = value.split("|")
            if len(fields) == 6 and fields[4] == "KRX_LIKE_PREMARKET":
                fields[4] = "PREMARKET_KRX_LIKE"
            return "|".join(fields)

        current = incidents.get(key, {})
        ids = sorted(
            set(current.get("evidence_ids", []))
            | {normalized_identity(value) for value in old.get("evidence_ids", [])}
        )
        incidents[key] = {
            **old,
            **current,
            "scope": scope,
            "evidence_ids": ids[:128],
            "count": max(len(ids), old.get("count", 0), current.get("count", 0)),
            "first_seen": min(
                old["first_seen"], current.get("first_seen", old["first_seen"])
            ),
            "promotion_ids": sorted(
                set(old.get("promotion_ids", []))
                | set(current.get("promotion_ids", []))
            ),
            "examples": current.get("examples")
            or [
                {
                    **example,
                    "evaluation_key": normalized_identity(example["evaluation_key"]),
                }
                for example in old.get("examples", [])
            ],
        }
        incidents[old_key] = {**old, "status": "superseded_alias", "superseded_by": key}
    groups = defaultdict(list)
    for row in source.get("rows", []):
        start = stamp(row.get("first_evaluated_at"))
        if start and 0 <= (now - start).total_seconds() <= 2700:
            scope = "|".join(
                str(row.get(k) or "missing")
                for k in ("effective_venue", "session_bucket", "policy_bundle_hash")
            )
            groups[scope].append(row)
    if not groups:
        result.update(
            status="unobservable", blocker="no_identified_scanner_machine_evaluation"
        )
    for scope, all_rows in groups.items():
        rows = [
            r
            for r in all_rows
            if (now - stamp(r["first_evaluated_at"])).total_seconds() <= WINDOW_SEC
        ]
        # Count each promotion once for scarcity, but retain exact attempts for gaps.
        parents = {}
        for row in sorted(rows, key=lambda r: r["first_evaluated_at"]):
            parents[(row["scanner_promotion_id"], row["stock_code"])] = row
        valid = [
            r
            for r in parents.values()
            if not r["conflict_reasons"] and r["mechanistic_action"] != "SOURCE_INVALID"
        ]
        entered = [r for r in valid if r["mechanistic_action"] == "ENTER_NOW"]
        veto = [r for r in entered if r["ai_screen_status"] == "veto"]
        accepted = [r for r in rows if r["broker_acceptance_observed"]]
        gaps = [
            r
            for r in all_rows
            if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
            and (
                r["conflict_reasons"]
                or r["mechanistic_action"] == "SOURCE_INVALID"
                or r["final_state"].startswith("lineage_gap")
                or r["final_state"] == "pending_broker_reconciliation"
                or (r["ai_screen_status"] == "pass" and r["final_state"] == "pending")
            )
        ]
        economic_gaps = [
            r
            for r in all_rows
            if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
            and (r.get("economic_source") or {}).get("status") == "source_gap"
            and not _nonentry_downstream_gap(r)
        ]
        observation_gaps = [r for r in rows if _nonentry_capacity_observation_gap(r)]
        tests = {
            "economic_producer_gap": (economic_gaps, "structural_evidence", 240),
            "source_or_submit_lineage_gap": (gaps, "structural_evidence", 240),
            "enter_now_scarcity": (
                (
                    valid
                    if len(valid) >= MIN_PROMOTIONS
                    and not entered
                    and not any(r.get("enter_now_observed") for r in rows)
                    else []
                ),
                "review_required",
                PERSIST_SEC,
            ),
            "ai_veto_concentration": (
                (
                    veto
                    if len(entered) >= MIN_PROMOTIONS
                    and len(veto) / len(entered) >= 0.9
                    and not accepted
                    else []
                ),
                "review_required",
                PERSIST_SEC,
            ),
        }
        result["scopes"][scope] = {
            "unique_promotions": len(parents),
            "valid_promotions": len(valid),
            "enter_now_observed_attempts": sum(
                bool(r.get("enter_now_observed")) for r in rows
            ),
            "enter_now_observed_conflicting_attempts": sum(
                bool(r.get("enter_now_observed")) and bool(r["conflict_reasons"])
                for r in rows
            ),
            "enter_now": len(entered),
            "veto": len(veto),
            "accepted_attempts": len(accepted),
            "machine_action_counts": dict(
                Counter(r["mechanistic_action"] for r in valid)
            ),
            "unresolved_attempts": len(gaps),
            "economic_producer_gaps": len(economic_gaps),
            "nonentry_capacity_observation_gaps": len(observation_gaps),
            "nonentry_downstream_observation_gaps": sum(
                _nonentry_downstream_gap(r) for r in rows
            ),
            "economic_producer_gap_owner": "downstream_execution_replay_not_machine_tuning",
            "nonentry_capacity_observation_examples": [
                {
                    k: r.get(k)
                    for k in (
                        "stock_code",
                        "evaluation_key",
                        "first_evaluated_at",
                        "mechanistic_action",
                        "economic_source",
                    )
                }
                for r in observation_gaps[:3]
            ],
            "economic_gap_action_counts": {
                action: sum(
                    r["mechanistic_action"] == action
                    and (r.get("economic_source") or {}).get("status") == "source_gap"
                    for r in rows
                )
                for action in ("ENTER_NOW", "BLOCK", "RECHECK", "SOURCE_INVALID")
            },
            "economic_status_counts": {
                status: sum(
                    (r.get("economic_source") or {}).get("status") == status
                    for r in rows
                )
                for status in (
                    "recorded_source_only",
                    "source_gap",
                    "guard_excluded",
                    "unsupported_scope",
                )
            },
            "guard_blocked": sum(r["final_guard_blocked"] for r in rows),
        }
        for rule, (bad, category, persistence) in tests.items():
            key = hashlib.sha256(f"{scope}|{rule}".encode()).hexdigest()[:24]
            old = incidents.get(key, {})
            ids = sorted({r["evaluation_key"] for r in bad})
            if bad:
                first = (
                    old.get("first_seen", now.isoformat())
                    if old.get("status") in {"pending", "active"}
                    else now.isoformat()
                )
                # Ratios need new independent promotions, not repeated snapshots.
                identities = sorted(
                    {f'{r["scanner_promotion_id"]}|{r["stock_code"]}' for r in bad}
                )
                new_support = bool(set(identities) - set(old.get("promotion_ids", [])))
                confirmed = (
                    bool(old) and (now - stamp(first)).total_seconds() >= persistence
                )
                confirmed = confirmed and (
                    category == "structural_evidence"
                    or new_support
                    or old.get("status") == "active"
                )
                item = {
                    "scope": scope,
                    "rule": rule,
                    "category": category,
                    "first_seen": first,
                    "last_seen": now.isoformat(),
                    "status": "active" if confirmed else "pending",
                    "evidence_ids": ids[:128],
                    "promotion_ids": identities[:128],
                    "count": len(ids),
                    "notified_status": old.get("notified_status"),
                    "examples": [
                        {
                            k: r.get(k)
                            for k in (
                                "stock_code",
                                "evaluation_key",
                                "mechanistic_action",
                                "final_state",
                                "conflict_reasons",
                                "auxiliary_ai_semantics",
                                "source_invalid_decomposition",
                                "economic_source",
                                "final_guard_evidence",
                            )
                        }
                        for r in bad[:3]
                    ],
                    "owner": (
                        (bad[0].get("economic_source") or {}).get("owner")
                        if rule == "economic_producer_gap"
                        else "buy_funnel_sentinel.machine_primary_entry_funnel"
                    ),
                    "closure_test": (
                        "same attempt publishes valid frozen economic proof"
                        if rule == "economic_producer_gap"
                        else (
                            "new conflict-free ENTER_NOW promotion in the same scope; order submission is tracked separately"
                            if rule == "enter_now_scarcity"
                            else "same attempt receives a consistent terminal; ratios recover on new valid promotions"
                        )
                    ),
                }
                if old.get("history"):
                    item["history"] = old["history"]
                if old.get("status") == "observation_only_unresolved":
                    item["history"] = (
                        list(old.get("history") or [])
                        + [{k: v for k, v in old.items() if k != "history"}]
                    )[-8:]
                    item["notified_status"] = None
                incidents[key] = item
            elif (
                rule == "economic_producer_gap"
                and old
                and old.get("status") in {"active", "pending"}
                and old.get("count") == len(set(old.get("evidence_ids", [])))
                and old.get("evidence_ids")
                and set(old["evidence_ids"])
                <= {
                    r["evaluation_key"] for r in all_rows if _nonentry_downstream_gap(r)
                }
            ):
                # Reclassification is not source recovery. Preserve old proof
                # IDs/count/examples; unknown/expired/mixed incidents stay open.
                incidents[key] = {
                    **old,
                    "status": "observation_only_unresolved",
                    "classification_reason": "exact_nonentry_downstream_evidence_not_machine_tuning",
                    "classified_at": now.isoformat(),
                }
            elif old and old.get("status") == "active":
                # Window expiration is not recovery. Require explicit closure evidence.
                old_ids = set(old.get("evidence_ids", []))
                resolved = {
                    r["evaluation_key"]
                    for r in all_rows
                    if r["evaluation_key"] in old_ids
                    and (
                        (r.get("economic_source") or {}).get("status")
                        == "recorded_source_only"
                        if rule == "economic_producer_gap"
                        else not r["conflict_reasons"]
                        and r["final_state"]
                        in {
                            "submit_pipeline_reached",
                            "final_guard_blocked",
                            "broker_rejected",
                        }
                    )
                }
                healthy = (
                    bool(
                        old_ids
                        and old.get("count") == len(old_ids)
                        and old_ids <= resolved
                    )
                    if category == "structural_evidence"
                    else bool(
                        accepted
                        and any(r["evaluation_key"] not in old_ids for r in accepted)
                    )
                )
                if rule == "enter_now_scarcity":
                    healthy = any(
                        r["mechanistic_action"] == "ENTER_NOW"
                        and not r["conflict_reasons"]
                        for r in rows
                    )
                if healthy:
                    incidents[key] = {
                        **old,
                        "status": "recovered",
                        "last_seen": now.isoformat(),
                    }
            elif old and old.get("status") == "pending":
                incidents.pop(key, None)
    missing = source.get("missing_identity_evidence") or []
    key = "unbound_machine_identity"
    old = incidents.get(key, {})
    observation = source.get("identity_observation") or {}
    current_status = (
        observation.get("status")
        if observation.get("schema") == "machine_identity_recency_v1"
        else "unobservable"
    )
    if current_status not in {"current_gap", "no_recurrence_observed", "unobservable"}:
        current_status = "unobservable"
    result["identity_observation"] = observation or {
        "status": "unobservable",
        "reason": "legacy_source_no_recency",
    }
    if missing:
        recurrence = (
            old.get("status") == "historical_unresolved"
            and current_status == "current_gap"
            and bool(set(missing) - set(old.get("evidence_ids", [])))
        )
        history = list(old.get("history") or [])
        if recurrence:
            history.append({k: v for k, v in old.items() if k != "history"})
        first = (
            old.get("first_seen", now.isoformat())
            if not recurrence
            else now.isoformat()
        )
        status = (
            "active"  # Exact current identity loss needs no ratio/persistence floor.
        )
        if current_status != "current_gap":
            status = "historical_unresolved"
        # A shrinking window must not erase the already recorded old incident.
        preserve = (
            bool(old)
            and not recurrence
            and (
                status == "historical_unresolved"
                or old.get("status") == "historical_unresolved"
            )
        )
        if preserve:
            status = "historical_unresolved"
        incidents[key] = {
            **old,
            "scope": "unbound",
            "rule": "source_identity_missing",
            "category": "structural_evidence",
            "first_seen": first,
            "last_seen": now.isoformat(),
            "status": status,
            "current_status": current_status,
            "history": history,
            "count": old.get("count", len(missing)) if preserve else len(missing),
            "evidence_ids": (
                old.get("evidence_ids", missing[:128]) if preserve else missing[:128]
            ),
            "examples": (
                (old.get("examples") or [])
                if preserve
                else source.get("missing_identity_examples") or []
            ),
            "occurred_first_at": (
                old.get("occurred_first_at")
                if preserve
                else source.get("missing_identity_first_at")
            ),
            "occurred_last_at": (
                old.get("occurred_last_at")
                if preserve
                else source.get("missing_identity_last_at")
            ),
            "notified_status": None if recurrence else old.get("notified_status"),
            "normal_observation_pending": (
                False if recurrence else old.get("normal_observation_pending", False)
            ),
            "normal_observation_notified_at": (
                None if recurrence else old.get("normal_observation_notified_at")
            ),
            "owner": "ENTRY_PIPELINE machine producer identity",
            "closure_test": "new identified machine evaluations with no missing identity; old unbound rows remain unrepairable",
        }
    elif old:
        incidents[key] = {
            **old,
            "status": "historical_unresolved",
            "current_status": current_status,
        }
    item = incidents.get(key, {})
    if (
        item.get("status") == "historical_unresolved"
        and old.get("status") == "active"
        and old.get("notified_status") == "active"
    ):
        item["normal_observation_pending"] = True
    if item and not item.get("examples"):
        matched = {
            r["evidence_id"]: r
            for r in (
                source.get("historical_identity_samples", [])
                + source.get("missing_identity_examples", [])
            )
            if r.get("evidence_id") in set(item.get("evidence_ids", []))
        }
        if matched:
            details = sorted(matched.values(), key=lambda r: r["occurred_at"])
            item["examples"] = details[:3]
            item["detail_basis"] = "existing_cache_exact_evidence_hash_match"
            if (
                len(matched)
                == len(set(item.get("evidence_ids", [])))
                == item.get("count")
            ):
                item["occurred_first_at"] = details[0]["occurred_at"]
                item["occurred_last_at"] = details[-1]["occurred_at"]
    if missing or old:
        result["scopes"]["unbound"] = {
            "missing_identity_events": len(missing),
            "current_missing_events": observation.get("missing_event_count"),
            "current_status": current_status,
        }
    if observation.get("missing_event_count"):
        result["blocker"] = "machine_identity_missing_events"
        result["identity_missing_events"] = observation["missing_event_count"]
    # Absent scopes/stale sources retain incidents without asserting they resolved.
    result["notification_pending"] = [
        k
        for k, v in incidents.items()
        if _notification_kind(v, result) and v["scope"] in result["scopes"]
    ]
    return result


def _notification_kind(item, result):
    status = item.get("status")
    if status in {"active", "recovered"} and item.get("notified_status") != status:
        return status
    observation = result.get("identity_observation") or {}
    if (
        status == "historical_unresolved"
        and item.get("rule") == "source_identity_missing"
        and item.get("normal_observation_pending")
        and observation.get("status") == "no_recurrence_observed"
        and observation.get("missing_event_count") == 0
        and observation.get("identified_event_count", 0) > 0
    ):
        return "normal_observation"
    return None


def notify(result, path, send=None):
    keys = [
        key
        for key in result["notification_pending"]
        if _notification_kind(result["incidents"][key], result)
    ]
    keys.sort(
        key=lambda key: (
            _notification_kind(result["incidents"][key], result) != "active",
            key != "machine_auxiliary_intraday_source_gap",
        )
    )
    last = stamp(result.get("last_notification_at"))
    if last and (stamp(result["as_of"]) - last).total_seconds() < 300:
        result["notification_status"] = "cooldown"
        return
    if not keys:
        return
    messages = []
    for key in keys[:4]:
        item = result["incidents"][key]
        if _notification_kind(item, result) == "normal_observation":
            obs = result["identity_observation"]
            messages.append(
                "현재 정상 관측: 식별자 결손 최근10분 0건 / "
                f'정상 식별 {obs["identified_event_count"]} 이벤트\n'
                "추가 점검 요청 없음. 과거 결손은 보고서에 보존하며 원천 복구를 뜻하지 않습니다."
            )
            continue
        if item["rule"] == "source_identity_missing":
            obs = result.get("identity_observation") or {}
            examples = obs.get("examples") or item.get("examples") or []
            sample = examples[0] if examples else {}
            identity_details = []
            if sample.get("missing_fields"):
                identity_details.append(
                    "누락 필드: " + ", ".join(sample["missing_fields"])
                )
            if sample.get("conflicting_fields"):
                identity_details.append(
                    "충돌 필드: " + ", ".join(sample["conflicting_fields"])
                )
            if sample.get("identity_contract_issues"):
                identity_details.append(
                    "식별 계약: " + ", ".join(sample["identity_contract_issues"])
                )
            if not identity_details:
                identity_details.append("식별 결손 세부정보: 미확인(구형 이력)")
            messages.append(
                f'{item["status"]}: source_identity_missing\n'
                f'현재 최근10분: {item.get("current_status", "unobservable")} '
                f'/ 결손 {obs.get("missing_event_count", "미확인")}건\n'
                f'과거 원천 복구 주장 없음 / 보존 근거 {item["count"]} 이벤트 (주문 수 아님)\n'
                f'현재 결손 발생: {obs.get("current_missing_first_at") or item.get("occurred_first_at") or "미확인(구형 이력)"} ~ '
                f'{obs.get("current_missing_last_at") or item.get("occurred_last_at") or "미확인(구형 이력)"}\n'
                f'종목: {sample.get("stock_code") or "미확인(구형 이력)"} / '
                f'{" / ".join(identity_details)}\n'
                f'대표 발생시각: {sample.get("occurred_at") or "미확인(구형 이력)"}'
            )
            continue
        if item["rule"] == "enter_now_scarcity":
            stats = result.get("scopes", {}).get(item["scope"], {})
            actions = stats.get("machine_action_counts", {})
            messages.append(
                f'{item["status"]}: 기계판정 ENTER_NOW 희소 / {item["scope"]}\n'
                f'유효 승격 {stats.get("valid_promotions", "미확인")}건 / '
                f'BLOCK {actions.get("BLOCK", 0)} / RECHECK {actions.get("RECHECK", 0)} / '
                f'ENTER_NOW {actions.get("ENTER_NOW", 0)}\n'
                "판정 경로 검토 신호이며 주문 제출 실패·미체결 증거가 아닙니다."
            )
            continue
        if item["rule"] == "machine_auxiliary_intraday_source_gap":
            if item["status"] == "recovered":
                messages.append(
                    "현재 정상 관측: 해당 결손 단계에 새 정상 영수증이 들어왔습니다. "
                    "과거 결손 원천이 복구됐다는 뜻은 아닙니다."
                )
                continue
            sample = (item.get("examples") or [{}])[0]
            messages.append(
                f'{item["status"]}: 기계·보조 AI 장중 원천결손 / '
                f'{item["count"]}건 (주문 수 아님)\n'
                f'원인: {json.dumps(item.get("issues", {}), ensure_ascii=False)[:500]}\n'
                f'대표: {sample.get("stock_code") or "미확인"} '
                f'{sample.get("route") or "경로 미확인"} '
                f'{sample.get("reason") or "원인 미확인"}\n'
                "정확한 판정 ID의 원천을 확인하고 기존 제한된 원천 보강 경로로 처리하세요."
            )
            continue
        if item["rule"] == "pre_submit_delay_intraday_source_gap":
            if item["status"] == "recovered":
                messages.append(
                    "pre_submit_delay의 새 원천 구간이 정상입니다. 과거 결손은 복원되지 않았습니다."
                )
            else:
                semantics = result.get("pre_submit_delay_source_semantics") or {}
                collection_counts = semantics.get("collection_health_counts", {})
                quote_counts = semantics.get("quote_eligibility_counts", {})
                warning_only = set(item.get("issues") or {}) <= {
                    "quote_collection_unobservable"
                }
                label = "호가 관측 원인 미확정" if warning_only else "장중 원천 점검"
                messages.append(
                    f'{item["status"]}: pre_submit_delay {label} / {item["count"]}건\n'
                    f'원인: {json.dumps(item.get("issues", {}), ensure_ascii=False)[:450]}\n'
                    f'대표: {json.dumps((item.get("examples") or [{}])[0], ensure_ascii=False)[:350]}\n'
                    f'연구 호가 무효: {quote_counts.get("invalid", 0)} / '
                    f'수집 결함 확정: {semantics.get("collection_fault_event_count", collection_counts.get("collection_fault_confirmed", 0))} / '
                    f'갱신 대기: {collection_counts.get("expected_wait", 0)} / '
                    f'미확정: {collection_counts.get("unobservable", 0) + collection_counts.get("cadence_exceeded_unproven", 0)}\n'
                    f'원천 상태: {semantics.get("sources")} / 요약 PID: {semantics.get("summary_last_writer_pid")}\n'
                    "정확한 원천 ID와 호가 경로를 대조하세요. 자동 매매 변경은 없습니다."
                )
            continue
        example = (item.get("examples") or [{}])[0]
        cause = (
            (example.get("economic_source") or {}).get("blocker")
            if item["rule"] == "economic_producer_gap"
            else (example.get("source_invalid_decomposition") or {}).get(
                "primary_blocker"
            )
            or next(iter(example.get("conflict_reasons") or []), None)
            or example.get("final_state")
            or example.get("reason")
            or next(iter(item.get("issues") or {}), None)
        )
        cause_text = f"첫 결손: {str(cause)[:180]}\n" if cause else ""
        if item["rule"] == "economic_producer_gap":
            detail = (example.get("economic_source") or {}).get("capacity_blocker")
            cause_text += (
                f"판정: {example.get('mechanistic_action') or '미확인'} / "
                f"조회 원인: {detail or '자금 조회 외 계약 결손 또는 구형 근거'}\n"
                "후단 실행 재생 증거 결손입니다. 기계 튜닝 실패나 실제 주문 실패 건수가 아닙니다.\n"
            )
        elif item["rule"] == "entry_execution_tuning_receipt_contract":
            axis = ", ".join(
                sorted(
                    {
                        str(row.get("axis"))
                        for row in item.get("examples", [])
                        if row.get("axis")
                    }
                )
            )
            cause_text += f"대상 축: {axis or 'entry_split / pre_submit_delay'}\n"
            cause_text += "보고서의 후보 부족·source gap 자체는 오류나 EV 0으로 판정하지 않습니다.\n"
        messages.append(
            cause_text
            + f'{item["status"]}: {item["rule"]}\n{item["scope"]}\n근거 {item["count"]}건 / {item["category"]}\n'
            + json.dumps(item.get("examples", [])[:1], ensure_ascii=False)[:350]
        )
    active_keys = [
        key
        for key in keys[:4]
        if _notification_kind(result["incidents"][key], result) == "active"
    ]
    actionable = bool(active_keys)
    has_structural = any(
        result["incidents"][key].get("category") == "structural_evidence"
        for key in active_keys
    )
    active_rules = {result["incidents"][key].get("rule") for key in active_keys}
    if not actionable and {
        result["incidents"][key].get("rule") for key in keys[:4]
    } == {"pre_submit_delay_intraday_source_gap"}:
        title = "매수 지연 원천 정상 관측"
    elif not actionable:
        title = "제출병목 정상 확인"
    elif not has_structural and active_rules == {"enter_now_scarcity"}:
        title = "기계판정 검토"
    elif not has_structural and active_rules <= {
        "enter_now_scarcity",
        "ai_veto_concentration",
    }:
        title = "진입판정 검토"
    elif active_rules == {"machine_auxiliary_intraday_source_gap"}:
        title = "판정 원천결손 점검"
    elif active_rules == {"pre_submit_delay_intraday_source_gap"}:
        title = (
            "매수 지연 호가 관측 점검"
            if all(
                set(result["incidents"][key].get("issues") or {})
                <= {"quote_collection_unobservable"}
                for key in keys
            )
            else "매수 지연 원천결손 점검"
        )
    else:
        title = "제출병목 점검"
    message = (
        f"[{title}] 자동 매매 변경 없음\n" + "\n".join(messages) + f"\n근거: {path}"
    )
    if actionable:
        message += (
            "\n정확 경로의 수신·판정 원천을 대조하세요. 체결 희소를 API 결함으로 단정하지 않습니다."
            if active_rules == {"machine_auxiliary_intraday_source_gap"}
            else (
                "\nCodex에서 원천과 제출 경로를 점검하세요."
                if has_structural
                else "\n판정·기회비용 검토 신호이며 자동 매매 변경은 없습니다."
            )
        )
    if send is None:
        try:
            token, admin = _load_telegram_config()
        except (OSError, ValueError):
            result["notification_status"] = "configuration_invalid"
            return
        if not token or not admin:
            result["notification_status"] = "configuration_missing"
            return
        send = lambda text: _send_telegram(token, admin, text)
    try:
        send(message[:4000])
    except Exception as exc:
        # Never leak a token-bearing HTTP exception into logs.
        result["notification_status"] = f"retry_required:{type(exc).__name__}"
        return
    for key in keys[:4]:
        if _notification_kind(result["incidents"][key], result) == "normal_observation":
            result["incidents"][key]["normal_observation_pending"] = False
            result["incidents"][key]["normal_observation_notified_at"] = result["as_of"]
        result["incidents"][key]["notified_status"] = result["incidents"][key]["status"]
    result["notification_status"] = "sent"
    result["last_notification_at"] = result["as_of"]


def _observer_seal(value):
    return hashlib.sha256(
        json.dumps(
            {key: item for key, item in value.items() if key != "sha256"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _observer_code_identity():
    root = Path(__file__).resolve().parents[3]
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True, timeout=3
    ).strip()
    if not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("observer_code_commit_invalid")
    return dict(
        release_root=str(root),
        git_commit=commit,
        observer_code_sha256=hashlib.sha256(
            observer_io.regular_bytes(Path(__file__), limit=1024 * 1024)
        ).hexdigest(),
    )


def _observer_generation_snapshot(project, *, run_id, target_date, started_at):
    """Small publication provenance only; never substitutes for policy/PID proof."""
    result = dict(
        schema="submission_monitor_observer_generation_v1",
        run_id=run_id,
        target_date=target_date,
        started_at=started_at.isoformat(),
        completed_at=None,
        status="unavailable",
        generation_current=False,
        reason=None,
        policy_pid_consumption_proven=False,
    )
    try:
        path = Path(project) / "data/runtime/runtime_release_selection.json"
        encoded = observer_io.regular_bytes(path, limit=1024 * 1024)
        selection = observer_io.json_object(encoded)
        code = _observer_code_identity()
        if (
            selection.get("schema") != "runtime_release_selection_v1"
            or not isinstance(selection.get("release_root"), str)
            or not Path(selection["release_root"]).is_absolute()
            or not re.fullmatch("[0-9a-f]{40}", str(selection.get("git_commit") or ""))
            or stamp(selection.get("selected_at_kst")) is None
        ):
            raise ValueError("observer_selection_identity_invalid")
        current = (
            selection["release_root"] == code["release_root"]
            and selection["git_commit"] == code["git_commit"]
        )
        result.update(
            code,
            selection_sha256=hashlib.sha256(encoded).hexdigest(),
            selected_release_root=selection["release_root"],
            selected_git_commit=selection["git_commit"],
            selected_at_kst=selection["selected_at_kst"],
            selector_reported_actual_pid_consumed=selection.get("actual_pid_consumed"),
            selector_reported_pid_receipt=selection.get("actual_pid_receipt"),
            generation_current=current,
            status="current" if current else "not_current",
            reason=None if current else "observer_release_not_selected",
        )
        if selection.get(
            "approval_scope"
        ) == "ordered_intraday_deploy_and_restart" or selection.get(
            "deployment_transition"
        ):
            # An observer started after selection but before PID attestation
            # must not replace the frozen predecessor. Its selector hash will
            # necessarily expire when startup records the consumed child.
            from src.engine.infrastructure.runtime_release_router import (
                _startup_ordered_transition,
            )

            workspace = (Path(project) / "data").resolve(strict=True).parent
            transition = _startup_ordered_transition(
                workspace,
                selection,
                Path(selection["release_root"]),
                selection["git_commit"],
                target_date,
            )
            if transition is not None:
                result["publication_transition"] = dict(
                    path=str(transition["path"]),
                    sha256=hashlib.sha256(transition["raw"]).hexdigest(),
                    phase=transition["value"]["phase"],
                )
                if transition["active"]:
                    result.update(
                        status="startup_pending",
                        generation_current=False,
                        reason="observer_waiting_ordered_startup_completion",
                    )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        subprocess.SubprocessError,
    ) as exc:
        result.update(status="unavailable", generation_current=False)
        result["reason"] = type(exc).__name__ + ":" + str(exc)[:160]
    result["sha256"] = _observer_seal(result)
    return result


@contextmanager
def _observer_publication_lease(project):
    """Use the selector writer's existing lock only for final small publication."""
    from src.engine.infrastructure.validation_digest_session import ValidationDeferred

    path = Path(project) / "data/runtime/runtime_release_selection.lock"
    opened = False
    try:
        with observer_io.regular_fd(path) as fd:
            opened = True
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValidationDeferred("observer_selection_lease_busy") from exc
            yield
    except (OSError, ValueError) as exc:
        if not opened:
            raise ValidationDeferred("observer_selection_lease_unavailable") from exc
        raise  # Preserve real notification/publication IO failures.


def _finish_observer_generation(original, project, *, completed_at):
    final = _observer_generation_snapshot(
        project,
        run_id=original["run_id"],
        target_date=original["target_date"],
        started_at=stamp(original["started_at"]),
    )
    stable = (
        original.get("generation_current") is True
        and final.get("generation_current") is True
        and all(
            original.get(key) == final.get(key)
            for key in (
                "selection_sha256",
                "release_root",
                "git_commit",
                "observer_code_sha256",
                "publication_transition",
            )
        )
    )
    result = dict(
        original,
        completed_at=completed_at.isoformat(),
        generation_current=stable,
        status="current" if stable else "changed_or_unavailable",
        reason=None if stable else "observer_generation_changed_during_run",
        final_selection_sha256=final.get("selection_sha256"),
    )
    result["sha256"] = _observer_seal(result)
    return result


def _load_state(path):
    """Own the observer's bounded state contract, independently of Telegram."""
    try:
        Path(path).lstat()
    except FileNotFoundError:
        return {}
    # Removal/replacement after the initial presence check must fail, never
    # turn lost incident custody into a first run. Symlinks/FIFOs fail closed.
    value = observer_io.json_object(
        observer_io.regular_bytes(path, limit=8 * 1024 * 1024)
    )
    if (
        value.get("schema") != SCHEMA
        or not isinstance(value.get("incidents"), dict)
        or value.get("persistence_schema")
        not in (None, "submission_monitor_continuation_v1")
    ):
        raise ValueError("observer_state_contract_invalid")
    return value


def _continuation_state(result):
    """Keep exact incident/cursor custody; bulky observations live in reports."""
    return dict(
        {
            key: result[key]
            for key in (
                "schema",
                "date",
                "as_of",
                "run_id",
                "incidents",
                "source_as_of",
                "last_notification_at",
                "pre_submit_delay_source_cursor",
                "historical_scanner_observations",
                "historical_scanner_conflicts",
            )
            if key in result
        },
        persistence_schema="submission_monitor_continuation_v1",
    )


def main(argv=None):
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--notify", action="store_true")
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Use current-day bounded probe/trace/pending receipts when Sentinel fails.",
    )
    parser.add_argument(
        "--delay-source-only",
        action="store_true",
        help="Independently inspect current-day pre-submit source and producer summary.",
    )
    parser.add_argument(
        "--date", help="Exact KST date for independent source monitoring."
    )
    parser.add_argument("--reuse-validation-digests", action="store_true")
    parser.add_argument("--budget-seconds", type=float, default=120)
    args = parser.parse_args(argv)
    if not math.isfinite(args.budget_seconds) or not 20 <= args.budget_seconds <= 120:
        parser.error("observer_budget_requires_20_to_120_seconds")
    current = datetime.now(KST)
    if args.date and args.date != current.date().isoformat():
        parser.error("source_monitor_requires_current_kst_date")
    state_path = (
        PROJECT_ROOT
        / "tmp"
        / (
            "pre_submit_delay_source_monitor_state.json"
            if args.delay_source_only
            else "submission_bottleneck_monitor_state.json"
        )
    )
    output = (
        PROJECT_ROOT
        / "data/report/buy_funnel_sentinel"
        / (
            "pre_submit_delay_source_monitor_latest.json"
            if args.delay_source_only
            else "submission_bottleneck_monitor_latest.json"
        )
    )
    try:
        report = observer_io.json_object(
            observer_io.regular_bytes(args.report, limit=8 * 1024 * 1024)
        )
    except (OSError, ValueError):
        report = {}
    from src.engine.infrastructure.validation_digest_session import (
        DigestSession,
        ValidationDeferred,
        bounded_lock,
        code_generation,
    )
    from src.engine.monitoring.observation_budget import (
        computation_budget,
        ObservationDeadline,
    )

    state_path.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    observer_generation = (
        None
        if args.delay_source_only
        else _observer_generation_snapshot(
            PROJECT_ROOT,
            run_id=run_id,
            target_date=current.date().isoformat(),
            started_at=current,
        )
    )
    if observer_generation is not None:
        observer_generation["actor_birth_proof"] = _attest_health_actor_birth(
            observer_generation, current
        )
    terminal = dict(
        schema="submission_monitor_execution_v1",
        run_id=run_id,
        target_date=current.date().isoformat(),
        execution_status="failed",
        semantic_status="unobservable",
        notification_status="not_attempted",
        publication={},
        status="unobservable",
        blocker=None,
    )
    deadline = started + args.budget_seconds
    # Notification can consume twelve seconds; startup never requests it.
    # Keep publication time without reserving work that this invocation omits.
    # The caller's total deadline and owned-child cleanup remain unchanged.
    computation_reserve = 15 if args.notify else 5
    terminal["execution_budget"] = dict(
        total_seconds=args.budget_seconds,
        computation_reserve_seconds=computation_reserve,
        notification_requested=args.notify,
    )
    result = None
    session = None
    try:
        if (
            observer_generation is not None
            and observer_generation.get("status") == "startup_pending"
        ):
            terminal.update(
                semantic_status="partial", observer_generation=observer_generation
            )
            raise ValidationDeferred("observer_waiting_ordered_startup_completion")
        with bounded_lock(state_path.with_suffix(".lock"), private=False):
            prior = _load_state(state_path)
            result = evaluate(
                {} if args.source_only or args.delay_source_only else report,
                prior,
                current,
            )
            if "historical_scanner_observations" in prior:
                result["historical_scanner_observations"] = prior[
                    "historical_scanner_observations"
                ]
                result["historical_scanner_conflicts"] = prior.get(
                    "historical_scanner_conflicts", []
                )
            result["run_id"] = run_id
            result["execution_mode"] = (
                "delay_source_only"
                if args.delay_source_only
                else "source_only" if args.source_only else "full"
            )
            result["execution_budget"] = dict(terminal["execution_budget"])
            deferred = False
            stages = (
                [
                    (
                        "pre_submit_delay_source_semantics",
                        attach_pre_submit_delay_source_semantics,
                        lambda: pre_submit_delay_source_semantics(
                            PROJECT_ROOT / "data",
                            result["as_of"],
                            prior.get("pre_submit_delay_source_cursor"),
                        ),
                    )
                ]
                if args.delay_source_only
                else [
                    (
                        "source_gap_semantics",
                        attach_source_gap_semantics,
                        lambda: source_gap_semantics(
                            PROJECT_ROOT / "data", result["as_of"]
                        ),
                    )
                ]
            )
            if not args.source_only and not args.delay_source_only:
                stages += [
                    (
                        "entry_execution_tuning_semantics",
                        attach_entry_execution_tuning_semantics,
                        lambda: entry_execution_tuning_semantics(
                            PROJECT_ROOT / "data", result["as_of"]
                        ),
                    ),
                    (
                        "machine_semantics",
                        attach_machine_semantics,
                        lambda: machine_semantics(
                            PROJECT_ROOT / "data",
                            result["as_of"],
                            historical_scanner_observations=prior.get(
                                "historical_scanner_observations"
                            ),
                            historical_scanner_conflicts=prior.get(
                                "historical_scanner_conflicts", []
                            ),
                            incident_evidence_ids=tuple(
                                {
                                    identity
                                    for item in result["incidents"].values()
                                    if item.get("rule")
                                    in {
                                        "economic_producer_gap",
                                        "source_or_submit_lineage_gap",
                                    }
                                    for identity in item.get("evidence_ids", [])
                                    if isinstance(identity, str)
                                }
                            ),
                        ),
                    ),
                ]
            if args.reuse_validation_digests:
                session = DigestSession(
                    PROJECT_ROOT / "data",
                    current.date().isoformat(),
                    role="observer",
                    generation=code_generation(),
                )
            for name, attach, read in stages:
                try:
                    with computation_budget(deadline - computation_reserve):
                        with (
                            session.activate()
                            if session
                            and name
                            in {"entry_execution_tuning_semantics", "machine_semantics"}
                            else nullcontext()
                        ):
                            with _health_actor_scope(observer_generation):
                                semantics = read()
                    attach(result, semantics)
                except (ObservationDeadline, ValidationDeferred) as exc:
                    deferred = True
                    semantics = dict(
                        status="validation_deferred", reason=str(exc), issues={}
                    )
                    # Source/cursor observers own their own richer recovery
                    # rules. Do not feed them a synthetic empty observation.
                    if name in {
                        "machine_semantics",
                        "entry_execution_tuning_semantics",
                    }:
                        attach(result, semantics)
                    else:
                        result[name] = semantics
                        if (
                            name == "pre_submit_delay_source_semantics"
                            and "pre_submit_delay_source_cursor" in prior
                        ):
                            result["pre_submit_delay_source_cursor"] = prior[
                                "pre_submit_delay_source_cursor"
                            ]
            result["execution_status"] = "deferred" if deferred else "completed"
            result["semantic_status"] = (
                "partial"
                if deferred
                or (
                    result.get("status") == "unobservable"
                    and not args.source_only
                    and not args.delay_source_only
                )
                or any(_incomplete_semantics(result[name]) for name, _, _ in stages)
                else "validated"
            )
            with (
                _observer_publication_lease(PROJECT_ROOT)
                if observer_generation is not None
                else nullcontext()
            ):
                if observer_generation is not None:
                    result["observer_generation"] = _finish_observer_generation(
                        observer_generation,
                        PROJECT_ROOT,
                        completed_at=datetime.now(KST),
                    )
                if (
                    observer_generation is not None
                    and result["observer_generation"]["generation_current"] is not True
                ):
                    terminal.update(
                        execution_status="deferred",
                        semantic_status="partial",
                        observer_generation=result["observer_generation"],
                        source_gap_status=(
                            result.get("source_gap_semantics") or {}
                        ).get("status"),
                    )
                    raise ValidationDeferred(
                        result["observer_generation"].get("reason")
                        or "observer_generation_unavailable"
                    )
                if args.notify and (
                    observer_generation is None
                    or result["observer_generation"]["generation_current"] is True
                ):
                    if time.monotonic() + 12 < deadline:
                        notify(result, output)
                    else:
                        result["notification_status"] = "retry_required:resource_budget"
                if session:
                    result["validation_io"] = dict(session.stats)
                result["execution_wall_seconds"] = time.monotonic() - started
                name = (
                    "pre_submit_delay_source_monitor"
                    if args.delay_source_only
                    else "submission_bottleneck_monitor"
                )
                # Notification may take time. Recheck immediately before canonical
                # publication so an old reader cannot claim a new selector's PASS.
                if observer_generation is not None:
                    result["observer_generation"] = _finish_observer_generation(
                        observer_generation,
                        PROJECT_ROOT,
                        completed_at=datetime.now(KST),
                    )
                if (
                    observer_generation is not None
                    and result["observer_generation"]["generation_current"] is not True
                ):
                    terminal.update(
                        execution_status="deferred",
                        semantic_status="partial",
                        observer_generation=result["observer_generation"],
                        source_gap_status=(
                            result.get("source_gap_semantics") or {}
                        ).get("status"),
                    )
                    raise ValidationDeferred(
                        result["observer_generation"].get("reason")
                        or "observer_generation_unavailable"
                    )
                if not args.delay_source_only:
                    result["observation_health"] = observation_health_projection(result)
                for label, path in (
                    ("state", state_path),
                    ("latest", output),
                    ("dated", output.with_name(f"{name}_{result['date']}.json")),
                ):
                    _write_state(
                        path,
                        _continuation_state(result) if label == "state" else result,
                    )
                    terminal["publication"][label] = True
            terminal.update(
                {
                    k: result.get(k)
                    for k in (
                        "status",
                        "blocker",
                        "notification_status",
                        "execution_status",
                        "semantic_status",
                    )
                }
            )
            terminal["source_gap_status"] = (
                result.get("source_gap_semantics") or {}
            ).get("status")
            terminal["pre_submit_delay_source_status"] = (
                result.get("pre_submit_delay_source_semantics") or {}
            ).get("status")
    except ValidationDeferred as exc:
        terminal.update(execution_status="deferred", blocker=str(exc))
    except (OSError, ValueError) as exc:
        terminal.update(execution_status="failed", blocker=type(exc).__name__)
    terminal["wall_seconds"] = time.monotonic() - started
    print(json.dumps(terminal, ensure_ascii=False))
    return (
        0
        if terminal["execution_status"] == "completed"
        else 75 if terminal["execution_status"] == "deferred" else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
