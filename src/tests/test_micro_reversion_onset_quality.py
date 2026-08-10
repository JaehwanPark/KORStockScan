from __future__ import annotations

import pytest

from src.engine.scalping.micro_reversion.onset_quality import (
    ShockOnsetContext,
    ShockTriggerBasis,
    analyze_shock_onset,
    reconstruct_shock_onset_context,
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


def _context(**overrides) -> ShockOnsetContext:
    values = {
        "shock_event_id": "shock-1",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "shock_horizon_ms": 1_000,
        "event_exchange_timestamp_ms": 1_000_000,
        "event_local_receive_timestamp_ms": 1_000_010,
        "event_source_sequence": 2,
        "reference_price": 100.5,
        "shock_price": 100.0,
        "shock_return_bps": -49.751244,
        "trigger_trade_qty": 10,
        "trigger_aggressor_side": "SELL",
        "trigger_basis": ShockTriggerBasis.ROBUST_RETURN,
        "return_robust_z": -3.5,
    }
    values.update(overrides)
    return ShockOnsetContext(**values)


def test_reconstructs_onset_price_and_marks_trigger_basis_unknown() -> None:
    points = (
        _point(-1_000, 1, trade_price=100.5, aggressor_side="BUY"),
        _point(0, 2, trade_price=100.0, trade_qty=3),
        _point(100, 3, trade_price=99.8),
    )
    reference = {
        "schema": "scalp_micro_reversion_path_event_reference_v2",
        "shock_event_id": "shock-1",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "shock_horizon_ms": 1_000,
        "event_detected_at_ms": 1_000_010,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }

    context = reconstruct_shock_onset_context(points, reference=reference)

    assert context.reference_price == 100.5
    assert context.shock_price == 100.0
    assert context.shock_return_bps == pytest.approx(-49.751244)
    assert context.event_source_sequence == 2
    assert context.trigger_trade_qty == 3
    assert context.trigger_trade_notional == 300.0
    assert context.trigger_aggressor_side == "SELL"
    assert context.trigger_basis is ShockTriggerBasis.UNKNOWN_RECONSTRUCTED


def test_onset_quality_measures_additional_low_delay_and_reclaim() -> None:
    report = analyze_shock_onset(
        (
            _point(100, 3, trade_price=99.0),
            _point(200, 4, trade_price=99.5),
            _point(600, 5, trade_price=100.2),
        ),
        context=_context(),
        horizons_ms=(300, 500),
    )

    first, second = report.horizons
    assert first.mature is True
    assert first.post_trade_count == 2
    assert first.additional_mae_bps == -100.0
    assert first.post_low_delay_ms == 100
    assert first.terminal_trade_return_bps == -50.0
    assert first.max_reclaim_from_post_low_bps == pytest.approx(50.505051)
    assert second.mature is True
    assert second.post_trade_count == 2
    payload = report.as_dict()
    assert payload["decision_authority"] == "shock_onset_timing_diagnostic_only"
    assert payload["selection_authority"] is False
    assert payload["actual_order_submitted"] is False
    assert payload["broker_order_forbidden"] is True


def test_onset_quality_does_not_impute_missing_post_trade() -> None:
    report = analyze_shock_onset(
        (
            _point(
                600,
                3,
                trade_price=None,
                trade_qty=None,
                best_bid=99.0,
                best_ask=99.1,
            ),
        ),
        context=_context(),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert horizon.mature is True
    assert horizon.post_trade_count == 0
    assert horizon.additional_mae_bps is None
    assert horizon.terminal_trade_return_bps is None


def test_onset_reconstruction_replays_detector_clock_for_duplicate_receive_ms() -> None:
    points = (
        _point(-1_000, 1, trade_price=100.5),
        _point(0, 2, trade_price=100.0),
        _point(0, 3, trade_price=99.9),
    )
    reference = {
        "schema": "scalp_micro_reversion_path_event_reference_v2",
        "shock_event_id": "shock-1",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "shock_horizon_ms": 1_000,
        "event_detected_at_ms": 1_000_011,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }

    context = reconstruct_shock_onset_context(points, reference=reference)

    assert context.event_source_sequence == 3
    assert context.shock_price == 99.9
