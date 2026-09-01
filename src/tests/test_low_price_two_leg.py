from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.engine.risk.market_weakness_entry_guard import (
    MarketWeaknessEntryDecision,
)
from src.engine.monitoring.low_price_two_leg_tuning import (
    CLEAN_WINDOW_NAME,
    DEFAULT_ROUND_TRIP_COST_PCT,
    PROFILE_FIRST_OPERATIONAL_DATES,
    REPORT_SCHEMA,
    _aggregate,
    _apply_broker_realized_economics,
    _historical_profile_row,
    build_candidate,
    build_report,
    extract_profile_row,
    load_realized_pnl_ka10073,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import candidate_grid
from src.trading.low_price_two_leg.gateway import (
    CurrentOpenOrderSnapshot,
    ExecutionSnapshot,
    KiwoomLowPriceTwoLegGateway,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.low_price_two_leg.machine import LowPriceTwoLegMachine
from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
)
from src.trading.low_price_two_leg.policy_runtime import (
    BASELINE_POLICIES,
    CANDIDATE_SCHEMA,
    KAKAO_MORNING_TARGET_TRANSITION,
    POLICY_BOUNDS,
    PRE_RECOMMENDATION_BASELINE_POLICIES,
    PROFILE_20260819_BASELINE_POLICIES,
    PROFILE_20260821_BASELINE_POLICIES,
    apply_operator_policy_transitions,
    atomic_write_json,
    load_applied_profile_policy,
    policy_hash,
    validate_applied,
    validate_candidate,
)
from src.trading.low_price_two_leg.preflight import (
    RECOMMENDATION_20260818_PROFILE_MAP,
    RECOMMENDATION_20260819_PROFILE_MAP,
    RECOMMENDATION_20260820_PROFILE_MAP,
    RECOMMENDATION_20260821_PROFILE_MAP,
    RECOMMENDATION_20260824_PROFILE_MAP,
    RECOMMENDATION_20260826_PROFILE_MAP,
    RECOMMENDATION_20260827_PROFILE_MAP,
    RECOMMENDATION_20260828_PROFILE_MAP,
    build_authority_artifact,
    evaluate_preflight,
    validate_research_evidence,
)
from src.trading.low_price_two_leg.profiles import (
    AFTERNOON_WINDOW,
    CJ_CGV_AFTERNOON_WINDOW,
    CJ_CGV_LATE_MORNING_WINDOW,
    CJ_CGV_MIDDAY_20260831_WINDOW,
    DOOSAN_ENERBILITY_AFTERNOON_WINDOW,
    DOOSAN_ENERBILITY_MORNING_WINDOW,
    DOOSAN_ENERBILITY_LATE_MORNING_REVISED_WINDOW,
    FAN_OCEAN_LATE_MORNING_WINDOW,
    FAN_OCEAN_MORNING_WINDOW,
    HANSE_AFTERNOON_WINDOW,
    HANSE_LATE_MORNING_REVISED_WINDOW,
    HANSE_MIDDAY_WINDOW,
    HANSE_MORNING_WINDOW,
    HANWHA_OCEAN_LATE_MORNING_WINDOW,
    JEJU_SEMICONDUCTOR_MORNING_WINDOW,
    KAKAO_LATE_MORNING_WINDOW,
    KAKAO_MORNING_WINDOW,
    KAKAO_MIDDAY_WINDOW,
    KEPCO_AFTERNOON_WINDOW,
    KEPCO_LATE_MORNING_WINDOW,
    KEPCO_MORNING_WINDOW,
    KEPCO_MIDDAY_WINDOW,
    MIRAE_ASSET_MIDDAY_WINDOW,
    MIRAE_ASSET_MORNING_WINDOW,
    MIRAE_ASSET_LATE_MORNING_20260828_WINDOW,
    NHN_LATE_MORNING_WINDOW,
    NHN_MORNING_WINDOW,
    SAMSUNG_EA_AFTERNOON_20260828_WINDOW,
    SAMSUNG_EA_LATE_MORNING_WINDOW,
    SAMSUNG_EA_MORNING_WINDOW,
    SAMSUNG_EA_MIDDAY_WINDOW,
    SAMSUNG_HEAVY_MORNING_WINDOW,
    PROFILES,
    PROFILES_20260819,
    PROFILES_20260821_0819,
    PROFILES_20260824_PRIOR,
    PROFILES_20260825_PRIOR,
    PROFILES_20260827_PRIOR,
    PROFILES_20260828_PRIOR,
    PROFILES_20260831_PRIOR,
    PRE_RECOMMENDATION_PROFILES,
    SAMSUNG_HEAVY_MIDDAY_WINDOW,
    SK_ETERNIX_MIDDAY_WINDOW,
    SK_ETERNIX_MORNING_WINDOW,
    SK_ETERNIX_LATE_MORNING_WINDOW,
    SK_ETERNIX_AFTERNOON_REVISED_WINDOW,
    SK_TELECOM_AFTERNOON_WINDOW,
    SK_TELECOM_LATE_MORNING_REVISED_WINDOW,
    SK_TELECOM_MORNING_WINDOW,
    SD_BIOSENSOR_LATE_MORNING_WINDOW,
    SD_BIOSENSOR_MIDDAY_WINDOW,
    SD_BIOSENSOR_MORNING_20260828_WINDOW,
    TYM_AFTERNOON_WINDOW,
    TYM_MIDDAY_20260831_WINDOW,
    NHN_AFTERNOON_WINDOW,
    YOUNGONE_AFTERNOON_REVISED_WINDOW,
    YOUNGONE_MORNING_WINDOW,
    MinuteBar,
)
from src.trading.low_price_two_leg.service import _profile_with_applied_policy
from src.trading.order import regular_two_leg_machine as regular_machine_module
from src.trading.order.regular_two_leg_machine import KST
from src.trading.order.tick_utils import move_price_by_ticks


@pytest.fixture(autouse=True)
def _isolate_market_weakness_counterfactual_writer(monkeypatch):
    monkeypatch.setattr(
        regular_machine_module,
        "record_market_weakness_blocked_entry",
        lambda *_args, **_kwargs: {
            "status": "test_isolated",
            "observation_id": "test-market-weakness-block",
            "path": "test-only",
        },
    )


def _at(day: int, hour: int, minute: int = 0, second: int = 10) -> datetime:
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


def _signal_bars(profile_id: str, *, through: int = 0) -> tuple[MinuteBar, ...]:
    profile = PROFILES[profile_id]
    latest = datetime.combine(date(2026, 8, 12), profile.policy.scan_start, tzinfo=KST)
    history_bars = profile.policy.lookback_bars - 1
    start = latest - timedelta(minutes=history_bars)
    bars = [
        MinuteBar(start + timedelta(minutes=index), 23_500, 23_500, 22_650, 23_500)
        for index in range(history_bars)
    ]
    bars.append(MinuteBar(latest, 22_700, 22_700, 22_650, 22_650))
    for offset in range(1, through + 1):
        bars.append(
            MinuteBar(
                latest + timedelta(minutes=offset),
                22_650,
                22_700,
                22_600,
                22_650,
            )
        )
    return tuple(bars)


def _profile_run_at(profile_id: str) -> datetime:
    started = datetime.combine(
        date(2026, 8, 12), PROFILES[profile_id].policy.scan_start, tzinfo=KST
    )
    return started + timedelta(minutes=1, seconds=10)


def _episode_market_weakness_decision(now: datetime, *, mode: str):
    if mode == "active":
        reason = "entry_blocked_market_weakness_active"
        blocked = True
        active_markets = ("KOSPI",)
    elif mode == "invalid_scope":
        reason = "entry_blocked_market_weakness_state_invalid"
        blocked = True
        active_markets = ()
    else:
        reason = "market_weakness_latch_not_active"
        blocked = False
        active_markets = ()
    return MarketWeaknessEntryDecision(
        blocked=blocked,
        reason=reason,
        symbol="010140",
        owner="episode",
        listing_market="KOSPI",
        phase="active" if blocked else "released",
        active_markets=active_markets,
        session_key=now.date().isoformat(),
        observation_id="weakness-episode-cancel-1",
        observation_as_of=now.isoformat(),
        source_status="test",
        state_path="test-state.json",
        symbol_master_path="test-master.json",
    )


class FakeGateway:
    def __init__(self, profile_id: str) -> None:
        self.profile_id = profile_id
        self.bars = _signal_bars(profile_id)
        self.buy_calls: list[int] = []
        self.sell_calls: list[int] = []
        self.cancel_calls: list[str] = []
        self.snapshots: dict[str, ExecutionSnapshot] = {}
        self.sequence = 0
        self.best_bid_qty = 1_000
        self.best_ask_qty = 1_000
        self.liquidity_calls: list[str] = []
        self.execution_velocity_span_ms = 1_000
        self.execution_velocity_latest_age_ms = 0
        self.execution_velocity_recent_volume = 1_000
        self.execution_velocity_calls: list[str] = []

    def completed_sor_minute_bars(self, *, trade_date, now):
        return MinuteBarsSnapshot(True, self.bars)

    def entry_liquidity_snapshot(self, *, route="SOR"):
        self.liquidity_calls.append(route)
        return EntryLiquiditySnapshot(
            True,
            PROFILES[self.profile_id].symbol,
            route,
            f"{PROFILES[self.profile_id].symbol}_AL",
            best_bid=100_000,
            best_ask=100_100,
            best_bid_qty=self.best_bid_qty,
            best_ask_qty=self.best_ask_qty,
            age_ms=0,
            received_ts_ms=1,
        )

    def entry_execution_velocity_snapshot(self, *, route="SOR"):
        self.execution_velocity_calls.append(route)
        return EntryExecutionVelocitySnapshot(
            True,
            PROFILES[self.profile_id].symbol,
            route,
            f"{PROFILES[self.profile_id].symbol}_AL",
            print_count=10,
            recent_print_span_ms=self.execution_velocity_span_ms,
            latest_print_age_ms=self.execution_velocity_latest_age_ms,
            recent_volume=self.execution_velocity_recent_volume,
            observed_at_kst="2026-08-12T14:00:10+09:00",
            print_times=("140010",) * 10,
            venues=("KRX",) * 10,
        )

    def _accepted(self, prefix: str) -> SubmitResult:
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def submit_limit_buy(self, *, price, quantity):
        assert quantity in {1, 10}
        self.buy_calls.append(price)
        return self._accepted("B")

    def submit_limit_sell(self, *, price, quantity):
        assert 1 <= quantity <= 10
        self.sell_calls.append(price)
        return self._accepted("T")

    def cancel_buy(self, *, order_no):
        self.cancel_calls.append(order_no)
        return self._accepted("C")

    def execution_snapshot(self, *, order_no, order_date, expected_order_qty):
        snapshot = self.snapshots.get(
            order_no,
            ExecutionSnapshot(True, True, 0, expected_order_qty, expected_order_qty),
        )
        if snapshot.order_qty == 1 and expected_order_qty == 10:
            return ExecutionSnapshot(
                snapshot.source_ok,
                snapshot.found,
                snapshot.filled_qty * 10,
                snapshot.remaining_qty * 10,
                10,
                snapshot.fill_price,
                snapshot.error,
            )
        return snapshot


class FakeResponse:
    def __init__(self, body, *, status_code=200, headers=None):
        self._body = body
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_profiles_are_exact_seventeen_symbols_and_forty_eight_independent_sessions():
    assert {key: (item.symbol, item.session) for key, item in PROFILES.items()} == {
        "samsung_heavy_midday": ("010140", "midday"),
        "samsung_heavy_afternoon": ("010140", "afternoon"),
        "sk_eternix_midday": ("475150", "midday"),
        "mirae_asset_morning": ("006800", "morning"),
        "jeju_semiconductor_morning": ("080220", "morning"),
        "doosan_enerbility_morning": ("034020", "morning"),
        "hanwha_ocean_late_morning": ("042660", "late_morning"),
        "kakao_morning": ("035720", "morning"),
        "kepco_afternoon": ("015760", "afternoon"),
        "kakao_late_morning": ("035720", "late_morning"),
        "sk_eternix_morning": ("475150", "morning"),
        "mirae_asset_midday": ("006800", "midday"),
        "sk_eternix_afternoon": ("475150", "afternoon"),
        "samsung_heavy_morning": ("010140", "morning"),
        "doosan_enerbility_late_morning": ("034020", "late_morning"),
        "kakao_midday": ("035720", "midday"),
        "sk_telecom_afternoon": ("017670", "afternoon"),
        "samsung_ea_morning": ("028050", "morning"),
        "samsung_ea_late_morning": ("028050", "late_morning"),
        "samsung_ea_afternoon": ("028050", "afternoon"),
        "sk_telecom_late_morning": ("017670", "late_morning"),
        "sk_telecom_morning": ("017670", "morning"),
        "hanse_morning": ("105630", "morning"),
        "hanse_afternoon": ("105630", "afternoon"),
        "cj_cgv_midday": ("079160", "midday"),
        "cj_cgv_afternoon": ("079160", "afternoon"),
        "tym_midday": ("002900", "midday"),
        "tym_afternoon": ("002900", "afternoon"),
        "cj_cgv_late_morning": ("079160", "late_morning"),
        "kepco_late_morning": ("015760", "late_morning"),
        "kepco_midday": ("015760", "midday"),
        "hanse_late_morning": ("105630", "late_morning"),
        "hanse_midday": ("105630", "midday"),
        "nhn_afternoon": ("181710", "afternoon"),
        "youngone_morning": ("111770", "morning"),
        "youngone_afternoon": ("111770", "afternoon"),
        "sk_eternix_late_morning": ("475150", "late_morning"),
        "mirae_asset_late_morning": ("006800", "late_morning"),
        "kepco_morning": ("015760", "morning"),
        "nhn_morning": ("181710", "morning"),
        "nhn_late_morning": ("181710", "late_morning"),
        "sd_biosensor_morning": ("137310", "morning"),
        "sd_biosensor_late_morning": ("137310", "late_morning"),
        "sd_biosensor_midday": ("137310", "midday"),
        "doosan_enerbility_afternoon": ("034020", "afternoon"),
        "samsung_ea_midday": ("028050", "midday"),
        "fan_ocean_morning": ("028670", "morning"),
        "fan_ocean_late_morning": ("028670", "late_morning"),
    }
    assert {
        (item.policy.scan_start, item.policy.scan_last_bar)
        for item in PROFILES.values()
    } == {
        SAMSUNG_HEAVY_MIDDAY_WINDOW,
        AFTERNOON_WINDOW,
        SK_ETERNIX_MIDDAY_WINDOW,
        MIRAE_ASSET_MORNING_WINDOW,
        JEJU_SEMICONDUCTOR_MORNING_WINDOW,
        DOOSAN_ENERBILITY_MORNING_WINDOW,
        HANWHA_OCEAN_LATE_MORNING_WINDOW,
        KAKAO_MORNING_WINDOW,
        KAKAO_LATE_MORNING_WINDOW,
        SK_ETERNIX_MORNING_WINDOW,
        MIRAE_ASSET_MIDDAY_WINDOW,
        KEPCO_AFTERNOON_WINDOW,
        SAMSUNG_HEAVY_MORNING_WINDOW,
        DOOSAN_ENERBILITY_LATE_MORNING_REVISED_WINDOW,
        KAKAO_MIDDAY_WINDOW,
        SK_TELECOM_AFTERNOON_WINDOW,
        SK_TELECOM_LATE_MORNING_REVISED_WINDOW,
        SK_TELECOM_MORNING_WINDOW,
        SK_ETERNIX_AFTERNOON_REVISED_WINDOW,
        HANSE_MORNING_WINDOW,
        HANSE_AFTERNOON_WINDOW,
        SAMSUNG_EA_MORNING_WINDOW,
        SAMSUNG_EA_MIDDAY_WINDOW,
        SAMSUNG_EA_LATE_MORNING_WINDOW,
        SAMSUNG_EA_AFTERNOON_20260828_WINDOW,
        CJ_CGV_MIDDAY_20260831_WINDOW,
        CJ_CGV_AFTERNOON_WINDOW,
        TYM_MIDDAY_20260831_WINDOW,
        TYM_AFTERNOON_WINDOW,
        CJ_CGV_LATE_MORNING_WINDOW,
        KEPCO_LATE_MORNING_WINDOW,
        KEPCO_MIDDAY_WINDOW,
        HANSE_LATE_MORNING_REVISED_WINDOW,
        HANSE_MIDDAY_WINDOW,
        NHN_AFTERNOON_WINDOW,
        YOUNGONE_MORNING_WINDOW,
        YOUNGONE_AFTERNOON_REVISED_WINDOW,
        SK_ETERNIX_LATE_MORNING_WINDOW,
        MIRAE_ASSET_LATE_MORNING_20260828_WINDOW,
        KEPCO_MORNING_WINDOW,
        NHN_MORNING_WINDOW,
        NHN_LATE_MORNING_WINDOW,
        SD_BIOSENSOR_MORNING_20260828_WINDOW,
        SD_BIOSENSOR_LATE_MORNING_WINDOW,
        SD_BIOSENSOR_MIDDAY_WINDOW,
        DOOSAN_ENERBILITY_AFTERNOON_WINDOW,
        SAMSUNG_EA_MIDDAY_WINDOW,
        FAN_OCEAN_MORNING_WINDOW,
        FAN_OCEAN_LATE_MORNING_WINDOW,
    }
    assert PROFILES["samsung_heavy_midday"].policy.lookback_bars == 30
    assert PROFILES["samsung_heavy_midday"].policy.rolling_high_drawdown_pct == 0.75
    assert PROFILES["samsung_heavy_midday"].policy.rolling_low_proximity_pct == 0.35
    assert PROFILES["sk_eternix_midday"].policy.lookback_bars == 60
    assert PROFILES["sk_eternix_midday"].policy.rolling_high_drawdown_pct == 0.75
    assert PROFILES["sk_eternix_midday"].policy.rolling_low_proximity_pct == 0.35
    assert POLICY_BOUNDS["samsung_heavy_midday"] == {
        "drawdown_min": 0.75,
        "drawdown_max": 1.0,
        "near_low_min": 0.25,
        "near_low_max": 0.35,
    }
    assert POLICY_BOUNDS["sk_eternix_midday"] == {
        "drawdown_min": 0.75,
        "drawdown_max": 1.0,
        "near_low_min": 0.25,
        "near_low_max": 0.35,
    }
    assert all(item.policy.quantity == 20 for item in PROFILES.values())
    assert PROFILES["mirae_asset_morning"].policy.entry_offsets_ticks == (0, -1)
    assert PROFILES["jeju_semiconductor_morning"].policy.entry_valid_completed_bars == 3
    assert all(
        PROFILES[profile_id].policy.target_ticks == 4
        for profile_id in {
            "mirae_asset_morning",
            "jeju_semiconductor_morning",
            "doosan_enerbility_morning",
            "hanwha_ocean_late_morning",
        }
    )
    assert {
        profile_id: (
            profile.policy.lookback_bars,
            profile.policy.rolling_high_drawdown_pct,
            profile.policy.rolling_low_proximity_pct,
            profile.policy.entry_offsets_ticks,
            profile.policy.entry_valid_completed_bars,
            profile.policy.target_ticks,
        )
        for profile_id, profile in PROFILES.items()
        if profile_id
        in {
            "kakao_morning",
            "kepco_afternoon",
            "kakao_late_morning",
            "sk_eternix_morning",
            "mirae_asset_midday",
            "sk_eternix_afternoon",
        }
    } == {
        "kakao_morning": (15, 0.75, 0.35, (0, -1), 5, 4),
        "kepco_afternoon": (45, 0.75, 0.75, (0, -1), 3, 4),
        "kakao_late_morning": (15, 0.50, 0.05, (0, -1), 5, 4),
        "sk_eternix_morning": (15, 2.50, 0.75, (0, -1), 5, 4),
        "mirae_asset_midday": (45, 1.00, 0.20, (0, -1), 5, 4),
        "sk_eternix_afternoon": (15, 2.00, 0.50, (0, -1), 5, 4),
    }


def test_all_profiles_are_routed_by_preflight_live_and_systemd_timers():
    project_root = Path(__file__).resolve().parents[2]
    preflight_script = (
        project_root / "deploy" / "run_low_price_two_leg_preflight.sh"
    ).read_text(encoding="utf-8")
    live_script = (project_root / "deploy" / "run_low_price_two_leg_live.sh").read_text(
        encoding="utf-8"
    )
    install_script = (
        project_root / "deploy" / "install_low_price_two_leg_systemd.sh"
    ).read_text(encoding="utf-8")
    uninstall_script = (
        project_root / "deploy" / "uninstall_low_price_two_leg_systemd.sh"
    ).read_text(encoding="utf-8")
    for profile_id in PROFILES:
        unit_name = profile_id.replace("_", "-")
        assert profile_id in preflight_script
        assert profile_id in live_script
        assert f"export {PROFILES[profile_id].enable_env}=true" in live_script
        assert f'CONFIRM="{PROFILES[profile_id].live_confirmation}"' in live_script
        assert f"low-price-two-leg-{unit_name}.timer" in install_script
        assert f"low-price-two-leg-{unit_name}-preflight.timer" in install_script
        assert f"low-price-two-leg-{unit_name}.timer" in uninstall_script
        assert f"low-price-two-leg-{unit_name}-preflight.timer" in uninstall_script
        assert (
            install_script.count(f"korstockscan-low-price-two-leg-{unit_name}.timer")
            == 2
        )
        assert (
            install_script.count(
                f"korstockscan-low-price-two-leg-{unit_name}-preflight.timer"
            )
            == 2
        )
        assert (
            uninstall_script.count(f"korstockscan-low-price-two-leg-{unit_name}.timer")
            == 1
        )
        assert (
            uninstall_script.count(
                f"korstockscan-low-price-two-leg-{unit_name}-preflight.timer"
            )
            == 1
        )
        assert f"low-price-two-leg@{profile_id}.service" in uninstall_script
        assert f"low-price-two-leg-preflight@{profile_id}.service" in uninstall_script
        assert (
            project_root
            / "deploy"
            / "systemd"
            / f"korstockscan-low-price-two-leg-{unit_name}.timer"
        ).is_file()
        assert (
            project_root
            / "deploy"
            / "systemd"
            / f"korstockscan-low-price-two-leg-{unit_name}-preflight.timer"
        ).is_file()
    timer_files = set(
        (project_root / "deploy" / "systemd").glob(
            "korstockscan-low-price-two-leg-*.timer"
        )
    )
    assert len(timer_files) == len(PROFILES) * 2


def test_live_systemd_unit_requires_fresh_preflight_and_does_not_restart_on_guard_block():
    unit = (
        Path(__file__).resolve().parents[2]
        / "deploy/systemd/korstockscan-low-price-two-leg@.service"
    ).read_text(encoding="utf-8")

    assert "Requires=korstockscan-low-price-two-leg-preflight@%i.service" in unit
    assert (
        "After=network-online.target "
        "korstockscan-low-price-two-leg-preflight@%i.service" in unit
    )
    assert "RestartPreventExitStatus=4 5" in unit


@pytest.mark.parametrize(
    ("profile_id", "preflight_time", "service_time"),
    [
        ("kakao_morning", "09:15:00", "09:19:00"),
        ("kakao_late_morning", "10:00:00", "10:04:00"),
        ("sk_eternix_morning", "09:45:00", "09:49:00"),
        ("mirae_asset_midday", "13:10:00", "13:14:00"),
        ("kepco_afternoon", "13:55:00", "13:59:00"),
        ("sk_eternix_afternoon", "13:55:00", "13:59:00"),
        ("sk_telecom_late_morning", "10:40:00", "10:44:00"),
        ("sk_telecom_morning", "09:05:00", "09:09:00"),
        ("hanse_morning", "09:10:00", "09:14:00"),
        ("hanse_afternoon", "14:15:00", "14:19:00"),
        ("cj_cgv_midday", "13:15:00", "13:19:00"),
        ("cj_cgv_afternoon", "14:10:00", "14:14:00"),
        ("tym_midday", "13:10:00", "13:14:00"),
        ("tym_afternoon", "14:25:00", "14:29:00"),
        ("youngone_morning", "09:15:00", "09:19:00"),
        ("cj_cgv_late_morning", "09:55:00", "09:59:00"),
        ("kepco_late_morning", "09:55:00", "09:59:00"),
        ("hanse_late_morning", "09:55:00", "09:59:00"),
        ("hanse_midday", "13:15:00", "13:19:00"),
        ("kepco_midday", "13:25:00", "13:29:00"),
        ("nhn_afternoon", "13:55:00", "13:59:00"),
        ("youngone_afternoon", "14:25:00", "14:29:00"),
        ("sk_eternix_late_morning", "10:40:00", "10:44:00"),
        ("mirae_asset_late_morning", "09:55:00", "09:59:00"),
        ("kepco_morning", "09:30:00", "09:34:00"),
        ("nhn_morning", "09:35:00", "09:39:00"),
        ("nhn_late_morning", "10:25:00", "10:29:00"),
        ("sd_biosensor_morning", "09:25:00", "09:29:00"),
        ("sd_biosensor_late_morning", "10:35:00", "10:39:00"),
        ("sd_biosensor_midday", "13:20:00", "13:24:00"),
        ("doosan_enerbility_afternoon", "14:05:00", "14:09:00"),
        ("samsung_ea_midday", "13:15:00", "13:19:00"),
        ("fan_ocean_morning", "09:30:00", "09:34:00"),
        ("fan_ocean_late_morning", "10:00:00", "10:04:00"),
    ],
)
def test_expanded_profile_timers_bind_exact_instance_and_start_time(
    profile_id, preflight_time, service_time
):
    timer_dir = Path(__file__).resolve().parents[2] / "deploy" / "systemd"
    unit_name = profile_id.replace("_", "-")
    preflight = (
        timer_dir / f"korstockscan-low-price-two-leg-{unit_name}-preflight.timer"
    ).read_text(encoding="utf-8")
    service = (
        timer_dir / f"korstockscan-low-price-two-leg-{unit_name}.timer"
    ).read_text(encoding="utf-8")

    assert f"OnCalendar=Mon..Fri *-*-* {preflight_time} Asia/Seoul" in preflight
    assert (
        f"Unit=korstockscan-low-price-two-leg-preflight@{profile_id}.service"
        in preflight
    )
    assert f"OnCalendar=Mon..Fri *-*-* {service_time} Asia/Seoul" in service
    assert f"Unit=korstockscan-low-price-two-leg@{profile_id}.service" in service


def test_current_and_install_time_profile_symbols_have_explicit_manual_ownership():
    install_script = (
        Path(__file__).resolve().parents[2]
        / "deploy"
        / "install_low_price_two_leg_systemd.sh"
    ).read_text(encoding="utf-8")
    install_time_symbols = {
        "002900",
        "015760",
        "017670",
        "028050",
        "028670",
        "035720",
        "079160",
        "105630",
        "111770",
        "181710",
    }
    for symbol in install_time_symbols:
        assert f'"{symbol}":' in install_script
    for symbol in {profile.symbol for profile in PROFILES.values()}:
        assert manual_control_operator_exclusion_source(symbol) == "manual_operator"


@pytest.mark.parametrize("profile_id", sorted(PROFILES))
def test_each_profile_uses_same_two_leg_signal_contract(profile_id):
    policy = PROFILES[profile_id].policy
    signal = policy.evaluate(list(_signal_bars(profile_id)))
    assert signal is not None
    assert signal.drawdown_pct > policy.rolling_high_drawdown_pct
    assert signal.near_low_pct == 0.0
    assert [leg["entry_price"] for leg in policy.entry_legs(22_650)] == [
        move_price_by_ticks(22_650, offset) for offset in policy.entry_offsets_ticks
    ]
    assert policy.target_price(22_650) == move_price_by_ticks(
        22_650, policy.target_ticks
    )


def test_all_fourteen_user_approved_recommendations_bind_exact_live_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-18.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260818_PROFILE_MAP) == 14
    assert set(RECOMMENDATION_20260818_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260818_PROFILE_MAP.items():
        profile = PROFILES_20260819[live_profile_id]
        policy = profile.policy
        spot = recommendations[report_profile_id]["recommended_spot"]
        assert {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        } == spot
        assert validate_research_evidence(profile, target_date=date(2026, 8, 19)) == (
            True,
            "ready",
        )


def test_all_eleven_20260819_recommendations_bind_preserved_staged_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-19.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260819_PROFILE_MAP) == 11
    assert set(RECOMMENDATION_20260819_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260819_PROFILE_MAP.items():
        profile = PROFILES_20260821_0819[live_profile_id]
        policy = profile.policy
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        if live_profile_id not in RECOMMENDATION_20260820_PROFILE_MAP:
            assert validate_research_evidence(
                profile, target_date=date(2026, 8, 21)
            ) == (True, "ready")


def test_all_nine_20260820_recommendations_bind_exact_latest_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-20.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260820_PROFILE_MAP) == 9
    assert set(RECOMMENDATION_20260820_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260820_PROFILE_MAP.items():
        profile = PROFILES_20260824_PRIOR[live_profile_id]
        policy = profile.policy
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        assert validate_research_evidence(profile, target_date=date(2026, 8, 21)) == (
            True,
            "ready",
        )


def test_all_fourteen_20260821_recommendations_bind_exact_next_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-21.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260821_PROFILE_MAP) == 14
    assert set(RECOMMENDATION_20260821_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260821_PROFILE_MAP.items():
        profile = PROFILES_20260825_PRIOR[live_profile_id]
        policy = profile.policy
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        assert validate_research_evidence(profile, target_date=date(2026, 8, 24)) == (
            True,
            "ready",
        )


def test_all_twelve_20260824_recommendations_bind_exact_next_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-24.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260824_PROFILE_MAP) == 12
    assert set(RECOMMENDATION_20260824_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260824_PROFILE_MAP.items():
        profile = PROFILES_20260827_PRIOR[live_profile_id]
        policy = profile.policy
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        assert validate_research_evidence(profile, target_date=date(2026, 8, 25)) == (
            True,
            "ready",
        )


def test_all_twelve_20260826_recommendations_bind_exact_next_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-26.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260826_PROFILE_MAP) == 12
    assert set(RECOMMENDATION_20260826_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260826_PROFILE_MAP.items():
        profile = PROFILES_20260828_PRIOR[live_profile_id]
        policy = profile.policy
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        assert validate_research_evidence(profile, target_date=date(2026, 8, 27)) == (
            True,
            "ready",
        )


def test_all_nine_20260827_recommendations_bind_exact_next_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-27.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260827_PROFILE_MAP) == 9
    assert set(RECOMMENDATION_20260827_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260827_PROFILE_MAP.items():
        profile = PROFILES_20260831_PRIOR[live_profile_id]
        policy = profile.policy
        assert policy.quantity == 20
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        assert validate_research_evidence(profile, target_date=date(2026, 8, 28)) == (
            True,
            "ready",
        )


def test_profile_revision_is_exact_date_preopen_transition(tmp_path):
    prior, _ = build_applied_policy(
        target_date=date(2026, 8, 18), candidate_dir=tmp_path / "none"
    )
    revised, _ = build_applied_policy(
        target_date=date(2026, 8, 19), candidate_dir=tmp_path / "none"
    )

    assert set(prior["profiles"]) == set(PRE_RECOMMENDATION_PROFILES)
    assert "profile_revision_transition" not in prior
    assert set(revised["profiles"]) == set(PROFILES_20260819)
    assert revised["profile_revision_transition"]["recommendation_count"] == 14
    assert revised["profile_revision_transition"]["evidence_canonical_sha256"] == (
        "3f829f002f5ce53615460c55f9fa71211d286c87443794e1bd506f622544d795"
    )
    assert validate_applied(prior, target_date=date(2026, 8, 18)) == (
        True,
        "valid",
    )
    assert validate_applied(revised, target_date=date(2026, 8, 19)) == (
        True,
        "valid",
    )

    today, _ = build_applied_policy(
        target_date=date(2026, 8, 20), candidate_dir=tmp_path / "none"
    )
    next_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 21), candidate_dir=tmp_path / "none"
    )
    assert set(today["profiles"]) == set(PROFILES_20260819)
    assert set(next_generation["profiles"]) == set(PROFILES_20260824_PRIOR)
    assert next_generation["profile_revision_transition"] == {
        "effective_target_date": "2026-08-21",
        "source_date": "2026-08-20",
        "before_profile_count": 20,
        "staged_prior_profile_count": 23,
        "after_profile_count": 27,
        "recommendation_count": 9,
        "new_profile_count": 4,
        "logic_revision_count": 5,
        "approved_profile_ids": [
            "cj_cgv_afternoon",
            "cj_cgv_midday",
            "doosan_enerbility_late_morning",
            "hanse_afternoon",
            "hanse_morning",
            "kakao_late_morning",
            "kakao_midday",
            "samsung_ea_afternoon",
            "samsung_ea_morning",
            "samsung_heavy_morning",
            "sk_eternix_afternoon",
            "sk_telecom_afternoon",
            "sk_telecom_late_morning",
            "tym_afternoon",
            "tym_midday",
        ],
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-20.json"
        ),
        "evidence_canonical_sha256": (
            "36010903a2536f0bd860165e3257eacf967548b68f407522b5fefa54670e86c1"
        ),
        "prior_generation": {
            "source_date": "2026-08-19",
            "recommendation_count": 11,
            "new_profile_count": 3,
            "logic_revision_count": 8,
            "evidence_path": (
                "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-19.json"
            ),
            "evidence_canonical_sha256": (
                "3acf5125074eaf7e48eca0e73c22f037b5e6b1ec354bd5b203cf32f14dea2381"
            ),
            "disposition": "carry_forward_unless_replaced_by_latest_generation",
        },
        "decision_authority": "explicit_user_directed_profile_revision_2026_08_20",
        "existing_order_effect": "none_preserve_prior_policy_custody",
    }
    assert validate_applied(next_generation, target_date=date(2026, 8, 21)) == (
        True,
        "valid",
    )
    monday_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 24), candidate_dir=tmp_path / "none"
    )
    assert set(monday_generation["profiles"]) == set(PROFILES_20260825_PRIOR)
    assert monday_generation["profile_revision_transition"] == {
        "effective_target_date": "2026-08-24",
        "source_date": "2026-08-21",
        "before_profile_count": 27,
        "after_profile_count": 35,
        "recommendation_count": 14,
        "new_profile_count": 8,
        "logic_revision_count": 6,
        "approved_profile_ids": sorted(RECOMMENDATION_20260821_PROFILE_MAP),
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-21.json"
        ),
        "evidence_canonical_sha256": (
            "6e25675e9647289bb3313f35dcd8bda9004a17fc7a7c43958f091d3cf18aa0d8"
        ),
        "decision_authority": "explicit_user_directed_profile_revision_2026_08_21",
        "existing_order_effect": "none_preserve_prior_policy_custody",
    }
    assert validate_applied(monday_generation, target_date=date(2026, 8, 24)) == (
        True,
        "valid",
    )
    tuesday_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 25), candidate_dir=tmp_path / "none"
    )
    assert set(tuesday_generation["profiles"]) == set(PROFILES_20260827_PRIOR)
    assert tuesday_generation["profile_revision_transition"] == {
        "effective_target_date": "2026-08-25",
        "source_date": "2026-08-24",
        "before_profile_count": 35,
        "after_profile_count": 40,
        "recommendation_count": 12,
        "new_profile_count": 5,
        "logic_revision_count": 7,
        "approved_profile_ids": sorted(RECOMMENDATION_20260824_PROFILE_MAP),
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-24.json"
        ),
        "evidence_canonical_sha256": (
            "ce447fe0c6d55a5004f821fb450cbe5d6377fc9664f2bee9a5cd6a31ee12d82f"
        ),
        "decision_authority": "explicit_user_directed_profile_revision_2026_08_24",
        "existing_order_effect": "none_preserve_prior_policy_custody",
    }
    assert validate_applied(tuesday_generation, target_date=date(2026, 8, 25)) == (
        True,
        "valid",
    )
    wednesday_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 26), candidate_dir=tmp_path / "none"
    )
    thursday_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 27), candidate_dir=tmp_path / "none"
    )
    friday_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 28), candidate_dir=tmp_path / "none"
    )
    assert set(wednesday_generation["profiles"]) == set(PROFILES_20260827_PRIOR)
    assert set(thursday_generation["profiles"]) == set(PROFILES_20260828_PRIOR)
    assert thursday_generation["profile_revision_transition"] == {
        "effective_target_date": "2026-08-27",
        "source_date": "2026-08-26",
        "before_profile_count": 40,
        "after_profile_count": 45,
        "recommendation_count": 12,
        "new_profile_count": 5,
        "logic_revision_count": 7,
        "approved_profile_ids": sorted(RECOMMENDATION_20260826_PROFILE_MAP),
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-26.json"
        ),
        "evidence_canonical_sha256": (
            "0a7b39dcdf625ed2148bdf7716521e219f70a64f18a9c61892cc67dd42ba6455"
        ),
        "decision_authority": "explicit_user_directed_profile_revision_2026_08_26",
        "existing_order_effect": "none_preserve_prior_policy_custody",
    }
    assert validate_applied(thursday_generation, target_date=date(2026, 8, 27)) == (
        True,
        "valid",
    )
    assert set(friday_generation["profiles"]) == set(PROFILES_20260831_PRIOR)
    assert friday_generation["profile_revision_transition"] == {
        "effective_target_date": "2026-08-28",
        "source_date": "2026-08-27",
        "before_profile_count": 45,
        "after_profile_count": 46,
        "recommendation_count": 9,
        "new_profile_count": 1,
        "logic_revision_count": 8,
        "approved_profile_ids": sorted(RECOMMENDATION_20260827_PROFILE_MAP),
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-27.json"
        ),
        "evidence_canonical_sha256": (
            "12f750f9d719c8d4042574586ac85823f42a4afb429c239c710302d90847be56"
        ),
        "decision_authority": "explicit_user_directed_profile_revision_2026_08_27",
        "existing_order_effect": "none_preserve_prior_policy_custody",
    }
    assert validate_applied(friday_generation, target_date=date(2026, 8, 28)) == (
        True,
        "valid",
    )
    monday_0831_generation, _ = build_applied_policy(
        target_date=date(2026, 8, 31), candidate_dir=tmp_path / "none"
    )
    assert set(monday_0831_generation["profiles"]) == set(PROFILES)
    assert monday_0831_generation["profile_revision_transition"] == {
        "effective_target_date": "2026-08-31",
        "source_date": "2026-08-28",
        "before_profile_count": 46,
        "after_profile_count": 48,
        "recommendation_count": 7,
        "new_profile_count": 2,
        "logic_revision_count": 5,
        "approved_profile_ids": sorted(RECOMMENDATION_20260828_PROFILE_MAP),
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-28.json"
        ),
        "evidence_canonical_sha256": (
            "d5f6e6cb6f80e2fa70c1807f39dc18955060f74d14cdf2111821f1a6b9d1e944"
        ),
        "decision_authority": "explicit_user_directed_profile_revision_2026_08_28",
        "existing_order_effect": "none_preserve_prior_policy_custody",
    }
    assert validate_applied(monday_0831_generation, target_date=date(2026, 8, 31)) == (
        True,
        "valid",
    )


def test_all_seven_20260828_recommendations_bind_exact_next_profiles():
    evidence_path = (
        Path(__file__).resolve().parents[2]
        / "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-28.json"
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    recommendations = {row["profile_id"]: row for row in evidence["recommendations"]}

    assert len(RECOMMENDATION_20260828_PROFILE_MAP) == 7
    assert set(RECOMMENDATION_20260828_PROFILE_MAP.values()) == set(recommendations)
    for (
        live_profile_id,
        report_profile_id,
    ) in RECOMMENDATION_20260828_PROFILE_MAP.items():
        profile = PROFILES[live_profile_id]
        policy = profile.policy
        assert policy.quantity == 20
        assert recommendations[report_profile_id]["recommended_spot"] == {
            "scan_start": policy.scan_start.strftime("%H:%M"),
            "scan_end": policy.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": policy.lookback_bars,
            "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        assert validate_research_evidence(profile, target_date=date(2026, 8, 31)) == (
            True,
            "ready",
        )


def test_20260820_postclose_tuning_keeps_twenty_profile_generation(tmp_path):
    source_quality_dir = tmp_path / "source_quality"
    _write_source_quality_audit(source_quality_dir, "2026-08-20")
    report = build_report(
        target_date="2026-08-20",
        state_dir=tmp_path / "states",
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
        applied_dir=tmp_path / "applied",
        machine_microstructure_report_dir=tmp_path / "micro",
    )
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "candidates",
        samsung_candidate_dir=tmp_path / "samsung",
    )

    assert set(report["daily"]["profiles"]) == set(PROFILES_20260819)
    assert set(candidate["profiles"]) == set(PROFILES_20260819)
    assert validate_candidate(candidate) == (True, "valid")


def test_20260821_profile_revision_validates_but_does_not_apply_source_generation_mutation(
    tmp_path,
):
    source_policies = {
        profile_id: dict(policy)
        for profile_id, policy in PROFILE_20260819_BASELINE_POLICIES.items()
    }
    profile_id = "samsung_heavy_midday"
    source_policies[profile_id]["rolling_high_drawdown_pct"] = 1.0
    source_candidate = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": "2026-08-20",
        "source_report": "low_price_two_leg_tuning",
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": "2026-06-05",
        "policy_hash": policy_hash(source_policies),
        "policy_mutations": [
            {
                "profile_id": profile_id,
                "axis": "rolling_high_drawdown_pct",
                "before": 0.75,
                "after": 1.0,
            }
        ],
        "same_stage_owner_guard": {"mutation_present": False},
        "profiles": {
            current_profile_id: {
                "selection_status": (
                    "selected_bounded_tightening"
                    if current_profile_id == profile_id
                    else "carry_forward_profile_policy"
                ),
                "selected_axis": (
                    "rolling_high_drawdown_pct"
                    if current_profile_id == profile_id
                    else None
                ),
                "policy": policy,
                "allowed_runtime_apply": True,
            }
            for current_profile_id, policy in source_policies.items()
        },
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
    }
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / "low_price_two_leg_policy_candidate_2026-08-20.json").write_text(
        json.dumps(source_candidate), encoding="utf-8"
    )

    revised, status = build_applied_policy(
        target_date=date(2026, 8, 21), candidate_dir=candidate_dir
    )

    assert status == "candidate_validated_profile_revision_applied"
    assert revised["policy_mutations"] == []
    assert revised["profiles"][profile_id]["policy"] == (
        PROFILE_20260821_BASELINE_POLICIES[profile_id]
    )
    assert revised["profiles"][profile_id]["selection_status"] == (
        "profile_revision_same_stage_mutation_not_applied"
    )
    assert validate_applied(revised, target_date=date(2026, 8, 21)) == (
        True,
        "valid",
    )


def test_20260821_postclose_tuning_uses_combined_twenty_seven_profile_generation(
    tmp_path,
):
    source_quality_dir = tmp_path / "source_quality"
    _write_source_quality_audit(source_quality_dir, "2026-08-21")
    report = build_report(
        target_date="2026-08-21",
        state_dir=tmp_path / "states",
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
        applied_dir=tmp_path / "applied",
        machine_microstructure_report_dir=tmp_path / "micro",
    )
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "candidates",
        samsung_candidate_dir=tmp_path / "samsung",
    )

    assert set(report["daily"]["profiles"]) == set(PROFILES_20260824_PRIOR)
    assert set(candidate["profiles"]) == set(PROFILES_20260824_PRIOR)
    assert validate_candidate(candidate) == (True, "valid")


def test_20260824_postclose_tuning_uses_thirty_five_profile_generation(tmp_path):
    source_quality_dir = tmp_path / "source_quality"
    _write_source_quality_audit(source_quality_dir, "2026-08-24")
    report = build_report(
        target_date="2026-08-24",
        state_dir=tmp_path / "states",
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
        applied_dir=tmp_path / "applied",
        machine_microstructure_report_dir=tmp_path / "micro",
    )
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "candidates",
        samsung_candidate_dir=tmp_path / "samsung",
    )

    assert set(report["daily"]["profiles"]) == set(PROFILES_20260825_PRIOR)
    assert set(candidate["profiles"]) == set(PROFILES_20260825_PRIOR)
    assert validate_candidate(candidate) == (True, "valid")


def test_profile_revision_attribution_separates_candidate_and_user_approved_rows(
    tmp_path,
):
    source_policies = {
        profile_id: dict(policy)
        for profile_id, policy in PRE_RECOMMENDATION_BASELINE_POLICIES.items()
    }
    source_candidate = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": "2026-08-18",
        "source_report": "low_price_two_leg_tuning",
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": "2026-06-05",
        "policy_hash": policy_hash(source_policies),
        "policy_mutations": [],
        "same_stage_owner_guard": {"mutation_present": False},
        "profiles": {
            profile_id: {
                "selection_status": "carry_forward_profile_policy",
                "selected_axis": None,
                "policy": policy,
                "allowed_runtime_apply": True,
            }
            for profile_id, policy in source_policies.items()
        },
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
    }
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / "low_price_two_leg_policy_candidate_2026-08-18.json").write_text(
        json.dumps(source_candidate), encoding="utf-8"
    )

    revised, status = build_applied_policy(
        target_date=date(2026, 8, 19), candidate_dir=candidate_dir
    )

    assert status == "candidate_validated_profile_revision_applied"
    revised_profile_ids = set(RECOMMENDATION_20260818_PROFILE_MAP)
    assert {
        profile_id
        for profile_id, item in revised["profiles"].items()
        if item["selection_status"] == "user_approved_profile_revision_baseline"
    } == revised_profile_ids
    assert all(
        revised["profiles"][profile_id]["selection_status"]
        == "carry_forward_profile_policy"
        for profile_id in set(PROFILES_20260819) - revised_profile_ids
    )


def test_20260821_revision_attribution_marks_combined_approved_rows(tmp_path):
    source_policies = {
        profile_id: dict(policy)
        for profile_id, policy in PROFILE_20260819_BASELINE_POLICIES.items()
    }
    source_candidate = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": "2026-08-19",
        "source_report": "low_price_two_leg_tuning",
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": "2026-06-05",
        "policy_hash": policy_hash(source_policies),
        "policy_mutations": [],
        "same_stage_owner_guard": {"mutation_present": False},
        "profiles": {
            profile_id: {
                "selection_status": "carry_forward_profile_policy",
                "selected_axis": None,
                "policy": policy,
                "allowed_runtime_apply": True,
            }
            for profile_id, policy in source_policies.items()
        },
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
    }
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / "low_price_two_leg_policy_candidate_2026-08-19.json").write_text(
        json.dumps(source_candidate), encoding="utf-8"
    )

    revised, status = build_applied_policy(
        target_date=date(2026, 8, 21), candidate_dir=candidate_dir
    )

    assert status == "candidate_validated_profile_revision_applied"
    combined_approved_profile_ids = set(RECOMMENDATION_20260819_PROFILE_MAP) | set(
        RECOMMENDATION_20260820_PROFILE_MAP
    )
    assert (
        set(revised["profile_revision_transition"]["approved_profile_ids"])
        == combined_approved_profile_ids
    )
    assert {
        profile_id
        for profile_id, item in revised["profiles"].items()
        if item["selection_status"] == "user_approved_profile_revision_baseline"
    } == combined_approved_profile_ids
    assert validate_applied(revised, target_date=date(2026, 8, 21)) == (
        True,
        "valid",
    )


def test_20260824_revision_attribution_marks_only_latest_approved_rows(tmp_path):
    source_policies = {
        profile_id: dict(policy)
        for profile_id, policy in PROFILE_20260821_BASELINE_POLICIES.items()
    }
    source_candidate = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": "2026-08-21",
        "source_report": "low_price_two_leg_tuning",
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": "2026-06-05",
        "policy_hash": policy_hash(source_policies),
        "policy_mutations": [],
        "same_stage_owner_guard": {"mutation_present": False},
        "profiles": {
            profile_id: {
                "selection_status": "carry_forward_profile_policy",
                "selected_axis": None,
                "policy": policy,
                "allowed_runtime_apply": True,
            }
            for profile_id, policy in source_policies.items()
        },
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
    }
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / "low_price_two_leg_policy_candidate_2026-08-21.json").write_text(
        json.dumps(source_candidate), encoding="utf-8"
    )

    revised, status = build_applied_policy(
        target_date=date(2026, 8, 24), candidate_dir=candidate_dir
    )

    assert status == "candidate_validated_profile_revision_applied"
    approved_profile_ids = set(RECOMMENDATION_20260821_PROFILE_MAP)
    assert {
        profile_id
        for profile_id, item in revised["profiles"].items()
        if item["selection_status"] == "user_approved_profile_revision_baseline"
    } == approved_profile_ids
    assert all(
        revised["profiles"][profile_id]["selection_status"]
        == "carry_forward_profile_policy"
        for profile_id in set(PROFILES_20260825_PRIOR) - approved_profile_ids
    )
    assert validate_applied(revised, target_date=date(2026, 8, 24)) == (
        True,
        "valid",
    )


def test_machine_state_and_order_ledger_are_bound_to_one_profile(tmp_path):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    state = machine.run_once(_profile_run_at(profile.profile_id))
    assert state["status"] == "BUY_OPEN"
    assert gateway.buy_calls == [22_650, 22_600]
    assert state["signal_features"]["symbol"] == "010140"
    assert state["signal_features"]["strategy"] == profile.profile_id
    assert state["signal_features"]["source"] == (
        "kiwoom_ka10080_010140_AL_completed_1m"
    )


def test_market_weakness_cancels_exact_reconciled_episode_buy_orders(
    tmp_path, monkeypatch
):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "weakness-cancel-state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    mode = {"value": "released"}
    monkeypatch.setattr(
        regular_machine_module,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _episode_market_weakness_decision(
            started_at, mode=mode["value"]
        ),
    )
    submitted = machine.run_once(started_at)
    order_nos = [leg["buy_order_no"] for leg in submitted["legs"]]
    mode["value"] = "active"

    canceled = machine.run_once(started_at + timedelta(seconds=1))

    assert gateway.cancel_calls == order_nos
    assert {leg["status"] for leg in canceled["legs"]} == {"BUY_CANCEL_PENDING"}
    assert all(
        leg["buy_cancel_reason"] == "market_weakness_active_exact_market"
        for leg in canceled["legs"]
    )
    assert all(leg["buy_cancel_attempt_count"] == 1 for leg in canceled["legs"])
    assert (
        canceled["signal_features"]["market_weakness_entry_guard"][
            "market_weakness_open_buy_cancel_allowed"
        ]
        is True
    )


def test_invalid_market_scope_never_authorizes_episode_buy_cancel(
    tmp_path, monkeypatch
):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "weakness-invalid-state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    mode = {"value": "released"}
    monkeypatch.setattr(
        regular_machine_module,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _episode_market_weakness_decision(
            started_at, mode=mode["value"]
        ),
    )
    machine.run_once(started_at)
    mode["value"] = "invalid_scope"

    state = machine.run_once(started_at + timedelta(seconds=1))

    assert gateway.cancel_calls == []
    assert {leg["status"] for leg in state["legs"]} == {"BUY_OPEN"}


def test_episode_cancel_ambiguity_reconciles_before_bounded_retry(
    tmp_path, monkeypatch
):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "weakness-ambiguous-state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    mode = {"value": "released"}
    monkeypatch.setattr(
        regular_machine_module,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _episode_market_weakness_decision(
            started_at, mode=mode["value"]
        ),
    )
    machine.run_once(started_at)
    mode["value"] = "active"
    first_b1 = {"pending": True}

    def flaky_cancel(*, order_no):
        gateway.cancel_calls.append(order_no)
        if order_no == "B1" and first_b1["pending"]:
            first_b1["pending"] = False
            return SubmitResult(False, "", "1700", "timeout", ambiguous=True)
        return gateway._accepted("C")

    monkeypatch.setattr(gateway, "cancel_buy", flaky_cancel)

    ambiguous = machine.run_once(started_at + timedelta(seconds=1))
    throttled = machine.run_once(started_at + timedelta(seconds=2))
    retried = machine.run_once(started_at + timedelta(seconds=6))

    assert ambiguous["legs"][0]["buy_cancel_ambiguous"] is True
    assert throttled["legs"][0]["buy_cancel_attempt_count"] == 1
    assert retried["legs"][0]["buy_cancel_ambiguous"] is False
    assert retried["legs"][0]["buy_cancel_attempt_count"] == 2
    assert gateway.cancel_calls == ["B1", "B2", "B1"]


def test_machine_blocks_entire_episode_when_either_touch_has_under_100_shares(
    tmp_path,
):
    profile = PROFILES["nhn_afternoon"]
    gateway = FakeGateway(profile.profile_id)
    gateway.best_bid_qty = 97
    gateway.best_ask_qty = 93
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "nhn-state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_profile_run_at(profile.profile_id))

    assert state["status"] == "NO_TRADE"
    assert state["attempt_consumed"] is True
    assert state["position_qty"] == 0
    assert {leg["status"] for leg in state["legs"]} == {"NO_FILL"}
    assert state["blocked_reason"] == "entry_liquidity_touch_depth_insufficient"
    assert state["last_action"] == "entry_liquidity_blocked_before_buy"
    assert gateway.buy_calls == []
    guard = state["signal_features"]["entry_liquidity"]
    assert guard["entry_liquidity_required_each_side_quantity"] == 100
    assert guard["entry_liquidity_snapshot"]["best_bid_qty"] == 97
    assert guard["entry_liquidity_snapshot"]["best_ask_qty"] == 93


def test_machine_blocks_entire_episode_when_latest_ten_prints_are_too_slow(
    tmp_path,
):
    profile = PROFILES["youngone_afternoon"]
    gateway = FakeGateway(profile.profile_id)
    gateway.execution_velocity_span_ms = 35_000
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "youngone-slow-state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_profile_run_at(profile.profile_id))

    assert state["status"] == "NO_TRADE"
    assert state["attempt_consumed"] is True
    assert state["position_qty"] == 0
    assert {leg["status"] for leg in state["legs"]} == {"NO_FILL"}
    assert state["blocked_reason"] == "entry_execution_velocity_too_slow"
    assert state["last_action"] == "entry_execution_velocity_blocked_before_buy"
    assert gateway.buy_calls == []
    assert gateway.liquidity_calls == ["SOR"]
    assert gateway.execution_velocity_calls == ["SOR"]
    guard = state["signal_features"]["entry_execution_velocity"]
    assert guard["entry_execution_velocity_snapshot"]["recent_print_span_ms"] == (
        35_000
    )
    assert guard["entry_execution_velocity_allowed"] is False


def test_machine_rechecks_liquidity_after_restart_with_a_planned_leg(tmp_path):
    profile = PROFILES["nhn_afternoon"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "nhn-restart-state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    machine._state.update(
        {
            "trade_date": _profile_run_at(profile.profile_id).date().isoformat(),
            "status": "READY",
            "signal_features": {
                "entry_liquidity": {
                    "entry_liquidity_allowed": True,
                    "entry_liquidity_snapshot": {"route": "SOR"},
                }
            },
            "legs": [
                {
                    "leg_id": "L1",
                    "status": "PLANNED",
                    "entry_price": 75_000,
                    "quantity": 10,
                }
            ],
        }
    )
    gateway.best_bid_qty = 99

    machine._submit_planned_buys(_profile_run_at(profile.profile_id))

    assert gateway.liquidity_calls == ["SOR"]
    assert gateway.buy_calls == []
    assert machine._state["legs"][0]["status"] == "NO_FILL"
    assert machine._state["blocked_reason"] == (
        "entry_liquidity_touch_depth_insufficient"
    )


def test_machine_rechecks_same_signal_after_bounded_entry_delay(tmp_path, monkeypatch):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    monkeypatch.setattr(
        "src.trading.order.regular_two_leg_machine.resolve_entry_confirmation_delay",
        lambda **kwargs: (
            3,
            {
                "status": "applied",
                "policy_hash": "a" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    first_at = _profile_run_at(profile.profile_id)

    armed = machine.run_once(first_at)
    waiting = machine.run_once(first_at + timedelta(seconds=2))
    submitted = machine.run_once(first_at + timedelta(seconds=3))

    assert armed["pending_entry_confirmation"]["delay_sec"] == 3
    assert waiting["status"] == "READY"
    assert gateway.buy_calls == [22_650, 22_600]
    assert submitted["signal_features"]["signal_decision_at"] == first_at.isoformat()
    assert submitted["signal_features"]["entry_confirmation_delay_sec"] == 3


def test_machine_one_second_delay_survives_six_second_live_poll(tmp_path, monkeypatch):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    monkeypatch.setattr(
        "src.trading.order.regular_two_leg_machine.resolve_entry_confirmation_delay",
        lambda **kwargs: (
            1,
            {
                "status": "applied",
                "policy_hash": "a" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    first_at = _profile_run_at(profile.profile_id)

    machine.run_once(first_at)
    assert machine._next_loop_delay_sec(interval_sec=6, now=first_at) == 1.0
    assert (
        machine._next_loop_delay_sec(
            interval_sec=6, now=first_at + timedelta(milliseconds=500)
        )
        == 0.5
    )
    submitted = machine.run_once(first_at + timedelta(seconds=6))

    assert gateway.buy_calls == [22_650, 22_600]
    assert submitted["signal_features"]["entry_confirmation_delay_sec"] == 1


def test_machine_discards_entry_confirmation_after_recheck_window(
    tmp_path, monkeypatch
):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    monkeypatch.setattr(
        "src.trading.order.regular_two_leg_machine.resolve_entry_confirmation_delay",
        lambda **kwargs: (
            3,
            {
                "status": "applied",
                "policy_hash": "a" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    first_at = _profile_run_at(profile.profile_id)

    machine.run_once(first_at)
    expired = machine.run_once(first_at + timedelta(seconds=14))

    assert gateway.buy_calls == []
    assert expired["pending_entry_confirmation"] is None
    assert expired["last_action"] == "entry_confirmation_invalidated"
    assert expired["blocked_reason"] == ""


def test_machine_blocks_malformed_persisted_entry_confirmation(tmp_path, monkeypatch):
    profile = PROFILES["samsung_heavy_midday"]
    gateway = FakeGateway(profile.profile_id)
    monkeypatch.setattr(
        "src.trading.order.regular_two_leg_machine.resolve_entry_confirmation_delay",
        lambda **kwargs: (
            3,
            {
                "status": "applied",
                "policy_hash": "a" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    first_at = _profile_run_at(profile.profile_id)
    machine.run_once(first_at)
    machine._state["pending_entry_confirmation"]["signal_close"] = "invalid"

    blocked = machine.run_once(first_at + timedelta(seconds=1))

    assert gateway.buy_calls == []
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_pending_entry_confirmation_invalid"


def test_terminal_partial_fill_does_not_report_whole_episode_as_unfilled(tmp_path):
    profile = PROFILES["hanse_morning"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    state = machine.run_once(started_at)
    first_order = state["legs"][0]["buy_order_no"]
    second_order = state["legs"][1]["buy_order_no"]
    first_price = state["legs"][0]["entry_price"]

    gateway.snapshots[first_order] = ExecutionSnapshot(
        True, True, 4, 6, 10, first_price
    )
    machine.run_once(started_at + timedelta(minutes=3))
    gateway.snapshots[first_order] = ExecutionSnapshot(
        True, True, 4, 0, 10, first_price
    )
    state = machine.run_once(started_at + timedelta(minutes=3, seconds=1))
    target_order = state["legs"][0]["target_order_no"]
    target_price = state["legs"][0]["target_price"]
    gateway.snapshots[target_order] = ExecutionSnapshot(
        True, True, 4, 0, 4, target_price
    )
    gateway.snapshots[second_order] = ExecutionSnapshot(True, True, 0, 0, 10)

    state = machine.run_once(started_at + timedelta(minutes=3, seconds=2))

    assert state["status"] == "COMPLETE"
    assert state["position_qty"] == 0
    assert state["last_action"] == ("unfilled_buy_leg_resolved_after_sibling_completed")
    assert state["audit"][-1]["completed_sibling_leg_ids"] == ["signal_close"]


@pytest.mark.parametrize(
    ("prior_status", "prior_reason"),
    [
        ("COMPLETE", ""),
        ("BLOCKED", "state_leg_target_policy_mismatch"),
    ],
)
def test_prior_terminal_ledger_rolls_before_current_policy_validation(
    tmp_path, prior_status, prior_reason
):
    prior_profile = PROFILES["kakao_morning"]
    current_profile = replace(
        prior_profile,
        policy=replace(
            prior_profile.policy,
            target_ticks=prior_profile.policy.target_ticks + 1,
        ),
    )
    signal_close = 39_250
    legs = []
    owned_order_nos = []
    for index, plan in enumerate(prior_profile.policy.entry_legs(signal_close), 1):
        entry_price = int(plan["entry_price"])
        buy_order_no = f"B{index}"
        target_order_no = f"T{index}"
        owned_order_nos.extend([buy_order_no, target_order_no])
        legs.append(
            {
                "leg_id": plan["leg_id"],
                "price_role": plan["price_role"],
                "quantity": 1,
                "entry_price": entry_price,
                "status": "COMPLETE",
                "buy_order_no": buy_order_no,
                "fill_price": entry_price,
                "buy_filled_qty": 1,
                "position_qty": 0,
                "target_price": prior_profile.policy.target_price(entry_price),
                "target_order_no": target_order_no,
                "target_quantity": 1,
                "target_filled_qty": 1,
                "target_fill_price": prior_profile.policy.target_price(entry_price),
            }
        )
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "low_price_two_leg_kakao_morning_state_v1",
                "trade_date": "2026-08-13",
                "status": prior_status,
                "attempt_consumed": True,
                "signal_close": signal_close,
                "signal_features": {},
                "legs": legs,
                "position_qty": 0,
                "blocked_reason": prior_reason,
                "owned_order_nos": owned_order_nos,
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    machine = LowPriceTwoLegMachine(
        profile=current_profile,
        gateway=FakeGateway(current_profile.profile_id),
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(14, 9, 19))

    assert state["trade_date"] == "2026-08-14"
    assert state["status"] == "READY"
    assert state["blocked_reason"] != "state_leg_target_policy_mismatch"
    assert any(
        event.get("action") == "daily_state_initialized_from_prior_terminal_policy"
        and event.get("prior_trade_date") == "2026-08-13"
        and event.get("prior_blocked_reason") == prior_reason
        for event in state["audit"]
    )


def test_prior_policy_mismatch_with_open_exposure_never_rolls(tmp_path):
    profile = PROFILES["kakao_morning"]
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "low_price_two_leg_kakao_morning_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": True,
                "signal_features": {},
                "legs": [],
                "position_qty": 1,
                "blocked_reason": "state_leg_target_policy_mismatch",
                "owned_order_nos": [],
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=FakeGateway(profile.profile_id),
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(14, 9, 19))

    assert state["trade_date"] == "2026-08-13"
    assert state["status"] == "BLOCKED"
    assert state["position_qty"] == 1


def test_prior_held_inventory_keeps_its_original_target_policy(tmp_path):
    prior_profile = PRE_RECOMMENDATION_PROFILES["kakao_late_morning"]
    current_profile = PROFILES["kakao_late_morning"]
    signal_close = 38_850
    legs = []
    owned_order_nos = []
    for index, plan in enumerate(prior_profile.policy.entry_legs(signal_close), 1):
        entry_price = int(plan["entry_price"])
        buy_order_no = f"B{index}"
        target_order_no = f"T{index}"
        owned_order_nos.extend([buy_order_no, target_order_no])
        legs.append(
            {
                "leg_id": plan["leg_id"],
                "price_role": plan["price_role"],
                "quantity": 10,
                "entry_price": entry_price,
                "status": "HELD",
                "buy_order_no": buy_order_no,
                "buy_order_date": "2026-08-18",
                "buy_cancel_requested": False,
                "fill_price": entry_price,
                "buy_filled_at": "2026-08-18T10:08:00+09:00",
                "buy_filled_qty": 10,
                "position_qty": 10,
                "target_price": prior_profile.policy.target_price(entry_price),
                "target_order_no": target_order_no,
                "target_order_date": "2026-08-18",
                "target_quantity": 10,
                "target_filled_qty": 0,
                "target_fill_price": 0,
                "target_filled_at": "",
            }
        )
    state_path = tmp_path / "held.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "low_price_two_leg_kakao_late_morning_state_v1",
                "trade_date": "2026-08-18",
                "status": "HELD",
                "attempt_consumed": True,
                "signal_close": signal_close,
                "signal_features": {
                    "scan_start": "10:05:00",
                    "scan_last_bar": "10:34:00",
                    "lookback_bars": 15,
                    "required_drawdown_pct": 0.5,
                    "max_near_low_pct": 0.35,
                    "entry_valid_completed_bars": 5,
                    "target_ticks": 2,
                    "runtime_policy_source": "preopen_applied_policy",
                    "runtime_policy_hash": "prior-policy-hash",
                },
                "legs": legs,
                "position_qty": 20,
                "blocked_reason": "",
                "owned_order_nos": owned_order_nos,
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    machine = LowPriceTwoLegMachine(
        profile=current_profile,
        gateway=FakeGateway(current_profile.profile_id),
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(19, 10, 4))

    assert state["status"] == "HELD"
    assert state["blocked_reason"] == ""
    assert [leg["target_price"] for leg in state["legs"]] == [38_950, 38_900]
    assert current_profile.policy.target_ticks == 4


def test_mirae_machine_uses_user_approved_close_minus_one_split(tmp_path):
    profile = PROFILES["mirae_asset_morning"]
    gateway = FakeGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "mirae.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    state = machine.run_once(_profile_run_at(profile.profile_id))

    assert state["status"] == "BUY_OPEN"
    assert gateway.buy_calls == [22_650, 22_600]
    assert [leg["leg_id"] for leg in state["legs"]] == [
        "signal_close",
        "signal_close_minus_1tick",
    ]
    assert state["signal_features"]["target_ticks"] == 4
    reconciled = machine.run_once(_profile_run_at(profile.profile_id))
    assert reconciled["status"] == "BUY_OPEN"
    assert reconciled["blocked_reason"] == ""


def test_machine_requires_profile_symbol_manual_exclusion(tmp_path):
    profile = PROFILES["sk_eternix_midday"]
    gateway = FakeGateway(profile.profile_id)
    state = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "",
    ).run_once(_profile_run_at(profile.profile_id))
    assert state["blocked_reason"] == "475150_not_excluded_from_primary_bot"
    assert gateway.buy_calls == []


def test_machine_clears_transient_source_error_after_valid_bar_recovers(tmp_path):
    profile = PROFILES["sk_eternix_midday"]
    signal_start = datetime.combine(
        date(2026, 8, 12), profile.policy.scan_start, tzinfo=KST
    )

    class RecoveringGateway(FakeGateway):
        def __init__(self):
            super().__init__(profile.profile_id)
            self.source_calls = 0

        def completed_sor_minute_bars(self, *, trade_date, now):
            self.source_calls += 1
            if self.source_calls == 1:
                return MinuteBarsSnapshot(False, error="[1700] request limit")
            return MinuteBarsSnapshot(
                True,
                (MinuteBar(signal_start, 22_650, 22_650, 22_650, 22_650),),
            )

    gateway = RecoveringGateway()
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "source-recovery.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    failed = machine.run_once(signal_start + timedelta(minutes=1, seconds=10))
    recovered = machine.run_once(signal_start + timedelta(minutes=1, seconds=16))

    assert failed["blocked_reason"] == "[1700] request limit"
    assert recovered["blocked_reason"] == ""
    assert recovered["last_action"] == "bar_evaluated_no_signal"


def test_gateway_uses_bound_symbol_sor_and_one_share_for_every_write():
    session = FakeSession(
        [
            FakeResponse({"return_code": 0, "ord_no": "B1"}),
            FakeResponse({"return_code": 0, "ord_no": "T1"}),
            FakeResponse({"return_code": 0, "ord_no": "C1"}),
        ]
    )
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150",
        request_session=session,
        token_loader=lambda: "TOKEN",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    assert gateway.submit_limit_buy(price=17_000, quantity=10).accepted
    assert gateway.submit_limit_sell(price=17_050, quantity=10).accepted
    assert gateway.cancel_buy(order_no="B1").accepted
    assert [call[1]["headers"]["api-id"] for call in session.calls] == [
        "kt10000",
        "kt10001",
        "kt10003",
    ]
    assert all(call[1]["json"]["stk_cd"] == "475150" for call in session.calls)
    assert all(call[1]["json"].get("dmst_stex_tp") == "SOR" for call in session.calls)
    assert session.calls[0][1]["json"]["ord_qty"] == "10"
    assert session.calls[1][1]["json"]["ord_qty"] == "10"
    assert session.calls[2][1]["json"]["cncl_qty"] == "0"


def test_gateway_minute_request_uses_integrated_sor_code_and_completed_bar_only():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "stk_min_pole_chart_qry": [
                        {
                            "cntr_tm": "20260812131500",
                            "open_pric": "17000",
                            "high_pric": "17050",
                            "low_pric": "16950",
                            "cur_prc": "17000",
                        },
                        {
                            "cntr_tm": "20260812131600",
                            "open_pric": "17000",
                            "high_pric": "17050",
                            "low_pric": "16950",
                            "cur_prc": "17000",
                        },
                    ],
                }
            )
        ]
    )
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
    )
    snapshot = gateway.completed_sor_minute_bars(
        trade_date=date(2026, 8, 12), now=_at(12, 13, 16)
    )
    assert snapshot.source_ok
    assert len(snapshot.bars) == 1
    assert session.calls[0][1]["headers"]["api-id"] == "ka10080"
    assert session.calls[0][1]["json"]["stk_cd"] == "475150_AL"


def test_gateway_current_open_sell_snapshot_requires_exact_ka10075_order():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "oso": [
                        {
                            "ord_no": "0000123",
                            "orig_ord_no": "0000000",
                            "stk_cd": "A475150",
                            "oso_qty": "10",
                        }
                    ],
                }
            )
        ]
    )
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
    )

    snapshot = gateway.current_open_sell_snapshot(
        order_no="123", order_date="2026-09-01", observed_date="2026-09-01"
    )

    assert snapshot == CurrentOpenOrderSnapshot(
        True, True, exact_order_no="0000123"
    )
    call = session.calls[0][1]
    assert call["headers"]["api-id"] == "ka10075"
    assert call["json"] == {
        "all_stk_tp": "1",
        "trde_tp": "1",
        "stk_cd": "475150",
        "stex_tp": "0",
    }


@pytest.mark.parametrize(
    ("method", "response_body", "expected_error"),
    [
        (
            "execution",
            {"return_code": 0, "acnt_ord_cntr_prps_dtl": []},
            "execution_continuation_header_invalid",
        ),
        (
            "current_open",
            {"return_code": 0, "oso": []},
            "current_unfilled_continuation_header_invalid",
        ),
    ],
)
def test_gateway_rejects_missing_next_key_on_continuation(
    method, response_body, expected_error
):
    session = FakeSession(
        [FakeResponse(response_body, headers={"cont-yn": "Y", "next-key": ""})]
    )
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
    )

    if method == "execution":
        snapshot = gateway.execution_snapshot(
            order_no="123", order_date="2026-09-01", expected_order_qty=10
        )
    else:
        snapshot = gateway.current_open_sell_snapshot(
            order_no="123", order_date="2026-09-01", observed_date="2026-09-01"
        )

    assert snapshot.source_ok is False
    assert snapshot.found is False
    assert snapshot.error == expected_error


@pytest.mark.parametrize(
    "row",
    [
        {"ord_no": "NOT-NUMERIC", "stk_cd": "475150", "oso_qty": "10"},
        {"ord_no": "0000123", "stk_cd": "475150", "oso_qty": "-10"},
    ],
)
def test_gateway_never_infers_terminal_absence_from_malformed_open_rows(row):
    session = FakeSession([FakeResponse({"return_code": 0, "oso": [row]})])
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
    )

    snapshot = gateway.current_open_sell_snapshot(
        order_no="123", order_date="2026-09-01", observed_date="2026-09-01"
    )

    assert snapshot.source_ok is False
    assert snapshot.found is False
    assert snapshot.error == "current_unfilled_row_contract_invalid"


def test_gateway_never_joins_prior_date_target_to_reused_current_order_number():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "oso": [
                        {
                            "ord_no": "0000123",
                            "orig_ord_no": "0000000",
                            "stk_cd": "475150",
                            "oso_qty": "10",
                        }
                    ],
                }
            )
        ]
    )
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol="475150", request_session=session, token_loader=lambda: "TOKEN"
    )

    snapshot = gateway.current_open_sell_snapshot(
        order_no="123", order_date="2026-08-26", observed_date="2026-09-01"
    )

    assert snapshot == CurrentOpenOrderSnapshot(True, False)


def test_target_absent_from_current_unfilled_ledger_becomes_held(tmp_path):
    profile = PROFILES["sk_eternix_midday"]

    class CurrentOpenAwareGateway(FakeGateway):
        def current_open_sell_snapshot(self, **kwargs):
            return CurrentOpenOrderSnapshot(True, False)

    gateway = CurrentOpenAwareGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "target-terminal-absence.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    submitted = machine.run_once(started_at)
    first_buy, second_buy = [leg["buy_order_no"] for leg in submitted["legs"]]
    first_entry = submitted["legs"][0]["entry_price"]
    gateway.snapshots[first_buy] = ExecutionSnapshot(
        True, True, 10, 0, 10, first_entry
    )
    gateway.snapshots[second_buy] = ExecutionSnapshot(True, True, 0, 0, 10)
    targeted = machine.run_once(started_at + timedelta(seconds=1))
    target_order_no = targeted["legs"][0]["target_order_no"]
    gateway.snapshots[target_order_no] = ExecutionSnapshot(
        True, True, 0, 10, 10
    )

    reconciled = machine.run_once(started_at + timedelta(seconds=2))

    assert reconciled["status"] == "HELD"
    assert reconciled["position_qty"] == 10
    assert reconciled["legs"][0]["status"] == "HELD"
    assert reconciled["last_action"] == "target_terminal_absence_position_held"
    assert reconciled["audit"][-1]["current_open_source"] == (
        "ka10075_terminal_absence_confirmed"
    )


def test_target_exact_current_unfilled_order_remains_target_open(tmp_path):
    profile = PROFILES["sk_eternix_midday"]

    class CurrentOpenAwareGateway(FakeGateway):
        def current_open_sell_snapshot(self, **kwargs):
            return CurrentOpenOrderSnapshot(
                True, True, exact_order_no=str(kwargs["order_no"])
            )

    gateway = CurrentOpenAwareGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "target-exact-current-open.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    submitted = machine.run_once(started_at)
    first_buy, second_buy = [leg["buy_order_no"] for leg in submitted["legs"]]
    first_entry = submitted["legs"][0]["entry_price"]
    gateway.snapshots[first_buy] = ExecutionSnapshot(
        True, True, 10, 0, 10, first_entry
    )
    gateway.snapshots[second_buy] = ExecutionSnapshot(True, True, 0, 0, 10)
    targeted = machine.run_once(started_at + timedelta(seconds=1))
    target_order_no = targeted["legs"][0]["target_order_no"]
    gateway.snapshots[target_order_no] = ExecutionSnapshot(
        True, True, 0, 10, 10
    )

    reconciled = machine.run_once(started_at + timedelta(seconds=2))

    assert reconciled["status"] == "TARGET_OPEN"
    assert reconciled["position_qty"] == 10
    assert reconciled["legs"][0]["status"] == "TARGET_OPEN"
    assert reconciled["last_action"] == "target_open_wait"
    assert reconciled["audit"][-1]["current_open_source"] == (
        "ka10075_exact_order"
    )


def test_target_successor_open_order_fails_closed_without_adopting_it(tmp_path):
    profile = PROFILES["sk_eternix_midday"]

    class SuccessorGateway(FakeGateway):
        def current_open_sell_snapshot(self, **kwargs):
            return CurrentOpenOrderSnapshot(
                True, True, successor_order_no="SUCCESSOR-1"
            )

    gateway = SuccessorGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "target-successor.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    submitted = machine.run_once(started_at)
    first_buy, second_buy = [leg["buy_order_no"] for leg in submitted["legs"]]
    first_entry = submitted["legs"][0]["entry_price"]
    gateway.snapshots[first_buy] = ExecutionSnapshot(
        True, True, 10, 0, 10, first_entry
    )
    gateway.snapshots[second_buy] = ExecutionSnapshot(True, True, 0, 0, 10)
    targeted = machine.run_once(started_at + timedelta(seconds=1))
    target_order_no = targeted["legs"][0]["target_order_no"]
    gateway.snapshots[target_order_no] = ExecutionSnapshot(
        True, True, 0, 10, 10
    )

    reconciled = machine.run_once(started_at + timedelta(seconds=2))

    assert reconciled["status"] == "BLOCKED"
    assert reconciled["blocked_reason"].startswith(
        "target_successor_order_not_owned:"
    )
    assert "SUCCESSOR-1" not in reconciled["owned_order_nos"]


def test_target_current_unfilled_source_failure_keeps_target_open(tmp_path):
    profile = PROFILES["sk_eternix_midday"]

    class SourceUnavailableGateway(FakeGateway):
        def current_open_sell_snapshot(self, **kwargs):
            return CurrentOpenOrderSnapshot(
                False, False, error="current_unfilled_request_failed"
            )

    gateway = SourceUnavailableGateway(profile.profile_id)
    machine = LowPriceTwoLegMachine(
        profile=profile,
        gateway=gateway,
        state_path=tmp_path / "target-current-open-source-failure.json",
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    started_at = _profile_run_at(profile.profile_id)
    submitted = machine.run_once(started_at)
    first_buy, second_buy = [leg["buy_order_no"] for leg in submitted["legs"]]
    first_entry = submitted["legs"][0]["entry_price"]
    gateway.snapshots[first_buy] = ExecutionSnapshot(
        True, True, 10, 0, 10, first_entry
    )
    gateway.snapshots[second_buy] = ExecutionSnapshot(True, True, 0, 0, 10)
    targeted = machine.run_once(started_at + timedelta(seconds=1))
    target_order_no = targeted["legs"][0]["target_order_no"]
    gateway.snapshots[target_order_no] = ExecutionSnapshot(
        True, True, 0, 10, 10
    )

    reconciled = machine.run_once(started_at + timedelta(seconds=2))

    assert reconciled["status"] == "TARGET_OPEN"
    assert reconciled["position_qty"] == 10
    assert reconciled["last_action"] == "target_current_open_reconciliation_wait"
    assert reconciled["audit"][-1]["error"] == "current_unfilled_request_failed"


def test_research_evidence_gate_validates_each_selected_profile(tmp_path):
    assert all(validate_research_evidence(profile)[0] for profile in PROFILES.values())
    profiles = {}
    source_meta = {}
    legacy_profiles = [
        PRE_RECOMMENDATION_PROFILES["samsung_heavy_midday"],
        PRE_RECOMMENDATION_PROFILES["samsung_heavy_afternoon"],
        PRE_RECOMMENDATION_PROFILES["sk_eternix_midday"],
    ]
    for profile in legacy_profiles:
        source_meta[profile.symbol] = {
            "source_quality_status": "PASS",
            "trading_date_count": 46,
            "invalid_row_count": 0,
            "duplicate_row_count": 0,
        }
        profiles[profile.profile_id] = {
            "recommended_spot": {
                "scan_start": profile.policy.scan_start.strftime("%H:%M"),
                "scan_end": profile.policy.scan_last_bar.strftime("%H:%M"),
                "lookback_bars": profile.policy.lookback_bars,
                "rolling_high_drawdown_pct": profile.policy.rolling_high_drawdown_pct,
                "rolling_low_proximity_pct": profile.policy.rolling_low_proximity_pct,
            },
            "decision": "holdout_pass_source_only_early_candidate",
            "selected": {
                "holdout": {
                    "signal_episodes": 3,
                    "completed_legs": 4,
                    "held_legs": 0,
                    "notional_weighted_ev_pct": 0.01,
                }
            },
        }
    path = tmp_path / "report.json"
    payload = {
        "schema": "low_price_two_leg_entry_spot_research_v1",
        "start_date": "2026-06-05",
        "end_date": "2026-08-10",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_meta": source_meta,
        "profiles": profiles,
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert all(
        validate_research_evidence(
            profile,
            path,
            expected_sha256=digest,
            target_date=date(2026, 8, 10),
        )[0]
        for profile in legacy_profiles
    )
    payload["profiles"]["samsung_heavy_midday"]["recommended_spot"][
        "scan_start"
    ] = "13:19"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert not validate_research_evidence(
        PROFILES["samsung_heavy_midday"], path, expected_sha256=digest
    )[0]


def test_preflight_requires_token_main_bot_exclusion_evidence_and_applied_policy():
    profile = PROFILES["sk_eternix_midday"]
    blocked = evaluate_preflight(
        target_date=date(2026, 8, 12),
        profile=profile,
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="",
        research_evidence_ready=True,
        applied_policy_ready=True,
        applied_policy_hash="hash",
    )
    assert not blocked.ready
    assert blocked.blockers == ("manual_operator_exclusion_missing",)
    ready = evaluate_preflight(
        target_date=date(2026, 8, 12),
        profile=profile,
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
        research_evidence_ready=True,
        applied_policy_ready=True,
        applied_policy_hash="hash",
    )
    assert ready.ready


@pytest.mark.parametrize(
    "profile_id",
    [
        "mirae_asset_morning",
        "jeju_semiconductor_morning",
        "doosan_enerbility_morning",
        "hanwha_ocean_late_morning",
    ],
)
def test_new_profile_authority_binds_exact_offsets_and_frozen_evidence(profile_id):
    profile = PRE_RECOMMENDATION_PROFILES[profile_id]
    decision = evaluate_preflight(
        target_date=date(2026, 8, 13),
        profile=profile,
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
        research_evidence_ready=True,
        applied_policy_ready=True,
        applied_policy_hash="HASH",
    )
    artifact = build_authority_artifact(
        decision,
        profile=profile,
        applied_policy=PRE_RECOMMENDATION_BASELINE_POLICIES[profile_id],
        applied_policy_hash="HASH",
        observed_at=_at(13, 8, 55),
    )

    assert artifact["policy"]["allocation"]["entry_offsets_ticks"] == list(
        profile.policy.entry_offsets_ticks
    )
    assert artifact["policy"]["target_ticks"] == profile.policy.target_ticks
    assert artifact["policy"]["entry_valid_completed_bars"] == (
        profile.policy.entry_valid_completed_bars
    )
    assert artifact["evidence"]["schema"] == (
        "low_price_two_leg_episode_policy_research_v1"
    )


@pytest.mark.parametrize(
    "profile_id",
    [
        "kakao_morning",
        "kepco_afternoon",
        "kakao_late_morning",
        "sk_eternix_morning",
        "mirae_asset_midday",
        "sk_eternix_afternoon",
    ],
)
def test_expanded_recommendation_authority_binds_v5_evidence(profile_id):
    profile = PRE_RECOMMENDATION_PROFILES[profile_id]
    decision = evaluate_preflight(
        target_date=date(2026, 8, 13),
        profile=profile,
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
        research_evidence_ready=True,
        applied_policy_ready=True,
        applied_policy_hash="HASH",
    )
    artifact = build_authority_artifact(
        decision,
        profile=profile,
        applied_policy=PRE_RECOMMENDATION_BASELINE_POLICIES[profile_id],
        applied_policy_hash="HASH",
        observed_at=_at(13, 8, 55),
    )

    assert artifact["evidence"]["schema"] == (
        "low_price_two_leg_user_approved_profile_evidence_v1"
    )
    assert artifact["evidence"]["window"] == (
        "2026-06-05_through_2026-08-12_48_trading_days"
    )
    assert artifact["sample_floor"] == (
        "explicit_user_selected_48_trading_day_clean_baseline_source_replay"
    )


def test_kakao_morning_authority_records_target_transition(tmp_path):
    profile = PRE_RECOMMENDATION_PROFILES["kakao_morning"]
    target_date = date(2026, 8, 14)
    applied, _ = build_applied_policy(
        target_date=target_date, candidate_dir=tmp_path / "none"
    )
    decision = evaluate_preflight(
        target_date=target_date,
        profile=profile,
        main_bot_active=True,
        shared_token_available=True,
        operator_exclusion_source="manual_operator",
        research_evidence_ready=True,
        applied_policy_ready=True,
        applied_policy_hash=applied["policy_hash"],
    )
    artifact = build_authority_artifact(
        decision,
        profile=profile,
        applied_policy=applied["profiles"][profile.profile_id]["policy"],
        applied_policy_hash=applied["policy_hash"],
        observed_at=_at(14, 8, 55),
    )

    assert artifact["policy"]["target_ticks"] == 3
    assert artifact["policy"]["target_ticks_baseline"] == 2
    assert artifact["policy"]["target_ticks_authority"] == (
        "explicit_user_directed_runtime_policy_transition"
    )
    assert artifact["policy"]["target_ticks_transition"] == (
        KAKAO_MORNING_TARGET_TRANSITION
    )


def test_expanded_recommendation_preflight_rejects_source_only_contract_tamper(
    tmp_path,
):
    source_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "config"
        / "low_price_two_leg_expanded_profile_evidence_2026-08-12.json"
    )
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    recommendation = next(
        row
        for row in payload["recommendations"]
        if row["profile_id"] == "candidate_035720_morning"
    )
    recommendation["implementation_status"] = "implemented_without_user_review"
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    path = tmp_path / "tampered_expanded_recommendation.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    ready, reason = validate_research_evidence(
        PRE_RECOMMENDATION_PROFILES["kakao_morning"],
        path,
        expected_sha256=digest,
        target_date=date(2026, 8, 18),
    )

    assert not ready
    assert reason == "research_profile_result_not_eligible"


def test_preopen_apply_writes_and_loads_safe_baseline_when_no_candidate(tmp_path):
    applied, status = build_applied_policy(
        target_date=date(2026, 8, 12), candidate_dir=tmp_path / "candidates"
    )
    assert status == "baseline_no_prior_candidate"
    assert validate_applied(applied, target_date=date(2026, 8, 12))[0]
    applied_dir = tmp_path / "applied"
    atomic_write_json(applied_dir / "low_price_two_leg_policy_2026-08-12.json", applied)
    policy, digest, reason = load_applied_profile_policy(
        "samsung_heavy_midday",
        target_date=date(2026, 8, 12),
        applied_dir=applied_dir,
    )
    assert reason == "ready"
    assert digest == applied["policy_hash"]
    assert policy == BASELINE_POLICIES["samsung_heavy_midday"]


def test_kakao_morning_target_transition_starts_next_date_only(tmp_path):
    today, _ = build_applied_policy(
        target_date=date(2026, 8, 13), candidate_dir=tmp_path / "none"
    )
    tomorrow, _ = build_applied_policy(
        target_date=date(2026, 8, 14), candidate_dir=tmp_path / "none"
    )

    assert today["profiles"]["kakao_morning"]["policy"]["target_ticks"] == 2
    assert "operator_policy_transitions" not in today
    assert validate_applied(today, target_date=date(2026, 8, 13)) == (
        True,
        "valid",
    )
    assert tomorrow["profiles"]["kakao_morning"]["policy"]["target_ticks"] == 3
    assert tomorrow["profiles"]["kakao_late_morning"]["policy"]["target_ticks"] == 2
    assert tomorrow["profiles"]["mirae_asset_morning"]["policy"]["target_ticks"] == 4
    assert tomorrow["operator_policy_transitions"] == [KAKAO_MORNING_TARGET_TRANSITION]
    assert validate_applied(tomorrow, target_date=date(2026, 8, 14)) == (
        True,
        "valid",
    )

    tampered = json.loads(json.dumps(tomorrow))
    tampered.pop("operator_policy_transitions")
    assert validate_applied(tampered, target_date=date(2026, 8, 14))[1] == (
        "applied_operator_policy_transition_invalid"
    )


def test_legacy_two_share_candidate_normalizes_to_current_twenty_share_runtime(
    tmp_path,
):
    legacy_policies = {
        profile_id: {**policy, "quantity": 2}
        for profile_id, policy in PRE_RECOMMENDATION_BASELINE_POLICIES.items()
    }
    legacy = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": "2026-08-12",
        "source_report": "low_price_two_leg_tuning",
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": "2026-06-05",
        "policy_hash": policy_hash(legacy_policies),
        "policy_mutations": [],
        "same_stage_owner_guard": {"mutation_present": False},
        "profiles": {
            profile_id: {
                "selection_status": "carry_forward_profile_policy",
                "selected_axis": None,
                "policy": policy,
                "allowed_runtime_apply": True,
            }
            for profile_id, policy in legacy_policies.items()
        },
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
    }
    assert all(item["policy"]["quantity"] == 2 for item in legacy["profiles"].values())
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / "low_price_two_leg_policy_candidate_2026-08-12.json").write_text(
        json.dumps(legacy), encoding="utf-8"
    )

    applied, status = build_applied_policy(
        target_date=date(2026, 8, 14), candidate_dir=candidate_dir
    )

    assert status == "candidate_applied"
    assert all(
        item["policy"]["quantity"] == 20 for item in applied["profiles"].values()
    )
    assert validate_applied(applied, target_date=date(2026, 8, 14)) == (
        True,
        "valid",
    )


def test_kakao_morning_service_consumes_applied_three_tick_target():
    transitioned = apply_operator_policy_transitions(
        PRE_RECOMMENDATION_BASELINE_POLICIES, target_date=date(2026, 8, 14)
    )
    profile = _profile_with_applied_policy(
        PRE_RECOMMENDATION_PROFILES["kakao_morning"],
        transitioned["kakao_morning"],
        "HASH",
    )

    assert profile.policy.target_ticks == 3
    assert profile.policy.target_price(39_250) == 39_400
    assert profile.policy.target_price(39_200) == 39_350
    assert profile.policy.runtime_policy_source == "preopen_applied_policy"
    assert profile.policy.runtime_policy_hash == "HASH"


def test_three_tick_research_extension_is_scoped_to_kakao_morning():
    kakao_targets = {
        candidate.target_ticks
        for candidate in candidate_grid(PROFILES["kakao_morning"])
    }
    kepco_targets = {
        candidate.target_ticks
        for candidate in candidate_grid(PROFILES["kepco_afternoon"])
    }

    assert 3 in kakao_targets
    assert 3 not in kepco_targets


def test_pre_expansion_applied_policy_is_scoped_to_legacy_profiles_and_date(tmp_path):
    applied, _ = build_applied_policy(
        target_date=date(2026, 8, 12), candidate_dir=tmp_path / "none"
    )
    applied["profiles"] = {
        profile_id: applied["profiles"][profile_id]
        for profile_id in {
            "samsung_heavy_midday",
            "samsung_heavy_afternoon",
            "sk_eternix_midday",
        }
    }
    applied["policy_hash"] = policy_hash(
        {profile_id: item["policy"] for profile_id, item in applied["profiles"].items()}
    )
    assert validate_applied(applied, target_date=date(2026, 8, 12)) == (
        True,
        "valid",
    )
    applied_dir = tmp_path / "applied"
    applied_dir.mkdir()
    atomic_write_json(applied_dir / "low_price_two_leg_policy_2026-08-12.json", applied)
    assert (
        load_applied_profile_policy(
            "samsung_heavy_afternoon",
            target_date=date(2026, 8, 12),
            applied_dir=applied_dir,
        )[2]
        == "ready"
    )
    assert (
        load_applied_profile_policy(
            "mirae_asset_morning",
            target_date=date(2026, 8, 12),
            applied_dir=applied_dir,
        )[2]
        == "applied_profile_policy_missing"
    )
    applied["target_date"] = "2026-08-13"
    assert validate_applied(applied, target_date=date(2026, 8, 13))[1] == (
        "applied_profile_set_invalid"
    )


def _tuning_row(profile_id: str, index: int, *, strong: bool) -> dict:
    profile = PROFILES[profile_id]
    profit_pct = 0.50 if strong else -0.10
    return {
        "profile_id": profile_id,
        "symbol": profile.symbol,
        "session": profile.session,
        "target_date": f"2026-07-{index + 1:02d}",
        "source_quality": "pass",
        "source_quality_reasons": [],
        "eligible_for_tuning": True,
        "attempted": True,
        "no_signal": False,
        "state_status": "COMPLETE",
        "signal_features": {
            "observed_drawdown_pct": 1.60 if strong else 0.80,
            "observed_near_low_pct": 0.15,
        },
        "legs": [
            {
                "leg_id": leg_id,
                "quantity": 1,
                "status": "COMPLETE",
                "entry_price": 20_000,
                "fill_price": 20_000,
                "target_price": 20_100,
                "target_fill_price": 20_100,
                "completed": True,
                "held": False,
                "terminal": True,
                "buy_filled_qty": 1,
                "net_profit_pct": profit_pct,
                "profit_price_source": "broker_target_fill_price",
            }
            for leg_id in profile.policy.entry_leg_ids
        ],
    }


def test_tuning_accepts_ten_share_partial_fill_and_weights_actual_quantity(
    tmp_path: Path,
):
    from src.engine.monitoring.low_price_two_leg_tuning import (
        _aggregate,
        extract_profile_row,
    )

    profile_id = "samsung_heavy_midday"
    profile = PROFILES[profile_id]
    signal_close = 20_000
    plans = profile.policy.entry_legs(signal_close)
    completed_plan, no_fill_plan = plans
    completed_fill_qty = 4
    completed_fill_price = int(completed_plan["entry_price"])
    target_price = profile.policy.target_price(completed_fill_price)
    payload = {
        "schema": f"low_price_two_leg_{profile_id}_state_v1",
        "trade_date": "2026-08-13",
        "status": "COMPLETE",
        "attempt_consumed": True,
        "signal_features": {
            "schema": "regular_two_leg_entry_signal_features_v1",
            "strategy": profile_id,
            "symbol": profile.symbol,
            "signal_close": signal_close,
        },
        "legs": [
            {
                "leg_id": completed_plan["leg_id"],
                "quantity": 10,
                "entry_price": completed_plan["entry_price"],
                "status": "COMPLETE",
                "fill_price": completed_fill_price,
                "position_qty": 0,
                "buy_filled_qty": completed_fill_qty,
                "target_price": target_price,
                "target_filled_qty": completed_fill_qty,
                "target_fill_price": target_price,
            },
            {
                "leg_id": no_fill_plan["leg_id"],
                "quantity": 10,
                "entry_price": no_fill_plan["entry_price"],
                "status": "NO_FILL",
                "fill_price": 0,
                "position_qty": 0,
                "buy_filled_qty": 0,
                "target_price": 0,
                "target_filled_qty": 0,
            },
        ],
    }
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    row = extract_profile_row(
        profile_id=profile_id,
        state_path=state_path,
        target_date="2026-08-13",
        cost_pct=0.20,
    )
    summary = _aggregate([row])
    completed_profit_pct = (target_price / completed_fill_price - 1.0) * 100.0 - 0.20
    expected_ev = (
        completed_fill_price
        * completed_fill_qty
        * completed_profit_pct
        / sum(int(plan["entry_price"]) * 10 for plan in plans)
    )

    assert row["source_quality"] == "pass"
    assert summary["notional_weighted_ev_pct"] == pytest.approx(expected_ev)

    payload["legs"][1]["quantity"] = 1
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    mixed_row = extract_profile_row(
        profile_id=profile_id,
        state_path=state_path,
        target_date="2026-08-13",
        cost_pct=0.20,
    )
    assert mixed_row["source_quality"] == "gap"
    assert "leg_quantity_or_status_invalid" in mixed_row["source_quality_reasons"]


def _skt_partial_fill_economics_row() -> dict:
    return {
        "profile_id": "sk_telecom_afternoon",
        "symbol": "017670",
        "session": "afternoon",
        "target_date": "2026-08-20",
        "source_quality": "pass",
        "source_quality_reasons": [],
        "eligible_for_tuning": True,
        "attempted": True,
        "state_status": "COMPLETE",
        "legs": [
            {
                "leg_id": "signal_close",
                "quantity": 10,
                "status": "COMPLETE",
                "entry_price": 96_600,
                "fill_price": 96_600,
                "target_price": 96_800,
                "target_fill_price": 96_800,
                "target_filled_qty": 4,
                "target_filled_at": "2026-08-20T14:31:00+09:00",
                "buy_filled_qty": 4,
                "completed": True,
                "terminal": True,
                "held": False,
                "profit_price_source": "broker_target_fill_price",
                "net_profit_pct": round(
                    (96_800 / 96_600 - 1) * 100 - DEFAULT_ROUND_TRIP_COST_PCT,
                    6,
                ),
            },
            {
                "leg_id": "signal_close_minus_1tick",
                "quantity": 10,
                "status": "NO_FILL",
                "entry_price": 96_500,
                "fill_price": 0,
                "target_filled_qty": 0,
                "buy_filled_qty": 0,
                "completed": False,
                "terminal": True,
                "held": False,
                "profit_price_source": "not_completed",
                "net_profit_pct": None,
            },
        ],
    }


def test_skt_partial_fill_uses_exact_negative_broker_pnl_when_uniquely_matched():
    row = _skt_partial_fill_economics_row()

    def loader(trade_date: str, symbol: str) -> list[dict]:
        assert (trade_date, symbol) == ("2026-08-20", "017670")
        return [
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "filled_qty": 4,
                "buy_average_price": 96_600,
                "sell_average_price": 96_800,
                "realized_net_profit_krw": -73,
                "broker_profit_rate_pct": -0.02,
                "commission_krw": 100,
                "tax_krw": 773,
                "source_api": "ka10073",
            }
        ]

    reconciliation = _apply_broker_realized_economics([row], loader)
    summary = _aggregate([row])

    assert reconciliation == {"matched": 1, "fallback": 0, "api_requests": 1}
    assert row["broker_realized_economics"]["status"] == "matched_exact"
    assert row["broker_realized_economics"]["entry_trade_date"] == "2026-08-20"
    assert row["broker_realized_economics"]["realization_date"] == "2026-08-20"
    assert row["broker_realized_economics"]["realized_net_profit_krw"] == -73
    assert summary["broker_realized_net_profit_krw"] == -73
    assert summary["exact_broker_cost_completed_legs"] == 1
    assert summary["fixed_cost_estimate_completed_legs"] == 0
    assert summary["notional_weighted_ev_pct"] < 0


def test_skt_partial_fill_fixed_cost_fallback_is_also_negative():
    row = _skt_partial_fill_economics_row()
    _apply_broker_realized_economics([row], None)

    summary = _aggregate([row])

    assert row["broker_realized_economics"] == {
        "status": "fixed_cost_fallback",
        "reason": "ka10073_loader_not_configured",
        "realization_date": "2026-08-20",
        "realization_date_source": "target_fill_reconciliation_date",
        "selection_effect": True,
    }
    assert summary["broker_realized_net_profit_krw"] < 0
    assert summary["exact_broker_cost_completed_legs"] == 0
    assert summary["fixed_cost_estimate_completed_legs"] == 1


def test_exact_broker_pnl_is_not_allocated_across_same_symbol_day_profiles():
    first = _skt_partial_fill_economics_row()
    second = json.loads(json.dumps(first))
    second["profile_id"] = "sk_telecom_late_morning"

    def loader(_trade_date: str, _symbol: str) -> list[dict]:
        raise AssertionError("ambiguous symbol-day must not query or allocate")

    reconciliation = _apply_broker_realized_economics([first, second], loader)

    assert reconciliation == {"matched": 0, "fallback": 2, "api_requests": 0}
    assert {row["broker_realized_economics"]["reason"] for row in (first, second)} == {
        "multiple_episode_profiles_share_symbol_realization_day"
    }


def test_carried_episode_queries_exact_pnl_on_realization_date() -> None:
    row = _skt_partial_fill_economics_row()
    row["target_date"] = "2026-08-19"
    row["legs"][0]["target_filled_at"] = "2026-08-20T09:11:00+09:00"
    calls: list[tuple[str, str]] = []

    def loader(trade_date: str, symbol: str) -> list[dict]:
        calls.append((trade_date, symbol))
        return [
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "filled_qty": 4,
                "buy_average_price": 96_600,
                "sell_average_price": 96_800,
                "realized_net_profit_krw": -73,
                "broker_profit_rate_pct": -0.02,
                "commission_krw": 100,
                "tax_krw": 773,
                "source_api": "ka10073",
            }
        ]

    result = _apply_broker_realized_economics([row], loader)

    assert result == {"matched": 1, "fallback": 0, "api_requests": 1}
    assert calls == [("2026-08-20", "017670")]
    assert row["broker_realized_economics"]["entry_trade_date"] == "2026-08-19"
    assert row["broker_realized_economics"]["realization_date"] == "2026-08-20"


def test_multiple_realization_dates_use_fixed_cost_without_query() -> None:
    row = _skt_partial_fill_economics_row()
    second = json.loads(json.dumps(row["legs"][0]))
    second["leg_id"] = "signal_close_minus_1tick"
    second["target_filled_at"] = "2026-08-21T09:11:00+09:00"
    row["legs"] = [row["legs"][0], second]

    result = _apply_broker_realized_economics(
        [row], lambda *_args: (_ for _ in ()).throw(AssertionError("must not query"))
    )

    assert result == {"matched": 0, "fallback": 1, "api_requests": 0}
    assert row["broker_realized_economics"]["reason"] == (
        "completed_legs_have_multiple_realization_dates"
    )


def test_ka10073_loader_uses_official_path_headers_fields_and_normalizes(monkeypatch):
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return [
            {
                "return_code": 0,
                "dt_stk_rlzt_pl": [
                    {
                        "dt": "20260820",
                        "stk_cd": "017670",
                        "cntr_qty": "4",
                        "buy_uv": "96600",
                        "cntr_pric": "96800",
                        "tdy_sel_pl": "-73",
                        "pl_rt": "-0.02",
                        "tdy_trde_cmsn": "100",
                        "tdy_trde_tax": "773",
                    }
                ],
            }
        ]

    monkeypatch.setattr(
        "src.engine.monitoring.low_price_two_leg_tuning.kiwoom_utils.get_api_url",
        lambda endpoint: f"https://api.example{endpoint}",
    )
    monkeypatch.setattr(
        "src.engine.monitoring.low_price_two_leg_tuning.kiwoom_utils.fetch_kiwoom_api_continuous",
        fake_fetch,
    )

    rows = load_realized_pnl_ka10073("TOKEN", "2026-08-20", "017670")

    assert captured == {
        "url": "https://api.example/api/dostk/acnt",
        "token": "TOKEN",
        "api_id": "ka10073",
        "payload": {
            "stk_cd": "017670",
            "strt_dt": "20260820",
            "end_dt": "20260820",
        },
        "use_continuous": True,
    }
    assert rows[0]["realized_net_profit_krw"] == -73
    assert rows[0]["commission_krw"] == 100
    assert rows[0]["tax_krw"] == 773


def test_tuning_accepts_exact_date_kakao_three_tick_policy_and_hash(tmp_path):
    profile_id = "kakao_morning"
    target_date = date(2026, 8, 14)
    applied_dir = tmp_path / "applied"
    applied, status = build_applied_policy(
        target_date=target_date,
        candidate_dir=tmp_path / "candidates",
    )
    assert status == "baseline_no_prior_candidate"
    atomic_write_json(
        applied_dir / f"low_price_two_leg_policy_{target_date.isoformat()}.json",
        applied,
    )
    profile = PROFILES[profile_id]
    signal_close = 39_250
    policy = applied["profiles"][profile_id]["policy"]
    plans = profile.policy.entry_legs(signal_close)
    legs = []
    for plan in plans:
        fill_price = int(plan["entry_price"])
        legs.append(
            {
                "leg_id": plan["leg_id"],
                "quantity": 10,
                "entry_price": fill_price,
                "status": "COMPLETE",
                "fill_price": fill_price,
                "position_qty": 0,
                "buy_filled_qty": 10,
                "target_price": move_price_by_ticks(fill_price, 3),
                "target_filled_qty": 10,
                "target_fill_price": move_price_by_ticks(fill_price, 3),
            }
        )
    state = {
        "schema": f"low_price_two_leg_{profile_id}_state_v1",
        "trade_date": target_date.isoformat(),
        "status": "COMPLETE",
        "attempt_consumed": True,
        "signal_features": {
            "schema": "regular_two_leg_entry_signal_features_v1",
            "strategy": profile_id,
            "symbol": profile.symbol,
            "signal_close": signal_close,
            "observed_drawdown_pct": 1.0,
            "observed_near_low_pct": 0.1,
            "required_drawdown_pct": policy["rolling_high_drawdown_pct"],
            "max_near_low_pct": policy["rolling_low_proximity_pct"],
            "lookback_bars": policy["lookback_bars"],
            "entry_valid_completed_bars": policy["entry_valid_completed_bars"],
            "target_ticks": policy["target_ticks"],
            "runtime_policy_source": "preopen_applied_policy",
            "runtime_policy_hash": applied["policy_hash"],
        },
        "legs": legs,
    }
    state_path = tmp_path / "kakao.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    row = extract_profile_row(
        profile_id=profile_id,
        state_path=state_path,
        target_date=target_date.isoformat(),
        cost_pct=0.20,
        applied_dir=applied_dir,
    )

    assert row["source_quality"] == "pass"
    assert all(
        leg["profit_price_source"] == "broker_target_fill_price" for leg in row["legs"]
    )
    state["signal_features"]["runtime_policy_hash"] = "f" * 64
    state_path.write_text(json.dumps(state), encoding="utf-8")
    mismatched = extract_profile_row(
        profile_id=profile_id,
        state_path=state_path,
        target_date=target_date.isoformat(),
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert (
        "signal_feature_exact_date_applied_policy_mismatch"
        in mismatched["source_quality_reasons"]
    )
    state["signal_features"]["runtime_policy_hash"] = applied["policy_hash"]
    state["legs"][0]["quantity"] = 1
    state_path.write_text(json.dumps(state), encoding="utf-8")
    quantity_mismatch = extract_profile_row(
        profile_id=profile_id,
        state_path=state_path,
        target_date=target_date.isoformat(),
        cost_pct=0.20,
        applied_dir=applied_dir,
    )
    assert (
        "exact_date_applied_quantity_mismatch"
        in quantity_mismatch["source_quality_reasons"]
    )


def test_tuning_keeps_profiles_separate_and_selects_only_one_axis(tmp_path):
    from src.engine.monitoring.low_price_two_leg_tuning import _aggregate

    target = "samsung_heavy_midday"
    rows = [_tuning_row(target, index, strong=index % 2 == 0) for index in range(20)]
    windows = {CLEAN_WINDOW_NAME: {}}
    for profile_id in PROFILES_20260824_PRIOR:
        profile_rows = rows if profile_id == target else []
        windows[CLEAN_WINDOW_NAME][profile_id] = {
            "summary": _aggregate(profile_rows),
            "rows": profile_rows,
        }
    report = {
        "target_date": "2026-08-21",
        "generated_at_kst": "2026-08-21T20:10:00+09:00",
        "clean_tuning_baseline_date": "2026-06-05",
        "target_date_is_krx_trading_day": True,
        "source_quality_preflight": {"tuning_input_allowed": True},
        "daily": {
            "profiles": {
                profile_id: {"source_quality": "pass"}
                for profile_id in PROFILES_20260824_PRIOR
            }
        },
        "windows": windows,
    }
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "low_price",
        samsung_candidate_dir=tmp_path / "samsung",
    )
    assert validate_candidate(candidate)[0]
    legacy_candidate = json.loads(json.dumps(candidate))
    legacy_candidate["source_report_schema"] = "low_price_two_leg_tuning_report_v1"
    assert validate_candidate(legacy_candidate) == (True, "valid")
    assert candidate["policy_mutations"] == [
        {
            "profile_id": target,
            "axis": "rolling_high_drawdown_pct",
            "before": 0.75,
            "after": 1.0,
        }
    ]
    assert all(
        item["policy"] == PROFILE_20260821_BASELINE_POLICIES[profile_id]
        for profile_id, item in candidate["profiles"].items()
        if profile_id != target
    )
    transition_dir = tmp_path / "target_transition"
    transition_dir.mkdir()
    (transition_dir / "low_price_two_leg_policy_candidate_2026-08-21.json").write_text(
        json.dumps(candidate), encoding="utf-8"
    )
    transitioned_applied, transitioned_status = build_applied_policy(
        target_date=date(2026, 8, 22), candidate_dir=transition_dir
    )
    assert transitioned_status == "candidate_applied"
    assert transitioned_applied["policy_mutations"] == candidate["policy_mutations"]
    assert (
        transitioned_applied["profiles"]["kakao_morning"]["policy"]["target_ticks"] == 4
    )
    assert validate_applied(transitioned_applied, target_date=date(2026, 8, 22)) == (
        True,
        "valid",
    )

    legacy_universe_candidate = json.loads(json.dumps(candidate))
    legacy_universe_candidate["schema"] = "low_price_two_leg_policy_candidate_v1"
    legacy_universe_candidate["source_date"] = "2026-08-11"
    legacy_universe_candidate["profiles"] = {
        profile_id: legacy_universe_candidate["profiles"][profile_id]
        for profile_id in {
            "samsung_heavy_midday",
            "samsung_heavy_afternoon",
            "sk_eternix_midday",
        }
    }
    for profile_id, item in legacy_universe_candidate["profiles"].items():
        item["policy"] = dict(PRE_RECOMMENDATION_BASELINE_POLICIES[profile_id])
    legacy_universe_candidate["profiles"][target]["policy"][
        "rolling_high_drawdown_pct"
    ] = 1.0
    legacy_universe_candidate["policy_hash"] = policy_hash(
        {
            profile_id: item["policy"]
            for profile_id, item in legacy_universe_candidate["profiles"].items()
        }
    )
    assert validate_candidate(legacy_universe_candidate) == (True, "valid")
    legacy_dir = tmp_path / "legacy_universe"
    legacy_dir.mkdir()
    (legacy_dir / "low_price_two_leg_policy_candidate_2026-08-11.json").write_text(
        json.dumps(legacy_universe_candidate), encoding="utf-8"
    )
    migrated, migrated_status = build_applied_policy(
        target_date=date(2026, 8, 12), candidate_dir=legacy_dir
    )
    assert migrated_status == "candidate_applied"
    assert set(migrated["profiles"]) == set(PRE_RECOMMENDATION_PROFILES)
    assert migrated["profiles"]["mirae_asset_morning"]["policy"] == (
        PRE_RECOMMENDATION_BASELINE_POLICIES["mirae_asset_morning"]
    )

    pre_expanded_v2 = json.loads(json.dumps(candidate))
    pre_expanded_v2["source_date"] = "2026-08-12"
    pre_expanded_v2["profiles"] = {
        profile_id: pre_expanded_v2["profiles"][profile_id]
        for profile_id in {
            "samsung_heavy_midday",
            "samsung_heavy_afternoon",
            "sk_eternix_midday",
            "mirae_asset_morning",
            "jeju_semiconductor_morning",
            "doosan_enerbility_morning",
            "hanwha_ocean_late_morning",
        }
    }
    for profile_id, item in pre_expanded_v2["profiles"].items():
        item["policy"] = dict(PRE_RECOMMENDATION_BASELINE_POLICIES[profile_id])
    pre_expanded_v2["profiles"][target]["policy"]["rolling_high_drawdown_pct"] = 1.0
    pre_expanded_v2["policy_hash"] = policy_hash(
        {
            profile_id: item["policy"]
            for profile_id, item in pre_expanded_v2["profiles"].items()
        }
    )
    assert validate_candidate(pre_expanded_v2) == (True, "valid")
    pre_expanded_dir = tmp_path / "pre_expanded_v2"
    pre_expanded_dir.mkdir()
    (
        pre_expanded_dir / "low_price_two_leg_policy_candidate_2026-08-12.json"
    ).write_text(json.dumps(pre_expanded_v2), encoding="utf-8")
    expanded_applied, expanded_status = build_applied_policy(
        target_date=date(2026, 8, 13), candidate_dir=pre_expanded_dir
    )
    assert expanded_status == "candidate_applied"
    assert set(expanded_applied["profiles"]) == set(PRE_RECOMMENDATION_PROFILES)
    assert expanded_applied["profiles"]["kakao_morning"]["policy"] == (
        PRE_RECOMMENDATION_BASELINE_POLICIES["kakao_morning"]
    )

    source_gap_report = json.loads(json.dumps(report))
    source_gap_report["daily"]["profiles"][target]["source_quality"] = "gap"
    source_gap_candidate = build_candidate(
        source_gap_report,
        candidate_dir=tmp_path / "low_price_source_gap",
        samsung_candidate_dir=tmp_path / "samsung_source_gap",
    )
    assert source_gap_candidate["policy_mutations"] == []

    samsung_dir = tmp_path / "samsung_blocked"
    samsung_dir.mkdir()
    (samsung_dir / "samsung_machine_entry_policy_candidate_2026-08-21.json").write_text(
        "{}", encoding="utf-8"
    )
    blocked = build_candidate(
        report,
        candidate_dir=tmp_path / "low_price_blocked",
        samsung_candidate_dir=samsung_dir,
    )
    assert blocked["policy_mutations"] == []
    assert blocked["same_stage_owner_guard"]["mutation_present"] is True


def test_profile_inventory_blocks_tuning_even_when_held_row_has_no_axis_features(
    tmp_path,
):
    from src.engine.monitoring.low_price_two_leg_tuning import _aggregate

    target = "samsung_heavy_midday"
    rows = [_tuning_row(target, index, strong=index % 2 == 0) for index in range(20)]
    held = _tuning_row(target, 20, strong=True)
    held["eligible_for_tuning"] = False
    held["source_quality"] = "gap"
    held["source_quality_reasons"] = ["signal_feature_profile_contract_mismatch"]
    held["signal_features"] = {}
    for leg in held["legs"]:
        leg.update(
            {
                "status": "HELD",
                "completed": False,
                "held": True,
                "terminal": False,
                "net_profit_pct": None,
            }
        )
    rows.append(held)
    windows = {CLEAN_WINDOW_NAME: {}}
    for profile_id in PROFILES:
        profile_rows = rows if profile_id == target else []
        windows[CLEAN_WINDOW_NAME][profile_id] = {
            "summary": _aggregate(profile_rows),
            "rows": profile_rows,
        }
    candidate = build_candidate(
        {
            "target_date": "2026-08-11",
            "generated_at_kst": "2026-08-11T20:10:00+09:00",
            "clean_tuning_baseline_date": "2026-06-05",
            "target_date_is_krx_trading_day": True,
            "source_quality_preflight": {"tuning_input_allowed": True},
            "daily": {
                "profiles": {
                    profile_id: {"source_quality": "pass"} for profile_id in PROFILES
                }
            },
            "windows": windows,
        },
        candidate_dir=tmp_path / "low_price",
        samsung_candidate_dir=tmp_path / "samsung",
    )

    assert candidate["policy_mutations"] == []
    assert (
        candidate["profiles"][target]["evaluation"]["profile_inventory_clear"] is False
    )


def _write_source_quality_audit(directory: Path, target_date: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"observation_source_quality_audit_{target_date}.json").write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )


def _write_carried_state(
    directory: Path, profile_id: str, source_date: str, *, held: bool
) -> None:
    profile = PROFILES[profile_id]
    status = "HELD" if held else "COMPLETE"
    directory.mkdir(parents=True, exist_ok=True)
    legs = []
    for plan in profile.policy.entry_legs(20_000):
        leg_id = plan["leg_id"]
        fill_price = plan["entry_price"]
        legs.append(
            {
                "leg_id": leg_id,
                "quantity": 1,
                "status": status,
                "entry_price": fill_price,
                "fill_price": fill_price,
                "target_price": profile.policy.target_price(fill_price),
                "position_qty": 1 if held else 0,
                "target_filled_qty": 0 if held else 1,
            }
        )
    (directory / f"{profile_id}_state.json").write_text(
        json.dumps(
            {
                "schema": f"low_price_two_leg_{profile_id}_state_v1",
                "trade_date": source_date,
                "status": status,
                "attempt_consumed": True,
                "signal_features": {
                    "schema": "regular_two_leg_entry_signal_features_v1",
                    "strategy": profile_id,
                    "symbol": profile.symbol,
                    "observed_drawdown_pct": 1.6,
                    "observed_near_low_pct": 0.1,
                    "signal_close": 20_000,
                },
                "legs": legs,
            }
        ),
        encoding="utf-8",
    )


def test_prior_episode_completion_is_reconciled_to_original_profile_date(tmp_path):
    profile_id = "samsung_heavy_midday"
    state_dir = tmp_path / "states"
    source_quality_dir = tmp_path / "source_quality"
    _write_carried_state(state_dir, profile_id, "2026-08-10", held=False)
    _write_source_quality_audit(source_quality_dir, "2026-08-10")
    _write_source_quality_audit(source_quality_dir, "2026-08-11")

    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
    )

    reconciliation = report["prior_state_reconciliations"][profile_id]
    assert reconciliation["source_date"] == "2026-08-10"
    assert reconciliation["state_status"] == "COMPLETE"
    summary = report["windows"][CLEAN_WINDOW_NAME][profile_id]["summary"]
    assert summary["completed_legs"] == 2
    assert summary["held_or_unresolved_legs"] == 0
    assert report["daily"]["profiles"][profile_id]["attempted"] is False


def test_actual_leg_lifecycle_timing_and_gross_diagnostics_are_preserved(tmp_path):
    profile_id = "samsung_heavy_midday"
    state_dir = tmp_path / "states"
    source_quality_dir = tmp_path / "source_quality"
    _write_carried_state(state_dir, profile_id, "2026-08-11", held=False)
    state_path = state_dir / f"{profile_id}_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    durations = (30, 300)
    for leg, duration in zip(state["legs"], durations, strict=True):
        leg["buy_filled_at"] = "2026-08-11T13:00:00+09:00"
        leg["target_filled_at"] = (
            datetime(2026, 8, 11, 13, 0, tzinfo=KST) + timedelta(seconds=duration)
        ).isoformat()
        leg["target_fill_price"] = leg["target_price"]
    state_path.write_text(json.dumps(state), encoding="utf-8")
    _write_source_quality_audit(source_quality_dir, "2026-08-11")

    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
        machine_microstructure_report_dir=tmp_path / "micro",
    )

    legs = report["daily"]["profiles"][profile_id]["legs"]
    assert [leg["holding_duration_sec"] for leg in legs] == [30.0, 300.0]
    assert all(leg["gross_no_slippage_return_pct"] is not None for leg in legs)
    summary = report["windows"][CLEAN_WINDOW_NAME][profile_id]["summary"]
    assert summary["completed_legs_with_lifecycle_timing"] == 2
    assert summary["median_reconciliation_confirmed_holding_duration_sec"] == 165.0
    assert summary["p90_reconciliation_confirmed_holding_duration_sec"] == 300.0
    assert summary["target_reconciliation_completion_within_180s_ratio"] == 0.5
    assert summary["broker_completed_capital_occupied_krw_seconds"] > 0
    assert summary["broker_completed_net_return_per_capital_hour"] > 0


def test_verified_manual_stop_loss_is_negative_ev_not_target_speed_success():
    from src.engine.monitoring.low_price_two_leg_tuning import (
        _aggregate,
        _sanitize_leg,
    )

    manual_leg = _sanitize_leg(
        {
            "leg_id": "signal_close",
            "quantity": 10,
            "status": "COMPLETE",
            "entry_price": 71_500,
            "fill_price": 71_500,
            "target_price": 71_900,
            "position_qty": 0,
            "buy_filled_qty": 10,
            "target_filled_qty": 10,
            "target_fill_price": 69_900,
            "buy_filled_at": "2026-08-28T14:00:00+09:00",
            "target_filled_at": "2026-08-28T14:00:30+09:00",
            "exit_fill_source": "broker_verified_manual_sell_receipt",
            "manual_exit_receipt": {"order_date": "2026-08-28"},
        },
        DEFAULT_ROUND_TRIP_COST_PCT,
    )
    target_leg = _sanitize_leg(
        {
            "leg_id": "signal_close_minus_1tick",
            "quantity": 10,
            "status": "COMPLETE",
            "entry_price": 71_400,
            "fill_price": 71_400,
            "target_price": 71_800,
            "position_qty": 0,
            "buy_filled_qty": 10,
            "target_filled_qty": 10,
            "target_fill_price": 71_800,
            "buy_filled_at": "2026-08-28T14:00:00+09:00",
            "target_filled_at": "2026-08-28T14:05:00+09:00",
        },
        DEFAULT_ROUND_TRIP_COST_PCT,
    )
    row = {
        "eligible_for_tuning": True,
        "attempted": True,
        "legs": [manual_leg, target_leg],
    }

    summary = _aggregate([row])

    assert manual_leg["exit_execution_class"] == "manual_operator_exit"
    assert manual_leg["manual_exit_realized"] is True
    assert manual_leg["autonomous_target_filled"] is False
    assert manual_leg["realized_loss"] is True
    assert manual_leg["net_profit_pct"] < 0
    assert summary["manual_exit_completed_legs"] == 1
    assert summary["manual_exit_loss_legs"] == 1
    assert summary["machine_target_completed_legs"] == 1
    assert summary["manual_exit_fixed_cost_estimate_net_profit_krw"] < 0
    assert summary["broker_realized_net_profit_krw"] < 0
    assert summary["target_reconciliation_completion_within_180s_count"] == 0
    assert summary["target_reconciliation_completion_within_180s_ratio"] == 0.0


def test_clean_window_loads_legacy_report_and_does_not_impute_missing_dates(tmp_path):
    profile_id = "samsung_heavy_midday"
    state_dir = tmp_path / "states"
    report_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source_quality"
    _write_carried_state(state_dir, profile_id, "2026-08-10", held=False)
    _write_source_quality_audit(source_quality_dir, "2026-08-10")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=report_dir,
        source_quality_dir=source_quality_dir,
    )
    first["schema"] = "low_price_two_leg_tuning_report_v1"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "low_price_two_leg_tuning_2026-08-10.json").write_text(
        json.dumps(first), encoding="utf-8"
    )

    _write_carried_state(state_dir, profile_id, "2026-08-11", held=False)
    _write_source_quality_audit(source_quality_dir, "2026-08-11")
    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=report_dir,
        source_quality_dir=source_quality_dir,
    )

    assert second["schema"] == REPORT_SCHEMA
    assert set(second["windows"]) == {CLEAN_WINDOW_NAME}
    coverage = second["clean_baseline_window"]
    assert coverage["available_actual_observation_dates"] == [
        "2026-08-10",
        "2026-08-11",
    ]
    assert coverage["available_actual_observation_date_count"] == 2
    assert coverage["unobserved_trading_date_count"] > 0
    assert coverage["unobserved_dates_block_candidate"] is False
    assert coverage["candidate_window_uses_only_available_actual_observations"] is True
    assert coverage["missing_dates_imputed_as_outcomes"] is False
    assert coverage["historical_market_replay_included"] is False
    summary = second["windows"][CLEAN_WINDOW_NAME][profile_id]["summary"]
    assert summary["eligible_days"] == 2
    assert summary["completed_legs"] == 4


def test_profile_expansion_dates_do_not_create_historical_source_gaps(tmp_path):
    report_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source_quality"
    report_dir.mkdir()
    assert set(PROFILE_FIRST_OPERATIONAL_DATES) == set(PROFILES)

    def missing_row(profile_id: str, target_date: str) -> dict:
        return {
            "profile_id": profile_id,
            "target_date": target_date,
            "source_quality": "gap",
            "source_quality_reasons": ["state_missing_or_invalid"],
            "eligible_for_tuning": False,
            "attempted": False,
            "no_signal": False,
            "state_status": "UNKNOWN",
            "signal_features": {},
            "legs": [],
        }

    for target_date, profile_ids in (
        (
            "2026-08-11",
            {
                "samsung_heavy_midday",
                "samsung_heavy_afternoon",
                "sk_eternix_midday",
            },
        ),
        ("2026-08-12", set(PRE_RECOMMENDATION_PROFILES)),
    ):
        payload = {
            "report_type": "low_price_two_leg_tuning",
            "schema": REPORT_SCHEMA,
            "target_date": target_date,
            "clean_tuning_baseline_date": "2026-06-05",
            "cost_pct": 0.20,
            "daily": {
                "profiles": {
                    profile_id: missing_row(profile_id, target_date)
                    for profile_id in profile_ids
                }
            },
        }
        (report_dir / f"low_price_two_leg_tuning_{target_date}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    _write_source_quality_audit(source_quality_dir, "2026-08-13")
    report = build_report(
        target_date="2026-08-13",
        state_dir=tmp_path / "states",
        output_dir=report_dir,
        source_quality_dir=source_quality_dir,
    )

    new_profile_rows = report["windows"][CLEAN_WINDOW_NAME]["kakao_morning"]["rows"]
    assert [row.get("cohort") for row in new_profile_rows[:2]] == [
        "pre_operational_not_applicable",
        "pre_operational_not_applicable",
    ]
    new_profile_summary = report["windows"][CLEAN_WINDOW_NAME]["kakao_morning"][
        "summary"
    ]
    assert new_profile_summary["pre_operational_days"] == 2
    assert new_profile_summary["source_gap_days"] == 1

    initial_profile_summary = report["windows"][CLEAN_WINDOW_NAME][
        "samsung_heavy_midday"
    ]["summary"]
    assert initial_profile_summary["pre_operational_days"] == 1
    assert initial_profile_summary["source_gap_days"] == 2


def test_prior_report_cost_is_rebased_from_fill_prices_without_losing_history(tmp_path):
    profile_id = "samsung_heavy_midday"
    state_dir = tmp_path / "states"
    report_dir = tmp_path / "reports"
    source_quality_dir = tmp_path / "source_quality"
    _write_carried_state(state_dir, profile_id, "2026-08-10", held=False)
    _write_source_quality_audit(source_quality_dir, "2026-08-10")
    first = build_report(
        target_date="2026-08-10",
        state_dir=state_dir,
        output_dir=report_dir,
        source_quality_dir=source_quality_dir,
    )
    first["cost_pct"] = 0.10
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "low_price_two_leg_tuning_2026-08-10.json").write_text(
        json.dumps(first), encoding="utf-8"
    )

    _write_carried_state(state_dir, profile_id, "2026-08-11", held=False)
    _write_source_quality_audit(source_quality_dir, "2026-08-11")
    second = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=report_dir,
        source_quality_dir=source_quality_dir,
    )

    profile_window = second["windows"][CLEAN_WINDOW_NAME][profile_id]
    summary = profile_window["summary"]
    assert summary["source_gap_days"] == 0
    assert summary["eligible_days"] == 2
    assert summary["completed_legs"] == 4
    historical_legs = profile_window["rows"][0]["legs"]
    expected = round(
        (historical_legs[0]["target_price"] / historical_legs[0]["fill_price"] - 1)
        * 100
        - DEFAULT_ROUND_TRIP_COST_PCT,
        6,
    )
    assert historical_legs[0]["net_profit_pct"] == expected


def test_nontrading_target_is_excluded_and_cannot_open_candidate(tmp_path):
    report = build_report(
        target_date="2026-08-09",
        state_dir=tmp_path / "states",
        output_dir=tmp_path / "reports",
        source_quality_dir=tmp_path / "source_quality",
    )
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "candidates",
        samsung_candidate_dir=tmp_path / "samsung_candidates",
    )

    assert report["target_date_is_krx_trading_day"] is False
    assert (
        "2026-08-09"
        not in report["clean_baseline_window"]["available_actual_observation_dates"]
    )
    assert candidate["policy_mutations"] == []


def test_prior_microstructure_diagnostic_is_consumed_without_candidate_effect(
    tmp_path,
):
    micro_dir = tmp_path / "machine_micro"
    micro_dir.mkdir()
    profile_id = "samsung_heavy_midday"
    (micro_dir / "machine_microstructure_attribution_2026-08-13.json").write_text(
        json.dumps(
            {
                "schema": "machine_microstructure_attribution_v1",
                "target_date": "2026-08-13",
                "status": "warning",
                "authority": {
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                "consumers": {
                    "episode_machine_postclose_tuning": {
                        "profiles": {
                            profile_id: {
                                "micro_context_status": "matched",
                                "anchor_results": [
                                    {"anchor_role": "episode_signal_bar"}
                                ],
                            }
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    common = {
        "target_date": "2026-08-14",
        "state_dir": tmp_path / "states",
        "output_dir": tmp_path / "reports",
        "source_quality_dir": tmp_path / "source_quality",
    }
    loaded = build_report(
        **common,
        machine_microstructure_report_dir=micro_dir,
    )
    missing = build_report(
        **common,
        machine_microstructure_report_dir=tmp_path / "missing_micro",
    )

    diagnostic = loaded["daily"]["profiles"][profile_id][
        "microstructure_prior_trading_day_diagnostic"
    ]
    assert diagnostic["status"] == "loaded"
    assert diagnostic["source_date"] == "2026-08-13"
    assert diagnostic["selection_effect"] is False
    assert diagnostic["payload"]["micro_context_status"] == "matched"
    assert (
        missing["daily"]["profiles"][profile_id][
            "microstructure_prior_trading_day_diagnostic"
        ]["status"]
        == "missing"
    )

    loaded_candidate = build_candidate(
        loaded,
        candidate_dir=tmp_path / "loaded_candidates",
        samsung_candidate_dir=tmp_path / "samsung_candidates",
    )
    missing_candidate = build_candidate(
        missing,
        candidate_dir=tmp_path / "missing_candidates",
        samsung_candidate_dir=tmp_path / "samsung_candidates",
    )
    assert loaded_candidate["policy_hash"] == missing_candidate["policy_hash"]
    assert loaded_candidate["policy_mutations"] == missing_candidate["policy_mutations"]


def test_multi_day_prior_episode_reconciliation_loads_exact_source_date_diagnostic(
    tmp_path,
):
    profile_id = "samsung_heavy_midday"
    state_dir = tmp_path / "states"
    source_quality_dir = tmp_path / "source_quality"
    micro_dir = tmp_path / "machine_micro"
    micro_dir.mkdir()
    _write_carried_state(state_dir, profile_id, "2026-08-12", held=False)
    _write_source_quality_audit(source_quality_dir, "2026-08-12")
    _write_source_quality_audit(source_quality_dir, "2026-08-14")
    (micro_dir / "machine_microstructure_attribution_2026-08-12.json").write_text(
        json.dumps(
            {
                "schema": "machine_microstructure_attribution_v1",
                "target_date": "2026-08-12",
                "authority": {
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                "consumers": {
                    "episode_machine_postclose_tuning": {
                        "profiles": {profile_id: {"micro_context_status": "matched"}}
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-08-14",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
        machine_microstructure_report_dir=micro_dir,
    )

    diagnostic = report["prior_state_reconciliations"][profile_id]["row"][
        "microstructure_prior_trading_day_diagnostic"
    ]
    assert diagnostic["status"] == "loaded"
    assert diagnostic["source_date"] == "2026-08-12"
    assert diagnostic["owner_source_date"] == "2026-08-12"
    assert diagnostic["payload"]["micro_context_status"] == "matched"


def test_prior_held_episode_blocks_only_its_own_profile_tuning(tmp_path):
    profile_id = "sk_eternix_midday"
    state_dir = tmp_path / "states"
    source_quality_dir = tmp_path / "source_quality"
    _write_carried_state(state_dir, profile_id, "2026-08-10", held=True)
    _write_source_quality_audit(source_quality_dir, "2026-08-10")
    _write_source_quality_audit(source_quality_dir, "2026-08-11")

    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
    )

    summary = report["windows"][CLEAN_WINDOW_NAME][profile_id]["summary"]
    row = report["prior_state_reconciliations"][profile_id]["row"]
    assert row["source_quality"] == "pass"
    assert row["eligible_for_tuning"] is False
    assert row["outcome_complete_for_ev"] is False
    assert row["outcome_exclusion_reasons"] == ["held_or_unresolved_inventory"]
    assert summary["completed_legs"] == 0
    assert summary["held_or_unresolved_legs"] == 2
    for other_profile in set(report["windows"][CLEAN_WINDOW_NAME]) - {profile_id}:
        other = report["windows"][CLEAN_WINDOW_NAME][other_profile]["summary"]
        assert other["held_or_unresolved_legs"] == 0


def test_historical_held_reason_is_outcome_exclusion_not_source_gap() -> None:
    profile_id = "sk_eternix_midday"
    row = {
        "attempted": True,
        "eligible_for_tuning": False,
        "source_quality": "gap",
        "source_quality_reasons": ["held_or_unresolved_inventory"],
        "legs": [
            {"status": "COMPLETE", "completed": True, "net_profit_pct": 0.1},
            {"status": "HELD", "completed": False, "terminal": False},
        ],
    }

    normalized = _historical_profile_row(
        profile_id, date(2026, 8, 13), {profile_id: row}, 0.23
    )

    assert normalized["source_quality"] == "pass"
    assert normalized["source_quality_reasons"] == []
    assert normalized["eligible_for_tuning"] is False
    assert normalized["outcome_complete_for_ev"] is False


def test_contradictory_complete_receipt_is_quarantined(tmp_path):
    profile_id = "samsung_heavy_afternoon"
    state_dir = tmp_path / "states"
    source_quality_dir = tmp_path / "source_quality"
    _write_carried_state(state_dir, profile_id, "2026-08-11", held=False)
    state_path = state_dir / f"{profile_id}_state.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["legs"][0]["position_qty"] = 1
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    _write_source_quality_audit(source_quality_dir, "2026-08-11")

    report = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports",
        source_quality_dir=source_quality_dir,
    )

    row = report["daily"]["profiles"][profile_id]
    assert row["eligible_for_tuning"] is False
    assert "leg_execution_contract_invalid" in row["source_quality_reasons"]

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["legs"][0]["position_qty"] = 0
    payload["legs"][0]["target_fill_price"] = payload["legs"][0]["target_price"] - 50
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    below_limit = build_report(
        target_date="2026-08-11",
        state_dir=state_dir,
        output_dir=tmp_path / "reports-below-limit",
        source_quality_dir=source_quality_dir,
    )["daily"]["profiles"][profile_id]
    assert "leg_execution_contract_invalid" in below_limit["source_quality_reasons"]
