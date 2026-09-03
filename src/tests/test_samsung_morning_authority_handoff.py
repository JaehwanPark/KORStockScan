from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.trading.samsung_morning_one_share import authority_handoff as handoff
from src.trading.samsung_morning_one_share import preflight as preflight_module
from src.trading.samsung_morning_one_share.preflight import (
    build_authority_artifact,
    evaluate_preflight,
)
from src.trading.samsung_morning_one_share.machine import KST


NOW = datetime(2026, 9, 3, 10, 15, tzinfo=KST)
OLD_PID = 10101
NEW_PID = 20202
SERVICE_PID = 30303


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _ready_authority(path: Path) -> dict:
    decision = evaluate_preflight(
        target_date=NOW.date(),
        main_bot_active=True,
        main_bot_pid=OLD_PID,
        main_bot_runtime_env_verified=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
    )
    artifact = build_authority_artifact(
        decision,
        observed_at=NOW.replace(hour=7, minute=57),
    )
    _write_json(path, artifact)
    return artifact


def _state(path: Path, *, status: str = "TARGET_OPEN") -> None:
    payload = {
        "schema": "samsung_morning_two_leg_state_v2",
        "trade_date": NOW.date().isoformat(),
        "status": status,
        "position_qty": 20 if status == "TARGET_OPEN" else 0,
        "legs": [],
    }
    if status == "TARGET_OPEN":
        payload["legs"] = [
            {
                "leg_id": "base_plus_1tick",
                "status": "TARGET_OPEN",
                "quantity": 10,
                "position_qty": 10,
                "buy_order_no": "0000001",
                "target_order_no": "0000003",
                "buy_filled_at": "2026-09-03T09:10:00+09:00",
            },
            {
                "leg_id": "base",
                "status": "TARGET_OPEN",
                "quantity": 10,
                "position_qty": 10,
                "buy_order_no": "0000002",
                "target_order_no": "0000004",
                "buy_filled_at": "2026-09-03T09:11:00+09:00",
            },
        ]
    _write_json(path, payload)


def _live_state(pid: int = SERVICE_PID) -> dict:
    return {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "MainPID": pid,
        "Result": "success",
    }


@pytest.fixture
def handoff_paths(tmp_path, monkeypatch):
    authority_path = tmp_path / "authority.json"
    plan_path = tmp_path / "plan.json"
    first_state = tmp_path / "first_state.json"
    reentry_state = tmp_path / "reentry_state.json"
    verify_path = tmp_path / "verify.json"
    _ready_authority(authority_path)
    _state(first_state)
    _write_json(
        reentry_state,
        {
            "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
            "trade_date": "2026-09-02",
            "status": "NO_TRADE",
            "position_qty": 0,
            "legs": [],
        },
    )
    verification = {
        "status": "pass",
        "passed": True,
        "pid": OLD_PID,
        "pid_passed": True,
        "pid_env_available": True,
        "pid_missing": [],
        "findings": [],
        "pid_mismatches": [],
        "runtime_policy_fail_count": 0,
        "dated_runtime_override_fail_count": 0,
        "unverified_selected_family_count": 0,
    }
    _write_json(verify_path, verification)
    monkeypatch.setattr(handoff, "DEFAULT_STATE_PATH", first_state)
    monkeypatch.setattr(handoff, "DEFAULT_REENTRY_STATE_PATH", reentry_state)
    monkeypatch.setattr(
        handoff, "_runtime_verify_artifact_path", lambda _date: verify_path
    )
    monkeypatch.setattr(
        handoff,
        "verify_runtime_env_handoff",
        lambda target_date, pid=None: {**verification, "pid": pid},
    )
    monkeypatch.setattr(
        preflight_module,
        "verify_runtime_env_handoff",
        lambda target_date, pid=None: {"status": "pass", "pid": pid},
    )
    monkeypatch.setattr(
        handoff,
        "_is_samsung_live_service_pid",
        lambda pid, **kwargs: pid == SERVICE_PID,
    )
    monkeypatch.setattr(
        preflight_module,
        "_is_bot_main_pid",
        lambda pid, **kwargs: pid in {OLD_PID, NEW_PID},
    )
    live_pids = {OLD_PID, NEW_PID}
    monkeypatch.setattr(
        handoff,
        "_is_bot_main_pid",
        lambda pid, **kwargs: pid in live_pids,
    )
    return {
        "authority": authority_path,
        "plan": plan_path,
        "first_state": first_state,
        "reentry_state": reentry_state,
        "verify": verify_path,
        "verification": verification,
        "live_pids": live_pids,
    }


def test_prepared_handoff_changes_only_pid_and_appends_audited_continuity(
    handoff_paths, monkeypatch
):
    authority_path = handoff_paths["authority"]
    plan_path = handoff_paths["plan"]
    before = json.loads(authority_path.read_text(encoding="utf-8"))
    before_hash = handoff._sha256_file(authority_path)

    prepared, prepare_rc = handoff.prepare_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW,
        authority_path=authority_path,
        plan_path=plan_path,
        live_state=_live_state(),
    )

    assert prepare_rc == 0
    assert prepared["status"] == "prepared"
    assert prepared["plan"]["authority_sha256_before"] == before_hash
    assert prepared["plan"]["new_order_authority_created"] is False
    assert plan_path.exists()

    handoff_paths["live_pids"].remove(OLD_PID)
    handoff_paths["verification"]["pid"] = NEW_PID
    _write_json(handoff_paths["verify"], handoff_paths["verification"])
    committed, commit_rc = handoff.commit_main_bot_handoff(
        new_main_bot_pid=NEW_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW + timedelta(seconds=30),
        authority_path=authority_path,
        plan_path=plan_path,
        live_state=_live_state(),
    )

    assert commit_rc == 0
    assert committed["status"] == "committed"
    assert not plan_path.exists()
    after = json.loads(authority_path.read_text(encoding="utf-8"))
    assert after["preopen_main_bot_pid"] == OLD_PID
    assert after["decision"]["main_bot_pid"] == NEW_PID
    assert after["observed_at_kst"] == before["observed_at_kst"]
    assert after["valid_until_kst"] == before["valid_until_kst"]
    assert after["policy"] == before["policy"]
    assert after["decision"] == {**before["decision"], "main_bot_pid": NEW_PID}
    record = after["main_bot_pid_handoffs"][0]
    assert record["previous_main_bot_pid"] == OLD_PID
    assert record["replacement_main_bot_pid"] == NEW_PID
    assert record["authority_sha256_before"] == before_hash
    assert record["new_order_authority_created"] is False
    assert record["authority_deadline_bypassed"] is False
    assert record["policy_changed"] is False


def test_commit_validates_staged_authority_before_atomic_publish(
    handoff_paths, monkeypatch
):
    authority_path = handoff_paths["authority"]
    plan_path = handoff_paths["plan"]
    _, prepare_rc = handoff.prepare_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW,
        authority_path=authority_path,
        plan_path=plan_path,
        live_state=_live_state(),
    )
    assert prepare_rc == 0
    before = authority_path.read_bytes()
    handoff_paths["live_pids"].remove(OLD_PID)
    handoff_paths["verification"]["pid"] = NEW_PID
    _write_json(handoff_paths["verify"], handoff_paths["verification"])
    original_loader = handoff._load_valid_authority

    def reject_staged(path, **kwargs):
        if path != authority_path:
            return None, "test_staged_contract_rejected"
        return original_loader(path, **kwargs)

    monkeypatch.setattr(handoff, "_load_valid_authority", reject_staged)
    result, rc = handoff.commit_main_bot_handoff(
        new_main_bot_pid=NEW_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW + timedelta(seconds=30),
        authority_path=authority_path,
        plan_path=plan_path,
        live_state=_live_state(),
    )

    assert rc == 3
    assert result["reason"] == (
        "rebound_authority_invalid:test_staged_contract_rejected"
    )
    assert authority_path.read_bytes() == before
    assert plan_path.exists()


def test_new_buy_guard_rejects_tampered_handoff_chain(handoff_paths):
    authority_path = handoff_paths["authority"]
    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    payload["preopen_main_bot_pid"] = OLD_PID
    payload["main_bot_pid_handoffs"] = [
        {
            "schema": handoff.HANDOFF_SCHEMA,
            "status": "committed",
            "sequence": 1,
            "target_date": NOW.date().isoformat(),
            "handoff_mode": "prepared_graceful_restart",
            "previous_main_bot_pid": OLD_PID + 1,
            "replacement_main_bot_pid": OLD_PID,
            "live_service_pid": SERVICE_PID,
            "new_order_authority_created": False,
            "authority_deadline_bypassed": False,
            "policy_changed": False,
            "quantity_changed": False,
            "custody_changed_by_handoff": False,
            "new_buy_order_nos_during_handoff": [],
        }
    ]
    _write_json(authority_path, payload)

    assert handoff.validate_new_buy_authority(
        authority_path=authority_path,
        plan_path=handoff_paths["plan"],
        now=NOW,
    ) == (False, "authority_handoff_root_pid_mismatch")


def test_commit_fails_closed_if_new_buy_appears_during_handoff(handoff_paths):
    authority_path = handoff_paths["authority"]
    plan_path = handoff_paths["plan"]
    _, prepare_rc = handoff.prepare_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW,
        authority_path=authority_path,
        plan_path=plan_path,
        live_state=_live_state(),
    )
    assert prepare_rc == 0
    state = json.loads(handoff_paths["first_state"].read_text(encoding="utf-8"))
    state["legs"].append(
        {
            "status": "BUY_OPEN",
            "quantity": 10,
            "position_qty": 0,
            "buy_order_no": "0000099",
        }
    )
    _write_json(handoff_paths["first_state"], state)
    handoff_paths["live_pids"].remove(OLD_PID)
    handoff_paths["verification"]["pid"] = NEW_PID
    _write_json(handoff_paths["verify"], handoff_paths["verification"])

    result, rc = handoff.commit_main_bot_handoff(
        new_main_bot_pid=NEW_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW + timedelta(seconds=30),
        authority_path=authority_path,
        plan_path=plan_path,
        live_state=_live_state(),
    )

    assert rc == 3
    assert result["reason"] == "new_buy_order_observed_during_handoff"
    assert plan_path.exists()
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    assert authority["decision"]["main_bot_pid"] == OLD_PID


def test_restart_guard_blocks_active_owner_without_prepared_plan(handoff_paths):
    result = handoff.restart_guard_decision(
        main_bot_pid=OLD_PID,
        now=NOW,
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state=_live_state(),
    )

    assert result["allowed"] is False
    assert result["reason"] == "handoff_plan_missing"


def test_restart_guard_allows_only_exact_prepared_plan(handoff_paths):
    _, rc = handoff.prepare_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW,
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state=_live_state(),
    )
    assert rc == 0

    result = handoff.restart_guard_decision(
        main_bot_pid=OLD_PID,
        now=NOW + timedelta(seconds=1),
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state=_live_state(),
    )

    assert result["allowed"] is True
    assert result["reason"] == "prepared_same_date_pid_handoff"


def test_restart_guard_rejects_tampered_prepared_plan(handoff_paths):
    _, rc = handoff.prepare_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW,
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state=_live_state(),
    )
    assert rc == 0
    plan = json.loads(handoff_paths["plan"].read_text(encoding="utf-8"))
    plan["old_main_bot_pid"] = OLD_PID + 1
    _write_json(handoff_paths["plan"], plan)

    result = handoff.restart_guard_decision(
        main_bot_pid=OLD_PID,
        now=NOW + timedelta(seconds=1),
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state=_live_state(),
    )

    assert result["allowed"] is False
    assert result["reason"] == "handoff_plan_evidence_invalid"


def test_restart_flag_is_consumed_and_audited_when_guard_blocks(tmp_path):
    restart_flag = tmp_path / "restart.flag"
    blocked_path = tmp_path / "blocked.json"
    lock_path = tmp_path / "guard.lock"
    restart_flag.write_text("source=test", encoding="utf-8")

    result = handoff.consume_guarded_restart_request(
        restart_flag,
        main_bot_pid=OLD_PID,
        now=NOW,
        decision_loader=lambda **kwargs: {
            "allowed": False,
            "reason": "handoff_plan_missing",
        },
        blocked_path=blocked_path,
        lock_path=lock_path,
    )

    assert result["claimed"] is True
    assert result["allowed"] is False
    assert not restart_flag.exists()
    blocked = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert blocked["main_bot_restarted"] is False
    assert blocked["orders_mutated"] is False
    assert blocked["request"] == "source=test"


def test_restart_flag_allowed_request_is_claimed_once_without_block_receipt(tmp_path):
    restart_flag = tmp_path / "restart.flag"
    blocked_path = tmp_path / "blocked.json"
    lock_path = tmp_path / "guard.lock"
    restart_flag.write_text("source=test-allowed", encoding="utf-8")

    result = handoff.consume_guarded_restart_request(
        restart_flag,
        main_bot_pid=OLD_PID,
        now=NOW,
        decision_loader=lambda **kwargs: {
            "allowed": True,
            "reason": "prepared_same_date_pid_handoff",
        },
        blocked_path=blocked_path,
        lock_path=lock_path,
    )

    assert result["claimed"] is True
    assert result["allowed"] is True
    assert not restart_flag.exists()
    assert not blocked_path.exists()


def test_restart_flag_guard_exception_is_fail_closed_and_audited(tmp_path):
    restart_flag = tmp_path / "restart.flag"
    blocked_path = tmp_path / "blocked.json"
    restart_flag.write_text("source=test-exception", encoding="utf-8")

    def broken_guard(**kwargs):
        raise RuntimeError("boom")

    result = handoff.consume_guarded_restart_request(
        restart_flag,
        main_bot_pid=OLD_PID,
        now=NOW,
        decision_loader=broken_guard,
        blocked_path=blocked_path,
        lock_path=tmp_path / "guard.lock",
    )

    assert result["allowed"] is False
    assert result["reason"] == "restart_guard_exception:RuntimeError"
    assert json.loads(blocked_path.read_text(encoding="utf-8"))["status"] == "blocked"


def test_restart_guard_blocks_unreadable_same_date_runtime_state(handoff_paths):
    handoff_paths["first_state"].write_text("{", encoding="utf-8")

    result = handoff.restart_guard_decision(
        main_bot_pid=OLD_PID,
        now=NOW,
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state={"ActiveState": "inactive", "SubState": "dead", "MainPID": 0},
    )

    assert result["allowed"] is False
    assert result["reason"] == "inactive_service_has_unresolved_custody"
    assert result["custody_reason"].startswith("runtime_state_unreadable:")


def test_new_buy_authority_blocks_while_handoff_plan_exists(handoff_paths):
    _, rc = handoff.prepare_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        confirmation=handoff.PREPARE_CONFIRMATION,
        write=True,
        now=NOW,
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        live_state=_live_state(),
    )
    assert rc == 0

    assert handoff.validate_new_buy_authority(
        authority_path=handoff_paths["authority"],
        plan_path=handoff_paths["plan"],
        now=NOW,
    ) == (False, "main_bot_pid_handoff_pending")


def test_recovery_requires_target_open_custody(handoff_paths, monkeypatch):
    _state(handoff_paths["first_state"], status="READY")
    monkeypatch.setattr(
        handoff,
        "_process_started_at",
        lambda pid, **kwargs: NOW.replace(hour=9, minute=39),
    )
    handoff_paths["live_pids"].remove(OLD_PID)
    handoff_paths["verification"]["pid"] = NEW_PID
    _write_json(handoff_paths["verify"], handoff_paths["verification"])

    result, rc = handoff.recover_existing_main_bot_handoff(
        old_main_bot_pid=OLD_PID,
        new_main_bot_pid=NEW_PID,
        live_service_pid=SERVICE_PID,
        expected_authority_sha256=handoff._sha256_file(handoff_paths["authority"]),
        confirmation=handoff.RECOVERY_CONFIRMATION,
        write=False,
        now=NOW,
        authority_path=handoff_paths["authority"],
        live_state=_live_state(),
    )

    assert rc == 3
    assert result["reason"] == "recovery_requires_existing_target_open_custody"
