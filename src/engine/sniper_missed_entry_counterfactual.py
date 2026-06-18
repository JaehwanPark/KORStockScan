"""Counterfactual evaluation for AI BUY entries that never reached order submission."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.engine import kiwoom_orders
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import read_jsonl
from src.utils.logger import log_error


MISSED_ENTRY_COUNTERFACTUAL_SCHEMA_VERSION = 2
_ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
_INFERRED_BUY_INTENT_STAGES = _ENTRY_ARMED_STAGES | {"score65_74_recovery_probe_entry_unlocked"}
_INFERRED_BUY_INTENT_DEDUP_TERMINAL_STAGES = {
    "pre_submit_liquidity_guard_block",
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
}
_BUY_MISSED_MFE_PCT = 0.8
_BUY_MISSED_CLOSE_PCT = 0.3
_BUY_AVOIDED_MAE_PCT = -0.8
_BUY_AVOIDED_CLOSE_PCT = -0.3
_BUY_TP_PCT = 0.5
_BUY_SL_PCT = -0.5
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
    "pre_submit_weak_context_late_entry_guard_block": "약한 문맥 늦은 진입 차단",
    "entry_armed_expired": "진입 자격 만료",
    "entry_armed_expired_after_wait": "진입 대기 후 자격 만료",
    "entry_arm_expired": "진입 자격 만료(legacy)",
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


def _sim_virtual_budget_krw() -> int:
    return max(0, int(getattr(TRADING_RULES, "SIM_VIRTUAL_BUDGET_KRW", 10_000_000) or 0))


def _scalp_ratio_from_score(ai_score: float) -> float:
    min_ratio = float(getattr(TRADING_RULES, "INVEST_RATIO_SCALPING_MIN", 0.10) or 0.10)
    max_ratio = float(getattr(TRADING_RULES, "INVEST_RATIO_SCALPING_MAX", 0.30) or 0.30)
    score = max(0.0, min(100.0, float(ai_score or 0.0)))
    return min_ratio + (score / 100.0) * (max_ratio - min_ratio)


def _sim_virtual_qty(entry_price: int, ai_score: float) -> dict:
    virtual_budget = _sim_virtual_budget_krw()
    ratio = _scalp_ratio_from_score(ai_score)
    max_budget = int(getattr(TRADING_RULES, "SCALPING_MAX_BUY_BUDGET_KRW", 0) or 0)
    if entry_price <= 0 or virtual_budget <= 0:
        return {
            "qty": 0,
            "ratio": ratio,
            "virtual_budget_krw": virtual_budget,
            "target_budget": 0,
            "safe_budget": 0,
            "safety_ratio": 0.0,
            "max_budget": max_budget,
        }
    target_budget, safe_budget, qty, safety_ratio = kiwoom_orders.describe_buy_capacity(
        entry_price,
        virtual_budget,
        ratio,
        max_budget=max_budget,
    )
    return {
        "qty": max(1, _safe_int(qty, 0)),
        "ratio": ratio,
        "virtual_budget_krw": virtual_budget,
        "target_budget": target_budget,
        "safe_budget": safe_budget,
        "safety_ratio": safety_ratio,
        "max_budget": max_budget,
    }


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return round((float(numerator) / float(denominator)) * 100.0, 1) if denominator > 0 else 0.0


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


def _parse_minute_time(value: str, signal_date: str) -> datetime | None:
    try:
        return datetime.strptime(f"{signal_date} {value}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _classify_stage(stage: str) -> str:
    if stage == "order_bundle_submitted":
        return "submitted"
    if stage.startswith("blocked_") or stage.endswith("_block") or stage.endswith("_failed"):
        return "blocked"
    if stage in {"first_ai_wait", "entry_armed_expired", "entry_armed_expired_after_wait", "entry_arm_expired"}:
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
                fields={str(key): str(value) for key, value in dict(row.get("fields") or {}).items()},
            )
        )
    events.sort(key=lambda item: (_parse_event_dt(item.emitted_at) or datetime.min, item.code, item.stage))
    return events


def _split_attempt_segments(item_events: list[EntryEvent]) -> list[list[EntryEvent]]:
    if not item_events:
        return []
    segments: list[list[EntryEvent]] = []
    current: list[EntryEvent] = []
    current_record_id = ""
    segment_terminated = False

    for event in item_events:
        record_changed = bool(current and event.record_id and current_record_id and event.record_id != current_record_id)
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


def _buy_intent_events(attempt_events: list[EntryEvent]) -> tuple[list[EntryEvent], str]:
    explicit_buy_events = [
        event for event in attempt_events
        if event.stage == "ai_confirmed" and str(event.fields.get("action") or "").upper() == "BUY"
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
        in {"NO_BUY_AI", "WAIT_REQUOTE", "SKIP_STALE", "SKIP_PRE_SUBMIT_SAFETY", "SKIP_SOURCE_QUALITY"}
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
    if chosen_action in {"WAIT_REQUOTE", "SKIP_STALE", "SKIP_PRE_SUBMIT_SAFETY", "SKIP_SOURCE_QUALITY"}:
        return "waiting"
    return None


def _missed_submit_cohort(candidate: dict) -> str:
    terminal_stage = str(candidate.get("terminal_stage") or "")
    terminal_fields = candidate.get("terminal_fields") if isinstance(candidate.get("terminal_fields"), dict) else {}
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
    if terminal_stage == "scalp_entry_action_decision_snapshot" and chosen_action == "NO_BUY_AI":
        if "early_accel_strong_bundle_recheck_corrected" in stage_flow:
            return "early_accel_strong_bundle_recheck_corrected"
        if "early_accel_strong_bundle_recheck_failed" in stage_flow:
            return "early_accel_strong_bundle_recheck_failed"
        if "early_accel_strong_bundle_recheck_skipped" in stage_flow:
            return "early_accel_strong_bundle_recheck_skipped"
        if terminal_fields.get("ai_reason_numeric_inconsistency") in {True, "true", "True", "1"}:
            return "ai_numeric_inconsistency_no_buy"
        return "ai_no_buy_clean_reason"
    if terminal_stage == "pre_submit_liquidity_guard_block":
        return "entry_armed_pre_submit_liquidity_block"
    if terminal_stage in {
        "latency_block",
        "entry_submit_revalidation_block",
        "pre_submit_weak_context_late_entry_guard_block",
        "pre_submit_overbought_pullback_guard_block",
        "real_weak_pullback_entry_block",
    }:
        return "entry_armed_latency_or_safety_block"
    if chosen_action in {"WAIT_REQUOTE", "SKIP_STALE", "SKIP_PRE_SUBMIT_SAFETY", "SKIP_SOURCE_QUALITY"}:
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


def _build_buy_attempts(target_date: str, *, include_submitted: bool = True) -> list[dict]:
    events = _load_entry_events(target_date)
    by_stock: dict[tuple[str, str], list[EntryEvent]] = defaultdict(list)
    for event in events:
        by_stock[(event.name, event.code)].append(event)

    candidates: list[dict] = []
    for _key, item_events in by_stock.items():
        for attempt_events in _split_attempt_segments(item_events):
            if not attempt_events:
                continue
            has_submitted = any(event.stage == "order_bundle_submitted" for event in attempt_events)
            if has_submitted and not include_submitted:
                continue

            buy_events, buy_intent_source = _buy_intent_events(attempt_events)
            if not buy_events:
                continue

            terminal_event = next(
                (
                    event
                    for event in reversed(attempt_events)
                    if _classify_stage(event.stage) in ({"blocked", "waiting", "submitted"} if include_submitted else {"blocked", "waiting"})
                ),
                None,
            )
            if terminal_event is None:
                terminal_event = next(
                    (
                        event
                        for event in reversed(attempt_events)
                        if _snapshot_terminal_class(event) in ({"blocked", "waiting", "submitted"} if include_submitted else {"blocked", "waiting"})
                    ),
                    None,
                )
            if terminal_event is None:
                continue

            anchor_event = next(
                (event for event in reversed(attempt_events) if event.stage in _ENTRY_ARMED_STAGES),
                None,
            ) or buy_events[-1]

            anchor_dt = _parse_event_dt(anchor_event.emitted_at)
            if anchor_dt is None:
                continue

            budget_event = next(
                (event for event in reversed(attempt_events) if event.stage == "budget_pass"),
                None,
            )
            signal_price = _safe_int(anchor_event.fields.get("target_buy_price"), 0)
            ai_score = _safe_float(anchor_event.fields.get("ai_score"), _safe_float(buy_events[-1].fields.get("ai_score"), 0.0))
            blocker_counts = Counter(
                event.stage for event in attempt_events if _classify_stage(event.stage) in {"blocked", "waiting"}
            )

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
                    "target_qty": _safe_int((budget_event.fields if budget_event else {}).get("qty"), 0),
                    "safe_budget": _safe_int((budget_event.fields if budget_event else {}).get("safe_budget"), 0),
                    "budget_passed": bool(budget_event is not None),
                    "entry_armed": any(event.stage in _ENTRY_ARMED_STAGES for event in attempt_events),
                    "buy_signal_count": len(buy_events),
                    "buy_intent_source": buy_intent_source,
                    "stage_flow": [event.stage for event in attempt_events],
                    "blocker_counts": dict(blocker_counts),
                    "terminal_fields": dict(terminal_event.fields),
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


def _resolve_anchor_price(signal_price: float, relevant: list[tuple[datetime, dict]]) -> float:
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


def _compute_window_metrics(candidate: dict, candles: list[dict], window_minutes: int) -> dict:
    signal_dt = datetime.strptime(
        f"{candidate['signal_date']} {candidate['signal_time']}",
        "%Y-%m-%d %H:%M:%S",
    )
    start_dt = signal_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end_dt = start_dt + timedelta(minutes=window_minutes)

    relevant: list[tuple[datetime, dict]] = []
    for candle in candles:
        candle_dt = _parse_minute_time(str(candle.get("체결시간", "") or ""), candidate["signal_date"])
        if candle_dt is None:
            continue
        if candle_dt < start_dt or candle_dt >= end_dt:
            continue
        relevant.append((candle_dt, candle))
    relevant.sort(key=lambda item: item[0])

    anchor_price = _resolve_anchor_price(float(candidate.get("signal_price", 0) or 0), relevant)
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
        "tp05_before_sl05": bool(first_tp_dt is not None and (first_sl_dt is None or first_tp_dt <= first_sl_dt)),
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


def _build_blocker_outcome_metrics(items: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        stage = str(item.get("terminal_stage") or "-")
        buckets[stage].append(item)

    metrics: dict[str, dict] = {}
    for stage, rows in sorted(buckets.items()):
        total = len(rows)
        missed = sum(1 for row in rows if str(row.get("outcome") or "") == "MISSED_WINNER")
        avoided = sum(1 for row in rows if str(row.get("outcome") or "") == "AVOIDED_LOSER")
        neutral = sum(1 for row in rows if str(row.get("outcome") or "") == "NEUTRAL")
        estimated_pnl = int(sum(_safe_int(row.get("estimated_counterfactual_pnl_10m_krw"), 0) for row in rows))
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
                [_safe_float((row.get("metrics_5m") or {}).get("close_ret_pct"), 0.0) for row in rows]
            ),
            "avg_close_10m_pct": _avg(
                [_safe_float((row.get("metrics_10m") or {}).get("close_ret_pct"), 0.0) for row in rows]
            ),
            "avg_mfe_10m_pct": _avg(
                [_safe_float((row.get("metrics_10m") or {}).get("mfe_pct"), 0.0) for row in rows]
            ),
            "avg_mae_10m_pct": _avg(
                [_safe_float((row.get("metrics_10m") or {}).get("mae_pct"), 0.0) for row in rows]
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
        missed = sum(1 for row in rows if str(row.get("outcome") or "") == "MISSED_WINNER")
        avoided = sum(1 for row in rows if str(row.get("outcome") or "") == "AVOIDED_LOSER")
        metrics[cohort] = {
            "cohort": cohort,
            "evaluated_candidates": total,
            "missed_winner_rate": _ratio(missed, total),
            "avoided_loser_rate": _ratio(avoided, total),
            "avg_close_10m_pct": _avg(
                [_safe_float((row.get("metrics_10m") or {}).get("close_ret_pct"), 0.0) for row in rows]
            ),
            "avg_mfe_10m_pct": _avg(
                [_safe_float((row.get("metrics_10m") or {}).get("mfe_pct"), 0.0) for row in rows]
            ),
            "avg_mae_10m_pct": _avg(
                [_safe_float((row.get("metrics_10m") or {}).get("mae_pct"), 0.0) for row in rows]
            ),
        }
    return metrics


def missed_entry_counterfactual_summary_to_dict(summary: MissedEntryCounterfactualSummary) -> dict:
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
    all_buy_attempts = _build_buy_attempts(safe_date, include_submitted=True)
    candidates = [item for item in all_buy_attempts if str(item.get("attempt_status") or "") == "MISSED"]
    summary = MissedEntryCounterfactualSummary(date=safe_date)
    summary.total_candidates = len(candidates)

    if not candidates:
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
                "estimated_counterfactual_pnl_10m_krw_sum": 0,
                "blocker_outcome_metrics": {},
                "cohort_outcome_metrics": {},
            },
            "buy_signal_universe": {
                "metrics": {
                    "total_buy_judged_attempts": int(len(all_buy_attempts)),
                    "entered_attempts": int(sum(1 for item in all_buy_attempts if str(item.get("attempt_status") or "") == "ENTERED")),
                    "missed_attempts": int(sum(1 for item in all_buy_attempts if str(item.get("attempt_status") or "") == "MISSED")),
                },
                "confidence_breakdown": [],
                "rows": [],
            },
            "insight": {
                "headline": "AI BUY 후 미진입 counterfactual 표본이 없습니다.",
                "comment": "장중 BUY 후 주문전 차단 사례가 쌓이면 missed winner / avoided loser를 함께 해석할 수 있습니다.",
            },
            "reason_breakdown": [],
            "top_missed_winners": [],
            "top_avoided_losers": [],
            "rows": [],
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

    candle_cache: dict[str, list[dict]] = {}
    evaluations: list[dict] = []
    all_buy_evaluations: list[dict] = []

    for candidate in all_buy_attempts:
        code = str(candidate.get("stock_code") or "").strip()[:6]
        if not code or token is None or kiwoom_utils is None:
            continue
        if code not in candle_cache:
            try:
                candle_cache[code] = kiwoom_utils.get_minute_candles_ka10080(token, code, limit=700) or []
            except Exception as exc:
                log_error(f"[MISSED_ENTRY_CF] {code} minute candles fetch failed: {exc}")
                candle_cache[code] = []

        candles = candle_cache.get(code, [])
        metrics_5m = _compute_window_metrics(candidate, candles, 5)
        metrics_10m = _compute_window_metrics(candidate, candles, 10)
        outcome = _classify_candidate(metrics_5m, metrics_10m)
        entry_price_used = _safe_int(metrics_10m.get("entry_price_used"), 0)
        capacity = _sim_virtual_qty(entry_price_used, _safe_float(candidate.get("ai_score"), 0.0))
        qty = _safe_int(capacity.get("qty"), 0)
        est_pnl_10m = int(round(entry_price_used * qty * (_safe_float(metrics_10m.get("close_ret_pct"), 0.0) / 100.0))) if entry_price_used > 0 and qty > 0 else 0
        evaluations.append(
            {
                **candidate,
                "outcome": outcome,
                "metrics_5m": metrics_5m,
                "metrics_10m": metrics_10m,
                "entry_price_used": entry_price_used,
                "price_source": "explicit_target_buy_price" if _safe_int(candidate.get("signal_price"), 0) > 0 else "minute_candle_proxy",
                "counterfactual_qty": int(qty),
                "counterfactual_qty_source": "sim_virtual_budget_dynamic_formula" if qty > 0 else "unpriced",
                "virtual_budget_override": True,
                "virtual_budget_krw": int(capacity.get("virtual_budget_krw") or 0),
                "counterfactual_ratio": round(float(capacity.get("ratio") or 0.0), 4),
                "counterfactual_target_budget": int(capacity.get("target_budget") or 0),
                "counterfactual_safe_budget": int(capacity.get("safe_budget") or 0),
                "counterfactual_safety_ratio": round(float(capacity.get("safety_ratio") or 0.0), 4),
                "counterfactual_max_budget": int(capacity.get("max_budget") or 0),
                "counterfactual_notional_krw": int(entry_price_used * qty) if entry_price_used > 0 and qty > 0 else 0,
                "real_target_qty_observed": _safe_int(candidate.get("target_qty"), 0),
                "estimated_counterfactual_pnl_10m_krw": est_pnl_10m,
            }
        )
        if str(candidate.get("attempt_status") or "") == "MISSED":
            all_buy_evaluations.append(evaluations[-1])
        else:
            all_buy_evaluations.append(evaluations[-1])

    # Keep missed-only evaluation slice for the main summary.
    evaluations = [item for item in all_buy_evaluations if str(item.get("attempt_status") or "") == "MISSED"]

    summary.evaluated_candidates = len(evaluations)
    outcome_counts: dict[str, int] = {"MISSED_WINNER": 0, "AVOIDED_LOSER": 0, "NEUTRAL": 0}
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
        [item for item in evaluations if str(item.get("outcome") or "") == "MISSED_WINNER"],
        key=_winner_score,
        reverse=True,
    )[: max(1, int(top_n or 10))]
    summary.top_avoided_losers = sorted(
        [item for item in evaluations if str(item.get("outcome") or "") == "AVOIDED_LOSER"],
        key=_loser_score,
        reverse=True,
    )[: max(1, int(top_n or 10))]

    evaluated_count = len(evaluations)
    missed_winner_rate = _ratio(outcome_counts.get("MISSED_WINNER", 0), evaluated_count)
    avoided_loser_rate = _ratio(outcome_counts.get("AVOIDED_LOSER", 0), evaluated_count)
    explicit_rows = [item for item in evaluations if str(item.get("price_source") or "") == "explicit_target_buy_price"]
    explicit_count = len(explicit_rows)
    explicit_missed_rate = _ratio(
        sum(1 for item in explicit_rows if str(item.get("outcome") or "") == "MISSED_WINNER"),
        explicit_count,
    )
    explicit_avoided_rate = _ratio(
        sum(1 for item in explicit_rows if str(item.get("outcome") or "") == "AVOIDED_LOSER"),
        explicit_count,
    )
    avg_close_5m = _avg([_safe_float((item.get("metrics_5m") or {}).get("close_ret_pct"), 0.0) for item in evaluations])
    avg_close_10m = _avg([_safe_float((item.get("metrics_10m") or {}).get("close_ret_pct"), 0.0) for item in evaluations])
    avg_mfe_10m = _avg([_safe_float((item.get("metrics_10m") or {}).get("mfe_pct"), 0.0) for item in evaluations])
    avg_mae_10m = _avg([_safe_float((item.get("metrics_10m") or {}).get("mae_pct"), 0.0) for item in evaluations])
    estimated_pnl_sum = int(sum(_safe_int(item.get("estimated_counterfactual_pnl_10m_krw"), 0) for item in evaluations))

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
    reason_breakdown = []
    for stage, items in sorted(reason_buckets.items(), key=lambda pair: len(pair[1]), reverse=True):
        trades = len(items)
        missed_count = sum(1 for item in items if str(item.get("outcome") or "") == "MISSED_WINNER")
        avoided_count = sum(1 for item in items if str(item.get("outcome") or "") == "AVOIDED_LOSER")
        reason_breakdown.append(
            {
                "stage": stage,
                "stage_label": _stage_label(stage),
                "candidates": trades,
                "missed_winner_rate": _ratio(missed_count, trades),
                "avoided_loser_rate": _ratio(avoided_count, trades),
                "avg_close_10m_pct": _avg([_safe_float((item.get("metrics_10m") or {}).get("close_ret_pct"), 0.0) for item in items]),
                "avg_mfe_10m_pct": _avg([_safe_float((item.get("metrics_10m") or {}).get("mfe_pct"), 0.0) for item in items]),
                "avg_mae_10m_pct": _avg([_safe_float((item.get("metrics_10m") or {}).get("mae_pct"), 0.0) for item in items]),
            }
        )

    def _row_view(item: dict) -> dict:
        metrics_5m = item.get("metrics_5m", {}) or {}
        metrics_10m = item.get("metrics_10m", {}) or {}
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
            "signal_time": str(item.get("signal_time") or ""),
            "signal_price": int(_safe_int(item.get("signal_price"), 0)),
            "entry_price_used": int(_safe_int(item.get("entry_price_used"), 0)),
            "target_qty": int(_safe_int(item.get("target_qty"), 0)),
            "counterfactual_qty": int(_safe_int(item.get("counterfactual_qty"), 0)),
            "counterfactual_qty_source": str(item.get("counterfactual_qty_source") or ""),
            "virtual_budget_krw": int(_safe_int(item.get("virtual_budget_krw"), 0)),
            "counterfactual_ratio": round(_safe_float(item.get("counterfactual_ratio"), 0.0), 4),
            "counterfactual_safe_budget": int(_safe_int(item.get("counterfactual_safe_budget"), 0)),
            "counterfactual_notional_krw": int(_safe_int(item.get("counterfactual_notional_krw"), 0)),
            "ai_score": round(_safe_float(item.get("ai_score"), 0.0), 1),
            "price_source": str(item.get("price_source") or "minute_candle_proxy"),
            "confidence_tier": _confidence_tier(item),
            "outcome": str(item.get("outcome") or "NEUTRAL"),
            "close_5m_pct": round(_safe_float(metrics_5m.get("close_ret_pct"), 0.0), 3),
            "close_10m_pct": round(_safe_float(metrics_10m.get("close_ret_pct"), 0.0), 3),
            "mfe_10m_pct": round(_safe_float(metrics_10m.get("mfe_pct"), 0.0), 3),
            "mae_10m_pct": round(_safe_float(metrics_10m.get("mae_pct"), 0.0), 3),
            "estimated_counterfactual_pnl_10m_krw": int(_safe_int(item.get("estimated_counterfactual_pnl_10m_krw"), 0)),
            "missed_submit_cohort": str(item.get("missed_submit_cohort") or ""),
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
            "estimated_counterfactual_pnl_10m_krw_sum": int(estimated_pnl_sum),
            "blocker_outcome_metrics": blocker_outcome_metrics,
            "cohort_outcome_metrics": cohort_outcome_metrics,
        },
        "buy_signal_universe": {
            "metrics": {
                "total_buy_judged_attempts": int(len(all_buy_attempts)),
                "entered_attempts": int(sum(1 for item in all_buy_attempts if str(item.get("attempt_status") or "") == "ENTERED")),
                "missed_attempts": int(sum(1 for item in all_buy_attempts if str(item.get("attempt_status") or "") == "MISSED")),
                "entered_rate": _ratio(
                    sum(1 for item in all_buy_attempts if str(item.get("attempt_status") or "") == "ENTERED"),
                    len(all_buy_attempts),
                ),
            },
            "confidence_breakdown": [
                {
                    "tier": tier,
                    "attempts": len(items),
                    "entered_attempts": sum(1 for item in items if str(item.get("attempt_status") or "") == "ENTERED"),
                    "missed_attempts": sum(1 for item in items if str(item.get("attempt_status") or "") == "MISSED"),
                }
                for tier, items in sorted(
                    defaultdict(list, {
                        tier: [item for item in all_buy_evaluations if _confidence_tier(item) == tier]
                        for tier in ("A", "B", "C")
                    }).items()
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
        "rows": [_row_view(item) for item in evaluations[: max(1, int(top_n or 10) * 3)]],
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
