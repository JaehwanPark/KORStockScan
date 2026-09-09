"""Concrete port tests: tmp owner journal + fake official wire, no broker calls."""

from dataclasses import asdict, replace
import json

import pytest

from src.tests.test_machine_adaptive_exit_broker import (  # noqa: F401
    DATE,
    NOW,
    TARGET,
    current,
    detail,
    setup as broker_setup,
)
from src.tests.test_machine_adaptive_exit_decision import inputs, trail_inputs
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.driver import DriverState, ExecutionBounds
from src.trading.order.adaptive_exit.models import Clock, DecisionState
from src.trading.order.adaptive_exit.reducer import ExitState, OrderKey
from src.trading.order.adaptive_exit.runtime import (
    OwnerSession,
    RegisteredOwnerExitPort,
)
from src.trading.order.adaptive_exit.source import OwnerScope
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerRegistryConflict,
)


@pytest.fixture(params=["episode", "widget"])
def runtime(request, tmp_path):
    adapter, wire, registry = request.getfixturevalue("broker_setup")
    owner = request.param
    if owner == "widget":
        registry = OrderOwnerRegistry(tmp_path / "widget-registry.jsonl")
        adapter.context = replace(
            adapter.context, owner_type="widget_auto_trade", owner_id="widget:test"
        )
        registry.register_migrated_position(
            context=adapter.context,
            symbol="005930",
            quantity=10,
            average_price=10000,
            route="SOR",
            order_date=DATE,
            broker_order_no="0000001",
            evidence_sha256="a" * 64,
        )
        target = registry.reserve(
            context=replace(adapter.context, client_intent_id="widget-target"),
            symbol="005930",
            side="SELL",
            quantity=10,
            route="SOR",
            order_date=DATE,
        )
        registry.transition(
            target, state="ORDER_BOUND", broker_order_no=TARGET.order_no
        )
    saved, now, flags = [], [NOW], {"authorized": True, "guard": True, "locked": True}

    def initial(*, trailing=False):
        policy, p, snap, _, _ = trail_inputs() if trailing else inputs()
        scope = OwnerScope(owner, "test-profile", "005930", "SOR", "KRX_REGULAR")
        policy = replace(policy, scope_key=scope.key)
        policy = replace(
            policy,
            policy_hash=canonical_sha256(
                {k: v for k, v in asdict(policy).items() if k != "policy_hash"}
            ),
        )
        p = replace(
            p,
            owner_id=owner,
            scope_key=scope.key,
            cost_contract_hash="c" * 64,
            first_fill_at_ms=NOW - (20000 if trailing else 60000),
        )
        target = registry.order_owner(order_date=DATE, broker_order_no=TARGET.order_no)
        return (
            OwnerSession(
                policy,
                p,
                ExecutionBounds(
                    3000, 2, 5000, "exit_with_fresh_guard", "retain_manager_and_alert"
                ),
                adapter.context,
                target["intent_id"],
                "b" * 64,
                DriverState(
                    ExitState(
                        p.owner_id,
                        p.episode_id,
                        p.lot_id,
                        policy.policy_hash,
                        p.position_epoch,
                        TARGET,
                        p.open_qty,
                    ),
                    DecisionState(
                        policy.policy_hash,
                        p.position_epoch,
                        p.first_fill_at_ms,
                        p.open_qty,
                    ),
                ),
            ),
            snap,
        )

    def build(session, *, fail_phase=None, authorize=True):
        def save(payload):
            if payload["driver"]["orders"]["phase"] == fail_phase:
                raise OSError("disk failure")
            saved.append(json.loads(json.dumps(payload)))

        def factory(guard):
            return RegisteredSellAdapter(
                post=wire,
                registry=registry,
                context=session.context,
                symbol="005930",
                routes=("SOR",),
                policy_hash=session.policy.policy_hash,
                maximum_quantity=10,
                require_write_authority=lambda: None,
                write_guard=guard,
                now_ms=lambda: now[0],
            )

        return RegisteredOwnerExitPort(
            session=session,
            adapter_factory=factory,
            persist_record=save,
            lock_held=lambda: flags["locked"],
            owner_guard=lambda *a, **k: flags["guard"],
            authorize_binding=(
                (lambda binding: flags["authorized"]) if authorize else None
            ),
        )

    def tick(port, *, bid=10010, quote=True, seq=None):
        now[0] += 1
        _, original = initial()
        snap = replace(
            original,
            scope_key=port.session.policy.scope_key,
            position_epoch=port.session.remaining_position.position_epoch,
            observed_at_ms=now[0],
            quote_at_ms=now[0],
            sequence=seq or now[0],
            best_ask=bid + 5,
            bid_levels=((bid, 10),),
            supportive=port.session.policy.trail is not None,
        )
        return port.step(snapshot=snap if quote else None, clock=Clock(now[0], 0))

    wire.write_body["cncl_qty"] = "10"
    return initial, build, tick, wire, registry, saved, now, flags


def cancelled(runtime, *, trailing=False):
    initial, build, tick, wire, *_ = runtime
    session, _ = initial(trailing=trailing)
    port = build(session)
    tick(port, bid=10065 if trailing else 10010)
    assert port.session.driver.orders.phase == "CANCEL_PENDING"
    wire.detailed, wire.current = [detail(ord_remnq="0")], []
    tick(port, quote=False)
    assert port.session.driver.orders.phase == "RESIDUAL_READY"
    return port


def working_exit(wire, *, fill=0, remaining=10):
    wire.detailed = [
        detail(ord_remnq="0"),
        detail(ord_no="0000004", cntr_qty=str(fill), ord_remnq=str(remaining)),
    ]
    wire.current = (
        []
        if not remaining
        else [current(ord_no="0000004", cntr_qty=str(fill), oso_qty=str(remaining))]
    )


def test_concrete_cancel_sell_fill_owner_registry_and_roundtrip(runtime):
    _, build, tick, wire, registry, saved, *_ = runtime
    port = cancelled(runtime)
    wire.write_body["ord_no"] = "0000004"
    tick(port)
    assert port.session.driver.orders.phase == "EXIT_WORKING"
    assert [row["api_id"] for row in wire.writes] == ["kt10003", "kt10001"]
    restored = OwnerSession.from_payload(saved[-1])
    assert restored == port.session
    assert restored.manager_required
    working_exit(wire, fill=10, remaining=0)
    port = build(restored)
    tick(port, quote=False)
    assert port.session.driver.orders.phase == "FLAT"
    assert not port.session.manager_required
    assert registry.owner_position_qty("position:test", symbol="005930") == 0


def test_cancel_ack_is_not_terminal_or_permission_for_second_sell(runtime):
    initial, build, tick, wire, *_ = runtime
    port = build(initial()[0])
    tick(port)
    for _ in range(3):
        tick(port, quote=False)
    assert port.session.driver.orders.phase == "CANCEL_PENDING"
    assert len(wire.writes) == 1


def test_partial_fill_while_cancel_pending_rebinds_without_clock_reset(runtime):
    initial, build, tick, wire, _, saved, *_ = runtime
    port = build(initial()[0])
    anchor = port.session.position.first_fill_at_ms
    tick(port)
    wire.detailed = [detail(cntr_qty="3", ord_remnq="7")]
    wire.current = [current(cntr_qty="3", oso_qty="7")]
    tick(port, quote=False)
    assert port.session.driver.orders.open_qty == 7
    port = build(OwnerSession.from_payload(saved[-1]))
    tick(port, quote=False)
    assert port.session.driver.decision.open_qty == 7
    assert (
        port.session.remaining_position.position_epoch
        != port.session.position.position_epoch
    )
    assert port.session.position.first_fill_at_ms == anchor
    wire.detailed, wire.current = [detail(cntr_qty="3", ord_remnq="0")], []
    tick(port, quote=False)
    wire.write_body["ord_no"] = "0000004"
    tick(port)
    assert wire.writes[-1]["payload"]["ord_qty"] == "7"


def test_partial_target_fill_precedes_any_exit_decision(runtime):
    initial, build, tick, wire, *_ = runtime
    port = build(initial()[0])
    wire.detailed = [detail(cntr_qty="4", ord_remnq="6")]
    wire.current = [current(cntr_qty="4", oso_qty="6")]
    tick(port)
    assert not wire.writes
    wire.write_body["cncl_qty"] = "6"
    tick(port)
    assert wire.writes[-1]["payload"]["cncl_qty"] == "6"


def test_ack_then_save_crash_recovers_bound_order_without_resubmit(runtime):
    _, build, tick, wire, _, saved, *_ = runtime
    port = cancelled(runtime)
    port = build(port.session, fail_phase="EXIT_WORKING")
    wire.write_body["ord_no"] = "0000004"
    with pytest.raises(OSError):
        tick(port)
    assert saved[-1]["driver"]["orders"]["phase"] == "EXIT_SUBMITTING"
    working_exit(wire)
    port = build(OwnerSession.from_payload(saved[-1]))
    tick(port, quote=False)
    assert port.session.driver.orders.exit_order == OrderKey(DATE, "0000004")
    assert len(wire.writes) == 2


def test_ambiguous_submit_retains_reservation_no_blind_retry(runtime):
    _, build, tick, wire, _, saved, *_ = runtime
    port = cancelled(runtime)
    wire.crash = True
    tick(port)
    port = build(OwnerSession.from_payload(saved[-1]))
    for _ in range(3):
        tick(port, quote=False)
    assert port.session.driver.alert_reason == "ambiguous_submit_reservation_retained"
    assert port.session.manager_required
    assert len(wire.writes) == 2


def test_no_quote_can_reconcile_but_cannot_issue_replacement(runtime):
    _, _, tick, wire, *_ = runtime
    port = cancelled(runtime)
    tick(port, quote=False)
    assert port.session.driver.alert_reason == "fresh_executable_snapshot_required"
    assert len(wire.writes) == 1


def test_trailing_state_and_decision_are_atomic_at_every_save(runtime):
    _, build, tick, _, _, saved, *_ = runtime
    port = cancelled(runtime, trailing=True)
    tick(port, bid=10065)
    assert port.session.driver.orders.phase == "TRAIL_ACTIVE"
    tick(port, bid=10080)
    for record in saved:
        restored = OwnerSession.from_payload(record)
        if restored.driver.orders.phase == "TRAIL_ACTIVE":
            assert restored.driver.decision.trail_active
            assert (
                restored.driver.decision.stop_price == restored.driver.orders.stop_price
            )
    restored = build(OwnerSession.from_payload(saved[-1]))
    assert restored.session.driver.decision.stop_price == 10065


@pytest.mark.parametrize("flag", ["authorized", "guard", "locked"])
def test_each_independent_authority_veto_blocks_broker_writes(runtime, flag):
    initial, build, tick, wire, _, _, _, flags = runtime
    port = build(initial()[0])
    flags[flag] = False
    if flag == "locked":
        with pytest.raises(PermissionError):
            tick(port)
    else:
        tick(port)
    assert not wire.writes
    assert port.session.manager_required


def test_self_hash_does_not_authorize_any_runtime_or_broker_read(runtime):
    initial, build, tick, wire, *_ = runtime
    port = build(OwnerSession.from_payload(initial()[0].to_payload()), authorize=False)
    tick(port)
    assert wire.calls == []
    assert port.session.driver.alert_reason == "frozen_policy_authority_missing"


def test_cross_date_keeps_exact_order_and_manager_without_undated_join(runtime):
    _, build, tick, wire, _, saved, now, _ = runtime
    port = cancelled(runtime)
    now[0] += 86400000
    port = build(OwnerSession.from_payload(saved[-1]))
    wire.calls.clear()
    # Return to an ambiguous cancel state, as saved before terminal confirmation.
    pending = next(
        p for p in saved if p["driver"]["orders"]["phase"] == "CANCEL_PENDING"
    )
    port = build(OwnerSession.from_payload(pending))
    tick(port, quote=False)
    assert port.session.driver.orders.target == TARGET
    assert port.session.manager_required and not wire.calls
    assert (
        port.session.driver.alert_reason
        == "broker_source_gap:cross_date_current_ledger_requires_owner_recovery"
    )


@pytest.mark.parametrize(
    "kind",
    [
        "hash",
        "unknown",
        "quantity",
        "cost",
        "policy",
        "target",
        "timestamp",
        "decision",
    ],
)
def test_corrupt_or_rehashed_invalid_record_never_loads(runtime, kind):
    initial, *_ = runtime
    payload = json.loads(json.dumps(initial()[0].to_payload()))
    if kind == "hash":
        payload["canonical_sha256"] = "0" * 64
    elif kind == "unknown":
        payload["new_authority"] = True
    elif kind == "quantity":
        payload["driver"]["orders"]["buy_filled_qty"] = 11
    elif kind == "cost":
        payload["position"]["cost_contract_hash"] = "missing"
    elif kind == "policy":
        payload["policy"]["loss_budget_pct"] = 99
    elif kind == "target":
        payload["driver"]["orders"]["target"]["trading_date"] = "yesterday"
    elif kind == "timestamp":
        payload["driver"]["submitted_at_ms"] = True
    else:
        payload["driver"]["decision"]["open_qty"] = 100
    if kind != "hash":
        payload["canonical_sha256"] = canonical_sha256(payload)
    with pytest.raises(ValueError):
        OwnerSession.from_payload(payload)


def test_persistence_failure_prevents_cancel_and_memory_advance(runtime):
    initial, build, tick, wire, *_ = runtime
    port = build(initial()[0], fail_phase="CANCEL_PENDING")
    with pytest.raises(OSError):
        tick(port)
    assert port.session.driver.orders.phase == "INTENT_PERSISTED"
    assert not wire.writes


def test_another_target_same_owner_position_is_not_adopted(runtime):
    initial, build, *_ = runtime
    session = replace(initial()[0], target_intent_id="another-lot-intent")
    with pytest.raises(ValueError, match="independent_target"):
        build(session)


@pytest.mark.parametrize("latency_ms", [1, 600, 1500])
def test_real_read_latency_not_misclassified_as_future_proof(runtime, latency_ms):
    initial, build, tick, wire, _, _, now, _ = runtime
    port = build(initial()[0])
    original = port._adapter.post

    def slow(**kwargs):
        result = original(**kwargs)
        if kwargs["api_id"] == "ka10075":
            now[0] += latency_ms
        return result

    port._adapter.post = slow
    tick(port)
    assert port.session.driver.alert_reason != "target_reconciliation_pending"
    if latency_ms > port.session.policy.max_quote_age_ms:
        assert port.session.driver.alert_reason == "stale_quote"
        assert not wire.writes
    else:
        assert port.session.driver.orders.phase == "CANCEL_PENDING"
        if latency_ms * 2 > port.session.policy.max_quote_age_ms:
            assert not wire.writes  # Quote expires during the second read.
            port._adapter.post = original
            tick(port)  # No broker reservation: resume the persisted cancel once.
            assert len(wire.writes) == 1
        wire.detailed, wire.current = [detail(ord_remnq="0")], []
        tick(port, quote=False)
        assert port.session.driver.orders.phase == "RESIDUAL_READY"


def test_authority_revoked_during_broker_read_is_rechecked_before_cancel(runtime):
    initial, build, tick, wire, _, _, _, flags = runtime
    port = build(initial()[0])
    original = port._adapter.post

    def revoke(**kwargs):
        result = original(**kwargs)
        if kwargs["api_id"] == "ka10075":
            flags["authorized"] = False
        return result

    port._adapter.post = revoke
    tick(port)
    assert not wire.writes
    assert port.session.driver.alert_reason == "owner_guard_blocked"


def test_latest_replacement_partial_fill_ttl_and_second_attempt_uses_last_order(
    runtime,
):
    _, build, tick, wire, _, saved, now, _ = runtime
    port = cancelled(runtime)
    wire.write_body["ord_no"] = "0000004"
    tick(port)
    working_exit(wire, fill=3, remaining=7)
    now[0] += 3000
    wire.write_body.update(ord_no="0000005", base_orig_ord_no="0000004", cncl_qty="7")
    tick(port, quote=False)
    assert port.session.driver.orders.phase == "EXIT_CANCEL_PENDING"
    assert wire.writes[-1]["payload"]["orig_ord_no"] == "0000004"
    working_exit(wire, fill=3, remaining=0)
    port = build(OwnerSession.from_payload(saved[-1]))
    tick(port, quote=False)
    wire.write_body["ord_no"] = "0000006"
    tick(port)
    assert port.session.driver.orders.exit_order == OrderKey(DATE, "0000006")
    assert wire.writes[-1]["payload"]["ord_qty"] == "7"
    # Bound second successor is recoverable through the same original lot.
    build(OwnerSession.from_payload(saved[-1]))


def test_cancel_persisted_but_not_dispatched_recovers_once_with_fresh_quote(runtime):
    initial, build, tick, wire, _, saved, *_ = runtime
    port = build(initial()[0])
    original = port._adapter.cancel_owned_sell
    port._adapter.cancel_owned_sell = lambda *a, **k: (_ for _ in ()).throw(
        OSError("crash before reserve")
    )
    with pytest.raises(OSError):
        tick(port)
    assert not wire.writes
    assert saved[-1]["driver"]["orders"]["phase"] == "CANCEL_PENDING"
    port._adapter.cancel_owned_sell = original
    port = build(OwnerSession.from_payload(saved[-1]))
    tick(port, quote=False)
    assert not wire.writes
    tick(port)
    tick(port)
    assert len(wire.writes) == 1


def test_cancel_ambiguous_reservation_never_retries_even_with_fresh_quote(runtime):
    initial, build, tick, wire, _, saved, *_ = runtime
    port = build(initial()[0])
    wire.crash = True
    tick(port)
    port = build(OwnerSession.from_payload(saved[-1]))
    tick(port)
    tick(port)
    assert len(wire.writes) == 1


def test_registry_client_lookup_is_readonly_and_rejects_cross_owner_account(
    request,
    monkeypatch,
):
    adapter, _, registry = request.getfixturevalue("broker_setup")
    context = replace(adapter.context, client_intent_id="target")
    before = registry.path.read_bytes()
    row = registry.intent_for_client(context=context)
    assert row["broker_order_no"] == TARGET.order_no
    assert registry.path.read_bytes() == before
    with pytest.raises(OwnerRegistryConflict, match="client_binding_conflict"):
        registry.intent_for_client(context=replace(context, owner_id="another-owner"))
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "different-account")
    with pytest.raises(OwnerRegistryConflict, match="client_binding_conflict"):
        registry.intent_for_client(context=context)
