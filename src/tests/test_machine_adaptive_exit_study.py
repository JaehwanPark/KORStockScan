from dataclasses import asdict, replace
from datetime import datetime

import pytest

from src.engine.monitoring.machine_adaptive_exit_study import (
    run_study,
    eligible_execution_paths,
)
from src.engine.monitoring.machine_adaptive_exit_evidence import build_evidence
from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.source import (
    OwnerScope,
    catalog_from_owner_inventories,
)
from src.tests.test_machine_adaptive_exit_execution_replay import fixture
from src.tests.test_machine_adaptive_exit_policy import contract
from src.tests.test_machine_adaptive_exit_decision import trail_inputs

SOURCE_DAYS = (
    "2026-09-01",
    "2026-09-02",
    "2026-09-03",
    "2026-09-04",
    "2026-09-07",
    "2026-09-08",
    "2026-09-09",
)


def test_partial_runner_needs_a_strict_subset_and_independent_targets():
    path, _, _ = fixture()
    policy, *_ = trail_inputs()
    one = path.position.lot_id
    second = replace(
        path,
        position=replace(path.position, lot_id="lot2"),
        target_order_key="2026-09-09:3",
    )
    expected = {path.position.episode_id: (one, "lot2")}
    supported, gaps = eligible_execution_paths([path, second], policy, expected)
    assert len(supported) == 2 and not gaps
    supported, gaps = eligible_execution_paths(
        [path], policy, {path.position.episode_id: (one,)}
    )
    assert not supported and "strict_lot_subset" in next(iter(gaps.values()))
    second = replace(second, target_order_key=path.target_order_key)
    supported, gaps = eligible_execution_paths([path, second], policy, expected)
    assert not supported and "partial_cancel_adapter" in next(iter(gaps.values()))


def signed(payload):
    return payload | {"canonical_sha256": canonical_sha256(payload)}


def pair(day, eid, lot="leg1", model="base", pnl=10):
    start = int(datetime.fromisoformat(day + "T09:00:00+09:00").timestamp() * 1000)
    shared = dict(
        owner_id="widget",
        policy_hash="policy",
        scope_key="scope",
        episode_id=eid,
        lot_id=lot,
        position_epoch=eid + lot,
        entry_policy_hash="entry",
        cost_contract_hash="cost",
        source_hash=eid + lot,
        first_fill_at_ms=start,
        horizon_end_ms=start + 600000,
        entry_notional_krw=10000,
        model_hash=model,
        authority=dict(AUTHORITY),
        actual_broker_terminal=False,
        counterfactual_exit_resolved=True,
        remaining_quantity=0,
    )
    return dict(
        policy_hash="policy",
        model_id=model,
        baseline=shared | dict(baseline=True, net_pnl_krw=0, net_ev_pct=0),
        candidate=shared | dict(baseline=False, net_pnl_krw=pnl, net_ev_pct=pnl / 100),
    )


def test_episode_not_leg_count_and_zero_yield_days_preserved():
    c = replace(contract(), minimum_unique_episodes=2, minimum_holdout_episodes=1)
    pairs = [
        pair(d, e, leg)
        for d, e in (("2026-09-01", "one"), ("2026-09-09", "two"))
        for leg in ("a", "b")
    ]
    e = build_evidence(
        pairs,
        c,
        source_trading_dates=SOURCE_DAYS,
        model_id="base",
        expected_episode_lots={"one": ("a", "b"), "two": ("a", "b")},
    )
    assert e["unique_episodes"] == 2 and e["holdout_unique_episodes"] == 1
    assert e["observed_days"] == 7 and e["primary_paired_net_pnl_uplift_krw"] == 40
    assert e["primary_paired_net_ev_uplift_pct_points"] == pytest.approx(0.1)


def test_missing_leg_and_censored_lot_not_completed_zero_pnl():
    c = contract()
    pairs = [pair("2026-09-01", "one")]
    e = build_evidence(
        pairs,
        c,
        source_trading_dates=SOURCE_DAYS,
        model_id="base",
        expected_episode_lots={"one": ("leg1", "leg2")},
    )
    assert e["unique_episodes"] == 0 and e["right_censored_pct"] == 100
    assert e["primary_candidate_net_ev_pct"] is None


def test_turnover_cost_profit_frequency_and_capital_minutes_use_same_pairs():
    p = pair("2026-09-01", "one", pnl=10)
    p["baseline"]["closed_at_ms"] = p["baseline"]["first_fill_at_ms"] + 120000
    p["candidate"]["closed_at_ms"] = p["candidate"]["first_fill_at_ms"] + 60000
    e = build_evidence(
        [p],
        contract(),
        source_trading_dates=SOURCE_DAYS,
        model_id="base",
        expected_episode_lots={"one": ("leg1",)},
    )
    metrics = e["turnover_diagnostics"]
    assert metrics["candidate"][
        "net_profitable_episodes_per_source_trading_day"
    ] == pytest.approx(1 / 7)
    assert metrics["base"]["capital_krw_minutes"] == 20000
    assert metrics["candidate"]["capital_krw_minutes"] == 10000
    assert metrics["candidate"]["net_profit_per_capital_minute_pct"] == pytest.approx(
        0.1
    )
    p["candidate"].pop("closed_at_ms")
    e = build_evidence(
        [p],
        contract(),
        source_trading_dates=SOURCE_DAYS,
        model_id="base",
        expected_episode_lots={"one": ("leg1",)},
    )
    assert e["turnover_diagnostics"]["candidate"]["capital_krw_minutes"] is None


def test_purge_boundary_uses_horizon_not_actual_early_close():
    p = pair("2026-09-01", "one")
    for x in (p["baseline"], p["candidate"]):
        x["horizon_end_ms"] = int(
            datetime.fromisoformat("2026-09-02T09:00:00+09:00").timestamp() * 1000
        )
    e = build_evidence(
        [p],
        contract(),
        source_trading_dates=SOURCE_DAYS,
        model_id="base",
        expected_episode_lots={"one": ("leg1",)},
    )
    assert e["purged_episode_ids"] == ["one"] and e["unique_episodes"] == 0


def test_duplicate_lot_and_wrong_cost_do_not_pass_quality():
    p = pair("2026-09-01", "one")
    kwargs = dict(
        source_trading_dates=SOURCE_DAYS,
        model_id="base",
        expected_episode_lots={"one": ("leg1",)},
    )
    assert not build_evidence([p, p], contract(), **kwargs)["source_quality_valid"]
    p["candidate"]["cost_contract_hash"] = "other"
    assert not build_evidence([p], contract(), **kwargs)["cost_contract_valid"]


def test_zero_yield_trading_days_cannot_be_omitted_from_calendar():
    with pytest.raises(ValueError, match="missing_or_nontrading"):
        build_evidence(
            [],
            contract(),
            source_trading_dates=("2026-09-01", "2026-09-02", "2026-09-09"),
            model_id="base",
            expected_episode_lots={},
        )


def test_incomplete_or_invalid_lot_census_is_never_healthy_empty():
    scope = OwnerScope("episode", "p", "005930", "SOR", "morning")
    for lots, expected in (
        ({"episode": []}, "source_or_contract_invalid"),
        ({"episode": ["leg1"]}, "blocked_missing_evidence"),
    ):
        source = signed(
            dict(
                schema="machine_adaptive_exit_owner_census_v1",
                target_date="2026-09-09",
                authority=dict(AUTHORITY),
                scopes={
                    scope.key: dict(
                        complete=True, expected_episode_lots=lots, lot_paths=[]
                    )
                },
            )
        )
        result = run_study(
            target_date="2026-09-09", catalog=(scope,), source=source, contract=None
        )
        assert result["scopes"][0]["status"] == expected
        if not lots["episode"]:
            assert not result["all_owner_episode_census_complete"]
        else:
            assert (
                result["scopes"][0]["first_depleted_stage"]
                == "ordered_first_fill_lot_path"
            )


def test_all_widget_sessions_included_even_with_anchor_in_only_one():
    widget = {
        "005930": {
            "symbol": "005930",
            "anchor_results": [
                {
                    "scope_id": "actual",
                    "session": "KRX_REGULAR",
                    "expected_venues": ["KRX"],
                }
            ],
            "session_contexts": {
                "005930:KRX_REGULAR": {"expected_venues": ["KRX"]},
                "005930:NXT_AFTERMARKET": {"expected_venues": ["NXT"]},
            },
        }
    }
    scopes = catalog_from_owner_inventories(widget, {})
    assert len(scopes) == 2
    assert {s.session for s in scopes} == {"KRX_REGULAR", "NXT_AFTERMARKET"}


def test_invalid_inventory_row_is_isolated_without_hiding_healthy_scopes():
    errors = []
    scopes = catalog_from_owner_inventories(
        {},
        {
            "valid": {
                "symbol": "005930",
                "session": "morning",
                "expected_venues": ["SOR"],
            },
            "bad": {"symbol": None, "session": None, "expected_venues": []},
        },
        errors=errors,
    )
    assert len(scopes) == 1 and len(errors) == 1 and "bad" in errors[0]


def test_all_registered_low_price_profiles_have_scope_even_without_samples():
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    from datetime import date

    profiles = profiles_for_target_date(date(2026, 9, 9))
    scopes = catalog_from_owner_inventories(
        {},
        {
            k: {"symbol": v.symbol, "session": v.session, "expected_venues": ["SOR"]}
            for k, v in profiles.items()
        },
    )
    r = run_study(target_date="2026-09-09", catalog=scopes, source=None, contract=None)
    assert len(r["scopes"]) == len(profiles)
    assert all(
        row["first_depleted_stage"] == "owner_episode_census" for row in r["scopes"]
    )
    assert all(not row["eligible_for_next_preopen"] for row in r["scopes"])


def test_malformed_global_source_is_gap_not_parent_crash_or_fake_empty():
    s = OwnerScope("widget", "widget", "005930", "KRX", "KRX_REGULAR")
    r = run_study(
        target_date="2026-09-09",
        catalog=(s,),
        source={
            "schema": "machine_adaptive_exit_owner_census_v1",
            "target_date": "2026-09-09",
            "bad": float("nan"),
        },
        contract=None,
    )
    assert r["scopes"][0]["status"] == "blocked_missing_evidence"


def test_complete_empty_census_is_not_structural_exhaustion_or_live_ready():
    s = OwnerScope("episode", "p", "005930", "SOR", "morning")
    source = signed(
        dict(
            schema="machine_adaptive_exit_owner_census_v1",
            target_date="2026-09-09",
            authority=dict(AUTHORITY),
            scopes={s.key: dict(complete=True, expected_episode_lots={}, lot_paths=[])},
        )
    )
    r = run_study(target_date="2026-09-09", catalog=(s,), source=source, contract=None)
    assert r["scopes"][0]["status"] == "healthy_no_natural_sample"
    assert r["all_owner_episode_census_complete"]


def test_full_study_computes_native_candidates_without_publishing_policy():
    scope = OwnerScope("widget", "p", "005930", "KRX", "KRX_REGULAR")
    path, policy, base = fixture((10080, 10080, 10080, 10080, 10080, 10080, 10080))
    policy = replace(policy, scope_key=scope.key, hard_wall_sec=3)
    base = replace(base, horizon_close_lead_ms=2000)
    stress = replace(base, model_id="stress", extra_sell_cost_pct=0.02)
    paths = []
    for day, eid in (("2026-09-01", "one"), ("2026-09-09", "two")):
        start = int(datetime.fromisoformat(day + "T09:00:00+09:00").timestamp() * 1000)
        offset = start - path.position.first_fill_at_ms
        p = replace(
            path.position,
            owner_id="widget",
            scope_key=scope.key,
            episode_id=eid,
            first_fill_at_ms=start,
        )
        obs = [
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
        ]
        paths.append(
            signed(
                dict(
                    schema="machine_adaptive_exit_lot_path_v1",
                    authority=dict(AUTHORITY),
                    position=asdict(p),
                    entry_policy_hash="entry",
                    entry_order_key=eid + ":1",
                    target_order_key=eid + ":2",
                    target_ack_at_ms=start,
                    horizon_end_ms=start + 6000,
                    observations=obs,
                )
            )
        )
    census = signed(
        dict(
            schema="machine_adaptive_exit_owner_census_v1",
            target_date="2026-09-09",
            authority=dict(AUTHORITY),
            scopes={
                scope.key: dict(
                    complete=True,
                    expected_episode_lots={
                        eid: (path.position.lot_id,) for eid in ("one", "two")
                    },
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
    for k in ("contract_hash", "scope_key", "policy_hash"):
        del evaluation[k]
    cfg = signed(
        dict(
            schema="machine_adaptive_exit_study_contract_v1",
            scopes={
                scope.key: dict(
                    parameter_grid=[params],
                    maximum_candidates=1,
                    execution_models=[asdict(base), asdict(stress)],
                    evaluation=evaluation,
                )
            },
        )
    )
    r = run_study(
        target_date="2026-09-09", catalog=(scope,), source=census, contract=cfg
    )
    assert r["status"] == "study_evaluated", r
    assert len(r["policy_promotion_candidates"]) == 1 and len(r["evidence"]) == 2
    assert r["policy_promotion_candidates"][0]["recommendation_id"].startswith(
        "adaptive-exit:"
    )
    assert not r["policy_promotion_candidates"][0]["eligible_for_next_preopen"]
