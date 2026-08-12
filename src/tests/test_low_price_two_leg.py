from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.engine.monitoring.low_price_two_leg_tuning import (
    CLEAN_WINDOW_NAME,
    REPORT_SCHEMA,
    build_candidate,
    build_report,
)
from src.trading.low_price_two_leg.gateway import (
    ExecutionSnapshot,
    KiwoomLowPriceTwoLegGateway,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.low_price_two_leg.machine import LowPriceTwoLegMachine
from src.trading.low_price_two_leg.policy_runtime import (
    BASELINE_POLICIES,
    POLICY_BOUNDS,
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
    MIRAE_ASSET_MORNING_WINDOW,
    PROFILES,
    SAMSUNG_HEAVY_MIDDAY_WINDOW,
    SK_ETERNIX_MIDDAY_WINDOW,
    MinuteBar,
)
from src.trading.order.regular_two_leg_machine import KST
from src.trading.order.tick_utils import move_price_by_ticks


def _at(day: int, hour: int, minute: int = 0, second: int = 10) -> datetime:
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


def _signal_bars(profile_id: str, *, through: int = 0) -> tuple[MinuteBar, ...]:
    profile = PROFILES[profile_id]
    latest = datetime.combine(date(2026, 8, 12), profile.policy.scan_start, tzinfo=KST)
    start = latest - timedelta(minutes=29)
    bars = [
        MinuteBar(start + timedelta(minutes=index), 23_500, 23_500, 22_650, 23_500)
        for index in range(29)
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

    def submit_limit_buy(self, *, price):
        self.buy_calls.append(price)
        return self._accepted("B")

    def submit_limit_sell(self, *, price):
        self.sell_calls.append(price)
        return self._accepted("T")

    def cancel_buy(self, *, order_no):
        self.cancel_calls.append(order_no)
        return self._accepted("C")

    def execution_snapshot(self, *, order_no, order_date):
        return self.snapshots.get(order_no, ExecutionSnapshot(True, True, 0, 1, 1))


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


def test_profiles_are_exact_six_symbols_and_seven_independent_sessions():
    assert {key: (item.symbol, item.session) for key, item in PROFILES.items()} == {
        "samsung_heavy_midday": ("010140", "midday"),
        "samsung_heavy_afternoon": ("010140", "afternoon"),
        "sk_eternix_midday": ("475150", "midday"),
        "mirae_asset_morning": ("006800", "morning"),
        "jeju_semiconductor_morning": ("080220", "morning"),
        "doosan_enerbility_morning": ("034020", "morning"),
        "hanwha_ocean_late_morning": ("042660", "late_morning"),
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
    assert all(item.policy.quantity == 2 for item in PROFILES.values())
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
    assert gateway.submit_limit_buy(price=17_000).accepted
    assert gateway.submit_limit_sell(price=17_050).accepted
    assert gateway.cancel_buy(order_no="B1").accepted
    assert [call[1]["headers"]["api-id"] for call in session.calls] == [
        "kt10000",
        "kt10001",
        "kt10003",
    ]
    assert all(call[1]["json"]["stk_cd"] == "475150" for call in session.calls)
    assert all(call[1]["json"].get("dmst_stex_tp") == "SOR" for call in session.calls)
    assert session.calls[0][1]["json"]["ord_qty"] == "1"
    assert session.calls[1][1]["json"]["ord_qty"] == "1"
    assert session.calls[2][1]["json"]["cncl_qty"] == "1"


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
                "completed": True,
                "held": False,
                "terminal": True,
                "net_profit_pct": profit_pct,
            }
            for leg_id in profile.policy.entry_leg_ids
        ],
    }


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
