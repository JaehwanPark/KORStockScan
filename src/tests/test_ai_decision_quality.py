import sys
from datetime import datetime
from types import SimpleNamespace
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


def test_control_manifest_rejects_explicit_sparse_canonical_decision_window():
    payload = _payload()
    payload["sanitized_user_input"]["entry_candle_context"]["source_quality"] = {
        "decision_window": {
            "status": "sparse_observed_minutes",
            "provider_call_allowed": True,
            "missing_bar_count": 2,
        }
    }
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
    assert (
        report["excluded_counts"]["canonical_decision_window_source_quality_blocked"]
        == 1
    )


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


def test_kiwoom_completed_minute_loader_excludes_forming_and_wrong_session_bars():
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return (
            [
                {
                    "source_timestamp": "20260727085900",
                    "현재가": 99,
                },
                {
                    "source_timestamp": "20260727090100",
                    "현재가": 101,
                    "고가": 103,
                    "저가": 98,
                },
                {
                    "source_timestamp": "20260727090300",
                    "현재가": 103,
                },
            ],
            {
                "api_id": "ka10080",
                "received_count": 3,
                "cont_yn_seen": True,
            },
        )

    prices, provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[_pending()],
        as_of=datetime(2026, 7, 27, 9, 3, 20, tzinfo=KST),
        fetcher=fetcher,
    )

    assert calls == [("005930", "005930")]
    assert [row["timestamp"] for row in prices] == ["2026-07-27T09:01:00+09:00"]
    assert prices[0]["source_quality"] == "pass_completed_ka10080_bar"
    assert prices[0]["high"] == 103
    assert prices[0]["low"] == 98
    assert provenance[0]["source_quality_status"] == "pass_target_window_available"
    assert provenance[0]["target_completed_bar_count"] == 1


def test_mature_outcome_uses_bar_high_low_and_marks_same_bar_first_hit_ambiguous():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 100,
                "high": 102,
                "low": 98,
                "close": 100,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass_completed_ka10080_bar",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 2, tzinfo=KST),
    )

    metric = labels[0]["horizon_metrics"]["1m"]
    assert metric["mfe_pct"] == 2
    assert metric["mae_pct"] == -2
    assert metric["end_return_pct"] == 0
    assert metric["first_hit"] == "ambiguous_same_bar"


def test_kiwoom_completed_minute_loader_preserves_nxt_request_suffix():
    pending = {
        **_pending(),
        "effective_venue": "NXT",
        "session_bucket": "NXT_AFTERMARKET",
    }
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return (
            [{"source_timestamp": "20260727160100", "현재가": 101}],
            {"api_id": "ka10080", "received_count": 1},
        )

    prices, _provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[pending],
        as_of=datetime(2026, 7, 27, 16, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert calls == [("005930", "005930_NX")]
    assert prices[0]["effective_venue"] == "NXT"
    assert prices[0]["session_bucket"] == "NXT_AFTERMARKET"


def test_kiwoom_completed_minute_loader_preserves_sor_request_suffix():
    pending = {
        **_pending(),
        "effective_venue": "SOR",
        "session_bucket": "KRX_REGULAR",
    }
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return (
            [{"source_timestamp": "20260727090100", "현재가": 101}],
            {"api_id": "ka10080", "received_count": 1},
        )

    prices, _provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[pending],
        as_of=datetime(2026, 7, 27, 9, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert calls == [("005930", "005930_AL")]
    assert prices[0]["effective_venue"] == "SOR"


def test_kiwoom_completed_minute_loader_accepts_nxt_overlap_session():
    pending = {
        **_pending(),
        "effective_venue": "NXT",
        "session_bucket": "NXT_REGULAR_OVERLAP",
    }

    def fetcher(_stock_code, _request_code):
        return (
            [{"source_timestamp": "20260727120100", "현재가": 101}],
            {"api_id": "ka10080", "received_count": 1},
        )

    prices, _provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[pending],
        as_of=datetime(2026, 7, 27, 12, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert prices[0]["session_bucket"] == "NXT_REGULAR_OVERLAP"


def test_kiwoom_completed_minute_loader_blocks_ambiguous_or_conflicting_route():
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return [], {}

    prices, provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[
            {
                **_pending(),
                "effective_venue": "PREMARKET_KRX_LIKE",
                "session_bucket": "PREMARKET_KRX_LIKE",
            },
            {
                **_pending(),
                "effective_venue": "KRX",
                "session_bucket": "NXT_AFTERMARKET",
            },
        ],
        as_of=datetime(2026, 7, 27, 16, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert prices == []
    assert calls == []
    assert {row["fetch_error"] for row in provenance} == {
        "unsupported_effective_venue",
        "venue_session_conflict",
    }
    assert all(
        row["source_quality_status"] == "source_quality_blocked" for row in provenance
    )


def test_score_outcome_correlation_report_uses_spearman_primary_and_sample_floor():
    labels = []
    for index in range(30):
        score = float(index)
        labels.append(
            {
                **_pending(),
                "decision_trace_id": f"trace-{index}",
                "stock_code": f"{index % 10:06d}",
                "score": score,
                "label_status": "partial",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "10m": {
                        "mfe_pct": score,
                        "mae_pct": score - 29.0,
                    }
                },
            }
        )

    report = quality.build_score_outcome_correlation_report(
        target_date="2026-07-27",
        labels=labels,
    )

    assert report["status"] == "exploratory_score_outcome_correlation_available"
    bucket = report["buckets"][0]
    assert bucket["sample_floor_pass"] is True
    assert bucket["score_vs_mfe_pct"]["spearman"] == 1.0
    assert bucket["score_vs_mae_pct"]["spearman"] == 1.0
    assert bucket["score_vs_adverse_magnitude_pct"]["spearman"] == -1.0
    assert bucket["interpretation_contract"]["pearson_role"] == "diagnostic_only"


def test_default_sources_skips_large_pipeline_load_when_not_requested(monkeypatch):
    loaded_paths = []

    def fake_load(path):
        loaded_paths.append(path)
        return []

    monkeypatch.setattr(quality, "_load_jsonl", fake_load)
    sources = quality._default_sources("2026-07-27", include_pipeline=False)

    assert sources["pipeline"] == []
    assert all(path.parent != quality.PIPELINE_DIR for path in loaded_paths)


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
        "expected_edge_values_required",
        "reason_codes_invalid",
    ]
    unsupported = {**response, "reason_codes": ["invented_ascii_reason"]}
    assert quality.validate_candidate_response(unsupported, stage="entry") == [
        "reason_codes_invalid"
    ]
    duplicate = {
        **response,
        "reason_codes": ["trend_tape_aligned", "trend_tape_aligned"],
    }
    assert quality.validate_candidate_response(duplicate, stage="entry") == [
        "reason_codes_invalid"
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
    assert report["status"] == "paired_replay_complete_candidate_quality_rejected"
    assert report["candidate_quality_gate_pass"] is False
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
            "new_missed_upside_count": 0,
            "control_adverse_first_exposure_count": 0,
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


def test_prepare_paired_replay_marks_stage_floor_without_cherry_picking():
    traces = []
    payloads = []
    labels = []
    for index in range(30):
        trace_id = f"trace-{index}"
        payload_hash = f"payload-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        traces.append(
            {
                **_trace(),
                "decision_trace_id": trace_id,
                "payload_sha256": payload_hash,
            }
        )
        payloads.append(
            {
                **_payload(),
                "payload_sha256": payload_hash,
                "endpoint": "analyze_target",
            }
        )
        labels.append(
            {
                **_pending(),
                "decision_trace_id": trace_id,
                "label_id": f"{trace_id}:v1",
                "stock_code": stock_code,
                "label_status": "mature",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "10m": {"end_return_pct": 1.0, "first_hit": "target"}
                },
            }
        )
    control = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=traces,
        payloads=payloads,
    )

    requests = quality.prepare_paired_replay_requests(
        control_manifest=control,
        traces=traces,
        payloads=payloads,
        labels=labels,
    )

    assert len(requests) == 30
    assert all(request["sample_floor"]["pass"] is True for request in requests)
    assert requests[0]["sample_floor"]["unique_symbols"] == 10


def test_paired_replay_retries_schema_once_and_report_omits_exact_payload():
    request = {
        "paired_replay_id": "pair-1",
        "decision_trace_id": "trace-1",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "payload-1",
        "exact_payload": {"secret_free_exact": True},
        "candidate": {"system_prompt_sha256": "candidate-prompt-1"},
        **quality.OFFLINE_CONTRACT,
    }
    responses = [
        {"action": "WAIT"},
        {
            "edge_state": "NO_EDGE",
            "action": "WAIT",
            "expected_upside_pct": 0.2,
            "expected_downside_pct": -0.4,
            "confidence": 55,
            "reason_codes": ["no_positive_edge"],
            "evidence": {
                "trend": "mixed",
                "liquidity": "supportive",
                "tape": "mixed",
                "risk": "medium",
                "uncertainty": "medium",
            },
        },
    ]

    def candidate_runner(attempt_request):
        if len(responses) == 1:
            assert attempt_request["candidate_schema_correction_errors"]
        return responses.pop(0)

    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "DROP"},
        candidate_runner=candidate_runner,
    )
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=[request],
        results=results,
        labels=[],
    )

    assert results[0]["status"] == "pass"
    assert len(results[0]["candidate_attempts"]) == 2
    assert "exact_payload" not in report["requests"][0]
    assert report["candidate_provider_none_count"] == 0


def test_openai_candidate_parse_gap_is_retryable_and_secret_free(monkeypatch):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="resp-test",
                output_text="not-json",
                usage=SimpleNamespace(
                    input_tokens=12,
                    output_tokens=3,
                    total_tokens=15,
                ),
            )

    class FakeOpenAI:
        def __init__(self, *, api_key, max_retries):
            assert api_key == "test-secret"
            assert max_retries == 0
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    request = {
        "paired_replay_id": "pair-1",
        "stage": "entry",
        "exact_payload": {"value": 1},
        "control": {"provider": "openai", "model": "gpt-test"},
        "candidate": {
            "provider": "openai",
            "model": "gpt-test",
            "system_prompt": "Return JSON.",
        },
        **quality.OFFLINE_CONTRACT,
    }

    envelope = quality.execute_openai_prompt_v2_candidate(
        request,
        api_keys=["test-secret"],
    )

    assert envelope["candidate_response"] == {}
    assert envelope["provider_provenance"]["parse_error"] == (
        "candidate_response_json_invalid"
    )
    assert envelope["provider_provenance"]["response_id"] == "resp-test"
    assert "test-secret" not in str(envelope)
    assert captured["store"] is False
    assert captured["input"] == '{"value":1}'
