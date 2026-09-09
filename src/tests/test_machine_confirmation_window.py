from datetime import datetime, timedelta

import pytest

from src.trading.market.confirmation_window import build_confirmation_window
from src.trading.market.micro_confirmation import (
    build_live_dynamic_confirmation_checkpoint,
    evaluate_live_dynamic_confirmation_progress,
    build_dynamic_micro_confirmation_checkpoints,
)
from src.engine.monitoring.machine_microstructure_attribution import (
    _entry_checkpoint_ask_depletion_feature,
)

NOW = datetime.fromisoformat("2026-09-09T10:00:01+09:00")
MS = int(NOW.timestamp() * 1000)


def _rows(end_qty=80, buy=50):
    common = {"item": "005930_NX", "transport_epoch": 3}
    depths = [
        {
            **common,
            "received_at_ms": MS - 1000 + offset,
            "route_sequence": i,
            "best_bid": 10000,
            "best_ask": 10010,
            "best_ask_qty": qty,
        }
        for i, (offset, qty) in enumerate(((0, 100), (300, 20), (900, end_qty)), 1)
    ]
    trades = [
        {
            **common,
            "received_at_ms": MS - 1000 + offset,
            "route_sequence": i,
            "price": 10010,
            "volume": qty,
            "aggressor_side": side,
        }
        for i, (offset, qty, side) in enumerate(
            ((-100, 1, "SELL"), (200, buy, "BUY")), 1
        )
    ]
    return depths, trades


def _feature(depths, trades):
    return build_confirmation_window(
        depth_rows=depths,
        trade_rows=trades,
        item="005930_NX",
        epoch=3,
        checkpoint_at_ms=MS,
    )


def _live(depths, trades, *, now=NOW):
    snapshot = {
        "stocks": {
            "005930": {
                "machine_confirmation_routes": {
                    "route": {
                        "realtime_types": {
                            kind: {
                                "item": "005930_NX",
                                "transport_epoch": 3,
                                "observed_epoch": now.timestamp(),
                            }
                            for kind in ("0B", "0D")
                        },
                        "recent_depth": list(reversed(depths)),
                        "recent_trades": list(reversed(trades)),
                    }
                }
            }
        }
    }
    return build_live_dynamic_confirmation_checkpoint(
        snapshot=snapshot,
        now=now,
        signal_decision_at=NOW,
        checkpoint_sec=0,
        symbol="005930",
        route="NXT",
        owner="episode",
        baseline_fill_price=10010,
        owner_entry_limit_price=10010,
        owner_target_price=10050,
        round_trip_cost_pct=0.23,
        widget_take_profit=False,
    )[0]


def _offline(depths, trades):
    def raw(row):
        return {
            **row,
            "symbol": "005930",
            "venue": "NXT",
            "session_bucket": "NXT_REGULAR",
            "sequence_epoch": 3,
            "series_sequence": row["route_sequence"],
            "local_receive_timestamp": datetime.fromtimestamp(
                row["received_at_ms"] / 1000, NOW.tzinfo
            ).isoformat(),
        }

    return _entry_checkpoint_ask_depletion_feature(
        {
            "anchor_role": "episode_signal_decision_leg",
            "anchor_id": "signal:1",
            "anchor_at": NOW.isoformat(),
            "symbol": "005930",
            "expected_venues": ["NXT"],
            "expected_session_buckets": ["NXT_REGULAR"],
        },
        {
            "raw_depth_rows": [raw(r) for r in depths],
            "raw_market_rows": [raw(r) for r in trades],
        },
        source_complete=True,
        checkpoint_sec=0,
    )


@pytest.mark.parametrize(
    "end_qty,buy,ratio,refill,action",
    [
        (80, 50, 0.625, 0.75, "WAIT"),
        (100, 40, 0.5, 1.0, "REJECT"),
        (20, 50, 0.625, 0.0, "ENTER"),
    ],
)
def test_offline_and_live_use_identical_intermediate_path(
    end_qty, buy, ratio, refill, action
):
    depths, trades = _rows(end_qty, buy)
    report = _offline(depths, trades)
    feature = report["horizons"][0]
    live = _live(depths, trades)
    assert feature["eligible_for_feature_ablation"] is True
    assert live["source_quality_status"] == "eligible"
    for key, expected in (
        ("aggressive_buy_trade_backed_ratio", ratio),
        ("refill_ratio", refill),
    ):
        assert feature[key] == live[key] == expected
    assert live["window_source_sha256"] == feature["window_source_sha256"]
    assert evaluate_live_dynamic_confirmation_progress({0: live})["action"] == action
    checkpoints = build_dynamic_micro_confirmation_checkpoints(
        anchor_bbo={},
        future_bbo={},
        checkpoint_ask_depletion={
            "schema": "machine_entry_confirmation_checkpoint_ask_depletion_v1",
            "checkpoint_reports": {"0": report},
            "causal_past_only": True,
            "future_outcome_input_used": False,
            "runtime_effect": False,
            "trading_runtime_effect": False,
            "trading_decision_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        anchor_id="signal:1",
        signal_decision_at=NOW.isoformat(),
        symbol="005930",
        expected_venues=["NXT"],
        expected_session_buckets=["NXT_REGULAR"],
        owner="episode",
        baseline_fill_price=10010,
        owner_entry_limit_price=10010,
        owner_target_price=10050,
        round_trip_cost_pct=0.23,
        widget_take_profit=False,
    )
    for key in (
        "best_bid",
        "best_ask",
        "bid_return_bps",
        "bid_recovery_from_low_bps",
        "quote_age_ms",
        "net_edge_after_cost_bps",
    ):
        assert checkpoints[0][key] == live[key]
    assert (
        evaluate_live_dynamic_confirmation_progress({0: checkpoints[0]})["action"]
        == action
    )


def test_post_checkpoint_rows_do_not_change_earlier_metrics_even_when_live_late():
    depths, trades = _rows()
    before = _feature(depths, trades)
    depths.append(
        {
            **depths[-1],
            "received_at_ms": MS + 100,
            "route_sequence": 4,
            "best_ask_qty": 1,
        }
    )
    trades.append(
        {**trades[-1], "received_at_ms": MS + 100, "route_sequence": 3, "volume": 9999}
    )
    assert _feature(depths, trades) == before
    live = _live(depths, trades, now=NOW + timedelta(milliseconds=500))
    assert live["refill_ratio"] == 0.75
    assert live["window_source_sha256"] == before["window_source_sha256"]


def test_old_start_depth_cannot_be_hidden_by_fresh_endpoint():
    depths, trades = _rows()
    depths[0]["received_at_ms"] = MS - 60000
    assert "starting_depth_stale" in _feature(depths, trades)["source_gap_reasons"]
    assert _live(depths, trades)["source_quality_status"] == "source_gap"


@pytest.mark.parametrize(
    "change", ["gap", "epoch", "missing_sequence", "conflict", "unknown_side", "nan"]
)
def test_incomplete_or_corrupt_window_fails_closed(change):
    depths, trades = _rows()
    if change == "gap":
        depths[1]["route_sequence"] = 20
    if change == "epoch":
        depths[0]["transport_epoch"] = 4
    if change == "missing_sequence":
        trades[0].pop("route_sequence")
    if change == "conflict":
        depths.append({**depths[-1], "best_ask_qty": 17})
    if change == "unknown_side":
        trades[-1]["aggressor_side"] = "UNKNOWN"
    if change == "nan":
        depths[-1]["best_ask_qty"] = float("nan")
    assert _feature(depths, trades)["eligible_for_feature_ablation"] is False


def test_trade_at_different_price_does_not_explain_fixed_price_depletion():
    depths, trades = _rows()
    trades[-1]["price"] = 10020
    feature = _feature(depths, trades)
    assert feature["aggressive_buy_trade_backed_ratio"] == 0
    assert feature["unexplained_or_cancel_like_depletion_ratio"] == 1


def test_malformed_aggressor_and_epoch_produce_gap_not_producer_crash():
    depths, trades = _rows()
    trades[-1]["aggressor_side"] = {"invalid": True}
    assert "aggressor_side_unresolved" in _feature(depths, trades)["source_gap_reasons"]
    feature = build_confirmation_window(
        depth_rows=depths,
        trade_rows=trades,
        item="005930_NX",
        epoch=float("nan"),
        checkpoint_at_ms=MS,
    )
    assert "exact_epoch_identity_invalid" in feature["source_gap_reasons"]


def test_fixed_level_survives_downward_reprice():
    depths, trades = _rows()
    depths[1].update(
        best_ask=10000,
        best_ask_qty=400,
        ask_levels=[
            {"price": 10000, "quantity": 400},
            {"price": 10010, "quantity": 20},
        ],
    )
    feature = _feature(depths, trades)
    assert feature["eligible_for_feature_ablation"] is True
    assert feature["refill_ratio"] == 0.75
    assert feature["downward_reprice_observed"] is True
    depths[1].pop("ask_levels")
    assert (
        "fixed_ask_level_unobserved" in _feature(depths, trades)["source_gap_reasons"]
    )


def test_dense_window_retains_boundary_and_projection_sequence():
    from src.engine.bd_fbuy_accum_pre_scanner import _ws_machine_route_payload

    depths, trades = _rows()
    source_depth = []
    for i in range(110):
        source_depth.append(
            {
                **depths[0],
                "route_sequence": i + 1,
                "received_at_ms": MS - 1100 + i * 10,
                "ask_levels": [{"price": 10010, "quantity": 100}],
                "bid_levels": [{"price": 10000, "quantity": 100}],
            }
        )
    source = {
        "recent_depth_ticks_by_route": {"route": list(reversed(source_depth))},
        "recent_trade_ticks_by_route": {"route": list(reversed(trades))},
    }
    projected = _ws_machine_route_payload(source, now_ts=NOW.timestamp())["route"]
    assert len(projected["recent_depth"]) == 110
    assert projected["recent_depth"][-1]["route_sequence"] == 1
    feature = _feature(projected["recent_depth"], projected["recent_trades"])
    assert feature["eligible_for_feature_ablation"] is True


def test_live_progress_rejects_reconnect_against_original_signal_epoch(monkeypatch):
    import src.trading.market.micro_confirmation as module
    from src.tests.test_dynamic_micro_confirmation import _live_snapshot, _checkpoint

    snapshot = _live_snapshot(NOW)
    for route in snapshot["stocks"]["005930"]["machine_confirmation_routes"].values():
        for receipt in route["realtime_types"].values():
            receipt["transport_epoch"] = 4
        for receipt in route["recent_depth"] + route["recent_trades"]:
            receipt["transport_epoch"] = 4
    monkeypatch.setattr(
        module,
        "load_live_dynamic_confirmation_source",
        lambda **kwargs: (snapshot, "ready"),
    )
    result = module.advance_live_dynamic_confirmation(
        now=NOW,
        signal_decision_at=NOW - timedelta(seconds=1),
        checkpoint_sec=1,
        prior_checkpoints={0: _checkpoint(0, trade_backed_ratio=0.2)},
        prior_anchor={"best_bid": 10000, "sequence_epoch": 3, "item": "005930_NX"},
        symbol="005930",
        route="NXT",
        owner="episode",
        baseline_fill_price=10010,
        owner_entry_limit_price=10010,
        owner_target_price=10050,
        round_trip_cost_pct=0.23,
        widget_take_profit=False,
    )
    assert result["action"] != "ENTER"
    assert (
        "signal_anchor_route_or_epoch_changed"
        in result["checkpoints"]["1"]["source_gap_reasons"]
    )
