"""Bounded, resumable source scan jobs without raw ledger replication.

Checkpoints retain only normalized projections. Every resume independently
rehashes the exact source byte range; canonical dedup remains the caller's
single global index, including conflicts arriving in later jobs.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
from contextlib import contextmanager

from . import research_storage as storage
from .holding_window_generation import byte_generation, source_stat
from .research_input_budget import Claim

SCHEMA = "research_jsonl_scan_job_v1"


def scan(
    path,
    *,
    output_root,
    project,
    projection_sha256,
    job_bytes,
    record_bytes=storage.RECORD_BYTES,
):
    path = Path(path)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    before = byte_generation(path)
    global_sha = hashlib.sha256()
    offset = 0
    with path.open("rb") as handle, storage.index(root) as db:
        db.execute("CREATE TABLE job_rows(seq INTEGER PRIMARY KEY,body TEXT)")
        while offset < before["size"]:
            key = hashlib.sha256(
                storage.encoded([str(path.resolve()), projection_sha256, offset])
            ).hexdigest()
            receipt_path = storage.safe_path(root, "jobs/" + key + ".json")
            old = None
            if receipt_path.exists():
                try:
                    size = receipt_path.stat().st_size
                    if size > 4 * 1024 * 1024:
                        raise ValueError("scan_job_receipt_budget_invalid")
                    with Claim(size * 8):
                        raw = receipt_path.read_bytes()
                        if len(raw) != size:
                            raise ValueError("scan_job_receipt_changed")
                        candidate = json.loads(raw)
                    if (
                        candidate["schema"] != SCHEMA
                        or candidate["source_path"] != str(path.resolve())
                        or candidate["projection_sha256"] != projection_sha256
                        or candidate["start"] != offset
                        or candidate["end"] > before["size"]
                        or candidate["end"] <= offset
                        or (
                            candidate["end"] < before["size"]
                            and candidate.get("terminal_boundary_complete") is not True
                        )
                        or candidate["artifact_sha256"]
                        != hashlib.sha256(
                            storage.encoded(
                                {
                                    k: v
                                    for k, v in candidate.items()
                                    if k != "artifact_sha256"
                                }
                            )
                        ).hexdigest()
                    ):
                        raise ValueError("scan_job_receipt_invalid")
                    chunk = hashlib.sha256()
                    remaining = candidate["end"] - offset
                    while remaining:
                        block = handle.read(min(65536, remaining))
                        remaining -= len(block)
                        chunk.update(block)
                        if not block:
                            raise ValueError("scan_job_source_short")
                    if chunk.hexdigest() != candidate["source_range_sha256"]:
                        raise ValueError("scan_job_source_range_changed")
                    # Verify referenced projections before accepting this job;
                    # do not partially yield a corrupt resume.
                    for _ in storage.iter_tree(root, candidate["rows_ref"]):
                        pass
                    old = candidate
                except (OSError, ValueError, TypeError, KeyError):
                    handle.seek(offset)
            if old is not None:
                handle.seek(offset)
                remaining = old["end"] - offset
                while remaining:
                    block = handle.read(min(65536, remaining))
                    remaining -= len(block)
                    global_sha.update(block)
                yield {"kind": "checkpoint", "receipt": old, "reused": True}
                for row in storage.iter_tree(root, old["rows_ref"]):
                    yield {"kind": "row", "value": row}
                offset = old["end"]
                continue
            start = offset
            chunk = hashlib.sha256()
            counts = Counter()
            seq = 0
            db.execute("DELETE FROM job_rows")
            while handle.tell() < before["size"]:
                with Claim(record_bytes * 8):
                    raw = handle.readline(record_bytes + 1)
                    complete = raw.endswith(b"\n")
                    oversize = len(raw) > record_bytes
                    chunk.update(raw)
                    global_sha.update(raw)
                    while not complete:
                        tail = handle.readline(record_bytes)
                        if not tail:
                            break
                        chunk.update(tail)
                        global_sha.update(tail)
                        complete = tail.endswith(b"\n")
                        oversize = True
                    counts["records"] += 1
                    if oversize or not complete:
                        counts["isolated_records"] += 1
                    else:
                        try:
                            value = project(json.loads(raw))
                            if value is not None:
                                encoded = storage.encoded(value)
                                if len(encoded) > storage.RECORD_BYTES:
                                    raise ValueError("scan_projection_record_oversize")
                                db.execute(
                                    "INSERT INTO job_rows VALUES (?,?)",
                                    (seq, encoded.decode()),
                                )
                                seq += 1
                        except (ValueError, TypeError, KeyError, AttributeError):
                            counts["isolated_records"] += 1
                    raw = None
                    value = None
                    encoded = None
                if handle.tell() - start >= job_bytes:
                    break
            offset = handle.tell()
            if offset <= start:
                raise ValueError("scan_job_progress_invalid")
            ref = storage.write_tree(
                root,
                (
                    json.loads(body)
                    for body, in db.execute("SELECT body FROM job_rows ORDER BY seq")
                ),
            )
            receipt = dict(
                schema=SCHEMA,
                source_path=str(path.resolve()),
                projection_sha256=projection_sha256,
                start=start,
                end=offset,
                source_range_sha256=chunk.hexdigest(),
                rows_ref=ref,
                census=dict(counts),
            )
            receipt["terminal_boundary_complete"] = complete
            receipt["artifact_sha256"] = hashlib.sha256(
                storage.encoded(receipt)
            ).hexdigest()
            from src.engine.scalping.pre_submit_delay_initial_policy import _atomic

            _atomic(receipt_path, receipt)
            yield {"kind": "checkpoint", "receipt": receipt, "reused": False}
            for row in storage.iter_tree(root, ref):
                yield {"kind": "row", "value": row}
        if (
            byte_generation(path) != before
            or global_sha.hexdigest() != before["sha256"]
        ):
            raise ValueError("scan_source_changed_during_read")
        yield {"kind": "source", "generation": before}
