"""Immutable symbol/session profiles selected by clean-baseline replay."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

from src.trading.order.episode_quantity import EPISODE_TOTAL_QUANTITY
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks

SAMSUNG_HEAVY_MIDDAY_WINDOW = (time(13, 20), time(13, 29))
AFTERNOON_WINDOW = (time(14, 0), time(14, 40))
SK_ETERNIX_MIDDAY_LEGACY_WINDOW = (time(13, 30), time(13, 54))
SK_ETERNIX_MIDDAY_WINDOW = (time(13, 30), time(13, 39))
MIRAE_ASSET_MORNING_WINDOW = (time(9, 35), time(9, 44))
JEJU_SEMICONDUCTOR_MORNING_WINDOW = (time(9, 10), time(9, 49))
DOOSAN_ENERBILITY_MORNING_WINDOW = (time(9, 20), time(9, 49))
HANWHA_OCEAN_LATE_MORNING_WINDOW = (time(10, 5), time(10, 24))
KAKAO_MORNING_WINDOW = (time(9, 20), time(9, 39))
KAKAO_LATE_MORNING_LEGACY_WINDOW = (time(10, 5), time(10, 34))
KAKAO_LATE_MORNING_WINDOW = (time(10, 5), time(10, 24))
SK_ETERNIX_MORNING_WINDOW = (time(9, 50), time(9, 59))
MIRAE_ASSET_MIDDAY_WINDOW = (time(13, 15), time(13, 24))
KEPCO_AFTERNOON_WINDOW = (time(14, 0), time(14, 29))
SAMSUNG_HEAVY_MORNING_WINDOW = (time(9, 20), time(9, 29))
SAMSUNG_EA_MORNING_WINDOW = (time(9, 45), time(9, 59))
SAMSUNG_EA_LATE_MORNING_WINDOW = (time(10, 5), time(10, 14))
DOOSAN_ENERBILITY_LATE_MORNING_WINDOW = (time(10, 15), time(10, 59))
KAKAO_MIDDAY_WINDOW = (time(13, 20), time(13, 39))
SAMSUNG_EA_AFTERNOON_WINDOW = (time(14, 5), time(14, 34))
SK_TELECOM_AFTERNOON_WINDOW = (time(14, 25), time(14, 34))
PROFILE_REVISION_EFFECTIVE_DATE = date(2026, 8, 19)
ALLOWED_SYMBOLS = frozenset(
    {
        "006800",
        "010140",
        "015760",
        "017670",
        "028050",
        "034020",
        "035720",
        "042660",
        "080220",
        "475150",
    }
)
SUPPORTED_REGULAR_SCAN_WINDOWS = frozenset(
    {
        SAMSUNG_HEAVY_MIDDAY_WINDOW,
        AFTERNOON_WINDOW,
        SK_ETERNIX_MIDDAY_LEGACY_WINDOW,
        SK_ETERNIX_MIDDAY_WINDOW,
        MIRAE_ASSET_MORNING_WINDOW,
        JEJU_SEMICONDUCTOR_MORNING_WINDOW,
        DOOSAN_ENERBILITY_MORNING_WINDOW,
        HANWHA_OCEAN_LATE_MORNING_WINDOW,
        KAKAO_MORNING_WINDOW,
        KAKAO_LATE_MORNING_LEGACY_WINDOW,
        KAKAO_LATE_MORNING_WINDOW,
        SK_ETERNIX_MORNING_WINDOW,
        MIRAE_ASSET_MIDDAY_WINDOW,
        KEPCO_AFTERNOON_WINDOW,
        SAMSUNG_HEAVY_MORNING_WINDOW,
        SAMSUNG_EA_MORNING_WINDOW,
        SAMSUNG_EA_LATE_MORNING_WINDOW,
        DOOSAN_ENERBILITY_LATE_MORNING_WINDOW,
        KAKAO_MIDDAY_WINDOW,
        SAMSUNG_EA_AFTERNOON_WINDOW,
        SK_TELECOM_AFTERNOON_WINDOW,
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
    quantity: int = EPISODE_TOTAL_QUANTITY
    lookback_bars: int = 30
    rolling_high_drawdown_pct: float = 1.25
    rolling_low_proximity_pct: float = 0.20
    entry_offsets_ticks: tuple[int, int] = (0, -1)
    entry_valid_completed_bars: int = 5
    target_ticks: int = 2
    max_source_lag_minutes: int = 2
    runtime_policy_source: str = "clean_baseline_replay_selected_default"
    runtime_policy_hash: str = ""

    def __post_init__(self) -> None:
        if self.symbol not in ALLOWED_SYMBOLS:
            raise ValueError("symbol_not_in_low_price_machine_allowlist")
        if self.route != "SOR" or self.quantity != EPISODE_TOTAL_QUANTITY:
            raise ValueError("policy_requires_episode_quantity_integrated_sor")
        if (self.scan_start, self.scan_last_bar) not in SUPPORTED_REGULAR_SCAN_WINDOWS:
            raise ValueError("unsupported_regular_scan_window")
        if self.lookback_bars < 2:
            raise ValueError("invalid_lookback")
        if (
            min(
                self.rolling_high_drawdown_pct,
                self.rolling_low_proximity_pct,
                self.entry_valid_completed_bars,
                self.target_ticks,
                self.max_source_lag_minutes,
            )
            <= 0
        ):
            raise ValueError("invalid_regular_two_leg_policy")
        if (
            len(self.entry_offsets_ticks) != 2
            or len(set(self.entry_offsets_ticks)) != 2
            or any(
                not isinstance(offset, int)
                or isinstance(offset, bool)
                or not -10 <= offset <= 0
                for offset in self.entry_offsets_ticks
            )
        ):
            raise ValueError("invalid_entry_offsets_ticks")

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
            entry_price=move_price_by_ticks(close, self.entry_offsets_ticks[0]),
        )

    def target_price(self, fill_price: int) -> int:
        if fill_price <= 0:
            raise ValueError("invalid_fill_price")
        return move_price_by_ticks(fill_price, self.target_ticks)

    @staticmethod
    def _leg_id(offset_ticks: int) -> str:
        if offset_ticks == 0:
            return "signal_close"
        suffix = "tick" if abs(offset_ticks) == 1 else "ticks"
        direction = "minus" if offset_ticks < 0 else "plus"
        return f"signal_close_{direction}_{abs(offset_ticks)}{suffix}"

    def entry_legs(self, signal_close: int) -> list[dict]:
        executable_close = clamp_price_to_tick(signal_close)
        return [
            {
                "leg_id": self._leg_id(offset),
                "price_role": f"entry_offset_{offset}_ticks_50pct",
                "entry_price": move_price_by_ticks(executable_close, offset),
            }
            for offset in self.entry_offsets_ticks
        ]

    @property
    def entry_leg_ids(self) -> tuple[str, str]:
        return tuple(self._leg_id(offset) for offset in self.entry_offsets_ticks)


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
    entry_offsets_ticks: tuple[int, int] = (0, -1),
    entry_valid_completed_bars: int = 5,
    target_ticks: int = 2,
    runtime_policy_source: str = "clean_baseline_30d_calibration_16d_holdout_selected_v2",
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
            entry_offsets_ticks=entry_offsets_ticks,
            entry_valid_completed_bars=entry_valid_completed_bars,
            target_ticks=target_ticks,
            runtime_policy_source=runtime_policy_source,
        ),
        enable_env=f"KORSTOCKSCAN_LOW_PRICE_TWO_LEG_{upper}_ENABLED",
        live_confirmation=f"{symbol}_{session.upper()}_TWO_LEG_LIVE",
    )


_PRE_RECOMMENDATION_PROFILES = {
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
            window=SK_ETERNIX_MIDDAY_LEGACY_WINDOW,
            lookback_bars=20,
            drawdown_pct=2.00,
            near_low_pct=0.75,
        ),
        _profile(
            "mirae_asset_morning",
            "006800",
            "미래에셋증권",
            "morning",
            window=MIRAE_ASSET_MORNING_WINDOW,
            lookback_bars=15,
            drawdown_pct=1.75,
            near_low_pct=0.50,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
            runtime_policy_source="clean_baseline_31d_calibration_16d_holdout_penetration_selected_v1",
        ),
        _profile(
            "jeju_semiconductor_morning",
            "080220",
            "제주반도체",
            "morning",
            window=JEJU_SEMICONDUCTOR_MORNING_WINDOW,
            lookback_bars=20,
            drawdown_pct=2.50,
            near_low_pct=0.10,
            entry_valid_completed_bars=3,
            target_ticks=4,
            runtime_policy_source="clean_baseline_31d_calibration_16d_holdout_penetration_selected_v1",
        ),
        _profile(
            "doosan_enerbility_morning",
            "034020",
            "두산에너빌리티",
            "morning",
            window=DOOSAN_ENERBILITY_MORNING_WINDOW,
            lookback_bars=15,
            drawdown_pct=2.00,
            near_low_pct=0.50,
            target_ticks=4,
            runtime_policy_source="clean_baseline_31d_calibration_16d_holdout_penetration_selected_v1",
        ),
        _profile(
            "hanwha_ocean_late_morning",
            "042660",
            "한화오션",
            "late_morning",
            window=HANWHA_OCEAN_LATE_MORNING_WINDOW,
            lookback_bars=20,
            drawdown_pct=1.25,
            near_low_pct=0.10,
            target_ticks=4,
            runtime_policy_source="clean_baseline_31d_calibration_16d_holdout_penetration_selected_v1",
        ),
        _profile(
            "kakao_morning",
            "035720",
            "카카오",
            "morning",
            window=KAKAO_MORNING_WINDOW,
            lookback_bars=15,
            drawdown_pct=0.75,
            near_low_pct=0.35,
            runtime_policy_source="clean_baseline_32d_calibration_16d_holdout_expanded_selected_v1",
        ),
        _profile(
            "kepco_afternoon",
            "015760",
            "한국전력",
            "afternoon",
            window=KEPCO_AFTERNOON_WINDOW,
            lookback_bars=60,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            runtime_policy_source="clean_baseline_32d_calibration_16d_holdout_expanded_selected_v1",
        ),
        _profile(
            "kakao_late_morning",
            "035720",
            "카카오",
            "late_morning",
            window=KAKAO_LATE_MORNING_LEGACY_WINDOW,
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.35,
            runtime_policy_source="clean_baseline_32d_calibration_16d_holdout_expanded_selected_v1",
        ),
        _profile(
            "sk_eternix_morning",
            "475150",
            "SK이터닉스",
            "morning",
            window=SK_ETERNIX_MORNING_WINDOW,
            lookback_bars=15,
            drawdown_pct=1.50,
            near_low_pct=0.75,
            runtime_policy_source="clean_baseline_32d_calibration_16d_holdout_expanded_selected_v1",
        ),
        _profile(
            "mirae_asset_midday",
            "006800",
            "미래에셋증권",
            "midday",
            window=MIRAE_ASSET_MIDDAY_WINDOW,
            lookback_bars=45,
            drawdown_pct=1.00,
            near_low_pct=0.50,
            runtime_policy_source="clean_baseline_32d_calibration_16d_holdout_expanded_selected_v1",
        ),
        _profile(
            "sk_eternix_afternoon",
            "475150",
            "SK이터닉스",
            "afternoon",
            window=AFTERNOON_WINDOW,
            lookback_bars=45,
            drawdown_pct=2.50,
            near_low_pct=0.50,
            runtime_policy_source="clean_baseline_32d_calibration_16d_holdout_expanded_selected_v1",
        ),
    )
}

PRE_RECOMMENDATION_PROFILES = dict(_PRE_RECOMMENDATION_PROFILES)
_REVISION_SOURCE = "clean_baseline_35d_calibration_16d_holdout_user_approved_v1"


def _revise_profile(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] | None = None,
    target_ticks: int,
) -> MachineProfile:
    prior = PRE_RECOMMENDATION_PROFILES[profile_id]
    return replace(
        prior,
        policy=replace(
            prior.policy,
            scan_start=(
                window or (prior.policy.scan_start, prior.policy.scan_last_bar)
            )[0],
            scan_last_bar=(
                window or (prior.policy.scan_start, prior.policy.scan_last_bar)
            )[1],
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            entry_offsets_ticks=(
                entry_offsets_ticks or prior.policy.entry_offsets_ticks
            ),
            target_ticks=target_ticks,
            runtime_policy_source=_REVISION_SOURCE,
            runtime_policy_hash="",
        ),
    )


PROFILES = dict(PRE_RECOMMENDATION_PROFILES)
PROFILES.update(
    {
        "mirae_asset_midday": _revise_profile(
            "mirae_asset_midday",
            lookback_bars=45,
            drawdown_pct=1.00,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "sk_eternix_morning": _revise_profile(
            "sk_eternix_morning",
            lookback_bars=15,
            drawdown_pct=2.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "sk_eternix_midday": _revise_profile(
            "sk_eternix_midday",
            window=SK_ETERNIX_MIDDAY_WINDOW,
            lookback_bars=60,
            drawdown_pct=0.75,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "doosan_enerbility_morning": _revise_profile(
            "doosan_enerbility_morning",
            lookback_bars=15,
            drawdown_pct=1.75,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "mirae_asset_morning": _revise_profile(
            "mirae_asset_morning",
            lookback_bars=30,
            drawdown_pct=1.75,
            near_low_pct=0.75,
            entry_offsets_ticks=(0, -1),
            target_ticks=4,
        ),
        "kakao_morning": _revise_profile(
            "kakao_morning",
            lookback_bars=15,
            drawdown_pct=0.75,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "kakao_late_morning": _revise_profile(
            "kakao_late_morning",
            window=KAKAO_LATE_MORNING_WINDOW,
            lookback_bars=20,
            drawdown_pct=0.50,
            near_low_pct=0.05,
            target_ticks=4,
        ),
    }
)
PROFILES.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "samsung_heavy_morning",
                "010140",
                "삼성중공업",
                "morning",
                window=SAMSUNG_HEAVY_MORNING_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                runtime_policy_source=_REVISION_SOURCE,
            ),
            _profile(
                "doosan_enerbility_late_morning",
                "034020",
                "두산에너빌리티",
                "late_morning",
                window=DOOSAN_ENERBILITY_LATE_MORNING_WINDOW,
                lookback_bars=30,
                drawdown_pct=1.75,
                near_low_pct=0.05,
                runtime_policy_source=_REVISION_SOURCE,
            ),
            _profile(
                "kakao_midday",
                "035720",
                "카카오",
                "midday",
                window=KAKAO_MIDDAY_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.50,
                near_low_pct=0.35,
                runtime_policy_source=_REVISION_SOURCE,
            ),
            _profile(
                "sk_telecom_afternoon",
                "017670",
                "SK텔레콤",
                "afternoon",
                window=SK_TELECOM_AFTERNOON_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.75,
                near_low_pct=0.20,
                runtime_policy_source=_REVISION_SOURCE,
            ),
            _profile(
                "samsung_ea_late_morning",
                "028050",
                "삼성E&A",
                "late_morning",
                window=SAMSUNG_EA_LATE_MORNING_WINDOW,
                lookback_bars=20,
                drawdown_pct=1.50,
                near_low_pct=0.20,
                runtime_policy_source=_REVISION_SOURCE,
            ),
            _profile(
                "samsung_ea_afternoon",
                "028050",
                "삼성E&A",
                "afternoon",
                window=SAMSUNG_EA_AFTERNOON_WINDOW,
                lookback_bars=60,
                drawdown_pct=1.25,
                near_low_pct=0.75,
                runtime_policy_source=_REVISION_SOURCE,
            ),
            _profile(
                "samsung_ea_morning",
                "028050",
                "삼성E&A",
                "morning",
                window=SAMSUNG_EA_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=1.25,
                near_low_pct=0.50,
                runtime_policy_source=_REVISION_SOURCE,
            ),
        )
    }
)


def profiles_for_target_date(target_date: date) -> dict[str, MachineProfile]:
    if target_date < PROFILE_REVISION_EFFECTIVE_DATE:
        return PRE_RECOMMENDATION_PROFILES
    return PROFILES


def get_profile(profile_id: str, *, target_date: date | None = None) -> MachineProfile:
    inventory = (
        PROFILES if target_date is None else profiles_for_target_date(target_date)
    )
    try:
        return inventory[str(profile_id)]
    except KeyError as exc:
        raise ValueError("unknown_low_price_two_leg_profile") from exc
