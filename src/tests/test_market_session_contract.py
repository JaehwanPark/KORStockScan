from __future__ import annotations

from datetime import date, datetime

import pytest

from src.trading.market import session_contract as contract


def _kst_datetime(y: int, m: int, d: int, h: int, minute: int = 0, sec: int = 0):
    return datetime(y, m, d, h, minute, sec, tzinfo=contract.KST)


def test_resolve_market_session_before_effective_date_preserves_legacy_contract():
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 13, 9, 15))
    assert context.contract_version == contract.MARKET_SESSION_CONTRACT_VERSION_V1
    assert context.blocker is None
    assert context.session_regime == contract.MARKET_SESSION_REGIME_LEGACY_KRX_ONLY
    assert context.preferred_market_data_route == contract.MARKET_DATA_ROUTE_KRX_ONLY
    assert context.entry_allowed_by_clock is True


def test_resolve_market_session_before_effective_date_before_20_00_preserves_new_style_for_nxt():
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 13, 19, 45))
    assert context.contract_version == contract.MARKET_SESSION_CONTRACT_VERSION_V1
    assert context.session_regime == contract.MARKET_SESSION_REGIME_LEGACY_NXT_ONLY
    assert context.preferred_market_data_route == contract.MARKET_DATA_ROUTE_NXT_ONLY


def test_resolve_market_session_after_effective_date_krx_regular():
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 9, 15))
    assert context.contract_version == contract.MARKET_SESSION_CONTRACT_VERSION_V2
    assert context.session_regime == contract.MARKET_SESSION_REGIME_KRX_REGULAR
    assert context.open_venues == (contract.ACTUAL_EXECUTION_VENUE_KRX,)
    assert context.entry_allowed_by_clock is True
    assert context.exit_allowed_by_clock is True
    assert context.blocker is None


def test_resolve_market_session_after_effective_date_preserves_premarket():
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 8, 30))

    assert context.contract_version == contract.MARKET_SESSION_CONTRACT_VERSION_V2
    assert context.session_regime == contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET
    assert context.open_venues == (contract.ACTUAL_EXECUTION_VENUE_KRX,)
    assert context.entry_allowed_by_clock is False
    assert context.exit_allowed_by_clock is False


@pytest.mark.parametrize(
    ("clock_time", "expected"),
    [
        (("15:30", "00"), contract.MARKET_SESSION_REGIME_SESSION_TRANSITION),
        (("15:40", "00"), contract.MARKET_SESSION_REGIME_SESSION_TRANSITION),
        (("16:00", "00"), contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET),
        (("19:40", "00"), contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY),
        (("19:45", "00"), contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_TERMINAL_EXIT),
        (("20:00", "00"), contract.MARKET_SESSION_REGIME_CLOSED),
    ],
)
def test_resolve_market_session_after_effective_date_boundary_windows(clock_time, expected):
    clock_raw, second_raw = clock_time
    hour, minute = map(int, clock_raw.split(":"))
    second = int(second_raw)
    context = contract.resolve_market_session(
        datetime(2026, 9, 14, hour, minute, second, tzinfo=contract.KST)
    )
    assert context.session_regime == expected


def test_resolve_market_session_rejects_naive_datetime():
    context = contract.resolve_market_session(datetime(2026, 9, 14, 10, 0))
    assert context.blocker == contract.VENDOR_BLOCKER
    assert context.contract_version == contract.MARKET_SESSION_CONTRACT_VERSION_V1
    assert context.session_regime == contract.MARKET_SESSION_REGIME_LEGACY_TRANSITION


def test_resolve_symbol_venue_eligibility_projects_known_fields():
    context = contract.resolve_symbol_venue_eligibility(
        stock_code="005930",
        trade_date=date(2026, 9, 14),
        source_snapshot={
            "source_id": "ka10099",
            "krx_regular_eligible": True,
            "nxt_eligible": False,
            "krx_aftermarket_eligible": None,
            "quality_state": contract.SOURCE_QUALITY_VALID,
            "observed_at_kst": datetime(2026, 9, 14, 9, 0, tzinfo=contract.KST).isoformat(),
            "payload_sha256": "abc",
            "blocked_reasons_json": ["known_ok"],
        },
    )
    assert context.stock_code == "005930"
    assert context.krx_regular_eligible is True
    assert context.nxt_eligible is False
    assert context.eligible_venues == (contract.ACTUAL_EXECUTION_VENUE_KRX,)
    assert context.source_id == "ka10099"
    assert context.source_sha256 == "abc"
    assert context.quality_state == contract.SOURCE_QUALITY_VALID
    assert context.blockers == ("known_ok",)


def test_resolve_symbol_venue_eligibility_reports_blockers_for_missing_snapshot():
    context = contract.resolve_symbol_venue_eligibility(
        stock_code="005930",
        trade_date=date(2026, 9, 14),
        source_snapshot=None,
    )
    assert context.source_id == "005930"
    assert context.blockers == (contract.VENDOR_SOURCE_MISSING,)
    assert context.eligible_venues == tuple()


def _eligibility(*, krx: bool | None = True, nxt: bool | None = True):
    return contract.resolve_symbol_venue_eligibility(
        stock_code="005930",
        trade_date=date(2026, 9, 14),
        source_snapshot={
            "source_id": "test-policy",
            "krx_regular_eligible": True,
            "krx_aftermarket_eligible": krx,
            "nxt_eligible": nxt,
            "quality_state": contract.SOURCE_QUALITY_VALID,
            "observed_at_kst": _kst_datetime(2026, 9, 14, 15, 55).isoformat(),
            "payload_sha256": "fixture-sha",
        },
    )


@pytest.mark.parametrize("route", ["KRX", "NXT", "SOR"])
@pytest.mark.parametrize("side", ["buy", "sell"])
@pytest.mark.parametrize(
    ("order_type", "allowed", "effective_type", "reason"),
    [
        ("0", True, "0", contract.ORDER_TYPE_PREFLIGHT_ALLOWED),
        ("00", True, "00", contract.ORDER_TYPE_PREFLIGHT_ALLOWED),
        ("6", True, "6", contract.ORDER_TYPE_PREFLIGHT_ALLOWED),
        ("3", True, "6", contract.ORDER_TYPE_PREFLIGHT_REMAP_MARKET_TO_BEST),
        ("5", False, None, contract.ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED),
        ("16", False, None, contract.ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED),
        ("29", False, None, contract.ORDER_TYPE_PREFLIGHT_TYPE_UNSUPPORTED),
    ],
)
def test_aftermarket_order_type_matrix(
    route, side, order_type, allowed, effective_type, reason
):
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 16, 0))
    result = contract.resolve_order_type_preflight(
        context,
        route,
        side,
        order_type,
        eligibility=_eligibility(),
    )

    assert result.allowed is allowed
    assert result.effective_order_type == effective_type
    assert result.reason == reason
    assert result.remapped is (order_type == "3")


@pytest.mark.parametrize("minute", [30, 40, 59])
def test_nxt_solo_window_is_removed_and_orders_are_blocked(minute):
    hour = 15 if minute < 60 else 16
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, hour, minute))
    result = contract.resolve_order_type_preflight(context, "NXT", "buy", "6")

    assert context.session_regime == contract.MARKET_SESSION_REGIME_SESSION_TRANSITION
    assert result.allowed is False
    assert result.reason == contract.ORDER_TYPE_PREFLIGHT_SESSION_BLOCKED


@pytest.mark.parametrize("route", ["KRX", "NXT", "SOR"])
def test_aftermarket_buy_fails_closed_when_eligibility_is_unknown(route):
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 16, 0))

    result = contract.resolve_order_type_preflight(context, route, "buy", "6")

    assert result.allowed is False
    assert result.reason == contract.ORDER_TYPE_PREFLIGHT_ELIGIBILITY_UNKNOWN


@pytest.mark.parametrize(
    ("route", "eligibility"),
    [
        ("KRX", _eligibility(krx=None, nxt=True)),
        ("NXT", _eligibility(krx=True, nxt=None)),
        ("SOR", _eligibility(krx=None, nxt=True)),
        ("SOR", _eligibility(krx=True, nxt=None)),
    ],
)
def test_aftermarket_buy_preserves_nullable_eligibility_as_unknown(route, eligibility):
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 16, 0))

    result = contract.resolve_order_type_preflight(
        context,
        route,
        "buy",
        "6",
        eligibility=eligibility,
    )

    assert result.allowed is False
    assert result.reason == contract.ORDER_TYPE_PREFLIGHT_ELIGIBILITY_UNKNOWN


@pytest.mark.parametrize(
    ("route", "eligibility"),
    [
        ("KRX", _eligibility(krx=False, nxt=True)),
        ("NXT", _eligibility(krx=True, nxt=False)),
        ("SOR", _eligibility(krx=True, nxt=False)),
    ],
)
def test_aftermarket_buy_blocks_route_ineligible_symbol(route, eligibility):
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 16, 0))

    result = contract.resolve_order_type_preflight(
        context,
        route,
        "buy",
        "0",
        eligibility=eligibility,
    )

    assert result.allowed is False
    assert result.reason == contract.ORDER_TYPE_PREFLIGHT_ROUTE_INELIGIBLE


@pytest.mark.parametrize("hour,minute", [(19, 40), (19, 45), (19, 59)])
def test_aftermarket_after_1940_blocks_buy_and_requires_existing_holding_for_sell(
    hour, minute
):
    context = contract.resolve_market_session(
        _kst_datetime(2026, 9, 14, hour, minute)
    )

    buy = contract.resolve_order_type_preflight(
        context,
        "SOR",
        "buy",
        "0",
        eligibility=_eligibility(),
    )
    new_sell = contract.resolve_order_type_preflight(context, "SOR", "sell", "0")
    holding_sell = contract.resolve_order_type_preflight(
        context,
        "SOR",
        "sell",
        "3",
        existing_holding=True,
    )

    assert buy.allowed is False
    assert buy.reason == contract.ORDER_TYPE_PREFLIGHT_BUY_WINDOW_CLOSED
    assert new_sell.allowed is False
    assert new_sell.reason == contract.ORDER_TYPE_PREFLIGHT_EXISTING_HOLDING_REQUIRED
    assert holding_sell.allowed is True
    assert holding_sell.effective_order_type == "6"


def test_regular_session_preserves_existing_order_type_behavior():
    context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 9, 15))

    result = contract.resolve_order_type_preflight(context, "KRX", "buy", "29")

    assert result.allowed is True
    assert result.effective_order_type == "29"
    assert result.remapped is False


def test_order_type_preflight_rejects_unknown_route_and_closed_session():
    open_context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 16, 0))
    closed_context = contract.resolve_market_session(_kst_datetime(2026, 9, 14, 20, 0))

    unknown_route = contract.resolve_order_type_preflight(
        open_context,
        "UNKNOWN",
        "sell",
        "6",
    )
    closed = contract.resolve_order_type_preflight(
        closed_context,
        "KRX",
        "sell",
        "6",
        existing_holding=True,
    )

    assert unknown_route.allowed is False
    assert unknown_route.reason == contract.ORDER_TYPE_PREFLIGHT_ROUTE_UNSUPPORTED
    assert closed.allowed is False
    assert closed.reason == contract.ORDER_TYPE_PREFLIGHT_SESSION_BLOCKED
