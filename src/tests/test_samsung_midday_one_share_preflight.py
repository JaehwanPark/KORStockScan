from __future__ import annotations

import json
from datetime import date, datetime

import pytest

from src.trading.samsung_midday_one_share.machine import KST
from src.trading.samsung_midday_one_share.preflight import (
    build_authority_artifact,
    evaluate_preflight,
    validate_authority,
)


def _ready():
    return evaluate_preflight(
        target_date=date(2026, 8, 12),
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
    )


def test_preflight_keeps_morning_afternoon_widget_and_midday_independent():
    decision = _ready()
    assert decision.ready is True
    assert decision.morning_parallel_independent is True
    assert decision.afternoon_parallel_independent is True
    assert decision.widget_parallel_independent is True
    assert decision.independent_order_ledger_required is True


@pytest.mark.parametrize(
    ("change", "blocker"),
    [
        ({"main_bot_active": False}, "main_bot_inactive"),
        ({"shared_token_available": False}, "shared_token_unavailable"),
        ({"operator_exclusion_source": ""}, "manual_operator_exclusion_missing"),
    ],
)
def test_preflight_fails_closed(change, blocker):
    values = {
        "target_date": date(2026, 8, 12),
        "main_bot_active": True,
        "shared_token_available": True,
        "operator_exclusion_source": "manual_operator",
    }
    values.update(change)
    assert blocker in evaluate_preflight(**values).blockers


def test_authority_exactly_preserves_no_stop_and_sor_contract(tmp_path):
    now = datetime(2026, 8, 12, 13, 12, tzinfo=KST)
    artifact = build_authority_artifact(_ready(), observed_at=now)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    assert validate_authority(path, now=now) == (True, "ready")
    assert artifact["policy"]["market"] == "SOR_regular_integrated"
    assert artifact["policy"]["scan"] == (
        "completed_1m_bars_13:15_through_13:54_13:55_exclusive"
    )
    assert artifact["policy"]["stop_loss"] == "none"
    assert artifact["policy"]["unfilled_target"] == "hold_position_without_forced_exit"
    assert artifact["rollback"]["morning_service_effect"] == "none"
    assert artifact["rollback"]["afternoon_service_effect"] == "none"
    assert artifact["rollback"]["widget_service_effect"] == "none"


def test_authority_uses_target3_after_operator_override(tmp_path):
    now = datetime(2026, 8, 14, 13, 12, tzinfo=KST)
    decision = evaluate_preflight(
        target_date=now.date(),
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
    )
    artifact = build_authority_artifact(decision, observed_at=now)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert artifact["policy"]["target"] == "fill_plus_3_ticks"
    assert artifact["policy"]["operator_target_override"]["before"] == 2
    assert artifact["policy"]["operator_target_override"]["after"] == 3
    assert validate_authority(path, now=now) == (True, "ready")


@pytest.mark.parametrize(
    "change",
    [
        {"symbol": "000660"},
        {"quantity": 3},
        {"allocation": "two_shares_at_signal_close"},
        {"market": "NXT_regular_separate"},
        {"entry": "best_bid"},
        {"stop_loss": "minus_2_ticks"},
        {"unfilled_target": "forced_best_sell"},
        {"morning_relationship": "shared_position"},
        {"afternoon_relationship": "shared_position"},
        {"widget_relationship": "shared_position"},
    ],
)
def test_authority_rejects_route_entry_or_forced_exit_tamper(tmp_path, change):
    now = datetime(2026, 8, 12, 13, 12, tzinfo=KST)
    artifact = build_authority_artifact(_ready(), observed_at=now)
    artifact["policy"].update(change)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    assert validate_authority(path, now=now) == (False, "authority_policy_mismatch")


def test_authority_rejects_timeout_field_even_if_other_policy_matches(tmp_path):
    now = datetime(2026, 8, 12, 13, 12, tzinfo=KST)
    artifact = build_authority_artifact(_ready(), observed_at=now)
    artifact["policy"]["max_hold_minutes"] = 12
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    assert validate_authority(path, now=now) == (
        False,
        "authority_forced_exit_policy_forbidden",
    )
