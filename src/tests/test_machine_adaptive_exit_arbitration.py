"""Qualified source EXIT uses the original owner and single adaptive writer."""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.tests import test_machine_adaptive_exit_owner_loop as fixtures
from src.tests.test_machine_adaptive_exit_broker import detail
from src.tests.test_machine_adaptive_exit_runtime import working_exit, cancel_detail
from src.tests.test_machine_adaptive_exit_decision import inputs, trail_inputs
from src.tests.test_widget_signal_auto_trade import FakeContract
from src.trading.widget_auto_trade.engine import WidgetSpec
from src.trading.order.adaptive_exit.arbitration import FINAL_EXIT_KEY
from src.trading.order.adaptive_exit.decision import evaluate_exit
from src.trading.order.adaptive_exit.models import TrailPolicy
from src.trading.order.adaptive_exit.runtime import OwnerSession
from src.trading.order.adaptive_exit.owner_loop import step_session
from src.trading.order.adaptive_exit.models import Clock
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.engine.monitoring.samsung_widget_contract import KST


@pytest.fixture(params=["widget"])
def loop(request, tmp_path, monkeypatch):
    # Reuse the actual-owner/fake-wire fixture, without pretending episode
    # machines have the widget producer's final EXIT signal contract.
    return fixtures.loop.__wrapped__(request, tmp_path, monkeypatch)


@pytest.fixture
def widget_loop(loop, monkeypatch):
    assert loop.owner == "widget"
    machine = loop.machine
    spec = WidgetSpec("005930", "test", Path("unused.json"), FakeContract, True)
    machine.specs = (spec,)
    machine.adaptive_exit_services = replace(
        machine.adaptive_exit_services,
        authorize_final_exit=lambda receipt: loop.flags.get("final_authority", True),
    )
    state = machine._state["symbols"]["005930"]
    state["entry_execution_policy"] = {
        "policy_id": "original-widget-policy",
        "source_final_exit_action": "sell_own_filled_quantity",
    }
    # Keep normal alpha before its soft deadline so only a qualified final
    # EXIT, not elapsed time, can start cancellation in these tests.
    session = OwnerSession.from_payload(loop.record())
    policy = replace(session.policy, soft_sec=120)
    policy = replace(
        policy,
        policy_hash=canonical_sha256(
            {k: v for k, v in asdict(policy).items() if k != "policy_hash"}
        ),
    )
    session = replace(
        session,
        policy=policy,
        driver=replace(
            session.driver,
            orders=replace(session.driver.orders, policy_hash=policy.policy_hash),
            decision=replace(session.driver.decision, policy_hash=policy.policy_hash),
        ),
    )
    loop.set_record(session.to_payload())
    loop.wire.detailed = [detail(cntr_qty="0", ord_remnq="10")]
    loop.wire.current[0].update(cntr_qty="0", oso_qty="10")
    now = datetime.fromtimestamp(loop.clock[0] / 1000, KST)
    box = {
        "payload": {
            "status": "ok",
            "symbol": "005930",
            "strategy_profile": "TEST_WIDGET_V1",
            "market_venue": "KRX",
            "observed_at_kst": now.isoformat(),
            "exit_event": {"valid": True, "event_type": "EXIT", "event_id": "EXIT-1"},
        }
    }
    machine.snapshot_loader = lambda path: box["payload"]
    monkeypatch.setattr(
        machine, "_maybe_submit_exit", lambda *a: pytest.fail("second SELL owner")
    )
    loop.box = box
    return loop


def test_qualified_exit_is_sticky_cancels_once_and_finishes_via_same_owner(widget_loop):
    loop = widget_loop
    state = loop.machine._state["symbols"]["005930"]
    state["pending_entry_confirmation"] = {"signal_id": "NEW-BUY"}
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "CANCEL_PENDING"
    receipt = deepcopy(state[FINAL_EXIT_KEY])
    assert state["pending_entry_confirmation"] is None
    assert len(loop.wire.writes) == 1
    loop.box["payload"] = None
    loop.machine._state = loop.machine._load_state()
    loop.wire.detailed = [detail(cntr_qty="0", ord_remnq="0"), cancel_detail()]
    loop.wire.current = []
    loop.tick()
    loop.wire.write_body["ord_no"] = "0000004"
    loop.tick()
    working_exit(loop.wire, fill=10, remaining=0)
    loop.tick()
    state = loop.machine._state["symbols"]["005930"]
    assert FINAL_EXIT_KEY not in state and state["exit_requested"] is False
    assert state["completed_entry_count"] == 1
    assert state["adaptive_exit_history"][-1]["final_exit_request"] == receipt
    assert state["adaptive_exit_history"][-1]["superseded_entry_confirmation"] == {
        "signal_id": "NEW-BUY"
    }
    assert len(loop.wire.writes) == 2


@pytest.mark.parametrize(
    "kind",
    [
        "observe",
        "invalid_action",
        "stale",
        "wrong_symbol",
        "wrong_route",
        "untrusted",
        "no_authority",
    ],
)
def test_invalid_or_observation_only_exit_cannot_become_forced_sell(widget_loop, kind):
    loop = widget_loop
    state = loop.machine._state["symbols"]["005930"]
    payload = loop.box["payload"]
    if kind in {"observe", "invalid_action"}:
        state["entry_execution_policy"]["source_final_exit_action"] = (
            "observe_only_no_forced_sell" if kind == "observe" else "UNKNOWN"
        )
    elif kind == "stale":
        payload["observed_at_kst"] = (
            datetime.fromisoformat(payload["observed_at_kst"]) - timedelta(seconds=31)
        ).isoformat()
    elif kind == "wrong_symbol":
        payload["symbol"] = "000660"
    elif kind == "wrong_route":
        payload["market_venue"] = "NXT"
    elif kind == "untrusted":
        payload["exit_event"]["valid"] = False
    else:
        loop.flags["final_authority"] = False
    loop.tick()
    assert FINAL_EXIT_KEY not in state
    assert loop.record()["driver"]["orders"]["phase"] == "TARGET_WORKING"
    assert not loop.wire.writes


@pytest.mark.parametrize("block", ["quote", "guard", "authority", "lock"])
def test_final_exit_never_bypasses_existing_guards(widget_loop, block):
    loop = widget_loop
    loop.flags[block] = False
    loop.tick()
    assert not loop.wire.writes


def test_exit_receipt_save_failure_occurs_before_any_broker_write(
    widget_loop, monkeypatch
):
    loop = widget_loop
    prior = deepcopy(loop.machine._state)
    monkeypatch.setattr(
        loop.machine, "_save", lambda: (_ for _ in ()).throw(OSError("disk"))
    )
    with pytest.raises(OSError):
        loop.tick()
    assert loop.machine._state == prior and not loop.wire.writes


def test_changed_policy_cannot_reuse_consumed_exit_receipt(widget_loop):
    loop = widget_loop
    loop.flags["quote"] = False
    loop.tick()
    state = loop.machine._state["symbols"]["005930"]
    assert FINAL_EXIT_KEY in state
    state["entry_execution_policy"]["policy_id"] = "different-policy"
    loop.flags["quote"] = True
    loop.tick()
    assert "binding_invalid" in loop.status()
    assert not loop.wire.writes


@pytest.mark.parametrize(
    "field,value", [("position_id", "another-position"), ("session_bindings", [])]
)
def test_owner_port_rejects_foreign_receipt_before_adapter_construction(
    widget_loop, field, value
):
    loop = widget_loop
    loop.flags["quote"] = False
    loop.tick()
    receipt = deepcopy(loop.machine._state["symbols"]["005930"][FINAL_EXIT_KEY])
    receipt[field] = value
    receipt["canonical_sha256"] = canonical_sha256(receipt)
    result = step_session(
        session=OwnerSession.from_payload(loop.record()),
        services=loop.machine.adaptive_exit_services,
        adapter_factory=lambda **kwargs: pytest.fail(
            "foreign receipt constructed broker adapter"
        ),
        persist_record=lambda record: pytest.fail(
            "foreign receipt changed owner state"
        ),
        clock=Clock(loop.clock[0], 0),
        final_exit_requested=True,
        final_exit_request=receipt,
    )
    assert result == "adaptive_final_exit_receipt_binding_invalid"
    assert not loop.wire.writes


@pytest.mark.parametrize(
    "field,value",
    [
        ("entry_signal_id", "other-entry"),
        ("session_bindings", []),
        ("source_session", "NXT_AFTERMARKET"),
        ("route", "NXT"),
        ("observed_at_ms", True),
        ("accepted_at_ms", True),
        ("source_hash", "unknown"),
    ],
)
def test_rehashed_receipt_cannot_change_original_owner_binding(
    widget_loop, field, value
):
    loop = widget_loop
    loop.flags["quote"] = False
    loop.tick()
    receipt = loop.machine._state["symbols"]["005930"][FINAL_EXIT_KEY]
    receipt[field] = value
    receipt["canonical_sha256"] = canonical_sha256(receipt)
    loop.flags["quote"] = True
    loop.tick()
    assert "invalid" in loop.status() or "conflict" in loop.status()
    assert not loop.wire.writes


def test_final_exit_can_exit_nonrunner_without_converting_it_to_trailing():
    policy, p, snapshot, clock, state = trail_inputs()
    policy = replace(policy, runner_lot_ids=("another-lot",))
    assert evaluate_exit(policy, p, snapshot, clock, state).action == "KEEP_TARGET"
    result = evaluate_exit(policy, p, snapshot, clock, state, final_exit_requested=True)
    assert result.action == "REQUEST_EARLY_EXIT" and result.high_water is None


def test_authority_revocation_during_snapshot_read_blocks_broker_write(widget_loop):
    loop = widget_loop
    services = loop.machine.adaptive_exit_services
    original = services.snapshot_loader

    def snapshot(session, clock):
        loop.flags["final_authority"] = False
        return original(session, clock)

    loop.machine.adaptive_exit_services = replace(services, snapshot_loader=snapshot)
    loop.tick()
    assert not loop.wire.writes
    assert "authority_missing" in loop.status()


@pytest.mark.parametrize("status", ["SUBMITTED", "ACCEPTED", "UNKNOWN", "AMBIGUOUS"])
def test_pending_broker_buy_stays_explicit_recovery_not_implicit_cancel(
    widget_loop, status
):
    loop = widget_loop
    state = loop.machine._state["symbols"]["005930"]
    state["orders"].append(
        {
            "side": "BUY",
            "status": status,
            "order_date": "2026-09-09",
            "order_no": "0000007",
        }
    )
    loop.tick()
    assert "competing_order" in loop.status()
    assert not loop.wire.calls and FINAL_EXIT_KEY not in state


def test_receipt_does_not_override_unbound_legacy_exit_intent(widget_loop):
    loop = widget_loop
    state = loop.machine._state["symbols"]["005930"]
    state.update(exit_requested=True, exit_signal_id="LEGACY-EXIT")
    loop.tick()
    assert "existing_intent_arbitration_required" in loop.status()
    assert not loop.wire.calls


def test_direct_process_payload_also_uses_qualified_exit_arbitration(widget_loop):
    loop = widget_loop
    loop.machine.process_payload(
        loop.machine.specs[0],
        loop.box["payload"],
        datetime.fromtimestamp(loop.clock[0] / 1000, KST),
    )
    assert loop.record()["driver"]["orders"]["phase"] == "CANCEL_PENDING"
    assert len(loop.wire.writes) == 1


def test_missing_original_policy_validator_never_activates_final_exit(widget_loop):
    loop = widget_loop
    loop.machine.adaptive_exit_services = replace(
        loop.machine.adaptive_exit_services, authorize_final_exit=None
    )
    loop.tick()
    state = loop.machine._state["symbols"]["005930"]
    assert (
        state["adaptive_source_exit_status"]
        == "source_final_exit_policy_authority_missing"
    )
    assert not loop.wire.writes and FINAL_EXIT_KEY not in state


@pytest.mark.parametrize("offset_ms", [-20000, 20000])
def test_source_timestamp_before_current_fill_or_in_future_is_not_consumed(
    widget_loop, offset_ms
):
    loop = widget_loop
    # The lot was filled 60 seconds before the original NOW. Move processing
    # to 10 seconds after that fill; both test snapshots remain within the
    # source's 30-second freshness allowance, but neither is causal evidence.
    loop.clock[0] -= 50000
    loop.box["payload"]["observed_at_kst"] = datetime.fromtimestamp(
        (loop.clock[0] + offset_ms) / 1000, KST
    ).isoformat()
    loop.tick()
    state = loop.machine._state["symbols"]["005930"]
    assert FINAL_EXIT_KEY not in state and not loop.wire.writes


def test_receipt_keeps_source_time_separate_from_consumption_time(widget_loop):
    loop = widget_loop
    source_at_ms = loop.clock[0] - 10000
    loop.box["payload"]["observed_at_kst"] = datetime.fromtimestamp(
        source_at_ms / 1000, KST
    ).isoformat()
    loop.tick()
    receipt = loop.machine._state["symbols"]["005930"][FINAL_EXIT_KEY]
    assert receipt["observed_at_ms"] == source_at_ms
    assert receipt["accepted_at_ms"] == loop.clock[0]


@pytest.mark.parametrize("trail", [False, True])
def test_explicit_final_exit_precedes_soft_deadline_and_trailing(trail):
    args = trail_inputs() if trail else inputs(age=1000)
    policy, p, snapshot, clock, state = args
    if trail:
        state = replace(state, trail_active=True, high_water=10065, stop_price=10050)
    decision = evaluate_exit(
        policy, p, snapshot, clock, state, final_exit_requested=True
    )
    assert decision.action == "REQUEST_EARLY_EXIT"
    assert decision.reason == "original_owner_final_exit"
    stale = replace(snapshot, quote_at_ms=clock.now_ms - 1001)
    assert (
        evaluate_exit(policy, p, stale, clock, state, final_exit_requested=True).action
        == "SOURCE_GAP"
    )


def test_final_exit_in_trail_active_submits_one_original_owner_sell(widget_loop):
    loop = widget_loop
    session = OwnerSession.from_payload(loop.record())
    policy = replace(
        session.policy,
        mode="time_progress_and_trailing",
        runner_lot_ids=(session.position.lot_id,),
        trail=TrailPolicy(90, 0.5, 3, 2, 0.1),
    )
    policy = replace(
        policy,
        policy_hash=canonical_sha256(
            {k: v for k, v in asdict(policy).items() if k != "policy_hash"}
        ),
    )
    session = replace(
        session,
        policy=policy,
        driver=replace(
            session.driver,
            orders=replace(session.driver.orders, policy_hash=policy.policy_hash),
            decision=replace(session.driver.decision, policy_hash=policy.policy_hash),
        ),
    )
    loop.set_record(session.to_payload())
    # Use the actual cancel/reconciliation path to establish trailing first.
    loop.box["payload"]["exit_event"]["valid"] = False
    services = loop.machine.adaptive_exit_services
    original_snapshot = services.snapshot_loader
    loop.machine.adaptive_exit_services = replace(
        services,
        snapshot_loader=lambda s, c: replace(
            original_snapshot(s, c),
            bid_levels=((10060, 10),),
            best_ask=10070,
            supportive=True,
        ),
    )
    loop.tick()
    loop.wire.detailed = [detail(cntr_qty="0", ord_remnq="0"), cancel_detail()]
    loop.wire.current = []
    loop.tick()
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "TRAIL_ACTIVE"
    loop.box["payload"]["exit_event"]["valid"] = True
    loop.wire.write_body["ord_no"] = "0000004"
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "EXIT_WORKING"
    assert len(loop.wire.writes) == 2
