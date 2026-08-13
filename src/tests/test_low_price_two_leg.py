from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.engine.monitoring.low_price_two_leg_tuning import (
    CLEAN_WINDOW_NAME,
    PROFILE_FIRST_OPERATIONAL_DATES,
    REPORT_SCHEMA,
    build_candidate,
    build_report,
    extract_profile_row,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import candidate_grid
from src.trading.low_price_two_leg.gateway import (
    ExecutionSnapshot,
    KiwoomLowPriceTwoLegGateway,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.low_price_two_leg.machine import LowPriceTwoLegMachine
from src.trading.low_price_two_leg.policy_runtime import (
    BASELINE_POLICIES,
    KAKAO_MORNING_TARGET_TRANSITION,
    POLICY_BOUNDS,
    apply_operator_policy_transitions,
    atomic_write_json,
    load_applied_profile_policy,
    policy_hash,
    validate_applied,
    validate_candidate,
)
from src.trading.low_price_two_leg.preflight import (
    build_authority_artifact,
    evaluate_preflight,
    validate_research_evidence,
)
from src.trading.low_price_two_leg.profiles import (
    AFTERNOON_WINDOW,
    DOOSAN_ENERBILITY_MORNING_WINDOW,
    HANWHA_OCEAN_LATE_MORNING_WINDOW,
    JEJU_SEMICONDUCTOR_MORNING_WINDOW,
    KAKAO_LATE_MORNING_WINDOW,
    KAKAO_MORNING_WINDOW,
    KEPCO_AFTERNOON_WINDOW,
    MIRAE_ASSET_MIDDAY_WINDOW,
    MIRAE_ASSET_MORNING_WINDOW,
    PROFILES,
    SAMSUNG_HEAVY_MIDDAY_WINDOW,
    SK_ETERNIX_MIDDAY_WINDOW,
    SK_ETERNIX_MORNING_WINDOW,
    MinuteBar,
)
from src.trading.low_price_two_leg.service import _profile_with_applied_policy
from src.trading.order.regular_two_leg_machine import KST
from src.trading.order.tick_utils import move_price_by_ticks


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


class FakeGateway:
    def __init__(self, profile_id: str) -> None:
        self.bars = _signal_bars(profile_id)
        self.buy_calls: list[int] = []
        self.sell_calls: list[int] = []
        self.cancel_calls: list[str] = []
        self.snapshots: dict[str, ExecutionSnapshot] = {}
        self.sequence = 0

    def completed_sor_minute_bars(self, *, trade_date, now):
        return MinuteBarsSnapshot(True, self.bars)

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


def test_profiles_are_exact_eight_symbols_and_thirteen_independent_sessions():
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
    }
    assert PROFILES["samsung_heavy_midday"].policy.lookback_bars == 30
    assert PROFILES["samsung_heavy_midday"].policy.rolling_high_drawdown_pct == 0.75
    assert PROFILES["samsung_heavy_midday"].policy.rolling_low_proximity_pct == 0.35
    assert PROFILES["sk_eternix_midday"].policy.lookback_bars == 20
    assert PROFILES["sk_eternix_midday"].policy.rolling_high_drawdown_pct == 2.0
    assert PROFILES["sk_eternix_midday"].policy.rolling_low_proximity_pct == 0.75
    assert POLICY_BOUNDS["samsung_heavy_midday"] == {
        "drawdown_min": 0.75,
        "drawdown_max": 1.0,
        "near_low_min": 0.25,
        "near_low_max": 0.35,
    }
    assert POLICY_BOUNDS["sk_eternix_midday"] == {
        "drawdown_min": 2.0,
        "drawdown_max": 2.25,
        "near_low_min": 0.65,
        "near_low_max": 0.75,
    }
    assert all(item.policy.quantity == 20 for item in PROFILES.values())
    assert PROFILES["mirae_asset_morning"].policy.entry_offsets_ticks == (-1, -2)
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
        "kakao_morning": (15, 0.75, 0.35, (0, -1), 5, 2),
        "kepco_afternoon": (60, 0.50, 0.75, (0, -1), 5, 2),
        "kakao_late_morning": (15, 0.50, 0.35, (0, -1), 5, 2),
        "sk_eternix_morning": (15, 1.50, 0.75, (0, -1), 5, 2),
        "mirae_asset_midday": (45, 1.00, 0.50, (0, -1), 5, 2),
        "sk_eternix_afternoon": (45, 2.50, 0.50, (0, -1), 5, 2),
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


@pytest.mark.parametrize(
    ("profile_id", "preflight_time", "service_time"),
    [
        ("kakao_morning", "09:15:00", "09:19:00"),
        ("kakao_late_morning", "10:00:00", "10:04:00"),
        ("sk_eternix_morning", "09:45:00", "09:49:00"),
        ("mirae_asset_midday", "13:10:00", "13:14:00"),
        ("kepco_afternoon", "13:55:00", "13:59:00"),
        ("sk_eternix_afternoon", "13:55:00", "13:59:00"),
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


def test_current_profile_symbols_have_explicit_manual_ownership():
    install_script = (
        Path(__file__).resolve().parents[2]
        / "deploy"
        / "install_low_price_two_leg_systemd.sh"
    ).read_text(encoding="utf-8")
    install_time_symbols = {"015760", "035720"}
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


def test_mirae_machine_uses_user_approved_minus_one_minus_two_split(tmp_path):
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
    assert gateway.buy_calls == [22_600, 22_550]
    assert [leg["leg_id"] for leg in state["legs"]] == [
        "signal_close_minus_1tick",
        "signal_close_minus_2ticks",
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


def test_research_evidence_gate_validates_each_selected_profile(tmp_path):
    assert all(validate_research_evidence(profile)[0] for profile in PROFILES.values())
    profiles = {}
    source_meta = {}
    legacy_profiles = [
        PROFILES["samsung_heavy_midday"],
        PROFILES["samsung_heavy_afternoon"],
        PROFILES["sk_eternix_midday"],
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
        validate_research_evidence(profile, path, expected_sha256=digest)[0]
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
    profile = PROFILES[profile_id]
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
        applied_policy=BASELINE_POLICIES[profile_id],
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
    profile = PROFILES[profile_id]
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
        applied_policy=BASELINE_POLICIES[profile_id],
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
    profile = PROFILES["kakao_morning"]
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
        PROFILES["kakao_morning"], path, expected_sha256=digest
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
    source = Path(
        "data/threshold_cycle/low_price_two_leg/candidates/"
        "low_price_two_leg_policy_candidate_2026-08-12.json"
    )
    legacy = json.loads(source.read_text(encoding="utf-8"))
    assert all(item["policy"]["quantity"] == 2 for item in legacy["profiles"].values())
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / source.name).write_text(json.dumps(legacy), encoding="utf-8")

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
        BASELINE_POLICIES, target_date=date(2026, 8, 14)
    )
    profile = _profile_with_applied_policy(
        PROFILES["kakao_morning"], transitioned["kakao_morning"], "HASH"
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
    for profile_id in PROFILES:
        profile_rows = rows if profile_id == target else []
        windows[CLEAN_WINDOW_NAME][profile_id] = {
            "summary": _aggregate(profile_rows),
            "rows": profile_rows,
        }
    report = {
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
        item["policy"] == BASELINE_POLICIES[profile_id]
        for profile_id, item in candidate["profiles"].items()
        if profile_id != target
    )
    transition_dir = tmp_path / "target_transition"
    transition_dir.mkdir()
    (transition_dir / "low_price_two_leg_policy_candidate_2026-08-11.json").write_text(
        json.dumps(candidate), encoding="utf-8"
    )
    transitioned_applied, transitioned_status = build_applied_policy(
        target_date=date(2026, 8, 14), candidate_dir=transition_dir
    )
    assert transitioned_status == "candidate_applied"
    assert transitioned_applied["policy_mutations"] == candidate["policy_mutations"]
    assert (
        transitioned_applied["profiles"]["kakao_morning"]["policy"]["target_ticks"] == 3
    )
    assert validate_applied(transitioned_applied, target_date=date(2026, 8, 14)) == (
        True,
        "valid",
    )

    legacy_universe_candidate = json.loads(json.dumps(candidate))
    legacy_universe_candidate["schema"] = "low_price_two_leg_policy_candidate_v1"
    legacy_universe_candidate["profiles"] = {
        profile_id: legacy_universe_candidate["profiles"][profile_id]
        for profile_id in {
            "samsung_heavy_midday",
            "samsung_heavy_afternoon",
            "sk_eternix_midday",
        }
    }
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
    assert set(migrated["profiles"]) == set(PROFILES)
    assert migrated["profiles"]["mirae_asset_morning"]["policy"] == (
        BASELINE_POLICIES["mirae_asset_morning"]
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
    assert set(expanded_applied["profiles"]) == set(PROFILES)
    assert expanded_applied["profiles"]["kakao_morning"]["policy"] == (
        BASELINE_POLICIES["kakao_morning"]
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
    (samsung_dir / "samsung_machine_entry_policy_candidate_2026-08-11.json").write_text(
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
        ("2026-08-12", set(PROFILES)),
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


def test_prior_report_cost_contract_mismatch_is_excluded(tmp_path):
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

    summary = second["windows"][CLEAN_WINDOW_NAME][profile_id]["summary"]
    assert summary["source_gap_days"] == 1
    assert summary["eligible_days"] == 1
    assert summary["completed_legs"] == 2


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
    assert summary["completed_legs"] == 0
    assert summary["held_or_unresolved_legs"] == 2
    for other_profile in set(PROFILES) - {profile_id}:
        other = report["windows"][CLEAN_WINDOW_NAME][other_profile]["summary"]
        assert other["held_or_unresolved_legs"] == 0


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
