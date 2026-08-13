import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION,
    DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION,
)
from src.engine.scalping import entry_price_live_policy as policy

KST = ZoneInfo("Asia/Seoul")


def _report() -> dict:
    return {
        "schema": policy.EXPECTED_REPORT_SCHEMA,
        "status": policy.EXPECTED_REPORT_STATUS,
        "stage": "entry_price",
        "candidate_prompt_versions": [DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION],
        "candidate_semantic_validator_versions": [policy.EXPECTED_SEMANTIC_VALIDATOR],
        "cohort_filter": {
            "effective_venue": "KRX",
            "session_bucket": "krx_regular",
        },
        "request_count": 200,
        "pass_count": 200,
        "provider_failed_count": 0,
        "schema_rejected_count": 0,
        "coverage_sample_floor": {
            "required_decision_rows": 30,
            "required_unique_symbols": 10,
            "observed_decision_rows": 200,
            "observed_unique_symbols": 60,
            "pass": True,
        },
        "entry_price_selection_complete": True,
        "entry_price_effect_not_collapsed": True,
        "entry_price_selection_outcome_comparison": {"quality_gate_pass": True},
        "outcome_comparison": {
            "source_quality_adjusted_ev_delta_pct": 0.004,
            "new_missed_upside_count": 0,
            "control_probe_severe_tail_exposure_count": 3,
            "candidate_probe_severe_tail_exposure_count": 3,
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _snapshot(*, venue: str = "KRX", session: str = "KRX_REGULAR") -> dict:
    return {
        "ai_market_snapshot_v1": {
            "effective_venue": venue,
            "session_bucket": session,
            "ai_input_preflight_v1": {
                "allowed": True,
                "venue_consistent": True,
                "blockers": [],
            },
        }
    }


def _env(path: Path) -> dict[str, str]:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        policy.ENABLED_ENV: "true",
        policy.ACTIVE_DATE_ENV: "2026-08-14",
        policy.EVIDENCE_PATH_ENV: str(path),
        policy.EVIDENCE_SHA256_ENV: sha,
    }


def test_resolve_entry_price_live_policy_selects_only_verified_krx_regular(
    tmp_path,
):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")

    result = policy.resolve_entry_price_live_policy(
        _snapshot(),
        env=_env(report_path),
        now=datetime(2026, 8, 14, 9, 1, tzinfo=KST),
    )

    assert result["status"] == "active_krx_regular_v2_5"
    assert (
        result["selected_prompt_version"]
        == DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION
    )
    assert result["runtime_effect"] is True
    assert result["allowed_runtime_apply"] is True
    assert result["actual_order_submitted"] is False
    assert result["broker_order_forbidden"] is True


def test_resolve_entry_price_live_policy_keeps_nxt_and_premarket_on_control(
    tmp_path,
):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")
    env = _env(report_path)

    nxt = policy.resolve_entry_price_live_policy(
        _snapshot(venue="NXT", session="NXT_AFTERMARKET"),
        env=env,
        now=datetime(2026, 8, 14, 16, 1, tzinfo=KST),
    )
    premarket = policy.resolve_entry_price_live_policy(
        _snapshot(venue="NXT", session="PREMARKET_KRX_LIKE"),
        env=env,
        now=datetime(2026, 8, 14, 8, 31, tzinfo=KST),
    )

    assert nxt["selected_prompt_version"] == "entry_price_v1"
    assert "effective_venue_not_krx" in nxt["blocking_reasons"]
    assert premarket["selected_prompt_version"] == "entry_price_v1"
    assert "session_not_krx_regular" in premarket["blocking_reasons"]


def test_resolve_entry_price_live_policy_fails_closed_on_evidence_hash_change(
    tmp_path,
):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")
    env = _env(report_path)
    report_path.write_text(
        json.dumps({**_report(), "pass_count": 199}), encoding="utf-8"
    )

    result = policy.resolve_entry_price_live_policy(
        _snapshot(),
        env=env,
        now=datetime(2026, 8, 14, 9, 1, tzinfo=KST),
    )

    assert result["selected_prompt_version"] == "entry_price_v1"
    assert result["runtime_effect"] is False
    assert "evidence_report_hash_mismatch" in result["blocking_reasons"]


def test_resolve_entry_price_live_policy_fails_closed_on_malformed_counts(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                **_report(),
                "provider_failed_count": "not-a-number",
                "outcome_comparison": {
                    **_report()["outcome_comparison"],
                    "candidate_probe_severe_tail_exposure_count": "bad",
                },
            }
        ),
        encoding="utf-8",
    )

    result = policy.resolve_entry_price_live_policy(
        _snapshot(),
        env=_env(report_path),
        now=datetime(2026, 8, 14, 9, 1, tzinfo=KST),
    )

    assert result["selected_prompt_version"] == "entry_price_v1"
    assert "evidence_provider_failure" in result["blocking_reasons"]
    assert "evidence_severe_tail_increased" in result["blocking_reasons"]
