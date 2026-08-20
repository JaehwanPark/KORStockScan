from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from src.engine.monitoring.samsung_widget_contract import KST
from src.trading.widget_auto_trade.policy import (
    POLICY_AUTHORITY,
    POLICY_SCHEMA,
    WIDGET_AUTO_TRADE_LEG_QUANTITY,
    WidgetAutoTradePolicyLoader,
)
from src.utils.market_day import is_krx_trading_day


def _policy(*, effective_date: str = "2026-08-12") -> dict:
    return {
        "schema": POLICY_SCHEMA,
        "status": "verified",
        "policy_version": "test-policy-v1",
        "source_target_date": "2026-08-11",
        "effective_date": effective_date,
        "source_quality_status": "PASS",
        "authority": POLICY_AUTHORITY,
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "metric_contract": {
            "metric_role": "bounded_widget_auto_trade_policy_calibration",
            "decision_authority": POLICY_AUTHORITY,
            "window_policy": "clean_baseline_cumulative",
            "sample_floor": "two_dates",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "completed_prior_dates",
            "forbidden_uses": ["same_day_policy"],
        },
        "symbols": {
            "034020": {
                "sessions": {
                    "KRX_REGULAR": {
                        "enabled": True,
                        "market_venue": "KRX",
                        "allowed_entry_states": ["ENTRY_CAUTION", "ENTRY_READY"],
                        "leg_quantity_each": WIDGET_AUTO_TRADE_LEG_QUANTITY,
                        "add_trigger_bps_from_initial_fill": [-80, -160],
                        "take_profit_bps_from_equal_share_average": 100,
                        "max_completed_entries_per_day": 2,
                        "reentry_cooldown_minutes": 5,
                        "new_entry_cutoff_time": "14:30:00",
                        "force_flat_at_session_end": True,
                        "force_exit_time": "15:18:00",
                        "overnight_forbidden": True,
                        "source_final_exit_action": "sell_own_filled_quantity",
                        "actual_order_submitted": False,
                        "broker_guard_bypass": False,
                    }
                }
            }
        },
    }


def _write_policy(tmp_path: Path, filename: str, payload: dict) -> None:
    policy_path = tmp_path / filename
    report_path = tmp_path / f"report_{payload['effective_date']}.json"
    report = {
        "status": "complete",
        "source_quality_status": "PASS",
        "target_date": payload["source_target_date"],
        "effective_date": payload["effective_date"],
        "policy_verification": {
            "status": "pass",
            "policy_path": str(policy_path),
        },
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    payload["evidence_report_path"] = str(report_path)
    for symbol_payload in payload["symbols"].values():
        for session_payload in symbol_payload["sessions"].values():
            session_payload["evidence_artifact"] = str(report_path)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")


def test_loader_selects_newest_effective_verified_policy(tmp_path: Path) -> None:
    older = _policy(effective_date="2026-08-12")
    newer = _policy(effective_date="2026-08-13")
    newer["source_target_date"] = "2026-08-12"
    newer["policy_version"] = "test-policy-v2"
    _write_policy(tmp_path, "widget_auto_trade_policy_2026-08-12.json", older)
    _write_policy(tmp_path, "widget_auto_trade_policy_2026-08-13.json", newer)

    loaded = WidgetAutoTradePolicyLoader(tmp_path).resolve_all(
        observed_date=date(2026, 8, 13)
    )

    policy = loaded["034020"]["KRX_REGULAR"]
    assert policy["policy_id"] == "test-policy-v2"
    assert policy["overnight_forbidden"] is True
    assert policy["force_exit_time"] == "15:18:00"
    assert policy["new_entry_runtime_eligible"] is False
    assert (
        policy["new_entry_runtime_block_reason"]
        == "cumulative_research_40_qualified_dates_incomplete"
    )


def test_loader_allows_low_symbol_only_after_verified_40_date_gate(
    tmp_path: Path,
) -> None:
    qualified_dates = []
    candidate = date(2026, 8, 12)
    while len(qualified_dates) < 40:
        if is_krx_trading_day(candidate):
            qualified_dates.append(candidate.isoformat())
        candidate = date.fromordinal(candidate.toordinal() + 1)
    source_target_date = qualified_dates[-1]
    effective = date.fromordinal(date.fromisoformat(source_target_date).toordinal() + 1)
    while not is_krx_trading_day(effective):
        effective = date.fromordinal(effective.toordinal() + 1)
    payload = _policy(effective_date=effective.isoformat())
    payload["source_target_date"] = source_target_date
    session = payload["symbols"]["034020"]["sessions"]["KRX_REGULAR"]
    session.update(
        {
            "research_accumulation_start_date": "2026-08-12",
            "research_qualified_observation_date_count": 40,
            "research_minimum_qualified_observation_dates": 40,
            "research_accumulation_gate_status": "ready",
        }
    )
    policy_path = tmp_path / f"widget_auto_trade_policy_{effective.isoformat()}.json"
    report_path = tmp_path / f"report_{source_target_date}.json"
    report = {
        "status": "complete",
        "source_quality_status": "PASS",
        "target_date": source_target_date,
        "effective_date": effective.isoformat(),
        "symbols": {
            "034020": {
                "sessions": {
                    "KRX_REGULAR": {
                        "research_accumulation": {
                            "status": "ready",
                            "start_date": "2026-08-12",
                            "minimum_qualified_observation_dates": 40,
                            "qualified_observation_date_count": 40,
                            "qualified_observation_dates": qualified_dates,
                            "qualification_contract": (
                                "KRX_trading_date;KRX_REGULAR/KRX;"
                                "source_quality_PASS_rows>=300;"
                                "first_PASS_observation<=09:30;"
                                "last_PASS_observation>=15:20"
                            ),
                            "runtime_eligible": True,
                        }
                    }
                }
            }
        },
        "policy_verification": {
            "status": "pass",
            "policy_path": str(policy_path),
        },
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    payload["evidence_report_path"] = str(report_path)
    session["evidence_artifact"] = str(report_path)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = WidgetAutoTradePolicyLoader(tmp_path).resolve_all(observed_date=effective)

    assert loaded["034020"]["KRX_REGULAR"]["new_entry_runtime_eligible"] is True


def test_loader_rejects_same_day_evidence_and_unsafe_contract(tmp_path: Path) -> None:
    payload = _policy()
    payload["source_target_date"] = payload["effective_date"]
    payload["symbols"]["034020"]["sessions"]["KRX_REGULAR"][
        "broker_guard_bypass"
    ] = True
    _write_policy(tmp_path, "widget_auto_trade_policy_2026-08-12.json", payload)

    assert (
        WidgetAutoTradePolicyLoader(tmp_path).resolve_all(
            observed_date=date(2026, 8, 12)
        )
        == {}
    )


def test_loader_rejects_static_symbol_exit_action_mismatch(tmp_path: Path) -> None:
    payload = _policy()
    payload["symbols"]["034020"]["sessions"]["KRX_REGULAR"][
        "source_final_exit_action"
    ] = "observe_only_no_forced_sell"
    _write_policy(tmp_path, "widget_auto_trade_policy_2026-08-12.json", payload)

    assert (
        WidgetAutoTradePolicyLoader(tmp_path).resolve_all(
            observed_date=date(2026, 8, 12)
        )
        == {}
    )


def test_loader_does_not_apply_future_policy(tmp_path: Path) -> None:
    payload = _policy(effective_date="2026-08-13")
    _write_policy(tmp_path, "widget_auto_trade_policy_2026-08-13.json", payload)

    assert (
        WidgetAutoTradePolicyLoader(tmp_path).resolve_all(
            observed_date=datetime(2026, 8, 12, 9, tzinfo=KST).date()
        )
        == {}
    )


def test_loader_requires_completed_verified_evidence_report(tmp_path: Path) -> None:
    payload = _policy()
    payload["evidence_report_path"] = str(tmp_path / "missing-report.json")
    (tmp_path / "widget_auto_trade_policy_2026-08-12.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    assert (
        WidgetAutoTradePolicyLoader(tmp_path).resolve_all(
            observed_date=date(2026, 8, 12)
        )
        == {}
    )
