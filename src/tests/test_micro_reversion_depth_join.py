import json

import pytest

from src.engine.scalping.micro_reversion.depth_join import (
    join_latest_past_depth,
    read_depth_rows,
)
from src.engine.scalping.micro_reversion.path_journal import (
    MarketDepthPoint,
    _validate_batch_order,
)


def _depth_row(
    *,
    received: str,
    sequence: int = 1,
    venue: str = "KRX",
    sequence_epoch: int = 123,
) -> dict:
    return MarketDepthPoint(
        symbol="000001",
        exchange_timestamp=received,
        local_receive_timestamp=received,
        source_sequence=sequence,
        sequence_epoch=sequence_epoch,
        series_sequence=sequence,
        venue=venue,
        session_bucket=f"{venue}_REGULAR",
        item={"KRX": "000001", "NXT": "000001_NX", "SOR": "000001_AL"}[venue],
        orderbook_time_raw="090000000",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=200,
        best_ask_qty=100,
        bid_depth=400,
        ask_depth=300,
        bid_levels=((1, 10_000, 200), (2, 9_990, 200)),
        ask_levels=((1, 10_010, 100), (2, 10_020, 200)),
        route_depth_totals={
            "combined": {"ask": 300, "bid": 400},
            "KRX": {"ask": 300, "bid": 400},
            "NXT": {"ask": 0, "bid": 0},
        },
    ).as_dict()


def _market_row(
    *,
    received: str,
    venue: str = "KRX",
    sequence_epoch: int = 123,
    sequence: int = 1,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_stream_point_v3",
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v3",
        "realtime_type": "0B",
        "item": {"KRX": "000001", "NXT": "000001_NX", "SOR": "000001_AL"}[venue],
        "symbol": "000001",
        "venue": venue,
        "session_bucket": f"{venue}_REGULAR",
        "local_receive_timestamp": received,
        "exchange_timestamp": received,
        "sequence_epoch": sequence_epoch,
        "source_sequence": sequence,
        "series_sequence": sequence,
        "bid_depth": None,
        "ask_depth": None,
        "path_order_status": "accept",
        "path_consumer_eligible": True,
        "exchange_timestamp_regression_ms": 0,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "decision_authority": "canonical_market_stream_observation_only",
    }


def test_join_uses_latest_nonfuture_same_series_depth() -> None:
    depths = (
        _depth_row(received="2026-08-08T09:00:00.100+09:00", sequence=1),
        _depth_row(received="2026-08-08T09:00:00.300+09:00", sequence=2),
    )

    joined = join_latest_past_depth(
        (_market_row(received="2026-08-08T09:00:00.200+09:00"),),
        depths,
        max_age_ms=500,
    )[0]

    assert joined["depth_join_status"] == "joined_fresh_past_depth"
    assert joined["depth_age_ms"] == 100
    assert joined["depth_context"]["source_sequence"] == 1
    assert joined["bid_depth"] == 400
    assert joined["ask_depth"] == 300
    assert joined["decision_authority"] == "canonical_market_stream_observation_only"
    assert joined["depth_join_metric_contract"]["decision_authority"] == (
        "offline_research_join_only"
    )


def test_join_never_crosses_venue_and_marks_stale() -> None:
    depth = _depth_row(received="2026-08-08T09:00:00.000+09:00")
    rows = (
        _market_row(received="2026-08-08T09:00:02.000+09:00"),
        _market_row(received="2026-08-08T09:00:00.100+09:00", venue="NXT"),
    )

    stale, wrong_venue = join_latest_past_depth(rows, (depth,), max_age_ms=500)

    assert stale["depth_join_status"] == "stale_past_depth"
    assert stale["bid_depth"] is None
    assert wrong_venue["depth_join_status"] == "missing_same_series_depth"


def test_join_never_crosses_sequence_epoch() -> None:
    depth = _depth_row(received="2026-08-08T09:00:00.000+09:00", sequence_epoch=122)
    market = _market_row(received="2026-08-08T09:00:00.100+09:00", sequence_epoch=123)

    joined = join_latest_past_depth((market,), (depth,), max_age_ms=500)[0]

    assert joined["depth_join_status"] == "missing_same_series_depth"
    assert "depth_context" not in joined


def test_join_preserves_sub_millisecond_causality() -> None:
    depth = _depth_row(received="2026-08-08T09:00:00.100900+09:00")
    market = _market_row(received="2026-08-08T09:00:00.100100+09:00")

    joined = join_latest_past_depth((market,), (depth,), max_age_ms=500)[0]

    assert joined["depth_join_status"] == "missing_same_series_depth"


def test_join_rejects_market_authority_drift_and_depth_quantity_conflict() -> None:
    depth = _depth_row(received="2026-08-08T09:00:00.000+09:00")
    market = _market_row(received="2026-08-08T09:00:00.100+09:00")
    market["actual_order_submitted"] = True

    with pytest.raises(ValueError, match="market authority"):
        join_latest_past_depth((market,), (depth,))

    invalid_depth = dict(depth)
    invalid_depth["best_bid_qty"] = 199
    with pytest.raises(ValueError, match="quantity conflicts"):
        join_latest_past_depth(
            (_market_row(received="2026-08-08T09:00:00.100+09:00"),),
            (invalid_depth,),
        )


def test_join_rejects_item_symbol_and_venue_scope_conflicts() -> None:
    depth = _depth_row(received="2026-08-08T09:00:00.000+09:00")
    depth["item"] = "999999"
    with pytest.raises(ValueError, match="item symbol or venue"):
        join_latest_past_depth(
            (_market_row(received="2026-08-08T09:00:00.100+09:00"),),
            (depth,),
        )

    market = _market_row(
        received="2026-08-08T09:00:00.100+09:00",
        venue="NXT",
    )
    market["item"] = "000001"
    with pytest.raises(ValueError, match="item symbol or venue"):
        join_latest_past_depth((market,), ())


def test_join_rejects_duplicate_depth_sequence_and_prejoined_market_row() -> None:
    depth = _depth_row(received="2026-08-08T09:00:00.000+09:00")
    market = _market_row(received="2026-08-08T09:00:00.100+09:00")

    with pytest.raises(ValueError, match="duplicate"):
        join_latest_past_depth((market,), (depth, dict(depth)))

    market["bid_depth"] = 1
    with pytest.raises(ValueError, match="prejoined"):
        join_latest_past_depth((market,), (depth,))


def test_read_depth_rows_rejects_authority_drift(tmp_path) -> None:
    row = _depth_row(received="2026-08-08T09:00:00.000+09:00")
    row["actual_order_submitted"] = True
    path = tmp_path / "market_depth_stream.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="authority"):
        read_depth_rows((path,))


def test_depth_writer_order_rejects_local_receive_time_regression() -> None:
    first = MarketDepthPoint(
        **{
            key: value
            for key, value in _depth_row(
                received="2026-08-08T09:00:00.200+09:00", sequence=1
            ).items()
            if key in MarketDepthPoint.__dataclass_fields__
        }
    )
    second_payload = _depth_row(received="2026-08-08T09:00:00.100+09:00", sequence=2)
    second = MarketDepthPoint(
        **{
            key: value
            for key, value in second_payload.items()
            if key in MarketDepthPoint.__dataclass_fields__
        }
    )

    with pytest.raises(ValueError, match="increase"):
        _validate_batch_order((first, second))
