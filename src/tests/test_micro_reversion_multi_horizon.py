from src.engine.scalping.micro_reversion.contracts import PriceObservation
from src.engine.scalping.micro_reversion.detector import DetectorConfig
from src.engine.scalping.micro_reversion.multi_horizon import (
    MultiHorizonConfig,
    MultiHorizonShockDetector,
)


def _observation(timestamp_ms: int, price: float) -> PriceObservation:
    return PriceObservation(
        symbol="000001",
        observed_at_ms=timestamp_ms,
        price=price,
        trade_date="2026-08-08",
        venue="KRX",
        session_bucket="KRX_REGULAR",
    )


def test_multi_horizon_groups_same_wave_and_state_rearms() -> None:
    detector = MultiHorizonShockDetector(
        MultiHorizonConfig(
            horizons_ms=(1_000,),
            recovery_from_low_bps=20,
            new_impulse_from_peak_bps=-20,
            detector_base=DetectorConfig(
                return_window_ms=1_000,
                absolute_shock_bps=-30,
                release_return_bps=-10,
                cooldown_ms=0,
            ),
        )
    )
    events = detector.process_many(
        [
            _observation(1_000, 100.0),
            _observation(2_000, 99.0),
            _observation(3_000, 100.0),
            _observation(4_000, 99.0),
        ]
    )

    assert len(events) == 2
    assert events[0].parent_wave_id != events[1].parent_wave_id
    assert events[0].shock_event_id.endswith("-H1000")
    assert events[0].rearm_reason == "initial_shock"
    assert events[1].rearm_reason == "recovery_then_new_impulse"
    assert events[0].as_dict()["metric_role"] == "pattern_discovery_feature"


def test_drop_symbol_discards_detector_state() -> None:
    detector = MultiHorizonShockDetector(MultiHorizonConfig(horizons_ms=(1_000, 3_000)))
    detector.process(_observation(1_000, 10_000.0))

    assert detector.drop_symbol("000001") == 2
