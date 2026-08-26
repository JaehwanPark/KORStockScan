from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path

import pytest

from src.engine.scalping import ai_decision_trace as trace_producer
from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge_module
from src.engine.scalping.micro_reversion.ai_quality_bridge import (
    ASK_DEPLETION_FEATURE_VIEW_SCHEMA,
    AUTHORITY_CONTRACT,
    LIFECYCLE_PROJECTION_SCHEMA,
    TACTICAL_EVIDENCE_SCHEMA,
    BridgeConfig,
    _SQLiteRelevantSourceStore,
    _cleanup_relevant_source_cache,
    _economics,
    _control_decision_findings,
    _lifecycle_projection,
    _liquidity_projection,
    _position_context,
    _relevant_windows,
    _sha256,
    attach_micro_context_to_replay_request,
    build_ask_depletion_feature_sidecar,
    build_bridge_report,
    build_future_outcome,
    build_tactical_evidence,
    build_three_arm_manifest,
    materialize_micro_reversion_three_arm_requests,
    open_relevant_source_store,
    resolve_micro_scope,
)
from src.engine.scalping.micro_reversion.replay_ablation_contract import (
    CURRENT_ARMS,
    CURRENT_DESIGN_VERSION,
    LEGACY_DESIGN_VERSION,
    SOURCE_ONLY_AUTHORITY_CONTRACT,
)
from src.utils.jsonl_io import read_json_object_strict

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


def _ask_depletion_depth_path() -> list[dict]:
    def row(timestamp: str, sequence: int, quantities: tuple[int, ...]) -> dict:
        value = _depth(timestamp, sequence=sequence)
        ask_prices = tuple(9_960.0 + index * 10.0 for index in range(5))
        ask_depth = sum(quantities)
        value.update(
            {
                "best_ask_qty": quantities[0],
                "ask_depth": ask_depth,
                "ask_levels": [
                    [index, price, quantity]
                    for index, (price, quantity) in enumerate(
                        zip(ask_prices, quantities, strict=True), start=1
                    )
                ],
                "route_depth_totals": {
                    "KRX": {"bid": 1_000, "ask": ask_depth},
                    "NXT": {"bid": 0, "ask": 0},
                    "combined": {"bid": 1_000, "ask": ask_depth},
                },
            }
        )
        return value

    return [
        row("2026-08-14T09:00:05.900+09:00", 1, (100, 200, 300, 400, 500)),
        row("2026-08-14T09:00:06.250+09:00", 2, (80, 180, 280, 380, 480)),
        row("2026-08-14T09:00:06.500+09:00", 3, (60, 160, 260, 360, 460)),
        row("2026-08-14T09:00:06.700+09:00", 4, (70, 170, 270, 370, 470)),
        row("2026-08-14T09:00:07.000+09:00", 5, (80, 180, 280, 380, 480)),
        row("2026-08-14T09:00:07.500+09:00", 6, (90, 190, 290, 390, 490)),
        row("2026-08-14T09:00:08.999+09:00", 7, (90, 190, 290, 390, 490)),
    ]


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


def _complete_ask_depletion_paths() -> tuple[list[dict], list[dict]]:
    market_rows = [
        *_past_market_rows(),
        _market(
            "2026-08-14T09:00:11.000+09:00",
            price=9_970,
            side="BUY",
            qty=100,
            sequence=5,
            bid=9_960,
            ask=9_970,
        ),
        _market(
            "2026-08-14T09:00:16.000+09:00",
            price=9_980,
            side="BUY",
            qty=100,
            sequence=6,
            bid=9_970,
            ask=9_980,
        ),
    ]
    depth_rows = _ask_depletion_depth_path()
    for timestamp, sequence in (
        ("2026-08-14T09:00:10.999+09:00", 8),
        ("2026-08-14T09:00:15.999+09:00", 9),
    ):
        row = deepcopy(depth_rows[-1])
        row.update(
            {
                "source_sequence": sequence,
                "series_sequence": sequence,
                "exchange_timestamp": timestamp,
                "local_receive_timestamp": timestamp,
            }
        )
        depth_rows.append(row)
    return market_rows, depth_rows


def _complete_ask_depletion_feature_fixture() -> tuple[dict, dict, dict]:
    captured_at = "2026-08-14T09:00:16.000+09:00"
    trace = _trace(captured_at=captured_at)
    trace["decision_ts"] = "2026-08-14T09:00:17.000+09:00"
    market_rows, depth_rows = _complete_ask_depletion_paths()
    for row, best_bid, best_ask in (
        (depth_rows[-2], 9_960.0, 9_970.0),
        (depth_rows[-1], 9_970.0, 9_980.0),
    ):
        row["best_bid"] = best_bid
        row["best_ask"] = best_ask
        row["bid_levels"] = [
            [level[0], best_bid - (level[0] - 1) * 10.0, level[2]]
            for level in row["bid_levels"]
        ]
        row["ask_levels"] = [
            [level[0], best_ask + (level[0] - 1) * 10.0, level[2]]
            for level in row["ask_levels"]
        ]
    evidence = build_tactical_evidence(
        trace=trace,
        payload=_payload(captured_at=captured_at),
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    sidecar = build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=market_rows,
        depth_rows=depth_rows,
    )
    feature = bridge_module._validated_ask_depletion_feature_view(
        sidecar,
        evidence=evidence,
    )
    return evidence, sidecar, feature


def _reseal_ask_depletion_feature(evidence: dict, feature: dict) -> None:
    evidence["evidence_sha256"] = _sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )
    feature["tactical_micro_reversion_evidence_sha256"] = evidence["evidence_sha256"]
    reconstructed_sidecar = {
        "context": deepcopy(feature["context"]),
        "anchor_source_sequence": feature["anchor_source_sequence"],
        **deepcopy(dict(feature["sidecar_hash_reconstruction"])),
        "horizons": deepcopy(feature["eligible_horizons"]),
        "schema": bridge_module.ASK_DEPLETION_SCHEMA,
        **bridge_module.ASK_DEPLETION_SIDECAR_AUTHORITY,
        **bridge_module.ASK_DEPLETION_METRIC_CONTRACT,
        "tactical_micro_reversion_evidence_sha256": evidence["evidence_sha256"],
        "ask_depletion_contract_sha256": feature["ask_depletion_contract_sha256"],
    }
    feature["ask_depletion_context_sha256"] = _sha256(reconstructed_sidecar)
    feature["feature_view_sha256"] = _sha256(
        {key: value for key, value in feature.items() if key != "feature_view_sha256"}
    )


def _verified_config(*, max_outcome_internal_gap_ms: int = 2_500) -> BridgeConfig:
    artifact_id = "test-cost-profile-2026-08-14"
    artifact = {
        "schema": "micro_reversion_reviewed_cost_profile_v1",
        "artifact_id": artifact_id,
        "effective_date": "2026-08-14",
        "venues": ["KRX", "NXT", "SOR"],
        "instrument_scope": "domestic_common_or_preferred_stock",
        "source": f"canonical_economic_reference_v2:{artifact_id}",
        "buy_fee_bps": 0.0,
        "sell_fee_bps": 0.0,
        "statutory_sell_tax_bps": 20.0,
        "uncertainty_buffer_bps": 3.0,
        **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
    return BridgeConfig(
        max_outcome_internal_gap_ms=max_outcome_internal_gap_ms,
        statutory_sell_tax_bps=20.0,
        uncertainty_buffer_bps=3.0,
        cost_profile_source=f"canonical_economic_reference_v2:{artifact_id}",
        cost_profile_verified=True,
        cost_profile_artifact_id=artifact_id,
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


def _canonical_symbol_master_payload(*, symbol: str = "000001") -> dict:
    source_hash = "b" * 64
    logical_path = "policy://micro-reversion/symbol_product_master.json"
    record = deepcopy(_verified_symbol_metadata(symbol=symbol)["record"])
    record.update(
        {
            "metadata_source": "official_symbol_product_master_v2",
            "source_reference": f"{logical_path}#sha256={source_hash}",
        }
    )
    body = {
        "schema": "scalp_micro_reversion_symbol_master_v1",
        "artifact_id": "main-ai-economic-reference-2026-08-25-symbol-master",
        "source_contract_schema": "micro_reversion_raw_symbol_product_master_v3",
        "verification_status": "verified",
        "verified": True,
        "decision_authority": "instrument_metadata_source_only",
        **{
            key: value
            for key, value in bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY.items()
            if key != "decision_authority"
        },
        "source_artifacts": [
            {
                "source_id": "kis-official-common-stock-master-2026-08-25",
                "kind": "symbol_product_master",
                "logical_path": logical_path,
                "expected_sha256": source_hash,
                "expected_size_bytes": 100,
                "observed_sha256": source_hash,
                "observed_size_bytes": 100,
                "record_count": 1,
                "payload_schema": "micro_reversion_raw_symbol_product_master_v3",
                "status": "verified",
                "verified": True,
                "blockers": [],
                **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
            }
        ],
        "census": {"record_count": 1, "symbol_count": 1},
        "records": [record],
    }
    return {**body, "content_sha256": _producer_hash(body)}


def _current_cost_catalog_payload(
    *,
    buy_fee_bps: float = 1.5,
    sell_fee_bps: float = 1.5,
    statutory_sell_tax_bps: float = 20.0,
) -> dict:
    profile_id = "economic-reference-v2-current-test"
    bridge_payload = {
        "schema": bridge_module.COST_PROFILE_SCHEMA,
        "artifact_id": profile_id,
        "effective_date": "2026-08-18",
        "venues": ["KRX"],
        "instrument_scope": "domestic_common_or_preferred_stock",
        "source": f"canonical_economic_reference_v2:{profile_id}",
        "buy_fee_bps": buy_fee_bps,
        "sell_fee_bps": sell_fee_bps,
        "statutory_sell_tax_bps": statutory_sell_tax_bps,
        "uncertainty_buffer_bps": 0.0,
        **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
    profile_body = {
        "profile_id": profile_id,
        "effective_from": "2026-08-18",
        "effective_to": None,
        "venues": ["KRX"],
        "listing_markets": ["KOSPI"],
        "instrument_types": ["EQUITY"],
        "instrument_tax_classes": ["ordinary_taxable_equity_20bps"],
        "buy_fee_bps": buy_fee_bps,
        "sell_fee_bps": sell_fee_bps,
        "statutory_sell_tax_bps": statutory_sell_tax_bps,
        "uncertainty_buffer_bps": 0.0,
        "source_bindings": {
            "symbol_master_source_id": "kis-official-common-stock-master-2026-08-25",
            "symbol_master_source_sha256": "1" * 64,
            "broker_fee_source_id": "operator-reviewed-kiwoom-fee-2026-08-18",
            "broker_fee_source_sha256": "2" * 64,
            "broker_fee_record_sha256": "3" * 64,
            "statutory_tax_source_id": "operator-reviewed-statutory-tax-2026-08-18",
            "statutory_tax_source_sha256": "4" * 64,
            "statutory_tax_record_sha256": "5" * 64,
        },
        "bridge_reviewed_cost_payload": bridge_payload,
        "bridge_reviewed_cost_payload_sha256": _producer_hash(bridge_payload),
        "verification_status": "verified",
        "verified": True,
        **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
    profile = {**profile_body, "content_sha256": _producer_hash(profile_body)}
    catalog_body = {
        "schema": bridge_module.COST_CATALOG_SCHEMA,
        "artifact_id": "main-ai-economic-reference-2026-08-25-cost-catalog",
        "target_date": "2026-08-25",
        "verification_status": "verified",
        "verified": True,
        "profile_count": 1,
        "census": {
            "profile_count": 1,
            "venue_count": 1,
            "listing_market_count": 1,
            "instrument_type_count": 1,
            "instrument_tax_class_count": 1,
        },
        "profiles": [profile],
        **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
    return {**catalog_body, "content_sha256": _producer_hash(catalog_body)}


def _entry_pipeline_allocator_row(
    *,
    quantity: int = 50,
    formula_version: str = "entry_type_5stage_cap25_v1",
    stage: str = "order_bundle_submitted",
    broker_order_no: str = "0000101",
    submitted_qty: int | None = None,
) -> dict:
    exact_submitted_qty = quantity if submitted_qty is None else submitted_qty
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
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
            "actual_order_submitted": True,
            "broker_order_no": broker_order_no,
            "order_no": broker_order_no,
            "submitted_qty": exact_submitted_qty,
            "submitted_leg_count": 1,
            "broker_order_qty_list": f"{broker_order_no}:{exact_submitted_qty}",
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
    assert "confirmation_window_axis" not in evidence["event"]
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


def test_confirmation_window_is_future_label_not_prompt_context() -> None:
    config = _verified_config(max_outcome_internal_gap_ms=30_000)
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=config,
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    future_rows = [
        _market(
            "2026-08-14T09:01:06.000+09:00",
            price=9_800,
            side="SELL",
            qty=100,
            sequence=5,
        ),
        _market(
            "2026-08-14T09:02:05.000+09:00",
            price=9_950,
            side="BUY",
            qty=100,
            sequence=6,
        ),
        _market(
            "2026-08-14T09:02:06.000+09:00",
            price=9_950,
            side="BUY",
            qty=100,
            sequence=7,
        ),
        _market(
            "2026-08-14T09:02:36.000+09:00",
            price=9_700,
            side="SELL",
            qty=100,
            sequence=8,
        ),
        _market(
            "2026-08-14T09:03:06.000+09:00",
            price=9_800,
            side="BUY",
            qty=100,
            sequence=9,
        ),
    ]

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[*_past_market_rows(), *future_rows],
        config=config,
    )

    assert "confirmation_window_axis" not in evidence["event"]
    axis = outcome["confirmation_window_axis"]
    assert axis["axis_role"] == "micro_reversion_tuning_only"
    assert axis["horizons_sec"] == [120, 180]
    assert axis["followthrough_horizons_sec"] == [30, 60]
    assert axis["confirmation_fraction"] == 0.5
    assert axis["included_in_prompt_context"] is False
    assert axis["runtime_effect"] is False
    assert axis["selection_authority"] is False
    assert [row["direction_state"] for row in axis["observations"]] == [
        "REVERSION_CONFIRMED",
        "CONTINUATION_CONFIRMED",
    ]
    assert all(row["classification_eligible"] for row in axis["observations"])
    assert axis["observations"][0]["active_confirmation_delay_ms"] == 119_000
    fixed = axis["observations"][0]["fixed_followthrough_outcomes"]
    assert [row["followthrough_sec"] for row in fixed] == [30, 60]
    assert all(row["tuning_outcome_eligible"] is True for row in fixed)
    assert fixed[0]["entry_delay_from_confirmation_ms"] == 0
    assert fixed[0]["standardized_one_share_net_return_bps"] == pytest.approx(
        -284.306533
    )
    assert all(
        row["tuning_outcome_eligible"] is False
        for row in axis["observations"][1]["fixed_followthrough_outcomes"]
    )


def test_confirmation_window_marks_invalid_endpoint_as_source_gap() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    invalid_marker = _market(
        "2026-08-14T09:02:07.000+09:00",
        price=9_940,
        side="BUY",
        qty=100,
        sequence=6,
    )
    invalid_marker["realtime_type"] = "INVALID"

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[
            *_past_market_rows(),
            _market(
                "2026-08-14T09:01:46.000+09:00",
                price=9_900,
                side="SELL",
                qty=100,
                sequence=5,
            ),
            invalid_marker,
        ],
        config=_verified_config(),
    )

    observation = outcome["confirmation_window_axis"]["observations"][0]
    assert observation["horizon_sec"] == 120
    assert observation["mature"] is True
    assert observation["classification_eligible"] is False
    assert observation["direction_state"] == "SOURCE_GAP"
    assert observation["source_quality_blockers"] == [
        "confirmation_invalid_market_row_in_path"
    ]


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
    ("field", "value", "expected_error"),
    [
        ("buy_fee_bps", True, "verified_cost_profile_numeric_invalid:buy_fee_bps"),
        (
            "sell_fee_bps",
            "0.0",
            "verified_cost_profile_numeric_invalid:sell_fee_bps",
        ),
        (
            "statutory_sell_tax_bps",
            -1.0,
            "verified_cost_profile_numeric_invalid:statutory_sell_tax_bps",
        ),
        ("uncertainty_buffer_bps", float("nan"), "non-finite JSON number:NaN"),
    ],
)
def test_verified_cost_artifact_rejects_non_native_or_nonfinite_numbers(
    tmp_path, field, value, expected_error
) -> None:
    artifact = json.loads(_verified_config().cost_profile_artifact_payload_json)
    artifact[field] = value
    path = tmp_path / "invalid_cost_profile.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match=expected_error):
        bridge_module._verified_cost_config_from_path(
            path, target_date=datetime.fromisoformat("2026-08-14").date()
        )


@pytest.mark.parametrize(
    ("unsafe_generation", "expected_error"),
    (
        ("broken_symlink", "json_artifact_path_type_invalid"),
        ("duplicate_key", "duplicate JSON key:schema"),
        ("divergent_plain_gzip", "json_artifact_plain_gzip_conflict"),
    ),
)
def test_verified_cost_artifact_strict_reader_rejects_unsafe_generation(
    tmp_path: Path,
    unsafe_generation: str,
    expected_error: str,
) -> None:
    path = tmp_path / "verified_cost_profile.json"
    payload = json.loads(_verified_config().cost_profile_artifact_payload_json)
    if unsafe_generation == "broken_symlink":
        path.symlink_to(tmp_path / "missing-cost-profile.json")
    elif unsafe_generation == "duplicate_key":
        path.write_text(
            '{"schema":"micro_reversion_reviewed_cost_profile_v1",'
            '"schema":"micro_reversion_reviewed_cost_profile_v1"}',
            encoding="utf-8",
        )
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
        divergent = {**payload, "buy_fee_bps": 99.0}
        path.with_name(f"{path.name}.gz").write_bytes(
            gzip.compress(json.dumps(divergent).encode("utf-8"))
        )

    with pytest.raises(ValueError, match=expected_error):
        bridge_module._verified_cost_config_from_path(
            path,
            target_date=datetime.fromisoformat("2026-08-14").date(),
        )


def test_verified_cost_catalog_resolves_symbol_and_venue_specific_profile(
    tmp_path,
) -> None:
    def profile(*, venue: str, buy_fee_bps: float) -> dict:
        profile_id = f"profile-{venue.lower()}"
        bridge_payload = {
            "schema": bridge_module.COST_PROFILE_SCHEMA,
            "artifact_id": profile_id,
            "effective_date": "2026-08-01",
            "venues": [venue],
            "instrument_scope": "domestic_common_or_preferred_stock",
            "source": f"canonical_economic_reference_v2:{profile_id}",
            "buy_fee_bps": buy_fee_bps,
            "sell_fee_bps": 0.2,
            "statutory_sell_tax_bps": 20.0,
            "uncertainty_buffer_bps": 3.0,
            **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
        }
        body = {
            "profile_id": profile_id,
            "effective_from": "2026-08-01",
            "effective_to": None,
            "venues": [venue],
            "listing_markets": ["KOSPI"],
            "instrument_types": ["EQUITY"],
            "instrument_tax_classes": ["ordinary_taxable_equity_20bps"],
            "buy_fee_bps": buy_fee_bps,
            "sell_fee_bps": 0.2,
            "statutory_sell_tax_bps": 20.0,
            "uncertainty_buffer_bps": 3.0,
            "source_bindings": {
                "symbol_master_source_id": "test-symbol-source",
                "symbol_master_source_sha256": "1" * 64,
                "broker_fee_source_id": "test-broker-source",
                "broker_fee_source_sha256": "2" * 64,
                "broker_fee_record_sha256": "3" * 64,
                "statutory_tax_source_id": "test-tax-source",
                "statutory_tax_source_sha256": "4" * 64,
                "statutory_tax_record_sha256": "5" * 64,
            },
            "bridge_reviewed_cost_payload": bridge_payload,
            "bridge_reviewed_cost_payload_sha256": _producer_hash(bridge_payload),
            "verification_status": "verified",
            "verified": True,
            **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
        }
        return {**body, "content_sha256": _producer_hash(body)}

    profiles = [
        profile(venue="KRX", buy_fee_bps=0.1),
        profile(venue="NXT", buy_fee_bps=0.7),
    ]
    body = {
        "schema": bridge_module.COST_CATALOG_SCHEMA,
        "artifact_id": "catalog-2026-08-14",
        "target_date": "2026-08-14",
        "verification_status": "verified",
        "verified": True,
        "profile_count": len(profiles),
        "census": {
            "profile_count": len(profiles),
            "venue_count": 2,
            "listing_market_count": 1,
            "instrument_type_count": 1,
            "instrument_tax_class_count": 1,
        },
        "profiles": profiles,
        **bridge_module._ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
    catalog = {**body, "content_sha256": _producer_hash(body)}
    path = tmp_path / "reviewed_cost_catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")

    config = bridge_module._verified_cost_config_from_path(
        path, target_date=datetime.fromisoformat("2026-08-14").date()
    )
    metadata = {
        "symbol_metadata_status": "verified",
        "listing_market": "KOSPI",
        "instrument_type": "EQUITY",
        "instrument_tax_class": "ordinary_taxable_equity_20bps",
    }
    krx = _economics(
        liquidity={"counterfactual_liquidity_qty_grid": []},
        config=config,
        venue="KRX",
        snapshot_date="2026-08-14",
        symbol_metadata=metadata,
    )
    nxt = _economics(
        liquidity={"counterfactual_liquidity_qty_grid": []},
        config=config,
        venue="NXT",
        snapshot_date="2026-08-14",
        symbol_metadata=metadata,
    )

    assert krx["cost_profile_verified"] is True
    assert krx["selected_cost_profile_id"] == "profile-krx"
    assert krx["buy_fee_bps"] == pytest.approx(0.1)
    assert nxt["cost_profile_verified"] is True
    assert nxt["selected_cost_profile_id"] == "profile-nxt"
    assert nxt["buy_fee_bps"] == pytest.approx(0.7)
    assert krx["cost_profile_artifact_sha256"] == nxt["cost_profile_artifact_sha256"]


def test_current_reviewed_cost_catalog_enforces_operator_values() -> None:
    payload = _current_cost_catalog_payload()

    config = bridge_module._verified_cost_config_from_payload(
        payload,
        target_date=datetime.fromisoformat("2026-08-25").date(),
    )

    assert config.cost_profile_verified is True
    assert config.cost_profile_catalog_content_sha256 == payload["content_sha256"]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("buy_fee_bps", 1.4),
        ("sell_fee_bps", 1.4),
        ("statutory_sell_tax_bps", 19.0),
        ("uncertainty_buffer_bps", 0.1),
    ),
)
def test_current_resealed_fabricated_catalog_cost_is_rejected(
    field: str,
    value: float,
) -> None:
    payload = _current_cost_catalog_payload()
    profile = payload["profiles"][0]
    profile[field] = value
    bridge_payload = profile["bridge_reviewed_cost_payload"]
    bridge_payload[field] = value
    profile["bridge_reviewed_cost_payload_sha256"] = _producer_hash(bridge_payload)
    profile["content_sha256"] = _producer_hash(
        {key: item for key, item in profile.items() if key != "content_sha256"}
    )
    payload["content_sha256"] = _producer_hash(
        {key: item for key, item in payload.items() if key != "content_sha256"}
    )

    with pytest.raises(ValueError, match=f"reviewed_value_mismatch:{field}"):
        bridge_module._verified_cost_config_from_payload(
            payload,
            target_date=datetime.fromisoformat("2026-08-25").date(),
        )


def test_current_resealed_fabricated_catalog_source_binding_is_rejected() -> None:
    payload = _current_cost_catalog_payload()
    profile = payload["profiles"][0]
    profile["source_bindings"]["broker_fee_source_id"] = "fabricated-fee-source"
    profile["content_sha256"] = _producer_hash(
        {key: item for key, item in profile.items() if key != "content_sha256"}
    )
    payload["content_sha256"] = _producer_hash(
        {key: item for key, item in payload.items() if key != "content_sha256"}
    )

    with pytest.raises(
        ValueError,
        match="verified_cost_catalog_reviewed_source_binding_invalid",
    ):
        bridge_module._verified_cost_config_from_payload(
            payload,
            target_date=datetime.fromisoformat("2026-08-25").date(),
        )


def test_current_direct_legacy_cost_contract_is_exact_and_policy_pinned() -> None:
    payload = deepcopy(
        _current_cost_catalog_payload()["profiles"][0]["bridge_reviewed_cost_payload"]
    )
    config = bridge_module._verified_cost_config_from_payload(
        payload,
        target_date=datetime.fromisoformat("2026-08-25").date(),
    )
    assert config.buy_fee_bps == pytest.approx(1.5)
    assert config.sell_fee_bps == pytest.approx(1.5)
    assert config.statutory_sell_tax_bps == pytest.approx(20.0)
    assert config.cost_profile_verified is True

    fabricated = deepcopy(payload)
    fabricated["provider_cost_usd"] = 1.0
    with pytest.raises(ValueError, match="verified_cost_profile_fields_invalid"):
        bridge_module._verified_cost_config_from_payload(
            fabricated,
            target_date=datetime.fromisoformat("2026-08-25").date(),
        )

    buffered = deepcopy(payload)
    buffered["uncertainty_buffer_bps"] = 0.1
    with pytest.raises(
        ValueError,
        match="reviewed_value_mismatch:uncertainty_buffer_bps",
    ):
        bridge_module._verified_cost_config_from_payload(
            buffered,
            target_date=datetime.fromisoformat("2026-08-25").date(),
        )

    historical_config = _verified_config()
    with pytest.raises(
        ValueError,
        match="verified_cost_profile_effective_before_reviewed_policy",
    ):
        _economics(
            liquidity={"counterfactual_liquidity_qty_grid": []},
            config=historical_config,
            venue="KRX",
            snapshot_date="2026-08-25",
            symbol_metadata={
                "symbol_metadata_status": "verified",
                "listing_market": "KOSPI",
                "instrument_type": "EQUITY",
                "instrument_tax_class": "ordinary_taxable_equity_20bps",
            },
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


def test_missing_snapshot_date_is_row_local_observation_only_with_symbol_master() -> (
    None
):
    evidence = build_tactical_evidence(
        trace=_trace(captured_at=""),
        payload=_payload(captured_at=""),
        market_rows=[],
        depth_rows=[],
        event_references=[],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )

    assert evidence["state"] == "source_unavailable"
    assert evidence["economics"]["symbol_metadata_status"] == "missing"
    assert "verified_symbol_metadata_snapshot_date_unavailable" in (
        evidence["source_quality"]["blockers"]
    )
    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        depth_rows=[],
        entry_pipeline_rows=[],
        config=_verified_config(),
    )
    assert outcome["economic_promotion_evidence_eligible"] is False


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
        verified_symbol_metadata=_verified_symbol_metadata(),
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
    mature_horizons = [row for row in outcome["horizons"] if row["mature"] is True]
    assert mature_horizons
    assert all(
        row["action_neutral_executable_end_return_bps"] is not None
        and len(row["action_neutral_path_sha256"]) == 64
        for row in mature_horizons
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


def test_entry_outcome_allocator_conflict_isolated_as_observation_only() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[
            _entry_pipeline_allocator_row(quantity=5),
            _entry_pipeline_allocator_row(quantity=6),
        ],
        config=_verified_config(),
    )

    assert outcome["counterfactual_quantity"] == 1
    assert outcome["counterfactual_quantity_basis"] == (
        "standardized_one_share_observation_only"
    )
    assert outcome["quantity_authority"] == ("standardized_one_share_observation_only")
    assert outcome["allocator_event_sha256"] is None
    assert outcome["effective_qty"] is None
    assert outcome["allocator_semantic_count"] == 2
    assert outcome["allocator_submitted_semantic_count"] == 2
    assert outcome["notional_net_profit_eligible"] is False
    assert outcome["economic_promotion_evidence_eligible"] is False


def test_entry_outcome_conflict_uses_unique_broker_submitted_quantity() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    initial = _entry_pipeline_allocator_row(quantity=50)
    initial["stage"] = "ai_confirmed"
    initial["fields"]["actual_order_submitted"] = False
    submitted = _entry_pipeline_allocator_row(quantity=40)
    submitted["stage"] = "order_bundle_submitted"
    submitted["emitted_at"] = "2026-08-14T09:00:12.100+09:00"
    submitted["fields"]["actual_order_submitted"] = True

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[initial, submitted],
        config=_verified_config(),
    )

    assert outcome["effective_qty"] == 40
    assert outcome["quantity_authority"] == (
        "position_sizing_dynamic_formula_outcome_only"
    )
    assert outcome["allocator_semantic_count"] == 2
    assert outcome["allocator_submitted_semantic_count"] == 1
    assert outcome["notional_net_profit_eligible"] is True


def test_entry_outcome_intended_but_not_submitted_qty_is_observation_only() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    intended = _entry_pipeline_allocator_row(quantity=50)
    intended["stage"] = "ai_confirmed"
    intended["fields"]["actual_order_submitted"] = False
    intended["fields"].pop("broker_order_no")

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[intended],
        config=_verified_config(),
    )

    assert outcome["allocator_provenance_status"] == (
        "allocator_provenance_not_submitted_observation_only"
    )
    assert outcome["counterfactual_quantity"] == 1
    assert outcome["effective_qty"] is None
    assert outcome["economic_promotion_evidence_eligible"] is False


def test_probe_only_submission_cannot_claim_full_allocator_notional() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    probe = _entry_pipeline_allocator_row(
        quantity=40,
        stage="probe_submitted",
        submitted_qty=1,
    )

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[probe],
        config=_verified_config(),
    )

    assert outcome["allocator_provenance_status"] == (
        "allocator_provenance_partial_submission_observation_only"
    )
    assert outcome["counterfactual_quantity"] == 1
    assert outcome["effective_qty"] is None
    assert outcome["allocator_submitted_qty"] == 1
    assert outcome["allocator_submission_coverage_pct"] == pytest.approx(2.5)
    assert outcome["allocator_fully_submitted_semantic_count"] == 0
    assert outcome["notional_net_profit_eligible"] is False
    assert outcome["economic_promotion_evidence_eligible"] is False


def test_probe_and_residual_exact_orders_unlock_allocator_outcome_only() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    probe = _entry_pipeline_allocator_row(
        quantity=40,
        stage="probe_submitted",
        broker_order_no="0000101",
        submitted_qty=1,
    )
    duplicate_leg = deepcopy(probe)
    duplicate_leg["stage"] = "order_leg_sent"
    duplicate_leg["emitted_at"] = "2026-08-14T09:00:11.200+09:00"
    residual = _entry_pipeline_allocator_row(
        quantity=40,
        stage="residual_submitted",
        broker_order_no="0000102",
        submitted_qty=39,
    )
    residual["emitted_at"] = "2026-08-14T09:00:12.100+09:00"

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[probe, duplicate_leg, residual],
        config=_verified_config(),
    )

    assert outcome["allocator_provenance_status"] == (
        "central_allocator_provenance_joined"
    )
    assert outcome["effective_qty"] == 40
    assert outcome["allocator_submitted_qty"] == 40
    assert outcome["allocator_submission_coverage_pct"] == 100.0
    assert outcome["allocator_fully_submitted_semantic_count"] == 1
    assert outcome["notional_net_profit_eligible"] is True


def test_submitted_krx_allocator_can_bind_exact_venue_when_route_is_omitted() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    submitted = _entry_pipeline_allocator_row(quantity=40)
    submitted["fields"].pop("market_data_route")

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[submitted],
        config=_verified_config(),
    )

    assert outcome["allocator_provenance_status"] == (
        "central_allocator_provenance_joined"
    )
    assert outcome["effective_qty"] == 40
    assert outcome["notional_net_profit_eligible"] is True


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

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[allocator],
        config=_verified_config(),
    )

    assert outcome["allocator_provenance_status"] == (
        "allocator_provenance_invalid_observation_only"
    )
    assert outcome["allocator_provenance_error"] == reason
    assert outcome["counterfactual_quantity"] == 1
    assert outcome["notional_net_profit_eligible"] is False
    assert outcome["economic_promotion_evidence_eligible"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda row: row["fields"].update(
                {"broker_order_qty_list": "0000101:not-a-number"}
            ),
            "entry_pipeline_allocator_broker_order_qty_list_invalid",
        ),
        (
            lambda row: row["fields"].update(
                {
                    "broker_order_qty_list": "",
                    "submitted_qty": None,
                    "broker_order_no": "",
                    "order_no": "",
                    "ord_no": "",
                }
            ),
            "entry_pipeline_allocator_broker_order_qty_missing",
        ),
    ],
)
def test_allocator_join_fails_closed_on_broker_quantity_contract_gap(
    mutation, reason
) -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )
    allocator = _entry_pipeline_allocator_row(
        quantity=5,
        stage="probe_submitted",
        submitted_qty=1,
    )
    mutation(allocator)

    outcome = build_future_outcome(
        evidence=evidence,
        market_rows=[],
        entry_pipeline_rows=[allocator],
        config=_verified_config(),
    )

    assert outcome["allocator_provenance_status"] == (
        "allocator_provenance_invalid_observation_only"
    )
    assert outcome["allocator_provenance_error"] == reason
    assert outcome["notional_net_profit_eligible"] is False


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
        evidence=evidence,
        ablation_design_version=LEGACY_DESIGN_VERSION,
        control_prompt_version="decision_quality_v2_14",
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
        ablation_design_version=LEGACY_DESIGN_VERSION,
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
            ablation_design_version=LEGACY_DESIGN_VERSION,
            source_trace=_trace(),
            source_payload=_payload(),
            source_market_rows=_past_market_rows(),
            source_depth_rows=[_depth()],
            source_event_references=[_reference()],
            config=_verified_config(),
            verified_symbol_metadata=_verified_symbol_metadata(),
        )


def test_materializes_current_ask_depletion_ablation_as_exact_single_axes() -> None:
    captured_at = "2026-08-14T09:00:16.000+09:00"
    trace = _trace(captured_at=captured_at)
    trace["decision_ts"] = "2026-08-14T09:00:17.000+09:00"
    payload = _payload(captured_at=captured_at)
    market_rows, depth_rows = _complete_ask_depletion_paths()
    evidence = build_tactical_evidence(
        trace=trace,
        payload=payload,
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    sidecar = build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=market_rows,
        depth_rows=depth_rows,
    )
    assert all(
        row["eligible_for_feature_ablation"] is True for row in sidecar["horizons"]
    )
    before_event_same_timestamp = deepcopy(market_rows[0])
    before_event_same_timestamp.update(
        {
            "source_sequence": 1,
            "series_sequence": 1,
            "exchange_timestamp": "2026-08-14T09:00:06.000+09:00",
            "local_receive_timestamp": "2026-08-14T09:00:06.000+09:00",
            "actual_order_submitted": True,
        }
    )
    assert (
        build_ask_depletion_feature_sidecar(
            evidence=evidence,
            market_rows=[*market_rows, before_event_same_timestamp],
            depth_rows=depth_rows,
        )
        == sidecar
    )
    same_ms_depth_path = deepcopy(depth_rows)
    for row in same_ms_depth_path[1:]:
        row["source_sequence"] += 1
        row["series_sequence"] += 1
    production_same_ms_depth = deepcopy(depth_rows[1])
    production_same_ms_depth.update(
        {
            "source_sequence": 2,
            "series_sequence": 2,
            "exchange_timestamp": "2026-08-14T09:00:06.000+09:00",
            "local_receive_timestamp": "2026-08-14T09:00:06.000+09:00",
        }
    )
    same_ms_depth_path.insert(1, production_same_ms_depth)
    ambiguous_sidecar = build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=market_rows,
        depth_rows=same_ms_depth_path,
    )
    assert ambiguous_sidecar["anchor_source_sequence"] == 1
    assert ambiguous_sidecar["source_quality_status"] == "source_gap"
    assert "depth_order_ambiguous_at_shock_millisecond" in (
        ambiguous_sidecar["source_gap_reasons"]
    )
    assert not any(
        row["eligible_for_feature_ablation"] for row in ambiguous_sidecar["horizons"]
    )

    after_snapshot_depth = deepcopy(same_ms_depth_path[-1])
    after_snapshot_depth.update(
        {
            "source_sequence": 11,
            "series_sequence": 11,
            "exchange_timestamp": "2026-08-14T09:00:16.000500+09:00",
            "local_receive_timestamp": "2026-08-14T09:00:16.000500+09:00",
        }
    )
    after_snapshot_market = deepcopy(market_rows[-1])
    after_snapshot_market.update(
        {
            "source_sequence": 7,
            "series_sequence": 7,
            "exchange_timestamp": "2026-08-14T09:00:16.000500+09:00",
            "local_receive_timestamp": "2026-08-14T09:00:16.000500+09:00",
        }
    )
    future_supplied_sidecar = build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=[*market_rows, after_snapshot_market],
        depth_rows=[*same_ms_depth_path, after_snapshot_depth],
    )
    assert future_supplied_sidecar == ambiguous_sidecar
    exact_payload = deepcopy(payload["sanitized_replay_context"]["exact_payload"])

    def request(prompt_version: str, prompt: str, *, stored: bool = False) -> dict:
        candidate_input = {"exact_payload": deepcopy(exact_payload)}
        response_schema = deepcopy(TEST_RESPONSE_SCHEMA)
        return {
            "paired_replay_id": "pair-current-design",
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
                "system_prompt_sha256": (
                    _stored_prompt_hash(prompt) if stored else _producer_hash(prompt)
                ),
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

    materialized = materialize_micro_reversion_three_arm_requests(
        replay_control_request=request(
            "decision_quality_v2_14", CONTROL_PROMPT, stored=True
        ),
        replay_candidate_request=request("candidate_v2", "candidate prompt"),
        evidence=evidence,
        ablation_design_version=CURRENT_DESIGN_VERSION,
        source_trace=trace,
        source_payload=payload,
        source_market_rows=market_rows,
        source_depth_rows=depth_rows,
        source_event_references=[_reference()],
        config=_verified_config(),
        ask_depletion_sidecar=sidecar,
        verified_symbol_metadata=_verified_symbol_metadata(),
    )

    assert materialized["ablation_design_version"] == CURRENT_DESIGN_VERSION
    assert tuple(materialized["ablation_arms"]) == CURRENT_ARMS
    arms = materialized["requests"]
    assert tuple(row["micro_reversion_replay_arm"] for row in arms) == CURRENT_ARMS
    assert len({row["paired_replay_parent_id"] for row in arms}) == 1
    assert all(
        f":ablation:{CURRENT_DESIGN_VERSION}:" in row["paired_replay_id"]
        for row in arms
    )

    feature_key = ASK_DEPLETION_FEATURE_VIEW_SCHEMA
    assert feature_key not in arms[0]["candidate_input"]
    assert arms[0]["candidate_input"][TACTICAL_EVIDENCE_SCHEMA] == evidence
    assert (
        arms[1]["candidate_input"][feature_key]
        == arms[2]["candidate_input"][feature_key]
    )
    control_without_feature = deepcopy(arms[1]["candidate_input"])
    control_without_feature.pop(feature_key)
    assert control_without_feature == arms[0]["candidate_input"]
    assert arms[0]["candidate_input_sha256"] != arms[1]["candidate_input_sha256"]
    assert arms[1]["candidate_input_sha256"] == arms[2]["candidate_input_sha256"]
    assert (
        arms[0]["candidate"]["system_prompt"] == arms[1]["candidate"]["system_prompt"]
    )
    assert (
        arms[1]["candidate"]["system_prompt"] != arms[2]["candidate"]["system_prompt"]
    )
    assert all(
        row["ask_depletion_context_sha256"] == sidecar["ask_depletion_context_sha256"]
        for row in arms[1:]
    )
    assert "ask_depletion_context_sha256" not in arms[0]
    for row in [materialized, *arms]:
        for field, expected in SOURCE_ONLY_AUTHORITY_CONTRACT.items():
            assert row[field] is expected
    with pytest.raises(ValueError, match="current_design_sidecar_missing"):
        build_three_arm_manifest(
            evidence=evidence,
            ablation_design_version=CURRENT_DESIGN_VERSION,
            control_prompt_version="decision_quality_v2_14",
        )
    with pytest.raises(ValueError, match="legacy_design_sidecar_forbidden"):
        build_three_arm_manifest(
            evidence=evidence,
            ablation_design_version=LEGACY_DESIGN_VERSION,
            control_prompt_version="decision_quality_v2_14",
            ask_depletion_sidecar=sidecar,
        )


@pytest.mark.parametrize(
    "case",
    (
        "sequence_epoch_float",
        "event_sequence_float",
        "snapshot_ms_float",
        "context_timestamp_float",
        "context_completeness_integer",
        "snapshot_iso_ms_split",
        "event_after_snapshot",
        "horizons_not_observed_through",
    ),
)
def test_persisted_ask_depletion_rejects_rehashed_watermark_tampering(case) -> None:
    evidence, _sidecar, feature = _complete_ask_depletion_feature_fixture()

    if case == "sequence_epoch_float":
        evidence["sequence_epoch"] = float(evidence["sequence_epoch"])
        feature["context"]["sequence_epoch"] = evidence["sequence_epoch"]
    elif case == "event_sequence_float":
        evidence["event"]["event_source_sequence"] = float(
            evidence["event"]["event_source_sequence"]
        )
        feature["context"]["event_market_source_sequence"] = evidence["event"][
            "event_source_sequence"
        ]
    elif case == "snapshot_ms_float":
        evidence["snapshot_captured_at_ms"] = float(evidence["snapshot_captured_at_ms"])
        feature["context"]["observed_through_local_receive_timestamp_ms"] = evidence[
            "snapshot_captured_at_ms"
        ]
    elif case == "context_timestamp_float":
        feature["context"]["anchor_event_local_receive_timestamp_ms"] = float(
            feature["context"]["anchor_event_local_receive_timestamp_ms"]
        )
    elif case == "context_completeness_integer":
        feature["context"]["depth_source_complete"] = 1
    elif case == "snapshot_iso_ms_split":
        evidence["snapshot_captured_at_ms"] += 1
        feature["context"]["observed_through_local_receive_timestamp_ms"] = evidence[
            "snapshot_captured_at_ms"
        ]
    elif case == "event_after_snapshot":
        evidence["event"]["event_detected_at_ms"] = (
            evidence["snapshot_captured_at_ms"] + 1
        )
        feature["context"]["anchor_event_local_receive_timestamp_ms"] = evidence[
            "event"
        ]["event_detected_at_ms"]
    else:
        evidence["snapshot_captured_at"] = "2026-08-14T09:00:06.100+09:00"
        evidence["snapshot_captured_at_ms"] = _ms(evidence["snapshot_captured_at"])
        feature["context"]["observed_through_local_receive_timestamp_ms"] = evidence[
            "snapshot_captured_at_ms"
        ]

    _reseal_ask_depletion_feature(evidence, feature)
    with pytest.raises(ValueError):
        bridge_module.validate_ask_depletion_feature_view(
            feature,
            evidence=evidence,
        )


@pytest.mark.parametrize(
    "case",
    (
        "sequence_epoch_float",
        "event_sequence_float",
        "snapshot_iso_ms_split",
        "event_after_snapshot",
    ),
)
def test_ask_depletion_source_rejects_rehashed_watermark_tampering(case) -> None:
    evidence, _sidecar, _feature = _complete_ask_depletion_feature_fixture()

    if case == "sequence_epoch_float":
        evidence["sequence_epoch"] = float(evidence["sequence_epoch"])
    elif case == "event_sequence_float":
        evidence["event"]["event_source_sequence"] = float(
            evidence["event"]["event_source_sequence"]
        )
    elif case == "snapshot_iso_ms_split":
        evidence["snapshot_captured_at_ms"] += 1
    else:
        evidence["event"]["event_detected_at_ms"] = (
            evidence["snapshot_captured_at_ms"] + 1
        )
    evidence["evidence_sha256"] = _sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )

    with pytest.raises(ValueError):
        build_ask_depletion_feature_sidecar(
            evidence=evidence,
            market_rows=[],
            depth_rows=[],
        )


@pytest.mark.parametrize(
    "case",
    ("stock_code_integer", "event_id_integer", "event_id_whitespace"),
)
@pytest.mark.parametrize("consumer", ("producer", "persisted_feature"))
def test_ask_depletion_rejects_resealed_non_native_identity(case, consumer) -> None:
    evidence, _sidecar, feature = _complete_ask_depletion_feature_fixture()
    if case == "stock_code_integer":
        evidence["stock_code"] = 1
    elif case == "event_id_integer":
        evidence["event"]["shock_event_id"] = 123
        feature["context"]["event_id"] = "123"
    else:
        evidence["event"]["shock_event_id"] = " shock-1 "
        feature["context"]["event_id"] = "shock-1"
    _reseal_ask_depletion_feature(evidence, feature)

    with pytest.raises(ValueError, match="micro_context_native_string_invalid"):
        if consumer == "producer":
            market_rows, depth_rows = _complete_ask_depletion_paths()
            build_ask_depletion_feature_sidecar(
                evidence=evidence,
                market_rows=market_rows,
                depth_rows=depth_rows,
            )
        else:
            bridge_module.validate_ask_depletion_feature_view(
                feature,
                evidence=evidence,
            )


@pytest.mark.parametrize(
    "case",
    (
        "zero_initial_best_ask",
        "clear_delay_after_horizon",
        "refill_half_life_after_horizon",
        "missing_half_life_after_half_refill",
        "invented_half_life_without_half_refill",
    ),
)
def test_persisted_ask_depletion_rejects_rehashed_producer_invariant_tampering(
    case,
) -> None:
    evidence, _sidecar, feature = _complete_ask_depletion_feature_fixture()

    if case == "zero_initial_best_ask":
        horizon = feature["eligible_horizons"][0]
        horizon.update(
            {
                "initial_anchor_ask_qty": 0,
                "endpoint_anchor_ask_qty": 0,
                "minimum_anchor_ask_qty": 0,
                "max_best_ask_depletion_qty": 0,
                "max_best_ask_depletion_ratio": None,
                "best_ask_depletion_velocity_qty_per_sec": 0.0,
                "price_level_cleared": False,
                "first_price_level_clear_delay_ms": None,
                "aggressive_buy_qty_before_max_depletion": 0,
                "aggressive_buy_trade_backed_ratio": None,
                "unexplained_or_cancel_like_depletion_qty": None,
                "unexplained_or_cancel_like_depletion_ratio": None,
                "max_refill_qty": 0,
                "refill_ratio": None,
                "refill_half_life_ms": None,
            }
        )
    elif case == "clear_delay_after_horizon":
        horizon = next(
            row for row in feature["eligible_horizons"] if row["price_level_cleared"]
        )
        horizon["first_price_level_clear_delay_ms"] = horizon["horizon_ms"] + 1
    elif case == "refill_half_life_after_horizon":
        horizon = next(
            row
            for row in feature["eligible_horizons"]
            if row["refill_half_life_ms"] is not None
        )
        horizon["refill_half_life_ms"] = horizon["horizon_ms"] + 1
    elif case == "missing_half_life_after_half_refill":
        horizon = next(
            row
            for row in feature["eligible_horizons"]
            if row["refill_half_life_ms"] is not None
        )
        horizon["refill_half_life_ms"] = None
    else:
        horizon = next(
            row
            for row in feature["eligible_horizons"]
            if row["max_refill_qty"] * 2 < row["max_best_ask_depletion_qty"]
        )
        horizon["refill_half_life_ms"] = 1

    _reseal_ask_depletion_feature(evidence, feature)
    with pytest.raises(ValueError):
        bridge_module.validate_ask_depletion_feature_view(
            feature,
            evidence=evidence,
        )


@pytest.mark.parametrize(
    "path_case", ("zero_depletion", "over_refill", "zero_at_price")
)
def test_valid_ask_depletion_producer_edge_shapes_revalidate(path_case) -> None:
    captured_at = "2026-08-14T09:00:16.000+09:00"
    trace = _trace(captured_at=captured_at)
    trace["decision_ts"] = "2026-08-14T09:00:17.000+09:00"
    market_rows, depth_rows = _complete_ask_depletion_paths()

    def replace_ask_quantities(row: dict, quantities: tuple[int, ...]) -> None:
        row["best_ask_qty"] = quantities[0]
        row["ask_depth"] = sum(quantities)
        row["ask_levels"] = [
            [level[0], level[1], quantity]
            for level, quantity in zip(row["ask_levels"], quantities, strict=True)
        ]
        row["route_depth_totals"]["KRX"]["ask"] = sum(quantities)
        row["route_depth_totals"]["combined"]["ask"] = sum(quantities)

    if path_case == "zero_depletion":
        for row in depth_rows:
            replace_ask_quantities(row, (100, 200, 300, 400, 500))
    elif path_case == "over_refill":
        replace_ask_quantities(depth_rows[3], (130, 230, 330, 430, 530))
    else:
        replace_ask_quantities(depth_rows[2], (0, 160, 260, 360, 460))

    evidence = build_tactical_evidence(
        trace=trace,
        payload=_payload(captured_at=captured_at),
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    sidecar = build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=market_rows,
        depth_rows=depth_rows,
    )
    feature = bridge_module._validated_ask_depletion_feature_view(
        sidecar,
        evidence=evidence,
    )

    bridge_module.validate_ask_depletion_feature_view(feature, evidence=evidence)
    if path_case == "zero_depletion":
        assert all(
            row["max_best_ask_depletion_qty"] == 0
            for row in feature["eligible_horizons"]
        )
    elif path_case == "over_refill":
        assert any(
            (row["refill_ratio"] or 0) > 1 for row in feature["eligible_horizons"]
        )
    else:
        assert any(
            row["minimum_anchor_ask_qty"] == 0 and row["price_level_cleared"] is False
            for row in feature["eligible_horizons"]
        )


def test_current_manifest_rejects_partial_ask_depletion_horizon_census() -> None:
    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=_ask_depletion_depth_path(),
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata=_verified_symbol_metadata(),
    )
    sidecar = build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=_past_market_rows(),
        depth_rows=_ask_depletion_depth_path(),
    )

    assert sidecar["source_quality_status"] == "partial"
    assert any(row["mature"] is False for row in sidecar["horizons"])
    with pytest.raises(
        ValueError, match="ask_depletion_sidecar_source_quality_invalid"
    ):
        build_three_arm_manifest(
            evidence=evidence,
            ablation_design_version=CURRENT_DESIGN_VERSION,
            control_prompt_version="decision_quality_v2_14",
            ask_depletion_sidecar=sidecar,
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
    assert (
        report["summary"]["micro_observation_context_eligible_primary_episode_count"]
        == 1
    )
    assert report["summary"]["micro_context_eligible_primary_episode_count"] == 0
    assert report["summary"]["same_parent_wave_repeat_count"] == 1
    assert all(
        row["three_arm_manifest"]["ablation_design_version"] == CURRENT_DESIGN_VERSION
        for row in report["rows"]
    )
    assert all(
        row["three_arm_manifest"]["paired_replay_materialization_eligible"] is False
        for row in report["rows"]
    )
    assert report["summary"][
        "confirmation_window_primary_episode_direction_counts"
    ] == {
        "120": {"DATA_WAIT": 1},
        "180": {"DATA_WAIT": 1},
    }
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
        report["summary"]["paired_decision_quality_eligible_primary_episode_count"] == 0
    )
    by_trace = {row["decision_trace_id"]: row for row in report["rows"]}
    assert by_trace["trace-1"]["primary_parent_wave_stage_row"] is True
    assert by_trace["trace-1"]["primary_control_parent_wave_stage_row"] is False
    assert by_trace["trace-2"]["primary_control_parent_wave_stage_row"] is True
    assert report["decision"] == "micro_context_keep_collecting_or_source_gap"
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


def test_canonical_source_selects_newest_epoch_before_semantic_validation() -> None:
    invalid_new_epoch = _market(
        "2026-08-14T09:00:09.900+09:00",
        price=9_940,
        side="BUY",
        qty=10,
        sequence=1,
        epoch=124,
    )
    invalid_new_epoch["schema"] = "invalid_market_schema"

    canonical = bridge_module._canonical_tactical_source_rows(
        target_date="2026-08-14",
        trace=_trace(),
        payload=_payload(),
        market_rows=[*_past_market_rows(), invalid_new_epoch],
        depth_rows=[_depth(), _depth(epoch=124)],
        event_references=[_reference(), _reference(epoch=124)],
        config=_verified_config(),
    )

    assert canonical["selected_epoch"] == 124
    assert canonical["market_rows"] == [invalid_new_epoch]
    assert all(row["sequence_epoch"] == 124 for row in canonical["depth_rows"])
    assert all(
        row["sequence_epoch"] == 124 for row in canonical["event_reference_rows"]
    )


def test_canonical_source_rejects_same_timestamp_competing_latest_epochs() -> None:
    competing_epoch = _market(
        "2026-08-14T09:00:09.800+09:00",
        price=9_936,
        side="BUY",
        qty=10,
        sequence=1,
        epoch=124,
    )

    canonical = bridge_module._canonical_tactical_source_rows(
        target_date="2026-08-14",
        trace=_trace(),
        payload=_payload(),
        market_rows=[*_past_market_rows(), competing_epoch],
        depth_rows=[_depth(), _depth(epoch=124)],
        event_references=[_reference(), _reference(epoch=124)],
        config=_verified_config(),
    )

    assert canonical["selected_epoch"] == 0
    assert canonical["market_rows"] == []
    assert canonical["depth_rows"] == []
    assert canonical["event_reference_rows"] == []


def test_canonical_source_depth_only_reconnect_selects_newest_transport_epoch() -> None:
    reconnect_depth = _depth(
        "2026-08-14T09:00:09.900+09:00",
        epoch=124,
        sequence=1,
    )

    canonical = bridge_module._canonical_tactical_source_rows(
        target_date="2026-08-14",
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth(), reconnect_depth],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert canonical["selected_epoch"] == 124
    assert canonical["market_rows"] == []
    assert canonical["depth_rows"] == [reconnect_depth]
    assert canonical["event_reference_rows"] == []

    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth(), reconnect_depth],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )
    evidence = report["rows"][0][TACTICAL_EVIDENCE_SCHEMA]
    assert evidence["source_quality"]["status"] == "blocked"
    assert "past_market_row_missing" in evidence["source_quality"]["blockers"]


def test_canonical_source_reference_only_reconnect_selects_newest_transport_epoch() -> (
    None
):
    reconnect_reference = _reference(epoch=124, parent_wave="wave-2")
    reconnect_detected_at_ms = _ms("2026-08-14T09:00:09.900+09:00")
    reconnect_reference.update(
        {
            "event_detected_at_ms": reconnect_detected_at_ms,
            "segment_event_detected_at_ms": reconnect_detected_at_ms,
            "capture_started_at": "2026-08-14T09:00:09.800+09:00",
            "capture_ended_at": "2026-08-14T09:03:09.900+09:00",
        }
    )

    canonical = bridge_module._canonical_tactical_source_rows(
        target_date="2026-08-14",
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference(), reconnect_reference],
        config=_verified_config(),
    )

    assert canonical["selected_epoch"] == 124
    assert canonical["market_rows"] == []
    assert canonical["depth_rows"] == []
    assert canonical["event_reference_rows"] == [reconnect_reference]

    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference(), reconnect_reference],
        config=_verified_config(),
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )
    evidence = report["rows"][0][TACTICAL_EVIDENCE_SCHEMA]
    assert evidence["source_quality"]["status"] == "blocked"
    assert "past_market_row_missing" in evidence["source_quality"]["blockers"]


def test_canonical_source_rejects_cross_stream_competing_latest_epochs() -> None:
    reconnect_depth = _depth(
        "2026-08-14T09:00:09.800+09:00",
        epoch=124,
        sequence=1,
    )

    canonical = bridge_module._canonical_tactical_source_rows(
        target_date="2026-08-14",
        trace=_trace(),
        payload=_payload(),
        market_rows=_past_market_rows(),
        depth_rows=[_depth(), reconnect_depth],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert canonical["selected_epoch"] == 0
    assert canonical["market_rows"] == []
    assert canonical["depth_rows"] == []
    assert canonical["event_reference_rows"] == []


def test_selected_epoch_without_valid_market_blocks_provider_materialization() -> None:
    invalid_new_epoch = _market(
        "2026-08-14T09:00:09.900+09:00",
        price=9_940,
        side="BUY",
        qty=10,
        sequence=1,
        epoch=124,
    )
    invalid_new_epoch["schema"] = "invalid_market_schema"

    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=[*_past_market_rows(), invalid_new_epoch],
        depth_rows=[_depth(), _depth(epoch=124)],
        event_references=[_reference(), _reference(epoch=124)],
        config=_verified_config(),
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )

    row = report["rows"][0]
    evidence = row[TACTICAL_EVIDENCE_SCHEMA]
    assert evidence["state"] == "source_unavailable"
    assert evidence["source_quality"]["status"] == "blocked"
    assert "past_market_row_missing" in evidence["source_quality"]["blockers"]
    assert evidence["source_quality"]["rejected_market_reason_counts"] == {
        "market_schema_invalid": 1
    }
    assert row["three_arm_manifest"]["replay_context_eligible"] is False
    assert row["three_arm_manifest"]["paired_replay_materialization_eligible"] is False
    assert row["three_arm_manifest"]["provider_call_performed"] is False


def test_report_persists_only_exact_causal_rows_and_keeps_exact_invalid_rows() -> None:
    exact_future_market = _market(
        "2026-08-14T09:00:11.500+09:00",
        price=9_970,
        side="BUY",
        qty=30,
        sequence=5,
    )
    exact_semantic_invalid_market = _market(
        "2026-08-14T09:00:12.000+09:00",
        price=9_980,
        side="BUY",
        qty=20,
        sequence=6,
    )
    exact_semantic_invalid_market["schema"] = "invalid_market_schema"
    wrong_epoch_market = {
        **exact_future_market,
        "sequence_epoch": 124,
        "source_sequence": 7,
    }
    cross_date_market = {
        **exact_future_market,
        "exchange_timestamp": "2026-08-15T09:00:11.500+09:00",
        "local_receive_timestamp": "2026-08-15T09:00:11.500+09:00",
        "source_sequence": 8,
    }
    out_of_window_market = {
        **exact_future_market,
        "exchange_timestamp": "2026-08-14T09:05:00.000+09:00",
        "local_receive_timestamp": "2026-08-14T09:05:00.000+09:00",
        "source_sequence": 9,
    }

    anchor_depth = _depth()
    exact_semantic_invalid_depth = _depth("2026-08-14T09:00:11.500+09:00", sequence=2)
    exact_semantic_invalid_depth["schema"] = "invalid_depth_schema"
    wrong_epoch_depth = _depth("2026-08-14T09:00:11.700+09:00", epoch=124, sequence=3)
    cross_date_depth = _depth("2026-08-15T09:00:11.700+09:00", sequence=4)
    out_of_window_depth = _depth("2026-08-14T09:05:00.000+09:00", sequence=5)

    causal_reference = _reference()
    post_snapshot_reference = {
        **_reference(parent_wave="future-wave"),
        "event_detected_at_ms": _ms("2026-08-14T09:00:10.500+09:00"),
        "segment_event_detected_at_ms": _ms("2026-08-14T09:00:10.500+09:00"),
    }
    exact_pipeline = _entry_pipeline_allocator_row(quantity=50)
    predecision_pipeline = deepcopy(exact_pipeline)
    predecision_pipeline.update(
        {
            "record_id": 102,
            "emitted_at": "2026-08-14T09:00:10.500+09:00",
        }
    )
    cross_date_pipeline = deepcopy(exact_pipeline)
    cross_date_pipeline.update(
        {
            "record_id": 103,
            "emitted_at": "2026-08-15T09:00:11.100+09:00",
            "emitted_date": "2026-08-15",
        }
    )
    out_of_window_pipeline = deepcopy(exact_pipeline)
    out_of_window_pipeline.update(
        {
            "record_id": 104,
            "emitted_at": "2026-08-14T09:05:00.000+09:00",
        }
    )
    wrong_session_pipeline = deepcopy(exact_pipeline)
    wrong_session_pipeline["record_id"] = 105
    wrong_session_pipeline["fields"]["market_session_bucket"] = "NXT_REGULAR"

    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=[
            *_past_market_rows(),
            exact_future_market,
            exact_semantic_invalid_market,
            wrong_epoch_market,
            cross_date_market,
            out_of_window_market,
        ],
        depth_rows=[
            anchor_depth,
            exact_semantic_invalid_depth,
            wrong_epoch_depth,
            cross_date_depth,
            out_of_window_depth,
        ],
        event_references=[causal_reference, post_snapshot_reference],
        entry_pipeline_rows=[
            exact_pipeline,
            predecision_pipeline,
            cross_date_pipeline,
            out_of_window_pipeline,
            wrong_session_pipeline,
        ],
        entry_pipeline_source={
            "status": "available_hash_verified",
            "source_path": "test",
            "source_sha256": "c" * 64,
        },
        config=_verified_config(),
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )

    evidence = report["rows"][0][TACTICAL_EVIDENCE_SCHEMA]
    assert evidence["event"]["parent_wave_id"] == "wave-1"
    pools = report["future_outcome_source_pool"]["row_pools"]
    assert set(pools["market"]) == {
        _sha256(exact_future_market),
        _sha256(exact_semantic_invalid_market),
    }
    assert set(pools["depth"]) == {
        _sha256(anchor_depth),
        _sha256(exact_semantic_invalid_depth),
    }
    assert set(pools["entry_pipeline"]) == {_sha256(exact_pipeline)}
    outcome = report["rows"][0]["future_outcome"]
    assert bridge_module._valid_market_row(exact_semantic_invalid_market) == (
        False,
        "market_schema_invalid",
    )
    assert bridge_module._valid_depth_row(exact_semantic_invalid_depth) == (
        False,
        "depth_contract_invalid",
    )
    assert (
        bridge_module.rebuild_future_outcome_from_source(
            evidence=evidence,
            rebuild_source=report["rows"][0]["future_outcome_rebuild_source"],
            source_pool=report["future_outcome_source_pool"],
        )
        == outcome
    )


def test_invalid_timestamp_census_is_bounded_once_not_copied_per_parent() -> None:
    trace_two = _trace(trace_id="trace-2", request_id="request-2")
    payload_two = _payload(request_id="request-2")
    invalid_market_rows = [
        {
            **_past_market_rows()[0],
            "source_sequence": 100 + index,
            "local_receive_timestamp": f"invalid-{index}",
        }
        for index in range(64)
    ]
    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace(), trace_two],
        payloads=[_payload(), payload_two],
        market_rows=[*_past_market_rows(), *invalid_market_rows],
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata_by_trace={
            "trace-1": _verified_symbol_metadata(),
            "trace-2": _verified_symbol_metadata(),
        },
    )

    assert report["report_row_count"] == 2
    assert (
        report["summary"]["noncausal_source_diagnostics"][
            "invalid_market_timestamp_row_count"
        ]
        == 64
    )
    assert all(
        row[TACTICAL_EVIDENCE_SCHEMA]["source_quality"]["rejected_market_reason_counts"]
        == {}
        for row in report["rows"]
    )
    pooled_hashes = set(report["future_outcome_source_pool"]["row_pools"]["market"])
    assert pooled_hashes.isdisjoint(_sha256(row) for row in invalid_market_rows)


def test_bridge_producer_validates_future_source_pool_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace_two = _trace(trace_id="trace-2", request_id="request-2")
    payload_two = _payload(request_id="request-2")
    validation_calls = 0
    original_validation = bridge_module.validate_future_outcome_source_pool

    def counted_validation(*args, **kwargs):
        nonlocal validation_calls
        validation_calls += 1
        return original_validation(*args, **kwargs)

    monkeypatch.setattr(
        bridge_module,
        "validate_future_outcome_source_pool",
        counted_validation,
    )

    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace(), trace_two],
        payloads=[_payload(), payload_two],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata_by_trace={
            "trace-1": _verified_symbol_metadata(),
            "trace-2": _verified_symbol_metadata(),
        },
    )

    assert report["report_row_count"] == 2
    assert validation_calls == 1


@pytest.mark.parametrize("decision_stage", ("holding", "holding_flow", "exit"))
def test_position_stage_never_retains_fabricated_entry_pipeline_source(
    decision_stage: str,
) -> None:
    pipeline = _entry_pipeline_allocator_row(quantity=50)
    evidence = {
        "decision_stage": decision_stage,
        "decision_trace_id": "trace-1",
        "stock_code": "000001",
        "trace_effective_venue": "KRX",
        "trace_session_bucket": "KRX_REGULAR",
        "trace_decision_ts": "2026-08-14T09:00:11.000+09:00",
        "snapshot_captured_at": "2026-08-14T09:00:10.000+09:00",
    }

    assert (
        bridge_module._canonical_entry_pipeline_rows(
            evidence=evidence,
            entry_pipeline_rows=[pipeline],
            future_end_us=_ms("2026-08-14T09:03:12.500+09:00") * 1_000,
        )
        == []
    )


def test_entry_pipeline_canonicalizer_preserves_historical_naive_kst_rows() -> None:
    pipeline = _entry_pipeline_allocator_row(quantity=50)
    pipeline["emitted_at"] = "2026-08-14T09:00:11.100"
    evidence = {
        "decision_stage": "entry_screen",
        "decision_trace_id": "trace-1",
        "stock_code": "000001",
        "trace_effective_venue": "KRX",
        "trace_session_bucket": "KRX_REGULAR",
        "trace_decision_ts": "2026-08-14T09:00:11.000+09:00",
        "snapshot_captured_at": "2026-08-14T09:00:10.000+09:00",
    }

    assert bridge_module._canonical_entry_pipeline_rows(
        evidence=evidence,
        entry_pipeline_rows=[pipeline],
        future_end_us=_ms("2026-08-14T09:03:12.500+09:00") * 1_000,
    ) == [pipeline]


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


def test_market_v3_accepts_canonical_journal_identity_without_registration_item() -> (
    None
):
    market_rows = _past_market_rows()
    for row in market_rows:
        row.pop("item")

    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=market_rows,
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert "past_market_row_missing" not in evidence["source_quality"]["blockers"]
    assert evidence["source_quality"]["rejected_market_reason_counts"] == {}


def test_market_v3_still_rejects_conflicting_registration_item_when_present() -> None:
    market_rows = _past_market_rows()
    market_rows[-1] = {**market_rows[-1], "item": "999999_AL"}

    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=market_rows,
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["source_quality"]["rejected_market_reason_counts"] == {
        "market_item_scope_conflict": 1
    }


def test_legacy_market_schema_does_not_inherit_v3_item_omission_contract() -> None:
    market_rows = _past_market_rows()
    market_rows[-1] = {
        **market_rows[-1],
        "schema": "scalp_micro_reversion_market_stream_point_v2",
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v2",
    }
    market_rows[-1].pop("item")

    evidence = build_tactical_evidence(
        trace=_trace(),
        payload=_payload(),
        market_rows=market_rows,
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
    )

    assert evidence["source_quality"]["rejected_market_reason_counts"] == {
        "market_item_scope_conflict": 1
    }


@pytest.mark.parametrize(
    ("field", "value"),
    (("symbol", " 000001"), ("venue", "SMART"), ("venue", "krx")),
)
def test_market_v3_requires_canonical_stored_scope(field: str, value: str) -> None:
    market_row = {**_past_market_rows()[-1], field: value}
    market_row.pop("item")

    assert bridge_module._valid_market_row(market_row) == (
        False,
        "market_item_scope_conflict",
    )


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
    assert source["canonical_entry_pipeline_row_count"] == 2
    assert source["trace_symbol_linked_noncanonical_row_count"] == 0
    assert source["outcome_join_mode"] == (
        "central_allocator_full_submission_outcome_only"
    )
    assert report["summary"]["entry_pipeline_allocator_outcome_joined_count"] == 1
    assert report["summary"]["entry_pipeline_allocator_partial_submission_count"] == 0
    assert report["summary"]["entry_pipeline_allocator_tuning_input_allowed"] is True
    assert report["summary"]["entry_pipeline_allocator_decision_authority"] == (
        "source_quality_eligible_full_submission_outcome_only"
    )
    assert report["summary"]["entry_pipeline_allocator_status_counts"] == {
        "central_allocator_provenance_joined": 1
    }
    assert report["summary"]["entry_pipeline_allocator_error_counts"] == {}
    assert report["report_row_count"] == len(report["rows"])
    assert report["report_content_sha256"] == _producer_hash(
        {key: value for key, value in report.items() if key != "report_content_sha256"}
    )

    mismatched = _entry_pipeline_allocator_row(quantity=50)
    mismatched["fields"]["market_session_bucket"] = "nxt_regular"
    mismatch_report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        entry_pipeline_rows=[mismatched],
        entry_pipeline_source={
            "status": "available_hash_verified",
            "logical_source_path": "/test/pipeline_events_2026-08-14.jsonl",
            "source_path": "/test/pipeline_events_2026-08-14.jsonl",
            "source_compression": "plain",
            "source_bytes": 123,
            "source_sha256": "c" * 64,
            "source_content_sha256": "d" * 64,
            "source_content_bytes": 456,
            "source_line_count": 1,
            "source_nonempty_line_count": 1,
            "source_json_object_row_count": 1,
            "source_snapshot_stable": True,
        },
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )
    assert mismatch_report["status"] == "warning"
    assert mismatch_report["decision"] == "micro_context_keep_collecting_or_source_gap"
    assert (
        mismatch_report["summary"]["entry_pipeline_allocator_join_contract_gap"]
        is False
    )
    assert (
        mismatch_report["entry_pipeline_source"]["canonical_entry_pipeline_row_count"]
        == 0
    )
    assert (
        mismatch_report["entry_pipeline_source"][
            "trace_symbol_linked_noncanonical_row_count"
        ]
        == 1
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


def test_bridge_report_keeps_partial_probe_out_of_allocator_tuning_input() -> None:
    probe = _entry_pipeline_allocator_row(
        quantity=50,
        stage="probe_submitted",
        submitted_qty=1,
    )
    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[_trace()],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        entry_pipeline_rows=[probe],
        entry_pipeline_source={
            "status": "available_hash_verified",
            "logical_source_path": "/test/pipeline_events_2026-08-14.jsonl",
            "source_path": "/test/pipeline_events_2026-08-14.jsonl",
            "source_compression": "plain",
            "source_bytes": 123,
            "source_sha256": "c" * 64,
            "source_content_sha256": "d" * 64,
            "source_content_bytes": 456,
            "source_line_count": 1,
            "source_nonempty_line_count": 1,
            "source_json_object_row_count": 1,
            "source_snapshot_stable": True,
        },
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )

    assert report["entry_pipeline_source"]["outcome_join_mode"] == (
        "partial_submission_standardized_one_share_observation_only"
    )
    assert report["summary"]["entry_pipeline_allocator_outcome_joined_count"] == 0
    assert report["summary"]["entry_pipeline_allocator_partial_submission_count"] == 1
    assert report["summary"]["entry_pipeline_allocator_tuning_input_allowed"] is False
    assert report["summary"]["entry_pipeline_allocator_decision_authority"] == (
        "partial_submission_standardized_one_share_observation_only"
    )
    outcome = report["rows"][0]["future_outcome"]
    assert outcome["allocator_submitted_qty"] == 1
    assert outcome["allocator_submission_coverage_pct"] == 2.0
    assert outcome["notional_net_profit_eligible"] is False


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

    pipeline_gzip_path.symlink_to(tmp_path / "missing-pipeline-target.jsonl.gz")
    with pytest.raises(ValueError, match="jsonl_artifact_path_type_invalid"):
        bridge_module.main(["--date", "2026-08-14"])
    pipeline_gzip_path.unlink()

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


def test_cli_binds_verified_artifacts_to_one_strict_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    trace_path = data_dir / "ai_decision_trace" / "ai_decision_trace_2026-08-25.jsonl"
    payload_path = (
        data_dir / "ai_decision_payloads" / "ai_decision_payloads_2026-08-25.jsonl"
    )
    for path in (trace_path, payload_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    cost_payload = _current_cost_catalog_payload()
    cost_path = tmp_path / "verified_cost_profile.json"
    cost_path.write_text(json.dumps(cost_payload), encoding="utf-8")
    symbol_payload = _canonical_symbol_master_payload()
    symbol_path = tmp_path / "verified_symbol_master.json"
    symbol_path.write_text(json.dumps(symbol_payload), encoding="utf-8")

    strict_reader = bridge_module.read_json_object_strict
    strict_reads: list[Path] = []

    def read_then_replace(selected: Path) -> dict:
        payload = strict_reader(selected)
        strict_reads.append(selected)
        replacement = (
            {"schema": "replaced_cost_generation"}
            if selected == cost_path
            else {**symbol_payload, "records": []}
        )
        selected.write_text(json.dumps(replacement), encoding="utf-8")
        return payload

    original_read_text = Path.read_text

    def forbid_verified_artifact_path_read(selected: Path, *args, **kwargs) -> str:
        if selected in {cost_path, symbol_path}:
            raise AssertionError(f"verified artifact decoded twice:{selected}")
        return original_read_text(selected, *args, **kwargs)

    def fake_iter(paths):
        selected = tuple(paths)
        if not selected:
            return iter(())
        if "ai_decision_trace" in selected[0].name:
            return iter([_trace()])
        if "ai_decision_payloads" in selected[0].name:
            return iter([_payload()])
        return iter(())

    captured: dict = {}

    def fake_report(**kwargs):
        captured.update(
            {
                "config": kwargs["config"],
                "metadata": kwargs["verified_symbol_metadata_by_trace"],
            }
        )
        return {"status": "warning", "decision": "test", "summary": {}}

    monkeypatch.setattr(bridge_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(bridge_module, "read_json_object_strict", read_then_replace)
    monkeypatch.setattr(Path, "read_text", forbid_verified_artifact_path_read)
    monkeypatch.setattr(bridge_module, "_iter_jsonl", fake_iter)
    monkeypatch.setattr(
        bridge_module,
        "load_source_exclusion_manifest",
        lambda _path: {"exclusions": []},
    )
    monkeypatch.setattr(bridge_module, "build_bridge_report", fake_report)

    assert (
        bridge_module.main(
            [
                "--date",
                "2026-08-25",
                "--verified-cost-profile",
                str(cost_path),
                "--symbol-master",
                str(symbol_path),
            ]
        )
        == 0
    )

    assert strict_reads == [cost_path, symbol_path]
    assert captured["config"].cost_profile_artifact_sha256 == _producer_hash(
        cost_payload
    )
    metadata = captured["metadata"]["trace-1"]
    assert metadata["lookup_status"] == "verified"
    assert metadata["record"]["symbol"] == "000001"
    assert metadata["symbol_master_artifact_sha256"] == _sha256(symbol_payload)
    assert (
        json.loads(original_read_text(symbol_path, encoding="utf-8"))["records"] == []
    )

    cost_path.write_text(json.dumps(cost_payload), encoding="utf-8")
    symbol_path.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_symbol_master_v1",
                "decision_authority": "instrument_metadata_source_only",
                "runtime_effect": False,
                "records": [_verified_symbol_metadata()["record"]],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        bridge_module.main(
            [
                "--date",
                "2026-08-25",
                "--verified-cost-profile",
                str(cost_path),
                "--symbol-master",
                str(symbol_path),
            ]
        )


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


def test_bridge_writer_reopens_compacted_generation_without_dual_conflict(
    tmp_path: Path,
) -> None:
    logical = tmp_path / "micro_reversion_ai_quality_bridge_2026-08-24.json"
    compressed = logical.with_suffix(".json.gz")
    old_payload = {"schema": "old", "generation": 1}
    new_payload = {"schema": "new", "generation": 2}
    compressed.write_bytes(
        gzip.compress(
            (json.dumps(old_payload, ensure_ascii=False) + "\n").encode("utf-8")
        )
    )

    bridge_module._atomic_write_json(logical, new_payload)

    assert read_json_object_strict(logical) == new_payload
    assert logical.exists()
    assert not compressed.exists()
    archived = list((tmp_path / "superseded").rglob(compressed.name))
    assert len(archived) == 1
    with gzip.open(archived[0], "rt", encoding="utf-8") as handle:
        assert json.load(handle) == old_payload


def _write_source_rows(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def test_relevant_source_cache_complete_reuse_skips_jsonl_ingest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    market_path = tmp_path / "market.jsonl"
    depth_path = tmp_path / "depth.jsonl"
    reference_path = tmp_path / "reference.jsonl"
    _write_source_rows(
        market_path,
        [
            _market(
                "2026-08-14T09:00:09.900+09:00",
                price=9_950.0,
                side="BUY",
                qty=10,
                sequence=1,
            )
        ],
    )
    _write_source_rows(depth_path, [_depth()])
    _write_source_rows(reference_path, [])
    windows = {
        ("000001", "KRX", "KRX_REGULAR"): (
            (
                _ms("2026-08-14T09:00:09.000+09:00"),
                _ms("2026-08-14T09:00:11.000+09:00"),
            ),
        )
    }
    cache_root = tmp_path / "cache"
    original_iter = bridge_module._iter_jsonl
    ingest_calls = 0

    def counted_iter(paths):
        nonlocal ingest_calls
        ingest_calls += 1
        yield from original_iter(paths)

    monkeypatch.setattr(bridge_module, "_iter_jsonl", counted_iter)
    kwargs = {
        "target_date": "2026-08-14",
        "windows": windows,
        "config": _verified_config(),
        "market_paths": [market_path],
        "depth_paths": [depth_path],
        "reference_paths": [reference_path],
        "persistent_cache": True,
        "cache_root": cache_root,
    }
    with open_relevant_source_store(**kwargs) as store:
        assert store.cache_status == "cache_built"
        first_artifact_diagnostics = dict(store.cache_diagnostics)
        assert (
            len(
                store.rows(
                    "market",
                    ("000001", "KRX", "KRX_REGULAR"),
                    start_us=_ms("2026-08-14T09:00:09.000+09:00") * 1_000,
                    end_us=_ms("2026-08-14T09:00:11.000+09:00") * 1_000,
                )
            )
            == 1
        )
    assert ingest_calls == 3

    def forbidden_iter(_paths):
        raise AssertionError("complete cache reuse must not parse raw JSONL")
        yield  # pragma: no cover

    monkeypatch.setattr(bridge_module, "_iter_jsonl", forbidden_iter)
    with open_relevant_source_store(**kwargs) as store:
        assert store.cache_status == "cache_reused"
        assert store.cache_diagnostics["requested_windows_covered"] is True
        assert store.cache_diagnostics == first_artifact_diagnostics


def test_stable_source_hash_rejects_symlink_target_swap_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    link = tmp_path / "current.jsonl"
    first.write_text('{"generation":1}\n', encoding="utf-8")
    second.write_text('{"generation":2}\n', encoding="utf-8")
    link.symlink_to(first)
    original_read = os.read
    swapped = False

    def swapping_read(descriptor: int, size: int) -> bytes:
        nonlocal swapped
        chunk = original_read(descriptor, size)
        if chunk and not swapped:
            swapped = True
            link.unlink()
            link.symlink_to(second)
        return chunk

    monkeypatch.setattr(bridge_module.os, "read", swapping_read)

    with pytest.raises(
        ValueError, match="relevant_source_generation_changed_during_hash"
    ):
        bridge_module._stable_file_sha256(link)


def test_relevant_source_cache_recheck_rejects_append_before_artifact_publish(
    tmp_path: Path,
) -> None:
    market_path = tmp_path / "market.jsonl"
    depth_path = tmp_path / "depth.jsonl"
    reference_path = tmp_path / "reference.jsonl"
    _write_source_rows(
        market_path,
        [
            _market(
                "2026-08-14T09:00:09.900+09:00",
                price=9_950.0,
                side="BUY",
                qty=10,
                sequence=1,
            )
        ],
    )
    _write_source_rows(depth_path, [])
    _write_source_rows(reference_path, [])
    windows = {
        ("000001", "KRX", "KRX_REGULAR"): (
            (
                _ms("2026-08-14T09:00:09.000+09:00"),
                _ms("2026-08-14T09:00:11.000+09:00"),
            ),
        )
    }
    kwargs = {
        "target_date": "2026-08-14",
        "windows": windows,
        "config": _verified_config(),
        "market_paths": [market_path],
        "depth_paths": [depth_path],
        "reference_paths": [reference_path],
        "persistent_cache": True,
        "cache_root": tmp_path / "cache",
    }
    with open_relevant_source_store(**kwargs):
        pass

    with pytest.raises(
        ValueError,
        match="relevant_source_generation_changed_during_materialization",
    ):
        with open_relevant_source_store(**kwargs) as store:
            assert store.cache_status == "cache_reused"
            with market_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        _market(
                            "2026-08-14T09:00:10.100+09:00",
                            price=9_960.0,
                            side="BUY",
                            qty=10,
                            sequence=2,
                        )
                    )
                    + "\n"
                )


@pytest.mark.parametrize("damage", ["metadata", "sqlite", "source_change"])
def test_relevant_source_cache_damage_or_source_change_rebuilds_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    market_path = tmp_path / "market.jsonl"
    depth_path = tmp_path / "depth.jsonl"
    reference_path = tmp_path / "reference.jsonl"
    first_market = _market(
        "2026-08-14T09:00:09.900+09:00",
        price=9_950.0,
        side="BUY",
        qty=10,
        sequence=1,
    )
    _write_source_rows(market_path, [first_market])
    _write_source_rows(depth_path, [_depth()])
    _write_source_rows(reference_path, [])
    windows = {
        ("000001", "KRX", "KRX_REGULAR"): (
            (
                _ms("2026-08-14T09:00:09.000+09:00"),
                _ms("2026-08-14T09:00:11.000+09:00"),
            ),
        )
    }
    cache_root = tmp_path / "cache"
    kwargs = {
        "target_date": "2026-08-14",
        "windows": windows,
        "config": _verified_config(),
        "market_paths": [market_path],
        "depth_paths": [depth_path],
        "reference_paths": [reference_path],
        "persistent_cache": True,
        "cache_root": cache_root,
    }
    with open_relevant_source_store(**kwargs) as store:
        assert store.cache_status == "cache_built"
    cache_dir = next((cache_root / "2026-08-14").glob("cache-*"))
    if damage == "metadata":
        metadata_path = cache_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["complete"] = False
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    elif damage == "sqlite":
        with (cache_dir / "source.sqlite3").open("ab") as handle:
            handle.write(b"tampered")
    else:
        second_market = _market(
            "2026-08-14T09:00:10.100+09:00",
            price=9_960.0,
            side="BUY",
            qty=11,
            sequence=2,
        )
        _write_source_rows(market_path, [first_market, second_market])

    original_iter = bridge_module._iter_jsonl
    ingest_calls = 0

    def counted_iter(paths):
        nonlocal ingest_calls
        ingest_calls += 1
        yield from original_iter(paths)

    monkeypatch.setattr(bridge_module, "_iter_jsonl", counted_iter)
    with open_relevant_source_store(**kwargs) as store:
        assert store.cache_status == "cache_built"
    assert ingest_calls == 3


def test_relevant_source_cache_reuses_covering_superset_for_subset_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    market_path = tmp_path / "market.jsonl"
    depth_path = tmp_path / "depth.jsonl"
    reference_path = tmp_path / "reference.jsonl"
    _write_source_rows(
        market_path,
        [
            _market(
                "2026-08-14T09:00:09.200+09:00",
                price=9_950.0,
                side="BUY",
                qty=10,
                sequence=1,
            ),
            _market(
                "2026-08-14T09:00:10.800+09:00",
                price=9_960.0,
                side="BUY",
                qty=10,
                sequence=2,
            ),
        ],
    )
    _write_source_rows(depth_path, [])
    _write_source_rows(reference_path, [])
    key = ("000001", "KRX", "KRX_REGULAR")
    broad = {
        key: (
            (
                _ms("2026-08-14T09:00:09.000+09:00"),
                _ms("2026-08-14T09:00:11.000+09:00"),
            ),
        )
    }
    narrow = {
        key: (
            (
                _ms("2026-08-14T09:00:09.000+09:00"),
                _ms("2026-08-14T09:00:10.000+09:00"),
            ),
        )
    }
    common = {
        "target_date": "2026-08-14",
        "config": _verified_config(),
        "market_paths": [market_path],
        "depth_paths": [depth_path],
        "reference_paths": [reference_path],
        "persistent_cache": True,
        "cache_root": tmp_path / "cache",
    }
    with open_relevant_source_store(windows=broad, **common):
        pass

    def forbidden_iter(_paths):
        raise AssertionError("covered subset must reuse the source index")
        yield  # pragma: no cover

    monkeypatch.setattr(bridge_module, "_iter_jsonl", forbidden_iter)
    with open_relevant_source_store(windows=narrow, **common) as store:
        rows = store.rows(
            "market",
            key,
            start_us=narrow[key][0][0] * 1_000,
            end_us=narrow[key][0][1] * 1_000,
        )
        assert store.cache_status == "cache_reused"
        assert [row["source_sequence"] for row in rows] == [1]
        assert store.retained_row_counts["market"] == 1


def test_relevant_source_cache_cleanup_bounds_completed_and_partial(
    tmp_path: Path,
) -> None:
    cache_root = tmp_path / "cache"
    target_root = cache_root / "2026-08-14"
    target_root.mkdir(parents=True)
    for index in range(4):
        cache_dir = target_root / f"cache-{index}"
        cache_dir.mkdir()
        (cache_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "created_at": f"2026-08-14T00:00:0{index}+00:00",
                }
            ),
            encoding="utf-8",
        )
    partial = target_root / ".partial-abandoned"
    partial.mkdir()

    result = _cleanup_relevant_source_cache(
        cache_root,
        keep_completed=2,
        partial_max_age_sec=0,
        now_timestamp=partial.stat().st_mtime + 1,
    )

    assert result == {"partial_removed": 1, "completed_removed": 2}
    assert len(list(target_root.glob("cache-*"))) == 2
    assert not partial.exists()


def test_scheduled_census_reseal_uses_artifact_hash_contract_with_non_ascii() -> None:
    from src.engine.scalping import ai_decision_quality as quality

    trace = _trace()
    report = build_bridge_report(
        target_date="2026-08-14",
        traces=[trace],
        payloads=[_payload()],
        market_rows=_past_market_rows(),
        depth_rows=[_depth()],
        event_references=[_reference()],
        config=_verified_config(),
        verified_symbol_metadata_by_trace={"trace-1": _verified_symbol_metadata()},
    )
    report_body = {
        key: value for key, value in report.items() if key != "report_content_sha256"
    }
    report_body["non_ascii_hash_regression"] = "호가 잔량 검증"
    report = {
        **report_body,
        "report_content_sha256": bridge_module._sha256(report_body),
    }
    census = {
        "schema": "micro_reversion_scheduled_prepared_trace_census_v1",
        "target_date": "2026-08-14",
        "prepared_artifact_sha256": "a" * 64,
        "prepared_request_count": 1,
        "decision_trace_ids_sha256": bridge_module._sha256(["trace-1"]),
        "exact_trace_census": True,
        "broad_manual_trace_corpus_used": False,
        "provider_call_performed": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }

    bound = bridge_module._bind_scheduled_prepared_census_to_report(
        report=report,
        traces=[trace],
        census=census,
    )

    assert bound["report_content_sha256"] == bridge_module._sha256(
        {key: value for key, value in bound.items() if key != "report_content_sha256"}
    )
    commitment = quality._micro_reversion_outcome_source_commitment(
        bound,
        expected_target_date="2026-08-14",
    )
    assert commitment["bridge_report_content_sha256"] == bound["report_content_sha256"]
