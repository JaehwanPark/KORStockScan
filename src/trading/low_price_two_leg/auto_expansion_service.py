"""Run every exact-date auto-promoted episode profile under existing guards."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import time as time_module
from datetime import datetime, time
from pathlib import Path

from src.engine.automation.low_price_two_leg_auto_expansion_policy import load_policy
from src.engine.risk.manual_control_exclusion import (
    independent_machine_ownership_source,
)
from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway
from src.trading.low_price_two_leg.machine import (
    LowPriceTwoLegMachine,
    default_state_path,
)
from src.trading.low_price_two_leg.profiles import (
    MachineProfile,
    RegularTwoLegPolicy,
)
from src.trading.order.regular_two_leg_machine import KST

ENABLE_ENV = "KORSTOCKSCAN_LOW_PRICE_TWO_LEG_AUTO_EXPANSION_ENABLED"
LOCK_PATH = Path("data/runtime/low_price_two_leg/auto_expansion_service.lock")


def _enabled() -> bool:
    return str(os.getenv(ENABLE_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def _profile(row: dict, *, authority_hash: str) -> MachineProfile:
    policy = row["policy"]
    return MachineProfile(
        profile_id=row["profile_id"],
        symbol=row["symbol"],
        name=row["name"],
        session=row["session"],
        policy=RegularTwoLegPolicy(
            symbol=row["symbol"],
            scan_start=time.fromisoformat(policy["scan_start"]),
            scan_last_bar=time.fromisoformat(policy["scan_end"]),
            lookback_bars=int(policy["lookback_bars"]),
            rolling_high_drawdown_pct=float(policy["rolling_high_drawdown_pct"]),
            rolling_low_proximity_pct=float(policy["rolling_low_proximity_pct"]),
            entry_offsets_ticks=tuple(
                int(value) for value in policy["entry_offsets_ticks"]
            ),
            entry_valid_completed_bars=int(policy["entry_valid_completed_bars"]),
            target_ticks=int(policy["target_ticks"]),
            runtime_policy_source="exact_date_auto_expansion_policy",
            runtime_policy_hash=authority_hash,
            dynamic_authority_hash=authority_hash,
        ),
        enable_env=ENABLE_ENV,
        live_confirmation="EXACT_DATE_AUTO_EXPANSION_POLICY",
    )


def _load_profiles(now: datetime) -> tuple[str, list[MachineProfile]]:
    payload = load_policy(now.date())
    authority_hash = str(payload["policy_hash"])
    profiles = [
        _profile(row, authority_hash=authority_hash)
        for row in payload["profiles"].values()
    ]
    for profile in profiles:
        if not independent_machine_ownership_source(
            profile.symbol,
            owner="episode",
            target_date=now.date(),
            new_entry=True,
        ):
            raise ValueError(
                f"episode_auto_expansion_owner_authority_missing:{profile.symbol}"
            )
    return authority_hash, profiles


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-sec", type=float, default=6.0)
    parser.add_argument("--check-active", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    now = datetime.now(KST)
    if not _enabled():
        return 3
    try:
        authority_hash, profiles = _load_profiles(now)
    except (OSError, ValueError, TypeError, KeyError):
        return 4
    if not profiles:
        return 5
    if args.check_active:
        return 0
    lock = _acquire_lock(LOCK_PATH)
    if lock is None:
        return 6
    machines = [
        LowPriceTwoLegMachine(
            profile=profile,
            gateway=KiwoomLowPriceTwoLegGateway(
                symbol=profile.symbol,
                order_authority=True,
                dynamic_authority_hash=authority_hash,
            ),
            state_path=default_state_path(profile),
            live_enabled=True,
        )
        for profile in profiles
    ]
    for machine in machines:
        machine.profit_exit_lock_held = lambda bound=lock: not bound.closed
    while True:
        observed = datetime.now(KST)
        states = [machine.run_once(now=observed) for machine in machines]
        if args.once:
            print(json.dumps(states, ensure_ascii=False, indent=2))
            return 0
        if observed.time().replace(tzinfo=None) > time(20, 1):
            return 0
        time_module.sleep(max(1.0, float(args.interval_sec)))


if __name__ == "__main__":
    raise SystemExit(main())
