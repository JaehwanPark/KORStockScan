from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from src.engine.scalping.early_volatility_partial_tp import (
    EarlyTPRuntimeLedger,
    EarlyVolatilityTPContext,
    resolve_early_volatility_tp,
)


def _context(**overrides):
    values = {
        "position_cycle_id": "1:005930:1",
        "venue": "KRX",
        "entry_lineage": "SCANNER",
        "average_price": 10_000,
        "holding_qty": 10,
        "entry_bundle_complete": True,
        "pending_entry": False,
        "pending_add": False,
        "quote_fresh": True,
        "quote_conflict": False,
        "direction_state": "NEUTRAL",
        "observed_prices": (10_000, 10_040, 10_080),
        "observation_span_sec": 3.0,
        "tick_sample_count": 3,
        "trade_cost_rate": 0.0023,
    }
    values.update(overrides)
    return EarlyVolatilityTPContext(**values)


def test_resolver_keeps_runner_and_builds_fee_aware_sell_limit():
    decision = resolve_early_volatility_tp(_context())

    assert decision.eligible is True
    assert decision.partial_qty == 3
    assert decision.runner_qty == 7
    assert decision.limit_price >= 10_080
    assert decision.partial_qty + decision.runner_qty == 10
    assert decision.observed_range_pct == 0.8


def test_resolver_fail_closed_contracts():
    cases = [
        (_context(venue="NXT"), "venue_not_krx"),
        (_context(holding_qty=1), "runner_minimum_not_met"),
        (_context(entry_bundle_complete=False), "entry_bundle_not_terminal"),
        (_context(quote_fresh=False), "quote_source_unusable"),
        (_context(direction_state="HARD_NEGATIVE"), "direction_unusable"),
        (
            _context(observed_prices=(10_000, 10_010, 10_020)),
            "volatility_range_not_met",
        ),
        (_context(partial_already_filled=True), "single_partial_already_filled"),
    ]

    for context, expected_reason in cases:
        decision = resolve_early_volatility_tp(context)
        assert decision.eligible is False
        assert decision.reason == expected_reason
        assert decision.partial_qty == 0
        assert decision.runner_qty == context.holding_qty


def test_runtime_ledger_atomic_round_trip(tmp_path):
    path = tmp_path / "ledger.json"
    ledger = EarlyTPRuntimeLedger(path)

    row = ledger.upsert(
        "cycle-1",
        state="OPEN",
        order_no="123",
        reserved_qty=3,
    )
    assert row["position_cycle_id"] == "cycle-1"
    assert ledger.get("cycle-1")["state"] == "OPEN"

    ledger.upsert("cycle-1", state="FILLED_RUNNER", filled_qty=3)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["positions"]["cycle-1"]["state"] == "FILLED_RUNNER"


def test_holding_early_tp_receipt_stays_holding_and_resets_runner_peak(
    monkeypatch, tmp_path
):
    from src.engine import sniper_execution_receipts as receipts

    class Record:
        status = "HOLDING"
        buy_qty = 10

    record = Record()

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, _model):
            return Query()

    class DB:
        def get_session(self):
            return Session()

    stock = {
        "id": 1,
        "code": "005930",
        "name": "test",
        "status": "HOLDING",
        "buy_qty": 10,
        "early_volatility_tp_position_cycle_id": "cycle-1",
        "early_volatility_tp_ord_no": "123",
        "early_volatility_tp_requested_qty": 3,
        "early_volatility_tp_filled_qty": 0,
        "early_volatility_tp_fill_amount": 0,
    }
    monkeypatch.setattr(receipts, "DB", DB())
    monkeypatch.setattr(
        receipts,
        "_EARLY_VOLATILITY_TP_LEDGER",
        EarlyTPRuntimeLedger(tmp_path / "receipt-ledger.json"),
    )

    receipts._handle_early_volatility_tp_sell_execution(
        target_id=1,
        target_stock=stock,
        code="005930",
        order_no="123",
        exec_price=10_100,
        exec_qty=3,
        now=datetime.now(),
        safe_buy_price=10_000,
    )

    assert stock["status"] == "HOLDING"
    assert stock["buy_qty"] == 7
    assert stock["early_volatility_tp_state"] == "FILLED_RUNNER"
    assert stock["early_volatility_tp_applied"] is True
    assert stock["early_volatility_tp_runner_peak_reset_pending"] is True
    assert record.status == "HOLDING"
    assert record.buy_qty == 7


def test_execution_target_matches_early_tp_without_sell_ordered(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts

    stock = {
        "id": 1,
        "code": "005930",
        "status": "HOLDING",
        "early_volatility_tp_ord_no": "123",
    }
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])

    assert receipts._find_execution_target("005930", "SELL", "123") is stock


def test_execution_target_binds_unique_submitting_early_tp(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts

    stock = {
        "id": 1,
        "code": "005930",
        "status": "HOLDING",
        "early_volatility_tp_state": "SUBMITTING",
        "early_volatility_tp_ord_no": "",
    }
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])

    assert receipts._find_execution_target("005930", "SELL", "456") is stock
    receipts._apply_order_notice_to_target(
        stock,
        code="005930",
        exec_type="SELL",
        order_no="456",
        status="accepted",
    )
    assert stock["early_volatility_tp_ord_no"] == "456"


def test_replay_candidate_uses_observed_first_hit_and_keeps_runner():
    from src.engine.scalping.early_volatility_partial_tp_replay import (
        Trade,
        replay_candidate,
    )

    kst = timezone(timedelta(hours=9))
    terminal = datetime(2026, 7, 23, 9, 10, tzinfo=kst)
    trade = Trade(
        record_id="1",
        code="005930",
        venue="KRX",
        entry_terminal_at=terminal,
        exit_at=terminal + timedelta(seconds=30),
        exit_price=9_900,
        avg_price=10_000,
        qty=10,
        actual_submit_seen=True,
        completed_seen=True,
        events=[
            {
                "at": terminal,
                "stage": "tick",
                "price": 10_000,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
            {
                "at": terminal + timedelta(seconds=2),
                "stage": "tick",
                "price": 10_040,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
            {
                "at": terminal + timedelta(seconds=4),
                "stage": "tick",
                "price": 10_080,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
            {
                "at": terminal + timedelta(seconds=10),
                "stage": "tick",
                "price": 10_100,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
        ],
    )

    result = replay_candidate(trade, 0.30, 0.45, 90)

    assert result is not None
    assert result["partial_qty"] == 3
    assert result["runner_qty"] == 7
    assert result["partial_qty"] + result["runner_qty"] == trade.qty
    assert result["delta_net_profit_krw"] > 0


def test_runtime_policy_requires_qualification_and_activation_epoch(
    monkeypatch, tmp_path
):
    from src.engine import sniper_state_handlers as handlers

    policy_path = tmp_path / "policy.json"
    payload = {
        "policy_version": "early_volatility_partial_tp_v1",
        "decision": "implemented_historical_real_validation_pass",
        "qualified_for_runtime": True,
        "effective_venue": "KRX",
        "partial_ratio": 0.35,
        "target_net_profit_pct": 0.55,
        "ttl_sec": 210,
        "active_from_epoch": 1000.0,
    }
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_EARLY_VOLATILITY_TP_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_EARLY_VOLATILITY_TP_ACTIVE_DATE", "2026-07-23")
    monkeypatch.setenv("KORSTOCKSCAN_EARLY_VOLATILITY_TP_POLICY_FILE", str(policy_path))
    handlers._EARLY_VOLATILITY_TP_POLICY_CACHE.clear()

    policy = handlers._early_volatility_tp_policy(datetime(2026, 7, 23))

    assert policy["enabled"] is True
    assert policy["reason"] == "active"
    assert policy["partial_ratio"] == 0.35

    payload["qualified_for_runtime"] = False
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    handlers._EARLY_VOLATILITY_TP_POLICY_CACHE.clear()
    policy = handlers._early_volatility_tp_policy(datetime(2026, 7, 23))
    assert policy == {"enabled": False, "reason": "policy_not_qualified"}


def test_cancel_confirms_unfilled_absence_and_reconciles_broker_qty(
    monkeypatch, tmp_path
):
    from src.engine import sniper_state_handlers as handlers

    class Record:
        status = "HOLDING"
        buy_qty = 10

    record = Record()

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, _model):
            return Query()

    class DB:
        def get_session(self):
            return Session()

    stock = {
        "id": 1,
        "code": "005930",
        "status": "HOLDING",
        "buy_qty": 10,
        "early_volatility_tp_position_cycle_id": "cycle-1",
        "early_volatility_tp_state": "OPEN",
        "early_volatility_tp_ord_no": "123",
    }
    monkeypatch.setattr(handlers, "DB", DB())
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers,
        "_EARLY_VOLATILITY_TP_LEDGER",
        EarlyTPRuntimeLedger(tmp_path / "cancel-ledger.json"),
    )
    monkeypatch.setattr(
        handlers.sniper_trade_utils,
        "send_cancel_order_with_exchange_retry",
        lambda **_kwargs: {"return_code": "0"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": "005930", "qty": 7}], {"KRX"}),
    )

    assert handlers._cancel_early_volatility_tp(
        stock,
        "005930",
        reason="full_exit_precedence",
        now_ts=1000.0,
    )
    assert stock["early_volatility_tp_state"] == "CANCELLED"
    assert stock["buy_qty"] == 7
    assert record.buy_qty == 7


def test_final_runner_sell_composes_early_partial_realized_pnl(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts
    from src.engine.trade_profit import calculate_net_realized_pnl

    class Record:
        buy_price = 10_000.0
        buy_qty = 7
        position_tag = "SCANNER"
        status = "HOLDING"
        sell_price = 0
        sell_time = None
        profit_rate = 0.0

    record = Record()

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, _model):
            return Query()

    class DB:
        def get_session(self):
            return Session()

    class Bus:
        def publish(self, *_args, **_kwargs):
            return None

    events = []
    monkeypatch.setattr(receipts, "DB", DB())
    monkeypatch.setattr(receipts, "event_bus", Bus())
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: None)
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **fields: events.append(fields),
    )
    snapshot = {
        "name": "test",
        "code": "005930",
        "position_tag": "SCANNER",
        "early_volatility_tp_filled_qty": 3,
        "early_volatility_tp_fill_amount": 30_300,
    }

    receipts._update_db_for_sell(
        1,
        9_900,
        datetime.now(),
        snapshot,
        "SCALPING",
        False,
    )

    expected = calculate_net_realized_pnl(
        10_000, 10_100, 3
    ) + calculate_net_realized_pnl(10_000, 9_900, 7)
    assert record.status == "COMPLETED"
    assert record.buy_qty == 10
    assert record.sell_price == 9_960
    assert snapshot["realized_pnl_krw"] == expected
    assert snapshot["partial_realized_qty"] == 3
    assert snapshot["runner_realized_qty"] == 7
    assert events[-1]["realized_pnl_krw"] == expected
