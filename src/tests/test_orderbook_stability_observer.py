from src.trading.entry.orderbook_stability_observer import OrderbookStabilityObserver


def test_flicker_rate_counts_reversion_within_10s():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=100.0)
    observer.record_quote("123456", best_bid=10_010, best_ask=10_020, ts=101.0)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=102.0)

    snapshot = observer.snapshot("123456", now=102.0)

    assert snapshot["fr_10s"] == 2
    assert snapshot["sample_quote_count"] == 3


def test_quote_age_percentiles_are_matched_to_previous_quote():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=100.0)
    observer.record_trade("123456", price=10_010, ts=100.1)
    observer.record_trade("123456", price=10_000, ts=100.5)

    snapshot = observer.snapshot("123456", now=100.5)

    assert snapshot["quote_age_p50_ms"] == 300.0
    assert snapshot["quote_age_p90_ms"] == 460.0
    assert snapshot["sample_trade_count"] == 2


def test_print_quote_alignment_accepts_spread_and_mid_plus_one_tick():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_050, ts=100.0)
    observer.record_trade("123456", price=10_020, ts=100.1)
    observer.record_trade("123456", price=10_035, ts=100.2)
    observer.record_trade("123456", price=10_100, ts=100.3)

    snapshot = observer.snapshot("123456", now=100.3)

    assert snapshot["print_quote_alignment"] == 0.666667
    assert snapshot["unstable_quote_observed"] is True
    assert "print_quote_alignment" in snapshot["unstable_reasons"]


def test_window_prunes_old_quote_trade_and_flicker_events():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=100.0)
    observer.record_quote("123456", best_bid=10_010, best_ask=10_020, ts=101.0)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=102.0)
    observer.record_trade("123456", price=10_010, ts=102.0)

    snapshot = observer.snapshot("123456", now=113.0)

    assert snapshot["fr_10s"] == 0
    assert snapshot["sample_quote_count"] == 0
    assert snapshot["sample_trade_count"] == 0


def test_orderbook_micro_qi_ofi_and_depth_normalization():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=100,
        best_ask_qty=100,
        bid_depth_l=500,
        ask_depth_l=500,
        ts=100.0,
    )
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=140,
        best_ask_qty=80,
        bid_depth_l=620,
        ask_depth_l=420,
        ts=101.0,
    )

    micro = observer.snapshot("123456", now=101.0)["orderbook_micro"]

    assert micro["ready"] is False
    assert micro["reason"] == "insufficient_samples"
    assert micro["qi"] == 0.636364
    assert micro["qi_ewma"] == 0.540909
    assert micro["ofi_instant"] == 60.0
    assert micro["ofi_ewma"] == 18.0
    assert micro["ofi_norm"] > 0
    assert micro["depth_ewma"] == 1012.0
    assert micro["captured_at_ms"] == 101000
    assert micro["observer_healthy"] is False
    assert micro["observer_missing_reason"] == "missing_trade"
    assert micro["micro_window_sec"] == 60.0
    assert micro["micro_z_min_samples"] == 20
    assert micro["micro_lambda"] == 0.3
    assert micro["ofi_threshold_source"] == "global"
    assert micro["ofi_bull_threshold"] == 1.2
    assert micro["ofi_bear_threshold"] == -1.0
    assert micro["qi_bull_threshold"] == 0.55
    assert micro["qi_bear_threshold"] == 0.48
    assert micro["ofi_calibration_warning"] == "insufficient_symbol_samples"


def test_orderbook_micro_bucket_key_uses_explicit_not_available_provenance():
    observer = OrderbookStabilityObserver(window_sec=10, micro_z_min_samples=3)
    observer.record_quote(
        "123456",
        best_bid=0,
        best_ask=0,
        best_bid_qty=100,
        best_ask_qty=100,
        bid_depth_l=0,
        ask_depth_l=0,
        ts=100.0,
    )

    micro = observer.snapshot("123456", now=100.0)["orderbook_micro"]

    assert "unknown" not in micro["ofi_bucket_key"]
    assert micro["ofi_bucket_key"] == (
        "spread=not_available_no_bid_ask|price=not_available_no_price|"
        "depth=not_available_no_depth|sample=insufficient"
    )
    assert micro["ofi_calibration_bucket"] == micro["ofi_bucket_key"]
    assert micro["ofi_threshold_bucket_key"] == micro["ofi_bucket_key"]


def test_orderbook_micro_becomes_ready_after_min_samples_and_prunes_window():
    observer = OrderbookStabilityObserver(
        window_sec=10, micro_window_sec=2, micro_z_min_samples=3
    )
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=100,
        best_ask_qty=100,
        bid_depth_l=500,
        ask_depth_l=500,
        ts=100.0,
    )
    for offset in range(1, 4):
        observer.record_quote(
            "123456",
            best_bid=10_000,
            best_ask=10_010,
            best_bid_qty=100 + offset,
            best_ask_qty=100,
            bid_depth_l=500 + offset,
            ask_depth_l=500,
            ts=100.0 + offset * 0.5,
        )

    ready_micro = observer.snapshot("123456", now=101.5)["orderbook_micro"]
    assert ready_micro["ready"] is True
    assert ready_micro["reason"] == "ready"
    assert ready_micro["micro_state"] in {"bullish", "neutral", "bearish"}
    assert ready_micro["ofi_z"] is not None

    pruned_micro = observer.snapshot("123456", now=104.0)["orderbook_micro"]
    assert pruned_micro["sample_quote_count"] == 0
    assert pruned_micro["ready"] is False


def test_orderbook_micro_wide_windows_retain_report_only_flow_context():
    observer = OrderbookStabilityObserver(
        window_sec=10,
        micro_window_sec=2,
        micro_z_min_samples=3,
        wide_micro_windows_sec=(3, 5, 10),
    )
    for offset in range(8):
        observer.record_quote(
            "123456",
            best_bid=10_000,
            best_ask=10_010,
            best_bid_qty=100 + offset * 30,
            best_ask_qty=100,
            bid_depth_l=1000 + offset * 30,
            ask_depth_l=1000,
            ts=100.0 + offset,
        )

    micro = observer.snapshot("123456", now=107.0)["orderbook_micro"]

    assert micro["sample_quote_count"] == 3
    assert micro["wide_3s_sample_count"] == 4
    assert micro["wide_5s_sample_count"] == 6
    assert micro["wide_10s_sample_count"] == 8
    assert micro["wide_10s_ready_sample_count"] >= micro["wide_3s_ready_sample_count"]
    assert micro["wide_10s_state"] in {
        "insufficient",
        "persistent_bullish",
        "persistent_bearish",
        "mixed",
        "neutral",
    }
    assert micro["wide_windows"]["10s"]["window_sec"] == 10


def test_orderbook_micro_observer_health_fields_with_quote_and_trade():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=100,
        best_ask_qty=100,
        ts=100.0,
    )
    observer.record_trade("123456", price=10_010, ts=100.2)

    snapshot = observer.snapshot("123456", now=100.5)
    micro = snapshot["orderbook_micro"]

    assert snapshot["observer_healthy"] is True
    assert snapshot["observer_missing_reason"] == "ok"
    assert snapshot["observer_last_quote_age_ms"] == 500.0
    assert snapshot["observer_last_trade_age_ms"] == 300.0
    assert micro["observer_healthy"] is True
    assert micro["observer_missing_reason"] == "ok"


def test_orderbook_micro_bucket_manifest_can_override_thresholds():
    manifest = {
        "enabled": True,
        "manifest_id": "test_manifest",
        "version": "v1",
        "min_bucket_samples": 0,
        "bucket_thresholds": {
            "spread=tight|price=mid|depth=normal|sample=normal": {
                "ofi_bull_threshold": 999.0,
                "ofi_bear_threshold": 999.0,
                "qi_bull_threshold": 0.99,
                "qi_bear_threshold": 0.99,
                "bucket_sample_count": 100,
            }
        },
    }
    observer = OrderbookStabilityObserver(
        window_sec=10,
        micro_z_min_samples=3,
        bucket_calibration_enabled=True,
        threshold_manifest=manifest,
    )
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=100,
        best_ask_qty=100,
        bid_depth_l=1000,
        ask_depth_l=1000,
        ts=100.0,
    )
    for offset in range(1, 4):
        observer.record_quote(
            "123456",
            best_bid=10_000,
            best_ask=10_010,
            best_bid_qty=100 + offset * 50,
            best_ask_qty=100,
            bid_depth_l=1200,
            ask_depth_l=1000,
            ts=100.0 + offset,
        )

    micro = observer.snapshot("123456", now=104.0)["orderbook_micro"]

    assert micro["ready"] is True
    assert micro["ofi_threshold_source"] == "bucket"
    assert micro["ofi_threshold_manifest_id"] == "test_manifest"
    assert micro["ofi_threshold_manifest_version"] == "v1"
    assert (
        micro["ofi_threshold_bucket_key"]
        == "spread=tight|price=mid|depth=normal|sample=normal"
    )
    assert micro["ofi_bear_threshold"] == 999.0
    assert micro["micro_state"] == "bearish"


def test_orderbook_micro_bucket_manifest_falls_back_when_bucket_missing():
    observer = OrderbookStabilityObserver(
        window_sec=10,
        micro_z_min_samples=3,
        bucket_calibration_enabled=True,
        threshold_manifest={"enabled": True, "bucket_thresholds": {}},
    )
    for offset in range(4):
        observer.record_quote(
            "123456",
            best_bid=10_000,
            best_ask=10_010,
            best_bid_qty=100 + offset,
            best_ask_qty=100,
            bid_depth_l=1000,
            ask_depth_l=1000,
            ts=100.0 + offset,
        )

    micro = observer.snapshot("123456", now=104.0)["orderbook_micro"]

    assert micro["ofi_threshold_source"] == "fallback"
    assert micro["ofi_threshold_fallback_reason"] == "bucket_missing"
    assert micro["ofi_calibration_warning"] == "bucket_missing"


def test_orderbook_micro_bucket_manifest_falls_back_when_symbol_samples_low():
    manifest = {
        "enabled": True,
        "min_symbol_samples": 10,
        "bucket_thresholds": {
            "spread=tight|price=mid|depth=normal|sample=normal": {
                "ofi_bull_threshold": 999.0,
                "ofi_bear_threshold": 999.0,
                "qi_bull_threshold": 0.99,
                "qi_bear_threshold": 0.99,
                "bucket_sample_count": 100,
            }
        },
    }
    observer = OrderbookStabilityObserver(
        window_sec=10,
        micro_z_min_samples=3,
        bucket_calibration_enabled=True,
        threshold_manifest=manifest,
    )
    for offset in range(4):
        observer.record_quote(
            "123456",
            best_bid=10_000,
            best_ask=10_010,
            best_bid_qty=100 + offset * 50,
            best_ask_qty=100,
            bid_depth_l=1000,
            ask_depth_l=1000,
            ts=100.0 + offset,
        )

    micro = observer.snapshot("123456", now=104.0)["orderbook_micro"]

    assert micro["ready"] is True
    assert micro["ofi_threshold_source"] == "fallback"
    assert micro["ofi_threshold_fallback_reason"] == "insufficient_symbol_samples"
    assert micro["ofi_calibration_warning"] == "insufficient_symbol_samples"
