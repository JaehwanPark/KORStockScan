"""Source-only WS follow-up and finalized, contract-isolated economic evidence.

Monitoring owns these report contracts, not broker recovery or PREOPEN policy.
"""

from __future__ import annotations

import hashlib
import json
import math
import zlib
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from src.utils.jsonl_io import read_json_object_strict

RECEIPT_SCHEMA = "ws_prune_daily_economics_v1"
HOTSET_RECEIPT_SCHEMA = "ws_hotset_daily_economics_v1"
ROLLING_SOURCE_DAYS = 10
RESOLVED_FLOOR = 20
BBO_COVERAGE_FLOOR_PCT = 95.0
RIGHT_CENSORED_MAX_PCT = 20.0
BOUNDED_REJECTIONS = frozenset(
    {
        "active_episode_capacity_rejected",
        "daily_request_budget_exhausted",
        "daily_request_budget_rejected",
        "pending_sample_capacity_rejected",
    }
)
SOURCE_QUALITY_REJECTIONS = frozenset({"anchor_schedule_latency_exceeded"})


def observer_receipt_accounting(episodes: list[dict], sample_count: int) -> dict:
    """Account for every selected episode; explicit gaps are receipts, not valid BBO."""
    counts = defaultdict(int)
    details = []
    for episode in episodes:
        states = set(episode.get("prune_observer_schedule_statuses") or [])
        scheduled = bool(
            states
            & {
                "new_episode_scheduled",
                "existing_episode_reused",
                "completed_episode_reused",
            }
        )
        indices = set(episode.get("prune_observer_receipt_indices") or [])
        declared_count = episode.get(
            "prune_observer_scheduled_sample_count", sample_count
        )
        count_valid = type(declared_count) is int and 0 < declared_count <= sample_count
        expected_indices = set(range(declared_count if count_valid else sample_count))
        terminal_valid = (
            count_valid
            and declared_count - 1
            in set(episode.get("prune_observer_terminal_indices") or [])
        ) or (
            declared_count == sample_count
            and episode.get("prune_observer_receipt_terminal_valid") is True
        )
        complete = (
            bool(episode.get("prune_observer_episode_id"))
            and not episode.get("metadata_conflicts")
            and count_valid
            and indices == expected_indices
            and terminal_valid
        )
        if scheduled:
            state = "scheduled_complete" if complete else "scheduled_receipt_gap"
        elif states & BOUNDED_REJECTIONS and not (states - BOUNDED_REJECTIONS):
            state = "bounded_not_admitted"
        elif states & SOURCE_QUALITY_REJECTIONS and not (
            states - BOUNDED_REJECTIONS - SOURCE_QUALITY_REJECTIONS
        ):
            # The collector explicitly rejected an expired original anchor.
            # This is a recorded source-quality loss, never absent telemetry,
            # a fresh re-anchored sample, or executable BBO evidence.
            state = "source_quality_not_admitted"
        else:
            state = "admission_receipt_gap"
        counts[state] += 1
        if state.endswith("gap"):
            details.append(
                {
                    "episode_id": episode.get("prune_observer_episode_id"),
                    "scan_generation_ids": episode.get("scan_generation_ids"),
                    "code": episode.get("code"),
                    "venue": episode.get("venue"),
                    "market_session_bucket": episode.get("market_session_bucket"),
                    "state": state,
                    "declared_sample_count": declared_count,
                    "observed_sample_indices": sorted(indices),
                    "missing_sample_indices": (
                        sorted(expected_indices - indices) if scheduled else []
                    ),
                }
            )
    return {
        "schema": "ws_prune_receipt_accounting_v1",
        "episode_count": len(episodes),
        "state_counts": dict(counts),
        "unaccounted_episode_count": counts["scheduled_receipt_gap"]
        + counts["admission_receipt_gap"],
        "gap_examples": details[:30],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _repair_evidence_missing(states: dict) -> bool:
    return not states or any(
        count
        and (
            key in {"not_observed", "unknown", "repair_required_without_cycle_state"}
            or "missing" in key
        )
        for key, count in states.items()
    )


def _hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def finalize_followups(summary: dict, orders: list[dict]) -> list[dict]:
    """A completed observation window cannot defer to that same window again."""
    final = summary.get("evaluation_phase") == "postclose_final"
    causal = summary.get("causal_attribution") or {}
    funnel = summary.get("scanner_unique_funnel") or {}
    observer = funnel.get("prune_observer_summary") or {}
    for order in orders:
        if order.get("decision") != "defer_evidence":
            continue
        order["diagnostic_acceptance_requires_economic_floor"] = False
        order["followup_window"] = "target_date_postclose_final"
        if not final:
            order["diagnostic_status"] = "pending_declared_window"
            continue
        order_id = order["order_id"]
        gap = None
        if order_id == "order_ws_total_stale_escalation":
            states = (causal.get("both_ws_stale") or {}).get(
                "repair_cycle_state_counts"
            ) or {}
            gap = "repair_receipt_missing" if _repair_evidence_missing(states) else None
        elif order_id == "order_ws_decision_stage_stale_backoff_attribution":
            states = (causal.get("decision_stage_stale_backoff") or {}).get(
                "repair_cycle_state_counts"
            ) or {}
            if _repair_evidence_missing(states):
                gap = "stale_backoff_attribution_missing"
        elif order_id == "order_ws_trade_tick_quiet_low_liquidity_classification":
            volumes = (causal.get("trade_tick_quiet") or {}).get(
                "cumulative_volume_provenance_counts"
            ) or {}
            if not volumes or any(
                value for key, value in volumes.items() if "missing" in key
            ):
                gap = "quiet_tape_volume_provenance_missing"
        elif order_id == "order_scanner_eligible_no_heavy_closed_loop":
            gap = "eligible_heavy_terminal_attribution_missing"
        elif order_id == "order_scanner_runtime_handoff_provenance_gap":
            gap = "attach_handoff_provenance_missing"
        elif order_id == "order_scanner_scan_generation_conservation_gap":
            gap = "final_scan_generation_conservation_unresolved"
        elif order_id == "order_scanner_funnel_executable_bbo_join":
            eligible = observer.get("eligible_episode_census_count")
            scheduled = observer.get("scheduled_stable_episode_count")
            configuration = observer.get("runtime_configuration_valid_receipt_count")
            accounting = observer.get("receipt_accounting") or {}
            if type(configuration) is not int or configuration <= 0:
                gap = "observer_configuration_receipt_missing"
            elif (
                type(eligible) is not int
                or type(scheduled) is not int
                or not eligible >= scheduled >= 0
            ):
                gap = "observer_eligible_census_missing"
            elif not eligible and (
                not accounting or accounting.get("episode_count") != 0
            ):
                gap = "observer_eligible_census_missing"
            elif (
                accounting.get("schema") != "ws_prune_receipt_accounting_v1"
                or accounting.get("episode_count") != eligible
                or accounting.get("unaccounted_episode_count") != 0
            ):
                gap = "observer_episode_receipt_accounting_gap"
            else:
                order.update(
                    decision="observe",
                    diagnostic_status=(
                        "healthy_no_natural_sample"
                        if not eligible
                        else (
                            "bounded_collector_admission_observed"
                            if not scheduled
                            else "collector_receipts_observed"
                        )
                    ),
                    next_action="evaluate_contract_isolated_rolling_groups",
                    economic_acceptance=(
                        summary.get("rolling_prune_economics") or {}
                    ).get("status", "hold_sample"),
                    acceptance_tests=[
                        "exact_owner_route_schedule_and_observation_receipts_accounted",
                        "explicit_source_gaps_are_not_zero_profit",
                        "economic_floors_do_not_block_instrumentation_closure",
                        "runtime_effect_and_allowed_runtime_apply_remain_false",
                    ],
                )
                continue
        if gap:
            # An attribution defect is not proof that resubscription or BUY is safe.
            order.update(
                decision="implement_now",
                diagnostic_status="source_contract_gap",
                implementation_state="source_contract_repair_required",
                implementation_status=None,
                gap_reason=gap,
                next_action="repair_source_contract_and_verify_exact_consumer",
            )
            order["files_likely_touched"] = [
                "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                "src/engine/monitoring/ws_freshness_acceptance.py",
                "src/tests/test_intraday_ws_freshness_monitor.py",
            ]
            order["acceptance_tests"] = [
                "exact_event_owner_and_missing_field_attribution_reproduced",
                "producer_consumer_receipt_gap_closed_or_historical_loss_explicitly_quarantined",
                "no_order_resubscribe_threshold_or_process_mutation",
            ]
        else:
            order.update(
                decision="observe",
                diagnostic_status="attributed_safety_observation",
                next_action="retain_safety_boundary_and_observe_new_events",
            )
    return orders


def economic_receipt(summary: dict) -> dict:
    attribution = (
        (summary.get("scanner_unique_funnel") or {}).get("economic_cohorts") or {}
    ).get("executable_bbo_attribution") or {}
    cost = attribution.get("comparison_cost_contract") or {}
    contract = {
        "schema": RECEIPT_SCHEMA,
        "cost": {
            key: cost.get(key)
            for key in (
                "policy_id",
                "effective_from",
                "effective_to",
                "buy_fee_bps",
                "sell_fee_bps",
                "statutory_sell_tax_bps",
                "round_trip_cost_pct",
            )
        },
        "path": {
            key: attribution.get(key)
            for key in (
                "gross_target_pct",
                "adverse_stop_pct",
                "horizon_sec",
                "timeout_max_lag_sec",
            )
        },
    }
    master = attribution.get("official_symbol_master_binding") or {}
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "target_date": summary["target_date"],
        "finalized": summary.get("evaluation_phase") == "postclose_final",
        "contract": contract,
        "contract_sha256": _hash(contract),
        "source_cost_sha256": cost.get("contract_sha256"),
        "source_master_sha256": master.get("artifact_sha256"),
        "source_verified": attribution.get("comparison_cost_contract_status")
        == "verified"
        and master.get("status") == "verified"
        and bool(cost.get("contract_sha256"))
        and bool(master.get("artifact_sha256"))
        and (summary.get("diagnostic_acceptance") or {}).get("status")
        == "diagnostic_generated",
        "source_generation": (summary.get("input_processing") or {}).get(
            "source_offsets"
        )
        or {},
        "groups": (attribution.get("prune_observer_acceptance") or {}).get("groups")
        or [],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    receipt["sha256"] = _hash(receipt)
    return receipt


def hotset_economic_receipt(summary: dict) -> dict:
    """Reuse existing sampled queue-rank scenarios; do not generate a new policy."""
    source = (summary.get("scanner_unique_funnel") or {}).get(
        "hotset_capacity_counterfactual"
    ) or {}
    receipt = economic_receipt(
        {
            **summary,
            "scanner_unique_funnel": {
                "economic_cohorts": {"executable_bbo_attribution": source}
            },
        }
    )
    receipt["schema"] = HOTSET_RECEIPT_SCHEMA
    receipt["contract"]["schema"] = HOTSET_RECEIPT_SCHEMA
    receipt["contract"]["path"].update(
        {
            "population": "first_queue_rank_capacity_proxy_not_runtime_scheduler_replay",
            "capacity_values": source.get("capacity_values"),
            "gross_target_values": source.get("gross_target_values"),
            "adverse_stop_values": source.get("adverse_stop_values"),
        }
    )
    receipt["groups"] = [
        {
            **row,
            "cohort": "first_queue_rank_capacity_proxy",
            "resolved_outcome_count": row.get("cost_adjusted_resolved_outcome_count"),
        }
        for row in source.get("scenarios") or []
    ]
    receipt["contract_sha256"] = _hash(receipt["contract"])
    receipt["sha256"] = _hash({k: v for k, v in receipt.items() if k != "sha256"})
    return receipt


def rolling_economics(current: dict, report_dir: Path, *, hotset: bool = False) -> dict:
    """Replace same-date generations, retain empty days, never mix contracts/venues.

    Consume compact producer-issued self-hashed daily receipts, not historical raw.
    Legacy reports without this receipt are diagnostic history, not invented EV.
    """
    target = current["target_date"]
    receipt_field = (
        "daily_hotset_economic_receipt" if hotset else "daily_prune_economic_receipt"
    )
    receipt_schema = HOTSET_RECEIPT_SCHEMA if hotset else RECEIPT_SCHEMA
    receipts = {target: current}
    window_dates = [target]
    rejected = []
    paths = sorted(
        {
            Path(str(path).removesuffix(".gz"))
            for pattern in (
                "intraday_ws_freshness_monitor_????-??-??.json",
                "intraday_ws_freshness_monitor_????-??-??.json.gz",
            )
            for path in report_dir.glob(pattern)
        },
        reverse=True,
    )
    for path in paths:
        source_date = path.stem[-10:]
        if not "2026-06-05" <= source_date < target:
            continue
        try:
            date.fromisoformat(source_date)
            if len(window_dates) >= ROLLING_SOURCE_DAYS:
                break
            window_dates.append(source_date)
            payload = read_json_object_strict(path)
            receipt = payload[receipt_field]
            if receipt.get("target_date") != source_date:
                raise ValueError("target_date_mismatch")
            if receipt.get("finalized") is not True:
                continue
            receipts[source_date] = receipt
        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            EOFError,
            OSError,
            zlib.error,
        ):
            rejected.append(
                {"source_date": source_date, "reason": "receipt_missing_or_invalid"}
            )
    groups: dict[tuple, list] = defaultdict(list)
    accepted_dates = []
    source_hashes = {}
    for source_date, receipt in sorted(receipts.items()):
        reason = None
        try:
            if date.fromisoformat(source_date) < date(2026, 6, 5):
                raise ValueError("prebaseline_source_forbidden")
            body = {k: v for k, v in receipt.items() if k != "sha256"}
            if receipt.get("schema") != receipt_schema or receipt.get(
                "sha256"
            ) != _hash(body):
                reason = "receipt_hash_invalid"
            elif (
                receipt.get("runtime_effect") is not False
                or receipt.get("allowed_runtime_apply") is not False
                or receipt.get("actual_order_submitted") is not False
                or receipt.get("broker_order_forbidden") is not True
            ):
                reason = "authority_invalid"
            elif receipt.get("finalized") is not True:
                reason = "not_finalized"
            elif receipt.get("source_verified") is not True:
                reason = "source_quality_blocked"
            elif receipt.get("contract_sha256") != current.get("contract_sha256"):
                reason = "different_economic_contract"
            elif receipt.get("contract_sha256") != _hash(receipt.get("contract")):
                reason = "economic_contract_hash_invalid"
            if reason:
                raise ValueError(reason)
            day_groups = receipt["groups"]
            if not isinstance(day_groups, list):
                raise ValueError("group_list_invalid")
            keyed_groups = defaultdict(list)
            for group in day_groups:
                try:
                    key = tuple(
                        group[k] for k in ("cohort", "venue", "market_session_bucket")
                    )
                    if any(
                        not isinstance(k, str) or not k or k.upper() == "UNKNOWN"
                        for k in key
                    ):
                        raise ValueError("group_identity_invalid")
                    if hotset:
                        axes = (
                            group["capacity_proxy"],
                            group["gross_target_pct"],
                            group["adverse_stop_pct"],
                        )
                        if any(
                            type(value) not in (int, float) or not math.isfinite(value)
                            for value in axes
                        ):
                            raise ValueError("scenario_axes_invalid")
                        path = receipt["contract"]["path"]
                        if any(
                            value not in (path.get(name) or [])
                            for value, name in zip(
                                axes,
                                (
                                    "capacity_values",
                                    "gross_target_values",
                                    "adverse_stop_values",
                                ),
                            )
                        ):
                            raise ValueError("scenario_axes_invalid")
                        key += axes
                    keyed_groups[key].append(group)
                except (ValueError, KeyError, TypeError):
                    rejected.append(
                        {
                            "source_date": source_date,
                            "scope": "group",
                            "reason": "group_identity_invalid",
                        }
                    )
            for key, candidates in keyed_groups.items():
                try:
                    if len(candidates) != 1:
                        raise ValueError("duplicate_daily_group")
                    group = candidates[0]
                    counts = [
                        group[k]
                        for k in (
                            "eligible_verified_common_stock_candidate_count",
                            "exact_bbo_joined_count",
                            "resolved_outcome_count",
                            "right_censored_count",
                        )
                    ]
                    if any(type(n) is not int or n < 0 for n in counts):
                        raise ValueError("invalid_group_counts")
                    eligible, joined, resolved, censored = counts
                    if not eligible >= joined >= resolved + censored:
                        raise ValueError("group_conservation_invalid")
                    value = group.get("resolved_return_sum_pct")
                    if resolved and (
                        type(value) not in (int, float) or not math.isfinite(value)
                    ):
                        raise ValueError("net_outcome_sum_missing")
                    if not resolved and value not in (None, 0):
                        raise ValueError("net_sum_without_outcomes")
                    if hotset:
                        duration = group.get("resolved_holding_sec_sum")
                        positive = group.get("profitable_outcome_count")
                        if (
                            type(duration) not in (int, float)
                            or not math.isfinite(duration)
                            or duration < 0
                            or (resolved and duration <= 0)
                        ):
                            raise ValueError("holding_duration_missing_or_invalid")
                        if type(positive) is not int or not 0 <= positive <= resolved:
                            raise ValueError("profitable_outcome_count_invalid")
                    groups[key].append(group)
                except (ValueError, KeyError, TypeError) as exc:
                    rejected.append(
                        {
                            "source_date": source_date,
                            "scope": "group",
                            "group": list(key),
                            "reason": str(exc),
                        }
                    )
            accepted_dates.append(source_date)
            source_hashes[source_date] = receipt["sha256"]
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({"source_date": source_date, "reason": str(exc)})
    output = []
    for key, rows in sorted(groups.items()):
        counts = {
            name: sum(row[name] for row in rows)
            for name in (
                "eligible_verified_common_stock_candidate_count",
                "exact_bbo_joined_count",
                "resolved_outcome_count",
                "right_censored_count",
            )
        }
        eligible, joined, resolved, censored = counts.values()
        coverage = 100 * joined / eligible if eligible else 0.0
        censor_rate = 100 * censored / joined if joined else 0.0
        ready = (
            coverage >= BBO_COVERAGE_FLOOR_PCT
            and resolved >= RESOLVED_FLOOR
            and censor_rate <= RIGHT_CENSORED_MAX_PCT
        )
        output.append(
            {
                "cohort": key[0],
                "venue": key[1],
                "market_session_bucket": key[2],
                **counts,
                "exact_bbo_join_coverage_pct": coverage,
                "right_censored_rate_pct_of_joined": censor_rate,
                "source_only_comparison_ready": ready,
                "source_quality_adjusted_ev_pct": (
                    sum(row.get("resolved_return_sum_pct") or 0 for row in rows)
                    / resolved
                    if ready
                    else None
                ),
                "diagnostic_resolved_subset_equal_weight_avg_profit_pct": (
                    sum(row.get("resolved_return_sum_pct") or 0 for row in rows)
                    / resolved
                    if resolved
                    else None
                ),
                "subset_population_extrapolation_allowed": False,
                "comparison_block_reasons": [
                    name
                    for name, blocked in (
                        ("bbo_coverage_below_floor", coverage < BBO_COVERAGE_FLOOR_PCT),
                        ("resolved_sample_below_floor", resolved < RESOLVED_FLOOR),
                        (
                            "right_censor_above_floor",
                            censor_rate > RIGHT_CENSORED_MAX_PCT,
                        ),
                    )
                    if blocked
                ],
            }
        )
        if hotset:
            holding = sum(row["resolved_holding_sec_sum"] for row in rows)
            output[-1].update(
                {
                    "capacity_proxy": key[3],
                    "gross_target_pct": key[4],
                    "adverse_stop_pct": key[5],
                    "profitable_outcome_count": sum(
                        row["profitable_outcome_count"] for row in rows
                    ),
                    "resolved_holding_sec_sum": holding,
                    "avg_resolved_holding_sec": (
                        holding / resolved if resolved else None
                    ),
                    "resolved_observations_per_source_report_date": resolved
                    / len(window_dates),
                    "frequency_role": "sampled_opportunities_not_real_trade_frequency",
                    "scenario_additivity_allowed": False,
                }
            )
    return {
        "status": (
            "source_only_groups_ready"
            if any(g["source_only_comparison_ready"] for g in output)
            else "hold_sample_or_source_quality"
        ),
        "window_policy": "last_10_source_report_dates_finalized_only_contract_isolated",
        "window_source_dates": sorted(window_dates),
        "source_dates": accepted_dates,
        "source_receipt_hashes": source_hashes,
        "excluded_sources": rejected,
        "groups": output,
        "all_groups_required": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_role": "source_only_comparison_economics",
        "decision_authority": (
            "scanner_hotset_capacity_proxy_source_only"
            if hotset
            else "scanner_funnel_executable_bbo_source_only"
        ),
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "sample_floor": "per_group_resolved20_coverage95_censored20",
        "source_quality_gate": "finalized_self_hashed_exact_date_cost_master_and_group_conservation",
        "forbidden_uses": [
            "runtime_apply",
            "broker_orders",
            "full_population_extrapolation",
            "real_fill_quality",
        ],
    }
