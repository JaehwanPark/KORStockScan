"""Synthetic tapes and isolated policies; no broker or profitability claims."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from src.trading.market.entry_adverse_flow import CONTRACT, evaluate_snapshot
from src.trading.config.machine_entry_adverse_policy import (
    PATH_ENV,
    HASH_ENV,
    load_policy,
)
from src.trading.order import entry_adverse_guard as guard

SCOPE = dict(
    owner="widget",
    scope_id="005930:KRX_REGULAR",
    symbol="005930",
    route="SOR",
    session="KRX_REGULAR",
)
NOW = datetime(2026, 9, 9, 4, tzinfo=timezone.utc)


def source(data):
    return data["stocks"]["005930"]["machine_confirmation_routes"]["SOR"]


def snapshot(now):
    cutoff = int(now.timestamp() * 1000)
    item = "005930_AL"

    def depth(seq, offset, qty):
        return dict(
            item=item,
            transport_epoch=1,
            route_sequence=seq,
            received_at_ms=cutoff + offset,
            best_bid=10100,
            best_ask=10110,
            best_ask_qty=qty,
            ask_levels=[dict(price=10110, quantity=qty)],
            bid_levels=[dict(price=10100, quantity=100)],
        )

    def trade(seq, offset, qty):
        return dict(
            item=item,
            transport_epoch=1,
            route_sequence=seq,
            received_at_ms=cutoff + offset,
            price=10110,
            volume=qty,
            aggressor_side="BUY",
        )

    return dict(
        schema_version="kiwoom_ws_dashboard_snapshot_v1",
        decision_authority="source_quality_only",
        runtime_effect=False,
        machine_confirmation_input_contract=dict(
            schema="machine_entry_confirmation_ws_snapshot_v1",
            decision_authority="market_data_input_only_no_order_authority",
            exact_route_required=True,
            causal_past_only=True,
            runtime_effect=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
        stocks={
            "005930": {
                "machine_confirmation_routes": {
                    "SOR": dict(
                        realtime_types={
                            k: dict(
                                item=item,
                                transport_epoch=1,
                                route_sequence=seq,
                                observed_epoch=(cutoff + offset) / 1000,
                            )
                            for k, seq, offset in (("0B", 4, -150), ("0D", 3, 0))
                        },
                        recent_depth=[
                            depth(1, -1000, 120),
                            depth(2, -100, 20),
                            depth(3, 0, 25),
                        ],
                        recent_trades=[
                            trade(1, -1100, 1),
                            trade(2, -800, 40),
                            trade(3, -300, 40),
                            trade(4, -150, 30),
                        ],
                        sequence_authority="local_projection_continuity_not_exchange_completeness",
                    )
                }
            }
        },
    )


def tape(now=NOW, adverse=True):
    data = snapshot(now)
    s = source(data)
    if adverse:
        for row in s["recent_trades"]:
            row["aggressor_side"] = "SELL"
        s["recent_depth"][1]["best_bid"] = 10090
        s["recent_depth"][2]["best_bid"] = 10080
    return data


def calc(data):
    return evaluate_snapshot(
        snapshot=data,
        symbol="005930",
        route="SOR",
        cutoff_ms=int(NOW.timestamp() * 1000),
    )


@pytest.fixture
def pin(tmp_path, monkeypatch):
    policy = dict(
        contract=CONTRACT,
        enabled=True,
        valid_from="2026-06-05T00:00:00+09:00",
        valid_until=None,
        scopes=[SCOPE],
        approval_reference="test-only-no-live-authority",
    )
    path = tmp_path / "policy.json"

    def write():
        raw = json.dumps(policy).encode()
        path.write_bytes(raw)
        monkeypatch.setenv(PATH_ENV, str(path))
        monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())

    write()
    return policy, write


@pytest.mark.parametrize("adverse", [True, False])
def test_relational_rule(adverse):
    result = calc(tape(adverse=adverse))
    assert result["action"] == ("DEFER_ADVERSE_FLOW" if adverse else "CONTINUE")


@pytest.mark.parametrize(
    "mutation", ["bid_recovery", "buy_dominance", "sell_easing", "bid_support"]
)
def test_each_condition_is_necessary(mutation):
    data = tape()
    s = source(data)
    if mutation == "bid_recovery":
        s["recent_depth"][1]["best_bid"] = 10070
    elif mutation == "buy_dominance":
        s["recent_trades"][1]["aggressor_side"] = "BUY"
    elif mutation == "sell_easing":
        s["recent_trades"][1]["volume"] = 1000
    else:
        s["recent_depth"][2]["best_bid"] = 10100
    assert calc(data)["action"] == "CONTINUE"


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "duplicate_conflict",
        "gap",
        "truncated",
        "epoch",
        "authority",
        "missing",
        "stale",
    ],
)
def test_source_failure_is_not_neutral(mutation):
    data = tape()
    s = source(data)
    if mutation == "unknown":
        s["recent_trades"][1]["aggressor_side"] = "UNKNOWN"
    elif mutation == "duplicate_conflict":
        s["recent_trades"].append(dict(s["recent_trades"][1], volume=99))
    elif mutation == "gap":
        s["recent_trades"].pop(2)
    elif mutation == "truncated":
        s["recent_depth"].pop(0)
    elif mutation == "epoch":
        s["realtime_types"]["0B"]["transport_epoch"] = 2
    elif mutation == "authority":
        data["runtime_effect"] = True
    elif mutation == "missing":
        s["recent_trades"] = []
    else:
        s["recent_depth"][0]["received_at_ms"] -= 2000
    assert calc(data)["action"] == "SOURCE_UNAVAILABLE"


def test_causal_cutoff_duplicate_and_half_boundary():
    data = tape()
    s = source(data)
    s["recent_trades"][1]["received_at_ms"] = int(NOW.timestamp() * 1000) - 500
    before = calc(data)
    s["recent_trades"].append(deepcopy(s["recent_trades"][1]))
    s["recent_trades"].append(
        dict(
            s["recent_trades"][-2],
            received_at_ms=int(NOW.timestamp() * 1000) + 1,
            aggressor_side="UNKNOWN",
        )
    )
    assert calc(data) == before
    assert before["sell_qty_halves"] == [40, 70]


def prepare(holder, now=NOW, identity="signal1", **kwargs):
    return guard.prepare(
        holder=holder,
        identity=identity,
        signal_at=NOW,
        now=now,
        scope=SCOPE,
        timing_mode="baseline_immediate",
        **kwargs,
    )


def test_wait_recovery_terminal_and_no_extension(pin, monkeypatch):
    clock = [NOW]
    adverse = [True]
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (tape(clock[0], adverse[0]), "ready"),
    )
    holder = {}
    assert not prepare(holder)
    assert holder[guard.KEY]["next_checkpoint_ms"] == 1000
    clock[0] += timedelta(seconds=1)
    adverse[0] = False
    assert prepare(holder, clock[0])
    assert not prepare(holder, NOW + timedelta(milliseconds=6501))
    assert not prepare(holder, NOW + timedelta(seconds=1))
    assert holder[guard.KEY]["action"] == "SKIP_DEADLINE"


@pytest.mark.parametrize("elapsed,allowed", [(5000, True), (6500, True), (6501, False)])
def test_last_checkpoint_grace(pin, monkeypatch, elapsed, allowed):
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (tape(NOW + timedelta(seconds=5), False), "ready"),
    )
    holder = {}
    assert prepare(holder, NOW + timedelta(milliseconds=elapsed)) is allowed


@pytest.mark.parametrize(
    "data,action", [(None, "SKIP_SOURCE_UNAVAILABLE"), ("adverse", "SKIP_ADVERSE_FLOW")]
)
def test_last_checkpoint_never_falls_through(pin, monkeypatch, data, action):
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (tape(NOW + timedelta(seconds=5)) if data else None, "gap"),
    )
    holder = {}
    assert not prepare(holder, NOW + timedelta(seconds=5))
    assert holder[guard.KEY]["action"] == action


def test_revocation_and_terminal_identity_history(pin, monkeypatch):
    monkeypatch.setattr(
        guard, "load_live_dynamic_confirmation_source", lambda: (tape(), "ready")
    )
    holder = {}
    assert not prepare(holder)
    monkeypatch.delenv(PATH_ENV)
    monkeypatch.delenv(HASH_ENV)
    assert not prepare(holder)
    assert prepare(holder, identity="signal2")
    assert guard.KEY not in holder
    assert not prepare(holder)


def test_policy_no_daily_economics_gate_and_exact_scope(pin):
    selected = load_policy(scope=SCOPE, now=NOW, signal_at=NOW)
    assert selected is not None
    assert (
        load_policy(scope=dict(SCOPE, symbol="000001"), now=NOW, signal_at=NOW) is None
    )
    assert (
        load_policy(
            scope=SCOPE, now=NOW + timedelta(days=7), signal_at=NOW + timedelta(days=7)
        )
        is not None
    )


@pytest.mark.parametrize(
    "change", ["pin", "duplicate_scopes", "approval", "extra", "owner"]
)
def test_malformed_activation_blocks(pin, monkeypatch, change):
    p, write = pin
    if change == "pin":
        monkeypatch.setenv(HASH_ENV, "0" * 64)
    else:
        if change == "duplicate_scopes":
            p["scopes"].append(dict(SCOPE))
        if change == "approval":
            p["approval_reference"] = ""
        if change == "extra":
            p["positive_ev_required"] = True
        if change == "owner":
            p["scopes"][0] = dict(SCOPE, owner="main")
        write()
    holder = {}
    assert not prepare(holder)
    assert holder[guard.KEY]["action"] == "SKIP_POLICY_INVALID"


def test_dynamic_policy_not_overridden(pin):
    holder = {}
    assert not guard.prepare(
        holder=holder,
        identity="a",
        signal_at=NOW,
        now=NOW,
        scope=SCOPE,
        timing_mode="dynamic",
    )
    assert holder[guard.KEY]["action"] == "SKIP_TIMING_CONFLICT"


@pytest.mark.parametrize(
    "failure", ["adverse", "gap", "deadline", "owner", "save", "epoch"]
)
def test_final_transport_veto_after_waits(pin, monkeypatch, failure):
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (tape(adverse=False), "ready"),
    )
    holder = {}
    assert prepare(holder)
    data = tape(adverse=failure == "adverse")
    if failure == "epoch":
        for kind in ("0B", "0D"):
            source(data)["realtime_types"][kind]["transport_epoch"] = 2
        for stream in ("recent_depth", "recent_trades"):
            for row in source(data)[stream]:
                row["transport_epoch"] = 2
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (None if failure == "gap" else data, "ready"),
    )

    def save():
        if failure == "save":
            raise OSError("disk_error")

    with pytest.raises(guard.EntryNotSent):
        guard.final_check(
            holder=holder,
            clock=lambda: NOW + timedelta(seconds=7) if failure == "deadline" else NOW,
            validate_owner=lambda: failure != "owner",
            save=save,
        )
    assert holder[guard.KEY]["action"] != "TRANSPORT_STARTED"


def test_single_transport_context_no_cancel_or_other_task_effect(pin, monkeypatch):
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (tape(adverse=False), "ready"),
    )
    holder = {}
    assert prepare(holder)
    calls = []
    callback = lambda: guard.final_check(
        holder=holder,
        clock=lambda: NOW,
        validate_owner=lambda: True,
        save=lambda: calls.append(1),
    )
    with guard.transport_check(callback):
        guard.before_transport("kt10003")
        assert not calls
        guard.before_transport("kt10000")
        with pytest.raises(guard.EntryNotSent):
            guard.before_transport("kt10000")
    guard.before_transport("kt10000")
    assert calls == [1]


@pytest.mark.parametrize("limit", ["policy", "owner", "source", "clock_regression"])
def test_save_latency_cannot_cross_earlier_deadline(pin, monkeypatch, limit):
    policy, write = pin
    if limit == "policy":
        policy["valid_until"] = (NOW + timedelta(milliseconds=500)).isoformat()
        write()
    monkeypatch.setattr(
        guard,
        "load_live_dynamic_confirmation_source",
        lambda: (tape(adverse=False), "ready"),
    )
    holder = {}
    assert prepare(holder)
    if limit == "owner":
        holder[guard.KEY]["owner_deadline_ms"] = int(NOW.timestamp() * 1000) + 500
    clock = {"now": NOW}

    def save():
        clock["now"] = NOW + timedelta(seconds=-1 if limit == "clock_regression" else 2)

    with pytest.raises(guard.EntryNotSent):
        guard.final_check(
            holder=holder,
            clock=lambda: clock["now"],
            validate_owner=lambda: True,
            save=save,
        )
    assert holder[guard.KEY]["action"] == "SKIP_DEADLINE"


@pytest.mark.parametrize(
    "owner,scope_id,symbol,route,session",
    [
        ("widget", "005930:KRX_REGULAR", "005930", "SOR", "KRX_REGULAR"),
        ("episode", "morning", "005930", "NXT", "NXT_PREMARKET"),
        ("episode", "low_price:custom", "080220", "KRX", "KRX_REGULAR"),
    ],
)
def test_operator_all_existing_scopes_preserves_original_owner(
    pin, owner, scope_id, symbol, route, session
):
    from src.trading.config.machine_entry_adverse_policy import load_policy

    p, write = pin
    p["scopes"] = "all_existing_widget_episode"
    write()
    scope = dict(
        owner=owner, scope_id=scope_id, symbol=symbol, route=route, session=session
    )
    assert load_policy(scope=scope, now=NOW, signal_at=NOW) is not None
    with pytest.raises(ValueError, match="scope_invalid"):
        load_policy(scope=dict(scope, owner="main"), now=NOW, signal_at=NOW)
