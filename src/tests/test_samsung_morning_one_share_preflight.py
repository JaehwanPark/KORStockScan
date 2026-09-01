from __future__ import annotations

import json
import argparse
from datetime import date, datetime

import pytest

from src.trading.samsung_morning_one_share import preflight as preflight_module
from src.trading.samsung_morning_one_share.machine import KST
from src.trading.samsung_morning_one_share.preflight import (
    _authority_deadline_elapsed,
    _is_bot_main_pid,
    _parse_hhmmss,
    build_authority_artifact,
    evaluate_preflight,
    validate_authority,
)


def _ready_decision():
    return evaluate_preflight(
        target_date=date(2026, 8, 12),
        main_bot_active=True,
        main_bot_pid=12345,
        main_bot_runtime_env_verified=True,
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
        ({"main_bot_pid": 0}, "main_bot_pid_missing"),
        (
            {"main_bot_runtime_env_verified": False},
            "main_bot_runtime_env_unverified",
        ),
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
        "main_bot_pid": 12345,
        "main_bot_runtime_env_verified": True,
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
    assert artifact["rollback"]["action"] == (
        "fail_closed_and_disable_only_morning_two_leg_timer_and_services"
    )


def test_authority_builder_requires_timezone_aware_observation():
    with pytest.raises(ValueError, match="preflight_observed_at_timezone_missing"):
        build_authority_artifact(
            _ready_decision(),
            observed_at=datetime(2026, 8, 12, 7, 57),
        )


def test_authority_builder_rejects_target_date_different_from_observation_date():
    decision = evaluate_preflight(
        target_date=date(2026, 8, 11),
        main_bot_active=True,
        main_bot_pid=12345,
        main_bot_runtime_env_verified=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
    )

    with pytest.raises(ValueError, match="preflight_target_date_not_observed_date"):
        build_authority_artifact(
            decision,
            observed_at=datetime(2026, 8, 12, 7, 57, tzinfo=KST),
        )


def test_authority_uses_target3_after_operator_override(tmp_path):
    now = datetime(2026, 8, 14, 9, 22, tzinfo=KST)
    decision = evaluate_preflight(
        target_date=now.date(),
        main_bot_active=True,
        main_bot_pid=12345,
        main_bot_runtime_env_verified=True,
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
    ("observed_at_change", "reason"),
    [
        ("invalid", "authority_observed_at_invalid"),
        ("2026-08-11T07:57:00+09:00", "authority_observed_target_date_mismatch"),
        ("2026-08-12T08:00:00+09:00", "authority_observed_in_future"),
    ],
)
def test_authority_rejects_invalid_or_future_observation_time(
    tmp_path, observed_at_change, reason
):
    now = datetime(2026, 8, 12, 7, 58, tzinfo=KST)
    artifact = build_authority_artifact(
        _ready_decision(),
        observed_at=datetime(2026, 8, 12, 7, 57, tzinfo=KST),
    )
    artifact["observed_at_kst"] = observed_at_change
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert validate_authority(path, now=now) == (False, reason)


@pytest.mark.parametrize(
    "artifact_change",
    [
        {"decision_authority": "report_only"},
        {"source_quality_gate": "FAIL"},
        {"runtime_effect": False},
        {"actual_order_submitted": True},
        {"broker_order_forbidden": True},
    ],
)
def test_authority_rejects_runtime_contract_drift(tmp_path, artifact_change):
    observed_at = datetime(2026, 8, 12, 7, 57, tzinfo=KST)
    artifact = build_authority_artifact(_ready_decision(), observed_at=observed_at)
    artifact.update(artifact_change)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert validate_authority(path, now=observed_at) == (
        False,
        "authority_runtime_contract_mismatch",
    )


def test_authority_rejects_rollback_contract_drift(tmp_path):
    observed_at = datetime(2026, 8, 12, 7, 57, tzinfo=KST)
    artifact = build_authority_artifact(_ready_decision(), observed_at=observed_at)
    artifact["rollback"]["widget_service_effect"] = "stop_widget"
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert validate_authority(path, now=observed_at) == (
        False,
        "authority_rollback_contract_mismatch",
    )


@pytest.mark.parametrize(
    ("decision_change", "reason"),
    [
        ({"target_date": "2026-08-11"}, "authority_decision_target_date_mismatch"),
        ({"main_bot_active": False}, "authority_main_bot_inactive"),
        ({"main_bot_pid": 0}, "authority_main_bot_pid_missing"),
        (
            {"main_bot_runtime_env_verified": False},
            "authority_main_bot_runtime_env_unverified",
        ),
        ({"shared_token_available": False}, "authority_shared_token_unavailable"),
        (
            {"operator_exclusion_source": ""},
            "authority_manual_operator_exclusion_missing",
        ),
        ({"blockers": ["main_bot_inactive"]}, "authority_decision_blockers_present"),
    ],
)
def test_authority_rejects_unbound_main_bot_runtime(tmp_path, decision_change, reason):
    artifact = build_authority_artifact(
        _ready_decision(),
        observed_at=datetime(2026, 8, 12, 7, 57, tzinfo=KST),
    )
    artifact["decision"].update(decision_change)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert validate_authority(path, now=datetime(2026, 8, 12, 7, 58, tzinfo=KST)) == (
        False,
        reason,
    )


def test_authority_rechecks_bound_pid_before_live_service_start(monkeypatch, tmp_path):
    artifact = build_authority_artifact(
        _ready_decision(),
        observed_at=datetime(2026, 8, 12, 7, 57, tzinfo=KST),
    )
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(preflight_module, "_is_bot_main_pid", lambda pid: True)
    monkeypatch.setattr(
        preflight_module,
        "verify_runtime_env_handoff",
        lambda target_date, pid=None: {
            "status": "fail",
            "pid": pid,
            "findings": ["pid_dead"],
        },
    )

    assert validate_authority(
        path,
        now=datetime(2026, 8, 12, 7, 58, tzinfo=KST),
        require_live_main_bot_runtime=True,
    ) == (False, "authority_main_bot_runtime_env_unverified")


def test_authority_accepts_live_service_only_after_bound_pid_recheck(
    monkeypatch, tmp_path
):
    artifact = build_authority_artifact(
        _ready_decision(),
        observed_at=datetime(2026, 8, 12, 7, 57, tzinfo=KST),
    )
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(preflight_module, "_is_bot_main_pid", lambda pid: True)
    monkeypatch.setattr(
        preflight_module,
        "verify_runtime_env_handoff",
        lambda target_date, pid=None: {
            "status": "pass",
            "pid": pid,
            "findings": [],
        },
    )

    assert validate_authority(
        path,
        now=datetime(2026, 8, 12, 7, 58, tzinfo=KST),
        require_live_main_bot_runtime=True,
    ) == (True, "ready")


def test_bot_main_pid_identity_requires_exact_cmdline_token(tmp_path):
    proc_root = tmp_path / "proc"
    exact = proc_root / "123"
    misleading = proc_root / "456"
    exact.mkdir(parents=True)
    misleading.mkdir(parents=True)
    (exact / "cmdline").write_bytes(b"/venv/bin/python\0bot_main.py\0")
    (misleading / "cmdline").write_bytes(
        b"/bin/bash\0-c\0pgrep -f python bot_main.py\0"
    )

    assert _is_bot_main_pid(123, proc_root=proc_root) is True
    assert _is_bot_main_pid(456, proc_root=proc_root) is False
    assert _is_bot_main_pid(789, proc_root=proc_root) is False


def test_authority_deadline_is_inclusive_and_kst_bounded():
    deadline = _parse_hhmmss("09:25:00")

    assert not _authority_deadline_elapsed(
        deadline,
        now=datetime.fromisoformat("2026-09-02T09:24:59+09:00"),
    )
    assert _authority_deadline_elapsed(
        deadline,
        now=datetime.fromisoformat("2026-09-02T09:25:00+09:00"),
    )


@pytest.mark.parametrize("value", ["25:00:00", "09:25:00.100000", "09:25"])
def test_authority_deadline_parser_rejects_non_contract_values(value):
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_hhmmss(value)


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


def test_main_derives_runtime_verification_from_exact_bot_pid(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    target_date = datetime.now(tz=KST).date().isoformat()
    verify_calls = []
    monkeypatch.setattr(
        preflight_module,
        "verify_runtime_env_handoff",
        lambda target_date, pid=None: verify_calls.append((target_date, pid))
        or {"status": "pass", "pid": pid, "findings": []},
    )
    monkeypatch.setattr(preflight_module, "_is_bot_main_pid", lambda pid: True)
    monkeypatch.setattr(
        preflight_module.kiwoom_utils,
        "get_cached_kiwoom_token",
        lambda: "cached-token",
    )
    monkeypatch.setattr(
        preflight_module,
        "manual_control_operator_exclusion_source",
        lambda symbol: "manual_operator",
    )
    monkeypatch.setattr(
        preflight_module,
        "prior_reentry_allows_new_first_episode",
        lambda path, target_date: (True, "clear"),
    )

    result = preflight_module.main(
        [
            "--target-date",
            target_date,
            "--authority-path",
            str(authority_path),
            "--main-bot-active",
            "--main-bot-pid",
            "24680",
            "--write",
        ]
    )

    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    assert result == 0
    assert verify_calls == [(target_date, 24680)]
    assert payload["decision"]["main_bot_pid"] == 24680
    assert payload["decision"]["main_bot_runtime_env_verified"] is True


def test_main_does_not_trust_active_pid_when_runtime_verification_fails(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    target_date = datetime.now(tz=KST).date().isoformat()
    monkeypatch.setattr(
        preflight_module,
        "verify_runtime_env_handoff",
        lambda target_date, pid=None: {
            "status": "fail",
            "pid": pid,
            "findings": ["pid_env_mismatch"],
        },
    )
    monkeypatch.setattr(preflight_module, "_is_bot_main_pid", lambda pid: True)
    monkeypatch.setattr(
        preflight_module.kiwoom_utils,
        "get_cached_kiwoom_token",
        lambda: "cached-token",
    )
    monkeypatch.setattr(
        preflight_module,
        "manual_control_operator_exclusion_source",
        lambda symbol: "manual_operator",
    )
    monkeypatch.setattr(
        preflight_module,
        "prior_reentry_allows_new_first_episode",
        lambda path, target_date: (True, "clear"),
    )

    result = preflight_module.main(
        [
            "--target-date",
            target_date,
            "--authority-path",
            str(authority_path),
            "--main-bot-active",
            "--main-bot-pid",
            "24680",
            "--write",
        ]
    )

    assert result == 2
    assert not authority_path.exists()


def test_main_rejects_non_current_target_date_before_authority_checks(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    observed_date = datetime.now(tz=KST).date()
    target_date = date.fromordinal(observed_date.toordinal() + 1).isoformat()
    monkeypatch.setattr(
        preflight_module,
        "prior_reentry_allows_new_first_episode",
        lambda *args, **kwargs: pytest.fail("future authority reached source checks"),
    )

    result = preflight_module.main(
        [
            "--target-date",
            target_date,
            "--authority-path",
            str(authority_path),
            "--main-bot-active",
            "--main-bot-pid",
            "24680",
            "--write",
        ]
    )

    assert result == 2
    assert not authority_path.exists()


def test_main_rejects_non_trading_day_before_authority_checks(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    target_date = datetime.now(tz=KST).date().isoformat()
    monkeypatch.setattr(
        preflight_module,
        "get_krx_trading_day_status",
        lambda value: (False, "holiday:test"),
    )
    monkeypatch.setattr(
        preflight_module,
        "prior_reentry_allows_new_first_episode",
        lambda *args, **kwargs: pytest.fail("holiday reached authority source checks"),
    )

    result = preflight_module.main(
        [
            "--target-date",
            target_date,
            "--authority-path",
            str(authority_path),
            "--main-bot-active",
            "--main-bot-pid",
            "24680",
            "--write",
        ]
    )

    assert result == 2
    assert not authority_path.exists()
