"""Materialize compact, source-only main-bot lifecycle rows.

The default producer makes one streaming pass over the existing pipeline event
file and consumes only strict stages carrying an explicit lifecycle identity.
An explicit transition journal remains a supported audit/test source.  The
producer never reconstructs identity from symbol or time proximity and never
grants runtime, order, provider, threshold, or promotion authority.
"""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import heapq
import json
import math
import os
import re
import stat
import tempfile
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping.main_lifecycle_journal import (
    AUTHORITY_CONTRACT,
    BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC,
    BROKER_EXECUTION_MAX_RECEIVE_LAG_SEC,
    BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE,
    BROKER_EXECUTION_ORDERING_TIME_SOURCE,
    BROKER_EXECUTION_PROVENANCE_SCHEMA,
    BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA,
    BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
    BROKER_EXECUTION_TIMING_SCHEMA,
    CARRY_IN_CUSTODY_SCHEMA,
    JOURNAL_SCHEMA,
    KIWOOM_OFFICIAL_REFERENCE_SHA,
    PIPELINE_IDENTITY_SCHEMA,
    PIPELINE_STAGE_MAP,
    SHA256_RE,
    VALID_STAGES,
    build_broker_execution_provenance,
    build_transition,
    canonical_submitted_order_qty_list,
    normalize_submitted_order_quantities,
    validate_main_lifecycle_id,
)
from src.utils.constants import DATA_DIR

REPORT_SCHEMA = "main_scalping_lifecycle_paired_daily_v2"
LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_lifecycle_window_exclusion_manifest_v1"
)
PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_pipeline_owner_exclusion_manifest_v1"
)
REPORT_DIR = DATA_DIR / "report" / "main_scalping_lifecycle_paired"
PIPELINE_EVENT_DIR = DATA_DIR / "pipeline_events"

_TRACE_ID_LIMIT = 256
_GAP_EXAMPLE_LIMIT = 20
_EVENT_ID_LIMIT_PER_LIFECYCLE = 4_096
MAX_LIFECYCLE_ACCUMULATORS = 50_000
MAX_TRANSITION_EVENT_IDENTITIES = 500_000
LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC = 300.0
PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS = 1_000
_QUANTITY_EPSILON = 1e-8
_BROKER_SUBMIT_CLOCK_SKEW_SEC = 2
KST = ZoneInfo("Asia/Seoul")
LIFECYCLE_POPULATION_REAL_SUBMITTED = "real_submitted"
LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION = "candidate_observation"
LIFECYCLE_POPULATION_SCOPES = frozenset(
    {
        LIFECYCLE_POPULATION_REAL_SUBMITTED,
        LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION,
    }
)
PIPELINE_SOURCE_POPULATION_SCOPES = frozenset(
    {"real_record_bound", "sim_observation_only"}
)
LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE = date(2026, 8, 25)
HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA = (
    "historical_fill_before_submit_diagnostic_recovery_v1"
)
HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA = (
    "historical_legacy_exit_submission_diagnostic_recovery_v1"
)
HISTORICAL_DIAGNOSTIC_RECOVERY_DATA_FIELD_PREFIXES = (
    "historical_fill_before_submit_diagnostic_",
    "historical_legacy_exit_submission_diagnostic_",
)
HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_NONPROMOTION_BLOCKER = (
    "historical_fill_before_submit_diagnostic_recovery_non_promotable"
)
SUBMISSION_CUSTODY_BINDING_SCHEMA = "broker_execution_inferred_submission_binding_v1"
SUBMISSION_CUSTODY_SOURCE_STAGES = frozenset(
    {
        "entry_execution_receipt_submission_custody",
        "scale_in_execution_receipt_submission_custody",
        "exit_execution_receipt_submission_custody",
    }
)
SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES = (
    "lifecycle_submission_ordering_clock",
    "submission_causal_upper_bound_at",
    "submission_causal_upper_bound_source",
    "submission_custody_binding_schema",
    "submission_custody_broker_order_no",
    "submission_custody_broker_execution_no",
    "submission_custody_broker_order_qty",
    "submission_custody_broker_cumulative_qty",
    "submission_custody_broker_remaining_qty",
    "submission_custody_broker_unit_qty",
)
TRANSFORMED_SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES = tuple(
    (
        "submission_ordering_clock"
        if field == "lifecycle_submission_ordering_clock"
        else field
    )
    for field in SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES
)
_REQUIRED_COMPLETE_STAGES = frozenset(
    {
        "scanner",
        "entry_decision",
        "submit",
        "fill",
        "holding",
        "scale_in",
        "exit",
    }
)

REPORT_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "main_scalping_lifecycle_paired_source_quality",
    "decision_authority": "source_only_candidate_evidence",
    "window_policy": "exact_trade_date_scanner_attempt_to_reconciled_final_exit",
    "sample_floor": "one_complete_exact_lineage_lifecycle",
    "primary_decision_metric": "complete_reconciled_lifecycle_coverage",
    "source_quality_gate": (
        "exact_lineage_complete_lifecycle_reconciled_cost_symbol_and_market_depth"
    ),
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "direct_runtime_or_order_apply",
        "provider_model_bot_threshold_price_quantity_or_cap_change",
        "hard_safety_or_broker_guard_bypass",
        "cross_attempt_symbol_or_timestamp_join",
        "label_horizon_as_actual_holding_duration",
        "raw_fallback_without_explicit_main_lifecycle_id_for_promotion",
    ],
}

PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "source_quality_gate",
    "decision_authority": "pipeline_owner_window_exclusion_only",
    "window_policy": "exact_trade_date_record_id_and_stock_code",
    "sample_floor": "not_applicable_source_quality_manifest",
    "primary_decision_metric": "excluded_pipeline_owner_count",
    "source_quality_gate": "missing_explicit_lifecycle_identity_owner_quarantine",
    "exclusion_scope": "exact_pipeline_owner_window",
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "infer_or_reconstruct_main_lifecycle_id",
        "join_by_symbol_or_timestamp_proximity",
        "exclude_other_clean_pipeline_owner_windows",
        "direct_runtime_or_order_apply",
    ],
}


def paired_report_path(target_date: str | date) -> Path:
    """Return the daily compact artifact path."""

    value = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    value = date.fromisoformat(value).isoformat()
    return REPORT_DIR / f"main_scalping_lifecycle_paired_{value}.json"


def report_path(target_date: str | date) -> Path:
    """Return the stable orchestration name for the daily report path."""

    return paired_report_path(target_date)


def pipeline_event_path(target_date: str | date) -> Path:
    """Return the existing live pipeline stream used by the default producer."""

    value = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    value = date.fromisoformat(value).isoformat()
    return PIPELINE_EVENT_DIR / f"pipeline_events_{value}.jsonl"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


class _DigestingReader:
    """Proxy a binary source while hashing exactly the bytes read once."""

    def __init__(self, raw: BinaryIO, *, aggregate_hasher: Any | None = None) -> None:
        self._raw = raw
        self._hasher = hashlib.sha256()
        self._aggregate_hasher = aggregate_hasher
        self.byte_count = 0

    def _record(self, payload: bytes) -> bytes:
        if payload:
            self._hasher.update(payload)
            if self._aggregate_hasher is not None:
                self._aggregate_hasher.update(payload)
            self.byte_count += len(payload)
        return payload

    def read(self, size: int = -1) -> bytes:
        return self._record(self._raw.read(size))

    def readline(self, size: int = -1) -> bytes:
        return self._record(self._raw.readline(size))

    def readable(self) -> bool:
        return True

    @property
    def digest(self) -> str:
        return self._hasher.hexdigest()


@dataclass
class _StreamCensus:
    source_path: str
    source_exists: bool = False
    source_is_gzip: bool = False
    source_part_count: int = 0
    source_raw_sha256: str = field(
        default_factory=lambda: hashlib.sha256(b"").hexdigest()
    )
    source_raw_bytes: int = 0
    source_decoded_sha256: str = field(
        default_factory=lambda: hashlib.sha256(b"").hexdigest()
    )
    source_decoded_bytes: int = 0
    physical_line_count: int = 0
    blank_line_count: int = 0
    json_object_count: int = 0
    malformed_json_count: int = 0
    non_object_count: int = 0
    source_read_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_exists": self.source_exists,
            "source_is_gzip": self.source_is_gzip,
            "source_part_count": self.source_part_count,
            "source_raw_sha256": self.source_raw_sha256,
            "source_raw_bytes": self.source_raw_bytes,
            "source_decoded_sha256": self.source_decoded_sha256,
            "source_decoded_bytes": self.source_decoded_bytes,
            "physical_line_count": self.physical_line_count,
            "blank_line_count": self.blank_line_count,
            "json_object_count": self.json_object_count,
            "malformed_json_count": self.malformed_json_count,
            "non_object_count": self.non_object_count,
            "source_read_error": self.source_read_error,
        }


def _resolve_source_paths(
    path: Path,
    *,
    parent_descriptor: int | None = None,
) -> list[Path]:
    """Return every physical part of one logical JSONL partition."""

    logical = path.with_name(path.name.removesuffix(".gz"))
    if logical.suffix != ".jsonl":
        return (
            [path]
            if _path_entry_exists(path, parent_descriptor=parent_descriptor)
            else []
        )
    gzip_path = logical.with_name(logical.name + ".gz")
    late_path = logical.with_name(f"{logical.stem}.late.jsonl")
    late_gzip_path = late_path.with_name(late_path.name + ".gz")
    base_parts: list[Path]
    if (
        _path_entry_exists(gzip_path, parent_descriptor=parent_descriptor)
        and _path_entry_exists(logical, parent_descriptor=parent_descriptor)
        and _same_decoded_bytes(
            gzip_path,
            logical,
            parent_descriptor=parent_descriptor,
        )
    ):
        # A crash after verified gzip publication but before source unlink can
        # leave byte-equivalent dual representations.  They are one physical
        # source generation, not two logical event streams.
        base_parts = [gzip_path]
    else:
        base_parts = [
            candidate
            for candidate in (gzip_path, logical)
            if _path_entry_exists(candidate, parent_descriptor=parent_descriptor)
        ]
    late_parts: list[Path]
    if (
        _path_entry_exists(late_gzip_path, parent_descriptor=parent_descriptor)
        and _path_entry_exists(late_path, parent_descriptor=parent_descriptor)
        and _same_decoded_bytes(
            late_gzip_path,
            late_path,
            parent_descriptor=parent_descriptor,
        )
    ):
        # The late overlay is independently compacted. Apply the same
        # crash-after-publish dedupe as the base partition so one append is not
        # counted twice when gzip publication completed before source unlink.
        late_parts = [late_gzip_path]
    else:
        # Divergent physical parts can be legitimate pre-fix generations.
        # Preserve both so exact identity/census checks surface conflicts
        # instead of dropping bytes.
        late_parts = [
            candidate
            for candidate in (late_gzip_path, late_path)
            if _path_entry_exists(candidate, parent_descriptor=parent_descriptor)
        ]
    # A pre-fix midnight append could leave an archived base plus a plain
    # rollover sidecar.  Current cross-midnight writes use the explicit late
    # sidecar and never mutate the verified base gzip.  Consume immutable base
    # parts before later parts so neither representation shadows another.
    return [
        *base_parts,
        *late_parts,
    ]


def _path_entry_metadata(
    path: Path,
    *,
    parent_descriptor: int | None = None,
) -> os.stat_result:
    if parent_descriptor is None:
        return path.lstat()
    return os.stat(
        path.name,
        dir_fd=parent_descriptor,
        follow_symlinks=False,
    )


def _path_entry_exists(
    path: Path,
    *,
    parent_descriptor: int | None = None,
) -> bool:
    """Return true for any directory entry, including a broken symlink."""

    try:
        _path_entry_metadata(path, parent_descriptor=parent_descriptor)
    except FileNotFoundError:
        return False
    return True


def _same_decoded_bytes(
    compressed: Path,
    plain: Path,
    *,
    parent_descriptor: int | None = None,
) -> bool:
    """Compare a gzip/plain crash pair without materializing either file."""

    try:
        compressed_lstat = _path_entry_metadata(
            compressed,
            parent_descriptor=parent_descriptor,
        )
        plain_lstat = _path_entry_metadata(
            plain,
            parent_descriptor=parent_descriptor,
        )
        if not stat.S_ISREG(compressed_lstat.st_mode) or not stat.S_ISREG(
            plain_lstat.st_mode
        ):
            return False
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        compressed_fd = os.open(
            compressed.name if parent_descriptor is not None else compressed,
            flags,
            dir_fd=parent_descriptor,
        )
        try:
            plain_fd = os.open(
                plain.name if parent_descriptor is not None else plain,
                flags,
                dir_fd=parent_descriptor,
            )
        except Exception:
            os.close(compressed_fd)
            raise
        with (
            os.fdopen(compressed_fd, "rb") as compressed_raw,
            os.fdopen(plain_fd, "rb") as plain_handle,
        ):
            compressed_opened = os.fstat(compressed_raw.fileno())
            plain_opened = os.fstat(plain_handle.fileno())
            expected_compressed = (
                compressed_lstat.st_dev,
                compressed_lstat.st_ino,
                compressed_lstat.st_size,
                compressed_lstat.st_mtime_ns,
            )
            expected_plain = (
                plain_lstat.st_dev,
                plain_lstat.st_ino,
                plain_lstat.st_size,
                plain_lstat.st_mtime_ns,
            )
            if (
                compressed_opened.st_dev,
                compressed_opened.st_ino,
                compressed_opened.st_size,
                compressed_opened.st_mtime_ns,
            ) != expected_compressed or (
                plain_opened.st_dev,
                plain_opened.st_ino,
                plain_opened.st_size,
                plain_opened.st_mtime_ns,
            ) != expected_plain:
                return False
            decoded_equal = True
            with gzip.GzipFile(fileobj=compressed_raw, mode="rb") as compressed_handle:
                while True:
                    compressed_chunk = compressed_handle.read(1024 * 1024)
                    plain_chunk = plain_handle.read(1024 * 1024)
                    if compressed_chunk != plain_chunk:
                        decoded_equal = False
                        break
                    if not compressed_chunk:
                        break
            compressed_after = os.fstat(compressed_raw.fileno())
            plain_after = os.fstat(plain_handle.fileno())
            try:
                compressed_current = _path_entry_metadata(
                    compressed,
                    parent_descriptor=parent_descriptor,
                )
                plain_current = _path_entry_metadata(
                    plain,
                    parent_descriptor=parent_descriptor,
                )
            except FileNotFoundError:
                return False
            return (
                decoded_equal
                and (
                    compressed_after.st_dev,
                    compressed_after.st_ino,
                    compressed_after.st_size,
                    compressed_after.st_mtime_ns,
                )
                == expected_compressed
                and (
                    plain_after.st_dev,
                    plain_after.st_ino,
                    plain_after.st_size,
                    plain_after.st_mtime_ns,
                )
                == expected_plain
                and (
                    compressed_current.st_dev,
                    compressed_current.st_ino,
                    compressed_current.st_size,
                    compressed_current.st_mtime_ns,
                )
                == expected_compressed
                and (
                    plain_current.st_dev,
                    plain_current.st_ino,
                    plain_current.st_size,
                    plain_current.st_mtime_ns,
                )
                == expected_plain
            )
    except (EOFError, OSError):
        # Keep both candidates.  The streaming reader will surface the corrupt
        # archive as a source-read error and fail the daily quality gate.
        return False


def _pipeline_partition_lock_path(path: Path) -> Path | None:
    logical = path.with_name(path.name.removesuffix(".gz"))
    if re.fullmatch(r"pipeline_events_\d{4}-\d{2}-\d{2}\.jsonl", logical.name) is None:
        return None
    return logical.with_name(f".{logical.name}.partition.lock")


@contextmanager
def _stable_pipeline_partition(path: Path) -> Iterator[int | None]:
    lock_path = _pipeline_partition_lock_path(path)
    try:
        parent_metadata = path.parent.lstat()
    except FileNotFoundError:
        yield None
        return
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise OSError("pipeline event source parent is not a real directory")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    parent_descriptor = os.open(path.parent, directory_flags)
    try:
        opened_parent = os.fstat(parent_descriptor)
        if not stat.S_ISDIR(opened_parent.st_mode) or (
            opened_parent.st_dev,
            opened_parent.st_ino,
        ) != (parent_metadata.st_dev, parent_metadata.st_ino):
            raise OSError("pipeline event source parent changed before open")
        if lock_path is None:
            yield parent_descriptor
            return
        flags = os.O_RDWR | os.O_CREAT
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(
            lock_path.name,
            flags,
            0o640,
            dir_fd=parent_descriptor,
        )
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("pipeline event partition lock is not a regular file")
            fcntl.flock(descriptor, fcntl.LOCK_SH)
            yield parent_descriptor
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
    finally:
        os.close(parent_descriptor)


def _stream_json_objects(
    path: Path,
) -> tuple[Iterator[tuple[int, dict[str, Any]]], _StreamCensus]:
    """Yield JSON objects and fill a census without retaining source rows."""

    census = _StreamCensus(
        source_path=str(path),
    )

    def iterator() -> Iterator[tuple[int, dict[str, Any]]]:
        decoded_hasher = hashlib.sha256()
        aggregate_raw_hasher = hashlib.sha256()
        try:
            with _stable_pipeline_partition(path) as parent_descriptor:
                if parent_descriptor is None:
                    census.source_path = str(path)
                    census.source_exists = False
                    census.source_part_count = 0
                    return
                resolved_paths = _resolve_source_paths(
                    path,
                    parent_descriptor=parent_descriptor,
                )
                census.source_path = (
                    "|".join(str(candidate) for candidate in resolved_paths)
                    if resolved_paths
                    else str(path)
                )
                census.source_exists = bool(resolved_paths)
                census.source_is_gzip = (
                    len(resolved_paths) == 1 and resolved_paths[0].suffix == ".gz"
                )
                census.source_part_count = len(resolved_paths)
                if not resolved_paths:
                    return
                for resolved in resolved_paths:
                    expected_metadata = _path_entry_metadata(
                        resolved,
                        parent_descriptor=parent_descriptor,
                    )
                    if not stat.S_ISREG(expected_metadata.st_mode):
                        raise OSError("pipeline_event_source_not_regular")
                    descriptor = os.open(
                        resolved.name if parent_descriptor is not None else resolved,
                        os.O_RDONLY
                        | getattr(os, "O_CLOEXEC", 0)
                        | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=parent_descriptor,
                    )
                    with os.fdopen(descriptor, "rb") as physical_handle:
                        opened_metadata = os.fstat(physical_handle.fileno())
                        expected_identity = (
                            expected_metadata.st_dev,
                            expected_metadata.st_ino,
                            expected_metadata.st_size,
                            expected_metadata.st_mtime_ns,
                        )
                        opened_identity = (
                            opened_metadata.st_dev,
                            opened_metadata.st_ino,
                            opened_metadata.st_size,
                            opened_metadata.st_mtime_ns,
                        )
                        if opened_identity != expected_identity:
                            raise OSError("pipeline_event_source_changed_before_read")
                        late_sidecar = ".late.jsonl" in resolved.name
                        if late_sidecar:
                            fcntl.flock(physical_handle.fileno(), fcntl.LOCK_SH)
                        digesting_reader = _DigestingReader(
                            physical_handle,
                            aggregate_hasher=aggregate_raw_hasher,
                        )
                        decoded_stream: BinaryIO
                        if resolved.suffix == ".gz":
                            decoded_stream = gzip.GzipFile(
                                fileobj=digesting_reader,
                                mode="rb",
                            )
                        else:
                            decoded_stream = digesting_reader  # type: ignore[assignment]
                        try:
                            while True:
                                raw_line = decoded_stream.readline()
                                if not raw_line:
                                    break
                                census.physical_line_count += 1
                                census.source_decoded_bytes += len(raw_line)
                                decoded_hasher.update(raw_line)
                                stripped = raw_line.strip()
                                if not stripped:
                                    census.blank_line_count += 1
                                    continue
                                try:
                                    payload = json.loads(stripped.decode("utf-8"))
                                except (UnicodeDecodeError, json.JSONDecodeError):
                                    census.malformed_json_count += 1
                                    continue
                                if not isinstance(payload, dict):
                                    census.non_object_count += 1
                                    continue
                                census.json_object_count += 1
                                yield census.physical_line_count, payload
                        finally:
                            if resolved.suffix == ".gz":
                                decoded_stream.close()
                            digesting_reader.read()
                            census.source_raw_bytes += digesting_reader.byte_count
                            if late_sidecar:
                                fcntl.flock(
                                    physical_handle.fileno(),
                                    fcntl.LOCK_UN,
                                )
                        after_metadata = os.fstat(physical_handle.fileno())
                        after_identity = (
                            after_metadata.st_dev,
                            after_metadata.st_ino,
                            after_metadata.st_size,
                            after_metadata.st_mtime_ns,
                        )
                        try:
                            current_metadata = _path_entry_metadata(
                                resolved,
                                parent_descriptor=parent_descriptor,
                            )
                        except FileNotFoundError as exc:
                            raise OSError(
                                "pipeline_event_source_changed_during_read"
                            ) from exc
                        current_identity = (
                            current_metadata.st_dev,
                            current_metadata.st_ino,
                            current_metadata.st_size,
                            current_metadata.st_mtime_ns,
                        )
                        if (
                            after_identity != opened_identity
                            or current_identity != opened_identity
                            or not stat.S_ISREG(current_metadata.st_mode)
                        ):
                            raise OSError("pipeline_event_source_changed_during_read")
        except (EOFError, OSError) as exc:
            census.source_read_error = type(exc).__name__
        finally:
            census.source_raw_sha256 = aggregate_raw_hasher.hexdigest()
            census.source_decoded_sha256 = decoded_hasher.hexdigest()

    return iterator(), census


def _aware_datetime(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError("timestamp_not_timezone_aware")
    return parsed


def _finite_number(
    value: Any,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if (
        not math.isfinite(number)
        or (positive and number <= 0)
        or (nonnegative and number < 0)
    ):
        return None
    return number


def _pipeline_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _pipeline_text(value: Any) -> str:
    normalized = str(value or "").strip()
    return "" if normalized.lower() in {"", "-", "none", "null"} else normalized


def _pipeline_broker_order_numbers(
    fields: Mapping[str, Any],
) -> tuple[list[str] | None, str | None]:
    list_text = _pipeline_text(fields.get("broker_order_no_list"))
    primary = _pipeline_text(
        fields.get("broker_order_no") or fields.get("order_no") or fields.get("ord_no")
    )
    raw_values = list_text.split(",") if list_text else ([primary] if primary else [])
    order_numbers: list[str] = []
    for raw_value in raw_values:
        order_no = str(raw_value or "").strip()
        if not re.fullmatch(r"[0-9]{7}", order_no) or int(order_no) == 0:
            return None, "pipeline_broker_order_no_invalid"
        if order_no not in order_numbers:
            order_numbers.append(order_no)
    if not order_numbers:
        return None, "pipeline_broker_order_no_missing"
    if primary and primary not in order_numbers:
        return None, "pipeline_broker_order_primary_not_in_list"
    return order_numbers, None


def _pipeline_submitted_order_quantities(
    fields: Mapping[str, Any],
    order_numbers: list[str],
    requested_qty: Any,
) -> tuple[dict[str, int] | None, str | None]:
    try:
        quantities = normalize_submitted_order_quantities(
            fields,
            order_numbers,
            requested_qty,
        )
    except ValueError as exc:
        return None, f"pipeline_{exc}"
    return quantities, None


def _pipeline_submission_contract_data(
    fields: Mapping[str, Any],
    *,
    order_numbers: list[str],
    allow_single_order_leg: bool = False,
) -> tuple[dict[str, Any] | None, str | None]:
    contract: dict[str, Any] = {}
    leg_contract = _pipeline_text(fields.get("lifecycle_submission_leg_contract"))
    if leg_contract:
        if leg_contract not in {
            "exact_broker_order_leg_v1",
            "exact_broker_single_order_leg_v1",
        }:
            return None, "pipeline_submission_leg_contract_invalid"
        if leg_contract == "exact_broker_single_order_leg_v1" and (
            not allow_single_order_leg or len(order_numbers) != 1
        ):
            return None, "pipeline_single_order_leg_contract_count_invalid"
        contract["submission_leg_contract"] = leg_contract
        if leg_contract == "exact_broker_single_order_leg_v1":
            contract["submission_leg_self_summarizing"] = True
    summary_only = _pipeline_bool(fields.get("lifecycle_submission_summary_only"))
    if summary_only is True:
        if leg_contract == "exact_broker_single_order_leg_v1":
            return None, "pipeline_single_order_leg_summary_invalid"
        expected = _finite_number(
            fields.get("submitted_leg_count"),
            positive=True,
        )
        if (
            expected is None
            or not expected.is_integer()
            or int(expected) != len(order_numbers)
        ):
            return None, "pipeline_submission_summary_leg_count_mismatch"
        contract.update(
            {
                "submission_summary_only": True,
                "submission_summary_expected_leg_count": int(expected),
            }
        )
    elif summary_only is False:
        contract["submission_summary_only"] = False
    return contract, None


def _pipeline_submission_custody_data(
    fields: Mapping[str, Any],
    *,
    source_stage: str,
    order_numbers: list[str],
    requested_qty: float,
    lifecycle_observed_at: str,
) -> tuple[dict[str, Any] | None, str | None]:
    has_custody_claim = any(
        fields.get(name) is not None and fields.get(name) != ""
        for name in SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES
    )
    if source_stage not in SUBMISSION_CUSTODY_SOURCE_STAGES:
        if has_custody_claim:
            return None, "pipeline_submission_custody_stage_invalid"
        return {}, None
    if not has_custody_claim:
        return None, "pipeline_submission_custody_contract_missing"
    if (
        len(order_numbers) != 1
        or not requested_qty.is_integer()
        or _pipeline_text(fields.get("lifecycle_submission_time_source"))
        != BROKER_EXECUTION_RECEIVE_TIME_SOURCE
        or _pipeline_text(fields.get("lifecycle_submission_ordering_clock"))
        != "broker_execution_received_at"
        or _pipeline_text(fields.get("submission_causal_upper_bound_source"))
        != BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        or _pipeline_text(fields.get("submission_custody_binding_schema"))
        != SUBMISSION_CUSTODY_BINDING_SCHEMA
    ):
        return None, "pipeline_submission_custody_contract_invalid"

    bound_order_no = _pipeline_text(fields.get("submission_custody_broker_order_no"))
    execution_no = _pipeline_text(fields.get("submission_custody_broker_execution_no"))
    bound_order_qty = _finite_number(
        fields.get("submission_custody_broker_order_qty"), positive=True
    )
    cumulative_qty = _finite_number(
        fields.get("submission_custody_broker_cumulative_qty"), positive=True
    )
    remaining_qty = _finite_number(
        fields.get("submission_custody_broker_remaining_qty"), nonnegative=True
    )
    unit_qty = _finite_number(
        fields.get("submission_custody_broker_unit_qty"), positive=True
    )
    numeric_values = (bound_order_qty, cumulative_qty, remaining_qty, unit_qty)
    if (
        bound_order_no != order_numbers[0]
        or not execution_no
        or execution_no in {"-", "None", "none", "null"}
        or re.fullmatch(r"[0-9]{1,20}", execution_no) is None
        or int(execution_no) == 0
        or any(value is None or not value.is_integer() for value in numeric_values)
    ):
        return None, "pipeline_submission_custody_binding_invalid"
    assert all(value is not None for value in numeric_values)
    order_qty = int(bound_order_qty)
    cumulative = int(cumulative_qty)
    remaining = int(remaining_qty)
    unit = int(unit_qty)
    if (
        order_qty != int(requested_qty)
        or cumulative + remaining != order_qty
        or unit > cumulative
    ):
        return None, "pipeline_submission_custody_quantity_binding_invalid"
    try:
        receive_at = _aware_datetime(lifecycle_observed_at).astimezone(KST)
        causal_upper_bound_at = _aware_datetime(
            fields.get("submission_causal_upper_bound_at")
        ).astimezone(KST)
    except (TypeError, ValueError):
        return None, "pipeline_submission_custody_timestamp_invalid"
    receive_lag_sec = (receive_at - causal_upper_bound_at).total_seconds()
    if (
        causal_upper_bound_at.microsecond != 0
        or receive_lag_sec < -BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC
        or receive_lag_sec > BROKER_EXECUTION_MAX_RECEIVE_LAG_SEC
    ):
        return None, "pipeline_submission_custody_causal_bound_invalid"
    return (
        {
            "submission_time_source": BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
            "submission_ordering_clock": "broker_execution_received_at",
            "submission_causal_upper_bound_at": causal_upper_bound_at.isoformat(
                timespec="microseconds"
            ),
            "submission_causal_upper_bound_source": (
                BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
            ),
            "submission_custody_binding_schema": SUBMISSION_CUSTODY_BINDING_SCHEMA,
            "submission_custody_broker_order_no": bound_order_no,
            "submission_custody_broker_execution_no": execution_no,
            "submission_custody_broker_order_qty": order_qty,
            "submission_custody_broker_cumulative_qty": cumulative,
            "submission_custody_broker_remaining_qty": remaining,
            "submission_custody_broker_unit_qty": unit,
        },
        None,
    )


def _pipeline_scale_in_decision(
    source_stage: str, fields: Mapping[str, Any]
) -> str | None:
    if source_stage in {
        "scale_in_order_submitted",
        "scale_in_order_leg_submitted",
        "scale_in_execution_receipt_submission_custody",
        "scale_in_executed",
    }:
        return (
            "ADD"
            if _pipeline_bool(fields.get("actual_order_submitted")) is True
            else None
        )
    if source_stage != "stat_action_decision_snapshot":
        return None
    chosen_action = _pipeline_text(fields.get("chosen_action")).lower()
    if chosen_action in {"avg_down_wait", "pyramid_wait"}:
        action_type = _pipeline_text(fields.get("scale_in_action_type")).upper()
        if action_type not in {"AVG_DOWN", "PYRAMID"}:
            return None
        if _pipeline_bool(fields.get("scale_in_gate_allowed")) is not True:
            return None
        return "ADD"
    if chosen_action == "hold_wait":
        return "NO_ADD"
    if chosen_action == "exit_now":
        return "NOT_APPLICABLE"
    return None


def _pipeline_execution_timing_data(
    fields: Mapping[str, Any],
    *,
    lifecycle_observed_at: str,
    legacy_unattested_receive_clock_diagnostic: bool = False,
) -> tuple[dict[str, Any] | None, str | None]:
    """Recover exact receive/occurrence clocks without synthesizing either."""

    raw_envelope_schema = _pipeline_text(
        fields.get("main_lifecycle_broker_raw_envelope_schema")
        or fields.get("broker_raw_envelope_schema")
    )
    raw_source_type = _pipeline_text(
        fields.get("main_lifecycle_broker_raw_source_type")
        or fields.get("broker_raw_source_type")
    )
    if raw_envelope_schema != BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA:
        return None, "pipeline_broker_execution_raw_envelope_schema_invalid"
    if raw_source_type != "00":
        return None, "pipeline_broker_execution_raw_source_type_invalid"
    received_text = _pipeline_text(fields.get("broker_execution_received_at"))
    occurred_text = _pipeline_text(fields.get("broker_execution_observed_at"))
    if not received_text:
        return None, "pipeline_broker_execution_received_at_missing"
    if not occurred_text:
        return None, "pipeline_broker_execution_occurred_at_missing"
    if _pipeline_text(fields.get("broker_execution_time_source")) != (
        BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
    ):
        return None, "pipeline_broker_execution_occurrence_source_invalid"
    declared_receive_source = _pipeline_text(
        fields.get("broker_execution_receive_time_source")
    )
    legacy_receive_clock_recovered = False
    if declared_receive_source != BROKER_EXECUTION_RECEIVE_TIME_SOURCE:
        if legacy_unattested_receive_clock_diagnostic and not declared_receive_source:
            # Historical rows already stored a distinct receive timestamp but
            # predate the explicit packet-ingress source attestation.  An
            # operator-requested diagnostic may order by that stored clock,
            # but the recovery marker below permanently excludes the result
            # from R2/R3 or promotion evidence.
            legacy_receive_clock_recovered = True
        else:
            return None, "pipeline_broker_execution_receive_source_invalid"
    try:
        original_lifecycle_at = _aware_datetime(lifecycle_observed_at).astimezone(KST)
        received_at = _aware_datetime(received_text).astimezone(KST)
        occurred_at = _aware_datetime(occurred_text).astimezone(KST)
    except (TypeError, ValueError):
        return None, "pipeline_broker_execution_timing_timestamp_invalid"

    raw_fid_908 = _pipeline_text(fields.get("908"))
    if not re.fullmatch(r"[0-9]{6}", raw_fid_908):
        return None, "pipeline_broker_execution_fid908_missing_or_invalid"
    if occurred_at.strftime("%H%M%S") != raw_fid_908:
        return None, "pipeline_broker_execution_occurrence_fid908_mismatch"

    generated_received = _pipeline_text(
        fields.get("main_lifecycle_execution_received_at")
    )
    generated_occurred = _pipeline_text(
        fields.get("main_lifecycle_execution_occurred_at")
    )
    try:
        if generated_received and (
            _aware_datetime(generated_received).astimezone(KST) != received_at
        ):
            return None, "pipeline_broker_execution_generated_receive_mismatch"
        if generated_occurred and (
            _aware_datetime(generated_occurred).astimezone(KST) != occurred_at
        ):
            return None, "pipeline_broker_execution_generated_occurrence_mismatch"
    except (TypeError, ValueError):
        return None, "pipeline_broker_execution_generated_timestamp_invalid"

    generated_ordering_source = _pipeline_text(
        fields.get("main_lifecycle_ordering_time_source")
    )
    if generated_ordering_source and generated_ordering_source != (
        BROKER_EXECUTION_ORDERING_TIME_SOURCE
    ):
        return None, "pipeline_broker_execution_generated_ordering_source_invalid"
    generated_occurrence_source = _pipeline_text(
        fields.get("main_lifecycle_execution_occurrence_time_source")
    )
    if generated_occurrence_source and generated_occurrence_source != (
        BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
    ):
        return None, "pipeline_broker_execution_generated_occurrence_source_invalid"
    generated_receive_source = _pipeline_text(
        fields.get("main_lifecycle_execution_receive_time_source")
    )
    if generated_receive_source and generated_receive_source != (
        BROKER_EXECUTION_RECEIVE_TIME_SOURCE
    ):
        return None, "pipeline_broker_execution_generated_receive_source_invalid"
    generated_trade_date = _pipeline_text(
        fields.get("main_lifecycle_execution_trade_date")
    )
    if generated_trade_date and generated_trade_date != occurred_at.date().isoformat():
        return None, "pipeline_broker_execution_generated_trade_date_mismatch"

    if original_lifecycle_at == received_at:
        rebound = False
    elif original_lifecycle_at == occurred_at:
        # Pre-P0 rows used FID 908 as the transition clock.  Both source clocks
        # are already present in those raw rows, so rebinding to receive time is
        # deterministic recovery rather than a timestamp inference.
        rebound = True
    else:
        return None, "pipeline_broker_execution_lifecycle_timestamp_unbound"

    lag_sec = (received_at - occurred_at).total_seconds()
    if lag_sec < -BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC:
        return None, "pipeline_broker_execution_receive_precedes_occurrence"
    if lag_sec > BROKER_EXECUTION_MAX_RECEIVE_LAG_SEC:
        return None, "pipeline_broker_execution_receive_lag_exceeds_bound"
    return (
        {
            "broker_execution_timing_schema": BROKER_EXECUTION_TIMING_SCHEMA,
            "broker_execution_received_at": received_at.isoformat(
                timespec="microseconds"
            ),
            "broker_execution_occurred_at": occurred_at.isoformat(
                timespec="microseconds"
            ),
            "broker_execution_receive_time_source": (
                BROKER_EXECUTION_RECEIVE_TIME_SOURCE
            ),
            "broker_execution_ordering_time_source": (
                BROKER_EXECUTION_ORDERING_TIME_SOURCE
            ),
            "broker_execution_occurrence_time_source": (
                BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
            ),
            "broker_execution_receive_lag_ms": lag_sec * 1000.0,
            "broker_execution_lifecycle_observed_at_rebound": rebound,
            "legacy_unattested_receive_clock_recovered": (
                legacy_receive_clock_recovered
            ),
        },
        None,
    )


def _pipeline_transition_data(
    *,
    lifecycle_stage: str,
    source_stage: str,
    fields: Mapping[str, Any],
    lifecycle_stock_code: str,
    lifecycle_venue: str,
    lifecycle_observed_at: str,
    lifecycle_trade_date: str,
    legacy_unattested_receive_clock_diagnostic: bool = False,
) -> tuple[dict[str, Any] | None, str | None]:
    data: dict[str, Any] = {}
    carry_source_fields = {
        "main_lifecycle_carry_in_custody_schema",
        "main_lifecycle_origin",
        "main_lifecycle_carry_in_entry_observed_at",
        "main_lifecycle_carry_in_entry_source",
    }
    present_carry_fields = {
        field_name
        for field_name in carry_source_fields
        if fields.get(field_name) is not None and fields.get(field_name) != ""
    }
    if present_carry_fields:
        if present_carry_fields != carry_source_fields:
            return None, "pipeline_carry_in_custody_contract_incomplete"
        carry_entry_source = _pipeline_text(
            fields.get("main_lifecycle_carry_in_entry_source")
        )
        carry_entry_observed_at = _pipeline_text(
            fields.get("main_lifecycle_carry_in_entry_observed_at")
        )
        try:
            carry_entry_at = _aware_datetime(carry_entry_observed_at).astimezone(KST)
            carry_trade_date = date.fromisoformat(lifecycle_trade_date)
        except (TypeError, ValueError):
            return None, "pipeline_carry_in_custody_timestamp_invalid"
        if (
            lifecycle_stage not in {"holding", "exit"}
            or fields.get("main_lifecycle_carry_in_custody_schema")
            != CARRY_IN_CUSTODY_SCHEMA
            or fields.get("main_lifecycle_origin") != "preexisting_position_custody"
            or carry_entry_source not in {"stock.holding_started_at", "stock.buy_time"}
            or carry_entry_at.date() >= carry_trade_date
        ):
            return None, "pipeline_carry_in_custody_contract_invalid"
        data.update(
            {
                "carry_in_custody_schema": CARRY_IN_CUSTODY_SCHEMA,
                "lifecycle_origin": "preexisting_position_custody",
                "carry_in_entry_observed_at": carry_entry_at.isoformat(
                    timespec="microseconds"
                ),
                "carry_in_entry_source": carry_entry_source,
            }
        )
    if source_stage not in SUBMISSION_CUSTODY_SOURCE_STAGES and any(
        fields.get(name) is not None and fields.get(name) != ""
        for name in (
            "submission_custody_binding_schema",
            "submission_causal_upper_bound_at",
            "submission_custody_broker_order_no",
        )
    ):
        return None, "pipeline_submission_custody_stage_invalid"
    source_population_scope = _pipeline_text(
        fields.get("pipeline_lifecycle_population_scope")
    )
    if source_population_scope:
        if source_population_scope not in PIPELINE_SOURCE_POPULATION_SCOPES:
            return None, "pipeline_lifecycle_population_scope_invalid"
        data["source_population_scope"] = source_population_scope
    decision_trace_id = _pipeline_text(fields.get("main_lifecycle_decision_trace_id"))
    if decision_trace_id:
        data["decision_trace_id"] = decision_trace_id
    for source_key, destination_key in (
        (
            "main_lifecycle_market_observation_expected",
            "market_observation_expected",
        ),
        ("main_lifecycle_bbo_observed", "bbo_observed"),
        ("main_lifecycle_depth_observed", "depth_observed"),
        ("main_lifecycle_heartbeat", "heartbeat"),
    ):
        parsed = _pipeline_bool(fields.get(source_key))
        if parsed is not None:
            data[destination_key] = parsed

    action = _pipeline_text(fields.get("action"))
    reason = _pipeline_text(fields.get("reason"))
    if action:
        data["action"] = action
    if reason:
        data["reason"] = reason
    for source_key, destination_key in (
        ("main_lifecycle_venue_source", "venue_source"),
        ("main_lifecycle_venue_provenance_status", "venue_provenance_status"),
        ("main_lifecycle_session_bucket_source", "session_bucket_source"),
        ("main_lifecycle_session_provenance_status", "session_provenance_status"),
    ):
        value = _pipeline_text(fields.get(source_key))
        if value:
            data[destination_key] = value

    if lifecycle_stage == "submit":
        if _pipeline_bool(fields.get("actual_order_submitted")) is not True:
            return None, "pipeline_submit_not_explicitly_broker_submitted"
        data["actual_broker_order_submitted"] = True
        broker_order_numbers, order_error = _pipeline_broker_order_numbers(fields)
        if broker_order_numbers is None:
            return None, order_error or "pipeline_submit_broker_order_no_missing"
        data["broker_order_no"] = broker_order_numbers[0]
        data["broker_order_no_list"] = ",".join(broker_order_numbers)
        requested_qty = _finite_number(
            (
                fields.get("submitted_qty")
                if "submitted_qty" in fields
                else fields.get("requested_qty")
            ),
            positive=True,
        )
        if requested_qty is None:
            return None, "pipeline_submit_requested_qty_invalid"
        order_quantities, quantity_error = _pipeline_submitted_order_quantities(
            fields,
            broker_order_numbers,
            requested_qty,
        )
        if order_quantities is None:
            return None, quantity_error or "pipeline_submit_order_qty_invalid"
        submission_contract, contract_error = _pipeline_submission_contract_data(
            fields,
            order_numbers=broker_order_numbers,
        )
        if submission_contract is None:
            return None, contract_error or "pipeline_submit_contract_invalid"
        custody_contract, custody_error = _pipeline_submission_custody_data(
            fields,
            source_stage=source_stage,
            order_numbers=broker_order_numbers,
            requested_qty=requested_qty,
            lifecycle_observed_at=lifecycle_observed_at,
        )
        if custody_contract is None:
            return None, custody_error or "pipeline_submission_custody_invalid"
        data["requested_qty"] = requested_qty
        data["broker_order_qty_list"] = canonical_submitted_order_qty_list(
            order_quantities
        )
        data.update(submission_contract)
        data.update(custody_contract)

    if lifecycle_stage == "fill":
        fill_state = _pipeline_text(fields.get("fill_state")).lower()
        if not fill_state:
            fill_quality = _pipeline_text(fields.get("fill_quality")).upper()
            fill_state = {
                "PARTIAL_FILL": "partial",
                "FULL_FILL": "full",
            }.get(fill_quality, "")
        if fill_state not in {"partial", "full"}:
            return None, "pipeline_fill_state_invalid"
        fill_qty = _finite_number(fields.get("fill_qty"), positive=True)
        fill_price = _finite_number(fields.get("fill_price"), positive=True)
        if fill_qty is None or fill_price is None:
            return None, "pipeline_fill_price_or_qty_invalid"
        data.update(
            {
                "fill_state": fill_state,
                "fill_qty": fill_qty,
                "fill_price": fill_price,
            }
        )
        requested_qty = _finite_number(fields.get("requested_qty"), positive=True)
        if requested_qty is not None:
            data["requested_qty"] = requested_qty

    if lifecycle_stage == "holding":
        data.setdefault("action", "HOLD")

    if lifecycle_stage == "scale_in":
        decision = _pipeline_scale_in_decision(source_stage, fields)
        if decision is None:
            return None, "pipeline_scale_in_decision_unmapped"
        data["scale_in_decision"] = decision
        if source_stage in {
            "scale_in_order_submitted",
            "scale_in_order_leg_submitted",
            "scale_in_execution_receipt_submission_custody",
        }:
            broker_order_numbers, order_error = _pipeline_broker_order_numbers(fields)
            if broker_order_numbers is None:
                return None, order_error or "pipeline_scale_in_order_no_missing"
            requested_qty = _finite_number(
                (
                    fields.get("submitted_qty")
                    if "submitted_qty" in fields
                    else fields.get("qty")
                ),
                positive=True,
            )
            if requested_qty is None:
                return None, "pipeline_scale_in_submitted_qty_invalid"
            order_quantities, quantity_error = _pipeline_submitted_order_quantities(
                fields,
                broker_order_numbers,
                requested_qty,
            )
            if order_quantities is None:
                return (
                    None,
                    quantity_error or "pipeline_scale_in_order_qty_invalid",
                )
            submission_contract, contract_error = _pipeline_submission_contract_data(
                fields,
                order_numbers=broker_order_numbers,
            )
            if submission_contract is None:
                return (
                    None,
                    contract_error or "pipeline_scale_in_submit_contract_invalid",
                )
            custody_contract, custody_error = _pipeline_submission_custody_data(
                fields,
                source_stage=source_stage,
                order_numbers=broker_order_numbers,
                requested_qty=requested_qty,
                lifecycle_observed_at=lifecycle_observed_at,
            )
            if custody_contract is None:
                return (
                    None,
                    custody_error or "pipeline_scale_in_submission_custody_invalid",
                )
            data.update(
                {
                    "actual_broker_order_submitted": True,
                    "broker_order_no": broker_order_numbers[0],
                    "broker_order_no_list": ",".join(broker_order_numbers),
                    "broker_order_qty_list": canonical_submitted_order_qty_list(
                        order_quantities
                    ),
                    "requested_qty": requested_qty,
                    **submission_contract,
                    **custody_contract,
                }
            )
        if source_stage == "scale_in_executed":
            fill_qty = _finite_number(fields.get("fill_qty"), positive=True)
            fill_price = _finite_number(fields.get("fill_price"), positive=True)
            if fill_qty is None or fill_price is None:
                return None, "pipeline_scale_in_fill_price_or_qty_invalid"
            data.update({"fill_qty": fill_qty, "fill_price": fill_price})

    if lifecycle_stage == "exit" and source_stage in {
        "sell_order_sent",
        "exit_execution_receipt_submission_custody",
    }:
        if _pipeline_bool(fields.get("actual_order_submitted")) is not True:
            return None, "pipeline_sell_not_explicitly_broker_submitted"
        broker_order_numbers, order_error = _pipeline_broker_order_numbers(fields)
        if broker_order_numbers is None:
            return None, order_error or "pipeline_sell_order_no_missing"
        requested_qty = _finite_number(
            fields.get("qty") if "qty" in fields else fields.get("requested_qty"),
            positive=True,
        )
        if requested_qty is None:
            return None, "pipeline_sell_submitted_qty_invalid"
        order_quantities, quantity_error = _pipeline_submitted_order_quantities(
            fields,
            broker_order_numbers,
            requested_qty,
        )
        if order_quantities is None:
            return None, quantity_error or "pipeline_sell_order_qty_invalid"
        submission_contract: dict[str, Any] = {}
        custody_contract: dict[str, Any] = {}
        parsed_submission_contract, contract_error = _pipeline_submission_contract_data(
            fields,
            order_numbers=broker_order_numbers,
            allow_single_order_leg=True,
        )
        if parsed_submission_contract is None:
            return (
                None,
                contract_error or "pipeline_sell_submit_contract_invalid",
            )
        submission_contract = parsed_submission_contract
        if (
            legacy_unattested_receive_clock_diagnostic
            and source_stage == "sell_order_sent"
            and not _pipeline_text(fields.get("lifecycle_submission_leg_contract"))
        ):
            # Historical rows predate the per-leg/self-summary contract.  The
            # transition remains only a diagnostic candidate here: the report
            # builder withholds it until a later strict official SELL receipt
            # proves the same single broker order and full order quantity.
            submission_contract["submission_contract_legacy_unattested"] = True
        if source_stage == "exit_execution_receipt_submission_custody":
            parsed_custody_contract, custody_error = _pipeline_submission_custody_data(
                fields,
                source_stage=source_stage,
                order_numbers=broker_order_numbers,
                requested_qty=requested_qty,
                lifecycle_observed_at=lifecycle_observed_at,
            )
            if parsed_custody_contract is None:
                return (
                    None,
                    custody_error or "pipeline_sell_submission_custody_invalid",
                )
            custody_contract = parsed_custody_contract
        data.update(
            {
                "actual_broker_order_submitted": True,
                "broker_order_no": broker_order_numbers[0],
                "broker_order_no_list": ",".join(broker_order_numbers),
                "broker_order_qty_list": canonical_submitted_order_qty_list(
                    order_quantities
                ),
                "requested_qty": requested_qty,
                **submission_contract,
                **custody_contract,
            }
        )

    execution_exit_stages = {
        "sell_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_sell_completed",
        "sell_completed",
    }
    if lifecycle_stage == "exit" and source_stage in execution_exit_stages:
        if (
            "main_lifecycle_exit_qty" not in fields
            or "main_lifecycle_exit_price" not in fields
        ):
            return None, "pipeline_execution_exit_exact_price_or_qty_missing"
        exit_qty = _finite_number(fields.get("main_lifecycle_exit_qty"), positive=True)
        exit_price = _finite_number(
            fields.get("main_lifecycle_exit_price"), positive=True
        )
        if exit_qty is None or exit_price is None:
            return None, "pipeline_execution_exit_exact_price_or_qty_invalid"
        data["exit_qty"] = exit_qty
        data["exit_price"] = exit_price
        basis_price_present = "main_lifecycle_slippage_basis_price" in fields
        basis_source_present = "main_lifecycle_slippage_basis_source" in fields
        if basis_price_present != basis_source_present:
            return None, "pipeline_slippage_basis_pair_incomplete"
        if basis_price_present:
            slippage_basis_price = _finite_number(
                fields.get("main_lifecycle_slippage_basis_price"), positive=True
            )
            slippage_basis_source = _pipeline_text(
                fields.get("main_lifecycle_slippage_basis_source")
            )
            if slippage_basis_price is None or not slippage_basis_source:
                return None, "pipeline_slippage_basis_pair_invalid"
            data["slippage_basis_price"] = slippage_basis_price
            data["slippage_basis_source"] = slippage_basis_source

    terminal_no_fill = _pipeline_bool(fields.get("main_lifecycle_terminal_no_fill"))
    if terminal_no_fill is True:
        data["terminal_no_fill"] = True
        data["terminal_reason"] = (
            _pipeline_text(fields.get("main_lifecycle_terminal_reason"))
            or "explicit_pipeline_terminal_no_fill"
        )

    reconciled_final_exit = _pipeline_bool(
        fields.get("main_lifecycle_reconciled_final_exit")
    )
    if reconciled_final_exit is True:
        if lifecycle_stage != "exit" or source_stage != "sell_completed":
            return None, "pipeline_final_exit_stage_invalid"
        if _pipeline_bool(fields.get("main_lifecycle_broker_reconciled")) is not True:
            return None, "pipeline_final_exit_not_broker_reconciled"
        if "exit_qty" not in data or "exit_price" not in data:
            return None, "pipeline_final_exit_price_or_qty_missing"
        data["broker_reconciled"] = True
        data["reconciled_final_exit"] = True

    for source_key, destination_key, nonnegative in (
        ("main_lifecycle_fees_taxes_krw", "fees_taxes_krw", True),
        ("main_lifecycle_slippage_krw", "slippage_krw", True),
        ("main_lifecycle_realized_net_pnl_krw", "realized_net_pnl_krw", False),
    ):
        value = _finite_number(fields.get(source_key), nonnegative=nonnegative)
        if value is not None:
            data[destination_key] = value

    execution_qty: Any | None = None
    execution_price: Any | None = None
    if lifecycle_stage == "fill":
        execution_qty = data.get("fill_qty")
        execution_price = data.get("fill_price")
    elif (
        lifecycle_stage == "scale_in"
        and source_stage == "scale_in_executed"
        and data.get("scale_in_decision") == "ADD"
    ):
        execution_qty = data.get("fill_qty")
        execution_price = data.get("fill_price")
    elif lifecycle_stage == "exit" and source_stage in execution_exit_stages:
        execution_qty = data.get("exit_qty")
        execution_price = data.get("exit_price")
    if execution_qty is not None and execution_price is not None:
        broker_provenance = build_broker_execution_provenance(
            fields,
            expected_qty=execution_qty,
            expected_price=execution_price,
            expected_stock_code=lifecycle_stock_code,
            expected_side="SELL" if lifecycle_stage == "exit" else "BUY",
            lifecycle_venue=lifecycle_venue,
            # The official quantity/remainder pair owns partial/full.  A
            # producer label is never allowed to duplicate one execution by
            # relabeling the same raw identity on replay.
            expected_fill_state=None,
        )
        data.update(broker_provenance)
        if broker_provenance.get("broker_execution_provenance_state") in {
            "complete",
            "identity_complete_venue_unresolved",
        }:
            timing_data, timing_error = _pipeline_execution_timing_data(
                fields,
                lifecycle_observed_at=lifecycle_observed_at,
                legacy_unattested_receive_clock_diagnostic=(
                    legacy_unattested_receive_clock_diagnostic
                ),
            )
            if timing_data is None:
                return None, timing_error or "pipeline_broker_execution_timing_invalid"
            data.update(timing_data)
        if lifecycle_stage == "fill" and broker_provenance.get(
            "broker_execution_provenance_state"
        ) in {"complete", "identity_complete_venue_unresolved"}:
            # Partial/full is an exact broker-order quantity property. An
            # integrated SOR receipt may leave the underlying KRX/NXT venue
            # unresolved while still proving that the materialized order leg
            # is fully filled. Do not retain the broader bundle-level
            # PARTIAL_FILL label in that case.
            data["fill_state"] = broker_provenance["broker_execution_fill_state"]
    elif any(
        _pipeline_text(fields.get(field))
        for field in (
            "main_lifecycle_broker_raw_envelope_schema",
            "broker_raw_envelope_schema",
            "main_lifecycle_broker_raw_source_type",
            "broker_raw_source_type",
            "broker_execution_received_at",
            "broker_execution_observed_at",
            "broker_execution_time_source",
            "908",
        )
    ):
        if lifecycle_stage != "holding" or source_stage != "holding_started":
            return None, "pipeline_broker_receipt_companion_stage_invalid"
        # Some receipt handlers emit a non-execution companion transition
        # (for example ``holding_started``) from the same immutable type-00
        # envelope immediately after the fill transition.  Pre-P0 rows bound
        # both transitions to the second-resolution FID 908 clock.  Rebound
        # the companion ordering clock only when the exact raw marker and both
        # stored clocks validate; never count it as another execution or use it
        # for holding-duration economics.
        companion_side = {"1": "SELL", "2": "BUY"}.get(
            _pipeline_text(fields.get("907"))
        )
        companion_qty = _finite_number(fields.get("915"), positive=True)
        companion_price = _finite_number(fields.get("914"), positive=True)
        if companion_side != "BUY":
            return None, "pipeline_broker_receipt_companion_side_invalid"
        if (
            companion_qty is None
            or not companion_qty.is_integer()
            or companion_price is None
            or not companion_price.is_integer()
        ):
            return None, "pipeline_broker_receipt_companion_economics_invalid"
        companion_provenance = build_broker_execution_provenance(
            fields,
            expected_qty=int(companion_qty),
            expected_price=int(companion_price),
            expected_stock_code=lifecycle_stock_code,
            expected_side=companion_side,
            lifecycle_venue=lifecycle_venue,
            expected_fill_state=None,
        )
        if companion_provenance.get("broker_execution_provenance_state") not in {
            "complete",
            "identity_complete_venue_unresolved",
        }:
            return None, "pipeline_broker_receipt_companion_provenance_invalid"
        timing_data, timing_error = _pipeline_execution_timing_data(
            fields,
            lifecycle_observed_at=lifecycle_observed_at,
            legacy_unattested_receive_clock_diagnostic=(
                legacy_unattested_receive_clock_diagnostic
            ),
        )
        if timing_data is None:
            return (
                None,
                timing_error or "pipeline_broker_receipt_companion_timing_invalid",
            )
        data.update(companion_provenance)
        data.update(timing_data)
        data["broker_execution_receipt_companion"] = True
        data["broker_execution_receipt_companion_of_identity"] = companion_provenance[
            "broker_execution_identity"
        ]
    return data, None


def _validated_pipeline_transition(
    raw_row: Mapping[str, Any],
    *,
    target_date: str,
    legacy_unattested_receive_clock_diagnostic: bool = False,
) -> tuple[dict[str, Any] | None, str | None, bool]:
    """Validate one explicitly instrumented pipeline row.

    The final boolean marks whether the raw pipeline/stage is in the strict
    lifecycle allowlist.  Out-of-scope pipeline rows are ignored; an in-scope
    row without exact identity is an instrumentation gap, never a join input.
    """

    if raw_row.get("event_type") != "pipeline_event":
        return None, None, False
    pipeline = _pipeline_text(raw_row.get("pipeline")).upper()
    source_stage = _pipeline_text(raw_row.get("stage"))
    lifecycle_stage = PIPELINE_STAGE_MAP.get((pipeline, source_stage))
    if lifecycle_stage is None:
        return None, None, False
    fields = raw_row.get("fields")
    if not isinstance(fields, dict):
        return None, "pipeline_lifecycle_fields_invalid", True
    strict_leg_contract = {
        "sell_order_sent": "exact_broker_single_order_leg_v1",
        "exit_execution_receipt_submission_custody": (
            "exact_broker_single_order_leg_v1"
        ),
    }.get(source_stage, "exact_broker_order_leg_v1")
    sell_order_sent_has_custody_spoof = bool(
        source_stage == "sell_order_sent"
        and any(
            fields.get(field_name) is not None and fields.get(field_name) != ""
            for field_name in SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES
        )
    )
    if sell_order_sent_has_custody_spoof:
        return None, "pipeline_submission_custody_stage_invalid", True
    exact_exit_submission_stages = {
        "sell_order_sent",
        "exit_execution_receipt_submission_custody",
    }
    diagnostic_legacy_sell_submission = bool(
        legacy_unattested_receive_clock_diagnostic
        and source_stage == "sell_order_sent"
        and not _pipeline_text(fields.get("lifecycle_submission_leg_contract"))
        and fields.get("lifecycle_submission_summary_only") in {None, ""}
        and fields.get("submitted_leg_count") in {None, ""}
    )
    if (
        source_stage in exact_exit_submission_stages
        and fields.get("lifecycle_submission_leg_contract") != strict_leg_contract
        and not diagnostic_legacy_sell_submission
    ):
        # These are current real-exit custody/submission stages.  Silently
        # treating an exact lifecycle row as legacy out-of-scope would hide a
        # sell-side custody gap and let the remaining lifecycle appear clean.
        return None, "pipeline_sell_submit_contract_invalid", True
    if (
        source_stage
        in {
            "order_leg_sent",
            "scale_in_order_leg_submitted",
            "entry_execution_receipt_submission_custody",
            "scale_in_execution_receipt_submission_custody",
        }
        and fields.get("lifecycle_submission_leg_contract") != strict_leg_contract
    ):
        # Rows emitted before the exact per-leg contract existed are ordinary
        # operational telemetry, not lifecycle instrumentation gaps.
        return None, None, False
    if fields.get(
        "pipeline_lifecycle_population_scope"
    ) == "sim_observation_only" and raw_row.get("record_id") in {None, ""}:
        return None, None, False
    # Statistical action snapshots also serve a separate simulator lane.  A
    # source-declared sim-only snapshot has no real RecommendationHistory
    # record and is not a main-bot lifecycle transition.  Keep it out of the
    # strict denominator instead of turning expected sim telemetry into an
    # unbound global instrumentation failure.
    if (
        source_stage == "stat_action_decision_snapshot"
        and raw_row.get("record_id") in {None, ""}
        and str(fields.get("decision_authority") or "").strip()
        == "sim_observation_only"
        and _pipeline_bool(fields.get("snapshot_observe_only")) is True
    ):
        return None, None, False
    if fields.get("main_lifecycle_identity_schema") != PIPELINE_IDENTITY_SCHEMA:
        return None, "pipeline_lifecycle_identity_missing", True
    if fields.get("main_lifecycle_source_pipeline") != pipeline:
        return None, "pipeline_lifecycle_source_pipeline_mismatch", True
    if fields.get("main_lifecycle_source_stage") != source_stage:
        return None, "pipeline_lifecycle_source_stage_mismatch", True
    if fields.get("main_lifecycle_stage") != lifecycle_stage:
        return None, "pipeline_lifecycle_stage_mapping_mismatch", True
    if fields.get("main_lifecycle_trade_date") != target_date:
        return None, "pipeline_lifecycle_trade_date_mismatch", True
    if fields.get("main_lifecycle_decision_authority") != (
        "source_only_lifecycle_observation"
    ):
        return None, "pipeline_lifecycle_authority_mismatch", True
    for key in (
        "main_lifecycle_runtime_effect",
        "main_lifecycle_order_authority",
        "main_lifecycle_provider_authority",
    ):
        if _pipeline_bool(fields.get(key)) is not False:
            return None, f"pipeline_lifecycle_authority_mismatch:{key}", True

    record_id = raw_row.get("record_id")
    stock_code = _pipeline_text(raw_row.get("stock_code"))
    attempt_id = _pipeline_text(fields.get("attempt_id"))
    if attempt_id != _pipeline_text(fields.get("main_lifecycle_attempt_id")):
        return None, "pipeline_lifecycle_attempt_id_mismatch", True
    if str(record_id if record_id is not None else "").strip() != _pipeline_text(
        fields.get("main_lifecycle_record_id")
    ):
        return None, "pipeline_lifecycle_record_id_mismatch", True
    if stock_code != _pipeline_text(fields.get("main_lifecycle_stock_code")):
        return None, "pipeline_lifecycle_stock_code_mismatch", True
    observed_at = _pipeline_text(fields.get("main_lifecycle_observed_at"))
    try:
        _aware_datetime(observed_at)
    except (TypeError, ValueError):
        return None, "pipeline_lifecycle_explicit_timestamp_invalid", True

    data, data_error = _pipeline_transition_data(
        lifecycle_stage=lifecycle_stage,
        source_stage=source_stage,
        fields=fields,
        lifecycle_stock_code=stock_code,
        lifecycle_venue=(
            _pipeline_text(fields.get("main_lifecycle_venue")) or "UNKNOWN"
        ),
        lifecycle_observed_at=observed_at,
        lifecycle_trade_date=target_date,
        legacy_unattested_receive_clock_diagnostic=(
            legacy_unattested_receive_clock_diagnostic
        ),
    )
    if data is None:
        return None, data_error or "pipeline_lifecycle_data_invalid", True
    transition_observed_at = str(
        data.get("broker_execution_received_at") or observed_at
    )
    try:
        transition = build_transition(
            main_lifecycle_id=_pipeline_text(fields.get("main_lifecycle_id")),
            record_id=record_id,
            stock_code=stock_code,
            attempt_id=attempt_id,
            trade_date=target_date,
            stage=lifecycle_stage,
            observed_at=transition_observed_at,
            venue=_pipeline_text(fields.get("main_lifecycle_venue")) or "UNKNOWN",
            session_bucket=(
                _pipeline_text(fields.get("main_lifecycle_session_bucket")) or "unknown"
            ),
            data=data,
        )
    except (TypeError, ValueError) as exc:
        return None, f"pipeline_lifecycle_contract_invalid:{exc}", True
    return transition, None, True


def _validated_transition(
    raw_row: Mapping[str, Any], *, target_date: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Return an exact canonical transition or a non-joinable reason."""

    if raw_row.get("schema") != JOURNAL_SCHEMA:
        return None, "transition_schema_mismatch"
    if raw_row.get("trade_date") != target_date:
        return None, "transition_trade_date_mismatch"
    if raw_row.get("stage") not in VALID_STAGES:
        return None, "transition_stage_invalid"
    if not isinstance(raw_row.get("data"), dict):
        return None, "transition_data_invalid"
    direct_data = raw_row["data"]
    assert isinstance(direct_data, dict)
    if any(
        str(field).startswith(prefix)
        for field in direct_data
        for prefix in HISTORICAL_DIAGNOSTIC_RECOVERY_DATA_FIELD_PREFIXES
    ):
        # These fields are minted only by the bounded in-memory archived
        # diagnostic below.  A persisted/direct journal row cannot claim that
        # provenance or use it to manufacture receipt-derived custody.
        return None, "transition_historical_diagnostic_recovery_spoof"
    direct_submission_ordering_clock = str(
        direct_data.get("submission_ordering_clock") or ""
    ).strip()
    if direct_submission_ordering_clock == "broker_execution_received_at" or any(
        direct_data.get(field) is not None and direct_data.get(field) != ""
        for field in TRANSFORMED_SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES
        if field != "submission_ordering_clock"
    ):
        # Receipt-inferred submission custody is valid only after the strict
        # pipeline converter has attested its exact source stage and raw type
        # 00/FID908 envelope.  A direct canonical journal row has neither
        # source-stage provenance nor those raw fields and must not claim the
        # receive-clock skew bypass contract.
        return None, "transition_submission_custody_requires_pipeline_attestation"
    if any(
        direct_data.get(field_name) is not None and direct_data.get(field_name) != ""
        for field_name in (
            "carry_in_custody_schema",
            "lifecycle_origin",
            "carry_in_entry_observed_at",
            "carry_in_entry_source",
        )
    ):
        return None, "transition_carry_in_requires_pipeline_attestation"
    for key, expected in AUTHORITY_CONTRACT.items():
        if raw_row.get(key) != expected:
            return None, f"transition_authority_contract_mismatch:{key}"
    try:
        canonical = build_transition(
            main_lifecycle_id=str(raw_row.get("main_lifecycle_id") or ""),
            record_id=raw_row.get("record_id"),
            stock_code=raw_row.get("stock_code"),
            attempt_id=raw_row.get("attempt_id"),
            trade_date=target_date,
            stage=str(raw_row.get("stage") or ""),
            observed_at=str(raw_row.get("observed_at") or ""),
            venue=str(raw_row.get("venue") or "UNKNOWN"),
            session_bucket=str(raw_row.get("session_bucket") or "unknown"),
            data=raw_row.get("data"),
        )
    except (TypeError, ValueError) as exc:
        return None, f"transition_contract_invalid:{exc}"
    if dict(raw_row) != canonical:
        return None, "transition_content_or_lineage_mismatch"
    return canonical, None


@dataclass
class _LifecycleAccumulator:
    main_lifecycle_id: str
    record_id: str
    stock_code: str
    attempt_id: str
    trade_date: str
    venue: str
    session_bucket: str
    carry_in_custody: bool = False
    carry_in_entry_observed_at: str | None = None
    carry_in_entry_source: str | None = None
    stage_counts: dict[str, int] = field(default_factory=dict)
    transition_count: int = 0
    invalid_transition_count: int = 0
    invalid_reasons: list[str] = field(default_factory=list)
    first_observed_at: datetime | None = None
    last_observed_at: datetime | None = None
    scanner_first_at: datetime | None = None
    scanner_last_at: datetime | None = None
    scanner_sample_count: int = 0
    explicit_exposure_total_sec: float = 0.0
    explicit_exposure_current_start: datetime | None = None
    explicit_exposure_current_end: datetime | None = None
    explicit_exposure_last_start: datetime | None = None
    explicit_exposure_interval_count: int = 0
    market_observation_expected_count: int = 0
    bbo_observed_count: int = 0
    depth_observed_count: int = 0
    decision_trace_ids: list[str] = field(default_factory=list)
    trace_ids_overflow_count: int = 0
    partial_fill_event_count: int = 0
    full_fill_event_count: int = 0
    first_fill_at: datetime | None = None
    final_exit_at: datetime | None = None
    final_exit_source_sequence: int | None = None
    first_fill_execution_at: datetime | None = None
    final_exit_execution_at: datetime | None = None
    terminal_no_fill_at: datetime | None = None
    terminal_no_fill_reason: str | None = None
    final_exit_reconciled: bool = False
    requested_qty_max: float | None = None
    entry_fill_qty: float = 0.0
    scale_in_fill_qty: float = 0.0
    exit_qty: float = 0.0
    exit_amount_krw: float = 0.0
    exit_execution_leg_count: int = 0
    slippage_basis_covered_qty: float = 0.0
    slippage_basis_source_covered_qty: float = 0.0
    slippage_basis_amount_krw: float = 0.0
    slippage_basis_sources: list[str] = field(default_factory=list)
    economics_covered_exit_qty: dict[str, float] = field(default_factory=dict)
    open_qty: float = 0.0
    open_cost_krw: float = 0.0
    capital_time_krw_seconds: float = 0.0
    scale_in_decisions: list[str] = field(default_factory=list)
    fees_taxes_krw: float = 0.0
    slippage_krw: float = 0.0
    realized_net_pnl_krw: float = 0.0
    economics_observation_count: int = 0
    reviewed_cost_profile_sha256: str | None = None
    cost_hash_conflict: bool = False
    symbol_master_artifact_sha256: str | None = None
    symbol_hash_conflict: bool = False
    cost_verified_seen: bool = False
    cost_verified_all: bool = True
    symbol_verified_seen: bool = False
    symbol_verified_all: bool = True
    economics_fields_seen: set[str] = field(default_factory=set)
    observed_actual_broker_order_submitted: bool = False
    observed_real_order_evidence: bool = False
    source_population_scopes: set[str] = field(default_factory=set)
    legacy_unattested_receive_clock_recovery_count: int = 0
    historical_fill_before_submit_diagnostic_recovery_count: int = 0
    historical_fill_before_submit_diagnostic_recovery_provenance: list[
        dict[str, Any]
    ] = field(default_factory=list)
    historical_legacy_exit_submission_diagnostic_recovery_count: int = 0
    historical_legacy_exit_submission_diagnostic_recovery_provenance: list[
        dict[str, Any]
    ] = field(default_factory=list)
    post_final_stale_observation_quarantine_count: int = 0
    broker_late_arrival_stale_observation_quarantine_count: int = 0
    latest_reordered_exit_receipt_at: datetime | None = None
    latest_reordered_exit_receipt_source_sequence: int | None = None
    event_content_by_id: dict[str, str] = field(default_factory=dict)
    transition_replay_duplicate_count: int = 0
    broker_execution_content_by_identity: dict[str, str] = field(default_factory=dict)
    broker_execution_raw_content_by_identity: dict[str, str] = field(
        default_factory=dict
    )
    broker_execution_phase_by_identity: dict[str, str] = field(default_factory=dict)
    broker_execution_companion_content_by_identity: dict[str, str] = field(
        default_factory=dict
    )
    expected_receipt_companion_identity: str | None = None
    expected_receipt_companion_raw_content_sha256: str | None = None
    broker_execution_unique_count: int = 0
    broker_execution_replay_duplicate_count: int = 0
    broker_execution_conflict_count: int = 0
    broker_execution_receipt_companion_conflict_count: int = 0
    broker_execution_receipt_companion_replay_duplicate_count: int = 0
    broker_execution_order_progress_conflict_count: int = 0
    broker_execution_submission_link_conflict_count: int = 0
    broker_execution_provenance_state_counts: dict[str, int] = field(
        default_factory=dict
    )
    broker_order_progress_by_no: dict[str, tuple[int, int, int, int, datetime]] = field(
        default_factory=dict
    )
    submitted_order_phase_by_no: dict[str, str] = field(default_factory=dict)
    submitted_order_observed_at_by_no: dict[str, datetime] = field(default_factory=dict)
    submission_custody_binding_by_order_no: dict[
        str, tuple[str, int, int, int, int, str]
    ] = field(default_factory=dict)
    pending_submission_custody_binding_by_order_no: dict[
        str, tuple[str, int, int, int, int, str]
    ] = field(default_factory=dict)
    submitted_requested_qty_by_order_no: dict[str, int] = field(default_factory=dict)
    submitted_order_group_keys: set[tuple[str, tuple[tuple[str, int], ...]]] = field(
        default_factory=set
    )
    submitted_order_trace_id_by_no: dict[str, str] = field(default_factory=dict)
    submitted_order_context_by_no: dict[str, tuple[str, str, str, str]] = field(
        default_factory=dict
    )
    submission_leg_contract_phases: set[str] = field(default_factory=set)
    submission_self_summarizing_contract_phases: set[str] = field(default_factory=set)
    submission_contract_legacy_unattested_phases: set[str] = field(default_factory=set)
    submission_summary_quantities_by_phase: dict[str, dict[str, int]] = field(
        default_factory=dict
    )
    submission_summary_conflict_count: int = 0
    submission_summary_replay_duplicate_count: int = 0
    submitted_requested_qty_by_phase: dict[str, int] = field(default_factory=dict)
    executed_order_qty_by_phase: dict[str, dict[str, int]] = field(default_factory=dict)
    broker_submission_replay_duplicate_count: int = 0
    broker_execution_provenance_gap_count: int = 0
    broker_execution_provenance_gap_reasons: list[str] = field(default_factory=list)
    broker_execution_underlying_venue_unresolved_count: int = 0
    broker_execution_entry_covered_qty: float = 0.0
    broker_execution_exit_covered_qty: float = 0.0
    broker_execution_partial_count: int = 0
    broker_execution_full_count: int = 0
    broker_order_no_cross_lifecycle_conflict_count: int = 0
    broker_execution_cross_lifecycle_identity_conflict_count: int = 0
    decision_trace_stage_context_conflict_count: int = 0
    stage_context_counts: dict[tuple[str, str, str, str, str], int] = field(
        default_factory=dict
    )
    execution_venue_path_counts: dict[tuple[str, str, str, str], int] = field(
        default_factory=dict
    )
    decision_trace_context_counts: dict[tuple[str, str, str, str, str, str], int] = (
        field(default_factory=dict)
    )
    decision_trace_raw_context_counts: dict[
        tuple[str, str, str, str, str, str], int
    ] = field(default_factory=dict)
    decision_trace_context_by_stage: dict[
        tuple[str, str], tuple[str, str, str, str]
    ] = field(default_factory=dict)

    @classmethod
    def from_transition(cls, row: Mapping[str, Any]) -> _LifecycleAccumulator:
        data = row.get("data")
        carry_data = data if isinstance(data, Mapping) else {}
        carry_in_custody = (
            carry_data.get("carry_in_custody_schema") == CARRY_IN_CUSTODY_SCHEMA
            and carry_data.get("lifecycle_origin") == "preexisting_position_custody"
        )
        return cls(
            main_lifecycle_id=str(row["main_lifecycle_id"]),
            record_id=str(row["record_id"]),
            stock_code=str(row["stock_code"]),
            attempt_id=str(row["attempt_id"]),
            trade_date=str(row["trade_date"]),
            venue=str(row["venue"]),
            session_bucket=str(row["session_bucket"]),
            carry_in_custody=carry_in_custody,
            carry_in_entry_observed_at=(
                str(carry_data.get("carry_in_entry_observed_at"))
                if carry_in_custody
                else None
            ),
            carry_in_entry_source=(
                str(carry_data.get("carry_in_entry_source"))
                if carry_in_custody
                else None
            ),
        )

    def _invalid(self, reason: str) -> None:
        self.invalid_transition_count += 1
        if reason not in self.invalid_reasons and len(self.invalid_reasons) < 20:
            self.invalid_reasons.append(reason)

    def _matches_lineage(self, row: Mapping[str, Any]) -> bool:
        return all(
            (
                str(row.get("main_lifecycle_id")) == self.main_lifecycle_id,
                str(row.get("record_id")) == self.record_id,
                str(row.get("stock_code")) == self.stock_code,
                str(row.get("attempt_id")) == self.attempt_id,
                str(row.get("trade_date")) == self.trade_date,
            )
        )

    def _stage_contract_error(self, row: Mapping[str, Any]) -> str | None:
        stage = str(row.get("stage") or "")
        data = row.get("data")
        assert isinstance(data, dict)
        row_carry_in = data.get("carry_in_custody_schema") == CARRY_IN_CUSTODY_SCHEMA
        if self.carry_in_custody:
            if (
                not row_carry_in
                or data.get("lifecycle_origin") != "preexisting_position_custody"
                or data.get("carry_in_entry_observed_at")
                != self.carry_in_entry_observed_at
                or data.get("carry_in_entry_source") != self.carry_in_entry_source
            ):
                return "carry_in_custody_lineage_conflict"
            if stage not in {"holding", "exit"}:
                return "carry_in_custody_stage_invalid"
        elif row_carry_in or data.get("lifecycle_origin") == (
            "preexisting_position_custody"
        ):
            return "carry_in_custody_after_noncarry_start"
        if self.final_exit_at is not None or self.terminal_no_fill_at is not None:
            return "transition_after_terminal"
        if (
            self.transition_count == 0
            and stage != "scanner"
            and not (self.carry_in_custody and stage in {"holding", "exit"})
        ):
            return "scanner_transition_must_start_lifecycle"
        if stage == "scanner" and any(
            existing_stage in self.stage_counts
            for existing_stage in {"submit", "fill", "holding", "scale_in", "exit"}
        ):
            return "scanner_after_entry_phase"
        if stage == "entry_decision":
            if "scanner" not in self.stage_counts:
                return "entry_decision_before_scanner"
            if any(
                existing_stage in self.stage_counts
                for existing_stage in {"submit", "fill", "holding", "scale_in", "exit"}
            ):
                return "entry_decision_after_submit_phase"
        if stage == "submit":
            if "entry_decision" not in self.stage_counts:
                return "submit_before_entry_decision"
            if any(
                existing_stage in self.stage_counts
                for existing_stage in {"holding", "scale_in", "exit"}
            ):
                return "submit_after_fill_phase"
            if (
                self.first_fill_at is not None
                and data.get("submission_leg_contract") != "exact_broker_order_leg_v1"
            ):
                return "submit_after_fill_phase"
        if stage == "fill" and "submit" not in self.stage_counts:
            return "fill_before_submit"
        if stage == "fill" and "exit" in self.stage_counts:
            return "fill_after_exit_phase"
        if (
            stage == "holding"
            and self.first_fill_at is None
            and not self.carry_in_custody
        ):
            return "holding_before_fill"
        if stage == "scale_in":
            if self.first_fill_at is None:
                return "scale_in_before_fill"
            if "holding" not in self.stage_counts:
                return "scale_in_before_holding"
        if (
            stage == "exit"
            and data.get("terminal_no_fill") is not True
            and self.first_fill_at is None
            and not self.carry_in_custody
        ):
            return "exit_before_fill"
        trace_id = str(data.get("decision_trace_id") or "").strip()
        if trace_id:
            context = self._stage_context_identity(row, data=data)
            previous = self.decision_trace_context_by_stage.get((trace_id, stage))
            if previous is not None and previous != context:
                return "decision_trace_stage_context_conflict"
        return None

    @staticmethod
    def _stage_context(
        row: Mapping[str, Any], *, data: Mapping[str, Any]
    ) -> tuple[str, str, str, str]:
        venue = str(row.get("venue") or "UNKNOWN").strip().upper() or "UNKNOWN"
        session_bucket = (
            str(row.get("session_bucket") or "unknown").strip().lower() or "unknown"
        )
        venue_source = str(data.get("venue_source") or "transition.venue").strip()
        session_source = str(
            data.get("session_bucket_source") or "transition.session_bucket"
        ).strip()
        return venue, session_bucket, venue_source, session_source

    @classmethod
    def _stage_context_identity(
        cls, row: Mapping[str, Any], *, data: Mapping[str, Any]
    ) -> tuple[str, str, str, str]:
        venue, session_bucket, venue_source, session_source = cls._stage_context(
            row,
            data=data,
        )

        def canonical_source(value: str, *, venue_axis: bool) -> str:
            suffix = value.rsplit(".", 1)[-1]
            aliases = (
                {
                    "effective_venue",
                    "broker_actual_execution_venue",
                    "rising_missed_effective_venue",
                    "entry_setup_live_policy_effective_venue",
                    "venue",
                }
                if venue_axis
                else {
                    "holding_context_session",
                    "market_session_bucket",
                    "rising_missed_market_session_bucket",
                    "entry_setup_live_policy_session_bucket",
                    "session_bucket",
                }
            )
            return (
                "canonical_explicit_runtime_venue"
                if venue_axis and suffix in aliases
                else (
                    "canonical_explicit_runtime_session"
                    if not venue_axis and suffix in aliases
                    else value
                )
            )

        return (
            venue,
            session_bucket,
            canonical_source(venue_source, venue_axis=True),
            canonical_source(session_source, venue_axis=False),
        )

    def _duplicate_event_state(self, row: Mapping[str, Any]) -> str:
        event_id = str(row.get("event_id") or "").strip()
        content_hash = str(row.get("transition_content_sha256") or "").strip()
        previous = self.event_content_by_id.get(event_id)
        if previous is not None:
            if previous == content_hash:
                return "replay"
            return "conflict"
        if len(self.event_content_by_id) >= _EVENT_ID_LIMIT_PER_LIFECYCLE:
            return "limit"
        return "new"

    def _retain_event_identity(self, row: Mapping[str, Any]) -> None:
        event_id = str(row.get("event_id") or "").strip()
        content_hash = str(row.get("transition_content_sha256") or "").strip()
        self.event_content_by_id[event_id] = content_hash

    @staticmethod
    def _submission_phase(stage: str, data: Mapping[str, Any]) -> str | None:
        if stage == "submit" and data.get("terminal_no_fill") is not True:
            return "entry"
        if (
            stage == "scale_in"
            and data.get("scale_in_decision") == "ADD"
            and "fill_qty" not in data
            and data.get("actual_broker_order_submitted") is True
        ):
            return "scale_in"
        if (
            stage == "exit"
            and "exit_qty" not in data
            and data.get("actual_broker_order_submitted") is True
        ):
            return "exit"
        return None

    @staticmethod
    def _execution_phase(stage: str) -> str:
        if stage == "fill":
            return "entry"
        if stage == "scale_in":
            return "scale_in"
        return "exit"

    def _observe_order_submission(
        self,
        stage: str,
        data: Mapping[str, Any],
        *,
        observed_at: datetime,
        context: tuple[str, str, str, str],
    ) -> str:
        phase = self._submission_phase(stage, data)
        if phase is None:
            return "not_applicable"
        raw_order_numbers = str(data.get("broker_order_no_list") or "").split(",")
        order_numbers = tuple(
            order_no.strip() for order_no in raw_order_numbers if order_no.strip()
        )
        requested_qty = _finite_number(data.get("requested_qty"), positive=True)
        if not order_numbers or requested_qty is None or not requested_qty.is_integer():
            return "conflict"
        requested_int = int(requested_qty)
        try:
            quantities = normalize_submitted_order_quantities(
                data,
                list(order_numbers),
                requested_int,
            )
        except ValueError:
            return "conflict"
        custody_binding: tuple[str, int, int, int, int, str] | None = None
        if data.get("submission_custody_binding_schema") is not None:
            try:
                custody_order_no = str(data["submission_custody_broker_order_no"])
                custody_binding = (
                    str(data["submission_custody_broker_execution_no"]),
                    int(data["submission_custody_broker_order_qty"]),
                    int(data["submission_custody_broker_cumulative_qty"]),
                    int(data["submission_custody_broker_remaining_qty"]),
                    int(data["submission_custody_broker_unit_qty"]),
                    _aware_datetime(data["submission_causal_upper_bound_at"])
                    .astimezone(KST)
                    .isoformat(timespec="microseconds"),
                )
            except (KeyError, TypeError, ValueError):
                return "conflict"
            if data.get(
                "submission_custody_binding_schema"
            ) != SUBMISSION_CUSTODY_BINDING_SCHEMA or tuple(quantities) != (
                custody_order_no,
            ):
                return "conflict"
        group_key = (phase, tuple(quantities.items()))
        if group_key in self.submitted_order_group_keys:
            trace_id = str(data.get("decision_trace_id") or "").strip()
            if all(
                self.submitted_order_phase_by_no.get(order_no) == phase
                and self.submitted_requested_qty_by_order_no.get(order_no) == order_qty
                and self.submitted_order_trace_id_by_no.get(order_no, "") == trace_id
                and self.submitted_order_context_by_no.get(order_no) == context
                for order_no, order_qty in quantities.items()
            ):
                if custody_binding is not None and any(
                    self.submission_custody_binding_by_order_no.get(order_no)
                    not in {None, custody_binding}
                    for order_no in quantities
                ):
                    return "conflict"
                self.broker_submission_replay_duplicate_count += 1
                return "replay"
            return "conflict"
        for order_no in order_numbers:
            previous_phase = self.submitted_order_phase_by_no.get(order_no)
            if previous_phase is not None:
                return "conflict"
        self.submitted_order_group_keys.add(group_key)
        self.submitted_requested_qty_by_phase[phase] = (
            self.submitted_requested_qty_by_phase.get(phase, 0) + requested_int
        )
        observed_kst = observed_at.astimezone(KST)
        trace_id = str(data.get("decision_trace_id") or "").strip()
        for order_no, order_qty in quantities.items():
            self.submitted_order_phase_by_no[order_no] = phase
            self.submitted_order_observed_at_by_no[order_no] = observed_kst
            self.submitted_requested_qty_by_order_no[order_no] = order_qty
            self.submitted_order_trace_id_by_no[order_no] = trace_id
            self.submitted_order_context_by_no[order_no] = context
            if custody_binding is not None:
                self.submission_custody_binding_by_order_no[order_no] = custody_binding
                self.pending_submission_custody_binding_by_order_no[order_no] = (
                    custody_binding
                )
        if data.get("submission_leg_contract") == "exact_broker_order_leg_v1":
            self.submission_leg_contract_phases.add(phase)
        elif data.get("submission_leg_contract") == (
            "exact_broker_single_order_leg_v1"
        ):
            if (
                data.get("submission_leg_self_summarizing") is not True
                or len(quantities) != 1
            ):
                return "conflict"
            self.submission_self_summarizing_contract_phases.add(phase)
        if data.get("submission_contract_legacy_unattested") is True:
            self.submission_contract_legacy_unattested_phases.add(phase)
        return "new"

    def _pre_stage_submission_replay_state(
        self,
        row: Mapping[str, Any],
        *,
        stage: str,
        data: Mapping[str, Any],
    ) -> str:
        phase = self._submission_phase(stage, data)
        if phase is None or data.get("submission_summary_only") is True:
            return "not_applicable"
        raw_order_numbers = str(data.get("broker_order_no_list") or "").split(",")
        order_numbers = [value.strip() for value in raw_order_numbers if value.strip()]
        requested_qty = _finite_number(data.get("requested_qty"), positive=True)
        if not order_numbers or requested_qty is None or not requested_qty.is_integer():
            return "not_applicable"
        try:
            quantities = normalize_submitted_order_quantities(
                data,
                order_numbers,
                int(requested_qty),
            )
        except ValueError:
            return "not_applicable"
        group_key = (phase, tuple(quantities.items()))
        if group_key not in self.submitted_order_group_keys:
            return "not_applicable"
        context = self._stage_context_identity(row, data=data)
        trace_id = str(data.get("decision_trace_id") or "").strip()
        exact_order_binding = all(
            self.submitted_order_phase_by_no.get(order_no) == phase
            and self.submitted_requested_qty_by_order_no.get(order_no) == order_qty
            for order_no, order_qty in quantities.items()
        )
        if not exact_order_binding:
            return "conflict"
        if data.get("submission_custody_binding_schema") is not None:
            try:
                custody_order_no = str(data["submission_custody_broker_order_no"])
                incoming_custody_binding = (
                    str(data["submission_custody_broker_execution_no"]),
                    int(data["submission_custody_broker_order_qty"]),
                    int(data["submission_custody_broker_cumulative_qty"]),
                    int(data["submission_custody_broker_remaining_qty"]),
                    int(data["submission_custody_broker_unit_qty"]),
                    _aware_datetime(data["submission_causal_upper_bound_at"])
                    .astimezone(KST)
                    .isoformat(timespec="microseconds"),
                )
            except (KeyError, TypeError, ValueError):
                return "conflict"
            if (
                data.get("submission_custody_binding_schema")
                != SUBMISSION_CUSTODY_BINDING_SCHEMA
                or tuple(quantities) != (custody_order_no,)
                or any(
                    self.submitted_order_context_by_no.get(order_no) != context
                    for order_no in quantities
                )
                or any(
                    self.submission_custody_binding_by_order_no.get(order_no)
                    not in {None, incoming_custody_binding}
                    for order_no in quantities
                )
                or any(
                    self.submitted_order_trace_id_by_no.get(order_no, "")
                    and trace_id
                    and self.submitted_order_trace_id_by_no.get(order_no, "")
                    != trace_id
                    for order_no in quantities
                )
            ):
                return "conflict"
            if any(
                order_no not in self.submission_custody_binding_by_order_no
                for order_no in quantities
            ):
                # The ordinary broker-response row can be appended before the
                # receipt thread publishes its exact FID908-bound custody row.
                # Bind that later attestation to the already accepted exact
                # order without replaying or resizing the submit transition.
                return "custody_binding_corroboration"
        trace_and_context_match = all(
            self.submitted_order_trace_id_by_no.get(order_no, "") == trace_id
            and self.submitted_order_context_by_no.get(order_no) == context
            for order_no in quantities
        )
        if trace_and_context_match:
            return "replay"
        # A packet-ingress custody submit can be appended before the ordinary
        # broker-response telemetry in the exact race this contract repairs.
        # Treat the later row as corroboration only when the already accepted
        # submit is receipt-bound to every exact order/quantity, the canonical
        # stage context is unchanged, and no two non-empty trace IDs conflict.
        # This branch runs before timestamp/stage-order checks and does not
        # create, resize, or otherwise mutate the submitted order.
        if all(
            order_no in self.submission_custody_binding_by_order_no
            and self.submitted_order_context_by_no.get(order_no) == context
            and (
                not self.submitted_order_trace_id_by_no.get(order_no, "")
                or not trace_id
                or self.submitted_order_trace_id_by_no.get(order_no, "") == trace_id
            )
            for order_no in quantities
        ):
            previous_context = self.decision_trace_context_by_stage.get(
                (trace_id, stage)
            )
            if trace_id and previous_context not in {None, context}:
                return "conflict"
            if trace_id and any(
                not self.submitted_order_trace_id_by_no.get(order_no, "")
                for order_no in quantities
            ):
                return "custody_corroboration"
            return "replay"
        return "conflict"

    def _bind_custody_corroboration_trace(
        self,
        row: Mapping[str, Any],
        *,
        stage: str,
        data: Mapping[str, Any],
    ) -> None:
        """Retain a late exact submit trace without replaying the transition."""

        trace_id = str(data.get("decision_trace_id") or "").strip()
        if not trace_id:
            return
        order_numbers = [
            value.strip()
            for value in str(data.get("broker_order_no_list") or "").split(",")
            if value.strip()
        ]
        for order_no in order_numbers:
            if order_no in self.submission_custody_binding_by_order_no and not (
                self.submitted_order_trace_id_by_no.get(order_no, "")
            ):
                self.submitted_order_trace_id_by_no[order_no] = trace_id
        self._observe_trace_id(trace_id)
        # The late ordinary telemetry is an exact corroboration of the already
        # accepted custody submit, not a second transition.  Attach only its
        # submit-stage trace context; never backfill an entry/holding/exit
        # decision context that was absent from the original producer row.
        self._observe_decision_trace_context(row, stage=stage, data=data)

    def _bind_late_submission_custody(
        self,
        row: Mapping[str, Any],
        *,
        stage: str,
        data: Mapping[str, Any],
    ) -> None:
        """Attach a later exact receipt custody row to an existing submit."""

        binding = (
            str(data["submission_custody_broker_execution_no"]),
            int(data["submission_custody_broker_order_qty"]),
            int(data["submission_custody_broker_cumulative_qty"]),
            int(data["submission_custody_broker_remaining_qty"]),
            int(data["submission_custody_broker_unit_qty"]),
            _aware_datetime(data["submission_causal_upper_bound_at"])
            .astimezone(KST)
            .isoformat(timespec="microseconds"),
        )
        order_numbers = [
            value.strip()
            for value in str(data.get("broker_order_no_list") or "").split(",")
            if value.strip()
        ]
        for order_no in order_numbers:
            self.submission_custody_binding_by_order_no[order_no] = binding
            self.pending_submission_custody_binding_by_order_no[order_no] = binding
        self._retain_event_identity(row)
        self._bind_custody_corroboration_trace(row, stage=stage, data=data)

    def _consume_submission_summary(
        self,
        row: Mapping[str, Any],
        *,
        stage: str,
        data: Mapping[str, Any],
    ) -> bool:
        if data.get("submission_summary_only") is not True:
            return False
        phase = self._submission_phase(stage, data)
        raw_order_numbers = str(data.get("broker_order_no_list") or "").split(",")
        order_numbers = [value.strip() for value in raw_order_numbers if value.strip()]
        requested_qty = _finite_number(data.get("requested_qty"), positive=True)
        if phase is None or requested_qty is None or not requested_qty.is_integer():
            self.submission_summary_conflict_count += 1
            self._invalid("submission_summary_contract_conflict")
            return True
        try:
            quantities = normalize_submitted_order_quantities(
                data,
                order_numbers,
                int(requested_qty),
            )
        except ValueError:
            self.submission_summary_conflict_count += 1
            self._invalid("submission_summary_contract_conflict")
            return True
        previous = self.submission_summary_quantities_by_phase.get(phase)
        if previous is not None:
            if previous == quantities:
                self.submission_summary_replay_duplicate_count += 1
            else:
                self.submission_summary_conflict_count += 1
                self._invalid("submission_summary_content_conflict")
            return True
        self.submission_summary_quantities_by_phase[phase] = dict(quantities)
        self._retain_event_identity(row)
        return True

    @staticmethod
    def _execution_bearing_data(stage: str, data: Mapping[str, Any]) -> bool:
        if stage == "fill":
            return True
        if stage == "scale_in":
            return data.get("scale_in_decision") == "ADD" and "fill_qty" in data
        return stage == "exit" and "exit_qty" in data

    @staticmethod
    def _broker_execution_semantic_sha256(stage: str, data: Mapping[str, Any]) -> str:
        keys = (
            "broker_execution_content_sha256",
            "fill_state",
            "fill_qty",
            "fill_price",
            "exit_qty",
            "exit_price",
            "broker_reconciled",
            "reconciled_final_exit",
            "fees_taxes_krw",
            "slippage_krw",
            "slippage_basis_price",
            "slippage_basis_source",
            "realized_net_pnl_krw",
        )
        return _sha256(
            {
                "stage": stage,
                "data": {key: data.get(key) for key in keys if key in data},
            }
        )

    def _existing_broker_execution_state(
        self, stage: str, data: Mapping[str, Any]
    ) -> str:
        provenance_state = str(
            data.get("broker_execution_provenance_state") or ""
        ).strip()
        if not self._execution_bearing_data(stage, data) or provenance_state not in {
            "complete",
            "identity_complete_venue_unresolved",
        }:
            return "new"
        identity = str(data.get("broker_execution_identity") or "").strip()
        previous = self.broker_execution_content_by_identity.get(identity)
        if previous is None:
            return "new"
        semantic_hash = self._broker_execution_semantic_sha256(stage, data)
        return "replay" if previous == semantic_hash else "conflict"

    def _observe_broker_execution(
        self,
        stage: str,
        data: Mapping[str, Any],
        *,
        observed_at: datetime,
    ) -> str:
        """Return a bounded execution observation state."""

        if not self._execution_bearing_data(stage, data):
            return "not_applicable"
        state = (
            str(data.get("broker_execution_provenance_state") or "missing")
            .strip()
            .lower()
        )
        if state not in {
            "complete",
            "identity_complete_venue_unresolved",
            "missing",
            "incomplete",
            "invalid",
        }:
            state = "invalid"
        identity_complete = state in {
            "complete",
            "identity_complete_venue_unresolved",
        }
        if not identity_complete:
            self.broker_execution_provenance_state_counts[state] = (
                self.broker_execution_provenance_state_counts.get(state, 0) + 1
            )
            self.broker_execution_provenance_gap_count += 1
            reason = str(
                data.get("broker_execution_provenance_error")
                or "broker_execution_provenance_not_complete"
            )[:256]
            if (
                reason not in self.broker_execution_provenance_gap_reasons
                and len(self.broker_execution_provenance_gap_reasons) < 20
            ):
                self.broker_execution_provenance_gap_reasons.append(reason)
            return "gap"

        identity = str(data.get("broker_execution_identity") or "").strip()
        content_hash = str(data.get("broker_execution_content_sha256") or "").strip()
        if not identity or not SHA256_RE.fullmatch(content_hash):
            self.broker_execution_provenance_state_counts["invalid"] = (
                self.broker_execution_provenance_state_counts.get("invalid", 0) + 1
            )
            self.broker_execution_provenance_gap_count += 1
            reason = "broker_execution_identity_or_hash_invalid"
            if reason not in self.broker_execution_provenance_gap_reasons:
                self.broker_execution_provenance_gap_reasons.append(reason)
            return "gap"
        semantic_hash = self._broker_execution_semantic_sha256(stage, data)
        previous = self.broker_execution_content_by_identity.get(identity)
        if previous is not None:
            if previous == semantic_hash:
                self.broker_execution_replay_duplicate_count += 1
                return "replay"
            self.broker_execution_conflict_count += 1
            return "conflict"

        order_no = str(data.get("broker_execution_order_no") or "")
        execution_phase = self._execution_phase(stage)
        if self.submitted_order_phase_by_no.get(order_no) != execution_phase:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        submitted_at = self.submitted_order_observed_at_by_no.get(order_no)
        submitted_order_qty = self.submitted_requested_qty_by_order_no.get(order_no)
        if submitted_at is None or submitted_order_qty is None:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        expected_side = "SELL" if execution_phase == "exit" else "BUY"
        if (
            str(data.get("broker_execution_stock_code") or "") != self.stock_code
            or str(data.get("broker_execution_side") or "") != expected_side
        ):
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        try:
            order_qty = int(data["broker_execution_order_qty"])
            cumulative_qty = int(data["broker_execution_cumulative_fill_qty"])
            cumulative_amount = int(data["broker_execution_cumulative_fill_amount_krw"])
            remaining_qty = int(data["broker_execution_remaining_qty"])
            execution_price = int(data["broker_execution_price"])
            unit_qty = int(data["broker_execution_unit_fill_qty"])
            execution_no = str(data["broker_execution_no"])
            execution_at = _aware_datetime(
                data["broker_execution_occurred_at"]
            ).astimezone(KST)
        except (KeyError, TypeError, ValueError):
            self.broker_execution_provenance_state_counts["invalid"] = (
                self.broker_execution_provenance_state_counts.get("invalid", 0) + 1
            )
            self.broker_execution_provenance_gap_count += 1
            reason = "broker_execution_canonical_numeric_fields_invalid"
            if reason not in self.broker_execution_provenance_gap_reasons:
                self.broker_execution_provenance_gap_reasons.append(reason)
            return "gap"
        if order_qty != submitted_order_qty:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        pending_custody_binding = (
            self.pending_submission_custody_binding_by_order_no.get(order_no)
        )
        if pending_custody_binding is not None:
            (
                custody_execution_no,
                custody_order_qty,
                custody_cumulative_qty,
                custody_remaining_qty,
                custody_unit_qty,
                custody_causal_upper_bound_text,
            ) = pending_custody_binding
            try:
                custody_causal_upper_bound_at = _aware_datetime(
                    custody_causal_upper_bound_text
                ).astimezone(KST)
            except (TypeError, ValueError):
                self.broker_execution_submission_link_conflict_count += 1
                return "submission_conflict"
            if (
                execution_no != custody_execution_no
                or order_qty != custody_order_qty
                or cumulative_qty != custody_cumulative_qty
                or remaining_qty != custody_remaining_qty
                or unit_qty != custody_unit_qty
                or execution_at != custody_causal_upper_bound_at
            ):
                self.broker_execution_submission_link_conflict_count += 1
                return "submission_conflict"
        previous_progress = self.broker_order_progress_by_no.get(order_no)
        observed_kst = observed_at.astimezone(KST)
        if (
            pending_custody_binding is None
            and execution_at + timedelta(seconds=_BROKER_SUBMIT_CLOCK_SKEW_SEC)
            < submitted_at
        ):
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        if previous_progress is None:
            progress_valid = (
                cumulative_qty == unit_qty
                and cumulative_amount == unit_qty * execution_price
                and execution_at
                <= observed_kst
                + timedelta(seconds=BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC)
            )
        else:
            (
                previous_order_qty,
                previous_cumulative_qty,
                previous_cumulative_amount,
                previous_remaining_qty,
                previous_execution_at,
            ) = previous_progress
            progress_valid = all(
                (
                    order_qty == previous_order_qty,
                    cumulative_qty - previous_cumulative_qty == unit_qty,
                    cumulative_amount - previous_cumulative_amount
                    == unit_qty * execution_price,
                    remaining_qty < previous_remaining_qty,
                    execution_at >= previous_execution_at,
                    execution_at
                    <= observed_kst
                    + timedelta(seconds=BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC),
                )
            )
        if not progress_valid:
            self.broker_execution_order_progress_conflict_count += 1
            return "order_progress_conflict"

        phase_orders = self.executed_order_qty_by_phase.setdefault(execution_phase, {})
        previous_phase_order_qty = phase_orders.get(order_no)
        if (
            previous_phase_order_qty is not None
            and previous_phase_order_qty != order_qty
        ):
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        self.broker_execution_content_by_identity[identity] = semantic_hash
        if pending_custody_binding is not None:
            self.pending_submission_custody_binding_by_order_no.pop(order_no, None)
        self.broker_execution_raw_content_by_identity[identity] = content_hash
        self.broker_execution_phase_by_identity[identity] = execution_phase
        self._expect_receipt_companion(data)
        self.broker_order_progress_by_no[order_no] = (
            order_qty,
            cumulative_qty,
            cumulative_amount,
            remaining_qty,
            execution_at,
        )
        phase_orders[order_no] = order_qty
        self.broker_execution_unique_count += 1
        self.broker_execution_provenance_state_counts[state] = (
            self.broker_execution_provenance_state_counts.get(state, 0) + 1
        )
        if state == "identity_complete_venue_unresolved":
            self.broker_execution_underlying_venue_unresolved_count += 1
        fill_state = str(data.get("broker_execution_fill_state") or "")
        if fill_state == "partial":
            self.broker_execution_partial_count += 1
        elif fill_state == "full":
            self.broker_execution_full_count += 1
        return "new"

    def _receipt_companion_state(self, data: Mapping[str, Any]) -> str:
        """Bind a non-economic companion to a previously accepted receipt."""

        if data.get("broker_execution_receipt_companion") is not True:
            return "not_applicable"
        identity = str(data.get("broker_execution_identity") or "").strip()
        declared_identity = str(
            data.get("broker_execution_receipt_companion_of_identity") or ""
        ).strip()
        content_hash = str(data.get("broker_execution_content_sha256") or "").strip()
        accepted_content_hash = self.broker_execution_raw_content_by_identity.get(
            identity
        )
        accepted_phase = self.broker_execution_phase_by_identity.get(identity)
        previous_companion_hash = (
            self.broker_execution_companion_content_by_identity.get(identity)
        )
        if (
            not identity
            or declared_identity != identity
            or not SHA256_RE.fullmatch(content_hash)
            or str(data.get("broker_execution_side") or "").strip() != "BUY"
            or accepted_phase != "entry"
        ):
            return "conflict"
        if previous_companion_hash is not None:
            if previous_companion_hash == content_hash:
                return "replay"
            return "conflict"
        if (
            accepted_content_hash is None
            or accepted_content_hash != content_hash
            or self.expected_receipt_companion_identity != identity
            or self.expected_receipt_companion_raw_content_sha256 != content_hash
        ):
            return "conflict"
        return "new"

    def _expect_receipt_companion(self, data: Mapping[str, Any]) -> None:
        self.expected_receipt_companion_identity = str(
            data.get("broker_execution_identity") or ""
        ).strip()
        self.expected_receipt_companion_raw_content_sha256 = str(
            data.get("broker_execution_content_sha256") or ""
        ).strip()

    def _clear_expected_receipt_companion(
        self, data: Mapping[str, Any] | None = None
    ) -> None:
        if data is not None:
            identity = str(data.get("broker_execution_identity") or "").strip()
            content_hash = str(
                data.get("broker_execution_content_sha256") or ""
            ).strip()
            if (
                self.expected_receipt_companion_identity != identity
                or self.expected_receipt_companion_raw_content_sha256 != content_hash
            ):
                return
        self.expected_receipt_companion_identity = None
        self.expected_receipt_companion_raw_content_sha256 = None

    def _retain_receipt_companion(self, data: Mapping[str, Any]) -> None:
        if data.get("broker_execution_receipt_companion") is not True:
            return
        identity = str(data.get("broker_execution_identity") or "").strip()
        content_hash = str(data.get("broker_execution_content_sha256") or "").strip()
        self.broker_execution_companion_content_by_identity[identity] = content_hash

    def _integrate_capital(self, timestamp: datetime) -> bool:
        if self.last_observed_at is None:
            return True
        elapsed = (timestamp - self.last_observed_at).total_seconds()
        if elapsed < 0:
            self._invalid("lifecycle_timestamp_regression")
            return False
        self.capital_time_krw_seconds += self.open_cost_krw * elapsed
        return True

    def _observe_stage_context(
        self, row: Mapping[str, Any], *, stage: str, data: Mapping[str, Any]
    ) -> None:
        venue, session_bucket, venue_source, session_source = self._stage_context(
            row,
            data=data,
        )
        context_key = (
            stage,
            venue,
            session_bucket,
            venue_source,
            session_source,
        )
        self.stage_context_counts[context_key] = (
            self.stage_context_counts.get(context_key, 0) + 1
        )
        self._observe_decision_trace_context(row, stage=stage, data=data)

    def _observe_decision_trace_context(
        self, row: Mapping[str, Any], *, stage: str, data: Mapping[str, Any]
    ) -> None:
        trace_id = str(data.get("decision_trace_id") or "").strip()
        if trace_id:
            venue, session_bucket, venue_source, session_source = self._stage_context(
                row, data=data
            )
            canonical_context = self._stage_context_identity(row, data=data)
            self.decision_trace_context_by_stage.setdefault(
                (trace_id, stage),
                canonical_context,
            )
            trace_context_key = (
                trace_id,
                stage,
                *canonical_context,
            )
            self.decision_trace_context_counts[trace_context_key] = (
                self.decision_trace_context_counts.get(trace_context_key, 0) + 1
            )
            raw_trace_context_key = (
                trace_id,
                stage,
                venue,
                session_bucket,
                venue_source,
                session_source,
            )
            self.decision_trace_raw_context_counts[raw_trace_context_key] = (
                self.decision_trace_raw_context_counts.get(raw_trace_context_key, 0) + 1
            )

    def _observe_execution_path(
        self, *, stage: str, data: Mapping[str, Any]
    ) -> datetime | None:
        state = str(data.get("broker_execution_provenance_state") or "").strip()
        if state not in {"complete", "identity_complete_venue_unresolved"}:
            return None
        reported_scope = str(
            data.get("broker_execution_reported_venue_scope") or "UNKNOWN"
        ).strip()
        actual_venue = str(
            data.get("broker_execution_actual_venue") or "UNRESOLVED"
        ).strip()
        resolution_state = str(
            data.get("broker_execution_venue_resolution_state") or "unknown"
        ).strip()
        path_key = (stage, reported_scope, actual_venue, resolution_state)
        self.execution_venue_path_counts[path_key] = (
            self.execution_venue_path_counts.get(path_key, 0) + 1
        )
        try:
            return _aware_datetime(data.get("broker_execution_occurred_at"))
        except (TypeError, ValueError):
            # ``build_transition`` already rejects this for exact receipts.  A
            # defensive null here prevents any synthesized duration if a
            # future compatibility reader bypasses that builder.
            self._invalid("broker_execution_occurrence_timestamp_invalid")
            return None

    def _observe_trace_id(self, value: Any) -> None:
        trace_id = str(value or "").strip()
        if not trace_id or trace_id in self.decision_trace_ids:
            return
        if len(self.decision_trace_ids) >= _TRACE_ID_LIMIT:
            self.trace_ids_overflow_count += 1
            self._invalid("decision_trace_id_limit_exceeded")
            return
        self.decision_trace_ids.append(trace_id)

    def _observe_interval(self, data: Mapping[str, Any]) -> None:
        start_value = data.get("session_exposure_start_at")
        end_value = data.get("session_exposure_end_at")
        if start_value is None and end_value is None:
            return
        if start_value is None or end_value is None:
            self._invalid("session_exposure_interval_incomplete")
            return
        try:
            start_at = _aware_datetime(start_value)
            end_at = _aware_datetime(end_value)
        except (TypeError, ValueError):
            self._invalid("session_exposure_interval_invalid")
            return
        if end_at <= start_at:
            self._invalid("session_exposure_interval_non_positive")
            return
        if (
            self.explicit_exposure_last_start is not None
            and start_at < self.explicit_exposure_last_start
        ):
            self._invalid("session_exposure_interval_out_of_order")
            return
        self.explicit_exposure_last_start = start_at
        self.explicit_exposure_interval_count += 1
        if self.explicit_exposure_current_start is None:
            self.explicit_exposure_current_start = start_at
            self.explicit_exposure_current_end = end_at
            return
        assert self.explicit_exposure_current_end is not None
        if start_at <= self.explicit_exposure_current_end:
            self.explicit_exposure_current_end = max(
                self.explicit_exposure_current_end,
                end_at,
            )
            return
        self.explicit_exposure_total_sec += (
            self.explicit_exposure_current_end - self.explicit_exposure_current_start
        ).total_seconds()
        self.explicit_exposure_current_start = start_at
        self.explicit_exposure_current_end = end_at

    def _observe_hashes(self, data: Mapping[str, Any]) -> None:
        cost_hash = str(data.get("cost_artifact_sha256") or "").strip()
        if cost_hash:
            if not SHA256_RE.fullmatch(cost_hash):
                self._invalid("cost_artifact_sha256_invalid")
            elif self.reviewed_cost_profile_sha256 is None:
                self.reviewed_cost_profile_sha256 = cost_hash
            elif self.reviewed_cost_profile_sha256 != cost_hash:
                self.cost_hash_conflict = True
                self._invalid("cost_artifact_hash_conflict")
            self.cost_verified_seen = True
            self.cost_verified_all = (
                self.cost_verified_all and data.get("cost_artifact_verified") is True
            )
        symbol_hash = str(data.get("symbol_master_sha256") or "").strip()
        if symbol_hash:
            if not SHA256_RE.fullmatch(symbol_hash):
                self._invalid("symbol_master_sha256_invalid")
            elif self.symbol_master_artifact_sha256 is None:
                self.symbol_master_artifact_sha256 = symbol_hash
            elif self.symbol_master_artifact_sha256 != symbol_hash:
                self.symbol_hash_conflict = True
                self._invalid("symbol_master_hash_conflict")
            self.symbol_verified_seen = True
            self.symbol_verified_all = (
                self.symbol_verified_all and data.get("symbol_master_verified") is True
            )

    def bind_reference_contract(
        self,
        *,
        reviewed_cost_profile_sha256: str | None,
        reviewed_cost_profile_verified: bool,
        symbol_master_artifact_sha256: str | None,
        symbol_master_artifact_verified: bool,
    ) -> None:
        if reviewed_cost_profile_sha256 is not None:
            self.reviewed_cost_profile_sha256 = reviewed_cost_profile_sha256
            self.cost_verified_seen = True
            self.cost_verified_all = reviewed_cost_profile_verified
        if symbol_master_artifact_sha256 is not None:
            self.symbol_master_artifact_sha256 = symbol_master_artifact_sha256
            self.symbol_verified_seen = True
            self.symbol_verified_all = symbol_master_artifact_verified

    def _observe_economics(self, stage: str, data: Mapping[str, Any]) -> None:
        found = False
        for key in ("fees_taxes_krw", "slippage_krw", "realized_net_pnl_krw"):
            if key not in data:
                continue
            if stage != "exit":
                self._invalid(f"{key}_outside_exit")
                continue
            value = _finite_number(
                data.get(key),
                nonnegative=key in {"fees_taxes_krw", "slippage_krw"},
            )
            if value is None:
                self._invalid(f"{key}_invalid")
                continue
            setattr(self, key, getattr(self, key) + value)
            self.economics_fields_seen.add(key)
            found = True
        if found:
            self.economics_observation_count += 1

    def _add_fill(self, *, quantity: float, price: float, scale_in: bool) -> None:
        self.open_qty += quantity
        self.open_cost_krw += quantity * price
        if scale_in:
            self.scale_in_fill_qty += quantity
        else:
            self.entry_fill_qty += quantity

    def _apply_exit(self, quantity: float, price: float) -> None:
        if quantity > self.open_qty + _QUANTITY_EPSILON:
            self._invalid("exit_qty_exceeds_open_qty")
            return
        average_cost = self.open_cost_krw / self.open_qty if self.open_qty > 0 else 0.0
        self.open_qty = max(0.0, self.open_qty - quantity)
        self.open_cost_krw = max(0.0, self.open_cost_krw - average_cost * quantity)
        self.exit_qty += quantity
        self.exit_amount_krw += quantity * price
        self.exit_execution_leg_count += 1

    def consume(
        self,
        row: Mapping[str, Any],
        *,
        source_sequence: int | None = None,
        trusted_historical_diagnostic_recovery: Mapping[str, Any] | None = None,
        trusted_broker_late_arrival_reordered: bool = False,
    ) -> None:
        if not self._matches_lineage(row):
            self._invalid("cross_attempt_join_blocked")
            return
        duplicate_state = self._duplicate_event_state(row)
        if duplicate_state == "replay":
            self.transition_replay_duplicate_count += 1
            data = row.get("data")
            if (
                isinstance(data, dict)
                and self._existing_broker_execution_state(
                    str(row.get("stage") or ""), data
                )
                == "replay"
            ):
                self.broker_execution_replay_duplicate_count += 1
                self._expect_receipt_companion(data)
            return
        if duplicate_state == "conflict":
            self._invalid("duplicate_event_id_content_conflict")
            return
        if duplicate_state == "limit":
            self._invalid("transition_event_identity_limit_exceeded")
            return
        stage = str(row["stage"])
        data = row["data"]
        assert isinstance(data, dict)
        if trusted_historical_diagnostic_recovery is not None:
            recovery_provenance = trusted_historical_diagnostic_recovery
            recovery_schema = recovery_provenance.get("schema")
            if (
                recovery_provenance.get("in_memory_only") is not True
                or recovery_provenance.get("raw_source_mutated") is not False
                or recovery_provenance.get("promotion_evidence_eligible") is not False
                or recovery_provenance.get("r2_r3_evidence_eligible") is not False
            ):
                self._invalid("historical_diagnostic_recovery_contract_invalid")
                return
            if (
                recovery_schema
                == HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA
                and stage == "submit"
            ):
                self.historical_fill_before_submit_diagnostic_recovery_count += 1
                if (
                    len(
                        self.historical_fill_before_submit_diagnostic_recovery_provenance
                    )
                    < _GAP_EXAMPLE_LIMIT
                ):
                    self.historical_fill_before_submit_diagnostic_recovery_provenance.append(
                        dict(recovery_provenance)
                    )
            elif (
                recovery_schema
                == HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA
                and stage == "exit"
                and "exit_qty" not in data
                and data.get("actual_broker_order_submitted") is True
                and data.get("submission_leg_contract")
                == "exact_broker_single_order_leg_v1"
                and data.get("submission_leg_self_summarizing") is True
                and data.get("submission_contract_legacy_unattested") is True
            ):
                self.historical_legacy_exit_submission_diagnostic_recovery_count += 1
                if (
                    len(
                        self.historical_legacy_exit_submission_diagnostic_recovery_provenance
                    )
                    < _GAP_EXAMPLE_LIMIT
                ):
                    self.historical_legacy_exit_submission_diagnostic_recovery_provenance.append(
                        dict(recovery_provenance)
                    )
            else:
                self._invalid("historical_diagnostic_recovery_contract_invalid")
                return
        source_population_scope = str(data.get("source_population_scope") or "")
        if source_population_scope in PIPELINE_SOURCE_POPULATION_SCOPES:
            self.source_population_scopes.add(source_population_scope)
        # Classify the report population from concrete order evidence before
        # stage-order validation.  A valid broker submit/receipt that is later
        # rejected as out-of-order must remain in the real-order defect
        # denominator instead of being hidden as a candidate observation.
        if data.get("actual_broker_order_submitted") is True or str(
            data.get("broker_execution_provenance_state") or ""
        ) in {"complete", "identity_complete_venue_unresolved"}:
            self.observed_real_order_evidence = True
        if data.get("legacy_unattested_receive_clock_recovered") is True:
            self.legacy_unattested_receive_clock_recovery_count += 1
        if data.get("broker_execution_receipt_companion") is not True:
            # Companion binding is adjacency-scoped.  Any intervening distinct
            # transition consumes the previous expectation; an accepted new
            # or replayed execution below installs its own expectation.
            self._clear_expected_receipt_companion()
        if self._consume_submission_summary(
            row,
            stage=stage,
            data=data,
        ):
            return
        early_submission_replay = self._pre_stage_submission_replay_state(
            row,
            stage=stage,
            data=data,
        )
        if early_submission_replay in {
            "replay",
            "custody_corroboration",
            "custody_binding_corroboration",
        }:
            self.broker_submission_replay_duplicate_count += 1
            if early_submission_replay == "custody_corroboration":
                self._bind_custody_corroboration_trace(
                    row,
                    stage=stage,
                    data=data,
                )
            elif early_submission_replay == "custody_binding_corroboration":
                self._bind_late_submission_custody(
                    row,
                    stage=stage,
                    data=data,
                )
            return
        if early_submission_replay == "conflict":
            self.broker_execution_submission_link_conflict_count += 1
            self._invalid("broker_submission_replay_context_conflict")
            return
        existing_broker_execution = self._existing_broker_execution_state(stage, data)
        if existing_broker_execution == "replay":
            self.broker_execution_replay_duplicate_count += 1
            self._expect_receipt_companion(data)
            return
        if existing_broker_execution == "conflict":
            self.broker_execution_conflict_count += 1
            self._invalid("broker_execution_identity_content_conflict")
            return
        companion_state = self._receipt_companion_state(data)
        if companion_state == "replay":
            self.broker_execution_receipt_companion_replay_duplicate_count += 1
            self._clear_expected_receipt_companion(data)
            return
        if companion_state == "conflict":
            self.broker_execution_receipt_companion_conflict_count += 1
            self._clear_expected_receipt_companion()
            self._invalid("broker_execution_receipt_companion_binding_conflict")
            return
        if companion_state == "new":
            self._clear_expected_receipt_companion(data)
        try:
            timestamp = _aware_datetime(row.get("observed_at"))
        except (TypeError, ValueError):
            self._invalid("transition_timestamp_invalid")
            return
        post_final_stale_observation = bool(
            self.final_exit_at is not None
            and self.final_exit_source_sequence is not None
            and source_sequence is not None
            and source_sequence < self.final_exit_source_sequence
            and timestamp >= self.final_exit_at
        )
        post_reordered_exit_stale_observation = bool(
            self.latest_reordered_exit_receipt_at is not None
            and self.latest_reordered_exit_receipt_source_sequence is not None
            and source_sequence is not None
            and source_sequence < self.latest_reordered_exit_receipt_source_sequence
            and timestamp >= self.latest_reordered_exit_receipt_at
        )
        if (
            (post_final_stale_observation or post_reordered_exit_stale_observation)
            and stage in {"holding", "scale_in", "exit"}
            and data.get("actual_broker_order_submitted") is not True
            and str(data.get("broker_execution_provenance_state") or "")
            not in {"complete", "identity_complete_venue_unresolved"}
            and not any(
                field_name in data
                for field_name in ("fill_qty", "exit_qty", "terminal_no_fill")
            )
        ):
            # A bounded reorder can place an exact broker receipt before
            # an already-appended holding/decision row whose observation clock
            # is later.  That row saw stale position state and must not supply
            # stage/trace/coverage evidence, but it is not a malformed broker
            # transition and therefore must not poison the recovered lifecycle.
            self._retain_event_identity(row)
            self.broker_late_arrival_stale_observation_quarantine_count += 1
            if post_final_stale_observation:
                self.post_final_stale_observation_quarantine_count += 1
            return
        stage_error = self._stage_contract_error(row)
        if stage_error is not None:
            if stage_error == "decision_trace_stage_context_conflict":
                self.decision_trace_stage_context_conflict_count += 1
            self._invalid(stage_error)
            return
        if self.last_observed_at is not None and timestamp < self.last_observed_at:
            self._invalid("lifecycle_timestamp_regression")
            return
        submission_state = self._observe_order_submission(
            stage,
            data,
            observed_at=timestamp,
            context=self._stage_context_identity(row, data=data),
        )
        if submission_state == "replay":
            return
        if submission_state == "conflict":
            self.broker_execution_submission_link_conflict_count += 1
            self._invalid("broker_submission_identity_or_quantity_conflict")
            return
        broker_execution_state = self._observe_broker_execution(
            stage,
            data,
            observed_at=timestamp,
        )
        if broker_execution_state == "replay":
            return
        if broker_execution_state == "conflict":
            self._invalid("broker_execution_identity_content_conflict")
            return
        if broker_execution_state == "order_progress_conflict":
            self._invalid("broker_execution_order_progress_conflict")
            return
        if broker_execution_state == "submission_conflict":
            self._invalid("broker_execution_submission_link_conflict")
            return
        if not self._integrate_capital(timestamp):
            return
        self._retain_event_identity(row)
        if companion_state == "new":
            self._retain_receipt_companion(data)

        self.transition_count += 1
        self.first_observed_at = self.first_observed_at or timestamp
        self.last_observed_at = timestamp
        self.stage_counts[stage] = self.stage_counts.get(stage, 0) + 1
        self._observe_stage_context(row, stage=stage, data=data)
        execution_occurred_at = (
            self._observe_execution_path(stage=stage, data=data)
            if broker_execution_state == "new"
            else None
        )

        if data.get("market_observation_expected") is not False:
            self.market_observation_expected_count += 1
            if data.get("bbo_observed") is True:
                self.bbo_observed_count += 1
            if data.get("depth_observed") is True:
                self.depth_observed_count += 1
        self._observe_trace_id(data.get("decision_trace_id"))
        self._observe_interval(data)
        self._observe_hashes(data)
        self._observe_economics(stage, data)
        if data.get("actual_broker_order_submitted") is True:
            self.observed_actual_broker_order_submitted = True

        requested_qty = _finite_number(data.get("requested_qty"), positive=True)
        if "requested_qty" in data and requested_qty is None:
            self._invalid("requested_qty_invalid")
        if requested_qty is not None:
            self.requested_qty_max = max(self.requested_qty_max or 0.0, requested_qty)

        if stage == "scanner":
            if self.scanner_first_at is None:
                self.scanner_first_at = timestamp
                self.scanner_last_at = timestamp
                self.scanner_sample_count = 1
            elif data.get("heartbeat") is True:
                self.scanner_last_at = timestamp
                self.scanner_sample_count += 1
        elif data.get("heartbeat") is True:
            if self.scanner_first_at is None:
                self.scanner_first_at = timestamp
            self.scanner_last_at = timestamp
            self.scanner_sample_count += 1

        if data.get("terminal_no_fill") is True:
            if self.first_fill_at is not None:
                self._invalid("terminal_no_fill_after_fill")
            self.terminal_no_fill_at = timestamp
            self.terminal_no_fill_reason = str(data.get("terminal_reason") or "unknown")

        if stage == "fill":
            if self.terminal_no_fill_at is not None:
                self._invalid("fill_after_terminal_no_fill")
            fill_state = str(data.get("fill_state"))
            if fill_state == "partial":
                self.partial_fill_event_count += 1
            elif fill_state == "full":
                self.full_fill_event_count += 1
            quantity = _finite_number(data.get("fill_qty"), positive=True)
            price = _finite_number(data.get("fill_price"), positive=True)
            if quantity is not None and price is not None:
                self.first_fill_at = self.first_fill_at or timestamp
                if execution_occurred_at is not None:
                    if self.first_fill_execution_at is None:
                        self.first_fill_execution_at = execution_occurred_at
                    else:
                        self.first_fill_execution_at = min(
                            self.first_fill_execution_at,
                            execution_occurred_at,
                        )
                self._add_fill(quantity=quantity, price=price, scale_in=False)
                if broker_execution_state == "new":
                    self.broker_execution_entry_covered_qty += quantity

        if stage == "scale_in":
            decision = str(data.get("scale_in_decision") or "")
            if decision and decision not in self.scale_in_decisions:
                self.scale_in_decisions.append(decision)
            if decision == "ADD":
                quantity = _finite_number(data.get("fill_qty"), positive=True)
                price = _finite_number(data.get("fill_price"), positive=True)
                if quantity is not None and price is not None:
                    if self.first_fill_at is None:
                        self._invalid("scale_in_add_before_entry_fill")
                    else:
                        self._add_fill(quantity=quantity, price=price, scale_in=True)
                        if broker_execution_state == "new":
                            self.broker_execution_entry_covered_qty += quantity

        if stage == "exit":
            quantity = _finite_number(data.get("exit_qty"), positive=True)
            price = _finite_number(data.get("exit_price"), positive=True)
            if "exit_qty" in data and quantity is None:
                self._invalid("exit_qty_invalid")
            if "exit_price" in data and price is None:
                self._invalid("exit_price_invalid")
            if (quantity is None) != (price is None):
                self._invalid("exit_price_qty_pair_incomplete")
            if quantity is not None and price is not None:
                exit_applied = False
                if self.carry_in_custody:
                    self.exit_qty += quantity
                    self.exit_amount_krw += quantity * price
                    self.exit_execution_leg_count += 1
                    exit_applied = True
                else:
                    open_qty_before = self.open_qty
                    self._apply_exit(quantity, price)
                    exit_applied = self.open_qty < open_qty_before
                if exit_applied:
                    if (
                        trusted_broker_late_arrival_reordered
                        and broker_execution_state == "new"
                        and source_sequence is not None
                    ):
                        self.latest_reordered_exit_receipt_at = timestamp
                        self.latest_reordered_exit_receipt_source_sequence = (
                            source_sequence
                        )
                    if broker_execution_state == "new":
                        self.broker_execution_exit_covered_qty += quantity
                    basis_price = _finite_number(
                        data.get("slippage_basis_price"), positive=True
                    )
                    if basis_price is not None:
                        self.slippage_basis_covered_qty += quantity
                        self.slippage_basis_amount_krw += quantity * basis_price
                        basis_source = str(
                            data.get("slippage_basis_source") or ""
                        ).strip()
                        if basis_source:
                            self.slippage_basis_source_covered_qty += quantity
                            if basis_source not in self.slippage_basis_sources:
                                self.slippage_basis_sources.append(basis_source)
                    for field_name in (
                        "fees_taxes_krw",
                        "slippage_krw",
                        "realized_net_pnl_krw",
                    ):
                        value = _finite_number(
                            data.get(field_name),
                            nonnegative=field_name
                            in {"fees_taxes_krw", "slippage_krw"},
                        )
                        if value is not None:
                            self.economics_covered_exit_qty[field_name] = (
                                self.economics_covered_exit_qty.get(field_name, 0.0)
                                + quantity
                            )
            if data.get("reconciled_final_exit") is True:
                self.final_exit_at = timestamp
                self.final_exit_source_sequence = source_sequence
                self.final_exit_execution_at = execution_occurred_at
                self.final_exit_reconciled = data.get("broker_reconciled") is True
                if self.first_fill_at is None and not self.carry_in_custody:
                    self._invalid("final_exit_without_fill")
                if self.open_qty > _QUANTITY_EPSILON:
                    self._invalid("final_exit_leaves_open_quantity")

    def _explicit_session_exposure_sec(self) -> float | None:
        total = self.explicit_exposure_total_sec
        if (
            self.explicit_exposure_current_start is not None
            and self.explicit_exposure_current_end is not None
        ):
            total += (
                self.explicit_exposure_current_end
                - self.explicit_exposure_current_start
            ).total_seconds()
        return total if self.explicit_exposure_interval_count > 0 else None

    def _session_exposure_sec(self) -> float | None:
        explicit = self._explicit_session_exposure_sec()
        if explicit is not None:
            return explicit
        if (
            self.scanner_sample_count >= 2
            and self.scanner_first_at is not None
            and self.scanner_last_at is not None
        ):
            elapsed = (self.scanner_last_at - self.scanner_first_at).total_seconds()
            return elapsed if elapsed >= 0 else None
        return None

    def _fill_completion_class(self) -> str:
        if self.partial_fill_event_count and self.full_fill_event_count:
            return "partial_then_full"
        if self.partial_fill_event_count:
            return "partial_only"
        if self.full_fill_event_count:
            return "full_only"
        return "no_fill"

    def _terminal_state(self) -> tuple[str, bool]:
        if self.carry_in_custody:
            if (
                self.final_exit_at is not None
                and self.final_exit_reconciled
                and self.exit_qty > _QUANTITY_EPSILON
                and self.broker_execution_exit_covered_qty + _QUANTITY_EPSILON
                >= self.exit_qty
            ):
                return "CUSTODY_CARRY_FINAL_EXIT_RECONCILED", False
            return "CUSTODY_CARRY_HELD", True
        if self.terminal_no_fill_at is not None and self.first_fill_at is None:
            return "TERMINAL_NO_FILL", False
        if (
            self.final_exit_at is not None
            and self.final_exit_reconciled
            and self.open_qty <= _QUANTITY_EPSILON
        ):
            return "FINAL_EXIT_RECONCILED", False
        if self.first_fill_at is not None:
            return "HELD", True
        return "INCOMPLETE", False

    def finalize(self) -> dict[str, Any]:
        terminal_state, right_censored = self._terminal_state()
        lifecycle_population_scope = (
            LIFECYCLE_POPULATION_REAL_SUBMITTED
            if self.observed_real_order_evidence
            else LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION
        )
        actual_duration: float | None = None
        if (
            self.first_fill_execution_at is not None
            and self.final_exit_execution_at is not None
        ):
            duration = (
                self.final_exit_execution_at - self.first_fill_execution_at
            ).total_seconds()
            if duration < 0:
                self._invalid("official_final_exit_precedes_first_fill")
            else:
                actual_duration = duration

        bbo_coverage = (
            100.0 * self.bbo_observed_count / self.market_observation_expected_count
            if self.market_observation_expected_count
            else None
        )
        depth_coverage = (
            100.0 * self.depth_observed_count / self.market_observation_expected_count
            if self.market_observation_expected_count
            else None
        )
        session_exposure = self._session_exposure_sec()
        lifecycle_rate = (
            3600.0 / session_exposure
            if session_exposure is not None and session_exposure > 0
            else None
        )
        reviewed_cost_hash = (
            None if self.cost_hash_conflict else self.reviewed_cost_profile_sha256
        )
        symbol_master_hash = (
            None if self.symbol_hash_conflict else self.symbol_master_artifact_sha256
        )

        blockers: list[str] = []
        if self.carry_in_custody:
            blockers.append("custody_carry_in_entry_lifecycle_non_promotable")
        sim_scope_real_order_contract_violation_count = int(
            self.observed_real_order_evidence
            and "sim_observation_only" in self.source_population_scopes
        )
        missing_stages = sorted(_REQUIRED_COMPLETE_STAGES - self.stage_counts.keys())
        if missing_stages:
            blockers.append("missing_required_stages:" + ",".join(missing_stages))
        if terminal_state not in {
            "FINAL_EXIT_RECONCILED",
            "CUSTODY_CARRY_FINAL_EXIT_RECONCILED",
        }:
            blockers.append("reconciled_final_exit_required")
        if actual_duration is None:
            blockers.append("official_first_fill_to_final_exit_duration_required")
        if session_exposure is None:
            blockers.append("session_exposure_requires_interval_or_two_samples")
        if not self.scale_in_decisions:
            blockers.append("scale_in_decision_missing")
        if not self.observed_actual_broker_order_submitted:
            blockers.append("actual_broker_order_submission_required")
        if self.legacy_unattested_receive_clock_recovery_count:
            blockers.append("legacy_unattested_receive_clock_diagnostic_non_promotable")
        if (
            self.historical_fill_before_submit_diagnostic_recovery_count
            or self.historical_legacy_exit_submission_diagnostic_recovery_count
        ):
            blockers.append(
                HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_NONPROMOTION_BLOCKER
            )
        if sim_scope_real_order_contract_violation_count:
            # Concrete broker truth always wins population classification, but
            # a producer that labels the same order as simulation has violated
            # the source authority contract. Keep it in the real denominator
            # and fail closed instead of laundering it into R2/R3 evidence.
            blockers.append("sim_scope_real_order_contract_violation")
        if bbo_coverage is None or bbo_coverage < 95.0:
            blockers.append("bbo_coverage_below_95pct")
        if depth_coverage is None or depth_coverage < 90.0:
            blockers.append("depth_coverage_below_90pct")
        if reviewed_cost_hash is None or not (
            self.cost_verified_seen and self.cost_verified_all
        ):
            blockers.append("reviewed_cost_profile_required")
        if symbol_master_hash is None or not (
            self.symbol_verified_seen and self.symbol_verified_all
        ):
            blockers.append("verified_symbol_master_required")
        missing_economics = {
            "fees_taxes_krw",
            "slippage_krw",
            "realized_net_pnl_krw",
        } - self.economics_fields_seen
        if missing_economics:
            blockers.append(
                "realized_economics_fields_missing:"
                + ",".join(sorted(missing_economics))
            )
        for field_name in (
            "fees_taxes_krw",
            "slippage_krw",
            "realized_net_pnl_krw",
        ):
            if (
                self.exit_qty > _QUANTITY_EPSILON
                and self.economics_covered_exit_qty.get(field_name, 0.0)
                + _QUANTITY_EPSILON
                < self.exit_qty
            ):
                blockers.append(f"{field_name}_exit_qty_coverage_incomplete")
        if (
            self.exit_qty > _QUANTITY_EPSILON
            and self.slippage_basis_covered_qty + _QUANTITY_EPSILON < self.exit_qty
        ):
            blockers.append("slippage_basis_exit_qty_coverage_incomplete")
        if (
            self.exit_qty > _QUANTITY_EPSILON
            and self.slippage_basis_source_covered_qty + _QUANTITY_EPSILON
            < self.exit_qty
        ):
            blockers.append("slippage_basis_source_exit_qty_coverage_incomplete")
        total_entry_execution_qty = self.entry_fill_qty + self.scale_in_fill_qty
        unreconciled_broker_order_count = sum(
            1
            for _, _, _, remaining_qty, _ in self.broker_order_progress_by_no.values()
            if remaining_qty > 0
        )
        submitted_order_coverage_gap_phases: list[str] = []
        submitted_order_qty_mismatch_phases: list[str] = []
        submission_summary_missing_phases: list[str] = []
        submission_summary_mismatch_phases: list[str] = []
        for phase, submitted_qty in sorted(
            self.submitted_requested_qty_by_phase.items()
        ):
            submitted_order_nos = {
                order_no
                for order_no, submitted_phase in self.submitted_order_phase_by_no.items()
                if submitted_phase == phase
            }
            executed_order_qty = self.executed_order_qty_by_phase.get(phase, {})
            if submitted_order_nos != set(executed_order_qty):
                submitted_order_coverage_gap_phases.append(phase)
            if sum(executed_order_qty.values()) != submitted_qty:
                submitted_order_qty_mismatch_phases.append(phase)
        for phase in sorted(self.submission_leg_contract_phases):
            if phase not in self.submission_summary_quantities_by_phase:
                submission_summary_missing_phases.append(phase)
        for phase, expected_quantities in sorted(
            self.submission_summary_quantities_by_phase.items()
        ):
            observed_quantities = {
                order_no: self.submitted_requested_qty_by_order_no[order_no]
                for order_no, submitted_phase in self.submitted_order_phase_by_no.items()
                if submitted_phase == phase
            }
            if observed_quantities != expected_quantities:
                submission_summary_mismatch_phases.append(phase)
        if self.broker_execution_provenance_gap_count:
            blockers.append("broker_execution_raw_provenance_gap")
        if self.broker_execution_underlying_venue_unresolved_count:
            blockers.append("broker_execution_underlying_venue_unresolved")
        if self.broker_execution_conflict_count:
            blockers.append("broker_execution_identity_content_conflict")
        if self.broker_execution_receipt_companion_conflict_count:
            blockers.append("broker_execution_receipt_companion_binding_conflict")
        if self.broker_execution_order_progress_conflict_count:
            blockers.append("broker_execution_order_progress_conflict")
        if self.broker_execution_submission_link_conflict_count:
            blockers.append("broker_execution_submission_link_conflict")
        if self.broker_order_no_cross_lifecycle_conflict_count:
            blockers.append("broker_order_no_cross_lifecycle_conflict")
        if self.broker_execution_cross_lifecycle_identity_conflict_count:
            blockers.append("broker_execution_identity_cross_lifecycle_conflict")
        if self.decision_trace_stage_context_conflict_count:
            blockers.append("decision_trace_stage_context_conflict")
        if submitted_order_coverage_gap_phases:
            blockers.append(
                "broker_execution_submitted_order_coverage_incomplete:"
                + ",".join(submitted_order_coverage_gap_phases)
            )
        if submitted_order_qty_mismatch_phases:
            blockers.append(
                "broker_execution_submitted_qty_mismatch:"
                + ",".join(submitted_order_qty_mismatch_phases)
            )
        if submission_summary_missing_phases:
            blockers.append(
                "broker_submission_summary_missing:"
                + ",".join(submission_summary_missing_phases)
            )
        if submission_summary_mismatch_phases:
            blockers.append(
                "broker_submission_summary_mismatch:"
                + ",".join(submission_summary_mismatch_phases)
            )
        if self.submission_contract_legacy_unattested_phases:
            blockers.append(
                "broker_submission_contract_legacy_unattested:"
                + ",".join(sorted(self.submission_contract_legacy_unattested_phases))
            )
        if self.submission_summary_conflict_count:
            blockers.append("broker_submission_summary_content_conflict")
        if unreconciled_broker_order_count:
            blockers.append("broker_execution_order_remaining_unreconciled")
        if (
            total_entry_execution_qty > _QUANTITY_EPSILON
            and self.broker_execution_entry_covered_qty + _QUANTITY_EPSILON
            < total_entry_execution_qty
        ):
            blockers.append("broker_execution_entry_qty_coverage_incomplete")
        if (
            self.exit_qty > _QUANTITY_EPSILON
            and self.broker_execution_exit_covered_qty + _QUANTITY_EPSILON
            < self.exit_qty
        ):
            blockers.append("broker_execution_exit_qty_coverage_incomplete")
        if self.invalid_transition_count:
            blockers.append("invalid_transition_present")

        row = {
            "main_lifecycle_id": self.main_lifecycle_id,
            "record_id": self.record_id,
            "stock_code": self.stock_code,
            "attempt_id": self.attempt_id,
            "trade_date": self.trade_date,
            "venue": self.venue,
            "session_bucket": self.session_bucket,
            "origin_venue": self.venue,
            "origin_session_bucket": self.session_bucket,
            "lifecycle_origin": (
                "preexisting_position_custody"
                if self.carry_in_custody
                else "same_trade_date_lifecycle"
            ),
            "carry_in_custody_schema": (
                CARRY_IN_CUSTODY_SCHEMA if self.carry_in_custody else None
            ),
            "carry_in_entry_observed_at": self.carry_in_entry_observed_at,
            "carry_in_entry_source": self.carry_in_entry_source,
            "stage_context_path": [
                {
                    "stage": stage,
                    "venue": venue,
                    "session_bucket": session_bucket,
                    "venue_source": venue_source,
                    "session_bucket_source": session_source,
                    "transition_count": count,
                }
                for (
                    stage,
                    venue,
                    session_bucket,
                    venue_source,
                    session_source,
                ), count in sorted(self.stage_context_counts.items())
            ],
            "decision_trace_context_path": [
                {
                    "decision_trace_id": trace_id,
                    "stage": stage,
                    "venue": venue,
                    "session_bucket": session_bucket,
                    "venue_source": venue_source,
                    "session_bucket_source": session_source,
                    "transition_count": count,
                }
                for (
                    trace_id,
                    stage,
                    venue,
                    session_bucket,
                    venue_source,
                    session_source,
                ), count in sorted(self.decision_trace_context_counts.items())
            ],
            "decision_trace_raw_context_path": [
                {
                    "decision_trace_id": trace_id,
                    "stage": stage,
                    "venue": venue,
                    "session_bucket": session_bucket,
                    "venue_source": venue_source,
                    "session_bucket_source": session_source,
                    "transition_count": count,
                }
                for (
                    trace_id,
                    stage,
                    venue,
                    session_bucket,
                    venue_source,
                    session_source,
                ), count in sorted(self.decision_trace_raw_context_counts.items())
            ],
            "decision_trace_stage_context_conflict_count": (
                self.decision_trace_stage_context_conflict_count
            ),
            "venue_path_changed": len({key[1] for key in self.stage_context_counts})
            > 1,
            "session_bucket_path_changed": len(
                {key[2] for key in self.stage_context_counts}
            )
            > 1,
            "execution_venue_path": [
                {
                    "stage": stage,
                    "reported_venue_scope": reported_scope,
                    "actual_venue": actual_venue,
                    "venue_resolution_state": resolution_state,
                    "execution_count": count,
                }
                for (
                    stage,
                    reported_scope,
                    actual_venue,
                    resolution_state,
                ), count in sorted(self.execution_venue_path_counts.items())
            ],
            "decision_trace_ids": self.decision_trace_ids,
            "transition_count": self.transition_count,
            "stage_counts": dict(sorted(self.stage_counts.items())),
            "terminal_state": terminal_state,
            "right_censored": right_censored,
            "terminal_no_fill_reason": self.terminal_no_fill_reason,
            "first_fill_at": (
                self.first_fill_at.isoformat() if self.first_fill_at else None
            ),
            "final_exit_at": (
                self.final_exit_at.isoformat() if self.final_exit_at else None
            ),
            "first_fill_execution_at": (
                self.first_fill_execution_at.isoformat()
                if self.first_fill_execution_at
                else None
            ),
            "final_exit_execution_at": (
                self.final_exit_execution_at.isoformat()
                if self.final_exit_execution_at
                else None
            ),
            "actual_holding_duration_sec": actual_duration,
            "duration_source": (
                "official_fid_908_first_fill_to_reconciled_final_exit"
                if actual_duration is not None
                else None
            ),
            "label_horizon_used": False,
            "session_exposure_sec": session_exposure,
            "lifecycle_rate_per_exposure_hour": lifecycle_rate,
            "capital_time_krw_hours": self.capital_time_krw_seconds / 3600.0,
            "requested_qty_max": self.requested_qty_max,
            "entry_fill_qty": self.entry_fill_qty,
            "scale_in_fill_qty": self.scale_in_fill_qty,
            "exit_qty": self.exit_qty,
            "exit_execution_leg_count": self.exit_execution_leg_count,
            "exit_vwap_price": (
                self.exit_amount_krw / self.exit_qty
                if self.exit_qty > _QUANTITY_EPSILON
                else None
            ),
            "slippage_basis_covered_qty": self.slippage_basis_covered_qty,
            "slippage_basis_source_covered_qty": (
                self.slippage_basis_source_covered_qty
            ),
            "slippage_basis_sources": self.slippage_basis_sources,
            "slippage_basis_vwap_price": (
                self.slippage_basis_amount_krw / self.slippage_basis_covered_qty
                if self.slippage_basis_covered_qty > _QUANTITY_EPSILON
                else None
            ),
            "economics_covered_exit_qty": dict(
                sorted(self.economics_covered_exit_qty.items())
            ),
            "open_qty_at_censor": self.open_qty,
            "partial_fill_event_count": self.partial_fill_event_count,
            "full_fill_event_count": self.full_fill_event_count,
            "fill_completion_class": self._fill_completion_class(),
            "broker_execution_official_reference_sha": (KIWOOM_OFFICIAL_REFERENCE_SHA),
            "broker_execution_provenance_schema": (BROKER_EXECUTION_PROVENANCE_SCHEMA),
            "broker_execution_raw_envelope_schema": (
                BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
            ),
            "broker_execution_timing_schema": BROKER_EXECUTION_TIMING_SCHEMA,
            "broker_execution_ordering_time_source": (
                BROKER_EXECUTION_ORDERING_TIME_SOURCE
            ),
            "broker_execution_occurrence_time_source": (
                BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
            ),
            "broker_execution_receive_time_source": (
                BROKER_EXECUTION_RECEIVE_TIME_SOURCE
            ),
            "broker_execution_unique_count": self.broker_execution_unique_count,
            "broker_execution_replay_duplicate_count": (
                self.broker_execution_replay_duplicate_count
            ),
            "broker_execution_conflict_count": (self.broker_execution_conflict_count),
            "broker_execution_receipt_companion_conflict_count": (
                self.broker_execution_receipt_companion_conflict_count
            ),
            "broker_execution_receipt_companion_replay_duplicate_count": (
                self.broker_execution_receipt_companion_replay_duplicate_count
            ),
            "broker_execution_order_progress_conflict_count": (
                self.broker_execution_order_progress_conflict_count
            ),
            "broker_execution_submission_link_conflict_count": (
                self.broker_execution_submission_link_conflict_count
            ),
            "broker_order_no_cross_lifecycle_conflict_count": (
                self.broker_order_no_cross_lifecycle_conflict_count
            ),
            "broker_execution_cross_lifecycle_identity_conflict_count": (
                self.broker_execution_cross_lifecycle_identity_conflict_count
            ),
            "broker_submission_replay_duplicate_count": (
                self.broker_submission_replay_duplicate_count
            ),
            "broker_submitted_order_count": len(self.submitted_order_phase_by_no),
            "broker_submitted_requested_qty_by_phase": dict(
                sorted(self.submitted_requested_qty_by_phase.items())
            ),
            "broker_submitted_requested_qty_by_order_no": dict(
                sorted(self.submitted_requested_qty_by_order_no.items())
            ),
            "broker_submission_custody_order_count": len(
                self.submission_custody_binding_by_order_no
            ),
            "broker_submission_custody_by_order_no": {
                order_no: {
                    "binding_schema": SUBMISSION_CUSTODY_BINDING_SCHEMA,
                    "broker_execution_no": binding[0],
                    "broker_order_qty": binding[1],
                    "broker_cumulative_qty": binding[2],
                    "broker_remaining_qty": binding[3],
                    "broker_unit_qty": binding[4],
                    "causal_upper_bound_at": binding[5],
                    "causal_upper_bound_source": (
                        BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
                    ),
                    "ordering_clock": "broker_execution_received_at",
                    "submission_time_source": (BROKER_EXECUTION_RECEIVE_TIME_SOURCE),
                }
                for order_no, binding in sorted(
                    self.submission_custody_binding_by_order_no.items()
                )
            },
            "broker_submission_custody_pending_order_count": len(
                self.pending_submission_custody_binding_by_order_no
            ),
            "broker_executed_order_qty_by_phase": {
                phase: dict(sorted(order_qty.items()))
                for phase, order_qty in sorted(self.executed_order_qty_by_phase.items())
            },
            "broker_submitted_order_coverage_gap_phases": (
                submitted_order_coverage_gap_phases
            ),
            "broker_submitted_order_qty_mismatch_phases": (
                submitted_order_qty_mismatch_phases
            ),
            "broker_submission_leg_contract_phases": sorted(
                self.submission_leg_contract_phases
            ),
            "broker_submission_self_summarizing_contract_phases": sorted(
                self.submission_self_summarizing_contract_phases
            ),
            "broker_submission_contract_legacy_unattested_phases": sorted(
                self.submission_contract_legacy_unattested_phases
            ),
            "broker_submission_summary_quantities_by_phase": {
                phase: dict(sorted(order_qty.items()))
                for phase, order_qty in sorted(
                    self.submission_summary_quantities_by_phase.items()
                )
            },
            "broker_submission_summary_missing_phases": (
                submission_summary_missing_phases
            ),
            "broker_submission_summary_mismatch_phases": (
                submission_summary_mismatch_phases
            ),
            "broker_submission_summary_conflict_count": (
                self.submission_summary_conflict_count
            ),
            "broker_submission_summary_replay_duplicate_count": (
                self.submission_summary_replay_duplicate_count
            ),
            "broker_execution_provenance_state_counts": dict(
                sorted(self.broker_execution_provenance_state_counts.items())
            ),
            "broker_execution_provenance_gap_count": (
                self.broker_execution_provenance_gap_count
            ),
            "broker_execution_provenance_gap_reasons": (
                self.broker_execution_provenance_gap_reasons
            ),
            "broker_execution_underlying_venue_unresolved_count": (
                self.broker_execution_underlying_venue_unresolved_count
            ),
            "broker_execution_entry_covered_qty": (
                self.broker_execution_entry_covered_qty
            ),
            "broker_execution_exit_covered_qty": (
                self.broker_execution_exit_covered_qty
            ),
            "broker_execution_partial_count": (self.broker_execution_partial_count),
            "broker_execution_full_count": self.broker_execution_full_count,
            "broker_execution_unreconciled_order_count": (
                unreconciled_broker_order_count
            ),
            "transition_replay_duplicate_count": (
                self.transition_replay_duplicate_count
            ),
            "scale_in_decisions": self.scale_in_decisions,
            "scale_in_contract_state": (
                "explicit" if self.scale_in_decisions else "missing"
            ),
            "market_observation_expected_count": (
                self.market_observation_expected_count
            ),
            "bbo_observed_count": self.bbo_observed_count,
            "depth_observed_count": self.depth_observed_count,
            "bbo_coverage_pct": bbo_coverage,
            "depth_coverage_pct": depth_coverage,
            "fees_taxes_krw": self.fees_taxes_krw,
            "slippage_krw": self.slippage_krw,
            "realized_net_pnl_krw": self.realized_net_pnl_krw,
            "observed_actual_broker_order_submitted": (
                self.observed_actual_broker_order_submitted
            ),
            "observed_real_order_evidence": self.observed_real_order_evidence,
            "lifecycle_population_scope": lifecycle_population_scope,
            "source_population_scopes": sorted(self.source_population_scopes),
            "sim_scope_real_order_contract_violation_count": (
                sim_scope_real_order_contract_violation_count
            ),
            "legacy_unattested_receive_clock_recovery_count": (
                self.legacy_unattested_receive_clock_recovery_count
            ),
            "historical_fill_before_submit_diagnostic_recovery_count": (
                self.historical_fill_before_submit_diagnostic_recovery_count
            ),
            "historical_fill_before_submit_diagnostic_recovery_provenance": (
                self.historical_fill_before_submit_diagnostic_recovery_provenance
            ),
            "historical_legacy_exit_submission_diagnostic_recovery_count": (
                self.historical_legacy_exit_submission_diagnostic_recovery_count
            ),
            "historical_legacy_exit_submission_diagnostic_recovery_provenance": (
                self.historical_legacy_exit_submission_diagnostic_recovery_provenance
            ),
            "post_final_stale_observation_quarantine_count": (
                self.post_final_stale_observation_quarantine_count
            ),
            "broker_late_arrival_stale_observation_quarantine_count": (
                self.broker_late_arrival_stale_observation_quarantine_count
            ),
            "reviewed_cost_profile_sha256": reviewed_cost_hash,
            "reviewed_cost_profile_verified": (
                self.cost_verified_seen and self.cost_verified_all
            ),
            "symbol_master_artifact_sha256": symbol_master_hash,
            "symbol_master_artifact_verified": (
                self.symbol_verified_seen and self.symbol_verified_all
            ),
            "invalid_transition_count": self.invalid_transition_count,
            "invalid_transition_reasons": self.invalid_reasons,
            "decision_trace_id_overflow_count": self.trace_ids_overflow_count,
            "row_source_quality_gate_pass": not blockers,
            "promotion_evidence_eligible": not blockers,
            "promotion_blockers": blockers,
            **REPORT_AUTHORITY_CONTRACT,
        }
        return row


def _bounded_gap(
    examples: list[dict[str, Any]], *, reason: str, source: str, line_number: int
) -> None:
    if len(examples) >= _GAP_EXAMPLE_LIMIT:
        return
    examples.append(
        {
            "reason": reason,
            "source": source,
            "line_number": line_number,
        }
    )


def _pipeline_owner_scoped_identity_gap(
    raw_row: Mapping[str, Any], *, target_date: str, reason: str | None
) -> tuple[str, str] | None:
    """Return the exact owner window for an isolatable pre-identity row.

    This deliberately does not reconstruct a lifecycle attempt.  A legacy
    mapped row can be quarantined only when the raw pipeline event itself
    carries an exact DB record id, six-digit stock code, and target date.  All
    attempts for that owner are excluded; unrelated owner windows remain
    eligible.  Every other validation failure stays a global source gap.
    """

    if reason != "pipeline_lifecycle_identity_missing":
        return None
    if str(raw_row.get("emitted_date") or "").strip() != target_date:
        return None
    record_id = str(raw_row.get("record_id") or "").strip()
    stock_code = str(raw_row.get("stock_code") or "").strip()
    if (
        not record_id
        or len(record_id) > 160
        or any(char in record_id for char in "\r\n\x00")
        or not re.fullmatch(r"[0-9]{6}", stock_code)
    ):
        return None
    return record_id, stock_code


def _pipeline_exact_lifecycle_gap_id(
    raw_row: Mapping[str, Any], *, target_date: str
) -> str | None:
    """Return a cryptographically exact lifecycle for a row-local data gap.

    This gate repeats the immutable lineage and source-only authority prefix
    checked by ``_validated_pipeline_transition``.  It deliberately excludes
    identity, mapping, trade-date, and authority failures: those remain owner
    scoped or global because their lifecycle cannot be trusted.
    """

    if raw_row.get("event_type") != "pipeline_event":
        return None
    pipeline = _pipeline_text(raw_row.get("pipeline")).upper()
    source_stage = _pipeline_text(raw_row.get("stage"))
    lifecycle_stage = PIPELINE_STAGE_MAP.get((pipeline, source_stage))
    fields = raw_row.get("fields")
    if lifecycle_stage is None or not isinstance(fields, Mapping):
        return None
    if any(
        (
            fields.get("main_lifecycle_identity_schema") != PIPELINE_IDENTITY_SCHEMA,
            fields.get("main_lifecycle_source_pipeline") != pipeline,
            fields.get("main_lifecycle_source_stage") != source_stage,
            fields.get("main_lifecycle_stage") != lifecycle_stage,
            fields.get("main_lifecycle_trade_date") != target_date,
            fields.get("main_lifecycle_decision_authority")
            != "source_only_lifecycle_observation",
            _pipeline_bool(fields.get("main_lifecycle_runtime_effect")) is not False,
            _pipeline_bool(fields.get("main_lifecycle_order_authority")) is not False,
            _pipeline_bool(fields.get("main_lifecycle_provider_authority"))
            is not False,
        )
    ):
        return None
    record_id = raw_row.get("record_id")
    stock_code = _pipeline_text(raw_row.get("stock_code"))
    attempt_id = _pipeline_text(fields.get("attempt_id"))
    if (
        not attempt_id
        or attempt_id != _pipeline_text(fields.get("main_lifecycle_attempt_id"))
        or str(record_id if record_id is not None else "").strip()
        != _pipeline_text(fields.get("main_lifecycle_record_id"))
        or stock_code != _pipeline_text(fields.get("main_lifecycle_stock_code"))
    ):
        return None
    lifecycle_id = _pipeline_text(fields.get("main_lifecycle_id"))
    if not validate_main_lifecycle_id(
        lifecycle_id,
        record_id=record_id,
        stock_code=stock_code,
        attempt_id=attempt_id,
    ):
        return None
    try:
        _aware_datetime(fields.get("main_lifecycle_observed_at"))
    except (TypeError, ValueError):
        return None
    return lifecycle_id


def _lifecycle_window_exclusion_taxonomies(
    reason_codes: Sequence[str],
) -> list[str]:
    """Classify row-local blockers without granting promotion authority."""

    taxonomies: set[str] = set()
    for reason in reason_codes:
        if reason in {
            "broker_order_no_cross_lifecycle_conflict",
            "broker_execution_identity_cross_lifecycle_conflict",
        }:
            taxonomies.add("cross_lifecycle_identity_conflict")
        elif reason == "sim_scope_real_order_contract_violation":
            taxonomies.add("source_authority_contract_violation")
        elif reason == "custody_carry_in_entry_lifecycle_non_promotable":
            taxonomies.add("custody_carry_in_nonpromotion")
        elif reason.startswith("broker_execution_") or reason in {
            "actual_broker_order_submission_required",
            "official_first_fill_to_final_exit_duration_required",
        }:
            taxonomies.add("broker_execution_provenance_or_custody_gap")
        elif reason.startswith(("bbo_", "depth_", "session_exposure_")):
            taxonomies.add("market_observation_coverage_gap")
        elif reason.startswith(("reviewed_cost_", "verified_symbol_")):
            taxonomies.add("economic_reference_gap")
        elif reason.startswith(
            (
                "realized_economics_",
                "fees_taxes_",
                "slippage_",
                "realized_net_pnl_",
            )
        ):
            taxonomies.add("realized_economics_gap")
        else:
            taxonomies.add("lifecycle_completeness_or_consistency_gap")
    return sorted(taxonomies)


def _reference_hash_contract(
    value: str | None,
    *,
    verified: bool,
    field: str,
) -> tuple[str | None, bool, list[str]]:
    blockers: list[str] = []
    if not isinstance(verified, bool):
        blockers.append(f"{field}_verified_flag_invalid")
        verified = False
    normalized = str(value or "").strip() or None
    if normalized is not None and not SHA256_RE.fullmatch(normalized):
        blockers.append(f"{field}_invalid")
        normalized = None
    if verified and normalized is None:
        blockers.append(f"{field}_missing_for_verified_contract")
        verified = False
    return normalized, verified, blockers


def _scan_fallback_source(
    path: Path | None,
) -> tuple[dict[str, Any] | None, int, list[dict[str, Any]]]:
    if path is None:
        return None, 0, []
    rows, census = _stream_json_objects(path)
    missing_id_count = 0
    explicit_id_nonjoined_count = 0
    gaps: list[dict[str, Any]] = []
    for line_number, row in rows:
        lifecycle_id = str(row.get("main_lifecycle_id") or "").strip()
        if lifecycle_id:
            explicit_id_nonjoined_count += 1
            continue
        missing_id_count += 1
        _bounded_gap(
            gaps,
            reason="raw_fallback_missing_explicit_main_lifecycle_id",
            source=census.source_path,
            line_number=line_number,
        )
    result = census.as_dict()
    result.update(
        {
            "missing_main_lifecycle_id_count": missing_id_count,
            "explicit_main_lifecycle_id_nonjoined_count": (explicit_id_nonjoined_count),
            "join_policy": "never_join_raw_fallback",
            "promotion_evidence_eligible": False,
        }
    )
    parse_gap_count = census.malformed_json_count + census.non_object_count
    read_gap_count = int(census.source_read_error is not None)
    if parse_gap_count:
        _bounded_gap(
            gaps,
            reason="raw_fallback_parse_gap",
            source=census.source_path,
            line_number=0,
        )
    if read_gap_count:
        _bounded_gap(
            gaps,
            reason="raw_fallback_read_error",
            source=census.source_path,
            line_number=0,
        )
    missing_source_count = int(not census.source_exists)
    if missing_source_count:
        _bounded_gap(
            gaps,
            reason="raw_fallback_source_missing",
            source=census.source_path,
            line_number=0,
        )
    return (
        result,
        missing_id_count + parse_gap_count + read_gap_count + missing_source_count,
        gaps,
    )


def _apply_cross_lifecycle_broker_ownership_gate(
    accumulators: Mapping[str, _LifecycleAccumulator],
) -> tuple[int, int]:
    """Fail closed when one broker identity is claimed by two lifecycles."""

    order_owners: dict[str, list[_LifecycleAccumulator]] = {}
    execution_owners: dict[str, list[_LifecycleAccumulator]] = {}
    for accumulator in accumulators.values():
        for order_no in accumulator.submitted_order_phase_by_no:
            order_owners.setdefault(order_no, []).append(accumulator)
        for identity in accumulator.broker_execution_content_by_identity:
            execution_owners.setdefault(identity, []).append(accumulator)

    conflicting_orders = {
        order_no: owners
        for order_no, owners in order_owners.items()
        if len({owner.main_lifecycle_id for owner in owners}) > 1
    }
    conflicting_executions = {
        identity: owners
        for identity, owners in execution_owners.items()
        if len({owner.main_lifecycle_id for owner in owners}) > 1
    }
    for owners in conflicting_orders.values():
        for owner in owners:
            owner.broker_order_no_cross_lifecycle_conflict_count += 1
            owner._invalid("broker_order_no_cross_lifecycle_conflict")
    for owners in conflicting_executions.values():
        for owner in owners:
            owner.broker_execution_cross_lifecycle_identity_conflict_count += 1
            owner._invalid("broker_execution_identity_cross_lifecycle_conflict")
    return len(conflicting_orders), len(conflicting_executions)


@dataclass(frozen=True)
class _HistoricalFillBeforeSubmitCandidate:
    """One strict archived BUY receipt still present in the reorder buffer."""

    buffered_sequence: int
    line_number: int
    transition: dict[str, Any]


@dataclass(frozen=True)
class _HistoricalLegacyExitSubmissionCandidate:
    """One withheld archived SELL submit lacking the later per-leg contract."""

    source_sequence: int
    line_number: int
    transition: dict[str, Any]


def _strict_historical_fill_before_submit_candidate(
    transition: Mapping[str, Any],
    *,
    source_mode: str | None,
    source_stage: str,
) -> bool:
    """Return true only for an identity-complete transformed type-00 BUY."""

    if (
        source_mode != "pipeline_events"
        or source_stage != "position_rebased_after_fill"
        or transition.get("stage") != "fill"
    ):
        return False
    data = transition.get("data")
    if not isinstance(data, Mapping):
        return False
    provenance_state = data.get("broker_execution_provenance_state")
    venue_provenance_valid = bool(
        (
            provenance_state == "complete"
            and data.get("broker_execution_actual_venue") == transition.get("venue")
            and data.get("broker_execution_actual_venue_complete") is True
            and data.get("broker_execution_venue_resolution_state")
            == "exact_underlying_venue"
        )
        or (
            provenance_state == "identity_complete_venue_unresolved"
            and data.get("broker_execution_actual_venue") is None
            and data.get("broker_execution_actual_venue_complete") is False
            and data.get("broker_execution_reported_venue_scope") == "SOR"
            and data.get("broker_execution_venue_resolution_state")
            == "integrated_sor_underlying_venue_unresolved"
        )
    )
    if (
        data.get("broker_execution_receipt_companion") is True
        or not venue_provenance_valid
        or data.get("broker_execution_identity_complete") is not True
        or data.get("broker_execution_raw_envelope_schema")
        != BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
        or data.get("broker_execution_source_type") != "00"
        or data.get("broker_execution_timing_schema") != BROKER_EXECUTION_TIMING_SCHEMA
        or data.get("broker_execution_ordering_time_source")
        != BROKER_EXECUTION_ORDERING_TIME_SOURCE
        or data.get("broker_execution_occurrence_time_source")
        != BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        or data.get("broker_execution_receive_time_source")
        != BROKER_EXECUTION_RECEIVE_TIME_SOURCE
        or data.get("broker_execution_official_reference_sha")
        != KIWOOM_OFFICIAL_REFERENCE_SHA
        or data.get("broker_execution_side") != "BUY"
        or data.get("broker_execution_stock_code") != transition.get("stock_code")
        or data.get("broker_execution_fill_state") not in {"partial", "full"}
        or not str(data.get("broker_execution_identity") or "").strip()
        or not SHA256_RE.fullmatch(
            str(data.get("broker_execution_content_sha256") or "").strip()
        )
    ):
        return False
    try:
        order_qty = int(data["broker_execution_order_qty"])
        cumulative_qty = int(data["broker_execution_cumulative_fill_qty"])
        remaining_qty = int(data["broker_execution_remaining_qty"])
        unit_qty = int(data["broker_execution_unit_fill_qty"])
        fill_qty = _finite_number(data.get("fill_qty"), positive=True)
        received_at = _aware_datetime(data["broker_execution_received_at"]).astimezone(
            KST
        )
        occurred_at = _aware_datetime(data["broker_execution_occurred_at"]).astimezone(
            KST
        )
        observed_at = _aware_datetime(transition["observed_at"]).astimezone(KST)
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        order_qty > 0
        and cumulative_qty > 0
        and remaining_qty >= 0
        and unit_qty > 0
        and cumulative_qty + remaining_qty == order_qty
        and unit_qty <= cumulative_qty
        and fill_qty is not None
        and fill_qty.is_integer()
        and int(fill_qty) == unit_qty
        and observed_at == received_at
        and occurred_at.microsecond == 0
        and re.fullmatch(
            r"[0-9]{6}", str(data.get("broker_execution_time_hhmmss") or "")
        )
        and occurred_at.strftime("%H%M%S")
        == str(data.get("broker_execution_time_hhmmss"))
    )


def _ordinary_exact_entry_submit_binding(
    receipt: Mapping[str, Any],
    submit: Mapping[str, Any],
    *,
    source_mode: str | None,
    source_stage: str,
) -> tuple[str, int, float] | None:
    """Bind a later ordinary submit to one exact buffered BUY receipt."""

    if (
        source_mode != "pipeline_events"
        or source_stage not in {"order_leg_sent", "order_bundle_submitted"}
        or submit.get("stage") != "submit"
        or any(
            receipt.get(field) != submit.get(field)
            for field in (
                "main_lifecycle_id",
                "record_id",
                "stock_code",
                "attempt_id",
                "trade_date",
            )
        )
    ):
        return None
    receipt_data = receipt.get("data")
    submit_data = submit.get("data")
    if not isinstance(receipt_data, Mapping) or not isinstance(submit_data, Mapping):
        return None
    if (
        submit_data.get("actual_broker_order_submitted") is not True
        or submit_data.get("submission_summary_only") is True
        or any(
            submit_data.get(field) is not None and submit_data.get(field) != ""
            for field in TRANSFORMED_SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES
        )
        or _LifecycleAccumulator._stage_context_identity(receipt, data=receipt_data)
        != _LifecycleAccumulator._stage_context_identity(submit, data=submit_data)
    ):
        return None
    order_no = str(receipt_data.get("broker_execution_order_no") or "").strip()
    receipt_population_scope = str(receipt_data.get("source_population_scope") or "")
    submit_population_scope = str(submit_data.get("source_population_scope") or "")
    raw_submit_orders = str(submit_data.get("broker_order_no_list") or "").split(",")
    submit_orders = [value.strip() for value in raw_submit_orders if value.strip()]
    requested_qty = _finite_number(submit_data.get("requested_qty"), positive=True)
    try:
        receipt_order_qty = int(receipt_data["broker_execution_order_qty"])
        receipt_received_at = _aware_datetime(
            receipt_data["broker_execution_received_at"]
        ).astimezone(KST)
        submit_observed_at = _aware_datetime(submit["observed_at"]).astimezone(KST)
        quantities = normalize_submitted_order_quantities(
            submit_data,
            submit_orders,
            int(requested_qty) if requested_qty is not None else 0,
        )
    except (KeyError, TypeError, ValueError):
        return None
    lag_sec = (submit_observed_at - receipt_received_at).total_seconds()
    if (
        not order_no
        or submit_population_scope not in {"", "real_record_bound"}
        or receipt_population_scope not in {"", submit_population_scope}
        or submit_orders != [order_no]
        or submit_data.get("broker_order_no") != order_no
        or requested_qty is None
        or not requested_qty.is_integer()
        or int(requested_qty) != receipt_order_qty
        or quantities != {order_no: receipt_order_qty}
        or lag_sec < 0.0
        or lag_sec > LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC
    ):
        return None
    return order_no, receipt_order_qty, lag_sec


def _historical_fill_before_submit_custody_predecessor(
    receipt: Mapping[str, Any],
    submit: Mapping[str, Any],
    *,
    source_stage: str,
    order_no: str,
    order_qty: int,
    lag_sec: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Mint a canonical in-memory predecessor without changing source bytes."""

    receipt_data = receipt["data"]
    submit_data = submit["data"]
    assert isinstance(receipt_data, Mapping)
    assert isinstance(submit_data, Mapping)
    receive_clock_attested = (
        receipt_data.get("legacy_unattested_receive_clock_recovered") is not True
    )
    receipt_received_at = _aware_datetime(
        receipt_data["broker_execution_received_at"]
    ).astimezone(KST)
    receipt_occurred_at = _aware_datetime(
        receipt_data["broker_execution_occurred_at"]
    ).astimezone(KST)
    submit_observed_at = _aware_datetime(submit["observed_at"]).astimezone(KST)
    context = _LifecycleAccumulator._stage_context_identity(receipt, data=receipt_data)
    provenance = {
        "schema": HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA,
        "main_lifecycle_id": receipt["main_lifecycle_id"],
        "broker_order_no": order_no,
        "broker_order_qty": order_qty,
        "broker_execution_no": receipt_data["broker_execution_no"],
        "broker_execution_identity": receipt_data["broker_execution_identity"],
        "broker_execution_content_sha256": receipt_data[
            "broker_execution_content_sha256"
        ],
        "receipt_event_id": receipt["event_id"],
        "receipt_transition_content_sha256": receipt["transition_content_sha256"],
        "receipt_received_at": receipt_received_at.isoformat(timespec="microseconds"),
        "receipt_occurred_at": receipt_occurred_at.isoformat(timespec="microseconds"),
        "receipt_receive_clock_attested": receive_clock_attested,
        "receipt_receive_time_source": (
            BROKER_EXECUTION_RECEIVE_TIME_SOURCE
            if receive_clock_attested
            else "legacy_unattested_receive_clock_diagnostic"
        ),
        "corroborating_submit_source_stage": source_stage,
        "corroborating_submit_event_id": submit["event_id"],
        "corroborating_submit_transition_content_sha256": submit[
            "transition_content_sha256"
        ],
        "corroborating_submit_observed_at": submit_observed_at.isoformat(
            timespec="microseconds"
        ),
        "corroboration_lag_ms": lag_sec * 1000.0,
        "venue": context[0],
        "session_bucket": context[1],
        "venue_source": context[2],
        "session_bucket_source": context[3],
        "in_memory_only": True,
        "raw_source_mutated": False,
        "promotion_evidence_eligible": False,
        "r2_r3_evidence_eligible": False,
        "runtime_effect": False,
        "order_authority": False,
    }
    synthetic_data: dict[str, Any] = {
        "actual_broker_order_submitted": True,
        "broker_order_no": order_no,
        "broker_order_no_list": order_no,
        "broker_order_qty_list": canonical_submitted_order_qty_list(
            {order_no: order_qty}
        ),
        "requested_qty": order_qty,
        "submission_time_source": provenance["receipt_receive_time_source"],
        "submission_ordering_clock": "broker_execution_received_at",
        "submission_causal_upper_bound_at": receipt_occurred_at.isoformat(
            timespec="microseconds"
        ),
        "submission_causal_upper_bound_source": (
            BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        ),
        "submission_custody_binding_schema": SUBMISSION_CUSTODY_BINDING_SCHEMA,
        "submission_custody_broker_order_no": order_no,
        "submission_custody_broker_execution_no": receipt_data["broker_execution_no"],
        "submission_custody_broker_order_qty": order_qty,
        "submission_custody_broker_cumulative_qty": receipt_data[
            "broker_execution_cumulative_fill_qty"
        ],
        "submission_custody_broker_remaining_qty": receipt_data[
            "broker_execution_remaining_qty"
        ],
        "submission_custody_broker_unit_qty": receipt_data[
            "broker_execution_unit_fill_qty"
        ],
        "venue_source": receipt_data.get("venue_source") or "transition.venue",
        "session_bucket_source": receipt_data.get("session_bucket_source")
        or "transition.session_bucket",
    }
    source_population_scope = str(receipt_data.get("source_population_scope") or "")
    if source_population_scope:
        synthetic_data["source_population_scope"] = source_population_scope
    return (
        build_transition(
            main_lifecycle_id=str(receipt["main_lifecycle_id"]),
            record_id=receipt["record_id"],
            stock_code=receipt["stock_code"],
            attempt_id=receipt["attempt_id"],
            trade_date=receipt["trade_date"],
            stage="submit",
            observed_at=receipt_received_at,
            venue=receipt["venue"],
            session_bucket=receipt["session_bucket"],
            data=synthetic_data,
        ),
        provenance,
    )


def _strict_historical_legacy_exit_submission_candidate(
    transition: Mapping[str, Any],
    *,
    source_mode: str | None,
    source_stage: str,
) -> bool:
    """Accept only one exact archived SELL submit with no attested contract."""

    if (
        source_mode != "pipeline_events"
        or source_stage != "sell_order_sent"
        or transition.get("stage") != "exit"
    ):
        return False
    data = transition.get("data")
    if not isinstance(data, Mapping):
        return False
    if (
        data.get("actual_broker_order_submitted") is not True
        or data.get("submission_contract_legacy_unattested") is not True
        or data.get("submission_leg_contract") is not None
        or data.get("submission_summary_only") is not None
        or any(
            data.get(field) is not None and data.get(field) != ""
            for field in TRANSFORMED_SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES
        )
        or str(data.get("source_population_scope") or "") != "real_record_bound"
    ):
        return False
    context = _LifecycleAccumulator._stage_context_identity(
        transition,
        data=data,
    )
    if context[0] == "UNKNOWN" or context[1] == "unknown":
        return False
    order_no = str(data.get("broker_order_no") or "").strip()
    order_numbers = [
        value.strip()
        for value in str(data.get("broker_order_no_list") or "").split(",")
        if value.strip()
    ]
    requested_qty = _finite_number(data.get("requested_qty"), positive=True)
    try:
        quantities = normalize_submitted_order_quantities(
            data,
            order_numbers,
            int(requested_qty) if requested_qty is not None else 0,
        )
    except ValueError:
        return False
    return bool(
        re.fullmatch(r"[0-9]{7}", order_no)
        and int(order_no) != 0
        and order_numbers == [order_no]
        and requested_qty is not None
        and requested_qty.is_integer()
        and quantities == {order_no: int(requested_qty)}
    )


def _strict_historical_legacy_exit_receipt_binding(
    submit: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    source_mode: str | None,
    source_stage: str,
) -> tuple[str, int, float] | None:
    """Prove a withheld legacy SELL submit from one later official receipt."""

    if (
        source_mode != "pipeline_events"
        or source_stage
        not in {
            "sell_partial_fill_progress",
            "nxt_rising_missed_tp1_partial_fill_progress",
            "nxt_rising_missed_tp1_partial_sell_completed",
            "sell_completed",
        }
        or receipt.get("stage") != "exit"
        or any(
            submit.get(field) != receipt.get(field)
            for field in (
                "main_lifecycle_id",
                "record_id",
                "stock_code",
                "attempt_id",
                "trade_date",
            )
        )
    ):
        return None
    submit_data = submit.get("data")
    receipt_data = receipt.get("data")
    if not isinstance(submit_data, Mapping) or not isinstance(receipt_data, Mapping):
        return None
    if (
        receipt_data.get("broker_execution_receipt_companion") is True
        or receipt_data.get("broker_execution_provenance_state")
        not in {"complete", "identity_complete_venue_unresolved"}
        or receipt_data.get("broker_execution_identity_complete") is not True
        or receipt_data.get("broker_execution_raw_envelope_schema")
        != BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
        or receipt_data.get("broker_execution_source_type") != "00"
        or receipt_data.get("broker_execution_timing_schema")
        != BROKER_EXECUTION_TIMING_SCHEMA
        or receipt_data.get("broker_execution_ordering_time_source")
        != BROKER_EXECUTION_ORDERING_TIME_SOURCE
        or receipt_data.get("broker_execution_occurrence_time_source")
        != BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        or receipt_data.get("broker_execution_receive_time_source")
        != BROKER_EXECUTION_RECEIVE_TIME_SOURCE
        or receipt_data.get("broker_execution_official_reference_sha")
        != KIWOOM_OFFICIAL_REFERENCE_SHA
        or receipt_data.get("broker_execution_side") != "SELL"
        or receipt_data.get("broker_execution_stock_code") != receipt.get("stock_code")
        or not str(receipt_data.get("broker_execution_identity") or "").strip()
        or not SHA256_RE.fullmatch(
            str(receipt_data.get("broker_execution_content_sha256") or "").strip()
        )
        or _LifecycleAccumulator._stage_context_identity(
            submit,
            data=submit_data,
        )
        != _LifecycleAccumulator._stage_context_identity(
            receipt,
            data=receipt_data,
        )
    ):
        return None
    order_no = str(submit_data.get("broker_order_no") or "").strip()
    requested_qty = _finite_number(submit_data.get("requested_qty"), positive=True)
    exit_qty = _finite_number(receipt_data.get("exit_qty"), positive=True)
    try:
        order_qty = int(receipt_data["broker_execution_order_qty"])
        cumulative_qty = int(receipt_data["broker_execution_cumulative_fill_qty"])
        remaining_qty = int(receipt_data["broker_execution_remaining_qty"])
        unit_qty = int(receipt_data["broker_execution_unit_fill_qty"])
        submitted_at = _aware_datetime(submit["observed_at"]).astimezone(KST)
        received_at = _aware_datetime(
            receipt_data["broker_execution_received_at"]
        ).astimezone(KST)
    except (KeyError, TypeError, ValueError):
        return None
    lag_sec = (received_at - submitted_at).total_seconds()
    if (
        requested_qty is None
        or not requested_qty.is_integer()
        or exit_qty is None
        or not exit_qty.is_integer()
        or receipt_data.get("broker_execution_order_no") != order_no
        or int(requested_qty) != order_qty
        or cumulative_qty <= 0
        or remaining_qty < 0
        or unit_qty <= 0
        or cumulative_qty + remaining_qty != order_qty
        or unit_qty > cumulative_qty
        or int(exit_qty) != unit_qty
        or lag_sec < 0.0
        or lag_sec > LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC
    ):
        return None
    return order_no, order_qty, lag_sec


def _historical_legacy_exit_submission_predecessor(
    submit: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    receipt_source_stage: str,
    order_no: str,
    order_qty: int,
    lag_sec: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materialize one receipt-corroborated legacy SELL submit in memory."""

    submit_data = submit["data"]
    receipt_data = receipt["data"]
    assert isinstance(submit_data, Mapping)
    assert isinstance(receipt_data, Mapping)
    context = _LifecycleAccumulator._stage_context_identity(
        submit,
        data=submit_data,
    )
    submitted_at = _aware_datetime(submit["observed_at"]).astimezone(KST)
    received_at = _aware_datetime(
        receipt_data["broker_execution_received_at"]
    ).astimezone(KST)
    receive_clock_attested = (
        receipt_data.get("legacy_unattested_receive_clock_recovered") is not True
    )
    provenance = {
        "schema": HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA,
        "main_lifecycle_id": submit["main_lifecycle_id"],
        "broker_order_no": order_no,
        "broker_order_qty": order_qty,
        "legacy_submit_event_id": submit["event_id"],
        "legacy_submit_transition_content_sha256": submit["transition_content_sha256"],
        "legacy_submit_observed_at": submitted_at.isoformat(timespec="microseconds"),
        "corroborating_receipt_source_stage": receipt_source_stage,
        "corroborating_receipt_event_id": receipt["event_id"],
        "corroborating_receipt_transition_content_sha256": receipt[
            "transition_content_sha256"
        ],
        "broker_execution_no": receipt_data["broker_execution_no"],
        "broker_execution_identity": receipt_data["broker_execution_identity"],
        "broker_execution_content_sha256": receipt_data[
            "broker_execution_content_sha256"
        ],
        "receipt_received_at": received_at.isoformat(timespec="microseconds"),
        "receipt_receive_clock_attested": receive_clock_attested,
        "receipt_receive_time_source": (
            BROKER_EXECUTION_RECEIVE_TIME_SOURCE
            if receive_clock_attested
            else "legacy_unattested_receive_clock_diagnostic"
        ),
        "corroboration_lag_ms": lag_sec * 1000.0,
        "venue": context[0],
        "session_bucket": context[1],
        "venue_source": context[2],
        "session_bucket_source": context[3],
        "in_memory_only": True,
        "raw_source_mutated": False,
        "promotion_evidence_eligible": False,
        "r2_r3_evidence_eligible": False,
        "runtime_effect": False,
        "order_authority": False,
    }
    synthetic_data = dict(submit_data)
    synthetic_data.update(
        {
            "submission_leg_contract": "exact_broker_single_order_leg_v1",
            "submission_leg_self_summarizing": True,
            "submission_contract_legacy_unattested": True,
        }
    )
    return (
        build_transition(
            main_lifecycle_id=str(submit["main_lifecycle_id"]),
            record_id=submit["record_id"],
            stock_code=submit["stock_code"],
            attempt_id=submit["attempt_id"],
            trade_date=submit["trade_date"],
            stage="exit",
            observed_at=submitted_at,
            venue=submit["venue"],
            session_bucket=submit["session_bucket"],
            data=synthetic_data,
        ),
        provenance,
    )


def build_daily_report(
    target_date: str | date,
    *,
    source_path: Path | None = None,
    raw_fallback_path: Path | None = None,
    output_path: Path | None = None,
    reviewed_cost_profile_sha256: str | None = None,
    reviewed_cost_profile_verified: bool = False,
    symbol_master_artifact_sha256: str | None = None,
    symbol_master_artifact_verified: bool = False,
    legacy_unattested_receive_clock_diagnostic: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Build one compact row per explicit lifecycle from one streaming scan."""

    target = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    target = date.fromisoformat(target).isoformat()
    if (
        legacy_unattested_receive_clock_diagnostic
        and date.fromisoformat(target)
        > LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE
    ):
        raise ValueError(
            "legacy_unattested_receive_clock_diagnostic_outside_archived_window"
        )
    logical_source = source_path or pipeline_event_path(target)
    streamed_rows, census = _stream_json_objects(logical_source)
    accumulators: dict[str, _LifecycleAccumulator] = {}
    source_invalid_transition_count = 0
    journal_transition_source_row_count = 0
    pipeline_event_source_row_count = 0
    pipeline_lifecycle_mapped_row_count = 0
    pipeline_lifecycle_accepted_row_count = 0
    pipeline_lifecycle_out_of_scope_row_count = 0
    pipeline_lifecycle_instrumentation_gap_count = 0
    pipeline_lifecycle_missing_identity_count = 0
    pipeline_lifecycle_owner_scoped_gap_count = 0
    pipeline_lifecycle_exact_scoped_gap_count = 0
    pipeline_lifecycle_unscoped_gap_count = 0
    pipeline_owner_scoped_gaps: dict[tuple[str, str], dict[str, int]] = {}
    pipeline_exact_lifecycle_gaps: dict[str, dict[str, int]] = {}
    mixed_source_row_count = 0
    lifecycle_accumulator_overflow_row_count = 0
    transition_event_identity_overflow_row_count = 0
    retained_transition_event_identity_count = 0
    selected_source_mode: str | None = None
    gap_examples: list[dict[str, Any]] = []
    reviewed_cost_hash, reviewed_cost_verified, cost_reference_blockers = (
        _reference_hash_contract(
            reviewed_cost_profile_sha256,
            verified=reviewed_cost_profile_verified,
            field="reviewed_cost_profile_sha256",
        )
    )
    symbol_master_hash, symbol_master_verified, symbol_reference_blockers = (
        _reference_hash_contract(
            symbol_master_artifact_sha256,
            verified=symbol_master_artifact_verified,
            field="symbol_master_artifact_sha256",
        )
    )
    reference_contract_blockers = [
        *cost_reference_blockers,
        *symbol_reference_blockers,
    ]

    # Preserve producer/source order for every ordinary transition.  Only a
    # strictly attested broker execution receipt may move ahead of an earlier
    # source row whose observation timestamp is later.  This repairs bounded
    # handler-dispatch lag without letting a backdated scanner/decision row
    # rewrite lifecycle causality.
    pending_transitions: deque[
        tuple[float, int, int, dict[str, Any], bool, dict[str, Any] | None]
    ] = deque()
    pending_transition_by_sequence: dict[
        int,
        tuple[float, int, int, dict[str, Any], bool, dict[str, Any] | None],
    ] = {}
    pending_broker_receipts: list[tuple[float, int]] = []
    pending_historical_fill_before_submit_by_lifecycle: dict[
        str, list[_HistoricalFillBeforeSubmitCandidate]
    ] = {}
    pending_historical_legacy_exit_submission_by_lifecycle: dict[
        str, list[_HistoricalLegacyExitSubmissionCandidate]
    ] = {}
    recovered_historical_fill_before_submit_order_keys: set[tuple[str, str]] = set()
    recovered_historical_legacy_exit_submission_order_keys: set[tuple[str, str]] = set()
    historical_fill_candidate_by_sequence: dict[
        int, tuple[str, _HistoricalFillBeforeSubmitCandidate]
    ] = {}
    seen_lifecycle_ids: set[str] = set()
    pending_or_withheld_transition_count = 0
    pending_or_withheld_transition_count_by_lifecycle: dict[str, int] = {}
    enqueue_overflow_reason_counts_by_lifecycle: dict[str, dict[str, int]] = {}
    transition_sequence = 0
    transition_reorder_buffer_peak_count = 0
    broker_late_arrival_reordered_count = 0
    broker_late_arrival_outside_window_count = 0
    max_transition_timestamp = float("-inf")

    def compact_pending_storage_if_needed() -> None:
        """Discard selected deque/heap tombstones before applying hard caps."""

        active_count = len(pending_transition_by_sequence)
        if (
            len(pending_transitions) >= MAX_TRANSITION_EVENT_IDENTITIES
            or len(pending_transitions) > (2 * active_count) + 1_024
        ):
            active_items = [
                item
                for item in pending_transitions
                if item[1] in pending_transition_by_sequence
            ]
            pending_transitions.clear()
            pending_transitions.extend(active_items)
        if (
            len(pending_broker_receipts) >= MAX_TRANSITION_EVENT_IDENTITIES
            or len(pending_broker_receipts) > (2 * active_count) + 1_024
        ):
            pending_broker_receipts[:] = [
                item
                for item in pending_broker_receipts
                if item[1] in pending_transition_by_sequence
            ]
            heapq.heapify(pending_broker_receipts)

    def reserve_pending_or_withheld_slot(
        transition: Mapping[str, Any],
        *,
        line_number: int,
    ) -> bool:
        """Bound every not-yet-consumed transition before retaining it."""

        nonlocal lifecycle_accumulator_overflow_row_count
        nonlocal transition_event_identity_overflow_row_count
        nonlocal pending_or_withheld_transition_count

        compact_pending_storage_if_needed()
        lifecycle_id = str(transition.get("main_lifecycle_id") or "")
        is_new_lifecycle = lifecycle_id not in seen_lifecycle_ids
        if is_new_lifecycle and len(seen_lifecycle_ids) >= MAX_LIFECYCLE_ACCUMULATORS:
            lifecycle_accumulator_overflow_row_count += 1
            _bounded_gap(
                gap_examples,
                reason="lifecycle_accumulator_limit_exceeded_at_enqueue",
                source=census.source_path,
                line_number=line_number,
            )
            return False
        accumulator = accumulators.get(lifecycle_id)
        retained_for_lifecycle = (
            len(accumulator.event_content_by_id) if accumulator is not None else 0
        )
        pending_for_lifecycle = pending_or_withheld_transition_count_by_lifecycle.get(
            lifecycle_id,
            0,
        )
        if (
            retained_for_lifecycle + pending_for_lifecycle
            >= _EVENT_ID_LIMIT_PER_LIFECYCLE
        ):
            transition_event_identity_overflow_row_count += 1
            reason = "lifecycle_transition_event_identity_limit_exceeded"
            reason_counts = enqueue_overflow_reason_counts_by_lifecycle.setdefault(
                lifecycle_id,
                {},
            )
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            _bounded_gap(
                gap_examples,
                reason="lifecycle_transition_event_identity_limit_exceeded_at_enqueue",
                source=census.source_path,
                line_number=line_number,
            )
            return False
        if (
            retained_transition_event_identity_count
            + pending_or_withheld_transition_count
            >= MAX_TRANSITION_EVENT_IDENTITIES
        ):
            transition_event_identity_overflow_row_count += 1
            reason = "global_transition_event_identity_limit_exceeded"
            reason_counts = enqueue_overflow_reason_counts_by_lifecycle.setdefault(
                lifecycle_id,
                {},
            )
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            _bounded_gap(
                gap_examples,
                reason="global_transition_event_identity_limit_exceeded_at_enqueue",
                source=census.source_path,
                line_number=line_number,
            )
            return False
        if is_new_lifecycle:
            seen_lifecycle_ids.add(lifecycle_id)
        pending_or_withheld_transition_count += 1
        pending_or_withheld_transition_count_by_lifecycle[lifecycle_id] = (
            pending_for_lifecycle + 1
        )
        return True

    def release_pending_or_withheld_slot(transition: Mapping[str, Any]) -> None:
        nonlocal pending_or_withheld_transition_count

        lifecycle_id = str(transition.get("main_lifecycle_id") or "")
        current = pending_or_withheld_transition_count_by_lifecycle.get(
            lifecycle_id,
            0,
        )
        if current <= 0 or pending_or_withheld_transition_count <= 0:
            raise RuntimeError("pending_transition_slot_census_underflow")
        pending_or_withheld_transition_count -= 1
        if current == 1:
            pending_or_withheld_transition_count_by_lifecycle.pop(
                lifecycle_id,
                None,
            )
        else:
            pending_or_withheld_transition_count_by_lifecycle[lifecycle_id] = (
                current - 1
            )

    def consume_transition(
        transition: dict[str, Any],
        line_number: int,
        source_sequence: int,
        *,
        trusted_historical_diagnostic_recovery: Mapping[str, Any] | None = None,
        trusted_broker_late_arrival_reordered: bool = False,
    ) -> None:
        nonlocal lifecycle_accumulator_overflow_row_count
        nonlocal transition_event_identity_overflow_row_count
        nonlocal retained_transition_event_identity_count

        lifecycle_id = str(transition["main_lifecycle_id"])
        accumulator = accumulators.get(lifecycle_id)
        if accumulator is None:
            if len(accumulators) >= MAX_LIFECYCLE_ACCUMULATORS:
                lifecycle_accumulator_overflow_row_count += 1
                _bounded_gap(
                    gap_examples,
                    reason="lifecycle_accumulator_limit_exceeded",
                    source=census.source_path,
                    line_number=line_number,
                )
                return
            accumulator = _LifecycleAccumulator.from_transition(transition)
            accumulator.bind_reference_contract(
                reviewed_cost_profile_sha256=reviewed_cost_hash,
                reviewed_cost_profile_verified=reviewed_cost_verified,
                symbol_master_artifact_sha256=symbol_master_hash,
                symbol_master_artifact_verified=symbol_master_verified,
            )
            accumulators[lifecycle_id] = accumulator
        event_id = str(transition.get("event_id") or "").strip()
        is_new_event_identity = event_id not in accumulator.event_content_by_id
        if (
            is_new_event_identity
            and retained_transition_event_identity_count
            >= MAX_TRANSITION_EVENT_IDENTITIES
        ):
            transition_event_identity_overflow_row_count += 1
            accumulator._invalid("global_transition_event_identity_limit_exceeded")
            _bounded_gap(
                gap_examples,
                reason="global_transition_event_identity_limit_exceeded",
                source=census.source_path,
                line_number=line_number,
            )
            return
        retained_before = len(accumulator.event_content_by_id)
        accumulator.consume(
            transition,
            source_sequence=source_sequence,
            trusted_historical_diagnostic_recovery=(
                trusted_historical_diagnostic_recovery
            ),
            trusted_broker_late_arrival_reordered=(
                trusted_broker_late_arrival_reordered
            ),
        )
        retained_transition_event_identity_count += max(
            0, len(accumulator.event_content_by_id) - retained_before
        )

    def insert_historical_fill_before_submit_predecessor(
        submit_transition: dict[str, Any],
        *,
        submit_source_mode: str | None,
        submit_source_stage: str,
    ) -> None:
        """Pair one later exact ordinary submit while its receipt is buffered."""

        nonlocal transition_sequence
        if not legacy_unattested_receive_clock_diagnostic:
            return
        lifecycle_id = str(submit_transition.get("main_lifecycle_id") or "")
        candidates = pending_historical_fill_before_submit_by_lifecycle.get(
            lifecycle_id, []
        )
        for candidate in candidates:
            if candidate.buffered_sequence not in pending_transition_by_sequence:
                continue
            binding = _ordinary_exact_entry_submit_binding(
                candidate.transition,
                submit_transition,
                source_mode=submit_source_mode,
                source_stage=submit_source_stage,
            )
            if binding is None:
                continue
            order_no, order_qty, lag_sec = binding
            order_key = (lifecycle_id, order_no)
            if order_key in recovered_historical_fill_before_submit_order_keys:
                continue
            synthetic, recovery_provenance = (
                _historical_fill_before_submit_custody_predecessor(
                    candidate.transition,
                    submit_transition,
                    source_stage=submit_source_stage,
                    order_no=order_no,
                    order_qty=order_qty,
                    lag_sec=lag_sec,
                )
            )
            if not reserve_pending_or_withheld_slot(
                synthetic,
                line_number=candidate.line_number,
            ):
                return
            transition_sequence += 1
            synthetic_buffered = (
                _aware_datetime(synthetic["observed_at"]).timestamp(),
                transition_sequence,
                candidate.line_number,
                synthetic,
                False,
                recovery_provenance,
            )
            insertion_index = next(
                (
                    index
                    for index, buffered in enumerate(pending_transitions)
                    if buffered[1] == candidate.buffered_sequence
                ),
                None,
            )
            if insertion_index is not None:
                pending_transitions.insert(insertion_index, synthetic_buffered)
                pending_transition_by_sequence[transition_sequence] = synthetic_buffered
                recovered_historical_fill_before_submit_order_keys.add(order_key)
                pending_historical_fill_before_submit_by_lifecycle[lifecycle_id] = [
                    item for item in candidates if item is not candidate
                ]
                historical_fill_candidate_by_sequence.pop(
                    candidate.buffered_sequence,
                    None,
                )
                return
            # The candidate was drained between the membership check and the
            # deque scan only if this implementation changes to concurrent
            # consumption.  Preserve fail-closed behavior in that case.
            release_pending_or_withheld_slot(synthetic)
            return

    def insert_historical_legacy_exit_submission_predecessor(
        receipt_transition: dict[str, Any],
        *,
        receipt_source_mode: str | None,
        receipt_source_stage: str,
    ) -> None:
        """Release one withheld legacy SELL submit after exact receipt proof."""

        if not legacy_unattested_receive_clock_diagnostic:
            return
        lifecycle_id = str(receipt_transition.get("main_lifecycle_id") or "")
        candidates = pending_historical_legacy_exit_submission_by_lifecycle.get(
            lifecycle_id,
            [],
        )
        matches: list[
            tuple[_HistoricalLegacyExitSubmissionCandidate, str, int, float]
        ] = []
        for candidate in candidates:
            binding = _strict_historical_legacy_exit_receipt_binding(
                candidate.transition,
                receipt_transition,
                source_mode=receipt_source_mode,
                source_stage=receipt_source_stage,
            )
            if binding is None:
                continue
            order_no, order_qty, lag_sec = binding
            if (
                lifecycle_id,
                order_no,
            ) in recovered_historical_legacy_exit_submission_order_keys:
                continue
            matches.append((candidate, order_no, order_qty, lag_sec))
        # More than one indistinguishable historical claim is not an exact
        # single-leg reconstruction.  Leave every candidate unmatched so the
        # exact lifecycle window fails closed below.
        if len(matches) != 1:
            return
        candidate, order_no, order_qty, lag_sec = matches[0]
        synthetic, recovery_provenance = _historical_legacy_exit_submission_predecessor(
            candidate.transition,
            receipt_transition,
            receipt_source_stage=receipt_source_stage,
            order_no=order_no,
            order_qty=order_qty,
            lag_sec=lag_sec,
        )
        synthetic_buffered = (
            _aware_datetime(synthetic["observed_at"]).timestamp(),
            candidate.source_sequence,
            candidate.line_number,
            synthetic,
            False,
            recovery_provenance,
        )
        insertion_index = next(
            (
                index
                for index, buffered in enumerate(pending_transitions)
                if buffered[1] > candidate.source_sequence
            ),
            len(pending_transitions),
        )
        pending_transitions.insert(insertion_index, synthetic_buffered)
        pending_transition_by_sequence[candidate.source_sequence] = synthetic_buffered
        recovered_historical_legacy_exit_submission_order_keys.add(
            (lifecycle_id, order_no)
        )
        pending_historical_legacy_exit_submission_by_lifecycle[lifecycle_id] = [
            item for item in candidates if item is not candidate
        ]

    def drain_transition_reorder_buffer(*, force: bool = False) -> None:
        nonlocal broker_late_arrival_reordered_count
        watermark = (
            float("inf")
            if force
            else max_transition_timestamp - LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC
        )
        while pending_transition_by_sequence:
            while (
                pending_transitions
                and pending_transitions[0][1] not in pending_transition_by_sequence
            ):
                pending_transitions.popleft()
            while (
                pending_broker_receipts
                and pending_broker_receipts[0][1] not in pending_transition_by_sequence
            ):
                heapq.heappop(pending_broker_receipts)
            if not pending_transitions:
                break

            source_item = pending_transitions[0]
            source_timestamp, source_sequence = source_item[:2]
            broker_item = None
            if pending_broker_receipts:
                broker_item = pending_transition_by_sequence[
                    pending_broker_receipts[0][1]
                ]

            selected = None
            reordered_receipt = False
            if broker_item is not None:
                broker_timestamp, broker_sequence = broker_item[:2]
                broker_transition = broker_item[3]
                broker_lifecycle_id = str(
                    broker_transition.get("main_lifecycle_id") or ""
                )
                reorder_path_is_stale_same_lifecycle_observations = True
                broker_found = False
                for buffered_item in pending_transitions:
                    buffered_sequence = buffered_item[1]
                    if buffered_sequence not in pending_transition_by_sequence:
                        continue
                    if buffered_sequence == broker_sequence:
                        broker_found = True
                        break
                    buffered_transition = buffered_item[3]
                    if (
                        str(buffered_transition.get("main_lifecycle_id") or "")
                        != broker_lifecycle_id
                    ):
                        # Independent symbols/lifecycles interleave naturally
                        # in the shared pipeline journal.  They are not a
                        # causal barrier between one lifecycle's stale
                        # observation and its delayed exact broker receipt.
                        continue
                    buffered_data = buffered_transition.get("data")
                    buffered_stage = str(buffered_transition.get("stage") or "")
                    if (
                        buffered_stage not in {"holding", "scale_in", "exit"}
                        or not isinstance(buffered_data, Mapping)
                        or buffered_data.get("actual_broker_order_submitted") is True
                        or str(
                            buffered_data.get("broker_execution_provenance_state") or ""
                        )
                        in {"complete", "identity_complete_venue_unresolved"}
                        or any(
                            field_name in buffered_data
                            for field_name in (
                                "fill_qty",
                                "exit_qty",
                                "terminal_no_fill",
                            )
                        )
                    ):
                        reorder_path_is_stale_same_lifecycle_observations = False
                        break
                if (
                    broker_sequence != source_sequence
                    and broker_timestamp < source_timestamp
                    and broker_timestamp <= watermark
                    and broker_found
                    and reorder_path_is_stale_same_lifecycle_observations
                ):
                    selected = broker_item
                    reordered_receipt = True
            if selected is None and source_timestamp <= watermark:
                selected = source_item
            if selected is None:
                break

            (
                _timestamp,
                selected_sequence,
                line_number,
                transition,
                _strict_broker_receipt,
                trusted_historical_recovery_provenance,
            ) = selected
            pending_transition_by_sequence.pop(selected_sequence, None)
            release_pending_or_withheld_slot(transition)
            stale_fill_candidate = historical_fill_candidate_by_sequence.pop(
                selected_sequence,
                None,
            )
            if stale_fill_candidate is not None:
                candidate_lifecycle_id, stale_candidate = stale_fill_candidate
                candidates = pending_historical_fill_before_submit_by_lifecycle.get(
                    candidate_lifecycle_id,
                    [],
                )
                pending_historical_fill_before_submit_by_lifecycle[
                    candidate_lifecycle_id
                ] = [
                    candidate
                    for candidate in candidates
                    if candidate is not stale_candidate
                ]
            if reordered_receipt:
                broker_late_arrival_reordered_count += 1
            consume_transition(
                transition,
                line_number,
                selected_sequence,
                trusted_historical_diagnostic_recovery=(
                    trusted_historical_recovery_provenance
                ),
                trusted_broker_late_arrival_reordered=reordered_receipt,
            )

    for line_number, raw_row in streamed_rows:
        if raw_row.get("schema") == JOURNAL_SCHEMA:
            journal_transition_source_row_count += 1
            row_source_mode = "transition_journal"
        elif raw_row.get("event_type") == "pipeline_event":
            pipeline_event_source_row_count += 1
            row_source_mode = "pipeline_events"
        else:
            row_source_mode = None

        if row_source_mode is not None:
            if selected_source_mode is None:
                selected_source_mode = row_source_mode
            elif selected_source_mode != row_source_mode:
                mixed_source_row_count += 1
                source_invalid_transition_count += 1
                _bounded_gap(
                    gap_examples,
                    reason="mixed_transition_source_kinds_forbidden",
                    source=census.source_path,
                    line_number=line_number,
                )
                continue

        if row_source_mode == "transition_journal":
            transition, reason = _validated_transition(raw_row, target_date=target)
        elif row_source_mode == "pipeline_events":
            transition, reason, lifecycle_in_scope = _validated_pipeline_transition(
                raw_row,
                target_date=target,
                legacy_unattested_receive_clock_diagnostic=(
                    legacy_unattested_receive_clock_diagnostic
                ),
            )
            if not lifecycle_in_scope:
                pipeline_lifecycle_out_of_scope_row_count += 1
                continue
            pipeline_lifecycle_mapped_row_count += 1
            if transition is not None:
                pipeline_lifecycle_accepted_row_count += 1
            else:
                pipeline_lifecycle_instrumentation_gap_count += 1
                if reason == "pipeline_lifecycle_identity_missing":
                    pipeline_lifecycle_missing_identity_count += 1
        else:
            transition, reason = _validated_transition(raw_row, target_date=target)
        if transition is None:
            exact_lifecycle_id = (
                _pipeline_exact_lifecycle_gap_id(raw_row, target_date=target)
                if row_source_mode == "pipeline_events"
                else None
            )
            scoped_owner = (
                _pipeline_owner_scoped_identity_gap(
                    raw_row,
                    target_date=target,
                    reason=reason,
                )
                if row_source_mode == "pipeline_events"
                else None
            )
            scope_limit_exceeded = False
            if (
                exact_lifecycle_id is not None
                and exact_lifecycle_id not in pipeline_exact_lifecycle_gaps
                and len(pipeline_exact_lifecycle_gaps) >= MAX_LIFECYCLE_ACCUMULATORS
            ):
                scope_limit_exceeded = True
            if (
                scoped_owner is not None
                and scoped_owner not in pipeline_owner_scoped_gaps
                and len(pipeline_owner_scoped_gaps) >= MAX_LIFECYCLE_ACCUMULATORS
            ):
                scope_limit_exceeded = True
            if exact_lifecycle_id is not None and not scope_limit_exceeded:
                pipeline_lifecycle_exact_scoped_gap_count += 1
                lifecycle_reasons = pipeline_exact_lifecycle_gaps.setdefault(
                    exact_lifecycle_id, {}
                )
                reason_key = reason or "transition_invalid"
                lifecycle_reasons[reason_key] = lifecycle_reasons.get(reason_key, 0) + 1
            elif scoped_owner is not None and not scope_limit_exceeded:
                pipeline_lifecycle_owner_scoped_gap_count += 1
                owner_reasons = pipeline_owner_scoped_gaps.setdefault(scoped_owner, {})
                reason_key = reason or "transition_invalid"
                owner_reasons[reason_key] = owner_reasons.get(reason_key, 0) + 1
            else:
                if scope_limit_exceeded:
                    reason = "pipeline_scoped_gap_identity_limit_exceeded"
                source_invalid_transition_count += 1
                if row_source_mode == "pipeline_events":
                    pipeline_lifecycle_unscoped_gap_count += 1
            _bounded_gap(
                gap_examples,
                reason=reason or "transition_invalid",
                source=census.source_path,
                line_number=line_number,
            )
            continue
        transition_timestamp = _aware_datetime(transition["observed_at"]).timestamp()
        data = transition.get("data")
        transition_stage = str(transition.get("stage") or "")
        source_stage = _pipeline_text(raw_row.get("stage"))
        if not reserve_pending_or_withheld_slot(
            transition,
            line_number=line_number,
        ):
            continue
        insert_historical_fill_before_submit_predecessor(
            transition,
            submit_source_mode=row_source_mode,
            submit_source_stage=source_stage,
        )
        insert_historical_legacy_exit_submission_predecessor(
            transition,
            receipt_source_mode=row_source_mode,
            receipt_source_stage=source_stage,
        )
        if (
            legacy_unattested_receive_clock_diagnostic
            and _strict_historical_legacy_exit_submission_candidate(
                transition,
                source_mode=row_source_mode,
                source_stage=source_stage,
            )
        ):
            # Reserve the original source position, but do not expose this
            # unattested submission to the lifecycle accumulator until one
            # unique later official SELL receipt corroborates it exactly.
            transition_sequence += 1
            max_transition_timestamp = max(
                max_transition_timestamp,
                transition_timestamp,
            )
            pending_historical_legacy_exit_submission_by_lifecycle.setdefault(
                str(transition["main_lifecycle_id"]),
                [],
            ).append(
                _HistoricalLegacyExitSubmissionCandidate(
                    source_sequence=transition_sequence,
                    line_number=line_number,
                    transition=transition,
                )
            )
            transition_reorder_buffer_peak_count = max(
                transition_reorder_buffer_peak_count,
                pending_or_withheld_transition_count,
            )
            drain_transition_reorder_buffer()
            continue
        execution_bearing = isinstance(data, Mapping) and (
            transition_stage == "fill"
            or (
                transition_stage == "scale_in"
                and data.get("scale_in_decision") == "ADD"
                and "fill_qty" in data
            )
            or (transition_stage == "exit" and "exit_qty" in data)
        )
        strict_broker_receipt = bool(
            execution_bearing
            and isinstance(data, Mapping)
            and data.get("broker_execution_receipt_companion") is not True
            and str(data.get("broker_execution_provenance_state") or "")
            in {"complete", "identity_complete_venue_unresolved"}
            and data.get("broker_execution_timing_schema")
            == BROKER_EXECUTION_TIMING_SCHEMA
            and str(data.get("broker_execution_identity") or "").strip()
            and SHA256_RE.fullmatch(
                str(data.get("broker_execution_content_sha256") or "").strip()
            )
            and transition_stage == "exit"
            and "exit_qty" in data
        )
        broker_receipt_reorder_eligible = bool(
            strict_broker_receipt
            and (
                transition_timestamp >= max_transition_timestamp
                or max_transition_timestamp - transition_timestamp
                <= LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC
            )
        )
        if (
            strict_broker_receipt
            and transition_timestamp < max_transition_timestamp
            and max_transition_timestamp - transition_timestamp
            > LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC
        ):
            late_by_sec = max_transition_timestamp - transition_timestamp
            assert late_by_sec > LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC
            broker_late_arrival_outside_window_count += 1
        transition_sequence += 1
        max_transition_timestamp = max(
            max_transition_timestamp,
            transition_timestamp,
        )
        buffered_transition = (
            transition_timestamp,
            transition_sequence,
            line_number,
            transition,
            broker_receipt_reorder_eligible,
            None,
        )
        pending_transitions.append(buffered_transition)
        pending_transition_by_sequence[transition_sequence] = buffered_transition
        if (
            legacy_unattested_receive_clock_diagnostic
            and _strict_historical_fill_before_submit_candidate(
                transition,
                source_mode=row_source_mode,
                source_stage=source_stage,
            )
        ):
            historical_fill_candidate = _HistoricalFillBeforeSubmitCandidate(
                buffered_sequence=transition_sequence,
                line_number=line_number,
                transition=transition,
            )
            pending_historical_fill_before_submit_by_lifecycle.setdefault(
                str(transition["main_lifecycle_id"]), []
            ).append(historical_fill_candidate)
            historical_fill_candidate_by_sequence[transition_sequence] = (
                str(transition["main_lifecycle_id"]),
                historical_fill_candidate,
            )
        if broker_receipt_reorder_eligible:
            heapq.heappush(
                pending_broker_receipts,
                (transition_timestamp, transition_sequence),
            )
        transition_reorder_buffer_peak_count = max(
            transition_reorder_buffer_peak_count,
            pending_or_withheld_transition_count,
        )
        drain_transition_reorder_buffer()

    drain_transition_reorder_buffer(force=True)

    for (
        lifecycle_id,
        candidates,
    ) in pending_historical_legacy_exit_submission_by_lifecycle.items():
        for candidate in candidates:
            release_pending_or_withheld_slot(candidate.transition)
            pipeline_lifecycle_instrumentation_gap_count += 1
            pipeline_lifecycle_exact_scoped_gap_count += 1
            reason = "historical_legacy_exit_submission_exact_receipt_missing"
            lifecycle_reasons = pipeline_exact_lifecycle_gaps.setdefault(
                lifecycle_id,
                {},
            )
            lifecycle_reasons[reason] = lifecycle_reasons.get(reason, 0) + 1
            _bounded_gap(
                gap_examples,
                reason=reason,
                source=census.source_path,
                line_number=candidate.line_number,
            )
        candidates.clear()

    for lifecycle_id, reason_counts in pipeline_exact_lifecycle_gaps.items():
        accumulator = accumulators.get(lifecycle_id)
        if accumulator is None:
            continue
        for reason, count in reason_counts.items():
            for _ in range(count):
                accumulator._invalid(f"pipeline_source_contract_gap:{reason}")

    for (
        lifecycle_id,
        reason_counts,
    ) in enqueue_overflow_reason_counts_by_lifecycle.items():
        accumulator = accumulators.get(lifecycle_id)
        if accumulator is None:
            continue
        for reason, count in reason_counts.items():
            for _ in range(count):
                accumulator._invalid(reason)

    (
        broker_order_no_cross_lifecycle_conflict_count,
        broker_execution_cross_lifecycle_identity_conflict_count,
    ) = _apply_cross_lifecycle_broker_ownership_gate(accumulators)
    if broker_order_no_cross_lifecycle_conflict_count:
        _bounded_gap(
            gap_examples,
            reason="broker_order_no_cross_lifecycle_conflict",
            source=census.source_path,
            line_number=0,
        )
    if broker_execution_cross_lifecycle_identity_conflict_count:
        _bounded_gap(
            gap_examples,
            reason="broker_execution_identity_cross_lifecycle_conflict",
            source=census.source_path,
            line_number=0,
        )

    fallback_census, fallback_gap_count, fallback_gaps = _scan_fallback_source(
        raw_fallback_path
    )
    if census.malformed_json_count or census.non_object_count:
        _bounded_gap(
            gap_examples,
            reason="transition_journal_parse_gap",
            source=census.source_path,
            line_number=0,
        )
    if census.source_read_error is not None:
        _bounded_gap(
            gap_examples,
            reason="transition_journal_read_error",
            source=census.source_path,
            line_number=0,
        )
    if not census.source_exists:
        _bounded_gap(
            gap_examples,
            reason="transition_journal_missing",
            source=census.source_path,
            line_number=0,
        )
    gap_examples.extend(fallback_gaps[: max(0, _GAP_EXAMPLE_LIMIT - len(gap_examples))])
    rows = [
        accumulators[lifecycle_id].finalize() for lifecycle_id in sorted(accumulators)
    ]
    pipeline_owner_excluded_lifecycle_count = 0
    for row in rows:
        owner = (str(row["record_id"]), str(row["stock_code"]))
        if owner not in pipeline_owner_scoped_gaps:
            continue
        pipeline_owner_excluded_lifecycle_count += 1
        blocker = "pipeline_owner_window_missing_explicit_lifecycle_identity"
        if blocker not in row["promotion_blockers"]:
            row["promotion_blockers"].append(blocker)
        row["row_source_quality_gate_pass"] = False
        row["promotion_evidence_eligible"] = False

    pipeline_owner_reason_counts: dict[str, int] = {}
    pipeline_owner_entries: list[dict[str, Any]] = []
    for (record_id, stock_code), reason_counts in sorted(
        pipeline_owner_scoped_gaps.items()
    ):
        for reason, count in reason_counts.items():
            pipeline_owner_reason_counts[reason] = (
                pipeline_owner_reason_counts.get(reason, 0) + count
            )
        owner_payload = {
            "target_date": target,
            "record_id": record_id,
            "stock_code": stock_code,
        }
        pipeline_owner_entries.append(
            {
                **owner_payload,
                "owner_key_sha256": _sha256(owner_payload),
                "gap_count": sum(reason_counts.values()),
                "reason_code_counts": dict(sorted(reason_counts.items())),
            }
        )
    pipeline_owner_exclusion_manifest = {
        "schema": PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA,
        **PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT,
        "target_date": target,
        "excluded_owner_count": len(pipeline_owner_entries),
        "excluded_lifecycle_count": pipeline_owner_excluded_lifecycle_count,
        "gap_count": pipeline_lifecycle_owner_scoped_gap_count,
        "reason_code_counts": dict(sorted(pipeline_owner_reason_counts.items())),
        "entries": pipeline_owner_entries,
    }
    lifecycle_window_exclusion_entries: list[dict[str, Any]] = []
    lifecycle_window_exclusion_reason_counts: dict[str, int] = {}
    lifecycle_window_exclusion_taxonomy_counts: dict[str, int] = {}
    locally_excluded_lifecycle_ids: set[str] = set()
    for row in rows:
        reason_codes = [
            str(reason)
            for reason in row.get("promotion_blockers", [])
            if str(reason).strip()
        ]
        if not reason_codes:
            row["lifecycle_window_source_quality_disposition"] = (
                "eligible_before_global_source_contract_gate"
            )
            row["lifecycle_window_exclusion_taxonomies"] = []
            continue
        taxonomies = _lifecycle_window_exclusion_taxonomies(reason_codes)
        row["lifecycle_window_source_quality_disposition"] = (
            "excluded_exact_lifecycle_window"
        )
        row["lifecycle_window_exclusion_taxonomies"] = taxonomies
        locally_excluded_lifecycle_ids.add(str(row["main_lifecycle_id"]))
        for reason in reason_codes:
            lifecycle_window_exclusion_reason_counts[reason] = (
                lifecycle_window_exclusion_reason_counts.get(reason, 0) + 1
            )
        for taxonomy in taxonomies:
            lifecycle_window_exclusion_taxonomy_counts[taxonomy] = (
                lifecycle_window_exclusion_taxonomy_counts.get(taxonomy, 0) + 1
            )
        lifecycle_window_exclusion_entries.append(
            {
                "main_lifecycle_id": row["main_lifecycle_id"],
                "exclusion_scope": "exact_main_lifecycle_window",
                "taxonomies": taxonomies,
                "reason_codes_sha256": _sha256(reason_codes),
            }
        )
    lifecycle_window_exclusion_manifest = {
        "schema": LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA,
        "metric_role": "source_quality_gate",
        "decision_authority": "exact_lifecycle_window_exclusion_only",
        "window_policy": "exact_trade_date_and_main_lifecycle_id",
        "sample_floor": "not_applicable_source_quality_manifest",
        "primary_decision_metric": "excluded_lifecycle_count",
        "source_quality_gate": "row_local_promotion_blocker_taxonomy",
        "evaluation_phase": "before_global_source_contract_gate",
        "exclusion_scope": "exact_main_lifecycle_window",
        "excluded_lifecycle_count": len(lifecycle_window_exclusion_entries),
        "eligible_lifecycle_count": (
            len(rows) - len(lifecycle_window_exclusion_entries)
        ),
        "taxonomy_counts": dict(
            sorted(lifecycle_window_exclusion_taxonomy_counts.items())
        ),
        "reason_code_counts": dict(
            sorted(lifecycle_window_exclusion_reason_counts.items())
        ),
        "entries": lifecycle_window_exclusion_entries,
        "runtime_effect": False,
        "runtime_authority": False,
        "order_authority": False,
        "provider_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "direct_runtime_or_order_apply",
            "provider_model_bot_threshold_price_quantity_or_cap_change",
            "exclude_other_clean_lifecycle_windows",
        ],
    }
    reference_binding_mode = (
        "postclose_explicit"
        if reviewed_cost_hash is not None or symbol_master_hash is not None
        else "missing"
    )
    if reviewed_cost_hash is None:
        observed_cost_hashes = {
            str(row["reviewed_cost_profile_sha256"])
            for row in rows
            if row["reviewed_cost_profile_sha256"] is not None
        }
        if len(observed_cost_hashes) == 1:
            reviewed_cost_hash = next(iter(observed_cost_hashes))
            reviewed_cost_verified = bool(rows) and all(
                row["reviewed_cost_profile_sha256"] == reviewed_cost_hash
                and row["reviewed_cost_profile_verified"] is True
                for row in rows
            )
            reference_binding_mode = "transition_consensus"
        elif len(observed_cost_hashes) > 1:
            reference_contract_blockers.append(
                "reviewed_cost_profile_hash_conflict_across_lifecycles"
            )
    if symbol_master_hash is None:
        observed_symbol_hashes = {
            str(row["symbol_master_artifact_sha256"])
            for row in rows
            if row["symbol_master_artifact_sha256"] is not None
        }
        if len(observed_symbol_hashes) == 1:
            symbol_master_hash = next(iter(observed_symbol_hashes))
            symbol_master_verified = bool(rows) and all(
                row["symbol_master_artifact_sha256"] == symbol_master_hash
                and row["symbol_master_artifact_verified"] is True
                for row in rows
            )
            if reference_binding_mode == "missing":
                reference_binding_mode = "transition_consensus"
        elif len(observed_symbol_hashes) > 1:
            reference_contract_blockers.append(
                "symbol_master_artifact_hash_conflict_across_lifecycles"
            )
    lifecycle_invalid_transition_count = sum(
        int(row["invalid_transition_count"]) for row in rows
    )
    broker_execution_provenance_gap_count = sum(
        int(row["broker_execution_provenance_gap_count"]) for row in rows
    )
    broker_execution_conflict_count = sum(
        int(row["broker_execution_conflict_count"]) for row in rows
    )
    broker_execution_receipt_companion_conflict_count = sum(
        int(row["broker_execution_receipt_companion_conflict_count"]) for row in rows
    )
    broker_execution_receipt_companion_replay_duplicate_count = sum(
        int(row["broker_execution_receipt_companion_replay_duplicate_count"])
        for row in rows
    )
    broker_execution_order_progress_conflict_count = sum(
        int(row["broker_execution_order_progress_conflict_count"]) for row in rows
    )
    broker_execution_submission_link_conflict_count = sum(
        int(row["broker_execution_submission_link_conflict_count"]) for row in rows
    )
    broker_execution_replay_duplicate_count = sum(
        int(row["broker_execution_replay_duplicate_count"]) for row in rows
    )
    broker_execution_unique_count = sum(
        int(row["broker_execution_unique_count"]) for row in rows
    )
    broker_execution_underlying_venue_unresolved_count = sum(
        int(row.get("broker_execution_underlying_venue_unresolved_count") or 0)
        for row in rows
    )
    legacy_unattested_receive_clock_recovery_count = sum(
        int(row["legacy_unattested_receive_clock_recovery_count"]) for row in rows
    )
    historical_fill_before_submit_diagnostic_recovery_count = sum(
        int(row["historical_fill_before_submit_diagnostic_recovery_count"])
        for row in rows
    )
    historical_legacy_exit_submission_diagnostic_recovery_count = sum(
        int(row["historical_legacy_exit_submission_diagnostic_recovery_count"])
        for row in rows
    )
    post_final_stale_observation_quarantine_count = sum(
        int(row["post_final_stale_observation_quarantine_count"]) for row in rows
    )
    broker_late_arrival_stale_observation_quarantine_count = sum(
        int(row["broker_late_arrival_stale_observation_quarantine_count"])
        for row in rows
    )
    broker_submission_custody_order_count = sum(
        int(row["broker_submission_custody_order_count"]) for row in rows
    )
    broker_submission_custody_pending_order_count = sum(
        int(row["broker_submission_custody_pending_order_count"]) for row in rows
    )
    sim_scope_real_order_contract_violation_count = sum(
        int(row["sim_scope_real_order_contract_violation_count"]) for row in rows
    )
    custody_carry_lifecycle_count = sum(
        int(row.get("carry_in_custody_schema") == CARRY_IN_CUSTODY_SCHEMA)
        for row in rows
    )
    custody_carry_final_exit_reconciled_count = sum(
        int(row["terminal_state"] == "CUSTODY_CARRY_FINAL_EXIT_RECONCILED")
        for row in rows
    )
    candidate_row_gate_failure_count = sum(
        1
        for row in rows
        if row["terminal_state"] == "FINAL_EXIT_RECONCILED"
        and row["promotion_evidence_eligible"] is not True
    )
    pipeline_owner_scoped_gap_high_volume = (
        pipeline_lifecycle_owner_scoped_gap_count
        >= PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
        and pipeline_lifecycle_owner_scoped_gap_count
        > pipeline_lifecycle_accepted_row_count
    )
    global_gate_blockers: list[str] = []
    if not census.source_exists:
        global_gate_blockers.append("transition_journal_missing")
    global_gate_blockers.extend(reference_contract_blockers)
    if census.malformed_json_count or census.non_object_count:
        global_gate_blockers.append("transition_journal_parse_gap")
    if census.source_read_error is not None:
        global_gate_blockers.append("transition_journal_read_error")
    if source_invalid_transition_count:
        global_gate_blockers.append("invalid_or_cross_attempt_transition_present")
    if mixed_source_row_count:
        global_gate_blockers.append("mixed_transition_source_kinds_forbidden")
    if lifecycle_accumulator_overflow_row_count:
        global_gate_blockers.append("lifecycle_accumulator_limit_exceeded")
    if transition_event_identity_overflow_row_count:
        global_gate_blockers.append("global_transition_event_identity_limit_exceeded")
    if pipeline_lifecycle_unscoped_gap_count:
        global_gate_blockers.append("pipeline_lifecycle_instrumentation_gap")
    if pipeline_owner_scoped_gap_high_volume:
        global_gate_blockers.append("pipeline_owner_scoped_gap_high_volume")
    # Row-local lifecycle, broker-provenance, execution-progress, and candidate
    # gate failures are already bound to an exact main_lifecycle_id in the
    # exclusion manifest above.  They must not quarantine unrelated clean
    # lifecycle windows.  Unbound source failures and cross-lifecycle identity
    # conflicts remain global below.
    if broker_order_no_cross_lifecycle_conflict_count:
        global_gate_blockers.append("broker_order_no_cross_lifecycle_conflict")
    if broker_execution_cross_lifecycle_identity_conflict_count:
        global_gate_blockers.append(
            "broker_execution_identity_cross_lifecycle_conflict"
        )
    if fallback_gap_count:
        global_gate_blockers.append("raw_fallback_instrumentation_gap")
    if raw_fallback_path is not None and not bool(
        (fallback_census or {}).get("source_exists")
    ):
        global_gate_blockers.append("raw_fallback_source_missing")
    if not rows:
        global_gate_blockers.append("no_explicit_lifecycle_rows")
    if legacy_unattested_receive_clock_diagnostic:
        global_gate_blockers.append(
            "legacy_unattested_receive_clock_diagnostic_non_promotable"
        )
    if (
        historical_fill_before_submit_diagnostic_recovery_count
        or historical_legacy_exit_submission_diagnostic_recovery_count
    ):
        global_gate_blockers.append(
            HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_NONPROMOTION_BLOCKER
        )
    if broker_late_arrival_outside_window_count:
        global_gate_blockers.append("broker_late_arrival_outside_reorder_window")
    if sim_scope_real_order_contract_violation_count:
        global_gate_blockers.append("sim_scope_real_order_contract_violation")

    if global_gate_blockers:
        for row in rows:
            if row["promotion_evidence_eligible"]:
                row["promotion_evidence_eligible"] = False
                row["promotion_blockers"] = [
                    *row["promotion_blockers"],
                    "daily_source_quality_gate_failed",
                ]

    for row in rows:
        if row["promotion_evidence_eligible"] is True:
            row["promotion_disposition"] = "eligible_source_only"
        elif str(row["main_lifecycle_id"]) in locally_excluded_lifecycle_ids:
            row["promotion_disposition"] = "excluded_exact_lifecycle_window"
        else:
            row["promotion_disposition"] = "global_source_contract_blocked"

    eligible_count = sum(
        1 for row in rows if row["promotion_evidence_eligible"] is True
    )
    terminal_state_counts: dict[str, int] = {}
    fill_completion_counts: dict[str, int] = {}
    population_scope_counts: dict[str, int] = {
        scope: 0 for scope in sorted(LIFECYCLE_POPULATION_SCOPES)
    }
    for row in rows:
        terminal = str(row["terminal_state"])
        terminal_state_counts[terminal] = terminal_state_counts.get(terminal, 0) + 1
        fill_class = str(row["fill_completion_class"])
        fill_completion_counts[fill_class] = (
            fill_completion_counts.get(fill_class, 0) + 1
        )
        population_scope = str(row["lifecycle_population_scope"])
        population_scope_counts[population_scope] = (
            population_scope_counts.get(population_scope, 0) + 1
        )

    source_census = census.as_dict()
    if pipeline_event_source_row_count and journal_transition_source_row_count:
        source_kind = "mixed_pipeline_and_transition_journal"
    elif pipeline_event_source_row_count:
        source_kind = "pipeline_events_explicit_id_only"
    elif journal_transition_source_row_count:
        source_kind = "transition_journal"
    else:
        source_kind = "unknown_or_empty"
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "target_date": target,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_transition_schema": JOURNAL_SCHEMA,
        "source_pipeline_identity_schema": PIPELINE_IDENTITY_SCHEMA,
        "broker_execution_provenance_schema": (BROKER_EXECUTION_PROVENANCE_SCHEMA),
        "broker_execution_raw_envelope_schema": (BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA),
        "broker_execution_timing_schema": BROKER_EXECUTION_TIMING_SCHEMA,
        "broker_execution_ordering_time_source": (
            BROKER_EXECUTION_ORDERING_TIME_SOURCE
        ),
        "broker_execution_occurrence_time_source": (
            BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        ),
        "broker_execution_receive_time_source": (BROKER_EXECUTION_RECEIVE_TIME_SOURCE),
        "legacy_unattested_receive_clock_diagnostic": (
            legacy_unattested_receive_clock_diagnostic
        ),
        "legacy_unattested_receive_clock_diagnostic_last_date": (
            LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE.isoformat()
        ),
        "legacy_unattested_receive_clock_recovery_count": (
            legacy_unattested_receive_clock_recovery_count
        ),
        "historical_fill_before_submit_diagnostic_recovery_count": (
            historical_fill_before_submit_diagnostic_recovery_count
        ),
        "historical_fill_before_submit_diagnostic_recovery_contract": {
            "schema": HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA,
            "enabled": legacy_unattested_receive_clock_diagnostic,
            "last_archived_date": (
                LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE.isoformat()
            ),
            "window_sec": LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC,
            "receipt_contract": (
                "strict_transformed_identity_complete_buy_type00_fid908"
            ),
            "corroboration_contract": (
                "later_same_lineage_ordinary_exact_single_order_full_qty_context"
            ),
            "custody_materialization": "in_memory_canonical_predecessor_only",
            "raw_source_mutated": False,
            "promotion_evidence_eligible": False,
            "r2_r3_evidence_eligible": False,
            "runtime_effect": False,
            "order_authority": False,
            "provider_authority": False,
            "forbidden_uses": [
                "r2_or_r3_candidate_input",
                "runtime_or_order_promotion",
                "raw_source_rewrite",
                "cross_lifecycle_symbol_or_time_join",
                "custody_or_submission_summary_spoof",
            ],
        },
        "historical_legacy_exit_submission_diagnostic_recovery_count": (
            historical_legacy_exit_submission_diagnostic_recovery_count
        ),
        "historical_legacy_exit_submission_diagnostic_recovery_contract": {
            "schema": (HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA),
            "enabled": legacy_unattested_receive_clock_diagnostic,
            "last_archived_date": (
                LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE.isoformat()
            ),
            "window_sec": LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC,
            "legacy_submit_contract": (
                "exact_lifecycle_single_broker_order_full_qty_no_summary_or_custody"
            ),
            "corroboration_contract": (
                "later_same_lineage_context_strict_sell_type00_fid908_exact_order_qty"
            ),
            "custody_materialization": "in_memory_canonical_predecessor_only",
            "raw_source_mutated": False,
            "promotion_evidence_eligible": False,
            "r2_r3_evidence_eligible": False,
            "runtime_effect": False,
            "order_authority": False,
            "provider_authority": False,
            "forbidden_uses": [
                "r2_or_r3_candidate_input",
                "runtime_or_order_promotion",
                "raw_source_rewrite",
                "cross_lifecycle_symbol_or_time_join",
                "multiple_order_leg_or_unmatched_receipt_reconstruction",
            ],
        },
        "broker_late_arrival_reordered_count": broker_late_arrival_reordered_count,
        "broker_late_arrival_outside_window_count": (
            broker_late_arrival_outside_window_count
        ),
        "post_final_stale_observation_quarantine_count": (
            post_final_stale_observation_quarantine_count
        ),
        "broker_late_arrival_stale_observation_quarantine_count": (
            broker_late_arrival_stale_observation_quarantine_count
        ),
        "late_arrival_reorder_contract": {
            "metric_role": "source_quality_timestamp_order_repair",
            "decision_authority": "source_only_materialization_ordering",
            "window_policy": (
                "bounded_strict_broker_receipt_reorder_with_ordinary_source_order"
            ),
            "window_sec": LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC,
            "sample_floor": "one_exact_timezone_aware_lifecycle_transition",
            "primary_decision_metric": "broker_late_arrival_outside_window_count",
            "source_quality_gate": (
                "canonical_transition_exact_broker_receipt_and_source_sequence"
            ),
            "forbidden_uses": [
                "runtime_or_order_timing_change",
                "broker_receipt_timestamp_synthesis",
                "provider_threshold_price_quantity_or_cap_change",
            ],
        },
        "broker_submission_custody_order_count": (
            broker_submission_custody_order_count
        ),
        "broker_submission_custody_pending_order_count": (
            broker_submission_custody_pending_order_count
        ),
        "sim_scope_real_order_contract_violation_count": (
            sim_scope_real_order_contract_violation_count
        ),
        "custody_carry_schema": CARRY_IN_CUSTODY_SCHEMA,
        "custody_carry_lifecycle_count": custody_carry_lifecycle_count,
        "custody_carry_final_exit_reconciled_count": (
            custody_carry_final_exit_reconciled_count
        ),
        "broker_execution_official_reference_sha": (KIWOOM_OFFICIAL_REFERENCE_SHA),
        "source_kind": source_kind,
        "source_path": census.source_path,
        "source_raw_sha256": census.source_raw_sha256,
        "source_content_sha256": census.source_decoded_sha256,
        "source_raw_census": source_census,
        "source_census_content_sha256": _sha256(source_census),
        "raw_fallback_census": fallback_census,
        "reviewed_cost_profile_sha256": reviewed_cost_hash,
        "reviewed_cost_profile_verified": reviewed_cost_verified,
        "symbol_master_artifact_sha256": symbol_master_hash,
        "symbol_master_artifact_verified": symbol_master_verified,
        "reference_contract_blockers": reference_contract_blockers,
        "reference_binding_mode": reference_binding_mode,
        "instrumentation_gap_count": (
            source_invalid_transition_count
            + census.malformed_json_count
            + census.non_object_count
            + int(census.source_read_error is not None)
            + fallback_gap_count
            + candidate_row_gate_failure_count
            + broker_execution_provenance_gap_count
            + broker_execution_conflict_count
            + broker_execution_receipt_companion_conflict_count
            + broker_execution_order_progress_conflict_count
            + broker_execution_submission_link_conflict_count
            + broker_order_no_cross_lifecycle_conflict_count
            + broker_execution_cross_lifecycle_identity_conflict_count
            + lifecycle_accumulator_overflow_row_count
            + transition_event_identity_overflow_row_count
            + pipeline_lifecycle_owner_scoped_gap_count
            + pipeline_lifecycle_exact_scoped_gap_count
            + broker_late_arrival_outside_window_count
            + sim_scope_real_order_contract_violation_count
            + int(not census.source_exists)
            + int(not rows)
        ),
        "instrumentation_gap_examples": gap_examples,
        "source_invalid_transition_count": source_invalid_transition_count,
        "journal_transition_source_row_count": journal_transition_source_row_count,
        "pipeline_event_source_row_count": pipeline_event_source_row_count,
        "pipeline_lifecycle_mapped_row_count": (pipeline_lifecycle_mapped_row_count),
        "pipeline_lifecycle_accepted_row_count": (
            pipeline_lifecycle_accepted_row_count
        ),
        "pipeline_lifecycle_out_of_scope_row_count": (
            pipeline_lifecycle_out_of_scope_row_count
        ),
        "pipeline_lifecycle_instrumentation_gap_count": (
            pipeline_lifecycle_instrumentation_gap_count
        ),
        "pipeline_lifecycle_missing_identity_count": (
            pipeline_lifecycle_missing_identity_count
        ),
        "pipeline_lifecycle_owner_scoped_gap_count": (
            pipeline_lifecycle_owner_scoped_gap_count
        ),
        "pipeline_lifecycle_exact_scoped_gap_count": (
            pipeline_lifecycle_exact_scoped_gap_count
        ),
        "pipeline_lifecycle_unscoped_gap_count": (
            pipeline_lifecycle_unscoped_gap_count
        ),
        "pipeline_owner_exclusion_manifest": pipeline_owner_exclusion_manifest,
        "pipeline_owner_scoped_gap_high_volume_min_rows": (
            PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
        ),
        "pipeline_owner_scoped_gap_high_volume_blocked": (
            pipeline_owner_scoped_gap_high_volume
        ),
        "mixed_source_row_count": mixed_source_row_count,
        "lifecycle_accumulator_overflow_row_count": (
            lifecycle_accumulator_overflow_row_count
        ),
        "transition_event_identity_overflow_row_count": (
            transition_event_identity_overflow_row_count
        ),
        "lifecycle_invalid_transition_count": lifecycle_invalid_transition_count,
        "broker_execution_provenance_gap_count": (
            broker_execution_provenance_gap_count
        ),
        "broker_execution_conflict_count": broker_execution_conflict_count,
        "broker_execution_receipt_companion_conflict_count": (
            broker_execution_receipt_companion_conflict_count
        ),
        "broker_execution_receipt_companion_replay_duplicate_count": (
            broker_execution_receipt_companion_replay_duplicate_count
        ),
        "broker_execution_order_progress_conflict_count": (
            broker_execution_order_progress_conflict_count
        ),
        "broker_execution_submission_link_conflict_count": (
            broker_execution_submission_link_conflict_count
        ),
        "broker_order_no_cross_lifecycle_conflict_count": (
            broker_order_no_cross_lifecycle_conflict_count
        ),
        "broker_execution_cross_lifecycle_identity_conflict_count": (
            broker_execution_cross_lifecycle_identity_conflict_count
        ),
        "broker_execution_replay_duplicate_count": (
            broker_execution_replay_duplicate_count
        ),
        "broker_execution_unique_count": broker_execution_unique_count,
        "broker_execution_underlying_venue_unresolved_count": (
            broker_execution_underlying_venue_unresolved_count
        ),
        "candidate_row_gate_failure_count": candidate_row_gate_failure_count,
        "lifecycle_window_exclusion_manifest": (lifecycle_window_exclusion_manifest),
        "lifecycle_count": len(rows),
        "lifecycle_population_scope_counts": dict(
            sorted(population_scope_counts.items())
        ),
        "real_submitted_lifecycle_count": population_scope_counts[
            LIFECYCLE_POPULATION_REAL_SUBMITTED
        ],
        "candidate_observation_lifecycle_count": population_scope_counts[
            LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION
        ],
        "lifecycle_population_partition_complete": (
            sum(population_scope_counts.values()) == len(rows)
        ),
        "promotion_ready_population_scope": (
            f"{LIFECYCLE_POPULATION_REAL_SUBMITTED}_only"
        ),
        "terminal_state_counts": dict(sorted(terminal_state_counts.items())),
        "fill_completion_class_counts": dict(sorted(fill_completion_counts.items())),
        "promotion_evidence_eligible_count": eligible_count,
        "promotion_ready": eligible_count > 0 and not global_gate_blockers,
        "promotion_ready_lifecycle_ids": [
            str(row["main_lifecycle_id"])
            for row in rows
            if row["promotion_evidence_eligible"] is True
        ],
        "global_source_quality_gate_pass": not global_gate_blockers,
        "global_source_quality_gate_blockers": global_gate_blockers,
        "rows": rows,
        "streaming_memory_contract": {
            "source_scan_count": 1,
            "source_rows_retained": 0,
            "transition_buffers_retained": (pending_or_withheld_transition_count),
            "bounded_reorder_window_sec": (LIFECYCLE_LATE_ARRIVAL_REORDER_WINDOW_SEC),
            "transition_reorder_buffer_peak_count": (
                transition_reorder_buffer_peak_count
            ),
            "transition_reorder_buffer_capacity": (MAX_TRANSITION_EVENT_IDENTITIES),
            "withheld_candidates_share_transition_identity_caps": True,
            "seen_lifecycle_count": len(seen_lifecycle_ids),
            "accumulator_count": len(accumulators),
            "accumulator_limit": MAX_LIFECYCLE_ACCUMULATORS,
            "materialized_report_row_count": len(rows),
            "retained_transition_event_identity_count": (
                retained_transition_event_identity_count
            ),
            "global_transition_event_identity_limit": (MAX_TRANSITION_EVENT_IDENTITIES),
            "decision_trace_ids_per_lifecycle_limit": _TRACE_ID_LIMIT,
            "event_ids_per_lifecycle_limit": _EVENT_ID_LIMIT_PER_LIFECYCLE,
            "instrumentation_gap_example_limit": _GAP_EXAMPLE_LIMIT,
        },
        **REPORT_AUTHORITY_CONTRACT,
    }
    digest = _sha256(report)
    report["content_sha256"] = digest
    report["report_content_sha256"] = digest
    report["artifact_content_sha256"] = _sha256(report)
    if write:
        _atomic_write_json(output_path or paired_report_path(target), report)
    return report


def build_main_lifecycle_paired_report(
    target_date: str | date,
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility name for postclose orchestration."""

    return build_daily_report(target_date, **kwargs)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, dest="target_date")
    parser.add_argument(
        "--journal", "--source", "--pipeline", dest="journal", type=Path
    )
    parser.add_argument("--raw-fallback", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reviewed-cost-profile-sha256")
    parser.add_argument("--reviewed-cost-profile-verified", action="store_true")
    parser.add_argument("--symbol-master-artifact-sha256")
    parser.add_argument("--symbol-master-artifact-verified", action="store_true")
    parser.add_argument(
        "--legacy-unattested-receive-clock-diagnostic",
        action="store_true",
        help=(
            "Archived <=2026-08-25 diagnostic only; recovered rows are "
            "permanently non-promotable"
        ),
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_daily_report(
        args.target_date,
        source_path=args.journal,
        raw_fallback_path=args.raw_fallback,
        output_path=args.output,
        reviewed_cost_profile_sha256=args.reviewed_cost_profile_sha256,
        reviewed_cost_profile_verified=args.reviewed_cost_profile_verified,
        symbol_master_artifact_sha256=args.symbol_master_artifact_sha256,
        symbol_master_artifact_verified=args.symbol_master_artifact_verified,
        legacy_unattested_receive_clock_diagnostic=(
            args.legacy_unattested_receive_clock_diagnostic
        ),
        write=args.write,
    )
    stdout_payload: Mapping[str, Any]
    if args.write:
        stdout_payload = {
            "schema": "main_scalping_lifecycle_paired_cli_result_v1",
            "target_date": args.target_date,
            "output_path": str(args.output or paired_report_path(args.target_date)),
            "artifact_content_sha256": report["artifact_content_sha256"],
            "lifecycle_count": report["lifecycle_count"],
            "promotion_ready": report["promotion_ready"],
            "legacy_unattested_receive_clock_diagnostic": report[
                "legacy_unattested_receive_clock_diagnostic"
            ],
            "runtime_authority": False,
            "order_authority": False,
            "provider_authority": False,
        }
    else:
        stdout_payload = report
    print(json.dumps(stdout_payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT",
    "PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA",
    "REPORT_AUTHORITY_CONTRACT",
    "REPORT_SCHEMA",
    "build_daily_report",
    "build_main_lifecycle_paired_report",
    "main",
    "paired_report_path",
    "pipeline_event_path",
    "report_path",
]
