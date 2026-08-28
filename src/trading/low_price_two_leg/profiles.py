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
DOOSAN_ENERBILITY_LATE_MORNING_REVISED_WINDOW = (time(10, 15), time(10, 34))
KAKAO_MIDDAY_WINDOW = (time(13, 20), time(13, 39))
SAMSUNG_EA_AFTERNOON_WINDOW = (time(14, 5), time(14, 34))
SK_TELECOM_AFTERNOON_WINDOW = (time(14, 25), time(14, 34))
SK_TELECOM_MORNING_WINDOW = (time(9, 10), time(9, 29))
SK_TELECOM_LATE_MORNING_WINDOW = (time(10, 45), time(10, 59))
SK_TELECOM_LATE_MORNING_REVISED_WINDOW = (time(10, 45), time(10, 54))
SK_ETERNIX_AFTERNOON_REVISED_WINDOW = (time(14, 15), time(14, 40))
HANSE_MORNING_WINDOW = (time(9, 15), time(9, 44))
HANSE_AFTERNOON_WINDOW = (time(14, 20), time(14, 29))
CJ_CGV_MIDDAY_WINDOW = (time(13, 20), time(13, 49))
CJ_CGV_MIDDAY_20260831_WINDOW = (time(13, 20), time(13, 29))
CJ_CGV_AFTERNOON_WINDOW = (time(14, 15), time(14, 24))
TYM_MIDDAY_WINDOW = (time(13, 15), time(13, 44))
TYM_MIDDAY_20260831_WINDOW = (time(13, 15), time(13, 34))
TYM_AFTERNOON_WINDOW = (time(14, 30), time(14, 39))
CJ_CGV_LATE_MORNING_WINDOW = (time(10, 0), time(10, 9))
KEPCO_LATE_MORNING_WINDOW = (time(10, 0), time(10, 59))
KEPCO_MIDDAY_WINDOW = (time(13, 30), time(13, 49))
HANSE_LATE_MORNING_WINDOW = (time(10, 0), time(10, 59))
HANSE_LATE_MORNING_REVISED_WINDOW = (time(10, 0), time(10, 19))
HANSE_MIDDAY_WINDOW = (time(13, 20), time(13, 49))
NHN_AFTERNOON_WINDOW = (time(14, 0), time(14, 40))
YOUNGONE_MORNING_WINDOW = (time(9, 20), time(9, 39))
YOUNGONE_AFTERNOON_WINDOW = (time(14, 30), time(14, 40))
YOUNGONE_AFTERNOON_REVISED_WINDOW = (time(14, 30), time(14, 39))
SK_ETERNIX_LATE_MORNING_WINDOW = (time(10, 45), time(10, 54))
MIRAE_ASSET_LATE_MORNING_WINDOW = (time(10, 0), time(10, 59))
MIRAE_ASSET_LATE_MORNING_REVISED_WINDOW = (time(10, 0), time(10, 29))
MIRAE_ASSET_LATE_MORNING_20260828_WINDOW = (time(10, 0), time(10, 19))
KEPCO_MORNING_WINDOW = (time(9, 35), time(9, 59))
NHN_MORNING_WINDOW = (time(9, 40), time(9, 49))
NHN_LATE_MORNING_WINDOW = (time(10, 30), time(10, 49))
SD_BIOSENSOR_MORNING_WINDOW = (time(9, 30), time(9, 49))
SD_BIOSENSOR_MORNING_20260828_WINDOW = (time(9, 30), time(9, 39))
SD_BIOSENSOR_LATE_MORNING_WINDOW = (time(10, 40), time(10, 59))
SD_BIOSENSOR_MIDDAY_WINDOW = (time(13, 25), time(13, 54))
DOOSAN_ENERBILITY_AFTERNOON_WINDOW = (time(14, 10), time(14, 29))
SAMSUNG_EA_MIDDAY_WINDOW = (time(13, 20), time(13, 49))
SAMSUNG_EA_AFTERNOON_20260828_WINDOW = (time(14, 15), time(14, 34))
FAN_OCEAN_MORNING_WINDOW = (time(9, 35), time(9, 59))
FAN_OCEAN_LATE_MORNING_WINDOW = (time(10, 5), time(10, 14))
PROFILE_REVISION_20260819_EFFECTIVE_DATE = date(2026, 8, 19)
PROFILE_REVISION_20260821_EFFECTIVE_DATE = date(2026, 8, 21)
PROFILE_REVISION_20260824_EFFECTIVE_DATE = date(2026, 8, 24)
PROFILE_REVISION_20260825_EFFECTIVE_DATE = date(2026, 8, 25)
PROFILE_REVISION_20260827_EFFECTIVE_DATE = date(2026, 8, 27)
PROFILE_REVISION_20260828_EFFECTIVE_DATE = date(2026, 8, 28)
PROFILE_REVISION_20260831_EFFECTIVE_DATE = date(2026, 8, 31)
# Compatibility alias for consumers that own the first recommendation transition.
PROFILE_REVISION_EFFECTIVE_DATE = PROFILE_REVISION_20260819_EFFECTIVE_DATE
ALLOWED_SYMBOLS = frozenset(
    {
        "006800",
        "002900",
        "010140",
        "015760",
        "017670",
        "028050",
        "028670",
        "034020",
        "035720",
        "042660",
        "079160",
        "080220",
        "105630",
        "111770",
        "137310",
        "181710",
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
        DOOSAN_ENERBILITY_LATE_MORNING_REVISED_WINDOW,
        KAKAO_MIDDAY_WINDOW,
        SAMSUNG_EA_AFTERNOON_WINDOW,
        SK_TELECOM_AFTERNOON_WINDOW,
        SK_TELECOM_MORNING_WINDOW,
        SK_TELECOM_LATE_MORNING_WINDOW,
        SK_TELECOM_LATE_MORNING_REVISED_WINDOW,
        SK_ETERNIX_AFTERNOON_REVISED_WINDOW,
        HANSE_MORNING_WINDOW,
        HANSE_AFTERNOON_WINDOW,
        CJ_CGV_MIDDAY_WINDOW,
        CJ_CGV_MIDDAY_20260831_WINDOW,
        CJ_CGV_AFTERNOON_WINDOW,
        TYM_MIDDAY_WINDOW,
        TYM_MIDDAY_20260831_WINDOW,
        TYM_AFTERNOON_WINDOW,
        CJ_CGV_LATE_MORNING_WINDOW,
        KEPCO_LATE_MORNING_WINDOW,
        KEPCO_MIDDAY_WINDOW,
        HANSE_LATE_MORNING_WINDOW,
        HANSE_LATE_MORNING_REVISED_WINDOW,
        HANSE_MIDDAY_WINDOW,
        NHN_AFTERNOON_WINDOW,
        YOUNGONE_MORNING_WINDOW,
        YOUNGONE_AFTERNOON_WINDOW,
        YOUNGONE_AFTERNOON_REVISED_WINDOW,
        SK_ETERNIX_LATE_MORNING_WINDOW,
        MIRAE_ASSET_LATE_MORNING_WINDOW,
        MIRAE_ASSET_LATE_MORNING_REVISED_WINDOW,
        MIRAE_ASSET_LATE_MORNING_20260828_WINDOW,
        KEPCO_MORNING_WINDOW,
        NHN_MORNING_WINDOW,
        NHN_LATE_MORNING_WINDOW,
        SD_BIOSENSOR_MORNING_WINDOW,
        SD_BIOSENSOR_MORNING_20260828_WINDOW,
        SD_BIOSENSOR_LATE_MORNING_WINDOW,
        SD_BIOSENSOR_MIDDAY_WINDOW,
        DOOSAN_ENERBILITY_AFTERNOON_WINDOW,
        SAMSUNG_EA_MIDDAY_WINDOW,
        SAMSUNG_EA_AFTERNOON_20260828_WINDOW,
        FAN_OCEAN_MORNING_WINDOW,
        FAN_OCEAN_LATE_MORNING_WINDOW,
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
    inventory: dict[str, MachineProfile] | None = None,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] | None = None,
    target_ticks: int,
) -> MachineProfile:
    prior = (inventory or PRE_RECOMMENDATION_PROFILES)[profile_id]
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


PROFILES_20260819 = dict(PRE_RECOMMENDATION_PROFILES)
PROFILES_20260819.update(
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
PROFILES_20260819.update(
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

_REVISION_20260821_SOURCE = (
    "clean_baseline_36d_calibration_16d_holdout_user_approved_v2"
)


def _revise_20260821(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] | None = None,
    target_ticks: int,
) -> MachineProfile:
    revised = _revise_profile(
        profile_id,
        inventory=PROFILES_20260819,
        window=window,
        lookback_bars=lookback_bars,
        drawdown_pct=drawdown_pct,
        near_low_pct=near_low_pct,
        entry_offsets_ticks=entry_offsets_ticks,
        target_ticks=target_ticks,
    )
    return replace(
        revised,
        policy=replace(
            revised.policy,
            runtime_policy_source=_REVISION_20260821_SOURCE,
        ),
    )


PROFILES = dict(PROFILES_20260819)
PROFILES.update(
    {
        "doosan_enerbility_late_morning": _revise_20260821(
            "doosan_enerbility_late_morning",
            window=DOOSAN_ENERBILITY_LATE_MORNING_REVISED_WINDOW,
            lookback_bars=45,
            drawdown_pct=1.50,
            near_low_pct=0.05,
            target_ticks=4,
        ),
        "samsung_heavy_morning": _revise_20260821(
            "samsung_heavy_morning",
            lookback_bars=20,
            drawdown_pct=1.75,
            near_low_pct=0.75,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
        ),
        "kakao_midday": _revise_20260821(
            "kakao_midday",
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "kakao_late_morning": _revise_20260821(
            "kakao_late_morning",
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.05,
            target_ticks=4,
        ),
        "sk_telecom_afternoon": _revise_20260821(
            "sk_telecom_afternoon",
            lookback_bars=20,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "samsung_ea_morning": _revise_20260821(
            "samsung_ea_morning",
            lookback_bars=15,
            drawdown_pct=1.75,
            near_low_pct=0.50,
            target_ticks=4,
        ),
        "sk_eternix_afternoon": _revise_20260821(
            "sk_eternix_afternoon",
            window=SK_ETERNIX_AFTERNOON_REVISED_WINDOW,
            lookback_bars=15,
            drawdown_pct=2.00,
            near_low_pct=0.50,
            target_ticks=4,
        ),
        "samsung_ea_afternoon": _revise_20260821(
            "samsung_ea_afternoon",
            lookback_bars=20,
            drawdown_pct=0.75,
            near_low_pct=0.35,
            target_ticks=4,
        ),
    }
)

# Build only the 2026-08-24 recommendation overlay here because every target
# profile already exists at this stage. The authoritative 27-profile prior is
# captured after the later 2026-08-20 generation is assembled below.
_PROFILES_20260824_BUILD_BASE = dict(PROFILES)
_REVISION_20260824_SOURCE = (
    "clean_baseline_38d_calibration_16d_holdout_user_approved_v4"
)
# Four profiles are introduced by the still-later 2026-08-20 generation. Seed
# only their immutable identity/window fields so the next-date overlay can be
# assembled once and merged onto that authoritative generation at the end.
_PROFILES_20260824_BUILD_BASE.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "cj_cgv_afternoon",
                "079160",
                "CJ CGV",
                "afternoon",
                window=CJ_CGV_AFTERNOON_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.50,
                near_low_pct=0.35,
                target_ticks=2,
            ),
            _profile(
                "tym_midday",
                "002900",
                "TYM",
                "midday",
                window=TYM_MIDDAY_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
            ),
            _profile(
                "hanse_morning",
                "105630",
                "한세실업",
                "morning",
                window=HANSE_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.75,
                near_low_pct=0.75,
                target_ticks=2,
            ),
            _profile(
                "hanse_afternoon",
                "105630",
                "한세실업",
                "afternoon",
                window=HANSE_AFTERNOON_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
            ),
        )
    }
)


def _revise_20260824(
    profile_id: str,
    *,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] = (0, -1),
    entry_valid_completed_bars: int = 5,
    target_ticks: int,
) -> MachineProfile:
    prior = _PROFILES_20260824_BUILD_BASE[profile_id]
    return replace(
        prior,
        policy=replace(
            prior.policy,
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            entry_offsets_ticks=entry_offsets_ticks,
            entry_valid_completed_bars=entry_valid_completed_bars,
            target_ticks=target_ticks,
            runtime_policy_source=_REVISION_20260824_SOURCE,
            runtime_policy_hash="",
        ),
    )


_PROFILES_20260824_OVERLAY_BUILD = dict(_PROFILES_20260824_BUILD_BASE)
_PROFILES_20260824_OVERLAY_BUILD.update(
    {
        "cj_cgv_afternoon": _revise_20260824(
            "cj_cgv_afternoon",
            lookback_bars=30,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "kepco_afternoon": _revise_20260824(
            "kepco_afternoon",
            lookback_bars=45,
            drawdown_pct=0.75,
            near_low_pct=0.75,
            entry_valid_completed_bars=3,
            target_ticks=4,
        ),
        "tym_midday": _revise_20260824(
            "tym_midday",
            lookback_bars=20,
            drawdown_pct=0.50,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "hanse_morning": _revise_20260824(
            "hanse_morning",
            lookback_bars=15,
            drawdown_pct=0.75,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "samsung_ea_late_morning": _revise_20260824(
            "samsung_ea_late_morning",
            lookback_bars=45,
            drawdown_pct=1.00,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "hanse_afternoon": _revise_20260824(
            "hanse_afternoon",
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
        ),
    }
)
_PROFILE_REVISION_20260824_IDS = frozenset(
    {
        "cj_cgv_afternoon",
        "kepco_afternoon",
        "tym_midday",
        "hanse_morning",
        "samsung_ea_late_morning",
        "hanse_afternoon",
        "cj_cgv_late_morning",
        "kepco_late_morning",
        "kepco_midday",
        "hanse_late_morning",
        "hanse_midday",
        "nhn_afternoon",
        "youngone_morning",
        "youngone_afternoon",
    }
)
_PROFILES_20260824_OVERLAY_BUILD.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "cj_cgv_late_morning",
                "079160",
                "CJ CGV",
                "late_morning",
                window=CJ_CGV_LATE_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "kepco_late_morning",
                "015760",
                "한국전력",
                "late_morning",
                window=KEPCO_LATE_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.75,
                near_low_pct=0.05,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "kepco_midday",
                "015760",
                "한국전력",
                "midday",
                window=KEPCO_MIDDAY_WINDOW,
                lookback_bars=45,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "hanse_late_morning",
                "105630",
                "한세실업",
                "late_morning",
                window=HANSE_LATE_MORNING_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.75,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "hanse_midday",
                "105630",
                "한세실업",
                "midday",
                window=HANSE_MIDDAY_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "nhn_afternoon",
                "181710",
                "NHN",
                "afternoon",
                window=NHN_AFTERNOON_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "youngone_morning",
                "111770",
                "영원무역",
                "morning",
                window=YOUNGONE_MORNING_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
            _profile(
                "youngone_afternoon",
                "111770",
                "영원무역",
                "afternoon",
                window=YOUNGONE_AFTERNOON_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260824_SOURCE,
            ),
        )
    }
)
_PROFILE_REVISION_20260824_OVERLAY = {
    profile_id: _PROFILES_20260824_OVERLAY_BUILD[profile_id]
    for profile_id in _PROFILE_REVISION_20260824_IDS
}
PROFILES.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "sk_telecom_late_morning",
                "017670",
                "SK텔레콤",
                "late_morning",
                window=SK_TELECOM_LATE_MORNING_WINDOW,
                lookback_bars=60,
                drawdown_pct=1.25,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_SOURCE,
            ),
            _profile(
                "hanse_afternoon",
                "105630",
                "한세실업",
                "afternoon",
                window=HANSE_AFTERNOON_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_SOURCE,
            ),
            _profile(
                "hanse_morning",
                "105630",
                "한세실업",
                "morning",
                window=HANSE_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.75,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_SOURCE,
            ),
        )
    }
)

# The reviewed 2026-08-19 generation remains the staged base for profiles not
# replaced by the 2026-08-20 recommendation delta. The combined generation
# below owns 2026-08-21 PREOPEN.
PROFILES_20260821_0819 = dict(PROFILES)
_REVISION_20260821_LATEST_SOURCE = (
    "clean_baseline_37d_calibration_16d_holdout_user_approved_v3"
)


def _revise_20260821_latest(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] | None = None,
    target_ticks: int,
) -> MachineProfile:
    prior = PROFILES_20260821_0819[profile_id]
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
            runtime_policy_source=_REVISION_20260821_LATEST_SOURCE,
            runtime_policy_hash="",
        ),
    )


PROFILES = dict(PROFILES_20260821_0819)
PROFILES.update(
    {
        "doosan_enerbility_late_morning": _revise_20260821_latest(
            "doosan_enerbility_late_morning",
            window=DOOSAN_ENERBILITY_LATE_MORNING_REVISED_WINDOW,
            lookback_bars=45,
            drawdown_pct=1.50,
            near_low_pct=0.05,
            target_ticks=4,
        ),
        "samsung_heavy_morning": _revise_20260821_latest(
            "samsung_heavy_morning",
            lookback_bars=20,
            drawdown_pct=1.75,
            near_low_pct=0.75,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
        ),
        "samsung_ea_morning": _revise_20260821_latest(
            "samsung_ea_morning",
            lookback_bars=15,
            drawdown_pct=2.00,
            near_low_pct=0.50,
            target_ticks=4,
        ),
        "kakao_late_morning": _revise_20260821_latest(
            "kakao_late_morning",
            window=KAKAO_LATE_MORNING_WINDOW,
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.05,
            target_ticks=4,
        ),
        "sk_telecom_afternoon": _revise_20260821_latest(
            "sk_telecom_afternoon",
            lookback_bars=15,
            drawdown_pct=0.75,
            near_low_pct=0.50,
            target_ticks=4,
        ),
    }
)
PROFILES.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "cj_cgv_midday",
                "079160",
                "CJ CGV",
                "midday",
                window=CJ_CGV_MIDDAY_WINDOW,
                lookback_bars=60,
                drawdown_pct=0.75,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_LATEST_SOURCE,
            ),
            _profile(
                "cj_cgv_afternoon",
                "079160",
                "CJ CGV",
                "afternoon",
                window=CJ_CGV_AFTERNOON_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.50,
                near_low_pct=0.35,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_LATEST_SOURCE,
            ),
            _profile(
                "tym_midday",
                "002900",
                "TYM",
                "midday",
                window=TYM_MIDDAY_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.50,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_LATEST_SOURCE,
            ),
            _profile(
                "tym_afternoon",
                "002900",
                "TYM",
                "afternoon",
                window=TYM_AFTERNOON_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260821_LATEST_SOURCE,
            ),
        )
    }
)

# The 27-profile generation remains authoritative through 2026-08-21. The
# postclose-approved overlay becomes effective on the next KRX trading date
# without changing prior-date orders or held-position custody.
PROFILES_20260824_PRIOR = dict(PROFILES)
PROFILES.update(_PROFILE_REVISION_20260824_OVERLAY)

# The 2026-08-24 postclose recommendations become a separate 2026-08-25
# generation. Prior target dates retain their exact profile inventory so open
# orders and held-position custody are never reinterpreted by a later policy.
PROFILES_20260825_PRIOR = dict(PROFILES)
_REVISION_20260825_SOURCE = (
    "clean_baseline_39d_calibration_16d_holdout_user_approved_v5"
)


def _revise_20260825(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] = (0, -1),
    entry_valid_completed_bars: int = 5,
    target_ticks: int,
) -> MachineProfile:
    prior = PROFILES_20260825_PRIOR[profile_id]
    selected_window = window or (prior.policy.scan_start, prior.policy.scan_last_bar)
    return replace(
        prior,
        policy=replace(
            prior.policy,
            scan_start=selected_window[0],
            scan_last_bar=selected_window[1],
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            entry_offsets_ticks=entry_offsets_ticks,
            entry_valid_completed_bars=entry_valid_completed_bars,
            target_ticks=target_ticks,
            runtime_policy_source=_REVISION_20260825_SOURCE,
            runtime_policy_hash="",
        ),
    )


PROFILES = dict(PROFILES_20260825_PRIOR)
PROFILES.update(
    {
        "cj_cgv_late_morning": _revise_20260825(
            "cj_cgv_late_morning",
            lookback_bars=45,
            drawdown_pct=1.00,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "kepco_late_morning": _revise_20260825(
            "kepco_late_morning",
            lookback_bars=20,
            drawdown_pct=0.75,
            near_low_pct=0.50,
            target_ticks=4,
        ),
        "nhn_afternoon": _revise_20260825(
            "nhn_afternoon",
            lookback_bars=60,
            drawdown_pct=1.00,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "hanse_afternoon": _revise_20260825(
            "hanse_afternoon",
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "youngone_afternoon": _revise_20260825(
            "youngone_afternoon",
            window=YOUNGONE_AFTERNOON_REVISED_WINDOW,
            lookback_bars=45,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "hanse_late_morning": _revise_20260825(
            "hanse_late_morning",
            lookback_bars=20,
            drawdown_pct=0.75,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "hanse_midday": _revise_20260825(
            "hanse_midday",
            lookback_bars=45,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
    }
)
PROFILES.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "sk_eternix_late_morning",
                "475150",
                "SK이터닉스",
                "late_morning",
                window=SK_ETERNIX_LATE_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=1.50,
                near_low_pct=0.20,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260825_SOURCE,
            ),
            _profile(
                "mirae_asset_late_morning",
                "006800",
                "미래에셋증권",
                "late_morning",
                window=MIRAE_ASSET_LATE_MORNING_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.75,
                near_low_pct=0.75,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260825_SOURCE,
            ),
            _profile(
                "kepco_morning",
                "015760",
                "한국전력",
                "morning",
                window=KEPCO_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260825_SOURCE,
            ),
            _profile(
                "nhn_morning",
                "181710",
                "NHN",
                "morning",
                window=NHN_MORNING_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260825_SOURCE,
            ),
            _profile(
                "nhn_late_morning",
                "181710",
                "NHN",
                "late_morning",
                window=NHN_LATE_MORNING_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260825_SOURCE,
            ),
        )
    }
)


# The 2026-08-26 postclose recommendations become an exact-date generation on
# 2026-08-27. Prior target dates keep the 40-profile inventory so existing
# orders and held-position custody are never reinterpreted by later policy.
PROFILES_20260827_PRIOR = dict(PROFILES)
_REVISION_20260827_SOURCE = (
    "clean_baseline_41d_calibration_16d_holdout_user_approved_v6"
)


def _revise_20260827(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] = (0, -1),
    entry_valid_completed_bars: int = 5,
    target_ticks: int,
) -> MachineProfile:
    prior = PROFILES_20260827_PRIOR[profile_id]
    selected_window = window or (prior.policy.scan_start, prior.policy.scan_last_bar)
    return replace(
        prior,
        policy=replace(
            prior.policy,
            scan_start=selected_window[0],
            scan_last_bar=selected_window[1],
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            entry_offsets_ticks=entry_offsets_ticks,
            entry_valid_completed_bars=entry_valid_completed_bars,
            target_ticks=target_ticks,
            runtime_policy_source=_REVISION_20260827_SOURCE,
            runtime_policy_hash="",
        ),
    )


PROFILES = dict(PROFILES_20260827_PRIOR)
PROFILES.update(
    {
        "sk_eternix_late_morning": _revise_20260827(
            "sk_eternix_late_morning",
            lookback_bars=15,
            drawdown_pct=1.75,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "cj_cgv_late_morning": _revise_20260827(
            "cj_cgv_late_morning",
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "mirae_asset_late_morning": _revise_20260827(
            "mirae_asset_late_morning",
            window=MIRAE_ASSET_LATE_MORNING_REVISED_WINDOW,
            lookback_bars=20,
            drawdown_pct=1.00,
            near_low_pct=0.35,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
        ),
        "kepco_morning": _revise_20260827(
            "kepco_morning",
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "nhn_late_morning": _revise_20260827(
            "nhn_late_morning",
            lookback_bars=30,
            drawdown_pct=0.50,
            near_low_pct=0.50,
            target_ticks=4,
        ),
        "sk_telecom_late_morning": _revise_20260827(
            "sk_telecom_late_morning",
            window=SK_TELECOM_LATE_MORNING_REVISED_WINDOW,
            lookback_bars=30,
            drawdown_pct=0.75,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "hanse_late_morning": _revise_20260827(
            "hanse_late_morning",
            window=HANSE_LATE_MORNING_REVISED_WINDOW,
            lookback_bars=20,
            drawdown_pct=0.75,
            near_low_pct=0.20,
            target_ticks=4,
        ),
    }
)
PROFILES.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "sd_biosensor_morning",
                "137310",
                "에스디바이오센서",
                "morning",
                window=SD_BIOSENSOR_MORNING_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.75,
                near_low_pct=0.75,
                runtime_policy_source=_REVISION_20260827_SOURCE,
            ),
            _profile(
                "sd_biosensor_late_morning",
                "137310",
                "에스디바이오센서",
                "late_morning",
                window=SD_BIOSENSOR_LATE_MORNING_WINDOW,
                lookback_bars=30,
                drawdown_pct=0.50,
                near_low_pct=0.50,
                runtime_policy_source=_REVISION_20260827_SOURCE,
            ),
            _profile(
                "sd_biosensor_midday",
                "137310",
                "에스디바이오센서",
                "midday",
                window=SD_BIOSENSOR_MIDDAY_WINDOW,
                lookback_bars=20,
                drawdown_pct=0.75,
                near_low_pct=0.20,
                runtime_policy_source=_REVISION_20260827_SOURCE,
            ),
            _profile(
                "doosan_enerbility_afternoon",
                "034020",
                "두산에너빌리티",
                "afternoon",
                window=DOOSAN_ENERBILITY_AFTERNOON_WINDOW,
                lookback_bars=15,
                drawdown_pct=0.75,
                near_low_pct=0.05,
                runtime_policy_source=_REVISION_20260827_SOURCE,
            ),
            _profile(
                "samsung_ea_midday",
                "028050",
                "삼성E&A",
                "midday",
                window=SAMSUNG_EA_MIDDAY_WINDOW,
                lookback_bars=30,
                drawdown_pct=1.00,
                near_low_pct=0.75,
                runtime_policy_source=_REVISION_20260827_SOURCE,
            ),
        )
    }
)


# The 2026-08-27 postclose recommendations become a separate exact-date
# generation on 2026-08-28. The prior inventory remains immutable so active
# orders and held custody keep their original profile contract.
PROFILES_20260828_PRIOR = dict(PROFILES)
_REVISION_20260828_SOURCE = (
    "clean_baseline_42d_calibration_16d_holdout_user_approved_v7"
)


def _revise_20260828(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] = (0, -1),
    entry_valid_completed_bars: int = 5,
    target_ticks: int,
) -> MachineProfile:
    prior = PROFILES_20260828_PRIOR[profile_id]
    selected_window = window or (prior.policy.scan_start, prior.policy.scan_last_bar)
    return replace(
        prior,
        policy=replace(
            prior.policy,
            scan_start=selected_window[0],
            scan_last_bar=selected_window[1],
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            entry_offsets_ticks=entry_offsets_ticks,
            entry_valid_completed_bars=entry_valid_completed_bars,
            target_ticks=target_ticks,
            runtime_policy_source=_REVISION_20260828_SOURCE,
            runtime_policy_hash="",
        ),
    )


PROFILES = dict(PROFILES_20260828_PRIOR)
PROFILES.update(
    {
        "kepco_late_morning": _revise_20260828(
            "kepco_late_morning",
            lookback_bars=60,
            drawdown_pct=2.00,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "cj_cgv_midday": _revise_20260828(
            "cj_cgv_midday",
            lookback_bars=20,
            drawdown_pct=0.75,
            near_low_pct=0.20,
            target_ticks=4,
        ),
        "mirae_asset_late_morning": _revise_20260828(
            "mirae_asset_late_morning",
            window=MIRAE_ASSET_LATE_MORNING_20260828_WINDOW,
            lookback_bars=45,
            drawdown_pct=1.00,
            near_low_pct=0.75,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
        ),
        "sd_biosensor_late_morning": _revise_20260828(
            "sd_biosensor_late_morning",
            lookback_bars=30,
            drawdown_pct=0.50,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "sd_biosensor_morning": _revise_20260828(
            "sd_biosensor_morning",
            window=SD_BIOSENSOR_MORNING_20260828_WINDOW,
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "hanse_late_morning": _revise_20260828(
            "hanse_late_morning",
            lookback_bars=30,
            drawdown_pct=0.75,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "samsung_ea_midday": _revise_20260828(
            "samsung_ea_midday",
            lookback_bars=20,
            drawdown_pct=1.00,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "samsung_ea_afternoon": _revise_20260828(
            "samsung_ea_afternoon",
            window=SAMSUNG_EA_AFTERNOON_20260828_WINDOW,
            lookback_bars=60,
            drawdown_pct=0.50,
            near_low_pct=0.20,
            target_ticks=4,
        ),
    }
)
PROFILES["sk_telecom_morning"] = _profile(
    "sk_telecom_morning",
    "017670",
    "SK텔레콤",
    "morning",
    window=SK_TELECOM_MORNING_WINDOW,
    lookback_bars=30,
    drawdown_pct=1.50,
    near_low_pct=0.50,
    target_ticks=2,
    runtime_policy_source=_REVISION_20260828_SOURCE,
)


# The 2026-08-28 postclose recommendations become a separate exact-date
# generation on 2026-08-31. The 2026-08-28 inventory remains immutable so
# existing orders and held custody retain the contract active when submitted.
PROFILES_20260831_PRIOR = dict(PROFILES)
_REVISION_20260831_SOURCE = (
    "clean_baseline_43d_calibration_16d_holdout_user_approved_v8"
)


def _revise_20260831(
    profile_id: str,
    *,
    window: tuple[time, time] | None = None,
    lookback_bars: int,
    drawdown_pct: float,
    near_low_pct: float,
    entry_offsets_ticks: tuple[int, int] = (0, -1),
    entry_valid_completed_bars: int = 5,
    target_ticks: int,
) -> MachineProfile:
    prior = PROFILES_20260831_PRIOR[profile_id]
    selected_window = window or (prior.policy.scan_start, prior.policy.scan_last_bar)
    return replace(
        prior,
        policy=replace(
            prior.policy,
            scan_start=selected_window[0],
            scan_last_bar=selected_window[1],
            lookback_bars=lookback_bars,
            rolling_high_drawdown_pct=drawdown_pct,
            rolling_low_proximity_pct=near_low_pct,
            entry_offsets_ticks=entry_offsets_ticks,
            entry_valid_completed_bars=entry_valid_completed_bars,
            target_ticks=target_ticks,
            runtime_policy_source=_REVISION_20260831_SOURCE,
            runtime_policy_hash="",
        ),
    )


PROFILES = dict(PROFILES_20260831_PRIOR)
PROFILES.update(
    {
        "cj_cgv_midday": _revise_20260831(
            "cj_cgv_midday",
            window=CJ_CGV_MIDDAY_20260831_WINDOW,
            lookback_bars=20,
            drawdown_pct=0.75,
            near_low_pct=0.35,
            target_ticks=4,
        ),
        "mirae_asset_late_morning": _revise_20260831(
            "mirae_asset_late_morning",
            window=MIRAE_ASSET_LATE_MORNING_20260828_WINDOW,
            lookback_bars=45,
            drawdown_pct=1.00,
            near_low_pct=0.50,
            entry_offsets_ticks=(-1, -2),
            target_ticks=4,
        ),
        "nhn_morning": _revise_20260831(
            "nhn_morning",
            lookback_bars=20,
            drawdown_pct=0.50,
            near_low_pct=0.50,
            target_ticks=4,
        ),
        "tym_midday": _revise_20260831(
            "tym_midday",
            window=TYM_MIDDAY_20260831_WINDOW,
            lookback_bars=15,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
        "sk_telecom_morning": _revise_20260831(
            "sk_telecom_morning",
            lookback_bars=30,
            drawdown_pct=0.50,
            near_low_pct=0.75,
            target_ticks=4,
        ),
    }
)
PROFILES.update(
    {
        profile.profile_id: profile
        for profile in (
            _profile(
                "fan_ocean_morning",
                "028670",
                "팬오션",
                "morning",
                window=FAN_OCEAN_MORNING_WINDOW,
                lookback_bars=30,
                drawdown_pct=2.00,
                near_low_pct=0.20,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260831_SOURCE,
            ),
            _profile(
                "fan_ocean_late_morning",
                "028670",
                "팬오션",
                "late_morning",
                window=FAN_OCEAN_LATE_MORNING_WINDOW,
                lookback_bars=45,
                drawdown_pct=1.75,
                near_low_pct=0.50,
                target_ticks=2,
                runtime_policy_source=_REVISION_20260831_SOURCE,
            ),
        )
    }
)


def profiles_for_target_date(target_date: date) -> dict[str, MachineProfile]:
    if target_date < PROFILE_REVISION_20260819_EFFECTIVE_DATE:
        return PRE_RECOMMENDATION_PROFILES
    if target_date < PROFILE_REVISION_20260821_EFFECTIVE_DATE:
        return PROFILES_20260819
    if target_date < PROFILE_REVISION_20260824_EFFECTIVE_DATE:
        return PROFILES_20260824_PRIOR
    if target_date < PROFILE_REVISION_20260825_EFFECTIVE_DATE:
        return PROFILES_20260825_PRIOR
    if target_date < PROFILE_REVISION_20260827_EFFECTIVE_DATE:
        return PROFILES_20260827_PRIOR
    if target_date < PROFILE_REVISION_20260828_EFFECTIVE_DATE:
        return PROFILES_20260828_PRIOR
    if target_date < PROFILE_REVISION_20260831_EFFECTIVE_DATE:
        return PROFILES_20260831_PRIOR
    return PROFILES


def get_profile(profile_id: str, *, target_date: date | None = None) -> MachineProfile:
    inventory = (
        PROFILES if target_date is None else profiles_for_target_date(target_date)
    )
    try:
        return inventory[str(profile_id)]
    except KeyError as exc:
        raise ValueError("unknown_low_price_two_leg_profile") from exc
