"""Exact broker terminal proof must precede another initial BUY leg."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.initial_quantity_terminal import (
    prove_initial_buy_leg_terminal,
)


def test_sequential_bundle_owns_timeout_without_legacy_ttl(monkeypatch):
    from src.engine import sniper_state_handlers as handler

    monkeypatch.setattr(handler, "_decorate_entry_split_leg_ttls",
                        lambda *_args: pytest.fail("legacy TTL on sequential BUY"))
    monkeypatch.setattr(handler, "_resolve_buy_order_timeout_sec",
                        lambda *_args: pytest.fail("legacy timeout on sequential BUY"))
    order = {"initial_quantity_sequential_continuation": {
        "total_wait_sec": 61, "planned_legs": [{}, {}]}}
    context = {}
    assert handler._bind_initial_buy_timeout_owner(
        [order], {}, "SCALPING", context, sequential=True) == [order]
    assert "split_leg_ttl_sec" not in order
    assert context == {
        "order_leg_ttl_sec": [31],
        "order_bundle_hard_ttl_sec": 61,
        "order_timeout_owner": "initial_quantity_bundle_timeout_schedule",
    }
    with pytest.raises(ValueError, match="immediate_leg_count"):
        handler._bind_initial_buy_timeout_owner(
            [order, order], {}, "SCALPING", {}, sequential=True)


def _row(order_no: str, *, qty: str, filled: str, remaining: str,
         original: str = "0000000", confirmed: str = "0",
         confirmation_time: str = "") -> dict:
    return {"source_api": "kt00007", "trade_date": "20260928",
            "trade_date_contract_valid": True, "code": "005930",
            "code_contract_valid": True, "ord_no": order_no,
            "order_no_contract_valid": True, "orig_ord_no": original,
            "side": "매수", "side_contract_valid": True,
            "route_contract_valid": True, "stex_tp": "1", "sor_yn": "N",
            "raw": {"ord_qty": qty, "cntr_qty": filled,
                    "ord_remnq": remaining, "cnfm_qty": confirmed,
                    "cnfm_tm": confirmation_time,
                    "mdfy_cncl": "취소" if original != "0000000" else "",
                    "io_tp_nm": "현금매수취소" if original != "0000000"
                    else "현금매수"}}


def _input(*, cancel: bool = True) -> dict:
    rows = [_row("0000123", qty="0000000004", filled="1", remaining="0")]
    if cancel:
        rows.append(_row("0000124", qty="3", filled="0", remaining="0",
                         original="0000123", confirmed="3",
                         confirmation_time="09:31:20"))
    else:
        rows[0]["raw"]["cntr_qty"] = "4"
    observed = datetime(2026, 9, 28, 9, 31, 21,
                        tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    return {"order_date": "2026-09-28", "stock_code": "005930",
            "route": "KRX", "order_no": "0000123", "ordered_qty": 4,
            "cancel_order_no": "0000124" if cancel else None,
            "dated_rows": rows,
            "dated_meta": {"request_succeeded": True,
                           "normalization_contract_complete": True},
            "current_rows": [],
            "current_meta": {"request_succeeded": True,
                             "normalization_contract_complete": True},
            "observed_at_epoch": observed, "now_epoch": observed + .5}


def test_partial_buy_requires_positive_confirmed_cancel_child_and_current_absence():
    args = _input()
    proof = prove_initial_buy_leg_terminal(**args)
    assert proof is not None
    assert (proof["ordered_qty"], proof["filled_qty"],
            proof["cancelled_qty"], proof["broker_unfilled_qty"]) == (4, 1, 3, 0)
    assert proof["proof_sha256"] == prove_initial_buy_leg_terminal(**args)["proof_sha256"]
    for mutation in (
        lambda x: x["dated_rows"][1]["raw"].update(cnfm_qty="0"),
        lambda x: x["dated_rows"][1]["raw"].update(cnfm_qty="2"),
        lambda x: x["dated_rows"][1]["raw"].update(cnfm_tm=""),
        lambda x: x["dated_rows"][1]["raw"].update(mdfy_cncl="정정"),
        lambda x: x["dated_rows"][1]["raw"].update(io_tp_nm="현금매수정정"),
        lambda x: x["dated_rows"][1].update(orig_ord_no="0000999"),
        lambda x: x["dated_rows"][0]["raw"].update(cntr_qty="2"),
        lambda x: x["current_rows"].append({"ord_no": "0000123"}),
        lambda x: x["current_rows"].append({"ord_no": "0000124"}),
        lambda x: x["dated_rows"][0].update(stex_tp="NXT"),
        lambda x: x["dated_rows"][0].update(raw=["invalid"]),
        lambda x: x["dated_meta"].update(unserializable={1, 2}),
        lambda x: x["dated_rows"].append({"ord_no": "0000125",
                                           "orig_ord_no": "0000123"}),
        lambda x: x["dated_meta"].update(normalization_contract_complete=False),
        lambda x: x.update(now_epoch=x["observed_at_epoch"] + 3),
    ):
        altered = deepcopy(args)
        mutation(altered)
        assert prove_initial_buy_leg_terminal(**altered) is None


def test_full_fill_needs_exact_date_and_no_open_child():
    args = _input(cancel=False)
    proof = prove_initial_buy_leg_terminal(**args)
    assert proof is not None
    assert (proof["filled_qty"], proof["cancelled_qty"]) == (4, 0)
    args["order_date"] = "2026-09-29"
    assert prove_initial_buy_leg_terminal(**args) is None


def test_unrelated_current_buy_does_not_hide_exact_terminal():
    args = _input()
    args["current_rows"].append({"ord_no": "0000456",
                                 "orig_ord_no": "0000000"})
    assert prove_initial_buy_leg_terminal(**args) is not None


def test_sor_route_requires_explicit_broker_router_flag():
    args = _input()
    args["route"] = "SOR"
    for row in args["dated_rows"]:
        row["sor_yn"] = "Y"
    assert prove_initial_buy_leg_terminal(**args) is not None
    args["dated_rows"][1]["sor_yn"] = "N"
    assert prove_initial_buy_leg_terminal(**args) is None


def test_broker_reader_uses_exact_buy_date_and_complete_unfilled_census():
    from src.engine.scalping.initial_quantity_terminal import (
        read_initial_buy_leg_terminal,
    )
    args = _input()
    calls = []

    class Client:
        def get_order_reference_snapshot_kt00007_with_meta(self, token, **kwargs):
            calls.append(("dated", token, kwargs))
            return args["dated_rows"], args["dated_meta"]

        def get_unfilled_order_snapshot_ka10075_with_meta(self, token, **kwargs):
            calls.append(("current", token, kwargs))
            return args["current_rows"], args["current_meta"]

    ticks = iter((args["observed_at_epoch"] - 1,
                  args["observed_at_epoch"],
                  args["now_epoch"]))
    proof, state = read_initial_buy_leg_terminal(
        token="test-token", order_date=args["order_date"],
        stock_code=args["stock_code"], route=args["route"],
        order_no=args["order_no"], ordered_qty=args["ordered_qty"],
        cancel_order_no=args["cancel_order_no"],
        client=Client(), clock=lambda: next(ticks))
    assert state == "broker_terminal_proved" and proof is not None
    assert calls[0][2] == {"ord_dt": "20260928", "qry_tp": "1",
                           "stk_bond_tp": "1", "sell_tp": "2",
                           "stk_cd": "005930", "fr_ord_no": "",
                           "dmst_stex_tp": "%"}
    assert calls[1][2] == {"stk_cd": "005930", "all_stk_tp": "1",
                           "trde_tp": "2", "stex_tp": "0"}


def test_main_terminal_bridge_requires_exact_owner_and_inventory(monkeypatch):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_terminal as broker_reader
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule, next_bundle_timeout_action,
    )
    from src.engine.scalping.initial_quantity_bundle_state import (
        SCHEMA_DYNAMIC_PRICE, new_bundle_state, next_bundle_state,
    )

    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    bundle = new_bundle_state(
        attempt_id="attempt-1", code="005930", target_id="101",
        schedule=schedule, requested_qty=5,
        planned_legs=[{"leg_index": 0, "qty": 4, "price": 10000,
                       "route": "KRX", "tag": "primary"},
                      {"leg_index": 1, "qty": 1, "price": 9990,
                       "route": "KRX", "tag": "passive"}])
    bundle = next_bundle_state(bundle, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    bundle = next_bundle_state(bundle, 0, {
        "state": "OPEN", "broker_order_no": "0000123",
        "submit_intent_at_epoch": start})
    bundle = next_bundle_state(bundle, 0, {
        "state": "CANCEL_REQUESTED", "broker_order_no": "0000123",
        "submit_intent_at_epoch": start})
    stock = {"id": 101, "entry_filled_qty": 1,
             "initial_quantity_bundle": bundle}
    order = {"ord_no": "0000123", "qty": 4, "price": 10000,
             "tag": "primary", "filled_qty": 1,
             "sent_at": start + 1, "dmst_stex_tp": "KRX",
             "dmst_stex_tp_source": "request",
             "initial_quantity_leg_index": 0,
             "entry_submit_attempt_id": "attempt-1",
             "cancel_acknowledged_at": start + 18,
             "cancel_ack_order_no": "0000124"}
    broker = prove_initial_buy_leg_terminal(**_input())
    assert broker is not None
    monkeypatch.setattr(handler, "KIWOOM_TOKEN", "fake-token")
    monkeypatch.setattr(broker_reader, "read_initial_buy_leg_terminal",
                        lambda **_kwargs: (broker, "broker_terminal_proved"))
    monkeypatch.setattr(handler, "main_owner_context",
                        lambda *_args, **_kwargs: object())

    class Registry:
        registered = True
        owners = {"0000123", "0000124"}

        def symbol_registered(self, _code):
            return self.registered

        def order_owner(self, *, order_date, broker_order_no):
            assert order_date.isoformat() == "2026-09-28"
            return {"intent_id": broker_order_no} if broker_order_no in self.owners else None

        def assert_owner(self, **_kwargs):
            return {"state": "ORDER_TERMINAL",
                    "broker_order_no": _kwargs["broker_order_no"]}

    registry = Registry()
    monkeypatch.setattr(handler, "default_order_owner_registry", lambda: registry)
    custody = {"pass": True}
    monkeypatch.setattr(handler, "_order_terminal_inventory_reconciliation",
                        lambda *_args, **_kwargs: (
                            custody["pass"], "terminal_absence_and_owner_inventory_exact" if custody["pass"]
                            else "inventory_unverified", 1 if custody["pass"] else None))

    terminal, status = handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)
    assert status == "initial_quantity_leg_terminal_proved"
    assert terminal["state"] == "TERMINAL_CANCELLED"
    assert (terminal["ordered_qty"], terminal["filled_qty"],
            terminal["cancelled_qty"]) == (4, 1, 3)
    order["qty"] = 5
    assert handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)[0] is None
    order["qty"] = 4
    order["price"] = 9990
    assert handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)[0] is None
    order["price"] = 10000
    states = [terminal, {"state": "NOT_SUBMITTED"}]
    assert next_bundle_timeout_action(schedule, states,
                                      now_epoch=start + 32)["action"] == "SUBMIT"

    # The real dynamic-price dispatcher persists this exact terminal state.
    # Dropping its durable owner intent would strand every successor leg.
    dynamic = new_bundle_state(
        attempt_id="attempt-1", code="005930", target_id="101",
        schedule=schedule, requested_qty=5, schema=SCHEMA_DYNAMIC_PRICE,
        planned_legs=[{"leg_index": 0, "qty": 4, "price": 0,
                       "route": "KRX", "tag": "primary"},
                      {"leg_index": 1, "qty": 1, "price": 0,
                       "route": "KRX", "tag": "passive"}])
    dynamic = next_bundle_state(dynamic, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start,
        "submit_price": 10000, "owner_client_intent_id": "main:attempt-1:leg0"})
    dynamic = next_bundle_state(dynamic, 0, {
        **dynamic["leg_states"][0], "state": "OPEN",
        "broker_order_no": "0000123"})
    dynamic = next_bundle_state(dynamic, 0, {
        **dynamic["leg_states"][0], "state": "CANCEL_REQUESTED"})
    stock["initial_quantity_bundle"] = dynamic
    terminal_dynamic, status = handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)
    assert status == "initial_quantity_leg_terminal_proved"
    assert terminal_dynamic["owner_client_intent_id"] == "main:attempt-1:leg0"
    committed = next_bundle_state(dynamic, 0, terminal_dynamic)
    assert next_bundle_timeout_action(schedule, committed["leg_states"],
                                      now_epoch=start + 32)["action"] == "SUBMIT"
    stock["initial_quantity_bundle"] = bundle

    registry.owners.remove("0000124")
    assert handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)[0] is None
    registry.owners.add("0000124")
    custody["pass"] = False
    assert handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)[0] is None
    custody["pass"] = True
    order["cancel_ack_order_no"] = ""
    assert handler._initial_quantity_buy_leg_terminal_state(
        stock, "005930", order, now_ts=start + 20)[0] is None


def test_scheduled_cancel_path_blocks_unproved_terminal(monkeypatch, tmp_path):
    import time
    from datetime import timedelta

    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state, next_bundle_state,
        read_bundle_state, save_bundle_state_cas,
    )

    start = time.time() - 10
    start_clock = datetime.fromtimestamp(start, ZoneInfo("Asia/Seoul"))
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at=(start_clock - timedelta(seconds=10)).isoformat(),
        order_start_at=start_clock.isoformat(), total_wait_sec=60,
        leg_count=2, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    order = {"tag": "primary", "qty": 4, "filled_qty": 1, "price": 10000,
             "ord_no": "0000123", "status": "OPEN", "sent_at": start + 1,
             "dmst_stex_tp": "KRX", "dmst_stex_tp_source": "request",
             "initial_quantity_leg_index": 0,
             "entry_submit_attempt_id": "attempt-1"}
    bundle = new_bundle_state(
        attempt_id="attempt-1", code="005930", target_id="101",
        schedule=schedule, requested_qty=5,
        planned_legs=[{"leg_index": 0, "qty": 4, "price": 10000,
                       "route": "KRX", "tag": "primary"},
                      {"leg_index": 1, "qty": 1, "price": 9990,
                       "route": "KRX", "tag": "passive"}])
    journal = bundle_state_path(
        tmp_path / "runtime" / "initial_quantity" / "bundles", "attempt-1")
    save_bundle_state_cas(journal, bundle, expected_parent_sha256=None)
    intent = next_bundle_state(bundle, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    save_bundle_state_cas(journal, intent,
                          expected_parent_sha256=bundle["bundle_content_sha256"])
    bundle = next_bundle_state(intent, 0,
                               {"state": "OPEN", "broker_order_no": "0000123",
                                "submit_intent_at_epoch": start})
    save_bundle_state_cas(journal, bundle,
                          expected_parent_sha256=intent["bundle_content_sha256"])
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    stock = {"id": 101, "strategy": "SCALPING", "name": "TEST",
             "entry_filled_qty": 1, "buy_qty": 1,
             "pending_entry_orders": [order],
             "initial_quantity_bundle": bundle}
    cancel_calls = []
    monkeypatch.setattr(handler.kiwoom_orders, "send_cancel_order",
                        lambda **kwargs: (cancel_calls.append(kwargs) or
                                          {"return_code": "0", "ord_no": "0000124"}))
    monkeypatch.setattr(handler, "_log_entry_pipeline", lambda *_a, **_kw: None)
    monkeypatch.setattr(handler, "_log_holding_pipeline", lambda *_a, **_kw: True)
    monkeypatch.setattr(handler, "_request_broker_snapshot_refresh",
                        lambda *_a, **_kw: None)
    monkeypatch.setattr(handler, "_order_terminal_inventory_reconciliation",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            AssertionError("scheduled_path_must_use_exact_bridge")))
    evidence = {"valid": False}

    def terminal(*_args, **_kwargs):
        if not evidence["valid"]:
            return None, "broker_terminal_unproved"
        return ({"state": "TERMINAL_CANCELLED", "terminal_confirmed": True,
                 "terminal_confirmed_at_epoch": start + 5,
                 "submit_intent_at_epoch": start,
                 "broker_order_no": "0000123",
                 "broker_terminal_receipt_id": "broker-proof",
                 "owner_registry_receipt_id": "owner-proof",
                 "account_position_receipt_id": "account-proof",
                 "broker_unfilled_qty": 0, "owner_registry_terminal": True,
                 "account_position_reconciled": True, "ordered_qty": 4,
                 "filled_qty": 1, "cancelled_qty": 3},
                "initial_quantity_leg_terminal_proved")

    monkeypatch.setattr(handler, "_initial_quantity_buy_leg_terminal_state", terminal)
    original_persist = handler._initial_quantity_persist_leg_transition
    monkeypatch.setattr(
        handler, "_initial_quantity_persist_leg_transition",
        lambda *_a: (False, "injected_disk_failure"),
    )
    assert handler._cancel_pending_entry_orders(
        stock, "005930", force=True, now_ts=start + 9) == "failed"
    assert cancel_calls == []
    assert read_bundle_state(journal) == bundle
    monkeypatch.setattr(handler, "_initial_quantity_persist_leg_transition",
                        original_persist)
    assert handler._cancel_pending_entry_orders(
        stock, "005930", force=True, now_ts=start + 10) == "pending"
    assert order["status"] == "OPEN"
    order.pop("cancel_terminal_pending")
    assert handler._cancel_pending_entry_orders(
        stock, "005930", force=True, now_ts=start + 10) == "failed"
    assert len(cancel_calls) == 1
    order["cancel_terminal_pending"] = True
    evidence["valid"] = True
    assert handler._cancel_pending_entry_orders(
        stock, "005930", force=True, now_ts=start + 11) == "partial_cancelled"
    assert len(cancel_calls) == 1
    assert stock["initial_quantity_bundle"]["leg_states"][0]["state"] == "TERMINAL_CANCELLED"
    assert read_bundle_state(journal) == stock["initial_quantity_bundle"]
    assert stock["entry_filled_qty"] == 1


def test_missing_local_orders_preserves_unfinished_bundle(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_bundle_state import new_bundle_state
    from src.engine.scalping.initial_quantity_timeout import build_bundle_timeout_schedule

    refreshes = []
    monkeypatch.setattr(handler, "_request_broker_snapshot_refresh",
                        lambda *args, **kwargs: refreshes.append((args, kwargs)))
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=1, cancel_confirm_reserve_sec=5)
    bundle = new_bundle_state(
        attempt_id="missing-local-order", code="005930", target_id="101",
        schedule=schedule, requested_qty=4,
        planned_legs=[{"leg_index": 0, "qty": 4, "price": 10000,
                       "route": "KRX", "tag": "primary"}])
    stock = {"id": 101, "initial_quantity_bundle": bundle,
             "pending_entry_orders": [], "entry_requested_qty": 4}
    assert handler._cancel_pending_entry_orders(
        stock, "005930", force=True) == "pending"
    assert stock["entry_requested_qty"] == 4
    assert stock["initial_quantity_bundle"] == bundle
    assert refreshes


def test_full_fill_during_cancel_reconciliation_keeps_filled_status(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state, next_bundle_state, save_bundle_state_cas,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    bundle = new_bundle_state(
        attempt_id="attempt-full", code="005930", target_id="101",
        schedule=schedule, requested_qty=5,
        planned_legs=[{"leg_index": 0, "qty": 4, "price": 10000,
                       "route": "KRX", "tag": "primary"},
                      {"leg_index": 1, "qty": 1, "price": 9990,
                       "route": "KRX", "tag": "passive"}])
    path = bundle_state_path(
        tmp_path / "runtime" / "initial_quantity" / "bundles", "attempt-full")
    save_bundle_state_cas(path, bundle, expected_parent_sha256=None)
    for state in (
        {"state": "SUBMIT_INTENT", "submit_intent_at_epoch": start},
        {"state": "OPEN", "broker_order_no": "0000123",
         "submit_intent_at_epoch": start},
        {"state": "CANCEL_REQUESTED", "broker_order_no": "0000123",
         "submit_intent_at_epoch": start},
    ):
        successor = next_bundle_state(bundle, 0, state)
        save_bundle_state_cas(path, successor,
                              expected_parent_sha256=bundle["bundle_content_sha256"])
        bundle = successor
    order = {"tag": "primary", "qty": 4, "filled_qty": 4, "price": 10000,
             "ord_no": "0000123", "status": "OPEN", "sent_at": start + 1,
             "dmst_stex_tp": "KRX", "dmst_stex_tp_source": "request",
             "initial_quantity_leg_index": 0,
             "entry_submit_attempt_id": "attempt-full",
             "cancel_terminal_pending": True, "cancel_ack_order_no": "0000124"}
    stock = {"id": 101, "strategy": "SCALPING", "name": "TEST",
             "entry_filled_qty": 4, "buy_qty": 4,
             "pending_entry_orders": [order], "initial_quantity_bundle": bundle}
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler, "_log_entry_pipeline", lambda *_a, **_kw: None)
    monkeypatch.setattr(handler, "_log_holding_pipeline", lambda *_a, **_kw: True)
    monkeypatch.setattr(handler.time, "time", lambda: start + 10)
    monkeypatch.setattr(handler, "_initial_quantity_buy_leg_terminal_state",
                        lambda *_a, **_kw: (
                            {"state": "TERMINAL_FILLED", "terminal_confirmed": True,
                             "terminal_confirmed_at_epoch": start + 5,
                             "submit_intent_at_epoch": start,
                             "broker_order_no": "0000123",
                             "broker_terminal_receipt_id": "broker-proof",
                             "owner_registry_receipt_id": "owner-proof",
                             "account_position_receipt_id": "account-proof",
                             "broker_unfilled_qty": 0,
                             "owner_registry_terminal": True,
                             "account_position_reconciled": True,
                             "ordered_qty": 4, "filled_qty": 4,
                             "cancelled_qty": 0}, "proved"))
    assert handler._cancel_pending_entry_orders(
        stock, "005930", force=True, now_ts=start + 10) == "pending"
    assert order["status"] == "FILLED"
    assert "cancelled_at" not in order
    assert stock["initial_quantity_bundle"]["leg_states"][0]["state"] == (
        "TERMINAL_FILLED")


def test_full_fill_before_deadline_requires_exact_terminal_before_finishing_leg(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state, next_bundle_state,
        read_bundle_state, save_bundle_state_cas,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=1, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    bundle = new_bundle_state(
        attempt_id="full-before-deadline", code="005930", target_id="101",
        schedule=schedule, requested_qty=2,
        planned_legs=[{"leg_index": 0, "qty": 2, "price": 10000,
                       "route": "KRX", "tag": "primary"}])
    path = bundle_state_path(
        tmp_path / "runtime" / "initial_quantity" / "bundles",
        bundle["attempt_id"])
    save_bundle_state_cas(path, bundle, expected_parent_sha256=None)
    for state in ({"state": "SUBMIT_INTENT", "submit_intent_at_epoch": start},
                  {"state": "OPEN", "submit_intent_at_epoch": start,
                   "broker_order_no": "0000123"}):
        successor = next_bundle_state(bundle, 0, state)
        save_bundle_state_cas(path, successor,
                              expected_parent_sha256=bundle["bundle_content_sha256"])
        bundle = successor
    order = {"tag": "primary", "qty": 2, "filled_qty": 2,
             "price": 10000, "ord_no": "0000123", "status": "OPEN",
             "dmst_stex_tp": "KRX", "dmst_stex_tp_source": "request",
             "sent_at": start + 1, "initial_quantity_leg_index": 0,
             "entry_submit_attempt_id": bundle["attempt_id"]}
    stock = {"id": 101, "initial_quantity_bundle": bundle,
             "pending_entry_orders": [order]}
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler.time, "time", lambda: start + 5)
    proof = [None]
    monkeypatch.setattr(handler, "_initial_quantity_buy_leg_terminal_state",
                        lambda *_a, **_kw: (proof[0], "source_gap"))
    handler._reconcile_pending_entry_orders(stock, "005930", "SCALPING")
    assert read_bundle_state(path) == bundle
    assert order["status"] == "OPEN"
    proof[0] = {"state": "TERMINAL_FILLED", "terminal_confirmed": True,
                "terminal_confirmed_at_epoch": start + 6,
                "submit_intent_at_epoch": start,
                "broker_order_no": "0000123",
                "broker_terminal_receipt_id": "broker-proof",
                "owner_registry_receipt_id": "owner-proof",
                "account_position_receipt_id": "account-proof",
                "broker_unfilled_qty": 0, "owner_registry_terminal": True,
                "account_position_reconciled": True,
                "ordered_qty": 2, "filled_qty": 2, "cancelled_qty": 0}
    monkeypatch.setattr(handler.time, "time", lambda: start + 6)
    handler._reconcile_pending_entry_orders(stock, "005930", "SCALPING")
    assert order["status"] == "FILLED"
    assert read_bundle_state(path) == stock["initial_quantity_bundle"]
    assert stock["initial_quantity_bundle"]["leg_states"][0]["state"] == (
        "TERMINAL_FILLED")


def test_buy_ordered_uses_bundle_deadline_before_legacy_timeout(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state, next_bundle_state, save_bundle_state_cas,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    bundle = new_bundle_state(
        attempt_id="attempt-2", code="005930", target_id="102",
        schedule=schedule, requested_qty=4,
        planned_legs=[{"leg_index": 0, "qty": 1, "price": 10000,
                       "route": "KRX", "tag": "first"},
                      {"leg_index": 1, "qty": 3, "price": 9990,
                       "route": "KRX", "tag": "second"}])
    path = bundle_state_path(tmp_path / "runtime" / "initial_quantity" / "bundles",
                             bundle["attempt_id"])
    save_bundle_state_cas(path, bundle, expected_parent_sha256=None)
    for state in ({"state": "SUBMIT_INTENT", "submit_intent_at_epoch": start},
                  {"state": "OPEN", "broker_order_no": "0000123",
                   "submit_intent_at_epoch": start}):
        successor = next_bundle_state(bundle, 0, state)
        save_bundle_state_cas(path, successor,
                              expected_parent_sha256=bundle["bundle_content_sha256"])
        bundle = successor
    stock = {"id": 102, "name": "TEST", "strategy": "SCALPING",
             "status": "BUY_ORDERED", "order_time": start,
             "initial_quantity_bundle": bundle,
             "pending_entry_orders": [{"ord_no": "0000123", "status": "OPEN"}]}
    cancel_calls = []
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler.time, "time", lambda: start + 26)
    monkeypatch.setattr(handler, "_manual_control_exclusion_blocked",
                        lambda *_a, **_kw: False)
    monkeypatch.setattr(handler, "_resolve_buy_order_timeout_sec",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            AssertionError("legacy_timeout_must_not_own_bundle")))
    monkeypatch.setattr(handler, "_cancel_pending_entry_orders",
                        lambda *_a, **kw: cancel_calls.append(kw) or "pending")
    handler.handle_buy_ordered_state(stock, "005930")
    assert len(cancel_calls) == 1
    assert cancel_calls[0]["cancel_reason"] == "initial_quantity_bundle_leg_deadline"


def test_uncertain_bundle_submit_refreshes_snapshot_without_retrying_buy(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state, next_bundle_state, save_bundle_state_cas,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=1, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    bundle = new_bundle_state(
        attempt_id="uncertain-attempt", code="005930", target_id="102",
        schedule=schedule, requested_qty=1,
        planned_legs=[{"leg_index": 0, "qty": 1, "price": 10000,
                       "route": "KRX", "tag": "first"}])
    path = bundle_state_path(tmp_path / "runtime" / "initial_quantity" / "bundles",
                             bundle["attempt_id"])
    save_bundle_state_cas(path, bundle, expected_parent_sha256=None)
    intent = next_bundle_state(bundle, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    save_bundle_state_cas(path, intent,
                          expected_parent_sha256=bundle["bundle_content_sha256"])
    bundle = intent
    stock = {"id": 102, "initial_quantity_bundle": bundle}
    refreshes = []
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler.time, "time", lambda: start + 1)
    monkeypatch.setattr(handler, "_request_broker_snapshot_refresh",
                        lambda *_a, **kw: refreshes.append(kw))
    monkeypatch.setattr(handler, "_cancel_pending_entry_orders",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            AssertionError("uncertain_submit_must_not_cancel")))
    handler._reconcile_pending_entry_orders(stock, "005930", "SCALPING")
    handler._reconcile_pending_entry_orders(stock, "005930", "SCALPING")
    assert len(refreshes) == 1
    assert refreshes[0]["reason"] == "initial_quantity_submit_or_terminal_uncertain"


def test_cancel_requested_bundle_reenters_terminal_proof_without_new_buy(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state, next_bundle_state, save_bundle_state_cas,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=1, cancel_confirm_reserve_sec=5)
    start = schedule["order_start_at_epoch"]
    bundle = new_bundle_state(
        attempt_id="cancel-pending-attempt", code="005930", target_id="102",
        schedule=schedule, requested_qty=1,
        planned_legs=[{"leg_index": 0, "qty": 1, "price": 10000,
                       "route": "KRX", "tag": "first"}])
    path = bundle_state_path(tmp_path / "runtime" / "initial_quantity" / "bundles",
                             bundle["attempt_id"])
    save_bundle_state_cas(path, bundle, expected_parent_sha256=None)
    for state in ({"state": "SUBMIT_INTENT", "submit_intent_at_epoch": start},
                  {"state": "OPEN", "submit_intent_at_epoch": start,
                   "broker_order_no": "0000123"},
                  {"state": "CANCEL_REQUESTED", "submit_intent_at_epoch": start,
                   "broker_order_no": "0000123"}):
        successor = next_bundle_state(bundle, 0, state)
        save_bundle_state_cas(path, successor,
                              expected_parent_sha256=bundle["bundle_content_sha256"])
        bundle = successor
    stock = {"id": 102, "initial_quantity_bundle": bundle,
             "pending_entry_orders": [{"ord_no": "0000123", "status": "OPEN"}]}
    calls = []
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler.time, "time", lambda: start + 56)
    monkeypatch.setattr(handler, "_cancel_pending_entry_orders",
                        lambda *_a, **kw: calls.append(kw) or "pending")
    monkeypatch.setattr(handler, "_request_broker_snapshot_refresh",
                        lambda *_a, **_kw: None)
    handler._reconcile_pending_entry_orders(stock, "005930", "SCALPING")
    assert len(calls) == 1


def test_unfinished_bundle_cannot_fall_into_parallel_legacy_submit(monkeypatch):
    from src.engine import sniper_state_handlers as handler

    stages = []
    monkeypatch.setattr(handler, "_log_entry_pipeline",
                        lambda _stock, _code, stage, **_fields: stages.append(stage))
    monkeypatch.setattr(handler.kiwoom_orders, "get_deposit",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            AssertionError("legacy_submit_must_not_query_deposit")))
    monkeypatch.setattr(handler.kiwoom_orders, "send_buy_order",
                        lambda *_a, **_kw: (_ for _ in ()).throw(
                            AssertionError("legacy_submit_must_not_send_buy")))
    stock = {"id": 101, "strategy": "SCALPING",
             "initial_quantity_bundle": {"schema": "pending"}}
    assert handler._submit_watching_triggered_entry(
        stock, "005930", {}, 1, {"strategy": "SCALPING"}) is False
    assert "initial_quantity_sequential_dispatcher_missing" in stages


def test_first_sequential_buy_intent_is_durable_before_broker_response(
    monkeypatch, tmp_path,
):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.entry_split_order_plan import (
        build_initial_quantity_type_legs,
    )
    from src.engine.scalping.initial_quantity_bundle_state import (
        read_bundle_for_target,
    )

    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler, "submit_attempt_machine_lineage",
                        lambda *_args: {"evaluation_attempt_id": "attempt-1"})
    monkeypatch.setattr(handler, "_request_broker_snapshot_refresh",
                        lambda *_a, **_kw: None)
    class Registry:
        def symbol_registered(self, _code):
            return True

        def assert_owner(self, *, context, order_date, broker_order_no):
            assert str(order_date) == "2026-09-28"
            assert broker_order_no == "0000123"
            return {"client_intent_id": context.client_intent_id}

    monkeypatch.setattr(handler, "default_order_owner_registry",
                        lambda: Registry())
    from types import SimpleNamespace
    owner = SimpleNamespace(client_intent_id="main_scalping:101:attempt-1")
    legs = build_initial_quantity_type_legs(
        total_qty=5, selected_shape="two_leg_0_1tick",
        probe_first=False, route="KRX")
    first = {"tag": legs[0]["tag"],
             "initial_quantity_sequential_continuation": {
                 "planned_legs": legs, "requested_qty": 5,
                 "quantity_type": "KRX_PARENT", "policy_file_sha256": "a" * 64,
                 "total_wait_sec": 60,
                 "decision_at": "2026-09-28T09:29:50+09:00"}}
    clock = datetime.fromisoformat("2026-09-28T09:30:00+09:00").timestamp()
    stock = {"id": 101, "status": "WATCHING"}
    intent, status = handler._initial_quantity_prepare_first_submit(
        stock, "005930", first, qty=legs[0]["qty"],
        broker_price=10000, submit_price=10000,
        route="KRX", now_ts=clock,
        owner_context=owner)
    assert status == "first_submit_intent_persisted"
    assert intent["leg_states"][0]["state"] == "SUBMIT_INTENT"
    assert intent["leg_states"][0]["owner_client_intent_id"] == owner.client_intent_id
    assert stock["status"] == "BUY_ORDERED"
    assert read_bundle_for_target(
        tmp_path / "runtime" / "initial_quantity" / "bundles",
        "005930", "101") == (intent, "target_bundle_loaded")
    assert handler._initial_quantity_record_submit_response(
        stock, "005930", leg_index=0,
        response={"return_code": "0", "ord_no": "0000123",
                  "broker_route": "KRX"}, expected_route="KRX",
        owner_context=owner) == (
                      True, "initial_quantity_submit_open_persisted")
    assert stock["initial_quantity_bundle"]["leg_states"][0]["state"] == "OPEN"


def test_selected_type_sequential_plan_preserves_sizing_lineage(monkeypatch):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_activation as activation

    monkeypatch.setenv(activation.ENV_FILE, "/tmp/selected-initial-v2.json")
    monkeypatch.setenv(activation.ENV_SHA, "a" * 64)
    monkeypatch.setattr(activation, "load_pinned_initial_quantity_policy",
                        lambda *_args: ({
                            "schema_version": activation.RUNTIME_V2_SCHEMA,
                            "policy_content_sha256": "b" * 64,
                            "type_policies": {"KRX_PARENT": {
                                "selected_shape": "two_leg_0_1tick",
                                "timeout_mode": "existing_runtime_profile",
                                "selected_total_wait_sec": None,
                            }},
                        }, "initial_policy_v2_loaded"))
    monkeypatch.setattr(handler, "_entry_cancel_wait_profile_base_sec",
                        lambda _stock: ("standard", 90))
    stock = {
        "scalping_sizing_quantity_type": "KRX_PARENT",
        "scalping_sizing_quantity_type_policy_row": "KRX_PARENT",
        "scalping_sizing_position_sizing_policy_sha256": "a" * 64,
        "scalping_sizing_reference_time": "2026-09-28T09:29:50+09:00",
        "effective_venue": "KRX",
    }
    first = {"qty": 5, "price": 10000, "tag": "old",
             "dmst_stex_tp": "KRX"}
    orders, fields = handler._initial_quantity_sequential_plan(
        stock, [first], 5, {})
    continuation = orders[0]["initial_quantity_sequential_continuation"]
    assert orders[0]["qty"] == 3
    assert continuation["residual_quantities"] == [2]
    assert continuation["total_wait_sec"] == 90
    assert fields["initial_quantity_selected_shape"] == "two_leg_0_1tick"
    stock["scalping_sizing_position_sizing_policy_sha256"] = "c" * 64
    import pytest
    with pytest.raises(ValueError, match="lineage_mismatch"):
        handler._initial_quantity_sequential_plan(stock, [first], 5, {})


def test_selected_probe_is_one_market_leg_with_durable_guard_price(
    monkeypatch, tmp_path,
):
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_activation as activation

    monkeypatch.setenv(activation.ENV_FILE, str(tmp_path / "selected.json"))
    monkeypatch.setenv(activation.ENV_SHA, "a" * 64)
    monkeypatch.setattr(activation, "load_pinned_initial_quantity_policy",
                        lambda *_args: ({
                            "schema_version": activation.RUNTIME_V2_SCHEMA,
                            "policy_content_sha256": "b" * 64,
                            "type_policies": {"KRX_PARENT": {
                                "selected_shape": "two_leg_0_1tick",
                                "timeout_mode": "existing_runtime_profile",
                                "selected_total_wait_sec": None,
                            }},
                        }, "initial_policy_v2_loaded"))
    monkeypatch.setattr(handler, "_entry_cancel_wait_profile_base_sec",
                        lambda _stock: ("standard", 90))
    released = []
    monkeypatch.setattr(handler, "release_unsubmitted_probe_reservation",
                        lambda *args, **_kw: released.extend(args))
    stock = {
        "id": 101, "scalping_sizing_quantity_type": "KRX_PARENT",
        "scalping_sizing_quantity_type_policy_row": "KRX_PARENT",
        "scalping_sizing_position_sizing_policy_sha256": "a" * 64,
        "scalping_sizing_reference_time": "2026-09-28T09:29:50+09:00",
        "effective_venue": "KRX",
    }
    first = {"qty": 5, "price": 10000, "tag": "old_probe",
             "dmst_stex_tp": "KRX",
             "entry_split_order_probe_first_applied": True,
             "entry_split_order_execution_mode": "probe_first_market",
             "entry_split_order_probe_continuation": {"old": True}}
    orders, fields = handler._initial_quantity_sequential_plan(
        stock, [first], 5, {
            "entry_split_order_probe_first_applied": True,
            "entry_split_order_probe_bundle_id": "old-reservation"})
    assert released == ["old-reservation"]
    assert fields["entry_split_order_leg_count"] == 2
    assert orders[0]["qty"] == 1
    assert orders[0]["initial_quantity_probe_market"] is True
    assert "entry_split_order_probe_continuation" not in orders[0]
    request = handler._resolve_live_entry_order_request(
        "SCALPING", orders[0], "00", 10000)
    assert (request["price"], request["guard_price"],
            request["order_type_code"]) == (0, 10000, "3")
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler, "submit_attempt_machine_lineage",
                        lambda *_args: {"evaluation_attempt_id": "probe-attempt"})
    owner = SimpleNamespace(client_intent_id="main_scalping:101:probe-attempt")
    intent, status = handler._initial_quantity_prepare_first_submit(
        stock, "005930", orders[0], qty=1, broker_price=0,
        submit_price=10000, route="KRX", owner_context=owner,
        probe_ai_action="WAIT", probe_wait_contract=True,
        now_ts=datetime.fromisoformat("2026-09-28T09:30:00+09:00").timestamp())
    assert status == "first_submit_intent_persisted"
    assert intent["leg_states"][0]["submit_price"] == 10000
    assert stock["entry_split_probe_ai_action_at_submit"] == "WAIT"


def test_restart_recovers_only_exact_owner_bound_order(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.entry_split_order_plan import (
        build_initial_quantity_type_legs,
    )

    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler, "submit_attempt_machine_lineage",
                        lambda *_args: {"evaluation_attempt_id": "restart-attempt"})
    refreshes = []
    monkeypatch.setattr(handler, "_request_broker_snapshot_refresh",
                        lambda *_a, **kw: refreshes.append(kw))
    legs = build_initial_quantity_type_legs(
        total_qty=4, selected_shape="two_leg_0_1tick",
        probe_first=False, route="KRX")
    order = {"tag": legs[0]["tag"],
             "initial_quantity_sequential_continuation": {
                 "planned_legs": legs, "requested_qty": 4,
                 "quantity_type": "KRX_PARENT", "policy_file_sha256": "a" * 64,
                 "total_wait_sec": 60,
                 "decision_at": "2026-09-28T09:29:50+09:00"}}
    stock = {"id": 101}
    owner = SimpleNamespace(client_intent_id="main_scalping:101:restart-attempt")
    handler._initial_quantity_prepare_first_submit(
        stock, "005930", order, qty=2, broker_price=10000,
        submit_price=10000,
        route="KRX", owner_context=owner,
        now_ts=datetime.fromisoformat("2026-09-28T09:30:00+09:00").timestamp())

    class Registry:
        route = "KRX"

        def intent_for_client(self, *, context):
            assert context.client_intent_id == owner.client_intent_id
            return {"state": "ORDER_BOUND", "order_date": "2026-09-28",
                    "symbol": "005930", "side": "BUY", "action": "NEW",
                    "route": self.route, "quantity": 2,
                    "broker_order_no": "0000123"}

        def assert_owner(self, *, context, order_date, broker_order_no):
            assert broker_order_no == "0000123"
            return {"client_intent_id": context.client_intent_id}

    registry = Registry()
    monkeypatch.setattr(handler, "default_order_owner_registry",
                        lambda: registry)
    registry.route = "NXT"
    assert handler._initial_quantity_recover_submit_owner(
        stock, "005930", leg_index=0) == (
            False, "initial_quantity_owner_intent_identity_invalid")
    registry.route = "KRX"
    assert handler._initial_quantity_recover_submit_owner(
        stock, "005930", leg_index=0) == (
            True, "initial_quantity_owner_exact_order_recovered")
    assert stock["initial_quantity_bundle"]["leg_states"][0]["broker_order_no"] == "0000123"
    assert refreshes[-1]["reason"] == "initial_quantity_owner_exact_order_recovered"


def test_elapsed_unsent_leg_requires_exact_owner_absence(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.entry_split_order_plan import (
        build_initial_quantity_type_legs,
    )
    from src.engine.scalping.initial_quantity_bundle_state import (
        SCHEMA_DYNAMIC_PRICE, create_indexed_bundle, new_bundle_state,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    bundle = new_bundle_state(
        attempt_id="skip-attempt", code="005930", target_id="101",
        schedule=schedule, requested_qty=4,
        planned_legs=build_initial_quantity_type_legs(
            total_qty=4, selected_shape="two_leg_0_1tick",
            probe_first=False, route="KRX"),
        schema=SCHEMA_DYNAMIC_PRICE)
    create_indexed_bundle(
        tmp_path / "runtime" / "initial_quantity" / "bundles", bundle)
    stock = {"id": 101, "initial_quantity_bundle": bundle,
             "pending_entry_orders": []}

    class Registry:
        present = True

        def symbol_registered(self, _code):
            return True

        def intent_for_client(self, *, context):
            return {"client_intent_id": context.client_intent_id} if self.present else None

    registry = Registry()
    monkeypatch.setattr(handler, "default_order_owner_registry",
                        lambda: registry)
    now = schedule["slots"][0]["cancel_request_by_epoch"]
    assert handler._initial_quantity_skip_unsent_leg(
        stock, "005930", leg_index=0, now_ts=now) == (
            False, "initial_quantity_skip_owner_intent_present_or_unavailable")
    registry.present = False
    assert handler._initial_quantity_skip_unsent_leg(
        stock, "005930", leg_index=0, now_ts=now) == (
            True, "initial_quantity_unsent_leg_skipped")
    assert stock["initial_quantity_bundle"]["leg_states"][0]["state"] == (
        "TERMINAL_SKIPPED")


def test_successor_buy_waits_for_terminal_and_uses_fresh_p1_price(
    monkeypatch, tmp_path,
):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_activation as activation
    from src.engine.scalping.entry_split_order_plan import (
        build_initial_quantity_type_legs,
    )
    from src.engine.scalping.initial_quantity_bundle_state import (
        SCHEMA_DYNAMIC_PRICE, bundle_state_path, create_indexed_bundle,
        new_bundle_state, next_bundle_state, persist_dynamic_leg_submit_intent,
        persist_dynamic_leg_submit_response, save_bundle_state_cas,
    )
    from src.engine.scalping.initial_quantity_timeout import (
        build_bundle_timeout_schedule,
    )

    start = datetime.fromisoformat("2026-09-28T09:30:00+09:00").timestamp()
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    legs = build_initial_quantity_type_legs(
        total_qty=2, selected_shape="two_leg_0_1tick",
        probe_first=False, route="KRX")
    initial = new_bundle_state(
        attempt_id="two-leg", code="005930", target_id="101",
        schedule=schedule, requested_qty=2, planned_legs=legs,
        schema=SCHEMA_DYNAMIC_PRICE)
    base = tmp_path / "runtime" / "initial_quantity" / "bundles"
    create_indexed_bundle(base, initial)
    first_owner = "main_scalping:101:first"
    intent = persist_dynamic_leg_submit_intent(
        base, initial, leg_index=0, submit_price=10000,
        owner_client_intent_id=first_owner, now_epoch=start)
    opened = persist_dynamic_leg_submit_response(
        base, intent, leg_index=0, broker_order_no="0000123",
        owner_exact=True)
    terminal = next_bundle_state(opened, 0, {
        **opened["leg_states"][0], "state": "TERMINAL_FILLED",
        "terminal_confirmed": True, "terminal_confirmed_at_epoch": start + 10,
        "broker_terminal_receipt_id": "broker-proof",
        "owner_registry_receipt_id": "owner-proof",
        "account_position_receipt_id": "account-proof",
        "broker_unfilled_qty": 0, "owner_registry_terminal": True,
        "account_position_reconciled": True,
        "ordered_qty": 1, "filled_qty": 1, "cancelled_qty": 0})
    save_bundle_state_cas(
        bundle_state_path(base, initial["attempt_id"]), terminal,
        expected_parent_sha256=opened["bundle_content_sha256"])
    stock = {
        "id": 101, "status": "BUY_ORDERED", "buy_qty": 1,
        "entry_filled_qty": 1, "buy_price": 10000,
        "current_price": 10010, "initial_quantity_bundle": terminal,
        "pending_entry_orders": [{
            "tag": legs[0]["tag"], "qty": 1, "price": 10000,
            "ord_no": "0000123", "status": "FILLED", "filled_qty": 1,
            "initial_quantity_leg_index": 0,
            "entry_submit_attempt_id": "two-leg"}],
    }
    monkeypatch.setattr(handler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handler.time, "time", lambda: start + 31)
    monkeypatch.setattr(handler, "COOLDOWNS", {})
    monkeypatch.setenv(activation.ENV_FILE, str(tmp_path / "policy.json"))
    monkeypatch.setenv(activation.ENV_SHA, "a" * 64)
    monkeypatch.setattr(activation, "load_pinned_initial_quantity_policy",
                        lambda *_args: ({
                            "schema_version": activation.RUNTIME_V2_SCHEMA,
                            "p1_price_policy_sha256": "b" * 64,
                            "type_policies": {"KRX_PARENT": {
                                "selected_shape": "two_leg_0_1tick",
                                "timeout_mode": "existing_runtime_profile",
                                "selected_total_wait_sec": None,
                            }},
                        }, "initial_policy_v2_loaded"))
    monkeypatch.setattr(handler, "_entry_cancel_wait_profile_base_sec",
                        lambda _stock: ("standard", 60))
    monkeypatch.setattr(handler, "is_scalping_buy_time_allowed",
                        lambda *_args: True)
    monkeypatch.setattr(handler, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handler, "_manual_control_exclusion_blocked",
                        lambda *_a, **_kw: False)
    monkeypatch.setattr(handler, "_has_active_sell_order_pending",
                        lambda *_args: False)
    monkeypatch.setattr(handler, "_probe_residual_account_guard_fields",
                        lambda *_a, **_kw: {"account_guard_allowed": True})
    monkeypatch.setattr(handler, "_entry_setup_exploration_submit_cap_guard",
                        lambda *_a, **_kw: {"allowed": True})
    monkeypatch.setattr(handler, "_split_policy_pre_submit_price_guard_fields",
                        lambda *_a, **_kw: {"pre_submit_price_guard_blocked": False})
    monkeypatch.setattr(handler, "_build_quote_consistency_fields",
                        lambda *_a, **_kw: ({
                            "quote_consistency_state": "ok",
                            "quote_consistency_reason": "ws_only_fresh",
                            "passive_buy_price": 10000}, 10000, 10010, 10000))

    class WS:
        def get_latest_data(self, _code):
            return {"ws_route": "KRX", "market_data_transport_epoch": "epoch-1",
                    "curr": 10010}

    monkeypatch.setattr(handler, "WS_MANAGER", WS())
    monkeypatch.setattr(handler.kiwoom_orders, "describe_buy_order_resolution",
                        lambda _type, *, price, **_kw: {
                            "effective_dmst_stex_tp": "KRX",
                            "effective_order_price": price})
    sends = []
    monkeypatch.setattr(handler.kiwoom_orders, "send_buy_order",
                        lambda *args, **kw: (
                            sends.append((args, kw)) or
                            {"return_code": "0", "ord_no": "0000124",
                             "broker_route": "KRX"}))

    class Registry:
        def symbol_registered(self, _code):
            return True

        def assert_owner(self, *, context, order_date, broker_order_no):
            assert broker_order_no == "0000124"
            return {"client_intent_id": context.client_intent_id}

    monkeypatch.setattr(handler, "default_order_owner_registry",
                        lambda: Registry())
    assert handler._initial_quantity_submit_successor_leg(
        stock, "005930", leg_index=1) == (
            True, "initial_quantity_successor_submitted")
    assert len(sends) == 1
    assert sends[0][0][1:4] == (1, 9990, "00")
    assert stock["initial_quantity_bundle"]["leg_states"][1]["state"] == "OPEN"
    assert stock["pending_entry_orders"][-1]["price"] == 9990
    assert handler._initial_quantity_submit_successor_leg(
        stock, "005930", leg_index=1)[0] is False
    assert len(sends) == 1
