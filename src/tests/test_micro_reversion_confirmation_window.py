from __future__ import annotations

from src.engine.scalping.micro_reversion.confirmation_window import (
    ConfirmationDirectionState,
    analyze_confirmation_window,
)
from src.engine.scalping.micro_reversion.onset_quality import (
    ShockOnsetContext,
    ShockTriggerBasis,
)
from src.engine.scalping.micro_reversion.p2_replay import P2ReplayPoint


def _point(offset: int, sequence: int, **overrides) -> P2ReplayPoint:
    values = {
        "exchange_timestamp_ms": 1_000_000 + offset,
        "local_receive_timestamp_ms": 1_000_010 + offset,
        "source_sequence": sequence,
        "trade_price": 100.0,
        "trade_qty": 10,
        "best_bid": 99.9,
        "best_ask": 100.1,
        "quote_age_ms": 10.0,
        "aggressor_side": "SELL",
    }
    values.update(overrides)
    return P2ReplayPoint(**values)


def _context() -> ShockOnsetContext:
    return ShockOnsetContext(
        shock_event_id="shock-1",
        symbol="000001",
        venue="KRX",
        session_bucket="KRX_REGULAR",
        sequence_epoch=7,
        shock_horizon_ms=1_000,
        event_exchange_timestamp_ms=1_000_000,
        event_local_receive_timestamp_ms=1_000_010,
        event_source_sequence=2,
        reference_price=100.5,
        shock_price=100.0,
        shock_return_bps=-49.751244,
        trigger_trade_qty=10,
        trigger_aggressor_side="SELL",
        trigger_basis=ShockTriggerBasis.ROBUST_RETURN,
    )


def test_separates_120s_reversion_from_180s_continuation() -> None:
    horizons = analyze_confirmation_window(
        (
            _point(60_000, 3, trade_price=99.0),
            _point(119_000, 4, trade_price=99.8),
            _point(120_000, 5, trade_price=99.8),
            _point(150_000, 6, trade_price=98.8),
            _point(180_000, 7, trade_price=99.0),
        ),
        context=_context(),
    )

    two_minute, three_minute = horizons
    assert two_minute.mature is True
    assert two_minute.confirmation_fraction == 0.5
    assert two_minute.half_reclaim_confirmed is True
    assert two_minute.confirmation_count == 1
    assert two_minute.active_confirmation_delay_ms == 119_000
    assert two_minute.confirmation_followthrough_ms == 1_000
    assert two_minute.confirmation_followthrough_trade_count == 2
    assert two_minute.confirmation_to_terminal_trade_return_bps == 0.0
    assert two_minute.direction_state is ConfirmationDirectionState.REVERSION_CONFIRMED
    assert three_minute.mature is True
    assert three_minute.half_reclaim_confirmed is False
    assert three_minute.recovery_invalidation_count == 1
    assert three_minute.active_confirmation_delay_ms is None
    assert three_minute.confirmation_to_terminal_trade_return_bps is None
    assert (
        three_minute.direction_state
        is ConfirmationDirectionState.CONTINUATION_CONFIRMED
    )


def test_does_not_classify_a_stale_horizon_endpoint() -> None:
    horizons = analyze_confirmation_window(
        (
            _point(100_000, 3, trade_price=99.8),
            _point(
                121_000,
                4,
                trade_price=None,
                trade_qty=None,
                best_bid=99.7,
                best_ask=99.8,
            ),
        ),
        context=_context(),
        horizons_ms=(120_000,),
        max_terminal_trade_lag_ms=2_500,
    )

    horizon = horizons[0]
    assert horizon.mature is True
    assert horizon.terminal_trade_lag_ms == 20_000
    assert horizon.direction_state is ConfirmationDirectionState.SOURCE_GAP


def test_keeps_an_unfinished_horizon_in_data_wait() -> None:
    horizon = analyze_confirmation_window(
        (_point(60_000, 3, trade_price=99.0),),
        context=_context(),
        horizons_ms=(120_000,),
    )[0]

    assert horizon.mature is False
    assert horizon.direction_state is ConfirmationDirectionState.DATA_WAIT


def test_reclaim_must_remain_active_at_the_confirmation_deadline() -> None:
    horizon = analyze_confirmation_window(
        (
            _point(60_000, 3, trade_price=99.0),
            _point(90_000, 4, trade_price=99.8),
            _point(120_000, 5, trade_price=99.2),
        ),
        context=_context(),
        horizons_ms=(120_000,),
    )[0]

    assert horizon.confirmation_count == 1
    assert horizon.recovery_invalidation_count == 1
    assert horizon.half_reclaim_confirmed is False
    assert horizon.active_confirmation_delay_ms is None
    assert horizon.direction_state is ConfirmationDirectionState.CONTINUATION_CONFIRMED


def test_confirmation_fraction_is_an_explicit_tuning_parameter() -> None:
    points = (
        _point(60_000, 3, trade_price=99.0),
        _point(119_000, 4, trade_price=99.6),
        _point(120_000, 5, trade_price=99.6),
    )

    loose = analyze_confirmation_window(
        points,
        context=_context(),
        horizons_ms=(120_000,),
        confirmation_fraction=0.35,
    )[0]
    strict = analyze_confirmation_window(
        points,
        context=_context(),
        horizons_ms=(120_000,),
        confirmation_fraction=0.65,
    )[0]

    assert loose.direction_state is ConfirmationDirectionState.REVERSION_CONFIRMED
    assert strict.direction_state is ConfirmationDirectionState.CONTINUATION_CONFIRMED
