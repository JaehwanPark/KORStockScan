"""Prepare the same causal micro + ask input used by current A/B/C research.

The temporary capture below is a pre-call in-memory request, never a stored
provider-success trace. Actual delivery is recorded by the normal call owner.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Callable

from src.engine.scalping import main_ai_current_axis as policy


def prepare_input(
    *,
    base_input: str,
    request_id: str,
    symbol: str,
    metadata: dict,
    candidate: dict,
    now: datetime,
    source_reader: Callable | None = None,
) -> tuple[str, dict]:
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping import ai_decision_trace as capture
    from src.engine.scalping.ai_market_snapshot import ai_input_preflight
    from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge
    from src.engine.scalping.micro_reversion.current_axis_source import live_source
    from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

    current = policy.now_kst(now)
    parsed = json.loads(base_input)
    if not isinstance(parsed, dict):
        raise ValueError("structured_current_axis_input_required")
    # Preserve the B/C input shape: exact base plus the same deterministic ledgers.
    exact = parsed.get("exact_payload", parsed)
    if not isinstance(exact, dict):
        raise ValueError("exact_payload_required")
    if any(
        key in parsed
        for key in (
            bridge.TACTICAL_EVIDENCE_SCHEMA,
            bridge.ASK_DEPLETION_FEATURE_VIEW_SCHEMA,
        )
    ):
        raise ValueError("current_axis_input_already_enriched")
    snapshots = {
        policy.sha(row): row
        for row in bridge._walk_objects(exact)
        if row.get("schema") == "ai_market_snapshot_v1"
    }
    if len(snapshots) != 1:
        raise ValueError("unique_live_snapshot_required")
    snapshot = next(iter(snapshots.values()))
    captured = policy.now_kst(datetime.fromisoformat(snapshot["captured_at"]))
    if not 0 <= (current - captured).total_seconds() <= 1:
        raise ValueError("current_axis_snapshot_stale_or_future")
    if (
        snapshot.get("stock_code") != symbol
        or snapshot.get("effective_venue") != "KRX"
        or snapshot.get("session_bucket") != "KRX_REGULAR"
        or snapshot.get("market_data_route") not in {"KRX", "krx", "krx_only"}
    ):
        raise ValueError("current_axis_exact_scope_mismatch")
    contexts = [
        row
        for row in bridge._walk_objects(exact)
        if row.get("schema") == "entry_candle_context_v1"
    ]
    preflight = ai_input_preflight(snapshot)
    if (
        not contexts
        or preflight.get("allowed") is not True
        or preflight.get("source_allowed") is not True
        or preflight.get("venue_consistent") is not True
        or preflight.get("blockers")
    ):
        raise ValueError("current_axis_input_preflight_blocked")
    canonical = capture._canonical_context_capture(
        exact, endpoint_name="analyze_target"
    )
    control = candidate["control"]
    payload_hash = bridge._producer_sha256(parsed)
    prompt_hash = hashlib.sha256(control["system_prompt"].encode()).hexdigest()
    envelope = {
        "endpoint": "analyze_target",
        "model": control["model"],
        "schema_name": control["schema_name"],
        "require_json": control["require_json"],
        "temperature": control["temperature"],
        "max_output_tokens": control["max_output_tokens"],
        "reasoning_effort": control["reasoning_effort"],
        "prompt_sha256": prompt_hash,
        "user_input_sha256": payload_hash,
    }
    common = {
        "request_id": f"prepared-{request_id}",
        "snapshot_id": snapshot["snapshot_id"],
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "market_data_route": snapshot["market_data_route"],
        "broker_route": snapshot["broker_route"],
        "endpoint": "analyze_target",
        "model": control["model"],
        "prompt_sha256": prompt_hash,
        "payload_sha256": payload_hash,
        "request_envelope_sha256": bridge._producer_sha256(envelope),
    }
    payload = {
        **common,
        "schema": capture.PAYLOAD_SCHEMA,
        "symbol": symbol,
        "schema_name": control["schema_name"],
        "require_json": control["require_json"],
        "temperature": control["temperature"],
        "max_output_tokens": control["max_output_tokens"],
        "reasoning_effort": control["reasoning_effort"],
        "input_format": "structured",
        "sanitized_user_input": parsed,
        "replay_exact": True,
        "canonical_context_capture": canonical,
    }
    trace = {
        **common,
        "schema": capture.TRACE_SCHEMA,
        "stock_code": symbol,
        "decision_trace_id": common["request_id"],
        "decision_ts": current.isoformat(),
        "decision_stage": "entry_screen",
        "provider_actual": "openai",
        "provider_called": False,
        "result_source": "prepared_input_not_sent",
        "payload_replay_exact": True,
        "request_capture_status": "captured",
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "canonical_context_capture_status": canonical.get("status"),
    }
    # Do not erase simulation or custody provenance while constructing the
    # pending request; the existing bridge rejects it as a natural live cohort.
    for key in (
        "sim_record_id",
        "sim_parent_record_id",
        "position_reconciliation_mode",
    ):
        if metadata.get(key):
            trace[key] = payload[key] = metadata[key]
    watermark, findings = bridge.exact_snapshot_watermark(trace, payload)
    if findings or watermark is None:
        raise ValueError("current_axis_capture_contract:" + ",".join(findings))
    source = (source_reader or live_source)(
        symbol, captured_at_ms=watermark["captured_at_ms"]
    )
    if source.get("collector_barrier_verified") is not True:
        raise ValueError("current_axis_collector_barrier_missing")
    reference = candidate["input_reference"]
    config = quality._micro_reversion_bridge_config(reference["bridge_config"])
    master = VerifiedSymbolMaster.from_payload(
        reference["symbol_master"], require_canonical_owner=True
    )
    lookup = master.lookup(symbol, as_of=current.date())
    symbol_metadata = {
        "lookup_status": lookup.status.value,
        "record": lookup.record.as_dict() if lookup.record else None,
        "symbol_master_artifact_sha256": bridge._sha256(reference["symbol_master"]),
    }
    evidence = bridge.build_tactical_evidence(
        trace=trace,
        payload=payload,
        market_rows=source["market"],
        depth_rows=source["depth"],
        event_references=source["references"],
        config=config,
        verified_symbol_metadata=symbol_metadata,
    )
    if (
        evidence["source_quality"]["status"] != "pass"
        or evidence["source_quality"]["blockers"]
    ):
        raise ValueError("current_axis_tactical_source_blocked")
    event_start = evidence["event"].get("event_detected_at_ms")
    if (
        not isinstance(event_start, int)
        or source["coverage_start_ms"]
        > event_start - config.context_lookback_sec * 1000
    ):
        raise ValueError("current_axis_pre_event_coverage_incomplete")
    for key in ("selected_cost_profile_id", "selected_cost_profile_content_sha256"):
        if evidence["economics"].get(key) != candidate["r3_candidate"][key]:
            raise ValueError("current_axis_cost_cohort_mismatch")
    sidecar = bridge.build_ask_depletion_feature_sidecar(
        evidence=evidence,
        market_rows=source["market"],
        depth_rows=source["depth"],
        max_depth_age_ms=config.max_depth_age_ms,
    )
    view = bridge._validated_ask_depletion_feature_view(sidecar, evidence=evidence)
    enriched = (
        deepcopy(parsed)
        if "exact_payload" in parsed
        else {"exact_payload": deepcopy(parsed)}
    )
    enriched[bridge.TACTICAL_EVIDENCE_SCHEMA] = evidence
    enriched[bridge.ASK_DEPLETION_FEATURE_VIEW_SCHEMA] = view
    text = json.dumps(
        enriched, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    return text, {
        "prepared_input_id": common["request_id"],
        "snapshot_id": snapshot["snapshot_id"],
        "snapshot_captured_at": snapshot["captured_at"],
        "collector_generation": source["generation"],
        "sequence_epoch": source["sequence_epoch"],
        "base_input_sha256": hashlib.sha256(base_input.encode()).hexdigest(),
        "input_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "tactical_evidence_sha256": evidence["evidence_sha256"],
        "ask_depletion_context_sha256": view["ask_depletion_context_sha256"],
        "provider_delivery_confirmed": False,
    }
