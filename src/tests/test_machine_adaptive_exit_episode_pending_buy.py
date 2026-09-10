"""Pending BUY closure through the real episode loop, with isolated fake wire.

Order integration tests belong here, not in a report or live launcher module.
"""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, time

import pytest

from src.tests.test_machine_adaptive_exit_owner_loop import loop  # noqa: F401
from src.tests.test_machine_adaptive_exit_episode_sibling import sibling  # noqa: F401
from src.tests.test_machine_adaptive_exit_broker import DATE, detail, current, response
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.episode_pending_buy import (
    KEY,
    EpisodePendingBuyServices,
    _PendingBuy,
)
from src.trading.order.adaptive_exit.buy_cancel import PricedCancelledBuySnapshot
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.samsung_morning_one_share.machine import SamsungMorningOneShareMachine

pytestmark = pytest.mark.parametrize("loop", ["episode"], indirect=True)


@pytest.fixture
def pending(sibling, monkeypatch):  # noqa: F811
    p = sibling
    p.allow_pending = True
    p.cancel_writes = []
    p.authorizations = []
    p.cancel_mode = "accept"
    p.elapsed = 2
    p.bar_reads = []
    p.machine.policy.entry_valid_completed_bars = 2
    p.machine._state["signal_bar"] = DATE + "T12:58:00+09:00"

    def elapsed(now):
        p.bar_reads.append(now)
        return p.elapsed

    monkeypatch.setattr(p.machine, "_completed_bars_after_signal", elapsed)

    def authorize(request):
        p.authorizations.append(deepcopy(request))
        return p.allow_pending

    p.machine.adaptive_exit_services = replace(
        p.machine.adaptive_exit_services,
        pending_buy=EpisodePendingBuyServices(5000, authorize),
    )
    original = p.machine.gateway.adaptive_exit_adapter

    def factory(**kwargs):
        adapter = original(**kwargs)
        post = adapter.post

        def call(**request):
            if (
                request["api_id"] == "kt10003"
                and request["payload"]["orig_ord_no"] == "0000009"
            ):
                p.cancel_writes.append(request)
                if p.cancel_mode == "timeout":
                    raise TimeoutError("isolated transport timeout")
                if p.cancel_mode == "reject":
                    return response({"return_code": 1, "return_msg": "rejected"})
                return response(
                    {
                        "return_code": 0,
                        "ord_no": "0000010",
                        "base_orig_ord_no": "0000009",
                        "cncl_qty": request["payload"]["cncl_qty"],
                        "dmst_stex_tp": "SOR",
                    }
                )
            return post(**request)

        adapter.post = call
        return adapter

    monkeypatch.setattr(p.machine.gateway, "adaptive_exit_adapter", factory)
    market(p, filled=2, remaining=8)
    p.machine._save()
    return p


def market(p, *, filled, remaining, confirmed=None, requested=8, price="9995"):
    p.buy_rows = [
        detail(
            ord_no="0000009",
            cntr_qty=str(filled),
            ord_remnq=str(remaining),
            cntr_uv=price,
        )
    ]
    p.buy_current = (
        [current(ord_no="0000009", cntr_qty=str(filled), oso_qty=str(remaining))]
        if remaining
        else []
    )
    if confirmed is not None:
        p.buy_rows.append(
            detail(
                ord_no="0000010",
                ori_ord="0000009",
                ord_qty=str(requested),
                cntr_qty="0",
                ord_remnq="0",
                cnfm_qty=str(confirmed),
                cnfm_tm="12:59:59",
            )
        )


def leg(p):
    return p.machine._state["legs"][1]


def test_partial_cancel_then_late_fill_routes_only_exact_filled_sibling(pending):
    p = pending
    selected = deepcopy(p.record())
    assert (
        p.tick()["adaptive_exit_loop_status"] == "pending_buy_cancel_confirmation_wait"
    )
    assert (
        len(p.cancel_writes) == 1 and p.cancel_writes[0]["payload"]["cncl_qty"] == "8"
    )
    assert not p.bar_reads and not p.original_target_writes and p.record() == selected
    assert leg(p)["status"] == "BUY_OPEN" and leg(p)[KEY]["phase"] == "ACK_SAVED"
    market(p, filled=4, remaining=0, confirmed=6, price="10005")
    p.machine._state = p.machine._load_state()
    assert (
        p.tick()["adaptive_exit_loop_status"]
        == "pending_buy_terminal_original_target_pending"
    )
    assert leg(p)["buy_filled_qty"] == 4 and leg(p)["position_qty"] == 4
    assert not leg(p)["buy_filled_at"] and leg(p)["fill_price"] == 10005
    assert leg(p)[KEY]["phase"] == "PROJECTED"
    assert not p.original_target_writes
    assert canonical_sha256(p.record()) == canonical_sha256(selected)
    p.tick()
    assert p.original_target_writes == [{"price": 10105, "quantity": 4}]
    assert len(p.cancel_writes) == 1


def test_zero_fill_expired_sor_terminal_is_no_fill_not_zero_pnl(pending):
    p = pending
    market(p, filled=0, remaining=10, price=None)
    p.tick()
    assert p.cancel_writes[0]["payload"]["cncl_qty"] == "10" and len(p.bar_reads) == 1
    market(p, filled=0, remaining=0, confirmed=10, requested=10, price=None)
    p.tick()
    assert leg(p)["status"] == "NO_FILL" and leg(p)["buy_filled_qty"] == 0
    receipt = leg(p)["adaptive_sibling_full_buy_receipt"]
    assert receipt["fill_price"] is None and receipt["original_target_price"] is None
    assert receipt["realized_pnl_status"] == "unreconciled_exact_fill_cost_required"
    p.tick()
    assert not p.original_target_writes


@pytest.mark.parametrize("elapsed", [None, 0, 1])
def test_unexpired_original_signal_never_cancels(pending, elapsed):
    pending.elapsed = elapsed
    market(pending, filled=0, remaining=10)
    result = pending.tick()
    assert result["adaptive_exit_loop_status"] == "pending_buy_original_validity_wait"
    assert not pending.cancel_writes and KEY not in leg(pending)


@pytest.mark.parametrize(
    "missing", ["guard", "services", "lock", "authority", "disabled"]
)
def test_no_authority_no_new_pending_write(pending, missing):
    p = pending
    if missing == "guard":
        p.allow_pending = False
    elif missing == "services":
        p.machine.adaptive_exit_services = replace(
            p.machine.adaptive_exit_services, pending_buy=None
        )
    elif missing == "disabled":
        p.machine.live_enabled = False
    else:
        p.flags[missing] = False
    p.tick()
    assert not p.cancel_writes and not p.original_target_writes
    assert KEY not in leg(p) and leg(p)["status"] == "BUY_OPEN"


@pytest.mark.parametrize("mode", ["timeout", "reject"])
def test_ambiguous_or_rejected_child_never_retries_new_cancel(pending, mode):
    p = pending
    p.cancel_mode = mode
    p.tick()
    assert len(p.cancel_writes) == 1
    p.machine._state = p.machine._load_state()
    queries = len(p.buy_queries)
    for _ in range(3):
        result = p.tick()
    assert "spent_intent_requires_recovery" in result["adaptive_exit_loop_status"]
    assert len(p.cancel_writes) == 1 and len(p.buy_queries) == queries


def test_ack_is_not_terminal_and_deadline_stops_reads(pending):
    p = pending
    p.tick()
    p.tick()
    assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes
    p.clock[0] = leg(p)[KEY]["deadline_ms"]
    queries = len(p.buy_queries)
    assert "deadline_requires_recovery" in p.tick()["adaptive_exit_loop_status"]
    assert len(p.buy_queries) == queries and len(p.cancel_writes) == 1


@pytest.mark.parametrize("problem", ["price", "no_confirmation", "conflicting_price"])
def test_bad_terminal_source_never_projects_or_sells(pending, problem):
    p = pending
    p.tick()
    market(p, filled=4, remaining=0, confirmed=6)
    if problem == "price":
        p.buy_rows[0].pop("cntr_uv")
    elif problem == "no_confirmation":
        p.buy_rows[-1].pop("cnfm_qty")
    else:
        p.buy_rows.append({**p.buy_rows[0], "cntr_uv": "10005"})
    p.tick()
    assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes
    assert len(p.cancel_writes) == 1


@pytest.mark.parametrize("change", ["leg", "guard", "deadline", "state_replaced"])
def test_intervening_read_mutation_cannot_project(pending, monkeypatch, change):
    p = pending
    p.tick()
    market(p, filled=4, remaining=0, confirmed=6)
    factory = p.machine.gateway.adaptive_exit_adapter

    def make(**kwargs):
        adapter = factory(**kwargs)
        post = adapter.post

        def call(**request):
            result = post(**request)
            if request["api_id"] == "ka10075":
                if change == "leg":
                    leg(p)["entry_price"] += 5
                elif change == "guard":
                    p.allow_pending = False
                elif change == "state_replaced":
                    p.machine._state = deepcopy(p.machine._state)
                else:
                    p.clock[0] = leg(p)[KEY]["deadline_ms"]
            return result

        adapter.post = call
        return adapter

    monkeypatch.setattr(p.machine.gateway, "adaptive_exit_adapter", make)
    p.tick()
    assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes


@pytest.mark.parametrize("problem", [None, [], "bad", {"phase": "PROJECTED"}])
def test_malformed_journal_fails_closed(pending, problem):
    leg(pending)[KEY] = problem
    result = pending.tick()
    assert "invalid" in result["adaptive_exit_loop_status"]
    assert not pending.buy_queries and not pending.cancel_writes


@pytest.mark.parametrize(
    "tamper", ["journal_missing", "proof_hash", "filled_qty", "intent"]
)
def test_projected_source_proof_checked_before_any_target(pending, tamper):
    p = pending
    p.tick()
    market(p, filled=4, remaining=0, confirmed=6)
    p.tick()
    if tamper == "journal_missing":
        leg(p).pop(KEY)
    else:
        receipt = leg(p)["adaptive_sibling_full_buy_receipt"]
        if tamper == "proof_hash":
            receipt["registry_cancel_sha256"] = "0" * 64
        elif tamper == "filled_qty":
            receipt["filled_qty"] = 5
            leg(p)["buy_filled_qty"] = 5
        else:
            receipt["intent_id"] = "unrelated"
        receipt["canonical_sha256"] = canonical_sha256(receipt)
        leg(p)[KEY]["terminal_receipt"] = deepcopy(receipt)
        leg(p)[KEY]["canonical_sha256"] = canonical_sha256(leg(p)[KEY])
    p.tick()
    assert not p.original_target_writes and not p.wire.writes


def test_initial_read_cannot_accept_concurrent_leg_mutation(pending, monkeypatch):
    p = pending
    factory = p.machine.gateway.adaptive_exit_adapter

    def make(**kwargs):
        adapter = factory(**kwargs)
        post = adapter.post

        def call(**request):
            result = post(**request)
            if request["api_id"] == "ka10075":
                leg(p)["entry_price"] += 5
            return result

        adapter.post = call
        return adapter

    monkeypatch.setattr(p.machine.gateway, "adaptive_exit_adapter", make)
    p.tick()
    assert not p.cancel_writes and KEY not in leg(p)


def test_original_morning_deadline_is_not_regular_bar_floor(pending):
    p = pending
    p.machine._window = lambda _: type("Window", (), {"deadline": time(13, 0)})()
    leg(p)["route"] = "SOR"
    snapshot = type("Snapshot", (), {"filled_qty": 0})()
    method = SamsungMorningOneShareMachine._adaptive_pending_buy_cancel_reason
    assert (
        method(
            p.machine,
            datetime.fromisoformat(DATE + "T12:59:59+09:00"),
            leg(p),
            snapshot,
        )
        is None
    )
    result = method(
        p.machine, datetime.fromisoformat(DATE + "T13:00:00+09:00"), leg(p), snapshot
    )
    assert result["reason"] == "entry_validity_expired" and not p.bar_reads


@pytest.mark.parametrize("filled", [4, 10])
def test_fill_changes_before_cancel_reservation_keep_single_action(
    pending, monkeypatch, filled
):
    p = pending
    save = p.machine._save
    changed = False

    def persist():
        nonlocal changed
        save()
        if KEY in leg(p) and not changed:
            changed = True
            market(p, filled=filled, remaining=10 - filled)

    monkeypatch.setattr(p.machine, "_save", persist)
    first = p.tick()
    assert "exact_fresh_remaining_required" in first["adaptive_exit_loop_status"]
    assert not p.cancel_writes
    frozen = deepcopy(leg(p)[KEY])
    p.machine._state = p.machine._load_state()
    second = p.tick()
    assert leg(p)[KEY]["action_id"] == frozen["action_id"]
    assert leg(p)[KEY]["deadline_ms"] == frozen["deadline_ms"]
    if filled == 10:
        assert (
            second["adaptive_exit_loop_status"]
            == "pending_buy_terminal_original_target_pending"
        )
        assert not p.cancel_writes and leg(p)["position_qty"] == 10
        p.tick()
        assert p.original_target_writes == [{"price": 10095, "quantity": 10}]
    else:
        assert (
            len(p.cancel_writes) == 1
            and p.cancel_writes[0]["payload"]["cncl_qty"] == "6"
        )


@pytest.mark.parametrize("phase", ["INTENT_SAVED", "ACK_SAVED", "PROJECTED"])
@pytest.mark.parametrize("after_publish", [False, True])
def test_durable_crash_never_duplicates_cancel_or_sells_unproved_inventory(
    pending, monkeypatch, phase, after_publish
):
    p = pending
    if phase == "PROJECTED":
        p.tick()
        market(p, filled=4, remaining=0, confirmed=6)
    save = p.machine._save
    tripped = False

    def persist():
        nonlocal tripped
        if not tripped and leg(p).get(KEY, {}).get("phase") == phase:
            tripped = True
            if after_publish:
                save()
            raise OSError("isolated durable state failure")
        save()

    monkeypatch.setattr(p.machine, "_save", persist)
    with pytest.raises(OSError):
        p.tick()
    assert not p.original_target_writes
    p.machine._state = p.machine._load_state()
    p.tick()
    assert len(p.cancel_writes) <= 1
    if phase != "PROJECTED":
        assert len(p.cancel_writes) == 1
        market(p, filled=4, remaining=0, confirmed=6)
        p.tick()
    if not p.original_target_writes:
        p.tick()
    assert p.original_target_writes == [{"price": 10095, "quantity": 4}]
    assert len(p.cancel_writes) == 1


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_invalid_original_expiry_floor_cannot_cancel(pending, bad):
    pending.machine.policy.entry_valid_completed_bars = bad
    market(pending, filled=0, remaining=10)
    assert "validity_contract_invalid" in pending.tick()["adaptive_exit_loop_status"]
    assert not pending.cancel_writes


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, None])
def test_no_implicit_pending_confirmation_bound(loop, bad):  # noqa: F811
    with pytest.raises(ValueError, match="explicit_pending_buy"):
        EpisodePendingBuyServices(bad, lambda _: True)


def test_lost_registry_child_after_ack_is_not_a_new_cancel_slot(pending, monkeypatch):
    p = pending
    p.tick()
    original = p.machine.owner_registry.position_intents
    monkeypatch.setattr(p.machine.owner_registry, "intent_for_client", lambda **_: None)
    monkeypatch.setattr(
        p.machine.owner_registry,
        "position_intents",
        lambda **kw: [
            r for r in original(**kw) if r.get("original_order_no") != "0000009"
        ],
    )
    queries = len(p.buy_queries)
    result = p.tick()
    assert (
        "spent_intent_missing_requires_recovery" in result["adaptive_exit_loop_status"]
    )
    assert len(p.cancel_writes) == 1 and len(p.buy_queries) == queries


def test_nxt_zero_fill_projection_retains_original_fallback_handoff(pending):
    # Only the explicit unsupported branch; this is not an NXT integration receipt.
    p = pending
    handler = object.__new__(_PendingBuy)
    handler.authorized = lambda: True
    handler.binding = {"route": "NXT"}
    before = deepcopy(p.machine._state)
    result = handler.project(
        PricedCancelledBuySnapshot(OrderKey(DATE, "0000009"), filled_qty=0),
        OrderKey(DATE, "0000010"),
    )
    assert result == "pending_buy_zero_fill_original_nxt_fallback_handoff_required"
    assert p.machine._state == before and not p.cancel_writes


@pytest.mark.parametrize(
    "field,bad",
    [
        ("reason", None),
        ("observed_filled_qty", -1),
        ("action_id", "new-retry"),
        ("cancel_quantity", 0),
        ("binding", []),
    ],
)
def test_journal_semantic_tamper_cannot_recover_by_new_request(pending, field, bad):
    p = pending
    p.tick()
    journal = leg(p)[KEY]
    journal[field] = bad
    journal["canonical_sha256"] = canonical_sha256(journal)
    queries = len(p.buy_queries)
    assert "journal_binding_invalid" in p.tick()["adaptive_exit_loop_status"]
    assert len(p.buy_queries) == queries and len(p.cancel_writes) == 1
