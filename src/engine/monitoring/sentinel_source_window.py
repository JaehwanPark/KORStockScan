"""Forward-only source-health projection owned by the existing sentinel cache.

The optional compact database retains a time-indexed subset for the observer.
It never backfills historical gaps or replaces the raw stream as authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import stat
import types
import zlib
from contextlib import closing
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
STAGES = frozenset(
    (
        "zero_base_probe_result",
        "main_fixed_watch_observation_wait",
        "entry_async_disposition",
    )
)
LIMIT = 32 * 1024 * 1024

# This is the physical issuer of the selected predecessor's source-window
# generation. Its exact original bytes are retained in content-addressed
# custody; do not rewrite the issued contract as the successor's code hash.
_PREDECESSOR_ISSUERS = frozenset({
    "012d290ace2bd5e6cd16a4e0f8564f8082e03dc55851959a67a0418f010c5737",
})


def _predecessor_issuer(data_root, contract):
    """Load the exact issued writer, never a caller-provided code location."""
    if contract not in _PREDECESSOR_ISSUERS:
        raise ValueError("source_window_predecessor_migration_required")
    path = Path(data_root) / "runtime/sentinel_event_cache/issuers" / (contract + ".py")
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("source_window_predecessor_issuer_invalid")
    def identity(value):
        # Reading legitimately advances atime; the producer identity binds
        # the physical object and content-relevant metadata instead.
        return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
                value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        with os.fdopen(fd, "rb") as source:
            before = os.fstat(source.fileno())
            if (not stat.S_ISREG(before.st_mode) or before.st_size > 1024 * 1024
                or before.st_nlink != 1 or before.st_mode & 0o222):
                raise ValueError("source_window_predecessor_issuer_invalid")
            raw = source.read(1024 * 1024 + 1)
            after = os.fstat(source.fileno())
        if (identity(before) != identity(after) or identity(path.stat()) != identity(before)
            or hashlib.sha256(raw).hexdigest() != contract):
            raise ValueError("source_window_predecessor_issuer_invalid")
    except OSError as exc:
        raise ValueError("source_window_predecessor_issuer_invalid") from exc
    issuer = types.ModuleType("_sentinel_source_window_issued_" + contract)
    issuer.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), vars(issuer))
    if issuer._contract() != contract or identity(path.stat()) != identity(before):
        raise ValueError("source_window_predecessor_issuer_invalid")
    return issuer


def _epoch(value):
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.timestamp()


def _contract():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _object(encoded):
    value = json.loads(encoded)
    if not isinstance(value, dict):
        raise ValueError("source_window_json_object_required")
    return value


def _metadata(path):
    with path.open("rb") as stream:
        encoded = stream.read(1024 * 1024 + 1)
    if len(encoded) > 1024 * 1024:
        raise ValueError("source_window_metadata_oversized")
    return _object(encoded)


def _chain(previous, offset, epoch, sha):
    identity = json.dumps([offset, epoch, sha], separators=(",", ":"), allow_nan=False)
    return hashlib.sha256((previous + identity).encode()).hexdigest(), len(identity)


def maintain(cache_path, previous_generation, meta, *, previous_state=None, now=None):
    """Append only verified new cache bytes while holding its existing lock.

    A missing/stale index starts at the current cache cursor. Starting fresh
    means waiting for a complete future window, never scanning old raw bytes.
    """
    from src.engine.monitoring.sentinel_compact_store import stamp

    cache_path = Path(cache_path)
    generation = stamp(cache_path)
    at = float(now if now is not None else datetime.now(KST).timestamp())
    contract = _contract()
    with sqlite3.connect(cache_path.with_suffix(".compact.sqlite"), timeout=5) as conn:
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS source_window_rows "
            "(offset INTEGER PRIMARY KEY, emitted_epoch REAL NOT NULL, body BLOB NOT NULL, sha TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS source_window_time ON source_window_rows(emitted_epoch, offset)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS source_window_state "
            "(id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)"
        )
        saved = conn.execute(
            "SELECT body FROM source_window_state WHERE id=1"
        ).fetchone()
        try:
            state = _object(saved[0]) if saved else {}
        except (ValueError, TypeError):
            state = {}
        anchored = isinstance(previous_state, dict) and state == previous_state
        unchanged = (
            anchored
            and state.get("contract") == contract
            and state.get("generation") == generation
        )
        append = (
            anchored
            and state.get("contract") == contract
            and previous_generation is not None
            and state.get("generation") == previous_generation
            and state.get("offset") == previous_generation[2]
            and generation[:2] == previous_generation[:2]
            and 0 <= generation[2] - previous_generation[2] <= LIMIT
        )
        if unchanged:
            # Metadata may have advanced through irrelevant raw events only.
            state = dict(state)
        elif not append:
            conn.execute("DELETE FROM source_window_rows")
            state = dict(
                contract=contract,
                coverage_started_epoch=at,
                historical_stage_coverage="not_backfilled_before_cache_offset",
                initial_cache_offset=generation[2],
                invalid_rows=0,
                population_sha256=hashlib.sha256(b"").hexdigest(),
                population_bytes=0,
            )
        else:
            with cache_path.open("rb") as source:
                source.seek(previous_generation[2])
                while source.tell() < generation[2]:
                    encoded = source.readline(LIMIT + 1)
                    if not encoded.endswith(b"\n") or source.tell() > generation[2]:
                        raise ValueError("source_window_cache_partial_line")
                    try:
                        row = _object(encoded)
                        if (
                            row.get("pipeline") != "ENTRY_PIPELINE"
                            or row.get("stage") not in STAGES
                        ):
                            continue
                        epoch = _epoch(row.get("emitted_at"))
                    except (ValueError, TypeError, AttributeError, OverflowError):
                        state["invalid_rows"] += 1
                        continue
                    body = json.dumps(
                        row, separators=(",", ":"), ensure_ascii=False
                    ).encode()
                    sha = hashlib.sha256(body).hexdigest()
                    conn.execute(
                        "INSERT INTO source_window_rows VALUES (?, ?, ?, ?)",
                        (source.tell(), epoch, zlib.compress(body, 1), sha),
                    )
                    state["population_sha256"], size = _chain(
                        state["population_sha256"], source.tell(), epoch, sha
                    )
                    state["population_bytes"] += size
        # decode_errors is per append, not cumulative. Do not import errors
        # before this new projection's activation, or count a metadata retry twice.
        new_errors = (
            int(meta.get("decode_errors") or 0)
            if (unchanged or append)
            and meta["raw_offset"] > state.get("raw_offset", meta["raw_offset"])
            else 0
        )
        state.update(
            generation=generation,
            offset=generation[2],
            raw_offset=meta["raw_offset"],
            raw_generation=meta["raw_generation"],
            schema_version=meta["schema_version"],
            invalid_rows=state["invalid_rows"] + new_errors,
        )
        state["row_count"] = conn.execute(
            "SELECT count(*) FROM source_window_rows"
        ).fetchone()[0]
        if stamp(cache_path) != generation:
            raise ValueError("source_window_cache_generation_changed")
        conn.execute(
            "INSERT OR REPLACE INTO source_window_state VALUES (1, ?)",
            (json.dumps(state, sort_keys=True),),
        )
    return state


def read(data_root, now, *, lower_epoch, limit=LIMIT):
    """Read an exact indexed window plus one bounded raw append suffix.

    Caller may fall back to the old bounded raw reader on any exception. A
    partial index is never offered as a complete or zero-event population.
    """
    import fcntl
    from contextlib import ExitStack
    from src.engine.monitoring.sentinel_compact_store import stamp

    data_root = Path(data_root).resolve()
    if (
        type(lower_epoch) not in (int, float)
        or not math.isfinite(lower_epoch)
        or not 0 < lower_epoch <= now.timestamp()
    ):
        raise ValueError("source_window_clock_invalid")
    day = now.astimezone(KST).date().isoformat()
    cache = (
        data_root
        / "runtime/sentinel_event_cache"
        / f"buy_funnel_sentinel_events_{day}.jsonl"
    )
    meta_path = cache.with_suffix(".meta.json")
    # The cache writer and its optional time index form one generation.
    with meta_path.with_suffix(".lock").open("a") as lock, ExitStack() as stack:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        meta = _metadata(meta_path)
        from src.engine.monitoring import sentinel_compact_store as compact
        archive_receipt = Path(str(cache) + ".archive.json")
        binding = None
        if not cache.exists() and (archive_receipt.exists() or archive_receipt.is_symlink()):
            from src.engine.sentinel_event_cache import archived_cache_binding

            binding = archived_cache_binding(cache, meta)
        if binding:
            stack.enter_context(compact._verified_archive(cache, binding))
        generation = binding["source_generation"] if binding else stamp(cache)
        if (
            meta.get("schema_version") not in (19, 20, 21, 22)
            or meta.get("cache_generation") != generation
            or meta.get("cache_projection_skip_reason")
            or not meta.get("compact_index_enabled")
        ):
            raise ValueError("source_window_cache_unverified")
        raw = data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
        if str(raw) != meta.get("raw_path"):
            raise ValueError("source_window_raw_path_mismatch")
        if binding:
            from src.engine.sentinel_event_cache import _raw_producer_rotation_lease

            stack.enter_context(_raw_producer_rotation_lease(raw))
        conn = sqlite3.connect(
            f'file:{cache.with_suffix(".compact.sqlite")}?mode=ro',
            uri=True,
            isolation_level=None,
        )
        try:
            conn.execute("BEGIN")
            record = conn.execute(
                "SELECT body FROM source_window_state WHERE id=1"
            ).fetchone()
            state = _object(record[0]) if record else {}
            if state.get("contract") != _contract():
                _predecessor_issuer(data_root, state.get("contract"))
            if (
                state.get("generation") != generation
                or state != meta.get("source_window_projection")
                or state.get("raw_offset") != meta.get("raw_offset")
                or state.get("raw_generation") != meta.get("raw_generation")
                or state.get("schema_version") != meta["schema_version"]
                or state.get("invalid_rows") != 0
                or state.get("historical_stage_coverage")
                != "not_backfilled_before_cache_offset"
                or not isinstance(state.get("coverage_started_epoch"), (int, float))
                or state["coverage_started_epoch"] > lower_epoch
            ):
                raise ValueError("source_window_stage_coverage_incomplete")
            if conn.execute("SELECT count(*) FROM source_window_rows").fetchone()[
                0
            ] != state.get("row_count"):
                raise ValueError("source_window_index_population_changed")
            # Verify the complete lightweight identity index, including its SQL
            # clock column, against the cache owner's separately committed seal.
            # Changed clocks cannot quietly remove a row from the window query.
            chain, identity_bytes = hashlib.sha256(b"").hexdigest(), 0
            for offset, epoch, sha in conn.execute(
                "SELECT offset, emitted_epoch, sha FROM source_window_rows ORDER BY offset"
            ):
                chain, size = _chain(chain, offset, epoch, sha)
                identity_bytes += size
                if identity_bytes > limit:
                    raise ValueError("source_window_identity_read_budget_exceeded")
            if chain != state.get("population_sha256") or identity_bytes != state.get(
                "population_bytes"
            ):
                raise ValueError("source_window_index_population_changed")
            rows, indexed_bytes = [], 0
            for body, sha in conn.execute(
                "SELECT body, sha FROM source_window_rows "
                "WHERE emitted_epoch >= ? AND emitted_epoch <= ? ORDER BY offset",
                (lower_epoch, now.timestamp()),
            ):
                decoder = zlib.decompressobj()
                try:
                    decoded = decoder.decompress(body, limit - indexed_bytes + 1)
                except zlib.error as exc:
                    raise ValueError("source_window_index_row_corrupt") from exc
                indexed_bytes += len(decoded)
                if indexed_bytes > limit or not decoder.eof or decoder.unused_data:
                    raise ValueError("source_window_index_read_budget_exceeded")
                if hashlib.sha256(decoded).hexdigest() != sha:
                    raise ValueError("source_window_index_row_corrupt")
                row = _object(decoded)
                if (
                    row.get("pipeline") != "ENTRY_PIPELINE"
                    or row.get("stage") not in STAGES
                    or not lower_epoch
                    <= _epoch(row.get("emitted_at"))
                    <= now.timestamp()
                ):
                    raise ValueError("source_window_index_row_invalid")
                rows.append(row)
            original = state["raw_generation"]
            offset = state["raw_offset"]
            raw_archive_generation = None
            try:
                raw_source = raw.open("rb")
            except FileNotFoundError:
                if raw.is_symlink():
                    raise ValueError("source_window_raw_generation_or_budget_changed")
                from src.engine.sentinel_event_cache import _archive_raw_generation_matches, _raw_producer_rotation_lease
                from src.engine.automation import main_trailing_source_store as trailing

                if not binding:
                    stack.enter_context(_raw_producer_rotation_lease(raw))
                raw_archive = Path(str(raw) + ".gz")
                before = raw_archive.stat()
                if not _archive_raw_generation_matches(meta, raw_archive, before, cache.parent):
                    raise ValueError("source_window_raw_archive_generation_changed")
                raw_archive_generation = trailing._archive_generation(data_root, raw)
                after = raw_archive.stat()
                if (after != before or not _archive_raw_generation_matches(meta, raw_archive, after, cache.parent)):
                    raise ValueError("source_window_raw_archive_generation_changed")
                payload = b""
                logical_source_size = original["size_bytes"]
            else:
                with raw_source as source:
                    before = os.fstat(source.fileno())
                    if (
                        (before.st_dev, before.st_ino)
                        != (original.get("device"), original.get("inode"))
                        or not 0 <= before.st_size - offset <= limit
                        or (
                            before.st_size == original.get("size_bytes")
                            and (before.st_mtime_ns, before.st_ctime_ns)
                            != (original.get("mtime_ns"), original.get("ctime_ns"))
                        )
                    ):
                        raise ValueError("source_window_raw_generation_or_budget_changed")
                    source.seek(offset)
                    payload = source.read(before.st_size - offset)
                    after = raw.stat()
                logical_source_size = before.st_size
            if (
                (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                or after.st_size < before.st_size
                or (not binding and stamp(cache) != generation)
                or (
                    after.st_size == before.st_size
                    and (after.st_mtime_ns, after.st_ctime_ns)
                    != (before.st_mtime_ns, before.st_ctime_ns)
                )
            ):
                raise ValueError("source_window_generation_changed_during_read")
            if payload and not payload.endswith(b"\n"):
                raise ValueError("source_window_raw_partial_line")
            for line in payload.splitlines():
                row = _object(line)
                epoch = _epoch(row.get("emitted_at"))
                if (
                    row.get("pipeline") == "ENTRY_PIPELINE"
                    and row.get("stage") in STAGES
                    and lower_epoch <= epoch <= now.timestamp()
                ):
                    rows.append(row)
            return rows, dict(
                status="complete",
                window_covered=True,
                tail_truncated=False,
                recent_count=len(rows),
                malformed_rows=0,
                missing_timestamp_rows=0,
                incomplete_last_line=False,
                first_read_at=datetime.fromtimestamp(lower_epoch, KST).isoformat(),
                bytes_read=len(payload),
                indexed_bytes_read=indexed_bytes,
                read_count=1,
                indexed_identity_bytes_read=identity_bytes,
                source_size=logical_source_size,
                source_identity=dict(device=before.st_dev, inode=before.st_ino),
                coverage_basis="verified_forward_sentinel_source_window_v1",
                coverage_started_at=datetime.fromtimestamp(
                    state["coverage_started_epoch"], KST
                ).isoformat(),
                current_window_start_at=datetime.fromtimestamp(
                    lower_epoch, KST
                ).isoformat(),
                indexed_raw_offset=offset,
                cache_generation=generation,
                cache_schema_version=meta["schema_version"],
                projection_contract=state["contract"],
                historical_stage_coverage=state["historical_stage_coverage"],
                **({"cache_archive_binding": binding} if binding else {}),
                **({"raw_archive_generation": raw_archive_generation} if raw_archive_generation else {}),
            )
        finally:
            conn.close()


def _native_index_state(cache, generation, expected_count):
    """Verify the existing native index without creating or repairing it."""
    from src.engine.monitoring import sentinel_compact_store as compact

    if (
        type(expected_count) is not int
        or expected_count < 0
        or compact.stamp(cache) != generation
    ):
        raise ValueError("source_window_prepare_native_index_unverified")
    path = cache.with_suffix(".compact.sqlite")
    try:
        with closing(
            sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=1)
        ) as conn:
            conn.execute("PRAGMA query_only=ON")
            saved = conn.execute(
                "SELECT length(CAST(body AS BLOB)), "
                "substr(CAST(body AS BLOB), 1, 1048577) "
                "FROM state WHERE id=1"
            ).fetchone()
            if not saved or saved[0] > 1024 * 1024:
                raise ValueError("source_window_prepare_native_index_unverified")
            state = _object(saved[1])
    except (sqlite3.DatabaseError, OSError, TypeError, ValueError) as exc:
        raise ValueError("source_window_prepare_native_index_unverified") from exc
    contract = hashlib.sha256(Path(compact.__file__).read_bytes()).hexdigest()
    if (
        state.get("contract") != contract
        or state.get("generation") != generation
        or type(state.get("offset")) is not int
        or state["offset"] != generation[2]
        or type(state.get("count")) is not int
        or state["count"] != expected_count
        or compact.stamp(cache) != generation
    ):
        raise ValueError("source_window_prepare_native_index_unverified")
    return state


def prepare(data_root, *, max_batches=4):
    """Initialize the forward projection after drain and before Main starts.

    Retain the existing raw/cache cursor and its historical gaps. Only a small
    verified append is permitted here; no missing cache or full-day rebuild.
    The ordinary sentinel writer owns all subsequent append transactions.
    """
    import fcntl
    from src.engine import buy_funnel_sentinel as buy
    from src.engine.sentinel_event_cache import _update_and_load_cached_event_rows
    from src.engine.monitoring.sentinel_compact_store import stamp, indexed_rows

    data_root = Path(data_root).resolve()
    if type(max_batches) is not int or not 1 <= max_batches <= 4:
        raise ValueError("source_window_prepare_batch_budget_invalid")
    day = datetime.now(KST).date().isoformat()
    cache_dir = data_root / "runtime/sentinel_event_cache"
    cache = cache_dir / f"{buy.EVENT_CACHE_NAME}_{day}.jsonl"
    meta_path = cache.with_suffix(".meta.json")
    with meta_path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        meta = _metadata(meta_path)
        raw = data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
        raw_stat = raw.stat()
        old_schema = meta.get("schema_version")
        if (
            old_schema not in (17, 18, 19, 20, 21, 22)
            or meta.get("cache_generation") != stamp(cache)
            or meta.get("raw_path") != str(raw)
            or meta.get("raw_inode") != raw_stat.st_ino
            or not 0
            <= raw_stat.st_size - int(meta.get("raw_offset", -1))
            <= LIMIT * max_batches
            or meta.get("cache_projection_skip_reason")
            or meta.get("cache_projection_version") != "economic_source_refs_v1"
        ):
            raise ValueError("source_window_prepare_existing_cursor_unverified")
        schema = (
            buy.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION
            if old_schema % 2 == 0
            else buy.EVENT_CACHE_SCHEMA_VERSION
        )
        migration = None
        if old_schema != schema:
            migration = dict(
                from_schema=old_schema,
                to_schema=schema,
                raw_generation=dict(
                    device=raw_stat.st_dev,
                    inode=raw_stat.st_ino,
                    size_bytes=raw_stat.st_size,
                    mtime_ns=raw_stat.st_mtime_ns,
                    ctime_ns=raw_stat.st_ctime_ns,
                ),
                raw_offset=meta["raw_offset"],
                newly_admitted_stages=(
                    ["pre_submit_liquidity_guard_block"]
                    + (
                        sorted(STAGES - {"entry_async_disposition"})
                        if old_schema < 19
                        else []
                    )
                ),
                population_proof="forward_only_stage_extension",
                historical_stage_coverage="not_backfilled_before_raw_offset",
            )
        previous_offset = meta["raw_offset"]
        batch_meta = meta
        native_batches = []
        for batch in range(max_batches):
            prior_generation = batch_meta["cache_generation"]
            _native_index_state(
                cache, prior_generation, batch_meta["cache_event_count"]
            )
            _, updated = _update_and_load_cached_event_rows(
                raw_path=raw,
                cache_dir=cache_dir,
                cache_name=buy.EVENT_CACHE_NAME,
                target_date=day,
                schema_version=schema,
                parse_payload=lambda row: buy._payload_to_cache_row(
                    row,
                    exclude_summary_stages=schema
                    == buy.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION,
                ),
                verified_schema_migration=migration if batch == 0 else None,
                project_loaded_payload=buy._slim_economic_cache_row,
                cache_projection_version="economic_source_refs_v1",
                load_rows=False,
                compact_index=True,
                max_append_bytes=LIMIT,
            )
            generation = stamp(cache)
            delta = generation[2] - prior_generation[2]
            if (
                generation != updated["cache_generation"]
                or generation[:2] != prior_generation[:2]
                or not 0 <= delta <= LIMIT
            ):
                raise ValueError("source_window_prepare_native_append_budget_invalid")
            # The native owner commits and verifies its complete generation
            # before yielding its first row. Close immediately: preparation
            # needs its bounded append transaction, not all historical rows.
            rows = indexed_rows(
                cache,
                previous_stamp=prior_generation,
                expected_count=updated["cache_event_count"],
            )
            try:
                next(rows, None)
            finally:
                rows.close()
            native = _native_index_state(
                cache, generation, updated["cache_event_count"]
            )
            native_batches.append(
                dict(
                    prior_generation=prior_generation,
                    generation=generation,
                    appended_cache_bytes=delta,
                    count=native["count"],
                    contract=native["contract"],
                )
            )
            batch_meta = updated
            if updated["raw_offset"] == updated["raw_size"]:
                break
            if updated["raw_offset"] <= previous_offset:
                raise ValueError(
                    "source_window_prepare_incomplete_or_oversized_raw_line"
                )
            previous_offset = updated["raw_offset"]
        else:
            raise ValueError("source_window_prepare_append_budget_exhausted")
        return dict(
            schema="sentinel_source_window_preparation_v1",
            target_date=day,
            prior_raw_offset=meta["raw_offset"],
            raw_offset=updated["raw_offset"],
            prior_cache_generation=meta["cache_generation"],
            cache_generation=updated["cache_generation"],
            projection=updated["source_window_projection"],
            runtime_effect=False,
            batches=batch + 1,
            native_index_batches=native_batches,
            historical_stage_coverage="not_backfilled_before_cache_offset",
        )
