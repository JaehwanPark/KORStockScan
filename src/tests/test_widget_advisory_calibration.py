from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.monitoring import widget_advisory_calibration as calibration
from src.engine.monitoring.widget_advisory_calibration_policy import (
    POLICY_AUTHORITY,
    POLICY_SCHEMA,
    WidgetCalibrationPolicyLoader,
)

KST = ZoneInfo("Asia/Seoul")


def _spec(tmp_path: Path) -> calibration.WidgetSpec:
    return calibration.WidgetSpec(
        symbol="999999",
        name="테스트",
        strategy_profile="TEST_PROFILE_V1",
        observation_dir=tmp_path / "observations",
        observation_prefix="test_widget_advisory",
        evaluation_dir=tmp_path / "evaluations",
        evaluation_prefix="test_widget_advisory_evaluation",
        expected_sessions={"KRX_REGULAR": 390},
        target_return_pct=1.0,
    )


def _daily_report(target_date: date, *, source_rows: int = 10) -> dict:
    return {
        "schema_version": 2,
        "symbol": "999999",
        "status": "observed",
        "target_date": target_date.isoformat(),
        "source_row_count": source_rows,
        "outcomes": [],
        "target_return_pct": 1.0,
        "fallback_adverse_pct": -0.3,
        "metric_contract": {"decision_authority": "widget_advisory_evaluation_only"},
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _write_daily_with_hits(
    spec: calibration.WidgetSpec,
    target_date: date,
    *,
    target_first: int,
    adverse_first: int,
) -> dict:
    report = _daily_report(target_date)
    report["outcomes"] = [
        {
            "market_session": "KRX_REGULAR",
            "horizon_minutes": 10,
            "evaluation_eligible": True,
            "first_hit": "target_first",
        }
        for _ in range(target_first)
    ] + [
        {
            "market_session": "KRX_REGULAR",
            "horizon_minutes": 10,
            "evaluation_eligible": True,
            "first_hit": "adverse_first",
        }
        for _ in range(adverse_first)
    ]
    spec.evaluation_dir.mkdir(parents=True, exist_ok=True)
    path = spec.evaluation_dir / (
        f"{spec.evaluation_prefix}_{target_date.isoformat()}.json"
    )
    path.write_text(json.dumps(report), encoding="utf-8")
    return report


def _policy_payload(effective_date: date, *, confirmations: int) -> dict:
    return {
        "schema": POLICY_SCHEMA,
        "status": "verified",
        "policy_version": f"policy_{effective_date.isoformat()}",
        "source_target_date": "2026-08-05",
        "effective_date": effective_date.isoformat(),
        "authority": POLICY_AUTHORITY,
        "selected_axis": "required_actionable_confirmations",
        "metric_contract": calibration.CALIBRATION_CONTRACT,
        "widget_runtime_effect": True,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "symbols": {
            "999999": {
                "sessions": {
                    "KRX_REGULAR": {
                        "required_actionable_confirmations": confirmations,
                        "decision": "test",
                        "reason": "test",
                    }
                }
            }
        },
    }


def test_first_cumulative_adverse_outcome_tightens_next_day_policy(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 6)
    daily = _write_daily_with_hits(
        spec,
        target_date,
        target_first=0,
        adverse_first=1,
    )

    policy, report = calibration.build_calibration_policy(
        target_date=target_date,
        daily_reports={spec.symbol: daily},
        policy_dir=tmp_path / "policies",
        specs=(spec,),
    )

    selected = policy["symbols"][spec.symbol]["sessions"]["KRX_REGULAR"]
    assert policy["effective_date"] == "2026-08-07"
    assert selected["required_actionable_confirmations"] == 3
    assert selected["decision"] == "tighten_confirmation"
    assert selected["cumulative_decisive_sample_count"] == 1
    assert report["all_daily_reports_verified"] is True
    assert policy["trading_runtime_effect"] is False


def test_verified_target_dominance_restores_two_confirmations(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 6)
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    previous = _policy_payload(target_date, confirmations=3)
    (policy_dir / f"widget_advisory_policy_{target_date.isoformat()}.json").write_text(
        json.dumps(previous), encoding="utf-8"
    )
    daily = _write_daily_with_hits(
        spec,
        target_date,
        target_first=2,
        adverse_first=0,
    )

    policy, _ = calibration.build_calibration_policy(
        target_date=target_date,
        daily_reports={spec.symbol: daily},
        policy_dir=policy_dir,
        specs=(spec,),
    )

    selected = policy["symbols"][spec.symbol]["sessions"]["KRX_REGULAR"]
    assert selected["previous_required_actionable_confirmations"] == 3
    assert selected["required_actionable_confirmations"] == 2
    assert selected["decision"] == "restore_responsive_confirmation"


def test_confirmation_decision_reports_bound_hold_instead_of_false_change(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 6)
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    previous = _policy_payload(target_date, confirmations=3)
    (policy_dir / f"widget_advisory_policy_{target_date.isoformat()}.json").write_text(
        json.dumps(previous), encoding="utf-8"
    )
    daily = _write_daily_with_hits(
        spec,
        target_date,
        target_first=0,
        adverse_first=1,
    )

    policy, _ = calibration.build_calibration_policy(
        target_date=target_date,
        daily_reports={spec.symbol: daily},
        policy_dir=policy_dir,
        specs=(spec,),
    )

    selected = policy["symbols"][spec.symbol]["sessions"]["KRX_REGULAR"]
    assert selected["required_actionable_confirmations"] == 3
    assert selected["decision"] == "hold_confirmation_at_upper_bound_negative_ev"


def test_adverse_first_recovery_uses_ev_and_keeps_responsive_confirmation(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 6)
    daily = _daily_report(target_date)
    daily["outcomes"] = [
        {
            "market_session": "KRX_REGULAR",
            "horizon_minutes": 10,
            "evaluation_eligible": True,
            "first_hit": "adverse_first",
            "mfe_pct": 1.2,
            "mae_pct": -0.4,
        }
    ]

    policy, _ = calibration.build_calibration_policy(
        target_date=target_date,
        daily_reports={spec.symbol: daily},
        policy_dir=tmp_path / "policies",
        specs=(spec,),
    )

    selected = policy["symbols"][spec.symbol]["sessions"]["KRX_REGULAR"]
    assert selected["required_actionable_confirmations"] == 2
    assert selected["cumulative_adverse_first_recovered_count"] == 1
    assert selected["source_quality_adjusted_ev_pct"] == 0.8


def test_opportunity_cost_resolves_aware_timestamp_in_kst():
    net_return, recovered = calibration._opportunity_net_return_proxy(
        {
            "target_return_pct": 1.0,
            "first_hit": "target_first",
            "entry_touched_at_kst": "2026-08-17T15:30:00+00:00",
        }
    )

    assert recovered is False
    assert net_return == 0.77


def test_daily_report_rejects_nonfinite_cost_inputs(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 18)
    report = _daily_report(target_date)
    report["target_return_pct"] = math.nan

    assert (
        calibration._daily_report_issue(
            report,
            spec=spec,
            target_date=target_date,
        )
        == "target_policy_missing_or_invalid"
    )


def test_opportunity_proxy_rejects_nonfinite_adverse_return():
    try:
        calibration._opportunity_net_return_proxy(
            {
                "target_return_pct": 1.0,
                "first_hit": "adverse_first",
                "mae_pct": math.inf,
                "entry_touched_at_kst": "2026-08-18T10:00:00+09:00",
            }
        )
    except ValueError as exc:
        assert str(exc) == "widget_outcome_adverse_return_nonfinite"
    else:
        raise AssertionError("nonfinite adverse return must fail closed")


def test_failed_daily_report_carries_latest_valid_policy(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 6)
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    previous = _policy_payload(target_date, confirmations=3)
    (policy_dir / f"widget_advisory_policy_{target_date.isoformat()}.json").write_text(
        json.dumps(previous), encoding="utf-8"
    )
    invalid_daily = _daily_report(target_date, source_rows=0)

    policy, report = calibration.build_calibration_policy(
        target_date=target_date,
        daily_reports={spec.symbol: invalid_daily},
        policy_dir=policy_dir,
        specs=(spec,),
    )

    selected = policy["symbols"][spec.symbol]["sessions"]["KRX_REGULAR"]
    assert selected["required_actionable_confirmations"] == 3
    assert selected["decision"] == "carry_forward_report_verification_failed"
    assert policy["source_quality_status"] == "DEGRADED_SAFE_CARRY_FORWARD"
    assert report["all_daily_reports_verified"] is False


def test_policy_loader_ignores_future_and_malformed_policy(tmp_path):
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    current = _policy_payload(date(2026, 8, 6), confirmations=3)
    future = _policy_payload(date(2026, 8, 7), confirmations=2)
    malformed = _policy_payload(date(2026, 8, 5), confirmations=3)
    malformed["trading_runtime_effect"] = True
    for payload in (current, future, malformed):
        effective = payload["effective_date"]
        suffix = "-bad" if payload is malformed else ""
        (policy_dir / f"widget_advisory_policy_{effective}{suffix}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    selection = WidgetCalibrationPolicyLoader(policy_dir).resolve(
        symbol="999999",
        session="KRX_REGULAR",
        observed_date=date(2026, 8, 6),
    )

    assert selection["required_actionable_confirmations"] == 3
    assert selection["effective_date"] == "2026-08-06"
    assert selection["load_status"] == "dated_policy_loaded"


def test_policy_loader_uses_payload_effective_date_not_misleading_filename(tmp_path):
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    current = _policy_payload(date(2026, 8, 6), confirmations=2)
    older = _policy_payload(date(2026, 8, 5), confirmations=3)
    older["source_target_date"] = "2026-08-04"
    (policy_dir / "widget_advisory_policy_0000-current.json").write_text(
        json.dumps(current), encoding="utf-8"
    )
    (policy_dir / "widget_advisory_policy_9999-misleading.json").write_text(
        json.dumps(older), encoding="utf-8"
    )

    selection = WidgetCalibrationPolicyLoader(policy_dir).resolve(
        symbol="999999",
        session="KRX_REGULAR",
        observed_date=date(2026, 8, 6),
    )

    assert selection["required_actionable_confirmations"] == 2
    assert selection["effective_date"] == "2026-08-06"


def test_policy_loader_refreshes_cache_when_atomic_policy_is_published(tmp_path):
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    loader = WidgetCalibrationPolicyLoader(policy_dir)
    initial = loader.resolve(
        symbol="999999",
        session="KRX_REGULAR",
        observed_date=date(2026, 8, 6),
    )
    assert initial["load_status"] == "default_no_valid_dated_policy"

    policy = _policy_payload(date(2026, 8, 6), confirmations=3)
    staged = policy_dir / ".staged-policy"
    staged.write_text(json.dumps(policy), encoding="utf-8")
    staged.replace(policy_dir / "widget_advisory_policy_2026-08-06.json")

    refreshed = loader.resolve(
        symbol="999999",
        session="KRX_REGULAR",
        observed_date=date(2026, 8, 6),
    )
    assert refreshed["load_status"] == "dated_policy_loaded"
    assert refreshed["required_actionable_confirmations"] == 3


def test_default_target_date_does_not_treat_weekend_as_completed_session():
    assert calibration._resolve_default_target_date(
        now=datetime(2026, 8, 8, 21, 0, tzinfo=KST)
    ) == date(2026, 8, 7)


def test_current_in_memory_daily_report_replaces_existing_same_date(tmp_path):
    spec = _spec(tmp_path)
    target_date = date(2026, 8, 6)
    _write_daily_with_hits(
        spec,
        target_date,
        target_first=0,
        adverse_first=1,
    )
    current = _daily_report(target_date)
    current["outcomes"] = [
        {
            "market_session": "KRX_REGULAR",
            "horizon_minutes": 10,
            "evaluation_eligible": True,
            "first_hit": "target_first",
        }
    ]

    policy, _ = calibration.build_calibration_policy(
        target_date=target_date,
        daily_reports={spec.symbol: current},
        policy_dir=tmp_path / "policies",
        specs=(spec,),
    )

    selected = policy["symbols"][spec.symbol]["sessions"]["KRX_REGULAR"]
    assert selected["cumulative_target_first_count"] == 1
    assert selected["cumulative_adverse_first_count"] == 0
