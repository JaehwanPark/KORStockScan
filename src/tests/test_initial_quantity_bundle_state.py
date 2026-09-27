"""Crash and stale-writer boundaries for a sequential BUY bundle journal."""

from copy import deepcopy

import pytest

from src.engine.scalping.initial_quantity_bundle_state import (
    SCHEMA_DYNAMIC_PRICE, bundle_state_path, bundle_state_valid, new_bundle_state,
    next_bundle_state,
    bundle_target_index_path, create_indexed_bundle, read_bundle_for_target,
    persist_dynamic_leg_submit_intent, persist_dynamic_leg_submit_response,
    read_bundle_state, recover_bundle_state, retire_indexed_bundle,
    save_bundle_state_cas,
)
from src.engine.scalping.initial_quantity_timeout import (
    build_bundle_timeout_schedule,
)


def _initial():
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    return new_bundle_state(
        attempt_id="entry-attempt-1", code="005930", target_id="101",
        schedule=schedule, requested_qty=4,
        planned_legs=[{"leg_index": 0, "qty": 1, "price": 10000,
                       "route": "KRX", "tag": "probe"},
                      {"leg_index": 1, "qty": 3, "price": 9990,
                       "route": "KRX", "tag": "residual"}])


def test_bundle_journal_survives_restart_and_rejects_stale_or_regressed_writer(tmp_path):
    initial = _initial()
    path = bundle_state_path(tmp_path, initial["attempt_id"])
    assert save_bundle_state_cas(path, initial, expected_parent_sha256=None) == (
        initial["bundle_content_sha256"])
    assert read_bundle_state(path) == initial
    start = initial["schedule"]["order_start_at_epoch"]
    intent = next_bundle_state(initial, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    save_bundle_state_cas(path, intent,
                          expected_parent_sha256=initial["bundle_content_sha256"])
    assert read_bundle_state(path) == intent
    with pytest.raises(ValueError, match="parent_or_transition_invalid"):
        save_bundle_state_cas(path, intent,
                              expected_parent_sha256=initial["bundle_content_sha256"])
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(intent, 1, {"state": "SUBMIT_INTENT",
                                      "submit_intent_at_epoch": start + 30,
                                      "broker_order_no": "0000124"})
    open_state = next_bundle_state(intent, 0,
                                   {"state": "OPEN", "broker_order_no": "0000123",
                                    "submit_intent_at_epoch": start})
    save_bundle_state_cas(path, open_state,
                          expected_parent_sha256=intent["bundle_content_sha256"])
    assert read_bundle_state(path) == open_state
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(open_state, 0, {"state": "NOT_SUBMITTED"})
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(open_state, 0, {
            "state": "CANCEL_REQUESTED", "broker_order_no": "0000999",
            "submit_intent_at_epoch": start,
        })
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(open_state, 1, {"state": "OPEN", "broker_order_no": "0000124"})
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(open_state, 1, {"state": "SUBMIT_INTENT",
                                          "submit_intent_at_epoch": start + 30})


def test_bundle_recovery_accepts_only_same_sealed_plan_and_newer_journal(tmp_path):
    initial = _initial()
    path = bundle_state_path(tmp_path, initial["attempt_id"])
    assert recover_bundle_state(path, initial) == (
        None, "bundle_journal_missing_or_invalid")
    save_bundle_state_cas(path, initial, expected_parent_sha256=None)
    assert recover_bundle_state(path, initial) == (initial, "bundle_journal_current")
    intent = next_bundle_state(initial, 0, {
        "state": "SUBMIT_INTENT",
        "submit_intent_at_epoch": initial["schedule"]["order_start_at_epoch"],
    })
    save_bundle_state_cas(path, intent,
                          expected_parent_sha256=initial["bundle_content_sha256"])
    assert recover_bundle_state(path, initial) == (intent, "bundle_journal_ahead")
    assert recover_bundle_state(path, intent) == (intent, "bundle_journal_current")
    opened = next_bundle_state(intent, 0, {
        "state": "OPEN", "submit_intent_at_epoch":
            initial["schedule"]["order_start_at_epoch"],
        "broker_order_no": "0000123",
    })
    save_bundle_state_cas(path, opened,
                          expected_parent_sha256=intent["bundle_content_sha256"])
    assert recover_bundle_state(path, initial) == (None, "bundle_history_gap")
    assert recover_bundle_state(
        path, initial, indexed_journal_authority=True) == (
        None, "bundle_target_index_invalid")
    assert recover_bundle_state(path, intent) == (opened, "bundle_journal_ahead")
    assert recover_bundle_state(path, _initial() | {"generation": 1}) == (
        None, "observed_bundle_invalid")
    path.write_text("{broken")
    assert recover_bundle_state(path, initial) == (
        None, "bundle_journal_missing_or_invalid")


def test_terminal_proof_and_path_tamper_fail_closed(tmp_path):
    initial = _initial()
    path = bundle_state_path(tmp_path, initial["attempt_id"])
    forged = deepcopy(initial)
    forged["leg_states"][0] = {"state": "TERMINAL_FILLED",
                               "broker_order_no": "0000123"}
    assert not bundle_state_valid(forged)
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(initial, 0, forged["leg_states"][0])
    with pytest.raises(ValueError, match="path_invalid"):
        save_bundle_state_cas(tmp_path / "outside.json", initial,
                              expected_parent_sha256=None)
    save_bundle_state_cas(path, initial, expected_parent_sha256=None)
    path.write_text('{"broken": true}')
    assert read_bundle_state(path) is None
    with pytest.raises(ValueError, match="current_corrupt"):
        save_bundle_state_cas(path, initial, expected_parent_sha256=None)


def test_terminal_cannot_claim_more_than_the_pinned_leg_quantity():
    initial = _initial()
    start = initial["schedule"]["order_start_at_epoch"]
    intent = next_bundle_state(initial, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    opened = next_bundle_state(intent, 0, {
        "state": "OPEN", "submit_intent_at_epoch": start,
        "broker_order_no": "0000123"})
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(opened, 0, {
            "state": "TERMINAL_FILLED", "submit_intent_at_epoch": start,
            "broker_order_no": "0000123", "terminal_confirmed": True,
            "terminal_confirmed_at_epoch": start + 5,
            "broker_terminal_receipt_id": "broker-proof",
            "owner_registry_receipt_id": "owner-proof",
            "account_position_receipt_id": "account-proof",
            "broker_unfilled_qty": 0, "owner_registry_terminal": True,
            "account_position_reconciled": True, "ordered_qty": 2,
            "filled_qty": 2, "cancelled_qty": 0,
        })


def test_target_index_recovers_lost_bundle_and_retires_only_exact_terminal(tmp_path):
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=1, cancel_confirm_reserve_sec=5)
    initial = new_bundle_state(
        attempt_id="target-index-attempt", code="005930", target_id="101",
        schedule=schedule, requested_qty=1,
        planned_legs=[{"leg_index": 0, "qty": 1, "price": 10000,
                       "route": "KRX", "tag": "probe"}])
    path = create_indexed_bundle(tmp_path, initial)
    assert path == bundle_state_path(tmp_path, initial["attempt_id"])
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        initial, "target_bundle_loaded")
    assert create_indexed_bundle(tmp_path, initial) == path
    another = new_bundle_state(
        attempt_id="another-attempt", code="005930", target_id="101",
        schedule=schedule, requested_qty=1,
        planned_legs=initial["planned_legs"])
    with pytest.raises(ValueError, match="already_active"):
        create_indexed_bundle(tmp_path, another)
    with pytest.raises(ValueError, match="not_terminal"):
        retire_indexed_bundle(tmp_path, initial)
    start = schedule["order_start_at_epoch"]
    intent = next_bundle_state(initial, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    save_bundle_state_cas(path, intent,
                          expected_parent_sha256=initial["bundle_content_sha256"])
    opened = next_bundle_state(intent, 0, {
        "state": "OPEN", "submit_intent_at_epoch": start,
        "broker_order_no": "0000123"})
    save_bundle_state_cas(path, opened,
                          expected_parent_sha256=intent["bundle_content_sha256"])
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        opened, "target_bundle_loaded")
    assert recover_bundle_state(
        path, initial, indexed_journal_authority=True) == (
        opened, "bundle_journal_ahead")
    terminal = next_bundle_state(opened, 0, {
        "state": "TERMINAL_FILLED", "submit_intent_at_epoch": start,
        "broker_order_no": "0000123", "terminal_confirmed": True,
        "terminal_confirmed_at_epoch": start + 10,
        "broker_terminal_receipt_id": "broker-proof",
        "owner_registry_receipt_id": "owner-proof",
        "account_position_receipt_id": "account-proof",
        "broker_unfilled_qty": 0, "owner_registry_terminal": True,
        "account_position_reconciled": True, "ordered_qty": 1,
        "filled_qty": 1, "cancelled_qty": 0})
    save_bundle_state_cas(path, terminal,
                          expected_parent_sha256=opened["bundle_content_sha256"])
    assert retire_indexed_bundle(tmp_path, terminal)
    assert not retire_indexed_bundle(tmp_path, terminal)
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        terminal, "target_bundle_terminal")
    create_indexed_bundle(tmp_path, another)
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        another, "target_bundle_loaded")


def test_target_index_corruption_blocks_recovery_and_new_attempt(tmp_path):
    initial = _initial()
    create_indexed_bundle(tmp_path, initial)
    index_path = bundle_target_index_path(tmp_path, "005930", "101")
    index_path.write_text("{broken")
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        None, "target_index_unreadable")
    with pytest.raises(ValueError, match="already_active_or_invalid"):
        create_indexed_bundle(tmp_path, initial)


def test_target_index_creation_recovers_only_exact_orphan_initial_journal(tmp_path):
    initial = _initial()
    path = bundle_state_path(tmp_path, initial["attempt_id"])
    save_bundle_state_cas(path, initial, expected_parent_sha256=None)
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        None, "target_index_absent")
    assert create_indexed_bundle(tmp_path, initial) == path
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        initial, "target_bundle_loaded")

    other_root = tmp_path / "other"
    other_path = bundle_state_path(other_root, initial["attempt_id"])
    save_bundle_state_cas(other_path, initial, expected_parent_sha256=None)
    start = initial["schedule"]["order_start_at_epoch"]
    intent = next_bundle_state(initial, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    save_bundle_state_cas(other_path, intent,
                          expected_parent_sha256=initial["bundle_content_sha256"])
    with pytest.raises(ValueError, match="orphan_journal_conflict"):
        create_indexed_bundle(other_root, initial)
    assert read_bundle_for_target(other_root, "005930", "101") == (
        None, "target_index_absent")

    corrupt_root = tmp_path / "corrupt"
    corrupt_path = bundle_state_path(corrupt_root, initial["attempt_id"])
    corrupt_path.parent.mkdir(parents=True)
    corrupt_path.write_text("{broken")
    with pytest.raises(ValueError, match="orphan_journal_conflict"):
        create_indexed_bundle(corrupt_root, initial)
    assert read_bundle_for_target(corrupt_root, "005930", "101") == (
        None, "target_index_absent")


def test_dynamic_price_bundle_binds_each_leg_only_at_submit_intent(tmp_path):
    parent = _initial()
    template = [{**leg, "price": 0} for leg in parent["planned_legs"]]
    initial = new_bundle_state(
        attempt_id="dynamic-price", code="005930", target_id="101",
        schedule=parent["schedule"], planned_legs=template,
        requested_qty=4, schema=SCHEMA_DYNAMIC_PRICE,
    )
    path = create_indexed_bundle(tmp_path, initial)
    start = initial["schedule"]["slots"][0]["slot_start_epoch"]
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(initial, 0, {
            "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start})
    intent = next_bundle_state(initial, 0, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": start,
        "submit_price": 10000, "owner_client_intent_id": "owner:first"})
    save_bundle_state_cas(path, intent,
                          expected_parent_sha256=initial["bundle_content_sha256"])
    with pytest.raises(ValueError, match="transition_invalid"):
        next_bundle_state(intent, 0, {
            "state": "OPEN", "submit_intent_at_epoch": start,
            "submit_price": 10010, "owner_client_intent_id": "owner:first",
            "broker_order_no": "0000123"})
    opened = next_bundle_state(intent, 0, {
        "state": "OPEN", "submit_intent_at_epoch": start,
        "submit_price": 10000, "owner_client_intent_id": "owner:first",
        "broker_order_no": "0000123"})
    save_bundle_state_cas(path, opened,
                          expected_parent_sha256=intent["bundle_content_sha256"])
    terminal = next_bundle_state(opened, 0, {
        "state": "TERMINAL_FILLED", "submit_intent_at_epoch": start,
        "submit_price": 10000, "owner_client_intent_id": "owner:first",
        "broker_order_no": "0000123",
        "terminal_confirmed": True,
        "terminal_confirmed_at_epoch": start + 10,
        "broker_terminal_receipt_id": "broker-proof",
        "owner_registry_receipt_id": "owner-proof",
        "account_position_receipt_id": "account-proof",
        "broker_unfilled_qty": 0, "owner_registry_terminal": True,
        "account_position_reconciled": True, "ordered_qty": 1,
        "filled_qty": 1, "cancelled_qty": 0})
    save_bundle_state_cas(path, terminal,
                          expected_parent_sha256=opened["bundle_content_sha256"])
    second_start = initial["schedule"]["slots"][1]["slot_start_epoch"]
    second_intent = next_bundle_state(terminal, 1, {
        "state": "SUBMIT_INTENT", "submit_intent_at_epoch": second_start,
        "submit_price": 9980, "owner_client_intent_id": "owner:second"})
    save_bundle_state_cas(path, second_intent,
                          expected_parent_sha256=terminal["bundle_content_sha256"])
    assert read_bundle_for_target(tmp_path, "005930", "101") == (
        second_intent, "target_bundle_loaded")
    assert second_intent["planned_legs"][1]["price"] == 0
    assert second_intent["leg_states"][1]["submit_price"] == 9980


def test_dynamic_leg_submit_intent_and_response_are_single_use(tmp_path):
    parent = _initial()
    initial = new_bundle_state(
        attempt_id="dynamic-submit", code="005930", target_id="101",
        schedule=parent["schedule"], requested_qty=4,
        planned_legs=[{**leg, "price": 0} for leg in parent["planned_legs"]],
        schema=SCHEMA_DYNAMIC_PRICE,
    )
    create_indexed_bundle(tmp_path, initial)
    start = initial["schedule"]["order_start_at_epoch"]
    intent = persist_dynamic_leg_submit_intent(
        tmp_path, initial, leg_index=0, submit_price=10000,
        owner_client_intent_id="owner:first",
        now_epoch=start + 1)
    assert intent["leg_states"][0]["state"] == "SUBMIT_INTENT"
    with pytest.raises(ValueError, match="index_conflict"):
        persist_dynamic_leg_submit_intent(
            tmp_path, initial, leg_index=0, submit_price=10000,
            owner_client_intent_id="owner:first",
            now_epoch=start + 2)
    uncertain = persist_dynamic_leg_submit_response(
        tmp_path, intent, leg_index=0, broker_order_no=None,
        owner_exact=False)
    assert uncertain["leg_states"][0]["state"] == "UNCERTAIN"
    with pytest.raises(ValueError, match="index_conflict"):
        persist_dynamic_leg_submit_response(
            tmp_path, intent, leg_index=0, broker_order_no="0000123",
            owner_exact=True)
    with pytest.raises(ValueError, match="slot_closed"):
        persist_dynamic_leg_submit_intent(
            tmp_path, uncertain, leg_index=1, submit_price=9990,
            owner_client_intent_id="owner:second",
            now_epoch=initial["schedule"]["slots"][1]["slot_start_epoch"])


def test_dynamic_leg_submit_intent_rejects_elapsed_slot(tmp_path):
    parent = _initial()
    initial = new_bundle_state(
        attempt_id="dynamic-late", code="005930", target_id="101",
        schedule=parent["schedule"], requested_qty=4,
        planned_legs=[{**leg, "price": 0} for leg in parent["planned_legs"]],
        schema=SCHEMA_DYNAMIC_PRICE,
    )
    create_indexed_bundle(tmp_path, initial)
    first = initial["schedule"]["slots"][0]
    with pytest.raises(ValueError, match="slot_closed"):
        persist_dynamic_leg_submit_intent(
            tmp_path, initial, leg_index=0, submit_price=10000,
            owner_client_intent_id="owner:first",
            now_epoch=first["cancel_request_by_epoch"])
