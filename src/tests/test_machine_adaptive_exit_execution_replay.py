from dataclasses import replace, asdict

import pytest

from src.engine.monitoring.machine_adaptive_exit_execution_replay import (
    ExecutionModel,
    ExitPath,
    replay_execution,
)
from src.trading.order.adaptive_exit.models import Clock, Snapshot
from src.tests.test_machine_adaptive_exit_decision import inputs, trail_inputs


def fixture(prices=(10010, 10010, 10010, 10010, 10010), *, mode="time_progress_exit"):
    policy, p, _, _, _ = inputs()
    policy = replace(
        policy,
        mode=mode,
        soft_sec=1,
        extension_sec=1,
        max_observation_gap_ms=1001,
        hard_wall_sec=3,
    )
    observations = tuple(
        (
            Clock(p.first_fill_at_ms + i * 1000, 0),
            Snapshot(
                p.first_fill_at_ms + i * 1000,
                p.first_fill_at_ms + i * 1000,
                "epoch",
                i,
                f"source:{i}",
                p.scope_key,
                p.position_epoch,
                price + 10,
                ((price, 100),),
                False,
                0,
            ),
        )
        for i, price in enumerate(prices)
    )
    path = ExitPath(
        p,
        "entry-hash",
        "2026-09-09:1",
        "2026-09-09:2",
        p.first_fill_at_ms,
        p.first_fill_at_ms + (len(prices) - 1) * 1000,
        "raw-source",
        observations,
    )
    model = ExecutionModel(
        "base", 100, 100, 5000, 1, 1.0, 0.01, 2, "unresolved_not_zero"
    )
    return path, policy, model


def test_early_exit_executes_only_after_cancel_and_submit_latency():
    path, policy, model = fixture()
    r = replay_execution(path, policy, model)
    assert r["counterfactual_exit_resolved"]
    assert r["closed_at_ms"] == path.position.first_fill_at_ms + 3000
    assert r["actual_broker_terminal"] is False
    assert r["net_pnl_krw"] == pytest.approx(100 - 230 - 10.01)
    assert [t["phase"] for t in r["transitions"]] == ["cancel", "residual", "sell"]


def test_target_touch_does_not_imply_queue_fill():
    path, policy, model = fixture((10110, 10010, 10010, 10010, 10010))
    r = replay_execution(path, policy, model, baseline=True)
    assert not r["counterfactual_exit_resolved"]
    assert r["net_ev_pct"] is None


def test_target_filled_during_cancel_wins_over_replacement_sell():
    path, policy, model = fixture((10010, 10010, 10120, 10120, 10120))
    model = replace(model, cancel_latency_ms=3000)
    r = replay_execution(path, policy, model)
    assert r["counterfactual_exit_resolved"]
    assert not any(t["phase"] == "sell" for t in r["transitions"])


def test_sparse_or_short_or_reversed_full_horizon_cannot_select_winners():
    path, policy, model = fixture((10120, 10120, 10120, 10120, 10120))
    for observations in (
        path.observations[:-1],
        tuple(reversed(path.observations)),
        (path.observations[0], path.observations[-1]),
    ):
        r = replay_execution(
            replace(path, observations=observations), policy, model, baseline=True
        )
        assert not r["counterfactual_exit_resolved"]
        assert r["net_ev_pct"] is None


def test_partial_fill_does_not_become_completed_or_zero():
    path, policy, model = fixture()
    model = replace(model, depth_participation=0.01)
    r = replay_execution(path, policy, model)
    assert r["remaining_quantity"] == 8
    assert r["net_pnl_krw"] is None


def test_model_requires_explicit_bounds():
    _, _, model = fixture()
    for fields in (
        {"depth_participation": True},
        {"maximum_sell_attempts": 0},
        {"sell_ttl_ms": False},
        {"cancel_latency_ms": -1},
        {"extra_sell_cost_pct": float("nan")},
    ):
        with pytest.raises(ValueError):
            replace(model, **fields)


def test_combined_mode_retains_time_progress_even_when_trailing_geometry_impossible():
    policy, p, s, c, state = trail_inputs(age=60000)
    policy = replace(policy, mode="time_progress_and_trailing")
    from src.trading.order.adaptive_exit.decision import evaluate_exit

    s = replace(
        s,
        bid_levels=((p.entry_price, 100),),
        best_ask=p.entry_price + 10,
        supportive=False,
        improvement_bps=0,
    )
    assert evaluate_exit(policy, p, s, c, state).action == "REQUEST_EARLY_EXIT"


def test_mode_roundtrip_includes_all_three_without_implicit_risk_defaults():
    from src.trading.config.machine_adaptive_exit_policy import (
        make_policy_payload,
        parse_exit_policy,
    )

    p, *_ = trail_inputs()
    for mode in (
        "time_progress_exit",
        "fast_partial_trailing",
        "time_progress_and_trailing",
    ):
        params = asdict(p)
        del params["policy_hash"], params["scope_key"]
        params["mode"] = mode
        if mode == "time_progress_exit":
            params["trail"] = None
            params["runner_lot_ids"] = ()
        assert (
            parse_exit_policy(
                make_policy_payload(scope_key="test", parameters=params)
            ).mode
            == mode
        )


def test_repeated_quote_does_not_manufacture_target_queue_confirmations():
    path, policy, model = fixture(prices=(10200,) * 5)
    first = path.observations[0][1]
    # One quote, repeatedly evaluated with distinct checkpoint ordinals.
    path = replace(
        path,
        observations=tuple(
            (clock, replace(snapshot, quote_at_ms=first.quote_at_ms, quote_sequence=7))
            for clock, snapshot in path.observations
        ),
    )
    policy = replace(policy, max_quote_age_ms=5000, hard_wall_sec=None, soft_sec=10)
    result = replay_execution(path, policy, model, baseline=True)
    assert not result["counterfactual_exit_resolved"]
    assert not any(t["reason"] == "modeled_target_fill" for t in result["transitions"])


def test_same_quote_sequence_with_changed_book_is_rejected():
    path, policy, model = fixture()
    path = replace(
        path,
        observations=tuple(
            (clock, replace(snapshot, quote_sequence=7))
            for clock, snapshot in path.observations
        ),
    )
    result = replay_execution(path, policy, model)
    assert result["resolution_reason"] == "quote_sequence_conflict_or_regression"
