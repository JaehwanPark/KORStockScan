"""Fixed, auditable policy for the Samsung midday two-leg machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from src.trading.order.episode_quantity import EPISODE_TOTAL_QUANTITY
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks


@dataclass(frozen=True)
class MinuteBar:
    timestamp: datetime
    open_price: int
    high_price: int
    low_price: int
    close_price: int


@dataclass(frozen=True)
class MiddaySignal:
    signal_bar: MinuteBar
    rolling_high: int
    rolling_low: int
    drawdown_pct: float
    near_low_pct: float
    entry_price: int


@dataclass(frozen=True)
class MiddayOneSharePolicy:
    symbol: str = "005930"
    route: str = "SOR"
    quantity: int = EPISODE_TOTAL_QUANTITY
    scan_start: time = time(13, 15)
    # The analyzed window is half-open [13:15, 13:55), so 13:54 is the
    # final eligible completed signal bar.
    scan_last_bar: time = time(13, 54)
    lookback_bars: int = 30
    rolling_high_drawdown_pct: float = 1.25
    rolling_low_proximity_pct: float = 0.20
    entry_offset_ticks: int = 1
    entry_valid_completed_bars: int = 5
    target_ticks: int = 2
    max_source_lag_minutes: int = 2
    runtime_policy_source: str = "baseline_default"
    runtime_policy_hash: str = ""

    def __post_init__(self) -> None:
        if (
            self.symbol != "005930"
            or self.route != "SOR"
            or self.quantity != EPISODE_TOTAL_QUANTITY
        ):
            raise ValueError("policy_is_hard_limited_to_005930_episode_quantity_sor")
        if not (self.scan_start <= self.scan_last_bar):
            raise ValueError("invalid_scan_window")
        if self.lookback_bars < 2:
            raise ValueError("invalid_lookback")
        if (
            min(
                self.rolling_high_drawdown_pct,
                self.rolling_low_proximity_pct,
                self.entry_offset_ticks,
                self.entry_valid_completed_bars,
                self.target_ticks,
                self.max_source_lag_minutes,
            )
            <= 0
        ):
            raise ValueError("invalid_midday_policy")

    def evaluate(self, bars: list[MinuteBar]) -> MiddaySignal | None:
        if len(bars) < self.lookback_bars:
            return None
        candidate = bars[-1]
        if not self.scan_start <= candidate.timestamp.time() <= self.scan_last_bar:
            return None
        window = bars[-self.lookback_bars :]
        if any(
            current.timestamp - previous.timestamp != timedelta(minutes=1)
            for previous, current in zip(window, window[1:])
        ):
            return None
        rolling_high = max(bar.high_price for bar in window)
        rolling_low = min(bar.low_price for bar in window)
        close = candidate.close_price
        if min(rolling_high, rolling_low, close) <= 0:
            return None
        drawdown_pct = (rolling_high - close) / rolling_high * 100.0
        near_low_pct = (close - rolling_low) / rolling_low * 100.0
        if drawdown_pct + 1e-12 < self.rolling_high_drawdown_pct:
            return None
        if near_low_pct - 1e-12 > self.rolling_low_proximity_pct:
            return None
        return MiddaySignal(
            signal_bar=candidate,
            rolling_high=rolling_high,
            rolling_low=rolling_low,
            drawdown_pct=drawdown_pct,
            near_low_pct=near_low_pct,
            entry_price=move_price_by_ticks(close, -self.entry_offset_ticks),
        )

    def target_price(self, fill_price: int) -> int:
        if fill_price <= 0:
            raise ValueError("invalid_fill_price")
        return move_price_by_ticks(fill_price, self.target_ticks)

    @staticmethod
    def entry_legs(signal_close: int) -> list[dict]:
        executable_close = clamp_price_to_tick(signal_close)
        return [
            {
                "leg_id": "signal_close",
                "price_role": "aggressive_50pct",
                "entry_price": executable_close,
            },
            {
                "leg_id": "signal_close_minus_1tick",
                "price_role": "conservative_50pct",
                "entry_price": move_price_by_ticks(executable_close, -1),
            },
        ]


DEFAULT_POLICY = MiddayOneSharePolicy()
