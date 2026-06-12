"""Report-first score smoothing for real WATCHING Tier 1 decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


POLICY_VERSION = "watching_score_smoothing_v1"
VALID_MODES = frozenset({"off", "report_only", "applied"})
MAX_OBSERVATIONS = 6
WINDOW_SEC = 180.0
HALF_LIFE_SEC = 75.0
SHARP_DROP_POINTS = 15.0
MANUAL_REVIEW_CRITERION_RULES = {
    "buy_wait_flip_rate_reduction_pct": ("minimum", 20.0),
    "sharp_drop_delay_p95_sec": ("maximum", 30.0),
    "projected_buy_source_quality_adjusted_ev_pct": ("minimum_delta", 0.0),
    "projected_missed_upside_delta_pctp": ("maximum", 2.0),
    "parse_fallback_lock_contention_degradation": ("required", "no_degradation"),
    "safety_and_provenance_guards": ("required", "no_breach"),
}


def normalize_mode(value: Any) -> str:
    mode = str(value or "off").strip().lower()
    return mode if mode in VALID_MODES else "off"


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "stale"}


def excluded_reason(ai_result: dict[str, Any], *, quote_stale: bool = False, context_stale: bool = False) -> str:
    source = str(ai_result.get("ai_result_source") or ai_result.get("result_source") or "").strip().lower()
    reason = str(ai_result.get("reason") or "").strip().lower()
    if _truthy(quote_stale) or _truthy(context_stale) or _truthy(ai_result.get("quote_stale")) or _truthy(ai_result.get("tick_context_stale")):
        return "stale_context_or_quote"
    if source == "lock_contention" or "ai contention" in reason:
        return "lock_contention"
    if source == "engine_disabled" or "engine disabled" in reason:
        return "engine_disabled"
    if _truthy(ai_result.get("ai_fallback_score_50")):
        return "fallback_score_50"
    if _truthy(ai_result.get("cache_hit")) or source == "cache":
        return "cache_hit_same_input"
    if _truthy(ai_result.get("ai_parse_fail")) or not _truthy(ai_result.get("ai_parse_ok")):
        return "parse_invalid"
    return ""


def _trim_observations(observations: Iterable[dict[str, Any]], now_ts: float) -> list[dict[str, Any]]:
    valid = [
        dict(item)
        for item in observations
        if 0.0 <= now_ts - _float(item.get("observed_at"), -1.0) <= WINDOW_SEC
    ]
    valid.sort(key=lambda item: _float(item.get("observed_at"), 0.0))
    return valid[-MAX_OBSERVATIONS:]


def _time_weighted_score(observations: list[dict[str, Any]], now_ts: float) -> float:
    weighted = []
    for item in observations:
        age = max(0.0, now_ts - _float(item.get("observed_at"), now_ts))
        weight = math.pow(0.5, age / HALF_LIFE_SEC)
        weighted.append((_float(item.get("score"), 50.0), weight))
    total_weight = sum(weight for _, weight in weighted)
    if total_weight <= 0:
        return _float(observations[-1].get("score"), 50.0)
    return sum(score * weight for score, weight in weighted) / total_weight


@dataclass(frozen=True)
class WatchingScoreDecision:
    mode: str
    raw_score: float
    projected_score: float
    applied_score: float
    smoothing_applied: bool
    confidence: str
    valid_observation_count: int
    dispersion: float
    action_consistency: float
    excluded_reason: str
    buy_guard_blocked: bool
    policy_version: str = POLICY_VERSION

    def provenance_fields(self, *, early_refresh_trigger: str = "-") -> dict[str, Any]:
        return {
            "ai_score_raw": round(self.raw_score, 2),
            "ai_score_projected": round(self.projected_score, 2),
            "ai_score_smoothing_mode": self.mode,
            "ai_score_smoothing_applied": self.smoothing_applied,
            "ai_score_smoothing_confidence": self.confidence,
            "ai_score_valid_observation_count": self.valid_observation_count,
            "ai_score_dispersion": round(self.dispersion, 3),
            "ai_action_consistency": round(self.action_consistency, 4),
            "ai_early_refresh_trigger": early_refresh_trigger or "-",
            "ai_score_excluded_reason": self.excluded_reason or "-",
            "ai_score_buy_guard_blocked": self.buy_guard_blocked,
            "ai_score_policy_version": self.policy_version,
        }


def evaluate_watching_score(
    observations: Iterable[dict[str, Any]],
    *,
    now_ts: float,
    raw_score: float,
    action: str,
    mode: str,
    ai_result: dict[str, Any],
    previous_applied_score: float | None = None,
    quote_stale: bool = False,
    context_stale: bool = False,
) -> tuple[WatchingScoreDecision, list[dict[str, Any]]]:
    resolved_mode = normalize_mode(mode)
    raw = max(0.0, min(100.0, _float(raw_score, 50.0)))
    reason = excluded_reason(ai_result, quote_stale=quote_stale, context_stale=context_stale)
    retained = _trim_observations(observations, now_ts)
    if resolved_mode == "off":
        return WatchingScoreDecision(resolved_mode, raw, raw, raw, False, "off", len(retained), 0.0, 0.0, reason, False), retained
    if reason:
        fail_closed = min(raw, 50.0, _float(previous_applied_score, 50.0)) if resolved_mode == "applied" else raw
        return WatchingScoreDecision(resolved_mode, raw, raw, fail_closed, False, "excluded", len(retained), 0.0, 0.0, reason, False), retained

    retained.append({"observed_at": float(now_ts), "score": raw, "action": str(action or "WAIT").upper()})
    retained = _trim_observations(retained, now_ts)
    scores = [_float(item.get("score"), 50.0) for item in retained]
    projected = raw if len(retained) == 1 else _time_weighted_score(retained, now_ts)
    previous = raw if previous_applied_score is None else _float(previous_applied_score, raw)
    if str(action or "").upper() == "DROP" or raw <= previous - SHARP_DROP_POINTS:
        projected = raw
    confidence = "ready" if len(retained) >= 3 else "warming_up"
    recent_actions = [str(item.get("action") or "WAIT").upper() for item in retained[-3:]]
    consistency = max(Counter(recent_actions).values()) / len(recent_actions) if recent_actions else 0.0
    dispersion = statistics.pstdev(scores) if len(scores) >= 2 else 0.0
    normalized_action = str(action or "WAIT").upper()
    buy_votes = sum(1 for item in recent_actions if item == "BUY")
    buy_guard_blocked = normalized_action == "BUY" and (raw < 75.0 or len(retained) < 3 or buy_votes < 2)
    if normalized_action != "BUY" or raw < 75.0:
        projected = min(projected, raw)
    elif len(retained) < 3 or buy_votes < 2:
        projected = min(projected, 74.0)
    can_apply = resolved_mode == "applied" and len(retained) >= 2
    applied = projected if can_apply else raw
    return (
        WatchingScoreDecision(
            resolved_mode,
            raw,
            max(0.0, min(100.0, projected)),
            max(0.0, min(100.0, applied)),
            can_apply,
            confidence,
            len(retained),
            dispersion,
            consistency,
            "",
            buy_guard_blocked,
        ),
        retained,
    )


def diagnostic_artifact_path(target_date: str, root: Path = Path("data/report")) -> Path:
    return root / "ai_watching_score_smoothing_diagnostic" / f"ai_watching_score_smoothing_diagnostic_{target_date}.json"


def _load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except (TypeError, ValueError):
                continue
            if row.get("stage") in {"ai_confirmed", "ai_watching_score_projection"}:
                rows.append(row)
    return rows


def _artifact_check(path: Path, *, target_date: str = "", role: str = "", expected_sha256: str = "") -> dict[str, Any]:
    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
    expected = str(expected_sha256 or "").strip().lower()
    return {
        "path": str(path),
        "target_date": str(target_date or ""),
        "role": str(role or ""),
        "exists": path.is_file(),
        "sha256": actual_sha256,
        "sha256_match": bool(expected and actual_sha256 == expected),
    }


def _manual_review_value_matches(*, operator: str, observed: Any, threshold: Any) -> bool:
    if operator == "required":
        return str(observed or "").strip().lower() == str(threshold or "").strip().lower()
    try:
        observed_value = float(observed)
        threshold_value = float(threshold)
    except (TypeError, ValueError):
        return False
    if operator in {"minimum", "minimum_delta"}:
        return observed_value >= threshold_value
    if operator in {"maximum", "maximum_delta"}:
        return observed_value <= threshold_value
    return False


def _same_scalar(left: Any, right: Any) -> bool:
    try:
        return abs(float(left) - float(right)) <= 1e-9
    except (TypeError, ValueError):
        return str(left or "").strip().lower() == str(right or "").strip().lower()


def _manual_review_threshold_matches(*, operator: str, actual: Any, expected: Any) -> bool:
    if operator == "required":
        return _same_scalar(actual, expected)
    try:
        return abs(float(actual) - float(expected)) <= 1e-9
    except (TypeError, ValueError):
        return False


def _normal_session_dates(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(item) for item in value if str(item))


def _manual_review_artifact_matches(
    path: Path,
    *,
    criterion: str,
    item: dict[str, Any],
    session_dates: list[str],
) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return False
    if not isinstance(payload, dict):
        return False
    if str(payload.get("criterion") or "").strip() != criterion:
        return False
    for field_name in ("status", "observed", "threshold"):
        if field_name not in payload:
            return False
    if str(payload.get("status") or "").strip().lower() != str(item.get("status") or "").strip().lower():
        return False
    if not _same_scalar(payload.get("observed"), item.get("observed")):
        return False
    if not _same_scalar(payload.get("threshold"), item.get("threshold")):
        return False
    if _normal_session_dates(payload.get("session_dates")) != session_dates:
        return False
    if _normal_session_dates(item.get("session_dates")) != session_dates:
        return False
    return True


def _manual_review_criterion_passed(criterion: str, item: Any, *, session_dates: list[str]) -> bool:
    if not isinstance(item, dict):
        return False
    operator, expected_threshold = MANUAL_REVIEW_CRITERION_RULES.get(criterion, ("", None))
    if not operator:
        return False
    if str(item.get("status") or "").strip().lower() != "pass":
        return False
    if "observed" not in item or item.get("observed") in (None, ""):
        return False
    if "threshold" not in item or item.get("threshold") in (None, ""):
        return False
    if not _manual_review_threshold_matches(
        operator=operator,
        actual=item.get("threshold"),
        expected=expected_threshold,
    ):
        return False
    if not _manual_review_value_matches(operator=operator, observed=item.get("observed"), threshold=item.get("threshold")):
        return False
    artifact_path = Path(str(item.get("artifact_path") or ""))
    expected_sha256 = str(item.get("sha256") or "").strip().lower()
    if not artifact_path.is_file() or not expected_sha256:
        return False
    if hashlib.sha256(artifact_path.read_bytes()).hexdigest() != expected_sha256:
        return False
    return _manual_review_artifact_matches(
        artifact_path,
        criterion=criterion,
        item=item,
        session_dates=session_dates,
    )


def build_diagnostic_artifact(
    target_date: str,
    *,
    data_root: Path = Path("data"),
    write: bool = False,
    guard_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = guard_evidence if isinstance(guard_evidence, dict) else {}
    session_dates = sorted({str(item) for item in (evidence.get("normal_session_dates") or []) if str(item)})
    artifact_checks = []
    for item in evidence.get("artifacts") or []:
        if not isinstance(item, dict):
            continue
        path = Path(str(item.get("path") or ""))
        artifact_checks.append(
            _artifact_check(
                path,
                target_date=str(item.get("target_date") or ""),
                role=str(item.get("role") or ""),
                expected_sha256=str(item.get("sha256") or ""),
            )
        )
    artifact_dates = {item["target_date"] for item in artifact_checks if item["target_date"]}
    required_roles = {"post_sell", "source_quality", "postclose_verification"}
    roles_by_date = {
        session_date: {item["role"] for item in artifact_checks if item["target_date"] == session_date}
        for session_date in session_dates
    }
    evidence_accepted = bool(
        evidence.get("reviewed") is True
        and str(evidence.get("source") or "").strip()
        and len(session_dates) >= 3
        and len(artifact_checks) >= len(session_dates) * len(required_roles)
        and all(item["exists"] and item["sha256_match"] for item in artifact_checks)
        and set(session_dates).issubset(artifact_dates)
        and all(required_roles.issubset(roles_by_date.get(session_date, set())) for session_date in session_dates)
    )
    selected_dates = session_dates if evidence_accepted else [target_date]
    source_paths = [data_root / "pipeline_events" / f"pipeline_events_{item}.jsonl" for item in selected_dates]
    input_artifact_checks = [
        _artifact_check(path, target_date=session_date, role="pipeline_events")
        for session_date, path in zip(selected_dates, source_paths, strict=False)
    ]
    pipeline_input_integrity_passed = bool(input_artifact_checks) and all(
        item["exists"] and item["sha256"] for item in input_artifact_checks
    )
    events = []
    for session_date, source_path in zip(selected_dates, source_paths, strict=False):
        for event in _load_events(source_path):
            event = dict(event)
            event["_diagnostic_session_date"] = session_date
            events.append(event)
    rows = []
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exclusion_counts: Counter[str] = Counter()
    for event in events:
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if "ai_score_policy_version" not in fields:
            continue
        symbol = str(event.get("stock_code") or "-")
        row = {
            "symbol": symbol,
            "emitted_at": event.get("emitted_at"),
            "event_stage": event.get("stage"),
            "session_date": event.get("_diagnostic_session_date") or target_date,
            **fields,
        }
        rows.append(row)
        by_symbol[symbol].append(row)
        reason = str(fields.get("ai_score_excluded_reason") or "-")
        if reason != "-":
            exclusion_counts[reason] += 1

    regular_rows = [row for row in rows if row.get("event_stage") == "ai_confirmed"]
    projection_rows = [row for row in rows if row.get("event_stage") == "ai_watching_score_projection"]
    regular_rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    projection_rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in regular_rows:
        regular_rows_by_session[str(row.get("session_date") or target_date)].append(row)
    for row in projection_rows:
        projection_rows_by_session[str(row.get("session_date") or target_date)].append(row)
    primary_observation_rows: list[dict[str, Any]] = []
    primary_observation_stages_by_session: dict[str, str] = {}
    for session_date in selected_dates:
        session_regular_rows = regular_rows_by_session.get(session_date, [])
        if session_regular_rows:
            primary_observation_rows.extend(session_regular_rows)
            primary_observation_stages_by_session[session_date] = "ai_confirmed"
            continue
        session_projection_rows = projection_rows_by_session.get(session_date, [])
        primary_observation_rows.extend(session_projection_rows)
        primary_observation_stages_by_session[session_date] = (
            "ai_watching_score_projection" if session_projection_rows else "none"
        )
    observed_primary_stages = {
        stage for stage in primary_observation_stages_by_session.values() if stage != "none"
    }
    primary_observation_stage = (
        next(iter(observed_primary_stages))
        if len(observed_primary_stages) == 1
        else "mixed_by_session"
        if observed_primary_stages
        else "none"
    )
    valid_rows = [
        row
        for row in primary_observation_rows
        if str(row.get("ai_score_excluded_reason") or "-") == "-"
    ]
    raw_scores = [_float(row.get("ai_score_raw")) for row in valid_rows]
    projected_scores = [_float(row.get("ai_score_projected")) for row in valid_rows]
    projection_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in projection_rows:
        projection_by_symbol[row["symbol"]].append(row)
    valid_projection_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid_rows:
        valid_projection_by_symbol[row["symbol"]].append(row)
    sequence_count = sum(1 for items in valid_projection_by_symbol.values() if len(items) >= 3)
    raw_stddev = statistics.pstdev(raw_scores) if len(raw_scores) >= 2 else None
    projected_stddev = statistics.pstdev(projected_scores) if len(projected_scores) >= 2 else None
    stddev_reduction_pct = (
        (raw_stddev - projected_stddev) / raw_stddev * 100.0
        if raw_stddev not in (None, 0.0) and projected_stddev is not None
        else None
    )
    primary_exclusion_counts = Counter(
        str(row.get("ai_score_excluded_reason"))
        for row in primary_observation_rows
        if str(row.get("ai_score_excluded_reason") or "-") != "-"
    )
    projection_exclusion_counts = Counter(
        str(row.get("ai_score_excluded_reason"))
        for row in projection_rows
        if str(row.get("ai_score_excluded_reason") or "-") != "-"
    )
    contention_count = primary_exclusion_counts.get("lock_contention", 0)
    primary_observation_count = len(primary_observation_rows)
    contention_rate = contention_count / primary_observation_count * 100.0 if primary_observation_count else None
    parse_invalid_count = primary_exclusion_counts.get("parse_invalid", 0)
    fallback_count = primary_exclusion_counts.get("fallback_score_50", 0)
    engine_disabled_count = primary_exclusion_counts.get("engine_disabled", 0)
    cache_hit_count = primary_exclusion_counts.get("cache_hit_same_input", 0)
    parse_invalid_rate = parse_invalid_count / primary_observation_count * 100.0 if primary_observation_count else None
    fallback_or_lock_contention_rate = (
        (fallback_count + contention_count) / primary_observation_count * 100.0 if primary_observation_count else None
    )
    engine_disabled_rate = engine_disabled_count / primary_observation_count * 100.0 if primary_observation_count else None
    cache_hit_rate = cache_hit_count / primary_observation_count * 100.0 if primary_observation_count else None
    stale_invalid_applied_count = sum(
        1
        for row in rows
        if str(row.get("ai_score_smoothing_mode") or "off") == "applied"
        and str(row.get("ai_score_excluded_reason") or "-") != "-"
    )
    projection_session_count = len({row["session_date"] for row in valid_rows})
    criteria = {
        "pipeline_input_integrity": {
            "required": "all_selected_pipeline_files_present",
            "observed": f"{sum(1 for item in input_artifact_checks if item['exists'])}/{len(input_artifact_checks)}",
            "status": "pass" if pipeline_input_integrity_passed else "fail",
        },
        "normal_session_count": {"required": 3, "observed": projection_session_count, "status": "pass" if projection_session_count >= 3 else "pending"},
        "valid_response_count": {"required": 300, "observed": len(valid_rows), "status": "pass" if len(valid_rows) >= 300 else "pending"},
        "unique_symbol_count": {"required": 20, "observed": len(valid_projection_by_symbol), "status": "pass" if len(valid_projection_by_symbol) >= 20 else "pending"},
        "sequence_3plus_count": {"required": 50, "observed": sequence_count, "status": "pass" if sequence_count >= 50 else "pending"},
        "lock_contention_rate_pct": {"maximum": 1.0, "observed": contention_rate, "status": "pass" if contention_rate is not None and contention_rate <= 1.0 else "pending"},
        "fallback_or_lock_contention_absolute_cap_pct": {
            "maximum": 2.0,
            "observed": fallback_or_lock_contention_rate,
            "status": "pass" if fallback_or_lock_contention_rate is not None and fallback_or_lock_contention_rate <= 2.0 else "pending",
        },
        "engine_disabled_rate_pct": {
            "maximum": 0.0,
            "observed": engine_disabled_rate,
            "status": "pass" if engine_disabled_rate is not None and engine_disabled_rate <= 0.0 else "pending",
        },
        "stale_invalid_included_count": {"maximum": 0, "observed": stale_invalid_applied_count, "status": "pass" if stale_invalid_applied_count == 0 else "fail"},
        "score_stddev_reduction_pct": {"minimum": 20.0, "observed": stddev_reduction_pct, "status": "pass" if stddev_reduction_pct is not None and stddev_reduction_pct >= 20.0 else "pending"},
        "buy_wait_flip_rate_reduction_pct": {"minimum": 20.0, "observed": None, "status": "manual_review_required"},
        "sharp_drop_delay_p95_sec": {"maximum": 30.0, "observed": None, "status": "manual_review_required"},
        "projected_buy_source_quality_adjusted_ev_pct": {"minimum_delta": 0.0, "observed": None, "status": "manual_review_required"},
        "projected_missed_upside_delta_pctp": {"maximum": 2.0, "observed": None, "status": "manual_review_required"},
        "parse_fallback_lock_contention_degradation": {"required": "no_degradation", "observed": None, "status": "manual_review_required"},
        "safety_and_provenance_guards": {"required": "no_breach", "observed": None, "status": "manual_review_required"},
    }
    # External review files are provenance only. Transition criteria must be
    # derived by this producer from canonical artifacts, never supplied by a caller.
    automatic_criteria = {
        key: item
        for key, item in criteria.items()
        if item.get("status") != "manual_review_required"
    }
    manual_review_required = [
        key for key, item in criteria.items() if item.get("status") == "manual_review_required"
    ]
    manual_review = evidence.get("manual_review") if evidence_accepted and isinstance(evidence.get("manual_review"), dict) else {}
    manual_review_criteria = manual_review.get("criteria") if isinstance(manual_review.get("criteria"), dict) else {}
    manual_review_passed = bool(
        manual_review
        and manual_review.get("reviewed") is True
        and str(manual_review.get("status") or "").strip().lower() == "pass"
        and all(
            _manual_review_criterion_passed(
                key,
                manual_review_criteria.get(key),
                session_dates=selected_dates,
            )
            for key in manual_review_required
        )
    )
    if manual_review_passed:
        for key in manual_review_required:
            criteria[key] = {
                **criteria[key],
                "status": "pass",
                "manual_review_source": str(manual_review.get("source") or evidence.get("source") or "manual_postclose_review"),
            }
    automatic_criteria_passed = bool(automatic_criteria) and all(
        item.get("status") == "pass" for item in automatic_criteria.values()
    )
    eligible = automatic_criteria_passed and (not manual_review_required or manual_review_passed)
    applied_candidate_status = (
        "eligible"
        if eligible
        else "manual_review_required"
        if automatic_criteria_passed and manual_review_required
        else "await_required_evidence"
    )
    payload = {
        "schema_version": 1,
        "report_type": "ai_watching_score_smoothing_diagnostic",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "decision_authority": "report_only_no_automation_chain_authority",
        "runtime_effect": False,
        "forbidden_uses": ["threshold_cycle_input", "adm_ldm_input", "preopen_auto_apply", "order_authority"],
        "source": str(source_paths[0]) if len(source_paths) == 1 else [str(item) for item in source_paths],
        "guard_evidence_source": str(evidence.get("source") or "-") if evidence else "-",
        "guard_evidence_accepted": evidence_accepted,
        "normal_session_dates": session_dates,
        "guard_evidence_artifact_checks": artifact_checks,
        "input_artifact_checks": input_artifact_checks,
        "metrics": {
            "observed_count": len(rows),
            "primary_observation_stage": primary_observation_stage,
            "primary_observation_stages_by_session": primary_observation_stages_by_session,
            "primary_observation_count": primary_observation_count,
            "normal_session_count": projection_session_count,
            "regular_observed_count": len(regular_rows),
            "projection_observed_count": len(projection_rows),
            "early_projection_observed_count": len(projection_rows),
            "valid_response_count": len(valid_rows),
            "unique_symbol_count": len(valid_projection_by_symbol),
            "sequence_3plus_count": sequence_count,
            "raw_score_stddev": round(raw_stddev, 4) if raw_stddev is not None else None,
            "projected_score_stddev": round(projected_stddev, 4) if projected_stddev is not None else None,
            "score_stddev_reduction_pct": round(stddev_reduction_pct, 2) if stddev_reduction_pct is not None else None,
            "lock_contention_rate_pct": round(contention_rate, 4) if contention_rate is not None else None,
            "fallback_or_lock_contention_absolute_cap_pct": (
                round(fallback_or_lock_contention_rate, 4) if fallback_or_lock_contention_rate is not None else None
            ),
            "parse_invalid_rate_observed_pct": round(parse_invalid_rate, 4) if parse_invalid_rate is not None else None,
            "engine_disabled_rate_pct": round(engine_disabled_rate, 4) if engine_disabled_rate is not None else None,
            "cache_hit_same_input_rate_observed_pct": round(cache_hit_rate, 4) if cache_hit_rate is not None else None,
            "exclusion_counts": dict(sorted(exclusion_counts.items())),
            "primary_exclusion_counts": dict(sorted(primary_exclusion_counts.items())),
            "projection_exclusion_counts": dict(sorted(projection_exclusion_counts.items())),
        },
        "transition_guard": {
            "eligible": eligible,
            "status": (
                "eligible_for_next_preopen_applied_review"
                if eligible
                else "manual_postclose_review_required"
                if automatic_criteria_passed and manual_review_required
                else "await_required_evidence"
            ),
            "applied_candidate_status": applied_candidate_status,
            "automatic_criteria_passed": automatic_criteria_passed,
            "manual_review_passed": manual_review_passed,
            "manual_review_required_criteria": manual_review_required,
            "minimum_requirements": {"valid_response_count": 300, "unique_symbol_count": 20, "sequence_3plus_count": 50, "normal_session_count": 3},
            "criteria": criteria,
            "applied_rollback_guards": {
                "fallback_or_lock_contention_rate_pct_max": 2.0,
                "sharp_drop_delay_p95_sec_max": 45.0,
                "stale_invalid_applied_count_max": 0,
                "source_quality_or_provenance_breach_allowed": False,
                "missed_upside_delta_pctp_max": 5.0,
                "source_quality_adjusted_ev_degradation_allowed": False,
            },
            "note": "Only a next-PREOPEN operator/runtime-env decision may consume eligibility; this artifact is not an automation-chain input.",
        },
    }
    if write:
        path = diagnostic_artifact_path(target_date, data_root / "report")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload["artifact_path"] = str(path)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build report-only WATCHING score smoothing diagnostics")
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--guard-evidence", type=Path)
    args = parser.parse_args()
    guard_evidence = None
    if args.guard_evidence:
        guard_evidence = json.loads(args.guard_evidence.read_text(encoding="utf-8"))
    print(
        json.dumps(
            build_diagnostic_artifact(args.target_date, write=args.write, guard_evidence=guard_evidence),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
