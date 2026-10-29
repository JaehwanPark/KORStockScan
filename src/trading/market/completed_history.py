"""REST-adjusted minute history: immutable completed revisions, fresh forming.

A daily derived SQLite store deduplicates bars across revisions and consumers.
Readers pin private snapshots; corrections never alter returned inputs. There
is no order authority, raw WS composition, or deletion of referenced revisions.
"""

from copy import deepcopy
from contextlib import closing
from datetime import datetime
import hashlib
import json
import math
import os
import re
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo
import zlib

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "main_rest_minute_history_v2"
MAX_ROWS = 900
MAX_DATABASE_BYTES = 128 * 1024 * 1024
MAX_REVISIONS_PER_SCOPE = 2048


def key(scope, item, date, session="unspecified"):
    return dict(
        schema=SCHEMA,
        auth_scope=list(scope),
        item=item,
        date=date,
        session=session,
        interval_sec=60,
        adjustment="ka10080:upd_stkpc_tp=1",
        time_basis="provider_bar_open_kst",
    )


def _bytes(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _path(root, identity):
    day = identity["date"]
    datetime.strptime(day, "%Y%m%d")
    return Path(root) / "runtime" / "main_minute_history" / day / "completed.sqlite3"


def _unpack(raw):
    decoder = zlib.decompressobj()
    body = decoder.decompress(raw, 2 * 1024 * 1024 + 1)
    if len(body) > 2 * 1024 * 1024 or not decoder.eof or decoder.unused_data:
        raise ValueError("invalid history manifest")
    sealed = json.loads(body)
    if _digest(sealed["value"]) != sealed["sha256"]:
        raise ValueError("history receipt checksum mismatch")
    return sealed["value"]


def _pack(value):
    return zlib.compress(_bytes(dict(value=value, sha256=_digest(value))))


def _completed(rows, now):
    cutoff = datetime.fromtimestamp(now, KST).strftime("%Y%m%d%H%M00")
    completed, forming, seen = [], [], set()
    for row in rows:
        stamp = row["source_timestamp"]
        datetime.strptime(stamp, "%Y%m%d%H%M%S")
        if stamp in seen or stamp > cutoff:
            raise ValueError("duplicate or future source bar")
        seen.add(stamp)
        for field in ("시가", "고가", "저가", "현재가", "거래량"):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError("invalid source OHLCV")
        if not (
            0
            < row["저가"]
            <= min(row["시가"], row["현재가"])
            <= max(row["시가"], row["현재가"])
            <= row["고가"]
        ):
            raise ValueError("invalid source OHLC bounds")
        (forming if stamp == cutoff else completed).append(deepcopy(row))
    return sorted(completed, key=lambda r: r["source_timestamp"]), forming


def read(root, identity, *, now, limit, include_forming=True, revision=None):
    """Read a provider-verified cutoff or an available named historical revision."""
    try:
        path = _path(root, identity)
        if not path.exists() or not math.isfinite(now) or limit < 1:
            return None
        with closing(
            sqlite3.connect(
                path.absolute().as_uri() + "?mode=ro", uri=True, timeout=0.025
            )
        ) as db:
            db.execute("BEGIN")
            current = db.execute(
                "SELECT revision, receipt FROM current WHERE scope=?",
                (_digest(identity),),
            ).fetchone()
            if current is None:
                return None
            selected = revision or current[0]
            stored = db.execute(
                "SELECT manifest, available FROM revisions WHERE hash=? AND scope=?",
                (selected, _digest(identity)),
            ).fetchone()
            if stored is None or stored[1] > now:
                return None
            manifest = _unpack(stored[0])
            if _digest(manifest) != selected or manifest["identity"] != identity:
                return None
            receipt = (
                _unpack(current[1]) if revision is None else manifest["first_receipt"]
            )
            if receipt["received_at"] > now:
                return None
            if revision is None and int(now // 60) != receipt["verified_cutoff"]:
                return None
            if include_forming and (
                revision is not None or now >= receipt["forming_expires_at"]
            ):
                return None
            hashes = manifest["bar_hashes"]
            if len(hashes) > MAX_ROWS:
                return None
            rows = {}
            if hashes:
                query = (
                    "SELECT hash, content FROM bars WHERE hash IN ("
                    + ",".join("?" for _ in hashes)
                    + ")"
                )
                for fingerprint, content in db.execute(query, hashes):
                    row = json.loads(content)
                    if _digest(row) != fingerprint:
                        return None
                    rows[fingerprint] = row
            values = [rows[h] for h in hashes]
            if include_forming:
                values += receipt["forming"]
            if len(values) < limit:
                return None
            meta = dict(
                receipt["source_meta"],
                shared_history_schema=SCHEMA,
                shared_history_revision_sha256=selected,
                shared_history_available_at=stored[1],
                shared_history_completed_cutoff=receipt["verified_cutoff"],
                shared_history_reused=True,
                requested_limit=limit,
                shared_history_forming_included=include_forming,
                shared_history_completed_count=len(hashes),
                shared_history_selected_at=now,
                shared_history_source_method="rest_adjusted_completed_revision",
                read_response_cache_status="hit",
                read_response_cache_caller_http_attempt_count=0,
                read_singleflight_caller_http_attempt_count=0,
            )
            return deepcopy(values[-limit:]), meta
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, zlib.error):
        return None


def causal_generation(root, days):
    """Identity of available immutable revisions; absence is not a permanent cache.

    Read metadata only, once per date. Never expose private scope identifiers.
    A newly imported original revision invalidates a cached empty campaign.
    """
    generations = {}
    for day in sorted(set(days)):
        parsed = datetime.strptime(day, "%Y-%m-%d")
        path = _path(root, dict(date=parsed.strftime("%Y%m%d")))
        if not path.exists():
            generations[day] = None
            continue
        with closing(
            sqlite3.connect(
                path.absolute().as_uri() + "?mode=ro", uri=True, timeout=0.025
            )
        ) as db:
            fingerprint = hashlib.sha256()
            read_bytes = 0
            for row in db.execute(
                "SELECT hash,scope,available FROM revisions ORDER BY hash"
            ):
                raw = _bytes(row) + b"\n"
                read_bytes += len(raw)
                if read_bytes > MAX_DATABASE_BYTES:
                    raise ValueError("history_causal_metadata_budget")
                fingerprint.update(raw)
            generations[day] = fingerprint.hexdigest()
    return generations


def causal_prefixes(root, requests):
    """Read bounded, as-of completed prefixes for an outcome-blind reservoir.

    One metadata census per day, indexed scope lookups, and named revisions
    only. A later correction or current pointer never supplies past features.
    Multiple authentication scopes must agree; their identities stay private.
    """
    if not isinstance(requests, list) or len(requests) > 4096:
        raise ValueError("history_causal_request_bounds")
    from collections import defaultdict

    groups = defaultdict(list)
    results = [
        dict(status="unavailable", reason="history_database_absent") for _ in requests
    ]
    for index, request in enumerate(requests):
        at, item, session = (request.get(k) for k in ("at", "item", "session"))
        if (
            type(at) not in (int, float)
            or not math.isfinite(at)
            or not isinstance(item, str)
            or not re.fullmatch(r"\d{6}(?:_NX|_AL)?", item)
            or not isinstance(session, str)
            or not session
        ):
            raise ValueError("history_causal_request_invalid")
        day = datetime.fromtimestamp(at, KST).strftime("%Y%m%d")
        groups[day].append((index, request))
    for day, batch in groups.items():
        path = _path(root, dict(date=day))
        if not path.exists():
            continue
        with closing(
            sqlite3.connect(
                path.absolute().as_uri() + "?mode=ro", uri=True, timeout=0.025
            )
        ) as db:
            db.execute("BEGIN")
            scopes = defaultdict(list)
            read_bytes = 0
            for scope, revision, raw in db.execute(
                "SELECT c.scope,r.hash,r.manifest FROM current c JOIN revisions r ON c.revision=r.hash"
            ):
                read_bytes += len(raw)
                if read_bytes > MAX_DATABASE_BYTES:
                    raise ValueError("history_causal_metadata_budget")
                manifest = _unpack(raw)
                identity = manifest["identity"]
                if _digest(manifest) != revision or _digest(identity) != scope:
                    raise ValueError("history_causal_scope_changed")
                if identity["date"] == day:
                    scopes[identity["item"], identity["session"]].append(
                        (scope, identity)
                    )
            cache = {}
            for index, request in batch:
                at = request["at"]
                found = []
                for scope, identity in scopes[request["item"], request["session"]]:
                    selected = db.execute(
                        "SELECT hash,available FROM revisions WHERE scope=? AND available<=? "
                        "ORDER BY available DESC,hash LIMIT 1",
                        (scope, at),
                    ).fetchone()
                    if selected is None:
                        continue
                    revision, available = selected
                    key = (scope, revision)
                    if key not in cache:
                        raw = db.execute(
                            "SELECT manifest FROM revisions WHERE hash=?", (revision,)
                        ).fetchone()[0]
                        read_bytes += len(raw)
                        if read_bytes > MAX_DATABASE_BYTES:
                            raise ValueError("history_causal_metadata_budget")
                        manifest = _unpack(raw)
                        # Use the existing hash-validating reader; cache only an
                        # immutable five-row prefix, never a mutable latest view.
                        cache[key] = read(
                            root,
                            identity,
                            now=at,
                            limit=min(5, len(manifest["bar_hashes"])),
                            include_forming=False,
                            revision=revision,
                        )
                    result = cache[key]
                    if result is None:
                        continue
                    rows, meta = result
                    completed, forming = _completed(rows, at)
                    completed = [
                        row
                        for row in completed
                        if row["source_timestamp"].startswith(day)
                    ]
                    if (
                        forming
                        or not completed
                        or meta.get("api_id") != "ka10080"
                        or meta.get("request_code") != request["item"]
                    ):
                        continue
                    found.append(
                        dict(
                            rows=completed,
                            revision=revision,
                            available_at=available,
                            source_meta=meta,
                        )
                    )
                if not found:
                    results[index] = dict(
                        status="unavailable", reason="causal_revision_missing"
                    )
                elif len({_digest(row["rows"]) for row in found}) != 1:
                    results[index] = dict(
                        status="unavailable", reason="causal_revision_conflict"
                    )
                else:
                    chosen = max(
                        found, key=lambda row: (row["available_at"], row["revision"])
                    )
                    results[index] = dict(
                        status="verified",
                        item=request["item"],
                        session=request["session"],
                        at=at,
                        **chosen,
                    )
    return results


def outcome_revisions(root, day, *, as_of=None):
    """Export bounded, portable completed revisions for offline outcomes.

    This reads the native index and named immutable revisions, never the hot
    cache or a provider. A caller freezes each yielded source in its own run.
    No WS adjustment equivalence or execution authority is implied.
    """
    datetime.strptime(day, "%Y-%m-%d")
    now = datetime.now(KST).timestamp() if as_of is None else as_of
    if not math.isfinite(now):
        raise ValueError("invalid completed outcome selection clock")
    path = (
        Path(root)
        / "runtime/main_minute_history"
        / day.replace("-", "")
        / "completed.sqlite3"
    )
    base = dict(
        schema="main_rest_completed_outcome_v1",
        source_date=day,
        source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        runtime_effect=False,
        allowed_runtime_apply=False,
        metric_role="source_quality_gate",
        decision_authority="offline_outcome_only",
        window_policy="exact_item_date_named_completed_revision",
        sample_floor="none",
        primary_decision_metric="verified_completed_rows",
        source_quality_gate="native_revision_bar_hash_and_original_request_provenance",
        forbidden_uses=[
            "runtime_quote",
            "WS_adjustment_equivalence",
            "order_or_fill_authority",
        ],
    )
    if not path.exists():
        yield dict(base, status="unavailable", reason="history_database_absent")
        return
    try:
        with closing(
            sqlite3.connect(
                path.absolute().as_uri() + "?mode=ro", uri=True, timeout=0.025
            )
        ) as db:
            for scope, revision, stored_scope, available, raw in db.execute(
                "SELECT c.scope,c.revision,r.scope,r.available,r.manifest FROM current c "
                "LEFT JOIN revisions r ON r.hash=c.revision ORDER BY c.scope"
            ):
                try:
                    if raw is None:
                        raise ValueError("history_revision_unavailable")
                    manifest = _unpack(raw)
                    identity = manifest["identity"]
                    if (
                        scope != stored_scope
                        or scope != _digest(identity)
                        or _digest(manifest) != revision
                        or identity["schema"] != SCHEMA
                        or identity["date"] != day.replace("-", "")
                        or not isinstance(identity.get("auth_scope"), list)
                        or len(identity["auth_scope"]) < 2
                        or identity["interval_sec"] != 60
                        or identity["adjustment"] != "ka10080:upd_stkpc_tp=1"
                        or identity["time_basis"] != "provider_bar_open_kst"
                    ):
                        raise ValueError("history_identity_invalid")
                    meta = manifest["first_receipt"]["source_meta"]
                    if (
                        available > now
                        or type(meta.get("rest_received_ts_ms")) is not int
                        or meta["rest_received_ts_ms"] / 1000 > now
                        or meta.get("api_id") != "ka10080"
                        or meta.get("request_code") != identity["item"]
                        or meta.get("request_base_dt") != identity["date"]
                        or str(meta.get("last_http_status_code")) != "200"
                        or meta.get("read_rate_control_status") != "admitted"
                        or any(
                            meta.get(k)
                            for k in (
                                "continuous_next_key_missing",
                                "rate_limit_detected",
                                "fetch_error",
                                "read_shared_cache_scope_changed",
                            )
                        )
                    ):
                        raise ValueError("history_provenance_invalid")
                    pair = read(
                        root,
                        identity,
                        now=now,
                        limit=max(1, len(manifest["bar_hashes"])),
                        include_forming=False,
                        revision=revision,
                    )
                    if pair is None:
                        raise ValueError("history_revision_unavailable")
                    rows, _ = pair
                    # Revalidate the exported OHLCV and original completed cutoff.
                    completed, forming = _completed(
                        rows, meta["rest_received_ts_ms"] / 1000
                    )
                    if forming or len(completed) != len(rows):
                        raise ValueError("history_forming_row_in_completed_revision")
                    value = dict(
                        base,
                        status="verified",
                        revision=revision,
                        source_item=identity["item"],
                        request_session=identity["session"],
                        identity_sha256=_digest(identity),
                        available_at=available,
                        source_origin=identity["auth_scope"][1],
                        source_meta=meta,
                        rows=completed,
                        rows_sha256=_digest(completed),
                    )
                    outcome_rows(value, day=day)
                    yield value
                except (ValueError, KeyError, TypeError, zlib.error) as exc:
                    yield dict(
                        base,
                        status="excluded",
                        revision=revision,
                        reason=(
                            str(exc)
                            if isinstance(exc, ValueError)
                            else type(exc).__name__
                        ),
                    )
    except (OSError, sqlite3.Error) as exc:
        yield dict(base, status="unavailable", reason=type(exc).__name__)


def outcome_rows(value, *, day):
    """Validate a portable, hash-bound source without reopening a live index."""
    meta = value["source_meta"]
    if (
        value.get("schema") != "main_rest_completed_outcome_v1"
        or value.get("status") != "verified"
        or value.get("source_date") != day
        or value.get("runtime_effect") is not False
        or value.get("allowed_runtime_apply") is not False
        or value.get("decision_authority") != "offline_outcome_only"
        or not re.fullmatch(
            r"[0-9A-Z]{6}(?:_AL|_NX)?", str(value.get("source_item", ""))
        )
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("revision", "")))
        or value["rows_sha256"] != _digest(value["rows"])
        or not 0 < len(value["rows"]) <= MAX_ROWS
        or meta.get("request_code") != value["source_item"]
        or meta.get("request_base_dt") != day.replace("-", "")
        or meta.get("api_id") != "ka10080"
        or str(meta.get("last_http_status_code")) != "200"
        or meta.get("read_rate_control_status") != "admitted"
        or type(meta.get("rest_received_ts_ms")) is not int
        or type(value.get("available_at")) not in (int, float)
        or not math.isfinite(value["available_at"])
        or value["available_at"] > datetime.now(KST).timestamp()
        or meta["rest_received_ts_ms"] / 1000 > datetime.now(KST).timestamp()
        or any(
            meta.get(k)
            for k in (
                "continuous_next_key_missing",
                "rate_limit_detected",
                "fetch_error",
                "read_shared_cache_scope_changed",
            )
        )
    ):
        raise ValueError("completed_outcome_source_invalid")
    completed, forming = _completed(value["rows"], meta["rest_received_ts_ms"] / 1000)
    if forming or len(completed) != len(value["rows"]):
        raise ValueError("completed_outcome_rows_not_completed")
    return completed


def publish(root, identity, rows, source_meta, *, now, consumption_receipt=None):
    """Publish with CAS; recheck the full returned overlap on every refresh."""
    received = source_meta.get("rest_received_ts_ms")
    if (
        not rows
        or len(rows) > MAX_ROWS
        or type(received) is not int
        or not 0 <= now - received / 1000 <= 5
        or source_meta.get("request_code") != identity["item"]
    ):
        return False
    completed, forming = _completed(rows, now)
    if not completed:
        return False
    path = _path(root, identity)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size >= MAX_DATABASE_BYTES:
        return False
    receipt = dict(
        received_at=received / 1000,
        verified_cutoff=int(now // 60),
        forming=forming,
        forming_expires_at=min(
            received / 1000 + 3,
            source_meta.get("read_response_cache_expires_at", received / 1000 + 3),
        ),
        source_meta=deepcopy(source_meta),
        source_rows_sha256=_digest(rows),
    )
    scope = _digest(identity)
    with closing(sqlite3.connect(path, timeout=0.025)) as db, db:
        os.chmod(path, 0o600)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA wal_autocheckpoint=64")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS bars(hash TEXT PRIMARY KEY, content BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS revisions(hash TEXT PRIMARY KEY, scope TEXT NOT NULL,
                available REAL NOT NULL, manifest BLOB NOT NULL);
            CREATE INDEX IF NOT EXISTS revision_scope ON revisions(scope);
            CREATE TABLE IF NOT EXISTS current(scope TEXT PRIMARY KEY, revision TEXT NOT NULL,
                received REAL NOT NULL, receipt BLOB NOT NULL);
        """)
        db.execute("BEGIN IMMEDIATE")
        if (
            db.execute("PRAGMA page_count").fetchone()[0]
            * db.execute("PRAGMA page_size").fetchone()[0]
            >= MAX_DATABASE_BYTES
        ):
            return False
        old = db.execute(
            "SELECT received, revision FROM current WHERE scope=?", (scope,)
        ).fetchone()
        if old and old[0] > receipt["received_at"]:
            return False
        previous = (
            db.execute(
                "SELECT manifest FROM revisions WHERE hash=?", (old[1],)
            ).fetchone()
            if old
            else None
        )
        previous_manifest = _unpack(previous[0]) if previous else None
        prefix = []
        if previous_manifest:
            if (
                _digest(previous_manifest) != old[1]
                or previous_manifest["identity"] != identity
            ):
                raise ValueError("history parent revision mismatch")
            old_hashes = previous_manifest["bar_hashes"]
            if old_hashes:
                query = (
                    "SELECT hash, content FROM bars WHERE hash IN ("
                    + ",".join("?" for _ in old_hashes)
                    + ")"
                )
                previous_rows = {}
                for fingerprint, content in db.execute(query, old_hashes):
                    row = json.loads(content)
                    if _digest(row) != fingerprint:
                        raise ValueError("history parent bar mismatch")
                    previous_rows[fingerprint] = row
                prefix = [
                    previous_rows[h]
                    for h in old_hashes
                    if previous_rows[h]["source_timestamp"]
                    < completed[0]["source_timestamp"]
                ]
            prefix = (
                prefix[-max(0, MAX_ROWS - len(completed)) :]
                if len(completed) < MAX_ROWS
                else []
            )
            completed = prefix + completed
        hashes = [_digest(row) for row in completed]
        if previous_manifest and previous_manifest["bar_hashes"] == hashes:
            revision = old[1]
        else:
            count = db.execute(
                "SELECT count(*) FROM revisions WHERE scope=?", (scope,)
            ).fetchone()[0]
            if count >= MAX_REVISIONS_PER_SCOPE:
                return False
            # Forming is a separate fresh receipt, never part of a completed revision.
            first_receipt = dict(receipt, forming=[])
            manifest = dict(
                schema=SCHEMA,
                identity=identity,
                bar_hashes=hashes,
                first_receipt=first_receipt,
                first_completed=completed[0]["source_timestamp"],
                last_completed=completed[-1]["source_timestamp"],
                prefix_revision_sha256=old[1] if prefix else None,
                prefix_count=len(prefix),
                adjustment_equivalence_to_ws="unproven",
                gap_policy="observed_provider_rows_no_synthetic_fill",
            )
            revision = _digest(manifest)
            db.executemany(
                "INSERT OR IGNORE INTO bars VALUES (?,?)",
                [(h, _bytes(row)) for h, row in zip(hashes, completed)],
            )
            db.execute(
                "INSERT OR IGNORE INTO revisions VALUES (?,?,?,?)",
                (revision, scope, receipt["received_at"], _pack(manifest)),
            )
        db.execute(
            "INSERT OR REPLACE INTO current VALUES (?,?,?,?)",
            (scope, revision, receipt["received_at"], _pack(receipt)),
        )
    if consumption_receipt is not None:
        consumption_receipt.update(
            shared_history_schema=SCHEMA,
            shared_history_revision_sha256=revision,
            shared_history_completed_cutoff=receipt["verified_cutoff"],
            shared_history_completed_count=len(hashes),
            shared_history_reused=False,
            shared_history_selected_at=now,
            shared_history_source_rows_sha256=_digest(rows),
            shared_history_source_method="rest_adjusted_completed_revision",
        )
    return True
