from __future__ import annotations

from src.engine.scalping.micro_reversion.contracts import PriceObservation
from src.engine.scalping.micro_reversion.detector import (
    DetectorConfig,
    ShockDetector,
    robust_zscore,
)

BASE_MS = 1_786_000_000_000


def _observation(offset_sec: int, price: float) -> PriceObservation:
    return PriceObservation(
        symbol="000001",
        observed_at_ms=BASE_MS + offset_sec * 1_000,
        price=price,
        trade_date="2026-08-07",
        venue="KRX",
        session_bucket="KRX_REGULAR",
    )


def test_robust_zscore_uses_median_and_mad() -> None:
    assert robust_zscore(-40, [-2, -1, 0, 1, 2]) < -10
    assert robust_zscore(1, [1, 1]) is None


def test_detector_deduplicates_episode_and_enforces_release_cooldown() -> None:
    config = DetectorConfig(cooldown_ms=60_000)
    observations = [
        _observation(0, 10_000),
        _observation(5, 9_950),
        _observation(6, 9_940),
        _observation(10, 10_000),
        _observation(15, 9_940),
        _observation(70, 10_000),
        _observation(75, 9_940),
    ]

    detector = ShockDetector(config)
    events = detector.process_many(observations)

    assert len(events) == 2
    assert events[0].shock_return_bps == -50.0
    assert events[1].shock_return_bps == -60.0
    assert events[0].event_id != events[1].event_id

    replayed = ShockDetector(config).process_many(observations)
    assert [event.event_id for event in replayed] == [
        event.event_id for event in events
    ]


def test_detector_rejects_out_of_order_observation() -> None:
    detector = ShockDetector()
    detector.process(_observation(5, 10_000))

    try:
        detector.process(_observation(4, 9_900))
    except ValueError as exc:
        assert "strictly increasing" in str(exc)
    else:
        raise AssertionError("out-of-order observation must fail")
