"""Whole-catalog study called by the existing attribution producer.

No new cron, market API call, or mutation of existing policies. Normalized
owner lot paths are accepted only with their exact content hash. Missing old
source remains a named gap, not a perpetual hard-coded 'not implemented'.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Mapping

from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    EvaluationContract,
    canonical_sha256,
    make_policy_payload,
    parse_exit_policy,
    assess_sample_attainability,
)
from src.trading.order.adaptive_exit.source import (
    OwnerScope,
    normalize_position,
    normalize_observation,
    validate_source_day,
)
from .machine_adaptive_exit_execution_replay import (
    ExitPath,
    ExecutionModel,
    replay_paired,
)
from .machine_adaptive_exit_evidence import build_evidence, build_candidate
from .machine_adaptive_exit_group_replay import GEOMETRY, RULE, replay_group_paired


def _valid_hash(payload):
    try:
        return isinstance(payload, Mapping) and payload.get(
            "canonical_sha256"
        ) == canonical_sha256(payload)
    except (ValueError, TypeError, OverflowError):
        return False


def decode_path(payload: dict, *, scope: OwnerScope) -> ExitPath:
    if not isinstance(payload, Mapping):
        raise ValueError("lot_path_not_mapping")
    if (
        payload.get("schema") != "machine_adaptive_exit_lot_path_v1"
        or payload.get("canonical_sha256") != canonical_sha256(payload)
        or payload.get("authority") != AUTHORITY
        or any(
            payload.get("authority", {}).get(k) is not v for k, v in AUTHORITY.items()
        )
    ):
        raise ValueError("lot_path_schema_hash_or_authority_invalid")
    p = normalize_position(payload["position"], scope=scope)
    return ExitPath(
        p,
        payload["entry_policy_hash"],
        payload["entry_order_key"],
        payload["target_order_key"],
        payload["target_ack_at_ms"],
        payload["horizon_end_ms"],
        payload["canonical_sha256"],
        tuple(normalize_observation(x, position=p) for x in payload["observations"]),
    )


def eligible_execution_paths(paths, policy, expected_lots):
    """Do not model per-lot cancel against an aggregated broker target.

    Partial trailing needs a strict, nonempty subset of the episode's owned
    lots. Unsupported episodes remain in the census/coverage denominator.
    """
    exclusions = {}
    by_episode = {}
    for path in paths:
        by_episode.setdefault(path.position.episode_id, []).append(path)
    for eid, rows in by_episode.items():
        target_keys = [row.target_order_key for row in rows]
        if len(set(target_keys)) != len(target_keys):
            exclusions[eid] = "aggregated_target_requires_owned_partial_cancel_adapter"
        elif policy.trail is not None:
            lots = set(expected_lots[eid])
            selected = lots.intersection(policy.runner_lot_ids)
            if not selected or selected == lots:
                exclusions[eid] = "partial_trailing_requires_nonempty_strict_lot_subset"
    return [p for p in paths if p.position.episode_id not in exclusions], exclusions


def shared_target_research(paths, policy, models, census, cfg, contract, payload):
    """Coupled economics stay outside the independent-target approval surface.

    This existing study owns the native research candidate. A future group
    approval consumer must bind its geometry/allocation, not reuse single-lot
    execution bounds or remove the independent replay's exclusion.
    """
    by_episode = {}
    for path in paths:
        by_episode.setdefault(path.position.episode_id, []).append(path)
    known_shared = {
        record["group"]["episode_id"]
        for record in (census.get("shared_target_groups") or {}).values()
        if isinstance(record, dict)
        and isinstance(record.get("group"), dict)
        and isinstance(record["group"].get("episode_id"), str)
        and record["group"]["episode_id"] in census["expected_episode_lots"]
    }
    for eid in known_shared:
        by_episode.setdefault(eid, [])
    expected = {
        eid: tuple(census["expected_episode_lots"][eid])
        for eid, rows in by_episode.items()
        if eid in known_shared or len({p.target_order_key for p in rows}) < len(rows)
    }
    if not expected:
        return None
    result = {
        "geometry": GEOMETRY,
        "policy_hash": policy.policy_hash,
        "authority": dict(AUTHORITY),
        "runtime_geometry_approved": False,
        "intended_consumer": "group_geometry_approval_not_independent_target_publisher",
        "expected_episode_lots": expected,
        "unsupported_episodes": {},
        "execution_results": [],
        "evidence": [],
        "native_research_candidate": None,
    }
    allocation = cfg.get("shared_target_book_allocation")
    if (
        not isinstance(allocation, dict)
        or set(allocation) != {"rule", "episode_lot_order"}
        or allocation["rule"] != RULE
        or not isinstance(allocation["episode_lot_order"], dict)
    ):
        result["status"] = "blocked_missing_frozen_book_allocation"
        return result | {"canonical_sha256": canonical_sha256(result)}
    for eid, lots in expected.items():
        rows = by_episode[eid]
        try:
            order = allocation["episode_lot_order"].get(eid)
            if (
                not isinstance(order, (tuple, list))
                or any(not isinstance(x, str) or not x for x in order)
                or len(order) != len(lots)
                or set(order) != set(lots)
                or {p.position.lot_id for p in rows} != set(lots)
                or len({p.target_order_key for p in rows}) != 1
            ):
                raise ValueError("complete_single_group_and_frozen_lot_order_required")
            result["execution_results"].extend(
                replay_group_paired(rows, [policy], models, lot_order=tuple(order))
            )
        except (ValueError, TypeError, KeyError) as exc:
            result["unsupported_episodes"][eid] = str(exc)
    for model in models:
        evidence = build_evidence(
            result["execution_results"],
            contract,
            source_trading_dates=tuple(census["source_trading_dates"]),
            model_id=model.model_id,
            expected_episode_lots=expected,
        )
        evidence["execution_geometry"] = GEOMETRY
        evidence["group_execution_hashes"] = sorted(
            {
                pair["baseline"]["group_execution_hash"]
                for pair in result["execution_results"]
                if pair["model_id"] == model.model_id
            }
        )
        evidence["unsupported_episodes"] = result["unsupported_episodes"]
        evidence["canonical_sha256"] = canonical_sha256(evidence)
        result["evidence"].append(evidence)
    result["native_research_candidate"] = build_candidate(
        base_evidence=result["evidence"][0],
        stress_evidence=result["evidence"][1],
        contract=contract,
        policy_payload=payload,
    )
    result["status"] = "coupled_research_evaluated_not_runtime_approved"
    return result | {"canonical_sha256": canonical_sha256(result)}


def run_study(
    *,
    target_date: str,
    catalog: tuple[OwnerScope, ...],
    source: Mapping | None,
    contract: Mapping | None,
) -> dict:
    """One bad scope is isolated; absence of the whole source cannot be success."""
    validate_source_day(target_date)
    result = {
        "schema": "machine_adaptive_exit_study_v1",
        "target_date": target_date,
        "authority": dict(AUTHORITY),
        "scope_count": len(catalog),
        "scopes": [],
        "policy_promotion_candidates": [],
        "evidence": [],
        "runtime_automation": {
            "postclose_child_connected": True,
            "eligible_for_next_preopen": False,
            "live_owner_adapter_connected": False,
        },
        "all_owner_episode_census_complete": False,
    }
    source_valid = (
        isinstance(source, Mapping)
        and source.get("schema") == "machine_adaptive_exit_owner_census_v1"
        and source.get("target_date") == target_date
        and _valid_hash(source)
        and source.get("authority") == AUTHORITY
        and all(source.get("authority", {}).get(k) is v for k, v in AUTHORITY.items())
        and isinstance(source.get("scopes"), dict)
        and isinstance(source.get("owner_envelope_valid", {}), Mapping)
    )
    contract_valid = (
        isinstance(contract, Mapping)
        and contract.get("schema") == "machine_adaptive_exit_study_contract_v1"
        and _valid_hash(contract)
        and isinstance(contract.get("scopes"), dict)
    )
    for scope in catalog:
        row = {
            "scope": asdict(scope),
            "scope_key": scope.key,
            "status": "blocked_missing_evidence",
            "first_depleted_stage": "owner_episode_census",
            "eligible_for_next_preopen": False,
            "unique_episodes": 0,
            "lot_paths": 0,
            "candidates": 0,
            "errors": [],
            "owner_census_valid": False,
            "execution_scope": True,
            "sample_attainability": [],
            "shared_target_research": [],
        }
        result["scopes"].append(row)
        try:
            if not source_valid:
                continue
            census = source["scopes"].get(scope.key)
            if (
                isinstance(census, Mapping)
                and census.get("execution_scope") is False
                or census is None
                and scope.owner == "widget"
                and not scope.profile.startswith("actual:")
            ):
                row.update(
                    status="not_applicable_nonexecution_scope",
                    execution_scope=False,
                    first_depleted_stage=None,
                )
                continue
            if isinstance(census, Mapping):
                # Preserve invalid-group reasons too; this diagnostic does not
                # turn an incomplete scope into an economic input.
                row["shared_target_groups"] = census.get("shared_target_groups", {})
                row["shared_target_runtime_supported"] = False
            if not isinstance(census, Mapping) or census.get("complete") is not True:
                continue
            lots = census["expected_episode_lots"]
            if (
                not isinstance(lots, dict)
                or not isinstance(census["lot_paths"], list)
                or any(
                    not isinstance(eid, str)
                    or not eid
                    or not isinstance(items, (list, tuple))
                    or not items
                    or any(not isinstance(lot, str) or not lot for lot in items)
                    or len(set(items)) != len(items)
                    for eid, items in lots.items()
                )
            ):
                raise ValueError("census_schema_invalid")
            row["owner_census_valid"] = True
            row["unique_episodes"] = len(lots)
            row["first_depleted_stage"] = "ordered_first_fill_lot_path"
            paths = [decode_path(p, scope=scope) for p in census["lot_paths"]]
            row["lot_paths"] = len(paths)
            if not lots and not paths:
                row.update(
                    status="healthy_no_natural_sample", first_depleted_stage=None
                )
                continue
            if not paths:
                continue
            identities = [(p.position.episode_id, p.position.lot_id) for p in paths]
            if len(set(identities)) != len(identities) or any(
                lot not in lots.get(eid, ()) for eid, lot in identities
            ):
                row["owner_census_valid"] = False
                raise ValueError("path_outside_census_or_duplicate")
            row["first_depleted_stage"] = "frozen_study_contract"
            if not contract_valid or scope.key not in contract["scopes"]:
                continue
            cfg = contract["scopes"][scope.key]
            grid = cfg["parameter_grid"]
            if (
                not isinstance(grid, list)
                or type(cfg["maximum_candidates"]) is not int
                or not 1 <= len(grid) <= cfg["maximum_candidates"] <= 12
            ):
                raise ValueError("bounded_frozen_parameter_grid_required")
            base, stress = [ExecutionModel(**m) for m in cfg["execution_models"]]
            if (
                base.model_id == stress.model_id
                or base.horizon_close_lead_ms is None
                or base.horizon_close_lead_ms != stress.horizon_close_lead_ms
                or stress.cancel_latency_ms < base.cancel_latency_ms
                or stress.submit_latency_ms < base.submit_latency_ms
                or stress.depth_participation > base.depth_participation
                or stress.extra_sell_cost_pct < base.extra_sell_cost_pct
                or stress.target_queue_confirmations < base.target_queue_confirmations
                or (asdict(base) | {"model_id": stress.model_id}) == asdict(stress)
            ):
                raise ValueError("stress_model_not_more_conservative")
            emitted = set()
            for params in grid:
                policy = make_policy_payload(scope_key=scope.key, parameters=params)
                if policy["policy_hash"] in emitted:
                    raise ValueError("duplicate_parameter_grid_point")
                emitted.add(policy["policy_hash"])
                evaluation = dict(cfg["evaluation"])
                evaluation.update(
                    scope_key=scope.key, policy_hash=policy["policy_hash"]
                )
                evaluation["contract_hash"] = canonical_sha256(evaluation)
                frozen = EvaluationContract(**evaluation)
                if frozen.holdout_end != target_date:
                    raise ValueError("study_target_date_mismatch")
                typed_policy = parse_exit_policy(policy)
                coupled = shared_target_research(
                    paths, typed_policy, (base, stress), census, cfg, frozen, policy
                )
                if coupled is not None:
                    row["shared_target_research"].append(coupled)
                supported_paths, geometry_exclusions = eligible_execution_paths(
                    paths, typed_policy, lots
                )
                pairs = [
                    pair
                    for path in supported_paths
                    for pair in replay_paired(path, [typed_policy], [base, stress])
                ]
                evidence = [
                    build_evidence(
                        pairs,
                        frozen,
                        source_trading_dates=tuple(census["source_trading_dates"]),
                        model_id=m.model_id,
                        expected_episode_lots=lots,
                    )
                    for m in (base, stress)
                ]
                for item in evidence:
                    item["unsupported_strategy_geometry_episodes"] = geometry_exclusions
                    item["canonical_sha256"] = canonical_sha256(item)
                candidate = build_candidate(
                    base_evidence=evidence[0],
                    stress_evidence=evidence[1],
                    contract=frozen,
                    policy_payload=policy,
                )
                result["evidence"].extend(evidence)
                result["policy_promotion_candidates"].append(candidate)
                row["candidates"] += 1
                counts = tuple(
                    sum(u["day"] == day for u in evidence[0]["episode_units"])
                    for day in census["source_trading_dates"]
                )
                window = cfg.get("rolling_trading_days")
                if window is None or not evidence[0]["source_quality_valid"]:
                    attainability = {
                        "status": "blocked_missing_evidence",
                        "reason": "declared_rolling_horizon_or_source_quality_missing",
                        "current": sum(counts),
                        "required": frozen.minimum_unique_episodes,
                        "deficit": max(0, frozen.minimum_unique_episodes - sum(counts)),
                        "projected_trading_days_to_floor": None,
                    }
                else:
                    attainability = assess_sample_attainability(
                        daily_mature_unique_counts=counts,
                        minimum=frozen.minimum_unique_episodes,
                        rolling_trading_days=window,
                        daily_hard_capacity=cfg.get("daily_hard_episode_capacity"),
                    )
                row["sample_attainability"].append(
                    {
                        "policy_hash": policy["policy_hash"],
                        "denominator": "base_modeled_complete_paired_unique_episodes",
                        "window_trading_days": window,
                        "source_quality_valid": evidence[0]["source_quality_valid"],
                        "holdout_and_economic_approval_separate": True,
                        **attainability,
                    }
                )
            row.update(status="study_evaluated", first_depleted_stage=None)
        except (ValueError, TypeError, KeyError, OverflowError, AttributeError) as exc:
            row["status"] = "source_or_contract_invalid"
            row["errors"] = [str(exc)]
            row["shared_target_research"] = []
            # Never publish a partial successful grid after another arm failed.
            result["evidence"] = [
                e for e in result["evidence"] if e["scope_key"] != scope.key
            ]
            result["policy_promotion_candidates"] = [
                c
                for c in result["policy_promotion_candidates"]
                if c["scope_key"] != scope.key
            ]
            row["candidates"] = 0
            row["sample_attainability"] = []
    result["all_owner_episode_census_complete"] = (
        bool(catalog)
        and source_valid
        and all(
            value is True for value in source.get("owner_envelope_valid", {}).values()
        )
        and any(row["execution_scope"] for row in result["scopes"])
        and all(
            row["owner_census_valid"]
            for row in result["scopes"]
            if row["execution_scope"]
        )
    )
    result["status"] = (
        "study_evaluated" if result["evidence"] else "blocked_missing_evidence"
    )
    result["canonical_sha256"] = canonical_sha256(result)
    return result
