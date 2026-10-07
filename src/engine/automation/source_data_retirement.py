"""Apply an operator-reviewed file-source retirement manifest, never a DB purge.

Owns one-shot physical deletion and its durable journal. No scheduling, archive
creation, provider calls, policy changes or service control are performed here.
Period/consumer classification belongs to the reviewed manifest producer.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = "file_source_retirement_manifest_v1"
CUTOFF = "2026-09-01"
WORKSPACE = Path("/home/ubuntu/KORStockScan")
RAW_FAMILIES = {
    "analytics/parquet", "source_quality/raw_row_exclusion",
    "cache/low_price_two_leg_ka10080", "cache/widget_signal_research_sources",
    "monitoring/widget_research_watch", "ai_canonical_context_candidates",
    "ai_decision_trace", "ai_decision_outcomes", "observations",
    "pipeline_events", "pipeline_event_summaries", "post_sell",
    "runtime/sentinel_event_cache", "runtime/shared_ws_completed_bars",
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def identity(st):
    return dict(device=st.st_dev, inode=st.st_ino, size=st.st_size,
                mtime_ns=st.st_mtime_ns, ctime_ns=st.st_ctime_ns,
                nlink=st.st_nlink)


def file_hash(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _parent_fd(path):
    """Pin every ancestor without following even an intermediate symlink."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("noncanonical_path")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _raw_family(path):
    # Independent checkout copies must preserve the same data-relative family.
    if not path.is_relative_to(WORKSPACE.parent):
        raise ValueError("outside_project_storage")
    relative = path.relative_to(WORKSPACE.parent)
    if not relative.parts[0].startswith("KORStockScan"):
        raise ValueError("outside_project_storage")
    for index, part in enumerate(relative.parts):
        if part == "data":
            source = "/".join(relative.parts[index + 1:])
            for family in RAW_FAMILIES:
                if source.startswith(family + "/"):
                    return family
    raise ValueError("not_allowlisted_raw_family")


def _validate_entry(entry, protected):
    path = Path(entry["path"])
    if str(path) != entry["path"] or path.resolve() != path:
        raise ValueError("noncanonical_or_symlink_path")
    if str(path) in protected or entry["classification"] != "delete_unused_raw":
        raise ValueError("protected_or_unreleased_reader")
    if not entry.get("consumer_evidence"):
        raise ValueError("consumer_evidence_missing")
    proof = entry["period_evidence"]
    if entry.get("kind") == "retired_archive":
        archive_root = WORKSPACE.parent / "KORStockScan-storage-archives"
        if not path.is_relative_to(archive_root) or not path.name.endswith((".tar.zst", ".tar.gz")):
            raise ValueError("archive_path_invalid")
        if proof.get("mode") != "archive_member_census" or not proof.get("preserved_nonraw_receipt"):
            raise ValueError("archive_nonraw_preservation_missing")
        receipt = Path(proof["preserved_nonraw_receipt"])
        if file_hash(receipt) != proof.get("preserved_nonraw_receipt_sha256"):
            raise ValueError("archive_preservation_receipt_changed")
        preserved = json.loads(receipt.read_text())
        if preserved.get("source_archive_sha256") != entry["sha256"]:
            raise ValueError("archive_preservation_source_mismatch")
        if (preserved.get("schema") != "file_source_archive_nonraw_preservation_v1"
                or preserved.get("complete") is not True or preserved.get("unclassified_members")
                or preserved.get("raw_backup_created") is not False
                or preserved.get("member_byte_identity_verified", 0) <= 0
                or preserved.get("member_byte_identity_verified") != (
                    len(preserved.get("preserved_files", []))
                    + len(preserved.get("retired_raw_members", [])))):
            raise ValueError("archive_preservation_incomplete")
        for item in preserved["preserved_files"]:
            if file_hash(item["path"]) != item["sha256"]:
                raise ValueError("archive_preserved_file_changed")
    else:
        family = _raw_family(path)
        if not path.name.endswith((".parquet", ".json", ".jsonl", ".jsonl.gz")):
            raise ValueError("unsupported_raw_or_database_file")
        if path.name.endswith((".lock", ".env", ".db", ".sqlite", ".pkl")) or "manifest" in path.name:
            raise ValueError("metadata_or_database_not_raw")
        if proof.get("mode") == "unused_generation_preselection":
            if family != "cache/low_price_two_leg_ka10080":
                raise ValueError("generation_exception_family_invalid")
            if not CUTOFF <= proof["generation_end"] < proof["consumer_start"]:
                raise ValueError("generation_not_retired")
            date.fromisoformat(proof["generation_end"])
            date.fromisoformat(proof["consumer_start"])
        elif proof.get("mode") in {"payload_clock", "parquet_clock"}:
            if proof.get("unresolved_rows") != 0 or not proof.get("rows"):
                raise ValueError("payload_clock_incomplete")
            if date.fromisoformat(proof["max_date"]) >= date.fromisoformat(CUTOFF):
                raise ValueError("current_source_in_candidate")
        else:
            raise ValueError("period_evidence_invalid")
    return path


def verify_protected(files):
    for path, expected in files.items():
        if file_hash(path) != expected:
            raise ValueError(f"protected_file_changed:{path}")


def open_inodes():
    found = set()
    unobservable = []
    for process in Path("/proc").glob("[0-9]*"):
        try:
            for fd in (process / "fd").iterdir():
                try:
                    st = fd.stat()
                    if stat.S_ISREG(st.st_mode):
                        found.add((st.st_dev, st.st_ino))
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            pass
        except PermissionError:
            unobservable.append(int(process.name))
    return found, unobservable


def run(manifest_path, journal_path, *, apply=False):
    lock = WORKSPACE / "data/source_quality/file_source_retirement.apply.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _run(manifest_path, journal_path, apply=apply)


def _run(manifest_path, journal_path, *, apply=False):
    manifest_path, journal_path = Path(manifest_path), Path(journal_path)
    manifest_bytes = manifest_path.read_bytes()
    value = json.loads(manifest_bytes)
    seal = value.pop("content_sha256", None)
    if (value.get("schema") != SCHEMA or value.get("cutoff_exclusive") != CUTOFF
            or seal != digest(value)):
        raise ValueError("manifest_contract_invalid")
    protected = value["protected_files"]
    verify_protected(protected)
    entries = value["candidates"]
    paths = [_validate_entry(entry, protected) for entry in entries]
    if len(set(paths)) != len(paths):
        raise ValueError("duplicate_candidate_path")
    reader_hashes = {}
    for entry in entries:
        evidence = entry["consumer_evidence"]
        if isinstance(evidence, dict):
            for reader in evidence.get("readers", []):
                path, sha = reader["path"], reader["sha256"]
                if path in reader_hashes and reader_hashes[path] != sha:
                    raise ValueError("conflicting_consumer_receipts")
                reader_hashes[path] = sha
    verify_protected(reader_hashes)
    protected_inodes = {(Path(p).stat().st_dev, Path(p).stat().st_ino) for p in protected}
    inodes, unobservable = open_inodes()
    summary = dict(schema="file_source_retirement_result_v1", apply=apply,
                   manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                   started_at_kst=datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                   deleted_files=0, allocated_bytes=0, skipped=[], post_delete_errors=[],
                   fd_unobservable_pids=unobservable, fd_census_complete=not unobservable)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    # Do not overwrite a journal from a previous partially completed deletion.
    with journal_path.open("x") as journal:
        fcntl.flock(journal, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for index, (entry, path) in enumerate(zip(entries, paths)):
            result = dict(path=str(path), status="verified_dry_run")
            parent = fd = None
            deleted = False
            try:
                # An inaccessible process may hold the candidate open. Do not
                # certify a dry run or unlink with an incomplete census.
                if unobservable:
                    raise ValueError("fd_census_incomplete")
                parent = _parent_fd(path)
                fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
                before = os.fstat(fd)
                if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                        or identity(before) != entry["identity"]):
                    raise ValueError("identity_changed_or_linked")
                if (before.st_dev, before.st_ino) in inodes | protected_inodes:
                    raise ValueError("open_or_protected_inode")
                with os.fdopen(os.dup(fd), "rb") as handle:
                    actual = hashlib.file_digest(handle, "sha256").hexdigest()
                if actual != entry["sha256"]:
                    raise ValueError("source_content_changed")
                now = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if (identity(now) != identity(before) or path.resolve() != path
                        or identity(path.lstat()) != identity(before)):
                    raise ValueError("source_changed_during_verification")
                if apply:
                    # Evidence is durable before the irreversible operation.
                    journal.write(json.dumps(dict(result, status="delete_intent", identity=entry["identity"])) + "\n")
                    journal.flush()
                    os.fsync(journal.fileno())
                    os.unlink(path.name, dir_fd=parent)
                    deleted = True
                    result["status"] = "deleted"
                    summary["deleted_files"] += 1
                    summary["allocated_bytes"] += before.st_blocks * 512
                    os.fsync(parent)
            except (OSError, ValueError) as exc:
                if deleted:
                    result.update(status="deleted_durability_unconfirmed", reason=str(exc))
                    summary["post_delete_errors"].append(result)
                else:
                    result.update(status="skipped", reason=str(exc))
                    summary["skipped"].append(result)
            finally:
                if fd is not None:
                    os.close(fd)
                if parent is not None:
                    os.close(parent)
            journal.write(json.dumps(result) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
            if deleted and result["status"] == "deleted_durability_unconfirmed":
                summary["remaining_unprocessed"] = len(entries) - index - 1
                summary["stopped_reason"] = "post_delete_durability_failure"
                break
    verify_protected(protected)
    verify_protected(reader_hashes)
    summary["protected_hashes_verified"] = len(protected)
    summary["finished_at_kst"] = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    result = run(args.manifest, args.journal, apply=args.apply)
    print(json.dumps(result, indent=2))
    return 1 if result["skipped"] or result["post_delete_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
