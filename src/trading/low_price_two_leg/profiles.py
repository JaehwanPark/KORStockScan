"""Immutable symbol/session profiles selected by clean-baseline replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks

SAMSUNG_HEAVY_MIDDAY_WINDOW = (time(13, 20), time(13, 29))
AFTERNOON_WINDOW = (time(14, 0), time(14, 40))
SK_ETERNIX_MIDDAY_WINDOW = (time(13, 30), time(13, 54))
ALLOWED_SYMBOLS = frozenset({"010140", "475150"})
SUPPORTED_REGULAR_SCAN_WINDOWS = frozenset(
    {
        SAMSUNG_HEAVY_MIDDAY_WINDOW,
        AFTERNOON_WINDOW,
        SK_ETERNIX_MIDDAY_WINDOW,
    }
)


@dataclass(frozen=True)
class MinuteBar:
    timestamp: datetime
    open_price: int
    high_price: int
    low_price: int
    close_price: int


@dataclass(frozen=True)
class RegularSignal:
    signal_bar: MinuteBar
    rolling_high: int
    rolling_low: int
    drawdown_pct: float
    near_low_pct: float
    entry_price: int


@dataclass(frozen=True)
class RegularTwoLegPolicy:
    symbol: str
    scan_start: time
    scan_last_bar: time
    route: str = "SOR"
    quantity: int = 2
    lookback_bars: int = 30
    rolling_high_drawdown_pct: float = 1.25
    rolling_low_proximity_pct: float = 0.20
    entry_offset_ticks: int = 1
    entry_valid_completed_bars: int = 5
    target_ticks: int = 2
    max_source_lag_minutes: int = 2
    runtime_policy_source: str = "clean_baseline_replay_selected_default"
    runtime_policy_hash: str = ""

    def __post_init__(self) -> None:
        if self.symbol not in ALLOWED_SYMBOLS:
            raise ValueError("symbol_not_in_low_price_machine_allowlist")
        if self.route != "SOR" or self.quantity != 2:
            raise ValueError("policy_requires_two_share_integrated_sor")
        if (self.scan_start, self.scan_last_bar) not in SUPPORTED_REGULAR_SCAN_WINDOWS:
            raise ValueError("unsupported_regular_scan_window")
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
            raise ValueError("invalid_regular_two_leg_policy")

    def evaluate(self, bars: list[MinuteBar]) -> RegularSignal | None:
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
        return RegularSignal(
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


@dataclass(frozen=True)
class MachineProfile:
    profile_id: str
    symbol: str
    name: str
    session: str
    policy: RegularTwoLegPolicy
    enable_env: str
    live_confirmation: str


def _profile(
    profile_id: str,
    symbol: str,
    name: str,
    session: str,
    *,
    window: tuple[time, time],
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
) -> MachineProfile:
    upper = profile_id.upper()
    return MachineProfile(
        profile_id=profile_id,
        symbol=symbol,
        name=name,
        session=session,
        policy=RegularTwoLegPolicy(
            symbol=symbol,
            scan_start=window[0],
            scan_last_bar=window[1],
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            runtime_policy_source="clean_baseline_30d_calibration_16d_holdout_selected_v2",
        ),
        enable_env=f"KORSTOCKSCAN_LOW_PRICE_TWO_LEG_{upper}_ENABLED",
        live_confirmation=f"{symbol}_{session.upper()}_TWO_LEG_LIVE",
    )


PROFILES = {
    profile.profile_id: profile
    for profile in (
        _profile(
            "samsung_heavy_midday",
            "010140",
            "삼성중공업",
            "midday",
            window=SAMSUNG_HEAVY_MIDDAY_WINDOW,
            lookback_bars=30,
            drawdown_pct=0.75,
            near_low_pct=0.35,
        ),
        _profile(
            "samsung_heavy_afternoon",
            "010140",
            "삼성중공업",
            "afternoon",
            window=AFTERNOON_WINDOW,
            lookback_bars=30,
            drawdown_pct=1.25,
            near_low_pct=0.20,
        ),
        _profile(
            "sk_eternix_midday",
            "475150",
            "SK이터닉스",
            "midday",
            window=SK_ETERNIX_MIDDAY_WINDOW,
            lookback_bars=20,
            drawdown_pct=2.00,
            near_low_pct=0.75,
        ),
    )
}


def get_profile(profile_id: str) -> MachineProfile:
    try:
        return PROFILES[str(profile_id)]
    except KeyError as exc:
        raise ValueError("unknown_low_price_two_leg_profile") from exc
