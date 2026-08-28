from __future__ import annotations

from src.trading.order.entry_liquidity_guard import (
    ENTRY_LIQUIDITY_POLICY_CONTRACT,
    EntryLiquiditySnapshot,
    entry_liquidity_request_code,
    evaluate_entry_liquidity,
    parse_ka10004_entry_liquidity_snapshot,
)


def _snapshot(*, bid_qty: int, ask_qty: int, age_ms: int = 0):
    return EntryLiquiditySnapshot(
        True,
        "181710",
        "SOR",
        "181710_AL",
        best_bid=71_300,
        best_ask=71_500,
        best_bid_qty=bid_qty,
        best_ask_qty=ask_qty,
        bid_total_qty=1_255,
        ask_total_qty=880,
        age_ms=age_ms,
        received_ts_ms=1,
    )


def test_nhn_entry_snapshot_is_blocked_before_any_twenty_share_episode_order():
    decision = evaluate_entry_liquidity(
        _snapshot(bid_qty=97, ask_qty=93), requested_quantity=20
    )

    assert decision.allowed is False
    assert decision.reason == "entry_liquidity_touch_depth_insufficient"
    assert decision.required_each_side_quantity == 100


def test_touch_depth_must_pass_on_both_sides():
    assert evaluate_entry_liquidity(
        _snapshot(bid_qty=100, ask_qty=100), requested_quantity=20
    ).allowed
    assert not evaluate_entry_liquidity(
        _snapshot(bid_qty=99, ask_qty=10_000), requested_quantity=20
    ).allowed
    assert not evaluate_entry_liquidity(
        _snapshot(bid_qty=10_000, ask_qty=99), requested_quantity=20
    ).allowed
    assert ENTRY_LIQUIDITY_POLICY_CONTRACT["decision_authority"] == (
        "block_new_widget_or_episode_buy_only"
    )
    assert "existing_position_or_target_order_mutation" in (
        ENTRY_LIQUIDITY_POLICY_CONTRACT["forbidden_uses"]
    )


def test_larger_requested_quantity_uses_five_times_dynamic_floor():
    decision = evaluate_entry_liquidity(
        _snapshot(bid_qty=499, ask_qty=10_000), requested_quantity=100
    )

    assert decision.required_each_side_quantity == 500
    assert decision.allowed is False


def test_stale_or_invalid_source_fails_closed():
    stale = evaluate_entry_liquidity(
        _snapshot(bid_qty=1_000, ask_qty=1_000, age_ms=2_001),
        requested_quantity=20,
    )
    invalid = evaluate_entry_liquidity(
        EntryLiquiditySnapshot(False, "181710", "SOR", "181710_AL", error="api"),
        requested_quantity=20,
    )

    assert stale.reason == "entry_liquidity_snapshot_stale"
    assert invalid.reason == "api"
    assert not stale.allowed
    assert not invalid.allowed


def test_route_mapping_keeps_regular_sor_and_nxt_sessions_separate():
    assert entry_liquidity_request_code("181710", "KRX") == "181710_AL"
    assert entry_liquidity_request_code("181710", "SOR") == "181710_AL"
    assert entry_liquidity_request_code("181710", "NXT") == "181710_NX"


def test_normalized_ka10004_payload_requires_exact_route_and_freshness_contract():
    payload = {
        "source": "ka10004_rest_orderbook",
        "stock_code": "181710",
        "request_code": "181710_AL",
        "rest_freshness_basis": "response_received_epoch_ms",
        "best_bid": 71_300,
        "best_ask": 71_500,
        "best_bid_qty": 101,
        "best_ask_qty": 102,
        "bid_tot": 1_255,
        "ask_tot": 880,
        "rest_age_ms": 0,
        "rest_received_ts_ms": 1,
    }

    snapshot = parse_ka10004_entry_liquidity_snapshot(
        payload, symbol="181710", route="SOR"
    )
    wrong_route = parse_ka10004_entry_liquidity_snapshot(
        {**payload, "request_code": "181710_NX"},
        symbol="181710",
        route="SOR",
    )

    assert snapshot.source_ok
    assert snapshot.best_bid_qty == 101
    assert snapshot.best_ask_qty == 102
    assert not wrong_route.source_ok
    assert wrong_route.error == "ka10004_route_contract_invalid"
