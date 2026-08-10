import gzip
import json
from pathlib import Path

from src.engine.scalping.micro_reversion.p2_replay import (
    EntryPolicy,
    ExitPolicy,
    FillBound,
    P2ReplayPoint,
    P2ReplayPolicy,
    ReplayTerminalReason,
    SameTimestampPolicy,
    load_p2_points_from_canonical_stream,
    replay_path,
)


def test_canonical_stream_loader_reconstructs_only_referenced_window(
    tmp_path: Path,
) -> None:
    stream = tmp_path / "market_stream.jsonl"
    rows = []
    for sequence, second in enumerate((0, 1, 2, 4), start=1):
        rows.append(
            {
                "schema": "scalp_micro_reversion_market_stream_point_v1",
                "symbol": "000001",
                "venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "sequence_epoch": 7,
                "source_sequence": sequence,
                "series_sequence": sequence,
                "exchange_timestamp": f"2026-08-10T09:00:0{second}+09:00",
                "local_receive_timestamp": f"2026-08-10T09:00:0{second}.010+09:00",
                "trade_price": 10_000 + sequence,
                "trade_qty": 10,
                "best_bid": 9_990,
                "best_ask": 10_010,
                "quote_age_ms": 10,
                "metric_contract_id": (
                    "scalp_micro_reversion_market_stream_contract_v1"
                ),
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "trading_runtime_effect": False,
            }
        )
    stream.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    reference = {
        "schema": "scalp_micro_reversion_path_event_reference_v2",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "capture_started_at": "2026-08-10T09:00:01+09:00",
        "capture_ended_at": "2026-08-10T09:00:02+09:00",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }

    points = load_p2_points_from_canonical_stream((stream,), reference=reference)

    assert [point.source_sequence for point in points] == [2, 3]
    assert [point.trade_price for point in points] == [10_002, 10_003]


def test_canonical_stream_loader_reads_post_session_gzip(tmp_path: Path) -> None:
    stream = tmp_path / "market_stream.jsonl.gz"
    row = {
        "schema": "scalp_micro_reversion_market_stream_point_v1",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "source_sequence": 1,
        "series_sequence": 1,
        "exchange_timestamp": "2026-08-10T09:00:01+09:00",
        "local_receive_timestamp": "2026-08-10T09:00:01.010+09:00",
        "trade_price": 10_001,
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v1",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }
    with gzip.open(stream, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    reference = {
        "schema": "scalp_micro_reversion_path_event_reference_v2",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "capture_started_at": "2026-08-10T09:00:00+09:00",
        "capture_ended_at": "2026-08-10T09:00:02+09:00",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }

    points = load_p2_points_from_canonical_stream((stream,), reference=reference)

    assert [point.source_sequence for point in points] == [1]


def _policy(**overrides) -> P2ReplayPolicy:
    values = {
        "policy_id": "p2-synthetic-golden-1",
        "policy_version": "frozen-v1",
        "entry_policy": EntryPolicy.PASSIVE_EVENT_BID,
        "exit_policy": ExitPolicy.PARTIAL_TP_RUNNER,
        "fill_bound": FillBound.LOWER_TRADE_THROUGH,
        "entry_ttl_ms": 2_000,
        "holding_ttl_ms": 5_000,
        "take_profit_bps": 20,
        "stop_loss_bps": 30,
        "all_in_cost_bps": 5,
        "target_quantity": 10,
        "partial_take_profit_fraction": 0.5,
        "runner_max_ttl_ms": 3_000,
        "runner_trailing_bps": 20,
        "runner_exit_trigger": "TRAILING_OR_TTL",
    }
    values.update(overrides)
    return P2ReplayPolicy(**values)


def _point(offset: int, sequence: int, **overrides) -> P2ReplayPoint:
    values = {
        "exchange_timestamp_ms": 1_000_000 + offset,
        "local_receive_timestamp_ms": 1_000_010 + offset,
        "source_sequence": sequence,
        "trade_price": 99.9,
        "trade_qty": 5,
        "best_bid": 99.8,
        "best_ask": 100.0,
        "quote_age_ms": 10,
    }
    values.update(overrides)
    return P2ReplayPoint(**values)


def test_lower_bound_represents_partial_entry_and_partial_take_profit() -> None:
    result = replay_path(
        (
            _point(100, 2, trade_price=99.9, trade_qty=4),
            _point(200, 3, trade_price=99.8, trade_qty=2),
            _point(500, 4, trade_price=100.3, low_price=100.1, high_price=100.3),
            _point(900, 5, trade_price=99.6, low_price=99.6, high_price=99.7),
        ),
        policy=_policy(entry_ttl_ms=300),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
        event_bid_price=100.0,
        event_bid_quote_age_ms=10,
    )

    assert result.filled_quantity == 4
    assert result.fill_fraction == 0.4
    assert result.partial_fill_observed is True
    assert result.partial_take_profit_observed is True
    assert result.terminal_reason is ReplayTerminalReason.PARTIAL_TAKE_PROFIT_THEN_STOP
    assert result.unresolved_quantity == 0
    assert result.as_dict()["selection_authority"] is False
    assert result.as_dict()["actual_order_submitted"] is False


def test_same_timestamp_crossing_can_fail_closed_as_ambiguous() -> None:
    result = replay_path(
        (
            _point(100, 2, trade_price=99.9, trade_qty=10),
            _point(
                200,
                3,
                trade_price=100,
                low_price=99.6,
                high_price=100.3,
            ),
        ),
        policy=_policy(same_timestamp_policy=SameTimestampPolicy.MARK_AMBIGUOUS),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
        event_bid_price=100.0,
        event_bid_quote_age_ms=10,
    )

    assert result.terminal_reason is ReplayTerminalReason.AMBIGUOUS_SAME_TIMESTAMP
    assert result.ambiguity_observed is True
    assert result.net_return_bps is None


def test_golden_path_is_deterministic_and_uses_separate_ttls() -> None:
    path = (
        _point(100, 2, trade_price=99.9, trade_qty=10),
        _point(
            2_500,
            3,
            trade_price=100.3,
            trade_qty=10,
            low_price=100.2,
            high_price=100.3,
        ),
    )
    result = replay_path(
        path,
        policy=_policy(
            exit_policy=ExitPolicy.SINGLE_TP,
            partial_take_profit_fraction=1.0,
            runner_max_ttl_ms=None,
            runner_trailing_bps=None,
            runner_exit_trigger=None,
        ),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
        event_bid_price=100.0,
        event_bid_quote_age_ms=10,
    )

    expected = {
        "filled_quantity": 10,
        "fill_fraction": 1.0,
        "average_entry_price": 100.0,
        "average_exit_price": 100.2,
        "gross_return_bps": 20.0,
        "net_return_bps": 15.0,
        "terminal_reason": "TAKE_PROFIT",
        "selection_authority": False,
        "p2_runtime_effect": False,
    }
    actual = result.as_dict()
    assert {key: actual[key] for key in expected} == expected
    assert actual["policy_contract"]["entry_order_ttl_ms"] == 2_000
    assert actual["policy_contract"]["position_holding_ttl_ms"] == 5_000
    assert actual["policy_contract"]["cost_model_version"] == "all-in-cost-v1"


def test_entry_ttl_expiry_does_not_use_late_touch() -> None:
    result = replay_path(
        (_point(2_001, 2, trade_price=99.0, trade_qty=10),),
        policy=_policy(),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
        event_bid_price=100.0,
        event_bid_quote_age_ms=10,
    )

    assert result.terminal_reason is ReplayTerminalReason.NO_ENTRY_FILL


def test_lower_bound_does_not_treat_ask_only_touch_as_tp_fill() -> None:
    result = replay_path(
        (
            _point(100, 2, trade_price=99.9, trade_qty=10),
            _point(
                200,
                3,
                trade_price=100.0,
                trade_qty=0,
                best_bid=100.0,
                best_ask=100.5,
            ),
        ),
        policy=_policy(
            exit_policy=ExitPolicy.SINGLE_TP,
            partial_take_profit_fraction=1.0,
            runner_max_ttl_ms=None,
            runner_trailing_bps=None,
            runner_exit_trigger=None,
        ),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
        event_bid_price=100.0,
        event_bid_quote_age_ms=10,
    )

    assert result.terminal_reason is ReplayTerminalReason.PATH_ENDED
    assert result.average_exit_price is None
    assert result.net_return_bps is None
    assert result.unresolved_quantity == 10


def test_upper_entry_bound_requires_trade_low_or_crossed_ask() -> None:
    result = replay_path(
        (
            _point(
                100,
                2,
                trade_price=None,
                trade_qty=None,
                low_price=None,
                best_bid=99.0,
                best_ask=101.0,
            ),
        ),
        policy=_policy(fill_bound=FillBound.UPPER_TOUCH),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
        event_bid_price=100.0,
        event_bid_quote_age_ms=10,
    )

    assert result.terminal_reason is ReplayTerminalReason.NO_ENTRY_FILL


def test_marketable_entry_skips_stale_ask() -> None:
    result = replay_path(
        (
            _point(100, 2, best_ask=100.0, quote_age_ms=3_000),
            _point(200, 3, best_ask=100.1, quote_age_ms=10),
        ),
        policy=_policy(
            entry_policy=EntryPolicy.MARKETABLE_NEXT_ASK,
            exit_policy=ExitPolicy.SINGLE_TP,
            partial_take_profit_fraction=1.0,
            runner_max_ttl_ms=None,
            runner_trailing_bps=None,
            runner_exit_trigger=None,
        ),
        decision_watermark_timestamp_ms=1_000_000,
        decision_watermark_local_receive_timestamp_ms=1_000_010,
        decision_watermark_source_sequence=1,
    )

    assert result.entry_filled_at_ms == 1_000_200
    assert result.average_entry_price == 100.1
