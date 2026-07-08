"""Recommend next-preopen latency classifier thresholds from pipeline events."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.trading.config.entry_config import EntryConfig
from src.utils.constants import DATA_DIR


PIPELINE_EVENT_DIR = DATA_DIR / "pipeline_events"
REPORT_DIR = DATA_DIR / "report" / "latency_classifier_recommendation"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"

FAMILY = "latency_classifier_runtime_profile"
STAGE = "entry_latency_classifier"
TARGET_ENV_KEYS = [
    "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION",
    "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION",
    "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION",
    "SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO",
]
DEFAULT_CURRENT_VALUES = {
    "max_ws_age_ms_for_caution": 700,
    "max_ws_jitter_ms_for_caution": 300,
    "max_spread_ratio_for_caution": 0.005,
    "recovery_enabled": False,
    "recovery_min_signal_score": 75.0,
    "recovery_max_ws_age_ms": 1200,
    "recovery_max_ws_jitter_ms": 1500,
    "recovery_max_spread_ratio": 0.0100,
}
SYNTHETIC_CODES = {"123456", "000000", "-", ""}
SYNTHETIC_NAMES = {"TEST", "DUMMY", "MOCK"}


@dataclass(frozen=True)
class ThresholdProfile:
    profile_id: str
    max_ws_age_ms_for_caution: int
    max_ws_jitter_ms_for_caution: int
    max_spread_ratio_for_caution: float


PROFILES = [
    ThresholdProfile("current_700_300_0050", 700, 300, 0.0050),
    ThresholdProfile("quote_fresh_950_450_0075", 950, 450, 0.0075),
    ThresholdProfile("mechanical_1200_500_0085", 1200, 500, 0.0085),
    ThresholdProfile("balanced_1200_1500_0100", 1200, 1500, 0.0100),
    ThresholdProfile("loose_age_1500_1500_0100", 1500, 1500, 0.0100),
]
RECOMMENDED_PROFILE_ID = "balanced_1200_1500_0100"
DEFAULT_ENTRY_CONFIG = EntryConfig()
RECOVERY_MIN_SIGNAL_SCORE = 75.0
RECOVERY_PROFILE_MAX_WS_AGE_MS = 1500
RECOVERY_PROFILE_MAX_WS_JITTER_MS = 1500
RECOVERY_PROFILE_MAX_SPREAD_RATIO = 0.0120
RECOVERY_EVENT_FLOOR_RATIO = 0.10
COUNTERFACTUAL_SAMPLE_FLOOR = 3
GRID_QUANTILES = (0.25, 0.5, 0.75, 0.9, 0.95)


def report_json_path(target_date: str) -> Path:
    return REPORT_DIR / f"latency_classifier_recommendation_{target_date}.json"


def report_md_path(target_date: str) -> Path:
    return REPORT_DIR / f"latency_classifier_recommendation_{target_date}.md"


def _event_source_path(target_date: str) -> Path:
    plain = PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl"
    if plain.exists():
        return plain
    gz = PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl.gz"
    return gz


def _counterfactual_source_path(target_date: str) -> Path:
    plain = MONITOR_SNAPSHOT_DIR / f"missed_entry_counterfactual_{target_date}.json"
    if plain.exists():
        return plain
    gz = MONITOR_SNAPSHOT_DIR / f"missed_entry_counterfactual_{target_date}.json.gz"
    return gz


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value in {None, "", "-"}:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_synthetic(event: dict[str, Any]) -> bool:
    code = str(event.get("stock_code") or "").strip().zfill(6)
    name = str(event.get("stock_name") or "").strip().upper()
    if code in SYNTHETIC_CODES:
        return True
    return any(token in name for token in SYNTHETIC_NAMES)


def _boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _record_key(stock_code: Any, record_id: Any) -> tuple[str, str]:
    return (str(stock_code or "").strip().zfill(6), str(record_id or "").strip())


def _broker_bypass_required(event: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(event.get(key) or "")
        for key in (
            "reason",
            "decision",
            "blocked_stage",
            "decision_authority",
            "threshold_family",
            "latency_danger_reasons",
        )
    ).lower()
    return any(
        token in haystack
        for token in (
            "broker_submit_guard",
            "broker_guard",
            "account_order",
            "order_qty_guard",
            "cooldown_guard",
            "hard_safety",
        )
    )


def _latency_block_events(target_date: str, *, source_path: Path | None = None) -> list[dict[str, Any]]:
    path = source_path or _event_source_path(target_date)
    events: list[dict[str, Any]] = []
    for event in _read_jsonl(path):
        if event.get("pipeline") != "ENTRY_PIPELINE" or event.get("stage") != "latency_block":
            continue
        if _is_synthetic(event):
            continue
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        ws_age_ms = _to_float(fields.get("ws_age_ms"))
        ws_jitter_ms = _to_float(fields.get("ws_jitter_ms"))
        spread_ratio = _to_float(fields.get("spread_ratio"))
        if ws_age_ms is None or ws_jitter_ms is None or spread_ratio is None:
            continue
        events.append(
            {
                "stock_code": str(event.get("stock_code") or "").strip(),
                "stock_name": event.get("stock_name"),
                "record_id": event.get("record_id"),
                "ws_age_ms": ws_age_ms,
                "ws_jitter_ms": ws_jitter_ms,
                "spread_ratio": spread_ratio,
                "quote_stale": str(fields.get("quote_stale") or "").lower() == "true",
                "latency": fields.get("latency"),
                "decision": fields.get("decision"),
                "reason": fields.get("reason"),
                "ai_score": _to_float(fields.get("ai_score")),
                "latency_danger_reasons": fields.get("latency_danger_reasons"),
                "blocked_stage": fields.get("blocked_stage"),
                "threshold_family": fields.get("threshold_family"),
                "decision_authority": fields.get("decision_authority"),
                "actual_order_submitted": _boolish(fields.get("actual_order_submitted")),
                "broker_order_forbidden": _boolish(fields.get("broker_order_forbidden")),
                "emitted_at": event.get("emitted_at"),
            }
        )
    return events


def _load_counterfactual_labels(target_date: str) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    path = _counterfactual_source_path(target_date)
    payload = _read_json_dict(path)
    full_rows = payload.get("full_rows") if isinstance(payload.get("full_rows"), list) else []
    display_rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    rows = full_rows or display_rows
    row_source = "full_rows" if full_rows else "rows"
    labels: dict[tuple[str, str], dict[str, Any]] = {}
    terminal_stage_counts: Counter[str] = Counter()
    duplicate_keys = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _record_key(row.get("stock_code"), row.get("record_id"))
        if not key[0] or not key[1]:
            continue
        terminal_stage = str(row.get("terminal_stage") or "")
        terminal_stage_counts[terminal_stage] += 1
        if terminal_stage != "latency_block":
            continue
        if key in labels:
            duplicate_keys += 1
        labels[key] = row
    return labels, {
        "path": str(path),
        "status": "loaded" if payload else "missing",
        "row_source": row_source if payload else "missing",
        "row_count": len(rows),
        "full_row_count": len(full_rows),
        "display_row_count": len(display_rows),
        "latency_block_label_count": len(labels),
        "duplicate_latency_block_label_keys": duplicate_keys,
        "terminal_stage_counts": dict(sorted(terminal_stage_counts.items())),
    }


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _grid_values(
    events: list[dict[str, Any]],
    key: str,
    *,
    defaults: Iterable[float],
    cap: float,
    integer: bool = False,
) -> list[float]:
    observed = [
        float(event[key])
        for event in events
        if not bool(event.get("quote_stale")) and float(event.get(key) or 0.0) > 0
    ]
    values = {float(value) for value in defaults if float(value) > 0}
    for quantile in GRID_QUANTILES:
        value = min(cap, _quantile(observed, quantile))
        if value > 0:
            values.add(float(round(value)) if integer else round(float(value), 6))
    values.add(float(cap))
    if integer:
        return [float(int(value)) for value in sorted(values) if value <= cap]
    return [float(value) for value in sorted(values) if value <= cap]


def _build_profiles(events: list[dict[str, Any]]) -> list[ThresholdProfile]:
    profiles: dict[tuple[int, int, float], ThresholdProfile] = {}
    for profile in PROFILES:
        key = (
            int(profile.max_ws_age_ms_for_caution),
            int(profile.max_ws_jitter_ms_for_caution),
            round(float(profile.max_spread_ratio_for_caution), 6),
        )
        profiles[key] = profile

    age_values = _grid_values(
        events,
        "ws_age_ms",
        defaults=[700, 950, 1200, 1500],
        cap=RECOVERY_PROFILE_MAX_WS_AGE_MS,
        integer=True,
    )
    jitter_values = _grid_values(
        events,
        "ws_jitter_ms",
        defaults=[300, 450, 500, 1000, 1500],
        cap=RECOVERY_PROFILE_MAX_WS_JITTER_MS,
        integer=True,
    )
    spread_values = _grid_values(
        events,
        "spread_ratio",
        defaults=[0.0050, 0.0075, 0.0085, 0.0100, 0.0120],
        cap=RECOVERY_PROFILE_MAX_SPREAD_RATIO,
    )
    for age in age_values:
        for jitter in jitter_values:
            for spread in spread_values:
                key = (int(age), int(jitter), round(float(spread), 6))
                if key in profiles:
                    continue
                spread_token = int(round(float(spread) * 10000))
                profiles[key] = ThresholdProfile(
                    f"grid_age{int(age)}_jitter{int(jitter)}_spread{spread_token:04d}",
                    int(age),
                    int(jitter),
                    round(float(spread), 6),
                )
    return sorted(
        profiles.values(),
        key=lambda item: (
            item.max_ws_age_ms_for_caution,
            item.max_ws_jitter_ms_for_caution,
            item.max_spread_ratio_for_caution,
            item.profile_id,
        ),
    )


def _counterfactual_summary_for_events(
    recovery_candidates: list[dict[str, Any]],
    counterfactual_labels: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    attempted_keys = {
        _record_key(event.get("stock_code"), event.get("record_id"))
        for event in recovery_candidates
        if _record_key(event.get("stock_code"), event.get("record_id"))[1]
    }
    joined_rows = [counterfactual_labels[key] for key in sorted(attempted_keys) if key in counterfactual_labels]
    outcome_counts = Counter(str(row.get("outcome") or "UNKNOWN") for row in joined_rows)
    pnl_values = [_to_float(row.get("estimated_counterfactual_pnl_10m_krw"), 0.0) or 0.0 for row in joined_rows]
    notional_values = [_to_float(row.get("counterfactual_notional_krw"), 0.0) or 0.0 for row in joined_rows]
    close_values = [_to_float(row.get("close_10m_pct"), None) for row in joined_rows]
    close_values = [value for value in close_values if value is not None]
    pnl_sum = int(round(sum(pnl_values)))
    notional_sum = int(round(sum(notional_values)))
    ev_pct = round((float(pnl_sum) / float(notional_sum)) * 100.0, 4) if notional_sum > 0 else None
    return {
        "counterfactual_joined_sample": len(joined_rows),
        "counterfactual_joinable_attempts": len(attempted_keys),
        "counterfactual_join_rate_pct": round((len(joined_rows) / len(attempted_keys)) * 100.0, 1)
        if attempted_keys
        else 0.0,
        "counterfactual_ev_pct": ev_pct,
        "counterfactual_avg_close_10m_pct": round(sum(close_values) / len(close_values), 4)
        if close_values
        else None,
        "counterfactual_pnl_10m_krw_sum": pnl_sum,
        "counterfactual_notional_krw_sum": notional_sum,
        "missed_winner_recovered": int(outcome_counts.get("MISSED_WINNER", 0)),
        "avoided_loser_lost": int(outcome_counts.get("AVOIDED_LOSER", 0)),
        "neutral_recovered": int(outcome_counts.get("NEUTRAL", 0)),
        "counterfactual_outcome_counts": dict(sorted(outcome_counts.items())),
        "counterfactual_label_examples": [
            {
                "candidate_id": row.get("candidate_id"),
                "stock_code": row.get("stock_code"),
                "record_id": row.get("record_id"),
                "outcome": row.get("outcome"),
                "close_10m_pct": row.get("close_10m_pct"),
                "estimated_counterfactual_pnl_10m_krw": row.get("estimated_counterfactual_pnl_10m_krw"),
            }
            for row in joined_rows[:5]
        ],
    }


def _profile_result(
    profile: ThresholdProfile,
    events: list[dict[str, Any]],
    counterfactual_labels: dict[tuple[str, str], dict[str, Any]],
    *,
    total_events: int,
) -> dict[str, Any]:
    safe_passed: list[dict[str, Any]] = []
    caution_normal_candidates: list[dict[str, Any]] = []
    hard_rejected: list[dict[str, Any]] = []
    recovery_candidates: list[dict[str, Any]] = []
    stale_quote_candidates: list[dict[str, Any]] = []
    broker_bypass_candidates: list[dict[str, Any]] = []
    fallback_deprecated_excluded_from_pass = 0

    for event in events:
        quote_stale = bool(event.get("quote_stale"))
        reason = str(event.get("reason") or event.get("decision") or "")
        broker_bypass = _broker_bypass_required(event)
        safe = (
            not quote_stale
            and reason != "latency_fallback_deprecated"
            and not broker_bypass
            and event["ws_age_ms"] <= DEFAULT_ENTRY_CONFIG.max_ws_age_ms_for_safe
            and event["ws_jitter_ms"] <= DEFAULT_ENTRY_CONFIG.max_ws_jitter_ms_for_safe
            and event["spread_ratio"] <= DEFAULT_ENTRY_CONFIG.max_spread_ratio_for_safe
        )
        caution = (
            not quote_stale
            and event["ws_age_ms"] <= profile.max_ws_age_ms_for_caution
            and event["ws_jitter_ms"] <= profile.max_ws_jitter_ms_for_caution
            and event["spread_ratio"] <= profile.max_spread_ratio_for_caution
        )
        if safe:
            safe_passed.append(event)
        elif caution:
            caution_normal_candidates.append(event)
            if reason == "latency_fallback_deprecated":
                fallback_deprecated_excluded_from_pass += 1
            ai_score = _to_float(event.get("ai_score"), 0.0) or 0.0
            if quote_stale:
                stale_quote_candidates.append(event)
            elif broker_bypass:
                broker_bypass_candidates.append(event)
            elif reason == "latency_fallback_deprecated" and ai_score >= RECOVERY_MIN_SIGNAL_SCORE:
                recovery_candidates.append(event)
        else:
            hard_rejected.append(event)

    unique_safe_codes = {str(event.get("stock_code") or "") for event in safe_passed if event.get("stock_code")}
    unique_recovery_codes = {
        str(event.get("stock_code") or "") for event in recovery_candidates if event.get("stock_code")
    }
    unique_recovery_attempts = {
        _record_key(event.get("stock_code"), event.get("record_id"))
        for event in recovery_candidates
        if _record_key(event.get("stock_code"), event.get("record_id"))[1]
    }
    total = len(events)
    reason_breakdown = dict(
        sorted(
            Counter(str(event.get("reason") or event.get("decision") or "unknown") for event in events).items()
        )
    )
    recovery_reason_breakdown = dict(
        sorted(
            Counter(str(event.get("reason") or event.get("decision") or "unknown") for event in recovery_candidates).items()
        )
    )
    cf_summary = _counterfactual_summary_for_events(recovery_candidates, counterfactual_labels)
    recovery_floor = max(10, int(total_events * RECOVERY_EVENT_FLOOR_RATIO))
    stale_quote_override = len(stale_quote_candidates)
    broker_guard_bypass = len(broker_bypass_candidates)
    ev_pct = cf_summary.get("counterfactual_ev_pct")
    joined = int(cf_summary.get("counterfactual_joined_sample") or 0)
    missed_winners = int(cf_summary.get("missed_winner_recovered") or 0)
    avoided_losers = int(cf_summary.get("avoided_loser_lost") or 0)
    action = "reject"
    action_reason = (
        f"recovery_count={len(recovery_candidates)} below floor={recovery_floor}"
    )
    if stale_quote_override > 0:
        action_reason = f"stale_quote_override_events={stale_quote_override}"
    elif broker_guard_bypass > 0:
        action_reason = f"broker_guard_bypass_candidates={broker_guard_bypass}"
    elif len(recovery_candidates) >= recovery_floor:
        if joined < COUNTERFACTUAL_SAMPLE_FLOOR:
            action = "hold"
            action_reason = (
                f"counterfactual_joined_sample={joined} below floor={COUNTERFACTUAL_SAMPLE_FLOOR}"
            )
        elif ev_pct is None or float(ev_pct) <= 0.0:
            action = "hold"
            action_reason = f"counterfactual_ev_pct={ev_pct} not positive"
        elif avoided_losers > missed_winners:
            action = "hold"
            action_reason = (
                f"avoided_loser_lost={avoided_losers} exceeds missed_winner_recovered={missed_winners}"
            )
        else:
            action = "bounded_apply"
            action_reason = (
                f"counterfactual_ev_pct={ev_pct} joined_sample={joined} "
                f"recovery_count={len(recovery_candidates)}"
            )
    return {
        "profile_id": profile.profile_id,
        "profile_source": "fixed_seed" if profile in PROFILES else "grid_quantile",
        "max_ws_age_ms_for_caution": profile.max_ws_age_ms_for_caution,
        "max_ws_jitter_ms_for_caution": profile.max_ws_jitter_ms_for_caution,
        "max_spread_ratio_for_caution": profile.max_spread_ratio_for_caution,
        "would_pass_events": len(safe_passed),
        "would_pass_unique_codes": len(unique_safe_codes),
        "would_pass_ratio": round(len(safe_passed) / total, 6) if total else 0.0,
        "would_safe_pass_events": len(safe_passed),
        "would_safe_pass_unique_codes": len(unique_safe_codes),
        "would_caution_normal_events": len(caution_normal_candidates),
        "would_recovery_canary_events": len(recovery_candidates),
        "would_recovery_canary_unique_codes": len(unique_recovery_codes),
        "would_recovery_canary_attempts": len(unique_recovery_attempts),
        "hard_reject_events": len(hard_rejected),
        "quote_stale_override_events": stale_quote_override,
        "stale_quote_override_events": stale_quote_override,
        "broker_guard_bypass_candidates": broker_guard_bypass,
        "fallback_deprecated_excluded_from_pass_events": fallback_deprecated_excluded_from_pass,
        "runtime_semantics": {
            "safe": "EntryPolicy.ALLOW_NORMAL",
            "caution": "EntryPolicy.ALLOW_NORMAL:caution_normal_entry_allowed",
            "danger": "EntryPolicy.REJECT_DANGER",
            "recovery": "deprecated_not_needed_for_caution",
        },
        "reason_breakdown": reason_breakdown,
        "recovery_reason_breakdown": recovery_reason_breakdown,
        "recommended_action": action,
        "recommended_action_reason": action_reason,
        **cf_summary,
    }


def _build_candidate(target_date: str, profile: dict[str, Any], total_events: int) -> dict[str, Any]:
    sample_floor = 20
    recovery_floor = max(10, int(total_events * RECOVERY_EVENT_FLOOR_RATIO))
    recovery_count = int(profile.get("would_recovery_canary_events") or 0)
    quote_stale_override = int(profile.get("quote_stale_override_events") or 0)
    broker_guard_bypass = int(profile.get("broker_guard_bypass_candidates") or 0)
    recommended_action = str(profile.get("recommended_action") or "reject")
    runtime_simplified = True
    eligible = False
    if eligible:
        state = "adjust_up"
    elif runtime_simplified:
        state = "hold"
    elif recovery_count < recovery_floor or int(profile.get("counterfactual_joined_sample") or 0) < COUNTERFACTUAL_SAMPLE_FLOOR:
        state = "hold_sample"
    elif quote_stale_override > 0 or broker_guard_bypass > 0:
        state = "freeze"
    else:
        state = "hold_no_edge"
    reason = (
        f"recommended_action=bounded_apply; {profile.get('recommended_action_reason')}"
        if eligible
        else (
            "latency runtime simplified: CAUTION no longer blocks submit after slippage check; "
            "DANGER/stale/broker safety remains blocked; no adaptive latency env apply"
        )
        if runtime_simplified
        else (
            f"recommended_action={recommended_action}; {profile.get('recommended_action_reason')}; "
            f"latency_blocks={total_events} recovery_count={recovery_count} floor={recovery_floor} "
            f"quote_stale_override={quote_stale_override} broker_guard_bypass={broker_guard_bypass}"
        )
    )
    return {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 6,
        "allowed_runtime_apply": eligible,
        "runtime_effect": False if runtime_simplified else True,
        "safety_revert_required": False,
        "calibration_state": state,
        "calibration_reason": reason,
        "target_env_keys": TARGET_ENV_KEYS,
        "current_values": DEFAULT_CURRENT_VALUES,
        "recommended_values": {
            "max_ws_age_ms_for_caution": int(profile["max_ws_age_ms_for_caution"]),
            "max_ws_jitter_ms_for_caution": int(profile["max_ws_jitter_ms_for_caution"]),
            "max_spread_ratio_for_caution": float(profile["max_spread_ratio_for_caution"]),
            "recovery_enabled": bool(eligible),
            "recovery_min_signal_score": RECOVERY_MIN_SIGNAL_SCORE,
            "recovery_max_ws_age_ms": int(profile["max_ws_age_ms_for_caution"]),
            "recovery_max_ws_jitter_ms": int(profile["max_ws_jitter_ms_for_caution"]),
            "recovery_max_spread_ratio": float(profile["max_spread_ratio_for_caution"]),
        },
        "threshold_version": f"{FAMILY}:{target_date}:{profile['profile_id']}",
        "sample_count": total_events,
        "sample_floor": sample_floor,
        "recovery_floor": recovery_floor,
        "source_reports": [str(report_json_path(target_date))],
        "source_metrics": {
            "metric_role": "runtime_latency_classifier_calibration",
            "decision_authority": "next_preopen_env_apply_only",
            "window_policy": "same_day_postclose_latency_block_events",
            "primary_decision_metric": "counterfactual_ev_pct_after_runtime_semantics",
            "source_quality_gate": (
                "ENTRY_PIPELINE latency_block numeric fields + missed_entry_counterfactual latency_block join "
                "+ stale/broker bypass exclusion"
            ),
            "profile_runtime_semantics": "SAFE and CAUTION pass after slippage check; DANGER remains blocked",
            "simplified_runtime_semantics": (
                "SAFE and CAUTION pass after slippage check; DANGER, stale quote, broker/account/order/qty/cooldown "
                "guards remain blocking. Historical latency_fallback_deprecated rows are audit evidence, not runtime apply proof."
            ),
            "recommended_action": recommended_action,
            "recommended_action_reason": profile.get("recommended_action_reason"),
            "would_safe_pass_events": int(profile.get("would_safe_pass_events") or 0),
            "would_caution_normal_events": int(profile.get("would_caution_normal_events") or 0),
            "would_recovery_canary_events": recovery_count,
            "would_recovery_canary_attempts": int(profile.get("would_recovery_canary_attempts") or 0),
            "hard_reject_events": int(profile.get("hard_reject_events") or 0),
            "quote_stale_override_events": quote_stale_override,
            "stale_quote_override_events": int(profile.get("stale_quote_override_events") or 0),
            "broker_guard_bypass_candidates": broker_guard_bypass,
            "fallback_deprecated_excluded_from_pass_events": int(
                profile.get("fallback_deprecated_excluded_from_pass_events") or 0
            ),
            "counterfactual_joined_sample": int(profile.get("counterfactual_joined_sample") or 0),
            "counterfactual_joinable_attempts": int(profile.get("counterfactual_joinable_attempts") or 0),
            "counterfactual_join_rate_pct": profile.get("counterfactual_join_rate_pct"),
            "counterfactual_ev_pct": profile.get("counterfactual_ev_pct"),
            "counterfactual_avg_close_10m_pct": profile.get("counterfactual_avg_close_10m_pct"),
            "counterfactual_pnl_10m_krw_sum": int(profile.get("counterfactual_pnl_10m_krw_sum") or 0),
            "counterfactual_notional_krw_sum": int(profile.get("counterfactual_notional_krw_sum") or 0),
            "missed_winner_recovered": int(profile.get("missed_winner_recovered") or 0),
            "avoided_loser_lost": int(profile.get("avoided_loser_lost") or 0),
            "neutral_recovered": int(profile.get("neutral_recovered") or 0),
            "counterfactual_outcome_counts": profile.get("counterfactual_outcome_counts") or {},
            "reason_breakdown": profile.get("reason_breakdown") or {},
            "recovery_reason_breakdown": profile.get("recovery_reason_breakdown") or {},
            "r0_r6_consumer_map": {
                "R0_collect": "latency_block/latency_pass/order_bundle_submitted provenance",
                "R1_daily_report": "SAFE/CAUTION normal/DANGER hard reject split plus counterfactual EV",
                "R2_cumulative_report": "rolling latency submit recovery attribution and label coverage",
                "R3_manifest_only": "runtime-semantics-matched EV-ranked profile candidate",
                "R4_preopen_apply_candidate": "auto_bounded_live guard consumes recommended_action",
                "R5_bounded_calibrated_apply": "no adaptive latency env apply after CAUTION normal-submit simplification",
                "R6_post_apply_attribution": "predicted recovery vs actual latency_pass/order_bundle_submitted and EV",
            },
            "forbidden_uses": [
                "intraday_threshold_mutation",
                "provider_transport_change",
                "broker_submit_guard_bypass",
            ],
            "selected_profile": profile,
        },
    }


def build_report(target_date: str, *, source_path: Path | None = None) -> dict[str, Any]:
    events = _latency_block_events(target_date, source_path=source_path)
    counterfactual_labels, counterfactual_source = _load_counterfactual_labels(target_date)
    profiles = _build_profiles(events)
    profile_results = [
        _profile_result(profile, events, counterfactual_labels, total_events=len(events)) for profile in profiles
    ]
    recommended = max(
        profile_results,
        key=lambda item: (
            {"bounded_apply": 2, "hold": 1, "reject": 0}.get(str(item.get("recommended_action") or ""), 0),
            float(item.get("counterfactual_ev_pct") if item.get("counterfactual_ev_pct") is not None else -9999.0),
            int(item.get("missed_winner_recovered") or 0) - int(item.get("avoided_loser_lost") or 0),
            int(item.get("would_recovery_canary_events") or 0),
            int(item.get("would_safe_pass_events") or 0),
            -float(item.get("max_spread_ratio_for_caution") or 0.0),
            -int(item.get("max_ws_jitter_ms_for_caution") or 0),
            -int(item.get("max_ws_age_ms_for_caution") or 0),
        ),
        default=next(item for item in profile_results if item["profile_id"] == RECOMMENDED_PROFILE_ID),
    )
    candidate = _build_candidate(target_date, recommended, len(events))
    return {
        "date": target_date,
        "family": FAMILY,
        "stage": STAGE,
        "source_path": str(source_path or _event_source_path(target_date)),
        "counterfactual_source": counterfactual_source,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "latency_block_count": len(events),
        "unique_codes": sorted({str(event.get("stock_code") or "") for event in events if event.get("stock_code")}),
        "quote_stale_true_count": sum(1 for event in events if bool(event.get("quote_stale"))),
        "profile_generation": {
            "mode": "grid_quantile_search",
            "profile_count": len(profile_results),
            "age_cap_ms": RECOVERY_PROFILE_MAX_WS_AGE_MS,
            "jitter_cap_ms": RECOVERY_PROFILE_MAX_WS_JITTER_MS,
            "spread_cap_ratio": RECOVERY_PROFILE_MAX_SPREAD_RATIO,
            "counterfactual_sample_floor": COUNTERFACTUAL_SAMPLE_FLOOR,
            "recovery_event_floor_ratio": RECOVERY_EVENT_FLOOR_RATIO,
        },
        "profile_results": profile_results,
        "selected_profile_id": recommended["profile_id"],
        "selection_reason": (
            "rank_by_recommended_action_then_counterfactual_ev_then_bounded_recovery_count"
        ),
        "calibration_candidate": candidate,
        "calibration_candidates": [candidate],
    }


def _render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# Latency Classifier Recommendation {payload.get('date')}",
        "",
        f"- latency_block_count: {payload.get('latency_block_count')}",
        f"- unique_codes: {len(payload.get('unique_codes') or [])}",
        f"- selected_profile_id: {payload.get('selected_profile_id')}",
        f"- profile_generation: `{json.dumps(payload.get('profile_generation') or {}, ensure_ascii=False)}`",
        f"- counterfactual_source_status: `{(payload.get('counterfactual_source') or {}).get('status')}`",
        "",
        "| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    ranked = sorted(
        payload.get("profile_results") or [],
        key=lambda item: (
            {"bounded_apply": 2, "hold": 1, "reject": 0}.get(str(item.get("recommended_action") or ""), 0),
            float(item.get("counterfactual_ev_pct") if item.get("counterfactual_ev_pct") is not None else -9999.0),
            int(item.get("would_recovery_canary_events") or 0),
        ),
        reverse=True,
    )
    for item in ranked[:30]:
        lines.append(
            "| {profile_id} | {action} | {age} | {jitter} | {spread:.4f} | {safe} | {caution} | {recovery} | {cf_sample} | {cf_ev} | {missed} | {avoided} | {stale} | {broker} |".format(
                profile_id=item.get("profile_id"),
                action=item.get("recommended_action"),
                age=item.get("max_ws_age_ms_for_caution"),
                jitter=item.get("max_ws_jitter_ms_for_caution"),
                spread=float(item.get("max_spread_ratio_for_caution") or 0.0),
                safe=item.get("would_safe_pass_events"),
                caution=item.get("would_caution_normal_events"),
                recovery=item.get("would_recovery_canary_events"),
                cf_sample=item.get("counterfactual_joined_sample"),
                cf_ev=item.get("counterfactual_ev_pct"),
                missed=item.get("missed_winner_recovered"),
                avoided=item.get("avoided_loser_lost"),
                stale=item.get("stale_quote_override_events"),
                broker=item.get("broker_guard_bypass_candidates"),
            )
        )
    candidate = payload.get("calibration_candidate") or {}
    lines.extend(
        [
            "",
            "## Apply Candidate",
            "",
            f"- calibration_state: {candidate.get('calibration_state')}",
            f"- allowed_runtime_apply: {candidate.get('allowed_runtime_apply')}",
            f"- recommended_values: `{json.dumps(candidate.get('recommended_values') or {}, ensure_ascii=False)}`",
            f"- reason: {candidate.get('calibration_reason')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(target_date: str, *, source_path: Path | None = None) -> dict[str, Any]:
    payload = build_report(target_date, source_path=source_path)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_json_path(target_date).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md_path(target_date).write_text(_render_md(payload), encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build latency classifier threshold recommendation.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target source date")
    parser.add_argument("--source-path", default=None, help="Optional pipeline_events jsonl/jsonl.gz path")
    args = parser.parse_args(argv)
    payload = write_report(args.date, source_path=Path(args.source_path) if args.source_path else None)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
