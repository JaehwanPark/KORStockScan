from src.trading.market.market_data_cache import MarketDataCache, QuietTapeState


def test_cache_duplicate_identity_cannot_advance_source_clock(monkeypatch):
    monkeypatch.setattr("src.trading.market.market_data_cache.time.time", lambda: 1001.0)
    cache = MarketDataCache()
    cache.update("042660", received_at=1000.0, source_identity=("0D", 10),
                 best_bid=10000, best_ask=10010)
    cache.update("042660", received_at=1000.5, source_identity=("0D", 10),
                 best_bid=10000, best_ask=10010)
    cache.update("042660", received_at="bad", source_identity=("0D", 11))
    cache.update("042660", received_at=1000.5, source_identity=("0D",))
    assert cache.get_quote_health("042660").ws_age_ms == 1000


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


def test_cache_separates_exact_route_epoch_and_does_not_replace_equal_receipt(monkeypatch):
    monkeypatch.setattr("src.trading.market.market_data_cache.time.time", lambda: 1000.5)
    cache = MarketDataCache()
    krx, nxt, recovered = ("005930", "regular", 1), ("005930_NX", "regular", 1), ("005930", "regular", 2)
    cache.update("005930", scope=krx, received_at=1000, best_bid=10000, best_ask=10010)
    cache.update("005930", scope=nxt, received_at=1000.1, best_bid=10100, best_ask=10110)
    for _ in range(100):
        cache.update("005930", scope=krx, received_at=1000, best_bid=10000, best_ask=10010)
    assert cache.get_best_bid("005930", scope=krx) == 10000
    assert cache.get_best_bid("005930", scope=nxt) == 10100
    assert cache.get_quote_health("005930", scope=recovered).quote_stale
    assert cache.get_quote_health("005930", scope=krx).ws_age_ms == 500
    assert cache.get_quote_health("005930", scope=krx).ws_jitter_ms == 0
    cache.update("005930", scope=krx, received_at=1000, best_bid=9990, best_ask=10000)
    assert cache.get_best_bid("005930", scope=krx) == 10000
    assert cache.get_quote_health("005930", scope=krx).quote_stale


def test_cache_rejects_future_submillisecond_freshness_and_accepts_proven_next_sequence(monkeypatch):
    monkeypatch.setattr("src.trading.market.market_data_cache.time.time", lambda: 1000.0)
    cache = MarketDataCache()
    cache.update("005930", received_at=1000.0001, best_bid=10000, best_ask=10010)
    assert cache.get_quote_health("005930").quote_stale
    cache.update("042660", received_at=1000, source_identity=("0D", 1), best_bid=10000, best_ask=10010)
    cache.update("042660", received_at=1000, source_identity=("0D", 2), best_bid=10010, best_ask=10020)
    assert cache.get_best_bid("042660") == 10010
    assert not cache.get_quote_health("042660").quote_stale
    assert cache.get_quote_health("042660").ws_jitter_ms == 0


def test_typed_quote_health_preserves_raw_facts_without_renewal(monkeypatch):
    from src.trading.market.quote_consistency import build_market_data_health

    now = 1000.5
    monkeypatch.setattr("src.trading.market.market_data_cache.time.time", lambda: now)
    scope = ("005930", "krx", "regular", "2")
    cache = MarketDataCache(stale_after_ms=700)
    cache.update("005930", scope=scope, received_at=1000.0,
                 source_identity=("0D", 12), last_price=10000,
                 best_bid=10000, best_ask=10010)
    state = QuietTapeState(last_quote=1000.0, last_trade=990.0, closed_episodes=2)
    binding = {"item": "005930", "market_route": "krx", "effective_venue": "KRX",
               "transport_epoch": 2}
    frame = {"market_data_transport_epoch": 2,
             "last_realtime_type_ts": {"0D": 1000.0},
             "last_realtime_type_item": {"0D": "005930"},
             "realtime_type_snapshots_by_route": {"krx": {
                 "0D": {**binding, "observed_epoch": 1000.0,
                        "best_bid": 10000, "best_ask": 10010},
                 "0B": {**binding, "observed_epoch": 990.0},
                 "_quiet_tape_state": state}},
             "market_data_health": {"quote_receive_age_ms": 0}}
    for _ in range(100):
        health = cache.get_quote_health("005930", scope=scope, source_frame=frame)
        assert health.quote_received_epoch == 1000.0
        assert health.quote_receive_age_ms == 500.0
        assert health.source_scope == scope
        assert health.source_identity == ("0D", 12)
        assert health.ws_jitter_ms == 0
        assert not health.quote_stale
        facts = health.market_data_health["routes"]["krx"]
        assert facts["trade_receive_age_ms"] == 10500.0
        assert facts["quiet_episode_count"] == 3
        assert facts["trade_activity_state"] == "REPEATED_QUIET_TAPE_OBSERVED"
    assert state.closed_episodes == 2
    assert health.to_dict()["market_data_health"] == build_market_data_health(
        frame, now_ts=now, quote_max_age_ms=700)
    now = 1000.8
    assert cache.get_quote_health("005930", scope=scope, source_frame=frame).quote_stale
    assert cache.get_quote_health("005930", scope=("005930_NX",)).quote_received_epoch is None


def test_typed_quote_health_keeps_unknown_and_signed_future_clock(monkeypatch):
    now = 1000.0
    monkeypatch.setattr("src.trading.market.market_data_cache.time.time", lambda: now)
    cache = MarketDataCache()
    cache.update("legacy", best_bid=10000, best_ask=10010)
    legacy = cache.get_quote_health("legacy")
    assert legacy.quote_received_epoch is None
    assert legacy.quote_receive_age_ms is None
    assert legacy.market_data_health is None
    cache.update("original", received_at=now, best_bid=10000, best_ask=10010)
    now -= .1
    future = cache.get_quote_health("original")
    assert future.quote_received_epoch == 1000.0
    assert future.quote_receive_age_ms < 0
    assert future.quote_stale
