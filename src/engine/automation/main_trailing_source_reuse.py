"""Report-owned reuse of native normalized inputs and byte identity proofs.

An unchanged source epoch can reuse its native SHA attestation. This module
never reuses a semantic verdict, changes a policy, or scans an unproved large
source. Original source gaps and original extraction provenance remain intact.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from src.engine.lifecycle import research_storage as storage
from src.engine.infrastructure.validation_digest_session import identity, _sha
from src.engine.scalping.pre_submit_delay_initial_policy import digest

SCHEMA = "main_trailing_native_input_reuse_v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_UNPROVED_BYTES = 32 * 1024 * 1024
_REPLAY = ContextVar("trailing_frozen_input_replay", default=None)


class InputPending(ValueError):
    pass


def file_stat(path):
    path = Path(path)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("trailing_reuse_source_path_invalid")
    value = path.stat()
    if not stat.S_ISREG(value.st_mode) or value.st_uid != os.getuid():
        raise ValueError("trailing_reuse_source_owner_invalid")
    return [
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    ]


def read_json(path, *, private=False, limit=MAX_JSON_BYTES):
    path = Path(path)
    before = file_stat(path)
    if before[2] > limit or (private and path.stat().st_mode & 0o077):
        raise ValueError("trailing_reuse_proof_budget_or_permissions_invalid")
    raw = path.read_bytes()
    if len(raw) != before[2] or file_stat(path) != before:
        raise InputPending("trailing_reuse_proof_changed")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def sealed(path):
    value, sha = read_json(path)
    key = (
        "artifact_content_sha256"
        if "artifact_content_sha256" in value
        else "artifact_sha256"
    )
    if value.get(key) != digest({k: v for k, v in value.items() if k != key}):
        raise ValueError("trailing_reuse_native_seal_invalid")
    return value, sha


def _cursor_issuer_path(root, day, generation, path, filename):
    """Resolve only the native data mount; reject links below that boundary."""
    relative = (
        Path("report/main_market_weakness_research") / day / generation / filename
    )
    path = Path(path)
    if not path.is_absolute() or path.parts[-len(relative.parts) :] != relative.parts:
        raise ValueError("trailing_reuse_identity_issuer_path_invalid")
    mount = path.parents[len(relative.parts) - 1]
    if mount.resolve(strict=True) != root:
        raise ValueError("trailing_reuse_identity_issuer_path_invalid")
    child = path
    while child != mount:
        if child.is_symlink():
            raise ValueError("trailing_reuse_source_path_invalid")
        child = child.parent
    return root / relative


def _receipt_stat(value):
    return [value[key] for key in ("device", "inode", "size", "mtime_ns", "ctime_ns")]


def archived_master_matches(root, source_date, path, generation):
    """Authenticate a frozen master's exact bytes after bounded gzip storage."""
    path = Path(path)
    if (
        path.exists()
        or path.parent
        != Path(root).resolve() / "report/micro_reversion_economic_reference"
        or not re.fullmatch(
            r"micro_reversion_symbol_master_\d{4}-\d{2}-\d{2}\.json", path.name
        )
    ):
        return None
    if path.is_symlink():
        return False
    from datetime import date
    import gzip
    import zlib
    from src.engine.infrastructure.validation_digest_session import ACTIVE

    try:
        day = path.name[-15:-5]
        if date.fromisoformat(day).isoformat() != day or day > source_date:
            return False
        archive = Path(str(path) + ".gz")
        before = file_stat(archive)
        size = generation.get("size")
        if (
            generation.get("path") != path.name
            or generation.get("schema") is not None
            or type(size) is not int
            or not 0 < size <= MAX_JSON_BYTES
            or before[2] > MAX_JSON_BYTES
        ):
            return False
        session = ACTIVE.get()
        if session is not None and session.native_read_budget is not None:
            charge = before[2] + size
            if charge > session.native_read_budget["remaining"]:
                raise InputPending("trailing_reuse_master_read_budget")
            session.native_read_budget["remaining"] -= charge
        with gzip.open(archive, "rb") as handle:
            raw = handle.read(size + 1)
        return (
            len(raw) == size
            and hashlib.sha256(raw).hexdigest() == generation.get("sha256")
            and file_stat(archive) == before
        )
    except (OSError, ValueError, TypeError, EOFError, zlib.error):
        return False


def collect_proofs(data_root, original_manifest_path):
    """Verify native issuers; return only matching current byte epochs."""
    root = Path(data_root).resolve(strict=True)
    origin = Path(original_manifest_path)
    manifest, origin_sha = sealed(origin)
    source_date, target_date = manifest["source_date"], manifest["target_date"]
    if manifest.get("schema") != "main_all_scope_exit_input_manifest_v2":
        raise ValueError("trailing_reuse_original_manifest_invalid")
    from .main_trailing_source_assembler import VOTE_INVENTORY_SCHEMA
    from .main_trailing_source_store import SCHEMA as INDEX_SCHEMA

    expected = {}
    logical = {}
    for key in ("assembly_inventory_ref", "source_generations_ref"):
        for row in storage.iter_tree(origin.parent, manifest[key]):
            path = str(Path(row["path"]).absolute())
            generation = row["generation"]
            # These native digests describe a date-scoped view or an index
            # chain, not the source's physical bytes. Never admit them into a
            # full-byte digest cache, even when they share a path with a raw
            # source reference. Their owners validate them in proof_session.
            archived_snapshot = (
                Path(path).parent == root / "report/monitor_snapshots"
                and Path(path).suffix == ".json"
                and not Path(path).exists()
                and Path(path + ".gz.archive_receipt.json").is_file()
            )
            archived_master = (
                Path(path).parent == root / "report/micro_reversion_economic_reference"
                and Path(path).name.startswith("micro_reversion_symbol_master_")
                and Path(path).suffix == ".json"
                and not Path(path).exists()
                and Path(path + ".gz").exists()
            )
            cost_index = (
                Path(path).name == "index.json"
                and Path(path).parent.parent
                == root / "runtime/initial_quantity_research_costs"
            )
            if (
                generation.get("schema")
                in {VOTE_INVENTORY_SCHEMA, INDEX_SCHEMA + ":generation"}
                or archived_snapshot
                or archived_master
                or cost_index
            ):
                logical[(path, digest(generation))] = dict(
                    path=path, generation=generation
                )
                continue
            old = expected.get(path)
            if old is not None and old != generation:
                # Native registry custody adds diagnostic fields to the same
                # original byte generation; it cannot change its byte identity.
                if any(
                    old.get(k) != generation.get(k) for k in ("path", "size", "sha256")
                ):
                    raise ValueError("trailing_reuse_original_source_conflict")
            expected[path] = generation
    proofs = {}

    def add(name, observed, issuer_path, issuer_sha, kind):
        name = str(Path(name).absolute())
        generation = expected.get(name)
        if generation is None:
            return
        try:
            current = file_stat(name)
            if (
                not Path(name).is_relative_to(root)
                or current != list(observed)
                or current[2] != generation["size"]
            ):
                return
        except (OSError, ValueError, KeyError, TypeError):
            return
        body = dict(
            schema=SCHEMA + ":byte_proof",
            kind=kind,
            source_date=source_date,
            path=name,
            generation=generation,
            stat=current,
            issuer_path=str(issuer_path),
            issuer_sha256=issuer_sha,
            original_manifest_sha256=origin_sha,
        )
        proofs[name] = {**body, "proof_sha256": digest(body)}

    # The snapshot writer seals its digest while writing. Reuse that existing
    # byte proof rather than requiring a second research producer to attest it.
    from src.engine.infrastructure.validation_digest_session import (
        _native_bytes,
        _native_proof_path,
    )

    for name, generation in expected.items():
        if (
            Path(name).parent != root / "report/monitor_snapshots"
            or Path(name).suffix != ".json"
        ):
            continue
        proof = _native_bytes(root, name)
        if proof is not None and proof["generation"] == generation:
            proof_path = _native_proof_path(root, name)
            _, sha = read_json(proof_path, private=True, limit=4096)
            add(
                name,
                proof["source_stat"],
                proof_path,
                sha,
                "native_monitor_snapshot_writer",
            )

    # The approved frozen input binds exact enrollment bytes. Their byte proofs
    # survive reader changes; current semantic extraction bindings do not.
    from .main_trailing_completed_store import original_byte_observations

    for name, generation in expected.items():
        path = Path(name)
        if (
            path.parent.parent.parent == root / "report/main_trailing_completed_source"
            and path.parent.name == "generations"
            and path.name.startswith("offline-")
        ):
            for proof in original_byte_observations(root, path, generation):
                source = proof["path"]
                if (
                    Path(source).is_file()
                    and expected.get(source) == proof["generation"]
                ):
                    add(
                        source,
                        _receipt_stat(proof["source_epoch"]),
                        proof["issuer_path"],
                        proof["issuer_sha256"],
                        "native_completed_source_enrollment",
                    )

    # A native issued research report binds each SHA to its observed stat epoch.
    pointer_path = (
        root
        / "threshold_cycle/main_stop_confirmation"
        / f"committed_{source_date}.json"
    )
    if pointer_path.is_file():
        pointer, _ = read_json(pointer_path, limit=1024 * 1024)
        generation = pointer.get("generation", "")
        if (
            pointer.get("schema") != "main_stop_committed_v1"
            or pointer.get("source_date") != source_date
            or pointer.get("target_date") != target_date
            or re.fullmatch("[0-9a-f]{64}", str(generation)) is None
        ):
            raise ValueError("trailing_reuse_stop_proof_unbound")
        report_path = pointer_path.parent / "generations" / generation / "report.json"
        report, sha = read_json(report_path)
        if (
            sha != pointer.get("report_byte_sha256")
            or report.get("schema") != "main_stop_research_v1"
            or report.get("source_date") != source_date
            or report.get("target_date") != target_date
        ):
            raise ValueError("trailing_reuse_stop_proof_changed")
        for name, gen in report.get("source_inventory", {}).items():
            bound = expected.get(name)
            if bound and all(
                bound.get(k) == gen.get(k) for k in ("path", "size", "sha256")
            ):
                observed = report.get("dependency_stats", {}).get(name)
                if observed is not None:
                    add(
                        name,
                        observed,
                        report_path,
                        sha,
                        "native_paired_hash_and_identity",
                    )

    # This identity observation predates the original full-SHA publication.
    # Exact current metadata equality brackets that publication in an unchanged
    # native-owned byte epoch. Source-gap economics in the issuer are irrelevant
    # to this byte proof and are never converted into semantic success.
    origin_epoch = min(origin.stat().st_mtime_ns, origin.stat().st_ctime_ns)
    for day in manifest["consumed_dates"]:
        cursor_path = (
            root / "report/main_market_weakness_research" / day / "cursor.json"
        )
        if not cursor_path.is_file():
            continue
        cursor, _ = read_json(cursor_path)
        descriptor = cursor.get("source_descriptor", {})
        if (
            cursor.get("schema") != "main_market_weakness_research_v1:cursor"
            or cursor.get("source_date") != day
            or descriptor.get("source_date") != day
            or cursor.get("generation") != digest(descriptor)
        ):
            raise ValueError("trailing_reuse_identity_cursor_invalid")
        if cursor.get("status") == "in_progress":
            # The native writer publishes terminal references only on commit.
            # This optional issuer proves no bytes yet; the unproved intake
            # bound and other immutable native proofs remain mandatory.
            continue
        proof_path = _cursor_issuer_path(
            root,
            day,
            cursor["generation"],
            cursor["manifest_path"],
            "source_manifest.json",
        )
        terminal_path = _cursor_issuer_path(
            root, day, cursor["generation"], cursor["terminal_path"], "terminal.json"
        )
        observed, sha = sealed(proof_path)
        terminal, _ = sealed(terminal_path)
        if (
            observed.get("schema") != "main_market_weakness_research_v1:source_manifest"
            or observed.get("source_date") != day
            or observed.get("sources") != descriptor.get("sources")
            or terminal.get("generation") != cursor["generation"]
            or terminal.get("source_manifest_sha256")
            != observed["artifact_content_sha256"]
            or terminal.get("source_date") != day
            or terminal.get("status") not in {"completed", "completed_with_source_gaps"}
        ):
            raise ValueError("trailing_reuse_identity_issuer_unbound")
        if (
            max(proof_path.stat().st_ctime_ns, terminal_path.stat().st_ctime_ns)
            > origin_epoch
        ):
            continue
        for source in observed["sources"]:
            for item in [source, *source.get("aliases", [])]:
                try:
                    add(
                        item["path"],
                        _receipt_stat(item),
                        proof_path,
                        sha,
                        "prior_native_identity_and_original_hash_epoch",
                    )
                except (KeyError, TypeError):
                    continue

    # Native full-byte observations may re-attest a metadata-only preservation
    # repair. They are not validator results; current identities and the original
    # sealed SHA must still match. No trading/quote freshness TTL is changed.
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    directory = root / "runtime/validation_digests/transition"
    for path in sorted(
        directory.glob("*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True
    )[:32]:
        if re.fullmatch("[0-9a-f]{64}.json", path.name) is None:
            continue
        try:
            value, sha = read_json(path, private=True, limit=512 * 1024)
            payload = value["payload"]
            binding = payload["binding"]
            if (
                value["sha256"] != _sha(payload)
                or binding.get("role") != "transition"
                or binding.get("boot_id") != boot
                or binding.get("resolved_root") != str(root)
            ):
                continue
            for name, entry in payload["entries"].items():
                gen = expected.get(name)
                if (
                    gen
                    and entry.get("digest") == gen.get("sha256")
                    and entry.get("identity") == identity(name)
                ):
                    add(
                        name,
                        entry["identity"][2:7],
                        path,
                        sha,
                        "native_full_byte_observation",
                    )
        except (OSError, ValueError, KeyError, TypeError):
            continue
    unproved = []
    for name, generation in expected.items():
        if name in proofs:
            continue
        current = file_stat(name)
        unproved.append(dict(path=name, size=current[2], generation=generation))
    return dict(
        schema=SCHEMA + ":proof_catalog",
        source_date=source_date,
        target_date=target_date,
        original_manifest=str(origin),
        original_manifest_sha256=origin_sha,
        proofs=proofs,
        unproved=unproved,
        logical_sources=list(logical.values()),
        unproved_bytes=sum(row["size"] for row in unproved),
        semantic_verdict_reused=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
    )


@contextmanager
def proof_session(data_root, original_manifest_path):
    """Admit byte proofs only after native issuer checks, before any raw read."""
    from src.engine.infrastructure.validation_digest_session import (
        ACTIVE,
        postclose_session,
    )

    catalog = collect_proofs(data_root, original_manifest_path)
    if catalog["unproved_bytes"] > MAX_UNPROVED_BYTES:
        large = [
            row["path"] for row in catalog["unproved"] if row["size"] > 1024 * 1024
        ]
        raise InputPending(
            "trailing_reuse_native_source_proof_missing:" + ",".join(large[:8])
        )

    def admit(session):
        for name, proof in catalog["proofs"].items():
            session.admit_native_generation(
                name,
                proof["generation"],
                proof["stat"],
                proof_sha256=proof["proof_sha256"],
            )

    @contextmanager
    def bounded(session):
        prior = session.native_read_budget
        if prior is None:
            session.native_read_budget = dict(remaining=MAX_UNPROVED_BYTES)
        try:
            admit(session)
            from .main_trailing_source_assembler import source_generation_matches

            for row in catalog.get("logical_sources", []):
                if not source_generation_matches(
                    data_root, catalog["source_date"], row["path"], row["generation"]
                ):
                    raise InputPending(
                        "trailing_reuse_logical_source_changed:" + row["path"]
                    )
            yield catalog
        finally:
            session.native_read_budget = prior

    active = ACTIVE.get()
    if (
        active is not None
        and active.binding["role"] == "postclose"
        and active.data_root.resolve() == Path(data_root).resolve()
    ):
        with bounded(active):
            yield catalog
    else:
        with (
            postclose_session(data_root, catalog["source_date"]) as session,
            bounded(session),
        ):
            yield catalog


def _generation(path):
    value, sha = read_json(path)
    return value, dict(path=Path(path).name, size=Path(path).stat().st_size, sha256=sha)


def approved_origin(data_root, original_manifest_path):
    """The frozen holding handoff owns this exact original input epoch."""
    root = Path(data_root).resolve()
    origin = Path(original_manifest_path).resolve()
    manifest, origin_gen = _generation(origin)
    holding_path = (
        root
        / "report/monitor_snapshots"
        / f"holding_exit_observation_{manifest['source_date']}.json"
    )
    holding, holding_gen = _generation(holding_path)
    extension = holding.get("all_scope_trailing_research") or {}
    report_path = Path(extension["report_path"])
    report, report_gen = _generation(report_path)
    if (
        holding.get("date") != manifest["source_date"]
        or (holding.get("meta") or {}).get("snapshot_profile") != "postclose_exit"
        or extension.get("allowed_runtime_apply") is not False
        or extension.get("status") != "complete"
        or extension.get("scope_count")
        != (report.get("scope") or {}).get("scope_count")
        or extension.get("initial_policy_sha256")
        != (report.get("initial_policy") or {}).get("policy_sha256")
        or extension.get("input_window_generation_sha256")
        != report.get("input_window_generation_sha256")
        or extension.get("report_generation") != report_gen
        or report.get("schema") != "main_all_scope_exit_research_v2"
        or report.get("status") != "complete"
        or report.get("allowed_runtime_apply") is not False
        or report.get("source_date") != manifest["source_date"]
        or report.get("target_date") != manifest["target_date"]
        or Path(report["input_manifest_path"]).resolve() != origin
        or report.get("input_manifest_generation") != origin_gen
        or manifest.get("source_data_root") != str(root)
    ):
        raise ValueError("trailing_reuse_original_epoch_not_approved")
    sealed(origin)
    sealed(report_path)
    return dict(
        schema=SCHEMA,
        mode="approved_frozen_input_epoch",
        original_manifest=str(origin),
        original_manifest_generation=origin_gen,
        original_holding_generation=holding_gen,
        original_report_generation=report_gen,
        original_extraction_code_contract=manifest["assembly_code_contract_sha256"],
        semantic_verdict_reused=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
    )


def prepare(data_root, original_manifest_path, output_root):
    """Copy only normalized objects, preserving every original gap and field."""
    import time
    from src.engine.automation.main_trailing_all_scope_research import code_contract
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic

    root = Path(data_root).resolve()
    origin = Path(original_manifest_path).resolve()
    manifest, _ = sealed(origin)
    binding = approved_origin(root, origin)
    signature = digest([SCHEMA, binding, code_contract()])
    output = Path(output_root).resolve() / "generations" / signature
    if (
        output.is_relative_to(root)
        or output == origin.parent
        or output.is_relative_to(origin.parent)
    ):
        raise ValueError("trailing_reuse_output_not_isolated")
    with proof_session(root, origin) as catalog:
        files = []
        total = 0
        for path in origin.parent.rglob("*.json"):
            relative = path.relative_to(origin.parent)
            if relative.parts[0] in {
                "scratch",
                "holding_request_index",
            } or relative == Path("manifest.json"):
                continue
            size = file_stat(path)[2]
            if size > MAX_JSON_BYTES:
                raise InputPending("trailing_reuse_normalized_partition_required")
            total += size
            files.append((path, relative))
        from src.engine.lifecycle import research_disk_budget as disk
        import tempfile

        files.sort(key=lambda item: str(item[1]))
        inventory = [(str(relative), file_stat(path)) for path, relative in files]
        inventory_sha = digest(inventory)
        output.mkdir(parents=True, exist_ok=True)
        checkpoint = output / "copy_checkpoint.json"
        expected = dict(
            schema="main_trailing_normalized_copy_v1",
            input_generation=signature,
            inventory_sha256=inventory_sha,
            file_count=len(files),
            total_bytes=total,
        )
        if checkpoint.exists():
            prior, _ = sealed(checkpoint)
            if any(prior.get(key) != value for key, value in expected.items()):
                raise InputPending("trailing_reuse_copy_source_changed")

        def progress(count, size, complete):
            value = dict(
                **expected, verified_files=count, verified_bytes=size, complete=complete
            )
            value["artifact_sha256"] = digest(value)
            _atomic(checkpoint, value)

        started = time.monotonic()
        copied = verified = count = 0
        # The existing per-batch bound stays unchanged. Durable native files
        # are resumable checkpoints; no manifest is issued for a partial copy.
        with disk.use(output):
            progress(0, 0, False)
            for (path, relative), (_, before) in zip(files, inventory):
                destination = output / relative
                if file_stat(path) != before:
                    raise InputPending("trailing_reuse_original_projection_changed")
                with path.open("rb") as stream:
                    raw = stream.read(before[2] + 1)
                if len(raw) != before[2] or file_stat(path) != before:
                    raise InputPending("trailing_reuse_original_projection_changed")
                if destination.exists() or destination.is_symlink():
                    observed = file_stat(destination)
                    with destination.open("rb") as stream:
                        previous = stream.read(len(raw) + 1)
                    if (
                        observed[2] != len(raw)
                        or previous != raw
                        or file_stat(destination) != observed
                    ):
                        raise ValueError(
                            "trailing_reuse_normalized_generation_collision"
                        )
                else:
                    if copied + len(raw) > disk.INDEX_LIMIT:
                        progress(count, verified, False)
                        raise InputPending("trailing_reuse_copy_checkpoint_required")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with disk.atomic(destination, len(raw)):
                        fd, temporary = tempfile.mkstemp(
                            dir=destination.parent, prefix=".copy-"
                        )
                        try:
                            with os.fdopen(fd, "wb") as stream:
                                stream.write(raw)
                                stream.flush()
                                os.fsync(stream.fileno())
                            if file_stat(path) != before:
                                raise InputPending(
                                    "trailing_reuse_original_projection_changed"
                                )
                            os.replace(temporary, destination)
                        finally:
                            if os.path.exists(temporary):
                                os.unlink(temporary)
                    copied += len(raw)
                    pause = copied / (8 * 1024 * 1024) - (time.monotonic() - started)
                    if pause > 0:
                        time.sleep(min(pause, 0.5))
                verified += len(raw)
                count += 1
            if [(str(rel), file_stat(path)) for path, rel in files] != inventory:
                raise InputPending("trailing_reuse_original_projection_changed")
            progress(count, verified, True)
        reused = {
            **manifest,
            "assembly_input_generation_sha256": signature,
            "reuse_origin": binding,
        }
        reused.pop("artifact_sha256", None)
        reused["artifact_sha256"] = digest(reused)
        target = output / "manifest.json"
        if target.exists():
            if read_json(target)[0] != reused:
                raise ValueError("trailing_reuse_manifest_collision")
        else:
            _atomic(target, reused)
        validate_manifest(reused, output)
        return target


def validate_manifest(manifest, assembly_root):
    """Original extraction stays original; current native replay runs anew."""
    from src.engine.automation.main_trailing_all_scope_research import code_contract

    binding = manifest.get("reuse_origin")
    if not isinstance(binding, dict) or binding.get("schema") != SCHEMA:
        raise ValueError("trailing_reuse_binding_invalid")
    original_path = Path(binding["original_manifest"])
    original, _ = sealed(original_path)
    if approved_origin(manifest["source_data_root"], original_path) != binding:
        raise ValueError("trailing_reuse_approved_origin_changed")
    signature = digest([SCHEMA, binding, code_contract()])
    expected = {
        **original,
        "assembly_input_generation_sha256": signature,
        "reuse_origin": binding,
    }
    expected.pop("artifact_sha256", None)
    expected["artifact_sha256"] = digest(expected)
    if manifest != expected or Path(assembly_root).name != signature:
        raise ValueError("trailing_reuse_input_fields_or_replay_code_changed")


def _vote_prefix_unchanged(path, generation, source_date):
    """Exact old bytes and native later-session appends, bounded to16MiB."""
    from src.engine.ai.holding_exit_vote import _iter_path_events, PATH_MAX_STORE_BYTES

    path = Path(path)
    before = file_stat(path)
    size = generation["size"]
    if before[2] > PATH_MAX_STORE_BYTES or not 0 <= size <= before[2]:
        return False
    with path.open("rb") as handle:
        sha = hashlib.sha256()
        remaining = size
        last = b""
        while remaining:
            block = handle.read(min(65536, remaining))
            remaining -= len(block)
            sha.update(block)
            if not block:
                return False
            last = block[-1:]
    if sha.hexdigest() != generation["sha256"] or size and last != b"\n":
        return False
    if size == before[2]:
        return file_stat(path) == before
    with path.open("r", encoding="utf-8") as handle:
        first = json.loads(handle.readline(2 * 1024 * 1024 + 1))
        position = first["position_key"]

        class Tail:
            def fileno(self):
                return handle.fileno()

            def seek(self, offset):
                return handle.seek(size + offset)

            def readline(self, limit):
                return handle.readline(min(limit, 2 * 1024 * 1024 + 1))

        for row in _iter_path_events(Tail(), position):
            if row.get("session_key", "") <= source_date:
                return False
    return file_stat(path) == before


def frozen_cost_declaration(data_root, day):
    """Resolve only an active, approved replay's original research-cost scope."""
    active = _REPLAY.get()
    if active is None:
        return None
    manifest, assembly_root, cache = active
    root = Path(data_root).resolve()
    if (
        root
        != Path(
            manifest.get("holding_research_cost_data_root")
            or manifest["source_data_root"]
        ).resolve()
    ):
        return None
    if day not in manifest["consumed_dates"]:
        return None
    if "cost_index_generations" not in cache:
        cache["cost_index_generations"] = {
            row["path"]: row["generation"]
            for row in storage.iter_tree(
                assembly_root, manifest["assembly_inventory_ref"]
            )
            if Path(row["path"]).name == "index.json"
            and Path(row["path"]).parent.parent
            == root / "runtime/initial_quantity_research_costs"
        }
    path = root / "runtime/initial_quantity_research_costs" / day / "index.json"
    generation = cache["cost_index_generations"].get(str(path))
    if generation is None:
        return False
    from src.engine.lifecycle.holding_research_cost import frozen_index

    body = frozen_index(root, path, generation)
    return dict(
        source_dates=[
            frozen_official_source(
                root, root / "runtime/holding_broker_cost_sources" / (d + ".json")
            )[2]
            for d in body["source_dates"]
        ],
        receipts=[
            dict(record_id=record, content_sha256=sha)
            for record, sha in body["receipts"].items()
        ],
    )


def frozen_official_source(data_root, path):
    """Resolve the exact approved cost bytes after a proven later-window append."""
    active = _REPLAY.get()
    if active is None:
        return None
    manifest, assembly_root, cache = active
    root = Path(data_root).resolve()
    path = Path(path)
    if (
        root
        != Path(
            manifest.get("holding_research_cost_data_root")
            or manifest["source_data_root"]
        ).resolve()
        or path.parent != root / "runtime/holding_broker_cost_sources"
    ):
        return None
    if "official_original_inventory" not in cache:
        cache["official_original_inventory"] = {
            row["path"]: row["generation"]
            for row in storage.iter_tree(
                assembly_root, manifest["assembly_inventory_ref"]
            )
        }
    generation = cache["official_original_inventory"].get(str(path))
    if generation is None:
        raise InputPending("trailing_reuse_official_source_unbound")
    prior = cache.get(("official_source", str(path)))
    if prior is not None and prior[0] == (file_stat(path), file_stat(prior[1][0])):
        return prior[1]
    from src.engine.lifecycle import broker_cost_source as official

    def charge(size):
        total = cache.get("official_source_bytes", 0) + size
        if total > MAX_UNPROVED_BYTES:
            raise InputPending("trailing_reuse_official_source_read_budget")
        from src.engine.infrastructure.validation_digest_session import ACTIVE

        session = ACTIVE.get()
        if session is not None and session.native_read_budget is not None:
            if size > session.native_read_budget["remaining"]:
                raise InputPending("trailing_reuse_official_source_read_budget")
            session.native_read_budget["remaining"] -= size
        cache["official_source_bytes"] = total

    raw = official._source_raw(path, account_read=charge)
    if hashlib.sha256(raw).hexdigest() == generation["sha256"]:
        try:
            source = json.loads(raw)
        except (ValueError, UnicodeError):
            source = {}
        if not isinstance(source, dict):
            source = {}
        physical = path
    else:
        from src.engine.lifecycle.holding_research_cost import frozen_index

        candidates = set()
        for name, gen in cache["official_original_inventory"].items():
            index = Path(name)
            if (
                index.name != "index.json"
                or index.parent.parent
                != root / "runtime/initial_quantity_research_costs"
            ):
                continue
            body = frozen_index(root, index, gen)
            if path.stem not in body["source_dates"]:
                continue
            for sha in body["receipts"].values():
                receipt_path = index.parent / "generations" / (sha + ".json")
                charge(file_stat(receipt_path)[2])
                receipt, _ = read_json(receipt_path)
                if digest(receipt) != sha:
                    raise InputPending("trailing_reuse_original_cost_receipt_changed")
                candidates.update(
                    part["source_sha256"]
                    for part in receipt.get("sources", [])
                    if part.get("source_date") == path.stem
                )
        matches = []
        for logical in candidates:
            if re.fullmatch("[0-9a-f]{64}", str(logical)) is None:
                raise InputPending("trailing_reuse_original_cost_reference_invalid")
            archive = path.parent / "generations" / path.stem / (logical + ".json")
            if not archive.exists():
                continue
            old_raw = official._source_raw(archive, account_read=charge)
            if hashlib.sha256(old_raw).hexdigest() == generation["sha256"]:
                matches.append(
                    (archive, official.validate(json.loads(old_raw), path.stem))
                )
        if len(matches) != 1:
            raise InputPending("trailing_reuse_original_cost_bytes_missing")
        physical, source = matches[0]
    reference = dict(
        source_date=path.stem,
        sha256=generation["sha256"],
        source_sha256=source.get("source_sha256"),
    )
    old_raw = official.declared_source_bytes(root, reference, account_read=charge)
    if len(old_raw) != generation["size"]:
        raise InputPending("trailing_reuse_original_cost_size_changed")
    result = (physical, generation, reference)
    cache[("official_source", str(path))] = (
        (file_stat(path), file_stat(physical)),
        result,
    )
    return result


def verify_frozen_inventory(manifest, assembly_root):
    """Revalidate the original cohort without making future journals inputs."""
    from .main_trailing_source_assembler import (
        input_inventory,
        source_generation_matches,
        VOTE_INVENTORY_SCHEMA,
        universe,
    )

    validate_manifest(manifest, assembly_root)
    root = Path(manifest["source_data_root"]).resolve()
    source_date = manifest["source_date"]
    # Native inventory owns cohort selection and its bounded unindexed budget.
    # Total physical journal growth must not reject an already indexed cohort.
    _, master = universe(root, source_date)
    current = input_inventory(
        root,
        manifest["consumed_dates"],
        master["path"],
        root
        / "runtime/policy_bootstrap"
        / f"runtime_policy_bootstrap_{source_date}.json",
        cost_data_root=manifest.get("holding_research_cost_data_root"),
        include_legacy_auxiliary=True,
    )
    original = list(
        storage.iter_tree(assembly_root, manifest["assembly_inventory_ref"])
    )
    old = {
        row["path"]: row["generation"]
        for row in original
        if not row["path"].endswith(".claims.jsonl")
    }
    new = {row["path"]: row["generation"] for row in current}
    # Cost correction publishes a new native index while retaining the exact
    # prior index and receipt bodies. Replay this approved frozen cohort against
    # those original dependencies, without importing the corrected economics.
    from src.engine.lifecycle.holding_research_cost import (
        frozen_index,
        inventory as cost_inventory,
    )
    from src.engine.lifecycle.broker_cost_source import source_path as cost_source_path

    cost_root = Path(manifest.get("holding_research_cost_data_root") or root).resolve()
    current_costs = set()
    frozen_costs = set()
    for day in manifest["consumed_dates"]:
        index = (
            cost_root / "runtime/initial_quantity_research_costs" / day / "index.json"
        )
        current_costs.update(str(p.resolve()) for p in cost_inventory(cost_root, [day]))
        if str(index) not in old:
            if index.exists():
                # Original absence is also a frozen scope. Validate a later
                # native publisher, but do not import its new research cohort.
                from src.engine.lifecycle.holding_window_generation import (
                    byte_generation,
                )

                frozen_index(cost_root, index, byte_generation(index))
            continue
        body = frozen_index(cost_root, index, old[str(index)])
        frozen_costs.add(str(index))
        frozen_costs.update(
            str(index.parent / "generations" / (sha + ".json"))
            for sha in body["receipts"].values()
        )
        frozen_costs.update(
            str(cost_source_path(cost_root, d)) for d in body["source_dates"]
        )
    if not frozen_costs <= set(old):
        raise InputPending("trailing_reuse_frozen_cost_inventory_unbound")
    for name in frozen_costs:
        if not source_generation_matches(cost_root, source_date, name, old[name]):
            raise InputPending("trailing_reuse_frozen_cost_source_changed:" + name)
    new = {
        name: generation
        for name, generation in new.items()
        if name not in current_costs
    }
    new.update((name, old[name]) for name in frozen_costs)
    for name, generation in old.items():
        alias = name + ".gz"
        if (
            name not in new
            and alias in new
            and archived_master_matches(root, source_date, name, generation)
        ):
            from src.engine.lifecycle.holding_window_generation import byte_generation

            if byte_generation(Path(alias)) != new[alias]:
                raise InputPending("trailing_reuse_archived_master_changed")
            # Storage changes no frozen cohort or source-generation identity.
            new.pop(alias)
            new[name] = generation
        candidate = new.get(name)
        if candidate is None and name.endswith(".jsonl.gz.archive_receipt.json"):
            from .main_trailing_source_store import NAMESPACES

            logical = Path(name.removesuffix(".gz.archive_receipt.json"))
            if (
                logical.parent.name in NAMESPACES
                and str(logical) in old
                and source_generation_matches(
                    root, source_date, logical, old[str(logical)]
                )
                and source_generation_matches(root, source_date, name, generation)
            ):
                continue  # Preserve exact issued metadata; it is not a new raw input.
        is_vote = Path(name).parent == root / "runtime/holding_path_votes"
        if (
            is_vote
            and generation.get("schema") != VOTE_INVENTORY_SCHEMA
            and (candidate is None or candidate.get("schema") == VOTE_INVENTORY_SCHEMA)
        ):
            try:
                if _vote_prefix_unchanged(name, generation, source_date):
                    continue
            except (OSError, ValueError, KeyError, TypeError):
                pass
        if candidate is None or not (
            candidate == generation
            or source_generation_matches(root, source_date, name, generation)
        ):
            raise InputPending("trailing_reuse_original_inventory_changed:" + name)
    if set(new) - set(old):
        raise InputPending("trailing_reuse_historical_inventory_added")


def frozen_registry_matches(root, source_date, path, generation):
    """Scope registry equivalence to actual owners in the sealed input epoch.

    The journal's original byte prefix and complete native hash chain remain
    mandatory. This never authorizes custody or changes a current owner state.
    """
    context = _REPLAY.get()
    if context is None:
        return None
    manifest, assembly_root, cache = context
    if (
        str(Path(root).resolve()) != manifest["source_data_root"]
        or source_date != manifest["source_date"]
    ):
        return False
    name = str(Path(path).resolve())
    if "registry_original" not in cache:
        original = Path(manifest["reuse_origin"]["original_manifest"])
        value, _ = sealed(original)
        cache["registry_original"] = next(
            (
                row["generation"]
                for row in storage.iter_tree(
                    original.parent, value["assembly_inventory_ref"]
                )
                if row["path"] == name
            ),
            None,
        )
    original = cache["registry_original"]
    if original is None or any(
        generation.get(key) != original.get(key) for key in ("path", "size", "sha256")
    ):
        return False
    if "owners" not in cache:
        owners = set()
        for part in storage.iter_tree(assembly_root, manifest["partitions_ref"]):
            payload, _ = sealed(storage.safe_path(assembly_root, part["path"]))
            if digest(payload) != part["artifact_sha256"]:
                raise ValueError("trailing_reuse_partition_changed")
            for position in payload["positions"]:
                keys = [
                    position.get("position_key"),
                    (position.get("source_reference") or {}).get("id"),
                    (position.get("holding_vote_replay_ref") or {}).get(
                        "original_position_key"
                    ),
                ]
                for key in keys:
                    record = str(key or "").removeprefix("record:")
                    if record.isdigit():
                        owners.add("main_scalping:" + record)
        cache["owners"] = frozenset(owners)
    current = file_stat(path)
    key = (tuple(current), digest(generation))
    if cache.get("registry_verified") == key:
        return True
    from src.engine.lifecycle.holding_research_cost import (
        historical_registry_generation_matches,
    )

    result = historical_registry_generation_matches(
        path, generation, source_date, protected_owners=cache["owners"]
    )
    if result:
        cache["registry_verified"] = key
    return result


@contextmanager
def replay_session(manifest, assembly_root):
    binding = manifest.get("reuse_origin")
    if not binding:
        if manifest.get("assembly_source_index_version"):
            from .main_trailing_source_store import native_input_session

            with native_input_session(
                manifest["source_data_root"], manifest["source_date"]
            ):
                yield
        else:
            yield
        return
    validate_manifest(manifest, assembly_root)
    token = _REPLAY.set((manifest, Path(assembly_root), {}))
    try:
        from .main_trailing_source_store import native_input_session

        with (
            native_input_session(manifest["source_data_root"], manifest["source_date"]),
            proof_session(manifest["source_data_root"], binding["original_manifest"]),
        ):
            yield
    finally:
        _REPLAY.reset(token)


def main(argv=None):
    """Explicit closed-session regeneration; never an automatic raw rebuild."""
    import argparse
    import time
    from .main_trailing_all_scope_research import run, code_contract
    from src.engine.infrastructure.validation_digest_session import postclose_session
    from src.engine.lifecycle.research_admission import direct_job
    from src.engine.lifecycle.research_disk_budget import use
    from src.engine.monitoring.main_trailing_currentness import issue

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--input-output-root", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    from datetime import date

    if not date.fromisoformat(args.source_date) < date.fromisoformat(args.target_date):
        raise ValueError("trailing_reuse_dates_invalid")
    data = args.data_root.resolve(strict=True)
    holding_path = (
        data
        / "report/monitor_snapshots"
        / f"holding_exit_observation_{args.source_date}.json"
    )
    holding, _ = read_json(holding_path)
    original_report, _ = sealed(
        Path(holding["all_scope_trailing_research"]["report_path"])
    )
    if (
        original_report["source_date"] != args.source_date
        or original_report["target_date"] != args.target_date
    ):
        raise ValueError("trailing_reuse_original_dates_changed")
    origin = Path(original_report["input_manifest_path"])
    approved_origin(data, origin)
    if not args.write:
        with proof_session(data, origin) as catalog:
            print(
                json.dumps(
                    dict(
                        status="byte_proof_preflight_only",
                        proof_count=len(catalog["proofs"]),
                        unproved_bytes=catalog["unproved_bytes"],
                        unproved_source_bytes_limit=MAX_UNPROVED_BYTES,
                        full_native_validation=False,
                        runtime_effect=False,
                        allowed_runtime_apply=False,
                    )
                )
            )
        return 0
    started = time.monotonic()
    report_root = data / "report/main_all_scope_trailing" / args.source_date
    with (
        postclose_session(data, args.source_date) as session,
        direct_job(data, "main_trailing_all_scope", args.source_date),
        use(report_root),
    ):
        manifest = prepare(data, origin, args.input_output_root)
        output = report_root / "generations" / manifest.parent.name
        report = run(
            manifest,
            input_root=manifest.parent,
            output_root=output,
            dry_run=False,
            resume=True,
        )
        path = output / f"research_{args.source_date}.json"
        currentness = issue(
            data,
            source_date=args.source_date,
            target_date=args.target_date,
            report_path=path,
        )
    print(
        json.dumps(
            dict(
                status=report["status"],
                report_path=str(path),
                code_contract_sha256=code_contract(),
                scope_count=report["scope"]["scope_count"],
                currentness_sha256=currentness["artifact_sha256"],
                full_native_validation=True,
                semantic_verdict_reused=False,
                original_extraction_provenance_preserved=True,
                unproved_source_bytes_limit=MAX_UNPROVED_BYTES,
                validation_io=session.stats,
                wall_seconds=time.monotonic() - started,
                runtime_effect=False,
                allowed_runtime_apply=False,
                actual_pid_consumed=False,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
