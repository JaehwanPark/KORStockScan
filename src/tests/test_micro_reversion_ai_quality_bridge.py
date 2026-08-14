from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json

import pytest

from src.engine.scalping.micro_reversion.ai_quality_bridge import (
    AUTHORITY_CONTRACT,
    LIFECYCLE_PROJECTION_SCHEMA,
    TACTICAL_EVIDENCE_SCHEMA,
    BridgeConfig,
    _relevant_windows,
    attach_micro_context_to_replay_request,
    build_bridge_report,
    build_future_outcome,
    build_tactical_evidence,
    build_three_arm_manifest,
    resolve_micro_scope,
)


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp() * 1_000)


def _replay_context(captured_at: str) -> dict:
    return {
        "input_schema": "decision_quality_v2_14_entry",
        "exact_payload": {
            "schema": "entry_payload_v1",
            "requested_qty": 50,
            "position_sizing_allocator": {"effective_qty": 50},
            "entry_candle_context": {
                "schema": "entry_candle_context_v1",
                "input_bundle_version": "scalping_multi_timeframe_context_v1",
                "venue": "KRX",
                "session": "KRX_REGULAR",
                "bars": [{"minute": "09:00", "forming": False}],
            },
            "ai_market_snapshot": {
                "schema": "ai_market_snapshot_v1",
                "snapshot_id": "snapshot-1",
                "captured_at": captured_at,
                "stock_code": "000001",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "market_data_route": "krx_only",
                "broker_route": "KRX",
            },
        },
        "exact_payload_analysis_v1": {"schema": "exact_payload_analysis_v1"},
    }


def _producer_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _request_envelope_hash(
    *, payload_sha256: str, replay_context_sha256: str
) -> str:
    return _producer_hash(
        {
            "endpoint": "analyze_target",
            "model": "gpt-5.4-nano",
            "schema_name": "entry_decision_v2",
            "require_json": True,
            "temperature": 0.1,
            "max_output_tokens": 900,
            "reasoning_effort": "low",
            "prompt_sha256": "prompt-hash",
            "user_input_sha256": payload_sha256,
            "replay_context_sha256": replay_context_sha256,
        }
    )


def _trace(
    *,
    trace_id: str = "trace-1",
    request_id: str = "request-1",
    payload_sha256: str = "provider-payload-hash",
    request_envelope_sha256: str | None = None,
    captured_at: str = "2026-08-14T09:00:10.000+09:00",
) -> dict:
    replay_context_sha256 = _producer_hash(_replay_context(captured_at))
    request_envelope_sha256 = request_envelope_sha256 or _request_envelope_hash(
        payload_sha256=payload_sha256,
        replay_context_sha256=replay_context_sha256,
    )
    return {
        "schema": "ai_decision_trace_v1",
        "decision_trace_id": trace_id,
        "request_id": request_id,
        "decision_ts": "2026-08-14T09:00:11.000+09:00",
        "decision_stage": "entry_screen",
        "endpoint": "analyze_target",
        "stock_code": "000001",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "market_data_route": "krx_only",
        "broker_route": "KRX",
        "provider_actual": "openai",
        "provider_called": True,
        "timeout": False,
        "parse_ok": True,
        "result_source": "live",
        "decision_evaluation_status": "evaluated",
        "semantic_errors": [],
        "action": "WAIT",
        "decision_quality_contract_status": "pass",
        "prompt_version": "decision_quality_v2_14",
        "prompt_sha256": "prompt-hash",
        "model": "gpt-5.4-nano",
        "model_requested": "gpt-5.4-nano",
        "transport": "responses_http",
        "response_sha256": "response-hash",
        "provider_response_id": "resp-test",
        "openai_response_schema_mode": "strict_dynamic_entry_risk",
        "payload_sha256": payload_sha256,
        "request_envelope_sha256": request_envelope_sha256,
        "request_capture_status": "captured",
        "replay_context_present": True,
        "replay_context_exact": True,
        "replay_context_sha256": replay_context_sha256,
        "payload_replay_exact": True,
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "canonical_context_capture_status": "exact_completed_bars_captured",
        "snapshot_id": "snapshot-1",
    }


def _payload(
    *,
    request_id: str = "request-1",
    payload_sha256: str = "provider-payload-hash",
    request_envelope_sha256: str | None = None,
    captured_at: str = "2026-08-14T09:00:10.000+09:00",
) -> dict:
    replay_context = _replay_context(captured_at)
    replay_context_sha256 = _producer_hash(replay_context)
    request_envelope_sha256 = request_envelope_sha256 or _request_envelope_hash(
        payload_sha256=payload_sha256,
        replay_context_sha256=replay_context_sha256,
    )
    return {
        "schema": "ai_decision_payload_v1",
        "request_id": request_id,
        "payload_sha256": payload_sha256,
        "request_envelope_sha256": request_envelope_sha256,
        "endpoint": "analyze_target",
        "model": "gpt-5.4-nano",
        "schema_name": "entry_decision_v2",
        "require_json": True,
        "temperature": 0.1,
        "max_output_tokens": 900,
        "reasoning_effort": "low",
        "prompt_sha256": "prompt-hash",
        "replay_exact": True,
        "replay_context_present": True,
        "replay_context_exact": True,
        "replay_context_sha256": replay_context_sha256,
        "replay_context_input_format": "structured",
        "symbol": "000001",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "market_data_route": "krx_only",
        "broker_route": "KRX",
        "snapshot_id": "snapshot-1",
        "canonical_context_capture": {
            "status": "exact_completed_bars_captured",
            "schema": "entry_candle_context_v1",
            "input_bundle_version": "scalping_multi_timeframe_context_v1",
            "raw_bar_count": 1,
            "completed_bar_count": 1,
        },
        "sanitized_replay_context": replay_context,
    }


def _market(
    timestamp: str,
    *,
    price: float,
    side: str,
    qty: int,
    sequence: int,
    epoch: int = 123,
    venue: str = "KRX",
    session: str = "KRX_REGULAR",
    bid: float | None = None,
    ask: float | None = None,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_stream_point_v3",
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v3",
        "realtime_type": "0B",
        "item": "000001",
        "symbol": "000001",
        "venue": venue,
        "session_bucket": session,
        "sequence_epoch": epoch,
        "source_sequence": sequence,
        "series_sequence": sequence,
        "exchange_timestamp": timestamp,
        "local_receive_timestamp": timestamp,
        "trade_price": price,
        "trade_qty": qty,
        "best_bid": bid if bid is not None else price - 10,
        "best_ask": ask if ask is not None else price,
        "quote_age_ms": 0.0,
        "aggressor_side": side,
        "path_order_status": "accept",
        "path_consumer_eligible": True,
        "exchange_timestamp_regression_ms": 0,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }


def _depth(
    timestamp: str = "2026-08-14T09:00:09.700+09:00",
    *,
    epoch: int = 123,
    sequence: int = 1,
    bid: float = 9_950.0,
    ask: float = 9_960.0,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_depth_point_v1",
        "metric_contract_id": "scalp_micro_reversion_market_depth_contract_v1",
        "realtime_type": "0D",
        "item": "000001",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": epoch,
        "source_sequence": sequence,
        "series_sequence": sequence,
        "exchange_timestamp": timestamp,
        "local_receive_timestamp": timestamp,
        "best_bid": bid,
        "best_ask": ask,
        "best_bid_qty": 100,
        "best_ask_qty": 100,
        "bid_depth": 1_000,
        "ask_depth": 1_000,
        "route_depth_totals": {
            "KRX": {"bid": 1_000, "ask": 1_000},
            "NXT": {"bid": 0, "ask": 0},
            "combined": {"bid": 1_000, "ask": 1_000},
        },
        "bid_levels": [[1, bid, 100], [2, bid - 10.0, 900]],
        "ask_levels": [[1, ask, 100], [2, ask + 10.0, 900]],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }


def _reference(*, epoch: int = 123, parent_wave: str = "wave-1") -> dict:
    return {
        "schema": "scalp_micro_reversion_path_event_reference_v2",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": epoch,
        "parent_wave_id": parent_wave,
        "path_segment_id": "segment-1",
        "shock_event_id": "shock-1",
        "shock_horizon_ms": 1_000,
        "event_sequence_in_wave": 1,
        "event_detected_at_ms": _ms("2026-08-14T09:00:06.000+09:00"),
        "segment_event_detected_at_ms": _ms("2026-08-14T09:00:06.000+09:00"),
        "capture_started_at": "2026-08-14T09:00:05.000+09:00",
        "capture_ended_at": "2026-08-14T09:03:06.000+09:00",
        "decision_authority": "forward_path_observation_only_no_policy_selection",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }


def _past_market_rows() -> list[dict]:
    return [
        _market(
            "2026-08-14T09:00:05.000+09:00",
            price=10_000,
            side="BUY",
            qty=20,
            sequence=1,
        ),
        _market(
            "2026-08-14T09:00:06.000+09:00",
            price=9_900,
            side="SELL",
            qty=100,
            sequence=2,
        ),
        _market(
            "2026-08-14T09:00:07.000+09:00",
            price=9_880,
            side="SELL",
            qty=100,
            sequence=3,
        ),
        _market(
            "2026-08-14T09:00:09.800+09:00",
            price=9_960,
            side="BUY",
            qty=400,
            sequence=4,
            bid=9_950,
            ask=9_960,
        ),
    ]


def _verified_config() -> BridgeConfig:
    return BridgeConfig(
        statutory_sell_tax_bps=20.0,
        uncertainty_buffer_bps=3.0,
        cost_profile_source="verified_test_profile",
        cost_profile_verified=True,
    )


def _attach(request: dict, evidence: dict) -> dict:
    return attach_micro_context_to_replay_request(
        request,
        evidence,
        source_trace=_trace(),
        source_payload=_payload(),
        source_market_rows=_past_market_rows(),
        source_depth_rows=[_depth()],
        source_event_references=[_reference()],
        config=_verified_config(),
    )


def test_builds_past_only_context_and_liquidity_bounded_lifecycle() -> None:
    future_spike = _market(
        "2026-08-14T09:00:10.500+09:00",
        price=11_000,
        side="BUY",
        qty=10_000,
        sequence=5,
        bid=10_990,
        ask=11_000,
    )

    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=[*_past_market_rows(), future_spike],
        depth_rows=[_depth()],
        event_references=[_reference(), {**_reference(), "shock_event_id": "child"}],
        config=_verified_config(),
    )

    assert evidence["state"] == "reversion_confirmed"
    assert evidence["event"]["asof_trade_price"] == 9_960
    assert evidence["event"]["parent_wave_id"] == "wave-1"
    assert evidence["source_quality"]["parent_wave_reference_count"] == 1
    assert evidence["source_quality"]["future_outcome_fields_in_context"] is False
    assert evidence["decision_watermark"]["past_only_join"] is True
    assert evidence["liquidity_capacity"][
        "counterfactual_liquidity_qty_ceiling"
    ] == 5
    assert evidence["liquidity_capacity"]["existing_position_formula_candidate_qty"] == 50
    assert evidence["economics"]["spread_double_counted"] is False
    assert evidence["economics"]["minimum_gross_target_bps"] > 28.0
    lifecycle = evidence[LIFECYCLE_PROJECTION_SCHEMA]
    assert lifecycle["entry_projection"]["live_price_or_order_effect"] is False
    assert lifecycle["exit_projection"]["live_sell_or_cancel_effect"] is False
    for key, expected in AUTHORITY_CONTRACT.items():
        assert evidence[key] is expected
        assert lifecycle[key] is expected


def test_cross_epoch_depth_and_future_depth_are_not_joined() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[
            _depth(epoch=122),
            _depth(timestamp="2026-08-14T09:00:10.100+09:00", epoch=123),
        ],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["state"] == "reversion_confirmed"
    assert evidence["source_quality"]["status"] == "pass"
    assert evidence["source_quality"]["liquidity_capacity_status"] == "blocked"
    assert "same_epoch_past_depth_missing" in evidence["source_quality"][
        "liquidity_capacity_blockers"
    ]
    assert evidence["liquidity_capacity"][
        "counterfactual_liquidity_qty_ceiling"
    ] is None


def test_unknown_cost_keeps_net_target_null_without_blocking_price_context() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
    )

    assert evidence["source_quality"]["status"] == "pass"
    assert evidence["economics"]["all_in_cost_bps"] is None
    assert evidence["economics"]["minimum_gross_target_bps"] is None
    assert (
        evidence["economics"]["economic_source_quality_status"]
        == "cost_profile_unavailable_no_net_target"
    )


def test_future_outcome_is_separate_and_uses_executable_bid_after_cost() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    future = [
        _market(
            "2026-08-14T09:00:10.500+09:00",
            price=10_030,
            side="BUY",
            qty=100,
            sequence=5,
            bid=10_020,
            ask=10_030,
        ),
        _market(
            "2026-08-14T09:00:11.500+09:00",
            price=9_800,
            side="SELL",
            qty=100,
            sequence=6,
            bid=9_790,
            ask=9_800,
        ),
    ]

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=future,
        depth_rows=[
            _depth(
                "2026-08-14T09:00:10.500+09:00",
                sequence=2,
                bid=10_020.0,
                ask=10_030.0,
            ),
            _depth(
                "2026-08-14T09:00:11.500+09:00",
                sequence=3,
                bid=9_790.0,
                ask=9_800.0,
            ),
        ],
        config=_verified_config(),
    )

    assert outcome["label_role"] == "counterfactual_outcome_only_never_prompt_input"
    assert outcome["first_hit"] == "net_target_first"
    assert "future_outcome" not in evidence
    assert "horizons" not in evidence


def test_opt_in_replay_enrichment_preserves_exact_payload_and_three_arm_parity() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    exact_payload = deepcopy(_payload()["sanitized_replay_context"]["exact_payload"])
    candidate_input = {"exact_payload": exact_payload}
    request = {
        "decision_trace_id": "trace-1",
        "decision_authority": "offline_replay_no_runtime_change",
        "stage": "entry",
        "endpoint": "analyze_target",
        "stock_code": "000001",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "exact_payload": exact_payload,
        "source_exact_payload_sha256": evidence["source_exact_payload_sha256"],
        "payload_sha256": evidence["source_provider_payload_sha256"],
        "request_envelope_sha256": evidence["source_request_envelope_sha256"],
        "candidate_input": candidate_input,
        "candidate_input_sha256": _producer_hash(candidate_input),
        **AUTHORITY_CONTRACT,
    }
    original = deepcopy(request)

    enriched = _attach(request, evidence)
    manifest = build_three_arm_manifest(
        evidence=evidence, control_prompt_version="decision_quality_v2_14"
    )

    assert request == original
    assert enriched["exact_payload"] == exact_payload
    assert enriched["candidate_input"][TACTICAL_EVIDENCE_SCHEMA] == evidence
    assert manifest["replay_arms"][1]["analytical_context_pair_sha256"] == manifest[
        "replay_arms"
    ][2]["analytical_context_pair_sha256"]
    assert "tactical_micro_reversion_evidence_sha256" not in manifest[
        "replay_arms"
    ][0]
    assert manifest["provider_call_performed"] is False


def test_replay_enrichment_rejects_unregistered_candidate_ledger() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    exact_payload = deepcopy(_payload()["sanitized_replay_context"]["exact_payload"])
    request = {
        "decision_trace_id": "trace-1",
        "decision_authority": "offline_replay_no_runtime_change",
        "stage": "entry",
        "endpoint": "analyze_target",
        "stock_code": "000001",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "exact_payload": exact_payload,
        "source_exact_payload_sha256": evidence["source_exact_payload_sha256"],
        "payload_sha256": evidence["source_provider_payload_sha256"],
        "request_envelope_sha256": evidence["source_request_envelope_sha256"],
        "candidate_input": {"exact_payload": exact_payload, "other_ledger": {}},
        **AUTHORITY_CONTRACT,
    }

    with pytest.raises(ValueError, match="candidate_input_unknown_ledger"):
        _attach(request, evidence)


def test_premarket_scope_requires_explicit_route_mapping() -> None:
    trace = _trace()
    trace.update(
        {
            "effective_venue": "PREMARKET_KRX_LIKE",
            "session_bucket": "PREMARKET_KRX_LIKE",
            "market_data_route": "krx_only",
        }
    )
    assert resolve_micro_scope(trace).venue == "KRX"
    assert resolve_micro_scope(trace).session_bucket == "KRX_PREMARKET"

    trace["market_data_route"] = "krx_nxt_integrated"
    assert resolve_micro_scope(trace).venue == "SOR"
    assert resolve_micro_scope(trace).session_bucket == "SOR_PREMARKET"

    trace["market_data_route"] = None
    assert resolve_micro_scope(trace).status == "source_unavailable"
    assert resolve_micro_scope(trace).reason == "premarket_route_ambiguous"


def test_report_deduplicates_same_parent_wave_per_stage() -> None:
    second_trace = _trace(
        trace_id="trace-2",
        request_id="request-2",
        payload_sha256="provider-payload-hash-2",
        captured_at="2026-08-14T09:00:10.100+09:00",
    )
    second_payload = _payload(
        request_id="request-2",
        payload_sha256="provider-payload-hash-2",
        captured_at="2026-08-14T09:00:10.100+09:00",
    )
    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace(), second_trace],
        payloads=[_payload(), second_payload],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert report["summary"]["trace_payload_join_count"] == 2
    assert report["summary"]["micro_context_eligible_primary_episode_count"] == 1
    assert report["summary"]["same_parent_wave_repeat_count"] == 1
    assert report["source_exact_payload_mutated"] is False
    assert report["future_outcomes_separate_from_prompt_context"] is True


def test_report_time_index_keeps_invalid_rows_for_source_quality_attribution() -> None:
    invalid_market = {
        **_past_market_rows()[0],
        "local_receive_timestamp": "invalid-timestamp",
    }
    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=[*_past_market_rows(), invalid_market],
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    evidence = report["rows"][0][TACTICAL_EVIDENCE_SCHEMA]
    assert evidence["source_quality"]["rejected_market_reason_counts"] == {}
    assert report["summary"]["noncausal_source_diagnostics"] == {
        "invalid_market_timestamp_row_count": 1,
        "invalid_depth_timestamp_row_count": 0,
        "invalid_event_reference_timestamp_row_count": 0,
        "included_in_prompt_context": False,
    }


def test_envelope_join_supports_trace_without_request_id_in_report_and_prefilter() -> None:
    trace = _trace()
    trace.pop("request_id")
    payload = _payload()

    windows = _relevant_windows([trace], [payload], config=_verified_config())
    assert ("000001", "KRX", "KRX_REGULAR") in windows

    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[trace],
        payloads=[payload],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    assert report["summary"]["trace_payload_join_count"] == 1
    assert report["rows"][0]["payload_join_mode"] == "request_envelope_sha256"


def test_replay_enrichment_rejects_outcome_leakage() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    exact_payload = _payload()["sanitized_replay_context"]["exact_payload"]
    request = {
        "decision_trace_id": "trace-1",
        "exact_payload": exact_payload,
        "source_exact_payload_sha256": evidence["source_exact_payload_sha256"],
        "payload_sha256": evidence["source_provider_payload_sha256"],
        "request_envelope_sha256": evidence["source_request_envelope_sha256"],
    }
    leaking = {**evidence, "future_outcome": {"mfe": 1.0}}

    with pytest.raises(ValueError, match="future_outcome"):
        _attach(request, leaking)

    nested_leaking = {**evidence, "diagnostic": {"horizons": [{"mfe": 1.0}]}}
    with pytest.raises(ValueError, match="future_outcome"):
        _attach(request, nested_leaking)


def test_market_provenance_requires_native_boolean_and_integer_types() -> None:
    string_boolean = _past_market_rows()
    string_boolean[0] = {
        **string_boolean[0],
        "path_consumer_eligible": "true",
    }
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=string_boolean,
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["source_quality"]["rejected_market_reason_counts"] == {
        "market_provenance_invalid": 1
    }

    string_regression = _past_market_rows()
    string_regression[0] = {
        **string_regression[0],
        "exchange_timestamp_regression_ms": "0",
    }
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=string_regression,
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["source_quality"]["rejected_market_reason_counts"] == {
        "market_provenance_invalid": 1
    }
