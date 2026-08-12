from __future__ import annotations

import json
from datetime import date, datetime

import pytest

from src.trading.samsung_morning_one_share.machine import KST
from src.trading.samsung_morning_one_share.preflight import (
    build_authority_artifact,
    evaluate_preflight,
    validate_authority,
)


def _ready_decision():
    return evaluate_preflight(
        target_date=date(2026, 8, 12),
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
    )


def test_preflight_allows_parallel_widget_with_independent_ledgers():
    decision = _ready_decision()
    assert decision.ready is True
    assert decision.parallel_widget_trading_allowed is True
    assert decision.independent_order_ledger_required is True
    assert decision.prior_reentry_state_clear is True
    assert decision.blockers == ()


@pytest.mark.parametrize(
    ("overrides", "blocker"),
    [
        ({"main_bot_active": False}, "main_bot_inactive"),
        ({"shared_token_available": False}, "shared_token_unavailable"),
        ({"operator_exclusion_source": ""}, "manual_operator_exclusion_missing"),
        (
            {"prior_reentry_state_clear": False},
            "prior_reentry_order_or_position_unresolved",
        ),
    ],
)
def test_preflight_fails_closed_when_required_contract_is_missing(overrides, blocker):
    inputs = {
        "target_date": date(2026, 8, 12),
        "main_bot_active": True,
        "shared_token_available": True,
        "operator_exclusion_source": "manual_operator",
    }
    inputs.update(overrides)
    decision = evaluate_preflight(**inputs)
    assert decision.ready is False
    assert blocker in decision.blockers


def test_authority_artifact_is_same_day_and_never_controls_widget(tmp_path):
    observed_at = datetime(2026, 8, 12, 7, 57, tzinfo=KST)
    artifact = build_authority_artifact(_ready_decision(), observed_at=observed_at)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert validate_authority(path, now=observed_at) == (True, "ready")
    assert artifact["rollback"]["widget_service_effect"] == "none"
    assert artifact["policy"]["widget_relationship"] == (
        "parallel_independent_strategy"
    )
    assert artifact["policy"]["sor_regular_fallback"] == (
        "each_unfilled_leg_from_09:00_open_until_09:30"
    )
    assert artifact["policy"]["unfilled_target"] == (
        "hold_position_without_forced_exit"
    )
    assert artifact["policy"]["maximum_episodes_per_day"] == 2
    assert artifact["policy"]["sor_reentry_prerequisite"] == (
        "both_opening_episode_legs_complete"
    )
    assert artifact["policy"]["sor_reentry_validity"] == "three_completed_bars"
    assert "max_hold_minutes" not in artifact["policy"]
    assert (
        "use_widget_orders_or_positions_as_morning_machine_ledger"
        in artifact["forbidden_uses"]
    )
    assert "timeout_target_cancel_or_forced_exit" in artifact["forbidden_uses"]


def test_authority_rejects_other_trade_date(tmp_path):
    artifact = build_authority_artifact(
        _ready_decision(),
        observed_at=datetime(2026, 8, 12, 7, 57, tzinfo=KST),
    )
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    assert validate_authority(path, now=datetime(2026, 8, 13, 7, 57, tzinfo=KST)) == (
        False,
        "authority_target_date_mismatch",
    )


@pytest.mark.parametrize(
    ("policy_change", "reason"),
    [
        ({"sor_regular_fallback": "09:00_krx_only"}, "authority_sor_policy_mismatch"),
        ({"unfilled_target": "best_sell_after_12m"}, "authority_hold_policy_mismatch"),
        ({"max_hold_minutes": 12}, "authority_timeout_policy_forbidden"),
        ({"maximum_episodes_per_day": 3}, "authority_sor_policy_mismatch"),
        (
            {"sor_reentry_validity": "five_completed_bars"},
            "authority_sor_policy_mismatch",
        ),
    ],
)
def test_authority_rejects_stale_or_forced_exit_policy(tmp_path, policy_change, reason):
    now = datetime(2026, 8, 12, 7, 57, tzinfo=KST)
    artifact = build_authority_artifact(_ready_decision(), observed_at=now)
    artifact["policy"].update(policy_change)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    assert validate_authority(path, now=now) == (False, reason)
