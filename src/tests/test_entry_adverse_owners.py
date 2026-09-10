"""Real owner loops, fake wire; every writer is isolated in tmp_path."""

from datetime import timedelta
import hashlib
import json

import pytest

from src.tests import test_widget_signal_auto_trade as widget
from src.tests import test_samsung_midday_one_share as episode
from src.tests.test_entry_adverse_flow import tape
from src.trading.config.machine_entry_adverse_policy import PATH_ENV, HASH_ENV
from src.trading.order import (
    entry_adverse_guard as guard,
    entry_adverse_owners as owners,
)
from src.trading.market.entry_adverse_flow import CONTRACT


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(tmp_path / "registry.jsonl")
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(tmp_path / "absent.json")
    )
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "test-entry-adverse")
    monkeypatch.setenv(owners.EVENT_ROOT_ENV, str(tmp_path / "events"))
    monkeypatch.setattr(owners, "is_buy_side_paused", lambda: False)
    flags = {"time": widget._at(20), "adverse": True, "scope": None}
    monkeypatch.setattr(owners, "now", lambda: flags["time"])
    monkeypatch.setattr(
        owners,
        "_timing",
        lambda *a, **k: dict(
            mode="baseline_immediate", provenance={"policy_hash": None}
        ),
    )

    def data():
        s = tape(flags["time"], flags["adverse"])
        symbol = flags["scope"]["symbol"]
        stock = s["stocks"].pop("005930")
        s["stocks"][symbol] = stock
        route = stock["machine_confirmation_routes"]["SOR"]
        from src.trading.market.micro_confirmation import _live_route_item

        item = _live_route_item(symbol, flags["scope"]["route"])
        for entry in route["realtime_types"].values():
            entry["item"] = item
        for stream in ("recent_depth", "recent_trades"):
            for row in route[stream]:
                row["item"] = item
        return s, "ready"

    monkeypatch.setattr(guard, "load_live_dynamic_confirmation_source", data)

    def enable(scope):
        flags["scope"] = scope
        p = dict(
            contract=CONTRACT,
            enabled=True,
            valid_from="2026-06-05T00:00:00+09:00",
            valid_until=None,
            scopes=[scope],
            approval_reference="test-only",
        )
        raw = json.dumps(p).encode()
        path = tmp_path / "pin.json"
        path.write_bytes(raw)
        monkeypatch.setenv(PATH_ENV, str(path))
        monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())

    flags["enable"] = enable
    return flags


def widget_machine(tmp_path, monkeypatch, flags):
    box = {"payload": widget._payload(flags["time"], entry_id="ENTRY-A")}
    machine, gateway, _ = widget._trader(tmp_path, monkeypatch, box)
    gateway.entry_adverse_transport_supported = True
    submit = gateway.submit_buy

    def guarded(**kwargs):
        guard.before_transport("kt10000")
        return submit(**kwargs)

    gateway.submit_buy = guarded
    flags["enable"](
        dict(
            owner="widget",
            scope_id="999999:KRX_REGULAR",
            symbol="999999",
            route="KRX",
            session="KRX_REGULAR",
        )
    )
    return machine, gateway, box


def test_widget_wait_then_recovery_submits_once(tmp_path, monkeypatch, setup):
    m, g, _ = widget_machine(tmp_path, monkeypatch, setup)
    m.run_once(setup["time"])
    assert not g.buy_calls
    s = m._state["symbols"]["999999"]
    assert s[guard.KEY]["action"] == "WAIT"
    setup["time"] += timedelta(seconds=1)
    setup["adverse"] = False
    m.run_once(setup["time"])
    assert len(g.buy_calls) == 1
    assert s[guard.KEY]["action"] == "TRANSPORT_STARTED"
    m.run_once(setup["time"])
    assert len(g.buy_calls) == 1


def test_widget_restart_keeps_original_deadline(tmp_path, monkeypatch, setup):
    m, g, _ = widget_machine(tmp_path, monkeypatch, setup)
    m.run_once(setup["time"])
    original = m._state["symbols"]["999999"][guard.KEY]["t0_ms"]
    setup["time"] += timedelta(seconds=7)
    setup["adverse"] = False
    restored, gateway, _ = widget_machine(tmp_path, monkeypatch, setup)
    restored.run_once(setup["time"])
    state = restored._state["symbols"]["999999"][guard.KEY]
    assert state["t0_ms"] == original and state["action"] == "SKIP_DEADLINE"
    assert not gateway.buy_calls


def test_widget_late_gateway_veto_releases_only_unsent(tmp_path, monkeypatch, setup):
    m, g, _ = widget_machine(tmp_path, monkeypatch, setup)
    setup["adverse"] = False
    submit = g.submit_buy

    def delayed(**kwargs):
        setup["adverse"] = True
        return submit(**kwargs)

    g.submit_buy = delayed
    m.run_once(setup["time"])
    s = m._state["symbols"]["999999"]
    assert not g.buy_calls
    assert s["orders"][-1]["status"] == "NOT_SENT"
    assert not s["entry_episode_open"]
    setup["adverse"] = False
    setup["time"] += timedelta(seconds=1)
    g.submit_buy = submit
    m.run_once(setup["time"])
    assert len(g.buy_calls) == 1


def test_widget_expiry_and_signal_loss_are_sticky(tmp_path, monkeypatch, setup):
    m, g, box = widget_machine(tmp_path, monkeypatch, setup)
    m.run_once(setup["time"])
    box["payload"] = widget._payload(setup["time"])
    m.run_once(setup["time"])
    box["payload"] = widget._payload(setup["time"], entry_id="ENTRY-A")
    setup["adverse"] = False
    setup["time"] += timedelta(seconds=1)
    m.run_once(setup["time"])
    assert not g.buy_calls
    assert (
        m._state["symbols"]["999999"][guard.KEY]["action"] == "SKIP_SIGNAL_INVALIDATED"
    )


def test_episode_wait_then_two_original_legs(tmp_path, monkeypatch, setup):
    setup["time"] = episode._scan_at(12, 1)
    g = episode.FakeGateway()
    m = episode._machine(tmp_path, g)
    g.entry_adverse_transport_supported = True
    submit = g.submit_limit_buy

    def guarded(**kwargs):
        guard.before_transport("kt10000")
        return submit(**kwargs)

    g.submit_limit_buy = guarded
    setup["enable"](
        dict(
            owner="episode",
            scope_id=m.entry_timing_scope_id,
            symbol="005930",
            route="SOR",
            session=m.entry_timing_session,
        )
    )
    m.run_once(setup["time"])
    assert not g.buy_calls
    assert m._next_loop_delay_sec(interval_sec=6, now=setup["time"]) <= 1
    setup["time"] += timedelta(seconds=1)
    setup["adverse"] = False
    m.run_once(setup["time"])
    assert g.buy_calls == [98100, 98000]
    assert all(l["quantity"] == 10 for l in m._state["legs"])


def test_episode_second_leg_checks_after_first_transport(tmp_path, monkeypatch, setup):
    setup["time"] = episode._scan_at(12, 1)
    setup["adverse"] = False
    g = episode.FakeGateway()
    m = episode._machine(tmp_path, g)
    g.entry_adverse_transport_supported = True
    submit = g.submit_limit_buy

    def guarded(**kwargs):
        guard.before_transport("kt10000")
        result = submit(**kwargs)
        setup["adverse"] = True
        return result

    g.submit_limit_buy = guarded
    setup["enable"](
        dict(
            owner="episode",
            scope_id=m.entry_timing_scope_id,
            symbol="005930",
            route="SOR",
            session=m.entry_timing_session,
        )
    )
    m.run_once(setup["time"])
    assert g.buy_calls == [98100]
    assert m._state["legs"][0]["status"] == "BUY_OPEN"
    assert m._state["legs"][1]["status"] == "PLANNED"
    assert not g.cancel_calls


@pytest.mark.parametrize("route,hour", [("NXT", 8), ("SOR", 9)])
def test_all_scope_morning_routes_use_guard_before_wire(
    tmp_path, monkeypatch, setup, route, hour
):
    from src.tests import test_samsung_morning_one_share as morning
    from src.trading.config.machine_entry_adverse_policy import PATH_ENV

    setup["time"] = morning._at(10, hour)
    setup["adverse"] = True
    gateway = morning.FakeGateway()
    machine = morning._machine(tmp_path, gateway)
    gateway.entry_adverse_transport_supported = True
    original = gateway.submit_limit_buy

    def submit(**kwargs):
        guard.before_transport("kt10000")
        return original(**kwargs)

    gateway.submit_limit_buy = submit
    scope = dict(
        owner="episode",
        scope_id=machine.entry_timing_scope_id,
        symbol="005930",
        route=route,
        session="NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR",
    )
    setup["enable"](scope)
    from pathlib import Path
    import os

    pin = Path(os.environ[PATH_ENV])
    payload = json.loads(pin.read_text())
    payload["scopes"] = "all_existing_widget_episode"
    raw = json.dumps(payload).encode()
    pin.write_bytes(raw)
    monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())
    machine.run_once(setup["time"])
    assert not gateway.buy_calls
    assert any(guard.KEY in leg for leg in machine._state["legs"])
    setup["adverse"] = False
    setup["time"] += timedelta(seconds=1)
    machine.run_once(setup["time"])
    assert len(gateway.buy_calls) == 2
    assert all(
        leg[guard.KEY]["action"] == "TRANSPORT_STARTED"
        for leg in machine._state["legs"]
        if leg.get("route") == route
    )
