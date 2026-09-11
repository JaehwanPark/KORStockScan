"""Shared source-only BUY funnel contracts for report and PREOPEN consumers.

Owned by automation, not the live order engine. No I/O or runtime mutation.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any

CURRENT_SCHEMA_VERSION = 6
CURRENT_CONTRACT_DATE = "2026-09-07"
ENTRY_SUBMIT_DROUGHT_CORE_AXES = (
    "UPSTREAM_GATE",
    "LATENCY_PRE_SUBMIT",
    "ENTRY_AI_AUTHORITY_REVALIDATION",
    "PRICE_REVALIDATION",
    "BROKER_RECEIPT",
)
ENTRY_SUBMIT_DROUGHT_SUPPORTING_AXES = (
    "BUDGET_PASS_COLLAPSE",
    "ECONOMIC_PARTICIPATION",
    "SIM_REAL_AUTHORITY",
    "SOURCE_TAXONOMY_LEAKAGE",
)
UPSTREAM_TERMINAL_STAGES = frozenset(
    {
        "blocked_ai_score",
        "ai_score_50_buy_hold_override",
        "wait65_79_ev_candidate",
        "first_ai_wait",
        "blocked_liquidity",
        "blocked_overbought",
        "blocked_strength_momentum",
        "blocked_vpw",
        "blocked_gap",
        "rising_missed_tick_speed_entry_block",
        "real_weak_ai_micro_entry_block",
        "pre_submit_micro_unavailable_block",
        "rising_missed_reversal_pre_submit_block",
        "auth_zero_qty",
        "blocked_zero_qty",
        "entry_armed_expired",
        "entry_armed_expired_after_wait",
        "entry_arm_expired",
    }
)
TERMINAL_STAGES_BY_AXIS = {
    "UPSTREAM_GATE": UPSTREAM_TERMINAL_STAGES | {"order_bundle_failed"},
    "LATENCY_PRE_SUBMIT": {"latency_block"},
    "ENTRY_AI_AUTHORITY_REVALIDATION": {"pre_submit_entry_ai_authority_guard_block"},
    "PRICE_REVALIDATION": {
        "entry_submit_revalidation_block",
        "entry_price_canary_submit_block",
        "pre_submit_price_guard_block",
        "entry_ai_price_canary_skip_order",
    },
    "BROKER_RECEIPT": {
        "order_bundle_failed",
        "broker_submit_failed",
        "buy_order_failed",
        "submit_order_failed",
    },
}


def cash_shortfall_reason(fields: dict[str, Any], terminal_at: str) -> str:
    """Distinguish broker cash shortage from new-entry allocation shortage."""
    if fields.get("kt00011_cash_orderable_contract_status") != "valid" or fields.get(
        "kt00011_error"
    ):
        return ""
    try:
        values = [
            fields.get(k)
            for k in (
                "cash_orderable_qty_cap",
                "cash_orderable_amount",
                "kt00011_requested_unit_price",
            )
        ]
        if any(isinstance(v, bool) or v is None for v in values):
            return ""
        qty, cash, price = map(float, values)
        observed = datetime.fromisoformat(
            str(fields.get("kt00011_capacity_observed_at") or "")
        )
        terminal = datetime.fromisoformat(terminal_at)
        kst = timezone(timedelta(hours=9))
        observed = (
            observed.replace(tzinfo=kst)
            if observed.tzinfo is None
            else observed.astimezone(kst)
        )
        terminal = (
            terminal.replace(tzinfo=kst)
            if terminal.tzinfo is None
            else terminal.astimezone(kst)
        )
    except (TypeError, ValueError, OverflowError):
        return ""
    digest = str(fields.get("kt00011_capacity_source_sha256") or "")
    valid_source = (
        all(math.isfinite(v) for v in (qty, cash, price))
        and price > 0
        and cash >= 0
        and qty >= 0
        and observed.date() == terminal.date()
        and observed <= terminal
        and len(digest) == 64
        and all(c in "0123456789abcdef" for c in digest.lower())
    )
    if not valid_source:
        return ""
    if qty == 0 and cash < price:
        return "broker_proven_cash_shortfall"
    if any(
        isinstance(fields.get(k), bool)
        for k in ("pre_cap_qty", "effective_qty", "budget_base")
    ):
        return ""
    try:
        pre = float(fields.get("pre_cap_qty"))
        effective = float(fields.get("effective_qty"))
        budget = float(fields.get("budget_base"))
    except (TypeError, ValueError, OverflowError):
        return ""
    if (
        qty >= 1
        and cash >= price
        and pre >= 1
        and effective == 0
        and all(math.isfinite(v) for v in (pre, effective, budget))
        and budget > 0
        and fields.get("binding_caps") == "max_position_qty_cap"
        and fields.get("allocation_stage")
        in {"initial_entry", "rising_missed_scout_initial"}
        and fields.get("formula_version") == "entry_type_5stage_cap25_v1"
        and (
            fields.get("sizing_config_valid") is None
            or fields.get("sizing_config_valid") is True
            or fields.get("sizing_config_valid") in ("True", "true")
        )
    ):
        return "new_entry_position_budget_shortfall"
    return ""


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        number = float(value)
        return int(number) if math.isfinite(number) and number.is_integer() else default
    except (ValueError, TypeError, OverflowError):
        return default


def _validate_structure(
    buy_funnel: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    """Validate the schema-v4 exact-attempt causal partition.

    Historical schema-v3 artifacts remain readable archive evidence.  New
    reports must prove that all five core axes use record_id without fallback
    and that only terminal, ordered attempts enter the causal partition.
    """

    schema_version = _safe_int(buy_funnel.get("schema_version"), 0)
    if schema_version < 4:
        return {
            "status": "legacy_not_required",
            "structural_issues": [],
            "source_quality_gap": False,
            "exact_attempt_contract": {},
        }

    issues: list[str] = []
    expected_axes = list(ENTRY_SUBMIT_DROUGHT_CORE_AXES)
    exact_contract = (
        contract.get("exact_attempt_contract")
        if isinstance(contract.get("exact_attempt_contract"), dict)
        else {}
    )
    breakdown = (
        contract.get("observation_breakdown")
        if isinstance(contract.get("observation_breakdown"), dict)
        else {}
    )
    breakdown_exact = (
        breakdown.get("exact_attempt_contract")
        if isinstance(breakdown.get("exact_attempt_contract"), dict)
        else {}
    )
    axes = breakdown.get("axes") if isinstance(breakdown.get("axes"), dict) else {}
    causal_axes = (
        contract.get("causal_bottleneck_axes")
        if isinstance(contract.get("causal_bottleneck_axes"), list)
        else []
    )
    no_signal_axes = (
        contract.get("no_current_signal_axes")
        if isinstance(contract.get("no_current_signal_axes"), list)
        else []
    )
    observation_only_axes = (
        contract.get("observation_only_axes")
        if isinstance(contract.get("observation_only_axes"), list)
        else []
    )

    if not exact_contract:
        issues.append("exact_attempt_contract_missing")
    if contract.get("core_handoff_axes") != expected_axes:
        issues.append("core_handoff_axes_invalid")
    if breakdown.get("core_handoff_axes") != expected_axes:
        issues.append("breakdown_core_handoff_axes_invalid")
    expected_supporting_axes = list(ENTRY_SUBMIT_DROUGHT_SUPPORTING_AXES)
    if contract.get("supporting_diagnostic_axes") != expected_supporting_axes:
        issues.append("supporting_diagnostic_axes_invalid")
    if breakdown.get("supporting_diagnostic_axes") != expected_supporting_axes:
        issues.append("breakdown_supporting_diagnostic_axes_invalid")
    expected_axis_order = [*expected_axes, *expected_supporting_axes]
    if breakdown.get("axis_order") != expected_axis_order:
        issues.append("breakdown_axis_order_invalid")
    if set(axes) != set(expected_axis_order):
        issues.append("observation_axis_rows_invalid")
    if breakdown.get("causal_bottleneck_axes") != causal_axes:
        issues.append("causal_axis_copy_mismatch")
    if breakdown.get("no_current_signal_axes") != no_signal_axes:
        issues.append("no_signal_axis_copy_mismatch")
    if breakdown.get("observation_only_axes") != observation_only_axes:
        issues.append("observation_only_axis_copy_mismatch")
    partition_sets = [
        set(causal_axes),
        set(no_signal_axes),
        set(observation_only_axes),
    ]
    if any(
        partition_sets[left] & partition_sets[right]
        for left in range(len(partition_sets))
        for right in range(left + 1, len(partition_sets))
    ):
        issues.append("observation_axis_partition_not_disjoint")
    if set().union(*partition_sets) != set(expected_axis_order):
        issues.append("observation_axis_partition_incomplete")
    if exact_contract.get("core_handoff_axes") != expected_axes:
        issues.append("exact_contract_core_handoff_axes_invalid")
    if breakdown_exact != exact_contract:
        issues.append("exact_attempt_contract_copy_mismatch")
    if exact_contract.get("identity_field") != "record_id":
        issues.append("exact_identity_field_invalid")
    if exact_contract.get("identity_fallback_allowed") is not False:
        issues.append("exact_identity_fallback_not_forbidden")
    if exact_contract.get("exclusion_applied") is not True:
        issues.append("exact_invalid_row_exclusion_missing")
    if exact_contract.get("terminal_causal_partition_disjoint") is not True:
        issues.append("terminal_causal_partition_not_disjoint")
    if exact_contract.get("runtime_effect") is not False:
        issues.append("exact_attempt_runtime_effect_invalid")
    if exact_contract.get("allowed_runtime_apply") is not False:
        issues.append("exact_attempt_runtime_apply_authority_invalid")
    if exact_contract.get("status") not in {
        "pass",
        "source_quality_gap_excluded",
    }:
        issues.append("exact_attempt_status_invalid")

    denominator_missing = (
        exact_contract.get("denominator_missing_exact_attempt_key_events")
        if isinstance(
            exact_contract.get("denominator_missing_exact_attempt_key_events"), dict
        )
        else {}
    )
    denominator_counts = (
        exact_contract.get("denominator_exact_attempt_counts")
        if isinstance(exact_contract.get("denominator_exact_attempt_counts"), dict)
        else {}
    )
    denominator_order_violations = (
        exact_contract.get("denominator_stage_order_violation_events")
        if isinstance(
            exact_contract.get("denominator_stage_order_violation_events"), dict
        )
        else {}
    )
    axis_missing = (
        exact_contract.get("axis_missing_exact_attempt_key_events")
        if isinstance(exact_contract.get("axis_missing_exact_attempt_key_events"), dict)
        else {}
    )
    order_violations = (
        exact_contract.get("axis_stage_order_violation_events")
        if isinstance(exact_contract.get("axis_stage_order_violation_events"), dict)
        else {}
    )
    exact_event_counts = (
        exact_contract.get("axis_exact_attempt_event_counts")
        if isinstance(exact_contract.get("axis_exact_attempt_event_counts"), dict)
        else {}
    )
    later_progress_counts = (
        exact_contract.get("axis_later_progress_attempt_counts")
        if isinstance(exact_contract.get("axis_later_progress_attempt_counts"), dict)
        else {}
    )
    terminal_counts = (
        exact_contract.get("axis_terminal_causal_attempt_counts")
        if isinstance(exact_contract.get("axis_terminal_causal_attempt_counts"), dict)
        else {}
    )
    expected_denominator_stages = {
        "ai_confirmed",
        "budget_pass",
        "latency_pass",
        "order_bundle_submitted",
    }
    if set(exact_contract.get("denominator_stages") or []) != (
        expected_denominator_stages
    ):
        issues.append("exact_denominator_stage_declaration_invalid")
    if set(denominator_counts) != expected_denominator_stages:
        issues.append("exact_denominator_count_census_invalid")
    if set(denominator_missing) != expected_denominator_stages:
        issues.append("exact_denominator_stage_census_invalid")
    if set(denominator_order_violations) != expected_denominator_stages:
        issues.append("exact_denominator_order_census_invalid")
    if set(axis_missing) != set(expected_axes):
        issues.append("exact_axis_missing_census_invalid")
    if set(order_violations) != set(expected_axes):
        issues.append("exact_axis_order_census_invalid")
    if set(exact_event_counts) != set(expected_axes):
        issues.append("exact_axis_event_census_invalid")
    if set(later_progress_counts) != set(expected_axes):
        issues.append("exact_axis_later_progress_census_invalid")
    if set(terminal_counts) != set(expected_axes):
        issues.append("exact_axis_terminal_census_invalid")
    for census_name, census in (
        ("denominator_count", denominator_counts),
        ("denominator_missing", denominator_missing),
        ("denominator_order", denominator_order_violations),
        ("axis_missing", axis_missing),
        ("axis_order", order_violations),
        ("axis_event", exact_event_counts),
        ("axis_later_progress", later_progress_counts),
        ("axis_terminal", terminal_counts),
    ):
        if any(_safe_int(value, -1) < 0 for value in census.values()):
            issues.append(f"exact_{census_name}_negative")

    calculated_missing = sum(
        _safe_int(value, 0) for value in denominator_missing.values()
    )
    calculated_missing += sum(_safe_int(value, 0) for value in axis_missing.values())
    if (
        _safe_int(exact_contract.get("missing_exact_attempt_key_event_count"), -1)
        != calculated_missing
    ):
        issues.append("exact_missing_total_mismatch")
    calculated_order_violations = sum(
        _safe_int(value, 0) for value in order_violations.values()
    )
    calculated_order_violations += sum(
        _safe_int(value, 0) for value in denominator_order_violations.values()
    )
    if (
        _safe_int(exact_contract.get("stage_order_violation_event_count"), -1)
        != calculated_order_violations
    ):
        issues.append("exact_order_violation_total_mismatch")
    calculated_terminal = sum(_safe_int(value, 0) for value in terminal_counts.values())
    if _safe_int(exact_contract.get("terminal_causal_attempt_count"), -1) != (
        calculated_terminal
    ):
        issues.append("exact_terminal_total_mismatch")
    calculated_source_quality_gap = bool(
        calculated_missing > 0
        or calculated_order_violations > 0
        or _safe_int(exact_contract.get("unclassified_terminal_attempt_count"), 0) > 0
    )
    expected_exact_status = (
        "source_quality_gap_excluded" if calculated_source_quality_gap else "pass"
    )
    if exact_contract.get("status") != expected_exact_status:
        issues.append("exact_attempt_status_census_mismatch")

    expected_causal_axes: list[str] = []
    expected_no_signal_core_axes: list[str] = []
    for axis in expected_axes:
        axis_row = axes.get(axis) if isinstance(axes.get(axis), dict) else {}
        terminal_count = _safe_int(terminal_counts.get(axis), 0)
        if not axis_row:
            issues.append(f"core_axis_row_missing:{axis}")
            continue
        if _safe_int(axis_row.get("observed_count"), -1) != terminal_count:
            issues.append(f"core_axis_observed_count_mismatch:{axis}")
        expected_status = "observed" if terminal_count > 0 else "no_current_signal"
        if axis_row.get("status") != expected_status:
            issues.append(f"core_axis_status_mismatch:{axis}")
        if axis_row.get("exact_join_valid") is not (terminal_count > 0):
            issues.append(f"core_axis_exact_join_state_invalid:{axis}")
        if axis_row.get("identity_field") != "record_id":
            issues.append(f"core_axis_identity_field_invalid:{axis}")
        if axis_row.get("identity_fallback_allowed") is not False:
            issues.append(f"core_axis_identity_fallback_invalid:{axis}")
        axis_missing_count = _safe_int(axis_missing.get(axis), 0)
        axis_order_count = _safe_int(order_violations.get(axis), 0)
        if _safe_int(axis_row.get("missing_exact_attempt_key_events"), -1) != (
            axis_missing_count
        ):
            issues.append(f"core_axis_missing_count_mismatch:{axis}")
        if _safe_int(axis_row.get("stage_order_violation_events"), -1) != (
            axis_order_count
        ):
            issues.append(f"core_axis_order_count_mismatch:{axis}")
        if _safe_int(axis_row.get("exact_attempt_event_count"), -1) != _safe_int(
            exact_event_counts.get(axis), 0
        ):
            issues.append(f"core_axis_event_count_mismatch:{axis}")
        if _safe_int(axis_row.get("later_progress_attempt_count"), -1) != _safe_int(
            later_progress_counts.get(axis), 0
        ):
            issues.append(f"core_axis_later_progress_count_mismatch:{axis}")
        expected_axis_source_quality = (
            "source_quality_gap_excluded"
            if axis_missing_count > 0 or axis_order_count > 0
            else "pass"
        )
        if axis_row.get("source_quality_status") != expected_axis_source_quality:
            issues.append(f"core_axis_source_quality_status_mismatch:{axis}")
        if terminal_count > 0:
            expected_causal_axes.append(axis)
        else:
            expected_no_signal_core_axes.append(axis)
    if causal_axes != expected_causal_axes:
        issues.append("causal_core_axis_partition_invalid")
    if [axis for axis in expected_axes if axis in no_signal_axes] != (
        expected_no_signal_core_axes
    ):
        issues.append("no_signal_core_axis_partition_invalid")
    if any(axis in observation_only_axes for axis in expected_axes):
        issues.append("core_axis_misrouted_to_observation_only")

    source_quality_gap = bool(
        exact_contract.get("status") == "source_quality_gap_excluded"
        or calculated_source_quality_gap
    )
    return {
        "status": (
            "invalid"
            if issues
            else ("source_quality_blocked" if source_quality_gap else "pass")
        ),
        "structural_issues": issues,
        "source_quality_gap": source_quality_gap,
        "exact_attempt_contract": exact_contract,
    }


def evidence_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def validate_submit_drought_contract(
    report: dict[str, Any], contract: dict[str, Any], *, require_current: bool = False
) -> dict[str, Any]:
    """Validate census, terminal coverage and the actual decision denominators.

    Old reports are readable only as archive diagnostics. Runtime consumers must
    explicitly require the current contract even for rolling historical dates.
    """
    if not isinstance(report, dict) or not isinstance(contract, dict):
        return {
            "status": "invalid",
            "structural_issues": ["malformed_exact_contract"],
            "source_quality_gap": True,
            "exact_attempt_contract": {},
        }
    current = (
        require_current
        or str(report.get("target_date") or "") >= CURRENT_CONTRACT_DATE
        or str(report.get("_decision_date") or "") >= CURRENT_CONTRACT_DATE
        or _safe_int(report.get("schema_version")) >= CURRENT_SCHEMA_VERSION
    )
    if current and _safe_int(report.get("schema_version")) != CURRENT_SCHEMA_VERSION:
        return {
            "status": "invalid",
            "structural_issues": ["current_schema_required"],
            "source_quality_gap": True,
            "exact_attempt_contract": {},
        }
    try:
        result = _validate_structure(report, contract)
        if result["status"] == "legacy_not_required":
            return result
        issues = result["structural_issues"]
        exact = result["exact_attempt_contract"]
        counts = exact.get("denominator_exact_attempt_counts") or {}
        exclusion = contract.get("cash_shortfall_exclusion")
        if exclusion is not None:
            raw = exclusion["raw_exact_attempt_contract"]
            excluded = exclusion["excluded_attempts"]
            raw_rows = {r["attempt_key"]: r for r in raw["attempt_ledger"]}
            keys = [r["attempt_key"] for r in excluded]
            if (
                exclusion.get("schema") != "submit_drought_cash_shortfall_exclusion_v1"
                or exclusion.get("runtime_effect") is not False
                or exclusion.get("excluded_attempt_count") != len(excluded)
                or len(set(keys)) != len(keys)
                or len(raw_rows) != len(raw["attempt_ledger"])
                or raw.get("attempt_count") != len(raw_rows)
            ):
                issues.append("cash_shortfall_exclusion_census_invalid")
            for row in excluded:
                source = raw_rows.get(row["attempt_key"], {})
                record_id = str(source.get("record_id") or "")
                stages = source.get("stages")
                if (
                    source.get("state") != "blocked"
                    or source.get("terminal_axis") != "UPSTREAM_GATE"
                    or record_id.lower()
                    in {
                        "", "0", "0.0", "none", "null", "unknown", "-",
                        "nan", "nat", "false", "true",
                    }
                    or not row["attempt_key"].startswith(f"id:{record_id}:cycle:")
                    or not isinstance(stages, list)
                    or len(stages) != len(set(stages))
                    or not set(stages) <= set(counts)
                    or "order_bundle_submitted" in stages
                    or source.get("terminal_stage") != "blocked_zero_qty"
                    or source.get("stages") != row.get("stages")
                    or row.get("terminal_stage") != source.get("terminal_stage")
                    or datetime.fromisoformat(row["terminal_at"]).date().isoformat()
                    != report.get("target_date")
                    or not cash_shortfall_reason(
                        row.get("evidence", {}), row["terminal_at"]
                    )
                    or cash_shortfall_reason(row["evidence"], row["terminal_at"])
                    != row.get("reason")
                ):
                    issues.append("cash_shortfall_exclusion_evidence_invalid")
            eligible = [
                r for r in raw["attempt_ledger"] if r["attempt_key"] not in set(keys)
            ]
            expected = {
                stage: sum(stage in r["stages"] for r in eligible) for stage in counts
            }
            if expected != counts or len(eligible) != exact.get("attempt_count"):
                issues.append("cash_shortfall_exclusion_partition_mismatch")
            # Filtering can renumber a record's derived cycle ordinal. Every
            # other source identity, lifecycle field and terminal must survive.
            def retained_row_digest(row):
                return evidence_digest(
                    {key: value for key, value in row.items() if key != "attempt_key"}
                )

            if sorted(map(retained_row_digest, eligible)) != sorted(
                map(retained_row_digest, exact.get("attempt_ledger", []))
            ):
                issues.append("cash_shortfall_exclusion_retained_lineage_mismatch")
        # V4 archive fixtures may not have a decision envelope; actual current
        # decisions always do. Never accept a contradictory envelope at any date.
        if current or "stage_unique" in contract:
            if contract.get("stage_unique") != counts:
                issues.append("exact_denominator_decision_mismatch")
            ratios = contract.get("ratios") or {}
            for name, numerator, denominator in (
                (
                    "submitted_to_ai_unique_pct",
                    "order_bundle_submitted",
                    "ai_confirmed",
                ),
                (
                    "submitted_to_budget_unique_pct",
                    "order_bundle_submitted",
                    "budget_pass",
                ),
                ("budget_to_ai_unique_pct", "budget_pass", "ai_confirmed"),
                ("latency_to_budget_unique_pct", "latency_pass", "budget_pass"),
            ):
                n, d = _safe_int(counts.get(numerator)), _safe_int(
                    counts.get(denominator)
                )
                expected = round(100 * n / d, 1) if d else 0.0
                actual = ratios.get(name)
                if actual != expected or isinstance(actual, bool):
                    issues.append(f"exact_ratio_mismatch:{name}")
            ai, budget, submitted = (
                counts.get(k, 0)
                for k in ("ai_confirmed", "budget_pass", "order_bundle_submitted")
            )
            critical = (ai >= 20 and submitted / ai < 0.20) or (
                budget >= 3 and submitted / budget <= 0.10
            )
            if contract.get("critical") is not bool(critical):
                issues.append("exact_critical_decision_mismatch")
        terminal = exact.get("axis_terminal_causal_attempt_counts") or {}
        events = exact.get("axis_exact_attempt_event_counts") or {}
        for axis in ENTRY_SUBMIT_DROUGHT_CORE_AXES:
            if _safe_int(terminal.get(axis)) > _safe_int(events.get(axis)):
                issues.append(f"exact_terminal_exceeds_events:{axis}")
        if current:
            if (
                report.get("_decision_date")
                and report.get("target_date") != report["_decision_date"]
            ):
                issues.append("current_source_date_mismatch")
            if contract.get("source_taxonomy_leakage") is True:
                issues.append("sentinel_source_taxonomy_conflict")
            if (
                exact.get("schema_version") != 3
                or exact.get("attempt_partition_policy")
                != "call_local_submit_or_parent_ordered_retry_v3"
            ):
                issues.append("current_attempt_partition_required")
            ledger = exact.get("attempt_ledger")
            if not isinstance(ledger, list):
                issues.append("attempt_ledger_missing")
                ledger = []
            keys = set()
            rebuilt_counts = dict.fromkeys(counts, 0)
            rebuilt_terminal = dict.fromkeys(ENTRY_SUBMIT_DROUGHT_CORE_AXES, 0)
            states = dict.fromkeys(
                ("blocked", "submitted", "pending", "unclassified"), 0
            )
            for row in ledger:
                key = row.get("attempt_key")
                stages = row.get("stages")
                state = row.get("state")
                axis = row.get("terminal_axis")
                if not isinstance(key, str) or not key or key in keys:
                    issues.append("attempt_ledger_identity_invalid")
                keys.add(key)
                record_id = str(row.get("record_id") or "")
                excluded_identity = (
                    state == "unclassified"
                    and not record_id
                    and stages == []
                    and str(key).startswith("unidentified_terminal:")
                )
                if not excluded_identity and (
                    record_id.lower()
                    in {
                        "",
                        "0",
                        "0.0",
                        "none",
                        "null",
                        "unknown",
                        "-",
                        "nan",
                        "nat",
                        "false",
                        "true",
                    }
                    or not str(key).startswith(f"id:{record_id}:cycle:")
                ):
                    issues.append("attempt_ledger_record_binding_invalid")
                if (
                    not isinstance(stages, list)
                    or len(stages) != len(set(stages))
                    or not set(stages) <= set(counts)
                    or state not in states
                ):
                    issues.append("attempt_ledger_row_invalid")
                    continue
                states[state] += 1
                for stage in stages:
                    rebuilt_counts[stage] += 1
                if state == "blocked":
                    if row.get("terminal_stage") not in TERMINAL_STAGES_BY_AXIS.get(
                        axis, set()
                    ):
                        issues.append("attempt_ledger_terminal_stage_invalid")
                    if axis not in rebuilt_terminal:
                        issues.append("attempt_ledger_terminal_invalid")
                    else:
                        rebuilt_terminal[axis] += 1
                elif axis:
                    issues.append("attempt_ledger_nonblocked_axis_invalid")
                if ("order_bundle_submitted" in stages) != (state == "submitted"):
                    issues.append("attempt_ledger_submit_state_invalid")
                if "latency_pass" in stages and "budget_pass" not in stages:
                    issues.append("attempt_ledger_latency_order_invalid")
                if "order_bundle_submitted" in stages and "latency_pass" not in stages:
                    issues.append("attempt_ledger_submit_order_invalid")
                for earlier, later in (
                    ("budget_pass", "latency_pass"),
                    ("latency_pass", "order_bundle_submitted"),
                ):
                    if (
                        earlier in stages
                        and later in stages
                        and stages.index(earlier) > stages.index(later)
                    ):
                        issues.append("attempt_ledger_progress_order_invalid")
            if rebuilt_counts != counts or rebuilt_terminal != terminal:
                issues.append("attempt_ledger_census_mismatch")
            expected_totals = {
                "attempt_count": len(ledger),
                "terminal_causal_attempt_count": states["blocked"],
                "submitted_attempt_count": states["submitted"],
                "pending_attempt_count": states["pending"],
                "unclassified_terminal_attempt_count": states["unclassified"],
            }
            for field, value in expected_totals.items():
                if _safe_int(exact.get(field), -1) != value:
                    issues.append(f"attempt_ledger_total_mismatch:{field}")
            if any(
                contract.get(k) is not False
                for k in (
                    "runtime_effect",
                    "allowed_runtime_apply",
                    "broker_order_submit_allowed",
                )
            ):
                issues.append("sentinel_runtime_authority_invalid")
        result["structural_issues"] = sorted(set(issues))
        if issues:
            result["status"] = "invalid"
        return result
    except (TypeError, ValueError, KeyError, OverflowError, AttributeError):
        return {
            "status": "invalid",
            "structural_issues": ["malformed_exact_contract"],
            "source_quality_gap": True,
            "exact_attempt_contract": {},
        }


def make_scope_evidence(
    report: dict[str, Any], scope: str, contract: dict[str, Any]
) -> dict[str, Any]:
    body = {
        "report_schema_version": report.get("schema_version"),
        "target_date": report.get("target_date"),
        "as_of": report.get("as_of"),
        "scope_key": scope,
        "contract": contract,
    }
    return {**body, "sha256": evidence_digest(body)}


def validate_scope_evidence(evidence: Any, *, source_date: str, scope: str) -> bool:
    if not isinstance(evidence, dict):
        return False
    try:
        body = {k: v for k, v in evidence.items() if k != "sha256"}
        if (
            body.get("target_date") != source_date
            or body.get("scope_key") != scope
            or evidence.get("sha256") != evidence_digest(body)
        ):
            return False
        if (
            date.fromisoformat(source_date).isoformat() != source_date
            or not source_date >= "2026-06-05"
            or datetime.fromisoformat(body.get("as_of", "")).date().isoformat()
            != source_date
        ):
            return False
        result = validate_submit_drought_contract(
            {
                "schema_version": body.get("report_schema_version"),
                "target_date": source_date,
            },
            body.get("contract"),
            require_current=True,
        )
        if (
            body.get("contract", {})
            .get("exact_attempt_contract", {})
            .get("summary_terminal_identity_gap_events", 0)
        ):
            return False
        # The producer excludes identifiable bad rows before building the ledger;
        # valid survivors remain usable. Malformed/non-isolatable evidence does not.
        return result["status"] in {"pass", "source_quality_blocked"}
    except (ValueError, TypeError, AttributeError):
        return False
