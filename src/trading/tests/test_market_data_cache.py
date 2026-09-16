from src.trading.market.market_data_cache import MarketDataCache, QuietTapeState


def test_quiet_tape_requires_distinct_episodes_not_repeated_getters():
    state = QuietTapeState()
    state.observe(kind="0D", now=100.0, sequence=1)
    state.observe(kind="0B", now=100.0, sequence=1, volume=1)
    for now in range(101, 111):
        state.observe(kind="0D", now=float(now), sequence=now)
    for _ in range(100):
        assert state.facts(now=110.0)["quiet_episode_count"] == 1
    state.observe(kind="0B", now=110.0, sequence=2, volume=2)
    for now in range(111, 121):
        state.observe(kind="0D", now=float(now), sequence=now)
    assert state.facts(now=120.0)["quiet_episode_count"] == 2
    state.observe(kind="0B", now=120.0, sequence=3, volume=3)
    for now in range(121, 131):
        state.observe(kind="0D", now=float(now), sequence=now)
    assert (
        state.facts(now=130.0)["trade_activity_state"] == "REPEATED_QUIET_TAPE_OBSERVED"
    )


def test_quiet_tape_long_gap_is_one_episode_and_broken_quote_resets():
    state = QuietTapeState()
    state.observe(kind="0D", now=100.0, sequence=1)
    state.observe(kind="0B", now=100.0, sequence=1, volume=1)
    for now in range(101, 131):
        state.observe(kind="0D", now=float(now), sequence=now)
    assert state.facts(now=130.0)["quiet_episode_count"] == 1
    state.observe(kind="0D", now=140.0, sequence=140)
    assert state.facts(now=140.0)["trade_activity_state"] == "OBSERVATION_UNPROVEN"


def test_quiet_tape_duplicate_trade_does_not_close_episode():
    state = QuietTapeState()
    state.observe(kind="0D", now=100.0, sequence=1)
    state.observe(kind="0B", now=100.0, sequence=1, volume=1)
    for now in range(101, 111):
        state.observe(kind="0D", now=float(now), sequence=now)
    state.observe(kind="0B", now=110.0, sequence=2, volume=1)
    assert state.facts(now=110.0)["quiet_episode_count"] == 1
    assert state.last_trade == 100.0


def test_late_missing_or_future_provider_trade_does_not_recover_quiet_state():
    for event_at in (0.0, 80.0, 111.0):
        state = QuietTapeState()
        state.observe(kind="0D", now=100.0, sequence=1)
        state.observe(kind="0B", now=100.0, sequence=1, volume=1)
        for now in range(101, 111):
            state.observe(kind="0D", now=float(now), sequence=now)
        state.observe(
            kind="0B", now=110.0, sequence=2, volume=2, provider_event_at=event_at
        )
        assert state.facts(now=110.0)["trade_activity_state"] == "OBSERVATION_UNPROVEN"


def test_continuous_activity_resets_repeated_quiet_history():
    state = QuietTapeState(closed_episodes=2)
    for now in range(100, 112):
        state.observe(kind="0D", now=float(now), sequence=now)
        state.observe(kind="0B", now=float(now), sequence=now, volume=now)
    assert state.facts(now=111.0)["quiet_episode_count"] == 0


def test_market_data_cache_resets_jitter_window_after_large_stale_gap():
    cache = MarketDataCache(stale_after_ms=700)
    base_ts = 1_000.0

    cache.update(
        "005930",
        last_price=10_000,
        best_ask=10_010,
        best_bid=9_990,
        received_at=base_ts,
    )
    cache.update(
        "005930",
        last_price=10_010,
        best_ask=10_020,
        best_bid=10_000,
        received_at=base_ts + 0.15,
    )
    cache.update(
        "005930",
        last_price=10_020,
        best_ask=10_030,
        best_bid=10_010,
        received_at=base_ts + 3.50,
    )
    cache.update(
        "005930",
        last_price=10_030,
        best_ask=10_040,
        best_bid=10_020,
        received_at=base_ts + 3.66,
    )

    health = cache.get_quote_health("005930")

    assert health.ws_jitter_ms <= 1
    assert health.last_price == 10_030


def test_market_data_cache_ignores_duplicate_or_regressed_timestamps():
    cache = MarketDataCache(stale_after_ms=700)
    base_ts = 2_000.0

    cache.update(
        "005930",
        last_price=10_000,
        best_ask=10_010,
        best_bid=9_990,
        received_at=base_ts,
    )
    cache.update(
        "005930",
        last_price=10_000,
        best_ask=10_010,
        best_bid=9_990,
        received_at=base_ts + 0.12,
    )
    cache.update(
        "005930",
        last_price=10_010,
        best_ask=10_020,
        best_bid=10_000,
        received_at=base_ts + 0.12,
    )
    cache.update(
        "005930",
        last_price=10_020,
        best_ask=10_030,
        best_bid=10_010,
        received_at=base_ts + 0.10,
    )
    cache.update(
        "005930",
        last_price=10_030,
        best_ask=10_040,
        best_bid=10_020,
        received_at=base_ts + 0.25,
    )

    health = cache.get_quote_health("005930")

    assert 0 <= health.ws_jitter_ms <= 15
    assert health.last_price == 10_030


def test_market_data_cache_preserves_normal_jitter_signal():
    cache = MarketDataCache(stale_after_ms=700)
    base_ts = 3_000.0

    cache.update(
        "005930",
        last_price=10_000,
        best_ask=10_010,
        best_bid=9_990,
        received_at=base_ts,
    )
    cache.update(
        "005930",
        last_price=10_010,
        best_ask=10_020,
        best_bid=10_000,
        received_at=base_ts + 0.10,
    )
    cache.update(
        "005930",
        last_price=10_020,
        best_ask=10_030,
        best_bid=10_010,
        received_at=base_ts + 0.24,
    )
    cache.update(
        "005930",
        last_price=10_030,
        best_ask=10_040,
        best_bid=10_020,
        received_at=base_ts + 0.33,
    )

    health = cache.get_quote_health("005930")

    assert 35 <= health.ws_jitter_ms <= 55
    assert health.best_ask == 10_040
