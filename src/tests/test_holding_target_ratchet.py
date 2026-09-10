"""No Provider or broker network: real owner loops, temporary policy/journals."""

from dataclasses import replace
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

import pytest

from src.tests.test_profit_stagnation_exit import running as running
from src.tests.test_machine_adaptive_exit_owner_loop import loop as loop
from src.tests.test_machine_adaptive_exit_broker import DATE, TARGET, detail, current
from src.trading.config.machine_target_ratchet_policy import FAMILY, PATH_ENV, HASH_ENV
from src.trading.order import target_ratchet as ratchet
from src.trading.market.target_pressure import CONTRACT
from src.trading.widget_auto_trade.engine import KST


@pytest.fixture
def enabled(running, tmp_path, monkeypatch):  # noqa: F811 -- imported pytest fixture
    r = running
    policy = dict(
        family=FAMILY,
        enabled=True,
        valid_from=DATE + "T00:00:00+09:00",
        valid_until="2026-09-11T00:00:00+09:00",
        owners=["episode", "widget_auto_trade"],
        round_trip_cost_pct=0.23,
        slippage_bps=5,
        cost_source_sha256="c" * 64,
        decision_contract=CONTRACT,
    )
    raw = json.dumps(policy).encode()
    p = tmp_path / "ratchet.json"
    p.write_bytes(raw)
    monkeypatch.setenv(PATH_ENV, str(p))
    monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())
    r.flags["bid"] = 10100
    from src.trading.order import profit_stagnation_owners as bridge

    def pressure(**kwargs):
        return dict(
            decision="RAISE_ONE_TICK",
            contract=CONTRACT,
            quote=bridge.executable_quote(**kwargs),
            reasons=[],
        )

    monkeypatch.setattr(ratchet, "evaluate_pressure", pressure)
    r.wire.write_body.update(mdfy_qty="10")
    r.wire.detailed[0]["ord_uv"] = "10100"
    r.wire.current[0]["ord_pric"] = "10100"
    r.record_ratchet = lambda: (
        r.machine._state["legs"][0]
        if r.owner == "episode"
        else r.machine._state["symbols"]["005930"]
    )
    if r.owner == "widget":
        # Exercise run_once's payload branch; source EXIT has been resolved by
        # its original consumer before the shared exit hook is eligible.
        from src.trading.order.profit_stagnation_owners import widget_symbol

        r.machine.snapshot_loader = lambda _: {"test_source": True}
        monkeypatch.setattr(
            r.machine,
            "process_payload",
            lambda spec, payload, now: widget_symbol(
                r.machine, r.record_ratchet(), now, allow_new_target_ratchet=True
            ),
        )
    return r


def tick(r):
    r.machine.run_once(datetime.fromtimestamp(r.clock[0] / 1000, KST))


def amendments(r):
    return [c for c in r.wire.calls if c["api_id"] == "kt10002"]


def confirm(r, *, parent_filled=0):
    qty = 10 - parent_filled
    r.wire.detailed = [
        detail(ord_remnq="0", cntr_qty=str(parent_filled)),
        detail(
            ord_no="0000003",
            ori_ord=TARGET.order_no,
            ord_qty=str(qty),
            ord_remnq=str(qty),
            ord_uv="10110",
            cnfm_qty=str(qty),
        ),
    ]
    r.wire.current = [
        current(
            ord_no="0000003",
            orig_ord_no=TARGET.order_no,
            ord_qty=str(qty),
            oso_qty=str(qty),
            ord_pric="10110",
        )
    ]


def test_original_owner_amends_one_tick_and_recovers_ack(enabled):
    r = enabled
    tick(r)
    assert len(amendments(r)) == 1
    assert amendments(r)[0]["payload"]["mdfy_uv"] == "10110"
    assert ratchet.KEY in r.record_ratchet()
    # ACK alone leaves original commitment; repeated loop never repeats write.
    tick(r)
    assert len(amendments(r)) == 1
    confirm(r)
    tick(r)
    row = r.record_ratchet()
    assert ratchet.KEY not in row
    if r.owner == "episode":
        assert row["target_order_no"] == "0000003"
        assert row["target_price"] == 10110
    else:
        assert row["orders"][-1]["order_no"] == "0000003"
        assert row["orders"][-1]["limit_price"] == 10110
    # Hash chain can be reread and registry still owns exactly 10 shares.
    claim = row["holding_target_history"][-1]
    assert (
        r.machine.owner_registry.owner_position_qty(
            claim["binding"]["position_id"], symbol="005930"
        )
        == 10
    )
    assert claim["trigger"] == "ws_executable_target_reached"
    assert claim["quote"]["executable_bid"] == 10100
    assert "ai" not in claim


def test_ws_trigger_never_calls_holding_ai(enabled, monkeypatch):
    from src.engine.ai_engine_openai import GPTSniperEngine

    def forbidden(*args, **kwargs):
        pytest.fail("WS ratchet must not call or wait for Holding AI")

    monkeypatch.setattr(GPTSniperEngine, "evaluate_scalping_holding_flow", forbidden)
    tick(enabled)
    assert len(amendments(enabled)) == 1
    assert not hasattr(enabled.machine, "_target_holding_job")


def test_only_one_broker_preflight(enabled, monkeypatch):
    from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter

    called = []
    original = RegisteredSellAdapter.snapshot

    def counted(self, order):
        called.append(order)
        return original(self, order)

    monkeypatch.setattr(RegisteredSellAdapter, "snapshot", counted)
    tick(enabled)
    assert called == [TARGET]
    assert len(amendments(enabled)) == 1


def test_real_snapshot_pressure_reaches_original_broker_adapter(
    enabled, tmp_path, monkeypatch
):
    from src.tests.test_target_pressure import snapshot
    from src.trading.market.target_pressure import evaluate_pressure
    from src.trading.market.micro_confirmation import LIVE_SNAPSHOT_PATH_ENV

    r = enabled
    path = tmp_path / "ws.json"
    path.write_text(
        json.dumps(snapshot(datetime.fromtimestamp(r.clock[0] / 1000, KST)))
    )
    monkeypatch.setenv(LIVE_SNAPSHOT_PATH_ENV, str(path))
    monkeypatch.setattr(ratchet, "evaluate_pressure", evaluate_pressure)
    tick(r)
    assert len(amendments(r)) == 1
    pending = r.record_ratchet()[ratchet.KEY]
    assert pending["pressure"]["contract"] == CONTRACT
    assert pending["prewrite_pressure"]["decision"] == "RAISE_ONE_TICK"


def test_pressure_keep_does_not_claim_target_or_amend(enabled, monkeypatch):
    original = ratchet.evaluate_pressure

    def weak(**kwargs):
        return dict(original(**kwargs), decision="KEEP_TARGET", reasons=["refill_weak"])

    monkeypatch.setattr(ratchet, "evaluate_pressure", weak)
    tick(enabled)
    assert amendments(enabled) == []
    assert ratchet.KEY not in enabled.record_ratchet()
    assert (
        enabled.record_ratchet()["holding_target_last_decision"]["decision"]
        == "KEEP_TARGET"
    )


def test_pressure_reversal_after_reservation_never_posts(enabled, monkeypatch):
    r = enabled
    original, reserve = ratchet.evaluate_pressure, r.machine.owner_registry.reserve
    changed = [False]

    def signal(**kwargs):
        value = original(**kwargs)
        if changed[0]:
            value["decision"] = "KEEP_TARGET"
        return value

    def reserved(**kwargs):
        result = reserve(**kwargs)
        if kwargs.get("action") == "AMEND":
            changed[0] = True
        return result

    monkeypatch.setattr(ratchet, "evaluate_pressure", signal)
    monkeypatch.setattr(r.machine.owner_registry, "reserve", reserved)
    tick(r)
    assert amendments(r) == []


def test_prepressure_pin_cannot_silently_enable_new_rules(enabled, monkeypatch):
    path = Path(os.environ[PATH_ENV])
    p = json.loads(path.read_bytes())
    p.pop("decision_contract")
    raw = json.dumps(p).encode()
    path.write_bytes(raw)
    monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())
    tick(enabled)
    assert amendments(enabled) == []
    assert ratchet.KEY not in enabled.record_ratchet()


@pytest.mark.parametrize("weak", [False, True])
def test_snapshot_wake_is_read_only_and_only_shortens_eligible_sleep(
    enabled, tmp_path, monkeypatch, weak
):
    from copy import deepcopy
    from src.trading.market.micro_confirmation import LIVE_SNAPSHOT_PATH_ENV

    r = enabled
    path = tmp_path / "snapshot-watch.json"
    path.write_text("initial")
    monkeypatch.setenv(LIVE_SNAPSHOT_PATH_ENV, str(path))
    clock = [0.0]

    def sleep(seconds):
        clock[0] += seconds
        if clock[0] == 0.05:
            path.write_text("new snapshot")

    monkeypatch.setattr(ratchet.time, "sleep", sleep)
    monkeypatch.setattr(ratchet.time, "monotonic", lambda: clock[0])
    if weak:
        original = ratchet.evaluate_pressure
        monkeypatch.setattr(
            ratchet,
            "evaluate_pressure",
            lambda **k: dict(original(**k), decision="KEEP_TARGET"),
        )
    before, calls = deepcopy(r.machine._state), len(r.wire.calls)
    ratchet.wait_for_pressure(
        r.machine,
        6.0,
        owner_type=("episode" if r.owner == "episode" else "widget_auto_trade"),
        now_fn=lambda: datetime.fromtimestamp(r.clock[0] / 1000, KST),
    )
    assert clock[0] == (6.0 if weak else 0.05)
    assert r.machine._state == before
    assert len(r.wire.calls) == calls


def test_off_policy_preserves_original_sleep_without_probe(enabled, monkeypatch):
    monkeypatch.delenv(PATH_ENV)
    monkeypatch.delenv(HASH_ENV)
    sleeps = []
    monkeypatch.setattr(ratchet.time, "sleep", sleeps.append)

    def forbidden(**kwargs):
        pytest.fail("OFF feature must not evaluate source")

    monkeypatch.setattr(ratchet, "evaluate_pressure", forbidden)
    ratchet.wait_for_pressure(
        enabled.machine, 6, owner_type="episode", now_fn=lambda: None
    )
    assert sleeps == [6]


def test_production_owner_loop_uses_pressure_wait(enabled, monkeypatch):
    from src.trading.order import regular_two_leg_machine
    from src.trading.widget_auto_trade import engine

    class StopLoop(Exception):
        pass

    calls = []

    def waited(owner, delay, **kwargs):
        calls.append((owner, delay, kwargs["owner_type"]))
        raise StopLoop

    monkeypatch.setattr(enabled.machine, "run_once", lambda: {"status": "RUNNING"})
    module = regular_two_leg_machine if enabled.owner == "episode" else engine
    monkeypatch.setattr(module, "wait_for_pressure", waited)
    with pytest.raises(StopLoop):
        if enabled.owner == "episode":
            enabled.machine.run_until_terminal(interval_sec=6)
        else:
            enabled.machine.run_forever(interval_sec=1)
    assert calls[0][0] is enabled.machine
    assert 0 < calls[0][1] <= (6 if enabled.owner == "episode" else 1)


def test_source_failure_replaces_old_raise_diagnostic_without_claim(
    enabled, monkeypatch
):
    enabled.record_ratchet()["holding_target_last_decision"] = {
        "decision": "RAISE_ONE_TICK"
    }

    def unavailable(**kwargs):
        raise ValueError("pressure_source_gap")

    monkeypatch.setattr(ratchet, "evaluate_pressure", unavailable)
    tick(enabled)
    assert (
        enabled.record_ratchet()["holding_target_last_decision"]["decision"]
        == "KEEP_TARGET"
    )
    assert amendments(enabled) == []
    assert ratchet.KEY not in enabled.record_ratchet()


@pytest.mark.parametrize("bid", [10000, 10090])
def test_below_target_does_not_amend(enabled, bid):
    enabled.flags["bid"] = bid
    tick(enabled)
    assert amendments(enabled) == []


def test_rejection_stops_ratchets_without_inventing_fill(enabled):
    r = enabled
    r.wire.write_body = {"return_code": 3, "return_msg": "rejected"}
    tick(r)
    row = r.record_ratchet()
    assert ratchet.KEY not in row
    assert row["holding_target_disabled_order"] == TARGET.order_no
    assert row["holding_target_status"] == "amend_rejected_original_retained"
    for _ in range(3):
        tick(r)
    assert len(amendments(r)) == 1
    if r.owner == "episode":
        assert row["target_filled_qty"] == 0
        assert row["position_qty"] == 10
    else:
        target = next(o for o in row["orders"] if o["order_no"] == TARGET.order_no)
        assert target["filled_qty"] == 0
        assert target["status"] == "SUBMITTED"


@pytest.mark.parametrize(
    "status,body",
    [
        (500, {"return_code": 3}),
        (429, {"return_code": 3}),
        (200, {"return_code": 0}),
        (200, {"return_code": 3, "ord_no": "0000003"}),
    ],
)
def test_ambiguous_response_preserves_claim_and_never_resends(enabled, status, body):
    from src.tests.test_machine_adaptive_exit_broker import response

    r = enabled
    r.wire.overrides["kt10002"] = response(body, status=status)
    tick(r)
    tick(r)
    assert len(amendments(r)) == 1
    assert ratchet.KEY in r.record_ratchet()
    assert "holding_target_disabled_order" not in r.record_ratchet()


def test_source_lost_after_reservation_never_posts(enabled, monkeypatch):
    r = enabled
    reserve = r.machine.owner_registry.reserve

    def lose_source(**kwargs):
        result = reserve(**kwargs)
        if kwargs.get("action") == "AMEND":
            r.flags["quote"] = False
        return result

    monkeypatch.setattr(r.machine.owner_registry, "reserve", lose_source)
    tick(r)
    assert amendments(r) == []
    assert ratchet.KEY not in r.record_ratchet()


def test_old_holding_policy_cannot_enable_ws_strategy(enabled, monkeypatch, tmp_path):
    import os

    raw = json.loads(Path(os.environ[PATH_ENV]).read_text())
    raw["family"] = "machine_holding_target_ratchet_v1"
    encoded = json.dumps(raw).encode()
    path = tmp_path / "old-holding-policy.json"
    path.write_bytes(encoded)
    monkeypatch.setenv(PATH_ENV, str(path))
    monkeypatch.setenv(HASH_ENV, hashlib.sha256(encoded).hexdigest())
    tick(enabled)
    assert amendments(enabled) == []


def test_ratchet_has_no_strategy_count_cap(enabled):
    from src.trading.order.tick_utils import move_price_by_ticks

    r = enabled
    parent, price = TARGET.order_no, 10100
    for step in range(12):
        child = f"{step + 3:07d}"
        next_price = move_price_by_ticks(price, 1)
        r.flags["bid"] = price
        r.wire.write_body.update(ord_no=child, base_orig_ord_no=parent)
        tick(r)
        assert len(amendments(r)) == step + 1
        assert amendments(r)[-1]["payload"]["mdfy_uv"] == str(next_price)
        r.wire.detailed = [
            detail(ord_no=parent, ord_uv=str(price), ord_remnq="0"),
            detail(ord_no=child, ori_ord=parent, ord_uv=str(next_price), cnfm_qty="10"),
        ]
        r.wire.current = [
            current(ord_no=child, orig_ord_no=parent, ord_pric=str(next_price))
        ]
        tick(r)
        assert ratchet.KEY not in r.record_ratchet()
        parent, price = child, next_price
    assert len(r.record_ratchet()["holding_target_history"]) == 12


def test_partial_fill_never_amends(enabled):
    enabled.wire.detailed = [detail(cntr_qty="1", ord_remnq="9")]
    enabled.wire.current = [current(cntr_qty="1", oso_qty="9")]
    tick(enabled)
    assert amendments(enabled) == []


def test_policy_off_does_not_orphan_pending_amendment(enabled, monkeypatch):
    r = enabled
    tick(r)
    monkeypatch.delenv(PATH_ENV)
    monkeypatch.delenv(HASH_ENV)
    confirm(r)
    tick(r)
    assert ratchet.KEY not in r.record_ratchet()
    assert len(amendments(r)) == 1


def test_timeout_never_retries(enabled):
    r = enabled
    r.wire.crash = True
    tick(r)
    tick(r)
    assert len(amendments(r)) == 1
    assert ratchet.KEY in r.record_ratchet()
    assert "unresolved" in r.record_ratchet()["holding_target_status"]


def test_actual_broker_target_price_must_match_owner(enabled):
    enabled.wire.detailed[0]["ord_uv"] = "10120"
    enabled.wire.current[0]["ord_pric"] = "10120"
    tick(enabled)
    assert amendments(enabled) == []


def test_independent_episode_leg_is_not_an_extra_approval_gate(enabled):
    r = enabled
    if r.owner != "episode":
        return
    r.machine._state["legs"][1]["status"] = "BUY_OPEN"
    assert ratchet.episode(
        r.machine, r.record_ratchet(), datetime.fromtimestamp(r.clock[0] / 1000, KST)
    )
    assert len(amendments(r)) == 1


def test_second_step_uses_reconciled_child(enabled):
    r = enabled
    tick(r)
    confirm(r)
    tick(r)
    r.flags["bid"] = 10110
    r.wire.write_body.update(ord_no="0000004", base_orig_ord_no="0000003")
    tick(r)
    assert len(amendments(r)) == 2
    assert amendments(r)[1]["payload"]["orig_ord_no"] == "0000003"
    assert amendments(r)[1]["payload"]["mdfy_uv"] == "10120"


def test_partial_fill_race_is_preserved_without_second_amendment(enabled):
    r = enabled
    tick(r)
    confirm(r, parent_filled=1)
    tick(r)
    tick(r)
    assert len(amendments(r)) == 1
    state = r.record_ratchet()
    if r.owner == "episode":
        assert ratchet.KEY in state
        assert "exact_episode_recovery" in state["holding_target_status"]
    else:
        assert ratchet.KEY not in state
        assert state["orders"][-2]["filled_qty"] == 1
        assert state["orders"][-1]["requested_qty"] == 9
        assert state["orders"][-2]["fill_price"] is None


def test_original_exit_and_lock_dominate(enabled):
    r = enabled
    r.flags["lock"] = False
    tick(r)
    assert amendments(r) == []
    r.flags["lock"] = True
    if r.owner == "widget":
        r.record_ratchet()["exit_requested"] = True
    else:
        r.flags["guard"] = False
    tick(r)
    assert amendments(r) == []


def test_missing_widget_source_does_not_start_amendment(enabled):
    r = enabled
    if r.owner != "widget":
        return
    r.machine.snapshot_loader = lambda _: None
    tick(r)
    assert amendments(r) == []


def test_restart_reads_durable_claim_and_never_resubmits(enabled):
    r = enabled
    tick(r)
    r.machine._state = json.loads(r.machine.state_path.read_text())
    tick(r)
    assert len(amendments(r)) == 1
    confirm(r)
    tick(r)
    assert ratchet.KEY not in r.record_ratchet()


def test_amendment_reservation_cannot_be_a_buy(enabled):
    r = enabled
    tick(r)
    state = r.record_ratchet()[ratchet.KEY]
    context = (
        r.machine._episode_owner_context(
            leg=r.record_ratchet(), action="holding_target", ordinal=1
        )
        if r.owner == "episode"
        else r.machine._owner_context_from_order(r.record_ratchet()["orders"][-1])
    )
    from src.trading.order.owner_custody_registry import OwnerRegistryError

    with pytest.raises(OwnerRegistryError):
        r.machine.owner_registry.reserve(
            context=replace(context, client_intent_id="illegal-buy-amend"),
            symbol="005930",
            side="BUY",
            quantity=10,
            route="SOR",
            order_date=DATE,
            action="AMEND",
            original_order_no=TARGET.order_no,
            authority_policy_id=FAMILY,
            authority_policy_hash=state["pin"],
        )
