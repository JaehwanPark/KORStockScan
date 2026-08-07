from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.entry_odds import producer
from src.engine.scalping.entry_odds.producer import (
    PROMPT_SHA256,
    build_prediction_row,
    produce,
    select_exact_payload_jobs,
)

KST = ZoneInfo("Asia/Seoul")


def _trace(trace_id: str = "trace-1") -> dict:
    return {
        "decision_trace_id": trace_id,
        "decision_ts": datetime(2026, 8, 6, 9, 0, tzinfo=KST).isoformat(),
        "decision_stage": "entry_screen",
        "stock_code": "005930",
        "payload_sha256": "a" * 64,
        "request_envelope_sha256": "b" * 64,
        "payload_replay_exact": True,
        "input_preflight_allowed": True,
        "input_preflight_status": "fresh_consistent",
        "reference_price": 10000,
        "reference_price_type": "executable_ask",
        "broker_route": "SOR",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "action": "BUY",
        "score": 99,
    }


def _payload() -> dict:
    return {
        "schema": "ai_decision_payload_v1",
        "payload_sha256": "a" * 64,
        "request_envelope_sha256": "b" * 64,
        "replay_exact": True,
        "redacted": False,
        "raw_secret_storage": False,
        "sensitive_value_policy": "key_and_embedded_credential_redaction_v2",
        "storage_security_policy": "ai_trace_payload_security_v2",
        "sanitized_user_input": {
            "exact_payload": {
                "features": {
                    "entry_liquidity_status": "thin",
                    "spread_bp": 20.0,
                },
                "quote": {"spread_bp": 20.0},
                "entry_candle_context": {"regime": "range"},
            }
        },
    }


def _label(trace_id: str = "trace-1", *, first_hit: str = "target_first") -> dict:
    return {
        "decision_trace_id": trace_id,
        "decision_stage": "entry_screen",
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "invalid_reasons": [],
        "stage_outcome": {
            "entry_path_label_version": "tight_stop_entry_path_v1",
            "entry_path_primary_horizon": "10m",
            "entry_path_target_pct": 0.3,
            "entry_path_adverse_pct": -0.7,
            "entry_path_first_hit": first_hit,
        },
    }


def _model_payload() -> dict:
    return {
        "raw_probabilities": {
            "TARGET_FIRST": 0.4,
            "ADVERSE_FIRST": 0.3,
            "NEITHER_POSITIVE": 0.2,
            "NEITHER_NONPOSITIVE": 0.2,
        },
        "payoff_bps": {
            "TARGET_FIRST": 50.0,
            "ADVERSE_FIRST": -80.0,
            "NEITHER_POSITIVE": 12.0,
            "NEITHER_NONPOSITIVE": -8.0,
        },
        "counterfactual_fill_probability": 0.8,
        "counterfactual_fill_state": "FULL",
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_select_jobs_uses_label_only_for_eligibility_and_exact_payload_join() -> None:
    jobs, exclusions = select_exact_payload_jobs(
        target_date="2026-08-06",
        traces=[_trace()],
        payloads=[_payload()],
        outcome_labels=[_label()],
    )

    assert len(jobs) == 1
    assert jobs[0]["exact_input"] == _payload()["sanitized_user_input"]
    assert "stage_outcome" not in jobs[0]
    assert exclusions.get("exact_payload_missing", 0) == 0


def test_same_bar_ambiguous_is_not_sent_to_provider() -> None:
    jobs, exclusions = select_exact_payload_jobs(
        target_date="2026-08-06",
        traces=[_trace()],
        payloads=[_payload()],
        outcome_labels=[_label(first_hit="same_bar_ambiguous")],
    )

    assert jobs == []
    assert exclusions["label_same_bar_ambiguous"] == 1


def test_build_prediction_row_normalizes_probabilities_and_separates_costs() -> None:
    jobs, _ = select_exact_payload_jobs(
        target_date="2026-08-06",
        traces=[_trace()],
        payloads=[_payload()],
        outcome_labels=[_label()],
    )

    row = build_prediction_row(
        job=jobs[0],
        model_payload=_model_payload(),
        provider_provenance={"response_id": "response-1"},
        model="gpt-5-nano",
    )

    assert sum(row["raw_probabilities"].values()) == pytest.approx(1.0)
    assert row["probability_normalization_scale"] == 1.1
    assert row["cost_inputs"]["entry_spread_bps"] == 0.0
    assert row["cost_inputs"]["exit_spread_bps"] == 10.0
    assert row["cost_inputs"]["cost_source_quality_status"] == "assumption_only"
    assert row["odds_provenance"]["prompt_sha256"] == PROMPT_SHA256
    assert row["odds_provenance"]["risk_regime"] == "RANGE"
    assert row["odds_provenance"]["liquidity_bucket"] == "THIN"
    assert row["runtime_effect"] is False
    assert row["broker_order_forbidden"] is True


def test_produce_is_resumable_and_never_passes_action_to_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace_path = tmp_path / "trace.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    outcome_path = tmp_path / "outcomes.json"
    output_path = tmp_path / "predictions.jsonl"
    manifest_path = tmp_path / "manifest.json"
    _write_jsonl(trace_path, [_trace()])
    _write_jsonl(payload_path, [_payload()])
    outcome_path.write_text(json.dumps({"labels": [_label()]}), encoding="utf-8")
    seen_jobs: list[dict] = []

    def fake_caller(**kwargs):
        seen_jobs.append(dict(kwargs["job"]))
        return _model_payload(), {
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
        }

    monkeypatch.setattr(producer, "_configured_api_keys", lambda: ["test-key"])
    first = produce(
        target_date="2026-08-06",
        traces_path=trace_path,
        payloads_path=payload_path,
        outcomes_path=outcome_path,
        output_path=output_path,
        manifest_path=manifest_path,
        execute_openai=True,
        workers=1,
        caller=fake_caller,
    )
    second = produce(
        target_date="2026-08-06",
        traces_path=trace_path,
        payloads_path=payload_path,
        outcomes_path=outcome_path,
        output_path=output_path,
        manifest_path=manifest_path,
        execute_openai=True,
        workers=1,
        caller=fake_caller,
    )

    assert first["success_count"] == 1
    assert first["provider_usage"]["total_tokens"] == 120
    assert second["planned_prediction_count"] == 0
    assert len(seen_jobs) == 1
    assert seen_jobs[0]["trace"]["action"] == "BUY"
    request = producer._request_input(seen_jobs[0])
    assert '"action"' not in request
    assert '"score"' not in request
    assert len(output_path.read_text(encoding="utf-8").splitlines()) == 1
    assert output_path.stat().st_mode & 0o777 == 0o600


def test_dry_run_does_not_require_api_key_or_write_predictions(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    outcome_path = tmp_path / "outcomes.json"
    output_path = tmp_path / "predictions.jsonl"
    manifest_path = tmp_path / "manifest.json"
    _write_jsonl(trace_path, [_trace()])
    _write_jsonl(payload_path, [_payload()])
    outcome_path.write_text(json.dumps({"labels": [_label()]}), encoding="utf-8")

    result = produce(
        target_date="2026-08-06",
        traces_path=trace_path,
        payloads_path=payload_path,
        outcomes_path=outcome_path,
        output_path=output_path,
        manifest_path=manifest_path,
        execute_openai=False,
    )

    assert result["mode"] == "dry_run"
    assert result["planned_prediction_count"] == 1
    assert not output_path.exists()
    assert manifest_path.exists()


def test_resume_rejects_predictions_from_a_different_model(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    outcome_path = tmp_path / "outcomes.json"
    output_path = tmp_path / "predictions.jsonl"
    manifest_path = tmp_path / "manifest.json"
    _write_jsonl(trace_path, [_trace()])
    _write_jsonl(payload_path, [_payload()])
    outcome_path.write_text(json.dumps({"labels": [_label()]}), encoding="utf-8")
    jobs, _ = select_exact_payload_jobs(
        target_date="2026-08-06",
        traces=[_trace()],
        payloads=[_payload()],
        outcome_labels=[_label()],
    )
    row = build_prediction_row(
        job=jobs[0],
        model_payload=_model_payload(),
        provider_provenance={},
        model="different-model",
    )
    _write_jsonl(output_path, [row])

    with pytest.raises(ValueError, match="model mismatch"):
        produce(
            target_date="2026-08-06",
            traces_path=trace_path,
            payloads_path=payload_path,
            outcomes_path=outcome_path,
            output_path=output_path,
            manifest_path=manifest_path,
            execute_openai=False,
            model="gpt-5-nano",
        )
