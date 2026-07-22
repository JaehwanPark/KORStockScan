from datetime import datetime

from src.engine import kiwoom_sniper_v2
from src.engine.scalping.watch_budget import (
    GENERAL_SCALPING,
    OPENING_ROTATION,
    RISING_MISSED,
    classify_owner,
    limits,
    owner_allowances,
    slot_type,
)


def _watch_target(code, owner, armed_epoch):
    return {
        "id": code,
        "code": code,
        "name": code,
        "strategy": "SCALPING",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": armed_epoch,
        "scanner_watch_budget_owner": owner,
    }


def test_watch_budget_classifies_opening_rising_and_general():
    opening_now = datetime(2026, 7, 22, 9, 30)

    assert (
        classify_owner(
            source_signature="PRICE_JUMP_START",
            day_change_pct=3.0,
            now_dt=opening_now,
        )
        == OPENING_ROTATION
    )
    assert (
        classify_owner(
            source_signature="LOW_REBOUND_RISING_MISSED",
            day_change_pct=3.0,
            now_dt=opening_now,
        )
        == RISING_MISSED
    )
    assert (
        classify_owner(
            source_signature="SUPERNOVA",
            day_change_pct=3.0,
            now_dt=opening_now,
        )
        == GENERAL_SCALPING
    )


def test_watch_budget_limits_are_general1_opening3_rising12_with_borrow_to15():
    policy = limits(16, opening_window_active=True)

    assert policy.general_max == 1
    assert policy.opening_protected == 3
    assert policy.rising_guaranteed == 12
    assert policy.rising_max_with_borrow == 15
    assert (
        owner_allowances(
            {GENERAL_SCALPING: 1, OPENING_ROTATION: 1, RISING_MISSED: 14},
            total=16,
            opening_window_active=True,
        )[RISING_MISSED]
        == 14
    )
    assert (
        slot_type(
            RISING_MISSED,
            13,
            total=16,
            opening_window_active=True,
        )
        == "borrowed_opening_slot"
    )


def test_runtime_budget_reclaims_borrowed_rising_slot_for_opening(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "_scalping_fifo_max_active", lambda: 16)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_scalping_watch_budget_reallocation_enabled",
        lambda: True,
    )
    now_ts = datetime(2026, 7, 22, 10, 0).timestamp()
    targets = [_watch_target("G00001", GENERAL_SCALPING, 1.0)]
    targets.extend(
        _watch_target(f"O{index:05d}", OPENING_ROTATION, 10.0 + index)
        for index in range(2)
    )
    targets.extend(
        _watch_target(f"R{index:05d}", RISING_MISSED, 20.0 + index)
        for index in range(13)
    )

    assert (
        kiwoom_sniper_v2._scalping_watch_budget_overflow_candidates(targets, now_ts)
        == []
    )

    targets.append(_watch_target("O99999", OPENING_ROTATION, 99.0))
    overflow = kiwoom_sniper_v2._scalping_watch_budget_overflow_candidates(
        targets, now_ts
    )

    assert len(overflow) == 1
    assert overflow[0]["scanner_watch_budget_owner"] == RISING_MISSED


def test_runtime_budget_limits_general_even_below_total_cap(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "_scalping_fifo_max_active", lambda: 16)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_scalping_watch_budget_reallocation_enabled",
        lambda: True,
    )
    now_ts = datetime(2026, 7, 22, 10, 0).timestamp()
    targets = [
        _watch_target("G00001", GENERAL_SCALPING, 1.0),
        _watch_target("G00002", GENERAL_SCALPING, 2.0),
        _watch_target("R00001", RISING_MISSED, 3.0),
    ]

    overflow = kiwoom_sniper_v2._scalping_watch_budget_overflow_candidates(
        targets, now_ts
    )

    assert len(overflow) == 1
    assert overflow[0]["scanner_watch_budget_owner"] == GENERAL_SCALPING


def test_runtime_queue_orders_opening_then_rising_then_general():
    now_ts = datetime(2026, 7, 22, 10, 0).timestamp()
    targets = [
        _watch_target("G00001", GENERAL_SCALPING, 1.0),
        _watch_target("R00001", RISING_MISSED, 1.0),
        _watch_target("O00001", OPENING_ROTATION, 1.0),
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts)

    assert [target["code"] for target in ordered] == ["O00001", "R00001", "G00001"]


def test_runtime_queue_rollback_disables_owner_reordering(monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_scalping_watch_budget_reallocation_enabled",
        lambda: False,
    )
    now_ts = datetime(2026, 7, 22, 10, 0).timestamp()
    targets = [
        _watch_target("G00001", GENERAL_SCALPING, 1.0),
        _watch_target("R00001", RISING_MISSED, 1.0),
        _watch_target("O00001", OPENING_ROTATION, 1.0),
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts)

    assert [target["code"] for target in ordered] == ["G00001", "R00001", "O00001"]


def test_budget_expiration_keeps_ws_when_same_symbol_is_still_active(monkeypatch):
    published = []
    expired = _watch_target("000001", RISING_MISSED, 1.0)
    expired["id"] = None
    holding = {
        "id": "holding",
        "code": "000001",
        "name": "HOLDING",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "position_tag": "SCALP_BASE",
    }
    active = [expired, holding]
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        type(
            "Bus",
            (),
            {"publish": lambda _self, name, payload: published.append((name, payload))},
        )(),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2, "emit_pipeline_event", lambda *args, **kwargs: None
    )

    kiwoom_sniper_v2._expire_scalping_watch_budget_targets(
        [expired],
        active,
        reason="test_reallocation",
    )

    assert active == [holding]
    assert published == []
