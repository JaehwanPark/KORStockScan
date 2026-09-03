from __future__ import annotations

from copy import deepcopy

from src.trading.market.micro_confirmation import (
    DYNAMIC_CONFIRMATION_METRIC_CONTRACT,
    build_dynamic_micro_confirmation_checkpoints,
    evaluate_dynamic_micro_confirmation,
    modeled_dynamic_target_price,
    validate_dynamic_micro_confirmation_replay,
)


def _checkpoint(
    checkpoint_sec: int,
    *,
    bid_return_bps: float = 0.0,
    trade_backed_ratio: float = 0.8,
    refill_ratio: float = 0.1,
    downward_reprice: bool = False,
) -> dict:
    return {
        "checkpoint_sec": checkpoint_sec,
        "causal_past_only": True,
        "future_outcome_input_used": False,
        "source_quality_status": "eligible",
        "bbo_observed": True,
        "depth_backed": True,
        "same_sequence_epoch": True,
        "sequence_epoch": 7,
        "best_bid": 10_000,
        "best_ask": 10_010,
        "bid_return_bps": bid_return_bps,
        "bid_return_reference": "causal_pre_signal_best_bid",
        "spread_bps": 10.0,
        "quote_age_ms": 50,
        "modeled_target_price": 10_050,
        "net_edge_after_cost_bps": 50.0,
        "owner_price_feasible": True,
        "aggressive_buy_trade_backed_ratio": trade_backed_ratio,
        "refill_ratio": refill_ratio,
        "downward_reprice_observed": downward_reprice,
    }


def test_dynamic_confirmation_enters_at_first_supportive_checkpoint() -> None:
    checkpoints = {
        0: _checkpoint(0, bid_return_bps=-1, trade_backed_ratio=0.2),
        1: _checkpoint(1, bid_return_bps=-1, trade_backed_ratio=0.4),
        3: _checkpoint(3),
        5: _checkpoint(5),
    }

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "ENTER"
    assert replay["selected_delay_sec"] == 3
    assert [row["action"] for row in replay["checkpoint_decisions"]] == [
        "WAIT",
        "WAIT",
        "ENTER",
    ]
    assert replay["runtime_effect"] is False
    assert replay["allowed_runtime_apply"] is False
    assert replay["broker_order_forbidden"] is True
    assert replay["metric_contract"] == DYNAMIC_CONFIRMATION_METRIC_CONTRACT
    assert validate_dynamic_micro_confirmation_replay(replay) == (True, None)


def test_dynamic_confirmation_rejects_at_first_adverse_checkpoint() -> None:
    checkpoints = {
        0: _checkpoint(0, bid_return_bps=-1, trade_backed_ratio=0.2),
        1: _checkpoint(1, refill_ratio=1.0),
        3: _checkpoint(3),
        5: _checkpoint(5),
    }

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "REJECT"
    assert replay["terminal_reason"] == "adverse_checkpoint_veto"
    assert replay["selected_delay_sec"] is None
    assert len(replay["checkpoint_decisions"]) == 2


def test_dynamic_confirmation_does_not_impute_missing_early_checkpoint() -> None:
    missing = _checkpoint(0)
    missing["source_quality_status"] = "source_gap"
    checkpoints = {
        0: missing,
        1: _checkpoint(1),
        3: _checkpoint(3),
        5: _checkpoint(5),
    }

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "ENTER"
    assert replay["selected_delay_sec"] == 1
    assert replay["checkpoint_decisions"][0]["state"] == "SOURCE_GAP"
    assert replay["checkpoint_decisions"][0]["action"] == "WAIT"


def test_dynamic_confirmation_blocks_future_input_and_finishes_insufficient() -> None:
    checkpoints = {}
    for checkpoint_sec in (0, 1, 3, 5):
        row = _checkpoint(checkpoint_sec)
        row["future_outcome_input_used"] = True
        checkpoints[checkpoint_sec] = row

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "INSUFFICIENT_DATA"
    assert replay["source_quality_status"] == "source_gap"
    assert all(row["state"] == "SOURCE_GAP" for row in replay["checkpoint_decisions"])


def test_dynamic_confirmation_ambiguous_path_expires_as_reject() -> None:
    checkpoints = {
        checkpoint_sec: _checkpoint(
            checkpoint_sec,
            bid_return_bps=-1,
            trade_backed_ratio=0.2,
            refill_ratio=0.2,
        )
        for checkpoint_sec in (0, 1, 3, 5)
    }

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "REJECT"
    assert replay["terminal_reason"] == "confirmation_window_expired_without_support"
    assert replay["checkpoint_decisions"][-1]["action"] == "REJECT"


def test_dynamic_confirmation_incomplete_window_is_not_counted_as_reject() -> None:
    checkpoints = {
        checkpoint_sec: _checkpoint(
            checkpoint_sec,
            bid_return_bps=-1,
            trade_backed_ratio=0.2,
            refill_ratio=0.2,
        )
        for checkpoint_sec in (0, 1, 3, 5)
    }
    checkpoints[3]["source_quality_status"] = "source_gap"

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "INSUFFICIENT_DATA"
    assert replay["terminal_reason"] == (
        "confirmation_window_source_quality_incomplete"
    )
    assert replay["source_quality_status"] == "source_gap"


def test_dynamic_confirmation_requires_positive_net_edge_and_owner_price() -> None:
    checkpoints = {checkpoint: _checkpoint(checkpoint) for checkpoint in (0, 1, 3, 5)}
    checkpoints[0]["net_edge_after_cost_bps"] = -0.1
    checkpoints[1]["owner_price_feasible"] = False

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["terminal_action"] == "ENTER"
    assert replay["selected_delay_sec"] == 3


def test_checkpoint_builder_rejects_cross_epoch_confirmation() -> None:
    future_bbo = {
        str(checkpoint): {
            "observed": True,
            "best_bid": 10_000,
            "best_ask": 10_010,
            "spread_bps": 10.0,
            "quote_age_from_horizon_ms": 50,
            "depth_backed": True,
            "sequence_epoch": 8,
        }
        for checkpoint in (1, 3, 5)
    }
    checkpoints = build_dynamic_micro_confirmation_checkpoints(
        anchor_bbo={
            "observed": True,
            "best_bid": 10_000,
            "best_ask": 10_010,
            "spread_bps": 10.0,
            "quote_age_from_signal_ms": 50,
            "depth_backed": True,
            "sequence_epoch": 7,
        },
        future_bbo=future_bbo,
        checkpoint_ask_depletion={
            "schema": "machine_entry_confirmation_checkpoint_ask_depletion_v1",
            "checkpoint_reports": {
                str(checkpoint): {
                    "schema": "scalp_micro_reversion_ask_depletion_v2",
                    "context": {
                        "symbol": "005930",
                        "venue": "KRX",
                        "session_bucket": "KRX_REGULAR",
                        "sequence_epoch": 7 if checkpoint == 0 else 8,
                    },
                    "decision_anchor_binding": {
                        "decision_anchor_id": "episode:test",
                        "decision_anchor_at": "2026-08-27T10:00:00+09:00",
                        "checkpoint_sec": checkpoint,
                        "checkpoint_at": (f"2026-08-27T10:00:0{checkpoint}+09:00"),
                        "window_horizon_ms": 900,
                        "future_outcome_input_used": False,
                    },
                    "horizons": [
                        {
                            "horizon_ms": 900,
                            "eligible_for_feature_ablation": True,
                            "aggressive_buy_trade_backed_ratio": (
                                0.2 if checkpoint == 0 else 0.8
                            ),
                            "refill_ratio": 0.1,
                            "downward_reprice_observed": False,
                        }
                    ],
                    "runtime_effect": False,
                    "trading_runtime_effect": False,
                    "trading_decision_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                }
                for checkpoint in (0, 1, 3, 5)
            },
            "causal_past_only": True,
            "future_outcome_input_used": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "broker_order_forbidden": True,
        },
        anchor_id="episode:test",
        signal_decision_at="2026-08-27T10:00:00+09:00",
        symbol="005930",
        expected_venues=["KRX"],
        expected_session_buckets=["KRX_REGULAR"],
        owner="episode",
        baseline_fill_price=10_000,
        owner_entry_limit_price=10_020,
        owner_target_price=10_010,
        round_trip_cost_pct=0.23,
        widget_take_profit=False,
    )

    replay = evaluate_dynamic_micro_confirmation(checkpoints)

    assert replay["checkpoint_decisions"][0]["state"] == "AMBIGUOUS"
    assert replay["checkpoint_decisions"][1]["state"] == "SOURCE_GAP"
    assert replay["checkpoint_decisions"][1]["same_sequence_epoch"] is False
    assert replay["terminal_action"] == "INSUFFICIENT_DATA"
    assert replay["source_quality_status"] == "source_gap"


def test_dynamic_confirmation_replay_validator_rejects_tampered_action() -> None:
    replay = evaluate_dynamic_micro_confirmation(
        {checkpoint: _checkpoint(checkpoint) for checkpoint in (0, 1, 3, 5)}
    )
    replay["terminal_action"] = "REJECT"
    replay["selected_delay_sec"] = None

    valid, reason = validate_dynamic_micro_confirmation_replay(replay)

    assert valid is False
    assert reason == "dynamic_replay_reconstruction_mismatch"


def test_future_outcome_fields_cannot_change_checkpoint_action() -> None:
    checkpoints = {checkpoint: _checkpoint(checkpoint) for checkpoint in (0, 1, 3, 5)}
    perturbed = deepcopy(checkpoints)
    for row in perturbed.values():
        row["future_terminal_profit_pct"] = -999.0
        row["future_target_adverse_first_hit"] = "adverse_first"

    control = evaluate_dynamic_micro_confirmation(checkpoints)
    candidate = evaluate_dynamic_micro_confirmation(perturbed)

    assert candidate == control


def test_dynamic_target_preserves_episode_ticks_and_widget_ratio() -> None:
    assert (
        modeled_dynamic_target_price(
            owner="episode",
            baseline_fill_price=100,
            owner_target_price=101,
            checkpoint_ask=99,
            widget_take_profit=False,
        )
        == 100.0
    )
    assert (
        modeled_dynamic_target_price(
            owner="widget",
            baseline_fill_price=100,
            owner_target_price=101,
            checkpoint_ask=99,
            widget_take_profit=True,
        )
        == 100.0
    )
    assert (
        modeled_dynamic_target_price(
            owner="main",
            baseline_fill_price=100,
            owner_target_price=101,
            checkpoint_ask=99,
            widget_take_profit=False,
        )
        is None
    )
