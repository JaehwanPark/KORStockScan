"""Counterfactual evaluation for AI BUY entries that never reached order submission."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.engine.scalping.position_sizing_allocator import (
    ScalpingSizingContext,
    infer_scalping_venue,
    max_position_qty_cap_from_budget,
    resolve_scalping_allocation,
)
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import read_jsonl
from src.utils.logger import log_error

MISSED_ENTRY_COUNTERFACTUAL_SCHEMA_VERSION = 5
_EXPLICIT_TRADABLE_VENUES = {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
_WATCH_CYCLE_HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)
_WATCH_CYCLE_ESTIMATED_ROUND_TRIP_COST_PCT = 0.23
_SCANNER_PROMOTED_STAGE = "scalping_scanner_candidate_promoted"
_SCANNER_ATTACH_STAGE = "scalping_scanner_runtime_target_attach"
_SCANNER_EVICTION_STAGE = "scalping_scanner_watch_eviction"
_ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
_INFERRED_BUY_INTENT_STAGES = _ENTRY_ARMED_STAGES | {
    "score65_74_recovery_probe_entry_unlocked"
}
_INFERRED_BUY_INTENT_DEDUP_TERMINAL_STAGES = {
    "pre_submit_liquidity_guard_block",
    "pre_submit_entry_ai_authority_guard_block",
    "pre_submit_overbought_pullback_guard_block",
    "pre_submit_weak_context_late_entry_guard_block",
}
_INFERRED_BUY_INTENT_DEDUP_WINDOW_SEC = 120
_ATTEMPT_AUXILIARY_STAGES = {
    "dual_persona_shadow",
    "dual_persona_shadow_error",
    "ai_numeric_consistency_recheck_evaluated",
    "ai_numeric_consistency_recheck_allowed",
    "ai_numeric_consistency_recheck_skipped",
    "ai_numeric_consistency_recheck_failed",
    "ai_numeric_consistency_recheck_corrected",
    "early_accel_strong_bundle_recheck_evaluated",
    "early_accel_strong_bundle_recheck_allowed",
    "early_accel_strong_bundle_recheck_skipped",
    "early_accel_strong_bundle_recheck_failed",
    "early_accel_strong_bundle_recheck_corrected",
    "pre_submit_liquidity_relief_evaluated",
    "pre_submit_liquidity_relief_allowed",
    "pre_submit_liquidity_relief_skipped",
}
_BUY_MISSED_MFE_PCT = 0.8
_BUY_MISSED_CLOSE_PCT = 0.3
_BUY_AVOIDED_MAE_PCT = -0.8
_BUY_AVOIDED_CLOSE_PCT = -0.3
_BUY_TP_PCT = 0.5
_BUY_SL_PCT = -0.5
_RISING_MISSED_STAGE = "rising_missed_one_share_entry"
_STAGE_LABELS = {
    "latency_block": "지연 리스크 차단",
    "blocked_liquidity": "유동성 차단",
    "blocked_ai_score": "AI 점수 차단",
    "first_ai_wait": "첫 AI 대기",
    "blocked_zero_qty": "수량 0주 차단",
    "auth_zero_qty": "인증 장애 0원 예산",
    "blocked_gap_from_scan": "포착가 갭 차단",
    "blocked_overbought": "과열 차단",
    "blocked_big_bite_hard_gate": "Big-Bite 차단",
    "blocked_vpw": "정적 체결강도 차단",
    "blocked_strength_momentum": "동적 체결강도 차단",
    "pre_submit_entry_ai_authority_guard_block": "AI 평가 소스품질 차단",
    "pre_submit_weak_context_late_entry_guard_block": "약한 문맥 늦은 진입 차단",
    "entry_armed_expired": "진입 자격 만료",
    "entry_armed_expired_after_wait": "진입 대기 후 자격 만료",
    "entry_arm_expired": "진입 자격 만료(legacy)",
    "buy_like_no_submit_terminal": "BUY-like 미제출 종료",
    "scalp_entry_action_decision_snapshot": "AI 판정 스냅샷",
}


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    return read_jsonl(path)


def _safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, "", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _minute_candle_meta(
    candles: list[dict], meta: dict | None = None, *, requested_limit: int | None = None
) -> dict:
    source_meta = dict(meta or {})
    source_meta.setdefault("api_id", "ka10080")
    source_meta.setdefault("requested_limit", requested_limit)
    source_meta.setdefault("received_count", len(candles or []))
    source_meta.setdefault("truncated_window", False)
    source_meta.setdefault("sort_direction_detected", "unknown")
    source_meta.setdefault("cont_yn_seen", False)
    source_meta.setdefault("next_key_seen", False)
    source_meta.setdefault("continuous_next_key_missing", False)
    source_meta.setdefault("continuous_page_limit_reached", False)
    source_meta.setdefault("rest_received_ts_ms", None)
    source_meta.setdefault("latest_source_timestamp", None)
    source_meta.setdefault(
        "source_time_basis", "response_received_epoch_ms_and_chart_bar_timestamp"
    )
    return source_meta


def _fetch_minute_candles_with_meta(
    kiwoom_utils, token: str, code: str, *, limit: int
) -> tuple[list[dict], dict]:
    if hasattr(kiwoom_utils, "get_minute_candles_ka10080_with_meta"):
        candles, meta = kiwoom_utils.get_minute_candles_ka10080_with_meta(
            token, code, limit=limit
        )
        candles = candles or []
        return candles, _minute_candle_meta(candles, meta, requested_limit=limit)
    candles = kiwoom_utils.get_minute_candles_ka10080(token, code, limit=limit) or []
    return candles, _minute_candle_meta(candles, requested_limit=limit)


def _minute_forward_source_quality(
    metrics: dict, candle_meta: dict, *, window_minutes: int = 10
) -> dict:
    bars = _safe_int((metrics or {}).get("bars"), 0)
    if bars <= 0:
        status = "insufficient_window"
        gate = "source_quality_insufficient"
        reason = f"no_ka10080_bars_in_forward_{window_minutes}m_window"
    elif window_minutes > 10 and bars < window_minutes:
        status = "partial_window"
        gate = "source_quality_warning"
        reason = f"insufficient_ka10080_bars_in_forward_{window_minutes}m_window"
    elif bool(candle_meta.get("continuous_next_key_missing")):
        status = "partial_window"
        gate = "source_quality_warning"
        reason = "ka10080_continuation_key_missing"
    elif bool(candle_meta.get("continuous_page_limit_reached")):
        status = "partial_window"
        gate = "source_quality_warning"
        reason = "ka10080_continuation_page_limit_reached"
    elif bool(candle_meta.get("truncated_window")):
        status = "partial_window"
        gate = "source_quality_warning"
        reason = "ka10080_truncated_window"
    else:
        status = "pass"
        gate = "pass"
        reason = (
            "ka10080_forward_window_available"
            if window_minutes == 10
            else f"ka10080_forward_{window_minutes}m_window_available"
        )
    if window_minutes == 10:
        return {
            "minute_candle_source_quality": status,
            "minute_candle_source_quality_gate": gate,
            "minute_candle_source_quality_reason": reason,
            "minute_candle_forward_10m_bars": bars,
        }
    return {
        f"minute_candle_forward_{window_minutes}m_source_quality": status,
        f"minute_candle_forward_{window_minutes}m_source_quality_gate": gate,
        f"minute_candle_forward_{window_minutes}m_source_quality_reason": reason,
        f"minute_candle_forward_{window_minutes}m_bars": bars,
    }


def _sim_virtual_budget_krw() -> int:
    return max(
        0, int(getattr(TRADING_RULES, "SIM_VIRTUAL_BUDGET_KRW", 10_000_000) or 0)
    )


def _sim_virtual_qty(
    entry_price: int,
    ai_score: float,
    *,
    reference_time=None,
    source_signature=None,
    effective_venue=None,
) -> dict:
    _ = ai_score
    virtual_budget = _sim_virtual_budget_krw()
    max_budget = int(getattr(TRADING_RULES, "SCALPING_MAX_BUY_BUDGET_KRW", 0) or 0)
    venue = infer_scalping_venue(reference_time, effective_venue)
    decision = resolve_scalping_allocation(
        ScalpingSizingContext(
            allocation_stage="missed_entry_counterfactual",
            reference_time=reference_time,
            source_signature=source_signature,
            effective_venue=venue,
            budget_base_krw=virtual_budget,
            price_krw=entry_price,
            absolute_budget_cap_krw=max_budget,
            max_position_qty_cap=max_position_qty_cap_from_budget(
                virtual_budget,
                entry_price,
                getattr(TRADING_RULES, "MAX_POSITION_PCT", 0.20),
            ),
            simulation=True,
        )
    )
    return {
        "qty": decision.effective_qty,
        "virtual_budget_krw": virtual_budget,
        "max_budget": max_budget,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        **decision.event_fields(),
    }


_COUNTERFACTUAL_SIZING_KEYS = (
    "formula_version",
    "tier",
    "ratio",
    "tier_reason",
    "source_count",
    "reference_time",
    "venue",
    "target_budget",
    "safe_budget",
    "pre_cap_qty",
    "effective_qty",
    "min_one_share_floor_applied",
    "binding_caps",
    "allocation_stage",
    "simulation",
    "actual_order_submitted",
    "broker_order_forbidden",
)


def _counterfactual_sizing_fields(capacity: dict) -> dict:
    return {key: capacity.get(key) for key in _COUNTERFACTUAL_SIZING_KEYS}


def _attempt_source_contract(
    attempt_events: list["EntryEvent"], anchor_event: "EntryEvent"
) -> dict:
    """Resolve venue/provenance without treating clock inference as venue evidence."""

    authoritative_venue_values: set[str] = set()
    fallback_venue_values: set[str] = set()
    venue_field_sources: list[str] = []
    for event in attempt_events:
        for key in ("rising_missed_effective_venue", "effective_venue", "venue"):
            value = str(event.fields.get(key) or "").strip().upper()
            if value not in _EXPLICIT_TRADABLE_VENUES:
                continue
            if key == "venue":
                fallback_venue_values.add(value)
            else:
                authoritative_venue_values.add(value)
            venue_field_sources.append(f"{event.stage}.{key}")

    if len(authoritative_venue_values) == 1:
        effective_venue = next(iter(authoritative_venue_values))
        venue_resolution = "explicit_effective_venue_field"
        venue_source_quality = "pass"
        venue_tuning_allowed = True
    elif len(authoritative_venue_values) > 1:
        effective_venue = "UNKNOWN"
        venue_resolution = "conflicting_explicit_effective_venue"
        venue_source_quality = "conflict"
        venue_tuning_allowed = False
    elif len(fallback_venue_values) == 1:
        effective_venue = next(iter(fallback_venue_values))
        venue_resolution = "explicit_venue_fallback"
        venue_source_quality = "pass"
        venue_tuning_allowed = True
    elif len(fallback_venue_values) > 1:
        effective_venue = "UNKNOWN"
        venue_resolution = "conflicting_explicit_venue_fallback"
        venue_source_quality = "conflict"
        venue_tuning_allowed = False
    else:
        effective_venue = "UNKNOWN"
        venue_resolution = "missing_explicit_venue"
        venue_source_quality = "missing"
        venue_tuning_allowed = False

    def _latest_field(*keys: str) -> str:
        for event in reversed(attempt_events):
            for key in keys:
                value = str(event.fields.get(key) or "").strip()
                if value:
                    return value
        return ""

    return {
        "effective_venue": effective_venue,
        "venue_resolution": venue_resolution,
        "venue_source_quality": venue_source_quality,
        "venue_tuning_allowed": venue_tuning_allowed,
        "venue_field_sources": sorted(set(venue_field_sources)),
        "market_session_bucket": _latest_field(
            "rising_missed_market_session_bucket", "market_session_bucket"
        ),
        "source_signature": _latest_field("source_signature"),
        "reference_time": anchor_event.emitted_at,
        "metric_role": "source_quality_gate",
        "decision_authority": "missed_entry_counterfactual_source_only",
        "window_policy": "same_entry_attempt_explicit_event_fields",
        "sample_floor": "1_attempt_with_explicit_tradable_venue",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": (
            "single_conflict_free_explicit_effective_venue_or_venue_fallback"
        ),
        "forbidden_uses": [
            "clock_only_venue_inference_for_tuning",
            "intraday_threshold_mutation",
            "live_auto_promotion",
            "runtime_apply_bridge",
            "broker_order_submit",
        ],
    }


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return (
        round((float(numerator) / float(denominator)) * 100.0, 1)
        if denominator > 0
        else 0.0
    )


def _parse_event_dt(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    candidate = str(value or "").strip()
    if not candidate:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return None


def _parse_minute_time(
    value: str, signal_date: str, source_timestamp: str | None = None
) -> datetime | None:
    source_text = str(source_timestamp or "").strip()
    if source_text:
        for fmt in ("%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(
                    source_text[: 14 if fmt == "%Y%m%d%H%M%S" else 19], fmt
                )
            except Exception:
                continue
        try:
            return datetime.fromisoformat(source_text)
        except Exception:
            pass
    try:
        return datetime.strptime(f"{signal_date} {value}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _classify_stage(stage: str) -> str:
    if stage == "order_bundle_submitted":
        return "submitted"
    if (
        stage.startswith("blocked_")
        or stage.endswith("_block")
        or stage.endswith("_failed")
    ):
        return "blocked"
    if stage in {
        "first_ai_wait",
        "entry_armed_expired",
        "entry_armed_expired_after_wait",
        "entry_arm_expired",
    }:
        return "waiting"
    return "progress"


def _is_attempt_terminal(stage: str) -> bool:
    return _classify_stage(stage) in {"blocked", "submitted"}


def _stage_label(stage: str) -> str:
    return _STAGE_LABELS.get(stage, stage)


@dataclass
class EntryEvent:
    emitted_at: str
    signal_date: str
    name: str
    code: str
    stage: str
    record_id: str
    fields: dict[str, str]


@dataclass
class MissedEntryCounterfactualSummary:
    date: str
    total_candidates: int = 0
    evaluated_candidates: int = 0
    outcome_counts: dict[str, int] = field(default_factory=dict)
    top_missed_winners: list[dict] = field(default_factory=list)
    top_avoided_losers: list[dict] = field(default_factory=list)


def _load_entry_events(target_date: str) -> list[EntryEvent]:
    rows = _load_jsonl(_pipeline_events_path(target_date))
    events: list[EntryEvent] = []
    for row in rows:
        if str(row.get("pipeline") or "").strip() != "ENTRY_PIPELINE":
            continue
        code = str(row.get("stock_code") or "").strip()[:6]
        if not code:
            continue
        emitted_at = str(row.get("emitted_at") or "")
        events.append(
            EntryEvent(
                emitted_at=emitted_at,
                signal_date=str(row.get("emitted_date") or target_date),
                name=str(row.get("stock_name") or ""),
                code=code,
                stage=str(row.get("stage") or ""),
                record_id=str(row.get("record_id") or row.get("id") or ""),
                fields={
                    str(key): str(value)
                    for key, value in dict(row.get("fields") or {}).items()
                },
            )
        )
    events.sort(
        key=lambda item: (
            _parse_event_dt(item.emitted_at) or datetime.min,
            item.code,
            item.stage,
        )
    )
    return events


def _split_attempt_segments(item_events: list[EntryEvent]) -> list[list[EntryEvent]]:
    if not item_events:
        return []
    segments: list[list[EntryEvent]] = []
    current: list[EntryEvent] = []
    current_record_id = ""
    segment_terminated = False

    for event in item_events:
        record_changed = bool(
            current
            and event.record_id
            and current_record_id
            and event.record_id != current_record_id
        )
        should_rollover = record_changed or (
            segment_terminated and event.stage not in _ATTEMPT_AUXILIARY_STAGES
        )

        if should_rollover and current:
            segments.append(current)
            current = []
            current_record_id = ""
            segment_terminated = False

        current.append(event)
        if event.record_id and not current_record_id:
            current_record_id = event.record_id
        if _is_attempt_terminal(event.stage):
            segment_terminated = True

    if current:
        segments.append(current)
    return segments


def _build_candidates(target_date: str) -> list[dict]:
    return _build_buy_attempts(target_date, include_submitted=False)


def _buy_intent_events(
    attempt_events: list[EntryEvent],
) -> tuple[list[EntryEvent], str]:
    explicit_buy_events = [
        event
        for event in attempt_events
        if event.stage == "ai_confirmed"
        and str(event.fields.get("action") or "").upper() == "BUY"
    ]
    if explicit_buy_events:
        return explicit_buy_events, "explicit_ai_buy"

    inferred_buy_events = [
        event for event in attempt_events if event.stage in _INFERRED_BUY_INTENT_STAGES
    ]
    if inferred_buy_events:
        return inferred_buy_events, "inferred_entry_armed_path"
    snapshot_decision_events = [
        event
        for event in attempt_events
        if event.stage == "scalp_entry_action_decision_snapshot"
        and str(event.fields.get("chosen_action") or "").upper()
        in {
            "NO_BUY_AI",
            "WAIT_REQUOTE",
            "SKIP_STALE",
            "SKIP_PRE_SUBMIT_SAFETY",
            "SKIP_SOURCE_QUALITY",
        }
    ]
    if snapshot_decision_events:
        return snapshot_decision_events, "snapshot_decision_path"
    return [], "missing_buy_intent"


def _snapshot_terminal_class(event: EntryEvent) -> str | None:
    if event.stage != "scalp_entry_action_decision_snapshot":
        return None
    chosen_action = str(event.fields.get("chosen_action") or "").upper()
    if chosen_action == "NO_BUY_AI":
        return "blocked"
    if chosen_action in {
        "WAIT_REQUOTE",
        "SKIP_STALE",
        "SKIP_PRE_SUBMIT_SAFETY",
        "SKIP_SOURCE_QUALITY",
    }:
        return "waiting"
    return None


def _infer_buy_like_no_submit_reason(attempt_events: list[EntryEvent]) -> str:
    stages = {event.stage for event in attempt_events}
    if "latency_block" in stages:
        return "latency_block"
    if any(
        stage.startswith("pre_submit_") and stage.endswith("_block") for stage in stages
    ):
        return "pre_submit_guard_block"
    if "blocked_zero_qty" in stages:
        return "quantity_zero"
    if "auth_zero_qty" in stages:
        return "budget_blocked"
    if {
        "entry_armed_expired",
        "entry_armed_expired_after_wait",
        "entry_arm_expired",
    } & stages:
        return "entry_armed_expired"
    if any(stage in {"blocked_cooldown", "ai_cooldown_blocked"} for stage in stages):
        return "cooldown_blocked"
    if any(stage in _ENTRY_ARMED_STAGES for stage in stages):
        return "broker_submit_not_reached"
    return "state_transition_missing"


def _missed_submit_cohort(candidate: dict) -> str:
    terminal_stage = str(candidate.get("terminal_stage") or "")
    terminal_fields = (
        candidate.get("terminal_fields")
        if isinstance(candidate.get("terminal_fields"), dict)
        else {}
    )
    stage_flow = {
        str(stage).strip()
        for stage in (candidate.get("stage_flow") or [])
        if str(stage).strip()
    }
    chosen_action = str(terminal_fields.get("chosen_action") or "").upper()
    if terminal_stage == "early_accel_strong_bundle_recheck_failed":
        return "early_accel_strong_bundle_recheck_failed"
    if terminal_stage == "ai_numeric_consistency_recheck_failed":
        return "ai_numeric_consistency_recheck_failed"
    if (
        terminal_stage == "scalp_entry_action_decision_snapshot"
        and chosen_action == "NO_BUY_AI"
    ):
        if "early_accel_strong_bundle_recheck_corrected" in stage_flow:
            return "early_accel_strong_bundle_recheck_corrected"
        if "early_accel_strong_bundle_recheck_failed" in stage_flow:
            return "early_accel_strong_bundle_recheck_failed"
        if "early_accel_strong_bundle_recheck_skipped" in stage_flow:
            return "early_accel_strong_bundle_recheck_skipped"
        if terminal_fields.get("ai_reason_numeric_inconsistency") in {
            True,
            "true",
            "True",
            "1",
        }:
            return "ai_numeric_inconsistency_no_buy"
        return "ai_no_buy_clean_reason"
    if terminal_stage == "pre_submit_liquidity_guard_block":
        return "entry_armed_pre_submit_liquidity_block"
    if terminal_stage == "buy_like_no_submit_terminal":
        return "buy_like_no_submit_terminal"
    if terminal_stage in {
        "latency_block",
        "entry_submit_revalidation_block",
        "pre_submit_entry_ai_authority_guard_block",
        "pre_submit_weak_context_late_entry_guard_block",
        "pre_submit_overbought_pullback_guard_block",
        "real_weak_pullback_entry_block",
    }:
        return "entry_armed_latency_or_safety_block"
    if chosen_action in {
        "WAIT_REQUOTE",
        "SKIP_STALE",
        "SKIP_PRE_SUBMIT_SAFETY",
        "SKIP_SOURCE_QUALITY",
    }:
        return "entry_armed_latency_or_safety_block"
    return terminal_stage or "uncategorized"


def _dedupe_inferred_pre_submit_attempts(candidates: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    last_seen: dict[tuple[str, str, str], datetime] = {}
    for candidate in candidates:
        terminal_stage = str(candidate.get("terminal_stage") or "")
        buy_intent_source = str(candidate.get("buy_intent_source") or "")
        if (
            buy_intent_source != "inferred_entry_armed_path"
            or terminal_stage not in _INFERRED_BUY_INTENT_DEDUP_TERMINAL_STAGES
        ):
            deduped.append(candidate)
            continue

        signal_dt = _parse_event_dt(
            f"{candidate.get('signal_date')} {candidate.get('signal_time')}"
        )
        if signal_dt is None:
            deduped.append(candidate)
            continue

        key = (
            str(candidate.get("stock_code") or ""),
            str(candidate.get("record_id") or ""),
            terminal_stage,
        )
        previous_dt = last_seen.get(key)
        if previous_dt is not None:
            elapsed_sec = (signal_dt - previous_dt).total_seconds()
            if 0 <= elapsed_sec <= _INFERRED_BUY_INTENT_DEDUP_WINDOW_SEC:
                continue

        last_seen[key] = signal_dt
        deduped.append(candidate)
    return deduped


def _build_buy_attempts(
    target_date: str,
    *,
    include_submitted: bool = True,
    events: list[EntryEvent] | None = None,
) -> list[dict]:
    events = list(events) if events is not None else _load_entry_events(target_date)
    by_stock: dict[tuple[str, str], list[EntryEvent]] = defaultdict(list)
    for event in events:
        by_stock[(event.name, event.code)].append(event)

    candidates: list[dict] = []
    for _key, item_events in by_stock.items():
        for attempt_events in _split_attempt_segments(item_events):
            if not attempt_events:
                continue
            has_submitted = any(
                event.stage == "order_bundle_submitted" for event in attempt_events
            )
            if has_submitted and not include_submitted:
                continue

            buy_events, buy_intent_source = _buy_intent_events(attempt_events)
            if not buy_events:
                continue

            terminal_event = next(
                (
                    event
                    for event in reversed(attempt_events)
                    if _classify_stage(event.stage)
                    in (
                        {"blocked", "waiting", "submitted"}
                        if include_submitted
                        else {"blocked", "waiting"}
                    )
                ),
                None,
            )
            if terminal_event is None:
                terminal_event = next(
                    (
                        event
                        for event in reversed(attempt_events)
                        if _snapshot_terminal_class(event)
                        in (
                            {"blocked", "waiting", "submitted"}
                            if include_submitted
                            else {"blocked", "waiting"}
                        )
                    ),
                    None,
                )
            if terminal_event is None:
                if has_submitted:
                    continue
                anchor_for_terminal = buy_events[-1]
                reason = _infer_buy_like_no_submit_reason(attempt_events)
                terminal_event = EntryEvent(
                    emitted_at=anchor_for_terminal.emitted_at,
                    signal_date=target_date,
                    name=anchor_for_terminal.name,
                    code=anchor_for_terminal.code,
                    stage="buy_like_no_submit_terminal",
                    record_id=anchor_for_terminal.record_id,
                    fields={
                        "no_submit_reason": reason,
                        "terminal_stage_source": "counterfactual_inferred",
                    },
                )

            anchor_event = (
                next(
                    (
                        event
                        for event in reversed(attempt_events)
                        if event.stage in _ENTRY_ARMED_STAGES
                    ),
                    None,
                )
                or buy_events[-1]
            )

            anchor_dt = _parse_event_dt(anchor_event.emitted_at)
            if anchor_dt is None:
                continue

            budget_event = next(
                (
                    event
                    for event in reversed(attempt_events)
                    if event.stage == "budget_pass"
                ),
                None,
            )
            signal_price = _safe_int(anchor_event.fields.get("target_buy_price"), 0)
            ai_score = _safe_float(
                anchor_event.fields.get("ai_score"),
                _safe_float(buy_events[-1].fields.get("ai_score"), 0.0),
            )
            blocker_counts = Counter(
                event.stage
                for event in attempt_events
                if _classify_stage(event.stage) in {"blocked", "waiting"}
            )
            rising_missed_event = next(
                (
                    event
                    for event in reversed(attempt_events)
                    if event.stage == _RISING_MISSED_STAGE
                ),
                None,
            )
            source_contract = _attempt_source_contract(attempt_events, anchor_event)

            candidates.append(
                {
                    "candidate_id": f"{anchor_event.code}:{anchor_event.record_id or '-'}:{anchor_dt.strftime('%H%M%S')}",
                    "signal_date": target_date,
                    "signal_time": anchor_dt.strftime("%H:%M:%S"),
                    "stock_code": anchor_event.code,
                    "stock_name": anchor_event.name,
                    "attempt_status": "ENTERED" if has_submitted else "MISSED",
                    "record_id": anchor_event.record_id or None,
                    "anchor_stage": anchor_event.stage,
                    "anchor_stage_label": _stage_label(anchor_event.stage),
                    "terminal_stage": terminal_event.stage,
                    "terminal_stage_label": _stage_label(terminal_event.stage),
                    "signal_price": signal_price,
                    "ai_score": round(ai_score, 1),
                    "target_qty": _safe_int(
                        (budget_event.fields if budget_event else {}).get("qty"), 0
                    ),
                    "safe_budget": _safe_int(
                        (budget_event.fields if budget_event else {}).get(
                            "safe_budget"
                        ),
                        0,
                    ),
                    "budget_passed": bool(budget_event is not None),
                    "entry_armed": any(
                        event.stage in _ENTRY_ARMED_STAGES for event in attempt_events
                    ),
                    "buy_signal_count": len(buy_events),
                    "buy_intent_source": buy_intent_source,
                    **source_contract,
                    "stage_flow": [event.stage for event in attempt_events],
                    "blocker_counts": dict(blocker_counts),
                    "terminal_fields": dict(terminal_event.fields),
                    "rising_missed_fields": (
                        dict(rising_missed_event.fields) if rising_missed_event else {}
                    ),
                    "no_submit_reason": terminal_event.fields.get("no_submit_reason"),
                    "missed_submit_cohort": _missed_submit_cohort(
                        {
                            "terminal_stage": terminal_event.stage,
                            "terminal_fields": dict(terminal_event.fields),
                            "stage_flow": [event.stage for event in attempt_events],
                        }
                    ),
                }
            )
    return _dedupe_inferred_pre_submit_attempts(candidates)


def _resolve_anchor_price(
    signal_price: float, relevant: list[tuple[datetime, dict]]
) -> float:
    if signal_price > 0:
        return signal_price
    if not relevant:
        return 0.0
    first_candle = relevant[0][1]
    for key in ("시가", "현재가", "고가", "저가"):
        price = _safe_float(first_candle.get(key), 0.0)
        if price > 0:
            return price
    return 0.0


def _compute_window_metrics(
    candidate: dict, candles: list[dict], window_minutes: int
) -> dict:
    signal_dt = datetime.strptime(
        f"{candidate['signal_date']} {candidate['signal_time']}",
        "%Y-%m-%d %H:%M:%S",
    )
    start_dt = signal_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end_dt = start_dt + timedelta(minutes=window_minutes)

    relevant: list[tuple[datetime, dict]] = []
    for candle in candles:
        candle_dt = _parse_minute_time(
            str(candle.get("체결시간", "") or ""),
            candidate["signal_date"],
            str(candle.get("source_timestamp", "") or ""),
        )
        if candle_dt is None:
            continue
        if candle_dt < start_dt or candle_dt >= end_dt:
            continue
        relevant.append((candle_dt, candle))
    relevant.sort(key=lambda item: item[0])

    anchor_price = _resolve_anchor_price(
        float(candidate.get("signal_price", 0) or 0), relevant
    )
    if anchor_price <= 0 or not relevant:
        return {
            "entry_price_used": int(round(anchor_price)),
            "close_ret_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "hit_tp_05": False,
            "hit_sl_05": False,
            "tp05_before_sl05": False,
            "bars": len(relevant),
        }

    highs: list[float] = []
    lows: list[float] = []
    close_ret = 0.0
    first_tp_dt = None
    first_sl_dt = None

    for candle_dt, candle in relevant:
        high_p = _safe_float(candle.get("고가"), 0.0)
        low_p = _safe_float(candle.get("저가"), 0.0)
        close_p = _safe_float(candle.get("현재가"), 0.0)
        if high_p > 0:
            high_ret = ((high_p / anchor_price) - 1.0) * 100.0
            highs.append(high_ret)
            if first_tp_dt is None and high_ret >= _BUY_TP_PCT:
                first_tp_dt = candle_dt
        if low_p > 0:
            low_ret = ((low_p / anchor_price) - 1.0) * 100.0
            lows.append(low_ret)
            if first_sl_dt is None and low_ret <= _BUY_SL_PCT:
                first_sl_dt = candle_dt
        if close_p > 0:
            close_ret = ((close_p / anchor_price) - 1.0) * 100.0

    mfe_pct = max(highs) if highs else 0.0
    mae_pct = min(lows) if lows else 0.0
    return {
        "entry_price_used": int(round(anchor_price)),
        "close_ret_pct": round(close_ret, 3),
        "mfe_pct": round(mfe_pct, 3),
        "mae_pct": round(mae_pct, 3),
        "hit_tp_05": mfe_pct >= _BUY_TP_PCT,
        "hit_sl_05": mae_pct <= _BUY_SL_PCT,
        "tp05_before_sl05": bool(
            first_tp_dt is not None
            and (first_sl_dt is None or first_tp_dt <= first_sl_dt)
        ),
        "bars": len(relevant),
    }


def _confidence_tier(item: dict) -> str:
    price_source = str(item.get("price_source") or "")
    metrics_10m = item.get("metrics_10m", {}) or {}
    bars = _safe_int(metrics_10m.get("bars"), 0)
    if price_source == "explicit_target_buy_price":
        return "A"
    if bars >= 5:
        return "B"
    return "C"


def _classify_candidate(metrics_5m: dict, metrics_10m: dict) -> str:
    if bool(metrics_5m.get("tp05_before_sl05")):
        return "MISSED_WINNER"
    if bool(metrics_5m.get("hit_sl_05")) and not bool(metrics_5m.get("hit_tp_05")):
        return "AVOIDED_LOSER"

    mfe_10m = _safe_float(metrics_10m.get("mfe_pct"), 0.0)
    mae_10m = _safe_float(metrics_10m.get("mae_pct"), 0.0)
    close_10m = _safe_float(metrics_10m.get("close_ret_pct"), 0.0)
    if mfe_10m >= _BUY_MISSED_MFE_PCT and close_10m >= _BUY_MISSED_CLOSE_PCT:
        return "MISSED_WINNER"
    if mae_10m <= _BUY_AVOIDED_MAE_PCT and close_10m <= _BUY_AVOIDED_CLOSE_PCT:
        return "AVOIDED_LOSER"
    return "NEUTRAL"


def _clean_cycle_identity(value) -> str:
    candidate = str(value or "").strip()
    if not candidate or candidate.lower() in {
        "none",
        "null",
        "not_applicable",
        "not_applicable_runtime_record_id",
        "not_applicable_existing_runtime_record_id",
        "not_applicable_scanner_promotion_id",
    }:
        return ""
    return candidate


def _event_observed_price(event: EntryEvent) -> float:
    for key in (
        "current_price_observed",
        "current_price",
        "latest_price",
        "mark_price_at_submit",
        "submitted_order_price",
        "target_buy_price",
        "price",
    ):
        price = abs(_safe_float(event.fields.get(key), 0.0))
        if price > 0:
            return price
    return 0.0


def _event_market_observed_price(event: EntryEvent) -> float:
    """Return market observations only; never use intended/submitted order prices."""

    for key in (
        "current_price_observed",
        "current_price",
        "latest_price",
        "mark_price_at_submit",
    ):
        price = abs(_safe_float(event.fields.get(key), 0.0))
        if price > 0:
            return price
    return 0.0


def _watch_cycle_terminal_priority(stage: str) -> int:
    normalized = str(stage or "").strip()
    if normalized == "order_bundle_submitted":
        return 1000
    if normalized in {
        "entry_submit_revalidation_block",
        "pre_submit_entry_ai_authority_guard_block",
        "pre_submit_liquidity_guard_block",
        "pre_submit_overbought_pullback_guard_block",
        "pre_submit_weak_context_late_entry_guard_block",
        "real_weak_pullback_entry_block",
        "latency_block",
        "krx_direct_canary_live_ai_wait_submit_block",
        "rising_missed_tick_speed_entry_block",
    }:
        return 900
    if normalized in {
        "blocked_zero_qty",
        "auth_zero_qty",
        "blocked_cooldown",
        "ai_cooldown_blocked",
        "scalp_same_symbol_loss_reentry_blocked",
    }:
        return 800
    if normalized in {
        "scalp_entry_action_decision_snapshot",
        "blocked_ai_score",
        "first_ai_wait",
        "ai_confirmed_terminal_no_budget",
    }:
        return 700
    if normalized in {
        "blocked_strength_momentum",
        "blocked_vpw",
        "blocked_liquidity",
        "blocked_overbought",
        "blocked_gap_from_scan",
        "blocked_big_bite_hard_gate",
    }:
        return 600
    if normalized == "scalping_scanner_real_source_guard_block":
        return 500
    if normalized == _SCANNER_EVICTION_STAGE:
        return 300
    if normalized == _SCANNER_ATTACH_STAGE:
        return 200
    if normalized == _SCANNER_PROMOTED_STAGE:
        return 100
    return 0


def _watch_cycle_blocker_class(stage: str, reason: str, ai_action: str) -> str:
    stage_text = str(stage or "").lower()
    reason_text = str(reason or "").lower()
    if str(ai_action or "").upper() == "DROP":
        return "ai_veto"
    if "ai_authority_guard" in stage_text or "ai_veto" in reason_text:
        return "ai_veto"
    if any(
        token in f"{stage_text} {reason_text}"
        for token in (
            "hard_stop",
            "protect_stop",
            "emergency",
            "account",
            "quantity",
            "cooldown",
            "duplicate",
            "manual_control",
            "same_symbol",
        )
    ):
        return "hard_safety_or_broker_guard"
    if any(
        token in f"{stage_text} {reason_text}"
        for token in ("stale", "conflict", "source_guard", "source_quality")
    ):
        return "source_quality_guard"
    if (
        stage_text
        in {
            "",
            _SCANNER_PROMOTED_STAGE,
            _SCANNER_ATTACH_STAGE,
            _SCANNER_EVICTION_STAGE,
            "runtime_target_attach_skipped",
            "no_entry_evaluation_reached",
            "scanner_promotion_not_attached",
        }
        or stage_text.startswith("scalping_scanner_")
        or stage_text.startswith("rising_missed_watch_")
    ):
        return "upstream_participation_gap"
    return "bounded_strategy_or_execution_gate"


def _latest_cycle_ai_action(events: list[EntryEvent]) -> str:
    for event in reversed(events):
        for key in (
            "latest_ai_action",
            "pre_submit_ai_action",
            "action",
            "chosen_action",
        ):
            action = str(event.fields.get(key) or "").strip().upper()
            if action in {"BUY", "WAIT", "DROP"}:
                return action
            if action == "NO_BUY_AI":
                return "WAIT"
    return "UNKNOWN"


def _observed_price_horizon_metrics(
    *,
    anchor_dt: datetime,
    anchor_price: float,
    price_points: list[tuple[datetime, float]],
    horizon_min: int,
) -> dict:
    end_dt = anchor_dt + timedelta(minutes=horizon_min)
    relevant = [
        (observed_at, price)
        for observed_at, price in price_points
        if anchor_dt < observed_at <= end_dt and price > 0
    ]
    if anchor_price <= 0 or not relevant:
        return {
            "entry_price_used": int(round(anchor_price)),
            "close_ret_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "hit_tp_05": False,
            "hit_sl_05": False,
            "tp05_before_sl05": False,
            "bars": 0,
            "latest_offset_sec": 0.0,
            "source_quality_state": "source_gap_insufficient_post_reference_price",
        }

    returns = [
        (((price / anchor_price) - 1.0) * 100.0, observed_at)
        for observed_at, price in relevant
    ]
    first_tp = next(
        (observed_at for value, observed_at in returns if value >= _BUY_TP_PCT),
        None,
    )
    first_sl = next(
        (observed_at for value, observed_at in returns if value <= _BUY_SL_PCT),
        None,
    )
    latest_offset_sec = max(
        (observed_at - anchor_dt).total_seconds() for observed_at, _price in relevant
    )
    minimum_complete_offset_sec = max(1.0, horizon_min * 60.0 * 0.8)
    minimum_observation_count = 1 if horizon_min == 1 else 2 if horizon_min == 3 else 3
    if len(relevant) < minimum_observation_count:
        source_quality_state = "sparse_horizon"
    elif latest_offset_sec < minimum_complete_offset_sec:
        source_quality_state = "partial_horizon"
    else:
        source_quality_state = "pass"
    values = [value for value, _observed_at in returns]
    return {
        "entry_price_used": int(round(anchor_price)),
        "close_ret_pct": round(values[-1], 3),
        "mfe_pct": round(max(values), 3),
        "mae_pct": round(min(values), 3),
        "hit_tp_05": max(values) >= _BUY_TP_PCT,
        "hit_sl_05": min(values) <= _BUY_SL_PCT,
        "tp05_before_sl05": bool(
            first_tp is not None and (first_sl is None or first_tp < first_sl)
        ),
        "bars": len(relevant),
        "latest_offset_sec": round(latest_offset_sec, 3),
        "source_quality_state": source_quality_state,
    }


def _metric_source_quality_state(metrics: dict, horizon_min: int) -> str:
    explicit = str(metrics.get("source_quality_state") or "").strip()
    if explicit:
        return explicit
    bars = _safe_int(metrics.get("bars"), 0)
    if bars <= 0:
        return "source_gap_insufficient_post_reference_price"
    if bars < horizon_min:
        return "partial_horizon"
    return "pass"


def _build_watch_cycle_participation_ledger(
    target_date: str,
    events: list[EntryEvent],
    evaluations: list[dict],
) -> dict:
    """Collapse scanner promotions and repeated attempts into unique watch cycles."""

    promotions: dict[str, EntryEvent] = {}
    for event in events:
        if event.stage != _SCANNER_PROMOTED_STAGE:
            continue
        promotion_id = _clean_cycle_identity(event.fields.get("scanner_promotion_id"))
        if promotion_id:
            promotions[promotion_id] = event

    cycles: dict[str, dict] = {}
    runtime_cycle_by_id: dict[str, str] = {}
    promotion_cycle: dict[str, str] = {}

    def _new_cycle(
        cycle_id: str,
        *,
        stock_code: str,
        stock_name: str,
        cycle_type: str,
        runtime_record_id: str = "",
    ) -> dict:
        return cycles.setdefault(
            cycle_id,
            {
                "watch_cycle_id": cycle_id,
                "cycle_type": cycle_type,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "runtime_record_id": runtime_record_id,
                "promotion_ids": set(),
                "events": [],
                "event_keys": set(),
                "evaluations": [],
            },
        )

    def _append_event(cycle: dict, event: EntryEvent) -> None:
        event_key = (event.emitted_at, event.stage, event.record_id)
        if event_key in cycle["event_keys"]:
            return
        cycle["event_keys"].add(event_key)
        cycle["events"].append(event)

    for event in events:
        if event.stage != _SCANNER_ATTACH_STAGE:
            continue
        fields = event.fields
        outcome = str(fields.get("runtime_target_attach_outcome") or "").lower()
        runtime_record_id = _clean_cycle_identity(fields.get("runtime_record_id"))
        existing_record_id = _clean_cycle_identity(
            fields.get("existing_runtime_record_id")
        )
        promotion_id = _clean_cycle_identity(fields.get("scanner_promotion_id"))
        resolved_runtime_id = (
            runtime_record_id if outcome == "attached" else existing_record_id
        )
        if not resolved_runtime_id:
            continue
        cycle_id = f"{target_date}:SCANNER:{resolved_runtime_id}"
        cycle = _new_cycle(
            cycle_id,
            stock_code=event.code,
            stock_name=event.name,
            cycle_type="runtime_watch",
            runtime_record_id=resolved_runtime_id,
        )
        runtime_cycle_by_id[resolved_runtime_id] = cycle_id
        if promotion_id:
            promotion_cycle[promotion_id] = cycle_id
            cycle["promotion_ids"].add(promotion_id)
            promotion_event = promotions.get(promotion_id)
            if promotion_event is not None:
                _append_event(cycle, promotion_event)
        _append_event(cycle, event)

    for promotion_id, promotion_event in promotions.items():
        if promotion_id in promotion_cycle:
            continue
        cycle_id = f"{target_date}:PROMOTION:{promotion_id}"
        cycle = _new_cycle(
            cycle_id,
            stock_code=promotion_event.code,
            stock_name=promotion_event.name,
            cycle_type="promotion_not_attached",
        )
        promotion_cycle[promotion_id] = cycle_id
        cycle["promotion_ids"].add(promotion_id)
        _append_event(cycle, promotion_event)

    for event in events:
        promotion_id = _clean_cycle_identity(event.fields.get("scanner_promotion_id"))
        runtime_record_id = (
            _clean_cycle_identity(event.record_id)
            or _clean_cycle_identity(event.fields.get("runtime_record_id"))
            or _clean_cycle_identity(event.fields.get("existing_runtime_record_id"))
        )
        cycle_id = ""
        if runtime_record_id:
            cycle_id = runtime_cycle_by_id.get(runtime_record_id, "")
        if not cycle_id and promotion_id:
            cycle_id = promotion_cycle.get(promotion_id, "")
        if cycle_id:
            _append_event(cycles[cycle_id], event)

    events_by_record: dict[tuple[str, str], list[EntryEvent]] = defaultdict(list)
    for event in events:
        record_id = _clean_cycle_identity(event.record_id)
        if record_id:
            events_by_record[(event.code, record_id)].append(event)

    for evaluation in evaluations:
        record_id = _clean_cycle_identity(evaluation.get("record_id"))
        stock_code = str(evaluation.get("stock_code") or "")
        cycle_id = runtime_cycle_by_id.get(record_id, "") if record_id else ""
        if not cycle_id:
            fallback_identity = record_id or str(
                evaluation.get("candidate_id") or "unknown"
            )
            cycle_id = f"{target_date}:ENTRY:{evaluation.get('stock_code')}:{fallback_identity}"
            _new_cycle(
                cycle_id,
                stock_code=stock_code,
                stock_name=str(evaluation.get("stock_name") or ""),
                cycle_type="entry_attempt_fallback",
                runtime_record_id=record_id,
            )
        cycle = cycles[cycle_id]
        cycle["evaluations"].append(evaluation)
        for event in events_by_record.get((stock_code, record_id), []):
            _append_event(cycle, event)

    price_points_by_stock: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    for event in events:
        observed_at = _parse_event_dt(event.emitted_at)
        observed_price = _event_market_observed_price(event)
        if observed_at is None or observed_price <= 0:
            continue
        price_points_by_stock[event.code].append((observed_at, observed_price))
    for points in price_points_by_stock.values():
        points.sort(key=lambda item: item[0])

    ledger_rows: list[dict] = []
    for cycle in cycles.values():
        cycle_events = sorted(
            cycle["events"],
            key=lambda item: _parse_event_dt(item.emitted_at) or datetime.min,
        )
        cycle_evaluations = sorted(
            cycle["evaluations"],
            key=lambda item: (
                str(item.get("signal_date") or ""),
                str(item.get("signal_time") or ""),
            ),
        )
        submitted = any(
            str(item.get("attempt_status") or "") == "ENTERED"
            for item in cycle_evaluations
        ) or any(event.stage == "order_bundle_submitted" for event in cycle_events)

        terminal_candidates: list[tuple[int, datetime, str, str, str]] = []
        for item in cycle_evaluations:
            stage = str(item.get("terminal_stage") or "")
            terminal_fields = (
                item.get("terminal_fields")
                if isinstance(item.get("terminal_fields"), dict)
                else {}
            )
            reason = str(
                terminal_fields.get("reason")
                or terminal_fields.get("no_submit_reason")
                or terminal_fields.get("chosen_action")
                or item.get("no_submit_reason")
                or ""
            )
            emitted_at = (
                _parse_event_dt(f"{item.get('signal_date')} {item.get('signal_time')}")
                or datetime.min
            )
            terminal_candidates.append(
                (
                    _watch_cycle_terminal_priority(stage),
                    emitted_at,
                    stage,
                    reason,
                    stage,
                )
            )
        for event in cycle_events:
            if event.stage == _SCANNER_PROMOTED_STAGE:
                continue
            if (
                event.stage == _SCANNER_ATTACH_STAGE
                and str(event.fields.get("runtime_target_attach_outcome") or "").lower()
                == "attached"
            ):
                continue
            candidate_stage = event.stage
            if event.stage == _SCANNER_ATTACH_STAGE:
                candidate_stage = "runtime_target_attach_skipped"
            elif event.stage == _SCANNER_EVICTION_STAGE:
                candidate_stage = (
                    _clean_cycle_identity(event.fields.get("terminal_stage"))
                    or event.stage
                )
            priority = _watch_cycle_terminal_priority(event.stage)
            if priority <= 0:
                continue
            reason = str(
                event.fields.get("reason")
                or event.fields.get("runtime_target_attach_reason")
                or event.fields.get("terminal_reason")
                or event.fields.get("eviction_reason")
                or event.fields.get("chosen_action")
                or ""
            )
            terminal_candidates.append(
                (
                    priority,
                    _parse_event_dt(event.emitted_at) or datetime.min,
                    candidate_stage,
                    reason,
                    event.stage,
                )
            )
        if submitted:
            terminal_stage = "order_bundle_submitted"
            terminal_reason = "submitted"
        elif cycle["cycle_type"] == "promotion_not_attached" and not any(
            event.stage == _SCANNER_ATTACH_STAGE for event in cycle_events
        ):
            terminal_stage = "scanner_promotion_not_attached"
            terminal_reason = "runtime_target_attach_not_observed"
            terminal_source_stage = _SCANNER_PROMOTED_STAGE
        elif terminal_candidates:
            _priority, _at, terminal_stage, terminal_reason, terminal_source_stage = (
                max(terminal_candidates, key=lambda item: (item[0], item[1]))
            )
        else:
            terminal_stage = "no_entry_evaluation_reached"
            terminal_reason = "no_terminal_entry_stage_observed"
            terminal_source_stage = "watch_cycle_aggregation"
        if submitted:
            terminal_source_stage = "order_bundle_submitted"

        reference_evaluation = next(
            (
                item
                for item in cycle_evaluations
                if str(item.get("attempt_status") or "") == "MISSED"
            ),
            cycle_evaluations[0] if cycle_evaluations else None,
        )
        if reference_evaluation is not None:
            reference_dt = _parse_event_dt(
                f"{reference_evaluation.get('signal_date')} "
                f"{reference_evaluation.get('signal_time')}"
            )
            reference_price = _safe_float(
                reference_evaluation.get("entry_price_used"), 0.0
            )
            reference_source = "first_missed_entry_attempt"
        else:
            reference_event = next(
                (
                    event
                    for event in cycle_events
                    if event.stage in {_SCANNER_ATTACH_STAGE, _SCANNER_PROMOTED_STAGE}
                    and _event_observed_price(event) > 0
                ),
                cycle_events[0] if cycle_events else None,
            )
            reference_dt = (
                _parse_event_dt(reference_event.emitted_at)
                if reference_event is not None
                else None
            )
            reference_price = (
                _event_observed_price(reference_event)
                if reference_event is not None
                else 0.0
            )
            reference_source = "scanner_watch_or_promotion_price"

        horizon_metrics: dict[str, dict] = {}
        if reference_evaluation is not None:
            stored_horizons = reference_evaluation.get("forward_horizon_metrics")
            if isinstance(stored_horizons, dict):
                horizon_metrics = {
                    str(key): dict(value)
                    for key, value in stored_horizons.items()
                    if isinstance(value, dict)
                }
        if reference_dt is not None:
            price_points = price_points_by_stock.get(cycle["stock_code"], [])
            for horizon_min in _WATCH_CYCLE_HORIZONS_MIN:
                key = str(horizon_min)
                if key in horizon_metrics:
                    continue
                horizon_metrics[key] = _observed_price_horizon_metrics(
                    anchor_dt=reference_dt,
                    anchor_price=reference_price,
                    price_points=price_points,
                    horizon_min=horizon_min,
                )

        reference_venue = (
            str(reference_evaluation.get("effective_venue") or "").strip().upper()
            if reference_evaluation is not None
            else ""
        )
        if (
            reference_evaluation is not None
            and bool(reference_evaluation.get("venue_tuning_allowed"))
            and reference_venue in _EXPLICIT_TRADABLE_VENUES
        ):
            effective_venue = reference_venue
            venue_source_quality = "pass"
            venue_resolution = "reference_attempt_contract"
        elif reference_evaluation is not None:
            effective_venue = "UNKNOWN"
            venue_source_quality = str(
                reference_evaluation.get("venue_source_quality") or "missing"
            )
            venue_resolution = str(
                reference_evaluation.get("venue_resolution")
                or "reference_attempt_contract_blocked"
            )
        else:
            authoritative_venues: set[str] = set()
            fallback_venues: set[str] = set()
            scoped_events = [
                event
                for event in cycle_events
                if reference_dt is None
                or (_parse_event_dt(event.emitted_at) or datetime.max) <= reference_dt
            ]
            for event in scoped_events:
                for key in ("rising_missed_effective_venue", "effective_venue"):
                    venue = str(event.fields.get(key) or "").strip().upper()
                    if venue in _EXPLICIT_TRADABLE_VENUES:
                        authoritative_venues.add(venue)
                venue = str(event.fields.get("venue") or "").strip().upper()
                if venue in _EXPLICIT_TRADABLE_VENUES:
                    fallback_venues.add(venue)
            if len(authoritative_venues) == 1:
                effective_venue = next(iter(authoritative_venues))
                venue_source_quality = "pass"
                venue_resolution = "reference_event_authoritative"
            elif len(authoritative_venues) > 1:
                effective_venue = "UNKNOWN"
                venue_source_quality = "conflict"
                venue_resolution = "reference_event_authoritative_conflict"
            elif len(fallback_venues) == 1:
                effective_venue = next(iter(fallback_venues))
                venue_source_quality = "pass"
                venue_resolution = "reference_event_fallback"
            elif len(fallback_venues) > 1:
                effective_venue = "UNKNOWN"
                venue_source_quality = "conflict"
                venue_resolution = "reference_event_fallback_conflict"
            else:
                effective_venue = "UNKNOWN"
                venue_source_quality = "missing"
                venue_resolution = "reference_event_venue_missing"

        reference_session = (
            str(reference_evaluation.get("market_session_bucket") or "").strip()
            if reference_evaluation is not None
            else ""
        )
        if reference_session:
            market_session_bucket = reference_session
            market_session_source_quality = "pass"
        else:
            session_observations: list[tuple[datetime, str]] = []
            for event in cycle_events:
                event_dt = _parse_event_dt(event.emitted_at)
                if event_dt is None or (
                    reference_dt is not None and event_dt > reference_dt
                ):
                    continue
                for key in (
                    "rising_missed_market_session_bucket",
                    "market_session_bucket",
                ):
                    session = str(event.fields.get(key) or "").strip()
                    if session:
                        session_observations.append((event_dt, session))
            if session_observations:
                latest_session_dt = max(item[0] for item in session_observations)
                latest_sessions = {
                    session
                    for observed_at, session in session_observations
                    if observed_at == latest_session_dt
                }
                if len(latest_sessions) == 1:
                    market_session_bucket = next(iter(latest_sessions))
                    market_session_source_quality = "pass"
                else:
                    market_session_bucket = "UNKNOWN"
                    market_session_source_quality = "conflict"
            else:
                market_session_bucket = "UNKNOWN"
                market_session_source_quality = "missing"
        ai_action = _latest_cycle_ai_action(cycle_events)
        blocker_class = _watch_cycle_blocker_class(
            terminal_stage, terminal_reason, ai_action
        )
        primary_metrics = horizon_metrics.get("20", {})
        primary_source_quality = _metric_source_quality_state(primary_metrics, 20)
        gross_close_ret_pct = _safe_float(primary_metrics.get("close_ret_pct"), 0.0)
        cost_adjusted_return_pct = round(
            gross_close_ret_pct - _WATCH_CYCLE_ESTIMATED_ROUND_TRIP_COST_PCT, 4
        )
        notional = (
            _safe_int(reference_evaluation.get("counterfactual_notional_krw"), 0)
            if reference_evaluation is not None
            else 0
        )
        estimated_net_pnl = (
            int(round(notional * cost_adjusted_return_pct / 100.0))
            if notional > 0 and primary_source_quality == "pass"
            else None
        )
        if primary_source_quality != "pass":
            opportunity_label = "source_gap_or_partial_horizon"
        elif bool(primary_metrics.get("tp05_before_sl05")):
            opportunity_label = "gross_target_first"
        elif bool(primary_metrics.get("hit_sl_05")):
            opportunity_label = "adverse_stop_first"
        else:
            opportunity_label = "no_hit_within_20m"

        actionable_missed_winner = bool(
            not submitted
            and opportunity_label == "gross_target_first"
            and cost_adjusted_return_pct > 0
            and notional > 0
            and effective_venue in _EXPLICIT_TRADABLE_VENUES
            and venue_source_quality == "pass"
            and market_session_source_quality == "pass"
            and blocker_class == "bounded_strategy_or_execution_gate"
            and ai_action != "DROP"
        )
        ledger_rows.append(
            {
                "watch_cycle_id": cycle["watch_cycle_id"],
                "cycle_type": cycle["cycle_type"],
                "stock_code": cycle["stock_code"],
                "stock_name": cycle["stock_name"],
                "runtime_record_id": cycle["runtime_record_id"] or None,
                "scanner_promotion_ids": sorted(cycle["promotion_ids"]),
                "scanner_promotion_count": len(cycle["promotion_ids"]),
                "attempt_count": len(cycle_evaluations),
                "participation_state": "SUBMITTED" if submitted else "UNSUBMITTED",
                "single_terminal_blocker": terminal_stage,
                "single_terminal_blocker_reason": terminal_reason,
                "single_terminal_blocker_source_stage": terminal_source_stage,
                "single_terminal_blocker_class": blocker_class,
                "latest_ai_action": ai_action,
                "reference_time": (
                    reference_dt.isoformat() if reference_dt is not None else None
                ),
                "reference_price": int(round(reference_price)),
                "reference_price_source": reference_source,
                "effective_venue": effective_venue,
                "venue_source_quality": venue_source_quality,
                "venue_resolution": venue_resolution,
                "market_session_bucket": market_session_bucket,
                "market_session_source_quality": market_session_source_quality,
                "forward_horizon_metrics": horizon_metrics,
                "primary_horizon_min": 20,
                "primary_source_quality_state": primary_source_quality,
                "opportunity_label": opportunity_label,
                "estimated_round_trip_cost_pct": (
                    _WATCH_CYCLE_ESTIMATED_ROUND_TRIP_COST_PCT
                ),
                "cost_adjusted_counterfactual_return_pct": (
                    cost_adjusted_return_pct
                    if primary_source_quality == "pass"
                    else None
                ),
                "counterfactual_notional_krw": notional,
                "estimated_counterfactual_net_pnl_krw": estimated_net_pnl,
                "actionable_missed_winner": actionable_missed_winner,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": submitted,
                "broker_order_forbidden": True,
            }
        )

    ledger_rows.sort(
        key=lambda row: (
            str(row.get("reference_time") or ""),
            str(row.get("watch_cycle_id") or ""),
        )
    )
    unsubmitted_rows = [
        row for row in ledger_rows if row["participation_state"] == "UNSUBMITTED"
    ]
    ev_rows = [
        row
        for row in unsubmitted_rows
        if row["primary_source_quality_state"] == "pass"
        and row["venue_source_quality"] == "pass"
        and row["market_session_source_quality"] == "pass"
        and int(row["counterfactual_notional_krw"] or 0) > 0
        and row["cost_adjusted_counterfactual_return_pct"] is not None
    ]
    notional_sum = sum(int(row["counterfactual_notional_krw"] or 0) for row in ev_rows)
    notional_weighted_ev_pct = (
        round(
            sum(
                float(row["cost_adjusted_counterfactual_return_pct"])
                * int(row["counterfactual_notional_krw"])
                for row in ev_rows
            )
            / notional_sum,
            4,
        )
        if notional_sum > 0
        else None
    )
    blocker_counts = Counter(
        str(row["single_terminal_blocker"]) for row in unsubmitted_rows
    )
    venue_counts = Counter(str(row["effective_venue"]) for row in ledger_rows)
    source_quality_counts = Counter(
        str(row["primary_source_quality_state"]) for row in ledger_rows
    )
    return {
        "schema_version": 1,
        "contract": {
            "metric_role": "counterfactual_opportunity_attribution",
            "decision_authority": "watch_cycle_source_only_no_runtime_apply",
            "window_policy": (
                "unique_scanner_runtime_watch_or_unattached_promotion_cycle_"
                "with_1_3_5_10_20_30_60m_forward_observation"
            ),
            "sample_floor": "rolling_closed_source_quality_valid_cycles_ge_20",
            "primary_decision_metric": "notional_weighted_ev_pct",
            "source_quality_gate": (
                "single_conflict_free_explicit_venue_and_complete_20m_price_"
                "horizon_and_counterfactual_notional"
            ),
            "forbidden_uses": [
                "daily_only_threshold_mutation",
                "broker_order_submit",
                "provider_route_change",
                "bot_restart",
                "hard_safety_or_broker_guard_bypass",
                "unknown_or_conflicting_venue_tuning",
                "gross_mfe_as_realized_pnl",
                "promotion_attempt_count_as_unique_symbol_count",
            ],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "summary": {
            "unique_watch_cycle_count": len(ledger_rows),
            "unique_stock_count": len({str(row["stock_code"]) for row in ledger_rows}),
            "runtime_watch_cycle_count": sum(
                1 for row in ledger_rows if row["cycle_type"] == "runtime_watch"
            ),
            "unattached_promotion_cycle_count": sum(
                1
                for row in ledger_rows
                if row["cycle_type"] == "promotion_not_attached"
            ),
            "submitted_cycle_count": len(ledger_rows) - len(unsubmitted_rows),
            "unsubmitted_cycle_count": len(unsubmitted_rows),
            "actionable_missed_winner_count": sum(
                1 for row in unsubmitted_rows if row["actionable_missed_winner"]
            ),
            "unsubmitted_ev_eligible_cycle_count": len(ev_rows),
            "complete_20m_price_cycle_count": sum(
                1
                for row in ledger_rows
                if row["primary_source_quality_state"] == "pass"
            ),
            "venue_source_quality_valid_cycle_count": sum(
                1 for row in ledger_rows if row["venue_source_quality"] == "pass"
            ),
            "market_session_source_quality_valid_cycle_count": sum(
                1
                for row in ledger_rows
                if row["market_session_source_quality"] == "pass"
            ),
            "unsubmitted_counterfactual_notional_available_cycle_count": sum(
                1
                for row in unsubmitted_rows
                if int(row["counterfactual_notional_krw"] or 0) > 0
            ),
            "unsubmitted_ev_ineligible_cycle_count": len(unsubmitted_rows)
            - len(ev_rows),
            "counterfactual_notional_krw": notional_sum,
            "notional_weighted_ev_pct": notional_weighted_ev_pct,
            "estimated_counterfactual_net_pnl_krw": sum(
                int(row["estimated_counterfactual_net_pnl_krw"] or 0) for row in ev_rows
            ),
            "single_terminal_blocker_counts": dict(blocker_counts),
            "effective_venue_counts": dict(venue_counts),
            "primary_source_quality_counts": dict(source_quality_counts),
        },
        "rows": ledger_rows,
    }


def _build_blocker_outcome_metrics(items: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        stage = str(item.get("terminal_stage") or "-")
        buckets[stage].append(item)

    metrics: dict[str, dict] = {}
    for stage, rows in sorted(buckets.items()):
        total = len(rows)
        missed = sum(
            1 for row in rows if str(row.get("outcome") or "") == "MISSED_WINNER"
        )
        avoided = sum(
            1 for row in rows if str(row.get("outcome") or "") == "AVOIDED_LOSER"
        )
        neutral = sum(1 for row in rows if str(row.get("outcome") or "") == "NEUTRAL")
        estimated_pnl = int(
            sum(
                _safe_int(row.get("estimated_counterfactual_pnl_10m_krw"), 0)
                for row in rows
            )
        )
        metrics[stage] = {
            "stage": stage,
            "stage_label": _stage_label(stage),
            "evaluated_candidates": total,
            "missed_winner_count": missed,
            "avoided_loser_count": avoided,
            "neutral_count": neutral,
            "missed_winner_rate": _ratio(missed, total),
            "avoided_loser_rate": _ratio(avoided, total),
            "avg_close_5m_pct": _avg(
                [
                    _safe_float((row.get("metrics_5m") or {}).get("close_ret_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_close_10m_pct": _avg(
                [
                    _safe_float(
                        (row.get("metrics_10m") or {}).get("close_ret_pct"), 0.0
                    )
                    for row in rows
                ]
            ),
            "avg_mfe_10m_pct": _avg(
                [
                    _safe_float((row.get("metrics_10m") or {}).get("mfe_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_mae_10m_pct": _avg(
                [
                    _safe_float((row.get("metrics_10m") or {}).get("mae_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_close_15m_pct": _avg(
                [
                    _safe_float(
                        (row.get("metrics_15m") or {}).get("close_ret_pct"), 0.0
                    )
                    for row in rows
                ]
            ),
            "avg_mfe_15m_pct": _avg(
                [
                    _safe_float((row.get("metrics_15m") or {}).get("mfe_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_mae_15m_pct": _avg(
                [
                    _safe_float((row.get("metrics_15m") or {}).get("mae_pct"), 0.0)
                    for row in rows
                ]
            ),
            "estimated_counterfactual_pnl_10m_krw_sum": estimated_pnl,
            "candidate_ids": [str(row.get("candidate_id") or "") for row in rows[:20]],
        }
    return metrics


def _build_cohort_outcome_metrics(items: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        buckets[str(item.get("missed_submit_cohort") or "uncategorized")].append(item)

    metrics: dict[str, dict] = {}
    for cohort, rows in sorted(buckets.items()):
        total = len(rows)
        missed = sum(
            1 for row in rows if str(row.get("outcome") or "") == "MISSED_WINNER"
        )
        avoided = sum(
            1 for row in rows if str(row.get("outcome") or "") == "AVOIDED_LOSER"
        )
        metrics[cohort] = {
            "cohort": cohort,
            "evaluated_candidates": total,
            "missed_winner_rate": _ratio(missed, total),
            "avoided_loser_rate": _ratio(avoided, total),
            "avg_close_10m_pct": _avg(
                [
                    _safe_float(
                        (row.get("metrics_10m") or {}).get("close_ret_pct"), 0.0
                    )
                    for row in rows
                ]
            ),
            "avg_mfe_10m_pct": _avg(
                [
                    _safe_float((row.get("metrics_10m") or {}).get("mfe_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_mae_10m_pct": _avg(
                [
                    _safe_float((row.get("metrics_10m") or {}).get("mae_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_close_15m_pct": _avg(
                [
                    _safe_float(
                        (row.get("metrics_15m") or {}).get("close_ret_pct"), 0.0
                    )
                    for row in rows
                ]
            ),
            "avg_mfe_15m_pct": _avg(
                [
                    _safe_float((row.get("metrics_15m") or {}).get("mfe_pct"), 0.0)
                    for row in rows
                ]
            ),
            "avg_mae_15m_pct": _avg(
                [
                    _safe_float((row.get("metrics_15m") or {}).get("mae_pct"), 0.0)
                    for row in rows
                ]
            ),
        }
    return metrics


def _rising_missed_seen(item: dict) -> bool:
    return any(
        str(stage or "") == _RISING_MISSED_STAGE
        for stage in (item.get("stage_flow") or [])
    )


def _rising_missed_stage_count(item: dict) -> int:
    return sum(
        1
        for stage in (item.get("stage_flow") or [])
        if str(stage or "") == _RISING_MISSED_STAGE
    )


def _rising_missed_source_field(item: dict, key: str) -> str:
    direct_value = item.get(key)
    if direct_value not in (None, ""):
        return str(direct_value)
    for field_name in ("rising_missed_fields", "terminal_fields"):
        fields = item.get(field_name)
        if isinstance(fields, dict):
            value = fields.get(key)
            if value not in (None, ""):
                return str(value)
    return ""


def _rising_missed_postclose_label(item: dict) -> str:
    if not _rising_missed_seen(item):
        return "not_rising_missed"
    outcome = str(item.get("outcome") or "NEUTRAL").upper()
    if outcome == "MISSED_WINNER":
        return "rising_missed_missed_winner_positive"
    if outcome == "AVOIDED_LOSER":
        return "rising_missed_avoided_loser_negative"
    return "rising_missed_neutral"


def _build_rising_missed_refinement_metrics(items: list[dict]) -> dict:
    rising_rows = [item for item in items if _rising_missed_seen(item)]
    total = len(items)
    rising_total = len(rising_rows)
    total_missed_winners = sum(
        1 for item in items if str(item.get("outcome") or "") == "MISSED_WINNER"
    )
    positive = sum(
        1 for item in rising_rows if str(item.get("outcome") or "") == "MISSED_WINNER"
    )
    negative = sum(
        1 for item in rising_rows if str(item.get("outcome") or "") == "AVOIDED_LOSER"
    )
    neutral = sum(
        1 for item in rising_rows if str(item.get("outcome") or "") == "NEUTRAL"
    )

    def _bucket_metrics(key_fn) -> list[dict]:
        buckets: dict[str, list[dict]] = defaultdict(list)
        for item in rising_rows:
            key = str(key_fn(item) or "-")
            buckets[key].append(item)
        rows: list[dict] = []
        for key, bucket_rows in sorted(
            buckets.items(), key=lambda pair: (-len(pair[1]), pair[0])
        ):
            bucket_total = len(bucket_rows)
            bucket_positive = sum(
                1
                for row in bucket_rows
                if str(row.get("outcome") or "") == "MISSED_WINNER"
            )
            bucket_negative = sum(
                1
                for row in bucket_rows
                if str(row.get("outcome") or "") == "AVOIDED_LOSER"
            )
            rows.append(
                {
                    "key": key,
                    "evaluated_candidates": bucket_total,
                    "missed_winner_count": bucket_positive,
                    "avoided_loser_count": bucket_negative,
                    "neutral_count": bucket_total - bucket_positive - bucket_negative,
                    "missed_winner_rate": _ratio(bucket_positive, bucket_total),
                    "avoided_loser_rate": _ratio(bucket_negative, bucket_total),
                    "avg_mfe_10m_pct": _avg(
                        [
                            _safe_float(
                                (row.get("metrics_10m") or {}).get("mfe_pct"), 0.0
                            )
                            for row in bucket_rows
                        ]
                    ),
                    "avg_mae_10m_pct": _avg(
                        [
                            _safe_float(
                                (row.get("metrics_10m") or {}).get("mae_pct"), 0.0
                            )
                            for row in bucket_rows
                        ]
                    ),
                    "avg_close_15m_pct": _avg(
                        [
                            _safe_float(
                                (row.get("metrics_15m") or {}).get("close_ret_pct"), 0.0
                            )
                            for row in bucket_rows
                        ]
                    ),
                    "avg_mfe_15m_pct": _avg(
                        [
                            _safe_float(
                                (row.get("metrics_15m") or {}).get("mfe_pct"), 0.0
                            )
                            for row in bucket_rows
                        ]
                    ),
                    "avg_mae_15m_pct": _avg(
                        [
                            _safe_float(
                                (row.get("metrics_15m") or {}).get("mae_pct"), 0.0
                            )
                            for row in bucket_rows
                        ]
                    ),
                }
            )
        return rows

    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "postclose_source_only_refinement_no_runtime_apply",
        "window_policy": "same_day_missed_entry_counterfactual_rows",
        "sample_floor": 1,
        "primary_decision_metric": "diagnostic_win_rate",
        "source_quality_gate": "pipeline_stage_flow_and_counterfactual_outcome_present",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "intraday_threshold_mutation",
            "broker_order_submit",
            "provider_route_change",
            "bot_restart_trigger",
            "forced_scout_success_counting",
            "real_execution_quality_approval",
        ],
        "evaluated_candidates": total,
        "rising_missed_candidate_count": rising_total,
        "rising_missed_candidate_rate": _ratio(rising_total, total),
        "rising_missed_missed_winner_count": positive,
        "rising_missed_avoided_loser_count": negative,
        "rising_missed_neutral_count": neutral,
        "rising_missed_missed_winner_rate": _ratio(positive, rising_total),
        "rising_missed_avoided_loser_rate": _ratio(negative, rising_total),
        "rising_missed_share_of_all_missed_winners": _ratio(
            positive, total_missed_winners
        ),
        "by_terminal_stage": _bucket_metrics(lambda item: item.get("terminal_stage")),
        "by_source_signature": _bucket_metrics(
            lambda item: _rising_missed_source_field(item, "source_signature") or "-"
        ),
        "by_scanner_promotion_reason": _bucket_metrics(
            lambda item: _rising_missed_source_field(item, "scanner_promotion_reason")
            or "-"
        ),
    }


def _build_rising_missed_refinement_action_plan(metrics: dict) -> dict:
    positive_candidates: list[dict] = []
    exclusion_candidates: list[dict] = []
    hold_sample_candidates: list[dict] = []
    min_sample = 3

    def _candidate(
        axis: str, row: dict, disposition: str, next_route: str, recommended_use: str
    ) -> dict:
        return {
            "axis": axis,
            "key": str(row.get("key") or "-"),
            "disposition": disposition,
            "next_route": next_route,
            "recommended_use": recommended_use,
            "evaluated_candidates": int(
                _safe_int(row.get("evaluated_candidates"), 0) or 0
            ),
            "missed_winner_count": int(
                _safe_int(row.get("missed_winner_count"), 0) or 0
            ),
            "avoided_loser_count": int(
                _safe_int(row.get("avoided_loser_count"), 0) or 0
            ),
            "neutral_count": int(_safe_int(row.get("neutral_count"), 0) or 0),
            "missed_winner_rate": _safe_float(row.get("missed_winner_rate"), 0.0)
            or 0.0,
            "avoided_loser_rate": _safe_float(row.get("avoided_loser_rate"), 0.0)
            or 0.0,
            "avg_mfe_10m_pct": _safe_float(row.get("avg_mfe_10m_pct"), None),
            "avg_mae_10m_pct": _safe_float(row.get("avg_mae_10m_pct"), None),
            "avg_close_15m_pct": _safe_float(row.get("avg_close_15m_pct"), None),
            "avg_mfe_15m_pct": _safe_float(row.get("avg_mfe_15m_pct"), None),
            "avg_mae_15m_pct": _safe_float(row.get("avg_mae_15m_pct"), None),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }

    for axis, metric_key in (
        ("source_signature", "by_source_signature"),
        ("scanner_promotion_reason", "by_scanner_promotion_reason"),
        ("terminal_stage", "by_terminal_stage"),
    ):
        rows = (
            metrics.get(metric_key) if isinstance(metrics.get(metric_key), list) else []
        )
        for row in rows:
            if not isinstance(row, dict):
                continue
            sample = _safe_int(row.get("evaluated_candidates"), 0) or 0
            missed_rate = _safe_float(row.get("missed_winner_rate"), 0.0) or 0.0
            avoided_rate = _safe_float(row.get("avoided_loser_rate"), 0.0) or 0.0
            if (
                sample >= min_sample
                and missed_rate >= 60.0
                and missed_rate >= avoided_rate + 20.0
            ):
                positive_candidates.append(
                    _candidate(
                        axis,
                        row,
                        "positive_prior_candidate",
                        "rising_missed_classifier_refinement_workorder",
                        "raise_source_only_watch_priority_for_matching_rising_missed_rows",
                    )
                )
            elif (
                sample >= min_sample
                and avoided_rate >= 50.0
                and avoided_rate >= missed_rate + 20.0
            ):
                exclusion_candidates.append(
                    _candidate(
                        axis,
                        row,
                        "exclusion_or_confirmation_candidate",
                        "rising_missed_classifier_refinement_workorder",
                        "add_confirmation_or_exclusion_condition_before_priority_raise",
                    )
                )
            elif sample > 0:
                hold_sample_candidates.append(
                    _candidate(
                        axis,
                        row,
                        "hold_sample",
                        "collect_more_postclose_counterfactual_samples",
                        "do_not_change_classifier_priority_yet",
                    )
                )

    positive_candidates = sorted(
        positive_candidates,
        key=lambda item: (
            item["missed_winner_rate"] - item["avoided_loser_rate"],
            item["evaluated_candidates"],
            item["avg_mfe_10m_pct"] or 0.0,
        ),
        reverse=True,
    )[:5]
    exclusion_candidates = sorted(
        exclusion_candidates,
        key=lambda item: (
            item["avoided_loser_rate"] - item["missed_winner_rate"],
            item["evaluated_candidates"],
            abs(item["avg_mae_10m_pct"] or 0.0),
        ),
        reverse=True,
    )[:5]
    hold_sample_candidates = sorted(
        hold_sample_candidates,
        key=lambda item: (item["evaluated_candidates"], item["missed_winner_rate"]),
        reverse=True,
    )[:5]

    if positive_candidates:
        decision = "source_only_positive_prior_candidates_ready"
    elif exclusion_candidates:
        decision = "source_only_exclusion_candidates_ready"
    elif metrics.get("rising_missed_candidate_count"):
        decision = "hold_sample_collect_more_counterfactuals"
    else:
        decision = "no_rising_missed_counterfactual_rows"

    return {
        "metric_role": "source_quality_gate",
        "plan_type": "rising_missed_classifier_refinement_source_only",
        "decision": decision,
        "operator_manual_query_required": False,
        "window_policy": metrics.get("window_policy")
        or "same_day_missed_entry_counterfactual_rows",
        "sample_floor": min_sample,
        "primary_decision_metric": metrics.get("primary_decision_metric")
        or "diagnostic_win_rate",
        "source_quality_gate": metrics.get("source_quality_gate")
        or "pipeline_stage_flow_and_counterfactual_outcome_present",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "sample_floor_for_candidate": min_sample,
        "positive_prior_candidates": positive_candidates,
        "exclusion_or_confirmation_candidates": exclusion_candidates,
        "hold_sample_candidates": hold_sample_candidates,
        "next_actions": [
            "surface_positive_prior_candidates_in_daily_calibration_source_bundle",
            "route_candidates_to_source_only_classifier_refinement_or_workorder_review",
            "keep_runtime_threshold_order_provider_bot_changes_forbidden_until_separate_apply_contract",
        ],
        "forbidden_uses": list(metrics.get("forbidden_uses") or []),
        "decision_authority": metrics.get("decision_authority")
        or "postclose_source_only_refinement_no_runtime_apply",
    }


def _spread_ratio_bucket(value: float | None) -> str:
    if value is None:
        return "spread_ratio_missing"
    if value <= 0.005:
        return "spread_ratio_lte_0_005"
    if value <= 0.0075:
        return "spread_ratio_0_005_to_0_0075"
    if value <= 0.010:
        return "spread_ratio_0_0075_to_0_010"
    return "spread_ratio_gt_0_010"


def _build_quick_profit_source_only_metrics(items: list[dict]) -> dict:
    target_rows: list[dict] = []
    for item in items:
        if str(item.get("terminal_stage") or "") != "latency_block":
            continue
        if not _rising_missed_seen(item):
            continue
        if not _rising_missed_source_field(item, "rising_missed_class"):
            continue
        entry_price = _safe_float(item.get("entry_price_used"), 0.0)
        if not (5000.0 <= entry_price < 10000.0):
            continue
        target_rows.append(item)

    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in target_rows:
        terminal_fields = (
            item.get("terminal_fields")
            if isinstance(item.get("terminal_fields"), dict)
            else {}
        )
        raw_spread = terminal_fields.get("spread_ratio")
        spread_ratio = (
            _safe_float(raw_spread, None)
            if raw_spread not in (None, "", "None")
            else None
        )
        buckets[_spread_ratio_bucket(spread_ratio)].append(item)

    bucket_rows: list[dict] = []
    for bucket, rows in sorted(
        buckets.items(), key=lambda pair: (-len(pair[1]), pair[0])
    ):
        sample = len(rows)
        mfe_touch = sum(
            1
            for row in rows
            if _safe_float((row.get("metrics_15m") or {}).get("mfe_pct"), 0.0) >= 1.0
        )
        close_hold = sum(
            1
            for row in rows
            if _safe_float((row.get("metrics_15m") or {}).get("close_ret_pct"), 0.0)
            >= 1.0
        )
        bucket_rows.append(
            {
                "spread_ratio_bucket": bucket,
                "sample_count": sample,
                "mfe_15m_ge_1_count": mfe_touch,
                "mfe_15m_ge_1_rate": _ratio(mfe_touch, sample),
                "close_15m_ge_1_count": close_hold,
                "close_15m_ge_1_rate": _ratio(close_hold, sample),
                "avg_close_15m_pct": _avg(
                    [
                        _safe_float(
                            (row.get("metrics_15m") or {}).get("close_ret_pct"), 0.0
                        )
                        for row in rows
                    ]
                ),
                "avg_mfe_15m_pct": _avg(
                    [
                        _safe_float((row.get("metrics_15m") or {}).get("mfe_pct"), 0.0)
                        for row in rows
                    ]
                ),
                "avg_mae_15m_pct": _avg(
                    [
                        _safe_float((row.get("metrics_15m") or {}).get("mae_pct"), 0.0)
                        for row in rows
                    ]
                ),
                "candidate_ids": [
                    str(row.get("candidate_id") or "") for row in rows[:20]
                ],
            }
        )

    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "postclose_source_only_quick_profit_hypothesis_no_runtime_apply",
        "window_policy": "same_day_missed_entry_counterfactual_15m_labels",
        "sample_floor": 1,
        "primary_decision_metric": "diagnostic_mfe_15m_ge_1_rate",
        "source_quality_gate": "full_rows_counterfactual_metrics_15m_and_latency_spread_fields_present",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "intraday_threshold_mutation",
            "spread_guard_relaxation",
            "broker_order_submit",
            "provider_route_change",
            "bot_restart_trigger",
            "real_execution_quality_approval",
        ],
        "target_filter": {
            "price_band": "5000_10000",
            "terminal_stage": "latency_block",
            "rising_missed_class": "present",
        },
        "target_sample_count": len(target_rows),
        "spread_bucket_metrics": bucket_rows,
    }


def missed_entry_counterfactual_summary_to_dict(
    summary: MissedEntryCounterfactualSummary,
) -> dict:
    return {
        "date": summary.date,
        "total_candidates": int(summary.total_candidates),
        "evaluated_candidates": int(summary.evaluated_candidates),
        "outcome_counts": dict(summary.outcome_counts or {}),
        "top_missed_winners": list(summary.top_missed_winners or []),
        "top_avoided_losers": list(summary.top_avoided_losers or []),
    }


def build_missed_entry_counterfactual_report(
    target_date: str,
    *,
    top_n: int = 10,
    token: str | None = None,
) -> dict:
    try:
        from src.utils import kiwoom_utils
    except Exception as exc:
        log_error(f"[MISSED_ENTRY_CF] kiwoom_utils import failed: {exc}")
        kiwoom_utils = None

    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    entry_events = _load_entry_events(safe_date)
    all_buy_attempts = _build_buy_attempts(
        safe_date,
        include_submitted=True,
        events=entry_events,
    )
    candidates = [
        item
        for item in all_buy_attempts
        if str(item.get("attempt_status") or "") == "MISSED"
    ]
    summary = MissedEntryCounterfactualSummary(date=safe_date)
    summary.total_candidates = len(candidates)

    if not candidates:
        empty_rising_metrics = _build_rising_missed_refinement_metrics([])
        watch_cycle_ledger = _build_watch_cycle_participation_ledger(
            safe_date,
            entry_events,
            [],
        )
        return {
            "date": safe_date,
            "summary": missed_entry_counterfactual_summary_to_dict(summary),
            "metrics": {
                "total_candidates": 0,
                "evaluated_candidates": 0,
                "missed_winner_rate": 0.0,
                "avoided_loser_rate": 0.0,
                "avg_close_5m_pct": 0.0,
                "avg_close_10m_pct": 0.0,
                "avg_mfe_10m_pct": 0.0,
                "avg_mae_10m_pct": 0.0,
                "avg_close_15m_pct": 0.0,
                "avg_mfe_15m_pct": 0.0,
                "avg_mae_15m_pct": 0.0,
                "estimated_counterfactual_pnl_10m_krw_sum": 0,
                "venue_source_quality_counts": {},
                "venue_outcome_breakdown": [],
                "venue_attribution_contract": {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "missed_entry_counterfactual_source_only",
                    "window_policy": "same_entry_attempt_explicit_event_fields",
                    "sample_floor": "1_attempt_with_explicit_tradable_venue",
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": (
                        "single_conflict_free_explicit_effective_venue_or_venue_fallback"
                    ),
                    "forbidden_uses": [
                        "clock_only_venue_inference_for_tuning",
                        "unknown_or_conflicting_venue_specific_tuning",
                        "intraday_threshold_mutation",
                        "live_auto_promotion",
                        "runtime_apply_bridge",
                    ],
                },
                "blocker_outcome_metrics": {},
                "cohort_outcome_metrics": {},
                "rising_missed_refinement": empty_rising_metrics,
                "rising_missed_refinement_action_plan": _build_rising_missed_refinement_action_plan(
                    empty_rising_metrics
                ),
                "quick_profit_5k_10k_rising_missed_latency_source_only": _build_quick_profit_source_only_metrics(
                    []
                ),
            },
            "buy_signal_universe": {
                "metrics": {
                    "total_buy_judged_attempts": int(len(all_buy_attempts)),
                    "entered_attempts": int(
                        sum(
                            1
                            for item in all_buy_attempts
                            if str(item.get("attempt_status") or "") == "ENTERED"
                        )
                    ),
                    "missed_attempts": int(
                        sum(
                            1
                            for item in all_buy_attempts
                            if str(item.get("attempt_status") or "") == "MISSED"
                        )
                    ),
                },
                "confidence_breakdown": [],
                "rows": [],
            },
            "watch_cycle_participation_ledger": watch_cycle_ledger,
            "insight": {
                "headline": "AI BUY 후 미진입 counterfactual 표본이 없습니다.",
                "comment": "장중 BUY 후 주문전 차단 사례가 쌓이면 missed winner / avoided loser를 함께 해석할 수 있습니다.",
            },
            "reason_breakdown": [],
            "top_missed_winners": [],
            "top_avoided_losers": [],
            "rows": [],
            "full_rows": [],
            "meta": {
                "schema_version": MISSED_ENTRY_COUNTERFACTUAL_SCHEMA_VERSION,
                "generated_at": datetime.now().isoformat(),
                "evaluation_mode": "missed_entry_minute_forward",
                "thresholds": {
                    "missed_mfe_pct": _BUY_MISSED_MFE_PCT,
                    "missed_close_pct": _BUY_MISSED_CLOSE_PCT,
                    "avoided_mae_pct": _BUY_AVOIDED_MAE_PCT,
                    "avoided_close_pct": _BUY_AVOIDED_CLOSE_PCT,
                },
            },
        }

    if token is None and kiwoom_utils is not None:
        try:
            token = kiwoom_utils.get_kiwoom_token()
        except Exception as exc:
            log_error(f"[MISSED_ENTRY_CF] token fetch failed: {exc}")
            token = None

    candle_cache: dict[str, tuple[list[dict], dict]] = {}
    evaluations: list[dict] = []
    all_buy_evaluations: list[dict] = []

    for candidate in all_buy_attempts:
        code = str(candidate.get("stock_code") or "").strip()[:6]
        if not code:
            continue
        if code not in candle_cache:
            if token is None or kiwoom_utils is None:
                candle_cache[code] = (
                    [],
                    _minute_candle_meta([], requested_limit=700),
                )
            else:
                try:
                    candle_cache[code] = _fetch_minute_candles_with_meta(
                        kiwoom_utils, token, code, limit=700
                    )
                except Exception as exc:
                    log_error(
                        f"[MISSED_ENTRY_CF] {code} minute candles fetch failed: {exc}"
                    )
                    candle_cache[code] = (
                        [],
                        _minute_candle_meta([], requested_limit=700),
                    )

        candles, candle_meta = candle_cache.get(
            code, ([], _minute_candle_meta([], requested_limit=700))
        )
        forward_horizon_metrics = {
            str(horizon_min): _compute_window_metrics(candidate, candles, horizon_min)
            for horizon_min in _WATCH_CYCLE_HORIZONS_MIN
        }
        metrics_5m = forward_horizon_metrics["5"]
        metrics_10m = forward_horizon_metrics["10"]
        metrics_15m = _compute_window_metrics(candidate, candles, 15)
        outcome = _classify_candidate(metrics_5m, metrics_10m)
        source_quality = _minute_forward_source_quality(metrics_10m, candle_meta)
        source_quality_15m = _minute_forward_source_quality(
            metrics_15m, candle_meta, window_minutes=15
        )
        entry_price_used = _safe_int(metrics_10m.get("entry_price_used"), 0)
        capacity = _sim_virtual_qty(
            entry_price_used,
            _safe_float(candidate.get("ai_score"), 0.0),
            reference_time=candidate.get("reference_time"),
            source_signature=candidate.get("source_signature"),
            effective_venue=candidate.get("effective_venue"),
        )
        qty = _safe_int(capacity.get("qty"), 0)
        est_pnl_10m = (
            int(
                round(
                    entry_price_used
                    * qty
                    * (_safe_float(metrics_10m.get("close_ret_pct"), 0.0) / 100.0)
                )
            )
            if entry_price_used > 0 and qty > 0
            else 0
        )
        evaluations.append(
            {
                **candidate,
                **_counterfactual_sizing_fields(capacity),
                "outcome": outcome,
                "metrics_5m": metrics_5m,
                "metrics_10m": metrics_10m,
                "metrics_15m": metrics_15m,
                "forward_horizon_metrics": forward_horizon_metrics,
                "entry_price_used": entry_price_used,
                "price_source": (
                    "explicit_target_buy_price"
                    if _safe_int(candidate.get("signal_price"), 0) > 0
                    else "minute_candle_proxy"
                ),
                "minute_candle_source_meta": candle_meta,
                **source_quality,
                **source_quality_15m,
                "counterfactual_qty": int(qty),
                "counterfactual_qty_source": (
                    "scalping_position_sizing_allocator" if qty > 0 else "unpriced"
                ),
                "virtual_budget_override": True,
                "virtual_budget_krw": int(capacity.get("virtual_budget_krw") or 0),
                "counterfactual_ratio": round(float(capacity.get("ratio") or 0.0), 4),
                "counterfactual_target_budget": int(capacity.get("target_budget") or 0),
                "counterfactual_safe_budget": int(capacity.get("safe_budget") or 0),
                "counterfactual_safety_ratio": round(
                    float(capacity.get("safety_ratio") or 0.0), 4
                ),
                "counterfactual_max_budget": int(capacity.get("max_budget") or 0),
                "counterfactual_notional_krw": (
                    int(entry_price_used * qty)
                    if entry_price_used > 0 and qty > 0
                    else 0
                ),
                "real_target_qty_observed": _safe_int(candidate.get("target_qty"), 0),
                "estimated_counterfactual_pnl_10m_krw": est_pnl_10m,
            }
        )
        if str(candidate.get("attempt_status") or "") == "MISSED":
            all_buy_evaluations.append(evaluations[-1])
        else:
            all_buy_evaluations.append(evaluations[-1])

    # Keep missed-only evaluation slice for the main summary.
    evaluations = [
        item
        for item in all_buy_evaluations
        if str(item.get("attempt_status") or "") == "MISSED"
    ]
    watch_cycle_ledger = _build_watch_cycle_participation_ledger(
        safe_date,
        entry_events,
        all_buy_evaluations,
    )

    summary.evaluated_candidates = len(evaluations)
    outcome_counts: dict[str, int] = {
        "MISSED_WINNER": 0,
        "AVOIDED_LOSER": 0,
        "NEUTRAL": 0,
    }
    for item in evaluations:
        outcome = str(item.get("outcome") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts

    def _winner_score(item: dict) -> tuple[float, float]:
        metrics_10m = item.get("metrics_10m", {}) or {}
        return (
            _safe_float(metrics_10m.get("mfe_pct"), 0.0),
            _safe_float(metrics_10m.get("close_ret_pct"), 0.0),
        )

    def _loser_score(item: dict) -> tuple[float, float]:
        metrics_10m = item.get("metrics_10m", {}) or {}
        return (
            abs(_safe_float(metrics_10m.get("mae_pct"), 0.0)),
            abs(_safe_float(metrics_10m.get("close_ret_pct"), 0.0)),
        )

    summary.top_missed_winners = sorted(
        [
            item
            for item in evaluations
            if str(item.get("outcome") or "") == "MISSED_WINNER"
        ],
        key=_winner_score,
        reverse=True,
    )[: max(1, int(top_n or 10))]
    summary.top_avoided_losers = sorted(
        [
            item
            for item in evaluations
            if str(item.get("outcome") or "") == "AVOIDED_LOSER"
        ],
        key=_loser_score,
        reverse=True,
    )[: max(1, int(top_n or 10))]

    evaluated_count = len(evaluations)
    missed_winner_rate = _ratio(outcome_counts.get("MISSED_WINNER", 0), evaluated_count)
    avoided_loser_rate = _ratio(outcome_counts.get("AVOIDED_LOSER", 0), evaluated_count)
    explicit_rows = [
        item
        for item in evaluations
        if str(item.get("price_source") or "") == "explicit_target_buy_price"
    ]
    explicit_count = len(explicit_rows)
    explicit_missed_rate = _ratio(
        sum(
            1
            for item in explicit_rows
            if str(item.get("outcome") or "") == "MISSED_WINNER"
        ),
        explicit_count,
    )
    explicit_avoided_rate = _ratio(
        sum(
            1
            for item in explicit_rows
            if str(item.get("outcome") or "") == "AVOIDED_LOSER"
        ),
        explicit_count,
    )
    avg_close_5m = _avg(
        [
            _safe_float((item.get("metrics_5m") or {}).get("close_ret_pct"), 0.0)
            for item in evaluations
        ]
    )
    avg_close_10m = _avg(
        [
            _safe_float((item.get("metrics_10m") or {}).get("close_ret_pct"), 0.0)
            for item in evaluations
        ]
    )
    avg_mfe_10m = _avg(
        [
            _safe_float((item.get("metrics_10m") or {}).get("mfe_pct"), 0.0)
            for item in evaluations
        ]
    )
    avg_mae_10m = _avg(
        [
            _safe_float((item.get("metrics_10m") or {}).get("mae_pct"), 0.0)
            for item in evaluations
        ]
    )
    avg_close_15m = _avg(
        [
            _safe_float((item.get("metrics_15m") or {}).get("close_ret_pct"), 0.0)
            for item in evaluations
        ]
    )
    avg_mfe_15m = _avg(
        [
            _safe_float((item.get("metrics_15m") or {}).get("mfe_pct"), 0.0)
            for item in evaluations
        ]
    )
    avg_mae_15m = _avg(
        [
            _safe_float((item.get("metrics_15m") or {}).get("mae_pct"), 0.0)
            for item in evaluations
        ]
    )
    estimated_pnl_sum = int(
        sum(
            _safe_int(item.get("estimated_counterfactual_pnl_10m_krw"), 0)
            for item in evaluations
        )
    )
    minute_candle_source_quality_counts = dict(
        Counter(
            str(item.get("minute_candle_source_quality") or "unknown")
            for item in evaluations
        )
    )
    venue_source_quality_counts = dict(
        Counter(
            str(item.get("venue_source_quality") or "unknown") for item in evaluations
        )
    )
    venue_outcome_breakdown = []
    for venue in sorted(
        {str(item.get("effective_venue") or "UNKNOWN").upper() for item in evaluations}
    ):
        venue_rows = [
            item
            for item in evaluations
            if str(item.get("effective_venue") or "UNKNOWN").upper() == venue
        ]
        valid_rows = [
            item for item in venue_rows if bool(item.get("venue_tuning_allowed"))
        ]
        venue_outcome_breakdown.append(
            {
                "effective_venue": venue,
                "candidate_count": len(venue_rows),
                "source_quality_valid_count": len(valid_rows),
                "source_quality_blocked_count": len(venue_rows) - len(valid_rows),
                "missed_winner_count": sum(
                    1
                    for item in valid_rows
                    if str(item.get("outcome") or "") == "MISSED_WINNER"
                ),
                "avoided_loser_count": sum(
                    1
                    for item in valid_rows
                    if str(item.get("outcome") or "") == "AVOIDED_LOSER"
                ),
                "venue_specific_tuning_allowed": bool(valid_rows),
            }
        )

    if missed_winner_rate >= avoided_loser_rate + 20.0:
        headline = "BUY 후 미진입 차단이 과한 쪽으로 기울었을 가능성이 큽니다."
    elif avoided_loser_rate >= missed_winner_rate + 20.0:
        headline = "주문전 차단이 손실 회피에도 기여한 흔적이 더 큽니다."
    else:
        headline = "미진입 차단은 혼합 결과로 보여 사유별 분해가 중요합니다."

    reason_buckets: dict[str, list[dict]] = defaultdict(list)
    for item in evaluations:
        reason_buckets[str(item.get("terminal_stage") or "-")].append(item)
    blocker_outcome_metrics = _build_blocker_outcome_metrics(evaluations)
    cohort_outcome_metrics = _build_cohort_outcome_metrics(evaluations)
    rising_missed_refinement_metrics = _build_rising_missed_refinement_metrics(
        evaluations
    )
    rising_missed_refinement_action_plan = _build_rising_missed_refinement_action_plan(
        rising_missed_refinement_metrics
    )
    quick_profit_source_only_metrics = _build_quick_profit_source_only_metrics(
        evaluations
    )
    reason_breakdown = []
    for stage, items in sorted(
        reason_buckets.items(), key=lambda pair: len(pair[1]), reverse=True
    ):
        trades = len(items)
        missed_count = sum(
            1 for item in items if str(item.get("outcome") or "") == "MISSED_WINNER"
        )
        avoided_count = sum(
            1 for item in items if str(item.get("outcome") or "") == "AVOIDED_LOSER"
        )
        reason_breakdown.append(
            {
                "stage": stage,
                "stage_label": _stage_label(stage),
                "candidates": trades,
                "missed_winner_rate": _ratio(missed_count, trades),
                "avoided_loser_rate": _ratio(avoided_count, trades),
                "avg_close_10m_pct": _avg(
                    [
                        _safe_float(
                            (item.get("metrics_10m") or {}).get("close_ret_pct"), 0.0
                        )
                        for item in items
                    ]
                ),
                "avg_mfe_10m_pct": _avg(
                    [
                        _safe_float((item.get("metrics_10m") or {}).get("mfe_pct"), 0.0)
                        for item in items
                    ]
                ),
                "avg_mae_10m_pct": _avg(
                    [
                        _safe_float((item.get("metrics_10m") or {}).get("mae_pct"), 0.0)
                        for item in items
                    ]
                ),
                "avg_close_15m_pct": _avg(
                    [
                        _safe_float(
                            (item.get("metrics_15m") or {}).get("close_ret_pct"), 0.0
                        )
                        for item in items
                    ]
                ),
                "avg_mfe_15m_pct": _avg(
                    [
                        _safe_float((item.get("metrics_15m") or {}).get("mfe_pct"), 0.0)
                        for item in items
                    ]
                ),
                "avg_mae_15m_pct": _avg(
                    [
                        _safe_float((item.get("metrics_15m") or {}).get("mae_pct"), 0.0)
                        for item in items
                    ]
                ),
            }
        )

    def _row_view(item: dict) -> dict:
        metrics_5m = item.get("metrics_5m", {}) or {}
        metrics_10m = item.get("metrics_10m", {}) or {}
        metrics_15m = item.get("metrics_15m", {}) or {}
        return {
            "candidate_id": str(item.get("candidate_id") or ""),
            "stock_code": str(item.get("stock_code") or ""),
            "stock_name": str(item.get("stock_name") or ""),
            "attempt_status": str(item.get("attempt_status") or ""),
            "buy_intent_source": str(item.get("buy_intent_source") or ""),
            "record_id": item.get("record_id"),
            "anchor_stage": str(item.get("anchor_stage") or ""),
            "terminal_stage": str(item.get("terminal_stage") or ""),
            "terminal_stage_label": str(item.get("terminal_stage_label") or ""),
            "no_submit_reason": str(item.get("no_submit_reason") or ""),
            "liquidity_relief_skip_reason": str(
                (item.get("terminal_fields") or {}).get("liquidity_relief_skip_reason")
                if isinstance(item.get("terminal_fields"), dict)
                else ""
            ),
            "signal_time": str(item.get("signal_time") or ""),
            "reference_time": str(item.get("reference_time") or ""),
            "effective_venue": str(item.get("effective_venue") or "UNKNOWN"),
            "venue_resolution": str(item.get("venue_resolution") or ""),
            "venue_source_quality": str(item.get("venue_source_quality") or "unknown"),
            "venue_tuning_allowed": bool(item.get("venue_tuning_allowed")),
            "venue_field_sources": list(item.get("venue_field_sources") or []),
            "market_session_bucket": str(item.get("market_session_bucket") or ""),
            "signal_price": int(_safe_int(item.get("signal_price"), 0)),
            "entry_price_used": int(_safe_int(item.get("entry_price_used"), 0)),
            "target_qty": int(_safe_int(item.get("target_qty"), 0)),
            "counterfactual_qty": int(_safe_int(item.get("counterfactual_qty"), 0)),
            "counterfactual_qty_source": str(
                item.get("counterfactual_qty_source") or ""
            ),
            "virtual_budget_krw": int(_safe_int(item.get("virtual_budget_krw"), 0)),
            "counterfactual_ratio": round(
                _safe_float(item.get("counterfactual_ratio"), 0.0), 4
            ),
            "counterfactual_safe_budget": int(
                _safe_int(item.get("counterfactual_safe_budget"), 0)
            ),
            "counterfactual_notional_krw": int(
                _safe_int(item.get("counterfactual_notional_krw"), 0)
            ),
            **{key: item.get(key) for key in _COUNTERFACTUAL_SIZING_KEYS},
            "ai_score": round(_safe_float(item.get("ai_score"), 0.0), 1),
            "price_source": str(item.get("price_source") or "minute_candle_proxy"),
            "minute_candle_source_quality": str(
                item.get("minute_candle_source_quality") or "unknown"
            ),
            "minute_candle_source_quality_gate": str(
                item.get("minute_candle_source_quality_gate") or "unknown"
            ),
            "minute_candle_source_quality_reason": str(
                item.get("minute_candle_source_quality_reason") or ""
            ),
            "minute_candle_forward_10m_bars": _safe_int(
                item.get("minute_candle_forward_10m_bars"), 0
            ),
            "minute_candle_forward_15m_bars": _safe_int(
                item.get("minute_candle_forward_15m_bars"), 0
            ),
            "minute_candle_forward_15m_source_quality": str(
                item.get("minute_candle_forward_15m_source_quality") or "unknown"
            ),
            "minute_candle_forward_15m_source_quality_gate": str(
                item.get("minute_candle_forward_15m_source_quality_gate") or "unknown"
            ),
            "minute_candle_forward_15m_source_quality_reason": str(
                item.get("minute_candle_forward_15m_source_quality_reason") or ""
            ),
            "minute_candle_source_meta": item.get("minute_candle_source_meta") or {},
            "confidence_tier": _confidence_tier(item),
            "outcome": str(item.get("outcome") or "NEUTRAL"),
            "close_5m_pct": round(_safe_float(metrics_5m.get("close_ret_pct"), 0.0), 3),
            "close_10m_pct": round(
                _safe_float(metrics_10m.get("close_ret_pct"), 0.0), 3
            ),
            "mfe_10m_pct": round(_safe_float(metrics_10m.get("mfe_pct"), 0.0), 3),
            "mae_10m_pct": round(_safe_float(metrics_10m.get("mae_pct"), 0.0), 3),
            "close_15m_pct": round(
                _safe_float(metrics_15m.get("close_ret_pct"), 0.0), 3
            ),
            "mfe_15m_pct": round(_safe_float(metrics_15m.get("mfe_pct"), 0.0), 3),
            "mae_15m_pct": round(_safe_float(metrics_15m.get("mae_pct"), 0.0), 3),
            "estimated_counterfactual_pnl_10m_krw": int(
                _safe_int(item.get("estimated_counterfactual_pnl_10m_krw"), 0)
            ),
            "missed_submit_cohort": str(item.get("missed_submit_cohort") or ""),
            "stage_flow": [str(stage) for stage in (item.get("stage_flow") or [])],
            "source_signature": _rising_missed_source_field(item, "source_signature"),
            "scanner_promotion_reason": _rising_missed_source_field(
                item, "scanner_promotion_reason"
            ),
            "price_delta_since_first_seen_pct": round(
                _safe_float(
                    _rising_missed_source_field(
                        item, "price_delta_since_first_seen_pct"
                    ),
                    0.0,
                ),
                3,
            ),
            "rising_missed_class": _rising_missed_source_field(
                item, "rising_missed_class"
            ),
            "rising_missed_one_share_entry_seen": _rising_missed_seen(item),
            "rising_missed_stage_count": _rising_missed_stage_count(item),
            "rising_missed_postclose_label": _rising_missed_postclose_label(item),
            "rising_missed_refinement_authority": "postclose_source_only_no_runtime_apply",
        }

    return {
        "date": safe_date,
        "summary": missed_entry_counterfactual_summary_to_dict(summary),
        "metrics": {
            "total_candidates": int(summary.total_candidates),
            "evaluated_candidates": int(summary.evaluated_candidates),
            "missed_winner_rate": float(missed_winner_rate),
            "avoided_loser_rate": float(avoided_loser_rate),
            "explicit_price_candidates": int(explicit_count),
            "explicit_price_missed_winner_rate": float(explicit_missed_rate),
            "explicit_price_avoided_loser_rate": float(explicit_avoided_rate),
            "avg_close_5m_pct": float(avg_close_5m),
            "avg_close_10m_pct": float(avg_close_10m),
            "avg_mfe_10m_pct": float(avg_mfe_10m),
            "avg_mae_10m_pct": float(avg_mae_10m),
            "avg_close_15m_pct": float(avg_close_15m),
            "avg_mfe_15m_pct": float(avg_mfe_15m),
            "avg_mae_15m_pct": float(avg_mae_15m),
            "estimated_counterfactual_pnl_10m_krw_sum": int(estimated_pnl_sum),
            "minute_candle_source_quality_counts": minute_candle_source_quality_counts,
            "venue_source_quality_counts": venue_source_quality_counts,
            "venue_outcome_breakdown": venue_outcome_breakdown,
            "venue_attribution_contract": {
                "metric_role": "source_quality_gate",
                "decision_authority": "missed_entry_counterfactual_source_only",
                "window_policy": "same_entry_attempt_explicit_event_fields",
                "sample_floor": "1_attempt_with_explicit_tradable_venue",
                "primary_decision_metric": "source_quality_adjusted_ev_pct",
                "source_quality_gate": (
                    "single_conflict_free_explicit_effective_venue_or_venue_fallback"
                ),
                "forbidden_uses": [
                    "clock_only_venue_inference_for_tuning",
                    "unknown_or_conflicting_venue_specific_tuning",
                    "intraday_threshold_mutation",
                    "live_auto_promotion",
                    "runtime_apply_bridge",
                ],
            },
            "blocker_outcome_metrics": blocker_outcome_metrics,
            "cohort_outcome_metrics": cohort_outcome_metrics,
            "rising_missed_refinement": rising_missed_refinement_metrics,
            "rising_missed_refinement_action_plan": rising_missed_refinement_action_plan,
            "quick_profit_5k_10k_rising_missed_latency_source_only": quick_profit_source_only_metrics,
        },
        "buy_signal_universe": {
            "metrics": {
                "total_buy_judged_attempts": int(len(all_buy_attempts)),
                "entered_attempts": int(
                    sum(
                        1
                        for item in all_buy_attempts
                        if str(item.get("attempt_status") or "") == "ENTERED"
                    )
                ),
                "missed_attempts": int(
                    sum(
                        1
                        for item in all_buy_attempts
                        if str(item.get("attempt_status") or "") == "MISSED"
                    )
                ),
                "entered_rate": _ratio(
                    sum(
                        1
                        for item in all_buy_attempts
                        if str(item.get("attempt_status") or "") == "ENTERED"
                    ),
                    len(all_buy_attempts),
                ),
            },
            "confidence_breakdown": [
                {
                    "tier": tier,
                    "attempts": len(items),
                    "entered_attempts": sum(
                        1
                        for item in items
                        if str(item.get("attempt_status") or "") == "ENTERED"
                    ),
                    "missed_attempts": sum(
                        1
                        for item in items
                        if str(item.get("attempt_status") or "") == "MISSED"
                    ),
                }
                for tier, items in sorted(
                    defaultdict(
                        list,
                        {
                            tier: [
                                item
                                for item in all_buy_evaluations
                                if _confidence_tier(item) == tier
                            ]
                            for tier in ("A", "B", "C")
                        },
                    ).items()
                )
                if items
            ],
            "rows": [
                _row_view(item)
                for item in sorted(
                    all_buy_evaluations,
                    key=lambda item: (
                        str(item.get("signal_date") or ""),
                        str(item.get("signal_time") or ""),
                        str(item.get("stock_code") or ""),
                    ),
                    reverse=True,
                )[: max(1, int(top_n or 10) * 3)]
            ],
        },
        "watch_cycle_participation_ledger": watch_cycle_ledger,
        "insight": {
            "headline": headline,
            "comment": (
                f"평가 {evaluated_count}건 기준 missed_winner {missed_winner_rate:.1f}%, "
                f"avoided_loser {avoided_loser_rate:.1f}%, 10분 평균 종가 수익률 {avg_close_10m:+.2f}%입니다. "
                f"explicit target_buy_price 보유 표본은 {explicit_count}건입니다."
            ),
        },
        "reason_breakdown": reason_breakdown,
        "top_missed_winners": [_row_view(item) for item in summary.top_missed_winners],
        "top_avoided_losers": [_row_view(item) for item in summary.top_avoided_losers],
        "rows": [
            _row_view(item) for item in evaluations[: max(1, int(top_n or 10) * 3)]
        ],
        "full_rows": [_row_view(item) for item in evaluations],
        "meta": {
            "schema_version": MISSED_ENTRY_COUNTERFACTUAL_SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "evaluation_mode": "missed_entry_minute_forward",
            "thresholds": {
                "missed_mfe_pct": _BUY_MISSED_MFE_PCT,
                "missed_close_pct": _BUY_MISSED_CLOSE_PCT,
                "avoided_mae_pct": _BUY_AVOIDED_MAE_PCT,
                "avoided_close_pct": _BUY_AVOIDED_CLOSE_PCT,
                "tp_pct": _BUY_TP_PCT,
                "sl_pct": abs(_BUY_SL_PCT),
            },
        },
    }
