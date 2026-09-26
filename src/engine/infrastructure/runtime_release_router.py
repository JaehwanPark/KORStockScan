"""Route main-bot and scheduled tuning entrypoints to one reviewed release.

Deployment infrastructure only: this selector never approves dated trading policy.
Run by absolute filename with Python -I, not through a mutable package import.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

OWNED = {
    "preopen": ("threshold_cycle_preopen", "threshold_cycle_preopen_cron"),
    "postclose": ("threshold_cycle_postclose", "threshold_cycle_postclose_cron"),
    "controller": ("postclose_done_controller", "postclose_done_controller_cron"),
    "tuning": ("tuning_monitoring_postclose", "tuning_monitoring_postclose_cron"),
    "finalize": ("postclose_finalization", "postclose_finalization_cron"),
}
TAGS = {
    "THRESHOLD_CYCLE_PREOPEN": "preopen",
    "THRESHOLD_CYCLE_POSTCLOSE": "postclose",
    "POSTCLOSE_DONE_CONTROLLER": "controller",
    "TUNING_MONITORING_POSTCLOSE": "tuning",
    "POSTCLOSE_FINALIZATION_2155": "finalize",
    "UPDATE_KOSPI_EOD_2005": "eod",
    "DASHBOARD_DB_ARCHIVE_2050": "archive",
}
CRON_TARGETS = frozenset({"start", *TAGS.values()})
REQUIRED_CRON_TARGETS = CRON_TARGETS
OPERATIONS = ("start", "restart", *OWNED, "paired-replay", "eod", "archive", "buy-funnel", "holding-exit-sentinel")
RELEASE_SET_LOCK = "runtime_release_set.lock"
MAX_RELEASE_SET_UNITS = 256
CORE_SYSTEMD_UNITS = (
    "korstockscan-widget-signal-auto-trader.service",
    "korstockscan-low-price-two-leg-auto-expansion.service",
)


@contextmanager
def runtime_release_set_lock(workspace: Path):
    """Serialize a release-set check or a live owner transition."""
    lock_path = workspace / "data/runtime" / RELEASE_SET_LOCK
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o666)
    os.chmod(lock_path, 0o666)
    with os.fdopen(fd, "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("runtime_release_transition_in_progress") from exc
        yield


def _systemd_properties(unit: str, *, timeout_sec: float = 5) -> dict[str, str]:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            unit,
            "--no-pager",
            "--property=LoadState,ActiveState,SubState,MainPID,WorkingDirectory,ExecStart,Environment",
        ],
        capture_output=True,
        text=True,
            timeout=timeout_sec,
    )
    if result.returncode:
        raise ValueError(f"systemd_unit_unavailable:{unit}")
    return dict(
        line.split("=", 1)
        for line in result.stdout.splitlines()
        if "=" in line
    )


def _policy_environment_status(environment: str, unit: str) -> list[dict]:
    values = _environment_values(environment)
    checks = []
    for key, raw_path in values.items():
        if not key.endswith("_POLICY_PATH"):
            continue
        hash_key = f"{key[:-5]}_SHA256"
        expected = values.get(hash_key)
        if not Path(raw_path).is_absolute() or not re.fullmatch(
            r"[0-9a-f]{64}", expected or ""
        ):
            raise ValueError(f"systemd_policy_pin_invalid:{unit}:{key}")
        try:
            actual = hashlib.sha256(Path(raw_path).read_bytes()).hexdigest()
        except OSError as exc:
            raise ValueError(f"systemd_policy_file_unavailable:{unit}:{key}") from exc
        if actual != expected:
            raise ValueError(f"systemd_policy_hash_mismatch:{unit}:{key}")
        checks.append({"policy_key": key, "sha256": actual, "passed": True})
    return checks


def _environment_values(environment: str) -> dict[str, str]:
    values = {}
    for item in shlex.split(environment):
        key, separator, value = item.partition("=")
        if separator:
            values[key] = value
    return values


def _release_identity(
    workspace: Path, working_directory: str, unit: str, runtime_commit: str | None
) -> dict:
    if not working_directory or not Path(working_directory).is_absolute():
        raise ValueError(f"systemd_working_directory_missing:{unit}")
    path = Path(working_directory).resolve(strict=True)
    root = path.parent if path.name == "src" else path
    managed = (
        workspace.parent / f"{workspace.name}-runtime-releases"
    ).resolve(strict=True)
    if root.parent != managed:
        raise ValueError(f"systemd_release_root_outside_managed_directory:{unit}")
    try:
        commit = git(root, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        # Immutable release exports may intentionally omit .git. In that case
        # require the systemd full-commit pin and a matching release label.
        if not re.fullmatch(r"[0-9a-f]{40}", runtime_commit or ""):
            raise ValueError(f"systemd_release_commit_unattested:{unit}")
        release_hash = re.search(r"-([0-9a-f]{8,40})$", root.name)
        if not release_hash or not runtime_commit.startswith(release_hash.group(1)):
            raise ValueError(f"systemd_release_label_commit_mismatch:{unit}")
        return {
            "release_root": str(root),
            "git_commit": runtime_commit,
            "source_integrity": "git_metadata_unavailable_commit_pin_and_release_label_only",
        }
    if runtime_commit and runtime_commit != commit:
        raise ValueError(f"systemd_runtime_commit_mismatch:{unit}")
    if git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        "src",
        "deploy",
        "restart.sh",
    ):
        raise ValueError(f"systemd_release_source_dirty:{unit}")
    return {
        "release_root": str(root),
        "git_commit": commit,
        "source_integrity": "git_commit_and_clean_runtime_source",
    }


def check_release_set(workspace: Path, selected_root: Path, selected_commit: str) -> dict:
    """Read-only consistency check for separately routed live code owners."""
    units = list(CORE_SYSTEMD_UNITS)
    listed = subprocess.run(
        [
            "systemctl", "list-units", "--type=service", "--all", "--no-legend",
            "--plain", "korstockscan-low-price-two-leg@*.service",
            "korstockscan-low-price-two-leg-preflight@*.service",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if listed.returncode:
        raise ValueError("systemd_episode_unit_inventory_unavailable")
    for line in listed.stdout.splitlines():
        unit = line.split(None, 1)[0] if line.split() else ""
        if unit and unit not in units:
            units.append(unit)
    if len(units) > MAX_RELEASE_SET_UNITS:
        raise ValueError("systemd_release_set_inventory_limit_exceeded")

    owners = []
    deadline = time.monotonic() + 30
    for unit in units:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("systemd_release_set_check_timeout")
        fields = _systemd_properties(unit, timeout_sec=min(3, remaining))
        if fields.get("LoadState") != "loaded":
            raise ValueError(f"systemd_unit_not_loaded:{unit}")
        environment = fields.get("Environment", "")
        env_values = _environment_values(environment)
        identity = _release_identity(
            workspace,
            fields.get("WorkingDirectory", ""),
            unit,
            env_values.get("KORSTOCKSCAN_RUNTIME_GIT_COMMIT"),
        )
        exec_start = fields.get("ExecStart", "")
        if identity["release_root"] not in exec_start:
            raise ValueError(f"systemd_exec_release_mismatch:{unit}")
        for key in ("PROJECT_DIR", "KORSTOCKSCAN_PROJECT_DIR", "PYTHONPATH"):
            value = env_values.get(key)
            if value and Path(value).resolve() != Path(identity["release_root"]):
                raise ValueError(f"systemd_release_environment_mismatch:{unit}:{key}")
        runtime_commit = env_values.get("KORSTOCKSCAN_RUNTIME_GIT_COMMIT")
        if runtime_commit and runtime_commit != identity["git_commit"]:
            raise ValueError(f"systemd_runtime_commit_mismatch:{unit}")
        policy_checks = _policy_environment_status(environment, unit)
        owners.append(
            {
                "unit": unit,
                **identity,
                "active_state": fields.get("ActiveState", "unknown"),
                "sub_state": fields.get("SubState", "unknown"),
                "main_pid": int(fields.get("MainPID", "0") or 0),
                "policy_pin_count": len(policy_checks),
                "policy_pins_passed": all(check["passed"] for check in policy_checks),
            }
        )
    episode_units = [
        owner
        for owner in owners
        if owner["unit"].startswith("korstockscan-low-price-two-leg@")
        or owner["unit"].startswith("korstockscan-low-price-two-leg-preflight@")
    ]
    release_counts = {}
    active_counts = {}
    profile_policy_checks_passed = 0
    for owner in episode_units:
        release_counts[owner["git_commit"]] = release_counts.get(owner["git_commit"], 0) + 1
        state = owner["active_state"]
        active_counts[state] = active_counts.get(state, 0) + 1
        profile_policy_checks_passed += owner["policy_pin_count"]
    selection = json.loads(
        (workspace / "data/runtime/runtime_release_selection.json").read_text()
    )
    receipt = selection.get("actual_pid_receipt")
    if not isinstance(receipt, dict):
        main_pid_binding = {"status": "not_attested", "pid": None}
    else:
        try:
            receipt_pid = int(receipt.get("pid", 0))
            receipt_cwd = Path(os.readlink(f"/proc/{receipt_pid}/cwd")).resolve(strict=True)
            receipt_matches = (
                receipt_pid > 0
                and receipt.get("release_root") == str(selected_root)
                and receipt.get("git_commit") == selected_commit
                and receipt_cwd == (selected_root / "src").resolve(strict=True)
            )
            main_pid_binding = {
                "status": (
                    "matches_selected_release"
                    if receipt_matches
                    else "stale_or_mismatched"
                ),
                "pid": receipt_pid,
            }
        except (OSError, TypeError, ValueError):
            main_pid_binding = {"status": "receipt_process_unavailable", "pid": receipt.get("pid")}
    return {
        "schema": "runtime_release_set_check_v1",
        "runtime_effect": False,
        "functional_runtime_health": "not_assessed",
        "selected_main": {
            "release_root": str(selected_root),
            "git_commit": selected_commit,
        },
        "main_pid_binding": main_pid_binding,
        "systemd_owners": owners[: len(CORE_SYSTEMD_UNITS)],
        "owner_count": len(owners),
        "episode_profile_inventory": {
            "loaded_units_checked": len(episode_units),
            "release_commit_counts": release_counts,
            "active_state_counts": active_counts,
            "policy_pins_verified": profile_policy_checks_passed,
            "policy_pin_failures": 0,
        },
        "status": "passed",
        "note": "Separate owner release pins are allowed; PID policy consumption and natural function acceptance remain separate checks.",
    }


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def selected_release(workspace: Path) -> tuple[Path, str]:
    workspace = workspace.resolve(strict=True)
    selection = json.loads(
        (workspace / "data/runtime/runtime_release_selection.json").read_text()
    )
    if (
        not isinstance(selection, dict)
        or selection.get("schema") != "runtime_release_selection_v1"
    ):
        raise ValueError("release_selection_schema_invalid")
    if selection.get("workspace") != str(workspace):
        raise ValueError("release_workspace_mismatch")
    raw_root = selection.get("release_root")
    if not isinstance(raw_root, str) or not Path(raw_root).is_absolute():
        raise ValueError("release_root_invalid")
    root = Path(raw_root).resolve(strict=True)
    release_parent = workspace.parent / f"{workspace.name}-runtime-releases"
    if root.parent != release_parent.resolve(strict=True) or str(root) != raw_root:
        raise ValueError("release_root_outside_managed_directory")
    commit = selection.get("git_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("release_commit_invalid")
    if git(root, "rev-parse", "HEAD") != commit:
        raise ValueError("release_commit_mismatch")
    if git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        "src",
        "deploy",
        "restart.sh",
    ):
        raise ValueError("release_source_dirty")
    for name in ("data", "logs", "tmp", ".venv", "docs", "restart.flag"):
        shared = root / name
        if not shared.is_symlink() or shared.resolve() != (workspace / name).resolve():
            raise ValueError(f"release_shared_path_mismatch:{name}")
        if name != "restart.flag" and not shared.is_dir():
            raise ValueError(f"release_shared_path_missing:{name}")
    return root, commit


def record_runtime_pid_consumption(
    workspace: Path,
    *,
    pid: int,
    release_root: Path,
    git_commit: str,
) -> dict:
    """Atomically attest the bot child that consumed the selected release.

    This records deployment provenance only.  It neither selects a release nor
    changes a dated policy, and it deliberately fails closed when the child has
    not inherited the selected release's ``src`` working directory.
    """
    if pid <= 0:
        raise ValueError("runtime_pid_invalid")
    workspace = workspace.resolve(strict=True)
    release_root = release_root.resolve(strict=True)
    lock_path = workspace / "data/runtime/runtime_release_selection.lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        selected_root, selected_commit = selected_release(workspace)
        if release_root != selected_root:
            raise ValueError("runtime_pid_release_root_mismatch")
        if git_commit != selected_commit:
            raise ValueError("runtime_pid_commit_mismatch")
        try:
            process_cwd = Path(os.readlink(f"/proc/{pid}/cwd")).resolve(strict=True)
        except OSError as exc:
            raise ValueError("runtime_pid_not_running") from exc
        expected_cwd = (selected_root / "src").resolve(strict=True)
        if process_cwd != expected_cwd:
            raise ValueError("runtime_pid_cwd_mismatch")
        manifest_path = workspace / "data/runtime/runtime_release_selection.json"
        selection = json.loads(manifest_path.read_text())
        # Re-check the current manifest while holding the receipt lock.  A
        # selection made after selected_release() must never receive this PID.
        if (
            selection.get("release_root") != str(selected_root)
            or selection.get("git_commit") != selected_commit
        ):
            raise ValueError("runtime_selection_changed_before_pid_receipt")
        recorded_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        receipt = {
            "schema": "runtime_release_pid_receipt_v1",
            "pid": pid,
            "recorded_at_kst": recorded_at,
            "release_root": str(selected_root),
            "git_commit": selected_commit,
            "process_cwd": str(process_cwd),
            "attestation": "launcher_child_cwd_matches_selected_release",
        }
        selection["actual_pid_consumed"] = True
        selection["actual_pid_receipt"] = receipt
        selection["actual_pid_consumption_status"] = "pid_receipt_attested"
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=manifest_path.parent, delete=False
        ) as temporary:
            json.dump(selection, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.chmod(temporary_path, manifest_path.stat().st_mode & 0o777)
        os.replace(temporary_path, manifest_path)
    return receipt


def make_plan(
    workspace: Path, root: Path, commit: str, operation: str, target_date: str
) -> dict:
    if date.fromisoformat(target_date).isoformat() != target_date:
        raise ValueError("target_date_invalid")
    cwd = root
    if operation in OWNED:
        script, owner = OWNED[operation]
        command = [
            "/bin/bash",
            str(root / "deploy/run_with_owned_log.sh"),
            "--owner",
            owner,
            "--log",
            str(workspace / "logs" / f"{owner}.log"),
            str(root / "deploy" / f"run_{script}.sh"),
            target_date,
        ]
    elif operation == "buy-funnel":
        command = ["/bin/bash", str(root / "deploy/run_buy_funnel_sentinel_intraday.sh"), target_date]
    elif operation == "holding-exit-sentinel":
        command = ["/bin/bash", str(root / "deploy/run_holding_exit_sentinel_intraday.sh"), target_date]
    elif operation == "paired-replay":
        command = [
            "/bin/bash",
            str(root / "deploy/run_ai_entry_setup_paired_replay_postclose.sh"),
            target_date,
        ]
    elif operation == "archive":
        command = [
            "/bin/bash",
            str(root / "deploy/run_dashboard_db_archive_cron.sh"),
            "0",
        ]
    elif operation == "eod":
        command = [
            str(root / ".venv/bin/python"),
            str(root / "src/utils/update_kospi.py"),
        ]
    elif operation == "restart":
        command = ["/bin/bash", str(root / "restart.sh")]
    elif operation == "start":
        cwd = root / "src"
        # tmux may have a long-lived server with an older environment. Set the
        # release context in the actual child command, not only the client env.
        child = shlex.join(
            [
                "/usr/bin/env",
                f"PROJECT_DIR={root}",
                f"PYTHONPATH={root}",
                f"VENV_PY={root}/.venv/bin/python",
                "/bin/bash",
                str(root / "src/run_bot.sh"),
            ]
        )
        command = [
            "/usr/bin/tmux",
            "new-session",
            "-d",
            "-s",
            "bot",
            "-c",
            str(cwd),
            child,
        ]
    else:
        raise ValueError("operation_invalid")
    return {
        "release_root": str(root),
        "git_commit": commit,
        "operation": operation,
        "target_date": target_date,
        "cwd": str(cwd),
        "command": command,
        "policy_authority": "existing_exact_date_gates_unchanged",
    }


def render_crontab(original: str, workspace: Path) -> str:
    """Replace the eight installed command prefixes, preserving schedules/env/tails.

    Missing, duplicate or unfamiliar entrypoints fail closed. Other services,
    machine timers and intraday observers are deliberately outside this router.
    """
    router = f"bash {workspace}/deploy/run_runtime_release.sh"
    legacy_start = (
        f"/usr/bin/tmux new-session -d -s bot '/bin/bash -c \"cd {workspace}/src "
        "&& source ../.venv/bin/activate && ./run_bot.sh\"'"
    )
    simple_start = (
        f"/usr/bin/tmux new-session -d -s bot 'cd {workspace}/src && ./run_bot.sh'"
    )
    # Only leading shell assignments may precede an execution owner. A route
    # appearing in echo/printf, a conditional, or a comment is not execution.
    env_prefix = re.compile(
        r"""(?:[A-Za-z_][A-Za-z0-9_]*=(?:[^\s'";&|<>]+|'[^']*'|"[^"]*")+\s+)*"""
    )
    seen: list[str] = []
    result = []
    for line in original.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            result.append(line)
            continue
        tag = line.rsplit("#", 1)[-1].strip() if "#" in line else ""
        op = TAGS.get(tag)
        if tag == "RUNTIME_RELEASE_START" or (
            "/usr/bin/tmux new-session -d -s bot " in line
            and f"cd {workspace}/src " in line
        ):
            op = "start"
        if op is None:
            result.append(line)
            continue
        seen.append(op)
        scheduled = re.fullmatch(r"(\s*(?:\S+\s+){5})(.+)", line)
        if not scheduled:
            raise ValueError("cron_schedule_invalid")
        schedule, command = scheduled.groups()
        prefix = env_prefix.match(command).group()
        command = command[len(prefix) :]
        desired = f"{router} {op}"
        if op in OWNED:
            script, owner = OWNED[op]
            old = (
                f"bash {workspace}/deploy/run_with_owned_log.sh --owner {owner} "
                f"--log {workspace}/logs/{owner}.log {workspace}/deploy/run_{script}.sh"
            )
        elif op == "paired-replay":
            old = f"{workspace}/deploy/run_ai_entry_setup_paired_replay_postclose.sh"
        elif op == "eod":
            old = f"cd {workspace} && {workspace}/.venv/bin/python src/utils/update_kospi.py"
        elif op == "archive":
            old = f"{workspace}/deploy/run_dashboard_db_archive_cron.sh 0"
        else:
            old = legacy_start
        allowed = (desired, old, simple_start) if op == "start" else (desired, old)
        matched = next(
            (c for c in allowed if command == c or command.startswith(c + " ")), None
        )
        if matched is None:
            raise ValueError(f"cron_command_unrecognized:{op}")
        tail = command[len(matched) :]
        arguments, marker, comment = tail.partition("#")
        if op in OWNED or op == "paired-replay":
            date_arg = r" $(TZ=Asia/Seoul date +\%F)"
            if not arguments.startswith(date_arg):
                raise ValueError(f"cron_target_date_unrecognized:{op}")
            arguments = arguments[len(date_arg) :]
        # Do not accept --print-plan, an extra execution, or shell conditionals
        # as an installed scheduled worker. Preserve conventional log redirects.
        if not re.fullmatch(r"(?:\s+(?:>>?\s+[^\s;&|<>]+|2>&1))*\s*", arguments):
            raise ValueError(f"cron_arguments_unrecognized:{op}")
        if op == "start" and not marker:
            tail = tail.rstrip() + " # RUNTIME_RELEASE_START"
        elif op == "start" and comment.strip() != "RUNTIME_RELEASE_START":
            raise ValueError("cron_start_marker_unrecognized")
        line = schedule + prefix + desired + tail
        result.append(line)
    if not REQUIRED_CRON_TARGETS.issubset(seen) or len(seen) != len(set(seen)):
        raise ValueError("cron_target_missing_or_duplicate")
    return "\n".join(result) + "\n"


def manage_cron(workspace: Path, install: bool) -> None:
    if not install:
        old = subprocess.check_output(["crontab", "-l"], text=True)
        if render_crontab(old, workspace) != old:
            raise ValueError("cron_release_routing_not_installed")
        print(
            json.dumps(
                {
                    "cron_routing_verified": True,
                    "required_targets": len(REQUIRED_CRON_TARGETS),
                }
            )
        )
        return
    # Serialize router installs. Re-read just before writing to avoid clobbering
    # an unrelated session's edits observed during validation.
    with (workspace / "data/runtime/runtime_release_cron.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = subprocess.check_output(["crontab", "-l"], text=True)
        new = render_crontab(old, workspace)
        if new != old:
            backup_dir = Path(
                tempfile.mkdtemp(prefix="runtime-release-cron-", dir=workspace / "tmp")
            )
            (backup_dir / "before.crontab").write_text(old)
            (backup_dir / "after.crontab").write_text(new)
            if subprocess.check_output(["crontab", "-l"], text=True) != old:
                raise ValueError("cron_changed_during_install")
            subprocess.run(["crontab", "-"], input=new, text=True, check=True)
            if subprocess.check_output(["crontab", "-l"], text=True) != new:
                raise ValueError("cron_install_readback_mismatch")
            print(json.dumps({"cron_backup": str(backup_dir)}))
        print(
            json.dumps(
                {
                    "cron_routing_verified": True,
                    "required_targets": len(REQUIRED_CRON_TARGETS),
                }
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=OPERATIONS)
    parser.add_argument(
        "target_date",
        nargs="?",
        default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat(),
    )
    parser.add_argument("--print-plan", action="store_true")
    parser.add_argument("--record-pid", type=int)
    parser.add_argument("--record-release-root")
    parser.add_argument("--record-git-commit")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check-cron", action="store_true")
    group.add_argument("--install-cron", action="store_true")
    group.add_argument("--check-release-set", action="store_true")
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    try:
        root, commit = selected_release(workspace)
        if args.record_pid is not None:
            if (
                args.operation
                or args.print_plan
                or args.check_cron
                or args.install_cron
                or args.check_release_set
                or not args.record_release_root
                or not args.record_git_commit
            ):
                raise ValueError("runtime_pid_receipt_arguments_invalid")
            receipt = record_runtime_pid_consumption(
                workspace,
                pid=args.record_pid,
                release_root=Path(args.record_release_root),
                git_commit=args.record_git_commit,
            )
            print(json.dumps(receipt), flush=True)
            return 0
        if args.check_cron or args.install_cron:
            if args.operation or args.print_plan:
                raise ValueError("cron_mode_cannot_execute_operation")
            if args.install_cron:
                with runtime_release_set_lock(workspace):
                    manage_cron(workspace, True)
            else:
                manage_cron(workspace, False)
            return 0
        if args.check_release_set:
            if args.operation or args.print_plan:
                raise ValueError("release_set_check_cannot_execute_operation")
            with runtime_release_set_lock(workspace):
                root, commit = selected_release(workspace)
                report = check_release_set(workspace, root, commit)
            print(json.dumps(report, sort_keys=True), flush=True)
            return 0
        if not args.operation:
            raise ValueError("operation_required")
        plan = make_plan(workspace, root, commit, args.operation, args.target_date)
        if args.print_plan:
            print(json.dumps(plan), flush=True)
            return 0
        if args.operation not in {"start", "restart"}:
            print(json.dumps(plan), flush=True)
        env = dict(os.environ)
        env.pop("PYTHONHOME", None)
        env.update(
            PROJECT_DIR=str(root),
            PYTHONPATH=str(root),
            VENV_PY=str(root / ".venv/bin/python"),
        )
        os.chdir(plan["cwd"])
        if args.operation in {"start", "restart"}:
            # Hold the shared deployment lock through the transition, never for
            # the lifetime of the main bot. Re-resolve the selector after lock.
            with runtime_release_set_lock(workspace):
                root, commit = selected_release(workspace)
                plan = make_plan(
                    workspace, root, commit, args.operation, args.target_date
                )
                print(json.dumps(plan), flush=True)
                env.update(
                    PROJECT_DIR=str(root),
                    PYTHONPATH=str(root),
                    VENV_PY=str(root / ".venv/bin/python"),
                )
                os.chdir(plan["cwd"])
                if args.operation == "start":
                    with (workspace / "data/runtime/runtime_release_start.lock").open(
                        "a"
                    ) as start_lock:
                        fcntl.flock(start_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        existing = subprocess.run(
                            ["pgrep", "-f", "[/]python bot_main[.]py$"],
                            capture_output=True,
                        )
                        if existing.returncode != 1:
                            raise ValueError(
                                "bot_already_running_or_process_check_failed"
                            )
                        return subprocess.run(plan["command"], env=env, check=False).returncode
                return subprocess.run(plan["command"], env=env, check=False).returncode
        os.execvpe(plan["command"][0], plan["command"], env)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"runtime_release_route_blocked: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
