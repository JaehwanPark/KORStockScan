import json
import errno
import threading
import time
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


def _exact_open_sell_snapshot(order_no="0000456", qty=5):
    return (
        {"qty": qty, "avg_price": 10_000},
        (
            {
                "code": "123456",
                "side": "SELL",
                "order_no": order_no,
                "qty": qty,
                "remaining_qty": qty,
                "submitted_quantity_source_valid": True,
                "sor_yn": "Y",
            },
        ),
        "exact",
    )


def test_s15_sell_response_preserves_available_qty_ambiguity():
    response = {
        "rt_cd": "-1",
        "err_msg": "매도가능수량 부족",
        "non_fatal_no_qty": True,
    }

    state, order_no, message = s15._classify_s15_sell_response(response)

    assert state == "ambiguous"
    assert order_no == ""
    assert message == "매도가능수량 부족"


def test_s15_sell_response_keeps_other_numeric_reject_definitive():
    response = {"rt_cd": "-1", "err_msg": "일반 주문 거절"}

    state, order_no, message = s15._classify_s15_sell_response(response)

    assert state == "definitive_reject"
    assert order_no == ""
    assert message == "일반 주문 거절"


def test_s15_stop_cancel_fsyncs_intent_and_calls_broker_once(monkeypatch):
    state = _state(
        id=7,
        code="123456",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000456",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(state)
    cancel_calls = []
    monkeypatch.setattr(s15, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "0",
            "ord_no": "0000999",
            "base_orig_ord_no": "0000456",
            "cncl_qty": "5",
            "broker_route_attempted": True,
            "effective_dmst_stex_tp": "SOR",
            "cancel_request_api_id": "kt10003",
            "cancel_request_code": "123456",
            "cancel_request_orig_ord_no": "0000456",
            "cancel_request_qty": "0",
            "cancel_request_route": "SOR",
            "cancel_request_bound": True,
        },
    )

    assert s15._submit_s15_stop_cancel(state, "123456", "0000456")
    assert s15._submit_s15_stop_cancel(state, "123456", "0000456")

    assert len(cancel_calls) == 1
    assert receipts.pending_sell_cancel_intent_exact(
        state,
        code="123456",
        order_no="0000456",
    )
    assert receipts.pending_sell_cancel_ack_exact(
        state,
        code="123456",
        order_no="0000456",
    )


def test_s15_stop_cancel_pre_intent_failure_retries_then_calls_once(monkeypatch):
    state = _state(
        id=8,
        code="123456",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000456",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(state)
    fast_persists = iter((False, True, True))
    cancel_calls = []
    monkeypatch.setattr(s15, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: _exact_open_sell_snapshot(),
    )
    monkeypatch.setattr(
        s15,
        "_persist_fast_state",
        lambda *_args: next(fast_persists),
    )
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "0",
            "ord_no": "0000999",
            "base_orig_ord_no": "0000456",
            "cncl_qty": "5",
            "broker_route_attempted": True,
            "effective_dmst_stex_tp": "SOR",
            "cancel_request_api_id": "kt10003",
            "cancel_request_code": "123456",
            "cancel_request_orig_ord_no": "0000456",
            "cancel_request_qty": "0",
            "cancel_request_route": "SOR",
            "cancel_request_bound": True,
        },
    )

    assert not s15._submit_s15_stop_cancel(state, "123456", "0000456")
    assert cancel_calls == []
    assert state["s15_stop_cancel_retry_required"] is True
    assert state["s15_stop_cancel_retry_generation"] == state["sell_submit_generation"]
    assert (
        state["s15_stop_cancel_retry_context_sha256"]
        == state["sell_submit_context_sha256"]
    )
    assert state["s15_stop_cancel_retry_order_no"] == "0000456"
    state["status"] = "RECOVERY_REQUIRED"
    state["s15_recovery_reason"] = "stop_exit_cancel_intent_durability_failed"

    assert s15._retry_s15_stop_cancel_if_required("123456", state) is True
    assert s15._retry_s15_stop_cancel_if_required("123456", state) is None
    assert len(cancel_calls) == 1
    assert state["status"] == "SELL_ORDERED"
    assert "s15_stop_cancel_retry_required" not in state
    assert receipts.pending_sell_cancel_intent_exact(
        state,
        code="123456",
        order_no="0000456",
    )


def test_s15_stop_cancel_intent_failure_retries_then_calls_once(monkeypatch):
    state = _state(
        id=9,
        code="123456",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000456",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(state)
    real_persist_intent = receipts.persist_pending_sell_cancel_intent_custody
    intent_attempts = 0

    def persist_intent(*args, **kwargs):
        nonlocal intent_attempts
        intent_attempts += 1
        if intent_attempts == 1:
            return False
        return real_persist_intent(*args, **kwargs)

    cancel_calls = []
    monkeypatch.setattr(s15, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: _exact_open_sell_snapshot(),
    )
    monkeypatch.setattr(
        receipts,
        "persist_pending_sell_cancel_intent_custody",
        persist_intent,
    )
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "0",
            "ord_no": "0000999",
            "base_orig_ord_no": "0000456",
            "cncl_qty": "5",
            "broker_route_attempted": True,
            "effective_dmst_stex_tp": "SOR",
            "cancel_request_api_id": "kt10003",
            "cancel_request_code": "123456",
            "cancel_request_orig_ord_no": "0000456",
            "cancel_request_qty": "0",
            "cancel_request_route": "SOR",
            "cancel_request_bound": True,
        },
    )

    assert not s15._submit_s15_stop_cancel(state, "123456", "0000456")
    assert cancel_calls == []
    assert state["s15_stop_cancel_retry_required"] is True

    assert s15._retry_s15_stop_cancel_if_required("123456", state) is True
    assert len(cancel_calls) == 1
    assert intent_attempts == 2
    assert "s15_stop_cancel_retry_required" not in state


def test_s15_stop_cancel_retry_rejects_generation_drift(monkeypatch):
    state = _state(
        code="123456",
        status="RECOVERY_REQUIRED",
        sell_ord_no="0000456",
        sell_odno="0000456",
        sell_submit_generation="new-generation",
        sell_submit_context_sha256="new-context",
        s15_stop_cancel_retry_required=True,
        s15_stop_cancel_retry_generation="old-generation",
        s15_stop_cancel_retry_context_sha256="old-context",
        s15_stop_cancel_retry_order_no="0000456",
    )
    cancel_calls = []
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs),
    )

    assert s15._retry_s15_stop_cancel_if_required("123456", state) is False
    assert cancel_calls == []
    assert state["status"] == "RECOVERY_REQUIRED"
    assert state["s15_recovery_reason"] == "stop_exit_cancel_retry_context_mismatch"


def test_s15_stop_cancel_retry_requires_exact_open_order(monkeypatch):
    state = _state(
        code="123456",
        status="RECOVERY_REQUIRED",
        sell_ord_no="0000456",
        sell_odno="0000456",
        sell_submit_requested_qty=5,
        sell_submit_intended_route="SOR",
        sell_submit_generation="same-generation",
        sell_submit_context_sha256="same-context",
        s15_stop_cancel_retry_required=True,
        s15_stop_cancel_retry_generation="same-generation",
        s15_stop_cancel_retry_context_sha256="same-context",
        s15_stop_cancel_retry_order_no="0000456",
    )
    cancel_calls = []
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: ({"qty": 5, "avg_price": 10_000}, (), "exact_absence"),
    )
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs),
    )

    assert s15._retry_s15_stop_cancel_if_required("123456", state) is False
    assert cancel_calls == []
    assert state["status"] == "RECOVERY_REQUIRED"
    assert (
        state["s15_recovery_reason"]
        == "stop_exit_cancel_retry_exact_open_order_required"
    )


def test_s15_stop_cancel_retry_reissues_exact_open_order_after_intent_crash(
    monkeypatch,
):
    state = _state(
        id=10,
        code="123456",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000456",
        sell_odno="0000456",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(state)
    assert receipts.persist_pending_sell_cancel_intent_custody(
        state,
        order_no="0000456",
        broker_route="SOR",
    )
    state.update(
        {
            "s15_stop_cancel_retry_required": True,
            "s15_stop_cancel_retry_generation": state["sell_submit_generation"],
            "s15_stop_cancel_retry_context_sha256": state["sell_submit_context_sha256"],
            "s15_stop_cancel_retry_order_no": "0000456",
        }
    )
    cancel_calls = []
    monkeypatch.setattr(s15, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: _exact_open_sell_snapshot(),
    )
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "0",
            "ord_no": "0000999",
            "base_orig_ord_no": "0000456",
            "cncl_qty": "5",
            "broker_route_attempted": True,
            "effective_dmst_stex_tp": "SOR",
            "cancel_request_api_id": "kt10003",
            "cancel_request_code": "123456",
            "cancel_request_orig_ord_no": "0000456",
            "cancel_request_qty": "0",
            "cancel_request_route": "SOR",
            "cancel_request_bound": True,
        },
    )

    assert s15._retry_s15_stop_cancel_if_required("123456", state) is True
    assert len(cancel_calls) == 1
    assert receipts.pending_sell_cancel_ack_exact(
        state,
        code="123456",
        order_no="0000456",
    )


def test_s15_stop_cancel_retry_absent_order_enters_terminal_proof_without_recall(
    monkeypatch,
):
    state = _state(
        id=11,
        code="123456",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000456",
        sell_odno="0000456",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(state)
    assert receipts.persist_pending_sell_cancel_intent_custody(
        state,
        order_no="0000456",
        broker_route="SOR",
    )
    state.update(
        {
            "s15_stop_cancel_retry_required": True,
            "s15_stop_cancel_retry_generation": state["sell_submit_generation"],
            "s15_stop_cancel_retry_context_sha256": state["sell_submit_context_sha256"],
            "s15_stop_cancel_retry_order_no": "0000456",
        }
    )
    cancel_calls = []
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: ({"qty": 5, "avg_price": 10_000}, (), "exact_absence"),
    )
    monkeypatch.setattr(
        s15.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs),
    )

    assert s15._retry_s15_stop_cancel_if_required("123456", state) is True
    assert cancel_calls == []
    assert state["status"] == "SELL_ORDERED"
    assert state["pending_cancel_ord_no"] == "0000456"
    assert state["s15_recovery_reason"] == "stop_exit_terminal_pending"
    assert "s15_stop_cancel_retry_required" not in state


def test_s15_cancel_recovery_routes_terminal_release_to_common_owner(monkeypatch):
    from src.engine import sniper_state_handlers

    state = _state(
        id=7,
        code="123456",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000456",
        sell_odno="0000456",
        pending_cancel_ord_no="0000456",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(state)
    assert receipts.persist_pending_sell_cancel_intent_custody(
        state,
        order_no="0000456",
        broker_route="SOR",
    )
    calls = []
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *_args: True)

    def release(stock, code, order_no, db):
        calls.append((stock, code, order_no, db))
        stock["status"] = "HOLDING"
        return True

    monkeypatch.setattr(sniper_state_handlers, "process_sell_cancellation", release)

    assert s15._reconcile_s15_pending_sell_cancel("123456", state) is True
    assert len(calls) == 1
    assert calls[0][2] == "0000456"
    assert state["status"] == "HOLDING"
    assert "pending_cancel_ord_no" not in state
    assert state["s15_recovery_reason"] == "stop_exit_cancel_terminal_released"


def test_main_sell_timeout_handler_never_owns_s15_generation(monkeypatch):
    from src.engine import sniper_state_handlers

    stock = _state(
        id=7,
        code="123456",
        strategy="S15_FAST",
        status="SELL_ORDERED",
        sell_order_time=0,
        sell_ord_no="0000456",
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "_manual_control_exclusion_blocked",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("main S15 owner must return before cancel dispatch")
        ),
    )

    sniper_state_handlers.handle_sell_ordered_state(stock, "123456")

    assert stock["sell_order_time"] == 0
    assert stock["sell_ord_no"] == "0000456"


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
    state = _state(
        cum_buy_qty=5,
        cum_buy_amount=50_000,
        avg_buy_price=10_000,
        buy_ord_no="0000007",
        status="HOLDING",
    )
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


def _s15_terminal_marker_state(*, tamper_requested_qty=False):
    state = _state(
        code="123456",
        id=7,
        shadow_id=7,
        strategy="S15_FAST",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000001",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time() - 1,
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    context, reason = receipts._validated_sell_pending_submit_context(state)
    assert reason == "pending_submit_context_exact"
    state.update(
        {
            "s15_sell_terminal_outcome_kind": ("definitive_reject_no_broker_order"),
            "s15_sell_terminal_outcome_generation": context["generation"],
            "s15_sell_terminal_outcome_context_sha256": state[
                "sell_submit_context_sha256"
            ],
            "s15_sell_terminal_outcome_target_id": context["target_id"],
            "s15_sell_terminal_outcome_code": context["code"],
            "s15_sell_terminal_outcome_owner_position_qty": context[
                "owner_position_qty"
            ],
            "s15_sell_terminal_outcome_requested_qty": context["requested_qty"],
            "s15_sell_terminal_outcome_intended_route": context["intended_route"],
            "s15_sell_terminal_outcome_intended_effective_venue": context[
                "intended_effective_venue"
            ],
            "s15_sell_terminal_outcome_intended_session_bucket": context[
                "intended_session_bucket"
            ],
        }
    )
    if tamper_requested_qty:
        state["sell_submit_requested_qty"] = 4
        state["sell_submit_context_sha256"] = (
            receipts._sell_pending_submit_context_sha256(state)
        )
    return state


def test_s15_terminal_marker_restart_requires_full_exact_pending_context(
    tmp_path, monkeypatch
):
    record = SimpleNamespace(
        id=7,
        stock_code="123456",
        strategy="S15_FAST",
        status="HOLDING",
        buy_qty=5,
    )

    class Query:
        def filter_by(self, **_kwargs):
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
    monkeypatch.setattr(s15, "_start_s15_recovery_thread", lambda *_args: True)
    s15.FAST_TRADE_STATE.clear()

    exact = _s15_terminal_marker_state()
    assert s15._persist_fast_state("123456", exact)
    assert s15._restore_fast_trade_states_from_journal() == 1
    restored = s15.FAST_TRADE_STATE.pop("123456")
    assert restored["status"] == "HOLDING"
    assert "sell_submit_generation" not in restored

    tampered = _s15_terminal_marker_state(tamper_requested_qty=True)
    assert s15._persist_fast_state("123456", tampered)
    assert s15._restore_fast_trade_states_from_journal() == 1
    restored = s15.FAST_TRADE_STATE.pop("123456")
    assert restored["status"] == "RECOVERY_REQUIRED"
    assert restored["sell_submit_generation"]


def test_s15_inventory_requires_both_venues_and_exact_unfilled_snapshot(monkeypatch):
    monkeypatch.setattr(s15, "_s15_symbol_allocation_unambiguous", lambda _code: True)
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *_args, **_kwargs: (
            [],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_account_balance_kt00005_with_meta",
        lambda token: (
            [{"code": "123456", "qty": 5}],
            {"KRX"},
            {"normalization_contract_complete": False},
        ),
    )

    snapshot, orders, reason = s15._s15_inventory_and_orders("123456")

    assert snapshot is None
    assert orders == ()
    assert reason == "inventory_snapshot_contract_incomplete"


def test_s15_inventory_rejects_malformed_open_order_quantity(monkeypatch):
    monkeypatch.setattr(s15, "_s15_symbol_allocation_unambiguous", lambda _code: True)
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_account_balance_kt00005_with_meta",
        lambda _token: (
            [{"code": "123456", "qty": "5", "buy_price": "10000"}],
            {"KRX", "NXT"},
            {"normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *_args, **_kwargs: (
            [{"code": "123456", "remaining_qty": "1e2", "order_no": "O1"}],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )

    snapshot, orders, reason = s15._s15_inventory_and_orders("123456")

    assert snapshot is None
    assert orders == ()
    assert reason == "open_order_numeric_contract_invalid"


def test_s15_inventory_rejects_positive_open_order_with_unknown_side(monkeypatch):
    monkeypatch.setattr(s15, "_s15_symbol_allocation_unambiguous", lambda _code: True)
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_account_balance_kt00005_with_meta",
        lambda _token: (
            [{"code": "123456", "qty": "5", "buy_price": "10000"}],
            {"KRX", "NXT"},
            {"normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *_args, **_kwargs: (
            [
                {
                    "code": "123456",
                    "remaining_qty": 5,
                    "ord_no": "0000007",
                    "side": "UNKNOWN",
                }
            ],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )

    snapshot, orders, reason = s15._s15_inventory_and_orders("123456")

    assert snapshot is None
    assert orders == ()
    assert reason == "open_order_identity_or_side_invalid"


def test_s15_inventory_rejects_positive_unallocatable_blank_code_order(
    monkeypatch,
):
    monkeypatch.setattr(s15, "_s15_symbol_allocation_unambiguous", lambda _code: True)
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_account_balance_kt00005_with_meta",
        lambda _token: (
            [{"code": "123456", "qty": "5", "buy_price": "10000"}],
            {"KRX", "NXT"},
            {"normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        s15.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *_args, **_kwargs: (
            [
                {
                    "code": "",
                    "remaining_qty": 1,
                    "ord_no": "0000007",
                    "side": "SELL",
                }
            ],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )

    snapshot, orders, reason = s15._s15_inventory_and_orders("123456")

    assert snapshot is None
    assert orders == ()
    assert reason == "open_order_identity_or_side_invalid"


def test_s15_unknown_side_open_order_never_submits_residual_sell(monkeypatch):
    state = _state(cum_buy_qty=5, avg_buy_price=10_000, status="RECOVERY_REQUIRED")
    calls = []
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: (None, (), "open_order_identity_or_side_invalid"),
    )
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    s15._recover_s15_custody("123456", state)

    assert calls == []
    assert state["status"] == "RECOVERY_REQUIRED"
    assert state["s15_recovery_reason"] == "open_order_identity_or_side_invalid"


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
    state = _state(
        cum_buy_qty=5,
        cum_buy_amount=50_000,
        avg_buy_price=10_000,
        buy_ord_no="0000007",
        status="HOLDING",
    )
    record = SimpleNamespace(
        id=7,
        stock_code="123456",
        strategy="S15_FAST",
        buy_qty=5,
        buy_price=10_000,
        status="HOLDING",
        scale_in_locked=True,
    )

    class Query:
        def __init__(self):
            self.filters = {}

        def filter_by(self, **kwargs):
            self.filters.update(kwargs)
            return self

        def update(self, values):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return 0
            for key, value in values.items():
                setattr(record, key, value)
            return 1

        def first(self):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return None
            return record

    class Session:
        def query(self, _model):
            return Query()

    class DB:
        @contextmanager
        def get_session(self):
            yield Session()

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
    monkeypatch.setattr(s15, "DB", DB())
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda code, qty, token: (
            calls.append((code, qty)) or {"return_code": 0, "ord_no": "0000001"}
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
    assert state["sell_ord_no"] == "0000001"
    assert state["status"] == "RECOVERY_REQUIRED"
    assert "stop after first exact submission" in state["s15_recovery_reason"]
    assert db_updates == [(7, {"status": "SELL_ORDERED", "scale_in_locked": True})]
    assert threading.current_thread() not in s15._S15_RECOVERY_THREADS


def test_s15_partial_buy_inventory_reconciles_db_before_one_residual_sell(
    monkeypatch,
):
    state = _state(
        status="BUY_CANCEL_RECONCILING",
        buy_ord_no="0000007",
        req_buy_qty=10,
        cum_buy_qty=4,
        cum_buy_amount=40_000,
        avg_buy_price=10_000,
    )
    record = SimpleNamespace(
        id=7,
        stock_code="123456",
        strategy="S15_FAST",
        status="BUY_ORDERED",
        buy_qty=0,
        buy_price=0,
        scale_in_locked=True,
    )

    class Query:
        def __init__(self):
            self.filters = {}

        def filter_by(self, **kwargs):
            self.filters.update(kwargs)
            return self

        def first(self):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return None
            return record

        def update(self, values):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return 0
            for key, value in values.items():
                setattr(record, key, value)
            return 1

    class Session:
        def query(self, _model):
            return Query()

    class DB:
        @contextmanager
        def get_session(self):
            yield Session()

    snapshots = iter(
        (
            ({"qty": 4, "avg_price": 10_000}, (), "exact"),
            RuntimeError("stop after residual submit"),
        )
    )

    def snapshot(_code):
        value = next(snapshots)
        if isinstance(value, Exception):
            raise value
        return value

    calls = []
    monkeypatch.setattr(s15, "DB", DB())
    monkeypatch.setattr(s15, "_s15_inventory_and_orders", snapshot)
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda code, qty, token: calls.append((code, qty))
        or {"return_code": 0, "ord_no": "0000009"},
    )
    monkeypatch.setattr(s15.time, "sleep", lambda _seconds: None)

    s15._recover_s15_custody("123456", state)

    assert calls == [("123456", 4)]
    assert record.buy_qty == 4
    assert record.buy_price == 10_000
    assert record.status == "SELL_ORDERED"
    assert state["s15_partial_buy_owner_reconciled"] is True
    assert "stop after residual submit" in state["s15_recovery_reason"]


def test_s15_partial_buy_db_reconciliation_failure_never_submits_sell(monkeypatch):
    state = _state(
        status="BUY_CANCEL_RECONCILING",
        buy_ord_no="0000007",
        req_buy_qty=10,
        cum_buy_qty=4,
        cum_buy_amount=40_000,
        avg_buy_price=10_000,
    )
    record = SimpleNamespace(
        id=7,
        stock_code="123456",
        strategy="S15_FAST",
        status="BUY_ORDERED",
        buy_qty=0,
        buy_price=0,
    )

    class Query:
        def __init__(self):
            self.filters = {}

        def filter_by(self, **kwargs):
            self.filters.update(kwargs)
            return self

        def first(self):
            return record

        def update(self, _values):
            return 0

    class Session:
        def query(self, _model):
            return Query()

    class DB:
        @contextmanager
        def get_session(self):
            yield Session()

    calls = []
    monkeypatch.setattr(s15, "DB", DB())
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: ({"qty": 4, "avg_price": 10_000}, (), "exact"),
    )
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    s15._recover_s15_custody("123456", state)

    assert calls == []
    assert state["status"] == "RECOVERY_REQUIRED"
    assert state["s15_recovery_reason"] == "partial_buy_db_reconciliation_failed"


def test_s15_partial_buy_receipt_inventory_economics_mismatch_never_sells(
    monkeypatch,
):
    state = _state(
        status="BUY_CANCEL_RECONCILING",
        buy_ord_no="0000007",
        req_buy_qty=10,
        cum_buy_qty=4,
        cum_buy_amount=40_000,
        avg_buy_price=10_000,
    )
    record = SimpleNamespace(
        id=7,
        stock_code="123456",
        strategy="S15_FAST",
        status="BUY_ORDERED",
        buy_qty=0,
        buy_price=0,
    )

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

        def update(self, _values):
            raise AssertionError("mismatched evidence must not update DB")

    class Session:
        def query(self, _model):
            return Query()

    class DB:
        @contextmanager
        def get_session(self):
            yield Session()

    sell_calls = []
    monkeypatch.setattr(s15, "DB", DB())
    monkeypatch.setattr(
        s15,
        "_s15_inventory_and_orders",
        lambda _code: ({"qty": 5, "avg_price": 10_100}, (), "exact"),
    )
    monkeypatch.setattr(s15, "_persist_fast_state", lambda *args: True)
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: sell_calls.append((args, kwargs)),
    )

    s15._recover_s15_custody("123456", state)

    assert sell_calls == []
    assert record.status == "BUY_ORDERED"
    assert record.buy_qty == 0
    assert state["status"] == "RECOVERY_REQUIRED"
    assert "economics_mismatch" in state["s15_partial_buy_db_error"]


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


def test_s15_pending_order_conflict_never_rebinds_or_submits(monkeypatch):
    state = _state(
        code="123456",
        id=7,
        shadow_id=7,
        strategy="S15_FAST",
        status="SELL_ORDERED",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000001",
        sell_odno="0000001",
    )
    state.update(
        receipts.build_pending_sell_submit_context_fields(
            state,
            code="123456",
            requested_qty=5,
            started_at=time.time() - 1,
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    snapshots = iter(
        (
            (
                {"qty": 5, "avg_price": 10_000},
                (
                    {
                        "code": "123456",
                        "side": "SELL",
                        "qty": 5,
                        "remaining_qty": 5,
                        "ord_no": "0000002",
                        "sor_yn": "Y",
                        "submitted_quantity_source_valid": True,
                    },
                ),
                "exact",
            ),
            RuntimeError("stop after conflict persistence"),
        )
    )

    def snapshot(_code):
        value = next(snapshots)
        if isinstance(value, Exception):
            raise value
        return value

    sell_calls = []
    reasons = []
    monkeypatch.setattr(s15, "_s15_inventory_and_orders", snapshot)
    monkeypatch.setattr(
        s15, "_reconcile_s15_positive_inventory_owner", lambda *args: True
    )
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: sell_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        s15,
        "_persist_fast_state",
        lambda _code, current: reasons.append(current.get("s15_recovery_reason"))
        or True,
    )
    monkeypatch.setattr(s15.time, "sleep", lambda _seconds: None)

    s15._recover_s15_custody("123456", state)

    assert sell_calls == []
    assert state["sell_ord_no"] == "0000001"
    assert "pending_sell_order_open_identity_conflict" in reasons


def test_s15_stale_order_number_without_generation_never_claims_open_sell(
    monkeypatch,
):
    state = _state(
        code="123456",
        status="HOLDING",
        buy_qty=5,
        cum_buy_qty=5,
        avg_buy_price=10_000,
        sell_ord_no="0000002",
    )
    snapshots = iter(
        (
            (
                {"qty": 5, "avg_price": 10_000},
                (
                    {
                        "code": "123456",
                        "side": "SELL",
                        "qty": 5,
                        "remaining_qty": 5,
                        "ord_no": "0000002",
                    },
                ),
                "exact",
            ),
            RuntimeError("stop after ownership block"),
        )
    )
    reasons = []
    sell_calls = []

    def snapshot(_code):
        value = next(snapshots)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(s15, "_s15_inventory_and_orders", snapshot)
    monkeypatch.setattr(
        s15, "_reconcile_s15_positive_inventory_owner", lambda *args: True
    )
    monkeypatch.setattr(
        s15,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: sell_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        s15,
        "_persist_fast_state",
        lambda _code, current: reasons.append(current.get("s15_recovery_reason"))
        or True,
    )
    monkeypatch.setattr(s15.time, "sleep", lambda _seconds: None)

    s15._recover_s15_custody("123456", state)

    assert sell_calls == []
    assert "open_sell_without_pending_generation" in reasons


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
