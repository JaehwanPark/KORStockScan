from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from src.engine.scalping import entry_split_monitor_projection as projection
from src.engine.scalping import entry_split_order_plan as native

DAY = "2026-09-04"


@pytest.fixture
def pair(tmp_path, monkeypatch):
    root = tmp_path / "data"
    root.mkdir()
    monkeypatch.setattr(projection, "MANAGED_DATA_ROOT", root)
    report_path = (
        root / "report/entry_split_order_plan" / f"entry_split_order_plan_{DAY}.json"
    )
    policy_path = (
        root
        / "threshold_cycle/entry_split_order_policy"
        / f"entry_split_order_policy_{DAY}.json"
    )
    report_path.parent.mkdir(parents=True)
    policy_path.parent.mkdir(parents=True)
    policy = {
        "schema_version": native.POLICY_SCHEMA_VERSION,
        "source_date": DAY,
        "source_report": str(report_path),
        "policy_version": "test-v1",
        "runtime_apply_allowed": False,
        "buckets": {},
    }
    report = {
        "schema_version": native.SCHEMA_VERSION,
        "date": DAY,
        "recommended_policy": {
            "policy_version": "test-v1",
            "candidate_count": 3,
            "runtime_apply_allowed": False,
            "candidates": [{"evidence": [1, 2]}],
        },
        "cumulative_state": {
            "clean_tuning_baseline_date": "2026-06-05",
            "source_dates": [DAY],
        },
        "operating_candidate_grid": [{"code": "a"}, {"code": "b"}, {"code": "c"}],
        "economic_acceptance": {
            "status": "source_gap",
            "primary_operating_ev_pct": None,
            "blockers": ["actual_outcomes"],
            "candidate_count": 3,
            "model_rows": [{"row": 1}],
            "consumed_holdouts": {"abc": "def"},
            "input_rows": [{"test": [1, 2, 3]}],
            "candidates": [{"id": "a"}],
        },
    }
    report, policy = native.bind_report_policy_generation(report, policy)
    generation = report["artifact_generation_binding"]["generation_id"]
    paths = {
        "report_alias": report_path,
        "policy_alias": policy_path,
        "immutable_report": report_path.parent
        / "generations"
        / f"entry_split_order_plan_{DAY}_{generation}.json",
        "immutable_policy": policy_path.parent
        / "generations"
        / f"entry_split_order_policy_{DAY}_{generation}.json",
    }
    for key, path in paths.items():
        path.parent.mkdir(exist_ok=True)
        value = report if "report" in key else policy
        # Alias and immutable deliberately have different bytes, identical meaning.
        path.write_text(
            json.dumps(
                value, ensure_ascii=False, indent=2 if "immutable" in key else None
            )
        )
    return report_path, policy_path, paths, report, policy


def publish(pair):
    return projection.migrate_verification(pair[0], pair[1], source_date=DAY)


def test_native_projection_counts_nulls_authority_and_byte_hash(pair):
    evidence = publish(pair)
    view, proof = projection.read_verified_projection(
        pair[0], pair[1], source_date=DAY, role="submission_monitor"
    )
    assert proof["verified"] is True
    assert proof["_validated_policy"] == pair[4]
    assert proof["report_sha256"] == hashlib.sha256(pair[0].read_bytes()).hexdigest()
    assert (
        proof["report_sha256"]
        != pair[3]["artifact_generation_binding"]["report_content_sha256"]
    )
    assert view["operating_candidate_count"] == 3
    assert "operating_candidate_grid" not in view
    assert view["economic_acceptance"]["candidate_count"] == 3
    assert view["economic_acceptance"]["model_row_count"] == 1
    assert view["economic_acceptance"]["consumed_holdout_count"] == 1
    assert view["economic_acceptance"]["primary_operating_ev_pct"] is None
    assert view["economic_acceptance"]["blockers"] == ["actual_outcomes"]
    assert view["observation_projection"]["allowed_runtime_apply"] is False
    assert view["observation_projection"]["full_native_report"] is False
    assert view["observation_projection"]["metric_role"] == "source_quality_gate"
    assert (
        view["observation_projection"]["sample_floor"] == "none_for_contract_validation"
    )
    assert "order_authority" in view["observation_projection"]["forbidden_uses"]
    assert native.validate_report_policy_generation(view, pair[4])[0] is False
    assert evidence["projection_bytes"] < projection.MAX_PROJECTION_BYTES


def test_cross_process_style_warm_reader_never_opens_full_reports(pair, monkeypatch):
    publish(pair)
    full_paths = {path.absolute() for key, path in pair[2].items() if "report" in key}
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path.absolute() not in full_paths
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    for role in ("submission_monitor", "runtime_summary"):
        _, proof = projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role=role
        )
        assert proof["verified"]
    assert publish(pair)["reused_verified_receipt"] is True


@pytest.mark.parametrize(
    "which", ["report_alias", "immutable_report", "policy_alias", "immutable_policy"]
)
def test_each_source_mutation_invalidates_even_same_size_and_restored_mtime(
    pair, which
):
    publish(pair)
    path = pair[2][which]
    stamp = path.stat()
    encoded = path.read_bytes()
    changed = encoded.replace(b"test-v1", b"test-v2")
    assert len(changed) == len(encoded)
    path.write_bytes(changed)
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with pytest.raises(ValueError, match="source_changed"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="submission_monitor"
        )


def test_missing_manifest_on_large_report_is_pending_without_read(pair, monkeypatch):
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path == pair[0]:
            raise AssertionError("must not read full report")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(ValueError, match="verification_pending"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="submission_monitor"
        )


@pytest.mark.parametrize("key", ["projection", "receipt"])
def test_small_metadata_mutation_rejected(pair, key):
    publish(pair)
    pointer = json.loads(projection.manifest_path(pair[0]).read_text())
    path = Path(pointer[key]["identity"]["path"])
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source_changed"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="submission_monitor"
        )


def test_symlink_alias_rejected(pair):
    publish(pair)
    alias = pair[0]
    target = alias.with_suffix(".original")
    alias.rename(target)
    alias.symlink_to(target)
    with pytest.raises(ValueError):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="submission_monitor"
        )


def test_parent_symlink_inside_managed_root_rejected(pair):
    folder = pair[0].parent
    moved = folder.with_name("moved")
    folder.rename(moved)
    folder.symlink_to(moved)
    with pytest.raises(ValueError, match="managed_source_path|managed_child_symlink"):
        publish(pair)


def test_wrong_date_role_and_outside_root_rejected(pair, monkeypatch):
    publish(pair)
    with pytest.raises(ValueError, match="consumer_role_invalid"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="runtime_policy"
        )
    with pytest.raises(ValueError, match="manifest_contract"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date="2026-09-05", role="runtime_summary"
        )
    monkeypatch.setattr(projection, "MANAGED_DATA_ROOT", pair[0].parent)
    with pytest.raises(ValueError, match="managed_source_path"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="runtime_summary"
        )


def test_changed_validator_code_identity_requires_reverification(pair, monkeypatch):
    publish(pair)
    monkeypatch.setattr(projection, "_code_identity", lambda: {"changed": True})
    with pytest.raises(ValueError, match="manifest_contract"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="runtime_summary"
        )


def test_native_rejects_corrupt_semantics_before_manifest(pair):
    payload = json.loads(pair[0].read_text())
    payload["economic_acceptance"]["blockers"] = []
    pair[0].write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="generation_binding_digest_mismatch"):
        publish(pair)
    assert not projection.manifest_path(pair[0]).exists()


@pytest.mark.parametrize(
    "encoded",
    [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', b'{"x":'],
)
def test_strict_json_rejects_duplicates_nonfinite_and_truncation(encoded):
    with pytest.raises(ValueError):
        projection._strict_load(encoded)


def test_compact_stream_preserves_strings_unicode_numbers_chunk_boundary(tmp_path):
    value = {
        "s": ' spaced \\" quote " slash \\ 한글 ',
        "n": 1.25,
        "tail": "x" * (1024 * 1024 + 3),
    }
    source = tmp_path / "source.json"
    output = tmp_path / "compact.json"
    source.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    before = source.read_bytes()
    record, transform = projection._compact_copy(source, output)
    assert json.loads(output.read_bytes()) == value
    assert source.read_bytes() == before
    assert record["sha256"] == hashlib.sha256(before).hexdigest()
    assert transform["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert transform["size_bytes"] < len(before)


def test_compact_input_output_and_disk_budgets(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    source.write_text('{ "x": "1234567890" }')
    with pytest.raises(ValueError, match="migration_input_size_limit"):
        projection._compact_copy(source, tmp_path / "a.json", max_input_bytes=1)
    with pytest.raises(ValueError, match="migration_output_size_limit"):
        projection._compact_copy(source, tmp_path / "b.json", max_output_bytes=1)
    monkeypatch.setattr(
        projection.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 1})()
    )
    with pytest.raises(ValueError, match="migration_temporary_disk_budget"):
        projection._compact_copy(source, tmp_path / "c.json")


def test_nonzero_scalar_counts_and_candidate_count_preserved():
    report = {
        "economic_acceptance": {
            "model_rows": 7,
            "consumed_holdouts": 4,
            "candidate_count": 3,
        },
        "recommended_policy": {},
        "operating_candidate_grid": [1, 2],
    }
    value = projection.build_projection(report, {})
    assert value["economic_acceptance"]["model_rows"] == 7
    assert value["economic_acceptance"]["model_row_count"] == 7
    assert value["economic_acceptance"]["consumed_holdouts"] == 4
    assert value["economic_acceptance"]["consumed_holdout_count"] == 4
    assert value["economic_acceptance"]["candidate_count"] == 3


def test_manifest_atomic_failure_keeps_old_pointer(pair, monkeypatch):
    publish(pair)
    pointer_path = projection.manifest_path(pair[0])
    before = pointer_path.read_bytes()
    real_replace = projection.os.replace

    def fail_replace(source, target):
        if Path(target) == pointer_path:
            raise OSError("interrupted publication")
        return real_replace(source, target)

    monkeypatch.setattr(projection.os, "replace", fail_replace)
    with pytest.raises(OSError):
        projection._write_atomic(
            pointer_path, {"incomplete": True}, projection.MAX_METADATA_BYTES
        )
    assert pointer_path.read_bytes() == before
    assert projection.read_verified_projection(
        pair[0], pair[1], source_date=DAY, role="runtime_summary"
    )[1]["verified"]


def test_projection_size_overflow_is_not_truncated_to_success(pair, monkeypatch):
    monkeypatch.setattr(projection, "MAX_PROJECTION_BYTES", 100)
    with pytest.raises(ValueError, match="projection_size_limit"):
        publish(pair)
    assert not projection.manifest_path(pair[0]).exists()


def test_repeat_publish_reuses_existing_proof_without_new_generation(pair):
    first = publish(pair)
    files = set(pair[0].parent.rglob("*"))
    second = publish(pair)
    assert second["reused_verified_receipt"] is True
    assert set(pair[0].parent.rglob("*")) == files
    assert first["generation_id"] == second["generation_id"]


@pytest.mark.parametrize("number", [b"1 2", b"- 1", b"1e +2", b"tr ue", b"nu ll"])
def test_compaction_cannot_repair_malformed_primitive_tokens(tmp_path, number):
    source = tmp_path / "bad.json"
    output = tmp_path / "copy.json"
    source.write_bytes(
        b'{"padding":"' + b"x" * (1024 * 1024 - 17) + b'", "number":' + number + b"}"
    )
    projection._compact_copy(source, output)
    with pytest.raises(ValueError):
        projection._strict_load(output.read_bytes())


def test_missing_count_fields_remain_unknown():
    value = projection.build_projection(
        {"economic_acceptance": {}, "recommended_policy": {}}, {}
    )
    assert value["economic_acceptance"]["model_row_count"] is None
    assert value["economic_acceptance"]["consumed_holdout_count"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_authority", "runtime_policy"),
        ("runtime_effect", True),
        ("allowed_runtime_apply", True),
    ],
)
def test_manifest_observation_authority_is_enforced(pair, field, value):
    publish(pair)
    pointer_path = projection.manifest_path(pair[0])
    pointer = json.loads(pointer_path.read_text())
    pointer[field] = value
    pointer_path.write_text(json.dumps(pointer))
    with pytest.raises(ValueError, match="manifest_contract"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="runtime_summary"
        )


def test_invalid_managed_path_has_no_lock_or_temporary_side_effect(pair, monkeypatch):
    folder = pair[0].parent
    before = set(folder.iterdir())
    monkeypatch.setattr(projection, "MANAGED_DATA_ROOT", pair[0].parent)
    with pytest.raises(ValueError, match="managed_source_path"):
        publish(pair)
    assert set(folder.iterdir()) == before


def test_atomic_writer_rejects_broken_symlink(tmp_path):
    target = tmp_path / "proof.json"
    target.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="metadata_symlink"):
        projection._write_atomic(target, {}, 100, immutable=True)
    assert target.is_symlink()


def test_verifier_change_during_native_verification_cannot_publish(pair, monkeypatch):
    original = projection._code_identity()
    calls = 0

    def changing():
        nonlocal calls
        calls += 1
        return original if calls < 3 else {**original, "projection_sha256": "changed"}

    monkeypatch.setattr(projection, "_code_identity", changing)
    with pytest.raises(ValueError, match="verifier_changed_during_validation"):
        publish(pair)
    assert not projection.manifest_path(pair[0]).exists()


def test_supervisor_timeout_cleans_owned_temporary_files(pair, monkeypatch):
    observed = []

    def timeout(command, **kwargs):
        temporary = Path(command[command.index("--temporary-root") + 1])
        observed.append(temporary)
        (temporary / "copy.json").write_bytes(b"x" * 1024)
        raise projection.subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(projection.subprocess, "run", timeout)
    assert (
        projection.main(
            [
                "--source-date",
                DAY,
                "--report",
                str(pair[0]),
                "--policy",
                str(pair[1]),
                "--data-root",
                str(projection.MANAGED_DATA_ROOT),
                "--wall-seconds",
                "1",
            ]
        )
        == 1
    )
    assert observed and not observed[0].exists()


def test_native_writer_lock_prevents_concurrent_migration(pair):
    lock_path = pair[0].parent / f".entry_split_model_refresh_{DAY}.lock"
    with lock_path.open("a") as lock:
        projection.fcntl.flock(
            lock.fileno(), projection.fcntl.LOCK_EX | projection.fcntl.LOCK_NB
        )
        with pytest.raises(ValueError, match="producer_lock_busy"):
            publish(pair)
    assert not projection.manifest_path(pair[0]).exists()


def test_source_changed_after_native_validation_cannot_publish(pair, monkeypatch):
    validate = native.validate_report_policy_generation

    def mutation(report, policy):
        valid = validate(report, policy)
        pair[0].write_bytes(pair[0].read_bytes() + b" ")
        return valid

    monkeypatch.setattr(native, "validate_report_policy_generation", mutation)
    with pytest.raises(ValueError, match="source_changed"):
        publish(pair)
    assert not projection.manifest_path(pair[0]).exists()


def test_warm_metadata_total_budget_enforced(pair, monkeypatch):
    publish(pair)
    monkeypatch.setattr(projection, "MAX_WARM_METADATA_BYTES", 100)
    with pytest.raises(ValueError, match="warm_metadata_size_limit"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="runtime_summary"
        )


@pytest.mark.parametrize("which", ["receipt", "projection"])
def test_metadata_changed_after_snapshot_read_is_rejected(pair, monkeypatch, which):
    publish(pair)
    pointer = json.loads(projection.manifest_path(pair[0]).read_text())
    changed_path = Path(pointer[which]["identity"]["path"])
    read = projection._read

    def racing_read(path, limit):
        result = read(path, limit)
        if Path(path) == pair[1]:
            # Both immutable metadata snapshots have already been parsed. This
            # later policy read triggers a same-loop mutation of one of them.
            changed_path.write_bytes(changed_path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(projection, "_read", racing_read)
    with pytest.raises(ValueError, match="source_changed"):
        projection.read_verified_projection(
            pair[0], pair[1], source_date=DAY, role="submission_monitor"
        )


def test_original_producer_refs_are_observed_not_recomputed():
    report = {
        "code_commit": "old-commit",
        "producer_code_sha": "historical-producer-sha",
        "execution_model_refresh": {
            "model_implementation_sha256": "historical-model-sha"
        },
    }
    producer = projection.build_projection(report, {})["observation_projection"][
        "original_producer"
    ]
    assert producer["code_commit"] == "old-commit"
    assert producer["producer_code_sha"] == "historical-producer-sha"
    assert producer["producer_code_hash"] is None
    assert (
        producer["execution_model_refresh.model_implementation_sha256"]
        == "historical-model-sha"
    )
    assert producer["status"] == "recorded_refs_not_recomputed"
    assert producer["historical_code_replayed"] is False
    absent = projection.build_projection({}, {})["observation_projection"][
        "original_producer"
    ]
    assert absent["status"] == "not_recorded"
    assert absent["code_commit"] is None
    assert absent["producer_code_sha"] is None
    assert absent["producer_code_hash"] is None
    assert absent["execution_model_refresh.model_implementation_sha256"] is None
