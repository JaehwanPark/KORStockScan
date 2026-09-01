from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway
from src.trading.order.kiwoom_episode_read_control import (
    KiwoomEpisodeReadPacer,
    ShortTtlSnapshotCache,
    post_kiwoom_episode_read,
)
from src.trading.samsung_afternoon_one_share.gateway import (
    KiwoomAfternoonOneShareGateway,
)
from src.trading.samsung_midday_one_share.gateway import KiwoomMiddayOneShareGateway
from src.trading.samsung_morning_one_share.gateway import KiwoomOneShareGateway

KST = ZoneInfo("Asia/Seoul")


class FakeResponse:
    def __init__(self, body: object, *, status_code: int = 200) -> None:
        self._body = body
        self.status_code = status_code
        self.headers: dict[str, str] = {}

    def json(self) -> object:
        return self._body


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class MutableClock:
    def __init__(self, value: float) -> None:
        self.value = value
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.value

    def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.value += delay


def _minute_response(timestamp: str) -> FakeResponse:
    return FakeResponse(
        {
            "return_code": 0,
            "stk_min_pole_chart_qry": [
                {
                    "cntr_tm": timestamp,
                    "open_pric": "100000",
                    "high_pric": "100100",
                    "low_pric": "99900",
                    "cur_prc": "100000",
                }
            ],
        }
    )


def test_cross_process_pacer_reserves_minimum_interval(tmp_path: Path) -> None:
    clock = MutableClock(100.0)
    pacer = KiwoomEpisodeReadPacer(
        state_path=tmp_path / "ka10080.pacer",
        min_interval_sec=0.4,
        clock=clock,
        sleep=clock.sleep,
    )

    pacer.wait("ka10080")
    clock.value += 0.1
    pacer.wait("ka10075")
    clock.value += 0.1
    pacer.wait("kt00007")

    assert clock.sleeps == pytest.approx([0.3, 0.3])
    assert float((tmp_path / "ka10080.pacer").read_text()) == pytest.approx(100.8)


def test_ka10080_retries_only_explicit_1700_with_bounded_backoff() -> None:
    responses = iter(
        [
            (FakeResponse({"return_code": 1700}), {"return_code": 1700}),
            (FakeResponse({"return_code": 0}), {"return_code": 0}),
        ]
    )
    sleeps: list[float] = []

    response, body = post_kiwoom_episode_read(
        api_id="ka10080",
        post_once=lambda: next(responses),
        pacing_enabled=False,
        sleep=sleeps.append,
    )

    assert response.status_code == 200
    assert body == {"return_code": 0}
    assert sleeps == [0.8]


def test_ka10080_rate_limit_retry_is_capped_at_two() -> None:
    responses = iter(
        [
            (FakeResponse({"return_code": 1700}), {"return_code": 1700}),
            (FakeResponse({"return_code": 1700}), {"return_code": 1700}),
            (FakeResponse({"return_code": 1700}), {"return_code": 1700}),
            (FakeResponse({"return_code": 0}), {"return_code": 0}),
        ]
    )
    sleeps: list[float] = []

    _, body = post_kiwoom_episode_read(
        api_id="ka10080",
        post_once=lambda: next(responses),
        pacing_enabled=False,
        sleep=sleeps.append,
    )

    assert body == {"return_code": 1700}
    assert sleeps == [0.8, 1.6]


def test_episode_read_retry_rejects_order_api() -> None:
    called = False

    def post_once():
        nonlocal called
        called = True
        return FakeResponse({"return_code": 1700}), {"return_code": 1700}

    with pytest.raises(ValueError, match="requires_supported_read_api"):
        post_kiwoom_episode_read(
            api_id="kt10000", post_once=post_once, pacing_enabled=False
        )
    assert called is False


def test_short_ttl_cache_reuses_only_fresh_success() -> None:
    clock = MutableClock(10.0)
    cache = ShortTtlSnapshotCache(ttl_sec=1.0, clock=clock)
    first = object()
    cache.put(("kt00007", "20260820"), first)

    assert cache.get(("kt00007", "20260820")) is first
    clock.value += 1.1
    assert cache.get(("kt00007", "20260820")) is None


@pytest.mark.parametrize(
    ("gateway_factory", "symbol"),
    [
        (
            lambda session, sleeps: KiwoomLowPriceTwoLegGateway(
                symbol="475150",
                request_session=session,
                token_loader=lambda: "TOKEN",
                read_retry_sleep=sleeps.append,
            ),
            "475150",
        ),
        (
            lambda session, sleeps: KiwoomOneShareGateway(
                request_session=session,
                token_loader=lambda: "TOKEN",
                read_retry_sleep=sleeps.append,
            ),
            "005930",
        ),
        (
            lambda session, sleeps: KiwoomMiddayOneShareGateway(
                request_session=session,
                token_loader=lambda: "TOKEN",
                read_retry_sleep=sleeps.append,
            ),
            "005930",
        ),
        (
            lambda session, sleeps: KiwoomAfternoonOneShareGateway(
                request_session=session,
                token_loader=lambda: "TOKEN",
                read_retry_sleep=sleeps.append,
            ),
            "005930",
        ),
    ],
)
def test_kt00007_retries_1700_and_collapses_two_leg_same_query(
    gateway_factory, symbol: str
) -> None:
    body = {
        "return_code": 0,
        "acnt_ord_cntr_prps_dtl": [
            {
                "stk_cd": symbol,
                "ord_no": "0001",
                "ord_qty": "10",
                "cntr_qty": "10",
                "ord_remnq": "0",
                "cntr_uv": "50000",
            },
            {
                "stk_cd": symbol,
                "ord_no": "0002",
                "ord_qty": "10",
                "cntr_qty": "10",
                "ord_remnq": "0",
                "cntr_uv": "50100",
            },
        ],
    }
    session = FakeSession(
        [
            FakeResponse({"return_code": 1700, "return_msg": "[1700] request limit"}),
            FakeResponse(body),
        ]
    )
    sleeps: list[float] = []
    gateway = gateway_factory(session, sleeps)

    first = gateway.execution_snapshot(
        order_no="0001", order_date="2026-08-20", expected_order_qty=10
    )
    second = gateway.execution_snapshot(
        order_no="0002", order_date="2026-08-20", expected_order_qty=10
    )

    assert first.found is True and first.fill_price == 50_000
    assert second.found is True and second.fill_price == 50_100
    assert len(session.calls) == 2
    assert sleeps == [0.8]


@pytest.mark.parametrize(
    ("gateway_factory", "timestamp", "now"),
    [
        (
            lambda session: KiwoomLowPriceTwoLegGateway(
                symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813131500",
            datetime(2026, 8, 13, 13, 16, 5, tzinfo=KST),
        ),
        (
            lambda session: KiwoomOneShareGateway(
                request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813091700",
            datetime(2026, 8, 13, 9, 18, 5, tzinfo=KST),
        ),
        (
            lambda session: KiwoomMiddayOneShareGateway(
                request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813131500",
            datetime(2026, 8, 13, 13, 16, 5, tzinfo=KST),
        ),
        (
            lambda session: KiwoomAfternoonOneShareGateway(
                request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813140000",
            datetime(2026, 8, 13, 14, 1, 5, tzinfo=KST),
        ),
    ],
)
def test_episode_gateways_cache_successful_completed_bars_within_same_minute(
    gateway_factory, timestamp: str, now: datetime
) -> None:
    session = FakeSession([_minute_response(timestamp)])
    gateway = gateway_factory(session)

    first = gateway.completed_sor_minute_bars(trade_date=date(2026, 8, 13), now=now)
    second = gateway.completed_sor_minute_bars(
        trade_date=date(2026, 8, 13), now=now.replace(second=55)
    )

    assert first.source_ok is True
    assert second is first
    assert len(session.calls) == 1


@pytest.mark.parametrize(
    ("gateway_factory", "stale_timestamp", "fresh_timestamp", "now"),
    [
        (
            lambda session: KiwoomLowPriceTwoLegGateway(
                symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813131400",
            "20260813131500",
            datetime(2026, 8, 13, 13, 16, 2, tzinfo=KST),
        ),
        (
            lambda session: KiwoomOneShareGateway(
                request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813091600",
            "20260813091700",
            datetime(2026, 8, 13, 9, 18, 2, tzinfo=KST),
        ),
        (
            lambda session: KiwoomMiddayOneShareGateway(
                request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813131400",
            "20260813131500",
            datetime(2026, 8, 13, 13, 16, 2, tzinfo=KST),
        ),
        (
            lambda session: KiwoomAfternoonOneShareGateway(
                request_session=session, token_loader=lambda: "TOKEN"
            ),
            "20260813135900",
            "20260813140000",
            datetime(2026, 8, 13, 14, 1, 2, tzinfo=KST),
        ),
    ],
)
def test_episode_gateways_refetch_prepublication_snapshot_within_same_minute(
    gateway_factory,
    stale_timestamp: str,
    fresh_timestamp: str,
    now: datetime,
) -> None:
    session = FakeSession(
        [_minute_response(stale_timestamp), _minute_response(fresh_timestamp)]
    )
    gateway = gateway_factory(session)

    stale = gateway.completed_sor_minute_bars(trade_date=date(2026, 8, 13), now=now)
    fresh = gateway.completed_sor_minute_bars(
        trade_date=date(2026, 8, 13), now=now.replace(second=4)
    )

    assert stale.source_ok is True
    assert fresh.source_ok is True
    assert stale.bars[-1].timestamp < fresh.bars[-1].timestamp
    assert len(session.calls) == 2


def test_episode_gateway_does_not_cache_failed_snapshot() -> None:
    session = FakeSession(
        [
            FakeResponse({"return_code": 1001, "return_msg": "temporary error"}),
            _minute_response("20260813131500"),
        ]
    )
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
    )
    now = datetime(2026, 8, 13, 13, 16, 5, tzinfo=KST)

    failed = gateway.completed_sor_minute_bars(trade_date=date(2026, 8, 13), now=now)
    recovered = gateway.completed_sor_minute_bars(
        trade_date=date(2026, 8, 13), now=now.replace(second=10)
    )

    assert failed.source_ok is False
    assert recovered.source_ok is True
    assert len(session.calls) == 2


def test_gateway_recovers_1700_read_but_does_not_retry_order_write() -> None:
    read_session = FakeSession(
        [
            FakeResponse({"return_code": 1700, "return_msg": "[1700] 요청 개수 초과"}),
            _minute_response("20260813131500"),
        ]
    )
    sleeps: list[float] = []
    read_gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150",
        request_session=read_session,
        token_loader=lambda: "TOKEN",
        read_retry_sleep=sleeps.append,
    )
    snapshot = read_gateway.completed_sor_minute_bars(
        trade_date=date(2026, 8, 13),
        now=datetime(2026, 8, 13, 13, 16, 5, tzinfo=KST),
    )
    assert snapshot.source_ok is True
    assert len(read_session.calls) == 2
    assert sleeps == [0.8]

    write_session = FakeSession(
        [FakeResponse({"return_code": 1700, "return_msg": "[1700] 요청 개수 초과"})]
    )
    write_gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150",
        request_session=write_session,
        token_loader=lambda: "TOKEN",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    result = write_gateway.submit_limit_buy(price=50_000, quantity=10)
    assert result.accepted is False
    assert result.return_code == "1700"
    assert len(write_session.calls) == 1
