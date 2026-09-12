from __future__ import annotations

from datetime import date, datetime

import pytest

from src.trading.market import aftermarket_eligibility as contract


TRADE_DATE = date(2026, 9, 14)


def _snapshot(**updates):
    snapshot = {
        "trade_date": TRADE_DATE.isoformat(),
        "stock_code": "005930",
        "krx_regular_eligible": True,
        "nxtEnable": "Y",
        "krx_aftermarket_eligible": True,
        "auditInfo": "정상",
        "state": "정상",
        "orderWarning": 0,
        "marketCode": "0",
        "source_api_id": "ka10099",
        "source_revision": "69642586",
        "observed_at_kst": datetime(2026, 9, 14, 20, 5, tzinfo=contract.KST),
        "payload_sha256": "sha256-fixture",
        "quality_state": contract.QUALITY_VALID,
    }
    snapshot.update(updates)
    return snapshot


def test_resolve_aftermarket_eligibility_both_venues():
    result = contract.resolve_symbol_venue_eligibility(
        "005930", TRADE_DATE, _snapshot()
    )

    assert result.eligible_venues == (contract.VENUE_KRX, contract.VENUE_NXT)
    assert result.quality_state == contract.QUALITY_VALID
    assert result.blockers == tuple()
    assert result.audit_info == "정상"
    assert result.order_warning == "0"


@pytest.mark.parametrize(
    "krx_aftermarket,nxt,expected",
    [
        (True, False, (contract.VENUE_KRX,)),
        (False, True, (contract.VENUE_NXT,)),
    ],
)
def test_resolve_aftermarket_eligibility_only_one_venue(
    krx_aftermarket,
    nxt,
    expected,
):
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(
            krx_aftermarket_eligible=krx_aftermarket,
            nxt_eligible=nxt,
        ),
    )

    assert result.eligible_venues == expected
    assert result.quality_state == contract.QUALITY_VALID


def test_resolve_aftermarket_eligibility_neither_is_valid_empty():
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(krx_aftermarket_eligible=False, nxt_eligible=False),
    )

    assert result.eligible_venues == tuple()
    assert result.quality_state == contract.QUALITY_VALID


def test_resolve_aftermarket_eligibility_unknown_fails_closed():
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(krx_aftermarket_eligible=None, nxt_eligible=None),
    )

    assert result.eligible_venues == tuple()
    assert result.quality_state == contract.QUALITY_UNKNOWN
    assert contract.BLOCKER_ELIGIBILITY_UNKNOWN in result.blockers


def test_resolve_aftermarket_eligibility_conflict_fails_closed():
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(
            krx_aftermarket_eligible=False,
            nxt_eligible=True,
            eligible_venues_json=["KRX", "NXT"],
        ),
    )

    assert result.eligible_venues == tuple()
    assert result.quality_state == contract.QUALITY_CONFLICT
    assert contract.BLOCKER_SOURCE_CONFLICT in result.blockers


def test_resolve_aftermarket_eligibility_stale_source_fails_closed():
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(trade_date="2026-09-11"),
    )

    assert result.source_trade_date == date(2026, 9, 11)
    assert result.eligible_venues == tuple()
    assert result.quality_state == contract.QUALITY_UNKNOWN
    assert contract.BLOCKER_SOURCE_STALE in result.blockers


def test_incomplete_source_snapshot_fails_closed():
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(status="partial"),
    )

    assert result.eligible_venues == tuple()
    assert result.quality_state == contract.QUALITY_UNKNOWN
    assert contract.BLOCKER_SOURCE_INCOMPLETE in result.blockers


def test_unknown_krx_aftermarket_field_remains_nullable_without_reusing_nxt():
    result = contract.resolve_symbol_venue_eligibility(
        "005930",
        TRADE_DATE,
        _snapshot(krx_aftermarket_eligible=None, nxt_eligible=True),
    )

    assert result.krx_aftermarket_eligible is None
    assert result.nxt_eligible is True
    assert result.eligible_venues == (contract.VENUE_NXT,)
    assert result.quality_state == contract.QUALITY_PARTIAL
