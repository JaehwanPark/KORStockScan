"""Exact predecessor proof for native report-summary contract migration.

This owner permits only reviewed source-equivalent parser/callback transitions.
It never changes policy, rewrites an old checkpoint, or reads the raw prefix.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

PREVIOUS_PARSER = "1ddc6f33db48db5fec69ec36297119741caebf42444f95e5a6d2e67f4795eeb2"
BASE_PARSER = "b1b1e59a99c09c79304d9db7cfd731fe47deb1afb9926303c7ba7d1d9ea03116"
# The successor only adds the new producer's recheck observation stage.
# Legacy parsing and callback definitions are byte/AST identical; the stopped
# next-session transition has no old producer emitting that new stage.
PRE_RECHECK_PARSER = "8500f48239f82c9959ece854b6358df1502ff43d7ce7ec5336dc06853959b2e4"
# 0255cb05f changes only load_summary_rows' invocation-local projection reuse.
# Event parsing, summary aggregation and all callbacks remain source equivalent.
PRE_READ_REUSE_PARSER = (
    "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af"
)
PRE_FORMAT_PARSER = "f3051e000b6edbd349a58e37f7880f5db10ae62dde9dec7f32edaa4eea6ebe3b"
CURRENT_PARSER = "210d0ac7da6f400f87ed8aa1b77446b10123969981c3511b9710f475ed7e2473"
PREVIOUS_BUY_OWNER = "83d8b3d9e41f496e7f868789d635472fd5ebd994489f3db31bbb1f670565f468"
INTERMEDIATE_BUY_OWNER = (
    "d487b4041fff24f690f78bef9bbfea1bdbf6dedd59c70095585b23e9fe1005e7"
)
PRE_SCOPED_BUY_OWNER = (
    "332ffe2791e389741af907e3fa304352a0abea01e222053a20bff2ba2de7400b"
)
PRE_LIQUIDITY_BUY_OWNER = (
    "6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993"
)
PRE_TERMINAL_BUY_OWNER = (
    "4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1"
)
PRE_SCOPE_EXTRACTION_BUY_OWNER = (
    "b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7"
)
PRE_FORMAT_BUY_OWNER = (
    "40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a"
)
# Call completion attribution changes only the report consumer. The native
# summary parser and its callback definitions remain unchanged.
PRE_CALL_FINISH_BUY_OWNER = "a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2"
CURRENT_BUY_OWNER = "72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455"
LIMIT = 32 * 1024 * 1024
SUMMARY_LIMIT = 128 * 1024 * 1024
DEFINITIONS = {
    "buy:_blocker_label_from_stage_fields": "9aae9e21e776ae83e227bd4998a5b178479b5c0daf2efeafdef3aef538c12129",
    "buy:_is_ignored_event": "ff8adb687774f710cf74668dc962dcba42a3c468790c89db3413fa6d7371fa44",
    "buy:_safe_str": "68672915d00e452b0f495d7d394698c576d020f65fa35c0fc3f9e647fa9df206",
    "parser:default_reason_label": "eb7e1ccd546f853c7f85512431f2128c7b46e31cd45af338df6258015723e6e9",
    "parser:_first_field": "5baf01cc3bcc6e97ab65ad86f4b4ef182cf0170239b4bcb34187a257cc54ac30",
    "parser:_safe_str": "68672915d00e452b0f495d7d394698c576d020f65fa35c0fc3f9e647fa9df206",
}


def _fail(reason):
    raise RuntimeError("summary_contract_migration_" + reason)


def _stamp(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def _read(path, limit):
    with Path(path).open("rb") as f:
        before = os.fstat(f.fileno())
        if before.st_size > limit:
            _fail("artifact_read_budget_exceeded")
        value = f.read(limit + 1)
        after = os.fstat(f.fileno())
    if len(value) > limit or (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        _fail("artifact_changed_during_read")
    return value


def _definition(function, expected):
    if getattr(function, "__closure__", None):
        _fail("callback_closure_changed")
    try:
        node = ast.parse(inspect.getsource(function)).body[0]
        actual = hashlib.sha256(
            ast.dump(node, include_attributes=False).encode()
        ).hexdigest()
    except (OSError, TypeError, SyntaxError, IndexError):
        _fail("callback_definition_unverified")
    if actual != expected:
        _fail("callback_definition_changed")


def _parser_dependencies(parser):
    for name in ("default_reason_label", "_first_field", "_safe_str"):
        _definition(getattr(parser, name), DEFINITIONS["parser:" + name])
    if (
        parser.default_reason_label.__globals__.get("_first_field")
        is not parser._first_field
        or parser._first_field.__globals__.get("_safe_str") is not parser._safe_str
    ):
        _fail("parser_dependency_changed")


def _funnel_module_identity(callback, owner, owner_sha, parser_path):
    """Bind imported and real -m callbacks to the same pinned module owner."""
    canonical = "src.engine.buy_funnel_sentinel"
    name = getattr(callback, "__module__", None)
    module = sys.modules.get(name) if name in (canonical, "__main__") else None
    spec = getattr(module, "__spec__", None)
    file = getattr(module, "__file__", None)
    origin = getattr(spec, "origin", None)
    if (
        owner_sha != CURRENT_BUY_OWNER
        or owner != parser_path.with_name("buy_funnel_sentinel.py")
        or not isinstance(module, ModuleType)
        or callback.__globals__ is not vars(module)
        or getattr(module, "__name__", None) != name
        or getattr(module, callback.__name__, None) is not callback
        or getattr(spec, "name", None) != canonical
        or not isinstance(file, str)
        or not isinstance(origin, str)
        or Path(file).resolve() != owner
        or Path(origin).resolve() != owner
    ):
        _fail("funnel_owner_changed")


def _callback_predecessors(callbacks, parser_path):
    from src.engine import pipeline_event_summary as parser

    _parser_dependencies(parser)
    pre_format_original = []
    original, parser_only, funnel_old, funnel_intermediate, base_parser = (
        [],
        [],
        [],
        [],
        [],
    )
    (
        pre_recheck_parser,
        funnel_pre_scoped,
        pre_read_reuse_parser,
        funnel_pre_liquidity,
    ) = ([], [], [], [])
    funnel_pre_terminal, funnel_pre_scope_extraction, funnel_pre_call_finish = [], [], []
    funnel = tuple(getattr(f, "__name__", None) for f in callbacks) == (
        "_blocker_label_from_stage_fields",
        "_is_ignored_event",
    )
    for callback in callbacks:
        if callback is None:
            continue
        if getattr(callback, "__closure__", None):
            _fail("callback_closure_changed")
        source = inspect.getsource(callback)
        owner = Path(inspect.getsourcefile(callback)).resolve()
        raw = _read(owner, LIMIT)
        owner_sha = hashlib.sha256(raw).hexdigest()
        if owner == parser_path and callback is not parser.default_reason_label:
            _fail("parser_callback_not_reviewed")
        if funnel:
            _funnel_module_identity(callback, owner, owner_sha, parser_path)
            _definition(callback, DEFINITIONS["buy:" + callback.__name__])
            globals_ = callback.__globals__
            _definition(globals_["_safe_str"], DEFINITIONS["buy:_safe_str"])
            if (
                globals_["MANUAL_EXCLUDED_STOCKS"] != {("제룡전기", "033100")}
                or globals_["IGNORED_STOCK_NAMES"] != {"TEST", "DUMMY", "MOCK"}
                or globals_["default_reason_label"] is not parser.default_reason_label
            ):
                _fail("funnel_dependency_changed")
        original.extend((source, owner_sha))
        if funnel or owner == parser_path:
            from src.engine.automation.intraday_release_handoff import (
                reviewed_formatting_predecessor,
            )

            # The three native callback definitions retain their exact text;
            # only the pinned physical module owner changed under Black.
            owner_sha = reviewed_formatting_predecessor(
                str(owner.relative_to(Path(__file__).resolve().parents[3])),
                PRE_CALL_FINISH_BUY_OWNER if funnel else owner_sha
            )
        pre_format_original.extend((source, owner_sha))
        prior_owner = PREVIOUS_PARSER if owner == parser_path else owner_sha
        parser_only.extend((source, prior_owner))
        base_parser.extend((source, BASE_PARSER if owner == parser_path else owner_sha))
        pre_recheck_parser.extend(
            (source, PRE_RECHECK_PARSER if owner == parser_path else owner_sha)
        )
        pre_read_reuse_parser.extend(
            (source, PRE_READ_REUSE_PARSER if owner == parser_path else owner_sha)
        )
        funnel_old.extend((source, PREVIOUS_BUY_OWNER if funnel else prior_owner))
        funnel_intermediate.extend(
            (source, INTERMEDIATE_BUY_OWNER if funnel else prior_owner)
        )
        funnel_pre_scoped.extend(
            (source, PRE_SCOPED_BUY_OWNER if funnel else prior_owner)
        )
        funnel_pre_liquidity.extend(
            (source, PRE_LIQUIDITY_BUY_OWNER if funnel else prior_owner)
        )
        funnel_pre_terminal.extend(
            (source, PRE_TERMINAL_BUY_OWNER if funnel else prior_owner)
        )
        funnel_pre_scope_extraction.extend(
            (source, PRE_SCOPE_EXTRACTION_BUY_OWNER if funnel else prior_owner)
        )
        funnel_pre_call_finish.extend(
            (source, PRE_CALL_FINISH_BUY_OWNER if funnel else prior_owner)
        )
    digest = lambda parts: hashlib.sha256("\n".join(parts).encode()).hexdigest()
    if funnel:
        # These are reviewed parser/owner pairs, not independent allowlists.
        # In particular, the new owner never appeared with PREVIOUS_PARSER.
        predecessors = {
            (PREVIOUS_PARSER, digest(funnel_old)),
            (PREVIOUS_PARSER, digest(funnel_intermediate)),
            (PRE_RECHECK_PARSER, digest(funnel_intermediate)),
            (PRE_RECHECK_PARSER, digest(funnel_pre_scoped)),
            (PRE_RECHECK_PARSER, digest(pre_recheck_parser)),
            (BASE_PARSER, digest(funnel_intermediate)),
            (BASE_PARSER, digest(funnel_pre_scoped)),
            (PRE_READ_REUSE_PARSER, digest(funnel_pre_liquidity)),
            (PRE_FORMAT_PARSER, digest(funnel_pre_liquidity)),
            (PRE_FORMAT_PARSER, digest(funnel_pre_terminal)),
            (PRE_FORMAT_PARSER, digest(funnel_pre_scope_extraction)),
            (CURRENT_PARSER, digest(funnel_pre_call_finish)),
        }
    else:
        # Preserve the existing parser-only migration for unchanged external
        # callbacks and the pinned native default_reason_label callback.
        predecessors = {
            (PREVIOUS_PARSER, digest(parser_only)),
            (BASE_PARSER, digest(base_parser)),
            (PRE_RECHECK_PARSER, digest(pre_recheck_parser)),
            (PRE_READ_REUSE_PARSER, digest(pre_read_reuse_parser)),
        }
    predecessors.add((PRE_FORMAT_PARSER, digest(pre_format_original)))
    return digest(original), predecessors


def _verify_predecessor(
    *,
    manifest,
    manifest_path,
    raw_path,
    summary_path,
    callbacks,
    callback_contract,
    parser_path,
    parser_contract,
):
    """Validate an exact old contract before the native owner appends at its cursor."""
    from src.engine.pipeline_event_summary import checkpoint_digest

    parser_path = Path(parser_path).resolve()
    if (
        parser_contract != CURRENT_PARSER
        or hashlib.sha256(_read(parser_path, LIMIT)).hexdigest() != CURRENT_PARSER
        or manifest.get("parser_contract")
        not in {
            PREVIOUS_PARSER,
            BASE_PARSER,
            PRE_RECHECK_PARSER,
            PRE_READ_REUSE_PARSER,
            PRE_FORMAT_PARSER,
            CURRENT_PARSER,
        }
    ):
        _fail("parser_predecessor_unverified")
    actual_callback, predecessors = _callback_predecessors(callbacks, parser_path)
    predecessor = (manifest.get("parser_contract"), manifest.get("callback_contract"))
    if actual_callback != callback_contract or predecessor not in predecessors:
        _fail("callback_predecessor_unverified")
    original = _read(manifest_path, LIMIT)
    if json.loads(original) != manifest or manifest.get(
        "checkpoint_digest"
    ) != checkpoint_digest(manifest):
        _fail("checkpoint_unverified")
    raw_path, summary_path = Path(raw_path).resolve(), Path(summary_path).resolve()
    raw, summary = _stamp(raw_path), _stamp(summary_path)
    offset = manifest.get("raw_offset")
    if (
        raw_path.suffix == ".gz"
        or summary_path.suffix == ".gz"
        or manifest.get("raw_path") != str(raw_path)
        or manifest.get("summary_path") != str(summary_path)
        or type(offset) is not int
        or not 0 <= offset <= raw[2]
        or manifest.get("complete_through_raw_offset") != offset
        or manifest.get("incomplete_tail")
        or manifest.get("decode_errors")
        or manifest.get("raw_inode") != raw[1]
        or not offset <= int(manifest.get("raw_size", -1)) <= raw[2]
        or manifest.get("summary_stamp") != summary[1:]
        or (
            manifest.get("raw_size") == raw[2]
            and [manifest.get("raw_mtime_ns"), manifest.get("raw_ctime_ns")] != raw[3:]
        )
    ):
        _fail("source_prefix_unverified")
    if raw[2] - offset > LIMIT:
        _fail("append_budget_exceeded")
    body = _read(summary_path, SUMMARY_LIMIT)
    if _stamp(summary_path) != summary or _stamp(raw_path)[:2] != raw[:2]:
        _fail("source_generation_changed")
    return dict(
        schema="native_summary_contract_migration_v1",
        from_parser=manifest["parser_contract"],
        to_parser=parser_contract,
        from_callback=manifest["callback_contract"],
        to_callback=callback_contract,
        original_checkpoint=manifest["checkpoint_digest"],
        original_manifest_sha256=hashlib.sha256(original).hexdigest(),
        original_summary_sha256=hashlib.sha256(body).hexdigest(),
        original_summary_generation=summary,
        raw_generation=raw,
        raw_read_start=offset,
        raw_read_end=raw[2],
        verification_owner_sha256=hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        decision_authority="report_only",
        runtime_effect=False,
        historical_rebuild_performed=False,
    )


def verify_predecessor(**arguments):
    try:
        return _verify_predecessor(**arguments)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RuntimeError("summary_contract_migration_evidence_unavailable") from exc


def check_pending_migration(data_root, day):
    """Use the native migration proof before an authorized Main drain.

    No checkpoint is changed here. An over-budget predecessor remains running
    so its ordinary producer can catch up before the transition is retried.
    """
    from src.engine import buy_funnel_sentinel as buy, pipeline_event_summary as parser

    manifest_path = (
        Path(data_root)
        / "pipeline_event_summaries"
        / ("pipeline_event_summary_manifest_" + day + ".json")
    )
    manifest = json.loads(_read(manifest_path, LIMIT))
    raw_path = (
        Path(data_root) / "pipeline_events" / ("pipeline_events_" + day + ".jsonl")
    )
    offset = manifest.get("raw_offset")
    if type(offset) is not int or not 0 <= raw_path.stat().st_size - offset <= LIMIT:
        _fail("append_budget_exceeded")
    parser_path = Path(parser.__file__).resolve()
    callback, _ = _callback_predecessors(
        (buy._blocker_label_from_stage_fields, buy._is_ignored_event), parser_path
    )
    parser_sha = hashlib.sha256(_read(parser_path, LIMIT)).hexdigest()
    if (
        manifest.get("callback_contract") == callback
        and manifest.get("parser_contract") == parser_sha
    ):
        return dict(status="current_contract", runtime_effect=False)
    proof = verify_predecessor(
        manifest=manifest,
        manifest_path=manifest_path,
        raw_path=raw_path,
        summary_path=Path(data_root)
        / "pipeline_event_summaries"
        / ("pipeline_event_summary_" + day + ".jsonl"),
        callbacks=(buy._blocker_label_from_stage_fields, buy._is_ignored_event),
        callback_contract=callback,
        parser_path=parser_path,
        parser_contract=parser_sha,
    )
    return dict(status="migration_verified", proof=proof, runtime_effect=False)


def _archive_predecessor(receipt, manifest_path):
    """The native writer preserves exact old bytes before publishing a successor."""
    manifest_path = Path(manifest_path)
    original = _read(manifest_path, LIMIT)
    digest = receipt["original_manifest_sha256"]
    if hashlib.sha256(original).hexdigest() != digest:
        _fail("predecessor_changed_before_archive")
    directory = manifest_path.parent / "contract_migrations"
    directory.mkdir(exist_ok=True)
    name = manifest_path.name + "." + digest + ".json"
    path = directory / name
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        directory_stat = os.fstat(directory_fd)
        try:
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_fd,
            )
        except FileExistsError:
            fd = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
            )
            with os.fdopen(fd, "rb") as stream:
                archived_stat = os.fstat(stream.fileno())
                if (
                    not stat.S_ISREG(archived_stat.st_mode)
                    or archived_stat.st_size > LIMIT
                ):
                    _fail("predecessor_archive_not_regular")
                if stream.read(LIMIT + 1) != original:
                    _fail("predecessor_archive_conflict")
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
                archived_stat = os.fstat(stream.fileno())
        current_directory = directory.lstat()
        current_archive = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            not stat.S_ISDIR(current_directory.st_mode)
            or (current_directory.st_dev, current_directory.st_ino)
            != (directory_stat.st_dev, directory_stat.st_ino)
            or not stat.S_ISREG(current_archive.st_mode)
            or (
                current_archive.st_dev,
                current_archive.st_ino,
                current_archive.st_size,
                current_archive.st_mtime_ns,
                current_archive.st_ctime_ns,
            )
            != (
                archived_stat.st_dev,
                archived_stat.st_ino,
                archived_stat.st_size,
                archived_stat.st_mtime_ns,
                archived_stat.st_ctime_ns,
            )
        ):
            _fail("predecessor_archive_generation_changed")
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return {**receipt, "original_manifest_archive": str(path.absolute())}


def archive_predecessor(receipt, manifest_path):
    try:
        return _archive_predecessor(receipt, manifest_path)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RuntimeError("summary_contract_migration_archive_failed") from exc


def _verify_before_publication(receipt, raw_path, summary_path):
    before, current = receipt["raw_generation"], _stamp(raw_path)
    if (
        current[:2] != before[:2]
        or current[2] < before[2]
        or (current[2] == before[2] and current != before)
        or _stamp(summary_path) != receipt["original_summary_generation"]
    ):
        _fail("source_changed_before_publication")


def verify_before_publication(receipt, raw_path, summary_path):
    try:
        return _verify_before_publication(receipt, raw_path, summary_path)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RuntimeError(
            "summary_contract_migration_source_unavailable_before_publication"
        ) from exc
