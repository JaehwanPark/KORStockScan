"""Causal synthetic tapes; neither profitability evidence nor live orders."""

from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from src.trading.market.target_pressure import pressure_from_snapshot, evaluate_pressure
from src.trading.market.micro_confirmation import LIVE_SNAPSHOT_PATH_ENV

NOW = datetime(2026, 9, 9, 4, tzinfo=timezone.utc)


def snapshot(now=NOW):
    cutoff = int(now.timestamp() * 1000)
    item = "005930_AL"

    def depth(seq, offset, qty):
        return dict(
            item=item,
            transport_epoch=1,
            route_sequence=seq,
            received_at_ms=cutoff + offset,
            best_bid=10100,
            best_ask=10110,
            best_ask_qty=qty,
            ask_levels=[dict(price=10110, quantity=qty)],
            bid_levels=[dict(price=10100, quantity=100)],
        )

    def trade(seq, offset, qty):
        return dict(
            item=item,
            transport_epoch=1,
            route_sequence=seq,
            received_at_ms=cutoff + offset,
            price=10110,
            volume=qty,
            aggressor_side="BUY",
        )

    return dict(
        schema_version="kiwoom_ws_dashboard_snapshot_v1",
        decision_authority="source_quality_only",
        runtime_effect=False,
        machine_confirmation_input_contract=dict(
            schema="machine_entry_confirmation_ws_snapshot_v1",
            decision_authority="market_data_input_only_no_order_authority",
            exact_route_required=True,
            causal_past_only=True,
            runtime_effect=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
        stocks={
            "005930": {
                "machine_confirmation_routes": {
                    "SOR": dict(
                        realtime_types={
                            k: dict(
                                item=item,
                                transport_epoch=1,
                                route_sequence=seq,
                                observed_epoch=(cutoff + offset) / 1000,
                            )
                            for k, seq, offset in (("0B", 4, -150), ("0D", 3, 0))
                        },
                        recent_depth=[
                            depth(1, -1000, 120),
                            depth(2, -100, 20),
                            depth(3, 0, 25),
                        ],
                        recent_trades=[
                            trade(1, -1100, 1),
                            trade(2, -800, 40),
                            trade(3, -300, 40),
                            trade(4, -150, 30),
                        ],
                        sequence_authority="local_projection_continuity_not_exchange_completeness",
                    )
                }
            }
        },
    )


def source(s):
    return s["stocks"]["005930"]["machine_confirmation_routes"]["SOR"]


def evaluate(s):
    return pressure_from_snapshot(
        snapshot=s,
        symbol="005930",
        route="SOR",
        quantity=10,
        target_price=10100,
        now=NOW,
    )


def test_combined_pressure_raises_one_tick_without_new_observation_wait():
    r = evaluate(snapshot())
    assert r["decision"] == "RAISE_ONE_TICK"
    assert r["next_price"] == 10110
    assert r["buy_speed_early_qty_per_sec"] == 80
    assert r["buy_speed_recent_qty_per_sec"] == 140
    assert r["feature"]["aggressive_buy_trade_backed_ratio"] == 1
    assert r["feature"]["refill_ratio"] == 0.05
    assert r["target_reach_basis"] == "executable_bid_gte_target_price"
    assert r["trade_target_touch_observed"] is True
    assert r["target_touch_buy_qty_observed"] == 110
    assert r["trade_watermark_age_ms"] == 150
    assert r["depth_watermark_age_ms"] == 0
    assert r["buy_qty_first_half_observed"] == 40
    assert r["buy_qty_recent_half_observed"] == 70
    assert r["source_scope"] == "exact_route_local_projection_not_exchange_completeness"
    assert r["source_quality_status"] == "eligible_local_projection"
    assert len(r["observed_window_trade_rows"]) == 3
    assert len(r["feature"]["source_hash_depth_rows"]) == 3
    assert len(r["feature"]["source_hash_trade_rows"]) == 4


def test_recent_half_zero_is_explicit_local_observation_not_market_completeness():
    s = snapshot()
    src = source(s)
    src["recent_trades"] = [
        src["recent_trades"][0],
        src["recent_trades"][1],
    ]
    src["realtime_types"]["0B"].update(
        route_sequence=2,
        observed_epoch=src["recent_trades"][1]["received_at_ms"] / 1000,
    )
    r = evaluate(s)
    assert r["buy_qty_first_half_observed"] == 40
    assert r["buy_qty_recent_half_observed"] == 0
    assert r["buy_speed_recent_qty_per_sec"] == 0
    assert r["source_complete_claim"] is None
    assert r["source_sequence_authority"].endswith("not_exchange_completeness")


@pytest.mark.parametrize(
    "case,reason",
    [
        ("slowing", "buy_speed_sustained"),
        ("cancellation", "depletion_trade_backed"),
        ("refill", "refill_weak"),
        ("wall", "next_wall_consumable"),
        ("selling", "buy_flow_dominant"),
        ("bid", "bid_support"),
        ("flat", "depletion_positive"),
    ],
)
def test_weak_pressure_retains_target(case, reason):
    s = snapshot()
    d, t = source(s)["recent_depth"], source(s)["recent_trades"]
    if case == "slowing":
        t[1]["volume"] = 150
    elif case == "cancellation":
        for r in t:
            r["volume"] = 1
    elif case == "refill":
        d[-1].update(best_ask_qty=80, ask_levels=[dict(price=10110, quantity=80)])
    elif case == "wall":
        # Large initial wall depletes through backed trades but stays too large.
        for r in d:
            r["best_ask_qty"] += 1000
            r["ask_levels"][0]["quantity"] += 1000
    elif case == "selling":
        t[1].update(aggressor_side="SELL", volume=200)
    elif case == "bid":
        d[0]["best_bid"] = 10105
    elif case == "flat":
        for r in d:
            r.update(best_ask_qty=120, ask_levels=[dict(price=10110, quantity=120)])
    r = evaluate(s)
    assert r["decision"] == "KEEP_TARGET"
    assert reason in r["reasons"]


@pytest.mark.parametrize(
    "case",
    ["gap", "epoch", "receipt", "unknown", "truncated", "incomplete", "future_receipt"],
)
def test_missing_or_conflicting_source_cannot_raise(case):
    s = snapshot()
    src = source(s)
    if case == "gap":
        src["recent_trades"].pop(2)
    elif case == "epoch":
        src["realtime_types"]["0B"]["transport_epoch"] = 2
    elif case == "receipt":
        src["realtime_types"]["0B"]["route_sequence"] += 1
    elif case == "unknown":
        src["recent_trades"][-1]["aggressor_side"] = "UNKNOWN"
    elif case == "truncated":
        src["recent_depth"].pop(0)
    elif case == "incomplete":
        src["source_complete"] = False
    else:
        src["realtime_types"]["0D"]["observed_epoch"] += 1
    with pytest.raises(ValueError):
        evaluate(s)


def test_duplicate_and_future_rows_do_not_inflate_speed():
    s = snapshot()
    before = evaluate(s)
    src = source(s)
    src["recent_trades"].append(deepcopy(src["recent_trades"][-1]))
    future = deepcopy(src["recent_trades"][-1])
    future.update(
        received_at_ms=int(NOW.timestamp() * 1000) + 1, route_sequence=5, volume=10000
    )
    src["recent_trades"].append(future)
    assert evaluate(s) == before


def test_loader_to_decision_and_malformed_document(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.json"
    monkeypatch.setenv(LIVE_SNAPSHOT_PATH_ENV, str(path))
    path.write_text(json.dumps(snapshot()))
    kwargs = dict(
        symbol="005930", route="SOR", quantity=10, target_price=10100, now=NOW
    )
    assert evaluate_pressure(**kwargs)["decision"] == "RAISE_ONE_TICK"
    path.write_text("[]")
    with pytest.raises(ValueError, match="contract_invalid"):
        evaluate_pressure(**kwargs)


@pytest.mark.parametrize("stamp", [float("nan"), float("inf"), True, "bad"])
def test_invalid_receipt_time_is_not_fresh(stamp):
    s = snapshot()
    source(s)["realtime_types"]["0B"]["observed_epoch"] = stamp
    with pytest.raises(ValueError, match="endpoint_mismatch"):
        evaluate(s)
