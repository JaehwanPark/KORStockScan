"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import hashlib


import json


import math


import re


from contextvars import ContextVar


from dataclasses import dataclass


from pathlib import Path


from typing import Any


from src.engine.lifecycle.retirement import (
    current_report_view,
    retired_artifact,
    retired_owner,
    retired_status,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]


REPORT_DIR = PROJECT_ROOT / "data" / "report"


THRESHOLD_CYCLE_EV_DIR = REPORT_DIR / "threshold_cycle_ev"


CODE_IMPROVEMENT_WORKORDER_DIR = PROJECT_ROOT / "docs" / "code-improvement-workorders"


CODE_IMPROVEMENT_WORKORDER_REPORT_DIR = REPORT_DIR / "code_improvement_workorder"


WORKORDER_SCHEMA_VERSION = 2


WORKORDER_PRODUCER_CONTRACT_VERSION = "code_improvement_workorder_producer_v8"


SOURCE_HASH_CONTRACT = "logical_source_content_v2"


IMPLEMENTED_STATUSES = {
    "implemented",
    "implemented_but_hold_sample",
    "implemented_but_waiting_sample",
    "implemented_submit_contract_verified",
    "implemented_source_quality_contract_available",
    "implemented_source_quality_contract_waiting_sample",
    "implemented_source_quality_gap_open",
}


ROOT_CAUSE_CLOSURE_STATUSES = {
    "implementation_done",
    "artifact_regeneration_required",
    "source_quality_blocked",
    "handoff_closed_root_cause_open",
    "root_cause_closed",
    "needs_followup_workorder",
}


TERMINAL_NON_IMPLEMENT_STATUSES = {
    "terminal_design_family_candidate",
    "terminal_deferred_evidence",
    "terminal_existing_family_evidence",
    "terminal_not_applicable_evidence",
    "terminal_rejected",
}


KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS = {
    "venue",
    "effective_venue",
    "market_session_bucket",
    "scanner_promotion_reanchor_effective_venue",
    "scanner_stale_backoff_canonical_effective_venue",
    "opening_rotation_no_pullback_continuation_effective_venue",
    "entry_order_flow_status",
    "tier_reason",
    "swing_micro_ws_quote_stale",
    "lifecycle_bucket_entry_bucket_key",
    "lifecycle_bucket_entry_bucket_id",
    "lifecycle_bucket_bucket_id",
    "entry_adm_cache_token",
    "entry_adm_bucket_token",
    "entry_adm_price_resolution_bucket",
    "pre_submit_liquidity_value",
    "overbought_guard_reason",
    "pre_submit_overbought_reason",
    "entry_score_source",
    "entry_score_excluded_reason",
    "entry_recheck_excluded_reason",
    "score_prior_band",
    "score_prior_confidence",
    "soft_stop_dynamic_grace_score_prior_band",
    "holding_exit_matrix_decision_alignment",
    "sim_pre_submit_overbought_reason",
    "broker_receipt_status",
    "fill_quality",
    "sell_order_exchange_resolution_reason",
}


DECISION_RANK = {
    "implement_now": 0,
    "attach_existing_family": 1,
    "design_family_candidate": 2,
    "defer_evidence": 3,
    "reject": 4,
}


_RETIRED_COMMON_TUNING_TOKENS = (
    "daily_threshold_cycle_report",
    "threshold_cycle_ev_report",
    "threshold_cycle_preopen_apply",
    "test_daily_threshold_cycle_report",
    "test_threshold_cycle_ev_report",
    "test_threshold_cycle_preopen_apply",
)


@dataclass(frozen=True)
class ClassifiedOrder:
    order: dict[str, Any]
    decision: str
    reason: str
    mapped_family: str | None
    route: str | None
    confidence: str | None
    automation_reentry: str
    decision_source: str | None = None


_SOURCE_READS: ContextVar[dict[str, str | None] | None] = ContextVar(
    "workorder_source_reads", default=None
)


class WorkorderSourceChanged(RuntimeError):
    pass


def _direct_family_order(order: dict[str, Any]) -> dict[str, Any] | None:
    """Remove retired common-tuning ownership from a manual direct-family order."""
    ownership = " ".join(
        str(order.get(key) or "")
        for key in (
            "source_report_type",
            "target_subsystem",
            "mapped_family",
            "threshold_family",
        )
    )
    if any(token in ownership for token in _RETIRED_COMMON_TUNING_TOKENS):
        return None
    sanitized = dict(order)
    sanitized["files_likely_touched"] = [
        path
        for path in order.get("files_likely_touched") or []
        if not any(token in str(path) for token in _RETIRED_COMMON_TUNING_TOKENS)
    ]
    sanitized["acceptance_tests"] = [
        command
        for command in order.get("acceptance_tests") or []
        if not any(token in str(command) for token in _RETIRED_COMMON_TUNING_TOKENS)
    ]
    sanitized["required_downstream"] = [
        owner
        for owner in order.get("required_downstream") or []
        if not any(token in str(owner) for token in _RETIRED_COMMON_TUNING_TOKENS)
    ]
    provenance = order.get("implementation_provenance")
    if isinstance(provenance, dict):
        provenance = dict(provenance)
        if "required_downstream" in provenance:
            provenance["required_downstream"] = [
                owner
                for owner in provenance.get("required_downstream") or []
                if not any(
                    token in str(owner) for token in _RETIRED_COMMON_TUNING_TOKENS
                )
            ]
        sanitized["implementation_provenance"] = provenance
    return sanitized


def _read_source_bytes(path: Path) -> bytes:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raw = None
    reads = _SOURCE_READS.get()
    if reads is not None:
        key = str(path.resolve())
        sha = hashlib.sha256(raw).hexdigest() if raw is not None else None
        if key in reads and reads[key] != sha:
            raise WorkorderSourceChanged(
                f"workorder_source_changed_between_reads:{path}"
            )
        reads[key] = sha
    if raw is None:
        raise FileNotFoundError(path)
    return raw


def _load_json(path: Path) -> dict[str, Any]:
    if retired_artifact(path):
        return {}
    try:
        payload = json.loads(_read_source_bytes(path))
    except WorkorderSourceChanged:
        raise
    except Exception:
        return {}
    return current_report_view(payload) if isinstance(payload, dict) else {}


def _file_fingerprint(path: Path, label: str) -> dict[str, Any]:
    exists = path.exists()
    payload = b""
    if exists:
        payload = path.read_bytes()
    stat = path.stat() if exists else None
    return {
        "label": label,
        "path": str(path),
        "exists": bool(exists),
        "size_bytes": int(stat.st_size) if stat else 0,
        "mtime_ns": int(stat.st_mtime_ns) if stat else None,
        "sha256": hashlib.sha256(payload).hexdigest() if exists else None,
    }


def _source_fingerprint(source_paths: dict[str, Path]) -> dict[str, Any]:
    files = [
        _file_fingerprint(path, label) for label, path in sorted(source_paths.items())
    ]
    reads = _SOURCE_READS.get() or {}
    for entry in files:
        key = str(Path(entry["path"]).resolve())
        if key in reads and reads[key] != entry["sha256"]:
            raise WorkorderSourceChanged(
                f"workorder_source_changed_after_read:{entry['label']}"
            )
    # Absolute release roots are deployment provenance, not source identity.
    # Managed releases share the same canonical files through different root
    # aliases, so binding the alias would create a new generation for identical
    # bytes and metadata.
    identity_files = [
        {key: value for key, value in entry.items() if key != "path"} for entry in files
    ]
    hash_input = json.dumps(
        identity_files, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    source_hash = hashlib.sha256(hash_input).hexdigest()
    return {
        "source_hash": source_hash,
        "generation_id": source_hash[:12],
        "files": files,
    }


def _generation_fingerprint(
    source_hash: str,
    *,
    max_orders: int,
    include_swing: bool,
    direct_family_only: bool,
) -> dict[str, Any]:
    inputs = {
        "source_hash": source_hash,
        "schema_version": WORKORDER_SCHEMA_VERSION,
        "producer_contract_version": WORKORDER_PRODUCER_CONTRACT_VERSION,
        "max_orders": max(1, int(max_orders)),
        "include_swing": bool(include_swing),
        "direct_family_only": bool(direct_family_only),
        "source_hash_contract": SOURCE_HASH_CONTRACT,
    }
    generation_hash = hashlib.sha256(
        json.dumps(
            inputs,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "generation_hash": generation_hash,
        "generation_id": generation_hash[:12],
        "inputs": inputs,
    }


def _previous_workorder_lineage(
    previous_report: dict[str, Any],
    current_orders: list[dict[str, Any]],
    current_non_selected_orders: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from src.engine.automation.postclose_workorder_contract import all_orders, digest

    previous_selected = previous_report.get("orders")
    previous_selected = previous_selected if isinstance(previous_selected, list) else []
    previous_selected_ids = {
        row["order_id"]
        for row in previous_selected
        if isinstance(row, dict) and isinstance(row.get("order_id"), str)
    }
    current_selected_ids = {
        row["order_id"]
        for row in current_orders
        if isinstance(row, dict) and isinstance(row.get("order_id"), str)
    }
    previous_orders = all_orders(previous_report)
    previous_by_id = {
        str(order.get("order_id")): order
        for order in previous_orders
        if isinstance(order, dict) and order.get("order_id") not in (None, "")
    }
    current_by_id = {
        str(order.get("order_id")): order
        for order in [*current_orders, *(current_non_selected_orders or [])]
        if isinstance(order, dict) and order.get("order_id") not in (None, "")
    }
    previous_ids = set(previous_by_id)
    current_ids = set(current_by_id)
    decision_changed = sorted(
        order_id
        for order_id in previous_ids & current_ids
        if previous_by_id[order_id].get("decision")
        != current_by_id[order_id].get("decision")
    )
    return {
        "previous_exists": bool(previous_report),
        "previous_generation_id": previous_report.get("generation_id"),
        "previous_source_hash": previous_report.get("source_hash"),
        "previous_generated_at": previous_report.get("generated_at"),
        "new_order_ids": sorted(current_ids - previous_ids),
        "removed_order_ids": sorted(previous_ids - current_ids),
        "unchanged_order_ids": sorted(current_ids & previous_ids),
        "decision_changed_order_ids": decision_changed,
        "contract_changed_order_ids": sorted(
            key
            for key in previous_ids & current_ids
            if digest(previous_by_id[key]) != digest(current_by_id[key])
        ),
        "comparison_scope": "all_selected_and_non_selected_native_orders",
        "new_selected_order_ids": sorted(
            current_selected_ids - previous_selected_ids, key=str
        ),
        "removed_selected_order_ids": sorted(
            previous_selected_ids - current_selected_ids, key=str
        ),
    }


def _conversion_lane_followup_orders(
    conversion_lane: dict[str, Any], *, limit: int = 20
) -> list[dict[str, Any]]:
    blockers = conversion_lane.get("conversion_blocker_rank")
    if not isinstance(blockers, list):
        return []
    orders: list[dict[str, Any]] = []
    actionable_classes = {
        "key_lineage",
        "submit_drought",
        "runtime_hook",
        "env_mapping",
        "post_apply_attribution",
        "bridge_contract",
        "source_quality",
    }
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        blocker_class = str(blocker.get("blocker_class") or "").strip()
        if blocker_class not in actionable_classes:
            continue
        candidate_id = str(blocker.get("conversion_candidate_id") or "").strip()
        if not candidate_id:
            continue
        safe_slug = _slug_with_hash(f"{blocker_class}_{candidate_id}")
        instrumentation_implemented = (
            blocker.get("blocker_runtime_effect") is False
            and blocker.get("blocker_allowed_runtime_apply") is False
            and str(blocker.get("blocker_resolution_status") or "") == "open"
            and bool(str(blocker.get("blocker_axis") or "").strip())
        )
        implementation_provenance = None
        if instrumentation_implemented:
            root_cause_signal = ":".join(
                part
                for part in (
                    "conversion_lane",
                    blocker_class,
                    str(blocker.get("blocker_axis") or "").strip(),
                    str(blocker.get("blocker_resolution_status") or "open").strip(),
                )
                if part
            )
            implementation_provenance = {
                "implementation_status": "implemented",
                "implemented_scope": "conversion_lane_blocker_axis_report_provenance",
                "blocker_axis": blocker.get("blocker_axis"),
                "blocker_resolution_status": blocker.get("blocker_resolution_status"),
                "root_cause_signal": root_cause_signal,
                "root_cause_acceptance_test": blocker.get("acceptance_test"),
                "root_cause_next_repair_action": blocker.get("next_repair_action"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "remaining_blocker_is_observation_or_policy_closure": True,
            }
        orders.append(
            {
                "order_id": f"order_conversion_lane_{safe_slug}",
                "title": f"Conversion lane blocker follow-up: {blocker_class} {candidate_id}",
                "source_report_type": "conversion_lane",
                "target_subsystem": "sim_to_real_conversion_lineage",
                "lifecycle_stage": "conversion",
                "threshold_family": "sim_to_real_conversion_lane",
                "mapped_family": "sim_to_real_conversion_lane",
                "route": "instrumentation_order",
                "improvement_type": f"conversion_{blocker_class}_blocker",
                "priority": _safe_int(blocker.get("conversion_impact_rank"), 999),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "conversion_candidate_id": candidate_id,
                "blocker_axis": blocker.get("blocker_axis"),
                "blocker_resolution_status": blocker.get("blocker_resolution_status"),
                "conversion_impact_rank": blocker.get("conversion_impact_rank"),
                "remaining_gap_count_before": blocker.get("remaining_gap_count"),
                "remaining_gap_count_after_expected": max(
                    0, _safe_int(blocker.get("remaining_gap_count"), 1) - 1
                ),
                "blocks_bounded_real_canary": True,
                "acceptance_test": blocker.get("acceptance_test"),
                "implementation_status": (
                    "implemented" if instrumentation_implemented else None
                ),
                "original_implementation_status": (
                    "implemented" if instrumentation_implemented else None
                ),
                "implementation_provenance": implementation_provenance,
                "intent": (
                    "Close the conversion critical-path blocker as source-only instrumentation/report/test work. "
                    "This does not create real order, provider, bot, cap, or threshold authority."
                ),
                "expected_ev_effect": "reduce remaining blocker count before bounded real canary can be requested",
                "evidence": [
                    f"conversion_candidate_id={candidate_id}",
                    f"blocker_class={blocker_class}",
                    f"conversion_impact_rank={blocker.get('conversion_impact_rank')}",
                    f"next_repair_action={blocker.get('next_repair_action')}",
                    f"acceptance_test={blocker.get('acceptance_test')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "files_likely_touched": [
                    "src/engine/automation/key_lineage_ledger.py",
                    "src/engine/automation/conversion_lane.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "forbidden_uses": [
                    "real_order_authority",
                    "provider_route_change",
                    "bot_restart",
                    "cap_release",
                    "runtime_threshold_mutation",
                    "broker_order_guard_change",
                ],
            }
        )
        if len(orders) >= limit:
            break
    return orders


def _intraday_ws_freshness_followup_orders(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    directives = report.get("workorder_directives")
    if not isinstance(directives, list):
        return []
    source_paths = [
        str(path) for path in (report.get("source_paths") or {}).values() if path
    ]
    orders: list[dict[str, Any]] = []
    implemented_state_statuses = {
        "closed_loop_instrumentation_active": "implemented_but_waiting_sample",
        "scanner_prefilter_and_exact_terminalization_implemented": (
            "implemented_but_waiting_sample"
        ),
        "scanner_candidate_prune_receipts_implemented_waiting_natural_generation": (
            "implemented_but_waiting_sample"
        ),
        "bounded_prune_rest_bbo_collector_implemented_waiting_next_pid_natural_episode_receipts": (
            "implemented_but_waiting_sample"
        ),
        "bounded_prune_rest_bbo_collector_schedule_receipts_observed": (
            "implemented_but_waiting_sample"
        ),
        "bounded_prune_rest_bbo_collector_runtime_receipts_observed": (
            "implemented_but_waiting_sample"
        ),
        "handoff_provenance_implemented_not_runtime_reflected": (
            "implemented_but_waiting_sample"
        ),
        "implemented_in_source_report": (
            "implemented_source_quality_contract_waiting_sample"
        ),
        "implemented_pending_new_dashboard_snapshot": (
            "implemented_source_quality_contract_waiting_sample"
        ),
    }
    for raw in directives:
        if not isinstance(raw, dict) or not raw.get("order_id"):
            continue
        implementation_state = str(raw.get("implementation_state") or "").strip()
        implementation_status = str(raw.get("implementation_status") or "").strip()
        if not implementation_status:
            implementation_status = implemented_state_statuses.get(
                implementation_state, ""
            )
        if (
            raw.get("order_id") == "order_ws_subscription_stale_repair_observability"
            and not implementation_status
        ):
            implementation_status = "implemented_source_quality_contract_waiting_sample"
            implementation_state = (
                "remove_reg_cooldown_receipts_implemented_waiting_natural_pid"
            )
        source_provenance = (
            raw.get("implementation_provenance")
            if isinstance(raw.get("implementation_provenance"), dict)
            else {}
        )
        source_decision = str(raw.get("decision") or "").strip()
        order = {
            **raw,
            "source_report_type": "intraday_ws_freshness_monitor",
            "lifecycle_stage": "entry",
            "target_subsystem": "scanner_runtime_freshness_funnel",
            "route": (
                "design_family_candidate"
                if source_decision == "design_family_candidate"
                else "instrumentation_order"
            ),
            "mapped_family": "scanner_runtime_freshness_funnel",
            "threshold_family": "scanner_runtime_freshness_funnel",
            "improvement_type": "scanner_funnel_source_quality_followup",
            "required_downstream": raw.get("required_downstream")
            or [
                "intraday_ws_freshness_monitor",
                "code_improvement_workorder",
                "runtime_approval_summary",
                "threshold_cycle_postclose_verification",
            ],
            "confidence": "intraday_unique_lineage_diagnostic",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "source_paths": source_paths,
            "implementation_status": implementation_status or None,
            "original_implementation_status": implementation_status or None,
            "implementation_provenance": {
                **source_provenance,
                "implementation_type": (
                    source_provenance.get("implementation_type")
                    or "intraday_ws_freshness_source_only_instrumentation"
                ),
                "source_decision": source_decision or None,
                "source_implementation_state": implementation_state or None,
                "source_next_action": raw.get("next_action"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "remaining_blocker_is_observation_or_policy_closure": bool(
                    implementation_status
                ),
                "root_cause_closure_status_hint": None,
            },
            "next_postclose_metric": (
                "The next natural session must regenerate unique promotion/prune lineages, "
                "handoff coverage, terminal outcomes, and executable-BBO source-quality status."
            ),
        }
        if implementation_status:
            order.update(
                {
                    "action_priority_class": "P3",
                    "resolution_mode": "natural_maturity",
                    "economic_eligibility": "pending_maturity",
                    "first_blocker": "future_natural_source_or_terminal_receipt",
                    "closure_owner": "intraday_ws_freshness_monitor",
                    "closure_test": order["next_postclose_metric"],
                    "eta": None,
                }
            )
        else:
            order.update(
                {
                    "action_priority_class": "P2",
                    "resolution_mode": "producer_repair",
                    "economic_eligibility": "blocked_structural",
                    "first_blocker": (
                        "scanner_source_capture_or_ws_repair_provenance_missing"
                    ),
                    "closure_owner": "intraday_ws_freshness_monitor",
                    "closure_test": (
                        (raw.get("acceptance_tests") or [None])[0]
                        if isinstance(raw.get("acceptance_tests"), list)
                        else None
                    ),
                    "eta": None,
                }
            )
        forbidden = raw.get("forbidden_uses")
        order["forbidden_uses"] = (
            list(forbidden)
            if isinstance(forbidden, list)
            else [str(forbidden)]
            if forbidden
            else []
        )
        orders.append(order)
    return orders


def _scanner_lookup_attention_economic_evidence(
    report: dict[str, Any],
) -> dict[str, Any] | None:
    """Project family-owned economics without recomputing or promoting them."""
    funnel = report.get("scanner_unique_funnel")
    cohorts = funnel.get("economic_cohorts") if isinstance(funnel, dict) else None
    selection = (
        cohorts.get("lookup_attention_selection") if isinstance(cohorts, dict) else None
    )
    if not isinstance(selection, dict):
        return None
    opportunity = selection.get("selection_opportunity_economics")
    primary = selection.get("primary_economics")
    actual = selection.get("actual_completed")
    opportunity = opportunity if isinstance(opportunity, dict) else {}
    primary = primary if isinstance(primary, dict) else {}
    actual = actual if isinstance(actual, dict) else {}
    if not any((opportunity, primary, actual)):
        return None

    opportunity_status = str(opportunity.get("status") or "").strip()
    comparison_status = (
        "measured_no_edge"
        if opportunity_status == "hold_no_edge"
        else "validated_edge"
        if opportunity_status in {"validated_edge", "economic_improvement_validated"}
        else "source_gap"
        if opportunity_status.startswith("source_")
        else "pending_maturity"
    )
    primary_gaps = [
        str(value) for value in (primary.get("source_gaps") or []) if str(value).strip()
    ]
    historical_unrecoverable = (
        "original_unselected_entry_recipe_quantity_guard_missing" in primary_gaps
    )
    publication = report.get("scanner_lookup_attention_publication")
    publication = publication if isinstance(publication, dict) else {}
    quality_handoff = report.get("postclose_quality_handoff")
    quality_handoff = quality_handoff if isinstance(quality_handoff, dict) else {}
    evidence = {
        "family": "scanner_lookup_attention",
        "source_report_type": "intraday_ws_freshness_monitor",
        "source_date": report.get("target_date"),
        "economic_artifact_sha256": selection.get("artifact_sha256")
        or quality_handoff.get("economic_section_sha256"),
        "opportunity": {
            "comparison_status": comparison_status,
            "metric_role": opportunity.get("metric_role"),
            "baseline_cost_adjusted_ev_pct": opportunity.get(
                "outgoing_snapshot_ev_pct"
            ),
            "candidate_cost_adjusted_ev_pct": opportunity.get(
                "incoming_snapshot_ev_pct"
            ),
            "paired_delta_ev_pct": opportunity.get("selection_opportunity_ev_pct"),
            "daily_delta_pct": opportunity.get("daily_incremental_opportunity_pct")
            or {},
            "daily_net_profit_krw": opportunity.get("daily_net_profit_krw"),
            "daily_net_profit_reason": opportunity.get("daily_net_profit_reason"),
            "paired_sample_count": opportunity.get("resolved_pair_count"),
            "paired_date_count": opportunity.get("resolved_date_count"),
            "cost_contract": selection.get("cost_contract"),
            "tail": None,
            "capital": None,
            "source_quality_gate": opportunity.get("source_quality_gate"),
            "resolution_mode": (
                "measured_no_edge"
                if comparison_status == "measured_no_edge"
                else "natural_maturity"
            ),
            "economic_eligibility": "eligible",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "actual_policy_comparison": {
            "comparison_status": ("source_gap" if primary_gaps else "pending_maturity"),
            "metric_role": "realized",
            "baseline_cost_adjusted_ev_pct": primary.get("baseline_budget_ev_pct"),
            "candidate_cost_adjusted_ev_pct": primary.get("candidate_budget_ev_pct"),
            "paired_delta_ev_pct": primary.get("paired_delta_ev_pct"),
            "baseline_daily_net_profit_krw": primary.get("baseline_net_pnl_krw"),
            "candidate_daily_net_profit_krw": primary.get("candidate_net_pnl_krw"),
            "source_gaps": primary_gaps,
            "first_blocker": primary_gaps[0] if primary_gaps else None,
            "resolution_mode": (
                "historical_unrecoverable"
                if historical_unrecoverable
                else "natural_maturity"
            ),
            "economic_eligibility": (
                "blocked_structural" if primary_gaps else "pending_maturity"
            ),
            "closure_owner": "KiwoomCommonHealthOpportunityCostAcceptance0917",
            "closure_test": selection.get("closure_test"),
            "eta": selection.get("eta"),
        },
        "observational_completed": {
            "comparison_status": "diagnostic_only",
            "metric_role": actual.get("metric_role"),
            "causal_uplift": actual.get("causal_uplift"),
            "book": actual.get("book"),
        },
        "policy_handoff": {
            "disposition": (
                "incumbent_preserved"
                if comparison_status == "measured_no_edge"
                else "apply_blocked"
            ),
            "source_evaluation_date": publication.get("source_evaluation_date"),
            "publication_date": publication.get("publication_date"),
            "effective_date": publication.get("effective_date"),
            "policy_artifact_sha256": publication.get("policy_artifact_sha256"),
        },
    }
    evidence["semantic_sha256"] = hashlib.sha256(
        json.dumps(
            evidence,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return evidence


def _market_census_followup_orders(report, target_date):
    """Intake exact-date native diagnostics without upgrading them to live orders."""
    from src.engine.monitoring.market_opportunity_review import report_sha256

    if not report:
        return []
    valid = False
    try:
        contract = report.get("metric_contract") or {}
        valid = (
            report.get("target_date") == target_date
            and report.get("report_type") == "market_opportunity_census"
            and report.get("schema_version")
            in {"market_opportunity_census_v4", "market_opportunity_census_v5"}
            and report.get("artifact_sha256") == report_sha256(report)
            and contract.get("runtime_effect") is False
            and contract.get("allowed_runtime_apply") is False
            and contract.get("actual_order_submitted") is False
            and contract.get("broker_order_forbidden") is True
            and contract.get("decision_authority")
            == "source_only_scanner_coverage_audit"
            and isinstance(report.get("diagnostic_followups"), list)
        )
    except (ValueError, TypeError, AttributeError):
        pass
    raw_orders = report.get("diagnostic_followups", []) if valid else []
    ids = [o.get("recommendation_id") for o in raw_orders if isinstance(o, dict)]
    valid = (
        valid
        and len(ids) == len(raw_orders)
        and all(
            isinstance(i, str) and re.fullmatch(r"market_census_[a-z0-9_]+", i)
            for i in ids
        )
        and len(ids) == len(set(ids))
    )
    valid = valid and all(
        o.get("target_date") == target_date
        and o.get("decision") == "objective_followup_required"
        and o.get("runtime_effect") is False
        and o.get("allowed_runtime_apply") is False
        and o.get("actual_order_submitted") is False
        and o.get("broker_order_forbidden") is True
        and o.get("intended_consumer") == "code_improvement_workorder"
        for o in raw_orders
    )
    if not valid:
        raw_orders = [
            {
                # This is the workorder producer's integrity diagnostic, not
                # an invented native recommendation from the invalid source.
                "recommendation_id": None,
                "reason": "missing_invalid_or_legacy_census_contract_no_authority",
                "evidence": {"source_date": report.get("target_date")},
            }
        ]
    return [
        {
            **{
                key: o[key]
                for key in (
                    "recommendation_id",
                    "target_date",
                    "scope",
                    "decision",
                    "owner",
                    "intended_consumer",
                    "implementation_scope",
                    "acceptance",
                    "files_likely_touched",
                    "acceptance_tests",
                    "required_downstream",
                    "reason",
                    "evidence",
                )
                if key in o
            },
            "order_id": (
                "order_" + o["recommendation_id"]
                if valid
                else "order_market_census_source_contract"
            ),
            "source_report_type": "market_opportunity_census",
            "source_artifact_sha256": report.get("artifact_sha256"),
            "decision_authority": "source_only_scanner_coverage_audit",
            "title": "External census scoped first-blocker review",
            "lifecycle_stage": "entry",
            "target_subsystem": "scanner_recall_instrumentation",
            "mapped_family": "scanner_recall_instrumentation",
            "route": "instrumentation_order",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "census_contract_valid": valid,
            "forbidden_uses": [
                "live_policy_apply",
                "threshold_mutation",
                "broker_order_submit",
                "bot_restart",
            ],
        }
        for o in raw_orders
    ]


def _repeat_unresolved_signature(order: dict[str, Any]) -> str | None:
    source_report_type = str(order.get("source_report_type") or "").strip()
    target_subsystem = str(order.get("target_subsystem") or "").strip()
    lifecycle_stage = str(order.get("lifecycle_stage") or "").strip()
    improvement_type = str(order.get("improvement_type") or "").strip()
    threshold_family = str(order.get("threshold_family") or "").strip()
    title_slug = _slug(str(order.get("title") or ""))
    identity_fields = [
        source_report_type,
        target_subsystem,
        lifecycle_stage,
        improvement_type,
        threshold_family,
        title_slug,
    ]
    if sum(1 for value in identity_fields if value) < 3:
        return None
    parts = [
        source_report_type,
        target_subsystem,
        lifecycle_stage,
        improvement_type,
        threshold_family,
        title_slug,
    ]
    return "sig:" + "|".join(parts)


def _repeat_info_count(repeat_info: Any) -> int:
    if isinstance(repeat_info, dict):
        return _safe_int(repeat_info.get("count"))
    return _safe_int(repeat_info)


def _repeat_info_primary_status(repeat_info: Any) -> str | None:
    if not isinstance(repeat_info, dict):
        return None
    status_counts = repeat_info.get("implementation_status_counts")
    if not isinstance(status_counts, dict) or not status_counts:
        return None
    status, _ = max(
        (
            (str(key), _safe_int(value))
            for key, value in status_counts.items()
            if str(key).strip()
        ),
        key=lambda pair: pair[1],
        default=("", 0),
    )
    return status or None


def _escalate_repeated_unresolved_orders(
    classified: list[ClassifiedOrder],
    *,
    repeat_counts: dict[str, dict[str, Any]],
    repeat_floor: int = 2,
) -> tuple[list[ClassifiedOrder], list[str]]:
    escalated: list[ClassifiedOrder] = []
    escalated_ids: list[str] = []
    unresolved_decisions = {
        "attach_existing_family",
        "design_family_candidate",
        "defer_evidence",
    }
    for item in classified:
        if retired_owner(item.order.get("source_report_type")):
            continue
        if (
            item.order.get("source_report_type") == "pipeline_event_verbosity"
            and item.decision == "defer_evidence"
        ):
            escalated.append(item)
            continue  # Same native diagnostic source gap is not a new code/provider order.
        order_id = str(item.order.get("order_id") or "").strip()
        signature = _repeat_unresolved_signature(item.order)
        repeat_keys = [order_id]
        if signature:
            repeat_keys.append(signature)
        repeat_key_counts = {
            key: _repeat_info_count(repeat_counts.get(key))
            for key in repeat_keys
            if key
        }
        repeat_key, repeat_count = max(
            repeat_key_counts.items(),
            key=lambda pair: pair[1],
            default=("", 0),
        )
        status = str(item.order.get("implementation_status") or "").strip()
        primary_history_status = _repeat_info_primary_status(
            repeat_counts.get(repeat_key)
        )
        implemented_status_present = _is_implemented_status(status)
        terminal_non_implement_status_present = _is_terminal_non_implement_status(
            status
        ) or _is_terminal_non_implement_status(primary_history_status)
        existing_family_only = (
            item.decision == "attach_existing_family"
            and bool(item.mapped_family)
            and not status
            and str(item.order.get("improvement_type") or "") != "source_quality_gap"
        )
        pattern_lab_design_only = (
            item.decision == "design_family_candidate"
            and item.order.get("source_report_type")
            in {
                "scalping_pattern_lab_automation",
                "swing_pattern_lab_automation",
                "swing_improvement_automation",
            }
            and not item.mapped_family
            and not status
            and not primary_history_status
        )
        pattern_lab_existing_family_evidence_only = (
            item.decision == "defer_evidence"
            and item.order.get("source_report_type")
            in {"scalping_pattern_lab_automation", "swing_pattern_lab_automation"}
            and bool(item.mapped_family)
            and str(item.order.get("route") or "")
            in {"existing_family", "attach_existing_family"}
            and str(item.order.get("improvement_type") or "")
            in {"threshold_family_input", "pattern_lab_observation"}
            and not status
        )
        manual_review_only = item.order.get(
            "source_report_type"
        ) == "codebase_performance_workorder" and str(
            item.order.get("performance_candidate_state")
            or item.order.get("candidate_state")
            or ""
        ).strip() in {
            "deferred",
            "rejected",
        }
        provenance = item.order.get("implementation_provenance") or {}
        if (
            order_id
            and repeat_count >= repeat_floor
            and item.decision in unresolved_decisions
            and not implemented_status_present
            and not terminal_non_implement_status_present
            and item.order.get("runtime_effect") is not True
            and item.decision_source != "implement_now_rejudge"
            and not existing_family_only
            and not pattern_lab_design_only
            and not pattern_lab_existing_family_evidence_only
            and not manual_review_only
            and item.order.get("source_report_type") != "market_opportunity_census"
        ):
            escalated_order = dict(item.order)
            original_status = status or primary_history_status or None
            provenance = escalated_order.get("implementation_provenance")
            if not isinstance(provenance, dict):
                provenance = {}
            escalated_order["original_implementation_status"] = original_status
            escalated_order["implementation_status"] = "repeat_unresolved_escalated"
            escalated_order["repeat_unresolved_escalation"] = {
                "repeat_count": repeat_count,
                "repeat_floor": repeat_floor,
                "repeat_key": repeat_key,
                "repeat_signature": signature,
                "previous_decision": item.decision,
                "previous_route": item.route,
                "implementation_status": original_status,
                "implementation_status_counts": (
                    (repeat_counts.get(repeat_key) or {}).get(
                        "implementation_status_counts"
                    )
                    if isinstance(repeat_counts.get(repeat_key), dict)
                    else {}
                ),
                "runtime_effect": escalated_order.get("runtime_effect"),
                "allowed_runtime_apply": escalated_order.get("allowed_runtime_apply"),
            }
            escalated_order["implementation_provenance"] = {
                **provenance,
                "repeat_unresolved_escalation": escalated_order[
                    "repeat_unresolved_escalation"
                ],
            }
            escalated.append(
                ClassifiedOrder(
                    order=escalated_order,
                    decision="implement_now",
                    reason=(
                        f"repeat unresolved automation finding appeared in {repeat_count} recent workorders; "
                        "promote to source-only implementation review instead of leaving it as passive evidence"
                    ),
                    mapped_family=item.mapped_family,
                    route="repeat_unresolved_escalation",
                    confidence=item.confidence or "repeat_unresolved",
                    automation_reentry=(
                        "After implementation, regenerate the source report, code improvement workorder, "
                        "threshold EV/runtime summary, and postclose verifier; runtime/order/provider/bot state "
                        "must remain unchanged."
                    ),
                )
            )
            escalated_ids.append(order_id)
        else:
            escalated.append(item)
    return escalated, sorted(escalated_ids)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _is_real_primary_sample_book(value: Any) -> bool:
    text = str(value or "").strip()
    return text == "real" or text.startswith("real_")


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip(
        "_"
    )
    return text[:80] or "unknown"


def _slug_with_hash(value: str, *, limit: int = 80) -> str:
    raw = str(value or "")
    normalized = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", raw.strip().lower()).strip("_")
    if not normalized:
        return "unknown"
    if len(normalized) <= limit:
        return normalized
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    keep = max(1, int(limit) - len(digest) - 1)
    return f"{normalized[:keep].rstrip('_')}_{digest}"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _source_path_enabled(path: Path, *, isolated_source_mode: bool) -> bool:
    if retired_artifact(path):
        return False
    if not isolated_source_mode:
        return True
    return not _is_relative_to(path, REPORT_DIR)


def _load_source_json(path: Path, *, isolated_source_mode: bool) -> dict[str, Any]:
    if not _source_path_enabled(path, isolated_source_mode=isolated_source_mode):
        return {}
    return _load_json(path)


def _load_prompt_research_source(
    path: Path, *, isolated_source_mode: bool
) -> dict[str, Any]:
    """Preserve self-hashed research and distinguish corrupt from absent input."""
    if not _source_path_enabled(path, isolated_source_mode=isolated_source_mode):
        return {}
    try:
        payload = json.loads(_read_source_bytes(path))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        return {"source_read_error": type(exc).__name__}
    return (
        payload
        if isinstance(payload, dict) and payload
        else {"source_read_error": "invalid_prompt_research_object"}
    )


def _load_market_census_source(
    path: Path, *, isolated_source_mode: bool
) -> dict[str, Any]:
    """Preserve self-hashed bytes' JSON value before authority/schema validation.

    Generic retirement projection must not rewrite nested audit evidence before
    verifying this source's integrity. Missing optional sources remain absent;
    existing malformed sources produce a visible integrity diagnostic.
    """
    if not _source_path_enabled(path, isolated_source_mode=isolated_source_mode):
        return {}
    try:
        payload = json.loads(_read_source_bytes(path))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        return {"source_read_error": "invalid_or_unreadable_census_json"}
    return (
        payload
        if isinstance(payload, dict) and payload
        else {"source_read_error": "census_object_missing"}
    )


def threshold_ev_report_path(target_date: str) -> Path:
    return THRESHOLD_CYCLE_EV_DIR / f"threshold_cycle_ev_{target_date}.json"


def code_improvement_workorder_paths(target_date: str) -> tuple[Path, Path]:
    base = f"code_improvement_workorder_{target_date}"
    return (
        CODE_IMPROVEMENT_WORKORDER_REPORT_DIR / f"{base}.json",
        CODE_IMPROVEMENT_WORKORDER_DIR / f"{base}.md",
    )


def _sanitize_producer_gap_order(order: dict[str, Any]) -> dict[str, Any]:
    sanitized = {**order, "source_report_type": "producer_gap_discovery"}
    sanitized.pop("runtime_hook_candidate_contract", None)
    if (
        str(sanitized.get("improvement_type") or "") == "ai_review_followup"
        and str(sanitized.get("route") or "") == "review_ai_output"
    ):
        evidence_text = "\n".join(str(item) for item in sanitized.get("evidence") or [])
        if (
            "audit_status=pass" in evidence_text
            and "forbidden_use_violations=[]" in evidence_text
            and sanitized.get("runtime_effect") is False
            and sanitized.get("allowed_runtime_apply") is False
            and sanitized.get("actual_order_submitted") is False
            and sanitized.get("broker_order_forbidden") is True
        ):
            sanitized["implementation_status"] = (
                "implemented_source_quality_contract_available"
            )
            sanitized["implementation_provenance"] = {
                "implementation_type": "producer_gap_ai_review_followup_source_only_provenance",
                "audit_status": "pass",
                "forbidden_use_violations": [],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "producer_gap_discovery_source_only_review",
                "root_cause_closure_status_hint": "root_cause_closed",
            }
    return sanitized


def _is_implemented_status(value: Any) -> bool:
    return str(value or "").strip() in IMPLEMENTED_STATUSES


def _is_terminal_non_implement_status(value: Any) -> bool:
    return str(value or "").strip() in TERMINAL_NON_IMPLEMENT_STATUSES


def _terminal_non_implement_status(item: ClassifiedOrder) -> str | None:
    status = str(item.order.get("implementation_status") or "").strip()
    if _is_implemented_status(status) or _is_terminal_non_implement_status(status):
        return status
    source_type = str(item.order.get("source_report_type") or "").strip()
    if item.decision == "attach_existing_family":
        provenance = (
            item.order.get("implementation_provenance")
            if isinstance(item.order.get("implementation_provenance"), dict)
            else {}
        )
        if (
            str(provenance.get("recommended_resolution") or "")
            == "mark_not_applicable_explicitly"
        ):
            return "terminal_not_applicable_evidence"
        if not status:
            return "terminal_existing_family_evidence"
        return None
    if item.decision == "design_family_candidate":
        if source_type in {
            "scalping_pattern_lab_automation",
            "swing_pattern_lab_automation",
            "swing_improvement_automation",
        }:
            return "terminal_design_family_candidate"
        return None
    if item.decision == "defer_evidence":
        if item.decision_source == "implement_now_rejudge":
            return "terminal_deferred_evidence"
        if source_type in {
            "scalping_pattern_lab_automation",
            "swing_pattern_lab_automation",
        } and str(item.order.get("improvement_type") or "").strip() in {
            "threshold_family_input",
            "pattern_lab_observation",
        }:
            return "terminal_deferred_evidence"
        if source_type in {"pattern_lab_ai_review", "codebase_performance_workorder"}:
            return "terminal_deferred_evidence"
        return None
    if item.decision == "reject":
        return "terminal_rejected"
    return None


def _root_cause_closure_status_for_order(order: dict[str, Any]) -> str | None:
    implementation_status = str(order.get("implementation_status") or "").strip()
    provenance = (
        order.get("implementation_provenance")
        if isinstance(order.get("implementation_provenance"), dict)
        else {}
    )
    hinted = str(provenance.get("root_cause_closure_status_hint") or "").strip()
    if hinted in ROOT_CAUSE_CLOSURE_STATUSES:
        return hinted
    if bool(provenance.get("artifact_regeneration_required")):
        return "artifact_regeneration_required"
    if implementation_status in {
        "repeat_unresolved_structural_blocker",
        "repeat_unresolved_escalated",
    }:
        return "needs_followup_workorder"
    if implementation_status.startswith("open_"):
        return "needs_followup_workorder"
    if _is_implemented_status(implementation_status):
        if (
            str(provenance.get("blocker_resolution_status") or "").strip() == "open"
            or bool(
                provenance.get("remaining_blocker_is_observation_or_policy_closure")
            )
            or bool(provenance.get("unresolved_root_cause_present"))
        ):
            return "handoff_closed_root_cause_open"
        sample_status = str(provenance.get("sample_status") or "").strip()
        if implementation_status in {
            "implemented_but_hold_sample",
            "implemented_but_waiting_sample",
            "implemented_source_quality_contract_waiting_sample",
        } or sample_status.startswith("waiting_"):
            return "implementation_done"
        return "root_cause_closed"
    if (
        bool(order.get("implementation_candidate"))
        or str(order.get("decision") or "").strip() == "implement_now"
    ):
        return "needs_followup_workorder"
    if str(order.get("decision") or "").strip() == "design_family_candidate":
        return "needs_followup_workorder"
    return None


def _root_cause_followup_contract(
    order: dict[str, Any], status: str | None
) -> dict[str, Any] | None:
    if status not in {
        "artifact_regeneration_required",
        "source_quality_blocked",
        "handoff_closed_root_cause_open",
        "needs_followup_workorder",
    }:
        return None
    provenance = (
        order.get("implementation_provenance")
        if isinstance(order.get("implementation_provenance"), dict)
        else {}
    )
    source_report_type = str(order.get("source_report_type") or "unknown_source")
    improvement_type = str(order.get("improvement_type") or "unknown_gap")
    blocker_axis = str(
        order.get("blocker_axis") or provenance.get("blocker_axis") or ""
    ).strip()
    blocker_state = str(
        order.get("blocker_resolution_status")
        or provenance.get("blocker_resolution_status")
        or "open"
    ).strip()
    signal = str(provenance.get("root_cause_signal") or "").strip()
    if not signal:
        signal = ":".join(
            part
            for part in (
                source_report_type,
                improvement_type,
                blocker_axis,
                blocker_state,
            )
            if part
        )
    acceptance_test = provenance.get("root_cause_acceptance_test") or order.get(
        "acceptance_test"
    )
    if not acceptance_test:
        acceptance_tests = order.get("acceptance_tests")
        if isinstance(acceptance_tests, list) and acceptance_tests:
            acceptance_test = acceptance_tests[0]
    if not acceptance_test:
        acceptance_test = (
            f"a new {source_report_type} artifact records {signal} as resolved and "
            "the owning verifier passes"
        )
    next_repair_action = (
        provenance.get("root_cause_next_repair_action")
        or order.get("next_repair_action")
        or f"collect new evidence for {signal} and re-run the owning verifier"
    )
    return {
        "status": status,
        "root_cause_signal": signal,
        "acceptance_test": acceptance_test,
        "next_repair_action": next_repair_action,
        "closure_requires_new_evidence": True,
        "implementation_only_closure_allowed": False,
    }


def _entry_submit_drought_implementation_marker(
    report: dict[str, Any],
    contract: dict[str, Any],
    lifecycle_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = (
        contract.get("required_downstream")
        if isinstance(contract.get("required_downstream"), list)
        else []
    )
    if not {
        "code_improvement_workorder",
        "runtime_approval_summary",
        "postclose_verifier",
    }.issubset({str(item) for item in required}):
        return {}
    classification = (
        report.get("classification")
        if isinstance(report.get("classification"), dict)
        else {}
    )
    root_cause = (
        classification.get("submit_drought_root_cause")
        if isinstance(classification.get("submit_drought_root_cause"), dict)
        else {}
    )
    quote_freshness = (
        root_cause.get("quote_freshness_attribution")
        if isinstance(root_cause.get("quote_freshness_attribution"), dict)
        else {}
    )
    latency_root_cause_counts = (
        root_cause.get("latency_root_cause_counts")
        if isinstance(root_cause.get("latency_root_cause_counts"), dict)
        else {}
    )
    observation_breakdown = (
        contract.get("observation_breakdown")
        if isinstance(contract.get("observation_breakdown"), dict)
        else {}
    )
    observation_axes = (
        observation_breakdown.get("axes")
        if isinstance(observation_breakdown.get("axes"), dict)
        else {}
    )
    exact_attempt_contract = (
        contract.get("exact_attempt_contract")
        if isinstance(contract.get("exact_attempt_contract"), dict)
        else {}
    )
    from src.engine.automation.submit_drought_contract import (
        validate_submit_drought_contract,
    )

    exact_validation = validate_submit_drought_contract(report, contract)
    exact_attempt_contract_invalid = exact_validation["status"] == "invalid"
    attempt_ledger = (
        exact_attempt_contract.get("attempt_ledger")
        if isinstance(exact_attempt_contract.get("attempt_ledger"), list)
        else []
    )
    unclassified_attempts = [
        row
        for row in attempt_ledger
        if isinstance(row, dict) and row.get("state") == "unclassified"
    ]
    # Before the call-local submit observer existed, a new scanner promotion
    # could supersede an AI-confirmed row without a terminal receipt.  Those
    # rows cannot be repaired retrospectively.  The current producer closes
    # every submit invocation with entry_submit_attempt_finished, so this
    # historical shape waits for a new natural receipt instead of repeatedly
    # generating the same P0 implementation order.
    historical_superseded_only = (
        bool(unclassified_attempts)
        and all(
            row.get("lineage_gap_reason") == "new_evaluation_without_previous_terminal"
            and not str(row.get("producer_attempt_id") or "").strip()
            for row in unclassified_attempts
        )
        and _safe_int(
            exact_attempt_contract.get("missing_exact_attempt_key_event_count"), 0
        )
        == 0
        and _safe_int(
            exact_attempt_contract.get("stage_order_violation_event_count"), 0
        )
        == 0
    )
    refresh_attempted_count = _safe_int(
        quote_freshness.get("refresh_attempted_count"), 0
    )
    refresh_applied_count = _safe_int(quote_freshness.get("refresh_applied_count"), 0)
    latency_pass_recovered_count = _safe_int(
        quote_freshness.get("latency_pass_recovered_count"), 0
    )
    current_primary = str(classification.get("primary") or "").strip()
    # Sentinel owns exact quote-refresh attribution; retired LDM is not a
    # second mandatory copy of the same operational evidence.
    ldm_quote_freshness_present = bool(quote_freshness)
    quote_freshness_inconsistent = (
        (refresh_attempted_count <= 0 and latency_pass_recovered_count > 0)
        or (refresh_attempted_count <= 0 and refresh_applied_count > 0)
        or refresh_applied_count > refresh_attempted_count
    )
    root_cause_open = (
        _safe_int(root_cause.get("unknown_latency_reason_count"), 0) > 0
        or bool(root_cause.get("unknown_latency_workorder_required"))
        or (refresh_attempted_count > 0 and not ldm_quote_freshness_present)
    )
    exact_attempt_source_quality_open = bool(
        exact_attempt_contract
        and exact_attempt_contract.get("status") != "pass"
        and not historical_superseded_only
    )
    if quote_freshness_inconsistent or exact_attempt_contract_invalid:
        root_cause_closure_status = "artifact_regeneration_required"
    elif exact_attempt_source_quality_open:
        root_cause_closure_status = "source_quality_blocked"
    elif root_cause_open:
        root_cause_closure_status = "handoff_closed_root_cause_open"
    else:
        root_cause_closure_status = "root_cause_closed"
    natural_receipt_pending = bool(
        historical_superseded_only
        and not quote_freshness_inconsistent
        and not exact_attempt_contract_invalid
        and not root_cause_open
    )
    implementation_status = (
        "implemented_source_quality_contract_waiting_sample"
        if natural_receipt_pending
        else (
            "implemented_source_quality_gap_open"
            if exact_attempt_source_quality_open or exact_attempt_contract_invalid
            else "implemented"
        )
    )
    return {
        **(
            {
                "action_priority_class": "P3",
                "resolution_mode": "natural_maturity",
                "economic_eligibility": "pending_maturity",
                "first_blocker": "future_call_local_submit_terminal_receipt",
                "closure_owner": "sniper_state_handlers._submit_watching_triggered_entry",
                "closure_test": (
                    "a new natural submit invocation carries call_local_submit_attempt_v1 "
                    "and finishes as submitted or one exact terminal block/reject"
                ),
            }
            if natural_receipt_pending
            else {}
        ),
        "implementation_status": implementation_status,
        "implementation_checks": [
            "buy_funnel_sentinel emits entry_submit_drought_contract",
            "code_improvement_workorder selects drought and weak-contract follow-ups",
            "required_downstream includes workorder intake, runtime summary, and verifier consumers",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ],
        "implementation_provenance": {
            "implementation_type": "source_only_report_provenance_handoff",
            "source_report_type": "buy_funnel_sentinel",
            "required_downstream": required,
            "weak_contract_matches": contract.get("weak_contract_matches") or [],
            "observation_breakdown": observation_breakdown,
            "core_handoff_axes": contract.get("core_handoff_axes") or [],
            "exact_attempt_contract": exact_attempt_contract,
            "observation_axis_status": {
                str(axis): (
                    axis_payload.get("status")
                    if isinstance(axis_payload, dict)
                    else None
                )
                for axis, axis_payload in observation_axes.items()
            },
            "root_cause_signal": current_primary or None,
            "root_cause_counts": latency_root_cause_counts,
            "quote_freshness_refresh_attempted_count": refresh_attempted_count,
            "quote_freshness_refresh_applied_count": refresh_applied_count,
            "quote_freshness_latency_pass_recovered_count": latency_pass_recovered_count,
            "quote_freshness_attribution_inconsistent": quote_freshness_inconsistent,
            "ldm_quote_freshness_attribution_present": ldm_quote_freshness_present,
            "artifact_regeneration_required": (
                quote_freshness_inconsistent or exact_attempt_contract_invalid
            ),
            "exact_attempt_contract_invalid": exact_attempt_contract_invalid,
            "exact_attempt_source_quality_open": exact_attempt_source_quality_open,
            "historical_superseded_attempt_count": (
                len(unclassified_attempts) if historical_superseded_only else 0
            ),
            "historical_superseded_only": historical_superseded_only,
            "current_terminal_capture": (
                "entry_submit_attempt_finished_call_local_submit_attempt_v1"
            ),
            "sample_status": (
                "waiting_new_call_local_submit_terminal_receipt"
                if natural_receipt_pending
                else None
            ),
            "root_cause_closure_status_hint": (
                "implementation_done"
                if natural_receipt_pending
                else root_cause_closure_status
            ),
            "runtime_effect": contract.get("runtime_effect"),
            "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            "broker_order_submit_allowed": contract.get("broker_order_submit_allowed"),
            "forbidden_uses": contract.get("forbidden_uses") or [],
        },
    }


def _entry_submit_weak_contract_implementation_marker(
    *,
    gap_type: str,
    contract: dict[str, Any],
    taxonomy_leakage_labels: list[str] | None = None,
    lifecycle_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = (
        contract.get("required_downstream")
        if isinstance(contract.get("required_downstream"), list)
        else []
    )
    if "code_improvement_workorder" not in {str(item) for item in required}:
        return {}
    # Archived LDM attribution cannot verify a current broker/receipt contract.
    stage_unique = (
        contract.get("stage_unique")
        if isinstance(contract.get("stage_unique"), dict)
        else {}
    )
    submitted_unique = _safe_int(stage_unique.get("order_bundle_submitted"), 0)
    if submitted_unique > 0 and gap_type == "source_taxonomy_contract_gap":
        return {
            "implementation_status": "pending_exact_source_taxonomy_verification",
            "implementation_checks": [
                "buy_funnel_sentinel weak contract workorder is source-only",
                "real order_bundle_submitted samples exist",
                "strategy/source/blocker taxonomy must be emitted or explicitly marked not applicable",
                "weak contract gap=source_taxonomy_contract_gap",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
            ],
            "implementation_provenance": {
                "implementation_type": "source_taxonomy_provenance_gap",
                "source_report_type": "buy_funnel_sentinel",
                "downstream_consumer": "code_improvement_workorder",
                "gap_type": gap_type,
                "weak_contract_matches": contract.get("weak_contract_matches") or [],
                "sample_status": "submitted_sample_requires_exact_taxonomy_verification",
                "submitted_unique": submitted_unique,
                "gap_confirmation": "not_established_by_submit_count",
                "runtime_effect": contract.get("runtime_effect"),
                "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            },
        }
    if submitted_unique > 0 and gap_type in {
        "broker_receipt_contract_gap",
        "fill_quality_contract_gap",
        "post_submit_contract_gap",
        "telegram_post_submit_contract_gap",
    }:
        return {
            "implementation_status": "pending_exact_post_submit_verification",
            "implementation_checks": [
                "buy_funnel_sentinel weak contract workorder is source-only",
                "real order_bundle_submitted samples exist",
                "broker/fill/post-submit provenance must join from broker order key instead of waiting for sample",
                f"weak contract gap={gap_type}",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
            ],
            "implementation_provenance": {
                "implementation_type": "post_submit_provenance_join_gap",
                "source_report_type": "buy_funnel_sentinel",
                "downstream_consumer": "code_improvement_workorder",
                "gap_type": gap_type,
                "weak_contract_matches": contract.get("weak_contract_matches") or [],
                "sample_status": "submitted_sample_requires_exact_join_verification",
                "submitted_unique": submitted_unique,
                "gap_confirmation": "not_established_by_submit_count",
                "runtime_effect": contract.get("runtime_effect"),
                "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            },
        }
    return {
        "implementation_status": "implemented_but_waiting_sample",
        "implementation_checks": [
            "buy_funnel_sentinel weak contract workorder is source-only",
            "code_improvement_workorder owns raw submit/receipt source repair",
            f"weak contract gap={gap_type}",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ],
        "implementation_provenance": {
            "implementation_type": "entry_submit_source_contract_waiting_real_sample",
            "source_report_type": "buy_funnel_sentinel",
            "downstream_consumer": "code_improvement_workorder",
            "gap_type": gap_type,
            "weak_contract_matches": contract.get("weak_contract_matches") or [],
            "sample_status": "waiting_real_broker_or_fill_sample",
            "runtime_effect": contract.get("runtime_effect"),
            "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
        },
    }


def _serialize_classified_order(item: ClassifiedOrder) -> dict[str, Any]:
    ldm_existing_source_handoff = (
        item.decision == "attach_existing_family"
        and str(item.order.get("target_subsystem") or "") == "lifecycle_decision_matrix"
    )
    implementation_status = _terminal_non_implement_status(item) or item.order.get(
        "implementation_status"
    )
    resolution_mode = item.order.get("resolution_mode")
    economic_eligibility = item.order.get("economic_eligibility")
    action_priority_class = item.order.get("action_priority_class")
    if not resolution_mode:
        if _is_implemented_status(implementation_status):
            resolution_mode = "natural_maturity"
            economic_eligibility = economic_eligibility or "pending_maturity"
            action_priority_class = action_priority_class or "P3"
        elif item.decision in {"implement_now", "design_family_candidate"}:
            resolution_mode = "producer_repair"
            economic_eligibility = economic_eligibility or "blocked_structural"
            action_priority_class = action_priority_class or "P2"
        else:
            resolution_mode = "retired_or_not_applicable"
            economic_eligibility = economic_eligibility or "not_applicable"
            action_priority_class = action_priority_class or "P4"
    acceptance_tests = item.order.get("acceptance_tests") or []
    closure_test = item.order.get("closure_test")
    if not closure_test and acceptance_tests:
        closure_test = acceptance_tests[0]
    first_blocker = item.order.get("first_blocker")
    if not first_blocker and economic_eligibility == "blocked_structural":
        first_blocker = (
            f"{item.order.get('source_report_type') or 'unknown'}:"
            f"{item.order.get('order_id') or 'unknown'}"
        )
    serialized = {
        "order_id": item.order.get("order_id"),
        "title": item.order.get("title"),
        "target_subsystem": item.order.get("target_subsystem"),
        "source_report_type": item.order.get("source_report_type"),
        "lifecycle_stage": item.order.get("lifecycle_stage"),
        "threshold_family": item.order.get("threshold_family"),
        "improvement_type": item.order.get("improvement_type"),
        "priority": item.order.get("priority"),
        "decision": item.decision,
        "decision_reason": item.reason,
        "derived_review_category": (
            "already_implemented_source_handoff"
            if ldm_existing_source_handoff
            else item.order.get("derived_review_category")
        ),
        "implementation_candidate": (
            False if ldm_existing_source_handoff else item.decision == "implement_now"
        ),
        "route": item.route,
        "mapped_family": item.mapped_family,
        "confidence": item.confidence,
        "intent": item.order.get("intent"),
        "expected_ev_effect": item.order.get("expected_ev_effect"),
        "action_priority_class": action_priority_class,
        "resolution_mode": resolution_mode,
        "economic_eligibility": economic_eligibility,
        "first_blocker": first_blocker,
        "closure_owner": item.order.get("closure_owner")
        or item.mapped_family
        or item.order.get("source_report_type"),
        "closure_test": closure_test,
        "eta": item.order.get("eta"),
        "economic_evidence_ref": item.order.get("economic_evidence_ref"),
        "evidence": item.order.get("evidence") or [],
        "required_downstream": item.order.get("required_downstream") or [],
        "weak_contract_matches": item.order.get("weak_contract_matches") or [],
        "next_postclose_metric": item.order.get("next_postclose_metric"),
        "files_likely_touched": item.order.get("files_likely_touched") or [],
        "acceptance_tests": acceptance_tests,
        "forbidden_uses": item.order.get("forbidden_uses") or [],
        "decision_authority": item.order.get("decision_authority"),
        "source_handoff_contract": item.order.get("source_handoff_contract"),
        "adm_issue_types": item.order.get("adm_issue_types") or [],
        "automation_reentry": item.automation_reentry,
        "runtime_effect": item.order.get("runtime_effect"),
        "allowed_runtime_apply": item.order.get("allowed_runtime_apply"),
        "actual_order_submitted": item.order.get("actual_order_submitted"),
        "broker_order_forbidden": item.order.get("broker_order_forbidden"),
        "strategy_effect": bool(item.order.get("strategy_effect")),
        "data_quality_effect": bool(item.order.get("data_quality_effect")),
        "tuning_axis_effect": bool(item.order.get("tuning_axis_effect")),
        "implementation_status": implementation_status,
        "original_implementation_status": item.order.get(
            "original_implementation_status"
        ),
        "implementation_checks": item.order.get("implementation_checks") or [],
        "implementation_id": item.order.get("implementation_id"),
        "explicit_redecision_required": item.order.get("explicit_redecision_required"),
        "conflict_resolution_acceptance_test": item.order.get(
            "conflict_resolution_acceptance_test"
        ),
        "implementation_provenance": item.order.get("implementation_provenance"),
        "diagnostic_actionability": item.order.get("diagnostic_actionability"),
        "diagnostic_provenance": item.order.get("diagnostic_provenance"),
        "repeat_unresolved_escalation": item.order.get("repeat_unresolved_escalation"),
        "longstanding_non_implement_review": item.order.get(
            "longstanding_non_implement_review"
        ),
        "longstanding_non_implement_action": item.order.get(
            "longstanding_non_implement_action"
        ),
        "structural_blocker_escalation": item.order.get(
            "structural_blocker_escalation"
        ),
        "parity_contract": item.order.get("parity_contract"),
        "source_bucket_id": item.order.get("source_bucket_id"),
        "conversion_candidate_id": item.order.get("conversion_candidate_id"),
        "blocker_axis": item.order.get("blocker_axis"),
        "blocker_resolution_status": item.order.get("blocker_resolution_status"),
        "next_repair_action": item.order.get("next_repair_action"),
        "conversion_impact_rank": item.order.get("conversion_impact_rank"),
        "remaining_gap_count_before": item.order.get("remaining_gap_count_before"),
        "remaining_gap_count_after_expected": item.order.get(
            "remaining_gap_count_after_expected"
        ),
        "blocks_bounded_real_canary": item.order.get("blocks_bounded_real_canary"),
        "acceptance_test": item.order.get("acceptance_test"),
        "runtime_hook_candidate_contract": item.order.get(
            "runtime_hook_candidate_contract"
        ),
        "stage_hook_candidate_contract": item.order.get(
            "stage_hook_candidate_contract"
        ),
        "initial_runtime_state": item.order.get("initial_runtime_state"),
        "requires_separate_runtime_apply_candidate": item.order.get(
            "requires_separate_runtime_apply_candidate"
        ),
        "raw_row_exclusion_context_classification": item.order.get(
            "raw_row_exclusion_context_classification"
        ),
        "raw_row_exclusion_context": item.order.get("raw_row_exclusion_context"),
        "raw_row_exclusion_data_sanitation_revalidated": item.order.get(
            "raw_row_exclusion_data_sanitation_revalidated"
        ),
        "producer_gap_closure_contract": item.order.get(
            "producer_gap_closure_contract"
        ),
        "terminal_disposition": item.order.get("terminal_disposition"),
    }
    from src.engine.automation.postclose_workorder_contract import AUTHORITY_FLAGS

    serialized.update(
        {key: item.order[key] for key in AUTHORITY_FLAGS if key in item.order}
    )
    if item.order.get("source_report_type") == "market_opportunity_census":
        serialized.update(
            {
                key: item.order.get(key)
                for key in (
                    "recommendation_id",
                    "source_artifact_sha256",
                    "target_date",
                    "scope",
                    "owner",
                    "intended_consumer",
                    "implementation_scope",
                    "acceptance",
                    "census_contract_valid",
                )
            }
        )
        serialized["source_decision"] = item.order.get("decision")
    if item.order.get("source_report_type") == "main_ai_prompt_optimizer":
        serialized.update(
            {
                key: item.order.get(key)
                for key in (
                    "recommendation_id",
                    "source_artifact_sha256",
                    "source_target_date",
                    "source_calibration_sha256",
                    "owner",
                    "parent_prompt_version",
                    "parent_prompt_hash",
                    "candidate_contract_sha256",
                    "effective_venue",
                    "session_bucket",
                    "case_ids",
                    "cost_evidence_by_case",
                    "proposal_content_sha256",
                    "proposed_appendix",
                    "counterexamples",
                    "patch_type",
                    "next_action",
                    "provider_authority",
                    "order_authority",
                    "runtime_authority",
                    "runtime_registry_mutation_allowed",
                    "provider_budget_increase_allowed",
                    "evidence_basis",
                    "rollback_prompt_hash",
                )
            }
        )
        serialized["source_decision"] = item.order.get("decision")
    root_cause_closure_status = _root_cause_closure_status_for_order(serialized)
    serialized["root_cause_closure_status"] = root_cause_closure_status
    serialized["root_cause_followup_contract"] = _root_cause_followup_contract(
        serialized, root_cause_closure_status
    )
    return serialized


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(token in lower for token in tokens)


_IMPLEMENT_ACCEPTANCE_PREFIXES = (
    "python -m pytest ",
    "pytest ",
    "python -m src.engine.sync_docs_backlog_to_project ",
    "python -m py_compile ",
)


def _normalized_acceptance_text(text: str) -> str:
    normalized = str(text or "").strip()
    if normalized.startswith("PYTHONPATH=. "):
        normalized = normalized[len("PYTHONPATH=. ") :]
    if normalized.startswith(".venv/bin/python "):
        normalized = "python " + normalized[len(".venv/bin/python ") :]
    if normalized.startswith("./.venv/bin/python "):
        normalized = "python " + normalized[len("./.venv/bin/python ") :]
    if normalized.startswith(".venv/bin/pytest "):
        normalized = "pytest " + normalized[len(".venv/bin/pytest ") :]
    if normalized.startswith("./.venv/bin/pytest "):
        normalized = "pytest " + normalized[len("./.venv/bin/pytest ") :]
    if normalized.startswith("venv/Scripts/python.exe "):
        normalized = "python " + normalized[len("venv/Scripts/python.exe ") :]
    return normalized


def _has_runnable_acceptance(order: dict[str, Any]) -> bool:
    for raw in order.get("acceptance_tests") or []:
        normalized = _normalized_acceptance_text(str(raw))
        if not any(
            normalized.startswith(prefix) for prefix in _IMPLEMENT_ACCEPTANCE_PREFIXES
        ):
            continue
        if normalized.startswith("pytest ") or normalized.startswith(
            "python -m pytest "
        ):
            parts = normalized.split()
            meaningful = [
                part
                for part in parts
                if part not in {"python", "-m", "pytest"} and not part.startswith("-")
            ]
            if not any(
                part.startswith(("src/tests/", "tests/"))
                or part.endswith("_test.py")
                or part.startswith("src/tests/test_")
                for part in meaningful
            ):
                continue
            return True
    return False


def _implement_now_rejudge(order: dict[str, Any]) -> tuple[str, str] | None:
    if _is_implemented_status(order.get("implementation_status")):
        return None
    if (
        order.get("source_report_type") == "pattern_lab_ai_review"
        and str(order.get("improvement_type") or "") == "automation_handoff_gap"
    ):
        return None
    issues = {
        str(item).strip()
        for item in (order.get("adm_issue_types") or [])
        if str(item).strip()
    }
    if issues and issues.issubset(
        {"joined_sample_below_sample_floor", "prompt_context_not_loaded"}
    ):
        return (
            "defer_evidence",
            "Entry ADM warning is waiting on clean sample/runtime observation, not a code implementation gap",
        )
    provenance = (
        order.get("implementation_provenance")
        if isinstance(order.get("implementation_provenance"), dict)
        else {}
    )
    if (
        str(provenance.get("recommended_resolution") or "")
        == "mark_not_applicable_explicitly"
    ):
        return (
            "attach_existing_family",
            "source coverage is present and the remaining bucket is an explicit not_applicable evidence classification",
        )
    files = order.get("files_likely_touched")
    file_count = (
        len([item for item in files if str(item).strip()])
        if isinstance(files, list)
        else 0
    )
    source_type = str(order.get("source_report_type") or "")
    if (
        source_type
        in {
            "lifecycle_decision_matrix_holding_bucket_attribution",
            "lifecycle_decision_matrix_exit_bucket_attribution",
        }
        and file_count <= 0
        and not _has_runnable_acceptance(order)
    ):
        return (
            "defer_evidence",
            "not code-actionable in this cycle: no files_likely_touched and no runnable acceptance tests",
        )
    tests = [
        str(item).strip()
        for item in (order.get("acceptance_tests") or [])
        if str(item).strip()
    ]
    if (
        tests
        and not _has_runnable_acceptance(order)
        and order.get("order_id") == "order_swing_lifecycle_observation_coverage"
    ):
        return (
            "defer_evidence",
            "not code-actionable in this cycle: acceptance contract is review text only, not an executable validation",
        )
    if (
        source_type == "pattern_lab_ai_review"
        and file_count <= 0
        and not _has_runnable_acceptance(order)
    ):
        return (
            "defer_evidence",
            "not code-actionable in this cycle: no files_likely_touched and no runnable acceptance tests",
        )
    return None


def _classify_order(
    order: dict[str, Any],
    *,
    finding_by_order_id: dict[str, dict[str, Any]],
    finding_by_title_slug: dict[str, dict[str, Any]],
    auto_family_order_ids: set[str],
    closed_instrumentation_order_families: dict[str, str],
) -> ClassifiedOrder:
    order_id = str(order.get("order_id") or "").strip()
    title = str(order.get("title") or "").strip()
    subsystem = str(order.get("target_subsystem") or "").strip()
    text = f"{order_id} {title} {subsystem}"
    finding = (
        finding_by_order_id.get(order_id)
        or finding_by_title_slug.get(_slug(title))
        or {}
    )
    route = str(finding.get("route") or order.get("route") or "").strip() or None
    mapped_family = (
        str(finding.get("mapped_family") or order.get("mapped_family") or "").strip()
        or None
    )
    confidence = (
        str(finding.get("confidence") or order.get("confidence") or "").strip() or None
    )
    closed_family = closed_instrumentation_order_families.get(order_id)
    if order_id == "order_latency_guard_miss_ev_recovery" and not bool(
        order.get("runtime_effect")
    ):
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="Independent latency calibration and aggregate join-gap inference are retired; retain existing BUY Funnel diagnostics only.",
            mapped_family="buy_funnel_sentinel",
            route="existing_family",
            confidence=confidence,
            automation_reentry="Next BUY Funnel postclose diagnostics retain block/pass reasons and source quality; no independent sample/join gate or runtime mutation.",
        )
    if (
        order.get("source_report_type") == "pipeline_event_verbosity"
        and not bool(order.get("runtime_effect"))
        and order.get("allowed_runtime_apply") is not True
    ):
        if (
            order.get("diagnostic_state")
            in {
                "missing_report",
                "resource_deferred",
                "bootstrap_required",
                "source_snapshot_changed",
                "v2_shadow_pending_flush",
            }
            or order.get("implementation_status") == "implemented"
        ):
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason="Existing native diagnostic owner remains OPEN; scoped source/resource/natural closure is required, not duplicate implementation or trading promotion.",
                mapped_family=mapped_family,
                route="instrumentation_order",
                confidence=confidence,
                automation_reentry=str(
                    order.get("closure_test")
                    or "Verify exact-date source and completed-window parity under the unchanged resource guard."
                ),
            )
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="pipeline event compaction V2 is report-only instrumentation; shadow means producer-summary observe mode, not trading shadow",
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry="Next postclose pipeline_event_verbosity report must show producer summary freshness and parity status.",
        )

    if closed_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="instrumentation/provenance contract is already implemented; keep as report source for the existing family",
            mapped_family=closed_family,
            route="existing_family",
            confidence=confidence,
            automation_reentry="Next postclose calibration consumes the implemented report/provenance fields; no runtime mutation.",
        )

    if bool(order.get("runtime_effect")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="automation order must remain runtime_effect=false; runtime_effect=true is treated as artifact error",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Reject artifact and regenerate the source automation report before implementation.",
        )

    rejudged = _implement_now_rejudge(order)
    if rejudged:
        decision, reason = rejudged
        return ClassifiedOrder(
            order=order,
            decision=decision,
            reason=reason,
            mapped_family=mapped_family
            or str(order.get("threshold_family") or "").strip()
            or None,
            route=(
                "existing_family"
                if decision == "attach_existing_family"
                else route or "evidence_wait"
            ),
            confidence=confidence,
            decision_source="implement_now_rejudge",
            automation_reentry=(
                "Keep the item out of the canonical implement_now queue; regenerated postclose reports and "
                "runner terminal dispositions must preserve the non-implement decision."
            ),
        )

    if (
        order.get("source_report_type") == "swing_improvement_automation"
        and order_id == "order_swing_entry_bottleneck_auto_resolution"
    ):
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "SWING_ENTRY_DROUGHT_CRITICAL is a source-only swing entry bottleneck handoff and must not be "
                "dropped by workorder selection limits"
            ),
            mapped_family=mapped_family or "swing_gatekeeper_accept_reject",
            route=route or "instrumentation_order",
            confidence=confidence or "consensus",
            automation_reentry=(
                "After implementation, regenerate swing audit, Swing LDM, bucket discovery, code workorder, "
                "EV/runtime summary, and postclose verifier; runtime/live order guards remain unchanged."
            ),
        )

    if (
        _is_implemented_status(order.get("implementation_status"))
        and order.get("source_report_type") != "codebase_performance_workorder"
    ):
        status = str(order.get("implementation_status") or "").strip()
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                f"instrumentation/report/provenance implementation status is {status}; keep the order as "
                "existing-family source evidence instead of re-implementing"
            ),
            mapped_family=mapped_family
            or str(order.get("threshold_family") or "").strip()
            or None,
            route="existing_family",
            confidence=confidence,
            automation_reentry=(
                f"Next postclose workorder should preserve implementation_status={status} and use the "
                "source metrics as provenance only."
            ),
        )

    if (
        order.get("source_report_type") == "intraday_ws_freshness_monitor"
        and str(order.get("decision") or "").strip() == "design_family_candidate"
        and route == "design_family_candidate"
    ):
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason=(
                "the executable-BBO consumer exists, but the depleted scanner cohort needs a reviewed "
                "capacity-bounded source-only collection design before implementation"
            ),
            mapped_family=mapped_family or "scanner_funnel_executable_bbo_source_only",
            route="design_family_candidate",
            confidence=confidence or "deterministic_source_gap",
            decision_source="intraday_ws_source_capture_design",
            automation_reentry=(
                "Keep runtime_effect=false and require reviewed WS item-budget, active-owner non-displacement, "
                "exact venue/session lineage, and >=95% BBO coverage before implementation closure."
            ),
        )

    if order.get("source_report_type") == "market_opportunity_census":
        return ClassifiedOrder(
            order=order,
            decision="defer_evidence",
            reason="Scoped diagnosis is not a proven code defect or live permission; resolve the exact first owner and source evidence before implementation.",
            mapped_family="scanner_recall_instrumentation",
            route="instrumentation_order",
            confidence="source_only_scoped_diagnostic",
            automation_reentry="Next exact-date census preserves native ID, scope, exclusions and hash; no changes to scanner or order guards.",
        )

    if order.get("source_report_type") == "codebase_performance_workorder":
        if _is_implemented_status(order.get("implementation_status")):
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason=(
                    "report-only performance implementation is already present in code; keep the order as provenance "
                    "and validate through regenerated reports/tests instead of re-implementing"
                ),
                mapped_family=mapped_family
                or "ops_performance_report_only_implemented",
                route=route or "existing_report_only_implementation",
                confidence=confidence,
                automation_reentry="Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.",
            )
        state = str(
            order.get("performance_candidate_state")
            or order.get("candidate_state")
            or ""
        ).strip()
        if state == "accepted":
            return ClassifiedOrder(
                order=order,
                decision="implement_now",
                reason="accepted codebase performance order is logic-preserving and report/workorder-only; implementation still requires parity tests",
                mapped_family=mapped_family,
                route=route or "performance_optimization_order",
                confidence=confidence,
                automation_reentry="After implementation, rerun the same artifact/report parity tests before postclose workorder refresh.",
            )
        if state == "deferred":
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason=str(
                    order.get("defer_reason")
                    or "performance order requires manual review before implementation"
                ),
                mapped_family=mapped_family,
                route=route or "performance_optimization_order",
                confidence=confidence,
                automation_reentry="Keep as deferred performance backlog until scope/risk is reviewed separately.",
            )
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason=str(
                order.get("defer_reason")
                or "performance order is outside current no-logic-change scope"
            ),
            mapped_family=mapped_family,
            route=route or "performance_optimization_order",
            confidence=confidence,
            automation_reentry="Do not implement from this workorder source.",
        )

    if order.get("source_report_type") in {
        "pattern_lab_currentness_audit",
        "pattern_lab_ai_review",
        "tuning_observability_summary",
    }:
        actionability = order.get("diagnostic_actionability") or {}
        if (
            order.get("source_report_type") == "pattern_lab_ai_review"
            and isinstance(actionability, dict)
            and actionability.get("schema") == "pattern_review_actionability_v1"
            and actionability.get("status") == "blocked_missing_evidence"
            and actionability.get("source_quality_resolved") is False
        ):
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason="Preserved AI gap claim lacks an exact failing source contract; a passing currentness check and generic pytest path do not authorize implementation",
                mapped_family=mapped_family or "pattern_lab_feedback_handoff",
                route="pattern_lab_ai_review_followup_evidence",
                confidence=confidence,
                automation_reentry="Identify the exact failing field/row and consumer under the existing Pattern Lab owner; preserve the provider response and existing daily call budget.",
            )
        if order.get("source_report_type") == "pattern_lab_ai_review" and order.get(
            "upstream_currentness_order_id"
        ):
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason="Deterministic AI review mirrors an exact native currentness repair; preserve the failure without duplicate implementation",
                mapped_family=mapped_family or "pattern_lab_feedback_handoff",
                route="pattern_lab_exact_currentness_evidence",
                confidence=confidence,
                automation_reentry=f"Close upstream order {order['upstream_currentness_order_id']} and regenerate currentness before clearing this evidence.",
            )
        if (
            order.get("source_report_type") == "pattern_lab_ai_review"
            and str(order.get("improvement_type") or "") == "ai_review_followup"
        ):
            material_pending = order.get("material_review_pending") is True
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason=(
                    "Pattern Lab primary inputs need a fresh exact-generation AI review; this is evidence pending, not implemented code or live approval"
                    if material_pending
                    else "Pattern Lab generic ai_review_followup is reviewer evidence for concrete source-quality "
                    "or handoff orders; do not duplicate it as a Codex implement_now item"
                ),
                mapped_family=mapped_family or "pattern_lab_feedback_handoff",
                route="pattern_lab_ai_review_followup_evidence",
                confidence=confidence or "parsed_ai_review_followup",
                automation_reentry=(
                    "Use the existing exact-date Pattern Lab review owner and persisted primary/one-retry budget. "
                    "Budget exhaustion or a terminal rejected/interrupted attempt remains explicitly unreviewed source-only; "
                    "do not reset capacity or call a provider during metadata-only refresh."
                    if material_pending
                    else "Keep as terminal review evidence until the concrete source-quality/handoff orders and "
                    "regenerated Pattern Lab AI review close the audit."
                ),
            )
        if (
            order.get("source_report_type") == "pattern_lab_ai_review"
            and str(order.get("improvement_type") or "") == "automation_handoff_gap"
        ):
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason=(
                    "Pattern Lab AI review automation_handoff_gap is coverage evidence for the currentness "
                    "handoff workorders; do not create duplicate implement_now items from the reviewer layer"
                ),
                mapped_family=mapped_family or "pattern_lab_feedback_handoff",
                route="pattern_lab_ai_review_handoff_evidence",
                confidence=confidence or "ai_two_pass_review",
                automation_reentry=(
                    "Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff "
                    "orders close and the regenerated AI review parses sufficient context."
                ),
            )
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="pattern lab audit/review/observability order is report/source-quality instrumentation only and must remain runtime_effect=false",
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence or "consensus",
            automation_reentry="After implementation, rerun pattern labs, currentness audit, workorder, EV, and propagation audit.",
        )

    if order.get("source_report_type") == "producer_gap_discovery":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "producer gap discovery high-priority order is source-only missing producer work; "
                "implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state"
            ),
            mapped_family=mapped_family,
            route=route or "implement_now",
            confidence=confidence or "ai_two_pass_review",
            automation_reentry=(
                "After implementation, rerun producer_gap_discovery, code improvement workorder, "
                "threshold EV, runtime summary, and postclose verifier."
            ),
        )

    if order.get("source_report_type") == "stage_hook_workorder_discovery":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "stage hook workorder discovery surfaced an implementation-ready hook scaffold; "
                "implementation starts disabled/source-only and requires a separate runtime apply candidate"
            ),
            mapped_family=mapped_family,
            route=route or "implement_now",
            confidence=confidence or "ai_tier2_review",
            automation_reentry=(
                "After implementation, rerun stage_hook_workorder_discovery, code improvement workorder, "
                "threshold EV, and postclose verifier; runtime/live order guards remain unchanged."
            ),
        )

    if order.get("source_report_type") == "conversion_lane":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "conversion lane blocker is source-only lineage/report/instrumentation work needed before any "
                "bounded real canary request can be considered"
            ),
            mapped_family=mapped_family or "sim_to_real_conversion_lane",
            route=route or "instrumentation_order",
            confidence=confidence or "conversion_kpi",
            automation_reentry=(
                "After implementation, rerun key_lineage_ledger, conversion_lane, code_improvement_workorder, "
                "tuning performance control tower, and postclose verifier; runtime/live order guards remain unchanged."
            ),
        )

    if order.get("source_report_type") in (
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
    ) and (
        route in ("auto_family_candidate", "design_family_candidate")
        or order_id in auto_family_order_ids
    ):
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason=(
                "pattern lab proposes source-only family design input; the existing dedicated strategy owner "
                "must validate exact cost-adjusted rolling economics, safety and PREOPEN mapping before runtime use"
            ),
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry=(
                "Keep as report-only family metadata and validate through lifecycle artifacts before any runtime "
                "approval artifact is considered."
            ),
        )

    if (
        order.get("source_report_type")
        == "lifecycle_decision_matrix_scale_in_bucket_attribution"
    ):
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; "
                "runtime scale-in changes still require a separate approval artifact"
            ),
            mapped_family=mapped_family or "lifecycle_decision_matrix_runtime",
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry=(
                "Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve "
                "scale-in bucket candidates/workorders without runtime mutation."
            ),
        )

    if (
        order.get("source_report_type")
        == "lifecycle_decision_matrix_lifecycle_flow_bucket_attribution"
    ):
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "LDM lifecycle-flow parent bucket workorder is source-only bundle attribution/handoff "
                "instrumentation; Greenfield real-env stays blocked until complete entry-submit-holding-exit "
                "flows pass the regenerated chain."
            ),
            mapped_family=mapped_family or "lifecycle_decision_matrix_runtime",
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry=(
                "Next postclose LDM, lifecycle bucket discovery, threshold EV, runtime approval summary, "
                "runtime apply bridge, and verifier must preserve lifecycle-flow parent bucket state."
            ),
        )

    if (
        order.get("source_report_type")
        == "lifecycle_bucket_discovery_source_dimension_rollup"
    ):
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "source-dimension gap rollup is visibility evidence; actionable emit/backfill gaps are tracked "
                "by dedicated lifecycle_bucket_discovery implement_now orders"
            ),
            mapped_family=mapped_family or "lifecycle_bucket_discovery",
            route=route or "source_dimension_rollup",
            confidence=confidence,
            automation_reentry=(
                "Next postclose checklist/workorder should keep source_dimension_gap_summary visible until "
                "actionable gaps are resolved or explicitly marked not applicable."
            ),
        )

    if order.get("source_report_type") == "lifecycle_bucket_discovery_quiet_gap_rollup":
        is_conflict_order = order.get("route") == "parent_conflict_exclusion_review"
        conflict_ready = is_conflict_order and bool(
            order.get("implementation_candidate")
        )
        if conflict_ready:
            return ClassifiedOrder(
                order=order,
                decision="implement_now",
                reason=(
                    "parent conflict resolution evidence is closed with resolution states and child "
                    "reclassification items; implementation is source-only output generation and does "
                    "not authorize runtime mutation"
                ),
                mapped_family=mapped_family or "lifecycle_bucket_discovery",
                route=route or "parent_conflict_resolution_implement_now",
                confidence=confidence or "postclose_discovery_source",
                automation_reentry=(
                    "After implementation, rerun lifecycle_bucket_discovery, code_improvement_workorder, "
                    "threshold EV, and postclose verifier. runtime_effect=false, allowed_runtime_apply=false."
                ),
            )
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "quiet gap rollup is visibility evidence for parent conflict/source-only/AI coverage review; "
                "it does not authorize a runtime patch by itself"
            ),
            mapped_family=mapped_family or "lifecycle_bucket_discovery",
            route=route or "quiet_gap_rollup",
            confidence=confidence,
            automation_reentry=(
                "Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is "
                "implemented, covered by parent policy, deferred for more sample, or explicitly rejected."
            ),
        )

    if order.get("improvement_type") == "observation_source_quality_warning_rollup":
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "observation source-quality warning rollup is evidence-only visibility for warnings outside "
                "the immediate implementation allowlist"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_warning_rollup",
            confidence=confidence,
            automation_reentry=(
                "Next postclose observation source-quality audit and workorder should preserve this warning "
                "until it is covered by a dedicated source-quality order or explicitly deferred."
            ),
        )

    if order.get("improvement_type") == "source_quality_hard_block_contract_gap":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "observation source-quality hard block prevents tuning/live-auto/runtime approval inputs until "
                "the producer contract gap is fixed and a new clean cutoff is recorded"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_gap",
            confidence=confidence or "audit",
            automation_reentry=(
                "After implementation, rerun observation_source_quality_audit, code improvement workorder, "
                "threshold EV, runtime approval summary, and postclose verifier; only post-cutoff raw may feed tuning."
            ),
        )

    if order.get("improvement_type") == "source_quality_raw_row_exclusion_producer_gap":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "raw row exclusion protected tuning inputs, but the producer/source-quality cause must be fixed "
                "or explicitly classified so future rows are not repeatedly excluded"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_raw_row_exclusion_producer_fix",
            confidence=confidence or "audit",
            automation_reentry=(
                "After implementation, rerun observation_source_quality_audit and code improvement workorder; "
                "raw_row_exclusion.excluded_row_count should fall or remaining exclusions must carry reviewed "
                "not_available/waiting_sample-only provenance."
            ),
        )

    if (
        order.get("improvement_type")
        == "source_quality_raw_row_exclusion_revalidated_closed"
    ):
        reopened_order = {
            **order,
            "terminal_disposition": None,
            "raw_row_exclusion_context_classification": None,
            "producer_gap_closure_contract": (
                "producer_fix_receipt_plus_post_fix_natural_zero_recurrence_required"
            ),
        }
        return ClassifiedOrder(
            order=reopened_order,
            decision="implement_now",
            reason=(
                "legacy data-sanitization closure cannot close its producer gap; "
                "a producer fix receipt and post-fix natural zero-recurrence sample remain required"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route="source_quality_raw_row_exclusion_producer_fix",
            confidence=confidence or "audit",
            automation_reentry=(
                "Keep the manifest as audit provenance and rerun the source-quality audit after producer repair; "
                "only a post-fix natural zero-recurrence sample can close the producer gap."
            ),
        )

    if (
        order.get("improvement_type")
        == "source_quality_raw_row_exclusion_limit_up_locked_context"
    ):
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "raw row exclusion is concentrated in a limit-up locked context; keep it as reviewed "
                "source-quality evidence and do not create an automatic producer-fix implementation"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "review_required_limit_up_locked_context",
            confidence=confidence or "audit",
            automation_reentry=(
                "Next postclose source-quality audit should reclassify only if the same intraday_range_pct=0 "
                "gap repeats in non-limit-up rows or independent high/low/candle source loss is proven."
            ),
        )

    if (
        order.get("improvement_type")
        == "source_quality_raw_row_exclusion_market_halt_context"
    ):
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "raw row exclusion is concentrated inside a confirmed market halt/circuit-breaker recovery "
                "window; keep it as reviewed source-quality evidence and do not create an automatic producer-fix "
                "implementation unless the gap repeats after normal flow resumes"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "review_required_market_halt_context",
            confidence=confidence or "audit",
            automation_reentry=(
                "Next postclose source-quality audit should reclassify only if the same intraday_range_pct=0 "
                "gap repeats outside the market halt/circuit-breaker recovery window."
            ),
        )

    if order.get("improvement_type") == "source_quality_unknown_token_provenance_gap":
        if order.get("economic_eligibility") == "not_applicable":
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason=(
                    "unknown-token rows are warning-only reviewed provenance and the owning audit still "
                    "allows tuning input; keep them visible without creating a false EV-blocking repair"
                ),
                mapped_family=mapped_family or "observation_source_quality_audit",
                route="existing_family",
                confidence=confidence or "audit",
                automation_reentry=(
                    "Reopen only if the owning audit marks tuning_input_allowed=false or identifies an "
                    "exact economic denominator field blocked by the unknown token."
                ),
            )
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "unknown-token source-quality warnings are not tuning hard blocks, but they must be traced to "
                "producer provenance or replaced with explicit not_available/insufficient_sample labels"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_warning_producer_fix",
            confidence=confidence or "audit",
            automation_reentry=(
                "After implementation, rerun observation_source_quality_audit and code improvement workorder; "
                "unknown_token_stage_count should fall or remaining unknowns must carry explicit reviewed provenance."
            ),
        )

    if order.get("source_report_type") == "lifecycle_bucket_discovery":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains "
                "blocked until the regenerated reports and verifier pass"
            ),
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry=(
                "After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime "
                "approval summary, threshold EV, and postclose verifier."
            ),
        )

    if _contains_any(text, ("fallback", "shadow")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="fallback revival or shadow reintroduction conflicts with current Plan Rebase policy",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Keep as rejected finding unless translated into report_only_calibration or bounded canary design.",
        )

    if confidence == "solo":
        return ClassifiedOrder(
            order=order,
            decision="defer_evidence",
            reason="single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Re-evaluate against the surviving strategy owner and daily EV report.",
        )

    if subsystem == "runtime_instrumentation" or route == "instrumentation_order":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="instrumentation/provenance work can improve attribution without direct runtime mutation",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, next postclose report must show source freshness or warning reduction.",
        )

    if route == "existing_family" or mapped_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="finding maps to an existing threshold family and should strengthen source metrics/provenance",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, intraday/postclose calibration should include the updated family input.",
        )

    if route == "auto_family_candidate" or order_id in auto_family_order_ids:
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason="finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Create report-only family metadata first; only later can auto_bounded_live consider it.",
        )

    return ClassifiedOrder(
        order=order,
        decision="defer_evidence",
        reason="route is not strong enough for immediate implementation",
        mapped_family=mapped_family,
        route=route,
        confidence=confidence,
        automation_reentry="Keep in generated workorder as deferred context and re-check after next daily EV report.",
    )


def _sort_classified(items: list[ClassifiedOrder]) -> list[ClassifiedOrder]:
    action_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}

    def priority_class(item: ClassifiedOrder) -> str:
        explicit = str(item.order.get("action_priority_class") or "")
        if explicit:
            return explicit
        if _is_implemented_status(
            _terminal_non_implement_status(item)
            or item.order.get("implementation_status")
        ):
            return "P3"
        if item.decision in {"implement_now", "design_family_candidate"}:
            return "P2"
        return "P4"

    return sorted(
        items,
        key=lambda item: (
            action_rank.get(priority_class(item), 99),
            DECISION_RANK.get(item.decision, 99),
            _safe_int(item.order.get("priority"), 999),
            str(item.order.get("order_id") or ""),
        ),
    )


def _holding_exit_counterfactual_contract_status(target_date: str) -> dict[str, Any]:
    return retired_status("holding_exit_decision_matrix")


def lifecycle_entry_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug_with_hash(
        str(item.get("bucket_key") or item.get("workorder_id") or "unknown")
    )
    return f"order_lifecycle_entry_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_entry_bucket_order_id(item: dict[str, Any]) -> str:
    """Backward-compatible wrapper for the entry-bucket workorder ID owner."""
    return lifecycle_entry_bucket_order_id(item)


ENTRY_POST_SUBMIT_WEAK_CONTRACT_ORDERS = (
    (
        "order_entry_post_submit_contract_gap_review",
        "Entry post-submit contract gap review",
        "post_submit_contract_gap",
        "Ensure pre-submit revalidation, cancel, and post-submit state transitions are observable.",
    ),
    (
        "order_entry_broker_receipt_contract_gap_review",
        "Entry broker receipt contract gap review",
        "broker_receipt_contract_gap",
        "Ensure real submitted orders bind broker receipt/order number/fill/cancel provenance.",
    ),
    (
        "order_entry_fill_quality_contract_gap_review",
        "Entry fill quality contract gap review",
        "fill_quality_contract_gap",
        "Ensure full fill, partial fill, slippage, limit fill, and no-fill outcomes are separated.",
    ),
    (
        "order_entry_telegram_post_submit_contract_gap_review",
        "Entry Telegram post-submit contract gap review",
        "telegram_post_submit_contract_gap",
        "Ensure BUY Telegram messages are emitted only for orders submitted to the broker path.",
    ),
    (
        "order_entry_source_taxonomy_contract_gap_review",
        "Entry source taxonomy contract gap review",
        "source_taxonomy_contract_gap",
        "Ensure scalping and swing blocker namespaces are separated in BUY funnel attribution.",
    ),
)


def _entry_post_submit_weak_contract_orders(
    *,
    evidence: list[str],
    contract: dict[str, Any],
    weak_contract_matches: list[Any],
    taxonomy_leakage_labels: list[str],
    lifecycle_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    required_downstream = contract.get("required_downstream") if contract else []
    orders: list[dict[str, Any]] = []
    for order_id, title, gap_type, intent in ENTRY_POST_SUBMIT_WEAK_CONTRACT_ORDERS:
        order_evidence = [
            *evidence,
            f"weak_contract_gap={gap_type}",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ]
        if order_id == "order_entry_source_taxonomy_contract_gap_review":
            order_evidence.append(f"taxonomy_leakage_labels={taxonomy_leakage_labels}")
        orders.append(
            {
                "order_id": order_id,
                "title": title,
                "source_report_type": "buy_funnel_sentinel",
                "target_subsystem": "runtime_instrumentation",
                "lifecycle_stage": "entry_submit",
                "route": "instrumentation_order",
                "mapped_family": "entry_submit_drought_attribution",
                "threshold_family": "entry_submit_drought_attribution",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                **_entry_submit_weak_contract_implementation_marker(
                    gap_type=gap_type,
                    contract=contract,
                    taxonomy_leakage_labels=taxonomy_leakage_labels,
                    lifecycle_report=lifecycle_report,
                ),
                "strategy_effect": gap_type,
                "data_quality_effect": "post_entry_contract_gap",
                "tuning_axis_effect": "source_quality_only",
                "expected_ev_effect": "none_direct_source_quality_only",
                "intent": intent,
                "evidence": order_evidence,
                "required_downstream": required_downstream,
                "weak_contract_matches": weak_contract_matches,
                "files_likely_touched": [
                    "src/engine/buy_funnel_sentinel.py",
                    "src/engine/scalping/main_lifecycle_paired.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "next_postclose_metric": (
                    "Entry post-submit weak contracts remain source-only workorders with runtime_effect=false "
                    "and allowed_runtime_apply=false until explicit implementation and verification."
                ),
            }
        )
    return orders


def _lifecycle_bucket_discovery_followup_orders(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    return []


def _pipeline_event_verbosity_followup_orders(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    if not report:
        return []
    state = str(report.get("state") or "").strip()
    recommended = str(report.get("recommended_workorder_state") or "").strip()
    raw_stream = (
        report.get("raw_stream") if isinstance(report.get("raw_stream"), dict) else {}
    )
    parity = report.get("parity") if isinstance(report.get("parity"), dict) else {}
    producer = (
        report.get("producer_summary")
        if isinstance(report.get("producer_summary"), dict)
        else {}
    )
    evidence = [
        f"state={state}",
        f"recommended_workorder_state={recommended}",
        f"raw_size_bytes={raw_stream.get('raw_size_bytes')}",
        f"high_volume_line_count={raw_stream.get('high_volume_line_count')}",
        f"high_volume_byte_share_pct={raw_stream.get('high_volume_byte_share_pct')}",
        f"producer_summary_exists={producer.get('exists')}",
        f"parity_ok={parity.get('ok')}",
        f"raw_derived_event_count={parity.get('raw_derived_event_count')}",
        f"producer_event_count={parity.get('producer_event_count')}",
    ]
    base = {
        "source_report_type": "pipeline_event_verbosity",
        "diagnostic_state": state,
        "source_date": report.get("target_date"),
        "implementation_status": report.get("implementation_status"),
        "closure_test": report.get("closure_test")
        or "Produce and verify the exact-date scoped diagnostic; no full wrapper or provider retry for unchanged evidence.",
        "required_downstream": [
            "pipeline_event_verbosity",
            "code_improvement_workorder",
            "runtime_approval_summary",
            "threshold_cycle_postclose_verification",
        ],
        "lifecycle_stage": "ops_volume_diagnostic",
        "target_subsystem": "runtime_instrumentation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "route": "instrumentation_order",
        "confidence": "consensus",
        "expected_ev_effect": "none_direct_ops_cpu_io_reduction_only",
        "next_postclose_metric": "pipeline_event_verbosity.parity.ok",
    }
    if recommended in {
        "open_shadow_order",
        "block_suppress_and_fix_shadow",
        "repair_source_contract",
        "await_exact_date_report",
        "raw_missing",
        "await_resource_for_scoped_diagnostic",
        "retry_stable_source_snapshot",
        "observe_pending_next_flush",
    }:
        return [
            {
                **base,
                "order_id": "order_pipeline_event_compaction_v2_shadow",
                "title": "Pipeline event compaction V2 shadow producer summary",
                "priority": 1,
                "intent": "Keep or repair producer-side high-volume diagnostic summary in shadow mode without raw suppression.",
                "evidence": evidence,
                "files_likely_touched": [
                    "src/utils/pipeline_event_logger.py",
                    "src/engine/pipeline_event_summary.py",
                    "src/engine/pipeline_event_verbosity_report.py",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py",
                ],
            }
        ]
    # Historical suppress-candidate artifacts cannot reopen the unreviewed
    # raw-discard path. Current work is source repair and lightweight summaries.
    return []


_LDM_MATCH_MISSING_ORDER_THRESHOLD = 5


def _sim_fill_and_match_report_contract_orders(
    ev_report: dict[str, Any], source_quality_report: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    calibration = (
        ev_report.get("calibration")
        if isinstance(ev_report.get("calibration"), dict)
        else {}
    )
    scalp_simulator = (
        ev_report.get("scalp_simulator")
        if isinstance(ev_report.get("scalp_simulator"), dict)
        else {}
    )
    if not scalp_simulator:
        scalp_simulator = (
            calibration.get("scalp_simulator")
            if isinstance(calibration.get("scalp_simulator"), dict)
            else {}
        )
    lifecycle_match = (
        scalp_simulator.get("lifecycle_bucket_match_aggregation")
        if isinstance(scalp_simulator.get("lifecycle_bucket_match_aggregation"), dict)
        else {}
    )
    swing_micro = (
        scalp_simulator.get("swing_micro_source_quality")
        if isinstance(scalp_simulator.get("swing_micro_source_quality"), dict)
        else {}
    )

    sim_quality = {}
    family_reports = (
        ev_report.get("family_reports")
        if isinstance(ev_report.get("family_reports"), list)
        else []
    )
    for family in family_reports:
        if not isinstance(family, dict):
            continue
        if str(family.get("family") or "") == "dynamic_entry_price_resolver":
            sim_quality = (
                family.get("sim_submit_path_quality")
                if isinstance(family.get("sim_submit_path_quality"), dict)
                else {}
            )
            break

    has_canonical_fill_price_gap = False
    unpriced_no_canonical_total = 0
    if sim_quality:
        for stage, data in sim_quality.items():
            if not isinstance(data, dict):
                continue
            defect = (
                data.get("canonical_sim_fill_price_defect_breakdown")
                if isinstance(
                    data.get("canonical_sim_fill_price_defect_breakdown"), dict
                )
                else {}
            )
            unpriced_no_canonical_total += _safe_int(
                defect.get("unpriced_no_canonical"), 0
            )
    has_canonical_fill_price_gap = unpriced_no_canonical_total > 0

    active_seed_none = _safe_int(
        lifecycle_match.get("active_seed_matched_none_count"), 0
    )
    eligible_active_seed_none = _safe_int(
        lifecycle_match.get("eligible_active_seed_matched_none_count"),
        active_seed_none,
    )
    contract_missing = _safe_int(lifecycle_match.get("contract_missing_count"), 0)
    policy_missing = _safe_int(
        lifecycle_match.get("eligible_policy_missing_count"),
        _safe_int(lifecycle_match.get("policy_missing_count"), 0),
    )
    not_instrumented = _safe_int(lifecycle_match.get("not_instrumented_count"), 0)
    prefix_parent_missing = _safe_int(
        lifecycle_match.get("active_seed_prefix_matched_parent_missing_count"), 0
    )
    natural_no_match = _safe_int(lifecycle_match.get("natural_no_match_count"), 0)
    hypothesis_no_match = _safe_int(
        lifecycle_match.get("hypothesis_matched_but_parent_bucket_no_match_count"), 0
    )
    panic_excluded = _safe_int(
        lifecycle_match.get("panic_scale_in_stage_excluded_count"), 0
    )
    provenance_gap = _safe_int(swing_micro.get("provenance_gap_count"), 0)
    missing_ws_quote = _safe_int(swing_micro.get("missing_ws_quote_source_count"), 0)

    source_quality_status = str(
        (source_quality_report or {}).get("status") or ""
    ).strip()
    source_quality_contract_gap = source_quality_status in {
        "fail",
        "missing",
        "incomplete",
    }

    base = {
        "source_report_type": "threshold_cycle_ev_report",
        "lifecycle_stage": "entry",
        "target_subsystem": "daily_threshold_cycle_report",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "expected_ev_effect": "Keep fill/EV denominator clean and ADM/LDM/sim matching contracts accurate without affecting real order authority.",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "cap_release",
        ],
    }

    if has_canonical_fill_price_gap:
        orders.append(
            {
                **base,
                "order_id": "order_sim_fill_canonical_price_contract_gap",
                "title": "Sim fill canonical price contract gap",
                "priority": 1,
                "route": "source_quality_gap",
                "mapped_family": "dynamic_entry_price_resolver",
                "threshold_family": "dynamic_entry_price_resolver",
                "improvement_type": "sim_fill_canonical_price_contract_gap",
                "confidence": "postclose_threshold_ev_source",
                "intent": "Priced sim fill rows must produce a canonical_sim_fill_price. Fix the producer or report contract so no priced row has unpriced_no_canonical classification.",
                "evidence": [
                    f"unpriced_no_canonical_total={unpriced_no_canonical_total}",
                    f"has_canonical_fill_price_gap={has_canonical_fill_price_gap}",
                ],
                "next_postclose_metric": "canonical_sim_fill_price_defect_breakdown.unpriced_no_canonical=0 for all priced stages",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/sniper_state_handlers.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_daily_threshold_cycle_report.py",
                ],
            }
        )

    if (
        contract_missing >= _LDM_MATCH_MISSING_ORDER_THRESHOLD
        or policy_missing >= _LDM_MATCH_MISSING_ORDER_THRESHOLD
        or prefix_parent_missing >= _LDM_MATCH_MISSING_ORDER_THRESHOLD
    ):
        orders.append(
            {
                **base,
                "order_id": "order_active_seed_or_ldm_match_missing_contract_gap",
                "title": "Contract/policy missing or active seed parent bridge missing above threshold",
                "priority": 1,
                "route": "source_quality_gap",
                "mapped_family": "lifecycle_decision_matrix_runtime",
                "threshold_family": "lifecycle_decision_matrix_runtime",
                "improvement_type": "active_seed_ldm_match_contract_gap",
                "confidence": "postclose_threshold_ev_source",
                "intent": "contract_missing indicates required instrumentation gap; policy_missing indicates policy/catalog handoff is unavailable for eligible lifecycle events; prefix_matched_parent_missing indicates active seed prefix found but parent lifecycle-flow approved row not closed. These must be diagnosed.",
                "evidence": [
                    f"contract_missing_count={contract_missing} (lifecycle-eligible stages only)",
                    f"eligible_policy_missing_count={policy_missing}",
                    f"not_instrumented_count={not_instrumented} (excluded: diagnostic/observation stages without lifecycle contract requirement)",
                    f"active_seed_prefix_matched_parent_missing_count={prefix_parent_missing}",
                    f"active_seed_matched_none_count={active_seed_none} (raw compatibility counter)",
                    f"eligible_active_seed_matched_none_count={eligible_active_seed_none}",
                    f"natural_no_match_count={natural_no_match} (excluded from workorder trigger)",
                    f"panic_scale_in_stage_excluded_count={panic_excluded} (excluded from workorder trigger)",
                    f"hypothesis_matched_but_parent_bucket_no_match_count={hypothesis_no_match} (includes natural_no_match + prefix_matched_parent_missing)",
                    f"ldm_match_missing_order_threshold={_LDM_MATCH_MISSING_ORDER_THRESHOLD}",
                ],
                "next_postclose_metric": "contract_missing_count < threshold AND eligible_policy_missing_count < threshold AND prefix_parent_missing_count < threshold",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/observation_source_quality_audit.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_observation_source_quality_audit.py",
                ],
            }
        )

    if (
        provenance_gap > 0
        and missing_ws_quote > 0
        and swing_micro.get("ready_count", 0) > 0
    ):
        orders.append(
            {
                **base,
                "order_id": "order_swing_micro_provenance_gap_missing_from_report",
                "title": "Swing micro ws_quote_source=missing provenance gap not surfaced in postclose report",
                "priority": 2,
                "route": "source_quality_gap",
                "mapped_family": "swing_micro_source_quality",
                "threshold_family": "swing_micro_source_quality",
                "improvement_type": "swing_micro_provenance_gap",
                "confidence": "postclose_threshold_ev_source",
                "intent": "Swing micro ws_quote_source=missing with orderbook_micro ready state is a provenance gap, not a readiness gap. Ensure it is tracked separately in postclose reports.",
                "evidence": [
                    f"provenance_gap_count={provenance_gap}",
                    f"missing_ws_quote_source_count={missing_ws_quote}",
                    f"ready_count={swing_micro.get('ready_count', 0)}",
                    f"wide_spread_count={swing_micro.get('wide_spread_count', 0)}",
                    f"ofi_outlier_count={swing_micro.get('ofi_outlier_count', 0)}",
                ],
                "next_postclose_metric": "swing_micro_source_quality.provenance_gap_count visible and ws_quote_source=missing not mixed with readiness",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/sniper_state_handlers.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_observation_source_quality_audit.py",
                ],
            }
        )

    if source_quality_contract_gap:
        orders.append(
            {
                **base,
                "order_id": "order_source_quality_report_contract_status_gap",
                "title": "Source quality report contract status failed/missing/incomplete",
                "priority": 0,
                "route": "source_quality_hard_gap",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "report_contract_gap",
                "confidence": "postclose_source_quality_fail",
                "intent": "Report contract status is failed/missing/incomplete. Tuning inputs using this report must be blocked until the contract is restored.",
                "evidence": [
                    f"source_quality_status={source_quality_status}",
                ],
                "next_postclose_metric": "observation_source_quality_audit status=pass or warning",
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )

    return orders


def _observation_source_quality_followup_orders(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    if not report:
        return []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    raw_row_exclusion = (
        report.get("raw_row_exclusion")
        if isinstance(report.get("raw_row_exclusion"), dict)
        else {}
    )
    raw_row_exclusion = _raw_row_exclusion_with_manifest_details(raw_row_exclusion)
    if (
        str(report.get("status") or "").strip() not in {"warning", "fail"}
        and int(raw_row_exclusion.get("excluded_row_count") or 0) <= 0
    ):
        return []
    hard_gaps = (
        report.get("hard_blocking_contract_gaps")
        if isinstance(report.get("hard_blocking_contract_gaps"), list)
        else []
    )
    stage_contracts = (
        report.get("stage_contracts")
        if isinstance(report.get("stage_contracts"), dict)
        else {}
    )
    high_volume_gaps = (
        report.get("high_volume_no_source_fields")
        if isinstance(report.get("high_volume_no_source_fields"), list)
        else []
    )
    unknown_token_findings = (
        report.get("unknown_token_findings")
        if isinstance(report.get("unknown_token_findings"), list)
        else []
    )

    def unknown_findings_covered_by_known_fix() -> bool:
        fields: set[str] = set()
        for finding in unknown_token_findings:
            if not isinstance(finding, dict):
                continue
            for field in finding.get("fields") or []:
                if isinstance(field, dict) and field.get("field"):
                    fields.add(str(field.get("field")))
        return bool(fields) and fields.issubset(KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS)

    warning_stages = [
        stage
        for stage, result in stage_contracts.items()
        if isinstance(result, dict) and result.get("status") == "warning"
    ]
    evidence = [
        f"status={report.get('status')}",
        f"event_count={summary.get('event_count')}",
        f"warning_stage_count={summary.get('warning_stage_count')}",
        f"warning_stages={','.join(warning_stages[:12])}",
        f"high_volume_no_source_field_stage_count={summary.get('high_volume_no_source_field_stage_count')}",
        f"unknown_token_stage_count={summary.get('unknown_token_stage_count')}",
        f"review_warning_count={summary.get('review_warning_count')}",
        "decision_authority=source_quality_only",
        "runtime_effect=false",
    ]
    base = {
        "source_report_type": "observation_source_quality_audit",
        "lifecycle_stage": "source_quality_gate",
        "target_subsystem": "runtime_instrumentation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "route": "instrumentation_order",
        "confidence": "audit",
        "expected_ev_effect": "none_direct_source_quality_attribution_only",
        "next_postclose_metric": "observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "cap_release",
            "hard_safety_relaxation",
        ],
    }
    orders: list[dict[str, Any]] = []
    if summary.get("tuning_input_allowed") is False or hard_gaps:
        hard_evidence = [
            *evidence,
            f"tuning_input_allowed={summary.get('tuning_input_allowed')}",
            f"blocked_reason={summary.get('blocked_reason')}",
            f"hard_blocking_contract_gap_count={summary.get('hard_blocking_contract_gap_count')}",
            f"hard_blocking_stages={','.join(str(stage) for stage in (summary.get('hard_blocking_stages') or [])[:20])}",
            "forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval until fixed",
            "required_acceptance_tests=source-quality audit pass, EV/runtime summary source_quality_gate pass_or_not_evaluated, postclose verifier pass",
        ]
        for gap in hard_gaps[:12]:
            if not isinstance(gap, dict):
                continue
            hard_evidence.append(
                "gap:"
                f"stage={gap.get('stage')} "
                f"reason={gap.get('reason')} "
                f"missing_fields={','.join(str(field) for field in (gap.get('missing_fields') or [])[:12]) or '-'} "
                f"sample_count={gap.get('sample_count')} "
                f"first_timestamp={gap.get('first_timestamp') or '-'} "
                f"last_timestamp={gap.get('last_timestamp') or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_hard_block_contract_gap",
                "title": "Observation source-quality hard block contract gap",
                "priority": 0,
                "route": "source_quality_gap",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "source_quality_hard_block_contract_gap",
                "intent": (
                    "Fix producer-side contract/provenance gaps before any affected raw row/window can feed EV, "
                    "rolling/MTD/cumulative tuning, live-auto promotion, or runtime approval."
                ),
                "evidence": hard_evidence,
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_threshold_cycle_ev_report.py src/tests/test_runtime_approval_summary.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
            }
        )
    excluded_row_count = int(raw_row_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count > 0:
        data_sanitation_revalidated = (
            report.get("status") in {"pass", "warning"}
            and summary.get("tuning_input_allowed") is True
            and "hard_blocking_contract_gap_count" in summary
            and "current_scan_hard_blocking_excluded_row_count" in summary
            and "post_exclusion_hard_blocking_excluded_row_count" in summary
            and int(summary.get("hard_blocking_contract_gap_count") or 0) == 0
            and int(summary.get("current_scan_hard_blocking_excluded_row_count") or 0)
            == 0
            and int(summary.get("post_exclusion_hard_blocking_excluded_row_count") or 0)
            == 0
            and summary.get("raw_row_exclusion_revalidation_required") is False
        )
        context_review = _raw_row_exclusion_limit_up_locked_context(raw_row_exclusion)
        market_halt_context_review = (
            None
            if context_review
            else _raw_row_exclusion_market_halt_context(raw_row_exclusion)
        )
        context_classification = None
        if context_review:
            context_classification = "limit_up_locked_context"
        elif market_halt_context_review:
            context_classification = "market_halt_or_circuit_window_overlap"
        stage_counts = (
            raw_row_exclusion.get("stage_counts")
            if isinstance(raw_row_exclusion.get("stage_counts"), dict)
            else {}
        )
        field_gap_counts = (
            raw_row_exclusion.get("field_gap_counts")
            if isinstance(raw_row_exclusion.get("field_gap_counts"), dict)
            else {}
        )
        exclusion_reasons = (
            raw_row_exclusion.get("exclusion_reasons")
            if isinstance(raw_row_exclusion.get("exclusion_reasons"), dict)
            else {}
        )
        producer_hint = (
            raw_row_exclusion.get("producer_hint")
            if isinstance(raw_row_exclusion.get("producer_hint"), list)
            else []
        )
        sample_rows = (
            raw_row_exclusion.get("sample_rows")
            if isinstance(raw_row_exclusion.get("sample_rows"), list)
            else []
        )
        raw_exclusion_evidence = [
            *evidence,
            f"raw_row_exclusion_manifest={raw_row_exclusion.get('manifest_path') or '-'}",
            f"excluded_row_count={excluded_row_count}",
            f"stage_counts={json.dumps(stage_counts, ensure_ascii=False, sort_keys=True)}",
            f"field_gap_counts={json.dumps(field_gap_counts, ensure_ascii=False, sort_keys=True)}",
            f"exclusion_reasons={json.dumps(exclusion_reasons, ensure_ascii=False, sort_keys=True)}",
            f"first_timestamp={raw_row_exclusion.get('first_timestamp') or '-'}",
            f"last_timestamp={raw_row_exclusion.get('last_timestamp') or '-'}",
            "forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval for excluded rows",
            "required_action=fix producer provenance/source-quality cause or mark reviewed_not_available/waiting_sample_only explicitly",
        ]
        if data_sanitation_revalidated:
            raw_exclusion_evidence.extend(
                [
                    "current_scan_hard_blocking_excluded_row_count=0",
                    "post_exclusion_hard_blocking_excluded_row_count=0",
                    "raw_row_exclusion_revalidation_required=false",
                    "data_sanitation_disposition=closed_preserved_manifest_audit_evidence",
                    "producer_gap_disposition=open_until_producer_fix_and_post_fix_natural_acceptance",
                ]
            )
        for hint in producer_hint[:12]:
            if isinstance(hint, dict):
                raw_exclusion_evidence.append(
                    "producer_hint:"
                    f"stage={hint.get('stage')} "
                    f"count={hint.get('count')} "
                    f"pipeline={hint.get('pipeline') or '-'} "
                    f"subsystem={hint.get('subsystem') or '-'} "
                    f"top_reasons={','.join(str(item) for item in (hint.get('top_reasons') or [])[:8]) or '-'}"
                )
        for row in sample_rows[:8]:
            if isinstance(row, dict):
                raw_exclusion_evidence.append(
                    "sample_row:"
                    f"line_no={row.get('line_no')} "
                    f"stage={row.get('stage')} "
                    f"record_id={row.get('record_id')} "
                    f"reasons={','.join(str(item) for item in (row.get('reasons') or [])[:8]) or '-'} "
                    f"gap_fields={json.dumps(row.get('gap_fields') or {}, ensure_ascii=False, sort_keys=True)}"
                )
        if context_review:
            raw_exclusion_evidence.extend(
                [
                    "context_classification=limit_up_locked_context",
                    f"context_evidence={json.dumps(context_review, ensure_ascii=False, sort_keys=True)}",
                    (
                        "required_action=review postclose only; do not auto-implement unless non-limit-up rows "
                        "repeat the same zero intraday range gap or independent high/low/candle source loss is proven"
                    ),
                ]
            )
        if market_halt_context_review:
            raw_exclusion_evidence.extend(
                [
                    "context_classification=market_halt_or_circuit_window_overlap",
                    f"context_evidence={json.dumps(market_halt_context_review, ensure_ascii=False, sort_keys=True)}",
                    (
                        "required_action=review postclose only; do not auto-implement unless the same zero "
                        "intraday range gap repeats after normal market flow resumes"
                    ),
                ]
            )
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                "title": (
                    "Observation source-quality raw row exclusion limit-up locked context"
                    if context_review
                    else (
                        "Observation source-quality raw row exclusion market halt context"
                        if market_halt_context_review
                        else "Observation source-quality raw row exclusion producer gap"
                    )
                ),
                "priority": 0,
                "route": (
                    "review_required_limit_up_locked_context"
                    if context_review
                    else (
                        "review_required_market_halt_context"
                        if market_halt_context_review
                        else "source_quality_raw_row_exclusion_producer_fix"
                    )
                ),
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": (
                    "source_quality_raw_row_exclusion_limit_up_locked_context"
                    if context_review
                    else (
                        "source_quality_raw_row_exclusion_market_halt_context"
                        if market_halt_context_review
                        else "source_quality_raw_row_exclusion_producer_gap"
                    )
                ),
                "intent": (
                    "Keep the excluded rows out of tuning inputs, but treat the current cluster as a reviewed "
                    "limit-up locked market context until non-limit-up evidence proves a producer gap."
                    if context_review
                    else (
                        (
                            "Keep the excluded rows out of tuning inputs, but treat the current cluster as a reviewed "
                            "market halt/circuit-breaker recovery context until post-resume evidence proves a producer gap."
                        )
                        if market_halt_context_review
                        else (
                            "Analyze all excluded raw rows by stage/field/reason and fix producer-side source-quality "
                            "or provenance causes so the postclose chain does not repeatedly need to exclude the same "
                            "class of rows from tuning inputs."
                        )
                    )
                ),
                "evidence": raw_exclusion_evidence,
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "raw_row_exclusion_context_classification": context_classification,
                "raw_row_exclusion_context": context_review
                or market_halt_context_review,
                "raw_row_exclusion_data_sanitation_revalidated": (
                    data_sanitation_revalidated
                ),
                "producer_gap_closure_contract": (
                    "producer_fix_receipt_plus_post_fix_natural_zero_recurrence_required"
                ),
                "terminal_disposition": (
                    "no_code_required_pending_policy_classification"
                    if context_classification
                    else None
                ),
            }
        )
    if unknown_token_findings:
        producer_fix_implemented = unknown_findings_covered_by_known_fix()
        unknown_blocks_tuning = summary.get("tuning_input_allowed") is False
        field_provenance = []
        for finding in unknown_token_findings:
            stage = str(finding.get("stage") or "")
            for field in finding.get("fields") or []:
                name = str(field.get("field") or "")
                # Scanner observations precede execution; integrated route is
                # not proof of which venue a broker subsequently filled.
                unavailable = name == "actual_execution_venue" and stage.startswith(
                    "scalping_scanner_"
                )
                fixed = name in KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS
                field_provenance.append(
                    {
                        "stage": stage,
                        "field": name,
                        "count": field.get("count"),
                        "rate": field.get("rate"),
                        "producer": (
                            "src/trading/market/quote_consistency.py"
                            if name.startswith("market_data_health")
                            else "src/engine/scalping/entry_candle_context.py"
                            if name.startswith("entry_candle_")
                            else "src/scanners/scanner_source_census.py"
                            if stage
                            in {
                                "scalping_scanner_source_fetch_census",
                                "scalping_scanner_candidate_pool_census",
                            }
                            else "src/scanners/scalping_scanner.py"
                            if name.startswith("scanner_market_gainer_")
                            or name.startswith("lookup_attention_")
                            or stage.startswith("scalping_scanner_")
                            else "src/engine/scalp_entry_adm_runtime.py"
                            if name.startswith("entry_adm_")
                            else "src/engine/scalping/ai_market_snapshot.py"
                            if name.startswith("ai_input_preflight_")
                            or name.startswith("ai_market_snapshot_")
                            else "src/engine/sniper_state_handlers.py"
                            if stage
                            in {
                                "watching_runtime_skip",
                                "ai_confirmed",
                                "ai_confirmed_terminal_no_budget",
                            }
                            else None
                        ),
                        "disposition": "reviewed_not_available_before_broker_execution"
                        if unavailable
                        else "implemented_waiting_new_postfix_raw"
                        if fixed
                        else "source_gap_requires_exact_producer_context",
                        "closure_test": "exact_stage_field_provenance_or_reviewed_unavailable_in_new_natural_source",
                        "runtime_apply": False,
                        "eta": None,
                    }
                )
        remaining_fields = sorted(
            {
                row["field"]
                for row in field_provenance
                if row["disposition"] == "source_gap_requires_exact_producer_context"
            }
        )
        unknown_evidence = [
            *evidence,
            "unknown_token_policy=warning_only_not_tuning_hard_block",
            "required_action=producer_provenance_fix_or_explicit_reviewed_not_available_label",
            "forbidden_uses=ignore_unknown_token_warning/silent_tuning_promotion_without_review",
        ]
        top_fields: list[str] = []
        for finding in unknown_token_findings:
            if not isinstance(finding, dict):
                continue
            fields = (
                finding.get("fields") if isinstance(finding.get("fields"), list) else []
            )
            field_bits = []
            for field in fields:
                if not isinstance(field, dict):
                    continue
                field_bits.append(
                    f"{field.get('field')}:{field.get('count')}:{field.get('rate')}"
                )
                top_fields.append(str(field.get("field") or ""))
            unknown_evidence.append(
                "unknown:"
                f"stage={finding.get('stage')} "
                f"event_count={finding.get('event_count')} "
                f"fields={','.join(field_bits) or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_unknown_token_provenance_gap",
                "required_downstream": [
                    "observation_source_quality_audit",
                    "code_improvement_workorder",
                    "runtime_approval_summary",
                    "threshold_cycle_postclose_verification",
                ],
                "title": "Observation source-quality unknown-token provenance gap",
                "priority": 1,
                "route": "source_quality_warning_producer_fix",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "source_quality_unknown_token_provenance_gap",
                "intent": (
                    "Trace high-rate unknown-token warning fields back to their producers and replace silent "
                    "unknown placeholders with real provenance or explicit reviewed not_available/insufficient_sample "
                    "labels, without changing runtime thresholds, orders, provider route, bot state, or safety guards."
                ),
                "evidence": [
                    *unknown_evidence,
                    f"top_unknown_fields={','.join(item for item in top_fields if item)}",
                ],
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
                "implementation_status": (
                    "implemented_but_waiting_sample"
                    if producer_fix_implemented
                    else None
                ),
                "action_priority_class": ("P2" if unknown_blocks_tuning else "P4"),
                "resolution_mode": (
                    "producer_repair"
                    if unknown_blocks_tuning
                    else "retired_or_not_applicable"
                ),
                "economic_eligibility": (
                    "blocked_structural" if unknown_blocks_tuning else "not_applicable"
                ),
                "first_blocker": (
                    "unknown_token_blocks_tuning_input"
                    if unknown_blocks_tuning
                    else None
                ),
                "closure_owner": "observation_source_quality_audit",
                "closure_test": (
                    "reopen only when tuning_input_allowed=false and the exact affected economic field is named"
                ),
                "eta": None,
                "implementation_provenance": {
                    "field_provenance_review": field_provenance,
                    "remaining_unknown_fields": remaining_fields,
                    "source_target_date": report.get("target_date"),
                    "source_report_semantic_sha256": hashlib.sha256(
                        json.dumps(
                            report,
                            sort_keys=True,
                            ensure_ascii=True,
                            separators=(",", ":"),
                        ).encode()
                    ).hexdigest(),
                    "producer_fix_status": (
                        "implemented_waiting_new_postfix_raw"
                        if producer_fix_implemented
                        else "open_unknown_field_producer_fix_required"
                    ),
                    "fixed_unknown_fields": sorted(KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS),
                    "current_raw_contains_pre_fix_rows": producer_fix_implemented,
                    "unknown_token_blocks_tuning": unknown_blocks_tuning,
                },
            }
        )
    if any(
        stage in warning_stages
        for stage in ("ai_confirmed", "blocked_ai_score", "wait65_79_ev_candidate")
    ):
        orders.append(
            {
                **base,
                "order_id": "order_ai_source_quality_not_evaluated_provenance",
                "title": "AI source-quality not-evaluated provenance for cooldown and score50 paths",
                "priority": 1,
                "intent": (
                    "Mark cooldown/score50 AI events as not_evaluated with reason and inherit available "
                    "source-quality snapshots where appropriate, without changing score thresholds or provider route."
                ),
                "evidence": evidence,
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py src/tests/test_state_handler_fast_signatures.py",
                ],
            }
        )
    if high_volume_gaps:
        gap_stages = [
            str(item.get("stage"))
            for item in high_volume_gaps
            if isinstance(item, dict) and item.get("stage")
        ][:12]
        orders.append(
            {
                **base,
                "order_id": "order_high_volume_diagnostic_stage_contract_labels",
                "title": "High-volume diagnostic stage metric contract labels",
                "priority": 2,
                "intent": (
                    "Label high-volume funnel diagnostics as ops_volume_diagnostic or funnel_count with explicit "
                    "decision_authority, so they cannot be mistaken for threshold/order inputs."
                ),
                "evidence": [*evidence, f"gap_stages={','.join(gap_stages)}"],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    swing_warning_stages = [
        stage
        for stage in warning_stages
        if stage
        in {
            "swing_probe_state_persisted",
            "scale_in_price_p2_observe",
            "swing_scale_in_micro_context_observed",
            "scale_in_price_resolved",
            "swing_probe_scale_in_order_assumed_filled",
            "swing_sim_scale_in_order_assumed_filled",
        }
    ]
    if swing_warning_stages:
        stage_evidence: list[str] = []
        for stage in swing_warning_stages[:8]:
            contract = (
                stage_contracts.get(stage)
                if isinstance(stage_contracts.get(stage), dict)
                else {}
            )
            missing = (
                contract.get("missing_violations")
                if isinstance(contract.get("missing_violations"), dict)
                else {}
            )
            missing_fields = ",".join(str(key) for key in list(missing)[:8])
            stage_evidence.append(
                f"{stage}:sample_count={contract.get('sample_count')} missing_fields={missing_fields or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_swing_source_quality_micro_context_provenance",
                "title": "Swing source-quality micro context provenance",
                "priority": 2,
                "intent": (
                    "Route swing probe-state contract warnings and OFI/QI micro-context observer gaps as "
                    "source-quality workorders, including fresh WS quote provenance where available, without "
                    "changing swing thresholds, order submission, approval gates, or provider route."
                ),
                "evidence": [
                    *evidence,
                    f"swing_warning_stages={','.join(swing_warning_stages)}",
                    *stage_evidence,
                ],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py "
                    "src/tests/test_swing_model_selection_funnel_repair.py "
                    "src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    if (warning_stages or unknown_token_findings) and not orders:
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_warning_rollup",
                "title": "Observation source-quality warning rollup",
                "priority": 3,
                "route": "source_quality_warning_rollup",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "observation_source_quality_warning_rollup",
                "intent": (
                    "Keep source-quality warning stages visible even when they are outside the immediate "
                    "implementation allowlist; follow-up Codex review decides whether a patch is needed."
                ),
                "evidence": evidence,
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    return orders


def _raw_row_exclusion_with_manifest_details(
    raw_row_exclusion: dict[str, Any],
) -> dict[str, Any]:
    if not raw_row_exclusion:
        return {}
    enriched = dict(raw_row_exclusion)
    if enriched.get("stage_counts") and enriched.get("exclusion_reasons"):
        return enriched
    manifest_path = Path(str(enriched.get("manifest_path") or ""))
    if not manifest_path.exists():
        return enriched
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return enriched
    if isinstance(manifest, dict):
        for key in (
            "stage_counts",
            "field_gap_counts",
            "exclusion_reasons",
            "first_timestamp",
            "last_timestamp",
            "sample_rows",
            "producer_hint",
        ):
            if not enriched.get(key) and manifest.get(key):
                enriched[key] = manifest.get(key)
        if not enriched.get("stage_counts") or not enriched.get("exclusion_reasons"):
            fallback = _summarize_legacy_raw_row_exclusion_manifest(manifest)
            for key, value in fallback.items():
                if not enriched.get(key) and value:
                    enriched[key] = value
    return enriched


def _float_or_none(value: Any) -> float | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _manifest_excluded_rows(raw_row_exclusion: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_path = Path(str(raw_row_exclusion.get("manifest_path") or ""))
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = manifest.get("excluded_rows") if isinstance(manifest, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _raw_row_exclusion_limit_up_locked_context(
    raw_row_exclusion: dict[str, Any],
) -> dict[str, Any] | None:
    excluded_row_count = int(raw_row_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count <= 0:
        return None
    stage_counts = (
        raw_row_exclusion.get("stage_counts")
        if isinstance(raw_row_exclusion.get("stage_counts"), dict)
        else {}
    )
    relevant_stage_count = sum(
        int(stage_counts.get(stage) or 0)
        for stage in ("blocked_overbought", "blocked_strength_momentum")
    )
    if relevant_stage_count <= 0 or relevant_stage_count < max(
        1, int(excluded_row_count * 0.8)
    ):
        return None
    field_gap_counts = (
        raw_row_exclusion.get("field_gap_counts")
        if isinstance(raw_row_exclusion.get("field_gap_counts"), dict)
        else {}
    )
    zero_range_count = int(field_gap_counts.get("zero_fields:intraday_range_pct") or 0)
    if zero_range_count < max(1, int(excluded_row_count * 0.8)):
        return None
    exclusion_reasons = (
        raw_row_exclusion.get("exclusion_reasons")
        if isinstance(raw_row_exclusion.get("exclusion_reasons"), dict)
        else {}
    )
    if not exclusion_reasons.get("source_quality_blocker"):
        return None
    if not (
        exclusion_reasons.get("not_evaluated_context")
        or exclusion_reasons.get("insufficient_history")
    ):
        return None

    rows = _manifest_excluded_rows(raw_row_exclusion)
    if not rows:
        return None
    identity_counts: dict[str, int] = {}
    limit_up_rows = 0
    zero_range_rows = 0
    stages_seen: set[str] = set()
    stock_codes_seen: set[str] = set()
    for item in rows:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        fields = (
            payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
        )
        stage = str(payload.get("stage") or "")
        stages_seen.add(stage)
        stock_code = str(payload.get("stock_code") or "")
        if stock_code:
            stock_codes_seen.add(stock_code)
        identity = f"{stock_code}:{payload.get('record_id') or ''}"
        identity_counts[identity] = identity_counts.get(identity, 0) + 1
        fluctuation = _float_or_none(fields.get("fluctuation"))
        if fluctuation is not None and fluctuation >= 29.0:
            limit_up_rows += 1
        intraday_range = _float_or_none(fields.get("intraday_range_pct"))
        if intraday_range is not None and abs(intraday_range) < 1e-9:
            zero_range_rows += 1

    top_identity, top_identity_count = ("", 0)
    if identity_counts:
        top_identity, top_identity_count = max(
            identity_counts.items(), key=lambda item: item[1]
        )
    if limit_up_rows <= 0:
        return None
    if top_identity_count < max(1, int(len(rows) * 0.5)):
        return None
    if zero_range_rows < max(1, int(len(rows) * 0.5)):
        return None
    return {
        "classification": "limit_up_locked_context",
        "excluded_row_count": excluded_row_count,
        "relevant_stage_count": relevant_stage_count,
        "zero_intraday_range_count": zero_range_count,
        "manifest_row_count": len(rows),
        "manifest_limit_up_row_count": limit_up_rows,
        "manifest_zero_range_row_count": zero_range_rows,
        "top_identity": top_identity,
        "top_identity_count": top_identity_count,
        "stock_codes_sample": sorted(stock_codes_seen)[:8],
        "stages_seen": sorted(stages_seen),
        "required_followup": (
            "review_only_until_non_limit_up_zero_range_repeats_or_high_low_candle_source_loss_is_proven"
        ),
    }


def _raw_row_exclusion_market_halt_context(
    raw_row_exclusion: dict[str, Any],
) -> dict[str, Any] | None:
    if raw_row_exclusion.get("market_halt_or_circuit_window_overlap") is not True:
        return None
    excluded_row_count = int(raw_row_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count <= 0:
        return None
    field_gap_counts = (
        raw_row_exclusion.get("field_gap_counts")
        if isinstance(raw_row_exclusion.get("field_gap_counts"), dict)
        else {}
    )
    zero_range_count = int(field_gap_counts.get("zero_fields:intraday_range_pct") or 0)
    if zero_range_count < max(1, int(excluded_row_count * 0.8)):
        return None
    context = (
        raw_row_exclusion.get("market_halt_or_circuit_context")
        if isinstance(raw_row_exclusion.get("market_halt_or_circuit_context"), dict)
        else {}
    )
    overlap_count = int(context.get("overlap_excluded_row_count") or 0)
    if overlap_count < max(1, int(excluded_row_count * 0.8)):
        return None
    return {
        **context,
        "classification": "market_halt_or_circuit_window_overlap",
        "excluded_row_count": excluded_row_count,
        "zero_intraday_range_count": zero_range_count,
        "required_followup": (
            "review_only_until_zero_range_repeats_after_normal_market_flow_resumes"
        ),
    }


def _summarize_legacy_raw_row_exclusion_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    rows = (
        manifest.get("excluded_rows")
        if isinstance(manifest.get("excluded_rows"), list)
        else []
    )
    stage_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    producer_hint: dict[str, dict[str, Any]] = {}
    timestamps: list[str] = []
    sample_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        fields = (
            payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
        )
        stage = str(payload.get("stage") or "-")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        if payload.get("emitted_at"):
            timestamps.append(str(payload.get("emitted_at")))
        reasons: set[str] = set()
        for key, value in fields.items():
            text = (
                json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
                if isinstance(value, (dict, list))
                else str(value).lower()
            )
            if (
                "source_quality_block" in text
                or str(key).lower() == "source_quality_blocker"
            ):
                reasons.add("source_quality_blocker")
            if "not_evaluated" in text:
                reasons.add("not_evaluated_context")
            if "insufficient_history" in text or "insufficient_sample" in text:
                reasons.add("insufficient_history")
            if "unknown" in text:
                reasons.add("unknown_token")
        if not reasons:
            reasons.add("row_contract_gap")
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        hint = producer_hint.setdefault(
            stage,
            {
                "stage": stage,
                "pipeline": payload.get("pipeline"),
                "subsystem": "runtime_instrumentation_producer",
                "count": 0,
                "top_reasons": [],
            },
        )
        hint["count"] += 1
        if len(sample_rows) < 10:
            sample_rows.append(
                {
                    "line_no": item.get("line_no"),
                    "stage": stage,
                    "emitted_at": payload.get("emitted_at"),
                    "record_id": payload.get("record_id"),
                    "stock_code": payload.get("stock_code"),
                    "reasons": sorted(reasons),
                    "gap_fields": {},
                    "source_quality_route": fields.get("source_quality_route"),
                    "source_quality_blocker": fields.get("source_quality_blocker"),
                    "threshold_family": fields.get("threshold_family"),
                }
            )
    for hint in producer_hint.values():
        hint["top_reasons"] = sorted(
            reason_counts, key=lambda key: (-reason_counts[key], key)
        )[:5]
    return {
        "stage_counts": dict(sorted(stage_counts.items())),
        "field_gap_counts": {},
        "exclusion_reasons": dict(sorted(reason_counts.items())),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
        "sample_rows": sample_rows,
        "producer_hint": sorted(
            producer_hint.values(),
            key=lambda item: (
                -int(item.get("count") or 0),
                str(item.get("stage") or ""),
            ),
        ),
    }


def _buy_funnel_sentinel_followup_orders(
    report: dict[str, Any],
    *,
    lifecycle_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not report:
        return []
    classification = (
        report.get("classification")
        if isinstance(report.get("classification"), dict)
        else {}
    )
    matches = (
        classification.get("matches")
        if isinstance(classification.get("matches"), list)
        else []
    )
    if (
        classification.get("primary") != "SUBMIT_DROUGHT_CRITICAL"
        and "SUBMIT_DROUGHT_CRITICAL" not in matches
    ):
        return []
    current = report.get("current") if isinstance(report.get("current"), dict) else {}
    scope_key = str(classification.get("scope_key") or "").strip()
    scope_reports = (
        current.get("by_venue_session")
        if isinstance(current.get("by_venue_session"), dict)
        else {}
    )
    selected_scope = (
        scope_reports.get(scope_key)
        if isinstance(scope_reports.get(scope_key), dict)
        else {}
    )
    session = (
        selected_scope.get("summary")
        if isinstance(selected_scope.get("summary"), dict)
        else current.get("session")
    )
    session = session if isinstance(session, dict) else {}
    ratios = session.get("ratios") if isinstance(session.get("ratios"), dict) else {}
    unique = (
        session.get("stage_unique")
        if isinstance(session.get("stage_unique"), dict)
        else {}
    )
    blockers = (
        session.get("blocker_top")
        if isinstance(session.get("blocker_top"), list)
        else []
    )
    upstream = (
        session.get("upstream_blocker_top")
        if isinstance(session.get("upstream_blocker_top"), list)
        else []
    )
    latency = (
        session.get("latency_blocker_top")
        if isinstance(session.get("latency_blocker_top"), list)
        else []
    )
    contract = (
        report.get("entry_submit_drought_contract")
        if isinstance(report.get("entry_submit_drought_contract"), dict)
        else {}
    )
    if isinstance(contract.get("required_downstream"), list):
        contract = {
            **contract,
            "required_downstream": [
                item
                for item in contract["required_downstream"]
                if not retired_owner(str(item))
            ],
        }
    implementation_marker = _entry_submit_drought_implementation_marker(
        report,
        contract,
        lifecycle_report=lifecycle_report,
    )
    weak_contract_matches = (
        contract.get("weak_contract_matches")
        if isinstance(contract.get("weak_contract_matches"), list)
        else []
    )
    evidence = [
        f"scope_key={scope_key or 'legacy_cross_venue'}",
        f"ai_confirmed_unique={_safe_int(unique.get('ai_confirmed'), 0)}",
        f"budget_pass_unique={_safe_int(unique.get('budget_pass'), 0)}",
        f"latency_pass_unique={_safe_int(unique.get('latency_pass'), 0)}",
        f"submitted_unique={_safe_int(unique.get('order_bundle_submitted'), 0)}",
        f"submitted_to_ai_pct={ratios.get('submitted_to_ai_unique_pct')}",
        f"submitted_to_budget_pct={ratios.get('submitted_to_budget_unique_pct')}",
    ]
    for label, items in (
        ("blocker", blockers),
        ("upstream", upstream),
        ("latency", latency),
    ):
        for item in items[:3]:
            if isinstance(item, dict):
                evidence.append(f"{label}:{item.get('label')}={item.get('count')}")
    orders = [
        {
            "order_id": "order_entry_submit_drought_auto_resolution",
            "title": "Entry submit drought automatic resolution handoff",
            "source_report_type": "buy_funnel_sentinel",
            "target_subsystem": "runtime_instrumentation",
            "lifecycle_stage": "entry_submit",
            "route": "instrumentation_order",
            "mapped_family": "entry_submit_drought_attribution",
            "threshold_family": "entry_submit_drought_attribution",
            "priority": 0,
            "action_priority_class": "P0",
            "resolution_mode": "producer_repair",
            "economic_eligibility": "blocked_structural",
            "first_blocker": "normal_submit_path_terminal_conservation_missing",
            "closure_owner": "buy_funnel_sentinel",
            "closure_test": (
                "same attempt identity reaches submitted or one exact terminal block/reject"
            ),
            "eta": None,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            **implementation_marker,
            "strategy_effect": "entry_submit_drought_handoff",
            "data_quality_effect": "funnel_root_cause_split_required",
            "tuning_axis_effect": "auto_surface_to_sentinel_and_workorder",
            "expected_ev_effect": "restore submitted coverage before evaluating EV edge",
            "intent": (
                "When submitted/ai is below the critical threshold, automatically create a Codex source-only workorder "
                "handoff so exact-attempt upstream, latency, Entry-AI authority, price revalidation, and broker receipt blockers are fixed "
                "or routed without operator approval."
            ),
            "evidence": evidence,
            "required_downstream": (
                [
                    item
                    for item in contract.get("required_downstream", [])
                    if not retired_owner(str(item))
                ]
                if isinstance(contract.get("required_downstream"), list)
                else [
                    "code_improvement_workorder",
                    "runtime_approval_summary",
                    "postclose_verifier",
                ]
            ),
            "weak_contract_matches": weak_contract_matches,
            "files_likely_touched": [
                "src/engine/buy_funnel_sentinel.py",
                "src/engine/build_code_improvement_workorder.py",
                "src/engine/verify_threshold_cycle_postclose_chain.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q "
                "src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py "
                "src/tests/test_runtime_approval_summary.py",
            ],
            "next_postclose_metric": (
                implementation_marker.get("closure_test")
                if implementation_marker.get("resolution_mode") == "natural_maturity"
                else (
                    "SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next "
                    "postclose Sentinel/runtime summary must show submit blocker attribution."
                )
            ),
        }
    ]
    taxonomy_leakage_labels = [
        str(item.get("label") or "")
        for item in blockers
        if isinstance(item, dict)
        and str(item.get("label") or "").startswith("blocked_swing_")
    ]
    orders.extend(
        _entry_post_submit_weak_contract_orders(
            evidence=evidence,
            contract=contract,
            weak_contract_matches=weak_contract_matches,
            taxonomy_leakage_labels=taxonomy_leakage_labels,
            lifecycle_report=lifecycle_report,
        )
    )
    return orders


def _closed_instrumentation_order_families(
    ev_report: dict[str, Any], *, target_date: str
) -> dict[str, str]:
    outcome = (
        ev_report.get("calibration_outcome")
        if isinstance(ev_report.get("calibration_outcome"), dict)
        else {}
    )
    decisions = (
        outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    )
    closed: dict[str, str] = {}
    for item in decisions:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        source_metrics = (
            item.get("source_metrics")
            if isinstance(item.get("source_metrics"), dict)
            else {}
        )
        if source_metrics.get("instrumentation_status") != "implemented":
            continue
        if family == "pre_submit_price_guard":
            closed["order_pre_submit_price_guard_safety_audit"] = family
        elif family == "holding_exit_decision_matrix_advisory":
            closed["order_holding_exit_decision_matrix_edge_counterfactual"] = family
    if (
        _holding_exit_counterfactual_contract_status(target_date).get("implemented")
        is True
    ):
        closed["order_holding_exit_decision_matrix_edge_counterfactual"] = (
            "holding_exit_decision_matrix_advisory"
        )
    return closed


def _entry_split_order_plan_followup_orders(
    ev_report: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = (
        ev_report.get("entry_split_order_plan")
        if isinstance(ev_report.get("entry_split_order_plan"), dict)
        else {}
    )
    if not summary:
        return []
    issues: list[str] = []
    status = str(summary.get("status") or "").strip()
    if not summary.get("available"):
        issues.append("report_contract_gap")
    if status == "source_quality_blocked" or status.startswith("blocked"):
        issues.append("source_quality_gap")
    if (
        _safe_int(summary.get("real_sample_count"), 0) >= 20
        and _safe_int(summary.get("real_outcome_joined_sample"), 0) > 0
        and _safe_int(summary.get("recommended_policy_candidate_count"), 0) <= 0
        and not _is_real_primary_sample_book(summary.get("primary_sample_book"))
    ):
        issues.append("real_sample_unused_by_postclose_decision")
    if (
        summary.get("schema_version")
        and summary.get("schema_version") != "entry_split_order_plan_v1"
    ):
        issues.append("report_contract_gap")
    if not issues:
        return []
    source_path = (
        (ev_report.get("sources") or {}).get("entry_split_order_plan")
        if isinstance(ev_report.get("sources"), dict)
        else None
    )
    return [
        {
            "order_id": "order_entry_split_order_plan_contract_gap",
            "title": "entry split order plan report/source-quality contract gap",
            "source_report_type": "threshold_cycle_ev",
            "lifecycle_stage": "submit",
            "target_subsystem": "entry_split_order_plan",
            "route": "source_quality_gap",
            "mapped_family": "entry_split_order_plan",
            "threshold_family": "entry_split_order_plan",
            "improvement_type": ",".join(sorted(set(issues))),
            "confidence": "postclose_threshold_ev_source",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "expected_ev_effect": (
                "Close report/source-quality/runtime-hook gaps so threshold-cycle can decide whether to pass a "
                "requested_qty-preserving split policy to next PREOPEN."
            ),
            "evidence": [
                f"status={summary.get('status')}",
                f"schema_version={summary.get('schema_version')}",
                f"candidate_grid_count={summary.get('candidate_grid_count')}",
                f"recommended_policy_candidate_count={summary.get('recommended_policy_candidate_count')}",
            ],
            "source_paths": [str(source_path)] if source_path else [],
            "next_postclose_metric": (
                "entry_split_order_plan should provide valid schema, source-quality pass/exclusion, "
                "candidate_grid, and recommended_policy."
            ),
            "files_likely_touched": [
                "src/engine/scalping/entry_split_order_plan.py",
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/sniper_state_handlers.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_entry_split_order_plan.py src/tests/test_daily_threshold_cycle_report.py",
                "Runtime hook must preserve total requested qty and not bypass pre-submit/broker guards.",
            ],
            "forbidden_uses": [
                "requested_qty_increase",
                "cap_release",
                "broker_guard_relief",
                "intraday_mutation",
            ],
        }
    ]


def _scale_in_split_order_plan_followup_orders(
    ev_report: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = (
        ev_report.get("scale_in_split_order_plan")
        if isinstance(ev_report.get("scale_in_split_order_plan"), dict)
        else {}
    )
    if not summary:
        return []
    state = (summary.get("evaluation_state") or {}).get("status")
    if (
        summary.get("available") is True
        and summary.get("schema_version") == "scale_in_split_order_plan_v4"
        and state
        in {
            "skipped_no_actual_fill",
            "skipped_no_applicable_fill",
            "skipped_unchanged_filled_outcome",
            "pending_filled_outcome",
        }
        and not (summary.get("evaluation_state") or {}).get("reason")
        and _safe_int(summary.get("unattributed_split_attempt_count"), 0) == 0
    ):
        return []
    issues: list[str] = []
    status = str(summary.get("status") or "").strip()
    if not summary.get("available"):
        issues.append("report_contract_gap")
    if status == "source_quality_blocked" or str(state or "").startswith("blocked"):
        issues.append("source_quality_gap")
    if (summary.get("evaluation_state") or {}).get("reason"):
        issues.append("filled_execution_source_gap")
    if (
        summary.get("schema_version")
        and summary.get("schema_version") != "scale_in_split_order_plan_v4"
    ):
        issues.append("report_contract_gap")
    if _safe_int(summary.get("price_observation_join_gap_count"), 0) > 0:
        issues.append("price_observation_join_gap")
    if _safe_int(summary.get("base_price_reconstruction_gap_count"), 0) > 0:
        issues.append("base_price_reconstruction_gap")
    if _safe_int(summary.get("recommended_policy_candidate_count"), 0) <= 0:
        issues.append("runtime_policy_handoff_gap")
    if _safe_int(summary.get("unattributed_split_attempt_count"), 0) > 0:
        issues.append("post_apply_policy_provenance_gap")
    if not issues:
        return []
    source_path = (
        (ev_report.get("sources") or {}).get("scale_in_split_order_plan")
        if isinstance(ev_report.get("sources"), dict)
        else None
    )
    return [
        {
            "order_id": "order_scale_in_split_order_plan_contract_gap",
            "title": "scale-in split order plan report/source-quality contract gap",
            "source_report_type": "threshold_cycle_ev",
            "lifecycle_stage": "scale_in",
            "target_subsystem": "scale_in_split_order_plan",
            "route": "source_quality_gap",
            "mapped_family": "scale_in_split_order_plan",
            "threshold_family": "scale_in_split_order_plan",
            "improvement_type": ",".join(sorted(set(issues))),
            "confidence": "postclose_threshold_ev_source",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "expected_ev_effect": (
                "Close report/source-quality/runtime-hook gaps so threshold-cycle can pass an AVG_DOWN "
                "qty-preserving split policy to next PREOPEN."
            ),
            "evidence": [
                f"status={summary.get('status')}",
                f"schema_version={summary.get('schema_version')}",
                f"candidate_grid_count={summary.get('candidate_grid_count')}",
                f"recommended_policy_candidate_count={summary.get('recommended_policy_candidate_count')}",
                f"counterfactual_selected_count={summary.get('counterfactual_selected_count')}",
                f"price_observation_join_gap_count={summary.get('price_observation_join_gap_count')}",
                f"base_price_reconstruction_gap_count={summary.get('base_price_reconstruction_gap_count')}",
            ],
            "source_paths": [str(source_path)] if source_path else [],
            "next_postclose_metric": (
                "scale_in_split_order_plan should provide valid schema, source-quality pass/exclusion, "
                "candidate_grid, post-submit price observation joins, and recommended_policy."
            ),
            "files_likely_touched": [
                "src/engine/scalping/scale_in_split_order_plan.py",
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/sniper_state_handlers.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scale_in_split_order_plan.py src/tests/test_daily_threshold_cycle_report.py",
                "Runtime hook must preserve total scale-in qty and not bypass broker guards.",
            ],
            "forbidden_uses": [
                "scale_in_qty_increase",
                "cap_release",
                "broker_guard_relief",
                "intraday_mutation",
                "pyramid_scale_in",
            ],
        }
    ]


def _panic_lifecycle_followup_orders(
    calibration_report: dict[str, Any],
) -> list[dict[str, Any]]:
    bundle = (
        calibration_report.get("calibration_source_bundle")
        if isinstance(calibration_report.get("calibration_source_bundle"), dict)
        else {}
    )
    source_metrics = (
        bundle.get("source_metrics")
        if isinstance(bundle.get("source_metrics"), dict)
        else {}
    )
    orders: list[dict[str, Any]] = []

    panic_sell = (
        source_metrics.get("panic_sell_defense")
        if isinstance(source_metrics.get("panic_sell_defense"), dict)
        else {}
    )
    panic_sell_candidates = (
        panic_sell.get("candidate_status")
        if isinstance(panic_sell.get("candidate_status"), dict)
        else {}
    )
    panic_sell_source_quality_blockers = (
        panic_sell.get("source_quality_blockers")
        if isinstance(panic_sell.get("source_quality_blockers"), list)
        else []
    )
    panic_sell_triggered = bool(panic_sell_candidates) or str(
        panic_sell.get("panic_state") or ""
    ) in {
        "PANIC_SELL",
        "RECOVERY_WATCH",
    }
    panic_sell_triggered = panic_sell_triggered or (
        _safe_int(panic_sell.get("active_sim_probe_positions"), 0) > 0
    )
    panic_sell_triggered = panic_sell_triggered or bool(
        panic_sell.get("market_breadth_followup_candidate")
    )
    panic_sell_triggered = panic_sell_triggered or bool(
        panic_sell_source_quality_blockers
    )
    if panic_sell_triggered:
        panic_sell_implementation_status = (
            "implemented_but_waiting_sample"
            if not panic_sell_source_quality_blockers
            else "implemented_source_quality_contract_waiting_sample"
        )
        orders.append(
            {
                "order_id": "order_panic_sell_defense_lifecycle_transition_pack",
                "title": "panic sell defense lifecycle transition pack",
                "source_report_type": "threshold_cycle_calibration_source_bundle",
                "lifecycle_stage": "holding_exit",
                "target_subsystem": "panic_sell_defense",
                "route": "auto_family_candidate",
                "mapped_family": None,
                "threshold_family": "panic_sell_defense",
                "improvement_type": "runtime_transition_design",
                "confidence": "consensus",
                "priority": 6,
                "runtime_effect": False,
                "implementation_status": panic_sell_implementation_status,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "required_downstream": [
                    "code_improvement_workorder",
                    "runtime_approval_summary",
                    "threshold_cycle_postclose_verification",
                ],
                "implementation_checks": [
                    "panic_sell_defense source metrics are present in calibration_source_bundle",
                    "panic_regime_mode and candidate_status are exposed as report-only provenance",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "implementation_provenance": {
                    "implementation_type": "panic_lifecycle_report_only_source_bundle",
                    "source_report_type": "threshold_cycle_calibration_source_bundle",
                    "source_metric_key": "panic_sell_defense",
                    "panic_state": panic_sell.get("panic_state"),
                    "panic_regime_mode": panic_sell.get("panic_regime_mode"),
                    "source_quality_blockers": panic_sell_source_quality_blockers,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "decision_authority": "report_only_source_bundle",
                },
                "expected_ev_effect": (
                    "Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, "
                    "then request explicit live-runtime approval without mutating exits automatically."
                ),
                "evidence": [
                    f"panic_state={panic_sell.get('panic_state')}",
                    f"panic_regime_mode={panic_sell.get('panic_regime_mode')}",
                    f"stop_loss_exit_count={panic_sell.get('stop_loss_exit_count')}",
                    f"confirmation_eligible_exit_count={panic_sell.get('confirmation_eligible_exit_count')}",
                    f"active_sim_probe_positions={panic_sell.get('active_sim_probe_positions')}",
                    f"post_sell_rebound_above_sell_10_20m_pct={panic_sell.get('post_sell_rebound_above_sell_10_20m_pct')}",
                    f"microstructure_market_risk_state={panic_sell.get('microstructure_market_risk_state')}",
                    f"microstructure_confirmed_risk_off_advisory={panic_sell.get('microstructure_confirmed_risk_off_advisory')}",
                    f"microstructure_portfolio_local_risk_off_only={panic_sell.get('microstructure_portfolio_local_risk_off_only')}",
                    f"market_breadth_followup_candidate={panic_sell.get('market_breadth_followup_candidate')}",
                    f"source_quality_blockers={panic_sell_source_quality_blockers}",
                    f"candidate_status={panic_sell_candidates}",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": (
                    "panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, "
                    "market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition."
                ),
                "files_likely_touched": [
                    "src/engine/panic_sell_defense_report.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "docs/plan-korStockScanPerformanceOptimization.rebase.md",
                ],
                "acceptance_tests": [
                    "pytest panic sell defense/report lifecycle tests",
                    "pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py",
                ],
            }
        )

    return orders


def _swing_ldm_order_id(item: dict[str, Any]) -> str:
    stage = _slug(str(item.get("lifecycle_stage") or "swing"))
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug_with_hash(
        str(item.get("bucket_key") or item.get("workorder_id") or "unknown")
    )
    return f"order_swing_ldm_{stage}_{bucket_type}_{bucket_key}"


def _swing_lifecycle_matrix_followup_orders(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    if not report:
        return []
    orders: list[dict[str, Any]] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    raw_event_count = _safe_int(summary.get("raw_swing_event_count"), 0)
    consumed_event_count = _safe_int(summary.get("ldm_consumed_event_count"), 0)
    coverage_rate = _safe_float(summary.get("ldm_event_coverage_rate"), 0.0)
    if raw_event_count >= 1000 and coverage_rate < 0.01:
        orders.append(
            {
                "order_id": "order_swing_ldm_event_coverage_rollup",
                "title": "Swing LDM raw event coverage roll-up review",
                "source_report_type": "swing_lifecycle_decision_matrix",
                "lifecycle_stage": "entry",
                "target_subsystem": "swing_lifecycle_decision_matrix",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "swing_ldm_event_coverage_gap",
                "confidence": "postclose_ldm_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Prevent observed Swing SIM events from being silently excluded before bucket discovery.",
                "evidence": [
                    f"raw_swing_event_count={raw_event_count}",
                    f"ldm_consumed_event_count={consumed_event_count}",
                    f"ldm_event_coverage_rate={coverage_rate}",
                    f"unmapped_swing_stage_counts={summary.get('unmapped_swing_stage_counts') or {}}",
                    "decision_authority=swing_ldm_source_only",
                    "actual_order_submitted=false",
                ],
                "next_postclose_metric": "Swing LDM coverage should stay >=0.01 when raw_swing_event_count>=1000, or unmapped stages should have explicit roll-up evidence.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_decision_matrix.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    for section_name in (
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        section = (
            report.get(section_name)
            if isinstance(report.get(section_name), dict)
            else {}
        )
        for item in section.get("code_improvement_workorders") or []:
            if not isinstance(item, dict):
                continue
            orders.append(
                {
                    "order_id": _swing_ldm_order_id(item),
                    "title": f"Swing LDM source field follow-up: {item.get('bucket_key')}",
                    "source_report_type": "swing_lifecycle_decision_matrix",
                    "lifecycle_stage": item.get("lifecycle_stage") or "source_quality",
                    "target_subsystem": item.get("target_subsystem")
                    or "swing_lifecycle_decision_matrix",
                    "route": "instrumentation_order",
                    "mapped_family": None,
                    "threshold_family": None,
                    "improvement_type": "swing_ldm_bucket_instrumentation_gap",
                    "confidence": "postclose_ldm_source",
                    "priority": 2,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "implementation_status": item.get("implementation_status"),
                    "implementation_provenance": item.get("implementation_provenance")
                    or {},
                    "expected_ev_effect": "Close Swing LDM bucket source-quality gaps while preserving sim-only authority.",
                    "evidence": [
                        f"section={section_name}",
                        f"bucket_type={item.get('bucket_type')}",
                        f"bucket_key={item.get('bucket_key')}",
                        f"reason={item.get('reason')}",
                        f"implementation_status={item.get('implementation_status') or '-'}",
                        "decision_authority=swing_ldm_source_only",
                        "actual_order_submitted=false",
                    ],
                    "next_postclose_metric": "Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.",
                    "files_likely_touched": [
                        "src/engine/swing_lifecycle_decision_matrix.py",
                        "src/engine/swing_lifecycle_bucket_discovery.py",
                    ],
                    "acceptance_tests": [
                        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py",
                    ],
                }
            )
    return orders


def _swing_lifecycle_bucket_discovery_followup_orders(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    if not report:
        return []
    orders: list[dict[str, Any]] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    surfaced_candidates = (
        report.get("surfaced_candidates")
        if isinstance(report.get("surfaced_candidates"), list)
        else []
    )
    contract_gap_ids: list[str] = []
    for candidate in surfaced_candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        bucket_id = str(candidate.get("bucket_id") or "").strip()
        stage = str(
            candidate.get("stage") or candidate.get("lifecycle_stage") or ""
        ).strip()
        if not candidate_id or not bucket_id or not stage or stage.lower() == "unknown":
            contract_gap_ids.append(candidate_id or bucket_id or "unknown")
    if contract_gap_ids:
        orders.append(
            {
                "order_id": "order_swing_lifecycle_bucket_discovery_contract_rollup",
                "title": "Swing lifecycle bucket discovery candidate contract roll-up review",
                "source_report_type": "swing_lifecycle_bucket_discovery",
                "lifecycle_stage": "source_quality",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "swing_bucket_candidate_contract_gap",
                "confidence": "postclose_bucket_discovery_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Ensure Swing discovery candidates preserve candidate_id, bucket_id, stage, and lifecycle_stage through downstream consumers.",
                "evidence": [
                    f"contract_gap_candidate_ids={sorted(set(contract_gap_ids))[:20]}",
                    "decision_authority=swing_ldm_bucket_discovery_sim_auto",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": "All surfaced Swing discovery candidates should expose candidate_id, bucket_id, stage, and lifecycle_stage.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_bucket_discovery.py",
                    "src/engine/runtime_apply_gap_audit.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_gap_audit.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
            }
        )
    unreviewed_count = _safe_int(summary.get("sim_auto_unreviewed_candidate_count"), 0)
    downgraded_count = _safe_int(summary.get("sim_auto_downgraded_by_review_count"), 0)
    if unreviewed_count > 0 or downgraded_count > 0:
        ai_review_followup_reasons = summary.get("ai_review_followup_reasons") or []
        provider_unavailable_hold = (
            str(summary.get("ai_review_blocker_state") or "") == "provider_unavailable"
            and not bool(summary.get("ai_review_followup_required"))
            and not ai_review_followup_reasons
        )
        implementation_status = (
            "implemented_but_waiting_sample"
            if provider_unavailable_hold
            else "implemented"
        )
        orders.append(
            {
                "order_id": "order_swing_lifecycle_bucket_discovery_ai_review_rollup",
                "title": "Swing lifecycle sim-auto AI review shard roll-up review",
                "source_report_type": "swing_lifecycle_bucket_discovery",
                "lifecycle_stage": "source_quality",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                "route": (
                    "ai_review_provider_unavailable_hold"
                    if provider_unavailable_hold
                    else "instrumentation_order"
                ),
                "mapped_family": (
                    "swing_lifecycle_bucket_discovery"
                    if provider_unavailable_hold
                    else None
                ),
                "threshold_family": None,
                "improvement_type": "swing_bucket_ai_review_shard_gap",
                "confidence": "postclose_bucket_discovery_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Keep parsed sim-auto shard candidates usable while fail-closing only unreviewed or failed shard candidates.",
                "evidence": [
                    f"sim_auto_review_shard_count={_safe_int(summary.get('sim_auto_review_shard_count'), 0)}",
                    f"sim_auto_reviewed_candidate_count={_safe_int(summary.get('sim_auto_reviewed_candidate_count'), 0)}",
                    f"sim_auto_unreviewed_candidate_count={unreviewed_count}",
                    f"sim_auto_downgraded_by_review_count={downgraded_count}",
                    f"ai_review_blocker_state={summary.get('ai_review_blocker_state') or ''}",
                    f"ai_review_followup_required={bool(summary.get('ai_review_followup_required'))}",
                    f"ai_review_followup_reasons={ai_review_followup_reasons}",
                    "decision_authority=swing_ldm_bucket_discovery_sim_auto",
                    "allowed_runtime_apply=false",
                ],
                "implementation_status": implementation_status,
                "implementation_provenance": {
                    "implementation_type": "swing_bucket_ai_review_shard_rollup",
                    "implemented_scope": (
                        "Swing bucket discovery preserves reviewed, unreviewed, and downgraded sim-auto shard "
                        "counts as source-only provenance for downstream workorders."
                    ),
                    "source_report_type": "swing_lifecycle_bucket_discovery",
                    "decision_authority": "swing_ldm_bucket_discovery_sim_auto",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "ai_review_blocker_state": summary.get("ai_review_blocker_state"),
                    "ai_review_followup_required": bool(
                        summary.get("ai_review_followup_required")
                    ),
                    "ai_review_followup_reasons": ai_review_followup_reasons,
                    "sim_auto_review_shard_count": _safe_int(
                        summary.get("sim_auto_review_shard_count"), 0
                    ),
                    "sim_auto_reviewed_candidate_count": _safe_int(
                        summary.get("sim_auto_reviewed_candidate_count"), 0
                    ),
                    "sim_auto_unreviewed_candidate_count": unreviewed_count,
                    "sim_auto_downgraded_by_review_count": downgraded_count,
                    "root_cause_closure_status_hint": "root_cause_closed",
                },
                "next_postclose_metric": "Partial AI review failures should create source-only downgrade evidence without hiding parsed shard candidates.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_bucket_discovery.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    for item in report.get("code_improvement_workorders") or []:
        if not isinstance(item, dict):
            continue
        bucket_id = str(item.get("bucket_id") or item.get("workorder_id") or "")
        orders.append(
            {
                "order_id": (
                    "order_swing_lifecycle_bucket_discovery_"
                    f"{_slug_with_hash(bucket_id)}"
                ),
                "title": f"Swing lifecycle bucket discovery handoff follow-up: {bucket_id}",
                "source_report_type": "swing_lifecycle_bucket_discovery",
                "lifecycle_stage": item.get("lifecycle_stage") or "source_quality",
                "target_subsystem": item.get("target_subsystem")
                or "swing_lifecycle_bucket_discovery",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "swing_bucket_handoff_or_contract_gap",
                "confidence": "postclose_bucket_discovery_source",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": item.get("implementation_status"),
                "implementation_provenance": item.get("implementation_provenance"),
                "expected_ev_effect": "Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.",
                "evidence": [
                    f"bucket_id={bucket_id}",
                    f"canonical_bucket={item.get('canonical_bucket') or '-'}",
                    f"legacy_raw_bucket_key={item.get('legacy_raw_bucket_key') or '-'}",
                    f"ai_tier2_taxonomy_decision={(item.get('comparative_review') or {}).get('selected_decision') if isinstance(item.get('comparative_review'), dict) else '-'}",
                    f"ai_tier2_selected_source={(item.get('comparative_review') or {}).get('selected_source') if isinstance(item.get('comparative_review'), dict) else '-'}",
                    f"classification_state={item.get('classification_state')}",
                    f"reason={item.get('reason')}",
                    f"source_workorder_id={item.get('source_workorder_id') or '-'}",
                    f"parent_bucket_id={item.get('parent_bucket_id') or '-'}",
                    "decision_authority=swing_ldm_bucket_discovery_sim_auto",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": "Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_bucket_discovery.py",
                    "src/engine/threshold_cycle_ev_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "canonical_bucket": item.get("canonical_bucket"),
                "legacy_raw_bucket_key": item.get("legacy_raw_bucket_key"),
                "deterministic_proposal": item.get("deterministic_proposal"),
                "ai_tier2_proposal": item.get("ai_tier2_proposal"),
                "comparative_review": item.get("comparative_review"),
            }
        )
    return orders


def _is_swing_scoped_order(order: dict[str, Any]) -> bool:
    scope = (
        str(
            order.get("strategy_scope")
            or order.get("domain")
            or order.get("strategy")
            or ""
        )
        .strip()
        .lower()
    )
    if scope == "swing":
        return True
    return "swing" in " ".join(
        str(order.get(key) or "").lower()
        for key in (
            "order_id",
            "title",
            "source_report_type",
            "target_subsystem",
            "mapped_family",
            "threshold_family",
        )
    )
