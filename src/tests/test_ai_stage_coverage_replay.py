from types import SimpleNamespace

from src.engine.scalping import ai_stage_coverage_replay as replay


def _control():
    return {
        "controls": [
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
    return {
        "decision_trace_id": f"trace-{endpoint}",
        "decision_ts": "2026-07-29T12:00:00+09:00",
        "decision_stage": "holding" if holding else "entry_price",
        "endpoint": endpoint,
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "payload_replay_exact": True,
        "request_capture_status": "captured",
        "payload_sha256": f"payload-{endpoint}",
        "prompt_version": "holding_score_v2" if holding else "entry_price_v1",
        "prompt_sha256": "prompt-1" if holding else "prompt-2",
        "provider_actual": "openai" if holding else "bedrock",
        "model": "gpt-test" if holding else "qwen3_32b",
        "request_temperature": 0,
        "request_reasoning_effort": "medium" if holding else None,
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "canonical_context_capture_status": "exact_completed_bars_captured",
        "action": "HOLD" if holding else "USE_DEFENSIVE",
        "score": 60 if holding else None,
    }


def _payload(endpoint="holding_score"):
    holding = endpoint == "holding_score"
    context = (
        {
            "position_context": {"buy_qty": 1, "buy_price": 100},
            "holding_decision_context": {
                "schema": "holding_decision_context_v1",
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
                "input_bundle_version": "scalping_multi_timeframe_context_v1",
                "bars": [{"t": "11:59", "c": 100, "forming": False}],
            }
        }
    )
    return {
        "endpoint": endpoint,
        "payload_sha256": f"payload-{endpoint}",
        "replay_exact": True,
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
            "stock_code": f"{index % 4:06d}",
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
    assert report["coverage_sample_floor"]["pass"] is False
    assert "candidate_input" not in report["requests"][0]
    assert "do-not-store" not in str(report)
