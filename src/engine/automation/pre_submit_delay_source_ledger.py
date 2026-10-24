"""External exact raw/compact overlap for the initial timing family.

Only source identities and byte seals are retained. Summary counts never
replace overlap, and late duplicates/conflicts remain ineligible globally.
"""

from collections import Counter
from contextlib import ExitStack
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import tempfile
from functools import lru_cache

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping import pre_submit_delay_tuning as owner
from src.engine.scalping.pre_submit_delay_initial_policy import (
    _atomic,
    digest,
    code_contract,
)
from src.engine.lifecycle.research_input_budget import Claim

SCHEMA = "pre_submit_delay_family_source_ledger_v2"


def publish_prepared(root, day, prepared_path):
    """Publish a precomputed raw/compact seal after exact source revalidation."""
    prepared_path = Path(prepared_path).resolve()
    root = Path(root).resolve()
    if prepared_path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("delay_ledger_partition_required")
    before = byte_generation(prepared_path)
    body = json.loads(prepared_path.read_bytes())
    if (
        body.get("schema") != SCHEMA
        or body.get("source_date") != day
        or body.get("code_contract_sha256") != code_contract()
        or owner.family_source_ledger_issues(root, day, ledger_path=prepared_path)
    ):
        raise ValueError("prepared_delay_ledger_invalid")
    target = owner.family_source_ledger_path(root, day)
    storage.copy_tree(
        prepared_path.parent, target.parent, body["matched_event_ids_ref"]
    )
    if byte_generation(prepared_path) != before:
        raise ValueError("prepared_delay_ledger_changed")
    _atomic(target, body)
    issues = owner.family_source_ledger_issues(root, day)
    if issues:
        raise ValueError("published_delay_ledger_invalid:" + ",".join(issues))
    return body


def seal(root, day, *, source_snapshot=None, output_root=None):
    from src.engine.lifecycle.research_disk_budget import use

    out = (
        Path(output_root)
        if output_root is not None
        else Path(root) / "pipeline_event_summaries"
    )
    with use(out / ".pre-submit-source-cache") as disk:
        # The shared summaries directory also contains other producers'
        # source metadata/aliases. Only ledger trees and this family's cache
        # are resident outputs; atomic() accounts each ledger old/new pair.
        disk.include(out / "shards")
        return _seal(
            root, day, source_snapshot=source_snapshot, output_root=output_root
        )


def _seal(root, day, *, source_snapshot=None, output_root=None):
    from .pre_submit_delay_partitioned_research import source
    from src.engine.pipeline_event_summary import (
        _source_part_path,
        _part_snapshot_stamp,
        execution_projection_identity,
    )

    root = Path(root).resolve()
    out = (
        Path(output_root).resolve()
        if output_root is not None
        else root / "pipeline_event_summaries"
    )
    if output_root is not None and (out == root or out.is_relative_to(root)):
        raise ValueError("delay_ledger_isolated_output_required")
    out.mkdir(parents=True, exist_ok=True)
    contract = code_contract()
    saved = out / owner.family_source_ledger_path(root, day).name
    if (
        output_root is None
        and saved.exists()
        and saved.stat().st_size <= 4 * 1024 * 1024
    ):
        try:
            old = json.loads(saved.read_bytes())
            if (
                old.get("schema") == SCHEMA
                and old.get("code_contract_sha256") == contract
                and not owner.family_source_ledger_issues(
                    root, day, source_snapshot=source_snapshot
                )
            ):
                return old
        except (OSError, ValueError, TypeError, KeyError):
            pass
    with (
        tempfile.TemporaryDirectory(prefix=".delay-ledger-", dir=out) as scratch,
        ExitStack() as stack,
    ):
        snapshot = source_snapshot or stack.enter_context(
            source(
                root,
                day,
                Path(scratch) / "compact",
                checkpoint_root=out / ".pre-submit-source-cache",
            )
        )
        with storage.index(Path(scratch) / "raw") as db:
            parts = []
            stages = Counter()
            isolated = Counter()
            global_sha = hashlib.sha256()
            for partition in ("base", "late"):
                logical = _source_part_path(root / "pipeline_events", day, partition)
                representations = [
                    p for p in (logical, Path(str(logical) + ".gz")) if p.exists()
                ]
                if not representations:
                    if partition == "base":
                        raise ValueError("raw_source_missing")
                    continue
                seals = []
                for number, path in enumerate(representations):
                    if path.is_symlink():
                        raise ValueError("raw_source_path_invalid")
                    stamp = _part_snapshot_stamp(path)
                    physical_generation = byte_generation(path)
                    logical_sha = hashlib.sha256()
                    size = rows = 0
                    opener = gzip.open if path.suffix == ".gz" else open
                    envelope_limit = 6 * 1024 * 1024
                    with opener(path, "rb") as handle, Claim(envelope_limit * 8):
                        while True:
                            raw = handle.readline(envelope_limit + 1)
                            if not raw:
                                break
                            complete = raw.endswith(b"\n")
                            oversize = len(raw) > envelope_limit
                            logical_sha.update(raw)
                            size += len(raw)
                            if number == 0:
                                global_sha.update(raw)
                            while not complete:
                                tail = handle.readline(storage.RECORD_BYTES)
                                if not tail:
                                    break
                                logical_sha.update(tail)
                                size += len(tail)
                                if number == 0:
                                    global_sha.update(tail)
                                complete = tail.endswith(b"\n")
                                oversize = True
                            rows += 1
                            if number:
                                continue
                            if oversize or not complete:
                                isolated["unidentifiable_raw_source_quarantine"] += 1
                                continue
                            try:
                                value = json.loads(raw)
                                if value.get("stage") not in owner.SOURCE_STAGES:
                                    continue
                                at = datetime.fromisoformat(value["emitted_at"])
                                # Legacy pipeline envelopes use a local date
                                # without an offset. This identity ledger only
                                # checks that date; causal price qualification
                                # still requires the timing family's own clocks.
                                emitted_day = (
                                    (
                                        at.astimezone(ZoneInfo("Asia/Seoul"))
                                        if at.tzinfo
                                        else at
                                    )
                                    .date()
                                    .isoformat()
                                )
                                if (
                                    value.get("event_type") != "pipeline_event"
                                    or value.get("emitted_date") != emitted_day
                                ):
                                    raise ValueError("raw_date_or_schema_invalid")
                                if value.get("emitted_date") != day or value.get(
                                    "storage_partition_date"
                                ) not in (None, "", day):
                                    continue  # Exact identifiable other-date rows are isolated.
                                identity = execution_projection_identity(value)
                                stages[value["stage"]] += 1
                                storage.put(db, identity, {"stage": value["stage"]})
                            except (ValueError, TypeError, KeyError):
                                isolated["unidentifiable_raw_source_quarantine"] += 1
                            finally:
                                value = None
                                raw = None
                    if _part_snapshot_stamp(path) != stamp:
                        raise ValueError("raw_generation_changed")
                    seals.append(
                        dict(
                            path=str(path.resolve()),
                            stamp=stamp,
                            generation=physical_generation,
                            logical_sha256=logical_sha.hexdigest(),
                            decoded_bytes=size,
                            raw_count=rows,
                        )
                    )
                if (
                    len(
                        {
                            (s["logical_sha256"], s["decoded_bytes"], s["raw_count"])
                            for s in seals
                        }
                    )
                    != 1
                ):
                    raise ValueError("raw_plain_gzip_conflict")
                parts.append(
                    dict(
                        partition=partition,
                        logical_path=str(logical.resolve()),
                        representations=[
                            {k: s[k] for k in ("path", "stamp", "generation")}
                            for s in seals
                        ],
                        logical_sha256=seals[0]["logical_sha256"],
                        decoded_bytes=seals[0]["decoded_bytes"],
                        raw_count=seals[0]["raw_count"],
                    )
                )
            if isolated:
                raise ValueError("unidentifiable_raw_source_quarantine")
            db.execute(
                "CREATE TABLE compact(id TEXT PRIMARY KEY,copies INTEGER,conflict INTEGER) WITHOUT ROWID"
            )
            for identity, copies, conflict in snapshot.connection.execute(
                "SELECT id,copies,conflicted FROM records"
            ):
                # The ledger is exact-date, while its source seal is cumulative.
                body = snapshot.connection.execute(
                    "SELECT body FROM records WHERE id=?", (identity,)
                ).fetchone()[0]
                if json.loads(body)["emitted_date"] == day:
                    db.execute(
                        "INSERT INTO compact VALUES (?,?,?)",
                        (identity, copies, conflict),
                    )

            def matched():
                return db.execute(
                    "SELECT r.id FROM records r JOIN compact c ON c.id=r.id "
                    "WHERE r.copies=1 AND r.conflicted=0 AND c.copies=1 AND c.conflict=0 ORDER BY r.id"
                )

            matched_ref = storage.write_tree(out, (i for i, in matched()))
            compact = (snapshot.source.get("cumulative_generations") or {}).get(
                day
            ) or snapshot.source
            body = dict(
                schema=SCHEMA,
                source_date=day,
                status="ready" if matched_ref["count"] else "valid_empty",
                metric_role="source_quality_gate",
                decision_authority="report_only",
                runtime_effect=False,
                code_contract_sha256=contract,
                raw_parts=parts,
                raw_logical_sha256=global_sha.hexdigest(),
                raw_stage_counts=dict(stages),
                compact_source_sha256=compact["sha256"],
                compact_paths=compact["paths"],
                matched_event_ids_ref=matched_ref,
                raw_event_id_n=db.execute("SELECT count(*) FROM records").fetchone()[0],
                compact_event_id_n=db.execute(
                    "SELECT count(*) FROM compact"
                ).fetchone()[0],
            )
            body["raw_only_event_count"] = body["raw_event_id_n"] - matched_ref["count"]
            body["compact_only_event_count"] = (
                body["compact_event_id_n"] - matched_ref["count"]
            )
            for part in parts:
                for representation in part["representations"]:
                    if (
                        _part_snapshot_stamp(Path(representation["path"]))
                        != representation["stamp"]
                    ):
                        raise ValueError("raw_generation_changed_before_publication")
                    if (
                        byte_generation(Path(representation["path"]))
                        != representation["generation"]
                    ):
                        raise ValueError("raw_bytes_changed_before_publication")
            body["ledger_sha256"] = digest(body)
            snapshot.verify(snapshot.target_date, root)
            if code_contract() != contract:
                raise ValueError("delay_ledger_code_changed_during_scan")
            _atomic(saved, body)
            return body


def verify_logical_part(part, raw_dir):
    """Verify lossless alias transitions against the original full logical seal.

    Full bytes and gzip CRC are checked once per exact file generation. The
    bounded cache retains digests only; append, replacement and late aliases
    invalidate the key. No ledger or original source receipt is rewritten.
    """
    from src.engine.lifecycle.holding_window_generation import source_stat

    logical = Path(part["logical_path"])
    if logical.parent != Path(raw_dir).resolve():
        raise ValueError("delay_raw_logical_path_invalid")
    aliases = [
        p for p in (logical, Path(str(logical) + ".gz")) if p.exists() or p.is_symlink()
    ]
    if not aliases or any(p.is_symlink() or not p.is_file() for p in aliases):
        raise ValueError("delay_raw_logical_source_missing")
    expected, size = part.get("logical_sha256"), part.get("decoded_bytes")
    if (
        not isinstance(expected, str)
        or len(expected) != 64
        or type(size) is not int
        or size < 0
    ):
        raise ValueError("delay_raw_logical_seal_invalid")
    signature = tuple((str(p), tuple(source_stat(p.stat()))) for p in aliases)
    _verified_logical_generation(str(logical), signature, expected, size)
    after = [
        p for p in (logical, Path(str(logical) + ".gz")) if p.exists() or p.is_symlink()
    ]
    if any(p.is_symlink() for p in after) or signature != tuple(
        (str(p), tuple(source_stat(p.stat()))) for p in after
    ):
        raise ValueError("delay_raw_logical_generation_changed")


@lru_cache(maxsize=64)
def _verified_logical_generation(logical, signature, expected, expected_size):
    from src.engine.lifecycle.holding_window_generation import source_stat

    for name, before in signature:
        path = Path(name)
        sha = hashlib.sha256()
        size = 0
        with (gzip.open if path.suffix == ".gz" else open)(path, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(block)
                size += len(block)
                if size > expected_size:
                    raise ValueError("delay_raw_logical_generation_changed")
        if (
            path.is_symlink()
            or tuple(source_stat(path.stat())) != before
            or sha.hexdigest() != expected
            or size != expected_size
        ):
            raise ValueError("delay_raw_logical_generation_changed")
    return expected
