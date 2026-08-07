from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.entry_odds.history import build_history, discover_source_dates
from src.engine.scalping.entry_odds.observer import CALIBRATION_ROW_SCHEMA

KST = ZoneInfo("Asia/Seoul")


def _prediction(date: str, index: int = 1) -> dict:
    decision_ts = datetime.fromisoformat(f"{date}T09:00:00+09:00").isoformat()
    payload_sha = f"{index:064x}"
    return {
        "schema": "entry_odds_raw_prediction_v1",
        "decision_trace_id": f"trace-{date}-{index}",
        "decision_ts": decision_ts,
        "stock_code": f"{index:06d}",
        "source_quality_status": "pass",
        "odds_provenance": {
            "provider_actual": "openai",
            "model_id": "gpt-5-nano",
            "prompt_sha256": "a" * 64,
            "input_schema_version": "entry_odds_exact_historical_payload_v1",
            "odds_policy_version": "entry_odds_raw_probability_policy_v1",
            "outcome_label_version": "tight_stop_entry_path_v1",
            "outcome_horizon": "10m",
            "outcome_target_bps": 30.0,
            "outcome_adverse_bps": -70.0,
            "cost_model_version": "explicit_2026_tax_quote_spread_assumption_v1",
            "execution_venue": "SOR",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "risk_regime": "RANGE",
            "liquidity_bucket": "THIN",
            "source_payload_sha256": payload_sha,
        },
        "raw_probabilities": {
            "TARGET_FIRST": 0.4,
            "ADVERSE_FIRST": 0.3,
            "NEITHER_POSITIVE": 0.2,
            "NEITHER_NONPOSITIVE": 0.1,
        },
        "payoff_bps": {
            "TARGET_FIRST": 50.0,
            "ADVERSE_FIRST": -80.0,
            "NEITHER_POSITIVE": 12.0,
            "NEITHER_NONPOSITIVE": -8.0,
        },
        "counterfactual_fill_probability": 0.8,
        "counterfactual_fill_state": "FULL",
        "uncertainty_hurdle_bps": 5.0,
        "uncertainty_hurdle_components_bps": {
            "model_uncertainty": 3.0,
            "tail_risk": 0.0,
            "operational_buffer": 2.0,
        },
        "cost_inputs": {
            "tax_bps": 20.0,
            "commission_buy_bps": 0.0,
            "commission_sell_bps": 0.0,
            "entry_spread_bps": 0.0,
            "exit_spread_bps": 10.0,
            "slippage_buy_bps": 0.0,
            "slippage_sell_bps": 0.0,
            "market_impact_bps": 0.0,
            "entry_price_basis": "executable_ask",
            "price_basis_includes_entry_spread": True,
            "listing_market": "KOSPI_OR_KOSDAQ_NOT_DISTINGUISHED",
            "execution_venue": "SOR",
            "instrument_tax_class": "taxable_listed_common_stock_assumed",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "cost_source_quality_status": "assumption_only",
            "assumption_flags": ["test_assumption"],
        },
    }


def _trace(prediction: dict) -> dict:
    return {
        "decision_trace_id": prediction["decision_trace_id"],
        "decision_ts": prediction["decision_ts"],
        "decision_stage": "entry_screen",
        "stock_code": prediction["stock_code"],
        "action": "WAIT",
        "score": 70,
        "payload_sha256": prediction["odds_provenance"]["source_payload_sha256"],
        "payload_replay_exact": True,
        "input_preflight_allowed": True,
        "input_preflight_status": "fresh_consistent",
        "reference_price": 10000.0,
        "reference_price_type": "executable_ask",
        "broker_route": "SOR",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
    }


def _label(prediction: dict) -> dict:
    return {
        "decision_trace_id": prediction["decision_trace_id"],
        "decision_ts": prediction["decision_ts"],
        "primary_payload_sha256": prediction["odds_provenance"][
            "source_payload_sha256"
        ],
        "decision_stage": "entry_screen",
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "invalid_reasons": [],
        "stage_outcome": {
            "entry_path_primary_horizon": "10m",
            "entry_path_label_version": "tight_stop_entry_path_v1",
            "entry_path_first_hit": "target_first",
            "entry_path_target_pct": 0.3,
            "entry_path_adverse_pct": -0.7,
        },
        "horizon_metrics": {"10m": {"end_return_pct": 0.5}},
        "correlation": {"actual_order_submitted": False},
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_build_history_writes_only_strictly_prior_verified_updates(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    trace_root = tmp_path / "trace"
    outcome_root = tmp_path / "outcomes"
    date = "2026-08-05"
    prediction = _prediction(date)
    prediction_path = raw_root / f"entry_odds_raw_predictions_{date}.jsonl"
    _write_jsonl(prediction_path, [prediction])
    (raw_root / f"entry_odds_raw_predictions_{date}.manifest.json").write_text(
        json.dumps(
            {
                "complete": True,
                "status": "complete",
                "failure_count": 0,
                "output_prediction_count": 1,
                "output_sha256": hashlib.sha256(
                    prediction_path.read_bytes()
                ).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(trace_root / f"ai_decision_trace_{date}.jsonl", [_trace(prediction)])
    outcome_root.mkdir(parents=True)
    (outcome_root / f"ai_decision_outcome_labels_{date}.json").write_text(
        json.dumps({"labels": [_label(prediction)]}), encoding="utf-8"
    )
    output_path = tmp_path / "calibration" / "history.jsonl"

    manifest = build_history(
        target_date="2026-08-06",
        source_dates=[date],
        raw_root=raw_root,
        trace_root=trace_root,
        outcome_root=outcome_root,
        output_path=output_path,
    )

    rows = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert manifest["history_row_count"] == 1
    assert rows[0]["schema"] == CALIBRATION_ROW_SCHEMA
    assert rows[0]["decision_ts"] < "2026-08-06T00:00:00+09:00"
    assert rows[0]["exact_trace_verified"] is True
    assert rows[0]["runtime_effect"] is False
    assert output_path.stat().st_mode & 0o777 == 0o600


def test_build_history_rejects_target_date_as_calibration_source(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="strictly before"):
        build_history(
            target_date="2026-08-06",
            source_dates=["2026-08-06"],
            raw_root=tmp_path,
            trace_root=tmp_path,
            outcome_root=tmp_path,
            output_path=tmp_path / "history.jsonl",
        )


def test_discover_source_dates_excludes_target_and_pre_baseline(tmp_path: Path) -> None:
    for date in ("2026-06-04", "2026-08-05", "2026-08-06"):
        (tmp_path / f"entry_odds_raw_predictions_{date}.jsonl").write_text("")

    assert discover_source_dates(tmp_path, "2026-08-06") == ["2026-08-05"]


def test_build_history_rejects_incomplete_producer_manifest(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    trace_root = tmp_path / "trace"
    outcome_root = tmp_path / "outcomes"
    date = "2026-08-05"
    prediction = _prediction(date)
    _write_jsonl(raw_root / f"entry_odds_raw_predictions_{date}.jsonl", [prediction])
    (raw_root / f"entry_odds_raw_predictions_{date}.manifest.json").write_text(
        json.dumps(
            {
                "complete": False,
                "status": "incomplete",
                "failure_count": 1,
                "output_prediction_count": 1,
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(trace_root / f"ai_decision_trace_{date}.jsonl", [_trace(prediction)])
    outcome_root.mkdir(parents=True)
    (outcome_root / f"ai_decision_outcome_labels_{date}.json").write_text(
        json.dumps({"labels": [_label(prediction)]}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="incomplete"):
        build_history(
            target_date="2026-08-06",
            source_dates=[date],
            raw_root=raw_root,
            trace_root=trace_root,
            outcome_root=outcome_root,
            output_path=tmp_path / "history.jsonl",
        )
