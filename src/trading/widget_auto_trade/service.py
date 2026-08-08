"""Service entrypoint for operator-directed widget signal auto trading."""

from __future__ import annotations

import argparse
import fcntl
import os
from pathlib import Path

from src.trading.widget_auto_trade.engine import (
    DEFAULT_STATE_PATH,
    WidgetSignalAutoTrader,
)


def _env_enabled() -> bool:
    return str(
        os.getenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENABLED", "false")
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_qty() -> int:
    return int(os.getenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY", "1") or "1")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=1.0)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--lock-path", type=Path, default=None)
    return parser


def _acquire_single_instance_lock(path: Path):
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
    lock_path = args.lock_path or args.state_path.with_suffix(".lock")
    lock_handle = _acquire_single_instance_lock(lock_path)
    if lock_handle is None:
        return 3
    trader = WidgetSignalAutoTrader(
        state_path=args.state_path,
        entry_qty=_env_qty(),
        enabled=_env_enabled(),
    )
    if args.once:
        trader.run_once()
        return 0
    trader.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
