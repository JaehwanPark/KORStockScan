from src.trading.market.market_data_cache import MarketDataCache


def test_market_data_cache_resets_jitter_window_after_large_stale_gap():
    cache = MarketDataCache(stale_after_ms=700)
    base_ts = 1_000.0

    cache.update("005930", last_price=10_000, best_ask=10_010, best_bid=9_990, received_at=base_ts)
    cache.update("005930", last_price=10_010, best_ask=10_020, best_bid=10_000, received_at=base_ts + 0.15)
    cache.update("005930", last_price=10_020, best_ask=10_030, best_bid=10_010, received_at=base_ts + 3.50)
    cache.update("005930", last_price=10_030, best_ask=10_040, best_bid=10_020, received_at=base_ts + 3.66)

    health = cache.get_quote_health("005930")

    assert health.ws_jitter_ms <= 1
    assert health.last_price == 10_030


def test_market_data_cache_ignores_duplicate_or_regressed_timestamps():
    cache = MarketDataCache(stale_after_ms=700)
    base_ts = 2_000.0

    cache.update("005930", last_price=10_000, best_ask=10_010, best_bid=9_990, received_at=base_ts)
    cache.update("005930", last_price=10_000, best_ask=10_010, best_bid=9_990, received_at=base_ts + 0.12)
    cache.update("005930", last_price=10_010, best_ask=10_020, best_bid=10_000, received_at=base_ts + 0.12)
    cache.update("005930", last_price=10_020, best_ask=10_030, best_bid=10_010, received_at=base_ts + 0.10)
    cache.update("005930", last_price=10_030, best_ask=10_040, best_bid=10_020, received_at=base_ts + 0.25)

    health = cache.get_quote_health("005930")

    assert 0 <= health.ws_jitter_ms <= 15
    assert health.last_price == 10_030


def test_market_data_cache_preserves_normal_jitter_signal():
    cache = MarketDataCache(stale_after_ms=700)
    base_ts = 3_000.0

    cache.update("005930", last_price=10_000, best_ask=10_010, best_bid=9_990, received_at=base_ts)
    cache.update("005930", last_price=10_010, best_ask=10_020, best_bid=10_000, received_at=base_ts + 0.10)
    cache.update("005930", last_price=10_020, best_ask=10_030, best_bid=10_010, received_at=base_ts + 0.24)
    cache.update("005930", last_price=10_030, best_ask=10_040, best_bid=10_020, received_at=base_ts + 0.33)

    health = cache.get_quote_health("005930")

    assert 35 <= health.ws_jitter_ms <= 55
    assert health.best_ask == 10_040
