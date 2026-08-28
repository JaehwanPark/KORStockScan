from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway

from src.trading.order.entry_liquidity_guard import (
    ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT,
    ENTRY_LIQUIDITY_POLICY_CONTRACT,
    KST,
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
    entry_liquidity_request_code,
    evaluate_entry_execution_velocity,
    evaluate_entry_liquidity,
    parse_ka10003_entry_execution_velocity_snapshot,
    parse_ka10004_entry_liquidity_snapshot,
)
from src.trading.samsung_afternoon_one_share.gateway import (
    KiwoomAfternoonOneShareGateway,
)
from src.trading.samsung_midday_one_share.gateway import KiwoomMiddayOneShareGateway
from src.trading.samsung_morning_one_share.gateway import KiwoomOneShareGateway
from src.trading.widget_auto_trade.gateway import KiwoomSharedTokenOrderGateway
from src.utils import kiwoom_utils


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


def _velocity_ticks(times: list[str], *, volume: int = 10, venue: str = "KRX"):
    return [
        {
            "time": print_time,
            "raw": {
                "tm": print_time,
                "cur_prc": "+73500",
                "cntr_trde_qty": f"+{volume}",
                "acc_trde_qty": str(100_000 - index * volume),
                "stex_tp": venue,
            },
        }
        for index, print_time in enumerate(times)
    ]


def _velocity_snapshot(times: list[str], *, volume: int = 10):
    return parse_ka10003_entry_execution_velocity_snapshot(
        _velocity_ticks(times, volume=volume),
        symbol="111770",
        route="SOR",
        observed_at=datetime(2026, 8, 28, 15, 12, 32, tzinfo=KST),
    )


def test_latest_ten_prints_within_twenty_seconds_allow_new_episode_buy():
    snapshot = _velocity_snapshot(
        [
            "151232",
            "151231",
            "151230",
            "151229",
            "151228",
            "151227",
            "151226",
            "151225",
            "151224",
            "151223",
        ]
    )
    decision = evaluate_entry_execution_velocity(snapshot, requested_quantity=20)

    assert snapshot.source_ok
    assert snapshot.recent_print_span_ms == 9_000
    assert snapshot.recent_volume == 100
    assert decision.allowed
    assert decision.reason == "entry_execution_velocity_sufficient"
    assert decision.required_recent_volume == 40


def test_cj_cgv_youngone_and_nhn_slow_print_fixtures_are_blocked():
    fixtures = {
        "cj_cgv": [
            "151231",
            "151231",
            "151230",
            "151230",
            "151226",
            "151210",
            "151147",
            "151147",
            "151146",
            "151146",
        ],
        "youngone": [
            "151230",
            "151228",
            "151224",
            "151224",
            "151224",
            "151224",
            "151208",
            "151208",
            "151200",
            "151155",
        ],
        "nhn": [
            "151229",
            "151222",
            "151216",
            "151203",
            "151201",
            "151201",
            "151201",
            "151200",
            "151200",
            "151200",
        ],
    }

    for times in fixtures.values():
        decision = evaluate_entry_execution_velocity(
            _velocity_snapshot(times, volume=100), requested_quantity=20
        )
        assert not decision.allowed
        assert decision.reason == "entry_execution_velocity_too_slow"


def test_execution_velocity_rejects_stale_low_volume_and_route_conflict():
    stale = EntryExecutionVelocitySnapshot(
        True,
        "111770",
        "SOR",
        "111770_AL",
        print_count=10,
        recent_print_span_ms=10_000,
        latest_print_age_ms=5_001,
        recent_volume=1_000,
    )
    low_volume = EntryExecutionVelocitySnapshot(
        True,
        "111770",
        "SOR",
        "111770_AL",
        print_count=10,
        recent_print_span_ms=10_000,
        latest_print_age_ms=0,
        recent_volume=39,
    )
    wrong_route = parse_ka10003_entry_execution_velocity_snapshot(
        _velocity_ticks(["151232"] * 10, venue="KRX"),
        symbol="111770",
        route="NXT",
        observed_at=datetime(2026, 8, 28, 15, 12, 32, tzinfo=KST),
    )

    assert (
        evaluate_entry_execution_velocity(stale, requested_quantity=20).reason
        == "entry_execution_velocity_latest_print_stale"
    )
    assert (
        evaluate_entry_execution_velocity(low_volume, requested_quantity=20).reason
        == "entry_execution_velocity_volume_insufficient"
    )
    assert not wrong_route.source_ok
    assert wrong_route.error == "ka10003_nxt_route_conflict"
    assert ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT["decision_authority"] == (
        "block_new_widget_or_episode_buy_only"
    )
    assert "aggressor_side_or_direction_inference" in (
        ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT["forbidden_uses"]
    )


def test_execution_velocity_freshness_preserves_observation_milliseconds():
    payload = _velocity_ticks(["151227"] * 10)

    exact_boundary = parse_ka10003_entry_execution_velocity_snapshot(
        payload,
        symbol="111770",
        route="SOR",
        observed_at=datetime(2026, 8, 28, 15, 12, 32, tzinfo=KST),
    )
    just_stale = parse_ka10003_entry_execution_velocity_snapshot(
        payload,
        symbol="111770",
        route="SOR",
        observed_at=datetime(2026, 8, 28, 15, 12, 32, 1_000, tzinfo=KST),
    )

    assert exact_boundary.latest_print_age_ms == 5_000
    assert evaluate_entry_execution_velocity(
        exact_boundary, requested_quantity=20
    ).allowed
    assert just_stale.latest_print_age_ms == 5_001
    assert evaluate_entry_execution_velocity(
        just_stale, requested_quantity=20
    ).reason == "entry_execution_velocity_latest_print_stale"


def test_execution_velocity_rejects_duplicate_accumulated_volume_rows():
    payload = _velocity_ticks(["151232"] * 10)
    payload[1]["raw"]["acc_trde_qty"] = payload[0]["raw"]["acc_trde_qty"]

    snapshot = parse_ka10003_entry_execution_velocity_snapshot(
        payload,
        symbol="111770",
        route="SOR",
        observed_at=datetime(2026, 8, 28, 15, 12, 32, tzinfo=KST),
    )

    assert not snapshot.source_ok
    assert snapshot.error == "ka10003_accumulated_volume_not_latest_first"


@pytest.mark.parametrize(
    ("gateway", "invoke", "expected_request_code"),
    [
        (
            KiwoomLowPriceTwoLegGateway(
                symbol="111770", token_loader=lambda: "shared-token"
            ),
            lambda value: value.entry_execution_velocity_snapshot(route="SOR"),
            "111770_AL",
        ),
        (
            KiwoomSharedTokenOrderGateway(token_loader=lambda: "shared-token"),
            lambda value: value.entry_execution_velocity_snapshot(
                code="111770", route="KRX"
            ),
            "111770_AL",
        ),
        (
            KiwoomSharedTokenOrderGateway(token_loader=lambda: "shared-token"),
            lambda value: value.entry_execution_velocity_snapshot(
                code="111770", route="NXT"
            ),
            "111770_NX",
        ),
        (
            KiwoomOneShareGateway(token_loader=lambda: "shared-token"),
            lambda value: value.entry_execution_velocity_snapshot(route="SOR"),
            "005930_AL",
        ),
        (
            KiwoomMiddayOneShareGateway(token_loader=lambda: "shared-token"),
            lambda value: value.entry_execution_velocity_snapshot(route="SOR"),
            "005930_AL",
        ),
        (
            KiwoomAfternoonOneShareGateway(token_loader=lambda: "shared-token"),
            lambda value: value.entry_execution_velocity_snapshot(route="SOR"),
            "005930_AL",
        ),
    ],
)
def test_production_gateways_request_exact_route_and_latest_ten_prints(
    monkeypatch, gateway, invoke, expected_request_code
):
    calls = []

    def fake_tick_history(token, request_code, *, limit):
        calls.append((token, request_code, limit))
        now = datetime.now(tz=KST)
        venue = "NXT" if request_code.endswith("_NX") else "KRX"
        return _velocity_ticks(
            [
                (now - timedelta(seconds=index)).strftime("%H%M%S")
                for index in range(10)
            ],
            venue=venue,
        )

    monkeypatch.setattr(kiwoom_utils, "get_tick_history_ka10003", fake_tick_history)

    snapshot = invoke(gateway)

    assert snapshot.source_ok
    assert snapshot.request_code == expected_request_code
    assert calls == [("shared-token", expected_request_code, 10)]


def test_production_gateway_tick_history_failure_is_fail_closed(monkeypatch):
    def fail_tick_history(*args, **kwargs):
        raise RuntimeError("broker_read_failed")

    monkeypatch.setattr(kiwoom_utils, "get_tick_history_ka10003", fail_tick_history)
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="111770", token_loader=lambda: "shared-token"
    )

    snapshot = gateway.entry_execution_velocity_snapshot(route="SOR")

    assert not snapshot.source_ok
    assert snapshot.error == "RuntimeError"
