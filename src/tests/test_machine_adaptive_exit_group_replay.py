"""Offline shared-order liquidity/consumer tests; no gateway or live files."""

from dataclasses import asdict, replace
from copy import deepcopy
from datetime import datetime

import pytest

from src.tests.test_machine_adaptive_exit_execution_replay import fixture
from src.tests.test_machine_adaptive_exit_policy import contract
from src.tests.test_machine_adaptive_exit_study import SOURCE_DAYS, signed
from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.group_decision import classify_group_request
from src.trading.order.adaptive_exit.models import TrailPolicy
from src.trading.order.adaptive_exit.source import OwnerScope
from src.engine.monitoring.machine_adaptive_exit_group_replay import (
    RULE,
    replay_group_execution,
    replay_group_paired,
)
from src.engine.monitoring.machine_adaptive_exit_study import run_study


def group_fixture(prices=(10080,) * 9, *, trailing=False):
    path, policy, model = fixture(prices)
    policy = replace(policy, hard_wall_sec=None)
    if trailing:
        policy = replace(
            policy,
            mode="fast_partial_trailing",
            soft_sec=60,
            trail=TrailPolicy(30, 0.5, 1, 1, 0.1),
            runner_lot_ids=("lot1",),
        )
    paths = []
    for lot, order in (("lot1", "1"), ("lot2", "3")):
        paths.append(
            replace(
                path,
                position=replace(path.position, lot_id=lot, position_epoch=lot),
                entry_order_key="2026-09-09:" + order,
                source_hash="source:" + lot,
                observations=tuple(
                    (c, replace(s, position_epoch=lot, supportive=trailing))
                    for c, s in path.observations
                ),
            )
        )
    return paths, policy, model


def run(paths, policy, model, **kwargs):
    return replay_group_execution(
        paths, policy, model, lot_order=("lot1", "lot2"), **kwargs
    )


def test_target_and_queue_depth_are_one_shared_budget():
    paths, policy, model = group_fixture((10110, 10110, 10080, 10080, 10080))
    rows = run(paths, policy, replace(model, depth_participation=0.1), baseline=True)
    assert [r["remaining_quantity"] for r in rows] == [0, 10]
    fills = [x for x in rows[0]["transitions"] if x["reason"] == "modeled_target_fill"]
    assert sum(x["quantity"] for x in fills) == 10
    assert rows[1]["net_pnl_krw"] is None


def test_target_costs_once_and_modeled_book_is_not_broker_attribution():
    paths, policy, model = group_fixture((10110,) * 5)
    rows = run(paths, policy, replace(model, depth_participation=0.1), baseline=True)
    assert all(r["counterfactual_exit_resolved"] for r in rows)
    assert sum(r["net_pnl_krw"] for r in rows) == pytest.approx(1540)
    assert all(
        r["actual_lot_fill_attribution"] is None
        and r["actual_broker_terminal"] is False
        for r in rows
    )
    assert rows[0]["closed_at_ms"] < rows[1]["closed_at_ms"]


def test_group_policy_request_matches_runtime_no_implicit_whole_exit():
    paths, policy, model = group_fixture((10010,) * 7)
    rows = run(paths, policy, model)
    reason = classify_group_request(
        {"lot1": "REQUEST_EARLY_EXIT", "lot2": "REQUEST_EARLY_EXIT"}, set()
    )
    assert reason == "UNSUPPORTED_GROUP_EXIT_REQUIRES_OWNER_RECOVERY"
    assert all(
        r["resolution_reason"] == reason and r["net_ev_pct"] is None for r in rows
    )


def test_common_horizon_is_latency_aware_and_same_for_both_arms():
    paths, policy, model = group_fixture()
    model = replace(model, horizon_close_lead_ms=3000)
    pairs = replay_group_paired(paths, [policy], [model], lot_order=("lot1", "lot2"))
    for pair in pairs:
        a, b = pair["baseline"], pair["candidate"]
        assert a["counterfactual_exit_resolved"] and b["counterfactual_exit_resolved"]
        assert (
            a["closed_at_ms"]
            == b["closed_at_ms"]
            == paths[0].position.first_fill_at_ms + 7000
        )
        assert a["net_pnl_krw"] == b["net_pnl_krw"]
        assert not a["group_execution"]["runtime_geometry_approved"]


def test_runner_fills_then_target_uses_separate_whole_successor_budget():
    paths, policy, model = group_fixture(
        (10080, 10080, 10065, 10065) + (10080,) * 5, trailing=True
    )
    rows = run(paths, policy, replace(model, horizon_close_lead_ms=3000))
    assert all(r["counterfactual_exit_resolved"] for r in rows), rows
    assert rows[0]["closed_at_ms"] < rows[1]["closed_at_ms"]
    intents = [
        x
        for x in rows[0]["transitions"]
        if x["reason"] == "pooled_marketable_limit_intent"
    ]
    assert [(x["chain"], x["quantity"]) for x in intents] == [
        ("runner", 10),
        ("whole", 10),
    ]


def test_late_target_fill_cannot_reuse_requested_runner_quantity():
    paths, policy, model = group_fixture(
        (10080, 10110, 10080, 10080, 10080), trailing=True
    )
    # One quote takes 15: ten nonrunner shares, then five runner BOOK shares.
    rows = run(
        paths,
        policy,
        replace(
            model,
            cancel_latency_ms=2500,
            target_queue_confirmations=1,
            depth_participation=0.15,
        ),
    )
    assert all(
        r["resolution_reason"]
        == "partial_cancel_quantity_changed_requires_owner_recovery"
        for r in rows
    )
    assert all(r["net_pnl_krw"] is None for r in rows)


def test_pending_cancel_cannot_advance_the_frozen_runner_decision_book():
    paths, policy, model = group_fixture((10080,) * 7, trailing=True)
    rows = run(paths, policy, replace(model, cancel_latency_ms=2500))
    assert all(
        r["resolution_reason"] == "group_decision_invalid:observation_path_gap"
        and r["net_pnl_krw"] is None
        for r in rows
    )
    assert not any(
        e["reason"] == "pooled_marketable_limit_intent" for e in rows[0]["transitions"]
    )


def test_whole_close_waits_for_working_runner_and_preserves_its_reservation():
    paths, policy, model = group_fixture((10080, 10080) + (10065,) * 10, trailing=True)
    rows = run(
        paths,
        policy,
        replace(model, depth_participation=0.01, horizon_close_lead_ms=6000),
    )
    trace = rows[0]["transitions"]
    intents = [x for x in trace if x["reason"] == "pooled_marketable_limit_intent"]
    assert [x["chain"] for x in intents] == ["runner", "whole"], trace
    whole = intents[1]
    assert whole["at_ms"] == paths[0].position.first_fill_at_ms + 6000
    assert whole["quantity"] == 16  # Four runner shares filled before cancel terminal.
    fills_before = [
        x
        for x in trace
        if x["reason"] == "modeled_sell_fill" and x["at_ms"] <= whole["at_ms"]
    ]
    assert all(x["lot_id"] == "lot1" for x in fills_before)
    assert all(r["net_pnl_krw"] is None for r in rows)


def test_target_and_working_sell_cannot_both_spend_same_quote_depth():
    paths, policy, model = group_fixture(
        (10080, 10080, 10065) + (10110,) * 4, trailing=True
    )
    model = replace(model, target_queue_confirmations=1, depth_participation=0.05)
    rows = run(paths, policy, model)
    by_time = {}
    for event in rows[0]["transitions"]:
        if event["reason"] in {"modeled_target_fill", "modeled_sell_fill"}:
            by_time[event["at_ms"]] = by_time.get(event["at_ms"], 0) + event["quantity"]
    assert by_time and max(by_time.values()) <= 5
    assert all(
        not r["counterfactual_exit_resolved"] for r in rows if r["remaining_quantity"]
    )


def test_source_quote_reuse_does_not_create_liquidity():
    paths, policy, model = group_fixture((10110,) * 3)
    # The last observation repeats the same exact quote, with a new evaluation sequence.
    adjusted = []
    for path in paths:
        obs = [
            (c, replace(s, quote_sequence=i))
            for i, (c, s) in enumerate(path.observations)
        ]
        c, s = obs[-1]
        obs[-1] = c, replace(s, quote_sequence=1, quote_at_ms=obs[1][1].quote_at_ms)
        adjusted.append(replace(path, observations=tuple(obs)))
    rows = run(
        adjusted,
        policy,
        replace(model, target_queue_confirmations=1, depth_participation=0.05),
        baseline=True,
    )
    assert sum(r["remaining_quantity"] for r in rows) == 10


@pytest.mark.parametrize(
    "damage", ["future_gap", "market", "clock", "order", "cost", "missing_lot"]
)
def test_bad_group_cannot_select_early_winners(damage):
    paths, policy, model = group_fixture((10110,) * 5)
    second = paths[1]
    if damage == "future_gap":
        second = replace(second, observations=second.observations[:-1])
    elif damage == "market":
        obs = list(second.observations)
        c, s = obs[-1]
        obs[-1] = c, replace(s, source_hash="different")
        second = replace(second, observations=tuple(obs))
    elif damage == "clock":
        c, s = second.observations[-1]
        second = replace(
            second,
            observations=second.observations[:-1]
            + ((replace(c, verified_halt_ms=None), s),),
        )
    elif damage == "order":
        second = replace(second, entry_order_key=paths[0].entry_order_key)
    elif damage == "cost":
        second = replace(
            second, position=replace(second.position, round_trip_cost_pct=0.1)
        )
    elif damage == "missing_lot":
        with pytest.raises(ValueError):
            run(paths[:1], policy, model)
        return
    if damage in {"order", "cost"}:
        with pytest.raises(ValueError):
            run([paths[0], second], policy, model)
    else:
        rows = run([paths[0], second], policy, model)
        assert all(
            not r["counterfactual_exit_resolved"] and r["net_ev_pct"] is None
            for r in rows
        )


def study_fixture():
    scope = OwnerScope(
        "widget", "actual:005930:KRX_REGULAR", "005930", "KRX", "KRX_REGULAR"
    )
    raw, policy, base = group_fixture()
    policy = replace(policy, scope_key=scope.key)
    base = replace(base, horizon_close_lead_ms=3000)
    stress = replace(base, model_id="stress", extra_sell_cost_pct=0.02)
    paths, expected = [], {}
    for day, eid in (("2026-09-01", "one"), ("2026-09-09", "two")):
        start = int(datetime.fromisoformat(day + "T09:00:00+09:00").timestamp() * 1000)
        expected[eid] = ["lot1", "lot2"]
        for path in raw:
            offset = start - path.position.first_fill_at_ms
            p = replace(
                path.position,
                owner_id="widget",
                scope_key=scope.key,
                episode_id=eid,
                first_fill_at_ms=start,
            )
            paths.append(
                signed(
                    dict(
                        schema="machine_adaptive_exit_lot_path_v1",
                        authority=dict(AUTHORITY),
                        position=asdict(p),
                        entry_policy_hash="entry",
                        entry_order_key=eid + ":" + p.lot_id,
                        target_order_key=eid + ":target",
                        target_ack_at_ms=start,
                        horizon_end_ms=start + 8000,
                        observations=[
                            {
                                "clock": asdict(replace(c, now_ms=c.now_ms + offset)),
                                "snapshot": asdict(
                                    replace(
                                        s,
                                        scope_key=scope.key,
                                        quote_at_ms=s.quote_at_ms + offset,
                                        observed_at_ms=s.observed_at_ms + offset,
                                    )
                                ),
                            }
                            for c, s in path.observations
                        ],
                    )
                )
            )
    source = signed(
        dict(
            schema="machine_adaptive_exit_owner_census_v1",
            target_date="2026-09-09",
            authority=dict(AUTHORITY),
            scopes={
                scope.key: dict(
                    complete=True,
                    expected_episode_lots=expected,
                    lot_paths=paths,
                    source_trading_dates=list(SOURCE_DAYS),
                )
            },
        )
    )
    params = asdict(policy)
    del params["policy_hash"], params["scope_key"]
    evaluation = asdict(
        replace(contract(), minimum_unique_episodes=2, minimum_holdout_episodes=1)
    )
    for key in ("contract_hash", "scope_key", "policy_hash"):
        del evaluation[key]
    cfg = signed(
        dict(
            schema="machine_adaptive_exit_study_contract_v1",
            scopes={
                scope.key: dict(
                    parameter_grid=[params],
                    maximum_candidates=1,
                    shared_target_book_allocation={
                        "rule": RULE,
                        "episode_lot_order": deepcopy(expected),
                    },
                    execution_models=[asdict(base), asdict(stress)],
                    evaluation=evaluation,
                )
            },
        )
    )
    return dict(target_date="2026-09-09", catalog=(scope,), source=source, contract=cfg)


def test_existing_study_consumes_coupled_pairs_without_independent_approval_leak():
    args = study_fixture()
    result = run_study(**args)
    assert result["status"] == "study_evaluated", result
    research = result["scopes"][0]["shared_target_research"][0]
    assert research["status"] == "coupled_research_evaluated_not_runtime_approved"
    assert len(research["execution_results"]) == 8  # 2 episodes x 2 lots x 2 models
    assert [len(e["episode_units"]) for e in research["evidence"]] == [2, 2]
    assert all(not e["episode_units"] for e in result["evidence"])
    native = research["native_research_candidate"]
    assert native["recommendation_id"].startswith("adaptive-exit:")
    assert native["recommendation_id"] not in {
        x["recommendation_id"] for x in result["policy_promotion_candidates"]
    }
    assert native["eligible_for_next_preopen"] is False
    assert research["canonical_sha256"] == canonical_sha256(research)
    from src.engine.monitoring.machine_microstructure_attribution import render_markdown

    text = render_markdown(
        {
            "target_date": "2026-09-09",
            "status": "ok",
            "decision": "source_only",
            "summary": {
                "dynamic_symbol_count": 0,
                "widget_symbol_count": 1,
                "episode_profile_count": 0,
                "anchor_count": 0,
                "matched_anchor_count": 0,
                "producer_consumer_gap_count": 0,
            },
            "producer_consumer_gaps": [],
            "rolling_policy_research_v2": {"all_scope_study": result},
        }
    )
    assert native["recommendation_id"] in text
    from src.engine.automation.machine_adaptive_exit_policy_apply import (
        select_approved_source,
    )

    child = signed(
        {
            "schema": "machine_adaptive_exit_source_census_v1",
            "target_date": args["target_date"],
            "authority": dict(AUTHORITY),
            "all_scope_study": result,
        }
    )
    with pytest.raises(ValueError, match="approved_candidate_missing_or_duplicate"):
        select_approved_source(
            {"target_date": args["target_date"], "rolling_policy_research_v2": child},
            envelope={
                "source_date": args["target_date"],
                "source_child_sha256": child["canonical_sha256"],
                "scopes": {
                    args["catalog"][0].key: {
                        "candidate_sha256": native["canonical_sha256"]
                    }
                },
            },
        )


def test_missing_frozen_allocation_blocks_only_coupled_research():
    args = study_fixture()
    cfg = args["contract"]
    del cfg["scopes"][args["catalog"][0].key]["shared_target_book_allocation"]
    cfg["canonical_sha256"] = canonical_sha256(cfg)
    result = run_study(**args)
    assert result["status"] == "study_evaluated"
    coupled = result["scopes"][0]["shared_target_research"][0]
    assert coupled["status"] == "blocked_missing_frozen_book_allocation"
    assert coupled["native_research_candidate"] is None


def test_missing_group_paths_remain_in_the_declared_denominator():
    args = study_fixture()
    census = args["source"]["scopes"][args["catalog"][0].key]
    census["shared_target_groups"] = {
        "source:one": {"group": {"episode_id": "one"}},
        "source:two": {"group": {"episode_id": "two"}},
    }
    census["lot_paths"] = [
        p for p in census["lot_paths"] if p["position"]["episode_id"] != "two"
    ]
    args["source"]["canonical_sha256"] = canonical_sha256(args["source"])
    result = run_study(**args)
    coupled = result["scopes"][0]["shared_target_research"][0]
    assert coupled["unsupported_episodes"] == {
        "two": "complete_single_group_and_frozen_lot_order_required"
    }
    for evidence in coupled["evidence"]:
        assert evidence["expected_unique_episodes"] == 2
        assert evidence["resolved_coverage_pct"] == 50
        assert evidence["right_censored_pct"] == 50


def test_natural_shared_source_reaches_existing_study_with_distinct_fill_clocks(
    tmp_path, monkeypatch
):
    import json
    from src.engine.monitoring import machine_adaptive_exit_source as producer
    from src.tests.test_machine_adaptive_exit_target_group import source as group_source
    from src.tests.test_machine_adaptive_exit_natural_source import (
        DAY,
        SCOPE,
        FIELD,
        collect,
        raw_path,
        write,
    )

    monkeypatch.setattr(producer, "HORIZON_SEC", 30)
    for day in ("2026-09-08", DAY):
        receipt, legs = group_source()
        receipt = json.loads(json.dumps(receipt).replace(DAY, day))
        legs = json.loads(json.dumps(legs).replace(DAY, day))
        receipt["entries"][1]["first_fill_observation"]["first_observed_at"] = (
            day + "T09:00:00.500+09:00"
        )
        receipt["canonical_sha256"] = canonical_sha256(receipt)
        for leg in legs:
            leg[FIELD] = {day + ":2222222": deepcopy(receipt)}
        census, anchors = collect(tmp_path, legs, day=day)
        assert len(anchors) == 2
        bound = producer.bind_ordered_paths(
            census, {a["anchor_id"]: raw_path(day=day, price=10080) for a in anchors}
        )
        scope = bound["scopes"][SCOPE.key]
        assert scope["conservation_valid"]
        assert scope["disposition_counts"] == {"eligible": 2}, scope["lots"]
        paths = scope["lot_paths"]
        assert len({p["horizon_end_ms"] for p in paths}) == 1
        assert len({p["position"]["first_fill_at_ms"] for p in paths}) == 2
        if day != DAY:
            write(
                tmp_path
                / "reports/machine_microstructure_attribution"
                / f"machine_microstructure_attribution_{day}.json",
                {"rolling_policy_research_v2": {"natural_owner_census": bound}},
            )
    rolling = producer.merge_census_history(bound, report_root=tmp_path / "reports")
    scope = rolling["scopes"][SCOPE.key]
    assert len(scope["shared_target_groups"]) == 2
    assert len(bound["scopes"][SCOPE.key]["shared_target_groups"]) == 1
    cfg = producer.propose_study_contract(rolling)
    assert cfg["scopes"][SCOPE.key]["maximum_candidates"] == 5
    result = run_study(target_date=DAY, catalog=(SCOPE,), source=rolling, contract=cfg)
    scope_result = result["scopes"][0]
    assert scope_result["status"] == "study_evaluated", scope_result
    assert len(scope_result["shared_target_research"]) == 5
    for research in scope_result["shared_target_research"]:
        assert len(research["execution_results"]) == 8
        assert all(len(e["episode_units"]) == 2 for e in research["evidence"])
        assert (
            research["native_research_candidate"]["eligible_for_next_preopen"] is False
        )
    assert all(not e["episode_units"] for e in result["evidence"])
