from __future__ import annotations

import json

from src.engine.scalping import ai_decision_trace as trace


def _rows(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _enable(monkeypatch, tmp_path):
    monkeypatch.setenv("KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED", "true")
    monkeypatch.setattr(trace, "DATA_DIR", tmp_path)
    trace._SEEN_PAYLOAD_HASHES.clear()
    trace._SEEN_PROMPT_HASHES.clear()
    trace._SEEN_TRACE_IDS.clear()


def test_capture_ai_request_persists_exact_payload_once(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    user_input = {
        "input_schema": "entry_screen_v2",
        "stock_code": "005930",
        "current_price": 70100,
        "best_bid": 70000,
        "best_ask": 70100,
        "ai_market_snapshot_v1": {
            "snapshot_id": "aims-1",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "broker_route": "SOR",
            "market_data_route": "krx_nxt_integrated",
        },
    }

    first = trace.capture_ai_request(
        prompt="prompt",
        user_input=user_input,
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-1",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
        temperature=0.2,
        max_output_tokens=700,
        reasoning_effort="low",
        metadata={"record_id": "17"},
    )
    second = trace.capture_ai_request(
        prompt="prompt",
        user_input=user_input,
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-2",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
        temperature=0.2,
        max_output_tokens=700,
        reasoning_effort="low",
        metadata={"record_id": "17"},
    )

    path = trace._payload_path(trace._date_text())
    assert len(_rows(path)) == 1
    assert len(_rows(trace._prompt_path(trace._date_text()))) == 1
    assert first["ai_input_payload_sha256"] == second["ai_input_payload_sha256"]
    assert first["ai_request_envelope_sha256"] == second["ai_request_envelope_sha256"]
    assert first["ai_input_payload_replay_exact"] is True
    assert first["ai_prompt_replay_exact"] is True
    assert first["ai_trace_stock_code"] == "005930"
    assert first["ai_trace_snapshot_id"] == "aims-1"
    assert first["ai_trace_reference_price"] == 70100
    assert first["ai_trace_reference_price_type"] == "executable_ask"
    assert first["ai_trace_best_bid"] == 70000
    assert first["ai_trace_best_ask"] == 70100
    payload_row = _rows(path)[0]
    assert payload_row["temperature"] == 0.2
    assert payload_row["max_output_tokens"] == 700
    assert payload_row["reasoning_effort"] == "low"


def test_capture_ai_request_prefers_resolved_entry_price_over_earlier_market_values(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "input_schema": "entry_price_v2",
            "stock_code": "005930",
            "ws_data": {"curr": 70100},
            "quote_change": {
                "decision_start_quote": {
                    "current_price": 70100,
                    "best_bid": 70000,
                    "best_ask": 70200,
                }
            },
            "candidate_prices": {
                "resolved_order_price": 69900,
            },
        },
        endpoint_name="entry_price",
        symbol="005930",
        request_id="entry-price-request",
        model="gpt-test",
        schema_name="entry_price_v1",
        require_json=True,
    )

    assert fields["ai_trace_reference_price"] == 69900
    assert fields["ai_trace_reference_price_type"] == "resolved_order_price"
    assert fields["ai_trace_best_bid"] == 70000
    assert fields["ai_trace_best_ask"] == 70200

    zero_resolved_fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "input_schema": "entry_price_v2",
            "stock_code": "005930",
            "quote_change": {
                "decision_start_quote": {
                    "current_price": 70100,
                    "best_bid": 70000,
                    "best_ask": 70200,
                }
            },
            "candidate_prices": {"resolved_order_price": 0},
        },
        endpoint_name="entry_price",
        symbol="005930",
        request_id="entry-price-zero-request",
        model="gpt-test",
        schema_name="entry_price_v1",
        require_json=True,
    )
    assert zero_resolved_fields["ai_trace_reference_price"] == 70200
    assert zero_resolved_fields["ai_trace_reference_price_type"] == "executable_ask"

    trace.record_ai_decision_trace(
        {
            **fields,
            "action": "USE_DEFENSIVE",
            "order_price": 69800,
            "provider_called": True,
            "provider": "bedrock",
            "bedrock_primary_used": True,
            "bedrock_model_family": "qwen3_32b",
            "ai_parse_ok": True,
        },
        prompt_type="entry_price",
        prompt_version="entry_price_v1",
        result_source="live",
    )

    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    outcome_row = _rows(trace._outcome_path(trace._date_text()))[0]
    assert trace_row["decision_trace_id"] == "entry-price-request"
    assert trace_row["prompt_sha256"] == fields["ai_prompt_sha256"]
    assert trace_row["prompt_store_date"] == fields["ai_prompt_store_date"]
    assert trace_row["payload_sha256"] == fields["ai_input_payload_sha256"]
    assert trace_row["payload_store_date"] == fields["ai_input_payload_store_date"]
    assert trace_row["request_envelope_sha256"] == fields["ai_request_envelope_sha256"]
    assert trace_row["provider_actual"] == "bedrock"
    assert trace_row["model"] == "qwen3_32b"
    assert trace_row["reference_price"] == 69800
    assert trace_row["reference_price_type"] == "resolved_order_price"
    assert trace_row["prompt_replay_exact"] is True
    assert trace_row["payload_replay_exact"] is True
    assert outcome_row["reference_price"] == 69800
    assert outcome_row["reference_price_type"] == "resolved_order_price"
    assert outcome_row["source_quality_status"] == "pending_future_window"
    assert outcome_row["invalid_reasons"] == []

    trace.record_ai_decision_trace(
        {
            **zero_resolved_fields,
            "action": "USE_DEFENSIVE",
            "order_price": 0,
            "provider_called": True,
            "provider": "bedrock",
            "bedrock_primary_used": True,
            "bedrock_model_family": "qwen3_32b",
            "ai_parse_ok": True,
        },
        prompt_type="entry_price",
        prompt_version="entry_price_v1",
        result_source="live",
    )
    zero_trace_row = _rows(trace._trace_path(trace._date_text()))[1]
    zero_outcome_row = _rows(trace._outcome_path(trace._date_text()))[1]
    assert zero_trace_row["reference_price"] == 70200
    assert zero_trace_row["reference_price_type"] == "executable_ask"
    assert zero_outcome_row["reference_price"] == 70200
    assert zero_outcome_row["source_quality_status"] == "pending_future_window"


def test_capture_holding_request_uses_executable_bid_not_historical_entry_price(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "input_schema": "holding_score_v2",
            "stock_code": "005930",
            "entry_time_context": {"resolved_order_price": 69_900},
            "position_context": {"current_price": 70_100},
            "holding_decision_context": {
                "microstructure": {
                    "best_bid": 70_000,
                    "best_ask": 70_200,
                }
            },
        },
        endpoint_name="holding_score",
        symbol="005930",
        request_id="holding-score-request",
        model="gpt-test",
        schema_name="holding_score_v2",
        require_json=True,
    )

    assert fields["ai_trace_reference_price"] == 70_000
    assert fields["ai_trace_reference_price_type"] == "executable_bid"
    assert fields["ai_trace_best_bid"] == 70_000
    assert fields["ai_trace_best_ask"] == 70_200


def test_capture_ai_request_redacts_sensitive_values(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "stock_code": "005930",
            "api_key": "secret-value",
            "authorization": "Bearer abc",
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-redacted",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    row = _rows(trace._payload_path(trace._date_text()))[0]
    assert fields["ai_input_payload_redacted"] is True
    assert fields["ai_input_payload_replay_exact"] is False
    assert row["sanitized_user_input"]["api_key"] == "[REDACTED]"
    assert row["sanitized_user_input"]["authorization"] == "[REDACTED]"
    assert "secret-value" not in json.dumps(row)


def test_record_decision_creates_pending_outcome_idempotently(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    result = {
        "ai_decision_trace_id": "request-1",
        "action": "WAIT",
        "score": 62,
        "reason": "Mixed continuation evidence",
        "provider_called": True,
        "ai_model": "gpt-test",
        "ai_parse_ok": True,
        "ai_input_payload_sha256": "a" * 64,
        "ai_input_payload_replay_exact": True,
        "ai_trace_stock_code": "005930",
        "ai_trace_effective_venue": "KRX",
        "ai_trace_session_bucket": "KRX_REGULAR",
        "ai_trace_reference_price": 70100,
        "ai_input_preflight_status": "fresh_consistent",
        "ai_input_preflight_allowed": True,
        "ai_input_preflight_venue_consistent": True,
    }

    fields = trace.record_ai_decision_trace(
        result,
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )
    trace.record_ai_decision_trace(
        result,
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )

    trace_rows = _rows(trace._trace_path(trace._date_text()))
    outcome_rows = _rows(trace._outcome_path(trace._date_text()))
    assert fields["ai_decision_trace_id"] == "request-1"
    assert len(trace_rows) == 1
    assert trace_rows[0]["decision_stage"] == "entry_screen"
    assert trace_rows[0]["provider_actual"] == "openai"
    assert trace_rows[0]["provider_decision_origin"] == "openai"
    assert trace_rows[0]["payload_replay_exact"] is True
    assert trace_rows[0]["decision_result_sha256"]
    assert trace_rows[0]["runtime_effect"] is False
    assert len(outcome_rows) == 1
    assert outcome_rows[0]["label_status"] == "pending"
    assert outcome_rows[0]["decision_ts"] == trace_rows[0]["decision_ts"]
    assert outcome_rows[0]["action"] == "WAIT"
    assert outcome_rows[0]["pending_horizons_min"] == [1, 3, 5, 10, 20, 30, 60]
    assert outcome_rows[0]["allowed_runtime_apply"] is False


def test_no_provider_decision_still_has_trace_without_order_authority(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
        {
            "action": "DROP",
            "reason": "ai_input_preflight_blocked",
            "provider_called": False,
            "ai_market_snapshot_stock_code": "005930",
            "ai_market_snapshot_effective_venue": "KRX",
            "ai_input_preflight_status": "blocked",
            "ai_input_preflight_allowed": False,
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="input_preflight_blocked",
        provider_called=False,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert fields["ai_decision_trace_id"].startswith("aidt-")
    assert row["provider_called"] is False
    assert row["provider_actual"] is None
    assert row["actual_order_authority"] is False
    assert row["broker_order_forbidden"] is True
    assert row["venue_consistent"] is None


def test_cache_trace_separates_provider_call_from_decision_origin(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "WAIT",
            "provider_called": False,
            "cache_hit": True,
            "ai_model": "gpt-test",
            "ai_trace_stock_code": "005930",
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="cache",
        provider_called=False,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["provider_actual"] is None
    assert row["provider_decision_origin"] == "openai"


def test_bedrock_trace_separates_requested_and_actual_model(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "USE_AI",
            "provider_called": True,
            "openai_model": "gpt-requested",
            "bedrock_primary_used": True,
            "bedrock_model_family": "qwen3-32b",
            "ai_trace_stock_code": "005930",
        },
        prompt_type="entry_price",
        prompt_version="entry_price_v1",
        result_source="live",
        provider_called=True,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["provider_actual"] == "bedrock"
    assert row["model_requested"] == "gpt-requested"
    assert row["model"] == "qwen3-32b"


def test_bedrock_failback_records_openai_as_actual_provider(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "WAIT",
            "openai_model": "gpt-failback",
            "bedrock_primary_used": False,
            "bedrock_failback_used": True,
            "ai_trace_stock_code": "005930",
        },
        prompt_type="scalping_holding_score",
        prompt_version="holding_score_v2",
        result_source="live",
        provider_called=True,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["provider_actual"] == "openai"
    assert row["model"] == "gpt-failback"


def test_non_code_identifier_is_not_written_as_stock_code(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {"action": "WAIT"},
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="cache",
        stock_code="테스트종목",
        provider_called=False,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["stock_code"] == "-"
    assert row["stock_identifier"] == "테스트종목"


def test_swing_gatekeeper_is_excluded_from_scalping_trace(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
        {"action_key": "wait", "selected_mode": "SWING"},
        prompt_type="realtime_gatekeeper",
        prompt_version="gatekeeper_quant_packet_v2",
        result_source="cache",
        provider_called=False,
    )

    assert fields == {}
    assert not trace._trace_path(trace._date_text()).exists()


def test_same_input_with_different_request_config_keeps_two_envelopes(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    common = {
        "prompt": "prompt",
        "user_input": {"stock_code": "005930", "current_price": 70000},
        "endpoint_name": "analyze_target",
        "symbol": "005930",
        "model": "gpt-test",
        "schema_name": "entry_v1",
        "require_json": True,
    }

    first = trace.capture_ai_request(
        **common,
        request_id="request-config-1",
        temperature=0.1,
    )
    second = trace.capture_ai_request(
        **common,
        request_id="request-config-2",
        temperature=0.3,
    )

    assert first["ai_input_payload_sha256"] == second["ai_input_payload_sha256"]
    assert first["ai_request_envelope_sha256"] != second["ai_request_envelope_sha256"]
    assert len(_rows(trace._payload_path(trace._date_text()))) == 2
