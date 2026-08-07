from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.scalping.entry_odds.observer import (
    AMBIGUOUS_OUTCOME,
    CALIBRATION_ROW_SCHEMA,
    METRIC_DECISION_CONTRACT,
    RAW_PREDICTION_SCHEMA,
    build_report,
    main,
    write_report,
)

KST = ZoneInfo("Asia/Seoul")


def _provenance(source_payload_sha256: str) -> dict:
    return {
        "provider_actual": "offline_test_provider",
        "model_id": "odds-test-model-v1",
        "prompt_sha256": "a" * 64,
        "input_schema_version": "exact_ai_payload_v1",
        "odds_policy_version": "entry_odds_policy_v1",
        "outcome_label_version": "tight_stop_entry_path_v1",
        "outcome_horizon": "10m",
        "outcome_target_bps": 30.0,
        "outcome_adverse_bps": -70.0,
        "cost_model_version": "explicit_round_trip_cost_v1",
        "execution_venue": "KRX",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "risk_regime": "NORMAL",
        "liquidity_bucket": "NORMAL",
        "source_payload_sha256": source_payload_sha256,
    }


def _probabilities(outcome: str = "TARGET_FIRST") -> dict[str, float]:
    probability = {
        "TARGET_FIRST": 0.1,
        "ADVERSE_FIRST": 0.1,
        "NEITHER_POSITIVE": 0.1,
        "NEITHER_NONPOSITIVE": 0.1,
    }
    probability[outcome] = 0.7
    return probability


def _cost_inputs(*, includes_spread: bool = False, spread_bps: float = 3.0) -> dict:
    return {
        "tax_bps": 20.0,
        "commission_buy_bps": 0.0,
        "commission_sell_bps": 0.0,
        "entry_spread_bps": spread_bps,
        "exit_spread_bps": 0.0,
        "slippage_buy_bps": 0.0,
        "slippage_sell_bps": 0.0,
        "market_impact_bps": 0.0,
        "entry_price_basis": "reference_mid",
        "price_basis_includes_entry_spread": includes_spread,
        "listing_market": "KOSPI",
        "execution_venue": "KRX",
        "instrument_tax_class": "listed_common_stock",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "cost_source_quality_status": "verified",
        "assumption_flags": [],
    }


def _prediction(index: int, decision_ts: datetime, *, spread_bps: float = 3.0) -> dict:
    trace_id = f"trace-{index}"
    payload_sha = f"{index:064x}"
    return {
        "schema": RAW_PREDICTION_SCHEMA,
        "decision_trace_id": trace_id,
        "decision_ts": decision_ts.isoformat(),
        "stock_code": f"{index % 10:06d}",
        "source_quality_status": "pass",
        "odds_provenance": _provenance(payload_sha),
        "raw_probabilities": _probabilities(),
        "payoff_bps": {
            "TARGET_FIRST": 100.0,
            "ADVERSE_FIRST": -100.0,
            "NEITHER_POSITIVE": 20.0,
            "NEITHER_NONPOSITIVE": -20.0,
        },
        "counterfactual_fill_probability": 1.0,
        "counterfactual_fill_state": "FULL",
        "uncertainty_hurdle_bps": 0.0,
        "uncertainty_hurdle_components_bps": {
            "model_uncertainty": 0.0,
            "tail_risk": 0.0,
            "operational_buffer": 0.0,
        },
        "cost_inputs": _cost_inputs(spread_bps=spread_bps),
    }


def _trace(prediction: dict, *, action: str = "BUY") -> dict:
    return {
        "decision_trace_id": prediction["decision_trace_id"],
        "decision_ts": prediction["decision_ts"],
        "decision_stage": "entry_screen",
        "stock_code": prediction["stock_code"],
        "action": action,
        "score": 80,
        "payload_sha256": prediction["odds_provenance"]["source_payload_sha256"],
        "payload_replay_exact": True,
        "input_preflight_allowed": True,
        "input_preflight_status": "fresh_consistent",
        "reference_price": 10_000.0,
        "effective_venue": "KRX",
        "broker_route": "KRX",
        "session_bucket": "KRX_REGULAR",
        "reference_price_type": "reference_mid",
    }


def _outcome_label(
    prediction: dict,
    *,
    first_hit: str = "target_first",
    end_return_pct: float = 1.0,
) -> dict:
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
            "entry_path_first_hit": first_hit,
            "entry_path_target_pct": 0.3,
            "entry_path_adverse_pct": -0.7,
        },
        "horizon_metrics": {"10m": {"end_return_pct": end_return_pct}},
        "correlation": {
            "actual_order_submitted": False,
            "realized_profit_pct": None,
        },
    }


def _calibration_rows(count: int = 40) -> list[dict]:
    start = datetime(2026, 8, 1, 9, 0, tzinfo=KST)
    rows = []
    for index in range(count):
        rows.append(
            {
                "schema": CALIBRATION_ROW_SCHEMA,
                "decision_trace_id": f"calibration-trace-{index}",
                "decision_ts": (
                    start + timedelta(days=index % 2, minutes=index)
                ).isoformat(),
                "stock_code": f"{index % 10:06d}",
                "source_quality_status": "pass",
                "exact_trace_verified": True,
                "outcome_contract_verified": True,
                "odds_provenance": _provenance(f"{index + 1000:064x}"),
                "raw_probabilities": _probabilities(),
                "observed_outcome_label": "TARGET_FIRST",
            }
        )
    return rows


def test_build_report_produces_calibrated_offline_odds_ledger() -> None:
    predictions = []
    traces = []
    outcomes = []
    veto_indexes = {0, 1, 2, 15, 16}
    for index in range(30):
        day = 5 if index < 15 else 6
        prediction = _prediction(index, datetime(2026, 8, day, 9, 0, tzinfo=KST))
        if index in veto_indexes:
            prediction["raw_probabilities"] = _probabilities("ADVERSE_FIRST")
            prediction["payoff_bps"] = {
                "TARGET_FIRST": 10.0,
                "ADVERSE_FIRST": -100.0,
                "NEITHER_POSITIVE": 1.0,
                "NEITHER_NONPOSITIVE": -20.0,
            }
        elif index < 15:
            prediction["payoff_bps"]["TARGET_FIRST"] = 30.0
        predictions.append(prediction)
        traces.append(_trace(prediction))
        outcomes.append(
            _outcome_label(
                prediction,
                first_hit=(
                    "adverse_first" if index in veto_indexes else "target_first"
                ),
                end_return_pct=(
                    -1.0 if index in veto_indexes else (0.3 if index < 15 else 1.0)
                ),
            )
        )

    report = build_report(
        target_date="2026-08-06",
        predictions=predictions,
        calibration_rows=_calibration_rows(),
        traces=traces,
        outcome_labels=outcomes,
        generated_at=datetime(2026, 8, 6, 20, 0, tzinfo=KST),
    )

    assert report["final_state"] == "sim_candidate_ready"
    assert report["summary"]["eligible_count"] == 30
    assert report["summary"]["assessment_counts"] == {
        "WOULD_BET": 25,
        "WOULD_NO_BET": 5,
        "ABSTAIN": 0,
    }
    assert report["summary"]["source_quality_adjusted_ev_pct"] == 0.1566666667
    assert report["ledger"][0]["cost"]["components_bps"]["tax_bps"] == 20.0
    assert report["ledger"][0]["cost"]["total_cost_bps"] == 23.0
    assert report["ledger"][0]["original_action"] == "BUY"
    assert report["ledger"][0]["observer_assessment"] == "WOULD_NO_BET"
    assert report["ledger"][0]["runtime_effect"] is False
    assert len(report["calibration_updates"]) == 30
    assert report["calibration_updates"][0]["exact_trace_verified"] is True
    assert (
        sum(row["sample_count"] for row in report["predicted_vs_oos_outcome"]["rows"])
        == 30
    )
    assert (
        report["predicted_vs_oos_outcome"]["observed_ev_monotonic_non_decreasing"]
        is True
    )
    assert report["negative_veto_attribution"]["sim_candidate_gate"]["pass"] is True
    assert report["fill_cohort_attribution"]["cohorts"]["FULL"]["sample_count"] == 30
    assert report["fill_cohort_attribution"]["full_and_partial_merged"] is False
    assert report["decision"]["applied_to_sim"] is False
    assert report["decision_authority"] == "counterfactual_only"
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert METRIC_DECISION_CONTRACT["primary_decision_metric"] == (
        "source_quality_adjusted_ev_pct"
    )


def test_unfitted_signature_abstains_without_runtime_authority() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=_calibration_rows(5),
        traces=[_trace(prediction)],
        outcome_labels=[_outcome_label(prediction)],
    )

    row = report["ledger"][0]
    assert row["observer_assessment"] == "ABSTAIN"
    assert "calibration_row_floor" in row["assessment_exclusion_reasons"]
    assert "calibration_unique_symbol_floor" in row["assessment_exclusion_reasons"]
    assert report["final_state"] == "hold_sample"
    assert report["runtime_effect"] is False


def test_spread_double_count_fails_closed() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    prediction["cost_inputs"] = _cost_inputs(includes_spread=True, spread_bps=3.0)
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=_calibration_rows(),
        traces=[_trace(prediction)],
        outcome_labels=[_outcome_label(prediction)],
    )

    row = report["ledger"][0]
    assert row["observer_assessment"] == "ABSTAIN"
    assert "entry_spread_cost_double_count" in row["assessment_exclusion_reasons"]
    assert report["final_state"] == "cost_model_incomplete"


def test_assumption_only_costs_remain_observable_but_block_sim_candidate() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    prediction["cost_inputs"]["cost_source_quality_status"] = "assumption_only"
    prediction["cost_inputs"]["assumption_flags"] = ["commission_assumed_zero"]
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=_calibration_rows(),
        traces=[_trace(prediction)],
        outcome_labels=[_outcome_label(prediction)],
    )

    assert report["ledger"][0]["cost"]["status"] == "complete"
    assert "cost_model_assumption_only" in report["summary"]["evaluation_blockers"]
    assert report["source_quality_and_exclusion_manifest"]["cost_warning_counts"] == {
        "cost_model_assumption_only": 1
    }
    assert report["final_state"] == "hold_sample"


def test_missing_odds_provenance_abstains_instead_of_raising() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    trace = _trace(prediction)
    outcome = _outcome_label(prediction)
    del prediction["odds_provenance"]

    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=_calibration_rows(),
        traces=[trace],
        outcome_labels=[outcome],
    )

    row = report["ledger"][0]
    assert row["observer_assessment"] == "ABSTAIN"
    assert "odds_provenance_missing" in row["assessment_exclusion_reasons"]
    assert "cost_model_version_missing" in row["assessment_exclusion_reasons"]


def test_same_bar_ambiguous_is_not_used_as_ev_or_calibration_truth() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=_calibration_rows(),
        traces=[_trace(prediction)],
        outcome_labels=[
            _outcome_label(
                prediction,
                first_hit="same_bar_ambiguous",
                end_return_pct=2.0,
            )
        ],
    )

    row = report["ledger"][0]
    assert row["outcome"]["market_path_label"] == AMBIGUOUS_OUTCOME
    assert row["observer_assessment"] == "WOULD_BET"
    assert row["evaluation_eligible"] is False
    assert row["counterfactual_net_return_pct"] is None
    assert "outcome_same_bar_ambiguous" in row["evaluation_exclusion_reasons"]
    assert report["summary"]["source_quality_adjusted_ev_pct"] is None
    assert report["calibration_updates"] == []


def test_negative_veto_reports_avoided_loss_and_one_share_krw_delta() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    prediction["payoff_bps"] = {
        "TARGET_FIRST": 10.0,
        "ADVERSE_FIRST": -100.0,
        "NEITHER_POSITIVE": 1.0,
        "NEITHER_NONPOSITIVE": -20.0,
    }
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=_calibration_rows(),
        traces=[_trace(prediction, action="BUY")],
        outcome_labels=[
            _outcome_label(
                prediction,
                first_hit="adverse_first",
                end_return_pct=-1.0,
            )
        ],
    )

    row = report["ledger"][0]
    veto = report["negative_veto_attribution"]
    assert row["observer_assessment"] == "WOULD_NO_BET"
    assert row["counterfactual_net_return_pct"] == -1.23
    assert row["counterfactual_net_profit_krw_one_share"] == -123.0
    assert veto["hypothetical_veto_count"] == 1
    assert veto["avoided_loser_count"] == 1
    assert veto["foregone_winner_count"] == 0
    assert veto["hypothetical_net_profit_delta_krw_one_share_reference"] == 123.0


def test_duplicate_predictions_are_all_excluded_from_evaluation() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction, dict(prediction)],
        calibration_rows=_calibration_rows(),
        traces=[_trace(prediction)],
        outcome_labels=[_outcome_label(prediction)],
    )

    assert report["summary"]["eligible_count"] == 0
    assert report["summary"]["assessment_counts"]["ABSTAIN"] == 2
    assert all(
        "duplicate_prediction_trace_id" in row["assessment_exclusion_reasons"]
        for row in report["ledger"]
    )


def test_calibration_must_be_strictly_prior_to_first_evaluation() -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    rows = _calibration_rows()
    for row in rows:
        row["decision_ts"] = prediction["decision_ts"]
    report = build_report(
        target_date="2026-08-06",
        predictions=[prediction],
        calibration_rows=rows,
        traces=[_trace(prediction)],
        outcome_labels=[_outcome_label(prediction)],
    )

    assert report["ledger"][0]["observer_assessment"] == "ABSTAIN"
    assert (
        report["source_quality_and_exclusion_manifest"]["calibration_exclusion_counts"][
            "calibration_not_strictly_prior"
        ]
        == 40
    )


def test_write_report_creates_json_and_markdown_with_private_permissions(
    tmp_path: Path,
) -> None:
    report = build_report(
        target_date="2026-08-06",
        predictions=[],
        calibration_rows=[],
        traces=[],
        outcome_labels=[],
        generated_at=datetime(2026, 8, 6, 20, 0, tzinfo=KST),
    )

    json_path, markdown_path = write_report(report, report_root=tmp_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["schema"] == (
        "entry_odds_observer_v1"
    )
    assert "counterfactual-only" in markdown_path.read_text(encoding="utf-8")
    assert json_path.stat().st_mode & 0o777 == 0o600
    assert markdown_path.stat().st_mode & 0o777 == 0o600


def test_cli_reads_exact_inputs_and_records_source_manifest(tmp_path: Path) -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    input_rows = {
        "predictions.jsonl": [prediction],
        "calibration.jsonl": _calibration_rows(),
        "trace.jsonl": [_trace(prediction)],
    }
    for name, rows in input_rows.items():
        (tmp_path / name).write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
    outcomes_path = tmp_path / "outcomes.json"
    outcomes_path.write_text(
        json.dumps({"labels": [_outcome_label(prediction)]}),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "--target-date",
                "2026-08-06",
                "--predictions",
                str(tmp_path / "predictions.jsonl"),
                "--calibration",
                str(tmp_path / "calibration.jsonl"),
                "--trace",
                str(tmp_path / "trace.jsonl"),
                "--outcomes",
                str(outcomes_path),
                "--report-root",
                str(tmp_path / "report"),
            ]
        )
        == 0
    )

    output = json.loads(
        (
            tmp_path
            / "report"
            / "entry_odds_observer"
            / "entry_odds_observer_2026-08-06.json"
        ).read_text(encoding="utf-8")
    )
    assert output["input_manifest"]["raw_predictions"]["row_count"] == 1
    assert output["input_manifest"]["raw_predictions"]["status"] == "present"
    assert len(output["input_manifest"]["raw_predictions"]["sha256"]) == 64


def test_cli_can_write_explicit_missing_odds_bootstrap_report(tmp_path: Path) -> None:
    prediction = _prediction(1, datetime(2026, 8, 6, 9, 0, tzinfo=KST))
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(json.dumps(_trace(prediction)) + "\n", encoding="utf-8")
    outcomes_path = tmp_path / "outcomes.json"
    outcomes_path.write_text(
        json.dumps({"labels": [_outcome_label(prediction)]}),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "--target-date",
                "2026-08-06",
                "--predictions",
                str(tmp_path / "missing_predictions.jsonl"),
                "--calibration",
                str(tmp_path / "missing_calibration.jsonl"),
                "--trace",
                str(trace_path),
                "--outcomes",
                str(outcomes_path),
                "--report-root",
                str(tmp_path / "report"),
                "--allow-missing-odds-inputs",
            ]
        )
        == 0
    )

    output = json.loads(
        (
            tmp_path
            / "report"
            / "entry_odds_observer"
            / "entry_odds_observer_2026-08-06.json"
        ).read_text(encoding="utf-8")
    )
    assert output["final_state"] == "hold_sample"
    assert output["source_quality_status"] == ("blocked_missing_offline_odds_input")
    assert output["source_quality_and_exclusion_manifest"]["required_input_gaps"] == [
        "raw_predictions",
        "calibration_history",
    ]
    assert output["input_manifest"]["raw_predictions"]["status"] == "missing"
    assert output["input_manifest"]["raw_predictions"]["sha256"] is None
    markdown = (
        tmp_path
        / "report"
        / "entry_odds_observer"
        / "entry_odds_observer_2026-08-06.md"
    ).read_text(encoding="utf-8")
    assert "blocked_missing_offline_odds_input" in markdown
    assert "missing_raw_predictions" in markdown
    assert "produce_exact_payload_raw_odds" in markdown
    assert "PREOPEN_runtime_selection" not in markdown
