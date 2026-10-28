"""Route main-bot and scheduled tuning entrypoints to one reviewed release.

Deployment infrastructure only: this selector never approves dated trading policy.
Run by absolute filename with Python -I, not through a mutable package import.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
from datetime import date, datetime
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import stat
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
    "POSTCLOSE_FINALIZATION_0535": "finalize",
    "UPDATE_KOSPI_EOD_2005": "eod",
    "DASHBOARD_DB_ARCHIVE_2050": "archive",
}
LEGACY_TAGS = {
    "POSTCLOSE_FINALIZATION_0500": "finalize",
    "POSTCLOSE_FINALIZATION_2155": "finalize",
    "POSTCLOSE_FINALIZATION_0600": "finalize",
}
# These are three schedule identities for one observer operation. Keep them
# separate from the uniquely scheduled pipeline operations in TAGS/OWNED.
SNAPSHOT_CRON_TAGS = frozenset(
    {
        "RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09",
        "RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11",
        "RUN_MONITOR_SNAPSHOT_1200",
    }
)
CRON_TARGETS = frozenset({"start", *TAGS.values()})
REQUIRED_CRON_TARGETS = CRON_TARGETS
OPERATIONS = (
    "start",
    "restart",
    "validate-startup",
    *OWNED,
    "paired-replay",
    "eod",
    "archive",
    "buy-funnel",
    "pre-submit-source",
    "holding-exit-sentinel",
    "error-detection",
    "log-retention",
    "snapshot-archive",
    "monitor-snapshot",
)
RELEASE_SET_LOCK = "runtime_release_set.lock"
MAX_RELEASE_SET_UNITS = 256
STARTUP_CONSUMPTION_TIMEOUT_SEC = 150
MAX_STARTUP_RECEIPT_BYTES = 4 * 1024 * 1024
CORE_SYSTEMD_UNITS = ("korstockscan-low-price-two-leg-auto-expansion.service",)


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


@contextmanager
def scheduled_execution_lease(workspace: Path, *, exclusive: bool = False):
    """Pin scheduled readers across their children, independently of writers.

    Followers may coexist and take native family/release writer locks. A
    deployment yields before preflight if any follower is already executing;
    a new follower waits before resolving the selector during a deployment.
    """
    path = Path(workspace) / "data/runtime/runtime_scheduled_execution.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o666)
    with os.fdopen(fd, "a") as lock:
        opened = os.fstat(lock.fileno())
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("runtime_scheduled_execution_lock_invalid")
        os.fchmod(lock.fileno(), 0o666)
        try:
            fcntl.flock(
                lock, fcntl.LOCK_EX | fcntl.LOCK_NB if exclusive else fcntl.LOCK_SH
            )
        except BlockingIOError as exc:
            raise ValueError("runtime_scheduled_execution_active") from exc
        current = path.lstat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("runtime_scheduled_execution_lock_changed")
        yield lock.fileno()


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
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
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
    managed = (workspace.parent / f"{workspace.name}-runtime-releases").resolve(
        strict=True
    )
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


def check_release_set(
    workspace: Path, selected_root: Path, selected_commit: str
) -> dict:
    """Read-only consistency check for separately routed live code owners."""
    main_only = (
        workspace / "data/runtime/retirements/main-only-retirement.json"
    ).is_file()
    if main_only:
        _validate_retired_surfaces(workspace, selected_root)
    units = [] if main_only else list(CORE_SYSTEMD_UNITS)
    listed = subprocess.run(
        [
            "systemctl",
            "list-units",
            "--type=service",
            "--all",
            "--no-legend",
            "--plain",
            "korstockscan-low-price-two-leg@*.service",
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
            if main_only:
                fields = _systemd_properties(unit)
                if int(fields.get("MainPID", "0") or 0) or fields.get(
                    "ActiveState"
                ) in {"active", "activating", "reloading"}:
                    raise ValueError(f"retired_automatic_owner_running:{unit}")
                continue
            units.append(unit)
    if len(units) > MAX_RELEASE_SET_UNITS:
        raise ValueError("systemd_release_set_inventory_limit_exceeded")

    owners = []
    retired_masked = []
    retired_instances = set()
    for receipt in _episode_retirement_receipts(workspace):
        closed = {
            unit
            for unit in _retirement_units(_retirement_symbols(receipt))
            if unit.endswith(".service")
        }
        claimed = receipt.get("masked_instances")
        if (
            receipt.get("state") == "terminal"
            and isinstance(claimed, list)
            and len(claimed) == len(closed)
            and set(claimed) == closed
        ):
            retired_instances.update(closed)
    deadline = time.monotonic() + 30
    for unit in units:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("systemd_release_set_check_timeout")
        fields = _systemd_properties(unit, timeout_sec=min(3, remaining))
        if (
            fields.get("LoadState") == "masked"
            and unit in retired_instances
            and fields.get("ActiveState") in {"inactive", "failed"}
            and fields.get("MainPID") == "0"
        ):
            retired_masked.append(unit)
            continue
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
        release_counts[owner["git_commit"]] = (
            release_counts.get(owner["git_commit"], 0) + 1
        )
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
            receipt_cwd = Path(os.readlink(f"/proc/{receipt_pid}/cwd")).resolve(
                strict=True
            )
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
            main_pid_binding = {
                "status": "receipt_process_unavailable",
                "pid": receipt.get("pid"),
            }
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
        "retired_masked_units": sorted(retired_masked),
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


def _retirement_digest(body):
    return hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    ).hexdigest()


def _retirement_profiles():
    # The router runs with Python -I. Read the adjacent reviewed guard's data
    # without importing a mutable application package or honoring PYTHONPATH.
    import ast

    path = (
        Path(__file__).resolve().parents[3] / "src/trading/config/owner_retirement.py"
    )
    tree = ast.parse(path.read_text())
    profiles = next(
        (
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "RETIRED_EPISODE_PROFILES"
                for target in node.targets
            )
        ),
        None,
    )
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("retirement_guard_profile_registry_invalid")
    return profiles


def _retirement_symbols(receipt):
    if receipt.get("schema") == "symbol_owner_retirement_transition_v1":
        if receipt.get("symbol") != "034020":
            raise ValueError("retirement_symbol_scope_invalid")
        return ("034020",)
    symbols = receipt.get("symbols")
    if (
        receipt.get("schema") != "symbol_owner_retirement_transition_v2"
        or not isinstance(symbols, list)
        or not symbols
        or symbols != sorted(set(symbols))
        or not set(symbols).issubset(_retirement_profiles())
    ):
        raise ValueError("retirement_symbol_scope_invalid")
    return tuple(symbols)


def _retirement_units(scope):
    profiles = _retirement_profiles()
    result = []
    for profile in sorted(profile for symbol in scope for profile in profiles[symbol]):
        stem = "korstockscan-low-price-two-leg-" + profile.replace("_", "-")
        result.extend(
            (
                stem + ".timer",
                stem + "-preflight.timer",
                f"korstockscan-low-price-two-leg@{profile}.service",
                f"korstockscan-low-price-two-leg-preflight@{profile}.service",
            )
        )
    return result


def _episode_retirement_receipts(workspace):
    directory = workspace / "data/runtime/retirements"
    paths = sorted(directory.glob("*episode-retirement.json")) + sorted(
        directory.glob("episode-retirement-*.json")
    )
    result = []
    for path in paths:
        receipt = json.loads(path.read_text())
        scope = _retirement_symbols(receipt)
        if (
            receipt.get("state") not in {"entry_retired", "terminal"}
            or receipt.get("owner") != "episode"
            or receipt.get("receipt_sha256")
            != _retirement_digest(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"}
            )
        ):
            raise ValueError("symbol_owner_retirement_receipt_invalid")
        if receipt["schema"] == "symbol_owner_retirement_transition_v2":
            expected = sorted(
                profile
                for symbol in scope
                for profile in _retirement_profiles()[symbol]
            )
            if receipt.get("profile_ids") != expected or receipt.get(
                "units"
            ) != _retirement_units(scope):
                raise ValueError("retirement_profile_scope_invalid")
        result.append(receipt)
    return result


def _validate_retired_surfaces(workspace: Path, root: Path) -> None:
    family_receipt = workspace / "data/runtime/retirements/main-only-retirement.json"
    if family_receipt.exists():
        body = json.loads(family_receipt.read_text())
        if (
            body.get("schema") != "main_only_automatic_owner_retirement_v1"
            or body.get("management") != "operator_manual"
            or body.get("retired_owners") != ["episode", "widget_auto_trade"]
            or body.get("receipt_sha256")
            != _retirement_digest(
                {k: v for k, v in body.items() if k != "receipt_sha256"}
            )
        ):
            raise ValueError("main_only_retirement_receipt_invalid")
        guard = root / "src/trading/config/owner_retirement.py"
        guard_sha = (
            hashlib.sha256(guard.read_bytes()).hexdigest() if guard.is_file() else ""
        )
        original_guard = body.get("guard_file_sha256")
        # Exact Black-only succession of the permanently retired owner guard.
        # Preserve the original receipt and reject every other source change.
        reviewed_format = (
            "d76ab535d13f65ee10df85e5a7deeb1bbba46af756820bbd19101d258c26794a",
            "dc197f249818c481db7d835317dbf858a916f5c71bd7e5c483abc334c212753f",
        )
        if (
            guard_sha != original_guard
            and (original_guard, guard_sha) != reviewed_format
        ):
            raise ValueError("release_restores_retired_automatic_owner_guard")
        for path in body.get("removed_surfaces", []):
            candidate = Path(path)
            if (
                candidate.is_absolute()
                or ".." in candidate.parts
                or not candidate.parts
                or candidate.parts[0] not in {"src", "deploy"}
            ):
                raise ValueError("main_only_retirement_surface_invalid")
            if (root / candidate).exists():
                raise ValueError("release_restores_retired_automatic_owner_surface")
        if not body.get("removed_surfaces"):
            raise ValueError("main_only_retirement_surfaces_missing")
        return
    receipt = workspace / "data/runtime/retirements/widget-retirement-2026-10-06.json"
    for owner in _episode_retirement_receipts(workspace):
        guard = root / "src/trading/config/owner_retirement.py"
        guard_sha = (
            hashlib.sha256(guard.read_bytes()).hexdigest() if guard.is_file() else ""
        )
        if guard_sha != owner.get("guard_file_sha256"):
            revision_path = (
                workspace
                / "data/runtime/retirements/guard_revisions"
                / (owner["receipt_sha256"] + "-" + guard_sha + ".json")
            )
            if not revision_path.is_file():
                raise ValueError("release_restores_permanently_retired_episode_owner")
            revision = json.loads(revision_path.read_text())
            if (
                revision.get("schema") != "retirement_guard_revision_v1"
                or revision.get("state") != "reviewed_code_only"
                or revision.get("predecessor_receipt_sha256") != owner["receipt_sha256"]
                or revision.get("predecessor_guard_sha256")
                != owner["guard_file_sha256"]
                or revision.get("guard_file_sha256") != guard_sha
                or revision.get("preserved_symbols") != list(_retirement_symbols(owner))
                or revision.get("runtime_effect") is not False
                or revision.get("receipt_sha256")
                != _retirement_digest(
                    {k: v for k, v in revision.items() if k != "receipt_sha256"}
                )
            ):
                raise ValueError("retirement_guard_revision_invalid")
    if not receipt.exists():
        return
    body = json.loads(receipt.read_text())
    if (
        body.get("schema") != "widget_retirement_transition_v1"
        or body.get("state") != "terminal"
        or body.get("owner") != "widget_auto_trade"
    ):
        raise ValueError("widget_retirement_receipt_invalid")
    surfaces = (
        "src/trading/widget_auto_trade/engine.py",
        "src/web/samsung_price_widget_routes.py",
        "deploy/run_widget_evaluation.sh",
        "deploy/systemd/korstockscan-widget-signal-auto-trader.service",
    )
    if any((root / name).exists() for name in surfaces):
        raise ValueError("release_restores_permanently_retired_widget")


def _assert_research_transition_readable(workspace: Path) -> None:
    if __package__:
        from .research_release_transition import assert_readable

        assert_readable(workspace / "data")
        return
    # The installed wrapper runs this file with -I. Load only its exact
    # siblings, without importing packages from cwd or PYTHONPATH.
    import importlib.util

    engine = Path(__file__).resolve().parents[1]
    admission_name = "src.engine.lifecycle.research_admission"
    if admission_name in sys.modules:
        raise ValueError("isolated_router_guard_module_already_loaded")

    def load(name: str, path: Path):
        if path.is_symlink():
            raise ValueError("isolated_router_guard_source_alias_invalid")
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ValueError("isolated_router_guard_source_unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    admission = load(admission_name, engine / "lifecycle/research_admission.py")
    sys.modules[admission_name] = admission
    try:
        guard = load(
            "isolated_router_transition_guard",
            engine / "infrastructure/research_release_transition.py",
        )
        guard.assert_readable(workspace / "data")
    finally:
        sys.modules.pop(admission_name, None)


def selected_release(workspace: Path) -> tuple[Path, str]:
    workspace = workspace.resolve(strict=True)
    _assert_research_transition_readable(workspace)
    selection = json.loads(
        (workspace / "data/runtime/runtime_release_selection.json").read_text()
    )
    return validate_release(workspace, selection)


def error_detector_release_is_current(
    root: Path, expected_commit: str | None = None
) -> bool:
    """Recheck a routed reader after acquiring its shared deployment lock.

    Invalid selection remains an error; a valid successor means this delayed
    invocation must yield to the next scheduled reader, without publishing.
    """
    root = root.resolve(strict=True)
    workspace = (root / "data").resolve(strict=True).parent
    selected_root, selected_commit = selected_release(workspace)
    return selected_root == root and (
        expected_commit is None or selected_commit == expected_commit
    )


def validate_release(workspace: Path, selection: dict) -> tuple[Path, str]:
    """Validate an immutable candidate without publishing it to live readers."""
    workspace = workspace.resolve(strict=True)
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
    _validate_retired_surfaces(workspace, root)
    return root, commit


def _process_start_ticks(pid: int) -> str:
    try:
        return Path("/proc", str(pid), "stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError) as exc:
        raise ValueError("runtime_pid_not_running") from exc


class _StartupReceiptReadRace(ValueError):
    """An atomic receipt publication raced the bounded read, not validation."""


def _startup_receipt(path: Path) -> tuple[dict, bytes]:
    """Read only bounded local receipts; never invoke a policy/source verifier."""
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode):
        raise ValueError("startup_receipt_symlink")
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("startup_receipt_regular_file_required")
    if before.st_size > MAX_STARTUP_RECEIPT_BYTES:
        raise ValueError("startup_receipt_size_limit")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("startup_receipt_regular_file_required")
        raw = handle.read(MAX_STARTUP_RECEIPT_BYTES + 1)
        opened = os.fstat(handle.fileno())
    after = path.lstat()
    signature = lambda item: (
        item.st_dev,
        item.st_ino,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )
    if signature(before) != signature(opened) or signature(opened) != signature(after):
        raise _StartupReceiptReadRace("startup_receipt_changed_during_read")
    if len(raw) > MAX_STARTUP_RECEIPT_BYTES:
        raise ValueError("startup_receipt_size_limit")

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("startup_receipt_duplicate_key")
            value[key] = item
        return value

    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except RecursionError as exc:
        raise ValueError("startup_receipt_json_invalid") from exc
    if not isinstance(value, dict):
        raise ValueError("startup_receipt_object_required")
    return value, raw


def _startup_ordered_transition(
    workspace, selection, release_root, git_commit, target_date
):
    """Bind only the canonical ordered owner; a completed past launch is history."""
    if selection.get("approval_scope") != "ordered_intraday_deploy_and_restart":
        if selection.get("deployment_transition"):
            raise ValueError("startup_ordered_transition_approval_invalid")
        return None
    if selection.get("approved_by") != "user":
        raise ValueError("startup_ordered_transition_approval_invalid")
    path = Path(str(selection.get("deployment_transition") or ""))
    source_day = path.parent.parent.name
    try:
        if (
            date.fromisoformat(source_day).isoformat() != source_day
            or source_day > target_date
        ):
            raise ValueError("startup_ordered_transition_date_invalid")
        selected_at = datetime.fromisoformat(selection["selected_at_kst"])
        if (
            selected_at.tzinfo is None
            or selected_at.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
            != source_day
        ):
            raise ValueError("startup_ordered_transition_date_invalid")
    except (KeyError, ValueError) as exc:
        raise ValueError("startup_ordered_transition_date_invalid") from exc
    owner = workspace / "data/runtime/release_transitions"
    expected = owner / source_day / git_commit / "status.json"
    if (
        path != expected
        or path.resolve(strict=True)
        != owner.resolve(strict=True) / source_day / git_commit / "status.json"
    ):
        raise ValueError("startup_ordered_transition_path_invalid")
    value, raw = _startup_receipt(path)
    if (
        value.get("schema") != "ordered_intraday_deployment_v1"
        or value.get("authority") != "APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART"
        or value.get("policy_effect") != "unchanged"
        or value.get("target_date") != source_day
        or value.get("candidate_root") != str(release_root)
        or value.get("candidate_commit") != git_commit
    ):
        raise ValueError("startup_ordered_transition_identity_invalid")
    phase = value.get("phase")
    if phase == "failed" or value.get("status") == "fail":
        raise ValueError("startup_ordered_transition_failed")
    active = phase in {"selected", "prepared", "starting"}
    if active:
        if source_day != target_date or value.get("status") not in (None, "running"):
            raise ValueError("startup_ordered_transition_state_invalid")
    elif phase != "complete" or value.get("status") != "pass":
        raise ValueError("startup_ordered_transition_state_invalid")
    else:
        identity = value.get("successor_identity") or {}
        if (
            not isinstance(identity, dict)
            or type(identity.get("pid")) is not int
            or identity["pid"] <= 0
            or not str(identity.get("start_ticks") or "").isdigit()
            or identity.get("cwd") != str(release_root / "src")
        ):
            raise ValueError("startup_ordered_transition_successor_invalid")
    return dict(path=path, raw=raw, value=value, active=active, source_date=source_day)


def startup_consumption_state(
    workspace: Path,
    *,
    pid: int,
    start_ticks: str,
    release_root: Path,
    git_commit: str,
    target_date: str,
) -> dict:
    """First-health ordering barrier for the launcher's completed PID receipts.

    These receipts reuse the parent's full validation. They grant no policy,
    launch or order authority and do not replace the subsequent full detector.
    """
    result = dict(
        schema="main_startup_consumption_barrier_v1",
        status="failed",
        target_date=target_date,
        pid=pid,
        start_ticks=str(start_ticks),
        runtime_effect=False,
        new_finalization_claimed=False,
    )
    try:
        workspace = Path(workspace).resolve(strict=True)
        release_root = Path(release_root).resolve(strict=True)
        if (
            type(pid) is not int
            or pid <= 0
            or not str(start_ticks).isdigit()
            or not re.fullmatch(r"[0-9a-f]{40}", git_commit or "")
            or date.fromisoformat(target_date).isoformat() != target_date
        ):
            raise ValueError("startup_expected_identity_invalid")
        if _process_start_ticks(pid) != str(start_ticks):
            raise ValueError("startup_process_identity_changed")
        if (
            Path(os.readlink(f"/proc/{pid}/cwd")).resolve(strict=True)
            != release_root / "src"
        ):
            raise ValueError("startup_process_cwd_changed")
        runtime = workspace / "data/runtime"
        selection_path = runtime / "runtime_release_selection.json"
        selection, selected_raw = _startup_receipt(selection_path)
        if (
            selection.get("schema") != "runtime_release_selection_v1"
            or selection.get("workspace") != str(workspace)
            or selection.get("release_root") != str(release_root)
            or selection.get("git_commit") != git_commit
        ):
            raise ValueError("startup_selected_generation_changed")
        transition = _startup_ordered_transition(
            workspace, selection, release_root, git_commit, target_date
        )
        receipt = selection.get("actual_pid_receipt") or {}
        if not isinstance(receipt, dict):
            raise ValueError("startup_attested_identity_invalid")
        if (
            selection.get("actual_pid_consumed") is not True
            or receipt.get("pid") != pid
        ):
            # A missing final attestation is expected during startup. A
            # published failure for this child already proves startup failed.
            pending_verify_path = (
                runtime
                / "policy_bootstrap"
                / f"runtime_policy_bootstrap_verify_{target_date}.json"
            )
            if pending_verify_path.exists() or pending_verify_path.is_symlink():
                pending_verify, _ = _startup_receipt(pending_verify_path)
                if (
                    pending_verify.get("target_date") == target_date
                    and pending_verify.get("pid") == pid
                    and (
                        pending_verify.get("status") != "pass"
                        or pending_verify.get("passed") is not True
                        or pending_verify.get("pid_passed") is not True
                        or pending_verify.get("pid_env_available") is not True
                    )
                ):
                    raise ValueError("startup_bootstrap_pid_receipt_invalid")
            return dict(
                result, status="pending", reason="waiting_current_pid_attestation"
            )
        if (
            receipt.get("schema") != "runtime_release_pid_receipt_v1"
            or receipt.get("start_ticks") != str(start_ticks)
            or receipt.get("release_root") != str(release_root)
            or receipt.get("git_commit") != git_commit
            or receipt.get("process_cwd") != str(release_root / "src")
        ):
            raise ValueError("startup_attested_identity_invalid")
        if transition is not None:
            required = receipt.get("ordered_transition_required")
            if type(required) is not bool or (
                transition["active"] and required is not True
            ):
                raise ValueError("startup_ordered_transition_receipt_invalid")
            if required and not transition["active"]:
                if transition["source_date"] != target_date or transition["value"][
                    "successor_identity"
                ] != dict(
                    pid=pid, start_ticks=str(start_ticks), cwd=str(release_root / "src")
                ):
                    raise ValueError("startup_ordered_transition_successor_invalid")
            elif not required:
                try:
                    recorded = datetime.fromisoformat(receipt["recorded_at_kst"])
                    completed = datetime.fromisoformat(
                        transition["value"]["updated_at"]
                    )
                    if (
                        recorded.tzinfo is None
                        or completed.tzinfo is None
                        or recorded < completed
                    ):
                        raise ValueError("startup_ordered_transition_receipt_invalid")
                except (KeyError, ValueError) as exc:
                    raise ValueError(
                        "startup_ordered_transition_receipt_invalid"
                    ) from exc
        directory = runtime / "policy_bootstrap"
        manifest, manifest_raw = _startup_receipt(
            directory / f"runtime_policy_bootstrap_{target_date}.json"
        )
        verification, verify_raw = _startup_receipt(
            directory / f"runtime_policy_bootstrap_verify_{target_date}.json"
        )
        unsigned = {
            key: value for key, value in manifest.items() if key != "manifest_sha256"
        }
        manifest_sha = hashlib.sha256(
            json.dumps(
                unsigned,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        if (
            manifest.get("target_date") != target_date
            or manifest.get("manifest_sha256") != manifest_sha
            or verification.get("target_date") != target_date
            or verification.get("status") != "pass"
            or verification.get("passed") is not True
            or verification.get("pid") != pid
            or verification.get("pid_passed") is not True
            or verification.get("pid_env_available") is not True
            or verification.get("manifest_sha256") != manifest_sha
        ):
            raise ValueError("startup_bootstrap_pid_receipt_invalid")
        handoff_path = (
            directory / "intraday_handoff" / target_date / (git_commit + ".json")
        )
        basis = "native_preopen"
        handoff_read = None
        if handoff_path.exists() or handoff_path.is_symlink():
            handoff, handoff_raw = _startup_receipt(handoff_path)
            consumed_path = handoff_path.with_suffix(".consumed.json")
            consumed, consumed_raw = _startup_receipt(consumed_path)
            identity = dict(
                pid=pid, start_ticks=str(start_ticks), cwd=str(release_root / "src")
            )
            if (
                handoff.get("schema") != "intraday_policy_preserving_release_handoff_v1"
                or handoff.get("status") != "prepared_verified"
                or handoff.get("authority")
                != "APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF"
                or handoff.get("target_date") != target_date
                or handoff.get("selected_release_commit") != git_commit
                or handoff.get("release_root") != str(release_root)
                or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
                or consumed.get("status") != "pass"
                or consumed.get("actual_pid_consumed") is not True
                or consumed.get("target_date") != target_date
                or consumed.get("selected_release_commit") != git_commit
                or consumed.get("release_root") != str(release_root)
                or consumed.get("pid_identity") != identity
                or consumed.get("handoff_sha256")
                != hashlib.sha256(handoff_raw).hexdigest()
                or consumed.get("manifest_sha256") != manifest_sha
            ):
                raise ValueError("startup_intraday_consumption_invalid")
            basis = "intraday_policy_preserving_handoff"
            handoff_read = (handoff_path, handoff_raw, consumed_path, consumed_raw)
        elif manifest.get("selected_release_sha") != git_commit:
            raise ValueError("startup_native_preopen_release_mismatch")
        receipt_set_changed = (
            _startup_receipt(selection_path)[1] != selected_raw
            or _startup_receipt(
                directory / f"runtime_policy_bootstrap_{target_date}.json"
            )[1]
            != manifest_raw
            or _startup_receipt(
                directory / f"runtime_policy_bootstrap_verify_{target_date}.json"
            )[1]
            != verify_raw
        )
        if _process_start_ticks(pid) != str(start_ticks):
            raise ValueError("startup_process_identity_changed")
        if receipt_set_changed:
            raise _StartupReceiptReadRace("startup_receipt_generation_changed")
        if handoff_read is not None:
            path, raw, consumed_path, consumed_raw = handoff_read
            if (
                _startup_receipt(path)[1] != raw
                or _startup_receipt(consumed_path)[1] != consumed_raw
            ):
                raise _StartupReceiptReadRace("startup_receipt_generation_changed")
        if transition is not None:
            if transition["active"]:
                return dict(
                    result,
                    status="pending",
                    reason="waiting_ordered_transition_completion",
                )
            if _startup_receipt(transition["path"])[1] != transition["raw"]:
                raise _StartupReceiptReadRace(
                    "startup_ordered_transition_generation_changed"
                )
        return dict(
            result,
            status="ready",
            reason="current_pid_consumption_complete",
            basis=basis,
            release_root=str(release_root),
            git_commit=git_commit,
            manifest_sha256=manifest_sha,
        )
    except _StartupReceiptReadRace as exc:
        # The caller retains the original process-start deadline. A stable
        # next read must still pass every identity/source/receipt validation.
        return dict(result, status="pending", reason=str(exc))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return dict(result, reason=str(exc)[:240])


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
        start_ticks = _process_start_ticks(pid)
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
        transition = _startup_ordered_transition(
            workspace,
            selection,
            selected_root,
            selected_commit,
            datetime.fromisoformat(recorded_at).date().isoformat(),
        )
        previous_receipt = selection.get("actual_pid_receipt") or {}
        transition_required = bool(
            transition
            and (
                transition["active"]
                or (
                    isinstance(previous_receipt, dict)
                    and previous_receipt.get("pid") == pid
                    and previous_receipt.get("start_ticks") == start_ticks
                    and previous_receipt.get("ordered_transition_required") is True
                )
            )
        )
        receipt = {
            "schema": "runtime_release_pid_receipt_v1",
            "pid": pid,
            "start_ticks": start_ticks,
            "ordered_transition_required": transition_required,
            "recorded_at_kst": recorded_at,
            "release_root": str(selected_root),
            "git_commit": selected_commit,
            "process_cwd": str(process_cwd),
            "attestation": "launcher_child_cwd_matches_selected_release",
        }
        selection["actual_pid_consumed"] = True
        selection["actual_pid_receipt"] = receipt
        selection["actual_pid_consumption_status"] = "pid_receipt_attested"
        original_stat = manifest_path.stat()
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=manifest_path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            try:
                json.dump(selection, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            except BaseException:
                temporary_path.unlink(missing_ok=True)
                raise
        try:
            if _process_start_ticks(pid) != start_ticks:
                raise ValueError("runtime_pid_changed_before_receipt")
            # A privileged launcher must not replace the cron user's private
            # selector with a root-owned 0600 file. Preserve custody before
            # publishing; failure leaves the existing selector untouched.
            temp_stat = temporary_path.stat()
            if (temp_stat.st_uid, temp_stat.st_gid) != (
                original_stat.st_uid,
                original_stat.st_gid,
            ):
                os.chown(temporary_path, original_stat.st_uid, original_stat.st_gid)
            os.chmod(temporary_path, original_stat.st_mode & 0o777)
            os.replace(temporary_path, manifest_path)
        finally:
            temporary_path.unlink(missing_ok=True)
    return receipt


def main_supervisor_command(root: Path) -> str:
    """One quoted child environment for initial start and drained restart."""
    database = []
    url_file = os.environ.get("KORSTOCKSCAN_POSTGRES_URL_FILE")
    required = os.environ.get("KORSTOCKSCAN_REQUIRE_POSTGRES_URL", "0")
    if url_file is not None and "KORSTOCKSCAN_POSTGRES_URL" in os.environ:
        raise ValueError("native_main_database_configuration_conflict")
    if url_file is not None or required != "0":
        if required not in {"0", "1"} or not url_file:
            raise ValueError("native_main_database_file_configuration_required")
        if not Path(url_file).is_absolute():
            raise ValueError("native_main_database_file_path_invalid")
        # Reuse the selected consumer's protected-file reader before a restart
        # can drain its incumbent. No database connection or URL output occurs.
        checked = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); "
                "from src.utils.constants import POSTGRES_URL",
                str(root),
            ],
            capture_output=True,
            timeout=30,
            check=False,
        )
        if checked.returncode:
            raise ValueError("native_main_database_file_invalid")
        # Forward only a protected file path, never credentials in argv.
        # A stale tmux server's direct URL must not override that file.
        database = [
            "-u",
            "KORSTOCKSCAN_POSTGRES_URL",
            f"KORSTOCKSCAN_REQUIRE_POSTGRES_URL={required}",
            f"KORSTOCKSCAN_POSTGRES_URL_FILE={url_file}",
        ]
    elif "KORSTOCKSCAN_POSTGRES_URL" in os.environ:
        raise ValueError("native_main_database_requires_protected_url_file")
    return shlex.join(
        [
            "/usr/bin/env",
            *database,
            f"PROJECT_DIR={root}",
            f"PYTHONPATH={root}",
            f"VENV_PY={root}/.venv/bin/python",
            "/bin/bash",
            str(root / "src/run_bot.sh"),
        ]
    )


def make_plan(
    workspace: Path, root: Path, commit: str, operation: str, target_date: str
) -> dict:
    if date.fromisoformat(target_date).isoformat() != target_date:
        raise ValueError("target_date_invalid")
    hold = workspace / "data/runtime/operator_startup_hold.json"
    if operation in {"start", "restart", "preopen"} and (
        hold.exists() or hold.is_symlink()
    ):
        raise ValueError("operator_postclose_startup_hold_active")
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
            "--resolve-effective-today" if operation == "finalize" else target_date,
        ]
    elif operation == "validate-startup":
        command = [
            str(root / ".venv/bin/python"),
            "-B",
            "-m",
            "src.engine.automation.main_startup_validation",
            "--workspace",
            str(workspace),
            "--target-date",
            target_date,
        ]
    elif operation == "buy-funnel":
        command = [
            "/bin/bash",
            str(root / "deploy/run_buy_funnel_sentinel_intraday.sh"),
            target_date,
        ]
    elif operation == "monitor-snapshot":
        # The existing cron owns logging. Pin the selected entrypoint directly;
        # its safe wrapper and async child inherit the same release environment.
        command = [
            "/bin/bash",
            str(root / "deploy/run_monitor_snapshot_incremental_cron.sh"),
            target_date,
        ]
    elif operation == "log-retention":
        command = [
            "/bin/bash",
            str(root / "deploy/run_with_owned_log.sh"),
            "--owner",
            "log_retention_daily",
            "--log",
            str(workspace / "logs/log_retention_daily.log"),
            str(root / ".venv/bin/python"),
            "-m",
            "src.engine.infrastructure.log_retention",
            "--workspace",
            str(workspace),
            "--apply",
            "--include-tmp",
            "--include-metrics",
            "--terminal",
            str(workspace / "data/report/log_retention" / (target_date + ".json")),
        ]
    elif operation == "error-detection":
        command = [
            "/bin/bash",
            str(root / "deploy/run_with_owned_log.sh"),
            "--owner",
            "error_detection_cron",
            "--log",
            str(workspace / "logs/run_error_detection_cron.log"),
            "/bin/bash",
            str(root / "deploy/run_error_detection.sh"),
            "full",
        ]
    elif operation == "pre-submit-source":
        command = [
            str(root / ".venv/bin/python"),
            "-m",
            "src.engine.monitoring.submission_bottleneck_monitor",
            "--report",
            str(
                root
                / "data/report/buy_funnel_sentinel"
                / f"submission_bottleneck_source_{target_date}.json"
            ),
            "--delay-source-only",
            "--date",
            target_date,
            "--notify",
        ]
    elif operation == "holding-exit-sentinel":
        command = [
            "/bin/bash",
            str(root / "deploy/run_holding_exit_sentinel_intraday.sh"),
            target_date,
        ]
    elif operation == "paired-replay":
        command = [
            "/bin/bash",
            str(root / "deploy/run_ai_entry_setup_paired_replay_postclose.sh"),
            target_date,
        ]
    elif operation == "snapshot-archive":
        command = [
            "/bin/bash",
            str(root / "deploy/run_with_owned_log.sh"),
            "--owner", "snapshot_archive_daily",
            "--log", str(workspace / "logs/snapshot_archive_daily.log"),
            str(root / ".venv/bin/python"), "-m",
            "src.engine.compress_db_backfilled_files",
            "--snapshots-only", "--days", "1",
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
        child = main_supervisor_command(root)
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


def render_crontab(
    original: str, workspace: Path, *, require_snapshot_group: bool = False
) -> str:
    """Route pipeline owners and the installed snapshot group without rescheduling.

    The eight pipeline owners are required. The snapshot group must contain
    all three unique tags when present; the operational CLI also requires its
    presence. Legacy pure transforms can omit it. Unknown command shapes fail
    closed; other services, timers and intraday observers remain untouched.
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
    seen_snapshots: list[str] = []
    result = []
    for line in original.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            result.append(line)
            continue
        tag = line.rsplit("#", 1)[-1].strip() if "#" in line else ""
        snapshot = tag in SNAPSHOT_CRON_TAGS
        op = "monitor-snapshot" if snapshot else TAGS.get(tag) or LEGACY_TAGS.get(tag)
        if tag == "RUNTIME_RELEASE_START" or (
            "/usr/bin/tmux new-session -d -s bot " in line
            and f"cd {workspace}/src " in line
        ):
            op = "start"
        if op is None:
            result.append(line)
            continue
        if snapshot:
            seen_snapshots.append(tag)
        else:
            seen.append(op)
        scheduled = re.fullmatch(r"(\s*(?:\S+\s+){5})(.+)", line)
        if not scheduled:
            raise ValueError("cron_schedule_invalid")
        schedule, command = scheduled.groups()
        prefix = env_prefix.match(command).group()
        command = command[len(prefix) :]
        desired = f"{router} {op}"
        if snapshot:
            # Keep the canonical logging owner. Only its inner producer moves
            # behind the release selector; the selected router need not know
            # this newly added operation.
            logger = (
                f"bash {workspace}/deploy/run_with_owned_log.sh --owner run_monitor_snapshot_cron "
                f"--log {workspace}/logs/run_monitor_snapshot_cron.log "
            )
            desired = logger + desired
            old = (
                logger + f"{workspace}/deploy/run_monitor_snapshot_incremental_cron.sh"
            )
        elif op in OWNED:
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
        date_arg = r" $(TZ=Asia/Seoul date +\%F)"
        if snapshot and matched == old:
            # Legacy incremental cron resolved the date inside its wrapper.
            # The routed schedule passes that same KST date explicitly.
            tail = date_arg + tail
        arguments, marker, comment = tail.partition("#")
        if op in OWNED or op == "paired-replay" or snapshot:
            if op == "finalize" and arguments.startswith(date_arg):
                arguments = arguments[len(date_arg) :]
            elif op != "finalize" and not arguments.startswith(date_arg):
                raise ValueError(f"cron_target_date_unrecognized:{op}")
            elif op != "finalize":
                arguments = arguments[len(date_arg) :]
        # Do not accept --print-plan, an extra execution, or shell conditionals
        # as an installed scheduled worker. The scheduled finalizer must resolve
        # the effective trading date and its immediately prior KRX source date.
        if op == "finalize" and arguments.startswith(" --resolve-effective-today"):
            arguments = arguments[len(" --resolve-effective-today") :]
        if not re.fullmatch(r"(?:\s+(?:>>?\s+[^\s;&|<>]+|2>&1))*\s*", arguments):
            raise ValueError(f"cron_arguments_unrecognized:{op}")
        if op == "start" and not marker:
            tail = tail.rstrip() + " # RUNTIME_RELEASE_START"
        elif op == "start" and comment.strip() != "RUNTIME_RELEASE_START":
            raise ValueError("cron_start_marker_unrecognized")
        if op == "finalize":
            schedule = "35 5 * * * "
            redirections = arguments
            line = (
                schedule
                + prefix
                + desired
                + " --resolve-effective-today"
                + redirections.rstrip()
                + " # POSTCLOSE_FINALIZATION_0535"
            )
        else:
            line = schedule + prefix + desired + tail
        result.append(line)
    if not REQUIRED_CRON_TARGETS.issubset(seen) or len(seen) != len(set(seen)):
        raise ValueError("cron_target_missing_or_duplicate")
    if (seen_snapshots or require_snapshot_group) and (
        set(seen_snapshots) != SNAPSHOT_CRON_TAGS
        or len(seen_snapshots) != len(SNAPSHOT_CRON_TAGS)
    ):
        raise ValueError("cron_snapshot_target_missing_or_duplicate")
    return "\n".join(result) + "\n"


def _cron_routing_status(crontab: str) -> dict:
    """Describe an already validated cron without conflating observer slots."""
    snapshot_count = sum(
        line.rsplit("#", 1)[-1].strip() in SNAPSHOT_CRON_TAGS
        for line in crontab.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return {
        "cron_routing_verified": True,
        "required_targets": len(REQUIRED_CRON_TARGETS),
        "snapshot_targets": snapshot_count,
    }


def manage_cron(
    workspace: Path, install: bool, *, require_snapshot_group: bool = False
) -> None:
    if not install:
        old = subprocess.check_output(["crontab", "-l"], text=True)
        if (
            render_crontab(
                old, workspace, require_snapshot_group=require_snapshot_group
            )
            != old
        ):
            raise ValueError("cron_release_routing_not_installed")
        print(json.dumps(_cron_routing_status(old)))
        return
    # Serialize router installs. Re-read just before writing to avoid clobbering
    # an unrelated session's edits observed during validation.
    with (workspace / "data/runtime/runtime_release_cron.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = subprocess.check_output(["crontab", "-l"], text=True)
        new = render_crontab(
            old, workspace, require_snapshot_group=require_snapshot_group
        )
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
        print(json.dumps(_cron_routing_status(new)))


def native_custody_environment(workspace: Path) -> dict[str, str]:
    """Give every routed consumer the same approved account/journal identity.

    Parse data assignments without shell execution. The file is transferred
    from the attested pre-cutover Main PID; it is not a policy publication.
    """
    path = workspace / "data/config/native_owner_custody.env"
    required = (
        workspace / "data/runtime/retirements/main-only-retirement.json"
    ).is_file()
    if not path.exists() and not required:
        return {}
    before = path.stat()
    if path.is_symlink() or not path.is_file() or before.st_size > 8192:
        raise ValueError("native_custody_environment_file_invalid")
    values = {}
    allowed = {
        "KORSTOCKSCAN_BROKER_ACCOUNT_KEY",
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH",
    }
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, raw = line.partition("=")
        if not separator or key not in allowed or key in values:
            raise ValueError("native_custody_environment_keys_invalid")
        tokens = shlex.split(raw)
        if len(tokens) != 1:
            raise ValueError("native_custody_environment_value_invalid")
        values[key] = tokens[0]
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ValueError("native_custody_environment_changed")
    if set(values) != allowed:
        raise ValueError("native_custody_environment_incomplete")
    account = values["KORSTOCKSCAN_BROKER_ACCOUNT_KEY"]
    if (
        not account.strip()
        or account.lower() == "default"
        or len(account) > 80
        or any(c in account for c in "\r\n\t")
    ):
        raise ValueError("native_custody_account_invalid")
    if not Path(values["KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH"]).is_absolute():
        raise ValueError("native_custody_registry_path_invalid")
    return values


def _record_owned_route_failure(workspace, operation, target_date, error):
    """Preserve pre-wrapper failures in the existing scheduled owner's log."""
    owner = OWNED[operation][1]
    path = Path(workspace) / "logs" / (owner + ".log")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o640)
    with os.fdopen(fd, "a") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("route_failure_log_not_regular")
        body = dict(operation=operation, target_date=target_date,
                    recorded_at_kst=datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                    router_source=str(Path(__file__).resolve()), pid=os.getpid(),
                    error_type=type(error).__name__, reason=str(error)[:1200], exit_code=2)
        stream.write("[ROUTE_FAILURE] " + json.dumps(body, ensure_ascii=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=OPERATIONS)
    parser.add_argument(
        "target_date",
        nargs="?",
        default=None,
    )
    parser.add_argument("--print-plan", action="store_true")
    parser.add_argument("--resolve-effective-today", action="store_true")
    parser.add_argument("--record-pid", type=int)
    parser.add_argument("--record-release-root")
    parser.add_argument("--record-git-commit")
    parser.add_argument(
        "--workspace",
        help="Canonical shared workspace; selected-router PID record only",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check-cron", action="store_true")
    group.add_argument("--install-cron", action="store_true")
    group.add_argument("--check-release-set", action="store_true")
    args = parser.parse_args()
    source_path = Path(__file__).resolve()
    workspace = source_path.parents[3]
    leases = ExitStack()
    try:
        if args.workspace is not None:
            if (
                args.record_pid is None
                or args.operation
                or args.target_date
                or args.print_plan
                or args.resolve_effective_today
                or args.check_cron
                or args.install_cron
                or args.check_release_set
            ):
                raise ValueError("runtime_pid_workspace_record_only")
            requested_workspace = Path(args.workspace)
            if (
                not requested_workspace.is_absolute()
                or str(requested_workspace.resolve(strict=True)) != args.workspace
            ):
                raise ValueError("runtime_pid_workspace_not_canonical")
            workspace = requested_workspace
        if args.resolve_effective_today and args.operation != "finalize":
            raise ValueError("resolve_effective_today_requires_finalize")
        scheduled = args.operation in {*TAGS.values(), "snapshot-archive"} and not args.print_plan
        if scheduled:
            scheduled_fd = leases.enter_context(scheduled_execution_lease(workspace))
        root, commit = selected_release(workspace)
        if (
            args.workspace is not None
            and source_path
            != root / "src/engine/infrastructure/runtime_release_router.py"
        ):
            raise ValueError("runtime_pid_router_not_selected_source")
        if args.record_pid is not None:
            if (
                args.operation
                or args.target_date
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
                    manage_cron(workspace, True, require_snapshot_group=True)
            else:
                manage_cron(workspace, False, require_snapshot_group=True)
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
        if args.operation == "validate-startup" and args.target_date is None:
            raise ValueError("startup_validation_target_date_required")
        target_date = (
            args.target_date or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        )
        plan = make_plan(workspace, root, commit, args.operation, target_date)
        if args.print_plan:
            print(json.dumps(plan), flush=True)
            return 0
        if args.operation not in {"start", "restart"}:
            print(json.dumps(plan), flush=True)
        env = dict(os.environ)
        env.pop("PYTHONHOME", None)
        env.update(native_custody_environment(workspace))
        env.update(
            PROJECT_DIR=str(root),
            PYTHONPATH=str(root),
            VENV_PY=str(root / ".venv/bin/python"),
            KORSTOCKSCAN_PROJECT_DIR=str(root),
            KORSTOCKSCAN_PYTHON_BIN=str(root / ".venv/bin/python"),
            KORSTOCKSCAN_RUNTIME_GIT_COMMIT=commit,
        )
        if args.operation == "archive":
            # The archive wrapper's positional argument is retention days;
            # its source-date interface is TARGET_DATE, including recovery.
            env["TARGET_DATE"] = target_date
        os.chdir(plan["cwd"])
        if args.operation in {"start", "restart"}:
            # Hold the shared deployment lock through the transition, never for
            # the lifetime of the main bot. Re-resolve the selector after lock.
            with runtime_release_set_lock(workspace):
                root, commit = selected_release(workspace)
                plan = make_plan(workspace, root, commit, args.operation, target_date)
                print(json.dumps(plan), flush=True)
                env.update(
                    PROJECT_DIR=str(root),
                    PYTHONPATH=str(root),
                    VENV_PY=str(root / ".venv/bin/python"),
                    KORSTOCKSCAN_PROJECT_DIR=str(root),
                    KORSTOCKSCAN_PYTHON_BIN=str(root / ".venv/bin/python"),
                    KORSTOCKSCAN_RUNTIME_GIT_COMMIT=commit,
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
                        return subprocess.run(
                            plan["command"], env=env, check=False
                        ).returncode
                return subprocess.run(plan["command"], env=env, check=False).returncode
        if scheduled:
            # The wrapper retains the lease even if only its router is killed.
            return subprocess.run(
                plan["command"], env=env, check=False, pass_fds=(scheduled_fd,)
            ).returncode
        os.execvpe(plan["command"][0], plan["command"], env)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        if args.operation in OWNED and not args.print_plan:
            try:
                _record_owned_route_failure(workspace, args.operation, args.target_date, exc)
            except (OSError, ValueError) as evidence_error:
                print("runtime_route_failure_evidence_unavailable:" + type(evidence_error).__name__, file=sys.stderr)
        print(f"runtime_release_route_blocked: {exc}", file=sys.stderr)
        return 2
    finally:
        leases.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
