"""CLI for the independently scheduled Samsung morning two-leg machine."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from src.trading.samsung_morning_one_share.gateway import KiwoomOneShareGateway
from src.trading.samsung_morning_one_share.machine import (
    DEFAULT_STATE_PATH,
    KST,
    SamsungMorningOneShareMachine,
)
from src.trading.samsung_morning_one_share.policy import (
    DEFAULT_POLICY,
    DEFAULT_REENTRY_POLICY,
)
from src.trading.samsung_morning_one_share.reentry import (
    DEFAULT_REENTRY_STATE_PATH,
    SamsungMorningSORReentryMachine,
    runtime_ledgers_allow_service_start,
)
from src.trading.order.samsung_entry_policy import (
    OPERATOR_OVERRIDE_RUNTIME_SOURCE,
    load_applied_machine_policy,
)
from src.trading.samsung_morning_one_share.preflight import (
    DEFAULT_AUTHORITY_PATH,
    validate_authority,
)

ENABLE_ENV = "KORSTOCKSCAN_SAMSUNG_MORNING_ONE_SHARE_ENABLED"
LIVE_CONFIRMATION = "005930_MORNING_TWO_EPISODE_LIVE"


def _env_enabled() -> bool:
    return str(os.getenv(ENABLE_ENV, "false")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=2.0)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--state-path", type=Path, default=None)
    parser.add_argument("--lock-path", type=Path, default=None)
    return parser


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
    args = _parser().parse_args(argv)
    live_enabled = bool(
        args.live and _env_enabled() and args.confirm == LIVE_CONFIRMATION
    )
    if args.live and not live_enabled:
        raise SystemExit(
            f"live authority requires {ENABLE_ENV}=true and "
            f"--confirm {LIVE_CONFIRMATION}"
        )
    if live_enabled and args.once:
        raise SystemExit(
            "--once is dry-run only; live mode requires continuous custody"
        )
    if live_enabled and (args.state_path is not None or args.lock_path is not None):
        raise SystemExit("live mode forbids custom state or lock paths")
    if live_enabled:
        authority_ok, authority_reason = validate_authority(
            DEFAULT_AUTHORITY_PATH, require_live_main_bot_runtime=True
        )
        if not authority_ok:
            print(f"live authority artifact blocked: {authority_reason}")
            return 4
        rollover_ok, rollover_reason = runtime_ledgers_allow_service_start(
            target_date=datetime.now(tz=KST).date()
        )
        if not rollover_ok:
            print(f"live prior reentry state blocked: {rollover_reason}")
            return 6
    policy = DEFAULT_POLICY
    applied: dict | None = None
    applied_hash = ""
    applied_policy_source = "preopen_applied_policy"
    if live_enabled:
        target_date = datetime.now(tz=KST).date()
        applied, applied_hash, applied_reason = load_applied_machine_policy(
            "morning", target_date=target_date
        )
        if applied is None:
            print(f"live applied entry policy blocked: {applied_reason}")
            return 5
        applied_policy_source = (
            OPERATOR_OVERRIDE_RUNTIME_SOURCE
            if applied_reason == "ready_operator_override"
            else "preopen_applied_policy"
        )
        policy = replace(
            DEFAULT_POLICY,
            nxt=replace(
                DEFAULT_POLICY.nxt,
                drawdown_pct=float(applied["nxt_drawdown_pct"]),
            ),
            sor=replace(
                DEFAULT_POLICY.sor,
                drawdown_pct=float(applied["sor_drawdown_pct"]),
            ),
            target_ticks=int(applied["target_ticks"]),
            runtime_policy_source=applied_policy_source,
            runtime_policy_hash=applied_hash,
        )
    state_path = args.state_path or (
        DEFAULT_STATE_PATH
        if live_enabled
        else DEFAULT_STATE_PATH.with_name(
            "samsung_morning_one_share_dry_run_state.json"
        )
    )
    lock_path = args.lock_path or state_path.with_suffix(".lock")
    lock_handle = _acquire_lock(lock_path)
    if lock_handle is None:
        return 3
    gateway = KiwoomOneShareGateway(order_authority=live_enabled)
    machine = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        policy=policy,
        live_enabled=live_enabled,
    )
    if args.once:
        print(json.dumps(machine.run_once(), ensure_ascii=False, indent=2))
        return 0
    if live_enabled:
        first_terminal = machine.run_until_terminal(interval_sec=args.interval_sec)
        result = {"first_episode": first_terminal, "reentry_episode": None}
        if first_terminal.get("status") == "COMPLETE":
            reentry_policy = replace(
                DEFAULT_REENTRY_POLICY,
                target_ticks=int(applied["target_ticks"]),
                runtime_policy_source=applied_policy_source,
                runtime_policy_hash=applied_hash,
            )
            reentry = SamsungMorningSORReentryMachine(
                gateway=gateway,
                state_path=DEFAULT_REENTRY_STATE_PATH,
                first_episode_state_path=DEFAULT_STATE_PATH,
                policy=reentry_policy,
                live_enabled=True,
            )
            result["reentry_episode"] = reentry.run_until_terminal(
                interval_sec=args.interval_sec
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    machine.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
