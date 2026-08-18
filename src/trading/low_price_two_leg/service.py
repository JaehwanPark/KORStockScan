"""CLI for one independently scheduled lower-price two-leg machine."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway
from src.trading.low_price_two_leg.machine import (
    LowPriceTwoLegMachine,
    default_state_path,
)
from src.trading.low_price_two_leg.preflight import validate_authority
from src.trading.low_price_two_leg.policy_runtime import load_applied_profile_policy
from src.trading.low_price_two_leg.profiles import PROFILES, MachineProfile, get_profile
from src.trading.order.regular_two_leg_machine import KST


def _env_enabled(name: str) -> bool:
    return str(os.getenv(name, "false")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _acquire_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def _profile_with_applied_policy(
    profile: MachineProfile, applied: dict, applied_hash: str
) -> MachineProfile:
    """Bind PREOPEN entry/target fields while quantity stays compiled safety."""

    return replace(
        profile,
        policy=replace(
            profile.policy,
            rolling_high_drawdown_pct=float(applied["rolling_high_drawdown_pct"]),
            rolling_low_proximity_pct=float(applied["rolling_low_proximity_pct"]),
            lookback_bars=int(applied["lookback_bars"]),
            entry_valid_completed_bars=int(applied["entry_valid_completed_bars"]),
            target_ticks=int(applied["target_ticks"]),
            runtime_policy_source="preopen_applied_policy",
            runtime_policy_hash=applied_hash,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=2.0)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--state-path", type=Path, default=None)
    parser.add_argument("--lock-path", type=Path, default=None)
    args = parser.parse_args(argv)
    runtime_date = datetime.now(tz=KST).date()
    profile = get_profile(
        args.profile, target_date=runtime_date if args.live else None
    )
    live_enabled = bool(
        args.live
        and _env_enabled(profile.enable_env)
        and args.confirm == profile.live_confirmation
    )
    if args.live and not live_enabled:
        raise SystemExit(
            f"live authority requires {profile.enable_env}=true and "
            f"--confirm {profile.live_confirmation}"
        )
    if live_enabled and args.once:
        raise SystemExit(
            "--once is dry-run only; live mode requires continuous custody"
        )
    if live_enabled and (args.state_path is not None or args.lock_path is not None):
        raise SystemExit("live mode forbids custom state or lock paths")
    if live_enabled:
        authority_ok, authority_reason = validate_authority(profile=profile)
        if not authority_ok:
            print(f"live authority artifact blocked: {authority_reason}")
            return 4
        applied, applied_hash, applied_reason = load_applied_profile_policy(
            profile.profile_id, target_date=runtime_date
        )
        if applied is None:
            print(f"live applied entry policy blocked: {applied_reason}")
            return 5
        profile = _profile_with_applied_policy(profile, applied, applied_hash)
    state_path = args.state_path or (
        default_state_path(profile)
        if live_enabled
        else default_state_path(profile).with_name(
            f"{profile.profile_id}_dry_run_state.json"
        )
    )
    lock_path = args.lock_path or state_path.with_suffix(".lock")
    lock_handle = _acquire_lock(lock_path)
    if lock_handle is None:
        return 3
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol=profile.symbol, order_authority=live_enabled
    )
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=state_path,
        live_enabled=live_enabled,
    )
    if args.once:
        print(json.dumps(machine.run_once(), ensure_ascii=False, indent=2))
        return 0
    if live_enabled:
        terminal = machine.run_until_terminal(interval_sec=args.interval_sec)
        print(json.dumps(terminal, ensure_ascii=False, indent=2))
        return 0
    machine.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
