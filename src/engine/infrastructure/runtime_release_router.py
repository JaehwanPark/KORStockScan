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
        if op == "start":
            schedule = line.split(maxsplit=5)[:5]
            if len(schedule) != 5:
                raise ValueError("cron_start_schedule_invalid")
            line = " ".join(schedule) + f" {router} start # RUNTIME_RELEASE_START"
        elif not re.search(
            re.escape(f"{router} {op}") + r"(?=\s|$)", line.partition("#")[0]
        ):
            if op in OWNED:
                script, owner = OWNED[op]
                old = (
                    f"bash {workspace}/deploy/run_with_owned_log.sh --owner {owner} "
                    f"--log {workspace}/logs/{owner}.log {workspace}/deploy/run_{script}.sh"
                )
            elif op == "paired-replay":
                old = (
                    f"{workspace}/deploy/run_ai_entry_setup_paired_replay_postclose.sh"
                )
            elif op == "eod":
                old = f"cd {workspace} && {workspace}/.venv/bin/python src/utils/update_kospi.py"
            else:
                old = f"{workspace}/deploy/run_dashboard_db_archive_cron.sh 0"
            if line.count(old) != 1:
                raise ValueError(f"cron_command_unrecognized:{op}")
            line = line.replace(old, f"{router} {op}", 1)
        result.append(line)
    expected = {"start", *TAGS.values()}
    if set(seen) != expected or len(seen) != len(expected):
        raise ValueError("cron_target_missing_or_duplicate")
    return "\n".join(result) + "\n"


def manage_cron(workspace: Path, install: bool) -> None:
    # Serialize router installs. Re-read just before writing to avoid clobbering
    # an unrelated session's edits observed during validation.
    with (workspace / "data/runtime/runtime_release_cron.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        old = subprocess.check_output(["crontab", "-l"], text=True)
        new = render_crontab(old, workspace)
        if not install and new != old:
            raise ValueError("cron_release_routing_not_installed")
        if install and new != old:
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check-cron", action="store_true")
    group.add_argument("--install-cron", action="store_true")
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    try:
        root, commit = selected_release(workspace)
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
