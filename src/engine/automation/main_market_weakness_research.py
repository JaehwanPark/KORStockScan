"""Optional, bounded night worker for Main advisory weakness research.

Owns its namespace, cursor and terminal only. It is not a mandatory postclose,
PREOPEN or runtime stage and cannot regenerate an upstream source or policy.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
from datetime import date, datetime, time as dt_time, timedelta
import fcntl
import hashlib
import gzip
import json
import os
import pwd
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


def code_hash():
    modules = [
        Path(__file__),
        Path(R.__file__),
        Path(__file__).with_name("main_market_weakness_research_notify.py"),
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


def observations(data_root, source_date):
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
        ):
            raw.pop(key, None)
        result.append(raw)
    # Only a retained exact-ID current observer receipt can establish availability.
    state_path = (
        Path(data_root).resolve().parent / "tmp/market_weakness_observer_state.json"
    )
    try:
        state = read_json(state_path, {}, limit=128 * 1024)
    except (ValueError, TypeError):
        state = {}
    if state_path.exists():
        receipts.append(stat_receipt(state_path))
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
                o["observed_source_delay_sec"] = (
                    checked - R.timestamp(o["as_of"]).timestamp()
                )
    return R.reconstruct_latches(result), receipts, dict(gaps)


class CounterDict(dict):
    def add(self, name, n=1):
        self[name] = self.get(name, 0) + n


def listing_lookup(data_root, source_date):
    from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

    directory = Path(data_root) / "report/micro_reversion_economic_reference"
    candidates = [
        p
        for p in directory.glob("micro_reversion_symbol_master_????-??-??.json")
        if p.stem[-10:] <= source_date
    ]
    if not candidates:
        return lambda _symbol: None, None
    p = max(candidates, key=lambda p: p.stem[-10:])
    try:
        before = stat_receipt(p)
        payload = read_json(p)
        if before != stat_receipt(p):
            raise Deferred("listing_source_changed")
        if (
            payload.get("artifact_id")
            != "main-ai-economic-reference-" + p.stem[-10:] + "-symbol-master"
        ):
            raise ValueError("listing_metadata_identity_invalid")
        master = VerifiedSymbolMaster.from_payload(
            payload, require_canonical_owner=True
        )
    except (ValueError, TypeError, KeyError):
        return lambda _symbol: None, dict(path=str(p), status="source_invalid")

    def lookup(symbol):
        result = master.lookup(symbol, as_of=date.fromisoformat(source_date))
        return (
            result.record.listing_market.value
            if result.economic_metadata_allowed and result.record
            else None
        )

    return lookup, dict(
        stat_receipt(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()
    )


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
    trace = (
        Path(data_root) / "ai_decision_trace" / f"ai_decision_trace_{source_date}.jsonl"
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
    if trace.exists():
        result.append(dict(stat_receipt(trace), kind="natural_trace"))
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
    _, listing = listing_lookup(data_root, day)
    return (
        listing == d.get("listing")
        and receipts_current(cursor.get("shared_object_receipts", []))
        and all(
            receipts_current([p["stat"]])
            for p in cursor.get("partitions", [])
            if p.get("stat")
        )
    )


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
                yield output, next_position, next_position[0] == len(parts), dict(gaps)
                gaps = CounterDict()
            if not records:
                yield [], [pi + 1, 0], pi + 1 == len(parts), {}
        if not parts:
            yield [], [0, 0], True, {}
    finally:
        store.close()


def label_index(root, cursor):
    path = root / cursor["source_date"] / cursor["generation"] / "label_bindings.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA cache_size=-2048")
    db.execute(
        "CREATE TABLE IF NOT EXISTS labels(id TEXT PRIMARY KEY,row TEXT,conflict INTEGER)"
    )
    db.execute("CREATE TABLE IF NOT EXISTS loaded(partition TEXT PRIMARY KEY)")
    for part in cursor["partitions"]:
        if db.execute(
            "SELECT 1 FROM loaded WHERE partition=?", (part["sha256"],)
        ).fetchone():
            continue
        for row in projection_rows([part]):
            _index_label(db, row)
        db.execute("INSERT INTO loaded VALUES(?)", (part["sha256"],))
    db.commit()
    return db


def _index_label(db, row):
    if row.get("decision_origin") != "confirmation_replay" or row.get("auxiliary_hash"):
        return
    raw = json.dumps(row, sort_keys=True)
    for key in {
        row["opportunity_id"],
        row.get("canonical_alias", row["opportunity_id"]),
    }:
        old = db.execute("SELECT row FROM labels WHERE id=?", (key,)).fetchone()
        if old and old[0] != raw:
            db.execute("UPDATE labels SET conflict=1 WHERE id=?", (key,))
        elif not old:
            db.execute("INSERT INTO labels VALUES(?,?,0)", (key, raw))


def bind_natural_label(row, labels):
    if row.get("identity_grade") != "canonical" or row.get("entry_ask") is None:
        return
    found = labels.execute(
        "SELECT row FROM labels WHERE id=? AND conflict=0", (row["opportunity_id"],)
    ).fetchone()
    if not found:
        return
    label = json.loads(found[0])
    if (
        row.get("machine_confirmed_at") == label.get("machine_confirmed_at")
        and row.get("event_id") == label.get("event_id")
        and row["entry_ask"] == label["entry_ask"]
        and row["symbol"] == label["symbol"]
    ):
        row.update(
            outcome=label["outcome"],
            outcome_reason=label.get("outcome_reason"),
            label_binding_ref=label["source_ref"],
            label_binding="exact_event_time_actual_ask",
        )


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
                record = json.loads(raw)
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
    obs, obs_receipts, obs_gaps = observations(data_root, source_date)
    obs = R.ObservationIndex(obs)
    listing, listing_receipt = listing_lookup(data_root, source_date)
    sources = source_plan(data_root, source_date)
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
    descriptor = dict(
        source_date=source_date,
        sources=sources,
        observations=obs_receipts,
        listing=listing_receipt,
        dependencies=dependencies(data_root, source_date),
        code=code_hash(),
        version=R.VERSION,
        label_contract=R.LABEL,
    )
    old_descriptor = prior.get("source_descriptor", {})
    if {
        k: v for k, v in old_descriptor.items() if k != "object_source_state"
    } == descriptor:
        if receipts_current(prior.get("shared_object_receipts", [])):
            descriptor = old_descriptor
        else:
            states = []
            for r in prior.get("shared_object_receipts", []):
                try:
                    states.append(stat_receipt(r["path"]))
                except FileNotFoundError:
                    states.append(dict(path=r["path"], status="missing"))
            descriptor["object_source_state"] = states
    generation = R.digest(descriptor)
    cursor = prior
    if cursor.get("generation") != generation:
        cursor = dict(
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
    while cursor["source_index"] < len(sources):
        if clock() >= stop_at:
            raise Deferred("chunk_wall_budget")
        source = sources[cursor["source_index"]]
        try:
            if source["kind"] == "natural_trace":
                rows, offset, done, gaps, range_proof = trace_records(
                    source, source_date, listing, cursor["offset"]
                )
                if range_proof["end"] > range_proof["start"]:
                    cursor.setdefault("source_ranges", []).append(
                        dict(path=source["path"], **range_proof)
                    )
                labels = label_index(root, cursor)
                try:
                    for row in rows:
                        bind_natural_label(row, labels)
                finally:
                    labels.close()
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
            cursor.setdefault("source_census", {}).setdefault(source["kind"], 0)
            cursor["source_census"][source["kind"]] += len(rows)
            object_receipts = {
                r["path"]: r for r in cursor.get("shared_object_receipts", [])
            }
            for row in rows:
                for receipt in row.get("source_ref", {}).get("object_receipts", []):
                    object_receipts[receipt["path"]] = receipt
            cursor["shared_object_receipts"] = list(object_receipts.values())
            rows = [R.attach_joins(row, obs) for row in rows]
            if done or offset != cursor["offset"]:
                part = write_partition(root, rows)
                cursor["partitions"].append(part)
            for key, n in gaps.items():
                cursor["gaps"][key] = cursor["gaps"].get(key, 0) + n
            if done:
                cursor.update(source_index=cursor["source_index"] + 1, offset=0)
            else:
                if offset == cursor["offset"]:
                    cursor["gaps"]["incomplete_tail"] = 1
                    atomic(path, cursor)
                    raise Deferred("incomplete_source_tail")
                cursor["offset"] = offset
            atomic(path, cursor)
        except (
            FileNotFoundError,
            ValueError,
            EOFError,
            sqlite3.OperationalError,
        ) as exc:
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
    for row in projection_rows(cursor["partitions"]):
        if clock() >= stop_at:
            raise Deferred("aggregation_wall_budget")
        aggregator.add(row)
    daily = aggregator.daily(source_date)
    daily = R.seal(
        dict(
            daily,
            source_census=cursor.get("source_census", {}),
            input_exclusions=cursor["gaps"],
            population="retained_natural_trace_and_confirmation_replay_cohorts_only",
            stored_response_subset_is_not_original_population=True,
        )
    )
    aggregator.close()
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
            source_ranges=cursor.get("source_ranges", []),
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
            dict(census=daily["census"], scopes=daily["scopes"]),
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
    return dict(status=status, source_date=source_date, generation=generation, delta=1)


def cumulative(data_root, *, stop_at, clock=time.monotonic):
    root = namespace(data_root)
    registry = read_json(root / "fixed_candidates.json", {})
    if registry:
        check_seal(registry)
    descriptors, days, invalidated = [], [], []
    for p in sorted(root.glob("????-??-??/cursor.json")):
        if clock() >= stop_at:
            raise Deferred("cumulative_source_validation_budget")
        cursor = read_json(p, {})
        if cursor.get("status") not in {
            "completed",
            "valid_empty",
            "completed_with_source_gaps",
        }:
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
                scopes[sid] = scope
        if scopes != registry.get("scopes", {}):
            registry = R.seal(
                dict(schema=R.VERSION + ":fixed_candidates", scopes=scopes, **R.AUTH)
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
        [descriptors, registry.get("artifact_content_sha256"), invalidated, code_hash()]
    )
    existing = root / "cumulative" / gen / "candidate_comparison.json"
    if existing.exists():
        comparison = check_seal(read_json(existing))
        saved = check_seal(read_json(existing.with_name("manifest.json")))
        atomic(root / "cumulative/current.json", saved)
        return comparison
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
        comparison = combined.comparison(gen)
    finally:
        combined.close()
    comparison = R.seal(
        dict(
            comparison,
            invalidated_source_dates=invalidated,
            source_generations=descriptors,
        )
    )
    atomic(existing, comparison, immutable=True)
    result = R.seal(
        dict(
            schema=R.VERSION + ":cumulative",
            generation=gen,
            sources=descriptors,
            invalidated_source_dates=invalidated,
            candidate_manifest_sha256=registry.get("artifact_content_sha256"),
            candidate_comparison_path=str(existing),
            candidate_sha256=comparison["artifact_content_sha256"],
            **R.AUTH,
        )
    )
    atomic(root / "cumulative" / gen / "manifest.json", result, immutable=True)
    atomic(root / "cumulative/current.json", result)
    return comparison


def comparison_current(data_root, comparison):
    current = read_json(namespace(data_root) / "cumulative/current.json", {})
    if current.get("candidate_sha256") != comparison.get("artifact_content_sha256"):
        return False
    for d in comparison.get("source_generations", []):
        cursor = read_json(namespace(data_root) / d["source_date"] / "cursor.json", {})
        if cursor.get("generation") != d["generation"] or not cursor_current(
            data_root, cursor
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
    paths = (Path(data_root) / "ai_decision_trace").glob(
        "ai_decision_trace_????-??-??.jsonl"
    )
    dates = {p.stem[-10:] for p in paths}
    dates.update(
        p.name
        for p in (Path(data_root) / "report/continuous_reversal_operating").glob(
            "????-??-??"
        )
    )
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
    names = (
        "src/engine/scalping/market_weakness_research.py",
        "src/engine/automation/main_market_weakness_research.py",
        "src/engine/automation/main_market_weakness_research_notify.py",
        "deploy/run_main_market_weakness_research_postclose.sh",
    )
    if any(
        not (selected / name).is_file()
        or (selected / name).read_bytes() != (Path(workspace) / name).read_bytes()
        for name in names
    ):
        raise ValueError("optional_selected_release_code_not_reviewed")
    return str(selected)


def configure_optional_cron(
    data_root, workspace, *, notify_enabled=False, cron_user=None, runner=subprocess.run
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
            enabled=True,
            notify_enabled=notify_enabled,
            installed_at=datetime.now(R.KST).isoformat(),
            installed_source_date=today,
            evidence_start_date=max(
                "2026-06-05", policy_refresh_start_date(today, policy)
            ),
            uid=owner.pw_uid,
            cron_user=owner.pw_name,
            cron_scope="one_named_user",
            alternate_schedule_census=alternate,
            selected_release_at_install=selected,
            installation_code_sha256=code_hash(),
            cron_zone=zone,
            workspace=str(Path(workspace).resolve()),
            **calendar,
            **R.AUTH,
        )
    )
    runner(command + ["-"], input=updated, text=True, check=True, timeout=5)
    atomic(root / "installation.json", config)
    if os.geteuid() == 0 and owner.pw_uid != 0:
        os.chown(root / "installation.json", owner.pw_uid, owner.pw_gid)
    installed = runner(
        command + ["-l"], capture_output=True, text=True, check=True, timeout=5
    )
    if installed.stdout != updated:
        raise ValueError("optional_cron_install_readback_mismatch")
    return dict(status="optional_cron_installed", cron_tag=TAG, **R.AUTH)


def verify_installed_calendar(config):
    try:
        old = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, check=True, timeout=5
        ).stdout
        return (
            config.get("uid") == os.geteuid()
            and config.get("installation_code_sha256") == code_hash()
            and host_cron_zone() == config.get("cron_zone")
            and calendar_signature(old, config["cron_zone"])["calendar_sha256"]
            == config.get("calendar_sha256")
            and old.count(TAG) == 1
            and render_optional_cron(old, config["workspace"], config["cron_zone"])
            == old
        )
    except (OSError, ValueError, subprocess.SubprocessError, KeyError):
        return False


def scheduled(data_root):
    started = time.monotonic()
    root = namespace(data_root)
    config = read_json(root / "installation.json", {})
    if config.get("enabled") is not True:
        return dict(status="disabled_or_not_installed", **R.AUTH)
    check_seal(config)
    if not verify_installed_calendar(config):
        return dict(
            status="deferred_resource_or_window",
            reason="installed_calendar_changed_or_unobservable",
            **R.AUTH,
        )
    now = datetime.now(R.KST)
    night, deadline, reason = night_window(now, config)
    if reason or heavy_owner_running():
        return dict(
            status="deferred_resource_or_window",
            reason=reason or "regular_postclose_or_eod_active",
            **R.AUTH,
        )
    with lock(root / "worker.lock"):
        p = root / "nights" / (night + ".json")
        state = read_json(p, dict(night_id=night, attempts=0, reserved_seconds=0))
        if state["attempts"] >= 9 or state["reserved_seconds"] >= NIGHT_SECONDS:
            return dict(
                status="deferred_resource_or_window",
                reason="night_budget_exhausted",
                **R.AUTH,
            )
        seconds = min(
            RESERVATION_SECONDS,
            NIGHT_SECONDS - state["reserved_seconds"],
            (deadline - now).total_seconds() - 2,
        )
        if seconds <= 0:
            return dict(
                status="deferred_resource_or_window",
                reason="night_deadline_margin",
                **R.AUTH,
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

        def preflight_status(status, reason):
            result = R.seal(
                dict(
                    schema=R.VERSION + ":night_status",
                    night_id=night,
                    status=status,
                    reason=reason,
                    worker_started=False,
                    attempts=state["attempts"],
                    reserved_seconds=state["reserved_seconds"],
                    **R.AUTH,
                )
            )
            atomic(root / "night_summary.json", result)
            return result

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
            dates = discover_dates(data_root, config)
            check_preflight()
            if not dates:
                return preflight_status("valid_empty", "no_retained_source_date")
            # Alternate latest and pending oldest; preserve date across midnight.
            pending = []
            for day in dates:
                check_preflight()
                c = read_json(root / day / "cursor.json", {})
                if c.get("status") not in {
                    "completed",
                    "completed_with_source_gaps",
                    "valid_empty",
                } or not cursor_current(data_root, c):
                    pending.append(day)
                check_preflight()
        except Deferred as exc:
            return preflight_status("deferred_resource_or_window", str(exc))
        day = (
            (pending[-1] if state["attempts"] % 2 else pending[0])
            if pending
            else dates[-1]
        )
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
        atomic(root / "night_summary.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--worker-date")
    parser.add_argument("--worker-seconds", type=float, default=55)
    parser.add_argument("--scheduled", action="store_true")
    parser.add_argument("--reservation-id")
    parser.add_argument("--configure-optional-cron", action="store_true")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--notify-enabled", action="store_true")
    parser.add_argument("--cron-user")
    args = parser.parse_args(argv)
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
            comparison = cumulative(args.data_root, stop_at=stop)
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
            ticket.update(
                cumulative_generation=comparison["generation"],
                notification_status=disposition["status"],
                daily_generation=result["generation"],
                notification_disposition_sha256=notification["artifact_content_sha256"],
                notification_disposition_path=str(notification_path),
            )
        elif args.scheduled:
            result = scheduled(args.data_root)
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
    except (ValueError, OSError, EOFError, sqlite3.Error, TypeError, KeyError) as exc:
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
