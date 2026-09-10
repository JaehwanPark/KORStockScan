"""Real owner run_once paths against temporary custody and a fake broker wire."""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    TARGET,
    Transport,
    detail,
    current,
)
from src.tests.test_machine_adaptive_exit_decision import inputs
from src.tests.test_machine_adaptive_exit_runtime import working_exit, cancel_detail
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.driver import DriverState, ExecutionBounds
from src.trading.order.adaptive_exit.models import Clock, DecisionState
from src.trading.order.adaptive_exit.owner_loop import (
    SESSION_KEY,
    OwnerLoopServices,
)
from src.trading.order.adaptive_exit.reducer import ExitState
from src.trading.order.adaptive_exit.runtime import OwnerSession
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


@pytest.fixture(params=["episode", "widget"])
def loop(request, tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "loop-test-account")
    owner = request.param
    wire, clock = Transport(), [NOW]
    wire.write_body["cncl_qty"] = "10"
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    position_id = (
        f"episode:test-profile:005930:{DATE}"
        if owner == "episode"
        else f"widget_auto_trade:005930:{DATE}:signal"
    )
    context = OwnerOrderContext(
        "episode" if owner == "episode" else "widget_auto_trade",
        position_id,
        position_id,
        "target",
    )
    registry.register_migrated_position(
        context=replace(context, client_intent_id="entry"),
        symbol="005930",
        quantity=10,
        average_price=10000,
        route="SOR",
        order_date=DATE,
        broker_order_no="0000001",
        evidence_sha256="a" * 64,
    )
    target = registry.reserve(
        context=context,
        symbol="005930",
        side="SELL",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(target, state="ORDER_BOUND", broker_order_no=TARGET.order_no)
    policy, p, snap, *_ = inputs()
    scope = f"{owner}|test-profile|005930|SOR|KRX_REGULAR"
    policy = replace(policy, scope_key=scope)
    policy = replace(
        policy,
        policy_hash=canonical_sha256(
            {k: v for k, v in asdict(policy).items() if k != "policy_hash"}
        ),
    )
    lot = "signal_close" if owner == "episode" else target
    p = replace(
        p,
        owner_id=owner,
        scope_key=scope,
        episode_id=position_id,
        lot_id=lot,
        first_fill_at_ms=NOW - 60000,
        cost_contract_hash="c" * 64,
    )
    session = OwnerSession(
        policy,
        p,
        ExecutionBounds(
            3000, 2, 5000, "exit_with_fresh_guard", "retain_manager_and_alert"
        ),
        context,
        target,
        "b" * 64,
        DriverState(
            ExitState(
                owner,
                p.episode_id,
                lot,
                policy.policy_hash,
                p.position_epoch,
                TARGET,
                10,
            ),
            DecisionState(policy.policy_hash, p.position_epoch, p.first_fill_at_ms, 10),
        ),
    )
    flags = {"guard": True, "lock": True, "authority": True, "quote": True}
    services = OwnerLoopServices(
        lock_held=lambda: flags["lock"],
        authorize_binding=lambda b: flags["authority"],
        owner_guard=lambda *a, **k: flags["guard"],
        snapshot_loader=lambda s, c: (
            replace(
                snap,
                scope_key=scope,
                position_epoch=s.remaining_position.position_epoch,
                observed_at_ms=c.now_ms,
                quote_at_ms=c.now_ms,
                sequence=c.now_ms,
            )
            if flags["quote"]
            else None
        ),
        clock_loader=lambda s, now: Clock(now, 0),
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
                now_ms=lambda: clock[0],
            )

    path = tmp_path / "owner.json"
    if owner == "episode":
        machine = SamsungRegularTwoLegMachine(
            gateway=Gateway(),
            state_path=path,
            policy=SimpleNamespace(symbol="005930"),
            strategy_name="test-profile",
            schema="test-v1",
            legacy_schema="old",
            live_enabled=True,
            owner_registry=registry,
            adaptive_exit_services=services,
        )
        machine._state = _fresh_state(
            datetime.fromtimestamp(NOW / 1000, widget.KST), "test-v1"
        )
        leg = _new_leg(lot, "signal_close", 10000)
        leg.update(
            status="TARGET_OPEN",
            buy_order_no="0000001",
            buy_order_date=DATE,
            buy_filled_qty=10,
            fill_price=10000,
            position_qty=10,
            target_order_no=TARGET.order_no,
            target_order_date=DATE,
            target_owner_registry_intent_id=target,
            target_quantity=10,
            target_price=10100,
        )
        leg[SESSION_KEY] = session.to_payload()
        other = _new_leg("signal_close_minus_1tick", "signal_close_minus_1tick", 9995)
        other["status"] = "NO_FILL"
        machine._state.update(
            legs=[leg, other],
            position_qty=10,
            status="TARGET_OPEN",
            attempt_consumed=True,
            owned_order_nos=["0000001", TARGET.order_no],
        )

        def record():
            return machine._state["legs"][0][SESSION_KEY]

        def replace_record(value):
            machine._state["legs"][0][SESSION_KEY] = value

        def status():
            return machine._state.get("adaptive_exit_loop_status") or machine._state[
                "legs"
            ][0].get("adaptive_exit_loop_status")

        monkeypatch.setattr(
            machine,
            "_reconcile_target",
            lambda *a: pytest.fail("legacy target reentered"),
        )
        monkeypatch.setattr(
            machine,
            "_submit_planned_buys",
            lambda *a: pytest.fail("legacy BUY reentered"),
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
        orders = [
            dict(
                side="BUY",
                filled_qty=10,
                broker_accepted=True,
                status="FILLED",
                order_no="0000001",
                order_date=DATE,
            ),
            dict(
                side="SELL",
                order_role=widget.ORDER_ROLE_TAKE_PROFIT,
                requested_qty=10,
                filled_qty=0,
                limit_price=10100,
                broker_accepted=True,
                status="ACCEPTED",
                order_no=TARGET.order_no,
                order_date=DATE,
                owner_id=context.owner_id,
                owner_position_id=context.position_id,
                owner_client_intent_id=context.client_intent_id,
                owner_registry_intent_id=target,
                parent_entry_signal_id="signal",
            ),
        ]
        machine._state = dict(
            active_date=DATE,
            symbols={
                "005930": dict(
                    code="005930",
                    orders=orders,
                    entry_episode_open=True,
                    entry_signal_id="signal",
                    adaptive_exit_sessions={lot: session.to_payload()},
                )
            },
        )

        def record():
            state = machine._state["symbols"]["005930"]
            if "adaptive_exit_sessions" in state:
                return state["adaptive_exit_sessions"][lot]
            return state["adaptive_exit_history"][-1]["sessions"][lot]

        def replace_record(value):
            machine._state["symbols"]["005930"]["adaptive_exit_sessions"][lot] = value

        def status():
            return machine._state["symbols"]["005930"].get("adaptive_exit_loop_status")

        monkeypatch.setattr(
            machine, "_reconcile", lambda *a: pytest.fail("legacy target reentered")
        )
    machine._save()

    def tick():
        clock[0] += 1
        return machine.run_once(datetime.fromtimestamp(clock[0] / 1000, widget.KST))

    return SimpleNamespace(
        machine=machine,
        record=record,
        set_record=replace_record,
        status=status,
        tick=tick,
        wire=wire,
        flags=flags,
        clock=clock,
        owner=owner,
        path=path,
    )


def test_actual_owner_cancel_and_restart_never_reenters_legacy(loop):
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "CANCEL_PENDING"
    assert len(loop.wire.writes) == 1
    loop.machine._state = loop.machine._load_state()
    loop.tick()
    assert len(loop.wire.writes) == 1
    assert OwnerSession.from_payload(loop.record()).driver.orders.reserved_qty == 10


@pytest.mark.parametrize("missing", ["services", "lock", "authority", "guard", "quote"])
def test_dependencies_never_fall_through_to_original_order_loop(loop, missing):
    if missing == "services":
        loop.machine.adaptive_exit_services = None
    else:
        loop.flags[missing] = False
    loop.tick()
    assert not loop.wire.writes
    if missing in {"services", "lock", "authority"}:
        assert not loop.wire.calls


def test_invalid_session_preserved_and_old_order_loop_suppressed(loop):
    bad = loop.record()
    bad["canonical_sha256"] = "f" * 64
    loop.tick()
    assert loop.record() == bad and not loop.wire.calls
    assert "hash_invalid" in loop.status()


def test_disk_failure_stops_before_cancel_and_rolls_back_memory(loop, monkeypatch):
    before = deepcopy(loop.machine._state)
    monkeypatch.setattr(
        loop.machine, "_save", lambda: (_ for _ in ()).throw(OSError("disk"))
    )
    with pytest.raises(OSError):
        loop.tick()
    assert loop.machine._state == before
    assert not loop.wire.writes


def test_midnight_retains_original_order_and_no_cross_date_query(loop):
    loop.tick()
    original = deepcopy(loop.record()["driver"]["orders"]["target"])
    loop.wire.calls.clear()
    loop.clock[0] += 86400000
    loop.tick()
    assert loop.record()["driver"]["orders"]["target"] == original
    assert not loop.wire.calls
    assert "cross_date" in loop.record()["driver"]["alert_reason"]


def test_exact_partial_target_updates_remaining_without_cross_lot_sale(loop):
    loop.wire.detailed = [detail(cntr_qty="4", ord_remnq="6")]
    loop.wire.current = [current(cntr_qty="4", oso_qty="6")]
    loop.tick()
    assert loop.record()["driver"]["orders"]["target_filled_qty"] == 4
    assert not loop.wire.writes
    assert loop.record()["driver"]["orders"]["exit_filled_qty"] == 0
    loop.wire.write_body["cncl_qty"] = "6"
    loop.tick()
    assert loop.wire.writes[0]["payload"]["cncl_qty"] == "6"


def test_pending_buy_is_explicit_recovery_not_adaptive_cancel_or_new_buy(loop):
    if loop.owner == "episode":
        loop.machine._state["legs"][1]["status"] = "PLANNED"
        loop.machine._sync_aggregate()
    else:
        loop.machine._state["symbols"]["005930"]["orders"].append(
            dict(side="BUY", status="SUBMITTING", order_no="", order_date=DATE)
        )
    loop.tick()
    assert not loop.wire.calls
    assert "requires_owner_recovery" in loop.status()


def test_terminal_replacement_updates_quantity_not_profit_or_new_entry(loop):
    loop.tick()
    loop.wire.detailed, loop.wire.current = [detail(ord_remnq="0"), cancel_detail()], []
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "RESIDUAL_READY"
    loop.wire.write_body["ord_no"] = "0000004"
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "EXIT_WORKING"
    working_exit(loop.wire, fill=10, remaining=0)
    loop.flags["quote"] = False
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "FLAT"
    assert [r["api_id"] for r in loop.wire.writes] == ["kt10003", "kt10001"]
    if loop.owner == "episode":
        state = loop.machine._state
        assert state["position_qty"] == 0 and state["status"] == "ADAPTIVE_EXIT_FLAT"
        assert state["legs"][0]["target_filled_qty"] == 0
        assert state["legs"][0]["adaptive_exit_filled_qty"] == 10
        assert loop.machine._validate_state_contract(
            datetime.fromtimestamp(loop.clock[0] / 1000, widget.KST)
        )
    else:
        state = loop.machine._state["symbols"]["005930"]
        assert state["adaptive_exit_remaining_qty"] == 0
        assert not state.get("completed_episode_count")
    before = deepcopy(loop.record())
    loop.tick()
    assert loop.record() == before and len(loop.wire.writes) == 2


def test_wrong_original_owner_binding_fails_before_gateway(loop):
    session = OwnerSession.from_payload(loop.record())
    session = replace(session, context=replace(session.context, position_id="wrong"))
    loop.set_record(session.to_payload())
    loop.tick()
    assert not loop.wire.calls and "binding_mismatch" in loop.status()


def test_empty_or_malformed_claim_cannot_reset_or_enable_legacy(loop):
    loop.set_record(None)
    loop.tick()
    assert loop.record() is None and not loop.wire.calls


def test_widget_missing_snapshot_and_removed_catalog_still_resumes(loop):
    if loop.owner != "widget":
        pytest.skip("widget-specific catalog contract")
    assert not loop.machine.specs
    loop.tick()
    assert len(loop.wire.writes) == 1


def test_corrupt_custody_file_never_becomes_empty_portfolio(loop):
    loop.path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="owner_state_unreadable"):
        loop.machine._load_state()
    assert loop.path.read_text() == "{"


def test_episode_run_until_terminal_retains_unprotected_manager(loop, monkeypatch):
    if loop.owner != "episode":
        pytest.skip("episode-specific terminal loop")
    loop.machine._state["status"] = "BLOCKED"

    class Waiting(Exception):
        pass

    monkeypatch.setattr(
        "src.trading.order.regular_two_leg_machine.time_module.sleep",
        lambda *a: (_ for _ in ()).throw(Waiting()),
    )
    with pytest.raises(Waiting):
        loop.machine.run_until_terminal()


def test_lost_original_lock_never_overwrites_existing_owner_state(loop):
    before = loop.path.read_bytes()
    loop.flags["lock"] = False
    loop.tick()
    assert loop.path.read_bytes() == before
    assert not loop.wire.calls


def test_missing_verified_clock_never_calls_broker(loop):
    loop.machine.adaptive_exit_services = replace(
        loop.machine.adaptive_exit_services, clock_loader=lambda *a: None
    )
    loop.tick()
    assert not loop.wire.calls
    assert loop.status() == "owner_loop_verified_clock_missing"


def test_existing_owner_recovery_cannot_be_bypassed(loop):
    if loop.owner == "episode":
        loop.machine._state["owner_registry_reconciliation_required"] = True
    else:
        loop.machine._state["symbols"]["005930"]["exit_requested"] = True
    loop.tick()
    assert not loop.wire.calls
    assert "required" in loop.status()


def test_missing_services_do_not_discard_invalid_scope_or_state(loop):
    loop.machine.adaptive_exit_services = None
    before = deepcopy(loop.record())
    loop.tick()
    assert loop.record() == before
    assert loop.status() == "owner_loop_services_missing"


def test_loader_rejects_schema_change_without_erasing_frozen_record(loop):
    state = loop.machine._state
    state["schema" if loop.owner == "episode" else "schema_version"] = "bad"
    # Write test data directly, not via _save which stamps widget schema.
    import json

    loop.path.write_text(json.dumps(state), encoding="utf-8")
    before = loop.path.read_bytes()
    with pytest.raises(ValueError, match="schema_requires_recovery"):
        loop.machine._load_state()
    assert loop.path.read_bytes() == before


def test_all_current_episode_profiles_expose_same_reviewed_loop(tmp_path):
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    from src.trading.low_price_two_leg.machine import LowPriceTwoLegMachine
    from src.trading.samsung_morning_one_share.machine import (
        SamsungMorningOneShareMachine,
    )
    from src.trading.samsung_midday_one_share.machine import (
        SamsungMiddayOneShareMachine,
    )
    from src.trading.samsung_afternoon_one_share.machine import (
        SamsungAfternoonOneShareMachine,
    )

    services = OwnerLoopServices(
        lambda: False,
        lambda b: False,
        lambda **k: False,
        lambda *a: None,
        lambda *a: None,
    )
    profiles = profiles_for_target_date(date.fromisoformat(DATE))
    assert profiles
    machines = [
        LowPriceTwoLegMachine(
            profile=profile,
            gateway=object(),
            state_path=tmp_path / f"{key}.json",
            adaptive_exit_services=services,
        )
        for key, profile in profiles.items()
    ]
    machines += [
        cls(
            gateway=object(),
            state_path=tmp_path / f"{cls.__name__}.json",
            adaptive_exit_services=services,
        )
        for cls in (
            SamsungMorningOneShareMachine,
            SamsungMiddayOneShareMachine,
            SamsungAfternoonOneShareMachine,
        )
    ]
    for machine in machines:
        assert machine.adaptive_exit_services is services
        assert (
            machine._run_adaptive_owner_once.__func__
            is SamsungRegularTwoLegMachine._run_adaptive_owner_once
        )
        assert not machine.adaptive_exit_manager_required()
