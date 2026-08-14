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
    schema_name = {
        "analyze_target": "decision_quality_v2_7_entry",
        "entry_price": "entry_price_explicit_fill_value_v1",
        "holding_score": "holding_score_v2",
        "holding_flow": "holding_exit_flow_v1",
    }[endpoint]
    response_schema = replay.build_openai_response_text_format(schema_name)["schema"]
    semantic_validator_version = {
        "analyze_target": replay.quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION,
        "entry_price": replay.quality.ENTRY_PRICE_SEMANTIC_VALIDATOR_VERSION,
        "holding_score": replay.quality.HOLDING_SEMANTIC_VALIDATOR_VERSION,
        "holding_flow": replay.quality.HOLDING_FLOW_BOUNDED_DEFER_SEMANTIC_VALIDATOR_VERSION,
    }[endpoint]
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
        "result_source": "live",
        "semantic_validator_version": semantic_validator_version,
        "semantic_validator_applied": True,
        "semantic_validation_status": "pass",
        "response_schema_sha256": replay.quality._sha256(response_schema),
        "response_schema_application": (
            "provider_enforced_openai"
            if holding or entry
            else "local_expected_only_not_sent_to_bedrock"
        ),
        "openai_response_schema_mode": "strict_registry",
        "openai_response_schema_registry_used": True,
        "transport": "test_transport",
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
    schema_name = {
        "analyze_target": "decision_quality_v2_7_entry",
        "entry_price": "entry_price_explicit_fill_value_v1",
        "holding_score": "holding_score_v2",
        "holding_flow": "holding_exit_flow_v1",
    }[endpoint]
    return {
        "endpoint": endpoint,
        "payload_sha256": f"payload-{endpoint}",
        "replay_exact": True,
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "schema_name": schema_name,
        "require_json": True,
        "max_output_tokens": 512,
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


def test_holding_control_and_candidate_use_distinct_response_contracts():
    requests, _ = replay.prepare_stage_requests(
        stage="holding",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[_trace("holding_score")],
        payloads=[_payload("holding_score")],
    )
    candidate_request = requests[0]
    candidate = candidate_request["candidate"]
    assert candidate["schema_name"] == "decision_quality_holding_v2_3_candidate"
    assert "edge_state" in candidate["response_schema"]["required"]
    candidate_response = {
        "edge_state": "EDGE",
        "action": "HOLD",
        "expected_upside_pct": 1.0,
        "expected_downside_pct": -0.5,
        "confidence": 70,
        "reason_codes": ["edge_positive"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "mixed",
            "risk": "low",
            "uncertainty": "low",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "low",
            "trigger": "confirmed",
        },
    }
    assert not replay.quality.validate_replay_candidate_response(
        candidate_request, candidate_response
    )

    control_request = json.loads(json.dumps(candidate_request))
    control_request["candidate"] = {
        **candidate,
        "schema_name": "holding_score_v2",
        "response_schema": replay.build_openai_response_text_format("holding_score_v2")[
            "schema"
        ],
        "semantic_validator_version": "holding_score_live_normalizer_v1",
    }
    live_response = {
        "action": "HOLD",
        "score": 60,
        "confidence": 70,
        "position_state": "open",
        "score_basis": "continuation intact",
        "risk_factors": [],
        "support_factors": ["completed trend"],
        "data_quality": "fresh",
        "reason": "hold",
    }
    assert not replay.quality.validate_replay_candidate_response(
        control_request, live_response
    )
    out_of_range = {**live_response, "score": 999, "confidence": -1}
    assert set(
        replay.quality.validate_replay_candidate_response(control_request, out_of_range)
    ) >= {
        "holding_score_score_out_of_range",
        "holding_score_confidence_out_of_range",
    }


def test_holding_flow_live_control_schema_is_not_used_for_generic_candidate():
    candidate_schema = replay.quality._prompt_v2_openai_schema("holding")
    assert "edge_state" in candidate_schema["required"]
    assert "flow_state" not in candidate_schema["properties"]
    control_schema = replay.build_openai_response_text_format("holding_exit_flow_v1")[
        "schema"
    ]
    control_request = {
        "stage": "holding",
        "candidate": {
            "semantic_validator_version": "holding_flow_live_schema_semantic_v1",
            "response_schema": control_schema,
        },
    }
    assert not replay.quality.validate_replay_candidate_response(
        control_request,
        {
            "action": "EXIT",
            "score": 30,
            "flow_state": "adverse",
            "thesis": "sell pressure",
            "evidence": ["bid depletion"],
            "reason": "exit",
            "next_review_sec": 0,
        },
    )


def test_legacy_entry_price_control_uses_captured_live_schema_validator():
    schema = replay.build_openai_response_text_format("entry_price_v1")["schema"]
    request = {
        "stage": "entry_price",
        "micro_reversion_replay_arm": "replay_control_exact_no_micro",
        "candidate": {
            "semantic_validator_version": "live_entry_price_v1_semantic_contract_v1",
            "response_schema": schema,
        },
    }
    response = {
        "action": "USE_DEFENSIVE",
        "order_price": 100,
        "confidence": 70,
        "reason": "passive price",
        "max_wait_sec": 5,
    }
    assert not replay.quality.validate_replay_candidate_response(request, response)
    invalid = {**response, "order_price": "100"}
    assert "response_order_price_type_invalid" in (
        replay.quality.validate_replay_candidate_response(request, invalid)
    )
    out_of_range = {
        **response,
        "order_price": -1,
        "confidence": 101,
        "max_wait_sec": 1_201,
    }
    assert set(
        replay.quality.validate_replay_candidate_response(request, out_of_range)
    ) >= {
        "entry_price_v1_order_price_negative",
        "entry_price_v1_confidence_out_of_range",
        "entry_price_v1_max_wait_sec_out_of_range",
    }
    assert not replay.quality.validate_replay_candidate_response(
        request, {**response, "max_wait_sec": 1_200}
    )
    assert "entry_price_v1_max_wait_sec_out_of_range" in (
        replay.quality.validate_replay_candidate_response(
            request, {**response, "max_wait_sec": 4}
        )
    )


def test_bedrock_offline_executor_emits_canonical_provider_provenance(monkeypatch):
    class Result:
        payload = {"action": "SKIP"}
        model_id = "test-qwen-model-id"

        @staticmethod
        def transport_meta():
            return {}

    class Provider:
        @staticmethod
        def converse(**_kwargs):
            return Result()

    monkeypatch.setattr(replay, "qwen3_32b_profile_from_env", lambda: object())
    request = {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "exact_payload": {},
        "candidate_input": {},
        "control": {"provider": "bedrock", "model": "qwen3_32b"},
        "candidate": {
            "provider": "bedrock",
            "model": "qwen3_32b",
            "transport": "bedrock_converse",
            "system_prompt": "offline test",
        },
    }

    result = replay.execute_bedrock_candidate(request, provider=Provider())

    provenance = result["provider_provenance"]
    assert provenance["provider_call_attempted"] is True
    assert provenance["provider_call_succeeded"] is True
    assert provenance["provider_none"] is False
    assert provenance["source_transport_contract"] == "bedrock_converse"
    assert provenance["canonical_response_sha256"] == (
        replay.quality._sha256(result["candidate_response"])
    )
    assert provenance["response_id_unavailable_reason"] == (
        "bedrock_transport_response_id_not_exposed"
    )


def test_budgeted_bedrock_executor_disables_two_key_retry(monkeypatch, tmp_path):
    provider_class = replay.BedrockNovaProvider
    profile = replay.qwen3_32b_profile_from_env()
    calls = []
    reservations = []
    summary_paths = []

    class Client:
        def __init__(self, key_index):
            self.key_index = key_index

        def converse(self, **_kwargs):
            calls.append(self.key_index)
            raise RuntimeError("429 throttling")

    def single_attempt_provider(*, key_rotation_enabled):
        assert key_rotation_enabled is False
        return provider_class(
            api_keys=["key-1", "key-2"],
            key_rotation_enabled=key_rotation_enabled,
            client_factory=lambda key_index, **_kwargs: Client(key_index),
        )

    class OneAttemptBudget:
        @staticmethod
        def reserve_attempt(identity, *, token_ceiling):
            if reservations:
                raise AssertionError("one-attempt cap exceeded before network call")
            reservations.append((identity, token_ceiling))
            return SimpleNamespace(
                reservation_id="reservation-1",
                attempt_identity_sha256=identity.content_sha256,
                reserved_cost_usd="0.01",
            )

        @staticmethod
        def settle_attempt(*_args, **_kwargs):
            raise AssertionError("failed provider attempt must retain its reservation")

        @staticmethod
        def write_summary(path):
            summary_paths.append(path)

    monkeypatch.setattr(replay, "BedrockNovaProvider", single_attempt_provider)
    monkeypatch.setattr(replay, "qwen3_32b_profile_from_env", lambda: profile)
    request = {
        "paired_replay_parent_id": "parent-1",
        "paired_replay_id": "request-arm-c",
        "micro_reversion_replay_arm": "replay_candidate_exact_plus_micro",
        "offline_provider_attempt_number": 1,
        "exact_payload": {"price": 100},
        "control": {"provider": "bedrock", "model": "qwen3_32b"},
        "candidate": {
            "provider": "bedrock",
            "model": "qwen3_32b",
            "system_prompt": "Return JSON",
            "max_output_tokens": profile.max_output_tokens,
        },
        **replay.CONTRACT,
    }
    runner = replay.quality.build_micro_reversion_budgeted_candidate_runner(
        target_date="2026-08-14",
        base_runner=replay.execute_bedrock_candidate_single_network_attempt,
        budget_ledger=OneAttemptBudget(),
        budget_summary_path=tmp_path / "budget-summary.json",
    )

    try:
        runner(request)
    except RuntimeError as exc:
        assert "429 throttling" in str(exc)
    else:
        raise AssertionError("retryable first-key failure must fail closed")

    assert len(reservations) == 1
    assert calls == [0]
    assert summary_paths == [tmp_path / "budget-summary.json"]


def test_budgeted_bedrock_executor_rejects_output_limit_above_reservation(monkeypatch):
    profile = replay.qwen3_32b_profile_from_env()
    oversized_profile = type(profile)(
        **{
            **profile.__dict__,
            "max_output_tokens": profile.max_output_tokens + 1,
        }
    )
    provider_created = False

    def provider_factory(**_kwargs):
        nonlocal provider_created
        provider_created = True
        raise AssertionError("provider must not be created before output-limit gate")

    monkeypatch.setattr(
        replay, "qwen3_32b_profile_from_env", lambda: oversized_profile
    )
    monkeypatch.setattr(replay, "BedrockNovaProvider", provider_factory)
    request = {
        "exact_payload": {"price": 100},
        "control": {"provider": "bedrock", "model": "qwen3_32b"},
        "candidate": {
            "provider": "bedrock",
            "model": "qwen3_32b",
            "system_prompt": "Return JSON",
            "max_output_tokens": profile.max_output_tokens,
        },
        **replay.CONTRACT,
    }

    try:
        replay.execute_bedrock_candidate_single_network_attempt(request)
    except ValueError as exc:
        assert str(exc) == "bedrock_budgeted_profile_exceeds_reserved_output_tokens"
    else:
        raise AssertionError("oversized provider output limit must fail closed")

    assert provider_created is False


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

    structured_payload = {
        **payload,
        "sanitized_user_input": {
            "holding_decision_context": holding_context,
        },
    }
    structured_requests, structured_summary = replay.prepare_stage_requests(
        stage="holding_flow",
        dates=["2026-08-04"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[trace],
        payloads=[structured_payload],
    )
    assert structured_summary["strict_eligible_count"] == 1
    assert structured_requests[0]["candidate_input"]["exact_payload"] == {
        "holding_decision_context": holding_context
    }


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
    trace = _trace("entry_price")
    trace["reference_price"] = 99
    requests, _ = replay.prepare_stage_requests(
        stage="entry_price",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[trace],
        payloads=[payload],
    )

    request = requests[0]
    facts = request["candidate_input"]["entry_price_exact_contract_facts_v1"]
    assert request["candidate"]["prompt_version"] == (
        "decision_quality_entry_price_v2_5_explicit_fill_value"
    )
    assert request["candidate"]["semantic_validator_version"] == (
        "entry_price_explicit_fill_value_semantic_v6"
    )
    selected_price_schema = request["candidate"]["response_schema"]["properties"][
        "selected_price"
    ]
    assert set(selected_price_schema["type"]) == {"integer", "null"}
    fill_edge_schema = request["candidate"]["response_schema"]["properties"][
        "fill_adjusted_edge_pct"
    ]
    assert set(fill_edge_schema["type"]) == {"number", "null"}
    assert '"control_fill_probability_pct"' in request["candidate"]["system_prompt"]
    assert '"fill_adjusted_edge_pct"' in request["candidate"]["system_prompt"]
    assert facts["skip_permitted"] is False
    assert facts["would_fill_now"] is False
    assert facts["control_selected_price"] == 99
    assert "REFERENCE" in facts["economically_distinct_bases"]
    assert facts["max_incremental_chase_cost_bp"] == 25.0
    assert facts["minimum_reward_risk_for_aggressive_basis"] == 1.0
    assert "would_fill_now=false" in request["candidate"]["system_prompt"]
    assert "incremental chase cost" in request["candidate"]["system_prompt"]


def test_prepare_stage_requests_filters_venue_before_frozen_limit():
    krx_trace = _trace("analyze_target")
    nxt_trace = {
        **_trace("analyze_target"),
        "decision_trace_id": "trace-analyze-target-nxt",
        "decision_ts": "2026-07-29T12:01:00+09:00",
        "effective_venue": "NXT",
        "session_bucket": "nxt_aftermarket",
        "payload_sha256": "payload-analyze-target-nxt",
    }
    krx_payload = _payload("analyze_target")
    nxt_payload = json.loads(json.dumps(_payload("analyze_target")))
    nxt_payload.update(
        {
            "payload_sha256": "payload-analyze-target-nxt",
            "effective_venue": "NXT",
            "session_bucket": "nxt_aftermarket",
        }
    )
    nxt_context = nxt_payload["sanitized_user_input"]["entry_candle_context"]
    nxt_context["venue"] = "NXT"
    nxt_context["session"] = "nxt_aftermarket"

    requests, summary = replay.prepare_stage_requests(
        stage="entry",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[krx_trace, nxt_trace],
        payloads=[krx_payload, nxt_payload],
        eligible_trace_ids={nxt_trace["decision_trace_id"]},
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
    )

    assert len(requests) == 1
    assert requests[0]["effective_venue"] == "NXT"
    assert requests[0]["session_bucket"] == "nxt_aftermarket"
    assert summary["cohort_venue_filter_excluded"] == 1
    assert summary.get("mature_outcome_not_eligible", 0) == 0


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
            "semantic_validator_version": (
                "entry_price_explicit_fill_value_semantic_v6"
            )
        },
        "candidate_input": {
            "entry_price_exact_contract_facts_v1": {
                "candidate_prices": {
                    "DEFENSIVE": 99,
                    "REFERENCE": 100,
                    "RESOLVED": 100,
                    "BEST_BID": 99,
                    "BEST_ASK": 101,
                },
                "skip_permitted": False,
                "control_selected_price": 99,
                "price_cost_baseline": 99,
                "price_delta_from_cost_baseline_bp": {
                    "DEFENSIVE": 0.0,
                    "REFERENCE": 101.01,
                    "RESOLVED": 101.01,
                    "BEST_BID": 0.0,
                    "BEST_ASK": 202.02,
                },
            }
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


def test_entry_price_semantic_gate_rejects_action_only_relabel_and_weak_chase():
    request = {
        "stage": "entry_price",
        "exact_payload": {
            "price_context": {
                "best_bid": 100,
                "best_ask": 102,
                "defensive_order_price": 100,
                "reference_target_price": 100,
                "resolved_order_price": 101,
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
            "semantic_validator_version": (
                "entry_price_explicit_fill_value_semantic_v6"
            )
        },
        "candidate_input": {
            "entry_price_exact_contract_facts_v1": {
                "candidate_prices": {
                    "DEFENSIVE": 100,
                    "REFERENCE": 100,
                    "RESOLVED": 101,
                    "BEST_BID": 100,
                    "BEST_ASK": 102,
                },
                "skip_permitted": False,
                "control_selected_price": 100,
                "price_cost_baseline": 100,
                "price_delta_from_cost_baseline_bp": {
                    "DEFENSIVE": 0.0,
                    "REFERENCE": 0.0,
                    "RESOLVED": 100.0,
                    "BEST_BID": 0.0,
                    "BEST_ASK": 200.0,
                },
                "max_incremental_chase_cost_bp": 25.0,
            }
        },
    }
    response = {
        "edge_state": "EDGE",
        "action": "USE_REFERENCE",
        "expected_upside_pct": 1.0,
        "expected_downside_pct": -0.5,
        "confidence": 70,
        "reason_codes": ["edge_positive"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
        "selected_price": 100,
        "price_basis": "REFERENCE",
    }
    errors = replay.quality.validate_replay_candidate_response(request, response)
    assert "entry_price_nondefensive_price_not_distinct" in errors

    weak_chase = {
        **response,
        "action": "IMPROVE_LIMIT",
        "selected_price": 101,
        "price_basis": "RESOLVED",
        "expected_upside_pct": 0.25,
        "evidence": {**response["evidence"], "trigger": "recovery_required"},
    }
    errors = replay.quality.validate_replay_candidate_response(request, weak_chase)
    assert "entry_price_aggressive_limit_without_confirmed_edge" in errors
    assert "entry_price_aggressive_limit_insufficient_edge_buffer" in errors
    assert "entry_price_aggressive_limit_exceeds_chase_cost_bound" in errors


def test_entry_price_semantic_gate_bounds_chase_cost_and_requires_real_downside():
    request = {
        "stage": "entry_price",
        "exact_payload": {
            "price_context": {
                "best_bid": 1000,
                "best_ask": 1005,
                "defensive_order_price": 1000,
                "reference_target_price": 1002,
                "resolved_order_price": 1003,
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
            "semantic_validator_version": (
                "entry_price_explicit_fill_value_semantic_v6"
            )
        },
        "candidate_input": {
            "entry_price_exact_contract_facts_v1": {
                "candidate_prices": {
                    "DEFENSIVE": 1000,
                    "REFERENCE": 1002,
                    "RESOLVED": 1003,
                    "BEST_BID": 1000,
                    "BEST_ASK": 1005,
                },
                "skip_permitted": False,
                "control_selected_price": 1000,
                "control_exposure_selected": True,
                "price_cost_baseline": 1000,
                "price_delta_from_cost_baseline_bp": {
                    "DEFENSIVE": 0.0,
                    "REFERENCE": 20.0,
                    "RESOLVED": 30.0,
                    "BEST_BID": 0.0,
                    "BEST_ASK": 50.0,
                },
                "max_incremental_chase_cost_bp": 25.0,
                "minimum_reward_risk_for_aggressive_basis": 1.0,
            }
        },
    }
    common = {
        "edge_state": "EDGE",
        "expected_upside_pct": 0.6,
        "expected_downside_pct": -0.3,
        "confidence": 75,
        "reason_codes": ["edge_positive"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    bounded = {
        **common,
        "action": "USE_REFERENCE",
        "selected_price": 1002,
        "price_basis": "REFERENCE",
        "control_fill_probability_pct": 50.0,
        "selected_fill_probability_pct": 90.0,
        "incremental_fill_probability_pct": 40.0,
        "incremental_chase_cost_pct": 0.2,
        "fill_adjusted_edge_pct": 0.04,
    }
    assert replay.quality.validate_replay_candidate_response(request, bounded) == []

    zero_downside = {**bounded, "expected_downside_pct": 0.0}
    assert "entry_price_aggressive_limit_requires_negative_downside" in (
        replay.quality.validate_replay_candidate_response(request, zero_downside)
    )

    epsilon_downside = {**bounded, "expected_downside_pct": -0.001}
    assert "entry_price_aggressive_limit_downside_below_chase_cost" in (
        replay.quality.validate_replay_candidate_response(request, epsilon_downside)
    )

    weak_reward_risk = {
        **bounded,
        "expected_upside_pct": 0.3,
        "expected_downside_pct": -0.4,
    }
    assert "entry_price_aggressive_limit_reward_risk_below_floor" in (
        replay.quality.validate_replay_candidate_response(request, weak_reward_risk)
    )

    over_bound = {
        **common,
        "action": "IMPROVE_LIMIT",
        "selected_price": 1003,
        "price_basis": "RESOLVED",
    }
    assert "entry_price_aggressive_limit_exceeds_chase_cost_bound" in (
        replay.quality.validate_replay_candidate_response(request, over_bound)
    )


def test_entry_price_fill_value_ledger_rejects_bad_arithmetic_and_fake_value():
    request = {
        "stage": "entry_price",
        "exact_payload": {
            "price_context": {
                "best_bid": 1000,
                "best_ask": 1005,
                "defensive_order_price": 1000,
                "reference_target_price": 1002,
                "resolved_order_price": 1003,
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
            "semantic_validator_version": (
                "entry_price_explicit_fill_value_semantic_v6"
            )
        },
        "candidate_input": {
            "entry_price_exact_contract_facts_v1": {
                "control_selected_price": 1000,
                "control_exposure_selected": True,
                "price_cost_baseline": 1000,
                "max_incremental_chase_cost_bp": 25.0,
                "minimum_reward_risk_for_aggressive_basis": 1.0,
            }
        },
    }
    response = {
        "edge_state": "EDGE",
        "action": "USE_REFERENCE",
        "expected_upside_pct": 0.6,
        "expected_downside_pct": -0.3,
        "confidence": 75,
        "reason_codes": ["edge_positive"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
        "selected_price": 1002,
        "price_basis": "REFERENCE",
        "control_fill_probability_pct": 50.0,
        "selected_fill_probability_pct": 90.0,
        "incremental_fill_probability_pct": 39.0,
        "incremental_chase_cost_pct": 0.1,
        "fill_adjusted_edge_pct": -0.01,
    }

    errors = replay.quality.validate_replay_candidate_response(request, response)

    assert "entry_price_incremental_fill_probability_mismatch" in errors
    assert "entry_price_incremental_chase_cost_mismatch" in errors
    assert "entry_price_fill_adjusted_edge_mismatch" in errors
    assert "entry_price_aggressive_limit_nonpositive_fill_value" in errors


def test_entry_price_fill_value_ledger_requires_nulls_for_skip():
    request = {
        "stage": "entry_price",
        "exact_payload": {
            "price_context": {},
            "entry_context_features": {"quote_stale": True},
            "ai_market_snapshot_v1": {
                "ai_input_preflight_v1": {
                    "allowed": False,
                    "blockers": ["quote_stale"],
                    "venue_consistent": True,
                }
            },
        },
        "candidate": {
            "semantic_validator_version": (
                "entry_price_explicit_fill_value_semantic_v6"
            )
        },
    }
    response = {
        "edge_state": "INSUFFICIENT_DATA",
        "action": "SKIP",
        "expected_upside_pct": None,
        "expected_downside_pct": None,
        "confidence": 0,
        "reason_codes": ["insufficient_core_data"],
        "evidence": {
            "trend": "insufficient",
            "liquidity": "insufficient",
            "tape": "insufficient",
            "risk": "insufficient",
            "uncertainty": "high",
            "setup": "insufficient",
            "positive_edge": "insufficient",
            "adverse_risk": "insufficient",
            "trigger": "insufficient",
        },
        "selected_price": None,
        "price_basis": "NONE",
        "control_fill_probability_pct": 0.0,
        "selected_fill_probability_pct": None,
        "incremental_fill_probability_pct": None,
        "incremental_chase_cost_pct": None,
        "fill_adjusted_edge_pct": None,
    }

    errors = replay.quality.validate_replay_candidate_response(request, response)

    assert "entry_price_skip_requires_null_fill_value_ledger" in errors


def test_entry_price_fill_value_ledger_normalizes_derived_arithmetic_only():
    facts = {
        "control_selected_price": 1000,
        "control_exposure_selected": True,
        "price_delta_from_cost_baseline_bp": {"DEFENSIVE": 0.0},
    }
    response = {
        "action": "USE_DEFENSIVE",
        "selected_price": 1000,
        "price_basis": "DEFENSIVE",
        "expected_upside_pct": 0.6,
        "control_fill_probability_pct": 55.0,
        "selected_fill_probability_pct": 75.0,
        "incremental_fill_probability_pct": 20.0,
        "incremental_chase_cost_pct": 0.1,
        "fill_adjusted_edge_pct": 0.6,
    }

    normalized, provenance = replay.normalize_entry_price_fill_value_ledger(
        response,
        contract_facts=facts,
    )

    assert normalized["control_fill_probability_pct"] == 55.0
    assert normalized["selected_fill_probability_pct"] == 55.0
    assert normalized["incremental_fill_probability_pct"] == 0.0
    assert normalized["incremental_chase_cost_pct"] == 0.0
    assert normalized["fill_adjusted_edge_pct"] == 0.0
    assert provenance["entry_price_fill_value_normalization_applied"] is True
    assert (
        provenance["entry_price_raw_fill_value_ledger"]["selected_fill_probability_pct"]
        == 75.0
    )


def test_entry_price_equivalent_action_canonicalization_changes_label_only():
    response = {
        "action": "USE_REFERENCE",
        "selected_price": 100,
        "price_basis": "REFERENCE",
        "confidence": 70,
    }
    canonical, provenance = (
        replay.canonicalize_entry_price_economically_equivalent_action(
            response,
            contract_facts={
                "control_selected_price": 100,
                "candidate_prices": {"DEFENSIVE": 100, "REFERENCE": 100},
            },
        )
    )

    assert canonical["action"] == "USE_DEFENSIVE"
    assert canonical["price_basis"] == "DEFENSIVE"
    assert canonical["selected_price"] == response["selected_price"]
    assert response["action"] == "USE_REFERENCE"
    assert provenance["entry_price_action_canonicalization_applied"] is True


def test_entry_price_canonicalization_does_not_hide_raw_basis_price_mismatch():
    response = {
        "action": "IMPROVE_LIMIT",
        "selected_price": 100,
        "price_basis": "RESOLVED",
        "confidence": 70,
    }

    canonical, provenance = (
        replay.canonicalize_entry_price_economically_equivalent_action(
            response,
            contract_facts={
                "control_selected_price": 100,
                "candidate_prices": {
                    "DEFENSIVE": 100,
                    "RESOLVED": 101,
                },
            },
        )
    )

    assert canonical == response
    assert provenance["entry_price_action_canonicalization_applied"] is False


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


def test_prepare_entry_price_control_skip_has_no_selected_price_but_cost_baseline():
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
    trace = _trace("entry_price")
    trace.update({"action": "SKIP", "reference_price": 99})

    requests, _ = replay.prepare_stage_requests(
        stage="entry_price",
        dates=["2026-07-29"],
        max_rows=1,
        control_manifest=_control(),
        promotion={"promoted_at": "2026-07-29T08:56:00+09:00"},
        traces=[trace],
        payloads=[payload],
    )

    control = requests[0]["control"]
    facts = requests[0]["candidate_input"]["entry_price_exact_contract_facts_v1"]
    assert control["captured_selected_price"] is None
    assert control["captured_reference_price"] == 99
    assert facts["control_selected_price"] is None
    assert facts["control_exposure_selected"] is False
    assert facts["price_cost_baseline"] == 99


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


def test_reusable_pass_results_from_reports_deduplicates_valid_pair():
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

    reusable, sources = replay.reusable_pass_results_from_reports(
        existing_reports=[
            ("first.json", {"target_date": "first", "results": results}),
            ("duplicate.json", {"target_date": "duplicate", "results": results}),
        ],
        requests=requests,
    )

    assert len(reusable) == 1
    assert sources[0]["reused_pass_count"] == 1
    assert len(sources[0]["source_report_sha256"]) == 64
    assert sources[1]["matched_pass_count"] == 1
    assert sources[1]["reused_pass_count"] == 0


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


def test_bedrock_entry_price_correction_names_noncanonical_setup_code():
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
        "candidate_schema_correction_errors": [
            "reason_codes_invalid",
            "entry_price_aggressive_limit_nonpositive_fill_value",
        ],
        **replay.CONTRACT,
    }

    replay.execute_bedrock_candidate(request, provider=FakeProvider())

    assert "evidence.setup=continuation" in captured["prompt"]
    assert "do not retry REFERENCE, RESOLVED, or BEST_ASK" in captured["prompt"]


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


def test_entry_price_report_rejects_action_diversity_without_price_effect():
    requests = [
        {
            "paired_replay_id": f"pair-price-{index}",
            "stock_code": f"{index:06d}",
            "control": {
                "captured_action": "USE_DEFENSIVE",
                "captured_selected_price": 100,
            },
        }
        for index in range(30)
    ]
    results = [
        {
            "paired_replay_id": f"pair-price-{index}",
            "status": "pass",
            "control_response": {"action": "USE_DEFENSIVE"},
            "candidate_response": {
                "action": "USE_REFERENCE" if index % 2 else "USE_DEFENSIVE",
                "selected_price": 100,
                "price_basis": "REFERENCE" if index % 2 else "DEFENSIVE",
            },
        }
        for index in range(30)
    ]

    report = replay.build_report(
        target_date="2026-08-13",
        stage="entry_price",
        dates=["2026-08-12"],
        requested_max_rows=30,
        source_summary={},
        requests=requests,
        results=results,
    )

    assert report["candidate_action_not_collapsed"] is True
    assert report["entry_price_effect_not_collapsed"] is False
    assert report["entry_price_action_only_relabel_count"] == 15
    assert report["status"] == (
        "coverage_replay_complete_candidate_price_effect_collapsed"
    )
    assert "do-not-store" not in str(report)


def test_entry_price_report_uses_price_effect_instead_of_action_collapse():
    requests = [
        {
            "paired_replay_id": f"pair-price-effect-{index}",
            "stock_code": f"{index:06d}",
            "control": {
                "captured_action": "USE_DEFENSIVE",
                "captured_selected_price": 100,
            },
        }
        for index in range(30)
    ]
    results = [
        {
            "paired_replay_id": f"pair-price-effect-{index}",
            "status": "pass",
            "control_response": {"action": "USE_DEFENSIVE"},
            "candidate_response": {
                "action": "USE_DEFENSIVE",
                "selected_price": 99 if index == 0 else 100,
                "price_basis": "DEFENSIVE",
            },
        }
        for index in range(30)
    ]

    report = replay.build_report(
        target_date="2026-08-13",
        stage="entry_price",
        dates=["2026-08-12"],
        requested_max_rows=30,
        source_summary={},
        requests=requests,
        results=results,
    )

    assert report["candidate_action_not_collapsed"] is False
    assert report["candidate_action_collapse_decision_authority"] == (
        "diagnostic_only_price_effect_gate_owns_decision"
    )
    assert report["entry_price_effect_not_collapsed"] is True
    assert report["status"] == ("coverage_replay_complete_outcome_comparison_pending")


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
    assert report["summary"]["candidate_economically_distinct_price_count"] == 1
    assert report["summary"]["candidate_action_only_relabel_count"] == 0
    assert report["quality_checks"]["price_selection_effect_observed"] is True
    assert report["quality_checks"]["action_only_relabel_absent"] is True


def test_entry_price_outcome_status_does_not_mask_incomplete_candidate_execution():
    incomplete = {"status": "coverage_replay_incomplete"}
    comparison = {"status": "no_comparable_rows"}

    replay.apply_entry_price_outcome_status(incomplete, comparison)

    assert incomplete["status"] == "coverage_replay_incomplete"
    assert incomplete["entry_price_selection_outcome_status"] == ("no_comparable_rows")

    complete = {"status": "coverage_replay_complete_outcome_comparison_pending"}
    replay.apply_entry_price_outcome_status(
        complete, {"status": "candidate_quality_rejected"}
    )
    assert complete["status"] == ("coverage_replay_complete_candidate_quality_rejected")


def test_entry_price_outcome_treats_control_skip_as_exposure_change():
    request = {
        "decision_trace_id": "trace-skip",
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
            "captured_action": "SKIP",
            "captured_selected_price": None,
        },
    }
    result = {
        "decision_trace_id": "trace-skip",
        "status": "pass",
        "same_payload_confirmed": True,
        "candidate_response": {
            "action": "USE_DEFENSIVE",
            "selected_price": 99,
            "price_basis": "DEFENSIVE",
        },
    }
    label = {
        "decision_trace_id": "trace-skip",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "reference_price": 100,
        "horizon_metrics": {
            "10m": {
                "mfe_pct": 1.0,
                "mae_pct": -1.0,
                "end_return_pct": 0.5,
                "profit_opportunity_observed": True,
            }
        },
    }

    report = replay.build_entry_price_selection_outcome_comparison(
        requests=[request], results=[result], labels=[label]
    )

    row = report["rows"][0]
    assert row["control_exposure_selected"] is False
    assert row["candidate_exposure_selected"] is True
    assert row["exposure_selection_changed"] is True
    assert report["summary"]["candidate_exposure_selection_change_count"] == 1
    assert report["summary"]["candidate_action_only_relabel_count"] == 0
