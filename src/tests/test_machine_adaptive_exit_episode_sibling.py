"""Exact natural full-fill recovery in the real independent two-leg owner.

Location: order-owner integration tests, not a new producer or live launcher.
All broker responses, account identity, state and custody are isolated fixtures.
"""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests.test_machine_adaptive_exit_owner_loop import loop  # noqa: F401
from src.tests.test_machine_adaptive_exit_broker import DATE, detail, response
from src.trading.low_price_two_leg.gateway import SubmitResult
from src.trading.order.adaptive_exit.owner_loop import SESSION_KEY
from src.trading.order.adaptive_exit.runtime import OwnerSession

pytestmark = pytest.mark.parametrize("loop", ["episode"], indirect=True)


@pytest.fixture
def sibling(loop, monkeypatch):  # noqa: F811 - explicitly imported pytest fixture
    machine = loop.machine
    leg = machine._state["legs"][1]
    leg.update(
        status="BUY_OPEN",
        buy_order_no="0000009",
        buy_order_date=DATE,
        buy_submit_attempt_count=1,
    )
    context = machine._episode_owner_context(leg=leg, action="NEW", ordinal="BUY:SOR:1")
    intent = machine.owner_registry.reserve(
        context=context,
        symbol="005930",
        side="BUY",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    machine.owner_registry.transition(
        intent, state="ORDER_BOUND", broker_order_no="0000009"
    )
    leg["buy_owner_registry_intent_id"] = intent
    machine._own_order("0000009")
    machine._sync_aggregate()
    machine._save()
    loop.buy_rows = [
        detail(ord_no="0000009", cntr_qty="10", ord_remnq="0", cntr_uv="9995")
    ]
    loop.buy_current = []
    loop.buy_queries = []
    loop.original_target_writes = []
    make = machine.gateway.adaptive_exit_adapter

    def factory(**kwargs):
        adapter = make(**kwargs)
        original_post = adapter.post

        def post(**request):
            payload = request["payload"]
            if payload.get("sell_tp") == "2" or payload.get("trde_tp") == "2":
                loop.buy_queries.append(request)
                field, rows = (
                    ("acnt_ord_cntr_prps_dtl", loop.buy_rows)
                    if request["api_id"] == "kt00007"
                    else ("oso", loop.buy_current)
                )
                return response({"return_code": 0, field: rows})
            return original_post(**request)

        adapter.post = post
        return adapter

    monkeypatch.setattr(machine.gateway, "adaptive_exit_adapter", factory)
    machine.policy.route = "SOR"
    machine.policy.target_price = lambda fill: fill + 100

    def reserve(**kwargs):
        bound = machine._episode_owner_context(
            leg=kwargs["leg"], action=kwargs["action"], ordinal=kwargs["ordinal"]
        )
        key = machine.owner_registry.reserve(
            context=bound,
            symbol="005930",
            side=kwargs["side"],
            quantity=kwargs["quantity"],
            route=kwargs["route"],
            order_date=DATE,
        )
        return key, bound

    def target(**kwargs):
        loop.original_target_writes.append(kwargs)
        return SubmitResult(True, order_no="0000008")

    monkeypatch.setattr(machine, "_reserve_episode_intent", reserve)
    monkeypatch.setattr(machine.gateway, "submit_limit_sell", target, raising=False)
    monkeypatch.setattr(
        machine,
        "_reconcile_buy",
        lambda *a: pytest.fail("legacy BUY/cancel loop entered"),
    )
    loop.sibling = leg
    return loop


def test_full_buy_projects_once_then_original_target_owner_resumes(sibling):
    before = deepcopy(sibling.record())
    result = sibling.tick()
    assert (
        result["adaptive_exit_loop_status"]
        == "sibling_full_buy_reconciled_original_target_pending"
    )
    leg = sibling.sibling
    assert leg["status"] == "POSITION_OPEN" and leg["position_qty"] == 10
    assert leg["fill_price"] == 9995 and not leg["buy_filled_at"]
    assert leg["target_price"] == 0 and SESSION_KEY not in leg
    assert sibling.record() == before
    assert len(sibling.buy_queries) == 2
    assert not sibling.wire.writes and not sibling.original_target_writes
    sibling.machine._state = sibling.machine._load_state()
    sibling.tick()
    assert len(sibling.buy_queries) == 2
    assert sibling.original_target_writes == [{"price": 10095, "quantity": 10}]
    other = sibling.machine._state["legs"][1]
    assert other["status"] == "TARGET_OPEN" and other["target_order_no"] == "0000008"
    assert OwnerSession.from_payload(sibling.record()).position.open_qty == 10


@pytest.mark.parametrize("missing", ["services", "lock", "authority", "disabled"])
def test_missing_authority_cannot_use_sibling_recovery_or_original_target(
    sibling, missing
):
    if missing == "services":
        sibling.machine.adaptive_exit_services = None
    elif missing == "disabled":
        sibling.machine.live_enabled = False
    else:
        sibling.flags[missing] = False
    sibling.tick()
    assert not sibling.buy_queries and not sibling.wire.writes
    assert not sibling.original_target_writes
    assert sibling.sibling["status"] == "BUY_OPEN"


@pytest.mark.parametrize(
    "problem", ["partial", "absent", "price_missing", "price_conflict", "wrong_route"]
)
def test_unproved_buy_preserves_original_state_and_no_order_path(sibling, problem):
    if problem == "partial":
        sibling.buy_rows[0].update(cntr_qty="4", ord_remnq="6")
    elif problem == "absent":
        sibling.buy_rows.clear()
    elif problem == "price_missing":
        sibling.buy_rows[0].pop("cntr_uv")
    elif problem == "price_conflict":
        sibling.buy_rows.append({**sibling.buy_rows[0], "cntr_uv": "9990"})
    else:
        sibling.buy_rows[0]["dmst_stex_tp"] = "unknown"
    before = deepcopy(sibling.sibling)
    result = sibling.tick()
    assert result["adaptive_exit_loop_status"].startswith(
        "adaptive_sibling_full_buy_wait:"
    )
    assert sibling.sibling == before
    assert not sibling.wire.writes and not sibling.original_target_writes


@pytest.mark.parametrize(
    "problem",
    [
        "cancel_requested",
        "cancel_intent",
        "wrong_leg",
        "wrong_date",
        "ambiguous",
        "planned",
    ],
)
def test_unsupported_sibling_identity_or_cancel_is_not_normalized(sibling, problem):
    leg = sibling.sibling
    if problem == "cancel_requested":
        leg["buy_cancel_requested"] = True
    elif problem == "cancel_intent":
        context = sibling.machine._episode_owner_context(
            leg=leg, action="CANCEL", ordinal=1
        )
        sibling.machine.owner_registry.reserve(
            context=context,
            symbol="005930",
            side="BUY",
            quantity=10,
            route="SOR",
            order_date=DATE,
            action="CANCEL",
            original_order_no="0000009",
        )
    elif problem == "wrong_leg":
        leg["buy_submit_attempt_count"] = 2
    elif problem == "wrong_date":
        leg["buy_order_date"] = "2026-09-08"
    elif problem == "ambiguous":
        leg["status"] = "BUY_SUBMITTING"
    else:
        leg["status"] = "PLANNED"
    sibling.machine._sync_aggregate()
    sibling.tick()
    assert not sibling.buy_queries and not sibling.wire.writes
    assert not sibling.original_target_writes


def test_registry_full_fill_before_owner_projection_is_idempotent(sibling):
    registry = sibling.machine.owner_registry
    leg = sibling.sibling
    context = sibling.machine._episode_owner_context(
        leg=leg, action="NEW", ordinal="BUY:SOR:1"
    )
    registry.record_fill(
        context=context,
        symbol="005930",
        side="BUY",
        order_quantity=10,
        order_date=DATE,
        broker_order_no="0000009",
        cumulative_filled_qty=10,
    )
    registry.transition(
        leg["buy_owner_registry_intent_id"],
        state="ORDER_TERMINAL",
        broker_order_no="0000009",
    )
    sibling.tick()
    assert (
        leg["status"] == "POSITION_OPEN"
        and registry.owner_position_qty(context.position_id, symbol="005930") == 20
    )


def test_lost_lock_after_read_cannot_project_or_submit(sibling, monkeypatch):
    original = sibling.machine.adaptive_exit_services.authorize_binding

    def authorize(binding):
        if len(sibling.buy_queries) == 2:
            sibling.flags["lock"] = False
        return original(binding)

    sibling.machine.adaptive_exit_services = replace(
        sibling.machine.adaptive_exit_services, authorize_binding=authorize
    )
    before = sibling.path.read_bytes()
    sibling.tick()
    assert sibling.path.read_bytes() == before
    assert sibling.sibling["status"] == "BUY_OPEN"
    assert not sibling.wire.writes and not sibling.original_target_writes


def test_projection_save_failure_retains_retryable_full_buy(sibling, monkeypatch):
    before = deepcopy(sibling.machine._state)

    def fail():
        raise OSError("test disk write failure")

    monkeypatch.setattr(sibling.machine, "_save", fail)
    with pytest.raises(OSError):
        sibling.tick()
    assert sibling.machine._state == before
    assert not sibling.wire.writes and not sibling.original_target_writes


@pytest.mark.parametrize("lost", ["lock", "authority"])
def test_original_target_does_not_write_after_reservation_loses_authority(
    sibling, monkeypatch, lost
):
    sibling.tick()
    reserve = sibling.machine._reserve_episode_intent

    def reserve_then_lose(**kwargs):
        result = reserve(**kwargs)
        sibling.flags[lost] = False
        return result

    monkeypatch.setattr(sibling.machine, "_reserve_episode_intent", reserve_then_lose)
    sibling.tick()
    assert not sibling.original_target_writes
    assert sibling.machine._state["legs"][1]["status"] == "TARGET_SUBMITTING"


@pytest.mark.parametrize("missing", ["services", "authority"])
def test_already_projected_sibling_cannot_bypass_missing_services(sibling, missing):
    sibling.tick()
    if missing == "services":
        sibling.machine.adaptive_exit_services = None
    else:
        sibling.flags["authority"] = False
    sibling.tick()
    assert not sibling.original_target_writes and not sibling.wire.writes


@pytest.mark.parametrize("changed", ["target_policy", "receipt_hash", "fill_price"])
def test_changed_original_target_or_full_buy_receipt_cannot_submit(sibling, changed):
    sibling.tick()
    if changed == "target_policy":
        sibling.machine.policy.target_price = lambda fill: fill + 105
    elif changed == "receipt_hash":
        sibling.sibling["adaptive_sibling_full_buy_receipt"]["source_sha256"] = "f" * 64
    else:
        sibling.sibling["fill_price"] = 10000
    sibling.tick()
    assert not sibling.original_target_writes
    assert not sibling.wire.writes
    assert (
        sibling.machine._state["adaptive_exit_loop_status"]
        == "adaptive_sibling_original_target_binding_mismatch"
    )


def test_next_date_does_not_relabel_old_buy_as_new_target(sibling):
    sibling.tick()
    sibling.clock[0] += 24 * 60 * 60 * 1000
    sibling.tick()
    assert not sibling.original_target_writes and not sibling.wire.writes
    assert (
        sibling.machine._state["adaptive_exit_loop_status"]
        == "adaptive_sibling_cross_date_target_requires_owner_recovery"
    )


def test_published_projection_then_fsync_error_resumes_without_duplicate_read(
    sibling, monkeypatch
):
    save = sibling.machine._save

    def publish_then_fail():
        save()
        raise OSError("test directory fsync failure")

    monkeypatch.setattr(sibling.machine, "_save", publish_then_fail)
    with pytest.raises(OSError):
        sibling.tick()
    assert sibling.machine._state["legs"][1]["status"] == "BUY_OPEN"
    sibling.machine._state = sibling.machine._load_state()
    assert sibling.machine._state["legs"][1]["status"] == "POSITION_OPEN"
    monkeypatch.setattr(sibling.machine, "_save", save)
    sibling.tick()
    assert len(sibling.buy_queries) == 2
    assert sibling.original_target_writes == [{"price": 10095, "quantity": 10}]


@pytest.mark.parametrize("veto", ["blocked", "pending_confirmation", "reconciliation"])
def test_owner_veto_arriving_during_read_is_not_erased_by_projection(sibling, veto):
    original = sibling.machine.adaptive_exit_services.authorize_binding

    def authorize(binding):
        if len(sibling.buy_queries) == 2:
            if veto == "blocked":
                sibling.machine._state["status"] = "BLOCKED"
            elif veto == "pending_confirmation":
                sibling.machine._state["pending_entry_confirmation"] = {
                    "unexpected": True
                }
            else:
                sibling.machine._state["owner_registry_reconciliation_required"] = True
        return original(binding)

    sibling.machine.adaptive_exit_services = replace(
        sibling.machine.adaptive_exit_services, authorize_binding=authorize
    )
    sibling.tick()
    assert sibling.sibling["status"] == "BUY_OPEN"
    assert not sibling.wire.writes and not sibling.original_target_writes
    if veto == "blocked":
        assert sibling.machine._state["status"] == "BLOCKED"
