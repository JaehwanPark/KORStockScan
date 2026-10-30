"""Authorized Main deployment: drain, select, prepare, then start and attest.

Startup automation owns this transition. It never changes trading policies,
forces process termination, resets monitor cursors or regenerates postclose work.
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
import shlex
import stat
import time
from contextlib import contextmanager, ExitStack
from datetime import datetime
from pathlib import Path

from src.engine.automation import intraday_release_handoff as H
from src.engine.infrastructure import runtime_release_router as R

CONFIRM = "APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART"

# Before selector publication the original selected release remains the native
# policy reader. Keep its own source validation instead of impersonating that
# release with candidate imports or a forged predecessor observation.
_AUXILIARY_ORIGIN_SCRIPT = r'''
import hashlib,json,sys
from pathlib import Path
from datetime import datetime
from src.engine.scalping import reversal_auxiliary_intraday as A
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.infrastructure import runtime_release_router as R
from src.engine.automation import ordered_intraday_deploy as D
q=json.loads(sys.argv[1]); origin=Path.cwd(); data=Path(q['data_root'])
selection=data/'runtime/runtime_release_selection.json'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
    if (Path(A.__file__).resolve().parents[3]!=origin
        or R.selected_release(data.parent)!=(origin,q['origin_commit'])
        or sha(selection)!=q['selection_sha256'] or A.code_hashes()!=q['code_hashes']):
        raise ValueError('auxiliary_native_origin_changed')
    if q['operation']!='prepare' and (D._main_pids() or not D._session_absent()
        or sha(data/'runtime/operator_startup_hold.json')!=q['hold_sha256']):
        raise ValueError('auxiliary_native_transition_not_drained')
guard()
if sha(q['manifest_path'])!=q['manifest_sha256']:
    raise ValueError('auxiliary_native_manifest_changed')
manifest=A.read(q['manifest_path'])
bundle=N.load_effective(data_root=data,target_date=q['day'])
if q['operation']=='prepare':
    result=A.prepare_contract_repair(data,bundle,expected_parent=manifest['expected_parent'],
        now=datetime.fromisoformat(manifest['prepared_at']),repair_schema=manifest['schema'])
elif q['operation']=='publish':
    result=A.publish_contract_repair(data,manifest,expected_parent=manifest['expected_parent'],
        confirm=A.CONTRACT_REPAIR_AUTHORITY)
elif q['operation']=='rollback':
    current=A.current(data,bundle,day=q['day'])
    result=(A.rollback(data,expected_parent=current['artifact_content_sha256'],
        reason='ordered_deployment_failed_before_selection',confirm=A.AUTHORITY)
        if current and current.get('contract_repair_manifest_sha256')==manifest['artifact_content_sha256'] else None)
else:
    raise ValueError('auxiliary_native_operation_invalid')
guard()
reference=None
if result is not None and q['operation']!='prepare':
    path=A.root(data)/'generations'/(result['artifact_content_sha256']+'.json')
    if A.read(path)!=result: raise ValueError('auxiliary_native_receipt_changed')
    reference=dict(path=str(path),sha256=sha(path))
print(json.dumps(dict(status='pass',operation=q['operation'],origin_root=str(origin),
    origin_commit=q['origin_commit'],code_hashes=A.code_hashes(),record=result,reference=reference)))
'''


def verify_candidate_delay_code(day, root, commit):
    """Retain a natively verified prepared origin across the first live handoff."""
    manifest_path = H.bootstrap.manifest_path(day)
    manifest_raw = manifest_path.read_bytes() if manifest_path.exists() else None
    try:
        return H.verify_candidate_delay_code(day, root, commit)
    except ValueError as exc:
        if str(exc) != "entry_consumer_original_code_contract_invalid":
            raise
    from src.engine.automation import prepared_policy_code_handoff as P
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS

    manifest = json.loads(manifest_raw)
    bound = manifest["pre_submit_delay_handoff"]
    selected, selected_commit = R.selected_release(H.DATA_DIR.parent)
    paths = {name: name for name in CONTRACT_PATHS}
    origin = P.resolve_prepared_code_origin(
        H.DATA_DIR,
        day,
        family="pre_submit_delay",
        policy_sha=bound["policy_sha256"],
        expected=bound["code_contract_sha256"],
        paths=paths,
        selected_root=selected,
        selected_commit=selected_commit,
    )
    if origin["basis"] != "verified_selected_prepared_code_handoff":
        raise ValueError("deployment_prepared_delay_origin_required")
    changed = H._verify_entry_code_delta(
        root, commit, origin["origin_commit"], paths, bound["code_contract_sha256"]
    )
    if manifest_path.read_bytes() != manifest_raw:
        raise ValueError("deployment_prepared_delay_manifest_changed")
    return dict(
        status="pass",
        target_date=day,
        origin_commit=origin["origin_commit"],
        release_commit=commit,
        changed_consumer_paths=changed,
        policy_effect="unchanged",
        actual_pid_consumed=False,
        prepared_code_origin=origin,
    )


def inherit_prepared_delay_code(workspace, day, candidate, check):
    """Run under ordered locks after drain, before selection; no policy writes."""
    origin = check.get("prepared_code_origin")
    if not origin:
        return None
    from src.engine.automation import prepared_policy_code_handoff as P

    if any(H._sha(path) != sha for path, sha in origin["sources"].items()):
        raise ValueError("deployment_prepared_delay_source_changed")
    previous_path = Path(origin["code_handoff_receipt_path"])
    previous = P._read(previous_path)
    prepared = P._read(previous["prepared_receipt"])
    return P.issue(
        Path(workspace) / "data",
        day,
        family="pre_submit_delay",
        policy_sha=previous["policy_sha256"],
        expected=previous["original_code_sha256"],
        paths=previous["paths"],
        release_root=candidate,
        prepared_receipt=previous["original_prepared_receipt"],
        origin_verification=prepared["verification_path"],
        confirm=P.AUTHORITY,
        previous_handoff=previous_path,
    )


@contextmanager
def detector_transition_lock(workspace, timeout=60):
    """Drain the existing detector before any deployment mutation.

    Share the wrapper's inode, including publication/notification time. Never
    unlink it; release automatically on success, timeout or failed deployment.
    Python descriptors are non-inheritable so a launched Main cannot keep it.
    """
    path = Path(workspace) / "tmp/run_error_detection.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as lock:

        def acquire():
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            return True

        _wait(acquire, timeout, "deployment_error_detector_drain_timeout")
        yield


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_candidate_active_policy(workspace, candidate, commit, day):
    """Require the complete candidate code handoff before Main can be drained."""
    from src.engine.scalping import reversal_code_handoff as C
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    data = Path(workspace) / "data"
    pointer = N.root(data) / "current.json"
    if not pointer.exists():
        raise ValueError("deployment_active_policy_pointer_missing")
    selection = data / "runtime/runtime_release_selection.json"
    selection_raw, pointer_raw = selection.read_bytes(), pointer.read_bytes()
    selected, ptr = json.loads(selection_raw), json.loads(pointer_raw)
    bundle = N._read(N.root(data) / "generations" / (ptr["bundle_sha256"] + ".json"))
    N.validate(bundle, target_date=bundle["target_date"])
    receipt_path = C.path(data, day, commit, bundle["bundle_sha256"])
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    C.validate_receipt(
        receipt,
        day=day,
        commit=commit,
        root=candidate,
        bundle_sha=bundle["bundle_sha256"],
        pointer_sha=_digest(pointer_raw),
    )
    if (
        receipt.get("origin_root") != selected.get("release_root")
        or receipt.get("origin_commit") != selected.get("git_commit")
        or receipt.get("origin_selection_sha256") != _digest(selection_raw)
        or receipt.get("actual_pid_consumed") is not False
        or receipt["code_hashes"] != C.code_hashes()
    ):
        raise ValueError("deployment_candidate_active_policy_unbound")
    for path, sha in {**receipt["source_hashes"], **receipt["code_hashes"]}.items():
        if not N.source_receipt_matches(dict(path=path, sha256=sha), data_root=data):
            raise ValueError(
                "deployment_candidate_active_policy_source_changed:" + path
            )
    if (
        selection.read_bytes() != selection_raw
        or pointer.read_bytes() != pointer_raw
        or receipt_path.read_bytes() != receipt_raw
        or receipt["code_hashes"] != C.code_hashes()
    ):
        raise ValueError("deployment_candidate_active_policy_generation_changed")
    return dict(
        status="pass",
        receipt_path=str(receipt_path),
        receipt_sha256=_digest(receipt_raw),
        pointer_path=str(pointer),
        pointer_sha256=_digest(pointer_raw),
        candidate_commit=commit,
        bundle_sha256=bundle["bundle_sha256"],
        policy_effect="unchanged",
    )


def verify_candidate_report_currentness(workspace, candidate, day):
    """Use existing bounded report consumers before any Main drain.

    Historical economic gaps remain evidence; invalidated current report/code
    bindings must be natively republished by their owners before a transition.
    """
    from src.engine.monitoring import main_trailing_currentness as trailing
    from src.engine.error_detectors.artifact_freshness import (
        _initial_quantity_semantics,
    )
    from src.engine.monitoring.policy_generation_code_handoff import consumer_inventory

    data = Path(workspace) / "data"
    source_date = H.preserve_checklist(day)["source_date"]
    holding = H._read(
        data
        / "report/monitor_snapshots"
        / ("holding_exit_observation_" + source_date + ".json")
    )
    observed = trailing.observe(data, holding, target_date=day)
    if observed.get("status") != "generation_current":
        raise ValueError("deployment_trailing_report_not_current")
    quantity = _initial_quantity_semantics(Path(candidate), source_date)
    if (
        quantity.get("bounded_contract_validated") is not True
        or quantity.get("observation_complete") is not True
        or "initial_quantity_stage_missing_after_date" in quantity.get("findings", [])
        or quantity.get("postclose_stage_status")
        in {None, "not_observed", "source_invalid"}
    ):
        raise ValueError(
            "deployment_quantity_report_not_current:"
            + ",".join(quantity.get("findings", []))
        )
    return dict(
        status="pass",
        source_date=source_date,
        target_date=day,
        capability_consumers=consumer_inventory(candidate, source_date, data_root=data),
        trailing=observed,
        quantity={
            key: quantity.get(key)
            for key in (
                "status",
                "findings",
                "postclose_stage_status",
                "observation_generation",
                "source_reference_count",
            )
        },
        policy_effect="unchanged",
        runtime_effect=False,
        actual_pid_consumed=False,
    )


def _metadata_signature(path):
    info = Path(path).lstat()
    return tuple(
        getattr(info, "st_" + name)
        for name in (
            "dev",
            "ino",
            "mode",
            "nlink",
            "uid",
            "gid",
            "size",
            "mtime_ns",
            "ctime_ns",
        )
    )


def _owned_metadata(path):
    """Reuse the startup owner's bounded, strict, no-follow regular reader."""
    value, raw = R._startup_receipt(Path(path))
    return value, raw, _metadata_signature(path)


def verify_candidate_p5(
    workspace, day, candidate, commit, path, expected_sha, selection
):
    """Authenticate pre-drain execution proof against its original selector.

    Candidate execution and then-selected incumbent are separate identities.
    Never inherit a predecessor's P5 pointer or accept a prepared successor P5.
    """
    path = Path(path or "")
    if (
        not path.is_absolute()
        or path.resolve() != path
        or path.parent.parent
        != Path(workspace) / "data/report/main_startup_validation" / day
        or path.name != "final.json"
        or re.fullmatch("[0-9a-f]{32}", path.parent.name) is None
        or re.fullmatch("[0-9a-f]{64}", str(expected_sha)) is None
    ):
        raise ValueError("deployment_candidate_p5_reference_invalid")
    proof, raw, signature = _owned_metadata(path)
    if (
        _digest(raw) != expected_sha
        or proof.get("schema") != "main_policy_load_exit_validation_v1"
        or proof.get("run_id") != path.parent.name
        or proof.get("status") != "passed"
        or proof.get("findings") != []
        or proof.get("target_date") != day
        or type(proof.get("child_exit_code")) is not int
        or proof["child_exit_code"] != 0
        or proof.get("failure_phase") is not None
        or proof.get("execution_release_root") != str(candidate)
        or proof.get("execution_release_commit") != commit
        or proof.get("selected_release_root") != selection.get("release_root")
        or proof.get("selected_release_commit") != selection.get("git_commit")
        or any(
            proof.get(k) is not True
            for k in (
                "child_terminated",
                "load_check_passed",
                "protected_sources_unchanged",
            )
        )
        or any(
            proof.get(k) is not False
            for k in ("runtime_effect", "allowed_runtime_apply", "actual_pid_consumed")
        )
    ):
        raise ValueError("deployment_candidate_p5_invalid")
    return dict(
        path=str(path),
        sha256=expected_sha,
        signature=signature,
        target_date=day,
        execution_release_root=str(candidate),
        execution_release_commit=commit,
        selected_release_root=selection["release_root"],
        selected_release_commit=selection["git_commit"],
    )


@contextmanager
def _existing_selector_lock(path):
    """Open the existing writer lock without following links or blocking on FIFO."""
    before = _metadata_signature(path)
    if not stat.S_ISREG(before[2]):
        raise ValueError("deployment_selector_lock_regular_file_required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        opened = tuple(
            getattr(info, "st_" + name)
            for name in (
                "dev",
                "ino",
                "mode",
                "nlink",
                "uid",
                "gid",
                "size",
                "mtime_ns",
                "ctime_ns",
            )
        )
        if not stat.S_ISREG(info.st_mode) or opened != before:
            raise ValueError("deployment_selector_lock_changed")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
        if _metadata_signature(path) != opened:
            raise ValueError("deployment_selector_lock_changed")
    finally:
        os.close(fd)


def _atomic(path, raw, *, expected=None):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(name, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        if expected is not None:
            _, current, signature = _owned_metadata(path)
            if current != expected["raw"] or signature != expected["signature"]:
                raise ValueError("deployment_failed_hold_compare_exchange_changed")
        os.replace(name, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def _predecessor_observer(workspace, day):
    """Freeze a small, exact old observation; never grant validation or trading authority."""
    path = (
        Path(workspace)
        / "data/report/buy_funnel_sentinel"
        / ("submission_bottleneck_monitor_" + day + ".json")
    ).absolute()
    try:
        expected_parent = (
            Path(workspace) / "data"
        ).resolve() / "report/buy_funnel_sentinel"
        if path.is_symlink() or path.parent.resolve() != expected_parent:
            raise ValueError("observer_symlink")
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 8 * 1024 * 1024:
            raise ValueError("observer_size_limit")
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError("observer_not_regular")
            raw = handle.read(8 * 1024 * 1024 + 1)
        after = path.stat()
        signature = lambda item: (
            item.st_dev,
            item.st_ino,
            item.st_mtime_ns,
            item.st_ctime_ns,
            item.st_size,
        )
        if (
            len(raw) > 8 * 1024 * 1024
            or signature(before) != signature(opened)
            or signature(opened) != signature(after)
        ):
            raise ValueError("observer_changed_during_capture")

        def unique_object(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise ValueError("observer_duplicate_key")
                result[key] = item
            return result

        def invalid_constant(_):
            raise ValueError("observer_non_finite")

        value = json.loads(
            raw, object_pairs_hook=unique_object, parse_constant=invalid_constant
        )
        # parse_constant does not see an overflowing JSON exponent (1e999).
        json.dumps(value, allow_nan=False)
        stamp = datetime.fromisoformat(value["as_of"])
        if (
            value.get("schema") != "submission_bottleneck_monitor_v1"
            or value.get("date") != day
            or not isinstance(value.get("run_id"), str)
            or not re.fullmatch(r"[0-9a-f]{32}", value["run_id"])
            or value.get("execution_status") != "completed"
            or value.get("semantic_status") not in {"partial", "validated"}
            or stamp.tzinfo is None
            or stamp.astimezone(H.KST).date().isoformat() != day
            or stamp > datetime.now(H.KST)
        ):
            raise ValueError("observer_identity_invalid")
        return dict(
            schema="startup_observer_predecessor_v1",
            status="captured",
            path=str(path),
            sha256=_digest(raw),
            mtime_ns=after.st_mtime_ns,
            **{
                key: value[key]
                for key in (
                    "date",
                    "as_of",
                    "run_id",
                    "execution_status",
                    "semantic_status",
                )
            },
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return dict(
            schema="startup_observer_predecessor_v1",
            status="unavailable",
            path=str(path),
            reason=type(exc).__name__,
        )


def _main_pids():
    result = subprocess.run(
        ["pgrep", "-f", "[/]python bot_main[.]py$"], capture_output=True, text=True
    )
    if result.returncode not in (0, 1):
        raise ValueError("deployment_process_inventory_failed")
    return [int(value) for value in result.stdout.split()]


def _session_absent():
    result = subprocess.run(["tmux", "has-session", "-t", "=bot"], capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError("deployment_supervisor_inventory_failed")
    return result.returncode == 1


def _launch(plan):
    for attempt in range(3):
        if _main_pids() or not _session_absent():
            raise ValueError("deployment_supervisor_or_main_appeared")
        result = subprocess.run(
            plan["command"], cwd=plan["cwd"], capture_output=True, timeout=15
        )
        if result.returncode == 0:
            return
        if attempt == 2:
            raise ValueError("deployment_supervisor_launch_failed")
        # The tmux server can outlive the drained final session briefly.
        time.sleep(1)


def _wait(predicate, timeout, reason):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise ValueError(reason)
        time.sleep(0.25)


def _drain_actor(workspace, identity, launcher, launcher_start, *, request, guard):
    """One cooperative Main/supervisor shutdown, with the original bounds."""
    guard()
    if H._identity(identity["pid"]) != identity:
        raise ValueError("deployment_predecessor_identity_changed")
    if (Path("/proc", str(launcher), "stat").read_text().rsplit(")", 1)[1].split()[19]
            != launcher_start):
        raise ValueError("deployment_supervisor_identity_changed")
    flag = Path(workspace) / "restart.flag"
    with flag.open("x") as out:
        out.write(request)
        out.flush()
        os.fsync(out.fileno())
    _wait(lambda: not Path("/proc", str(identity["pid"])).exists(),
          90, "deployment_graceful_stop_timeout")
    _wait(lambda: not Path("/proc", str(launcher)).exists() and _session_absent(),
          20, "deployment_supervisor_stop_timeout")
    guard()
    if _main_pids() or flag.exists() or flag.is_symlink():
        raise ValueError("deployment_drain_not_complete")


@contextmanager
def _source_database_epoch(workspace, day):
    """Keep native WAL readers resident across drain, launch and attestation."""
    from src.engine.automation import main_trailing_source_store as store
    from src.engine.lifecycle.research_input_budget import Claim

    data = (Path(workspace) / "data").resolve(strict=True)
    with ExitStack() as readers:
        for namespace in store.NAMESPACES:
            target = store._index_path(data, namespace, day)
            if target.exists() or target.is_symlink():
                claim = Claim(2 * 1024 * 1024)
                readers.callback(claim.close)
                readers.enter_context(store._connection(target, readonly=True))
        yield


@contextmanager
def sentinel_preparation_lock(driver):
    """Reserve the existing producer before drain and release before startup."""
    if getattr(driver, "_sentinel_preparation_owned", False) is True:
        yield
        return
    path = Path(driver.workspace) / "tmp/run_buy_funnel_sentinel.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as lock:

        def acquire():
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            return True

        _wait(acquire, 60, "deployment_sentinel_preparation_owner_busy")
        driver._sentinel_preparation_owned = True
        try:
            yield
        finally:
            driver._sentinel_preparation_owned = False


def stopped_preparation_failure_sources(failed, failed_path):
    """Authenticate native preparation and an exact retained prestart failure."""
    phase_error = failed.get("failed_phase"), failed.get("error")
    if failed.get("phase") != "failed" or failed.get("status") != "fail":
        return {}
    sources = {}
    known = phase_error in {
        ("selected", "[Errno 11] Resource temporarily unavailable"),
        ("prepared", "tuple indices must be integers or slices, not str"),
        ("prepared", "deployment_selection_changed"),
    }
    if not known and phase_error[0] == "prepared":
        # A short native P5 reference retains the original failed report. It
        # authorizes only stopped recovery after the missing prepared-code
        # handoffs have been repaired, never launch or a replacement verdict.
        error = phase_error[1]
        if not isinstance(error, str) or len(error) > 1024 * 1024:
            return {}
        base = (
            Path(failed_path).parents[4]
            / "report/main_startup_validation"
            / failed["target_date"]
        )
        short = error.startswith("selected_p5_failed:")
        if short:
            path = Path(error.removeprefix("selected_p5_failed:"))
            if (
                path.parent.parent != base
                or path.name != "final.json"
                or re.fullmatch("[0-9a-f]{32}", path.parent.name) is None
            ):
                raise ValueError("deployment_prestart_failure_identity_invalid")
            native, raw, _ = _owned_metadata(path)
            value = native
            finding = "ValueError:prepared_code_intraday_custody_invalid"
        else:
            if not error.startswith("{'schema': 'main_policy_load_exit_validation_v1'"):
                return {}
            value = ast.literal_eval(error)
            run = value.get("run_id", "")
            if not isinstance(run, str) or re.fullmatch("[0-9a-f]{32}", run) is None:
                raise ValueError("deployment_prestart_failure_identity_invalid")
            path = base / run / "final.json"
            native, raw, _ = _owned_metadata(path)
            finding = "ValueError:startup_main_code_pair_unreviewed:src/engine/scalping/reversal_code_handoff.py"
        intake = native.get("native_preparation_checks", {}).get("intake", {})
        native_intake_failure = short and native.get("findings") == [
            "ValueError:startup_native_preparation_result_invalid"
        ]
        if native_intake_failure:
            finding = native["findings"][0]
            lifecycle = intake.get("native_process_lifecycle") or {}
            source_day = (failed.get("candidate_report_currentness") or {}).get(
                "source_date"
            )
            intake_bound = (
                isinstance(source_day, str)
                and source_day < failed.get("target_date", "")
                and intake.get("source_date") == source_day
                and (intake.get("native_validation_io") or {}).get("source_date")
                == source_day
                and intake.get("status") == "invalid_result"
                and intake.get("exit_code") == 1
                and intake.get("diagnostics_status") == "observed"
                and native.get("load_check_passed") is False
                and native.get("child_terminated") is False
                and lifecycle.get("ownership_basis")
                == "dedicated_native_verifier_session"
                and type(lifecycle.get("pid")) is int
                and lifecycle["pid"] > 0
                and lifecycle.get("process_group") == lifecycle["pid"]
                and lifecycle.get("session_id") == lifecycle["pid"]
                and isinstance(lifecycle.get("start_ticks"), str)
                and lifecycle["start_ticks"].isdigit()
                and lifecycle.get("child_terminated") is True
                and lifecycle.get("descendants_drained") is True
                and lifecycle.get("cleanup_required") is False
            )
        else:
            intake_bound = (
                intake.get("status") == "pass" and intake.get("findings") == []
            )
        if (
            native != value
            or native.get("schema") != "main_policy_load_exit_validation_v1"
            or native.get("status") != "failed"
            or native.get("failure_phase") != "intake"
            or native.get("target_date") != failed.get("target_date")
            or native.get("findings") != [finding]
            or native.get("run_id") != path.parent.name
            or any(
                native.get(key) is not False
                for key in (
                    "runtime_effect",
                    "actual_pid_consumed",
                    "allowed_runtime_apply",
                )
            )
            or not intake_bound
            or intake.get("target_date") != failed.get("target_date")
            or intake.get(
                "selected_release_commit",
                failed.get("candidate_commit") if native_intake_failure else None,
            )
            != failed.get("candidate_commit")
            or intake.get(
                "verification_code_commit",
                failed.get("candidate_commit") if native_intake_failure else None,
            )
            != failed.get("candidate_commit")
            or intake.get(
                "verification_code_root",
                failed.get("candidate_root") if native_intake_failure else None,
            )
            != failed.get("candidate_root")
        ):
            raise ValueError("deployment_prestart_failure_binding_invalid")
        sources[str(path)] = _digest(raw)
        known = True
    if not known:
        return {}
    if phase_error[0] == "prepared":
        window = failed.get("sentinel_source_window") or {}
        summary = failed.get("sentinel_summary") or {}
        if (
            window.get("schema") != "sentinel_source_window_preparation_v1"
            or window.get("target_date") != failed.get("target_date")
            or window.get("runtime_effect") is not False
            or summary.get("status") != "ok"
            or summary.get("runtime_effect") is not False
        ):
            raise ValueError("deployment_prepared_stage_proof_invalid")
    for module in (
        "intraday_release_handoff",
        "runtime_policy_bootstrap",
        "auxiliary_reader_readiness",
    ):
        path = Path(failed_path).with_name("selected-" + module + ".log")
        value, raw, _ = _owned_metadata(path)
        if (
            value.get("status") != "pass"
            or value.get("target_date") != failed.get("target_date")
            or value.get("findings")
            or value.get("actual_pid_consumed") is True
        ):
            raise ValueError("deployment_selected_preparation_proof_invalid")
        sources[str(path)] = _digest(raw)
    return sources


def execute(driver, *, validate_prepared=None):
    """Order is deliberate: no selection or shared document write before drain."""
    if isinstance(getattr(driver, "auxiliary_repair_path", None), (str, Path)) and validate_prepared is None:
        raise ValueError("deployment_auxiliary_repair_selected_p5_required")
    with R.scheduled_execution_lease(driver.workspace, exclusive=True):
        try:
            # Reserve before preflight so a periodic producer cannot enter
            # during expensive validation. Release before selected P5/start.
            with ExitStack() as preparation:
                preparation.enter_context(sentinel_preparation_lock(driver))
                driver.preflight()
                with _source_database_epoch(driver.workspace, driver.day):
                    driver.acquire_hold()
                    driver.drain()
                    driver.publish()
                    driver.prepare()
                    preparation.close()
                    if validate_prepared is not None:
                        validate_prepared(driver)
                    driver.start()
                    return driver.attest()
        except BaseException as exc:
            driver.fail(exc)
            raise


def _compatible_validation_session(previous, candidate, module):
    """Opt in only to the reviewed CLI/cache implementation, without executing it."""
    if module not in {
        "src.engine.automation.intraday_release_handoff",
        "src.engine.automation.runtime_policy_bootstrap",
    }:
        return False

    def read(root, relative):
        path = Path(root) / relative
        before = _metadata_signature(path)
        if not stat.S_ISREG(before[2]) or not 0 < before[6] <= 2 * 1024 * 1024:
            raise ValueError("validation_cli_source_not_bounded_regular")
        descriptor = os.open(
            path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        )
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            identity = tuple(
                getattr(opened, "st_" + name)
                for name in (
                    "dev",
                    "ino",
                    "mode",
                    "nlink",
                    "uid",
                    "gid",
                    "size",
                    "mtime_ns",
                    "ctime_ns",
                )
            )
            if identity != before:
                raise ValueError("validation_cli_descriptor_changed")
            raw = handle.read(2 * 1024 * 1024 + 1)
        if len(raw) != before[6] or _metadata_signature(path) != before:
            raise ValueError("validation_cli_source_changed")
        return raw

    try:
        cache = "src/engine/infrastructure/validation_digest_session.py"
        if read(previous, cache) != read(candidate, cache):
            return False
        relative = module.replace(".", "/") + ".py"
        old, new = read(previous, relative), read(candidate, relative)
        if b"--validation-session" not in new:
            return False

        def contract(raw):
            tree = ast.parse(raw)
            # Only this reviewed code-pin table differs in the incumbent CLI.
            # Its values do not implement flags or cache behavior; all other
            # module syntax, including every validation call, must be identical.
            for node in tree.body:
                if (
                    module.endswith(".intraday_release_handoff")
                    and isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES"
                ):
                    node.value = ast.Constant(value="reviewed_receipt_source_pairs")
            return ast.dump(tree, include_attributes=False)

        return contract(old) == contract(new)
    except (OSError, ValueError, SyntaxError, UnicodeError):
        return False


def pin_collector_shutdown(workspace, identity):
    """Pin the actual collector actor before any stop request is published."""
    path = (
        Path(workspace)
        / "data/runtime/scalp_micro_reversion_forward_collector/latest.json"
    )
    payload, raw = R._startup_receipt(path)
    snapshot = payload.get("collector_snapshot") or {}
    if snapshot.get("collector_lifecycle") == "closed":
        return _pin_closed_collector(Path(workspace), identity, path, payload, raw)
    if not Path("/proc", str(identity["pid"])).exists():
        proof = H.closed_consumption_observation()
        if (
            proof.get("basis") != "interrupted_consumed_process"
            or proof.get("pid_identity") != identity
            or proof.get("collector_path") != str(path)
            or proof.get("collector_sha256") != _digest(raw)
            or _main_pids()
            or not _session_absent()
        ):
            raise ValueError("deployment_interrupted_collector_unproven")
        return dict(
            path=str(path),
            sha256=_digest(raw),
            pid=identity["pid"],
            start_ticks=identity["start_ticks"],
            sequence_epoch=proof["collector_epoch"],
            basis="interrupted_consumed_process",
            source_admission="unverified_interrupted_epoch",
            terminal_verified=False,
            original_collector_receipt=payload,
            historical_consumption=proof,
        )

    if (
        snapshot.get("process_pid") != identity["pid"]
        or snapshot.get("process_start_ticks") != identity["start_ticks"]
        or snapshot.get("collector_lifecycle") != "running"
        or type(snapshot.get("sequence_epoch")) is not int
        or snapshot["sequence_epoch"] <= 0
        or payload.get("valid_until_epoch", 0) < time.time()
        or snapshot.get("source_contract") != "main_market_source_v1"
    ):
        raise ValueError("deployment_collector_shutdown_actor_unproven")
    return dict(
        path=str(path),
        sha256=_digest(raw),
        pid=identity["pid"],
        start_ticks=identity["start_ticks"],
        sequence_epoch=snapshot["sequence_epoch"],
        enqueued_count=snapshot["enqueued_count"],
    )


def _pin_closed_collector(workspace, identity, path, payload, raw):
    """Bind an already closed native epoch without requiring Main to be closed.

    A modern observer-only latency canary can end before its live Main. Legacy
    closures still require market-close and WS actor proof. Both require exact
    native writer reconciliation before any restart request.
    """
    from src.engine.error_detectors.process_health import _is_expected_thread_terminal

    selected, _ = R._startup_receipt(
        workspace / "data/runtime/runtime_release_selection.json"
    )
    heartbeat, _ = R._startup_receipt(workspace / "tmp/error_detector_heartbeat.json")
    receipt = selected.get("actual_pid_receipt") or {}
    terminal = (heartbeat.get("threads") or {}).get("sniper_engine") or {}
    circuit = heartbeat.get("ai_circuit") or {}
    snapshot = payload["collector_snapshot"]
    now = datetime.now(H.KST)
    recorded = datetime.fromisoformat(str(receipt.get("recorded_at_kst") or ""))
    closed = datetime.fromisoformat(str(payload.get("generated_at") or ""))
    ended = datetime.fromisoformat(str(terminal.get("last_beat") or ""))
    epoch = snapshot.get("sequence_epoch")
    canary_stop = snapshot.get("canary_auto_stop_reason")
    if (
        any(value.tzinfo is None for value in (recorded, closed, ended))
        or not recorded <= closed <= now
        or not recorded <= ended <= now
        or any(
            value.astimezone(H.KST).date() != now.date()
            for value in (recorded, closed, ended)
        )
        or selected.get("actual_pid_consumed") is not True
        or receipt.get("pid") != identity["pid"]
        or receipt.get("start_ticks") != identity["start_ticks"]
        or receipt.get("process_cwd") != identity["cwd"]
        or identity["cwd"] != str(Path(selected.get("release_root") or "") / "src")
        or type(epoch) is not int
        or epoch <= 0
        or (heartbeat.get("main_loop") or {}).get("pid") != identity["pid"]
        or circuit.get("pid") != identity["pid"]
        or circuit.get("process_start_ticks") != identity["start_ticks"]
        or (
            not canary_stop
            and (
                not ended <= closed
                or terminal.get("alive") is not False
                or type(terminal.get("unresolved_scalping_count")) is not int
                or terminal["unresolved_scalping_count"] != 0
                or terminal.get("unresolved_scalping_codes") != ""
                or not _is_expected_thread_terminal(
                    "sniper_engine", terminal, now_ts=now.timestamp()
                )
            )
        )
    ):
        raise ValueError("deployment_closed_collector_actor_or_terminal_unproven")
    pin = dict(
        path=str(path),
        sha256=_digest(raw),
        pid=identity["pid"],
        start_ticks=identity["start_ticks"],
        sequence_epoch=epoch,
        enqueued_count=snapshot["enqueued_count"],
        basis="native_observer_canary_stop" if canary_stop else "native_market_close",
        terminal=terminal,
    )
    if canary_stop:
        from src.engine.scalping.micro_reversion import canary_monitor as C

        guard_path = (
            Path(selected["release_root"]) / "configs" / C.DEFAULT_GUARD_PATH.name
        )
        if guard_path.is_symlink() or not stat.S_ISREG(guard_path.stat().st_mode):
            raise ValueError("deployment_canary_guard_config_unproven")
        guard = C.load_canary_guard(guard_path)
        evaluated = json.loads(json.dumps(C.evaluate_canary_snapshot(snapshot, guard)))
        reasons = set(evaluated.get("stop_reasons") or ()) - {
            "prior_auto_stop:" + str(canary_stop)
        }
        if (
            not isinstance(canary_stop, str)
            or not reasons
            or set(canary_stop.split(";")) != reasons
            or any(
                not reason.startswith(
                    (
                        "producer_callback_latency_p95_exceeded:",
                        "producer_callback_latency_p99_exceeded:",
                    )
                )
                for reason in reasons
            )
            or evaluated.get("stop_required") is not True
            or evaluated.get("latency_guard_armed") is not True
            or payload.get("canary_guard") != evaluated
            or payload.get("guard_config_sha256") != guard.config_sha256
            or payload.get("baseline_id") != guard.baseline_id
            or H._sha(guard_path) != guard.config_sha256
            or snapshot.get("process_pid") != identity["pid"]
            or snapshot.get("process_start_ticks") != identity["start_ticks"]
        ):
            raise ValueError("deployment_observer_canary_close_unproven")
        pin["guard_config_source"] = dict(
            path=str(guard_path), sha256=guard.config_sha256
        )
    if "process_pid" in snapshot or "process_start_ticks" in snapshot:
        if (
            snapshot.get("process_pid") != identity["pid"]
            or snapshot.get("process_start_ticks") != identity["start_ticks"]
            or snapshot.get("source_contract") != "main_market_source_v1"
        ):
            raise ValueError("deployment_market_closed_collector_unproven")
    else:
        # Legacy receipts alone need the historical WS actor. A modern closed
        # collector may have stopped before this actor ever published a frame.
        frame_path = workspace / "data/runtime/kiwoom_ws_snapshot/latest.json"
        frame, frame_raw = R._startup_receipt(frame_path)
        producer = frame.get("shared_transport_producer") or {}
        frame_at = frame.get("generated_at_epoch")
        if (
            type(frame_at) not in (int, float)
            or not recorded.timestamp() <= frame_at <= closed.timestamp()
            or producer.get("schema") != "shared_ws_transport_producer_v1"
            or producer.get("process")
            != dict(
                pid=identity["pid"],
                start_ticks=int(identity["start_ticks"]),
                boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            )
            or producer.get("source_root") != selected.get("release_root")
            or producer.get("source_commit") != selected.get("git_commit")
            or (producer.get("completed_bar_integrity") or {}).get("observer_epoch")
            != epoch
        ):
            raise ValueError("deployment_market_closed_collector_unproven")
        pin["actor_source"] = dict(path=str(frame_path), sha256=_digest(frame_raw))
    # Require durable full native closure BEFORE publishing a restart flag.
    pin["closed_receipts"] = verify_collector_shutdown(pin)["receipts"]
    return pin


def verify_collector_shutdown(pin, *, owned_interrupted_transition=None):
    """Process exit is insufficient: require its immutable, native closed epoch."""
    from src.engine.scalping.micro_reversion.observer_source_quality import (
        main_raw_epoch_validation,
        source_close_verified,
        source_loss_counters,
        CANARY_FORBIDDEN_TRUE_FIELDS,
    )

    path = Path(pin["path"])
    payload, raw = R._startup_receipt(path)
    snapshot = payload.get("collector_snapshot") or {}
    if pin.get("basis") == "interrupted_consumed_process":
        if (
            _digest(raw) != pin["sha256"]
            or payload != pin["original_collector_receipt"]
            or (H.closed_consumption_observation(
                owned_interrupted_transition=owned_interrupted_transition
            ) if owned_interrupted_transition is not None else H.closed_consumption_observation())
            != pin["historical_consumption"]
            or _main_pids()
            or not _session_absent()
        ):
            raise ValueError("deployment_interrupted_collector_changed")
        return dict(
            status="preserved_unverified",
            pid=pin["pid"],
            start_ticks=pin["start_ticks"],
            sequence_epochs=[pin["sequence_epoch"]],
            receipts=[],
            terminal_verified=False,
            source_admission="unverified_interrupted_epoch",
        )
    epochs = snapshot.get("reconciled_sequence_epochs") or []
    if (
        not isinstance(epochs, list)
        or not epochs
        or any(type(epoch) is not int or epoch <= 0 for epoch in epochs)
    ):
        raise ValueError("deployment_collector_closed_epochs_invalid")
    already_closed = pin.get("basis") in {
        "native_market_close",
        "native_observer_canary_stop",
    }
    guard = pin.get("guard_config_source")
    if pin.get("basis") == "native_observer_canary_stop" and not isinstance(
        guard, dict
    ):
        raise ValueError("deployment_canary_guard_config_missing")
    if guard and (
        Path(guard["path"]).is_symlink() or H._sha(guard["path"]) != guard["sha256"]
    ):
        raise ValueError("deployment_canary_guard_config_changed")
    if already_closed:
        actor = pin.get("actor_source")
        if (
            _digest(raw) != pin["sha256"]
            or actor is not None
            and _digest(R._startup_receipt(Path(actor["path"]))[1]) != actor["sha256"]
            or actor is None
            and (
                snapshot.get("process_pid") != pin["pid"]
                or snapshot.get("process_start_ticks") != pin["start_ticks"]
                or snapshot.get("source_contract") != "main_market_source_v1"
            )
        ):
            raise ValueError("deployment_market_closed_collector_changed")
    if (
        not already_closed
        and (
            snapshot.get("process_pid") != pin["pid"]
            or snapshot.get("process_start_ticks") != pin["start_ticks"]
        )
        or pin["sequence_epoch"] not in epochs
        or snapshot.get("enqueued_count", -1) < pin["enqueued_count"]
    ):
        raise ValueError("deployment_collector_closed_identity_invalid")
    dates = sorted(snapshot.get("writer_bytes_by_trade_date") or {})
    if not dates:
        dates = [
            datetime.fromisoformat(payload["generated_at"])
            .astimezone(H.KST)
            .date()
            .isoformat()
        ]
    proofs = []
    semantic_verdicts = []
    for day in dates:
        receipt = path.parent / "closed" / f"{day}-{snapshot['sequence_epoch']}.json"
        closed, raw = R._startup_receipt(receipt)
        native = main_raw_epoch_validation(closed, source_date=day)
        # A latency canary deliberately remains semantically ineligible. The
        # deployment consumes byte closure only, never rewrites that guard or
        # grants research/trading admission to the stopped epoch.
        canary_drained = (
            pin.get("basis") == "native_observer_canary_stop"
            and closed.get("canary_guard") == payload.get("canary_guard")
            and closed.get("guard_config_sha256") == guard["sha256"]
            and closed.get("baseline_id") == payload.get("baseline_id")
            and native.get("status") == "main_raw_epoch_contract_invalid"
            and snapshot.get("source_contract") == "main_market_source_v1"
            and snapshot.get("collector_lifecycle") == "closed"
            and source_close_verified(snapshot)
            and all(
                type(snapshot.get(k)) is int and snapshot[k] == 0
                for k in source_loss_counters(snapshot)
            )
            and snapshot.get("broker_order_forbidden") is True
            and all(snapshot.get(k) is False for k in CANARY_FORBIDDEN_TRUE_FIELDS)
        )
        # A closed source can remain research-ineligible (for example mixed
        # row exclusions). Deployment needs lossless writer closure, not source
        # admission. Keep the native semantic verdict unchanged in this receipt.
        generated = datetime.fromisoformat(closed["generated_at"])
        groups = [("enqueued_count", "worker_processed_count",
                   "writer_persisted_envelope_count", "path_point_submitted_count")]
        if snapshot.get("depth_capture_requested") is True:
            groups.append(("depth_enqueued_count", "depth_worker_processed_count",
                           "depth_writer_persisted_envelope_count"))
        reconciled_closed = (
            snapshot.get("process_pid") == pin["pid"]
            and snapshot.get("process_start_ticks") == pin["start_ticks"]
            and generated.tzinfo is not None
            and generated <= datetime.now(H.KST)
            and closed.get("source_date", generated.astimezone(H.KST).date().isoformat()) == day
            and closed.get("generated_at") == payload.get("generated_at")
            and closed.get("canary_guard") == payload.get("canary_guard")
            and (closed.get("canary_guard") or {}).get("status") == "stopped_clean"
            and (closed.get("canary_guard") or {}).get("stop_required") is False
            and (closed.get("canary_guard") or {}).get("stop_reasons") in ([], ())
            and snapshot.get("source_contract") == "main_market_source_v1"
            and snapshot.get("collector_lifecycle") == "closed"
            and source_close_verified(snapshot)
            and snapshot.get("broker_order_forbidden") is True
            and all(snapshot.get(k) is False for k in CANARY_FORBIDDEN_TRUE_FIELDS)
            and all(type(snapshot.get(k)) is int and snapshot[k] == 0 for k in (
                *source_loss_counters(snapshot), "stale_sequence_epoch_envelope_count",
                "collector_active_callback_count", "writer_queue_depth", "depth_queue_depth"))
            and all(all(type(snapshot.get(k)) is int and snapshot[k] >= 0 for k in group)
                    and len({snapshot[k] for k in group}) == 1 for group in groups)
        )
        if closed.get("collector_snapshot") != snapshot or not (
            canary_drained or reconciled_closed or native.get("eligible")
        ):
            raise ValueError("deployment_collector_closed_epoch_invalid")
        proofs.append(dict(path=str(receipt), sha256=_digest(raw), source_date=day))
        semantic_verdicts.append(dict(source_date=day, **native))
    if "closed_receipts" in pin and proofs != pin["closed_receipts"]:
        raise ValueError("deployment_collector_closed_receipts_changed")
    return dict(
        status="verified",
        pid=pin["pid"],
        start_ticks=pin["start_ticks"],
        sequence_epochs=epochs,
        receipts=proofs,
        source_admission="native_semantics_unchanged",
        native_source_validation=semantic_verdicts,
        observer_canary_stopped=pin.get("basis") == "native_observer_canary_stop",
    )


def verify_interrupted_transition_hold(workspace, day, identity, transition_path, *, adopted_transition=None):
    """Authenticate the exact preselection hold and its interrupted predecessor.

    The same evidence is needed while the owner is holding startup and after
    this precise failure. It does not establish collector closure or a new PID.
    """
    workspace = Path(workspace).resolve(strict=True)
    hold_path = (Path(adopted_transition).with_name("failed-startup-hold-before.json")
                 if adopted_transition is not None else workspace / "data/runtime/operator_startup_hold.json")
    hold, hold_raw, hold_sig = _owned_metadata(hold_path)
    commit = hold.get("candidate_commit")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("deployment_interrupted_hold_invalid")
    path = workspace / "data/runtime/release_transitions" / day / commit / "status.json"
    if Path(transition_path) != path or hold.get("transition") != str(path):
        raise ValueError("deployment_interrupted_hold_path_invalid")
    failed, raw, sig = _owned_metadata(path)
    prior_path = path.with_name("selection-before.json")
    prior, prior_raw, prior_sig = _owned_metadata(prior_path)
    selection_path = (prior_path if adopted_transition is not None
                      else workspace / "data/runtime/runtime_release_selection.json")
    selected, selected_raw, selection_sig = _owned_metadata(selection_path)
    closed_path = path.with_name("closed-predecessor.json")
    closed, closed_raw, closed_sig = _owned_metadata(closed_path)
    pin = failed.get("interrupted_collector") or {}
    observation = closed.get("closed_observation") or {}
    phase_ok = (
        failed.get("phase") == "startup_held" and failed.get("status") in (None, "running")
    ) or (
        failed.get("phase") == "failed" and failed.get("status") == "fail"
        and failed.get("failed_phase") == "startup_held"
        and failed.get("error") == "deployment_stopped_recovery_source_invalid"
    )
    if (
        not phase_ok or failed.get("schema") != "ordered_intraday_deployment_v1"
        or failed.get("authority") != CONFIRM or failed.get("target_date") != day
        or failed.get("candidate_commit") != commit
        or failed.get("predecessor_identity") != identity
        or failed.get("predecessor_launcher") != {"pid": None, "start_ticks": None}
        or failed.get("policy_effect") != "unchanged"
        or hold != dict(schema="ordered_deployment_startup_hold_v1", authority=CONFIRM,
                        transition=str(path), target_date=day, candidate_commit=commit,
                        old_pid_identity=identity)
        or prior_raw != selected_raw or failed.get("original_selection_sha256") != _digest(prior_raw)
        or prior.get("git_commit") != failed.get("previous_commit")
        or prior.get("release_root") != failed.get("previous_root")
        or prior.get("actual_pid_consumed") is not True
        or closed != failed.get("closed_predecessor")
        or closed.get("schema") != "intraday_closed_predecessor_verification_v1"
        or closed.get("status") != "pass" or closed.get("target_date") != day
        or closed.get("pid_identity") != identity or closed.get("historical_consumption_verified") is not True
        or closed.get("actual_pid_consumed") is not False or closed.get("runtime_effect") is not False
        or closed.get("selected_release_commit") != prior.get("git_commit")
        or closed.get("release_root") != prior.get("release_root")
        or observation.get("basis") != "interrupted_consumed_process"
        or observation.get("target_date") != day or observation.get("pid_identity") != identity
        or observation.get("selection_sha256") != _digest(prior_raw)
        or observation.get("release_commit") != prior.get("git_commit")
        or observation.get("terminal_verified") is not False
        or observation.get("source_admission") != "unverified_interrupted_epoch"
        or pin.get("basis") != "interrupted_consumed_process"
        or pin.get("historical_consumption") != observation
        or pin.get("pid") != identity.get("pid") or pin.get("start_ticks") != identity.get("start_ticks")
        or pin.get("path") != str(workspace / "data/runtime/scalp_micro_reversion_forward_collector/latest.json")
        or pin.get("sha256") != observation.get("collector_sha256")
        or pin.get("sequence_epoch") != observation.get("collector_epoch")
        or pin.get("terminal_verified") is not False
        or pin.get("source_admission") != "unverified_interrupted_epoch"
        or not isinstance(observation.get("source_hashes"), dict)
        or not observation["source_hashes"]
    ):
        raise ValueError("deployment_interrupted_hold_evidence_invalid")
    p5 = failed.get("candidate_p5") or {}
    R.validate_release(workspace, dict(schema="runtime_release_selection_v1",
        workspace=str(workspace), release_root=failed.get("candidate_root"), git_commit=commit))
    checked_p5 = verify_candidate_p5(workspace, day, Path(failed.get("candidate_root") or ""), commit,
                                     p5.get("path"), p5.get("sha256"), prior)
    if json.loads(_json_bytes(checked_p5)) != p5:
        raise ValueError("deployment_interrupted_hold_p5_changed")
    collector = Path(pin["path"])
    heartbeat = workspace / "tmp/error_detector_heartbeat.json"
    originals = ((collector, path.with_name("interrupted-collector-original.json")),
                 (heartbeat, path.with_name("interrupted-heartbeat-original.json")))
    sources = dict(observation["source_hashes"])
    if adopted_transition is not None:
        live_selection = workspace / "data/runtime/runtime_release_selection.json"
        sources.pop(str(live_selection), None)
        # The successor owns these live pointers after launch. Their original
        # bytes are preserved below and must not freeze the next PID's writes.
        sources.pop(str(collector), None)
        sources.pop(str(heartbeat), None)
        adoption_path = Path(adopted_transition)
        adoption, _, _ = _owned_metadata(adoption_path)
        current_hold, _, _ = _owned_metadata(workspace / "data/runtime/operator_startup_hold.json")
        live, _, _ = _owned_metadata(live_selection)
        transfer = adoption.get("failed_hold_adoption") or {}
        if (
            adoption_path != workspace / "data/runtime/release_transitions" / day / str(adoption.get("candidate_commit")) / "status.json"
            or adoption.get("schema") != "ordered_intraday_deployment_v1"
            or adoption.get("phase") != "selected"
            or adoption.get("authority") != CONFIRM or adoption.get("target_date") != day
            or adoption.get("predecessor_identity") != identity
            or transfer.get("failed_transition_path") != str(path)
            or transfer.get("failed_transition_sha256") != _digest(raw)
            or transfer.get("previous_hold_sha256") != _digest(hold_raw)
            or transfer.get("transfer_status") != "transferred_exact_owned_hold"
            or current_hold != dict(schema="ordered_deployment_startup_hold_v1", authority=CONFIRM,
                transition=str(adoption_path), target_date=day,
                candidate_commit=adoption.get("candidate_commit"), old_pid_identity=identity)
            or live.get("deployment_transition") != str(adoption_path)
            or live.get("git_commit") != adoption.get("candidate_commit")
            or live.get("actual_pid_consumed") is not False
            or live.get("previous_git_commit") != prior.get("git_commit")
            or live.get("previous_release_root") != prior.get("release_root")
        ):
            raise ValueError("deployment_interrupted_hold_transfer_invalid")
        sources[str(hold_path)] = _digest(hold_raw)
        sources[str(path)] = _digest(raw)
    sources[str(closed_path)] = _digest(closed_raw)
    sources[str(prior_path)] = _digest(prior_raw)
    sources[str(p5["path"])] = p5["sha256"]
    for original, saved in originals:
        _, saved_raw, _ = _owned_metadata(saved)
        if (_digest(saved_raw) != observation["source_hashes"].get(str(original))
            or H._sha(original) != _digest(saved_raw)):
            raise ValueError("deployment_interrupted_original_changed")
        sources[str(saved)] = _digest(saved_raw)
    if (any(H._sha(p) != sha for p, sha in sources.items())
        or _main_pids() or not _session_absent()
        or Path("/proc", str(identity["pid"])).exists()):
        raise ValueError("deployment_interrupted_sources_changed")
    return dict(observation=observation, sources=sources, transition_sha256=_digest(raw),
                transition_signature=sig, hold_sha256=_digest(hold_raw), hold_signature=hold_sig,
                prior_signature=prior_sig, selection_signature=selection_sig, closed_signature=closed_sig)


class Deployment:
    def __init__(
        self,
        workspace,
        candidate,
        day,
        confirm,
        *,
        adopt_failed_hold=False,
        operator_hold_sha256=None,
        candidate_p5_path=None,
        candidate_p5_sha256=None,
        auxiliary_repair_path=None,
        auxiliary_repair_sha256=None,
    ):
        if confirm != CONFIRM:
            raise ValueError("ordered_deployment_explicit_approval_required")
        H._today(day, None)
        self.workspace = Path(workspace).resolve(strict=True)
        self.candidate = Path(candidate).resolve(strict=True)
        self.day = day
        self.selection = self.workspace / "data/runtime/runtime_release_selection.json"
        self.hold = self.workspace / "data/runtime/operator_startup_hold.json"
        self.flag = self.workspace / "restart.flag"
        self.phase = "new"
        self.hold_bytes = None
        self.validation_session = uuid.uuid4().hex
        # Explicit embedding-only recovery; the ordinary CLI never adopts holds.
        if type(adopt_failed_hold) is not bool:
            raise ValueError("deployment_failed_hold_adoption_flag_invalid")
        self.adopt_failed_hold = adopt_failed_hold
        self.failed_hold_adoption = None
        self.operator_hold_sha256 = operator_hold_sha256
        self.operator_hold_adoption = None
        if operator_hold_sha256 is not None and (
            not isinstance(operator_hold_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", operator_hold_sha256) is None
            or adopt_failed_hold
        ):
            raise ValueError("deployment_operator_hold_adoption_invalid")
        self._preflight_native_verified = False
        self.preserve_editable_checklist = True
        self.candidate_p5_path = candidate_p5_path
        self.candidate_p5_sha256 = candidate_p5_sha256
        self.auxiliary_repair_path = auxiliary_repair_path
        self.auxiliary_repair_sha256 = auxiliary_repair_sha256

    def pin_auxiliary_repair(self):
        """Verify the complete issued successor and incumbent PID before drain."""
        if getattr(self, "auxiliary_repair_path", None) is None and getattr(self, "auxiliary_repair_sha256", None) is None:
            return
        if not self.auxiliary_repair_path or not re.fullmatch(
            r"[0-9a-f]{64}", self.auxiliary_repair_sha256 or ""
        ):
            raise ValueError("deployment_auxiliary_repair_reference_invalid")
        from src.engine.scalping import reversal_auxiliary_intraday as auxiliary

        path = Path(self.auxiliary_repair_path)
        manifest, raw, _ = _owned_metadata(path)
        if _digest(raw) != self.auxiliary_repair_sha256 or auxiliary.read(path) != manifest:
            raise ValueError("deployment_auxiliary_repair_reference_changed")
        data = self.workspace / "data"
        prepared_at = datetime.fromisoformat(manifest["prepared_at"])
        if prepared_at.tzinfo is None or prepared_at > datetime.now(H.KST):
            raise ValueError("deployment_auxiliary_repair_clock_invalid")
        original = self.run_auxiliary_native("prepare", manifest)
        if original != manifest or manifest.get("day") != self.day:
            raise ValueError("deployment_auxiliary_repair_preparation_changed")
        consumption = auxiliary.read(
            auxiliary.root(data) / "consumed" / self.day / (str(self.identity["pid"]) + ".json")
        )
        if (consumption.get("actual_pid_consumed") is not True
            or consumption.get("day") != self.day
            or consumption.get("pid_identity") != self.identity
            or consumption.get("release_commit") != self.previous_commit
            or consumption.get("base_bundle_sha256") != manifest["base_bundle_sha256"]
            or consumption.get("overlay_sha256") != manifest["expected_parent"]
            or consumption.get("code_hashes") != auxiliary.code_hashes()
            or consumption.get("bindings") != manifest["old_bindings"]):
            raise ValueError("deployment_auxiliary_repair_incumbent_binding_invalid")
        for mutable in (auxiliary.root(data) / "current.json",
                        auxiliary.root(data) / "days" / self.day / (manifest["base_bundle_sha256"] + ".json")):
            if str(mutable) in self.frozen:
                raise ValueError("deployment_auxiliary_repair_pointer_frozen")
        additions = {str(path): _digest(raw), **manifest["source_hashes"]}
        if any(name in self.frozen and self.frozen[name] != sha for name, sha in additions.items()):
            raise ValueError("deployment_auxiliary_repair_frozen_source_conflict")
        self.frozen.update(additions)
        self.auxiliary_repair = manifest
        self.state["auxiliary_repair_preflight"] = dict(path=str(path), sha256=_digest(raw),
            manifest_sha256=manifest["artifact_content_sha256"], base_bundle_sha256=manifest["base_bundle_sha256"])

    def run_auxiliary_native(self, operation, manifest):
        """Invoke the original native reader and transfer its exact issued bytes."""
        from src.engine.scalping import reversal_auxiliary_intraday as auxiliary

        if operation not in {"prepare", "publish", "rollback"}:
            raise ValueError("deployment_auxiliary_native_operation_invalid")
        if self.selection.read_bytes() != self.before:
            raise ValueError("deployment_auxiliary_native_selection_changed")
        if operation != "prepare":
            self.assert_hold()
            if self.phase != "drained" or _main_pids() or not _session_absent():
                raise ValueError("deployment_auxiliary_native_not_drained")
        R.validate_release(self.workspace, dict(schema="runtime_release_selection_v1",
            workspace=str(self.workspace), release_root=str(self.previous), git_commit=self.previous_commit))
        path = Path(self.auxiliary_repair_path)
        pinned, raw, _ = _owned_metadata(path)
        if pinned != manifest or _digest(raw) != self.auxiliary_repair_sha256:
            raise ValueError("deployment_auxiliary_native_manifest_changed")
        codes = auxiliary.code_hashes()
        request = dict(operation=operation, data_root=str(self.workspace / "data"), day=self.day,
            origin_commit=self.previous_commit, selection_sha256=_digest(self.before),
            code_hashes=codes, manifest_path=str(path), manifest_sha256=_digest(raw),
            hold_sha256=(_digest(self.hold_bytes) if operation != "prepare" else None))
        result = subprocess.run([str(self.previous / ".venv/bin/python"), "-B", "-c",
            _AUXILIARY_ORIGIN_SCRIPT, json.dumps(request)], cwd=self.previous,
            env={**os.environ, "PYTHONPATH": str(self.previous)}, capture_output=True, text=True, timeout=120)
        _atomic(self.directory / (self.phase + "-auxiliary-native-" + operation + ".log"),
                (result.stdout + result.stderr).encode())
        if result.returncode:
            raise ValueError("deployment_auxiliary_native_failed:" + operation)
        value = json.loads(result.stdout)
        if (value.get("status") != "pass" or value.get("operation") != operation
            or value.get("origin_root") != str(self.previous)
            or value.get("origin_commit") != self.previous_commit
            or value.get("code_hashes") != codes or auxiliary.code_hashes() != codes
            or self.selection.read_bytes() != self.before):
            raise ValueError("deployment_auxiliary_native_result_invalid")
        if _owned_metadata(path)[1] != raw:
            raise ValueError("deployment_auxiliary_native_manifest_changed")
        record = value.get("record")
        if record is not None and operation != "prepare":
            expected = auxiliary.root(self.workspace / "data") / "generations" / (record["artifact_content_sha256"] + ".json")
            reference = value.get("reference") or {}
            if (reference.get("path") != str(expected) or reference.get("sha256") != H._sha(expected)
                or auxiliary.read(expected) != record):
                raise ValueError("deployment_auxiliary_native_receipt_invalid")
        R.validate_release(self.workspace, dict(schema="runtime_release_selection_v1",
            workspace=str(self.workspace), release_root=str(self.previous), git_commit=self.previous_commit))
        if operation != "prepare":
            self.assert_hold()
            if _main_pids() or not _session_absent():
                raise ValueError("deployment_auxiliary_native_not_drained")
        return record

    def inherit_auxiliary_repair(self, origin, active_check):
        """Keep an already-issued repair across native stopped recovery."""
        published = origin["failed"].get("auxiliary_repair_published")
        if not published:
            return {}
        from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
        from src.engine.scalping import mechanistic_entry_runtime_policy as native

        before = origin["failed"].get("auxiliary_repair_preflight") or {}
        path = Path(before.get("path") or "")
        manifest, raw, _ = _owned_metadata(path)
        data = self.workspace / "data"
        bundle_sha = active_check["bundle_sha256"]
        bundle = native._read(native.root(data) / "generations" / (bundle_sha + ".json"))
        native.validate(bundle, target_date=self.day)
        overlay = auxiliary.current(data, bundle, day=self.day)
        if (_digest(raw) != before.get("sha256") or auxiliary.read(path) != manifest
            or manifest.get("artifact_content_sha256") != before.get("manifest_sha256")
            or manifest.get("base_bundle_sha256") != bundle_sha
            or overlay is None or overlay.get("artifact_content_sha256") != published
            or overlay.get("contract_repair_manifest_sha256") != manifest["artifact_content_sha256"]
            or overlay.get("bindings") != manifest["new_bindings"]):
            raise ValueError("deployment_recovery_auxiliary_repair_unbound")
        auxiliary.validate_contract_repair_manifest(data, manifest, bundle, force_source_hashes=True)
        generation = auxiliary.root(data) / "generations" / (published + ".json")
        if auxiliary.read(generation) != overlay:
            raise ValueError("deployment_recovery_auxiliary_generation_changed")
        self.auxiliary_repair_path, self.auxiliary_repair_sha256 = path, _digest(raw)
        self.auxiliary_repair, self.auxiliary_overlay = manifest, overlay
        self.auxiliary_repair_reused = dict(manifest_path=str(path), manifest_sha256=_digest(raw),
            overlay_path=str(generation), overlay_sha256=H._sha(generation),
            source_transition=str(origin["failed_path"]), source_transition_sha256=_digest(origin["failed_raw"]))
        return {**manifest["source_hashes"], str(path): _digest(raw),
                str(generation): H._sha(generation),
                str(auxiliary.root(data) / "current.json"): H._sha(auxiliary.root(data) / "current.json")}

    def pin_candidate_p5(self):
        self.candidate_p5 = verify_candidate_p5(
            self.workspace,
            self.day,
            self.candidate,
            self.commit,
            self.candidate_p5_path,
            self.candidate_p5_sha256,
            json.loads(self.before),
        )

    def run_json(self, root, module, *args, timeout=120):
        # Compatible predecessors share this invocation's digest session too.
        # Older/different CLI or cache code retains its native full path.
        if module in {
            "src.engine.automation.intraday_release_handoff",
            "src.engine.automation.runtime_policy_bootstrap",
        } and (
            root == self.candidate
            or _compatible_validation_session(root, self.candidate, module)
        ):
            args = (*args, "--validation-session", self.validation_session)
        result = subprocess.run(
            [str(root / ".venv/bin/python"), "-B", "-m", module, *args],
            cwd=root,
            env={**os.environ, "PYTHONPATH": str(root)},
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if hasattr(self, "directory"):
            name = self.phase + "-" + module.rsplit(".", 1)[-1] + ".log"
            _atomic(self.directory / name, (result.stdout + result.stderr).encode())
        if result.returncode:
            raise ValueError("deployment_validation_failed:" + module)
        value = json.loads(result.stdout)
        if value.get("status") != "pass":
            raise ValueError("deployment_validation_not_pass:" + module)
        return value

    def checkpoint(self, phase, **values):
        self.phase = phase
        self.state.update(
            phase=phase, updated_at=datetime.now(H.KST).isoformat(), **values
        )
        _atomic(self.directory / "status.json", _json_bytes(self.state))

    def observe_report_consumers(self, phase):
        """Carry the same native report-only census through each live phase.

        Source/economic warnings remain observations. Registry/code identity
        must remain the candidate's; these reports acquire no startup authority.
        """
        from src.engine.monitoring.policy_generation_code_handoff import consumer_inventory

        reports = self.state["candidate_report_currentness"]
        baseline = reports["capability_consumers"]
        current = consumer_inventory(
            self.candidate, reports["source_date"], data_root=self.workspace / "data"
        )
        identity = lambda rows: [
            {k: row[k] for k in ("family", "role", "source_date", "code_sha256", "validation_plan_sha256")}
            for row in rows
        ]
        if identity(current) != identity(baseline):
            raise ValueError("deployment_report_consumer_identity_changed")
        self.state.setdefault("report_consumer_observations", {})[phase] = current

    def preflight(self):
        self.before = self.selection.read_bytes()
        self.old = json.loads(self.before)
        self.previous, self.previous_commit = R.selected_release(self.workspace)
        commit = R.git(self.candidate, "rev-parse", "HEAD")
        self.candidate, self.commit = R.validate_release(
            self.workspace,
            {
                "schema": "runtime_release_selection_v1",
                "workspace": str(self.workspace),
                "release_root": str(self.candidate),
                "git_commit": commit,
            },
        )
        self.pin_candidate_p5()
        if Path(__file__).resolve().parents[3] != self.candidate:
            raise ValueError("deployment_must_execute_reviewed_candidate_code")
        if self.candidate == self.previous:
            raise ValueError("deployment_candidate_already_selected")
        from src.engine.scalping.reversal_cumulative_registration import pending_scoring_code_check

        self.pending_scoring = pending_scoring_code_check(self.workspace / "data", self.day)
        for name in ("operator_startup_hold.json",):
            p = self.workspace / "data/runtime" / name
            if p.exists() or p.is_symlink():
                if not getattr(self, "adopt_failed_hold", False) and not getattr(self, "operator_hold_sha256", None):
                    raise ValueError("deployment_existing_operator_hold")
            elif getattr(self, "adopt_failed_hold", False):
                raise ValueError("deployment_failed_hold_required")
        if self.flag.exists() or self.flag.is_symlink():
            raise ValueError("deployment_existing_restart_request")
        receipt = self.old.get("actual_pid_receipt") or {}
        self.closed_predecessor = None
        try:
            self.identity = H._identity(receipt.get("pid"))
        except FileNotFoundError:
            self.closed_predecessor = H.verify_closed_predecessor_consumption(self.day)
            self.identity = self.closed_predecessor["pid_identity"]
        if (
            self.old.get("actual_pid_consumed") is not True
            or self.identity["cwd"] != str(self.previous / "src")
            or _main_pids()
            != ([] if self.closed_predecessor else [self.identity["pid"]])
        ):
            raise ValueError("deployment_predecessor_not_current_singleton")
        operator_closed = bool(self.closed_predecessor and self.closed_predecessor["closed_observation"].get("basis") == "native_preopen_closed")
        if operator_closed:
            hold, _, _ = _owned_metadata(self.hold)
            baseline, _, _ = _owned_metadata(Path(hold["evidence"]) / "baseline.json")
            self.collector_shutdown_pin = baseline["collector_shutdown_pin"]
            verify_collector_shutdown(self.collector_shutdown_pin)
        else:
            self.collector_shutdown_pin = pin_collector_shutdown(self.workspace, self.identity)
        self.launcher = self.launcher_stat = None
        if self.closed_predecessor:
            if not _session_absent():
                raise ValueError("deployment_closed_predecessor_supervisor_present")
        else:
            parent = (
                Path("/proc", str(self.identity["pid"]), "stat")
                .read_text()
                .rsplit(")", 1)[1]
                .split()[1]
            )
            self.launcher = int(parent)
            self.launcher_stat = (
                Path("/proc", parent, "stat").read_text().rsplit(")", 1)[1].split()[19]
            )
            if str(self.previous / "src/run_bot.sh").encode() not in Path(
                "/proc", parent, "cmdline"
            ).read_bytes().split(b"\0"):
                raise ValueError("deployment_predecessor_supervisor_unrecognized")
        self.directory = (
            self.workspace / "data/runtime/release_transitions" / self.day / self.commit
        )
        self.directory.mkdir(parents=True, exist_ok=False)
        self.state = dict(
            schema="ordered_intraday_deployment_v1",
            authority=CONFIRM,
            target_date=self.day,
            previous_root=str(self.previous),
            previous_commit=self.previous_commit,
            candidate_root=str(self.candidate),
            candidate_commit=self.commit,
            predecessor_identity=self.identity,
            runtime_effect="authorized_code_restart_only",
            predecessor_launcher=dict(
                pid=self.launcher, start_ticks=self.launcher_stat
            ),
            policy_effect="unchanged",
            original_selection_sha256=_digest(self.before),
        )
        self.state["candidate_p5"] = self.candidate_p5
        _atomic(self.directory / "selection-before.json", self.before)
        if self.collector_shutdown_pin.get("basis") == "interrupted_consumed_process":
            raw = Path(self.collector_shutdown_pin["path"]).read_bytes()
            if _digest(raw) != self.collector_shutdown_pin["sha256"]:
                raise ValueError("deployment_interrupted_collector_changed")
            _atomic(self.directory / "interrupted-collector-original.json", raw)
            heartbeat = self.workspace / "tmp/error_detector_heartbeat.json"
            heartbeat_raw = heartbeat.read_bytes()
            if (
                _digest(heartbeat_raw)
                != self.closed_predecessor["closed_observation"]["source_hashes"][
                    str(heartbeat)
                ]
            ):
                raise ValueError("deployment_interrupted_heartbeat_changed")
            _atomic(
                self.directory / "interrupted-heartbeat-original.json", heartbeat_raw
            )
            self.state["interrupted_collector"] = self.collector_shutdown_pin
        self.checkpoint("preflight")
        try:
            if self.closed_predecessor:
                check = self.closed_predecessor
                self.state["closed_predecessor"] = check
                _atomic(self.directory / "closed-predecessor.json", _json_bytes(check))
            else:
                check = self.run_json(
                    self.previous,
                    "src.engine.automation.intraday_release_handoff",
                    "--verify",
                    "--target-date",
                    self.day,
                    "--pid",
                    str(self.identity["pid"]),
                )
                self.run_json(
                    self.previous,
                    "src.engine.automation.runtime_policy_bootstrap",
                    "--verify",
                    "--target-date",
                    self.day,
                    "--pid",
                    str(self.identity["pid"]),
                )
        except ValueError:
            if not getattr(self, "preserve_editable_checklist", False):
                raise
            for module in ("intraday_release_handoff", "runtime_policy_bootstrap"):
                log = self.directory / ("preflight-" + module + ".log")
                if log.exists():
                    log.rename(log.with_name("preflight-previous-" + module + ".log"))
            # A repaired reader must revalidate the entire live predecessor;
            # the old failure is retained and never converted to a receipt.
            check = self.run_json(
                self.candidate,
                "src.engine.automation.intraday_release_handoff",
                "--verify-predecessor",
                "--target-date",
                self.day,
                "--pid",
                str(self.identity["pid"]),
            )
            if (
                check.get("status") != "pass"
                or check.get("schema") != "intraday_pid_consumption_verification_v1"
                or check.get("target_date") != self.day
                or not check.get("manifest_sha256")
                or check.get("verification_code_commit") != self.commit
                or check.get("verification_code_root") != str(self.candidate)
                or check.get("selected_release_commit") != self.previous_commit
                or check.get("release_root") != str(self.previous)
                or check.get("pid_identity") != self.identity
                or check.get("actual_pid_consumed") is not True
                or check.get("candidate_pid_consumed") is not False
                or check.get("runtime_effect") is not False
            ):
                raise ValueError("deployment_predecessor_revalidation_unbound")
            self.state["predecessor_revalidation"] = check
        if check.get("basis") == "native_preopen":
            self.seal_native_predecessor(check)
        else:
            path, _ = H._paths(self.day, self.previous_commit)
            self.frozen = H._read(path)["frozen_files"]
        code_check = verify_candidate_delay_code(self.day, self.candidate, self.commit)
        self.prepared_delay_check = code_check
        _atomic(self.directory / "candidate-delay-code.json", _json_bytes(code_check))
        stop_check = H.verify_candidate_stop_code(self.day, self.candidate, self.commit)
        _atomic(self.directory / "candidate-stop-code.json", _json_bytes(stop_check))
        holding_check = H.verify_candidate_holding_vote_code(
            self.day, self.candidate, self.commit
        )
        _atomic(
            self.directory / "candidate-holding-vote-code.json",
            _json_bytes(holding_check),
        )
        active_check = verify_candidate_active_policy(
            self.workspace, self.candidate, self.commit, self.day
        )
        _atomic(
            self.directory / "candidate-active-policy-code.json",
            _json_bytes(active_check),
        )
        self.state["candidate_report_currentness"] = (
            verify_candidate_report_currentness(
                self.workspace, self.candidate, self.day
            )
        )
        self.observe_report_consumers("candidate")
        self.frozen = dict(self.frozen)
        self.frozen.update(
            (code_check.get("prepared_code_origin") or {}).get("sources", {})
        )
        # The selector is transition provenance, asserted separately below.
        self.frozen.pop(str(self.selection), None)
        self.frozen[active_check["receipt_path"]] = active_check["receipt_sha256"]
        self.frozen[active_check["pointer_path"]] = active_check["pointer_sha256"]
        self.pin_auxiliary_repair()
        self.checklist = (
            self.workspace
            / "docs/checklists"
            / (self.day + "-stage2-todo-checklist.md")
        )
        self.document_before = self.checklist.read_bytes()
        if getattr(self, "preserve_editable_checklist", False):
            self.document_after = self.document_before
            # Policy/source receipts remain frozen. The live PID proof above
            # independently validated its consumed historical document.
            self.frozen = dict(self.frozen)
            self.frozen.pop(str(self.checklist), None)
        else:
            self.document_after = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(self.candidate),
                    "show",
                    self.commit + ":docs/checklists/" + self.checklist.name,
                ],
                timeout=10,
            )
        _atomic(self.directory / "checklist-before.md", self.document_before)
        self.assert_unchanged()
        from src.engine.monitoring.sentinel_summary_contract import (
            check_pending_migration,
        )

        self.state["sentinel_summary_preflight"] = check_pending_migration(
            self.workspace / "data", self.day
        )
        self._preflight_native_verified = True
        if getattr(self, "adopt_failed_hold", False):
            # All native predecessor, policy/code and source checks above stay
            # mandatory. No shared hold bytes change during this inspection.
            self.capture_failed_hold_adoption()
            self.assert_unchanged()
        if getattr(self, "operator_hold_sha256", None):
            if not operator_closed:
                raise ValueError("deployment_operator_stop_native_proof_required")
            hold, raw, signature = _owned_metadata(self.hold)
            if _digest(raw) != self.operator_hold_sha256:
                raise ValueError("deployment_operator_hold_changed")
            self.operator_hold_adoption = dict(raw=raw, signature=signature)
            _atomic(self.directory / "operator-startup-hold-before.json", raw)
            self.state["operator_hold_adoption"] = dict(original_sha256=_digest(raw), transfer_status="verified_not_transferred")
            self.checkpoint("preflight")

    def capture_failed_hold_adoption(self):
        if (
            getattr(self, "adopt_failed_hold", False) is not True
            or getattr(self, "_preflight_native_verified", False) is not True
        ):
            raise ValueError("deployment_failed_hold_native_preflight_required")
        hold, raw, signature = _owned_metadata(self.hold)
        expected_transition = (
            self.workspace
            / "data/runtime/release_transitions"
            / self.day
            / self.previous_commit
            / "status.json"
        )
        selected_transition = self.old.get("deployment_transition")
        if (
            selected_transition != str(expected_transition)
            or hold.get("schema") != "ordered_deployment_startup_hold_v1"
            or hold.get("authority") != CONFIRM
            or hold.get("target_date") != self.day
            or hold.get("candidate_commit") != self.previous_commit
            or hold.get("transition") != str(expected_transition)
        ):
            raise ValueError("deployment_failed_hold_identity_invalid")
        if expected_transition.resolve(strict=True) != expected_transition:
            raise ValueError("deployment_failed_transition_path_invalid")
        failed, failed_raw, failed_signature = _owned_metadata(expected_transition)
        old_identity = hold.get("old_pid_identity")
        if (
            failed.get("schema") != "ordered_intraday_deployment_v1"
            or failed.get("authority") != CONFIRM
            or failed.get("target_date") != self.day
            or failed.get("candidate_commit") != self.previous_commit
            or failed.get("candidate_root") != str(self.previous)
            or failed.get("policy_effect") != "unchanged"
            or failed.get("status") != "fail"
            or failed.get("phase") != "failed"
            or failed.get("failed_phase") != "starting"
            or failed.get("error") not in {
                "deployment_pid_attestation_timeout",
                "deployment_original_policy_generation_changed",
            }
            or not isinstance(old_identity, dict)
            or old_identity != failed.get("predecessor_identity")
            or type(old_identity.get("pid")) is not int
            or old_identity["pid"] <= 0
            or not isinstance(old_identity.get("start_ticks"), str)
            or not old_identity["start_ticks"].isdigit()
            or not isinstance(old_identity.get("cwd"), str)
            or not Path(old_identity["cwd"]).is_absolute()
        ):
            raise ValueError("deployment_failed_transition_not_adoptable")
        prior_path = expected_transition.with_name("selection-before.json")
        prior, prior_raw, prior_signature = _owned_metadata(prior_path)
        if (
            prior.get("schema") != "runtime_release_selection_v1"
            or prior.get("actual_pid_consumed") is not True
            or failed.get("original_selection_sha256") != _digest(prior_raw)
            or prior.get("git_commit") != failed.get("previous_commit")
            or prior.get("release_root") != failed.get("previous_root")
            or old_identity.get("cwd") != str(Path(prior["release_root"]) / "src")
            or (prior.get("actual_pid_receipt") or {}).get("pid") != old_identity["pid"]
            or self.old.get("previous_selection_backup") != str(prior_path)
            or self.old.get("previous_git_commit") != prior.get("git_commit")
            or self.old.get("previous_release_root") != prior.get("release_root")
        ):
            raise ValueError("deployment_failed_transition_source_invalid")
        if (
            self.old.get("schema") != "runtime_release_selection_v1"
            or self.old.get("actual_pid_consumed") is not True
            or self.old.get("git_commit") != self.previous_commit
            or self.old.get("release_root") != str(self.previous)
            or (self.old.get("actual_pid_receipt") or {}).get("pid")
            != self.identity["pid"]
            or H._identity(self.identity["pid"]) != self.identity
            or _main_pids() != [self.identity["pid"]]
        ):
            raise ValueError("deployment_failed_hold_current_pid_unverified")
        if failed["error"] == "deployment_original_policy_generation_changed":
            # A stopped-recovery latest pointer advances when the successor
            # collects. Accept this old failure only with the original consumed
            # policy bytes still valid, in addition to fresh current PID proof.
            parent = failed.get("failed_hold_adoption") or {}
            if parent.get("source_failure") == "deployment_stopped_recovery_source_invalid":
                origin = Path(parent.get("failed_transition_path") or "")
                expected = (self.workspace / "data/runtime/release_transitions" / self.day
                            / str(parent.get("failed_selected_commit")) / "status.json")
                previous_failure, previous_raw, _ = _owned_metadata(origin)
                proof_path = origin.with_name("closed-predecessor.json")
                proof, proof_raw, _ = _owned_metadata(proof_path)
                observation = proof.get("closed_observation") or {}
                checked = H._verify_handoff(self.day, self.previous_commit)
                handoff = checked.get("handoff") or {}
                custody = handoff.get("interrupted_recovery_custody") or {}
                p5 = failed.get("candidate_p5") or {}
                checked_p5 = verify_candidate_p5(
                    self.workspace, self.day, self.previous, self.previous_commit,
                    p5.get("path"), p5.get("sha256"), prior,
                )
                mutable = (observation.get("collector_path"),
                           str(self.workspace / "tmp/error_detector_heartbeat.json"))
                if (
                    origin != expected or parent.get("failed_transition_sha256") != _digest(previous_raw)
                    or parent.get("transfer_status") != "transferred_exact_owned_hold"
                    or previous_failure.get("phase") != "failed" or previous_failure.get("status") != "fail"
                    or previous_failure.get("failed_phase") != "startup_held"
                    or previous_failure.get("error") != parent.get("source_failure")
                    or previous_failure.get("predecessor_identity") != old_identity
                    or previous_failure.get("closed_predecessor") != proof
                    or observation.get("basis") != "interrupted_consumed_process"
                    or parent.get("intraday_predecessor_proof_sha256") != _digest(proof_raw)
                    or checked.get("status") != "pass"
                    or custody.get("failed_transition_path") != str(origin)
                    or not isinstance(custody.get("sources"), dict)
                    or json.loads(_json_bytes(checked_p5)) != p5
                    or any(not isinstance(path, str) or not path for path in mutable)
                    or not any(H._sha(path) != observation["source_hashes"].get(path) for path in mutable)
                    or any(path in custody["sources"] for path in mutable)
                ):
                    raise ValueError("deployment_failed_interrupted_custody_unverified")
                self.frozen.update(custody["sources"])
            elif parent.get("source_failure") != "deployment_collector_closed_epoch_invalid":
                raise ValueError("deployment_failed_collector_custody_unverified")
            else:
                native = _stopped_intraday_predecessor(
                    self.day, Path(failed["previous_root"]), failed["previous_commit"],
                    old_identity, expected_transition,
                )
                if native["sha256"] != parent.get("intraday_predecessor_proof_sha256"):
                    raise ValueError("deployment_failed_collector_custody_changed")
                self.frozen.update(native["frozen_files"])
        self.failed_hold_adoption = dict(
            raw=raw,
            signature=signature,
            transition_path=str(expected_transition),
            transition_raw=failed_raw,
            transition_signature=failed_signature,
            prior_path=str(prior_path),
            prior_raw=prior_raw,
            prior_signature=prior_signature,
        )
        proof = dict(
            schema="ordered_failed_startup_hold_adoption_v1",
            authority=CONFIRM,
            target_date=self.day,
            previous_commit=self.previous_commit,
            candidate_commit=self.commit,
            previous_hold_path=str(self.hold),
            previous_hold_sha256=_digest(raw),
            failed_transition_path=str(expected_transition),
            failed_transition_sha256=_digest(failed_raw),
            failed_original_selection_path=str(prior_path),
            failed_original_selection_sha256=_digest(prior_raw),
            source_failure=failed["error"],
            previous_hold_identity=old_identity,
            verified_current_pid_identity=self.identity,
            original_selection_sha256=_digest(self.before),
            transfer_status="verified_not_transferred",
            runtime_effect="authorized_code_restart_only",
            policy_effect="unchanged",
        )
        _atomic(self.directory / "failed-startup-hold-before.json", raw)
        _atomic(self.directory / "failed-transition-before.json", failed_raw)
        _atomic(self.directory / "failed-original-selection-before.json", prior_raw)
        self.checkpoint("preflight", failed_hold_adoption=proof)

    def _assert_failed_transition_unchanged(self):
        adoption = getattr(self, "failed_hold_adoption", None)
        if adoption is None:
            return
        _, raw, signature = _owned_metadata(adoption["transition_path"])
        if (
            raw != adoption["transition_raw"]
            or signature != adoption["transition_signature"]
        ):
            raise ValueError("deployment_failed_transition_changed")
        _, raw, signature = _owned_metadata(adoption["prior_path"])
        if raw != adoption["prior_raw"] or signature != adoption["prior_signature"]:
            raise ValueError("deployment_failed_transition_source_changed")

    def seal_native_predecessor(self, check):
        """Capture verified LIVE native consumption before requesting drain."""
        if (
            check.get("schema") != "intraday_pid_consumption_verification_v1"
            or check.get("status") != "pass"
            or check.get("basis") != "native_preopen"
            or (check.get("actual_pid_consumed") is not True and not (
                check.get("historical_consumption_verified") is True
                and (check.get("closed_observation") or {}).get("basis") == "native_preopen_closed"
                and check == self.closed_predecessor))
            or check.get("target_date") != self.day
            or check.get("selected_release_commit") != self.previous_commit
            or check.get("release_root") != str(self.previous)
            or check.get("pid_identity") != self.identity
            or not check.get("manifest_sha256")
        ):
            raise ValueError("deployment_native_predecessor_unverified")
        index = (
            H.DATA_DIR / "runtime/policy_bootstrap/prepared" / self.day / "latest.json"
        )
        ref = H._read(index)
        receipt = Path(ref["receipt_path"])
        if (
            receipt.resolve().parent.parent != index.parent.resolve()
            or H._sha(receipt) != ref["receipt_sha256"]
        ):
            raise ValueError("deployment_native_prepared_generation_invalid")
        paths = [
            H.bootstrap.env_path(self.day),
            H.bootstrap.manifest_path(self.day),
            H._preopen_path(self.day),
            index,
            receipt,
        ]
        self.frozen = {str(p): H._sha(p) for p in paths}
        self.assert_unchanged()
        if not getattr(self, "closed_predecessor", None) and H._identity(self.identity["pid"]) != self.identity:
            raise ValueError("deployment_native_predecessor_changed")
        snapshots = {}
        if getattr(self, "closed_predecessor", None):
            for original, sha in check["closed_observation"]["source_hashes"].items():
                raw = Path(original).read_bytes()
                if _digest(raw) != sha:
                    raise ValueError("deployment_closed_native_source_changed")
                path = self.directory / "native-source-originals" / (sha + ".bytes")
                path.parent.mkdir(exist_ok=True)
                if not path.exists():
                    _atomic(path, raw)
                snapshots[original] = dict(path=str(path), sha256=sha)
        # PREOPEN can generate today's checklist after this release's Git
        # commit. Preserve its strict-bound bytes before document publication.
        checklist_snapshot = H.preserve_checklist(self.day)
        self.native_path = self.directory / "native-predecessor.json"
        _atomic(
            self.native_path,
            _json_bytes(
                dict(
                    schema="native_preopen_predecessor_v1",
                    authority=CONFIRM,
                    candidate_commit=self.commit,
                    verification=check,
                    frozen_files=self.frozen,
                    closed_source_snapshots=snapshots,
                    original_checklist_snapshot=checklist_snapshot,
                    prepared_receipt_path=str(receipt),
                    prepared_receipt_sha256=ref["receipt_sha256"],
                    selection_before_sha256=_digest(self.before),
                )
            ),
        )
        self.native_sha = H._sha(self.native_path)
        self.frozen[str(self.native_path)] = self.native_sha
        self.frozen.update((item["path"], item["sha256"]) for item in snapshots.values())

    def assert_unchanged(self):
        self._assert_failed_transition_unchanged()
        if hasattr(self, "pending_scoring"):
            from src.engine.scalping.reversal_cumulative_registration import pending_scoring_code_check

            if pending_scoring_code_check(self.workspace / "data", self.day) != self.pending_scoring:
                raise ValueError("deployment_pending_scoring_changed")
        if self.selection.read_bytes() != self.before:
            raise ValueError("deployment_selection_changed")
        if (
            verify_candidate_p5(
                self.workspace,
                self.day,
                self.candidate,
                self.commit,
                self.candidate_p5["path"],
                self.candidate_p5["sha256"],
                json.loads(self.before),
            )
            != self.candidate_p5
        ):
            raise ValueError("deployment_candidate_p5_changed")
        if any(H._sha(path) != sha for path, sha in {
            **self.frozen, **getattr(self, "stopped_collector_source", {})
        }.items()):
            raise ValueError("deployment_predecessor_generation_changed")

    def acquire_hold(self):
        self.assert_unchanged()
        self.hold_bytes = _json_bytes(
            dict(
                schema="ordered_deployment_startup_hold_v1",
                authority=CONFIRM,
                transition=str(self.directory / "status.json"),
                target_date=self.day,
                candidate_commit=self.commit,
                old_pid_identity=self.identity,
            )
        )
        operator_adoption = getattr(self, "operator_hold_adoption", None)
        adoption = operator_adoption or getattr(self, "failed_hold_adoption", None)
        adoption_key = "operator_hold_adoption" if operator_adoption else "failed_hold_adoption"
        if getattr(self, "operator_hold_sha256", None) and (
            operator_adoption is None or not self._preflight_native_verified
            or _digest(operator_adoption["raw"]) != self.operator_hold_sha256
        ):
            raise ValueError("deployment_operator_hold_adoption_unverified")
        if getattr(self, "adopt_failed_hold", False) and (
            adoption is None
            or getattr(self, "_preflight_native_verified", False) is not True
        ):
            raise ValueError("deployment_failed_hold_adoption_unverified")
        if adoption is None:
            with self.hold.open("xb") as out:
                out.write(self.hold_bytes)
                out.flush()
                os.fsync(out.fileno())
        else:
            # Existing release-set serialization remains required by execute's
            # caller. The same selector lock also excludes native PID writers.
            with _existing_selector_lock(
                self.workspace / "data/runtime/runtime_release_selection.lock"
            ):
                self.assert_unchanged()
                try:
                    _atomic(self.hold, self.hold_bytes, expected=adoption)
                except BaseException:
                    # A directory fsync can fail after rename. Preserve the
                    # actually observed owner in failure evidence; never roll
                    # back over a hold another operator may have published.
                    transfer = "transfer_outcome_unobservable"
                    try:
                        _, observed, _ = _owned_metadata(self.hold)
                        transfer = (
                            "transferred_but_publication_failed"
                            if observed == self.hold_bytes
                            else (
                                "not_transferred"
                                if observed == adoption["raw"]
                                else "hold_ownership_changed"
                            )
                        )
                    except (OSError, ValueError, TypeError, KeyError):
                        pass
                    self.state[adoption_key]["transfer_status"] = transfer
                    raise
            self.state[adoption_key][
                "transfer_status"
            ] = "transferred_exact_owned_hold"
        self.checkpoint("startup_held")

    def assert_hold(self):
        if self.hold.is_symlink() or self.hold.read_bytes() != self.hold_bytes:
            raise ValueError("deployment_hold_ownership_changed")

    def drain(self):
        self.assert_hold()
        if getattr(self, "closed_predecessor", None):
            self.assert_unchanged()
            interrupted_transition = (
                self.directory / "status.json"
                if self.closed_predecessor["closed_observation"].get("basis")
                == "interrupted_consumed_process" else None
            )
            if (
                (H.closed_consumption_observation(
                    self.day, owned_interrupted_transition=interrupted_transition
                ) if interrupted_transition is not None else H.closed_consumption_observation(self.day))
                != self.closed_predecessor["closed_observation"]
                or _main_pids()
                or not _session_absent()
                or self.flag.exists()
            ):
                raise ValueError("deployment_closed_predecessor_changed")
            self.checkpoint(
                "drained",
                drained_at=datetime.now(H.KST).isoformat(),
                drain_basis=(
                    "interrupted_consumed_process_preserved"
                    if self.closed_predecessor["closed_observation"].get("basis")
                    == "interrupted_consumed_process"
                    else "native_postclose_stopped_consumption_verified"
                ),
                collector_shutdown=(verify_collector_shutdown(
                    self.collector_shutdown_pin,
                    owned_interrupted_transition=interrupted_transition,
                ) if interrupted_transition is not None else verify_collector_shutdown(self.collector_shutdown_pin)),
            )
            return
        self.assert_unchanged()
        self.collector_shutdown_pin = pin_collector_shutdown(
            self.workspace, self.identity
        )
        self.checkpoint(self.phase, collector_shutdown_pin=self.collector_shutdown_pin)
        self.checkpoint("draining")
        _drain_actor(self.workspace, self.identity, self.launcher, self.launcher_stat,
                     request="source=ordered_intraday_deploy old_pid=" + str(self.identity["pid"]) + "\n",
                     guard=lambda: (self.assert_hold(), self.assert_unchanged()))
        closure = verify_collector_shutdown(self.collector_shutdown_pin)
        self.checkpoint(
            "drained",
            drained_at=datetime.now(H.KST).isoformat(),
            collector_shutdown=closure,
        )

    def publish(self):
        self.assert_hold()
        self.assert_unchanged()
        if self.phase != "drained" or _main_pids():
            raise ValueError("deployment_publish_requires_drained_main")
        predecessor_observer = _predecessor_observer(self.workspace, self.day)
        value = dict(self.old)
        value.pop("actual_pid_receipt", None)
        value.update(
            release_root=str(self.candidate),
            git_commit=self.commit,
            candidate_p5_path=self.candidate_p5["path"],
            candidate_p5_sha256=self.candidate_p5["sha256"],
            source_commit=self.previous_commit,
            previous_release_root=str(self.previous),
            previous_git_commit=self.previous_commit,
            previous_selection_backup=str(self.directory / "selection-before.json"),
            preserved_main_pid_receipt=self.old["actual_pid_receipt"],
            selected_at_kst=datetime.now(H.KST).isoformat(),
            approved_by="user",
            approval_scope="ordered_intraday_deploy_and_restart",
            actual_pid_consumed=False,
            actual_pid_consumption_status="drained_awaiting_verified_start",
            deployment_transition=str(self.directory / "status.json"),
        )
        value.pop("source_validation", None)
        if hasattr(self, "native_path"):
            value.update(
                native_predecessor_path=str(self.native_path),
                native_predecessor_sha256=self.native_sha,
            )
        else:
            value.pop("native_predecessor_path", None)
            value.pop("native_predecessor_sha256", None)
        self.published = _json_bytes(value)
        with (self.workspace / "data/runtime/runtime_release_selection.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assert_unchanged()
            inherit_prepared_delay_code(
                self.workspace,
                self.day,
                self.candidate,
                getattr(self, "prepared_delay_check", {}),
            )
            self.assert_unchanged()
            if getattr(self, "auxiliary_repair", None) is not None:
                from src.engine.scalping import reversal_auxiliary_intraday as auxiliary

                reused = getattr(self, "auxiliary_repair_reused", None)
                if reused:
                    overlay = auxiliary.read(Path(reused["overlay_path"]))
                    if (overlay != self.auxiliary_overlay
                        or H._sha(reused["overlay_path"]) != reused["overlay_sha256"]
                        or auxiliary.read(auxiliary.root(self.workspace / "data") / "current.json") != overlay):
                        raise ValueError("deployment_recovery_auxiliary_generation_changed")
                else:
                    overlay = self.run_auxiliary_native("publish", self.auxiliary_repair)
                if (overlay.get("bindings") != self.auxiliary_repair["new_bindings"]
                    or overlay.get("contract_repair_manifest_sha256") != self.auxiliary_repair["artifact_content_sha256"]):
                    raise ValueError("deployment_auxiliary_repair_publication_invalid")
                self.auxiliary_overlay = overlay
                self.checkpoint("drained", **(
                    {"auxiliary_repair_reused": reused} if reused else
                    {"auxiliary_repair_published": overlay["artifact_content_sha256"]}))
                self.assert_unchanged()
            _atomic(self.selection, self.published)
            if getattr(self, "preserve_editable_checklist", False):
                self.document_after = self.checklist.read_bytes()
            else:
                _atomic(self.checklist, self.document_after)
        self.checkpoint(
            "selected",
            selected_at=value["selected_at_kst"],
            checklist_sha256=_digest(self.document_after),
            predecessor_observer=predecessor_observer,
        )

    def prepare(self):
        self.assert_hold()
        self.run_json(
            self.candidate,
            "src.engine.automation.intraday_release_handoff",
            "--prepare",
            "--target-date",
            self.day,
            "--old-pid",
            str(self.identity["pid"]),
            "--previous-root",
            str(self.previous),
            "--previous-stopped",
            "--reseal-postclose-source",
            "--freeze-operating-checklist",
            "--confirm",
            H.CONFIRM,
        )
        self.run_json(
            self.candidate,
            "src.engine.automation.runtime_policy_bootstrap",
            "--verify",
            "--target-date",
            self.day,
        )
        self.run_json(
            self.candidate,
            "src.engine.automation.auxiliary_reader_readiness",
            "--target-date",
            self.day,
        )
        with sentinel_preparation_lock(self):
            from src.engine.monitoring.sentinel_source_window import prepare

            source_window = prepare(self.workspace / "data")
            from src.engine import buy_funnel_sentinel as buy
            from src.engine.monitoring.sentinel_summary_contract import (
                check_pending_migration,
            )

            check_pending_migration(self.workspace / "data", self.day)
            _, summary = buy.load_pipeline_event_summaries(self.day)
        from src.engine.automation import prepared_policy_code_handoff as code

        handoffs = code.issue_selected(
            self.workspace / "data", self.day, release_root=self.candidate
        )
        self.observe_report_consumers("selected_prepared")
        self.checkpoint(
            "prepared",
            sentinel_source_window=source_window,
            sentinel_summary=summary,
            native_prepared_code_handoffs=handoffs,
        )

    def start(self):
        self.assert_hold()
        if (
            self.phase != "prepared"
            or self.selection.read_bytes() != self.published
            or _main_pids()
        ):
            raise ValueError("deployment_start_generation_changed")
        if any(H._sha(path) != sha for path, sha in
               getattr(self, "stopped_collector_source", {}).items()):
            raise ValueError("deployment_stopped_collector_changed_before_start")
        # The native router rejects every startup hold, including ours. The
        # release-set lock still serializes launch; execute() restores this
        # exact owned hold on any planning/launch failure before attestation.
        self.hold.unlink()
        plan = R.make_plan(
            self.workspace, self.candidate, self.commit, "start", self.day
        )
        child = shlex.split(plan["command"][-1])
        if child[0] != "/usr/bin/env":
            raise ValueError("deployment_launcher_environment_contract_changed")
        child.insert(1, "KORSTOCKSCAN_VALIDATION_SESSION_ID=" + self.validation_session)
        plan["command"][-1] = shlex.join(child)
        _launch(plan)
        self.checkpoint("starting")

    def attest(self):
        attestation_started = time.monotonic()
        def consumed():
            value = H._read(self.selection)
            if value.get("git_commit") != self.commit:
                raise ValueError("deployment_selection_changed_during_start")
            return value.get("actual_pid_consumed") is True

        _wait(
            consumed,
            R.STARTUP_CONSUMPTION_TIMEOUT_SEC,
            "deployment_pid_attestation_timeout",
        )
        value = H._read(self.selection)
        identity = H._identity(value["actual_pid_receipt"]["pid"])
        if identity["cwd"] != str(self.candidate / "src") or _main_pids() != [
            identity["pid"]
        ]:
            raise ValueError("deployment_successor_identity_invalid")
        self.run_json(
            self.candidate,
            "src.engine.automation.runtime_policy_bootstrap",
            "--verify",
            "--target-date",
            self.day,
            "--pid",
            str(identity["pid"]),
        )
        self.run_json(
            self.candidate,
            "src.engine.automation.intraday_release_handoff",
            "--verify",
            "--target-date",
            self.day,
            "--pid",
            str(identity["pid"]),
        )
        if (
            H._identity(identity["pid"]) != identity
            or _main_pids() != [identity["pid"]]
            or H._read(self.selection) != value
        ):
            raise ValueError("deployment_successor_changed_during_attestation")
        if getattr(self, "auxiliary_repair", None) is not None:
            from src.engine.scalping import reversal_auxiliary_intraday as auxiliary

            receipt_path = auxiliary.root(self.workspace / "data") / "consumed" / self.day / (str(identity["pid"]) + ".json")
            if not receipt_path.exists() and not receipt_path.is_symlink():
                remaining = R.STARTUP_CONSUMPTION_TIMEOUT_SEC - (time.monotonic() - attestation_started)
                if remaining <= 0:
                    raise ValueError("deployment_auxiliary_repair_pid_consumption_timeout")
                _wait(lambda: receipt_path.exists() or receipt_path.is_symlink(), remaining,
                      "deployment_auxiliary_repair_pid_consumption_timeout")
            receipt = auxiliary.read(receipt_path)
            if (receipt.get("actual_pid_consumed") is not True
                or receipt.get("day") != self.day
                or receipt.get("pid_identity") != identity
                or receipt.get("release_commit") != self.commit
                or receipt.get("base_bundle_sha256") != self.auxiliary_repair["base_bundle_sha256"]
                or receipt.get("overlay_sha256") != self.auxiliary_overlay["artifact_content_sha256"]
                or receipt.get("code_hashes") != auxiliary.code_hashes()
                or receipt.get("bindings") != self.auxiliary_repair["new_bindings"]):
                raise ValueError("deployment_auxiliary_repair_pid_consumption_invalid")
            self.state["auxiliary_repair_pid_consumption"] = dict(path=str(receipt_path), sha256=H._sha(receipt_path))
        if any(
            H._sha(path) != sha
            for path, sha in self.frozen.items()
            if path != str(self.checklist)
        ):
            raise ValueError("deployment_original_policy_generation_changed")
        self.observe_report_consumers("actual_pid")
        self.checkpoint("complete", successor_identity=identity, status="pass")
        return self.state

    def fail(self, exc):
        # Never switch back while a new Main may exist, erase another operator's
        # hold, or force-stop a child. Preserve the exact phase for recovery.
        if not hasattr(self, "state"):
            return
        if (getattr(self, "auxiliary_repair", None) is not None
            and not getattr(self, "auxiliary_repair_reused", None)
            and self.phase == "drained" and not _main_pids()):
            try:
                self.assert_hold()
                if self.selection.read_bytes() == self.before:
                    reverted = self.run_auxiliary_native("rollback", self.auxiliary_repair)
                    if reverted is not None:
                        if reverted.get("bindings") != self.auxiliary_repair["old_bindings"]:
                            raise ValueError("deployment_auxiliary_rollback_binding_invalid")
                        self.state["auxiliary_repair_unwind"] = dict(
                            status="rolled_back", overlay_sha256=reverted["artifact_content_sha256"])
            except Exception as unwind:
                self.state["auxiliary_repair_unwind"] = dict(
                    status="failed", error=type(unwind).__name__ + ":" + str(unwind))
        if self.phase in {"prepared", "starting"} and self.hold_bytes is not None:
            try:
                with self.hold.open("xb") as out:
                    out.write(self.hold_bytes)
                    out.flush()
                    os.fsync(out.fileno())
            except FileExistsError:
                pass  # Never replace an operator's intervening hold.
        self.checkpoint(
            "failed",
            failed_phase=self.phase,
            status="fail",
            error=str(exc),
            recovery="inspect_transition_and_preserve_startup_hold",
        )


def _stopped_intraday_predecessor(
    day, previous, previous_commit, identity, failed_path, *, _depth=0
):
    """Recheck the genuine same-day consumption, without inventing a native PID."""
    if _depth > 3:
        raise ValueError("deployment_stopped_predecessor_ancestry_invalid")
    proof_path = Path(failed_path).with_name("preflight-intraday_release_handoff.log")
    if not proof_path.exists():
        failed, failed_raw, _ = _owned_metadata(failed_path)
        parent = failed.get("failed_hold_adoption") or {}
        origin = Path(parent.get("failed_transition_path") or "")
        expected = (
            Path(failed_path).parent.parent
            / (parent.get("failed_selected_commit") or "")
            / "status.json"
        )
        if (
            _depth >= 3
            or origin != expected
            or origin == Path(failed_path)
            or not parent.get("intraday_predecessor_proof_sha256")
            or parent.get("transfer_status") != "transferred_exact_owned_hold"
        ):
            raise ValueError("deployment_stopped_predecessor_ancestry_invalid")
        original, raw, _ = _owned_metadata(origin)
        if (
            _digest(raw) != parent.get("failed_transition_sha256")
            or original.get("predecessor_identity") != identity
            or original.get("previous_commit") != previous_commit
            or original.get("candidate_commit") != parent.get("failed_selected_commit")
        ):
            raise ValueError("deployment_stopped_predecessor_ancestry_changed")
        proof = _stopped_intraday_predecessor(
            day, previous, previous_commit, identity, origin, _depth=1
        )
        if proof["sha256"] != parent["intraday_predecessor_proof_sha256"]:
            raise ValueError("deployment_stopped_predecessor_proof_changed")
        proof["frozen_files"].update(
            {str(origin): _digest(raw), str(failed_path): _digest(failed_raw)}
        )
        return proof
    proof, proof_raw, _ = _owned_metadata(proof_path)
    handoff_path, consumed_path = H._paths(day, previous_commit)
    handoff, handoff_raw, _ = _owned_metadata(handoff_path)
    consumed, consumed_raw, _ = _owned_metadata(consumed_path)
    manifest = H._read(H.bootstrap.manifest_path(day))
    if (
        proof.get("schema") != "intraday_pid_consumption_verification_v1"
        or proof.get("status") != "pass"
        or proof.get("findings") != []
        or proof.get("basis") != "intraday_policy_preserving_handoff"
        or proof.get("actual_pid_consumed") is not True
        or proof.get("target_date") != day
        or proof.get("pid_identity") != identity
        or proof.get("selected_release_commit") != previous_commit
        or proof.get("release_root") != str(previous)
        or proof.get("manifest_sha256") != manifest.get("manifest_sha256")
        or handoff.get("schema") != "intraday_policy_preserving_release_handoff_v1"
        or handoff.get("status") != "prepared_verified"
        or handoff.get("authority") != H.CONFIRM
        or handoff.get("target_date") != day
        or handoff.get("selected_release_commit") != previous_commit
        or handoff.get("release_root") != str(previous)
        or handoff.get("preopen_sha256") != H._sha(H._preopen_path(day))
        or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
        or consumed.get("status") != "pass"
        or consumed.get("target_date") != day
        or consumed.get("selected_release_commit") != previous_commit
        or consumed.get("release_root") != str(previous)
        or consumed.get("actual_pid_consumed") is not True
        or consumed.get("pid_identity") != identity
        or consumed.get("handoff_sha256") != _digest(handoff_raw)
        or consumed.get("manifest_sha256") != proof.get("manifest_sha256")
        or not handoff.get("frozen_files")
        or any(H._sha(p) != sha for p, sha in handoff["frozen_files"].items())
    ):
        raise ValueError("deployment_stopped_intraday_predecessor_invalid")
    return dict(
        path=str(proof_path),
        sha256=_digest(proof_raw),
        frozen_files={
            **handoff["frozen_files"],
            str(proof_path): _digest(proof_raw),
            str(handoff_path): _digest(handoff_raw),
            str(consumed_path): _digest(consumed_raw),
        },
    )


class StoppedDeploymentRecovery(Deployment):
    """Explicit embedding-only recovery of a failed selected native transition.

    The caller holds both ordinary deployment locks. Reuse the live-captured
    native or intraday proof, never infer consumption from an absent process. The failed
    attempt remains immutable; only its exact owned hold may transfer.
    """

    def assert_stopped(self):
        if (
            _main_pids()
            or not _session_absent()
            or self.flag.exists()
            or self.flag.is_symlink()
            or Path("/proc", str(self.identity["pid"])).exists()
            or (self.launcher is not None and Path("/proc", str(self.launcher)).exists())
        ):
            raise ValueError("deployment_recovery_requires_stopped_main_and_supervisor")

    def inspect_stopped_origin(self):
        """Read-only original custody inspection shared with isolated P5."""
        self.before = self.selection.read_bytes()
        selected = json.loads(self.before)
        failed_root, failed_commit = R.selected_release(self.workspace)
        failed_path = (
            self.workspace
            / "data/runtime/release_transitions"
            / self.day
            / failed_commit
            / "status.json"
        )
        hold, hold_raw, hold_sig = _owned_metadata(self.hold)
        preselection = selected.get("actual_pid_consumed") is True
        if preselection:
            held_commit = hold.get("candidate_commit")
            if (not isinstance(held_commit, str) or len(held_commit) != 40
                or any(c not in "0123456789abcdef" for c in held_commit)):
                raise ValueError("deployment_drained_hold_commit_invalid")
            failed_path = self.workspace / "data/runtime/release_transitions" / self.day / held_commit / "status.json"
            if hold.get("transition") != str(failed_path):
                raise ValueError("deployment_drained_hold_path_invalid")
        failed, failed_raw, failed_sig = _owned_metadata(failed_path)
        if preselection:
            failed_root, failed_commit = R.validate_release(self.workspace, dict(
                schema="runtime_release_selection_v1", workspace=str(self.workspace),
                release_root=failed.get("candidate_root"), git_commit=held_commit))
        prior_path = failed_path.with_name("selection-before.json")
        prior, prior_raw, prior_sig = _owned_metadata(prior_path)
        identity = failed.get("predecessor_identity") or {}
        preparation_sources = stopped_preparation_failure_sources(failed, failed_path)
        interrupted = preselection and (
            failed.get("failed_phase"), failed.get("error")
        ) == ("startup_held", "deployment_stopped_recovery_source_invalid")
        if (
            (not preselection and (
                selected.get("deployment_transition") != str(failed_path)
                or selected.get("actual_pid_consumed") is not False))
            or (preselection and (
                self.before != prior_raw
                or (not interrupted and (failed.get("failed_phase") != "draining"
                    or failed.get("error") != "deployment_collector_closed_epoch_invalid"))))
            or selected.get("approval_scope") != "ordered_intraday_deploy_and_restart"
            or selected.get("approved_by") != "user"
            or failed.get("schema") != "ordered_intraday_deployment_v1"
            or failed.get("authority") != CONFIRM
            or failed.get("target_date") != self.day
            or failed.get("candidate_commit") != failed_commit
            or failed.get("candidate_root") != str(failed_root)
            or failed.get("phase") != "failed"
            or failed.get("status") != "fail"
            or (
                (failed.get("failed_phase"), failed.get("error"))
                not in {
                    (
                        "selected",
                        "deployment_validation_failed:src.engine.automation.intraday_release_handoff",
                    ),
                    ("starting", "deployment_pid_attestation_timeout"),
                }
                and not preparation_sources
                and not preselection
            )
            or failed.get("policy_effect") != "unchanged"
            or hold
            != dict(
                schema="ordered_deployment_startup_hold_v1",
                authority=CONFIRM,
                transition=str(failed_path),
                target_date=self.day,
                candidate_commit=failed_commit,
                old_pid_identity=identity,
            )
            or failed.get("original_selection_sha256") != _digest(prior_raw)
            or prior.get("actual_pid_consumed") is not True
            or prior.get("schema") != "runtime_release_selection_v1"
            or prior.get("git_commit") != failed.get("previous_commit")
            or prior.get("release_root") != failed.get("previous_root")
            or (not preselection and (
                selected.get("previous_selection_backup") != str(prior_path)
                or selected.get("previous_git_commit") != prior.get("git_commit")
                or selected.get("previous_release_root") != prior.get("release_root")))
            or type(identity.get("pid")) is not int
            or identity["pid"] <= 0
            or not isinstance(identity.get("start_ticks"), str)
            or not identity["start_ticks"].isdigit()
            or (not interrupted and (
                type((failed.get("predecessor_launcher") or {}).get("pid")) is not int
                or failed["predecessor_launcher"]["pid"] <= 0
                or not isinstance(failed["predecessor_launcher"].get("start_ticks"), str)
                or not failed["predecessor_launcher"]["start_ticks"].isdigit()))
            or (prior.get("actual_pid_receipt") or {}).get("pid") != identity["pid"]
            or identity.get("cwd") != str(Path(prior["release_root"]) / "src")
        ):
            raise ValueError("deployment_stopped_recovery_source_invalid")
        if (
            failed_path.resolve(strict=True) != failed_path
            or prior_path.resolve(strict=True) != prior_path
        ):
            raise ValueError("deployment_stopped_recovery_path_invalid")
        self.identity = identity
        self.launcher = failed["predecessor_launcher"]["pid"]
        self.assert_stopped()
        self.previous, self.previous_commit = R.validate_release(self.workspace, prior)
        collector_source = {}
        interrupted_native = None
        if interrupted:
            evidence = verify_interrupted_transition_hold(self.workspace, self.day, identity, failed_path)
            if H.closed_consumption_observation(
                self.day, owned_interrupted_transition=failed_path
            ) != evidence["observation"]:
                raise ValueError("deployment_interrupted_consumption_changed")
            pin = failed["interrupted_collector"]
            verify_collector_shutdown(pin, owned_interrupted_transition=failed_path)
            proof_path = failed_path.with_name("closed-predecessor.json")
            mutable = {
                pin["path"],
                str(self.workspace / "tmp/error_detector_heartbeat.json"),
            }
            stable_sources = {path: sha for path, sha in evidence["sources"].items()
                              if path not in mutable}
            interrupted_native = dict(path=str(proof_path), sha256=H._sha(proof_path),
                                      frozen_files=stable_sources)
            preparation_sources.update(stable_sources)
            collector_source.update({path: evidence["sources"][path] for path in mutable})
        elif preselection:
            pin = failed.get("collector_shutdown_pin") or {}
            if (pin.get("pid") != identity["pid"]
                or pin.get("start_ticks") != identity["start_ticks"]
                or pin.get("path") != str(self.workspace / "data/runtime/scalp_micro_reversion_forward_collector/latest.json")):
                raise ValueError("deployment_drained_collector_identity_invalid")
            closure = verify_collector_shutdown(pin)
            native = _stopped_intraday_predecessor(
                self.day, self.previous, self.previous_commit, identity, failed_path)
            preparation_sources.update(native["frozen_files"])
            collector_source[pin["path"]] = H._sha(pin["path"])
            preparation_sources.update({r["path"]: r["sha256"] for r in closure["receipts"]})
        return dict(
            preselection=preselection,
            collector_source=collector_source,
            selected=selected,
            failed_root=failed_root,
            failed_commit=failed_commit,
            failed_path=failed_path,
            hold=hold,
            hold_raw=hold_raw,
            hold_sig=hold_sig,
            failed=failed,
            failed_raw=failed_raw,
            failed_sig=failed_sig,
            prior_path=prior_path,
            prior=prior,
            prior_raw=prior_raw,
            prior_sig=prior_sig,
            identity=identity,
            preparation_sources=preparation_sources,
            interrupted_native=interrupted_native,
            interrupted_observation=(evidence["observation"] if interrupted else None),
        )

    def preflight(self):
        origin = self.inspect_stopped_origin()
        selected = origin["selected"]
        failed_root = origin["failed_root"]
        failed_commit = origin["failed_commit"]
        failed_path = origin["failed_path"]
        hold = origin["hold"]
        hold_raw = origin["hold_raw"]
        hold_sig = origin["hold_sig"]
        failed = origin["failed"]
        failed_raw = origin["failed_raw"]
        failed_sig = origin["failed_sig"]
        prior_path = origin["prior_path"]
        prior = origin["prior"]
        prior_raw = origin["prior_raw"]
        prior_sig = origin["prior_sig"]
        identity = origin["identity"]
        preparation_sources = origin["preparation_sources"]
        self.stopped_collector_source = origin["collector_source"]
        commit = R.git(self.candidate, "rev-parse", "HEAD")
        self.candidate, self.commit = R.validate_release(
            self.workspace,
            dict(
                schema="runtime_release_selection_v1",
                workspace=str(self.workspace),
                release_root=str(self.candidate),
                git_commit=commit,
            ),
        )
        self.pin_candidate_p5()
        if (
            self.candidate in {failed_root, self.previous}
            or Path(__file__).resolve().parents[3] != self.candidate
        ):
            raise ValueError("deployment_recovery_requires_new_reviewed_candidate")
        from src.engine.scalping.reversal_cumulative_registration import pending_scoring_code_check

        self.pending_scoring = pending_scoring_code_check(self.workspace / "data", self.day)
        native_basis = bool(selected.get("native_predecessor_path")) and not origin["preselection"]
        if origin["interrupted_native"]:
            native = origin["interrupted_native"]
        elif native_basis:
            native = H._native_predecessor(
                self.day,
                failed_commit,
                self.previous,
                self.previous_commit,
                identity,
                selected.get("native_predecessor_path"),
                selected.get("native_predecessor_sha256"),
            )
            native_value = H._read(native["path"])
        else:
            native = _stopped_intraday_predecessor(
                self.day, self.previous, self.previous_commit, identity, failed_path
            )
        checks = dict(
            delay=verify_candidate_delay_code(self.day, self.candidate, self.commit),
            stop=H.verify_candidate_stop_code(self.day, self.candidate, self.commit),
            holding=H.verify_candidate_holding_vote_code(
                self.day, self.candidate, self.commit
            ),
            active=verify_candidate_active_policy(
                self.workspace, self.candidate, self.commit, self.day
            ),
            reports=verify_candidate_report_currentness(
                self.workspace, self.candidate, self.day
            ),
        )
        auxiliary_sources = self.inherit_auxiliary_repair(origin, checks["active"])
        self.prepared_delay_check = checks["delay"]
        self.directory = (
            self.workspace / "data/runtime/release_transitions" / self.day / self.commit
        )
        self.directory.mkdir(parents=True, exist_ok=False)
        self.old = prior
        self.frozen = {**native["frozen_files"], **preparation_sources}
        self.frozen.update(auxiliary_sources)
        self.frozen.update(
            (checks["delay"].get("prepared_code_origin") or {}).get("sources", {})
        )
        self.frozen.pop(str(self.selection), None)
        active = checks["active"]
        self.frozen.update(
            {
                active["receipt_path"]: active["receipt_sha256"],
                active["pointer_path"]: active["pointer_sha256"],
            }
        )
        self.checklist = (
            self.workspace
            / "docs/checklists"
            / (self.day + "-stage2-todo-checklist.md")
        )
        self.document_before = self.document_after = self.checklist.read_bytes()
        self.state = dict(
            schema="ordered_intraday_deployment_v1",
            authority=CONFIRM,
            target_date=self.day,
            previous_root=str(self.previous),
            previous_commit=self.previous_commit,
            candidate_root=str(self.candidate),
            candidate_commit=self.commit,
            predecessor_identity=identity,
            predecessor_launcher=failed["predecessor_launcher"],
            original_selection_sha256=_digest(prior_raw),
            runtime_effect="authorized_code_restart_only",
            policy_effect="unchanged",
            stopped_recovery_selection_sha256=_digest(self.before),
            failed_hold_adoption=dict(
                source_failure=failed["error"],
                failed_transition_path=str(failed_path),
                failed_transition_sha256=_digest(failed_raw),
                failed_selected_root=str(failed_root),
                failed_selected_commit=failed_commit,
                previous_hold_sha256=_digest(hold_raw),
                **{
                    (
                        "native_predecessor_sha256"
                        if native_basis
                        else "intraday_predecessor_proof_sha256"
                    ): native["sha256"]
                },
                transfer_status="verified_not_transferred",
            ),
        )
        self.state["candidate_p5"] = self.candidate_p5
        if getattr(self, "auxiliary_repair_reused", None):
            self.state["auxiliary_repair_reused"] = self.auxiliary_repair_reused
        self.state["candidate_report_currentness"] = checks["reports"]
        self.observe_report_consumers("candidate")
        self.failed_hold_adoption = dict(
            raw=hold_raw,
            signature=hold_sig,
            transition_path=str(failed_path),
            transition_raw=failed_raw,
            transition_signature=failed_sig,
            prior_path=str(prior_path),
            prior_raw=prior_raw,
            prior_signature=prior_sig,
        )
        for name, raw in [
            ("selection-before.json", prior_raw),
            ("failed-selection-before.json", self.before),
            ("failed-startup-hold-before.json", hold_raw),
            ("failed-transition-before.json", failed_raw),
            ("checklist-before.md", self.document_before),
        ]:
            _atomic(self.directory / name, raw)
        if native_basis:
            self.native_path = self.directory / "native-predecessor.json"
            _atomic(
                self.native_path,
                _json_bytes(dict(native_value, candidate_commit=self.commit)),
            )
            self.native_sha = H._sha(self.native_path)
            H._native_predecessor(
                self.day,
                self.commit,
                self.previous,
                self.previous_commit,
                identity,
                self.native_path,
                self.native_sha,
            )
            self.frozen[str(self.native_path)] = self.native_sha
        self.frozen.update(
            {
                native["path"]: native["sha256"],
                str(failed_path): _digest(failed_raw),
                str(prior_path): _digest(prior_raw),
            }
        )
        for name, check in checks.items():
            _atomic(
                self.directory / ("candidate-" + name + "-code.json"),
                _json_bytes(check),
            )
        self.assert_unchanged()
        self.assert_stopped()
        self.checkpoint("preflight")

    def drain(self):
        self.assert_hold()
        self.assert_unchanged()
        self.assert_stopped()
        self.checkpoint(
            "drained",
            drained_at=datetime.now(H.KST).isoformat(),
            drain_basis="verified_original_native_predecessor_already_stopped",
        )


def stop_after_eod(workspace, day, confirm, *, now=None):
    """Native stop-only boundary for postclose; never selects or starts code.

    Failed requests retain their exact hold and baseline. A later invocation
    may finish that same stopped actor, but never sends a second stop request.
    """
    from src.trading.market.session_contract import resolve_market_session, MARKET_SESSION_REGIME_CLOSED
    from src.utils.market_day import is_krx_trading_day
    from src.engine.infrastructure.validation_digest_session import postclose_session
    from src.engine.infrastructure.log_retention import resume_pre_postclose_logs, maintain_tmp

    workspace = Path(workspace).resolve(strict=True)
    current = now or datetime.now(H.KST)
    if (confirm != CONFIRM or current.tzinfo is None
            or current.astimezone(H.KST).date().isoformat() != day
            or current.astimezone(H.KST).hour < 20
            or not is_krx_trading_day(current.astimezone(H.KST).date())
            or resolve_market_session(current).session_regime != MARKET_SESSION_REGIME_CLOSED):
        raise ValueError("postclose_stop_market_or_authority_invalid")
    root, commit = R.selected_release(workspace)
    if root != Path(__file__).resolve().parents[3]:
        raise ValueError("postclose_stop_reader_not_selected")
    selection = workspace / "data/runtime/runtime_release_selection.json"
    eod = workspace / "data/runtime/update_kospi_status" / ("update_kospi_" + day + ".json")
    terminal, eod_raw = R._startup_receipt(eod)
    finished = datetime.fromisoformat(terminal.get("finished_at") or "")
    finished = finished.replace(tzinfo=H.KST) if finished.tzinfo is None else finished
    db = terminal.get("db_state") or {}
    if (terminal.get("target_date") != day
            or terminal.get("status") not in {"completed", "completed_with_warnings"}
            or finished.astimezone(H.KST).date().isoformat() != day or finished > current
            or db.get("latest_quote_date") != day
            or type(db.get("rows_on_latest_date")) is not int or db["rows_on_latest_date"] <= 0):
        raise ValueError("postclose_stop_eod_not_complete")
    directory = workspace / "data/runtime/postclose_stop" / day
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "owner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status_path = directory / "status.json"
        hold_path = workspace / "data/runtime/operator_startup_hold.json"
        if status_path.exists():
            state, _, _ = _owned_metadata(status_path)
        else:
            selected, selection_raw = R._startup_receipt(selection)
            receipt = selected.get("actual_pid_receipt") or {}
            actor = H._identity(receipt["pid"])
            if (selected.get("actual_pid_consumed") is not True
                    or receipt.get("start_ticks") != actor["start_ticks"]
                    or actor["cwd"] != str(root / "src")
                    or hold_path.exists() or hold_path.is_symlink()):
                raise ValueError("postclose_stop_actor_or_hold_invalid")
            with postclose_session(workspace / "data", day):
                verified = H.verify_pid_consumption(day, pid=actor["pid"])
            if (verified.get("status") != "pass"
                    or verified.get("target_date") != day
                    or verified.get("actual_pid_consumed") is not True):
                raise ValueError("postclose_stop_policy_consumption_invalid")
            pin = pin_collector_shutdown(workspace, actor)
            closure = (verify_collector_shutdown(pin)
                       if pin.get("basis") in {"native_market_close", "native_observer_canary_stop"}
                       else None)
            parent = Path("/proc", str(actor["pid"]), "stat").read_text().rsplit(")", 1)[1].split()[1]
            launcher = int(parent)
            launcher_start = Path("/proc", parent, "stat").read_text().rsplit(")", 1)[1].split()[19]
            if str(root / "src/run_bot.sh").encode() not in Path("/proc", parent, "cmdline").read_bytes().split(b"\0"):
                raise ValueError("postclose_stop_supervisor_unrecognized")
            state = dict(schema="native_postclose_stop_v1", source_date=day,
                         phase="verified", status="running", release_root=str(root), git_commit=commit,
                         selection_sha256=_digest(selection_raw), eod_sha256=_digest(eod_raw),
                         actor=actor, launcher=launcher, launcher_start=launcher_start,
                         collector_pin=pin, collector_closure=closure,
                         policy_consumption=verified, started_at=current.isoformat(),
                         runtime_effect=False, actual_pid_consumed=False)
            _atomic(directory / "selection-before.json", selection_raw)
            _atomic(directory / "eod-before.json", eod_raw)
            _atomic(status_path, _json_bytes(state))

        def guard():
            if (state.get("schema") != "native_postclose_stop_v1" or state.get("source_date") != day
                    or state.get("phase") not in {"verified", "draining", "stopped", "cleanup_complete"}
                    or state.get("release_root") != str(root) or state.get("git_commit") != commit
                    or _digest(selection.read_bytes()) != state["selection_sha256"]
                    or _digest(eod.read_bytes()) != state["eod_sha256"]):
                raise ValueError("postclose_stop_sources_changed")

        guard()
        hold = _json_bytes(dict(schema="native_postclose_stop_hold_v1", source_date=day,
                               authority=CONFIRM, source_pid=state["actor"]["pid"],
                               source_start_ticks=state["actor"]["start_ticks"],
                               evidence=str(status_path)))
        try:
            if state["phase"] == "verified":
                if hold_path.exists() or hold_path.is_symlink():
                    if (hold_path.is_symlink() or hold_path.read_bytes() != hold
                            or not (directory / "hold-original.json").exists()
                            or (directory / "hold-original.json").read_bytes() != hold):
                        raise ValueError("postclose_stop_foreign_hold")
                else:
                    _atomic(directory / "hold-original.json", hold)
                    with hold_path.open("xb") as out:
                        out.write(hold); out.flush(); os.fsync(out.fileno())
                state.update(phase="draining", drain_requested_at=datetime.now(H.KST).isoformat())
                _atomic(status_path, _json_bytes(state))

                def held_guard():
                    guard()
                    if hold_path.is_symlink() or hold_path.read_bytes() != hold:
                        raise ValueError("postclose_stop_hold_changed")

                _drain_actor(workspace, state["actor"], state["launcher"], state["launcher_start"],
                             request="source=native_postclose_stop old_pid=" + str(state["actor"]["pid"]) + "\n",
                             guard=held_guard)
            if state["phase"] == "draining":
                guard()
                if (_main_pids() or not _session_absent()
                        or Path("/proc", str(state["actor"]["pid"])).exists()
                        or Path("/proc", str(state["launcher"])).exists()
                        or (workspace / "restart.flag").exists()):
                    raise ValueError("postclose_stop_original_drain_incomplete")
                state["collector_closure"] = verify_collector_shutdown(state["collector_pin"])
                # This is the isolation owner's native receipt, issued only
                # after exact PID/supervisor/writer closure, never a stop signal.
                isolation = dict(schema_version=1, active=True, target_date=day, session="bot",
                                 action="stop", reason="threshold_cycle_postclose_resource_isolation",
                                 started_at=datetime.now(H.KST).isoformat(), native_stop=str(status_path))
                _atomic(workspace / "tmp/postclose_bot_isolation.json", _json_bytes(isolation))
                if hold_path.is_symlink() or hold_path.read_bytes() != hold:
                    raise ValueError("postclose_stop_hold_changed")
                state.update(phase="stopped", stopped_at=datetime.now(H.KST).isoformat())
                _atomic(status_path, _json_bytes(state))
            if state["phase"] in {"stopped", "cleanup_complete"}:
                guard()
                if _main_pids() or not _session_absent():
                    raise ValueError("postclose_stop_consumer_reappeared")
                if hold_path.exists() or hold_path.is_symlink():
                    if hold_path.is_symlink() or hold_path.read_bytes() != hold:
                        raise ValueError("postclose_stop_hold_changed")
                    hold_path.unlink()  # Remove only this owner's verified hold.
                if state["phase"] != "cleanup_complete":
                    cleanup = resume_pre_postclose_logs(workspace, apply=True)
                    state["cleanup"] = cleanup
                    if cleanup.get("status") != "complete":
                        raise ValueError("postclose_stop_cleanup_incomplete")
                    cleanup["tmp"] = maintain_tmp(workspace, apply=True)
                    if cleanup["tmp"].get("status") != "complete":
                        raise ValueError("postclose_stop_tmp_cleanup_incomplete")
                    state.update(phase="cleanup_complete", status="pass", finished_at=datetime.now(H.KST).isoformat())
                    _atomic(status_path, _json_bytes(state))
                if state.get("cleanup", {}).get("status") != "complete":
                    raise ValueError("postclose_stop_cleanup_proof_invalid")
            return state
        except BaseException as exc:
            state.update(status="failed", error=str(exc))
            _atomic(directory / (uuid.uuid4().hex + ".failure.json"), _json_bytes(state))
            _atomic(status_path, _json_bytes(state))
            raise


def validate_selected_p5(driver):
    """Run the native startup reader after selected preparation, before launch."""
    from src.engine.automation import main_startup_validation

    driver.assert_hold()
    if (driver.phase != "prepared" or driver.selection.read_bytes() != driver.published
        or _main_pids()):
        raise ValueError("selected_p5_generation_changed")
    result, path = main_startup_validation.run_validation(
        workspace=driver.workspace,
        target_date=driver.day,
        execution_root=driver.candidate,
        candidate=False,
    )
    path = Path(path)
    if result.get("status") != "passed":
        raise ValueError("selected_p5_failed:" + str(path))
    run_id = result.get("run_id")
    expected_parent = driver.workspace / "data/report/main_startup_validation" / driver.day
    if (not isinstance(run_id, str) or re.fullmatch(r"[0-9a-f]{32}", run_id) is None
        or path != expected_parent / run_id / "final.json"
        or any(parent.is_symlink() for parent in (path, path.parent, expected_parent))):
        raise ValueError("selected_p5_receipt_path_invalid")
    persisted, raw, _ = _owned_metadata(path)
    if (persisted != result
        or result.get("schema") != "main_policy_load_exit_validation_v1"
        or result.get("target_date") != driver.day
        or result.get("execution_release_root") != str(driver.candidate)
        or result.get("execution_release_commit") != driver.commit
        or result.get("selected_release_root") != str(driver.candidate)
        or result.get("selected_release_commit") != driver.commit
        or result.get("findings")
        or result.get("child_terminated") is not True
        or result.get("child_exit_code") != 0
        or result.get("load_check_passed") is not True
        or result.get("protected_sources_unchanged") is not True
        or result.get("failure_phase") is not None
        or result.get("actual_pid_consumed") is not False
        or result.get("runtime_effect") is not False
        or result.get("allowed_runtime_apply") is not False):
        raise ValueError("selected_p5_receipt_invalid")
    driver.assert_hold()
    if driver.selection.read_bytes() != driver.published or _main_pids():
        raise ValueError("selected_p5_generation_changed")
    driver.checkpoint("prepared", selected_p5=dict(path=str(path), sha256=_digest(raw)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=H.DATA_DIR.parent)
    parser.add_argument("--release-root", type=Path)
    parser.add_argument("--stop-after-eod", action="store_true")
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--candidate-p5-path", type=Path)
    parser.add_argument("--candidate-p5-sha256")
    parser.add_argument("--auxiliary-repair-path", type=Path)
    parser.add_argument("--auxiliary-repair-sha256")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args(argv)
    if not args.stop_after_eod and not all((args.release_root, args.candidate_p5_path, args.candidate_p5_sha256)):
        parser.error("deployment requires release root and exact candidate P5")
    if bool(args.auxiliary_repair_path) != bool(args.auxiliary_repair_sha256):
        parser.error("auxiliary repair requires both its manifest path and SHA-256")
    if args.stop_after_eod and args.auxiliary_repair_path:
        parser.error("postclose stop cannot publish an auxiliary repair")
    try:
        with R.runtime_release_set_lock(args.workspace):
            with detector_transition_lock(args.workspace):
                result = stop_after_eod(args.workspace, args.target_date, args.confirm) if args.stop_after_eod else execute(
                    Deployment(
                        args.workspace,
                        args.release_root,
                        args.target_date,
                        args.confirm,
                        candidate_p5_path=args.candidate_p5_path,
                        candidate_p5_sha256=args.candidate_p5_sha256,
                        auxiliary_repair_path=args.auxiliary_repair_path,
                        auxiliary_repair_sha256=args.auxiliary_repair_sha256,
                    ), validate_prepared=validate_selected_p5
                )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as exc:
        print(json.dumps({"status": "fail", "findings": [str(exc)]}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
