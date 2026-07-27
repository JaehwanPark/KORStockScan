from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.scalping import ai_decision_quality as quality

KST = ZoneInfo("Asia/Seoul")


def _payload():
    return {
        "payload_sha256": "payload-1",
        "replay_exact": True,
        "sanitized_user_input": {
            "entry_candle_context": {
                "schema": quality.ENTRY_CONTEXT_SCHEMA,
                "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
                "bars": [
                    {
                        "t": "09:00",
                        "o": 100,
                        "h": 101,
                        "l": 99,
                        "c": 100,
                        "v": 10,
                        "forming": False,
                    }
                ],
            }
        },
    }


def _trace(action="DROP"):
    return {
        "decision_trace_id": "trace-1",
        "decision_ts": "2026-07-27T09:00:00+09:00",
        "decision_stage": "entry",
        "endpoint": "analyze_target",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_replay_exact": True,
        "request_capture_status": "captured",
        "payload_sha256": "payload-1",
        "prompt_version": "entry_v1",
        "prompt_sha256": "prompt-1",
        "provider_actual": "openai",
        "model": "gpt-test",
        "request_temperature": 0,
        "request_reasoning_effort": "medium",
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "action": action,
    }


def _pending(action="DROP"):
    return {
        "schema": "ai_decision_outcome_label_v1",
        "label_id": "trace-1:v1",
        "decision_trace_id": "trace-1",
        "decision_stage": "entry",
        "stock_code": "005930",
        "decision_ts": "2026-07-27T09:00:00+09:00",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "reference_price": 100,
        "target_price": 101,
        "adverse_price": 99,
        "action": action,
        "confidence": 90,
        "record_id": "record-1",
    }


def test_control_manifest_freezes_exact_post_promotion_signature():
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[_payload()],
    )
    assert report["status"] == "control_manifest_frozen_collect_exact_samples"
    assert report["controls"][0]["prompt_sha256"] == "prompt-1"
    assert report["prompt_model_provider_change_count"] == 0
    assert report["runtime_effect"] is False


def test_control_manifest_rejects_non_exact_preflight_mode():
    trace = {**_trace(), "input_preflight_mode": "baseline_v1"}
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[_payload()],
    )
    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"]["input_preflight_not_exact_v2"] == 1


def test_control_manifest_rejects_canonical_context_without_completed_bars():
    payload = _payload()
    payload["sanitized_user_input"]["entry_candle_context"]["bars"] = [
        {"t": "09:00", "c": 100, "forming": True}
    ]
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[payload],
    )
    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"]["canonical_completed_bars_missing"] == 1


def test_holding_context_contract_reads_nested_candle_bundle_and_bars():
    trace = {
        **_trace(),
        "decision_stage": "holding",
        "endpoint": "holding_score",
    }
    payload = {
        "payload_sha256": "payload-1",
        "replay_exact": True,
        "sanitized_user_input": {
            "holding_decision_context": {
                "schema": quality.HOLDING_CONTEXT_SCHEMA,
                "candle": {
                    "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
                    "bars": [{"minute": "09:00", "close": 100, "is_forming": False}],
                },
            }
        },
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[payload],
    )
    assert report["status"] == "control_manifest_frozen_collect_exact_samples"


def test_mature_outcome_labels_calculates_mfe_mae_first_hit_and_correlation():
    prices = [
        {
            "timestamp": "2026-07-27T09:01:00+09:00",
            "stock_code": "A005930",
            "price": 98,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass",
        },
        {
            "timestamp": "2026-07-27T09:02:00+09:00",
            "stock_code": "005930",
            "price": 102,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass",
        },
    ]
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=prices,
        lifecycle_rows=[
            {
                "timestamp": "2026-07-27T09:02:30+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "actual_order_submitted": True,
                "filled": True,
                "realized_profit_pct": 0.5,
            }
        ],
        as_of=datetime(2026, 7, 27, 9, 3, tzinfo=KST),
    )
    row = labels[0]
    assert row["label_status"] == "partial"
    assert row["horizon_metrics"]["1m"]["mae_pct"] == -2
    assert row["horizon_metrics"]["1m"]["first_hit"] == "adverse"
    assert row["horizon_metrics"]["3m"]["mfe_pct"] == 2
    assert row["correlation"]["actual_order_submitted"] is True
    assert row["correlation"]["status"] == "exact_matched"
    assert row["correlation"]["realized_separate_from_counterfactual"] is True


def test_outcome_correlation_does_not_treat_missing_or_cross_symbol_as_zero_fill():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 101,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            }
        ],
        lifecycle_rows=[
            {
                "timestamp": "2026-07-27T09:01:30+09:00",
                "stock_code": "000660",
                "record_id": "record-1",
                "actual_order_submitted": True,
                "filled": True,
            }
        ],
        as_of=datetime(2026, 7, 27, 9, 2, tzinfo=KST),
    )

    correlation = labels[0]["correlation"]
    assert correlation["status"] == "open_unresolved"
    assert correlation["matched_event_count"] == 0
    assert correlation["actual_order_submitted"] is None
    assert correlation["fill_observed"] is None


def test_quality_baseline_classifies_false_drop():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending("DROP")],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:05:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            },
            {
                "timestamp": "2026-07-27T09:10:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            },
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )
    labels = quality.annotate_primary_cohort_eligibility(
        labels=labels,
        traces=[_trace("DROP")],
        payloads=[_payload()],
        promotion={"promoted_at": "2026-07-27T08:30:00+09:00"},
    )
    baseline = quality.build_quality_baseline(target_date="2026-07-27", labels=labels)
    assert baseline["status"] == "control_error_baseline_ready"
    assert baseline["taxonomy_counts"]["false_drop"] == 1
    assert baseline["rows"][0]["outcome_return_pct"] == 2
    assert baseline["source_quality_adjusted_ev_pct"] == 0


def test_quality_baseline_waits_for_stage_primary_horizon():
    label = {
        **_pending(),
        "label_status": "partial",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {"3m": {"end_return_pct": 1.0}},
    }
    baseline = quality.build_quality_baseline(target_date="2026-07-27", labels=[label])
    assert baseline["status"] == "partial_horizons_keep_maturing"
    assert baseline["eligible_sample_count"] == 0
    assert baseline["primary_horizon_pending_count"] == 1


def test_quality_baseline_excludes_non_exact_primary_cohort():
    label = {
        **_pending(),
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": False,
        "primary_cohort_exclusion_reasons": ["input_preflight_not_exact_v2"],
        "horizon_metrics": {"10m": {"end_return_pct": 2.0}},
    }

    baseline = quality.build_quality_baseline(
        target_date="2026-07-27",
        labels=[label],
    )

    assert baseline["status"] == "partial_horizons_keep_maturing"
    assert baseline["eligible_sample_count"] == 0
    assert baseline["primary_cohort_ineligible_count"] == 1


def test_mature_outcome_requires_fresh_observation_near_horizon_end():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )

    assert "1m" in labels[0]["horizon_metrics"]
    assert "10m" not in labels[0]["horizon_metrics"]
    assert 10 in labels[0]["pending_horizons_min"]


def test_mature_outcome_rejects_uncontracted_price_source():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:10:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "not_recorded",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )

    assert labels[0]["label_status"] == "pending"
    assert labels[0]["source_quality_status"] == "source_quality_blocked"


def test_overnight_outcome_uses_next_day_first_session_window():
    pending = {
        **_pending("HOLD_OVERNIGHT"),
        "decision_stage": "overnight",
        "decision_ts": "2026-07-27T19:50:00+09:00",
        "effective_venue": "NXT",
        "session_bucket": "NXT_AFTERMARKET",
    }
    labels = quality.mature_outcome_labels(
        pending_labels=[pending],
        price_rows=[
            {
                "timestamp": "2026-07-27T19:51:00+09:00",
                "stock_code": "005930",
                "price": 120,
                "effective_venue": "NXT",
                "session_bucket": "NXT_AFTERMARKET",
                "source_quality": "pass",
            },
            {
                "timestamp": "2026-07-28T08:00:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "session_bucket": "PREMARKET_KRX_LIKE",
                "source_quality": "pass",
            },
            {
                "timestamp": "2026-07-28T08:10:00+09:00",
                "stock_code": "005930",
                "price": 103,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "session_bucket": "PREMARKET_KRX_LIKE",
                "source_quality": "pass",
            },
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 28, 8, 11, tzinfo=KST),
    )

    metric = labels[0]["horizon_metrics"]["10m"]
    assert metric["window_basis"] == "next_session_from_first_observation"
    assert metric["mfe_pct"] == 3
    assert metric["gap_from_reference_pct"] == 2
    assert labels[0]["stage_outcome"]["next_session_date"] == "2026-07-28"
    assert labels[0]["stage_outcome"]["next_session_bucket"] == "PREMARKET_KRX_LIKE"


def test_candidate_contract_requires_structured_reasons():
    response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.2,
        "expected_downside_pct": -0.5,
        "confidence": 70,
        "reason_codes": ["trend_tape_aligned"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "supportive",
            "risk": "low",
            "uncertainty": "low",
        },
    }
    assert quality.validate_candidate_response(response, stage="entry") == []
    assert quality.decision_quality_v2_system_prompt("entry").isascii()

    invalid = {**response, "reason_codes": ["Not canonical"]}
    invalid.pop("expected_downside_pct")
    assert quality.validate_candidate_response(invalid, stage="entry") == [
        "expected_downside_pct_missing",
        "reason_codes_invalid",
    ]


def test_paired_replay_uses_same_exact_payload_and_has_no_runtime_authority():
    control_manifest = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[_payload()],
    )
    labels = [
        {
            **_pending(),
            "label_status": "mature",
            "source_quality_status": "pass",
            "primary_cohort_eligible": True,
            "horizon_metrics": {
                "10m": {
                    "end_return_pct": 2.0,
                    "first_hit": "target",
                }
            },
        }
    ]
    requests = quality.prepare_paired_replay_requests(
        control_manifest=control_manifest,
        traces=[_trace()],
        payloads=[_payload()],
        labels=labels,
    )
    assert len(requests) == 1
    assert requests[0]["payload_sha256"] == "payload-1"
    assert requests[0]["runtime_effect"] is False
    response = {
        "edge_state": "NO_EDGE",
        "action": "WAIT",
        "expected_upside_pct": 0.3,
        "expected_downside_pct": -0.4,
        "confidence": 60,
        "reason_codes": ["no_positive_edge"],
        "evidence": {
            "trend": "mixed",
            "liquidity": "supportive",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
        },
    }
    results = quality.run_paired_replay(
        requests,
        control_runner=lambda request: {"action": "DROP"},
        candidate_runner=lambda request: response,
    )
    assert results[0]["same_payload_confirmed"] is True
    assert results[0]["status"] == "pass"
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=requests,
        results=results,
        labels=labels,
    )
    assert report["control_source_quality_adjusted_ev_pct"] == 0
    assert report["candidate_source_quality_adjusted_ev_pct"] == 0
    assert report["paired_comparable_count"] == 1
    assert report["buckets"] == [
        {
            "stage": "entry",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sample_count": 1,
            "control_source_quality_adjusted_ev_pct": 0,
            "candidate_source_quality_adjusted_ev_pct": 0,
            "source_quality_adjusted_ev_delta_pct": 0,
            "missed_upside_reduction_count": 0,
            "adverse_first_candidate_exposure_count": 0,
        }
    ]


def test_paired_report_excludes_schema_rejected_candidate_from_ev():
    labels = [
        {
            **_pending(),
            "label_status": "mature",
            "source_quality_status": "pass",
            "primary_cohort_eligible": True,
            "horizon_metrics": {
                "10m": {
                    "end_return_pct": 2.0,
                    "first_hit": "target",
                }
            },
        }
    ]
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=[],
        results=[
            {
                "decision_trace_id": "trace-1",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "schema_rejected",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {"action": "BUY"},
            }
        ],
        labels=labels,
    )

    assert report["status"] == "candidate_rejected_no_runtime_apply"
    assert report["paired_comparable_count"] == 0
    assert report["candidate_source_quality_adjusted_ev_pct"] is None
