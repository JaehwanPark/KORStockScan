"""Adaptive exit decision replay and attribution-child source census.

Sparse horizon marks are deliberately not converted to ordered fill paths.
This helper does not submit orders, infer broker fills, or emit live candidates.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, Sequence

from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.decision import evaluate_exit
from src.trading.order.adaptive_exit.models import (
    Clock,
    DecisionState,
    ExitPolicy,
    Position,
    Snapshot,
)


def replay_decisions(
    policy: ExitPolicy,
    position: Position,
    path: Sequence[tuple[Clock, Snapshot]],
) -> dict[str, Any]:
    """Replay to the first transition intent using exactly the shared evaluator.

    An exit/arm intent is NOT a counterfactual fill. A future execution model
    must resolve cancel-race, queue, fill latency, and residual quantity before
    assigning any EV. This function intentionally leaves economics null.
    """
    state = DecisionState(
        policy.policy_hash,
        position.position_epoch,
        position.first_fill_at_ms,
        position.open_qty,
    )
    rows: list[dict[str, Any]] = []
    for clock, snapshot in path:
        decision = evaluate_exit(policy, position, snapshot, clock, state)
        rows.append(
            {
                "observed_at_ms": snapshot.observed_at_ms,
                "source_hash": snapshot.source_hash,
                "action": decision.action,
                "reason": decision.reason,
                "executable_bid": decision.executable_bid,
                "worst_bid": decision.worst_bid,
                "progress": decision.progress,
            }
        )
        if decision.action in ("SOURCE_GAP", "RECOVERY_REQUIRED"):
            break
        if decision.action.startswith("REQUEST_"):
            break
        state = replace(
            state,
            last_observed_at_ms=snapshot.observed_at_ms,
            source_epoch=snapshot.source_epoch,
            sequence=snapshot.sequence,
        )
        if decision.action == "GRANT_EXTENSION":
            state = replace(
                state,
                extensions=1,
                extension_until_active_ms=decision.next_active_deadline_ms,
                extension_granted_at_active_ms=clock.now_ms
                - position.first_fill_at_ms
                - clock.verified_halt_ms,
            )
    status = (
        "source_gap"
        if not rows or rows[-1]["action"] in ("SOURCE_GAP", "RECOVERY_REQUIRED")
        else "decision_path_observed"
    )
    return {
        "schema": "machine_adaptive_exit_decision_replay_v1",
        "status": status,
        "policy_hash": policy.policy_hash,
        "scope_key": position.scope_key,
        "owner_id": position.owner_id,
        "episode_id": position.episode_id,
        "position_epoch": position.position_epoch,
        "first_fill_at_ms": position.first_fill_at_ms,
        "cost_contract_hash": position.cost_contract_hash,
        "lot_id": position.lot_id,
        "decisions": rows,
        "counterfactual_exit_resolved": False,
        "actual_broker_terminal": False,
        "net_ev_pct": None,
        "economic_blocker": "execution_transition_model_not_bound",
        "authority": dict(AUTHORITY),
    }


def build_adaptive_exit_source_census(report: Mapping[str, Any]) -> dict[str, Any]:
    """Attach a hash-bound v2 child to the existing attribution owner.

    The available population is attribution anchors, NOT all account episodes.
    Until a first-fill/lot epoch and post-target ordered execution path producer
    exists, even excellent legacy timeout EV is not new-family evidence.
    """
    groups: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    malformed_count = 0
    contract_gaps: list[str] = []
    consumers = report.get("consumers") or {}
    if not isinstance(consumers, Mapping):
        consumers = {}
        contract_gaps.append("consumers_not_mapping")
    for consumer_name, collection_name in (
        ("widget_postclose_tuning", "symbols"),
        ("episode_machine_postclose_tuning", "profiles"),
    ):
        consumer = consumers.get(consumer_name) or {}
        collection = (
            consumer.get(collection_name) if isinstance(consumer, Mapping) else None
        )
        if not isinstance(collection, Mapping):
            contract_gaps.append(consumer_name + "_missing_or_invalid")
            continue
        for item in collection.values():
            anchors = item.get("anchor_results") if isinstance(item, Mapping) else None
            if not isinstance(anchors, list):
                malformed_count += 1
                continue
            for anchor in anchors:
                if not isinstance(anchor, Mapping):
                    malformed_count += 1
                    continue
                fields = tuple(
                    anchor.get(k)
                    for k in ("owner", "scope_id", "symbol", "session", "lifecycle_id")
                )
                if not all(isinstance(v, str) and v for v in fields):
                    malformed_count += 1
                    continue
                group = groups.setdefault(fields, {"anchor_count": 0, "stages": set()})
                group["anchor_count"] += 1
                stage = anchor.get("lifecycle_stage")
                if isinstance(stage, str):
                    group["stages"].add(stage)
    rows = []
    for key, group in sorted(groups.items()):
        rows.append(
            dict(zip(("owner", "scope_id", "symbol", "session", "lifecycle_id"), key))
            | {
                "anchor_count": group["anchor_count"],
                "stages": sorted(group["stages"]),
                "disposition": "source_invalid",
                "disposition_scope": "new_exit_contract_unbound_not_a_claim_of_corrupt_legacy_source",
                "first_depleted_stage": "first_fill_lot_epoch_ordered_exit_path_binding",
                "actual_economic_eligible": False,
                "counterfactual_economic_eligible": False,
            }
        )
    try:
        projection_hash = canonical_sha256(
            {
                "target_date": report.get("target_date"),
                "rolling_policy_source_contract": report.get(
                    "rolling_policy_source_contract"
                ),
                "sources": report.get("sources"),
                "consumers": consumers,
            }
        )
    except (TypeError, ValueError):
        projection_hash = None
        contract_gaps.append("source_projection_not_finite_json")
    payload = {
        "schema": "machine_adaptive_exit_source_census_v1",
        "family": "machine_adaptive_exit_v1",
        "target_date": report.get("target_date"),
        "status": (
            "blocked_source_contract"
            if rows or malformed_count or contract_gaps
            else "no_attribution_lifecycle_source"
        ),
        "contract_gaps": contract_gaps,
        "authority": dict(AUTHORITY),
        "rows": rows,
        "population_contract": {
            "denominator": "unique_owner_scope_symbol_session_lifecycle_in_attribution_anchors",
            "all_owner_episode_census_complete": False,
            "observed_unique_lifecycles": len(rows),
            "malformed_anchor_count": malformed_count,
            "eligible": 0,
            "source_invalid": len(rows),
            "unsupported_policy_epoch": 0,
            "outside_scope": 0,
            "conservation_valid": True,
        },
        "source_binding": {
            "kind": "canonical_projection_sha256_not_parent_byte_hash",
            "sha256": projection_hash,
        },
        "economic_acceptance": "not_evaluated",
        "net_ev_pct": None,
        "policy_promotion_candidates": [],
        "runtime_automation": {
            "postclose_child_connected": True,
            "preopen_consumer_registered": False,
            "runtime_adapter_connected": False,
            "eligible_for_next_preopen": False,
            "blocker": "initial_envelope_and_owned_sell_transition_not_implemented",
        },
        "next_owner": "machine_lifecycle_turnover_policy_research",
        "next_action": "bind_first_fill_lot_epoch_and_ordered_post_target_path_before_execution_replay",
    }
    payload["canonical_sha256"] = canonical_sha256(payload)
    return payload
