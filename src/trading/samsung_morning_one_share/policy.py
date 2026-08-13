"""Fixed, auditable policy for the Samsung morning two-leg machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from src.trading.order.episode_quantity import EPISODE_TOTAL_QUANTITY
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks


@dataclass(frozen=True)
class EntryWindow:
    route: str
    open_time: time
    deadline: time
    drawdown_pct: float


@dataclass(frozen=True)
class MinuteBar:
    timestamp: datetime
    open_price: int
    high_price: int
    low_price: int
    close_price: int


@dataclass(frozen=True)
class MorningReentrySignal:
    setup_bar: MinuteBar
    signal_bar: MinuteBar
    rolling_high: int
    rolling_low: int
    drawdown_pct: float
    near_low_pct: float


@dataclass(frozen=True)
class MorningOneSharePolicy:
    symbol: str = "005930"
    quantity: int = EPISODE_TOTAL_QUANTITY
    nxt: EntryWindow = EntryWindow("NXT", time(8, 0), time(8, 10), 3.0)
    sor: EntryWindow = EntryWindow("SOR", time(9, 0), time(9, 30), 0.75)
    target_ticks: int = 2
    runtime_policy_source: str = "baseline_default"
    runtime_policy_hash: str = ""

    def __post_init__(self) -> None:
        if self.symbol != "005930" or self.quantity != EPISODE_TOTAL_QUANTITY:
            raise ValueError("policy_is_hard_limited_to_005930_episode_quantity")
        if self.target_ticks <= 0:
            raise ValueError("invalid_exit_policy")
        if self.nxt.route != "NXT" or self.sor.route != "SOR":
            raise ValueError("invalid_route_priority")

    @staticmethod
    def entry_price(open_price: int, drawdown_pct: float) -> int:
        if open_price <= 0 or drawdown_pct <= 0:
            raise ValueError("invalid_open_or_drawdown")
        return clamp_price_to_tick(open_price * (1.0 - drawdown_pct / 100.0))

    def target_price(self, fill_price: int) -> int:
        if fill_price <= 0:
            raise ValueError("invalid_fill_price")
        return move_price_by_ticks(fill_price, self.target_ticks)

    @classmethod
    def entry_legs(cls, open_price: int, drawdown_pct: float) -> list[dict]:
        base_price = cls.entry_price(open_price, drawdown_pct)
        return [
            {
                "leg_id": "base_plus_1tick",
                "price_role": "aggressive_50pct",
                "entry_price": move_price_by_ticks(base_price, 1),
            },
            {
                "leg_id": "base",
                "price_role": "conservative_50pct",
                "entry_price": base_price,
            },
        ]


DEFAULT_POLICY = MorningOneSharePolicy()


@dataclass(frozen=True)
class MorningReentryPolicy:
    """User-approved bounded SOR episode after the opening episode completes."""

    symbol: str = "005930"
    route: str = "SOR"
    quantity: int = EPISODE_TOTAL_QUANTITY
    scan_start: time = time(9, 0)
    scan_last_bar: time = time(10, 0)
    lookback_bars: int = 15
    rolling_high_drawdown_pct: float = 0.75
    rolling_low_proximity_pct: float = 0.35
    confirmation_bars: int = 2
    reclaim_ticks: int = 1
    entry_offset_ticks: int = 1
    entry_valid_completed_bars: int = 3
    target_ticks: int = 2
    max_source_lag_minutes: int = 2
    runtime_policy_source: str = "user_approved_sor_reentry_2026-08-12"
    runtime_policy_hash: str = (
        "6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a"
    )

    def __post_init__(self) -> None:
        if (
            self.symbol != "005930"
            or self.route != "SOR"
            or self.quantity != EPISODE_TOTAL_QUANTITY
        ):
            raise ValueError("reentry_policy_is_hard_limited_to_episode_quantity_sor")
        if not self.scan_start <= self.scan_last_bar:
            raise ValueError("invalid_reentry_scan_window")
        if (
            self.lookback_bars < 2
            or min(
                self.rolling_high_drawdown_pct,
                self.rolling_low_proximity_pct,
                self.confirmation_bars,
                self.reclaim_ticks,
                self.entry_offset_ticks,
                self.entry_valid_completed_bars,
                self.target_ticks,
                self.max_source_lag_minutes,
            )
            <= 0
        ):
            raise ValueError("invalid_reentry_policy")

    def evaluate(self, bars: list[MinuteBar]) -> MorningReentrySignal | None:
        required = self.lookback_bars + self.confirmation_bars
        if len(bars) < required:
            return None
        confirmation = bars[-1]
        if not self.scan_start <= confirmation.timestamp.time() <= self.scan_last_bar:
            return None
        setup_index = len(bars) - self.confirmation_bars - 1
        setup = bars[setup_index]
        rolling_window = bars[setup_index - self.lookback_bars + 1 : setup_index + 1]
        confirmation_window = bars[
            setup_index : setup_index + self.confirmation_bars + 1
        ]
        combined = rolling_window + confirmation_window[1:]
        if any(
            current.timestamp - previous.timestamp != timedelta(minutes=1)
            for previous, current in zip(combined, combined[1:])
        ):
            return None
        rolling_high = max(bar.high_price for bar in rolling_window)
        rolling_low = min(bar.low_price for bar in rolling_window)
        if min(rolling_high, rolling_low, setup.close_price) <= 0:
            return None
        drawdown_pct = (rolling_high - setup.close_price) / rolling_high * 100.0
        near_low_pct = (setup.close_price - rolling_low) / rolling_low * 100.0
        if drawdown_pct + 1e-12 < self.rolling_high_drawdown_pct:
            return None
        if near_low_pct - 1e-12 > self.rolling_low_proximity_pct:
            return None
        if min(bar.low_price for bar in confirmation_window) < setup.low_price:
            return None
        if confirmation.close_price < move_price_by_ticks(
            setup.close_price, self.reclaim_ticks
        ):
            return None
        return MorningReentrySignal(
            setup,
            confirmation,
            rolling_high,
            rolling_low,
            drawdown_pct,
            near_low_pct,
        )

    def target_price(self, fill_price: int) -> int:
        if fill_price <= 0:
            raise ValueError("invalid_fill_price")
        return move_price_by_ticks(fill_price, self.target_ticks)

    def entry_legs(self, confirmation_close: int) -> list[dict]:
        anchor = clamp_price_to_tick(confirmation_close)
        first = move_price_by_ticks(anchor, -self.entry_offset_ticks)
        return [
            {
                "leg_id": "confirmation_close_minus_1tick",
                "price_role": "aggressive_50pct",
                "entry_price": first,
            },
            {
                "leg_id": "confirmation_close_minus_2ticks",
                "price_role": "conservative_50pct",
                "entry_price": move_price_by_ticks(first, -1),
            },
        ]


DEFAULT_REENTRY_POLICY = MorningReentryPolicy()
