"""Bounded Main quantity evidence on the existing observation executor.

Owns source-only capture, never orders, subscriptions, workers or custody.
Enqueue is explicitly separate from durable append confirmation.
"""

from collections import Counter
from threading import Lock
from datetime import datetime
from itertools import islice
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import math
import os
import re
import tempfile
import time

_SINK = None
_LOCK = Lock()
_COUNTS = Counter()
_ACTIVE = {}
_DATA_ROOT = None
MAX_ACTIVE = 128
MAX_RECEIPT_BYTES = 16 * 1024


def _process_start(pid):
    try:
        return Path("/proc", str(pid), "stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError, UnicodeError):
        return None


def _process_exists(pid):
    return Path("/proc", str(pid)).is_dir()


def trace_metadata_valid(trace):
    if not isinstance(trace, dict):
        return False
    identity = trace.get("capture_lifecycle_identity")
    if identity is not None and not isinstance(identity, dict):
        return False
    if identity:
        if (
            not re.fullmatch(r"[0-9]{6}", str(identity.get("capture_stock_code") or ""))
            or not re.fullmatch(
                r"[1-9][0-9]*", str(identity.get("capture_record_id") or "")
            )
            or identity.get("capture_id")
            != _capture_id(
                {
                    **identity,
                    "entry_submit_attempt_id": trace.get("entry_submit_attempt_id"),
                    "entry_execution_sizing_plan_sha256": trace.get(
                        "entry_execution_sizing_plan_sha256"
                    ),
                }
            )
        ):
            return False
    if any(
        type(trace.get(key, 0)) is not int or trace.get(key, 0) < 0
        for key in (
            "queue_rejected_count",
            "queued_observation_count",
            "duplicate_observation_count",
        )
    ):
        return False
    return True


def _root():
    if _DATA_ROOT is not None:
        return Path(_DATA_ROOT)
    from src.utils.constants import DATA_DIR

    return Path(DATA_DIR)


def _capture_id(fields):
    identity = [
        fields.get(key)
        for key in (
            "capture_source_date",
            "capture_runtime_pid",
            "capture_runtime_start_ticks",
            "entry_submit_attempt_id",
            "entry_execution_sizing_plan_sha256",
        )
    ]
    if any(value in (None, "") for value in identity):
        return None
    identity = [str(value) for value in identity]
    if (
        not re.fullmatch(r"\d{4}-\d{2}-\d{2}", identity[0])
        or not all(re.fullmatch(r"[1-9]\d*", value) for value in identity[1:3])
        or len(identity[3]) > 128
        or not re.fullmatch(r"[a-f0-9]{64}", identity[4])
    ):
        return None
    return hashlib.sha256(
        json.dumps(identity, separators=(",", ":")).encode()
    ).hexdigest()


def _atomic_receipt(path, body):
    body = dict(body)
    body["sha256"] = hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()
    raw = (json.dumps(body, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(raw) > MAX_RECEIPT_BYTES or path.is_symlink() or path.parent.is_symlink():
        raise ValueError("cap_capture_receipt_path_or_size_invalid")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".capture-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _verified_closed(path, identity):
    if not path.exists():
        return False
    if path.is_symlink() or path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError("cap_capture_closed_contract_invalid")
    old = json.loads(path.read_bytes())
    claimed = old.pop("sha256", None)
    if (
        claimed
        != hashlib.sha256(
            json.dumps(
                old, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        or old.get("capture_id") != identity
        or old.get("raw_event_durable") is not True
        or old.get("status") not in {"finished", "interrupted"}
    ):
        raise ValueError("cap_capture_closed_contract_invalid")
    return True


def _persist_event(*args, record_id=None, fields=None, observed_at_epoch=None):
    """Run on the existing queue drain; a queued terminal is never durable proof."""
    from src.utils.pipeline_event_logger import emit_pipeline_event

    fields = fields or {}
    identity = _capture_id(fields)
    stage = args[-1]
    pending = (
        _root()
        / "runtime/initial_quantity/cap_capture_pending"
        / str(identity + ".json")
        if identity
        else None
    )
    closed = (
        (
            _root()
            / "runtime/initial_quantity/cap_capture_receipts"
            / fields["capture_source_date"]
            / (identity + ".json")
        )
        if identity
        else None
    )
    if closed is not None:
        try:
            if _verified_closed(closed, identity):
                return dict(
                    status="intentionally_not_written",
                    reason="capture_already_terminal",
                )
        except (OSError, ValueError, TypeError):
            with _LOCK:
                _COUNTS["lifecycle_receipt_failed"] += 1
    body = dict(
        schema="initial_quantity_cap_capture_lifecycle_v1",
        capture_id=identity,
        code=args[2],
        name=args[1],
        record_id=record_id,
        fields=fields,
        observed_at_epoch=observed_at_epoch,
        status="pending",
        runtime_effect=False,
    )
    if pending is not None:
        # The pending intent survives a raw append failure or process death.
        try:
            _atomic_receipt(pending, body)
        except (OSError, ValueError):
            with _LOCK:
                _COUNTS["lifecycle_receipt_failed"] += 1
    result = emit_pipeline_event(
        *args, record_id=record_id, fields=fields, observed_at_epoch=observed_at_epoch
    )
    if pending is not None and result.get("structured_append_succeeded") is True:
        raw_event = {
            key: value
            for key, value in result.items()
            if not key.startswith("structured_")
        }
        # The native writer has no event_id field. Bind its original event
        # content explicitly instead of treating queue admission as an ID.
        if (
            raw_event.get("pipeline") != "HOLDING_PIPELINE"
            or raw_event.get("stage") != stage
            or raw_event.get("stock_code") != args[2]
            or str(raw_event.get("record_id")) != str(record_id)
            or not raw_event.get("emitted_at")
            or not isinstance(raw_event.get("fields"), dict)
        ):
            with _LOCK:
                _COUNTS["lifecycle_raw_identity_missing"] += 1
            return result
        raw_id = hashlib.sha256(
            json.dumps(
                raw_event,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        terminal = stage in {
            "initial_quantity_cap_capture_finished",
            "initial_quantity_cap_capture_interrupted",
        }
        body.update(
            raw_event_durable=True,
            raw_event_id=raw_id,
            raw_event_identity_contract="canonical_original_pipeline_event_sha256_v1",
            raw_event_stage=stage,
            status=(
                ("finished" if stage.endswith("_finished") else "interrupted")
                if terminal
                else "pending"
            ),
        )
        if terminal:
            try:
                if not _verified_closed(closed, identity):
                    _atomic_receipt(closed, body)
                pending.unlink(missing_ok=True)
            except (OSError, ValueError, TypeError):
                with _LOCK:
                    _COUNTS["lifecycle_receipt_failed"] += 1
        else:
            try:
                _atomic_receipt(pending, body)
            except (OSError, ValueError):
                with _LOCK:
                    _COUNTS["lifecycle_receipt_failed"] += 1
    return result


def _recover_pending():
    """Account for a dead producer, without inventing a past horizon terminal."""
    pending_root = _root() / "runtime/initial_quantity/cap_capture_pending"
    recovered = failed = 0
    paths = islice(pending_root.glob("*.json"), MAX_ACTIVE + 1)
    for index, path in enumerate(paths):
        if index == MAX_ACTIVE:
            with _LOCK:
                _COUNTS["pending_recovery_budget_exhausted"] += 1
            break
        try:
            if path.is_symlink() or path.stat().st_size > MAX_RECEIPT_BYTES:
                raise ValueError("cap_capture_pending_path_invalid")
            body = json.loads(path.read_bytes())
            claimed = body.pop("sha256", None)
            if (
                claimed
                != hashlib.sha256(
                    json.dumps(
                        body, sort_keys=True, separators=(",", ":"), allow_nan=False
                    ).encode()
                ).hexdigest()
            ):
                raise ValueError("cap_capture_pending_hash_invalid")
            fields = body["fields"]
            if (
                body.get("schema") != "initial_quantity_cap_capture_lifecycle_v1"
                or path.stem != _capture_id(fields)
                or body.get("capture_id") != path.stem
                or body.get("status") != "pending"
            ):
                raise ValueError("cap_capture_pending_identity_invalid")
            process_start = _process_start(fields.get("capture_runtime_pid"))
            if process_start == str(fields.get("capture_runtime_start_ticks")):
                continue
            if process_start is None and _process_exists(
                fields.get("capture_runtime_pid")
            ):
                # Unreadable identity is not proof that the original owner
                # ended. Keep its pending source rather than taking custody.
                with _LOCK:
                    _COUNTS["pending_recovery_identity_unproven"] += 1
                continue
            unknown_terminal = fields.get("capture_disposition") in {
                "horizon_reached",
                "interrupted",
            }
            fields = {
                **fields,
                "capture_disposition": "interrupted",
                "capture_interruption_reason": (
                    "prior_process_terminal_durability_unverified"
                    if unknown_terminal
                    else "prior_process_ended_before_terminal"
                ),
                "capture_recovery_observed_at_epoch": time.time(),
                "capture_durable_tick_count": None,
            }
            outcome = _persist_event(
                "HOLDING_PIPELINE",
                body["name"],
                body["code"],
                "initial_quantity_cap_capture_interrupted",
                record_id=body["record_id"],
                fields=fields,
                observed_at_epoch=fields["capture_recovery_observed_at_epoch"],
            )
            if (
                outcome.get("structured_append_succeeded") is True
                or outcome.get("reason") == "capture_already_terminal"
            ):
                recovered += 1
            else:
                failed += 1
                with _LOCK:
                    _COUNTS["pending_recovery_failed"] += 1
        except (OSError, ValueError, TypeError, KeyError):
            failed += 1
            with _LOCK:
                _COUNTS["pending_recovery_failed"] += 1
    return dict(
        status="intentionally_not_written",
        reason="bounded_capture_recovery_accounted",
        recovered=recovered,
        failed=failed,
    )


def register(*, code, name, record_id, trace):
    """Retain only source scalars, independent of the mutable stock lifecycle."""
    if not trace_metadata_valid(trace):
        with _LOCK:
            _COUNTS["capture_metadata_invalid"] += 1
        return False
    fields = {
        key: trace.get(key)
        for key in ("entry_submit_attempt_id", "entry_execution_sizing_plan_sha256")
    }
    started = trace.get("started_at_epoch")
    if type(started) not in (int, float) or not math.isfinite(started) or started <= 0:
        with _LOCK:
            _COUNTS["capture_metadata_invalid"] += 1
        return False
    try:
        day = datetime.fromtimestamp(started, ZoneInfo("Asia/Seoul")).date().isoformat()
    except (ValueError, OverflowError, OSError):
        with _LOCK:
            _COUNTS["capture_metadata_invalid"] += 1
        return False
    fields.update(
        capture_source_date=day,
        capture_runtime_pid=os.getpid(),
        capture_runtime_start_ticks=_process_start(os.getpid()),
        capture_record_id=record_id,
        capture_stock_code=str(code),
        capture_planned_epoch=started,
        capture_end_epoch=started + 1200,
        capture_clock_status="no_order_start_observed",
        capture_disposition="pending",
        observation_coverage="sampled_last_trade_tick",
        actual_order_submitted=False,
        broker_order_forbidden=True,
        runtime_effect=False,
    )
    identity = _capture_id(fields)
    if identity is None:
        with _LOCK:
            _COUNTS["capture_identity_unavailable"] += 1
        return False
    fields["capture_id"] = identity
    with _LOCK:
        existing = _ACTIVE.get(identity)
        if identity not in _ACTIVE and len(_ACTIVE) >= MAX_ACTIVE:
            _COUNTS["capture_registry_full"] += 1
            return False
        if existing is None:
            _ACTIVE[identity] = dict(
                code=str(code),
                name=str(name or code),
                record_id=record_id,
                fields=fields,
            )
    trace["capture_lifecycle_identity"] = {
        key: fields[key]
        for key in (
            "capture_id",
            "capture_source_date",
            "capture_runtime_pid",
            "capture_runtime_start_ticks",
            "capture_stock_code",
            "capture_record_id",
        )
    }
    if existing is not None and existing.get("capture_started_queued"):
        return True
    accepted = append(
        code=code,
        name=name,
        record_id=record_id,
        stage="initial_quantity_cap_capture_started",
        fields=fields,
        observed_at_epoch=started,
    )
    if not accepted:
        trace["queue_rejected_count"] = trace.get("queue_rejected_count", 0) + 1
    with _LOCK:
        if identity in _ACTIVE:
            _ACTIVE[identity]["capture_started_queued"] = accepted
    return accepted


def interrupt(*, code, name, record_id, trace, reason, now=None):
    if not trace_metadata_valid(trace):
        with _LOCK:
            _COUNTS["capture_metadata_invalid"] += 1
        return False
    now = time.time() if now is None else now
    if type(now) not in (int, float) or not math.isfinite(now) or now <= 0:
        with _LOCK:
            _COUNTS["capture_metadata_invalid"] += 1
        return False
    fields = {
        **(trace.get("capture_lifecycle_identity") or {}),
        "entry_submit_attempt_id": trace.get("entry_submit_attempt_id"),
        "entry_execution_sizing_plan_sha256": trace.get(
            "entry_execution_sizing_plan_sha256"
        ),
        "capture_planned_epoch": trace.get("started_at_epoch"),
        "capture_order_start_epoch": trace.get("order_start_epoch"),
        "capture_end_epoch": trace.get("order_capture_end_epoch"),
        "capture_clock_status": trace.get(
            "capture_clock_status", "no_order_start_observed"
        ),
        "capture_queue_rejected_count": trace.get("queue_rejected_count", 0),
        "capture_queued_count": trace.get("queued_observation_count", 0),
        "capture_disposition": "interrupted",
        "capture_interruption_reason": reason,
        "observation_coverage": "sampled_last_trade_tick",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
    }
    return append(
        code=fields.get("capture_stock_code") or code,
        name=name,
        record_id=fields.get("capture_record_id", record_id),
        stage="initial_quantity_cap_capture_interrupted",
        fields=fields,
        observed_at_epoch=now,
    )


def capture_active(identity):
    with _LOCK:
        return identity in _ACTIVE


def observe_position_terminal(event):
    """Censor the exact current capture after durable native SELL completion.

    Receipt/reconciliation writers do not call the state-handler logger. The
    shared raw writer reaches this owner only after persisting the original
    real terminal; a mutable target or a queued event is not terminal proof.
    """
    fields = event.get("fields") or {}
    if (
        event.get("pipeline") != "HOLDING_PIPELINE"
        or event.get("stage") != "sell_completed"
        or fields.get("pipeline_lifecycle_population_scope") != "real_record_bound"
        or fields.get("actual_order_submitted") != "True"
        or fields.get("broker_order_forbidden") != "False"
    ):
        return
    at = datetime.fromisoformat(event["emitted_at"])
    if at.tzinfo is None:
        at = at.replace(tzinfo=ZoneInfo("Asia/Seoul"))
    now = at.timestamp()
    with _LOCK:
        matches = [
            {**row, "fields": dict(row["fields"])}
            for row in _ACTIVE.values()
            if str(row["record_id"]) == str(event.get("record_id"))
            and row["code"] == event.get("stock_code")
        ]
    for row in matches:
        source = row["fields"]
        planned = source.get("capture_planned_epoch")
        if (
            source.get("capture_runtime_pid") != os.getpid()
            or source.get("capture_runtime_start_ticks") != _process_start(os.getpid())
            or type(planned) not in (int, float)
            or not math.isfinite(planned)
            or now < planned
        ):
            with _LOCK:
                _COUNTS["terminal_capture_binding_invalid"] += 1
            continue
        end = source.get("capture_end_epoch")
        reason = (
            "position_completed_before_capture_horizon"
            if type(end) in (int, float) and math.isfinite(end) and now < end
            else "capture_horizon_terminal_missing_at_position_completion"
        )
        append(
            code=row["code"],
            name=row["name"],
            record_id=row["record_id"],
            stage="initial_quantity_cap_capture_interrupted",
            observed_at_epoch=now,
            fields={
                **source,
                "capture_disposition": "interrupted",
                "capture_interruption_reason": reason,
                "capture_position_terminal_sha256": hashlib.sha256(
                    json.dumps(
                        event,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    ).encode()
                ).hexdigest(),
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
            },
        )


def quote_route_binding(item, market_route, *, legacy=False):
    """Bind an existing local quote receipt without inferring fill venue.

    These are the local session/entry snapshot owner's route names, not API
    request or FID mappings. Legacy artifact rows retain their old names.
    """
    routes = {
        "krx_only": ("KRX", ""),
        "nxt_only": ("NXT", "_NX"),
        "krx_nxt_integrated": ("SOR", "_AL"),
    }
    if legacy:
        routes.update(KRX=("KRX", ""), NXT=("NXT", "_NX"), SOR=("SOR", "_AL"))
    value = routes.get(market_route)
    if not value or not isinstance(item, str):
        return None
    route, suffix = value
    if not re.fullmatch(r"[0-9]{6}" + suffix, item):
        return None
    return dict(
        order_route=route,
        market_data_route=market_route,
        item=item,
        fill_venues=("KRX", "NXT") if route == "SOR" else (route,),
        underlying_event_venue_proven=route != "SOR",
    )


def configure_sink(sink, *, recover_pending=False, data_root=None):
    global _SINK
    global _DATA_ROOT
    if data_root is not None:
        _DATA_ROOT = Path(data_root)
    if sink is None and _SINK is not None:
        with _LOCK:
            active = list(_ACTIVE.values())
        for value in active:
            append(
                code=value["code"],
                name=value["name"],
                record_id=value["record_id"],
                stage="initial_quantity_cap_capture_interrupted",
                fields={
                    **value["fields"],
                    "capture_disposition": "interrupted",
                    "capture_interruption_reason": "process_shutdown_observation_censored",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                },
                observed_at_epoch=time.time(),
            )
    _SINK = sink
    if sink is not None and recover_pending:
        try:
            outcome = sink(_recover_pending, observation_category="initial_quantity")
            if not isinstance(outcome, dict) or outcome.get("status") != "queued":
                with _LOCK:
                    _COUNTS["pending_recovery_queue_failed"] += 1
        except Exception:
            with _LOCK:
                _COUNTS["pending_recovery_queue_failed"] += 1


def append(*, code, name, record_id, stage, fields, observed_at_epoch):
    from src.utils.pipeline_event_logger import emit_pipeline_event

    if not isinstance(fields, dict):
        with _LOCK:
            _COUNTS["capture_metadata_invalid"] += 1
        return False
    if _SINK is None:
        with _LOCK:
            _COUNTS["writer_not_prepared"] += 1
        return False
    try:
        writer = (
            _persist_event
            if stage.startswith("initial_quantity_cap_capture_")
            else emit_pipeline_event
        )
        result = _SINK(
            writer,
            "HOLDING_PIPELINE",
            str(name or code),
            str(code),
            stage,
            record_id=record_id,
            fields=fields,
            observed_at_epoch=observed_at_epoch,
            observation_category="initial_quantity",
        )
        accepted = isinstance(result, dict) and result.get("status") == "queued"
    except Exception:
        accepted = False
    with _LOCK:
        _COUNTS["queued" if accepted else "queue_rejected"] += 1
    identity = _capture_id(fields)
    with _LOCK:
        active = _ACTIVE.get(identity)
        if active is not None:
            active["fields"].update(fields)
            if not accepted or stage == "initial_quantity_cap_following_tick":
                key = (
                    "capture_queue_rejected_count"
                    if not accepted
                    else "capture_queued_count"
                )
                count = active["fields"].get(key, 0)
                if type(count) is int and count >= 0:
                    active["fields"][key] = count + 1
                else:
                    _COUNTS["capture_metadata_invalid"] += 1
            if accepted and stage in {
                "initial_quantity_cap_capture_finished",
                "initial_quantity_cap_capture_interrupted",
            }:
                _ACTIVE.pop(identity, None)
    return accepted


def snapshot():
    with _LOCK:
        return dict(_COUNTS)
