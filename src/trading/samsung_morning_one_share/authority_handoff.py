"""Fail-closed main-bot restart handoff for the Samsung morning owner.

The PREOPEN authority remains the sole source of live authority.  This module
may only replace the PID bound inside that already-ready, same-date artifact;
it cannot create an authority, change policy, extend expiry, or bypass the
PREOPEN publication deadline.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from src.engine.threshold_cycle_preopen_apply import verify_runtime_env_handoff
from src.trading.samsung_morning_one_share.machine import DEFAULT_STATE_PATH, KST
from src.trading.samsung_morning_one_share.preflight import (
    DEFAULT_AUTHORITY_PATH,
    _is_bot_main_pid,
    validate_authority,
)
from src.trading.samsung_morning_one_share.reentry import DEFAULT_REENTRY_STATE_PATH
from src.utils.constants import DATA_DIR, PROJECT_ROOT

HANDOFF_SCHEMA = "samsung_morning_main_bot_pid_handoff_v1"
PLAN_SCHEMA = "samsung_morning_main_bot_restart_handoff_plan_v1"
BLOCKED_RESTART_SCHEMA = "samsung_morning_main_bot_restart_blocked_v1"
PREPARE_CONFIRMATION = "SAMSUNG_MAIN_BOT_RESTART_HANDOFF"
RECOVERY_CONFIRMATION = "RECOVER_EXISTING_SAMSUNG_MAIN_BOT_PID_HANDOFF"
LIVE_UNIT = "korstockscan-samsung-morning-one-share.service"
DEFAULT_PLAN_PATH = (
    DATA_DIR / "runtime" / "samsung_morning_main_bot_restart_handoff_plan.json"
)
DEFAULT_BLOCKED_RESTART_PATH = (
    DATA_DIR / "runtime" / "samsung_morning_main_bot_restart_blocked.json"
)
DEFAULT_GUARD_LOCK_PATH = PROJECT_ROOT / "tmp" / "main_bot_restart_guard.lock"
DEFAULT_PLAN_TTL_SEC = 360


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(raw)


def _is_sha256(value: object) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "0123456789abcdef" for character in text
    )


def _is_zero_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == 0


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_object_required:{path}")
    return payload


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o640)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _systemd_live_state() -> dict:
    properties = "LoadState,ActiveState,SubState,MainPID,Result,ExecMainStartTimestamp"
    try:
        completed = subprocess.run(
            [
                "/bin/systemctl",
                "show",
                LIVE_UNIT,
                f"--property={properties}",
                "--no-pager",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"query_error": f"{type(exc).__name__}:{exc}"}
    if completed.returncode != 0:
        return {
            "query_error": f"systemctl_rc_{completed.returncode}",
            "stderr": completed.stderr.strip()[:300],
        }
    state: dict[str, str | int] = {}
    for line in completed.stdout.splitlines():
        key, separator, value = line.partition("=")
        if not separator:
            continue
        state[key] = int(value) if key == "MainPID" and value.isdigit() else value
    return state


def _live_service_pid(state: dict) -> int:
    pid = state.get("MainPID")
    if (
        state.get("ActiveState") == "active"
        and state.get("SubState") == "running"
        and isinstance(pid, int)
        and not isinstance(pid, bool)
        and pid > 0
    ):
        return pid
    return 0


def _is_samsung_live_service_pid(pid: int, *, proc_root: Path = Path("/proc")) -> bool:
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        tokens = [
            token.decode("utf-8", errors="replace")
            for token in (proc_root / str(pid) / "cmdline").read_bytes().split(b"\0")
            if token
        ]
    except OSError:
        return False
    return (
        "-m" in tokens
        and "src.trading.samsung_morning_one_share.service" in tokens
        and "--live" in tokens
    )


def _process_started_at(pid: int, *, proc_root: Path = Path("/proc")) -> datetime:
    stat_tokens = (proc_root / str(pid) / "stat").read_text(encoding="utf-8").split()
    start_ticks = int(stat_tokens[21])
    boot_time = 0
    for line in (proc_root / "stat").read_text(encoding="utf-8").splitlines():
        if line.startswith("btime "):
            boot_time = int(line.split()[1])
            break
    if boot_time <= 0:
        raise ValueError("proc_boot_time_missing")
    clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    return datetime.fromtimestamp(boot_time + start_ticks / clock_ticks, tz=KST)


def _runtime_verify_artifact_path(target_date: str) -> Path:
    return (
        DATA_DIR
        / "threshold_cycle"
        / "runtime_env"
        / f"threshold_runtime_env_verify_{target_date}.json"
    )


def _strict_runtime_verification(target_date: str, pid: int) -> tuple[dict, str]:
    verification = verify_runtime_env_handoff(target_date, pid=pid)
    checks = (
        verification.get("status") == "pass",
        verification.get("passed") is True,
        verification.get("pid") == pid,
        verification.get("pid_passed") is True,
        verification.get("pid_env_available") is True,
        not verification.get("pid_missing"),
        verification.get("findings") == [],
        verification.get("pid_mismatches") == [],
        int(verification.get("runtime_policy_fail_count", -1)) == 0,
        int(verification.get("dated_runtime_override_fail_count", -1)) == 0,
        int(verification.get("unverified_selected_family_count", -1)) == 0,
    )
    if not all(checks):
        return verification, "replacement_main_bot_runtime_env_unverified"
    artifact_path = _runtime_verify_artifact_path(target_date)
    try:
        artifact = _read_json(artifact_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return verification, "replacement_runtime_verify_artifact_unreadable"
    if (
        artifact.get("status") != "pass"
        or artifact.get("pid") != pid
        or artifact.get("pid_passed") is not True
        or artifact.get("findings") != []
        or artifact.get("pid_mismatches") != []
    ):
        return verification, "replacement_runtime_verify_artifact_mismatch"
    return {
        "status": "pass",
        "pid": pid,
        "target_date": target_date,
        "artifact_path": str(artifact_path),
        "artifact_sha256": _sha256_file(artifact_path),
        "runtime_policy_fail_count": verification["runtime_policy_fail_count"],
        "dated_runtime_override_fail_count": verification[
            "dated_runtime_override_fail_count"
        ],
        "unverified_selected_family_count": verification[
            "unverified_selected_family_count"
        ],
    }, "ready"


def _state_snapshot(paths: tuple[Path, ...], *, target_date: str) -> dict:
    rows: list[dict] = []
    buy_order_nos: set[str] = set()
    for path in paths:
        if not path.exists():
            rows.append({"path": str(path), "status": "not_found"})
            continue
        payload = _read_json(path)
        row = {
            "path": str(path),
            "sha256": _sha256_file(path),
            "schema": str(payload.get("schema") or ""),
            "trade_date": str(payload.get("trade_date") or ""),
            "status": str(payload.get("status") or ""),
            "position_qty": int(payload.get("position_qty", 0) or 0),
        }
        current_date = row["trade_date"] == target_date
        current_buy_order_nos = sorted(
            {
                str(leg.get("buy_order_no") or "").strip()
                for leg in payload.get("legs", [])
                if isinstance(leg, dict) and str(leg.get("buy_order_no") or "").strip()
            }
        )
        row["buy_order_nos"] = current_buy_order_nos if current_date else []
        if current_date:
            buy_order_nos.update(current_buy_order_nos)
        rows.append(row)
    return {
        "target_date": target_date,
        "states": rows,
        "current_date_buy_order_nos": sorted(buy_order_nos),
    }


def _current_state_requires_custody(*, target_date: str) -> tuple[bool, str]:
    active_statuses = {
        "READY",
        "BUY_OPEN",
        "BUY_CANCEL_PENDING",
        "POSITION_OPEN",
        "TARGET_OPEN",
        "BLOCKED",
    }
    for path in (DEFAULT_STATE_PATH, DEFAULT_REENTRY_STATE_PATH):
        if not path.exists():
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            return True, f"runtime_state_unreadable:{path}"
        if str(payload.get("trade_date") or "") != target_date:
            continue
        try:
            position_qty = int(payload.get("position_qty", 0) or 0)
        except (TypeError, ValueError):
            return True, f"runtime_state_quantity_invalid:{path}"
        if position_qty > 0:
            return True, "same_date_unresolved_custody"
        if str(payload.get("status") or "") in active_statuses:
            return True, "same_date_active_machine_state"
        legs = payload.get("legs", [])
        if not isinstance(legs, list):
            return True, f"runtime_state_legs_invalid:{path}"
        for leg in legs:
            if not isinstance(leg, dict):
                return True, f"runtime_state_leg_invalid:{path}"
            try:
                leg_position_qty = int(leg.get("position_qty", 0) or 0)
            except (TypeError, ValueError):
                return True, f"runtime_state_leg_quantity_invalid:{path}"
            if leg_position_qty > 0:
                return True, "same_date_unresolved_leg_custody"
            if str(leg.get("status") or "") in active_statuses:
                return True, "same_date_active_leg_state"
    return False, "no_same_date_active_state"


def _validate_existing_handoffs(authority: dict) -> tuple[bool, str]:
    rows = authority.get("main_bot_pid_handoffs", [])
    if rows is None:
        rows = []
    if not isinstance(rows, list) or len(rows) > 16:
        return False, "authority_handoff_history_invalid"
    root_pid = authority.get("preopen_main_bot_pid")
    if rows and (
        isinstance(root_pid, bool) or not isinstance(root_pid, int) or root_pid <= 0
    ):
        return False, "authority_handoff_root_pid_invalid"
    policy_sha256 = _canonical_sha256(authority.get("policy"))
    previous_replacement = None
    previous_rebound_at: datetime | None = None
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get("schema") != HANDOFF_SCHEMA:
            return False, "authority_handoff_history_invalid"
        if row.get("sequence") != index or row.get("status") != "committed":
            return False, "authority_handoff_history_invalid"
        if (
            row.get("target_date") != authority.get("target_date")
            or row.get("new_order_authority_created") is not False
            or row.get("authority_deadline_bypassed") is not False
            or row.get("policy_changed") is not False
            or row.get("quantity_changed") is not False
            or row.get("custody_changed_by_handoff") is not False
            or row.get("new_buy_order_nos_during_handoff") != []
            or row.get("handoff_mode")
            not in {
                "prepared_graceful_restart",
                "explicit_custody_only_post_restart_recovery",
            }
        ):
            return False, "authority_handoff_history_invalid"
        previous_pid = row.get("previous_main_bot_pid")
        replacement_pid = row.get("replacement_main_bot_pid")
        service_pid = row.get("live_service_pid")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in (previous_pid, replacement_pid, service_pid)
        ):
            return False, "authority_handoff_history_invalid"
        if index == 1 and previous_pid != root_pid:
            return False, "authority_handoff_root_pid_mismatch"
        if previous_replacement is not None and previous_pid != previous_replacement:
            return False, "authority_handoff_history_invalid"
        try:
            rebound_at = datetime.fromisoformat(str(row.get("rebound_at_kst") or ""))
        except ValueError:
            return False, "authority_handoff_time_invalid"
        if (
            rebound_at.tzinfo is None
            or rebound_at.astimezone(KST).date().isoformat()
            != authority.get("target_date")
            or (
                previous_rebound_at is not None
                and rebound_at.astimezone(KST) < previous_rebound_at
            )
        ):
            return False, "authority_handoff_time_invalid"
        rebound_at = rebound_at.astimezone(KST)
        runtime_verification = row.get("runtime_verification_after")
        if (
            not _is_sha256(row.get("authority_sha256_before"))
            or row.get("policy_sha256_before") != policy_sha256
            or row.get("policy_sha256_after") != policy_sha256
            or not isinstance(runtime_verification, dict)
            or runtime_verification.get("status") != "pass"
            or runtime_verification.get("pid") != replacement_pid
            or runtime_verification.get("target_date") != authority.get("target_date")
            or not _is_sha256(runtime_verification.get("artifact_sha256"))
            or not _is_zero_int(runtime_verification.get("runtime_policy_fail_count"))
            or not _is_zero_int(
                runtime_verification.get("dated_runtime_override_fail_count")
            )
            or not _is_zero_int(
                runtime_verification.get("unverified_selected_family_count")
            )
            or not isinstance(row.get("state_snapshot_before"), dict)
            or row["state_snapshot_before"].get("target_date")
            != authority.get("target_date")
            or not isinstance(row.get("state_snapshot_after"), dict)
            or row["state_snapshot_after"].get("target_date")
            != authority.get("target_date")
        ):
            return False, "authority_handoff_evidence_invalid"
        record_seed = {
            "sequence": index,
            "target_date": authority.get("target_date"),
            "previous_main_bot_pid": previous_pid,
            "replacement_main_bot_pid": replacement_pid,
            "rebound_at_kst": row.get("rebound_at_kst"),
            "authority_sha256_before": row.get("authority_sha256_before"),
        }
        if row.get("handoff_id") != _canonical_sha256(record_seed):
            return False, "authority_handoff_id_invalid"
        previous_replacement = replacement_pid
        previous_rebound_at = rebound_at
    decision = authority.get("decision")
    if rows and (
        not isinstance(decision, dict)
        or decision.get("main_bot_pid") != previous_replacement
    ):
        return False, "authority_handoff_history_current_pid_mismatch"
    return True, "ready"


def _load_valid_authority(
    authority_path: Path,
    *,
    now: datetime,
    require_live_main_bot_runtime: bool,
) -> tuple[dict | None, str]:
    valid, reason = validate_authority(
        authority_path,
        now=now,
        require_live_main_bot_runtime=require_live_main_bot_runtime,
    )
    if not valid:
        return None, reason
    try:
        authority = _read_json(authority_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, f"authority_unreadable:{type(exc).__name__}"
    history_valid, history_reason = _validate_existing_handoffs(authority)
    if not history_valid:
        return None, history_reason
    return authority, "ready"


def _validate_live_service(
    expected_pid: int,
    *,
    live_state: dict | None,
    proc_root: Path,
) -> tuple[dict, str]:
    state = dict(live_state) if live_state is not None else _systemd_live_state()
    if state.get("query_error"):
        return state, "samsung_live_service_state_unreadable"
    actual_pid = _live_service_pid(state)
    if actual_pid <= 0:
        return state, "samsung_live_service_not_active"
    if actual_pid != expected_pid:
        return state, "samsung_live_service_pid_mismatch"
    if not _is_samsung_live_service_pid(actual_pid, proc_root=proc_root):
        return state, "samsung_live_service_identity_invalid"
    return state, "ready"


def prepare_main_bot_handoff(
    *,
    old_main_bot_pid: int,
    confirmation: str,
    write: bool,
    now: datetime | None = None,
    authority_path: Path = DEFAULT_AUTHORITY_PATH,
    plan_path: Path = DEFAULT_PLAN_PATH,
    live_state: dict | None = None,
    proc_root: Path = Path("/proc"),
    ttl_sec: int = DEFAULT_PLAN_TTL_SEC,
) -> tuple[dict, int]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    if confirmation != PREPARE_CONFIRMATION:
        return {"status": "blocked", "reason": "confirmation_invalid"}, 2
    state = dict(live_state) if live_state is not None else _systemd_live_state()
    service_pid = _live_service_pid(state)
    target_date = now.date().isoformat()
    if service_pid <= 0:
        if state.get("query_error"):
            return {
                "status": "blocked",
                "reason": "samsung_live_service_state_unreadable",
                "live_state": state,
            }, 3
        custody_required, custody_reason = _current_state_requires_custody(
            target_date=target_date
        )
        if custody_required:
            return {
                "status": "blocked",
                "reason": "inactive_service_has_unresolved_custody",
                "custody_reason": custody_reason,
                "live_state": state,
            }, 3
        return {"status": "not_required", "reason": "morning_owner_not_active"}, 0
    state, service_reason = _validate_live_service(
        service_pid, live_state=state, proc_root=proc_root
    )
    if service_reason != "ready":
        return {"status": "blocked", "reason": service_reason}, 3
    if plan_path.exists():
        return {
            "status": "blocked",
            "reason": "handoff_plan_already_exists",
            "plan_path": str(plan_path),
        }, 3
    authority, reason = _load_valid_authority(
        authority_path, now=now, require_live_main_bot_runtime=True
    )
    if authority is None:
        return {"status": "blocked", "reason": reason}, 3
    decision = authority["decision"]
    if decision.get("main_bot_pid") != old_main_bot_pid:
        return {"status": "blocked", "reason": "authority_old_pid_mismatch"}, 3
    runtime_verification, runtime_reason = _strict_runtime_verification(
        target_date, old_main_bot_pid
    )
    if runtime_reason != "ready":
        return {
            "status": "blocked",
            "reason": runtime_reason,
            "runtime_verification": runtime_verification,
        }, 3
    authority_sha256 = _sha256_file(authority_path)
    state_snapshot = _state_snapshot(
        (DEFAULT_STATE_PATH, DEFAULT_REENTRY_STATE_PATH), target_date=target_date
    )
    expires_at = now + timedelta(seconds=min(900, max(60, int(ttl_sec))))
    plan = {
        "schema": PLAN_SCHEMA,
        "status": "prepared",
        "target_date": target_date,
        "prepared_at_kst": now.isoformat(),
        "expires_at_kst": expires_at.isoformat(),
        "old_main_bot_pid": old_main_bot_pid,
        "live_service_pid": service_pid,
        "authority_path": str(authority_path),
        "authority_sha256_before": authority_sha256,
        "policy_sha256": _canonical_sha256(authority.get("policy")),
        "runtime_verification_before": runtime_verification,
        "state_snapshot_before": state_snapshot,
        "new_order_authority_created": False,
        "authority_deadline_bypassed": False,
        "policy_change_allowed": False,
        "quantity_change_allowed": False,
        "custody_change_allowed": False,
    }
    plan["plan_id"] = _canonical_sha256(plan)
    if write:
        _atomic_write(plan_path, plan)
    return {
        "status": "prepared" if write else "ready_to_prepare",
        "reason": "same_date_authority_handoff_only",
        "plan_path": str(plan_path),
        "plan": plan,
    }, 0


def _load_valid_plan(
    plan_path: Path,
    *,
    now: datetime,
) -> tuple[dict | None, str]:
    try:
        plan = _read_json(plan_path)
    except FileNotFoundError:
        return None, "handoff_plan_missing"
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, f"handoff_plan_unreadable:{type(exc).__name__}"
    if plan.get("schema") != PLAN_SCHEMA or plan.get("status") != "prepared":
        return None, "handoff_plan_contract_invalid"
    if plan.get("target_date") != now.date().isoformat():
        return None, "handoff_plan_target_date_mismatch"
    try:
        prepared_at = datetime.fromisoformat(str(plan.get("prepared_at_kst") or ""))
        expires_at = datetime.fromisoformat(str(plan.get("expires_at_kst") or ""))
    except ValueError:
        return None, "handoff_plan_time_invalid"
    if prepared_at.tzinfo is None or expires_at.tzinfo is None:
        return None, "handoff_plan_time_invalid"
    prepared_at = prepared_at.astimezone(KST)
    expires_at = expires_at.astimezone(KST)
    lifetime_sec = (expires_at - prepared_at).total_seconds()
    if (
        prepared_at.date().isoformat() != plan.get("target_date")
        or expires_at.date().isoformat() != plan.get("target_date")
        or not 60 <= lifetime_sec <= 900
    ):
        return None, "handoff_plan_time_invalid"
    if prepared_at > now or now > expires_at:
        return None, "handoff_plan_expired"
    if (
        plan.get("new_order_authority_created") is not False
        or plan.get("authority_deadline_bypassed") is not False
        or plan.get("policy_change_allowed") is not False
        or plan.get("quantity_change_allowed") is not False
        or plan.get("custody_change_allowed") is not False
    ):
        return None, "handoff_plan_scope_invalid"
    old_pid = plan.get("old_main_bot_pid")
    service_pid = plan.get("live_service_pid")
    runtime_verification = plan.get("runtime_verification_before")
    state_snapshot = plan.get("state_snapshot_before")
    plan_body = {key: value for key, value in plan.items() if key != "plan_id"}
    if (
        any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in (old_pid, service_pid)
        )
        or not _is_sha256(plan.get("authority_sha256_before"))
        or not _is_sha256(plan.get("policy_sha256"))
        or not str(plan.get("authority_path") or "").startswith("/")
        or not isinstance(runtime_verification, dict)
        or runtime_verification.get("status") != "pass"
        or runtime_verification.get("pid") != old_pid
        or runtime_verification.get("target_date") != plan.get("target_date")
        or not _is_sha256(runtime_verification.get("artifact_sha256"))
        or not isinstance(state_snapshot, dict)
        or state_snapshot.get("target_date") != plan.get("target_date")
        or plan.get("plan_id") != _canonical_sha256(plan_body)
    ):
        return None, "handoff_plan_evidence_invalid"
    return plan, "ready"


def restart_guard_decision(
    *,
    main_bot_pid: int,
    now: datetime | None = None,
    authority_path: Path = DEFAULT_AUTHORITY_PATH,
    plan_path: Path = DEFAULT_PLAN_PATH,
    live_state: dict | None = None,
    proc_root: Path = Path("/proc"),
) -> dict:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    target_date = now.date().isoformat()
    state = dict(live_state) if live_state is not None else _systemd_live_state()
    if state.get("query_error"):
        return {
            "allowed": False,
            "reason": "samsung_live_service_state_unreadable",
            "live_state": state,
        }
    service_pid = _live_service_pid(state)
    if service_pid <= 0:
        custody_required, custody_reason = _current_state_requires_custody(
            target_date=target_date
        )
        if custody_required:
            return {
                "allowed": False,
                "reason": "inactive_service_has_unresolved_custody",
                "custody_reason": custody_reason,
                "live_state": state,
            }
        return {
            "allowed": True,
            "reason": "morning_owner_not_active",
            "live_state": state,
        }
    _, service_reason = _validate_live_service(
        service_pid, live_state=state, proc_root=proc_root
    )
    if service_reason != "ready":
        return {"allowed": False, "reason": service_reason, "live_state": state}
    plan, plan_reason = _load_valid_plan(plan_path, now=now)
    if plan is None:
        return {
            "allowed": False,
            "reason": plan_reason,
            "live_state": state,
            "required_action": "use_restart_sh_to_prepare_same_date_pid_handoff",
        }
    try:
        authority_sha256 = _sha256_file(authority_path)
    except OSError:
        return {"allowed": False, "reason": "authority_unreadable"}
    if (
        plan.get("old_main_bot_pid") != main_bot_pid
        or plan.get("live_service_pid") != service_pid
        or plan.get("authority_path") != str(authority_path)
        or plan.get("authority_sha256_before") != authority_sha256
    ):
        return {"allowed": False, "reason": "handoff_plan_binding_mismatch"}
    return {
        "allowed": True,
        "reason": "prepared_same_date_pid_handoff",
        "plan_id": plan.get("plan_id"),
        "live_service_pid": service_pid,
    }


def _apply_handoff(
    *,
    old_main_bot_pid: int,
    new_main_bot_pid: int,
    service_pid: int,
    authority_path: Path,
    now: datetime,
    runtime_verification: dict,
    state_snapshot_before: dict,
    handoff_mode: str,
) -> tuple[dict, str]:
    lock_path = authority_path.with_suffix(authority_path.suffix + ".handoff.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        authority = _read_json(authority_path)
        history_valid, history_reason = _validate_existing_handoffs(authority)
        if not history_valid:
            return {}, history_reason
        decision = authority.get("decision")
        if (
            not isinstance(decision, dict)
            or decision.get("main_bot_pid") != old_main_bot_pid
        ):
            return {}, "authority_old_pid_mismatch"
        before_sha256 = _sha256_file(authority_path)
        policy_sha256 = _canonical_sha256(authority.get("policy"))
        current_snapshot = _state_snapshot(
            (DEFAULT_STATE_PATH, DEFAULT_REENTRY_STATE_PATH),
            target_date=now.date().isoformat(),
        )
        before_orders = set(
            state_snapshot_before.get("current_date_buy_order_nos") or []
        )
        current_orders = set(current_snapshot.get("current_date_buy_order_nos") or [])
        new_orders = sorted(current_orders - before_orders)
        if new_orders:
            return {}, "new_buy_order_observed_during_handoff"
        history = list(authority.get("main_bot_pid_handoffs") or [])
        sequence = len(history) + 1
        record_seed = {
            "sequence": sequence,
            "target_date": now.date().isoformat(),
            "previous_main_bot_pid": old_main_bot_pid,
            "replacement_main_bot_pid": new_main_bot_pid,
            "rebound_at_kst": now.isoformat(),
            "authority_sha256_before": before_sha256,
        }
        record = {
            "schema": HANDOFF_SCHEMA,
            "status": "committed",
            "handoff_id": _canonical_sha256(record_seed),
            "sequence": sequence,
            "handoff_mode": handoff_mode,
            "target_date": now.date().isoformat(),
            "rebound_at_kst": now.isoformat(),
            "previous_main_bot_pid": old_main_bot_pid,
            "replacement_main_bot_pid": new_main_bot_pid,
            "live_service_pid": service_pid,
            "authority_sha256_before": before_sha256,
            "policy_sha256_before": policy_sha256,
            "policy_sha256_after": policy_sha256,
            "runtime_verification_after": runtime_verification,
            "state_snapshot_before": state_snapshot_before,
            "state_snapshot_after": current_snapshot,
            "new_buy_order_nos_during_handoff": [],
            "new_order_authority_created": False,
            "authority_deadline_bypassed": False,
            "policy_changed": False,
            "quantity_changed": False,
            "custody_changed_by_handoff": False,
        }
        history.append(record)
        if len(history) == 1:
            authority["preopen_main_bot_pid"] = old_main_bot_pid
        authority["main_bot_pid_handoffs"] = history
        authority["decision"] = {**decision, "main_bot_pid": new_main_bot_pid}

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{authority_path.name}.handoff.", dir=authority_path.parent
        )
        staged_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    authority,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(staged_path, 0o640)
            staged, staged_reason = _load_valid_authority(
                staged_path,
                now=now,
                require_live_main_bot_runtime=True,
            )
            if staged is None:
                return {}, f"rebound_authority_invalid:{staged_reason}"
            if _canonical_sha256(staged.get("policy")) != policy_sha256:
                return {}, "authority_policy_changed_during_handoff"
            if _sha256_file(authority_path) != before_sha256:
                return {}, "authority_changed_during_handoff_publish"
            os.replace(staged_path, authority_path)
            directory_fd = os.open(authority_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            staged_path.unlink(missing_ok=True)
        return {
            "status": "committed",
            "reason": "same_date_pid_binding_replaced_without_new_authority",
            "authority_path": str(authority_path),
            "authority_sha256_after": _sha256_file(authority_path),
            "handoff": record,
        }, "ready"


def commit_main_bot_handoff(
    *,
    new_main_bot_pid: int,
    confirmation: str,
    write: bool,
    now: datetime | None = None,
    authority_path: Path = DEFAULT_AUTHORITY_PATH,
    plan_path: Path = DEFAULT_PLAN_PATH,
    live_state: dict | None = None,
    proc_root: Path = Path("/proc"),
) -> tuple[dict, int]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    if confirmation != PREPARE_CONFIRMATION:
        return {"status": "blocked", "reason": "confirmation_invalid"}, 2
    plan, plan_reason = _load_valid_plan(plan_path, now=now)
    if plan is None:
        state = dict(live_state) if live_state is not None else _systemd_live_state()
        if plan_reason == "handoff_plan_missing" and _live_service_pid(state) <= 0:
            return {"status": "not_required", "reason": "morning_owner_not_active"}, 0
        return {"status": "blocked", "reason": plan_reason}, 3
    old_pid = int(plan["old_main_bot_pid"])
    service_pid = int(plan["live_service_pid"])
    if plan.get("authority_path") != str(authority_path):
        return {"status": "blocked", "reason": "handoff_plan_authority_mismatch"}, 3
    if _is_bot_main_pid(old_pid, proc_root=proc_root):
        return {"status": "blocked", "reason": "previous_main_bot_still_active"}, 3
    if not _is_bot_main_pid(new_main_bot_pid, proc_root=proc_root):
        return {"status": "blocked", "reason": "replacement_main_bot_inactive"}, 3
    _, service_reason = _validate_live_service(
        service_pid, live_state=live_state, proc_root=proc_root
    )
    if service_reason != "ready":
        return {"status": "blocked", "reason": service_reason}, 3
    try:
        authority_sha256 = _sha256_file(authority_path)
    except OSError:
        return {"status": "blocked", "reason": "authority_unreadable"}, 3
    if authority_sha256 != plan.get("authority_sha256_before"):
        return {"status": "blocked", "reason": "authority_changed_after_prepare"}, 3
    authority, reason = _load_valid_authority(
        authority_path, now=now, require_live_main_bot_runtime=False
    )
    if authority is None:
        return {"status": "blocked", "reason": reason}, 3
    if authority["decision"].get("main_bot_pid") != old_pid:
        return {"status": "blocked", "reason": "authority_old_pid_mismatch"}, 3
    runtime_verification, runtime_reason = _strict_runtime_verification(
        now.date().isoformat(), new_main_bot_pid
    )
    if runtime_reason != "ready":
        return {
            "status": "blocked",
            "reason": runtime_reason,
            "runtime_verification": runtime_verification,
        }, 3
    if not write:
        return {
            "status": "ready_to_commit",
            "reason": "same_date_pid_handoff_validated",
            "plan_id": plan.get("plan_id"),
        }, 0
    output, apply_reason = _apply_handoff(
        old_main_bot_pid=old_pid,
        new_main_bot_pid=new_main_bot_pid,
        service_pid=service_pid,
        authority_path=authority_path,
        now=now,
        runtime_verification=runtime_verification,
        state_snapshot_before=plan["state_snapshot_before"],
        handoff_mode="prepared_graceful_restart",
    )
    if apply_reason != "ready":
        return {"status": "blocked", "reason": apply_reason}, 3
    plan_path.unlink(missing_ok=True)
    return output, 0


def _recovery_state_is_custody_only(
    *,
    target_date: str,
    replacement_started_at: datetime,
) -> tuple[bool, str, dict]:
    try:
        state = _read_json(DEFAULT_STATE_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return False, f"morning_state_unreadable:{type(exc).__name__}", {}
    if state.get("trade_date") != target_date or state.get("status") != "TARGET_OPEN":
        return False, "recovery_requires_existing_target_open_custody", state
    legs = state.get("legs")
    if not isinstance(legs, list) or len(legs) != 2:
        return False, "recovery_two_leg_custody_invalid", state
    if int(state.get("position_qty", 0) or 0) != 20:
        return False, "recovery_position_quantity_invalid", state
    for leg in legs:
        if (
            not isinstance(leg, dict)
            or leg.get("status") != "TARGET_OPEN"
            or int(leg.get("quantity", 0) or 0) != 10
            or int(leg.get("position_qty", 0) or 0) != 10
            or not str(leg.get("buy_order_no") or "").strip()
            or not str(leg.get("target_order_no") or "").strip()
        ):
            return False, "recovery_two_leg_custody_invalid", state
        try:
            filled_at = datetime.fromisoformat(str(leg.get("buy_filled_at") or ""))
        except ValueError:
            return False, "recovery_buy_fill_time_invalid", state
        if (
            filled_at.tzinfo is None
            or filled_at.astimezone(KST) >= replacement_started_at
        ):
            return False, "recovery_buy_activity_not_proven_pre_restart", state
    try:
        reentry = _read_json(DEFAULT_REENTRY_STATE_PATH)
    except FileNotFoundError:
        reentry = {}
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return False, f"reentry_state_unreadable:{type(exc).__name__}", state
    if reentry.get("trade_date") == target_date and (
        int(reentry.get("position_qty", 0) or 0) > 0
        or any(
            str(leg.get("buy_order_no") or "").strip()
            for leg in reentry.get("legs", [])
            if isinstance(leg, dict)
        )
    ):
        return False, "recovery_reentry_activity_present", state
    return True, "ready", state


def recover_existing_main_bot_handoff(
    *,
    old_main_bot_pid: int,
    new_main_bot_pid: int,
    live_service_pid: int,
    expected_authority_sha256: str,
    confirmation: str,
    write: bool,
    now: datetime | None = None,
    authority_path: Path = DEFAULT_AUTHORITY_PATH,
    live_state: dict | None = None,
    proc_root: Path = Path("/proc"),
) -> tuple[dict, int]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    if confirmation != RECOVERY_CONFIRMATION:
        return {"status": "blocked", "reason": "confirmation_invalid"}, 2
    if _is_bot_main_pid(old_main_bot_pid, proc_root=proc_root):
        return {"status": "blocked", "reason": "previous_main_bot_still_active"}, 3
    if not _is_bot_main_pid(new_main_bot_pid, proc_root=proc_root):
        return {"status": "blocked", "reason": "replacement_main_bot_inactive"}, 3
    _, service_reason = _validate_live_service(
        live_service_pid, live_state=live_state, proc_root=proc_root
    )
    if service_reason != "ready":
        return {"status": "blocked", "reason": service_reason}, 3
    try:
        authority_sha256 = _sha256_file(authority_path)
    except OSError:
        return {"status": "blocked", "reason": "authority_unreadable"}, 3
    if authority_sha256 != expected_authority_sha256:
        return {"status": "blocked", "reason": "authority_sha256_mismatch"}, 3
    authority, reason = _load_valid_authority(
        authority_path, now=now, require_live_main_bot_runtime=False
    )
    if authority is None:
        return {"status": "blocked", "reason": reason}, 3
    if authority["decision"].get("main_bot_pid") != old_main_bot_pid:
        return {"status": "blocked", "reason": "authority_old_pid_mismatch"}, 3
    try:
        replacement_started_at = _process_started_at(
            new_main_bot_pid, proc_root=proc_root
        )
    except (OSError, ValueError, IndexError) as exc:
        return {
            "status": "blocked",
            "reason": f"replacement_start_time_unreadable:{type(exc).__name__}",
        }, 3
    custody_only, custody_reason, _ = _recovery_state_is_custody_only(
        target_date=now.date().isoformat(),
        replacement_started_at=replacement_started_at,
    )
    if not custody_only:
        return {"status": "blocked", "reason": custody_reason}, 3
    runtime_verification, runtime_reason = _strict_runtime_verification(
        now.date().isoformat(), new_main_bot_pid
    )
    if runtime_reason != "ready":
        return {
            "status": "blocked",
            "reason": runtime_reason,
            "runtime_verification": runtime_verification,
        }, 3
    state_snapshot = _state_snapshot(
        (DEFAULT_STATE_PATH, DEFAULT_REENTRY_STATE_PATH),
        target_date=now.date().isoformat(),
    )
    if not write:
        return {
            "status": "ready_to_recover",
            "reason": "custody_only_post_restart_rebind_validated",
            "state_snapshot": state_snapshot,
        }, 0
    output, apply_reason = _apply_handoff(
        old_main_bot_pid=old_main_bot_pid,
        new_main_bot_pid=new_main_bot_pid,
        service_pid=live_service_pid,
        authority_path=authority_path,
        now=now,
        runtime_verification=runtime_verification,
        state_snapshot_before=state_snapshot,
        handoff_mode="explicit_custody_only_post_restart_recovery",
    )
    if apply_reason != "ready":
        return {"status": "blocked", "reason": apply_reason}, 3
    return output, 0


def abort_main_bot_handoff(
    *,
    old_main_bot_pid: int,
    confirmation: str,
    plan_path: Path = DEFAULT_PLAN_PATH,
    proc_root: Path = Path("/proc"),
) -> tuple[dict, int]:
    if confirmation != PREPARE_CONFIRMATION:
        return {"status": "blocked", "reason": "confirmation_invalid"}, 2
    now = datetime.now(tz=KST)
    plan, reason = _load_valid_plan(plan_path, now=now)
    if plan is None:
        return {"status": "blocked", "reason": reason}, 3
    if plan.get("old_main_bot_pid") != old_main_bot_pid:
        return {"status": "blocked", "reason": "handoff_plan_binding_mismatch"}, 3
    if not _is_bot_main_pid(old_main_bot_pid, proc_root=proc_root):
        return {"status": "blocked", "reason": "cannot_abort_after_old_pid_exit"}, 3
    plan_path.unlink(missing_ok=True)
    return {"status": "aborted", "reason": "old_main_bot_remained_active"}, 0


def validate_new_buy_authority(
    *,
    authority_path: Path = DEFAULT_AUTHORITY_PATH,
    plan_path: Path = DEFAULT_PLAN_PATH,
    now: datetime | None = None,
) -> tuple[bool, str]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    if plan_path.exists():
        plan, reason = _load_valid_plan(plan_path, now=now)
        return False, "main_bot_pid_handoff_pending" if plan is not None else reason
    authority, reason = _load_valid_authority(
        authority_path,
        now=now,
        require_live_main_bot_runtime=True,
    )
    return authority is not None, reason


def consume_guarded_restart_request(
    restart_flag_path: Path,
    *,
    main_bot_pid: int,
    now: datetime | None = None,
    decision_loader: Callable[..., dict] = restart_guard_decision,
    blocked_path: Path = DEFAULT_BLOCKED_RESTART_PATH,
    lock_path: Path = DEFAULT_GUARD_LOCK_PATH,
) -> dict:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if not restart_flag_path.exists():
            return {"claimed": False, "allowed": False, "reason": "flag_absent"}
        try:
            request = restart_flag_path.read_text(encoding="utf-8").strip()[:512]
        except OSError as exc:
            request = f"unreadable:{type(exc).__name__}:{exc}"
        restart_flag_path.unlink(missing_ok=True)
        try:
            decision = decision_loader(main_bot_pid=main_bot_pid, now=now)
            if not isinstance(decision, dict):
                raise TypeError("restart_guard_decision_must_be_object")
        except Exception as exc:
            decision = {
                "allowed": False,
                "reason": f"restart_guard_exception:{type(exc).__name__}",
            }
        output = {"claimed": True, "request": request, **decision}
        if not decision.get("allowed"):
            _atomic_write(
                blocked_path,
                {
                    "schema": BLOCKED_RESTART_SCHEMA,
                    "status": "blocked",
                    "observed_at_kst": now.isoformat(),
                    "main_bot_pid": main_bot_pid,
                    "request": request,
                    "decision": decision,
                    "runtime_effect": False,
                    "main_bot_restarted": False,
                    "samsung_service_mutated": False,
                    "orders_mutated": False,
                },
            )
        return output


def record_scheduled_restart_block(
    *,
    main_bot_pid: int,
    request: str,
    decision: dict,
    now: datetime | None = None,
    blocked_path: Path = DEFAULT_BLOCKED_RESTART_PATH,
) -> None:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    _atomic_write(
        blocked_path,
        {
            "schema": BLOCKED_RESTART_SCHEMA,
            "status": "blocked",
            "observed_at_kst": now.isoformat(),
            "main_bot_pid": main_bot_pid,
            "request": request,
            "decision": decision,
            "runtime_effect": False,
            "main_bot_restarted": False,
            "samsung_service_mutated": False,
            "orders_mutated": False,
        },
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--action",
        choices=("check", "prepare", "commit", "recover", "abort"),
        required=True,
    )
    parser.add_argument("--old-main-bot-pid", type=int, default=0)
    parser.add_argument("--new-main-bot-pid", type=int, default=0)
    parser.add_argument("--live-service-pid", type=int, default=0)
    parser.add_argument("--expected-authority-sha256", default="")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--authority-path", type=Path, default=DEFAULT_AUTHORITY_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.action == "check":
            output = restart_guard_decision(main_bot_pid=args.old_main_bot_pid)
            rc = 0 if output.get("allowed") else 3
        elif args.action == "prepare":
            output, rc = prepare_main_bot_handoff(
                old_main_bot_pid=args.old_main_bot_pid,
                confirmation=args.confirm,
                write=args.write,
                authority_path=args.authority_path,
                plan_path=args.plan_path,
            )
        elif args.action == "commit":
            output, rc = commit_main_bot_handoff(
                new_main_bot_pid=args.new_main_bot_pid,
                confirmation=args.confirm,
                write=args.write,
                authority_path=args.authority_path,
                plan_path=args.plan_path,
            )
        elif args.action == "recover":
            output, rc = recover_existing_main_bot_handoff(
                old_main_bot_pid=args.old_main_bot_pid,
                new_main_bot_pid=args.new_main_bot_pid,
                live_service_pid=args.live_service_pid,
                expected_authority_sha256=args.expected_authority_sha256,
                confirmation=args.confirm,
                write=args.write,
                authority_path=args.authority_path,
            )
        else:
            output, rc = abort_main_bot_handoff(
                old_main_bot_pid=args.old_main_bot_pid,
                confirmation=args.confirm,
                plan_path=args.plan_path,
            )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        output = {
            "status": "blocked",
            "reason": f"handoff_contract_error:{type(exc).__name__}",
        }
        rc = 3
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
