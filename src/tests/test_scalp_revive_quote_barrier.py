from src.engine import kiwoom_sniper_v2 as sniper
from src.engine import sniper_execution_receipts as receipts


def test_scalp_revive_sets_quote_barrier_before_rewatch(monkeypatch):
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(receipts, "move_orders_to_terminal", lambda stock, reason: None)
    stock = {"id": 7, "status": "HOLDING", "buy_price": 10000, "buy_qty": 3}

    receipts._apply_scalp_revive_memory_state(
        target_stock=stock,
        code="002990",
        new_watch_id=8,
        revived_position_tag="scalping_default",
        revived_at_ts=1000.0,
    )

    assert stock["status"] == "WATCHING"
    assert stock["_scalp_revive_min_quote_ts"] == 1000.0


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
