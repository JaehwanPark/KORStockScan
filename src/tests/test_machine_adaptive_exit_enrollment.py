"""Synthetic initial policies into real owner stores; fake broker wire only."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest

from src.tests.test_machine_adaptive_exit_activation import fixture, publish, CODE, OPEN
from src.tests.test_machine_adaptive_exit_broker import Transport
from src.tests.test_machine_adaptive_exit_decision import inputs
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.enrollment import (
    ENROLLMENT_KEY,
    InitialPolicyAdmission,
    EnrollmentReloadRequired,
)
from src.trading.order.adaptive_exit.models import Clock
from src.trading.order.adaptive_exit.owner_loop import SESSION_KEY, OwnerLoopServices
from src.trading.order.adaptive_exit.runtime import OwnerSession
from src.trading.order.adaptive_exit.source import (
    record_first_fill_observation,
    record_target_observation,
)
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
)
from src.trading.order.regular_two_leg_machine import (
    SamsungRegularTwoLegMachine,
    _fresh_state,
    _new_leg,
)
from src.trading.widget_auto_trade import engine as widget

DAY = OPEN.date().isoformat()
SIGNAL = f"005930:{DAY}:ENTRY_READY:KRX_REGULAR:0900"


@pytest.fixture(params=["episode", "widget"])
def enrolled_owner(request, tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "isolated-enrollment-test")
    owner = request.param
    profile = (
        "samsung:test-profile" if owner == "episode" else "actual:005930:KRX_REGULAR"
    )
    entry_policy = {"test_only": "not_live"}
    data = fixture(
        tmp_path,
        owner=owner,
        route="SOR",
        profile=profile,
        entry_policy_hash=canonical_sha256(entry_policy),
    )
    publish(data)
    admission = InitialPolicyAdmission(
        data["output_path"],
        data["envelope_path"],
        data["envelope"]["canonical_sha256"],
        CODE,
        OPEN - timedelta(minutes=10),
    )
    position = (
        f"episode:test-profile:005930:{DAY}"
        if owner == "episode"
        else f"widget_auto_trade:005930:{DAY}:{SIGNAL}"
    )
    context = OwnerOrderContext(
        "episode" if owner == "episode" else "widget_auto_trade",
        position,
        position,
        "target",
    )
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    buy_context = replace(context, client_intent_id="buy")
    buy_id = registry.reserve(
        context=buy_context,
        symbol="005930",
        side="BUY",
        quantity=10,
        route="SOR",
        order_date=DAY,
    )
    registry.transition(buy_id, state="ORDER_BOUND", broker_order_no="0000001")
    registry.record_fill(
        context=buy_context,
        symbol="005930",
        side="BUY",
        order_quantity=10,
        order_date=DAY,
        broker_order_no="0000001",
        cumulative_filled_qty=10,
    )
    registry.transition(buy_id, state="ORDER_TERMINAL")
    target_id = registry.reserve(
        context=context,
        symbol="005930",
        side="SELL",
        quantity=10,
        route="SOR",
        order_date=DAY,
    )
    registry.transition(target_id, state="ORDER_BOUND", broker_order_no="0000002")
    observation = {}
    record_first_fill_observation(
        observation,
        previous_filled_qty=0,
        filled_qty=10,
        observed_at=(OPEN - timedelta(minutes=2)).isoformat(),
    )
    first = observation["adaptive_exit_first_fill_observation"]
    lot = "signal_close" if owner == "episode" else "entry"
    source_store = {}
    record_target_observation(
        source_store,
        owner=owner,
        profile=profile,
        symbol="005930",
        session="KRX_REGULAR",
        entry_policy=entry_policy,
        observed_at=(OPEN - timedelta(minutes=1)).isoformat(),
        target=dict(
            order_date=DAY, order_no="0000002", route="SOR", quantity=10, price=10100
        ),
        entries=[
            dict(
                episode_id=f"{profile}:{DAY}" if owner == "episode" else SIGNAL,
                lot_id=lot,
                order_date=DAY,
                order_no="0000001",
                quantity=10,
                requested_quantity=10,
                price=10000,
                first_fill_observation=deepcopy(first),
            )
        ],
    )
    wire, flags = Transport(), {"lock": True, "guard": True, "authority": True}
    wire.write_body["cncl_qty"] = "10"
    snap = inputs()[2]
    services = OwnerLoopServices(
        lock_held=lambda: flags["lock"],
        authorize_binding=lambda b: flags["authority"],
        owner_guard=lambda *a, **k: flags["guard"],
        clock_loader=lambda s, ms: Clock(ms, 0),
        snapshot_loader=lambda s, c: replace(
            snap,
            scope_key=s.policy.scope_key,
            position_epoch=s.remaining_position.position_epoch,
            observed_at_ms=c.now_ms,
            quote_at_ms=c.now_ms,
            sequence=c.now_ms,
        ),
        admission=admission,
    )

    class Gateway:
        def adaptive_exit_adapter(
            self, *, registry, context, policy_hash, write_guard, code="005930"
        ):
            return RegisteredSellAdapter(
                post=wire,
                registry=registry,
                context=context,
                symbol=code,
                routes=("SOR",),
                policy_hash=policy_hash,
                maximum_quantity=10,
                require_write_authority=lambda: None,
                write_guard=write_guard,
                now_ms=lambda: int(OPEN.timestamp() * 1000),
            )

    path = tmp_path / "owner.json"
    if owner == "episode":
        machine = SamsungRegularTwoLegMachine(
            gateway=Gateway(),
            state_path=path,
            policy=SimpleNamespace(symbol="005930", route="SOR"),
            strategy_name="test-profile",
            schema="test-v1",
            legacy_schema="old",
            live_enabled=True,
            owner_registry=registry,
            adaptive_exit_services=services,
        )
        leg = _new_leg(lot, lot, 10000)
        leg.update(
            quantity=10,
            status="TARGET_OPEN",
            buy_order_no="0000001",
            buy_order_date=DAY,
            buy_filled_qty=10,
            fill_price=10000,
            position_qty=10,
            target_order_no="0000002",
            target_order_date=DAY,
            target_quantity=10,
            target_price=10100,
            target_owner_registry_intent_id=target_id,
            adaptive_exit_first_fill_observation=deepcopy(first),
            **source_store,
        )
        other = _new_leg("signal_close_minus_1tick", "signal_close_minus_1tick", 9995)
        other["status"] = "NO_FILL"
        machine._state = _fresh_state(OPEN, "test-v1")
        machine._state.update(
            owned_order_nos=["0000001", "0000002"],
            legs=[leg, other],
            position_qty=10,
            status="TARGET_OPEN",
            attempt_consumed=True,
        )
        state = leg

        def propose(now=OPEN):
            return machine._try_adaptive_enrollment(now)

        def raw():
            return machine._state["legs"][0][SESSION_KEY]

        def receipt():
            return machine._state["legs"][0][ENROLLMENT_KEY]

        monkeypatch.setattr(
            machine,
            "_reconcile_target",
            lambda *a: pytest.fail("legacy target entered"),
        )
    else:
        machine = widget.WidgetSignalAutoTrader(
            gateway=Gateway(),
            specs=(),
            dynamic_spec_catalog=(),
            state_path=path,
            policy_loader=SimpleNamespace(resolve_all=lambda **k: {}),
            enabled=True,
            owner_registry=registry,
            adaptive_exit_services=services,
        )
        buy = dict(
            side="BUY",
            status="FILLED",
            broker_accepted=True,
            filled_qty=10,
            requested_qty=10,
            fill_price=10000,
            order_no="0000001",
            order_date=DAY,
            signal_id=SIGNAL,
            adaptive_exit_first_fill_observation=deepcopy(first),
        )
        target = dict(
            side="SELL",
            status="SUBMITTED",
            order_role=widget.ORDER_ROLE_TAKE_PROFIT,
            broker_accepted=True,
            filled_qty=0,
            requested_qty=10,
            limit_price=10100,
            order_no="0000002",
            order_date=DAY,
            owner_id=position,
            owner_position_id=position,
            owner_client_intent_id=context.client_intent_id,
            owner_registry_intent_id=target_id,
            parent_entry_signal_id=SIGNAL,
            **source_store,
        )
        state = dict(
            code="005930",
            orders=[buy, target],
            entry_signal_id=SIGNAL,
            entry_episode_open=True,
        )
        machine._state = dict(active_date=DAY, symbols={"005930": state})

        def propose(now=OPEN):
            return machine._try_adaptive_enrollment("005930", state, now)

        def raw():
            return machine._state["symbols"]["005930"]["adaptive_exit_sessions"][lot]

        def receipt():
            return machine._state["symbols"]["005930"][ENROLLMENT_KEY][lot]

        monkeypatch.setattr(
            machine, "_reconcile", lambda *a: pytest.fail("legacy target entered")
        )
    machine._save()
    return SimpleNamespace(
        machine=machine,
        owner=owner,
        state=state,
        data=data,
        admission=admission,
        registry=registry,
        source=source_store["adaptive_exit_target_observations"][f"{DAY}:0000002"],
        path=path,
        propose=propose,
        raw=raw,
        receipt=receipt,
        flags=flags,
        wire=wire,
    )


def test_policy_original_owner_enrollment_then_existing_execution_loop(enrolled_owner):
    x = enrolled_owner
    registry_before = x.registry.path.read_bytes()
    assert x.propose()
    assert not x.wire.calls  # admission neither reads nor writes the broker
    assert x.registry.path.read_bytes() == registry_before
    session = OwnerSession.from_payload(x.raw())
    assert session.position.cost_contract_hash == "f" * 64
    assert x.admission.authorize(session.binding, x.receipt(), now=OPEN)
    original = x.path.read_bytes()
    assert not x.propose()  # no enrollment retry/replacement
    assert x.path.read_bytes() == original
    x.machine._state = x.machine._load_state()
    x.machine.run_once(OPEN)
    assert (
        OwnerSession.from_payload(x.raw()).driver.orders.phase == "CANCEL_PENDING"
    ), x.machine._state
    assert len(x.wire.writes) == 1  # fake wire, only the existing owner port


@pytest.mark.parametrize("flag", ["lock", "guard", "authority"])
def test_authority_loss_never_enrolls(enrolled_owner, flag):
    x = enrolled_owner
    x.flags[flag] = False
    before = x.path.read_bytes()
    assert not x.propose()
    assert not x.wire.calls and x.path.read_bytes() == before


def test_late_start_cannot_adopt_existing_holding(enrolled_owner):
    x = enrolled_owner
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services,
        admission=replace(x.admission, started_at=OPEN),
    )
    assert not x.propose()
    assert not x.wire.calls


def test_expiry_blocks_new_but_keeps_frozen_enrollment_after_restart(enrolled_owner):
    x = enrolled_owner
    assert not x.propose(OPEN + timedelta(days=1))
    assert x.propose()
    fresh_process = replace(x.admission, started_at=OPEN + timedelta(days=1))
    assert fresh_process.authorize(
        OwnerSession.from_payload(x.raw()).binding,
        x.receipt(),
        now=OPEN + timedelta(days=1),
    )


@pytest.mark.parametrize(
    "field", ["envelope_sha256", "applied_sha256", "binding_sha256"]
)
def test_receipt_tamper_is_not_self_authority(enrolled_owner, field):
    x = enrolled_owner
    assert x.propose()
    x.receipt()[field] = "0" * 64
    x.receipt()["canonical_sha256"] = canonical_sha256(x.receipt())
    x.machine.run_once(OPEN)
    assert not x.wire.calls


def test_publish_then_save_failure_requires_owner_reload(enrolled_owner, monkeypatch):
    x = enrolled_owner
    save = x.machine._save

    def uncertain():
        save()
        raise OSError("synthetic directory fsync failure after publish")

    monkeypatch.setattr(x.machine, "_save", uncertain)
    with pytest.raises(EnrollmentReloadRequired):
        x.propose()
    published = x.path.read_bytes()
    with pytest.raises(EnrollmentReloadRequired):
        x.machine.run_once(OPEN)
    monkeypatch.setattr(x.machine, "_save", save)
    with pytest.raises(EnrollmentReloadRequired):
        x.machine._save()
    assert x.path.read_bytes() == published and not x.wire.calls


def test_missing_session_receipt_cannot_fall_back_to_legacy(enrolled_owner):
    x = enrolled_owner
    assert x.propose()
    if x.owner == "episode":
        del x.state[SESSION_KEY]
    else:
        del x.state["adaptive_exit_sessions"]
    with pytest.raises(ValueError, match="enrollment_session_missing"):
        x.propose()
    assert not x.wire.calls


def test_run_once_claims_before_ordinary_target_management(enrolled_owner):
    x = enrolled_owner
    x.machine.run_once(OPEN)
    assert OwnerSession.from_payload(x.raw()).driver.orders.phase == "TARGET_WORKING"
    assert not x.wire.calls


@pytest.mark.parametrize(
    "kind",
    [
        "target_bool",
        "source_authority",
        "clock_basis",
        "old_first_fill",
        "unapproved_entry",
        "same_buy_sell",
    ],
)
def test_invalid_frozen_source_does_not_enroll(enrolled_owner, kind):
    x = enrolled_owner
    source = x.source
    if kind == "target_bool":
        source["target"]["quantity"] = True
    elif kind == "source_authority":
        source["authority"]["runtime_effect"] = True
    elif kind == "clock_basis":
        source["timestamp_provenance"] = "unknown"
    elif kind == "old_first_fill":
        source["entries"][0]["first_fill_observation"]["first_observed_at"] = (
            OPEN - timedelta(days=1)
        ).isoformat()
    elif kind == "unapproved_entry":
        source["entry_policy"]["test_only"] = "changed"
        source["entry_policy_hash"] = canonical_sha256(source["entry_policy"])
    else:
        source["entries"][0]["order_no"] = source["target"]["order_no"]
    source["canonical_sha256"] = canonical_sha256(source)
    assert not x.propose()
    assert not x.wire.calls


def test_partial_original_target_in_registry_is_not_zero_fill(enrolled_owner):
    x = enrolled_owner
    target = x.source["target"]
    context = (
        x.machine._episode_owner_context(leg=x.state, action="test", ordinal=1)
        if x.owner == "episode"
        else x.machine._owner_context_from_order(x.state["orders"][1])
    )
    x.registry.record_fill(
        context=context,
        symbol="005930",
        side="SELL",
        order_quantity=10,
        order_date=DAY,
        broker_order_no=target["order_no"],
        cumulative_filled_qty=1,
    )
    assert not x.propose()
    assert not x.wire.calls


def test_removing_admission_service_does_not_downgrade_existing_receipt(enrolled_owner):
    x = enrolled_owner
    assert x.propose()
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services, admission=None
    )
    x.machine.run_once(OPEN)
    assert not x.wire.calls


def test_missing_enrollment_receipt_cannot_run_with_initial_service(enrolled_owner):
    x = enrolled_owner
    assert x.propose()
    del x.state[ENROLLMENT_KEY]
    x.machine.run_once(OPEN)
    assert not x.wire.calls


def test_invalid_enrollment_container_has_explicit_failure(enrolled_owner):
    x = enrolled_owner
    assert x.propose()
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services, admission=None
    )
    x.state[ENROLLMENT_KEY] = None
    x.machine.run_once(OPEN)
    assert not x.wire.calls


def test_policy_file_mutation_invalidates_retained_binding(enrolled_owner):
    x = enrolled_owner
    assert x.propose()
    x.data["output_path"].write_text("{}", encoding="utf-8")
    x.machine.run_once(OPEN)
    assert not x.wire.calls


def test_lost_lock_during_prepare_stops_before_ordinary_fallthrough(
    enrolled_owner, monkeypatch
):
    x = enrolled_owner
    original = InitialPolicyAdmission.prepare

    def lose(self, **kwargs):
        result = original(self, **kwargs)
        x.flags["lock"] = False
        return result

    monkeypatch.setattr(InitialPolicyAdmission, "prepare", lose)
    with pytest.raises(PermissionError, match="original_owner_lock_required"):
        x.propose()
    assert not x.wire.calls
