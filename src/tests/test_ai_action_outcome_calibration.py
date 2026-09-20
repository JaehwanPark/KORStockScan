from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping.entry_setup_scalping_rollout import AUTO_PROMOTION_SCOPES

build_report = calibration.build_report


def _economic_row(index: int, ev: float = 0.4) -> dict:
    return {
        "decision_trace_id": f"economic-{index}",
        "stock_code": f"{index % 10:06d}",
        "control_action": "WAIT",
        "candidate_action": "BUY",
        "control_decision_value_pct": 0.0,
        "candidate_primary_decision_value_pct": ev,
        "delta_pct": ev,
        "candidate_execution_cost_contract_applied": True,
        "candidate_execution_cost_pct": 0.2,
        "candidate_probe_worst_loss_pct": -0.2,
        "outcome_return_pct": ev,
    }


def test_small_profit_opportunity_is_handed_off_without_changing_live_gate(tmp_path):
    from src.engine.scalping.micro_reversion import (
        main_ai_prompt_optimizer as optimizer,
    )

    row = _economic_row(1)
    row.update(
        {
            "candidate_action": "DROP",
            "candidate_error_taxonomy": ["false_drop_small_profit_execution_proxy"],
            "entry_small_profit_opportunity": {
                "schema": "entry_small_profit_opportunity_v1",
                "positive_target_first_after_execution_proxy": True,
            },
        }
    )
    path = (
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-08_small.json"
    )
    _write_json(path, {"target_date": "2026-09-08", "paired_comparisons": [row]})
    summary = build_report(target_date="2026-09-08", data_root=tmp_path)[
        "candidate_summaries"
    ][0]
    assert summary["small_profit_opportunity_diagnostic"]["candidate_missed_count"] == 1
    assert summary["false_drop_count"] == 0
    taxonomy = optimizer._error_taxonomy(
        [
            {
                "error_taxonomy_counts": summary["candidate_error_taxonomy_counts"],
            }
        ]
    )
    assert (
        taxonomy["candidate_patch_objectives"]["small_profit_opportunity_diagnostic"]
        == 1
    )


def test_partial_batch_retains_exact_learning_without_live_promotion(tmp_path):
    pairs = [_economic_row(i) for i in range(39)]
    payload = _valid_detailed_payload(
        {
            "target_date": "2026-09-07",
            "request_count": 40,
            "provider_failed_count": 1,
            "promotion_report_integrity_pass": False,
            "promotion_quality_gate_pass": False,
            "paired_comparisons": pairs,
        }
    )
    payload["calibration_source_contract"] = {
        "schema": "ai_paired_calibration_source_v1",
        "global_integrity_pass": True,
        "request_count": 40,
        "retained_pair_count": 39,
        "excluded_request_count": 1,
        "retained_pairs_sha256": calibration._canonical_sha256(
            payload["paired_comparisons"]
        ),
        "decision_authority": "calibration_learning_only",
        "runtime_apply_authority": False,
    }
    path = (
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_partial.json"
    )
    _write_json(path, payload)
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 39
    assert (
        candidate["diagnostic_checks_not_review_veto"]["provider_transport_clean"]
        is False
    )
    assert report["runtime_effect"] is False
    payload["calibration_source_contract"]["global_integrity_pass"] = False
    _write_json(path, payload)
    blocked = build_report(target_date="2026-09-07", data_root=tmp_path)
    assert blocked["candidate_count"] == 0
    assert blocked["source_contract_summary"]["rejection_reason_counts"] == {
        "calibration_source_contract_invalid": 1
    }


def test_conflict_exclusion_does_not_poison_remaining_clean_cohort(tmp_path):
    folder = tmp_path / "report" / calibration.PAIRED_SUBDIR
    for day, offset in (("2026-09-04", 0), ("2026-09-07", 20)):
        _write_json(
            folder / f"ai_prompt_detailed_paired_replay_{day}_clean.json",
            {
                "target_date": day,
                "paired_comparisons": [
                    _economic_row(i) for i in range(offset, offset + 20)
                ],
            },
        )
    for suffix, ev in (("a", 0.4), ("b", -0.4)):
        _write_json(
            folder
            / f"ai_prompt_detailed_paired_replay_2026-09-07_conflict_{suffix}.json",
            {
                "target_date": "2026-09-07",
                "paired_comparisons": [_economic_row(100, ev)],
            },
        )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 40
    assert candidate["conflicting_duplicate_trace_count"] == 1
    assert candidate["prompt_review_gate"]["blockers"] == []
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_two_thin_candidates_remain_diagnostic_without_runtime_handoff(tmp_path):
    folder = tmp_path / "report" / calibration.PAIRED_SUBDIR
    for i, ev in enumerate((0.1, 0.5)):
        _write_json(
            folder / f"ai_prompt_detailed_paired_replay_2026-09-07_v{i}.json",
            {
                "target_date": "2026-09-07",
                "requests": [{"candidate": {"prompt_version": f"v{i}"}}],
                "paired_comparisons": [_economic_row(i, ev)],
            },
        )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    assert report["thin_positive_review_candidate_count"] == 2
    assert calibration._artifact_content_sha256_valid(report)
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False


def test_runtime_review_route_never_reactivates_legacy_family():
    registered = calibration.runtime_review_route(
        "decision_quality_v2_14_setup_risk_adjudicator", "entry", "KRX", "KRX_REGULAR"
    )
    assert registered["owner"] == "entry_setup_live_policy"
    assert registered["runtime_apply_authority"] is False
    assert registered["legacy_main_ai_quality_family_available"] is False
    assert (
        calibration.runtime_review_route(
            "decision_quality_v2_6", "entry", "KRX", "KRX_REGULAR"
        )["status"]
        == "source_only_no_registered_runtime_route"
    )


@pytest.mark.parametrize("field", ["delta_pct", "candidate_primary_decision_value_pct"])
@pytest.mark.parametrize("invalid", [None, True, "NaN"])
def test_incomplete_economic_values_cannot_be_thin_positive(tmp_path, field, invalid):
    row = _economic_row(1)
    row["candidate_decision_value_pct"] = 0.6
    row[field] = invalid
    _write_json(
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_invalid.json",
        {"target_date": "2026-09-07", "paired_comparisons": [row]},
    )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["review_classification"] == "learning_only_or_rejected"
    assert (
        "paired_economic_values_complete" in candidate["prompt_review_gate"]["blockers"]
    )


@pytest.mark.parametrize("invalid", [None, True, "NaN", -0.1])
def test_missing_or_invalid_cost_not_assumed_zero_for_review(tmp_path, invalid):
    row = _economic_row(1)
    row["candidate_execution_cost_pct"] = invalid
    _write_json(
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_cost.json",
        {"target_date": "2026-09-07", "paired_comparisons": [row, _economic_row(2)]},
    )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 1
    assert candidate["probe_cost_contract_complete"] is True
    assert report["source_contract_summary"]["row_exclusion_count"] == 1
    assert report["source_reports"][0]["row_exclusion_reason_counts"] == {
        "exposure_execution_cost_missing_or_invalid": 1
    }
    assert candidate["review_classification"] == "thin_positive_review"


def test_calibration_rejects_target_before_clean_baseline(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="target_date_before_clean_baseline"):
        build_report(target_date="2026-06-04", data_root=tmp_path)


def _write_json(path: Path, payload: dict) -> None:
    if path.name.startswith("ai_prompt_detailed_paired_replay_"):
        payload = _valid_detailed_payload(payload)
    elif path.name.startswith("ai_decision_action_outcome_calibration_"):
        payload = _valid_prior_calibration_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _valid_detailed_payload(payload: dict) -> dict:
    value = json.loads(json.dumps(payload))
    source_date = str(value.get("target_date") or "2026-07-29")
    requests = value.setdefault(
        "requests", [{"candidate": {"prompt_version": "candidate_v1"}}]
    )
    candidate = requests[0].setdefault("candidate", {})
    candidate_version = str(candidate.get("prompt_version") or "candidate_v1")
    candidate["prompt_version"] = candidate_version
    candidate.setdefault("system_prompt_sha256", "a" * 64)
    candidate.setdefault("contract_sha256", "b" * 64)
    contract_sha256 = candidate["contract_sha256"]
    rows = value.setdefault("paired_comparisons", [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        row.setdefault("stage", "entry")
        row.setdefault("effective_venue", "KRX")
        row.setdefault("session_bucket", "KRX_REGULAR")
        row.setdefault("decision_ts", f"{source_date}T10:00:00+09:00")
        row.setdefault(
            "outcome_return_pct", row.get("candidate_primary_decision_value_pct", 0.0)
        )
    value.setdefault("schema", calibration.DETAILED_PAIRED_SCHEMA)
    value.setdefault("runtime_effect", False)
    value.setdefault("allowed_runtime_apply", False)
    value.setdefault("actual_order_submitted", False)
    value.setdefault("broker_order_forbidden", True)
    value.setdefault("promotion_report_integrity_pass", True)
    value.setdefault("paired_comparable_count", len(rows))
    value.setdefault("schema_rejected_count", 0)
    value.setdefault("provider_failed_count", 0)
    value.setdefault("candidate_provider_none_count", 0)
    value.setdefault("candidate_contract_sha256", contract_sha256)
    value.setdefault(
        "promotion_cohort_scope",
        {
            "stages": ["entry"],
            "effective_venues": ["KRX"],
            "session_buckets": ["KRX_REGULAR"],
            "isolated": True,
            "candidate_contract_sha256": contract_sha256,
            "candidate_contract_isolated": True,
            "cross_cohort_promotion_forbidden": True,
        },
    )
    value.setdefault(
        "cohort_filter",
        {
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "runtime_effect": False,
        },
    )
    value.setdefault(
        "cumulative_learning",
        {
            "candidate_prompt_version": candidate_version,
            "candidate_contract_sha256": contract_sha256,
            "as_of_date": source_date,
            "clean_tuning_baseline_date": calibration.CLEAN_BASELINE_DATE,
        },
    )
    value.pop("artifact_content_sha256", None)
    return calibration._with_artifact_content_sha256(value)


def _valid_prior_calibration_payload(payload: dict) -> dict:
    value = json.loads(json.dumps(payload))
    value.setdefault("schema", calibration.SCHEMA)
    value.setdefault("policy_version", calibration.POLICY_VERSION)
    value.setdefault("runtime_effect", False)
    value.setdefault("runtime_authority", False)
    value.setdefault("order_authority", False)
    value.setdefault("provider_authority", False)
    value.setdefault("allowed_runtime_apply", False)
    value.setdefault("actual_order_submitted", False)
    value.setdefault("broker_order_forbidden", True)
    ledger = value.setdefault("ofi_action_outcome_calibration", {})
    ledger.setdefault("schema", calibration.OFI_LEDGER_SCHEMA)
    value.pop("artifact_content_sha256", None)
    return calibration._with_artifact_content_sha256(value)


def _hierarchy_training_rows():
    from src.engine.scalping import entry_setup_evidence as evidence

    rows = []
    dates = [
        "2026-09-07",
        "2026-09-08",
        "2026-09-09",
        "2026-09-10",
        "2026-09-11",
        "2026-09-14",
        "2026-09-15",
    ]
    parts = {
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "price_tick_band": "P1",
        "volatility_band": "V1",
    }
    for day in dates:
        for i in range(4):
            setup = _mechanistic_evidence()
            setup.update(
                setup_state="WAIT_CONFIRMATION",
                micro_recovery_observation={
                    "source_usable": True,
                    "net_aggressive_delta_10t": 20,
                    "price_change_10t_pct": 0.1,
                },
            )
            context = {
                "symbol": "005930",
                "group": {"key_parts": parts},
                "flow": {"matched_families": ["DEPTH_SUPPORTED_STAIRCASE"]},
                "micro_window": None,
            }
            setup["mechanistic_context"] = {
                **context,
                "context_sha256": evidence._canonical_sha256(context),
            }
            rows.append(
                {
                    "decision_trace_id": f"{day}-{i}",
                    "decision_ts": f"{day}T10:{i * 10:02d}:00+09:00",
                    "source_date": day,
                    "stock_code": "005930",
                    "setup_evidence": setup,
                    "entry_group_observation": context["group"],
                    "entry_group_contract_valid": True,
                    "mechanistic_flow_observation": context["flow"],
                    "mechanistic_flow_observation_contract_valid": True,
                    "entry_quality_path": {
                        "status": "evaluable",
                        "entry_quality_label": "CLEAN_FAST_PROFIT",
                        "conservative_execution_cost_pct": 0.2,
                    },
                    "entry_quality_contract_valid": True,
                    "source_provenance_verified": True,
                    "source_report_hash_verified": True,
                    "comparison": {
                        "entry_cost_contract": {
                            "schema": "entry_round_trip_cost_v1",
                            "source_date": day,
                            "effective_venue": "KRX",
                            "session_bucket": "KRX_REGULAR",
                            "basis": "source_bound_estimate",
                            "source_sha256": "a" * 64,
                            "components_pct": {
                                "buy_fee": 0.01,
                                "sell_fee": 0.01,
                                "sell_tax": 0.15,
                                "slippage": 0.03,
                            },
                        },
                        "control_action": "WAIT",
                        "entry_path_first_hit": "target_first",
                        "entry_path_target_pct": 0.5,
                        "entry_path_adverse_pct": -1.0,
                        "conservative_execution_cost_pct": 0.2,
                    },
                }
            )
    return rows


def test_hierarchy_nxt_fit_is_not_a_krx_candidate():
    import copy
    from src.engine.scalping import entry_setup_evidence as evidence

    rows = copy.deepcopy(_hierarchy_training_rows())
    cohort = ("NXT", "NXT_AFTERMARKET")
    for row in rows:
        parts = row["entry_group_observation"]["key_parts"]
        parts.update(venue=cohort[0], session_bucket=cohort[1])
        context = row["setup_evidence"]["mechanistic_context"]
        context["group"]["key_parts"] = parts
        context["context_sha256"] = evidence._canonical_sha256(
            {k: v for k, v in context.items() if k != "context_sha256"}
        )
        row["comparison"]["entry_cost_contract"].update(
            effective_venue=cohort[0], session_bucket=cohort[1]
        )
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15", cohort=cohort
    )
    assert result["promotion_pass"] is True
    assert (
        calibration.validate_hierarchy_candidate(
            result, source_date="2026-09-15", cohort=cohort
        )
        == []
    )
    assert "candidate_cohort_invalid" in calibration.validate_hierarchy_candidate(
        result, source_date="2026-09-15"
    )
    assert (
        calibration.build_mechanistic_hierarchy_candidate(
            rows, target_date="2026-09-15"
        )["source_count"]
        == 0
    )
    for row in rows:
        row["comparison"]["entry_cost_contract"]["effective_venue"] = "KRX"
    assert (
        calibration.build_mechanistic_hierarchy_candidate(
            rows, target_date="2026-09-15", cohort=cohort
        )["source_count"]
        == 0
    )


def test_hierarchy_fits_groups_and_never_uses_pre_freeze_dates_as_holdout():
    rows = _hierarchy_training_rows()
    prior = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-11"
    )
    assert prior["policy_candidate"] is None
    assert prior["holdout_dates"] == []
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15"
    )
    assert result["promotion_pass"] is True
    assert (
        calibration.validate_hierarchy_candidate(result, source_date="2026-09-15") == []
    )
    assert result["calibration_dates"][-1] == "2026-09-11"
    candidate = result["policy_candidate"]
    assert candidate["threshold_policy"]["hierarchy"]["rules"]
    for r in rows:
        if r["source_date"] > "2026-09-11":
            r["entry_quality_path"]["entry_quality_label"] = "PROFIT_AFTER_DEEP_ADVERSE"
    rejected = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15"
    )
    assert rejected["policy_candidate"] is None
    assert rejected["evaluations"][0]["rule"] == result["evaluations"][0]["rule"]


def test_hierarchy_excludes_overlap_and_future_rows():
    rows = _hierarchy_training_rows()
    extra = dict(
        rows[0], decision_trace_id="repeat", decision_ts="2026-09-07T10:00:10+09:00"
    )
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows + [extra], target_date="2026-09-15"
    )
    assert result["excluded"]["duplicate_or_overlapping_anchor"] == 1


def test_hierarchy_never_promotes_half_spread_only_cost_as_net_ev():
    rows = _hierarchy_training_rows()
    for row in rows:
        row["comparison"].pop("entry_cost_contract")
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15"
    )
    assert result["policy_candidate"] is None
    assert result["excluded"]["full_cost_or_relabel_required"] == len(rows)


def test_machine_capture_matures_with_existing_cost_owner_without_ai(
    monkeypatch, tmp_path
):
    from datetime import datetime, timedelta
    from src.engine.scalping import (
        ai_decision_quality as quality,
        ai_decision_trace as trace,
    )
    from src.tests.test_ai_decision_trace import _enable
    from src.tests.test_entry_setup_evidence import _hierarchy_case

    _enable(monkeypatch, tmp_path)
    day = "2026-09-14"
    now = datetime.fromisoformat(day + "T10:00:00+09:00")
    monkeypatch.setattr(trace, "_now", lambda: now)
    setup = _hierarchy_case()[0]
    profile = {
        "profile_id": "reviewed",
        "economic_source_sha256": "a" * 64,
        "buy_fee_bps": 1,
        "sell_fee_bps": 1,
        "statutory_sell_tax_bps": 15,
        "uncertainty_buffer_bps": 1,
    }
    monkeypatch.setattr(
        calibration,
        "_hierarchy_cost_profiles",
        lambda root, d, venue="KRX": {"005930": profile},
    )
    prices = [
        {
            "stock_code": "005930",
            "timestamp": (now + timedelta(seconds=i * 30)).isoformat(),
            "price": 10050,
            "high": 10055,
            "low": 10000,
            "close": 10050,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass",
        }
        for i in range(1, 21)
    ]
    monkeypatch.setattr(
        quality,
        "load_pipeline_price_and_lifecycle_rows",
        lambda *args, **kwargs: (prices, []),
    )
    capture = trace.capture_machine_observation(
        exact_payload={
            "stock_code": "005930",
            "name": "삼성전자",
            "best_ask": 10000,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "conservative_execution_cost_pct": 0.02,
        },
        setup_evidence=setup,
        assessment={"action": "RECHECK"},
        bundle_sha256="b" * 64,
    )
    assert capture["machine_capture_status"] == "captured"
    rows, census = calibration.load_machine_observation_rows(tmp_path, target_date=day)
    assert census["captured"] == 1
    assert census["evaluable"] == 1
    assert census["machine_snapshot_id_missing"] == 1
    assert census["pipeline_lifecycle_unresolved"] == 1
    assert len(rows) == 1
    assert rows[0]["comparison"]["conservative_execution_cost_pct"] == pytest.approx(
        0.20
    )
    assert rows[0]["exit_cohort"] == "existing_fixed_boundary_counterfactual"
    assert rows[0]["machine_observation_hash_verified"] is True
    assert rows[0]["entry_quality_path"][
        "conservative_execution_cost_pct"
    ] == pytest.approx(0.20)
    assert rows[0]["machine_action"] == "RECHECK"


def test_machine_capture_normalizes_runtime_session_for_scope_lookup(
    monkeypatch, tmp_path
):
    from datetime import datetime, timedelta
    from src.engine.scalping import (
        ai_decision_quality as quality,
        ai_decision_trace as trace,
    )
    from src.tests.test_ai_decision_trace import _enable
    from src.tests.test_entry_setup_evidence import _hierarchy_case

    _enable(monkeypatch, tmp_path)
    day = "2026-09-14"
    now = datetime.fromisoformat(day + "T10:00:00+09:00")
    monkeypatch.setattr(trace, "_now", lambda: now)
    profile = {
        "profile_id": "reviewed",
        "economic_source_sha256": "a" * 64,
        "buy_fee_bps": 1,
        "sell_fee_bps": 1,
        "statutory_sell_tax_bps": 15,
        "uncertainty_buffer_bps": 1,
    }
    monkeypatch.setattr(
        calibration,
        "_hierarchy_cost_profiles",
        lambda root, d, venue="KRX": {"005930": profile},
    )
    prices = [
        {
            "stock_code": "005930",
            "timestamp": (now + timedelta(seconds=i * 30)).isoformat(),
            "price": 10050,
            "high": 10055,
            "low": 10000,
            "close": 10050,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass",
        }
        for i in range(1, 21)
    ]
    monkeypatch.setattr(
        quality,
        "load_pipeline_price_and_lifecycle_rows",
        lambda *args, **kwargs: (prices, []),
    )
    setup = _hierarchy_case()[0]
    capture = trace.capture_machine_observation(
        exact_payload={
            "stock_code": "005930",
            "name": "Samsung Electronics",
            "best_ask": 10000,
            "effective_venue": "KRX",
            # This is the actual casing persisted by _request_context.
            "session_bucket": "krx_regular",
            "conservative_execution_cost_pct": 0.02,
        },
        setup_evidence=setup,
        assessment={"action": "RECHECK"},
        bundle_sha256="b" * 64,
    )
    assert capture["machine_capture_status"] == "captured"

    rows, census = calibration.load_machine_observation_rows(tmp_path, target_date=day)

    assert census["captured"] == 1
    assert census["evaluable"] == 1
    assert len(rows) == 1
    assert rows[0]["comparison"]["entry_cost_contract"]["session_bucket"] == (
        "KRX_REGULAR"
    )


def test_machine_decision_case_table_separates_missed_and_bad_entry_timing():
    def row(
        action,
        label,
        trace_id,
        *,
        second=0,
        hierarchy=None,
        attempt_id=None,
    ):
        return {
            "decision_trace_id": trace_id,
            "evaluation_attempt_id": attempt_id or trace_id,
            "scanner_promotion_id": f"SCANPROM-{attempt_id or trace_id}",
            "evaluation_attempt_identity_source": "exact_market_snapshot",
            "decision_snapshot_id": f"snapshot-{trace_id}",
            "decision_ts": f"2026-09-14T12:00:{second:02d}+09:00",
            "source_date": "2026-09-14",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "bundle_sha256": "a" * 64,
            "machine_action": action,
            "machine_reason": "fixture",
            "machine_hierarchy_selection": hierarchy or {"level": "common"},
            "outcome_horizon_metrics": {
                "10m": {
                    "entry_quality_status": "evaluable",
                    "entry_quality_label": label,
                }
            },
            "ai_and_final_guard": {
                "join_status": "ai_trace_missing_for_exact_snapshot"
            },
            "entry_quality_path": {
                "status": "evaluable",
                "entry_quality_label": label,
                "gross_net_target_pct": 0.33,
                "time_to_net_target_sec": 30,
                "time_to_exact_stop_sec": None,
                "pre_target_mae_pct": -0.1,
                "pre_target_underwater_ratio": 0.2,
                "pre_target_neutral_dwell_ratio": 0.1,
                "checkpoints": [],
                "path_authority": "counterfactual_completed_bar_touch_not_actual_fill",
            },
        }

    report = calibration.build_machine_decision_case_table(
        [
            row("BLOCK", "CLEAN_FAST_PROFIT", "missed"),
            row("ENTER_NOW", "CLEAN_FAST_LOSS_OR_ADVERSE", "bad-enter"),
            row(
                "RECHECK",
                "CLEAN_FAST_LOSS_OR_ADVERSE",
                "good-recheck",
                hierarchy={"level": "group", "rule_id": "flow-rule-1"},
            ),
            row(
                "RECHECK",
                "CLEAN_FAST_LOSS_OR_ADVERSE",
                "good-recheck",
                second=30,
                hierarchy={"level": "group", "rule_id": "flow-rule-1"},
                attempt_id="good-recheck",
            ),
        ],
        capture_census={"captured": 4, "evaluable": 4},
        source_receipt={
            "schema": "machine_ai_natural_source_consumption_v1",
            "status": "pass",
            "source_manifest_sha256": "d" * 64,
            "tuning_input_allowed": True,
            "machine_threshold_tuning_input_allowed": True,
        },
    )

    assert report["status"] == "evaluable"
    assert report["input_evaluable_observation_count"] == 4
    assert report["case_count"] == 3
    assert report["duplicate_same_action_collapsed_count"] == 1
    assert report["machine_action_counts"] == {
        "BLOCK": 1,
        "ENTER_NOW": 1,
        "RECHECK": 1,
    }
    assert report["case_classification_counts"] == {
        "correct_avoidance_candidate": 1,
        "false_positive_entry_candidate": 1,
        "missed_opportunity_candidate": 1,
    }
    assert report["hierarchy_selection_counts"] == {
        "common": 2,
        "group": 1,
    }
    assert report["compact_auxiliary_screen_outcomes"]["screened_enter_now_count"] == 0
    assert (
        report["compact_auxiliary_screen_outcomes"]["prompt_body_tuning"]
        == "bounded_automatic_versioned_successor_enabled"
    )
    assert (
        report["compact_auxiliary_screen_outcomes"]["automatic_successor_selection"][
            "eligible"
        ]
        is False
    )
    assert report["observed_selected_child_rule_ids"] == ["flow-rule-1"]
    assert report["legacy_60_second_same_action_collapse_disabled"] is True
    assert report["conflicting_attempt_identity_count"] == 0
    assert report["policy_learning_eligible_observation_count"] == 3
    assert report["machine_ai_populations_are_separate"] is True


def test_machine_case_table_preserves_but_excludes_unresolved_terminal_lineage():
    row = {
        "decision_trace_id": "trace-1",
        "evaluation_attempt_id": "attempt-1",
        "scanner_promotion_id": "promotion-1",
        "decision_ts": "2026-09-15T10:00:00+09:00",
        "source_date": "2026-09-15",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "bundle_sha256": "a" * 64,
        "machine_action": "ENTER_NOW",
        "machine_reason": "fixture",
        "machine_hierarchy_selection": {"level": "common"},
        "entry_quality_path": {
            "status": "evaluable",
            "entry_quality_label": "CLEAN_FAST_PROFIT",
            "conservative_execution_cost_pct": 0.23,
            "gross_net_target_pct": 0.5,
            "first_hit": "net_target_first",
        },
        "ai_and_final_guard": {},
    }
    key = calibration._machine_evaluation_key(row)

    report = calibration.build_machine_decision_case_table(
        [row],
        capture_census={"captured": 1, "evaluable": 1},
        source_receipt={
            "tuning_input_allowed": True,
            "machine_threshold_tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {
                "excluded_evaluation_keys": [key],
                "denominator_preserved": True,
                "economic_tuning_input_allowed": True,
            },
        },
    )

    assert report["case_count"] == 1
    assert report["policy_learning_eligible_observation_count"] == 0
    assert report["terminal_lineage_exclusion"]["excluded_case_count"] == 1
    assert report["rows"][0]["policy_learning_excluded"] is True
    assert report["rows"][0]["policy_learning_exclusion_reason"] == (
        "terminal_lineage_unresolved"
    )


def test_machine_case_table_uses_machine_specific_source_gate_for_learning():
    row = {
        "decision_trace_id": "trace-1",
        "evaluation_attempt_id": "attempt-1",
        "decision_snapshot_id": "snapshot-1",
        "decision_ts": "2026-09-14T12:00:00+09:00",
        "source_date": "2026-09-14",
        "stock_code": "005930",
        "scanner_promotion_id": "SCANPROM-snapshot-series",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "bundle_sha256": "a" * 64,
        "machine_action": "RECHECK",
        "machine_hierarchy_selection": {"level": "common"},
        "entry_quality_path": {
            "status": "evaluable",
            "entry_quality_label": "CLEAN_FAST_PROFIT",
        },
        "outcome_horizon_metrics": {},
        "ai_and_final_guard": {"join_status": "exact_snapshot_machine_action_join"},
    }
    report = calibration.build_machine_decision_case_table(
        [row],
        source_receipt={
            "tuning_input_allowed": True,
            "machine_threshold_tuning_input_allowed": False,
            "machine_threshold_tuning_blocked_reason": (
                "machine_attempt_conservation_gap"
            ),
        },
    )

    assert report["case_count"] == 1
    assert report["policy_learning_eligible_observation_count"] == 0


def test_machine_source_receipt_propagates_machine_conservation_gate(tmp_path):
    day = "2026-09-14"
    path = (
        tmp_path
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "machine_ai_natural_source_consumption": {
                    "schema": "machine_ai_natural_source_consumption_v1",
                    "status": "warning_machine_assessment_contract_invalid",
                    "source_manifest": {"source_manifest_sha256": "a" * 64},
                    "tuning_input_allowed": True,
                    "machine_attempt_conservation": {
                        "unaccounted_trace_count": 1,
                        "denominator_preserved": False,
                    },
                    "machine_threshold_tuning_input_allowed": False,
                    "machine_threshold_tuning_blocked_reason": (
                        "machine_attempt_conservation_gap"
                    ),
                }
            }
        ),
        encoding="utf-8",
    )

    receipt = calibration._machine_ai_natural_source_receipt(tmp_path, day)

    assert receipt["tuning_input_allowed"] is True
    assert receipt["machine_threshold_tuning_input_allowed"] is False
    assert receipt["machine_attempt_conservation"]["denominator_preserved"] is False


def test_compact_screen_conserves_caution_and_not_evaluated_without_veto():
    from src.engine.ai_prompt_contracts import (
        ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
    )

    def row(trace_id: str, *, provider_called: bool, verdict: str):
        return {
            "decision_trace_id": trace_id,
            "evaluation_attempt_id": trace_id,
            "decision_snapshot_id": trace_id,
            "decision_ts": "2026-09-14T12:00:00+09:00",
            "source_date": "2026-09-14",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "bundle_sha256": "a" * 64,
            "machine_action": "ENTER_NOW",
            "machine_hierarchy_selection": {"level": "common"},
            "entry_quality_path": {
                "status": "evaluable",
                "entry_quality_label": "CLEAN_FAST_PROFIT",
                "conservative_execution_cost_pct": 0.23,
                "first_hit": "net_target_first",
                "gross_net_target_pct": 0.4,
            },
            "outcome_horizon_metrics": {},
            "ai_and_final_guard": {
                "provider_called": provider_called,
                "prompt_version": ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
                "ai_risk_verdict": verdict,
                "decision_quality_contract_status": "pass",
                "semantic_validation_status": "pass",
            },
        }

    report = calibration.build_machine_decision_case_table(
        [
            row("caution", provider_called=True, verdict="CAUTION"),
            row("not-evaluated", provider_called=False, verdict=""),
        ],
        source_receipt={
            "tuning_input_allowed": True,
            "machine_threshold_tuning_input_allowed": True,
            "compact_auxiliary_policy_measurement": {
                "prompt_version": ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
                "measurement_allowed": True,
            },
        },
    )["compact_auxiliary_screen_outcomes"]

    assert report["terminal_verdict_counts"] == {"CAUTION": 1}
    assert report["screen_attempt_conservation"] == {
        "expected_enter_now_count": 2,
        "terminal_classified_count": 2,
        "provider_called_count": 1,
        "provider_not_called_count": 1,
        "denominator_preserved": True,
        "not_evaluated_is_not_veto": True,
    }
    assert report["all_machine_enter_ai_routing"] == {
        "machine_enter_now_count": 2,
        "routing_counts": {"current_compact_prompt": 2},
        "denominator_preserved": True,
        "mixed_prompt_generations_are_not_merged": True,
    }
    assert report["economic_contract"]["economic_eligible_count"] == 0
    assert report["economic_contract"]["exclusion_counts"] == {
        "bounded_recheck_nonexposure_unproven": 1,
        "provider_not_called": 1,
    }


def _compact_router_case_table(*, verdict="CAUTION", submitted=False, disposition="ai_caution_bounded_recheck", adverse_count=0, decision_gate=True):
    from src.engine.scalping.mechanistic_entry_runtime_policy import AI_VERSION
    rows = [{
        "decision_trace_id": f"router-trace-{index}",
        "evaluation_attempt_id": f"router-attempt-{index}",
        "scanner_promotion_id": f"promotion-{index}",
        "decision_snapshot_id": f"snapshot-{index}",
        "decision_ts": f"2026-09-15T12:00:{index:02d}+09:00",
        "source_date": "2026-09-15", "stock_code": "005930",
        "effective_venue": "KRX", "session_bucket": "KRX_REGULAR",
        "bundle_sha256": "a" * 64, "machine_action": "ENTER_NOW",
        "entry_quality_path": {
            "status": "evaluable", "entry_quality_label": "CLEAN_FAST_PROFIT",
            "conservative_execution_cost_pct": 0.23,
            "first_hit": "net_target_first", "gross_net_target_pct": 0.30,
        },
        "ai_and_final_guard": {
            "provider_called": True, "prompt_version": AI_VERSION,
            "ai_risk_verdict": verdict, "decision_quality_contract_status": "pass",
            "semantic_validation_status": "pass", "followup_disposition": disposition,
            "observed_actual_order_submitted": submitted,
        },
    } for index in range(20)]
    for row in rows[:adverse_count]:
        row["entry_quality_path"].update(
            entry_quality_label="CLEAN_FAST_LOSS_OR_ADVERSE", first_hit="exact_stop_first",
            exact_stop_distance_pct=-0.70,
        )
    receipt = {
        "target_date": "2026-09-15", "source_manifest_sha256": "d" * 64,
        "tuning_input_allowed": True,
        "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": decision_gate},
        "compact_auxiliary_policy_measurement": {"prompt_version": AI_VERSION, "measurement_allowed": True},
    }
    return calibration.build_machine_decision_case_table(rows, source_receipt=receipt)


@pytest.mark.parametrize("submitted,disposition", [
    (False, "ai_caution_bounded_recheck"),
    (True, "ai_caution_bounded_recheck"),
    (None, "ai_caution_bounded_recheck"),
    (False, "ai_pass_existing_submit_guard"),
])
def test_compact_caution_opportunity_cost_preserves_router_nonexposure(submitted, disposition):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    table = _compact_router_case_table(submitted=submitted, disposition=disposition)
    outcomes = table["compact_auxiliary_screen_outcomes"]
    economic, selection = outcomes["economic_contract"], outcomes["automatic_successor_selection"]
    allowed = submitted is False and disposition == "ai_caution_bounded_recheck"
    assert economic["denominator_preserved"] is True
    assert outcomes["terminal_verdict_counts"] == {"CAUTION": 20}
    assert economic["evaluable_veto_count"] == 0
    assert economic["economic_eligible_count"] == (20 if allowed else 0)
    assert economic["evaluable_caution_count"] == (20 if allowed else 0)
    assert economic["missed_profit_caution_count"] == (20 if allowed else 0)
    assert economic["missed_profit_caution_net_sum_pct"] == pytest.approx(1.4 if allowed else 0)
    assert economic["caution_is_not_veto"] is True
    assert economic["screened_policy_counterfactual_net_ev_pct"] == (0 if allowed else None)
    assert policy.compact_outcome_counts_valid(economic)
    assert selection["eligible"] is allowed
    assert selection["selected_prompt_version"] == (policy.ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION if allowed else policy.AI_VERSION)
    if allowed:
        corrupted = json.loads(json.dumps(economic))
        corrupted["missed_profit_caution_count"] -= 1
        assert not policy.compact_outcome_counts_valid(corrupted)
        assert policy.compact_economic_direction(corrupted) == "carry_balanced_compact_contract"


def test_compact_insufficient_is_source_repair_not_opportunity_policy_training():
    table = _compact_router_case_table(verdict="INSUFFICIENT", disposition="ai_insufficient_bounded_recheck")
    outcomes = table["compact_auxiliary_screen_outcomes"]
    assert outcomes["economic_contract"]["economic_eligible_count"] == 0
    assert outcomes["economic_contract"]["exclusion_counts"] == {"source_gap_router_verdict": 20}
    assert outcomes["automatic_successor_selection"]["eligible"] is False


def test_compact_caution_avoided_losses_prevent_one_sided_relaxation():
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    outcomes = _compact_router_case_table(adverse_count=15)["compact_auxiliary_screen_outcomes"]
    economic = outcomes["economic_contract"]
    assert economic["missed_profit_caution_count"] == 5
    assert economic["missed_profit_caution_net_sum_pct"] == pytest.approx(0.35)
    assert economic["avoided_nonentry_loss_sum_pct"] == pytest.approx(13.95)
    assert outcomes["automatic_successor_selection"]["eligible"] is True
    assert outcomes["automatic_successor_selection"]["selected_prompt_version"] == policy.AI_VERSION


@pytest.mark.parametrize("corruption", [None, "count", "nan_amount", "terminal_gate"])
def test_router_economic_contract_is_rechecked_by_its_owner(tmp_path, corruption):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    report = calibration.build_report(target_date="2026-09-15", data_root=tmp_path)
    table = _compact_router_case_table(decision_gate=corruption != "terminal_gate")
    economic = table["compact_auxiliary_screen_outcomes"]["economic_contract"]
    if corruption == "count":
        economic["evaluable_caution_count"] -= 1
    elif corruption == "nan_amount":
        economic["missed_profit_caution_net_sum_pct"] = float("nan")
    assert (not policy.compact_outcome_counts_valid(economic)) is (
        corruption in {"count", "nan_amount"}
    )


def test_compact_machine_horizons_preserve_pending_or_source_gap():
    horizons = calibration._compact_machine_horizon_metrics(
        {"10m": {"sample_count": 2, "mfe_pct": 0.3}}
    )

    assert set(horizons) == {"1m", "3m", "5m", "10m", "20m", "30m", "60m"}
    assert horizons["10m"]["status"] == "observed"
    assert horizons["1m"]["status"] == "pending_or_source_gap"


def test_machine_case_table_automatically_selects_bounded_compact_variant():
    from src.engine.ai_prompt_contracts import (
        ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION,
    )
    from src.engine.scalping.mechanistic_entry_runtime_policy import AI_VERSION

    rows = []
    for index in range(20):
        verdict = "VETO" if index < 5 else "PASS"
        label = "CLEAN_FAST_PROFIT" if index != 5 else "CLEAN_FAST_LOSS_OR_ADVERSE"
        rows.append(
            {
                "decision_trace_id": f"trace-{index}",
                "evaluation_attempt_id": f"attempt-{index}",
                "scanner_promotion_id": "promotion-fixture",
                "decision_snapshot_id": f"snapshot-{index}",
                "decision_ts": f"2026-09-14T12:00:{index:02d}+09:00",
                "source_date": "2026-09-14",
                "stock_code": f"{index:06d}",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "bundle_sha256": "a" * 64,
                "machine_action": "ENTER_NOW",
                "machine_reason": "fixture",
                "machine_hierarchy_selection": {"level": "common"},
                "entry_quality_path": {
                    "status": "evaluable",
                    "entry_quality_label": label,
                    "conservative_execution_cost_pct": 0.23,
                    "first_hit": (
                        "exact_stop_first"
                        if label == "CLEAN_FAST_LOSS_OR_ADVERSE"
                        else "net_target_first"
                    ),
                    "gross_net_target_pct": 0.30,
                    "exact_stop_distance_pct": -0.70,
                },
                "ai_and_final_guard": {
                    "provider_called": True,
                    "prompt_version": AI_VERSION,
                    "ai_risk_verdict": verdict,
                    "decision_quality_contract_status": "pass",
                    "semantic_validation_status": "pass",
                },
            }
        )

    report = calibration.build_machine_decision_case_table(
        rows,
        capture_census={"captured": 20, "evaluable": 20},
        source_receipt={
            "target_date": "2026-09-14",
            "tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": True},
            "compact_auxiliary_policy_measurement": {
                "prompt_version": AI_VERSION,
                "measurement_allowed": True,
            },
        },
    )

    selection = report["compact_auxiliary_screen_outcomes"][
        "automatic_successor_selection"
    ]
    assert selection["eligible"] is True
    assert selection["minimum_economic_eligible_count"] == 20
    assert selection["contract_version"] == "compact_auxiliary_router_economic_selection_v3"
    # The same exact source is evaluable on an all-VETO day, with no actual
    # submit/fill prerequisites. Do not relax partition or cost/path gates.
    all_veto = json.loads(json.dumps(rows))
    for item in all_veto:
        item["ai_and_final_guard"]["ai_risk_verdict"] = "VETO"
        item["scanner_promotion_id"] = "promotion-fixture"
        item["source_date"] = "2026-09-15"
    veto_receipt = {
        "target_date": "2026-09-15",
        "tuning_input_allowed": True,
        "machine_terminal_tuning_gate": {
            "economic_tuning_input_allowed": False,
            "decision_counterfactual_tuning_input_allowed": True,
        },
        "compact_auxiliary_policy_measurement": {
            "prompt_version": AI_VERSION,
            "measurement_allowed": True,
        },
    }
    veto_report = calibration.build_machine_decision_case_table(
        all_veto, source_receipt=veto_receipt
    )["compact_auxiliary_screen_outcomes"]
    assert veto_report["economic_contract"]["economic_eligible_count"] == 20
    assert veto_report["automatic_successor_selection"]["eligible"] is True
    veto_receipt["machine_terminal_tuning_gate"][
        "decision_counterfactual_tuning_input_allowed"
    ] = False
    veto_receipt["machine_terminal_tuning_gate"]["economic_tuning_input_allowed"] = True
    veto_blocked = calibration.build_machine_decision_case_table(
        all_veto, source_receipt=veto_receipt
    )["compact_auxiliary_screen_outcomes"]
    assert veto_blocked["automatic_successor_selection"]["eligible"] is False
    # Five missed 0.07% opportunities do not outweigh one 0.93% loss.
    assert selection["selected_prompt_version"] == AI_VERSION
    rows[5]["entry_quality_path"]["exact_stop_distance_pct"] = -0.01
    profitable = calibration.build_machine_decision_case_table(
        rows,
        capture_census={"captured": 20, "evaluable": 20},
        source_receipt={
            "target_date": "2026-09-14",
            "tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": True},
            "compact_auxiliary_policy_measurement": {
                "prompt_version": AI_VERSION,
                "measurement_allowed": True,
            },
        },
    )["compact_auxiliary_screen_outcomes"]
    assert (
        profitable["automatic_successor_selection"]["selected_prompt_version"]
        == ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION
    )
    rows[5]["entry_quality_path"]["exact_stop_distance_pct"] = -0.70
    assert selection["allowed_runtime_apply"] is True

    rows[0]["ai_and_final_guard"][
        "decision_quality_contract_status"
    ] = "semantic_rejected"
    blocked = calibration.build_machine_decision_case_table(
        rows,
        capture_census={"captured": 20, "evaluable": 20},
        source_receipt={
            "target_date": "2026-09-14",
            "tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": True},
            "compact_auxiliary_policy_measurement": {
                "prompt_version": AI_VERSION,
                "measurement_allowed": True,
            },
        },
    )["compact_auxiliary_screen_outcomes"]
    assert blocked["semantic_unclassified_count"] == 1
    assert blocked["automatic_successor_selection"]["eligible"] is False
    assert blocked["automatic_successor_selection"]["selected_prompt_version"] == (
        AI_VERSION
    )

    rows[0]["ai_and_final_guard"]["decision_quality_contract_status"] = "pass"
    sparse_economics_rows = [dict(item) for item in rows]
    for item in sparse_economics_rows[2:]:
        item["entry_quality_path"] = {
            **item["entry_quality_path"],
            "conservative_execution_cost_pct": None,
        }
    sparse = calibration.build_machine_decision_case_table(
        sparse_economics_rows,
        capture_census={"captured": 20, "evaluable": 20},
        source_receipt={
            "target_date": "2026-09-14",
            "tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": True},
            "compact_auxiliary_policy_measurement": {
                "prompt_version": AI_VERSION,
                "measurement_allowed": True,
            },
        },
    )["compact_auxiliary_screen_outcomes"]
    assert sparse["screened_enter_now_count"] == 20
    assert sparse["economic_contract"]["economic_eligible_count"] == 2
    assert sparse["economic_contract"]["screened_total"] == 20
    assert sparse["economic_contract"]["denominator_preserved"] is True
    assert sparse["economic_contract"]["exclusion_counts"] == {
        "cost_contract_missing": 18
    }
    assert sparse["automatic_successor_selection"]["eligible"] is False

    all_pass_rows = [dict(item) for item in rows]
    for item in all_pass_rows:
        item["ai_and_final_guard"] = {
            **item["ai_and_final_guard"],
            "ai_risk_verdict": "PASS",
            "decision_quality_contract_status": "pass",
        }
    all_pass = calibration.build_machine_decision_case_table(
        all_pass_rows,
        capture_census={"captured": 20, "evaluable": 20},
        source_receipt={
            "target_date": "2026-09-14",
            "tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": True},
            "compact_auxiliary_policy_measurement": {
                "prompt_version": AI_VERSION,
                "measurement_allowed": True,
            },
        },
    )["compact_auxiliary_screen_outcomes"]
    assert all_pass["economic_contract"]["evaluable_veto_count"] == 0
    assert all_pass["economic_contract"]["missed_veto_rate"] is None
    assert all_pass["automatic_successor_selection"]["direction"] == (
        "carry_balanced_compact_contract"
    )

    tail_rows = json.loads(json.dumps(rows))
    tail_rows[5]["entry_quality_path"]["exact_stop_distance_pct"] = -1.25
    tail = calibration.build_machine_decision_case_table(
        tail_rows,
        capture_census={"captured": 20, "evaluable": 20},
        source_receipt={
            "target_date": "2026-09-14",
            "tuning_input_allowed": True,
            "machine_terminal_tuning_gate": {"decision_counterfactual_tuning_input_allowed": True},
            "compact_auxiliary_policy_measurement": {
                "prompt_version": AI_VERSION,
                "measurement_allowed": True,
            },
        },
    )["compact_auxiliary_screen_outcomes"]
    assert tail["economic_contract"]["material_tail_pass_count"] == 1
    assert tail["automatic_successor_selection"]["direction"] == (
        "select_material_risk_specificity_variant"
    )


def test_compact_history_requires_own_source_and_unchanged_machine_policy(
    tmp_path, monkeypatch
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    from src.engine.observation_source_quality_audit import _raw_generation

    day = "2026-09-13"
    raw = tmp_path / "raw.jsonl"
    raw.write_text("{}\n")
    incumbent = {
        "machine_policy": {"threshold": 1},
        "ai_policy": {"prompt_version": policy.AI_VERSION},
        "bundle_sha256": "b" * 64,
    }
    monkeypatch.setattr(policy, "load_effective", lambda **kwargs: incumbent)
    audit_path = (
        tmp_path
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    audit_path.parent.mkdir(parents=True)
    manifest = {"raw": "verified"}
    audit = {
        "audit_phase": "final",
        "machine_ai_natural_source_consumption": {
            "target_date": day,
            "tuning_input_allowed": True,
            "source_manifest": {
                "sources": manifest,
                "source_manifest_sha256": calibration._canonical_sha256(manifest),
            },
            "sources": {
                "raw": {
                    "path": str(raw),
                    "exists": True,
                    "generation": _raw_generation(raw),
                    "logical_content_sha256": calibration.hashlib.sha256(
                        raw.read_bytes()
                    ).hexdigest(),
                }
            },
            "compact_auxiliary_policy_measurement": {
                "partitions": [
                    {"measurement_allowed": True, "machine_bundle_sha256": "b" * 64}
                ]
            },
        },
    }
    audit_path.write_text(json.dumps(audit))
    rows = [{"source_date": day}]
    receipt = {"compact_auxiliary_policy_measurement": {"partitions": []}}
    result = calibration._compact_history_receipt(
        tmp_path, "2026-09-14", rows, incumbent, receipt
    )
    assert result["compact_history_receipts"][0]["allowed"] is True
    assert (
        result["compact_auxiliary_policy_measurement"]["partitions"][0]["source_date"]
        == day
    )
    different = {**incumbent, "machine_policy": {"threshold": 2}}
    blocked = calibration._compact_history_receipt(
        tmp_path, "2026-09-14", rows, different, receipt
    )
    assert blocked["compact_history_receipts"][0]["allowed"] is False
    import gzip

    compressed = raw.with_suffix(raw.suffix + ".gz")
    compressed.write_bytes(gzip.compress(raw.read_bytes()))
    raw.unlink()
    archived = calibration._compact_history_receipt(
        tmp_path, "2026-09-14", rows, incumbent, receipt
    )
    assert archived["compact_history_receipts"][0]["allowed"] is True
    compressed.write_bytes(compressed.read_bytes()[:-5])
    truncated = calibration._compact_history_receipt(
        tmp_path, "2026-09-14", rows, incumbent, receipt
    )
    assert truncated["compact_history_receipts"][0]["allowed"] is False
    assert (
        truncated["compact_history_receipts"][0]["reason"]
        == "historical_source_or_policy_invalid"
    )
    raw.write_text("changed\n")
    stale = calibration._compact_history_receipt(
        tmp_path, "2026-09-14", rows, incumbent, receipt
    )
    assert stale["compact_history_receipts"][0]["allowed"] is False


def test_machine_case_table_preserves_distinct_snapshots_inside_sixty_seconds():
    base = {
        "source_date": "2026-09-14",
        "stock_code": "005930",
        "scanner_promotion_id": "SCANPROM-snapshot-series",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "bundle_sha256": "a" * 64,
        "machine_action": "RECHECK",
        "machine_reason": "fixture",
        "machine_hierarchy_selection": {"level": "common"},
        "entry_quality_path": {
            "status": "evaluable",
            "entry_quality_label": "CLEAN_FAST_PROFIT",
        },
        "outcome_horizon_metrics": {
            "10m": {
                "entry_quality_status": "evaluable",
                "entry_quality_label": "CLEAN_FAST_PROFIT",
            }
        },
        "ai_and_final_guard": {"join_status": "exact_snapshot_machine_action_join"},
    }
    report = calibration.build_machine_decision_case_table(
        [
            {
                **base,
                "decision_trace_id": "capture-a",
                "evaluation_attempt_id": "snapshot-a",
                "decision_ts": "2026-09-14T12:00:00+09:00",
            },
            {
                **base,
                "decision_trace_id": "capture-b",
                "evaluation_attempt_id": "snapshot-b",
                "decision_ts": "2026-09-14T12:00:30+09:00",
            },
        ]
    )

    assert report["case_count"] == 2
    assert report["duplicate_same_action_collapsed_count"] == 0
    assert report["incomplete_attempt_identity_count"] == 0


def test_machine_case_table_excludes_incomplete_exact_identity_from_policy_learning():
    row = {
        "decision_trace_id": "capture-missing-promotion",
        "evaluation_attempt_id": "attempt-missing-promotion",
        "decision_ts": "2026-09-14T12:00:00+09:00",
        "source_date": "2026-09-14",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "bundle_sha256": "a" * 64,
        "machine_action": "RECHECK",
        "machine_hierarchy_selection": {"level": "common"},
        "entry_quality_path": {
            "status": "evaluable",
            "entry_quality_label": "CLEAN_FAST_PROFIT",
        },
        "outcome_horizon_metrics": {},
        "ai_and_final_guard": {"join_status": "exact_snapshot_machine_action_join"},
    }

    report = calibration.build_machine_decision_case_table(
        [row],
        source_receipt={"machine_threshold_tuning_input_allowed": True},
    )

    assert report["case_count"] == 1
    assert report["rows"][0]["exact_attempt_identity_complete"] is False
    assert report["incomplete_attempt_identity_count"] == 1
    assert report["policy_learning_eligible_observation_count"] == 0


def test_machine_case_table_preserves_distinct_promotions_for_same_attempt_token():
    base = {
        "evaluation_attempt_id": "attempt-reused",
        "decision_ts": "2026-09-14T12:00:00+09:00",
        "source_date": "2026-09-14",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "bundle_sha256": "a" * 64,
        "machine_action": "RECHECK",
        "machine_hierarchy_selection": {"level": "common"},
        "entry_quality_path": {
            "status": "evaluable",
            "entry_quality_label": "CLEAN_FAST_PROFIT",
        },
        "outcome_horizon_metrics": {},
        "ai_and_final_guard": {"join_status": "exact_snapshot_machine_action_join"},
    }
    report = calibration.build_machine_decision_case_table(
        [
            {
                **base,
                "decision_trace_id": "capture-a",
                "scanner_promotion_id": "SCANPROM-a",
            },
            {
                **base,
                "decision_trace_id": "capture-b",
                "scanner_promotion_id": "SCANPROM-b",
            },
        ]
    )

    assert report["case_count"] == 2
    assert report["duplicate_same_action_collapsed_count"] == 0


def test_machine_ai_trace_match_uses_snapshot_route_bundle_and_machine_action():
    capture = {
        "captured_at": "2026-09-14T12:00:00+09:00",
        "bundle_sha256": "b" * 64,
        "source": {"assessment": {"action": "ENTER_NOW"}},
    }
    context = {
        "snapshot_id": "aims-exact",
        "scanner_promotion_id": "SCANPROM-exact",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
    }
    good = {
        "decision_ts": "2026-09-14T12:00:01+09:00",
        "decision_trace_id": "aidt-good",
        "snapshot_id": "aims-exact",
        "scanner_promotion_id": "SCANPROM-exact",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "machine_bundle_sha256": "b" * 64,
        "entry_mechanistic_action": "ENTER_NOW",
    }
    wrong_route = {**good, "decision_trace_id": "aidt-wrong", "effective_venue": "NXT"}

    matched, status = calibration._match_machine_ai_trace(
        capture, context, {"aims-exact": [wrong_route, good]}
    )

    assert status == "exact_snapshot_machine_action_join"
    assert matched["decision_trace_id"] == "aidt-good"


def test_machine_ai_trace_match_rejects_conflicting_promotion_identity():
    capture = {
        "captured_at": "2026-09-14T12:00:00+09:00",
        "bundle_sha256": "b" * 64,
        "source": {"assessment": {"action": "ENTER_NOW"}},
    }
    context = {
        "snapshot_id": "aims-exact",
        "scanner_promotion_id": "SCANPROM-a",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
    }
    wrong = {
        "decision_ts": "2026-09-14T12:00:01+09:00",
        "decision_trace_id": "aidt-wrong-promotion",
        "snapshot_id": "aims-exact",
        "scanner_promotion_id": "SCANPROM-b",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "machine_bundle_sha256": "b" * 64,
        "entry_mechanistic_action": "ENTER_NOW",
    }

    matched, status = calibration._match_machine_ai_trace(
        capture,
        context,
        {"aims-exact": [wrong]},
    )

    assert matched == {}
    assert status == "ai_trace_missing_for_exact_snapshot"


def test_machine_ai_trace_match_excludes_snapshot_action_mismatch():
    capture = {
        "captured_at": "2026-09-14T12:00:00+09:00",
        "bundle_sha256": "b" * 64,
        "source": {"assessment": {"action": "ENTER_NOW"}},
    }
    context = {
        "snapshot_id": "aims-exact",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
    }
    mismatched = {
        "decision_ts": "2026-09-14T12:00:01+09:00",
        "snapshot_id": "aims-exact",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "machine_bundle_sha256": "b" * 64,
        "entry_mechanistic_action": "RECHECK",
    }

    matched, status = calibration._match_machine_ai_trace(
        capture, context, {"aims-exact": [mismatched]}
    )

    assert matched == {}
    assert status == "machine_action_mismatch_for_exact_snapshot"


def test_hierarchy_cost_owner_rejects_changed_raw_source(tmp_path):
    import hashlib
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256

    raw = tmp_path / "fee.json"
    raw.write_text("{}")
    profile = {"profile_id": "reviewed"}
    catalog = {"profiles": [profile]}
    catalog["content_sha256"] = content_sha256(catalog)
    artifact = {
        "schema": "micro_reversion_economic_reference_daily_resolution_v2",
        "verified": True,
        "target_date": "2026-09-14",
        "tuning_input_allowed": True,
        "source_artifacts": [
            {
                "kind": kind,
                "verified": True,
                "resolved_path": str(raw),
                "expected_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
            }
            for kind in ("broker_fee", "statutory_tax", "symbol_product_master")
        ],
        "canonical_reviewed_cost_payload": catalog,
        "coverage_rows": [
            {
                "status": "eligible",
                "venue": "KRX",
                "symbol": "005930",
                "reviewed_cost_profile_id": "reviewed",
            }
        ],
    }
    artifact["artifact_content_sha256"] = content_sha256(artifact)
    path = (
        tmp_path
        / "report/micro_reversion_economic_reference/micro_reversion_economic_reference_2026-09-14.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(artifact))
    assert "005930" in calibration._hierarchy_cost_profiles(tmp_path, "2026-09-14")
    raw.write_text('{"changed":true}')
    assert calibration._hierarchy_cost_profiles(tmp_path, "2026-09-14") == {}


def test_hierarchy_pipeline_price_cache_reads_each_day_once(monkeypatch, tmp_path):
    from src.engine.scalping import ai_decision_quality as quality

    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    for day in ("2026-09-13", "2026-09-14"):
        (pipeline_dir / f"pipeline_events_{day}.jsonl").write_text("{}\n")
    calls = []

    def load(rows, *, stock_codes):
        list(rows)
        calls.append(frozenset(stock_codes))
        return ([{"stock_code": code} for code in stock_codes], [])

    monkeypatch.setattr(quality, "load_pipeline_price_and_lifecycle_rows", load)
    cache = calibration._hierarchy_pipeline_price_cache(
        [
            {"source_date": "2026-09-13", "stock_code": "005930"},
            {"source_date": "2026-09-13", "stock_code": "000660"},
            {"source_date": "2026-09-14", "stock_code": "005930"},
        ],
        tmp_path,
    )

    assert calls == [frozenset({"005930", "000660"}), frozenset({"005930"})]
    assert set(cache["2026-09-13"]) == {"005930", "000660"}


def test_hierarchy_relabel_cached_missing_symbol_remains_source_gap(
    monkeypatch, tmp_path
):
    from src.engine.scalping import ai_decision_quality as quality

    monkeypatch.setattr(
        calibration,
        "_hierarchy_cost_profiles",
        lambda *args, **kwargs: {
            "005930": {
                "profile_id": "reviewed",
                "economic_source_sha256": "a" * 64,
                "buy_fee_bps": 1,
                "sell_fee_bps": 1,
                "statutory_sell_tax_bps": 15,
                "uncertainty_buffer_bps": 1,
            }
        },
    )
    observed = []

    def mature(*, pending_labels, price_rows, lifecycle_rows, as_of):
        observed.append(list(price_rows))
        return [{"horizon_metrics": {}}]

    monkeypatch.setattr(quality, "mature_outcome_labels", mature)
    rows, census = calibration.relabel_hierarchy_source_rows(
        [
            {
                "source_date": "2026-09-14",
                "stock_code": "005930",
                "decision_ts": "2026-09-14T10:00:00+09:00",
                "decision_trace_id": "trace",
                "comparison": {"conservative_execution_cost_pct": 0.01},
                "label_context": {"reference_price_type": "executable_ask"},
            }
        ],
        tmp_path,
        pipeline_prices_by_day={"2026-09-14": {}},
    )

    assert observed == [[]]
    assert len(rows) == 1
    assert census["raw_path_missing"] == 1


def test_hierarchy_fits_a_real_symbol_delta_instead_of_only_counting_symbols():
    import copy

    rows = []
    for template in _hierarchy_training_rows()[::4]:
        for i in range(10):
            row = copy.deepcopy(template)
            row["decision_trace_id"] += f"-s{i}"
            row["decision_ts"] = (
                f"{row['source_date']}T{10 + i // 6:02d}:{i % 6 * 10:02d}:00+09:00"
            )
            row["stock_code"] = "005930" if i < 5 else "000660"
            row["setup_evidence"]["tail_risk_assessment"]["inputs"]["spread_bp"] = (
                80 if i < 5 else (90 if i < 8 else 20)
            )
            if 5 <= i < 8:
                row["entry_quality_path"][
                    "entry_quality_label"
                ] = "PROFIT_AFTER_SIDEWAYS"
            rows.append(row)
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15"
    )
    assert result["promotion_pass"] is True
    rule = result["policy_candidate"]["threshold_policy"]["hierarchy"]["rules"][0]
    assert rule["symbols"]["000660"]["delta"]["maximum_spread_bp"] < 0
    assert result["evaluations"][0]["symbol_holdout_checks"] == {"000660": True}


def test_hierarchy_net_ev_exact_floor_survives_float_roundoff():
    rows = _hierarchy_training_rows()
    for row in rows:
        row["comparison"]["entry_cost_contract"]["components_pct"]["sell_tax"] = 0.35
        row["comparison"]["conservative_execution_cost_pct"] = 0.4
        row["entry_quality_path"]["conservative_execution_cost_pct"] = 0.4
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15"
    )
    assert result["promotion_pass"] is True
    assert (
        calibration.validate_hierarchy_candidate(result, source_date="2026-09-15") == []
    )
    assert (
        result["economic_contract_diagnostics"][
            "rows_whose_gross_target_cannot_clear_net_ev_floor"
        ]
        == 0
    )


def test_hierarchy_learns_micro_child_and_reports_same_population_four_arms():
    from src.engine.scalping.entry_setup_evidence import _canonical_sha256

    rows = _hierarchy_training_rows()
    for i, row in enumerate(rows):
        good = i % 4 < 2
        context = row["setup_evidence"]["mechanistic_context"]
        context["micro_window"] = {
            "source_quality_status": "eligible",
            "action": "CONTINUE",
            "bid_start": 100,
            "bid_end": 101,
            "feature": {
                "feature_version": "machine_confirmation_fixed_price_window_v1",
                "eligible_for_feature_ablation": True,
                "source_gap_reasons": [],
                "anchor_depth": {"quantity": 1000},
                "best_ask_depletion_velocity_qty_per_sec": 500,
                "aggressive_buy_trade_backed_ratio": 0.9 if good else 0.1,
                "refill_ratio": 0.1,
                "downward_reprice_observed": False,
            },
        }
        context["context_sha256"] = _canonical_sha256(
            {k: v for k, v in context.items() if k != "context_sha256"}
        )
        if not good:
            row["entry_quality_path"][
                "entry_quality_label"
            ] = "CLEAN_FAST_LOSS_OR_ADVERSE"
            row["comparison"]["entry_path_first_hit"] = "adverse_first"
    result = calibration.build_mechanistic_hierarchy_candidate(
        rows, target_date="2026-09-15"
    )
    assert result["promotion_pass"] is True
    evaluation = result["evaluations"][0]
    assert evaluation["rule"]["micro"] is not None
    ablation = evaluation["feature_ablation_study"]["holdout"]
    assert ablation["intersection_count"] == 8
    assert set(ablation["arms"]) == {
        "baseline",
        "bid_rebound",
        "depletion_trade_refill",
        "combined",
    }
    assert ablation["arms"]["combined"]["row_count"] == 4


def _mechanistic_evidence(
    *,
    spread_bp: float = 30.0,
    fillability: float = 70.0,
    ratio: float = 0.8,
) -> dict:
    body = {
        "schema": "entry_setup_evidence_v1",
        "version": "entry_setup_evidence_policy_test",
        "setup_state": "READY",
        "invalidation_facts": [],
        "tail_risk_assessment": {
            "inputs": {
                "spread_bp": spread_bp,
                "fillability_score": fillability,
                "top3_ask_to_bid_ratio": ratio,
            }
        },
        "source_quality": {"status": "fresh_consistent"},
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "evidence_sha256": calibration._canonical_sha256(body)}


def _write_mechanistic_report(
    folder: Path,
    *,
    source_date: str,
    start: int,
    count: int = 2,
    first_hit: str = "target_first",
    suffix: str = "base",
    ratio: float = 0.8,
    target_pct: float = 0.4,
    include_complete_group: bool = True,
    include_flow_analysis: bool = False,
    venue: str = "KRX",
    session_bucket: str = "KRX_REGULAR",
) -> None:
    requests = []
    comparisons = []
    for index in range(start, start + count):
        evidence = _mechanistic_evidence(ratio=ratio)
        trace_id = f"mechanistic-{index}"
        request = {
            "decision_trace_id": trace_id,
            "decision_ts": f"{source_date}T10:00:00+09:00",
            "stage": "entry",
            "effective_venue": venue,
            "session_bucket": session_bucket,
            "stock_code": f"{index:06d}",
            "reference_price": 10000,
            "entry_setup_evidence": evidence,
            "entry_setup_evidence_sha256": evidence["evidence_sha256"],
        }
        if include_flow_analysis:
            analysis_body = {
                "schema": "exact_payload_analysis_v1",
                "source_quality": {
                    "status": "fresh_consistent",
                    "completed_bar_count": 20,
                    "forming_bar_excluded": True,
                },
                "completed_structure": {
                    "returns_pct": {
                        "1m": 0.1,
                        "3m": 0.5,
                        "5m": 1.0,
                        "10m": 1.5,
                        "20m": 2.0,
                        "60m": 3.0,
                    },
                    "slopes_pct_per_bar": {
                        "1m": 0.1,
                        "3m": 0.1,
                        "5m": 0.1,
                        "10m": 0.1,
                        "20m": 0.1,
                        "60m": 0.05,
                    },
                    "phase": "continuation",
                    "regime": "intraday",
                    "alignment": "positive",
                    "bars_since_session_high": 1,
                },
                "executable_liquidity": {
                    "spread_bp": 30.0,
                    "fillability_score": 70.0,
                    "top1_ask_to_bid_ratio": 0.4,
                    "top3_ask_to_bid_ratio": 0.4,
                },
                "volume_confirmation": {"volume_ratio": 1.0},
                "tape_sample": {
                    "buy_pressure_pct": 60.0,
                    "net_aggressive_delta_shares": 100.0,
                },
                "program_flow": {"net_qty": 100.0},
            }
            analysis_hash = calibration._canonical_sha256(analysis_body)
            request["exact_payload_analysis"] = {
                **analysis_body,
                "analysis_sha256": analysis_hash,
            }
            request["exact_payload_analysis_sha256"] = analysis_hash
        if include_complete_group:
            group_body = {
                "schema": calibration.ENTRY_GROUP_OBSERVATION_SCHEMA,
                "group_key": (
                    "GE_10BP|SUPPORTIVE|MEDIUM|continuation|LT_180S|LT_1PCT|"
                    f"{venue}|{session_bucket}"
                ),
                "key_parts": {
                    "price_tick_band": "GE_10BP",
                    "liquidity_band": "SUPPORTIVE",
                    "volatility_band": "MEDIUM",
                    "structure_phase": "continuation",
                    "watch_age_band": "LT_180S",
                    "extension_band": "LT_1PCT",
                    "venue": venue,
                    "session_bucket": session_bucket,
                },
                "missing_dimensions": [],
                "provenance": "native_predecision_observation",
                "future_outcome_fields_forbidden": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
            request[calibration.ENTRY_GROUP_OBSERVATION_SCHEMA] = {
                **group_body,
                "group_observation_sha256": calibration._canonical_sha256(group_body),
            }
        requests.append(request)
        comparisons.append(
            {
                "decision_trace_id": trace_id,
                "control_action": "WAIT",
                "candidate_action": "WAIT",
                "entry_path_first_hit": first_hit,
                "entry_path_target_pct": target_pct,
                "entry_path_adverse_pct": -0.7,
                "conservative_execution_cost_pct": 0.2,
                "probe_cost_adjusted_mfe_pct": 0.2,
                "probe_cost_adjusted_mae_pct": -0.2,
                "directional_pre_profit_mae_estimate_ex_initial_spread_pct": (
                    -0.1 if index % 2 else 0.0
                ),
                "drawdown_recovery_observed": index % 2 == 1,
                "path_basis": (
                    "counterfactual_completed_1m_trade_path_with_conservative_cost"
                ),
                "entry_quality_path": {
                    "schema": calibration.ENTRY_QUALITY_PATH_SCHEMA,
                    "status": "evaluable",
                    "entry_quality_label": (
                        "CLEAN_FAST_PROFIT"
                        if first_hit == "target_first"
                        else "CLEAN_FAST_LOSS_OR_ADVERSE"
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                },
            }
        )
    body = {
        "schema": calibration.DETAILED_PAIRED_SCHEMA,
        "target_date": source_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "cohort_filter": {
            "effective_venue": venue,
            "session_bucket": session_bucket,
        },
        "requests": requests,
        "paired_comparisons": comparisons,
    }
    payload = calibration._with_artifact_content_sha256(body)
    path = folder / (
        f"ai_prompt_detailed_paired_replay_{source_date}_{suffix}_"
        f"venue_{venue.lower()}_session_{session_bucket.lower()}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_mechanistic_refinement_uses_clean_chronological_holdout(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
        "2026-07-09",
        "2026-07-10",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
        )

    result = calibration.build_clean_baseline_mechanistic_refinement(
        folder, target_date=dates[-1]
    )

    assert result["chronological_split"]["calibration_source_dates"] == dates[:5]
    assert result["chronological_split"]["holdout_source_dates"] == dates[-3:]
    assert (
        result["chronological_split"]["holdout_used_for_candidate_selection"] is False
    )
    assert result["promotion_pass"] is True
    candidate = result["policy_candidate"]
    assert candidate["calibration_metrics"]["exposure_count"] == 10
    assert candidate["holdout_metrics"]["exposure_count"] == 6
    assert candidate["calibration_metrics"][
        "cost_adjusted_terminal_proxy_ev_pct"
    ] == pytest.approx(0.2)
    assert candidate["holdout_metrics"][
        "cost_adjusted_terminal_proxy_ev_pct"
    ] == pytest.approx(0.2)
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False
    body = {
        key: value
        for key, value in candidate.items()
        if key != "candidate_content_sha256"
    }
    assert candidate["candidate_content_sha256"] == calibration._canonical_sha256(body)


def _natural_refinement_fixture():
    import copy
    rows = copy.deepcopy(_hierarchy_training_rows())
    earlier = copy.deepcopy(rows[:4])
    for row in earlier:
        row["source_date"] = "2026-09-04"
        row["decision_ts"] = row["decision_ts"].replace("2026-09-07", "2026-09-04")
        row["decision_trace_id"] = row["decision_trace_id"].replace("2026-09-07", "2026-09-04")
        row["comparison"]["entry_cost_contract"]["source_date"] = "2026-09-04"
    rows = earlier + rows
    for i, row in enumerate(rows):
        row.update(
            stock_code=("005930", "000660", "035420", "051910", "005380")[i % 5],
            scanner_promotion_id=f"promotion-{i}",
            evaluation_attempt_id=f"attempt-{i}",
            effective_venue="KRX", session_bucket="KRX_REGULAR",
            bundle_sha256="b" * 64, machine_action="BLOCK",
            machine_observation_hash_verified=True,
            source_report_hash_verified=False,
        )
        evidence = _mechanistic_evidence(spread_bp=30, fillability=70, ratio=0.8)
        row["setup_evidence"] = evidence
    receipt = {
        "target_date": "2026-09-15",
        "machine_threshold_tuning_input_allowed": True,
        "machine_terminal_tuning_gate": {
            "economic_tuning_input_allowed": False,
            "excluded_evaluation_keys": [], "pending_evaluation_keys": [],
        },
    }
    return rows, receipt


def test_common_refinement_keeps_natural_block_for_research_without_promoting_proxy(
    monkeypatch,
):
    rows, receipt = _natural_refinement_fixture()
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt,
        paired_contract={},
    )
    assert len(normalized) == len(rows)
    assert contract["accepted_lane_counts"] == {"natural": len(rows)}
    assert contract["actual_fills_or_ai_calls_required"] is False
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 20
    monkeypatch.setitem(
        calibration.MECHANISTIC_REFINEMENT_GATE,
        "minimum_calibration_exposure_count",
        10_000,
    )
    result = calibration.build_clean_baseline_mechanistic_refinement(
        Path("unused"), target_date="2026-09-15", source_rows=normalized,
        source_contract=contract, parent_policy=parent,
    )
    assert result["promotion_pass"] is False
    assert result["policy_candidate"] is None
    assert result["status"] == "insufficient_mature_sample"
    assert result["evaluated_distinct_policy_count"] > 0
    assert result["economically_evaluable_candidate_count"] > 0
    assert result["best_observed_candidate"]["calibration"][
        "cost_adjusted_terminal_proxy_ev_pct"
    ] is not None
    assert result["calibration_gate_passing_candidate_count"] == 0
    assert result["best_observed_candidate"]["calibration_paired_population"][
        "paired_terminal_proxy_delta_pct"
    ] > 0
    assert result["best_observed_candidate"]["calibration_paired_population"][
        "downstream_operating_evidence_complete"
    ] is False
    assert rows[0]["comparison"]["control_action"] == "WAIT"


@pytest.mark.parametrize("block", ["receipt", "cost", "pending", "hash", "conflict", "date"])
def test_common_refinement_fails_closed_for_natural_source_gaps(block):
    rows, receipt = _natural_refinement_fixture()
    kwargs = {}
    if block == "receipt":
        receipt["machine_threshold_tuning_input_allowed"] = False
    elif block == "cost":
        for row in rows:
            row["comparison"].pop("entry_cost_contract")
    elif block == "pending":
        receipt["machine_terminal_tuning_gate"]["pending_evaluation_keys"] = [
            calibration._machine_evaluation_key(row) for row in rows
        ]
    elif block == "hash":
        for row in rows:
            row["setup_evidence"]["setup_state"] = "tampered"
    elif block == "conflict":
        kwargs["natural_conflicting_attempt_identity_count"] = 1
    else:
        receipt["target_date"] = "2026-09-14"
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt,
        paired_contract={}, **kwargs,
    )
    assert normalized == []
    assert sum(contract["row_exclusion_reason_counts"].values()) == len(rows)


def test_common_refinement_no_improvement_over_incumbent_does_not_promote():
    rows, receipt = _natural_refinement_fixture()
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt,
        paired_contract={},
    )
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 35
    result = calibration.build_clean_baseline_mechanistic_refinement(
        Path("unused"), target_date="2026-09-15", source_rows=normalized,
        source_contract=contract, parent_policy=parent,
    )
    assert result["promotion_pass"] is False
    assert result["policy_candidate"] is None


@pytest.mark.parametrize("reverse", [False, True])
def test_localized_natural_attempt_conflict_preserves_unaffected_population(reverse):
    import copy

    rows, receipt = _natural_refinement_fixture()
    conflicting = copy.deepcopy(rows[0])
    conflicting["comparison"]["entry_path_target_pct"] = 0.9
    originals = [*rows, conflicting]
    if reverse:
        originals.reverse()
    key = calibration._machine_evaluation_key(rows[0])
    case_table = calibration.build_machine_decision_case_table(
        originals, source_receipt=receipt
    )
    assert case_table["conflicting_evaluation_keys"] == [key]
    assert case_table["conflicting_attempt_identity_count"] == 1
    assert case_table["conflict_locations_complete"] is True
    assert case_table["policy_learning_eligible_observation_count"] == len(rows) - 1
    assert all(
        row["policy_learning_excluded"] is True
        and row["policy_learning_exclusion_reason"] == "conflicting_exact_attempt"
        for row in case_table["rows"] if row["evaluation_key"] == key
    )
    normalized, contract = calibration._common_refinement_population(
        [], originals, target_date="2026-09-15", source_receipt=receipt,
        paired_contract={}, natural_conflicting_attempt_identity_count=1,
        natural_conflicting_evaluation_keys=case_table["conflicting_evaluation_keys"],
    )
    assert len(normalized) == len(rows) - 1
    assert contract["natural_conflict_locations_complete"] is True
    assert contract["row_exclusion_reason_counts"]["conflicting_exact_attempt"] == 2
    assert contract["input_row_disposition_complete"] is True


def test_localized_conflict_excludes_matching_paired_alias_too():
    import copy

    rows, receipt = _natural_refinement_fixture()
    alias = copy.deepcopy(rows[0])
    conflicting = copy.deepcopy(rows[0])
    conflicting["machine_action"] = "ENTER_NOW"
    key = calibration._machine_evaluation_key(rows[0])
    normalized, contract = calibration._common_refinement_population(
        [alias], [*rows, conflicting], target_date="2026-09-15",
        source_receipt=receipt, paired_contract={},
        natural_conflicting_attempt_identity_count=1,
        natural_conflicting_evaluation_keys=[key],
    )
    assert len(normalized) == len(rows) - 1
    assert contract["row_exclusion_reason_counts"]["conflicting_exact_attempt"] == 3
    assert contract["input_row_disposition_complete"] is True


def test_localized_conflict_repeated_versions_cannot_inflate_case_denominators():
    import copy

    rows, receipt = _natural_refinement_fixture()
    conflicting = copy.deepcopy(rows[0])
    conflicting["machine_action"] = "ENTER_NOW"
    table = calibration.build_machine_decision_case_table(
        [*rows, conflicting, copy.deepcopy(conflicting), copy.deepcopy(rows[0])],
        source_receipt=receipt,
    )
    assert table["conflicting_attempt_identity_count"] == 1
    assert table["duplicate_same_action_collapsed_count"] == 2
    assert table["case_count"] == len(rows) + 1
    assert table["policy_learning_eligible_observation_count"] == len(rows) - 1


@pytest.mark.parametrize("manifest", [[], ["machine:unknown"], None, [{}]])
def test_unproven_conflict_manifest_cannot_bypass_global_natural_block(manifest):
    import copy

    rows, receipt = _natural_refinement_fixture()
    conflicting = copy.deepcopy(rows[0])
    conflicting["comparison"]["entry_path_target_pct"] = 0.9
    normalized, contract = calibration._common_refinement_population(
        [], [*rows, conflicting], target_date="2026-09-15",
        source_receipt=receipt, paired_contract={},
        natural_conflicting_attempt_identity_count=1,
        natural_conflicting_evaluation_keys=manifest,
    )
    assert normalized == []
    assert contract["natural_conflict_locations_complete"] is False
    assert contract["input_row_disposition_complete"] is True


def test_invalid_manifest_cannot_restore_conflicted_attempt_through_paired_lane():
    import copy

    rows, receipt = _natural_refinement_fixture()
    alias = copy.deepcopy(rows[0])
    conflicting = copy.deepcopy(rows[0])
    conflicting["machine_action"] = "ENTER_NOW"
    normalized, contract = calibration._common_refinement_population(
        [alias], [*rows, conflicting], target_date="2026-09-15",
        source_receipt=receipt, paired_contract={},
        natural_conflicting_attempt_identity_count=1,
        natural_conflicting_evaluation_keys=["machine:unproven"],
    )
    assert normalized == []
    assert contract["row_exclusion_reason_counts"]["conflicting_exact_attempt"] == 1
    assert contract["input_row_disposition_complete"] is True


def _compact_conflict_case_table(valid_count=20):
    import copy
    from src.engine.scalping.mechanistic_entry_runtime_policy import AI_VERSION

    template = _compact_router_case_table(verdict="VETO")["rows"][0]
    rows = []
    for index in range(valid_count + 1):
        row = copy.deepcopy(template)
        row.update(
            decision_trace_id=f"trace-{index}", evaluation_attempt_id=f"attempt-{index}",
            scanner_promotion_id=f"promotion-{index}",
        )
        rows.append(row)
    conflicting = copy.deepcopy(rows[0])
    conflicting["entry_quality_path"]["gross_net_target_pct"] = 999.0
    receipt = {
        "target_date": "2026-09-15", "tuning_input_allowed": True,
        "source_manifest_sha256": "d" * 64,
        "machine_terminal_tuning_gate": {
            "decision_counterfactual_tuning_input_allowed": True,
        },
        "compact_auxiliary_policy_measurement": {
            "prompt_version": AI_VERSION, "measurement_allowed": True,
        },
    }
    return calibration.build_machine_decision_case_table(
        [*rows, conflicting], source_receipt=receipt
    )


@pytest.mark.parametrize("valid_count", [19, 20])
def test_compact_conflicting_veto_attempt_does_not_freeze_unaffected_screens(valid_count):
    report = _compact_conflict_case_table(valid_count)
    compact = report["compact_auxiliary_screen_outcomes"]
    economic = compact["economic_contract"]
    assert report["conflicting_attempt_identity_count"] == 1
    assert economic["economic_eligible_count"] == valid_count
    assert economic["missed_profit_veto_net_sum_pct"] == pytest.approx(valid_count * 0.07)
    assert economic["exclusion_counts"]["conflicting_exact_attempt"] == 2
    assert economic["denominator_preserved"] is True
    assert compact["automatic_successor_selection"]["eligible"] is (valid_count == 20)


@pytest.mark.parametrize("net_ev", [0.12, 0.07, 0.0, -0.01])
@pytest.mark.parametrize("next_generation", [False, True])
def test_full_population_research_value_does_not_bypass_live_10bp_and_downstream_gate(net_ev, next_generation):
    rows, receipt = _natural_refinement_fixture()
    for row in rows:
        row["comparison"]["entry_path_target_pct"] = 0.2 + net_ev
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt, paired_contract={},
    )
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 20
    if next_generation:
        parent["version"] = calibration.MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        parent["postclose_selection"]["minimum_cost_adjusted_ev_pct"] = 0.0
    result = calibration.build_clean_baseline_mechanistic_refinement(
        Path("unused"), target_date="2026-09-15", source_rows=normalized,
        source_contract=contract, parent_policy=parent,
    )
    assert result["promotion_pass"] is False
    assert result["objective"]["minimum_ev_pct"] == 0.1
    assert result["policy_version"] == calibration.MECHANISTIC_FULL_POPULATION_POLICY_VERSION


def test_common_refinement_deduplicates_exact_natural_attempts():
    import copy
    rows, receipt = _natural_refinement_fixture()
    normalized, contract = calibration._common_refinement_population(
        [], rows + [copy.deepcopy(rows[0])], target_date="2026-09-15",
        source_receipt=receipt, paired_contract={},
    )
    assert len(normalized) == len(rows)
    assert contract["row_exclusion_reason_counts"]["identical_duplicate"] == 1
    assert contract["input_row_disposition_complete"] is True


@pytest.mark.parametrize("conflict", [False, True])
def test_common_refinement_trace_cannot_inflate_cross_lane_population(conflict):
    import copy
    rows, receipt = _natural_refinement_fixture()
    paired = copy.deepcopy(rows[0])
    if conflict:
        paired["comparison"]["entry_path_target_pct"] = 0.4
    normalized, contract = calibration._common_refinement_population(
        [paired], rows, target_date="2026-09-15", source_receipt=receipt, paired_contract={},
    )
    assert len(normalized) == len(rows) - int(conflict)
    assert contract["input_row_disposition_complete"] is True
    assert len({r["decision_trace_id"] for r in normalized}) == len(normalized)
    assert contract["row_exclusion_reason_counts"]["conflicting_duplicate" if conflict else "identical_duplicate"] == (2 if conflict else 1)


@pytest.mark.parametrize("net_ev", [0.07, 0.0, -0.01])
@pytest.mark.parametrize("scope", AUTO_PROMOTION_SCOPES)
def test_hierarchy_full_population_recovers_small_net_non_entries(net_ev, scope):
    rows, receipt = _natural_refinement_fixture()
    cohort = tuple(scope.split("|"))
    for row in rows:
        row["entry_group_observation"]["key_parts"].update(venue=cohort[0], session_bucket=cohort[1])
        row.update(effective_venue=cohort[0], session_bucket=cohort[1])
        row["comparison"]["entry_cost_contract"].update(effective_venue=cohort[0], session_bucket=cohort[1])
        row["comparison"]["entry_path_target_pct"] = 0.2 + net_ev
        evidence = row["setup_evidence"]
        evidence["micro_recovery_observation"] = {
            "source_usable": True, "net_aggressive_delta_10t": 20, "price_change_10t_pct": 0.1,
        }
        evidence["evidence_sha256"] = calibration._canonical_sha256({
            k: v for k, v in evidence.items() if k != "evidence_sha256"
        })
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt, paired_contract={}, cohort=cohort,
    )
    if cohort != ("KRX", "KRX_REGULAR"):
        with pytest.raises(ValueError, match="common_refinement_krx_cohort_required"):
            calibration.build_clean_baseline_mechanistic_refinement(
                Path("unused"), target_date="2026-09-15",
                source_rows=normalized, source_contract=contract,
                parent_policy=calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
            )
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 20
    result = calibration.build_mechanistic_hierarchy_candidate(
        normalized, target_date="2026-09-15", parent_policy=parent,
        population_source_contract=contract,
        cohort=cohort,
    )
    assert result["promotion_pass"] is (net_ev >= 0.10)
    if net_ev >= 0.10:
        assert calibration.validate_hierarchy_candidate(result, source_date="2026-09-15", cohort=cohort) == []
        if cohort != ("KRX", "KRX_REGULAR"):
            assert calibration.validate_hierarchy_candidate(result, source_date="2026-09-15", cohort=("KRX", "KRX_REGULAR"))
        candidate = result["policy_candidate"]
        assert candidate["incumbent_machine_policy_sha256"] == calibration._canonical_sha256(parent)
        assert candidate["holdout"]["paired_population"]["paired_terminal_proxy_delta_pct"] > 0
        assert candidate["threshold_policy"]["version"] == calibration.MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        again = calibration.build_mechanistic_hierarchy_candidate(
            normalized, target_date="2026-09-15", parent_policy=candidate["threshold_policy"],
            population_source_contract=contract,
            cohort=cohort,
        )
        assert again["promotion_pass"] is False
        candidate["holdout"]["paired_population"]["paired_terminal_proxy_delta_pct"] = 0.0
        candidate["candidate_content_sha256"] = calibration._canonical_sha256({
            k: v for k, v in candidate.items() if k != "candidate_content_sha256"
        })
        assert "candidate_full_population_economic_proof_invalid" in calibration.validate_hierarchy_candidate(
            result, source_date="2026-09-15", cohort=cohort
        )


def test_hierarchy_full_population_no_gain_over_current_incumbent_carries():
    rows, receipt = _natural_refinement_fixture()
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt, paired_contract={},
    )
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 35
    result = calibration.build_mechanistic_hierarchy_candidate(
        normalized, target_date="2026-09-15", parent_policy=parent,
        population_source_contract=contract,
    )
    assert result["promotion_pass"] is False
    contract["accepted_rows_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hierarchy_full_population_source_contract_invalid"):
        calibration.build_mechanistic_hierarchy_candidate(
            normalized, target_date="2026-09-15", parent_policy=parent,
            population_source_contract=contract,
        )


def test_report_common_refinement_uses_natural_population_and_current_parent(monkeypatch, tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
    rows, receipt = _natural_refinement_fixture()
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 20
    monkeypatch.setattr(runtime_policy, "load_effective", lambda **kw: {"machine_policy": parent})
    monkeypatch.setattr(calibration, "load_machine_observation_rows", lambda *a, **kw: (rows, {"evaluable": len(rows)}))
    monkeypatch.setattr(calibration, "_machine_ai_natural_source_receipt", lambda *a: receipt)
    monkeypatch.setattr(calibration, "_compact_history_receipt", lambda root, day, observations, incumbent, receipt: receipt)
    report = calibration.build_report(target_date="2026-09-15", data_root=tmp_path)
    result = report["mechanistic_entry_refinement"]
    # A producer cannot promote a proxy-only BLOCK population without the
    # uncalled downstream AI and frozen operating owner contract.
    assert result["promotion_pass"] is False
    assert result["source_contract"]["accepted_lane_counts"] == {"natural": len(rows)}
    assert result["source_contract"][
        "machine_population_independent_of_compact_projection"
    ] is True
    assert report["report_scope"] == "main_mechanistic_entry"
    assert report["noncompact_sections_refreshed"] is True
    assert report["machine_full_evaluation"]["full_population_count"] == len(rows)
    assert result["incumbent_machine_policy_sha256"] == calibration._canonical_sha256(parent)


def test_machine_only_report_does_not_scan_unrelated_pipeline_history(
    monkeypatch, tmp_path
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy

    rows, receipt = _natural_refinement_fixture()
    parent = json.loads(json.dumps(calibration.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    parent["thresholds"]["maximum_spread_bp"] = 20
    monkeypatch.setattr(
        runtime_policy,
        "load_effective",
        lambda **kw: {"machine_policy": parent},
    )
    monkeypatch.setattr(
        calibration,
        "load_machine_observation_rows",
        lambda *a, **kw: (rows, {"evaluable": len(rows)}),
    )
    monkeypatch.setattr(
        calibration,
        "_machine_ai_natural_source_receipt",
        lambda *a: receipt,
    )
    monkeypatch.setattr(
        calibration,
        "_compact_history_receipt",
        lambda root, day, observations, incumbent, value: value,
    )
    monkeypatch.setattr(
        calibration,
        "_hierarchy_pipeline_price_cache",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("machine-only must not scan pipeline history")
        ),
    )

    report = calibration.build_main_mechanistic_report(
        target_date="2026-09-15", data_root=tmp_path
    )

    assert report["report_scope"] == "main_mechanistic_entry"
    assert report["noncompact_sections_refreshed"] is True
    assert report["machine_full_evaluation"]["full_population_count"] == len(rows)
    assert report["ofi_smoothing_audit"]["status"] == "not_recomputed_machine_only"
    assert report["hierarchical_entry_quality"]["policy_candidate"] is None
    assert report["hierarchical_entry_quality"]["runtime_extension"][
        "promotion_pass"
    ] is False


def test_mechanistic_source_loader_includes_supported_nxt_only_for_all_scope_mode(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    _write_mechanistic_report(
        folder,
        source_date="2026-09-07",
        start=1,
        venue="NXT",
        session_bucket="NXT_AFTERMARKET",
        include_flow_analysis=True,
    )

    default_rows, _ = calibration._mechanistic_source_rows(
        folder, target_date="2026-09-07"
    )
    all_scope_rows, _ = calibration._mechanistic_source_rows(
        folder, target_date="2026-09-07", all_supported_cohorts=True
    )

    assert default_rows == []
    assert len(all_scope_rows) == 2
    assert {
        (
            row["entry_group_observation"]["key_parts"]["venue"],
            row["entry_group_observation"]["key_parts"]["session_bucket"],
        )
        for row in all_scope_rows
    } == {("NXT", "NXT_AFTERMARKET")}


def test_mechanistic_source_rows_preserve_valid_multihorizon_flow_projection(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    _write_mechanistic_report(
        folder,
        source_date="2026-07-01",
        start=0,
        include_flow_analysis=True,
    )

    rows, source_contract = calibration._mechanistic_source_rows(
        folder, target_date="2026-07-01"
    )

    assert len(rows) == 2
    assert all(
        row["mechanistic_flow_observation_contract_valid"] is True for row in rows
    )
    assert all(
        row["mechanistic_flow_observation"]["matched_families"]
        == [
            "DEPTH_SUPPORTED",
            "DEPTH_SUPPORTED_STAIRCASE",
            "MID_HORIZON_STAIRCASE",
        ]
        for row in rows
    )
    assert source_contract["flow_observation_status_counts"] == {
        "valid_predecision_projection": 2
    }


def test_mechanistic_flow_groups_select_on_past_and_only_nominate_recheck() -> None:
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
        "2026-07-09",
        "2026-07-10",
    ]
    rows = []
    for date_index, source_date in enumerate(dates):
        family_count = 4 if date_index < 5 else 2
        other_count = 4 if date_index < 5 else 2
        for index in range(family_count + other_count):
            in_family = index < family_count
            positive = in_family and index % 2 == 0
            rows.append(
                {
                    "decision_trace_id": f"{source_date}-{index}",
                    "source_date": source_date,
                    "stock_code": f"{date_index:02d}{index:04d}",
                    "mechanistic_flow_observation_contract_valid": True,
                    "mechanistic_flow_observation": {
                        "family_memberships": {"DEPTH_SUPPORTED": in_family}
                    },
                    "comparison": {
                        "entry_path_first_hit": (
                            "target_first" if positive else "adverse_first"
                        ),
                        "entry_path_target_pct": 0.4,
                        "entry_path_adverse_pct": -0.7,
                        "conservative_execution_cost_pct": 0.2,
                        "probe_cost_adjusted_mfe_pct": 0.2 if positive else -0.2,
                    },
                }
            )
    source_contract = {"accepted_rows_sha256": "source-rows-hash"}

    result = calibration.build_mechanistic_flow_group_study(
        target_date=dates[-1],
        source_rows=rows,
        source_contract=source_contract,
    )

    assert result["chronological_split"]["calibration_source_dates"] == dates[:5]
    assert (
        result["chronological_split"]["retrospective_validation_source_dates"]
        == dates[-3:]
    )
    assert (
        result["chronological_split"]["retrospective_validation_is_not_forward_holdout"]
        is True
    )
    assert result["retrospective_supported_recheck_families"] == ["DEPTH_SUPPORTED"]
    assert result["research_candidate"]["action_ceiling"] == "RECHECK"
    assert result["research_candidate"]["direct_enter_authority"] is False
    assert result["research_candidate"]["forward_acceptance_required"] is True
    assert result["recheck_candidate"] is None
    assert result["enter_policy_candidate"] is None
    assert (
        result["micro_confirmation_upgrade_contract"]["flow_family_alone_can_enter"]
        is False
    )
    assert (
        result["family_results"][0]["retrospective_validation_metrics"][
            "direct_enter_fixed_boundary_terminal_proxy_ev_pct"
        ]
        < 0.0
    )

    for source_date in ("2026-09-14", "2026-09-15", "2026-09-16"):
        for index in range(4):
            in_family = index < 2
            positive = in_family and index == 0
            rows.append(
                {
                    "decision_trace_id": f"{source_date}-{index}",
                    "source_date": source_date,
                    "stock_code": f"forward-{source_date}-{index}",
                    "mechanistic_flow_observation_contract_valid": True,
                    "mechanistic_flow_observation": {
                        "family_memberships": {"DEPTH_SUPPORTED": in_family}
                    },
                    "comparison": {
                        "entry_path_first_hit": (
                            "target_first" if positive else "adverse_first"
                        ),
                        "entry_path_target_pct": 0.4,
                        "entry_path_adverse_pct": -0.7,
                        "conservative_execution_cost_pct": 0.2,
                        "probe_cost_adjusted_mfe_pct": 0.2 if positive else -0.2,
                    },
                }
            )
    forward_result = calibration.build_mechanistic_flow_group_study(
        target_date="2026-09-16",
        source_rows=rows,
        source_contract=source_contract,
    )
    assert forward_result["forward_accepted_recheck_families"] == ["DEPTH_SUPPORTED"]
    assert forward_result["recheck_candidate"]["action_ceiling"] == "RECHECK"
    assert forward_result["recheck_candidate"]["direct_enter_authority"] is False
    assert forward_result["enter_policy_candidate"] is None


def test_flow_micro_audit_does_not_backfill_prefreeze_sidecars(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "micro_reversion_ai_quality_bridge"
    folder.mkdir(parents=True)
    (folder / "micro_reversion_ai_quality_bridge_2026-09-11.json").write_text(
        "not-json",
        encoding="utf-8",
    )

    audit = calibration._flow_micro_confirmation_source_audit(
        tmp_path,
        target_date="2026-09-14",
        source_rows=[],
    )

    assert audit["first_eligible_source_date_is_after"] == "2026-09-11"
    assert audit["historical_sidecar_backfill_allowed"] is False
    assert audit["discovered_report_count"] == 0
    assert audit["eligible_same_trace_join_count"] == 0
    assert audit["micro_threshold_fitted"] is False
    assert audit["enter_candidate_issued"] is False


def test_flow_micro_identity_rejects_same_trace_cross_scope_collision() -> None:
    flow = {
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "mechanistic_flow_observation": {"sequence_epoch": 101},
    }
    bridge = {
        "tactical_micro_reversion_evidence_v1": {
            "stock_code": "005930",
            "trace_effective_venue": "KRX",
            "trace_session_bucket": "krx_regular",
            "sequence_epoch": 102,
        },
        "ask_depletion_sidecar": {
            "context": {},
            "horizons": [{"horizon_ms": 1000, "eligible_for_feature_ablation": True}],
        },
    }

    assert calibration._flow_micro_identity_mismatch_reason(flow, bridge) == (
        "same_trace_sequence_epoch_mismatch"
    )
    bridge["tactical_micro_reversion_evidence_v1"]["sequence_epoch"] = 101
    assert calibration._flow_micro_identity_mismatch_reason(flow, bridge) is None


def test_entry_cost_evidence_keeps_comparison_and_executable_layers_separate() -> None:
    contract = {
        "schema": "entry_round_trip_cost_v1",
        "source_date": "2026-09-14",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "basis": "source_bound_estimate",
        "source_sha256": "a" * 64,
        "components_pct": {
            "buy_fee": 0.015,
            "sell_fee": 0.015,
            "sell_tax": 0.2,
            "slippage": 0.495,
        },
    }

    evidence = calibration._entry_cost_evidence(contract, source_date="2026-09-14")

    assert evidence["comparison_cost_pct"] == pytest.approx(0.23)
    assert evidence["executable_estimated_cost_pct"] == pytest.approx(0.725)
    assert evidence["broker_reconciled_cost_pct"] is None
    assert evidence["cost_basis"] == "executable_estimated_cost_pct"
    assert evidence["selected_cost_basis"] == "executable_estimated_cost_pct"
    assert evidence["cost_components"] == contract["components_pct"]
    assert evidence["missing_cost_imputed"] is False


def test_hierarchical_entry_quality_uses_past_group_rows_only_and_blocks_without_actual_path(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "report" / calibration.PAIRED_SUBDIR
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
        "2026-07-09",
        "2026-07-10",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
        )
    rows, source_contract = calibration._mechanistic_source_rows(
        folder, target_date=dates[-1]
    )

    result = calibration.build_hierarchical_entry_quality_walk_forward(
        folder,
        target_date=dates[-1],
        source_rows=rows,
        source_contract=source_contract,
    )

    assert result["walk_forward"]["fold_count"] == 5
    assert result["walk_forward"]["fold_dates_strictly_ordered"] is True
    assert all(
        fold["training_max_date"] < fold["evaluation_date"]
        and fold["future_rows_used_for_training"] is False
        for fold in result["walk_forward"]["folds"]
    )
    assert (
        result["walk_forward"]["aggregate_selected_evaluation"]["clean_fast_count"] > 0
    )
    assert result["group_contract"]["qualifying_symbol_count"] == 0
    assert result["group_contract"]["symbol_residual_active"] is False
    assert result["actual_entry_lane"]["status"] == "actual_path_source_gap"
    assert result["actual_entry_lane"]["economic_acceptance_eligible_count"] == 0
    assert result["promotion_checks"]["actual_path_evidence_available"] is False
    assert result["promotion_pass"] is False
    assert result["policy_candidate"] is None
    raw_anchors = result["market_path_opportunity_anchors"]
    assert raw_anchors["anchor_count"] == 16
    assert raw_anchors["rebound_anchor_count"] == 8
    assert raw_anchors["direct_continuation_anchor_count"] == 8
    assert raw_anchors["path_detail_gap_anchor_count"] == 0
    assert raw_anchors["ai_non_entry_anchor_count"] == 16
    assert raw_anchors["counterfactual_only_not_realized_pnl"] is True
    assert len(raw_anchors["source_date_summaries"]) == len(dates)
    assert all(
        row["exact_trace_count"] == 2 and row["target_first_anchor_count"] == 2
        for row in raw_anchors["source_date_summaries"]
    )
    assert raw_anchors["learning_contract"]["all_accepted_source_dates_used"] is True


def test_actual_lane_reads_lifecycles_and_preserves_realized_fast_vs_late(
    tmp_path: Path,
) -> None:
    source_date = "2026-07-08"
    folder = tmp_path / "report" / "main_scalping_lifecycle_paired"
    folder.mkdir(parents=True)
    trace_id = "actual-entry-1"
    rows = [
        {
            "stock_code": "000001",
            "first_fill_execution_at": f"{source_date}T10:00:00+09:00",
            "final_exit_execution_at": f"{source_date}T10:01:00+09:00",
            "actual_holding_duration_sec": 60,
            "terminal_state": "FINAL_EXIT_RECONCILED",
            "entry_notional_krw": 10_000,
            "realized_net_pnl_krw": 20,
            "decision_trace_context_path": [
                {"stage": "entry_decision", "decision_trace_id": trace_id}
            ],
        },
        {
            "stock_code": "000002",
            "first_fill_execution_at": f"{source_date}T10:00:00+09:00",
            "final_exit_execution_at": f"{source_date}T10:10:00+09:00",
            "actual_holding_duration_sec": 600,
            "terminal_state": "FINAL_EXIT_RECONCILED",
            "entry_notional_krw": 10_000,
            "realized_net_pnl_krw": 15,
            "decision_trace_context_path": [],
        },
    ]
    (folder / f"main_scalping_lifecycle_paired_{source_date}.json").write_text(
        json.dumps({"target_date": source_date, "lifecycles": rows}),
        encoding="utf-8",
    )

    audit = calibration._actual_entry_quality_source_audit(
        tmp_path / "report",
        target_date=source_date,
        counterfactual_rows=[{"decision_trace_id": trace_id}],
    )

    assert audit["filled_lifecycle_count"] == 2
    assert audit["realized_lifecycle_count"] == 2
    assert audit["realized_net_10bp_count"] == 2
    assert audit["realized_net_10bp_fast_count"] == 1
    assert audit["realized_net_10bp_late_count"] == 1
    assert audit["raw_decision_path_join_count"] == 1
    assert audit["fast_realized_outcome_is_clean_path_proof"] is False
    assert audit["status"] == "realized_outcome_available_path_quality_gap"
    assert audit["realized_anchor_ledger"][0]["entry_decision_trace_id"] == trace_id
    assert audit["realized_anchor_ledger"][0]["market_path_projection_joined"] is True


def test_hierarchical_entry_quality_excludes_incomplete_group_dimensions(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "report" / calibration.PAIRED_SUBDIR
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
            include_complete_group=False,
        )
    rows, source_contract = calibration._mechanistic_source_rows(
        folder, target_date=dates[-1]
    )

    result = calibration.build_hierarchical_entry_quality_walk_forward(
        folder,
        target_date=dates[-1],
        source_rows=rows,
        source_contract=source_contract,
    )

    assert result["source_population"]["entry_quality_evaluable_count"] == 12
    assert result["group_contract"]["group_complete_evaluable_count"] == 0
    assert result["group_contract"]["group_incomplete_evaluable_count"] == 12
    assert result["group_contract"]["missing_group_dimensions_imputed"] is False
    assert result["walk_forward"]["fold_count"] == 0
    assert result["promotion_pass"] is False


def test_actual_completed_bar_path_is_diagnostic_not_economic_acceptance(
    tmp_path: Path,
) -> None:
    source_date = "2026-07-08"
    folder = tmp_path / "report" / "ai_decision_outcome_labels"
    folder.mkdir(parents=True)
    report = {
        "schema": "ai_decision_outcome_labels_v1",
        "target_date": source_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "labels": [
            {
                "stage_outcome": {
                    "actual_fill_entry_quality_path": {
                        "actual_fill_observed": True,
                        "status": "evaluable",
                        "entry_quality_label": "CLEAN_FAST_PROFIT",
                        "path_authority": (
                            "actual_fill_anchor_completed_bar_touch_not_executable_bid"
                        ),
                        "economic_acceptance_eligible": False,
                        "realized_cost_contract_complete": False,
                    }
                }
            }
        ],
    }
    (folder / f"ai_decision_outcome_labels_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    audit = calibration._actual_entry_quality_source_audit(
        tmp_path / "report", target_date=source_date
    )

    assert audit["path_evaluable_count"] == 1
    assert audit["economic_acceptance_eligible_count"] == 0
    assert audit["status"] == "actual_path_diagnostic_available"


def test_mechanistic_refinement_excludes_conflicting_trace_and_never_imputes_micro(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
        "2026-07-09",
        "2026-07-10",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
        )
    _write_mechanistic_report(
        folder,
        source_date=dates[-1],
        start=(len(dates) - 1) * 2,
        count=2,
        suffix="conflict",
        ratio=0.9,
    )

    result = calibration.build_clean_baseline_mechanistic_refinement(
        folder, target_date=dates[-1]
    )

    source = result["source_contract"]
    assert source["accepted_unique_trace_count"] == 14
    assert source["conflicting_duplicate_trace_count"] == 2
    assert source["conflicting_duplicate_traces_excluded"] is True
    assert source["missing_micro_fields_imputed"] is False
    assert result["common_feature_contract"]["micro_enhanced_trace_count"] == 0
    assert result["chronological_split"]["holdout_source_dates"] == dates[-3:]
    assert result["promotion_pass"] is False
    assert result["policy_candidate"] is None


def test_mechanistic_refinement_censors_same_bar_paths_instead_of_zero_filling(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
        "2026-07-09",
        "2026-07-10",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
            first_hit="same_bar_ambiguous",
        )

    result = calibration.build_clean_baseline_mechanistic_refinement(
        folder, target_date=dates[-1]
    )

    assert result["grid_candidate_count"] == 0
    assert result["best_observed_candidate"] is None
    assert result["status"] == "insufficient_clean_common_feature_evidence"


def test_mechanistic_refinement_blocks_mixed_path_boundary_contracts(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-07-08",
        "2026-07-09",
        "2026-07-10",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
            target_pct=0.4 if day_index < 7 else 0.5,
        )

    result = calibration.build_clean_baseline_mechanistic_refinement(
        folder, target_date=dates[-1]
    )

    assert result["objective"]["path_boundary_contract_isolated"] is False
    assert result["promotion_checks"]["path_boundary_contract_isolated"] is False
    assert result["promotion_pass"] is False
    assert result["policy_candidate"] is None


def test_mechanistic_paired_delta_counts_avoided_control_exposure() -> None:
    adverse = {
        "decision_trace_id": "adverse",
        "comparison": {
            "control_action": "BUY",
            "entry_path_first_hit": "adverse_first",
            "entry_path_target_pct": 0.4,
            "entry_path_adverse_pct": -0.7,
            "conservative_execution_cost_pct": 0.2,
        },
    }
    target = {
        "decision_trace_id": "target",
        "comparison": {
            "control_action": "WAIT",
            "entry_path_first_hit": "target_first",
            "entry_path_target_pct": 0.4,
            "entry_path_adverse_pct": -0.7,
            "conservative_execution_cost_pct": 0.2,
        },
    }

    metrics = calibration._mechanistic_paired_population_metrics(
        [adverse, target], [target]
    )

    assert metrics["paired_comparable_count"] == 2
    assert metrics["paired_terminal_contract_complete"] is True
    assert metrics["paired_terminal_proxy_delta_pct"] == pytest.approx(0.55)
    assert metrics["candidate_opportunity_ev_pct"] == pytest.approx(0.1)
    assert metrics["incumbent_opportunity_ev_pct"] == pytest.approx(-0.45)


def test_mechanistic_legacy_hashless_rows_use_exact_file_and_row_hash_provenance(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "paired"
    dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-06",
        "2026-07-07",
        "2026-09-08",
        "2026-09-09",
        "2026-09-10",
    ]
    for day_index, source_date in enumerate(dates):
        _write_mechanistic_report(
            folder,
            source_date=source_date,
            start=day_index * 2,
        )
    legacy_path = next(folder.glob("*2026-07-01*.json"))
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    legacy.pop("artifact_content_sha256")
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")

    result = calibration.build_clean_baseline_mechanistic_refinement(
        folder, target_date=dates[-1]
    )

    assert (
        result["best_observed_candidate"]["calibration"][
            "source_report_hash_contract_complete"
        ]
        is False
    )
    assert (
        result["best_observed_candidate"]["calibration"][
            "source_provenance_contract_complete"
        ]
        is True
    )
    assert result["source_contract"]["legacy_hashless_report_count"] == 1
    assert (
        result["source_contract"]["accepted_provenance_verified_unique_trace_count"]
        == result["source_contract"]["accepted_unique_trace_count"]
    )
    legacy_sources = [
        source
        for source in result["source_contract"]["accepted_source_artifacts"]
        if source["source_date"] == "2026-07-01"
    ]
    assert len(legacy_sources) == 1
    assert legacy_sources[0]["provenance_tier"] == (
        "legacy_row_self_hash_and_observed_file_hash"
    )
    assert len(legacy_sources[0]["observed_file_sha256"]) == 64
    assert result["calibration_floor_passing_candidate_count"] > 0
    assert result["promotion_pass"] is True
    assert result["policy_candidate"] is not None


def _write_pipeline(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_cumulative_calibration_updates_from_one_exact_trace(tmp_path: Path) -> None:
    report_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-29_candidate_v1.json"
    )
    _write_json(
        report_path,
        {
            "target_date": "2026-07-29",
            "runtime_effect": False,
            "schema_rejected_count": 0,
            "provider_failed_count": 0,
            "candidate_provider_none_count": 0,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "BUY",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 1.2,
                    "delta_pct": 1.2,
                    "first_hit": "target",
                    "outcome_return_pct": 1.2,
                    "outcome_mfe_pct": 1.5,
                    "outcome_mae_pct": -0.1,
                    "candidate_error_taxonomy": [],
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 1
    assert candidate["learning_update_floor"]["pass"] is True
    assert candidate["source_quality_adjusted_ev_delta_pct"] == 1.2
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert "exact_trace_floor" in candidate["prompt_review_gate"]["blockers"]
    assert (
        "independent_source_date_floor" in candidate["prompt_review_gate"]["blockers"]
    )
    assert report["runtime_effect"] is False
    assert report["selected_review_candidate"] is None


def test_prompt_review_candidate_requires_multi_day_bounded_exploration(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for source_date, start in (("2026-07-28", 0), ("2026-07-29", 20)):
        rows = []
        for index in range(start, start + 20):
            is_exposure = index < 5
            rows.append(
                {
                    "decision_trace_id": f"trace-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": (
                        0.4 if is_exposure else 0.01
                    ),
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "candidate_probe_worst_loss_pct": -0.2,
                    "delta_pct": 0.4 if is_exposure else 0.01,
                    "first_hit": "target",
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_{source_date}_candidate_v2.json",
            {
                "target_date": source_date,
                "runtime_effect": False,
                "schema_rejected_count": 0,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "requests": [{"candidate": {"prompt_version": "candidate_v2"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["source_date_count"] == 2
    assert candidate["candidate_exposure_count"] == 5
    assert candidate["candidate_exposure_ev_pct"] == 0.4
    assert candidate["prompt_review_gate"]["blockers"] == []
    assert candidate["review_ready_for_prompt_candidate"] is True
    assert report["selected_review_candidate"]["candidate_prompt_version"] == (
        "candidate_v2"
    )


def test_bounded_recovery_exposure_is_not_blocked_by_raw_adverse_first_count(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-08-02", "2026-08-03")):
        rows = []
        for offset in range(20):
            index = day_index * 20 + offset
            is_exposure = index < 5
            is_recovery = index == 0
            rows.append(
                {
                    "decision_trace_id": f"bounded-recovery-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": (
                        0.5 if is_exposure else 0.01
                    ),
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "delta_pct": 0.5 if is_exposure else 0.01,
                    "first_hit": "adverse" if is_recovery else "target",
                    "profit_opportunity_sequence": (
                        "drawdown_then_profit_recovery"
                        if is_recovery
                        else "profit_before_drawdown"
                    ),
                    "candidate_probe_worst_loss_pct": (-1.5 if is_recovery else -0.2),
                    "probe_worst_loss_pct": -1.5 if is_recovery else -0.2,
                    "control_probe_severe_tail_exposure": False,
                    "candidate_probe_severe_tail_exposure": False,
                    "control_drawdown_recovery_captured": False,
                    "candidate_drawdown_recovery_captured": is_recovery,
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_{source_date}_candidate_bounded.json",
            {
                "target_date": source_date,
                "runtime_effect": False,
                "schema_rejected_count": 0,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "requests": [{"candidate": {"prompt_version": "candidate_bounded"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-08-03", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["adverse_first_exposure_not_increased"] is False
    assert candidate["adverse_first_role"] == ("diagnostic_not_absolute_quality_veto")
    assert candidate["candidate_probe_loss_budget_breach_count"] == 0
    assert candidate["candidate_drawdown_recovery_capture_count"] == 1
    assert (
        candidate["prompt_review_gate"]["checks"]["bounded_probe_risk_budget"] is True
    )
    assert (
        candidate["diagnostic_checks_not_review_veto"]["severe_tail_rate_not_increased"]
        is None
    )
    assert (
        candidate["diagnostic_checks_not_review_veto"][
            "drawdown_recovery_capture_rate_not_decreased"
        ]
        is True
    )
    assert (
        "adverse_first_not_increased" not in candidate["prompt_review_gate"]["checks"]
    )
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_schema_reject_blocks_review_selection_but_keeps_learning(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-29_candidate_v1.json"
    )
    _write_json(
        report_path,
        {
            "target_date": "2026-07-29",
            "runtime_effect": False,
            "schema_rejected_count": 1,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "control_action": "WAIT",
                    "candidate_action": "BUY",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.5,
                    "delta_pct": 0.5,
                    "first_hit": "target",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["learning_update_floor"]["pass"] is True
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert report["selected_review_candidate"] is None


def test_isolated_schema_reject_does_not_block_bounded_prompt_review(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-07-28", "2026-07-29")):
        rows = []
        for offset in range(60):
            index = day_index * 60 + offset
            is_exposure = index < 6
            rows.append(
                {
                    "decision_trace_id": f"trace-{index}",
                    "stock_code": f"{index % 12:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": (
                        0.4 if is_exposure else 0.01
                    ),
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "candidate_probe_worst_loss_pct": -0.2,
                    "delta_pct": 0.4 if is_exposure else 0.01,
                    "first_hit": "target",
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_{source_date}_candidate_v3.json",
            {
                "target_date": source_date,
                "runtime_effect": False,
                "schema_rejected_count": 1 if day_index == 0 else 0,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "requests": [{"candidate": {"prompt_version": "candidate_v3"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["schema_rejected_count"] == 1
    assert candidate["schema_evaluated_count"] == 121
    assert candidate["schema_rejection_rate_pct"] < 1.0
    assert (
        candidate["prompt_review_gate"]["checks"]["schema_rejection_rate_ceiling"]
        is True
    )
    assert candidate["prompt_review_gate"]["blockers"] == []
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_model_comparison_artifact_is_excluded_from_prompt_cumulative_ledger(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / (
            "ai_prompt_detailed_paired_replay_2026-07-29_candidate_v1_"
            "model_gpt-5-nano.json"
        )
    )
    _write_json(
        report_path,
        {
            "target_date": "2026-07-29",
            "runtime_effect": False,
            "model_comparison_contract": {
                "enabled": True,
                "baseline_model": "gpt-5.4-nano",
                "candidate_model": "gpt-5-nano",
                "decision_authority": "offline_model_comparison_only",
            },
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "control_action": "WAIT",
                    "candidate_action": "BUY",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 1.0,
                    "delta_pct": 1.0,
                    "first_hit": "target",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    assert report["candidate_count"] == 0
    assert report["source_reports"] == []
    assert report["selected_review_candidate"] is None


def test_ofi_action_adjustment_joins_exact_trace_outcome_from_first_row(
    tmp_path: Path,
) -> None:
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "holding-trace-1",
                    "control_action": "EXIT",
                    "candidate_action": "EXIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.0,
                    "delta_pct": 0.0,
                    "first_hit": "target",
                    "outcome_return_pct": 0.8,
                    "outcome_mfe_pct": 1.0,
                    "outcome_mae_pct": -0.2,
                }
            ],
        },
    )
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    fields = {
        "smoothing_action": "DEBOUNCE_EXIT",
        "raw_flow_action": "EXIT",
        "final_flow_action": "HOLD",
        "ai_decision_trace_id": "holding-trace-1",
        "ai_input_snapshot_id": "snapshot-1",
        "holding_flow_ofi_usable": True,
        "holding_flow_ofi_regime": "stable_bullish",
        "metric_role": "ai_action_postprocessor_outcome_calibration",
        "decision_authority": (
            "bounded_runtime_action_postprocessor_with_exact_trace_attribution"
        ),
    }
    _write_pipeline(
        pipeline_path,
        [
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:00:00+09:00",
                "fields": fields,
            }
        ],
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["mature_outcome_row_count"] == 1
    assert ledger["mature_effective_transition_outcome_row_count"] == 1
    assert ledger["effective_transition_row_count"] == 1
    assert ledger["no_change_control_row_count"] == 0
    assert ledger["learning_update_floor"]["pass"] is True
    assert ledger["source_quality_adjusted_ev_delta_pct"] == 0.8
    assert ledger["raw_to_final_transition_counts"] == {"EXIT->HOLD": 1}
    assert report["ofi_smoothing_audit"]["status"] == "pass"


def test_ofi_no_change_exact_outcome_is_control_not_learning_evidence(
    tmp_path: Path,
) -> None:
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "holding-control-1",
                    "control_action": "EXIT",
                    "candidate_action": "EXIT",
                    "outcome_return_pct": 0.8,
                    "outcome_mfe_pct": 1.0,
                    "outcome_mae_pct": -0.2,
                    "first_hit": "target",
                }
            ],
        },
    )
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    _write_pipeline(
        pipeline_path,
        [
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "fields": {
                    "smoothing_action": "NO_CHANGE",
                    "raw_flow_action": "EXIT",
                    "final_flow_action": "EXIT",
                    "ai_decision_trace_id": "holding-control-1",
                    "ai_input_snapshot_id": "snapshot-control-1",
                },
            }
        ],
    )

    ledger = build_report(target_date="2026-07-30", data_root=tmp_path)[
        "ofi_action_outcome_calibration"
    ]

    assert ledger["schema"] == "ofi_exact_trace_action_outcome_calibration_v2"
    assert ledger["status"] == "sample_floor_keep_collecting"
    assert ledger["mature_outcome_row_count"] == 1
    assert ledger["mature_effective_transition_outcome_row_count"] == 0
    assert ledger["effective_transition_row_count"] == 0
    assert ledger["no_change_control_row_count"] == 1
    assert ledger["no_change_control_outcome_status_counts"] == {"mature": 1}
    assert ledger["raw_to_final_transition_counts"] == {}
    assert ledger["source_quality_adjusted_ev_delta_pct"] is None
    assert ledger["learning_update_floor"]["pass"] is False


def test_ofi_unlinked_events_are_preserved_as_audit_exclusions(
    tmp_path: Path,
) -> None:
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    _write_pipeline(
        pipeline_path,
        [
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "fields": {
                    "smoothing_action": "NO_CHANGE",
                    "raw_flow_action": "EXIT",
                    "final_flow_action": "EXIT",
                },
            }
        ],
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["exact_trace_row_count"] == 0
    assert ledger["current_date_exclusion_counts"] == {
        "exact_decision_trace_missing": 1
    }
    assert (
        "exact_decision_trace_attribution_incomplete"
        in report["ofi_smoothing_audit"]["defects"]
    )


def test_prior_pending_ofi_row_is_rejoined_when_outcome_matures(
    tmp_path: Path,
) -> None:
    prior_report = (
        tmp_path
        / "report"
        / "ai_decision_action_outcome_calibration"
        / "ai_decision_action_outcome_calibration_2026-07-29.json"
    )
    _write_json(
        prior_report,
        {
            "target_date": "2026-07-29",
            "ofi_action_outcome_calibration": {
                "rows": [
                    {
                        "ledger_key": "holding_flow_ofi_smoothing_applied:trace-1",
                        "decision_trace_id": "trace-1",
                        "ai_input_snapshot_id": "snapshot-1",
                        "stage": "holding_flow_ofi_smoothing_applied",
                        "raw_action": "EXIT",
                        "final_action": "HOLD",
                        "outcome_status": "pending",
                    }
                ]
            },
        },
    )
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "control_action": "EXIT",
                    "candidate_action": "EXIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.0,
                    "delta_pct": 0.0,
                    "outcome_return_pct": 0.4,
                    "first_hit": "target",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["mature_outcome_row_count"] == 1
    assert ledger["source_quality_adjusted_ev_delta_pct"] == 0.4


def test_ofi_partial_action_without_quantity_is_mature_not_comparable(
    tmp_path: Path,
) -> None:
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    pipeline_path.parent.mkdir(parents=True)
    pipeline_path.write_text(
        json.dumps(
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "fields": {
                    "ai_decision_trace_id": "trace-trim",
                    "ai_input_snapshot_id": "snapshot-trim",
                    "raw_flow_action": "TRIM",
                    "final_flow_action": "EXIT",
                    "smoothing_action": "CONFIRM_EXIT",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-trim",
                    "control_action": "TRIM",
                    "candidate_action": "EXIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.0,
                    "delta_pct": 0.0,
                    "outcome_return_pct": -0.8,
                    "first_hit": "adverse",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["status"] == "mature_outcome_not_comparable_keep_collecting"
    assert ledger["mature_outcome_row_count"] == 0
    assert ledger["pending_outcome_row_count"] == 0
    assert ledger["mature_not_comparable_outcome_row_count"] == 1
    assert ledger["mature_not_comparable_reason_counts"] == {
        "action_value_requires_exact_quantity_or_cashflow_contract": 1
    }


def test_same_prompt_isolated_krx_and_nxt_are_separate_candidates(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for venue, session, suffix in (
        ("KRX", "KRX_REGULAR", "krx"),
        ("NXT", "NXT_AFTERMARKET", "nxt"),
    ):
        payload = _valid_detailed_payload(
            {
                "target_date": "2026-09-07",
                "requests": [{"candidate": {"prompt_version": "candidate_isolated"}}],
                "paired_comparisons": [
                    {
                        "decision_trace_id": f"trace-{suffix}",
                        "stock_code": "005930",
                        "stage": "entry",
                        "effective_venue": venue,
                        "session_bucket": session,
                        "decision_ts": "2026-09-07T10:00:00+09:00",
                        "control_action": "WAIT",
                        "candidate_action": "WAIT",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": 0.1,
                        "delta_pct": 0.1,
                        "outcome_return_pct": 0.1,
                    }
                ],
            }
        )
        contract = payload["candidate_contract_sha256"]
        payload["promotion_cohort_scope"] = {
            "stages": ["entry"],
            "effective_venues": [venue],
            "session_buckets": [session],
            "isolated": True,
            "candidate_contract_sha256": contract,
            "candidate_contract_isolated": True,
            "cross_cohort_promotion_forbidden": True,
        }
        payload["cohort_filter"] = {
            "effective_venue": venue,
            "session_bucket": session,
            "runtime_effect": False,
        }
        payload = calibration._with_artifact_content_sha256(payload)
        path = paired_dir / f"ai_prompt_detailed_paired_replay_2026-09-07_{suffix}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["candidate_count"] == 2
    assert {
        (row["effective_venue"], row["session_bucket"])
        for row in report["candidate_summaries"]
    } == {("KRX", "KRX_REGULAR"), ("NXT", "NXT_AFTERMARKET")}


def test_dual_aftermarket_uses_route_key_and_remains_observe_only(
    tmp_path: Path,
) -> None:
    assert calibration._cohort_route_scope("KRX", "KRX_REGULAR", "") == (
        "KRX:KRX_REGULAR"
    )
    rows = [
        {
            "decision_trace_id": "dual-known",
            "stock_code": "005930",
            "stage": "entry",
            "effective_venue": "UNKNOWN",
            "session_bucket": "KRX_NXT_AFTERMARKET",
            "market_data_route": "krx_nxt_integrated",
            "actual_execution_venue": "KRX",
            "control_action": "WAIT",
            "candidate_action": "WAIT",
            "control_decision_value_pct": 0.0,
            "candidate_primary_decision_value_pct": 0.1,
            "delta_pct": 0.1,
            "outcome_return_pct": 0.1,
        },
        {
            "decision_trace_id": "dual-unknown-venue",
            "stock_code": "005930",
            "stage": "entry",
            "effective_venue": "UNKNOWN",
            "session_bucket": "KRX_NXT_AFTERMARKET",
            "market_data_route": "krx_nxt_integrated",
            "actual_execution_venue": "UNKNOWN",
            "control_action": "WAIT",
            "candidate_action": "WAIT",
            "control_decision_value_pct": 0.0,
            "candidate_primary_decision_value_pct": 0.1,
            "delta_pct": 0.1,
            "outcome_return_pct": 0.1,
        },
        {
            "decision_trace_id": "dual-cost-missing",
            "stock_code": "005930",
            "stage": "entry",
            "effective_venue": "UNKNOWN",
            "session_bucket": "KRX_NXT_AFTERMARKET",
            "market_data_route": "krx_nxt_integrated",
            "actual_execution_venue": "NXT",
            "control_action": "WAIT",
            "candidate_action": "BUY",
            "control_decision_value_pct": 0.0,
            "candidate_primary_decision_value_pct": 0.1,
            "delta_pct": 0.1,
            "outcome_return_pct": 0.1,
        },
    ]
    payload = _valid_detailed_payload(
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "dual_v1"}}],
            "paired_comparisons": rows,
        }
    )
    contract = payload["candidate_contract_sha256"]
    payload["promotion_cohort_scope"] = {
        "stages": ["entry"],
        "effective_venues": ["INTEGRATED"],
        "session_buckets": ["KRX_NXT_AFTERMARKET"],
        "market_data_routes": ["krx_nxt_integrated"],
        "isolated": True,
        "candidate_contract_sha256": contract,
        "candidate_contract_isolated": True,
        "cross_cohort_promotion_forbidden": True,
    }
    payload["cohort_filter"] = {
        "effective_venue": "INTEGRATED",
        "session_bucket": "KRX_NXT_AFTERMARKET",
        "market_data_route": "krx_nxt_integrated",
        "runtime_effect": False,
    }
    payload = calibration._with_artifact_content_sha256(payload)
    path = (
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_dual.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["cohort_key_version"] == "v2"
    assert candidate["market_data_route"] == "KRX_NXT_INTEGRATED"
    assert candidate["authority_state"] == "OBSERVE_ONLY"
    assert candidate["exact_trace_count"] == 1
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert candidate["review_classification"] == "dual_aftermarket_observe_only"
    assert report["source_reports"][0]["row_exclusion_reason_counts"] == {
        "dual_actual_execution_venue_unknown": 1,
        "dual_exposure_cost_missing_or_invalid": 1,
    }
    assert report["review_ready_candidates"] == []


def test_multiple_ready_cohorts_are_not_ranked_into_one_global_selection(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    routes = (("KRX", "KRX_REGULAR"), ("NXT", "NXT_AFTERMARKET"))
    for venue, session in routes:
        for day_index, source_date in enumerate(("2026-09-07", "2026-09-08")):
            rows = []
            for offset in range(20):
                is_exposure = day_index == 0 and offset < 5
                rows.append(
                    {
                        "decision_trace_id": f"ready-{venue}-{day_index}-{offset}",
                        "stock_code": f"{offset % 10:06d}",
                        "effective_venue": venue,
                        "session_bucket": session,
                        "control_action": "WAIT",
                        "candidate_action": "BUY" if is_exposure else "WAIT",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": 0.2,
                        "candidate_execution_cost_contract_applied": is_exposure,
                        "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                        "candidate_probe_worst_loss_pct": -0.1,
                        "delta_pct": 0.2,
                    }
                )
            payload = _valid_detailed_payload(
                {
                    "target_date": source_date,
                    "requests": [{"candidate": {"prompt_version": "candidate_ready"}}],
                    "paired_comparisons": rows,
                }
            )
            payload["promotion_cohort_scope"]["effective_venues"] = [venue]
            payload["promotion_cohort_scope"]["session_buckets"] = [session]
            payload["cohort_filter"] = {
                "effective_venue": venue,
                "session_bucket": session,
                "runtime_effect": False,
            }
            payload = calibration._with_artifact_content_sha256(payload)
            path = paired_dir / (
                "ai_prompt_detailed_paired_replay_"
                f"{source_date}_{venue.lower()}_ready.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-08", data_root=tmp_path)

    assert report["review_candidate_count"] == 2
    assert len(report["review_ready_candidates"]) == 2
    assert report["selected_review_candidate"] is None
    assert report["selection_status"] == (
        "multiple_isolated_review_candidates_no_cross_cohort_selection"
    )
    assert report["optimizer_handoff"]["selected_review_candidate"] is None
    assert len(report["optimizer_handoff"]["review_ready_candidates"]) == 2


def test_conflicting_duplicate_trace_is_excluded_and_blocks_only_affected_cohort(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for suffix, outcome in (("a", 0.4), ("b", -0.4)):
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_2026-09-07_conflict_{suffix}.json",
            {
                "target_date": "2026-09-07",
                "requests": [{"candidate": {"prompt_version": "candidate_conflict"}}],
                "paired_comparisons": [
                    {
                        "decision_trace_id": "same-trace",
                        "stock_code": "005930",
                        "control_action": "WAIT",
                        "candidate_action": "BUY",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": outcome,
                        "candidate_execution_cost_contract_applied": True,
                        "candidate_execution_cost_pct": 0.2,
                        "candidate_probe_worst_loss_pct": -0.2,
                        "delta_pct": outcome,
                        "outcome_return_pct": outcome,
                    }
                ],
            },
        )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["source_contract_summary"]["conflicting_duplicate_trace_count"] == 1
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 0
    assert candidate["source_integrity_complete"] is False
    assert report["selected_review_candidate"] is None
    assert report["optimizer_handoff"]["source_contract_pass"] is True


def test_bounded_probe_budget_allows_one_twopercent_breach_in_five_exposures(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-09-07", "2026-09-08")):
        rows = []
        for offset in range(20):
            index = day_index * 20 + offset
            is_exposure = index < 5
            rows.append(
                {
                    "decision_trace_id": f"risk-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.4,
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "candidate_probe_worst_loss_pct": (-2.5 if index == 0 else -0.2),
                    "delta_pct": 0.4,
                    "first_hit": "target",
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir / f"ai_prompt_detailed_paired_replay_{source_date}_risk.json",
            {
                "target_date": source_date,
                "requests": [{"candidate": {"prompt_version": "candidate_risk"}}],
                "paired_comparisons": rows,
            },
        )

    candidate = build_report(target_date="2026-09-08", data_root=tmp_path)[
        "candidate_summaries"
    ][0]

    assert candidate["candidate_probe_loss_budget_breach_count"] == 1
    assert candidate["candidate_probe_loss_budget_breach_rate_pct"] == 20.0
    assert candidate["candidate_probe_severe_tail_exposure_count"] == 1
    assert candidate["candidate_probe_severe_tail_rate_pct"] == 20.0
    assert candidate["candidate_probe_catastrophic_loss_count"] == 0
    assert (
        candidate["prompt_review_gate"]["checks"]["bounded_probe_risk_budget"] is True
    )
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_positive_selective_candidate_is_ranked_as_thin_review_not_discarded(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-09-07", "2026-09-08")):
        rows = []
        for offset in range(15):
            index = day_index * 15 + offset
            is_exposure = index == 0
            rows.append(
                {
                    "decision_trace_id": f"thin-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.2,
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "candidate_probe_worst_loss_pct": -0.2,
                    "delta_pct": 0.2,
                }
            )
        _write_json(
            paired_dir / f"ai_prompt_detailed_paired_replay_{source_date}_thin.json",
            {
                "target_date": source_date,
                "requests": [{"candidate": {"prompt_version": "candidate_thin"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-09-08", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]

    assert candidate["candidate_exposure_count"] == 1
    assert candidate["review_classification"] == "thin_positive_review"
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert report["thin_positive_review_candidate_count"] == 1
    assert report["selected_review_candidate"] is None


def test_status_distinguishes_cumulative_unchanged_from_current_update(
    tmp_path: Path,
) -> None:
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        },
    )

    report = build_report(target_date="2026-09-08", data_root=tmp_path)

    assert report["status"] == "cumulative_unchanged_no_new_exact_results"
    assert report["new_current_result_count"] == 0


def test_post_cutover_hashless_detailed_report_is_explicitly_rejected(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_hashless.json"
    )
    payload = _valid_detailed_payload(
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_hashless"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "hashless-1",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "candidate_primary_decision_value_pct": 0.1,
                    "outcome_return_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        }
    )
    payload.pop("artifact_content_sha256")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["candidate_count"] == 0
    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["source_contract_summary"]["rejection_reason_counts"] == {
        "artifact_content_sha256_missing_after_cutover": 1
    }


def test_pre_cutover_hashless_rows_are_diagnostic_and_do_not_poison_new_candidate(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for source_date, trace_id in (
        ("2026-09-06", "legacy-trace"),
        ("2026-09-07", "verified-trace"),
    ):
        payload = _valid_detailed_payload(
            {
                "target_date": source_date,
                "requests": [{"candidate": {"prompt_version": "candidate_continuity"}}],
                "paired_comparisons": [
                    {
                        "decision_trace_id": trace_id,
                        "stock_code": "005930",
                        "control_action": "WAIT",
                        "candidate_action": "WAIT",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": 0.1,
                        "delta_pct": 0.1,
                    }
                ],
            }
        )
        if source_date < calibration.DETAILED_SELF_HASH_CUTOVER_DATE:
            payload.pop("artifact_content_sha256")
        path = paired_dir / (
            f"ai_prompt_detailed_paired_replay_{source_date}_continuity.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 1
    assert candidate["source_integrity_complete"] is True
    assert candidate["source_report_count"] == 2
    assert candidate["verified_source_report_count"] == 1
    assert candidate["legacy_hashless_source_report_count"] == 1
    assert (
        report["source_contract_summary"]["legacy_hashless_diagnostic_row_count"] == 1
    )


def test_current_date_invalid_row_is_excluded_and_status_is_not_updated(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_row_gap.json",
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_row_gap"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "wrong-stage",
                    "stage": "holding",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "candidate_primary_decision_value_pct": 0.1,
                    "outcome_return_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        },
    )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["new_current_result_count"] == 0
    assert report["source_contract_summary"]["current_date_row_exclusion_count"] == 1


def test_non_native_source_count_is_rejected_before_calibration(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_bad_count.json",
        {
            "target_date": "2026-09-07",
            "schema_rejected_count": 0.5,
            "requests": [{"candidate": {"prompt_version": "candidate_bad_count"}}],
            "paired_comparisons": [],
        },
    )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["candidate_count"] == 0
    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["source_contract_summary"]["rejection_reason_counts"] == {
        "schema_rejected_count_invalid": 1
    }


def test_naive_decision_timestamp_is_excluded_from_exact_date_calibration(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_naive_time.json",
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_naive"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "naive-time",
                    "decision_ts": "2026-09-07T10:00:00",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "candidate_primary_decision_value_pct": 0.1,
                    "outcome_return_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        },
    )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["source_contract_summary"]["current_date_row_exclusion_count"] == 1
    assert report["source_reports"][0]["row_exclusion_reason_counts"] == {
        "decision_timestamp_invalid_or_naive": 1
    }


def test_runtime_policy_publication_receipt_requires_exact_source_binding():
    from src.engine.scalping.entry_setup_evidence import (
        MECHANISTIC_PRIMARY_ROLE_CONTRACT,
    )

    source = {
        "target_date": "2026-09-14",
        "artifact_content_sha256": "a" * 64,
    }
    published = {
        "target_date": "2026-09-15",
        "source_date": "2026-09-14",
        "source_artifact_sha256": "a" * 64,
        "role_contract": MECHANISTIC_PRIMARY_ROLE_CONTRACT,
        "actual_order_submitted": False,
        "all_continuous_adopted": True,
    }

    assert calibration._runtime_policy_publication_errors(published, source) == []
    mixed_successor = {
        **published,
        "target_date": "2026-09-21",
        "source_date": "2026-09-20",
        "publication_date": "2026-09-20",
        "machine_evaluation_source": {
            "source_date": "2026-09-14",
            "artifact_content_sha256": "a" * 64,
        },
    }
    assert calibration._runtime_policy_publication_errors(
        mixed_successor, source, publication_date="2026-09-20"
    ) == []
    assert calibration._runtime_policy_publication_errors(
        {
            **mixed_successor,
            "machine_evaluation_source": {
                **mixed_successor["machine_evaluation_source"],
                "source_date": "2026-09-13",
            },
        },
        source,
        publication_date="2026-09-20",
    ) == ["mechanistic_entry_runtime_policy_source_date_mismatch"]
    assert calibration._runtime_policy_publication_errors(
        {**published, "source_artifact_sha256": "b" * 64}, source
    ) == ["mechanistic_entry_runtime_policy_source_hash_mismatch"]
    assert calibration._runtime_policy_publication_errors(None, source) == [
        "mechanistic_entry_runtime_policy_not_published"
    ]


def _bound_microstructure_case_row(index, *, bundle='a' * 64, action='BLOCK'):
    from src.engine.ai_prompt_contracts import ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION

    return {
        'decision_trace_id': f'trace-{index}', 'evaluation_attempt_id': f'attempt-{index}',
        'scanner_promotion_id': f'promotion-{index}', 'decision_snapshot_id': f'snapshot-{index}',
        'decision_ts': '2026-09-17T10:00:00+09:00', 'source_date': '2026-09-17',
        'stock_code': '005930', 'effective_venue': 'KRX_NXT_INTEGRATED',
        'session_bucket': 'KRX_NXT_AFTERMARKET', 'bundle_sha256': bundle,
        'machine_action': action,
        'microstructure_evaluation_binding': {
            'capture_sha256': 'b' * 64, 'snapshot_identity_matches': True,
            'venue_session_matches': True, 'bundle_sha256': bundle,
            'flow_source_quality_status': 'fresh_consistent',
            'micro_recovery': {'source_usable': True},
            'reaction_context': {'microstructure_reaction_context_status': 'ok'},
            'micro_window': {'action': 'SOURCE_UNAVAILABLE', 'source_quality_status': 'source_gap'},
        },
        'entry_quality_path': {
            'status': 'evaluable', 'entry_quality_label': 'CLEAN_FAST_PROFIT',
            'cadence_complete': True,
        },
        'comparison': {'cost_evidence': {
            'selected_economic_cost_pct': 0.5,
            'selected_cost_basis': 'executable_estimated_cost_pct',
            'cost_source_sha256': 'c' * 64, 'missing_cost_imputed': False,
        }},
        'outcome_horizon_metrics': {'3m': {'status': 'observed', 'end_return_pct': 1, 'mae_pct': -0.2}},
        'ai_and_final_guard': {
            'join_status': 'exact_snapshot_machine_action_join', 'provider_called': True,
            'prompt_version': ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
            'ai_risk_verdict': 'PASS', 'decision_quality_contract_status': 'pass',
        },
    }


def test_microstructure_full_denominator_precedes_export_limit_and_keeps_policy_partitions():
    rows = [_bound_microstructure_case_row(i) for i in range(205)]
    rows.append(_bound_microstructure_case_row(205, bundle='d' * 64, action='ENTER_NOW'))
    rows.append(dict(rows[0]))
    table = calibration.build_machine_decision_case_table(rows)
    result = table['microstructure_evaluation']
    assert len(table['rows']) == 200
    assert table['duplicate_same_action_collapsed_count'] == 1
    assert result['case_count'] == result['cost_adjusted_outcome_count'] == 206
    assert result['denominator_preserved'] is True
    assert result['machine_enter_ai_routing_counts'] == {'PASS': 1}
    assert len(result['partitions']) == 2
    assert result['source_binding_counts']['micro_window_source_gap'] == 206
    assert result['actual_completed_ev_pct'] is None
    assert result['causal_model_delta_ev_pct'] is None
    assert all(p['cost_adjusted_3m_endpoint_cf']['mean_net_pct'] == 0.5 for p in result['partitions'])


def test_microstructure_cost_identity_cadence_and_conflict_exclusions_are_not_zero_returns():
    import copy

    rows = [_bound_microstructure_case_row(i) for i in range(6)]
    rows[1]['comparison']['cost_evidence']['selected_economic_cost_pct'] = None
    rows[2]['microstructure_evaluation_binding']['venue_session_matches'] = False
    rows[3]['entry_quality_path']['cadence_complete'] = False
    conflict = copy.deepcopy(rows[4])
    conflict['outcome_horizon_metrics']['3m']['end_return_pct'] = -2
    rows.append(conflict)
    table = calibration.build_machine_decision_case_table(rows)
    result = table['microstructure_evaluation']
    assert result['cost_adjusted_outcome_count'] == 2
    assert result['exclusion_counts'] == {
        'full_cost_contract_gap': 1, 'exact_identity_or_source_gap': 1,
        'mature_cadence_outcome_gap': 1, 'conflicting_exact_attempt': 2,
    }
    assert result['denominator_preserved'] is True


def test_machine_capture_binding_does_not_invent_venue_or_future_cutoff():
    from src.engine.scalping.microstructure_reaction_context import bind_machine_microstructure_source
    from datetime import datetime

    captured = '2026-09-17T10:00:00+09:00'
    epoch = datetime.fromisoformat(captured).timestamp() * 1000
    capture = {
        'captured_at': captured, 'machine_observation_sha256': 'a' * 64,
        'bundle_sha256': 'b' * 64,
        'label_context': {'snapshot_id': 's1', 'effective_venue': 'KRX', 'session_bucket': 'KRX_REGULAR'},
        'source': {'exact_payload': {'ai_market_snapshot_v1': {
            'snapshot_id': 's1', 'effective_venue': 'NXT', 'session_bucket': 'KRX_REGULAR'},
            'mechanistic_micro_window': {'cutoff_ms': epoch + 1}}, 'setup_evidence': {}},
    }
    binding = bind_machine_microstructure_source(capture)
    assert binding['venue_session_matches'] is False
    assert binding['micro_window_cutoff_valid'] is False
    assert binding['reaction_context'] == {}


def test_machine_cost_prerequisite_preserves_valid_source_and_does_not_backdate(monkeypatch, tmp_path):
    path = tmp_path / 'report/micro_reversion_economic_reference/micro_reversion_economic_reference_2026-09-17.json'
    path.parent.mkdir(parents=True)
    path.write_text('original-cost-proof')
    monkeypatch.setattr(calibration, '_hierarchy_cost_profiles', lambda *a, **k: {'005930': {'verified': True}})
    receipt = calibration.ensure_machine_economic_reference(data_root=tmp_path, target_date='2026-09-17')
    assert receipt['status'] == 'existing_verified_sources_preserved'
    assert path.read_text() == 'original-cost-proof'
    monkeypatch.setattr(calibration, '_hierarchy_cost_profiles', lambda *a, **k: {})
    receipt = calibration.ensure_machine_economic_reference(data_root=tmp_path, target_date='2026-06-05')
    assert receipt['status'] == 'source_gap_historical_official_master_unavailable'
    assert not (path.parent / 'micro_reversion_economic_reference_2026-06-05.json').exists()


def test_capture_population_survives_cost_exclusion_and_collapses_same_capture():
    from src.engine.scalping.microstructure_reaction_context import summarize_machine_capture_population
    capture = {
        'machine_observation_sha256': 'a' * 64, 'bundle_sha256': 'b' * 64,
        'captured_at': '2026-09-17T10:00:00+09:00',
        'label_context': {'snapshot_id': 's', 'effective_venue': 'KRX_NXT_INTEGRATED', 'session_bucket': 'krx_nxt_aftermarket'},
        'source': {'assessment': {'action': 'BLOCK'}, 'exact_payload': {'ai_market_snapshot_v1': {
            'snapshot_id': 's', 'effective_venue': 'KRX_NXT_INTEGRATED', 'session_bucket': 'krx_nxt_aftermarket'}}, 'setup_evidence': {}},
    }
    result = summarize_machine_capture_population([capture, capture])
    assert result['verified_capture_count'] == 2
    assert result['unique_verified_capture_count'] == 1
    assert result['duplicate_capture_collapsed_count'] == 1
    assert result['partitions'][0]['source_binding_counts'] == {'exact_bound': 1, 'micro_window_source_gap': 1}


def test_machine_cost_prerequisite_uses_private_sources_not_live_provider_budget(monkeypatch, tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping.micro_reversion import economic_reference as reference, economic_reference_owner as owner
    import json

    day = datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    calls = []
    def build_sources(**kwargs):
        calls.append(kwargs)
        root = kwargs['output_root']
        root.mkdir(parents=True)
        (root / 'provider_budget_policy.json').write_text('private-source-only')
    monkeypatch.setattr(owner, 'build_daily_sources', build_sources)
    monkeypatch.setattr(reference, 'build_daily_resolution', lambda **kwargs: {'verified': True, 'status': 'verified', 'target_date': day})
    receipt = calibration.ensure_machine_economic_reference(data_root=tmp_path, target_date=day)
    assert receipt['verified'] is True
    assert calls[0]['output_root'] == tmp_path / 'report/micro_reversion_economic_reference/machine_source_inputs' / day
    assert not (tmp_path / 'policy').exists()
    assert json.loads((tmp_path / 'report/micro_reversion_economic_reference' / f'micro_reversion_economic_reference_{day}.json').read_text())['target_date'] == day


def test_calibration_write_publishes_machine_link_before_policy_with_valid_parent_seal(monkeypatch, tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    from src.engine.scalping.microstructure_reaction_context import microstructure_summary_contract
    import json

    table = calibration.build_machine_decision_case_table([_bound_microstructure_case_row(0)])
    report = {'schema': calibration.SCHEMA, 'target_date': '2026-09-17',
              'runtime_effect': False, 'allowed_runtime_apply': False,
              'hierarchical_entry_quality': {'machine_decision_case_table': table}}
    monkeypatch.setattr(calibration, 'build_report', lambda **kwargs: calibration._with_artifact_content_sha256(report))
    monkeypatch.setattr(calibration, 'ensure_machine_economic_reference', lambda **kwargs: {'status': 'source_only_test'})
    published = []
    def publish(path, **kwargs):
        parent = json.loads(path.read_text())
        assert calibration._artifact_content_sha256_valid(parent)
        linked_path = tmp_path / 'report/microstructure_reaction_context/microstructure_reaction_context_2026-09-17.json'
        linked = microstructure_summary_contract(json.loads(linked_path.read_text())['summary'])['machine_primary_auxiliary_evaluation']
        assert linked['cost_adjusted_outcome_count'] == 1
        published.append(path)
    monkeypatch.setattr(policy, 'publish', publish)
    assert calibration.main(['--target-date', '2026-09-17', '--data-root', str(tmp_path), '--write']) == 0
    assert len(published) == 1


def test_integrated_and_premarket_cost_reference_requires_exact_broker_route_not_venue_guess():
    import copy
    capture = {'label_context': {'snapshot_id': 's', 'broker_route': 'NXT', 'market_data_route': 'krx_nxt_integrated'},
               'source': {'exact_payload': {'ai_market_snapshot_v1': {'snapshot_id': 's', 'broker_route': 'NXT', 'market_data_route': 'krx_nxt_integrated'}}}}
    for cohort in [('KRX_NXT_INTEGRATED', 'KRX_NXT_AFTERMARKET'), ('PREMARKET_KRX_LIKE', 'PREMARKET_KRX_LIKE')]:
        assert calibration._machine_capture_cost_reference_venue(capture, cohort) == 'NXT'
        missing = copy.deepcopy(capture)
        missing['source']['exact_payload']['ai_market_snapshot_v1'].pop('broker_route')
        assert calibration._machine_capture_cost_reference_venue(missing, cohort) is None
        conflict = copy.deepcopy(capture)
        conflict['source']['exact_payload']['ai_market_snapshot_v1']['broker_route'] = 'SOR'
        assert calibration._machine_capture_cost_reference_venue(conflict, cohort) is None
    assert calibration._machine_capture_cost_reference_venue({}, ('KRX', 'KRX_REGULAR')) == 'KRX'


def test_machine_micro_window_is_bound_to_market_data_item_not_order_route():
    from datetime import datetime
    from src.engine.scalping.microstructure_reaction_context import bind_machine_microstructure_source
    capture = {'captured_at': '2026-09-17T10:00:00+09:00',
               'label_context': {'stock_code': '005930', 'broker_route': 'SOR', 'market_data_route': 'krx_only'},
               'source': {'exact_payload': {'mechanistic_micro_window': {
                   'item': '005930', 'cutoff_ms': int(datetime.fromisoformat('2026-09-17T10:00:00+09:00').timestamp()*1000)}}}}
    assert bind_machine_microstructure_source(capture)['micro_window_item_matches'] is True
    capture['source']['exact_payload']['mechanistic_micro_window']['item'] = '005930_AL'
    assert bind_machine_microstructure_source(capture)['micro_window_item_matches'] is False


def test_cost_prerequisite_only_never_builds_report_or_publishes_policy(monkeypatch, tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    def forbidden(**kwargs):
        raise AssertionError('unexpected report or policy work')
    monkeypatch.setattr(calibration, 'build_report', forbidden)
    monkeypatch.setattr(policy, 'publish', forbidden)
    monkeypatch.setattr(calibration, 'ensure_machine_economic_reference', lambda **kwargs: {'status': 'verified', 'verified': True})
    assert calibration.main(['--target-date', '2026-09-17', '--data-root', str(tmp_path), '--write', '--ensure-economic-reference-only']) == 0
    monkeypatch.setattr(calibration, 'ensure_machine_economic_reference', lambda **kwargs: {'status': 'source_gap_historical_official_master_unavailable'})
    assert calibration.main(['--target-date', '2026-09-17', '--write', '--ensure-economic-reference-only']) == 2


def test_machine_only_write_reuses_exact_input_fingerprint(monkeypatch, tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    target = "2026-09-17"
    path = calibration.report_path(target, tmp_path / "report")
    path.parent.mkdir(parents=True)
    report = calibration._with_artifact_content_sha256(
        {
            "schema": calibration.SCHEMA,
            "target_date": target,
            "report_scope": "main_mechanistic_entry",
            "noncompact_sections_refreshed": True,
            "evaluation_contract_version": (
                calibration.MAIN_MECHANISTIC_EVALUATION_CONTRACT_VERSION
            ),
            "evaluation_fingerprint": "f" * 64,
            "status": "main_mechanistic_entry_full_evaluation_complete",
            "candidate_count": 0,
            "selected_review_candidate": None,
            "ofi_smoothing_audit": {"status": "not_recomputed_machine_only"},
            "machine_full_evaluation": {"state": "evaluated_no_edge"},
            "hierarchical_entry_quality": {},
        }
    )
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(
        calibration,
        "_main_mechanistic_input_fingerprint",
        lambda *_args, **_kwargs: "f" * 64,
    )
    monkeypatch.setattr(
        calibration,
        "ensure_machine_economic_reference",
        lambda **_kwargs: {"status": "existing_verified_sources_preserved"},
    )
    monkeypatch.setattr(
        calibration,
        "build_main_mechanistic_report",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected rebuild")),
    )
    monkeypatch.setattr(policy, "publish", lambda *_args, **_kwargs: None)

    assert calibration.main(
        [
            "--target-date",
            target,
            "--data-root",
            str(tmp_path),
            "--machine-only",
            "--write",
        ]
    ) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == report


def test_main_fingerprint_ignores_same_compact_projection_rewrite(
    monkeypatch, tmp_path
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    monkeypatch.setattr(policy, "load_effective", lambda **_kwargs: None)
    projection = (
        tmp_path
        / "report/ai_entry_setup_paired_replay_batch"
        / "compact_auxiliary_paired_economic_2026-09-17.source.json"
    )
    projection.parent.mkdir(parents=True)
    projection.write_text('{"sealed":"same"}\n', encoding="utf-8")
    first = calibration._main_mechanistic_input_fingerprint(
        tmp_path, "2026-09-17"
    )
    replacement = projection.with_suffix(".replacement")
    replacement.write_bytes(projection.read_bytes())
    replacement.replace(projection)
    assert (
        calibration._main_mechanistic_input_fingerprint(tmp_path, "2026-09-17")
        == first
    )
    projection.write_text('{"sealed":"changed"}\n', encoding="utf-8")
    assert (
        calibration._main_mechanistic_input_fingerprint(tmp_path, "2026-09-17")
        != first
    )


def test_machine_microstructure_diagnostic_preserves_existing_auxiliary_gate():
    table = calibration.build_machine_decision_case_table([_bound_microstructure_case_row(1, action='ENTER_NOW')], source_receipt={
        'tuning_input_allowed': True, 'machine_threshold_tuning_input_allowed': True,
        'compact_auxiliary_policy_measurement': {'measurement_allowed': False},
    })
    summary = table['microstructure_evaluation']
    assert summary['cost_adjusted_outcome_count'] == 1
    assert summary['machine_tuning_input_allowed'] is True
    assert summary['auxiliary_tuning_input_allowed'] is False


def test_current_machine_operating_filter_uses_same_downstream_ai_and_model():
    from src.tests.test_entry_setup_paired_replay_batch import full_compact_proof
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    proof=full_compact_proof()
    source=proof['chronological_validation']['holdout_pairs'][0]
    # Current machine ENTER_NOW with an actual VETO remains no exposure even
    # when a machine challenger retains that selection.
    row=dict(decision_trace_id='machine-exact',comparison={'control_action':'BUY'},
        operating_comparison_input=source,operating_model_validation=proof['owner_execution_model_validation'],
        operating_runtime_cost_receipt={'delta_krw':0.})
    unchanged=calibration._mechanistic_paired_population_metrics([row],[row])
    assert unchanged['paired_terminal_proxy_delta_pct']==0.
    assert unchanged['operating_economic_comparison']['status']=='supported_operating_comparison'
    assert unchanged['paired_terminal_contract_complete']
    assert unchanged['operating_economic_promotion_pass'] is False
    assert unchanged['baseline_preserved'] is True
    assert unchanged['daily_net_profit_delta_krw'] == 0.0
    assert unchanged['daily_net_profit_status'] == 'baseline_preserved_no_independent_policy_change'
    # Recompute a signed losing operating arm, never copy a real SELL outcome.
    import copy
    losing=copy.deepcopy(row)
    s=losing['operating_comparison_input']
    s['incumbent_verdict']='PASS'
    replay=s['owner_replay']; arm=next(iter(replay['operating_arms'].values()))
    for key in ('net_pnl_krw','stress_net_pnl_krw','net_return_pct','stress_net_return_pct'):
        arm[key]=-abs(arm[key])
    arm['sha256']=compact.digest({k:v for k,v in arm.items() if k!='sha256'})
    replay['replay_sha256']=compact.digest({k:v for k,v in replay.items() if k!='replay_sha256'})
    filtered=calibration._mechanistic_paired_population_metrics([losing],[])
    assert filtered['operating_economic_comparison']['robust_paired_delta_ev_lower_bound_pct']>0
    assert filtered['operating_economic_comparison']['candidate']['net_pnl_krw']==0.
    assert filtered['paired_terminal_contract_complete']
