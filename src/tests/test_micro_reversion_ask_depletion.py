from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.engine.scalping.micro_reversion.ask_depletion import (
    ASK_DEPLETION_METRIC_CONTRACT,
    AskDepletionContext,
    build_ask_depletion_report,
)
from src.engine.scalping.micro_reversion.path_journal import MarketDepthPoint

BASE = datetime.fromisoformat("2026-08-25T09:00:00+09:00")


def _timestamp(offset_ms: int) -> str:
    return (BASE + timedelta(milliseconds=offset_ms)).isoformat(timespec="milliseconds")


def _depth_row(
    *,
    offset_ms: int,
    sequence: int,
    best_ask: int = 10_010,
    ask_prices: tuple[int, ...] = (10_010, 10_020, 10_030, 10_040, 10_050),
    ask_quantities: tuple[int, ...] = (100, 200, 300, 400, 500),
    symbol: str = "000001",
    venue: str = "KRX",
    sequence_epoch: int = 7,
) -> dict:
    ask_depth = sum(ask_quantities)
    return MarketDepthPoint(
        symbol=symbol,
        exchange_timestamp=_timestamp(offset_ms),
        local_receive_timestamp=_timestamp(offset_ms),
        source_sequence=sequence,
        sequence_epoch=sequence_epoch,
        series_sequence=sequence,
        venue=venue,
        session_bucket=f"{venue}_REGULAR",
        item={"KRX": symbol, "NXT": f"{symbol}_NX"}[venue],
        orderbook_time_raw="090000000",
        best_bid=9_990,
        best_ask=best_ask,
        best_bid_qty=500,
        best_ask_qty=ask_quantities[0],
        bid_depth=1_500,
        ask_depth=ask_depth,
        bid_levels=(
            (1, 9_990, 500),
            (2, 9_980, 400),
            (3, 9_970, 300),
            (4, 9_960, 200),
            (5, 9_950, 100),
        ),
        ask_levels=tuple(
            (index, price, quantity)
            for index, (price, quantity) in enumerate(
                zip(ask_prices, ask_quantities, strict=True), start=1
            )
        ),
        route_depth_totals={
            "combined": {"ask": ask_depth, "bid": 1_500},
            venue: {"ask": ask_depth, "bid": 1_500},
        },
    ).as_dict()


def _market_row(
    *,
    offset_ms: int,
    sequence: int,
    aggressor_side: str = "BUY",
    trade_price: int | None = 10_010,
    trade_qty: int | None = 30,
    symbol: str = "000001",
    venue: str = "KRX",
    sequence_epoch: int = 7,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_stream_point_v3",
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v3",
        "realtime_type": "0B",
        "item": {"KRX": symbol, "NXT": f"{symbol}_NX"}[venue],
        "symbol": symbol,
        "venue": venue,
        "session_bucket": f"{venue}_REGULAR",
        "local_receive_timestamp": _timestamp(offset_ms),
        "exchange_timestamp": _timestamp(offset_ms),
        "sequence_epoch": sequence_epoch,
        "source_sequence": sequence,
        "series_sequence": sequence,
        "trade_price": trade_price,
        "trade_qty": trade_qty,
        "aggressor_side": aggressor_side,
        "path_order_status": "accept",
        "path_consumer_eligible": True,
        "exchange_timestamp_regression_ms": 0,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }


def _context(**overrides) -> AskDepletionContext:
    values = {
        "event_id": "shock-1",
        "anchor_role": "shock_event",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "anchor_event_local_receive_timestamp_ms": int(BASE.timestamp() * 1_000),
        "event_market_source_sequence": 50,
        "observed_through_local_receive_timestamp_ms": int(
            (BASE + timedelta(seconds=11)).timestamp() * 1_000
        ),
        "depth_source_complete": True,
        "market_source_complete": True,
    }
    values.update(overrides)
    return AskDepletionContext(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_id", 123),
        ("event_id", " shock-1"),
        ("anchor_role", "decision"),
        ("symbol", 1),
        ("venue", 1),
        ("session_bucket", 123),
        ("sequence_epoch", True),
        ("anchor_event_local_receive_timestamp_ms", True),
        ("event_market_source_sequence", True),
        ("observed_through_local_receive_timestamp_ms", True),
    ],
)
def test_context_rejects_non_native_or_ambiguous_identity_values(field, value) -> None:
    with pytest.raises(ValueError):
        _context(**{field: value})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"horizons_ms": (True,)},
        {"horizons_ms": (500.0,)},
        {"top_depth_levels": (True,)},
        {"top_depth_levels": (3.0,)},
        {"max_depth_age_ms": 1_000.0},
    ],
)
def test_configuration_rejects_non_native_integer_values(kwargs) -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    with pytest.raises(ValueError):
        build_ask_depletion_report(
            context=_context(),
            anchor_depth=anchor,
            depth_rows=(anchor,),
            market_rows=(),
            **kwargs,
        )


def _complete_depth_path() -> tuple[dict, ...]:
    return (
        _depth_row(
            offset_ms=250,
            sequence=11,
            ask_quantities=(60, 160, 260, 360, 460),
        ),
        _depth_row(
            offset_ms=499,
            sequence=12,
            ask_quantities=(60, 160, 260, 360, 460),
        ),
        _depth_row(
            offset_ms=700,
            sequence=13,
            ask_quantities=(80, 180, 280, 380, 480),
        ),
        _depth_row(
            offset_ms=999,
            sequence=14,
            ask_quantities=(80, 180, 280, 380, 480),
        ),
        _depth_row(
            offset_ms=1_500,
            sequence=15,
            best_ask=10_020,
            ask_prices=(10_020, 10_030, 10_040, 10_050, 10_060),
            ask_quantities=(150, 250, 350, 450, 550),
        ),
        _depth_row(
            offset_ms=2_999,
            sequence=16,
            best_ask=10_020,
            ask_prices=(10_020, 10_030, 10_040, 10_050, 10_060),
            ask_quantities=(150, 250, 350, 450, 550),
        ),
        _depth_row(
            offset_ms=4_999,
            sequence=17,
            best_ask=10_020,
            ask_prices=(10_020, 10_030, 10_040, 10_050, 10_060),
            ask_quantities=(150, 250, 350, 450, 550),
        ),
        _depth_row(
            offset_ms=9_999,
            sequence=18,
            best_ask=10_020,
            ask_prices=(10_020, 10_030, 10_040, 10_050, 10_060),
            ask_quantities=(150, 250, 350, 450, 550),
        ),
    )


def test_builds_fixed_price_depletion_trade_backing_refill_and_clear() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(anchor, *_complete_depth_path()),
        market_rows=(
            _market_row(offset_ms=200, sequence=51, trade_qty=30),
            _market_row(
                offset_ms=400,
                sequence=52,
                aggressor_side="SELL",
                trade_qty=5,
            ),
        ),
    )

    assert tuple(row.horizon_ms for row in report.horizons) == (
        500,
        1_000,
        3_000,
        5_000,
        10_000,
    )
    first = report.horizons[0]
    assert first.source_quality_status == "eligible_source_only_feature_ablation"
    assert first.initial_anchor_ask_qty == 100
    assert first.minimum_anchor_ask_qty == 60
    assert first.max_best_ask_depletion_qty == 40
    assert first.max_best_ask_depletion_ratio == 0.4
    assert first.best_ask_depletion_velocity_qty_per_sec == 160.0
    assert first.aggressive_buy_qty_before_max_depletion == 30
    assert first.aggressive_buy_trade_backed_ratio == 0.75
    assert first.unexplained_or_cancel_like_depletion_qty == 10
    assert first.unexplained_or_cancel_like_depletion_ratio == 0.25
    assert first.top_depth[0].retained_level_count == 3
    assert first.top_depth[0].initial_qty == 600
    assert first.top_depth[0].max_depletion_qty == 120
    assert first.top_depth[1].retained_level_count == 5

    one_second = report.horizons[1]
    assert one_second.max_refill_qty == 20
    assert one_second.refill_ratio == 0.5
    assert one_second.refill_half_life_ms == 450

    three_second = report.horizons[2]
    assert three_second.price_level_cleared is True
    assert three_second.first_price_level_clear_delay_ms == 1_500
    assert three_second.minimum_anchor_ask_qty == 0
    assert three_second.endpoint_anchor_ask_qty == 0

    payload = report.as_dict()
    assert payload["runtime_effect"] is False
    assert payload["actual_order_submitted"] is False
    assert payload["broker_order_forbidden"] is True
    assert payload["decision_authority"] == (
        "source_only_feature_ablation_no_runtime_authority"
    )
    assert set(ASK_DEPLETION_METRIC_CONTRACT) == {
        "metric_role",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "source_quality_gate",
        "forbidden_uses",
    }
    assert "runtime_or_preopen_env_mutation" in payload["forbidden_uses"]


def test_ignores_cross_scope_rows_and_never_uses_their_depletion() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    same_scope = _depth_row(offset_ms=499, sequence=11)
    wrong_venue = _depth_row(
        offset_ms=100,
        sequence=1,
        venue="NXT",
        ask_quantities=(0, 0, 0, 0, 0),
    )
    wrong_epoch = _depth_row(
        offset_ms=100,
        sequence=1,
        sequence_epoch=8,
        ask_quantities=(0, 0, 0, 0, 0),
    )
    wrong_epoch["actual_order_submitted"] = True
    wrong_market = _market_row(
        offset_ms=100,
        sequence=1,
        venue="NXT",
        trade_qty=1_000,
    )
    wrong_market["broker_order_forbidden"] = False

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(same_scope, wrong_venue, wrong_epoch),
        market_rows=(wrong_market,),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert horizon.max_best_ask_depletion_qty == 0
    assert horizon.aggressive_buy_qty_before_max_depletion == 0
    assert report.ignored_cross_scope_depth_row_count == 2
    assert report.ignored_cross_scope_market_row_count == 1


def test_downward_reprice_without_anchor_price_fails_fixed_price_gate() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    displaced = _depth_row(
        offset_ms=499,
        sequence=11,
        best_ask=10_000,
        ask_prices=(10_000, 10_001, 10_002, 10_003, 10_004),
        ask_quantities=(100, 100, 100, 100, 100),
    )

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(displaced,),
        market_rows=(),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert horizon.source_quality_status == "source_gap"
    assert "anchor_ask_price_not_retained" in horizon.source_gap_reasons
    assert horizon.downward_reprice_observed is True
    assert horizon.max_best_ask_depletion_qty is None
    assert horizon.unexplained_or_cancel_like_depletion_ratio is None


def test_stale_depth_data_wait_and_incomplete_market_are_fail_closed() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    stale_report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(),
        market_rows=(),
        horizons_ms=(500,),
        max_depth_age_ms=500,
    )
    assert stale_report.horizons[0].source_quality_status == "source_gap"
    assert "depth_endpoint_stale" in stale_report.horizons[0].source_gap_reasons

    decision_ms = int(BASE.timestamp() * 1_000)
    wait_report = build_ask_depletion_report(
        context=_context(
            observed_through_local_receive_timestamp_ms=decision_ms + 300,
        ),
        anchor_depth=anchor,
        depth_rows=(),
        market_rows=(),
        horizons_ms=(500,),
    )
    assert wait_report.horizons[0].source_quality_status == "data_wait"
    assert wait_report.horizons[0].mature is False

    incomplete_report = build_ask_depletion_report(
        context=_context(market_source_complete=False),
        anchor_depth=anchor,
        depth_rows=(
            _depth_row(
                offset_ms=499,
                sequence=11,
                ask_quantities=(50, 150, 250, 350, 450),
            ),
        ),
        market_rows=(),
        horizons_ms=(500,),
    )
    incomplete = incomplete_report.horizons[0]
    assert "market_source_incomplete" in incomplete.source_gap_reasons
    assert incomplete.max_best_ask_depletion_qty == 50
    assert incomplete.aggressive_buy_trade_backed_ratio is None
    assert incomplete.unexplained_or_cancel_like_depletion_ratio is None

    zero_anchor = _depth_row(
        offset_ms=-100,
        sequence=10,
        ask_quantities=(0, 200, 300, 400, 500),
    )
    zero_report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=zero_anchor,
        depth_rows=(
            _depth_row(
                offset_ms=499,
                sequence=11,
                ask_quantities=(0, 200, 300, 400, 500),
            ),
        ),
        market_rows=(),
        horizons_ms=(500,),
    )
    assert (
        "anchor_best_ask_quantity_not_positive"
        in zero_report.horizons[0].source_gap_reasons
    )


def test_sequence_gap_blocks_feature_ablation_and_authority_drift_is_rejected() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(_depth_row(offset_ms=499, sequence=12),),
        market_rows=(),
        horizons_ms=(500,),
    )
    assert "depth_sequence_gap" in report.horizons[0].source_gap_reasons
    assert report.horizons[0].eligible_for_feature_ablation is False

    invalid = _market_row(offset_ms=100, sequence=51)
    invalid["actual_order_submitted"] = True
    with pytest.raises(ValueError, match="authority"):
        build_ask_depletion_report(
            context=_context(),
            anchor_depth=anchor,
            depth_rows=(_depth_row(offset_ms=499, sequence=11),),
            market_rows=(invalid,),
            horizons_ms=(500,),
        )


def test_canonical_v3_market_row_may_omit_registration_item() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    market = _market_row(offset_ms=200, sequence=51)
    market.pop("item")

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(
            _depth_row(
                offset_ms=499,
                sequence=11,
                ask_quantities=(70, 170, 270, 370, 470),
            ),
        ),
        market_rows=(market,),
        horizons_ms=(500,),
    )

    assert report.horizons[0].aggressive_buy_trade_backed_ratio == 1.0


def test_millisecond_event_watermark_excludes_the_exact_event_sequence() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    event_row = _market_row(offset_ms=0, sequence=50, trade_qty=100)
    event_row["local_receive_timestamp"] = "2026-08-25T09:00:00.000900+09:00"
    event_row["exchange_timestamp"] = "2026-08-25T09:00:00.000800+09:00"

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(
            _depth_row(
                offset_ms=499,
                sequence=11,
                ask_quantities=(50, 150, 250, 350, 450),
            ),
        ),
        market_rows=(event_row, _market_row(offset_ms=200, sequence=51)),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert "market_sequence_gap" not in horizon.source_gap_reasons
    assert horizon.aggressive_buy_qty_before_max_depletion == 30


def test_unknown_aggressor_at_anchor_ask_blocks_cancel_like_attribution() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(
            _depth_row(
                offset_ms=499,
                sequence=11,
                ask_quantities=(50, 150, 250, 350, 450),
            ),
        ),
        market_rows=(
            _market_row(
                offset_ms=200,
                sequence=51,
                aggressor_side="UNKNOWN",
            ),
        ),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert "anchor_ask_trade_aggressor_unknown" in horizon.source_gap_reasons
    assert horizon.aggressive_buy_trade_backed_ratio is None
    assert horizon.unexplained_or_cancel_like_depletion_ratio is None


def test_same_millisecond_depth_after_shock_is_never_used_as_anchor_or_sample() -> None:
    anchor = _depth_row(offset_ms=-1, sequence=10)
    ambiguous = _depth_row(
        offset_ms=0,
        sequence=11,
        ask_quantities=(1, 2, 3, 4, 5),
    )
    later = _depth_row(
        offset_ms=250,
        sequence=12,
        ask_quantities=(50, 150, 250, 350, 450),
    )

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(ambiguous, later),
        market_rows=(),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert report.anchor_source_sequence == 10
    assert "depth_order_ambiguous_at_shock_millisecond" in (horizon.source_gap_reasons)
    assert horizon.initial_anchor_ask_qty == 100
    assert horizon.minimum_anchor_ask_qty == 50
    assert horizon.eligible_for_feature_ablation is False


def test_depth_at_exact_horizon_endpoint_is_included() -> None:
    anchor = _depth_row(offset_ms=-1, sequence=10)
    exact_endpoint = _depth_row(
        offset_ms=500,
        sequence=11,
        ask_quantities=(0, 100, 200, 300, 400),
    )

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(exact_endpoint,),
        market_rows=(),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert horizon.depth_observation_count == 2
    assert horizon.depth_endpoint_age_ms == 0
    assert horizon.endpoint_anchor_ask_qty == 0
    assert horizon.minimum_anchor_ask_qty == 0
    assert horizon.max_best_ask_depletion_qty == 100


def test_trade_at_same_millisecond_as_depth_minimum_is_not_attributed() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    minimum = _depth_row(
        offset_ms=250,
        sequence=11,
        ask_quantities=(50, 150, 250, 350, 450),
    )

    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(minimum,),
        market_rows=(_market_row(offset_ms=250, sequence=51, trade_qty=50),),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert "trade_depth_order_ambiguous_same_millisecond" in (
        horizon.source_gap_reasons
    )
    assert horizon.aggressive_buy_trade_backed_ratio is None
    assert horizon.unexplained_or_cancel_like_depletion_ratio is None


def test_missing_market_trade_fields_block_cancel_like_attribution() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(
            _depth_row(
                offset_ms=499,
                sequence=11,
                ask_quantities=(50, 150, 250, 350, 450),
            ),
        ),
        market_rows=(
            _market_row(
                offset_ms=200,
                sequence=51,
                trade_price=None,
                trade_qty=None,
            ),
        ),
        horizons_ms=(500,),
    )

    horizon = report.horizons[0]
    assert horizon.eligible_for_feature_ablation is False
    assert "market_trade_fields_missing" in horizon.source_gap_reasons
    assert horizon.aggressive_buy_qty_before_max_depletion is None
    assert horizon.unexplained_or_cancel_like_depletion_ratio is None


def test_anchor_must_be_exact_latest_nonfuture_scope() -> None:
    anchor = _depth_row(offset_ms=-100, sequence=10)
    later_nonfuture = _depth_row(offset_ms=-50, sequence=11)
    report = build_ask_depletion_report(
        context=_context(),
        anchor_depth=anchor,
        depth_rows=(later_nonfuture,),
        market_rows=(),
        horizons_ms=(500,),
    )
    assert report.anchor_source_quality_status == "source_gap"
    assert "anchor_is_not_latest_nonfuture_depth" in report.source_gap_reasons

    wrong_scope = _depth_row(
        offset_ms=-100,
        sequence=10,
        venue="NXT",
    )
    with pytest.raises(ValueError, match="anchor scope"):
        build_ask_depletion_report(
            context=_context(),
            anchor_depth=wrong_scope,
            depth_rows=(),
            market_rows=(),
            horizons_ms=(500,),
        )

    with pytest.raises(ValueError, match="duplicate depth"):
        build_ask_depletion_report(
            context=_context(),
            anchor_depth=anchor,
            depth_rows=(anchor, dict(anchor)),
            market_rows=(),
            horizons_ms=(500,),
        )
