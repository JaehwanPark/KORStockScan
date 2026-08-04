import json
from types import SimpleNamespace

from src.engine.scalping import ai_stage_coverage_replay as replay


def _control():
    return {
        "controls": [
            {
                "endpoint": "analyze_target",
                "prompt_version": "decision_quality_v2_7",
                "prompt_sha256": "prompt-entry",
                "provider_actual": "openai",
                "model": "gpt-test",
                "request_temperature": 0,
                "request_reasoning_effort": "medium",
            },
            {
                "endpoint": "holding_score",
                "prompt_version": "holding_score_v2",
                "prompt_sha256": "prompt-1",
                "provider_actual": "openai",
                "model": "gpt-test",
                "request_temperature": 0,
                "request_reasoning_effort": "medium",
            },
            {
                "endpoint": "holding_flow",
                "prompt_version": "flow_v1",
                "prompt_sha256": "prompt-flow",
                "provider_actual": "openai",
                "model": "gpt-5.4-mini",
                "request_temperature": 0,
                "request_reasoning_effort": "medium",
            },
            {
                "endpoint": "entry_price",
                "prompt_version": "entry_price_v1",
                "prompt_sha256": "prompt-2",
                "provider_actual": "bedrock",
                "model": "qwen3_32b",
                "request_temperature": 0,
                "request_reasoning_effort": None,
            },
        ]
    }


def _trace(endpoint="holding_score"):
    holding = endpoint == "holding_score"
    entry = endpoint == "analyze_target"
    return {
        "decision_trace_id": f"trace-{endpoint}",
        "decision_ts": "2026-07-29T12:00:00+09:00",
        "decision_stage": (
            "holding" if holding else ("entry" if entry else "entry_price")
        ),
        "endpoint": endpoint,
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "payload_replay_exact": True,
        "request_capture_status": "captured",
        "payload_sha256": f"payload-{endpoint}",
        "prompt_version": (
            "holding_score_v2"
            if holding
            else ("decision_quality_v2_7" if entry else "entry_price_v1")
        ),
        "prompt_sha256": (
            "prompt-1" if holding else ("prompt-entry" if entry else "prompt-2")
        ),
        "provider_actual": "openai" if holding or entry else "bedrock",
        "model": "gpt-test" if holding or entry else "qwen3_32b",
        "request_temperature": 0,
        "request_reasoning_effort": "medium" if holding or entry else None,
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "canonical_context_capture_status": "exact_completed_bars_captured",
        "action": "HOLD" if holding else ("DROP" if entry else "USE_DEFENSIVE"),
        "score": 60 if holding else None,
    }


def _payload(endpoint="holding_score"):
    holding = endpoint == "holding_score"
    context = (
        {
            "position_context": {"buy_qty": 1, "buy_price": 100},
            "holding_decision_context": {
                "schema": "holding_decision_context_v1",
                "venue": "KRX",
                "session": "krx_regular",
                "execution_pnl": {
                    "remaining_qty": 1,
                    "average_entry_price": 100,
                    "executable_sell_price": 100,
                },
                "source_quality": {
                    "status": "fresh_consistent",
                    "candle_status": "fresh_consistent",
                    "bbo_fresh": True,
                    "position_valid": True,
                    "order_consistent": True,
                    "position_reconciled": False,
                },
                "candle": {
                    "input_bundle_version": "scalping_multi_timeframe_context_v1",
                    "completed_bar_count": 1,
                    "bars": [{"minute": "11:59", "close": 100, "is_forming": False}],
                },
            },
        }
        if holding
        else {
            "entry_candle_context": {
                "schema": "entry_candle_context_v1",
                "venue": "KRX",
                "session": "krx_regular",
                "input_bundle_version": "scalping_multi_timeframe_context_v1",
                "bars": [{"t": "11:59", "c": 100, "forming": False}],
            }
        }
    )
    return {
        "endpoint": endpoint,
        "payload_sha256": f"payload-{endpoint}",
        "replay_exact": True,
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "sanitized_user_input": context,
    }


def test_prepare_stage_requests_freezes_exact_holding_without_outcome():
    requests, summary = replay.prepare_stage_requests(
        stage="holding",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[_trace()],
        payloads=[_payload()],
    )

    assert len(requests) == 1
    assert requests[0]["runtime_effect"] is False
    assert requests[0]["control"]["captured_action"] == "HOLD"
    assert requests[0]["candidate"]["prompt_version"] == "decision_quality_holding_v2_3"
    assert (
        "position_reconciled=false alone is uncertainty"
        in requests[0]["candidate"]["system_prompt"]
    )
    assert requests[0]["candidate_input"]["holding_exact_contract_facts_v1"][
        "fresh_consistent_core"
    ]
    assert summary["strict_eligible_count"] == 1


def test_prepare_holding_flow_preserves_endpoint_and_extracts_marked_context():
    holding_context = {
        "schema": "holding_decision_context_v1",
        "venue": "KRX",
        "session": "krx_regular",
        "execution_pnl": {
            "remaining_qty": 1,
            "average_entry_price": 100,
            "executable_sell_price": 99,
        },
        "position_lifecycle": {"memory_qty": 1},
        "source_quality": {
            "status": "fresh_consistent",
            "candle_status": "fresh_consistent",
            "bbo_fresh": True,
            "position_valid": True,
            "order_consistent": True,
            "position_reconciled": True,
        },
        "candle": {
            "input_bundle_version": "scalping_multi_timeframe_context_v1",
            "completed_bar_count": 1,
            "bars": [{"is_forming": False, "close": 99}],
        },
        "order_reconciliation": {
            "open_sell_qty": 0,
            "cancel_pending": False,
            "exit_token_active": False,
            "order_or_quantity_conflict": False,
        },
    }
    exact_text = (
        "[DECISION_TYPE]\n- candidate_exit_rule: scalp_soft_stop_pct\n\n"
        "[POSITION_CONTEXT]\n- allowed_worsen_pct: 0.80\n\n"
        "[ENTRY_TIME_CONTEXT]\n{}\n\n[HOLDING_DECISION_CONTEXT]\n"
        + json.dumps(holding_context)
    )
    trace = {
        **_trace("holding_score"),
        "decision_trace_id": "trace-holding-flow",
        "decision_stage": "holding",
        "endpoint": "holding_flow",
        "payload_sha256": "payload-holding-flow",
        "prompt_version": "flow_v1",
        "prompt_sha256": "prompt-flow",
        "provider_actual": "openai",
        "model": "gpt-5.4-mini",
    }
    payload = {
        "endpoint": "holding_flow",
        "payload_sha256": "payload-holding-flow",
        "replay_exact": True,
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "sanitized_user_input": exact_text,
    }

    requests, summary = replay.prepare_stage_requests(
        stage="holding_flow",
        dates=["2026-08-04"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[trace],
        payloads=[payload],
    )

    assert summary["strict_eligible_count"] == 1
    assert requests[0]["stage"] == "holding"
    assert requests[0]["coverage_stage"] == "holding_flow"
    assert requests[0]["endpoint"] == "holding_flow"
    assert requests[0]["candidate"]["prompt_version"] == (
        "decision_quality_holding_flow_v2_2_bounded_defer"
    )
    assert requests[0]["candidate"]["semantic_validator_version"] == (
        "holding_flow_bounded_defer_semantic_v1"
    )
    assert requests[0]["candidate_input"]["holding_exact_contract_facts_v1"][
        "fresh_consistent_core"
    ]
    assert requests[0]["candidate_input"]["holding_exact_contract_facts_v1"][
        "bounded_defer_eligible"
    ]


def test_holding_flow_bounded_defer_semantic_gate_preserves_hard_exit():
    context = {
        "holding_decision_context": {
            "execution_pnl": {
                "remaining_qty": 1,
                "average_entry_price": 100,
                "executable_sell_price": 97,
            },
            "source_quality": {
                "status": "fresh_consistent",
                "candle_status": "fresh_consistent",
                "bbo_fresh": True,
                "position_valid": True,
                "order_consistent": True,
            },
            "candle": {
                "completed_bar_count": 1,
                "bars": [{"is_forming": False, "close": 97}],
            },
            "order_reconciliation": {"open_sell_qty": 0},
        }
    }
    exact_text = (
        "[DECISION_TYPE]\n- candidate_exit_rule: scalp_hard_stop_pct\n\n"
        "[POSITION_CONTEXT]\n- allowed_worsen_pct: 0.80\n\n"
        "[HOLDING_DECISION_CONTEXT]\n" + json.dumps(context["holding_decision_context"])
    )
    request = {
        "stage": "holding",
        "exact_payload": exact_text,
        "candidate": {
            "semantic_validator_version": "holding_flow_bounded_defer_semantic_v1"
        },
    }
    response = {
        "edge_state": "EDGE",
        "action": "HOLD",
        "expected_upside_pct": 0.8,
        "expected_downside_pct": -0.6,
        "confidence": 55,
        "reason_codes": ["edge_positive", "recovery_trigger_required"],
        "evidence": {
            "trend": "mixed",
            "liquidity": "mixed",
            "tape": "mixed",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "high",
            "trigger": "recovery_required",
        },
    }

    errors = replay.quality.validate_replay_candidate_response(request, response)

    assert "holding_flow_hard_guard_requires_exit" in errors
    assert "holding_flow_defer_not_eligible" in errors

    soft_request = {
        **request,
        "exact_payload": exact_text.replace(
            "scalp_hard_stop_pct", "scalp_soft_stop_pct"
        ),
    }
    soft_errors = replay.quality.validate_replay_candidate_response(
        soft_request, response
    )
    assert not [error for error in soft_errors if error.startswith("holding_flow_")]


def test_holding_flow_checkpoint_loader_does_not_infer_missing_or_position_path(
    tmp_path,
):
    source = tmp_path / "pipeline.jsonl"
    snapshot_39 = {
        "sources": {
            "bbo": {
                "value": {"best_bid": 99, "best_ask": 100},
                "source": "ws_0D",
                "observed_at": "2026-08-04T10:00:39+09:00",
                "quality": "fresh",
                "market_route": "krx_only",
            }
        }
    }
    events = [
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "scale_in_executed",
            "stock_code": "005930",
            "record_id": 7,
            "emitted_at": "2026-08-04T10:00:05+09:00",
            "fields": {
                "actual_order_submitted": "True",
                "order_no": "1",
                "fill_qty": "1",
                "fill_price": "100",
                "new_buy_qty": "2",
                "new_avg_price": "100.5",
            },
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stage": "ai_holding_review",
            "stock_code": "005930",
            "record_id": 7,
            "emitted_at": "2026-08-04T10:00:40+09:00",
            "fields": {
                "holding_context_venue": "KRX",
                "holding_context_session": "krx_regular",
                "holding_context_ai_market_snapshot": repr(snapshot_39),
            },
        },
    ]
    source.write_text("".join(json.dumps(row) + "\n" for row in events))
    request = {
        "decision_trace_id": "holding-flow-1",
        "decision_ts": "2026-08-04T10:00:00+09:00",
        "record_id": "7",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "control": {"captured_selected_price": 100},
    }

    evidence = replay.load_holding_flow_checkpoint_evidence(
        pipeline_path=source,
        requests=[request],
    )
    ledger = evidence["holding-flow-1"]
    assert ledger["checkpoint_available_count"] == 1
    assert [row["status"] for row in ledger["checkpoints"]] == [
        "available",
        "source_unavailable",
        "source_unavailable",
    ]
    assert all(not row["bar_price_inference_used"] for row in ledger["checkpoints"])
    assert ledger["position_mutation_observed"] is True

    report = replay.build_holding_flow_bounded_defer_v2_2_report(
        requests=[request],
        results=[
            {
                "decision_trace_id": "holding-flow-1",
                "status": "pass",
                "control_response": {"action": "EXIT"},
                "candidate_response": {"action": "HOLD"},
            }
        ],
        checkpoint_evidence=evidence,
    )
    row = report["rows"][0]
    assert report["status"] == "checkpoint_source_partial_keep_collecting"
    assert row["pure_defer_counterfactual_eligible"] is False
    assert row["cost_adjusted_defer_ev_pct"] is None
    assert row["source_runtime_position_mutation_observed"] is True


def test_prepare_stage_requests_preserves_source_quality_exclusion():
    trace = {**_trace("entry_price"), "input_blockers": ["candle_source_quality"]}
    requests, summary = replay.prepare_stage_requests(
        stage="entry_price",
        dates=["2026-07-29"],
        max_rows=16,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[trace],
        payloads=[_payload("entry_price")],
    )

    assert requests == []
    assert summary["source_quality_blockers_present"] == 1


def test_prepare_stage_requests_restricts_to_mature_outcome_trace_ids():
    included = _trace("entry_price")
    excluded = {
        **included,
        "decision_trace_id": "trace-entry-price-without-mature-outcome",
        "payload_sha256": "payload-entry-price-without-mature-outcome",
    }
    excluded_payload = {
        **_payload("entry_price"),
        "payload_sha256": "payload-entry-price-without-mature-outcome",
    }

    requests, summary = replay.prepare_stage_requests(
        stage="entry_price",
        dates=["2026-07-29"],
        max_rows=16,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[included, excluded],
        payloads=[_payload("entry_price"), excluded_payload],
        eligible_trace_ids={"trace-entry_price"},
    )

    assert [row["decision_trace_id"] for row in requests] == ["trace-entry_price"]
    assert summary["mature_outcome_not_eligible"] == 1


def test_prepare_entry_price_uses_conditional_selection_contract():
    payload = _payload("entry_price")
    payload["sanitized_user_input"].update(
        {
            "price_context": {
                "best_bid": 99,
                "best_ask": 101,
                "defensive_order_price": 99,
                "reference_target_price": 100,
                "resolved_order_price": 100,
            },
            "entry_context_features": {
                "quote_fresh_for_entry": True,
                "quote_stale": False,
                "would_fill_now": False,
                "spread_bp": 200,
            },
            "ai_market_snapshot_v1": {
                "ai_input_preflight_v1": {
                    "allowed": True,
                    "blockers": [],
                    "venue_consistent": True,
                }
            },
        }
    )
    requests, _ = replay.prepare_stage_requests(
        stage="entry_price",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[_trace("entry_price")],
        payloads=[payload],
    )

    request = requests[0]
    facts = request["candidate_input"]["entry_price_exact_contract_facts_v1"]
    assert request["candidate"]["prompt_version"] == (
        "decision_quality_entry_price_v2_1_conditional_selection"
    )
    assert request["candidate"]["semantic_validator_version"] == (
        "entry_price_exact_semantic_gate_v1"
    )
    assert request["candidate"]["response_schema"]["selected_price"] == (
        "positive_integer_or_null"
    )
    assert facts["skip_permitted"] is False
    assert facts["would_fill_now"] is False
    assert "would_fill_now=false" in request["candidate"]["system_prompt"]


def test_entry_price_semantic_gate_rejects_unjustified_skip_and_basis_mismatch():
    request = {
        "stage": "entry_price",
        "exact_payload": {
            "price_context": {
                "best_bid": 99,
                "best_ask": 101,
                "defensive_order_price": 99,
                "reference_target_price": 100,
                "resolved_order_price": 100,
            },
            "entry_context_features": {
                "quote_fresh_for_entry": True,
                "quote_stale": False,
            },
            "ai_market_snapshot_v1": {
                "ai_input_preflight_v1": {
                    "allowed": True,
                    "blockers": [],
                    "venue_consistent": True,
                }
            },
        },
        "candidate": {
            "semantic_validator_version": "entry_price_exact_semantic_gate_v1"
        },
    }
    common = {
        "edge_state": "NO_EDGE",
        "expected_upside_pct": 0.3,
        "expected_downside_pct": -0.4,
        "confidence": 50,
        "reason_codes": ["edge_absent"],
        "evidence": {
            "trend": "mixed",
            "liquidity": "mixed",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "not_applicable",
            "positive_edge": "weak",
            "adverse_risk": "moderate",
            "trigger": "not_applicable",
        },
    }
    skip_errors = replay.quality.validate_replay_candidate_response(
        request,
        {**common, "action": "SKIP", "selected_price": None, "price_basis": "NONE"},
    )
    assert "entry_price_skip_without_explicit_blocker" in skip_errors
    mismatch_errors = replay.quality.validate_replay_candidate_response(
        request,
        {
            **common,
            "action": "USE_REFERENCE",
            "selected_price": 99,
            "price_basis": "DEFENSIVE",
        },
    )
    assert "entry_price_action_basis_mismatch" in mismatch_errors


def test_entry_price_contract_facts_fail_closed_when_preflight_is_missing():
    facts = replay.quality._entry_price_contract_facts(
        {
            "price_context": {
                "best_bid": 99,
                "best_ask": 101,
                "defensive_order_price": 99,
            },
            "entry_context_features": {
                "quote_fresh_for_entry": True,
                "quote_stale": False,
            },
        }
    )

    assert facts["skip_permitted"] is True
    assert "preflight_missing" in facts["source_blockers"]


def test_prepare_entry_stage_uses_v2_8_and_unwraps_live_v2_7_payload():
    payload = _payload("analyze_target")
    raw_exact = payload["sanitized_user_input"]
    payload["sanitized_user_input"] = {
        "exact_payload": raw_exact,
        "exact_payload_analysis_v1": {"schema": "captured-live-analysis"},
    }
    requests, summary = replay.prepare_stage_requests(
        stage="entry",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[_trace("analyze_target")],
        payloads=[payload],
    )

    assert summary["strict_eligible_count"] == 1
    assert len(requests) == 1
    assert requests[0]["exact_payload"] == raw_exact
    assert requests[0]["candidate_input"]["exact_payload"] == raw_exact
    assert requests[0]["candidate"]["prompt_version"] == "decision_quality_v2_8"
    assert requests[0]["runtime_effect"] is False


def test_prepare_entry_stage_separates_approved_cache_redaction_supplemental():
    payload = _payload("analyze_target")
    raw_exact = payload["sanitized_user_input"]
    raw_exact["runtime_context"] = {"lifecycle_ai": {"cache_token": "[REDACTED]"}}
    payload.update(
        {
            "redacted": True,
            "replay_exact": False,
            "sanitized_user_input": {
                "exact_payload": raw_exact,
                "exact_payload_analysis_v1": {"schema": "exact_payload_analysis_v1"},
            },
        }
    )
    trace = {**_trace("analyze_target"), "payload_replay_exact": False}
    control = _control()
    control["supplemental_semantic_controls"] = [control["controls"][0]]

    requests, summary = replay.prepare_stage_requests(
        stage="entry",
        dates=["2026-07-30"],
        max_rows=1,
        control_manifest=control,
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[trace],
        payloads=[payload],
        allow_approved_cache_redaction_supplemental=True,
    )

    assert summary["supplemental_semantic_source_count"] == 1
    assert summary["supplemental_semantic_eligible_count"] == 1
    assert summary["exact_source_excluded_count"] == 0
    assert requests[0]["source_exactness"] == (
        "non_exact_approved_cache_token_redaction"
    )
    assert requests[0]["primary_exact_cohort_eligible"] is False
    assert requests[0]["supplemental_semantic_replay"] is True
    assert requests[0]["decision_authority"] == (
        "offline_supplemental_replay_no_runtime_change"
    )
    assert "approved_cache_redaction" in requests[0]["source_quality_gate"]
    report = replay.build_report(
        target_date="2026-07-30",
        stage="entry",
        dates=["2026-07-30"],
        requested_max_rows=1,
        source_summary=summary,
        requests=requests,
        results=[],
    )
    assert report["primary_quality_authority"] is False
    assert report["decision_authority"] == (
        "offline_supplemental_replay_no_runtime_change"
    )
    assert "approved_cache_redaction" in report["source_quality_gate"]


def test_reusable_pass_results_requires_same_candidate_and_payload():
    requests, _ = replay.prepare_stage_requests(
        stage="entry",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[_trace("analyze_target")],
        payloads=[_payload("analyze_target")],
    )
    response = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.3,
        "expected_downside_pct": -0.4,
        "confidence": 60,
        "reason_codes": ["no_positive_edge"],
        "evidence": {
            "trend": "mixed",
            "liquidity": "mixed",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "moderate",
            "trigger": "not_applicable",
        },
    }
    results = replay.quality.run_paired_replay(
        requests,
        control_runner=lambda _: {"action": "DROP"},
        candidate_runner=lambda _: response,
    )

    reusable = replay.reusable_pass_results(
        existing_report={"results": results},
        requests=requests,
    )
    assert len(reusable) == 1

    changed_requests = [
        {
            **requests[0],
            "candidate": {
                **requests[0]["candidate"],
                "system_prompt_sha256": "changed",
            },
        }
    ]
    assert (
        replay.reusable_pass_results(
            existing_report={"results": results},
            requests=changed_requests,
        )
        == []
    )


def test_bedrock_candidate_uses_qwen_only_and_no_failback():
    captured = {}

    class FakeProvider:
        def converse(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                payload={
                    "edge_state": "EDGE",
                    "action": "USE_DEFENSIVE",
                    "expected_upside_pct": 1.0,
                    "expected_downside_pct": -0.5,
                    "confidence": 70,
                    "reason_codes": ["edge_positive"],
                    "evidence": {
                        "trend": "supportive",
                        "liquidity": "mixed",
                        "tape": "mixed",
                        "risk": "medium",
                        "uncertainty": "medium",
                        "setup": "continuation",
                        "positive_edge": "moderate",
                        "adverse_risk": "moderate",
                        "trigger": "confirmed",
                    },
                    "selected_price": 100,
                    "price_basis": "BEST_BID",
                },
                model_id="qwen.qwen3-32b-v1:0",
                transport_meta=lambda: {
                    "provider": "bedrock",
                    "provider_response_id": "response-1",
                },
            )

    request = {
        "exact_payload": {"price": 100},
        "control": {"provider": "bedrock", "model": "qwen3_32b"},
        "candidate": {
            "provider": "bedrock",
            "model": "qwen3_32b",
            "system_prompt": "Return JSON",
        },
        **replay.CONTRACT,
    }
    result = replay.execute_bedrock_candidate(request, provider=FakeProvider())

    assert result["candidate_response"]["selected_price"] == 100
    assert captured["profile"].family == "qwen3_32b"
    assert result["provider_provenance"]["failback_chain"] == []


def test_report_marks_action_collapse_before_outcome_comparison():
    requests = [
        {
            "paired_replay_id": f"pair-{index}",
            "stock_code": f"{index:06d}",
            "control": {},
            "candidate_input": {"exact_payload": {"secret_marker": "do-not-store"}},
        }
        for index in range(30)
    ]
    results = [
        {
            "paired_replay_id": f"pair-{index}",
            "status": "pass",
            "control_response": {"action": "EXIT"},
            "candidate_response": {"action": "HOLD"},
        }
        for index in range(30)
    ]

    report = replay.build_report(
        target_date="2026-07-30",
        stage="holding",
        dates=["2026-07-29"],
        requested_max_rows=30,
        source_summary={},
        requests=requests,
        results=results,
    )

    assert report["status"] == "coverage_replay_complete_candidate_action_collapsed"
    assert report["candidate_action_not_collapsed"] is False
    assert report["coverage_sample_floor"]["pass"] is True
    assert report["candidate_action_collapse_evaluable"] is True
    assert "candidate_input" not in report["requests"][0]
    assert "do-not-store" not in str(report)


def test_report_keeps_collecting_before_action_collapse_is_evaluable():
    requests = [
        {
            "paired_replay_id": "pair-thin",
            "stock_code": "108860",
            "control": {},
        }
    ]
    results = [
        {
            "paired_replay_id": "pair-thin",
            "status": "pass",
            "control_response": {"action": "EXIT"},
            "candidate_response": {"action": "EXIT"},
        }
    ]

    report = replay.build_report(
        target_date="2026-08-04",
        stage="holding_flow",
        dates=["2026-08-04"],
        requested_max_rows=10,
        source_summary={},
        requests=requests,
        results=results,
    )

    assert report["status"] == ("coverage_replay_complete_sample_floor_keep_collecting")
    assert report["candidate_action_collapse_evaluable"] is False
    assert report["candidate_action_not_collapsed"] is None


def test_holding_flow_outcome_attribution_keeps_observed_path_noncausal():
    request = {
        "decision_trace_id": "trace-flow",
        "stock_code": "108860",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
    }
    result = {
        "decision_trace_id": "trace-flow",
        "status": "pass",
        "same_payload_confirmed": True,
        "control_response": {"action": "EXIT"},
        "candidate_response": {"action": "HOLD"},
    }
    label = {
        "decision_trace_id": "trace-flow",
        "decision_stage": "holding",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "30m": {
                "end_return_pct": 0.4,
                "mfe_pct": 1.2,
                "mae_pct": -0.5,
                "first_hit": "target",
            }
        },
        "stage_outcome": {
            "secured_upside_pct": 1.2,
            "enlarged_loss_pct": -0.5,
        },
    }

    report = replay.build_holding_flow_outcome_attribution(
        requests=[request], results=[result], labels=[label]
    )

    assert report["status"] == "sample_floor_keep_collecting"
    assert report["candidate_action_counts"] == {"HOLD": 1}
    assert report["rows"][0]["observed_peak_giveback_pct"] == 0.8
    assert report["rows"][0]["outcome_interpretation"] == (
        "same_observed_path_not_action_counterfactual"
    )
    assert "claim_observed_path_as_action_counterfactual" in report["forbidden_uses"]


def test_entry_price_selection_outcome_uses_selected_limit_and_not_fill_claim():
    request = {
        "decision_trace_id": "trace-price",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "exact_payload": {
            "price_context": {
                "best_bid": 99,
                "best_ask": 101,
                "defensive_order_price": 99,
                "reference_target_price": 100,
                "resolved_order_price": 100,
            }
        },
        "control": {
            "captured_action": "USE_DEFENSIVE",
            "captured_selected_price": 99,
        },
    }
    result = {
        "decision_trace_id": "trace-price",
        "status": "pass",
        "same_payload_confirmed": True,
        "candidate_response": {
            "action": "USE_REFERENCE",
            "selected_price": 100,
            "price_basis": "REFERENCE",
        },
    }
    label = {
        "decision_trace_id": "trace-price",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "reference_price": 99,
        "horizon_metrics": {
            "10m": {
                "mfe_pct": 2.0,
                "mae_pct": 0.5,
                "end_return_pct": 1.0,
                "profit_opportunity_observed": True,
            }
        },
    }

    report = replay.build_entry_price_selection_outcome_comparison(
        requests=[request], results=[result], labels=[label]
    )

    assert report["summary"]["comparable_count"] == 1
    assert report["rows"][0]["control"]["limit_touch_observed"] is False
    assert report["rows"][0]["candidate"]["limit_touch_observed"] is True
    assert "not_fill_proof" in report["limit_touch_semantics"]
    assert report["actual_order_submitted"] is False
    assert report["quality_gate_pass"] is False
    assert report["summary"]["candidate_more_aggressive_price_count"] == 1
