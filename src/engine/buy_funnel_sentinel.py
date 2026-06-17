"""Intraday BUY funnel bottleneck sentinel.

This module is report-only. It reads structured pipeline events, classifies
BUY/submitted drought causes, and writes artifacts. It never mutates runtime
strategy thresholds.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day
from src.engine.pipeline_event_summary import (
    SUMMARY_SCHEMA_VERSION,
    SUMMARY_STAGES,
    default_reason_label,
    update_and_load_pipeline_event_summaries,
)
from src.engine.sentinel_event_cache import update_and_load_cached_event_rows
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


MANUAL_EXCLUDED_STOCKS = {
    ("제룡전기", "033100"),
}
IGNORED_STOCK_NAMES = {"TEST", "DUMMY", "MOCK"}
ENTRY_STAGES = {
    "ai_confirmed",
    "entry_armed",
    "budget_pass",
    "latency_pass",
    "order_bundle_submitted",
}
HOLDING_STAGES = {"holding_started"}
UPSTREAM_BLOCK_STAGES = {
    "blocked_ai_score",
    "ai_score_50_buy_hold_override",
    "wait65_79_ev_candidate",
    "first_ai_wait",
}
PRICE_GUARD_STAGES = {
    "pre_submit_price_guard_block",
    "entry_ai_price_canary_skip_order",
    "entry_ai_price_canary_fallback",
    "scale_in_price_guard_block",
}
POST_LATENCY_SUBMIT_BLOCK_STAGES = {
    "budget_pass",
    "pre_submit_price_guard_block",
    "entry_ai_price_canary_skip_order",
    "entry_ai_price_canary_fallback",
    "scale_in_price_guard_block",
    "order_bundle_submitted",
    "broker_submit_failed",
    "buy_order_failed",
    "submit_order_failed",
    "entry_armed_expired",
    "entry_armed_expired_after_wait",
    "entry_arm_expired",
}
BLOCKER_STAGE_PREFIXES = ("blocked_",)
BLOCKER_STAGES = {
    "latency_block",
    "entry_armed_expired",
    "entry_armed_expired_after_wait",
    "entry_arm_expired",
    *UPSTREAM_BLOCK_STAGES,
    *PRICE_GUARD_STAGES,
}
DEFAULT_WINDOWS = (5, 10, 30)
SESSION_START = time(9, 0)
SENTINEL_END = time(15, 20)
SUBMIT_DROUGHT_MIN_AI_UNIQUE = 20
SUBMIT_DROUGHT_MIN_BUDGET_UNIQUE = 3
SUBMIT_TO_AI_CRITICAL_PCT = 20.0
SUBMIT_TO_BUDGET_CRITICAL_PCT = 10.0
REPORT_DIRNAME = "buy_funnel_sentinel"
EVENT_CACHE_SCHEMA_VERSION = 3
LOSSLESS_EVENT_CACHE_SCHEMA_VERSION = 5
EVENT_CACHE_NAME = "buy_funnel_sentinel_events"
FORBIDDEN_AUTOMATIONS = [
    "score_threshold_relaxation",
    "spread_cap_relaxation",
    "fallback_reenable",
    "live_threshold_runtime_mutation",
    "bot_restart",
]
PRE_SUBMIT_REFRESH_NOOP_REASONS = {
    "",
    "not_attempted",
    "quote_not_stale",
    "observer_quote_fresh",
    "latest_ws_snapshot_fresh",
    "latest_snapshot_fresh",
}


@dataclass(frozen=True)
class PipelineEvent:
    emitted_at: datetime
    pipeline: str
    stage: str
    stock_name: str
    stock_code: str
    record_id: str
    fields: dict[str, str]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _event_cache_dir() -> Path:
    return DATA_DIR / "runtime" / "sentinel_event_cache"


def _event_summary_dir() -> Path:
    return DATA_DIR / "pipeline_event_summaries"


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _parse_iso_datetime(value: str) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _parse_target_date(target_date: str) -> date:
    return datetime.strptime(target_date, "%Y-%m-%d").date()


def _parse_as_of(target_date: str, as_of: str | None) -> datetime | None:
    text = _safe_str(as_of)
    if not text:
        return None
    parsed = _parse_iso_datetime(text)
    if parsed is not None:
        return parsed
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(f"{target_date} {text}", f"%Y-%m-%d {fmt}")
        except ValueError:
            continue
    raise ValueError(f"invalid --as-of value: {as_of}")


def _is_ignored_event(payload: dict[str, Any]) -> bool:
    name = _safe_str(payload.get("stock_name"))
    code = _safe_str(payload.get("stock_code"))[:6]
    if (name, code) in MANUAL_EXCLUDED_STOCKS:
        return True
    if name.upper() in IGNORED_STOCK_NAMES:
        return True
    return False


def _is_truthy_text(value: Any) -> bool:
    return _safe_str(value).lower() in {"1", "true", "t", "yes", "y"}


def _contains_text_token(value: Any, token: str) -> bool:
    if isinstance(value, dict):
        return any(token in str(key) or _contains_text_token(item, token) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_token(item, token) for item in value)
    return token in _safe_str(value)


def _is_early_accel_recheck_retry_fields(fields: dict[str, Any]) -> bool:
    return (
        _safe_str(fields.get("ai_call_trigger_reason")) == "early_accel_recheck"
        or _safe_str(fields.get("tuning_authority_excluded_reason"))
        == "early_accel_recheck_operator_retry"
    )


def _payload_requires_lossless_cache(payload: dict[str, Any], fields: dict[str, Any]) -> bool:
    for key in ("actual_order_submitted", "broker_order_submitted", "order_submitted"):
        if _is_truthy_text(payload.get(key)) or _is_truthy_text(fields.get(key)):
            return True
    for key in fields:
        lowered = str(key).lower()
        if "source_quality" in lowered or "provenance" in lowered:
            return True
    return False


def _payload_to_cache_row(
    payload: dict[str, Any],
    *,
    exclude_summary_stages: bool = False,
) -> dict[str, Any] | None:
    if _safe_str(payload.get("event_type")) != "pipeline_event":
        return None
    if _is_ignored_event(payload):
        return None
    stage = _safe_str(payload.get("stage"))
    raw_fields = payload.get("fields") or {}
    raw_field_dict = raw_fields if isinstance(raw_fields, dict) else {}
    if _is_early_accel_recheck_retry_fields(raw_field_dict):
        return None
    if exclude_summary_stages and stage in SUMMARY_STAGES and not _payload_requires_lossless_cache(payload, raw_field_dict):
        return None
    if not (
        stage in ENTRY_STAGES
        or stage in HOLDING_STAGES
        or stage in BLOCKER_STAGES
        or stage in UPSTREAM_BLOCK_STAGES
        or stage in PRICE_GUARD_STAGES
        or stage.startswith(BLOCKER_STAGE_PREFIXES)
        or _contains_text_token(raw_field_dict, "ai_score_50_buy_hold_override")
    ):
        return None
    emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
    if emitted_at is None:
        return None
    fields = {str(k): _safe_str(v) for k, v in raw_fields.items()}
    record_id = payload.get("record_id")
    if record_id in (None, "", 0):
        record_id = fields.get("id") or ""
    return {
        "emitted_at": emitted_at.isoformat(),
        "pipeline": _safe_str(payload.get("pipeline")),
        "stage": stage,
        "stock_name": _safe_str(payload.get("stock_name")),
        "stock_code": _safe_str(payload.get("stock_code"))[:6],
        "record_id": _safe_str(record_id),
        "fields": fields,
    }


def _blocker_label_from_stage_fields(stage: str, fields: dict[str, str]) -> str:
    return default_reason_label(stage, fields)


def _is_early_accel_recheck_retry_event(event: PipelineEvent) -> bool:
    return _is_early_accel_recheck_retry_fields(event.fields)


def _is_swing_blocker_label(label: str) -> bool:
    return _safe_str(label).startswith("blocked_swing_")


def _event_from_cache_row(row: dict[str, Any]) -> PipelineEvent | None:
    emitted_at = _parse_iso_datetime(_safe_str(row.get("emitted_at")))
    if emitted_at is None:
        return None
    raw_fields = row.get("fields") or {}
    fields = {str(k): _safe_str(v) for k, v in raw_fields.items()} if isinstance(raw_fields, dict) else {}
    return PipelineEvent(
        emitted_at=emitted_at,
        pipeline=_safe_str(row.get("pipeline")),
        stage=_safe_str(row.get("stage")),
        stock_name=_safe_str(row.get("stock_name")),
        stock_code=_safe_str(row.get("stock_code"))[:6],
        record_id=_safe_str(row.get("record_id")),
        fields=fields,
    )


def load_pipeline_events(
    target_date: str,
    *,
    use_cache: bool = False,
    exclude_summary_stages: bool = False,
) -> list[PipelineEvent]:
    path = existing_or_gzip_path(_pipeline_events_path(target_date))
    if not path.exists():
        return []
    if use_cache:
        cache_schema_version = (
            LOSSLESS_EVENT_CACHE_SCHEMA_VERSION if exclude_summary_stages else EVENT_CACHE_SCHEMA_VERSION
        )
        rows, _ = update_and_load_cached_event_rows(
            raw_path=path,
            cache_dir=_event_cache_dir(),
            cache_name=EVENT_CACHE_NAME,
            target_date=target_date,
            schema_version=cache_schema_version,
            parse_payload=lambda payload: _payload_to_cache_row(
                payload,
                exclude_summary_stages=exclude_summary_stages,
            ),
        )
        events = [event for row in rows if (event := _event_from_cache_row(row)) is not None]
        events.sort(key=lambda event: event.emitted_at)
        return events

    events: list[PipelineEvent] = []
    for payload in iter_jsonl(path):
        if _safe_str(payload.get("event_type")) != "pipeline_event":
            continue
        if _is_ignored_event(payload):
            continue
        emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
        if emitted_at is None:
            continue
        raw_fields = payload.get("fields") or {}
        raw_field_dict = raw_fields if isinstance(raw_fields, dict) else {}
        if (
            exclude_summary_stages
            and _safe_str(payload.get("stage")) in SUMMARY_STAGES
            and not _payload_requires_lossless_cache(payload, raw_field_dict)
        ):
            continue
        fields = {str(k): _safe_str(v) for k, v in raw_fields.items()}
        record_id = payload.get("record_id")
        if record_id in (None, "", 0):
            record_id = fields.get("id") or ""
        events.append(
            PipelineEvent(
                emitted_at=emitted_at,
                pipeline=_safe_str(payload.get("pipeline")),
                stage=_safe_str(payload.get("stage")),
                stock_name=_safe_str(payload.get("stock_name")),
                stock_code=_safe_str(payload.get("stock_code"))[:6],
                record_id=_safe_str(record_id),
                fields=fields,
            )
        )
    events.sort(key=lambda event: event.emitted_at)
    return events


def load_pipeline_event_summaries(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return update_and_load_pipeline_event_summaries(
        raw_path=_pipeline_events_path(target_date),
        summary_dir=_event_summary_dir(),
        target_date=target_date,
        reason_labeler=_blocker_label_from_stage_fields,
        ignore_payload=_is_ignored_event,
        include_samples=False,
    )


def _load_event_sources(
    target_date: str,
    *,
    use_cache: bool,
    use_summary: bool,
) -> tuple[list[PipelineEvent], list[dict[str, Any]], dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    summary_meta: dict[str, Any] = {
        "enabled": bool(use_summary),
        "status": "disabled",
        "raw_suppression_enabled": False,
    }
    exclude_summary_stages = False
    if use_summary:
        loaded_summary_rows, loaded_summary_meta = load_pipeline_event_summaries(target_date)
        summary_meta = loaded_summary_meta
        if loaded_summary_meta.get("status") == "ok":
            summary_rows = loaded_summary_rows
            exclude_summary_stages = True

    events = load_pipeline_events(
        target_date,
        use_cache=use_cache,
        exclude_summary_stages=exclude_summary_stages,
    )
    return events, summary_rows, {
        "cache_enabled": bool(use_cache),
        "cache_name": EVENT_CACHE_NAME if use_cache else None,
        "cache_schema_version": (
            LOSSLESS_EVENT_CACHE_SCHEMA_VERSION if exclude_summary_stages and use_cache else EVENT_CACHE_SCHEMA_VERSION
        )
        if use_cache
        else None,
        "summary_enabled": bool(use_summary),
        "summary_status": summary_meta.get("status"),
        "summary_schema_version": SUMMARY_SCHEMA_VERSION if use_summary else None,
        "summary_target_stages": sorted(SUMMARY_STAGES) if use_summary else [],
        "summary_row_count": summary_meta.get("summary_row_count"),
        "summary_appended_source_events": summary_meta.get("appended_source_events"),
        "summary_appended_rows": summary_meta.get("appended_summary_rows"),
        "summary_rebuilt": summary_meta.get("rebuilt"),
        "summary_path": summary_meta.get("summary_path"),
        "summary_manifest_raw_offset": summary_meta.get("raw_offset"),
        "summary_manifest_raw_size": summary_meta.get("raw_size"),
        "summary_raw_suppression_enabled": bool(summary_meta.get("raw_suppression_enabled", False)),
        "summary_lossless_cache_excludes_summary_stages": bool(exclude_summary_stages),
        "fallback_to_raw_cache": bool(use_summary and not exclude_summary_stages),
    }


def previous_trading_day_with_events(target_date: str, *, max_lookback_days: int = 10) -> str | None:
    current = _parse_target_date(target_date)
    for offset in range(1, max_lookback_days + 1):
        candidate = current - timedelta(days=offset)
        if not is_krx_trading_day(candidate):
            continue
        candidate_text = candidate.isoformat()
        if existing_or_gzip_path(_pipeline_events_path(candidate_text)).exists():
            return candidate_text
    return None


def _attempt_key(event: PipelineEvent) -> str:
    if event.record_id:
        return f"id:{event.record_id}"
    if event.stock_code:
        return f"code:{event.stock_code}"
    return f"name:{event.stock_name}"


def _is_blocker_stage(stage: str) -> bool:
    return stage in BLOCKER_STAGES or stage.startswith(BLOCKER_STAGE_PREFIXES)


def _field_first(fields: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = _safe_str(fields.get(name))
        if value:
            return value
    return ""


def _blocker_label(event: PipelineEvent) -> str:
    fields = event.fields
    if event.stage == "blocked_ai_score":
        score = _field_first(fields, ("score", "ai_score", "current_ai_score"))
        reason = _field_first(fields, ("reason", "block_reason", "blocked_reason", "decision"))
        if "ai_score_50_buy_hold_override" in reason or fields.get("ai_score_50_buy_hold_override") == "True":
            return "blocked_ai_score:ai_score_50_buy_hold_override"
        if score:
            return f"blocked_ai_score:score_{score}"
    if event.stage == "latency_block":
        reason = _field_first(fields, ("reason", "latency_danger_reasons", "decision"))
        return f"latency_block:{reason or '-'}"
    if event.stage in PRICE_GUARD_STAGES:
        reason = _field_first(fields, ("reason", "block_reason", "resolution_reason", "action"))
        return f"{event.stage}:{reason or '-'}"
    if event.stage == "wait65_79_ev_candidate":
        score = _field_first(fields, ("ai_score", "score", "current_ai_score"))
        return f"wait65_79_ev_candidate:score_{score or '-'}"
    reason = _field_first(fields, ("reason", "block_reason", "decision", "action"))
    return f"{event.stage}:{reason or '-'}"


def _post_refresh_downstream_bucket(event: PipelineEvent | None) -> str:
    if event is None:
        return "no_downstream_event"
    stage = event.stage
    label = _blocker_label(event).lower()
    if stage == "order_bundle_submitted":
        return "order_bundle_submitted"
    if stage in PRICE_GUARD_STAGES or "price" in label or "slippage" in label or "gap" in label:
        return "price_guard_or_revalidation"
    if stage in {"entry_armed_expired", "entry_armed_expired_after_wait", "entry_arm_expired"}:
        return "armed_expired_before_submit"
    if stage == "budget_pass":
        return "budget_pass_no_submit_event"
    if any(token in label for token in ("broker", "account", "order", "cooldown", "budget", "deposit", "cash")):
        return "broker_account_order_budget_cooldown"
    if stage.startswith(BLOCKER_STAGE_PREFIXES):
        return "upstream_block_after_latency_recovery"
    return f"other:{stage}"


def _ratio(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator else 0.0


def _count_unique(events: list[PipelineEvent], stage: str) -> int:
    return len({_attempt_key(event) for event in events if event.stage == stage})


def _summary_row_count_in_range(row: dict[str, Any], *, start_at: datetime, end_at: datetime) -> tuple[int, datetime | None]:
    second_counts = row.get("second_counts")
    count = 0
    latest: datetime | None = None
    if isinstance(second_counts, dict) and second_counts:
        for second_text, raw_count in second_counts.items():
            parsed = _parse_iso_datetime(_safe_str(second_text))
            if parsed is None or parsed < start_at or parsed > end_at:
                continue
            if end_at.microsecond == 0 and parsed == end_at.replace(microsecond=0):
                continue
            try:
                second_count = int(raw_count)
            except (TypeError, ValueError):
                continue
            count += second_count
            if latest is None or parsed > latest:
                latest = parsed
        return count, latest

    first_seen = _parse_iso_datetime(_safe_str(row.get("first_seen")))
    last_seen = _parse_iso_datetime(_safe_str(row.get("last_seen")))
    if first_seen is None or last_seen is None or last_seen < start_at or first_seen > end_at:
        return 0, None
    try:
        return int(row.get("event_count") or 0), min(last_seen, end_at)
    except (TypeError, ValueError):
        return 0, None


def _summarize_events(
    events: list[PipelineEvent],
    *,
    start_at: datetime,
    end_at: datetime,
    summary_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    scoped = [
        event
        for event in events
        if start_at <= event.emitted_at <= end_at and not _is_early_accel_recheck_retry_event(event)
    ]
    has_summary_rows = bool(summary_rows)
    lossless_scoped = [
        event for event in scoped if not (has_summary_rows and event.stage in SUMMARY_STAGES)
    ]
    stage_event_counts = Counter(event.stage for event in lossless_scoped)
    summary_event_count = 0
    summary_latest_candidates: list[datetime] = []
    summary_blocker_counter: Counter[str] = Counter()
    summary_swing_blocker_counter: Counter[str] = Counter()
    for row in summary_rows or []:
        count, latest = _summary_row_count_in_range(row, start_at=start_at, end_at=end_at)
        if count <= 0:
            continue
        stage = _safe_str(row.get("stage"))
        label = _safe_str(row.get("reason_label")) or f"{stage}:-"
        stage_event_counts[stage] += count
        summary_event_count += count
        if latest is not None:
            summary_latest_candidates.append(latest)
        if _is_blocker_stage(stage):
            if _is_swing_blocker_label(label):
                summary_swing_blocker_counter[label] += count
            else:
                summary_blocker_counter[label] += count
    stage_unique_counts = {
        stage: len({_attempt_key(event) for event in lossless_scoped if event.stage == stage})
        for stage in sorted(set(stage_event_counts) | ENTRY_STAGES | HOLDING_STAGES)
    }
    raw_blocker_labels = [_blocker_label(event) for event in lossless_scoped if _is_blocker_stage(event.stage)]
    blocker_counter = Counter(label for label in raw_blocker_labels if not _is_swing_blocker_label(label))
    blocker_counter.update(summary_blocker_counter)
    swing_blocker_counter = Counter(label for label in raw_blocker_labels if _is_swing_blocker_label(label))
    swing_blocker_counter.update(summary_swing_blocker_counter)
    upstream_events = [
        event
        for event in lossless_scoped
        if event.stage in UPSTREAM_BLOCK_STAGES
        or _contains_text_token(event.fields, "ai_score_50_buy_hold_override")
    ]
    price_guard_events = [event for event in lossless_scoped if event.stage in PRICE_GUARD_STAGES]
    latency_blocks = [
        event
        for event in lossless_scoped
        if event.stage == "latency_block"
        and (
            _field_first(event.fields, ("reason", "latency_danger_reasons", "decision"))
            in {"latency_state_danger", "REJECT_DANGER"}
            or _contains_text_token(event.fields, "latency_state_danger")
        )
    ]
    upstream_counter = Counter(_blocker_label(event) for event in upstream_events)
    latency_counter = Counter(_blocker_label(event) for event in latency_blocks)
    price_guard_counter = Counter(_blocker_label(event) for event in price_guard_events)
    latency_danger_reason_counts = Counter(
        label
        for event in latency_blocks
        for label in _latency_danger_reason_labels(event)
    )
    refresh_scope_events = [
        event
        for event in lossless_scoped
        if event.stage in {"latency_block", "latency_pass", "order_bundle_submitted"}
    ]
    refresh_attempt_keys = {_attempt_key(event) for event in refresh_scope_events if _event_refresh_attempted(event)}
    refresh_applied_keys = {_attempt_key(event) for event in refresh_scope_events if _event_refresh_applied(event)}
    refresh_blocked_after_attempt_keys = {
        _attempt_key(event)
        for event in refresh_scope_events
        if event.stage == "latency_block" and _event_refresh_attempted(event) and not _event_refresh_applied(event)
    }
    refresh_latency_pass_count = len(
        {
            _attempt_key(event)
            for event in refresh_scope_events
            if event.stage == "latency_pass" and _event_refresh_applied(event)
        }
    )
    refresh_latency_pass_keys = {
        _attempt_key(event)
        for event in refresh_scope_events
        if event.stage == "latency_pass" and _event_refresh_applied(event)
    }
    refresh_order_bundle_submitted_count = len(
        {
            _attempt_key(event)
            for event in refresh_scope_events
            if event.stage == "order_bundle_submitted" and _event_refresh_applied(event)
        }
    )
    events_by_key: dict[str, list[PipelineEvent]] = {}
    for event in lossless_scoped:
        events_by_key.setdefault(_attempt_key(event), []).append(event)
    post_refresh_downstream_counter: Counter[str] = Counter()
    post_refresh_downstream_stage_counter: Counter[str] = Counter()
    for key in refresh_latency_pass_keys:
        events_for_key = events_by_key.get(key) or []
        latency_pass_events = [
            event
            for event in events_for_key
            if event.stage == "latency_pass" and _event_refresh_applied(event)
        ]
        if not latency_pass_events:
            post_refresh_downstream_counter["no_latency_pass_event"] += 1
            continue
        first_latency_pass = min(latency_pass_events, key=lambda item: item.emitted_at)
        next_event = None
        for event in sorted(events_for_key, key=lambda item: item.emitted_at):
            if event.emitted_at <= first_latency_pass.emitted_at:
                continue
            if event.stage in POST_LATENCY_SUBMIT_BLOCK_STAGES or (
                _is_blocker_stage(event.stage) and event.stage != "latency_block"
            ):
                next_event = event
                break
        bucket = _post_refresh_downstream_bucket(next_event)
        post_refresh_downstream_counter[bucket] += 1
        if next_event is not None:
            post_refresh_downstream_stage_counter[next_event.stage] += 1
    ai_unique = stage_unique_counts.get("ai_confirmed", 0)
    budget_unique = stage_unique_counts.get("budget_pass", 0)
    latency_unique = stage_unique_counts.get("latency_pass", 0)
    submitted_unique = stage_unique_counts.get("order_bundle_submitted", 0)
    latest_candidates = [lossless_scoped[-1].emitted_at] if lossless_scoped else []
    latest_candidates.extend(summary_latest_candidates)
    latest_event_at = max(latest_candidates).isoformat(timespec="seconds") if latest_candidates else None

    return {
        "start_at": start_at.isoformat(timespec="seconds"),
        "end_at": end_at.isoformat(timespec="seconds"),
        "event_count": len(lossless_scoped) + summary_event_count,
        "lossless_event_count": len(lossless_scoped),
        "summary_event_count": summary_event_count,
        "latest_event_at": latest_event_at,
        "stage_events": dict(sorted(stage_event_counts.items())),
        "stage_unique": stage_unique_counts,
        "blocker_top": [
            {"label": label, "count": count}
            for label, count in blocker_counter.most_common(10)
        ],
        "swing_blocker_top": [
            {"label": label, "count": count}
            for label, count in swing_blocker_counter.most_common(10)
        ],
        "upstream_blocker_top": [
            {"label": label, "count": count}
            for label, count in upstream_counter.most_common(10)
        ],
        "latency_blocker_top": [
            {"label": label, "count": count}
            for label, count in latency_counter.most_common(10)
        ],
        "latency_danger_reason_top": [
            {"label": label, "count": count}
            for label, count in latency_danger_reason_counts.most_common(10)
        ],
        "latency_danger_reason_counts": dict(sorted(latency_danger_reason_counts.items())),
        "price_guard_top": [
            {"label": label, "count": count}
            for label, count in price_guard_counter.most_common(10)
        ],
        "upstream_block_events": len(upstream_events),
        "latency_state_danger_events": len(latency_blocks),
        "price_guard_events": len(price_guard_events),
        "quote_freshness_refresh_attempted_count": len(refresh_attempt_keys),
        "quote_freshness_refresh_applied_count": len(refresh_applied_keys),
        "quote_freshness_still_latency_blocked_after_refresh_count": len(refresh_blocked_after_attempt_keys),
        "quote_freshness_refresh_latency_pass_count": refresh_latency_pass_count,
        "quote_freshness_refresh_order_bundle_submitted_count": refresh_order_bundle_submitted_count,
        "quote_freshness_recovered_downstream_counts": dict(sorted(post_refresh_downstream_counter.items())),
        "quote_freshness_recovered_downstream_stage_counts": dict(
            sorted(post_refresh_downstream_stage_counter.items())
        ),
        "ratios": {
            "budget_to_ai_unique_pct": _ratio(budget_unique, ai_unique),
            "latency_to_budget_unique_pct": _ratio(latency_unique, budget_unique),
            "submitted_to_budget_unique_pct": _ratio(submitted_unique, budget_unique),
            "submitted_to_ai_unique_pct": _ratio(submitted_unique, ai_unique),
        },
        "unique_symbols": {
            "ai_confirmed": _count_unique(lossless_scoped, "ai_confirmed"),
            "entry_armed": _count_unique(lossless_scoped, "entry_armed"),
            "budget_pass": _count_unique(lossless_scoped, "budget_pass"),
            "latency_pass": _count_unique(lossless_scoped, "latency_pass"),
            "order_bundle_submitted": _count_unique(lossless_scoped, "order_bundle_submitted"),
            "holding_started": _count_unique(lossless_scoped, "holding_started"),
        },
    }


def _same_time_on_date(target_date: str, source: datetime) -> datetime:
    base = _parse_target_date(target_date)
    return datetime.combine(base, source.time())


def _event_refresh_attempted(event: PipelineEvent) -> bool:
    for prefix in ("pre_submit_ws_snapshot_refresh", "pre_submit_quote_refresh"):
        reason = _safe_str(event.fields.get(f"{prefix}_reason")).lower()
        if _event_refresh_applied(event) or reason not in PRE_SUBMIT_REFRESH_NOOP_REASONS:
            return True
    return False


def _event_refresh_applied(event: PipelineEvent) -> bool:
    return (
        _is_truthy_text(event.fields.get("pre_submit_quote_refresh_applied"))
        or _is_truthy_text(event.fields.get("pre_submit_ws_snapshot_refresh_applied"))
    )


def _latency_danger_reason_labels(event: PipelineEvent) -> list[str]:
    raw = _safe_str(event.fields.get("latency_danger_reasons"))
    labels = [
        label.strip()
        for label in raw.replace(";", ",").split(",")
        if label.strip()
    ]
    if _safe_str(event.fields.get("quote_stale")).lower() == "true":
        labels.append("quote_stale")
    observer_reason = _safe_str(event.fields.get("orderbook_micro_observer_missing_reason"))
    if observer_reason and observer_reason not in {"ok", "-", "None"}:
        labels.append(f"observer_{observer_reason}")
    refresh_reason = _safe_str(event.fields.get("pre_submit_quote_refresh_reason")).lower()
    if refresh_reason and refresh_reason not in PRE_SUBMIT_REFRESH_NOOP_REASONS:
        labels.append(f"pre_submit_quote_refresh_{refresh_reason}")
    ws_refresh_reason = _safe_str(event.fields.get("pre_submit_ws_snapshot_refresh_reason")).lower()
    if ws_refresh_reason and ws_refresh_reason not in PRE_SUBMIT_REFRESH_NOOP_REASONS:
        labels.append(f"pre_submit_ws_snapshot_refresh_{ws_refresh_reason}")
    return labels or [_blocker_label(event)]


def _refresh_reason_bucket(label: str) -> str | None:
    text = label.lower()
    if text.startswith("pre_submit_ws_snapshot_refresh_"):
        reason = text.removeprefix("pre_submit_ws_snapshot_refresh_")
        if reason in {"latest_ws_snapshot_fresh", "applied"}:
            return "ws_snapshot_refresh_applied"
        if "stale" in reason or "older_than_input" in reason:
            return "ws_snapshot_refresh_failed_stale"
        if "missing" in reason or "ws_manager_missing" in reason:
            return "ws_snapshot_refresh_failed_missing"
        if "invalid" in reason:
            return "ws_snapshot_refresh_failed_invalid"
        if "non_scalping" in reason or "disabled" in reason:
            return "refresh_disabled_or_alias_gap"
        return f"ws_snapshot_refresh_failed_{reason}"
    if text.startswith("pre_submit_quote_refresh_"):
        reason = text.removeprefix("pre_submit_quote_refresh_")
        if reason in {"observer_quote_fresh", "applied"}:
            return "observer_quote_refresh_applied"
        if "stale" in reason:
            return "observer_quote_refresh_failed_stale"
        if "missing" in reason:
            return "observer_quote_refresh_failed_missing"
        if "invalid" in reason:
            return "observer_quote_refresh_failed_invalid"
        if "spread" in reason:
            return "observer_quote_refresh_failed_spread"
        if "disabled" in reason:
            return "refresh_disabled_or_alias_gap"
        return f"observer_quote_refresh_failed_{reason}"
    if "refresh" in text and "disabled" in text:
        return "refresh_disabled_or_alias_gap"
    return None


def _latency_root_cause_bucket(label: str) -> str:
    text = label.lower()
    if _refresh_reason_bucket(label) == "refresh_disabled_or_alias_gap":
        return "observer_unhealthy"
    if "ws_jitter" in text:
        return "quote_stale"
    # `other_danger` is the residual DANGER state after quote_stale/ws_age/
    # ws_jitter/spread were already ruled out by the live classifier. The
    # remaining source dimension is order RTT / transport execution health.
    if "other_danger" in text or "order_rtt" in text or "rtt" in text:
        return "order_rtt_guard"
    if "quote_stale" in text or "stale" in text or "ws_age" in text or "quote_age" in text:
        return "quote_stale"
    if (
        "observer_unhealthy" in text
        or ("observer" in text and any(token in text for token in ("unhealthy", "missing", "invalid")))
        or ("ws_snapshot" in text and any(token in text for token in ("missing", "invalid")))
    ):
        return "observer_unhealthy"
    if "missing_trade" in text:
        return "missing_trade"
    if "spread" in text or "slippage" in text:
        return "spread_or_slippage_guard"
    if "price_gap" in text or "gap" in text:
        return "price_gap_guard"
    if any(token in text for token in ("broker", "account", "order", "cooldown")):
        return "broker_account_order_cooldown"
    return "unknown_latency_reason"


def _latency_drought_root_cause_summary(current: dict[str, Any]) -> dict[str, Any]:
    buckets = Counter()
    refresh_buckets = Counter()
    reason_counts = current.get("latency_danger_reason_counts")
    if isinstance(reason_counts, dict) and reason_counts:
        label_count_items = reason_counts.items()
    else:
        labels = (
            current.get("latency_danger_reason_top")
            if isinstance(current.get("latency_danger_reason_top"), list)
            else current.get("latency_blocker_top")
        )
        labels = labels if isinstance(labels, list) else []
        label_count_items = [
            (str(item.get("label") or ""), int(item.get("count") or 0))
            for item in labels
            if isinstance(item, dict)
        ]
    for label, raw_count in label_count_items:
        count = int(raw_count or 0)
        refresh_bucket = _refresh_reason_bucket(label)
        if refresh_bucket:
            refresh_buckets[refresh_bucket] += count
        buckets[_latency_root_cause_bucket(label)] += count
    total = sum(buckets.values())
    refresh_attempted = int(
        current.get("quote_freshness_refresh_attempted_count", 0) or sum(refresh_buckets.values())
    )
    refresh_applied = int(
        current.get("quote_freshness_refresh_applied_count", 0)
        or (
            refresh_buckets.get("ws_snapshot_refresh_applied", 0)
            + refresh_buckets.get("observer_quote_refresh_applied", 0)
        )
    )
    recovered_latency_pass = int(current.get("quote_freshness_refresh_latency_pass_count", 0) or 0)
    submitted_after_refresh = int(current.get("quote_freshness_refresh_order_bundle_submitted_count", 0) or 0)
    still_blocked_after_refresh = int(
        current.get("quote_freshness_still_latency_blocked_after_refresh_count", 0)
        or max(refresh_attempted - refresh_applied, 0)
    )
    recovered_downstream_counts = (
        current.get("quote_freshness_recovered_downstream_counts")
        if isinstance(current.get("quote_freshness_recovered_downstream_counts"), dict)
        else {}
    )
    recovered_downstream_stage_counts = (
        current.get("quote_freshness_recovered_downstream_stage_counts")
        if isinstance(current.get("quote_freshness_recovered_downstream_stage_counts"), dict)
        else {}
    )
    submitted_after_refresh = max(
        submitted_after_refresh,
        int(recovered_downstream_counts.get("order_bundle_submitted", 0) or 0),
    )
    return {
        "latency_danger_event_count": int(current.get("latency_state_danger_events", 0) or 0),
        "latency_root_cause_counts": dict(buckets),
        "quote_freshness_attribution": {
            "runtime_effect": False,
            "decision_authority": "submit_drought_quote_freshness_attribution_only",
            "forbidden_uses": [
                "broker_order_submit",
                "adm_ldm_training_input",
                "general_threshold_ev_input",
                "live_auto_promotion",
            ],
            "refresh_subreason_counts": dict(refresh_buckets),
            "refresh_block_subreason_counts": dict(refresh_buckets),
            "refresh_attempted_count": refresh_attempted,
            "refresh_applied_count": refresh_applied,
            "still_latency_blocked_after_refresh_count": still_blocked_after_refresh,
            "latency_pass_recovered_count": recovered_latency_pass,
            "order_bundle_submitted_after_refresh_count": submitted_after_refresh,
            "latency_pass_recovered_downstream_counts": recovered_downstream_counts,
            "latency_pass_recovered_downstream_stage_counts": recovered_downstream_stage_counts,
            "post_restart_window_policy": "event_provenance_only",
        },
        "unknown_latency_reason_count": buckets.get("unknown_latency_reason", 0),
        "known_latency_reason_count": total - buckets.get("unknown_latency_reason", 0),
        "unknown_latency_workorder_required": buckets.get("unknown_latency_reason", 0) > 0,
        "known_guard_route": "report_only_tuning_candidate",
        "unknown_guard_route": "implement_now_candidate",
    }


def _classify(current: dict[str, Any], baseline: dict[str, Any] | None, *, as_of: datetime) -> dict[str, Any]:
    unique = current["stage_unique"]
    ratios = current["ratios"]
    ai_unique = int(unique.get("ai_confirmed", 0) or 0)
    budget_unique = int(unique.get("budget_pass", 0) or 0)
    latency_unique = int(unique.get("latency_pass", 0) or 0)
    submitted_unique = int(unique.get("order_bundle_submitted", 0) or 0)
    latest = _parse_iso_datetime(_safe_str(current.get("latest_event_at")))
    stale_sec = int((as_of - latest).total_seconds()) if latest else None
    during_sentinel_hours = SESSION_START <= as_of.time() <= SENTINEL_END

    baseline_budget_to_ai = None
    baseline_submitted_to_ai = None
    if baseline:
        baseline_budget_to_ai = float(baseline["ratios"].get("budget_to_ai_unique_pct", 0.0) or 0.0)
        baseline_submitted_to_ai = float(baseline["ratios"].get("submitted_to_ai_unique_pct", 0.0) or 0.0)

    reasons: list[str] = []
    matches: list[str] = []

    runtime_ops = current["event_count"] == 0 or (
        during_sentinel_hours and stale_sec is not None and stale_sec > 600
    )
    if runtime_ops:
        matches.append("RUNTIME_OPS")
        reasons.append("pipeline event stream is empty or stale during sentinel hours")

    price_guard = current["price_guard_events"] >= 3 and (
        submitted_unique == 0 or current["price_guard_events"] >= max(3, latency_unique)
    )
    if price_guard:
        matches.append("PRICE_GUARD_DROUGHT")
        reasons.append("price guard blocks dominate the downstream submit path")

    latency_drought = budget_unique >= 3 and (
        submitted_unique == 0
        or ratios["latency_to_budget_unique_pct"] < 25.0
        or current["latency_state_danger_events"] >= max(3, submitted_unique + latency_unique)
    )
    if latency_drought:
        matches.append("LATENCY_DROUGHT")
        reasons.append("budget_pass exists but latency/submitted conversion is weak")

    budget_to_ai = float(ratios.get("budget_to_ai_unique_pct", 0.0) or 0.0)
    upstream_block_events = int(current.get("upstream_block_events", 0) or 0)
    upstream_collapse = ai_unique >= 10 and budget_to_ai < 35.0
    if baseline_budget_to_ai is not None and baseline_budget_to_ai > 0:
        upstream_collapse = upstream_collapse and budget_to_ai <= baseline_budget_to_ai * 0.6
    upstream_threshold = upstream_collapse or (
        ai_unique >= 10 and upstream_block_events >= max(5, budget_unique)
    )
    if upstream_threshold:
        matches.append("UPSTREAM_AI_THRESHOLD")
        reasons.append("AI threshold/wait blockers suppress budget_pass before submit")

    submitted_to_ai = float(ratios.get("submitted_to_ai_unique_pct", 0.0) or 0.0)
    submitted_to_budget = float(ratios.get("submitted_to_budget_unique_pct", 0.0) or 0.0)
    submit_drought_critical = (
        ai_unique >= SUBMIT_DROUGHT_MIN_AI_UNIQUE
        and submitted_to_ai < SUBMIT_TO_AI_CRITICAL_PCT
    ) or (
        budget_unique >= SUBMIT_DROUGHT_MIN_BUDGET_UNIQUE
        and submitted_to_budget <= SUBMIT_TO_BUDGET_CRITICAL_PCT
    )
    if submit_drought_critical:
        matches.append("SUBMIT_DROUGHT_CRITICAL")
        reasons.append(
            "submitted conversion breached critical floor: "
            f"submitted/ai={submitted_to_ai:.2f}% < {SUBMIT_TO_AI_CRITICAL_PCT:.2f}% "
            f"or submitted/budget={submitted_to_budget:.2f}% <= {SUBMIT_TO_BUDGET_CRITICAL_PCT:.2f}%"
        )
    submit_drought_root_cause = _latency_drought_root_cause_summary(current)

    primary = "NORMAL"
    if "RUNTIME_OPS" in matches:
        primary = "RUNTIME_OPS"
    elif "SUBMIT_DROUGHT_CRITICAL" in matches:
        primary = "SUBMIT_DROUGHT_CRITICAL"
    elif "PRICE_GUARD_DROUGHT" in matches:
        primary = "PRICE_GUARD_DROUGHT"
    elif "UPSTREAM_AI_THRESHOLD" in matches and (
        budget_to_ai < 35.0 or baseline_budget_to_ai is not None
    ):
        primary = "UPSTREAM_AI_THRESHOLD"
    elif "LATENCY_DROUGHT" in matches:
        primary = "LATENCY_DROUGHT"
    elif "UPSTREAM_AI_THRESHOLD" in matches:
        primary = "UPSTREAM_AI_THRESHOLD"

    secondary = [item for item in matches if item != primary]
    if primary == "NORMAL":
        reasons.append("no sentinel threshold breached")

    return {
        "primary": primary,
        "secondary": secondary,
        "matches": matches,
        "reasons": reasons,
        "stale_sec": stale_sec,
        "baseline_budget_to_ai_unique_pct": baseline_budget_to_ai,
        "baseline_submitted_to_ai_unique_pct": baseline_submitted_to_ai,
        "submit_drought_thresholds": {
            "min_ai_unique": SUBMIT_DROUGHT_MIN_AI_UNIQUE,
            "min_budget_unique": SUBMIT_DROUGHT_MIN_BUDGET_UNIQUE,
            "submitted_to_ai_critical_pct": SUBMIT_TO_AI_CRITICAL_PCT,
            "submitted_to_budget_critical_pct": SUBMIT_TO_BUDGET_CRITICAL_PCT,
        },
        "submit_drought_handoff_state": "handoff_required" if submit_drought_critical else "not_required",
        "submit_drought_root_cause": submit_drought_root_cause,
        "live_runtime_effect": False,
        "forbidden_automations": FORBIDDEN_AUTOMATIONS,
    }


def _recommend_actions(classification: dict[str, Any]) -> list[str]:
    primary = classification.get("primary")
    matches = classification.get("matches") if isinstance(classification.get("matches"), list) else []
    if "SUBMIT_DROUGHT_CRITICAL" in matches:
        primary = "SUBMIT_DROUGHT_CRITICAL"
    if primary == "RUNTIME_OPS":
        return [
            "Check WS/token/event stream health immediately.",
            "Do not restart automatically; use the restart playbook only after explicit approval.",
        ]
    if primary == "PRICE_GUARD_DROUGHT":
        return [
            "Review top price guard block labels and affected symbols.",
            "Keep threshold/runtime mutation blocked before ThresholdOpsTransition0506.",
        ]
    if primary == "SUBMIT_DROUGHT_CRITICAL":
        return [
            "Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose workorder/LDM handoff.",
            "Split root cause into upstream gate, budget pass, latency/pre-submit guard, and broker receipt buckets before tuning thresholds.",
            "Do not require operator approval for submitted drought surfacing or downstream workorder generation.",
        ]
    if primary == "UPSTREAM_AI_THRESHOLD":
        return [
            "Append score50/wait65_74 missed-winner and avoided-loser cohorts to report-only review.",
            "Do not relax score threshold or revive fallback without a new single-axis workorder.",
        ]
    if primary == "LATENCY_DROUGHT":
        return [
            "Inspect latency_state_danger top reasons and recent quote quality.",
            "Do not auto-relax spread/ws/jitter caps; produce a candidate playbook with rollback guard first.",
        ]
    return ["Continue monitoring; no dynamic action required."]


def _followup_route(classification: dict[str, Any]) -> dict[str, Any]:
    primary = classification.get("primary")
    matches = classification.get("matches") if isinstance(classification.get("matches"), list) else []
    if "SUBMIT_DROUGHT_CRITICAL" in matches:
        primary = "SUBMIT_DROUGHT_CRITICAL"
    if primary == "RUNTIME_OPS":
        return {
            "route": "runtime_ops_playbook",
            "owner": "operator_review",
            "operator_action_required": True,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "incident_playbook_review",
        }
    if primary == "PRICE_GUARD_DROUGHT":
        return {
            "route": "pre_submit_price_guard_review",
            "owner": "postclose_threshold_cycle",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "threshold_cycle_calibration_source_bundle",
        }
    if primary == "SUBMIT_DROUGHT_CRITICAL":
        return {
            "route": "entry_submit_drought_auto_workorder",
            "owner": "postclose_threshold_cycle_and_lifecycle_decision_matrix",
            "operator_action_required": False,
            "runtime_effect": "auto_workorder_no_intraday_mutation",
            "next_artifact": "code_improvement_workorder_and_lifecycle_decision_matrix",
        }
    if primary == "UPSTREAM_AI_THRESHOLD":
        return {
            "route": "score65_74_counterfactual_review",
            "owner": "postclose_threshold_cycle",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "wait6579_ev_cohort_and_missed_probe_counterfactual",
        }
    if primary == "LATENCY_DROUGHT":
        return {
            "route": "latency_quote_quality_review",
            "owner": "postclose_threshold_cycle",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "threshold_cycle_calibration_source_bundle",
        }
    return {
        "route": "normal_no_action",
        "owner": "none",
        "operator_action_required": False,
        "runtime_effect": "report_only_no_mutation",
        "next_artifact": "none",
    }


def _entry_submit_drought_contract(
    classification: dict[str, Any],
    session_summary: dict[str, Any],
) -> dict[str, Any]:
    matches = classification.get("matches") if isinstance(classification.get("matches"), list) else []
    ratios = session_summary.get("ratios") if isinstance(session_summary.get("ratios"), dict) else {}
    unique = session_summary.get("stage_unique") if isinstance(session_summary.get("stage_unique"), dict) else {}
    blocker_labels = [
        str(item.get("label") or "")
        for item in (session_summary.get("blocker_top") or [])
        if isinstance(item, dict)
    ]
    taxonomy_leakage = any(label.startswith("blocked_swing_") for label in blocker_labels)
    weak_contract_matches = []
    if "UPSTREAM_AI_THRESHOLD" in matches:
        weak_contract_matches.append("UPSTREAM_GATE")
    if "SUBMIT_DROUGHT_CRITICAL" in matches:
        weak_contract_matches.extend(
            [
                "BUDGET_PASS_COLLAPSE",
                "BROKER_RECEIPT",
                "FILL_QUALITY",
                "TELEGRAM_POST_SUBMIT_ONLY",
                "SIM_REAL_AUTHORITY",
            ]
        )
    if "LATENCY_DROUGHT" in matches:
        weak_contract_matches.append("LATENCY_PRE_SUBMIT")
    if "PRICE_GUARD_DROUGHT" in matches:
        weak_contract_matches.append("PRICE_REVALIDATION")
    if taxonomy_leakage:
        weak_contract_matches.append("SOURCE_TAXONOMY_LEAKAGE")
    return {
        "primary": classification.get("primary"),
        "matches": matches,
        "critical": "SUBMIT_DROUGHT_CRITICAL" in matches,
        "operator_action_required": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_submit_allowed": False,
        "required_downstream": [
            "code_improvement_workorder",
            "lifecycle_decision_matrix.submit_bucket_attribution",
            "threshold_cycle_ev_report",
            "runtime_approval_summary",
            "postclose_verifier",
        ],
        "stage_unique": {
            "ai_confirmed": int(unique.get("ai_confirmed", 0) or 0),
            "budget_pass": int(unique.get("budget_pass", 0) or 0),
            "latency_pass": int(unique.get("latency_pass", 0) or 0),
            "order_bundle_submitted": int(unique.get("order_bundle_submitted", 0) or 0),
        },
        "ratios": {
            "submitted_to_ai_unique_pct": ratios.get("submitted_to_ai_unique_pct"),
            "submitted_to_budget_unique_pct": ratios.get("submitted_to_budget_unique_pct"),
            "budget_to_ai_unique_pct": ratios.get("budget_to_ai_unique_pct"),
            "latency_to_budget_unique_pct": ratios.get("latency_to_budget_unique_pct"),
        },
        "thresholds": classification.get("submit_drought_thresholds") or {},
        "weak_contract_matches": sorted(set(weak_contract_matches)),
        "source_taxonomy_leakage": taxonomy_leakage,
        "forbidden_uses": [
            "intraday_threshold_mutation",
            "broker_guard_bypass",
            "provider_route_change",
            "bot_restart_trigger",
            "telegram_pre_submit_buy_alert",
        ],
    }


def build_buy_funnel_sentinel_report(
    target_date: str,
    *,
    as_of: datetime | None = None,
    windows_min: tuple[int, ...] = DEFAULT_WINDOWS,
    dry_run: bool = False,
    use_cache: bool = False,
    use_summary: bool = False,
) -> dict[str, Any]:
    events, summary_rows, event_load = _load_event_sources(
        target_date,
        use_cache=use_cache,
        use_summary=use_summary,
    )
    if as_of is None:
        if dry_run and events:
            as_of = events[-1].emitted_at
        else:
            as_of = datetime.now()

    session_start = datetime.combine(_parse_target_date(target_date), SESSION_START)
    session_summary = _summarize_events(
        events,
        start_at=session_start,
        end_at=as_of,
        summary_rows=summary_rows,
    )
    windows: dict[str, dict[str, Any]] = {}
    for minutes in sorted(set(windows_min)):
        start_at = max(session_start, as_of - timedelta(minutes=minutes))
        windows[f"{minutes}m"] = _summarize_events(
            events,
            start_at=start_at,
            end_at=as_of,
            summary_rows=summary_rows,
        )

    baseline_date = previous_trading_day_with_events(target_date)
    baseline_summary = None
    baseline_event_load = None
    if baseline_date:
        baseline_events, baseline_summary_rows, baseline_event_load = _load_event_sources(
            baseline_date,
            use_cache=use_cache,
            use_summary=use_summary,
        )
        baseline_start = datetime.combine(_parse_target_date(baseline_date), SESSION_START)
        baseline_end = _same_time_on_date(baseline_date, as_of)
        baseline_summary = _summarize_events(
            baseline_events,
            start_at=baseline_start,
            end_at=baseline_end,
            summary_rows=baseline_summary_rows,
        )

    classification = _classify(session_summary, baseline_summary, as_of=as_of)
    followup = _followup_route(classification)
    recommended_actions = _recommend_actions(classification)
    entry_submit_drought_contract = _entry_submit_drought_contract(classification, session_summary)

    return {
        "schema_version": 2,
        "report_type": "buy_funnel_sentinel",
        "target_date": target_date,
        "as_of": as_of.isoformat(timespec="seconds"),
        "dry_run": bool(dry_run),
        "event_load": {
            **event_load,
            "baseline": baseline_event_load,
        },
        "policy": {
            "report_only": True,
            "live_runtime_effect": False,
            "allowed_automations": [
                "json_report",
                "markdown_report",
                "action_recommendation",
            ],
            "forbidden_automations": FORBIDDEN_AUTOMATIONS,
        },
        "excluded_stocks": [
            {"stock_name": name, "stock_code": code, "reason": "manual_trade"}
            for name, code in sorted(MANUAL_EXCLUDED_STOCKS)
        ],
        "baseline": {
            "date": baseline_date,
            "same_time_summary": baseline_summary,
        },
        "current": {
            "session": session_summary,
            "windows": windows,
        },
        "classification": classification,
        "entry_submit_drought_contract": entry_submit_drought_contract,
        "followup": followup,
        "recommended_actions": recommended_actions,
    }


def _format_top_blockers(blockers: list[dict[str, Any]], *, limit: int = 5) -> str:
    if not blockers:
        return "-"
    return ", ".join(f"{item['label']}={item['count']}" for item in blockers[:limit])


def build_markdown(report: dict[str, Any]) -> str:
    session = report["current"]["session"]
    ratios = session["ratios"]
    unique = session["stage_unique"]
    classification = report["classification"]
    quote_freshness = (
        (classification.get("submit_drought_root_cause") or {}).get("quote_freshness_attribution")
        if isinstance(classification.get("submit_drought_root_cause"), dict)
        else {}
    )
    quote_freshness = quote_freshness if isinstance(quote_freshness, dict) else {}
    baseline = report["baseline"]["same_time_summary"]
    baseline_ratios = baseline["ratios"] if baseline else {}
    lines = [
        f"# BUY Funnel Sentinel {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- primary: `{classification['primary']}`",
        f"- secondary: `{', '.join(classification['secondary']) if classification['secondary'] else '-'}`",
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- live_runtime_effect: `{str(report['policy']['live_runtime_effect']).lower()}`",
        f"- operator_action_required: `{str(report['followup']['operator_action_required']).lower()}`",
        f"- followup_route: `{report['followup']['route']}`",
        f"- followup_owner: `{report['followup']['owner']}`",
        f"- runtime_effect: `{report['followup']['runtime_effect']}`",
        f"- submit_contract_downstream: `{', '.join((report.get('entry_submit_drought_contract') or {}).get('required_downstream') or []) or '-'}`",
        f"- submit_contract_weak_matches: `{', '.join((report.get('entry_submit_drought_contract') or {}).get('weak_contract_matches') or []) or '-'}`",
        "",
        "## 근거",
        "",
        f"- as_of: `{report['as_of']}`",
        f"- baseline_date: `{report['baseline']['date'] or '-'}`",
        f"- ai_confirmed unique: `{unique.get('ai_confirmed', 0)}`",
        f"- budget_pass unique: `{unique.get('budget_pass', 0)}`",
        f"- latency_pass unique: `{unique.get('latency_pass', 0)}`",
        f"- submitted unique: `{unique.get('order_bundle_submitted', 0)}`",
        f"- holding_started unique: `{unique.get('holding_started', 0)}`",
        f"- budget/ai unique: `{ratios.get('budget_to_ai_unique_pct', 0.0)}%`"
        f" (baseline `{baseline_ratios.get('budget_to_ai_unique_pct', '-')}`)",
        f"- submitted/ai unique: `{ratios.get('submitted_to_ai_unique_pct', 0.0)}%`"
        f" (baseline `{baseline_ratios.get('submitted_to_ai_unique_pct', '-')}`)",
        f"- critical submit thresholds: `submitted/ai < {SUBMIT_TO_AI_CRITICAL_PCT}%` "
        f"or `submitted/budget <= {SUBMIT_TO_BUDGET_CRITICAL_PCT}%` "
        f"(floors: ai>={SUBMIT_DROUGHT_MIN_AI_UNIQUE}, budget>={SUBMIT_DROUGHT_MIN_BUDGET_UNIQUE})",
        f"- top blockers: `{_format_top_blockers(session['blocker_top'])}`",
        f"- swing blockers: `{_format_top_blockers(session.get('swing_blocker_top') or [])}`",
        f"- upstream blockers: `{_format_top_blockers(session['upstream_blocker_top'])}`",
        f"- latency blockers: `{_format_top_blockers(session['latency_blocker_top'])}`",
        f"- price guards: `{_format_top_blockers(session['price_guard_top'])}`",
        f"- quote refresh: `attempted={quote_freshness.get('refresh_attempted_count', 0)}, "
        f"applied={quote_freshness.get('refresh_applied_count', 0)}, "
        f"latency_recovered={quote_freshness.get('latency_pass_recovered_count', 0)}, "
        f"submitted_after_refresh={quote_freshness.get('order_bundle_submitted_after_refresh_count', 0)}`",
        f"- quote refresh downstream: `{quote_freshness.get('latency_pass_recovered_downstream_counts') or {}}`",
        "",
        "## 금지된 자동변경",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["policy"]["forbidden_automations"])
    lines.extend(["", "## 권고 액션", ""])
    lines.extend(f"- {item}" for item in report["recommended_actions"])
    lines.extend(["", "## Window Summary", ""])
    for name, summary in report["current"]["windows"].items():
        stage_unique = summary["stage_unique"]
        lines.append(
            f"- `{name}`: ai={stage_unique.get('ai_confirmed', 0)}, "
            f"budget={stage_unique.get('budget_pass', 0)}, "
            f"latency={stage_unique.get('latency_pass', 0)}, "
            f"submitted={stage_unique.get('order_bundle_submitted', 0)}, "
            f"top=`{_format_top_blockers(summary['blocker_top'], limit=3)}`, "
            f"swing=`{_format_top_blockers(summary.get('swing_blocker_top') or [], limit=3)}`, "
            f"upstream=`{_format_top_blockers(summary['upstream_blocker_top'], limit=3)}`"
        )
    lines.append("")
    return "\n".join(lines)


def save_report_artifacts(report: dict[str, Any]) -> dict[str, str]:
    target_date = report["target_date"]
    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"buy_funnel_sentinel_{target_date}.json"
    md_path = report_dir / f"buy_funnel_sentinel_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build intraday BUY funnel sentinel report.")
    parser.add_argument("--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--as-of", dest="as_of", default="")
    parser.add_argument(
        "--window-min",
        dest="window_min",
        action="append",
        type=int,
        default=[],
        help="Rolling window minutes. Repeatable. Defaults to 5/10/30.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Use latest event as as_of if omitted.")
    parser.add_argument("--use-cache", action="store_true", help="Use slim incremental sentinel event cache.")
    parser.add_argument(
        "--use-summary",
        action="store_true",
        help="Use high-volume blocked_* summary sidecar for BUY diagnostic blockers.",
    )
    parser.add_argument("--print-json", action="store_true", help="Print final result JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    as_of = _parse_as_of(args.target_date, args.as_of) if args.as_of else None
    windows = tuple(args.window_min) if args.window_min else DEFAULT_WINDOWS
    report = build_buy_funnel_sentinel_report(
        args.target_date,
        as_of=as_of,
        windows_min=windows,
        dry_run=bool(args.dry_run),
        use_cache=bool(args.use_cache),
        use_summary=bool(args.use_summary),
    )
    artifacts = save_report_artifacts(report)
    result = {
        "status": "success",
        "target_date": args.target_date,
        "classification": report["classification"]["primary"],
        "secondary": report["classification"]["secondary"],
        "artifacts": artifacts,
    }
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
