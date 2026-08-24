from src.engine import kiwoom_sniper_v2 as sniper
from src.engine import sniper_execution_receipts as receipts


def test_scalp_revive_sets_quote_barrier_before_rewatch(monkeypatch):
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(receipts, "move_orders_to_terminal", lambda stock, reason: None)
    stock = {
        "id": 7,
        "status": "HOLDING",
        "buy_price": 10000,
        "buy_qty": 3,
        "rising_missed_scout_upgraded": True,
        "rising_missed_scout_position_cycle_active": True,
    }

    receipts._apply_scalp_revive_memory_state(
        target_stock=stock,
        code="002990",
        new_watch_id=8,
        revived_position_tag="scalping_default",
        revived_at_ts=1000.0,
    )

    assert stock["status"] == "WATCHING"
    assert stock["_scalp_revive_min_quote_ts"] == 1000.0
    assert "rising_missed_scout_upgraded" not in stock
    assert "rising_missed_scout_position_cycle_active" not in stock


def test_revive_barrier_discards_pre_sell_ws_then_accepts_new_ws_snapshot():
    stock = {"_scalp_revive_min_quote_ts": 1000.0}

    stale_snapshot, stale_fields = sniper._discard_pre_revive_scanner_snapshot(
        stock,
        {"curr": 12820, "last_ws_update_ts": 999.9},
        now_ts=1001.0,
    )

    assert stale_snapshot == {}
    assert stale_fields["scalp_revive_quote_barrier_state"] == "pre_revive_ws_discarded"
    assert stock["_scalp_revive_min_quote_ts"] == 1000.0

    fresh_snapshot, fresh_fields = sniper._discard_pre_revive_scanner_snapshot(
        stock,
        {"curr": 13950, "last_ws_update_ts": 1000.1},
        now_ts=1001.0,
    )

    assert fresh_snapshot["curr"] == 13950
    assert fresh_fields["scalp_revive_quote_barrier_state"] == "fresh_ws_after_revive"
    assert "_scalp_revive_min_quote_ts" not in stock


def test_revive_barrier_allows_current_rest_price_without_promoting_or_clearing_ws():
    stock = {"_scalp_revive_min_quote_ts": 1000.0}

    snapshot, fields = sniper._discard_pre_revive_scanner_snapshot(
        stock,
        {
            "curr": 13950,
            "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback",
            "ws_snapshot_recovery_epoch": 1000.1,
        },
        now_ts=1001.0,
    )

    assert snapshot["curr"] == 13950
    assert (
        fields["scalp_revive_quote_barrier_state"]
        == "fresh_rest_after_revive_ws_pending"
    )
    assert fields["scalp_revive_quote_barrier_ws_pending"] is True
    assert stock["_scalp_revive_min_quote_ts"] == 1000.0


def test_revived_watch_registers_new_generation_from_first_fresh_ws(monkeypatch):
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_mode",
        "async_v1",
        raising=False,
    )
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_venues",
        frozenset({"KRX"}),
        raising=False,
    )
    monkeypatch.setattr(
        sniper,
        "_emit_scanner_scheduler_event",
        lambda **kwargs: None,
    )
    scheduler = sniper.ScannerRuntimeScheduler(max_active=16)
    old = scheduler.register_generation(
        code="002990",
        promotion_id="PROMO-OLD",
        record_id=7,
        venue="KRX",
        promotion_epoch=990.0,
        attach_epoch=991.0,
        observed_price=12_800,
        source_signature="VALUE_TOP",
    )
    stock = {
        "id": 8,
        "code": "002990",
        "name": "TEST",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "effective_venue": "KRX",
        "venue": "KRX",
        "scanner_generation_id": old.item.generation.generation_id,
        "scanner_promotion_id": "PROMO-OLD",
        "scanner_promotion_emitted_epoch": 990.0,
        "price_delta_since_first_seen_pct": 3.5,
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 57.0,
        "rising_missed_one_share_entry_forced": True,
        "forced_entry_reason": "rising_missed_one_share_entry",
        "forced_entry_qty": 43,
    }
    ws_data = {
        "curr": 13_950,
        "last_ws_update_ts": 1000.1,
        "last_realtime_type_ts": {"0B": 1000.1},
    }

    generation = sniper._scanner_scheduler_register_revived_watch_on_fresh_ws(
        scheduler,
        stock,
        ws_data,
        revive_quote_barrier_fields={
            "scalp_revive_quote_barrier_state": "fresh_ws_after_revive",
            "scalp_revive_quote_barrier_min_ts": 1000.0,
            "scalp_revive_quote_barrier_received_ts": 1000.1,
        },
        now_epoch=1000.2,
    )

    assert generation is not None
    assert stock["scanner_generation_id"] != old.item.generation.generation_id
    assert stock["scanner_promotion_id"].startswith("SCALPREVIVE-002990-8-")
    assert stock["scanner_promotion_reason"] == "post_sell_revive_fresh_ws"
    assert stock["current_price_observed"] == 13_950
    assert stock["price_delta_since_first_seen_pct"] == 0.0
    assert "last_watching_ai_action" not in stock
    assert "last_watching_ai_score" not in stock
    assert "rising_missed_one_share_entry_forced" not in stock
    assert "forced_entry_reason" not in stock
    assert "forced_entry_qty" not in stock
    assert (
        sniper._scanner_scheduler_pre_recovery_block_reason(
            stock,
            scheduler=scheduler,
        )
        == ""
    )


def test_revived_watch_does_not_register_from_rest_only_recovery(monkeypatch):
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_mode",
        "async_v1",
        raising=False,
    )
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_venues",
        frozenset({"KRX"}),
        raising=False,
    )
    scheduler = sniper.ScannerRuntimeScheduler(max_active=16)
    stock = {
        "id": 8,
        "code": "002990",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "effective_venue": "KRX",
    }

    generation = sniper._scanner_scheduler_register_revived_watch_on_fresh_ws(
        scheduler,
        stock,
        {
            "curr": 13_950,
            "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback",
            "ws_snapshot_recovery_epoch": 1000.1,
        },
        revive_quote_barrier_fields={
            "scalp_revive_quote_barrier_state": ("fresh_rest_after_revive_ws_pending"),
            "scalp_revive_quote_barrier_min_ts": 1000.0,
        },
        now_epoch=1000.2,
    )

    assert generation is None
    assert scheduler.current_generation("002990") is None


def test_revived_watch_legacy_route_does_not_rearm_quote_barrier(monkeypatch):
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_mode",
        "legacy",
        raising=False,
    )
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_venues",
        frozenset({"KRX"}),
        raising=False,
    )
    monkeypatch.setattr(
        sniper,
        "_emit_scanner_scheduler_event",
        lambda **kwargs: None,
    )
    scheduler = sniper.ScannerRuntimeScheduler(max_active=16)
    stock = {
        "id": 8,
        "code": "002990",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "effective_venue": "KRX",
        "venue": "KRX",
        "_scalp_revive_min_quote_ts": 1000.0,
        "last_watching_ai_action": "WAIT",
    }
    ws_data, barrier_fields = sniper._discard_pre_revive_scanner_snapshot(
        stock,
        {
            "curr": 13_950,
            "last_ws_update_ts": 1000.1,
            "last_realtime_type_ts": {"0B": 1000.1},
        },
        now_ts=1000.2,
    )

    generation = sniper._scanner_scheduler_register_revived_watch_on_fresh_ws(
        scheduler,
        stock,
        ws_data,
        revive_quote_barrier_fields=barrier_fields,
        now_epoch=1000.2,
    )

    assert generation is None
    assert scheduler.current_generation("002990") is None
    assert "_scalp_revive_min_quote_ts" not in stock
    assert stock["scanner_promotion_reason"] == "post_sell_revive_fresh_ws"
    assert stock["current_price_observed"] == 13_950
    assert "last_watching_ai_action" not in stock
    assert stock["_scanner_scheduler_registration_reason"] == (
        "venue_not_selected_legacy_route"
    )


def test_revived_watch_rearms_quote_barrier_when_scheduler_attach_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_mode",
        "async_v1",
        raising=False,
    )
    monkeypatch.setattr(
        sniper.run_sniper,
        "scanner_scheduler_venues",
        frozenset({"KRX"}),
        raising=False,
    )
    monkeypatch.setattr(
        sniper,
        "_emit_scanner_scheduler_event",
        lambda **kwargs: None,
    )
    scheduler = sniper.ScannerRuntimeScheduler(max_active=1)
    scheduler.register_generation(
        code="111111",
        promotion_id="PROMO-CAPACITY",
        record_id=1,
        venue="KRX",
        promotion_epoch=990.0,
        attach_epoch=991.0,
        observed_price=10_000,
        source_signature="VALUE_TOP",
    )
    stock = {
        "id": 8,
        "code": "002990",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "effective_venue": "KRX",
        "venue": "KRX",
    }

    generation = sniper._scanner_scheduler_register_revived_watch_on_fresh_ws(
        scheduler,
        stock,
        {"curr": 13_950, "last_ws_update_ts": 1000.1},
        revive_quote_barrier_fields={
            "scalp_revive_quote_barrier_state": "fresh_ws_after_revive",
            "scalp_revive_quote_barrier_min_ts": 1000.0,
            "scalp_revive_quote_barrier_received_ts": 1000.1,
        },
        now_epoch=1000.2,
    )

    assert generation is None
    assert stock["_scalp_revive_min_quote_ts"] == 1000.0
    assert scheduler.current_generation("002990") is None
