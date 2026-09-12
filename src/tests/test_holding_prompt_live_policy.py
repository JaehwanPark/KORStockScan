from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.scalping import holding_prompt_live_policy as policy

KST = ZoneInfo("Asia/Seoul")


def _economics(*, candidate_ev: float = 0.12, control_ev: float = 0.10):
    return {
        "clean_baseline_date": "2026-06-05",
        "as_of_date": "2026-09-11",
        "row_count": 10,
        "unique_symbol_count": 3,
        "candidate_cost_adjusted_ev_pct": candidate_ev,
        "control_cost_adjusted_ev_pct": control_ev,
        "candidate_cost_adjusted_ev_delta_pct": candidate_ev - control_ev,
        "candidate_positive_outcome_frequency": 0.6,
        "candidate_severe_tail_count": 0,
        "control_severe_tail_count": 0,
        "source_reports": [],
    }


def test_holding_economics_uses_only_explicit_cost_and_excludes_trim():
    requests = [
        {"paired_replay_id": "pair-1", "stock_code": "005930"},
        {"paired_replay_id": "pair-2", "stock_code": "000660"},
        {"paired_replay_id": "pair-3", "stock_code": "035420"},
    ]
    results = [
        {
            "paired_replay_id": "pair-1",
            "decision_trace_id": "trace-1",
            "status": "pass",
            "same_payload_confirmed": True,
            "control_response": {"action": "EXIT"},
            "candidate_response": {"action": "HOLD"},
        },
        {
            "paired_replay_id": "pair-2",
            "decision_trace_id": "trace-2",
            "status": "pass",
            "same_payload_confirmed": True,
            "control_response": {"action": "HOLD"},
            "candidate_response": {"action": "TRIM"},
        },
        {
            "paired_replay_id": "pair-3",
            "decision_trace_id": "trace-3",
            "status": "pass",
            "same_payload_confirmed": True,
            "control_response": {"action": "HOLD"},
            "candidate_response": {"action": "TRIM"},
        },
    ]
    labels = [
        {
            "decision_trace_id": "trace-1",
            "decision_stage": "holding",
            "source_quality_status": "pass",
            "horizon_metrics": {"30m": {"net_return_pct": 0.15}},
        },
        {
            "decision_trace_id": "trace-2",
            "decision_stage": "holding",
            "source_quality_status": "pass",
            "horizon_metrics": {"30m": {"end_return_pct": 9.0}},
        },
        {
            "decision_trace_id": "trace-3",
            "decision_stage": "holding",
            "source_quality_status": "pass",
            "horizon_metrics": {"30m": {"net_return_pct": 0.2}},
        },
    ]

    result = policy._holding_economics(
        requests=requests,
        results=results,
        labels=labels,
    )

    assert result["row_count"] == 1
    assert result["candidate_cost_adjusted_ev_pct"] == 0.15
    assert result["control_cost_adjusted_ev_pct"] == 0.0
    assert result["exclusions"] == [
        {
            "decision_trace_id": "trace-2",
            "reason": "explicit_cost_adjusted_outcome_missing",
        },
        {
            "decision_trace_id": "trace-3",
            "reason": "trim_fractional_outcome_contract_missing",
        },
    ]


def test_candidate_promotes_at_explicit_point_one_percent(monkeypatch):
    monkeypatch.setattr(policy, "_cumulative_economics", lambda *_: _economics())

    candidate = policy.build_candidate(
        "2026-09-11",
        ("KRX", "KRX_REGULAR"),
    )

    assert candidate["effective_date"] == "2026-09-14"
    assert candidate["status"] == "preopen_apply_ready"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["runtime_effect"] is False
    assert candidate["actual_order_submitted"] is False


def test_runtime_requires_exact_activation_and_unchanged_candidate(
    monkeypatch,
    tmp_path,
):
    candidate_dir = tmp_path / "candidates"
    activation_dir = tmp_path / "activations"
    monkeypatch.setattr(policy, "CANDIDATE_DIR", candidate_dir)
    monkeypatch.setattr(policy, "ACTIVATION_DIR", activation_dir)
    monkeypatch.setattr(policy, "_cumulative_economics", lambda *_: _economics())
    cohort = ("KRX", "KRX_REGULAR")
    candidate = policy.build_candidate("2026-09-11", cohort)
    policy._write_json(policy.candidate_path("2026-09-11", cohort), candidate)
    activation = policy.build_activation("2026-09-14", cohort)
    policy._write_json(policy.activation_path("2026-09-14", cohort), activation)

    selected = policy.resolve_holding_prompt_policy(
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        now=datetime(2026, 9, 14, 9, 0, tzinfo=KST),
    )
    assert selected["enabled"] is True
    assert selected["runtime_effect"] is True

    candidate["cumulative_economics"]["candidate_cost_adjusted_ev_pct"] = 99.0
    policy._write_json(policy.candidate_path("2026-09-11", cohort), candidate)
    fallback = policy.resolve_holding_prompt_policy(
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        now=datetime(2026, 9, 14, 9, 0, tzinfo=KST),
    )
    assert fallback["enabled"] is False
    assert fallback["reason"] == "holding_prompt_candidate_contract_invalid"


def test_wrapper_paths_are_natural_postclose_and_preopen_only():
    postclose = policy.Path(
        "deploy/run_ai_entry_setup_paired_replay_postclose.sh"
    ).read_text(encoding="utf-8")
    preopen = policy.Path("deploy/run_threshold_cycle_preopen.sh").read_text(
        encoding="utf-8"
    )

    assert "holding_prompt_live_policy" in postclose
    assert "--phase postclose" in postclose
    assert "--max-new-total" in postclose
    assert "holding_prompt_live_policy" in preopen
    assert "--phase preopen" in preopen
