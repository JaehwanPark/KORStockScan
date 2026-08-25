from __future__ import annotations

import json
import stat
from contextlib import contextmanager

import pytest

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
    trace._SEEN_REQUEST_IDS.clear()
    trace._SEEN_OUTCOME_LABEL_IDS.clear()
    trace._SEEN_CONTEXT_CANDIDATE_HASHES.clear()


def test_append_jsonl_fails_closed_on_parent_directory_replacement(
    tmp_path,
    monkeypatch,
):
    parent = tmp_path / "ai_decision_trace"
    replaced_parent = tmp_path / "ai_decision_trace-replaced"
    parent.mkdir()
    path = parent / "ai_decision_trace_2026-08-25.jsonl"
    original_lock = trace.jsonl_artifact_generation_lock

    @contextmanager
    def replace_parent_after_lock(*args, **kwargs):
        with original_lock(*args, **kwargs) as generation:
            parent.rename(replaced_parent)
            parent.mkdir()
            yield generation

    monkeypatch.setattr(
        trace,
        "jsonl_artifact_generation_lock",
        replace_parent_after_lock,
    )

    with pytest.raises(OSError, match="jsonl_generation_parent_changed"):
        trace._append_jsonl(path, {"schema": "ai_decision_trace_v1"})

    assert list(parent.iterdir()) == []
    assert not (replaced_parent / path.name).exists()


def test_append_jsonl_rejects_named_entry_replacement_after_write(
    tmp_path,
    monkeypatch,
):
    parent = tmp_path / "ai_decision_trace"
    parent.mkdir()
    path = parent / "ai_decision_trace_2026-08-25.jsonl"
    path.write_text('{"generation":"old"}\n', encoding="utf-8")
    replacement = parent / "replacement.tmp"
    replacement_bytes = b'{"generation":"replacement"}\n'
    real_write = trace.os.write
    replaced = False

    def replace_named_entry_after_write(descriptor, payload):
        nonlocal replaced
        count = real_write(descriptor, payload)
        if not replaced:
            replaced = True
            replacement.write_bytes(replacement_bytes)
            replacement.replace(path)
        return count

    monkeypatch.setattr(trace.os, "write", replace_named_entry_after_write)

    with pytest.raises(OSError, match="jsonl_generation_entry_changed"):
        trace._append_jsonl(path, {"schema": "ai_decision_trace_v1"})

    assert path.read_bytes() == replacement_bytes


def test_timeout_exception_trace_normalizes_transport_provenance(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "DROP",
            "score": 0,
            "reason": (
                "OpenAI Responses HTTP timeout budget exhausted: "
                "endpoint=analyze_target, attempts=1, request timed out"
            ),
            "provider_called": False,
            "openai_http_attempt_count": 1,
            "openai_http_timeout_budget_exhausted": True,
            "openai_transport_mode": "http",
            "ai_parse_ok": False,
        },
        prompt_type="scalping_entry",
        prompt_version="decision_quality_v2_7",
        result_source="exception",
        stock_code="068270",
        provider_called=False,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["timeout"] is True
    assert row["result_source"] == "timeout"
    assert row["decision_evaluation_status"] == "not_evaluated_transport_timeout"
    assert row["provider_called"] is True
    assert row["provider_actual"] == "openai"


def test_non_timeout_transport_failure_is_not_labeled_timeout(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "DROP",
            "score": 0,
            "reason": "provider returned invalid response",
            "provider_called": True,
            "openai_transport_fail_closed": True,
            "openai_transport_mode": "http",
            "ai_parse_ok": False,
        },
        prompt_type="scalping_entry",
        prompt_version="decision_quality_v2_7",
        result_source="exception",
        stock_code="068270",
        provider_called=True,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["timeout"] is False
    assert row["result_source"] == "exception"
    assert row["decision_evaluation_status"] == "not_evaluated_provider_or_preflight"
    assert row["provider_called"] is True


def test_trace_preserves_parent_entry_price_lineage(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "WAIT",
            "score": 72,
            "reason": "fresh exact context retry",
            "ai_decision_parent_trace_id": "trace-entry-price",
            "ai_input_parent_snapshot_id": "snapshot-entry-price",
            "ai_parent_source_event_stage": "pre_submit_entry_ai_authority_retry",
            "ai_parse_ok": True,
        },
        prompt_type="scalping_entry",
        prompt_version="decision_quality_v2_7",
        result_source="live",
        stock_code="005930",
        provider_called=True,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["parent_decision_trace_id"] == "trace-entry-price"
    assert row["parent_snapshot_id"] == "snapshot-entry-price"
    assert row["parent_source_event_stage"] == "pre_submit_entry_ai_authority_retry"


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
    request_rows = _rows(trace._request_path(trace._date_text()))
    assert [row["request_id"] for row in request_rows] == [
        "request-1",
        "request-2",
    ]
    assert all(
        row["payload_sha256"] == first["ai_input_payload_sha256"]
        for row in request_rows
    )
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
    assert payload_row["request_id"] == "request-1"
    assert payload_row["symbol"] == "005930"
    assert payload_row["temperature"] == 0.2
    assert payload_row["max_output_tokens"] == 700
    assert payload_row["reasoning_effort"] == "low"


def test_capture_ai_request_separates_compact_provider_input_from_replay_context(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    provider_input = {
        "input_schema": "entry_setup_v2_14_risk_input_v1",
        "entry_setup_evidence_v1": {"setup_family": "CLEAN_CONTINUATION"},
    }
    replay_context = {
        "exact_payload": {
            "input_schema": "entry_screen_hot_v1",
            "stock_code": "005930",
            "current": {"price": 70100},
        },
        "entry_setup_evidence_v1": {"setup_family": "CLEAN_CONTINUATION"},
    }

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input=provider_input,
        replay_context=replay_context,
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-compact-1",
        model="gpt-test",
        schema_name="entry_setup_risk_adjudication_v1",
        require_json=True,
    )
    trace.capture_ai_request(
        prompt="prompt",
        user_input=provider_input,
        replay_context={
            **replay_context,
            "exact_payload": {
                **replay_context["exact_payload"],
                "current": {"price": 70200},
            },
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-compact-2",
        model="gpt-test",
        schema_name="entry_setup_risk_adjudication_v1",
        require_json=True,
    )

    rows = _rows(trace._payload_path(trace._date_text()))
    assert len(rows) == 2
    assert rows[0]["sanitized_user_input"] == provider_input
    assert rows[0]["sanitized_replay_context"] == replay_context
    assert trace.replay_source_input(rows[0]) == replay_context
    assert rows[0]["payload_bytes"] < rows[0]["replay_context_bytes"]
    assert fields["ai_replay_context_exact"] is True
    assert fields["ai_input_payload_bytes"] == rows[0]["payload_bytes"]
    trace.record_ai_decision_trace(
        {
            **fields,
            "action": "WAIT",
            "provider_called": True,
            "provider": "openai",
            "openai_model": "gpt-test",
            "ai_parse_ok": True,
        },
        prompt_type="scalping_entry",
        prompt_version="entry_setup_risk_adjudication_v1",
        result_source="live",
    )
    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    assert trace_row["replay_context_present"] is True
    assert trace_row["replay_context_exact"] is True
    assert trace_row["replay_context_sha256"] == fields["ai_replay_context_sha256"]
    assert (
        trace.replay_source_input(
            {
                "replay_context_present": True,
                "replay_context_exact": False,
                "sanitized_user_input": provider_input,
            }
        )
        is None
    )


def test_capture_ai_request_preserves_simulation_cohort_provenance(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "input_schema": "holding_score_v2",
            "stock_code": "005930",
            "holding_decision_context": {
                "schema": "holding_decision_context_v1",
                "candle": {
                    "input_bundle_version": "scalping_multi_timeframe_context_v1",
                    "bars": [
                        {
                            "minute": "09:00",
                            "close": 100,
                            "is_forming": False,
                        }
                    ],
                },
            },
        },
        endpoint_name="holding_score",
        symbol="005930",
        request_id="holding-sim-request",
        model="gpt-test",
        schema_name="holding_score_v2",
        require_json=True,
        metadata={
            "sim_record_id": "sim-005930-1",
            "sim_parent_record_id": "sim-parent-1",
            "source_event_stage": "scalp_sim_holding_review",
        },
    )

    assert fields["sim_record_id"] == "sim-005930-1"
    assert fields["sim_parent_record_id"] == "sim-parent-1"
    assert fields["source_event_stage"] == "scalp_sim_holding_review"
    request_row = _rows(trace._request_path(trace._date_text()))[0]
    assert request_row["sim_record_id"] == "sim-005930-1"
    assert request_row["source_event_stage"] == "scalp_sim_holding_review"
    trace.record_ai_decision_trace(
        {
            **fields,
            "action": "HOLD",
            "score": 60,
            "provider_called": True,
            "provider": "openai",
            "ai_parse_ok": True,
        },
        prompt_type="scalping_holding_score",
        prompt_version="holding_score_v2",
        result_source="live",
    )
    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    assert trace_row["sim_record_id"] == "sim-005930-1"
    assert trace_row["position_reconciliation_mode"] is None
    assert trace_row["source_event_stage"] == "scalp_sim_holding_review"


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
    assert trace_row["request_capture_status"] == "captured"
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


def test_capture_marks_compact_forensic_context_ineligible_without_reconstructing_it(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "stock_code": "005930",
            "entry_candle_context": {
                "schema": "entry_candle_context_v1",
                "input_bundle_version": "scalping_multi_timeframe_context_v1",
                "bars": [],
            },
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="compact-forensic-request",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    assert fields["ai_trace_canonical_context_capture_status"] == (
        "canonical_completed_bars_missing"
    )
    payload_row = _rows(trace._payload_path(trace._date_text()))[0]
    assert payload_row["canonical_context_capture"] == {
        "expected_schema": "entry_candle_context_v1",
        "status": "canonical_completed_bars_missing",
        "exact_v2_candidate": False,
        "schema": "entry_candle_context_v1",
        "input_bundle_version": "scalping_multi_timeframe_context_v1",
        "raw_bar_count": 0,
        "completed_bar_count": 0,
        "forming_bar_present": False,
    }


def test_capture_marks_canonical_completed_bars_as_exact_candidate(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "stock_code": "005930",
            "entry_candle_context": {
                "schema": "entry_candle_context_v1",
                "input_bundle_version": "scalping_multi_timeframe_context_v1",
                "bars": [
                    {"t": "09:00", "c": 100, "forming": False},
                    {"t": "09:01", "c": 101, "forming": True},
                ],
            },
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="canonical-request",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    assert fields["ai_trace_canonical_context_capture_status"] == (
        "exact_completed_bars_captured"
    )
    assert fields["ai_trace_canonical_context_completed_bar_count"] == 1
    assert fields["ai_trace_canonical_context_forming_bar_present"] is True


def test_capture_finds_holding_context_embedded_after_known_plain_text_marker(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    holding_context = {
        "schema": "holding_decision_context_v1",
        "candle": {
            "input_bundle_version": "scalping_multi_timeframe_context_v1",
            "bars": [
                {"t": "09:00", "c": 100, "is_forming": False},
                {"t": "09:01", "c": 101, "is_forming": True},
            ],
        },
    }
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input=(
            "[POSITION_CONTEXT]\ncurrent_price: 101\n\n"
            "[HOLDING_DECISION_CONTEXT]\n"
            + json.dumps(holding_context, separators=(",", ":"))
            + "\n\n[DECISION_REQUEST]\nChoose HOLD, TRIM, or EXIT."
        ),
        endpoint_name="holding_flow",
        symbol="005930",
        request_id="holding-plain-text-canonical",
        model="gpt-test",
        schema_name="holding_flow_v1",
        require_json=True,
    )

    assert fields["ai_trace_canonical_context_capture_status"] == (
        "exact_completed_bars_captured"
    )
    assert fields["ai_trace_canonical_context_schema"] == (
        "holding_decision_context_v1"
    )
    assert fields["ai_trace_canonical_context_completed_bar_count"] == 1
    assert fields["ai_trace_canonical_context_forming_bar_present"] is True


def test_capture_does_not_accept_malformed_marked_holding_context(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input="[HOLDING_DECISION_CONTEXT]\n{malformed-json}",
        endpoint_name="holding_flow",
        symbol="005930",
        request_id="holding-plain-text-malformed",
        model="gpt-test",
        schema_name="holding_flow_v1",
        require_json=True,
    )

    assert fields["ai_trace_canonical_context_capture_status"] == (
        "canonical_context_missing"
    )


def test_capture_uses_request_metadata_for_venue_when_payload_is_compact(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "input_schema": "entry_screen_hot_v1",
            "current": {"price": 70000},
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="compact-with-exact-route",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
        metadata={
            "effective_venue": "NXT",
            "session_bucket": "nxt_aftermarket",
            "broker_route": "SOR",
            "market_data_route": "nxt_only",
            "snapshot_id": "snapshot-nxt-1",
        },
    )

    row = _rows(trace._request_path(trace._date_text()))[0]
    assert fields["ai_trace_effective_venue"] == "NXT"
    assert row["effective_venue"] == "NXT"
    assert row["snapshot_id"] == "snapshot-nxt-1"
    assert row["session_bucket"] == "nxt_aftermarket"
    assert row["broker_route"] == "SOR"
    assert row["market_data_route"] == "nxt_only"
    assert row["canonical_context_capture"]["status"] == "canonical_context_missing"


def test_capture_canonical_context_candidate_is_separate_from_ai_request(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    source_context = {
        "schema": "entry_candle_context_v1",
        "enabled": False,
        "venue": "KRX",
        "session": "krx_regular",
        "input_bundle_version": "scalping_multi_timeframe_context_v1",
        "bars": [{"t": "09:00", "c": 70000, "forming": False}],
        "source_quality": {"status": "fresh_consistent", "blockers": []},
    }
    model_context = {
        **source_context,
        "multi_timeframe_ai_input_enabled": True,
        "multi_timeframe_context": {
            "schema": "scalping_multi_timeframe_context_v1",
            "source_quality": {"status": "pass"},
        },
    }

    fields = trace.capture_canonical_context_candidate(
        source_context=source_context,
        model_context=model_context,
        endpoint_name="analyze_target",
        symbol="005930",
        call_inputs={
            "target_name": "삼성전자",
            "ws_data": {"curr": 70050},
            "recent_ticks": [],
            "recent_candles": [{"현재가": 70050}],
            "strategy": "SCALPING",
            "program_net_qty": 0,
            "cache_profile": "default",
            "prompt_profile": "watching",
        },
        metadata={"source_event_stage": "watching_analyze_target_async_v1"},
    )

    rows = _rows(trace._context_candidate_path(trace._date_text()))
    assert len(rows) == 1
    assert rows[0]["validation_only_eligible"] is True
    assert rows[0]["request_capture_status"] == "not_called_candidate_only"
    assert rows[0]["provider_called"] is False
    assert rows[0]["decision_authority"] == "forensics_only_no_runtime_change"
    assert rows[0]["runtime_effect"] is False
    assert rows[0]["actual_order_submitted"] is False
    assert rows[0]["call_inputs"]["ws_data"]["curr"] == 70050
    assert rows[0]["call_inputs_contract"]["ready"] is True
    assert rows[0]["canonical_context_capture"]["status"] == (
        "exact_completed_bars_captured"
    )
    assert fields["ai_context_candidate_sha256"] == rows[0]["candidate_sha256"]
    assert not trace._request_path(trace._date_text()).exists()
    assert not trace._payload_path(trace._date_text()).exists()


def test_trace_distinguishes_promotion_gated_candidate_from_applied_payload(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    fields = trace.record_ai_decision_trace(
        {
            "action": "WAIT",
            "provider_called": True,
            "provider": "openai",
            "ai_trace_canonical_context_capture_status": "canonical_context_missing",
            "ai_context_candidate_status": "ready_for_explicit_provider_call",
            "ai_context_candidate_schema": "entry_candle_context_v1",
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert fields["ai_decision_trace_id"] == row["decision_trace_id"]
    assert row["canonical_context_capture_status"] == "canonical_context_missing"
    assert row["canonical_context_candidate_status"] == (
        "ready_for_explicit_provider_call"
    )
    assert row["canonical_context_candidate_schema"] == "entry_candle_context_v1"
    assert row["canonical_context_application_state"] == (
        "promotion_gated_forensic_exact_available"
    )


def test_trace_marks_exact_canonical_payload_as_applied(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    trace.record_ai_decision_trace(
        {
            "action": "WAIT",
            "provider_called": True,
            "provider": "openai",
            "ai_trace_canonical_context_capture_status": "exact_completed_bars_captured",
            "ai_context_candidate_status": "ready_for_explicit_provider_call",
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["canonical_context_application_state"] == "applied_exact"


def test_capture_canonical_context_candidate_rejects_redacted_source(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    source_context = {
        "schema": "entry_candle_context_v1",
        "enabled": False,
        "venue": "KRX",
        "session": "krx_regular",
        "input_bundle_version": "scalping_multi_timeframe_context_v1",
        "bars": [{"t": "09:00", "c": 70000, "forming": False}],
        "source_quality": {"status": "fresh_consistent", "blockers": []},
        "api_key": "must-not-persist",
    }

    trace.capture_canonical_context_candidate(
        source_context=source_context,
        model_context=source_context,
        endpoint_name="analyze_target",
        symbol="005930",
        call_inputs={
            "target_name": "삼성전자",
            "ws_data": {},
            "recent_ticks": [],
            "recent_candles": [],
            "strategy": "SCALPING",
            "program_net_qty": 0,
            "cache_profile": "default",
            "prompt_profile": "watching",
        },
    )

    row = _rows(trace._context_candidate_path(trace._date_text()))[0]
    assert row["source_context"]["api_key"] == "[REDACTED]"
    assert row["validation_only_eligible"] is False


def test_capture_holding_candidate_accepts_feature_disabled_clean_source(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    candle = {
        "schema": "entry_candle_context_v1",
        "enabled": False,
        "venue": "KRX",
        "session": "krx_regular",
        "input_bundle_version": "scalping_multi_timeframe_context_v1",
        "bars": [{"t": "09:00", "c": 70000, "forming": False}],
        "source_quality": {"status": "fresh_consistent", "blockers": []},
    }
    source_context = {
        "schema": "holding_decision_context_v1",
        "enabled": False,
        "venue": "KRX",
        "session": "krx_regular",
        "candle": candle,
        "source_quality": {"status": "disabled", "blockers": []},
    }
    model_context = {
        **source_context,
        "candle": {
            **candle,
            "multi_timeframe_ai_input_enabled": True,
        },
    }

    trace.capture_canonical_context_candidate(
        source_context=source_context,
        model_context=model_context,
        endpoint_name="holding_score",
        symbol="005930",
        call_inputs={
            "stock_name": "삼성전자",
            "stock_code": "005930",
            "ws_data": {"curr": 70000},
            "recent_ticks": [],
            "recent_candles": [{"현재가": 70000}],
            "position_ctx": {"buy_price": 69000, "quantity": 1},
        },
    )

    row = _rows(trace._context_candidate_path(trace._date_text()))[0]
    assert row["promotion_disabled_only"] is True
    assert row["validation_only_eligible"] is True


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
                "schema": "holding_decision_context_v1",
                "candle": {
                    "input_bundle_version": "scalping_multi_timeframe_context_v1",
                    "bars": [{"minute": "09:00", "close": 70_000, "is_forming": False}],
                },
                "microstructure": {
                    "best_bid": 70_000,
                    "best_ask": 70_200,
                },
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
    assert fields["ai_trace_canonical_context_capture_status"] == (
        "exact_completed_bars_captured"
    )


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


def test_capture_ai_request_redacts_embedded_credentials_without_redacting_session(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.capture_ai_request(
        prompt=(
            "Use Authorization: Bearer abcdef123456 and "
            "api_key=sk-1234567890abcdefghijklmnop"
        ),
        user_input={
            "stock_code": "005930",
            "session_bucket": "KRX_REGULAR",
            "token": "generic-token-secret",
            "refresh_token": "refresh-secret",
            "headers": {
                "Cookie": "sessionid=private-cookie",
                "X-Debug": "access_token=url-secret&mode=test",
            },
            "note": (
                "jwt=eyJabcdefghijk.abcdefghijk.abcdefghijk "
                'aws=AKIA1234567890ABCDEF password="two word secret"'
            ),
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-embedded-redacted",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    payload_row = _rows(trace._payload_path(trace._date_text()))[0]
    prompt_row = _rows(trace._prompt_path(trace._date_text()))[0]
    serialized = json.dumps(
        {"payload": payload_row, "prompt": prompt_row},
        ensure_ascii=False,
    )
    assert fields["ai_input_payload_replay_exact"] is False
    assert fields["ai_prompt_replay_exact"] is False
    assert payload_row["sanitized_user_input"]["session_bucket"] == "KRX_REGULAR"
    assert payload_row["sanitized_user_input"]["refresh_token"] == "[REDACTED]"
    for secret in (
        "refresh-secret",
        "generic-token-secret",
        "private-cookie",
        "url-secret",
        "abcdef123456",
        "sk-1234567890abcdefghijklmnop",
        "eyJabcdefghijk.abcdefghijk.abcdefghijk",
        "AKIA1234567890ABCDEF",
        "two word secret",
    ):
        assert secret not in serialized
    assert payload_row["storage_security_policy"] == "ai_trace_payload_security_v2"
    assert payload_row["raw_secret_storage"] is False


def test_prompt_sanitizer_preserves_nonsecret_json_enum_token(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    prompt = (
        "The action value must be exactly one JSON enum token: BUY, WAIT, or DROP. "
        "Never expose token=actual-secret or JSON enum token: hidden-secret."
    )

    fields = trace.capture_ai_request(
        prompt=prompt,
        user_input={"stock_code": "005930"},
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-enum-token",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    prompt_row = _rows(trace._prompt_path(trace._date_text()))[0]
    assert "JSON enum token: BUY, WAIT, or DROP" in prompt_row["sanitized_prompt"]
    assert "actual-secret" not in prompt_row["sanitized_prompt"]
    assert "hidden-secret" not in prompt_row["sanitized_prompt"]
    assert fields["ai_prompt_replay_exact"] is False


def test_prompt_sanitizer_keeps_nonsecret_json_enum_only_prompt_exact(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    prompt = "The action value must be exactly one JSON enum token: BUY, WAIT, or DROP."

    fields = trace.capture_ai_request(
        prompt=prompt,
        user_input={"stock_code": "005930"},
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-enum-token-only",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    prompt_row = _rows(trace._prompt_path(trace._date_text()))[0]
    assert prompt_row["sanitized_prompt"] == prompt
    assert prompt_row["redacted"] is False
    assert prompt_row["replay_exact"] is True
    assert fields["ai_prompt_redacted"] is False
    assert fields["ai_prompt_replay_exact"] is True


def test_payload_sanitizer_preserves_nonsecret_token_metrics_and_redacts_opaque_keys(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    secret_key = "sk-1234567890abcdefghijklmnop"

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "stock_code": "005930",
            "token_usage": {"input": 10, "output": 2},
            "secretary_score": 77,
            "kiwoom_token": "opaque-provider-token",
            "accessToken": "camel-secret",
            "APIKey": "uppercase-camel-secret",
            secret_key: "dynamic-secret-key",
            "binary_note": b"key=sk-abcdefghijklmnopqrstuvwxyz",
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-key-boundary",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    row = _rows(trace._payload_path(trace._date_text()))[0]
    sanitized = row["sanitized_user_input"]
    serialized = json.dumps(sanitized, ensure_ascii=False)
    assert fields["ai_input_payload_replay_exact"] is False
    assert sanitized["token_usage"] == {"input": 10, "output": 2}
    assert sanitized["secretary_score"] == 77
    assert sanitized["kiwoom_token"] == "[REDACTED]"
    assert sanitized["accessToken"] == "[REDACTED]"
    assert sanitized["APIKey"] == "[REDACTED]"
    assert secret_key not in serialized
    assert "dynamic-secret-key" not in serialized
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in serialized


def test_payload_sanitizer_preserves_only_approved_runtime_cache_token_paths(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    bucket_token = (
        "score_70_74|risk_neutral|market_regime_neutral|fresh|"
        "price_valid|liquidity_normal|not_overbought|midday"
    )
    runtime_context = {
        "entry_adm": {
            "cache_token": f"entry_adm:v1:{bucket_token}",
            "entry_adm_bucket_token": bucket_token,
            "entry_adm_cache_token": f"entry_adm:v1:{bucket_token}",
        },
        "holding_exit_matrix": {
            "cache_token": "baseline:holding_exit_matrix_v1:mid:active:midday",
        },
        "lifecycle_ai": {
            "cache_token": "lifecycle_ai_context:v1:entry:abcdef123456",
        },
    }

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "stock_code": "005930",
            "runtime_context": runtime_context,
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-runtime-cache-identifiers",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    row = _rows(trace._payload_path(trace._date_text()))[0]
    assert fields["ai_input_payload_redacted"] is False
    assert fields["ai_input_payload_replay_exact"] is True
    assert row["sanitized_user_input"]["runtime_context"] == runtime_context


def test_payload_sanitizer_preserves_approved_tokens_inside_exact_payload_wrapper(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    runtime_context = {
        "holding_exit_matrix": {
            "cache_token": "baseline:holding_exit_matrix_v1:mid:active:midday",
        },
        "lifecycle_ai": {
            "cache_token": "lifecycle_ai_context:v1:entry:abcdef123456",
        },
    }

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "exact_payload": {
                "stock_code": "005930",
                "runtime_context": runtime_context,
            },
            "exact_payload_analysis_v1": {"schema": "exact_payload_analysis_v1"},
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-wrapped-runtime-cache-identifiers",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    row = _rows(trace._payload_path(trace._date_text()))[0]
    assert fields["ai_input_payload_redacted"] is False
    assert fields["ai_input_payload_replay_exact"] is True
    assert (
        row["sanitized_user_input"]["exact_payload"]["runtime_context"]
        == runtime_context
    )


def test_payload_sanitizer_keeps_cache_token_sensitive_outside_approved_paths(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={
            "stock_code": "005930",
            "cache_token": "root-secret",
            "runtime_context": {
                "other_component": {"cache_token": "other-secret"},
                "entry-adm": {"cache_token": "entry_adm:v1:valid-looking"},
                "entry_adm": {
                    "cache_token": "entry_adm:access_token=provider-secret",
                    "access_token": "provider-secret",
                },
            },
            "exact_payload": {
                "runtime_context": {
                    "other_component": {"cache_token": "wrapped-other-secret"}
                }
            },
        },
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-unapproved-cache-token",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    row = _rows(trace._payload_path(trace._date_text()))[0]
    sanitized = row["sanitized_user_input"]
    assert fields["ai_input_payload_redacted"] is True
    assert fields["ai_input_payload_replay_exact"] is False
    assert sanitized["cache_token"] == "[REDACTED]"
    assert (
        sanitized["runtime_context"]["other_component"]["cache_token"] == "[REDACTED]"
    )
    assert sanitized["runtime_context"]["entry_adm"]["access_token"] == "[REDACTED]"
    assert sanitized["runtime_context"]["entry_adm"]["cache_token"] == "[REDACTED]"
    assert sanitized["runtime_context"]["entry-adm"]["cache_token"] == "[REDACTED]"
    assert (
        sanitized["exact_payload"]["runtime_context"]["other_component"]["cache_token"]
        == "[REDACTED]"
    )


def test_request_ledger_is_not_written_when_payload_store_fails(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    original_append = trace._append_jsonl

    def fail_payload(path, payload):
        if path == trace._payload_path(trace._date_text()):
            raise OSError("payload store unavailable")
        return original_append(path, payload)

    monkeypatch.setattr(trace, "_append_jsonl", fail_payload)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={"stock_code": "005930"},
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="request-must-not-orphan",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    assert fields == {}
    assert not trace._request_path(trace._date_text()).exists()


def test_trace_storage_uses_private_directory_and_file_modes(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={"stock_code": "005930", "current_price": 70_000},
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="private-mode-request",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )
    trace.record_ai_decision_trace(
        {
            **fields,
            "action": "WAIT",
            "provider_called": True,
            "provider": "openai",
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )

    paths = (
        trace._payload_path(trace._date_text()),
        trace._request_path(trace._date_text()),
        trace._prompt_path(trace._date_text()),
        trace._trace_path(trace._date_text()),
        trace._outcome_path(trace._date_text()),
    )
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in paths)
    assert all(stat.S_IMODE(path.parent.stat().st_mode) == 0o700 for path in paths)


def test_trace_storage_refuses_payload_file_symlink(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    payload_path = trace._payload_path(trace._date_text())
    payload_path.parent.mkdir(parents=True)
    target = tmp_path / "outside-target.jsonl"
    target.write_text("sentinel\n", encoding="utf-8")
    payload_path.symlink_to(target)

    fields = trace.capture_ai_request(
        prompt="prompt",
        user_input={"stock_code": "005930"},
        endpoint_name="analyze_target",
        symbol="005930",
        request_id="symlink-request",
        model="gpt-test",
        schema_name="entry_v1",
        require_json=True,
    )

    assert fields == {}
    assert target.read_text(encoding="utf-8") == "sentinel\n"
    assert not trace._request_path(trace._date_text()).exists()


def test_record_decision_creates_pending_outcome_idempotently(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    result = {
        "ai_decision_trace_id": "request-1",
        "action": "WAIT",
        "score": 62,
        "reason": "Mixed continuation evidence",
        "provider_called": True,
        "ai_model": "gpt-test",
        "openai_response_id": "resp-trace-1",
        "openai_input_tokens": 100,
        "openai_output_tokens": 20,
        "openai_total_tokens": 120,
        "ai_parse_ok": True,
        "ai_input_payload_sha256": "a" * 64,
        "ai_input_payload_replay_exact": True,
        "ai_trace_stock_code": "005930",
        "ai_trace_effective_venue": "KRX",
        "ai_trace_session_bucket": "KRX_REGULAR",
        "ai_trace_reference_price": 70100,
        "ai_input_preflight_status": "fresh_consistent",
        "ai_input_preflight_quality_warnings": ["broker_snapshot_stale_advisory"],
        "ai_input_runtime_preflight_mode": "exact_v2",
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
    assert trace_rows[0]["provider_response_id"] == "resp-trace-1"
    assert trace_rows[0]["input_tokens"] == 100
    assert trace_rows[0]["output_tokens"] == 20
    assert trace_rows[0]["total_tokens"] == 120
    assert trace_rows[0]["input_preflight_mode"] == "exact_v2"
    assert trace_rows[0]["input_quality_warnings"] == ["broker_snapshot_stale_advisory"]
    assert len(trace_rows[0]["response_sha256"]) == 64
    assert trace_rows[0]["provider_decision_origin"] == "openai"
    assert trace_rows[0]["payload_replay_exact"] is True
    assert trace_rows[0]["request_capture_status"] == "partial"
    assert trace_rows[0]["decision_result_sha256"]
    assert trace_rows[0]["runtime_effect"] is False
    assert len(outcome_rows) == 1
    assert outcome_rows[0]["label_status"] == "pending"
    assert outcome_rows[0]["decision_ts"] == trace_rows[0]["decision_ts"]
    assert outcome_rows[0]["action"] == "WAIT"
    assert outcome_rows[0]["pending_horizons_min"] == [1, 3, 5, 10, 20, 30, 60]
    assert outcome_rows[0]["input_preflight_mode"] == "exact_v2"
    assert outcome_rows[0]["input_preflight_status"] == "fresh_consistent"
    assert outcome_rows[0]["input_quality_warnings"] == [
        "broker_snapshot_stale_advisory"
    ]
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
    assert row["request_capture_status"] == "missing"
    assert row["actual_order_authority"] is False
    assert row["broker_order_forbidden"] is True
    assert row["venue_consistent"] is None
    assert row["outcome_label_eligible"] is False
    assert row["outcome_label_exclusion_reasons"] == [
        "input_preflight_blocked",
        "input_preflight_not_allowed",
        "provider_not_called",
    ]
    assert fields["ai_decision_outcome_label_status"] == (
        "not_applicable_input_preflight_blocked"
    )
    assert fields["ai_decision_outcome_label_exclusion_reasons"] == [
        "input_preflight_blocked",
        "input_preflight_not_allowed",
        "provider_not_called",
    ]
    assert not trace._outcome_path(trace._date_text()).exists()


def test_no_provider_holding_trace_uses_canonical_logical_endpoint(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "HOLD",
            "provider_called": False,
            "ai_trace_endpoint_name": "holding_score",
            "ai_trace_stock_code": "005930",
            "ai_input_preflight_status": "blocked",
            "ai_input_preflight_allowed": False,
        },
        prompt_type="scalping_holding_score",
        prompt_version="holding_score_v2",
        result_source="input_preflight_blocked",
        provider_called=False,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["endpoint"] == "holding_score"
    assert row["prompt_type"] == "scalping_holding_score"
    assert row["provider_called"] is False
    assert row["provider_actual"] is None


def test_holding_trace_preserves_model_decision_before_source_quality_override(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "HOLD",
            "score": 50,
            "confidence": 0,
            "reason": (
                "holding_context_source_quality_unusable_defer_to_deterministic_guards"
            ),
            "holding_score_model_action": "EXIT",
            "holding_score_model_score": 23,
            "holding_score_model_confidence": 81,
            "holding_score_model_reason": "support failed",
            "holding_score_model_data_quality": "fresh",
            "holding_score_effective_action": "HOLD",
            "holding_score_source_quality_override_applied": True,
            "holding_score_source_quality_override_reason": (
                "holding_context_source_quality_unusable_defer_to_deterministic_guards"
            ),
            "holding_score_source_quality_override_blockers": [
                "microstructure_missing_or_stale"
            ],
            "provider_called": True,
            "provider": "openai",
            "ai_parse_ok": True,
        },
        prompt_type="scalping_holding_score",
        prompt_version="holding_score_v2",
        result_source="live",
        stock_code="005930",
        provider_called=True,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["action"] == "HOLD"
    assert row["score"] == 50
    assert row["holding_score_model_action"] == "EXIT"
    assert row["holding_score_model_score"] == 23
    assert row["holding_score_model_confidence"] == 81
    assert row["holding_score_model_reason"] == "support failed"
    assert row["holding_score_model_data_quality"] == "fresh"
    assert row["holding_score_effective_action"] == "HOLD"
    assert row["holding_score_source_quality_override_applied"] is True
    assert row["holding_score_source_quality_override_blockers"] == [
        "microstructure_missing_or_stale"
    ]
    outcome = _rows(trace._outcome_path(trace._date_text()))[0]
    assert outcome["holding_score_model_action"] == "EXIT"
    assert outcome["holding_score_model_score"] == 23
    assert outcome["holding_score_effective_action"] == "HOLD"
    assert outcome["holding_score_source_quality_override_applied"] is True


def test_string_false_preflight_contract_cannot_create_outcome_label(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
        {
            "action": "EXIT",
            "provider_called": False,
            "ai_market_snapshot_stock_code": "005930",
            "ai_input_preflight_status": "partial",
            "ai_input_preflight_allowed": "False",
        },
        prompt_type="holding_exit_flow",
        prompt_version="flow_v1",
        result_source="input_preflight_blocked",
        provider_called=False,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["input_preflight_allowed"] is False
    assert row["outcome_label_eligible"] is False
    assert row["outcome_label_exclusion_reasons"] == [
        "input_preflight_blocked",
        "input_preflight_not_allowed",
        "provider_not_called",
    ]
    assert fields["ai_decision_outcome_label_status"] == (
        "not_applicable_input_preflight_blocked"
    )
    assert not trace._outcome_path(trace._date_text()).exists()


def test_final_trace_redacts_provider_echoed_credentials(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "ai_decision_trace_id": "provider-secret-echo",
            "action": "WAIT",
            "reason": "provider error Authorization: Bearer echoed-secret",
            "provider_called": True,
            "provider": "openai",
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    serialized = json.dumps(row, ensure_ascii=False)
    assert "echoed-secret" not in serialized
    assert row["reason"] == "provider error Authorization: [REDACTED]"
    assert row["trace_storage_redacted"] is True


def test_rejected_physical_attempt_has_trace_without_outcome_label(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
        {
            "ai_decision_trace_id": "rejected-attempt-1",
            "action": "WAIT",
            "provider_called": True,
            "provider": "openai",
            "ai_decision_outcome_eligible": False,
            "forensic_attempt": 1,
            "forensic_attempt_final": False,
            "forensic_semantic_errors": ["reason_non_ascii"],
        },
        prompt_type="scalping_entry",
        prompt_version="entry_context_intraday_probe_forensics_v1",
        result_source="schema_semantic_rejected_retry",
        provider_called=True,
    )

    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    assert trace_row["outcome_label_eligible"] is False
    assert trace_row["outcome_label_exclusion_reasons"] == [
        "explicit_ai_decision_outcome_ineligible"
    ]
    assert trace_row["attempt"] == 1
    assert trace_row["attempt_final"] is False
    assert trace_row["semantic_errors"] == ["reason_non_ascii"]
    assert fields["ai_decision_outcome_label_status"] == (
        "not_applicable_rejected_attempt"
    )
    assert not trace._outcome_path(trace._date_text()).exists()


def test_entry_price_semantic_reject_preserves_physical_provider_and_errors(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
        {
            "ai_decision_trace_id": "entry-price-rejected-1",
            "action": "USE_DEFENSIVE",
            "provider_called": True,
            "provider": "bedrock",
            "provider_response_id": "bedrock-response-1",
            "ai_decision_outcome_eligible": False,
            "forensic_semantic_errors": ["selected_price_not_in_candidate_set"],
            "decision_quality_contract_status": "semantic_rejected",
            "decision_quality_contract_errors": ["selected_price_not_in_candidate_set"],
            "entry_price_v2_5_contract_status": "rejected",
            "entry_price_v2_5_contract_errors": ["selected_price_not_in_candidate_set"],
            "ai_trace_stock_code": "005930",
        },
        prompt_type="entry_price",
        prompt_version="decision_quality_entry_price_v2_5_live_krx_v1",
        result_source="schema_semantic_rejected",
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["provider_called"] is True
    assert row["provider_actual"] == "bedrock"
    assert row["provider_response_id"] == "bedrock-response-1"
    assert row["semantic_errors"] == ["selected_price_not_in_candidate_set"]
    assert row["entry_price_v2_5_contract_status"] == "rejected"
    assert row["entry_price_v2_5_contract_errors"] == [
        "selected_price_not_in_candidate_set"
    ]
    assert row["decision_quality_contract_status"] == "semantic_rejected"
    assert row["decision_quality_contract_errors"] == [
        "selected_price_not_in_candidate_set"
    ]
    assert row["outcome_label_eligible"] is False
    assert row["outcome_label_exclusion_reasons"] == [
        "explicit_ai_decision_outcome_ineligible"
    ]
    assert fields["ai_decision_outcome_label_status"] == (
        "not_applicable_rejected_attempt"
    )
    assert not trace._outcome_path(trace._date_text()).exists()


def test_decision_quality_contract_rejection_is_preserved_in_trace(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "ai_decision_trace_id": "decision-quality-rejected-1",
            "action": "DROP",
            "score": 0,
            "provider_called": True,
            "provider": "openai",
            "decision_quality_contract_status": "semantic_rejected",
            "decision_quality_contract_errors": [
                "entry_structural_edge_floor_misclassified",
            ],
            "decision_quality_model_action": "WAIT",
            "decision_quality_model_edge_state": "NO_EDGE",
            "decision_quality_model_expected_upside_pct": 0.4,
            "decision_quality_model_expected_downside_pct": -0.8,
            "decision_quality_model_evidence": {
                "liquidity": "adverse",
                "trigger": "recovery_required",
            },
            "openai_response_schema_registry_used": True,
            "openai_response_schema_mode": "strict_dynamic_entry_risk",
            "openai_response_schema_sha256": "schema-sha256",
            "openai_response_schema_application": "provider_enforced_openai",
            "expected_semantic_validator_version": "entry_expected_v1",
            "semantic_validator_version": "entry_applied_v1",
            "semantic_validator_applied": True,
            "semantic_validation_status": "rejected",
            "entry_price_v1_contract_status": "semantic_rejected",
            "entry_price_v1_contract_errors": [
                "entry_price_v1_confidence_type_invalid"
            ],
            "openai_entry_risk_dynamic_fact_schema_applied": True,
            "entry_ai_raw_risk_verdict": "CAUTION",
            "entry_ai_raw_risk_codes": ["CONFIRMATION_MISSING"],
            "entry_ai_raw_confidence": 0.74,
            "entry_ai_raw_supporting_fact_ids": ["invented_positive_fact"],
            "entry_ai_raw_contradicting_fact_ids": ["trigger_confirmation_missing"],
            "entry_ai_invalid_supporting_fact_ids": ["invented_positive_fact"],
            "entry_ai_invalid_contradicting_fact_ids": [],
            "entry_ai_rejected_unexpected_fields": ["action"],
        },
        prompt_type="scalping_entry",
        prompt_version="decision_quality_v2_7",
        result_source="live",
        provider_called=True,
    )

    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    assert trace_row["decision_quality_contract_status"] == "semantic_rejected"
    assert trace_row["decision_quality_contract_errors"] == [
        "entry_structural_edge_floor_misclassified"
    ]
    assert trace_row["decision_quality_model_action"] == "WAIT"
    assert trace_row["decision_quality_model_edge_state"] == "NO_EDGE"
    assert trace_row["decision_quality_model_expected_upside_pct"] == 0.4
    assert trace_row["decision_quality_model_expected_downside_pct"] == -0.8
    assert trace_row["decision_quality_model_evidence"] == {
        "liquidity": "adverse",
        "trigger": "recovery_required",
    }
    assert trace_row["openai_response_schema_registry_used"] is True
    assert trace_row["openai_response_schema_mode"] == "strict_dynamic_entry_risk"
    assert trace_row["response_schema_sha256"] == "schema-sha256"
    assert trace_row["response_schema_application"] == "provider_enforced_openai"
    assert trace_row["expected_semantic_validator_version"] == "entry_expected_v1"
    assert trace_row["semantic_validator_version"] == "entry_applied_v1"
    assert trace_row["semantic_validator_applied"] is True
    assert trace_row["semantic_validation_status"] == "rejected"
    assert trace_row["entry_price_v1_contract_status"] == "semantic_rejected"
    assert trace_row["entry_price_v1_contract_errors"] == [
        "entry_price_v1_confidence_type_invalid"
    ]
    assert trace_row["openai_entry_risk_dynamic_fact_schema_applied"] is True
    assert trace_row["entry_ai_raw_risk_verdict"] == "CAUTION"
    assert trace_row["entry_ai_raw_risk_codes"] == ["CONFIRMATION_MISSING"]
    assert trace_row["entry_ai_raw_confidence"] == 0.74
    assert trace_row["entry_ai_raw_supporting_fact_ids"] == ["invented_positive_fact"]
    assert trace_row["entry_ai_raw_contradicting_fact_ids"] == [
        "trigger_confirmation_missing"
    ]
    assert trace_row["entry_ai_invalid_supporting_fact_ids"] == [
        "invented_positive_fact"
    ]
    assert trace_row["entry_ai_invalid_contradicting_fact_ids"] == []
    assert trace_row["entry_ai_rejected_unexpected_fields"] == ["action"]


def test_entry_probe_intent_is_preserved_in_trace_and_pending_label(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "ai_decision_trace_id": "entry-probe-intent-1",
            "action": "WAIT",
            "score": 65,
            "provider_called": True,
            "provider": "openai",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "entry_probe_intent_prompt_version": "decision_quality_v2_7_probe_v1",
            "entry_probe_intent_eligibility_path": ("v2_13_clean_continuation_wait"),
            "entry_probe_intent_after_cost_reward_risk": 0.875,
            "entry_probe_intent_rollback_condition": (
                "disable_wait_probe_owner_or_restore_model_buy_only_mapping"
            ),
            "entry_probe_intent_authority": (
                "candidate_only_existing_submit_guard_required"
            ),
            "entry_probe_intent_submit_guard_required": True,
            "entry_probe_intent_actual_order_submitted": False,
            "entry_setup_family": "CLEAN_CONTINUATION",
            "entry_setup_state": "READY",
            "entry_structure_phase": "continuation",
            "entry_structure_phase_policy_version": (
                "entry_completed_bar_structure_phase_v2"
            ),
            "entry_structure_phase_sha256": "phase-sha",
            "entry_structure_phase_bar_end": "2026-08-07T09:10:00+09:00",
            "entry_execution_readiness_state": "READY",
            "entry_ai_risk_verdict": "PASS",
            "entry_ai_risk_codes": ["NO_BLOCKING_RISK"],
            "entry_ai_veto_corroborated": False,
            "entry_setup_live_policy_status": "active_bounded_krx_canary",
            "entry_setup_live_policy_mode": "one_share_exploration",
            "entry_setup_live_policy_max_daily_exploration_probes": 3,
            "entry_setup_live_policy_source_date": "2026-08-06",
            "entry_setup_live_policy_target_date": "2026-08-07",
            "entry_setup_live_policy_activation_sha256": "activation-sha",
            "entry_setup_live_policy_candidate_contract_sha256": "candidate-sha",
            "entry_setup_live_policy_runtime_effect": True,
            "main_ai_quality_live_policy_status": (
                "active_exact_bound_prompt_contract"
            ),
            "main_ai_quality_live_policy_target_date": "2026-08-07",
            "main_ai_quality_live_policy_candidate_id": "candidate-exact-1",
            "main_ai_quality_live_policy_candidate_sha256": "a" * 64,
            "main_ai_quality_live_policy_activation_sha256": "b" * 64,
            "main_ai_quality_live_policy_runtime_effect": True,
            "entry_probe_first_required": True,
            "entry_ai_full_entry_forbidden": True,
            "entry_recent_exit_context_status": "active",
            "entry_recent_exit_probe_blocked": True,
            "entry_recent_exit_price_vs_exit_pct": 0.273723,
        },
        prompt_type="scalping_entry",
        prompt_version="decision_quality_v2_7_probe_v1",
        result_source="live",
        provider_called=True,
    )

    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    pending_row = _rows(trace._outcome_path(trace._date_text()))[0]
    assert trace_row["entry_probe_intent"] is True
    assert trace_row["entry_probe_intent_status"] == "eligible_wait_probe"
    assert trace_row["entry_probe_intent_submit_guard_required"] is True
    assert trace_row["entry_probe_intent_actual_order_submitted"] is False
    assert (
        trace_row["entry_probe_intent_eligibility_path"]
        == "v2_13_clean_continuation_wait"
    )
    assert trace_row["entry_probe_intent_after_cost_reward_risk"] == 0.875
    assert pending_row["entry_probe_intent_eligibility_path"] == (
        "v2_13_clean_continuation_wait"
    )
    assert pending_row["entry_probe_intent_after_cost_reward_risk"] == 0.875
    assert trace_row["entry_recent_exit_context_status"] == "active"
    assert trace_row["entry_recent_exit_probe_blocked"] is True
    assert trace_row["entry_recent_exit_price_vs_exit_pct"] == 0.273723
    assert pending_row["entry_probe_intent"] is True
    assert pending_row["entry_probe_intent_status"] == "eligible_wait_probe"
    assert pending_row["entry_probe_intent_actual_order_submitted"] is False
    assert trace_row["entry_setup_family"] == "CLEAN_CONTINUATION"
    assert trace_row["entry_setup_state"] == "READY"
    assert trace_row["entry_structure_phase"] == "continuation"
    assert pending_row["entry_structure_phase"] == "continuation"
    assert trace_row["entry_execution_readiness_state"] == "READY"
    assert trace_row["entry_ai_risk_verdict"] == "PASS"
    assert trace_row["entry_ai_risk_codes"] == ["NO_BLOCKING_RISK"]
    assert trace_row["entry_setup_live_policy_status"] == ("active_bounded_krx_canary")
    assert trace_row["entry_setup_live_policy_runtime_effect"] is True
    assert trace_row["entry_setup_live_policy_mode"] == "one_share_exploration"
    assert pending_row["entry_setup_live_policy_max_daily_exploration_probes"] == 3
    assert pending_row["entry_setup_live_policy_source_date"] == "2026-08-06"
    assert pending_row["entry_setup_live_policy_target_date"] == "2026-08-07"
    assert trace_row["main_ai_quality_live_policy_status"] == (
        "active_exact_bound_prompt_contract"
    )
    assert trace_row["main_ai_quality_live_policy_candidate_id"] == (
        "candidate-exact-1"
    )
    assert pending_row["main_ai_quality_live_policy_target_date"] == "2026-08-07"
    assert pending_row["main_ai_quality_live_policy_activation_sha256"] == "b" * 64
    assert pending_row["main_ai_quality_live_policy_runtime_effect"] is True
    assert pending_row["entry_probe_first_required"] is True
    assert pending_row["entry_ai_full_entry_forbidden"] is True
    assert pending_row["entry_recent_exit_context_status"] == "active"
    assert pending_row["entry_recent_exit_probe_blocked"] is True
    assert pending_row["entry_recent_exit_price_vs_exit_pct"] == 0.273723


def test_decision_quality_non_buy_repair_provenance_is_preserved_in_trace(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "ai_decision_trace_id": "decision-quality-repaired-1",
            "action": "DROP",
            "score": 11,
            "provider_called": True,
            "provider": "openai",
            "decision_quality_contract_status": "pass",
            "decision_quality_live_adapter": "decision_quality_v2_7_entry_v2",
            "decision_quality_contract_errors": [],
            "decision_quality_model_reason_codes": [
                "edge_absent",
                "trigger=insufficient_tape_confirmation",
            ],
            "decision_quality_contract_repair_applied": True,
            "decision_quality_contract_repair_codes": [
                "non_buy_invalid_reason_codes_removed"
            ],
            "decision_quality_contract_original_errors": ["reason_codes_invalid"],
            "decision_quality_contract_invalid_reason_codes": [
                "trigger=insufficient_tape_confirmation"
            ],
        },
        prompt_type="scalping_entry",
        prompt_version="decision_quality_v2_7",
        result_source="live",
        provider_called=True,
    )

    trace_row = _rows(trace._trace_path(trace._date_text()))[0]
    assert trace_row["decision_quality_contract_status"] == "pass"
    assert trace_row["decision_quality_live_adapter"] == (
        "decision_quality_v2_7_entry_v2"
    )
    assert trace_row["decision_quality_model_reason_codes"] == [
        "edge_absent",
        "trigger=insufficient_tape_confirmation",
    ]
    assert trace_row["decision_quality_contract_repair_applied"] is True
    assert trace_row["decision_quality_contract_repair_codes"] == [
        "non_buy_invalid_reason_codes_removed"
    ]
    assert trace_row["decision_quality_contract_original_errors"] == [
        "reason_codes_invalid"
    ]
    assert trace_row["decision_quality_contract_invalid_reason_codes"] == [
        "trigger=insufficient_tape_confirmation"
    ]


def test_pending_outcome_is_recovered_without_duplicate_trace_after_write_failure(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)
    original_append = trace._append_jsonl
    failed_once = False

    def fail_first_outcome(path, payload):
        nonlocal failed_once
        if path == trace._outcome_path(trace._date_text()) and not failed_once:
            failed_once = True
            raise OSError("outcome store unavailable")
        return original_append(path, payload)

    monkeypatch.setattr(trace, "_append_jsonl", fail_first_outcome)
    result = {
        "ai_decision_trace_id": "recover-outcome-1",
        "action": "WAIT",
        "confidence": 84,
        "reason_codes": ["mixed_tape"],
        "provider_called": True,
        "provider": "openai",
    }
    first = trace.record_ai_decision_trace(
        result,
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )
    second = trace.record_ai_decision_trace(
        result,
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="live",
    )

    assert first == {}
    assert second["ai_decision_outcome_label_status"] == "pending"
    assert len(_rows(trace._trace_path(trace._date_text()))) == 1
    outcomes = _rows(trace._outcome_path(trace._date_text()))
    assert len(outcomes) == 1
    assert outcomes[0]["confidence"] == 84
    assert outcomes[0]["reason_codes"] == ["mixed_tape"]


def test_cache_trace_separates_provider_call_from_decision_origin(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
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
    assert row["outcome_label_eligible"] is False
    assert row["outcome_label_exclusion_reasons"] == ["provider_not_called"]
    assert fields["ai_decision_outcome_label_status"] == (
        "not_applicable_provider_not_called"
    )
    assert not trace._outcome_path(trace._date_text()).exists()


def test_string_false_provider_flag_cannot_create_outcome_label(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)

    fields = trace.record_ai_decision_trace(
        {
            "action": "WAIT",
            "provider_called": "False",
            "cache_hit": True,
            "ai_trace_stock_code": "005930",
        },
        prompt_type="scalping_entry",
        prompt_version="entry_v1",
        result_source="cache",
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["provider_called"] is False
    assert row["outcome_label_eligible"] is False
    assert fields["ai_decision_outcome_label_status"] == (
        "not_applicable_provider_not_called"
    )
    assert not trace._outcome_path(trace._date_text()).exists()


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


def test_entry_price_bedrock_failback_records_bedrock_actual_model(
    monkeypatch, tmp_path
):
    _enable(monkeypatch, tmp_path)

    trace.record_ai_decision_trace(
        {
            "action": "USE_AI",
            "openai_model": "gpt-requested",
            "openai_transport_mode": "bedrock_primary",
            "bedrock_primary_used": False,
            "bedrock_failback_used": True,
            "bedrock_model_family": "lite_v2",
            "bedrock_primary_family": "qwen3_32b",
            "bedrock_failback_family": "lite_v2",
            "ai_trace_stock_code": "005930",
        },
        prompt_type="entry_price",
        prompt_version="entry_price_v1",
        result_source="live",
        provider_called=True,
    )

    row = _rows(trace._trace_path(trace._date_text()))[0]
    assert row["provider_actual"] == "bedrock"
    assert row["provider_decision_origin"] == "bedrock"
    assert row["model_requested"] == "gpt-requested"
    assert row["model"] == "lite_v2"


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
