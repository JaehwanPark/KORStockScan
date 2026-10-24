"""Current code capability evidence for immutable historical native reports.

This additive reader never changes reports, policy selection, or runtime authority.
The old contract remains historical; the current fixture is independently verified.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
import stat
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.scalping.main_stop_policy import bounded_object

ROOT = Path(__file__).resolve().parents[3]
PLANS = {
    "entry_cancel_wait": [
        "src/tests/test_entry_cancel_wait_tuning.py",
        "src/tests/test_entry_cancel_wait_runtime.py",
        "src/tests/test_entry_cancel_wait_attribution.py",
    ],
    "rising_missed": [
        "src/tests/test_rising_missed_classifier_prior.py",
        "src/tests/test_rising_missed_intraday_feedback.py",
    ],
    "holding_vote": [
        "src/tests/test_holding_path_vote_replay.py",
        "src/tests/test_holding_vote_numeric_successor.py",
        "src/tests/test_holding_exit_vote.py",
    ],
    "auxiliary": [
        "src/tests/test_reversal_auxiliary_tuning.py",
        "src/tests/test_reversal_auxiliary_transition.py",
        "src/tests/test_reversal_cumulative_policy.py",
    ],
}
AUTHORITY_FALSE = (
    "runtime_effect",
    "allowed_runtime_apply",
    "actual_pid_consumed",
    "actual_profit_verified",
    "policy_published",
)
NATIVE_REPORT_LIMIT = 8 * 1024 * 1024
NATIVE_REPORT_LOGICAL_LIMIT = 16 * 1024 * 1024


def publish_native_report_projection(data, family, day):
    """Preserve original JSON with its existing lossless native archive contract.

    The warm physical read stays8MiB. This bounded migration verifies complete
    original bytes, native source semantics and gzip CRC/hash before publication.
    """
    import gzip
    import tempfile
    from src.engine.lifecycle import snapshot_archive as archive
    from src.engine.scalping import entry_split_monitor_projection as files
    from src.utils.jsonl_io import json_artifact_generation_lock

    path = native_report_path(Path(data).resolve(), family, day)
    if path.resolve() != path:
        raise ValueError("native_report_canonical_path_required")
    with json_artifact_generation_lock(path, exclusive=True):
        before = archive.file_identity(path.lstat())
        raw = file_bytes(path, NATIVE_REPORT_LOGICAL_LIMIT)
        payload = json.loads(raw)
        native = (
            payload["holding_path_vote_replay"] if family == "holding_vote" else payload
        )
        observed = generation.inspect(
            native.get("policy_generation"),
            family=family,
            day=day,
            payload=native,
            data_root=Path(data),
        )
        if (
            observed.get("status") not in {"verified", "unverified"}
            or not observed.get("observation_complete")
            or observed.get("missing_components")
        ):
            raise ValueError("native_report_source_contract_invalid")
        encoded = gzip.compress(raw, mtime=0)
        if len(encoded) > NATIVE_REPORT_LIMIT or gzip.decompress(encoded) != raw:
            raise ValueError("native_report_archive_budget_or_roundtrip_invalid")
        destination = Path(str(path) + ".gz")
        if destination.exists() or destination.is_symlink():
            import io

            existing = file_bytes(destination, NATIVE_REPORT_LIMIT)
            with gzip.GzipFile(fileobj=io.BytesIO(existing)) as stream:
                restored = stream.read(len(raw) + 1)
            if restored != raw:
                raise ValueError("native_report_existing_archive_preserved")
            encoded = existing
        else:
            descriptor, temporary = tempfile.mkstemp(
                prefix=destination.name + ".", dir=path.parent
            )
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.link(temporary, destination)
            finally:
                Path(temporary).unlink(missing_ok=True)
        if archive.file_identity(path.lstat()) != before:
            raise ValueError("native_report_source_changed_during_archive")
        receipt = dict(
            schema=archive.SCHEMA,
            logical_path=str(path),
            logical_content_sha256=hashlib.sha256(raw).hexdigest(),
            logical_size_bytes=len(raw),
            original_identity=before,
            archive_generation=archive.file_identity(destination.lstat()),
            archive_sha256=hashlib.sha256(encoded).hexdigest(),
            runtime_effect=False,
            allowed_runtime_apply=False,
        )
        receipt["artifact_content_sha256"] = generation.digest(receipt)
        files._write_atomic(
            Path(str(destination) + ".archive_receipt.json"),
            receipt,
            65536,
            immutable=True,
        )
        if (
            read_native_report(data, family, day)[1]
            != receipt["logical_content_sha256"]
        ):
            raise ValueError("native_report_archive_publication_invalid")
        return receipt


def read_native_report(data, family, day):
    """Read bounded physical bytes and verify the original native JSON identity."""
    import gzip
    import io
    from src.engine.lifecycle import snapshot_archive as archive

    path = native_report_path(Path(data).resolve(), family, day)
    if path.resolve() != path:
        raise ValueError("native_report_canonical_path_required")
    before = archive.file_identity(path.lstat())
    if before["size"] <= NATIVE_REPORT_LIMIT:
        return bounded_object(path, NATIVE_REPORT_LIMIT)
    if before["size"] > NATIVE_REPORT_LOGICAL_LIMIT:
        raise ValueError("native_report_logical_source_budget_exceeded")
    archived = Path(str(path) + ".gz")
    hint, _ = bounded_object(Path(str(archived) + ".archive_receipt.json"), 65536)
    if hint.get("original_identity") != before:
        raise ValueError("native_report_original_generation_changed")
    # Hash/decode the bounded compressed bytes first, then bind their actual
    # logical generation through the existing archive verifier without a
    # second unbounded physical hash if a concurrent writer changed the file.
    encoded = file_bytes(archived, NATIVE_REPORT_LIMIT)
    with gzip.GzipFile(fileobj=io.BytesIO(encoded)) as stream:
        raw = stream.read(before["size"] + 1)
    logical_sha = hashlib.sha256(raw).hexdigest()
    receipt = archive.archived_receipt(
        path,
        bound_logical_generation=dict(
            path=path.name, size=len(raw), sha256=logical_sha
        ),
    )
    if (
        len(raw) != before["size"]
        or hashlib.sha256(raw).hexdigest() != receipt["logical_content_sha256"]
        or archive.file_identity(path.lstat()) != before
        or hashlib.sha256(encoded).hexdigest() != receipt["archive_sha256"]
    ):
        raise ValueError("native_report_archive_source_changed")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("native_report_object_required")
    return payload, receipt["logical_content_sha256"]


def _file_blocks(path, limit):
    """Hash-only protected sources need no resident JSON/evidence-sized buffer."""
    path = Path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or (
            limit is not None and before.st_size > limit
        ):
            raise ValueError("fixture_regular_bounded_file_required")
        size = 0
        for block in iter(lambda: stream.read(64 * 1024), b""):
            size += len(block)
            if size > before.st_size:
                raise ValueError("fixture_read_changed_or_limit_exceeded")
            yield block
        finished = os.fstat(stream.fileno())
        after = path.lstat()
        identity = lambda value: (
            value.st_dev,
            value.st_ino,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )
        if (
            size != before.st_size
            or identity(before) != identity(finished)
            or identity(before) != identity(after)
        ):
            raise ValueError("fixture_read_changed_or_limit_exceeded")


def file_bytes(path, limit=8 * 1024 * 1024):
    return b"".join(_file_blocks(path, limit))


def file_sha(path, limit=8 * 1024 * 1024, *, stream=False):
    sha = hashlib.sha256()
    for block in _file_blocks(path, None if stream else limit):
        sha.update(block)
    return sha.hexdigest()


def plan_identity(family):
    paths = [
        *PLANS[family],
        "src/engine/monitoring/policy_generation_validation.py",
        "src/engine/automation/policy_generation_fixture_validation.py",
    ]
    return {path: file_sha(ROOT / path) for path in paths}


def junit_counts(path, family, *, raw=None):
    root = ET.fromstring(file_bytes(path) if raw is None else raw)
    cases = list(root.iter("testcase"))
    if not cases or any(
        list(root.iter(tag)) for tag in ("failure", "error", "skipped")
    ):
        raise ValueError("fixture_tests_not_all_passed")
    covered = {case.get("classname", "").rsplit(".", 1)[-1] for case in cases}
    if not {Path(name).stem for name in PLANS[family]} <= covered:
        raise ValueError("fixture_test_plan_incomplete")
    return len(cases)


def fixture_path(data, family):
    return (
        Path(data)
        / "report/postclose_generation_validation"
        / f"{family}_{generation.code_generation(family)}.json"
    )


def verify_fixture(data, family):
    path = fixture_path(data, family)
    value, sha = bounded_object(path, 65536)
    if (
        path.is_symlink()
        or value.get("schema") != "postclose_generation_fixture_receipt_v1"
        or value.get("family") != family
        or value.get("status") != "pass"
        or value.get("code_sha256") != generation.code_generation(family)
        or value.get("closure_tests") != PLANS[family]
        or value.get("unresolved_findings") != []
        or any(value.get(key) is not False for key in AUTHORITY_FALSE)
        or value.get("provider_calls") != 0
        or type(value.get("provider_calls")) is not int
        or value.get("orders") != 0
        or type(value.get("orders")) is not int
        or value.get("receipt_sha256")
        != generation.digest({k: v for k, v in value.items() if k != "receipt_sha256"})
        or value.get("validation_plan") != plan_identity(family)
        or value.get("protected_unchanged") is not True
        or not isinstance(value.get("protected_artifact_sha256"), dict)
    ):
        raise ValueError("fixture_identity_or_authority_invalid")
    run = Path(value.get("validation_run", ""))
    expected_parent = (
        Path(data) / "report/postclose_generation_validation/runs"
    ).resolve()
    if run.is_symlink() or run.resolve().parent != expected_parent:
        raise ValueError("fixture_run_path_invalid")
    evidence = value.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != {
        "tests.log",
        "tests.xml",
        "network.json",
    }:
        raise ValueError("fixture_evidence_missing")
    raw = {name: file_bytes(run / name) for name in evidence}
    if any(
        hashlib.sha256(raw[name]).hexdigest() != digest
        for name, digest in evidence.items()
    ):
        raise ValueError("fixture_evidence_changed")
    if json.loads(raw["network.json"]) != {"blocked_attempts": 0}:
        raise ValueError("fixture_network_attempted")
    count = junit_counts(run / "tests.xml", family, raw=raw["tests.xml"])
    if type(value.get("passed_tests")) is not int or value["passed_tests"] != count:
        raise ValueError("fixture_test_count_invalid")
    return value, dict(path=str(path), sha256=sha)


def native_report_path(data, family, day):
    relative = {
        "entry_cancel_wait": f"entry_cancel_wait_tuning/entry_cancel_wait_tuning_{day}.json",
        "rising_missed": f"rising_missed_classifier_prior/rising_missed_classifier_prior_{day}.json",
        "holding_vote": f"monitor_snapshots/holding_exit_observation_{day}.json",
        "auxiliary": f"reversal_auxiliary_tuning/{day}/evaluation.json",
    }[family]
    return Path(data) / "report" / relative


def current_fixture_observation(observed, data):
    """Supplement only a valid, same-code native contract lacking its fixture.

    No original bytes are rewritten. Real source/selection/sample gaps and the
    original contract status remain visible, independently of code capability.
    """
    family = observed.get("family")
    if (
        family not in PLANS
        or observed.get("status") != "unverified"
        or observed.get("findings") != ["policy_generation_unverified"]
        or observed.get("missing_components") != []
        or observed.get("observation_complete") is not True
        or observed.get("native_validated") is not False
    ):
        return observed
    path = fixture_path(data, family)
    if not path.exists() and not path.is_symlink():
        return observed
    try:
        fixture, reference = verify_fixture(data, family)
        expected = native_report_path(data, family, observed["source_date"])
        if Path(observed["artifact"]) != expected:
            raise ValueError("fixture_native_report_path_invalid")
        payload, report_sha = read_native_report(data, family, observed["source_date"])
        native_payload = (
            payload["holding_path_vote_replay"] if family == "holding_vote" else payload
        )
        contract = native_payload["policy_generation"]
        if observed.get("binding_repair") is not None:
            contract, binding = generation._read_holding_code_rebinding(
                Path(data), observed["source_date"], report_sha, payload
            )
            if binding != observed["binding_repair"]:
                raise ValueError("fixture_report_binding_repair_changed")
        original = generation.inspect(
            contract,
            family=family,
            day=observed["source_date"],
            payload=native_payload,
            data_root=Path(data),
        )
        if (
            original["status"] != "unverified"
            or contract.get("fixture_receipt") is not None
            or report_sha != observed.get("report_sha256")
            or contract["contract_sha256"] != observed.get("contract_sha256")
            or contract["code_sha256"] != fixture["code_sha256"]
            or any(
                original[key] != observed.get(key)
                for key in (
                    "source_generation",
                    "code_sha256",
                    "source_state",
                    "comparison_state",
                    "handoff_state",
                )
            )
        ):
            raise ValueError("fixture_preserved_report_generation_changed")
        # Native producer/reader, in memory, binds the verified current fixture
        # to the same source body. It grants code capability only.
        current = generation.native(
            native_payload,
            family=family,
            day=observed["source_date"],
            data_root=Path(data),
            source_state=contract["source_state"],
            comparison_state=contract["comparison_state"],
            handoff_state=contract["handoff_state"],
        )
        verified = generation.inspect(
            current,
            family=family,
            day=observed["source_date"],
            payload=native_payload,
            data_root=Path(data),
        )
        if (
            verified["status"] != "verified"
            or current["fixture_receipt"] != reference
            or verified["source_generation"] != original["source_generation"]
        ):
            raise ValueError("fixture_native_reader_unverified")
        # Recheck the authoritative source after projection; never close a
        # concurrently replaced generation using the preceding bytes.
        if read_native_report(data, family, observed["source_date"])[1] != report_sha:
            raise ValueError("fixture_report_changed_during_validation")
        result = deepcopy(observed)
        result.update(
            status="verified",
            findings=[],
            native_validated=False,
            current_code_capability_verified=True,
            historical_contract_status="unverified",
            verification_basis="current_fixture_for_preserved_native_report",
            current_fixture=reference,
            current_capability_contract_sha256=current["contract_sha256"],
        )
        result["scopes"] = {
            family: {
                k: v
                for k, v in result.items()
                if k not in {"scopes", "family", "source_date", "artifact"}
            }
        }
        return result
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        return dict(
            observed, current_fixture_status="invalid", current_fixture_reason=str(exc)
        )
