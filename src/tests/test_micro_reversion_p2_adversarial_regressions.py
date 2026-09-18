from __future__ import annotations

import base64
from copy import deepcopy
from datetime import date, timedelta
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge
from src.tests.test_ai_decision_quality import (
    _healthy_capacity_gate,
    _micro_reversion_action_neutral_bridge_fixture,
    _micro_reversion_materialization_fixture,
    _tamper_evident_openai_runner,
    _valid_micro_reversion_entry_response,
)
from src.tests.test_micro_reversion_ai_quality_bridge import (
    _entry_pipeline_allocator_row,
)


def _rows_from_bundle(
    source_bundle: dict,
    bundle_row: dict,
    *,
    pool_name: str,
    reference_field: str,
) -> list[dict]:
    return quality._micro_reversion_source_rows_from_pool(
        source_bundle=source_bundle,
        bundle_row=bundle_row,
        pool_name=pool_name,
        reference_field=reference_field,
    )


def _replace_referenced_source_row(
    source_bundle: dict,
    *,
    pool_name: str,
    reference_field: str,
    mutate,
) -> None:
    """Coherently reseal one pool row and every persisted reference to it."""

    bundle_row = source_bundle["rows"][0]
    old_hash = bundle_row[reference_field][0]
    pool = source_bundle["source_row_pool"][pool_name]
    replacement = deepcopy(pool.pop(old_hash))
    mutate(replacement)
    new_hash = quality._sha256(replacement)
    pool[new_hash] = replacement
    bundle_row[reference_field][0] = new_hash

    future_field = {
        "market": "market_row_sha256s",
        "depth": "depth_row_sha256s",
        "entry_pipeline": "entry_pipeline_row_sha256s",
    }.get(pool_name)
    future_refs = bundle_row.get("future_outcome_source_refs")
    if isinstance(future_refs, dict) and future_field:
        values = future_refs[future_field]
        if old_hash in values:
            values[values.index(old_hash)] = new_hash
            future_refs[f"{future_field}_sha256"] = quality._sha256(values)
            future_refs["future_source_refs_content_sha256"] = quality._sha256(
                {
                    key: value
                    for key, value in future_refs.items()
                    if key != "future_source_refs_content_sha256"
                }
            )
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )








@pytest.fixture(scope="module")
def bound_source_fixture() -> dict:
    prepared, seed_bundle = _micro_reversion_materialization_fixture()
    _, _, seed_bridge = _micro_reversion_action_neutral_bridge_fixture()
    seed_row = seed_bundle["rows"][0]
    bridge_row = seed_bridge["rows"][0]
    rebuild_source = bridge_row["future_outcome_rebuild_source"]
    source_pools = seed_bridge["future_outcome_source_pool"]["row_pools"]
    market_rows = _rows_from_bundle(
        seed_bundle,
        seed_row,
        pool_name="market",
        reference_field="source_market_row_sha256s",
    ) + [
        deepcopy(source_pools["market"][row_hash])
        for row_hash in rebuild_source["market_row_sha256s"]
    ]
    market_rows = list({quality._sha256(row): row for row in market_rows}.values())
    depth_rows = _rows_from_bundle(
        seed_bundle,
        seed_row,
        pool_name="depth",
        reference_field="source_depth_row_sha256s",
    ) + [
        deepcopy(source_pools["depth"][row_hash])
        for row_hash in rebuild_source["depth_row_sha256s"]
    ]
    depth_rows = list({quality._sha256(row): row for row in depth_rows}.values())
    event_references = _rows_from_bundle(
        seed_bundle,
        seed_row,
        pool_name="event_reference",
        reference_field="source_event_reference_sha256s",
    )
    pipeline_row = _entry_pipeline_allocator_row(quantity=5)
    pipeline_row["fields"]["ai_decision_trace_id"] = "trace-materialize-1"
    pipeline_row["emitted_at"] = "2026-08-14T09:00:17.100+09:00"
    pipeline_row["emitted_date"] = "2026-08-14"
    trace = seed_row["source_trace"]
    payload = seed_row["source_payload"]
    control_contract = seed_row["current_control_prompt_contract"]
    prompt_rows = [
        {
            "schema": "ai_decision_prompt_v1",
            "prompt_sha256": trace["prompt_sha256"],
            "endpoint": trace["endpoint"],
            "model": trace["model"],
            "schema_name": payload["schema_name"],
            "redacted": False,
            "replay_exact": True,
            "sanitized_prompt": control_contract["system_prompt"],
        }
    ]
    control_contracts = [
        {
            "decision_trace_id": trace["decision_trace_id"],
            "prompt_sha256": trace["prompt_sha256"],
            "prompt_contract": deepcopy(control_contract),
        }
    ]
    fixture = {
        "prepared": prepared,
        "seed_bundle": seed_bundle,
        "seed_row": seed_row,
        "trace": trace,
        "payload": payload,
        "prompt_rows": prompt_rows,
        "control_contracts": control_contracts,
        "market_rows": market_rows,
        "depth_rows": depth_rows,
        "event_references": event_references,
        "entry_pipeline_rows": [pipeline_row],
    }
    external_bridge = _build_external_bridge(fixture)
    source_bundle = _build_bound_source_bundle(fixture, external_bridge)
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
        outcome_source_bridge_report=external_bridge,
    )
    assert source_bundle["eligible_row_count"] == 1
    assert materialized["request_count"] == 3
    return {
        **fixture,
        "external_bridge": external_bridge,
        "source_bundle": source_bundle,
        "materialized": materialized,
    }
































def test_provider_capacity_receipt_recomputes_state_and_rejects_aliases(
    tmp_path,
    monkeypatch,
):
    target_date = "2026-08-25"
    capacity_path = tmp_path / "capacity.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    receipt = _healthy_capacity_gate(
        target_date=target_date,
        capacity_path=capacity_path,
    )
    assert (
        quality.validate_micro_reversion_provider_capacity_gate_receipt(
            receipt,
            expected_target_date=target_date,
        )
        == receipt
    )

    forged_state = deepcopy(receipt)
    forged_state["direct_disk_snapshot"]["disk_free_bytes"] = 0
    with pytest.raises(
        ValueError,
        match="provider_capacity_receipt_state_invalid",
    ):
        quality.validate_micro_reversion_provider_capacity_gate_receipt(
            forged_state,
            expected_target_date=target_date,
        )

    forged_authority = deepcopy(receipt)
    forged_authority["promotion_authority"] = True
    with pytest.raises(
        ValueError,
        match="provider_capacity_receipt_invalid",
    ):
        quality.validate_micro_reversion_provider_capacity_gate_receipt(
            forged_authority,
            expected_target_date=target_date,
        )












def test_current_source_bundle_rejects_unreferenced_raw_pool_row(
    bound_source_fixture,
):
    source_bundle = deepcopy(bound_source_fixture["source_bundle"])
    orphan = {"schema": "orphan_market_row", "value": 1}
    orphan_hash = quality._sha256(orphan)
    source_bundle["source_row_pool"]["market"][orphan_hash] = orphan
    source_bundle["source_row_pool_counts"]["market"] += 1
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="micro_reversion_source_row_pool_orphan_or_missing"
    ):
        quality._validate_micro_reversion_source_bundle_artifact(source_bundle)


@pytest.mark.parametrize(
    ("mutation", "pool_name", "reference_field"),
    (
        (
            lambda row: row.update(
                {
                    "exchange_timestamp": "2026-08-15T09:00:05.000+09:00",
                    "local_receive_timestamp": "2026-08-15T09:00:05.000+09:00",
                }
            ),
            "market",
            "source_market_row_sha256s",
        ),
        (
            lambda row: row.update(
                {
                    "exchange_timestamp": "2026-08-14T15:00:00.000+09:00",
                    "local_receive_timestamp": "2026-08-14T15:00:00.000+09:00",
                }
            ),
            "market",
            "source_market_row_sha256s",
        ),
        (
            lambda row: row.update({"sequence_epoch": 124}),
            "market",
            "source_market_row_sha256s",
        ),
        (
            lambda row: row.update(
                {
                    "event_detected_at_ms": 1_786_666_000_000,
                    "segment_event_detected_at_ms": 1_786_666_000_000,
                }
            ),
            "event_reference",
            "source_event_reference_sha256s",
        ),
        (
            lambda row: row.update(
                {"pipeline": "HOLDING_PIPELINE", "stage": "holding_flow"}
            ),
            "entry_pipeline",
            "source_entry_pipeline_row_sha256s",
        ),
    ),
    ids=(
        "cross_date_market",
        "out_of_window_market",
        "wrong_epoch_market",
        "future_event",
        "fabricated_holding_pipeline",
    ),
)
def test_current_source_validator_rejects_resealed_noncanonical_rows(
    bound_source_fixture,
    mutation,
    pool_name,
    reference_field,
):
    source_bundle = deepcopy(bound_source_fixture["source_bundle"])
    _replace_referenced_source_row(
        source_bundle,
        pool_name=pool_name,
        reference_field=reference_field,
        mutate=mutation,
    )

    with pytest.raises(
        ValueError,
        match=(
            "micro_reversion_source_rows_noncanonical|"
            "micro_reversion_entry_pipeline_source_rows_noncanonical|"
            "micro_reversion_future_source_refs_census_invalid"
        ),
    ):
        quality._validate_micro_reversion_source_bundle_artifact(source_bundle)






@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ("schema", "micro_reversion_source_bundle_schema_invalid"),
        ("status", "micro_reversion_source_bundle_status_invalid"),
        ("extra_pool", "micro_reversion_source_row_pool_shape_invalid"),
        ("scalar_exclusion", "micro_reversion_source_bundle_exclusion_invalid"),
        ("exclusion_extra_field", "micro_reversion_source_bundle_exclusion_invalid"),
    ),
)
def test_source_bundle_strict_shape_rejects_resealed_mutations(
    bound_source_fixture,
    mutation,
    reason,
):
    source_bundle = deepcopy(bound_source_fixture["source_bundle"])
    if mutation == "schema":
        source_bundle["schema"] = "forged_source_bundle"
    elif mutation == "status":
        source_bundle["status"] = "provider_ready"
    elif mutation == "extra_pool":
        source_bundle["source_row_pool"]["hidden"] = {"opaque": "payload"}
        source_bundle["source_row_pool_counts"]["hidden"] = 1
    elif mutation == "scalar_exclusion":
        source_bundle["exclusions"] = [7]
        source_bundle["excluded_row_count"] = 1
        source_bundle["prepared_request_count"] = len(source_bundle["rows"]) + 1
    else:
        source_bundle["exclusions"] = [
            {
                "decision_trace_id": "excluded-shape-test",
                "paired_replay_id": "excluded-shape-test:v1",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "reason": "test_exclusion",
                "source_quality_blockers": [],
                "hidden_authority": True,
            }
        ]
        source_bundle["excluded_row_count"] = 1
        source_bundle["prepared_request_count"] = len(source_bundle["rows"]) + 1
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )

    with pytest.raises(ValueError, match=reason):
        quality._validate_micro_reversion_source_bundle_artifact(source_bundle)


def test_current_source_and_bridge_reject_resealed_positive_authority_alias(
    bound_source_fixture,
    monkeypatch,
):
    source_bundle = deepcopy(bound_source_fixture["source_bundle"])
    source_bundle["provider_effect"] = True
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )
    with pytest.raises(
        ValueError, match="micro_reversion_source_bundle_source_only_authority_invalid"
    ):
        quality._validate_micro_reversion_source_bundle_artifact(source_bundle)

    monkeypatch.setattr(quality, "CURRENT_DESIGN_ACTIVATION_DATE", "2026-08-14")
    bridge_report = deepcopy(bound_source_fixture["external_bridge"])
    bridge_report.update(quality.ABLATION_SOURCE_ONLY_AUTHORITY)
    bridge_report["provider_effect"] = True
    bridge_report["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in bridge_report.items()
            if key != "report_content_sha256"
        }
    )
    with pytest.raises(
        ValueError, match="micro_reversion_outcome_source_bridge_authority_invalid"
    ):
        quality._micro_reversion_outcome_source_commitment(
            bridge_report,
            expected_target_date="2026-08-14",
        )








def test_current_provider_custody_rejects_present_empty_checkpoint_generation():
    with pytest.raises(
        ValueError,
        match="historical_backfill_checkpoint_census_invalid",
    ):
        quality._micro_reversion_provider_checkpoint_bindings(
            target_date=quality.CURRENT_DESIGN_ACTIVATION_DATE,
            materialized_report={},
            outcome_label_artifact={},
            checkpoint_artifact={},
            provider_ablation_sample_floor_content_sha256="f" * 64,
        )
















def test_current_bridge_rejects_unreferenced_future_outcome_pool_row(
    bound_source_fixture,
):
    bridge_report = deepcopy(bound_source_fixture["external_bridge"])
    source_pool = bridge_report["future_outcome_source_pool"]
    orphan = {"schema": "orphan_future_market_row", "value": 1}
    orphan_hash = quality._sha256(orphan)
    source_pool["row_pools"]["market"][orphan_hash] = orphan
    source_pool["row_pool_counts"]["market"] += 1
    pool_body = {
        key: value
        for key, value in source_pool.items()
        if key != "source_pool_content_sha256"
    }
    source_pool["source_pool_content_sha256"] = quality._sha256(pool_body)
    for row in bridge_report["rows"]:
        rebuild = row["future_outcome_rebuild_source"]
        rebuild_body = {
            key: value
            for key, value in rebuild.items()
            if key != "rebuild_source_sha256"
        }
        rebuild_body["source_pool_content_sha256"] = source_pool[
            "source_pool_content_sha256"
        ]
        row["future_outcome_rebuild_source"] = {
            **rebuild_body,
            "rebuild_source_sha256": quality._sha256(rebuild_body),
        }
    bridge_report["future_outcome_source_pool_content_sha256"] = source_pool[
        "source_pool_content_sha256"
    ]
    bridge_report["future_outcome_source_pool_artifact_sha256"] = quality._sha256(
        source_pool
    )
    bridge_report["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in bridge_report.items()
            if key != "report_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="future_outcome_source_pool_orphan_or_missing"
    ):
        quality._micro_reversion_outcome_source_commitment(
            bridge_report,
            expected_target_date="2026-08-14",
        )


def test_current_bridge_rejects_referenced_cross_date_row_after_coherent_reseal(
    bound_source_fixture,
):
    bridge_report = deepcopy(bound_source_fixture["external_bridge"])
    source_pool = bridge_report["future_outcome_source_pool"]
    injected = deepcopy(bound_source_fixture["market_rows"][0])
    injected.update(
        {
            "exchange_timestamp": "2026-08-15T09:00:11.500+09:00",
            "local_receive_timestamp": "2026-08-15T09:00:11.500+09:00",
            "source_sequence": 999,
            "series_sequence": 999,
        }
    )
    injected_hash = quality._sha256(injected)
    source_pool["row_pools"]["market"][injected_hash] = injected
    source_pool["row_pool_counts"]["market"] += 1
    pool_body = {
        key: value
        for key, value in source_pool.items()
        if key != "source_pool_content_sha256"
    }
    source_pool["source_pool_content_sha256"] = quality._sha256(pool_body)

    target_row = bridge_report["rows"][0]
    for row in bridge_report["rows"]:
        rebuild = row["future_outcome_rebuild_source"]
        rebuild_body = {
            key: deepcopy(value)
            for key, value in rebuild.items()
            if key != "rebuild_source_sha256"
        }
        rebuild_body["source_pool_content_sha256"] = source_pool[
            "source_pool_content_sha256"
        ]
        if row is target_row:
            rebuild_body["market_row_sha256s"].append(injected_hash)
            rebuild_body["market_row_count"] += 1
            rebuild_body["market_row_sha256s_sha256"] = quality._sha256(
                rebuild_body["market_row_sha256s"]
            )
        row["future_outcome_rebuild_source"] = {
            **rebuild_body,
            "rebuild_source_sha256": quality._sha256(rebuild_body),
        }
    bridge_report["future_outcome_source_pool_content_sha256"] = source_pool[
        "source_pool_content_sha256"
    ]
    bridge_report["future_outcome_source_pool_artifact_sha256"] = quality._sha256(
        source_pool
    )
    bridge_report["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in bridge_report.items()
            if key != "report_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="future_outcome_rebuild_source_noncanonical_rows"
    ):
        quality._micro_reversion_outcome_source_commitment(
            bridge_report,
            expected_target_date="2026-08-14",
        )


def _build_external_bridge(
    fixture: dict,
    *,
    market_rows: list[dict] | None = None,
    depth_rows: list[dict] | None = None,
    entry_pipeline_rows: list[dict] | None = None,
) -> dict:
    seed_row = fixture["seed_row"]
    return bridge.build_bridge_report(
        target_date="2026-08-14",
        traces=[fixture["trace"]],
        payloads=[fixture["payload"]],
        market_rows=market_rows or fixture["market_rows"],
        depth_rows=depth_rows or fixture["depth_rows"],
        event_references=fixture["event_references"],
        entry_pipeline_rows=(
            entry_pipeline_rows
            if entry_pipeline_rows is not None
            else fixture["entry_pipeline_rows"]
        ),
        entry_pipeline_source={
            "status": "available_hash_verified",
            "source_path": "test",
            "source_sha256": "c" * 64,
        },
        config=bridge.BridgeConfig(**seed_row["bridge_config"]),
        verified_symbol_metadata_by_trace={
            fixture["trace"]["decision_trace_id"]: seed_row["verified_symbol_metadata"]
        },
    )


def _build_bound_source_bundle(
    fixture: dict,
    external_bridge: dict,
    *,
    market_rows: list[dict] | None = None,
    depth_rows: list[dict] | None = None,
    entry_pipeline_rows: list[dict] | None = None,
) -> dict:
    seed_row = fixture["seed_row"]
    return quality.build_micro_reversion_source_bundle(
        target_date="2026-08-14",
        prepared_requests=fixture["prepared"],
        traces=[fixture["trace"]],
        payloads=[fixture["payload"]],
        prompt_rows=fixture["prompt_rows"],
        control_prompt_contracts=fixture["control_contracts"],
        market_rows=fixture["market_rows"] if market_rows is None else market_rows,
        depth_rows=fixture["depth_rows"] if depth_rows is None else depth_rows,
        event_references=fixture["event_references"],
        entry_pipeline_rows=(
            fixture["entry_pipeline_rows"]
            if entry_pipeline_rows is None
            else entry_pipeline_rows
        ),
        bridge_config=seed_row["bridge_config"],
        verified_symbol_metadata_by_trace={
            fixture["trace"]["decision_trace_id"]: seed_row["verified_symbol_metadata"]
        },
        outcome_source_bridge_report=external_bridge,
    )


@pytest.mark.parametrize("source_kind", ("market", "depth", "entry_pipeline"))
def test_post_snapshot_raw_rewrite_is_rejected_against_independent_source(
    bound_source_fixture,
    source_kind,
):
    rewritten_market = deepcopy(bound_source_fixture["market_rows"])
    rewritten_depth = deepcopy(bound_source_fixture["depth_rows"])
    rewritten_pipeline = deepcopy(bound_source_fixture["entry_pipeline_rows"])
    if source_kind == "market":
        rewritten_market[-1]["trade_qty"] += 7
    elif source_kind == "depth":
        latest = rewritten_depth[-1]
        latest["best_ask_qty"] += 7
        latest["ask_levels"][0][2] += 7
        latest["ask_depth"] += 7
        latest["route_depth_totals"]["KRX"]["ask"] += 7
        latest["route_depth_totals"]["combined"]["ask"] += 7
    else:
        rewritten_pipeline[0]["fields"]["effective_qty"] = "4"

    rewritten_bridge = _build_external_bridge(
        bound_source_fixture,
        market_rows=rewritten_market,
        depth_rows=rewritten_depth,
        entry_pipeline_rows=rewritten_pipeline,
    )
    assert rewritten_bridge["rows"][0]["future_outcome"]["outcome_eligibility"] == (
        "eligible_observation_only" if source_kind == "entry_pipeline" else "eligible"
    )
    assert (
        rewritten_bridge["rows"][0][bridge.TACTICAL_EVIDENCE_SCHEMA]
        == bound_source_fixture["seed_row"]["evidence"]
    )

    result = _build_bound_source_bundle(bound_source_fixture, rewritten_bridge)

    assert result["eligible_row_count"] == 0
    assert [row["reason"] for row in result["exclusions"]] == [
        "micro_reversion_outcome_source_independent_raw_mismatch"
    ]


def test_source_validator_rejects_resealed_future_refs_not_in_external_bridge(
    bound_source_fixture,
):
    tampered = deepcopy(bound_source_fixture["source_bundle"])
    bundle_row = tampered["rows"][0]
    references = bundle_row["source_entry_pipeline_row_sha256s"]
    old_hash = references[0]
    pipeline_pool = tampered["source_row_pool"]["entry_pipeline"]
    rewritten_row = pipeline_pool.pop(old_hash)
    rewritten_row["fields"]["effective_qty"] = "4"
    new_hash = quality._sha256(rewritten_row)
    pipeline_pool[new_hash] = rewritten_row
    references[0] = new_hash
    tampered["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered.items()
            if key != "source_bundle_content_sha256"
        }
    )
    with pytest.raises(
        ValueError,
        match="micro_reversion_future_source_refs_census_invalid",
    ):
        quality._validate_micro_reversion_source_bundle_artifact(tampered)


def test_action_neutral_artifact_cannot_hide_materialized_parent_census(
    bound_source_fixture,
):
    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bound_source_fixture["external_bridge"],
        materialized_report=bound_source_fixture["materialized"],
    )
    quality._validate_micro_reversion_outcome_label_artifact(
        artifact,
        source_bridge_report=bound_source_fixture["external_bridge"],
        expected_design_version=quality.CURRENT_DESIGN_VERSION,
        expected_target_date="2026-08-14",
        expected_materialized_report_content_sha256=bound_source_fixture[
            "materialized"
        ]["report_content_sha256"],
        expected_materialized_report=bound_source_fixture["materialized"],
    )
    hidden = deepcopy(artifact)
    hidden.update(
        {
            "prepared_parent_count": 0,
            "eligible_label_count": 0,
            "labels": [],
            "materialized_parent_binding_count": 0,
            "materialized_parent_bindings": [],
            "materialized_parent_bindings_sha256": quality._sha256([]),
        }
    )
    hidden["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in hidden.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(
        ValueError,
        match="micro_reversion_action_neutral_materialized_parent_binding_mismatch",
    ):
        quality._validate_micro_reversion_outcome_label_artifact(
            hidden,
            source_bridge_report=bound_source_fixture["external_bridge"],
            expected_design_version=quality.CURRENT_DESIGN_VERSION,
            expected_target_date="2026-08-14",
            expected_materialized_report_content_sha256=bound_source_fixture[
                "materialized"
            ]["report_content_sha256"],
            expected_materialized_report=bound_source_fixture["materialized"],
        )


def test_action_neutral_artifact_rejects_resealed_wrong_child_schema_and_ev(
    bound_source_fixture,
):
    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bound_source_fixture["external_bridge"],
        materialized_report=bound_source_fixture["materialized"],
    )
    forged = deepcopy(artifact)
    label = forged["labels"][0]
    label["schema"] = "forged_action_neutral_label"
    primary = label["primary_horizon_key"]
    label["horizon_metrics"][primary]["source_quality_adjusted_ev_pct"] = 999.0
    label["label_content_sha256"] = quality._sha256(
        {key: value for key, value in label.items() if key != "label_content_sha256"}
    )
    forged["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in forged.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="micro_reversion_action_neutral_label_schema_invalid"
    ):
        quality._validate_micro_reversion_outcome_label_artifact(
            forged,
            source_bridge_report=bound_source_fixture["external_bridge"],
            expected_design_version=quality.CURRENT_DESIGN_VERSION,
            expected_target_date="2026-08-14",
            expected_materialized_report_content_sha256=bound_source_fixture[
                "materialized"
            ]["report_content_sha256"],
            expected_materialized_report=bound_source_fixture["materialized"],
        )


@pytest.mark.parametrize(
    ("authority_field", "validator", "error"),
    [
        (
            field,
            validator,
            expected_error,
        )
        for field in ("runtime_authority", "order_authority", "provider_authority")
        for validator, expected_error in (
            (
                quality._validate_micro_reversion_action_neutral_label,
                "micro_reversion_action_neutral_label_source_only_authority_invalid",
            ),
            (
                quality._validate_micro_reversion_outcome_label_artifact,
                "micro_reversion_action_neutral_artifact_source_only_authority_invalid",
            ),
        )
    ],
)
def test_current_action_neutral_resealed_authority_escalation_is_rejected(
    authority_field,
    validator,
    error,
):
    value = {
        "schema": quality.MICRO_REVERSION_ACTION_NEUTRAL_LABEL_SCHEMA,
        "target_date": quality.CURRENT_DESIGN_ACTIVATION_DATE,
        "ablation_design_version": quality.CURRENT_DESIGN_VERSION,
        **quality.ABLATION_SOURCE_ONLY_AUTHORITY,
    }
    value[authority_field] = True
    hash_field = (
        "label_content_sha256"
        if validator is quality._validate_micro_reversion_action_neutral_label
        else "artifact_content_sha256"
    )
    value[hash_field] = quality._sha256(value)

    with pytest.raises(ValueError, match=error):
        validator(value)








def test_source_bundle_second_pass_uses_each_distinct_parent_trace():
    prepared, seed_bundle = _micro_reversion_materialization_fixture()
    _, _, seed_bridge = _micro_reversion_action_neutral_bridge_fixture()
    seed_row = seed_bundle["rows"][0]
    bridge_row = seed_bridge["rows"][0]
    rebuild_source = bridge_row["future_outcome_rebuild_source"]
    source_pools = seed_bridge["future_outcome_source_pool"]["row_pools"]
    market_rows = _rows_from_bundle(
        seed_bundle,
        seed_row,
        pool_name="market",
        reference_field="source_market_row_sha256s",
    ) + [
        deepcopy(source_pools["market"][row_hash])
        for row_hash in rebuild_source["market_row_sha256s"]
    ]
    market_rows = list({quality._sha256(row): row for row in market_rows}.values())
    depth_rows = _rows_from_bundle(
        seed_bundle,
        seed_row,
        pool_name="depth",
        reference_field="source_depth_row_sha256s",
    ) + [
        deepcopy(source_pools["depth"][row_hash])
        for row_hash in rebuild_source["depth_row_sha256s"]
    ]
    depth_rows = list({quality._sha256(row): row for row in depth_rows}.values())
    event_references = _rows_from_bundle(
        seed_bundle,
        seed_row,
        pool_name="event_reference",
        reference_field="source_event_reference_sha256s",
    )
    trace_one = deepcopy(seed_row["source_trace"])
    trace_two = deepcopy(trace_one)
    trace_two.update(
        {
            "decision_trace_id": "trace-materialize-2",
            "request_id": "request-materialize-2",
        }
    )
    payload_one = deepcopy(seed_row["source_payload"])
    payload_two = deepcopy(payload_one)
    payload_two["request_id"] = "request-materialize-2"
    request_one = deepcopy(prepared[0])
    request_two = deepcopy(request_one)
    request_two.update(
        {
            "decision_trace_id": "trace-materialize-2",
            "paired_replay_id": "pair-materialize-2",
            "outcome_join_key": "trace-materialize-2:v1",
        }
    )
    trace_ids = (trace_one["decision_trace_id"], trace_two["decision_trace_id"])
    metadata = {
        trace_id: deepcopy(seed_row["verified_symbol_metadata"])
        for trace_id in trace_ids
    }
    external_bridge = bridge.build_bridge_report(
        target_date="2026-08-14",
        traces=[trace_one, trace_two],
        payloads=[payload_one, payload_two],
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=event_references,
        config=bridge.BridgeConfig(**seed_row["bridge_config"]),
        verified_symbol_metadata_by_trace=metadata,
    )
    control = seed_row["current_control_prompt_contract"]
    prompt_rows = [
        {
            "schema": "ai_decision_prompt_v1",
            "prompt_sha256": trace_one["prompt_sha256"],
            "endpoint": trace_one["endpoint"],
            "model": trace_one["model"],
            "schema_name": payload_one["schema_name"],
            "redacted": False,
            "replay_exact": True,
            "sanitized_prompt": control["system_prompt"],
        }
    ]
    control_contracts = [
        {
            "decision_trace_id": trace_id,
            "prompt_sha256": trace_one["prompt_sha256"],
            "prompt_contract": deepcopy(control),
        }
        for trace_id in trace_ids
    ]

    result = quality.build_micro_reversion_source_bundle(
        target_date="2026-08-14",
        prepared_requests=[request_one, request_two],
        traces=[trace_one, trace_two],
        payloads=[payload_one, payload_two],
        prompt_rows=prompt_rows,
        control_prompt_contracts=control_contracts,
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=event_references,
        bridge_config=seed_row["bridge_config"],
        verified_symbol_metadata_by_trace=metadata,
        outcome_source_bridge_report=external_bridge,
    )

    assert result["eligible_row_count"] == 2
    assert result["excluded_row_count"] == 0
    assert {row["decision_trace_id"] for row in result["rows"]} == set(trace_ids)
