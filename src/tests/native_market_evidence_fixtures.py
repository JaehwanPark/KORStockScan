"""Synthetic Main packet fixtures without episode research imports."""


def _depth_row(
    symbol: str,
    at: str,
    *,
    venue: str = "KRX",
    session: str = "KRX_REGULAR",
    sequence_epoch: int = 1,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_depth_point_v1",
        "symbol": symbol,
        "venue": venue,
        "session_bucket": session,
        "exchange_timestamp": at,
        "local_receive_timestamp": at,
        "source_sequence": 1,
        "series_sequence": 1,
        "sequence_epoch": sequence_epoch,
        "item": (
            f"{symbol}_AL"
            if venue == "SOR"
            else f"{symbol}_NX" if venue == "NXT" else symbol
        ),
        "orderbook_time_raw": "100000",
        "bid_depth": 1000,
        "ask_depth": 800,
        "best_bid": 9950,
        "best_ask": 10000,
        "best_bid_qty": 1000,
        "best_ask_qty": 800,
        "bid_levels": [[1, 9950, 1000]],
        "ask_levels": [[1, 10000, 800]],
        "route_depth_totals": {
            "combined": {"bid": 1000, "ask": 800},
        },
        "realtime_type": "0D",
        "metric_contract_id": "scalp_micro_reversion_market_depth_contract_v1",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }

def _micro_row(
    symbol: str,
    at: str,
    price: int,
    *,
    eligible: bool = True,
    venue: str = "SOR",
    session: str | None = None,
    sequence_epoch: int = 1,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_stream_point_v3",
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v3",
        "symbol": symbol,
        "venue": venue,
        "session_bucket": session or f"{venue}_REGULAR",
        "exchange_timestamp": at,
        "local_receive_timestamp": at,
        "source_sequence": 1,
        "series_sequence": 1,
        "sequence_epoch": sequence_epoch,
        "realtime_type": "0B",
        "trade_price": price,
        "trade_qty": 1,
        "best_bid": price - 50,
        "best_ask": price,
        "path_consumer_eligible": eligible,
        "path_order_status": "accept" if eligible else "source_sequence_regression",
        "exchange_timestamp_regression_ms": 0,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }
