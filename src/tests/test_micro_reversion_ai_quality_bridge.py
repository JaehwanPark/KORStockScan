from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import gzip
import hashlib
import json

import pytest

from src.engine.scalping import ai_decision_trace as trace_producer
from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge_module
from src.engine.scalping.micro_reversion.ai_quality_bridge import (
    AUTHORITY_CONTRACT,
    LIFECYCLE_PROJECTION_SCHEMA,
    TACTICAL_EVIDENCE_SCHEMA,
    BridgeConfig,
    _SQLiteRelevantSourceStore,
    _economics,
    _control_decision_findings,
    _lifecycle_projection,
    _liquidity_projection,
    _position_context,
    _relevant_windows,
    _sha256,
    attach_micro_context_to_replay_request,
    build_bridge_report,
    build_future_outcome,
    build_tactical_evidence,
    build_three_arm_manifest,
    materialize_micro_reversion_three_arm_requests,
    resolve_micro_scope,
)

CONTROL_PROMPT = "control prompt"
TEST_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"action": {"type": "string"}},
    "required": ["action"],
    "additionalProperties": False,
}


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


def _stored_prompt_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request_envelope_hash(*, payload_sha256: str, replay_context_sha256: str) -> str:
    return _producer_hash(
        {
            "endpoint": "analyze_target",
            "model": "gpt-5.4-nano",
            "schema_name": "entry_decision_v2",
            "require_json": True,
            "temperature": 0.1,
            "max_output_tokens": 900,
            "reasoning_effort": "low",
            "prompt_sha256": _stored_prompt_hash(CONTROL_PROMPT),
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
        "prompt_sha256": _stored_prompt_hash(CONTROL_PROMPT),
        "model": "gpt-5.4-nano",
        "model_requested": "gpt-5.4-nano",
        "transport": "responses_http",
        "response_sha256": "response-hash",
        "provider_response_id": "resp-test",
        "openai_response_schema_mode": "strict_dynamic_entry_risk",
        "openai_response_schema_registry_used": True,
        "response_schema_sha256": _producer_hash(TEST_RESPONSE_SCHEMA),
        "response_schema_application": "provider_enforced_openai",
        "request_temperature": 0.1,
        "request_max_output_tokens": 900,
        "request_reasoning_effort": "low",
        "semantic_validator_version": "entry_semantic_v1",
        "semantic_validator_applied": True,
        "semantic_validation_status": "pass",
        "instrument_type": "COMMON_STOCK",
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
        "prompt_sha256": _stored_prompt_hash(CONTROL_PROMPT),
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
    artifact = {
        "schema": "micro_reversion_reviewed_cost_profile_v1",
        "artifact_id": "test-cost-profile-2026-08-14",
        "effective_date": "2026-08-14",
        "venues": ["KRX", "NXT", "SOR"],
        "instrument_scope": "domestic_common_or_preferred_stock",
        "source": "verified_test_profile",
        "buy_fee_bps": 0.0,
        "sell_fee_bps": 0.0,
        "statutory_sell_tax_bps": 20.0,
        "uncertainty_buffer_bps": 3.0,
    }
    return BridgeConfig(
        statutory_sell_tax_bps=20.0,
        uncertainty_buffer_bps=3.0,
        cost_profile_source="verified_test_profile",
        cost_profile_verified=True,
        cost_profile_artifact_id="test-cost-profile-2026-08-14",
        cost_profile_artifact_sha256=_producer_hash(artifact),
        cost_profile_artifact_payload_json=json.dumps(
            artifact,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        cost_profile_effective_date="2026-08-14",
        cost_profile_venues=("KRX", "NXT", "SOR"),
    )


def _verified_symbol_metadata(*, symbol: str = "000001") -> dict:
    record = {
        "symbol": symbol,
        "listing_market": "KOSPI",
        "instrument_type": "EQUITY",
        "instrument_tax_class": "ordinary_taxable_equity_20bps",
        "effective_from": "2026-08-01",
        "effective_to": None,
        "metadata_source": "verified_test_symbol_master",
        "source_reference": "test://symbol-master/000001",
        "verified_at": "2026-08-13T18:00:00+09:00",
        "conflict_status": "clean",
    }
    return {
        "lookup_status": "verified",
        "record": record,
        "record_sha256": _producer_hash(record),
        "symbol_master_artifact_sha256": "a" * 64,
    }


def _entry_pipeline_allocator_row(
    *, quantity: int = 50, formula_version: str = "entry_type_5stage_cap25_v1"
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": "ai_confirmed",
        "stock_code": "000001",
        "record_id": 101,
        "emitted_at": "2026-08-14T09:00:11.100+09:00",
        "emitted_date": "2026-08-14",
        "fields": {
            "ai_decision_trace_id": "trace-1",
            "formula_version": formula_version,
            "effective_qty": str(quantity),
            "qty_source": "scalping_position_sizing_allocator",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
            "market_data_route": "krx_only",
        },
    }


def _premarket_route_inputs(
    *, market_data_route: str, integrated_proven: bool
) -> tuple[dict, dict, list[dict], dict, dict]:
    trace = _trace()
    payload = _payload()
    trace.update(
        {
            "effective_venue": "PREMARKET_KRX_LIKE",
            "session_bucket": "PREMARKET_KRX_LIKE",
            "market_data_route": market_data_route,
        }
    )
    payload.update(
        {
            "effective_venue": "PREMARKET_KRX_LIKE",
            "session_bucket": "PREMARKET_KRX_LIKE",
            "market_data_route": market_data_route,
        }
    )
    replay_context = payload["sanitized_replay_context"]
    exact_payload = replay_context["exact_payload"]
    candle = exact_payload["entry_candle_context"]
    candle.update(
        {
            "venue": "PREMARKET_KRX_LIKE",
            "session": "PREMARKET_KRX_LIKE",
        }
    )
    snapshot = exact_payload["ai_market_snapshot"]
    snapshot.update(
        {
            "effective_venue": "PREMARKET_KRX_LIKE",
            "session_bucket": "PREMARKET_KRX_LIKE",
            "market_data_route": market_data_route,
            "integrated_sor_route_proven": integrated_proven,
        }
    )
    replay_context_sha256 = _producer_hash(replay_context)
    request_envelope_sha256 = _request_envelope_hash(
        payload_sha256=payload["payload_sha256"],
        replay_context_sha256=replay_context_sha256,
    )
    payload["replay_context_sha256"] = replay_context_sha256
    trace["replay_context_sha256"] = replay_context_sha256
    payload["request_envelope_sha256"] = request_envelope_sha256
    trace["request_envelope_sha256"] = request_envelope_sha256

    venue = "SOR" if "integrated" in market_data_route else "KRX"
    session = f"{venue}_PREMARKET"
    item = "000001_AL" if venue == "SOR" else "000001"
    market_rows = deepcopy(_past_market_rows())
    for row in market_rows:
        row.update({"item": item, "venue": venue, "session_bucket": session})
    depth = deepcopy(_depth())
    depth.update({"item": item, "venue": venue, "session_bucket": session})
    reference = deepcopy(_reference())
    reference.update({"venue": venue, "session_bucket": session})
    return trace, payload, market_rows, depth, reference


def _attach(request: dict, evidence: dict) -> dict:
    metadata = (
        _verified_symbol_metadata()
        if evidence.get("economics", {}).get("symbol_metadata_status") == "verified"
        else None
    )
    return attach_micro_context_to_replay_request(
        request,
        evidence,
        source_trace=_trace(),
        source_payload=_payload(),
        source_market_rows=_past_market_rows(),
        source_depth_rows=[_depth()],
        source_event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=metadata,
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
        verified_symbol_metadata=_verified_symbol_metadata(),
    )

    assert evidence["state"] == "reversion_confirmed"
    assert evidence["event"]["asof_trade_price"] == 9_960
    assert evidence["event"]["parent_wave_id"] == "wave-1"
    assert evidence["source_quality"]["parent_wave_reference_count"] == 1
    assert evidence["source_quality"]["future_outcome_fields_in_context"] is False
    assert evidence["decision_watermark"]["past_only_join"] is True
    assert evidence["trace_market_data_route"] == "krx_only"
    assert evidence["integrated_sor_route_proven"] is False
    assert evidence["liquidity_capacity"]["counterfactual_liquidity_qty_ceiling"] == 5
    assert evidence["liquidity_capacity"]["quantity_authority_status"] == (
        "depth_capacity_only_no_order_authority"
    )
    assert (
        "existing_position_formula_candidate_qty" not in evidence["liquidity_capacity"]
    )
    assert (
        evidence["liquidity_capacity"]["snapshot_depth_execution_basis"][
            "allocator_or_order_quantity_present"
        ]
        is False
    )
    assert evidence["economics"]["symbol_metadata_status"] == "verified"
    assert evidence["economics"]["spread_double_counted"] is False
    assert evidence["economics"]["minimum_gross_target_bps"] > 28.0
    lifecycle = evidence[LIFECYCLE_PROJECTION_SCHEMA]
    assert lifecycle["entry_projection"]["live_price_or_order_effect"] is False
    assert lifecycle["exit_projection"]["live_sell_or_cancel_effect"] is False
    for key, expected in AUTHORITY_CONTRACT.items():
        assert evidence[key] is expected
        assert lifecycle[key] is expected


def test_one_share_probe_floor_requires_real_bid_and_ask_capacity() -> None:
    shallow_depth = _depth()
    shallow_depth.update(
        {
            "best_bid_qty": 5,
            "best_ask_qty": 5,
            "bid_depth": 10,
            "ask_depth": 10,
            "route_depth_totals": {
                "KRX": {"bid": 10, "ask": 10},
                "NXT": {"bid": 0, "ask": 0},
                "combined": {"bid": 10, "ask": 10},
            },
            "bid_levels": [[1, 9_950.0, 5], [2, 9_940.0, 5]],
            "ask_levels": [[1, 9_960.0, 5], [2, 9_970.0, 5]],
        }
    )

    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[shallow_depth],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )

    conservative = evidence["liquidity_capacity"]["counterfactual_liquidity_qty_grid"][
        1
    ]
    assert conservative["counterfactual_liquidity_bounded_qty"] == 1
    assert conservative["strict_depth_participation_capacity_qty"] == 0
    assert conservative["one_share_probe_floor_applied"] is True
    assert conservative["immediate_marketable_exit_capacity_qty"] == 1
    assert conservative["immediate_exit_one_share_floor_applied"] is True

    allocator_outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[_entry_pipeline_allocator_row(quantity=5)],
        config=_verified_config(),
    )
    assert allocator_outcome["counterfactual_quantity"] == 0
    assert allocator_outcome["notional_net_profit_eligible"] is False


def test_missing_allocator_qty_keeps_one_share_as_observation_only() -> None:
    projection = _liquidity_projection(
        depth=_depth(),
        recent_rows=_past_market_rows(),
        config=_verified_config(),
    )

    conservative = projection["counterfactual_liquidity_qty_grid"][1]
    assert conservative["counterfactual_liquidity_bounded_qty"] == 5
    assert conservative["standardized_one_share_probe_observation_qty"] == 1
    assert projection["counterfactual_liquidity_qty_ceiling"] == 5
    assert projection["quantity_authority_status"] == (
        "depth_capacity_only_no_order_authority"
    )


def test_verified_cost_profile_requires_versioned_scope_artifact() -> None:
    with pytest.raises(ValueError, match="reviewed artifact hash"):
        BridgeConfig(
            statutory_sell_tax_bps=20.0,
            cost_profile_source="test",
            cost_profile_verified=True,
        )


def test_verified_cost_profile_rejects_tampered_artifact_and_future_scope() -> None:
    config = _verified_config()
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        BridgeConfig(
            **{
                **{
                    field: getattr(config, field)
                    for field in BridgeConfig.__dataclass_fields__
                },
                "cost_profile_artifact_sha256": "b" * 64,
            }
        )

    economics = _economics(
        liquidity={"counterfactual_liquidity_qty_grid": []},
        config=config,
        venue="KRX",
        snapshot_date="2026-08-13",
        symbol_metadata={
            "symbol_metadata_status": "verified",
            "listing_market": "KOSPI",
            "instrument_type": "EQUITY",
            "instrument_tax_class": "ordinary_taxable_equity_20bps",
        },
    )
    assert economics["cost_profile_contract_verified"] is True
    assert economics["cost_profile_verified"] is False
    assert economics["cost_profile_scope_status"] == (
        "reviewed_artifact_not_applicable_to_venue_or_date"
    )

    unknown_instrument = _economics(
        liquidity={"counterfactual_liquidity_qty_grid": []},
        config=config,
        venue="KRX",
        snapshot_date="2026-08-14",
        symbol_metadata={"symbol_metadata_status": "missing"},
    )
    assert unknown_instrument["cost_profile_verified"] is False
    assert unknown_instrument["cost_profile_scope_status"] == (
        "reviewed_artifact_instrument_type_unverified_or_not_covered"
    )

    konex_tax_scope = _economics(
        liquidity={"counterfactual_liquidity_qty_grid": []},
        config=config,
        venue="KRX",
        snapshot_date="2026-08-14",
        symbol_metadata={
            "symbol_metadata_status": "verified",
            "listing_market": "KONEX",
            "instrument_type": "EQUITY",
            "instrument_tax_class": "konex_taxable_equity_10bps",
        },
    )
    assert konex_tax_scope["cost_profile_verified"] is False
    assert konex_tax_scope["cost_profile_scope_status"] == (
        "reviewed_artifact_instrument_tax_scope_mismatch"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("buy_fee_bps", True),
        ("sell_fee_bps", "0.0"),
        ("statutory_sell_tax_bps", -1.0),
        ("uncertainty_buffer_bps", float("nan")),
    ],
)
def test_verified_cost_artifact_rejects_non_native_or_nonfinite_numbers(
    tmp_path, field, value
) -> None:
    artifact = json.loads(_verified_config().cost_profile_artifact_payload_json)
    artifact[field] = value
    path = tmp_path / "invalid_cost_profile.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(
        ValueError, match=f"verified_cost_profile_numeric_invalid:{field}"
    ):
        bridge_module._verified_cost_config_from_path(
            path, target_date=datetime.fromisoformat("2026-08-14").date()
        )


def test_verified_symbol_metadata_is_hash_bound_and_trace_guessing_is_forbidden() -> (
    None
):
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )

    economics = evidence["economics"]
    assert economics["cost_profile_verified"] is True
    assert economics["instrument_type"] == "EQUITY"
    assert economics["listing_market"] == "KOSPI"
    assert len(economics["symbol_metadata_record_sha256"]) == 64
    assert economics["symbol_master_artifact_sha256"] == "a" * 64
    assert "record" not in economics

    unverified = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    assert unverified["economics"]["symbol_metadata_status"] == "missing"
    assert unverified["economics"]["instrument_type"] is None
    assert unverified["economics"]["cost_profile_verified"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda value: value["record"].update({"symbol": "000002"}),
            "verified_symbol_metadata_symbol_mismatch",
        ),
        (
            lambda value: value.update({"record_sha256": "b" * 64}),
            "verified_symbol_metadata_record_sha256_mismatch",
        ),
        (
            lambda value: value["record"].update({"effective_from": "2026-08-15"}),
            "verified_symbol_metadata_outside_effective_window",
        ),
    ],
)
def test_verified_symbol_metadata_mismatch_fails_closed(mutation, reason) -> None:
    metadata = _verified_symbol_metadata()
    mutation(metadata)
    with pytest.raises(ValueError, match=reason):
        build_tactical_evidence(
            trace=_trace(),
            payload=_payload(),
            market_rows=_past_market_rows(),
            depth_rows=[_depth()],
            event_references=[_reference()],
            config=_verified_config(),
            verified_symbol_metadata=metadata,
        )


def test_invalid_latest_market_and_depth_do_not_fallback_to_older_valid_rows() -> None:
    invalid_market = {
        **_past_market_rows()[-1],
        "local_receive_timestamp": "2026-08-14T09:00:09.900+09:00",
        "exchange_timestamp": "2026-08-14T09:00:09.900+09:00",
        "source_sequence": 5,
        "series_sequence": 5,
        "path_consumer_eligible": "true",
    }
    market_blocked = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=[*_past_market_rows(), invalid_market],
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    assert market_blocked["source_quality"]["status"] == "blocked"
    assert (
        "market_invalid_row_supersedes_latest_valid"
        in market_blocked["source_quality"]["blockers"]
    )
    blocked_outcome = build_future_outcome(
        evidence=market_blocked,
        market_rows=[],
        depth_rows=[],
        config=_verified_config(),
    )
    assert blocked_outcome["outcome_eligibility"] == "source_unavailable"
    assert (
        "tactical_evidence_source_quality_not_pass"
        in blocked_outcome["outcome_eligibility_blockers"]
    )

    invalid_depth = {
        **_depth(
            "2026-08-14T09:00:09.900+09:00",
            sequence=2,
        ),
        "best_bid_qty": 99,
    }
    depth_blocked = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth(), invalid_depth],
        event_references=[_reference()],
        config=_verified_config(),
    )
    assert depth_blocked["source_quality"]["status"] == "pass"
    assert depth_blocked["source_quality"]["liquidity_capacity_status"] == "blocked"
    assert (
        "depth_invalid_row_supersedes_latest_valid"
        in depth_blocked["source_quality"]["liquidity_capacity_blockers"]
    )
    assert (
        depth_blocked["liquidity_capacity"]["counterfactual_liquidity_qty_ceiling"]
        is None
    )


def test_future_outcome_rejects_tampered_evidence_identity() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    tampered = deepcopy(evidence)
    tampered["snapshot_captured_at_ms"] -= 5_000

    with pytest.raises(ValueError, match="future_outcome_evidence_sha256_mismatch"):
        build_future_outcome(
            evidence=tampered,
            market_rows=[],
            depth_rows=[],
            config=_verified_config(),
        )


def test_reconfirmed_price_does_not_reuse_buy_support_from_invalidated_cycle() -> None:
    rows = [
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
            "2026-08-14T09:00:08.000+09:00",
            price=9_940,
            side="BUY",
            qty=400,
            sequence=4,
        ),
        _market(
            "2026-08-14T09:00:09.000+09:00",
            price=9_870,
            side="SELL",
            qty=1,
            sequence=5,
        ),
        _market(
            "2026-08-14T09:00:09.800+09:00",
            price=9_935,
            side="SELL",
            qty=1,
            sequence=6,
            bid=9_925,
            ask=9_935,
        ),
    ]
    depth = _depth(bid=9_925.0, ask=9_935.0)
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=rows,
        depth_rows=[depth],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["state"] == "reversion_candidate"
    assert evidence["event"]["recovery_invalidation_count"] == 1
    assert evidence["event"]["latest_recovery_cycle_reconfirmed"] is True
    assert evidence["tape"]["latest_recovery_cycle_support"]["buy_qty"] == 0


def test_latest_recovery_cycle_keeps_buy_buildup_before_final_reclaim_cross() -> None:
    rows = [
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
            "2026-08-14T09:00:08.000+09:00",
            price=9_940,
            side="BUY",
            qty=400,
            sequence=4,
        ),
        _market(
            "2026-08-14T09:00:09.000+09:00",
            price=9_870,
            side="SELL",
            qty=1,
            sequence=5,
        ),
        _market(
            "2026-08-14T09:00:09.400+09:00",
            price=9_900,
            side="BUY",
            qty=100,
            sequence=6,
        ),
        _market(
            "2026-08-14T09:00:09.800+09:00",
            price=9_935,
            side="SELL",
            qty=1,
            sequence=7,
            bid=9_925,
            ask=9_935,
        ),
    ]
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=rows,
        depth_rows=[_depth(bid=9_925.0, ask=9_935.0)],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["state"] == "reversion_confirmed"
    assert evidence["tape"]["latest_recovery_cycle_support"]["buy_qty"] == 100
    assert evidence["event"]["latest_recovery_cycle_reconfirmed"] is True


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
    assert (
        "same_epoch_past_depth_missing"
        in evidence["source_quality"]["liquidity_capacity_blockers"]
    )
    assert (
        evidence["liquidity_capacity"]["counterfactual_liquidity_qty_ceiling"] is None
    )


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
    assert outcome["counterfactual_quantity"] == 1
    assert outcome["counterfactual_quantity_basis"] == (
        "standardized_one_share_observation_only"
    )
    assert outcome["notional_net_profit_eligible"] is False
    assert outcome["economic_promotion_evidence_eligible"] is False
    assert outcome["economic_promotion_authority"] is False
    assert all(
        row["action_neutral_executable_end_return_bps"] is None
        and row["action_neutral_path_sha256"] is None
        for row in outcome["horizons"]
    )
    assert "future_outcome" not in evidence
    assert "horizons" not in evidence


def test_entry_outcome_joins_deduplicated_allocator_and_caps_at_5pct_depth() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    allocator = _entry_pipeline_allocator_row(quantity=50)
    duplicate = deepcopy(allocator)
    duplicate["stage"] = "scalp_entry_action_decision_snapshot"
    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[
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
                price=10_040,
                side="BUY",
                qty=100,
                sequence=6,
                bid=10_030,
                ask=10_040,
            ),
        ],
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
                bid=10_030.0,
                ask=10_040.0,
            ),
        ],
        entry_pipeline_rows=[allocator, duplicate],
        config=_verified_config(),
    )

    assert outcome["counterfactual_quantity"] == 5
    assert outcome["effective_qty"] == 50
    assert outcome["liquidity_capped_qty"] == 5
    assert outcome["quantity_authority"] == (
        "position_sizing_dynamic_formula_outcome_only"
    )
    assert outcome["formula_version"] == "entry_type_5stage_cap25_v1"
    assert len(outcome["allocator_event_sha256"]) == 64
    assert len(outcome["allocator_source_event_sha256s"]) == 2
    assert all(len(value) == 64 for value in outcome["allocator_source_event_sha256s"])
    assert outcome["allocator_first_event_timestamp_ms"] >= _ms(
        "2026-08-14T09:00:11.000+09:00"
    )
    assert (
        outcome["allocator_last_event_timestamp_ms"]
        >= outcome["allocator_first_event_timestamp_ms"]
    )
    assert outcome["allocator_matching_row_count"] == 2
    assert outcome["allocator_deduplicated_event_count"] == 1
    assert outcome["notional_net_profit_eligible"] is True
    assert outcome["economic_promotion_evidence_eligible"] is True
    assert outcome["economic_promotion_authority"] is False
    assert outcome["action_neutral_economic_grade"] == (
        "reviewed_after_cost_entry_value"
    )
    assert outcome["cost_invariant_between_exit_timings"] is False
    mature_neutral = [
        row
        for row in outcome["horizons"]
        if row["mature"] is True
        and row["action_neutral_executable_end_return_bps"] is not None
    ]
    assert mature_neutral
    assert all(len(row["action_neutral_path_sha256"]) == 64 for row in mature_neutral)
    assert all(
        row["action_neutral_first_hit"]
        in {"net_target_first", "adverse_first", "none", "ambiguous_same_timestamp"}
        for row in mature_neutral
    )
    assert outcome["action_neutral_first_hit"] != "unavailable"


def test_entry_outcome_allocator_conflict_fails_closed() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    with pytest.raises(
        ValueError, match="entry_pipeline_allocator_provenance_conflict"
    ):
        build_future_outcome(
            evidence=evidence,
            market_rows=[],
            entry_pipeline_rows=[
                _entry_pipeline_allocator_row(quantity=5),
                _entry_pipeline_allocator_row(quantity=6),
            ],
            config=_verified_config(),
        )


def test_allocator_join_ignores_other_trace_and_symbol() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    other_trace = _entry_pipeline_allocator_row(quantity=50)
    other_trace["fields"]["ai_decision_trace_id"] = "trace-other"
    other_symbol = _entry_pipeline_allocator_row(quantity=50)
    other_symbol["stock_code"] = "000002"

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[other_trace, other_symbol],
        config=_verified_config(),
    )

    assert outcome["counterfactual_quantity"] == 1
    assert outcome["allocator_event_sha256"] is None
    assert outcome["notional_net_profit_eligible"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda row: row.update({"emitted_at": "2026-08-14T09:00:10.999+09:00"}),
            "entry_pipeline_allocator_event_precedes_ai_decision",
        ),
        (
            lambda row: row["fields"].update({"effective_venue": "NXT"}),
            "entry_pipeline_allocator_venue_mismatch",
        ),
        (
            lambda row: row["fields"].update({"market_session_bucket": "nxt_regular"}),
            "entry_pipeline_allocator_session_mismatch",
        ),
        (
            lambda row: row["fields"].update({"market_data_route": "nxt_only"}),
            "entry_pipeline_allocator_route_mismatch",
        ),
    ],
)
def test_allocator_join_fails_closed_on_causal_scope_mismatch(mutation, reason) -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    allocator = _entry_pipeline_allocator_row(quantity=1)
    mutation(allocator)

    with pytest.raises(ValueError, match=reason):
        build_future_outcome(
            evidence=evidence,
            market_rows=[],
            entry_pipeline_rows=[allocator],
            config=_verified_config(),
        )


def test_scale_in_outcome_delegates_quantity_owner() -> None:
    trace = _trace()
    trace["decision_stage"] = "scale_in"
    evidence = build_tactical_evidence(
        trace=trace,
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[_entry_pipeline_allocator_row(quantity=50)],
        config=_verified_config(),
    )

    assert outcome["evaluation_basis"] == (
        "scale_in_quantity_evaluation_owned_by_stage_replay"
    )
    assert outcome["counterfactual_quantity"] is None
    assert outcome["counterfactual_quantity_basis"] == (
        "scale_in_quantity_owner_delegated"
    )
    assert (
        "scale_in_quantity_owner_not_connected"
        in outcome["outcome_eligibility_blockers"]
    )
    assert outcome["notional_net_profit_eligible"] is False


def test_holding_exit_keeps_action_neutral_endpoint_on_hold_return_basis() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    holding = deepcopy(evidence)
    holding["decision_stage"] = "holding_score"
    lifecycle = holding[LIFECYCLE_PROJECTION_SCHEMA]
    lifecycle["decision_stage"] = "holding_score"
    projection = lifecycle["holding_projection"]
    projection["counterfactual_free_to_sell_qty"] = 1
    projection["counterfactual_snapshot_exit_sweep_vwap"] = 9_950.0
    projection["observed_position_average_price"] = 10_000.0
    projection["position_provenance"]["position_execution_eligible"] = True
    projection["position_provenance"]["hard_exit_guard_observed"] = False
    without_hash = {
        key: value for key, value in holding.items() if key != "evidence_sha256"
    }
    holding["evidence_sha256"] = _sha256(without_hash)

    outcome = build_future_outcome(
        evidence=holding,
        market_rows=[
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
                price=10_040,
                side="BUY",
                qty=100,
                sequence=6,
                bid=10_030,
                ask=10_040,
            ),
        ],
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
                bid=10_030.0,
                ask=10_040.0,
            ),
        ],
        control_action="EXIT",
        config=_verified_config(),
    )

    first_mature = next(row for row in outcome["horizons"] if row["mature"])
    assert first_mature["decision_quality_mfe_bps"] < 0
    assert first_mature["action_neutral_executable_end_return_bps"] > 0
    assert first_mature["action_neutral_mfe_bps"] > 0
    assert len(first_mature["action_neutral_path_sha256"]) == 64
    assert first_mature["action_neutral_first_hit"] == "net_target_first"
    assert outcome["action_neutral_first_hit"] == "net_target_first"
    assert outcome["action_neutral_cost_treatment"] == (
        "identical_proportional_exit_cost_cancels"
    )
    assert outcome["action_neutral_economic_grade"] == (
        "liquidity_adjusted_incremental_exit_value"
    )
    assert outcome["cost_invariant_between_exit_timings"] is True


def test_future_outcome_requires_same_conservative_fast_exit_capacity() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    thin_depths = []
    for sequence, timestamp in (
        (2, "2026-08-14T09:00:10.500+09:00"),
        (3, "2026-08-14T09:00:11.500+09:00"),
    ):
        row = _depth(timestamp, sequence=sequence, bid=10_020.0, ask=10_030.0)
        row.update(
            {
                "best_bid_qty": 25,
                "bid_depth": 50,
                "route_depth_totals": {
                    "KRX": {"bid": 50, "ask": 1_000},
                    "NXT": {"bid": 0, "ask": 0},
                    "combined": {"bid": 50, "ask": 1_000},
                },
                "bid_levels": [[1, 10_020.0, 25], [2, 10_010.0, 25]],
            }
        )
        thin_depths.append(row)
    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[
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
                price=10_030,
                side="BUY",
                qty=100,
                sequence=6,
                bid=10_020,
                ask=10_030,
            ),
        ],
        depth_rows=thin_depths,
        entry_pipeline_rows=[_entry_pipeline_allocator_row(quantity=50)],
        config=_verified_config(),
    )

    assert outcome["future_depth_participation_rate"] == 0.05
    assert all(
        row["quantity_sweep_observation_count"] == 0 for row in outcome["horizons"]
    )
    assert outcome["first_hit"] == "none_or_unmatured"


def test_allocator_entry_future_depth_never_applies_one_share_floor() -> None:
    snapshot_depth = _depth()
    snapshot_depth.update(
        {
            "best_bid_qty": 20,
            "best_ask_qty": 20,
            "bid_depth": 20,
            "ask_depth": 20,
            "route_depth_totals": {
                "KRX": {"bid": 20, "ask": 20},
                "NXT": {"bid": 0, "ask": 0},
                "combined": {"bid": 20, "ask": 20},
            },
            "bid_levels": [[1, 9_950.0, 20]],
            "ask_levels": [[1, 9_960.0, 20]],
        }
    )
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[snapshot_depth],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    future_market = [
        _market(
            "2026-08-14T09:00:10.500+09:00",
            price=10_030,
            side="BUY",
            qty=10,
            sequence=5,
            bid=10_020,
            ask=10_030,
        )
    ]
    future_depth = _depth(
        "2026-08-14T09:00:10.500+09:00",
        sequence=2,
        bid=10_020.0,
        ask=10_030.0,
    )
    future_depth.update(
        {
            "best_bid_qty": 5,
            "best_ask_qty": 5,
            "bid_depth": 10,
            "ask_depth": 10,
            "route_depth_totals": {
                "KRX": {"bid": 10, "ask": 10},
                "NXT": {"bid": 0, "ask": 0},
                "combined": {"bid": 10, "ask": 10},
            },
            "bid_levels": [[1, 10_020.0, 5], [2, 10_010.0, 5]],
            "ask_levels": [[1, 10_030.0, 5], [2, 10_040.0, 5]],
        }
    )

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=future_market,
        depth_rows=[future_depth],
        entry_pipeline_rows=[_entry_pipeline_allocator_row(quantity=1)],
        config=_verified_config(),
    )

    assert outcome["counterfactual_quantity"] == 1
    assert all(
        row["quantity_sweep_observation_count"] == 0 for row in outcome["horizons"]
    )
    assert outcome["economic_promotion_evidence_eligible"] is False


def test_holding_position_requires_fresh_reconciled_free_to_sell_quantity() -> None:
    holding_context = {
        "schema": "holding_decision_context_v1",
        "execution_pnl": {"remaining_qty": 10, "average_entry_price": 10_000},
        "position_lifecycle": {
            "broker_qty": 10,
            "memory_qty": 10,
            "average_entry_price": 10_000,
        },
        "order_reconciliation": {
            "broker_snapshot_age_sec": 2.0,
            "open_sell_qty": 3,
            "cancel_pending": False,
            "exit_token_active": False,
            "quantity_mismatch": False,
            "order_or_quantity_conflict": False,
        },
        "source_quality": {
            "position_reconciled": True,
            "position_authority_reconciled": True,
            "position_reconciliation_mode": "broker_book",
            "simulation_position_reconciled": False,
        },
    }
    exact_payload = {
        "input_schema": "holding_flow_v2",
        "decision_type": {"candidate_exit_rule": "soft_stop"},
        "holding_decision_context": holding_context,
    }
    payload = {
        "replay_context_present": True,
        "sanitized_replay_context": {
            "input_schema": "decision_quality_holding_flow_exact_v2",
            "exact_payload": exact_payload,
        },
    }

    fresh = _position_context(payload, max_broker_position_age_sec=60.0)
    assert fresh["position_execution_eligible"] is True
    assert fresh["free_to_sell_quantity"] == 7
    assert fresh["hard_exit_guard_observed"] is False

    stale_payload = deepcopy(payload)
    stale_payload["sanitized_replay_context"]["exact_payload"][
        "holding_decision_context"
    ]["order_reconciliation"]["broker_snapshot_age_sec"] = 61.0
    stale = _position_context(stale_payload, max_broker_position_age_sec=60.0)
    assert stale["position_execution_eligible"] is False
    assert stale["free_to_sell_quantity"] is None

    hard_payload = deepcopy(payload)
    hard_payload["sanitized_replay_context"]["exact_payload"]["decision_type"][
        "candidate_exit_rule"
    ] = "hard_stop"
    hard = _position_context(hard_payload, max_broker_position_age_sec=60.0)
    assert hard["hard_exit_guard_observed"] is True

    lifecycle = _lifecycle_projection(
        trace={"decision_stage": "holding_score"},
        payload=payload,
        capacity_depth=_depth(),
        liquidity={
            "counterfactual_liquidity_qty_ceiling": 5,
            "counterfactual_immediate_exit_qty_ceiling": 50,
        },
        economics={
            "statutory_sell_tax_bps": 20.0,
            "buy_fee_bps": 0.0,
            "sell_fee_bps": 0.0,
            "uncertainty_buffer_bps": 3.0,
            "minimum_net_profit_bps": 5.0,
        },
        max_exit_sweep_slippage_bps=10.0,
        max_broker_position_age_sec=60.0,
    )
    assert (
        lifecycle["exit_projection"]["counterfactual_immediately_executable_qty"] == 7
    )


def test_opt_in_replay_enrichment_preserves_exact_payload_and_three_arm_parity() -> (
    None
):
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
    assert (
        manifest["replay_arms"][1]["analytical_context_pair_sha256"]
        == manifest["replay_arms"][2]["analytical_context_pair_sha256"]
    )
    assert "tactical_micro_reversion_evidence_sha256" not in manifest["replay_arms"][0]
    assert manifest["provider_call_performed"] is False


def test_entry_price_control_semantics_are_prompt_version_specific() -> None:
    trace = _trace()
    trace.update(
        {
            "decision_stage": "entry_price",
            "endpoint": "entry_price",
            "action": "USE_DEFENSIVE",
            "prompt_version": "entry_price_v1",
            "semantic_validator_version": ("live_entry_price_v1_schema_semantic_v1"),
            "entry_price_v1_contract_status": "pass",
            "entry_price_v1_contract_errors": [],
            "entry_price_v1_forensic_errors": [],
        }
    )
    contract = {
        "schema_name": "entry_price_v1",
        "response_schema_mode": "strict_dynamic_entry_risk",
        "semantic_validator_version": "live_entry_price_v1_schema_semantic_v1",
        "max_output_tokens": 900,
        "require_json": True,
        "response_schema_registry_used": True,
    }
    assert not {
        finding
        for finding in _control_decision_findings(trace, control_contract=contract)
        if "entry_price" in finding
    }

    rejected = deepcopy(trace)
    rejected["entry_price_v1_contract_errors"] = ["price_semantics_invalid"]
    assert "control_entry_price_v1_semantic_errors_present" in (
        _control_decision_findings(rejected, control_contract=contract)
    )

    v2_5 = deepcopy(trace)
    v2_5.update(
        {
            "prompt_version": "entry_price_v2_5",
            "semantic_validator_version": "entry_price_v2_5_semantic_v1",
            "entry_price_v2_5_contract_status": "pass",
        }
    )
    v2_5_contract = {
        **contract,
        "schema_name": "entry_price_v2_5",
        "semantic_validator_version": "entry_price_v2_5_semantic_v1",
    }
    assert not {
        finding
        for finding in _control_decision_findings(v2_5, control_contract=v2_5_contract)
        if "entry_price" in finding
    }


def test_entry_price_v1_trace_producer_fields_reach_bridge_consumer(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED", "true")
    monkeypatch.setattr(trace_producer, "DATA_DIR", tmp_path)
    for cache in (
        trace_producer._SEEN_PAYLOAD_HASHES,
        trace_producer._SEEN_PROMPT_HASHES,
        trace_producer._SEEN_TRACE_IDS,
        trace_producer._SEEN_REQUEST_IDS,
        trace_producer._SEEN_OUTCOME_LABEL_IDS,
        trace_producer._SEEN_CONTEXT_CANDIDATE_HASHES,
    ):
        cache.clear()
    result = _trace()
    result.update(
        {
            "decision_stage": "entry_price",
            "endpoint": "entry_price",
            "action": "USE_DEFENSIVE",
            "prompt_version": "entry_price_v1",
            "provider": "openai",
            "ai_parse_ok": True,
            "openai_request_id": "request-1",
            "openai_response_schema_sha256": result["response_schema_sha256"],
            "openai_response_schema_application": "provider_enforced_openai",
            "semantic_validator_version": ("live_entry_price_v1_schema_semantic_v1"),
            "semantic_validator_applied": True,
            "semantic_validation_status": "pass",
            "entry_price_v1_contract_status": "pass",
            "entry_price_v1_contract_errors": [],
            "entry_price_v1_forensic_errors": [],
            "ai_trace_stock_code": "000001",
        }
    )
    trace_producer.record_ai_decision_trace(
        result,
        prompt_type="entry_price",
        prompt_version="entry_price_v1",
        result_source="live",
        provider_called=True,
    )
    trace_path = trace_producer._trace_path(trace_producer._date_text())
    produced = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])
    assert produced["entry_price_v1_contract_status"] == "pass"
    assert produced["entry_price_v1_contract_errors"] == []
    contract = {
        "schema_name": "entry_price_v1",
        "response_schema_mode": "strict_dynamic_entry_risk",
        "semantic_validator_version": "live_entry_price_v1_schema_semantic_v1",
        "max_output_tokens": 900,
        "require_json": True,
        "response_schema_registry_used": True,
    }
    findings = _control_decision_findings(produced, control_contract=contract)
    assert not {finding for finding in findings if "entry_price_v1" in finding}


def test_materializes_fair_three_arm_requests_without_provider_authority() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    exact_payload = deepcopy(_payload()["sanitized_replay_context"]["exact_payload"])

    def request(prompt_version: str, prompt: str) -> dict:
        candidate_input = {"exact_payload": deepcopy(exact_payload)}
        response_schema = deepcopy(TEST_RESPONSE_SCHEMA)
        return {
            "decision_trace_id": "trace-1",
            "decision_authority": "offline_replay_no_runtime_change",
            "stage": "entry",
            "endpoint": "analyze_target",
            "stock_code": "000001",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "exact_payload": deepcopy(exact_payload),
            "source_exact_payload_sha256": evidence["source_exact_payload_sha256"],
            "payload_sha256": evidence["source_provider_payload_sha256"],
            "request_envelope_sha256": evidence["source_request_envelope_sha256"],
            "candidate_input": candidate_input,
            "candidate_input_sha256": _producer_hash(candidate_input),
            "candidate": {
                "prompt_version": prompt_version,
                "system_prompt": prompt,
                "system_prompt_sha256": _producer_hash(prompt),
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "temperature": 0.1,
                "reasoning_effort": "low",
                "transport": "responses_http",
                "max_output_tokens": 900,
                "schema_name": "entry_decision_v2",
                "require_json": True,
                "response_schema_mode": "strict_dynamic_entry_risk",
                "response_schema_registry_used": True,
                "response_schema": response_schema,
                "response_schema_sha256": _producer_hash(response_schema),
                "semantic_validator_version": "entry_semantic_v1",
            },
            **AUTHORITY_CONTRACT,
        }

    control_request = request("decision_quality_v2_14", CONTROL_PROMPT)
    control_request["candidate"]["system_prompt_sha256"] = hashlib.sha256(
        CONTROL_PROMPT.encode("utf-8")
    ).hexdigest()
    materialized = materialize_micro_reversion_three_arm_requests(
        replay_control_request=control_request,
        replay_candidate_request=request("candidate_v2", "candidate prompt"),
        evidence=evidence,
        source_trace=_trace(),
        source_payload=_payload(),
        source_market_rows=_past_market_rows(),
        source_depth_rows=[_depth()],
        source_event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )

    arms = materialized["requests"]
    assert [row["micro_reversion_replay_arm"] for row in arms] == [
        "replay_control_exact_no_micro",
        "replay_control_exact_plus_micro",
        "replay_candidate_exact_plus_micro",
    ]
    assert arms[0]["candidate_input_sha256"] != arms[1]["candidate_input_sha256"]
    assert arms[1]["candidate_input_sha256"] == arms[2]["candidate_input_sha256"]
    assert len({row["paired_replay_id"] for row in arms}) == 3
    assert len({row["paired_replay_parent_id"] for row in arms}) == 1
    assert materialized["paired_replay_materialized"] is True
    assert materialized["paired_replay_ready"] is True
    assert materialized["provider_call_performed"] is False
    enriched_economics = arms[1]["candidate_input"][TACTICAL_EVIDENCE_SCHEMA][
        "economics"
    ]
    assert enriched_economics["symbol_metadata_status"] == "verified"
    assert "record" not in enriched_economics
    assert (
        "effective_qty"
        not in arms[1]["candidate_input"][TACTICAL_EVIDENCE_SCHEMA][
            "liquidity_capacity"
        ]
    )
    for row in arms:
        assert row["actual_order_submitted"] is False
        assert row["broker_order_forbidden"] is True

    stale_control = request("decision_quality_v2_14", CONTROL_PROMPT)
    stale_control["candidate"]["system_prompt_sha256"] = hashlib.sha256(
        CONTROL_PROMPT.encode("utf-8")
    ).hexdigest()
    stale_control["candidate_input_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="candidate_input_sha256_mismatch"):
        materialize_micro_reversion_three_arm_requests(
            replay_control_request=stale_control,
            replay_candidate_request=request("candidate_v2", "candidate prompt"),
            evidence=evidence,
            source_trace=_trace(),
            source_payload=_payload(),
            source_market_rows=_past_market_rows(),
            source_depth_rows=[_depth()],
            source_event_references=[_reference()],
            config=_verified_config(),
            verified_symbol_metadata=_verified_symbol_metadata(),
        )


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

    (
        krx_trace,
        krx_payload,
        krx_market,
        krx_depth,
        krx_reference,
    ) = _premarket_route_inputs(market_data_route="krx_only", integrated_proven=False)
    krx_evidence = build_tactical_evidence(
        trace=krx_trace,
        payload=krx_payload,
        market_rows=krx_market,
        depth_rows=[krx_depth],
        event_references=[krx_reference],
        config=_verified_config(),
    )
    assert krx_evidence["trace_market_data_route"] == "krx_only"
    assert krx_evidence["integrated_sor_route_proven"] is False
    assert krx_evidence["micro_venue"] == "KRX"

    (
        sor_trace,
        sor_payload,
        sor_market,
        sor_depth,
        sor_reference,
    ) = _premarket_route_inputs(
        market_data_route="krx_nxt_integrated", integrated_proven=True
    )
    sor_evidence = build_tactical_evidence(
        trace=sor_trace,
        payload=sor_payload,
        market_rows=sor_market,
        depth_rows=[sor_depth],
        event_references=[sor_reference],
        config=_verified_config(),
    )
    assert sor_evidence["trace_market_data_route"] == "krx_nxt_integrated"
    assert sor_evidence["integrated_sor_route_proven"] is True
    assert sor_evidence["micro_venue"] == "SOR"
    assert len(sor_evidence["evidence_sha256"]) == 64

    (
        blocked_trace,
        blocked_payload,
        blocked_market,
        blocked_depth,
        blocked_reference,
    ) = _premarket_route_inputs(
        market_data_route="krx_nxt_integrated", integrated_proven=False
    )
    blocked_evidence = build_tactical_evidence(
        trace=blocked_trace,
        payload=blocked_payload,
        market_rows=blocked_market,
        depth_rows=[blocked_depth],
        event_references=[blocked_reference],
        config=_verified_config(),
    )
    assert blocked_evidence["state"] == "source_unavailable"
    assert (
        "integrated_route_proof_missing"
        in blocked_evidence["source_quality"]["blockers"]
    )
    blocked_outcome = build_future_outcome(
        evidence=blocked_evidence,
        market_rows=[],
        config=_verified_config(),
    )
    assert blocked_outcome["outcome_eligibility"] == "source_unavailable"


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


def test_report_uses_purpose_specific_primary_when_first_control_is_invalid() -> None:
    first_trace = _trace()
    first_trace["timeout"] = True
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
        traces=[first_trace, second_trace],
        payloads=[_payload(), second_payload],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert report["summary"]["control_decision_eligible_primary_episode_count"] == 1
    assert (
        report["summary"]["paired_decision_quality_eligible_primary_episode_count"] == 1
    )
    by_trace = {row["decision_trace_id"]: row for row in report["rows"]}
    assert by_trace["trace-1"]["primary_parent_wave_stage_row"] is True
    assert by_trace["trace-1"]["primary_control_parent_wave_stage_row"] is False
    assert by_trace["trace-2"]["primary_control_parent_wave_stage_row"] is True
    assert report["decision"] == (
        "micro_three_arm_paired_replay_materialization_eligible"
    )
    assert report["paired_replay_materialized"] is False
    assert report["paired_replay_ready"] is False


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


def test_disk_backed_source_store_matches_in_memory_report(tmp_path) -> None:
    trace = _trace()
    payload = _payload()
    config = _verified_config()
    windows = _relevant_windows([trace], [payload], config=config)
    generated_at = datetime.fromisoformat("2026-08-14T16:00:00+09:00")
    unrelated_invalid_market = {
        **_past_market_rows()[0],
        "item": "999999",
        "symbol": "999999",
        "local_receive_timestamp": "invalid-timestamp",
    }
    invalid_reference = {**_reference(), "event_detected_at_ms": True}
    market_rows = [*_past_market_rows(), unrelated_invalid_market]
    references = [_reference(), invalid_reference]
    direct = build_bridge_report(
        target_date="2026-08-14",
        traces=[trace],
        payloads=[payload],
        market_rows=market_rows,
        depth_rows=[_depth()],
        event_references=references,
        config=config,
        generated_at=generated_at,
    )

    with _SQLiteRelevantSourceStore(
        tmp_path / "source.sqlite3", windows=windows
    ) as store:
        store.ingest("market", market_rows)
        store.ingest("depth", [_depth()])
        store.ingest("reference", references, reference_rows=True)
        store.finalize()
        indexed = build_bridge_report(
            target_date="2026-08-14",
            traces=[trace],
            payloads=[payload],
            market_rows=(),
            depth_rows=(),
            event_references=(),
            config=config,
            generated_at=generated_at,
            source_store=store,
        )

    assert indexed["bridge_contract"] == direct["bridge_contract"]
    assert indexed["rows"] == direct["rows"]
    assert indexed["summary"] == direct["summary"]
    assert direct["summary"]["noncausal_source_diagnostics"] == {
        "invalid_market_timestamp_row_count": 0,
        "invalid_depth_timestamp_row_count": 0,
        "invalid_event_reference_timestamp_row_count": 1,
        "included_in_prompt_context": False,
    }


def test_envelope_join_supports_trace_without_request_id_in_report_and_prefilter() -> (
    None
):
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


def test_bridge_report_records_outcome_only_pipeline_source_census() -> None:
    duplicate = deepcopy(_entry_pipeline_allocator_row(quantity=50))
    duplicate["stage"] = "scalp_entry_action_decision_snapshot"
    unrelated = deepcopy(_entry_pipeline_allocator_row(quantity=10))
    unrelated["fields"]["ai_decision_trace_id"] = "other-trace"
    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        entry_pipeline_rows=[
            _entry_pipeline_allocator_row(quantity=50),
            duplicate,
            unrelated,
        ],
        entry_pipeline_source={
            "status": "available_hash_verified",
            "logical_source_path": "/test/pipeline_events_2026-08-14.jsonl",
            "source_path": "/test/pipeline_events_2026-08-14.jsonl",
            "source_compression": "plain",
            "source_bytes": 123,
            "source_sha256": "c" * 64,
            "source_content_sha256": "d" * 64,
            "source_content_bytes": 456,
            "source_line_count": 3,
            "source_nonempty_line_count": 3,
            "source_json_object_row_count": 3,
            "source_snapshot_stable": True,
        },
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )

    source = report["entry_pipeline_source"]
    assert source["provider_visible"] is False
    assert source["source_sha256"] == "c" * 64
    assert source["source_content_sha256"] == "d" * 64
    assert source["source_compression"] == "plain"
    assert source["source_json_object_row_count"] == 3
    assert source["json_object_row_count"] == 3
    assert source["entry_pipeline_row_count"] == 3
    assert source["allocator_contract_row_count"] == 3
    assert source["trace_symbol_linked_row_count"] == 2
    assert report["summary"]["entry_pipeline_allocator_outcome_joined_count"] == 1
    assert report["report_row_count"] == len(report["rows"])
    assert report["report_content_sha256"] == _producer_hash(
        {key: value for key, value in report.items() if key != "report_content_sha256"}
    )

    missing = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        entry_pipeline_rows=(),
        entry_pipeline_source={
            "status": "missing_observation_only",
            "source_path": "/missing/pipeline_events_2026-08-14.jsonl",
            "source_sha256": None,
        },
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )
    assert missing["status"] == "warning"
    assert missing["entry_pipeline_source"]["outcome_join_mode"] == (
        "standardized_one_share_observation_only"
    )
    missing_outcome = missing["rows"][0]["future_outcome"]
    assert missing_outcome["counterfactual_quantity"] == 1
    assert missing_outcome["notional_net_profit_eligible"] is False

    unverified_programmatic = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        entry_pipeline_rows=[_entry_pipeline_allocator_row(quantity=50)],
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )
    assert unverified_programmatic["entry_pipeline_source"]["status"] == (
        "programmatic_rows_source_unspecified"
    )
    assert (
        unverified_programmatic["entry_pipeline_source"]["outcome_join_mode"]
        == "standardized_one_share_observation_only"
    )
    unverified_outcome = unverified_programmatic["rows"][0]["future_outcome"]
    assert unverified_outcome["allocator_event_sha256"] is None
    assert unverified_outcome["notional_net_profit_eligible"] is False

    with pytest.raises(ValueError, match="entry_pipeline_source_census_mismatch"):
        build_bridge_report(
            target_date="2026-08-14",
            traces=[],
            payloads=[],
            market_rows=(),
            depth_rows=(),
            event_references=(),
            entry_pipeline_rows=[_entry_pipeline_allocator_row(quantity=5)],
            entry_pipeline_source={
                "status": "available_hash_verified",
                "logical_source_path": "/test/pipeline_events_2026-08-14.jsonl",
                "source_path": "/test/pipeline_events_2026-08-14.jsonl",
                "source_compression": "plain",
                "source_bytes": 123,
                "source_sha256": "c" * 64,
                "source_content_sha256": "d" * 64,
                "source_content_bytes": 456,
                "source_line_count": 2,
                "source_nonempty_line_count": 2,
                "source_json_object_row_count": 2,
                "source_snapshot_stable": True,
            },
        )


def test_cli_defaults_pipeline_path_and_missing_source_to_observation_only(
    tmp_path, monkeypatch
) -> None:
    data_dir = tmp_path / "data"
    trace_path = data_dir / "ai_decision_trace" / "ai_decision_trace_2026-08-14.jsonl"
    payload_path = (
        data_dir / "ai_decision_payloads" / "ai_decision_payloads_2026-08-14.jsonl"
    )
    pipeline_path = data_dir / "pipeline_events" / "pipeline_events_2026-08-14.jsonl"
    for path in (trace_path, payload_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    pipeline_path.parent.mkdir(parents=True, exist_ok=True)
    pipeline_bytes = (
        json.dumps(
            _entry_pipeline_allocator_row(quantity=5),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    pipeline_path.write_bytes(pipeline_bytes)

    def fake_iter(paths):
        selected_paths = tuple(paths)
        if not selected_paths:
            return iter(())
        path = selected_paths[0]
        if "ai_decision_trace" in path.name:
            return iter([_trace()])
        if "ai_decision_payloads" in path.name:
            return iter([_payload()])
        if "pipeline_events" in path.name:
            return iter([_entry_pipeline_allocator_row(quantity=5)])
        return iter(())

    captured = []

    def fake_report(**kwargs):
        captured.append(
            {
                "rows": list(kwargs["entry_pipeline_rows"]),
                "source": kwargs["entry_pipeline_source"],
                "config": kwargs["config"],
                "metadata": kwargs["verified_symbol_metadata_by_trace"],
            }
        )
        return {"status": "warning", "decision": "test", "summary": {}}

    monkeypatch.setattr(bridge_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(bridge_module, "_iter_jsonl", fake_iter)
    monkeypatch.setattr(
        bridge_module,
        "load_source_exclusion_manifest",
        lambda _path: {"exclusions": []},
    )
    monkeypatch.setattr(bridge_module, "build_bridge_report", fake_report)

    assert bridge_module.main(["--date", "2026-08-14"]) == 0
    assert captured[0]["rows"][0]["pipeline"] == "ENTRY_PIPELINE"
    assert captured[0]["source"]["status"] == "available_hash_verified"
    assert captured[0]["source"]["logical_source_path"] == str(pipeline_path)
    assert captured[0]["source"]["source_path"] == str(pipeline_path)
    assert captured[0]["source"]["source_compression"] == "plain"
    assert (
        captured[0]["source"]["source_sha256"]
        == hashlib.sha256(pipeline_bytes).hexdigest()
    )
    assert (
        captured[0]["source"]["source_content_sha256"]
        == hashlib.sha256(pipeline_bytes).hexdigest()
    )
    assert captured[0]["source"]["source_bytes"] == len(pipeline_bytes)
    assert captured[0]["source"]["source_content_bytes"] == len(pipeline_bytes)
    assert captured[0]["source"]["source_line_count"] == 1
    assert captured[0]["source"]["source_nonempty_line_count"] == 1
    assert captured[0]["source"]["source_json_object_row_count"] == 1
    assert captured[0]["source"]["source_snapshot_stable"] is True

    for path, content in (
        (trace_path, b"{}\n"),
        (payload_path, b"{}\n"),
        (pipeline_path, pipeline_bytes),
    ):
        gzip_path = path.with_name(path.name + ".gz")
        with gzip.open(gzip_path, "wb") as handle:
            handle.write(content)
        path.unlink()
    pipeline_gzip_path = pipeline_path.with_name(pipeline_path.name + ".gz")

    assert bridge_module.main(["--date", "2026-08-14"]) == 0
    assert captured[1]["rows"][0]["pipeline"] == "ENTRY_PIPELINE"
    assert captured[1]["source"]["logical_source_path"] == str(pipeline_path)
    assert captured[1]["source"]["source_path"] == str(pipeline_gzip_path)
    assert captured[1]["source"]["source_compression"] == "gzip"
    assert (
        captured[1]["source"]["source_sha256"]
        == hashlib.sha256(pipeline_gzip_path.read_bytes()).hexdigest()
    )
    assert (
        captured[1]["source"]["source_content_sha256"]
        == hashlib.sha256(pipeline_bytes).hexdigest()
    )
    assert captured[1]["source"]["source_bytes"] == (pipeline_gzip_path.stat().st_size)
    assert captured[1]["source"]["source_content_bytes"] == len(pipeline_bytes)

    assert (
        bridge_module.main(
            [
                "--date",
                "2026-08-14",
                "--entry-pipeline",
                str(pipeline_path),
            ]
        )
        == 0
    )
    assert captured[2]["source"]["source_path"] == str(pipeline_gzip_path)

    pipeline_gzip_path.unlink()
    assert bridge_module.main(["--date", "2026-08-14"]) == 0
    assert captured[3]["rows"] == []
    assert captured[3]["source"]["status"] == "missing_observation_only"
    assert captured[3]["source"]["logical_source_path"] == str(pipeline_path)

    cost_profile_path = tmp_path / "verified_cost_profile.json"
    cost_profile_path.write_text(
        _verified_config().cost_profile_artifact_payload_json,
        encoding="utf-8",
    )
    symbol_master_path = tmp_path / "verified_symbol_master.json"
    symbol_master_path.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_symbol_master_v1",
                "decision_authority": "instrument_metadata_source_only",
                "runtime_effect": False,
                "records": [_verified_symbol_metadata()["record"]],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert (
        bridge_module.main(
            [
                "--date",
                "2026-08-14",
                "--verified-cost-profile",
                str(cost_profile_path),
                "--symbol-master",
                str(symbol_master_path),
            ]
        )
        == 0
    )
    assert captured[4]["config"].cost_profile_verified is True
    assert captured[4]["metadata"]["trace-1"]["lookup_status"] == "verified"
    assert captured[4]["metadata"]["trace-1"]["record"]["instrument_type"] == "EQUITY"


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
