"""Route main-bot and scheduled tuning entrypoints to one reviewed release.

Deployment infrastructure only: this selector never approves dated trading policy.
Run by absolute filename with Python -I, not through a mutable package import.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
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
    "AI_ENTRY_SETUP_PAIRED_REPLAY_POSTCLOSE": "paired-replay",
    "POSTCLOSE_DONE_CONTROLLER": "controller",
    "TUNING_MONITORING_POSTCLOSE": "tuning",
    "POSTCLOSE_FINALIZATION_2155": "finalize",
    "UPDATE_KOSPI_EOD_2005": "eod",
    "DASHBOARD_DB_ARCHIVE_2050": "archive",
}
OPERATIONS = ("start", "restart", *OWNED, "paired-replay", "eod", "archive")


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
    """Replace only nine known command prefixes, preserving schedules/env/tails.

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
    expected = {"start", *TAGS.values()}
    if set(seen) != expected or len(seen) != len(expected):
        raise ValueError("cron_target_missing_or_duplicate")
    return "\n".join(result) + "\n"


def manage_cron(workspace: Path, install: bool) -> None:
    if not install:
        old = subprocess.check_output(["crontab", "-l"], text=True)
        if render_crontab(old, workspace) != old:
            raise ValueError("cron_release_routing_not_installed")
        print(json.dumps({"cron_routing_verified": True, "targets": 9}))
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
        print(json.dumps({"cron_routing_verified": True, "targets": 9}))


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
            manage_cron(workspace, args.install_cron)
            return 0
        if not args.operation:
            raise ValueError("operation_required")
        plan = make_plan(workspace, root, commit, args.operation, args.target_date)
        print(json.dumps(plan), flush=True)
        if args.print_plan:
            return 0
        env = dict(os.environ)
        env.pop("PYTHONHOME", None)
        env.update(
            PROJECT_DIR=str(root),
            PYTHONPATH=str(root),
            VENV_PY=str(root / ".venv/bin/python"),
        )
        os.chdir(plan["cwd"])
        if args.operation == "start":
            # Hold only until tmux creation completes, never for the bot lifetime.
            with (workspace / "data/runtime/runtime_release_start.lock").open(
                "a"
            ) as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                existing = subprocess.run(
                    ["pgrep", "-f", "[/]python bot_main[.]py$"], capture_output=True
                )
                if existing.returncode != 1:
                    raise ValueError("bot_already_running_or_process_check_failed")
                return subprocess.run(plan["command"], env=env, check=False).returncode
        os.execvpe(plan["command"][0], plan["command"], env)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"runtime_release_route_blocked: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
