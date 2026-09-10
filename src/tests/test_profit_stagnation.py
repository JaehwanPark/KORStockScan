"""Pure candidate tests: no broker, policy publication or live process."""

import math

import pytest

from src.trading.order.profit_stagnation import (
    positive_net_stagnation,
    stagnation_window,
)


def candidate(at=1000.0, previous=None, **overrides):
    args = dict(
        identity="widget:005930:episode1:NXT:policy1:cost1",
        now=at,
        quote_at=at,
        quote_id=str(at),
        entry_price=10000.0,
        executable_bid=10040.0,
        quantity=10,
        available_quantity=10,
        round_trip_cost_pct=0.23,
        slippage_bps=5.0,
        previous=previous,
    )
    args.update(overrides)
    return positive_net_stagnation(**args)


def mature(**overrides):
    state = None
    for second in range(1000, 1181):
        result, state = candidate(float(second), state, **overrides)
    return result, state


def test_small_positive_profit_does_not_require_main_one_percent():
    result, _ = mature()
    assert result["should_exit"] is True
    assert result["net_return_pct"] == pytest.approx(0.1198)
    assert result["elapsed_sec"] == 180


def test_no_immediate_exit_just_because_profitable():
    result, state = candidate()
    assert result["reason"] == "anchor_reset"
    result, _ = candidate(1001, state)
    assert result["reason"] == "waiting"


@pytest.mark.parametrize("bid", [10000, 10020, 9990])
def test_costs_prevent_gross_positive_or_loss_exit(bid):
    result, state = mature(executable_bid=bid)
    assert not result["should_exit"]
    assert result["reason"] == "nonpositive_net"
    assert state == {}


def test_zero_net_is_not_positive_and_small_net_is_not_rounded_to_zero():
    result, _ = candidate(executable_bid=10000, round_trip_cost_pct=0, slippage_bps=0)
    assert not result["should_exit"]
    result, _ = mature(executable_bid=10000.001, round_trip_cost_pct=0, slippage_bps=0)
    assert result["should_exit"]
    assert 0 < result["net_return_pct"] < 0.0001


@pytest.mark.parametrize(
    "entry,bid,cost", [(10000, 10023, 0.23), (1000, 1001, 0.1), (20000, 20060, 0.3)]
)
def test_exact_cost_break_even_never_becomes_positive_from_float_error(
    entry, bid, cost
):
    result, state = mature(
        entry_price=entry, executable_bid=bid, round_trip_cost_pct=cost, slippage_bps=0
    )
    assert result["net_return_pct"] == 0
    assert not result["should_exit"]
    assert state == {}


def test_invalid_persisted_peak_does_not_keep_mature_window():
    _, state = mature()
    state["peak"] = -1
    result, new = candidate(1181, state)
    assert result["reason"] == "anchor_reset"
    assert new["started"] == 1181


def test_later_nonpositive_price_invalidates_previously_mature_candidate():
    result, state = mature()
    assert result["should_exit"]
    result, state = candidate(1181, state, executable_bid=10020)
    assert result["reason"] == "nonpositive_net"
    assert state == {}


@pytest.mark.parametrize(
    "overrides",
    [
        {"round_trip_cost_pct": None},
        {"round_trip_cost_pct": -0.1},
        {"round_trip_cost_pct": math.nan},
        {"slippage_bps": None},
        {"slippage_bps": -1},
        {"slippage_bps": 10000},
        {"quantity": True},
        {"quantity": 0},
        {"available_quantity": 9},
        {"entry_price": 0},
        {"entry_price": math.inf},
        {"quote_at": 1001},
        {"quote_at": 997},
        {"max_observation_gap_sec": 0},
        {"min_sec": True},
        {"min_sec": 0},
        {"max_profit_move": -1},
        {"identity": ""},
        {"quote_id": ""},
        {"now": 10**500},
    ],
)
def test_invalid_inputs_reset_only_decision_state(overrides):
    _, old = mature()
    before = dict(old)
    result, state = candidate(previous=old, **overrides)
    assert not result["should_exit"]
    assert state == {}
    assert old == before


@pytest.mark.parametrize(
    "change",
    [
        {"identity": "other-owner"},
        {"quantity": 5},
        {"entry_price": 10001},
        {"round_trip_cost_pct": 0.24},
        {"slippage_bps": 6},
        {"min_sec": 181},
    ],
)
def test_identity_cost_quantity_or_policy_change_restarts_window(change):
    _, state = mature()
    result, new = candidate(1181, state, **change)
    assert result["reason"] == "anchor_reset"
    assert new["started"] == 1181


def test_no_outage_or_clock_regression_is_counted_as_stagnation():
    _, state = mature()
    for at in (1190, 1100):
        result, new = candidate(at, state)
        assert result["reason"] == "anchor_reset"
        assert new["started"] == at


def test_repeated_quote_cannot_advance_elapsed_or_bridge_gap():
    _, state = candidate()
    result, next_state = candidate(1002, state, quote_at=1000, quote_id="1000.0")
    assert result["reason"] == "duplicate_quote"
    assert next_state == state
    result, state = candidate(1003, next_state, quote_at=1000, quote_id="1000.0")
    assert state == {}
    assert not result["should_exit"]


def test_rising_or_falling_price_resets_absolute_move_window():
    _, state = mature()
    for price in (10060, 10025):
        result, new = candidate(1181, state, executable_bid=price, max_profit_move=0.01)
        assert not result["should_exit"]
        assert result["reason"] in ("anchor_reset", "nonpositive_net")


def legacy_window(
    profit,
    peak,
    now,
    started,
    anchor_profit,
    anchor_peak,
    min_sec,
    max_profit_move,
    max_peak_improve,
):
    # Independent frozen copy of the previous main arithmetic, not a call back
    # into the new helper. Main's prior/eligibility fields are tested separately.
    move, improvement = abs(profit - anchor_profit), peak - anchor_peak
    if started <= 0 or move > max_profit_move or improvement > max_peak_improve:
        return dict(
            should_exit=False,
            reason="anchor_reset",
            elapsed_sec=0,
            anchor_profit=float(profit),
            anchor_peak=float(peak),
            profit_move=0.0,
            peak_improve=0.0,
        )
    elapsed = max(0, int(float(now) - started))
    fields = dict(
        should_exit=elapsed >= min_sec,
        elapsed_sec=elapsed,
        anchor_profit=anchor_profit,
        anchor_peak=anchor_peak,
        profit_move=move,
        peak_improve=max(0.0, improvement),
    )
    if elapsed >= min_sec:
        fields.update(
            min_sec=min_sec,
            max_profit_move=max_profit_move,
            max_peak_improve=max_peak_improve,
        )
    else:
        fields["reason"] = "waiting"
    return fields


@pytest.mark.parametrize("profit", [1.0, 1.1, 1.149, 1.151, 0.84])
@pytest.mark.parametrize("peak", [0.9, 1.0, 1.099, 1.101])
@pytest.mark.parametrize(
    "now,started", [(1000, 0), (1179.9, 1000), (1180, 1000), (900, 1000)]
)
def test_shared_main_arithmetic_parity(profit, peak, now, started):
    args = dict(
        profit=profit,
        peak=peak,
        now=now,
        started=started,
        anchor_profit=1.0,
        anchor_peak=1.0,
        min_sec=180,
        max_profit_move=0.15,
        max_peak_improve=0.1,
    )
    assert stagnation_window(**args) == legacy_window(**args)
