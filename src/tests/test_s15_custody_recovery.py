import json
import errno
import threading
from contextlib import contextmanager
from types import SimpleNamespace

import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_s15_fast_track as s15


def _state(**overrides):
    state = {
        "lock": threading.RLock(),
        "name": "TEST",
        "status": "BUY_SENT",
        "shadow_id": 7,
        "buy_ord_no": "B1",
        "sell_ord_no": "",
        "pending_cancel_ord_no": "",
        "req_buy_qty": 5,
        "cum_buy_qty": 0,
        "cum_buy_amount": 0,
        "avg_buy_price": 0,
        "cum_sell_qty": 0,
        "cum_sell_amount": 0,
        "avg_sell_price": 0,
    }
    state.update(overrides)
    return state


def test_s15_custody_journal_round_trip_and_hash_tamper(tmp_path, monkeypatch):
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    state = _state(
        cum_buy_qty=2,
        avg_buy_price=10_000,
        s15_custody_persist_failed=True,
        s15_custody_persist_error="previous failure",
    )

    assert s15._persist_fast_state("123456", state) is True
    code, restored = s15._load_fast_state_journal(tmp_path / "123456.json")

    assert code == "123456"
    assert restored["cum_buy_qty"] == 2
    assert restored["s15_custody_restored"] is True
    assert "s15_custody_persist_failed" not in restored
    assert "s15_custody_persist_error" not in restored
    payload = json.loads((tmp_path / "123456.json").read_text())
    payload["state"]["cum_buy_qty"] = 3
    (tmp_path / "123456.json").write_text(json.dumps(payload))

    try:
        s15._load_fast_state_journal(tmp_path / "123456.json")
    except ValueError as exc:
        assert str(exc) == "s15_custody_hash_mismatch"
    else:
        raise AssertionError("tampered custody journal must fail closed")


def test_s15_restore_rehydrates_state_before_starting_recovery(tmp_path, monkeypatch):
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    s15.FAST_TRADE_STATE.clear()
    state = _state(cum_buy_qty=5, avg_buy_price=10_000, status="HOLDING")
    assert s15._persist_fast_state("123456", state) is True
    started = []
    monkeypatch.setattr(
        s15,
        "_start_s15_recovery_thread",
        lambda code, restored: started.append((code, restored)) or True,
    )

    assert s15._restore_fast_trade_states_from_journal() == 1
    assert s15.FAST_TRADE_STATE["123456"]["status"] == "HOLDING"
    assert started[0][0] == "123456"


def test_s15_restore_rejects_symlink_custody_directory(tmp_path, monkeypatch):
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", linked)

    assert s15._restore_fast_trade_states_from_journal() == 0


def test_s15_inventory_requires_both_venues_and_exact_unfilled_snapshot(monkeypatch):
    monkeypatch.setattr(s15, "_s15_symbol_allocation_unambiguous", lambda _code: True)
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([{"code": "123456", "qty": 5}], {"KRX"}),
    )

    snapshot, orders, reason = s15._s15_inventory_and_orders("123456")

    assert snapshot is None
    assert orders == ()
    assert reason == "partial_venue_inventory_snapshot"


def test_s15_inventory_rejects_malformed_open_order_quantity(monkeypatch):
    monkeypatch.setattr(s15, "_s15_symbol_allocation_unambiguous", lambda _code: True)
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda _token: (
            [{"code": "123456", "qty": "5", "buy_price": "10000"}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *_args, **_kwargs: (
            [{"code": "123456", "remaining_qty": "1e2", "order_no": "O1"}],
            {"request_succeeded": True},
        ),
    )

    snapshot, orders, reason = s15._s15_inventory_and_orders("123456")

    assert snapshot is None
    assert orders == ()
    assert reason == "open_order_numeric_contract_invalid"


def test_s15_recovery_blocks_same_symbol_multi_owner(monkeypatch):
    rows = [
        SimpleNamespace(strategy="S15_FAST"),
        SimpleNamespace(strategy="SCALPING"),
    ]

    class Query:
        def filter(self, *args):
            return self

        def all(self):
            return rows

    class Session:
        def query(self, _model):
            return Query()

    class DB:
        @contextmanager
        def get_session(self):
            yield Session()

    monkeypatch.setattr(s15, "DB", DB())

    assert s15._s15_symbol_allocation_unambiguous("123456") is False


def test_s15_recovery_submits_only_exact_inventory_residual(monkeypatch):
    state = _state(cum_buy_qty=5, avg_buy_price=10_000, status="HOLDING")
    calls = []
    db_updates = []
    snapshots = iter(
        [
            ({"qty": 5, "avg_price": 10_000}, (), "exact"),
            RuntimeError("stop after first exact submission"),
        ]
    )

    def snapshot(_code):
        value = next(snapshots)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(s15, "_s15_inventory_and_orders", snapshot)
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda code, qty, token: (
            calls.append((code, qty)) or {"return_code": 0, "ord_no": "S1"}
        ),
    )
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(
        s15,
        "update_s15_shadow_record",
        lambda shadow_id, **values: db_updates.append((shadow_id, values)) or True,
    )
    monkeypatch.setattr(s15.time, "sleep", lambda _seconds: None)

    s15._recover_s15_custody("123456", state)

    assert calls == [("123456", 5)]
    assert state["sell_ord_no"] == "S1"
    assert state["status"] == "RECOVERY_REQUIRED"
    assert "stop after first exact submission" in state["s15_recovery_reason"]
    assert db_updates == [(7, {"status": "SELL_ORDERED", "scale_in_locked": True})]
    assert threading.current_thread() not in s15._S15_RECOVERY_THREADS


def test_s15_recovery_keeps_low_frequency_reconciliation_after_initial_window(
    monkeypatch,
):
    state = _state(cum_buy_qty=5, avg_buy_price=10_000, status="HOLDING")
    calls = 0
    sleeps = []

    def snapshot(_code):
        nonlocal calls
        calls += 1
        if calls <= 121:
            return None, (), "inventory_temporarily_unavailable"
        raise RuntimeError("stop persistent recovery test")

    monkeypatch.setattr(s15, "_s15_inventory_and_orders", snapshot)
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(s15.time, "sleep", sleeps.append)

    s15._recover_s15_custody("123456", state)

    assert calls == 122
    assert sleeps[:120] == [1.0] * 120
    assert sleeps[120] == 30.0
    assert state["status"] == "RECOVERY_REQUIRED"
    assert "stop persistent recovery test" in state["s15_recovery_reason"]


def test_s15_no_order_terminal_block_clears_durable_state(tmp_path, monkeypatch):
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    monkeypatch.setattr(s15, "AI_ENGINE", None)
    monkeypatch.setattr(s15, "DB", None)
    monkeypatch.setattr(
        s15,
        "WS_MANAGER",
        SimpleNamespace(get_latest_data=lambda _code: {"curr": 10_000}),
    )
    monkeypatch.setattr(s15, "update_s15_shadow_record", lambda *args, **kwargs: True)
    monkeypatch.setattr(s15, "_log_s15_event", lambda *args, **kwargs: None)
    state = _state(
        status="ARMED",
        buy_ord_no="",
        shadow_id=None,
        cum_buy_qty=0,
        cum_sell_qty=0,
    )
    s15.FAST_TRADE_STATE["123456"] = state
    assert s15._persist_fast_state("123456", state) is True

    s15.execute_fast_track_scalp_v2("123456", "TEST", 10_000)

    assert "123456" not in s15.FAST_TRADE_STATE
    assert not (tmp_path / "123456.json").exists()


def test_s15_custody_enospc_keeps_runtime_state_and_cleans_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    monkeypatch.setattr(
        s15.os,
        "replace",
        lambda *_args: (_ for _ in ()).throw(OSError(errno.ENOSPC, "full")),
    )
    state = _state(cum_buy_qty=2, avg_buy_price=10_000)

    assert s15._persist_fast_state("123456", state) is False

    assert state["s15_custody_persist_failed"] is True
    assert list(tmp_path.glob(".*.tmp")) == []


def test_s15_custody_size_limit_interlocks_without_writing_partial_file(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    state = _state(oversized="x" * s15.S15_CUSTODY_MAX_BYTES)

    assert s15._persist_fast_state("123456", state) is False

    assert state["status"] == "RECOVERY_REQUIRED"
    assert "size_limit_exceeded" in state["s15_custody_persist_error"]
    assert not (tmp_path / "123456.json").exists()
    assert list(tmp_path.glob(".*.tmp")) == []


def test_standard_sell_journal_enospc_interlocks_all_followup_orders(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(
        receipts.os,
        "replace",
        lambda *_args: (_ for _ in ()).throw(OSError(errno.ENOSPC, "full")),
    )
    target = {
        "id": 17,
        "code": "123456",
        "name": "TEST",
        "buy_price": 10_000,
        "_sell_execution_receipt_state": {
            "position_qty": 5,
            "aggregate_cumulative_qty": 2,
            "aggregate_cumulative_amount": 20_100,
            "final": False,
        },
    }

    assert (
        receipts._persist_sell_receipt_recovery_or_interlock(
            target,
            code="123456",
            reason="test_enospc",
        )
        is False
    )

    assert target["scale_in_locked"] is True
    assert target["sell_partial_exit_recovery_required"] is True
    assert target["sell_cancel_reconciliation_required"] is True
    assert target["sell_receipt_durability_blocked"] is True
    assert list(tmp_path.glob(".*.tmp")) == []


def test_s15_exact_receipt_completion_commits_before_journal_clear(
    tmp_path, monkeypatch
):
    record = SimpleNamespace(
        id=7,
        status="SELL_ORDERED",
        sell_price=None,
        sell_time=None,
        profit_rate=None,
        buy_price=10_000,
        buy_qty=5,
        scale_in_locked=True,
    )

    class Query:
        def filter_by(self, **kwargs):
            return self

        def first(self):
            return record

    class Session:
        def query(self, _model):
            return Query()

    class DB:
        @contextmanager
        def get_session(self):
            yield Session()

    monkeypatch.setattr(s15, "DB", DB())
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    monkeypatch.setattr(s15, "_log_s15_event", lambda *args, **kwargs: None)
    state = _state(
        status="DONE",
        cum_buy_qty=5,
        cum_buy_amount=50_000,
        avg_buy_price=10_000,
        cum_sell_qty=5,
        cum_sell_amount=50_500,
        avg_sell_price=10_100,
        sell_receipt_position_complete=True,
        sell_receipt_economics_complete=True,
    )
    s15.FAST_TRADE_STATE["123456"] = state
    assert s15._persist_fast_state("123456", state) is True

    assert s15._finalize_s15_completed_state("123456", state) is True

    assert record.status == "COMPLETED"
    assert record.sell_price == 10_100
    assert record.scale_in_locked is False
    assert "123456" not in s15.FAST_TRADE_STATE
    assert not (tmp_path / "123456.json").exists()


def test_s15_completion_db_failure_keeps_exact_final_pending_journal(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(s15, "S15_CUSTODY_DIR", tmp_path)
    monkeypatch.setattr(s15, "update_s15_shadow_record", lambda *args, **kwargs: False)
    state = _state(
        status="EXIT_RECEIPT_PENDING",
        cum_buy_qty=5,
        cum_buy_amount=50_000,
        avg_buy_price=10_000,
        cum_sell_qty=5,
        cum_sell_amount=50_500,
        avg_sell_price=10_100,
        sell_receipt_position_complete=True,
        sell_receipt_economics_complete=True,
    )
    s15.FAST_TRADE_STATE["123456"] = state

    assert s15._finalize_s15_completed_state("123456", state) is False

    _code, restored = s15._load_fast_state_journal(tmp_path / "123456.json")
    assert restored["s15_final_pending_db_commit"] is True
    assert restored["status"] == "RECOVERY_REQUIRED"
    assert restored["s15_recovery_reason"] == "completion_db_commit_failed"
    assert "123456" in s15.FAST_TRADE_STATE
    s15.FAST_TRADE_STATE.pop("123456", None)


def test_s15_committed_marker_cleanup_retry_does_not_replay_db_completion(
    monkeypatch,
):
    updates = []
    clear_results = iter((False, True))
    state = _state(
        status="EXIT_RECEIPT_PENDING",
        cum_buy_qty=5,
        avg_buy_price=10_000,
        cum_sell_qty=5,
        avg_sell_price=10_100,
        sell_receipt_position_complete=True,
        sell_receipt_economics_complete=True,
    )
    s15.FAST_TRADE_STATE["123456"] = state
    monkeypatch.setattr(
        s15,
        "update_s15_shadow_record",
        lambda *args, **kwargs: updates.append((args, kwargs)) or True,
    )
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(s15, "_log_s15_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        s15, "_clear_fast_state_journal", lambda _code: next(clear_results)
    )

    assert s15._finalize_s15_completed_state("123456", state) is False
    assert state["s15_completion_committed"] is True
    assert len(updates) == 1

    assert s15._finalize_s15_completed_state("123456", state) is True
    assert len(updates) == 1
    assert "123456" not in s15.FAST_TRADE_STATE


def test_fast_receipt_must_persist_before_returning(monkeypatch):
    state = _state()
    persisted = []
    monkeypatch.setattr(
        receipts, "_get_fast_state", lambda code: state if code == "123456" else None
    )
    monkeypatch.setattr(receipts, "_weighted_avg", s15._weighted_avg)
    monkeypatch.setattr(receipts, "_now_ts", lambda: 1.0)
    monkeypatch.setattr(
        receipts,
        "_persist_fast_state_callback",
        lambda code, current: persisted.append((code, current["cum_buy_qty"])) or True,
    )
    monkeypatch.setattr(receipts, "_finalize_fast_state_callback", lambda *_: False)

    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "BUY",
            "order_no": "B1",
            "price": 10_000,
            "qty": 2,
            "order_qty": 5,
            "remaining_qty": 3,
            "cumulative_exec_amount": 20_000,
            "execution_no": "E1",
            "unit_exec_price": 10_000,
            "unit_exec_qty": 2,
        }
    )

    assert state["cum_buy_qty"] == 2
    assert persisted == [("123456", 2)]


def test_fast_receipt_missing_economics_requests_exact_broker_snapshot(monkeypatch):
    state = _state(
        status="EXIT_SENT",
        cum_buy_qty=5,
        sell_ord_no="S1",
    )
    refreshes = []
    monkeypatch.setattr(
        receipts, "_get_fast_state", lambda code: state if code == "123456" else None
    )
    monkeypatch.setattr(receipts, "_persist_fast_state_callback", lambda *_: True)
    monkeypatch.setattr(receipts, "_now_ts", lambda: 1.0)
    monkeypatch.setattr(
        receipts,
        "_broker_snapshot_refresh_callback",
        lambda **values: refreshes.append(values),
    )

    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "S1",
            "price": 0,
            "qty": 2,
            "order_qty": 5,
            "remaining_qty": 3,
            "cumulative_exec_amount": None,
            "execution_no": "E1",
            "unit_exec_price": None,
            "unit_exec_qty": None,
        }
    )

    assert state["cum_sell_qty"] == 0
    assert state["sell_receipt_source_gap"] == "buy_receipt_incremental_price_missing"
    assert refreshes == [
        {"code": "123456", "reason": "fast_sell_receipt_reconcile_blocked"}
    ]
