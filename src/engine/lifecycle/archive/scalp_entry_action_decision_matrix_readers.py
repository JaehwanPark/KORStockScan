"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy
from src.engine.scalping.entry_adm_bucket_contract import (
    ENTRY_ADM_BUCKET_DIMENSIONS,
    entry_adm_bucket_token,
)
from src.engine.scalping.entry_observation_events import (
    SCORE_CONTEXT_NOT_AVAILABLE_STAGES,
    SCORE_SOURCE_FIELDS,
    _iter_jsonl,
    _nonempty,
    _open_text,
    _safe_float,
    _safe_int,
)
from src.utils.jsonl_io import existing_or_gzip_path

PROJECT_ROOT = Path(__file__).resolve().parents[4]


DATA_DIR = PROJECT_ROOT / "data"


REPORT_DIR = DATA_DIR / "report"


ADM_REPORT_DIR = REPORT_DIR / "scalp_entry_action_decision_matrix"


POST_SELL_DIR = DATA_DIR / "post_sell"


SAMPLE_FLOOR = 20


SKIP_FOLLOWUP_SAMPLE_FLOOR = 20


NON_ENTRY_ADM_DIAGNOSTIC_STAGES = frozenset(SCORE_CONTEXT_NOT_AVAILABLE_STAGES)


def _load_sim_evaluations(
    target_date: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = existing_or_gzip_path(
        POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl"
    )
    by_key: dict[str, dict[str, Any]] = {}
    total = 0
    joined_keys: set[str] = set()
    if not path.exists():
        return by_key, {"artifact": None, "rows": 0, "join_keys": 0}
    for item in _iter_jsonl(path, filter_entry_tokens=False):
        total += 1
        item = dict(item)
        item["_post_sell_evaluation_id"] = (
            _nonempty(item.get("post_sell_id"))
            or _nonempty(item.get("sim_record_id"))
            or _nonempty(item.get("entry_adm_candidate_id"))
            or _nonempty(item.get("candidate_id"))
            or f"evaluation-row-{total}"
        )
        for key in (
            _nonempty(item.get("candidate_id")),
            _nonempty(item.get("entry_adm_candidate_id")),
            _nonempty(item.get("sim_record_id")),
        ):
            if key:
                by_key[key] = item
                joined_keys.add(key)
    return by_key, {"artifact": str(path), "rows": total, "join_keys": len(joined_keys)}


def _classify_adm_lookup_not_applicable(rows: list[dict[str, Any]]) -> None:
    advisory_only_stages = {"ai_confirmed", "blocked_ai_score"}
    for row in rows:
        existing = str(row.get("entry_adm_bucket_lookup_status") or "").strip()
        if existing and existing not in {"-", "None"}:
            continue
        if str(row.get("stage") or "") not in advisory_only_stages:
            continue
        if not row.get("entry_adm_bucket_token_recomputed") and not row.get(
            "entry_adm_bucket_token"
        ):
            continue
        row["entry_adm_bucket_lookup_status"] = (
            "advisory_only_stage_without_prior_lookup"
        )
        row["entry_adm_bucket_lookup_not_applicable_reason"] = (
            "adm_prompt_context_stage_without_prior_bucket_lookup"
        )
        row["entry_adm_bucket_sample_count"] = 0
        row["entry_adm_bucket_joined_sample"] = 0


def _adm_lookup_closure_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    producer_context_missing_counts: Counter[str] = Counter()
    for row in rows:
        status = str(row.get("entry_adm_bucket_lookup_status") or "").strip()
        if status != "new_or_unseen_token_vs_prior_adm":
            continue
        token = str(
            row.get("entry_adm_bucket_token_recomputed")
            or row.get("entry_adm_bucket_token")
            or ""
        )
        stage = str(row.get("stage") or "-")
        stage_counts[stage] += 1
        missing_contexts = []
        if "risk_context_not_available" in token:
            missing_contexts.append("risk_context_not_available")
        if "price_not_available_pre_submit" in token:
            missing_contexts.append("price_not_available_pre_submit")
        if "liquidity_not_available" in token:
            missing_contexts.append("liquidity_not_available")
        if missing_contexts:
            status_counts["producer_context_missing"] += 1
            for context in missing_contexts:
                producer_context_missing_counts[context] += 1
        elif stage in {"ai_confirmed", "blocked_ai_score"}:
            status_counts["advisory_or_not_applicable_stage"] += 1
        else:
            status_counts["new_bucket_candidate_waiting_prior_rollup"] += 1
    total = sum(status_counts.values())
    followup_required = status_counts.get("producer_context_missing", 0) > 0
    return {
        "new_or_unseen_total": total,
        "closure_status": (
            "closed_with_producer_followup" if followup_required else "closed"
        ),
        "followup_required": followup_required,
        "status_counts": dict(status_counts),
        "producer_context_missing_counts": dict(producer_context_missing_counts),
        "top_stages": [[stage, count] for stage, count in stage_counts.most_common(10)],
        "decision_authority": "entry_adm_lookup_closure_diagnostic_only",
        "runtime_effect": False,
    }


def _outcome_join_diagnostic(
    *,
    rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    evaluations: dict[str, dict[str, Any]],
    eval_summary: dict[str, Any],
) -> dict[str, Any]:
    candidate_keys_by_field: dict[str, set[str]] = {
        "candidate_id": set(),
        "entry_adm_candidate_id": set(),
        "sim_record_id": set(),
        "record_id": set(),
    }
    for row in rows:
        for field, keys in candidate_keys_by_field.items():
            value = str(row.get(field) or "").strip()
            if value:
                keys.add(value)
    candidate_keys = set().union(*candidate_keys_by_field.values())
    evaluation_keys = {
        str(key or "").strip() for key in evaluations.keys() if str(key or "").strip()
    }
    overlap_keys = candidate_keys & evaluation_keys
    sim_eligible_rows = [
        row for row in aggregate_rows if str(row.get("sim_record_id") or "").strip()
    ]
    sim_eligible_keys = {
        str(value).strip()
        for row in sim_eligible_rows
        for value in (row.get("candidate_id"), row.get("sim_record_id"))
        if str(value or "").strip()
    }
    evaluation_join_candidate_keys = {
        str(value).strip()
        for row in aggregate_rows
        for value in (row.get("candidate_id"), row.get("sim_record_id"))
        if str(value or "").strip()
    }
    relevant_evaluation_object_ids = {
        id(evaluation)
        for key, evaluation in evaluations.items()
        if key in evaluation_join_candidate_keys
    }
    joined_evaluation_object_ids = {
        id(evaluations[key])
        for row in aggregate_rows
        if row.get("outcome_joined")
        for key in (
            str(row.get("candidate_id") or "").strip(),
            str(row.get("sim_record_id") or "").strip(),
        )
        if key and key in evaluations
    }
    aggregate_joined_sample = sum(
        1 for row in aggregate_rows if row.get("outcome_joined")
    )
    sim_eligible_joined_sample = sum(
        1 for row in sim_eligible_rows if row.get("outcome_joined")
    )
    joined_sample_all_rows = sum(1 for row in rows if row.get("outcome_joined"))
    post_sell_rows = _safe_int(eval_summary.get("rows"), 0)
    join_keys = _safe_int(eval_summary.get("join_keys"), len(evaluation_keys))
    relevant_evaluation_rows = len(relevant_evaluation_object_ids)
    matched_evaluation_rows = len(
        relevant_evaluation_object_ids & joined_evaluation_object_ids
    )
    unmatched_relevant_evaluation_rows = len(
        relevant_evaluation_object_ids - joined_evaluation_object_ids
    )
    non_entry_or_unmatched_evaluation_rows = max(
        0, post_sell_rows - relevant_evaluation_rows
    )
    if not sim_eligible_rows:
        coverage_state = "no_sim_outcome_eligible_candidates"
        coverage_reason = "entry_adm_rows_have_no_sim_record_id"
    elif post_sell_rows <= 0:
        coverage_state = "post_sell_source_missing"
        coverage_reason = "no_sim_post_sell_evaluation_rows_for_target_date"
    elif unmatched_relevant_evaluation_rows > 0:
        coverage_state = "join_contract_gap"
        coverage_reason = (
            "some_entry_adm_relevant_post_sell_evaluations_did_not_join_eligible_rows"
        )
    elif relevant_evaluation_rows < SAMPLE_FLOOR:
        coverage_state = "source_outcome_underproduction"
        coverage_reason = "entry_adm_relevant_sim_post_sell_evaluation_underproduction"
    elif sim_eligible_joined_sample < SAMPLE_FLOOR:
        coverage_state = "eligible_outcome_coverage_below_sample_floor"
        coverage_reason = "sim_eligible_rows_outnumber_mature_post_sell_outcomes"
    else:
        coverage_state = "sufficient"
        coverage_reason = "sim_outcome_source_and_join_coverage_meet_sample_floor"
    if aggregate_joined_sample > 0:
        status = "joined"
        reason = "post_sell_outcome_join_available"
    elif not rows:
        status = "no_entry_adm_candidates"
        reason = "no_relevant_entry_adm_events"
    elif post_sell_rows <= 0 or join_keys <= 0:
        status = "post_sell_evaluation_missing_or_empty"
        reason = "no_post_sell_evaluation_rows_for_target_date"
    elif not candidate_keys:
        status = "candidate_join_keys_missing"
        reason = "entry_adm_rows_have_no_candidate_or_sim_record_join_key"
    elif not overlap_keys:
        status = "no_candidate_key_overlap"
        reason = "entry_adm_candidate_keys_do_not_overlap_post_sell_evaluation_keys"
    else:
        status = "overlap_present_but_unjoined"
        reason = "candidate_keys_overlap_but_rows_did_not_mark_outcome_joined"
    return {
        "status": status,
        "zero_join_reason": reason if aggregate_joined_sample <= 0 else "",
        "candidate_key_count": len(candidate_keys),
        "candidate_key_field_counts": {
            field: len(values) for field, values in candidate_keys_by_field.items()
        },
        "post_sell_evaluation_rows": post_sell_rows,
        "post_sell_evaluation_join_keys": join_keys,
        "entry_adm_relevant_post_sell_evaluation_rows": relevant_evaluation_rows,
        "non_entry_or_unmatched_post_sell_evaluation_rows": (
            non_entry_or_unmatched_evaluation_rows
        ),
        "unmatched_entry_adm_relevant_post_sell_evaluation_rows": (
            unmatched_relevant_evaluation_rows
        ),
        "sim_outcome_eligible_rows": len(sim_eligible_rows),
        "sim_outcome_eligible_key_count": len(sim_eligible_keys),
        "sim_eligible_joined_sample": sim_eligible_joined_sample,
        "sim_eligible_outcome_coverage_rate": (
            round(sim_eligible_joined_sample / len(sim_eligible_rows), 4)
            if sim_eligible_rows
            else None
        ),
        "matched_post_sell_evaluation_rows": matched_evaluation_rows,
        "post_sell_evaluation_match_rate": (
            round(matched_evaluation_rows / relevant_evaluation_rows, 4)
            if relevant_evaluation_rows > 0
            else None
        ),
        "entry_adm_relevant_rate_of_all_post_sell_evaluations": (
            round(relevant_evaluation_rows / post_sell_rows, 4)
            if post_sell_rows > 0
            else None
        ),
        "coverage_state": coverage_state,
        "coverage_reason": coverage_reason,
        "candidate_post_sell_key_overlap_count": len(overlap_keys),
        "joined_sample": aggregate_joined_sample,
        "joined_sample_all_rows": joined_sample_all_rows,
        "sample_floor": SAMPLE_FLOOR,
        "sample_floor_met": aggregate_joined_sample >= SAMPLE_FLOOR,
        "decision_authority": "source_quality_gap_discovery",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _is_numeric_consistency_excluded_row(row: dict[str, Any]) -> bool:
    if bool(row.get("ai_reason_numeric_inconsistency")):
        return True
    return (
        str(row.get("source_quality_gate") or "").strip()
        == "ai_numeric_consistency_review_required"
    )


def _is_entry_adm_aggregate_row(row: dict[str, Any]) -> bool:
    return (
        not _is_numeric_consistency_excluded_row(row)
        and str(row.get("stage") or "") not in NON_ENTRY_ADM_DIAGNOSTIC_STAGES
    )


def _load_prior_entry_price_skip_rows(
    target_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    policy = clean_baseline_policy()
    baseline_date = str(
        policy.get("clean_tuning_baseline_date") or "2026-06-05"
    ).strip()
    rows: list[dict[str, Any]] = []
    source_dates: list[str] = []
    source_artifacts: list[str] = []
    excluded_artifacts: list[dict[str, str]] = []
    selected_paths: dict[str, Path] = {}

    for path in sorted(
        ADM_REPORT_DIR.glob("scalp_entry_action_decision_matrix_*.json*")
    ):
        name = path.name
        prefix = "scalp_entry_action_decision_matrix_"
        source_date = name[len(prefix) : len(prefix) + 10]
        try:
            source_dt = date.fromisoformat(source_date)
            target_dt = date.fromisoformat(target_date)
            baseline_dt = date.fromisoformat(baseline_date)
        except ValueError:
            excluded_artifacts.append(
                {"artifact": str(path), "reason": "invalid_artifact_date"}
            )
            continue
        if not (baseline_dt <= source_dt < target_dt):
            continue
        current = selected_paths.get(source_date)
        if current is None or (current.suffix == ".gz" and path.suffix != ".gz"):
            selected_paths[source_date] = path

    for source_date, path in sorted(selected_paths.items()):
        try:
            with _open_text(path) as handle:
                payload = json.loads(handle.read())
        except Exception as exc:
            excluded_artifacts.append(
                {
                    "artifact": str(path),
                    "reason": f"unreadable_or_invalid_json:{type(exc).__name__}",
                }
            )
            continue
        report_rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(report_rows, list):
            excluded_artifacts.append(
                {"artifact": str(path), "reason": "rows_missing_or_invalid"}
            )
            continue
        source_dates.append(source_date)
        source_artifacts.append(str(path))
        for row in report_rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("stage") or "") not in {
                "scalp_sim_entry_ai_price_skip_order",
                "scalp_sim_entry_mechanistic_price_skip_order",
            }:
                continue
            copied = dict(row)
            copied["_cumulative_source_date"] = source_date
            rows.append(copied)

    return rows, {
        "clean_tuning_baseline_date": baseline_date,
        "source_dates": source_dates,
        "source_date_count": len(source_dates),
        "source_artifacts": source_artifacts,
        "source_artifact_count": len(source_artifacts),
        "excluded_artifacts": excluded_artifacts,
        "excluded_artifact_count": len(excluded_artifacts),
    }


def _finite_followup_value(
    row: dict[str, Any], prefix: str, suffix: str
) -> float | None:
    value = _safe_float(row.get(f"{prefix}_{suffix}"), None)
    if value is None or not math.isfinite(float(value)):
        return None
    return float(value)


def _entry_price_skip_followup_cumulative_summary(
    target_date: str, current_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    prior_rows, provenance = _load_prior_entry_price_skip_rows(target_date)
    baseline_date = str(provenance.get("clean_tuning_baseline_date") or "2026-06-05")
    try:
        target_allowed = date.fromisoformat(target_date) >= date.fromisoformat(
            baseline_date
        )
    except ValueError:
        target_allowed = False
    cumulative_rows = list(prior_rows)
    for row in current_rows if target_allowed else []:
        if str(row.get("stage") or "") not in {
            "scalp_sim_entry_ai_price_skip_order",
            "scalp_sim_entry_mechanistic_price_skip_order",
        }:
            continue
        copied = dict(row)
        copied["_cumulative_source_date"] = target_date
        cumulative_rows.append(copied)

    deduped: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(cumulative_rows):
        source_date = str(row.get("_cumulative_source_date") or target_date)
        lineage = next(
            (
                _nonempty(row.get(field))
                for field in (
                    "sim_record_id",
                    "candidate_id",
                    "record_id",
                    "sim_parent_record_id",
                )
                if _nonempty(row.get(field))
            ),
            "",
        )
        key = "|".join(
            [
                source_date,
                _nonempty(row.get("stock_code")),
                lineage or f"row-{index}",
            ]
        )
        deduped[key] = row

    interval_summary: dict[str, dict[str, Any]] = {}
    for interval in (30, 90):
        prefix = f"entry_price_skip_followup_{interval}s"
        paired = [
            row
            for row in deduped.values()
            if _finite_followup_value(row, prefix, "mfe_bps") is not None
            and _finite_followup_value(row, prefix, "mae_bps") is not None
        ]
        mfe_values = [
            float(_finite_followup_value(row, prefix, "mfe_bps") or 0.0)
            for row in paired
        ]
        mae_values = [
            float(_finite_followup_value(row, prefix, "mae_bps") or 0.0)
            for row in paired
        ]
        interval_summary[f"{interval}s"] = {
            "mature_paired_sample_count": len(paired),
            "equal_weight_avg_mfe_bps": (
                round(sum(mfe_values) / len(mfe_values), 4) if mfe_values else None
            ),
            "equal_weight_avg_mae_bps": (
                round(sum(mae_values) / len(mae_values), 4) if mae_values else None
            ),
        }

    primary_sample = int(interval_summary["90s"].get("mature_paired_sample_count") or 0)
    sample_floor_met = bool(
        target_allowed and primary_sample >= SKIP_FOLLOWUP_SAMPLE_FLOOR
    )
    observed_dates = sorted(
        {
            str(row.get("_cumulative_source_date") or "")
            for row in deduped.values()
            if any(
                _finite_followup_value(
                    row,
                    f"entry_price_skip_followup_{interval}s",
                    "mfe_bps",
                )
                is not None
                for interval in (30, 90)
            )
        }
        - {""}
    )
    return {
        "status": (
            "source_quality_blocked_pre_clean_baseline"
            if not target_allowed
            else (
                "ready_for_offline_counterfactual_review"
                if sample_floor_met
                else "collecting_mature_followups"
            )
        ),
        "metric_role": "counterfactual_opportunity_diagnostic",
        "decision_authority": "report_only_counterfactual_quality_review",
        "window_policy": "clean_baseline_cumulative_through_target_date",
        "sample_floor": SKIP_FOLLOWUP_SAMPLE_FLOOR,
        "sample_floor_basis": "mature_paired_90s_followups",
        "sample_floor_met": sample_floor_met,
        "primary_decision_metric": "paired_90s_mfe_mae_bps_diagnostic",
        "source_quality_gate": (
            "exact same-symbol lineage join with finite paired MFE/MAE and "
            "clean-baseline daily ADM artifact"
        ),
        "forbidden_uses": [
            "treat_counterfactual_mfe_as_realized_pnl_or_ev",
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "real_execution_quality_approval",
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "max_runtime_apply_count": 0,
        "candidate_count": len(deduped),
        "observed_dates": observed_dates,
        "observed_date_count": len(observed_dates),
        "intervals": interval_summary,
        "provenance": {
            **provenance,
            "target_date_in_memory": target_date,
            "target_date_allowed": target_allowed,
            "target_date_row_count": sum(
                1
                for row in current_rows
                if target_allowed
                if str(row.get("stage") or "")
                in {
                    "scalp_sim_entry_ai_price_skip_order",
                    "scalp_sim_entry_mechanistic_price_skip_order",
                }
            ),
        },
    }


def _joined_sample_cumulative_summary(
    target_date: str, current_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Count mature ADM outcome joins across the clean-baseline window.

    Daily rows remain the diagnostic owner for today's coverage.  Runtime and
    pattern-lab sample-floor decisions use this exact-lineage cumulative view
    so a quiet session cannot erase already mature clean-baseline evidence.
    """

    policy = clean_baseline_policy()
    baseline_date = str(
        policy.get("clean_tuning_baseline_date") or "2026-06-05"
    ).strip()
    try:
        baseline_dt = date.fromisoformat(baseline_date)
        target_dt = date.fromisoformat(target_date)
    except ValueError:
        return {
            "status": "invalid_date_contract",
            "window_policy": "clean_baseline_cumulative_through_target_date",
            "sample_floor": SAMPLE_FLOOR,
            "sample_count": 0,
            "sample_floor_met": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "invalid_date_contract",
        }

    selected_paths: dict[str, Path] = {}
    excluded_artifacts: list[dict[str, str]] = []
    for path in sorted(
        ADM_REPORT_DIR.glob("scalp_entry_action_decision_matrix_*.json*")
    ):
        source_date = path.name[
            len("scalp_entry_action_decision_matrix_") : len(
                "scalp_entry_action_decision_matrix_"
            )
            + 10
        ]
        try:
            source_dt = date.fromisoformat(source_date)
        except ValueError:
            excluded_artifacts.append(
                {"artifact": str(path), "reason": "invalid_artifact_date"}
            )
            continue
        if not (baseline_dt <= source_dt < target_dt):
            continue
        current = selected_paths.get(source_date)
        if current is None or (current.suffix == ".gz" and path.suffix != ".gz"):
            selected_paths[source_date] = path

    rows_by_identity: dict[str, dict[str, Any]] = {}
    source_artifacts: list[str] = []

    def observe_rows(source_date: str, rows: Any) -> None:
        if not isinstance(rows, list):
            return
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not row.get("outcome_joined"):
                continue
            if not _is_entry_adm_aggregate_row(row):
                continue
            profit = _safe_float(row.get("profit_rate"), None)
            if profit is None or not math.isfinite(float(profit)):
                continue
            if _is_numeric_consistency_excluded_row(row):
                continue
            lineage = next(
                (
                    _nonempty(row.get(field))
                    for field in (
                        "post_sell_evaluation_id",
                        "sim_record_id",
                        "candidate_id",
                        "record_id",
                        "sim_parent_record_id",
                    )
                    if _nonempty(row.get(field))
                ),
                "",
            )
            identity = "|".join(
                (
                    source_date,
                    _nonempty(row.get("stock_code")),
                    lineage or f"row-{index}",
                )
            )
            copied = dict(row)
            copied["_cumulative_source_date"] = source_date
            rows_by_identity[identity] = copied

    for source_date, path in sorted(selected_paths.items()):
        try:
            with _open_text(path) as handle:
                payload = json.loads(handle.read())
        except Exception as exc:
            excluded_artifacts.append(
                {
                    "artifact": str(path),
                    "reason": f"unreadable_or_invalid_json:{type(exc).__name__}",
                }
            )
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
            excluded_artifacts.append(
                {"artifact": str(path), "reason": "rows_missing_or_invalid"}
            )
            continue
        source_artifacts.append(str(path))
        observe_rows(source_date, payload.get("rows"))

    if baseline_dt <= target_dt:
        observe_rows(target_date, current_rows)

    observed_dates = sorted(
        {
            str(row.get("_cumulative_source_date") or "")
            for row in rows_by_identity.values()
        }
        - {""}
    )
    sample_count = len(rows_by_identity)
    return {
        "status": "ready" if sample_count >= SAMPLE_FLOOR else "collecting",
        "metric_role": "entry_adm_joined_outcome_sample_floor",
        "decision_authority": "report_and_pattern_lab_source_quality_only",
        "window_policy": "clean_baseline_cumulative_through_target_date",
        "clean_tuning_baseline_date": baseline_date,
        "sample_floor": SAMPLE_FLOOR,
        "sample_count": sample_count,
        "sample_floor_met": sample_count >= SAMPLE_FLOOR,
        "observed_dates": observed_dates,
        "observed_date_count": len(observed_dates),
        "source_artifacts": source_artifacts,
        "source_artifact_count": len(source_artifacts),
        "excluded_artifacts": excluded_artifacts,
        "excluded_artifact_count": len(excluded_artifacts),
        "source_quality_gate": (
            "finite outcome_joined rows after numeric-consistency exclusion, "
            "excluding terminal-only diagnostic stages and deduped by source "
            "date plus exact post-sell/simulator/candidate lineage"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "single_daily_sample_as_live_authority",
            "direct_order_or_threshold_mutation",
            "pre_clean_baseline_tuning",
        ],
    }


def _is_not_available_bucket(value: str) -> bool:
    return "not_available" in str(value or "").lower()


def _is_unknown_bucket(value: str) -> bool:
    compact = str(value or "").lower()
    return "unknown" in compact and "not_available" not in compact


def _context_unknown_reason(
    row: dict[str, Any], key: str, provenance_value: str
) -> str:
    stage = str(row.get("stage") or "").strip()
    if stage and stage not in {"scalp_entry_action_decision_snapshot", "entry"}:
        return "post_submit_or_exit_not_required"
    if provenance_value == "adm_field":
        return "producer_context_missing"
    if key == "risk_context_bucket":
        context_values = [
            row.get("risk_regime_mode"),
            row.get("panic_regime_mode"),
        ]
        return (
            "source_field_missing"
            if not any(v not in (None, "") for v in context_values)
            else "backfilled"
        )
    if key == "price_resolution_bucket":
        price_values = [
            row.get("order_price"),
            row.get("curr_price"),
            row.get("current_price"),
            row.get("best_bid"),
            row.get("best_ask"),
        ]
        return (
            "source_field_missing"
            if not any(v not in (None, "") for v in price_values)
            else "backfilled"
        )
    return "source_field_missing"


def _unknown_bucket_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = ENTRY_ADM_BUCKET_DIMENSIONS
    total = len(rows)
    dimension_counts: dict[str, int] = {}
    not_available_counts: dict[str, int] = {}
    unknown_affected_row_count = 0
    not_available_affected_row_count = 0
    stage_counts: Counter[str] = Counter()
    unknown_root_causes: Counter[str] = Counter()
    unknown_root_cause_detail_counts: Counter[str] = Counter()
    unknown_resolution_route_counts: Counter[str] = Counter()
    score_root_cause_counts: Counter[str] = Counter()
    score_backfill_match_type_counts: Counter[str] = Counter()
    score_source_missing_examples: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    adm_source_count = 0
    raw_recomputed_count = 0
    adm_source_total = 0
    for row in rows:
        provenance = row.get("bucket_field_provenance")
        if isinstance(provenance, dict):
            adm_count = sum(1 for v in provenance.values() if v == "adm_field")
            raw_count = sum(1 for v in provenance.values() if v == "raw_recomputed")
            adm_source_total += adm_count
            raw_recomputed_count += raw_count
            if adm_count > 0:
                adm_source_count += 1
            if row.get("score_source_value") is not None and provenance.get(
                "score_bucket"
            ) in {"raw_recomputed", "backfilled"}:
                score_root_cause_counts["backfilled"] += 1
                if provenance.get("score_bucket") == "backfilled":
                    score_backfill_match_type_counts[
                        str(row.get("score_backfill_match_type") or "unknown")
                    ] += 1
        unknown_dimensions = [
            key for key in dimensions if _is_unknown_bucket(row.get(key) or "")
        ]
        not_available_dimensions = [
            key for key in dimensions if _is_not_available_bucket(row.get(key) or "")
        ]
        if not unknown_dimensions and not not_available_dimensions:
            continue
        if unknown_dimensions:
            unknown_affected_row_count += 1
        if not_available_dimensions:
            not_available_affected_row_count += 1
        for key in unknown_dimensions:
            dimension_counts[key] = dimension_counts.get(key, 0) + 1
            provenance_value = ""
            if isinstance(provenance, dict):
                provenance_value = str(provenance.get(key) or "")
            if provenance_value == "adm_field":
                unknown_root_causes[f"{key}:adm_field_unknown"] += 1
                if key == "score_bucket":
                    score_root_cause_counts["missing"] += 1
            elif key == "score_bucket" and row.get("score_source_value") is None:
                unknown_root_causes[f"{key}:source_score_missing"] += 1
                score_root_cause_counts["missing"] += 1
                if len(score_source_missing_examples) < 10:
                    score_source_missing_examples.append(
                        {
                            "stage": row.get("stage"),
                            "source_stage": row.get("source_stage"),
                            "stock_code": row.get("stock_code"),
                            "candidate_id": row.get("candidate_id"),
                            "record_id": row.get("record_id"),
                            "event_time": row.get("event_time"),
                            "source_path": row.get("source_path"),
                            "bucket_token": entry_adm_bucket_token(row),
                            "bucket_provenance": (
                                provenance if isinstance(provenance, dict) else None
                            ),
                            "expected_source_fields": list(SCORE_SOURCE_FIELDS),
                        }
                    )
            elif key == "risk_context_bucket":
                reason = _context_unknown_reason(row, key, provenance_value)
                unknown_root_causes[f"{key}:{reason}"] += 1
                unknown_root_cause_detail_counts[f"{key}:{reason}"] += 1
                unknown_resolution_route_counts[reason] += 1
            elif key == "price_resolution_bucket":
                reason = _context_unknown_reason(row, key, provenance_value)
                unknown_root_causes[f"{key}:{reason}"] += 1
                unknown_root_cause_detail_counts[f"{key}:{reason}"] += 1
                unknown_resolution_route_counts[reason] += 1
            else:
                unknown_root_causes[f"{key}:raw_recomputed_unknown"] += 1
                if key == "score_bucket":
                    score_root_cause_counts["missing"] += 1
        for key in not_available_dimensions:
            not_available_counts[key] = not_available_counts.get(key, 0) + 1
            if key == "score_bucket":
                score_root_cause_counts["not_applicable"] += 1
        stage_counts[str(row.get("stage") or "-")] += 1
        if len(examples) < 10:
            examples.append(
                {
                    "stage": row.get("stage"),
                    "stock_code": row.get("stock_code"),
                    "event_time": row.get("event_time"),
                    "unknown_dimensions": unknown_dimensions,
                    "not_available_dimensions": not_available_dimensions,
                    "bucket_token": entry_adm_bucket_token(row),
                    "bucket_provenance": (
                        provenance if isinstance(provenance, dict) else None
                    ),
                }
            )
    unknown_dimension_occurrence = sum(dimension_counts.values())
    not_available_dimension_occurrence = sum(not_available_counts.values())
    actionable_unknown_roots = {
        key: value
        for key, value in unknown_root_causes.items()
        if not key.endswith(":post_submit_or_exit_not_required")
        and not key.endswith(":backfilled")
    }
    unknown_source_quality_gate = (
        "source_quality_blocker"
        if actionable_unknown_roots
        else "classified_non_actionable" if unknown_affected_row_count else "pass"
    )
    unknown_recommended_route = (
        "source_quality_workorder"
        if actionable_unknown_roots
        else (
            "classified_not_applicable_no_workorder"
            if unknown_affected_row_count
            else "none"
        )
    )
    return {
        "affected_rows": unknown_affected_row_count,
        "not_available_affected_rows": not_available_affected_row_count,
        "unknown_dimension_occurrence_count": unknown_dimension_occurrence,
        "not_available_dimension_occurrence_count": not_available_dimension_occurrence,
        "total_rows": total,
        "affected_rate": round(unknown_affected_row_count / total, 4) if total else 0.0,
        "not_available_affected_rate": (
            round(not_available_affected_row_count / total, 4) if total else 0.0
        ),
        "dimension_counts": dimension_counts,
        "not_available_dimension_counts": not_available_counts,
        "stage_counts": dict(stage_counts),
        "unknown_root_cause_counts": dict(unknown_root_causes),
        "unknown_root_cause_detail_counts": dict(unknown_root_cause_detail_counts),
        "unknown_resolution_route_counts": dict(unknown_resolution_route_counts),
        "score_root_cause_counts": {
            "missing": score_root_cause_counts.get("missing", 0),
            "not_applicable": score_root_cause_counts.get("not_applicable", 0),
            "backfilled": score_root_cause_counts.get("backfilled", 0),
        },
        "score_backfill_match_type_counts": dict(score_backfill_match_type_counts),
        "score_source_missing_count": unknown_root_causes.get(
            "score_bucket:source_score_missing", 0
        ),
        "score_source_missing_examples": score_source_missing_examples,
        "score_source_missing_provenance": (
            {
                "gap": "score_bucket_source_score_missing",
                "expected_source_fields": list(SCORE_SOURCE_FIELDS),
                "recommended_resolution": "join_or_emit_entry_score_before_adm_bucket_decision",
                "decision_authority": "source_quality_gap_discovery",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
            if score_source_missing_examples
            else {}
        ),
        "examples": examples,
        "source_quality_gate": unknown_source_quality_gate,
        "recommended_route": unknown_recommended_route,
        "actionable_unknown_route_counts": dict(actionable_unknown_roots),
        "recomputed_unknown_count": raw_recomputed_count,
        "adm_source_bucket_used_count": adm_source_count,
        "adm_source_bucket_field_count": adm_source_total,
        "not_available_route": "field_legitimately_unavailable_no_workorder",
    }
