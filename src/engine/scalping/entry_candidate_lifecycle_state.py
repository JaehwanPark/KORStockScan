"""Candidate-owned entry lifecycle instrumentation and materialization.

This module observes the already-selected V2.14 live candidate path.  It has no
order, account, provider, pricing, sizing, threshold, or bot-state authority.
Failures are isolated from the trading path and a missing component is never
inferred from a natural (control) position lifecycle.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from src.engine.trade_profit import get_trade_cost_rate
from src.utils.constants import DATA_DIR
from src.utils.logger import log_error

EVENT_SCHEMA = "entry_candidate_lifecycle_event_v1"
STATE_SCHEMA = "entry_candidate_lifecycle_state_v1"
REPORT_SCHEMA = "entry_candidate_lifecycle_state_report_v1"
CONTEXT_SCHEMA = "entry_candidate_lifecycle_context_v1"
CONTEXT_KEY = "entry_candidate_lifecycle_context"

EVENT_DIR = DATA_DIR / "entry_candidate_lifecycle"
REPORT_DIR = DATA_DIR / "report" / "entry_candidate_lifecycle_state"

OBSERVATION_CONTRACT = {
    "metric_role": "candidate_lifecycle_source_quality",
    "decision_authority": "offline_candidate_lifecycle_attribution_only",
    "window_policy": "same_exact_candidate_trace_probe_through_terminal_exit",
    "sample_floor": "one_candidate_probe_submission_starts_observation",
    "primary_decision_metric": "full_lifecycle_evaluable_candidate_count",
    "source_quality_gate": (
        "same_trace_pair_venue_session_with_explicit_time_price_quantity_cost"
    ),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": (
        "runtime_decision|order_submit|provider_or_model_change|threshold_change|"
        "price_or_quantity_change|cap_release|broker_guard_bypass|hard_safety_bypass|"
        "attribute_natural_control_lifecycle|assume_missing_stage|bot_restart"
    ),
}

_WRITE_LOCK = threading.RLock()
_ACTIVE_POLICY_STATUSES = {"active_bounded_krx_canary", "active_bounded_nxt_canary"}
_ACTIVE_ADAPTERS = {"entry_setup_v2_14_krx_bounded_probe_v1"}
_VALID_VENUES = {"KRX", "NXT", "PREMARKET_KRX_LIKE"}

_COMPONENT_COMPLETE_STATUSES = {
    "probe": {"filled"},
    "post_probe": {"evaluated"},
    "residual_multi_leg": {"terminal_submitted", "terminal_not_submitted"},
    "scale_in": {"evaluated_submitted", "evaluated_not_submitted"},
    "holding_exit": {"terminal_exit_filled"},
    "economics": {"complete"},
}

_STAGE_COMPONENTS = {
    "ai_confirmed": ("decision",),
    "entry_split_order_plan_applied": ("probe",),
    "entry_split_order_plan_skipped": ("probe",),
    "probe_submitted": ("probe",),
    "probe_filled": ("probe",),
    "probe_source_quality_deferred": ("post_probe",),
    "residual_blocked": ("post_probe", "residual_multi_leg"),
    "bundle_completed": ("residual_multi_leg",),
    "holding_started": ("holding_exit",),
    "stat_action_decision_snapshot": ("scale_in",),
    "pyramid_blocked_reason": ("scale_in",),
    "scale_in_arm_blocked": ("scale_in",),
    "scale_in_executed": ("scale_in",),
    "exit_signal": ("holding_exit",),
    "sell_order_sent": ("holding_exit",),
    "sell_completed": ("holding_exit", "economics"),
}

_ALLOWED_EXACT_FIELDS = {
    "action",
    "actual_order_submitted",
    "ai_decision_trace_id",
    "ai_input_payload_sha256",
    "avg_buy_price",
    "best_ask_at_submit",
    "best_bid_at_submit",
    "broker_order_no",
    "broker_route",
    "broker_route_resolution",
    "buy_price",
    "buy_qty",
    "chosen_action",
    "cancel_ord_no",
    "cancel_reason",
    "cancel_response",
    "cum_filled_qty",
    "decision_quality_live_adapter",
    "effective_order_type",
    "effective_venue",
    "entry_ai_full_entry_forbidden",
    "entry_probe_first_required",
    "entry_probe_intent",
    "entry_probe_intent_status",
    "entry_setup_live_policy_mode",
    "entry_setup_live_policy_status",
    "entry_setup_live_policy_effective_venue",
    "entry_setup_live_policy_session_bucket",
    "entry_split_order_leg_count",
    "entry_split_order_probe_bundle_id",
    "entry_split_order_probe_first_applied",
    "entry_split_probe_bundle_id",
    "entry_split_probe_continuation_action",
    "entry_split_probe_direction_reason",
    "entry_split_probe_direction_state",
    "entry_split_probe_phase",
    "entry_split_probe_requested_qty",
    "entry_split_probe_terminal_abort_detail_reason",
    "entry_split_probe_terminal_abort_reason",
    "entry_split_probe_terminal_at",
    "entry_split_probe_terminal_continuation_action",
    "entry_split_probe_terminal_direction_reason",
    "entry_split_probe_terminal_direction_state",
    "entry_split_probe_terminal_outcome",
    "exit_decision_source",
    "exit_rule",
    "fee_tax_cost_rate",
    "fill_price",
    "fill_qty",
    "filled_qty",
    "holding_started_at",
    "mark_price_at_submit",
    "new_avg_price",
    "new_buy_qty",
    "order_filled_qty",
    "order_no",
    "order_price",
    "order_requested_qty",
    "ord_no",
    "orig_ord_no",
    "paired_replay_id",
    "payload_sha256",
    "position_cycle_id",
    "position_peak_cycle_id",
    "probe_bundle_id",
    "probe_fill_slippage_bps",
    "probe_submit_best_ask",
    "probe_submit_to_fill_ms",
    "profit_rate",
    "price",
    "realized_pnl_krw",
    "reason",
    "remaining_qty",
    "requested_qty",
    "residual_leg_index",
    "residual_submitted_leg_count",
    "residual_submitted_qty",
    "runner_realized_pnl_krw",
    "scale_in_action_reason",
    "scale_in_action_type",
    "scale_in_arm",
    "scale_in_blocker_namespace",
    "scale_in_blocker_reason",
    "scale_in_gate_allowed",
    "scale_in_gate_reason",
    "sell_price",
    "sell_qty",
    "session_bucket",
    "submitted_broker_price",
    "submitted_price",
    "tag",
    "qty",
}

_ALLOWED_PREFIXES = (
    "post_probe_",
    "residual_",
    "entry_split_probe_",
    "entry_split_order_",
    "scale_in_",
)
_SENSITIVE_FIELD_PARTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "account_no",
    "account_number",
    "app_key",
    "appkey",
)


def event_path(target_date: str) -> Path:
    return EVENT_DIR / f"entry_candidate_lifecycle_events_{target_date}.jsonl"


def report_path(target_date: str) -> Path:
    return REPORT_DIR / f"entry_candidate_lifecycle_state_{target_date}.json"


def _now() -> datetime:
    return datetime.now().astimezone()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def paired_replay_id(decision_trace_id: str, payload_sha256: str) -> str:
    return f"pair-{_canonical_sha256((decision_trace_id, payload_sha256))[:24]}"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _text(value).upper()


def _number(value: Any) -> float | None:
    if value in (None, "", "-", "not_available", "not_evaluated"):
        return None
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> int | None:
    parsed = _number(value)
    return int(parsed) if parsed is not None else None


def _identifier(value: Any) -> str:
    text = _text(value)
    if text.lower() in {"", "-", "none", "null", "not_available"}:
        return ""
    return text


def _ensure_secure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    _ensure_secure_parent(path)
    payload = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    with _WRITE_LOCK:
        with path.open("a", encoding="utf-8") as handle:
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.write(payload + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_secure_parent(path)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _candidate_context_from_fields(
    stock: dict[str, Any], fields: dict[str, Any], *, observed_at: datetime
) -> dict[str, Any] | None:
    status = _text(fields.get("entry_setup_live_policy_status"))
    adapter = _text(fields.get("decision_quality_live_adapter"))
    if status not in _ACTIVE_POLICY_STATUSES or adapter not in _ACTIVE_ADAPTERS:
        return None
    trace_id = _text(
        fields.get("ai_decision_trace_id")
        or fields.get("decision_trace_id")
        or stock.get("last_watching_ai_decision_trace_id")
    )
    payload_sha = _text(
        fields.get("ai_input_payload_sha256") or fields.get("payload_sha256")
    )
    venue = _upper(
        fields.get("entry_setup_live_policy_effective_venue")
        or fields.get("effective_venue")
        or fields.get("venue")
    )
    session = _text(
        fields.get("entry_setup_live_policy_session_bucket")
        or fields.get("session_bucket")
    ).lower()
    if (
        not trace_id
        or len(payload_sha) != 64
        or venue not in _VALID_VENUES
        or not session
    ):
        return None
    context = {
        "schema": CONTEXT_SCHEMA,
        "decision_trace_id": trace_id,
        "payload_sha256": payload_sha,
        "paired_replay_id": paired_replay_id(trace_id, payload_sha),
        "effective_venue": venue,
        "session_bucket": session,
        "policy_status": status,
        "policy_mode": _text(fields.get("entry_setup_live_policy_mode")) or "unknown",
        "live_adapter": adapter,
        "prompt_version": _text(fields.get("ai_prompt_version")),
        "stock_code": _text(stock.get("code") or fields.get("stock_code"))[:6],
        "record_id": stock.get("id"),
        "bound_at": observed_at.isoformat(),
        "trade_date": (
            _text(fields.get("entry_setup_live_policy_target_date"))
            or observed_at.date().isoformat()
        ),
        "lifecycle_basis": "observed_live_candidate",
        "terminal": False,
    }
    stock[CONTEXT_KEY] = context
    return context


def bind_candidate_context(
    stock: dict[str, Any] | None,
    fields: dict[str, Any] | None,
    *,
    observed_at: datetime | None = None,
    output_path: Path | None = None,
) -> dict[str, Any] | None:
    """Bind an exact V2.14 candidate decision without affecting its decision."""

    if not isinstance(stock, dict) or not isinstance(fields, dict):
        return None
    now = observed_at or _now()
    context = _candidate_context_from_fields(stock, fields, observed_at=now)
    if context is None:
        return None
    row = _event_row(
        stock,
        context,
        stage="candidate_decision_bound",
        components=("decision",),
        fields=fields,
        observed_at=now,
    )
    try:
        _append_jsonl(output_path or event_path(context["trade_date"]), row)
    except OSError as exc:
        log_error(f"[ENTRY_CANDIDATE_LIFECYCLE] bind write failed: {exc}")
    return context


def _components_for_stage(
    stage: str,
    stock: dict[str, Any] | None = None,
    fields: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    normalized = _text(stage).lower()
    if normalized == "entry_order_cancel_confirmed":
        tag = _text((fields or {}).get("tag"))
        if tag.startswith("entry_split_probe_residual_"):
            return ("residual_multi_leg",)
        return ()
    if normalized == "position_rebased_after_fill":
        phase = _text((stock or {}).get("entry_split_probe_phase")).lower()
        if phase in {
            "residual_claimed",
            "residual_submitting",
            "residual_submitted",
            "residual_partial_submitted",
            "complete",
        }:
            return ("residual_multi_leg",)
        if phase == "probe_filled":
            return ("probe",)
        return ()
    if normalized in _STAGE_COMPONENTS:
        return _STAGE_COMPONENTS[normalized]
    if normalized.startswith("post_probe_") or normalized.startswith(
        "probe_direction_"
    ):
        return ("post_probe",)
    if normalized.startswith("residual_"):
        return ("post_probe", "residual_multi_leg")
    if normalized.startswith("scale_in_") or normalized.startswith("pyramid_"):
        return ("scale_in",)
    if normalized.startswith("sell_") or normalized.startswith("exit_"):
        return ("holding_exit",)
    return ()


def _context_has_execution_lineage(
    stock: dict[str, Any], context: dict[str, Any]
) -> bool:
    if _identifier(context.get("probe_bundle_id")):
        return True
    if _identifier(
        stock.get("entry_split_probe_bundle_id")
        or stock.get("entry_split_probe_exit_bundle_id")
    ):
        return True
    return _upper(stock.get("status")) == "HOLDING"


def _recover_candidate_context(
    stock: dict[str, Any], code: str, *, observed_at: datetime
) -> dict[str, Any] | None:
    """Recover a small candidate context after a process restart.

    Recovery is identity-only.  It cannot create an event when neither the
    exact probe bundle nor decision trace is present on the recovered holding.
    """

    bundle_id = _identifier(
        stock.get("entry_split_probe_bundle_id")
        or stock.get("entry_split_probe_exit_bundle_id")
    )
    trace_id = _identifier(
        stock.get("entry_split_probe_ai_decision_trace_id")
        or stock.get("last_watching_ai_decision_trace_id")
    )
    active_trace_lineage = bool(
        trace_id
        and _text(stock.get("entry_setup_live_policy_status"))
        in _ACTIVE_POLICY_STATUSES
        and _text(stock.get("decision_quality_live_adapter")) in _ACTIVE_ADAPTERS
    )
    if not bundle_id and not active_trace_lineage:
        return None
    candidates: list[dict[str, Any]] = []
    for days_ago in (0, 1):
        source_date = (observed_at.date() - timedelta(days=days_ago)).isoformat()
        for row in _read_events(event_path(source_date)):
            if _text(row.get("stock_code")) != _text(code)[:6]:
                continue
            row_bundle_id = _identifier(row.get("probe_bundle_id"))
            row_trace_id = _identifier(row.get("decision_trace_id"))
            if bundle_id and row_bundle_id == bundle_id:
                candidates.append(row)
            elif active_trace_lineage and row_trace_id == trace_id:
                candidates.append(row)
    if not candidates:
        return None
    candidates.sort(key=lambda row: _text(row.get("observed_at")))
    latest = candidates[-1]
    if _text(latest.get("stage")) == "sell_completed":
        return None
    context = {
        "schema": CONTEXT_SCHEMA,
        "decision_trace_id": latest.get("decision_trace_id"),
        "payload_sha256": latest.get("payload_sha256"),
        "paired_replay_id": latest.get("paired_replay_id"),
        "effective_venue": latest.get("effective_venue"),
        "session_bucket": latest.get("session_bucket"),
        "policy_status": latest.get("policy_status"),
        "policy_mode": latest.get("policy_mode"),
        "live_adapter": "entry_setup_v2_14_krx_bounded_probe_v1",
        "stock_code": _text(code)[:6],
        "record_id": latest.get("record_id") or stock.get("id"),
        "bound_at": latest.get("observed_at"),
        "trade_date": _text(latest.get("trade_date"))
        or _text(latest.get("observed_at"))[:10],
        "lifecycle_basis": latest.get("lifecycle_basis") or "observed_live_candidate",
        "probe_bundle_id": bundle_id or latest.get("probe_bundle_id"),
        "position_cycle_id": latest.get("position_cycle_id"),
        "broker_order_no": latest.get("broker_order_no"),
        "terminal": False,
        "recovered_after_restart": True,
    }
    stock[CONTEXT_KEY] = context
    return context


def _safe_event_fields(stock: dict[str, Any], fields: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in (stock, fields):
        for key, value in source.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if any(part in key_lower for part in _SENSITIVE_FIELD_PARTS):
                continue
            if key_text in _ALLOWED_EXACT_FIELDS or key_text.startswith(
                _ALLOWED_PREFIXES
            ):
                if isinstance(value, (str, int, float, bool)) or value is None:
                    merged[key_text] = value
    return merged


def _event_row(
    stock: dict[str, Any],
    context: dict[str, Any],
    *,
    stage: str,
    components: tuple[str, ...],
    fields: dict[str, Any],
    observed_at: datetime,
) -> dict[str, Any]:
    data = _safe_event_fields(stock, fields)
    if _text(stage).lower() == "sell_completed":
        data.setdefault("fee_tax_cost_rate", float(get_trade_cost_rate()))
        data.setdefault(
            "fee_tax_basis", "configured_combined_sell_side_cost_rate_at_fill"
        )
    bundle_id = _identifier(
        fields.get("probe_bundle_id")
        or fields.get("entry_split_probe_bundle_id")
        or stock.get("entry_split_probe_bundle_id")
        or context.get("probe_bundle_id")
    )
    cycle_id = _identifier(
        fields.get("position_cycle_id")
        or stock.get("position_cycle_id")
        or stock.get("position_peak_cycle_id")
        or context.get("position_cycle_id")
    )
    order_no = _identifier(
        fields.get("broker_order_no")
        or fields.get("order_no")
        or fields.get("ord_no")
        or fields.get("orig_ord_no")
    )
    if not order_no and _text(stage).lower() in {"probe_submitted", "probe_filled"}:
        order_no = _identifier(stock.get("entry_split_probe_order_no"))
    if bundle_id:
        context["probe_bundle_id"] = bundle_id
    if cycle_id:
        context["position_cycle_id"] = cycle_id
    if order_no:
        context["broker_order_no"] = order_no
    event_venue = _upper(
        fields.get("effective_venue")
        or fields.get("entry_setup_live_policy_effective_venue")
    )
    event_session = _text(
        fields.get("session_bucket")
        or fields.get("entry_setup_live_policy_session_bucket")
    ).lower()
    route_conflict = bool(
        (event_venue and event_venue != context.get("effective_venue"))
        or (event_session and event_session != context.get("session_bucket"))
    )
    return {
        "schema": EVENT_SCHEMA,
        "event_id": _canonical_sha256(
            (
                context.get("paired_replay_id"),
                stage,
                observed_at.isoformat(),
                bundle_id,
                cycle_id,
                order_no,
                data,
            )
        )[:32],
        "observed_at": observed_at.isoformat(),
        "stage": _text(stage).lower(),
        "components": list(components),
        "decision_trace_id": context.get("decision_trace_id"),
        "payload_sha256": context.get("payload_sha256"),
        "paired_replay_id": context.get("paired_replay_id"),
        "effective_venue": context.get("effective_venue"),
        "session_bucket": context.get("session_bucket"),
        "policy_status": context.get("policy_status"),
        "policy_mode": context.get("policy_mode"),
        "trade_date": context.get("trade_date"),
        "lifecycle_basis": context.get("lifecycle_basis"),
        "stock_code": context.get("stock_code") or _text(stock.get("code"))[:6],
        "record_id": context.get("record_id") or stock.get("id"),
        "probe_bundle_id": bundle_id or None,
        "position_cycle_id": cycle_id or None,
        "broker_order_no": order_no or None,
        "route_conflict": route_conflict,
        "data": data,
        **OBSERVATION_CONTRACT,
    }


def observe_candidate_transition(
    stock: dict[str, Any] | None,
    code: str,
    stage: str,
    fields: dict[str, Any] | None = None,
    *,
    observed_at: datetime | None = None,
    output_path: Path | None = None,
) -> bool:
    """Record one whitelisted candidate lifecycle transition, fail-open."""

    if not isinstance(stock, dict):
        return False
    fields = fields if isinstance(fields, dict) else {}
    now = observed_at or _now()
    components = _components_for_stage(stage, stock, fields)
    if not components:
        return False
    stock.setdefault("code", _text(code)[:6])
    context = stock.get(CONTEXT_KEY)
    lazy_bound = False
    normalized_stage = _text(stage).lower()
    if normalized_stage == "ai_confirmed" and isinstance(context, dict):
        if _context_has_execution_lineage(stock, context):
            return False
        previous_context = context
        replacement = _candidate_context_from_fields(stock, fields, observed_at=now)
        if replacement is None:
            stock.pop(CONTEXT_KEY, None)
            return False
        if replacement.get("paired_replay_id") == previous_context.get(
            "paired_replay_id"
        ):
            stock[CONTEXT_KEY] = previous_context
            context = previous_context
        else:
            context = replacement
            lazy_bound = True
    if not isinstance(context, dict):
        context = _candidate_context_from_fields(stock, fields, observed_at=now)
        if context is not None:
            lazy_bound = True
        else:
            context = _recover_candidate_context(stock, code, observed_at=now)
    if not isinstance(context, dict) or context.get("terminal") is True:
        return False
    if lazy_bound:
        try:
            _append_jsonl(
                output_path or event_path(context["trade_date"]),
                _event_row(
                    stock,
                    context,
                    stage="candidate_decision_bound",
                    components=("decision",),
                    fields=fields,
                    observed_at=now,
                ),
            )
        except OSError as exc:
            log_error(f"[ENTRY_CANDIDATE_LIFECYCLE] lazy bind failed: {exc}")
    if lazy_bound and _text(stage).lower() == "ai_confirmed":
        return True
    row = _event_row(
        stock,
        context,
        stage=stage,
        components=components,
        fields=fields,
        observed_at=now,
    )
    signature = _canonical_sha256(
        (
            row.get("stage"),
            row.get("components"),
            row.get("probe_bundle_id"),
            row.get("position_cycle_id"),
            row.get("broker_order_no"),
            row.get("data"),
        )
    )
    if context.get("last_transition_signature") == signature:
        return False
    context["last_transition_signature"] = signature
    try:
        _append_jsonl(
            output_path
            or event_path(_text(context.get("trade_date")) or now.date().isoformat()),
            row,
        )
    except OSError as exc:
        log_error(
            f"[ENTRY_CANDIDATE_LIFECYCLE] {code or '-'} {stage} write failed: {exc}"
        )
        return False
    if _text(stage).lower() == "sell_completed":
        context["terminal"] = True
    return True


def observe_candidate_transition_safe(
    stock: dict[str, Any] | None,
    code: str,
    stage: str,
    fields: dict[str, Any] | None = None,
    *,
    observed_at: datetime | None = None,
    output_path: Path | None = None,
) -> bool:
    """Fail-open wrapper used by latency-sensitive trading call sites."""

    try:
        return observe_candidate_transition(
            stock,
            code,
            stage,
            fields,
            observed_at=observed_at,
            output_path=output_path,
        )
    except Exception as exc:  # instrumentation must never alter trading flow
        log_error(
            f"[ENTRY_CANDIDATE_LIFECYCLE] {code or '-'} {stage} observer failed: {exc}"
        )
        return False


def _read_events(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return ()

    def _iter() -> Iterable[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict) and row.get("schema") == EVENT_SCHEMA:
                    yield row

    return _iter()


def _last_event(
    events: list[dict[str, Any]], stages: set[str]
) -> dict[str, Any] | None:
    return next(
        (row for row in reversed(events) if _text(row.get("stage")) in stages),
        None,
    )


def _component(
    status: str, event: dict[str, Any] | None, **extra: Any
) -> dict[str, Any]:
    return {
        "status": status,
        "observed_at": event.get("observed_at") if event else None,
        "stage": event.get("stage") if event else None,
        "data": dict(event.get("data") or {}) if event else {},
        **extra,
    }


def _materialize_one(events: list[dict[str, Any]]) -> dict[str, Any]:
    events.sort(key=lambda row: _text(row.get("observed_at")))
    first = events[0]
    policy_mode = _text(first.get("policy_mode")) or "unknown"
    identity_fields = (
        "decision_trace_id",
        "payload_sha256",
        "paired_replay_id",
        "lifecycle_basis",
    )
    identity_conflict = any(
        any(row.get(field) != first.get(field) for field in identity_fields)
        for row in events[1:]
    )
    route_conflict = bool(
        any(row.get("route_conflict") is True for row in events)
        or any(
            row.get("effective_venue") != first.get("effective_venue")
            or row.get("session_bucket") != first.get("session_bucket")
            for row in events[1:]
        )
    )
    expected_pair_id = paired_replay_id(
        _text(first.get("decision_trace_id")),
        _text(first.get("payload_sha256")),
    )
    pair_identity_valid = bool(
        _text(first.get("decision_trace_id"))
        and len(_text(first.get("payload_sha256"))) == 64
        and first.get("paired_replay_id") == expected_pair_id
    )
    event_contract_valid = all(
        row.get("runtime_effect") is False
        and row.get("allowed_runtime_apply") is False
        and row.get("actual_order_submitted") is False
        and row.get("broker_order_forbidden") is True
        and row.get("decision_authority") == OBSERVATION_CONTRACT["decision_authority"]
        for row in events
    )

    probe_submitted = _last_event(events, {"probe_submitted"})
    probe_filled = _last_event(events, {"probe_filled"})
    if probe_filled and _integer((probe_filled.get("data") or {}).get("fill_qty")):
        probe = _component("filled", probe_filled)
    elif probe_submitted:
        probe = _component("submitted_not_filled", probe_submitted)
    else:
        probe = _component("not_observed", None)

    post_probe_events = [
        row for row in events if "post_probe" in (row.get("components") or [])
    ]
    post_probe_event = post_probe_events[-1] if post_probe_events else None
    post_data = dict(post_probe_event.get("data") or {}) if post_probe_event else {}
    direction_state = _upper(
        post_data.get("post_probe_direction_state")
        or post_data.get("entry_split_probe_terminal_direction_state")
        or post_data.get("entry_split_probe_direction_state")
    )
    continuation_action = _upper(
        post_data.get("post_probe_continuation_action")
        or post_data.get("entry_split_probe_terminal_continuation_action")
        or post_data.get("entry_split_probe_continuation_action")
    )
    post_probe = _component(
        "evaluated" if direction_state and continuation_action else "not_evaluated",
        post_probe_event,
        direction_state=direction_state or None,
        continuation_action=continuation_action or None,
    )

    residual_events = [
        row for row in events if "residual_multi_leg" in (row.get("components") or [])
    ]
    residual_event = residual_events[-1] if residual_events else None
    residual_data = dict(residual_event.get("data") or {}) if residual_event else {}
    residual_stage = _text(residual_event.get("stage")) if residual_event else ""
    residual_fills_by_order: dict[str, dict[str, Any]] = {}
    residual_cancels_by_order: dict[str, dict[str, Any]] = {}
    for row in residual_events:
        row_data = dict(row.get("data") or {})
        order_key = _text(
            row.get("broker_order_no")
            or row_data.get("order_no")
            or row_data.get("ord_no")
            or row_data.get("orig_ord_no")
        )
        if not order_key:
            continue
        if _text(row.get("stage")) == "position_rebased_after_fill":
            residual_fills_by_order[order_key] = row_data
        elif _text(row.get("stage")) == "entry_order_cancel_confirmed":
            residual_cancels_by_order[order_key] = row_data
    residual_legs = []
    for row in residual_events:
        if _text(row.get("stage")) != "residual_submitted":
            continue
        row_data = dict(row.get("data") or {})
        order_key = _text(
            row.get("broker_order_no")
            or row_data.get("order_no")
            or row_data.get("ord_no")
        )
        fill_data = residual_fills_by_order.get(order_key, {})
        cancel_data = residual_cancels_by_order.get(order_key, {})
        requested_leg_qty = _integer(row_data.get("qty"))
        filled_leg_qty = _integer(fill_data.get("order_filled_qty"))
        residual_legs.append(
            {
                "submitted_at": row.get("observed_at"),
                "filled_at": (
                    next(
                        (
                            event.get("observed_at")
                            for event in reversed(residual_events)
                            if _text(event.get("stage"))
                            == "position_rebased_after_fill"
                            and _text(event.get("broker_order_no")) == order_key
                        ),
                        None,
                    )
                ),
                "order_no": order_key or None,
                "leg_index": row_data.get("residual_leg_index"),
                "submitted_price": _integer(row_data.get("price")),
                "requested_qty": requested_leg_qty,
                "fill_price": _integer(fill_data.get("fill_price")),
                "filled_qty": filled_leg_qty,
                "fill_slippage_bps": (
                    (
                        float(_integer(fill_data.get("fill_price")))
                        - float(_integer(row_data.get("price")))
                    )
                    / float(_integer(row_data.get("price")))
                    * 10000.0
                    if _integer(fill_data.get("fill_price"))
                    and _integer(row_data.get("price"))
                    else None
                ),
                "terminal_state": (
                    "filled"
                    if requested_leg_qty
                    and filled_leg_qty is not None
                    and filled_leg_qty >= requested_leg_qty
                    else (
                        "cancelled_partial"
                        if cancel_data and filled_leg_qty
                        else (
                            "cancelled_unfilled"
                            if cancel_data
                            else (
                                "partial_fill" if filled_leg_qty else "submitted_open"
                            )
                        )
                    )
                ),
                "cancel_reason": cancel_data.get("cancel_reason"),
                "cancel_response": cancel_data.get("cancel_response"),
                "broker_route": row_data.get("broker_route"),
            }
        )
    residual_leg_state_complete = bool(residual_legs) and all(
        leg.get("terminal_state")
        in {"filled", "cancelled_partial", "cancelled_unfilled"}
        for leg in residual_legs
    )
    if policy_mode == "one_share_exploration":
        residual = _component("policy_forbidden", residual_event, legs=residual_legs)
    elif residual_stage in {"bundle_completed", "residual_partial_complete"}:
        residual = _component(
            (
                "terminal_submitted"
                if residual_leg_state_complete
                else "terminal_submitted_incomplete_leg_state"
            ),
            residual_event,
            legs=residual_legs,
        )
    elif residual_stage == "residual_blocked" and (
        _text(residual_data.get("entry_split_probe_terminal_outcome"))
        or _integer(residual_data.get("residual_submitted_qty"))
    ):
        residual = _component(
            (
                (
                    "terminal_submitted"
                    if residual_leg_state_complete
                    else "terminal_submitted_incomplete_leg_state"
                )
                if _integer(residual_data.get("residual_submitted_qty"))
                else "terminal_not_submitted"
            ),
            residual_event,
            legs=residual_legs,
        )
    else:
        residual = _component("not_evaluated", residual_event, legs=residual_legs)

    scale_events = [
        row for row in events if "scale_in" in (row.get("components") or [])
    ]
    scale_executed = _last_event(events, {"scale_in_executed"})
    scale_event = scale_executed or (scale_events[-1] if scale_events else None)
    scale_stage = _text(scale_event.get("stage")) if scale_event else ""
    scale_data = dict(scale_event.get("data") or {}) if scale_event else {}
    if policy_mode == "one_share_exploration":
        scale_in = _component("policy_forbidden", scale_event)
    elif scale_executed is not None:
        scale_in = _component("evaluated_submitted", scale_event)
    elif scale_event and (
        scale_stage
        in {
            "stat_action_decision_snapshot",
            "pyramid_blocked_reason",
            "scale_in_arm_blocked",
        }
        and (
            "scale_in_gate_allowed" in scale_data
            or _text(scale_data.get("scale_in_blocker_reason"))
        )
    ):
        scale_in = _component("evaluated_not_submitted", scale_event)
    else:
        scale_in = _component("not_evaluated", scale_event)

    holding_started = _last_event(events, {"holding_started"})
    exit_signal = _last_event(events, {"exit_signal"})
    sell_completed = _last_event(events, {"sell_completed"})
    sell_data = dict(sell_completed.get("data") or {}) if sell_completed else {}
    if sell_completed and _number(sell_data.get("sell_price")) is not None:
        holding_exit = _component(
            "terminal_exit_filled",
            sell_completed,
            holding_started_at=(
                holding_started.get("observed_at") if holding_started else None
            ),
            exit_signal_at=exit_signal.get("observed_at") if exit_signal else None,
        )
    elif holding_started:
        holding_exit = _component("holding_open", holding_started)
    else:
        holding_exit = _component("not_observed", None)

    buy_price = _number(sell_data.get("buy_price"))
    buy_qty = _integer(sell_data.get("buy_qty") or sell_data.get("sell_qty"))
    sell_price = _number(sell_data.get("sell_price"))
    realized_pnl = _number(sell_data.get("realized_pnl_krw"))
    cost_rate = _number(sell_data.get("fee_tax_cost_rate"))
    if cost_rate is None:
        cost_rate = float(get_trade_cost_rate())
    exit_notional = sell_price * buy_qty if sell_price and buy_qty else None
    combined_cost = exit_notional * cost_rate if exit_notional is not None else None
    economics_complete = bool(
        buy_price and buy_qty and sell_price and realized_pnl is not None
    )
    economics = _component(
        "complete" if economics_complete else "not_evaluated",
        sell_completed,
        entry_notional_krw=(buy_price * buy_qty if buy_price and buy_qty else None),
        exit_notional_krw=exit_notional,
        realized_pnl_krw=realized_pnl,
        fee_tax_cost_rate=cost_rate,
        estimated_combined_fee_tax_cost_krw=combined_cost,
        fee_tax_basis="configured_combined_sell_side_cost_rate",
        broker_fee_krw=None,
        transaction_tax_krw=None,
        fee_tax_exact_breakdown_available=False,
        probe_fill_slippage_bps=(
            _number((probe_filled.get("data") or {}).get("probe_fill_slippage_bps"))
            if probe_filled
            else None
        ),
        residual_leg_fill_slippage_bps=[
            leg.get("fill_slippage_bps")
            for leg in residual_legs
            if leg.get("fill_slippage_bps") is not None
        ],
    )

    components = {
        "probe": probe,
        "post_probe": post_probe,
        "residual_multi_leg": residual,
        "scale_in": scale_in,
        "holding_exit": holding_exit,
        "economics": economics,
    }
    incomplete = [
        name
        for name, component in components.items()
        if component.get("status") not in _COMPONENT_COMPLETE_STATUSES[name]
    ]
    blockers = []
    if route_conflict:
        blockers.append("venue_or_session_conflict")
    if identity_conflict:
        blockers.append("candidate_identity_conflict")
    if not pair_identity_valid:
        blockers.append("paired_replay_identity_mismatch")
    if not event_contract_valid:
        blockers.append("event_authority_contract_invalid")
    blockers.extend(f"{name}:{components[name].get('status')}" for name in incomplete)
    source_quality_status = "pass" if not blockers else "blocked"
    ids = {
        "probe_bundle_ids": sorted(
            {
                _text(row.get("probe_bundle_id"))
                for row in events
                if row.get("probe_bundle_id")
            }
        ),
        "position_cycle_ids": sorted(
            {
                _text(row.get("position_cycle_id"))
                for row in events
                if row.get("position_cycle_id")
            }
        ),
        "broker_order_nos": sorted(
            {
                _text(row.get("broker_order_no"))
                for row in events
                if row.get("broker_order_no")
            }
        ),
    }
    return {
        "schema": STATE_SCHEMA,
        "decision_trace_id": first.get("decision_trace_id"),
        "payload_sha256": first.get("payload_sha256"),
        "paired_replay_id": first.get("paired_replay_id"),
        "effective_venue": first.get("effective_venue"),
        "session_bucket": first.get("session_bucket"),
        "stock_code": first.get("stock_code"),
        "record_id": first.get("record_id"),
        "policy_mode": policy_mode,
        "lifecycle_basis": first.get("lifecycle_basis") or "observed_live_candidate",
        "first_observed_at": first.get("observed_at"),
        "last_observed_at": events[-1].get("observed_at"),
        "event_count": len(events),
        "source_quality_status": source_quality_status,
        "source_quality_blockers": blockers,
        "route_conflict": route_conflict,
        **ids,
        **components,
        **OBSERVATION_CONTRACT,
    }


def materialize_candidate_states(
    target_date: str,
    *,
    source_path: Path | None = None,
    output_path: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Materialize exact candidate-owned states from the small transition ledger."""

    source = source_path or event_path(target_date)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_count = 0
    for row in _read_events(source):
        event_count += 1
        pair_id = _text(row.get("paired_replay_id"))
        if pair_id:
            groups[pair_id].append(row)
    states = [_materialize_one(rows) for rows in groups.values() if rows]
    states.sort(
        key=lambda row: (
            _text(row.get("effective_venue")),
            _text(row.get("session_bucket")),
            _text(row.get("decision_trace_id")),
        )
    )
    report = {
        "schema": REPORT_SCHEMA,
        "target_date": target_date,
        "generated_at": _now().isoformat(),
        "source_event_path": str(source),
        "source_event_count": event_count,
        "candidate_state_count": len(states),
        "source_quality_pass_count": sum(
            row.get("source_quality_status") == "pass" for row in states
        ),
        "full_lifecycle_evaluable_candidate_count": sum(
            row.get("source_quality_status") == "pass" for row in states
        ),
        "states": states,
        **OBSERVATION_CONTRACT,
    }
    if write:
        _atomic_write_json(output_path or report_path(target_date), report)
    return report


def load_candidate_state_index(
    target_date: str,
    *,
    materialize: bool = True,
    write: bool = True,
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    path = report_path(target_date)
    payload: dict[str, Any] = {}
    if materialize and event_path(target_date).exists():
        payload = materialize_candidate_states(target_date, write=write)
    elif path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            payload = loaded if isinstance(loaded, dict) else {}
        except (OSError, json.JSONDecodeError):
            payload = {}
    index: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for state in payload.get("states") or []:
        if not isinstance(state, dict):
            continue
        key = (
            _text(state.get("decision_trace_id")),
            _text(state.get("paired_replay_id")),
            _upper(state.get("effective_venue")),
            _text(state.get("session_bucket")).lower(),
        )
        if all(key):
            index[key] = state
    return index


def component_is_complete(name: str, component: Any) -> bool:
    return bool(
        isinstance(component, dict)
        and component.get("status") in _COMPONENT_COMPLETE_STATUSES.get(name, set())
    )


__all__ = [
    "CONTEXT_KEY",
    "EVENT_SCHEMA",
    "OBSERVATION_CONTRACT",
    "REPORT_SCHEMA",
    "STATE_SCHEMA",
    "bind_candidate_context",
    "component_is_complete",
    "event_path",
    "load_candidate_state_index",
    "materialize_candidate_states",
    "observe_candidate_transition",
    "observe_candidate_transition_safe",
    "paired_replay_id",
    "report_path",
]
