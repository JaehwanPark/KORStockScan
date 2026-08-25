"""Source-only entry diagnostics for natural WAIT/DROP lifecycle absences.

Actual R3 evidence requires a reconciled broker lifecycle.  That is the right
contract for realized execution quality, but a natural control WAIT or DROP
has no order lifecycle by design.  This module keeps those parents in a
separate, non-promotable diagnostic lane so missed-upside and trade-frequency
effects are observable without weakening the actual-lifecycle gate.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
import hashlib
import json
import math
import re
from statistics import fmean, median
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.market_day import is_krx_trading_day

from .replay_ablation_contract import (
    CURRENT_DESIGN_ACTIVATION_DATE,
    CURRENT_ARMS,
    CURRENT_DESIGN_VERSION,
    SOURCE_ONLY_AUTHORITY_CONTRACT,
)

KST = ZoneInfo("Asia/Seoul")

COUNTERFACTUAL_ENTRY_DIAGNOSTIC_SCHEMA = (
    "main_ai_quality_counterfactual_entry_r3_diagnostic_v1"
)
COUNTERFACTUAL_ENTRY_EXCLUSION_SCHEMA = (
    "main_ai_quality_counterfactual_entry_exclusion_v1"
)
COUNTERFACTUAL_ENTRY_INPUT_CENSUS_SCHEMA = (
    "main_ai_quality_counterfactual_entry_input_census_v1"
)
COUNTERFACTUAL_ENTRY_DIAGNOSTIC_AUTHORITY = (
    "postclose_source_only_counterfactual_entry_diagnostic"
)
WINDOW_TRADING_DAYS = (5, 10, 20)
MAX_PERSISTED_ARTIFACT_BYTES = 2 * 1024 * 1024
ARM_FIELDS = {
    "A": ("baseline_action", "baseline_ev_pct", "baseline_ev_basis"),
    "B": ("control_action", "control_ev_pct", "control_ev_basis"),
    "C": ("candidate_action", "candidate_ev_pct", "candidate_ev_basis"),
}
COMPARISONS = (
    ("feature_effect", "A", "B", "ask_liquidity_depletion_context_only"),
    ("prompt_effect", "B", "C", "prompt_and_response_contract_only"),
    (
        "composite_effect",
        "A",
        "C",
        "ask_liquidity_depletion_context_plus_prompt_response_contract",
    ),
)
ALLOWED_ENTRY_ACTIONS = frozenset({"BUY", "WAIT", "DROP"})
ALLOWED_EV_BASES = frozenset(
    {"full_exposure_ev_pct", "standardized_one_share_probe_ev_pct"}
)
ALLOWED_OUTCOME_EV_BASES = frozenset(
    {
        "source_quality_adjusted_ev_pct",
        "probe_cost_adjusted_ev_pct",
        "cost_adjusted_end_return_pct",
        "liquidity_adjusted_incremental_exit_value_pct",
        "net_return_pct",
    }
)
ALLOWED_FIRST_HIT = frozenset(
    {"net_target_first", "adverse_first", "none", "ambiguous_same_timestamp"}
)
ALLOWED_EXCLUSION_REASONS = frozenset(
    {
        "counterfactual_entry_contract_not_eligible",
        "economic_reference_not_verified",
        "source_quality_audit_not_pass",
    }
)
ALLOWED_CONTRACT_EXCLUSION_FINDINGS = frozenset(
    {
        "lifecycle_promotion_evidence_not_eligible",
        "lifecycle_invalid_transition",
        "lifecycle_session_exposure_nonpositive",
        "lifecycle_bbo_coverage_below_floor",
        "lifecycle_depth_coverage_below_floor",
        "lifecycle_reviewed_cost_hash_missing",
        "lifecycle_reviewed_cost_not_verified",
        "lifecycle_symbol_master_hash_missing",
        "lifecycle_symbol_master_not_verified",
        "daily_lifecycle_identity_binding_mismatch",
        "daily_lifecycle_trace_context_stage_invalid",
        "daily_lifecycle_trace_context_missing",
        "daily_lifecycle_trace_context_ambiguous",
        "daily_lifecycle_trace_context_invalid",
        "daily_lifecycle_trace_context_mismatch",
        "daily_economic_reference_binding_mismatch",
        "lifecycle_artifact_or_trace_invalid",
        "lifecycle_exact_join_missing",
    }
)
ALLOWED_LIFECYCLE_METRIC_MISSING_FIELDS = frozenset(
    {
        "actual_holding_duration_sec",
        "session_exposure_sec",
        "capital_time_krw_hours",
        "bbo_coverage_pct",
        "depth_coverage_pct",
    }
)

AUTHORITY_CONTRACT: dict[str, Any] = {
    "decision_authority": COUNTERFACTUAL_ENTRY_DIAGNOSTIC_AUTHORITY,
    **SOURCE_ONLY_AUTHORITY_CONTRACT,
    "promotion_authority": False,
    "runtime_candidate_eligible": False,
    "auto_apply_eligible": False,
    "actual_lifecycle_evidence": False,
    "counterfactual_only": True,
    "realized_profit_claim_allowed": False,
}

METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "counterfactual_entry_opportunity_diagnostic",
    "window_policy": (
        "last_5_10_20_available_clean_trading_dates_same_entry_venue_"
        "session_exact_three_arm_partition"
    ),
    "sample_floor": "diagnostic_census_only_no_promotion_floor",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "current_design_exact_provider_outcome_and_natural_control_wait_drop_"
        "sole_lifecycle_exact_join_missing"
    ),
    "forbidden_uses": [
        "merge_with_actual_lifecycle_r2_or_r3_candidates",
        "claim_realized_profit_or_execution_quality",
        "infer_fill_quantity_holding_time_session_exposure_or_capital_time",
        "live_sim_preopen_intraday_runtime_or_order_apply",
        "provider_threshold_prompt_quantity_cap_bot_or_safety_mutation",
        "cherry_pick_only_positive_or_action_changed_parents",
    ],
}

SOURCE_ROW_FIELDS = frozenset(
    {
        "target_date",
        "ablation_design_version",
        "tuning_axis",
        "paired_replay_parent_id",
        "decision_trace_id",
        "decision_stage",
        "effective_venue",
        "session_bucket",
        "stock_code",
        "captured_control_action",
        "lifecycle_findings",
        "baseline_action",
        "control_action",
        "candidate_action",
        "baseline_ev_pct",
        "baseline_ev_basis",
        "control_ev_pct",
        "control_ev_basis",
        "candidate_ev_pct",
        "candidate_ev_basis",
        "action_neutral_outcome_ev_pct",
        "action_neutral_outcome_ev_basis",
        "action_neutral_mfe_pct",
        "action_neutral_mae_pct",
        "action_neutral_first_hit",
        "action_neutral_target_first_delay_sec",
        "full_parent_arm_count",
        "full_parent_arms",
        "full_parent_census_verified",
        "full_parent_census",
        "full_parent_census_sha256",
        "execution_source_commitment",
        "execution_source_commitment_sha256",
        "control_contract_sha256",
        "candidate_contract_sha256",
        "control_prompt_sha256",
        "candidate_prompt_sha256",
        "outcome_label_content_sha256",
        "selected_cost_profile_id",
        "selected_cost_profile_content_sha256",
        "cost_profile_artifact_sha256",
        "cost_catalog_content_sha256",
        "symbol_master_artifact_sha256",
        "symbol_metadata_record_sha256",
    }
)
EXCLUSION_PARENT_BINDING_FIELDS = SOURCE_ROW_FIELDS - {"lifecycle_findings"}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(raw).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _bounded_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"counterfactual_entry_{field}_invalid")
    normalized = value.strip()
    if not normalized or normalized != value or len(normalized) > 512:
        raise ValueError(f"counterfactual_entry_{field}_invalid")
    return normalized


def _canonical_source_row(row: Mapping[str, Any]) -> dict[str, Any]:
    try:
        row_date = date.fromisoformat(str(row.get("target_date") or ""))
    except ValueError as exc:
        raise ValueError("counterfactual_entry_target_date_invalid") from exc
    if row_date < date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE):
        raise ValueError("counterfactual_entry_before_current_design")
    if row.get("ablation_design_version") != CURRENT_DESIGN_VERSION:
        raise ValueError("counterfactual_entry_current_design_required")
    if str(row.get("decision_stage") or "").strip().lower() != "entry":
        raise ValueError("counterfactual_entry_stage_invalid")
    captured_control_action = (
        str(row.get("captured_control_action") or "").strip().upper()
    )
    if captured_control_action not in {"WAIT", "DROP"}:
        raise ValueError("counterfactual_entry_natural_control_absence_required")
    if row.get("lifecycle_findings") != ["lifecycle_exact_join_missing"]:
        raise ValueError("counterfactual_entry_sole_lifecycle_finding_required")

    actions: dict[str, str] = {}
    values: dict[str, float] = {}
    bases: dict[str, str] = {}
    for arm, (action_field, ev_field, basis_field) in ARM_FIELDS.items():
        action = str(row.get(action_field) or "").strip().upper()
        ev = _finite_number(row.get(ev_field))
        basis = str(row.get(basis_field) or "").strip()
        if (
            action not in ALLOWED_ENTRY_ACTIONS
            or ev is None
            or basis not in ALLOWED_EV_BASES
        ):
            raise ValueError(f"counterfactual_entry_arm_{arm.lower()}_invalid")
        actions[action_field] = action
        values[ev_field] = ev
        bases[basis_field] = basis

    outcome_ev = _finite_number(row.get("action_neutral_outcome_ev_pct"))
    outcome_ev_basis = str(row.get("action_neutral_outcome_ev_basis") or "").strip()
    mfe = _finite_number(row.get("action_neutral_mfe_pct"))
    mae = _finite_number(row.get("action_neutral_mae_pct"))
    first_hit = str(row.get("action_neutral_first_hit") or "").strip()
    target_delay = _finite_number(row.get("action_neutral_target_first_delay_sec"))
    if (
        outcome_ev is None
        or outcome_ev_basis not in ALLOWED_OUTCOME_EV_BASES
        or mfe is None
        or mae is None
        or mfe < outcome_ev
        or mae > outcome_ev
        or first_hit not in ALLOWED_FIRST_HIT
        or target_delay is not None
        and target_delay < 0
        or (first_hit in {"net_target_first", "ambiguous_same_timestamp"})
        is not (target_delay is not None)
    ):
        raise ValueError("counterfactual_entry_outcome_metric_invalid")

    full_parent_census = row.get("full_parent_census")
    if (
        row.get("full_parent_arm_count") != len(CURRENT_ARMS)
        or row.get("full_parent_arms") != list(CURRENT_ARMS)
        or row.get("full_parent_census_verified") is not True
        or not isinstance(full_parent_census, Mapping)
        or full_parent_census.get("paired_replay_parent_id")
        != row.get("paired_replay_parent_id")
        or not isinstance(full_parent_census.get("arms"), list)
        or [
            arm.get("arm") if isinstance(arm, Mapping) else None
            for arm in full_parent_census.get("arms") or []
        ]
        != list(CURRENT_ARMS)
        or any(
            not isinstance(arm, Mapping)
            or set(arm) != {"arm", "prompt_contract_sha256", "prompt_sha256"}
            or not _valid_sha256(arm.get("prompt_contract_sha256"))
            or not _valid_sha256(arm.get("prompt_sha256"))
            for arm in full_parent_census.get("arms") or []
        )
        or row.get("full_parent_census_sha256") != _sha256(full_parent_census)
    ):
        raise ValueError("counterfactual_entry_full_parent_census_invalid")
    census_arms = full_parent_census["arms"]
    if (
        census_arms[1]["prompt_contract_sha256"] != row.get("control_contract_sha256")
        or census_arms[2]["prompt_contract_sha256"]
        != row.get("candidate_contract_sha256")
        or census_arms[1]["prompt_sha256"] != row.get("control_prompt_sha256")
        or census_arms[2]["prompt_sha256"] != row.get("candidate_prompt_sha256")
    ):
        raise ValueError("counterfactual_entry_full_parent_binding_invalid")

    execution_source_commitment = row.get("execution_source_commitment")
    expected_execution_commitment_fields = {
        "schema",
        "target_date",
        "paired_replay_parent_id",
        "decision_trace_id",
        "execution_report_content_sha256",
        "execution_report_artifact_sha256",
        "three_arm_evaluation_content_sha256",
        "evaluation_parent_row_sha256",
        "execution_parent_request_refs_sha256",
        "execution_parent_results_sha256",
        "outcome_label_content_sha256",
        "outcome_label_artifact_sha256",
        "materialized_report_content_sha256",
        "materialized_report_artifact_sha256",
        "full_parent_census_sha256",
        "commitment_sha256",
    }
    if row_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE):
        expected_execution_commitment_fields.update(
            {
                "provider_ablation_sample_floor_content_sha256",
                "provider_ablation_sample_floor_artifact_sha256",
            }
        )
    if not isinstance(execution_source_commitment, Mapping):
        raise ValueError("counterfactual_entry_execution_source_commitment_invalid")
    execution_commitment_content = {
        key: value
        for key, value in execution_source_commitment.items()
        if key != "commitment_sha256"
    }
    if (
        set(execution_source_commitment) != expected_execution_commitment_fields
        or execution_source_commitment.get("schema")
        != "main_ai_quality_counterfactual_entry_execution_source_v1"
        or execution_source_commitment.get("target_date") != row_date.isoformat()
        or execution_source_commitment.get("paired_replay_parent_id")
        != row.get("paired_replay_parent_id")
        or execution_source_commitment.get("decision_trace_id")
        != row.get("decision_trace_id")
        or execution_source_commitment.get("outcome_label_content_sha256")
        != row.get("outcome_label_content_sha256")
        or execution_source_commitment.get("full_parent_census_sha256")
        != row.get("full_parent_census_sha256")
        or any(
            not _valid_sha256(execution_source_commitment.get(field))
            for field in expected_execution_commitment_fields
            - {
                "schema",
                "target_date",
                "paired_replay_parent_id",
                "decision_trace_id",
            }
        )
        or execution_source_commitment.get("commitment_sha256")
        != _sha256(execution_commitment_content)
        or row.get("execution_source_commitment_sha256")
        != execution_source_commitment.get("commitment_sha256")
    ):
        raise ValueError("counterfactual_entry_execution_source_commitment_invalid")

    hashes = {}
    for field in (
        "control_contract_sha256",
        "candidate_contract_sha256",
        "control_prompt_sha256",
        "candidate_prompt_sha256",
        "outcome_label_content_sha256",
        "selected_cost_profile_content_sha256",
        "cost_profile_artifact_sha256",
        "cost_catalog_content_sha256",
        "symbol_master_artifact_sha256",
        "symbol_metadata_record_sha256",
    ):
        value = row.get(field)
        if not _valid_sha256(value):
            raise ValueError(f"counterfactual_entry_{field}_invalid")
        hashes[field] = value

    projected = {
        "target_date": row_date.isoformat(),
        "ablation_design_version": CURRENT_DESIGN_VERSION,
        "tuning_axis": _bounded_text(
            row.get("r3_tuning_axis") or row.get("tuning_axis"),
            field="tuning_axis",
        ),
        "paired_replay_parent_id": _bounded_text(
            row.get("paired_replay_parent_id"), field="parent_id"
        ),
        "decision_trace_id": _bounded_text(
            row.get("decision_trace_id"), field="decision_trace_id"
        ),
        "decision_stage": "entry",
        "effective_venue": _bounded_text(
            row.get("effective_venue"), field="effective_venue"
        ),
        "session_bucket": _bounded_text(
            row.get("session_bucket"), field="session_bucket"
        ),
        "stock_code": _bounded_text(row.get("stock_code"), field="stock_code"),
        "captured_control_action": captured_control_action,
        "lifecycle_findings": ["lifecycle_exact_join_missing"],
        **actions,
        **values,
        **bases,
        "action_neutral_outcome_ev_pct": outcome_ev,
        "action_neutral_outcome_ev_basis": outcome_ev_basis,
        "action_neutral_mfe_pct": mfe,
        "action_neutral_mae_pct": mae,
        "action_neutral_first_hit": first_hit,
        "action_neutral_target_first_delay_sec": target_delay,
        "full_parent_arm_count": len(CURRENT_ARMS),
        "full_parent_arms": list(CURRENT_ARMS),
        "full_parent_census_verified": True,
        "full_parent_census": json.loads(
            _canonical_bytes(full_parent_census).decode("utf-8")
        ),
        "full_parent_census_sha256": _sha256(full_parent_census),
        "execution_source_commitment": json.loads(
            _canonical_bytes(execution_source_commitment).decode("utf-8")
        ),
        "execution_source_commitment_sha256": execution_source_commitment[
            "commitment_sha256"
        ],
        **hashes,
        "selected_cost_profile_id": _bounded_text(
            row.get("selected_cost_profile_id"), field="selected_cost_profile_id"
        ),
    }
    if not re.fullmatch(r"[0-9]{6}", projected["stock_code"]):
        raise ValueError("counterfactual_entry_stock_code_invalid")
    if set(projected) != SOURCE_ROW_FIELDS:
        raise AssertionError("counterfactual entry source projection drift")
    return projected


def _validated_exclusion_reason_findings(
    *, reason: Any, findings: Any
) -> tuple[str, list[str]]:
    normalized_reason = _bounded_text(reason, field="exclusion_reason")
    if normalized_reason not in ALLOWED_EXCLUSION_REASONS:
        raise ValueError("counterfactual_entry_exclusion_reason_invalid")
    if (
        not isinstance(findings, list)
        or not findings
        or len(findings) > 64
        or any(not isinstance(finding, str) for finding in findings)
    ):
        raise ValueError("counterfactual_entry_exclusion_findings_invalid")
    normalized_findings = [
        _bounded_text(finding, field="exclusion_finding") for finding in findings
    ]
    if len(normalized_findings) != len(set(normalized_findings)):
        raise ValueError("counterfactual_entry_exclusion_findings_invalid")
    if normalized_reason in {
        "source_quality_audit_not_pass",
        "economic_reference_not_verified",
    }:
        if normalized_findings != [normalized_reason]:
            raise ValueError("counterfactual_entry_exclusion_findings_invalid")
    elif normalized_findings == ["lifecycle_exact_join_missing"]:
        raise ValueError("counterfactual_entry_exclusion_eligible_parent_invalid")
    elif any(
        finding not in ALLOWED_CONTRACT_EXCLUSION_FINDINGS
        and not (
            finding.startswith("lifecycle_metric_missing:")
            and finding.partition(":")[2] in ALLOWED_LIFECYCLE_METRIC_MISSING_FIELDS
        )
        for finding in normalized_findings
    ):
        raise ValueError("counterfactual_entry_exclusion_findings_invalid")
    return normalized_reason, normalized_findings


def _exclusion_parent_binding(source_row: Mapping[str, Any]) -> dict[str, Any]:
    canonical_source = _canonical_source_row(
        {
            **dict(source_row),
            "lifecycle_findings": ["lifecycle_exact_join_missing"],
        }
    )
    return {
        field: canonical_source[field]
        for field in canonical_source
        if field in EXCLUSION_PARENT_BINDING_FIELDS
    }


def _canonical_exclusion_from_source(exclusion: Mapping[str, Any]) -> dict[str, Any]:
    if set(exclusion) != {"source_row", "reason", "findings"} or not isinstance(
        exclusion.get("source_row"), Mapping
    ):
        raise ValueError("counterfactual_entry_exclusion_invalid")
    reason, findings = _validated_exclusion_reason_findings(
        reason=exclusion.get("reason"), findings=exclusion.get("findings")
    )
    binding = _exclusion_parent_binding(exclusion["source_row"])
    return {
        "schema": COUNTERFACTUAL_ENTRY_EXCLUSION_SCHEMA,
        "reason": reason,
        "findings": findings,
        "source_parent_binding": binding,
        "source_parent_binding_sha256": _sha256(binding),
    }


def _validated_persisted_exclusion(exclusion: Mapping[str, Any]) -> dict[str, Any]:
    if set(exclusion) != {
        "schema",
        "reason",
        "findings",
        "source_parent_binding",
        "source_parent_binding_sha256",
    }:
        raise ValueError("counterfactual_entry_exclusion_shape_invalid")
    reason, findings = _validated_exclusion_reason_findings(
        reason=exclusion.get("reason"), findings=exclusion.get("findings")
    )
    binding = exclusion.get("source_parent_binding")
    if (
        not isinstance(binding, Mapping)
        or set(binding) != EXCLUSION_PARENT_BINDING_FIELDS
    ):
        raise ValueError("counterfactual_entry_exclusion_parent_binding_invalid")
    rebuilt_binding = _exclusion_parent_binding(binding)
    if (
        exclusion.get("schema") != COUNTERFACTUAL_ENTRY_EXCLUSION_SCHEMA
        or dict(binding) != rebuilt_binding
        or exclusion.get("source_parent_binding_sha256") != _sha256(rebuilt_binding)
    ):
        raise ValueError("counterfactual_entry_exclusion_parent_binding_invalid")
    return {
        "schema": COUNTERFACTUAL_ENTRY_EXCLUSION_SCHEMA,
        "reason": reason,
        "findings": findings,
        "source_parent_binding": rebuilt_binding,
        "source_parent_binding_sha256": _sha256(rebuilt_binding),
    }


def _source_input_census(
    *,
    source_rows: Sequence[Mapping[str, Any]],
    exclusions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    census = [
        {
            "target_date": row["target_date"],
            "paired_replay_parent_id": row["paired_replay_parent_id"],
            "decision_trace_id": row["decision_trace_id"],
            "disposition": "eligible",
            "source_parent_projection_sha256": _sha256(row),
            "execution_source_commitment_sha256": row[
                "execution_source_commitment_sha256"
            ],
        }
        for row in source_rows
    ]
    for exclusion in exclusions:
        binding = exclusion["source_parent_binding"]
        census.append(
            {
                "target_date": binding["target_date"],
                "paired_replay_parent_id": binding["paired_replay_parent_id"],
                "decision_trace_id": binding["decision_trace_id"],
                "disposition": "excluded",
                "source_parent_projection_sha256": exclusion[
                    "source_parent_binding_sha256"
                ],
                "execution_source_commitment_sha256": binding[
                    "execution_source_commitment_sha256"
                ],
                "exclusion_reason": exclusion["reason"],
                "exclusion_findings_sha256": _sha256(exclusion["findings"]),
                "exclusion_content_sha256": _sha256(exclusion),
            }
        )
    census.sort(
        key=lambda row: (
            row["target_date"],
            row["paired_replay_parent_id"],
            row["disposition"],
        )
    )
    return census


def _input_census_summary(
    *,
    source_rows: Sequence[Mapping[str, Any]],
    exclusions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return bounded rolling census commitments without copying parent rows."""

    input_census = _source_input_census(
        source_rows=source_rows,
        exclusions=exclusions,
    )
    commitment_census = [
        {
            "target_date": row["target_date"],
            "paired_replay_parent_id": row["paired_replay_parent_id"],
            "decision_trace_id": row["decision_trace_id"],
            "execution_source_commitment_sha256": row[
                "execution_source_commitment_sha256"
            ],
        }
        for row in input_census
    ]
    source_date_counts = Counter(row["target_date"] for row in input_census)
    return {
        "input_parent_count": len(input_census),
        "input_census_sha256": _sha256(input_census),
        "execution_source_commitment_census_sha256": _sha256(commitment_census),
        "input_disposition_counts": dict(
            sorted(Counter(row["disposition"] for row in input_census).items())
        ),
        "exclusion_reason_counts": dict(
            sorted(Counter(row["reason"] for row in exclusions).items())
        ),
        "source_date_counts": dict(sorted(source_date_counts.items())),
    }


def _date_window_rows(
    rows: Sequence[Mapping[str, Any]], *, target_date: str, trading_days: int
) -> tuple[list[Mapping[str, Any]], list[str]]:
    target = date.fromisoformat(target_date)
    parsed_dates: set[date] = set()
    for row in rows:
        try:
            candidate = date.fromisoformat(str(row.get("target_date") or ""))
        except ValueError:
            continue
        if candidate <= target and is_krx_trading_day(candidate):
            parsed_dates.add(candidate)
    dates = sorted(candidate.isoformat() for candidate in parsed_dates)
    selected_dates = dates[-trading_days:]
    return (
        [row for row in rows if row.get("target_date") in selected_dates],
        selected_dates,
    )


def _arm_metrics(rows: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Any]:
    action_field, ev_field, basis_field = ARM_FIELDS[arm]
    actions = [str(row[action_field]) for row in rows]
    open_rows = [row for row in rows if row[action_field] == "BUY"]
    target_first_delays = [
        float(row["action_neutral_target_first_delay_sec"])
        for row in open_rows
        if row["action_neutral_target_first_delay_sec"] is not None
    ]
    return {
        "arm": arm,
        "parent_count": len(rows),
        "action_counts": dict(sorted(Counter(actions).items())),
        "economic_metric_basis_counts": dict(
            sorted(Counter(str(row[basis_field]) for row in rows).items())
        ),
        "exposure_open_count": len(open_rows),
        "exposure_open_rate_pct": (
            len(open_rows) / len(rows) * 100.0 if rows else None
        ),
        "source_quality_adjusted_ev_pct": (
            fmean(float(row[ev_field]) for row in rows) if rows else None
        ),
        "exposure_open_outcome_sample_count": len(open_rows),
        "exposure_open_equal_weight_avg_profit_pct": (
            fmean(float(row["action_neutral_outcome_ev_pct"]) for row in open_rows)
            if open_rows
            else None
        ),
        "exposure_open_mean_mfe_pct": (
            fmean(float(row["action_neutral_mfe_pct"]) for row in open_rows)
            if open_rows
            else None
        ),
        "exposure_open_mean_mae_pct": (
            fmean(float(row["action_neutral_mae_pct"]) for row in open_rows)
            if open_rows
            else None
        ),
        "exposure_open_first_hit_counts": dict(
            sorted(
                Counter(row["action_neutral_first_hit"] for row in open_rows).items()
            )
        ),
        "exposure_open_target_first_rate_pct": (
            sum(
                row["action_neutral_first_hit"] == "net_target_first"
                for row in open_rows
            )
            / len(open_rows)
            * 100.0
            if open_rows
            else None
        ),
        "exposure_open_target_first_delay_sample_count": len(target_first_delays),
        "exposure_open_mean_target_first_delay_sec": (
            fmean(target_first_delays) if target_first_delays else None
        ),
        "exposure_open_median_target_first_delay_sec": (
            median(target_first_delays) if target_first_delays else None
        ),
    }


def _comparison_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    role: str,
    left: str,
    right: str,
    changed_axis: str,
) -> dict[str, Any]:
    left_action_field, left_ev_field, _left_basis_field = ARM_FIELDS[left]
    right_action_field, right_ev_field, _right_basis_field = ARM_FIELDS[right]
    newly_open = [
        row
        for row in rows
        if row[left_action_field] != "BUY" and row[right_action_field] == "BUY"
    ]
    closed = [
        row
        for row in rows
        if row[left_action_field] == "BUY" and row[right_action_field] != "BUY"
    ]
    target_first_delays = [
        float(row["action_neutral_target_first_delay_sec"])
        for row in newly_open
        if row["action_neutral_target_first_delay_sec"] is not None
    ]
    return {
        "comparison_role": role,
        "left_arm": left,
        "right_arm": right,
        "changed_axis": changed_axis,
        "common_parent_count": len(rows),
        "action_changed_count": sum(
            row[left_action_field] != row[right_action_field] for row in rows
        ),
        "no_action_transition_count": sum(
            row[left_action_field] == row[right_action_field] for row in rows
        ),
        "exposure_opened_count": len(newly_open),
        "exposure_closed_count": len(closed),
        "net_exposure_open_count_delta": len(newly_open) - len(closed),
        "exposure_open_rate_delta_pct": (
            fmean(
                float(row[right_action_field] == "BUY")
                - float(row[left_action_field] == "BUY")
                for row in rows
            )
            * 100.0
            if rows
            else None
        ),
        "paired_source_quality_adjusted_ev_delta_pct": (
            fmean(
                float(row[right_ev_field]) - float(row[left_ev_field]) for row in rows
            )
            if rows
            else None
        ),
        "new_exposure_counterfactual_sample_count": len(newly_open),
        "new_exposure_equal_weight_avg_profit_pct": (
            fmean(float(row["action_neutral_outcome_ev_pct"]) for row in newly_open)
            if newly_open
            else None
        ),
        "new_exposure_mean_mfe_pct": (
            fmean(float(row["action_neutral_mfe_pct"]) for row in newly_open)
            if newly_open
            else None
        ),
        "new_exposure_mean_mae_pct": (
            fmean(float(row["action_neutral_mae_pct"]) for row in newly_open)
            if newly_open
            else None
        ),
        "new_exposure_first_hit_counts": dict(
            sorted(
                Counter(row["action_neutral_first_hit"] for row in newly_open).items()
            )
        ),
        "new_exposure_target_first_rate_pct": (
            sum(
                row["action_neutral_first_hit"] == "net_target_first"
                for row in newly_open
            )
            / len(newly_open)
            * 100.0
            if newly_open
            else None
        ),
        "new_exposure_target_first_delay_sample_count": len(target_first_delays),
        "new_exposure_mean_target_first_delay_sec": (
            fmean(target_first_delays) if target_first_delays else None
        ),
        "new_exposure_median_target_first_delay_sec": (
            median(target_first_delays) if target_first_delays else None
        ),
    }


def _window_metrics(
    rows: Sequence[Mapping[str, Any]], *, target_date: str, trading_days: int
) -> dict[str, Any]:
    selected, selected_dates = _date_window_rows(
        rows, target_date=target_date, trading_days=trading_days
    )
    return {
        "window_trading_days": trading_days,
        "observed_trading_days": len(selected_dates),
        "selected_dates": selected_dates,
        "full_parent_census_count": len(selected),
        "unique_symbol_count": len({str(row["stock_code"]) for row in selected}),
        "arms": {arm: _arm_metrics(selected, arm) for arm in ARM_FIELDS},
        "comparisons": [
            _comparison_metrics(
                selected,
                role=role,
                left=left,
                right=right,
                changed_axis=changed_axis,
            )
            for role, left, right, changed_axis in COMPARISONS
        ],
    }


def _build_partitions(
    rows: Sequence[Mapping[str, Any]], *, target_date: str
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["effective_venue"]),
            str(row["session_bucket"]),
            str(row["control_contract_sha256"]),
            str(row["candidate_contract_sha256"]),
            str(row["selected_cost_profile_id"]),
            str(row["selected_cost_profile_content_sha256"]),
            str(row["tuning_axis"]),
        )
        grouped[key].append(row)
    partitions = []
    for key, partition_rows in sorted(grouped.items()):
        ordered_rows = sorted(
            partition_rows,
            key=lambda row: (
                str(row["target_date"]),
                str(row["paired_replay_parent_id"]),
            ),
        )
        partitions.append(
            {
                "decision_stage": "entry",
                "effective_venue": key[0],
                "session_bucket": key[1],
                "control_contract_sha256": key[2],
                "candidate_contract_sha256": key[3],
                "selected_cost_profile_id": key[4],
                "selected_cost_profile_content_sha256": key[5],
                "tuning_axis": key[6],
                "source_parent_count": len(ordered_rows),
                "source_dates": sorted(
                    {str(row["target_date"]) for row in ordered_rows}
                ),
                "windows": {
                    str(days): _window_metrics(
                        ordered_rows,
                        target_date=target_date,
                        trading_days=days,
                    )
                    for days in WINDOW_TRADING_DAYS
                },
            }
        )
    return partitions


def build_counterfactual_entry_diagnostic(
    *,
    target_date: str,
    rows: Iterable[Mapping[str, Any]],
    exclusions: Iterable[Mapping[str, Any]] = (),
    global_blockers: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a complete, non-promotable A/B/C entry opportunity census."""

    try:
        target_day = date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("counterfactual_entry_artifact_target_date_invalid") from exc
    if target_day < date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE):
        raise ValueError("counterfactual_entry_artifact_before_current_design")
    source_rows = [_canonical_source_row(row) for row in rows]
    source_rows.sort(
        key=lambda row: (
            row["target_date"],
            row["paired_replay_parent_id"],
        )
    )
    parent_keys = [
        (row["target_date"], row["paired_replay_parent_id"]) for row in source_rows
    ]
    trace_keys = [(row["target_date"], row["decision_trace_id"]) for row in source_rows]
    if len(parent_keys) != len(set(parent_keys)) or len(trace_keys) != len(
        set(trace_keys)
    ):
        raise ValueError("counterfactual_entry_parent_census_duplicate")
    if any(str(row["target_date"]) > target_date for row in source_rows):
        raise ValueError("counterfactual_entry_future_source_date_invalid")

    normalized_exclusions: list[dict[str, Any]] = []
    for exclusion in exclusions:
        if not isinstance(exclusion, Mapping):
            raise ValueError("counterfactual_entry_exclusion_invalid")
        normalized_exclusions.append(_canonical_exclusion_from_source(exclusion))
    normalized_exclusions.sort(
        key=lambda exclusion: (
            exclusion["source_parent_binding"]["target_date"],
            exclusion["source_parent_binding"]["paired_replay_parent_id"],
            exclusion["reason"],
        )
    )
    exclusion_parent_keys = [
        (
            exclusion["source_parent_binding"]["target_date"],
            exclusion["source_parent_binding"]["paired_replay_parent_id"],
        )
        for exclusion in normalized_exclusions
    ]
    exclusion_trace_keys = [
        (
            exclusion["source_parent_binding"]["target_date"],
            exclusion["source_parent_binding"]["decision_trace_id"],
        )
        for exclusion in normalized_exclusions
    ]
    if (
        len(exclusion_parent_keys) != len(set(exclusion_parent_keys))
        or len(exclusion_trace_keys) != len(set(exclusion_trace_keys))
        or set(parent_keys) & set(exclusion_parent_keys)
        or set(trace_keys) & set(exclusion_trace_keys)
    ):
        raise ValueError("counterfactual_entry_full_parent_census_duplicate")
    if any(
        exclusion["source_parent_binding"]["target_date"] > target_date
        for exclusion in normalized_exclusions
    ):
        raise ValueError("counterfactual_entry_future_source_date_invalid")
    census_summary = _input_census_summary(
        source_rows=source_rows,
        exclusions=normalized_exclusions,
    )
    blockers = sorted(
        {_bounded_text(value, field="global_blocker") for value in global_blockers}
    )
    partitions = (
        [] if blockers else _build_partitions(source_rows, target_date=target_date)
    )
    body = {
        "schema": COUNTERFACTUAL_ENTRY_DIAGNOSTIC_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "counterfactual_entry_diagnostic_blocked"
            if blockers
            else (
                "counterfactual_entry_diagnostic_evaluated"
                if source_rows
                else (
                    "counterfactual_entry_diagnostic_no_eligible_parent"
                    if normalized_exclusions
                    else "no_natural_wait_drop_entry_parent"
                )
            )
        ),
        "ablation_design_version": CURRENT_DESIGN_VERSION,
        "ablation_arms": list(ARM_FIELDS),
        "eligible_parent_count": len(source_rows),
        "excluded_parent_count": len(normalized_exclusions),
        "full_parent_census_count": len(source_rows) + len(normalized_exclusions),
        "input_census_schema": COUNTERFACTUAL_ENTRY_INPUT_CENSUS_SCHEMA,
        **census_summary,
        "global_blockers": blockers,
        "partitions": partitions,
        "candidate_count": 0,
        "candidates": [],
        **METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }
    artifact = {**body, "artifact_content_sha256": _sha256(body)}
    if len(_canonical_bytes(artifact)) > MAX_PERSISTED_ARTIFACT_BYTES:
        blockers = sorted(
            {
                *blockers,
                "counterfactual_entry_partition_artifact_size_bound_exceeded",
            }
        )
        body.update(
            {
                "status": "counterfactual_entry_diagnostic_blocked",
                "global_blockers": blockers,
                "partitions": [],
            }
        )
        artifact = {**body, "artifact_content_sha256": _sha256(body)}
        if len(_canonical_bytes(artifact)) > MAX_PERSISTED_ARTIFACT_BYTES:
            raise ValueError("counterfactual_entry_artifact_size_bound_exceeded")
    validate_counterfactual_entry_diagnostic(
        artifact,
        expected_source_rows=source_rows,
        expected_exclusions=normalized_exclusions,
        expected_global_blockers=blockers,
    )
    return artifact


def validate_counterfactual_entry_diagnostic(
    artifact: Mapping[str, Any],
    *,
    expected_source_rows: Iterable[Mapping[str, Any]] | None = None,
    expected_exclusions: Iterable[Mapping[str, Any]] | None = None,
    expected_global_blockers: Iterable[str] | None = None,
) -> None:
    """Rebuild the full census and reject authority or metric reseals."""

    if artifact.get("schema") != COUNTERFACTUAL_ENTRY_DIAGNOSTIC_SCHEMA:
        raise ValueError("counterfactual_entry_artifact_schema_invalid")
    content = {
        key: value
        for key, value in artifact.items()
        if key != "artifact_content_sha256"
    }
    if artifact.get("artifact_content_sha256") != _sha256(content):
        raise ValueError("counterfactual_entry_artifact_hash_invalid")
    for field, expected in AUTHORITY_CONTRACT.items():
        if artifact.get(field) != expected:
            raise ValueError(f"counterfactual_entry_authority_invalid:{field}")
    for field, expected in METRIC_CONTRACT.items():
        if artifact.get(field) != expected:
            raise ValueError(f"counterfactual_entry_metric_contract_invalid:{field}")
    expected_top_level_fields = {
        "schema",
        "target_date",
        "generated_at",
        "status",
        "ablation_design_version",
        "ablation_arms",
        "eligible_parent_count",
        "excluded_parent_count",
        "full_parent_census_count",
        "input_census_schema",
        "input_parent_count",
        "input_census_sha256",
        "execution_source_commitment_census_sha256",
        "input_disposition_counts",
        "exclusion_reason_counts",
        "source_date_counts",
        "global_blockers",
        "partitions",
        "candidate_count",
        "candidates",
        "artifact_content_sha256",
        *AUTHORITY_CONTRACT,
        *METRIC_CONTRACT,
    }
    if set(artifact) != expected_top_level_fields:
        raise ValueError("counterfactual_entry_artifact_shape_invalid")
    if artifact.get(
        "ablation_design_version"
    ) != CURRENT_DESIGN_VERSION or artifact.get("ablation_arms") != list(ARM_FIELDS):
        raise ValueError("counterfactual_entry_ablation_contract_invalid")
    blockers = artifact.get("global_blockers")
    partitions = artifact.get("partitions")
    if (
        not isinstance(blockers, list)
        or not isinstance(partitions, list)
        or artifact.get("input_census_schema")
        != COUNTERFACTUAL_ENTRY_INPUT_CENSUS_SCHEMA
        or not _valid_sha256(artifact.get("input_census_sha256"))
        or not _valid_sha256(artifact.get("execution_source_commitment_census_sha256"))
        or not isinstance(artifact.get("input_disposition_counts"), Mapping)
        or not isinstance(artifact.get("exclusion_reason_counts"), Mapping)
        or not isinstance(artifact.get("source_date_counts"), Mapping)
        or artifact.get("candidate_count") != 0
        or artifact.get("candidates") != []
    ):
        raise ValueError("counterfactual_entry_artifact_census_invalid")
    if expected_source_rows is None or expected_exclusions is None:
        raise ValueError("counterfactual_entry_external_input_census_required")
    rebuilt_rows = [_canonical_source_row(row) for row in expected_source_rows]
    rebuilt_rows.sort(
        key=lambda row: (row["target_date"], row["paired_replay_parent_id"])
    )
    rebuilt_exclusions: list[dict[str, Any]] = []
    for exclusion in expected_exclusions:
        if not isinstance(exclusion, Mapping):
            raise ValueError("counterfactual_entry_exclusion_invalid")
        if "source_row" in exclusion:
            rebuilt_exclusions.append(_canonical_exclusion_from_source(exclusion))
        else:
            rebuilt_exclusions.append(_validated_persisted_exclusion(exclusion))
    rebuilt_exclusions.sort(
        key=lambda exclusion: (
            exclusion["source_parent_binding"]["target_date"],
            exclusion["source_parent_binding"]["paired_replay_parent_id"],
            exclusion["reason"],
        )
    )
    parent_keys = [
        (row["target_date"], row["paired_replay_parent_id"]) for row in rebuilt_rows
    ]
    trace_keys = [
        (row["target_date"], row["decision_trace_id"]) for row in rebuilt_rows
    ]
    exclusion_parent_keys = [
        (
            exclusion["source_parent_binding"]["target_date"],
            exclusion["source_parent_binding"]["paired_replay_parent_id"],
        )
        for exclusion in rebuilt_exclusions
    ]
    exclusion_trace_keys = [
        (
            exclusion["source_parent_binding"]["target_date"],
            exclusion["source_parent_binding"]["decision_trace_id"],
        )
        for exclusion in rebuilt_exclusions
    ]
    if (
        len(parent_keys) != len(set(parent_keys))
        or len(trace_keys) != len(set(trace_keys))
        or len(exclusion_parent_keys) != len(set(exclusion_parent_keys))
        or len(exclusion_trace_keys) != len(set(exclusion_trace_keys))
        or set(parent_keys) & set(exclusion_parent_keys)
        or set(trace_keys) & set(exclusion_trace_keys)
    ):
        raise ValueError("counterfactual_entry_parent_census_duplicate")
    target_date = str(artifact.get("target_date") or "")
    try:
        target_day = date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("counterfactual_entry_artifact_target_date_invalid") from exc
    if (
        target_day < date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
        or any(str(row["target_date"]) > target_date for row in rebuilt_rows)
        or any(key[0] > target_date for key in exclusion_parent_keys)
    ):
        raise ValueError("counterfactual_entry_artifact_date_scope_invalid")
    try:
        generated_at = datetime.fromisoformat(str(artifact.get("generated_at") or ""))
    except ValueError as exc:
        raise ValueError("counterfactual_entry_generated_at_invalid") from exc
    if generated_at.tzinfo is None:
        raise ValueError("counterfactual_entry_generated_at_invalid")
    if blockers != sorted(set(blockers)) or any(
        not isinstance(value, str) or not value.strip() for value in blockers
    ):
        raise ValueError("counterfactual_entry_global_blocker_invalid")
    if expected_global_blockers is None:
        raise ValueError("counterfactual_entry_external_global_blockers_required")
    canonical_expected_blockers = sorted(
        {
            _bounded_text(value, field="global_blocker")
            for value in expected_global_blockers
        }
    )
    if blockers != canonical_expected_blockers:
        raise ValueError("counterfactual_entry_external_global_blockers_mismatch")
    rebuilt_census_summary = _input_census_summary(
        source_rows=rebuilt_rows,
        exclusions=rebuilt_exclusions,
    )
    if any(
        artifact.get(field) != value for field, value in rebuilt_census_summary.items()
    ) or (
        artifact.get("eligible_parent_count") != len(rebuilt_rows)
        or artifact.get("excluded_parent_count") != len(rebuilt_exclusions)
        or artifact.get("full_parent_census_count")
        != len(rebuilt_rows) + len(rebuilt_exclusions)
    ):
        raise ValueError("counterfactual_entry_external_input_census_mismatch")
    expected_partitions = (
        [] if blockers else _build_partitions(rebuilt_rows, target_date=target_date)
    )
    if partitions != expected_partitions:
        raise ValueError("counterfactual_entry_partition_rebuild_mismatch")
    expected_status = (
        "counterfactual_entry_diagnostic_blocked"
        if blockers
        else (
            "counterfactual_entry_diagnostic_evaluated"
            if rebuilt_rows
            else (
                "counterfactual_entry_diagnostic_no_eligible_parent"
                if rebuilt_exclusions
                else "no_natural_wait_drop_entry_parent"
            )
        )
    )
    if artifact.get("status") != expected_status:
        raise ValueError("counterfactual_entry_artifact_status_invalid")
    if len(_canonical_bytes(artifact)) > MAX_PERSISTED_ARTIFACT_BYTES:
        raise ValueError("counterfactual_entry_artifact_size_bound_exceeded")
