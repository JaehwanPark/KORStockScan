from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway

from src.trading.order.entry_liquidity_guard import (
    ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT,
    ENTRY_LIQUIDITY_POLICY_CONTRACT,
    EXECUTABLE_MICRO_CONFIRMATION_MODE,
    EXECUTABLE_MICRO_CONFIRMATION_POLICY_CONTRACT,
    KST,
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
    entry_liquidity_request_code,
    evaluate_entry_execution_velocity,
    evaluate_executable_micro_confirmation,
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
        received_ts_ms=int(datetime.now().timestamp() * 1000) - 10,
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


def _executable_confirmation_policy() -> dict:
    return {
        "mode": EXECUTABLE_MICRO_CONFIRMATION_MODE,
        "supportive_confirmation_only": True,
        "require_bid_non_deterioration": True,
        "require_ask_non_deterioration": True,
        "require_positive_net_edge_after_costs": True,
        "broker_receipt_exact": False,
        "round_trip_cost_pct": 0.23,
        "cost_contract_sha256": "a" * 64,
    }


def test_selected_delay_requires_non_deteriorating_bbo_and_positive_net_edge():
    anchor = _snapshot(bid_qty=1_000, ask_qty=1_000)
    current = replace(anchor, best_bid=71_400, received_ts_ms=anchor.received_ts_ms + 1)
    passed = evaluate_executable_micro_confirmation(
        anchor_snapshot=anchor,
        current_snapshot=current,
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=72_000,
        policy=_executable_confirmation_policy(),
    )
    bid_deteriorated = evaluate_executable_micro_confirmation(
        anchor_snapshot=anchor,
        current_snapshot=replace(current, best_bid=71_200),
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=72_000,
        policy=_executable_confirmation_policy(),
    )
    negative_edge = evaluate_executable_micro_confirmation(
        anchor_snapshot=anchor,
        current_snapshot=current,
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=71_600,
        policy=_executable_confirmation_policy(),
    )

    assert passed.allowed
    assert passed.modeled_net_edge_pct is not None and passed.modeled_net_edge_pct > 0
    assert bid_deteriorated.reason == (
        "entry_executable_micro_confirmation_bid_deteriorated"
    )
    assert negative_edge.reason == (
        "entry_executable_micro_confirmation_nonpositive_net_edge"
    )
    assert EXECUTABLE_MICRO_CONFIRMATION_POLICY_CONTRACT["decision_authority"] == (
        "block_selected_widget_or_episode_new_buy_only"
    )


def test_executable_micro_confirmation_fails_closed_without_selected_policy():
    snapshot = _snapshot(bid_qty=1_000, ask_qty=1_000)
    decision = evaluate_executable_micro_confirmation(
        anchor_snapshot=snapshot,
        current_snapshot=snapshot,
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=72_000,
        policy=None,
    )

    assert not decision.allowed
    assert decision.reason == "entry_executable_micro_confirmation_policy_invalid"

    boolean_cost_policy = {**_executable_confirmation_policy()}
    boolean_cost_policy["round_trip_cost_pct"] = True
    decision = evaluate_executable_micro_confirmation(
        anchor_snapshot=snapshot,
        current_snapshot=snapshot,
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=72_000,
        policy=boolean_cost_policy,
    )
    assert not decision.allowed
    assert decision.reason == "entry_executable_micro_confirmation_policy_invalid"


def test_executable_micro_confirmation_blocks_invalid_typed_snapshot():
    anchor = replace(
        _snapshot(bid_qty=1_000, ask_qty=1_000),
        best_bid=0,
        best_ask=0,
    )
    current = _snapshot(bid_qty=1_000, ask_qty=1_000)

    decision = evaluate_executable_micro_confirmation(
        anchor_snapshot=anchor,
        current_snapshot=current,
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=72_000,
        policy=_executable_confirmation_policy(),
    )

    assert not decision.allowed
    assert decision.reason == (
        "entry_executable_micro_confirmation_anchor_contract_invalid"
    )

    malformed = replace(anchor, best_bid="not-a-price")
    malformed_decision = evaluate_executable_micro_confirmation(
        anchor_snapshot=malformed,
        current_snapshot=current,
        requested_quantity=20,
        reference_price=71_500,
        maximum_entry_price=71_500,
        target_price=72_000,
        policy=_executable_confirmation_policy(),
    )
    assert not malformed_decision.allowed
    assert malformed_decision.reason == (
        "entry_executable_micro_confirmation_anchor_missing"
    )


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
        "rest_received_ts_ms": int(datetime.now().timestamp() * 1000),
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
    assert (
        evaluate_entry_execution_velocity(just_stale, requested_quantity=20).reason
        == "entry_execution_velocity_latest_print_stale"
    )


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

    def fake_tick_history(token, request_code, *, limit, request_owner, request_class):
        calls.append((token, request_code, limit))
        assert request_owner.endswith("_entry_velocity")
        assert request_class == "execution_critical"
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


def _rest_book(**overrides):
    return {
        "source": "ka10004_rest_orderbook",
        "stock_code": "005930",
        "request_code": "005930_AL",
        "rest_freshness_basis": "response_received_epoch_ms",
        "best_bid": 71300,
        "best_ask": 71500,
        "best_bid_qty": 1000,
        "best_ask_qty": 1000,
        "rest_age_ms": 0,
        "rest_received_ts_ms": 100000,
        **overrides,
    }


def test_rest_health_is_recomputed_at_parser_and_final_liquidity_decision():
    payload = _rest_book(market_data_health={"rest_quote": {"quote_state": "fresh"}})
    snapshot = parse_ka10004_entry_liquidity_snapshot(
        payload, symbol="005930", route="SOR", now_ts=100.5
    )
    assert snapshot.age_ms == 500
    assert (
        snapshot.market_data_health["rest_quote"]["trade_activity_state"]
        == "OBSERVATION_UNPROVEN"
    )
    assert evaluate_entry_liquidity(snapshot, requested_quantity=20, now_ts=102).allowed
    stale = evaluate_entry_liquidity(snapshot, requested_quantity=20, now_ts=102.001)
    assert not stale.allowed
    assert stale.reason == "entry_liquidity_snapshot_stale"
    assert stale.snapshot.age_ms == 2001
    assert (
        stale.event_fields()["entry_liquidity_snapshot"]["market_data_health"][
            "rest_quote"
        ]["quote_state"]
        == "stale"
    )
    assert payload["rest_age_ms"] == 0 and snapshot.age_ms == 500


@pytest.mark.parametrize("stamp", [100001, True, None, float("inf")])
def test_rest_clock_invalid_or_future_is_never_fresh(stamp):
    snapshot = parse_ka10004_entry_liquidity_snapshot(
        _rest_book(rest_received_ts_ms=stamp), symbol="005930", route="SOR", now_ts=100
    )
    assert not snapshot.source_ok
    assert not evaluate_entry_liquidity(
        snapshot, requested_quantity=20, now_ts=100
    ).allowed


def test_delayed_micro_reages_current_book_but_does_not_expire_signal_anchor():
    anchor = parse_ka10004_entry_liquidity_snapshot(
        _rest_book(), symbol="005930", route="SOR", now_ts=100
    )
    current = parse_ka10004_entry_liquidity_snapshot(
        _rest_book(rest_received_ts_ms=105000), symbol="005930", route="SOR", now_ts=105
    )
    arguments = dict(
        anchor_snapshot=anchor,
        current_snapshot=current,
        requested_quantity=20,
        reference_price=71500,
        maximum_entry_price=71500,
        target_price=72000,
        policy=_executable_confirmation_policy(),
    )
    assert evaluate_executable_micro_confirmation(**arguments, now_ts=105).allowed
    stale = evaluate_executable_micro_confirmation(**arguments, now_ts=107.001)
    assert not stale.allowed
    assert stale.reason == "entry_executable_micro_confirmation_current_stale"
    assert stale.current_snapshot.age_ms == 2001


def test_invalid_injected_scope_fails_closed_without_raising():
    snapshot = replace(
        _snapshot(bid_qty=1000, ask_qty=1000), symbol="bad", route="UNKNOWN"
    )
    assert not evaluate_entry_liquidity(snapshot, requested_quantity=20).allowed


@pytest.mark.parametrize("quantity", [True, float("nan"), -1, "1000"])
def test_invalid_injected_depth_cannot_bypass_liquidity_guard(quantity):
    snapshot = replace(_snapshot(bid_qty=1000, ask_qty=1000), best_ask_qty=quantity)
    assert not evaluate_entry_liquidity(snapshot, requested_quantity=20).allowed


@pytest.mark.parametrize("age", [True, "0", -1, float("nan")])
def test_invalid_injected_age_fails_closed_without_raising(age):
    snapshot = replace(_snapshot(bid_qty=1000, ask_qty=1000), age_ms=age)
    assert not evaluate_entry_liquidity(snapshot, requested_quantity=20).allowed


@pytest.mark.parametrize(
    "gateway_class,kwargs,invoke",
    [
        (
            KiwoomSharedTokenOrderGateway,
            {},
            lambda g: g.entry_liquidity_snapshot(code="005930", route="KRX"),
        ),
        (KiwoomOneShareGateway, {}, lambda g: g.entry_liquidity_snapshot()),
        (KiwoomMiddayOneShareGateway, {}, lambda g: g.entry_liquidity_snapshot()),
        (KiwoomAfternoonOneShareGateway, {}, lambda g: g.entry_liquidity_snapshot()),
        (
            KiwoomLowPriceTwoLegGateway,
            {"symbol": "111770"},
            lambda g: g.entry_liquidity_snapshot(route="SOR"),
        ),
    ],
)
def test_all_five_gateways_preserve_common_rest_quote_health(
    monkeypatch, gateway_class, kwargs, invoke
):
    monkeypatch.setattr(
        kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code, **k: _rest_book(stock_code=code[:6], request_code=code),
    )
    import src.trading.order.entry_liquidity_guard as guard

    monkeypatch.setattr(guard.time, "time", lambda: 100.5)
    snapshot = invoke(gateway_class(token_loader=lambda: "shared-token", **kwargs))
    assert snapshot.source_ok
    rest = snapshot.market_data_health["rest_quote"]
    assert snapshot.age_ms == rest["quote_receive_age_ms"] == 500
    assert rest["market_data_scope"] == "KRX_NXT_INTEGRATED"
    assert rest["effective_venue"] == "UNKNOWN"
    assert rest["underlying_event_venue_proven"] is False
    assert rest["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    assert rest["quiet_episode_count"] is None


def _velocity_receipted_rows(observed):
    times = ['151232', '151231', '151230', '151229', '151228', '151227', '151226', '151225', '151224', '151223']
    rows = _velocity_ticks(times, volume=100)
    for row in rows:
        row['_kiwoom_source_meta'] = {'api_id': 'ka10003', 'request_code': '111770_AL',
            'rest_received_ts_ms': int(observed.timestamp() * 1000),
            'request_owner': 'entry_velocity', 'request_class': 'execution_critical'}
        row['market_data_health'] = {'rest_input': {'response_receive_age_ms': 0}}
    return rows


def test_velocity_retains_original_receipt_and_revalidates_without_tr():
    observed = datetime(2026, 9, 17, 15, 12, 32, tzinfo=KST)
    snapshot = parse_ka10003_entry_execution_velocity_snapshot(
        _velocity_receipted_rows(observed), symbol='111770', route='SOR', observed_at=observed)
    assert snapshot.source_ok
    assert snapshot.market_data_health['rest_input']['trade_activity_state'] == 'OBSERVATION_UNPROVEN'
    assert snapshot.market_data_health['rest_input']['quiet_episode_count'] is None
    fresh = evaluate_entry_execution_velocity(snapshot, requested_quantity=20, now_ts=observed.timestamp())
    assert fresh.allowed
    snapshot.market_data_health['rest_input']['response_receive_age_ms'] = 0
    expired = evaluate_entry_execution_velocity(snapshot, requested_quantity=20, now_ts=observed.timestamp() + 5.001)
    assert not expired.allowed
    assert expired.snapshot.latest_print_age_ms >= 5001
    assert expired.snapshot.source_meta == snapshot.source_meta
    assert expired.snapshot.market_data_health['rest_input']['response_receive_age_ms'] > 5000


@pytest.mark.parametrize('change', ['future_clock', 'wrong_item', 'wrong_api', 'mixed_packet', 'missing_receipt'])
def test_velocity_rejects_receipt_clock_scope_or_packet_conflict(change):
    observed = datetime(2026, 9, 17, 15, 12, 32, tzinfo=KST)
    rows = _velocity_receipted_rows(observed)
    if change == 'future_clock':rows[0]['_kiwoom_source_meta']['rest_received_ts_ms'] += 1
    elif change == 'wrong_item':rows[0]['response_item_raw'] = '005930_NX'
    elif change == 'wrong_api':rows[0]['_kiwoom_source_meta']['api_id'] = 'ka10004'
    elif change == 'mixed_packet':rows[0]['_kiwoom_source_meta']['rest_received_ts_ms'] -= 1
    elif change == 'missing_receipt':del rows[0]['_kiwoom_source_meta']
    snapshot = parse_ka10003_entry_execution_velocity_snapshot(rows, symbol='111770', route='SOR', observed_at=observed)
    assert not snapshot.source_ok
    assert not evaluate_entry_execution_velocity(snapshot, requested_quantity=20, now_ts=observed.timestamp()).allowed


def test_velocity_future_print_age_is_signed_and_never_normalized_to_zero():
    observed = datetime(2026, 9, 17, 15, 12, 31, tzinfo=KST)
    rows = _velocity_receipted_rows(observed)
    snapshot = parse_ka10003_entry_execution_velocity_snapshot(rows, symbol='111770', route='SOR', observed_at=observed)
    assert snapshot.latest_print_age_ms == -1000
    decision = evaluate_entry_execution_velocity(snapshot, requested_quantity=20, now_ts=observed.timestamp())
    assert not decision.allowed
    assert decision.reason == 'ka10003_latest_trade_time_in_future'


def test_velocity_future_packet_does_not_recover_by_wait_or_cached_reparse():
    observed = datetime(2026, 9, 17, 15, 12, 31, tzinfo=KST)
    rows = _velocity_receipted_rows(observed)
    snapshot = parse_ka10003_entry_execution_velocity_snapshot(rows, symbol='111770', route='SOR', observed_at=observed)
    assert not snapshot.source_ok
    waited = evaluate_entry_execution_velocity(snapshot, requested_quantity=20, now_ts=observed.timestamp() + 1)
    assert not waited.allowed
    reparsed = parse_ka10003_entry_execution_velocity_snapshot(rows, symbol='111770', route='SOR', observed_at=observed + timedelta(seconds=1))
    assert not reparsed.source_ok
    assert reparsed.error == 'ka10003_latest_trade_time_in_future'


@pytest.fixture
def entry_ws_source(tmp_path, monkeypatch):
    import json
    from src.trading.market import entry_ws_snapshot as ws
    from src.tests.test_entry_adverse_flow import snapshot
    now = datetime(2026, 9, 21, 10, 0, 20, tzinfo=KST).timestamp()
    data = snapshot(datetime.fromtimestamp(now, KST))
    data['generated_at_epoch'] = now
    data['shared_transport_producer'] = dict(
        schema='shared_ws_transport_producer_v1', process=ws.process_generation(__import__('os').getpid()),
        source_commit='a'*40, transport_epoch=1, connection_available=True, registered_items=['005930_AL'])
    stock = data['stocks']['005930'];stock['market_data_transport_epoch']=1
    route = stock['machine_confirmation_routes']['SOR']
    for kind,row in route['realtime_types'].items():
        row.update(realtime_type=kind, market_route='krx_nxt_integrated', market_suffix='_AL',
                   effective_venue='', observed_epoch=now-.1, route_sequence=20)
    route['realtime_types']['0D']['orderbook'] = {'bids':[{'price':10100,'volume':1000}], 'asks':[{'price':10110,'volume':1000}]}
    route['recent_trades'] = [dict(item='005930_AL', transport_epoch=1, route_sequence=20-i,
        received_at_ms=round((now-.1-i)*1000),provider_trade_epoch=now-1-i,
        provider_trade_time_precision_ms=1000,provider_trade_date_basis='local_receive_calendar_date_not_provider_date',
        volume=100,price=10110,cum_volume=10000-i*100) for i in range(10)]
    path = tmp_path/'source.json'
    def write():
        # Atomic replacement tests cache generation invalidation too.
        new=tmp_path/'next.json';new.write_text(json.dumps(data));new.replace(path)
    write()
    monkeypatch.setattr(ws, '_live_snapshot_path', lambda: path)
    monkeypatch.setattr(ws.time, 'time', lambda: now)
    monkeypatch.setenv(ws.SOURCE_ENV, 'ws')
    return ws, data, route, path, now, write


def test_ws_entry_inputs_preserve_existing_guard_decisions(entry_ws_source):
    ws,data,route,path,now,write=entry_ws_source
    book=ws.read_entry_snapshot(symbol='005930',route='SOR',kind='0D')
    ticks=ws.read_entry_snapshot(symbol='005930',route='SOR',kind='0B')
    assert book.source_ok and ticks.source_ok
    assert evaluate_entry_liquidity(book,requested_quantity=20,now_ts=now).allowed
    assert evaluate_entry_execution_velocity(ticks,requested_quantity=20,now_ts=now).allowed
    assert not evaluate_entry_liquidity(book,requested_quantity=20,now_ts=now+2).allowed
    assert not evaluate_entry_execution_velocity(ticks,requested_quantity=20,now_ts=now+5).allowed
    assert ticks.recent_volume==1000 and ticks.recent_print_span_ms==9000
    assert ticks.source_meta['exchange_completeness_proven'] is False
    route['realtime_types']['0D']['orderbook']['asks'][0]['volume']=1;write()
    weak=ws.read_entry_snapshot(symbol='005930',route='SOR',kind='0D')
    assert weak.source_ok
    assert not evaluate_entry_liquidity(weak,requested_quantity=20,now_ts=now).allowed


@pytest.mark.parametrize('fault', ['missing','duplicate','gap','epoch','future','reversed','producer_dead','wrong_route','partial','stale','bad_authority','cumulative_duplicate','cumulative_missing'])
def test_ws_entry_source_contract_failures(entry_ws_source,fault):
    ws,data,route,path,now,write=entry_ws_source
    kind='0B'
    if fault=='missing':route['recent_trades'].pop()
    elif fault=='duplicate':route['recent_trades'][-1]=dict(route['recent_trades'][-2])
    elif fault=='gap':route['recent_trades'][-1]['route_sequence']-=1
    elif fault=='epoch':route['recent_trades'][-1]['transport_epoch']=2
    elif fault=='future':route['recent_trades'][0]['provider_trade_epoch']=now+1
    elif fault=='reversed':route['recent_trades'][2]['provider_trade_epoch']=now
    elif fault=='producer_dead':data['shared_transport_producer']['process']['pid']=99999999
    elif fault=='wrong_route':route['realtime_types']['0B']['market_suffix']='_NX'
    elif fault=='partial':kind='0D';route['realtime_types']['0D']['orderbook']['asks']=[]
    elif fault=='stale':kind='0D';route['realtime_types']['0D']['observed_epoch']=now-3
    elif fault=='bad_authority':data['runtime_effect']=True
    elif fault=='cumulative_duplicate':route['recent_trades'][1]['cum_volume']=route['recent_trades'][0]['cum_volume']
    elif fault=='cumulative_missing':route['recent_trades'][0].pop('cum_volume')
    write()
    result=ws.read_entry_snapshot(symbol='005930',route='SOR',kind=kind)
    assert not result.source_ok and result.error.startswith('entry_ws_source_unavailable:')


def test_ws_preserves_existing_krx_sor_alias_and_nxt_separation(entry_ws_source):
    ws,*_=entry_ws_source
    assert ws.read_entry_snapshot(symbol='005930',route='KRX',kind='0D').source_ok
    assert not ws.read_entry_snapshot(symbol='005930',route='NXT',kind='0D').source_ok


@pytest.mark.parametrize('gateway_class',[KiwoomLowPriceTwoLegGateway,KiwoomOneShareGateway,KiwoomMiddayOneShareGateway,KiwoomAfternoonOneShareGateway,KiwoomSharedTokenOrderGateway])
def test_ws_gateway_no_rest_even_for_source_gap(entry_ws_source,monkeypatch,gateway_class):
    ws,data,route,path,now,write=entry_ws_source
    def forbidden(*a,**kw):raise AssertionError('REST must not be called')
    monkeypatch.setattr(kiwoom_utils,'get_stock_orderbook_ka10004',forbidden)
    monkeypatch.setattr(kiwoom_utils,'get_tick_history_ka10003',forbidden)
    g=object.__new__(gateway_class);g.symbol='005930'
    kwargs={'code':'005930','route':'SOR'} if gateway_class is KiwoomSharedTokenOrderGateway else {'route':'SOR'}
    assert g.entry_liquidity_snapshot(**kwargs).source_ok
    assert g.entry_execution_velocity_snapshot(**kwargs).source_ok
    route['recent_trades']=[];write()
    assert not g.entry_execution_velocity_snapshot(**kwargs).source_ok
    path.unlink()
    assert not g.entry_liquidity_snapshot(**kwargs).source_ok


def test_ws_source_receipt_survives_delayed_anchor_roundtrip(entry_ws_source):
    from dataclasses import asdict
    from src.trading.order.entry_liquidity_guard import _coerce_liquidity_snapshot
    ws,data,route,path,now,write=entry_ws_source
    book=ws.read_entry_snapshot(symbol="005930",route="SOR",kind="0D")
    restored=_coerce_liquidity_snapshot(asdict(book))
    assert restored == book
    assert evaluate_entry_liquidity(restored,requested_quantity=20,now_ts=now).allowed
    assert "0D" in evaluate_entry_liquidity(restored,requested_quantity=20,now_ts=now).event_fields()["entry_liquidity_policy_contract"]["sample_floor"]


@pytest.mark.parametrize("quantity", [True, float("nan"), -1, "1000"])
def test_ws_injected_malformed_quantity_is_not_accepted(entry_ws_source,quantity):
    ws,data,route,path,now,write=entry_ws_source
    book=ws.read_entry_snapshot(symbol="005930",route="SOR",kind="0D")
    assert not evaluate_entry_liquidity(replace(book,best_ask_qty=quantity),requested_quantity=20,now_ts=now).allowed
    assert not evaluate_entry_liquidity(replace(book,source_meta=None),requested_quantity=20,now_ts=now).allowed


def test_ws_rollout_preserves_unselected_exact_route(entry_ws_source,monkeypatch):
    ws,*_=entry_ws_source
    monkeypatch.setenv(ws.ITEMS_ENV,"005930_AL")
    assert ws.selected_entry_snapshot(symbol="005930",route="SOR",kind="0D").source_ok
    assert ws.selected_entry_snapshot(symbol="005930",route="NXT",kind="0D") is None
    monkeypatch.setenv(ws.ITEMS_ENV,"005930_AL,invalid")
    assert not ws.selected_entry_snapshot(symbol="005930",route="SOR",kind="0D").source_ok
