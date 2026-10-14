"""Native-verified entry-split observation receipts; never a runtime policy source.

Only a producer/migration worker reads full reports. Readers trust its content-bound
receipt while exact source inode/ctime/size/path identity and verifier code remain
unchanged. This is a same-owner local filesystem contract, not a signed attestation
against a malicious writer able to replace both source and proof.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timezone
from typing import Any

from src.utils.constants import DATA_DIR

MANAGED_DATA_ROOT = DATA_DIR

PROJECTION_SCHEMA = "entry_split_monitor_projection_v1"
RECEIPT_SCHEMA = "entry_split_monitor_validation_v1"
MANIFEST_SCHEMA = "entry_split_monitor_generation_v1"
MAX_PROJECTION_BYTES = 512 * 1024
MAX_METADATA_BYTES = 64 * 1024
MAX_POLICY_BYTES = 8 * 1024 * 1024
MAX_WARM_METADATA_BYTES = 1024 * 1024
MAX_NATIVE_BYTES = 512 * 1024 * 1024
MAX_INPUT_BYTES = 768 * 1024 * 1024
ALLOWED_ROLES = {"submission_monitor", "runtime_summary"}


def manifest_path(report_path: Path) -> Path:
    return Path(report_path).with_suffix(".verification.json")


def _fail(reason: str) -> ValueError:
    return ValueError("entry_split_verification_invalid:" + reason)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _reject_constant(value: str):
    raise _fail("non_finite_number:" + value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _fail("duplicate_key:" + str(key)[:80])
        result[key] = value
    return result


def _strict_load(encoded: bytes) -> dict:
    value = json.loads(encoded, object_pairs_hook=_unique_object,
                       parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise _fail("object_required")
    # JSON's finite-looking exponent can overflow Python's float parser.
    def finite(item):
        if isinstance(item, float):
            import math
            if not math.isfinite(item):
                raise _fail("non_finite_number")
        elif isinstance(item, dict):
            for child in item.values(): finite(child)
        elif isinstance(item, list):
            for child in item: finite(child)
    finite(value)
    return value


def _identity(path: Path) -> dict:
    path = Path(path).absolute()
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise _fail("regular_file_required:" + path.name)
    # Parent symlinks are permitted only as a fixed trusted data mount. Record
    # both spellings and the resolved parent inode so replacement is detected.
    parent = path.parent.resolve(strict=True)
    parent_stat = parent.stat()
    return dict(path=str(path), resolved_path=str(path.resolve(strict=True)),
        parent_path=str(parent), parent_dev=parent_stat.st_dev,
        parent_ino=parent_stat.st_ino, dev=info.st_dev, ino=info.st_ino,
        size=info.st_size, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns,
        mode=info.st_mode, uid=info.st_uid, gid=info.st_gid, nlink=info.st_nlink)


def _check_identity(record: dict, path: Path | None = None) -> None:
    if not isinstance(record, dict) or not isinstance(record.get("identity"), dict):
        raise _fail("source_identity_missing")
    expected = record["identity"]
    selected = Path(path) if path is not None else Path(expected["path"])
    if _identity(selected) != expected:
        raise _fail("source_changed:" + selected.name)
    if not isinstance(record.get("sha256"), str) or len(record["sha256"]) != 64:
        raise _fail("source_hash_missing")


def _fd_matches(handle, identity: dict) -> bool:
    info = os.fstat(handle.fileno())
    return all(getattr(info, "st_" + key) == identity[key]
               for key in ("dev", "ino", "size", "mtime_ns", "ctime_ns", "mode", "uid", "gid", "nlink"))


def _read(path: Path, limit: int) -> tuple[dict, dict]:
    before = _identity(path)
    if before["size"] > limit:
        raise _fail("size_limit:" + Path(path).name)
    with Path(path).open("rb") as handle:
        if not _fd_matches(handle, before): raise _fail("read_open_race")
        encoded = handle.read(limit + 1)
        if not _fd_matches(handle, before): raise _fail("read_mutation")
    if _identity(path) != before or len(encoded) > limit:
        raise _fail("read_mutation")
    result = _strict_load(encoded)
    return result, dict(identity=before, sha256=hashlib.sha256(encoded).hexdigest())


def publication_file_receipt(path: Path) -> dict:
    """Cold writer-only byte hash; observation readers never call this."""
    before = _identity(path)
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        if not _fd_matches(handle, before): raise _fail("hash_open_race")
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
        if not _fd_matches(handle, before): raise _fail("hash_mutation")
    if _identity(path) != before: raise _fail("hash_mutation")
    return dict(identity=before, sha256=hasher.hexdigest())


def _code_identity() -> dict:
    from src.engine.scalping import entry_split_order_plan as native
    return {"projection_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
            "verification_contract": "full_native_pair_then_exact_source_identity_v1"}


def _collection_count(value):
    if isinstance(value, (list, dict)): return len(value)
    if type(value) is int and value >= 0: return value
    return None


def _without_bulk(value: dict, fields: set[str]) -> tuple[dict, dict]:
    removed = {key: item for key, item in value.items()
               if key in fields and isinstance(item, (list, dict))}
    selected = {key: copy.deepcopy(item) for key, item in value.items() if key not in removed}
    omitted = {key: {"count": _collection_count(item), "sha256": _digest(item)}
               for key, item in removed.items()}
    return selected, omitted


def build_projection(report: dict, policy: dict) -> dict:
    """Preserve consumed metrics exactly, with explicit counts for omitted rows."""
    economic = report.get("economic_acceptance") or {}
    if not isinstance(economic, dict): raise _fail("economic_section_invalid")
    economic, omitted = _without_bulk(economic, {
        "input_rows", "model_rows", "model_scopes", "cohort_checks", "candidates", "consumed_holdouts"})
    original = report.get("economic_acceptance") or {}
    if "candidate_count" not in economic and isinstance(original.get("candidates"), list):
        economic["candidate_count"] = len(original["candidates"])
    economic["projection_omitted"] = omitted
    economic["model_row_count"] = _collection_count(original.get("model_rows"))
    economic["consumed_holdout_count"] = _collection_count(original.get("consumed_holdouts"))
    recommended, rec_omitted = _without_bulk(report.get("recommended_policy") or {}, {"candidates"})
    recommended["projection_omitted"] = rec_omitted
    cumulative = report.get("cumulative_state") or {}
    refresh = report.get("execution_model_refresh") or {}
    original_producer = {key: copy.deepcopy(report.get(key))
                         for key in ("code_commit", "producer_code_sha", "producer_code_hash")}
    original_producer["execution_model_refresh.model_implementation_sha256"] = (
        copy.deepcopy(refresh.get("model_implementation_sha256")) if isinstance(refresh, dict) else None)
    original_producer["status"] = ("recorded_refs_not_recomputed"
        if any(value is not None for value in original_producer.values()) else "not_recorded")
    original_producer["source"] = "native_verified_full_report_fields"
    original_producer["historical_code_replayed"] = False
    result = {key: copy.deepcopy(report[key]) for key in (
        "schema_version", "report_type", "date", "source_date", "generated_at", "publication_date",
        "effective_date", "prepared_effective_date", "status", "comparison_status", "selection_status",
        "decision", "conclusion", "evaluation_state", "blocked_reason", "metric_role",
        "artifact_generation_binding") if key in report}
    result.update(economic_acceptance=economic, recommended_policy=recommended,
        cumulative_state={key: copy.deepcopy(cumulative[key]) for key in (
            "clean_tuning_baseline_date", "source_dates", "schema_version") if key in cumulative},
        operating_candidate_count=len(report.get("operating_candidate_grid") or []),
        observation_projection={"schema": PROJECTION_SCHEMA, "decision_authority": "report_only",
            "metric_role": "source_quality_gate",
            "window_policy": "same_source_date_and_exact_generation",
            "sample_floor": "none_for_contract_validation",
            "primary_decision_metric": "native_report_policy_binding",
            "source_quality_gate": "full_native_validation_and_exact_source_identity",
            "forbidden_uses": ["policy_promotion", "order_authority", "realized_pnl", "missing_as_zero"],
            "runtime_effect": False, "allowed_runtime_apply": False,
            "full_native_report": False, "rows_omitted": True,
            "policy_runtime_apply_allowed": policy.get("runtime_apply_allowed"),
            "original_producer": original_producer})
    if len(_canonical(result)) > MAX_PROJECTION_BYTES: raise _fail("projection_size_limit")
    return result


def _write_atomic(path: Path, value: dict, limit: int, *, immutable=False) -> dict:
    if path.is_symlink(): raise _fail("metadata_symlink")
    encoded = _canonical(value) + b"\n"
    if len(encoded) > limit: raise _fail("metadata_size_limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        if path.is_symlink() or path.read_bytes() != encoded: raise _fail("immutable_collision")
        return publication_file_receipt(path)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return publication_file_receipt(path)


def _paths(report_path: Path, policy_path: Path, day: str, generation: str) -> dict:
    root = Path(MANAGED_DATA_ROOT).resolve(strict=True)
    expected = {
        "report_alias": root / "report" / "entry_split_order_plan" / f"entry_split_order_plan_{day}.json",
        "policy_alias": root / "threshold_cycle" / "entry_split_order_policy" / f"entry_split_order_policy_{day}.json",
    }
    for key, selected in (("report_alias", report_path), ("policy_alias", policy_path)):
        selected = Path(selected).absolute()
        # Resolve the trusted data mount once. Every child below it must be a
        # plain directory/file, and the requested date/family path is exact.
        if selected != expected[key] or selected.resolve(strict=True) != expected[key]:
            raise _fail("managed_source_path:" + key)
        current = expected[key]
        while current != root:
            if current.is_symlink(): raise _fail("managed_child_symlink")
            current = current.parent
        expected[key] = selected
    expected["immutable_report"] = Path(report_path).absolute().parent / "generations" / f"entry_split_order_plan_{day}_{generation}.json"
    expected["immutable_policy"] = Path(policy_path).absolute().parent / "generations" / f"entry_split_order_policy_{day}_{generation}.json"
    for key in ("immutable_report", "immutable_policy"):
        if expected[key].is_symlink() or expected[key].parent.is_symlink():
            raise _fail("managed_immutable_symlink")
    return expected


def _publish(projection: dict, records: dict, binding: dict, day: str,
             native_validation: dict, migration: dict | None = None, *, verified_code: dict) -> dict:
    if _code_identity() != verified_code: raise _fail("verifier_changed_during_validation")
    for record in records.values(): _check_identity(record)
    generation = binding["generation_id"]
    report_path = Path(records["report_alias"]["identity"]["path"])
    identity = _digest({"records": records, "code": verified_code, "projection": projection,
                        "migration": migration})
    base = report_path.parent / "generations" / f"entry_split_monitor_{day}_{generation}_{identity}"
    projection_record = _write_atomic(base.with_suffix(".projection.json"), projection, MAX_PROJECTION_BYTES, immutable=True)
    receipt = dict(schema=RECEIPT_SCHEMA, source_date=day, generation_id=generation,
        validated_at=datetime.now(timezone.utc).isoformat(), native_validation=native_validation,
        records=records, projection=projection_record, code=verified_code, migration=migration,
        binding=binding, decision_authority="report_only", runtime_effect=False, allowed_runtime_apply=False)
    receipt_path = base.with_suffix(".receipt.json")
    if receipt_path.exists():
        previous, _ = _read(receipt_path, MAX_METADATA_BYTES)
        if {key: value for key, value in previous.items() if key != "validated_at"} != {
                key: value for key, value in receipt.items() if key != "validated_at"}:
            raise _fail("immutable_receipt_collision")
        receipt["validated_at"] = previous["validated_at"]
    receipt_record = _write_atomic(receipt_path, receipt, MAX_METADATA_BYTES, immutable=True)
    for record in records.values(): _check_identity(record)
    pointer = dict(schema=MANIFEST_SCHEMA, source_date=day, generation_id=generation,
        receipt=receipt_record, projection=projection_record, code=verified_code,
        decision_authority="report_only", runtime_effect=False, allowed_runtime_apply=False)
    if _code_identity() != verified_code: raise _fail("verifier_changed_during_validation")
    _write_atomic(manifest_path(report_path), pointer, MAX_METADATA_BYTES)
    if _code_identity() != verified_code: raise _fail("verifier_changed_during_validation")
    return {"verified": True, "source_date": day, "generation_id": generation,
            "report_sha256": records["report_alias"]["sha256"], "manifest": str(manifest_path(report_path)),
            "projection_bytes": projection_record["identity"]["size"]}


def _observation_authority(value: dict) -> bool:
    return (value.get("decision_authority") == "report_only"
            and value.get("runtime_effect") is False
            and value.get("allowed_runtime_apply") is False)


def read_verified_projection(report_path: Path, policy_path: Path, *, source_date: str,
                             role: str) -> tuple[dict, dict]:
    """Bounded cross-process reuse; never read/hash/parse the full report."""
    started = time.monotonic()
    if role not in ALLOWED_ROLES: raise _fail("consumer_role_invalid")
    if date.fromisoformat(source_date).isoformat() != source_date: raise _fail("date_invalid")
    pointer_path = manifest_path(report_path)
    if not pointer_path.exists():
        raise ValueError("entry_split_verification_pending:manifest_missing")
    pointer, pointer_record = _read(pointer_path, MAX_METADATA_BYTES)
    if (pointer.get("schema") != MANIFEST_SCHEMA or pointer.get("source_date") != source_date
            or pointer.get("code") != _code_identity()
            or not _observation_authority(pointer)): raise _fail("manifest_contract")
    generation = pointer.get("generation_id")
    if not isinstance(generation, str) or len(generation) != 64 or any(c not in "0123456789abcdef" for c in generation):
        raise _fail("generation_invalid")
    parent = Path(report_path).absolute().parent.resolve(strict=True) / "generations"
    def child(record, suffix, limit):
        path = Path(record["identity"]["path"])
        if path.parent.resolve(strict=True) != parent or not path.name.endswith(suffix):
            raise _fail("metadata_path_escape")
        _check_identity(record, path)
        value, observed = _read(path, limit)
        if observed != record: raise _fail("metadata_content_mismatch")
        return value
    receipt = child(pointer["receipt"], ".receipt.json", MAX_METADATA_BYTES)
    if (receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("source_date") != source_date
            or receipt.get("generation_id") != generation or receipt.get("code") != _code_identity()
            or receipt.get("projection") != pointer.get("projection")
            or not _observation_authority(receipt)
            or (receipt.get("native_validation") or {}).get("status") != "verified"
            or (receipt.get("native_validation") or {}).get("scope") != "full_report_policy_native_contract"):
        raise _fail("receipt_contract")
    expected = _paths(report_path, policy_path, source_date, generation)
    records = receipt.get("records") or {}
    if set(records) != set(expected): raise _fail("source_inventory")
    for key, path in expected.items(): _check_identity(records[key], path)
    metadata_bytes = sum(record["identity"]["size"] for record in (
        pointer_record, pointer["receipt"], pointer["projection"], records["policy_alias"]))
    if metadata_bytes > MAX_WARM_METADATA_BYTES: raise _fail("warm_metadata_size_limit")
    projection = child(pointer["projection"], ".projection.json", MAX_PROJECTION_BYTES)
    policy, policy_record = _read(Path(policy_path), MAX_POLICY_BYTES)
    if policy_record != records["policy_alias"]: raise _fail("policy_content_changed")
    binding = receipt.get("binding")
    if (projection.get("date") != source_date or policy.get("source_date") != source_date
            or projection.get("artifact_generation_binding") != binding
            or policy.get("artifact_generation_binding") != binding
            or (binding or {}).get("generation_id") != generation
            or (projection.get("observation_projection") or {}).get("full_native_report") is not False
            or not _observation_authority(projection.get("observation_projection") or {})):
        raise _fail("projection_binding")
    for key, path in expected.items(): _check_identity(records[key], path)
    _check_identity(pointer["receipt"])
    _check_identity(pointer["projection"])
    if _identity(pointer_path) != pointer_record["identity"]: raise _fail("manifest_changed_during_read")
    return projection, dict(verified=True, role=role, source_date=source_date, generation_id=generation,
        report_sha256=records["report_alias"]["sha256"], policy_sha256=policy_record["sha256"],
        native_validation=receipt["native_validation"], manifest_path=str(pointer_path),
        manifest_sha256=pointer_record["sha256"], _validated_policy=policy,
        full_report_bytes_read=0, metadata_bytes_read=metadata_bytes,
        consumer_elapsed_ms=round((time.monotonic() - started) * 1000, 3))


def _compact_copy(source: Path, output: Path, *, max_input_bytes=MAX_INPUT_BYTES,
                  max_output_bytes=MAX_NATIVE_BYTES) -> tuple[dict, dict]:
    before = _identity(source)
    if before["size"] > max_input_bytes: raise _fail("migration_input_size_limit")
    if output.exists(): raise _fail("migration_temporary_exists")
    if shutil.disk_usage(output.parent).free < min(before["size"], max_output_bytes) + 64 * 1024 * 1024:
        raise _fail("migration_temporary_disk_budget")
    hasher = hashlib.sha256(); out_hasher = hashlib.sha256(); written = 0
    quoted = escaped = whitespace = False
    with Path(source).open("rb") as incoming, output.open("xb") as outgoing:
        if not _fd_matches(incoming, before): raise _fail("migration_open_race")
        for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
            hasher.update(chunk)
            kept = bytearray()
            for byte in chunk:
                if quoted:
                    kept.append(byte)
                    if escaped: escaped = False
                    elif byte == 92: escaped = True
                    elif byte == 34: quoted = False
                elif byte in (32, 9, 10, 13):
                    # Keep the first byte of a whitespace run. Removing the
                    # entire separator would silently repair malformed primitive
                    # tokens (1 2 -> 12, - 1 -> -1, 1e +2 -> 1e+2).
                    if not whitespace: kept.append(byte)
                    whitespace = True
                else:
                    whitespace = False
                    if byte == 34: quoted = True
                    kept.append(byte)
            written += len(kept)
            if written > max_output_bytes: raise _fail("migration_output_size_limit")
            outgoing.write(kept); out_hasher.update(kept)
        outgoing.flush(); os.fsync(outgoing.fileno())
        if not _fd_matches(incoming, before): raise _fail("migration_mutation")
    if _identity(source) != before: raise _fail("migration_mutation")
    return (dict(identity=before, sha256=hasher.hexdigest()),
            {"sha256": out_hasher.hexdigest(), "size_bytes": written,
             "transform": "collapse_ascii_json_whitespace_runs_outside_strings_v1"})


def migrate_verification(report_path: Path, policy_path: Path, *, source_date: str,
                         max_input_bytes=MAX_INPUT_BYTES, temporary_root: Path | None = None) -> dict:
    """One cold sequential native verification of alias and immutable sources."""
    from src.engine.scalping import entry_split_order_plan as native
    if date.fromisoformat(source_date).isoformat() != source_date: raise _fail("date_invalid")
    report_path = Path(report_path).absolute(); policy_path = Path(policy_path).absolute()
    _paths(report_path, policy_path, source_date, "0" * 64)
    # Retry an already verified exact-byte generation without repeating cold IO.
    if manifest_path(report_path).exists():
        try:
            _, prior = read_verified_projection(report_path, policy_path,
                source_date=source_date, role="runtime_summary")
            prior.pop("_validated_policy", None)
            prior["reused_verified_receipt"] = True
            return prior
        except (OSError, ValueError, TypeError, KeyError):
            pass
    lock_path = report_path.parent / f".entry_split_model_refresh_{source_date}.lock"
    with lock_path.open("a") as lock:
        try: fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise _fail("producer_lock_busy") from exc
        verified_code = _code_identity()
        policy, policy_record = _read(policy_path, MAX_POLICY_BYTES)
        binding = policy.get("artifact_generation_binding") or {}
        generation = binding.get("generation_id")
        if (not native._valid_generation_id(generation) or policy.get("source_date") != source_date):
            raise _fail("policy_generation_or_date")
        paths = _paths(report_path, policy_path, source_date, generation)
        immutable_policy, immutable_policy_record = _read(paths["immutable_policy"], MAX_POLICY_BYTES)
        if immutable_policy != policy: raise _fail("immutable_policy_mismatch")
        projections = []; records = {"policy_alias": policy_record, "immutable_policy": immutable_policy_record}
        transforms = {}
        started = time.monotonic()
        for key in ("report_alias", "immutable_report"):
            source = paths[key]
            with tempfile.TemporaryDirectory(prefix=".entry-split-native-", dir=temporary_root or report_path.parent) as temporary:
                compact = Path(temporary) / "native.json"
                source_record, transform = _compact_copy(source, compact, max_input_bytes=max_input_bytes)
                report, _ = _read(compact, MAX_NATIVE_BYTES)
                if report.get("date") != source_date: raise _fail("report_date")
                valid, reason = native.validate_report_policy_generation(report, policy)
                if not valid: raise _fail(reason)
                if _code_identity() != verified_code: raise _fail("verifier_changed_during_validation")
                projections.append(build_projection(report, policy)); records[key] = source_record
                transforms[key] = transform
                del report
                gc.collect()
        if projections[0] != projections[1]: raise _fail("alias_immutable_projection_mismatch")
        return _publish(projections[0], records, binding, source_date,
            {"status": "verified", "reason": "generation_binding_valid",
             "scope": "full_report_policy_native_contract"},
            migration={"input_bytes": sum(records[k]["identity"]["size"] for k in ("report_alias", "immutable_report")),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "temporary_transform": transforms, "sequential_full_objects": True}, verified_code=verified_code)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=DATA_DIR)
    parser.add_argument("--wall-seconds", type=int, default=300)
    parser.add_argument("--memory-mib", type=int, default=4096)
    parser.add_argument("--max-input-mib", type=int, default=768)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--temporary-root", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    global MANAGED_DATA_ROOT
    MANAGED_DATA_ROOT = args.data_root.resolve(strict=True)
    if not (1 <= args.wall_seconds <= 600 and 256 <= args.memory_mib <= 6144
            and 1 <= args.max_input_mib <= 1024): parser.error("bounded worker resource limits required")
    try:
        if date.fromisoformat(args.source_date).isoformat() != args.source_date: raise _fail("date_invalid")
        _paths(args.report, args.policy, args.source_date, "0" * 64)
    except (OSError, ValueError) as exc:
        print(json.dumps({"verified": False, "reason": str(exc)[:240]})); return 1
    if not args.worker:
        command = [sys.executable, "-m", __name__ if __name__ != "__main__" else "src.engine.scalping.entry_split_monitor_projection",
            "--worker", "--source-date", args.source_date, "--report", str(args.report), "--policy", str(args.policy),
            "--data-root", str(MANAGED_DATA_ROOT), "--wall-seconds", str(args.wall_seconds), "--memory-mib", str(args.memory_mib), "--max-input-mib", str(args.max_input_mib)]
        with tempfile.TemporaryDirectory(prefix=".entry-split-supervisor-", dir=args.report.absolute().parent) as temporary:
            command += ["--temporary-root", temporary]
            try:
                result = subprocess.run(command, timeout=args.wall_seconds, check=False)
                return result.returncode
            except subprocess.TimeoutExpired:
                print(json.dumps({"verified": False, "reason": "entry_split_migration_wall_limit"})); return 1
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mib * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (args.wall_seconds, args.wall_seconds + 1))
    try:
        result = migrate_verification(args.report, args.policy, source_date=args.source_date,
            max_input_bytes=args.max_input_mib * 1024 * 1024, temporary_root=args.temporary_root)
        print(json.dumps(result, sort_keys=True)); return 0
    except (OSError, ValueError, TypeError, KeyError, MemoryError) as exc:
        print(json.dumps({"verified": False, "reason": str(exc)[:240] or type(exc).__name__})); return 1


if __name__ == "__main__":
    raise SystemExit(main())
