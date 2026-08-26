import gzip
import hashlib
import json
import os
import fcntl
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.micro_reversion import (
    storage_maintenance as storage_maintenance_module,
)
from src.engine.scalping.micro_reversion.path_journal import PathStoragePolicy
from src.engine.scalping.micro_reversion.storage_maintenance import (
    evaluate_large_artifact_capacity_gate,
    maintain_forward_storage,
    maintain_report_artifact_storage,
    purge_excluded_forward_scopes,
)


def _canonical_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _with_hash(payload: dict[str, object], field: str) -> dict[str, object]:
    return {**payload, field: _canonical_hash(payload)}


def _provider_canonical_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _with_provider_hash(
    payload: dict[str, object],
    field: str,
) -> dict[str, object]:
    return {**payload, field: _provider_canonical_hash(payload)}


_STORAGE_SOURCE_ONLY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
_STORAGE_CURRENT_P2_SOURCE_ONLY = {
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}


def _write_source_exclusion_fixture(
    path: Path,
    *,
    trade_date: str,
    venue: str = "SOR",
    session_bucket: str = "SOR_REGULAR",
    sequence_epoch: int = 123,
    stream_rows: int = 1,
    reference_rows: int = 1,
) -> None:
    payload = {
        "schema": "scalp_micro_reversion_source_exclusion_manifest_v1",
        "generated_at": f"{trade_date}T20:00:00+09:00",
        "source_base_commit": "a" * 40,
        "scope_policy": "exact_trade_date_venue_session_sequence_epoch",
        "summary": {
            "trade_date_count": 1,
            "excluded_scope_count": 1,
            "excluded_market_stream_row_count": stream_rows,
            "excluded_event_reference_count": reference_rows,
        },
        "exclusions": [
            {
                "trade_date": trade_date,
                "venue": venue,
                "session_bucket": session_bucket,
                "sequence_epoch": sequence_epoch,
                "reason_code": "test_source_quality_failure",
                "market_stream_row_count": stream_rows,
                "event_reference_count": reference_rows,
                "exchange_window_start": f"{trade_date}T09:00:00+09:00",
                "exchange_window_end": f"{trade_date}T09:00:01+09:00",
                "evidence": "test",
            }
        ],
        "metric_role": "source_quality_exclusion_and_gate_b_input_filter",
        "decision_authority": "p2_source_filter_only_no_policy_selection_authority",
        "window_policy": "exact_trade_date_venue_session_sequence_epoch_only",
        "sample_floor": "not_applicable_exact_failed_process_scope_exclusion",
        "primary_decision_metric": "excluded_market_stream_row_count",
        "source_quality_gate": "documented_exact_process_scope_failure",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "selection_authority": False,
        "forbidden_uses": ["whole_trade_date_exclusion"],
    }
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _write_exclusion_partition(
    root: Path,
    *,
    trade_date: str,
    excluded_epoch: int = 123,
    valid_epoch: int = 456,
) -> tuple[Path, Path, Path, Path]:
    leaf = root / f"trade_date={trade_date}" / "venue=SOR" / "session=SOR_REGULAR"
    leaf.mkdir(parents=True)
    stream = leaf / "market_stream.jsonl.gz"
    references = leaf / "market_stream_event_references.jsonl.gz"
    depth = leaf / "market_depth_stream.jsonl.gz"
    with gzip.open(stream, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"sequence_epoch": excluded_epoch, "row": "bad"}) + "\n"
        )
        handle.write(json.dumps({"sequence_epoch": valid_epoch, "row": "good"}) + "\n")
    with gzip.open(references, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"sequence_epoch": excluded_epoch, "ref": "bad"}) + "\n"
        )
        handle.write(json.dumps({"sequence_epoch": valid_epoch, "ref": "good"}) + "\n")
    with gzip.open(depth, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"sequence_epoch": excluded_epoch, "depth": "kept"}) + "\n"
        )
    manifest = leaf / "market_stream.manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_market_path_manifest_v1",
                "shards": [
                    {
                        "index": 0,
                        "file": stream.name,
                        "bytes": stream.stat().st_size,
                        "compressed": True,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return stream, references, depth, manifest


def test_storage_maintenance_dry_run_does_not_mutate(tmp_path: Path) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
    )

    assert result["mode"] == "dry_run"
    assert result["action_count"] == 1
    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_reports_truthful_reclaimed_and_retained_bytes(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    payload = b'{"value":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}\n' * 8_192
    source.write_bytes(payload)

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    compressed = source.with_suffix(".jsonl.gz")
    compressed_bytes = compressed.stat().st_size
    assert compressed_bytes < len(payload)
    assert result["retained_physical_bytes_before"] == len(payload)
    assert result["retained_physical_bytes_after"] == compressed_bytes
    assert result["retained_physical_bytes_delta"] == compressed_bytes - len(payload)
    assert result["compressed_target_bytes"] == compressed_bytes
    assert result["bytes_reclaimed"] == len(payload) - compressed_bytes
    assert result["deletion_performed"] is False


def test_storage_maintenance_low_capacity_is_warning_not_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path.mkdir(exist_ok=True)
    snapshots = iter(
        (
            {"disk_total_bytes": 1_000, "disk_used_bytes": 800, "disk_free_bytes": 200},
            {"disk_total_bytes": 1_000, "disk_used_bytes": 950, "disk_free_bytes": 50},
        )
    )
    monkeypatch.setattr(
        storage_maintenance_module,
        "_disk_capacity_snapshot",
        lambda _path: next(snapshots),
    )

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(
            low_disk_watermark_bytes=100,
            critical_disk_watermark_bytes=25,
        ),
        apply=True,
    )

    assert result["status"] == "pass"
    assert result["capacity_state"] == "low_warning"
    assert result["capacity_warning"] is True
    assert result["capacity_failure"] is False
    assert result["capacity_workorder_required"] is True
    assert result["capacity_reason_codes"] == ["disk_free_below_low_watermark"]
    assert result["disk_free_bytes_before"] == 200
    assert result["disk_free_bytes_after"] == 50
    assert result["disk_free_bytes_delta"] == -150


def test_storage_maintenance_cli_critical_capacity_writes_source_only_status_and_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "forward"
    root.mkdir()
    status_path = tmp_path / "reports" / "capacity.json"
    monkeypatch.setattr(
        storage_maintenance_module,
        "_disk_capacity_snapshot",
        lambda _path: {
            "disk_total_bytes": 1_000,
            "disk_used_bytes": 990,
            "disk_free_bytes": 10,
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "storage_maintenance",
            "--root",
            str(root),
            "--as-of-date",
            "2026-08-10",
            "--apply",
            "--low-disk-watermark-bytes",
            "100",
            "--critical-disk-watermark-bytes",
            "25",
            "--capacity-status-path",
            str(status_path),
        ],
    )

    exit_code = storage_maintenance_module.main()

    emitted = json.loads(capsys.readouterr().out)
    artifact = json.loads(status_path.read_text(encoding="utf-8"))
    declared_hash = artifact.pop("artifact_content_sha256")
    assert exit_code == 1
    assert emitted["status"] == "partial_failure"
    assert emitted["capacity_state"] == "critical"
    assert emitted["capacity_status_written"] is True
    assert artifact["status"] == "critical_blocked"
    assert artifact["capacity_workorder"]["state"] == "open"
    assert artifact["automatic_deletion_authorized"] is False
    assert artifact["runtime_effect"] is False
    assert artifact["actual_order_submitted"] is False
    assert artifact["broker_order_forbidden"] is True
    assert artifact["deletion_performed"] is False
    assert declared_hash == _canonical_hash(artifact)


def _write_capacity_status(
    path: Path,
    *,
    target_date: date,
    free_bytes: int,
    low_watermark: int = 100,
    critical_watermark: int = 25,
) -> dict[str, object]:
    state = (
        "critical"
        if free_bytes < critical_watermark
        else ("low_warning" if free_bytes < low_watermark else "healthy")
    )
    result = {
        "capacity_state": state,
        "capacity_reason_codes": (
            ["disk_free_below_critical_watermark"]
            if state == "critical"
            else (["disk_free_below_low_watermark"] if state == "low_warning" else [])
        ),
        "disk_total_bytes": 1_000,
        "disk_used_bytes_after": 1_000 - free_bytes,
        "disk_free_bytes_before": free_bytes,
        "disk_free_bytes_after": free_bytes,
        "disk_free_bytes_delta": 0,
        "retained_physical_bytes_before": 0,
        "retained_physical_bytes_after": 0,
        "retained_physical_bytes_delta": 0,
        "compressed_target_bytes": 0,
        "bytes_reclaimed": 0,
        "low_disk_watermark_bytes": low_watermark,
        "critical_disk_watermark_bytes": critical_watermark,
        "purge_enabled": False,
        "deletion_performed": False,
    }
    artifact = storage_maintenance_module._capacity_status_artifact(
        result,
        target_date=target_date,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact) + "\n", encoding="utf-8")
    return artifact


def test_large_artifact_capacity_gate_allows_missing_artifact_from_direct_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        storage_maintenance_module,
        "_disk_capacity_snapshot",
        lambda _path: {
            "disk_total_bytes": 1_000,
            "disk_used_bytes": 800,
            "disk_free_bytes": 200,
        },
    )

    result = evaluate_large_artifact_capacity_gate(
        target_date=date(2026, 8, 25),
        capacity_status_path=tmp_path / "missing.json",
        storage_path=tmp_path,
        low_disk_watermark_bytes=100,
        critical_disk_watermark_bytes=25,
    )

    assert result["status"] == "allowed"
    assert result["large_artifact_growth_allowed"] is True
    assert result["artifact_status"] == "missing"
    assert result["direct_capacity_state"] == "healthy"
    assert result["direct_snapshot_provenance"] == (
        "shutil.disk_usage_at_consumer_gate"
    )
    assert (
        "capacity_status_artifact_missing_direct_snapshot_used"
        in result["reason_codes"]
    )


def test_large_artifact_capacity_gate_blocks_invalid_present_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_path = tmp_path / "capacity.json"
    artifact = _write_capacity_status(
        status_path,
        target_date=date(2026, 8, 25),
        free_bytes=200,
    )
    artifact["artifact_content_sha256"] = "0" * 64
    status_path.write_text(json.dumps(artifact) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        storage_maintenance_module,
        "_disk_capacity_snapshot",
        lambda _path: {
            "disk_total_bytes": 1_000,
            "disk_used_bytes": 800,
            "disk_free_bytes": 200,
        },
    )

    result = evaluate_large_artifact_capacity_gate(
        target_date=date(2026, 8, 25),
        capacity_status_path=status_path,
        storage_path=tmp_path,
        low_disk_watermark_bytes=100,
        critical_disk_watermark_bytes=25,
    )

    assert result["status"] == "blocked_invalid_capacity_artifact"
    assert result["large_artifact_growth_allowed"] is False
    assert result["artifact_status"] == "invalid"
    assert "capacity_status_artifact_invalid" in result["reason_codes"]


@pytest.mark.parametrize(
    ("artifact_free", "direct_free", "expected_artifact_state"),
    ((10, 200, "critical"), (200, 10, "healthy")),
)
def test_large_artifact_capacity_gate_blocks_effective_critical_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact_free: int,
    direct_free: int,
    expected_artifact_state: str,
) -> None:
    status_path = tmp_path / "capacity.json"
    _write_capacity_status(
        status_path,
        target_date=date(2026, 8, 25),
        free_bytes=artifact_free,
    )
    monkeypatch.setattr(
        storage_maintenance_module,
        "_disk_capacity_snapshot",
        lambda _path: {
            "disk_total_bytes": 1_000,
            "disk_used_bytes": 1_000 - direct_free,
            "disk_free_bytes": direct_free,
        },
    )

    result = evaluate_large_artifact_capacity_gate(
        target_date=date(2026, 8, 25),
        capacity_status_path=status_path,
        storage_path=tmp_path,
        low_disk_watermark_bytes=100,
        critical_disk_watermark_bytes=25,
    )

    assert result["status"] == "blocked_critical_or_unknown_capacity"
    assert result["large_artifact_growth_allowed"] is False
    assert result["artifact_status"] == "valid"
    assert result["artifact_capacity_state"] == expected_artifact_state
    assert result["effective_capacity_state"] == "critical"


def test_large_artifact_capacity_gate_allows_effective_low_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_path = tmp_path / "capacity.json"
    _write_capacity_status(
        status_path,
        target_date=date(2026, 8, 25),
        free_bytes=50,
    )
    monkeypatch.setattr(
        storage_maintenance_module,
        "_disk_capacity_snapshot",
        lambda _path: {
            "disk_total_bytes": 1_000,
            "disk_used_bytes": 800,
            "disk_free_bytes": 200,
        },
    )

    result = evaluate_large_artifact_capacity_gate(
        target_date=date(2026, 8, 25),
        capacity_status_path=status_path,
        storage_path=tmp_path,
        low_disk_watermark_bytes=100,
        critical_disk_watermark_bytes=25,
    )

    assert result["status"] == "allowed_with_low_capacity_warning"
    assert result["large_artifact_growth_allowed"] is True
    assert result["effective_capacity_state"] == "low_warning"


def test_report_artifact_maintenance_compresses_only_owned_closed_dates(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    paired_root = tmp_path / "ai_prompt_paired_replay"
    paired_root.mkdir()
    closed = root / "ai_micro_reversion_three_arm_offline_results_2026-08-08.json"
    materialized = (
        root / "ai_micro_reversion_materialized_replay_requests_2026-08-08.json"
    )
    paired = paired_root / "ai_prompt_paired_replay_2026-08-08.json"
    suffixed_paired = paired_root / "ai_prompt_paired_replay_2026-08-08_entry_KRX.json"
    protected = root / "micro_reversion_ai_quality_bridge_2026-08-10.json"
    unrelated = root / "unowned_report_2026-08-08.json"
    materialized_content = {
        "schema": "ai_micro_reversion_materialized_replay_requests_v1",
        "target_date": "2026-08-08",
        **_STORAGE_SOURCE_ONLY,
    }
    materialized_report = _with_hash(
        materialized_content,
        "report_content_sha256",
    )
    materialized.write_text(
        json.dumps(materialized_report) + "\n",
        encoding="utf-8",
    )
    closed_content = {
        "schema": "ai_micro_reversion_three_arm_offline_results_v1",
        "target_date": "2026-08-08",
        "status": "offline_three_arm_execution_complete",
        "materialized_report_content_sha256": materialized_report[
            "report_content_sha256"
        ],
        "materialized_request_census_sha256": "a" * 64,
        "request_count": 1,
        "result_count": 1,
        "deferred_request_count": 0,
        **_STORAGE_SOURCE_ONLY,
    }
    closed_bytes = (
        json.dumps(_with_hash(closed_content, "report_content_sha256")) + "\n"
    ).encode()
    closed.write_bytes(closed_bytes)
    paired.write_text(
        json.dumps(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": "2026-08-08",
                **_STORAGE_SOURCE_ONLY,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    suffixed_paired.write_text('{"target_date":"2026-08-08"}\n', encoding="utf-8")
    protected_content = {
        "schema": "micro_reversion_ai_quality_bridge_v1",
        "target_date": "2026-08-10",
        **_STORAGE_SOURCE_ONLY,
    }
    protected.write_text(
        json.dumps(_with_hash(protected_content, "report_content_sha256")) + "\n",
        encoding="utf-8",
    )
    unrelated.write_text('{"target_date":"2026-08-08"}\n', encoding="utf-8")

    dry_run = maintain_report_artifact_storage(
        [root, paired_root],
        as_of_date=date(2026, 8, 10),
        retention_days=1,
    )

    assert dry_run["status"] == "pass"
    assert dry_run["action_count"] == 3
    assert dry_run["retention_candidate_count"] == 3
    assert dry_run["deletion_performed"] is False
    assert closed.exists()
    assert not closed.with_suffix(".json.gz").exists()

    applied = maintain_report_artifact_storage(
        [root, paired_root],
        as_of_date=date(2026, 8, 10),
        retention_days=1,
        apply=True,
    )

    compressed = closed.with_suffix(".json.gz")
    assert applied["status"] == "pass"
    assert applied["compressed_count"] == 3
    assert applied["actions"][0]["action"] == "compress_json_artifact"
    assert not closed.exists()
    with gzip.open(compressed, "rb") as handle:
        assert handle.read() == closed_bytes
    assert not materialized.exists()
    assert materialized.with_suffix(".json.gz").exists()
    assert not paired.exists()
    assert paired.with_suffix(".json.gz").exists()
    assert suffixed_paired.exists()
    assert not suffixed_paired.with_suffix(".json.gz").exists()
    assert protected.exists()
    assert unrelated.exists()
    assert applied["retention_policy"] == (
        "compressed_full_audit_retained_deletion_requires_separate_authority"
    )


def test_report_artifact_maintenance_covers_all_daily_r0_r3_outputs(
    tmp_path: Path,
) -> None:
    root = tmp_path / "main_ai_quality_r0_r3"
    root.mkdir()
    artifact_contracts = {
        "main_ai_quality_micro_control_driver_2026-08-08.json": (
            "main_ai_quality_micro_control_driver_v1"
        ),
        "main_ai_quality_rolling_paired_2026-08-08.json": (
            "main_ai_quality_rolling_paired_evaluation_v1"
        ),
        "main_ai_quality_r3_source_candidates_2026-08-08.json": (
            "main_ai_quality_source_only_candidate_manifest_v1"
        ),
        "main_ai_quality_r0_r3_cycle_2026-08-08.json": (
            "main_ai_quality_postclose_r0_r3_cycle_v1"
        ),
        "main_ai_quality_counterfactual_entry_2026-08-08.json": (
            "main_ai_quality_counterfactual_entry_r3_diagnostic_v1"
        ),
        "micro_reversion_storage_capacity_2026-08-08.json": (
            "scalp_micro_reversion_storage_capacity_status_v1"
        ),
    }
    for file_name, schema in artifact_contracts.items():
        content = {
            "schema": schema,
            "target_date": "2026-08-08",
            **_STORAGE_SOURCE_ONLY,
        }
        (root / file_name).write_text(
            json.dumps(_with_hash(content, "artifact_content_sha256")) + "\n",
            encoding="utf-8",
        )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "pass"
    assert result["compressed_count"] == len(artifact_contracts)
    assert result["artifact_set_census"]["immutable_source_artifact_count"] == len(
        artifact_contracts
    )
    for file_name in artifact_contracts:
        logical = root / file_name
        assert not logical.exists()
        assert logical.with_suffix(".json.gz").exists()


def test_report_artifact_maintenance_covers_all_current_p2_basenames_and_is_idempotent(
    tmp_path: Path,
) -> None:
    root = tmp_path / "p2_artifacts"
    root.mkdir()
    target_date = "2026-08-08"

    source_bundle_content = {
        "schema": "ai_micro_reversion_replay_source_bundle_v1",
        "target_date": target_date,
        "rows": [],
        **_STORAGE_SOURCE_ONLY,
    }
    source_bundle = _with_hash(
        source_bundle_content,
        "source_bundle_content_sha256",
    )
    materialized_content = {
        "schema": "ai_micro_reversion_materialized_replay_requests_v1",
        "target_date": target_date,
        "source_bundle_content_sha256": source_bundle["source_bundle_content_sha256"],
        "source_bundle_artifact_sha256": _canonical_hash(source_bundle),
        **_STORAGE_SOURCE_ONLY,
    }
    materialized = _with_hash(materialized_content, "report_content_sha256")
    execution_content = {
        "schema": "ai_micro_reversion_three_arm_offline_results_v1",
        "target_date": target_date,
        "status": "offline_three_arm_execution_complete",
        "materialized_report_content_sha256": materialized["report_content_sha256"],
        "materialized_request_census_sha256": "a" * 64,
        "request_count": 0,
        "result_count": 0,
        "deferred_request_count": 0,
        **_STORAGE_SOURCE_ONLY,
    }
    execution = _with_hash(execution_content, "report_content_sha256")

    hashed_artifacts = {
        f"ai_micro_reversion_replay_source_bundle_{target_date}.json": (
            source_bundle,
            "source_bundle_content_sha256",
        ),
        f"ai_micro_reversion_materialized_replay_requests_{target_date}.json": (
            materialized,
            "report_content_sha256",
        ),
        f"ai_micro_reversion_action_neutral_outcome_labels_{target_date}.json": (
            _with_hash(
                {
                    "schema": "ai_micro_reversion_action_neutral_outcome_labels_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"ai_micro_reversion_three_arm_offline_results_{target_date}.json": (
            execution,
            "report_content_sha256",
        ),
        f"micro_reversion_ai_quality_bridge_{target_date}.json": (
            _with_hash(
                {
                    "schema": "micro_reversion_ai_quality_bridge_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "report_content_sha256",
            ),
            "report_content_sha256",
        ),
        f"main_ai_quality_micro_prepared_requests_{target_date}.json": (
            _with_hash(
                {
                    "schema": "main_ai_quality_micro_prepared_requests_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"main_ai_quality_micro_control_driver_{target_date}.json": (
            _with_hash(
                {
                    "schema": "main_ai_quality_micro_control_driver_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"main_ai_quality_rolling_paired_{target_date}.json": (
            _with_hash(
                {
                    "schema": "main_ai_quality_rolling_paired_evaluation_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"main_ai_quality_r3_source_candidates_{target_date}.json": (
            _with_hash(
                {
                    "schema": "main_ai_quality_source_only_candidate_manifest_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"main_ai_quality_r0_r3_cycle_{target_date}.json": (
            _with_hash(
                {
                    "schema": "main_ai_quality_postclose_r0_r3_cycle_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"main_ai_quality_counterfactual_entry_{target_date}.json": (
            _with_hash(
                {
                    "schema": "main_ai_quality_counterfactual_entry_r3_diagnostic_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"micro_reversion_provider_ablation_sample_floor_{target_date}.json": (
            _with_hash(
                {
                    "schema": "micro_reversion_provider_ablation_sample_floor_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "floor_content_sha256",
            ),
            "floor_content_sha256",
        ),
        f"micro_reversion_storage_capacity_{target_date}.json": (
            _with_hash(
                {
                    "schema": "scalp_micro_reversion_storage_capacity_status_v1",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"micro_reversion_economic_reference_{target_date}.json": (
            _with_hash(
                {
                    "schema": "micro_reversion_economic_reference_daily_resolution_v2",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "artifact_content_sha256",
            ),
            "artifact_content_sha256",
        ),
        f"micro_reversion_reviewed_cost_profile_{target_date}.json": (
            _with_hash(
                {
                    "schema": "micro_reversion_reviewed_cost_catalog_v2",
                    "target_date": target_date,
                    **_STORAGE_SOURCE_ONLY,
                },
                "content_sha256",
            ),
            "content_sha256",
        ),
        f"micro_reversion_symbol_master_{target_date}.json": (
            _with_hash(
                {
                    "schema": "scalp_micro_reversion_symbol_master_v1",
                    "artifact_id": (
                        f"main-ai-economic-reference-{target_date}-symbol-master"
                    ),
                    **_STORAGE_SOURCE_ONLY,
                },
                "content_sha256",
            ),
            "content_sha256",
        ),
    }
    unhashed_artifacts = {
        f"ai_prompt_paired_replay_{target_date}.json": {
            "schema": "ai_prompt_paired_replay_v1",
            "target_date": target_date,
            **_STORAGE_SOURCE_ONLY,
        }
    }
    expected_names = set(hashed_artifacts) | set(unhashed_artifacts)
    assert len(storage_maintenance_module.REPORT_ARTIFACT_NAME_PATTERNS) == 17
    assert len(expected_names) == 17
    assert all(
        storage_maintenance_module._report_artifact_trade_date(name)
        == date.fromisoformat(target_date)
        for name in expected_names
    )

    original_bytes: dict[str, bytes] = {}
    for file_name, (payload, _) in hashed_artifacts.items():
        path = root / file_name
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        original_bytes[file_name] = path.read_bytes()
    for file_name, payload in unhashed_artifacts.items():
        path = root / file_name
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        original_bytes[file_name] = path.read_bytes()

    first = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert first["status"] == "pass"
    assert first["compressed_count"] == len(expected_names)
    assert first["artifact_set_census"]["immutable_source_artifact_count"] == 16
    compressed_bytes: dict[str, bytes] = {}
    for file_name in expected_names:
        logical = root / file_name
        compressed = logical.with_suffix(".json.gz")
        assert not logical.exists()
        with gzip.open(compressed, "rb") as handle:
            assert handle.read() == original_bytes[file_name]
        compressed_bytes[file_name] = compressed.read_bytes()
    for file_name, (_, hash_field) in hashed_artifacts.items():
        with gzip.open((root / file_name).with_suffix(".json.gz"), "rb") as handle:
            payload = json.loads(handle.read())
        storage_maintenance_module._validate_content_hash(
            payload,
            hash_field=hash_field,
        )

    second = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert second["status"] == "pass"
    assert second["action_count"] == 0
    assert second["compressed_count"] == 0
    assert {
        file_name: (root / file_name).with_suffix(".json.gz").read_bytes()
        for file_name in expected_names
    } == compressed_bytes


@pytest.mark.parametrize("link_suffix", (".json", ".json.gz"))
def test_report_artifact_maintenance_rejects_dangling_allowlisted_symlink(
    tmp_path: Path,
    link_suffix: str,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    link = root / (
        "micro_reversion_provider_ablation_sample_floor_2026-08-08" + link_suffix
    )
    link.symlink_to(tmp_path / "missing-provider-floor")

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["failure_count"] >= 1
    assert link.is_symlink()
    assert any("symlink" in failure["reason"].lower() for failure in result["failures"])


def test_report_artifact_maintenance_rejects_dangling_root_symlink(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.symlink_to(tmp_path / "missing-report-root", target_is_directory=True)

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["failure_count"] == 1
    assert result["failures"][0]["path"] == str(root.absolute())
    assert "real directory" in result["failures"][0]["reason"]
    assert root.is_symlink()


@pytest.mark.parametrize(
    "floor_schema",
    [
        storage_maintenance_module.LEGACY_PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
        storage_maintenance_module.PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
    ],
)
def test_report_artifact_maintenance_scopes_current_p2_authority_from_floor_schemas(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    floor_schema: str,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    target_date = "2026-08-24"
    monkeypatch.setattr(
        storage_maintenance_module,
        "CURRENT_DESIGN_ACTIVATION_DATE",
        target_date,
    )
    floor_content = {
        "schema": floor_schema,
        "target_date": target_date,
        **_STORAGE_CURRENT_P2_SOURCE_ONLY,
    }
    floor = root / f"micro_reversion_provider_ablation_sample_floor_{target_date}.json"
    floor.write_text(
        json.dumps(_with_hash(floor_content, "floor_content_sha256")) + "\n",
        encoding="utf-8",
    )
    # These two artifacts are intentionally not governed by the ablation
    # seven-field authority surface: paired is a general replay input and
    # capacity is an operational storage receipt.
    paired = root / f"ai_prompt_paired_replay_{target_date}.json"
    paired.write_text(
        json.dumps(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": target_date,
                **_STORAGE_SOURCE_ONLY,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    capacity_content = {
        "schema": "scalp_micro_reversion_storage_capacity_status_v1",
        "target_date": target_date,
        **_STORAGE_SOURCE_ONLY,
    }
    capacity = root / f"micro_reversion_storage_capacity_{target_date}.json"
    capacity.write_text(
        json.dumps(_with_hash(capacity_content, "artifact_content_sha256")) + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 25),
        apply=True,
    )

    assert result["status"] == "pass"
    assert result["compressed_count"] == 3
    for logical in (floor, paired, capacity):
        assert not logical.exists()
        assert logical.with_suffix(".json.gz").exists()


@pytest.mark.parametrize(
    ("field", "mutation"),
    [
        ("runtime_authority", "delete"),
        ("order_authority", "delete"),
        ("provider_authority", "delete"),
        *[
            (field, "true")
            for field in storage_maintenance_module.CURRENT_P2_FALSE_AUTHORITY_ALIASES
        ],
    ],
)
def test_report_artifact_maintenance_rejects_resealed_current_p2_authority_escalation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    mutation: str,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    target_date = "2026-08-24"
    monkeypatch.setattr(
        storage_maintenance_module,
        "CURRENT_DESIGN_ACTIVATION_DATE",
        target_date,
    )
    content = {
        "schema": "micro_reversion_provider_ablation_sample_floor_v1",
        "target_date": target_date,
        **_STORAGE_CURRENT_P2_SOURCE_ONLY,
    }
    if mutation == "delete":
        del content[field]
    else:
        content[field] = True
    artifact = root / (
        f"micro_reversion_provider_ablation_sample_floor_{target_date}.json"
    )
    artifact.write_text(
        json.dumps(_with_hash(content, "floor_content_sha256")) + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 25),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["compressed_count"] == 0
    assert artifact.exists()
    assert not artifact.with_suffix(".json.gz").exists()
    assert any(
        "source_only_authority" in failure["reason"] for failure in result["failures"]
    )


def test_report_artifact_maintenance_finalizes_verified_existing_gzip(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    source = (
        root
        / "superseded"
        / "generation-a"
        / "micro_reversion_ai_quality_bridge_2026-08-08.json"
    )
    source.parent.mkdir(parents=True)
    payload = b'{"target_date":"2026-08-08","value":1}\n'
    source.write_bytes(payload)
    compressed = source.with_suffix(".json.gz")
    with gzip.open(compressed, "wb") as handle:
        handle.write(payload)

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "pass"
    assert result["compressed_count"] == 1
    assert result["actions"][0]["action"] == (
        "finalize_verified_json_artifact_compression"
    )
    assert not source.exists()
    with gzip.open(compressed, "rb") as handle:
        assert handle.read() == payload


def test_report_artifact_maintenance_separates_superseded_generations_from_active_set(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    target_date = "2026-08-08"
    file_name = f"ai_micro_reversion_three_arm_offline_results_{target_date}.json"
    archived_paths = []
    for generation in ("generation-a", "generation-b"):
        generation_dir = root / "superseded" / generation
        generation_dir.mkdir(parents=True)
        archived = generation_dir / file_name
        archived.write_text(
            json.dumps({"target_date": target_date, "generation": generation}) + "\n",
            encoding="utf-8",
        )
        archived_paths.append(archived)
    active_content = {
        "schema": "ai_micro_reversion_three_arm_offline_results_v1",
        "target_date": target_date,
        "status": "offline_three_arm_execution_batch_complete",
        "request_count": 3,
        "result_count": 1,
        "deferred_request_count": 2,
        **_STORAGE_SOURCE_ONLY,
    }
    active = root / file_name
    active.write_text(
        json.dumps(_with_hash(active_content, "report_content_sha256")) + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "pass"
    census = result["artifact_set_census"]
    assert census["set_count"] == 3
    assert census["explicitly_superseded_count"] == 2
    assert census["incomplete_resumable_count"] == 1
    assert active.exists()
    assert not active.with_suffix(".json.gz").exists()
    for archived in archived_paths:
        assert not archived.exists()
        assert archived.with_suffix(".json.gz").exists()


def test_report_artifact_maintenance_keeps_paired_only_date_resumable(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ai_prompt_paired_replay"
    root.mkdir()
    paired = root / "ai_prompt_paired_replay_2026-08-01.json"
    paired.write_text(
        json.dumps(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": "2026-08-01",
                **_STORAGE_SOURCE_ONLY,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        retention_days=1,
        apply=True,
    )

    assert result["status"] == "pass"
    census = result["artifact_set_census"]
    assert census["set_count"] == 1
    assert census["incomplete_resumable_count"] == 1
    assert census["stale_workorder_count"] == 1
    assert census["immutable_source_artifact_count"] == 1
    assert not paired.exists()
    assert paired.with_suffix(".json.gz").exists()


def test_report_artifact_maintenance_rejects_paired_plain_gzip_mismatch(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ai_prompt_paired_replay"
    root.mkdir()
    paired = root / "ai_prompt_paired_replay_2026-08-01.json"
    paired.write_text(
        json.dumps(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": "2026-08-01",
                "generation": "plain",
                **_STORAGE_SOURCE_ONLY,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with gzip.open(paired.with_suffix(".json.gz"), "wt", encoding="utf-8") as handle:
        json.dump(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": "2026-08-01",
                "generation": "gzip",
                **_STORAGE_SOURCE_ONLY,
            },
            handle,
        )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert any(
        "owned_json_plain_gzip_mismatch" in failure["reason"]
        for failure in result["failures"]
    )
    assert paired.exists()
    assert paired.with_suffix(".json.gz").exists()


def _write_checkpoint_journal(
    root: Path,
    *,
    target_date: str,
    result_status: str | None,
    result_request_census_hash: str | None = None,
) -> tuple[Path, Path]:
    stem = f"ai_micro_reversion_three_arm_offline_results_{target_date}"
    checkpoint_path = root / f"{stem}.checkpoint.json"
    record_dir = root / f"{stem}.checkpoint.json.records"
    record_dir.mkdir(parents=True)
    materialized_hash = "a" * 64
    record_content = {
        "schema": "ai_micro_reversion_execution_checkpoint_record_v1",
        "materialized_report_content_sha256": materialized_hash,
        "checkpoint_record_sequence": 1,
        "previous_checkpoint_record_sha256": None,
        "result_id": "result-1",
        "result": {"result_id": "result-1"},
        "provider_call_performed": True,
        **_STORAGE_SOURCE_ONLY,
    }
    record = _with_hash(record_content, "checkpoint_record_content_sha256")
    record_hash = str(record["checkpoint_record_content_sha256"])
    record_path = record_dir / f"00000001-{record_hash}.json"
    record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    manifest_content = {
        "schema": "ai_micro_reversion_execution_checkpoint_manifest_v1",
        "materialized_report_content_sha256": materialized_hash,
        "checkpoint_record_count": 1,
        "checkpoint_head_sha256": record_hash,
        "record_directory": record_dir.name,
        "provider_call_performed": True,
        **_STORAGE_SOURCE_ONLY,
    }
    checkpoint_path.write_text(
        json.dumps(_with_hash(manifest_content, "checkpoint_manifest_content_sha256"))
        + "\n",
        encoding="utf-8",
    )
    if result_status is not None:
        materialized_content = {
            "schema": "ai_micro_reversion_materialized_replay_requests_v1",
            "target_date": target_date,
            **_STORAGE_SOURCE_ONLY,
        }
        materialized_report = _with_hash(
            materialized_content,
            "report_content_sha256",
        )
        (
            root / f"ai_micro_reversion_materialized_replay_requests_{target_date}.json"
        ).write_text(
            json.dumps(materialized_report) + "\n",
            encoding="utf-8",
        )
        terminal = result_status == "offline_three_arm_execution_complete"
        result_content = {
            "schema": "ai_micro_reversion_three_arm_offline_results_v1",
            "target_date": target_date,
            "status": result_status,
            "materialized_report_content_sha256": materialized_report[
                "report_content_sha256"
            ],
            "materialized_request_census_sha256": (
                result_request_census_hash or materialized_hash
            ),
            "request_count": 1 if terminal else 2,
            "result_count": 1,
            "deferred_request_count": 0 if terminal else 1,
            **_STORAGE_SOURCE_ONLY,
        }
        (root / f"{stem}.json").write_text(
            json.dumps(_with_hash(result_content, "report_content_sha256")) + "\n",
            encoding="utf-8",
        )
    return record_path, checkpoint_path


def test_report_artifact_maintenance_compresses_terminal_and_superseded_journals_only(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    terminal_record, _ = _write_checkpoint_journal(
        root,
        target_date="2026-08-07",
        result_status="offline_three_arm_execution_complete",
    )
    incomplete_record, _ = _write_checkpoint_journal(
        root,
        target_date="2026-08-06",
        result_status="offline_three_arm_execution_batch_complete",
    )
    superseded_record, _ = _write_checkpoint_journal(
        root,
        target_date="2026-08-05",
        result_status="offline_three_arm_execution_batch_complete",
        result_request_census_hash="b" * 64,
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        retention_days=1,
        apply=True,
    )

    assert result["status"] == "pass"
    artifact_census = result["artifact_set_census"]
    assert artifact_census["set_count"] == 3
    assert artifact_census["terminal_count"] == 1
    assert artifact_census["incomplete_resumable_count"] == 2
    assert artifact_census["stale_workorder_count"] == 2
    census = result["checkpoint_journal_census"]
    assert census["journal_count"] == 3
    assert census["terminal_count"] == 1
    assert census["superseded_count"] == 1
    assert census["incomplete_resumable_count"] == 1
    assert census["stale_workorder_count"] == 1
    assert not terminal_record.exists()
    assert terminal_record.with_suffix(".json.gz").exists()
    assert not superseded_record.exists()
    assert superseded_record.with_suffix(".json.gz").exists()
    assert incomplete_record.exists()
    assert not incomplete_record.with_suffix(".json.gz").exists()
    assert result["deletion_performed"] is False


def test_checkpoint_batch_resume_binds_request_census_not_full_materialized_hash(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    record, checkpoint = _write_checkpoint_journal(
        root,
        target_date="2026-08-24",
        result_status="offline_three_arm_execution_batch_complete",
    )
    manifest = json.loads(checkpoint.read_text(encoding="utf-8"))
    result_path = root / "ai_micro_reversion_three_arm_offline_results_2026-08-24.json"
    execution_result = json.loads(result_path.read_text(encoding="utf-8"))
    assert (
        manifest["materialized_report_content_sha256"]
        == execution_result["materialized_request_census_sha256"]
    )
    assert (
        manifest["materialized_report_content_sha256"]
        != execution_result["materialized_report_content_sha256"]
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 25),
        apply=True,
    )

    assert result["status"] == "pass"
    census = result["checkpoint_journal_census"]
    assert census["incomplete_resumable_count"] == 1
    assert census["superseded_count"] == 0
    assert record.exists()
    assert not record.with_suffix(".json.gz").exists()


@pytest.mark.parametrize(
    "invalid_field",
    (
        "materialized_report_content_sha256",
        "materialized_request_census_sha256",
    ),
)
def test_checkpoint_result_rejects_invalid_materialized_hash_domains(
    tmp_path: Path,
    invalid_field: str,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    record, _ = _write_checkpoint_journal(
        root,
        target_date="2026-08-07",
        result_status="offline_three_arm_execution_batch_complete",
    )
    result_path = root / "ai_micro_reversion_three_arm_offline_results_2026-08-07.json"
    execution_result = json.loads(result_path.read_text(encoding="utf-8"))
    execution_result[invalid_field] = "not-a-sha256"
    result_content = {
        key: value
        for key, value in execution_result.items()
        if key != "report_content_sha256"
    }
    result_path.write_text(
        json.dumps(_with_hash(result_content, "report_content_sha256")) + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert any(
        f"sha256_field_invalid:{invalid_field}" in failure["reason"]
        for failure in result["failures"]
    )
    assert record.exists()
    assert not record.with_suffix(".json.gz").exists()


def test_checkpoint_current_terminal_requires_exact_external_companion_binding(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    record_path, checkpoint_path = _write_checkpoint_journal(
        root,
        target_date="2026-08-24",
        result_status="offline_three_arm_execution_complete",
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    embedded_result = dict(record["result"])
    embedded_result["ablation_design_version"] = (
        storage_maintenance_module.CURRENT_DESIGN_VERSION
    )
    record_content = {
        key: value
        for key, value in record.items()
        if key != "checkpoint_record_content_sha256"
    }
    record_content["result"] = embedded_result
    record_content.update(storage_maintenance_module.CHECKPOINT_RECONSTRUCTED_CONTRACT)
    current_record = _with_hash(
        record_content,
        "checkpoint_record_content_sha256",
    )
    current_record_path = record_path.with_name(
        f"00000001-{current_record['checkpoint_record_content_sha256']}.json"
    )
    current_record_path.write_text(json.dumps(current_record) + "\n", encoding="utf-8")
    record_path.unlink()

    manifest = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    manifest_content = {
        key: value
        for key, value in manifest.items()
        if key != "checkpoint_manifest_content_sha256"
    }
    manifest_content["checkpoint_head_sha256"] = current_record[
        "checkpoint_record_content_sha256"
    ]
    checkpoint_path.write_text(
        json.dumps(_with_hash(manifest_content, "checkpoint_manifest_content_sha256"))
        + "\n",
        encoding="utf-8",
    )

    result_path = root / "ai_micro_reversion_three_arm_offline_results_2026-08-24.json"
    execution = json.loads(result_path.read_text(encoding="utf-8"))
    execution_content = {
        key: value for key, value in execution.items() if key != "report_content_sha256"
    }
    execution_content.update(
        {
            "ablation_design_version": storage_maintenance_module.CURRENT_DESIGN_VERSION,
            "results": [embedded_result],
            "result_ids": [embedded_result["result_id"]],
            "checkpoint_journal_schema": (
                storage_maintenance_module.CHECKPOINT_RECONSTRUCTED_SCHEMA
            ),
            "checkpoint_journal_record_count": 1,
            "checkpoint_journal_head_sha256": current_record[
                "checkpoint_record_content_sha256"
            ],
            "checkpoint_journal_reconstructed_content_sha256": "f" * 64,
        }
    )
    result_path.write_text(
        json.dumps(_with_hash(execution_content, "report_content_sha256")) + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 25),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert any(
        "checkpoint_current_terminal_companion_binding_invalid" in row["reason"]
        for row in result["failures"]
    )
    assert current_record_path.exists()
    assert not current_record_path.with_suffix(".json.gz").exists()


def test_checkpoint_activation_date_cannot_downgrade_current_terminal_design(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    record_path, _ = _write_checkpoint_journal(
        root,
        target_date="2026-08-24",
        result_status="offline_three_arm_execution_complete",
    )
    monkeypatch.setattr(
        storage_maintenance_module,
        "CURRENT_DESIGN_ACTIVATION_DATE",
        "2026-08-24",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 25),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert any(
        "checkpoint_current_terminal_design_required" in row["reason"]
        for row in result["failures"]
    )
    assert record_path.exists()
    assert not record_path.with_suffix(".json.gz").exists()


def _write_provider_budget_ledger(
    root: Path,
    *,
    execution_date: str,
) -> Path:
    ledger = root / f"ai_micro_reversion_provider_budget_{execution_date}.jsonl"
    provider_authority = {
        **_STORAGE_SOURCE_ONLY,
        "provider_route_change_allowed": False,
        "network_call_performed_by_module": False,
    }
    record_content = {
        "schema": "ai_provider_budget_ledger_record_v1",
        "sequence": 1,
        "previous_record_sha256": None,
        "execution_date": execution_date,
        **provider_authority,
    }
    record = _with_hash(record_content, "record_content_sha256")
    ledger_bytes = (json.dumps(record, separators=(",", ":")) + "\n").encode()
    ledger.write_bytes(ledger_bytes)
    ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    manifest_content = {
        "schema": "ai_provider_budget_ledger_manifest_v1",
        "execution_date": execution_date,
        "ledger_file": ledger.name,
        "ledger_size_bytes": len(ledger_bytes),
        "ledger_bytes_sha256": ledger_hash,
        "record_count": 1,
        "head_record_sha256": record["record_content_sha256"],
        **provider_authority,
    }
    ledger.with_suffix(".manifest.json").write_text(
        json.dumps(_with_hash(manifest_content, "manifest_content_sha256")) + "\n",
        encoding="utf-8",
    )
    summary_content = {
        "schema": "ai_provider_budget_summary_v1",
        "execution_date": execution_date,
        "ledger_record_count": 1,
        "ledger_head_sha256": record["record_content_sha256"],
        "ledger_bytes_sha256": ledger_hash,
        **provider_authority,
    }
    ledger.with_suffix(".json").write_text(
        json.dumps(_with_hash(summary_content, "summary_content_sha256")) + "\n",
        encoding="utf-8",
    )
    ledger.with_suffix(".lock").touch()
    return ledger


def _write_current_provider_budget_ledger(
    root: Path,
    *,
    execution_date: str,
) -> Path:
    ledger = root / f"ai_micro_reversion_provider_budget_{execution_date}.jsonl"
    provider_authority = dict(
        storage_maintenance_module.PROVIDER_BUDGET_AUTHORITY_CONTRACT
    )
    budget_contract = {
        "schema": "ai_provider_budget_contract_v1",
        "execution_date": execution_date,
        "daily_attempt_cap": 10,
        "daily_usd_cap": "1",
        "pricing_artifact_content_sha256": "1" * 64,
        "pricing_basis": "operator_accounting_zero_cost",
    }
    budget_contract_sha256 = _provider_canonical_hash(budget_contract)
    attempt_identity = {
        "target_date": execution_date,
        "parent_id": "parent-1",
        "provider": "openai",
        "model": "검증-model",
        "request_id": "request-1",
        "arm": "control",
        "attempt_number": 1,
    }
    attempt_identity_sha256 = _provider_canonical_hash(attempt_identity)
    reservation_id = (
        "provider-reservation-"
        + _provider_canonical_hash(
            {
                "execution_date": execution_date,
                "attempt_identity_sha256": attempt_identity_sha256,
                "pricing_artifact_content_sha256": "1" * 64,
            }
        )[:32]
    )
    common = {
        "budget_contract": budget_contract,
        "budget_contract_sha256": budget_contract_sha256,
        "pricing_artifact_id": "가격-contract",
        "pricing_artifact_content_sha256": "1" * 64,
        "pricing_artifact_file_sha256": "2" * 64,
        "raw_pricing_source_bytes_sha256": "3" * 64,
        "raw_pricing_source_path": "data/가격.json",
        "raw_pricing_source_size_bytes": 100,
        "pricing_effective_from": execution_date,
        "pricing_effective_to": execution_date,
    }
    record_content = {
        "schema": "ai_provider_budget_ledger_record_v1",
        "sequence": 1,
        "previous_record_sha256": None,
        "event_type": "reservation",
        "recorded_at": f"{execution_date}T20:00:00+09:00",
        "execution_date": execution_date,
        "reservation_id": reservation_id,
        "attempt_identity": attempt_identity,
        "attempt_identity_sha256": attempt_identity_sha256,
        "token_ceiling": {
            "input_utf8_bytes": 1,
            "input_token_ceiling": 1,
            "max_output_tokens": 1,
            "total_token_ceiling": 2,
            "estimator": "utf8_bytes_as_input_token_upper_bound_v1",
        },
        "model_pricing": {
            "provider": "openai",
            "model": "검증-model",
            "input_usd_per_million_tokens": "0",
            "output_usd_per_million_tokens": "0",
        },
        "reserved_cost_usd": "0",
        "reservation_status": "reserved_before_provider_call",
        "unknown_or_crashed_call_refund_allowed": False,
        **common,
        **provider_authority,
    }
    record = _with_provider_hash(record_content, "record_content_sha256")
    ledger_bytes = (
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    ledger.write_bytes(ledger_bytes)
    ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    manifest_content = {
        "schema": "ai_provider_budget_ledger_manifest_v1",
        "updated_at": f"{execution_date}T20:00:00+09:00",
        "execution_date": execution_date,
        "ledger_file": ledger.name,
        "ledger_size_bytes": len(ledger_bytes),
        "ledger_bytes_sha256": ledger_hash,
        "record_count": 1,
        "head_record_sha256": record["record_content_sha256"],
        "budget_contract_sha256": budget_contract_sha256,
        **provider_authority,
    }
    ledger.with_suffix(".manifest.json").write_text(
        json.dumps(
            _with_provider_hash(manifest_content, "manifest_content_sha256"),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_content = {
        "schema": "ai_provider_budget_summary_v1",
        "generated_at": f"{execution_date}T20:00:01+09:00",
        "execution_date": execution_date,
        "status": "daily_budget_available",
        "daily_attempt_cap": 10,
        "daily_usd_cap": "1",
        "ledger_record_count": 1,
        "ledger_head_sha256": record["record_content_sha256"],
        "ledger_bytes_sha256": ledger_hash,
        "budget_contract_sha256": budget_contract_sha256,
        "pricing_basis": budget_contract["pricing_basis"],
        **{key: value for key, value in common.items() if key != "budget_contract"},
        "reservation_count": 1,
        "settlement_count": 0,
        "outstanding_reservation_count": 1,
        "actual_cost_usd": "0",
        "outstanding_reserved_cost_usd": "0",
        "committed_cost_usd": "0",
        "remaining_attempt_count": 9,
        "remaining_usd": "1",
        "circuit_breaker_open": False,
        "provider_model_attempt_counts": [
            {
                "provider": attempt_identity["provider"],
                "model": attempt_identity["model"],
                "attempt_count": 1,
            }
        ],
        **provider_authority,
    }
    ledger.with_suffix(".json").write_text(
        json.dumps(
            _with_provider_hash(summary_content, "summary_content_sha256"),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    ledger.with_suffix(".lock").touch()
    return ledger


def test_provider_budget_current_semantics_use_owner_canonical_hash_and_cross_binding(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offline_provider_budget"
    root.mkdir()
    execution_date = date(2026, 8, 25)
    ledger = _write_current_provider_budget_ledger(
        root,
        execution_date=execution_date.isoformat(),
    )

    storage_maintenance_module._validate_provider_budget_ledger(
        ledger,
        execution_date=execution_date,
    )

    summary_path = ledger.with_suffix(".json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["budget_contract_sha256"] = "f" * 64
    summary_content = {
        key: value for key, value in summary.items() if key != "summary_content_sha256"
    }
    summary = _with_provider_hash(summary_content, "summary_content_sha256")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="provider_budget_manifest_summary_contract_binding_invalid",
    ):
        storage_maintenance_module._validate_provider_budget_ledger(
            ledger,
            execution_date=execution_date,
        )


def test_report_artifact_maintenance_compresses_valid_closed_provider_budget_ledger(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offline_provider_budget"
    root.mkdir()
    ledger = _write_provider_budget_ledger(root, execution_date="2026-08-07")
    protected_ledger = _write_provider_budget_ledger(root, execution_date="2026-08-10")
    ledger_bytes = ledger.read_bytes()

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        retention_days=1,
        apply=True,
    )

    assert result["status"] == "pass"
    census = result["provider_budget_ledger_census"]
    assert census["ledger_count"] == 2
    assert census["retention_candidate_count"] == 1
    assert result["provider_runtime_effect"] is False
    assert result["provider_route_change_allowed"] is False
    assert not ledger.exists()
    with gzip.open(ledger.with_suffix(".jsonl.gz"), "rb") as handle:
        assert handle.read() == ledger_bytes
    assert protected_ledger.exists()
    assert not protected_ledger.with_suffix(".jsonl.gz").exists()
    assert any(
        row["action"] == "compress_provider_budget_jsonl" for row in result["actions"]
    )


def test_report_artifact_maintenance_rejects_unbound_provider_budget_ledger(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offline_provider_budget"
    root.mkdir()
    ledger = _write_provider_budget_ledger(root, execution_date="2026-08-07")
    summary_path = ledger.with_suffix(".json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["ledger_bytes_sha256"] = "f" * 64
    content = {
        key: value for key, value in summary.items() if key != "summary_content_sha256"
    }
    summary_path.write_text(
        json.dumps(_with_hash(content, "summary_content_sha256")) + "\n",
        encoding="utf-8",
    )

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["failure_count"] == 1
    assert (
        "provider_budget_summary_ledger_binding_invalid"
        in result["failures"][0]["reason"]
    )
    assert ledger.exists()
    assert not ledger.with_suffix(".jsonl.gz").exists()


def test_report_artifact_maintenance_defers_locked_provider_budget_ledger(
    tmp_path: Path,
) -> None:
    root = tmp_path / "offline_provider_budget"
    root.mkdir()
    ledger = _write_provider_budget_ledger(root, execution_date="2026-08-07")
    lock_handle = ledger.with_suffix(".lock").open("r+b")
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        result = maintain_report_artifact_storage(
            [root],
            as_of_date=date(2026, 8, 10),
            apply=True,
        )
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()

    assert result["status"] == "partial_failure"
    assert "provider_budget_archive_lock_busy" in result["failures"][0]["reason"]
    assert ledger.exists()
    assert not ledger.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_compresses_and_verifies_closed_date(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = '{"value":1}\n{"value":2}\n'
    source.write_text(original, encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    compressed = source.with_suffix(".jsonl.gz")
    assert result["action_count"] == 1
    assert not source.exists()
    with gzip.open(compressed, "rt", encoding="utf-8") as handle:
        assert handle.read() == original


def test_storage_maintenance_preserves_open_closed_date_source_inode(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")
    handle = source.open("a+", encoding="utf-8")
    original_inode = os.fstat(handle.fileno()).st_ino
    try:
        result = maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            storage_policy=PathStoragePolicy(compression_after_days=1),
            apply=True,
        )

        assert result["status"] == "partial_failure"
        assert result["partition_failure_count"] == 1
        assert result["failed_candidate_count"] == 1
        assert "source_open_fd" in result["partition_failures"][0]["reason"]
        assert source.stat().st_ino == original_inode
        assert os.fstat(handle.fileno()).st_nlink == 1
        assert not source.with_suffix(".jsonl.gz").exists()
        handle.write('{"value":2}\n')
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    assert source.read_text(encoding="utf-8") == '{"value":1}\n{"value":2}\n'


def test_storage_maintenance_reports_partial_purge_and_recovers_next_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trade_dir = tmp_path / "trade_date=2026-07-01"
    first = trade_dir / "venue=KRX" / "a.jsonl"
    second = trade_dir / "venue=KRX" / "b.jsonl"
    first.parent.mkdir(parents=True)
    first.write_text("a\n", encoding="utf-8")
    second.write_text("bb\n", encoding="utf-8")
    first_bytes = first.stat().st_size
    second_bytes = second.stat().st_size
    real_rmtree = storage_maintenance_module.shutil.rmtree

    def partial_rmtree(path: Path) -> None:
        assert Path(path) == trade_dir
        first.unlink()
        raise OSError("injected_partial_rmtree_failure")

    monkeypatch.setattr(storage_maintenance_module.shutil, "rmtree", partial_rmtree)
    first_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
        purge_expired=True,
    )

    assert first_result["status"] == "partial_failure"
    assert not first.exists()
    assert second.exists()
    assert first_result["purge_applied_count"] == 0
    assert first_result["purge_partial_applied_count"] == 1
    assert first_result["deletion_performed"] is True
    assert first_result["actions"][0]["action"] == "purge_trade_date_partial"
    assert first_result["actions"][0]["source_bytes"] == first_bytes
    assert first_result["failed_candidate_count"] == 1
    assert first_result["failed_candidate_bytes"] == second_bytes
    assert first_result["recovery_required_count"] == 1

    monkeypatch.setattr(storage_maintenance_module.shutil, "rmtree", real_rmtree)
    second_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
        purge_expired=True,
    )

    assert second_result["status"] == "pass"
    assert second_result["purge_applied_count"] == 1
    assert not trade_dir.exists()


def test_storage_maintenance_isolates_open_group_and_compresses_peer_group(
    tmp_path: Path,
) -> None:
    session_dir = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=KRX_REGULAR"
    )
    session_dir.mkdir(parents=True)
    first_source = session_dir / "a.jsonl"
    open_source = session_dir / "z.jsonl"
    manifest = session_dir / "a.manifest.json"
    first_source.write_text('{"value":"first"}\n', encoding="utf-8")
    open_source.write_text('{"value":"open"}\n', encoding="utf-8")
    manifest_payload = {
        "schema": "scalp_micro_reversion_market_path_manifest_v1",
        "shards": [
            {
                "index": 0,
                "file": first_source.name,
                "bytes": first_source.stat().st_size,
            }
        ],
    }
    manifest.write_text(json.dumps(manifest_payload) + "\n", encoding="utf-8")
    original_bytes = {
        path: path.read_bytes() for path in (first_source, open_source, manifest)
    }
    original_inodes = {
        path: path.stat().st_ino for path in (first_source, open_source, manifest)
    }
    handle = open_source.open("a+", encoding="utf-8")
    try:
        result = maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            storage_policy=PathStoragePolicy(compression_after_days=1),
            apply=True,
        )

        assert result["status"] == "partial_failure"
        assert result["partition_failure_count"] == 1
        assert result["action_count"] == 1
        assert not first_source.exists()
        assert first_source.with_suffix(".jsonl.gz").exists()
        assert open_source.read_bytes() == original_bytes[open_source]
        assert open_source.stat().st_ino == original_inodes[open_source]
        assert not open_source.with_suffix(".jsonl.gz").exists()
        updated_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        assert updated_manifest["shards"][0]["file"] == "a.jsonl.gz"
        assert os.fstat(handle.fileno()).st_nlink == 1
    finally:
        handle.close()


def test_storage_maintenance_preserves_source_changed_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")
    real_assert = storage_maintenance_module._assert_source_unchanged_and_closed
    changed = False

    def assert_with_change(
        path: Path,
        expected: tuple[int, int, int, int, str],
        *,
        phase: str,
    ) -> None:
        nonlocal changed
        if path == source and phase == "before_partition_publish" and not changed:
            changed = True
            with source.open("a", encoding="utf-8") as handle:
                handle.write('{"value":2}\n')
                handle.flush()
                os.fsync(handle.fileno())
        real_assert(path, expected, phase=phase)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_assert_source_unchanged_and_closed",
        assert_with_change,
    )
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert (
        "source_changed_before_partition_publish"
        in result["partition_failures"][0]["reason"]
    )
    assert source.read_text(encoding="utf-8") == '{"value":1}\n{"value":2}\n'
    assert not source.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_repoints_manifest_to_compressed_shard(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")
    manifest = source.with_name("market_stream.manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_market_path_manifest_v1",
                "shards": [
                    {"index": 0, "file": source.name, "bytes": source.stat().st_size}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["shards"][0]["file"] == "market_stream.jsonl.gz"
    assert payload["shards"][0]["compressed"] is True
    assert payload["storage_maintenance_as_of_date"] == "2026-08-10"


def test_storage_maintenance_never_purges_expired_date_without_explicit_opt_in(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
    )

    assert expired.parents[1].exists()
    assert not expired.exists()
    assert expired.with_suffix(".jsonl.gz").exists()
    assert result["purge_enabled"] is False
    assert result["purge_status"] == "disabled_no_deletion_authority"
    assert result["purge_candidate_count"] == 1
    assert result["purge_candidate_bytes"] > 0
    assert result["purge_applied_count"] == 0
    assert result["deletion_performed"] is False
    assert all(row["action"] != "purge_trade_date" for row in result["actions"])


def test_storage_maintenance_purges_only_expired_trade_date_with_explicit_opt_in(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    current = tmp_path / "trade_date=2026-08-10" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    current.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")
    current.write_text("{}\n", encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
        purge_expired=True,
    )

    assert result["action_count"] == 1
    assert not expired.parents[1].exists()
    assert current.exists()
    assert result["purge_enabled"] is True
    assert result["purge_status"] == "explicit_opt_in_apply"
    assert result["purge_candidate_count"] == 1
    assert result["purge_applied_count"] == 1
    assert result["deletion_performed"] is True


def test_storage_maintenance_explicit_purge_preserves_open_tree_file(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")
    handle = expired.open("rb")
    original_inode = os.fstat(handle.fileno()).st_ino
    try:
        result = maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            storage_policy=PathStoragePolicy(retention_days=14),
            apply=True,
            purge_expired=True,
        )

        assert result["status"] == "partial_failure"
        assert result["partition_failure_count"] == 1
        assert result["failed_candidate_count"] == 1
        assert result["failed_candidate_bytes"] == expired.stat().st_size
        assert result["purge_candidate_count"] == 1
        assert result["purge_candidate_bytes"] == expired.stat().st_size
        assert any(
            "source_open_fd" in row["reason"] for row in result["partition_failures"]
        )
        assert expired.stat().st_ino == original_inode
        assert os.fstat(handle.fileno()).st_nlink == 1
        assert expired.parents[1].exists()
    finally:
        handle.close()


def test_storage_maintenance_purge_dry_run_reports_but_does_not_delete(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        purge_expired=True,
    )

    assert expired.exists()
    assert result["mode"] == "dry_run"
    assert result["purge_status"] == "explicit_opt_in_dry_run"
    assert result["purge_applied_count"] == 0
    assert result["deletion_performed"] is False
    assert result["actions"] == [
        {
            "action": "purge_trade_date",
            "path": str(expired.parents[1]),
            "trade_date": "2026-07-01",
            "source_bytes": expired.stat().st_size,
            "applied": False,
        }
    ]


@pytest.mark.parametrize(
    ("apply", "purge_expired"),
    (("true", False), (False, "true")),
)
def test_storage_maintenance_rejects_non_boolean_authority(
    tmp_path: Path,
    apply: object,
    purge_expired: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="storage maintenance authorities must be native booleans",
    ):
        maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            apply=apply,  # type: ignore[arg-type]
            purge_expired=purge_expired,  # type: ignore[arg-type]
        )


def test_storage_maintenance_does_not_follow_nested_symlink(tmp_path: Path) -> None:
    real_session = tmp_path / "real_session"
    real_session.mkdir()
    source = real_session / "market_stream.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    trade_dir = tmp_path / "trade_date=2026-08-08" / "venue=KRX"
    trade_dir.mkdir(parents=True)
    os.symlink(real_session, trade_dir / "session=KRX_REGULAR")
    peer = trade_dir / "session=PEER" / "peer.jsonl"
    peer.parent.mkdir()
    peer.write_text('{"peer":true}\n', encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["partition_failure_count"] == 1
    assert result["failed_candidate_count"] == 1
    assert result["failed_candidate_bytes"] == 0
    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_rejects_fifo_and_continues_peer(tmp_path: Path) -> None:
    blocked = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=BLOCKED"
        / "market_stream.jsonl"
    )
    peer = blocked.parents[1] / "session=PEER" / "peer.jsonl"
    blocked.parent.mkdir(parents=True)
    peer.parent.mkdir()
    os.mkfifo(blocked)
    peer.write_text('{"peer":true}\n', encoding="utf-8")

    started = time.monotonic()
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert time.monotonic() - started < 2
    assert result["status"] == "partial_failure"
    assert blocked.is_fifo()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()
    assert any(
        "unsafe_non_regular_file" in row["reason"]
        for row in result["partition_failures"]
    )


def test_storage_maintenance_isolates_unsafe_trade_date_and_continues_peer(
    tmp_path: Path,
) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-external"
    external.mkdir()
    external_source = external / "outside.jsonl"
    external_source.write_text('{"outside":true}\n', encoding="utf-8")
    os.symlink(external, tmp_path / "trade_date=2026-08-07")
    peer = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=PEER" / "peer.jsonl"
    )
    peer.parent.mkdir(parents=True)
    peer.write_text('{"peer":true}\n', encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert any(
        row["trade_date"] == "2026-08-07" for row in result["partition_failures"]
    )
    assert external_source.exists()
    assert not external_source.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_rejects_future_apply_and_protects_runtime_date(
    tmp_path: Path,
) -> None:
    runtime_trade_date = datetime.now(ZoneInfo("Asia/Seoul")).date()
    source = (
        tmp_path
        / f"trade_date={runtime_trade_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="storage maintenance as-of date must not be in the future",
    ):
        maintain_forward_storage(
            tmp_path,
            as_of_date=runtime_trade_date + timedelta(days=1),
            storage_policy=PathStoragePolicy(compression_after_days=1),
            apply=True,
        )

    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_recovers_interrupted_source_unlink(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = '{"value":1}\n'
    source.write_text(original, encoding="utf-8")
    compressed = source.with_suffix(".jsonl.gz")
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write(original)

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["actions"][0]["action"] == "finalize_verified_compression"
    assert not source.exists()
    with gzip.open(compressed, "rt", encoding="utf-8") as handle:
        assert handle.read() == original


def test_storage_maintenance_repairs_manifest_after_interrupted_refresh(
    tmp_path: Path,
) -> None:
    compressed = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl.gz"
    )
    compressed.parent.mkdir(parents=True)
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write('{"value":1}\n')
    manifest = compressed.with_name("market_stream.manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_market_path_manifest_v1",
                "shards": [
                    {
                        "index": 0,
                        "file": "market_stream.jsonl",
                        "bytes": 12,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    original_manifest = manifest.read_bytes()

    dry_run = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
    )

    assert dry_run["action_count"] == 1
    assert dry_run["source_bytes"] == manifest.stat().st_size
    assert dry_run["actions"] == [
        {
            "action": "repair_manifest_reference",
            "path": str(manifest),
            "trade_date": "2026-08-08",
            "source_bytes": manifest.stat().st_size,
            "applied": False,
        }
    ]
    assert manifest.read_bytes() == original_manifest

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert result["action_count"] == 1
    assert result["actions"][0]["action"] == "repair_manifest_reference"
    assert payload["shards"][0]["file"] == "market_stream.jsonl.gz"
    assert payload["shards"][0]["compressed"] is True


def test_storage_maintenance_reports_partial_unlink_and_preserves_claim_next_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=KRX_REGULAR"
    session.mkdir(parents=True)
    first = session / "stream.jsonl"
    second = session / "stream.part-000001.jsonl"
    first.write_text('{"row":1}\n', encoding="utf-8")
    second.write_text('{"row":2}\n', encoding="utf-8")
    manifest = session / "stream.manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "shards": [
                    {"index": 0, "file": first.name, "bytes": first.stat().st_size},
                    {
                        "index": 1,
                        "file": second.name,
                        "bytes": second.stat().st_size,
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    real_unlink = Path.unlink

    def fail_second_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path.name == second.name and ".storage-unlink-claim." in path.parent.name:
            raise OSError("injected_second_unlink_failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_second_unlink)
    first_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert first_result["status"] == "partial_failure"
    assert first_result["recovery_required_count"] == 1
    assert first_result["failed_candidate_count"] == 1
    assert first_result["failed_candidate_bytes"] == second.stat().st_size
    assert first_result["action_count"] == 3
    assert not first.exists()
    assert first.with_suffix(".jsonl.gz").exists()
    assert second.exists()
    assert second.with_suffix(".jsonl.gz").exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert all(row["file"].endswith(".gz") for row in manifest_payload["shards"])
    recovery_claims = list(
        second.parent.glob(f".{second.name}.storage-unlink-claim.*/*")
    )
    assert len(recovery_claims) == 1
    recovery_inode = recovery_claims[0].stat().st_ino

    monkeypatch.setattr(Path, "unlink", real_unlink)
    second_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second_result["status"] == "partial_failure"
    assert second_result["action_count"] == 0
    assert second_result["recovery_required_count"] == 1
    assert "storage_unlink_claim_recovery_required" in (
        second_result["partition_failures"][0]["reason"]
    )
    assert second.exists()
    assert recovery_claims[0].stat().st_ino == recovery_inode


def test_storage_maintenance_never_unlinks_raced_replacement_inode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = b'{"generation":"validated"}\n'
    replacement = b'{"generation":"historical-repair"}\n'
    source.write_bytes(original)
    real_claim = storage_maintenance_module._claim_source_for_verified_unlink
    replacement_inode = 0

    def replace_immediately_before_claim(
        path: Path,
        expected: tuple[int, int, int, int, str],
    ) -> tuple[Path, Path]:
        nonlocal replacement_inode
        if path == source:
            staged = source.with_name(f".{source.name}.producer-replacement")
            staged.write_bytes(replacement)
            os.replace(staged, source)
            replacement_inode = source.stat().st_ino
        return real_claim(path, expected)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_claim_source_for_verified_unlink",
        replace_immediately_before_claim,
    )
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    target = source.with_suffix(".jsonl.gz")
    claims = list(source.parent.glob(f".{source.name}.storage-unlink-claim.*/*"))
    assert result["status"] == "partial_failure"
    assert "source_inode_replaced_before_verified_claim" in (
        result["partition_failures"][0]["reason"]
    )
    assert result["recovery_required_count"] == 1
    assert source.read_bytes() == replacement
    assert source.stat().st_ino == replacement_inode
    assert len(claims) == 1
    assert claims[0].read_bytes() == replacement
    assert claims[0].stat().st_ino == replacement_inode
    with gzip.open(target, "rb") as handle:
        assert handle.read() == original


def test_storage_maintenance_preserves_claim_when_source_is_recreated_before_unlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = b'{"generation":"validated"}\n'
    replacement = b'{"generation":"late-sidecar-repair"}\n'
    source.write_bytes(original)
    real_absence_check = (
        storage_maintenance_module._assert_source_path_absent_after_claim
    )
    replacement_created = False

    def recreate_before_unlink(path: Path, *, phase: str) -> None:
        nonlocal replacement_created
        if (
            path == source
            and phase == "before_verified_claim_unlink"
            and not replacement_created
        ):
            source.write_bytes(replacement)
            replacement_created = True
        real_absence_check(path, phase=phase)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_assert_source_path_absent_after_claim",
        recreate_before_unlink,
    )
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    target = source.with_suffix(".jsonl.gz")
    claims = list(source.parent.glob(f".{source.name}.storage-unlink-claim.*/*"))
    assert result["status"] == "partial_failure"
    assert "source_path_recreated_before_verified_claim_unlink" in (
        result["partition_failures"][0]["reason"]
    )
    assert result["recovery_required_count"] == 1
    assert source.read_bytes() == replacement
    assert len(claims) == 1
    assert claims[0].read_bytes() == original
    with gzip.open(target, "rb") as handle:
        assert handle.read() == original

    claim_inode = claims[0].stat().st_ino
    claim_bytes = claims[0].read_bytes()
    monkeypatch.setattr(
        storage_maintenance_module,
        "_assert_source_path_absent_after_claim",
        real_absence_check,
    )
    second = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second["status"] == "partial_failure"
    assert any(
        "storage_unlink_claim_recovery_required" in row["reason"]
        for row in second["partition_failures"]
    )
    assert claims[0].stat().st_ino == claim_inode
    assert claims[0].read_bytes() == claim_bytes


def test_storage_maintenance_preserves_verified_gzip_custody_on_target_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = b'{"generation":"validated"}\n'
    replacement = b"not-a-valid-gzip"
    source.write_bytes(original)
    target = source.with_suffix(".jsonl.gz")
    real_absence_check = (
        storage_maintenance_module._assert_source_path_absent_after_claim
    )
    swapped = False

    def swap_target_before_source_unlink(path: Path, *, phase: str) -> None:
        nonlocal swapped
        if path == source and phase == "before_verified_claim_unlink" and not swapped:
            target.unlink()
            target.write_bytes(replacement)
            swapped = True
        real_absence_check(path, phase=phase)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_assert_source_path_absent_after_claim",
        swap_target_before_source_unlink,
    )
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    custodies = list(source.parent.glob(f".{target.name}.storage-target-custody.*/*"))
    assert result["status"] == "partial_failure"
    assert result["recovery_required_count"] == 1
    assert target.read_bytes() == replacement
    assert len(custodies) == 1
    with gzip.open(custodies[0], "rb") as handle:
        assert handle.read() == original


def test_report_artifact_maintenance_surfaces_orphaned_custody(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    custody = root / ".artifact.json.storage-target-custody.crash"
    custody.mkdir(parents=True)
    (custody / "artifact.json.gz").write_bytes(gzip.compress(b'{"value":1}\n'))

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date(2026, 8, 10),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["failure_count"] == 1
    assert result["failures"][0]["recovery_required"] == "true"
    assert "storage_custody_recovery_required" in result["failures"][0]["reason"]
    assert custody.exists()


def test_report_artifact_compactor_defers_busy_generation_lock(
    tmp_path: Path,
) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    artifact = root / "ai_prompt_paired_replay_2026-08-08.json"
    artifact.write_text(
        json.dumps(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": "2026-08-08",
                **_STORAGE_SOURCE_ONLY,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with storage_maintenance_module.json_artifact_generation_lock(artifact):
        result = maintain_report_artifact_storage(
            [root],
            as_of_date=date(2026, 8, 10),
            apply=True,
        )

    assert result["status"] == "partial_failure"
    assert any(
        "json_generation_lock_busy" in row["reason"] for row in result["failures"]
    )
    assert artifact.exists()
    assert not artifact.with_suffix(".json.gz").exists()


def test_storage_maintenance_fsyncs_both_directories_after_source_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")
    real_fsync_directory = storage_maintenance_module._fsync_directory
    fsync_paths: list[Path] = []

    def record_fsync(path: Path) -> None:
        fsync_paths.append(path)
        real_fsync_directory(path)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_fsync_directory",
        record_fsync,
    )
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    claim_fsync_indices = [
        index
        for index, path in enumerate(fsync_paths)
        if ".storage-unlink-claim." in path.name
    ]
    assert result["status"] == "pass"
    assert len(claim_fsync_indices) == 2
    assert fsync_paths[claim_fsync_indices[0] - 1] == source.parent
    assert fsync_paths[claim_fsync_indices[-1] + 1] == source.parent


def test_storage_maintenance_rejects_external_gzip_symlink_before_source_unlink(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    payload = b'{"row":1}\n'
    source.write_bytes(payload)
    external = tmp_path.parent / f"{tmp_path.name}-external.gz"
    external.write_bytes(gzip.compress(payload, mtime=0))
    original_external = external.read_bytes()
    target = source.with_suffix(".jsonl.gz")
    target.symlink_to(external)

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert source.read_bytes() == payload
    assert target.is_symlink()
    assert external.read_bytes() == original_external
    assert result["action_count"] == 0
    assert any("symlink" in row["reason"] for row in result["partition_failures"])


def test_storage_maintenance_reports_gzip_published_before_directory_fsync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"row":1}\n', encoding="utf-8")
    source_bytes = source.stat().st_size
    real_fsync_directory = storage_maintenance_module._fsync_directory
    call_count = 0

    def fail_first_directory_fsync(path: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("injected_publish_directory_fsync_failure")
        real_fsync_directory(path)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_fsync_directory",
        fail_first_directory_fsync,
    )
    first = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    target = source.with_suffix(".jsonl.gz")
    assert first["status"] == "partial_failure"
    assert source.exists()
    assert target.exists()
    assert first["action_count"] == 1
    assert first["actions"][0]["action"] == ("publish_verified_gzip_source_preserved")
    assert first["failed_candidate_count"] == 1
    assert first["failed_candidate_bytes"] == source_bytes
    assert first["partition_failures"][0]["published_target_count"] == "1"
    assert first["recovery_required_count"] == 1

    monkeypatch.setattr(
        storage_maintenance_module,
        "_fsync_directory",
        real_fsync_directory,
    )
    second = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second["status"] == "pass"
    assert not source.exists()
    assert second["actions"][0]["action"] == "finalize_verified_compression"


def test_storage_maintenance_isolates_invalid_manifest_group(
    tmp_path: Path,
) -> None:
    blocked_session = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=BLOCKED"
    )
    peer_session = blocked_session.with_name("session=PEER")
    blocked_session.mkdir(parents=True)
    peer_session.mkdir(parents=True)
    blocked = blocked_session / "a.jsonl"
    peer = peer_session / "z.jsonl"
    blocked.write_text('{"row":"blocked"}\n', encoding="utf-8")
    peer.write_text('{"row":"peer"}\n', encoding="utf-8")
    (blocked_session / "a.manifest.json").write_text("{malformed", encoding="utf-8")
    (peer_session / "z.manifest.json").write_text(
        json.dumps(
            {"shards": [{"index": 0, "file": peer.name, "bytes": peer.stat().st_size}]}
        )
        + "\n",
        encoding="utf-8",
    )

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["partition_failure_count"] >= 1
    assert blocked.exists()
    assert not blocked.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_rejects_overlapping_manifest_ownership_before_mutation(
    tmp_path: Path,
) -> None:
    conflict_session = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=CONFLICT"
    )
    peer_session = conflict_session.with_name("session=PEER")
    conflict_session.mkdir(parents=True)
    peer_session.mkdir(parents=True)
    source = conflict_session / "market_stream.jsonl"
    source.write_text('{"row":"conflict"}\n', encoding="utf-8")
    manifests = (
        conflict_session / "a.manifest.json",
        conflict_session / "b.manifest.json",
    )
    payload = {
        "shards": [{"index": 0, "file": source.name, "bytes": source.stat().st_size}]
    }
    for manifest in manifests:
        manifest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    peer = peer_session / "peer.jsonl"
    peer.write_text('{"row":"peer"}\n', encoding="utf-8")
    peer_manifest = peer_session / "peer.manifest.json"
    peer_manifest.write_text(
        json.dumps(
            {"shards": [{"index": 0, "file": peer.name, "bytes": peer.stat().st_size}]}
        )
        + "\n",
        encoding="utf-8",
    )
    original = {path: path.read_bytes() for path in (source, *manifests)}

    first = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert first["status"] == "partial_failure"
    assert any(
        "multiple manifests claim one shard" in row["reason"]
        for row in first["partition_failures"]
    )
    assert {path: path.read_bytes() for path in (source, *manifests)} == original
    assert not source.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()

    second = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second["status"] == "partial_failure"
    assert {path: path.read_bytes() for path in (source, *manifests)} == original
    assert not source.with_suffix(".jsonl.gz").exists()


def test_source_exclusion_purge_dry_run_preserves_exact_scope(tmp_path: Path) -> None:
    stream, references, depth, _ = _write_exclusion_partition(
        tmp_path,
        trade_date="2026-08-10",
    )
    exclusion = tmp_path / "exclusions.json"
    _write_source_exclusion_fixture(exclusion, trade_date="2026-08-10")
    original = {path: path.read_bytes() for path in (stream, references, depth)}

    result = purge_excluded_forward_scopes(
        tmp_path,
        source_exclusion_manifest_path=exclusion,
        runtime_trade_date=date(2026, 8, 11),
    )

    assert result["status"] == "pass"
    assert result["mode"] == "dry_run"
    assert result["stream_rows_removed"] == 1
    assert result["event_reference_rows_removed"] == 1
    assert result["deletion_performed"] is False
    assert {path: path.read_bytes() for path in original} == original


def test_source_exclusion_purge_removes_only_manifest_epoch(tmp_path: Path) -> None:
    stream, references, depth, manifest = _write_exclusion_partition(
        tmp_path,
        trade_date="2026-08-10",
    )
    exclusion = tmp_path / "exclusions.json"
    _write_source_exclusion_fixture(exclusion, trade_date="2026-08-10")
    depth_before = depth.read_bytes()

    result = purge_excluded_forward_scopes(
        tmp_path,
        source_exclusion_manifest_path=exclusion,
        apply=True,
        runtime_trade_date=date(2026, 8, 11),
    )

    assert result["status"] == "pass"
    assert result["deletion_performed"] is True
    with gzip.open(stream, "rt", encoding="utf-8") as handle:
        assert [json.loads(line)["sequence_epoch"] for line in handle] == [456]
    with gzip.open(references, "rt", encoding="utf-8") as handle:
        assert [json.loads(line)["sequence_epoch"] for line in handle] == [456]
    assert depth.read_bytes() == depth_before
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["shards"][0]["file"] == stream.name
    assert payload["shards"][0]["bytes"] == stream.stat().st_size
    assert not list(stream.parent.glob("*.source-exclusion-backup"))
    assert not list(stream.parent.glob("*.source-exclusion.tmp"))


def test_source_exclusion_purge_count_mismatch_is_fail_closed(tmp_path: Path) -> None:
    stream, references, depth, manifest = _write_exclusion_partition(
        tmp_path,
        trade_date="2026-08-10",
    )
    exclusion = tmp_path / "exclusions.json"
    _write_source_exclusion_fixture(
        exclusion,
        trade_date="2026-08-10",
        stream_rows=2,
    )
    original = {
        path: path.read_bytes() for path in (stream, references, depth, manifest)
    }

    result = purge_excluded_forward_scopes(
        tmp_path,
        source_exclusion_manifest_path=exclusion,
        apply=True,
        runtime_trade_date=date(2026, 8, 11),
    )

    assert result["status"] == "partial_failure"
    assert result["deletion_performed"] is False
    assert "excluded stream row count mismatch" in result["failures"][0]["reason"]
    assert {path: path.read_bytes() for path in original} == original


def test_source_exclusion_purge_rejects_current_trade_date(tmp_path: Path) -> None:
    stream, references, depth, manifest = _write_exclusion_partition(
        tmp_path,
        trade_date="2026-08-10",
    )
    exclusion = tmp_path / "exclusions.json"
    _write_source_exclusion_fixture(exclusion, trade_date="2026-08-10")
    original = {
        path: path.read_bytes() for path in (stream, references, depth, manifest)
    }

    result = purge_excluded_forward_scopes(
        tmp_path,
        source_exclusion_manifest_path=exclusion,
        apply=True,
        runtime_trade_date=date(2026, 8, 10),
    )

    assert result["status"] == "partial_failure"
    assert result["deletion_performed"] is False
    assert (
        "current_or_future_trade_date_purge_forbidden"
        in result["failures"][0]["reason"]
    )
    assert {path: path.read_bytes() for path in original} == original


def test_source_exclusion_purge_rolls_back_files_when_manifest_refresh_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream, references, depth, manifest = _write_exclusion_partition(
        tmp_path,
        trade_date="2026-08-10",
    )
    exclusion = tmp_path / "exclusions.json"
    _write_source_exclusion_fixture(exclusion, trade_date="2026-08-10")
    original = {
        path: path.read_bytes() for path in (stream, references, depth, manifest)
    }

    def fail_manifest_refresh(*args: object, **kwargs: object) -> None:
        raise OSError("injected_manifest_refresh_failure")

    monkeypatch.setattr(
        storage_maintenance_module,
        "_refresh_manifest_current_bytes",
        fail_manifest_refresh,
    )
    result = purge_excluded_forward_scopes(
        tmp_path,
        source_exclusion_manifest_path=exclusion,
        apply=True,
        runtime_trade_date=date(2026, 8, 11),
    )

    assert result["status"] == "partial_failure"
    assert result["deletion_performed"] is False
    assert "injected_manifest_refresh_failure" in result["failures"][0]["reason"]
    assert {path: path.read_bytes() for path in original} == original
    assert not list(stream.parent.glob("*.source-exclusion-backup"))
    assert not list(stream.parent.glob("*.source-exclusion.tmp"))


def test_current_r3_storage_requires_exact_r2_artifact_binding(
    tmp_path: Path,
) -> None:
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle

    root = tmp_path / "current-r2-r3"
    root.mkdir()
    target_date = storage_maintenance_module.CURRENT_DESIGN_ACTIVATION_DATE
    floor_bindings: list[dict[str, object]] = []
    floor_sha256 = cycle._sha256(floor_bindings)
    rolling_body = {
        "schema": cycle.ROLLING_SCHEMA,
        "target_date": target_date,
        "status": "no_joined_lifecycle_rows",
        "provider_ablation_floor_bindings": floor_bindings,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        "global_candidate_blockers": [],
        "current_run_global_blockers": [],
        "current_run_global_blockers_sha256": cycle._sha256([]),
        "blocked_pre_clear_candidate_count": 0,
        "partitions": [],
        **cycle.OFFLINE_AUTHORITY,
    }
    rolling = _with_hash(rolling_body, "artifact_content_sha256")
    rolling_path = root / f"main_ai_quality_rolling_paired_{target_date}.json"
    rolling_path.write_text(json.dumps(rolling) + "\n", encoding="utf-8")

    manifest_body = {
        "schema": cycle.R3_SCHEMA,
        "target_date": target_date,
        "status": "no_source_only_candidate_passed_all_gates",
        "source_rolling_artifact_sha256": "f" * 64,
        "source_provider_ablation_floor_bindings_sha256": floor_sha256,
        "source_current_run_global_blockers_sha256": cycle._sha256([]),
        "candidate_count": 0,
        "candidates": [],
        "global_candidate_blockers": [],
        "blocked_pre_clear_candidate_count": 0,
        "first_runtime_candidate_auto_apply_performed": False,
        **cycle.OFFLINE_AUTHORITY,
    }
    manifest_path = root / f"main_ai_quality_r3_source_candidates_{target_date}.json"
    manifest_path.write_text(
        json.dumps(_with_hash(manifest_body, "artifact_content_sha256")) + "\n",
        encoding="utf-8",
    )

    invalid = maintain_report_artifact_storage(
        [root],
        as_of_date=date.fromisoformat(target_date) + timedelta(days=1),
    )

    assert invalid["status"] == "partial_failure"
    assert (
        "current_r2_r3_exact_artifact_binding_invalid"
        in invalid["failures"][0]["reason"]
    )

    bound_manifest_body = {
        **manifest_body,
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
    }
    manifest_path.write_text(
        json.dumps(_with_hash(bound_manifest_body, "artifact_content_sha256")) + "\n",
        encoding="utf-8",
    )
    valid = maintain_report_artifact_storage(
        [root],
        as_of_date=date.fromisoformat(target_date) + timedelta(days=1),
    )

    assert valid["status"] == "pass"
    assert valid["failure_count"] == 0

    fabricated_content = {
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        **cycle.OFFLINE_AUTHORITY,
    }
    fabricated_sha256 = cycle._sha256(fabricated_content)
    fabricated = {
        "candidate_id": f"main-ai-quality-{fabricated_sha256[:24]}",
        "candidate_sha256": fabricated_sha256,
        **fabricated_content,
    }
    fabricated_manifest_body = {
        **bound_manifest_body,
        "status": "source_only_candidates_ready",
        "candidate_count": 1,
        "candidates": [fabricated],
    }
    manifest_path.write_text(
        json.dumps(_with_hash(fabricated_manifest_body, "artifact_content_sha256"))
        + "\n",
        encoding="utf-8",
    )

    fabricated_result = maintain_report_artifact_storage(
        [root],
        as_of_date=date.fromisoformat(target_date) + timedelta(days=1),
    )

    assert fabricated_result["status"] == "partial_failure"
    assert "r3_manifest_candidate_projection_mismatch" in (
        fabricated_result["failures"][0]["reason"]
    )


def test_economic_artifacts_compress_closed_date_keep_current_and_remain_loadable(
    tmp_path: Path,
) -> None:
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle

    root = tmp_path / "micro_reversion_economic_reference"
    root.mkdir()
    closed_date = "2026-08-24"
    current_date = "2026-08-25"

    def payloads(target_date: str) -> dict[str, dict[str, object]]:
        economic = _with_hash(
            {
                "schema": "micro_reversion_economic_reference_daily_resolution_v2",
                "target_date": target_date,
                **_STORAGE_SOURCE_ONLY,
            },
            "artifact_content_sha256",
        )
        cost = _with_hash(
            {
                "schema": "micro_reversion_reviewed_cost_catalog_v2",
                "target_date": target_date,
                **_STORAGE_SOURCE_ONLY,
            },
            "content_sha256",
        )
        master = _with_hash(
            {
                "schema": "scalp_micro_reversion_symbol_master_v1",
                "artifact_id": (
                    f"main-ai-economic-reference-{target_date}-symbol-master"
                ),
                **_STORAGE_SOURCE_ONLY,
            },
            "content_sha256",
        )
        return {
            f"micro_reversion_economic_reference_{target_date}.json": economic,
            f"micro_reversion_reviewed_cost_profile_{target_date}.json": cost,
            f"micro_reversion_symbol_master_{target_date}.json": master,
        }

    all_payloads = {
        **payloads(closed_date),
        **payloads(current_date),
    }
    for file_name, payload in all_payloads.items():
        (root / file_name).write_text(json.dumps(payload) + "\n", encoding="utf-8")

    result = maintain_report_artifact_storage(
        [root],
        as_of_date=date.fromisoformat(current_date),
        apply=True,
    )

    assert result["status"] == "pass"
    assert result["compressed_count"] == 3
    for file_name, payload in all_payloads.items():
        logical = root / file_name
        if closed_date in file_name:
            assert not logical.exists()
            assert logical.with_suffix(".json.gz").exists()
        else:
            assert logical.exists()
            assert not logical.with_suffix(".json.gz").exists()
        assert cycle._load_json_auto(logical) == payload


def _write_exact_ai_storage_fixture(
    root: Path,
    *,
    root_name: str,
    target_date: str,
) -> tuple[Path, bytes]:
    contracts = {
        "ai_decision_payloads": (
            "ai_decision_payloads",
            "ai_decision_payload_v1",
            "captured_at",
            "jsonl",
        ),
        "ai_decision_trace": (
            "ai_decision_trace",
            "ai_decision_trace_v1",
            "decision_ts",
            "jsonl",
        ),
        "ai_decision_outcomes": (
            "ai_decision_outcomes",
            "ai_decision_outcome_label_v1",
            "created_at",
            "jsonl",
        ),
        "ai_decision_requests": (
            "ai_decision_requests",
            "ai_decision_request_provenance_v1",
            "captured_at",
            "jsonl",
        ),
        "ai_decision_prompts": (
            "ai_decision_prompts",
            "ai_decision_prompt_v1",
            "captured_at",
            "jsonl",
        ),
        "ai_decision_outcome_labels": (
            "ai_decision_outcome_labels",
            "ai_decision_outcome_labels_v1",
            "target_date",
            "json",
        ),
    }
    prefix, schema, date_field, kind = contracts[root_name]
    root.mkdir(parents=True, exist_ok=True)
    suffix = ".jsonl" if kind == "jsonl" else ".json"
    path = root / f"{prefix}_{target_date}{suffix}"
    payload = {
        "schema": schema,
        date_field: (
            target_date
            if date_field == "target_date"
            else f"{target_date}T20:00:00+09:00"
        ),
        **({"labels": []} if kind == "json" else {}),
    }
    raw = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return path, raw


def test_exact_ai_storage_compresses_all_six_closed_roots_and_protects_current(
    tmp_path: Path,
) -> None:
    closed_date = "2026-08-24"
    current_date = "2026-08-25"
    root_names = tuple(storage_maintenance_module.EXACT_AI_ARTIFACT_ROOT_CONTRACTS)
    roots: list[Path] = []
    fixtures: list[tuple[Path, bytes]] = []
    current_paths: list[Path] = []
    for root_name in root_names:
        root = tmp_path / root_name
        roots.append(root)
        fixtures.append(
            _write_exact_ai_storage_fixture(
                root,
                root_name=root_name,
                target_date=closed_date,
            )
        )
        current_path, _ = _write_exact_ai_storage_fixture(
            root,
            root_name=root_name,
            target_date=current_date,
        )
        current_paths.append(current_path)

    result = maintain_report_artifact_storage(
        [],
        as_of_date=date.fromisoformat(current_date),
        apply=True,
        exact_ai_artifact_roots=roots,
        low_disk_watermark_bytes=0,
        critical_disk_watermark_bytes=0,
    )

    exact = result["exact_ai_artifact_maintenance"]
    assert result["status"] == "pass"
    assert exact["artifact_count"] == 12
    assert exact["compressed_count"] == 6
    assert exact["protected_artifact_count"] == 6
    assert exact["deletion_performed"] is False
    assert exact["archive_offload_performed"] is False
    for logical, raw in fixtures:
        assert not logical.exists()
        with gzip.open(logical.with_suffix(f"{logical.suffix}.gz"), "rb") as handle:
            assert handle.read() == raw
    for current_path in current_paths:
        assert current_path.exists()
        assert not current_path.with_suffix(f"{current_path.suffix}.gz").exists()


def test_exact_ai_storage_rejects_dual_mismatch_and_busy_writer_lock(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ai_decision_trace"
    logical, raw = _write_exact_ai_storage_fixture(
        root,
        root_name="ai_decision_trace",
        target_date="2026-08-23",
    )
    compressed = logical.with_suffix(".jsonl.gz")
    compressed.write_bytes(gzip.compress(raw.replace(b"20:00:00", b"20:00:01")))

    mismatch = maintain_report_artifact_storage(
        [],
        as_of_date=date(2026, 8, 25),
        apply=True,
        exact_ai_artifact_roots=[root],
        low_disk_watermark_bytes=0,
        critical_disk_watermark_bytes=0,
    )

    assert mismatch["status"] == "partial_failure"
    assert mismatch["exact_ai_artifact_maintenance"]["failure_count"] == 1
    assert "jsonl_artifact_plain_gzip_conflict" in mismatch["failures"][0]["reason"]
    assert logical.read_bytes() == raw
    compressed.unlink()

    with storage_maintenance_module.jsonl_artifact_generation_lock(logical):
        locked = maintain_report_artifact_storage(
            [],
            as_of_date=date(2026, 8, 25),
            apply=True,
            exact_ai_artifact_roots=[root],
            low_disk_watermark_bytes=0,
            critical_disk_watermark_bytes=0,
        )

    assert locked["status"] == "partial_failure"
    assert "jsonl_generation_lock_busy" in locked["failures"][0]["reason"]
    assert logical.read_bytes() == raw
    assert not compressed.exists()


def test_exact_ai_storage_rejects_symlink_without_touching_external_source(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ai_decision_requests"
    root.mkdir()
    external = tmp_path / "external.jsonl"
    external.write_text(
        json.dumps(
            {
                "schema": "ai_decision_request_provenance_v1",
                "captured_at": "2026-08-23T20:00:00+09:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logical = root / "ai_decision_requests_2026-08-23.jsonl"
    logical.symlink_to(external)

    result = maintain_report_artifact_storage(
        [],
        as_of_date=date(2026, 8, 25),
        apply=True,
        exact_ai_artifact_roots=[root],
        low_disk_watermark_bytes=0,
        critical_disk_watermark_bytes=0,
    )

    assert result["status"] == "partial_failure"
    assert "exact AI artifact symlink forbidden" in result["failures"][0]["reason"]
    assert logical.is_symlink()
    assert external.exists()


def test_exact_ai_storage_parent_replacement_cannot_touch_replacement_generation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "ai_decision_trace"
    replaced_root = tmp_path / "ai_decision_trace-replaced"
    logical, _ = _write_exact_ai_storage_fixture(
        root,
        root_name="ai_decision_trace",
        target_date="2026-08-23",
    )
    replacement_bytes = b"replacement generation must remain untouched\n"
    original_compress = storage_maintenance_module._compress_group_verified
    replaced = False

    def replace_parent_then_compress(*args, **kwargs):
        nonlocal replaced
        if not replaced:
            replaced = True
            root.rename(replaced_root)
            root.mkdir()
            (root / logical.name).write_bytes(replacement_bytes)
        return original_compress(*args, **kwargs)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_compress_group_verified",
        replace_parent_then_compress,
    )

    result = maintain_report_artifact_storage(
        [],
        as_of_date=date(2026, 8, 25),
        apply=True,
        exact_ai_artifact_roots=[root],
        low_disk_watermark_bytes=0,
        critical_disk_watermark_bytes=0,
    )

    replacement = root / logical.name
    assert result["status"] == "partial_failure"
    assert "jsonl_generation_parent_changed" in result["failures"][-1]["reason"]
    assert replacement.read_bytes() == replacement_bytes
    assert not replacement.with_suffix(".jsonl.gz").exists()
    assert not (replaced_root / logical.name).exists()
    assert (replaced_root / f"{logical.name}.gz").exists()


def test_exact_ai_storage_rejects_runtime_date_gzip_without_mutation(
    tmp_path: Path,
) -> None:
    runtime_date = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    root = tmp_path / "ai_decision_prompts"
    logical, raw = _write_exact_ai_storage_fixture(
        root,
        root_name="ai_decision_prompts",
        target_date=runtime_date,
    )
    compressed = logical.with_suffix(".jsonl.gz")
    compressed.write_bytes(gzip.compress(raw))
    logical.unlink()
    stored_gzip = compressed.read_bytes()

    result = maintain_report_artifact_storage(
        [],
        as_of_date=date.fromisoformat(runtime_date),
        apply=True,
        exact_ai_artifact_roots=[root],
        low_disk_watermark_bytes=0,
        critical_disk_watermark_bytes=0,
    )

    assert result["status"] == "partial_failure"
    assert "runtime_date_exact_ai_gzip_generation_forbidden" in (
        result["failures"][0]["reason"]
    )
    assert not logical.exists()
    assert compressed.read_bytes() == stored_gzip


def test_micro_reversion_daily_owner_is_census_only_with_retention_owner_open(
    tmp_path: Path,
) -> None:
    root = tmp_path / "daily"
    old_partition = root / "2026-05-01"
    current_partition = root / "2026-08-25"
    old_partition.mkdir(parents=True)
    current_partition.mkdir(parents=True)
    old_file = old_partition / "symbol_product_master.json"
    current_file = current_partition / "symbol_product_master.json"
    old_file.write_bytes(b'{"generation":"old"}\n')
    current_file.write_bytes(b'{"generation":"current"}\n')

    result = maintain_report_artifact_storage(
        [],
        as_of_date=date(2026, 8, 25),
        apply=True,
        micro_reversion_daily_owner_root=root,
        retention_days=90,
        low_disk_watermark_bytes=0,
        critical_disk_watermark_bytes=0,
    )

    census = result["micro_reversion_daily_owner_census"]
    assert result["status"] == "pass"
    assert census["partition_count"] == 2
    assert census["file_count"] == 2
    assert census["exact_date_file_count"] == 1
    assert census["exact_date_bytes"] == len(current_file.read_bytes())
    assert census["retention_candidate_count"] == 1
    assert census["retention_candidate_bytes"] == len(old_file.read_bytes())
    assert census["automatic_compression_authorized"] is False
    assert census["automatic_deletion_authorized"] is False
    assert census["archive_offload_authorized"] is False
    assert census["durable_archive_offload_owner_status"] == (
        "open_owner_required_no_automatic_archive_offload_or_deletion"
    )
    assert old_file.exists()
    assert current_file.exists()
