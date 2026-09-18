from datetime import datetime

from src.engine import kiwoom_sniper_v2
from src.engine.scalping.watch_budget import (
    GENERAL_SCALPING,
    OPENING_ROTATION,
    RISING_MISSED,
    classify_owner,
    limits,
    owner_allowances,
    rising_source_reservation,
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
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }


def test_watch_budget_never_classifies_retired_opening_owner():
    opening_now = datetime(2026, 7, 22, 9, 30)

    assert (
        classify_owner(
            source_signature="PRICE_JUMP_START",
            day_change_pct=3.0,
            now_dt=opening_now,
            effective_venue="KRX",
            market_session_bucket="krx_regular",
        )
        == RISING_MISSED
    )
    assert (
        classify_owner(
            source_signature="LOW_REBOUND_RISING_MISSED",
            day_change_pct=3.0,
            now_dt=opening_now,
            effective_venue="KRX",
            market_session_bucket="krx_regular",
        )
        == GENERAL_SCALPING
    )
    assert (
        classify_owner(
            source_signature="SUPERNOVA",
            day_change_pct=0.0,
            now_dt=opening_now,
        )
        == GENERAL_SCALPING
    )
    assert (
        classify_owner(
            source_signature="PRICE_JUMP_START",
            day_change_pct=3.0,
            now_dt=opening_now,
            effective_venue="NXT",
            market_session_bucket="nxt",
        )
        == RISING_MISSED
    )


def test_watch_budget_limits_release_retired_opening_capacity_to_rising():
    policy = limits(16, opening_window_active=True)

    assert policy.general_max == 1
    assert policy.opening_protected == 0
    assert policy.rising_guaranteed == 15
    assert policy.rising_max_with_borrow == 15
    assert (
        owner_allowances(
            {GENERAL_SCALPING: 1, OPENING_ROTATION: 1, RISING_MISSED: 14},
            total=16,
            opening_window_active=True,
        )[RISING_MISSED]
        == 15
    )
    assert (
        slot_type(
            RISING_MISSED,
            14,
            total=16,
            opening_window_active=True,
        )
        == "guaranteed"
    )




def test_retired_limit_down_env_does_not_reserve_runtime_capacity(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "true")
    policy = limits(16, opening_window_active=True)
    assert policy.general_max == 1
    assert policy.rising_guaranteed == 15
    fields = kiwoom_sniper_v2._scalping_watch_budget_policy_fields([], datetime(2026, 9, 21, 10).timestamp())
    assert "limit_down_rotation" not in fields["scanner_watch_budget_owner_counts"]


def test_market_gainer_reservation_is_six_inside_rising_guaranteed_budget():
    assert (
        rising_source_reservation(
            16,
            requested_slots=6,
            opening_window_active=True,

        )
        == 6
    )
    assert (
        rising_source_reservation(
            3,
            requested_slots=6,
            opening_window_active=True,

        )
        == 3
    )




def test_runtime_budget_reclassifies_retired_opening_owner(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "_scalping_fifo_max_active", lambda: 16)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_scalping_watch_budget_reallocation_enabled",
        lambda: True,
    )
    now_ts = datetime(2026, 7, 22, 10, 0).timestamp()
    retired = _watch_target("O99999", OPENING_ROTATION, 99.0)
    assert (
        kiwoom_sniper_v2._scalping_watch_budget_owner(retired, now_ts=now_ts)
        == RISING_MISSED
    )
    fields = kiwoom_sniper_v2._scalping_watch_budget_policy_fields([retired], now_ts)
    assert fields["scanner_watch_budget_opening_protected"] == 0
    assert fields["scanner_watch_budget_owner_counts"][OPENING_ROTATION] == 0


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


def test_runtime_queue_treats_retired_opening_owner_as_rising():
    now_ts = datetime(2026, 7, 22, 10, 0).timestamp()
    targets = [
        _watch_target("G00001", GENERAL_SCALPING, 1.0),
        _watch_target("R00001", RISING_MISSED, 1.0),
        _watch_target("O00001", OPENING_ROTATION, 1.0),
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts)

    assert [target["code"] for target in ordered] == ["R00001", "O00001", "G00001"]


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
