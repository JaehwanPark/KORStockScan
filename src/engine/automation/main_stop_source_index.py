"""Offline stop source references, partitioned by whole position identity.

Owns no live collection. Source rows remain in the original pipeline ledger;
sealed indexes contain offsets and hashes, never duplicate AI/quote bodies.
"""

from collections import Counter, OrderedDict
from contextlib import contextmanager, ExitStack
import hashlib
import json
from pathlib import Path
import tempfile

from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_disk_budget import temporary, INDEX_LIMIT
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.utils.jsonl_io import open_text_auto

PARTITIONS = 16
SCHEMA = "main_stop_source_reference_index_v2"


def extract(event):
    if not isinstance(event, dict):
        return None
    stage = event.get("stage")
    release = stage == "manual_control_auto_released_at_average_price"
    if stage not in {
        "main_stop_source",
        "hard_stop_manual_control_handoff",
        "hard_stop_manual_control_handoff_deferred",
        "manual_control_auto_released_at_average_price",
    }:
        return None
    fields = event.get("fields")
    field = (
        "main_stop_source"
        if stage == "main_stop_source"
        else "main_stop_release_source" if release else "main_stop_handoff_source"
    )
    row = fields.get(field) if isinstance(fields, dict) else None
    # Historical events have no exact position/pin receipt. Do not backfill it.
    if row is None and stage != "main_stop_source":
        return None
    if isinstance(row, str):
        row = json.loads(row)
    if not isinstance(row, dict):
        raise ValueError("stop_source_row_invalid")
    if release:
        from src.engine.scalping.main_stop_replay import valid_release

        if not valid_release(row):
            raise ValueError("stop_release_stage_invalid")
        return row
    if stage != "main_stop_source" and (
        row.get("schema") != "main_stop_handoff_source_v1"
        or row.get("registered") is not (stage == "hard_stop_manual_control_handoff")
    ):
        raise ValueError("stop_handoff_stage_invalid")
    return row


def prepare(root, inventory, loader, census):
    """Decode a changed source once; unchanged sources reuse sealed references."""
    result = []
    # Cache identity includes the native decoder owner, even when a test or
    # observer wraps the callback without changing the producer contract.
    loader_source = Path(__file__).with_name("main_stop_postclose.py")
    projection_source = Path(__file__).with_name("main_stop_source_projection.py")
    decoder = policy.digest(
        dict(
            index=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            loader=hashlib.sha256(loader_source.read_bytes()).hexdigest(),
            projection=hashlib.sha256(projection_source.read_bytes()).hexdigest(),
        )
    )
    for name, generation in inventory.items():
        identity = policy.digest(
            dict(path=name, generation=generation, decoder=decoder)
        )
        directory = Path(root) / "source_index" / identity
        manifest = directory / "index.json"
        if manifest.exists():
            body, _ = policy.bounded_object(manifest)
            if (
                body.get("schema") != SCHEMA
                or body.get("identity") != identity
                or body.get("sha256")
                != policy.digest({k: v for k, v in body.items() if k != "sha256"})
            ):
                raise ValueError("stop_source_index_invalid")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            counts = Counter()
            refs = {}
            with (
                temporary(INDEX_LIMIT),
                tempfile.TemporaryDirectory(prefix=".refs-", dir=directory) as scratch,
            ):
                handles = {}
                used = 0
                try:
                    for event, offset, line_sha in loader(
                        Path(name), counts, references=True
                    ):
                        try:
                            row = extract(event)
                        except ValueError:
                            counts["malformed"] += 1
                            continue
                        if row is None:
                            if (
                                isinstance(event, dict)
                                and event.get("stage")
                                == "manual_control_auto_released_at_average_price"
                            ):
                                counts["unbound_release_events"] += 1
                            if isinstance(event, dict) and event.get("stage") in {
                                "hard_stop_manual_control_handoff",
                                "hard_stop_manual_control_handoff_deferred",
                            }:
                                counts["unbound_handoff_events"] += 1
                            continue
                        key, at = row.get("position_key"), row.get("at")
                        if not isinstance(key, str) or not key or not policy.finite(at):
                            counts["unidentifiable"] += 1
                            continue
                        cell = (
                            str(row.get("role", "")) + "|" + str(row.get("market", ""))
                        )
                        bucket = (
                            int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
                            % PARTITIONS
                        )
                        evaluation = (
                            row.get("schema") == "main_stop_evaluation_source_v1"
                        )
                        kind = (
                            "1"
                            if row.get("schema") == "main_stop_handoff_source_v1"
                            else (
                                "2"
                                if row.get("schema") == "main_stop_release_source_v1"
                                else "0e" if evaluation else "0"
                            )
                        )
                        # An actual normal decision and a fast/shared quote can
                        # have the same clock. Preserve distinct evaluation
                        # generations; conflicting bodies of one ID stay visible.
                        generation_id = row.get("evaluation_generation")
                        suffix = (
                            "|"
                            + f"{generation_id:020d}"
                            + "|"
                            + str(row.get("evaluation_id"))
                            if evaluation
                            and type(generation_id) is int
                            and generation_id > 0
                            else (
                                "|invalid|"
                                + policy.digest(
                                    [
                                        row.get("evaluator"),
                                        row.get("stage"),
                                        row.get("evaluation_id"),
                                    ]
                                )
                                if evaluation
                                else ""
                            )
                        )
                        observation = row.get("source_observation_generation")
                        native_id = (
                            row.get("evaluation_id")
                            if evaluation
                            else row.get("quote_id")
                        )
                        if (
                            type(observation) is int
                            and observation > 0
                            and isinstance(native_id, str)
                        ):
                            kind = "0n"
                            suffix = "|" + f"{observation:020d}" + "|" + native_id
                        record = dict(
                            id=f"{key}|{float(at):030.9f}|{kind}{suffix}",
                            position_key=key,
                            at=at,
                            cell=cell,
                            offset=offset,
                            line_sha256=line_sha,
                            content_sha256=policy.digest(row),
                        )
                        record["source_schema"] = row.get("schema")
                        if native_id:
                            record["event_anchor"] = (
                                str(row.get("schema")) + "|" + str(native_id)
                            )
                        if evaluation:
                            record.update(
                                evaluator=row.get("evaluator"),
                                stage=row.get("stage"),
                                evaluation_id=row.get("evaluation_id"),
                                quote_source_sha256=row.get("quote_source_sha256"),
                            )
                            counts[
                                "evaluation:"
                                + str(row.get("evaluator"))
                                + ":"
                                + str(row.get("stage"))
                            ] += 1
                        elif row.get("schema") == "main_stop_source_v1":
                            counts["shared_quote_rows"] += 1
                        raw = storage.encoded(record) + b"\n"
                        used += len(raw)
                        if used > INDEX_LIMIT:
                            raise ValueError(
                                "stop_daily_reference_spool_budget_exceeded"
                            )
                        if bucket not in handles:
                            handles[bucket] = open(Path(scratch) / str(bucket), "wb")
                        handles[bucket].write(raw)
                        counts["raw"] += 1
                finally:
                    for handle in handles.values():
                        handle.close()
                for bucket in sorted(handles):
                    with open(Path(scratch) / str(bucket)) as handle:
                        refs[str(bucket)] = storage.write_tree(
                            directory, (json.loads(line) for line in handle)
                        )
            if byte_generation(Path(name)) != generation:
                raise ValueError("stop_source_index_generation_changed")
            body = dict(
                schema=SCHEMA,
                identity=identity,
                source=name,
                generation=generation,
                partitions=refs,
                census=dict(counts),
            )
            body["sha256"] = policy.digest(body)
            _atomic(manifest, body)
        census.update(body["census"])
        result.append((directory, body))
    return result


@contextmanager
def prior_sealed_indexes(report_path):
    with ExitStack() as resources:
        yield _prior_sealed_indexes(report_path, resources)


def _prior_sealed_indexes(report_path, resources):
    """Read an earlier sealed census without pretending to rehash its raw files.

    The prior report owns population/source inventory. Selected rows are still
    re-read and checked by Position.rows; unselected raw bytes have no new claim.
    """
    from src.engine.lifecycle.research_input_budget import Claim

    def read(path):
        path = Path(path).absolute()
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("stop_prior_index_path_invalid")
        resources.enter_context(Claim(path.stat().st_size * 8))
        return policy.bounded_object(path)

    report_path = Path(report_path).absolute()
    report, report_sha = read(report_path)
    if (
        report.get("schema") != "main_stop_execution_research_v1"
        or report.get("status") != "completed_report_only"
        or report.get("report_sha256")
        != policy.digest({k: v for k, v in report.items() if k != "report_sha256"})
        or report.get("allowed_runtime_apply") is not False
        or report.get("policy_mutated") is not False
        or report.get("code_sha256")
        != policy.digest(report.get("research_code_generation"))
    ):
        raise ValueError("stop_prior_research_report_invalid")
    receipt_path = Path(report["input_receipt"])
    if receipt_path.absolute() != report_path.parent / "input_receipt.json":
        raise ValueError("stop_prior_input_path_invalid")
    receipt, receipt_sha = read(receipt_path)
    if (
        receipt.get("receipt_sha256")
        != policy.digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
        or receipt.get("receipt_sha256") != report.get("input_receipt_sha256")
        or receipt.get("source_sha256") != report.get("source_sha256")
        or receipt.get("source_date") != report.get("source_date")
        or receipt.get("code_sha256") != report.get("code_sha256")
        or receipt.get("research_code_generation")
        != report.get("research_code_generation")
        or receipt.get("original_report") != report.get("original_report")
        or receipt.get("allowed_runtime_apply") is not False
    ):
        raise ValueError("stop_prior_input_binding_invalid")
    inventory = receipt.get("source_inventory")
    if (
        not isinstance(inventory, dict)
        or len(inventory) > 4096
        or policy.digest(inventory) != report["source_sha256"]
    ):
        raise ValueError("stop_prior_inventory_invalid")
    files = report["research_code_generation"]["files"]
    decoder = policy.digest(
        dict(
            index=files["automation/main_stop_source_index.py"],
            loader=files["automation/main_stop_postclose.py"],
            projection=files["automation/main_stop_source_projection.py"],
        )
    )
    prepared = []
    references = []
    stats = {}
    from src.engine.lifecycle.holding_window_generation import source_stat

    for name, generation in inventory.items():
        source = Path(name)
        if (
            source.is_symlink()
            or any(p.is_symlink() for p in source.parents)
            or not source.is_file()
            or source.stat().st_size != generation.get("size")
        ):
            raise ValueError("stop_prior_selected_source_path_changed")
        stats[name] = source_stat(source.stat())
        identity = policy.digest(
            dict(path=name, generation=generation, decoder=decoder)
        )
        directory = report_path.parent / "source_index" / identity
        path = directory / "index.json"
        body, sha = read(path)
        if (
            body.get("schema") not in {"main_stop_source_reference_index_v1", SCHEMA}
            or body.get("identity") != identity
            or body.get("source") != name
            or body.get("generation") != generation
            or body.get("sha256")
            != policy.digest({k: v for k, v in body.items() if k != "sha256"})
        ):
            raise ValueError("stop_prior_index_binding_invalid")
        prepared.append((directory, body))
        references.append(dict(path=str(path), sha256=sha))
    if sum(body.get("census", {}).get("raw", 0) for _, body in prepared) != report.get(
        "source_census", {}
    ).get("raw", 0):
        raise ValueError("stop_prior_index_population_changed")
    proof = dict(
        prior_report=dict(path=str(report_path), sha256=report_sha),
        prior_input_receipt=dict(path=str(receipt_path), sha256=receipt_sha),
        prior_source_inventory_sha256=report["source_sha256"],
        prior_decoder_sha256=decoder,
        current_index_references=references,
        historical_index_byte_hash_previously_pinned=False,
        full_current_raw_generation_rehashed=False,
        population_scope="prior_sealed_index_selected_rows_only",
        allowed_runtime_apply=False,
    )
    return prepared, proof, stats, report


class Position:
    def __init__(self, db, key, cell, first, last, checkpoint):
        self.db, self.key, self.cell, self.first, self.last = db, key, cell, first, last
        self.checkpoint = checkpoint
        self.low, self.high = key + "|", key + "|" + chr(0x10FFFF)
        digest = hashlib.sha256()
        for sha, conflict in db.execute(
            "SELECT sha,conflicted FROM records WHERE id>=? AND id<=? ORDER BY id",
            (self.low, self.high),
        ):
            digest.update(f"{sha}:{conflict}\n".encode())
        self.source_sha256 = digest.hexdigest()

    def rows(self):
        references = self.db.execute(
            "SELECT id,body,conflicted FROM records WHERE id>=? AND id<=? ORDER BY id",
            (self.low, self.high),
        )
        for _, row in self._validated_rows(references):
            yield row

    def _validated_rows(self, references, *, forward_only=False):
        handles = OrderedDict()
        previous = None
        try:
            for identity, body, conflict in references:
                self.checkpoint()
                if conflict:
                    yield identity, {}
                    continue
                ref = json.loads(body)
                name = ref["path"]
                if name not in handles:
                    if len(handles) >= 8:
                        handles.popitem(last=False)[1].close()
                    handles[name] = open_text_auto(Path(name), errors="strict")
                handle = handles[name]
                handles.move_to_end(name)
                offset = ref["offset"]
                if forward_only and previous and previous[:2] == (name, offset):
                    line = previous[2]
                else:
                    if forward_only:
                        # TextIO seek can rewind gzip's decoder even when its
                        # logical offset increases. Consume intervening lines.
                        current = handle.tell()
                        while current < offset:
                            self.checkpoint()
                            part = handle.readline(2 * 1024 * 1024 + 1)
                            if not part:
                                raise ValueError("stop_source_reference_offset_invalid")
                            while not part.endswith("\n"):
                                self.checkpoint()
                                part = handle.readline(2 * 1024 * 1024 + 1)
                                if not part:
                                    raise ValueError(
                                        "stop_source_reference_offset_invalid"
                                    )
                            current = handle.tell()
                        if current != offset:
                            raise ValueError("stop_source_reference_offset_invalid")
                    else:
                        handle.seek(offset)
                    line = handle.readline(2 * 1024 * 1024 + 1)
                    previous = (name, offset, line)
                if hashlib.sha256(line.encode()).hexdigest() != ref["line_sha256"]:
                    raise ValueError("stop_source_reference_changed")
                row = extract(json.loads(line))
                if policy.digest(row) != ref["content_sha256"]:
                    raise ValueError("stop_source_reference_invalid")
                yield identity, row
        finally:
            for handle in handles.values():
                handle.close()

    @contextmanager
    def materialized(self, directory):
        """Read source offsets forward once, then restore original event order."""
        with storage.index(directory) as db:
            db.execute(
                "CREATE TABLE source_refs (id TEXT PRIMARY KEY,path TEXT,offset_length INTEGER,offset_text TEXT,body TEXT,conflicted INTEGER)"
            )
            for identity, body, conflict in self.db.execute(
                "SELECT id,body,conflicted FROM records WHERE id>=? AND id<=? ORDER BY id",
                (self.low, self.high),
            ):
                ref = json.loads(body)
                offset = ref["offset"]
                if type(offset) is not int or offset < 0:
                    raise ValueError("stop_source_reference_offset_invalid")
                text = str(offset)
                db.execute(
                    "INSERT INTO source_refs VALUES(?,?,?,?,?,?)",
                    (identity, ref["path"], len(text), text, body, conflict),
                )
            references = db.execute(
                "SELECT id,body,conflicted FROM source_refs ORDER BY path,offset_length,offset_text,id"
            )
            for identity, row in self._validated_rows(references, forward_only=True):
                storage.put(db, identity, row)

            def rows():
                for (raw,) in db.execute("SELECT body FROM records ORDER BY id"):
                    self.checkpoint()
                    yield json.loads(raw)

            yield rows


def positions(prepared, directory, census, *, checkpoint=lambda: None):
    # Whole positions stay in one partition, including cross-date duplicates.
    # Only compact references enter the sort index. Each partition is disposed
    # before the next one; the global census/selection lives with the publisher.
    for bucket in range(PARTITIONS):
        relevant = [
            (root, body) for root, body in prepared if str(bucket) in body["partitions"]
        ]
        if not relevant:
            continue
        with storage.index(directory) as db:
            db.execute(
                "CREATE TABLE event_anchors (anchor TEXT PRIMARY KEY,ordering_id TEXT,sha TEXT)"
            )
            for root, body in relevant:
                for ref in storage.iter_tree(root, body["partitions"][str(bucket)]):
                    checkpoint()
                    census["indexed_references"] += 1
                    storage.put(
                        db,
                        ref["id"],
                        dict(ref, path=body["source"]),
                        content_sha=ref["content_sha256"],
                    )
                    anchor = ref.get("event_anchor")
                    if anchor:
                        prior = db.execute(
                            "SELECT ordering_id,sha FROM event_anchors WHERE anchor=?",
                            (anchor,),
                        ).fetchone()
                        if prior is None:
                            db.execute(
                                "INSERT INTO event_anchors VALUES (?,?,?)",
                                (anchor, ref["id"], ref["content_sha256"]),
                            )
                        elif prior != (ref["id"], ref["content_sha256"]):
                            db.execute(
                                "UPDATE records SET conflicted=1 WHERE id IN (?,?)",
                                (prior[0], ref["id"]),
                            )
            db.execute(
                "CREATE TABLE positions (id TEXT PRIMARY KEY,cell TEXT,first_at REAL,last_at REAL)"
            )
            for raw, conflict in db.execute(
                "SELECT body,conflicted FROM records ORDER BY id"
            ):
                ref = json.loads(raw)
                db.execute(
                    "INSERT INTO positions VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_at=max(last_at,excluded.last_at)",
                    (ref["position_key"], ref["cell"], ref["at"], ref["at"]),
                )
                census["conflicting_rows" if conflict else "deduplicated"] += 1
            for key, cell, first, last in db.execute(
                "SELECT id,cell,first_at,last_at FROM positions ORDER BY first_at,id"
            ):
                yield Position(db, key, cell, first, last, checkpoint)
