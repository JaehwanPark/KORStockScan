"""Discover missing source-only producer candidates from sim/probe lifecycle results."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.automation.dual_candidate_review import (
    evidence_authority_contract,
    REQUIRED_METRIC_CONTRACT_FIELDS,
    default_comparative_review,
    has_evidence_authority_violation,
    has_forbidden_runtime_leak,
    missing_metric_contract_fields,
    proposal_counts,
    with_evidence_authority_forbidden_uses,
)
from src.engine.automation.producer_gap_source_bundle import report_paths as producer_gap_source_bundle_paths
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.constants import TRADING_RULES
from src.utils.jsonl_io import iter_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_TYPE = "producer_gap_discovery"
REPORT_SCHEMA_VERSION = 1
DISCOVERY_VERSION = "producer_gap_discovery_v1"
AI_REVIEW_SCHEMA_NAME = "producer_gap_discovery_ai_review_v1"
AI_REVIEWER_NAME = "producer_gap_discovery_ai_review"
AI_REVIEW_MODEL = str(getattr(TRADING_RULES, "GPT_DEEP_MODEL", "gpt-5.4") or "gpt-5.4")
AI_REVIEW_DEFAULT_PROVIDER = "openai"
AI_REVIEW_REASONING_EFFORT = os.getenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_REASONING_EFFORT", "low")
AI_REVIEW_TIMEOUT_SEC = int(os.getenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_TIMEOUT_SEC", "90") or "90")
POST_SELL_DIR = PROJECT_ROOT / "data" / "post_sell"

FORBIDDEN_USES = [
    "real order enablement",
    "threshold mutation",
    "provider change",
    "bot restart",
    "position cap release",
    "entry decision override",
    "exit decision override",
    "broker order submit",
]
FORBIDDEN_USES = with_evidence_authority_forbidden_uses(FORBIDDEN_USES)
PATTERN_TYPES = {
    "stop_recovery_counterfactual_missing",
    "missed_fill_recovery_counterfactual_missing",
    "swing_sim_probe_label_gap_missing",
    "scale_in_counterfactual_gap_missing",
    "time_window_policy_exception_missing",
    "volatile_runner_exit_counterfactual_missing",
    "limit_up_plateau_breakdown_exit_missing",
    "sim_entry_selection_gap_missing",
    "sim_submit_fill_quality_gap_missing",
    "sim_holding_runner_gap_missing",
    "sim_exit_plateau_breakdown_gap_missing",
    "sim_stop_recovery_gap_missing",
    "sim_scale_in_counterfactual_gap_missing",
    "sim_time_window_exception_gap_missing",
    "sim_source_quality_join_gap_missing",
    "sim_first_coverage_gap",
}
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
ROLLING_WINDOWS = ("daily", "3d", "5d", "10d", "all_available")
SIM_ROLLING_MAX_ROWS = int(os.getenv("KORSTOCKSCAN_PRODUCER_GAP_SIM_ROLLING_MAX_ROWS", "200000") or "200000")
SIM_ROLLING_MAX_SECONDS = int(os.getenv("KORSTOCKSCAN_PRODUCER_GAP_SIM_ROLLING_MAX_SECONDS", "240") or "240")
PRODUCER_DUAL_DECISIONS = {
    "new_producer",
    "extend_existing_producer",
    "absorb_as_metric_dimension",
    "source_quality_blocker",
    "reject",
}


@dataclass(frozen=True)
class DetectorContract:
    pattern_type: str
    source_scope: str
    domain: str
    lifecycle_stage: str
    required_sources: tuple[str, ...]
    sim_equivalent_required: bool
    coverage_family: str
    sim_equivalent_pattern: str | None = None
    explicit_exemption: str | None = None


DETECTOR_REGISTRY: tuple[DetectorContract, ...] = (
    DetectorContract("stop_recovery_counterfactual_missing", "counterfactual_only", "scalping", "exit", ("sim_post_sell_evaluations",), False, "stop_recovery", "sim_stop_recovery_gap_missing"),
    DetectorContract("missed_fill_recovery_counterfactual_missing", "mixed_source", "scalping", "submit", ("lifecycle_decision_matrix", "lifecycle_bucket_discovery"), False, "submit_fill", "sim_submit_fill_quality_gap_missing"),
    DetectorContract("swing_sim_probe_label_gap_missing", "swing_sim_first", "swing", "selection", ("swing_strategy_discovery_ev",), False, "swing_label", None, "swing source is already sim/probe first"),
    DetectorContract("scale_in_counterfactual_gap_missing", "mixed_source", "cross_domain", "scale_in", ("lifecycle_decision_matrix",), False, "scale_in", "sim_scale_in_counterfactual_gap_missing"),
    DetectorContract("time_window_policy_exception_missing", "counterfactual_only", "scalping", "entry", ("sim_post_sell_candidates", "wait6579_ev_cohort"), False, "time_window", "sim_time_window_exception_gap_missing"),
    DetectorContract("volatile_runner_exit_counterfactual_missing", "real_anchor", "scalping", "exit", ("post_sell_candidates", "sim_post_sell_candidates"), True, "runner_exit", "sim_holding_runner_gap_missing"),
    DetectorContract("limit_up_plateau_breakdown_exit_missing", "real_anchor", "scalping", "exit", ("post_sell_candidates", "sim_post_sell_candidates"), True, "plateau_exit", "sim_exit_plateau_breakdown_gap_missing"),
    DetectorContract("sim_entry_selection_gap_missing", "sim_first", "scalping", "entry", ("sim_post_sell_candidates",), False, "entry_selection"),
    DetectorContract("sim_submit_fill_quality_gap_missing", "sim_first", "scalping", "submit", ("sim_post_sell_candidates",), False, "submit_fill"),
    DetectorContract("sim_holding_runner_gap_missing", "sim_first", "scalping", "holding", ("sim_post_sell_candidates",), False, "runner_exit"),
    DetectorContract("sim_exit_plateau_breakdown_gap_missing", "sim_first", "scalping", "exit", ("sim_post_sell_candidates",), False, "plateau_exit"),
    DetectorContract("sim_stop_recovery_gap_missing", "sim_first", "scalping", "exit", ("sim_post_sell_candidates", "sim_post_sell_evaluations"), False, "stop_recovery"),
    DetectorContract("sim_scale_in_counterfactual_gap_missing", "sim_first", "cross_domain", "scale_in", ("sim_post_sell_candidates", "lifecycle_decision_matrix"), False, "scale_in"),
    DetectorContract("sim_time_window_exception_gap_missing", "sim_first", "scalping", "entry", ("sim_post_sell_candidates", "wait6579_ev_cohort"), False, "time_window"),
    DetectorContract("sim_source_quality_join_gap_missing", "source_quality", "cross_domain", "source_quality", ("sim_post_sell_candidates", "sim_post_sell_evaluations"), False, "source_quality"),
    DetectorContract("sim_first_coverage_gap", "source_quality", "cross_domain", "source_quality", ("sim_post_sell_candidates",), False, "coverage_audit"),
)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_TYPE / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, *, limit: int = 20000) -> list[dict[str, Any]]:
    return list(deque(iter_jsonl(path), maxlen=max(0, int(limit))))


def _iter_jsonl(path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in iter_jsonl(path):
        if limit is not None and len(rows) >= limit:
            break
        rows.append(payload)
    return rows


def _available_sim_dates(target_date: str) -> list[str]:
    dates = set()
    for pattern in (
        "sim_post_sell_candidates_*.jsonl",
        "sim_post_sell_candidates_*.jsonl.gz",
        "sim_post_sell_evaluations_*.jsonl",
        "sim_post_sell_evaluations_*.jsonl.gz",
    ):
        for path in POST_SELL_DIR.glob(pattern):
            match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
            if match and match.group(1) <= target_date:
                dates.add(match.group(1))
    dates.add(target_date)
    return sorted(dates)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _slug(value: Any, *, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:max_len] or "unknown"


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "sim_post_sell_evaluations": POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl",
        "post_sell_candidates": POST_SELL_DIR / f"post_sell_candidates_{target_date}.jsonl",
        "sim_post_sell_candidates": POST_SELL_DIR / f"sim_post_sell_candidates_{target_date}.jsonl",
        "wait6579_ev_cohort": REPORT_DIR / "monitor_snapshots" / f"wait6579_ev_cohort_{target_date}.json",
        "performance_tuning": REPORT_DIR / "monitor_snapshots" / f"performance_tuning_{target_date}.json",
        "time_window_regime_counterfactual": REPORT_DIR
        / "time_window_regime_counterfactual"
        / f"time_window_regime_counterfactual_{target_date}.json",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "swing_strategy_discovery_ev": REPORT_DIR
        / "swing_strategy_discovery_ev"
        / f"swing_strategy_discovery_ev_{target_date}.json",
        "swing_lifecycle_decision_matrix": REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_bucket_discovery": REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_audit": REPORT_DIR / "swing_lifecycle_audit" / f"swing_lifecycle_audit_{target_date}.json",
        "producer_gap_source_bundle": producer_gap_source_bundle_paths(target_date)[0],
    }


def _iter_nested(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_iter_nested(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_iter_nested(child))
    return found


def _candidate(
    *,
    candidate_id: str,
    domain: str,
    pattern_type: str,
    lifecycle_stage: str,
    priority: str,
    evidence: list[str],
    source_paths: list[str],
    sample_count: int,
    source_scope: str | None = None,
) -> dict[str, Any]:
    contract = next((item for item in DETECTOR_REGISTRY if item.pattern_type == pattern_type), None)
    return {
        "candidate_id": candidate_id,
        "domain": domain,
        "pattern_type": pattern_type,
        "lifecycle_stage": lifecycle_stage,
        "priority": priority,
        "producer_gap_state": "missing_producer_candidate",
        "metric_role": "source_quality_gate",
        "decision_authority": "producer_gap_discovery_source_only",
        "window_policy": "same_day_postclose_sim_probe_real_flow_review",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "source artifact exists and contains pattern evidence",
        "forbidden_uses": FORBIDDEN_USES,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "sample_count": sample_count,
        "source_scope": source_scope or (contract.source_scope if contract else "mixed_source"),
        "coverage_family": contract.coverage_family if contract else pattern_type,
        "real_case_anchor": bool(contract and contract.source_scope == "real_anchor"),
        "evidence": evidence[:20],
        "source_paths": source_paths[:12],
        "recommended_producer_contract": {
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "source_only_producer_gap_observation",
            "required_metric_contract_fields": [
                "metric_role",
                "decision_authority",
                "window_policy",
                "sample_floor",
                "primary_decision_metric",
                "source_quality_gate",
                "forbidden_uses",
            ],
        },
    }


def _detect_stop_recovery(rows: list[dict[str, Any]], source_path: Path) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for row in rows:
        text = json.dumps(row, ensure_ascii=False, default=str).lower()
        exit_reason = str(row.get("exit_reason") or row.get("sell_reason") or row.get("reason") or "").lower()
        profit = _safe_float(row.get("profit_rate") or row.get("profit_pct") or row.get("realized_profit_pct"), 0.0)
        mfe = _safe_float(row.get("mfe_pct") or row.get("max_favorable_excursion_pct") or row.get("post_exit_mfe_pct"), 0.0)
        recovery = _safe_float(row.get("recovery_profit_pct") or row.get("post_stop_recovery_pct"), 0.0)
        if ("hard" in exit_reason and "stop" in exit_reason) or "hard_stop" in text or "soft_stop" in text:
            if profit < 0 or mfe > 0 or recovery > 0:
                matches.append(row)
    if not matches:
        return []
    symbols = sorted({str(row.get("code") or row.get("symbol") or row.get("stock_code") or "unknown") for row in matches})[:8]
    return [
        _candidate(
            candidate_id="producer_gap_stop_recovery_counterfactual_missing",
            domain="scalping",
            pattern_type="stop_recovery_counterfactual_missing",
            lifecycle_stage="exit",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(source_path)],
            evidence=[
                f"matched_stop_exit_rows={len(matches)}",
                f"symbols={','.join(symbols)}",
                "gap=post-stop recovery is not isolated as a dedicated producer input",
            ],
        )
    ]


def _detect_missed_fill(payloads: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for label in ("lifecycle_decision_matrix", "lifecycle_bucket_discovery"):
        for item in _iter_nested(payloads.get(label)):
            text = json.dumps(item, ensure_ascii=False, default=str).lower()
            if any(token in text for token in ("missed_fill", "unfilled", "not_filled", "cancel", "defensive_price", "below_window", "fill_quality")):
                matches.append({"label": label, "item": item})
    if not matches:
        return []
    labels = sorted({row["label"] for row in matches})
    return [
        _candidate(
            candidate_id="producer_gap_missed_fill_recovery_counterfactual_missing",
            domain="scalping",
            pattern_type="missed_fill_recovery_counterfactual_missing",
            lifecycle_stage="submit",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(paths[label]) for label in labels if paths[label].exists()],
            evidence=[
                f"matched_submit_fill_gap_rows={len(matches)}",
                f"source_labels={','.join(labels)}",
                "gap=post-submit missed fill and re-entry/recovery quality lacks a dedicated producer",
            ],
        )
    ]


def _detect_swing_label_gap(payloads: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for label in ("swing_strategy_discovery_ev", "swing_lifecycle_decision_matrix", "swing_lifecycle_bucket_discovery", "swing_lifecycle_audit"):
        for item in _iter_nested(payloads.get(label)):
            text = json.dumps(item, ensure_ascii=False, default=str).lower()
            if any(token in text for token in ("label_missing", "missing_label", "pending_label", "insufficient_label", "source_quality", "handoff_missing")):
                matches.append({"label": label, "item": item})
    if not matches:
        return []
    labels = sorted({row["label"] for row in matches})
    return [
        _candidate(
            candidate_id="producer_gap_swing_sim_probe_label_gap_missing",
            domain="swing",
            pattern_type="swing_sim_probe_label_gap_missing",
            lifecycle_stage="selection",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(paths[label]) for label in labels if paths[label].exists()],
            evidence=[
                f"matched_swing_label_or_source_gap_rows={len(matches)}",
                f"source_labels={','.join(labels)}",
                "gap=swing sim/probe label and EV handoff defects need a dedicated source producer",
            ],
        )
    ]


def _detect_scale_in_gap(payloads: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for label in ("lifecycle_decision_matrix", "swing_lifecycle_decision_matrix", "swing_lifecycle_bucket_discovery"):
        for item in _iter_nested(payloads.get(label)):
            text = json.dumps(item, ensure_ascii=False, default=str).lower()
            if "scale_in" in text or "avg_down" in text or "pyramid" in text:
                if any(token in text for token in ("blocked", "missing", "would", "counterfactual", "mfe", "mae", "price_guard", "qty_reason")):
                    matches.append({"label": label, "item": item})
    if not matches:
        return []
    labels = sorted({row["label"] for row in matches})
    return [
        _candidate(
            candidate_id="producer_gap_scale_in_counterfactual_gap_missing",
            domain="cross_domain",
            pattern_type="scale_in_counterfactual_gap_missing",
            lifecycle_stage="scale_in",
            priority="high",
            sample_count=len(matches),
            source_paths=[str(paths[label]) for label in labels if paths[label].exists()],
            evidence=[
                f"matched_scale_in_gap_rows={len(matches)}",
                f"source_labels={','.join(labels)}",
                "gap=scale-in blocked/fill/unfill outcome comparison lacks a dedicated source producer",
            ],
        )
    ]


def _extract_minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"(\d{1,2}):(\d{2})", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def _row_event_time(row: dict[str, Any]) -> tuple[int, str] | None:
    for key in (
        "entry_time",
        "buy_time",
        "submitted_at",
        "order_submitted_at",
        "filled_at",
        "event_time",
        "sell_time",
        "exit_time",
        "timestamp",
        "created_at",
    ):
        minutes = _extract_minutes(row.get(key))
        if minutes is not None:
            return minutes, key
    return None


def _row_completed_profit_pct(row: dict[str, Any]) -> float | None:
    for key in (
        "profit_rate",
        "profit_pct",
        "realized_profit_pct",
        "sim_profit_pct",
        "pnl_pct",
        "return_pct",
    ):
        if row.get(key) not in (None, ""):
            return _safe_float(row.get(key))
    return None


def _row_symbol(row: dict[str, Any]) -> str:
    return str(row.get("stock_code") or row.get("code") or row.get("symbol") or "").strip()


def _row_name(row: dict[str, Any]) -> str:
    return str(row.get("stock_name") or row.get("name") or "").strip()


def _row_group_key(row: dict[str, Any], date: str) -> str:
    for key in ("sim_parent_record_id", "recommendation_id", "record_id", "candidate_id", "entry_adm_candidate_id"):
        value = row.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    symbol = _row_symbol(row) or "unknown"
    return f"symbol_date:{symbol}:{date}"


def _time_sort_key(row: dict[str, Any]) -> tuple[int, str] | None:
    event_time = _row_event_time(row)
    if event_time is None:
        return None
    return event_time


def _exit_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in ("exit_reason", "sell_reason", "reason", "exit_rule", "sell_reason_type", "outcome")
    ).lower()


def _is_stop_row(row: dict[str, Any]) -> bool:
    text = _exit_text(row)
    return "hard_stop" in text or "soft_stop" in text or "hard stop" in text or "soft stop" in text or "stop" in text


def _rolling_sim_sources(target_date: str, *, rolling_sim_scan: bool, max_rows: int = SIM_ROLLING_MAX_ROWS) -> dict[str, Any]:
    dates = _available_sim_dates(target_date) if rolling_sim_scan else [target_date]
    scanned_dates: list[str] = []
    rows: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    rows_by_date: dict[str, int] = {}
    eval_rows_by_date: dict[str, int] = {}
    guard_hit = False
    paused_reason: str | None = None
    started = datetime.now().astimezone()
    for date in dates:
        if len(rows) + len(evaluations) >= max_rows:
            guard_hit = True
            paused_reason = "max_rows"
            break
        candidate_path = POST_SELL_DIR / f"sim_post_sell_candidates_{date}.jsonl"
        remaining = max(0, max_rows - len(rows) - len(evaluations))
        date_rows = _iter_jsonl(candidate_path, limit=remaining)
        for row in date_rows:
            row.setdefault("_source_date", date)
            row.setdefault("_source_file", str(candidate_path))
        rows.extend(date_rows)
        rows_by_date[date] = len(date_rows)
        if len(rows) + len(evaluations) >= max_rows:
            guard_hit = True
            paused_reason = "max_rows"
            scanned_dates.append(date)
            break
        eval_path = POST_SELL_DIR / f"sim_post_sell_evaluations_{date}.jsonl"
        remaining = max(0, max_rows - len(rows) - len(evaluations))
        eval_rows = _iter_jsonl(eval_path, limit=remaining)
        for row in eval_rows:
            row.setdefault("_source_date", date)
            row.setdefault("_source_file", str(eval_path))
        evaluations.extend(eval_rows)
        eval_rows_by_date[date] = len(eval_rows)
        scanned_dates.append(date)
        elapsed = (datetime.now().astimezone() - started).total_seconds()
        if elapsed > SIM_ROLLING_MAX_SECONDS:
            guard_hit = True
            paused_reason = "max_seconds"
            break
    return {
        "dates": scanned_dates,
        "available_dates": dates,
        "rows": rows,
        "evaluations": evaluations,
        "rows_by_date": rows_by_date,
        "evaluation_rows_by_date": eval_rows_by_date,
        "guard_hit": guard_hit,
        "paused_reason": paused_reason,
        "max_rows": max_rows,
    }


def _group_sim_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        date = str(row.get("_source_date") or "")
        key = _row_group_key(row, date)
        symbol = _row_symbol(row)
        grouped.setdefault(f"{key}:{symbol}", []).append(row)
    return grouped


def _nested_first_float(payload: Any, keys: tuple[str, ...]) -> float | None:
    for item in _iter_nested(payload):
        for key in keys:
            if key in item and item.get(key) not in (None, ""):
                return _safe_float(item.get(key))
    return None


def _detect_time_window_policy_exception_gap(
    sim_candidate_rows: list[dict[str, Any]],
    payloads: dict[str, Any],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    existing_artifact = payloads.get("time_window_regime_counterfactual") or {}
    if existing_artifact.get("report_type") == "time_window_regime_counterfactual":
        artifact_status = str(existing_artifact.get("status") or "")
        if artifact_status in {"pass", "warning", "partial"}:
            return []
    cutoff_text = "09:30"
    cutoff_minutes = 9 * 60 + 30
    timed_rows: list[tuple[dict[str, Any], int, str, float | None]] = []
    for row in sim_candidate_rows:
        event_time = _row_event_time(row)
        if event_time is None:
            continue
        minutes, time_key = event_time
        timed_rows.append((row, minutes, time_key, _row_completed_profit_pct(row)))
    pre_rows = [
        (row, minutes, time_key, profit)
        for row, minutes, time_key, profit in timed_rows
        if minutes < cutoff_minutes
    ]
    post_rows = [
        (row, minutes, time_key, profit)
        for row, minutes, time_key, profit in timed_rows
        if minutes >= cutoff_minutes
    ]
    pre_profit_rows = [profit for _, _, _, profit in pre_rows if profit is not None]
    post_profit_rows = [profit for _, _, _, profit in post_rows if profit is not None]
    pre_avg = sum(pre_profit_rows) / len(pre_profit_rows) if pre_profit_rows else None
    post_avg = sum(post_profit_rows) / len(post_profit_rows) if post_profit_rows else None

    pre_window_worse = bool(
        len(pre_profit_rows) >= 2
        and pre_avg is not None
        and pre_avg < 0
        and (post_avg is None or pre_avg < post_avg)
    )
    stop_rows = [
        row
        for row, _, _, _ in pre_rows
        if any(
            token in json.dumps(row, ensure_ascii=False, default=str).lower()
            for token in ("hard_stop", "soft_stop", "hard stop", "soft stop")
        )
    ]
    early_stop_rate = (len(stop_rows) / len(pre_rows)) if pre_rows else 0.0
    early_stop_high = bool(pre_profit_rows) and len(stop_rows) >= 1 and early_stop_rate >= 0.34

    wait6579_payload = payloads.get("wait6579_ev_cohort") or {}
    performance_payload = payloads.get("performance_tuning") or {}
    wait6579_avg_ev = _nested_first_float(
        wait6579_payload,
        (
            "avg_expected_ev_pct",
            "equal_weight_avg_profit_pct",
            "notional_weighted_ev_pct",
            "source_quality_adjusted_ev_pct",
        ),
    )
    wait6579_ev_krw_sum = _nested_first_float(
        wait6579_payload,
        ("expected_ev_krw_sum", "ev_krw_sum", "expected_profit_krw_sum", "profit_krw_sum"),
    )
    performance_recovery_ev = _nested_first_float(
        performance_payload,
        ("recovery_avg_expected_ev_pct", "recovery_equal_weight_avg_profit_pct", "wait6579_avg_expected_ev_pct"),
    )
    exception_ev_positive = any(
        value is not None and value > 0
        for value in (wait6579_avg_ev, wait6579_ev_krw_sum, performance_recovery_ev)
    )
    early_general_loss = any((profit is not None and profit < 0) for _, _, _, profit in pre_rows)
    early_loss_and_recovery_coexist = early_general_loss and exception_ev_positive

    conditions = []
    if pre_window_worse:
        conditions.append("pre_window_sim_pnl_worse")
    if early_stop_high:
        conditions.append("early_window_stop_share_high")
    if exception_ev_positive:
        conditions.append("wait6579_or_recovery_ev_positive")
    if early_loss_and_recovery_coexist:
        conditions.append("completed_loss_and_counterfactual_exception_positive_same_day")
    if len(conditions) < 2:
        return []

    source_paths = [
        str(paths[label])
        for label in ("sim_post_sell_candidates", "wait6579_ev_cohort", "performance_tuning")
        if paths[label].exists()
    ]
    evidence = [
        "gap=early time-window block would also suppress positive recovery exceptions without a dedicated producer",
        f"operator_seed_cutoff={cutoff_text}",
        "operator_seed_cutoff_authority=source_only_hypothesis_not_runtime_hard_gate",
        "metric_scope=completed_sim_exit_pnl_vs_missed_entry_counterfactual_ev_not_directly_nettable",
        f"time_window_measurement_keys={','.join(sorted({time_key for _, _, time_key, _ in pre_rows + post_rows}))}",
        "required_policy_comparison=allow_all_vs_block_all_vs_block_general_allow_recovery",
        "required_exception_buckets=wait6579,recovery,high_score_buy,latency_caution,defensive_price",
        f"conditions={','.join(conditions)}",
        f"pre_window_sample={len(pre_rows)}",
        f"post_window_sample={len(post_rows)}",
        f"pre_window_stop_rate={early_stop_rate:.4f}",
    ]
    if pre_avg is not None:
        evidence.append(f"pre_window_avg_profit_pct={pre_avg:.4f}")
    if post_avg is not None:
        evidence.append(f"post_window_avg_profit_pct={post_avg:.4f}")
    if wait6579_avg_ev is not None:
        evidence.append(f"wait6579_avg_expected_ev_pct={wait6579_avg_ev:.4f}")
    if wait6579_ev_krw_sum is not None:
        evidence.append(f"wait6579_expected_ev_krw_sum={wait6579_ev_krw_sum:.0f}")
    if performance_recovery_ev is not None:
        evidence.append(f"performance_recovery_avg_expected_ev_pct={performance_recovery_ev:.4f}")

    candidate = _candidate(
        candidate_id="producer_gap_time_window_policy_exception_missing",
        domain="scalping",
        pattern_type="time_window_policy_exception_missing",
        lifecycle_stage="entry",
        priority="high",
        sample_count=len(pre_rows),
        source_paths=source_paths,
        evidence=evidence,
    )
    candidate["recommended_producer_contract"].update(
        {
            "candidate_producer_name": "time_window_regime_counterfactual",
            "preferred_producer_name": "time_window_regime_counterfactual",
            "operator_seed_cutoff": cutoff_text,
            "cutoff_authority": "source_only_hypothesis_not_runtime_hard_gate",
            "compare_policies": [
                "allow_all_in_window",
                "block_all_in_window",
                "block_general_allow_exception_in_window",
            ],
            "required_exception_buckets": [
                "wait6579",
                "recovery",
                "high_score_buy",
                "latency_caution",
                "defensive_price",
            ],
        }
    )
    return [candidate]


def _real_sim_join_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for key in (
        "recommendation_id",
        "sim_parent_record_id",
        "record_id",
        "candidate_id",
        "entry_adm_candidate_id",
    ):
        value = row.get(key)
        if value not in (None, ""):
            keys.add(str(value))
    return keys


def _detect_volatile_runner_exit_gap(
    real_post_sell_rows: list[dict[str, Any]],
    sim_candidate_rows: list[dict[str, Any]],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    sim_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in sim_candidate_rows:
        for key in _real_sim_join_keys(row):
            sim_by_key.setdefault(key, []).append(row)

    matches: list[tuple[dict[str, Any], dict[str, Any], float, float]] = []
    for real_row in real_post_sell_rows:
        real_profit = _safe_float(real_row.get("profit_rate"), 0.0)
        real_peak = _safe_float(real_row.get("peak_profit"), 0.0)
        if real_profit > 1.0 or real_peak < 2.0:
            continue
        real_symbol = str(real_row.get("stock_code") or real_row.get("code") or "")
        for key in _real_sim_join_keys(real_row):
            for sim_row in sim_by_key.get(key, []):
                sim_symbol = str(sim_row.get("stock_code") or sim_row.get("code") or "")
                if real_symbol and sim_symbol and real_symbol != sim_symbol:
                    continue
                sim_profit = _safe_float(sim_row.get("profit_rate"), 0.0)
                uplift = sim_profit - real_profit
                if sim_profit >= 3.0 and uplift >= 2.0:
                    matches.append((real_row, sim_row, sim_profit, uplift))
    if not matches:
        return []

    examples = []
    for real_row, sim_row, sim_profit, uplift in matches[:5]:
        symbol = real_row.get("stock_code") or real_row.get("code") or "unknown"
        name = real_row.get("stock_name") or sim_row.get("stock_name") or ""
        examples.append(
            f"{symbol}:{name}:real_profit={_safe_float(real_row.get('profit_rate')):.2f}:"
            f"real_peak={_safe_float(real_row.get('peak_profit')):.2f}:"
            f"sim_profit={sim_profit:.2f}:uplift={uplift:.2f}"
        )
    return [
        _candidate(
            candidate_id="producer_gap_volatile_runner_exit_counterfactual_missing",
            domain="scalping",
            pattern_type="volatile_runner_exit_counterfactual_missing",
            lifecycle_stage="exit",
            priority="high",
            sample_count=len(matches),
            source_paths=[
                str(paths[label])
                for label in ("post_sell_candidates", "sim_post_sell_candidates")
                if paths[label].exists()
            ],
            evidence=[
                f"matched_real_small_take_profit_vs_sim_runner_rows={len(matches)}",
                "gap=volatile bullish continuation after trailing exit lacks a dedicated source-only producer",
                "required_comparison=real_exit_profit_vs_same_parent_sim_runner_profit",
                "required_features=peak_drawdown,holding_flow_override_state,ofi_qi_smoothing,large_sell_print,top_depth_ratio,post_exit_mfe",
                "forbidden_runtime_action=do_not_override_exit_or_trailing_without_separate_approval",
                *examples,
            ],
        )
    ]


def _detect_limit_up_plateau_breakdown_exit_gap(
    real_post_sell_rows: list[dict[str, Any]],
    sim_candidate_rows: list[dict[str, Any]],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    sim_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in sim_candidate_rows:
        for key in _real_sim_join_keys(row):
            sim_by_key.setdefault(key, []).append(row)

    matches: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = []
    for real_row in real_post_sell_rows:
        real_profit = _safe_float(real_row.get("profit_rate"), 0.0)
        real_peak = _safe_float(real_row.get("peak_profit"), 0.0)
        held_sec = _safe_int(real_row.get("held_sec"), 0)
        exit_text = " ".join(
            str(real_row.get(key) or "")
            for key in ("exit_rule", "sell_reason_type", "reason", "exit_reason")
        ).lower()
        if real_profit > -2.0 or real_peak < 0.5 or held_sec < 1800:
            continue
        if "hard_stop" not in exit_text and "soft_stop" not in exit_text and "stop" not in exit_text:
            continue
        real_symbol = str(real_row.get("stock_code") or real_row.get("code") or "")
        real_time = _row_event_time(real_row)
        same_parent_rows: list[dict[str, Any]] = []
        for key in _real_sim_join_keys(real_row):
            for sim_row in sim_by_key.get(key, []):
                sim_symbol = str(sim_row.get("stock_code") or sim_row.get("code") or "")
                if real_symbol and sim_symbol and real_symbol != sim_symbol:
                    continue
                same_parent_rows.append(sim_row)
        if not same_parent_rows:
            continue
        positive_reentry_rows = []
        stop_loss_rows = []
        for sim_row in same_parent_rows:
            sim_profit = _safe_float(sim_row.get("profit_rate"), 0.0)
            sim_time = _row_event_time(sim_row)
            is_before_real = bool(
                real_time is None
                or sim_time is None
                or sim_time[0] <= real_time[0]
            )
            if is_before_real and sim_profit >= 0.5:
                positive_reentry_rows.append(sim_row)
            if sim_profit <= -2.0:
                stop_loss_rows.append(sim_row)
        if positive_reentry_rows or stop_loss_rows:
            matches.append((real_row, positive_reentry_rows, stop_loss_rows))

    if not matches:
        return []

    examples = []
    for real_row, positive_rows, stop_rows in matches[:5]:
        symbol = real_row.get("stock_code") or real_row.get("code") or "unknown"
        name = real_row.get("stock_name") or ""
        best_positive = max((_safe_float(row.get("profit_rate"), 0.0) for row in positive_rows), default=0.0)
        worst_stop = min((_safe_float(row.get("profit_rate"), 0.0) for row in stop_rows), default=0.0)
        examples.append(
            f"{symbol}:{name}:real_profit={_safe_float(real_row.get('profit_rate')):.2f}:"
            f"real_peak={_safe_float(real_row.get('peak_profit')):.2f}:held_sec={_safe_int(real_row.get('held_sec'))}:"
            f"best_same_parent_reentry_profit={best_positive:.2f}:worst_same_parent_stop={worst_stop:.2f}"
        )
    return [
        _candidate(
            candidate_id="producer_gap_limit_up_plateau_breakdown_exit_missing",
            domain="scalping",
            pattern_type="limit_up_plateau_breakdown_exit_missing",
            lifecycle_stage="exit",
            priority="high",
            sample_count=len(matches),
            source_paths=[
                str(paths[label])
                for label in ("post_sell_candidates", "sim_post_sell_candidates")
                if paths[label].exists()
            ],
            evidence=[
                f"matched_long_hold_plateau_to_stop_loss_rows={len(matches)}",
                "gap=limit-up or fixed-price plateau breakdown lacks a dedicated source-only exit regime producer",
                "required_comparison=current_stop_exit_vs_plateau_take_profit_vs_breakdown_exit",
                "required_features=plateau_duration,near_upper_limit_price_stickiness,top_depth_ratio,buy_pressure_decay,holding_flow_recovery_defer,hard_stop_after_plateau",
                "forbidden_runtime_action=do_not_override_hard_stop_or_create_exit_rule_without_separate_approval",
                *examples,
            ],
        )
    ]


def _sim_source_paths(rows: list[dict[str, Any]], evaluations: list[dict[str, Any]], target_date: str) -> list[str]:
    paths = sorted(
        {
            str(row.get("_source_file") or "")
            for row in [*rows, *evaluations]
            if row.get("_source_file")
        }
    )
    if paths:
        return paths[:12]
    return [str(POST_SELL_DIR / f"sim_post_sell_candidates_{target_date}.jsonl")]


def _detect_sim_first_stage_gaps(
    sim_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    payloads: dict[str, Any],
    target_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped = _group_sim_rows(sim_rows)
    source_paths = _sim_source_paths(sim_rows, eval_rows, target_date)
    candidates: list[dict[str, Any]] = []
    strict_runner: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    ambiguous_runner: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    strict_plateau: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    ambiguous_plateau: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    stop_rows = [row for row in [*sim_rows, *eval_rows] if _is_stop_row(row) or (_row_completed_profit_pct(row) or 0.0) <= -2.0]
    detectable_families: set[str] = set()

    entry_rows = [
        row for row in sim_rows
        if any(row.get(key) not in (None, "") for key in ("entry_time", "buy_time", "submitted_at", "filled_at"))
    ]
    if len(sim_rows) >= 10 and len(entry_rows) / max(1, len(sim_rows)) < 0.5:
        detectable_families.add("entry_selection")
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_entry_selection_gap_missing",
                domain="scalping",
                pattern_type="sim_entry_selection_gap_missing",
                lifecycle_stage="entry",
                priority="high",
                sample_count=len(sim_rows),
                source_paths=source_paths,
                evidence=[
                    f"sim_rows={len(sim_rows)}",
                    f"entry_time_field_rate={len(entry_rows) / max(1, len(sim_rows)):.4f}",
                    "gap=sim entry/selection rows are present but entry provenance is insufficient for bucket producer coverage",
                    "required_producer=sim_entry_selection_bucket_producer",
                ],
            )
        )

    def _has_submit_quality_signal(row: dict[str, Any]) -> bool:
        text = json.dumps(row, ensure_ascii=False, default=str).lower()
        explicit_tokens = (
            "unfilled",
            "not_filled",
            "missed_fill",
            "partial_fill",
            "full_fill",
            "cancel",
            "defensive_price",
            "below_window",
            "fill_quality",
            "fill_status",
        )
        explicit_fields = (
            "submitted_at",
            "order_submitted_at",
            "filled_at",
            "fill_status",
            "fill_quality",
            "order_status",
            "broker_order_id",
            "receipt_no",
        )
        if any(row.get(key) not in (None, "") for key in explicit_fields):
            return True
        if str(row.get("actual_order_submitted", "")).lower() == "true":
            return True
        return any(token in text for token in explicit_tokens)

    submit_rows = [row for row in sim_rows if _has_submit_quality_signal(row)]
    if len(submit_rows) >= 2:
        detectable_families.add("submit_fill")
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_submit_fill_quality_gap_missing",
                domain="scalping",
                pattern_type="sim_submit_fill_quality_gap_missing",
                lifecycle_stage="submit",
                priority="high",
                sample_count=len(submit_rows),
                source_paths=source_paths,
                evidence=[
                    f"sim_submit_quality_rows={len(submit_rows)}",
                    "gap=sim submit/fill/defensive-price rows need a source-only quality producer before policy interpretation",
                    "required_producer=sim_submit_fill_quality_counterfactual_producer",
                ],
            )
        )

    for rows in grouped.values():
        if len(rows) < 2:
            continue
        row_times = {id(row): _time_sort_key(row) for row in rows}
        for loss_row in rows:
            loss_profit = _row_completed_profit_pct(loss_row)
            if loss_profit is None or loss_profit > -2.0:
                continue
            loss_time = row_times[id(loss_row)]
            for win_row in rows:
                if win_row is loss_row:
                    continue
                win_profit = _row_completed_profit_pct(win_row)
                if win_profit is None:
                    continue
                uplift = win_profit - loss_profit
                win_time = row_times[id(win_row)]
                if win_profit >= 2.0 or uplift >= 3.0:
                    if loss_time is not None and win_time is not None and loss_time[0] < win_time[0]:
                        strict_runner.append((loss_row, win_row, uplift))
                    elif loss_time is None or win_time is None:
                        ambiguous_runner.append((loss_row, win_row, uplift))
        for win_row in rows:
            win_profit = _row_completed_profit_pct(win_row)
            if win_profit is None or win_profit < 0.5:
                continue
            win_time = row_times[id(win_row)]
            for stop_row in rows:
                if stop_row is win_row:
                    continue
                stop_profit = _row_completed_profit_pct(stop_row)
                if stop_profit is None or stop_profit > -2.0:
                    continue
                stop_time = row_times[id(stop_row)]
                giveback = win_profit - stop_profit
                if win_time is not None and stop_time is not None and win_time[0] < stop_time[0]:
                    strict_plateau.append((win_row, stop_row, giveback))
                elif win_time is None or stop_time is None:
                    ambiguous_plateau.append((win_row, stop_row, giveback))

    if strict_runner or ambiguous_runner:
        detectable_families.add("runner_exit")
        top_symbols = sorted({(_row_symbol(row[0]) or "unknown") for row in [*strict_runner, *ambiguous_runner]})[:8]
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_holding_runner_gap_missing",
                domain="scalping",
                pattern_type="sim_holding_runner_gap_missing",
                lifecycle_stage="holding",
                priority="high",
                sample_count=len(strict_runner) + len(ambiguous_runner),
                source_paths=source_paths,
                evidence=[
                    f"strict_match_count={len(strict_runner)}",
                    f"ambiguous_match_count={len(ambiguous_runner)}",
                    f"top_symbols={','.join(top_symbols)}",
                    f"estimated_uplift_pct_sum={sum(item[2] for item in strict_runner):.4f}",
                    "gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer",
                    "required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness",
                    "required_producer=runner_regime_counterfactual_producer",
                ],
            )
        )
    if strict_plateau or ambiguous_plateau:
        detectable_families.add("plateau_exit")
        top_symbols = sorted({(_row_symbol(row[0]) or "unknown") for row in [*strict_plateau, *ambiguous_plateau]})[:8]
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_exit_plateau_breakdown_gap_missing",
                domain="scalping",
                pattern_type="sim_exit_plateau_breakdown_gap_missing",
                lifecycle_stage="exit",
                priority="high",
                sample_count=len(strict_plateau) + len(ambiguous_plateau),
                source_paths=source_paths,
                evidence=[
                    f"strict_match_count={len(strict_plateau)}",
                    f"ambiguous_match_count={len(ambiguous_plateau)}",
                    f"top_symbols={','.join(top_symbols)}",
                    f"estimated_giveback_pct_sum={sum(item[2] for item in strict_plateau):.4f}",
                    "gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer",
                    "required_producer=plateau_breakdown_exit_counterfactual_producer",
                ],
            )
        )

    if len(stop_rows) >= 2:
        detectable_families.add("stop_recovery")
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_stop_recovery_gap_missing",
                domain="scalping",
                pattern_type="sim_stop_recovery_gap_missing",
                lifecycle_stage="exit",
                priority="high",
                sample_count=len(stop_rows),
                source_paths=source_paths,
                evidence=[
                    f"sim_stop_or_loss_rows={len(stop_rows)}",
                    "gap=sim stop/recovery variants need a sim-first source producer independent of real exits",
                    "required_producer=sim_stop_recovery_counterfactual_producer",
                ],
            )
        )

    text_payload = json.dumps({"rows": sim_rows[:200], "payloads": payloads}, ensure_ascii=False, default=str).lower()
    if any(token in text_payload for token in ("scale_in", "avg_down", "pyramid", "would_add")):
        detectable_families.add("scale_in")
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_scale_in_counterfactual_gap_missing",
                domain="cross_domain",
                pattern_type="sim_scale_in_counterfactual_gap_missing",
                lifecycle_stage="scale_in",
                priority="high",
                sample_count=max(1, text_payload.count("scale_in") + text_payload.count("avg_down") + text_payload.count("pyramid")),
                source_paths=source_paths,
                evidence=[
                    "gap=sim scale-in blocked/fill/unfill would-add comparison needs a dedicated producer",
                    "required_producer=sim_scale_in_would_add_counterfactual_producer",
                ],
            )
        )

    early_rows = []
    later_rows = []
    cutoff = 9 * 60 + 30
    for row in sim_rows:
        event_time = _row_event_time(row)
        if event_time is None:
            continue
        if event_time[0] < cutoff:
            early_rows.append(row)
        else:
            later_rows.append(row)
    time_window_artifact = payloads.get("time_window_regime_counterfactual") or {}
    time_window_existing_ok = (
        isinstance(time_window_artifact, dict)
        and time_window_artifact.get("report_type") == "time_window_regime_counterfactual"
        and str(time_window_artifact.get("status") or "") in {"pass", "warning", "partial"}
    )
    if len(early_rows) >= 2 and len(stop_rows) >= 1 and not time_window_existing_ok:
        detectable_families.add("time_window")
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_time_window_exception_gap_missing",
                domain="scalping",
                pattern_type="sim_time_window_exception_gap_missing",
                lifecycle_stage="entry",
                priority="high",
                sample_count=len(early_rows),
                source_paths=source_paths,
                evidence=[
                    f"operator_seed_cutoff=09:30",
                    f"early_timed_sim_rows={len(early_rows)}",
                    f"post_cutoff_timed_sim_rows={len(later_rows)}",
                    "gap=sim time-window exceptions need rolling policy comparison rather than a hard gate",
                    "required_producer=time_window_regime_counterfactual",
                ],
            )
        )

    timed_count = sum(1 for row in sim_rows if _row_event_time(row) is not None)
    grouped_count = sum(1 for row in sim_rows if _row_group_key(row, str(row.get("_source_date") or target_date)))
    unjoined_rate = 1.0 - (timed_count / max(1, len(sim_rows)))
    if len(sim_rows) >= 10 and unjoined_rate > 0.25:
        detectable_families.add("source_quality")
        candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_source_quality_join_gap_missing",
                domain="cross_domain",
                pattern_type="sim_source_quality_join_gap_missing",
                lifecycle_stage="source_quality",
                priority="high",
                sample_count=len(sim_rows) - timed_count,
                source_paths=source_paths,
                evidence=[
                    f"sim_rows={len(sim_rows)}",
                    f"timed_row_count={timed_count}",
                    f"grouped_row_count={grouped_count}",
                    f"time_unjoined_rate={unjoined_rate:.4f}",
                    "gap=sim rows cannot be fully assigned to entry/submit/holding/exit chronology without source-quality producer",
                    "required_producer=sim_lifecycle_join_quality_producer",
                ],
            )
        )

    summary = {
        "sim_rows_scanned": len(sim_rows),
        "sim_evaluation_rows_scanned": len(eval_rows),
        "strict_runner_match_count": len(strict_runner),
        "ambiguous_runner_match_count": len(ambiguous_runner),
        "strict_plateau_match_count": len(strict_plateau),
        "ambiguous_plateau_match_count": len(ambiguous_plateau),
        "detectable_coverage_families": sorted(detectable_families),
    }
    return candidates, summary


def _coverage_audit_candidates(
    candidates: list[dict[str, Any]],
    sim_row_count: int,
    source_paths: list[str],
    *,
    externally_covered_families: set[str] | None = None,
    detectable_families: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pattern_types = {str(item.get("pattern_type") or "") for item in candidates}
    gaps: list[str] = []
    for contract in DETECTOR_REGISTRY:
        if contract.source_scope == "real_anchor" and contract.sim_equivalent_required:
            if contract.pattern_type in pattern_types and contract.sim_equivalent_pattern not in pattern_types:
                gaps.append(f"real_anchor_without_sim_equivalent:{contract.pattern_type}->{contract.sim_equivalent_pattern}")
    stage_families = {contract.coverage_family for contract in DETECTOR_REGISTRY if contract.source_scope == "sim_first"}
    observed_families = {
        str(item.get("coverage_family") or "")
        for item in candidates
        if str(item.get("source_scope") or "") in {"sim_first", "source_quality", "counterfactual_only"}
    }
    observed_families.update(externally_covered_families or set())
    if sim_row_count > 0:
        expected_families = set(detectable_families or set()) & stage_families
        for family in sorted(expected_families - observed_families):
            gaps.append(f"sim_source_present_without_family_detector:{family}")
    audit_candidates: list[dict[str, Any]] = []
    if gaps:
        audit_candidates.append(
            _candidate(
                candidate_id="producer_gap_sim_first_coverage_gap",
                domain="cross_domain",
                pattern_type="sim_first_coverage_gap",
                lifecycle_stage="source_quality",
                priority="high",
                sample_count=len(gaps),
                source_paths=source_paths,
                evidence=[
                    f"coverage_gaps={','.join(gaps[:12])}",
                    "gap=producer_gap_discovery has sim evidence but missing sim-first detector/workorder coverage",
                    "required_producer=producer_gap_discovery_coverage_registry_audit",
                ],
            )
        )
    return audit_candidates, {
        "coverage_gap_count": len(gaps),
        "real_anchor_without_sim_equivalent_count": sum(
            1 for item in gaps if item.startswith("real_anchor_without_sim_equivalent:")
        ),
        "coverage_gaps": gaps[:20],
        "registered_detector_count": len(DETECTOR_REGISTRY),
    }


def _deterministic_proposal(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "unknown")
    pattern_type = str(candidate.get("pattern_type") or "producer_gap")
    contract = candidate.get("recommended_producer_contract")
    preferred = contract.get("preferred_producer_name") if isinstance(contract, dict) else None
    if pattern_type == "sim_source_quality_join_gap_missing":
        decision = "source_quality_blocker"
    elif preferred:
        decision = "extend_existing_producer"
    elif pattern_type in {"sim_submit_fill_quality_gap_missing", "sim_holding_runner_gap_missing", "sim_exit_plateau_breakdown_gap_missing"}:
        decision = "absorb_as_metric_dimension"
    else:
        decision = "new_producer"
    return {
        "candidate_id": candidate_id,
        "proposal_source": "deterministic",
        "proposal_decision": decision,
        "recommended_canonical_bucket": f"producer_gap:{pattern_type}",
        "recommended_metric_or_dimension": [
            "source_quality_adjusted_ev_pct",
            "diagnostic_win_rate",
            f"{pattern_type}_source_dimension",
        ],
        "reasoning_summary": "Deterministic missing-producer detector found a source-only lifecycle observation gap.",
        "confidence": "high" if candidate.get("priority") in {"critical", "high"} else "medium",
        "required_source_fields": list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": list(FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
        "workorder_title": f"Review producer gap: {pattern_type}",
        "workorder_priority": str(candidate.get("priority") or "medium"),
    }


def _default_ai_proposal(candidate: dict[str, Any]) -> dict[str, Any]:
    deterministic = candidate.get("deterministic_proposal") if isinstance(candidate.get("deterministic_proposal"), dict) else {}
    return {
        "candidate_id": str(candidate.get("candidate_id") or "unknown"),
        "proposal_source": "ai_tier2",
        "proposal_status": "not_provided",
        "proposal_decision": "reject",
        "recommended_canonical_bucket": deterministic.get("recommended_canonical_bucket") or "",
        "recommended_metric_or_dimension": deterministic.get("recommended_metric_or_dimension") or [],
        "reasoning_summary": "AI Tier2 proposal unavailable; fail-closed comparative review prevents automatic promotion.",
        "confidence": "low",
        "required_source_fields": list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": list(FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
    }


def _attach_deterministic_proposals(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for candidate in candidates:
        proposal = _deterministic_proposal(candidate)
        enriched.append({**candidate, "deterministic_proposal": proposal})
    return enriched


def _deterministic_candidates(target_date: str, *, rolling_sim_scan: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = _source_paths(target_date)
    jsonl_sources = {"sim_post_sell_evaluations", "post_sell_candidates", "sim_post_sell_candidates"}
    payloads = {label: _load_json(path) for label, path in paths.items() if label not in jsonl_sources}
    sim_rows = _load_jsonl(paths["sim_post_sell_evaluations"])
    real_post_sell_rows = _load_jsonl(paths["post_sell_candidates"])
    sim_candidate_rows = _load_jsonl(paths["sim_post_sell_candidates"])
    rolling_sources = _rolling_sim_sources(target_date, rolling_sim_scan=rolling_sim_scan)
    rolling_sim_rows = rolling_sources["rows"] or sim_candidate_rows
    rolling_eval_rows = rolling_sources["evaluations"] or sim_rows
    candidates: list[dict[str, Any]] = []
    candidates.extend(_detect_stop_recovery(sim_rows, paths["sim_post_sell_evaluations"]))
    candidates.extend(_detect_missed_fill(payloads, paths))
    candidates.extend(_detect_swing_label_gap(payloads, paths))
    candidates.extend(_detect_scale_in_gap(payloads, paths))
    candidates.extend(_detect_time_window_policy_exception_gap(sim_candidate_rows, payloads, paths))
    candidates.extend(_detect_volatile_runner_exit_gap(real_post_sell_rows, sim_candidate_rows, paths))
    candidates.extend(_detect_limit_up_plateau_breakdown_exit_gap(real_post_sell_rows, sim_candidate_rows, paths))
    sim_first_candidates, sim_first_summary = _detect_sim_first_stage_gaps(
        rolling_sim_rows,
        rolling_eval_rows,
        payloads,
        target_date,
    )
    candidates.extend(sim_first_candidates)
    externally_covered_families: set[str] = set()
    time_window_artifact = payloads.get("time_window_regime_counterfactual") or {}
    if (
        isinstance(time_window_artifact, dict)
        and time_window_artifact.get("report_type") == "time_window_regime_counterfactual"
        and str(time_window_artifact.get("status") or "") in {"pass", "warning", "partial"}
    ):
        externally_covered_families.add("time_window")
    coverage_candidates, coverage_summary = _coverage_audit_candidates(
        candidates,
        len(rolling_sim_rows),
        _sim_source_paths(rolling_sim_rows, rolling_eval_rows, target_date),
        externally_covered_families=externally_covered_families,
        detectable_families=set(sim_first_summary.get("detectable_coverage_families") or []),
    )
    candidates.extend(coverage_candidates)
    candidates = _attach_deterministic_proposals(candidates)
    source_scope_counts = Counter(str(item.get("source_scope") or "unknown") for item in candidates)
    context = {
        "date": target_date,
        "report_type": REPORT_TYPE,
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "sources": {
            label: {
                "path": str(path) if path.exists() else None,
                "exists": path.exists(),
                "row_count": (
                    len(sim_rows)
                    if label == "sim_post_sell_evaluations"
                    else len(real_post_sell_rows)
                    if label == "post_sell_candidates"
                    else len(sim_candidate_rows)
                    if label == "sim_post_sell_candidates"
                    else None
                ),
            }
            for label, path in paths.items()
        },
        "rolling_sim_discovery": {
            "enabled": bool(rolling_sim_scan),
            "windows": list(ROLLING_WINDOWS),
            "dates_scanned": rolling_sources["dates"],
            "rows_by_date": rolling_sources["rows_by_date"],
            "evaluation_rows_by_date": rolling_sources["evaluation_rows_by_date"],
            "sim_rows_scanned": len(rolling_sim_rows),
            "sim_evaluation_rows_scanned": len(rolling_eval_rows),
            "guard_hit": bool(rolling_sources["guard_hit"]),
            "paused_reason": rolling_sources.get("paused_reason"),
            "max_rows": rolling_sources["max_rows"],
            **sim_first_summary,
        },
        "coverage_audit": {
            **coverage_summary,
            "source_scope_counts": dict(source_scope_counts),
            "sim_first_coverage_status": "warning" if coverage_summary.get("coverage_gap_count") else "pass",
        },
        "producer_gap_candidates": candidates,
    }
    return candidates, context


def _build_ai_review_instructions() -> str:
    return (
        "You are producer_gap_discovery_ai_review, a source-only missing producer reviewer.\n"
        "Use a mandatory two-pass process: first interpretation, then audit, then final conclusions.\n"
        "Review deterministic missing producer candidates for scalping and swing sim/probe/real-flow results.\n"
        "Create an independent ai_tier2_proposal for each deterministic candidate, then create a comparative_review "
        "that compares deterministic_proposal and ai_tier2_proposal side by side.\n"
        "AI proposal decisions are limited to new_producer, extend_existing_producer, "
        "absorb_as_metric_dimension, source_quality_blocker, or reject.\n"
        "The comparative selected_source must be deterministic, ai_tier2, hybrid, or reject.\n"
        "Metric/dimension absorption requires metric_role, decision_authority, window_policy, sample_floor, "
        "primary_decision_metric, source_quality_gate, and forbidden_uses in required_source_fields.\n"
        "For every ai_tier2_proposal and comparative_review, required_source_fields must contain all seven exact "
        "strings: metric_role, decision_authority, window_policy, sample_floor, primary_decision_metric, "
        "source_quality_gate, forbidden_uses. Do not substitute field examples for this contract list.\n"
        "You may adjust priority, recommended route, implementation requirements, and acceptance tests.\n"
        "You must not delete deterministic candidates and must not grant runtime, threshold, provider, bot, cap, "
        "entry, exit, or broker order authority. Any forbidden-use leak must be surfaced in the audit.\n"
        "Do not request or infer runtime hooks, live apply authority, exit override authority, or broker/order authority. "
        "This report is limited to missing source-only producers and source-quality handoff gaps.\n"
        "For time_window_policy_exception_missing, treat operator seed cutoffs such as 09:30 as source-only "
        "hypotheses, not hard gates. Prefer a dedicated time_window_regime_counterfactual producer that compares "
        "allow_all_in_window, block_all_in_window, and block_general_allow_exception_in_window across cutoff and "
        "segment grids while preserving source-only authority.\n"
        "For volatile_runner_exit_counterfactual_missing, require a source-only producer that compares real trailing "
        "exit profit against same-parent sim runner outcomes and separates bullish volatility continuation from true "
        "reversal. It must not override exits or trailing rules without a separate approved runtime workorder.\n"
        "For limit_up_plateau_breakdown_exit_missing, require a source-only producer that separates long upper-limit "
        "or fixed-price plateau holds from late breakdowns to hard/soft stops. It may compare plateau take-profit, "
        "breakdown exit, and current stop outcomes, but must not override hard stops or create real exit rules without "
        "a separate approved runtime workorder.\n"
        "Real-anchor evidence is incident evidence only. Sim-first rolling evidence is the default missing producer "
        "basis. For sim_* patterns, require dedicated source-only producers and preserve strict versus ambiguous "
        "chronology/source-quality separation. Do not describe current-scope work as hooks, probes, exit actions, "
        "trim actions, stop review actions, or broker/order behavior.\n"
        "Evidence authority contract: bucket/dimension tuning primary evidence is sim/probe lifecycle EV. "
        "Real one-share samples are not primary EV evidence unless the mapped bucket policy was already enabled "
        "for the evaluated post-apply cohort. Pre-apply real samples may be used only for execution-quality "
        "calibration, safety veto, provenance validation, and broker/fill/slippage source-quality checks. "
        "Do not merge real PnL with sim/probe EV and do not promote runtime threshold/order/provider/cap/bot "
        "changes from pre-apply real one-share outcomes. If a proposal violates this contract, select reject or "
        "source_quality_blocker.\n"
        "Do not mark absent swing artifacts as correction_required unless a deterministic swing candidate is present. "
        "If an existing producer artifact already handles a family, recommend extension or audit only when the "
        "deterministic candidate explicitly requests it.\n"
        "AI unavailable or parse rejection is fail-closed by the caller, so return strict JSON only.\n"
        "Return only JSON conforming to producer_gap_discovery_ai_review_v1."
    )


def _call_openai_ai_review(context: dict[str, Any]) -> tuple[Any | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import (
            _extract_openai_response_text,
            _load_threshold_ai_openai_keys,
        )
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}
    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured"}
    prompt = json.dumps(context, ensure_ascii=False, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=AI_REVIEW_MODEL,
                instructions=_build_ai_review_instructions(),
                input=prompt,
                text={"format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME), "verbosity": "low"},
                reasoning={"effort": AI_REVIEW_REASONING_EFFORT},
                store=False,
                metadata={
                    "endpoint_name": AI_REVIEWER_NAME,
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "report_type": REPORT_TYPE,
                },
                timeout=AI_REVIEW_TIMEOUT_SEC,
            )
            raw_text = _extract_openai_response_text(response)
            usage = getattr(response, "usage", None)
            return raw_text, {
                "provider": "openai",
                "status": "success",
                "key_name": key_name,
                "attempt_index": attempt_index,
                "attempted_key_count": len(api_keys),
                "model": AI_REVIEW_MODEL,
                "schema_name": AI_REVIEW_SCHEMA_NAME,
                "reasoning_effort": AI_REVIEW_REASONING_EFFORT,
                "timeout_sec": AI_REVIEW_TIMEOUT_SEC,
                "input_context_hash": _text_hash(context),
                "input_context_chars": len(prompt),
                "output_chars": len(raw_text),
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
                "total_tokens": int(getattr(usage, "total_tokens", 0) or 0) if usage else 0,
            }
        except RateLimitError as exc:
            errors.append({"key_name": key_name, "error": f"rate_limit:{exc}"})
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {
        "provider": "openai",
        "status": "unavailable",
        "reason": "all OpenAI attempts failed",
        "model": AI_REVIEW_MODEL,
        "reasoning_effort": AI_REVIEW_REASONING_EFFORT,
        "timeout_sec": AI_REVIEW_TIMEOUT_SEC,
        "errors": errors[-3:],
    }


def _parse_ai_review_response(raw_response: Any | None) -> tuple[str, dict[str, Any], list[str]]:
    if raw_response in (None, ""):
        return "missing", {}, ["ai_review_response_missing"]
    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        try:
            payload = json.loads(str(raw_response))
        except Exception as exc:
            return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    warnings: list[str] = []
    if payload.get("schema_version") != 1:
        warnings.append("ai_review_schema_version_invalid")
    if payload.get("reviewer") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    if not isinstance(payload.get("candidate_reviews"), list):
        warnings.append("ai_review_candidate_reviews_missing")
    if not isinstance(payload.get("ai_tier2_proposals"), list):
        warnings.append("ai_review_ai_tier2_proposals_missing")
    if not isinstance(payload.get("comparative_reviews"), list):
        warnings.append("ai_review_comparative_reviews_missing")
    for item in payload.get("ai_tier2_proposals") or []:
        if not isinstance(item, dict):
            warnings.append("ai_review_ai_tier2_proposal_invalid")
            continue
        if str(item.get("proposal_decision") or "") not in PRODUCER_DUAL_DECISIONS:
            warnings.append(f"ai_review_ai_proposal_decision_invalid:{item.get('candidate_id')}")
        missing_contract = missing_metric_contract_fields(item.get("required_source_fields"))
        if missing_contract:
            warnings.append(f"ai_review_ai_proposal_contract_missing:{item.get('candidate_id')}:{','.join(missing_contract)}")
        if has_forbidden_runtime_leak(item):
            warnings.append(f"ai_review_ai_proposal_forbidden_use_leak:{item.get('candidate_id')}")
        if has_evidence_authority_violation(item):
            warnings.append(f"ai_review_ai_proposal_evidence_authority_violation:{item.get('candidate_id')}")
    proposal_ids = {
        str(item.get("candidate_id"))
        for item in payload.get("ai_tier2_proposals") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }
    review_ids = {
        str(item.get("candidate_id"))
        for item in payload.get("comparative_reviews") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }
    if proposal_ids and proposal_ids - review_ids:
        warnings.append("ai_review_comparative_review_missing_for_ai_proposal")
    for item in payload.get("comparative_reviews") or []:
        if not isinstance(item, dict):
            warnings.append("ai_review_comparative_review_invalid")
            continue
        if str(item.get("selected_decision") or "") not in PRODUCER_DUAL_DECISIONS:
            warnings.append(f"ai_review_comparative_decision_invalid:{item.get('candidate_id')}")
        if str(item.get("selected_source") or "") not in {"deterministic", "ai_tier2", "hybrid", "reject"}:
            warnings.append(f"ai_review_comparative_source_invalid:{item.get('candidate_id')}")
        missing_contract = missing_metric_contract_fields(item.get("required_source_fields"))
        if missing_contract:
            warnings.append(f"ai_review_comparative_contract_missing:{item.get('candidate_id')}:{','.join(missing_contract)}")
        if has_forbidden_runtime_leak(item):
            warnings.append(f"ai_review_comparative_forbidden_use_leak:{item.get('candidate_id')}")
        if has_evidence_authority_violation(item):
            warnings.append(f"ai_review_comparative_evidence_authority_violation:{item.get('candidate_id')}")
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_forbidden_use_violations_missing")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _load_ai_review_response(path: str | None) -> Any | None:
    if not path:
        return None
    review_path = Path(path)
    text = review_path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _review_by_candidate(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in ai_payload.get("candidate_reviews") or []:
        if isinstance(item, dict) and item.get("candidate_id"):
            result[str(item["candidate_id"])] = item
    return result


def _proposal_by_candidate(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("candidate_id")): {**item, "proposal_source": "ai_tier2", "proposal_status": "provided"}
        for item in ai_payload.get("ai_tier2_proposals") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }


def _comparative_by_candidate(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("candidate_id")): item
        for item in ai_payload.get("comparative_reviews") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }


def _order_from_candidate(
    candidate: dict[str, Any],
    review: dict[str, Any],
    *,
    ai_tier2_proposal: dict[str, Any] | None = None,
    comparative_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "unknown")
    pattern_type = str(candidate.get("pattern_type") or "producer_gap")
    priority = str(review.get("priority") or candidate.get("priority") or "high")
    implementation_status = candidate.get("implementation_status")
    implementation_provenance = (
        candidate.get("implementation_provenance")
        if isinstance(candidate.get("implementation_provenance"), dict)
        else {}
    )
    return {
        "order_id": f"order_{REPORT_TYPE}_{_slug(candidate_id)}",
        "title": f"Implement missing producer: {pattern_type}",
        "source_report_type": REPORT_TYPE,
        "lifecycle_stage": candidate.get("lifecycle_stage"),
        "target_subsystem": review.get("target_subsystem") or "postclose_source_producer",
        "route": review.get("recommended_route") or "implement_now",
        "priority": PRIORITY_RANK.get(priority, 1) + 1,
        "producer_gap_priority": priority,
        "confidence": review.get("confidence") or "ai_two_pass_review",
        "improvement_type": pattern_type,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "producer_gap_discovery_workorder_source_only",
        "intent": review.get("reason") or "Add a source-only producer for a missing observation gap.",
        "expected_ev_effect": "Improve source-quality adjusted EV attribution by making the missing producer observable.",
        "evidence": list(candidate.get("evidence") or []) + [f"ai_priority={priority}", f"ai_route={review.get('recommended_route')}"],
        "source_paths": candidate.get("source_paths") or [],
        "files_likely_touched": review.get("files_likely_touched")
        or [
            "src/engine/automation/producer_gap_discovery.py",
            "src/engine/build_code_improvement_workorder.py",
            "src/engine/verify_threshold_cycle_postclose_chain.py",
        ],
        "acceptance_tests": review.get("acceptance_tests")
        or [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_producer_gap_discovery.py src/tests/test_build_code_improvement_workorder.py",
            "runtime_effect remains false and broker/order/provider/bot/threshold authority is forbidden",
        ],
        "next_postclose_metric": f"{REPORT_TYPE}.{candidate_id}",
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "implementation_requirements": review.get("implementation_requirements") or [],
        "canonical_bucket": comparative_review.get("recommended_canonical_bucket") if isinstance(comparative_review, dict) else None,
        "legacy_raw_bucket_key": candidate.get("pattern_type"),
        "deterministic_proposal": candidate.get("deterministic_proposal"),
        "ai_tier2_proposal": ai_tier2_proposal or {},
        "comparative_review": comparative_review or {},
        "implementation_status": implementation_status,
        "implementation_provenance": implementation_provenance,
        "implementation_checks": candidate.get("implementation_checks") or [],
    }


def _source_bundle_by_pattern(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    sections = bundle.get("sections") if isinstance(bundle.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        pattern_type = str(section.get("pattern_type") or section.get("section_id") or "").strip()
        if pattern_type:
            out[pattern_type] = section
    return out


def _apply_source_bundle_implementation(
    candidate: dict[str, Any],
    source_bundle_sections: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pattern_type = str(candidate.get("pattern_type") or "").strip()
    normalized_pattern = pattern_type.removesuffix("_missing")
    aliases = {
        "sim_scale_in_counterfactual_gap": "sim_scale_in_would_add_counterfactual",
        "limit_up_plateau_breakdown_exit": "limit_up_plateau_breakdown_exit_counterfactual",
        "sim_exit_plateau_breakdown_gap": "sim_exit_plateau_breakdown_counterfactual",
        "sim_holding_runner_gap": "sim_holding_runner_counterfactual",
        "sim_stop_recovery_gap": "sim_stop_recovery_counterfactual",
    }
    section = (
        source_bundle_sections.get(pattern_type)
        or source_bundle_sections.get(normalized_pattern)
        or source_bundle_sections.get(aliases.get(normalized_pattern, ""))
    )
    if not section:
        return candidate
    status = str(section.get("source_quality_status") or "").strip()
    if status == "source_field_missing":
        return {
            **candidate,
            "producer_source_bundle_status": status,
            "producer_source_bundle_missing_fields": section.get("missing_fields") or [],
        }
    implementation_status = "implemented" if status == "implemented" else "implemented_but_hold_sample"
    return {
        **candidate,
        "implementation_status": implementation_status,
        "implementation_checks": [
            "producer_gap_source_bundle section exists",
            "section has source_paths and join_keys contract",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ],
        "implementation_provenance": {
            "implementation_type": "source_only_producer_gap_source_bundle",
            "source_report_type": "producer_gap_source_bundle",
            "section_id": section.get("section_id"),
            "pattern_type": section.get("pattern_type"),
            "source_quality_status": status,
            "sample_count": section.get("sample_count"),
            "source_paths": section.get("source_paths") or [],
            "join_keys": section.get("join_keys") or [],
            "missing_fields": section.get("missing_fields") or [],
            "runtime_effect": section.get("runtime_effect"),
            "allowed_runtime_apply": section.get("allowed_runtime_apply"),
        },
        "producer_source_bundle_status": status,
    }


def build_producer_gap_discovery_report(
    target_date: str,
    *,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
    rolling_sim_scan: bool = False,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    resolved_provider = str(
        provider
        if provider is not None
        else os.getenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)
    ).strip().lower() or "none"
    candidates, context = _deterministic_candidates(target_date, rolling_sim_scan=rolling_sim_scan)
    source_bundle_path, _ = producer_gap_source_bundle_paths(target_date)
    source_bundle = _load_json(source_bundle_path)
    source_bundle_sections = _source_bundle_by_pattern(source_bundle) if source_bundle else {}
    candidates = [_apply_source_bundle_implementation(candidate, source_bundle_sections) for candidate in candidates]
    provider_status: dict[str, Any] = {
        "provider": resolved_provider,
        "status": "disabled" if resolved_provider in {"none", "off", "false", "0"} else "not_called",
        "model": AI_REVIEW_MODEL if resolved_provider not in {"none", "off", "false", "0"} else None,
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "input_context_hash": _text_hash(context),
    }
    raw_response = ai_raw_response
    if raw_response is not None:
        provider_status["status"] = "provided_response"
    if raw_response is None and resolved_provider == "openai":
        raw_response, provider_status = _call_openai_ai_review(context)
    ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
    audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    audit_forbidden_use_violations = audit.get("forbidden_use_violations")
    if not isinstance(audit_forbidden_use_violations, list):
        audit_forbidden_use_violations = []
    review_map = _review_by_candidate(ai_payload) if ai_status == "parsed" else {}
    ai_proposal_map = _proposal_by_candidate(ai_payload) if ai_status == "parsed" else {}
    comparative_map = _comparative_by_candidate(ai_payload) if ai_status == "parsed" else {}
    candidate_ids = {str(item.get("candidate_id") or "") for item in candidates}
    missing_ai_proposal_count = len([candidate_id for candidate_id in candidate_ids if candidate_id not in ai_proposal_map])
    missing_comparative_review_count = len([candidate_id for candidate_id in candidate_ids if candidate_id not in comparative_map])
    fail_closed = (
        ai_status != "parsed"
        or audit.get("status") != "pass"
        or bool(audit_forbidden_use_violations)
        or missing_ai_proposal_count > 0
        or missing_comparative_review_count > 0
    )
    reviewed_candidates = []
    orders = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        review = review_map.get(candidate_id) or {}
        deterministic_proposal = (
            candidate.get("deterministic_proposal") if isinstance(candidate.get("deterministic_proposal"), dict) else {}
        )
        ai_tier2_proposal = ai_proposal_map.get(candidate_id) or _default_ai_proposal(candidate)
        comparative_review = comparative_map.get(candidate_id) or default_comparative_review(
            candidate_id=candidate_id,
            deterministic_proposal=deterministic_proposal,
            ai_tier2_proposal=ai_tier2_proposal,
            allowed_decisions=PRODUCER_DUAL_DECISIONS,
            default_decision="new_producer",
            workorder_title=f"Review producer gap: {candidate.get('pattern_type')}",
        )
        if ai_status != "parsed":
            comparative_review = {**comparative_review, "selected_decision": "source_quality_blocker", "selected_source": "reject"}
        merged = {
            **candidate,
            "ai_review": review,
            "ai_tier2_proposal": ai_tier2_proposal,
            "comparative_review": comparative_review,
            "ai_review_status": ai_status,
            "ai_priority": review.get("priority") or candidate.get("priority"),
            "ai_recommended_route": review.get("recommended_route") or "implement_now",
        }
        reviewed_candidates.append(merged)
        priority = str(merged.get("ai_priority") or "high")
        selected_decision = str(comparative_review.get("selected_decision") or "")
        if (
            not fail_closed
            and selected_decision not in {"reject", "source_quality_blocker"}
            and PRIORITY_RANK.get(priority, 99) <= PRIORITY_RANK["high"]
        ):
            orders.append(_order_from_candidate(candidate, review, ai_tier2_proposal=ai_tier2_proposal, comparative_review=comparative_review))
    state_counts = Counter(str(item.get("pattern_type") or "unknown") for item in candidates)
    source_scope_counts = Counter(str(item.get("source_scope") or "unknown") for item in candidates)
    rolling_summary = context.get("rolling_sim_discovery") if isinstance(context.get("rolling_sim_discovery"), dict) else {}
    coverage_audit = context.get("coverage_audit") if isinstance(context.get("coverage_audit"), dict) else {}
    status = "fail" if fail_closed else ("warning" if orders else "pass")
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_mutation_allowed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "producer_gap_discovery_source_only",
        "metric_role": "source_quality_gate",
        "window_policy": "same_day_postclose_sim_probe_real_flow_review",
        "sample_floor": 1,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "source artifact exists and parsed AI review passed",
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "status": status,
        "sources": {
            label: str(path) if path.exists() else None
            for label, path in _source_paths(target_date).items()
        },
        "summary": {
            "status": status,
            "candidate_count": len(candidates),
            "high_priority_candidate_count": sum(
                1 for item in reviewed_candidates if PRIORITY_RANK.get(str(item.get("ai_priority")), 99) <= 1
            ),
            "workorder_count": len(orders),
            "deterministic_proposal_count": len(candidates),
            "ai_tier2_proposal_count": sum(
                1 for item in reviewed_candidates if item.get("ai_tier2_proposal", {}).get("proposal_status") == "provided"
            ),
            "comparative_review_count": len(reviewed_candidates),
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
            "selected_decision_counts": proposal_counts(
                [item.get("comparative_review") or {} for item in reviewed_candidates],
                key="selected_decision",
            ),
            "selected_source_counts": proposal_counts(
                [item.get("comparative_review") or {} for item in reviewed_candidates],
                key="selected_source",
            ),
            "ai_two_pass_review_status": ai_status,
            "ai_fail_closed": fail_closed,
            "provider": resolved_provider,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "audit_status": audit.get("status"),
            "pattern_type_counts": dict(state_counts),
            "source_scope_counts": dict(source_scope_counts),
            "sim_first_pattern_count": source_scope_counts.get("sim_first", 0),
            "real_anchor_pattern_count": source_scope_counts.get("real_anchor", 0),
            "sim_first_coverage_status": coverage_audit.get("sim_first_coverage_status"),
            "coverage_gap_count": coverage_audit.get("coverage_gap_count", 0),
            "real_anchor_without_sim_equivalent_count": coverage_audit.get("real_anchor_without_sim_equivalent_count", 0),
            "rolling_sim_scan_enabled": bool(rolling_sim_scan),
            "rolling_dates_scanned": rolling_summary.get("dates_scanned") or [],
            "sim_rows_scanned": rolling_summary.get("sim_rows_scanned", 0),
            "strict_match_count": _safe_int(rolling_summary.get("strict_runner_match_count"), 0)
            + _safe_int(rolling_summary.get("strict_plateau_match_count"), 0),
            "ambiguous_match_count": _safe_int(rolling_summary.get("ambiguous_runner_match_count"), 0)
            + _safe_int(rolling_summary.get("ambiguous_plateau_match_count"), 0),
            "resume_required": bool(rolling_summary.get("guard_hit")),
            "human_intervention_required": False,
        },
        "rolling_sim_discovery": rolling_summary,
        "coverage_audit": coverage_audit,
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "input_context_hash": _text_hash(context),
            "audit": audit,
            "candidate_reviews": ai_payload.get("candidate_reviews") if isinstance(ai_payload.get("candidate_reviews"), list) else [],
            "deterministic_proposals": [
                item.get("deterministic_proposal") for item in reviewed_candidates if item.get("deterministic_proposal")
            ],
            "ai_tier2_proposals": [
                item.get("ai_tier2_proposal") for item in reviewed_candidates if item.get("ai_tier2_proposal")
            ],
            "comparative_reviews": [
                item.get("comparative_review") for item in reviewed_candidates if item.get("comparative_review")
            ],
            "warnings": ai_warnings,
            "fail_closed": fail_closed,
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
        },
        "deterministic_proposals": [
            item.get("deterministic_proposal") for item in reviewed_candidates if item.get("deterministic_proposal")
        ],
        "ai_tier2_proposals": [
            item.get("ai_tier2_proposal") for item in reviewed_candidates if item.get("ai_tier2_proposal")
        ],
        "comparative_reviews": [
            item.get("comparative_review") for item in reviewed_candidates if item.get("comparative_review")
        ],
        "selected_decision_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in reviewed_candidates],
            key="selected_decision",
        ),
        "selected_source_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in reviewed_candidates],
            key="selected_source",
        ),
        "producer_gap_candidates": reviewed_candidates,
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    review = report.get("ai_two_pass_review") if isinstance(report.get("ai_two_pass_review"), dict) else {}
    lines = [
        f"# Producer Gap Discovery - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- candidate_count: `{summary.get('candidate_count')}`",
        f"- high_priority_candidate_count: `{summary.get('high_priority_candidate_count')}`",
        f"- workorder_count: `{summary.get('workorder_count')}`",
        f"- sim_first_coverage_status: `{summary.get('sim_first_coverage_status')}`",
        f"- rolling_dates_scanned: `{summary.get('rolling_dates_scanned') or []}`",
        f"- sim_rows_scanned: `{summary.get('sim_rows_scanned')}`",
        f"- strict_match_count: `{summary.get('strict_match_count')}`",
        f"- ambiguous_match_count: `{summary.get('ambiguous_match_count')}`",
        f"- ai_two_pass_review_status: `{summary.get('ai_two_pass_review_status')}`",
        f"- ai_fail_closed: `{summary.get('ai_fail_closed')}`",
        f"- audit_status: `{summary.get('audit_status')}`",
        "",
        "## AI Review",
        "",
        f"- provider: `{review.get('provider')}`",
        f"- model: `{review.get('model') or '-'}`",
        f"- warnings: `{review.get('warnings') or []}`",
        "",
        "## Candidates",
        "",
    ]
    for item in report.get("producer_gap_candidates") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('candidate_id')}` type=`{item.get('pattern_type')}` "
            f"priority=`{item.get('ai_priority')}` samples=`{item.get('sample_count')}`"
        )
    lines.extend(["", "## Code Improvement Orders", ""])
    for order in report.get("code_improvement_orders") or []:
        if isinstance(order, dict):
            lines.append(f"- `{order.get('order_id')}`: {order.get('title')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--provider",
        default=os.getenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER),
        choices=["openai", "none", "off", "false", "0"],
    )
    parser.add_argument(
        "--ai-review-response-json",
        help="Strict producer_gap_discovery_ai_review_v1 JSON response to parse instead of calling a provider.",
    )
    parser.add_argument("--rolling-sim-scan", action="store_true", help="Scan all available historical sim rows.")
    args = parser.parse_args(argv)
    report = build_producer_gap_discovery_report(
        args.date,
        provider=args.provider,
        ai_raw_response=_load_ai_review_response(args.ai_review_response_json),
        rolling_sim_scan=bool(args.rolling_sim_scan),
    )
    json_path, md_path = report_paths(args.date)
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 1 if report.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
