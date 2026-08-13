"""Service entrypoint for operator-directed widget signal auto trading."""

from __future__ import annotations

import argparse
import fcntl
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_symbol_runtime_policy import (
    WidgetSymbolRuntimePolicyLoader,
)
from src.trading.widget_auto_trade.engine import (
    ALL_WIDGET_SPECS,
    CALIBRATED_WIDGET_SPECS,
    DEFAULT_STATE_PATH,
    SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    WidgetSpec,
    WidgetSignalAutoTrader,
)
from src.trading.widget_auto_trade.notifications import (
    WidgetAutoTradeEntryTelegramNotifier,
)
from src.trading.widget_auto_trade.policy import WIDGET_AUTO_TRADE_LEG_QUANTITY

LEGACY_DEFAULT_SYMBOLS = frozenset({"005930", "034020", "042660"})


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
    default = str(WIDGET_AUTO_TRADE_LEG_QUANTITY)
    return int(
        os.getenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY", default) or default
    )


def _env_specs() -> tuple[WidgetSpec, ...]:
    """Return the explicitly selected execution symbols.

    An omitted variable preserves the legacy all-symbol behavior.  Once the
    variable is present it is a strict allowlist: blank or unknown values fail
    closed instead of accidentally restoring order authority to every widget.
    """

    raw = os.getenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS")
    requested = (
        set(LEGACY_DEFAULT_SYMBOLS)
        if raw is None
        else {
            token.strip().upper().removeprefix("A")
            for token in raw.split(",")
            if token.strip()
        }
    )
    promoted = set(
        WidgetSymbolRuntimePolicyLoader()
        .resolve_all(observed_date=datetime.now(KST).date())
        .keys()
    )
    requested.update(promoted)
    by_code = {spec.code: spec for spec in ALL_WIDGET_SPECS}
    if not requested:
        raise ValueError("widget_auto_trader_symbols_empty")
    unknown = sorted(requested - by_code.keys())
    if unknown:
        raise ValueError(f"widget_auto_trader_symbols_unknown:{','.join(unknown)}")
    samsung_policy = str(
        os.getenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SAMSUNG_EXECUTION_POLICY", "") or ""
    ).strip()
    if samsung_policy and samsung_policy != SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID:
        raise ValueError(f"widget_auto_trader_samsung_policy_unknown:{samsung_policy}")
    return tuple(
        (
            replace(spec, execution_policy_id=samsung_policy)
            if spec.code == "005930" and samsung_policy
            else spec
        )
        for spec in ALL_WIDGET_SPECS
        if spec.code in requested
    )


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
        specs=_env_specs(),
        dynamic_spec_catalog=CALIBRATED_WIDGET_SPECS,
        entry_action_notifier=WidgetAutoTradeEntryTelegramNotifier(),
    )
    if args.once:
        trader.run_once()
        return 0
    trader.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
