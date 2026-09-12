"""Evaluate and activate a cohort-isolated live Holding prompt.

Postclose evaluation is provider-bounded, exact-payload replay only.  A
candidate becomes PREOPEN-eligible only after an explicit cost-adjusted EV of
at least +0.10 percentage point, a 10-row/3-symbol floor, and a non-worse
severe-tail count.  Runtime consumes only the date-scoped activation and falls
back to ``holding_score_v2`` on every contract gap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import fmean
from typing import Any, Mapping

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION,
    decision_quality_holding_v2_4_live_score_system_prompt,
)
from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import ai_stage_coverage_replay as coverage
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

REPORT_SCHEMA = "holding_prompt_paired_replay_v1"
ECONOMICS_SCHEMA = "holding_prompt_cost_adjusted_economics_v1"
CANDIDATE_SCHEMA = "holding_prompt_live_candidate_v1"
ACTIVATION_SCHEMA = "holding_prompt_preopen_activation_v1"
PROMPT_SCHEMA_NAME = "decision_quality_holding_score_v1"
FALLBACK_PROMPT_VERSION = "holding_score_v2"
REPORT_DIR = DATA_DIR / "report" / "holding_prompt_paired_replay"
CANDIDATE_DIR = DATA_DIR / "threshold_cycle" / "holding_prompt_candidates"
ACTIVATION_DIR = DATA_DIR / "runtime" / "holding_prompt_live_policy"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
MIN_COST_ADJUSTED_EV_PCT = 0.10
MIN_ROWS = 10
MIN_SYMBOLS = 3
SEVERE_TAIL_PCT = -1.0
SUPPORTED_COHORTS = (
    ("KRX", "KRX_REGULAR"),
    ("NXT", "KRX_REGULAR"),
    ("NXT", "NXT_REGULAR_OVERLAP"),
    ("NXT", "NXT_REGULAR"),
    ("PREMARKET_KRX_LIKE", "PREMARKET_KRX_LIKE"),
    ("NXT", "NXT_PREMARKET"),
    ("PREMARKET_KRX_LIKE", "NXT_PREMARKET"),
    ("NXT", "NXT_AFTERMARKET"),
    ("KRX_NXT_INTEGRATED", "KRX_NXT_AFTERMARKET"),
)
_POLICY_CACHE_LOCK = threading.Lock()
_POLICY_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}


def _slug(value: Any) -> str:
    return str(value or "").strip().lower()


def _cohort(value: tuple[Any, Any]) -> tuple[str, str]:
    return (str(value[0] or "").strip().upper(), str(value[1] or "").strip().upper())


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _file_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def report_path(target_date: str, cohort: tuple[str, str]) -> Path:
    venue, session = _cohort(cohort)
    return REPORT_DIR / (
        f"holding_prompt_paired_replay_{target_date}_{_slug(venue)}_{_slug(session)}.json"
    )


def candidate_path(source_date: str, cohort: tuple[str, str]) -> Path:
    venue, session = _cohort(cohort)
    return CANDIDATE_DIR / (
        f"holding_prompt_live_candidate_{source_date}_{_slug(venue)}_{_slug(session)}.json"
    )


def activation_path(target_date: str, cohort: tuple[str, str]) -> Path:
    venue, session = _cohort(cohort)
    return ACTIVATION_DIR / (
        f"holding_prompt_preopen_activation_{target_date}_{_slug(venue)}_{_slug(session)}.json"
    )


def _next_trading_date(source_date: str) -> str:
    current = date.fromisoformat(source_date) + timedelta(days=1)
    for _ in range(15):
        if is_krx_trading_day(current):
            return current.isoformat()
        current += timedelta(days=1)
    raise RuntimeError("next_krx_trading_date_unresolved")


def _holding_economics(
    *,
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> dict[str, Any]:
    request_by_pair = {str(row.get("paired_replay_id") or ""): row for row in requests}
    label_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in labels
        if row.get("source_quality_status") == "pass"
    }
    rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for result in results:
        if (
            result.get("status") != "pass"
            or result.get("same_payload_confirmed") is not True
        ):
            continue
        request = request_by_pair.get(str(result.get("paired_replay_id") or ""))
        trace_id = str(result.get("decision_trace_id") or "")
        label = label_by_trace.get(trace_id)
        metric = quality._primary_metric(label or {})
        cost_value, cost_basis = (
            quality._micro_reversion_cost_adjusted_outcome_with_basis(metric or {})
        )
        candidate_action = str(
            (result.get("candidate_response") or {}).get("action") or ""
        ).upper()
        control_action = str(
            (result.get("control_response") or {}).get("action") or ""
        ).upper()
        if request is None or label is None or cost_value is None or cost_basis is None:
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": "explicit_cost_adjusted_outcome_missing",
                }
            )
            continue
        if candidate_action == "TRIM" or control_action == "TRIM":
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": "trim_fractional_outcome_contract_missing",
                }
            )
            continue
        if candidate_action not in {"HOLD", "EXIT"} or control_action not in {
            "HOLD",
            "EXIT",
        }:
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": "holding_action_contract_invalid",
                }
            )
            continue
        candidate_value = cost_value if candidate_action == "HOLD" else 0.0
        control_value = cost_value if control_action == "HOLD" else 0.0
        rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": request.get("stock_code"),
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "cost_adjusted_outcome_pct": cost_value,
                "cost_adjusted_outcome_basis": cost_basis,
                "control_action": control_action,
                "candidate_action": candidate_action,
                "control_value_pct": control_value,
                "candidate_value_pct": candidate_value,
                "delta_pct": candidate_value - control_value,
            }
        )
    symbols = {
        str(row.get("stock_code") or "") for row in rows if row.get("stock_code")
    }
    candidate_ev = fmean(row["candidate_value_pct"] for row in rows) if rows else None
    control_ev = fmean(row["control_value_pct"] for row in rows) if rows else None
    candidate_tail = sum(
        row["candidate_action"] == "HOLD"
        and row["cost_adjusted_outcome_pct"] <= SEVERE_TAIL_PCT
        for row in rows
    )
    control_tail = sum(
        row["control_action"] == "HOLD"
        and row["cost_adjusted_outcome_pct"] <= SEVERE_TAIL_PCT
        for row in rows
    )
    return {
        "schema": ECONOMICS_SCHEMA,
        "status": "complete" if len(rows) == len(requests) and rows else "incomplete",
        "row_count": len(rows),
        "unique_symbol_count": len(symbols),
        "candidate_cost_adjusted_ev_pct": candidate_ev,
        "control_cost_adjusted_ev_pct": control_ev,
        "candidate_cost_adjusted_ev_delta_pct": (
            candidate_ev - control_ev
            if candidate_ev is not None and control_ev is not None
            else None
        ),
        "candidate_positive_outcome_frequency": (
            sum(row["candidate_value_pct"] > 0 for row in rows) / len(rows)
            if rows
            else None
        ),
        "candidate_severe_tail_count": candidate_tail,
        "control_severe_tail_count": control_tail,
        "exclusion_count": len(exclusions),
        "exclusions": exclusions,
        "rows": rows,
        "metric_role": "holding_prompt_explicit_cost_adjusted_counterfactual_ev",
        "decision_authority": "offline_replay_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _valid_report(report: Mapping[str, Any], cohort: tuple[str, str]) -> bool:
    venue, session = _cohort(cohort)
    prompt = decision_quality_holding_v2_4_live_score_system_prompt()
    economics = report.get("holding_cost_adjusted_economics")
    economics = economics if isinstance(economics, Mapping) else {}
    return bool(
        report.get("schema") == REPORT_SCHEMA
        and report.get("artifact_content_sha256")
        == _canonical_sha256(
            {
                key: value
                for key, value in report.items()
                if key != "artifact_content_sha256"
            }
        )
        and report.get("stage") == "holding"
        and report.get("effective_venue") == venue
        and report.get("session_bucket") == session
        and report.get("candidate_prompt_version")
        == DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION
        and report.get("candidate_prompt_sha256") == quality._sha256(prompt)
        and report.get("provider_failed_count") == 0
        and report.get("schema_rejected_count") == 0
        and report.get("request_count") == report.get("result_count")
        and report.get("request_count") == report.get("pass_count")
        and economics.get("schema") == ECONOMICS_SCHEMA
        and economics.get("runtime_effect") is False
        and economics.get("allowed_runtime_apply") is False
        and report.get("runtime_effect") is False
        and report.get("allowed_runtime_apply") is False
    )


def _cumulative_economics(source_date: str, cohort: tuple[str, str]) -> dict[str, Any]:
    latest_rows: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    source_limit = date.fromisoformat(source_date)
    for path in sorted(REPORT_DIR.glob("holding_prompt_paired_replay_*.json")):
        report = _read_json(path)
        try:
            report_date = date.fromisoformat(str(report.get("target_date") or ""))
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= report_date <= source_limit or not _valid_report(
            report, cohort
        ):
            continue
        economics = report["holding_cost_adjusted_economics"]
        for row in economics.get("rows") or []:
            if isinstance(row, dict) and row.get("decision_trace_id"):
                latest_rows[str(row["decision_trace_id"])] = dict(row)
        evidence.append(
            {
                "path": str(path),
                "file_sha256": _file_sha256(path),
                "target_date": report_date.isoformat(),
            }
        )
    rows = list(latest_rows.values())
    symbols = {
        str(row.get("stock_code") or "") for row in rows if row.get("stock_code")
    }
    candidate_ev = fmean(row["candidate_value_pct"] for row in rows) if rows else None
    control_ev = fmean(row["control_value_pct"] for row in rows) if rows else None
    candidate_tail = sum(
        row["candidate_action"] == "HOLD"
        and row["cost_adjusted_outcome_pct"] <= SEVERE_TAIL_PCT
        for row in rows
    )
    control_tail = sum(
        row["control_action"] == "HOLD"
        and row["cost_adjusted_outcome_pct"] <= SEVERE_TAIL_PCT
        for row in rows
    )
    return {
        "clean_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "as_of_date": source_date,
        "row_count": len(rows),
        "unique_symbol_count": len(symbols),
        "candidate_cost_adjusted_ev_pct": candidate_ev,
        "control_cost_adjusted_ev_pct": control_ev,
        "candidate_cost_adjusted_ev_delta_pct": (
            candidate_ev - control_ev
            if candidate_ev is not None and control_ev is not None
            else None
        ),
        "candidate_positive_outcome_frequency": (
            sum(row["candidate_value_pct"] > 0 for row in rows) / len(rows)
            if rows
            else None
        ),
        "candidate_severe_tail_count": candidate_tail,
        "control_severe_tail_count": control_tail,
        "source_reports": evidence,
    }


def build_candidate(source_date: str, cohort: tuple[str, str]) -> dict[str, Any]:
    venue, session = _cohort(cohort)
    economics = _cumulative_economics(source_date, cohort)
    blockers: list[str] = []
    if economics["row_count"] < MIN_ROWS:
        blockers.append("holding_prompt_row_floor_not_met")
    if economics["unique_symbol_count"] < MIN_SYMBOLS:
        blockers.append("holding_prompt_symbol_floor_not_met")
    candidate_ev = economics["candidate_cost_adjusted_ev_pct"]
    if candidate_ev is None:
        blockers.append("holding_prompt_explicit_cost_adjusted_ev_missing")
    elif candidate_ev < MIN_COST_ADJUSTED_EV_PCT:
        blockers.append("holding_prompt_cost_adjusted_ev_below_0_10pct")
    delta = economics["candidate_cost_adjusted_ev_delta_pct"]
    if delta is None or delta < 0:
        blockers.append("holding_prompt_cost_adjusted_ev_not_better_than_control")
    if (
        economics["candidate_severe_tail_count"]
        > economics["control_severe_tail_count"]
    ):
        blockers.append("holding_prompt_severe_tail_increased")
    prompt = decision_quality_holding_v2_4_live_score_system_prompt()
    body = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": source_date,
        "effective_date": _next_trading_date(source_date),
        "effective_venue": venue,
        "session_bucket": session,
        "status": "preopen_apply_ready" if not blockers else "keep_collecting",
        "selected_prompt_version": DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION,
        "selected_prompt_sha256": quality._sha256(prompt),
        "selected_response_schema": PROMPT_SCHEMA_NAME,
        "rollback_prompt_version": FALLBACK_PROMPT_VERSION,
        "promotion_thresholds": {
            "minimum_cost_adjusted_ev_pct": MIN_COST_ADJUSTED_EV_PCT,
            "minimum_rows": MIN_ROWS,
            "minimum_symbols": MIN_SYMBOLS,
            "severe_tail_pct": SEVERE_TAIL_PCT,
        },
        "cumulative_economics": economics,
        "blocking_reasons": blockers,
        "runtime_effect": False,
        "allowed_runtime_apply": not blockers,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "unchanged_runtime_guards": [
            "provider_and_model_route",
            "quantity_and_cap",
            "order_price_and_type",
            "deterministic_exit_and_hard_safety",
        ],
    }
    return {**body, "artifact_sha256": _canonical_sha256(body)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    quality._atomic_write_json(path, payload)


def run_postclose(
    target_date: str,
    *,
    execute_candidate: bool,
    max_new_total: int,
    workers: int,
    timeout_sec: float,
    write: bool,
) -> dict[str, Any]:
    control = quality._load_json(quality.control_path(target_date))
    traces = coverage._load_rows(quality.TRACE_DIR, "ai_decision_trace", [target_date])
    payloads = coverage._load_rows(
        quality.PAYLOAD_DIR, "ai_decision_payloads", [target_date]
    )
    labels = (
        quality._load_json(quality.label_report_path(target_date)).get("labels") or []
    )
    eligible_ids = {
        str(row.get("decision_trace_id") or "")
        for row in labels
        if row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
        and quality._primary_metric(row) is not None
    }
    observed: dict[tuple[str, str], int] = defaultdict(int)
    for trace in traces:
        if (
            str(trace.get("endpoint") or "") == "holding_score"
            and str(trace.get("decision_trace_id") or "") in eligible_ids
        ):
            observed[
                _cohort((trace.get("effective_venue"), trace.get("session_bucket")))
            ] += 1
    active_cohorts = [cohort for cohort in SUPPORTED_COHORTS if observed.get(cohort)]
    allocations: dict[tuple[str, str], int] = {}
    if active_cohorts and max_new_total > 0:
        base, remainder = divmod(max_new_total, len(active_cohorts))
        for index, cohort in enumerate(active_cohorts):
            allocations[cohort] = base + (1 if index < remainder else 0)
    cohort_results: list[dict[str, Any]] = []
    provider_new_call_count = 0
    for cohort in active_cohorts:
        limit = allocations.get(cohort, 0)
        requests, source_summary = coverage.prepare_stage_requests(
            stage="holding",
            dates=[target_date],
            max_rows=max(1, limit),
            control_manifest=control,
            promotion={},
            traces=traces,
            payloads=payloads,
            eligible_trace_ids=eligible_ids,
            holding_live_compatible=True,
            effective_venue=cohort[0],
            session_bucket=cohort[1],
        )
        path = report_path(target_date, cohort)
        previous = _read_json(path)
        previous_coverage = previous.get("coverage_report")
        previous_coverage = (
            previous_coverage if isinstance(previous_coverage, dict) else {}
        )
        results = coverage.reusable_pass_results(
            existing_report=previous_coverage,
            requests=requests,
        )
        if execute_candidate and limit > 0:
            completed = {str(row.get("paired_replay_id") or "") for row in results}
            pending = [
                row
                for row in requests
                if str(row.get("paired_replay_id") or "") not in completed
            ]
            provider_new_call_count += len(pending)
            results += quality.run_paired_replay_parallel(
                pending,
                control_runner=lambda request: {
                    "action": (request.get("control") or {}).get("captured_action"),
                    "score": (request.get("control") or {}).get("captured_score"),
                    "reason": (request.get("control") or {}).get("captured_reason"),
                    "result_source": "captured_natural_control",
                },
                candidate_runner=lambda request: quality.execute_openai_prompt_v2_candidate(
                    request, timeout_sec=timeout_sec
                ),
                max_workers=workers,
            )
        coverage_report = coverage.build_report(
            target_date=target_date,
            stage="holding",
            dates=[target_date],
            requested_max_rows=max(1, limit),
            source_summary=source_summary,
            requests=requests,
            results=results,
        )
        economics = _holding_economics(
            requests=requests, results=results, labels=labels
        )
        body = {
            "schema": REPORT_SCHEMA,
            "target_date": target_date,
            "generated_at": datetime.now(quality.KST).isoformat(),
            "stage": "holding",
            "effective_venue": cohort[0],
            "session_bucket": cohort[1],
            "status": (
                "completed_offline_only"
                if economics["status"] == "complete"
                else "keep_collecting"
            ),
            "candidate_prompt_version": DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION,
            "candidate_prompt_sha256": quality._sha256(
                decision_quality_holding_v2_4_live_score_system_prompt()
            ),
            "request_count": len(requests),
            "result_count": len(results),
            "pass_count": sum(row.get("status") == "pass" for row in results),
            "provider_failed_count": sum(
                row.get("status") == "provider_failed" for row in results
            ),
            "schema_rejected_count": sum(
                row.get("status") == "schema_rejected" for row in results
            ),
            "coverage_report": coverage_report,
            "holding_cost_adjusted_economics": economics,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        report = {**body, "artifact_content_sha256": _canonical_sha256(body)}
        if write:
            _write_json(path, report)
        cohort_results.append(
            {"cohort": "/".join(cohort), "status": report["status"], "path": str(path)}
        )
    candidate_results = []
    for cohort in SUPPORTED_COHORTS:
        candidate = build_candidate(target_date, cohort)
        path = candidate_path(target_date, cohort)
        if write:
            _write_json(path, candidate)
        candidate_results.append(
            {
                "cohort": "/".join(cohort),
                "status": candidate["status"],
                "path": str(path),
            }
        )
    return {
        "schema": "holding_prompt_postclose_batch_v1",
        "target_date": target_date,
        "status": "completed_offline_only",
        "provider_call_limit": max_new_total,
        "provider_new_call_count": provider_new_call_count,
        "provider_call_performed": provider_new_call_count > 0,
        "cohorts": cohort_results,
        "candidates": candidate_results,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }


def build_activation(target_date: str, cohort: tuple[str, str]) -> dict[str, Any]:
    venue, session = _cohort(cohort)
    matching: list[tuple[str, Path, dict[str, Any]]] = []
    for path in CANDIDATE_DIR.glob(
        f"holding_prompt_live_candidate_*_{_slug(venue)}_{_slug(session)}.json"
    ):
        candidate = _read_json(path)
        if candidate.get("effective_date") == target_date:
            matching.append((str(candidate.get("source_date") or ""), path, candidate))
    matching.sort(key=lambda item: item[0], reverse=True)
    source_date, path, candidate = matching[0] if matching else (None, None, {})
    errors: list[str] = []
    expected_hash = candidate.get("artifact_sha256")
    if not candidate:
        errors.append("holding_prompt_candidate_missing")
    elif expected_hash != _canonical_sha256(
        {key: value for key, value in candidate.items() if key != "artifact_sha256"}
    ):
        errors.append("holding_prompt_candidate_hash_invalid")
    if (
        candidate.get("schema") != CANDIDATE_SCHEMA
        or candidate.get("status") != "preopen_apply_ready"
    ):
        errors.append("holding_prompt_candidate_not_ready")
    if candidate.get("allowed_runtime_apply") is not True:
        errors.append("holding_prompt_candidate_runtime_apply_not_allowed")
    if (
        candidate.get("effective_venue") != venue
        or candidate.get("session_bucket") != session
    ):
        errors.append("holding_prompt_candidate_cohort_mismatch")
    if candidate.get("selected_prompt_sha256") != quality._sha256(
        decision_quality_holding_v2_4_live_score_system_prompt()
    ):
        errors.append("holding_prompt_candidate_prompt_hash_mismatch")
    errors = list(dict.fromkeys(errors))
    body = {
        "schema": ACTIVATION_SCHEMA,
        "target_date": target_date,
        "source_date": source_date,
        "effective_venue": venue,
        "session_bucket": session,
        "status": "active" if not errors else "fallback_holding_score_v2",
        "selected_prompt_version": (
            DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION
            if not errors
            else FALLBACK_PROMPT_VERSION
        ),
        "selected_prompt_sha256": (
            candidate.get("selected_prompt_sha256") if not errors else None
        ),
        "response_schema": PROMPT_SCHEMA_NAME if not errors else "holding_score_v2",
        "rollback_prompt_version": FALLBACK_PROMPT_VERSION,
        "candidate_path": str(path) if path else None,
        "candidate_file_sha256": _file_sha256(path) if path else None,
        "candidate_artifact_sha256": expected_hash if not errors else None,
        "blocking_reasons": errors,
        "runtime_effect": not errors,
        "actual_order_submitted": False,
        "hard_safety_unchanged": True,
    }
    return {**body, "artifact_sha256": _canonical_sha256(body)}


def resolve_holding_prompt_policy(
    *, effective_venue: Any, session_bucket: Any, now: datetime | None = None
) -> dict[str, Any]:
    current = (now or datetime.now(quality.KST)).astimezone(quality.KST)
    cohort = _cohort((effective_venue, session_bucket))
    fallback = {
        "enabled": False,
        "status": "fallback_holding_score_v2",
        "selected_prompt_version": FALLBACK_PROMPT_VERSION,
        "response_schema": "holding_score_v2",
        "runtime_effect": False,
    }
    if cohort not in SUPPORTED_COHORTS:
        return {**fallback, "reason": "holding_prompt_cohort_not_registered"}
    path = activation_path(current.date().isoformat(), cohort)
    cache_key = (current.date().isoformat(), cohort[0], cohort[1])
    activation_signature = _file_signature(path)
    with _POLICY_CACHE_LOCK:
        cached = _POLICY_CACHE.get(cache_key)
    if cached and cached.get("activation_signature") == activation_signature:
        cached_candidate_path = Path(str(cached.get("candidate_path") or ""))
        if cached.get("candidate_signature") == _file_signature(cached_candidate_path):
            return dict(cached["result"])
    activation = _read_json(path)
    if activation.get("artifact_sha256") != _canonical_sha256(
        {key: value for key, value in activation.items() if key != "artifact_sha256"}
    ):
        return {
            **fallback,
            "reason": "holding_prompt_activation_missing_or_invalid",
            "activation_path": str(path),
        }
    if (
        activation.get("schema") != ACTIVATION_SCHEMA
        or activation.get("target_date") != current.date().isoformat()
        or activation.get("status") != "active"
        or activation.get("effective_venue") != cohort[0]
        or activation.get("session_bucket") != cohort[1]
        or activation.get("selected_prompt_version")
        != DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION
        or activation.get("selected_prompt_sha256")
        != quality._sha256(decision_quality_holding_v2_4_live_score_system_prompt())
        or activation.get("response_schema") != PROMPT_SCHEMA_NAME
        or activation.get("hard_safety_unchanged") is not True
    ):
        return {
            **fallback,
            "reason": "holding_prompt_activation_contract_invalid",
            "activation_path": str(path),
        }
    candidate_raw_path = activation.get("candidate_path")
    candidate_file = Path(str(candidate_raw_path or ""))
    candidate = _read_json(candidate_file) if candidate_raw_path else {}
    expected_candidate_file = candidate_path(
        str(activation.get("source_date") or ""),
        cohort,
    )
    if (
        not candidate
        or candidate_file != expected_candidate_file
        or _file_sha256(candidate_file) != activation.get("candidate_file_sha256")
        or candidate.get("artifact_sha256")
        != activation.get("candidate_artifact_sha256")
        or candidate.get("artifact_sha256")
        != _canonical_sha256(
            {key: value for key, value in candidate.items() if key != "artifact_sha256"}
        )
        or candidate.get("schema") != CANDIDATE_SCHEMA
        or candidate.get("source_date") != activation.get("source_date")
        or candidate.get("effective_date") != current.date().isoformat()
        or candidate.get("effective_venue") != cohort[0]
        or candidate.get("session_bucket") != cohort[1]
        or candidate.get("status") != "preopen_apply_ready"
        or candidate.get("allowed_runtime_apply") is not True
        or candidate.get("selected_prompt_version")
        != DECISION_QUALITY_HOLDING_V2_4_LIVE_SCORE_PROMPT_VERSION
        or candidate.get("selected_prompt_sha256")
        != activation.get("selected_prompt_sha256")
        or candidate.get("selected_response_schema") != PROMPT_SCHEMA_NAME
    ):
        result = {
            **fallback,
            "reason": "holding_prompt_candidate_contract_invalid",
            "activation_path": str(path),
        }
    else:
        result = {
            "enabled": True,
            "status": "active_exact_date_holding_prompt",
            "selected_prompt_version": activation["selected_prompt_version"],
            "selected_prompt_sha256": activation["selected_prompt_sha256"],
            "response_schema": PROMPT_SCHEMA_NAME,
            "activation_path": str(path),
            "activation_artifact_sha256": activation["artifact_sha256"],
            "runtime_effect": True,
        }
    with _POLICY_CACHE_LOCK:
        _POLICY_CACHE[cache_key] = {
            "activation_signature": activation_signature,
            "candidate_path": str(candidate_file),
            "candidate_signature": _file_signature(candidate_file),
            "result": dict(result),
        }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("postclose", "preopen"), required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--execute-candidate", action="store_true")
    parser.add_argument("--max-new-total", type=int, default=10)
    parser.add_argument("--candidate-workers", type=int, default=2)
    parser.add_argument("--candidate-timeout-sec", type=float, default=45.0)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.max_new_total < 0 or args.candidate_workers <= 0:
        parser.error("provider bounds must be nonnegative and workers positive")
    if args.execute_candidate and (args.phase != "postclose" or not args.write):
        parser.error("--execute-candidate requires --phase postclose --write")
    if args.phase == "postclose":
        result = run_postclose(
            args.target_date,
            execute_candidate=args.execute_candidate,
            max_new_total=args.max_new_total,
            workers=args.candidate_workers,
            timeout_sec=args.candidate_timeout_sec,
            write=args.write,
        )
    else:
        activations = []
        for cohort in SUPPORTED_COHORTS:
            activation = build_activation(args.target_date, cohort)
            path = activation_path(args.target_date, cohort)
            if args.write:
                _write_json(path, activation)
            activations.append(
                {
                    "cohort": "/".join(cohort),
                    "status": activation["status"],
                    "path": str(path),
                }
            )
        result = {
            "schema": "holding_prompt_preopen_batch_v1",
            "target_date": args.target_date,
            "status": "completed",
            "activations": activations,
            "actual_order_submitted": False,
        }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
