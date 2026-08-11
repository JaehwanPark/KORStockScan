from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.engine.monitoring.low_price_two_leg_tuning import (
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
    validate_applied,
    validate_candidate,
)
from src.trading.low_price_two_leg.preflight import (
    evaluate_preflight,
    validate_research_evidence,
)
from src.trading.low_price_two_leg.profiles import (
    AFTERNOON_WINDOW,
    PROFILES,
    SAMSUNG_HEAVY_MIDDAY_WINDOW,
    SK_ETERNIX_MIDDAY_WINDOW,
    MinuteBar,
)
from src.trading.order.regular_two_leg_machine import KST


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


def test_profiles_are_exact_two_symbols_and_three_independent_sessions():
    assert {key: (item.symbol, item.session) for key, item in PROFILES.items()} == {
        "samsung_heavy_midday": ("010140", "midday"),
        "samsung_heavy_afternoon": ("010140", "afternoon"),
        "sk_eternix_midday": ("475150", "midday"),
    }
    assert {
        (item.policy.scan_start, item.policy.scan_last_bar)
        for item in PROFILES.values()
    } == {
        SAMSUNG_HEAVY_MIDDAY_WINDOW,
        AFTERNOON_WINDOW,
        SK_ETERNIX_MIDDAY_WINDOW,
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
    assert all(item.policy.target_ticks == 2 for item in PROFILES.values())
    assert all(
        item.policy.entry_valid_completed_bars == 5 for item in PROFILES.values()
    )


@pytest.mark.parametrize("profile_id", sorted(PROFILES))
def test_each_profile_uses_same_two_leg_signal_contract(profile_id):
    policy = PROFILES[profile_id].policy
    signal = policy.evaluate(list(_signal_bars(profile_id)))
    assert signal is not None
    assert signal.drawdown_pct > policy.rolling_high_drawdown_pct
    assert signal.near_low_pct == 0.0
    assert [leg["entry_price"] for leg in policy.entry_legs(22_650)] == [
        22_650,
        22_600,
    ]
    assert policy.target_price(22_650) == 22_750


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
    profiles = {}
    source_meta = {}
    for profile in PROFILES.values():
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
        for profile in PROFILES.values()
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
            for leg_id in ("signal_close", "signal_close_minus_1tick")
        ],
    }


def test_tuning_keeps_profiles_separate_and_selects_only_one_axis(tmp_path):
    from src.engine.monitoring.low_price_two_leg_tuning import _aggregate

    target = "samsung_heavy_midday"
    rows = [_tuning_row(target, index, strong=index % 2 == 0) for index in range(20)]
    windows = {}
    for window in ("rolling10", "rolling20", "cumulative"):
        windows[window] = {}
        for profile_id in PROFILES:
            profile_rows = rows if profile_id == target else []
            windows[window][profile_id] = {
                "summary": _aggregate(profile_rows),
                "rows": profile_rows,
            }
    report = {
        "target_date": "2026-08-11",
        "generated_at_kst": "2026-08-11T20:10:00+09:00",
        "clean_tuning_baseline_date": "2026-06-05",
        "source_quality_preflight": {"tuning_input_allowed": True},
        "windows": windows,
    }
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "low_price",
        samsung_candidate_dir=tmp_path / "samsung",
    )
    assert validate_candidate(candidate)[0]
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
    windows = {}
    for window in ("rolling10", "rolling20", "cumulative"):
        windows[window] = {}
        for profile_id in PROFILES:
            profile_rows = rows if profile_id == target else []
            windows[window][profile_id] = {
                "summary": _aggregate(profile_rows),
                "rows": profile_rows,
            }
    candidate = build_candidate(
        {
            "target_date": "2026-08-11",
            "generated_at_kst": "2026-08-11T20:10:00+09:00",
            "clean_tuning_baseline_date": "2026-06-05",
            "source_quality_preflight": {"tuning_input_allowed": True},
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
    for leg_id, fill_price in (
        ("signal_close", 20_000),
        ("signal_close_minus_1tick", 19_950),
    ):
        legs.append(
            {
                "leg_id": leg_id,
                "quantity": 1,
                "status": status,
                "entry_price": fill_price,
                "fill_price": fill_price,
                "target_price": fill_price + 100,
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
    summary = report["windows"]["cumulative"][profile_id]["summary"]
    assert summary["completed_legs"] == 2
    assert summary["held_or_unresolved_legs"] == 0
    assert report["daily"]["profiles"][profile_id]["attempted"] is False


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

    summary = report["windows"]["cumulative"][profile_id]["summary"]
    assert summary["completed_legs"] == 0
    assert summary["held_or_unresolved_legs"] == 2
    for other_profile in set(PROFILES) - {profile_id}:
        other = report["windows"]["cumulative"][other_profile]["summary"]
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
