"""Original owner loops with temporary journals and a fake Kiwoom transport."""

from copy import deepcopy
from datetime import datetime
import hashlib
import json

import pytest

from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    TARGET,
    detail,
    current,
)
from src.tests.test_machine_adaptive_exit_market_source import projection
from src.trading.config.machine_profit_stagnation_policy import (
    FAMILY,
    HASH_ENV,
    PATH_ENV,
    load_policy,
)
from src.trading.order import profit_stagnation_owners as bridge
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.profit_stagnation_exit import KEY
from src.trading.order.owner_custody_registry import OrderOwnerRegistry
from src.trading.market.profit_stagnation_quote import executable_quote
from src.trading.widget_auto_trade.engine import KST
from types import SimpleNamespace

pytest_plugins = ["src.tests.test_machine_adaptive_exit_owner_loop"]


def policy():
    # Test geometry, NOT deployment fee/risk approval.
    return dict(
        family=FAMILY,
        enabled=True,
        valid_from=DATE + "T00:00:00+09:00",
        valid_until="2026-09-11T00:00:00+09:00",
        owners=["episode", "widget_auto_trade"],
        round_trip_cost_pct=0.23,
        slippage_bps=5,
        cost_source_sha256="c" * 64,
        min_sec=12,
        max_profit_move=0.15,
        max_peak_improve=0.10,
        sell_ttl_sec=10,
        max_observation_gap_sec=12,
    )


@pytest.fixture
def running(loop, tmp_path, monkeypatch):
    raw = json.dumps(policy()).encode()
    path = tmp_path / "profit-policy.json"
    path.write_bytes(raw)
    monkeypatch.setenv(PATH_ENV, str(path))
    monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())
    m = loop.machine
    m.adaptive_exit_services = None
    m.profit_exit_lock_held = lambda: loop.flags["lock"]
    monkeypatch.setattr(
        bridge, "guard", lambda *a, **k: loop.flags["guard"] and loop.flags["lock"]
    )
    loop.flags["bid"] = 10040

    def quote(**kwargs):
        if not loop.flags["quote"]:
            raise ValueError("source_gap")
        return dict(
            executable_bid=loop.flags["bid"],
            available_quantity=100,
            quote_at=loop.clock[0] / 1000,
            quote_id=str(loop.clock[0]),
            source_epoch="SOR:1",
        )

    monkeypatch.setattr(bridge, "executable_quote", quote)

    def adapter(**kwargs):
        kwargs.pop("code", None)
        return RegisteredSellAdapter(
            post=loop.wire,
            symbol="005930",
            routes=("SOR",),
            maximum_quantity=10,
            require_write_authority=lambda: None,
            now_ms=lambda: loop.clock[0],
            **kwargs,
        )

    m.gateway.adaptive_exit_adapter = adapter
    if loop.owner == "episode":
        m._state["legs"][0].pop("adaptive_exit_session")
        m._state["signal_features"]["signal_decision_at"] = DATE + "T12:59:00+09:00"
        monkeypatch.setattr(m, "_submit_planned_buys", lambda *a: None)

        def record():
            return m._state["legs"][0][KEY]

        m.run_once(datetime.fromtimestamp(loop.clock[0] / 1000, KST))
    else:
        state = m._state["symbols"]["005930"]
        state.pop("adaptive_exit_sessions")
        buy, target = state["orders"]
        buy.update(
            requested_qty=10,
            fill_price=10000,
            signal_id="signal",
            intent_created_at=DATE + "T12:59:00+09:00",
        )
        target.update(status="SUBMITTED", remaining_qty=10)
        m.specs = (
            SimpleNamespace(
                code="005930", snapshot_path="unused", execution_policy_id=""
            ),
        )
        m.snapshot_loader = lambda _: None
        monkeypatch.setattr(m, "_refresh_same_day_policy_catalog", lambda *a: None)
        loop.flags["baseline_calls"] = 0

        def baseline(*args):
            assert KEY not in state
            loop.flags["baseline_calls"] += 1

        monkeypatch.setattr(m, "_reconcile", baseline)
        for method in (
            "_cancel_market_weakness_pending_buys",
            "_recover_definitive_rejected_entry_episode",
            "_close_completed_take_profit_episode",
            "_maybe_submit_take_profit",
            "_notify_pending_buy_actions",
        ):
            monkeypatch.setattr(m, method, lambda *a, **k: None)
        bridge.widget_symbol(
            m, state, datetime.fromtimestamp(loop.clock[0] / 1000, KST)
        )

        def record():
            current_state = m._state["symbols"]["005930"]
            return next(
                iter(
                    (
                        current_state.get(KEY)
                        or current_state.get(bridge.OBSERVATION_KEY)
                        or current_state["profit_stagnation_history"][-1]
                    ).values()
                )
            )

    loop.record = record
    return loop


def tick(run, seconds=1):
    run.clock[0] += seconds * 1000
    return run.machine.run_once(datetime.fromtimestamp(run.clock[0] / 1000, KST))


def canceled(run, filled=0):
    run.wire.detailed = [
        detail(cntr_qty=str(filled), ord_remnq="0"),
        detail(
            ord_no="0000003",
            ori_ord=TARGET.order_no,
            ord_qty="10",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty=str(10 - filled),
            cnfm_tm="13:00:13",
        ),
    ]
    run.wire.current = []


def ready(run, filled=0):
    tick(run, 6)
    tick(run, 6)
    assert run.record()["phase"] == "CANCEL"
    tick(run)
    assert len(run.wire.writes) == 1
    tick(run)
    assert run.record()["phase"] == "CANCEL"  # ACK is not terminal.
    canceled(run, filled)
    tick(run)
    assert run.record()["phase"] == "READY"


def submitted(run, *, filled=0, restore=False):
    ready(run, filled)
    if restore:
        run.flags["quote"] = False
    run.wire.write_body = dict(return_code=0, ord_no="0000004", dmst_stex_tp="SOR")
    tick(run)
    assert run.record()["phase"] == "SUBMITTING"
    assert len(run.wire.writes) == 2
    assert run.wire.writes[-1]["payload"]["ord_qty"] == str(10 - filled)
    assert run.wire.writes[-1]["payload"]["ord_uv"] == (
        "10100" if restore or filled else "10040"
    )
    run.wire.detailed.append(
        detail(ord_no="0000004", ord_qty=str(10 - filled), ord_remnq=str(10 - filled))
    )
    run.wire.current = [
        current(ord_no="0000004", ord_qty=str(10 - filled), oso_qty=str(10 - filled))
    ]
    tick(run)


def test_actual_owner_cancel_positive_limit_restart_full_terminal(running):
    submitted(running)
    assert running.record()["phase"] == "EXIT"
    # Reload the actual owner journal, no separate service factory.
    running.machine._state = running.machine._load_state()
    running.wire.detailed[-1].update(cntr_qty="10", ord_remnq="0")
    running.wire.current = []
    tick(running)
    if running.owner == "episode":
        leg = running.machine._state["legs"][0]
        assert leg["position_qty"] == 0 and leg["profit_stagnation_filled_qty"] == 10
        assert leg["target_price"] == 10100 and leg["target_quantity"] == 10
        from src.trading.samsung_morning_one_share.reentry import (
            _profit_terminal_complete,
        )

        assert _profit_terminal_complete(leg)
        invalid = deepcopy(leg)
        invalid[KEY]["phase"] = "SUBMITTING"
        assert not _profit_terminal_complete(invalid)
    else:
        assert (
            running.machine._open_qty(running.machine._state["symbols"]["005930"]) == 0
        )
    assert len(running.wire.writes) == 2


def test_episode_projects_exact_original_target_fill_facts(running, monkeypatch):
    if running.owner != "episode":
        return
    monkeypatch.setattr(
        bridge,
        "_original_target_fill_facts",
        lambda registry, order, filled, **identity: (
            10100,
            DATE + "T13:00:01+09:00",
        ),
    )
    running.wire.detailed[0].update(cntr_qty="10", ord_remnq="0")
    running.wire.current = []
    tick(running)
    leg = running.machine._state["legs"][0]
    assert leg["target_fill_price"] == 10100
    assert leg["target_filled_at"].startswith(DATE + "T")


def test_original_target_fill_facts_requires_exact_registry_amount_and_date():
    row = {
        "side": "SELL",
        "action": "NEW",
        "broker_order_no": TARGET.order_no,
        "order_date": DATE,
        "owner_type": "episode",
        "owner_id": "episode:test:005930:" + DATE,
        "position_id": "episode:test:005930:" + DATE,
        "symbol": "005930",
        "quantity": 10,
        "filled_qty": 10,
        "fill_amount": 101000,
        "fill_observed_at_kst": DATE + "T13:00:01+09:00",
    }
    registry = SimpleNamespace(order_owner=lambda **kwargs: row)
    assert bridge._original_target_fill_facts(
        registry,
        TARGET,
        10,
        owner_id="episode:test:005930:" + DATE,
        symbol="005930",
    ) == (
        10100,
        DATE + "T13:00:01+09:00",
    )
    assert bridge._original_target_fill_facts(
        registry,
        TARGET,
        9,
        owner_id="episode:test:005930:" + DATE,
        symbol="005930",
    ) is None
    row["fill_amount"] = 101001
    assert bridge._original_target_fill_facts(
        registry,
        TARGET,
        10,
        owner_id="episode:test:005930:" + DATE,
        symbol="005930",
    ) is None
    row["fill_amount"] = 101000
    row["owner_id"] = "episode:other:005930:" + DATE
    assert bridge._original_target_fill_facts(
        registry,
        TARGET,
        10,
        owner_id="episode:test:005930:" + DATE,
        symbol="005930",
    ) is None


def test_registry_projection_retains_fill_time_after_terminal_transition():
    events = [
        {
            "intent_id": "target",
            "event": "FILL_RECORDED",
            "observed_at_kst": DATE + "T13:00:01+09:00",
            "filled_qty": 10,
        },
        {
            "intent_id": "target",
            "event": "ORDER_TERMINAL",
            "observed_at_kst": DATE + "T13:00:02+09:00",
            "state": "ORDER_TERMINAL",
        },
    ]
    assert OrderOwnerRegistry._state(events)["target"]["fill_observed_at_kst"] == (
        DATE + "T13:00:01+09:00"
    )


def test_widget_observation_does_not_claim_existing_entry_path(running):
    if running.owner != "widget":
        return
    state = running.machine._state["symbols"]["005930"]
    assert KEY not in state
    assert (
        bridge.widget_symbol(
            running.machine, state, datetime.fromtimestamp(running.clock[0] / 1000, KST)
        )
        is False
    )
    assert not running.wire.writes


def test_widget_original_scale_in_reached_while_only_observing(running, monkeypatch):
    if running.owner != "widget":
        return
    m = running.machine
    spec = m.specs[0]
    spec.contract = SimpleNamespace(
        session_context=lambda _: SimpleNamespace(name="KRX_REGULAR")
    )
    monkeypatch.setattr(m, "_try_adaptive_enrollment", lambda *a: False)
    monkeypatch.setattr(m, "_maybe_request_policy_force_exit", lambda *a: None)
    monkeypatch.setattr(m, "_exit_signal", lambda *a: None)
    monkeypatch.setattr(m, "_entry_signal", lambda *a: None)
    monkeypatch.setattr(m, "_execution_policy", lambda *a, **k: None)
    monkeypatch.setattr(m, "_maybe_submit_exit", lambda *a: None)
    calls = []
    monkeypatch.setattr(
        m, "_maybe_submit_scale_in", lambda *a: calls.append("scale_in")
    )
    m.process_payload(
        spec,
        {"current_price": 10040},
        datetime.fromtimestamp(running.clock[0] / 1000, KST),
    )
    assert calls == ["scale_in"]
    assert running.flags["baseline_calls"] == 1
    assert KEY not in m._state["symbols"]["005930"]
    assert not running.wire.writes


def test_widget_pending_buy_clears_observation_without_cancel(running):
    if running.owner != "widget":
        return
    state = running.machine._state["symbols"]["005930"]
    pending = deepcopy(state["orders"][0])
    pending.update(status="SUBMITTED", filled_qty=0, order_no="0000006")
    state["orders"].append(pending)
    tick(running, 6)
    assert KEY not in state and bridge.OBSERVATION_KEY not in state
    assert not running.wire.writes


def unsent_widget_buy(buy):
    """Durable EntryNotSent receipt after registry reservation release."""
    row = deepcopy(buy)
    row.update(
        status="NOT_SENT", order_no="", broker_accepted=False,
        actual_order_submitted=False, filled_qty=0, fill_price=None,
        return_code="ENTRY_ADVERSE_NOT_SENT",
        owner_registry_bind_confirmed=False,
    )
    return row


def test_widget_unsent_attempt_preserves_observation_and_exit(running):
    if running.owner != "widget":
        return
    state = running.machine._state["symbols"]["005930"]
    unsent = unsent_widget_buy(state["orders"][0])
    # An unexecuted older attempt must not determine enrollment time/basis.
    unsent["intent_created_at"] = "2026-09-09T12:00:00+09:00"
    before = deepcopy(unsent)
    state["orders"].insert(0, unsent)
    submitted(running)
    assert state["orders"][0] == before
    assert running.record()["entry_price"] == 10000
    assert running.record()["quantity"] == 10


@pytest.mark.parametrize("change", [
    {"status": "AMBIGUOUS"}, {"status": "SUBMITTED"},
    {"status": "FAILED"}, {"broker_accepted": True},
    {"actual_order_submitted": True}, {"actual_order_submitted": None},
    {"filled_qty": 1}, {"filled_qty": False}, {"filled_qty": "0"},
    {"fill_price": 10000}, {"order_no": "0000006"},
    {"return_code": "0"}, {"owner_registry_bind_confirmed": True},
    {"owner_registry_reconciliation_required": True},
    {"ambiguous": True}, {"fill_amount": 10000},
    {"fill_amount_krw": 10000}, {"owner_registry_error": "failed_release"},
])
def test_widget_unproven_unsent_remains_blocked(running, change):
    if running.owner != "widget":
        return
    state = running.machine._state["symbols"]["005930"]
    unsent = unsent_widget_buy(state["orders"][0])
    unsent.update(change)
    state["orders"].append(unsent)
    tick(running, 6)
    tick(running, 6)
    assert KEY not in state and bridge.OBSERVATION_KEY not in state
    assert not running.wire.writes


def test_unsent_receipt_requires_explicit_fill_fields():
    order = unsent_widget_buy({"side": "BUY"})
    assert bridge.widget_buy_proven_not_sent(order)
    for field in ("fill_price", "filled_qty", "broker_accepted",
                  "actual_order_submitted", "order_no", "return_code"):
        missing = deepcopy(order)
        missing.pop(field)
        assert not bridge.widget_buy_proven_not_sent(missing), field


def test_widget_custody_buy_selection_preserves_identity_and_audit():
    filled = dict(side="BUY", status="FILLED", signal_id="entry")
    child = dict(side="BUY", status="SUBMITTED", parent_entry_signal_id="entry")
    other = dict(side="BUY", status="FILLED", signal_id="other")
    unsent = unsent_widget_buy(filled)
    state = dict(entry_signal_id="entry", orders=[unsent, filled, child, other])
    before = deepcopy(state)
    assert bridge.widget_position_buys(state) == [filled, child]
    assert state == before
    state.pop("entry_signal_id")
    assert bridge.widget_position_buys(state) == []


def test_widget_basis_change_restarts_only_observation(running):
    if running.owner != "widget":
        return
    tick(running, 6)
    state = running.machine._state["symbols"]["005930"]
    old_start = running.record()["decision"]["started"]
    state["orders"][0]["fill_price"] = 10001
    tick(running, 6)
    assert running.record()["decision"]["started"] > old_start
    assert KEY not in state and not running.wire.writes


def test_policy_unpinned_clears_selected_diagnostic(monkeypatch):
    monkeypatch.delenv(PATH_ENV, raising=False)
    monkeypatch.delenv(HASH_ENV, raising=False)
    diagnostic = {"profit_exit_policy_status": "selected"}
    assert bridge.policy_for(None, "widget_auto_trade", "", diagnostic) is None
    assert diagnostic["profit_exit_policy_status"] == "off_no_policy_pin"


@pytest.mark.parametrize("filled", [0, 3])
def test_source_loss_or_partial_fill_restores_exact_original_target(running, filled):
    submitted(running, filled=filled, restore=True)
    assert running.record()["phase"] == "TARGET"
    tick(running, 6)
    assert len(running.wire.writes) == 2
    if running.owner == "widget":
        state = running.machine._state["symbols"]["005930"]
        assert KEY not in state
        assert state["orders"][-1]["profit_stagnation_disabled"] is True


def test_ambiguous_submit_never_retries_or_restores_blindly(running):
    ready(running)
    running.wire.crash = True
    tick(running)
    for _ in range(3):
        tick(running)
    assert running.record()["phase"] == "SUBMITTING"
    assert len(running.wire.writes) == 2


def test_definite_rejection_restores_not_another_lower_exit(running):
    ready(running)
    running.wire.write_body = dict(return_code=1)
    tick(running)
    assert running.record()["phase"] == "READY"
    running.wire.write_body = dict(return_code=0, ord_no="0000004", dmst_stex_tp="SOR")
    tick(running)
    assert running.wire.writes[-1]["payload"]["ord_uv"] == "10100"
    assert len(running.wire.writes) == 3


def test_lock_loss_no_queries_or_journal_writes(running):
    before = running.path.read_bytes(), len(running.wire.calls)
    running.flags["lock"] = False
    tick(running, 6)
    assert len(running.wire.calls) == before[1]
    assert running.path.read_bytes() == before[0]


def test_partial_supplement_ttl_restores_only_remaining_at_original_target(running):
    submitted(running)
    running.wire.detailed[-1].update(cntr_qty="3", ord_remnq="7")
    running.wire.current[-1].update(cntr_qty="3", oso_qty="7")
    tick(running, 10)
    assert running.record()["phase"] == "EXIT_CANCEL"
    running.wire.write_body = dict(
        return_code=0,
        ord_no="0000005",
        base_orig_ord_no="0000004",
        cncl_qty="7",
        dmst_stex_tp="SOR",
    )
    tick(running)
    assert running.wire.writes[-1]["payload"]["cncl_qty"] == "7"
    running.wire.detailed[-1]["ord_remnq"] = "0"
    running.wire.detailed.append(
        detail(
            ord_no="0000005",
            ori_ord="0000004",
            ord_qty="7",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty="7",
            cnfm_tm="13:00:28",
        )
    )
    running.wire.current = []
    tick(running)
    assert running.record()["phase"] == "READY"
    running.wire.write_body = dict(return_code=0, ord_no="0000006", dmst_stex_tp="SOR")
    tick(running)
    assert running.wire.writes[-1]["payload"]["ord_uv"] == "10100"
    assert running.wire.writes[-1]["payload"]["ord_qty"] == "7"


def test_policy_revocation_before_cancel_preserves_original(running, monkeypatch):
    tick(running, 6)
    tick(running, 6)
    assert running.record()["phase"] == "CANCEL"
    monkeypatch.delenv(HASH_ENV)
    tick(running)
    assert running.record()["phase"] == "TARGET" and not running.wire.writes
    if running.owner == "widget":
        assert KEY not in running.machine._state["symbols"]["005930"]


@pytest.mark.parametrize("changed", ["quote_missing", "target_reached", "net_lost"])
def test_candidate_is_revalidated_before_cancel_not_only_before_sell(running, changed):
    tick(running, 6)
    tick(running, 6)
    if changed == "quote_missing":
        running.flags["quote"] = False
    else:
        running.flags["bid"] = 10100 if changed == "target_reached" else 10000
    tick(running)
    assert running.record()["phase"] == "TARGET"
    assert not running.wire.writes
    if running.owner == "widget":
        assert KEY not in running.machine._state["symbols"]["005930"]


def test_source_gap_after_cancel_revalidated_before_transport(running, monkeypatch):
    ready(running)
    registry = running.machine.owner_registry
    reserve = registry.reserve

    def delayed_reserve(**kwargs):
        result = reserve(**kwargs)
        if kwargs.get("action") == "NEW":
            running.flags["quote"] = False
        return result

    monkeypatch.setattr(registry, "reserve", delayed_reserve)
    tick(running)
    assert len(running.wire.writes) == 1
    assert running.record()["phase"] == "READY"
    tick(running)
    assert running.wire.writes[-1]["payload"]["ord_uv"] == "10100"


def test_frozen_policy_corruption_never_cancels(running):
    running.record()["policy"]["round_trip_cost_pct"] = 0.01
    tick(running, 6)
    assert not running.wire.writes
    assert running.machine._state["profit_exit_last_error"] == "ValueError"


def test_midnight_preserves_unresolved_manager_without_guessing_order_date(running):
    ready(running)
    original = deepcopy(running.record()["root"])
    tick(running, 86400)
    assert running.record()["root"] == original
    assert running.record()["phase"] == "READY"
    assert len(running.wire.writes) == 1


def test_initial_journal_failure_requires_reload_before_any_order(running, monkeypatch):
    # Any persist failure after enrollment also invalidates this owner object.
    monkeypatch.setattr(
        running.machine, "_save", lambda: (_ for _ in ()).throw(OSError("disk"))
    )
    with pytest.raises(OSError):
        tick(running, 6)
    assert running.machine._profit_exit_reload_required
    with pytest.raises(OSError, match="reload"):
        tick(running)
    assert not running.wire.writes


def test_widget_original_exit_handoff_does_not_submit_redundant_target(running):
    if running.owner != "widget":
        return
    submitted(running)
    state = running.machine._state["symbols"]["005930"]
    state["exit_requested"] = True
    tick(running)
    assert running.record()["phase"] == "EXIT_CANCEL"
    running.wire.write_body = dict(
        return_code=0,
        ord_no="0000005",
        base_orig_ord_no="0000004",
        cncl_qty="10",
        dmst_stex_tp="SOR",
    )
    tick(running)
    running.wire.detailed[-1]["ord_remnq"] = "0"
    running.wire.detailed.append(
        detail(
            ord_no="0000005",
            ori_ord="0000004",
            ord_qty="10",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty="10",
            cnfm_tm="13:00:20",
        )
    )
    running.wire.current = []
    tick(running)
    assert KEY not in state
    assert (
        len(running.wire.writes) == 3
    )  # Original EXIT, not this helper, owns the next SELL.
    assert running.machine._open_qty(state) == 10


@pytest.mark.parametrize(
    "kinds,expected",
    [
        ({"machine_owner_scope"}, True),
        ({"legacy_machine_owner_scope"}, True),
        ({"machine_owner_scope", "manual_operator"}, False),
        ({"generic_veto"}, False),
        ({"auto"}, False),
    ],
)
def test_real_guard_keeps_manual_veto_above_machine_scope(monkeypatch, kinds, expected):
    m = SimpleNamespace(enabled=True, profit_exit_lock_held=lambda: True)
    monkeypatch.setattr(bridge, "_file_exclusion_snapshot", lambda _: (kinds, ""))
    monkeypatch.setattr(bridge, "_env_codes", lambda: set())
    monkeypatch.setattr(
        bridge,
        "independent_machine_ownership_source",
        lambda *a, **k: "machine_owner_scope",
    )
    assert (
        bridge.guard(
            m,
            symbol="005930",
            owner_type="widget_auto_trade",
            now=datetime.fromtimestamp(NOW / 1000, KST),
        )
        is expected
    )


def test_nonpositive_net_never_cancels_original(running):
    running.flags["bid"] = 10000
    for _ in range(4):
        tick(running, 6)
    assert not running.wire.writes


@pytest.mark.parametrize("route", ["SOR", "KRX", "NXT"])
def test_existing_ws_projection_exact_route_worst_depth(route):
    snapshot = projection(route, now_ms=NOW)
    result = executable_quote(
        symbol="005930",
        route=route,
        quantity=150,
        now=datetime.fromtimestamp(NOW / 1000, KST),
        snapshot=snapshot,
    )
    assert result["executable_bid"] == 9995 and result["available_quantity"] == 300
    with pytest.raises(ValueError):
        executable_quote(
            symbol="005930",
            route=route,
            quantity=301,
            now=datetime.fromtimestamp(NOW / 1000, KST),
            snapshot=snapshot,
        )


def test_policy_absent_off_and_cost_or_pin_invalid(tmp_path, monkeypatch):
    now = datetime.fromtimestamp(NOW / 1000, KST)
    monkeypatch.delenv(PATH_ENV, raising=False)
    monkeypatch.delenv(HASH_ENV, raising=False)
    assert load_policy(now=now, owner="episode", entered_at=now) is None
    path = tmp_path / "policy.json"
    raw = json.dumps(policy()).encode()
    path.write_bytes(raw)
    monkeypatch.setenv(PATH_ENV, str(path))
    monkeypatch.setenv(HASH_ENV, "0" * 64)
    with pytest.raises(ValueError, match="pin"):
        load_policy(now=now, owner="episode", entered_at=now)
