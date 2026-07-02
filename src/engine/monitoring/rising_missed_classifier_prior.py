"""Build source-only cumulative priors for rising-missed classification."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
OUTPUT_DIR = REPORT_DIR / "rising_missed_classifier_prior"
LIFECYCLE_BUCKET_DISCOVERY_DIR = REPORT_DIR / "lifecycle_bucket_discovery"
LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "lifecycle_decision_matrix"
KEY_LINEAGE_LEDGER_DIR = REPORT_DIR / "key_lineage_ledger"
CONVERSION_LANE_DIR = REPORT_DIR / "conversion_lane"
RISING_MISSED_SCOUT_WORKORDER_DIR = REPORT_DIR / "rising_missed_scout_workorder"
RISING_MISSED_INTRADAY_FEEDBACK_DIR = REPORT_DIR / "rising_missed_intraday_feedback"
MISSED_ENTRY_COUNTERFACTUAL_DIR = REPORT_DIR / "missed_entry_counterfactual"

KST = timezone(timedelta(hours=9))
CLEAN_BASELINE_TS_KST = "2026-06-04T14:29:09+09:00"
PREFIX_KEYS = (
    "entry_score_parent",
    "entry_source_parent",
    "source_signature",
    "liquidity_bucket",
    "strength_bucket",
    "overbought_bucket",
    "chosen_action",
)
WINDOW_PRIORITY = ("rolling10d", "rolling5d", "mtd", "daily")
FORBIDDEN_USES = [
    "real_order_submission",
    "runtime_threshold_mutation",
    "broker_guard_bypass",
    "provider_route_change",
    "bot_restart",
    "cap_release",
    "hard_safety_relaxation",
    "forced_one_share_success_counting",
]


def _now_kst_iso() -> str:
    return datetime.now(tz=KST).isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return int(default)
        return int(float(value))
    except Exception:
        return int(default)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        result = float(value)
    except Exception:
        return default
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _norm(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "-"


def _default_source_paths(target_date: str) -> dict[str, Path]:
    counterfactual_path = MISSED_ENTRY_COUNTERFACTUAL_DIR / f"missed_entry_counterfactual_{target_date}.json"
    if not counterfactual_path.exists():
        gzip_path = REPORT_DIR / "monitor_snapshots" / f"missed_entry_counterfactual_{target_date}.json.gz"
        if gzip_path.exists():
            counterfactual_path = gzip_path
    return {
        "lifecycle_bucket_discovery_daily": LIFECYCLE_BUCKET_DISCOVERY_DIR
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "lifecycle_bucket_discovery_rolling5d": LIFECYCLE_BUCKET_DISCOVERY_DIR
        / f"lifecycle_bucket_discovery_{target_date}_rolling5d.json",
        "lifecycle_bucket_discovery_rolling10d": LIFECYCLE_BUCKET_DISCOVERY_DIR
        / f"lifecycle_bucket_discovery_{target_date}_rolling10d.json",
        "lifecycle_bucket_discovery_mtd": LIFECYCLE_BUCKET_DISCOVERY_DIR
        / f"lifecycle_bucket_discovery_{target_date}_mtd.json",
        "lifecycle_decision_matrix": LIFECYCLE_DECISION_MATRIX_DIR
        / f"lifecycle_decision_matrix_{target_date}.json",
        "key_lineage_ledger": KEY_LINEAGE_LEDGER_DIR / f"key_lineage_ledger_{target_date}.json",
        "conversion_lane": CONVERSION_LANE_DIR / f"conversion_lane_{target_date}.json",
        "rising_missed_scout_workorder": RISING_MISSED_SCOUT_WORKORDER_DIR
        / f"rising_missed_scout_workorder_{target_date}.json",
        "rising_missed_intraday_feedback": RISING_MISSED_INTRADAY_FEEDBACK_DIR
        / f"rising_missed_intraday_feedback_{target_date}.json",
        "missed_entry_counterfactual": counterfactual_path,
    }


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    return (
        OUTPUT_DIR / f"rising_missed_classifier_prior_{target_date}.json",
        OUTPUT_DIR / f"rising_missed_classifier_prior_{target_date}.md",
    )


def _source_ref(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _prefix_key(prefix: dict[str, Any]) -> str:
    return "|".join(f"{key}={_norm(prefix.get(key))}" for key in PREFIX_KEYS)


def _empty_prefix() -> dict[str, str]:
    return {key: "-" for key in PREFIX_KEYS}


def _candidate_prefix(item: dict[str, Any]) -> dict[str, str]:
    prefix = _empty_prefix()
    for field in (
        "observable_prefix",
        "dimension_filters",
        "lifecycle_flow_parent_dimensions",
        "normalized_dimensions",
        "source_dimensions",
    ):
        source = item.get(field)
        if not isinstance(source, dict):
            continue
        for key in PREFIX_KEYS:
            if prefix[key] == "-" and source.get(key) not in (None, ""):
                prefix[key] = _norm(source.get(key))

    bucket_id = str(item.get("bucket_id") or item.get("parent_bucket_id") or "").lower()
    source_stage = str(item.get("source_stage") or item.get("bucket_type") or "").lower()
    action = str(item.get("chosen_action") or item.get("action") or item.get("decision") or "").lower()
    if "wait6579" in bucket_id or "wait6579" in source_stage:
        prefix["entry_source_parent"] = "entry_source_wait6579"
    if "liquidity_high" in bucket_id:
        prefix["liquidity_bucket"] = "liquidity_high"
    if "strong_strength_momentum" in bucket_id:
        prefix["strength_bucket"] = "strong_strength_momentum"
    if "overbought_normal" in bucket_id:
        prefix["overbought_bucket"] = "overbought_normal"
    if "wait_requote" in bucket_id or "wait_requote" in action:
        prefix["chosen_action"] = "wait_requote"
    if item.get("source_signature") not in (None, ""):
        prefix["source_signature"] = _norm(item.get("source_signature"))
    if item.get("entry_score_parent") not in (None, ""):
        prefix["entry_score_parent"] = _norm(item.get("entry_score_parent"))
    return prefix


def _first_float(item: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        result = _safe_float(item.get(key), None)
        if result is not None:
            return result
    return None


def _bucket_metric(item: dict[str, Any]) -> dict[str, Any]:
    ev_pct = _first_float(
        item,
        (
            "source_quality_adjusted_ev_pct",
            "parent_source_quality_adjusted_ev_pct",
            "equal_weight_avg_profit_pct",
            "parent_equal_weight_avg_profit_pct",
            "parent_ev_pct",
            "ev_pct",
        ),
    )
    sample = _safe_int(
        item.get("sample")
        or item.get("sample_count")
        or item.get("parent_sample")
        or item.get("joined_sample")
        or item.get("parent_joined_sample")
    )
    joined_sample = _safe_int(item.get("joined_sample") or item.get("parent_joined_sample") or sample)
    return {
        "sample": sample,
        "joined_sample": joined_sample,
        "ev_pct": ev_pct,
        "ev_metric": "source_quality_adjusted_ev_pct"
        if _safe_float(item.get("source_quality_adjusted_ev_pct"), None) is not None
        else "equal_weight_avg_profit_pct_fallback",
        "complete_flow_count": _safe_int(item.get("complete_flow_count") or item.get("parent_complete_flow_count")),
        "bucket_id": _norm(item.get("bucket_id") or item.get("parent_bucket_id")),
        "source_quality_gate": _norm(item.get("source_quality_gate") or item.get("source_quality_status")),
        "child_conflict_warning": bool(item.get("child_conflict_warning") or item.get("child_conflict")),
        "exclusion_dimension_candidate": bool(item.get("exclusion_dimension_candidate")),
        "source_dimension_gap": bool(item.get("source_dimension_gap")),
    }


def _iter_bucket_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    summary = _as_dict(report.get("summary"))
    candidates: list[dict[str, Any]] = []
    for field in (
        "sim_auto_positive_ev_top",
        "sim_auto_approved_candidates",
        "parent_bucket_summaries",
        "bucket_summaries",
        "source_only_blockers",
    ):
        candidates.extend(item for item in _as_list(report.get(field)) if isinstance(item, dict))
        candidates.extend(item for item in _as_list(summary.get(field)) if isinstance(item, dict))
    return candidates


def _new_prior(prefix: dict[str, str]) -> dict[str, Any]:
    return {
        "prior_key": _prefix_key(prefix),
        "observable_prefix": dict(prefix),
        "window_metrics": {},
        "rising_missed_metrics": {
            "forced_scout_count": 0,
            "winner_count": 0,
            "loser_count": 0,
            "avg_profit_rate": None,
            "initial_quality_fail_count": 0,
            "avg_down_ge2_count": 0,
            "counterfactual_missed_winner_count": 0,
            "counterfactual_avoided_loser_count": 0,
            "counterfactual_neutral_count": 0,
        },
        "lineage_status": {},
        "conflict_status": {
            "child_conflict": False,
            "exclusion_dimension_candidate": False,
            "source_dimension_gap": False,
            "source_quality_blocked": False,
        },
        "recommendation": "hold_sample",
        "confidence": "low",
        "selected_window": None,
        "reason": "waiting_for_rolling_prior",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _merge_window_metric(prior: dict[str, Any], window: str, metric: dict[str, Any]) -> None:
    current = prior["window_metrics"].get(window)
    if current:
        current_rank = (_safe_int(current.get("joined_sample")), _safe_float(current.get("ev_pct"), -9999.0) or -9999.0)
        next_rank = (_safe_int(metric.get("joined_sample")), _safe_float(metric.get("ev_pct"), -9999.0) or -9999.0)
        if current_rank >= next_rank:
            return
    prior["window_metrics"][window] = metric
    conflicts = prior["conflict_status"]
    conflicts["child_conflict"] = conflicts["child_conflict"] or bool(metric.get("child_conflict_warning"))
    conflicts["exclusion_dimension_candidate"] = conflicts["exclusion_dimension_candidate"] or bool(
        metric.get("exclusion_dimension_candidate")
    )
    conflicts["source_dimension_gap"] = conflicts["source_dimension_gap"] or bool(metric.get("source_dimension_gap"))
    gate = str(metric.get("source_quality_gate") or "").lower()
    conflicts["source_quality_blocked"] = conflicts["source_quality_blocked"] or "block" in gate or "fail" in gate


def _merge_lifecycle_windows(priors: dict[str, dict[str, Any]], source_payloads: dict[str, dict[str, Any]]) -> None:
    label_to_window = {
        "lifecycle_bucket_discovery_daily": "daily",
        "lifecycle_bucket_discovery_rolling5d": "rolling5d",
        "lifecycle_bucket_discovery_rolling10d": "rolling10d",
        "lifecycle_bucket_discovery_mtd": "mtd",
    }
    for label, window in label_to_window.items():
        for item in _iter_bucket_candidates(source_payloads.get(label, {})):
            prefix = _candidate_prefix(item)
            key = _prefix_key(prefix)
            prior = priors.setdefault(key, _new_prior(prefix))
            _merge_window_metric(prior, window, _bucket_metric(item))


def _source_signature_prefix(signature: Any) -> dict[str, str]:
    prefix = _empty_prefix()
    prefix["source_signature"] = _norm(signature)
    return prefix


def _add_profit(metrics: dict[str, Any], profit: float | None) -> None:
    if profit is None:
        return
    profits = metrics.setdefault("_profits", [])
    if isinstance(profits, list):
        profits.append(profit)
        metrics["avg_profit_rate"] = round(sum(profits) / len(profits), 4)


def _merge_scout_metrics(priors: dict[str, dict[str, Any]], report: dict[str, Any]) -> None:
    for field, outcome in (
        ("profitable_forced_scout_examples", "winner"),
        ("loss_or_flat_forced_scout_examples", "loser"),
        ("forced_scout_outcomes", "outcome"),
    ):
        for item in _as_list(report.get(field)):
            if not isinstance(item, dict):
                continue
            signature = item.get("source_signature") or item.get("scanner_promotion_reason") or "unknown_source_signature"
            prefix = _source_signature_prefix(signature)
            prior = priors.setdefault(_prefix_key(prefix), _new_prior(prefix))
            metrics = prior["rising_missed_metrics"]
            metrics["forced_scout_count"] += 1
            profit = _safe_float(item.get("profit_rate") or item.get("profit_pct"), None)
            if outcome == "winner" or (outcome == "outcome" and profit is not None and profit > 0):
                metrics["winner_count"] += 1
            elif outcome == "loser" or (outcome == "outcome" and profit is not None and profit <= 0):
                metrics["loser_count"] += 1
            _add_profit(metrics, profit)


def _merge_intraday_feedback(priors: dict[str, dict[str, Any]], report: dict[str, Any]) -> None:
    records = _as_list(report.get("records"))
    for item in records:
        if not isinstance(item, dict):
            continue
        signature = item.get("source_signature") or item.get("scanner_promotion_reason") or "unknown_source_signature"
        prefix = _source_signature_prefix(signature)
        prior = priors.setdefault(_prefix_key(prefix), _new_prior(prefix))
        metrics = prior["rising_missed_metrics"]
        label = str(item.get("feedback_label") or "").lower()
        if "initial_quality_fail" in label or bool(item.get("initial_quality_fail")):
            metrics["initial_quality_fail_count"] += 1
        if bool(item.get("avg_down_ge2_seen")) or _safe_int(item.get("avg_down_ge2_count")) > 0:
            metrics["avg_down_ge2_count"] += 1
    summary = _as_dict(report.get("summary"))
    if records or not summary:
        return
    if _safe_int(summary.get("initial_quality_fail_count")) or _safe_int(summary.get("rising_missed_avg_down_ge2_count")):
        prefix = _source_signature_prefix("summary_only_feedback")
        prior = priors.setdefault(_prefix_key(prefix), _new_prior(prefix))
        prior["rising_missed_metrics"]["initial_quality_fail_count"] += _safe_int(
            summary.get("initial_quality_fail_count")
        )
        prior["rising_missed_metrics"]["avg_down_ge2_count"] += _safe_int(
            summary.get("rising_missed_avg_down_ge2_count")
        )


def _counterfactual_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    primary_rows = _as_list(report.get("rows")) or _as_list(report.get("evaluations"))
    if primary_rows:
        rows.extend(item for item in primary_rows if isinstance(item, dict))
    else:
        for field in ("top_missed_winners", "top_avoided_losers"):
            rows.extend(item for item in _as_list(report.get(field)) if isinstance(item, dict))
    metrics = _as_dict(report.get("metrics"))
    refinement = _as_dict(metrics.get("rising_missed_refinement"))
    for field in ("by_source_signature", "by_scanner_promotion_reason"):
        for item in _as_list(refinement.get(field)):
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _merge_counterfactual_metrics(priors: dict[str, dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    rows = _counterfactual_rows(report)
    summary_counts = Counter()
    keyed_rows = 0
    for item in rows:
        outcome = str(item.get("outcome") or "").strip().upper()
        if not outcome:
            missed_count = _safe_int(item.get("missed_winner_count"))
            avoided_count = _safe_int(item.get("avoided_loser_count"))
            neutral_count = _safe_int(item.get("neutral_count"))
        else:
            missed_count = 1 if outcome == "MISSED_WINNER" else 0
            avoided_count = 1 if outcome == "AVOIDED_LOSER" else 0
            neutral_count = 1 if outcome == "NEUTRAL" else 0
        summary_counts["missed_winner"] += missed_count
        summary_counts["avoided_loser"] += avoided_count
        summary_counts["neutral"] += neutral_count
        signature = item.get("source_signature") or item.get("key") or item.get("scanner_promotion_reason")
        if not signature:
            continue
        prefix = _source_signature_prefix(signature)
        prior = priors.setdefault(_prefix_key(prefix), _new_prior(prefix))
        metrics = prior["rising_missed_metrics"]
        metrics["counterfactual_missed_winner_count"] += missed_count
        metrics["counterfactual_avoided_loser_count"] += avoided_count
        metrics["counterfactual_neutral_count"] += neutral_count
        keyed_rows += 1
    return {
        "counterfactual_row_count": len(rows),
        "counterfactual_keyed_row_count": keyed_rows,
        "counterfactual_missed_winner_count": summary_counts["missed_winner"],
        "counterfactual_avoided_loser_count": summary_counts["avoided_loser"],
        "counterfactual_neutral_count": summary_counts["neutral"],
    }


def _lineage_status(source_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_lineage = source_payloads.get("key_lineage_ledger", {})
    conversion = source_payloads.get("conversion_lane", {})
    lineage_summary = _as_dict(key_lineage.get("summary"))
    conversion_summary = _as_dict(conversion.get("summary"))
    blockers = _as_list(conversion.get("conversion_blocker_rank"))
    blocker_counts = Counter(str(item.get("blocker_class") or "unknown") for item in blockers if isinstance(item, dict))
    lineage_blockers = {
        "preopen_missing": _safe_int(lineage_summary.get("preopen_missing_count")),
        "catalog_missing": _safe_int(lineage_summary.get("catalog_missing_count")),
        "natural_match_0": _safe_int(lineage_summary.get("natural_match_0_count")),
        "followup_missing_parent_seed_id": _safe_int(lineage_summary.get("followup_missing_parent_seed_id_count")),
    }
    return {
        "catalog_connected": lineage_blockers["catalog_missing"] == 0,
        "preopen_connected": lineage_blockers["preopen_missing"] == 0,
        "runtime_connected": _safe_int(conversion_summary.get("runtime_candidate_count")) > 0,
        "postclose_connected": bool(key_lineage or conversion),
        "lineage_blockers": lineage_blockers,
        "conversion_blocker_counts": dict(sorted(blocker_counts.items())),
    }


def _select_window(prior: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    for window in WINDOW_PRIORITY:
        metric = prior["window_metrics"].get(window)
        if isinstance(metric, dict) and _safe_int(metric.get("joined_sample") or metric.get("sample")) > 0:
            return window, metric
    return None, None


def _classify_prior(prior: dict[str, Any]) -> None:
    selected_window, metric = _select_window(prior)
    conflicts = prior["conflict_status"]
    metrics = prior["rising_missed_metrics"]
    ev_pct = _safe_float((metric or {}).get("ev_pct"), None)
    rolling_positive = selected_window in {"rolling10d", "rolling5d"} and ev_pct is not None and ev_pct > 0
    daily_only_positive = selected_window == "daily" and ev_pct is not None and ev_pct > 0
    lineage_blocked = any(_safe_int(value) > 0 for value in prior["lineage_status"].get("lineage_blockers", {}).values())
    counterfactual_missed = _safe_int(metrics.get("counterfactual_missed_winner_count"))
    counterfactual_avoided = _safe_int(metrics.get("counterfactual_avoided_loser_count"))

    if any(conflicts.values()):
        recommendation = "source_quality_blocked"
        reason = "child_conflict_or_source_quality_gap"
        confidence = "blocked"
    elif counterfactual_avoided > 0 and counterfactual_avoided > counterfactual_missed:
        recommendation = "loss_filter"
        reason = "counterfactual_avoided_loser_exceeds_missed_winner"
        confidence = "medium"
    elif _safe_int(metrics.get("loser_count")) > 0 and _safe_int(metrics.get("winner_count")) == 0:
        recommendation = "loss_filter"
        reason = "rising_missed_forced_scout_loser_without_winner"
        confidence = "medium"
    elif _safe_int(metrics.get("initial_quality_fail_count")) > 0:
        recommendation = "quality_risk"
        reason = "intraday_initial_quality_fail_feedback"
        confidence = "medium"
    elif daily_only_positive:
        recommendation = "hold_sample"
        reason = "daily_positive_without_rolling_confirmation"
        confidence = "low"
    elif rolling_positive and prior["observable_prefix"].get("chosen_action") == "wait_requote":
        recommendation = "recheck_prior"
        reason = f"{selected_window}_positive_wait_requote_prior"
        confidence = "medium" if lineage_blocked else "high"
    elif rolling_positive:
        recommendation = "positive_prior"
        reason = f"{selected_window}_positive_ev_prior"
        confidence = "medium" if lineage_blocked else "high"
    elif counterfactual_missed > counterfactual_avoided:
        recommendation = "hold_sample"
        reason = "counterfactual_missed_winner_waiting_rolling_confirmation"
        confidence = "low"
    else:
        recommendation = "hold_sample"
        reason = "insufficient_positive_rolling_prior"
        confidence = "low"

    prior["recommendation"] = recommendation
    prior["confidence"] = confidence
    prior["selected_window"] = selected_window
    prior["reason"] = reason
    prior["runtime_effect"] = False
    prior["allowed_runtime_apply"] = False


def _strip_private_metrics(prior: dict[str, Any]) -> dict[str, Any]:
    clean = dict(prior)
    metrics = dict(clean.get("rising_missed_metrics") or {})
    metrics.pop("_profits", None)
    clean["rising_missed_metrics"] = metrics
    return clean


def _build_code_improvement_orders(summary: dict[str, Any]) -> list[dict[str, Any]]:
    if _safe_int(summary.get("prior_count")) <= 0:
        return []
    return [
        {
            "order_id": "order_rising_missed_classifier_prior_bridge",
            "title": "Attach cumulative ADM/LDM prior lookup to rising-missed classifier reports",
            "target_subsystem": "rising_missed_entry_classifier",
            "route": "instrumentation_order",
            "mapped_family": "rising_missed_classifier_prior_bridge",
            "threshold_family": "rising_missed_classifier_prior_bridge",
            "lifecycle_stage": "entry",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "implementation_status": "implemented",
            "implementation_provenance": {
                "implementation_type": "rising_missed_classifier_prior_source_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "root_cause_closure_status_hint": "implementation_done",
            },
            "evidence": [
                f"prior_count={_safe_int(summary.get('prior_count'))}",
                f"positive_prior_count={_safe_int(summary.get('positive_prior_count'))}",
                f"source_quality_blocked_count={_safe_int(summary.get('source_quality_blocked_count'))}",
                "runtime_effect=false",
            ],
            "forbidden_uses": list(FORBIDDEN_USES),
        }
    ]


def build_report(
    target_date: str,
    *,
    source_paths: dict[str, Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    paths = source_paths or _default_source_paths(target_date)
    payloads = {label: _load_json(path) for label, path in paths.items()}
    priors: dict[str, dict[str, Any]] = {}
    _merge_lifecycle_windows(priors, payloads)
    _merge_scout_metrics(priors, payloads.get("rising_missed_scout_workorder", {}))
    _merge_intraday_feedback(priors, payloads.get("rising_missed_intraday_feedback", {}))
    counterfactual_metrics = _merge_counterfactual_metrics(
        priors,
        payloads.get("missed_entry_counterfactual", {}),
    )
    lineage = _lineage_status(payloads)
    for prior in priors.values():
        prior["lineage_status"] = dict(lineage)
        _classify_prior(prior)

    prior_rows = sorted((_strip_private_metrics(prior) for prior in priors.values()), key=lambda row: row["prior_key"])
    recommendation_counts = Counter(row["recommendation"] for row in prior_rows)
    counterfactual_path = paths.get("missed_entry_counterfactual")
    counterfactual_status = "available" if counterfactual_path and counterfactual_path.exists() else "counterfactual_source_unavailable"
    source_quality = {
        "clean_tuning_baseline_ts_kst": CLEAN_BASELINE_TS_KST,
        "tuning_input_allowed": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "counterfactual_status": counterfactual_status,
        "missing_required_sources": [
            label for label, path in paths.items() if label != "missed_entry_counterfactual" and not path.exists()
        ],
    }
    summary = {
        "prior_count": len(prior_rows),
        "recommendation_counts": dict(sorted(recommendation_counts.items())),
        "positive_prior_count": recommendation_counts.get("positive_prior", 0),
        "recheck_prior_count": recommendation_counts.get("recheck_prior", 0),
        "quality_risk_count": recommendation_counts.get("quality_risk", 0),
        "loss_filter_count": recommendation_counts.get("loss_filter", 0),
        "hold_sample_count": recommendation_counts.get("hold_sample", 0),
        "source_quality_blocked_count": recommendation_counts.get("source_quality_blocked", 0),
        "window_priority": list(WINDOW_PRIORITY),
        "counterfactual_status": counterfactual_status,
        "lifecycle_source_count": sum(
            1 for label in paths if label.startswith("lifecycle_bucket_discovery") and paths[label].exists()
        ),
        "rising_missed_feedback_record_count": sum(
            _safe_int(row["rising_missed_metrics"].get("initial_quality_fail_count"))
            + _safe_int(row["rising_missed_metrics"].get("avg_down_ge2_count"))
            for row in prior_rows
        ),
        **counterfactual_metrics,
        "lineage_blocker_count": sum(_safe_int(value) for value in lineage.get("lineage_blockers", {}).values()),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    orders = _build_code_improvement_orders(summary)
    return {
        "schema_version": 1,
        "report_type": "rising_missed_classifier_prior",
        "target_date": target_date,
        "generated_at": generated_at or _now_kst_iso(),
        "clean_tuning_baseline": {
            "clean_tuning_baseline_date": "2026-06-04",
            "clean_tuning_baseline_ts_kst": CLEAN_BASELINE_TS_KST,
        },
        "metric_contracts": {
            "rising_missed_classifier_prior": {
                "metric_role": "source_only_classifier_prior",
                "decision_authority": "rising_missed_classifier_prior_source_only",
                "window_policy": "rolling10d_gt_rolling5d_gt_mtd_gt_daily",
                "sample_floor": "daily_positive_is_hold_sample_until_rolling_confirmation",
                "primary_decision_metric": "source_quality_adjusted_ev_pct",
                "source_quality_gate": "clean_baseline_after_2026_06_04_and_contract_quality",
                "forbidden_uses": list(FORBIDDEN_USES),
            }
        },
        "source_paths": {label: _source_ref(path) for label, path in sorted(paths.items())},
        "source_quality": source_quality,
        "summary": summary,
        "priors": prior_rows,
        "code_improvement_orders": orders,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "rising_missed_classifier_prior_source_only",
        "forbidden_uses": list(FORBIDDEN_USES),
    }


def write_outputs(report: dict[str, Any], *, output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# Rising Missed Classifier Prior - {report.get('target_date')}",
        "",
        f"- generated_at: {report.get('generated_at')}",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        f"- counterfactual_status: {report.get('summary', {}).get('counterfactual_status')}",
        f"- prior_count: {report.get('summary', {}).get('prior_count')}",
        f"- recommendation_counts: {json.dumps(report.get('summary', {}).get('recommendation_counts', {}), ensure_ascii=False, sort_keys=True)}",
        "",
        "## Top Priors",
        "",
    ]
    for row in _as_list(report.get("priors"))[:20]:
        lines.append(
            "- "
            + str(row.get("prior_key"))
            + f" | recommendation={row.get('recommendation')}"
            + f" | confidence={row.get('confidence')}"
            + f" | window={row.get('selected_window')}"
            + f" | reason={row.get('reason')}"
        )
    if not _as_list(report.get("priors")):
        lines.append("- no prior rows")
    lines.extend(["", "## Code Improvement Orders", ""])
    for order in _as_list(report.get("code_improvement_orders")):
        lines.append(f"- {order.get('order_id')} | runtime_effect: false | allowed_runtime_apply: false")
    if not _as_list(report.get("code_improvement_orders")):
        lines.append("- none")
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args(argv)
    output_json, output_md = _default_output_paths(args.target_date)
    if args.output_json:
        output_json = Path(args.output_json)
    if args.output_md:
        output_md = Path(args.output_md)
    report = build_report(args.target_date)
    write_outputs(report, output_json=output_json, output_md=output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
