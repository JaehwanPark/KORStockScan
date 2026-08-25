from __future__ import annotations

import gzip
import json
import math
import os
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.utils import jsonl_io
from src.utils.jsonl_io import (
    existing_or_gzip_path,
    iter_jsonl_objects_strict,
    read_json_object_strict,
    read_jsonl,
)


def test_read_jsonl_falls_back_to_gzip_sibling(tmp_path):
    plain_path = tmp_path / "events.jsonl"
    gzip_path = tmp_path / "events.jsonl.gz"
    rows = [{"event_type": "pipeline_event", "stage": "sample"}]

    with gzip.open(gzip_path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    assert existing_or_gzip_path(plain_path) == gzip_path
    assert read_jsonl(plain_path) == rows


def test_iter_jsonl_objects_strict_streams_plain_with_provenance(tmp_path):
    path = tmp_path / "events.jsonl"
    rows = [{"sequence": 1}, {"sequence": 2}]
    raw = (
        b"\n".join(
            json.dumps(row, separators=(",", ":")).encode("utf-8") for row in rows
        )
        + b"\n"
    )
    path.write_bytes(raw)
    provenance = {}

    assert list(iter_jsonl_objects_strict(path, provenance=provenance)) == rows
    assert provenance["source_path"] == str(path.absolute())
    assert provenance["source_sha256"] == jsonl_io.hashlib.sha256(raw).hexdigest()
    assert provenance["source_content_sha256"] == provenance["source_sha256"]
    assert provenance["source_json_object_row_count"] == 2
    assert provenance["source_snapshot_stable"] is True


def test_iter_jsonl_objects_strict_parses_single_representation_once(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "events.jsonl"
    rows = [{"sequence": 1}, {"sequence": 2}, {"sequence": 3}]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    original_parser = jsonl_io._json_object_from_bytes
    parse_count = 0

    def counted_parser(raw_line, *, source):
        nonlocal parse_count
        parse_count += 1
        return original_parser(raw_line, source=source)

    monkeypatch.setattr(jsonl_io, "_json_object_from_bytes", counted_parser)

    assert list(iter_jsonl_objects_strict(path)) == rows
    assert parse_count == len(rows)


def test_iter_jsonl_objects_strict_accepts_identical_plain_and_gzip(tmp_path):
    path = tmp_path / "events.jsonl"
    rows = [{"sequence": 1}, {"sequence": 2}]
    raw = b"".join(
        (json.dumps(row, separators=(",", ":")) + "\n").encode("utf-8") for row in rows
    )
    path.write_bytes(raw)
    path.with_name(f"{path.name}.gz").write_bytes(gzip.compress(raw, mtime=0))

    assert list(iter_jsonl_objects_strict(path)) == rows


def test_iter_jsonl_objects_strict_rejects_divergent_plain_and_gzip(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"sequence":1}\n', encoding="utf-8")
    path.with_name(f"{path.name}.gz").write_bytes(
        gzip.compress(b'{"sequence":2}\n', mtime=0)
    )

    with pytest.raises(ValueError, match="jsonl_artifact_plain_gzip_conflict"):
        list(iter_jsonl_objects_strict(path))


@pytest.mark.parametrize(
    "payload",
    (
        b'{"sequence":1}\nnot-json\n',
        b'{"sequence":1,"sequence":2}\n',
        b'{"sequence":NaN}\n',
        b"[1,2,3]\n",
    ),
)
def test_iter_jsonl_objects_strict_rejects_invalid_rows(tmp_path, payload):
    path = tmp_path / "events.jsonl"
    path.write_bytes(payload)

    with pytest.raises(ValueError):
        list(iter_jsonl_objects_strict(path))


def test_iter_jsonl_objects_strict_rejects_symlink(tmp_path):
    target = tmp_path / "target.jsonl"
    target.write_text('{"sequence":1}\n', encoding="utf-8")
    path = tmp_path / "events.jsonl"
    path.symlink_to(target)

    with pytest.raises(ValueError, match="jsonl_artifact_path_type_invalid"):
        list(iter_jsonl_objects_strict(path))


@pytest.mark.parametrize("kind", ("json", "jsonl"))
def test_strict_readers_reject_symlinked_parent_component(tmp_path, kind):
    external = tmp_path / "external"
    external.mkdir()
    logical = external / f"artifact.{kind}"
    logical.write_text('{"value":1}\n', encoding="utf-8")
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(external, target_is_directory=True)
    linked_logical = linked_parent / logical.name

    with pytest.raises(ValueError, match="artifact_parent_invalid"):
        if kind == "json":
            read_json_object_strict(linked_logical)
        else:
            list(iter_jsonl_objects_strict(linked_logical))


def test_iter_jsonl_objects_strict_rejects_parent_replacement_during_read(
    tmp_path,
    monkeypatch,
):
    parent = tmp_path / "owner"
    replaced_parent = tmp_path / "owner-replaced"
    parent.mkdir()
    logical = parent / "artifact.jsonl"
    logical.write_text('{"value":1}\n', encoding="utf-8")
    replacement_bytes = b'{"value":2}\n'
    original_parser = jsonl_io._json_object_from_bytes
    replaced = False

    def replace_parent_during_parse(payload, *, source):
        nonlocal replaced
        value = original_parser(payload, source=source)
        if not replaced:
            replaced = True
            parent.rename(replaced_parent)
            parent.mkdir()
            (parent / logical.name).write_bytes(replacement_bytes)
        return value

    monkeypatch.setattr(
        jsonl_io,
        "_json_object_from_bytes",
        replace_parent_during_parse,
    )

    with pytest.raises(ValueError, match="jsonl_artifact_parent_invalid"):
        list(iter_jsonl_objects_strict(logical))

    assert (parent / logical.name).read_bytes() == replacement_bytes


def test_read_json_object_strict_accepts_identical_plain_and_gzip(tmp_path):
    plain_path = tmp_path / "artifact.json"
    gzip_path = tmp_path / "artifact.json.gz"
    payload = {"schema": "example_v1", "rows": [{"value": 1}]}
    plain_path.write_text(json.dumps(payload), encoding="utf-8")
    with gzip.open(gzip_path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle)

    assert read_json_object_strict(plain_path) == payload
    assert read_json_object_strict(gzip_path) == payload


def test_read_json_object_strict_rejects_conflicting_plain_and_gzip(tmp_path):
    plain_path = tmp_path / "artifact.json"
    gzip_path = tmp_path / "artifact.json.gz"
    plain_path.write_text(json.dumps({"value": 1}), encoding="utf-8")
    with gzip.open(gzip_path, "wt", encoding="utf-8") as handle:
        json.dump({"value": 2}, handle)

    with pytest.raises(ValueError, match="json_artifact_plain_gzip_conflict"):
        read_json_object_strict(plain_path)


def test_read_json_object_strict_rejects_raw_divergence_with_equal_json_value(
    tmp_path,
):
    plain_path = tmp_path / "artifact.json"
    gzip_path = tmp_path / "artifact.json.gz"
    plain_path.write_bytes(b'{"value":1}\n')
    gzip_path.write_bytes(gzip.compress(b'{ "value": 1 }\n', mtime=0))

    with pytest.raises(ValueError, match="json_artifact_plain_gzip_conflict"):
        read_json_object_strict(plain_path)


@pytest.mark.parametrize(
    "invalid_json",
    ('{"value":NaN}', '{"value":1,"value":2}'),
)
@pytest.mark.parametrize("compressed", (False, True))
def test_read_json_object_strict_rejects_non_finite_and_duplicate_keys(
    tmp_path,
    invalid_json,
    compressed,
):
    artifact = tmp_path / "artifact.json"
    candidate = artifact.with_name(f"{artifact.name}.gz") if compressed else artifact
    if compressed:
        candidate.write_bytes(gzip.compress(invalid_json.encode("utf-8")))
    else:
        candidate.write_text(invalid_json, encoding="utf-8")

    with pytest.raises(ValueError):
        read_json_object_strict(artifact)


def test_read_json_object_strict_rejects_symlink(tmp_path):
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"value": 1}), encoding="utf-8")
    link = tmp_path / "artifact.json"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="json_artifact_path_type_invalid"):
        read_json_object_strict(link)


def test_read_json_object_strict_rejects_symlink_swap_before_open(
    tmp_path, monkeypatch
):
    artifact = tmp_path / "artifact.json"
    original = tmp_path / "artifact.original.json"
    replacement = tmp_path / "replacement.json"
    artifact.write_text(json.dumps({"value": 1}), encoding="utf-8")
    replacement.write_text(json.dumps({"value": 2}), encoding="utf-8")
    real_open = os.open
    swapped = False

    def swap_then_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if Path(path).name == artifact.name and dir_fd is not None and not swapped:
            swapped = True
            artifact.rename(original)
            artifact.symlink_to(replacement)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(jsonl_io.os, "open", swap_then_open)
    with pytest.raises(ValueError, match="json_artifact_changed_during_read"):
        read_json_object_strict(artifact)


def test_read_json_object_strict_rejects_atomic_replace_before_open(
    tmp_path, monkeypatch
):
    artifact = tmp_path / "artifact.json"
    replacement = tmp_path / "replacement.json"
    artifact.write_text(json.dumps({"value": 1}), encoding="utf-8")
    replacement.write_text(json.dumps({"value": 2}), encoding="utf-8")
    real_open = os.open
    swapped = False

    def replace_then_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if Path(path).name == artifact.name and dir_fd is not None and not swapped:
            swapped = True
            replacement.replace(artifact)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(jsonl_io.os, "open", replace_then_open)
    with pytest.raises(ValueError, match="json_artifact_changed_during_read"):
        read_json_object_strict(artifact)


def test_read_json_object_strict_rejects_sibling_created_during_read(
    tmp_path, monkeypatch
):
    artifact = tmp_path / "artifact.json"
    compressed = tmp_path / "artifact.json.gz"
    payload = {"value": 1}
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    real_object_pairs = jsonl_io._strict_json_object_pairs
    created = False

    def create_sibling_during_parse(pairs):
        nonlocal created
        if not created:
            created = True
            compressed.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))
        return real_object_pairs(pairs)

    monkeypatch.setattr(
        jsonl_io,
        "_strict_json_object_pairs",
        create_sibling_during_parse,
    )
    with pytest.raises(ValueError, match="json_artifact_changed_during_read"):
        read_json_object_strict(artifact)


def test_generation_safe_writer_archives_gzip_only_generation(tmp_path):
    artifact = tmp_path / "artifact.json"
    compressed = artifact.with_name(f"{artifact.name}.gz")
    old_payload = {"generation": "old", "rows": [1, 2, 3]}
    new_payload = {"generation": "new", "rows": [4, 5, 6]}
    old_bytes = (json.dumps(old_payload, sort_keys=True) + "\n").encode("utf-8")
    compressed_bytes = gzip.compress(old_bytes, mtime=0)
    compressed.write_bytes(compressed_bytes)

    jsonl_io.write_json_object_generation_safe(
        artifact,
        new_payload,
        sort_keys=True,
        trailing_newline=True,
    )

    archived = list((tmp_path / "superseded").glob("*/artifact.json.gz"))
    assert read_json_object_strict(artifact) == new_payload
    assert artifact.exists()
    assert not compressed.exists()
    assert len(archived) == 1
    assert archived[0].read_bytes() == compressed_bytes


def test_generation_safe_writer_streams_gzip_restore_without_full_decompress(
    tmp_path,
    monkeypatch,
):
    artifact = tmp_path / "artifact.json"
    compressed = artifact.with_name(f"{artifact.name}.gz")
    old_payload = {"generation": "old", "rows": ["x" * 1_000] * 3_000}
    compressed.write_bytes(
        gzip.compress(json.dumps(old_payload).encode("utf-8"), mtime=0)
    )
    monkeypatch.setattr(
        jsonl_io.gzip,
        "decompress",
        lambda _payload: (_ for _ in ()).throw(
            AssertionError("full gzip decompression is forbidden")
        ),
    )

    jsonl_io.write_json_object_generation_safe(
        artifact,
        {"generation": "new"},
    )

    assert read_json_object_strict(artifact) == {"generation": "new"}
    assert len(list((tmp_path / "superseded").glob("*/artifact.json.gz"))) == 1


def test_generation_safe_writer_crash_before_new_publish_leaves_readable_old(
    tmp_path, monkeypatch
):
    artifact = tmp_path / "artifact.json"
    compressed = artifact.with_name(f"{artifact.name}.gz")
    old_payload = {"generation": "old"}
    new_payload = {"generation": "new"}
    compressed.write_bytes(gzip.compress(json.dumps(old_payload).encode("utf-8")))
    real_replace = jsonl_io.os.replace
    failed = False

    def fail_first_replace(source, target, *args, **kwargs):
        nonlocal failed
        if Path(target).name == artifact.name and not failed:
            failed = True
            raise OSError("injected_new_generation_publish_failure")
        return real_replace(source, target, *args, **kwargs)

    monkeypatch.setattr(jsonl_io.os, "replace", fail_first_replace)
    with pytest.raises(OSError, match="injected_new_generation_publish_failure"):
        jsonl_io.write_json_object_generation_safe(artifact, new_payload)

    assert read_json_object_strict(artifact) == old_payload
    assert artifact.exists()
    assert not compressed.exists()
    assert len(list((tmp_path / "superseded").glob("*/artifact.json.gz"))) == 1

    monkeypatch.setattr(jsonl_io.os, "replace", real_replace)
    jsonl_io.write_json_object_generation_safe(artifact, new_payload)
    assert read_json_object_strict(artifact) == new_payload


def test_generation_safe_writer_fails_closed_on_parent_directory_replacement(
    tmp_path,
    monkeypatch,
):
    parent = tmp_path / "owner"
    replaced_parent = tmp_path / "owner-replaced"
    parent.mkdir()
    artifact = parent / "artifact.json"
    original_lock = jsonl_io.json_artifact_generation_lock

    @contextmanager
    def replace_parent_after_lock(*args, **kwargs):
        with original_lock(*args, **kwargs) as generation:
            parent.rename(replaced_parent)
            parent.mkdir()
            yield generation

    monkeypatch.setattr(
        jsonl_io,
        "json_artifact_generation_lock",
        replace_parent_after_lock,
    )

    with pytest.raises(OSError, match="json_generation_parent_changed"):
        jsonl_io.write_json_object_generation_safe(artifact, {"generation": "new"})

    assert list(parent.iterdir()) == []
    assert not (replaced_parent / artifact.name).exists()


def test_generation_safe_writer_rejects_superseded_symlink_before_child_creation(
    tmp_path,
):
    artifact = tmp_path / "artifact.json"
    compressed = artifact.with_name(f"{artifact.name}.gz")
    external = tmp_path / "external"
    external.mkdir()
    (tmp_path / "superseded").symlink_to(external, target_is_directory=True)
    compressed.write_bytes(gzip.compress(json.dumps({"old": 1}).encode("utf-8")))

    with pytest.raises(OSError, match="archive_directory_invalid"):
        jsonl_io.write_json_object_generation_safe(artifact, {"new": 2})

    assert list(external.iterdir()) == []
    assert read_json_object_strict(artifact) == {"old": 1}
    assert compressed.exists()


@pytest.mark.parametrize("invalid_value", (math.nan, math.inf, -math.inf))
def test_generation_safe_writer_rejects_non_finite_json_by_default(
    tmp_path,
    invalid_value,
):
    artifact = tmp_path / "artifact.json"

    with pytest.raises(ValueError, match="Out of range float values"):
        jsonl_io.write_json_object_generation_safe(
            artifact,
            {"invalid": invalid_value},
        )

    assert not artifact.exists()
    assert not artifact.with_name(f"{artifact.name}.gz").exists()


@pytest.mark.parametrize("invalid_value", (math.nan, object()))
def test_generation_safe_writer_invalid_payload_leaves_gzip_generation_unchanged(
    tmp_path,
    invalid_value,
):
    artifact = tmp_path / "artifact.json"
    compressed = artifact.with_name(f"{artifact.name}.gz")
    compressed_bytes = gzip.compress(json.dumps({"old": 1}).encode("utf-8"))
    compressed.write_bytes(compressed_bytes)

    with pytest.raises((TypeError, ValueError)):
        jsonl_io.write_json_object_generation_safe(
            artifact,
            {"invalid": invalid_value},
        )

    assert not artifact.exists()
    assert compressed.read_bytes() == compressed_bytes
    assert not (tmp_path / "superseded").exists()


@pytest.mark.parametrize(
    "invalid_legacy_json",
    ('{"value":Infinity}', '{"value":1,"value":2}'),
)
def test_generation_safe_writer_rejects_invalid_legacy_gzip_without_mutation(
    tmp_path,
    invalid_legacy_json,
):
    artifact = tmp_path / "artifact.json"
    compressed = artifact.with_name(f"{artifact.name}.gz")
    compressed_bytes = gzip.compress(invalid_legacy_json.encode("utf-8"))
    compressed.write_bytes(compressed_bytes)

    with pytest.raises(ValueError, match="json_generation_payload_invalid"):
        jsonl_io.write_json_object_generation_safe(artifact, {"new": 1})

    assert not artifact.exists()
    assert compressed.read_bytes() == compressed_bytes
    assert not (tmp_path / "superseded").exists()
