"""Prepare and apply a finite systemd retirement after native flat custody.

Default invocation is read-only preparation. Apply only to a reviewed manifest;
active episode services and all residual orders/positions prevent deletion.
Historical market data and custody ledgers are never deleted by this tool.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from zoneinfo import ZoneInfo

from src.trading.config.owner_retirement import RETIRED_EPISODE_PROFILE_IDS

SCHEMA = "symbol_owner_retirement_transition_v1"
KST = ZoneInfo("Asia/Seoul")


def atomic_write_json(path, payload):
    """Publish a receipt without importing the retired strategy implementation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, sort_keys=True, indent=2)
            stream.flush()
            # systemd retirement applies as root; the unprivileged router and
            # Main launcher must still read this non-secret control receipt.
            os.fchmod(stream.fileno(), 0o644)
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def units():
    names = []
    for profile in sorted(RETIRED_EPISODE_PROFILE_IDS):
        stem = "korstockscan-low-price-two-leg-" + profile.replace("_", "-")
        names.extend((stem + ".timer", stem + "-preflight.timer",
                      f"korstockscan-low-price-two-leg@{profile}.service",
                      f"korstockscan-low-price-two-leg-preflight@{profile}.service"))
    return tuple(names)


def prepare(workspace, *, systemd_dir=Path("/etc/systemd/system")):
    workspace, systemd_dir = Path(workspace).resolve(), Path(systemd_dir).resolve()
    files = []
    for name in units():
        paths = [systemd_dir / name, *(systemd_dir / (name + ".d")).glob("*.conf")]
        for path in paths:
            if path.exists() or path.is_symlink():
                # A permanent instance mask is the surviving retirement guard,
                # not a dedicated strategy file to remove on reviewed retry.
                if name.endswith(".service") and path.is_symlink() and path.resolve() == Path("/dev/null"):
                    continue
                if path.is_dir():
                    raise ValueError("retirement_unit_path_is_directory")
                files.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    guard = workspace / "src/trading/config/owner_retirement.py"
    body = dict(schema=SCHEMA, state="prepared", symbol="034020", owner="episode",
                prepared_at_kst=datetime.now(KST).isoformat(), workspace=str(workspace),
                systemd_dir=str(systemd_dir), units=list(units()), installed_files=files,
                guard_file="src/trading/config/owner_retirement.py",
                guard_file_sha256=hashlib.sha256(guard.read_bytes()).hexdigest(),
                new_owner="main_scalping", initial_policy="current_main_non_samsung",
                initial_policy_preproof_required=False, runtime_effect=False)
    body["receipt_sha256"] = digest(body)
    return body


def require_flat(snapshot, registry, *, observed_at):
    from src.trading.order.symbol_owner_policy_apply import validate_broker_snapshot_contract
    validate_broker_snapshot_contract(snapshot, symbols={"034020"}, migration_receipts_allowed=False)
    if snapshot["inventory"].get("034020", 0) != 0 or any(
        row.get("symbol") == "034020" for row in snapshot["open_orders"]
    ):
        raise ValueError("retirement_broker_residual_exposure")
    reconciliation = registry.reconcile_symbol_quantity(symbol="034020", broker_quantity=0)
    unresolved = registry.unresolved_intent_summary(symbol="034020", active_date=None)
    if int(unresolved.get("unresolved_intent_count") or 0):
        raise ValueError("retirement_unresolved_intent")
    if int(reconciliation.get("registered_owner_quantity") or 0) or int(reconciliation.get("external_manual_remainder") or 0):
        raise ValueError("retirement_registry_residual_exposure")
    return dict(broker_snapshot_sha256=snapshot["snapshot_sha256"],
                observed_at_kst=observed_at.isoformat(), reconciliation=reconciliation, unresolved=unresolved)


def blocking_retirement_processes(rows, *, workspace, proc_root=Path("/proc")):
    """Retire one episode owner without stopping established foreign owners.

    Main already has separate entry authority. Recognize its actual argv, and
    known other episode profiles, rather than trusting substrings in a shell
    command. Unknown/dynamic profiles and unreadable processes stay blocking.
    The all-owner broker/custody flat check is still required for this symbol.
    """
    from src.trading.low_price_two_leg.profiles import PROFILES
    workspace = Path(workspace).resolve()
    managed = workspace.parent / (workspace.name + "-runtime-releases")
    blocked = []
    for row in rows:
        try:
            argv = [arg.decode() for arg in (proc_root / str(int(row["pid"])) / "cmdline").read_bytes().split(b"\0") if arg]
            interpreter = Path(argv[0]).name
            # The tmux server retains its original launch command in argv; it
            # is not an order process. Its children are independently scanned.
            executable = (proc_root / str(int(row["pid"])) / "exe").resolve(strict=True)
            if executable in {Path("/usr/bin/tmux"), Path("/bin/tmux")}:
                continue
            cwd = (proc_root / str(int(row["pid"])) / "cwd").resolve(strict=True)
            native_root = (cwd == workspace / "src" or
                           (cwd.name == "src" and cwd.parent.parent == managed))
            script = (cwd / argv[1]).resolve() if len(argv) > 1 else None
            main = (len(argv) == 2 and Path(argv[1]).name == "bot_main.py"
                    and interpreter.startswith("python") and native_root
                    and script == cwd / "bot_main.py")
            supervisor = (len(argv) == 2 and Path(argv[1]).name == "run_bot.sh"
                          and interpreter in {"bash", "sh"} and native_root
                          and script == cwd / "run_bot.sh")
            foreign_episode = False
            if (len(argv) > 4 and interpreter.startswith("python") and argv[1:3] ==
                    ["-m", "src.trading.low_price_two_leg.service"]
                    and argv.count("--profile") == 1):
                index = argv.index("--profile")
                profile = PROFILES.get(argv[index + 1])
                # A second symbol/profile override must not masquerade as a
                # known foreign owner. The native service only accepts profiles.
                foreign_episode = bool(profile and profile.symbol != "034020"
                                       and not any(arg.startswith(("--symbol", "--profile=")) for arg in argv))
            if main or supervisor or foreign_episode:
                continue
        except (OSError, ValueError, IndexError, UnicodeError, KeyError):
            pass
        blocked.append(row)
    return blocked


def apply(manifest, *, registry, snapshot_fetcher, runner=subprocess.run):
    from src.engine.infrastructure.runtime_release_router import runtime_release_set_lock
    with runtime_release_set_lock(Path(manifest["workspace"])):
        return _apply_locked(manifest, registry=registry, snapshot_fetcher=snapshot_fetcher, runner=runner)


def _apply_locked(manifest, *, registry, snapshot_fetcher, runner):
    body = {k: v for k, v in manifest.items() if k != "receipt_sha256"}
    if (manifest.get("schema") != SCHEMA or manifest.get("state") != "prepared"
        or manifest.get("symbol") != "034020" or manifest.get("owner") != "episode"
        or manifest.get("receipt_sha256") != digest(body)
        or manifest.get("units") != list(units())
        or manifest.get("systemd_dir") != "/etc/systemd/system"):
        raise ValueError("retirement_reviewed_manifest_invalid")
    workspace = Path(manifest["workspace"]).resolve(strict=True)
    current = prepare(workspace)
    receipt_path = workspace / "data/runtime/retirements/doosan-episode-retirement.json"
    previous = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    resumable = bool(previous and previous.get("state") in {"entry_retired", "terminal"}
                     and previous.get("reviewed_manifest_sha256") == manifest["receipt_sha256"]
                     and previous.get("receipt_sha256") == digest({k: v for k, v in previous.items() if k != "receipt_sha256"}))
    remaining = current["installed_files"]
    if (current["guard_file_sha256"] != manifest["guard_file_sha256"]
        or (remaining != manifest["installed_files"] and not (
            resumable and all(row in manifest["installed_files"] for row in remaining)))):
        raise ValueError("retirement_manifest_generation_changed")
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.trading.order.symbol_owner_policy_apply import find_running_trading_processes
    release, _ = selected_release(workspace)
    guard = release / manifest["guard_file"]
    if not guard.is_file() or hashlib.sha256(guard.read_bytes()).hexdigest() != manifest["guard_file_sha256"]:
        raise ValueError("retirement_reviewed_release_not_selected")
    if blocking_retirement_processes(find_running_trading_processes(), workspace=workspace):
        raise ValueError("retirement_episode_or_unknown_process_not_quiescent")
    installed_units = set()
    for unit in units():
        status = runner(["systemctl", "show", unit, "--property=LoadState", "--value"],
                        check=True, capture_output=True, text=True).stdout.strip()
        if status == "loaded":
            installed_units.add(unit)
        elif status != "not-found" and not (status == "masked" and unit.endswith(".service")):
            raise ValueError("retirement_unit_load_state_invalid:" + unit)
    # Prevent new timer starts before inspecting services. Never stop an active
    # residual exit owner merely because its next BUY is retired.
    for unit in units():
        if unit.endswith(".timer") and unit in installed_units:
            runner(["systemctl", "disable", "--now", unit], check=True, capture_output=True, text=True)
    services = [unit for unit in units() if unit.endswith(".service") and unit in installed_units]
    for unit in services:
        state = runner(["systemctl", "show", unit, "--property=ActiveState,MainPID", "--value"],
                       check=True, capture_output=True, text=True).stdout.splitlines()
        if not state or not {"inactive", "failed"}.intersection(state) or any(
            value.isdigit() and int(value) != 0 for value in state
        ):
            raise ValueError("retirement_episode_service_not_quiescent:" + unit)
    # Stop future triggers first. Existing SELL/cancel responsibility prevents
    # reaching this point until its own services and residuals are terminal.
    for unit in services:
        runner(["systemctl", "disable", unit], check=True, capture_output=True, text=True)
    snapshot = snapshot_fetcher()
    second = snapshot_fetcher()
    from src.trading.order.symbol_owner_policy_apply import validate_broker_snapshot_contract
    validate_broker_snapshot_contract(snapshot, symbols={"034020"}, migration_receipts_allowed=False)
    if snapshot.get("snapshot_sha256") != second.get("snapshot_sha256"):
        raise ValueError("retirement_broker_snapshot_changed")
    observed = datetime.now(KST)
    flat = require_flat(second, registry, observed_at=observed)
    for row in remaining:
        path = Path(row["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("retirement_installed_file_changed")
    # The native snapshot is fetched after timers are disabled; no old
    # planning/prepare receipt can substitute for the apply-time snapshot.
    if blocking_retirement_processes(find_running_trading_processes(), workspace=workspace):
        raise ValueError("retirement_trading_process_started_during_transition")
    # Persist the rollback exclusion before deletion. If reload fails, a retry
    # can finish deletion; an old release cannot restore the retired entry path.
    terminal = {**body, "state": "entry_retired", "runtime_effect": True, "flat_receipt": flat,
                "reviewed_manifest_sha256": manifest["receipt_sha256"],
                "applied_at_kst": datetime.now(KST).isoformat()}
    terminal["receipt_sha256"] = digest(terminal)
    atomic_write_json(receipt_path, terminal)
    for row in remaining:
        path = Path(row["path"])
        path.unlink()
        if path.parent.name.endswith(".d") and not any(path.parent.iterdir()):
            path.parent.rmdir()
    # Removing timers alone leaves generic templates able to restart the old
    # retired IDs. Mask only these flat/inactive instances; foreign owners and
    # the shared templates keep their current code and processes.
    masked = [unit for unit in units() if unit.endswith(".service")]
    runner(["systemctl", "mask", *masked], check=True, capture_output=True, text=True)
    runner(["systemctl", "daemon-reload"], check=True, capture_output=True, text=True)
    for unit in masked:
        state = runner(["systemctl", "show", unit, "--property=LoadState", "--value"],
                       check=True, capture_output=True, text=True).stdout.strip()
        if state != "masked":
            raise ValueError("retirement_instance_mask_not_observed:" + unit)
    terminal["state"] = "terminal"
    terminal["masked_instances"] = masked
    terminal["receipt_sha256"] = digest({k: v for k, v in terminal.items() if k != "receipt_sha256"})
    atomic_write_json(receipt_path, terminal)
    return terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply-reviewed-manifest", type=Path)
    args = parser.parse_args()
    if args.apply_reviewed_manifest:
        from src.trading.order.owner_custody_registry import default_order_owner_registry
        from src.trading.order.symbol_owner_policy_apply import collect_broker_snapshot
        from src.trading.config.symbol_owner_standing_authority import load_standing_authority
        from src.utils import kiwoom_utils
        manifest = json.loads(args.apply_reviewed_manifest.read_text())
        account_key = load_standing_authority()["broker_account_key"]
        if os.environ.setdefault("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", account_key) != account_key:
            raise ValueError("retirement_broker_account_binding_mismatch")
        result = apply(manifest, registry=default_order_owner_registry(),
            snapshot_fetcher=lambda: collect_broker_snapshot(
                kiwoom_utils.get_kiwoom_token(require_issued_today=True), {"034020"}, tuple()))
    else:
        result = prepare(args.workspace)
    if args.output:
        atomic_write_json(args.output, result)
    print(json.dumps({k: result[k] for k in ("state", "symbol", "owner", "receipt_sha256")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
