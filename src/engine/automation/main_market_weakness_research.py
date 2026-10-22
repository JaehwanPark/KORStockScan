"""Optional, bounded night worker for Main advisory weakness research.

Owns its namespace, cursor and terminal only. It is not a mandatory postclose,
PREOPEN or runtime stage and cannot regenerate an upstream source or policy.
"""

from __future__ import annotations

import argparse
import bisect
import contextlib
import ctypes
from datetime import date, datetime, time as dt_time, timedelta
import fcntl
import hashlib
import gzip
import json
import os
import pwd
import re
from pathlib import Path
import signal
import shutil
import shlex
import sqlite3
import subprocess
import sys
import tempfile
import time
import zlib

from src.engine.scalping import market_weakness_research as R

MAX_JSON = 16 * 1024 * 1024
MAX_OBJECT = 32 * 1024 * 1024
MAX_LINE = 2 * 1024 * 1024
CHUNK_BYTES = 64 * 1024 * 1024
CHUNK_ROWS = 1000
MEMORY_BYTES = 512 * 1024 * 1024
NIGHT_SECONDS = 600
RESERVATION_SECONDS = 60
TAG = "MAIN_MARKET_WEAKNESS_RESEARCH_NIGHT"
MODULE = "src.engine.automation.main_market_weakness_research"


class Deferred(Exception):
    pass


def namespace(data_root):
    return Path(data_root) / "report/main_market_weakness_research"


def read_json(path, default=None, *, limit=MAX_JSON):
    path = Path(path)
    try:
        with path.open("rb") as f:
            raw = f.read(limit + 1)
    except FileNotFoundError:
        return default
    if len(raw) > limit:
        raise ValueError("research_json_size_limit")
    return json.loads(raw)


def logical_day(path, prefix, suffix):
    match = re.fullmatch(
        re.escape(prefix) + r"(\d{4}-\d{2}-\d{2})" + re.escape(suffix) + r"(?:\.gz)?",
        Path(path).name,
    )
    if not match:
        return None
    try:
        return date.fromisoformat(match[1]).isoformat()
    except ValueError:
        return None


def stream_source(logical, kind):
    """One logical stream, with all physical aliases bound to its generation."""
    logical = Path(logical)
    aliases = [
        p for p in (logical, Path(str(logical) + ".gz")) if p.exists() or p.is_symlink()
    ]
    if not aliases:
        return None
    if any(p.is_symlink() or not p.is_file() for p in aliases):
        raise ValueError("research_source_path_type_invalid")
    selected = aliases[0]
    return dict(
        stat_receipt(selected),
        kind=kind,
        logical_path=str(logical.resolve()),
        compressed=selected.suffix == ".gz",
        aliases=[stat_receipt(p) for p in aliases],
    )


def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("research_source_duplicate_json_key")
            result[key] = value
        return result

    def constant(_value):
        raise ValueError("research_source_nonfinite_json")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


class HashingReader:
    """Hash physical bytes in the same sequential gzip pass."""

    def __init__(self, handle):
        self.handle = handle
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        raw = self.handle.read(size)
        self.digest.update(raw)
        return raw

    def __getattr__(self, name):
        return getattr(self.handle, name)


@contextlib.contextmanager
def source_handle(path):
    with Path(path).open("rb") as raw:
        if Path(path).suffix == ".gz":
            physical = HashingReader(raw)
            with gzip.GzipFile(fileobj=physical, mode="rb") as decoded:
                yield decoded, physical
        else:
            yield raw, None


def read_source_json(logical, *, limit=MAX_JSON):
    source = stream_source(logical, "json")
    if not source:
        raise FileNotFoundError(logical)
    values, receipts = [], []
    for alias in source["aliases"]:
        path = Path(alias["path"])
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as handle:
            raw = handle.read(limit + 1)
            if len(raw) > limit:
                raise ValueError("research_source_decoded_size_limit")
        if stat_receipt(path) != alias:
            raise Deferred("research_source_changed_during_read")
        values.append(strict_json(raw))
        receipts.append(dict(alias, sha256=file_hash(path)))
    if len({R.digest(v) for v in values}) != 1:
        raise ValueError("research_source_alias_conflict")
    return values[0], dict(
        source, alias_receipts=receipts, semantic_sha256=R.digest(values[0])
    )


def verify_stream_aliases(root, source, *, stop_at):
    aliases = source.get("aliases", [])
    if len(aliases) < 2:
        return
    key = R.digest(aliases)
    cache = Path(root) / "verified_sources" / ("aliases-" + key + ".json")
    previous = read_json(cache, {})
    if previous:
        check_seal(previous)
        if previous.get("aliases") == aliases:
            return
    hashes = []
    for alias in aliases:
        path = Path(alias["path"])
        opener = gzip.open if path.suffix == ".gz" else open
        digest = hashlib.sha256()
        with opener(path, "rb") as handle:
            while True:
                if time.monotonic() >= stop_at:
                    raise Deferred("stream_alias_validation_budget")
                block = handle.read(65536)
                if not block:
                    break
                digest.update(block)
        if stat_receipt(path) != alias:
            raise Deferred("stream_alias_generation_changed")
        hashes.append(digest.hexdigest())
    if len(set(hashes)) != 1:
        raise ValueError("research_source_alias_conflict")
    atomic(
        cache,
        R.seal(dict(aliases=aliases, decoded_sha256=hashes[0], **R.AUTH)),
        immutable=True,
    )


def atomic(path, value, *, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )
    if immutable and path.exists():
        if path.read_bytes() != raw:
            raise ValueError("research_immutable_artifact_changed")
        return
    fd, temp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        if immutable:
            try:
                os.link(temp, path)
            except FileExistsError:
                if path.read_bytes() != raw:
                    raise ValueError("research_immutable_artifact_changed")
        else:
            os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temp).unlink(missing_ok=True)


def atomic_text(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value.encode("utf-8")
    fd, temp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.link(temp, path)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise ValueError("immutable_markdown_changed")
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temp).unlink(missing_ok=True)


@contextlib.contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Deferred("research_namespace_busy") from None
        yield


def stat_receipt(path):
    s = Path(path).stat()
    return dict(
        path=str(Path(path).resolve()),
        device=s.st_dev,
        inode=s.st_ino,
        size=s.st_size,
        mtime_ns=s.st_mtime_ns,
        ctime_ns=s.st_ctime_ns,
    )


def check_seal(value):
    if (
        not isinstance(value, dict)
        or value.get("artifact_content_sha256")
        != R.seal(value)["artifact_content_sha256"]
    ):
        raise ValueError("research_or_source_seal_invalid")
    return value


def code_hash(code_root=None):
    modules = [
        Path(__file__),
        Path(R.__file__),
        Path(__file__).with_name("main_market_weakness_research_notify.py"),
        Path(R.__file__).parents[1] / "risk/market_weakness_state.py",
        Path(R.__file__).parents[1] / "risk/market_weakness_threshold_policy.py",
        Path(R.__file__).parents[1] / "market_panic_breadth_collector.py",
        Path(R.__file__).parent / "micro_reversion/symbol_master.py",
        Path(R.__file__).parent / "continuous_reversal.py",
        Path(R.__file__).parent / "continuous_reversal_source.py",
        Path(R.__file__).parents[1] / "lifecycle/research_json_stream.py",
    ]
    # These existing owners validate the effective registry, wire and native
    # request. Changing one invalidates research without changing live capture.
    modules.extend(
        Path(R.__file__).parent / (name + ".py")
        for name in (
            "reversal_auxiliary_intraday",
            "reversal_auxiliary_registry",
            "reversal_auxiliary_wire",
            "reversal_auxiliary_compatibility",
            "reversal_auxiliary_transition",
            "reversal_auxiliary_production_input",
            "reversal_auxiliary_risk_role_experiment",
            "reversal_operating_auxiliary",
            "reversal_extended_union",
            "continuous_reversal_policy_v5",
        )
    )
    if code_root is not None:
        executing_root = Path(__file__).resolve().parents[3]
        modules = [
            Path(code_root) / p.resolve().relative_to(executing_root) for p in modules
        ]
    return R.digest(
        {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in modules}
    )


class ReadObjects:
    """Bounded read-only pack reader. No store migration, writer lock or cache."""

    def __init__(self, data_root):
        self.root = Path(data_root) / "ai_comparison_store/v1"
        database = self.root / "metadata.sqlite3"
        if not database.exists():
            raise FileNotFoundError("retained_shared_store_unavailable")
        self.db = sqlite3.connect(
            database.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.1
        )
        self.db.execute("PRAGMA query_only=ON")
        self.db.execute("PRAGMA cache_size=-2048")
        self.receipts = {}

    def close(self):
        self.db.close()

    def get(self, ident):
        row = self.db.execute(
            "SELECT hash,pack,offset,length,size FROM objects WHERE id=?", (ident,)
        ).fetchone()
        if row is None:
            raise ValueError("research_source_object_missing")
        h, pack, offset, length, size = row
        if not (
            0 <= size <= MAX_OBJECT
            and 0 < length <= MAX_OBJECT
            and offset >= 0
            and isinstance(pack, str)
            and Path(pack).name == pack
            and pack not in {".", ".."}
        ):
            raise ValueError("research_source_object_size_or_path_invalid")
        pack_path = self.root / "packs" / pack
        if not pack_path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("shared_pack_outside_store")
        before = stat_receipt(pack_path)
        with pack_path.open("rb") as f:
            f.seek(offset)
            encoded = f.read(length)
        if before != stat_receipt(pack_path):
            raise Deferred("shared_pack_changed_during_read")
        self.receipts[str(pack_path.resolve())] = before
        d = zlib.decompressobj()
        try:
            raw = d.decompress(encoded, MAX_OBJECT + 1)
        except zlib.error:
            raise ValueError("shared_pack_compression_invalid") from None
        if (
            not d.eof
            or d.unused_data
            or len(raw) != size
            or hashlib.sha256(raw).hexdigest() != h
        ):
            raise ValueError("research_source_object_hash_or_size_invalid")
        return json.loads(raw)


def observer_snapshot_state(data_root, receipt):
    """Read only the immutable observer evidence captured by this night owner."""
    path = Path(receipt["path"])
    directory = (namespace(data_root) / "observer_receipts").resolve()
    if path.resolve().parent != directory or not receipts_current([receipt]):
        raise ValueError("observer_snapshot_receipt_invalid")
    snapshot = check_seal(read_json(path, limit=1024 * 1024))
    if (
        not isinstance(snapshot.get("source_raw"), str)
        or snapshot.get("source_path")
        != str(
            Path(data_root).resolve().parent / "tmp/market_weakness_observer_state.json"
        )
        or any(snapshot.get(k) != v for k, v in R.AUTH.items())
    ):
        raise ValueError("observer_snapshot_contract_invalid")
    raw = snapshot["source_raw"].encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if (
        snapshot.get("schema") != R.VERSION + ":observer_snapshot"
        or snapshot.get("source_sha256") != digest
        or path.name != digest + ".json"
    ):
        raise ValueError("observer_snapshot_binding_invalid")
    state = strict_json(raw)
    if not isinstance(state, dict):
        raise ValueError("observer_snapshot_state_invalid")
    return state


def observations(data_root, source_date, *, observer_snapshot=None):
    directory = Path(data_root) / "report/market_weakness_observations" / source_date
    result, receipts, gaps = [], [], CounterDict()
    paths = sorted(directory.glob("*.json"))
    if len(paths) > 6000:
        raise Deferred("observation_census_size_limit")
    for path in paths:
        before = stat_receipt(path)
        try:
            raw = read_json(path, {}, limit=256 * 1024)
        except (ValueError, TypeError):
            raw = {}
        if before != stat_receipt(path):
            raise Deferred("observation_source_changed")
        receipts.append(
            dict(before, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        )
        if R.market_weakness_observation_contract_errors(raw):
            gaps.add("invalid_market_observation")
            continue
        for key in (
            "observed_available_at",
            "availability_receipt_verified",
            "observed_source_delay_sec",
            "observed_latch_active",
        ):
            raw.pop(key, None)
        result.append(raw)
    # Only a retained exact-ID current observer receipt can establish availability.
    state_path = (
        Path(data_root).resolve().parent / "tmp/market_weakness_observer_state.json"
    )
    state_raw = None
    if observer_snapshot:
        state = observer_snapshot_state(data_root, observer_snapshot)
    else:
        try:
            before = stat_receipt(state_path)
            with state_path.open("rb") as handle:
                state_raw = handle.read(128 * 1024 + 1)
            if len(state_raw) > 128 * 1024:
                raise ValueError("observer_state_size_limit")
            if before != stat_receipt(state_path):
                raise Deferred("observer_state_changed_during_capture")
            state = strict_json(state_raw)
        except (FileNotFoundError, ValueError, TypeError):
            state = {}
    if not isinstance(state, dict):
        state = {}
    latch = state.get("market_weakness", {})
    health = state.get("market_weakness_observer_health", {})
    if (
        isinstance(latch, dict)
        and isinstance(health, dict)
        and health.get("ready") is True
        and isinstance(latch.get("last_source_gate"), dict)
        and latch["last_source_gate"].get("passed") is True
    ):
        for o in result:
            checked = R.number(health.get("checked_at_ts"))
            if (
                checked is not None
                and o["observation_id"]
                == latch.get("last_observation_id")
                == health.get("last_healthy_observation_id")
                and o["as_of"] == latch.get("last_observation_as_of")
            ):
                o["observed_available_at"] = datetime.fromtimestamp(
                    checked, R.KST
                ).isoformat()
                o["availability_receipt_verified"] = True
                markets = latch.get("market_states", {})
                if isinstance(markets, dict):
                    o["observed_latch_active"] = {
                        m: s["active"]
                        for m, s in markets.items()
                        if m in {"KOSPI", "KOSDAQ"}
                        and isinstance(s, dict)
                        and type(s.get("active")) is bool
                    }
                o["observed_source_delay_sec"] = (
                    checked - R.timestamp(o["as_of"]).timestamp()
                )
    if observer_snapshot:
        # Keep the same historical evidence even if its observation was removed.
        # Observation additions/removals still invalidate the daily generation.
        receipts.append(observer_snapshot)
    elif any(o.get("availability_receipt_verified") for o in result):
        digest = hashlib.sha256(state_raw).hexdigest()
        snapshot_path = namespace(data_root) / "observer_receipts" / (digest + ".json")
        atomic(
            snapshot_path,
            R.seal(
                dict(
                    schema=R.VERSION + ":observer_snapshot",
                    source_path=str(state_path),
                    source_sha256=digest,
                    source_raw=state_raw.decode("utf-8"),
                    **R.AUTH,
                )
            ),
            immutable=True,
        )
        receipts.append(stat_receipt(snapshot_path))
    return R.reconstruct_latches(result), receipts, dict(gaps)


class CounterDict(dict):
    def add(self, name, n=1):
        self[name] = self.get(name, 0) + n


def listing_lookup(data_root, source_date):
    from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

    directory = Path(data_root) / "report/micro_reversion_economic_reference"
    prefix = "micro_reversion_symbol_master_"
    candidates = {
        day
        for p in directory.glob(prefix + "*.json*")
        if (day := logical_day(p, prefix, ".json")) and day <= source_date
    }
    if not candidates:
        return lambda _symbol: None, None
    day = max(candidates)
    p = directory / (prefix + day + ".json")
    try:
        payload, receipt = read_source_json(p, limit=4 * 1024 * 1024)
        if (
            payload.get("artifact_id")
            != "main-ai-economic-reference-" + day + "-symbol-master"
        ):
            raise ValueError("listing_metadata_identity_invalid")
        master = VerifiedSymbolMaster.from_payload(
            payload, require_canonical_owner=True
        )
    except (ValueError, TypeError, KeyError, OSError, EOFError, zlib.error):
        return lambda _symbol: None, dict(path=str(p), status="source_invalid")

    def lookup(symbol):
        result = master.lookup(symbol, as_of=date.fromisoformat(source_date))
        return (
            result.record.listing_market.value
            if result.economic_metadata_allowed and result.record
            else None
        )

    return lookup, receipt


def source_path(data_root, value):
    p = Path(value)
    if not p.is_absolute():
        if not p.parts or p.parts[0] != "data":
            raise ValueError("upstream_source_path_undefined")
        p = Path(data_root).joinpath(*p.parts[1:])
    p = p.resolve()
    if not p.is_relative_to(Path(data_root).resolve()):
        raise ValueError("upstream_source_outside_data_anchor")
    return p


def file_hash(path, *, stop_at=float("inf")):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            if time.monotonic() >= stop_at:
                raise Deferred("source_hash_wall_budget")
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def source_plan(data_root, source_date):
    trace = stream_source(
        Path(data_root)
        / "ai_decision_trace"
        / f"ai_decision_trace_{source_date}.jsonl",
        "natural_trace",
    )
    directory = Path(data_root) / "report/continuous_reversal_operating" / source_date
    machine, auxiliary = (
        directory / "machine-comparison.json",
        directory / "auxiliary.json",
    )
    result = []
    if machine.exists():
        result.append(dict(stat_receipt(machine), kind="operating_comparison"))
    if auxiliary.exists():
        # Only sealed published exports are read. The shared writer DB is untouched.
        try:
            report = check_seal(read_json(auxiliary))
            if (
                report.get("source_date") != source_date
                or report.get("schema") != "continuous_reversal_operating_comparison_v1"
                or any(
                    report.get(k) != v
                    for k, v in R.AUTH.items()
                    if k != "decision_authority"
                )
            ):
                raise ValueError("auxiliary_date_or_authority_invalid")
            for ref in report.get("results_sources", []):
                path = source_path(data_root, ref["path"])
                if not path.exists():
                    result.append(
                        dict(
                            path=str(path),
                            kind="missing_auxiliary_export",
                            owner=stat_receipt(auxiliary),
                        )
                    )
                    continue
                result.append(
                    dict(
                        stat_receipt(path),
                        kind="stored_auxiliary",
                        sha256=ref["sha256"],
                        owner=stat_receipt(auxiliary),
                    )
                )
        except (ValueError, TypeError, KeyError):
            result.append(
                dict(stat_receipt(auxiliary), kind="invalid_auxiliary_report")
            )
    if trace:
        result.append(trace)
    payload = stream_source(
        Path(data_root)
        / "ai_decision_payloads"
        / f"ai_decision_payloads_{source_date}.jsonl",
        "native_observations",
    )
    if payload:
        # Native evidence is indexed before the trace consumer, never by a live writer.
        result.insert(0, payload)
    return result


def dependencies(data_root, source_date):
    machine = (
        Path(data_root)
        / "report/continuous_reversal_operating"
        / source_date
        / "machine-comparison.json"
    )
    result = []
    if machine.exists():
        try:
            report = check_seal(read_json(machine))
            for part in report.get("partitions", []):
                ref = part.get("normalized_source", {})
                if ref.get("day") != source_date:
                    continue
                p = source_path(data_root, ref["path"])
                result.append(
                    dict(stat_receipt(p), sha256=ref["sha256"])
                    if p.exists()
                    else dict(path=str(p), sha256=ref["sha256"], status="missing")
                )
        except (ValueError, TypeError, KeyError):
            result.append(dict(stat_receipt(machine), status="invalid_contract"))
    return sorted(result, key=lambda r: r["path"])


def receipts_current(receipts):
    for r in receipts:
        try:
            actual = stat_receipt(r["path"])
        except OSError:
            if r.get("status") == "missing":
                continue
            return False
        if r.get("status") == "missing":
            return False
        if any(actual.get(k) != r.get(k) for k in actual):
            return False
        if r.get("aliases") and not receipts_current(r["aliases"]):
            return False
    return True


def cursor_current(data_root, cursor):
    d = cursor.get("source_descriptor", {})
    day = cursor.get("source_date")
    if d.get("code") != code_hash() or source_plan(data_root, day) != d.get("sources"):
        return False
    if dependencies(data_root, day) != d.get("dependencies", []):
        return False
    # Added/removed observations and a changed canonical listing artifact invalidate a day.
    paths = sorted(
        str(p.resolve())
        for p in (Path(data_root) / "report/market_weakness_observations" / day).glob(
            "*.json"
        )
    )
    old = sorted(
        r["path"]
        for r in d.get("observations", [])
        if "/market_weakness_observations/" in r["path"]
    )
    if paths != old or not receipts_current(d.get("observations", [])):
        return False
    if d.get("observer_snapshot"):
        try:
            observer_snapshot_state(data_root, d["observer_snapshot"])
        except (OSError, ValueError, TypeError, KeyError):
            return False
    _, listing = listing_lookup(data_root, day)
    return (
        listing == d.get("listing")
        and receipts_current(cursor.get("source_dependency_receipts", []))
        and receipts_current(cursor.get("shared_object_receipts", []))
        and all(
            receipts_current([p["stat"]])
            for p in cursor.get("partitions", [])
            if p.get("stat")
        )
    )


def rebind_compressed_sources(root, prior, descriptor, *, stop_at):
    """Reuse completed projections only across proven representation changes.

    Keep the original projection IDs and immutable manifests. New physical
    bindings get a successor generation before cumulative/outbox consumption.
    Legacy inputs without complete read hashes must use the normal reader once.
    """
    old = prior.get("source_descriptor", {})
    if prior.get("status") not in {"completed", "valid_empty", "completed_with_source_gaps"}:
        return None
    if {k: v for k, v in old.items() if k not in {"sources", "listing"}} != {
        k: v for k, v in descriptor.items() if k not in {"sources", "listing"}
    }:
        return None
    before, after = old.get("listing"), descriptor.get("listing")
    if before != after and not (
        isinstance(before, dict) and isinstance(after, dict)
        and before.get("semantic_sha256") and not after.get("status")
        and before.get("logical_path") == after.get("logical_path")
        and before["semantic_sha256"] == after.get("semantic_sha256")
    ):
        return None
    sources, replacements = old.get("sources", []), descriptor["sources"]
    if len(sources) != len(replacements):
        return None
    manifest = check_seal(read_json(prior["manifest_path"]))
    terminal = check_seal(read_json(prior["terminal_path"]))
    daily = check_seal(read_json(prior["daily_path"]))
    if (prior.get("generation") != R.digest(old)
        or terminal.get("generation") != prior.get("generation")
        or terminal.get("status") != prior.get("status")
        or terminal.get("gaps") != prior.get("gaps")
        or any(daily.get(k) != prior.get(k, {}) for k in (
            "source_census", "source_projection_census"))
        or daily.get("native_indexed_rows") != prior.get("native_indexed_rows", 0)
        or terminal.get("source_manifest_sha256") != manifest["artifact_content_sha256"]
        or terminal.get("daily_sha256") != daily["artifact_content_sha256"]
        or any(manifest.get(k) != v for k, v in old.items())
        or any(manifest.get(k, []) != prior.get(k, []) for k in (
            "partitions", "source_ranges", "stream_receipts",
            "shared_object_receipts", "source_dependency_receipts"))
        or not receipts_current(prior.get("shared_object_receipts", [])
            + prior.get("source_dependency_receipts", [])
            + [p["stat"] for p in prior.get("partitions", []) if p.get("stat")])):
        return None
    proofs = []
    for source, replacement in zip(sources, replacements):
        if source == replacement:
            continue
        if (source.get("kind") not in {"native_observations", "natural_trace"}
            or source.get("kind") != replacement.get("kind")
            or not source.get("logical_path")
            or source["logical_path"] != replacement.get("logical_path")
            or not replacement.get("compressed")):
            return None
        whole = next((r for r in prior.get("stream_receipts", [])
                      if r["path"] == source["path"]), None)
        ranges = ([dict(start=0, end=whole["decoded_bytes"], sha256=whole["decoded_sha256"])]
                  if whole else [r for r in prior.get("source_ranges", []) if r["path"] == source["path"]])
        if not ranges or ranges[0]["start"] != 0 or any(
            a["end"] != b["start"] for a, b in zip(ranges, ranges[1:])
        ) or (not source.get("compressed") and ranges[-1]["end"] != source["size"]):
            return None
        verify_stream_aliases(root, replacement, stop_at=stop_at)
        key = R.digest(dict(source=replacement, ranges=ranges))
        cache = Path(root) / "verified_sources" / ("rebind-" + key + ".json")
        proof = read_json(cache)
        if proof:
            check_seal(proof)
            if proof.get("source") != replacement or proof.get("ranges") != ranges:
                raise ValueError("research_rebind_cache_invalid")
        else:
            decoded = hashlib.sha256()
            with source_handle(replacement["path"]) as (handle, physical):
                for r in ranges:
                    digest, remaining = hashlib.sha256(), r["end"] - r["start"]
                    if remaining < 0:
                        return None
                    while remaining:
                        if time.monotonic() >= stop_at:
                            raise Deferred("compressed_rebind_wall_budget")
                        raw = handle.read(min(65536, remaining))
                        if not raw:
                            return None
                        digest.update(raw)
                        decoded.update(raw)
                        remaining -= len(raw)
                    if digest.hexdigest() != r["sha256"]:
                        return None
                if handle.read(1):  # Also verifies gzip EOF/CRC, not a prefix.
                    return None
                proof = R.seal(dict(source=replacement, ranges=ranges,
                    decoded_sha256=decoded.hexdigest(), decoded_bytes=handle.tell(),
                    physical_sha256=physical.digest.hexdigest(), **R.AUTH))
            if not receipts_current([replacement]):
                raise Deferred("compressed_rebind_source_changed")
            atomic(cache, proof, immutable=True)
        if not receipts_current([replacement]):
            raise Deferred("compressed_rebind_source_changed")
        proofs.append(dict(path=replacement["path"], **{k: proof[k] for k in (
            "decoded_sha256", "decoded_bytes", "physical_sha256")}))
    return dict(prior, source_descriptor=descriptor, generation=R.digest(descriptor),
        status="in_progress", source_index=len(replacements), offset=0,
        stream_receipts=prior.get("stream_receipts", []) + proofs,
        representation_parent=dict(generation=prior["generation"],
            manifest_sha256=manifest["artifact_content_sha256"],
            manifest_path=prior["manifest_path"]))


def verify_file(root, path, expected, *, stop_at):
    before = stat_receipt(path)
    key = R.digest([before, expected])
    cache = root / "verified_sources" / (key + ".json")
    receipt = read_json(cache, {})
    if receipt.get("source") != before or receipt.get("sha256") != expected:
        if file_hash(path, stop_at=stop_at) != expected:
            raise ValueError("upstream_source_hash_invalid")
        if before != stat_receipt(path):
            raise Deferred("upstream_source_changed_during_hash")
        atomic(
            cache,
            R.seal(dict(source=before, sha256=expected, **R.AUTH)),
            immutable=True,
        )
    else:
        check_seal(receipt)
    return before


def replay_records(
    data_root, source_date, source, listing, start=0, *, stop_at=float("inf")
):
    report = check_seal(read_json(source["path"]))
    if not (
        report.get("schema") == "continuous_reversal_operating_comparison_v1"
        and report.get("status") == "completed"
        and report.get("source_date") == source_date
        and report.get("label_contract") == R.LABEL
        and report.get("parent_bundle_sha256")
    ):
        raise ValueError("operating_comparison_contract_invalid")
    parts = [
        p
        for p in report.get("partitions", [])
        if p.get("normalized_source", {}).get("day") == source_date
    ]
    store = ReadObjects(data_root)
    # Cursor encodes partition and record offset, bounding even a large single partition.
    part_start, row_start = start if isinstance(start, list) else [start, 0]
    scope_cache = {}
    try:
        for pi in range(part_start, len(parts)):
            part = parts[pi]
            ref = part["normalized_source"]
            gaps = CounterDict()
            try:
                verify_file(
                    namespace(data_root),
                    source_path(data_root, ref["path"]),
                    ref["sha256"],
                    stop_at=stop_at,
                )
                records = store.get(part["records_object"])
                if not isinstance(records, list) or R.digest(records) != part.get(
                    "records_sha256"
                ):
                    raise ValueError("comparison_records_hash_invalid")
            except (ValueError, TypeError, FileNotFoundError, KeyError):
                yield [], [pi + 1, 0], pi + 1 == len(parts), {
                    "normalized_or_records_source_invalid": 1
                }
                continue
            issues = ref.get("issues", {})
            if not isinstance(issues, dict):
                raise ValueError("replay_upstream_issues_invalid")
            upstream_gaps = {
                "replay_upstream_" + reason: count
                for reason, count in issues.items()
                if type(count) is int and count > 0
            }
            for offset in range(
                row_start if pi == part_start else 0, len(records), CHUNK_ROWS
            ):
                output = []
                for record in records[offset : offset + CHUNK_ROWS]:
                    if time.monotonic() >= stop_at:
                        raise Deferred("replay_projection_wall_budget")
                    try:
                        snapshot = store.get(record["snapshot_obj"])
                        if not isinstance(snapshot, list) or len(snapshot) != 2:
                            raise ValueError("replay_snapshot_contract_invalid")
                        event = snapshot[0]
                        row, reason = R.project_replay(
                            record,
                            event,
                            source_date,
                            report["parent_bundle_sha256"],
                            listing(event.get("symbol")),
                        )
                    except (ValueError, TypeError, KeyError, FileNotFoundError):
                        row, reason = None, "replay_row_contract_invalid"
                    if row and row["opportunity_id"] not in report.get(
                        "quarantined_conflicts", []
                    ):
                        scope = row.get("policy_scope")
                        if scope and "|" in scope:
                            key, route = scope.rsplit("|", 1)
                            cells = {
                                c["key"]: c
                                for c in report.get("cells", [])
                                if isinstance(c, dict) and c.get("key")
                            }
                            cell = cells.get(key, {}).get("routes", {}).get(route, {})
                            row["scope_parent_machine_payload_sha256"] = (
                                cell.get("payload_sha256")
                                if cell.get("payload_sha256")
                                == R.digest(cell.get("payload"))
                                else None
                            )
                            native_scope = scope_contract(
                                data_root,
                                report["parent_bundle_sha256"],
                                key,
                                route,
                                cache=scope_cache,
                            )
                            if (
                                native_scope.get("cohort_contract")
                                and native_scope.get(
                                    "scope_parent_machine_payload_sha256"
                                )
                                == row.get("scope_parent_machine_payload_sha256")
                                and re.fullmatch(
                                    r"[0-9a-f]{64}",
                                    str(report.get("execution_code_sha256")),
                                )
                            ):
                                row["cohort_contract"] = dict(
                                    native_scope["cohort_contract"],
                                    replay_kernel_sha256=report[
                                        "execution_code_sha256"
                                    ],
                                )
                                row["machine_axes"] = native_scope.get(
                                    "machine_axes", []
                                )
                                row["native_policy_ref"] = native_scope.get(
                                    "policy_source_ref"
                                )
                        row["source_ref"] = dict(
                            report_path=source["path"],
                            report_sha256=report["artifact_content_sha256"],
                            records_object=part["records_object"],
                            snapshot_object=record["snapshot_obj"],
                            object_receipts=list(store.receipts.values()),
                        )
                        output.append(row)
                    else:
                        gaps.add(reason or "upstream_quarantined_identity")
                next_offset = offset + CHUNK_ROWS
                next_position = (
                    [pi + 1, 0] if next_offset >= len(records) else [pi, next_offset]
                )
                # Commit partition-level raw exclusions once, with the final
                # record chunk, including when resuming within the partition.
                if next_position[0] == pi + 1:
                    for reason, count in upstream_gaps.items():
                        gaps.add(reason, count)
                yield output, next_position, next_position[0] == len(parts), dict(gaps)
                gaps = CounterDict()
            if not records:
                # Empty replay points do not establish an empty market. Preserve
                # upstream row exclusions instead of silently losing label ancestry.
                gaps.add("replay_empty_partition")
                for reason, count in upstream_gaps.items():
                    gaps.add(reason, count)
                yield [], [pi + 1, 0], pi + 1 == len(parts), dict(gaps)
        if not parts:
            yield [], [0, 0], True, {"replay_source_date_partition_missing": 1}
    finally:
        store.close()


def label_index(root, cursor, *, data_root=None, stop_at=float("inf")):
    path = root / cursor["source_date"] / cursor["generation"] / "label_bindings.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA cache_size=-2048")
    db.execute(
        "CREATE TABLE IF NOT EXISTS labels(id TEXT PRIMARY KEY,row TEXT,conflict INTEGER)"
    )
    db.execute("CREATE TABLE IF NOT EXISTS loaded(partition TEXT PRIMARY KEY)")
    try:
        for part in cursor["partitions"]:
            if db.execute(
                "SELECT 1 FROM loaded WHERE partition=?", (part["sha256"],)
            ).fetchone():
                continue
            if time.monotonic() >= stop_at:
                raise Deferred("label_projection_wall_budget")
            # The immutable partition and its loaded marker commit together.
            # Later budget/interrupt failures retain this verified progress.
            with db:
                for row in projection_rows([part]):
                    if time.monotonic() >= stop_at:
                        raise Deferred("label_projection_wall_budget")
                    _index_label(db, row)
                db.execute("INSERT INTO loaded VALUES(?)", (part["sha256"],))
        if data_root is not None:
            try:
                index_native_path_labels(data_root, root, cursor, db, stop_at=stop_at)
            except (ValueError, EOFError, OSError, zlib.error) as exc:
                # A dependency failure preserves the pending population.
                raise Deferred(
                    "native_label_path_budget"
                    if str(exc) == "normalized_native_window_budget"
                    else "native_label_source_contract_invalid"
                ) from exc
        return db
    except BaseException:
        db.close()
        raise


def index_native_path_labels(data_root, root, cursor, db, *, stop_at):
    """Label captured events in the existing frozen path, not replay FSM events.

    Collector continuity uses columns 1/2; captured WS identity uses 11/12.
    Neither namespace, the actual ask nor the captured clock is approximated.
    Each immutable normalized partition is decoded once per research generation.
    """
    from src.engine.scalping import continuous_reversal as K
    from src.engine.scalping.continuous_reversal_source import iter_normalized_symbols

    complete = "native-paths-complete"
    if db.execute("SELECT 1 FROM loaded WHERE partition=?", (complete,)).fetchone():
        return
    natives = native_index(root, cursor)
    events = {}
    try:
        for (raw,) in natives.execute("SELECT row FROM native WHERE conflict=0"):
            native = strict_json(raw)
            event = native.get("event") or {}
            canonical = native.get("canonical_opportunity_id")
            at = R.timestamp(event.get("at"))
            if not canonical or not at or not event.get("source_item"):
                continue
            ep, seq = event.get("native_epoch"), event.get("native_sequence")
            if type(ep) is not int or type(seq) is not int or min(ep, seq) <= 0:
                continue
            day = cursor["source_date"]
            if at.date().isoformat() != day or event.get("event_id") != (
                f"{day}:{event.get('venue')}:{event.get('session')}:"
                f"{native['symbol']}:{ep}:{seq}"
            ):
                continue
            row = dict(
                source_date=day,
                symbol=native["symbol"],
                opportunity_id=canonical,
                canonical_alias=event.get("canonical_opportunity_id") or canonical,
                machine_confirmed_at=event["at"],
                event_id=event["event_id"],
                entry_ask=R.number(event.get("entry_ask")),
                session=event.get("session"),
                route=event.get("venue"),
                source_item=event["source_item"],
                native_epoch=ep,
                native_sequence=seq,
            )
            key = exact_event_key(row)
            if key and row["entry_ask"] is not None and row["entry_ask"] > 0:
                events[key] = row
            if len(events) > 4096:
                raise Deferred("native_label_population_budget")
    finally:
        natives.close()
    for source in cursor["source_descriptor"].get("sources", []):
        if source.get("kind") != "operating_comparison" or not events:
            continue
        report = check_seal(read_json(source["path"]))
        if not (
            report.get("schema") == "continuous_reversal_operating_comparison_v1"
            and report.get("status") == "completed"
            and report.get("source_date") == cursor["source_date"]
            and report.get("label_contract") == R.LABEL
            and report.get("parent_bundle_sha256")
        ):
            # replay_records already reports this unavailable/legacy contract.
            # Preserve the natural population with U, without borrowing labels.
            continue
        for part in report.get("partitions", []):
            ref = part.get("normalized_source", {})
            selected = {
                key: row
                for key, row in events.items()
                if (
                    ref.get("day") == row["source_date"]
                    and ref.get("venue") == row["route"]
                    and ref.get("session") == row["session"]
                )
            }
            if not selected:
                continue
            if (
                type(ref.get("rows")) is int
                and ref["rows"] > 0
                and ref.get("issues", {}).get("source_epoch_unverified") == ref["rows"]
                and type(part.get("points")) is int
                and part["points"] == 0
            ):
                # The sealed upstream census proves no eligible path in this
                # partition. Preserve U; never decode excluded raw rows again.
                continue
            marker = "native-path:" + R.digest(ref)
            if db.execute(
                "SELECT 1 FROM loaded WHERE partition=?", (marker,)
            ).fetchone():
                continue
            if time.monotonic() >= stop_at:
                raise Deferred("native_label_wall_budget")
            path = source_path(data_root, ref["path"])
            before = verify_file(root, path, ref["sha256"], stop_at=stop_at)
            by_symbol = {}
            for key, row in selected.items():
                by_symbol.setdefault(row["symbol"], {})[key] = row
            native_windows = {
                symbol: [
                    (
                        R.timestamp(row["machine_confirmed_at"]).timestamp(),
                        R.timestamp(row["machine_confirmed_at"]).timestamp() + 1800,
                    )
                    for row in targets.values()
                ]
                for symbol, targets in by_symbol.items()
            }
            with db:
                expected_metadata = dict(
                    day=ref["day"],
                    venue=ref["venue"],
                    session=ref["session"],
                    runtime_effect=False,
                    columns=[
                        "receive_epoch",
                        "transport_epoch",
                        "series_sequence",
                        "trade_price",
                        "bid",
                        "ask",
                        "qty",
                        "side",
                        "valid",
                        "source_item",
                        "quote_age_ms",
                        "native_transport_epoch",
                        "native_route_sequence",
                        "native_receive_session",
                        "exchange_session",
                    ],
                    namespace_contract=dict(
                        transport_epoch_column="collector_sequence_epoch",
                        native_transport_epoch="ws_native_epoch",
                        native_route_sequence="ws_native_route_sequence",
                    ),
                )
                for symbol, rows in iter_normalized_symbols(
                    path,
                    expected_metadata=expected_metadata,
                    legacy_native_columns=ref["day"] < "2026-10-09",
                    native_windows=native_windows,
                ):
                    if time.monotonic() >= stop_at:
                        raise Deferred("native_label_wall_budget")
                    targets = by_symbol.get(symbol)
                    if not targets:
                        continue
                    identities = {}
                    for key, row in targets.items():
                        identity = (
                            row["native_epoch"],
                            row["native_sequence"],
                            row["source_item"],
                            R.timestamp(row["machine_confirmed_at"]),
                        )
                        identities.setdefault(identity, []).append(key)
                    anchors = {}
                    for i, point in enumerate(rows):
                        if len(point) < 13 or any(
                            type(v) is not int or v <= 0 for v in point[11:13]
                        ):
                            continue  # Legacy collector identity cannot prove WS identity.
                        identity = (
                            *point[11:13],
                            point[9],
                            R.timestamp(K.iso(point[0])),
                        )
                        for key in identities.get(identity, []):
                            anchors.setdefault(key, []).append(i)
                    symbol_times = [p[0] for p in rows]
                    for key, indices in anchors.items():
                        row = targets[key]
                        index = indices[0]
                        point = rows[index]
                        reason = (
                            "native_event_path_conflict"
                            if len(indices) != 1
                            else (
                                "native_entry_source_excluded"
                                if not point[8]
                                else (
                                    "native_entry_ask_mismatch"
                                    if not K.good_quote(point)
                                    or point[5] != row["entry_ask"]
                                    else None
                                )
                            )
                        )
                        label = dict(status="UNRESOLVED", reason=reason)
                        if reason is None:
                            # Only the bounded 30-minute suffix is needed. Preserve
                            # every invalid row and collector/sequence discontinuity.
                            start = R.timestamp(row["machine_confirmed_at"]).timestamp()
                            end = bisect.bisect_right(symbol_times, start + 1800)
                            path_rows = rows[index : min(len(rows), end + 1)]
                            if len(path_rows) > 200000:
                                raise Deferred("native_label_path_budget")
                            path_rows[0] = list(path_rows[0])
                            path_rows[0][0] = start
                            _, ends, valid = K.segments(path_rows)
                            path_times = [p[0] for p in path_rows]
                            tree = K.Tree([p[3] if p[8] else None for p in path_rows])
                            label = K.label(
                                path_rows,
                                path_times,
                                tree,
                                ends,
                                valid,
                                0,
                                row["entry_ask"],
                            )
                        outcome, reason = R.label_value(
                            label, row["entry_ask"], R.LABEL
                        )
                        value = dict(
                            row,
                            outcome=outcome,
                            outcome_reason=reason,
                            source_ref=dict(
                                normalized_source=ref,
                                stat=before,
                                point_index=point[-1],
                                label_contract=R.LABEL,
                            ),
                        )
                        raw = json.dumps(value, sort_keys=True)
                        label_key = "native-label:" + key
                        old = db.execute(
                            "SELECT row FROM labels WHERE id=?", (label_key,)
                        ).fetchone()
                        if old and old[0] != raw:
                            db.execute(
                                "UPDATE labels SET conflict=1 WHERE id=?", (label_key,)
                            )
                        elif not old:
                            db.execute(
                                "INSERT INTO labels VALUES(?,?,0)", (label_key, raw)
                            )
                if before != stat_receipt(path):
                    raise Deferred("native_label_source_changed")
                db.execute("INSERT INTO loaded VALUES(?)", (marker,))
    with db:
        db.execute("INSERT INTO loaded VALUES(?)", (complete,))


def native_key(row):
    native = (
        row.get("native_receipt") or row.get("continuous_reversal_consumption") or {}
    )
    return R.digest(
        [
            row.get("evaluation_attempt_id"),
            row.get("symbol") or row.get("stock_code"),
            *[
                native.get(k)
                for k in (
                    "bundle_sha256",
                    "pid",
                    "process_start_ticks",
                    "captured_at",
                    "event_id",
                    "exact_payload_sha256",
                    "assessment_sha256",
                )
            ],
        ]
    )


def native_index(root, cursor):
    path = (
        Path(root)
        / cursor["source_date"]
        / cursor["generation"]
        / "native_bindings.sqlite"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA cache_size=-2048")
    db.execute(
        "CREATE TABLE IF NOT EXISTS native(key TEXT PRIMARY KEY,source TEXT,row TEXT,conflict INTEGER)"
    )
    return db


def scope_contract(data_root, bundle_hash, cell_key, route, *, cache):
    if len(cache) >= 256:
        cache.clear()
    key = (bundle_hash, cell_key, route)
    if key in cache and "bundle:" + str(bundle_hash) in cache:
        return cache[key]
    result = {}
    if not re.fullmatch(r"[0-9a-f]{64}", str(bundle_hash)):
        return result
    p = (
        Path(data_root)
        / "runtime/mechanistic_entry_policy/generations"
        / (bundle_hash + ".json")
    )
    try:
        before = stat_receipt(p)
        bundle_key = "bundle:" + bundle_hash
        prior = cache.get(bundle_key)
        reused = prior and prior[0] == before
        bundle = prior[1] if reused else read_json(p)
        if bundle.get("bundle_sha256") != bundle_hash or (
            not reused
            and R.digest({k: v for k, v in bundle.items() if k != "bundle_sha256"})
            != bundle_hash
        ):
            raise ValueError("native_bundle_hash_invalid")
        for old_key in list(cache):
            if (
                isinstance(old_key, str)
                and old_key.startswith("bundle:")
                and old_key != bundle_key
            ):
                cache.pop(old_key)
        cache[bundle_key] = (before, bundle)
        family = bundle["continuous_reversal"]
        if family.get("family_sha256") != R.digest(
            {k: v for k, v in family.items() if k != "family_sha256"}
        ) or family.get("execution_code_sha256") != R.digest(
            family.get("contract_file_sha256")
        ):
            raise ValueError("native_family_contract_invalid")
        machine = family["machine_cells"][cell_key]["routes"][route]
        auxiliary = family["auxiliary_cells"][cell_key]["routes"][route]
        if machine.get("payload_sha256") != R.digest(machine["payload"]):
            raise ValueError("native_scope_payload_invalid")
        kernels = {
            k: v
            for k, v in family.get("contract_file_sha256", {}).items()
            if Path(k).name
            in {
                "continuous_reversal.py",
                "reversal_extended_state.py",
                "reversal_registered_state.py",
                "reversal_path_state.py",
            }
        }
        if kernels:
            result.update(
                cohort_contract=dict(
                    verified=True,
                    machine_payload_sha256=machine["payload_sha256"],
                    feature_kernel=kernels,
                    label_contract=family.get("label_contract"),
                ),
                scope_parent_machine_payload_sha256=machine["payload_sha256"],
                policy_scope=str(cell_key) + "|" + str(route),
            )
        if auxiliary.get("payload_sha256") == R.digest(auxiliary.get("payload")):
            result["auxiliary_binding"] = auxiliary.get("payload", {}).get("binding")
        if before != stat_receipt(p):
            raise Deferred("native_policy_source_changed")
        result["policy_source_ref"] = before
        result["machine_component_sha256"] = R.digest(family["machine_cells"])
        result["auxiliary_component_sha256"] = R.digest(family["auxiliary_cells"])
        result["family_sha256"] = family["family_sha256"]
        axes = machine.get("payload", {}).get("numeric_axis_contracts", [])
        definition_hashes = {
            b.get("definition_sha256")
            for b in machine.get("payload", {}).get("branches", [])
            if isinstance(b, dict)
        } - {None}
        if isinstance(axes, list):
            result["machine_axes"] = [
                dict(a, verified=True)
                for a in axes
                if isinstance(a, dict)
                and a.get("role") in {"baseline_prior", "bounded_tunable"}
                and a.get("axis") in R.FEATURES
                and a.get("operator") in {"lt", "le", "gt", "ge"}
                and a.get("unit")
                == {"volume_ratio_60s": "ratio", "drawdown_5m_pct": "pct"}.get(
                    a.get("axis")
                )
                and a.get("owner_definition_sha256") in definition_hashes
                and R.number(a.get("before")) is not None
            ]
    except (OSError, ValueError, TypeError, KeyError):
        result = {}
    cache[key] = result
    return result


def effective_auxiliary_contract(data_root, record, row, *, cache):
    """Bind the actual request through existing registry/overlay owners only."""

    ident = row.get("auxiliary_registry_sha256")
    if not row.get("auxiliary_registry_declared"):
        return
    row.update(
        auxiliary_binding=row.get("effective_auxiliary_binding")
        or {"registry_sha256": ident},
        effective_auxiliary_status="unverified",
        auxiliary_source_refs=[],
    )
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_registry as G

    # Missing dependencies remain row-local gaps; their appearance invalidates
    # the existing cursor through receipts_current, just like repaired files.
    try:
        if not re.fullmatch(r"[0-9a-f]{64}", str(ident)):
            raise ValueError("auxiliary_registry_identity_missing_or_invalid")
        path = G.directory(data_root) / (ident + ".json")
        row["auxiliary_source_refs"].append(
            stat_receipt(path)
            if path.exists()
            else dict(path=str(path), status="missing")
        )
        if (
            not row.get("cohort_contract")
            or row.get("request_binding_verified") is not True
        ):
            raise ValueError("auxiliary_native_scope_or_request_unverified")
        bundle = cache["bundle:" + row["native_receipt"]["bundle_sha256"]][1]
        assessment = record["source"]["assessment"]
        overlay_id = assessment.get("auxiliary_overlay_sha256")
        if overlay_id and not re.fullmatch(r"[0-9a-f]{64}", str(overlay_id)):
            raise ValueError("auxiliary_overlay_identity_invalid")
        path = (
            I.root(data_root) / "generations" / (overlay_id + ".json")
            if overlay_id
            else Path(data_root)
            / "runtime/mechanistic_entry_policy/sources"
            / (
                "reversal-"
                + bundle["continuous_reversal"]["auxiliary_report_sha256"]
                + ".json"
            )
        )
        row["auxiliary_source_refs"].append(
            stat_receipt(path)
            if path.exists()
            else dict(path=str(path), status="missing")
        )
        key = ("auxiliary_sources", bundle["bundle_sha256"], ident, overlay_id)
        proof = cache.get(key)
        if not proof or not receipts_current(proof[0]):
            value = G.load(data_root, ident)
            overlay = I.read(path) if overlay_id else None
            if overlay:
                I.validate_record(data_root, overlay, bundle)
                bindings = overlay["bindings"]
            else:
                bindings = I.inherited(data_root, bundle)
            sources = I.lineage_sources(data_root, bundle, overlay)
            refs = row["auxiliary_source_refs"] + [
                stat_receipt(s["path"]) for s in sources
            ]
            if overlay and overlay.get("code_hashes") != I.code_hashes():
                from src.engine.scalping import reversal_auxiliary_compatibility as C

                receipt = C.validate(
                    data_root, bundle, path, overlay.get("code_hashes"), I.code_hashes()
                )
                refs.extend(
                    stat_receipt(p)
                    for p in [
                        C.path(data_root, bundle, path, I.code_hashes()),
                        receipt["evidence_path"],
                        *[r["path"] for r in receipt["frozen_readers"]],
                    ]
                )
            current = value
            while True:
                refs.append(
                    stat_receipt(
                        G.directory(data_root) / (current["registry_sha256"] + ".json")
                    )
                )
                if current.get("research_registry_sha256"):
                    refs.append(
                        stat_receipt(
                            G.directory(data_root)
                            / (current["research_registry_sha256"] + ".json")
                        )
                    )
                parent = current.get("production_parent_registry_sha256")
                if not parent:
                    break
                current = G.load(data_root, parent)
            if not receipts_current(refs):
                raise ValueError("auxiliary_source_changed_during_audit")
            proof = (refs, value, G.binding(value), bindings, overlay)
            cache[key] = proof
        refs, value, binding, bindings, overlay = proof
        # Cache immutable provenance only. Every row still proves its request,
        # dynamic schema/wire, scope and original confirmation-time activation.
        row["auxiliary_source_refs"] = refs
        request = record["source"]["auxiliary_request"]
        if (
            request["prompt"] != value["prompt"]
            or assessment.get("auxiliary_binding") != binding
        ):
            raise ValueError("auxiliary_observation_registry_changed")
        envelope = G.envelope(request["input"], value)
        if request["response_schema"] != envelope["logical_schema"]:
            raise ValueError("auxiliary_observation_response_schema_changed")
        if value["schema"] == G.SCHEMA_V2 and (
            assessment.get("auxiliary_wire_contract") != envelope["contract"]
            or assessment.get("auxiliary_wire_hashes") != envelope["hashes"]
        ):
            raise ValueError("auxiliary_observation_wire_changed")
        scope = str(row["cell_key"]) + "|" + str(row["event"]["venue"])
        if bindings.get(scope) != ident:
            raise ValueError("auxiliary_observation_scope_changed")
        if (
            overlay
            and datetime.fromisoformat(overlay["effective_from"]).timestamp()
            > row["event"]["epoch"]
        ):
            raise ValueError("auxiliary_observation_before_effective_time")
        if not receipts_current(refs):
            raise ValueError("auxiliary_source_changed_during_audit")
        row.update(auxiliary_binding=binding, effective_auxiliary_status="verified")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        reason = str(exc).split(":", 1)[0][:160]
        if isinstance(exc, OSError) and exc.filename:
            path = Path(exc.filename)
            row["auxiliary_source_refs"].append(
                stat_receipt(path)
                if path.exists()
                else dict(path=str(path), status="missing")
            )
            if isinstance(exc, FileNotFoundError):
                reason = (
                    "historical_reader_compatibility_missing"
                    if path.is_relative_to(I.root(data_root) / "compatibility")
                    else (
                        "auxiliary_registry_source_missing"
                        if path.is_relative_to(G.directory(data_root))
                        else "auxiliary_dependency_missing"
                    )
                )
        row["effective_auxiliary_reason"] = reason


def native_records(source, source_date, data_root, start=0, *, stop_at):
    """Stream compact validated observations; never copy AI bodies to research."""
    path = Path(source["path"])
    compressed = path.suffix == ".gz"
    if compressed and start:
        raise ValueError("compressed_resume_unavailable")
    cache, output, gaps, scanned = {}, [], CounterDict(), 0
    decoded_digest = hashlib.sha256()
    with source_handle(path) as (handle, physical):
        if start:
            handle.seek(start)
        while True:
            if time.monotonic() >= stop_at:
                raise Deferred("native_index_wall_budget")
            offset = handle.tell()
            raw = handle.readline(MAX_LINE + 1)
            if not raw:
                proof = (
                    dict(
                        decoded_sha256=decoded_digest.hexdigest(),
                        decoded_bytes=handle.tell(),
                        physical_sha256=physical.digest.hexdigest() if physical else decoded_digest.hexdigest(),
                    )
                    if compressed or start == 0
                    else None
                )
                yield output, handle.tell(), True, dict(gaps), proof
                return
            if len(raw) > MAX_LINE:
                raise ValueError("native_row_size_limit")
            if not raw.endswith(b"\n"):
                if compressed:
                    raise ValueError("compressed_incomplete_source_tail")
                yield output, offset, False, dict(gaps), None
                return
            scanned += len(raw)
            decoded_digest.update(raw)
            try:
                record = strict_json(raw)
                row, reason = R.project_native_observation(record, source_date)
                if row:
                    native = row["native_receipt"]
                    scope = scope_contract(
                        data_root,
                        native.get("bundle_sha256"),
                        row.get("cell_key"),
                        (row.get("event") or {}).get("venue"),
                        cache=cache,
                    )
                    if (
                        scope.get("machine_component_sha256")
                        == native.get("machine_component_sha256")
                        and scope.get("family_sha256") == native.get("family_sha256")
                        and scope.get("auxiliary_component_sha256")
                        == native.get("auxiliary_component_sha256")
                    ):
                        row.update(
                            {
                                k: v
                                for k, v in scope.items()
                                if k
                                not in {
                                    "machine_component_sha256",
                                    "auxiliary_component_sha256",
                                    "family_sha256",
                                }
                            }
                        )
                    effective_auxiliary_contract(data_root, record, row, cache=cache)
                    row["source_ref"] = dict(
                        path=str(path),
                        offset=offset,
                        end_offset=handle.tell(),
                        row_sha256=hashlib.sha256(raw).hexdigest(),
                    )
                    output.append(row)
                else:
                    gaps.add(reason)
            except (ValueError, TypeError, AttributeError):
                gaps.add("malformed_native_observation")
            if len(output) >= CHUNK_ROWS or scanned >= CHUNK_BYTES:
                yield output, handle.tell(), False, dict(gaps), None
                output, gaps, scanned = [], CounterDict(), 0


def index_native_rows(db, rows, source):
    for row in rows:
        # The cursor owns the deduplicated dependency receipts. Repeating the
        # same overlay ancestry in every indexed/projected row is unbounded.
        key, raw = native_key(row), json.dumps(
            R.seal({k: v for k, v in row.items() if k != "auxiliary_source_refs"}),
            sort_keys=True,
        )
        old = db.execute("SELECT row FROM native WHERE key=?", (key,)).fetchone()
        if old:
            if json.loads(old[0]).get("observation_sha256") != row.get(
                "observation_sha256"
            ):
                db.execute("UPDATE native SET conflict=1 WHERE key=?", (key,))
        else:
            db.execute("INSERT INTO native VALUES(?,?,?,0)", (key, source, raw))
    db.commit()


def bind_trace_native(row, db):
    found = db.execute(
        "SELECT row FROM native WHERE key=? AND conflict=0", (native_key(row),)
    ).fetchone()
    if found:
        observation = json.loads(found[0])
        check_seal(observation)
        if native_key(observation) != native_key(row):
            raise ValueError("native_index_binding_changed")
        R.bind_native(row, observation)
    else:
        row["native_binding_status"] = "exact_native_binding_missing"


def gzip_trace_records(source, source_date, listing, *, stop_at):
    output, gaps, scanned = [], CounterDict(), 0
    decoded_digest = hashlib.sha256()
    with source_handle(source["path"]) as (handle, physical):
        while True:
            if time.monotonic() >= stop_at:
                raise Deferred("compressed_trace_wall_budget")
            offset = handle.tell()
            raw = handle.readline(MAX_LINE + 1)
            if not raw:
                yield output, handle.tell(), True, dict(gaps), dict(
                    decoded_sha256=decoded_digest.hexdigest(),
                    decoded_bytes=handle.tell(),
                    physical_sha256=physical.digest.hexdigest(),
                )
                return
            if len(raw) > MAX_LINE or not raw.endswith(b"\n"):
                raise ValueError("compressed_trace_row_invalid")
            scanned += len(raw)
            decoded_digest.update(raw)
            try:
                record = strict_json(raw)
                row, reason = R.project_trace(
                    record, source_date, listing(record.get("stock_code"))
                )
            except (ValueError, TypeError, AttributeError):
                row, reason = None, "malformed_trace_row"
            if row:
                row["source_ref"] = dict(
                    path=source["path"],
                    offset=offset,
                    end_offset=handle.tell(),
                    row_sha256=hashlib.sha256(raw).hexdigest(),
                    compressed=True,
                )
                output.append(row)
            else:
                gaps.add(reason or "excluded_trace_row")
            if len(output) >= CHUNK_ROWS or scanned >= CHUNK_BYTES:
                yield output, handle.tell(), False, dict(gaps), None
                output, gaps, scanned = [], CounterDict(), 0


def _index_label(db, row):
    if row.get("decision_origin") != "confirmation_replay" or row.get("auxiliary_hash"):
        return
    raw = json.dumps(row, sort_keys=True)
    keys = {
        row["opportunity_id"],
        row.get("canonical_alias", row["opportunity_id"]),
    }
    exact = exact_event_key(row)
    if exact:
        keys.add(exact)
    for key in keys:
        old = db.execute("SELECT row FROM labels WHERE id=?", (key,)).fetchone()
        if old and old[0] != raw:
            db.execute("UPDATE labels SET conflict=1 WHERE id=?", (key,))
        elif not old:
            db.execute("INSERT INTO labels VALUES(?,?,0)", (key, raw))


def bind_natural_label(row, labels):
    if row.get("identity_grade") != "canonical" or row.get("entry_ask") is None:
        return
    exact = exact_event_key(row)
    native = (
        labels.execute(
            "SELECT row,conflict FROM labels WHERE id=?", ("native-label:" + exact,)
        ).fetchone()
        if exact
        else None
    )
    keys = {row["opportunity_id"], row.get("canonical_alias"), exact} - {None}
    found_rows = (
        [native]
        if native
        else [
            labels.execute(
                "SELECT row,conflict FROM labels WHERE id=?", (k,)
            ).fetchone()
            for k in keys
        ]
    )
    if any(r and r[1] for r in found_rows):
        row["outcome_reason"] = "exact_label_binding_conflict"
        return
    choices = {r[0] for r in found_rows if r}
    if len(choices) != 1:
        return
    found = (next(iter(choices)),)
    if not found:
        return
    label = json.loads(found[0])
    if (
        row.get("machine_confirmed_at") == label.get("machine_confirmed_at")
        and row.get("event_id") == label.get("event_id")
        and row["entry_ask"] == label["entry_ask"]
        and row["symbol"] == label["symbol"]
        and all(row.get(k) == label.get(k) for k in ("source_date", "session", "route"))
        and all(
            row.get(k) is None or row.get(k) == label.get(k)
            for k in ("source_item", "native_epoch", "native_sequence")
        )
    ):
        row.update(
            outcome=label["outcome"],
            outcome_reason=label.get("outcome_reason"),
            label_binding_ref=label["source_ref"],
            label_binding="exact_event_time_actual_ask",
        )


def exact_event_key(row):
    fields = (
        "source_date",
        "symbol",
        "source_item",
        "session",
        "route",
        "native_epoch",
        "native_sequence",
        "event_id",
        "machine_confirmed_at",
        "entry_ask",
    )
    if any(row.get(k) is None for k in fields):
        return None
    return "exact-event:" + R.digest([row[k] for k in fields])


def decode_stored_response(req, result, label, data_root=None):
    inp = req["candidate_input"]
    candidate = req["candidate"]
    arm = req["micro_reversion_replay_arm"]
    response = result.get("candidate_response")
    base_prompt = candidate.get("system_prompt")
    codec = None
    if candidate.get("compact_runtime_contract"):
        from src.engine.scalping import reversal_auxiliary_wire as codec
    elif candidate.get("compact_wire_contract"):
        from src.engine.scalping import reversal_auxiliary_research_wire as codec
    object_receipts = []
    if codec:
        if data_root is None:
            raise ValueError("compact_logical_snapshot_unavailable")
        store = ReadObjects(data_root)
        try:
            snapshot = store.get(label["source_ref"]["snapshot_object"])
            from src.engine.scalping.reversal_auxiliary_registry import projector

            logical = projector(inp["schema"]).production_request(
                snapshot[1], arm, event=snapshot[0]
            )[0]
            if (
                codec.encode(logical)[0] != inp
                or not isinstance(base_prompt, str)
                or not base_prompt.endswith(codec.SUFFIX)
            ):
                raise ValueError("compact_original_logical_binding_invalid")
            response = codec.response(result, req, logical, arm)
            inp = logical
            base_prompt = base_prompt[: -len(codec.SUFFIX)]
            object_receipts = list(store.receipts.values())
        finally:
            store.close()
    if not isinstance(base_prompt, str) or not base_prompt:
        raise ValueError("actual_prompt_binding_unavailable")
    binding = dict(
        input_version=inp.get("schema"),
        validator_version=inp.get("schema"),
        arm=arm,
        prompt_version=candidate.get("prompt_version"),
        prompt_sha256=R.digest(base_prompt),
        response_schema_version=(response or {}).get("schema"),
    )
    version = binding["prompt_version"] or ""
    if version.startswith("main_auxiliary_prompt_registry_"):
        ident = version.rsplit(":", 1)[-1]
        if len(ident) != 64 or any(c not in "0123456789abcdef" for c in ident):
            raise ValueError("stored_registry_identity_invalid")
        binding["registry_sha256"] = ident
    return inp, response, binding, object_receipts


def stored_auxiliary_records(source, source_date, labels, start=0, *, data_root=None):
    from src.engine.scalping.reversal_operating_evaluation import validate_response

    output, gaps, scanned = [], CounterDict(), 0
    opener = gzip.open if str(source["path"]).endswith(".gz") else open
    with opener(source["path"], "rb") as f:
        f.seek(start)
        while scanned < CHUNK_BYTES and len(output) < CHUNK_ROWS:
            offset = f.tell()
            raw = f.readline(MAX_LINE + 1)
            if not raw:
                return output, f.tell(), True, dict(gaps)
            if len(raw) > MAX_LINE or not raw.endswith(b"\n"):
                raise ValueError("stored_auxiliary_row_size_or_tail_invalid")
            scanned += len(raw)
            try:
                entry = json.loads(raw)
                req = entry["request"]
                inp = req["candidate_input"]
                ctx = inp.get("common_context", {})
                arm = req["micro_reversion_replay_arm"]
                result = entry["result"]
                response = result.get("candidate_response")
                found = labels.execute(
                    "SELECT row FROM labels WHERE id=? AND conflict=0",
                    (ctx.get("opportunity_key"),),
                ).fetchone()
                if not found:
                    raise ValueError("exact_replay_label_binding_missing")
                row = json.loads(found[0])
                at = R.timestamp(ctx.get("as_of"))
                inp, response, binding, object_receipts = decode_stored_response(
                    req, result, row, data_root
                )
                if (
                    not at
                    or at.isoformat() != row["machine_confirmed_at"]
                    or ctx.get("symbol") != row["symbol"]
                    or R.number(ctx.get("entry_ask")) != row["entry_ask"]
                    or ctx.get("venue") != row["route"]
                    or ctx.get("objective")
                    != dict(
                        net_target_pct=0.4,
                        net_soft_stop_pct=-3.0,
                        cost_rate=0.0023,
                        horizon_seconds=1800,
                    )
                    or entry.get("transport_invoked") is not True
                    or entry.get("validation_errors")
                    or not result.get("provider_provenance", {}).get("response_id")
                    or req.get("candidate_input_sha256")
                    != R.digest(req["candidate_input"])
                    or entry.get("request_identity") != req.get("paired_replay_id")
                    or any(
                        req.get(k) != v
                        for k, v in R.AUTH.items()
                        if k != "decision_authority"
                    )
                    or validate_response(
                        response,
                        inp,
                        arm=arm,
                        phase=inp.get("observation_phase", {}).get("stage"),
                    )
                ):
                    raise ValueError("stored_auxiliary_binding_or_validation_invalid")
                if not binding["prompt_version"] or not req["candidate"].get(
                    "response_schema_sha256"
                ):
                    raise ValueError("stored_auxiliary_version_missing")
                row.update(
                    auxiliary_hash=R.digest(binding),
                    auxiliary_version=binding["prompt_version"],
                    auxiliary_binding=binding,
                    auxiliary_verdict=response["risk_verdict"],
                    response_origin="stored_offline_actual",
                    research_overlay_disposition="unadjusted",
                    classification_time_basis="confirmation_replay_not_natural_response",
                    source_ref=dict(
                        export_path=source["path"],
                        export_sha256=source["sha256"],
                        offset=offset,
                        row_sha256=hashlib.sha256(raw).hexdigest(),
                        request_id=entry.get("request_identity"),
                        response_id=result["provider_provenance"]["response_id"],
                        object_receipts=object_receipts,
                    ),
                )
                output.append(row)
            except (ValueError, TypeError, KeyError, AttributeError):
                gaps.add("stored_auxiliary_unmatched_or_invalid")
        return output, f.tell(), False, dict(gaps)


def trace_records(source, source_date, listing, start=0):
    """Read complete lines to a fixed stat cutoff; do not load the whole file."""
    path = Path(source["path"])
    with path.open("rb") as f:
        f.seek(start)
        output, gaps, scanned = [], CounterDict(), 0
        range_digest = hashlib.sha256()
        while (
            f.tell() < source["size"]
            and scanned < CHUNK_BYTES
            and len(output) < CHUNK_ROWS
        ):
            offset = f.tell()
            raw = f.readline(MAX_LINE + 1)
            if len(raw) > MAX_LINE:
                raise ValueError("trace_row_size_limit")
            if not raw.endswith(b"\n") or f.tell() > source["size"]:
                f.seek(offset)
                break
            scanned += len(raw)
            range_digest.update(raw)
            try:
                record = strict_json(raw)
                row, reason = R.project_trace(
                    record, source_date, listing(record.get("stock_code"))
                )
            except (ValueError, TypeError, AttributeError):
                row, reason = None, "malformed_trace_row"
            if row:
                row["source_ref"] = dict(
                    path=source["path"],
                    offset=offset,
                    end_offset=f.tell(),
                    row_sha256=hashlib.sha256(raw).hexdigest(),
                )
                output.append(row)
            else:
                gaps.add(reason or "excluded_trace_row")
        offset = f.tell()
        return (
            output,
            offset,
            offset == source["size"],
            dict(gaps),
            dict(start=start, end=offset, sha256=range_digest.hexdigest()),
        )


def write_partition(root, rows):
    value = R.seal(dict(schema=R.VERSION + ":projection", rows=rows, **R.AUTH))
    p = root / "objects" / (value["artifact_content_sha256"] + ".json")
    atomic(p, value, immutable=True)
    return dict(
        path=str(p),
        sha256=value["artifact_content_sha256"],
        rows=len(rows),
        stat=stat_receipt(p),
    )


def promote_compressed_partition(root, part):
    """Publish already-sealed bytes only after the gzip EOF/CRC succeeded."""
    path = Path(root) / "objects" / (part["sha256"] + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(part["path"], path)
    except FileExistsError:
        if Path(part["path"]).read_bytes() != path.read_bytes():
            raise ValueError("research_immutable_artifact_changed")
    with path.open("rb") as handle:
        os.fsync(handle.fileno())
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    Path(part["path"]).unlink()
    return dict(part, path=str(path), stat=stat_receipt(path))


def projection_rows(parts):
    for rec in parts:
        p = check_seal(read_json(rec["path"]))
        if p["artifact_content_sha256"] != rec["sha256"]:
            raise ValueError("projection_reference_changed")
        yield from p["rows"]


def process_date(data_root, source_date, *, stop_at, clock=time.monotonic):
    """Commit immutable partitions before the atomic cursor manifest."""
    root = namespace(data_root)
    path = root / source_date / "cursor.json"
    prior = read_json(path, {})
    baseline = read_json(
        Path(data_root) / "source_quality/clean_baseline_policy.json", {}
    )
    start_date = max(
        "2026-06-05",
        baseline.get("clean_tuning_baseline_date", "2026-06-05"),
        baseline.get("policy_refresh_start_date", "2026-09-29"),
    )
    if source_date < start_date:
        raise ValueError("archive_date_forbidden_for_research")
    obs, obs_receipts, obs_gaps = observations(
        data_root,
        source_date,
        observer_snapshot=prior.get("source_descriptor", {}).get("observer_snapshot"),
    )
    obs = R.ObservationIndex(obs)
    listing, listing_receipt = listing_lookup(data_root, source_date)
    sources = source_plan(data_root, source_date)
    if not sources:
        obs_gaps["retained_decision_sources_unavailable"] = 1
    descriptor = dict(
        source_date=source_date,
        sources=sources,
        observations=obs_receipts,
        observer_snapshot=next(
            (
                r
                for r in obs_receipts
                if Path(r["path"]).parent == (root / "observer_receipts").resolve()
            ),
            None,
        ),
        listing=listing_receipt,
        dependencies=dependencies(data_root, source_date),
        code=code_hash(),
        version=R.REPAIR_VERSION,
        label_contract=R.LABEL,
    )
    old_descriptor = prior.get("source_descriptor", {})
    if {
        k: v for k, v in old_descriptor.items() if k != "object_source_state"
    } == descriptor:
        derived_receipts = prior.get("shared_object_receipts", []) + prior.get(
            "source_dependency_receipts", []
        )
        if receipts_current(derived_receipts):
            descriptor = old_descriptor
        else:
            states = []
            for r in derived_receipts:
                try:
                    states.append(stat_receipt(r["path"]))
                except FileNotFoundError:
                    states.append(dict(path=r["path"], status="missing"))
            descriptor["object_source_state"] = states
    generation = R.digest(descriptor)
    cursor = prior
    if cursor.get("generation") != generation:
        cursor = rebind_compressed_sources(root, prior, descriptor, stop_at=stop_at) or dict(
            schema=R.VERSION + ":cursor",
            source_date=source_date,
            generation=generation,
            source_descriptor=descriptor,
            source_index=0,
            offset=0,
            partitions=[],
            gaps=obs_gaps,
            status="in_progress",
            **R.AUTH,
        )
    if cursor.get("status") in {
        "completed",
        "valid_empty",
        "completed_with_source_gaps",
    }:
        if not cursor_current(data_root, cursor):
            raise ValueError("published_projection_changed")
        check_seal(read_json(cursor["daily_path"]))
        check_seal(read_json(cursor["terminal_path"]))
        return dict(
            status=cursor["status"],
            source_date=source_date,
            generation=generation,
            delta=0,
        )
    streams = {}

    def abandon_compressed(reason, *, advance=True):
        ticket = cursor.pop("compressed_in_progress", None)
        if not ticket:
            return
        index = ticket.get("source_index")
        start = ticket.get("partition_start")
        if (
            type(index) is not int
            or not 0 <= index < len(sources)
            or ticket.get("source_path") != sources[index]["path"]
            or type(start) is not int
            or not 0 <= start <= len(cursor["partitions"])
        ):
            raise ValueError("compressed_checkpoint_binding_invalid")
        cursor["partitions"] = cursor["partitions"][: ticket["partition_start"]]
        staging = root / "compressed_staging" / generation / str(ticket["source_index"])
        if staging.is_dir() and not staging.is_symlink():
            # This generation/source has no committed terminal. No shared
            # content-addressed object or upstream source is removed here.
            shutil.rmtree(staging)
        cursor["source_census"] = ticket["source_census"]
        cursor["source_projection_census"] = ticket.get("source_projection_census", {})
        cursor["native_indexed_rows"] = ticket.get("native_indexed_rows", 0)
        cursor["source_dependency_receipts"] = ticket.get(
            "source_dependency_receipts", []
        )
        cursor["gaps"] = ticket["gaps"]
        if advance:
            cursor["gaps"][reason] = cursor["gaps"].get(reason, 0) + 1
        db = native_index(root, cursor)
        try:
            db.execute("DELETE FROM native WHERE source=?", (ticket["source_path"],))
            db.commit()
        finally:
            db.close()
        cursor.update(source_index=ticket["source_index"] + int(advance), offset=0)
        atomic(path, cursor)

    if cursor.get("compressed_in_progress"):
        abandon_compressed(
            "compressed_resume_unavailable",
            advance=not cursor["compressed_in_progress"].get("label_dependency_pending"),
        )
    while cursor["source_index"] < len(sources):
        if clock() >= stop_at:
            for stream in streams.values():
                stream.close()
            abandon_compressed("compressed_resume_unavailable")
            raise Deferred("chunk_wall_budget")
        source = sources[cursor["source_index"]]
        range_proof = None
        projection_commit_started = False
        try:
            if source.get("compressed") and not cursor.get("compressed_in_progress"):
                cursor["compressed_in_progress"] = dict(
                    source_index=cursor["source_index"],
                    source_path=source["path"],
                    partition_start=len(cursor["partitions"]),
                    source_census=dict(cursor.get("source_census", {})),
                    source_projection_census=dict(
                        cursor.get("source_projection_census", {})
                    ),
                    gaps=dict(cursor["gaps"]),
                    native_indexed_rows=cursor.get("native_indexed_rows", 0),
                    source_dependency_receipts=list(
                        cursor.get("source_dependency_receipts", [])
                    ),
                )
                atomic(path, cursor)
            verify_stream_aliases(root, source, stop_at=stop_at)
            if source["kind"] == "natural_trace":
                if source.get("compressed"):
                    if cursor["source_index"] not in streams:
                        streams[cursor["source_index"]] = gzip_trace_records(
                            source, source_date, listing, stop_at=stop_at
                        )
                    rows, offset, done, gaps, range_proof = next(
                        streams[cursor["source_index"]]
                    )
                else:
                    rows, offset, done, gaps, range_proof = trace_records(
                        source, source_date, listing, cursor["offset"]
                    )
                if (
                    range_proof
                    and not source.get("compressed")
                    and range_proof["end"] > range_proof["start"]
                ):
                    cursor.setdefault("source_ranges", []).append(
                        dict(path=source["path"], **range_proof)
                    )
                if cursor.get("compressed_in_progress"):
                    cursor["compressed_in_progress"]["label_dependency_pending"] = True
                    atomic(path, cursor)
                labels = label_index(root, cursor, data_root=data_root, stop_at=stop_at)
                if cursor.get("compressed_in_progress"):
                    cursor["compressed_in_progress"].pop("label_dependency_pending", None)
                natives = native_index(root, cursor)
                try:
                    for row in rows:
                        bind_trace_native(row, natives)
                        bind_natural_label(row, labels)
                finally:
                    labels.close()
                    natives.close()
            elif source["kind"] == "native_observations":
                if cursor["source_index"] not in streams:
                    streams[cursor["source_index"]] = native_records(
                        source,
                        source_date,
                        data_root,
                        cursor["offset"],
                        stop_at=stop_at,
                    )
                native_rows, offset, done, gaps, range_proof = next(
                    streams[cursor["source_index"]]
                )
                natives = native_index(root, cursor)
                try:
                    index_native_rows(natives, native_rows, source["path"])
                finally:
                    natives.close()
                rows = []
                cursor["native_indexed_rows"] = cursor.get(
                    "native_indexed_rows", 0
                ) + len(native_rows)
                dependencies_by_path = {
                    r["path"]: r for r in cursor.get("source_dependency_receipts", [])
                }
                for r in native_rows:
                    if r.get("policy_source_ref"):
                        dependencies_by_path[r["policy_source_ref"]["path"]] = r[
                            "policy_source_ref"
                        ]
                    for ref in r.get("auxiliary_source_refs", []):
                        dependencies_by_path[ref["path"]] = ref
                cursor["source_dependency_receipts"] = list(
                    dependencies_by_path.values()
                )
            elif source["kind"] == "stored_auxiliary":
                verify_file(root, source["path"], source["sha256"], stop_at=stop_at)
                labels = label_index(root, cursor)
                try:
                    rows, offset, done, gaps = stored_auxiliary_records(
                        source,
                        source_date,
                        labels,
                        cursor["offset"],
                        data_root=data_root,
                    )
                finally:
                    labels.close()
            elif source["kind"] == "operating_comparison":
                rows, offset, done, gaps = next(
                    replay_records(
                        data_root,
                        source_date,
                        source,
                        listing,
                        cursor["offset"],
                        stop_at=stop_at,
                    )
                )
            else:
                raise ValueError("upstream_evidence_unavailable")
            if any(
                stat_receipt(source["path"])[k] != source[k]
                for k in stat_receipt(source["path"])
            ):
                raise Deferred("source_cutoff_changed")
            projection_commit_started = True
            cursor.setdefault("source_census", {}).setdefault(source["kind"], 0)
            cursor["source_census"][source["kind"]] += (
                len(native_rows)
                if source["kind"] == "native_observations"
                else len(rows)
            )
            cursor.setdefault("source_projection_census", {}).setdefault(
                source["kind"], 0
            )
            cursor["source_projection_census"][source["kind"]] += len(rows)
            object_receipts = {
                r["path"]: r for r in cursor.get("shared_object_receipts", [])
            }
            for row in rows:
                for receipt in row.get("source_ref", {}).get("object_receipts", []):
                    object_receipts[receipt["path"]] = receipt
            dependency_receipts = {
                r["path"]: r for r in cursor.get("source_dependency_receipts", [])
            }
            for row in rows:
                if row.get("native_policy_ref"):
                    dependency_receipts[row["native_policy_ref"]["path"]] = row[
                        "native_policy_ref"
                    ]
            cursor["source_dependency_receipts"] = list(dependency_receipts.values())
            cursor["shared_object_receipts"] = list(object_receipts.values())
            rows = [R.attach_joins(row, obs) for row in rows]
            if source["kind"] != "native_observations" and (
                done or offset != cursor["offset"]
            ):
                partition_root = (
                    (
                        root
                        / "compressed_staging"
                        / generation
                        / str(cursor["source_index"])
                    )
                    if source.get("compressed")
                    else root
                )
                part = write_partition(partition_root, rows)
                cursor["partitions"].append(part)
            for key, n in gaps.items():
                cursor["gaps"][key] = cursor["gaps"].get(key, 0) + n
            if done:
                if range_proof and "decoded_sha256" in range_proof:
                    cursor.setdefault("stream_receipts", []).append(
                        dict(path=source["path"], **range_proof)
                    )
                if source.get("compressed") and range_proof:
                    start = cursor["compressed_in_progress"]["partition_start"]
                    cursor["partitions"][start:] = [
                        promote_compressed_partition(root, part)
                        for part in cursor["partitions"][start:]
                    ]
                stream = streams.pop(cursor["source_index"], None)
                if stream:
                    stream.close()
                cursor.pop("compressed_in_progress", None)
                cursor.update(source_index=cursor["source_index"] + 1, offset=0)
            else:
                if offset == cursor["offset"]:
                    cursor["gaps"]["incomplete_tail"] = 1
                    atomic(path, cursor)
                    raise Deferred("incomplete_source_tail")
                cursor["offset"] = offset
            atomic(path, cursor)
        except Deferred as exc:
            for stream in streams.values():
                stream.close()
            if cursor.get("compressed_in_progress"):
                abandon_compressed(
                    "compressed_resume_unavailable",
                    advance=not str(exc).startswith("native_label_"),
                )
            raise
        except (
            FileNotFoundError,
            ValueError,
            EOFError,
            OSError,
            zlib.error,
            sqlite3.OperationalError,
        ) as exc:
            if projection_commit_started:
                for stream in streams.values():
                    stream.close()
                # Destination write/commit failures are not upstream defects.
                # Retry from the last durable cursor; do not advance the input.
                raise Deferred("projection_commit_failed") from exc
            if cursor.get("compressed_in_progress"):
                for stream in streams.values():
                    stream.close()
                streams.clear()
                abandon_compressed("compressed_source_contract_invalid")
                continue
            if isinstance(exc, sqlite3.OperationalError):
                raise Deferred("shared_source_unavailable_or_busy") from None
            cursor["gaps"]["source_contract_invalid_or_unavailable"] = (
                cursor["gaps"].get("source_contract_invalid_or_unavailable", 0) + 1
            )
            cursor.update(source_index=cursor["source_index"] + 1, offset=0)
            atomic(path, cursor)
    # The entire frozen cutoff must still exist unchanged before publication.
    if not cursor_current(data_root, cursor):
        raise Deferred("source_generation_changed_before_seal")
    aggregator = R.Aggregator(scratch_root=root / "scratch")
    try:
        for row in projection_rows(cursor["partitions"]):
            if clock() >= stop_at:
                raise Deferred("aggregation_wall_budget")
            aggregator.add(row)
        daily = aggregator.daily(source_date)
    finally:
        aggregator.close()
    daily = R.seal(
        dict(
            daily,
            source_census=cursor.get("source_census", {}),
            source_projection_census=cursor.get("source_projection_census", {}),
            native_indexed_rows=cursor.get("native_indexed_rows", 0),
            input_exclusions=cursor["gaps"],
            analysis_coverage=coverage(daily),
            population="retained_natural_trace_and_confirmation_replay_cohorts_only",
            stored_response_subset_is_not_original_population=True,
        )
    )
    status = (
        "completed_with_source_gaps"
        if cursor["gaps"]
        or not obs
        or not sources
        or not listing_receipt
        or listing_receipt.get("status") == "source_invalid"
        or any(s["counts"].get("join_U", 0) for s in daily["scopes"].values())
        else ("completed" if daily["census"].get("projected_rows") else "valid_empty")
    )
    output = root / source_date / generation
    manifest = R.seal(
        dict(
            schema=R.VERSION + ":source_manifest",
            **descriptor,
            partitions=cursor["partitions"],
            shared_object_receipts=cursor.get("shared_object_receipts", []),
            source_dependency_receipts=cursor.get("source_dependency_receipts", []),
            source_ranges=cursor.get("source_ranges", []),
            stream_receipts=cursor.get("stream_receipts", []),
            representation_parent=cursor.get("representation_parent"),
            **R.AUTH,
        )
    )
    atomic(output / "source_manifest.json", manifest, immutable=True)
    atomic(output / "daily.json", daily, immutable=True)
    markdown = (
        "# Main market weakness advisory research\n\nSource date: "
        + source_date
        + "\n\nNo runtime or order effect. W/F/U are counterfactual price-path outcomes.\n\n```json\n"
        + json.dumps(
            dict(
                source_census=daily["source_census"],
                source_projection_census=daily["source_projection_census"],
                native_indexed_rows=daily["native_indexed_rows"],
                analysis_coverage=daily["analysis_coverage"],
                census=daily["census"],
                scopes=daily["scopes"],
            ),
            ensure_ascii=True,
            indent=2,
        )
        + "\n```\n"
    )
    atomic_text(output / "daily.md", markdown)
    terminal = R.seal(
        dict(
            schema=R.VERSION + ":terminal",
            source_date=source_date,
            generation=generation,
            status=status,
            code_sha256=descriptor["code"],
            source_manifest_sha256=manifest["artifact_content_sha256"],
            daily_sha256=daily["artifact_content_sha256"],
            gaps=cursor["gaps"],
            analysis_coverage=daily["analysis_coverage"],
            source_census=daily["source_census"],
            source_projection_census=daily["source_projection_census"],
            native_indexed_rows=daily["native_indexed_rows"],
            recommendation_status="not_evaluated_until_cumulative",
            **R.AUTH,
        )
    )
    atomic(output / "terminal.json", terminal, immutable=True)
    # One replace commits generation + cursor + published references together.
    cursor.update(
        status=status,
        manifest_path=str(output / "source_manifest.json"),
        daily_path=str(output / "daily.json"),
        terminal_path=str(output / "terminal.json"),
    )
    atomic(path, cursor)
    atomic(
        root / source_date / "phase.json",
        R.seal(
            dict(
                source_date=source_date,
                daily_generation=generation,
                phase="cumulative_pending",
                code_sha256=code_hash(),
                **R.AUTH,
            )
        ),
    )
    return dict(status=status, source_date=source_date, generation=generation, delta=1)


def coverage(daily):
    counts = CounterDict()
    for summary in daily.get("scopes", {}).values():
        for key, value in summary["counts"].items():
            if key == "rows" or key.startswith(
                ("join_", "outcome_", "native_binding_", "auxiliary_binding_")
            ):
                counts.add(key, value)
    return dict(counts)


def unfinished_phase(data_root, day, cursor):
    phase = read_json(namespace(data_root) / day / "phase.json", {})
    if not phase:
        return True  # A crash between the daily commit and phase commit is resumable.
    check_seal(phase)
    return (
        phase.get("code_sha256") != code_hash()
        or phase.get("daily_generation") != cursor.get("generation")
        or phase.get("phase") != "completed"
    )


def phase_receipt(data_root, day, daily_generation, phase, **refs):
    atomic(
        namespace(data_root) / day / "phase.json",
        R.seal(
            dict(
                source_date=day,
                daily_generation=daily_generation,
                phase=phase,
                code_sha256=code_hash(),
                **refs,
                **R.AUTH,
            )
        ),
    )


def research_source_scope(data_root, *, through_date=None, from_date=None):
    """Bound discovery, pending and currentness to the same closed source dates."""
    config = read_json(namespace(data_root) / "installation.json", {})
    if config:
        check_seal(config)
    baseline = read_json(
        Path(data_root) / "source_quality/clean_baseline_policy.json", {}
    )
    start = max(
        "2026-06-05",
        baseline.get("clean_tuning_baseline_date", "2026-06-05"),
        baseline.get("policy_refresh_start_date", "2026-09-29"),
        config.get("evidence_start_date", "2026-09-29"),
    )
    configured_start = start
    through = through_date or datetime.now(R.KST).date().isoformat()
    if from_date is not None:
        date.fromisoformat(from_date)
        start = max(start, from_date)
    date.fromisoformat(start)
    date.fromisoformat(through)
    if start > through:
        raise ValueError("research_source_range_invalid")
    result = dict(
        evidence_start_date=start,
        through_date=through,
        source_dates=[
            d
            for d in discover_dates(data_root, dict(evidence_start_date=start))
            if start <= d <= through
        ],
    )
    if from_date is not None:
        result.update(
            recovery_from_date=from_date,
            configured_evidence_start_date=configured_start,
        )
    return result


def source_cursor_states(root, source_dates):
    """Include discovered dates that have never started, without stream reads."""
    states = []
    for day in source_dates:
        cursor = read_json(root / day / "cursor.json", {})
        states.append(
            dict(
                source_date=day,
                generation=cursor.get("generation"),
                status=cursor.get("status", "not_started"),
                code=cursor.get("source_descriptor", {}).get("code"),
            )
        )
    return states


def cumulative(
    data_root, *, stop_at, clock=time.monotonic, through_date=None, from_date=None
):
    root = namespace(data_root)
    source_scope = research_source_scope(
        data_root, through_date=through_date, from_date=from_date
    )
    cursor_states = source_cursor_states(root, source_scope["source_dates"])
    registry = read_json(root / "fixed_candidates.json", {})
    if registry:
        check_seal(registry)
    previous_manifest = registry.get("artifact_content_sha256")
    if registry and registry.get("repair_version") != R.REPAIR_VERSION:
        registry = {}
    # All already-retained dates are historical at freeze, including days not
    # yet processed by the fair scheduler. Repairs cannot create forward data.
    freeze_cutoff = max(
        discover_dates(data_root, dict(evidence_start_date="2026-06-05")),
        default="0000",
    )
    descriptors, days, invalidated, pending = [], [], [], []
    for day in source_scope["source_dates"]:
        if clock() >= stop_at:
            raise Deferred("cumulative_source_validation_budget")
        p = root / day / "cursor.json"
        cursor = read_json(p, {})
        if cursor.get("status") not in {
            "completed",
            "valid_empty",
            "completed_with_source_gaps",
        }:
            pending.append(p.parent.name)
            continue
        if not cursor_current(data_root, cursor):
            invalidated.append(cursor["source_date"])
            continue
        daily = check_seal(read_json(cursor["daily_path"]))
        terminal = check_seal(read_json(cursor["terminal_path"]))
        if (
            terminal["daily_sha256"] != daily["artifact_content_sha256"]
            or terminal["generation"] != cursor["generation"]
        ):
            raise ValueError("daily_terminal_binding_invalid")
        descriptors.append(
            dict(
                source_date=cursor["source_date"],
                generation=cursor["generation"],
                daily_sha256=daily["artifact_content_sha256"],
                terminal_sha256=terminal["artifact_content_sha256"],
            )
        )
        days.append((cursor, daily))
        frozen = R.freeze_candidates(daily, cursor["generation"])
        scopes = dict(registry.get("scopes", {}))
        # Append new scopes only; existing cutpoints are never re-tuned using outcomes.
        for sid, scope in frozen["scopes"].items():
            if sid not in scopes and scope["candidates"]:
                scope["fixed_after_source_date"] = max(
                    freeze_cutoff, scope["fixed_after_source_date"]
                )
                scopes[sid] = scope
        if scopes != registry.get("scopes", {}):
            registry = R.seal(
                dict(
                    schema=R.VERSION + ":fixed_candidates",
                    scopes=scopes,
                    repair_version=R.REPAIR_VERSION,
                    previous_manifest_sha256=previous_manifest,
                    **R.AUTH,
                )
            )
            atomic(
                root
                / "candidate_generations"
                / (registry["artifact_content_sha256"] + ".json"),
                registry,
                immutable=True,
            )
            atomic(root / "fixed_candidates.json", registry)
    gen = R.digest(
        [
            descriptors,
            registry.get("artifact_content_sha256"),
            invalidated,
            source_scope,
            cursor_states,
            code_hash(),
        ]
    )
    existing = root / "cumulative" / gen / "candidate_comparison.json"

    def publish(comparison):
        if (
            comparison.get("generation") != gen
            or comparison.get("source_generations") != descriptors
            or comparison.get("source_cursor_states") != cursor_states
            or comparison.get("source_scope") != source_scope
        ):
            raise ValueError("cumulative_comparison_binding_invalid")
        if (
            research_source_scope(
                data_root,
                through_date=source_scope["through_date"],
                from_date=source_scope.get("recovery_from_date"),
            )
            != source_scope
        ):
            raise Deferred("cumulative_source_inventory_changed_before_seal")
        if source_cursor_states(root, source_scope["source_dates"]) != cursor_states:
            raise Deferred("cumulative_cursor_changed_before_seal")
        result = R.seal(
            dict(
                schema=R.VERSION + ":cumulative",
                generation=gen,
                sources=descriptors,
                invalidated_source_dates=invalidated,
                pending_source_dates=pending,
                source_cursor_states=cursor_states,
                source_scope=source_scope,
                candidate_manifest_sha256=registry.get("artifact_content_sha256"),
                candidate_comparison_path=str(existing),
                candidate_sha256=comparison["artifact_content_sha256"],
                **R.AUTH,
            )
        )
        # Repeat the immutable handoff after a crash at either write. Existing
        # conflicting bytes still fail; a missing manifest is reconstructible.
        atomic(existing, comparison, immutable=True)
        atomic(existing.with_name("manifest.json"), result, immutable=True)
        atomic(root / "cumulative/current.json", result)
        return comparison

    if existing.exists():
        comparison = check_seal(read_json(existing))
        return publish(comparison)
    combined = R.Aggregator(scratch_root=root / "scratch")
    try:
        for cursor, daily in days:
            relevant = {
                sid: registry.get("scopes", {}).get(sid)
                for sid in daily["scopes"]
                if sid in registry.get("scopes", {})
            }
            cache_key = R.digest(
                [daily["artifact_content_sha256"], relevant, code_hash()]
            )
            cache = root / "aggregate_cache" / (cache_key + ".json")
            aggregate = read_json(cache, {})
            if not aggregate:
                a = R.Aggregator(dict(scopes=relevant), scratch_root=root / "scratch")
                try:
                    for row in projection_rows(cursor["partitions"]):
                        if clock() >= stop_at:
                            raise Deferred("cumulative_changed_partition_budget")
                        a.add(row)
                    aggregate = R.seal(
                        dict(schema=R.VERSION + ":aggregate", **a.export(), **R.AUTH)
                    )
                finally:
                    a.close()
                atomic(cache, aggregate, immutable=True)
            else:
                check_seal(aggregate)
            combined.merge(aggregate)
        combined.candidates = registry

        def checkpoint(sid, cid, value):
            if clock() >= stop_at:
                raise Deferred("comparison_checkpoint_budget")
            pairs = [
                [delay, list(cluster), p]
                for delay, clusters in combined.pairs[sid][cid].items()
                for cluster, p in clusters.items()
            ]
            key = R.digest(
                [
                    code_hash(),
                    registry.get("scopes", {}).get(sid),
                    cid,
                    pairs,
                    combined.historical_pairs[sid][cid],
                    combined.scopes.get(sid),
                    sid in combined.conflict_scopes,
                ]
            )
            cache = root / "comparison_cache" / (key + ".json")
            if value is None:
                previous = read_json(cache, {})
                if previous:
                    check_seal(previous)
                    if previous.get("input_key") != key:
                        raise ValueError("comparison_checkpoint_binding_invalid")
                    return previous["result"]
                return None
            atomic(
                cache,
                R.seal(dict(input_key=key, result=value, **R.AUTH)),
                immutable=True,
            )

        try:
            comparison = combined.comparison(
                gen, checkpoint=checkpoint, gate=lambda: clock() < stop_at
            )
        except R.ResearchBudgetExceeded as exc:
            raise Deferred(str(exc)) from None
    finally:
        combined.close()
    comparison = R.seal(
        dict(
            comparison,
            invalidated_source_dates=invalidated,
            pending_source_dates=pending,
            source_cursor_states=cursor_states,
            source_scope=source_scope,
            source_generations=descriptors,
            migration_pending=any(
                read_json(root / day / "cursor.json", {})
                .get("source_descriptor", {})
                .get("code")
                != code_hash()
                for day in invalidated
            ),
        )
    )
    return publish(comparison)


def comparison_current(data_root, comparison):
    current = read_json(namespace(data_root) / "cumulative/current.json", {})
    if current.get("candidate_sha256") != comparison.get("artifact_content_sha256"):
        return False
    scope = comparison.get("source_scope")
    if not isinstance(scope, dict) or not scope.get("through_date"):
        return False
    if (
        research_source_scope(
            data_root,
            through_date=scope["through_date"],
            from_date=scope.get("recovery_from_date"),
        )
        != scope
    ):
        return False
    if comparison.get("source_cursor_states") != source_cursor_states(
        namespace(data_root), scope["source_dates"]
    ):
        return False
    for d in comparison.get("source_generations", []):
        cursor = read_json(namespace(data_root) / d["source_date"] / "cursor.json", {})
        if (
            cursor.get("status")
            not in {"completed", "valid_empty", "completed_with_source_gaps"}
            or cursor.get("generation") != d["generation"]
            or not cursor_current(data_root, cursor)
        ):
            return False
    return True


def night_window(now, config):
    now = now.astimezone(R.KST)
    if now.time() >= dt_time(21, 40):
        night = now.date()
    elif now.time() < dt_time(6, 30):
        night = now.date() - timedelta(days=1)
    else:
        return None, None, "outside_night_window"
    if config.get("calendar_verified") is not True:
        return None, None, "main_preparation_calendar_unverified"
    try:
        h, m = map(int, config["next_main_preparation_clock_kst"].split(":"))
        deadline = datetime.combine(
            night + timedelta(days=1), min(dt_time(6, 30), dt_time(h, m)), R.KST
        )
    except (ValueError, KeyError, TypeError):
        return None, None, "main_preparation_clock_invalid"
    from src.trading.market.session_contract import (
        resolve_market_session,
        MARKET_SESSION_REGIME_CLOSED,
    )

    if (
        now >= deadline
        or resolve_market_session(now).session_regime != MARKET_SESSION_REGIME_CLOSED
    ):
        return None, None, "market_open_or_main_preparation_due"
    return night.isoformat(), deadline, None


def heavy_owner_running(proc_root=Path("/proc")):
    names = {
        "run_threshold_cycle_postclose.sh",
        "run_postclose_finalization.sh",
        "update_kospi.py",
    }
    modules = {
        "src.engine.scalping.continuous_reversal_postclose",
        "src.engine.automation.postclose_done_controller",
    }
    for p in proc_root.glob("[0-9]*/cmdline"):
        try:
            words = p.read_bytes().split(b"\0")
            if any(Path(w.decode(errors="replace")).name in names for w in words):
                return True
            if b"-m" in words and words[words.index(b"-m") + 1].decode() in modules:
                return True
        except (OSError, IndexError):
            continue
    return False


def group_rss(pgid, proc_root=Path("/proc")):
    total = 0
    for p in proc_root.glob("[0-9]*/stat"):
        try:
            fields = p.read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == pgid:
                total += int((p.parent / "statm").read_text().split()[1]) * os.sysconf(
                    "SC_PAGE_SIZE"
                )
        except (OSError, ValueError, IndexError):
            continue
    return total


def terminate_group(process):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            continue
    process.wait()


@contextlib.contextmanager
def subreaper():
    # Linux prctl constants are owned by /usr/include/linux/prctl.h.
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    if (
        libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0
        or libc.prctl(36, 1, 0, 0, 0) != 0
    ):
        raise ValueError("research_subreaper_unavailable")
    try:
        yield
    finally:
        libc.prctl(36, previous.value, 0, 0, 0)


def reap_group(pgid):
    until = time.monotonic() + 0.5
    while time.monotonic() < until:
        try:
            pid, _ = os.waitpid(-pgid, os.WNOHANG)
        except ChildProcessError:
            return
        if not pid:
            time.sleep(0.01)


def supervisor_rss():
    return int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf(
        "SC_PAGE_SIZE"
    )


def supervise(command, *, seconds, gate, rss=group_rss, memory_limit=MEMORY_BYTES):
    started = time.monotonic()
    reason = None
    with subreaper():
        child = subprocess.Popen(command, start_new_session=True)
        try:
            while child.poll() is None:
                if time.monotonic() - started >= seconds:
                    reason = "worker_wall_budget"
                elif not gate():
                    reason = "worker_window_or_resource_changed"
                elif rss(child.pid) + supervisor_rss() > memory_limit:
                    reason = "worker_process_group_memory_limit"
                if reason:
                    break
                time.sleep(0.1)
        finally:
            terminate_group(child)
            reap_group(child.pid)
    return dict(
        exit_code=child.returncode,
        reason=reason,
        wall_seconds=time.monotonic() - started,
    )


def discover_dates(data_root, config):
    from src.utils.market_day import is_krx_trading_day

    start = config["evidence_start_date"]
    paths = (Path(data_root) / "ai_decision_trace").glob("ai_decision_trace_*.jsonl*")
    dates = {
        day for p in paths if (day := logical_day(p, "ai_decision_trace_", ".jsonl"))
    }
    dates.update(
        p.name
        for p in (Path(data_root) / "report/continuous_reversal_operating").glob(
            "????-??-??"
        )
    )
    # A retired/missing input still needs one explicit source-gap generation.
    # Otherwise its old-code cursor can keep migration pending indefinitely.
    dates.update(
        p.parent.name for p in namespace(data_root).glob("????-??-??/cursor.json")
    )
    # Keep a discovered-but-unstarted date visible after its input disappears.
    # Its next source attempt must publish an explicit gap, not silent completion.
    current = read_json(namespace(data_root) / "cumulative/current.json", {})
    if current:
        check_seal(current)
        dates.update(current.get("source_scope", {}).get("source_dates", []))
    last = datetime.now(R.KST).date().isoformat()
    return sorted(
        d
        for d in dates
        if start <= d <= last and is_krx_trading_day(date.fromisoformat(d))
    )


def host_cron_zone():
    name = (
        Path("/etc/timezone").read_text().strip()
        if Path("/etc/timezone").exists()
        else str(Path("/etc/localtime").resolve())
    )
    if name in {"Etc/UTC", "UTC"} or name.endswith("/Etc/UTC"):
        return "UTC"
    if name == "Asia/Seoul" or name.endswith("/Asia/Seoul"):
        return "Asia/Seoul"
    raise ValueError("optional_cron_timezone_unverified")


def calendar_signature(original, zone):
    lines = [
        line
        for line in original.splitlines()
        if not line.lstrip().startswith("#")
        and any(
            tag in line for tag in ("THRESHOLD_CYCLE_PREOPEN", "RUNTIME_RELEASE_START")
        )
    ]
    times = []
    for line in lines:
        fields = line.split()
        if len(fields) < 6 or not fields[0].isdigit() or not fields[1].isdigit():
            raise ValueError("main_preparation_cron_time_unverified")
        minute, hour = int(fields[0]), int(fields[1])
        if zone == "UTC":
            hour = (hour + 9) % 24
        if not (0 <= minute <= 59 and 0 <= hour <= 8):
            raise ValueError("main_preparation_cron_outside_verified_morning")
        times.append(dt_time(hour, minute))
    if not times or any(
        line.strip().startswith("CRON_TZ=") and line.strip().split("=", 1)[1] != zone
        for line in original.splitlines()
    ):
        raise ValueError("main_preparation_calendar_unverified")
    earliest = min(times)
    return dict(
        next_main_preparation_clock_kst=earliest.strftime("%H:%M"),
        calendar_verified=True,
        calendar_sha256=R.digest([zone, lines]),
    )


def render_optional_cron(original, workspace, zone):
    calendar_signature(original, zone)
    kept = [line for line in original.splitlines() if TAG not in line]
    clock = calendar_signature(original, zone)["next_main_preparation_clock_kst"]
    h, m = map(int, clock.split(":"))
    deadline = min(dt_time(6, 30), dt_time(h, m))
    kst_hours = [21, 22, 23] + [h for h in range(6) if dt_time(h, 40) < deadline]
    values = sorted((h - 9) % 24 if zone == "UTC" else h for h in kst_hours)
    ranges = []
    start = end = values[0]
    for h in values[1:] + [None]:
        if h is not None and h == end + 1:
            end = h
            continue
        ranges.append(str(start) if start == end else f"{start}-{end}")
        start = end = h
    hours = ",".join(ranges)
    script = shlex.quote(
        str(
            Path(workspace).resolve()
            / "deploy/run_main_market_weakness_research_postclose.sh"
        )
    )
    kept.append(f"40 {hours} * * * TZ=Asia/Seoul bash {script} # {TAG}")
    return "\n".join(kept) + "\n"


def alternate_schedule_census(
    cron_user, *, spool=Path("/var/spool/cron/crontabs"), etc=Path("/etc")
):
    paths = []
    try:
        if spool.exists():
            paths.extend(
                p for p in spool.iterdir() if p.is_file() and p.name != cron_user
            )
        if (etc / "crontab").exists():
            paths.append(etc / "crontab")
        paths.extend((etc / "cron.d").glob("*"))
        paths.extend((etc / "systemd/system").glob("*.timer"))
        paths.extend((etc / "systemd/system").glob("*.service"))
        receipts = []
        for p in paths:
            if not p.is_file():
                continue
            text = p.read_text(errors="replace")
            active = "\n".join(
                line for line in text.splitlines() if not line.lstrip().startswith("#")
            )
            if (
                TAG in text
                or "run_main_market_weakness_research_postclose.sh" in active
            ):
                raise ValueError("duplicate_optional_research_schedule")
            receipts.append(stat_receipt(p))
        return dict(
            status="observed_no_alternate_registration",
            receipt_sha256=R.digest(receipts),
        )
    except PermissionError:
        raise ValueError("alternate_schedule_scope_unobservable") from None


def selected_optional_code(workspace):
    from src.engine.infrastructure.runtime_release_router import selected_release

    selected, _ = selected_release(Path(workspace))
    executing_root = Path(__file__).resolve().parents[3]
    wrapper = "deploy/run_main_market_weakness_research_postclose.sh"
    try:
        # Canonical workspace owns shared data and cron, not deployed code.
        # Bind all existing research dependencies and the actual launch wrapper.
        matches = (code_hash(selected) == code_hash()
                   and (selected / wrapper).read_bytes()
                   == (executing_root / wrapper).read_bytes())
    except (OSError, ValueError):
        matches = False
    if not matches:
        raise ValueError("optional_selected_release_code_not_reviewed")
    return str(selected)


def configure_optional_cron(
    data_root, workspace, *, notify_enabled=None, cron_user=None, runner=subprocess.run
):
    """Explicit installer action. Never called by normal/scheduled execution."""
    owner = pwd.getpwnam(cron_user) if cron_user else pwd.getpwuid(os.geteuid())
    if os.geteuid() != 0 and owner.pw_uid != os.geteuid():
        raise ValueError("optional_cron_owner_not_authorized")
    command = ["crontab"] + (
        ["-u", owner.pw_name] if owner.pw_uid != os.geteuid() else []
    )
    alternate = alternate_schedule_census(owner.pw_name)
    selected = selected_optional_code(workspace)
    result = runner(
        command + ["-l"], capture_output=True, text=True, check=False, timeout=5
    )
    if result.returncode:
        raise ValueError("existing_user_cron_unavailable")
    zone = host_cron_zone()
    calendar = calendar_signature(result.stdout, zone)
    updated = render_optional_cron(result.stdout, workspace, zone)
    root = namespace(data_root)
    old = read_json(root / "installation.json", {})
    if old:
        check_seal(old)
    if old and old.get("uid") != owner.pw_uid:
        raise ValueError("optional_cron_owner_scope_conflict")
    if not root.parent.is_dir():
        raise ValueError("optional_report_directory_absent")
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        if root.is_symlink() or not root.is_dir() or root.stat().st_uid != owner.pw_uid:
            raise ValueError("optional_namespace_owner_invalid") from None
    else:
        if os.geteuid() == 0:
            os.chown(root, owner.pw_uid, owner.pw_gid)
    from src.engine.automation.source_quality_clean_baseline import (
        policy_refresh_start_date,
    )

    today = datetime.now(R.KST).date().isoformat()
    policy = read_json(
        Path(data_root) / "source_quality/clean_baseline_policy.json", {}
    )
    config = R.seal(
        dict(
            schema=R.VERSION + ":installation",
            enabled=old.get("enabled", True),
            notify_enabled=(
                old.get("notify_enabled", False)
                if notify_enabled is None
                else notify_enabled
            ),
            installed_at=old.get("installed_at", datetime.now(R.KST).isoformat()),
            installed_source_date=old.get("installed_source_date", today),
            evidence_start_date=max(
                "2026-06-05",
                policy_refresh_start_date(today, policy),
                old.get("evidence_start_date", "2026-06-05"),
            ),
            uid=owner.pw_uid,
            cron_user=owner.pw_name,
            cron_scope="one_named_user",
            alternate_schedule_census=alternate,
            selected_release_at_install=old.get(
                "selected_release_at_install", selected
            ),
            selected_release_at_rebind=selected if old else None,
            installation_rebound_at=datetime.now(R.KST).isoformat() if old else None,
            previous_installation_sha256=old.get("artifact_content_sha256"),
            installation_code_sha256=code_hash(),
            cron_zone=zone,
            workspace=str(Path(workspace).resolve()),
            **calendar,
            **R.AUTH,
        )
    )
    try:
        runner(command + ["-"], input=updated, text=True, check=True, timeout=5)
        atomic(root / "installation.json", config)
        if os.geteuid() == 0 and owner.pw_uid != 0:
            os.chown(root / "installation.json", owner.pw_uid, owner.pw_gid)
        installed = runner(
            command + ["-l"], capture_output=True, text=True, check=True, timeout=5
        )
        if installed.stdout != updated:
            raise ValueError("optional_cron_install_readback_mismatch")
    except (OSError, ValueError, subprocess.SubprocessError):
        try:
            runner(
                command + ["-"], input=result.stdout, text=True, check=True, timeout=5
            )
            if old:
                atomic(root / "installation.json", old)
                if os.geteuid() == 0 and owner.pw_uid != 0:
                    os.chown(root / "installation.json", owner.pw_uid, owner.pw_gid)
            else:
                (root / "installation.json").unlink(missing_ok=True)
            restored = runner(
                command + ["-l"], capture_output=True, text=True, check=True, timeout=5
            )
            if restored.stdout != result.stdout:
                raise ValueError("optional_cron_rebind_rollback_unverified")
        except (OSError, subprocess.SubprocessError):
            raise ValueError("optional_cron_rebind_rollback_unverified") from None
        raise
    return dict(status="optional_cron_installed", cron_tag=TAG, **R.AUTH)


def verify_installed_calendar(config):
    try:
        old = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, check=True, timeout=5
        ).stdout
        # Other installers may append their own lines after this owner. Only
        # this owner's exact command and its bound Main preparation calendar
        # determine validity; its position in the whole crontab is immaterial.
        rendered = render_optional_cron(old, config["workspace"], config["cron_zone"])
        installed_lines = [line for line in old.splitlines() if TAG in line]
        expected_lines = [line for line in rendered.splitlines() if TAG in line]
        return (
            config.get("uid") == os.geteuid()
            and config.get("installation_code_sha256") == code_hash()
            and host_cron_zone() == config.get("cron_zone")
            and calendar_signature(old, config["cron_zone"])["calendar_sha256"]
            == config.get("calendar_sha256")
            and old.count(TAG) == 1
            and installed_lines == expected_lines
        )
    except (OSError, ValueError, subprocess.SubprocessError, KeyError):
        return False


def select_source_date(data_root, dates, *, night, check_preflight):
    """Rotate source repairs before downstream retries; persist across nights.

    A notification waiting for migration must not monopolize the oldest/latest
    slots that the migration itself needs. Reserve the rotation before starting
    the worker so a crash or permanently unavailable date cannot starve peers.
    Caller owns worker.lock and has already reserved the night budget.
    """
    dates = sorted(d for d in set(dates) if d <= night)
    if not dates:
        return None
    root = namespace(data_root)
    repairs, phases = [], []
    for day in dates:
        check_preflight()
        cursor = read_json(root / day / "cursor.json", {})
        if cursor.get("status") not in {
            "completed",
            "completed_with_source_gaps",
            "valid_empty",
        } or not cursor_current(data_root, cursor):
            repairs.append(day)
        elif unfinished_phase(data_root, day, cursor):
            phases.append(day)
    check_preflight()
    lane, candidates = (
        ("source", repairs)
        if repairs
        else ("phase", phases) if phases else ("refresh", dates[-1:])
    )
    path = root / "schedule_cursor.json"
    rotation = read_json(path, {})
    if rotation:
        check_seal(rotation)
    previous = rotation.get("last_" + lane + "_date", "")
    if dates[-1] in repairs and rotation.get("latest_priority_night") != night:
        # One latest-source opportunity per night, without moving the backlog
        # cursor. Failed/crashed reservations cannot monopolize subsequent slots.
        day = dates[-1]
        rotation.update(latest_priority_night=night, latest_priority_date=day)
    else:
        if lane == "source" and len(candidates) > 1:
            candidates = [d for d in candidates if d != dates[-1]]
        day = next((d for d in candidates if d > previous), candidates[0])
        rotation.update({"last_" + lane + "_date": day})
    check_preflight()
    atomic(
        path,
        R.seal(
            dict(
                rotation,
                schema=R.VERSION + ":schedule_cursor",
                night_id=night,
                **R.AUTH,
            )
        ),
    )
    return day


def scheduled(data_root, *, source_date=None):
    started = time.monotonic()
    root = namespace(data_root)
    config = read_json(root / "installation.json", {})
    if config.get("enabled") is not True:
        return dict(status="disabled_or_not_installed", **R.AUTH)
    check_seal(config)
    now = datetime.now(R.KST)
    night, deadline, reason = night_window(now, config)
    if reason:
        return dict(
            status="deferred_resource_or_window",
            reason=reason,
            **R.AUTH,
        )
    with lock(root / "worker.lock"):
        p = root / "nights" / (night + ".json")
        state = read_json(p, dict(night_id=night, attempts=0, reserved_seconds=0))

        def preflight_status(status, reason):
            result = R.seal(
                dict(
                    schema=R.VERSION + ":night_status",
                    night_id=night,
                    attempted_at_kst=now.isoformat(),
                    status=status,
                    reason=reason,
                    worker_started=False,
                    attempts=state["attempts"],
                    reserved_seconds=state["reserved_seconds"],
                    **R.AUTH,
                )
            )
            return publish_night_status(root, result)

        if not verify_installed_calendar(config):
            return preflight_status(
                "deferred_resource_or_window",
                "installed_calendar_changed_or_unobservable",
            )
        if heavy_owner_running():
            return preflight_status(
                "deferred_resource_or_window", "regular_postclose_or_eod_active"
            )
        if state["attempts"] >= 9 or state["reserved_seconds"] >= NIGHT_SECONDS:
            return preflight_status(
                "deferred_resource_or_window", "night_budget_exhausted"
            )
        seconds = min(
            RESERVATION_SECONDS,
            NIGHT_SECONDS - state["reserved_seconds"],
            (deadline - now).total_seconds() - 2,
        )
        if seconds <= 0:
            return preflight_status(
                "deferred_resource_or_window", "night_deadline_margin"
            )
        state.update(
            attempts=state["attempts"] + 1,
            reserved_seconds=state["reserved_seconds"] + seconds,
        )
        atomic(p, state)  # Unknown/crashed reservations are not refunded.

        def check_preflight():
            # Source selection belongs to the same reservation as the child.
            if time.monotonic() - started >= seconds - 2:
                raise Deferred("supervisor_preflight_wall_budget")
            if night_window(datetime.now(R.KST), config)[2] or heavy_owner_running():
                raise Deferred("supervisor_preflight_window_or_resource_changed")
            if supervisor_rss() > MEMORY_BYTES:
                raise Deferred("supervisor_preflight_memory_limit")

        try:
            check_preflight()
            # Only this producer's abandoned scratch is removed under its lock.
            for scratch in (root / "scratch").glob("aggregate-*"):
                check_preflight()
                if (
                    scratch.is_dir()
                    and not scratch.is_symlink()
                    and all(
                        q.name in {"dedup.sqlite", "dedup.sqlite-journal"}
                        for q in scratch.iterdir()
                    )
                ):
                    shutil.rmtree(scratch)
            dates = research_source_scope(data_root, through_date=night)["source_dates"]
            check_preflight()
            if not dates:
                return preflight_status("valid_empty", "no_retained_source_date")
            if source_date is None:
                day = select_source_date(
                    data_root, dates, night=night, check_preflight=check_preflight
                )
            else:
                # An explicit report repair uses the same night reservation,
                # supervisor and child guards as automatic backlog rotation.
                if (date.fromisoformat(source_date).isoformat() != source_date
                        or source_date not in dates or source_date > night):
                    raise ValueError("repair_source_date_outside_retained_night_scope")
                day = source_date
                check_preflight()
            if day is None:
                return preflight_status("valid_empty", "no_closed_source_date")
        except Deferred as exc:
            return preflight_status("deferred_resource_or_window", str(exc))
        state["source_date"] = day
        atomic(p, state)
        import uuid

        attempt_id = uuid.uuid4().hex
        ticket = dict(
            attempt_id=attempt_id,
            supervisor_pid=os.getpid(),
            source_date=day,
            night_id=night,
            status="reserved",
            seconds=seconds,
            configuration_sha256=config["artifact_content_sha256"],
        )
        ticket_path = root / "attempts" / (attempt_id + ".json")
        atomic(ticket_path, ticket)
        remaining = max(0, seconds - (time.monotonic() - started))
        command = [
            sys.executable,
            "-m",
            MODULE,
            "--data-root",
            str(Path(data_root).resolve()),
            "--worker-date",
            day,
            "--worker-seconds",
            str(max(0, remaining - 2)),
            "--reservation-id",
            attempt_id,
        ]
        result = supervise(
            command,
            seconds=remaining,
            gate=lambda: night_window(datetime.now(R.KST), config)[2] is None
            and not heavy_owner_running(),
        )
        worker_receipt = read_json(ticket_path, {})
        state["last_attempt"] = result
        atomic(p, state)
        result = R.seal(
            dict(
                schema=R.VERSION + ":night_status",
                night_id=night,
                attempted_at_kst=now.isoformat(),
                source_date=day,
                status=(
                    "deferred_resource_or_window"
                    if result["reason"]
                    else (
                        worker_receipt.get("status")
                        if worker_receipt.get("status")
                        in {
                            "completed",
                            "completed_with_source_gaps",
                            "valid_empty",
                            "deferred_resource_or_window",
                            "failed_contract",
                        }
                        and result["exit_code"] == 0
                        else "failed_contract"
                    )
                ),
                worker=result,
                worker_receipt_path=str(ticket_path),
                daily_generation=worker_receipt.get("daily_generation"),
                cumulative_generation=worker_receipt.get("cumulative_generation"),
                notification_status=worker_receipt.get("notification_status"),
                notification_disposition_sha256=worker_receipt.get(
                    "notification_disposition_sha256"
                ),
                notification_disposition_path=worker_receipt.get(
                    "notification_disposition_path"
                ),
                reserved_seconds=state["reserved_seconds"],
                attempts=state["attempts"],
                **R.AUTH,
            )
        )
        result = publish_night_status(root, result)
    return result


def publish_night_status(root, result):
    """Keep latest attempt separate from the last completed computation."""
    root = Path(root)
    complete = result.get("status") in {
        "completed",
        "completed_with_source_gaps",
        "valid_empty",
    }
    if complete and result.get("cumulative_generation"):
        atomic(root / "last_completed_computation.json", result)
    previous = read_json(root / "last_completed_computation.json", {})
    if previous:
        check_seal(previous)
    latest = R.seal(
        dict(
            result,
            latest_attempt=dict(result),
            last_completed_computation=(
                {
                    k: previous.get(k)
                    for k in (
                        "night_id",
                        "source_date",
                        "daily_generation",
                        "cumulative_generation",
                        "notification_status",
                        "artifact_content_sha256",
                    )
                }
                if previous
                else None
            ),
        )
    )
    atomic(root / "night_summary.json", latest)
    return latest


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--worker-date")
    parser.add_argument("--worker-seconds", type=float, default=55)
    parser.add_argument("--scheduled", action="store_true")
    parser.add_argument("--source-date", help="Repair one retained source date under the night supervisor")
    parser.add_argument("--reservation-id")
    parser.add_argument("--configure-optional-cron", action="store_true")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--notify-enabled", action="store_true", default=None)
    parser.add_argument("--cron-user")
    args = parser.parse_args(argv)
    if args.source_date and (not args.scheduled or args.worker_date or args.configure_optional_cron):
        parser.error("--source-date requires only --scheduled")
    try:
        if args.worker_date:
            # Workers are entered only from the night supervisor; no bypass CLI.
            config = read_json(namespace(args.data_root) / "installation.json", {})
            check_seal(config)
            if (
                not args.reservation_id
                or len(args.reservation_id) != 32
                or any(c not in "0123456789abcdef" for c in args.reservation_id)
            ):
                raise Deferred("supervisor_reservation_required")
            ticket_path = (
                namespace(args.data_root) / "attempts" / (args.reservation_id + ".json")
            )
            ticket = read_json(ticket_path, {})
            date.fromisoformat(args.worker_date)
            night, deadline, reason = night_window(datetime.now(R.KST), config)
            if (
                config.get("enabled") is not True
                or reason
                or heavy_owner_running()
                or ticket.get("status") != "reserved"
                or ticket.get("supervisor_pid") != os.getppid()
                or ticket.get("source_date") != args.worker_date
                or ticket.get("night_id") != night
                or ticket.get("configuration_sha256")
                != config["artifact_content_sha256"]
            ):
                raise Deferred("worker_not_in_verified_night")
            stop = time.monotonic() + min(args.worker_seconds, RESERVATION_SECONDS)
            result = process_date(args.data_root, args.worker_date, stop_at=stop)
            comparison = cumulative(args.data_root, stop_at=stop, through_date=night)
            phase_receipt(
                args.data_root,
                args.worker_date,
                result["generation"],
                "notification_pending",
                cumulative_generation=comparison["generation"],
            )
            from src.engine.automation.main_market_weakness_research_notify import (
                reconcile,
            )

            disposition = reconcile(
                namespace(args.data_root),
                comparison,
                send_enabled=config.get("notify_enabled") is True,
                data_root=args.data_root,
                source_matches=lambda: comparison_current(args.data_root, comparison),
                gate=lambda: time.monotonic() < stop
                and night_window(datetime.now(R.KST), config)[2] is None,
            )
            notification = R.seal(
                dict(
                    disposition,
                    source_date=args.worker_date,
                    attempt_id=args.reservation_id,
                    cumulative_generation=comparison["generation"],
                    **R.AUTH,
                )
            )
            notification_path = (
                namespace(args.data_root)
                / "notifications"
                / (notification["artifact_content_sha256"] + ".json")
            )
            atomic(notification_path, notification, immutable=True)
            atomic(
                namespace(args.data_root) / "notification_disposition.json",
                notification,
            )
            phase_receipt(
                args.data_root,
                args.worker_date,
                result["generation"],
                (
                    "completed"
                    if disposition["status"]
                    in {
                        "not_eligible",
                        "completed",
                        "preview_only",
                        "delivery_uncertain",
                    }
                    else "notification_pending"
                ),
                cumulative_generation=comparison["generation"],
                notification_disposition_sha256=notification["artifact_content_sha256"],
            )
            ticket.update(
                cumulative_generation=comparison["generation"],
                notification_status=disposition["status"],
                daily_generation=result["generation"],
                notification_disposition_sha256=notification["artifact_content_sha256"],
                notification_disposition_path=str(notification_path),
            )
        elif args.scheduled:
            result = scheduled(args.data_root, source_date=args.source_date)
        elif args.configure_optional_cron:
            if not args.workspace:
                parser.error("--workspace required for optional cron installation")
            result = configure_optional_cron(
                args.data_root,
                args.workspace,
                notify_enabled=args.notify_enabled,
                cron_user=args.cron_user,
            )
        else:
            parser.error("--scheduled or supervised --worker-date required")
    except Deferred as exc:
        result = dict(status="deferred_resource_or_window", reason=str(exc), **R.AUTH)
    except (
        ValueError,
        OSError,
        EOFError,
        zlib.error,
        sqlite3.Error,
        TypeError,
        KeyError,
    ) as exc:
        result = dict(status="failed_contract", reason=type(exc).__name__, **R.AUTH)
    if (
        args.worker_date
        and args.reservation_id
        and "ticket" in locals()
        and ticket.get("supervisor_pid") == os.getppid()
    ):
        atomic(ticket_path, dict(ticket, status=result["status"], result=result))
    print(json.dumps(result, ensure_ascii=True))
    return 1 if result["status"] == "failed_contract" else 0


if __name__ == "__main__":
    raise SystemExit(main())
