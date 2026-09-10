"""Actual Samsung morning owner/registry handoff, entirely isolated fake I/O."""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.tests.test_machine_adaptive_exit_broker import DATE, detail, current, response
from src.tests.test_machine_adaptive_exit_decision import inputs
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.driver import DriverState, ExecutionBounds
from src.trading.order.adaptive_exit.episode_pending_buy import (
    EpisodePendingBuyServices,
    KEY as BUY_KEY,
)
from src.trading.order.adaptive_exit.episode_sor_fallback import (
    KEY,
    PLAN_KEY,
    validate,
    before_buy,
)
from src.trading.order.adaptive_exit.models import Clock, DecisionState
from src.trading.order.adaptive_exit.owner_loop import SESSION_KEY, OwnerLoopServices
from src.trading.order.adaptive_exit.reducer import ExitState, OrderKey
from src.trading.order.adaptive_exit.runtime import OwnerSession
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
)
from src.trading.order.regular_two_leg_machine import _fresh_state
from src.trading.samsung_morning_one_share.gateway import (
    OpenPriceSnapshot,
    SubmitResult,
)
from src.trading.samsung_morning_one_share.machine import (
    KST,
    SamsungMorningOneShareMachine,
    _morning_leg,
)
from src.trading.samsung_morning_one_share.policy import DEFAULT_POLICY


def at(value):
    return datetime.fromisoformat(DATE + "T" + value + "+09:00")


@pytest.fixture
def morning(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "isolated-morning-fallback")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(tmp_path / "registry.jsonl")
    )
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    m = SimpleNamespace(
        clock=int(at("08:10:00").timestamp() * 1000),
        flags={
            k: True
            for k in (
                "lock",
                "binding",
                "pending",
                "market",
                "confirmation",
                "liquidity",
                "broker",
            )
        },
        buys=[],
        sells=[],
        cancels=[],
        reads=[],
        guards=[],
        snapshots=[],
        requests=[],
    )
    position = f"episode:morning:005930:{DATE}"
    context = OwnerOrderContext("episode", position, position, "entry")
    registry.register_migrated_position(
        context=context,
        symbol="005930",
        quantity=10,
        average_price=10000,
        route="NXT",
        order_date=DATE,
        broker_order_no="0000001",
        evidence_sha256="a" * 64,
    )
    target = registry.reserve(
        context=replace(context, client_intent_id="target"),
        symbol="005930",
        side="SELL",
        quantity=10,
        route="NXT",
        order_date=DATE,
    )
    registry.transition(target, state="ORDER_BOUND", broker_order_no="0000002")
    policy, pos, snap, *_ = inputs()
    scope = "episode|morning|005930|NXT|NXT_PREMARKET"
    policy = replace(policy, scope_key=scope)
    policy = replace(
        policy,
        policy_hash=canonical_sha256(
            {k: v for k, v in asdict(policy).items() if k != "policy_hash"}
        ),
    )
    pos = replace(
        pos,
        owner_id="episode",
        scope_key=scope,
        episode_id=position,
        lot_id="base_plus_1tick",
        first_fill_at_ms=m.clock - 30000,
        cost_contract_hash="c" * 64,
    )
    session = OwnerSession(
        policy,
        pos,
        ExecutionBounds(
            3000, 2, 5000, "exit_with_fresh_guard", "retain_manager_and_alert"
        ),
        replace(context, client_intent_id="target"),
        target,
        "b" * 64,
        DriverState(
            ExitState(
                "episode",
                position,
                pos.lot_id,
                policy.policy_hash,
                pos.position_epoch,
                OrderKey(DATE, "0000002"),
                10,
            ),
            DecisionState(
                policy.policy_hash, pos.position_epoch, pos.first_fill_at_ms, 10
            ),
        ),
    )
    m.buy_rows = [
        detail(ord_no="0000009", cntr_qty="0", ord_remnq="10", dmst_stex_tp="NXT")
    ]
    m.buy_current = [
        current(ord_no="0000009", cntr_qty="0", oso_qty="10", stex_tp="2", sor_yn="N")
    ]

    def authorize(request):
        m.requests.append(request)
        return m.flags["pending"]

    def snapshot(s, c):
        m.snapshots.append(c.now_ms)
        return replace(
            snap,
            scope_key=scope,
            position_epoch=s.remaining_position.position_epoch,
            observed_at_ms=c.now_ms,
            quote_at_ms=c.now_ms,
            sequence=c.now_ms,
        )

    services = OwnerLoopServices(
        lock_held=lambda: m.flags["lock"],
        authorize_binding=lambda _: m.flags["binding"],
        owner_guard=lambda *a, **k: True,
        snapshot_loader=snapshot,
        clock_loader=lambda s, n: Clock(n, 0),
        pending_buy=EpisodePendingBuyServices(5000, authorize),
    )

    class Gateway:
        def adaptive_exit_adapter(self, *, registry, context, policy_hash, write_guard):
            return RegisteredSellAdapter(
                post=self.post,
                registry=registry,
                context=context,
                symbol="005930",
                routes=("NXT", "SOR"),
                policy_hash=policy_hash,
                maximum_quantity=10,
                require_write_authority=lambda: None,
                write_guard=write_guard,
                now_ms=lambda: m.clock,
            )

        def post(self, **request):
            payload = request["payload"]
            if request["api_id"] == "kt10003":
                m.cancels.append(request)
                return response(
                    {
                        "return_code": 0,
                        "ord_no": (
                            "0000010"
                            if payload["orig_ord_no"] == "0000009"
                            else "0000003"
                        ),
                        "base_orig_ord_no": payload["orig_ord_no"],
                        "cncl_qty": payload["cncl_qty"],
                        "dmst_stex_tp": payload["dmst_stex_tp"],
                    }
                )
            m.reads.append(request)
            is_buy = payload.get("sell_tp") == "2" or payload.get("trde_tp") == "2"
            field = (
                "acnt_ord_cntr_prps_dtl" if request["api_id"] == "kt00007" else "oso"
            )
            rows = (
                (m.buy_rows if field == "acnt_ord_cntr_prps_dtl" else m.buy_current)
                if is_buy
                else (
                    [detail(dmst_stex_tp="NXT")]
                    if field == "acnt_ord_cntr_prps_dtl"
                    else [current(stex_tp="2", sor_yn="N")]
                )
            )
            return response({"return_code": 0, field: rows})

        def opening_price(self, *, route, trade_date):
            m.guards.append("opening:" + route)
            return OpenPriceSnapshot(True, 10000, at("09:00:00").isoformat())

        def submit_limit_buy(self, **kwargs):
            m.buys.append(kwargs)
            if not m.flags["broker"]:
                return SubmitResult(False, return_code="AUTHORITY_BLOCKED")
            m.buy_rows.append(detail(ord_no="0000011", dmst_stex_tp="SOR"))
            m.buy_current.append(current(ord_no="0000011"))
            return SubmitResult(True, "0000011")

        def submit_limit_sell(self, **kwargs):
            m.sells.append(kwargs)
            return SubmitResult(True, "0000012")

    machine = SamsungMorningOneShareMachine(
        gateway=Gateway(),
        state_path=tmp_path / "owner.json",
        live_enabled=True,
        ownership_source=lambda _: "isolated-owner",
        adaptive_exit_services=services,
    )
    machine.owner_registry = registry
    machine._state = _fresh_state(at("08:10:00"), machine.schema)
    selected = _morning_leg(
        {
            "leg_id": "base_plus_1tick",
            "price_role": "aggressive_50pct",
            "entry_price": 10000,
        },
        "NXT",
    )
    selected.update(
        status="TARGET_OPEN",
        buy_order_no="0000001",
        buy_order_date=DATE,
        buy_filled_qty=10,
        fill_price=10000,
        position_qty=10,
        target_order_no="0000002",
        target_order_date=DATE,
        target_owner_registry_intent_id=target,
        target_quantity=10,
        target_price=10100,
    )
    selected[SESSION_KEY] = session.to_payload()
    other = _morning_leg(
        {"leg_id": "base", "price_role": "conservative_50pct", "entry_price": 9995},
        "NXT",
    )
    other.update(
        status="BUY_OPEN",
        buy_order_no="0000009",
        buy_order_date=DATE,
        buy_submit_attempt_count=1,
    )
    machine._state.update(
        legs=[selected, other],
        position_qty=10,
        status="TARGET_OPEN",
        attempt_consumed=True,
        signal_bar=at("08:00:00").isoformat(),
        owned_order_nos=["0000001", "0000002", "0000009"],
    )

    def reserve(**kwargs):
        ctx = machine._episode_owner_context(
            leg=kwargs["leg"], action=kwargs["action"], ordinal=kwargs["ordinal"]
        )
        return (
            registry.reserve(
                context=ctx,
                symbol="005930",
                side=kwargs["side"],
                quantity=kwargs["quantity"],
                route=kwargs["route"],
                order_date=DATE,
            ),
            ctx,
        )

    intent, _ = reserve(
        leg=other,
        action="NEW",
        ordinal="BUY:NXT:1",
        side="BUY",
        quantity=10,
        route="NXT",
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="0000009")
    other["buy_owner_registry_intent_id"] = intent
    monkeypatch.setattr(machine, "_reserve_episode_intent", reserve)

    def guard(name):
        def check(*a, **k):
            m.guards.append(name)
            return m.flags[name]

        return check

    monkeypatch.setattr(machine, "_market_weakness_allows_new_buys", guard("market"))
    monkeypatch.setattr(machine, "_confirm_planned_route", guard("confirmation"))
    monkeypatch.setattr(
        machine, "_entry_liquidity_allows_planned_buys", guard("liquidity")
    )
    machine._sync_aggregate()
    machine._save()
    m.machine = machine
    m.tick = lambda: machine.run_once(datetime.fromtimestamp(m.clock / 1000, KST))
    return m


def leg(m):
    return m.machine._state["legs"][1]


def prepare(m):
    result = m.tick()
    assert (
        result.get("adaptive_exit_loop_status")
        == "pending_buy_cancel_confirmation_wait"
    ), result
    m.buy_rows[0]["ord_remnq"] = "0"
    m.buy_rows.append(
        detail(
            ord_no="0000010",
            ori_ord="0000009",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty="10",
            cnfm_tm="08:10:00",
            dmst_stex_tp="NXT",
        )
    )
    m.buy_current = []
    m.clock += 1
    assert (
        m.tick()["adaptive_exit_loop_status"]
        == "pending_buy_terminal_sor_fallback_prepared"
    )


def test_nxt_zero_fill_preserved_until_original_sor_window_and_target(morning):
    m = morning
    prepare(m)
    assert leg(m)["status"] == "PLANNED" and leg(m)["route"] == "SOR"
    assert leg(m)[KEY]["source_leg"]["route"] == "NXT"
    assert leg(m)[KEY]["source_leg"]["buy_filled_qty"] == 0
    original = deepcopy(leg(m)[KEY])
    m.machine._state = m.machine._load_state()
    m.clock += 1
    m.tick()
    assert m.snapshots and not m.buys and not m.guards
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    assert m.buys == [
        {
            "route": "SOR",
            "price": DEFAULT_POLICY.entry_legs(10000, DEFAULT_POLICY.sor.drawdown_pct)[
                1
            ]["entry_price"],
            "quantity": 10,
        }
    ]
    assert set(m.guards) == {"market", "opening:SOR", "confirmation", "liquidity"}
    assert leg(m)["buy_submit_attempt_count"] == 2 and leg(m)["status"] == "BUY_OPEN"
    assert leg(m)[KEY] == original and len(m.snapshots) >= 2
    # Newly full SOR BUY is a different root, never a relabeled NXT fill.
    m.buy_rows[-1].update(cntr_qty="10", ord_remnq="0", cntr_uv="9920")
    m.buy_current = []
    m.clock += 1
    m.tick()
    assert leg(m)["status"] == "POSITION_OPEN" and leg(m)["buy_order_no"] == "0000011"
    m.clock += 1
    m.tick()
    assert m.sells == [
        {"route": "SOR", "price": DEFAULT_POLICY.target_price(9920), "quantity": 10}
    ]
    assert len(m.buys) == 1 and leg(m)[KEY] == original


@pytest.mark.parametrize(
    "guard", ["market", "confirmation", "liquidity", "pending", "lock", "binding"]
)
def test_fallback_never_bypasses_existing_or_independent_guard(morning, guard):
    m = morning
    prepare(m)
    m.flags[guard] = False
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    assert not m.buys and PLAN_KEY not in leg(m)


def test_expired_sor_window_is_no_fill_without_late_compensation_buy(morning):
    m = morning
    prepare(m)
    m.clock = int(at("09:30:00").timestamp() * 1000)
    m.tick()
    assert leg(m)["status"] == "NO_FILL" and not m.buys
    assert KEY in leg(m)


def test_broker_authority_blocked_slot_is_not_retried(morning):
    m = morning
    prepare(m)
    m.flags["broker"] = False
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    assert len(m.buys) == 1
    m.flags["broker"] = True
    m.machine._state = m.machine._load_state()
    result = m.tick()
    assert "spent_submit_requires_recovery" in result["adaptive_exit_loop_status"]
    assert len(m.buys) == 1


def reseal(handoff):
    handoff["source_leg_sha256"] = canonical_sha256(handoff["source_leg"])
    handoff["canonical_sha256"] = canonical_sha256(handoff)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_journal",
        "missing_receipt",
        "missing_child",
        "original_fill",
        "original_route",
        "original_date",
        "future",
        "naive",
        "offset",
        "successor",
        "current_route",
        "quantity",
        "policy",
        "corrupt_hash",
    ],
)
def test_rehashed_handoff_still_requires_original_proof_and_current_contract(
    morning, fault
):
    m = morning
    prepare(m)
    handoff = leg(m)[KEY]
    source = handoff["source_leg"]
    if fault == "missing_journal":
        source.pop(BUY_KEY)
    elif fault == "missing_receipt":
        source.pop("adaptive_sibling_full_buy_receipt")
    elif fault == "missing_child":
        source["adaptive_sibling_full_buy_receipt"]["cancel_order"] = None
    elif fault == "original_fill":
        source["buy_filled_qty"] = 1
    elif fault == "original_route":
        source["route"] = "SOR"
    elif fault == "original_date":
        source["buy_order_date"] = "2026-09-08"
    elif fault == "future":
        handoff["prepared_at"] = at("09:01:00").isoformat()
    elif fault == "naive":
        handoff["prepared_at"] = DATE + "T08:10:00"
    elif fault == "offset":
        handoff["prepared_at"] = DATE + "T00:10:00+00:00"
    elif fault == "successor":
        handoff["successor_attempt"] = 3
    elif fault == "current_route":
        leg(m)["route"] = "NXT"
    elif fault == "quantity":
        leg(m)["quantity"] = 20
    elif fault == "policy":
        m.machine.policy = replace(DEFAULT_POLICY, target_ticks=3)
    reseal(handoff)
    if fault == "corrupt_hash":
        handoff["canonical_sha256"] = "0" * 64
    m.clock = int(at("09:00:00").timestamp() * 1000)
    result = m.tick()
    assert result["status"] == "BLOCKED" or "adaptive_" in result.get(
        "adaptive_exit_loop_status", ""
    ), result
    assert not m.buys and not m.sells


@pytest.mark.parametrize("phase", ["before_reserve", "after_reserve", "after_ack"])
@pytest.mark.parametrize("published", [False, True])
def test_durable_failure_never_reissues_reserved_or_acknowledged_buy(
    morning, monkeypatch, phase, published
):
    m = morning
    prepare(m)
    save = m.machine._save
    fired = False

    def persist():
        nonlocal fired
        candidate = leg(m)
        matches = {
            "before_reserve": candidate["status"] == "BUY_SUBMITTING"
            and candidate["buy_submit_attempt_count"] == 1,
            "after_reserve": candidate["status"] == "BUY_SUBMITTING"
            and candidate["buy_submit_attempt_count"] == 2,
            "after_ack": candidate["status"] == "BUY_OPEN"
            and candidate.get("buy_order_no") == "0000011",
        }
        if not fired and matches[phase]:
            fired = True
            if published:
                save()
            raise OSError("isolated_durable_failure")
        save()

    monkeypatch.setattr(m.machine, "_save", persist)
    m.clock = int(at("09:00:00").timestamp() * 1000)
    with pytest.raises(OSError, match="isolated_durable_failure"):
        m.tick()
    assert fired
    before = len(m.buys)
    assert before == int(phase == "after_ack")
    monkeypatch.setattr(m.machine, "_save", save)
    m.machine._state = m.machine._load_state()
    m.tick()
    # Before any durable reservation/write, a non-published save may retry the
    # untouched original entry. Every persisted intent or ACK is single-use.
    expected = 1 if phase == "before_reserve" and not published else before
    assert len(m.buys) == expected
    m.tick()
    assert len(m.buys) == expected


@pytest.mark.parametrize("stage", ["confirmation", "reservation"])
@pytest.mark.parametrize(
    "loss", ["lock", "binding", "pending", "blocked", "replacement"]
)
def test_lost_authority_or_replaced_leg_blocks_next_wire(
    morning, monkeypatch, stage, loss
):
    m = morning
    prepare(m)

    def lose():
        if loss == "blocked":
            m.machine._state["status"] = "BLOCKED"
            m.machine._state["blocked_reason"] = "isolated_existing_guard"
        elif loss == "replacement":
            m.machine._state = deepcopy(m.machine._state)
        else:
            m.flags[loss] = False

    if stage == "confirmation":

        def confirm(*args, **kwargs):
            lose()
            return True

        monkeypatch.setattr(m.machine, "_confirm_planned_route", confirm)
    else:
        reserve = m.machine._reserve_episode_intent

        def reserved(**kwargs):
            result = reserve(**kwargs)
            lose()
            return result

        monkeypatch.setattr(m.machine, "_reserve_episode_intent", reserved)
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    assert not m.buys and not m.sells
    if loss == "blocked":
        assert m.machine._state["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "other"),
        ("route", "NXT"),
        ("quantity", 10.0),
        ("price", 0),
        ("at", DATE + "T08:59:59+09:00"),
    ],
)
def test_successor_plan_semantics_cannot_be_bypassed_by_rehashing(
    morning, field, value
):
    m = morning
    prepare(m)
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    assert len(m.buys) == 1
    plan = leg(m)[PLAN_KEY]
    plan[field] = value
    plan["canonical_sha256"] = canonical_sha256(plan)
    with pytest.raises(ValueError, match="adaptive_sor_submit_"):
        validate(m.machine, at("09:00:00"), leg(m))
    m.tick()
    assert len(m.buys) == 1 and not m.sells


def test_selected_nxt_lot_cannot_be_reinterpreted_as_sor_session(morning):
    m = morning
    m.machine._state["legs"][0]["route"] = "SOR"
    result = m.tick()
    assert "original_lot_binding_mismatch" in result["adaptive_exit_loop_status"]
    assert not m.cancels and not m.buys


def test_fresh_morning_leg_is_identical_after_durable_readback(morning):
    assert morning.machine._load_state()["legs"][1] == leg(morning)


@pytest.mark.parametrize("mutation", ["state", "signal", "selected"])
def test_authorization_callback_cannot_change_the_approved_owner_snapshot(
    morning, mutation
):
    m = morning
    prepare(m)
    services = m.machine.adaptive_exit_services

    def authorize(request):
        if request["action"] == "RESUME_SOR_FALLBACK":
            if mutation == "state":
                m.machine._state = dict(m.machine._state)
            elif mutation == "signal":
                m.machine._state["signal_features"] = {"changed": True}
            else:
                m.machine._state["legs"][0]["unexpected_mutation"] = True
        return True

    m.machine.adaptive_exit_services = replace(
        services, pending_buy=EpisodePendingBuyServices(5000, authorize)
    )
    m.clock = int(at("09:00:00").timestamp() * 1000)
    result = m.tick()
    assert (
        result["adaptive_exit_loop_status"]
        == "adaptive_sor_original_owner_authority_required"
    )
    assert not m.buys and not m.sells


def test_reservation_disappearance_has_explicit_recovery_not_attribute_error(
    morning, monkeypatch
):
    m = morning
    prepare(m)
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    leg(m)["status"] = "BUY_SUBMITTING"
    m.machine._sync_aggregate()
    m.machine._save()
    registry = m.machine.owner_registry
    context = m.machine._episode_owner_context(
        leg=leg(m), action="NEW", ordinal="BUY:SOR:2"
    )
    lookup = registry.intent_for_client
    count = 0

    def changed(*, context: OwnerOrderContext):
        nonlocal count
        if context.client_intent_id == expected_id:
            count += 1
            if count == 2:
                return None
        return lookup(context=context)

    expected_id = context.client_intent_id
    monkeypatch.setattr(registry, "intent_for_client", changed)
    with pytest.raises(ValueError, match="adaptive_sor_reserved_submit_required"):
        before_buy(m.machine, at("09:00:00"), leg(m), reserved=True)
    assert count == 2 and len(m.buys) == 1


def test_late_nxt_zero_fill_keeps_original_sor_consumer(morning):
    m = morning
    from src.trading.order.adaptive_exit.episode_buy_recovery import (
        KEY as RECOVERY_KEY,
        TerminalRecoveryServices,
    )

    services = m.machine.adaptive_exit_services
    m.machine.adaptive_exit_services = replace(
        services,
        pending_buy=replace(
            services.pending_buy,
            terminal_recovery=TerminalRecoveryServices(2, 1000, 10000, lambda _: True),
        ),
    )
    m.tick()
    journal = deepcopy(leg(m)[BUY_KEY])
    m.buy_rows[0]["ord_remnq"] = "0"
    m.buy_rows.append(
        detail(
            ord_no="0000010",
            ori_ord="0000009",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty="10",
            cnfm_tm="08:10:05",
            dmst_stex_tp="NXT",
        )
    )
    m.buy_current = []
    m.clock = journal["deadline_ms"] + 1
    assert (
        m.tick()["adaptive_exit_loop_status"]
        == "pending_buy_terminal_sor_fallback_prepared"
    )
    source = leg(m)[KEY]["source_leg"]
    assert source[BUY_KEY]["deadline_ms"] == journal["deadline_ms"]
    assert len(source[BUY_KEY][RECOVERY_KEY]["observation_starts_ms"]) == 1
    assert source["route"] == "NXT" and source["buy_filled_qty"] == 0
    assert leg(m)["route"] == "SOR" and not m.buys
    assert len(m.cancels) == 1
    m.machine._state = m.machine._load_state()
    m.clock = int(at("09:00:00").timestamp() * 1000)
    m.tick()
    assert (
        len(m.buys) == 1 and m.buys[0]["route"] == "SOR" and m.buys[0]["quantity"] == 10
    )
    # The other selected target keeps its independent exit owner at 09:00.
    # Its SELL cancellation must not be counted as a retry of pending BUY 9.
    assert len([r for r in m.cancels if r["payload"]["orig_ord_no"] == "0000009"]) == 1
