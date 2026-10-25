"""Operational retention owns closed files, never raw trading evidence."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.engine.infrastructure import log_retention as R


@pytest.fixture(autouse=True)
def document_root(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir(exist_ok=True)

    # Native production census is all-PID/fail-closed. Tests own only this
    # process's files and must not require sudo outside the test sandbox.
    def opened():
        result = set()
        for path in Path("/proc/self/fd").iterdir():
            try:
                s = path.stat()
                result.add((s.st_dev, s.st_ino))
            except FileNotFoundError:
                pass
        return result

    monkeypatch.setattr(R, "open_owned_inodes", opened)


def generation(root, name="writer.log.closed_one"):
    log = root / "logs"
    log.mkdir(exist_ok=True)
    path = log / name
    path.write_bytes(b"original\r\nevidence\n")
    row = R.register_generation(log / "writer.log", path, owner="writer")
    return path, row


def test_expired_closed_generation_deletes_with_tombstone_and_unknown_stays(tmp_path):
    path, row = generation(tmp_path)
    active = path.parent / "writer.log"
    active.write_text("live")
    unknown = path.parent / "unknown.log.1"
    unknown.write_text("unknown")
    now = row["closed_at"] + 31 * R.DAY
    preview = R.maintain_logs(tmp_path, now=now)
    assert preview["deleted"] == 1 and path.exists()
    result = R.maintain_logs(tmp_path, now=now, apply=True)
    assert result["status"] == "complete" and result["deleted"] == 1
    assert not path.exists() and active.read_text() == "live" and unknown.exists()
    assert R.maintain_logs(tmp_path, now=now, apply=True)["deleted"] == 0


@pytest.mark.parametrize(
    "protection", ["open", "pin", "reference", "modified", "symlink"]
)
def test_expiry_preserves_protected_or_changed_generations(tmp_path, protection):
    path, row = generation(tmp_path)
    handle = None
    if protection == "open":
        handle = path.open("rb")
    if protection == "pin":
        R.atomic_json(
            tmp_path / "data/config/log_retention_pins.json",
            dict(schema="operational_retention_pins_v1", pins=[str(path)]),
        )
    if protection == "reference":
        docs = tmp_path / "docs"
        (docs / "audit.md").write_text(path.name)
    if protection == "modified":
        path.write_text("changed")
    if protection == "symlink":
        dest = tmp_path / "outside"
        dest.write_text("original")
        path.unlink()
        path.symlink_to(dest)
    try:
        result = R.maintain_logs(
            tmp_path, now=row["closed_at"] + 31 * R.DAY, apply=True
        )
        assert path.exists() and result["deleted"] == 0
    finally:
        if handle:
            handle.close()


def test_generation_count_and_capacity_are_per_writer(tmp_path):
    paths = [generation(tmp_path, f"writer.log.closed_{n}")[0] for n in range(11)]
    other = tmp_path / "logs/other.log.closed"
    other.write_text("other")
    R.register_generation(tmp_path / "logs/other.log", other, owner="other")
    result = R.maintain_logs(tmp_path, apply=True)
    assert result["status"] == "complete" and result["deleted"] == 1
    assert sum(p.exists() for p in paths) == 10 and other.exists()


def test_unknown_tmp_worktree_and_evidence_never_age_out(tmp_path):
    run = tmp_path / "tmp/workorder-old"
    run.mkdir(parents=True)
    file = run / "evidence.json"
    file.write_text("{}")
    os.utime(file, (1, 1))
    assert R.maintain_tmp(tmp_path, apply=True)["deleted"] == 0 and file.exists()
    R.atomic_json(
        run / "run.retention.json",
        dict(
            schema="temporary_run_retention_v1",
            owner="test",
            closed=True,
            pinned=False,
            expires_at=1,
            files={"evidence.json": R.digest(file)},
        ),
    )
    assert R.maintain_tmp(tmp_path, apply=True)["deleted"] == 1 and not file.exists()


def test_daily_metrics_retains_invalid_and_exact_current_bytes(tmp_path):
    source = tmp_path / "logs/system_metric_samples.jsonl"
    source.parent.mkdir()
    original = b'{"ts":"2026-10-10T10:00:00+09:00"}\n{bad}\r\n{"ts":"2026-10-16T10:00:00+09:00"}\r\n'
    source.write_bytes(original)
    result = R.prune_metrics(
        tmp_path,
        apply=True,
        now=datetime(2026, 10, 16, 6, tzinfo=timezone.utc).timestamp(),
    )
    assert result["pruned"] == 1 and result["invalid_retained"] == 1
    assert source.read_bytes() == original.split(b"\n", 1)[1]


def test_active_file_cannot_register_as_closed(tmp_path):
    p = tmp_path / "writer.log"
    p.write_text("live")
    with pytest.raises(ValueError):
        R.register_generation(p, p, owner="writer")


def test_retention_failure_has_nonzero_and_failed_terminal(tmp_path):
    (tmp_path / "logs").mkdir()
    terminal = tmp_path / "receipt.json"
    R.atomic_json(
        tmp_path / "data/config/log_retention_pins.json", {"schema": "invalid"}
    )
    assert (
        R.main(["--workspace", str(tmp_path), "--terminal", str(terminal), "--apply"])
        == 1
    )
    assert json.loads(terminal.read_bytes())["status"] == "failed"


def test_tmp_recovers_crash_after_unlink_without_deleting_reappeared_path(
    tmp_path, monkeypatch
):
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    one = run / "one.json"
    one.write_text("one")
    two = run / "two.json"
    two.write_text("two")
    manifest = run / "run.retention.json"
    row = dict(
        schema="temporary_run_retention_v1",
        owner="test",
        closed=True,
        pinned=False,
        expires_at=1,
        files={p.name: R.digest(p) for p in (one, two)},
        delete_pending="one.json",
    )
    R.atomic_json(manifest, row)
    one.unlink()
    assert R.maintain_tmp(tmp_path, apply=True)["deleted"] == 1
    assert not two.exists() and R.read_json(manifest)["closed"] is False
    assert set(R.read_json(manifest)["deleted_files"]) == {"one.json", "two.json"}


def test_tmp_retry_does_not_accept_missing_file_without_delete_intent(tmp_path):
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    one = run / "one.json"
    one.write_text("one")
    two = run / "two.json"
    two.write_text("two")
    R.atomic_json(
        run / "run.retention.json",
        dict(
            schema="temporary_run_retention_v1",
            owner="test",
            closed=True,
            pinned=False,
            expires_at=1,
            files={p.name: R.digest(p) for p in (one, two)},
        ),
    )
    one.unlink()
    result = R.maintain_tmp(tmp_path, apply=True)
    assert result["deleted"] == 0 and result["deferred"] and two.exists()


@pytest.mark.parametrize(
    "reference",
    [
        "[proof](../../tmp/run/proof.json#result)",
        "[proof](<../../tmp/run/proof.json:12>)",
        '[proof][receipt]\n[receipt]: ../../tmp/%72un/proof.json "original"',
        '<a href="../../tmp/run/proof.json">original</a>',
        '<A HREF="../../tmp/run/proof.json">original</A>',
        "[directory](../../tmp/run/)",
        "[image](../../tmp/run/proof.json)",
    ],
)
def test_tmp_preserves_normalized_document_references(tmp_path, reference):
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / "proof.json"
    proof.write_bytes(b"original\r\n")
    R.atomic_json(
        run / "run.retention.json",
        dict(
            schema="temporary_run_retention_v1",
            owner="test",
            closed=True,
            pinned=False,
            expires_at=1,
            files={proof.name: R.digest(proof)},
        ),
    )
    doc = tmp_path / "docs/archive/audit.md"
    doc.parent.mkdir()
    doc.write_text(reference)
    for apply in (False, True):
        result = R.maintain_tmp(tmp_path, apply=apply)
        assert result["deleted"] == 0 and result["deferred"]
        assert proof.read_bytes() == b"original\r\n"


@pytest.mark.parametrize(
    "where,reference",
    [
        ("README.md", "[original](logs/writer.log.closed_one)"),
        ("AGENTS.md", "[directory](logs/)"),
        ("docs/audit.md", "[original](../logs/writer.log.%63losed_one)"),
        ("docs/audit.md", "[alias](../alias/proof)"),
    ],
)
def test_log_owner_preserves_root_encoded_and_symlink_links(tmp_path, where, reference):
    path, row = generation(tmp_path)
    (tmp_path / "alias").mkdir()
    (tmp_path / "alias/proof").symlink_to(path)
    (tmp_path / where).write_text(reference)
    result = R.maintain_logs(tmp_path, apply=True, now=row["closed_at"] + 31 * R.DAY)
    assert result["deleted"] == 0 and path.read_bytes() == b"original\r\nevidence\n"


@pytest.mark.parametrize(
    "defect",
    ["missing", "directory_symlink", "file_symlink", "invalid_utf8", "bytes", "count"],
)
def test_incomplete_document_census_cannot_delete(tmp_path, monkeypatch, defect):
    path, row = generation(tmp_path)
    docs = tmp_path / "docs"
    if defect == "missing":
        docs.rmdir()
    elif defect == "directory_symlink":
        (docs / "alias").symlink_to(tmp_path, target_is_directory=True)
    elif defect == "file_symlink":
        (docs / "a.md").symlink_to(path)
    elif defect == "invalid_utf8":
        (docs / "a.md").write_bytes(b"\xff")
    elif defect == "bytes":
        (docs / "a.md").write_text("oversize")
        monkeypatch.setattr(R, "MAX_DOCUMENT_BYTES", 2)
    else:
        monkeypatch.setattr(R, "MAX_DOCUMENT_FILES", 1)
    result = R.maintain_logs(tmp_path, apply=True, now=row["closed_at"] + 31 * R.DAY)
    assert result["status"] == "failed" and result["deleted"] == 0
    assert path.exists()


@pytest.mark.parametrize(
    "change", ["new_link", "new_document", "removed_document", "alias"]
)
def test_changed_document_generation_aborts_before_log_unlink(
    tmp_path, monkeypatch, change
):
    path, row = generation(tmp_path)
    doc = tmp_path / "docs/audit.md"
    doc.write_text("original")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path / "absent")
    if change == "alias":
        doc.write_text("[proof](../alias)")
    atomic = R.atomic_json

    def writing_intent(meta, record):
        atomic(meta, record)
        if record.get("state") != "delete_pending":
            return
        if change == "new_link":
            doc.write_text(f"[new]({path})")
        elif change == "new_document":
            (tmp_path / "docs/new.md").write_text(f"[new]({path})")
        elif change == "removed_document":
            doc.unlink()
        else:
            alias.unlink()
            alias.symlink_to(path)

    monkeypatch.setattr(R, "atomic_json", writing_intent)
    result = R.maintain_logs(tmp_path, apply=True, now=row["closed_at"] + 31 * R.DAY)
    assert result["status"] == "failed" and result["deleted"] == 0 and path.exists()


def scratch_owner(tmp_path, monkeypatch):
    """Load the actual legacy caller; replace only its host census dependency."""
    import importlib.util

    source = (
        Path(__file__).resolve().parents[2]
        / "tmp/source-disk-cleanup-20261022/worktree-audit/archive_tmp.py"
    )
    stub = tmp_path / "guards.py"
    stub.write_text(
        "from pathlib import Path\nfrom types import SimpleNamespace\n"
        "from src.engine.infrastructure import log_retention as R\n"
        f"M=SimpleNamespace(W=Path({str(tmp_path)!r}), A=SimpleNamespace(digest=R.digest))\n"
    )
    original = importlib.util.spec_from_file_location

    def spec(name, location, *args, **kwargs):
        return original(
            name, stub if name == "worktree_guards" else location, *args, **kwargs
        )

    monkeypatch.setattr(importlib.util, "spec_from_file_location", spec)
    loader = original("scratch_archive_under_test", source)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


@pytest.mark.parametrize("subset", [False, True])
def test_original_archive_delete_and_resume_preserve_cited_source(
    tmp_path, monkeypatch, subset
):
    archive = scratch_owner(tmp_path, monkeypatch)
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / "proof.json"
    proof.write_bytes(b"exact\r\noriginal\n")
    (run / "other").write_text("other")
    rows = archive.inventory(run)
    doc = tmp_path / "docs/audit.md"
    doc.write_text("[proof](../tmp/%72un/proof.json)")
    with pytest.raises(R.DocumentReferenceError, match="document_reference_preserved"):
        archive.delete_verified(
            run, {"proof.json": rows["proof.json"]} if subset else rows
        )
    assert proof.read_bytes() == b"exact\r\noriginal\n" and (run / "other").exists()
    # The planning path also rejects before its process/closure census.
    with pytest.raises(R.DocumentReferenceError, match="document_reference_preserved"):
        archive.check(run)


def test_verified_rebinding_allows_archive_delete_and_protects_recovered_target(
    tmp_path, monkeypatch
):
    archive = scratch_owner(tmp_path, monkeypatch)
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / "proof.json"
    proof.write_bytes(b"exact\r\noriginal\n")
    rows = archive.inventory(run)
    store = tmp_path / "preserved"
    store.mkdir()
    packed = store / "original.tar.zst"
    archive.archive(run, rows, packed)
    archive.verify(packed, rows)
    # The document rewrite is an explicit reviewed operation, not a deletion fallback.
    restored = store / "proof.json"
    restored.write_bytes(proof.read_bytes())
    assert R.digest(restored) == rows["proof.json"]["sha256"]
    (tmp_path / "docs/audit.md").write_text("[proof](../preserved/proof.json)")
    assert archive.delete_verified(run, rows) == ["proof.json"] and not run.exists()
    assert restored.read_bytes() == b"exact\r\noriginal\n"
    with pytest.raises(R.DocumentReferenceError, match="document_reference_preserved"):
        archive.delete_verified(store, archive.inventory(store))


def test_archive_doc_change_before_first_unlink_preserves_all_originals(
    tmp_path, monkeypatch
):
    archive = scratch_owner(tmp_path, monkeypatch)
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / "proof.json"
    proof.write_text("original")
    rows = archive.inventory(run)
    monkeypatch.setattr(
        archive,
        "write_access",
        lambda *_: (tmp_path / "docs/new.md").write_text(f"[proof]({proof})"),
    )
    with pytest.raises(R.DocumentReferenceError, match="document_references_changed"):
        archive.delete_verified(run, rows)
    assert proof.read_text() == "original"


def test_unavailable_native_fd_census_still_prevents_delete(tmp_path, monkeypatch):
    path, row = generation(tmp_path)

    def unavailable():
        raise PermissionError("census unavailable")

    monkeypatch.setattr(R, "open_owned_inodes", unavailable)
    result = R.maintain_logs(tmp_path, apply=True, now=row["closed_at"] + 31 * R.DAY)
    assert result["status"] == "failed" and result["deleted"] == 0
    assert path.exists()


def test_archive_index_protects_transitive_original_and_detects_index_edits(tmp_path):
    store = tmp_path / "preserved"
    store.mkdir()
    archive = store / "original.tar.zst"
    archive.write_bytes(b"original archive")
    index = store / "index.md"
    index.write_text("[original](original.tar.zst)\n[cycle](index.md)")
    (tmp_path / "docs/audit.md").write_text("[index](../preserved/index.md)")
    census = R.DocumentReferences(tmp_path)
    assert census.references({str(archive)}) == {str(archive)}
    assert len(census.linked_documents) == 1
    index.write_text("[new](new.tar.zst)")
    with pytest.raises(
        R.DocumentReferenceError, match="linked_document_references_changed"
    ):
        census.assert_unchanged()


def test_archive_batch_checks_unchanged_census_without_per_file_rescan(
    tmp_path, monkeypatch
):
    archive = scratch_owner(tmp_path, monkeypatch)
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    for index in range(25):
        (run / str(index)).write_text("closed fixture")
    rows = archive.inventory(run)
    original = R.DocumentReferences._inventory
    calls = []

    def counted(self):
        calls.append(None)
        return original(self)

    monkeypatch.setattr(R.DocumentReferences, "_inventory", counted)
    assert len(archive.delete_verified(run, rows)) == 25
    assert len(calls) < 10 and not run.exists()


@pytest.mark.parametrize(
    "change", ["edit", "new_document", "delete", "rename", "alias", "linked_index"]
)
def test_watched_census_rejects_every_reference_change(tmp_path, change):
    doc = tmp_path / "docs/audit.md"
    target = tmp_path / "target"
    target.write_text("original")
    alias = tmp_path / "alias"
    alias.symlink_to(target)
    index = tmp_path / "index.md"
    index.write_text("original index")
    doc.write_text(f"[alias]({alias}) [index]({index})")
    census = R.DocumentReferences(tmp_path)
    with pytest.raises(R.DocumentReferenceError):
        with census.watch_changes():
            census.assert_unchanged()
            if change == "edit":
                doc.write_text("changed")
            elif change == "new_document":
                (doc.parent / "new.md").write_text("new reference")
            elif change == "delete":
                doc.unlink()
            elif change == "rename":
                doc.rename(doc.with_name("renamed.md"))
            elif change == "alias":
                alias.unlink()
                alias.symlink_to(tmp_path / "different")
            else:
                index.write_text("changed index")
            census.assert_unchanged()
    assert census._watch is None


def test_unavailable_document_watch_uses_original_full_census(tmp_path, monkeypatch):
    census = R.DocumentReferences(tmp_path)

    def unavailable(_):
        raise OSError("watch budget exhausted")

    monkeypatch.setattr(R, "_DocumentChangeWatch", unavailable)
    with pytest.raises(R.DocumentReferenceError, match="document_references_changed"):
        with census.watch_changes():
            (tmp_path / "docs/new.md").write_text("new reference")
            census.assert_unchanged()


def test_document_watch_overflow_aborts_and_closes_fd(tmp_path, monkeypatch):
    import struct

    census = R.DocumentReferences(tmp_path)
    fd = None
    with pytest.raises(R.DocumentReferenceError, match="document_watch_invalidated"):
        with census.watch_changes():
            fd = census._watch.fd
            original = os.read
            monkeypatch.setattr(
                os,
                "read",
                lambda f, n: (
                    struct.pack("iIII", -1, 0x4000, 0, 0) if f == fd else original(f, n)
                ),
            )
            census.assert_unchanged()
    with pytest.raises(OSError):
        os.fstat(fd)


@pytest.mark.parametrize("leaf", ["proof (v1).json", "proof name.json"])
def test_local_link_forms_and_archive_sibling_do_not_escape_protection(tmp_path, leaf):
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / leaf
    proof.write_text("original")
    doc = tmp_path / "docs/audit.md"
    forms = [
        f"[proof](<{proof}>)",
        f"<{proof.as_uri()}>",
        f'[proof](../tmp/run/{leaf.replace(" ", "%20")})',
    ]
    for text in forms:
        doc.write_text(text)
        census = R.DocumentReferences(tmp_path)
        assert census.references({str(run)}) == {str(run)}
        assert census.references({str(tmp_path / "tmp/run-old")}) == set()


def test_tmp_document_change_is_failed_at_cli_boundary(tmp_path, monkeypatch):
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / "proof.json"
    proof.write_text("original")
    R.atomic_json(
        run / "run.retention.json",
        dict(
            schema="temporary_run_retention_v1",
            owner="test",
            closed=True,
            pinned=False,
            expires_at=1,
            files={proof.name: R.digest(proof)},
        ),
    )
    atomic = R.atomic_json

    def writing_intent(meta, row):
        atomic(meta, row)
        if row.get("delete_pending"):
            (tmp_path / "docs/new.md").write_text(f"[proof]({proof})")

    monkeypatch.setattr(R, "atomic_json", writing_intent)
    terminal = tmp_path / "terminal.json"
    assert (
        R.main(
            [
                "--workspace",
                str(tmp_path),
                "--apply",
                "--include-tmp",
                "--terminal",
                str(terminal),
            ]
        )
        == 1
    )
    assert proof.read_text() == "original"
    assert R.read_json(terminal)["tmp"]["status"] == "failed"


def test_empty_retention_lane_needs_no_document_or_process_census(
    tmp_path, monkeypatch
):
    (tmp_path / "docs").rmdir()

    def forbidden(*_):
        pytest.fail("no deletion candidates: census should not execute")

    monkeypatch.setattr(R, "DocumentReferences", forbidden)
    monkeypatch.setattr(R, "open_owned_inodes", forbidden)
    assert R.maintain_logs(tmp_path, apply=True)["deleted"] == 0
    assert R.maintain_tmp(tmp_path, apply=True)["deleted"] == 0


def test_failed_census_stops_once_with_multiple_expired_generations(
    tmp_path, monkeypatch
):
    one, row = generation(tmp_path)
    two, _ = generation(tmp_path, "writer.log.closed_two")
    calls = []

    def unavailable():
        calls.append(True)
        raise PermissionError("census unavailable")

    monkeypatch.setattr(R, "open_owned_inodes", unavailable)
    result = R.maintain_logs(tmp_path, apply=True, now=row["closed_at"] + 31 * R.DAY)
    assert result["status"] == "failed" and len(calls) == 1
    assert one.exists() and two.exists()


@pytest.mark.parametrize("defect", ["changed_source", "new_file", "bad_archive"])
def test_archive_existing_identity_and_integrity_guards_remain(
    tmp_path, monkeypatch, defect
):
    archive = scratch_owner(tmp_path, monkeypatch)
    run = tmp_path / "tmp/run"
    run.mkdir(parents=True)
    proof = run / "proof.json"
    proof.write_bytes(b"original\r\n")
    rows = archive.inventory(run)
    if defect == "changed_source":
        proof.write_text("new generation")
        with pytest.raises(AssertionError, match="entry_changed"):
            archive.delete_verified(run, rows)
        assert proof.read_text() == "new generation"
    elif defect == "new_file":
        new = run / "new.json"
        new.write_text("concurrent original")
        assert archive.delete_verified(run, rows) == ["proof.json"]
        assert new.read_text() == "concurrent original"
    else:
        packed = tmp_path / "original.tar.zst"
        archive.archive(run, rows, packed)
        packed.write_bytes(packed.read_bytes()[:14])
        with pytest.raises((AssertionError, archive.tarfile.TarError, EOFError)):
            archive.verify(packed, rows)
        assert proof.read_bytes() == b"original\r\n"
