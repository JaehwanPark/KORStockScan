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
from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle
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
from src.tests.test_micro_reversion_ai_quality_cycle import (
    _current_execution_report,
    _execution_report,
    _lifecycle_report,
    _seal_lifecycle_report,
    _reseal_execution_report,
    _reseal_execution_result_ids,
    _sample_floor_materialized_report,
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


def _retarget_normalized_execution_row(
    row: dict,
    *,
    target_date: str,
    parent_id: str,
    trace_id: str,
) -> dict:
    """Retarget an isolated normalized-row fixture and all local commitments."""

    row.update(
        {
            "target_date": target_date,
            "paired_replay_parent_id": parent_id,
            "decision_trace_id": trace_id,
            "decision_ts": f"{target_date}T09:00:00+09:00",
        }
    )
    full_parent_census = deepcopy(row["full_parent_census"])
    full_parent_census["paired_replay_parent_id"] = parent_id
    row["full_parent_census"] = full_parent_census
    row["full_parent_census_sha256"] = cycle._sha256(full_parent_census)
    commitment = deepcopy(row["execution_source_commitment"])
    commitment.update(
        {
            "target_date": target_date,
            "paired_replay_parent_id": parent_id,
            "decision_trace_id": trace_id,
            "full_parent_census_sha256": row["full_parent_census_sha256"],
        }
    )
    if target_date >= cycle.CURRENT_DESIGN_ACTIVATION_DATE:
        commitment.update(
            {
                "provider_ablation_sample_floor_content_sha256": "e" * 64,
                "provider_ablation_sample_floor_artifact_sha256": "f" * 64,
            }
        )
    commitment["commitment_sha256"] = cycle._sha256(
        {key: value for key, value in commitment.items() if key != "commitment_sha256"}
    )
    row["execution_source_commitment"] = commitment
    row["execution_source_commitment_sha256"] = commitment["commitment_sha256"]
    return row


def _postactivation_lineage_fixture(bound_source_fixture, monkeypatch) -> dict:
    target_date = "2026-08-14"
    monkeypatch.setattr(quality, "CURRENT_DESIGN_ACTIVATION_DATE", target_date)
    monkeypatch.setattr(
        quality,
        "MICRO_REVERSION_PROVIDER_RESPONSE_CHAIN_ACTIVATION_DATE",
        target_date,
    )
    monkeypatch.setattr(bridge, "CURRENT_DESIGN_ACTIVATION_DATE", target_date)

    paired = {
        "schema": quality.PAIRED_SCHEMA,
        "target_date": target_date,
        "status": "paired_replay_requests_ready_candidate_not_executed",
        "request_count": len(bound_source_fixture["prepared"]),
        "result_count": 0,
        "candidate_execution_performed": False,
        "prepared_request_count": len(bound_source_fixture["prepared"]),
        "sample_floor_excluded_request_count": 0,
        "prepared_request_exclusion_count": 0,
        "prepared_request_exclusions": [],
        "requests": deepcopy(bound_source_fixture["prepared"]),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    prepared_artifact = cycle.build_prepared_request_artifact(
        target_date=target_date,
        paired_report=paired,
        source={
            "resolved_path": "test",
            "stored_sha256": "a" * 64,
            "logical_content_sha256": quality._sha256(paired),
        },
    )
    external_bridge = deepcopy(bound_source_fixture["external_bridge"])
    external_bridge.update(quality.ABLATION_SOURCE_ONLY_AUTHORITY)
    external_bridge["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in external_bridge.items()
            if key != "report_content_sha256"
        }
    )
    source_bundle = deepcopy(bound_source_fixture["source_bundle"])
    source_bundle["outcome_source_commitment"] = (
        quality._micro_reversion_outcome_source_commitment(
            external_bridge,
            expected_target_date=target_date,
        )
    )
    source_bundle.update(quality.ABLATION_SOURCE_ONLY_AUTHORITY)
    source_bundle["selection_authority"] = False
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=deepcopy(prepared_artifact["prepared_requests"]),
        bridge_source_bundle=deepcopy(source_bundle),
        outcome_source_bridge_report=external_bridge,
    )
    materialized_body = {
        key: value
        for key, value in materialized.items()
        if key != "report_content_sha256"
    }
    materialized_body.update(
        {
            "prepared_request_artifact_path": "prepared.json",
            "prepared_request_artifact_sha256": quality._sha256(prepared_artifact),
            "source_bundle_path": "source_bundle.json",
        }
    )
    materialized = {
        **materialized_body,
        "report_content_sha256": quality._sha256(materialized_body),
    }
    return {
        "target_date": target_date,
        "paired": paired,
        "prepared": prepared_artifact,
        "source_bundle": source_bundle,
        "bridge": external_bridge,
        "materialized": materialized,
    }


def _persisted_provider_floor_fixture(tmp_path, monkeypatch):
    materialized_root = tmp_path / "materialized"
    source_root = tmp_path / "source"
    prepared_root = tmp_path / "prepared"
    bridge_root = tmp_path / "bridge"
    paired_root = tmp_path / "paired"
    for root in (
        materialized_root,
        source_root,
        prepared_root,
        bridge_root,
        paired_root,
    ):
        root.mkdir()
    monkeypatch.setattr(
        quality,
        "micro_reversion_materialized_request_path",
        lambda day: materialized_root / f"materialized-{day}.json",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_source_bundle_path",
        lambda day: source_root / f"source-{day}.json",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_prepared_request_path",
        lambda day: prepared_root / f"prepared-{day}.json",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_bridge_report_path",
        lambda day: bridge_root / f"bridge-{day}.json",
    )
    monkeypatch.setattr(quality, "PAIRED_REPORT_DIR", paired_root)
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda report: list(report.get("requests") or []),
    )
    monkeypatch.setattr(
        cycle,
        "_validate_current_materialized_source_lineage",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "validate_current_materialized_source_lineage",
        lambda **_kwargs: None,
    )
    reports = []
    materialized_reports = []
    days = (
        "2026-08-25",
        "2026-08-26",
        "2026-08-27",
        "2026-08-28",
        "2026-08-31",
        "2026-09-01",
    )
    for index, day in enumerate(days):
        report = _sample_floor_materialized_report(
            day,
            parent_start=index * 4,
            parent_count=4,
        )
        companions = {
            "source_bundle": {"target_date": day, "kind": "source"},
            "prepared": {"target_date": day, "kind": "prepared"},
            "bridge": {"target_date": day, "kind": "bridge"},
            "paired": {"target_date": day, "kind": "paired"},
        }
        paths = {
            "source_bundle": quality.micro_reversion_source_bundle_path(day),
            "prepared": quality.micro_reversion_prepared_request_path(day),
            "bridge": quality.micro_reversion_bridge_report_path(day),
            "paired": paired_root / f"ai_prompt_paired_replay_{day}.json",
        }
        materialized_path = quality.micro_reversion_materialized_request_path(day)
        materialized_path.write_text(json.dumps(report), encoding="utf-8")
        for name, path in paths.items():
            path.write_text(json.dumps(companions[name]), encoding="utf-8")
        reports.append(report)
        materialized_reports.append(
            (
                day,
                materialized_path,
                report,
                {**companions, "paths": paths},
            )
        )
    floor = cycle._provider_ablation_sample_floor_from_reports(
        target_date=days[-1],
        materialized_reports=materialized_reports,
    )
    assert floor["pass"] is True
    return (
        floor,
        reports[-1],
        quality.micro_reversion_materialized_request_path(days[1]),
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


def test_provider_floor_leaf_revalidates_full_canonical_window(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, _historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )

    validated = quality.validate_micro_reversion_provider_ablation_floor_artifact(
        floor,
        expected_target_date=floor["target_date"],
        current_materialized_report=current_materialized,
    )

    assert validated == floor


def test_provider_floor_leaf_admits_exact_historical_materialized_generation(
    tmp_path,
    monkeypatch,
):
    floor, _current_materialized, historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    historical_materialized = json.loads(historical_path.read_text(encoding="utf-8"))

    validated = quality.validate_micro_reversion_provider_ablation_floor_artifact(
        floor,
        expected_target_date=floor["target_date"],
        current_materialized_report=historical_materialized,
        expected_materialized_target_date="2026-08-26",
    )

    assert validated == floor


def test_provider_floor_leaf_rejects_historical_generation_not_in_floor_window(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, _historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    outside = deepcopy(current_materialized)
    outside["target_date"] = "2026-09-02"

    with pytest.raises(
        ValueError,
        match="provider_ablation_floor_materialized_after_floor_target",
    ):
        quality.validate_micro_reversion_provider_ablation_floor_artifact(
            floor,
            expected_target_date=floor["target_date"],
            current_materialized_report=outside,
            expected_materialized_target_date="2026-09-02",
        )


def test_provider_floor_validation_cache_loads_each_generation_once(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, _historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    loaded_paths: list[str] = []

    def counting_loader(path):
        loaded_paths.append(str(path))
        return quality._load_exact_p2_json(path)

    validation_cache = quality.MicroReversionProviderFloorValidationCache()
    for _ in range(2):
        quality.validate_micro_reversion_provider_ablation_floor_artifact(
            floor,
            expected_target_date=floor["target_date"],
            current_materialized_report=current_materialized,
            artifact_loader=counting_loader,
            validation_cache=validation_cache,
        )

    # Five trading-date generations, each with materialized plus four exact
    # companions, are heavy-read once despite an overlapping second floor.
    assert len(loaded_paths) == 5 * 5
    assert len(set(loaded_paths)) == 5 * 5
    assert len(validation_cache._generations) == 5
    for generation in validation_cache._generations.values():
        assert "materialized" not in generation
        assert "companions" not in generation
        assert set(generation) == {
            "logical_paths",
            "identity_census",
            "artifact_loader_identity",
            "summary",
            "summary_content_sha256",
        }
        assert len(quality._canonical_bytes(generation["summary"])) < 64 * 1024
    quality.finalize_micro_reversion_provider_floor_validation_cache(validation_cache)


def test_provider_floor_validation_cache_finalizer_rejects_generation_change(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    validation_cache = quality.MicroReversionProviderFloorValidationCache()
    quality.validate_micro_reversion_provider_ablation_floor_artifact(
        floor,
        expected_target_date=floor["target_date"],
        current_materialized_report=current_materialized,
        validation_cache=validation_cache,
    )
    historical_payload = json.loads(historical_path.read_text(encoding="utf-8"))
    historical_path.write_text(
        json.dumps(historical_payload, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="provider_ablation_floor_cached_generation_changed",
    ):
        quality.finalize_micro_reversion_provider_floor_validation_cache(
            validation_cache
        )


def test_provider_floor_leaf_rejects_resealed_authority_alias(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, _historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    floor["promotion_authority"] = True
    floor["floor_content_sha256"] = quality._sha256(
        {key: value for key, value in floor.items() if key != "floor_content_sha256"}
    )

    with pytest.raises(ValueError, match="provider_ablation_floor_fields_invalid"):
        quality.validate_micro_reversion_provider_ablation_floor_artifact(
            floor,
            expected_target_date=floor["target_date"],
            current_materialized_report=current_materialized,
        )


def test_provider_floor_leaf_rejects_missing_historical_canonical_artifact(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    historical_path.unlink()

    with pytest.raises(
        ValueError,
        match="provider_ablation_floor_orphan_companion_generation",
    ):
        quality.validate_micro_reversion_provider_ablation_floor_artifact(
            floor,
            expected_target_date=floor["target_date"],
            current_materialized_report=current_materialized,
        )


def test_provider_floor_leaf_rejects_divergent_dual_generation(
    tmp_path,
    monkeypatch,
):
    floor, current_materialized, historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    historical_path.with_name(f"{historical_path.name}.gz").write_bytes(
        gzip.compress(b'{"tampered":true}\n', mtime=0)
    )

    with pytest.raises(ValueError, match="json_artifact_plain_gzip_conflict"):
        quality.validate_micro_reversion_provider_ablation_floor_artifact(
            floor,
            expected_target_date=floor["target_date"],
            current_materialized_report=current_materialized,
        )


@pytest.mark.parametrize("broken_representation", ("plain", "gzip"))
def test_provider_floor_leaf_rejects_broken_symlink_generation(
    tmp_path,
    monkeypatch,
    broken_representation,
):
    floor, current_materialized, historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    historical_path.unlink()
    broken_path = (
        historical_path
        if broken_representation == "plain"
        else historical_path.with_name(f"{historical_path.name}.gz")
    )
    broken_path.symlink_to(tmp_path / "missing-materialized-target.json")

    with pytest.raises(ValueError, match="json_artifact_path_type_invalid"):
        quality.validate_micro_reversion_provider_ablation_floor_artifact(
            floor,
            expected_target_date=floor["target_date"],
            current_materialized_report=current_materialized,
        )


@pytest.mark.parametrize("broken_representation", ("plain", "gzip"))
def test_provider_floor_producer_censuses_broken_symlink_as_invalid_present_day(
    tmp_path,
    monkeypatch,
    broken_representation,
):
    floor, current_materialized, historical_path = _persisted_provider_floor_fixture(
        tmp_path, monkeypatch
    )
    target_date = str(floor["target_date"])

    def canonical_paths(day: str) -> dict[str, Path]:
        return {
            "materialized": quality.micro_reversion_materialized_request_path(day),
            "source_bundle": quality.micro_reversion_source_bundle_path(day),
            "prepared": quality.micro_reversion_prepared_request_path(day),
            "bridge_report": quality.micro_reversion_bridge_report_path(day),
            "paired_report": quality.PAIRED_REPORT_DIR
            / f"ai_prompt_paired_replay_{day}.json",
        }

    monkeypatch.setattr(cycle, "_default_paths", canonical_paths)
    current_paths = canonical_paths(target_date)
    current_companions = {
        "source_bundle": json.loads(
            current_paths["source_bundle"].read_text(encoding="utf-8")
        ),
        "prepared": json.loads(current_paths["prepared"].read_text(encoding="utf-8")),
        "bridge": json.loads(
            current_paths["bridge_report"].read_text(encoding="utf-8")
        ),
        "paired": json.loads(
            current_paths["paired_report"].read_text(encoding="utf-8")
        ),
        "paths": {
            "source_bundle": current_paths["source_bundle"],
            "prepared": current_paths["prepared"],
            "bridge": current_paths["bridge_report"],
            "paired": current_paths["paired_report"],
        },
    }
    historical_path.unlink()
    broken_path = (
        historical_path
        if broken_representation == "plain"
        else historical_path.with_name(f"{historical_path.name}.gz")
    )
    broken_path.symlink_to(tmp_path / "missing-materialized-target.json")

    rebuilt = cycle._collect_provider_ablation_sample_floor(
        target_date=target_date,
        current_materialized=current_materialized,
        current_companions=current_companions,
        selected_paths={"materialized": current_paths["materialized"]},
    )

    assert rebuilt["pass"] is False
    assert rebuilt["status"] == "blocked_invalid_materialized_history"
    assert any(
        finding.startswith("materialized_contract_invalid:2026-08-26:")
        for finding in rebuilt["contract_findings"]
    )


@pytest.mark.parametrize("broken_representation", ("plain", "gzip"))
def test_rolling_input_census_reports_broken_execution_symlink(
    tmp_path,
    monkeypatch,
    broken_representation,
):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    logical = tmp_path / "execution" / f"execution-{target_date}.json"
    logical.parent.mkdir(parents=True)
    broken_path = (
        logical
        if broken_representation == "plain"
        else logical.with_name(f"{logical.name}.gz")
    )
    broken_path.symlink_to(tmp_path / "missing-execution-target.json")
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _day: logical,
    )
    monkeypatch.setattr(cycle, "DATA_DIR", tmp_path / "isolated-data")
    monkeypatch.setattr(cycle, "LIFECYCLE_REPORT_ROOT", tmp_path / "lifecycle")
    monkeypatch.setattr(cycle, "ECONOMIC_REPORT_ROOT", tmp_path / "economic")

    *_, diagnostics = cycle._collect_rolling_inputs(
        target_date=target_date,
        lookback_calendar_days=1,
    )

    assert diagnostics == [
        {
            "target_date": target_date,
            "artifact": "execution",
            "status": "invalid",
            "reason": "ValueError",
        }
    ]


@pytest.mark.parametrize(
    "authority_alias",
    (
        "promotion_authority",
        "runtime_candidate_eligible",
        "auto_apply_eligible",
        "provider_route_change_allowed",
    ),
)
def test_current_source_bridge_and_label_reject_resealed_positive_authority_alias(
    bound_source_fixture,
    monkeypatch,
    authority_alias,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)

    forged_source = deepcopy(lineage["source_bundle"])
    forged_source[authority_alias] = True
    forged_source["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in forged_source.items()
            if key != "source_bundle_content_sha256"
        }
    )
    with pytest.raises(ValueError, match="source_only_authority_invalid"):
        quality._validate_micro_reversion_source_bundle_artifact(forged_source)

    forged_bridge = deepcopy(lineage["bridge"])
    forged_bridge[authority_alias] = True
    forged_bridge["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in forged_bridge.items()
            if key != "report_content_sha256"
        }
    )
    with pytest.raises(ValueError, match="outcome_source_bridge_authority_invalid"):
        quality._micro_reversion_outcome_source_commitment(
            forged_bridge,
            expected_target_date=lineage["target_date"],
        )

    labels = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=lineage["bridge"],
        materialized_report=lineage["materialized"],
    )["labels"]
    forged_label = deepcopy(labels[0])
    forged_label[authority_alias] = True
    forged_label["label_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in forged_label.items()
            if key != "label_content_sha256"
        }
    )
    with pytest.raises(
        ValueError,
        match="action_neutral_label_source_only_authority_invalid",
    ):
        quality._validate_micro_reversion_action_neutral_label(forged_label)


@pytest.mark.parametrize(
    "authority_alias",
    (
        "promotion_authority",
        "runtime_candidate_eligible",
        "auto_apply_eligible",
        "provider_route_change_allowed",
    ),
)
def test_r2_r3_exact_authority_rejects_positive_alias(authority_alias):
    forged = {**cycle.OFFLINE_AUTHORITY, authority_alias: True}

    with pytest.raises(ValueError, match="authority_alias_invalid"):
        cycle._validate_exact_offline_authority(forged, label="r3_manifest")


@pytest.mark.parametrize(
    "authority_alias",
    (
        "promotion_authority",
        "runtime_candidate_eligible",
        "auto_apply_eligible",
        "provider_route_change_allowed",
    ),
)
def test_cycle_execution_consumer_rejects_positive_authority_alias(authority_alias):
    forged = {
        **cycle.SOURCE_ONLY_AUTHORITY_CONTRACT,
        "selection_authority": False,
        "decision_authority": "offline_replay_and_attribution_only",
        authority_alias: True,
    }

    assert cycle._current_ablation_execution_authority_findings(forged) == [
        f"current_authority_alias_invalid:{authority_alias}"
    ]


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


def test_rejected_provider_receipt_keeps_raw_bytes_in_checkpoint_custody(
    tmp_path,
    monkeypatch,
    bound_source_fixture,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=lineage["bridge"],
        materialized_report=lineage["materialized"],
    )
    provider_floor = {"floor_content_sha256": "f" * 64}
    monkeypatch.setattr(
        quality,
        "validate_micro_reversion_provider_ablation_floor_artifact",
        lambda *_args, **_kwargs: provider_floor,
    )
    capacity_path = tmp_path / "capacity.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    healthy_capacity = _healthy_capacity_gate(
        target_date=lineage["target_date"],
        capacity_path=capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: deepcopy(healthy_capacity),
    )
    calls: list[str] = []
    expected_raw = json.dumps(
        _valid_micro_reversion_entry_response(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    def tampered_receipt_runner(attempt_request):
        calls.append(str(attempt_request["paired_replay_id"]))
        envelope = _tamper_evident_openai_runner(attempt_request)
        assert (
            base64.b64decode(
                envelope["provider_attempt_receipt"]["provider_output_bytes_b64"]
            )
            == expected_raw
        )
        envelope["provider_attempt_receipt"]["attempt_receipt_content_sha256"] = (
            "0" * 64
        )
        return envelope

    checkpoint_records: list[dict] = []
    with pytest.raises(
        quality._MicroReversionProviderReceiptRejected,
        match="provider_receipt_rejected_after_custody",
    ):
        quality.run_micro_reversion_materialized_requests(
            materialized_report=lineage["materialized"],
            outcome_label_artifact=outcome_artifact,
            source_bridge_report=lineage["bridge"],
            execute_candidate=True,
            candidate_runner=tampered_receipt_runner,
            max_new_requests=3,
            checkpoint_callback=checkpoint_records.append,
            provider_ablation_sample_floor_artifact=provider_floor,
            storage_capacity_status_path=capacity_path,
        )

    assert len(calls) == 1
    assert len(checkpoint_records) == 1
    replay_result = checkpoint_records[0]["result"]["replay_result"]
    assert replay_result["status"] == "provider_receipt_rejected"
    assert replay_result["candidate_response"] == {}
    attempt = replay_result["candidate_attempts"][0]
    assert attempt["status"] == "provider_receipt_rejected"
    assert attempt["parsed_candidate_response"] is None
    assert (
        base64.b64decode(
            attempt["provider_attempt_receipt"]["provider_output_bytes_b64"]
        )
        == expected_raw
    )
    custody = attempt["rejected_provider_attempt_custody"]
    assert custody["validation_status"] == ("rejected_untrusted_not_evaluation_input")
    assert custody["evaluation_allowed"] is False
    assert custody["retry_allowed"] is False
    assert custody["custody_content_sha256"] == quality._sha256(
        {
            key: value
            for key, value in custody.items()
            if key != "custody_content_sha256"
        }
    )
    assert base64.b64decode(custody["provider_output_bytes_b64"]) == expected_raw
    request = lineage["materialized"]["requests"][0]
    checkpoint_result = checkpoint_records[0]["result"]
    quality._validate_current_rejected_provider_attempt_custody(
        result=checkpoint_result,
        request=request,
        expected_target_date=lineage["target_date"],
    )

    tampered_result = deepcopy(checkpoint_result)
    tampered_replay = tampered_result["replay_result"]
    tampered_attempt = tampered_replay["candidate_attempts"][0]
    tampered_custody = tampered_attempt["rejected_provider_attempt_custody"]
    tampered_custody["observed_provider_output_size_bytes"] += 1
    tampered_custody["custody_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered_custody.items()
            if key != "custody_content_sha256"
        }
    )
    tampered_attempt["attempt_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered_attempt.items()
            if key != "attempt_content_sha256"
        }
    )
    tampered_replay["candidate_attempt_chain_head_sha256"] = tampered_attempt[
        "attempt_content_sha256"
    ]
    tampered_result["result_id"] = (
        "micro-result-"
        + quality._sha256(quality._micro_reversion_result_content(tampered_result))[:24]
    )
    with pytest.raises(
        ValueError,
        match="micro_reversion_rejected_provider_custody_raw_bytes_invalid",
    ):
        quality._validate_current_rejected_provider_attempt_custody(
            result=tampered_result,
            request=request,
            expected_target_date=lineage["target_date"],
        )


def test_current_empty_materialization_requires_canonical_four_companion_rebuild(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    decision_ts = str(bound_source_fixture["trace"]["decision_ts"])
    past_market_rows = [
        row
        for row in bound_source_fixture["market_rows"]
        if str(row.get("exchange_timestamp") or "") <= decision_ts
    ]
    past_depth_rows = [
        row
        for row in bound_source_fixture["depth_rows"]
        if str(row.get("exchange_timestamp") or "") <= decision_ts
    ]
    empty_bridge = _build_external_bridge(
        bound_source_fixture,
        market_rows=past_market_rows,
        depth_rows=past_depth_rows,
        entry_pipeline_rows=[],
    )
    empty_bridge.update(quality.ABLATION_SOURCE_ONLY_AUTHORITY)
    empty_bridge["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in empty_bridge.items()
            if key != "report_content_sha256"
        }
    )
    empty_source = _build_bound_source_bundle(
        bound_source_fixture,
        empty_bridge,
        market_rows=past_market_rows,
        depth_rows=past_depth_rows,
        entry_pipeline_rows=[],
    )
    empty_source.update(quality.ABLATION_SOURCE_ONLY_AUTHORITY)
    empty_source["selection_authority"] = False
    empty_source["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in empty_source.items()
            if key != "source_bundle_content_sha256"
        }
    )
    empty_materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=deepcopy(lineage["prepared"]["prepared_requests"]),
        bridge_source_bundle=deepcopy(empty_source),
        outcome_source_bridge_report=empty_bridge,
    )
    body = {
        key: value
        for key, value in empty_materialized.items()
        if key != "report_content_sha256"
    }
    body.update(
        {
            "prepared_request_artifact_path": "prepared.json",
            "prepared_request_artifact_sha256": quality._sha256(lineage["prepared"]),
            "source_bundle_path": "source_bundle.json",
        }
    )
    empty_materialized = {
        **body,
        "report_content_sha256": quality._sha256(body),
    }

    assert empty_source["eligible_row_count"] == 0
    assert empty_materialized["request_count"] == 0
    quality.validate_current_materialized_source_lineage(
        materialized_report=empty_materialized,
        source_bundle_report=empty_source,
        prepared_artifact=lineage["prepared"],
        source_bridge_report=empty_bridge,
        paired_report=lineage["paired"],
    )

    tampered_source = deepcopy(empty_source)
    tampered_source["exclusions"][0]["reason"] = "forged_empty_reason"
    tampered_source["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered_source.items()
            if key != "source_bundle_content_sha256"
        }
    )
    with pytest.raises(ValueError, match="micro_reversion_lineage"):
        quality.validate_current_materialized_source_lineage(
            materialized_report=empty_materialized,
            source_bundle_report=tampered_source,
            prepared_artifact=lineage["prepared"],
            source_bridge_report=empty_bridge,
            paired_report=lineage["paired"],
        )


def test_current_persisted_lineage_rebuilds_from_paired_and_raw_source(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)

    quality.validate_current_materialized_source_lineage(
        materialized_report=lineage["materialized"],
        source_bundle_report=lineage["source_bundle"],
        prepared_artifact=lineage["prepared"],
        source_bridge_report=lineage["bridge"],
        paired_report=lineage["paired"],
    )


def test_current_lineage_rejects_paired_parent_omission(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    extra = deepcopy(lineage["paired"]["requests"][0])
    extra["decision_trace_id"] = "trace-materialize-omitted"
    extra["paired_replay_id"] = "pair-materialize-omitted"
    extra["outcome_join_key"] = "trace-materialize-omitted:v1"
    lineage["paired"]["requests"].append(extra)

    with pytest.raises(
        ValueError, match="micro_reversion_lineage_prepared_artifact_invalid"
    ):
        quality.validate_current_materialized_source_lineage(
            materialized_report=lineage["materialized"],
            source_bundle_report=lineage["source_bundle"],
            prepared_artifact=lineage["prepared"],
            source_bridge_report=lineage["bridge"],
            paired_report=lineage["paired"],
        )


def test_current_materialization_rejects_captured_action_source_reseal(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    source_bundle = deepcopy(lineage["source_bundle"])
    source_bundle["rows"][0]["source_trace"]["action"] = "HOLD"
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="micro_reversion_current_control_captured_source_mismatch"
    ):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=deepcopy(lineage["prepared"]["prepared_requests"]),
            bridge_source_bundle=source_bundle,
            outcome_source_bridge_report=lineage["bridge"],
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


def test_current_lineage_rejects_eligible_row_replaced_by_fabricated_exclusion(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    source_bundle = deepcopy(lineage["source_bundle"])
    removed = source_bundle["rows"].pop()
    source_bundle["exclusions"] = [
        {
            "decision_trace_id": removed["decision_trace_id"],
            "paired_replay_id": lineage["prepared"]["prepared_requests"][0][
                "paired_replay_id"
            ],
            "stage": lineage["prepared"]["prepared_requests"][0]["stage"],
            "effective_venue": lineage["prepared"]["prepared_requests"][0][
                "effective_venue"
            ],
            "session_bucket": lineage["prepared"]["prepared_requests"][0][
                "session_bucket"
            ],
            "reason": "fabricated_source_failure",
            "source_quality_blockers": [],
        }
    ]
    source_bundle["status"] = "no_micro_reversion_eligible_rows"
    source_bundle["row_count"] = 0
    source_bundle["eligible_row_count"] = 0
    source_bundle["excluded_row_count"] = 1
    for pool_name in source_bundle["source_row_pool"]:
        source_bundle["source_row_pool"][pool_name] = {}
        source_bundle["source_row_pool_counts"][pool_name] = 0
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="micro_reversion_current_source_eligibility_census_invalid"
    ):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=lineage["prepared"]["prepared_requests"],
            bridge_source_bundle=source_bundle,
            outcome_source_bridge_report=lineage["bridge"],
        )


def test_current_lineage_accepts_independently_verified_ask_source_exclusion(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    bridge_report = deepcopy(lineage["bridge"])
    bridge_row = bridge_report["rows"][0]
    bridge_row["ask_depletion_sidecar"] = None
    bridge_row["ask_depletion_sidecar_status"] = (
        "ask_depletion_sidecar_source_quality_invalid"
    )
    bridge_report["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in bridge_report.items()
            if key != "report_content_sha256"
        }
    )

    source_bundle = deepcopy(lineage["source_bundle"])
    removed = source_bundle["rows"].pop()
    source_bundle["exclusions"] = [
        {
            "decision_trace_id": removed["decision_trace_id"],
            "paired_replay_id": lineage["prepared"]["prepared_requests"][0][
                "paired_replay_id"
            ],
            "stage": lineage["prepared"]["prepared_requests"][0]["stage"],
            "effective_venue": lineage["prepared"]["prepared_requests"][0][
                "effective_venue"
            ],
            "session_bucket": lineage["prepared"]["prepared_requests"][0][
                "session_bucket"
            ],
            "reason": "ask_depletion_sidecar_source_quality_invalid",
            "source_quality_blockers": [],
        }
    ]
    source_bundle["status"] = "no_micro_reversion_eligible_rows"
    source_bundle["row_count"] = 0
    source_bundle["eligible_row_count"] = 0
    source_bundle["excluded_row_count"] = 1
    for pool_name in source_bundle["source_row_pool"]:
        source_bundle["source_row_pool"][pool_name] = {}
        source_bundle["source_row_pool_counts"][pool_name] = 0
    source_bundle["outcome_source_commitment"] = (
        quality._micro_reversion_outcome_source_commitment(
            bridge_report,
            expected_target_date=lineage["target_date"],
        )
    )
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )

    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=lineage["prepared"]["prepared_requests"],
        bridge_source_bundle=source_bundle,
        outcome_source_bridge_report=bridge_report,
    )

    assert materialized["request_count"] == 0
    assert materialized["materialization_count"] == 0
    assert materialized["status"] == "no_micro_reversion_eligible_requests"


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


@pytest.mark.parametrize(
    "invalid_ancestor",
    ("paired", "prepared", "source_bundle"),
)
def test_current_execute_cli_rejects_invalid_lineage_before_provider_budget_or_call(
    bound_source_fixture,
    monkeypatch,
    tmp_path,
    invalid_ancestor,
):
    from src.engine.scalping.micro_reversion import provider_budget

    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    if invalid_ancestor == "paired":
        lineage["paired"]["provider_authority"] = True
    elif invalid_ancestor == "prepared":
        lineage["prepared"]["provider_effect"] = True
        lineage["prepared"]["artifact_content_sha256"] = quality._sha256(
            {
                key: value
                for key, value in lineage["prepared"].items()
                if key != "artifact_content_sha256"
            }
        )
    else:
        lineage["source_bundle"]["provider_effect"] = True
        lineage["source_bundle"]["source_bundle_content_sha256"] = quality._sha256(
            {
                key: value
                for key, value in lineage["source_bundle"].items()
                if key != "source_bundle_content_sha256"
            }
        )

    artifact_paths = {}
    for name in ("materialized", "prepared", "source_bundle", "bridge", "paired"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(lineage[name]), encoding="utf-8")
        artifact_paths[name] = path

    preflight_events: list[str] = []

    def forbidden_preflight(name):
        def fail(*_args, **_kwargs):
            preflight_events.append(name)
            raise AssertionError(f"{name} must not run before lineage validation")

        return fail

    monkeypatch.setattr(
        provider_budget,
        "load_reviewed_pricing_artifact",
        forbidden_preflight("pricing_load"),
    )
    monkeypatch.setattr(
        provider_budget,
        "ProviderBudgetLedger",
        forbidden_preflight("provider_budget_ledger"),
    )
    monkeypatch.setattr(
        quality,
        "run_micro_reversion_materialized_requests",
        forbidden_preflight("provider_execution"),
    )

    with pytest.raises(ValueError, match="micro_reversion_"):
        quality.main(
            [
                "--date",
                lineage["target_date"],
                "--mode",
                "micro_reversion_execute",
                "--micro-reversion-materialized-requests",
                str(artifact_paths["materialized"]),
                "--micro-reversion-prepared-requests",
                str(artifact_paths["prepared"]),
                "--micro-reversion-source-bundle",
                str(artifact_paths["source_bundle"]),
                "--micro-reversion-bridge-report",
                str(artifact_paths["bridge"]),
                "--micro-reversion-paired-report",
                str(artifact_paths["paired"]),
                "--execute-candidate",
                "--write",
                "--candidate-max-new-requests",
                "3",
                "--micro-reversion-provider-pricing",
                str(tmp_path / "pricing-must-not-load.json"),
                "--micro-reversion-provider-daily-attempt-cap",
                "3",
                "--micro-reversion-provider-daily-usd-cap",
                "1",
                "--micro-reversion-provider-ablation-floor",
                str(tmp_path / "floor-must-not-load.json"),
                "--micro-reversion-storage-capacity-status",
                str(tmp_path / "capacity-must-not-load.json"),
            ]
        )

    assert preflight_events == []


@pytest.mark.parametrize("floor_mode", ("missing", "tampered", "future"))
def test_current_execute_cli_rejects_floor_before_provider_import_or_call(
    bound_source_fixture,
    monkeypatch,
    tmp_path,
    floor_mode,
):
    from src.engine.scalping.micro_reversion import provider_budget

    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    artifact_paths = {}
    for name in ("materialized", "prepared", "source_bundle", "bridge", "paired"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(lineage[name]), encoding="utf-8")
        artifact_paths[name] = path
    floor_target_date = (
        (quality.datetime.now(quality.KST).date() + timedelta(days=1)).isoformat()
        if floor_mode == "future"
        else lineage["target_date"]
    )
    floor_path = tmp_path / (
        "micro_reversion_provider_ablation_sample_floor_" f"{floor_target_date}.json"
    )
    if floor_mode == "tampered":
        floor_path.write_text(
            json.dumps({"floor_content_sha256": "0" * 64}),
            encoding="utf-8",
        )
    capacity_path = tmp_path / "capacity.json"
    outcome_path = tmp_path / "outcome.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_ablation_floor_path",
        lambda _target_date: floor_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_action_neutral_label_path",
        lambda _target_date: outcome_path,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date=lineage["target_date"],
            capacity_path=capacity_path,
        ),
    )
    provider_events = []

    def forbidden(name):
        def fail(*_args, **_kwargs):
            provider_events.append(name)
            raise AssertionError(f"{name} must remain blocked")

        return fail

    monkeypatch.setattr(
        provider_budget,
        "load_reviewed_pricing_artifact",
        forbidden("pricing"),
    )
    monkeypatch.setattr(
        quality,
        "run_micro_reversion_materialized_requests",
        forbidden("execution"),
    )
    expected_error = (
        RuntimeError
        if floor_mode == "future"
        else (FileNotFoundError if floor_mode == "missing" else ValueError)
    )
    expected_match = (
        "micro_reversion_provider_ablation_floor_time_binding_invalid"
        if floor_mode == "future"
        else None
    )
    with pytest.raises(expected_error, match=expected_match):
        quality.main(
            [
                "--date",
                lineage["target_date"],
                "--mode",
                "micro_reversion_execute",
                "--micro-reversion-materialized-requests",
                str(artifact_paths["materialized"]),
                "--micro-reversion-prepared-requests",
                str(artifact_paths["prepared"]),
                "--micro-reversion-source-bundle",
                str(artifact_paths["source_bundle"]),
                "--micro-reversion-bridge-report",
                str(artifact_paths["bridge"]),
                "--micro-reversion-paired-report",
                str(artifact_paths["paired"]),
                "--execute-candidate",
                "--write",
                "--candidate-max-new-requests",
                "3",
                "--micro-reversion-provider-pricing",
                str(tmp_path / "pricing-must-not-load.json"),
                "--micro-reversion-provider-daily-attempt-cap",
                "3",
                "--micro-reversion-provider-daily-usd-cap",
                "1",
                "--micro-reversion-provider-ablation-floor",
                str(floor_path),
                "--micro-reversion-storage-capacity-status",
                str(capacity_path),
            ]
        )

    assert provider_events == []


@pytest.mark.parametrize(
    ("custody_status", "custody_failure", "returned_finding"),
    (
        (
            "orphan_reservation",
            "prior_provider_ledger_orphan_reservation:2026-08-15:request-1:1",
            True,
        ),
        (
            "schema_rejected",
            "historical_backfill_checkpoint_terminal_attempt_not_resumable",
            False,
        ),
        (
            "provider_receipt_rejected",
            "micro_reversion_rejected_provider_receipt_manual_resolution_required",
            False,
        ),
        (
            "provider_failed",
            "historical_backfill_checkpoint_terminal_attempt_unbound",
            False,
        ),
    ),
)
def test_current_execute_cli_blocks_cross_day_or_terminal_custody_before_new_call(
    bound_source_fixture,
    monkeypatch,
    tmp_path,
    custody_status,
    custody_failure,
    returned_finding,
):
    from src.engine.scalping.micro_reversion import provider_budget

    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    artifact_paths = {}
    for name in ("materialized", "prepared", "source_bundle", "bridge", "paired"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(lineage[name]), encoding="utf-8")
        artifact_paths[name] = path
    floor_path = tmp_path / (
        "micro_reversion_provider_ablation_sample_floor_"
        f"{lineage['target_date']}.json"
    )
    floor_path.write_text(
        json.dumps({"floor_content_sha256": "f" * 64}),
        encoding="utf-8",
    )
    pricing_path = tmp_path / "provider-pricing.json"
    capacity_path = tmp_path / "capacity.json"
    outcome_path = tmp_path / "outcome.json"
    output_path = tmp_path / "execution.json"
    budget_ledger_path = tmp_path / "provider-budget.jsonl"
    budget_summary_path = tmp_path / "provider-budget.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_ablation_floor_path",
        lambda _target_date: floor_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_pricing_path",
        lambda: pricing_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _target_date: output_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_action_neutral_label_path",
        lambda _target_date: outcome_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_budget_ledger_path",
        lambda _execution_date: budget_ledger_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_budget_summary_path",
        lambda _execution_date: budget_summary_path,
    )
    monkeypatch.setattr(
        quality,
        "validate_micro_reversion_provider_ablation_floor_artifact",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date=lineage["target_date"],
            capacity_path=capacity_path,
        ),
    )
    checkpoint_path = quality.micro_reversion_execution_checkpoint_path(
        lineage["target_date"]
    )
    if custody_status == "provider_failed":
        # Simulate a crash after immutable record publication but before the
        # checkpoint manifest head was committed. Direct preflight must retain
        # the existing repair path before applying the terminal no-call gate.
        crash_result = {"result_id": "micro-result-crash-before-manifest"}
        checkpoint_record = quality._micro_reversion_checkpoint_record(
            materialized_report_content_sha256=(
                quality._micro_reversion_materialized_request_census_sha256(
                    lineage["materialized"]
                )
            ),
            sequence=1,
            previous_record_sha256=None,
            result=crash_result,
        )
        record_dir = quality._micro_reversion_checkpoint_record_dir(checkpoint_path)
        record_dir.mkdir()
        record_hash = checkpoint_record["checkpoint_record_content_sha256"]
        (record_dir / f"00000001-{record_hash}.json").write_text(
            json.dumps(checkpoint_record),
            encoding="utf-8",
        )
    custody_gate_calls = []

    def custody_gate(**kwargs):
        custody_gate_calls.append((custody_status, kwargs))
        if custody_status == "provider_failed":
            assert kwargs["checkpoint_artifact"]["schema"] == (
                quality.MICRO_REVERSION_CHECKPOINT_RECONSTRUCTED_SCHEMA
            )
            assert checkpoint_path.exists()
        if returned_finding:
            return [custody_failure]
        raise ValueError(custody_failure)

    monkeypatch.setattr(
        quality,
        "_micro_reversion_prior_physical_ledger_findings",
        custody_gate,
    )
    provider_events = []

    def forbidden(name):
        def fail(*_args, **_kwargs):
            provider_events.append(name)
            raise AssertionError(f"{name} must remain blocked")

        return fail

    monkeypatch.setattr(
        provider_budget,
        "load_reviewed_pricing_artifact",
        forbidden("new_execution_pricing"),
    )
    monkeypatch.setattr(
        provider_budget,
        "ProviderBudgetLedger",
        forbidden("new_budget_ledger"),
    )
    monkeypatch.setattr(
        quality,
        "run_micro_reversion_materialized_requests",
        forbidden("provider_execution_callback"),
    )
    monkeypatch.setattr(
        quality,
        "_offline_openai_api_keys",
        forbidden("provider_client_credentials"),
    )

    with pytest.raises(ValueError, match=custody_failure):
        quality.main(
            [
                "--date",
                lineage["target_date"],
                "--mode",
                "micro_reversion_execute",
                "--micro-reversion-materialized-requests",
                str(artifact_paths["materialized"]),
                "--micro-reversion-prepared-requests",
                str(artifact_paths["prepared"]),
                "--micro-reversion-source-bundle",
                str(artifact_paths["source_bundle"]),
                "--micro-reversion-bridge-report",
                str(artifact_paths["bridge"]),
                "--micro-reversion-paired-report",
                str(artifact_paths["paired"]),
                "--execute-candidate",
                "--write",
                "--candidate-max-new-requests",
                "3",
                "--micro-reversion-provider-pricing",
                str(pricing_path),
                "--micro-reversion-provider-daily-attempt-cap",
                "3",
                "--micro-reversion-provider-daily-usd-cap",
                "1",
                "--micro-reversion-provider-ablation-floor",
                str(floor_path),
                "--micro-reversion-storage-capacity-status",
                str(capacity_path),
            ]
        )

    assert len(custody_gate_calls) == 1
    assert provider_events == []
    assert not budget_ledger_path.exists()
    assert not budget_summary_path.exists()
    assert not output_path.exists()
    if custody_status == "provider_failed":
        assert checkpoint_path.exists()


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


def test_current_provider_capacity_is_rechecked_and_bound_per_schema_attempt(
    bound_source_fixture,
    monkeypatch,
    tmp_path,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=lineage["bridge"],
        materialized_report=lineage["materialized"],
    )
    floor = {"floor_content_sha256": "f" * 64}
    monkeypatch.setattr(
        quality,
        "validate_micro_reversion_provider_ablation_floor_artifact",
        lambda *_args, **_kwargs: floor,
    )
    capacity_path = tmp_path / "capacity.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    capacity_checks = []

    def capacity_gate(**_kwargs):
        capacity_checks.append(len(capacity_checks) + 1)
        return _healthy_capacity_gate(
            target_date=lineage["target_date"],
            capacity_path=capacity_path,
        )

    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        capacity_gate,
    )
    provider_attempts = []

    def schema_retry_runner(request):
        provider_attempts.append(
            (
                request["paired_replay_id"],
                request["offline_provider_attempt_number"],
            )
        )
        if request["offline_provider_attempt_number"] == 1:
            return _tamper_evident_openai_runner(
                request,
                response={"action": "WAIT"},
            )
        return _tamper_evident_openai_runner(
            request,
            response=_valid_micro_reversion_entry_response(),
        )

    checkpoint_records = []
    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=lineage["materialized"],
        outcome_label_artifact=outcome_artifact,
        source_bridge_report=lineage["bridge"],
        execute_candidate=True,
        candidate_runner=schema_retry_runner,
        max_new_requests=3,
        checkpoint_callback=checkpoint_records.append,
        provider_ablation_sample_floor_artifact=floor,
        storage_capacity_status_path=capacity_path,
    )

    assert len(provider_attempts) == 6
    assert capacity_checks == list(range(1, 8))
    assert report["provider_call_capacity_receipt_count"] == 6
    assert [
        (
            row["paired_replay_id"],
            row["offline_provider_attempt_number"],
        )
        for row in report["provider_call_capacity_receipts"]
    ] == provider_attempts
    assert len(checkpoint_records) == 3
    for result in report["results"]:
        assert result["provider_attempt_capacity_receipt_count"] == 2
        assert [
            row["offline_provider_attempt_number"]
            for row in result["provider_attempt_capacity_receipts"]
        ] == [1, 2]
        assert (
            result["provider_capacity_gate_content_sha256"]
            == result["provider_attempt_capacity_receipts"][-1][
                "provider_capacity_gate_content_sha256"
            ]
        )
    labels_by_id = {
        str(label["label_id"]): [label] for label in outcome_artifact["labels"]
    }
    with pytest.raises(
        ValueError,
        match="micro_reversion_existing_provider_floor_mismatch",
    ):
        quality._micro_reversion_reusable_results(
            existing_artifact=report,
            materialized_report=lineage["materialized"],
            requests=lineage["materialized"]["requests"],
            labels_by_id=labels_by_id,
            provider_ablation_sample_floor_content_sha256="e" * 64,
        )


@pytest.mark.parametrize(
    (
        "blocked_capacity_check",
        "expected_provider_attempts",
        "expected_checkpoint_count",
    ),
    ((2, [], 0), (3, [1], 1)),
)
def test_current_provider_capacity_flip_blocks_schema_attempt(
    bound_source_fixture,
    monkeypatch,
    tmp_path,
    blocked_capacity_check,
    expected_provider_attempts,
    expected_checkpoint_count,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=lineage["bridge"],
        materialized_report=lineage["materialized"],
    )
    floor = {"floor_content_sha256": "f" * 64}
    monkeypatch.setattr(
        quality,
        "validate_micro_reversion_provider_ablation_floor_artifact",
        lambda *_args, **_kwargs: floor,
    )
    capacity_path = tmp_path / "capacity.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    capacity_checks = []

    def capacity_gate(**_kwargs):
        capacity_checks.append(len(capacity_checks) + 1)
        if len(capacity_checks) == blocked_capacity_check:
            raise RuntimeError("injected_capacity_flip")
        return _healthy_capacity_gate(
            target_date=lineage["target_date"],
            capacity_path=capacity_path,
        )

    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        capacity_gate,
    )
    provider_attempts = []

    def invalid_first_attempt(request):
        provider_attempts.append(request["offline_provider_attempt_number"])
        return _tamper_evident_openai_runner(
            request,
            response={"action": "WAIT"},
        )

    checkpoint_records = []
    with pytest.raises(
        quality._MicroReversionProviderCapacityBlocked,
        match="provider_attempt_capacity_blocked",
    ):
        quality.run_micro_reversion_materialized_requests(
            materialized_report=lineage["materialized"],
            outcome_label_artifact=outcome_artifact,
            source_bridge_report=lineage["bridge"],
            execute_candidate=True,
            candidate_runner=invalid_first_attempt,
            max_new_requests=3,
            checkpoint_callback=checkpoint_records.append,
            provider_ablation_sample_floor_artifact=floor,
            storage_capacity_status_path=capacity_path,
        )

    assert capacity_checks == list(range(1, blocked_capacity_check + 1))
    assert provider_attempts == expected_provider_attempts
    assert len(checkpoint_records) == expected_checkpoint_count
    if expected_checkpoint_count:
        preserved = checkpoint_records[0]["result"]
        replay_result = preserved["replay_result"]
        assert replay_result["status"] == "provider_capacity_blocked_before_retry"
        assert len(replay_result["candidate_attempts"]) == 1
        attempt = replay_result["candidate_attempts"][0]
        assert attempt["provider_attempt_receipt"]["provider_output_bytes_b64"]
        assert preserved["provider_attempt_capacity_receipt_count"] == 1
        assert len(preserved["provider_attempt_capacity_receipts"]) == 1


def test_capacity_blocked_retry_resumes_at_next_attempt_and_commits_parent(
    bound_source_fixture,
    monkeypatch,
    tmp_path,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=lineage["bridge"],
        materialized_report=lineage["materialized"],
    )
    floor = {"floor_content_sha256": "f" * 64}
    monkeypatch.setattr(
        quality,
        "validate_micro_reversion_provider_ablation_floor_artifact",
        lambda *_args, **_kwargs: floor,
    )
    capacity_path = tmp_path / "capacity.json"
    checkpoint_path = tmp_path / "capacity-resume.checkpoint.json"
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    capacity_checks = []

    def flip_before_retry(**_kwargs):
        capacity_checks.append(len(capacity_checks) + 1)
        if len(capacity_checks) == 3:
            raise RuntimeError("injected_capacity_flip")
        return _healthy_capacity_gate(
            target_date=lineage["target_date"],
            capacity_path=capacity_path,
        )

    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        flip_before_retry,
    )
    reserved_attempts = set()
    first_request_id = lineage["materialized"]["requests"][0]["paired_replay_id"]

    def first_runner(request):
        identity = (
            request["paired_replay_id"],
            request["offline_provider_attempt_number"],
        )
        assert identity not in reserved_attempts
        reserved_attempts.add(identity)
        return _tamper_evident_openai_runner(
            request,
            response={"action": "WAIT"},
        )

    with pytest.raises(quality._MicroReversionProviderCapacityBlocked):
        quality.run_micro_reversion_materialized_requests(
            materialized_report=lineage["materialized"],
            outcome_label_artifact=outcome_artifact,
            source_bridge_report=lineage["bridge"],
            execute_candidate=True,
            candidate_runner=first_runner,
            max_new_requests=3,
            checkpoint_callback=lambda record: (
                quality._write_micro_reversion_checkpoint_record(
                    checkpoint_path,
                    record,
                )
            ),
            provider_ablation_sample_floor_artifact=floor,
            storage_capacity_status_path=capacity_path,
        )
    assert reserved_attempts == {(first_request_id, 1)}
    partial_checkpoint = quality._load_micro_reversion_checkpoint(checkpoint_path)
    assert partial_checkpoint["checkpoint_record_count"] == 1

    tampered_checkpoint = deepcopy(partial_checkpoint)
    tampered_result = tampered_checkpoint["results"][0]
    tampered_replay = tampered_result["replay_result"]
    tampered_attempt = tampered_replay["candidate_attempts"][0]
    tampered_receipt = tampered_attempt["provider_attempt_receipt"]
    forged_raw = b"{}"
    forged_raw_sha256 = hashlib.sha256(forged_raw).hexdigest()
    tampered_receipt.update(
        {
            "provider_output_bytes_b64": base64.b64encode(forged_raw).decode("ascii"),
            "provider_output_size_bytes": len(forged_raw),
            "provider_output_bytes_sha256": forged_raw_sha256,
        }
    )
    tampered_receipt["attempt_receipt_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered_receipt.items()
            if key != "attempt_receipt_content_sha256"
        }
    )
    tampered_attempt["provider_provenance"]["response_sha256"] = forged_raw_sha256
    tampered_attempt["attempt_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered_attempt.items()
            if key != "attempt_content_sha256"
        }
    )
    tampered_replay["candidate_attempt_chain_head_sha256"] = tampered_attempt[
        "attempt_content_sha256"
    ]
    tampered_result["result_id"] = (
        "micro-result-"
        + quality._sha256(quality._micro_reversion_result_content(tampered_result))[:24]
    )
    tampered_checkpoint["checkpoint_reconstructed_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in tampered_checkpoint.items()
            if key != "checkpoint_reconstructed_content_sha256"
        }
    )
    labels_by_id = {
        str(label["label_id"]): [label] for label in outcome_artifact["labels"]
    }
    with pytest.raises(ValueError, match="openai_attempt_receipt_parse_mismatch"):
        quality._micro_reversion_partial_retry_states(
            existing_artifact=tampered_checkpoint,
            materialized_report=lineage["materialized"],
            requests=lineage["materialized"]["requests"],
            labels_by_id=labels_by_id,
            provider_ablation_sample_floor_content_sha256="f" * 64,
        )

    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date=lineage["target_date"],
            capacity_path=capacity_path,
        ),
    )
    resumed_attempts = []

    def resumed_runner(request):
        identity = (
            request["paired_replay_id"],
            request["offline_provider_attempt_number"],
        )
        assert identity not in reserved_attempts
        reserved_attempts.add(identity)
        resumed_attempts.append(identity)
        return _tamper_evident_openai_runner(
            request,
            response=_valid_micro_reversion_entry_response(),
        )

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=lineage["materialized"],
        outcome_label_artifact=outcome_artifact,
        source_bridge_report=lineage["bridge"],
        execute_candidate=True,
        candidate_runner=resumed_runner,
        existing_result_artifact=partial_checkpoint,
        max_new_requests=3,
        checkpoint_callback=lambda record: (
            quality._write_micro_reversion_checkpoint_record(
                checkpoint_path,
                record,
            )
        ),
        provider_ablation_sample_floor_artifact=floor,
        storage_capacity_status_path=capacity_path,
    )

    assert resumed_attempts[0] == (first_request_id, 2)
    assert all(identity != (first_request_id, 1) for identity in resumed_attempts)
    assert report["status"] == "offline_three_arm_execution_complete"
    assert report["result_count"] == 3
    assert report["provider_call_capacity_reused_receipt_count"] == 1
    assert report["provider_call_capacity_new_receipt_count"] == 3
    first_result = next(
        row for row in report["results"] if row["paired_replay_id"] == first_request_id
    )
    assert [
        attempt["attempt_number"]
        for attempt in first_result["replay_result"]["candidate_attempts"]
    ] == [1, 2]
    assert first_result["provider_attempt_capacity_receipt_count"] == 2
    rebuilt_checkpoint = quality._load_micro_reversion_checkpoint(checkpoint_path)
    assert rebuilt_checkpoint["checkpoint_record_count"] == 4
    quality.validate_current_micro_reversion_checkpoint_companion(
        report=report,
        checkpoint_artifact=rebuilt_checkpoint,
        materialized_report=lineage["materialized"],
        outcome_labels=outcome_artifact["labels"],
    )


def test_current_paired_preserves_full_sample_floor_exclusion_identity(
    bound_source_fixture,
    monkeypatch,
):
    target_date = "2026-08-14"
    monkeypatch.setattr(quality, "CURRENT_DESIGN_ACTIVATION_DATE", target_date)
    accepted = deepcopy(bound_source_fixture["prepared"][0])
    excluded = deepcopy(accepted)
    excluded.update(
        {
            "decision_trace_id": "trace-sample-floor-excluded",
            "paired_replay_id": "pair-sample-floor-excluded",
            "outcome_join_key": "trace-sample-floor-excluded:v1",
            "sample_floor": {"pass": False, "reason": "thin_parent"},
        }
    )
    paired = quality.build_paired_replay_report(
        target_date=target_date,
        requests=[accepted],
        results=[],
        labels=[],
        prepared_requests=[accepted, excluded],
    )
    quality._attach_paired_preparation_metadata(
        paired,
        prepared_requests=[accepted, excluded],
        accepted_requests=[accepted],
        outcome_price_source="test",
        outcome_price_source_requested="test",
        price_source_provenance=[],
    )

    prepared, exclusions = (
        quality.micro_reversion_prepared_request_census_from_paired_report(
            paired_report=paired,
            target_date=target_date,
        )
    )

    assert prepared == [quality._paired_report_request_view(accepted)]
    assert len(exclusions) == 1
    assert exclusions[0]["decision_trace_id"] == excluded["decision_trace_id"]
    assert exclusions[0]["request"] == quality._paired_report_request_view(excluded)
    assert exclusions[0]["request_content_sha256"] == quality._sha256(
        exclusions[0]["request"]
    )
    prepared_artifact = cycle.build_prepared_request_artifact(
        target_date=target_date,
        paired_report=paired,
        source={
            "resolved_path": "test",
            "stored_sha256": "a" * 64,
            "logical_content_sha256": quality._sha256(paired),
        },
    )
    assert prepared_artifact["source_request_count"] == 2
    quality.validate_micro_reversion_prepared_artifact(
        prepared_artifact,
        expected_target_date=target_date,
        paired_report=paired,
    )


def test_current_prepared_rejects_resealed_raw_provenance_generation_drift(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    prepared = deepcopy(lineage["prepared"])
    prepared["source_paired_report"]["logical_content_sha256"] = "0" * 64
    prepared["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in prepared.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(ValueError, match="raw_provenance_binding_invalid"):
        quality.validate_micro_reversion_prepared_artifact(
            prepared,
            expected_target_date=lineage["target_date"],
            paired_report=lineage["paired"],
        )


def test_current_paired_rejects_global_trace_duplicate_and_positive_alias(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    duplicate = deepcopy(lineage["paired"]["requests"][0])
    duplicate["paired_replay_id"] = "pair-duplicate-current"
    lineage["paired"]["requests"].append(duplicate)
    lineage["paired"]["request_count"] += 1
    lineage["paired"]["prepared_request_count"] += 1
    with pytest.raises(
        ValueError, match="micro_reversion_paired_report_trace_census_invalid"
    ):
        quality.micro_reversion_prepared_request_census_from_paired_report(
            paired_report=lineage["paired"],
            target_date=lineage["target_date"],
        )

    escalated = deepcopy(
        _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)["paired"]
    )
    escalated["provider_authority"] = True
    with pytest.raises(
        ValueError, match="micro_reversion_paired_report_authority_invalid"
    ):
        quality.micro_reversion_prepared_request_census_from_paired_report(
            paired_report=escalated,
            target_date=lineage["target_date"],
        )


def test_current_prepared_rejects_resealed_positive_authority_alias(
    bound_source_fixture,
    monkeypatch,
):
    lineage = _postactivation_lineage_fixture(bound_source_fixture, monkeypatch)
    prepared = deepcopy(lineage["prepared"])
    prepared["provider_effect"] = True
    prepared["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in prepared.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="micro_reversion_prepared_artifact_authority_invalid"
    ):
        quality.validate_micro_reversion_prepared_artifact(
            prepared,
            expected_target_date=lineage["target_date"],
            paired_report=lineage["paired"],
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


def test_rolling_input_locator_does_not_eagerly_load_label_companions(
    tmp_path,
    monkeypatch,
):
    execution_root = tmp_path / "execution"
    label_root = tmp_path / "labels"
    bridge_root = tmp_path / "bridges"
    materialized_root = tmp_path / "materialized"
    source_bundle_root = tmp_path / "source_bundle"
    prepared_root = tmp_path / "prepared"
    paired_root = tmp_path / "paired"
    checkpoint_root = tmp_path / "checkpoint"
    for root in (
        execution_root,
        label_root,
        bridge_root,
        materialized_root,
        source_bundle_root,
        prepared_root,
        paired_root,
        checkpoint_root,
    ):
        root.mkdir()
    for target_date in ("2026-08-24", "2026-08-25"):
        execution = _current_execution_report(
            target_date,
            parent_id=f"locator-parent-{target_date}",
            trace_id=f"locator-trace-{target_date}",
            stock_code="000001",
        )
        (execution_root / f"execution_{target_date}.json").write_text(
            json.dumps(execution), encoding="utf-8"
        )
        companion_paths = (
            label_root / f"labels_{target_date}.json.gz",
            bridge_root / f"micro_reversion_ai_quality_bridge_{target_date}.json.gz",
            materialized_root / f"materialized_{target_date}.json.gz",
            source_bundle_root / f"source_bundle_{target_date}.json.gz",
            prepared_root / f"prepared_{target_date}.json.gz",
            paired_root / f"ai_prompt_paired_replay_{target_date}.json.gz",
        )
        for path in companion_paths:
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                json.dump({}, handle)
        (checkpoint_root / f"checkpoint_{target_date}.json").write_text(
            "{}",
            encoding="utf-8",
        )

    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda target_date: execution_root / f"execution_{target_date}.json",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_materialized_request_path",
        lambda target_date: materialized_root / f"materialized_{target_date}.json",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_source_bundle_path",
        lambda target_date: source_bundle_root / f"source_bundle_{target_date}.json",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_checkpoint_path",
        lambda target_date: checkpoint_root / f"checkpoint_{target_date}.json",
    )
    monkeypatch.setattr(quality, "PAIRED_REPORT_DIR", paired_root)
    monkeypatch.setattr(cycle, "LIFECYCLE_REPORT_ROOT", tmp_path / "lifecycle")
    monkeypatch.setattr(cycle, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(cycle, "ECONOMIC_REPORT_ROOT", tmp_path / "economic")
    monkeypatch.setattr(cycle, "BRIDGE_REPORT_ROOT", bridge_root)
    monkeypatch.setattr(
        cycle,
        "prepared_request_path",
        lambda target_date: prepared_root / f"prepared_{target_date}.json",
    )
    monkeypatch.setattr(
        cycle,
        "action_neutral_label_path",
        lambda target_date: label_root / f"labels_{target_date}.json",
    )
    original_load = cycle._load_json_auto
    loaded_paths: list[Path] = []

    def track_execution_only(path):
        candidate = Path(path)
        loaded_paths.append(candidate)
        if candidate.parent != execution_root:
            raise AssertionError(
                "companion JSON must be loaded only by the per-date consumer"
            )
        return original_load(candidate)

    monkeypatch.setattr(cycle, "_load_json_auto", track_execution_only)

    executions, lifecycles, source_pass, economic_pass, locators, diagnostics = (
        cycle._collect_rolling_inputs(
            target_date="2026-08-25",
            lookback_calendar_days=2,
        )
    )

    assert len(executions) == 2
    assert lifecycles == []
    assert source_pass == economic_pass == {}
    assert diagnostics == []
    assert loaded_paths == [
        execution_root / "execution_2026-08-24.json",
        execution_root / "execution_2026-08-25.json",
    ]
    assert set(locators) == {"2026-08-24", "2026-08-25"}
    assert all(
        Path(locator["checkpoint_artifact_path"]).parent == checkpoint_root
        for locator in locators.values()
    )
    assert all(
        locator["lazy_load_one_date_at_a_time"] is True
        and locator["outcome_label_path"]
        and all(
            str(locator[field]).endswith(".json.gz")
            for field in (
                "outcome_label_path",
                "source_bridge_path",
                "materialized_report_path",
                "source_bundle_path",
                "prepared_artifact_path",
                "paired_report_path",
            )
        )
        for locator in locators.values()
    )


def test_invalid_preactivation_execution_does_not_globally_poison_current_r3():
    invalid = _execution_report(
        "2026-08-24",
        parent_id="legacy-invalid-parent",
        trace_id="legacy-invalid-trace",
        stock_code="000001",
    )
    invalid["report_content_sha256"] = "0" * 64

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=cycle.CURRENT_DESIGN_ACTIVATION_DATE,
        execution_reports=[invalid],
        lifecycle_reports=[],
        source_quality_pass_by_date={},
        economic_reference_pass_by_date={},
    )

    assert rolling["global_candidate_blockers"] == []
    assert manifest["global_candidate_blockers"] == []
    assert rolling["status"] == "no_joined_lifecycle_rows"
    assert rolling["exclusions"] == [
        {
            "reason": "execution_report_content_hash_mismatch",
            "target_date": "2026-08-24",
        }
    ]


def test_wait_probe_selects_one_comparable_ev_basis_and_rejects_dual_basis():
    report = _current_execution_report(
        "2026-08-24",
        parent_id="probe-parent",
        trace_id="probe-trace",
        stock_code="000001",
    )
    probe_arm = report["ablation_arms"][1]
    result = next(
        row
        for row in report["results"]
        if row["micro_reversion_replay_arm"] == probe_arm
    )
    response = result["replay_result"]["candidate_response"]
    response.update(
        {
            "action": "WAIT",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
        }
    )
    result["candidate_response_content_sha256"] = cycle._sha256(response)
    probe_metrics = report["three_arm_evaluation"]["rows"][0]["arms"][probe_arm]
    probe_metrics.update(
        {
            "action": "WAIT",
            "exposure_role": "standardized_probe_observation_only",
            "exposure_fraction": None,
            "economic_signal_selected": True,
            "source_quality_adjusted_ev_pct": None,
            "standardized_probe_observation_ev_pct": 0.2,
            "notional_net_profit_eligible": False,
            "notional_incremental_value_krw": None,
            "adverse_exposure": True,
            "severe_tail_exposure": False,
            "after_cost_target_first": True,
        }
    )
    _reseal_execution_result_ids(report)

    normalized = cycle._validated_execution_rows(report)

    assert normalized[0]["control_ev_pct"] == pytest.approx(0.2)
    assert normalized[0]["control_ev_basis"] == ("standardized_one_share_probe_ev_pct")

    dual_basis = deepcopy(report)
    dual_basis["three_arm_evaluation"]["rows"][0]["arms"][probe_arm][
        "source_quality_adjusted_ev_pct"
    ] = 0.2
    _reseal_execution_report(dual_basis)
    with pytest.raises(
        ValueError,
        match="execution_report_exact_census_invalid:"
        "evaluation_result_semantic_binding_invalid",
    ):
        cycle._validated_execution_rows(dual_basis)


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


def test_current_r3_blocks_one_contract_invalid_lifecycle_day_in_21_day_census(
    monkeypatch,
):
    template = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="template-parent",
            trace_id="template-trace",
            stock_code="000001",
        )
    )[0]
    start = date.fromisoformat(cycle.CURRENT_DESIGN_ACTIVATION_DATE)
    reports: list[dict] = []
    lifecycle_reports: list[dict] = []
    normalized_by_date: dict[str, list[dict]] = {}
    source_pass: dict[str, bool] = {}
    economic_pass: dict[str, bool] = {}
    omitted_index = 10
    for index in range(21):
        target_date = (start + timedelta(days=index)).isoformat()
        trace_id = f"post-trace-{index}"
        parent_id = f"post-parent-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        reports.append(
            {
                "target_date": target_date,
                "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
            }
        )
        lifecycle = _lifecycle_report(
            target_date,
            trace_id=trace_id,
            stock_code=stock_code,
        )
        lifecycle_row = lifecycle["rows"][0]
        normalized_row = deepcopy(template)
        normalized_row.update(
            {
                "target_date": target_date,
                "paired_replay_parent_id": parent_id,
                "decision_trace_id": trace_id,
                "decision_ts": f"{target_date}T09:00:00+09:00",
                "stock_code": stock_code,
                "cost_profile_artifact_sha256": lifecycle_row[
                    "reviewed_cost_profile_sha256"
                ],
                "symbol_master_artifact_sha256": lifecycle_row[
                    "symbol_master_artifact_sha256"
                ],
            }
        )
        normalized_by_date[target_date] = [normalized_row]
        source_pass[target_date] = True
        economic_pass[target_date] = True
        if index == omitted_index:
            lifecycle["rows"][0]["duration_source"] = "resealed_invalid_clock"
            _seal_lifecycle_report(lifecycle)
        lifecycle_reports.append(lifecycle)

    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda report, **_kwargs: deepcopy(normalized_by_date[report["target_date"]]),
    )
    target_date = (start + timedelta(days=20)).isoformat()

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=reports,
        lifecycle_reports=lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
    )

    omitted_date = (start + timedelta(days=omitted_index)).isoformat()
    assert rolling["joined_parent_count"] == 20
    assert rolling["excluded_parent_count"] == 1
    assert rolling["global_candidate_blockers"] == [
        "current_lifecycle_exact_census_invalid:"
        f"{omitted_date}:post-parent-{omitted_index}:lifecycle_exact_join_missing"
    ]
    assert rolling["status"] == "historical_execution_contract_blocked"
    assert manifest["status"] == (
        "source_only_candidate_blocked_invalid_historical_execution"
    )
    assert manifest["candidate_count"] == 0

    clean_reports = list(reports)
    clean_lifecycle_reports = [
        _lifecycle_report(
            (start + timedelta(days=index)).isoformat(),
            trace_id=f"post-trace-{index}",
            stock_code=f"{index % 10 + 1:06d}",
        )
        for index in range(21)
    ]
    for index in range(21, 36):
        clean_date = (start + timedelta(days=index)).isoformat()
        trace_id = f"post-trace-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        clean_reports.append(
            {
                "target_date": clean_date,
                "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
            }
        )
        lifecycle = _lifecycle_report(
            clean_date,
            trace_id=trace_id,
            stock_code=stock_code,
        )
        row = deepcopy(template)
        row.update(
            {
                "target_date": clean_date,
                "paired_replay_parent_id": f"post-parent-{index}",
                "decision_trace_id": trace_id,
                "decision_ts": f"{clean_date}T09:00:00+09:00",
                "stock_code": stock_code,
                "cost_profile_artifact_sha256": lifecycle["rows"][0][
                    "reviewed_cost_profile_sha256"
                ],
                "symbol_master_artifact_sha256": lifecycle["rows"][0][
                    "symbol_master_artifact_sha256"
                ],
            }
        )
        normalized_by_date[clean_date] = [row]
        source_pass[clean_date] = True
        economic_pass[clean_date] = True
        clean_lifecycle_reports.append(lifecycle)
    clean_target_date = (start + timedelta(days=35)).isoformat()
    _clean_rolling, clean_manifest = cycle.build_rolling_source_only_candidates(
        target_date=clean_target_date,
        execution_reports=clean_reports,
        lifecycle_reports=clean_lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
    )
    assert clean_manifest["candidate_count"] > 0

    current_blocker = "source_quality_audit_unavailable:FileNotFoundError"
    blocked_rolling, blocked_manifest = cycle.build_rolling_source_only_candidates(
        target_date=clean_target_date,
        execution_reports=clean_reports,
        lifecycle_reports=clean_lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
        current_run_global_blockers=[current_blocker],
    )
    assert blocked_rolling["status"] == "source_quality_or_composed_chain_blocked"
    assert blocked_rolling["current_run_global_blockers"] == [current_blocker]
    assert blocked_rolling["current_run_global_blockers_sha256"] == cycle._sha256(
        [current_blocker]
    )
    assert blocked_manifest["status"] == "source_only_candidate_blocked_current_run"
    assert blocked_manifest["candidate_count"] == 0
    assert blocked_manifest["candidates"] == []
    assert blocked_manifest["source_current_run_global_blockers_sha256"] == (
        blocked_rolling["current_run_global_blockers_sha256"]
    )


def test_current_r3_natural_lifecycle_absence_is_parent_exclusion_not_global_block(
    monkeypatch,
):
    report = {
        "target_date": cycle.CURRENT_DESIGN_ACTIVATION_DATE,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="natural-wait-parent",
            trace_id="natural-wait-trace",
            stock_code="000001",
        )
    )[0]
    _retarget_normalized_execution_row(
        normalized,
        target_date=cycle.CURRENT_DESIGN_ACTIVATION_DATE,
        parent_id="natural-wait-parent",
        trace_id="natural-wait-trace",
    )
    normalized["captured_control_action"] = "WAIT"
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )

    diagnostic: dict = {}
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=cycle.CURRENT_DESIGN_ACTIVATION_DATE,
        execution_reports=[report],
        lifecycle_reports=[],
        source_quality_pass_by_date={cycle.CURRENT_DESIGN_ACTIVATION_DATE: True},
        economic_reference_pass_by_date={cycle.CURRENT_DESIGN_ACTIVATION_DATE: True},
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["global_candidate_blockers"] == []
    exclusion = rolling["exclusions"][0]
    assert exclusion["reason"] == "lifecycle_not_applicable_non_order_entry"
    assert exclusion["lifecycle_join_requirement"] == (
        "not_applicable_non_order_entry"
    )
    assert exclusion["repair_required"] is False
    assert rolling["status"] == "no_joined_lifecycle_rows"
    assert manifest["status"] == "no_source_only_candidate_passed_all_gates"
    assert diagnostic["status"] == "counterfactual_entry_diagnostic_evaluated"
    assert diagnostic["eligible_parent_count"] == 1
    assert diagnostic["candidate_count"] == 0
    assert diagnostic["input_disposition_counts"] == {"eligible": 1}
    assert "source_rows" not in diagnostic
    assert (
        rolling["counterfactual_entry_diagnostic"]["artifact_content_sha256"]
        == diagnostic["artifact_content_sha256"]
    )


def test_counterfactual_entry_full_census_keeps_source_and_economic_failed_dates(
    monkeypatch,
):
    start = date.fromisoformat(cycle.CURRENT_DESIGN_ACTIVATION_DATE)
    dates = [(start + timedelta(days=index)).isoformat() for index in range(3)]
    template = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="template-parent",
            trace_id="template-trace",
            stock_code="000001",
        )
    )[0]
    rows_by_date: dict[str, list[dict]] = {}
    reports = []
    for index, target_date in enumerate(dates):
        parent_id = f"census-parent-{index}"
        trace_id = f"census-trace-{index}"
        row = _retarget_normalized_execution_row(
            deepcopy(template),
            target_date=target_date,
            parent_id=parent_id,
            trace_id=trace_id,
        )
        row["captured_control_action"] = "DROP" if index == 2 else "WAIT"
        rows_by_date[target_date] = [row]
        reports.append(
            {
                "target_date": target_date,
                "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
            }
        )
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda report, **_kwargs: deepcopy(rows_by_date[report["target_date"]]),
    )

    diagnostic: dict = {}
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=dates[-1],
        execution_reports=reports,
        lifecycle_reports=[],
        source_quality_pass_by_date={dates[0]: True, dates[1]: False, dates[2]: True},
        economic_reference_pass_by_date={
            dates[0]: True,
            dates[1]: True,
            dates[2]: False,
        },
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["global_candidate_blockers"] == []
    assert manifest["candidate_count"] == 0
    assert diagnostic["eligible_parent_count"] == 1
    assert diagnostic["excluded_parent_count"] == 2
    assert diagnostic["full_parent_census_count"] == 3
    assert diagnostic["input_disposition_counts"] == {
        "eligible": 1,
        "excluded": 2,
    }
    assert diagnostic["exclusion_reason_counts"] == {
        "economic_reference_not_verified": 1,
        "source_quality_audit_not_pass": 1,
    }
    assert diagnostic["source_date_counts"] == {target_date: 1 for target_date in dates}


def test_current_r3_missing_holding_lifecycle_is_global_blocker(monkeypatch):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    report = {
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="missing-hold-parent",
            trace_id="missing-hold-trace",
            stock_code="000001",
        )
    )[0]
    normalized.update(
        {
            "target_date": target_date,
            "paired_replay_parent_id": "missing-hold-parent",
            "decision_trace_id": "missing-hold-trace",
            "decision_stage": "holding",
            "captured_control_action": "HOLD",
        }
    )
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )

    diagnostic: dict = {}
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=[],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["global_candidate_blockers"] == [
        "current_lifecycle_exact_census_invalid:"
        f"{target_date}:missing-hold-parent:lifecycle_exact_join_missing"
    ]
    assert manifest["candidate_count"] == 0
    assert diagnostic["status"] == "counterfactual_entry_diagnostic_blocked"
    assert diagnostic["eligible_parent_count"] == 0
    assert diagnostic["candidate_count"] == 0


@pytest.mark.parametrize(
    "source_event_stage",
    [
        "scale_in_submit_authority_retry",
        "first_touch_avgdown_submit_authority_retry",
    ],
)
def test_current_r3_holding_endpoint_scale_in_retry_binds_scale_in_trace_context(
    monkeypatch,
    source_event_stage,
):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    trace_id = f"{source_event_stage}-trace"
    parent_id = f"{source_event_stage}-parent"
    report = {
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id=parent_id,
            trace_id=trace_id,
            stock_code="000001",
        )
    )[0]
    normalized.update(
        {
            "target_date": target_date,
            "decision_ts": f"{target_date}T09:00:00+09:00",
            "decision_stage": "holding",
            "source_event_stage": source_event_stage,
            "captured_control_action": "HOLD",
        }
    )
    lifecycle = _lifecycle_report(
        target_date,
        trace_id=trace_id,
        stock_code="000001",
    )
    lifecycle["rows"][0]["decision_trace_context_path"][0]["stage"] = "scale_in"
    normalized["cost_profile_artifact_sha256"] = lifecycle["rows"][0][
        "reviewed_cost_profile_sha256"
    ]
    normalized["symbol_master_artifact_sha256"] = lifecycle["rows"][0][
        "symbol_master_artifact_sha256"
    ]
    _seal_lifecycle_report(lifecycle)
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=[lifecycle],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert cycle._execution_lifecycle_stage(normalized) == "scale_in"
    assert rolling["joined_parent_count"] == 1
    assert rolling["excluded_parent_count"] == 0
    assert not any(
        "daily_lifecycle_trace_context_missing" in blocker
        for blocker in rolling["global_candidate_blockers"]
    )
    assert manifest["candidate_count"] == 0


def test_scale_in_trace_context_requires_exact_bound_source_event_stage():
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    lifecycle = _lifecycle_report(
        target_date,
        trace_id="scale-in-exact-stage-trace",
        stock_code="000001",
    )
    lifecycle_row = lifecycle["rows"][0]
    lifecycle_row["decision_trace_context_path"][0]["stage"] = "scale_in"
    execution_row = {
        "decision_trace_id": "scale-in-exact-stage-trace",
        "decision_stage": "holding",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
    }

    assert cycle._lifecycle_trace_context_findings(lifecycle_row, execution_row) == [
        "daily_lifecycle_trace_context_missing"
    ]
    execution_row["source_event_stage"] = "scale_in_submit_authority_retry "
    assert cycle._lifecycle_trace_context_findings(lifecycle_row, execution_row) == [
        "daily_lifecycle_trace_context_stage_invalid"
    ]
    execution_row["source_event_stage"] = "scale_in_unregistered_retry"
    assert cycle._lifecycle_trace_context_findings(lifecycle_row, execution_row) == [
        "daily_lifecycle_trace_context_stage_invalid"
    ]
    execution_row["source_event_stage"] = "SCALE_IN_SUBMIT_AUTHORITY_RETRY"
    assert cycle._lifecycle_trace_context_findings(lifecycle_row, execution_row) == [
        "daily_lifecycle_trace_context_stage_invalid"
    ]


def test_execution_receipt_binds_source_event_stage_before_lifecycle_routing():
    report = _current_execution_report(
        "2026-08-14",
        parent_id="source-stage-bound-parent",
        trace_id="source-stage-bound-trace",
        stock_code="000001",
    )
    for request_ref in report["request_refs"]:
        request_ref["source_event_stage"] = "pre_submit_entry_ai_authority_retry"
    for result in report["results"]:
        result["source_event_stage"] = "pre_submit_entry_ai_authority_retry"
    _reseal_execution_result_ids(report)

    normalized = cycle._validated_execution_rows(report)

    assert normalized[0]["source_event_stage"] == (
        "pre_submit_entry_ai_authority_retry"
    )
    tampered = deepcopy(report)
    tampered["results"][0]["source_event_stage"] = "scale_in_submit_authority_retry"
    _reseal_execution_result_ids(tampered)
    with pytest.raises(ValueError, match="result_identity_content_or_hash_invalid"):
        cycle._validated_execution_rows(tampered)


def test_current_r3_missing_buy_lifecycle_remains_global_blocker(monkeypatch):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    report = {
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="missing-buy-parent",
            trace_id="missing-buy-trace",
            stock_code="000001",
        )
    )[0]
    normalized.update(
        {
            "target_date": target_date,
            "paired_replay_parent_id": "missing-buy-parent",
            "decision_trace_id": "missing-buy-trace",
            "decision_stage": "entry",
            "captured_control_action": "BUY",
        }
    )
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )
    diagnostic: dict = {}

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=[],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["global_candidate_blockers"] == [
        "current_lifecycle_exact_census_invalid:"
        f"{target_date}:missing-buy-parent:lifecycle_exact_join_missing"
    ]
    assert manifest["candidate_count"] == 0
    assert diagnostic["status"] == "counterfactual_entry_diagnostic_blocked"
    assert diagnostic["eligible_parent_count"] == 0


def test_current_r3_invalid_lifecycle_collection_is_global_blocker(monkeypatch):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    report = {
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="natural-wait-parent",
            trace_id="natural-wait-trace",
            stock_code="000001",
        )
    )[0]
    _retarget_normalized_execution_row(
        normalized,
        target_date=target_date,
        parent_id="natural-wait-parent",
        trace_id="natural-wait-trace",
    )
    normalized["captured_control_action"] = "WAIT"
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )

    diagnostic: dict = {}
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=[],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
        input_diagnostics=[
            {
                "target_date": target_date,
                "artifact": "lifecycle",
                "status": "invalid",
                "reason": "artifact_target_date_path_mismatch",
            }
        ],
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["global_candidate_blockers"] == [
        "historical_lifecycle_artifact_collection_invalid:"
        f"{target_date}:artifact_target_date_path_mismatch"
    ]
    assert manifest["candidate_count"] == 0
    assert diagnostic["status"] == "counterfactual_entry_diagnostic_blocked"
    assert diagnostic["candidate_count"] == 0


def test_counterfactual_entry_invalid_lifecycle_report_keeps_bound_exclusion(
    monkeypatch,
):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    report = {
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="invalid-lifecycle-parent",
            trace_id="invalid-lifecycle-trace",
            stock_code="000001",
        )
    )[0]
    _retarget_normalized_execution_row(
        normalized,
        target_date=target_date,
        parent_id="invalid-lifecycle-parent",
        trace_id="invalid-lifecycle-trace",
    )
    normalized["captured_control_action"] = "WAIT"
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )

    diagnostic: dict = {}
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=[{"schema": "invalid", "target_date": target_date}],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["status"] == "historical_execution_contract_blocked"
    assert manifest["candidate_count"] == 0
    assert diagnostic["status"] == "counterfactual_entry_diagnostic_blocked"
    assert diagnostic["eligible_parent_count"] == 0
    assert diagnostic["excluded_parent_count"] == 1
    assert diagnostic["input_disposition_counts"] == {"excluded": 1}


def test_preactivation_lifecycle_finding_overflow_does_not_block_current_diagnostic(
    monkeypatch,
):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    report = {
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
    }
    normalized = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="overflow-current-parent",
            trace_id="overflow-current-trace",
            stock_code="000001",
        )
    )[0]
    _retarget_normalized_execution_row(
        normalized,
        target_date=target_date,
        parent_id="overflow-current-parent",
        trace_id="overflow-current-trace",
    )
    normalized["captured_control_action"] = "WAIT"
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(normalized)],
    )
    legacy_lifecycle_reports = []
    for trace_id in ("legacy-overflow-a", "legacy-overflow-b"):
        lifecycle = _lifecycle_report("2026-08-24", trace_id=trace_id)
        lifecycle["rows"][0].pop("broker_execution_raw_envelope_schema")
        lifecycle["rows"][0].pop("broker_execution_provenance_state_counts")
        legacy_lifecycle_reports.append(_seal_lifecycle_report(lifecycle))
    monkeypatch.setattr(cycle, "MAX_LIFECYCLE_FINDINGS", 3)

    diagnostic: dict = {}
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=legacy_lifecycle_reports,
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
        counterfactual_entry_diagnostic_out=diagnostic,
    )

    assert rolling["global_candidate_blockers"] == []
    assert manifest["candidate_count"] == 0
    assert diagnostic["status"] == "counterfactual_entry_diagnostic_evaluated"
    assert diagnostic["global_blockers"] == []
    assert diagnostic["eligible_parent_count"] == 1
    assert rolling["lifecycle_report_findings"][-1] == (
        "lifecycle_findings_truncated:"
        "pre_current_design=2,current_design=0,undated=0"
    )


def _promotion_cluster_row(
    *,
    lifecycle_id: str,
    parent_id: str,
    trace_id: str,
    decision_ts: str,
    stock_code: str,
    control_action: str,
    candidate_action: str,
    candidate_ev_pct: float,
    candidate_notional_value_krw: float,
    lifecycle_metrics: dict,
    decision_stage: str = "holding",
    source_event_stage: str | None = None,
    lifecycle_stage: str = "holding",
) -> dict:
    lifecycle = {
        "main_lifecycle_id": lifecycle_id,
        "trade_date": "2026-08-25",
        "stock_code": stock_code,
        **lifecycle_metrics,
    }
    return {
        "target_date": "2026-08-25",
        "paired_replay_parent_id": parent_id,
        "decision_trace_id": trace_id,
        "decision_ts": decision_ts,
        "decision_stage": decision_stage,
        "source_event_stage": source_event_stage,
        "main_lifecycle_id": lifecycle_id,
        "lifecycle_stage": lifecycle_stage,
        "stock_code": stock_code,
        "control_action": control_action,
        "candidate_action": candidate_action,
        "control_signal_selected": True,
        "candidate_signal_selected": True,
        "control_ev_pct": 0.0,
        "candidate_ev_pct": candidate_ev_pct,
        "paired_ev_delta_pct": candidate_ev_pct,
        "control_severe_tail": False,
        "candidate_severe_tail": False,
        "candidate_notional_value_krw": candidate_notional_value_krw,
        "lifecycle_source_row_sha256": cycle._sha256(lifecycle),
        "lifecycle": lifecycle,
    }


def test_rolling_join_binds_two_stages_to_one_exact_lifecycle_before_economics(
    monkeypatch,
):
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    holding_trace = "joined-holding-trace"
    scale_in_trace = "joined-scale-in-trace"
    lifecycle = _lifecycle_report(
        target_date,
        trace_id=holding_trace,
        stock_code="000001",
    )
    lifecycle_row = lifecycle["rows"][0]
    lifecycle_row["decision_trace_ids"] = [holding_trace, scale_in_trace]
    lifecycle_row["decision_trace_context_path"] = [
        {
            "decision_trace_id": holding_trace,
            "stage": "holding",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "venue_source": "test_exact_context",
            "session_bucket_source": "test_exact_context",
            "transition_count": 1,
        },
        {
            "decision_trace_id": scale_in_trace,
            "stage": "scale_in",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "venue_source": "test_exact_context",
            "session_bucket_source": "test_exact_context",
            "transition_count": 1,
        },
    ]
    _seal_lifecycle_report(lifecycle)

    template = cycle._validated_execution_rows(
        _current_execution_report(
            "2026-08-14",
            parent_id="joined-template-parent",
            trace_id="joined-template-trace",
            stock_code="000001",
        )
    )[0]
    holding = _retarget_normalized_execution_row(
        deepcopy(template),
        target_date=target_date,
        parent_id="joined-holding-parent",
        trace_id=holding_trace,
    )
    scale_in = _retarget_normalized_execution_row(
        deepcopy(template),
        target_date=target_date,
        parent_id="joined-scale-in-parent",
        trace_id=scale_in_trace,
    )
    for row in (holding, scale_in):
        row.update(
            {
                "decision_stage": "holding",
                "captured_control_action": "HOLD",
                "stock_code": "000001",
                "cost_profile_artifact_sha256": lifecycle_row[
                    "reviewed_cost_profile_sha256"
                ],
                "symbol_master_artifact_sha256": lifecycle_row[
                    "symbol_master_artifact_sha256"
                ],
            }
        )
    holding.update(
        {
            "decision_ts": f"{target_date}T09:00:00+09:00",
            "source_event_stage": None,
            "control_action": "HOLD",
            "candidate_action": "EXIT",
            "candidate_notional_value_krw": 100.0,
        }
    )
    scale_in.update(
        {
            "decision_ts": f"{target_date}T09:01:00+09:00",
            "source_event_stage": "scale_in_submit_authority_retry",
            "control_action": "HOLD",
            "candidate_action": "BUY",
            "candidate_notional_value_krw": 900.0,
        }
    )
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda _report, **_kwargs: [deepcopy(holding), deepcopy(scale_in)],
    )

    rolling, _manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[
            {
                "target_date": target_date,
                "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
            }
        ],
        lifecycle_reports=[lifecycle],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert rolling["joined_parent_count"] == 2
    assert len(rolling["partitions"]) == 1
    metrics = rolling["partitions"][0]["windows"]["20"]
    assert metrics["common_parent_count"] == 2
    assert metrics["unique_lifecycle_count"] == 1
    assert metrics["unique_lifecycle_stage_cluster_count"] == 2
    assert metrics["lifecycle_promotion_estimated_parent_count"] == 1
    assert metrics["candidate_total_notional_net_profit_krw"] == pytest.approx(100.0)
    assert metrics["session_exposure_hours"] == pytest.approx(1.0)
    assert metrics["capital_time_krw_hours"] == pytest.approx(50_000.0)


def test_promotion_economics_use_one_causal_parent_per_exact_lifecycle():
    shared_lifecycle_metrics = {
        "session_exposure_sec": 3_600.0,
        "capital_time_krw_hours": 100.0,
        "actual_holding_duration_sec": 120.0,
        "bbo_coverage_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "invalid_transition_count": 0,
    }
    shared_lifecycle_id = f"mlc-{'a' * 32}"
    early_no_divergence = _promotion_cluster_row(
        lifecycle_id=shared_lifecycle_id,
        parent_id="parent-early-no-divergence",
        trace_id="trace-a",
        decision_ts="2026-08-25T09:00:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="HOLD",
        candidate_ev_pct=0.1,
        candidate_notional_value_krw=700.0,
        lifecycle_metrics=shared_lifecycle_metrics,
    )
    earliest_divergence = _promotion_cluster_row(
        lifecycle_id=shared_lifecycle_id,
        parent_id="parent-divergence-a",
        trace_id="trace-b",
        decision_ts="2026-08-25T09:01:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="EXIT",
        candidate_ev_pct=0.2,
        candidate_notional_value_krw=100.0,
        lifecycle_metrics=shared_lifecycle_metrics,
    )
    tied_later_identity = _promotion_cluster_row(
        lifecycle_id=shared_lifecycle_id,
        parent_id="parent-divergence-z",
        trace_id="trace-z",
        decision_ts="2026-08-25T09:01:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="EXIT",
        candidate_ev_pct=0.3,
        candidate_notional_value_krw=900.0,
        lifecycle_metrics=shared_lifecycle_metrics,
    )
    other_lifecycle = _promotion_cluster_row(
        lifecycle_id=f"mlc-{'b' * 32}",
        parent_id="parent-other-lifecycle",
        trace_id="trace-other",
        decision_ts="2026-08-25T09:02:00+09:00",
        stock_code="000002",
        control_action="HOLD",
        candidate_action="EXIT",
        candidate_ev_pct=0.4,
        candidate_notional_value_krw=50.0,
        lifecycle_metrics={
            **shared_lifecycle_metrics,
            "session_exposure_sec": 1_800.0,
            "capital_time_krw_hours": 25.0,
            "actual_holding_duration_sec": 60.0,
        },
    )
    rows = [
        early_no_divergence,
        earliest_divergence,
        tied_later_identity,
        other_lifecycle,
    ]

    metrics = cycle._window_metrics(
        rows,
        target_date="2026-08-25",
        trading_days=20,
    )
    reversed_metrics = cycle._window_metrics(
        list(reversed(rows)),
        target_date="2026-08-25",
        trading_days=20,
    )

    # EV remains a four-parent decision-level diagnostic.
    assert metrics["common_parent_count"] == 4
    assert metrics["decision_level_parent_count"] == 4
    assert metrics["candidate_source_quality_adjusted_ev_pct"] == pytest.approx(0.25)
    # Promotion economics use 100 from the first divergence and 50 from the
    # other lifecycle, never 700/900 from the same lifecycle-stage cluster.
    assert metrics["decision_level_candidate_notional_eligible_count"] == 4
    assert metrics["candidate_notional_eligible_count"] == 2
    assert metrics["candidate_total_notional_net_profit_krw"] == pytest.approx(150.0)
    assert metrics["session_exposure_hours"] == pytest.approx(1.5)
    assert metrics["capital_time_krw_hours"] == pytest.approx(125.0)
    assert metrics["net_profit_per_capital_krw_hour"] == pytest.approx(1.2)
    assert metrics["unique_lifecycle_count"] == 2
    assert metrics["unique_lifecycle_stage_cluster_count"] == 2
    assert metrics["lifecycle_promotion_estimated_parent_count"] == 2
    assert metrics["lifecycle_promotion_censored_parent_count"] == 2
    assert "lifecycle_promotion_estimator_census_invalid" not in (
        cycle._window_gate_findings(metrics)
    )
    for field in (
        "unique_lifecycle_census_sha256",
        "promotion_economics_input_census_sha256",
        "lifecycle_stage_cluster_census_sha256",
        "lifecycle_selected_parent_census_sha256",
    ):
        assert reversed_metrics[field] == metrics[field]
    assert reversed_metrics["candidate_total_notional_net_profit_krw"] == pytest.approx(
        150.0
    )


def test_promotion_economics_censor_later_scale_in_stage_for_same_lifecycle():
    lifecycle_id = f"mlc-{'d' * 32}"
    lifecycle_metrics = {
        "session_exposure_sec": 3_600.0,
        "capital_time_krw_hours": 100.0,
        "actual_holding_duration_sec": 120.0,
        "bbo_coverage_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "invalid_transition_count": 0,
    }
    earlier_holding_exit = _promotion_cluster_row(
        lifecycle_id=lifecycle_id,
        parent_id="parent-holding-exit",
        trace_id="trace-holding-exit",
        decision_ts="2026-08-25T09:00:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="EXIT",
        candidate_ev_pct=0.2,
        candidate_notional_value_krw=100.0,
        lifecycle_metrics=lifecycle_metrics,
        lifecycle_stage="holding",
    )
    later_scale_in = _promotion_cluster_row(
        lifecycle_id=lifecycle_id,
        parent_id="parent-later-scale-in",
        trace_id="trace-later-scale-in",
        decision_ts="2026-08-25T09:01:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="BUY",
        candidate_ev_pct=0.4,
        candidate_notional_value_krw=900.0,
        lifecycle_metrics=lifecycle_metrics,
        source_event_stage="scale_in_submit_authority_retry",
        lifecycle_stage="scale_in",
    )

    metrics = cycle._window_metrics(
        [later_scale_in, earlier_holding_exit],
        target_date="2026-08-25",
        trading_days=20,
    )

    assert metrics["common_parent_count"] == 2
    assert metrics["candidate_source_quality_adjusted_ev_pct"] == pytest.approx(0.3)
    assert metrics["unique_lifecycle_count"] == 1
    assert metrics["unique_lifecycle_stage_cluster_count"] == 2
    assert metrics["lifecycle_promotion_estimated_parent_count"] == 1
    assert metrics["lifecycle_promotion_censored_parent_count"] == 1
    assert metrics["candidate_notional_eligible_count"] == 1
    assert metrics["candidate_total_notional_net_profit_krw"] == pytest.approx(100.0)
    assert metrics["session_exposure_hours"] == pytest.approx(1.0)
    assert metrics["capital_time_krw_hours"] == pytest.approx(100.0)
    assert metrics["net_profit_per_capital_krw_hour"] == pytest.approx(1.0)
    assert "lifecycle_promotion_estimator_census_invalid" not in (
        cycle._window_gate_findings(metrics)
    )


def test_promotion_economics_censor_lifecycle_without_decision_divergence():
    row = _promotion_cluster_row(
        lifecycle_id=f"mlc-{'e' * 32}",
        parent_id="parent-no-divergence",
        trace_id="trace-no-divergence",
        decision_ts="2026-08-25T09:00:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="HOLD",
        candidate_ev_pct=0.2,
        candidate_notional_value_krw=500.0,
        lifecycle_metrics={
            "session_exposure_sec": 3_600.0,
            "capital_time_krw_hours": 100.0,
            "actual_holding_duration_sec": 120.0,
            "bbo_coverage_pct": 100.0,
            "depth_coverage_pct": 100.0,
            "invalid_transition_count": 0,
        },
    )

    metrics = cycle._window_metrics(
        [row],
        target_date="2026-08-25",
        trading_days=20,
    )

    assert metrics["common_parent_count"] == 1
    assert metrics["candidate_source_quality_adjusted_ev_pct"] == pytest.approx(0.2)
    assert metrics["unique_lifecycle_count"] == 1
    assert metrics["lifecycle_no_divergence_count"] == 1
    assert metrics["lifecycle_promotion_estimated_parent_count"] == 0
    assert metrics["lifecycle_promotion_censored_parent_count"] == 1
    assert metrics["candidate_notional_eligible_count"] == 0
    assert metrics["candidate_total_notional_net_profit_krw"] is None
    assert metrics["session_exposure_hours"] is None
    assert metrics["capital_time_krw_hours"] is None
    assert "lifecycle_promotion_estimator_census_invalid" not in (
        cycle._window_gate_findings(metrics)
    )


def test_promotion_estimator_rejects_conflicting_rows_for_exact_lifecycle_id():
    lifecycle_id = f"mlc-{'c' * 32}"
    metrics = {
        "session_exposure_sec": 3_600.0,
        "capital_time_krw_hours": 100.0,
        "actual_holding_duration_sec": 120.0,
        "bbo_coverage_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "invalid_transition_count": 0,
    }
    first = _promotion_cluster_row(
        lifecycle_id=lifecycle_id,
        parent_id="parent-conflict-a",
        trace_id="trace-conflict-a",
        decision_ts="2026-08-25T09:00:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="EXIT",
        candidate_ev_pct=0.2,
        candidate_notional_value_krw=100.0,
        lifecycle_metrics=metrics,
    )
    conflicting = _promotion_cluster_row(
        lifecycle_id=lifecycle_id,
        parent_id="parent-conflict-b",
        trace_id="trace-conflict-b",
        decision_ts="2026-08-25T09:01:00+09:00",
        stock_code="000001",
        control_action="HOLD",
        candidate_action="EXIT",
        candidate_ev_pct=0.2,
        candidate_notional_value_krw=100.0,
        lifecycle_metrics={**metrics, "capital_time_krw_hours": 999.0},
    )

    with pytest.raises(
        ValueError,
        match="rolling_lifecycle_promotion_identity_cluster_conflict",
    ):
        cycle._window_metrics(
            [first, conflicting],
            target_date="2026-08-25",
            trading_days=20,
        )
