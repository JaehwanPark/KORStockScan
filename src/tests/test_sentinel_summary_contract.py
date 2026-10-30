"""Source-only migration tests; every writable source is an isolated fixture."""

import builtins
import hashlib
import inspect
import json
import runpy
import sys
from pathlib import Path
from types import FunctionType, ModuleType
from importlib.machinery import ModuleSpec

import pytest

from src.engine import buy_funnel_sentinel as B
from src.engine import pipeline_event_summary as P
from src.engine.monitoring import sentinel_summary_contract as C


def event(second):
    return dict(
        event_type="pipeline_event",
        emitted_at=f"2026-10-13T10:00:{second:02}",
        pipeline="ENTRY_PIPELINE",
        stage="blocked_overbought",
        stock_name="Alpha",
        stock_code="123456",
        record_id=second,
        fields={"reason": "stretched"},
    )


def predecessor(
    tmp_path, *, parser_callback=False, parser_contract=None, buy_owner=None
):
    raw = tmp_path / "raw.jsonl"
    raw.write_text(json.dumps(event(1)) + "\n")
    callbacks = (
        (P.default_reason_label, None)
        if parser_callback
        else (B._blocker_label_from_stage_fields, B._is_ignored_event)
    )
    options = dict(
        raw_path=raw,
        summary_dir=tmp_path / "summaries",
        target_date="2026-10-13",
        reason_labeler=callbacks[0],
        ignore_payload=callbacks[1],
        include_samples=False,
    )
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    manifest = Path(meta["manifest_path"])
    source = json.loads(manifest.read_text())
    parts = []
    for callback in callbacks:
        if callback is not None:
            parts.extend(
                (
                    inspect.getsource(callback),
                    (
                        (parser_contract or C.PREVIOUS_PARSER)
                        if parser_callback
                        else buy_owner or C.PREVIOUS_BUY_OWNER
                    ),
                )
            )
    source["callback_contract"] = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    source["parser_contract"] = parser_contract or C.PREVIOUS_PARSER
    source["checkpoint_digest"] = P.checkpoint_digest(source)
    manifest.write_text(json.dumps(source))
    return raw, options, manifest, manifest.read_bytes(), rows


def revise(manifest, **changes):
    source = json.loads(manifest.read_text())
    source.update(changes)
    source["checkpoint_digest"] = P.checkpoint_digest(source)
    manifest.write_text(json.dumps(source))


@pytest.mark.parametrize("oversized", [False, True])
def test_deployment_checks_migration_budget_without_mutating_checkpoint(
    tmp_path, oversized
):
    day = "2026-10-13"
    raw = tmp_path / "pipeline_events" / ("pipeline_events_" + day + ".jsonl")
    raw.parent.mkdir()
    raw.write_text(json.dumps(event(1)) + "\n")
    directory = tmp_path / "pipeline_event_summaries"
    _, meta = P.update_and_load_pipeline_event_summaries(
        raw_path=raw,
        summary_dir=directory,
        target_date=day,
        reason_labeler=B._blocker_label_from_stage_fields,
        ignore_payload=B._is_ignored_event,
        include_samples=False,
    )
    manifest = Path(meta["manifest_path"])
    parts = []
    for f in (B._blocker_label_from_stage_fields, B._is_ignored_event):
        parts.extend((inspect.getsource(f), C.PRE_TERMINAL_BUY_OWNER))
    revise(
        manifest,
        callback_contract=hashlib.sha256("\n".join(parts).encode()).hexdigest(),
        parser_contract=C.PRE_FORMAT_PARSER,
    )
    original = manifest.read_bytes()
    if oversized:
        with raw.open("ab") as stream:
            stream.truncate(raw.stat().st_size + C.LIMIT + 1)
        with pytest.raises(RuntimeError, match="append_budget_exceeded"):
            C.check_pending_migration(tmp_path, day)
    else:
        assert (
            C.check_pending_migration(tmp_path, day)["status"] == "migration_verified"
        )
        P.update_and_load_pipeline_event_summaries(
            raw_path=raw,
            summary_dir=directory,
            target_date=day,
            reason_labeler=B._blocker_label_from_stage_fields,
            ignore_payload=B._is_ignored_event,
            include_samples=False,
        )
        assert C.check_pending_migration(tmp_path, day)["status"] == "current_contract"
        return
    assert manifest.read_bytes() == original
    assert not (directory / "contract_migrations").exists()


@pytest.mark.parametrize("parser_callback", [False, True])
@pytest.mark.parametrize("append", [False, True])
def test_migration_preserves_original_and_reads_only_new_suffix(
    tmp_path, monkeypatch, parser_callback, append
):
    raw, options, manifest, original, rows = predecessor(
        tmp_path, parser_callback=parser_callback
    )
    start = raw.stat().st_size
    if append:
        with raw.open("a") as f:
            f.write(json.dumps(event(2)) + "\n")
    real_open = builtins.open
    reads = []

    class Tracked:
        def __init__(self, f):
            self.f = f

        def __getattr__(self, name):
            return getattr(self.f, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.f.__exit__(*args)

        def readline(self, *args):
            assert self.f.tell() >= start
            value = self.f.readline(*args)
            reads.append(len(value))
            return value

    def guarded(path, *args, **kwargs):
        f = real_open(path, *args, **kwargs)
        return Tracked(f) if Path(path) == raw and args and args[0] == "rb" else f

    monkeypatch.setattr(builtins, "open", guarded)
    result, meta = P.update_and_load_pipeline_event_summaries(**options)
    receipt = meta["contract_migration"]
    assert not meta["rebuilt"] and meta["start_raw_offset"] == start
    assert sum(row["event_count"] for row in result) == (2 if append else 1)
    assert sum(reads) == raw.stat().st_size - start
    assert Path(receipt["original_manifest_archive"]).read_bytes() == original

    assert receipt["original_manifest_sha256"] == hashlib.sha256(original).hexdigest()
    assert receipt["original_checkpoint"] == json.loads(original)["checkpoint_digest"]
    assert (
        receipt["from_parser"] == C.PREVIOUS_PARSER
        and receipt["to_parser"] == C.CURRENT_PARSER
    )
    committed = json.loads(manifest.read_text())
    assert committed["checkpoint_digest"] == P.checkpoint_digest(committed)
    unchanged = manifest.read_bytes()
    _, again = P.update_and_load_pipeline_event_summaries(**options)
    assert again["contract_migration"] == receipt
    assert Path(receipt["original_manifest_archive"]).read_bytes() == original


@pytest.mark.parametrize(
    "predecessor_owner", [C.PRE_TERMINAL_BUY_OWNER, C.PRE_SCOPE_EXTRACTION_BUY_OWNER]
)
def test_submit_terminal_successor_preserves_native_summary_callbacks_and_prefix(
    tmp_path, predecessor_owner
):
    import ast, subprocess

    old = subprocess.check_output(
        [
            "git",
            "-C",
            str(Path(B.__file__).resolve().parents[2]),
            "show",
            "75e0fbbf7:src/engine/buy_funnel_sentinel.py",
        ],
        text=True,
    )

    def definitions(source):
        return {
            n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef)
            and n.name
            in {"_blocker_label_from_stage_fields", "_is_ignored_event", "_safe_str"}
        }

    assert definitions(old) == definitions(Path(B.__file__).read_text())
    raw, options, manifest, original, _ = predecessor(
        tmp_path, parser_contract=C.PRE_FORMAT_PARSER, buy_owner=predecessor_owner
    )
    end = raw.stat().st_size
    with raw.open("a") as out:
        out.write(json.dumps(event(2)) + "\n")
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["start_raw_offset"] == end and meta["rebuilt"] is False
    assert sum(r["event_count"] for r in rows) == 2
    assert (
        Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes()
        == original
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"parser_contract": "unknown"}, "parser_predecessor_unverified"),
        ({"callback_contract": "unknown"}, "callback_predecessor_unverified"),
        ({"complete_through_raw_offset": 0}, "source_prefix_unverified"),
        ({"incomplete_tail": True}, "source_prefix_unverified"),
        ({"decode_errors": 1}, "source_prefix_unverified"),
        ({"summary_detail_level": "changed"}, "source_guard_failed"),
    ],
)
def test_invalid_predecessor_does_not_advance_or_archive(tmp_path, change, reason):
    raw, options, manifest, _, _ = predecessor(tmp_path)
    revise(manifest, **change)
    original = manifest.read_bytes()
    summary = Path(json.loads(original)["summary_path"]).read_bytes()
    with pytest.raises(RuntimeError, match=reason):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original
    assert Path(json.loads(original)["summary_path"]).read_bytes() == summary
    assert not (manifest.parent / "contract_migrations").exists()


def test_mutated_runtime_callback_dependency_is_rejected(tmp_path, monkeypatch):
    _, options, manifest, original, _ = predecessor(tmp_path)
    monkeypatch.setattr(B, "IGNORED_STOCK_NAMES", {"TEST"})
    with pytest.raises(RuntimeError, match="dependency_changed"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


def test_exact_current_parser_pin_rejects_unreviewed_source(tmp_path, monkeypatch):
    _, options, manifest, original, _ = predecessor(tmp_path)
    monkeypatch.setattr(C, "CURRENT_PARSER", "unreviewed")
    with pytest.raises(RuntimeError, match="parser_predecessor_unverified"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


@pytest.mark.parametrize("kind", ["truncate", "same_size_rewrite", "oversized_append"])
def test_raw_generation_and_migration_append_budget(tmp_path, kind):
    raw, options, manifest, original, _ = predecessor(tmp_path)
    if kind == "truncate":
        raw.write_bytes(b"")
    elif kind == "same_size_rewrite":
        raw.write_bytes(raw.read_bytes().replace(b"Alpha", b"Bravo"))
    else:
        with raw.open("ab") as f:
            f.truncate(raw.stat().st_size + C.LIMIT + 1)
    with pytest.raises(
        RuntimeError, match="source_prefix_unverified|append_budget_exceeded"
    ):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


def test_archive_conflict_is_fatal_before_source_append(tmp_path):
    raw, options, manifest, original, _ = predecessor(tmp_path)
    directory = manifest.parent / "contract_migrations"
    directory.mkdir()
    archive = directory / (
        manifest.name + "." + hashlib.sha256(original).hexdigest() + ".json"
    )
    archive.write_bytes(b"conflict")
    with pytest.raises(RuntimeError, match="archive_conflict"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original and archive.read_bytes() == b"conflict"


def test_incomplete_append_never_publishes_successor(tmp_path):
    raw, options, manifest, original, _ = predecessor(tmp_path)
    with raw.open("a") as f:
        f.write('{"unfinished":')
    with pytest.raises(RuntimeError, match="incomplete_source_prefix"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original
    assert len(list((manifest.parent / "contract_migrations").glob("*.json"))) == 1


def test_prepublication_same_size_raw_rewrite_is_rejected(tmp_path, monkeypatch):
    raw, options, manifest, original, _ = predecessor(tmp_path)
    real = C.archive_predecessor

    def alter(receipt, path):
        value = real(receipt, path)
        raw.write_bytes(raw.read_bytes().replace(b"Alpha", b"Bravo"))
        return value

    monkeypatch.setattr(C, "archive_predecessor", alter)
    with pytest.raises(RuntimeError, match="source_changed_before_publication"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


def test_prior_parser_intermediate_funnel_owner_remains_supported(tmp_path):
    _, options, manifest, _, _ = predecessor(tmp_path)
    parts = []
    for cb in (options["reason_labeler"], options["ignore_payload"]):
        parts.extend((inspect.getsource(cb), C.INTERMEDIATE_BUY_OWNER))
    revise(
        manifest,
        callback_contract=hashlib.sha256("\n".join(parts).encode()).hexdigest(),
    )
    _, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["contract_migration"]["from_parser"] == C.PREVIOUS_PARSER
    assert (
        meta["contract_migration"]["from_callback"]
        == hashlib.sha256("\n".join(parts).encode()).hexdigest()
    )
    assert not meta["rebuilt"]


def test_archive_io_failure_cannot_fall_back_to_raw_report(tmp_path, monkeypatch):
    _, options, manifest, original, _ = predecessor(tmp_path)

    def fail(*args, **kwargs):
        raise OSError("archive disk failure")

    monkeypatch.setattr(C.os, "open", fail)
    with pytest.raises(RuntimeError, match="archive_failed"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


def test_explicit_bootstrap_preserves_existing_revalidation_authority(tmp_path):
    _, options, manifest, _, _ = predecessor(tmp_path)
    revise(
        manifest,
        parser_contract=C.PRE_FORMAT_PARSER,
        callback_contract="changed_semantics",
    )
    original = manifest.read_bytes()
    with pytest.raises(RuntimeError, match="callback_predecessor_unverified"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original
    rows, meta = P.update_and_load_pipeline_event_summaries(
        **options, allow_bootstrap=True
    )
    assert meta["rebuilt"] and "contract_migration" not in meta
    assert sum(row["event_count"] for row in rows) == 1


def test_concurrent_append_is_left_for_next_owned_cursor(tmp_path, monkeypatch):
    raw, options, manifest, _, _ = predecessor(tmp_path)
    with raw.open("a") as f:
        f.write(json.dumps(event(2)) + "\n")
    end = raw.stat().st_size
    real = C.archive_predecessor

    def append(receipt, path):
        value = real(receipt, path)
        with raw.open("a") as f:
            f.write(json.dumps(event(3)) + "\n")
        return value

    monkeypatch.setattr(C, "archive_predecessor", append)
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["raw_offset"] == end < raw.stat().st_size
    assert sum(row["event_count"] for row in rows) == 2
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["raw_offset"] == raw.stat().st_size
    assert sum(row["event_count"] for row in rows) == 3


@pytest.mark.parametrize("target", ["archive", "directory"])
def test_predecessor_archive_rejects_symlink_without_publishing(tmp_path, target):
    _, options, manifest, original, _ = predecessor(tmp_path)
    directory = manifest.parent / "contract_migrations"
    if target == "directory":
        outside = tmp_path / "outside"
        outside.mkdir()
        directory.symlink_to(outside, target_is_directory=True)
    else:
        directory.mkdir()
        archive = directory / (
            manifest.name + "." + hashlib.sha256(original).hexdigest() + ".json"
        )
        archive.symlink_to(manifest)
    summary = Path(json.loads(original)["summary_path"])
    prior_summary = summary.read_bytes()
    with pytest.raises(RuntimeError, match="archive_failed"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original and summary.read_bytes() == prior_summary


def _intercept_real_funnel_cli(monkeypatch, inspect_callbacks):
    """Stop the real -m entry point before any runtime source or report access."""

    class Intercepted(Exception):
        pass

    calls = []

    def intercept(**options):
        calls.append(options)
        inspect_callbacks(options)
        raise Intercepted

    monkeypatch.setattr(P, "update_and_load_pipeline_event_summaries", intercept)
    monkeypatch.setattr(
        sys,
        "argv",
        ["buy_funnel_sentinel", "--date", "2026-10-13", "--use-cache", "--use-summary"],
    )
    monkeypatch.delitem(sys.modules, "src.engine.buy_funnel_sentinel")
    with pytest.raises(Intercepted):
        runpy.run_module(
            "src.engine.buy_funnel_sentinel", run_name="__main__", alter_sys=True
        )
    assert len(calls) == 1


@pytest.mark.parametrize("same_parser", [False, True])
def test_real_module_cli_migrates_exact_predecessor_without_runtime_reads(
    tmp_path, monkeypatch, same_parser
):
    _, options, manifest, original, _ = predecessor(
        tmp_path,
        parser_contract=C.PRE_RECHECK_PARSER if same_parser else C.PREVIOUS_PARSER,
        buy_owner=C.INTERMEDIATE_BUY_OWNER if same_parser else C.PREVIOUS_BUY_OWNER,
    )
    native_update = P.update_and_load_pipeline_event_summaries
    expected_contracts = C._callback_predecessors(
        (B._blocker_label_from_stage_fields, B._is_ignored_event),
        Path(P.__file__).resolve(),
    )

    def inspect_callbacks(actual):
        callbacks = (actual["reason_labeler"], actual["ignore_payload"])
        for callback in callbacks:
            assert callback.__module__ == "__main__"
            assert callback.__globals__ is vars(sys.modules["__main__"])
            assert (
                callback.__globals__["__spec__"].name
                == "src.engine.buy_funnel_sentinel"
            )
        assert (
            C._callback_predecessors(callbacks, Path(P.__file__).resolve())
            == expected_contracts
        )
        isolated = {
            **options,
            "reason_labeler": callbacks[0],
            "ignore_payload": callbacks[1],
        }
        rows, meta = native_update(**isolated)
        assert sum(row["event_count"] for row in rows) == 1
        assert not meta["rebuilt"]
        assert (
            meta["contract_migration"]["from_parser"]
            == json.loads(original)["parser_contract"]
        )
        assert meta["contract_migration"]["to_parser"] == C.CURRENT_PARSER
        assert (
            Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes()
            == original
        )
        assert (
            meta["contract_migration"]["raw_read_start"]
            == meta["contract_migration"]["raw_read_end"]
        )

    _intercept_real_funnel_cli(monkeypatch, inspect_callbacks)
    assert manifest.read_bytes() != original


@pytest.mark.parametrize("append", [False, True])
def test_same_parser_owner_migration_preserves_archival_and_suffix(
    tmp_path, monkeypatch, append
):
    raw, options, manifest, original, _ = predecessor(
        tmp_path,
        parser_contract=C.PRE_RECHECK_PARSER,
        buy_owner=C.INTERMEDIATE_BUY_OWNER,
    )
    start = raw.stat().st_size
    if append:
        with raw.open("a") as stream:
            stream.write(json.dumps(event(2)) + "\n")
    real_open = builtins.open
    reads = []

    class Tracked:
        def __init__(self, stream):
            self.stream = stream

        def __getattr__(self, name):
            return getattr(self.stream, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def readline(self, *args):
            assert self.stream.tell() >= start
            value = self.stream.readline(*args)
            reads.append(len(value))
            return value

    def guarded(path, *args, **kwargs):
        stream = real_open(path, *args, **kwargs)
        return (
            Tracked(stream)
            if Path(path) == raw and args and args[0] == "rb"
            else stream
        )

    monkeypatch.setattr(builtins, "open", guarded)
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    receipt = meta["contract_migration"]
    assert receipt["from_parser"] == C.PRE_RECHECK_PARSER
    assert receipt["to_parser"] == C.CURRENT_PARSER
    assert receipt["from_callback"] != receipt["to_callback"]
    assert receipt["from_callback"] == json.loads(original)["callback_contract"]
    assert not meta["rebuilt"] and meta["start_raw_offset"] == start
    assert receipt["raw_read_start"] == start
    assert sum(reads) == raw.stat().st_size - start
    assert sum(row["event_count"] for row in rows) == (2 if append else 1)
    assert Path(receipt["original_manifest_archive"]).read_bytes() == original
    assert json.loads(manifest.read_text())["checkpoint_digest"] == P.checkpoint_digest(
        json.loads(manifest.read_text())
    )


@pytest.mark.parametrize(
    "parser_kind,owner_kind",
    [
        ("current", "original"),
        ("previous", "current"),
        ("unknown", "intermediate"),
        ("current", "unknown"),
    ],
)
def test_parser_and_callback_owner_pairs_cannot_be_crossed(
    tmp_path, parser_kind, owner_kind
):
    parsers = {
        "current": C.PRE_FORMAT_PARSER,
        "previous": C.PREVIOUS_PARSER,
        "unknown": "f" * 64,
    }
    owners = {
        "original": C.PREVIOUS_BUY_OWNER,
        "intermediate": C.INTERMEDIATE_BUY_OWNER,
        "current": C.PRE_FORMAT_BUY_OWNER,
        "unknown": "e" * 64,
    }
    _, options, manifest, original, _ = predecessor(
        tmp_path, parser_contract=parsers[parser_kind], buy_owner=owners[owner_kind]
    )
    summary = Path(json.loads(original)["summary_path"])
    original_summary = summary.read_bytes()
    with pytest.raises(
        RuntimeError,
        match="parser_predecessor_unverified|callback_predecessor_unverified",
    ):
        P.update_and_load_pipeline_event_summaries(**options)
    assert (
        manifest.read_bytes() == original and summary.read_bytes() == original_summary
    )
    assert not (manifest.parent / "contract_migrations").exists()


def test_current_parser_does_not_adopt_previous_default_parser_callback(tmp_path):
    _, options, manifest, original, _ = predecessor(
        tmp_path, parser_callback=True, parser_contract=C.PRE_FORMAT_PARSER
    )
    prior_callback = hashlib.sha256(
        "\n".join(
            [inspect.getsource(P.default_reason_label), C.PREVIOUS_PARSER]
        ).encode()
    ).hexdigest()
    revise(manifest, callback_contract=prior_callback)
    original = manifest.read_bytes()
    with pytest.raises(RuntimeError, match="callback_predecessor_unverified"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original
    assert not (manifest.parent / "contract_migrations").exists()


def test_same_parser_migration_preserves_complete_previous_migration_chain(
    tmp_path, monkeypatch
):
    raw, options, manifest, first_original, _ = predecessor(tmp_path)
    first_source = json.loads(first_original)
    parts = []
    for callback in (options["reason_labeler"], options["ignore_payload"]):
        parts.extend((inspect.getsource(callback), C.INTERMEDIATE_BUY_OWNER))
    intermediate_callback = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    summary = Path(first_source["summary_path"])
    # Model the already published C checkpoint, including its native migration
    # receipt and original archive, entirely inside this private source fixture.
    first_receipt = C.archive_predecessor(
        dict(
            schema="native_summary_contract_migration_v1",
            from_parser=C.PREVIOUS_PARSER,
            to_parser=C.PRE_RECHECK_PARSER,
            from_callback=first_source["callback_contract"],
            to_callback=intermediate_callback,
            original_checkpoint=first_source["checkpoint_digest"],
            original_manifest_sha256=hashlib.sha256(first_original).hexdigest(),
            original_summary_sha256=hashlib.sha256(summary.read_bytes()).hexdigest(),
            original_summary_generation=C._stamp(summary),
            raw_generation=C._stamp(raw),
            raw_read_start=raw.stat().st_size,
            raw_read_end=raw.stat().st_size,
            verification_owner_sha256="083c8368b852618e47e3322958d8c8c655fdb27c958d0524049542d9fa32fabf",
            decision_authority="report_only",
            runtime_effect=False,
            historical_rebuild_performed=False,
        ),
        manifest,
    )
    first_archive = Path(first_receipt["original_manifest_archive"])
    revise(
        manifest,
        parser_contract=C.PRE_RECHECK_PARSER,
        callback_contract=intermediate_callback,
        contract_migration=first_receipt,
    )
    previous_checkpoint = manifest.read_bytes()
    start = raw.stat().st_size
    with raw.open("a") as stream:
        stream.write(json.dumps(event(2)) + "\n")
    real_open = builtins.open
    reads = []

    class Tracked:
        def __init__(self, stream):
            self.stream = stream

        def __getattr__(self, name):
            return getattr(self.stream, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def readline(self, *args):
            assert self.stream.tell() >= start
            value = self.stream.readline(*args)
            reads.append(len(value))
            return value

    def guarded(path, *args, **kwargs):
        stream = real_open(path, *args, **kwargs)
        return (
            Tracked(stream)
            if Path(path) == raw and args and args[0] == "rb"
            else stream
        )

    monkeypatch.setattr(builtins, "open", guarded)
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    second_receipt = meta["contract_migration"]
    second_archive = Path(second_receipt["original_manifest_archive"])
    assert second_archive != first_archive
    assert first_archive.read_bytes() == first_original
    assert second_archive.read_bytes() == previous_checkpoint
    assert json.loads(second_archive.read_text())["contract_migration"] == first_receipt
    assert (
        second_receipt["original_manifest_sha256"]
        == hashlib.sha256(previous_checkpoint).hexdigest()
    )
    assert (
        second_receipt["original_checkpoint"]
        == json.loads(previous_checkpoint)["checkpoint_digest"]
    )
    assert second_receipt["from_parser"] == C.PRE_RECHECK_PARSER
    assert second_receipt["to_parser"] == C.CURRENT_PARSER
    assert (
        second_receipt["from_callback"]
        == intermediate_callback
        != second_receipt["to_callback"]
    )
    assert sum(reads) == raw.stat().st_size - start
    assert not meta["rebuilt"] and meta["start_raw_offset"] == start
    assert sum(row["event_count"] for row in rows) == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "module_name",
        "missing_module",
        "different_module",
        "copied_globals",
        "callback_binding",
        "spec_missing",
        "spec_name",
        "origin_missing",
        "origin_path",
        "file_missing",
        "file_path",
        "globals_name",
        "runtime_dependency",
        "closure",
        "owner_hash",
    ],
)
def test_real_cli_rejects_unbound_or_modified_callbacks(
    tmp_path, monkeypatch, mutation
):
    _, options, manifest, original, _ = predecessor(tmp_path)
    native_update = P.update_and_load_pipeline_event_summaries

    def inspect_callbacks(actual):
        callback = actual["reason_labeler"]
        main = sys.modules["__main__"]
        with monkeypatch.context() as patch:
            if mutation == "module_name":
                patch.setattr(callback, "__module__", "unreviewed")
            elif mutation == "missing_module":
                patch.delitem(sys.modules, "__main__")
            elif mutation == "different_module":
                patch.setitem(sys.modules, "__main__", ModuleType("__main__"))
            elif mutation == "copied_globals":
                callback = FunctionType(
                    callback.__code__, dict(callback.__globals__), callback.__name__
                )
            elif mutation == "callback_binding":
                patch.setattr(main, callback.__name__, lambda *args: None)
            elif mutation == "spec_missing":
                patch.setattr(main, "__spec__", None)
            elif mutation in ("spec_name", "origin_missing", "origin_path"):
                spec = ModuleSpec(
                    "unreviewed" if mutation == "spec_name" else main.__spec__.name,
                    main.__spec__.loader,
                    origin=(
                        None
                        if mutation == "origin_missing"
                        else (
                            "/unreviewed.py"
                            if mutation == "origin_path"
                            else main.__spec__.origin
                        )
                    ),
                )
                patch.setattr(main, "__spec__", spec)
            elif mutation in ("file_missing", "file_path"):
                patch.setattr(
                    main,
                    "__file__",
                    None if mutation == "file_missing" else "/unreviewed.py",
                )
            elif mutation == "globals_name":
                patch.setattr(main, "__name__", "unreviewed")
            elif mutation == "runtime_dependency":
                patch.setattr(main, "MANUAL_EXCLUDED_STOCKS", set())
            elif mutation == "closure":
                original_callback = callback

                def closed(*args):
                    return original_callback(*args)

                closed.__name__ = callback.__name__
                closed.__module__ = "__main__"
                callback = closed
            elif mutation == "owner_hash":
                patch.setattr(C, "CURRENT_BUY_OWNER", "unreviewed")
            isolated = {
                **options,
                "reason_labeler": callback,
                "ignore_payload": actual["ignore_payload"],
            }
            with pytest.raises(
                RuntimeError,
                match="funnel_owner_changed|funnel_dependency_changed|callback_closure_changed",
            ):
                native_update(**isolated)
        assert manifest.read_bytes() == original
        assert not (manifest.parent / "contract_migrations").exists()

    _intercept_real_funnel_cli(monkeypatch, inspect_callbacks)


@pytest.mark.parametrize("parser_callback", [False, True])
def test_recent_producer_projection_migrates_exact_baseline_parser_without_replay(
    tmp_path, parser_callback
):
    raw, options, manifest, original, rows = predecessor(
        tmp_path,
        parser_callback=parser_callback,
        parser_contract=C.BASE_PARSER,
        buy_owner=C.PRE_SCOPED_BUY_OWNER,
    )
    if parser_callback:
        callback = hashlib.sha256(
            "\n".join(
                [inspect.getsource(P.default_reason_label), C.BASE_PARSER]
            ).encode()
        ).hexdigest()
        revise(manifest, callback_contract=callback)
        original = manifest.read_bytes()
    offset = raw.stat().st_size
    with raw.open("a") as stream:
        stream.write(json.dumps(event(2)) + "\n")
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert sum(r["event_count"] for r in rows) == 2 and meta["rebuilt"] is False
    assert meta["start_raw_offset"] == offset
    proof = meta["contract_migration"]
    assert proof["from_parser"] == C.BASE_PARSER
    assert proof["to_parser"] == C.CURRENT_PARSER
    assert Path(proof["original_manifest_archive"]).read_bytes() == original


def test_recheck_parser_change_is_only_new_producer_stage():
    """No old stage/callback semantics are inferred from an arbitrary new SHA."""
    import subprocess

    root = Path(P.__file__).resolve().parents[2]
    name = "src/engine/pipeline_event_summary.py"
    previous = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "c5aeda844dfab36146d04e6305cb29508cd47d4f:" + name,
        ]
    )
    current = subprocess.check_output(
        ["git", "-C", str(root), "show", "a7c0b0dc5:" + name]
    )
    addition = b'    "pre_submit_delay_recheck_observed",\n'
    assert current.count(addition) == 1 and addition not in previous
    assert current.replace(addition, b"") == previous
    assert hashlib.sha256(previous).hexdigest() == C.PRE_RECHECK_PARSER
    assert hashlib.sha256(current).hexdigest() == C.PRE_READ_REUSE_PARSER
    old_producer = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "c5aeda844dfab36146d04e6305cb29508cd47d4f:src/engine/sniper_state_handlers.py",
        ]
    )
    assert b"pre_submit_delay_recheck_observed" not in old_producer


@pytest.mark.parametrize("parser_callback", [False, True])
def test_pre_recheck_parser_migration_reads_legacy_suffix_without_rebuild(
    tmp_path, parser_callback
):
    raw, options, manifest, original, _ = predecessor(
        tmp_path,
        parser_callback=parser_callback,
        parser_contract=C.PRE_RECHECK_PARSER,
        buy_owner=C.PRE_FORMAT_BUY_OWNER,
    )
    offset = raw.stat().st_size
    new_event = event(2)
    with raw.open("a") as stream:
        stream.write(json.dumps(new_event) + "\n")
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["start_raw_offset"] == offset and meta["rebuilt"] is False
    assert meta["contract_migration"]["from_parser"] == C.PRE_RECHECK_PARSER
    assert meta["contract_migration"]["to_parser"] == C.CURRENT_PARSER
    assert (
        Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes()
        == original
    )
    assert sum(row["event_count"] for row in rows) == 2
    assert any(row["stage"] == new_event["stage"] for row in rows)


def test_scoped_funnel_owner_change_preserves_exact_callback_definitions():
    import ast
    import subprocess

    root = Path(B.__file__).resolve().parents[2]
    old = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "d942ba69b4d4d51da5ad846ecb4ddd1ba4e46b8d^:src/engine/buy_funnel_sentinel.py",
        ]
    )
    assert hashlib.sha256(old).hexdigest() == C.PRE_SCOPED_BUY_OWNER
    assert (
        hashlib.sha256(Path(B.__file__).read_bytes()).hexdigest() == C.CURRENT_BUY_OWNER
    )
    old_tree = ast.parse(old)
    for name in ("_safe_str", "_blocker_label_from_stage_fields", "_is_ignored_event"):
        original = next(
            node
            for node in old_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )
        actual = ast.parse(inspect.getsource(getattr(B, name))).body[0]
        assert ast.dump(original, include_attributes=False) == ast.dump(
            actual, include_attributes=False
        )
        assert (
            hashlib.sha256(
                ast.dump(actual, include_attributes=False).encode()
            ).hexdigest()
            == C.DEFINITIONS["buy:" + name]
        )


def test_pre_scoped_owner_and_pre_recheck_parser_migrate_exact_pair(tmp_path):
    _, options, manifest, original, _ = predecessor(
        tmp_path, parser_contract=C.PRE_RECHECK_PARSER, buy_owner=C.PRE_SCOPED_BUY_OWNER
    )
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["rebuilt"] is False and sum(row["event_count"] for row in rows) == 1
    assert (
        Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes()
        == original
    )


def test_archive_reader_successor_preserves_issued_predecessor_and_suffix(tmp_path):
    raw, options, manifest, original, _ = predecessor(
        tmp_path, parser_contract=C.CURRENT_PARSER, buy_owner=C.PRE_ARCHIVE_BUY_OWNER
    )
    offset = raw.stat().st_size
    with raw.open("a") as stream:
        stream.write(json.dumps(event(2)) + "\n")
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert meta["rebuilt"] is False and meta["start_raw_offset"] == offset
    assert sum(row["event_count"] for row in rows) == 2
    assert Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes() == original


def test_archive_reader_successor_rejects_unissued_parser_pair(tmp_path):
    _, options, manifest, original, _ = predecessor(
        tmp_path, parser_contract=C.PRE_FORMAT_PARSER, buy_owner=C.PRE_ARCHIVE_BUY_OWNER
    )
    with pytest.raises(RuntimeError, match="callback_predecessor_unverified"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


def test_expanded_producer_stage_profile_cannot_migrate_as_same_profile(tmp_path):
    _, options, manifest, _, _ = predecessor(
        tmp_path, parser_contract=C.PRE_RECHECK_PARSER, buy_owner=C.PRE_FORMAT_BUY_OWNER
    )
    original = manifest.read_bytes()
    with pytest.raises(RuntimeError, match="source_guard_failed"):
        P.update_and_load_pipeline_event_summaries(
            **options, summary_stages=P.PRODUCER_SUMMARY_STAGES
        )
    assert manifest.read_bytes() == original
    assert not (manifest.parent / "contract_migrations").exists()


def test_new_parser_cannot_inherit_unproduced_intermediate_owner_pair(tmp_path):
    _, options, manifest, original, _ = predecessor(
        tmp_path,
        parser_contract=C.PRE_FORMAT_PARSER,
        buy_owner=C.INTERMEDIATE_BUY_OWNER,
    )
    with pytest.raises(RuntimeError, match="callback_predecessor_unverified"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original


@pytest.mark.parametrize("parser_callback", [False, True])
def test_projection_reader_successor_migrates_existing_prefix_without_raw_rebuild(
    tmp_path, monkeypatch, parser_callback
):
    raw, options, manifest, original, rows = predecessor(
        tmp_path,
        parser_callback=parser_callback,
        parser_contract=C.PRE_READ_REUSE_PARSER,
        buy_owner=C.PRE_LIQUIDITY_BUY_OWNER,
    )
    offset = raw.stat().st_size
    with raw.open("a") as handle:
        handle.write(json.dumps(event(2)) + "\n")
    real_open = builtins.open

    class SuffixOnly:
        def __init__(self, f):
            self.f = f

        def __getattr__(self, name):
            return getattr(self.f, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.f.__exit__(*args)

        def readline(self, *args):
            assert self.f.tell() >= offset
            return self.f.readline(*args)

    def guarded(path, *args, **kwargs):
        f = real_open(path, *args, **kwargs)
        return SuffixOnly(f) if Path(path) == raw and args and args[0] == "rb" else f

    monkeypatch.setattr(builtins, "open", guarded)
    result, metadata = P.update_and_load_pipeline_event_summaries(**options)
    assert not metadata["rebuilt"] and metadata["start_raw_offset"] == offset
    assert sum(row["event_count"] for row in result) == 2
    receipt = metadata["contract_migration"]
    assert (
        receipt["from_parser"] == C.PRE_READ_REUSE_PARSER
        and receipt["to_parser"] == C.CURRENT_PARSER
    )
    assert Path(receipt["original_manifest_archive"]).read_bytes() == original


def test_projection_reuse_successor_preserves_all_parser_and_aggregation_source():
    import subprocess

    root = Path(P.__file__).resolve().parents[2]
    previous = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "a7c0b0dc5:src/engine/pipeline_event_summary.py",
        ]
    )
    current = Path(P.__file__).read_bytes()
    old = b"    return _load_summary_rows(path, include_samples=include_samples, strict=strict)"
    new = b"    return _load_summary_rows(path, include_samples=include_samples, strict=strict,\n                              _projection_reuse=not include_samples)"
    from src.engine.automation.intraday_release_handoff import (
        reviewed_formatting_source,
    )

    historical = reviewed_formatting_source(
        "src/engine/pipeline_event_summary.py", current
    )
    assert previous.count(old) == 1 and previous.replace(old, new) == historical
    assert hashlib.sha256(previous).hexdigest() == C.PRE_READ_REUSE_PARSER
    assert hashlib.sha256(historical).hexdigest() == C.PRE_FORMAT_PARSER
    assert hashlib.sha256(current).hexdigest() == C.CURRENT_PARSER


def test_liquidity_cache_successor_keeps_native_summary_and_only_reads_new_suffix(
    tmp_path, monkeypatch
):
    raw, options, manifest, original, rows = predecessor(
        tmp_path,
        parser_contract=C.PRE_FORMAT_PARSER,
        buy_owner=C.PRE_LIQUIDITY_BUY_OWNER,
    )
    offset = raw.stat().st_size
    with raw.open("a") as stream:
        stream.write(json.dumps(event(2)) + "\n")
    real_open = builtins.open

    class SuffixOnly:
        def __init__(self, stream):
            self.stream = stream

        def __getattr__(self, name):
            return getattr(self.stream, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def readline(self, *args):
            assert self.stream.tell() >= offset
            return self.stream.readline(*args)

    def guarded(path, *args, **kwargs):
        stream = real_open(path, *args, **kwargs)
        return (
            SuffixOnly(stream)
            if Path(path) == raw and args and args[0] == "rb"
            else stream
        )

    monkeypatch.setattr(builtins, "open", guarded)
    result, meta = P.update_and_load_pipeline_event_summaries(**options)
    assert not meta["rebuilt"] and meta["start_raw_offset"] == offset
    assert sum(row["event_count"] for row in result) == 2
    assert (
        Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes()
        == original
    )
    assert (
        meta["contract_migration"]["from_parser"] == C.PRE_FORMAT_PARSER
        and meta["contract_migration"]["to_parser"] == C.CURRENT_PARSER
    )


@pytest.mark.parametrize(
    "parser_sha",
    [C.PREVIOUS_PARSER, C.BASE_PARSER, C.PRE_RECHECK_PARSER, C.PRE_READ_REUSE_PARSER],
)
def test_scope_extraction_predecessor_cannot_be_combined_with_other_parsers(
    tmp_path, parser_sha
):
    _, options, manifest, original, _ = predecessor(
        tmp_path, parser_contract=parser_sha, buy_owner=C.PRE_SCOPE_EXTRACTION_BUY_OWNER
    )
    with pytest.raises(RuntimeError, match="callback_predecessor_unverified"):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes() == original
    assert not (manifest.parent / "contract_migrations").exists()


@pytest.mark.parametrize("parser_callback", [False, True])
@pytest.mark.parametrize("append", [False, True])
def test_exact_preformat_checkpoint_migrates_without_rewriting_prefix(
    tmp_path, parser_callback, append
):
    raw, options, manifest, original, _ = predecessor(
        tmp_path,
        parser_callback=parser_callback,
        parser_contract=C.PRE_FORMAT_PARSER,
        buy_owner=C.PRE_FORMAT_BUY_OWNER,
    )
    prefix = raw.read_bytes()
    if append:
        with raw.open("a") as stream:
            stream.write(json.dumps(event(2)) + "\n")
    rows, metadata = P.update_and_load_pipeline_event_summaries(**options)
    proof = metadata["contract_migration"]
    assert proof["from_parser"] == C.PRE_FORMAT_PARSER
    assert proof["to_parser"] == C.CURRENT_PARSER
    assert proof["raw_read_start"] == len(prefix)
    assert not metadata["rebuilt"] and not proof["historical_rebuild_performed"]
    assert raw.read_bytes().startswith(prefix)
    assert sum(row["event_count"] for row in rows) == (2 if append else 1)
    assert Path(proof["original_manifest_archive"]).read_bytes() == original


@pytest.mark.parametrize(
    "callback",
    [P.default_reason_label, B._blocker_label_from_stage_fields, B._is_ignored_event],
)
def test_formatting_keeps_exact_native_callback_text(callback):
    import ast
    import subprocess

    root = Path(P.__file__).resolve().parents[2]
    owner = Path(inspect.getsourcefile(callback)).resolve()
    original = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "78bfac3d7804d4c5d6da1f6345f8fbdc28241976:" + str(owner.relative_to(root)),
        ]
    )
    node = next(
        n
        for n in ast.parse(original).body
        if isinstance(n, ast.FunctionDef) and n.name == callback.__name__
    )
    source = "".join(
        inspect.getblock(original.decode().splitlines(keepends=True)[node.lineno - 1 :])
    )
    assert source == inspect.getsource(callback)
    assert (
        hashlib.sha256(original).hexdigest()
        != hashlib.sha256(owner.read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("parser", ["current", "previous"])
def test_call_finish_consumer_preserves_only_exact_native_summary_predecessor(tmp_path, parser):
    raw, options, manifest, original, _ = predecessor(
        tmp_path,
        parser_contract=C.CURRENT_PARSER if parser == "current" else C.PREVIOUS_PARSER,
        buy_owner=C.PRE_CALL_FINISH_BUY_OWNER,
    )
    offset = raw.stat().st_size
    with raw.open("a") as stream:
        stream.write(json.dumps(event(2)) + "\n")
    if parser == "previous":
        with pytest.raises(RuntimeError, match="callback_predecessor_unverified"):
            P.update_and_load_pipeline_event_summaries(**options)
        assert manifest.read_bytes() == original
    else:
        rows, meta = P.update_and_load_pipeline_event_summaries(**options)
        assert meta["start_raw_offset"] == offset and meta["rebuilt"] is False
        assert Path(meta["contract_migration"]["original_manifest_archive"]).read_bytes() == original
        assert sum(row["event_count"] for row in rows) == 2
