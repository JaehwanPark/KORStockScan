"""Surviving Doosan watch boundaries after complete automatic-owner retirement.

Custody, manual disposition and rollback rejection are covered by the shared
Main-only retirement regressions, including Doosan. Deleted transition workers
must not be recreated to satisfy historical migration tests.
"""

import asyncio
from copy import deepcopy
import importlib.util
import json
from types import SimpleNamespace

import pytest

from src.engine.scalping import main_fixed_watch as fixed
from src.trading.config import owner_retirement as retired
from src.tests.test_main_fixed_watch import _TestDB, epoch


def test_two_fixed_watches_have_separate_admissions_and_two_reserved_slots(monkeypatch):
    for spec in fixed.SPECS[:2]:
        monkeypatch.setenv(spec.enable_env, "true")
    monkeypatch.setattr(
        fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat")
    )
    db, targets = _TestDB(), []
    for spec in fixed.SPECS[:2]:
        assert (
            fixed.reconcile(
                db, targets, now_epoch=epoch(10), watch_cap=2, symbol=spec.symbol
            )[0]
            == "armed"
        )
    assert fixed.reserved_slots() == 2
    assert (
        len({t["id"] for t in targets})
        == len({t["watch_admission_id"] for t in targets})
        == 2
    )
    assert len({t["watch_generation_id"] for t in targets}) == 2
    assert targets[1]["initial_policy_scope"] == "non_samsung"
    samsung = deepcopy(targets[0])
    assert (
        fixed.reconcile(db, targets, now_epoch=epoch(16), watch_cap=2, symbol="034020")[
            0
        ]
        == "armed"
    )
    assert targets[0] == samsung


def test_al_observation_adoption_waits_for_new_real_packets(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager

    manager = KiwoomWSManager("test-token")
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    monkeypatch.setattr(
        manager, "_observe_micro_reversion_forward", lambda *a, **k: None
    )
    manager.websocket = SimpleNamespace()
    manager._session_ready.set()
    manager._market_data_transport_epoch = 3
    manager.subscribed_codes.add("034020")
    manager._registered_items_by_code["034020"] = ("034020_AL", "034020_NX")
    manager._registered_item_epochs["034020_AL"] = 3
    manager._registered_item_types["034020_AL"] = {"0B", "0D"}
    manager._micro_reversion_observation_only_items.update({"034020_AL", "034020_NX"})
    manager._micro_reversion_observation_only_codes.add("034020")
    old = manager._ensure_target_defaults(
        "034020_AL", store=manager._micro_reversion_observation_route_data
    )
    old["curr"] = 99999
    now = epoch(10)
    route = fixed.session_route(now, "034020")
    target = dict(
        code="034020",
        status="WATCHING",
        watch_origin=fixed.WATCH_ORIGIN,
        watch_generation_id=fixed.generation_id(now, route),
        watch_admission_id="native",
        entry_armed_at_epoch=now,
    )
    assert manager.adopt_main_fixed_watch_target(target, now_ts=now)
    assert manager.get_latest_data("034020").get("curr", 0) == 0
    assert "034020_NX" in manager._micro_reversion_observation_only_items
    assert "034020_AL" not in manager._micro_reversion_observation_only_items
    asyncio.run(
        manager._handle_message(
            json.dumps(
                dict(
                    trnm="REAL",
                    data=[
                        dict(
                            type="0B",
                            item="034020_AL",
                            values={"10": "10000", "15": "+1", "228": "101.5"},
                        )
                    ],
                )
            )
        )
    )
    assert manager.get_latest_data("034020")["curr"] == 10000
    manager._registered_item_epochs["034020_AL"] = 2
    assert not manager.adopt_main_fixed_watch_target(target, now_ts=now)


def test_fixed_reg_preserves_other_exact_observation_item(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.tests.test_kiwoom_websocket import _FakeWS

    manager = KiwoomWSManager("test-token")
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    monkeypatch.setattr(
        manager, "_observe_micro_reversion_forward", lambda *a, **k: None
    )
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._registered_items_by_code["034020"] = ("034020_NX",)
    manager._micro_reversion_observation_only_items.add("034020_NX")
    asyncio.run(
        manager._send_reg(
            ["034020_AL"],
            source="main_fixed_watch_admission",
            realtime_types=("0B", "0D"),
            replace_existing=False,
            remove_before_reg=False,
        )
    )
    assert all(
        json.loads(packet)["trnm"] != "REMOVE" for packet in manager.websocket.sent
    )
    assert set(manager._registered_items_by_code["034020"]) == {
        "034020_NX",
        "034020_AL",
    }
    assert "034020_NX" in manager._micro_reversion_observation_only_items
    assert manager._runtime_primary_items_by_code["034020"] == "034020_AL"


@pytest.mark.parametrize("symbol", ["034020", "A034020", "034020_AL", "034020_NX"])
def test_retired_symbol_aliases_keep_only_main_and_manual_owners(symbol):
    assert retired.new_entry_retired(symbol, "episode")
    assert not retired.new_entry_retired(symbol, "main_scalping")
    with pytest.raises(ValueError, match="symbol_owner_permanently_retired"):
        retired.require_new_entry_owner(symbol, "episode")
    assert retired.main_manual_after_episode_retirement(
        symbol, ["main_scalping", "manual_operator"]
    )


@pytest.mark.parametrize(
    "module",
    [
        "src.trading.low_price_two_leg",
        "src.engine.automation.owner_retirement_transition",
        "src.engine.monitoring.research_source_facts",
    ],
)
def test_removed_automatic_execution_and_transition_owners_stay_absent(module):
    assert importlib.util.find_spec(module) is None
