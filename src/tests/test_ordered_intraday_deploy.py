"""Deployment automation contracts; no real processes, flags or policy calls."""

import json
import fcntl
import os
import subprocess
from pathlib import Path

import pytest

from src.engine.automation import ordered_intraday_deploy as D


@pytest.mark.parametrize("damage", [None, "selector", "eod", "hold", "consumer", "cleanup", "clock"])
def test_postclose_stop_resumes_only_exact_closed_actor_before_cleanup(tmp_path, monkeypatch, damage):
    from datetime import datetime
    from src.engine.infrastructure import log_retention

    day = "2026-10-29"
    root = Path(D.__file__).resolve().parents[3]
    directory = tmp_path / "data/runtime/postclose_stop" / day
    directory.mkdir(parents=True)
    selection = tmp_path / "data/runtime/runtime_release_selection.json"
    selection.write_text(json.dumps(dict(release_root=str(root), git_commit="c" * 40)))
    eod = tmp_path / "data/runtime/update_kospi_status" / ("update_kospi_" + day + ".json")
    eod.parent.mkdir()
    eod.write_text(json.dumps(dict(target_date=day, status="completed", finished_at=day + "T20:07:00+09:00",
                                   db_state=dict(latest_quote_date=day, rows_on_latest_date=10))))
    state = dict(schema="native_postclose_stop_v1", source_date=day, phase="stopped", status="running",
                 release_root=str(root), git_commit="c" * 40, selection_sha256=D._digest(selection.read_bytes()),
                 eod_sha256=D._digest(eod.read_bytes()), actor=dict(pid=2147483601, start_ticks="123"),
                 launcher=2147483602, collector_pin={})
    (directory / "status.json").write_bytes(D._json_bytes(state))
    monkeypatch.setattr(D.R, "selected_release", lambda _: (root, "c" * 40))
    monkeypatch.setattr(D, "_main_pids", lambda: [1] if damage == "consumer" else [])
    monkeypatch.setattr(D, "_session_absent", lambda: True)
    calls = []

    def cleanup(*a, **kw):
        calls.append((a, kw))
        return dict(status="incomplete" if damage == "cleanup" else "complete", deleted_bytes=123)

    monkeypatch.setattr(log_retention, "resume_pre_postclose_logs", cleanup)
    monkeypatch.setattr(log_retention, "maintain_tmp", lambda *a, **kw: dict(status="complete", deleted_bytes=0))
    if damage == "selector": selection.write_text("changed")
    if damage == "eod":
        changed = json.loads(eod.read_bytes()); changed["status"] = "failed"; eod.write_text(json.dumps(changed))
    if damage == "hold": selection.with_name("operator_startup_hold.json").write_text("foreign")
    now = datetime.fromisoformat(day + ("T16:00:00+09:00" if damage == "clock" else "T20:10:00+09:00"))
    if damage:
        with pytest.raises(ValueError): D.stop_after_eod(tmp_path, day, D.CONFIRM, now=now)
        assert len(calls) == (1 if damage == "cleanup" else 0)
    else:
        assert D.stop_after_eod(tmp_path, day, D.CONFIRM, now=now)["phase"] == "cleanup_complete"
        assert D.stop_after_eod(tmp_path, day, D.CONFIRM, now=now)["status"] == "pass"
        assert len(calls) == 1
    assert not (tmp_path / "restart.flag").exists()


def _report_currentness_fixture(workspace, candidate, day):
    from src.engine.monitoring.policy_generation_code_handoff import consumer_inventory
    return dict(status="pass", source_date=day,
                capability_consumers=consumer_inventory(candidate, day, data_root=workspace / "data"))


def _candidate_p5_fixture(d, commit=None):
    selected = json.loads(d.selection.read_bytes())
    directory = d.workspace / "data/report/main_startup_validation" / d.day / ("d" * 32)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "final.json"
    value = dict(
        schema="main_policy_load_exit_validation_v1",
        run_id=directory.name,
        status="passed",
        findings=[],
        target_date=d.day,
        execution_release_root=str(d.candidate),
        execution_release_commit=commit or d.commit,
        selected_release_root=selected["release_root"],
        selected_release_commit=selected["git_commit"],
        child_terminated=True,
        child_exit_code=0,
        failure_phase=None,
        load_check_passed=True,
        protected_sources_unchanged=True,
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_pid_consumed=False,
    )
    path.write_bytes(D._json_bytes(value))
    d.candidate_p5_path = path
    d.candidate_p5_sha256 = D.H._sha(path)
    if hasattr(d, "commit"):
        d.pin_candidate_p5()
    return path


@pytest.fixture(autouse=True)
def _summary_preflight_contract(monkeypatch):
    from src.engine.monitoring import sentinel_summary_contract as summary

    monkeypatch.setattr(
        summary, "check_pending_migration", lambda *_: dict(status="current_contract")
    )


@pytest.fixture
def stopped_recovery(tmp_path, monkeypatch):
    day = "2026-10-12"
    candidate = Path(D.__file__).resolve().parents[3]
    old_root, failed_root = tmp_path / "old", tmp_path / "failed"
    old_commit, failed_commit, new_commit = "a" * 40, "b" * 40, "c" * 40
    directory = tmp_path / "data/runtime/release_transitions" / day / failed_commit
    directory.mkdir(parents=True)
    identity = dict(pid=2147483601, start_ticks="123", cwd=str(old_root / "src"))
    prior = dict(
        schema="runtime_release_selection_v1",
        workspace=str(tmp_path),
        release_root=str(old_root),
        git_commit=old_commit,
        actual_pid_consumed=True,
        actual_pid_receipt={"pid": identity["pid"]},
    )
    prior_path = directory / "selection-before.json"
    prior_path.write_bytes(D._json_bytes(prior))
    status_path = directory / "status.json"
    status = dict(
        schema="ordered_intraday_deployment_v1",
        authority=D.CONFIRM,
        target_date=day,
        candidate_commit=failed_commit,
        candidate_root=str(failed_root),
        previous_root=str(old_root),
        previous_commit=old_commit,
        predecessor_identity=identity,
        predecessor_launcher=dict(pid=2147483602, start_ticks="124"),
        phase="failed",
        status="fail",
        failed_phase="selected",
        error="deployment_validation_failed:src.engine.automation.intraday_release_handoff",
        policy_effect="unchanged",
        original_selection_sha256=D._digest(prior_path.read_bytes()),
    )
    status_path.write_bytes(D._json_bytes(status))
    native_path = directory / "native-predecessor.json"
    policy = tmp_path / "policy.json"
    policy.write_text("original policy")
    native_value = dict(
        candidate_commit=failed_commit, frozen_files={str(policy): D.H._sha(policy)}
    )
    native_path.write_bytes(D._json_bytes(native_value))
    selected = dict(
        schema="runtime_release_selection_v1",
        workspace=str(tmp_path),
        release_root=str(failed_root),
        git_commit=failed_commit,
        actual_pid_consumed=False,
        deployment_transition=str(status_path),
        approval_scope="ordered_intraday_deploy_and_restart",
        approved_by="user",
        previous_selection_backup=str(prior_path),
        previous_git_commit=old_commit,
        previous_release_root=str(old_root),
        native_predecessor_path=str(native_path),
        native_predecessor_sha256=D.H._sha(native_path),
    )
    selection = tmp_path / "data/runtime/runtime_release_selection.json"
    selection.write_bytes(D._json_bytes(selected))
    hold = selection.with_name("operator_startup_hold.json")
    hold.write_bytes(
        D._json_bytes(
            dict(
                schema="ordered_deployment_startup_hold_v1",
                authority=D.CONFIRM,
                transition=str(status_path),
                target_date=day,
                candidate_commit=failed_commit,
                old_pid_identity=identity,
            )
        )
    )
    selection.with_suffix(".lock").touch()
    checklist = tmp_path / "docs/checklists" / (day + "-stage2-todo-checklist.md")
    checklist.parent.mkdir(parents=True)
    checklist.write_text("editable original")
    monkeypatch.setattr(D.H, "_today", lambda *a: None)
    monkeypatch.setattr(
        D.R, "selected_release", lambda *a: (failed_root, failed_commit)
    )
    monkeypatch.setattr(D.R, "git", lambda *a: new_commit)
    monkeypatch.setattr(
        D.R, "validate_release", lambda w, v: (Path(v["release_root"]), v["git_commit"])
    )
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    monkeypatch.setattr(D, "_session_absent", lambda: True)

    def native(day, commit, previous, previous_commit, old_identity, path, sha):
        assert D.H._sha(path) == sha
        value = D.H._read(path)
        assert value["candidate_commit"] == commit and old_identity == identity
        assert all(D.H._sha(p) == s for p, s in value["frozen_files"].items())
        return dict(path=str(path), sha256=sha, frozen_files=value["frozen_files"])

    monkeypatch.setattr(D.H, "_native_predecessor", native)
    for name in ("delay", "stop", "holding_vote"):
        monkeypatch.setattr(
            D.H, "verify_candidate_" + name + "_code", lambda *a: dict(status="pass")
        )
    monkeypatch.setattr(
        D,
        "verify_candidate_active_policy",
        lambda *a: dict(
            status="pass",
            receipt_path=str(policy),
            receipt_sha256=D.H._sha(policy),
            pointer_path=str(policy),
            pointer_sha256=D.H._sha(policy),
        ),
    )
    monkeypatch.setattr(
        D,
        "verify_candidate_report_currentness",
        _report_currentness_fixture,
        raising=False,
    )
    d = D.StoppedDeploymentRecovery(tmp_path, candidate, day, D.CONFIRM)
    _candidate_p5_fixture(d, new_commit)
    return d, status_path, policy


def test_stopped_recovery_requires_active_policy_before_hold_transfer(
    stopped_recovery, monkeypatch
):
    d, status, policy = stopped_recovery
    before = d.selection.read_bytes(), d.hold.read_bytes(), status.read_bytes()

    def reject(*args):
        raise ValueError("active source changed")

    monkeypatch.setattr(D, "verify_candidate_active_policy", reject)
    with pytest.raises(ValueError, match="active source changed"):
        d.preflight()
    assert before == (
        d.selection.read_bytes(),
        d.hold.read_bytes(),
        status.read_bytes(),
    )


def test_stopped_recovery_freezes_prepared_origin_and_uses_native_inheritance(
    stopped_recovery, monkeypatch, tmp_path
):
    d, status, policy = stopped_recovery
    source = tmp_path / "prepared-origin.json"
    source.write_text("immutable origin")
    check = dict(
        status="pass",
        prepared_code_origin=dict(sources={str(source): D.H._sha(source)}),
    )
    monkeypatch.setattr(D, "verify_candidate_delay_code", lambda *a: check)
    d.preflight()
    assert d.prepared_delay_check == check and d.frozen[str(source)] == D.H._sha(source)
    assert str(d.selection) not in d.frozen
    source.write_text("different generation")
    with pytest.raises(ValueError, match="generation_changed"):
        d.acquire_hold()


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "phase",
        "error",
        "date",
        "hold",
        "selection",
        "original",
        "native",
        "main",
        "supervisor",
        "flag",
        "delay",
        "stop",
        "holding_vote",
        "changed_hold",
        "changed_status",
        "changed_policy",
    ],
)
def test_stopped_recovery_preserves_failed_attempt_and_requires_native_sources(
    stopped_recovery, monkeypatch, damage
):
    d, status_path, policy = stopped_recovery
    if damage in {"phase", "error", "date"}:
        value = D.H._read(status_path)
        value[
            {"phase": "failed_phase", "error": "error", "date": "target_date"}[damage]
        ] = "foreign"
        status_path.write_bytes(D._json_bytes(value))
    if damage == "hold":
        d.hold.write_text('{"operator":"another"}')
    if damage in {"selection", "original"}:
        path = (
            d.selection
            if damage == "selection"
            else status_path.with_name("selection-before.json")
        )
        value = D.H._read(path)
        value["actual_pid_consumed"] = False if damage == "original" else True
        path.write_bytes(D._json_bytes(value))
    if damage == "native":
        monkeypatch.setattr(
            D.H,
            "_native_predecessor",
            lambda *a: (_ for _ in ()).throw(ValueError("native invalid")),
        )
    if damage == "main":
        monkeypatch.setattr(D, "_main_pids", lambda: [1])
    if damage == "supervisor":
        monkeypatch.setattr(D, "_session_absent", lambda: False)
    if damage == "flag":
        d.flag.write_text("other request")
    if damage in {"delay", "stop", "holding_vote"}:
        monkeypatch.setattr(
            D.H,
            "verify_candidate_" + damage + "_code",
            lambda *a: (_ for _ in ()).throw(ValueError("code invalid")),
        )
    before = d.selection.read_bytes(), d.hold.read_bytes(), status_path.read_bytes()
    if damage and not damage.startswith("changed_"):
        with pytest.raises((ValueError, AssertionError)):
            d.preflight()
        assert before == (
            d.selection.read_bytes(),
            d.hold.read_bytes(),
            status_path.read_bytes(),
        )
        return
    d.preflight()
    assert before == (
        d.selection.read_bytes(),
        d.hold.read_bytes(),
        status_path.read_bytes(),
    )
    if damage == "changed_hold":
        d.hold.write_text('{"new_owner":true}')
    if damage == "changed_status":
        status_path.write_text("{}")
    if damage == "changed_policy":
        policy.write_text("changed policy")
    if damage:
        current = (
            d.selection.read_bytes(),
            d.hold.read_bytes(),
            status_path.read_bytes(),
        )
        with pytest.raises(ValueError):
            d.acquire_hold()
        assert current == (
            d.selection.read_bytes(),
            d.hold.read_bytes(),
            status_path.read_bytes(),
        )
        return
    d.acquire_hold()
    d.drain()
    d.publish()
    assert status_path.read_bytes() == before[2]
    assert d.checklist.read_text() == "editable original"
    assert D.H._read(d.selection)["previous_release_root"] == str(d.previous)
    assert D.H._read(d.native_path)["candidate_commit"] == d.commit
    assert (d.directory / "failed-selection-before.json").read_bytes() == before[0]
    assert (
        d.state["failed_hold_adoption"]["transfer_status"]
        == "transferred_exact_owned_hold"
    )


def _assert_detector_lock_held(workspace):
    with (workspace / "tmp/run_error_detection.lock").open("a") as other:
        with pytest.raises(BlockingIOError):
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize("chain", [False, True, "two", "three"])
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "proof_pid",
        "proof_basis",
        "consumed",
        "handoff",
        "policy",
        "preopen",
        "manifest",
        "parent_hash",
        "parent_path",
        "parent_proof",
        "depth",
    ],
)
def test_stopped_intraday_recovery_requires_original_consumption_and_every_frozen_byte(
    tmp_path, monkeypatch, damage, chain
):
    if not chain and damage in ("parent_hash", "parent_path", "parent_proof", "depth"):
        return
    day, commit = "2026-10-16", "a" * 40
    old = tmp_path / "old"
    identity = dict(pid=2147483601, start_ticks="123", cwd=str(old / "src"))
    policy = tmp_path / "policy.json"
    policy.write_text("original")
    preopen = tmp_path / "preopen.json"
    preopen.write_text("original preopen")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"manifest_sha256": "b" * 64}))
    origin = (
        tmp_path / ("b" * 40) / "status.json" if chain else tmp_path / "status.json"
    )
    origin.parent.mkdir(parents=True, exist_ok=True)
    proof_path = origin.with_name("preflight-intraday_release_handoff.log")
    proof = dict(
        schema="intraday_pid_consumption_verification_v1",
        status="pass",
        findings=[],
        basis="intraday_policy_preserving_handoff",
        actual_pid_consumed=True,
        target_date=day,
        selected_release_commit=commit,
        release_root=str(old),
        pid_identity=identity,
        manifest_sha256="b" * 64,
    )
    handoff_path = tmp_path / "handoff.json"
    consumed_path = tmp_path / "consumed.json"
    handoff = dict(
        schema="intraday_policy_preserving_release_handoff_v1",
        status="prepared_verified",
        authority=D.H.CONFIRM,
        target_date=day,
        selected_release_commit=commit,
        release_root=str(old),
        preopen_sha256=D.H._sha(preopen),
        frozen_files={str(policy): D.H._sha(policy), str(manifest): D.H._sha(manifest)},
    )
    handoff_path.write_bytes(D._json_bytes(handoff))
    consumed = dict(
        schema="intraday_policy_preserving_consumption_v1",
        status="pass",
        target_date=day,
        selected_release_commit=commit,
        release_root=str(old),
        actual_pid_consumed=True,
        pid_identity=identity,
        handoff_sha256=D.H._sha(handoff_path),
        manifest_sha256="b" * 64,
    )
    if damage == "proof_pid":
        proof["pid_identity"] = {**identity, "start_ticks": "456"}
    elif damage == "proof_basis":
        proof["basis"] = "native_preopen"
    elif damage == "consumed":
        consumed["actual_pid_consumed"] = False
    elif damage == "handoff":
        handoff_path.write_text("{}")
    elif damage == "policy":
        policy.write_text("changed")
    elif damage == "preopen":
        preopen.write_text("changed")
    elif damage == "manifest":
        manifest.write_text(json.dumps({"manifest_sha256": "c" * 64}))
    proof_path.write_bytes(D._json_bytes(proof))
    consumed_path.write_bytes(D._json_bytes(consumed))
    failed_path = origin
    depth = 0
    if chain:
        origin.write_bytes(
            D._json_bytes(
                dict(
                    predecessor_identity=identity,
                    previous_commit=commit,
                    candidate_commit="b" * 40,
                )
            )
        )
        parent = dict(
            failed_transition_path=str(origin),
            failed_selected_commit="b" * 40,
            failed_transition_sha256=D.H._sha(origin),
            intraday_predecessor_proof_sha256=D.H._sha(proof_path),
            transfer_status="transferred_exact_owned_hold",
        )
        if damage == "parent_hash":
            parent["failed_transition_sha256"] = "0" * 64
        if damage == "parent_path":
            parent["failed_transition_path"] = str(tmp_path / "foreign.json")
        if damage == "parent_proof":
            parent["intraday_predecessor_proof_sha256"] = "0" * 64
        if damage == "depth":
            depth = 3
        failed_path = tmp_path / ("c" * 40) / "status.json"
        failed_path.parent.mkdir()
        failed_path.write_bytes(
            D._json_bytes(
                dict(
                    failed_hold_adoption=parent,
                    predecessor_identity=identity,
                    previous_commit=commit,
                    candidate_commit="c" * 40,
                )
            )
        )
        if chain in ("two", "three"):
            parent = dict(
                failed_transition_path=str(failed_path),
                failed_selected_commit="c" * 40,
                failed_transition_sha256=D.H._sha(failed_path),
                intraday_predecessor_proof_sha256=D.H._sha(proof_path),
                transfer_status="transferred_exact_owned_hold",
            )
            failed_path = tmp_path / ("d" * 40) / "status.json"
            failed_path.parent.mkdir()
            failed_path.write_bytes(
                D._json_bytes(
                    dict(
                        failed_hold_adoption=parent,
                        predecessor_identity=identity,
                        previous_commit=commit,
                        candidate_commit="d" * 40,
                    )
                )
            )
            if chain == "three":
                parent = dict(
                    failed_transition_path=str(failed_path),
                    failed_selected_commit="d" * 40,
                    failed_transition_sha256=D.H._sha(failed_path),
                    intraday_predecessor_proof_sha256=D.H._sha(proof_path),
                    transfer_status="transferred_exact_owned_hold",
                )
                failed_path = tmp_path / ("e" * 40) / "status.json"
                failed_path.parent.mkdir()
                failed_path.write_bytes(
                    D._json_bytes(dict(failed_hold_adoption=parent))
                )
    monkeypatch.setattr(D.H, "_paths", lambda *a: (handoff_path, consumed_path))
    monkeypatch.setattr(D.H, "_preopen_path", lambda *a: preopen)
    monkeypatch.setattr(D.H.bootstrap, "manifest_path", lambda *a: manifest)
    before = {
        p: p.read_bytes()
        for p in (proof_path, handoff_path, consumed_path, policy, preopen, manifest)
    }
    if damage:
        with pytest.raises(
            ValueError, match="stopped_(intraday_predecessor|predecessor)_"
        ):
            D._stopped_intraday_predecessor(
                day, old, commit, identity, failed_path, _depth=depth
            )
    else:
        result = D._stopped_intraday_predecessor(
            day, old, commit, identity, failed_path, _depth=depth
        )
        assert result["frozen_files"][str(consumed_path)] == D.H._sha(consumed_path)
        assert result["frozen_files"][str(proof_path)] == D.H._sha(proof_path)
    assert all(p.read_bytes() == raw for p, raw in before.items())


def test_stopped_recovery_from_intraday_does_not_fabricate_native_receipt(
    stopped_recovery, monkeypatch
):
    d, status_path, policy = stopped_recovery
    selected = D.H._read(d.selection)
    selected.pop("native_predecessor_path")
    selected.pop("native_predecessor_sha256")
    d.selection.write_bytes(D._json_bytes(selected))
    proof = status_path.with_name("preflight-intraday_release_handoff.log")
    proof.write_text("verified original proof")
    monkeypatch.setattr(
        D,
        "_stopped_intraday_predecessor",
        lambda *a: dict(
            path=str(proof),
            sha256=D.H._sha(proof),
            frozen_files={str(policy): D.H._sha(policy)},
        ),
    )
    monkeypatch.setattr(
        D.H,
        "_native_predecessor",
        lambda *a: pytest.fail("intraday consumption relabeled native"),
    )
    d.preflight()
    d.acquire_hold()
    d.drain()
    d.publish()
    assert not hasattr(d, "native_path")
    assert "native_predecessor_path" not in D.H._read(d.selection)
    assert d.state["failed_hold_adoption"][
        "intraday_predecessor_proof_sha256"
    ] == D.H._sha(proof)


@pytest.mark.parametrize("failure", [None, "preflight", "publish", "attest"])
def test_cli_holds_detector_lock_through_attestation_and_failure(
    tmp_path, monkeypatch, failure
):
    (tmp_path / "data").mkdir(exist_ok=True)
    calls = []

    class Driver:
        workspace = tmp_path
        day = "2026-10-12"

        def __getattr__(self, name):
            def step(*args):
                _assert_detector_lock_held(tmp_path)
                calls.append(name)
                if name == failure:
                    raise ValueError(name)
                return {"status": "pass"}

            return step

    monkeypatch.setattr(D, "Deployment", lambda *args, **kw: Driver())
    def selected_p5(_driver):
        _assert_detector_lock_held(tmp_path)
        calls.append("selected_p5")
    monkeypatch.setattr(D, "validate_selected_p5", selected_p5)
    rc = D.main(
        [
            "--workspace",
            str(tmp_path),
            "--release-root",
            str(tmp_path),
            "--target-date",
            "2026-10-12",
            "--candidate-p5-path",
            str(tmp_path / "final.json"),
            "--candidate-p5-sha256",
            "a" * 64,
            "--confirm",
            D.CONFIRM,
        ]
    )
    assert rc == (1 if failure else 0)
    assert calls[-1] == ("fail" if failure else "attest")
    if not failure or failure == "attest":
        assert calls.index("prepare") < calls.index("selected_p5") < calls.index("start")
    with D.detector_transition_lock(tmp_path, timeout=0):
        _assert_detector_lock_held(tmp_path)


def test_busy_detector_times_out_before_deployment_preflight(tmp_path, monkeypatch):
    (tmp_path / "tmp").mkdir()
    lock_path = tmp_path / "tmp/run_error_detection.lock"
    with lock_path.open("a") as running:
        fcntl.flock(running, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inode = lock_path.stat().st_ino
        monkeypatch.setattr(
            D, "Deployment", lambda *a: pytest.fail("no deployment mutation")
        )
        ticks = iter([0, 61])
        monkeypatch.setattr(D.time, "monotonic", lambda: next(ticks))
        assert (
            D.main(
                [
                    "--workspace",
                    str(tmp_path),
                    "--release-root",
                    str(tmp_path),
                    "--target-date",
                    "2026-10-12",
                    "--candidate-p5-path",
                    str(tmp_path / "final.json"),
                    "--candidate-p5-sha256",
                    "a" * 64,
                    "--confirm",
                    D.CONFIRM,
                ]
            )
            == 1
        )
        assert lock_path.stat().st_ino == inode
        _assert_detector_lock_held(tmp_path)
        assert not (tmp_path / "data/runtime/operator_startup_hold.json").exists()
        assert not (tmp_path / "restart.flag").exists()


def test_wait_for_existing_detector_completion_then_acquire(tmp_path, monkeypatch):
    (tmp_path / "tmp").mkdir()
    with (tmp_path / "tmp/run_error_detection.lock").open("a") as running:
        fcntl.flock(running, fcntl.LOCK_EX | fcntl.LOCK_NB)
        waits = []

        def finish_detector(seconds):
            waits.append(seconds)
            fcntl.flock(running, fcntl.LOCK_UN)

        monkeypatch.setattr(D.time, "sleep", finish_detector)
        with D.detector_transition_lock(tmp_path):
            assert waits == [0.25]
            _assert_detector_lock_held(tmp_path)


@pytest.mark.parametrize("explicit_source,expected_rc", [(False, 0), (True, 75)])
def test_actual_detector_wrapper_yields_during_deployment(
    tmp_path, explicit_source, expected_rc
):
    project = Path(__file__).resolve().parents[2]
    args = ["bash", str(project / "deploy/run_error_detection.sh"), "full"]
    if explicit_source:
        args.append("2026-10-08")
    with D.detector_transition_lock(tmp_path):
        result = subprocess.run(
            args,
            env={**os.environ, "PROJECT_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        _assert_detector_lock_held(tmp_path)
    assert result.returncode == expected_rc, result.stderr
    assert "ordered deployment holds lock" in result.stdout
    assert "[START]" not in result.stdout
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize(
    "guard_rc,explicit_source,expected_rc",
    [(75, False, 0), (75, True, 75), (1, False, 1)],
)
def test_wrapper_stale_reader_and_invalid_selection_never_publish(
    tmp_path, guard_rc, explicit_source, expected_rc
):
    project = Path(__file__).resolve().parents[2]
    python = tmp_path / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/bin/sh\nexit {guard_rc}\n")
    python.chmod(0o755)
    args = ["bash", str(project / "deploy/run_error_detection.sh"), "full"]
    if explicit_source:
        args.append("2026-10-08")
    result = subprocess.run(
        args,
        env={**os.environ, "PROJECT_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == expected_rc, result.stderr
    assert "[START]" not in result.stdout
    assert not (tmp_path / "data").exists()
    assert not list((tmp_path / "tmp").glob("error_detection_*.json"))


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "preflight",
        "acquire_hold",
        "drain",
        "publish",
        "prepare",
        "start",
        "attest",
    ],
)
def test_transition_does_not_advance_past_failed_phase(tmp_path, failure):
    (tmp_path / "data").mkdir()
    calls = []
    steps = [
        "preflight",
        "acquire_hold",
        "drain",
        "publish",
        "prepare",
        "start",
        "attest",
    ]

    class Driver:
        workspace = tmp_path
        day = "2026-10-12"

        def __getattr__(self, name):
            def step(*args):
                with pytest.raises(ValueError, match="scheduled_execution_active"):
                    with D.R.scheduled_execution_lease(tmp_path, exclusive=True):
                        pass
                calls.append(name)
                if name == failure:
                    raise ValueError(name)
                return {"status": "pass"}

            return step

    if failure:
        with pytest.raises(ValueError, match=failure):
            D.execute(Driver())
        assert calls == steps[: steps.index(failure) + 1] + ["fail"]
    else:
        assert D.execute(Driver()) == {"status": "pass"}
        assert calls == steps


def test_active_scheduled_owner_blocks_before_deployment_preflight(tmp_path):
    calls = []

    class Driver:
        workspace = tmp_path

        def preflight(self):
            calls.append("preflight")

        def fail(self, exc):
            calls.append(str(exc))

    with D.R.scheduled_execution_lease(tmp_path):
        with pytest.raises(ValueError, match="scheduled_execution_active"):
            D.execute(Driver())
    assert calls == []
    assert not (tmp_path / "data/runtime/operator_startup_hold.json").exists()


@pytest.mark.parametrize("failure", [None, "drain", "attest"])
def test_source_epoch_keeps_native_readers_across_the_actual_transition(
    tmp_path, monkeypatch, failure
):
    import sqlite3
    from src.engine.automation import main_trailing_source_store as store

    data = tmp_path / "data"
    data.mkdir()
    target = store._index_path(data, "holding_path_votes", "2026-10-20")
    target.parent.mkdir(parents=True)
    native = store._open_database(target, readonly=False, writer=True)
    native.close()
    opened = []
    original = store._open_database

    def observe(*args, **kwargs):
        db = original(*args, **kwargs)
        assert kwargs["readonly"] is True and not db.in_transaction
        opened.append(db)
        return db

    monkeypatch.setattr(store, "_open_database", observe)

    class Driver:
        workspace = tmp_path
        day = "2026-10-20"

        def preflight(self):
            assert not opened

        def __getattr__(self, name):
            def step(*args):
                if name == "fail":
                    return
                assert len(opened) == 1 and not opened[0].in_transaction
                assert opened[0].execute("PRAGMA user_version").fetchone()[0] == 1
                if name == failure:
                    raise ValueError(name)
                return dict(status="pass")

            return step

    if failure:
        with pytest.raises(ValueError, match=failure):
            D.execute(Driver())
    else:
        assert D.execute(Driver()) == dict(status="pass")
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        opened[0].execute("SELECT 1")
    assert sorted(p.name for p in target.parent.glob("*.sqlite")) == [
        "holding_path_votes.sqlite"
    ]


def test_source_epoch_failure_cannot_acquire_hold_or_drain(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    target = data / "report/main_trailing_source_index/holding_path_votes.sqlite"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"not sqlite")
    target.chmod(0o600)
    called = []

    class Driver:
        workspace = tmp_path
        day = "2026-10-20"

        def preflight(self):
            called.append("preflight")

        def fail(self, exc):
            called.append("fail")

        def __getattr__(self, name):
            return lambda *a: called.append(name)

    with pytest.raises(__import__("sqlite3").DatabaseError):
        D.execute(Driver())
    assert called == ["preflight", "fail"]


@pytest.fixture
def driver(tmp_path, monkeypatch):
    monkeypatch.setattr(
        D,
        "verify_candidate_report_currentness",
        _report_currentness_fixture,
        raising=False,
    )
    monkeypatch.setattr(
        D, "pin_collector_shutdown", lambda *a: dict(pid=123, start_ticks="123")
    )
    monkeypatch.setattr(
        D, "verify_collector_shutdown", lambda *a: dict(status="verified")
    )
    d = object.__new__(D.Deployment)
    d.workspace = tmp_path
    runtime = tmp_path / "data/runtime"
    runtime.mkdir(parents=True)
    d.selection = runtime / "runtime_release_selection.json"
    d.hold = runtime / "operator_startup_hold.json"
    d.flag = tmp_path / "restart.flag"
    d.previous = tmp_path / "old"
    d.candidate = tmp_path / "new"
    d.previous_commit = "a" * 40
    d.commit = "b" * 40
    d.day = "2026-10-12"
    d.identity = dict(pid=123, start_ticks="123", cwd=str(d.previous / "src"))
    d.old = dict(
        actual_pid_receipt={"pid": 123},
        actual_pid_consumed=True,
        release_root=str(d.previous),
        git_commit=d.previous_commit,
    )
    d.before = D._json_bytes(d.old)
    d.selection.write_bytes(d.before)
    d.directory = runtime / "transition"
    d.directory.mkdir()
    d.state = dict(candidate_report_currentness=_report_currentness_fixture(d.workspace, d.candidate, d.day))
    d.phase = "preflight"
    d.hold_bytes = None
    d.validation_session = "1" * 32
    d.collector_shutdown_pin = dict(pid=123, start_ticks="123")
    d.checklist = tmp_path / "checklist.md"
    d.checklist.write_text("original")
    d.document_before = b"original"
    d.document_after = b"reviewed candidate"
    d.frozen = {str(d.checklist): D._digest(d.document_before)}
    _candidate_p5_fixture(d)
    return d


@pytest.mark.parametrize(
    "damage", [None, "proof", "main", "supervisor", "flag", "hold", "source"]
)
def test_closed_predecessor_drain_rechecks_native_closure_without_stop_mutation(
    driver, monkeypatch, damage
):
    d = driver
    proof = dict(
        schema="intraday_closed_consumption_observation_v1", pid_identity=d.identity
    )
    d.closed_predecessor = dict(closed_observation=proof)
    d.hold_bytes = b"owned"
    d.hold.write_bytes(d.hold_bytes)
    monkeypatch.setattr(
        D.H,
        "closed_consumption_observation",
        lambda *a: {} if damage == "proof" else proof,
    )
    monkeypatch.setattr(D, "_main_pids", lambda: [456] if damage == "main" else [])
    monkeypatch.setattr(D, "_session_absent", lambda: damage != "supervisor")
    if damage == "flag":
        d.flag.write_text("another owner")
    if damage == "hold":
        d.hold.write_text("another owner")
    if damage == "source":
        d.checklist.write_text("changed")
    before = {p: p.read_bytes() for p in (d.selection, d.hold, d.checklist)}
    if damage:
        with pytest.raises(ValueError):
            d.drain()
        assert not (d.directory / "status.json").exists()
    else:
        d.drain()
        assert d.state["drain_basis"] == "native_postclose_stopped_consumption_verified"
        assert d.phase == "drained" and not d.flag.exists()
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "missing",
        "malformed",
        "symlink",
        "future",
        "failed",
        "date",
        "oversize",
        "schema",
        "run_id",
        "duplicate",
        "nonfinite",
        "overflow",
        "as_of_date",
        "fifo",
    ],
)
def test_predecessor_observer_captures_only_exact_bounded_completed_source(
    tmp_path, damage
):
    day = "2026-10-12"
    path = (
        tmp_path
        / "data/report/buy_funnel_sentinel"
        / ("submission_bottleneck_monitor_" + day + ".json")
    )
    path.parent.mkdir(parents=True)
    value = dict(
        schema="submission_bottleneck_monitor_v1",
        date=day,
        as_of="2026-10-12T10:00:00+09:00",
        run_id="a" * 32,
        execution_status="completed",
        semantic_status="partial",
    )
    if damage == "future":
        value["as_of"] = "2099-10-12T10:00:00+09:00"
    if damage == "failed":
        value["execution_status"] = "failed"
    if damage == "date":
        value["date"] = "2026-10-11"
    if damage == "as_of_date":
        value["as_of"] = "2026-10-11T10:00:00+09:00"
    if damage == "schema":
        value["schema"] = "unknown"
    if damage == "run_id":
        value["run_id"] = 1
    if damage != "missing":
        path.write_bytes(D._json_bytes(value))
    if damage == "malformed":
        path.write_bytes(b"{")
    if damage == "duplicate":
        path.write_bytes(
            D._json_bytes(value).replace(b'"run_id":', b'"run_id":"extra", "run_id":')
        )
    if damage == "nonfinite":
        path.write_bytes(
            D._json_bytes(value).replace(b'"run_id":', b'"extra":NaN, "run_id":')
        )
    if damage == "overflow":
        path.write_bytes(
            D._json_bytes(value).replace(b'"run_id":', b'"extra":1e999, "run_id":')
        )
    if damage == "oversize":
        with path.open("wb") as out:
            out.truncate(8 * 1024 * 1024 + 1)
    if damage == "fifo":
        path.unlink()
        D.os.mkfifo(path)
    if damage == "symlink":
        other = path.with_suffix(".old")
        path.rename(other)
        path.symlink_to(other)
    result = D._predecessor_observer(tmp_path, day)
    if damage is not None:
        assert result["status"] == "unavailable"
    else:
        assert result["status"] == "captured"
        assert result["sha256"] == D._digest(path.read_bytes())
        assert result["mtime_ns"] == path.stat().st_mtime_ns
        assert result["path"] == str(path)
        assert result["as_of"] == value["as_of"]
        assert result["semantic_status"] == "partial"


@pytest.mark.parametrize("damage", ["running", "phase", "selection", "source", "hold"])
def test_publication_refuses_unfinished_or_changed_predecessor(
    driver, monkeypatch, damage
):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [123] if damage == "running" else [])
    if damage == "phase":
        d.phase = "draining"
    if damage == "selection":
        d.selection.write_text("changed")
    if damage == "source":
        d.checklist.write_text("changed")
    if damage == "hold":
        d.hold.write_text("operator hold")
    before = (d.selection.read_bytes(), d.checklist.read_bytes())
    with pytest.raises(ValueError):
        d.publish()
    assert before == (d.selection.read_bytes(), d.checklist.read_bytes())


@pytest.mark.parametrize(
    "damage", [None, "missing_consumption", "pid_changed", "selector_changed"]
)
def test_completion_requires_exact_successor_consumption(driver, monkeypatch, damage):
    d = driver
    d.phase = "starting"
    identity = dict(pid=456, start_ticks="456", cwd=str(d.candidate / "src"))
    selected = dict(
        git_commit=d.commit, actual_pid_consumed=True, actual_pid_receipt={"pid": 456}
    )
    d.selection.write_text(json.dumps(selected))
    monkeypatch.setattr(D.H, "_identity", lambda pid: dict(identity))
    monkeypatch.setattr(D, "_main_pids", lambda: [456])
    calls = []

    def verify(root, module, *args):
        calls.append((module, args))
        if module.endswith("intraday_release_handoff"):
            assert args == ("--verify", "--target-date", d.day, "--pid", "456")
            if damage == "missing_consumption":
                raise ValueError("intraday_consumption_current_pid_not_bound")
            if damage == "pid_changed":
                identity["start_ticks"] = "457"
            if damage == "selector_changed":
                d.selection.write_text(json.dumps(dict(selected, git_commit="c" * 40)))
        return {"status": "pass"}

    d.run_json = verify
    if damage:
        with pytest.raises(ValueError):
            d.attest()
        assert d.phase != "complete"
    else:
        assert d.attest()["status"] == "pass"
        assert d.phase == "complete"
        assert d.state["successor_identity"] == identity
    assert len(calls) == 2


def test_drained_publication_preserves_policy_files_and_records_pending_consumption(
    driver, monkeypatch
):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    policy = d.workspace / "policy.json"
    policy.write_text("immutable policy")
    d.publish()
    selected = json.loads(d.selection.read_text())
    assert (
        selected["actual_pid_consumed"] is False
        and "actual_pid_receipt" not in selected
    )
    assert selected["preserved_main_pid_receipt"] == d.old["actual_pid_receipt"]
    assert (
        selected["git_commit"] == d.commit
        and selected["previous_git_commit"] == d.previous_commit
    )
    assert d.checklist.read_bytes() == d.document_after
    assert (
        d.hold.read_bytes() == d.hold_bytes and policy.read_text() == "immutable policy"
    )
    assert d.state["phase"] == "selected"


def test_existing_operator_hold_is_never_overwritten(driver):
    d = driver
    d.hold.write_text("operator_owned")
    with pytest.raises(FileExistsError):
        d.acquire_hold()
    d.fail(ValueError("existing_hold"))
    assert d.hold.read_text() == "operator_owned"


@pytest.mark.parametrize(
    "damage", [None, "status", "identity", "manifest", "generation"]
)
@pytest.mark.parametrize("closed", [False, True])
def test_native_predecessor_seal_requires_verified_consumption(
    driver, monkeypatch, damage, closed
):
    d = driver
    data = d.workspace / "data"
    monkeypatch.setattr(D.H, "DATA_DIR", data)
    monkeypatch.setattr(D.H.bootstrap, "env_path", lambda day: data / "bootstrap.env")
    monkeypatch.setattr(
        D.H.bootstrap, "manifest_path", lambda day: data / "manifest.json"
    )
    monkeypatch.setattr(D.H, "_preopen_path", lambda day: data / "preopen.json")
    for p in [data / "bootstrap.env", data / "manifest.json", data / "preopen.json"]:
        p.write_text("{}")
    index = data / "runtime/policy_bootstrap/prepared" / d.day / "latest.json"
    receipt = index.parent / "generation/readiness.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}")
    index.write_text(
        json.dumps(dict(receipt_path=str(receipt), receipt_sha256=D.H._sha(receipt)))
    )
    check = dict(
        schema="intraday_pid_consumption_verification_v1",
        status="pass",
        basis="native_preopen",
        actual_pid_consumed=True,
        target_date=d.day,
        selected_release_commit=d.previous_commit,
        release_root=str(d.previous),
        pid_identity=d.identity,
        manifest_sha256="verified",
    )
    if closed:
        source = data / "original-live-verification.json"
        source.write_text('{"pid_verified":true}')
        check.update(actual_pid_consumed=False, historical_consumption_verified=True,
                     closed_observation=dict(basis="native_preopen_closed", source_hashes={str(source):D.H._sha(source)}))
        d.closed_predecessor = dict(check)
    if damage == "status":
        check["status"] = "fail"
    if damage == "identity":
        check["pid_identity"] = dict(d.identity, start_ticks="reused")
    if damage == "manifest":
        check["manifest_sha256"] = None
    if damage == "generation":
        receipt.write_text("changed")
    monkeypatch.setattr(D.H, "_identity", lambda pid: dict(d.identity))
    monkeypatch.setattr(
        D.H,
        "preserve_checklist",
        lambda day: dict(path="strict-bound", sha256="original"),
    )
    if damage:
        with pytest.raises(ValueError):
            d.seal_native_predecessor(check)
        assert not (d.directory / "native-predecessor.json").exists()
    else:
        d.seal_native_predecessor(check)
        assert d.native_sha == D.H._sha(d.native_path)
        assert d.frozen[str(d.native_path)] == d.native_sha
        sealed = json.loads(d.native_path.read_text())
        assert sealed["verification"] == check
        if closed:
            snapshots = sealed["closed_source_snapshots"]
            assert snapshots[str(source)]["sha256"] == D.H._sha(source)
            archived = Path(snapshots[str(source)]["path"])
            source.write_text("mutable verification advanced")
            assert D.H._sha(archived) == d.frozen[str(archived)]
    assert not d.hold.exists() and not d.flag.exists()


@pytest.mark.parametrize("damage", ["phase", "selection", "running", "hold"])
def test_start_refuses_unprepared_or_changed_generation(driver, monkeypatch, damage):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.publish()
    d.phase = "prepared"
    if damage == "phase":
        d.phase = "selected"
    if damage == "selection":
        d.selection.write_text("other")
    if damage == "running":
        monkeypatch.setattr(D, "_main_pids", lambda: [99])
    if damage == "hold":
        d.hold.write_text("other")
    monkeypatch.setattr(
        D.subprocess, "run", lambda *a, **kw: pytest.fail("must not launch")
    )
    with pytest.raises(ValueError):
        d.start()
    assert d.hold.exists()


def test_launch_failure_restores_only_own_startup_hold(driver, monkeypatch):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.publish()
    d.phase = "prepared"
    monkeypatch.setattr(
        D.R,
        "make_plan",
        lambda *a: dict(
            command=["tmux", "/usr/bin/env /bin/bash no_launch"], cwd=str(d.workspace)
        ),
    )
    monkeypatch.setattr(D, "_session_absent", lambda: True)

    def fail(*a, **kw):
        raise OSError("launch_failed")

    monkeypatch.setattr(D.subprocess, "run", fail)
    with pytest.raises(OSError):
        d.start()
    assert not d.hold.exists()
    selected = d.selection.read_bytes()
    d.fail(OSError("launch_failed"))
    assert d.hold.read_bytes() == d.hold_bytes and d.selection.read_bytes() == selected
    assert d.state["failed_phase"] == "prepared"


def test_start_uses_real_router_after_releasing_only_owned_hold(driver, monkeypatch):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.publish()
    d.phase = "prepared"
    calls = []

    def launch(plan):
        assert not d.hold.exists()
        assert plan["cwd"] == str(d.candidate / "src")
        assert (
            "KORSTOCKSCAN_VALIDATION_SESSION_ID=" + d.validation_session
            in plan["command"][-1]
        )
        calls.append(plan)

    monkeypatch.setattr(D, "_launch", launch)
    d.start()
    assert d.phase == "starting" and len(calls) == 1


def test_router_planning_failure_restores_owned_hold_through_failure_handler(
    driver, monkeypatch
):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.publish()
    d.phase = "prepared"

    def fail(*a):
        assert not d.hold.exists()
        raise ValueError("native_router_failure")

    monkeypatch.setattr(D.R, "make_plan", fail)
    monkeypatch.setattr(
        D, "_launch", lambda *a: pytest.fail("planning failure cannot launch")
    )
    with pytest.raises(ValueError, match="native_router_failure"):
        d.start()
    d.fail(ValueError("native_router_failure"))
    assert d.hold.read_bytes() == d.hold_bytes and d.state["failed_phase"] == "prepared"


def test_failed_validation_keeps_selected_generation_held_without_false_success(
    driver, monkeypatch
):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.publish()
    calls = []

    def reject(root, module, *args, **kwargs):
        calls.append((module, args))
        raise ValueError("invalid_policy")

    d.run_json = reject
    with pytest.raises(ValueError):
        d.prepare()
    d.fail(ValueError("invalid_policy"))
    assert "--previous-stopped" in calls[0][1]
    assert d.hold.exists() and d.state["status"] == "fail"
    assert json.loads(d.selection.read_text())["actual_pid_consumed"] is False


def test_atomic_document_replacement_keeps_reader_permissions(tmp_path):
    p = tmp_path / "receipt"
    p.write_bytes(b"old")
    p.chmod(0o640)
    D._atomic(p, b"new")
    assert p.read_bytes() == b"new" and p.stat().st_mode & 0o777 == 0o640
    assert list(tmp_path.iterdir()) == [p]


@pytest.mark.parametrize(
    "damage", [None, "main_identity", "launcher_identity", "stop_timeout", "new_main"]
)
def test_drain_requires_exact_predecessor_exit_and_never_changes_selector(
    driver, monkeypatch, damage
):
    d = driver
    d.acquire_hold()
    d.launcher = 124
    d.launcher_stat = "456"
    monkeypatch.setattr(D, "_session_absent", lambda: True)
    monkeypatch.setattr(
        D.H,
        "_identity",
        lambda pid: (
            {**d.identity, "start_ticks": "changed"}
            if damage == "main_identity"
            else d.identity
        ),
    )
    read = Path.read_text

    def stat(p, *a, **kw):
        if str(p) == "/proc/124/stat":
            values = (
                ["S"]
                + ["0"] * 18
                + ["changed" if damage == "launcher_identity" else "456"]
            )
            return "124 (bash) " + " ".join(values)
        return read(p, *a, **kw)

    monkeypatch.setattr(Path, "read_text", stat)
    exists = Path.exists
    alive = {"123": True, "124": True}
    monkeypatch.setattr(
        Path,
        "exists",
        lambda p: alive[p.name] if str(p) in ("/proc/123", "/proc/124") else exists(p),
    )
    waits = []

    def wait(predicate, timeout, reason):
        assert (
            d.selection.read_bytes() == d.before
            and d.checklist.read_bytes() == d.document_before
        )
        assert d.flag.exists() and d.hold.read_bytes() == d.hold_bytes
        waits.append(reason)
        if damage == "stop_timeout":
            raise ValueError(reason)
        assert not predicate()
        alive["123" if len(waits) == 1 else "124"] = False
        assert predicate()
        if len(waits) == 2:
            d.flag.unlink()

    monkeypatch.setattr(D, "_wait", wait)
    monkeypatch.setattr(D, "_main_pids", lambda: [999] if damage == "new_main" else [])
    if damage:
        with pytest.raises(ValueError):
            d.drain()
        assert d.phase != "drained"
    else:
        d.drain()
        assert d.phase == "drained" and len(waits) == 2
    assert (
        d.selection.read_bytes() == d.before
        and d.checklist.read_bytes() == d.document_before
    )


def test_wait_is_bounded(monkeypatch):
    ticks = iter([0, 0, 0.5, 1])
    monkeypatch.setattr(D.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(D.time, "sleep", lambda _: None)
    with pytest.raises(ValueError, match="not_drained"):
        D._wait(lambda: False, 1, "not_drained")


@pytest.mark.parametrize("damage", [None, "new_main", "new_session", "all_fail"])
def test_supervisor_retry_only_while_session_and_child_absent(monkeypatch, damage):
    from types import SimpleNamespace

    calls = []
    monkeypatch.setattr(
        D, "_main_pids", lambda: [10] if damage == "new_main" and calls else []
    )
    monkeypatch.setattr(
        D, "_session_absent", lambda: not (damage == "new_session" and calls)
    )

    def launch(*a, **kw):
        calls.append(a)
        return SimpleNamespace(
            returncode=1 if damage == "all_fail" or len(calls) == 1 else 0
        )

    monkeypatch.setattr(D.subprocess, "run", launch)
    monkeypatch.setattr(D.time, "sleep", lambda _: None)
    if damage:
        with pytest.raises(ValueError):
            D._launch(dict(command=["tmux"], cwd="/unused"))
        assert len(calls) == (3 if damage == "all_fail" else 1)
    else:
        D._launch(dict(command=["tmux"], cwd="/unused"))
        assert len(calls) == 2


@pytest.mark.parametrize("family", ["delay", "stop", "holding"])
def test_incompatible_candidate_is_rejected_before_hold_or_restart(
    driver, monkeypatch, family
):
    d = driver
    monkeypatch.setattr(D.H, "DATA_DIR", d.workspace / "data")
    prior, _ = D.H._paths(d.day, d.previous_commit)
    prior.parent.mkdir(parents=True)
    prior.write_text(json.dumps({"frozen_files": d.frozen}))
    monkeypatch.setattr(
        D,
        "__file__",
        str(d.candidate / "src/engine/automation/ordered_intraday_deploy.py"),
    )
    monkeypatch.setattr(
        D.R, "selected_release", lambda workspace: (d.previous, d.previous_commit)
    )
    monkeypatch.setattr(D.R, "git", lambda *a: d.commit)
    monkeypatch.setattr(D.R, "validate_release", lambda *a: (d.candidate, d.commit))
    monkeypatch.setattr(D.H, "_identity", lambda pid: d.identity)
    monkeypatch.setattr(D, "_main_pids", lambda: [123])
    read_text, read_bytes = Path.read_text, Path.read_bytes

    def stat(path, *args, **kwargs):
        if str(path) in ("/proc/123/stat", "/proc/124/stat"):
            return "123 (python) " + " ".join(["S", "124"] + ["0"] * 17 + ["456"])
        return read_text(path, *args, **kwargs)

    def command(path, *args, **kwargs):
        if str(path) == "/proc/124/cmdline":
            return b"/bin/bash\0" + str(d.previous / "src/run_bot.sh").encode() + b"\0"
        return read_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", stat)
    monkeypatch.setattr(Path, "read_bytes", command)
    calls = []

    def incumbent(root, module, *args, **kwargs):
        calls.append(module)
        return {"status": "pass", "handoff": {"frozen_files": d.frozen}}

    d.run_json = incumbent

    def incompatible(day, root, commit):
        assert len(calls) == 2 and root == d.candidate and commit == d.commit
        assert not d.hold.exists() and not d.flag.exists()
        assert d.selection.read_bytes() == d.before
        raise ValueError("entry_consumer_unreviewed_change:producer")

    monkeypatch.setattr(
        D.H,
        "verify_candidate_delay_code",
        incompatible if family == "delay" else lambda *a: dict(status="pass"),
    )
    monkeypatch.setattr(
        D.H,
        "verify_candidate_stop_code",
        incompatible if family == "stop" else lambda *a: dict(status="pass"),
    )
    monkeypatch.setattr(D.H, "verify_candidate_holding_vote_code", incompatible)
    with pytest.raises(ValueError, match="entry_consumer_unreviewed_change"):
        D.execute(d)
    assert d.state["failed_phase"] == "preflight"
    assert not d.hold.exists() and not d.flag.exists()
    assert (
        d.selection.read_bytes() == d.before
        and d.checklist.read_bytes() == d.document_before
    )


def _failed_hold_fixture(d, monkeypatch):
    older = d.workspace / "older"
    old_identity = dict(pid=111, start_ticks="111", cwd=str(older / "src"))
    prior = dict(
        schema="runtime_release_selection_v1",
        git_commit="c" * 40,
        release_root=str(older),
        actual_pid_consumed=True,
        actual_pid_receipt={"pid": 111},
    )
    failed_path = (
        d.workspace
        / "data/runtime/release_transitions"
        / d.day
        / d.previous_commit
        / "status.json"
    )
    failed_path.parent.mkdir(parents=True)
    prior_path = failed_path.with_name("selection-before.json")
    prior_path.write_bytes(D._json_bytes(prior))
    failed = dict(
        schema="ordered_intraday_deployment_v1",
        authority=D.CONFIRM,
        target_date=d.day,
        candidate_commit=d.previous_commit,
        candidate_root=str(d.previous),
        previous_commit=prior["git_commit"],
        previous_root=prior["release_root"],
        predecessor_identity=old_identity,
        original_selection_sha256=D._digest(prior_path.read_bytes()),
        policy_effect="unchanged",
        phase="failed",
        status="fail",
        failed_phase="starting",
        error="deployment_pid_attestation_timeout",
    )
    failed_path.write_bytes(D._json_bytes(failed))
    hold = dict(
        schema="ordered_deployment_startup_hold_v1",
        authority=D.CONFIRM,
        transition=str(failed_path),
        target_date=d.day,
        candidate_commit=d.previous_commit,
        old_pid_identity=old_identity,
    )
    d.hold.write_bytes(D._json_bytes(hold))
    d.old.update(
        schema="runtime_release_selection_v1",
        deployment_transition=str(failed_path),
        previous_selection_backup=str(prior_path),
        previous_git_commit=prior["git_commit"],
        previous_release_root=prior["release_root"],
    )
    d.before = D._json_bytes(d.old)
    d.selection.write_bytes(d.before)
    d.selection.with_suffix(".lock").write_text("")
    d.adopt_failed_hold = True
    d.failed_hold_adoption = None
    d._preflight_native_verified = True
    monkeypatch.setattr(D.H, "_identity", lambda pid: dict(d.identity))
    monkeypatch.setattr(D, "_main_pids", lambda: [d.identity["pid"]])
    return hold, failed, failed_path, prior_path


def test_failed_owned_hold_transfer_is_atomic_and_preserves_native_history(
    driver, monkeypatch
):
    d = driver
    hold, failed, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    original = {
        path: path.read_bytes()
        for path in (d.hold, failed_path, prior_path, d.selection, d.checklist)
    }
    d.capture_failed_hold_adoption()
    assert d.hold.read_bytes() == original[d.hold]
    assert (
        d.state["failed_hold_adoption"]["transfer_status"] == "verified_not_transferred"
    )
    replace = D.os.replace

    def held_replace(source, target):
        if Path(target) == d.hold:
            assert d.hold.exists() and d.hold.read_bytes() == original[d.hold]
        return replace(source, target)

    monkeypatch.setattr(D.os, "replace", held_replace)
    unlink = Path.unlink

    def preserve_hold(path, *args, **kwargs):
        if path == d.hold:
            pytest.fail("hold transfer must not unlink")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", preserve_hold)
    d.acquire_hold()
    assert d.hold.read_bytes() == d.hold_bytes
    assert json.loads(d.hold_bytes)["old_pid_identity"] == d.identity
    assert (
        d.state["failed_hold_adoption"]["transfer_status"]
        == "transferred_exact_owned_hold"
    )
    for path in (failed_path, prior_path, d.selection, d.checklist):
        assert path.read_bytes() == original[path]
    assert (d.directory / "failed-startup-hold-before.json").read_bytes() == original[
        d.hold
    ]
    assert (d.directory / "failed-transition-before.json").read_bytes() == original[
        failed_path
    ]
    # The live hold intentionally changed, but the original failed terminal
    # remains a separate frozen source, outside native family frozen_files.
    d.assert_unchanged()
    d.assert_hold()


@pytest.mark.parametrize(
    "damage",
    [
        "operator_hold",
        "hold_schema",
        "hold_authority",
        "hold_day",
        "hold_commit",
        "hold_transition",
        "hold_old_pid",
        "failed_status",
        "failed_phase",
        "failed_error",
        "failed_root",
        "failed_authority",
        "failed_candidate",
        "failed_source_hash",
        "failed_source_commit",
        "selector_root",
        "selector_commit",
        "selector_unconsumed",
        "selector_pid",
        "pid_changed",
        "extra_main",
        "native_preflight",
    ],
)
def test_failed_hold_adoption_rejects_foreign_or_unproven_ownership(
    driver, monkeypatch, damage
):
    d = driver
    hold, failed, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    if damage == "operator_hold":
        hold = {"schema": "operator_manual_veto", "authority": "OPERATOR"}
    elif damage == "hold_schema":
        hold["schema"] = "unknown"
    elif damage == "hold_authority":
        hold["authority"] = "unapproved"
    elif damage == "hold_day":
        hold["target_date"] = "2026-10-11"
    elif damage == "hold_commit":
        hold["candidate_commit"] = d.commit
    elif damage == "hold_transition":
        hold["transition"] = str(d.directory / "status.json")
    elif damage == "hold_old_pid":
        hold["old_pid_identity"] = d.identity
    elif damage == "failed_status":
        failed["status"] = "pass"
    elif damage == "failed_phase":
        failed["failed_phase"] = "prepared"
    elif damage == "failed_error":
        failed["error"] = "real_policy_failure"
    elif damage == "failed_root":
        failed["candidate_root"] = str(d.candidate)
    elif damage == "failed_authority":
        failed["authority"] = "unapproved"
    elif damage == "failed_candidate":
        failed["candidate_commit"] = d.commit
    elif damage == "failed_source_hash":
        failed["original_selection_sha256"] = "0" * 64
    elif damage == "failed_source_commit":
        old = json.loads(prior_path.read_text())
        old["git_commit"] = "d" * 40
        prior_path.write_bytes(D._json_bytes(old))
    elif damage == "selector_root":
        d.old["release_root"] = str(d.candidate)
    elif damage == "selector_commit":
        d.old["git_commit"] = d.commit
    elif damage == "selector_unconsumed":
        d.old["actual_pid_consumed"] = False
    elif damage == "selector_pid":
        d.old["actual_pid_receipt"] = {"pid": 999}
    elif damage == "pid_changed":
        monkeypatch.setattr(
            D.H, "_identity", lambda pid: {**d.identity, "start_ticks": "reused"}
        )
    elif damage == "extra_main":
        monkeypatch.setattr(D, "_main_pids", lambda: [d.identity["pid"], 999])
    elif damage == "native_preflight":
        d._preflight_native_verified = False
    d.hold.write_bytes(D._json_bytes(hold))
    failed_path.write_bytes(D._json_bytes(failed))
    before = {
        path: path.read_bytes()
        for path in (d.hold, d.selection, d.checklist, failed_path, prior_path)
    }
    with pytest.raises(ValueError):
        d.capture_failed_hold_adoption()
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize(
    "damage",
    [
        "hold",
        "same_bytes_replaced",
        "failed_terminal",
        "original_selection",
        "selector",
        "source",
    ],
)
def test_failed_hold_compare_exchange_aborts_later_mutation(
    driver, monkeypatch, damage
):
    d = driver
    _, _, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    d.capture_failed_hold_adoption()
    if damage == "hold":
        d.hold.write_text('{"operator":"new veto"}')
    elif damage == "same_bytes_replaced":
        replacement = d.hold.with_name("replacement")
        replacement.write_bytes(d.hold.read_bytes())
        D.os.replace(replacement, d.hold)
    elif damage == "failed_terminal":
        failed_path.write_bytes(failed_path.read_bytes() + b" ")
    elif damage == "original_selection":
        prior_path.write_bytes(prior_path.read_bytes() + b" ")
    elif damage == "selector":
        d.selection.write_bytes(d.selection.read_bytes() + b" ")
    elif damage == "source":
        d.checklist.write_bytes(b"changed")
    before = {
        path: path.read_bytes()
        for path in (d.hold, failed_path, prior_path, d.selection, d.checklist)
    }
    with pytest.raises(ValueError):
        d.acquire_hold()
    assert {path: path.read_bytes() for path in before} == before
    assert d.phase == "preflight"


def test_failed_hold_cannot_be_adopted_without_explicit_flag(driver, monkeypatch):
    d = driver
    _failed_hold_fixture(d, monkeypatch)
    d.adopt_failed_hold = False
    before = d.hold.read_bytes()
    with pytest.raises(ValueError, match="native_preflight_required"):
        d.capture_failed_hold_adoption()
    with pytest.raises(FileExistsError):
        d.acquire_hold()
    assert d.hold.read_bytes() == before


def test_unverified_failed_hold_adoption_cannot_acquire(driver, monkeypatch):
    d = driver
    _failed_hold_fixture(d, monkeypatch)
    before = d.hold.read_bytes()
    with pytest.raises(ValueError, match="adoption_unverified"):
        d.acquire_hold()
    assert d.hold.read_bytes() == before


def _mock_adoption_preflight(d, monkeypatch, reject=None):
    monkeypatch.setattr(D.H, "DATA_DIR", d.workspace / "data")
    prior_handoff, _ = D.H._paths(d.day, d.previous_commit)
    prior_handoff.parent.mkdir(parents=True, exist_ok=True)
    prior_handoff.write_text(json.dumps({"frozen_files": d.frozen}))
    monkeypatch.setattr(
        D,
        "__file__",
        str(d.candidate / "src/engine/automation/ordered_intraday_deploy.py"),
    )
    monkeypatch.setattr(
        D.R, "selected_release", lambda workspace: (d.previous, d.previous_commit)
    )
    monkeypatch.setattr(D.R, "git", lambda *args: d.commit)
    monkeypatch.setattr(D.R, "validate_release", lambda *args: (d.candidate, d.commit))
    text, raw = Path.read_text, Path.read_bytes

    def proc_stat(path, *args, **kwargs):
        if str(path) in ("/proc/123/stat", "/proc/124/stat"):
            return "123 (python) " + " ".join(["S", "124"] + ["0"] * 17 + ["456"])
        return text(path, *args, **kwargs)

    def proc_command(path, *args, **kwargs):
        if str(path) == "/proc/124/cmdline":
            return b"/bin/bash\0" + str(d.previous / "src/run_bot.sh").encode() + b"\0"
        return raw(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", proc_stat)
    monkeypatch.setattr(Path, "read_bytes", proc_command)
    checklist = d.workspace / "docs/checklists" / (d.day + "-stage2-todo-checklist.md")
    checklist.parent.mkdir(parents=True)
    checklist.write_bytes(b"original current checklist")
    monkeypatch.setattr(
        D.subprocess,
        "check_output",
        lambda *args, **kwargs: b"reviewed candidate checklist",
    )
    calls = []

    def native(root, module, *args, **kwargs):
        calls.append(module)
        assert d.hold.exists()
        if reject is not None and reject in module:
            raise ValueError("native_validation_rejected")
        return {"status": "pass", "basis": "intraday_policy_preserving_handoff"}

    d.run_json = native

    def code(family):
        def check(*args):
            calls.append(family)
            assert len([name for name in calls if name.startswith("src.engine")]) == 2
            if reject == family:
                raise ValueError("candidate_validation_rejected")
            return {"status": "pass"}

        return check

    monkeypatch.setattr(D.H, "verify_candidate_delay_code", code("delay"))
    monkeypatch.setattr(D.H, "verify_candidate_stop_code", code("stop"))
    monkeypatch.setattr(D.H, "verify_candidate_holding_vote_code", code("holding"))

    def active(*args):
        calls.append("active_policy")
        if reject == "active_policy":
            raise ValueError("candidate_validation_rejected")
        return dict(
            status="pass",
            receipt_path=str(prior_handoff),
            receipt_sha256=D.H._sha(prior_handoff),
            pointer_path=str(d.selection),
            pointer_sha256=D.H._sha(d.selection),
        )

    monkeypatch.setattr(D, "verify_candidate_active_policy", active)

    def reports(*args):
        calls.append("reports")
        if reject == "reports":
            raise ValueError("candidate_validation_rejected")
        return _report_currentness_fixture(*args)

    monkeypatch.setattr(
        D, "verify_candidate_report_currentness", reports, raising=False
    )
    d._preflight_native_verified = False
    return calls


@pytest.mark.parametrize(
    "rejected",
    [
        "intraday_release_handoff",
        "runtime_policy_bootstrap",
        "delay",
        "stop",
        "holding",
        "active_policy",
        "reports",
    ],
)
def test_adoption_native_preflight_failure_never_replaces_old_hold(
    driver, monkeypatch, rejected
):
    d = driver
    _, _, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    original = {
        path: path.read_bytes()
        for path in (d.hold, failed_path, prior_path, d.selection, d.checklist)
    }
    _mock_adoption_preflight(d, monkeypatch, rejected)
    with pytest.raises(ValueError, match="validation_rejected"):
        d.preflight()
    assert d._preflight_native_verified is False
    assert d.failed_hold_adoption is None
    assert {path: path.read_bytes() for path in original} == original


def test_adoption_preflight_native_checks_precede_capture_and_acquire(
    driver, monkeypatch
):
    d = driver
    _failed_hold_fixture(d, monkeypatch)
    hold_before = d.hold.read_bytes()
    calls = _mock_adoption_preflight(d, monkeypatch)
    d.preflight()
    assert calls == [
        "src.engine.automation.intraday_release_handoff",
        "src.engine.automation.runtime_policy_bootstrap",
        "delay",
        "stop",
        "holding",
        "active_policy",
        "reports",
    ]
    assert d._preflight_native_verified is True
    assert d.hold.read_bytes() == hold_before
    d.acquire_hold()
    d.assert_hold()
    d.assert_unchanged()
    assert d.hold.read_bytes() != hold_before and d.phase == "startup_held"


@pytest.mark.parametrize(
    "damage", [None, "native_source", "pid", "candidate", "runtime_effect", "consumed"]
)
def test_repaired_predecessor_requires_full_bound_read_before_any_mutation(
    driver, monkeypatch, damage
):
    d = driver
    _failed_hold_fixture(d, monkeypatch)
    _mock_adoption_preflight(d, monkeypatch)
    d.adopt_failed_hold = False
    d.hold.unlink()
    d.preserve_editable_checklist = True
    before = {p: p.read_bytes() for p in (d.selection, d.checklist)}
    calls = []

    def native(root, module, *args, **kwargs):
        calls.append((root, args))
        if root == d.previous:
            (d.directory / "preflight-intraday_release_handoff.log").write_text(
                "old failure"
            )
            raise ValueError("intraday_preserved_generation_changed")
        assert args == ("--verify-predecessor", "--target-date", d.day, "--pid", "123")
        if damage == "native_source":
            raise ValueError("actual_native_source_changed")
        result = dict(
            status="pass",
            schema="intraday_pid_consumption_verification_v1",
            target_date=d.day,
            manifest_sha256="a" * 64,
            verification_code_commit=d.commit,
            verification_code_root=str(d.candidate),
            selected_release_commit=d.previous_commit,
            release_root=str(d.previous),
            pid_identity=d.identity,
            actual_pid_consumed=True,
            candidate_pid_consumed=False,
            runtime_effect=False,
        )
        if damage == "pid":
            result["pid_identity"] = dict(d.identity, start_ticks="changed")
        if damage == "candidate":
            result["verification_code_commit"] = "c" * 40
        if damage == "runtime_effect":
            result["runtime_effect"] = True
        if damage == "consumed":
            result["actual_pid_consumed"] = False
        return result

    d.run_json = native
    for name in (
        "verify_candidate_delay_code",
        "verify_candidate_stop_code",
        "verify_candidate_holding_vote_code",
    ):
        monkeypatch.setattr(D.H, name, lambda *args: dict(status="pass"))
    if damage:
        with pytest.raises(ValueError):
            d.preflight()
        assert d._preflight_native_verified is False
    else:
        d.preflight()
        assert d._preflight_native_verified is True
        assert d.state["predecessor_revalidation"]["actual_pid_consumed"] is True
        assert d.document_after == b"original current checklist"
        assert (
            d.directory / "preflight-previous-intraday_release_handoff.log"
        ).read_text() == "old failure"
    assert len(calls) == 2
    assert not d.hold.exists()
    assert {p: p.read_bytes() for p in before} == before


def test_adopted_hold_continues_through_ordinary_native_drain(driver, monkeypatch):
    d = driver
    _, _, failed_path, _ = _failed_hold_fixture(d, monkeypatch)
    failed_before = failed_path.read_bytes()
    d.capture_failed_hold_adoption()
    d.acquire_hold()
    d.launcher = 124
    d.launcher_stat = "456"
    text = Path.read_text

    def stat(path, *args, **kwargs):
        if str(path) == "/proc/124/stat":
            return "124 (bash) " + " ".join(["S"] + ["0"] * 18 + ["456"])
        return text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", stat)
    exists = Path.exists
    alive = {"123": True, "124": True}
    monkeypatch.setattr(
        Path,
        "exists",
        lambda path: (
            alive[path.name]
            if str(path) in ("/proc/123", "/proc/124")
            else exists(path)
        ),
    )
    waits = []

    def wait(predicate, timeout, reason):
        waits.append(reason)
        assert not predicate()
        alive["123" if len(waits) == 1 else "124"] = False
        assert predicate()
        if len(waits) == 2:
            d.flag.unlink()

    monkeypatch.setattr(D, "_wait", wait)
    monkeypatch.setattr(D, "_session_absent", lambda: True)
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.drain()
    assert d.phase == "drained" and len(waits) == 2
    assert failed_path.read_bytes() == failed_before
    d.assert_hold()
    d.assert_unchanged()


def test_hold_transfer_postrename_io_failure_preserves_truthful_owned_hold(
    driver, monkeypatch
):
    d = driver
    _, _, failed_path, _ = _failed_hold_fixture(d, monkeypatch)
    failed_before = failed_path.read_bytes()
    d.capture_failed_hold_adoption()
    atomic = D._atomic

    def publication_failure(path, raw, **kwargs):
        atomic(path, raw, **kwargs)
        if Path(path) == d.hold:
            raise OSError("postrename directory sync failure")

    monkeypatch.setattr(D, "_atomic", publication_failure)
    with pytest.raises(OSError, match="postrename"):
        d.acquire_hold()
    assert d.hold.read_bytes() == d.hold_bytes
    assert (
        d.state["failed_hold_adoption"]["transfer_status"]
        == "transferred_but_publication_failed"
    )
    assert failed_path.read_bytes() == failed_before


@pytest.mark.parametrize("which", ["hold", "failed", "selector_lock"])
def test_failed_hold_adoption_rejects_special_files_without_replacement(
    driver, monkeypatch, which
):
    d = driver
    _, _, failed_path, _ = _failed_hold_fixture(d, monkeypatch)
    original = d.hold.read_bytes()
    if which == "selector_lock":
        d.capture_failed_hold_adoption()
        target = d.selection.with_suffix(".lock")
        target.unlink()
        os.mkfifo(target)
        with pytest.raises(ValueError, match="regular_file_required"):
            d.acquire_hold()
        assert d.hold.read_bytes() == original
    else:
        target = d.hold if which == "hold" else failed_path
        target.unlink()
        os.mkfifo(target)
        with pytest.raises(ValueError, match="regular_file_required"):
            d.capture_failed_hold_adoption()
        assert target.is_fifo()
        if which != "hold":
            assert d.hold.read_bytes() == original


def test_publish_preserves_concurrent_work_checklist(driver, monkeypatch):
    d = driver
    d.preserve_editable_checklist = True
    d.frozen = {}
    d.hold_bytes = b"owned"
    d.hold.write_bytes(d.hold_bytes)
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.checklist.write_bytes(b"other session changed its approved plan")
    before = d.checklist.read_bytes()
    d.publish()
    assert d.checklist.read_bytes() == before
    assert d.state["checklist_sha256"] == D._digest(before)
    assert d.selection.read_bytes() == d.published


@pytest.mark.parametrize("preserve", [True, False])
def test_preflight_reads_git_checklist_only_when_replacing_it(driver, monkeypatch, preserve):
    """An unversioned working checklist is valid only in preservation mode."""
    d = driver
    _failed_hold_fixture(d, monkeypatch)
    calls = _mock_adoption_preflight(d, monkeypatch)
    d.adopt_failed_hold = False
    d.hold.unlink()
    d.preserve_editable_checklist = preserve
    checklist = d.workspace / "docs/checklists" / (d.day + "-stage2-todo-checklist.md")
    before = checklist.read_bytes()

    def native(root, module, *args, **kwargs):
        calls.append(module)
        assert not d.hold.exists()
        return {"status": "pass", "basis": "intraday_policy_preserving_handoff"}

    d.run_json = native

    def unavailable(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0])

    monkeypatch.setattr(D.subprocess, "check_output", unavailable)
    if preserve:
        d.preflight()
        assert d.document_after == before
        assert d._preflight_native_verified is True
    else:
        with pytest.raises(subprocess.CalledProcessError):
            d.preflight()
        assert d._preflight_native_verified is False
    assert d.checklist.read_bytes() == before
    assert not d.hold.exists()


def test_publish_replaces_inherited_candidate_p5(driver, monkeypatch):
    d = driver
    d.old.update(
        candidate_p5_path="/old/candidate/final.json", candidate_p5_sha256="f" * 64
    )
    d.before = D._json_bytes(d.old)
    d.selection.write_bytes(d.before)
    original = d.selection.read_bytes()
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.publish()
    published = json.loads(d.selection.read_bytes())
    assert published["candidate_p5_path"] == str(d.candidate_p5_path)
    assert published["candidate_p5_sha256"] == d.candidate_p5_sha256
    assert d.before == original
    proof = json.loads(d.candidate_p5_path.read_bytes())
    assert proof["execution_release_commit"] == published["git_commit"]
    # Pre-drain P5 correctly identifies the incumbent as then-selected.
    assert proof["selected_release_commit"] == d.previous_commit != d.commit


@pytest.mark.parametrize(
    "fault",
    [
        "commit",
        "root",
        "date",
        "selected_commit",
        "selected_root",
        "sha",
        "missing",
        "failed",
        "findings",
        "terminated",
        "load",
        "sources",
        "runtime",
        "apply",
        "pid",
        "symlink",
        "fifo",
        "duplicate",
        "run_id",
        "exit",
        "failure_phase",
    ],
)
def test_candidate_p5_rejects_unbound_or_invalid_proof_before_hold(driver, fault):
    d = driver
    path = d.candidate_p5_path
    value = json.loads(path.read_bytes())
    fields = {
        "commit": "execution_release_commit",
        "root": "execution_release_root",
        "date": "target_date",
        "selected_commit": "selected_release_commit",
        "selected_root": "selected_release_root",
        "failed": "status",
        "findings": "findings",
        "terminated": "child_terminated",
        "load": "load_check_passed",
        "sources": "protected_sources_unchanged",
        "runtime": "runtime_effect",
        "apply": "allowed_runtime_apply",
        "pid": "actual_pid_consumed",
        "run_id": "run_id",
        "exit": "child_exit_code",
        "failure_phase": "failure_phase",
    }
    if fault in fields:
        value[fields[fault]] = (
            ["failure"]
            if fault == "findings"
            else (
                False
                if fault in {"terminated", "load", "sources"}
                else True if fault in {"runtime", "apply", "pid"} else "foreign"
            )
        )
        path.write_bytes(D._json_bytes(value))
        d.candidate_p5_sha256 = D.H._sha(path)
    elif fault == "sha":
        d.candidate_p5_sha256 = "0" * 64
    elif fault == "missing":
        path.unlink()
    elif fault == "symlink":
        saved = path.with_suffix(".old")
        path.rename(saved)
        path.symlink_to(saved)
    elif fault == "fifo":
        path.unlink()
        os.mkfifo(path)
    elif fault == "duplicate":
        path.write_bytes(b'{"status":"passed","status":"passed"}')
        d.candidate_p5_sha256 = D.H._sha(path)
    before = d.selection.read_bytes()
    with pytest.raises((ValueError, OSError)):
        d.pin_candidate_p5()
    assert d.selection.read_bytes() == before and not d.hold.exists()


@pytest.mark.parametrize(
    "changed", ["p5", "same_bytes_new_inode", "selector", "during_publication"]
)
def test_p5_or_selector_change_stops_publication(driver, monkeypatch, changed):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    original = d.selection.read_bytes()
    if changed == "p5":
        d.candidate_p5_path.write_text("{}")
    elif changed == "same_bytes_new_inode":
        saved = d.candidate_p5_path.with_suffix(".old")
        d.candidate_p5_path.rename(saved)
        d.candidate_p5_path.write_bytes(saved.read_bytes())
    elif changed == "selector":
        d.selection.write_text("{}")
    else:
        monkeypatch.setattr(
            D,
            "inherit_prepared_delay_code",
            lambda *a: d.candidate_p5_path.write_text("{}"),
        )
    expected = d.selection.read_bytes()
    with pytest.raises((ValueError, OSError)):
        d.publish()
    assert d.selection.read_bytes() == expected
    assert d.hold.read_bytes() == d.hold_bytes
    if changed != "selector":
        assert expected == original


@pytest.mark.parametrize(
    "module",
    [
        "src.engine.automation.intraday_release_handoff",
        "src.engine.automation.runtime_policy_bootstrap",
    ],
)
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "reviewed_pair",
        "other_code",
        "cache",
        "missing",
        "symlink",
        "oversize",
        "flag",
    ],
)
def test_predecessor_digest_session_requires_same_reviewed_cli_and_cache(
    tmp_path, module, damage
):
    previous, candidate = tmp_path / "old", tmp_path / "new"
    relative = module.replace(".", "/") + ".py"
    cache = "src/engine/infrastructure/validation_digest_session.py"
    raw = "REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES = {'path': ('old','new')}\ndef main():\n    return '--validation-session'\n"
    for root in (previous, candidate):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(raw)
        (root / cache).parent.mkdir(parents=True, exist_ok=True)
        (root / cache).write_text("DIGEST_CONTRACT=1\n")
    if damage == "reviewed_pair":
        (previous / relative).write_text(
            raw.replace("('old','new')", "('old','reviewed')")
        )
    elif damage == "other_code":
        (previous / relative).write_text(raw + "OTHER_VALIDATION=1\n")
    elif damage == "cache":
        (previous / cache).write_text("DIGEST_CONTRACT=2\n")
    elif damage == "missing":
        (previous / relative).unlink()
    elif damage == "symlink":
        (previous / relative).unlink()
        (previous / relative).symlink_to(candidate / relative)
    elif damage == "oversize":
        (previous / relative).write_text("#" * (2 * 1024 * 1024 + 1))
    elif damage == "flag":
        for root in (previous, candidate):
            (root / relative).write_text(
                raw.replace("--validation-session", "--unsupported")
            )
    expected = (
        damage is None
        or damage == "reviewed_pair"
        and module.endswith(".intraday_release_handoff")
    )
    before = {
        p: p.read_bytes()
        for root in (previous, candidate)
        for p in root.rglob("*.py")
        if p.exists()
    }
    assert D._compatible_validation_session(previous, candidate, module) is expected
    assert all(p.read_bytes() == value for p, value in before.items())


@pytest.mark.parametrize("compatible", [False, True])
def test_run_json_uses_predecessor_session_only_when_compatible_and_keeps_timeout(
    tmp_path, monkeypatch, compatible
):
    d = object.__new__(D.Deployment)
    d.candidate = tmp_path / "new"
    d.validation_session = "a" * 32
    previous = tmp_path / "old"
    calls = []
    monkeypatch.setattr(D, "_compatible_validation_session", lambda *a: compatible)

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, '{"status":"pass"}', "")

    monkeypatch.setattr(D.subprocess, "run", run)
    assert d.run_json(
        previous,
        "src.engine.automation.runtime_policy_bootstrap",
        "--verify",
        timeout=17,
    ) == {"status": "pass"}
    argv, options = calls[0]
    assert ("--validation-session" in argv) is compatible
    if compatible:
        assert argv[-2:] == ["--validation-session", d.validation_session]
    assert options["timeout"] == 17 and options["cwd"] == previous


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "phase",
        "error",
        "date",
        "hold",
        "selection",
        "original",
        "main",
        "supervisor",
        "flag",
        "native",
        "ancestry",
        "race",
    ],
)
@pytest.mark.parametrize("native_basis", [False, True])
def test_stopped_policy_code_handoff_uses_only_proven_original_ancestry(
    stopped_recovery, monkeypatch, damage, native_basis, origin_fault=None
):
    from src.engine.scalping import reversal_code_handoff as C

    d, status_path, policy = stopped_recovery
    selected = D.H._read(d.selection)
    failed_root = Path(selected["release_root"])
    failed_commit = selected["git_commit"]
    prior = D.H._read(status_path.with_name("selection-before.json"))
    if native_basis:
        selected.update(native_predecessor_path=str(status_path.with_name("native-predecessor.json")),
                        native_predecessor_sha256="f" * 64)
        d.selection.write_bytes(D._json_bytes(selected))
        issued_path = C.path(d.workspace / "data", d.day, failed_commit, "bundle")
        issued_path.parent.mkdir(parents=True)
        issued = dict(origin_root=prior["release_root"], origin_commit=prior["git_commit"],
                      origin_selection_sha256=D._digest(status_path.with_name("selection-before.json").read_bytes()))
        if origin_fault: issued[origin_fault] = "foreign"
        issued_path.write_bytes(D._json_bytes(issued))
        def native(day, commit, previous, previous_commit, identity, path, sha):
            assert day == d.day and commit == failed_commit
            assert str(previous) == prior["release_root"] and previous_commit == prior["git_commit"]
            assert path == selected["native_predecessor_path"] and sha == selected["native_predecessor_sha256"]
            if damage == "native": raise ValueError("native invalid")
            return dict(frozen_files={str(policy): D.H._sha(policy)})
        monkeypatch.setattr(D.H, "_native_predecessor", native)
    else:
        selected.pop("native_predecessor_path", None)
        selected.pop("native_predecessor_sha256", None)
        d.selection.write_bytes(D._json_bytes(selected))
    monkeypatch.setattr(
        D,
        "_stopped_intraday_predecessor",
        lambda *a: dict(frozen_files={str(policy): D.H._sha(policy)}),
    )

    if native_basis:
        monkeypatch.setattr(D, "_stopped_intraday_predecessor", lambda *a: (_ for _ in ()).throw(AssertionError("native origin must not use intraday receipt")))

    def ancestry(data, day, origin, commit, bundle, pointer):
        assert str(origin) == (str(failed_root) if native_basis else prior["release_root"])
        assert commit == (failed_commit if native_basis else prior["git_commit"])
        if damage == "race":
            d.hold.write_text("{}")
        return (
            None
            if damage == "ancestry"
            else dict(bundle_sha256=bundle, source_hashes={str(issued_path): D.H._sha(issued_path)} if native_basis else {})
        )

    monkeypatch.setattr(C, "_validated_origin_receipt", ancestry)
    if damage in {"phase", "error", "date"}:
        row = D.H._read(status_path)
        row[
            {"phase": "failed_phase", "error": "error", "date": "target_date"}[damage]
        ] = "foreign"
        status_path.write_bytes(D._json_bytes(row))
    if damage == "hold":
        d.hold.write_text("{}")
    if damage in {"selection", "original"}:
        p = (
            d.selection
            if damage == "selection"
            else status_path.with_name("selection-before.json")
        )
        row = D.H._read(p)
        row["actual_pid_consumed"] = True if damage == "selection" else False
        p.write_bytes(D._json_bytes(row))
    if damage == "main":
        monkeypatch.setattr(D, "_main_pids", lambda: [1])
    if damage == "supervisor":
        monkeypatch.setattr(D, "_session_absent", lambda: False)
    if damage == "flag":
        d.flag.write_text("restart")
    if damage == "native":
        monkeypatch.setattr(
            D,
            "_stopped_intraday_predecessor",
            lambda *a: (_ for _ in ()).throw(ValueError("native invalid")),
        )
    before = (d.selection.read_bytes(), status_path.read_bytes(), policy.read_bytes())
    if damage or origin_fault:
        with pytest.raises(ValueError):
            C._stopped_origin_receipt(
                d.workspace / "data",
                d.day,
                failed_root,
                failed_commit,
                "bundle",
                "pointer",
            )
    else:
        result = C._stopped_origin_receipt(
            d.workspace / "data", d.day, failed_root, failed_commit, "bundle", "pointer"
        )
        assert result["source_hashes"][str(policy)] == D.H._sha(policy)
        assert (
            str(d.hold) not in result["source_hashes"]
            and str(d.selection) not in result["source_hashes"]
        )
        assert str(status_path) in result["source_hashes"]
    assert before == (
        d.selection.read_bytes(),
        status_path.read_bytes(),
        policy.read_bytes(),
    )


@pytest.mark.parametrize(
    "damage", [None, "missing", "seal", "pointer", "origin", "code", "source", "race"]
)
def test_candidate_active_policy_preflight_is_source_bound_and_read_only(
    tmp_path, monkeypatch, damage
):
    from src.engine.scalping import (
        reversal_code_handoff as C,
        mechanistic_entry_runtime_policy as N,
    )

    data = tmp_path / "data"
    root = data / "runtime/mechanistic_entry_policy"
    root.mkdir(parents=True)
    pointer = root / "current.json"
    pointer.write_text(json.dumps({"bundle_sha256": "b" * 64}))
    selection = data / "runtime/runtime_release_selection.json"
    selection.write_text(json.dumps(dict(release_root="/old", git_commit="a" * 40)))
    monkeypatch.setattr(N, "root", lambda data: root)
    monkeypatch.setattr(N, "validate", lambda *a, **k: None)
    (root / "generations").mkdir()
    (root / "generations" / ("b" * 64 + ".json")).write_text(
        json.dumps(dict(bundle_sha256="b" * 64, target_date="2026-10-16"))
    )
    code = tmp_path / "code.py"
    code.write_text("reviewed code")
    source = tmp_path / "source.json"
    source.write_text("sealed source")
    codes = {str(code): D.H._sha(code)}
    monkeypatch.setattr(C, "code_hashes", lambda: codes)
    receipt = C.P.seal(
        dict(
            schema=C.SCHEMA,
            authority=C.AUTHORITY,
            target_date="2026-10-16",
            release_commit="c" * 40,
            release_root=str(tmp_path),
            bundle_sha256="b" * 64,
            current_pointer_sha256=D.H._sha(pointer),
            origin_root="/old",
            origin_commit="a" * 40,
            origin_selection_sha256=D.H._sha(selection),
            policy_reselected=False,
            provider_called=False,
            actual_pid_consumed=False,
            code_hashes=codes,
            source_hashes={str(source): D.H._sha(source)},
        )
    )
    if damage == "pointer":
        receipt["current_pointer_sha256"] = "x"
    if damage == "origin":
        receipt["origin_commit"] = "foreign"
    if damage == "code":
        receipt["code_hashes"] = {str(code): "0" * 64}
    receipt = C.P.seal(receipt)
    if damage == "seal":
        receipt["artifact_content_sha256"] = "0" * 64
    dest = C.path(data, "2026-10-16", "c" * 40, "b" * 64)
    dest.parent.mkdir(parents=True)
    dest.write_text(json.dumps(receipt))
    if damage == "missing":
        dest.unlink()
    if damage == "source":
        source.write_text("tampered")

    def matches(ref, **kwargs):
        if damage == "race":
            pointer.write_text("{}")
        return D.H._sha(ref["path"]) == ref["sha256"]

    monkeypatch.setattr(N, "source_receipt_matches", matches)
    before = selection.read_bytes()
    if damage:
        with pytest.raises((ValueError, OSError)):
            D.verify_candidate_active_policy(tmp_path, tmp_path, "c" * 40, "2026-10-16")
    else:
        result = D.verify_candidate_active_policy(
            tmp_path, tmp_path, "c" * 40, "2026-10-16"
        )
        assert result["status"] == "pass" and result["receipt_sha256"] == D.H._sha(dest)
    assert selection.read_bytes() == before
    assert not (data / "runtime/operator_startup_hold.json").exists()
    assert not (tmp_path / "restart.flag").exists()


def test_active_scheduled_owner_blocks_before_deployment_preflight(tmp_path):
    calls = []

    class Driver:
        workspace = tmp_path

        def preflight(self):
            calls.append("preflight")

        def fail(self, exc):
            calls.append(str(exc))

    with D.R.scheduled_execution_lease(tmp_path):
        with pytest.raises(ValueError, match="scheduled_execution_active"):
            D.execute(Driver())
    assert calls == []
    assert not (tmp_path / "data/runtime/operator_startup_hold.json").exists()


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "other_failure",
        "unverified_origin",
        "changed_manifest",
        "changed_candidate",
    ],
)
def test_prepared_delay_origin_preflight_remains_read_only(
    tmp_path, monkeypatch, fault
):
    from src.engine.automation import prepared_policy_code_handoff as P
    from src.engine.scalping import pre_submit_delay_initial_policy as delay

    data = tmp_path / "data"
    data.mkdir()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            dict(
                pre_submit_delay_handoff=dict(
                    policy_sha256="policy", code_contract_sha256="original"
                )
            )
        )
    )
    monkeypatch.setattr(D.H.bootstrap, "manifest_path", lambda _: manifest)
    monkeypatch.setattr(D.H, "DATA_DIR", data)

    def original(*a):
        raise ValueError(
            "other_failure"
            if fault == "other_failure"
            else "entry_consumer_original_code_contract_invalid"
        )

    monkeypatch.setattr(D.H, "verify_candidate_delay_code", original)
    monkeypatch.setattr(
        D.R, "selected_release", lambda _: (tmp_path / "previous", "previous")
    )
    monkeypatch.setattr(delay, "CONTRACT_PATHS", ("source.py",))
    calls = []

    def resolve(*a, **kw):
        calls.append(kw)
        return dict(
            basis=(
                "wrong"
                if fault == "unverified_origin"
                else "verified_selected_prepared_code_handoff"
            ),
            origin_commit="origin",
            sources={},
        )

    monkeypatch.setattr(P, "resolve_prepared_code_origin", resolve)

    def delta(*args):
        assert args == (
            tmp_path / "candidate",
            "candidate",
            "origin",
            {"source.py": "source.py"},
            "original",
        )
        if fault == "changed_manifest":
            manifest.write_text("{}")
        if fault == "changed_candidate":
            raise ValueError("candidate_dirty")
        return ["source.py"]

    monkeypatch.setattr(D.H, "_verify_entry_code_delta", delta)
    monkeypatch.setattr(
        P, "issue", lambda *a, **kw: pytest.fail("preflight must not publish")
    )
    if fault:
        with pytest.raises(ValueError):
            D.verify_candidate_delay_code("day", tmp_path / "candidate", "candidate")
    else:
        result = D.verify_candidate_delay_code(
            "day", tmp_path / "candidate", "candidate"
        )
        assert result["status"] == "pass" and result["actual_pid_consumed"] is False
        assert result["prepared_code_origin"]["origin_commit"] == "origin"
        assert (
            calls[0]["selected_commit"] == "previous"
            and calls[0]["policy_sha"] == "policy"
        )


@pytest.mark.parametrize("changed", [False, True])
def test_prepared_delay_inheritance_preserves_native_issuer_and_source_cas(
    tmp_path, monkeypatch, changed
):
    from src.engine.automation import prepared_policy_code_handoff as P

    source = tmp_path / "source"
    source.write_text("original")
    original = tmp_path / "prepared"
    original.write_text(json.dumps(dict(verification_path="original-verification")))
    previous = tmp_path / "previous"
    previous.write_text(
        json.dumps(
            dict(
                prepared_receipt=str(original),
                original_prepared_receipt="original-prepared",
                policy_sha256="policy",
                original_code_sha256="code",
                paths={"key": "source.py"},
            )
        )
    )
    check = dict(
        prepared_code_origin=dict(
            sources={str(source): D.H._sha(source)},
            code_handoff_receipt_path=str(previous),
        )
    )
    calls = []
    monkeypatch.setattr(
        P, "issue", lambda *a, **kw: calls.append((a, kw)) or {"verified": True}
    )
    if changed:
        source.write_text("changed")
        with pytest.raises(ValueError, match="source_changed"):
            D.inherit_prepared_delay_code(
                tmp_path, "day", tmp_path / "candidate", check
            )
        assert calls == []
    else:
        assert D.inherit_prepared_delay_code(
            tmp_path, "day", tmp_path / "candidate", check
        ) == {"verified": True}
        assert calls[0][1]["previous_handoff"] == previous
        assert calls[0][1]["origin_verification"] == "original-verification"
        assert calls[0][1]["confirm"] == P.AUTHORITY


@pytest.mark.parametrize("fail", [False, True])
def test_prepared_inheritance_happens_after_drain_before_selection(
    driver, monkeypatch, fail
):
    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    before = d.selection.read_bytes()
    d.prepared_delay_check = {"prepared_code_origin": {"test": "bound"}}
    calls = []

    def inherit(workspace, day, candidate, check):
        assert d.phase == "drained" and d.hold.read_bytes() == d.hold_bytes
        assert d.selection.read_bytes() == before and check == d.prepared_delay_check
        calls.append(True)
        if fail:
            raise ValueError("native_issuer_refused")

    monkeypatch.setattr(D, "inherit_prepared_delay_code", inherit)
    if fail:
        with pytest.raises(ValueError, match="native_issuer_refused"):
            d.publish()
        assert d.selection.read_bytes() == before and d.phase == "drained"
    else:
        d.publish()
        assert d.phase == "selected" and d.selection.read_bytes() != before
    assert calls == [True]


@pytest.mark.parametrize(
    "phase,error,valid",
    [
        ("starting", "deployment_pid_attestation_timeout", True),
        (
            "starting",
            "deployment_validation_failed:src.engine.automation.intraday_release_handoff",
            False,
        ),
        ("selected", "deployment_pid_attestation_timeout", False),
    ],
)
def test_stopped_startup_timeout_recovery_keeps_exact_phase_and_error(
    stopped_recovery, phase, error, valid
):
    d, path, _ = stopped_recovery
    value = D.H._read(path)
    value.update(failed_phase=phase, error=error)
    path.write_bytes(D._json_bytes(value))
    before = path.read_bytes(), d.hold.read_bytes()
    if valid:
        d.preflight()
        assert d.state["failed_hold_adoption"]["source_failure"] == error
    else:
        with pytest.raises(ValueError, match="stopped_recovery_source_invalid"):
            d.preflight()
    assert before == (path.read_bytes(), d.hold.read_bytes())


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "code",
        "source",
        "quantity_incomplete",
        "quantity_missing",
        "missing_after_date",
    ],
)
def test_report_preflight_reuses_native_currentness_and_preserves_economic_gaps(
    tmp_path, monkeypatch, fault
):
    from src.engine.monitoring import main_trailing_currentness as trailing
    from src.engine.error_detectors import artifact_freshness as artifacts

    day, source = "2026-10-20", "2026-10-19"
    monkeypatch.setattr(
        D.H, "preserve_checklist", lambda target: {"source_date": source}
    )
    monkeypatch.setattr(D.H, "_read", lambda path: {"original": "holding"})
    monkeypatch.setattr(
        trailing,
        "observe",
        lambda data, held, target_date: {
            "status": "code_changed" if fault == "code" else "generation_current"
        },
    )
    quantity = dict(
        status="source_gap",
        findings=["initial_quantity_economic_source_gap"],
        bounded_contract_validated=fault != "source",
        observation_complete=fault != "quantity_incomplete",
        postclose_stage_status=(
            "not_observed" if fault == "quantity_missing" else "source_gap"
        ),
    )
    if fault == "missing_after_date":
        quantity["findings"] = ["initial_quantity_stage_missing_after_date"]
    seen = []

    def observe(root, date):
        seen.append((root, date))
        return quantity

    monkeypatch.setattr(artifacts, "_initial_quantity_semantics", observe)
    if fault:
        with pytest.raises(ValueError, match="deployment_.*report_not_current"):
            D.verify_candidate_report_currentness(tmp_path, tmp_path / "candidate", day)
    else:
        result = D.verify_candidate_report_currentness(
            tmp_path, tmp_path / "candidate", day
        )
        assert result["status"] == "pass" and result["source_date"] == source
        assert result["quantity"]["findings"] == [
            "initial_quantity_economic_source_gap"
        ]
        assert (
            result["runtime_effect"] is False and result["policy_effect"] == "unchanged"
        )
    assert seen == ([] if fault == "code" else [(tmp_path / "candidate", source)])


@pytest.mark.parametrize("failure", [False, True, "handoff"])
def test_prepare_binds_native_source_window_before_start(
    monkeypatch, tmp_path, failure
):
    from src.engine.monitoring import sentinel_source_window as window
    from src.engine.automation import prepared_policy_code_handoff as code

    driver = object.__new__(D.Deployment)
    driver.workspace = tmp_path
    driver.candidate = tmp_path / "candidate"
    driver.previous = tmp_path / "previous"
    driver.day = "2026-10-21"
    driver.identity = {"pid": 123}
    driver.state = dict(candidate_report_currentness=_report_currentness_fixture(driver.workspace, driver.candidate, driver.day))
    calls = []
    driver.assert_hold = lambda: calls.append("hold")
    driver.run_json = lambda root, module, *args: calls.append(module)
    driver.checkpoint = lambda phase, **kw: calls.append((phase, kw))
    proof = {"schema": "sentinel_source_window_preparation_v1", "runtime_effect": False}

    def prepare(data):
        assert data == tmp_path / "data" and calls[-1].endswith(
            "auxiliary_reader_readiness"
        )
        calls.append("source_window")
        if failure is True:
            raise ValueError("source_window_cache_unverified")
        return proof

    monkeypatch.setattr(window, "prepare", prepare)
    from src.engine import buy_funnel_sentinel as buy

    (tmp_path / "tmp").mkdir()

    def summary(day):
        assert day == driver.day and calls[-1] == "source_window"
        calls.append("native_summary")
        return [], {"status": "ok"}

    monkeypatch.setattr(buy, "load_pipeline_event_summaries", summary)
    handoffs = [{"family": "main_stop", "actual_pid_consumed": False}]

    def issue(data, day, *, release_root):
        assert data == tmp_path / "data" and day == driver.day
        assert release_root == driver.candidate and calls[-1] == "native_summary"
        calls.append("prepared_code_handoffs")
        if failure == "handoff":
            raise ValueError("prepared_code_source_changed")
        return handoffs

    monkeypatch.setattr(code, "issue_selected", issue, raising=False)
    if failure is True:
        with pytest.raises(ValueError, match="source_window_cache_unverified"):
            driver.prepare()
        assert calls[-1] == "source_window"
    elif failure == "handoff":
        with pytest.raises(ValueError, match="prepared_code_source_changed"):
            driver.prepare()
        assert calls[-1] == "prepared_code_handoffs"
    else:
        driver.prepare()
        assert calls[-1] == (
            "prepared",
            {
                "sentinel_source_window": proof,
                "sentinel_summary": {"status": "ok"},
                "native_prepared_code_handoffs": handoffs,
            },
        )


@pytest.mark.parametrize("damage", [None, "pid", "start", "old_generation", "stale"])
def test_collector_pin_rejects_unproven_incumbent_without_stop_request(
    tmp_path, damage
):
    identity = dict(pid=123, start_ticks="456")
    snapshot = dict(
        process_pid=123,
        process_start_ticks="456",
        collector_lifecycle="running",
        sequence_epoch=9,
        enqueued_count=1,
        source_contract="main_market_source_v1",
    )
    payload = dict(collector_snapshot=snapshot, valid_until_epoch=D.time.time() + 30)
    if damage == "pid":
        snapshot["process_pid"] = 124
    if damage == "start":
        snapshot["process_start_ticks"] = "999"
    if damage == "old_generation":
        snapshot.pop("process_pid")
        snapshot.pop("process_start_ticks")
    if damage == "stale":
        payload["valid_until_epoch"] = 0
    path = tmp_path / "data/runtime/scalp_micro_reversion_forward_collector/latest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))
    if damage:
        with pytest.raises(ValueError, match="actor_unproven"):
            D.pin_collector_shutdown(tmp_path, identity)
    else:
        assert D.pin_collector_shutdown(tmp_path, identity)["sequence_epoch"] == 9
    assert not (tmp_path / "restart.flag").exists()


@pytest.mark.parametrize(
    "damage", [None, "missing", "foreign", "unclosed", "prior_epoch", "loss"]
)
def test_ordered_drain_consumes_exact_native_closed_epoch(tmp_path, damage):
    from src.tests.test_micro_reversion_forward_collector import (
        _closed_main_rejection_source,
    )

    _, payload, receipt = _closed_main_rejection_source(tmp_path)
    c = payload["collector_snapshot"]
    latest = receipt.parent.parent / "latest.json"
    pin = dict(
        path=str(latest),
        pid=c["process_pid"],
        start_ticks=c["process_start_ticks"],
        sequence_epoch=c["sequence_epoch"],
        enqueued_count=1,
    )
    if damage == "missing":
        receipt.unlink()
    elif damage == "foreign":
        pin["start_ticks"] = "foreign"
    elif damage == "prior_epoch":
        pin["sequence_epoch"] = 1
    elif damage:
        if damage == "unclosed":
            c["collector_lifecycle"] = "running"
        if damage == "loss":
            c["writer_dropped_envelope_count"] = 1
        latest.write_text(json.dumps(payload))
        closed = json.loads(receipt.read_bytes())
        closed["collector_snapshot"] = c
        receipt.write_text(json.dumps(closed))
    if damage:
        with pytest.raises((ValueError, FileNotFoundError)):
            D.verify_collector_shutdown(pin)
    else:
        assert D.verify_collector_shutdown(pin)["status"] == "verified"


@pytest.fixture
def market_closed_collector(tmp_path, monkeypatch):
    from datetime import datetime
    from src.tests.test_micro_reversion_forward_collector import (
        _closed_main_rejection_source,
    )

    _, payload, receipt = _closed_main_rejection_source(tmp_path, count=0)
    snapshot = payload["collector_snapshot"]
    # Native legacy receipt: actor comes from the existing WS producer, not
    # from adding missing fields to an operational closed receipt.
    snapshot.pop("process_pid")
    snapshot.pop("process_start_ticks")
    identity = dict(pid=123, start_ticks="456", cwd=str(tmp_path / "old/src"))
    selection = dict(
        release_root=str(tmp_path / "old"),
        git_commit="a" * 40,
        actual_pid_consumed=True,
        actual_pid_receipt=dict(
            pid=123,
            start_ticks="456",
            process_cwd=identity["cwd"],
            recorded_at_kst="2026-08-08T10:00:00+09:00",
        ),
    )
    frame = dict(
        generated_at_epoch=datetime.fromisoformat(
            "2026-08-08T19:59:59+09:00"
        ).timestamp(),
        shared_transport_producer=dict(
            schema="shared_ws_transport_producer_v1",
            process=dict(
                pid=123,
                start_ticks=456,
                boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            ),
            source_root=selection["release_root"],
            source_commit=selection["git_commit"],
            completed_bar_integrity=dict(observer_epoch=snapshot["sequence_epoch"]),
        ),
    )
    heartbeat = dict(
        main_loop=dict(pid=123),
        ai_circuit=dict(pid=123, process_start_ticks="456"),
        threads=dict(
            sniper_engine=dict(
                alive=False,
                terminal_reason="market_close",
                last_beat="2026-08-08T20:00:00+09:00",
                unresolved_scalping_count=0,
                unresolved_scalping_codes="",
            )
        ),
    )
    values = {
        receipt: payload,
        receipt.parent.parent / "latest.json": payload,
        tmp_path / "data/runtime/runtime_release_selection.json": selection,
        tmp_path / "data/runtime/kiwoom_ws_snapshot/latest.json": frame,
        tmp_path / "tmp/error_detector_heartbeat.json": heartbeat,
    }

    def persist():
        for path, value in values.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))

    persist()

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat("2026-08-08T20:01:00+09:00").astimezone(tz)

    monkeypatch.setattr(D, "datetime", Clock)
    return identity, payload, receipt, selection, frame, heartbeat, persist


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "running",
        "pid",
        "start",
        "boot",
        "commit",
        "root",
        "epoch",
        "future_frame",
        "future_close",
        "previous_day",
        "terminal_reason",
        "unresolved",
        "alive",
        "heartbeat_actor",
        "conflicting_collector_actor",
        "loss",
        "missing_closed",
        "closed_symlink",
        "closed_changed",
        "missing_frame",
        "unaccounted_rejections",
    ],
)
def test_legacy_first_transition_requires_native_closure_before_any_stop(
    tmp_path, market_closed_collector, damage
):
    identity, payload, receipt, selection, frame, heartbeat, persist = (
        market_closed_collector
    )
    c = payload["collector_snapshot"]
    producer = frame["shared_transport_producer"]
    terminal = heartbeat["threads"]["sniper_engine"]
    if damage == "running":
        c["collector_lifecycle"] = "running"
    if damage == "pid":
        producer["process"]["pid"] = 124
    if damage == "start":
        producer["process"]["start_ticks"] = 457
    if damage == "boot":
        producer["process"]["boot_id"] = "another-boot"
    if damage == "commit":
        producer["source_commit"] = "b" * 40
    if damage == "root":
        producer["source_root"] = str(tmp_path / "other")
    if damage == "epoch":
        producer["completed_bar_integrity"]["observer_epoch"] += 1
    if damage == "future_frame":
        frame["generated_at_epoch"] += 600
    if damage == "future_close":
        payload["generated_at"] = "2026-08-08T20:02:00+09:00"
    if damage == "previous_day":
        selection["actual_pid_receipt"]["recorded_at_kst"] = "2026-08-07T10:00:00+09:00"
    if damage == "terminal_reason":
        terminal["terminal_reason"] = "crash"
    if damage == "unresolved":
        terminal["unresolved_scalping_count"] = 1
    if damage == "alive":
        terminal["alive"] = True
    if damage == "heartbeat_actor":
        heartbeat["ai_circuit"]["process_start_ticks"] = "457"
    if damage == "conflicting_collector_actor":
        c["process_pid"] = 124
    if damage == "loss":
        c["writer_dropped_envelope_count"] = 1
    if damage == "unaccounted_rejections":
        c["timestamp_rejection_sample_total"] = 65
        payload["canary_guard"]["raw_row_exclusion_required"] = True
    persist()
    if damage == "missing_closed":
        receipt.unlink()
    if damage == "closed_symlink":
        other = receipt.with_suffix(".original")
        receipt.rename(other)
        receipt.symlink_to(other)
    if damage == "closed_changed":
        changed = json.loads(receipt.read_bytes())
        changed["collector_snapshot"]["enqueued_count"] += 1
        receipt.write_text(json.dumps(changed))
    if damage == "missing_frame":
        (tmp_path / "data/runtime/kiwoom_ws_snapshot/latest.json").unlink()
    if damage:
        with pytest.raises((ValueError, FileNotFoundError)):
            D.pin_collector_shutdown(tmp_path, identity)
    else:
        pin = D.pin_collector_shutdown(tmp_path, identity)
        assert pin["basis"] == "native_market_close"
        assert D.verify_collector_shutdown(pin)["status"] == "verified"
        # This is actor binding only; never rewrite the legacy producer bytes.
        assert (
            "process_pid" not in json.loads(receipt.read_bytes())["collector_snapshot"]
        )
    assert not (tmp_path / "restart.flag").exists()
    assert not (tmp_path / "data/runtime/operator_startup_hold.json").exists()


@pytest.mark.parametrize("changed", ["frame", "latest", "closed"])
def test_first_transition_rechecks_closed_proof_after_process_exit(
    tmp_path, market_closed_collector, changed
):
    identity, payload, receipt, selection, frame, heartbeat, persist = (
        market_closed_collector
    )
    pin = D.pin_collector_shutdown(tmp_path, identity)
    path = {
        "frame": tmp_path / "data/runtime/kiwoom_ws_snapshot/latest.json",
        "latest": receipt.parent.parent / "latest.json",
        "closed": receipt,
    }[changed]
    value = json.loads(path.read_bytes())
    if changed == "closed":
        value["collector_snapshot"]["writer_dropped_envelope_count"] = 1
    else:
        value["changed_generation"] = True
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        D.verify_collector_shutdown(pin)


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "stale_frame",
        "missing_frame",
        "pid",
        "start",
        "source_contract",
        "heartbeat",
        "unresolved",
        "missing_closed",
        "changed_after_pin",
    ],
)
def test_owned_closed_collector_uses_native_actor_without_legacy_ws_frame(
    tmp_path, market_closed_collector, damage
):
    identity, payload, receipt, selection, frame, heartbeat, persist = (
        market_closed_collector
    )
    snapshot = payload["collector_snapshot"]
    snapshot.update(
        process_pid=identity["pid"], process_start_ticks=identity["start_ticks"]
    )
    if damage in ("stale_frame", "missing_frame"):
        frame["shared_transport_producer"]["process"]["pid"] = 999
        frame["generated_at_epoch"] = 1
    if damage == "pid":
        snapshot["process_pid"] += 1
    if damage == "start":
        snapshot["process_start_ticks"] = "457"
    if damage == "source_contract":
        snapshot["source_contract"] = "unverified"
    if damage == "heartbeat":
        heartbeat["ai_circuit"]["pid"] = 999
    if damage == "unresolved":
        heartbeat["threads"]["sniper_engine"]["unresolved_scalping_count"] = 1
    persist()
    if damage == "missing_frame":
        (tmp_path / "data/runtime/kiwoom_ws_snapshot/latest.json").unlink()
    if damage == "missing_closed":
        receipt.unlink()
    if damage in (
        "pid",
        "start",
        "source_contract",
        "heartbeat",
        "unresolved",
        "missing_closed",
    ):
        with pytest.raises((ValueError, FileNotFoundError)):
            D.pin_collector_shutdown(tmp_path, identity)
    else:
        before = receipt.read_bytes()
        pin = D.pin_collector_shutdown(tmp_path, identity)
        assert D.verify_collector_shutdown(pin)["status"] == "verified"
        if damage == "changed_after_pin":
            receipt.write_bytes(before + b" ")
            with pytest.raises(ValueError):
                D.verify_collector_shutdown(pin)
        else:
            assert receipt.read_bytes() == before
    assert not (tmp_path / "restart.flag").exists()
    assert not (tmp_path / "data/runtime/operator_startup_hold.json").exists()


@pytest.mark.parametrize("failure", [None, "preflight", "prepare"])
def test_execute_reserves_sentinel_before_drain_releases_before_start(
    tmp_path, failure
):
    (tmp_path / "data").mkdir()
    (tmp_path / "tmp").mkdir()
    calls = []

    class Driver:
        workspace = tmp_path
        day = "2026-10-12"

        def __getattr__(self, name):
            def step(*args):
                calls.append(name)
                if name in ("preflight", "drain", "publish", "prepare", "start", "attest"):
                    with (tmp_path / "tmp/run_buy_funnel_sentinel.lock").open(
                        "a"
                    ) as lock:
                        if name in ("preflight", "drain", "publish", "prepare"):
                            with pytest.raises(BlockingIOError):
                                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        else:
                            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if name == failure:
                    raise ValueError(name)
                return {"status": "pass"}

            return step

    if failure:
        with pytest.raises(ValueError, match=failure):
            D.execute(Driver())
        assert "start" not in calls
    else:
        assert D.execute(Driver()) == {"status": "pass"}
    with (tmp_path / "tmp/run_buy_funnel_sentinel.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize("prepared", [False, True, "published_comparison"])
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "missing",
        "status",
        "date",
        "pid",
        "changed_after_preflight",
        "window",
        "summary",
    ],
)
def test_stopped_lock_recovery_requires_all_native_preparations(
    stopped_recovery, damage, prepared
):
    d, path, _ = stopped_recovery
    value = D.H._read(path)
    value["error"] = "[Errno 11] Resource temporarily unavailable"
    if prepared:
        value.update(
            failed_phase="prepared",
            error=(
                "deployment_selection_changed"
                if prepared == "published_comparison"
                else "tuple indices must be integers or slices, not str"
            ),
            sentinel_source_window=dict(
                schema="sentinel_source_window_preparation_v1",
                target_date=d.day,
                runtime_effect=False,
            ),
            sentinel_summary=dict(status="ok", runtime_effect=False),
        )
    if damage in ("window", "summary"):
        if not prepared:
            return
        value["sentinel_source_window" if damage == "window" else "sentinel_summary"][
            "runtime_effect"
        ] = True
    path.write_bytes(D._json_bytes(value))
    logs = []
    for module in (
        "intraday_release_handoff",
        "runtime_policy_bootstrap",
        "auxiliary_reader_readiness",
    ):
        p = path.with_name("selected-" + module + ".log")
        logs.append(p)
        p.write_bytes(
            D._json_bytes(
                dict(
                    status="pass",
                    target_date=d.day,
                    actual_pid_consumed=False,
                    findings=[],
                )
            )
        )
    last = logs[-1]
    if damage == "missing":
        last.unlink()
    elif damage in ("status", "date", "pid"):
        body = D.H._read(last)
        body[
            {"status": "status", "date": "target_date", "pid": "actual_pid_consumed"}[
                damage
            ]
        ] = {"status": "fail", "date": "2020-01-01", "pid": True}[damage]
        last.write_bytes(D._json_bytes(body))
    original = path.read_bytes(), d.hold.read_bytes()
    if damage in ("missing", "status", "date", "pid", "window", "summary"):
        with pytest.raises((OSError, ValueError)):
            d.preflight()
    else:
        d.preflight()
        assert all(d.frozen[str(p)] == D.H._sha(p) for p in logs)
        if damage == "changed_after_preflight":
            last.write_bytes(last.read_bytes() + b" ")
            with pytest.raises(ValueError, match="generation_changed"):
                d.acquire_hold()
    assert original == (path.read_bytes(), d.hold.read_bytes())


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "whitespace",
        "conflict",
        "date",
        "root",
        "commit",
        "status",
        "finding",
        "missing",
        "changed_after_preflight",
    ],
)
@pytest.mark.parametrize("short_reference", [False, True, "native_intake"])
def test_stopped_prestart_failure_is_bound_to_original_native_p5(
    stopped_recovery, damage, short_reference
):
    d, path, _ = stopped_recovery
    failed = D.H._read(path)
    intake = dict(
        status="pass",
        findings=[],
        target_date=d.day,
        selected_release_commit=failed["candidate_commit"],
        verification_code_commit=failed["candidate_commit"],
        verification_code_root=failed["candidate_root"],
    )
    result = dict(
        schema="main_policy_load_exit_validation_v1",
        run_id="1" * 32,
        status="failed",
        failure_phase="intake",
        target_date=d.day,
        findings=[
            "ValueError:startup_main_code_pair_unreviewed:src/engine/scalping/reversal_code_handoff.py"
        ],
        runtime_effect=False,
        actual_pid_consumed=False,
        allowed_runtime_apply=False,
        native_preparation_checks=dict(intake=intake),
    )
    if short_reference:
        result["findings"] = ["ValueError:prepared_code_intraday_custody_invalid"]
    if short_reference == "native_intake":
        from datetime import date, timedelta

        source_day = (date.fromisoformat(d.day) - timedelta(days=1)).isoformat()
        result.update(
            findings=["ValueError:startup_native_preparation_result_invalid"],
            load_check_passed=False,
            child_terminated=False,
        )
        intake.update(
            status="invalid_result",
            source_date=source_day,
            exit_code=1,
            diagnostics_status="observed",
            native_validation_io=dict(source_date=source_day),
            native_process_lifecycle=dict(
                ownership_basis="dedicated_native_verifier_session",
                pid=123,
                process_group=123,
                session_id=123,
                start_ticks="456",
                child_terminated=True,
                descendants_drained=True,
                cleanup_required=False,
            ),
        )
        failed["candidate_report_currentness"] = dict(source_date=source_day)
    failed.update(
        failed_phase="prepared",
        error=repr(result),
        sentinel_source_window=dict(
            schema="sentinel_source_window_preparation_v1",
            target_date=d.day,
            runtime_effect=False,
        ),
        sentinel_summary=dict(status="ok", runtime_effect=False),
    )
    native = (
        d.workspace
        / "data/report/main_startup_validation"
        / d.day
        / result["run_id"]
        / "final.json"
    )
    native.parent.mkdir(parents=True)
    native.write_bytes(D._json_bytes(result))
    if damage in ("date", "root", "commit", "status", "finding"):
        if damage == "date":
            result["target_date"] = "2000-01-01"
        elif damage == "root":
            intake["verification_code_root"] = "foreign"
        elif damage == "commit":
            intake["verification_code_commit"] = "d" * 40
        elif damage == "status":
            result["status"] = "passed"
        else:
            result["findings"] = ["unknown"]
        failed["error"] = repr(result)
        native.write_bytes(D._json_bytes(result))
    elif damage == "whitespace":
        native.write_bytes(
            native.read_bytes() + b" "
        )  # same semantics remains exact native bytes frozen
    if damage == "conflict":
        native.write_bytes(D._json_bytes(dict(result, status="passed")))
    if short_reference:
        failed["error"] = "selected_p5_failed:" + str(native)
    path.write_bytes(D._json_bytes(failed))
    for module in (
        "intraday_release_handoff",
        "runtime_policy_bootstrap",
        "auxiliary_reader_readiness",
    ):
        path.with_name("selected-" + module + ".log").write_bytes(
            D._json_bytes(
                dict(
                    status="pass",
                    target_date=d.day,
                    actual_pid_consumed=False,
                    findings=[],
                )
            )
        )
    if damage == "missing":
        native.unlink()
    original = path.read_bytes(), d.hold.read_bytes()
    if damage in ("conflict", "date", "root", "commit", "status", "finding", "missing"):
        with pytest.raises((OSError, ValueError)):
            d.preflight()
    else:
        d.preflight()
        assert d.frozen[str(native)] == D.H._sha(native)
        if damage == "changed_after_preflight":
            native.write_bytes(native.read_bytes() + b" ")
            with pytest.raises(ValueError, match="generation_changed"):
                d.acquire_hold()
    assert original == (path.read_bytes(), d.hold.read_bytes())


@pytest.mark.parametrize("reject", [False, True])
def test_execute_owns_start_after_prepared_validation(tmp_path, monkeypatch, reject):
    from contextlib import nullcontext

    calls = []
    monkeypatch.setattr(D, "_source_database_epoch", lambda *a: nullcontext())
    monkeypatch.setattr(D, "sentinel_preparation_lock", lambda *a: nullcontext())

    class Driver:
        workspace = tmp_path
        day = "2026-10-22"

        def __getattr__(self, name):
            def step(*args):
                calls.append(name)
                if name == "attest":
                    return {"status": "pass"}

            return step

    def validate(driver):
        assert calls == ["preflight", "acquire_hold", "drain", "publish", "prepare"]
        calls.append("validate_prepared")
        if reject:
            raise ValueError("native P5 failed")

    if reject:
        with pytest.raises(ValueError, match="native P5 failed"):
            D.execute(Driver(), validate_prepared=validate)
        assert calls[-1] == "fail" and "start" not in calls
    else:
        assert D.execute(Driver(), validate_prepared=validate) == {"status": "pass"}
        assert calls[-3:] == ["validate_prepared", "start", "attest"]


@pytest.mark.parametrize(
    "reason", ["callback_predecessor_unverified", "append_budget_exceeded"]
)
def test_summary_migration_rejection_prevents_hold_and_drain(
    driver, monkeypatch, reason
):
    from src.engine.monitoring import sentinel_summary_contract as summary

    d = driver
    _failed_hold_fixture(d, monkeypatch)
    native_calls = _mock_adoption_preflight(d, monkeypatch)

    def native(root, module, *args, **kwargs):
        native_calls.append(module)
        return dict(status="pass", basis="intraday_policy_preserving_handoff")

    d.run_json = native
    d.adopt_failed_hold = False
    d.hold.unlink()
    checklist = d.workspace / "docs/checklists" / (d.day + "-stage2-todo-checklist.md")
    before = d.selection.read_bytes(), checklist.read_bytes()
    calls = []

    def reject(*_):
        calls.append("summary_preflight")
        raise RuntimeError("summary_contract_migration_" + reason)

    monkeypatch.setattr(summary, "check_pending_migration", reject)
    for name in ("acquire_hold", "drain", "publish", "prepare", "start"):
        monkeypatch.setattr(d, name, lambda *_, name=name: calls.append(name))
    monkeypatch.setattr(d, "fail", lambda error: calls.append("failed"))
    with pytest.raises(RuntimeError, match=reason):
        D.execute(d)
    assert calls == ["summary_preflight", "failed"]
    assert before == (d.selection.read_bytes(), checklist.read_bytes())
    assert not d.hold.exists() and not d.flag.exists()


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "pid",
        "start",
        "missing_actor",
        "source_contract",
        "reason",
        "guard",
        "guard_config",
        "missing_closed",
        "loss",
        "closed_changed",
        "heartbeat_actor",
        "future_close",
        "previous_day",
        "unconsumed",
        "other_stop",
        "epochs",
        "source_date",
        "changed_after_pin",
    ],
)
def test_verified_observer_canary_close_is_not_a_market_close_requirement(
    tmp_path, market_closed_collector, damage
):
    from src.engine.scalping.micro_reversion import canary_monitor as C

    identity, payload, receipt, selection, frame, heartbeat, persist = (
        market_closed_collector
    )
    config = Path(selection["release_root"]) / "configs" / C.DEFAULT_GUARD_PATH.name
    config.parent.mkdir(parents=True)
    config.write_bytes(C.DEFAULT_GUARD_PATH.read_bytes())
    snapshot = payload["collector_snapshot"]
    reason = "producer_callback_latency_p99_exceeded:5.000000>2.000000"
    snapshot.update(
        process_pid=identity["pid"],
        process_start_ticks=identity["start_ticks"],
        producer_0b_callback_count=1000,
        producer_callback_latency_p95_ms=0.1,
        producer_callback_latency_p99_ms=5.0,
        canary_auto_stop_reason=reason,
    )
    guard = C.load_canary_guard(config)
    payload.update(
        guard_config_sha256=guard.config_sha256,
        baseline_id=guard.baseline_id,
        canary_guard=json.loads(
            json.dumps(C.evaluate_canary_snapshot(snapshot, guard))
        ),
    )
    heartbeat["threads"]["sniper_engine"].update(
        alive=True, last_beat="2026-08-08T20:00:59+09:00"
    )
    if damage == "pid":
        snapshot["process_pid"] += 1
    elif damage == "start":
        snapshot["process_start_ticks"] = "999"
    elif damage == "missing_actor":
        snapshot.pop("process_pid")
    elif damage == "source_contract":
        snapshot["source_contract"] = "unknown"
    elif damage == "reason":
        snapshot["canary_auto_stop_reason"] = "unknown_stop"
    elif damage == "guard":
        payload["canary_guard"]["stop_required"] = False
    elif damage == "guard_config":
        config.write_bytes(config.read_bytes() + b"\n# changed\n")
    elif damage == "loss":
        snapshot["writer_dropped_envelope_count"] = 1
    elif damage == "heartbeat_actor":
        heartbeat["ai_circuit"]["pid"] = 999
    elif damage == "future_close":
        payload["generated_at"] = "2026-08-08T20:02:00+09:00"
    elif damage == "previous_day":
        selection["actual_pid_receipt"]["recorded_at_kst"] = "2026-08-07T10:00:00+09:00"
    elif damage == "unconsumed":
        selection["actual_pid_consumed"] = False
    elif damage == "epochs":
        snapshot["reconciled_sequence_epochs"].append("unknown")
    elif damage == "source_date":
        payload["source_date"] = "2026-08-09"
    elif damage == "other_stop":
        snapshot["canary_auto_stop_reason"] = "nonzero_stop_metric:writer_error_count=1"
        payload["canary_guard"] = json.loads(
            json.dumps(C.evaluate_canary_snapshot(snapshot, guard))
        )
    persist()
    if damage == "missing_closed":
        receipt.unlink()
    elif damage == "closed_changed":
        changed = json.loads(receipt.read_bytes())
        changed["collector_snapshot"]["enqueued_count"] += 1
        receipt.write_text(json.dumps(changed))
    if damage not in (None, "changed_after_pin"):
        with pytest.raises((ValueError, FileNotFoundError)):
            D.pin_collector_shutdown(tmp_path, identity)
    else:
        pin = D.pin_collector_shutdown(tmp_path, identity)
        assert pin["basis"] == "native_observer_canary_stop"
        assert D.verify_collector_shutdown(pin)["status"] == "verified"
        from src.engine.scalping.micro_reversion.observer_source_quality import (
            main_raw_epoch_validation,
        )

        assert (
            main_raw_epoch_validation(payload, source_date="2026-08-08")["eligible"]
            is False
        )
        without_guard = dict(pin)
        without_guard.pop("guard_config_source")
        with pytest.raises(ValueError):
            D.verify_collector_shutdown(without_guard)
        changed = json.loads(receipt.read_bytes())
        changed["canary_guard"]["stop_required"] = False
        receipt.write_text(json.dumps(changed))
        with pytest.raises(ValueError):
            D.verify_collector_shutdown(pin)
        persist()
        if damage == "changed_after_pin":
            config.write_bytes(config.read_bytes() + b"\n# later change\n")
            with pytest.raises(ValueError):
                D.verify_collector_shutdown(pin)
    assert not (tmp_path / "restart.flag").exists()
    assert not (tmp_path / "data/runtime/operator_startup_hold.json").exists()


@pytest.mark.parametrize(
    "fault", [None, "actor", "hash", "main", "supervisor", "changed"]
)
def test_interrupted_collector_preserves_original_and_never_claims_terminal(
    tmp_path, monkeypatch, fault
):
    identity = dict(pid=2147483601, start_ticks="42", cwd=str(tmp_path / "release/src"))
    path = tmp_path / "data/runtime/scalp_micro_reversion_forward_collector/latest.json"
    path.parent.mkdir(parents=True)
    payload = dict(
        collector_snapshot=dict(collector_lifecycle="running", sequence_epoch=123)
    )
    path.write_bytes(D._json_bytes(payload))
    proof = dict(
        basis="interrupted_consumed_process",
        pid_identity=identity,
        collector_path=str(path),
        collector_sha256=D._digest(path.read_bytes()),
        collector_epoch=123,
    )
    if fault == "actor":
        proof["pid_identity"] = {**identity, "pid": 2}
    if fault == "hash":
        proof["collector_sha256"] = "0" * 64
    monkeypatch.setattr(D.H, "closed_consumption_observation", lambda: proof)
    monkeypatch.setattr(D, "_main_pids", lambda: [3] if fault == "main" else [])
    monkeypatch.setattr(D, "_session_absent", lambda: fault != "supervisor")
    if fault in ("actor", "hash", "main", "supervisor"):
        with pytest.raises(ValueError):
            D.pin_collector_shutdown(tmp_path, identity)
        return
    pin = D.pin_collector_shutdown(tmp_path, identity)
    assert (
        pin["original_collector_receipt"] == payload
        and pin["terminal_verified"] is False
    )
    if fault == "changed":
        path.write_text("{}")
        with pytest.raises(ValueError):
            D.verify_collector_shutdown(pin)
    else:
        checked = D.verify_collector_shutdown(pin)
        assert checked["status"] == "preserved_unverified" and checked["receipts"] == []
        assert checked["terminal_verified"] is False


@pytest.mark.parametrize("field", ["origin_root", "origin_commit", "origin_selection_sha256"])
def test_native_stopped_handoff_rejects_foreign_issued_ancestry(stopped_recovery, monkeypatch, field):
    test_stopped_policy_code_handoff_uses_only_proven_original_ancestry(
        stopped_recovery, monkeypatch, None, True, origin_fault=field)


@pytest.mark.parametrize('damage', [None, 'loss', 'pending', 'persistence', 'authority', 'date', 'changed_guard'])
def test_drained_research_ineligible_epoch_preserves_semantic_rejection(tmp_path, damage):
    from src.tests.test_micro_reversion_forward_collector import _closed_main_rejection_source
    from src.engine.scalping.micro_reversion.observer_source_quality import main_raw_epoch_validation
    _, payload, receipt = _closed_main_rejection_source(tmp_path)
    c = payload['collector_snapshot']
    latest = receipt.parent.parent / 'latest.json'
    # Sealed row rejection remains semantically unresolved; persistence is exact.
    payload['canary_guard']['raw_row_exclusion_required'] = True
    payload['canary_guard']['source_quality_row_exclusions'] = ['unresolved_source_rows']
    c['path_exchange_timestamp_regression_exceeded_count'] = 1
    if damage == 'loss': c['writer_dropped_envelope_count'] = 1
    if damage == 'pending': c['collector_active_callback_count'] = 1
    if damage == 'persistence': c['writer_persisted_envelope_count'] += 1
    if damage == 'authority': c['actual_order_submitted'] = True
    closed = {**payload, 'source_date': receipt.name[:10]}
    if damage == 'date': closed['source_date'] = '2099-01-01'
    latest.write_text(json.dumps(payload)); receipt.write_text(json.dumps(closed))
    if damage == 'changed_guard':
        closed['canary_guard'] = {**payload['canary_guard'], 'extra': 'changed'}
        receipt.write_text(json.dumps(closed))
    pin = dict(path=str(latest), pid=c['process_pid'], start_ticks=c['process_start_ticks'],
               sequence_epoch=c['sequence_epoch'], enqueued_count=1)
    assert not main_raw_epoch_validation(closed, source_date=receipt.name[:10])['eligible']
    before = receipt.read_bytes()
    if damage:
        with pytest.raises(ValueError): D.verify_collector_shutdown(pin)
    else:
        checked = D.verify_collector_shutdown(pin)
        assert checked['status'] == 'verified'
        assert checked['native_source_validation'][0]['eligible'] is False
        assert checked['source_admission'] == 'native_semantics_unchanged'
    assert receipt.read_bytes() == before


@pytest.mark.parametrize('damage', [None, 'selector', 'hold', 'collector', 'closure', 'source_after_preflight', 'prestart_current', 'poststart_current', 'poststart_closed'])
def test_drained_preselection_recovery_keeps_original_selector_and_failed_evidence(stopped_recovery, monkeypatch, damage):
    d, status_path, policy = stopped_recovery
    prior_path = status_path.with_name('selection-before.json')
    prior = D.H._read(prior_path)
    prior.update(approved_by='user', approval_scope='ordered_intraday_deploy_and_restart')
    prior_path.write_bytes(D._json_bytes(prior)); d.selection.write_bytes(prior_path.read_bytes())
    monkeypatch.setattr(D.R, 'selected_release', lambda *a: (Path(prior['release_root']), prior['git_commit']))
    _candidate_p5_fixture(d, 'c' * 40)
    failed = D.H._read(status_path)
    collector = d.workspace / 'data/runtime/scalp_micro_reversion_forward_collector/latest.json'
    collector.parent.mkdir(); collector.write_text('{}')
    closed = collector.parent / 'closed.json'; closed.write_text('{"closed":true}')
    failed.update(failed_phase='draining', error='deployment_collector_closed_epoch_invalid',
                  original_selection_sha256=D._digest(prior_path.read_bytes()),
                  collector_shutdown_pin=dict(path=str(collector), pid=failed['predecessor_identity']['pid'],
                    start_ticks=failed['predecessor_identity']['start_ticks']))
    status_path.write_bytes(D._json_bytes(failed))
    proof = status_path.with_name('preflight-intraday_release_handoff.log'); proof.write_text('verified actual prior consumption')
    monkeypatch.setattr(D, '_stopped_intraday_predecessor', lambda *a: dict(
        path=str(proof), sha256=D.H._sha(proof), frozen_files={str(policy):D.H._sha(policy)}))
    def closure(pin):
        if damage == 'closure': raise ValueError('native closure invalid')
        return dict(status='verified', receipts=[dict(path=str(closed),sha256=D.H._sha(closed))])
    monkeypatch.setattr(D,'verify_collector_shutdown',closure)
    if damage == 'selector': d.selection.write_bytes(d.selection.read_bytes()+b' ')
    if damage == 'hold':
        hold=D.H._read(d.hold);hold['old_pid_identity']['start_ticks']='foreign';d.hold.write_bytes(D._json_bytes(hold))
    if damage == 'collector':
        failed['collector_shutdown_pin']['pid']+=1;status_path.write_bytes(D._json_bytes(failed))
    original = {p:p.read_bytes() for p in (d.selection, d.hold, status_path, prior_path)}
    if damage in {'selector', 'hold', 'collector', 'closure'}:
        with pytest.raises(ValueError):d.preflight()
        assert all(p.read_bytes()==raw for p,raw in original.items())
        return
    d.preflight()
    if damage == 'source_after_preflight':
        collector.write_text('{"changed":true}')
        with pytest.raises(ValueError):d.acquire_hold()
        assert d.hold.read_bytes()==original[d.hold]
        return
    d.acquire_hold();d.drain();d.publish()
    assert D.H._read(d.selection)['previous_git_commit']==prior['git_commit']
    assert status_path.read_bytes()==original[status_path]
    assert prior_path.read_bytes()==original[prior_path]
    assert not hasattr(d,'native_path')
    d.checkpoint('prepared')
    if damage == 'prestart_current':
        collector.write_text('{"unowned_writer":true}')
        with pytest.raises(ValueError, match='stopped_collector_changed_before_start'):
            d.start()
        assert d.hold.exists()
        return
    identity = dict(pid=456, start_ticks='567', cwd=str(d.candidate / 'src'))
    def launch(plan):
        selected = D.H._read(d.selection)
        selected.update(actual_pid_consumed=True, actual_pid_receipt={'pid':456})
        d.selection.write_bytes(D._json_bytes(selected))
        if damage == 'poststart_current': collector.write_text('{"new_epoch":true}')
        if damage == 'poststart_closed': closed.write_text('{"tampered":true}')
        monkeypatch.setattr(D, '_main_pids', lambda:[456])
    monkeypatch.setattr(D.R, 'make_plan', lambda *a:dict(command=['/usr/bin/env python bot_main.py']))
    monkeypatch.setattr(D, '_launch', launch)
    monkeypatch.setattr(D.H, '_identity', lambda pid:identity)
    monkeypatch.setattr(d, 'run_json', lambda *a:None)
    d.start()
    if damage == 'poststart_closed':
        with pytest.raises(ValueError, match='original_policy_generation_changed'):d.attest()
    else:
        assert d.attest()['status']=='pass'
    assert status_path.read_bytes()==original[status_path]


@pytest.mark.parametrize('fault', [None, 'parent', 'old_proof', 'old_sources', 'current_pid'])
def test_live_failed_collector_pointer_recovery_requires_both_consumed_generations(driver, monkeypatch, fault):
    d=driver
    _,failed,path,_=_failed_hold_fixture(d,monkeypatch)
    failed.update(error='deployment_original_policy_generation_changed', failed_hold_adoption=dict(
        source_failure='deployment_collector_closed_epoch_invalid',intraday_predecessor_proof_sha256='oldproof'))
    policy=d.workspace/'old-policy.json';policy.write_text('unchanged')
    if fault=='parent':failed['failed_hold_adoption']['source_failure']='unreviewed_failure'
    path.write_bytes(D._json_bytes(failed))
    def native(*args):
        if fault=='old_sources':raise ValueError('old policy changed')
        return dict(sha256='changed' if fault=='old_proof' else 'oldproof',frozen_files={str(policy):D.H._sha(policy)})
    monkeypatch.setattr(D,'_stopped_intraday_predecessor',native)
    if fault=='current_pid':monkeypatch.setattr(D,'_main_pids',lambda:[])
    before=d.hold.read_bytes(),path.read_bytes()
    if fault:
        with pytest.raises(ValueError):d.capture_failed_hold_adoption()
    else:
        d.capture_failed_hold_adoption()
        assert d.state['failed_hold_adoption']['source_failure']==failed['error']
        assert d.frozen[str(policy)]==D.H._sha(policy)
    assert (d.hold.read_bytes(),path.read_bytes())==before


@pytest.mark.parametrize("phase", ["candidate", "selected_prepared", "actual_pid"])
@pytest.mark.parametrize("damage", [None, "code", "registry", "role", "plan"])
def test_deployment_uses_same_report_census_without_promoting_source_gaps(tmp_path, monkeypatch, phase, damage):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    baseline = [dict(family="auxiliary", role="report_only", source_date="2026-10-26", code_sha256="a" * 64, validation_plan_sha256="c" * 64,
                     observation=dict(status="unverified", findings=["policy_generation_unverified"]))]
    current = json.loads(json.dumps(baseline))
    if damage == "code":
        current[0]["code_sha256"] = "b" * 64
    elif damage == "registry":
        current.clear()
    elif damage == "role":
        current[0]["role"] = "startup_required"
    elif damage == "plan":
        current[0]["validation_plan_sha256"] = "d" * 64
    elif phase != "candidate":
        current[0]["observation"]["findings"] = ["historical_cost_source_gap"]
    calls = []
    def observe(root, day, *, data_root):
        calls.append((root, day, data_root))
        return current
    monkeypatch.setattr(handoff, "consumer_inventory", observe)
    d = object.__new__(D.Deployment)
    d.workspace, d.candidate = tmp_path, tmp_path / "candidate"
    d.state = dict(candidate_report_currentness=dict(source_date="2026-10-26", capability_consumers=baseline))
    if damage:
        with pytest.raises(ValueError, match="deployment_report_consumer_identity_changed"):
            d.observe_report_consumers(phase)
        assert "report_consumer_observations" not in d.state
    else:
        d.observe_report_consumers(phase)
        assert d.state["report_consumer_observations"][phase] == current
        assert current[0]["role"] == "report_only"
    assert calls == [(d.candidate, "2026-10-26", tmp_path / "data")]


@pytest.mark.parametrize("changed", [False, True])
def test_operator_incident_hold_transfers_only_exact_preflight_bytes(driver, monkeypatch, changed):
    d = driver
    d.operator_hold_sha256 = "a" * 64
    d._preflight_native_verified = True
    raw = D._json_bytes(dict(schema="operator_incident_startup_hold_v1", active=True))
    d.hold.write_bytes(raw)
    _, original, signature = D._owned_metadata(d.hold)
    d.operator_hold_sha256 = D._digest(original)
    (d.workspace / "data/runtime/runtime_release_selection.lock").touch()
    d.operator_hold_adoption = dict(raw=original, signature=signature)
    d.state["operator_hold_adoption"] = dict(transfer_status="verified_not_transferred")
    monkeypatch.setattr(d, "assert_unchanged", lambda: None)
    if changed:
        d.hold.write_bytes(raw + b" ")
        with pytest.raises(ValueError):
            d.acquire_hold()
        assert d.hold.read_bytes() == raw + b" "
    else:
        d.acquire_hold()
        assert json.loads(d.hold.read_bytes())["schema"] == "ordered_deployment_startup_hold_v1"
        assert d.state["operator_hold_adoption"]["transfer_status"] == "transferred_exact_owned_hold"


def test_operator_incident_hold_cannot_transfer_before_native_preflight(driver):
    d = driver
    d.operator_hold_sha256 = "a" * 64
    d.operator_hold_adoption = None
    d.assert_unchanged = lambda: None
    with pytest.raises(ValueError, match="operator_hold_adoption_unverified"):
        d.acquire_hold()


def test_preflight_rejects_pending_selection_from_another_code_generation(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_cumulative_registration as G
    from src.engine.scalping import continuous_reversal_postclose as P
    day='2026-10-28'
    candidate=Path(D.__file__).resolve().parents[3]
    old=tmp_path/'old'
    selection=tmp_path/'data/runtime/runtime_release_selection.json'
    selection.parent.mkdir(parents=True)
    selection.write_text('{}')
    monkeypatch.setattr(D.R,'selected_release',lambda *_:(old,'a'*40))
    monkeypatch.setattr(D.R,'validate_release',lambda *a:(candidate,'b'*40))
    monkeypatch.setattr(D.R,'git',lambda *a:'b'*40)
    monkeypatch.setattr(G,'_validate_scoring_intent',lambda value:value)
    P.write(G.scoring_intent_path(tmp_path/'data'),dict(publication_date=day,
        contract_file_sha256={'old.py':'a'*64},preparation_reader_code_sha256='a'*64))
    driver=object.__new__(D.Deployment)
    driver.workspace=tmp_path; driver.candidate=candidate; driver.day=day
    driver.selection=selection; driver.pin_candidate_p5=lambda:None
    # This executes the real preflight before it can create a hold or drain.
    with pytest.raises(ValueError,match='deployment_pending_scoring_code_changed'):
        driver.preflight()
    assert not (tmp_path/'data/runtime/operator_startup_hold.json').exists()
    assert not (tmp_path/'restart.flag').exists()


@pytest.mark.parametrize('change',['appeared','removed','changed'])
def test_prepublication_cas_includes_pending_selection(tmp_path, monkeypatch, change):
    from src.engine.scalping import reversal_cumulative_registration as G
    from src.engine.scalping import continuous_reversal_postclose as P
    day='2026-10-28'; data=tmp_path/'data'
    path=G.scoring_intent_path(data)
    # A different publication still has immutable pending custody to preserve.
    monkeypatch.setattr(G,'_validate_scoring_intent',lambda value:value)
    if change!='appeared':P.write(path,dict(publication_date='2026-10-27'))
    driver=object.__new__(D.Deployment)
    driver.workspace=tmp_path; driver.day=day
    driver.pending_scoring=G.pending_scoring_code_check(data,day)
    driver._assert_failed_transition_unchanged=lambda:None
    if change=='removed':path.unlink()
    else:P.write(path,dict(publication_date='2026-10-27',generation='new'))
    with pytest.raises(ValueError,match='deployment_pending_scoring_changed'):
        driver.assert_unchanged()


@pytest.mark.parametrize('publication', ['2026-10-28','2026-10-29'])
def test_pending_scoring_guard_covers_current_and_future_consumers(tmp_path, monkeypatch, publication):
    from src.engine.scalping import reversal_cumulative_registration as G
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.automation import postclose_summary_handoff as H
    monkeypatch.setattr(G,'_validate_scoring_intent',lambda value:value)
    value=dict(publication_date=publication,
        contract_file_sha256={Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()},
        preparation_reader_code_sha256=P.file_hash(H.__file__))
    path=G.scoring_intent_path(tmp_path)
    P.write(path,value)
    assert G.pending_scoring_code_check(tmp_path,'2026-10-28')['sha256']==P.file_hash(path)
    value['preparation_reader_code_sha256']='a'*64
    P.write(path,value)
    with pytest.raises(ValueError,match='pending_scoring_code_changed'):
        G.pending_scoring_code_check(tmp_path,'2026-10-28')


def test_stopped_recovery_preflight_preserves_pending_selection(stopped_recovery, monkeypatch):
    from src.engine.scalping import reversal_cumulative_registration as G
    from src.engine.scalping import continuous_reversal_postclose as P
    driver,_,_=stopped_recovery
    monkeypatch.setattr(G,'_validate_scoring_intent',lambda value:value)
    P.write(G.scoring_intent_path(driver.workspace/'data'),dict(publication_date=driver.day,
        contract_file_sha256={'old.py':'a'*64},preparation_reader_code_sha256='a'*64))
    before=driver.hold.read_bytes()
    with pytest.raises(ValueError,match='deployment_pending_scoring_code_changed'):
        driver.preflight()
    assert driver.hold.read_bytes()==before


@pytest.mark.parametrize('invalid', [None, 'date', 'not_consumed', 'failed'])
def test_postclose_stop_initial_admission_uses_current_selected_consumer(tmp_path, monkeypatch, invalid):
    from datetime import datetime
    day = '2026-10-29'
    root = Path(D.__file__).resolve().parents[3]
    runtime = tmp_path / 'data/runtime'
    runtime.mkdir(parents=True)
    actor = dict(pid=123, start_ticks='456', cwd=str(root / 'src'))
    (runtime / 'runtime_release_selection.json').write_text(json.dumps(dict(
        release_root=str(root), git_commit='c'*40, actual_pid_consumed=True,
        actual_pid_receipt=dict(pid=123, start_ticks='456'))))
    eod = runtime / 'update_kospi_status' / f'update_kospi_{day}.json'
    eod.parent.mkdir()
    eod.write_text(json.dumps(dict(target_date=day, status='completed',
        finished_at=day+'T20:07:00+09:00',
        db_state=dict(latest_quote_date=day, rows_on_latest_date=10))))
    monkeypatch.setattr(D.R, 'selected_release', lambda workspace: (root, 'c'*40))
    monkeypatch.setattr(D.H, '_identity', lambda pid: actor)
    monkeypatch.setattr(D.H, 'verify_predecessor_consumption', lambda *a, **kw:
        pytest.fail('intraday_predecessor_candidate_already_selected'))
    calls = []
    def consume(target, *, pid):
        assert (target, pid) == (day, 123)
        calls.append('current_consumer')
        return dict(status='fail' if invalid=='failed' else 'pass',
                    target_date='2026-10-28' if invalid=='date' else day,
                    actual_pid_consumed=invalid!='not_consumed')
    monkeypatch.setattr(D.H, 'verify_pid_consumption', consume)
    def pin(workspace, identity):
        assert calls == ['current_consumer'] and identity == actor
        raise RuntimeError('collector boundary reached after valid current consumption')
    monkeypatch.setattr(D, 'pin_collector_shutdown', pin)
    if invalid:
        with pytest.raises(ValueError, match='postclose_stop_policy_consumption_invalid'):
            D.stop_after_eod(tmp_path, day, D.CONFIRM,
                             now=datetime.fromisoformat(day+'T20:10:00+09:00'))
    else:
        with pytest.raises(RuntimeError, match='collector boundary reached'):
            D.stop_after_eod(tmp_path, day, D.CONFIRM,
                             now=datetime.fromisoformat(day+'T20:10:00+09:00'))
    assert calls == ['current_consumer']
    assert not (runtime / 'operator_startup_hold.json').exists()
    assert not (runtime / 'postclose_stop' / day / 'status.json').exists()
    assert not (tmp_path / 'restart.flag').exists()

@pytest.mark.parametrize("damage", [None, "failure", "phase", "hold", "collector", "selector", "new_pid", "p5", "closed"])
def test_interrupted_hold_phase_and_failed_recovery_preserve_native_consumption(
    stopped_recovery, monkeypatch, tmp_path, damage
):
    """Exercise observation before/after native hold, failed adoption and CAS."""
    from datetime import datetime
    from src.engine.error_detectors import artifact_freshness
    from src.engine.scalping import reversal_cumulative_registration as registration

    d, failed_path, policy = stopped_recovery
    day = d.day
    data = tmp_path / "data"
    previous = tmp_path / "old"
    previous.mkdir()
    failed_root = tmp_path / "failed"
    failed_root.mkdir()
    old = "a" * 40
    failed_commit = "b" * 40
    identity = dict(pid=2147483601, start_ticks="123", cwd=str(previous / "src"))
    monkeypatch.setattr(D.H, "DATA_DIR", data)
    monkeypatch.setattr(D.H, "_selection", lambda **kw: (previous, old))
    monkeypatch.setattr(D.H, "_identity", lambda pid: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(artifact_freshness, "_postclose_main_absent", lambda: True)
    monkeypatch.setattr(D.H.bootstrap, "manifest_path", lambda _: data / "manifest.json")
    monkeypatch.setattr(D.H, "_verify_handoff", lambda *a, **kw: {"status": "pass", "handoff": {"frozen_files": {str(policy): D.H._sha(policy)}}})
    monkeypatch.setattr(D.R, "selected_release", lambda _: (previous, old))
    monkeypatch.setattr(registration, "pending_scoring_code_check", lambda *a: {})
    monkeypatch.setattr(D.H, "_checked_bootstrap", lambda *a: {"manifest_sha256": "m" * 64})
    manifest = data / "manifest.json"
    manifest.write_text(json.dumps({"manifest_sha256": "m" * 64}))
    handoff_path, consumed_path = D.H._paths(day, old)
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text("{}")
    consumed_path.write_text(json.dumps(dict(schema="intraday_policy_preserving_consumption_v1", status="pass", target_date=day, selected_release_commit=old, release_root=str(previous), handoff_sha256=D.H._sha(handoff_path), pid_identity=identity, actual_pid_consumed=True, manifest_sha256="m" * 64)))
    prior = dict(schema="runtime_release_selection_v1", workspace=str(tmp_path), release_root=str(previous), git_commit=old, actual_pid_consumed=True, approved_by="user", approval_scope="ordered_intraday_deploy_and_restart", actual_pid_receipt=dict(schema="runtime_release_pid_receipt_v1", pid=identity["pid"], start_ticks=identity["start_ticks"], process_cwd=identity["cwd"], release_root=str(previous), git_commit=old, recorded_at_kst=day+"T09:00:00+09:00"))
    d.selection.write_bytes(D._json_bytes(prior))
    failed_path.with_name("selection-before.json").write_bytes(d.selection.read_bytes())
    heartbeat = tmp_path / "tmp/error_detector_heartbeat.json"
    heartbeat.parent.mkdir()
    heartbeat.write_text(json.dumps(dict(main_loop=dict(pid=identity["pid"], last_beat=day+"T09:01:00+09:00"), ai_circuit=dict(pid=identity["pid"], process_start_ticks="123"), threads=dict(sniper_engine=dict(alive=True, last_beat=day+"T09:01:00+09:00")))))
    collector = data / "runtime/scalp_micro_reversion_forward_collector/latest.json"
    collector.parent.mkdir(parents=True)
    payload = dict(schema="scalp_micro_reversion_canary_monitor_v1", generated_at=day+"T09:01:00+09:00", collector_snapshot=dict(process_pid=identity["pid"], process_start_ticks="123", source_contract="main_market_source_v1", collector_lifecycle="running", sequence_epoch=123))
    collector.write_text(json.dumps(payload))
    monkeypatch.setattr(D.H, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: datetime.fromisoformat(day+"T10:00:00+09:00"))}))
    d.hold.unlink()
    observation = D.H.closed_consumption_observation(day)
    closed = dict(schema="intraday_closed_predecessor_verification_v1", basis="closed_intraday", status="pass", target_date=day, selected_release_commit=old, release_root=str(previous), pid_identity=identity, closed_observation=observation, manifest_sha256="m"*64, historical_consumption_verified=True, actual_pid_consumed=False, runtime_effect=False)
    pin = dict(path=str(collector), sha256=D.H._sha(collector), pid=identity["pid"], start_ticks="123", sequence_epoch=123, basis="interrupted_consumed_process", source_admission="unverified_interrupted_epoch", terminal_verified=False, original_collector_receipt=payload, historical_consumption=observation)
    failed_path.with_name("closed-predecessor.json").write_bytes(D._json_bytes(closed))
    failed_path.with_name("interrupted-collector-original.json").write_bytes(collector.read_bytes())
    failed_path.with_name("interrupted-heartbeat-original.json").write_bytes(heartbeat.read_bytes())
    original_candidate = d.candidate
    d.candidate = failed_root
    p5_path = _candidate_p5_fixture(d, failed_commit)
    moved = p5_path.parent.with_name("e" * 32)
    p5_path.parent.rename(moved)
    p5_path = moved / "final.json"
    p5_value = json.loads(p5_path.read_bytes())
    p5_value["run_id"] = moved.name
    p5_path.write_bytes(D._json_bytes(p5_value))
    failed_p5 = D.verify_candidate_p5(tmp_path, day, failed_root, failed_commit, p5_path, D.H._sha(p5_path), prior)
    d.candidate = original_candidate
    _candidate_p5_fixture(d, "c"*40)
    status = dict(schema="ordered_intraday_deployment_v1", authority=D.CONFIRM, target_date=day, candidate_commit=failed_commit, candidate_root=str(failed_root), previous_commit=old, previous_root=str(previous), predecessor_identity=identity, predecessor_launcher=dict(pid=None, start_ticks=None), phase="startup_held", policy_effect="unchanged", original_selection_sha256=D._digest(d.selection.read_bytes()), candidate_p5=failed_p5, closed_predecessor=closed, interrupted_collector=pin)
    failed_path.write_bytes(D._json_bytes(status))
    d.hold.write_bytes(D._json_bytes(dict(schema="ordered_deployment_startup_hold_v1", authority=D.CONFIRM, transition=str(failed_path), target_date=day, candidate_commit=failed_commit, old_pid_identity=identity)))
    assert D.H.closed_consumption_observation(day, owned_interrupted_transition=failed_path) == observation
    assert D.verify_collector_shutdown(pin, owned_interrupted_transition=failed_path)["status"] == "preserved_unverified"
    status.update(phase="failed", status="fail", failed_phase="startup_held", error="deployment_stopped_recovery_source_invalid")
    if damage == "failure": status["error"] = "other"
    if damage == "phase": status["failed_phase"] = "draining"
    if damage == "closed": status["closed_predecessor"]["pid_identity"]["pid"] += 1
    failed_path.write_bytes(D._json_bytes(status))
    if damage == "hold": d.hold.write_text("{}")
    if damage == "collector": collector.write_text("{}")
    if damage == "selector": d.selection.write_text("{}")
    if damage == "p5": p5_path.write_text("{}")
    if damage == "new_pid": monkeypatch.setattr(D, "_main_pids", lambda: [7])
    if damage:
        with pytest.raises((ValueError, OSError, KeyError)):
            d.inspect_stopped_origin()
        return
    assert D.H.closed_consumption_observation(day) == observation
    origin = d.inspect_stopped_origin()
    assert origin["interrupted_observation"] == observation
    before = failed_path.read_bytes(), d.hold.read_bytes(), d.selection.read_bytes()
    d.preflight()
    assert str(collector) not in d.frozen and str(heartbeat) not in d.frozen
    assert d.stopped_collector_source == {
        str(collector): D.H._sha(collector), str(heartbeat): D.H._sha(heartbeat)
    }
    assert (failed_path.read_bytes(), d.hold.read_bytes(), d.selection.read_bytes()) == before
    d.acquire_hold()
    assert d.hold.read_bytes() != before[1]
    assert failed_path.read_bytes() == before[0] and d.selection.read_bytes() == before[2]
    d.drain()
    assert d.phase == "drained" and d.selection.read_bytes() == before[2]
    assert failed_path.read_bytes() == before[0]
    monkeypatch.setattr(D, "_predecessor_observer", lambda *a: {})
    monkeypatch.setattr(D, "inherit_prepared_delay_code", lambda *a: None)
    d.publish()
    assert d.phase == "selected" and failed_path.read_bytes() == before[0]
    preserved = D.verify_interrupted_transition_hold(
        tmp_path, day, identity, failed_path, adopted_transition=d.directory / "status.json"
    )
    assert preserved["observation"] == observation
    assert str(d.selection) not in preserved["sources"]
    assert str(collector) not in preserved["sources"] and str(heartbeat) not in preserved["sources"]
    assert preserved["sources"][str(failed_path)] == D.H._sha(failed_path)
    assert preserved["sources"][str(failed_path.with_name("selection-before.json"))] == observation["selection_sha256"]
    collector.write_text("tampered")
    with pytest.raises(ValueError, match="deployment_interrupted_original_changed"):
        D.verify_interrupted_transition_hold(
            tmp_path, day, identity, failed_path, adopted_transition=d.directory / "status.json"
        )
    d.phase = "prepared"
    with pytest.raises(ValueError, match="deployment_stopped_collector_changed_before_start"):
        d.start()
    heartbeat.write_text("new successor heartbeat")
    successor = dict(pid=2147483603, start_ticks="456", cwd=str(d.candidate / "src"))
    selected = json.loads(d.selection.read_bytes())
    selected.update(actual_pid_consumed=True, actual_pid_receipt={"pid": successor["pid"]})
    d.selection.write_bytes(D._json_bytes(selected))
    monkeypatch.setattr(D.H, "_identity", lambda pid: successor)
    monkeypatch.setattr(D, "_main_pids", lambda: [successor["pid"]])
    monkeypatch.setattr(d, "run_json", lambda *a, **kw: {"status": "pass"})
    monkeypatch.setattr(d, "observe_report_consumers", lambda *_: None)
    d.phase = "starting"
    assert d.attest()["status"] == "pass"

@pytest.mark.parametrize("damage", [None, "parent", "old_status", "proof", "p5", "current_pid", "no_advance", "unbound", "foreign_hold"])
def test_live_interrupted_custody_failure_admits_exact_owned_hold(driver, monkeypatch, damage):
    d = driver
    hold, failed, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    prior = json.loads(prior_path.read_bytes())
    old_identity = hold["old_pid_identity"]
    origin = d.workspace / "data/runtime/release_transitions" / d.day / ("d"*40) / "status.json"
    origin.parent.mkdir(parents=True)
    collector = d.workspace / "data/runtime/collector-latest.json"
    heartbeat = d.workspace / "tmp/error_detector_heartbeat.json"
    heartbeat.parent.mkdir()
    collector.write_text("new collector")
    heartbeat.write_text("new heartbeat")
    observation = dict(basis="interrupted_consumed_process", collector_path=str(collector), source_hashes={str(collector): D._digest(b"old collector"), str(heartbeat): D._digest(b"old heartbeat")})
    proof = dict(closed_observation=observation)
    proof_path = origin.with_name("closed-predecessor.json")
    proof_path.write_bytes(D._json_bytes(proof))
    original = dict(phase="failed", status="fail", failed_phase="startup_held", error="deployment_stopped_recovery_source_invalid", predecessor_identity=old_identity, closed_predecessor=proof)
    origin.write_bytes(D._json_bytes(original))
    parent = dict(source_failure=original["error"], failed_transition_path=str(origin), failed_transition_sha256=D._digest(origin.read_bytes()), failed_selected_commit="d"*40, transfer_status="transferred_exact_owned_hold", intraday_predecessor_proof_sha256=D._digest(proof_path.read_bytes()))
    p5_dir = d.workspace / "data/report/main_startup_validation" / d.day / ("e"*32)
    p5_dir.mkdir(parents=True)
    p5_path = p5_dir / "final.json"
    p5_path.write_bytes(D._json_bytes(dict(schema="main_policy_load_exit_validation_v1", run_id=p5_dir.name, status="passed", findings=[], target_date=d.day, child_exit_code=0, failure_phase=None, execution_release_root=str(d.previous), execution_release_commit=d.previous_commit, selected_release_root=prior["release_root"], selected_release_commit=prior["git_commit"], child_terminated=True, load_check_passed=True, protected_sources_unchanged=True, runtime_effect=False, allowed_runtime_apply=False, actual_pid_consumed=False)))
    p5 = D.verify_candidate_p5(d.workspace, d.day, d.previous, d.previous_commit, p5_path, D.H._sha(p5_path), prior)
    failed.update(error="deployment_original_policy_generation_changed", failed_hold_adoption=parent, candidate_p5=p5)
    failed_path.write_bytes(D._json_bytes(failed))
    saved = origin.with_name("interrupted-collector-original.json")
    saved.write_text("old collector")
    custody = {str(origin): D.H._sha(origin), str(proof_path): D.H._sha(proof_path), str(saved): D.H._sha(saved)}
    monkeypatch.setattr(D.H, "_verify_handoff", lambda *a: dict(status="pass" if all(D.H._sha(p)==sha for p,sha in custody.items()) else "fail", handoff=dict(interrupted_recovery_custody=dict(failed_transition_path=str(origin), sources=custody))))
    if damage == "parent": parent["source_failure"] = "unreviewed"
    elif damage == "old_status": origin.write_text("{}")
    elif damage == "proof": proof_path.write_text("{}")
    elif damage == "p5": p5_path.write_text("{}")
    elif damage == "current_pid": monkeypatch.setattr(D, "_main_pids", lambda: [])
    elif damage == "no_advance": collector.write_text("old collector"); heartbeat.write_text("old heartbeat")
    elif damage == "unbound": custody[str(collector)] = D.H._sha(collector)
    elif damage == "foreign_hold": d.hold.write_text("{}")
    if damage == "parent": failed_path.write_bytes(D._json_bytes(failed))
    before = d.hold.read_bytes(), failed_path.read_bytes(), d.selection.read_bytes()
    if damage:
        with pytest.raises((ValueError, KeyError, OSError)):
            d.capture_failed_hold_adoption()
        assert (d.hold.read_bytes(), failed_path.read_bytes(), d.selection.read_bytes()) == before
    else:
        d.capture_failed_hold_adoption()
        assert d.hold.read_bytes() == before[0]
        assert str(collector) not in d.frozen and str(heartbeat) not in d.frozen
        assert d.frozen[str(saved)] == D.H._sha(saved)
        d.acquire_hold()
        assert d.hold.read_bytes() != before[0]
        assert failed_path.read_bytes() == before[1] and d.selection.read_bytes() == before[2]

@pytest.mark.parametrize("reject", [False, True])
def test_selected_p5_callback_checks_native_profile_after_real_hold_and_publication(driver, monkeypatch, reject):
    from contextlib import nullcontext
    from src.engine.infrastructure import startup_validation_code_context as C

    d = driver
    d.candidate = Path(D.__file__).resolve().parents[3]
    d.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=d.candidate, text=True).strip()
    _candidate_p5_fixture(d, d.commit)
    old = dict(schema="intraday_closed_consumption_observation_v1", pid_identity=d.identity)
    d.closed_predecessor = dict(closed_observation=old)
    monkeypatch.setattr(D.H, "closed_consumption_observation", lambda *_: old)
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    monkeypatch.setattr(D, "_session_absent", lambda: True)
    monkeypatch.setattr(D, "_predecessor_observer", lambda *a: {})
    monkeypatch.setattr(D, "inherit_prepared_delay_code", lambda *a: None)
    monkeypatch.setattr(D, "_source_database_epoch", lambda *a: nullcontext())
    monkeypatch.setattr(D, "sentinel_preparation_lock", lambda *a: nullcontext())
    monkeypatch.setattr(d, "preflight", lambda: None)
    monkeypatch.setattr(d, "prepare", lambda: d.checkpoint("prepared"))
    calls = []
    monkeypatch.setattr(d, "start", lambda: calls.append("start"))
    monkeypatch.setattr(d, "attest", lambda: {"status": "pass"})
    def selected_p5(driver):
        assert driver.phase == "prepared"
        assert driver.hold.read_bytes() == driver.hold_bytes
        selected = json.loads(driver.selection.read_bytes())
        assert selected["git_commit"] == driver.commit and selected["actual_pid_consumed"] is False
        relative = "src/engine/automation/ordered_intraday_deploy.py"
        old_hash, new_hash = C.REVIEWED_STORAGE_ADMISSION_TRANSITION[relative]
        assert C.reviewed_preparation_pair(relative, old_hash, new_hash, root=driver.candidate)
        if reject: raise ValueError("native selected P5 failed")
    if reject:
        with pytest.raises(ValueError, match="native selected P5 failed"):
            D.execute(d, validate_prepared=selected_p5)
        assert not calls
    else:
        assert D.execute(d, validate_prepared=selected_p5)["status"] == "pass"
        assert calls == ["start"]


@pytest.mark.parametrize("fault", [None, "failed", "wrong_commit", "selection_changed", "live_main", "path", "child_exit", "source_changed"])
def test_cli_selected_p5_uses_native_prepared_generation(driver, monkeypatch, fault):
    from src.engine.automation import main_startup_validation as native

    d = driver
    d.phase = "prepared"
    d.hold_bytes = b"owned hold"
    d.hold.write_bytes(d.hold_bytes)
    d.published = D._json_bytes(dict(release_root=str(d.candidate), git_commit=d.commit))
    d.selection.write_bytes(d.published)
    monkeypatch.setattr(D, "_main_pids", lambda: [999] if fault == "live_main" else [])
    directory = d.workspace / "data/report/main_startup_validation" / d.day / ("a" * 32)
    directory.mkdir(parents=True)
    path = directory / "final.json"
    result = dict(schema="main_policy_load_exit_validation_v1", status="passed",
                  run_id="a" * 32, child_exit_code=0, protected_sources_unchanged=True,
                  failure_phase=None,
                  target_date=d.day, execution_release_root=str(d.candidate),
                  execution_release_commit=d.commit, selected_release_root=str(d.candidate),
                  selected_release_commit=d.commit, findings=[], child_terminated=True,
                  load_check_passed=True, actual_pid_consumed=False,
                  runtime_effect=False, allowed_runtime_apply=False)
    if fault == "failed": result["status"] = "failed"
    if fault == "wrong_commit": result["selected_release_commit"] = "f" * 40
    if fault == "child_exit": result["child_exit_code"] = 1
    if fault == "source_changed": result["protected_sources_unchanged"] = False
    if fault == "path": path = d.workspace / "selected-p5.json"
    path.write_bytes(D._json_bytes(result))
    calls = []
    def run_validation(**kwargs):
        calls.append(kwargs)
        if fault == "selection_changed": d.selection.write_text("{}")
        return result, path
    monkeypatch.setattr(native, "run_validation", run_validation)
    if fault:
        with pytest.raises(ValueError, match="selected_p5_"):
            D.validate_selected_p5(d)
        assert d.hold.read_bytes() == d.hold_bytes
    else:
        D.validate_selected_p5(d)
        assert calls == [dict(workspace=d.workspace, target_date=d.day,
                              execution_root=d.candidate, candidate=False)]
        assert d.state["selected_p5"]["sha256"] == D.H._sha(path)


@pytest.mark.parametrize("fault", [None, "manifest", "pid", "parent", "frozen", "day", "code"])
def test_auxiliary_repair_preflight_binds_exact_incumbent_before_hold(driver, monkeypatch, fault):
    from datetime import datetime
    from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
    from src.engine.scalping import mechanistic_entry_runtime_policy as native

    d = driver
    source = d.workspace / "auxiliary-source.json"
    source.write_text("original source")
    old = {"scope": "old"}
    manifest = dict(prepared_at=datetime.now(D.H.KST).isoformat(), day=d.day,
                    artifact_content_sha256="a" * 64, base_bundle_sha256="b" * 64,
                    expected_parent=None, old_bindings=old, new_bindings={"scope": "new"},
                    source_hashes={str(source): D.H._sha(source)})
    path = d.workspace / "review.json"
    path.write_bytes(D._json_bytes(manifest))
    d.auxiliary_repair_path = path
    d.auxiliary_repair_sha256 = D.H._sha(path)
    consumed = dict(actual_pid_consumed=True, day=d.day, pid_identity=d.identity,
                    release_commit=d.previous_commit, base_bundle_sha256="b" * 64,
                    overlay_sha256=None, code_hashes=auxiliary.code_hashes(), bindings=old)
    if fault == "manifest": d.auxiliary_repair_sha256 = "0" * 64
    if fault == "pid": consumed["pid_identity"] = {**d.identity, "start_ticks": "wrong"}
    if fault == "day": consumed["day"] = "2026-10-11"
    if fault == "code": consumed["code_hashes"] = {}
    if fault == "frozen": d.frozen[str(source)] = "f" * 64
    bundle = dict(bundle_sha256="b" * 64)
    monkeypatch.setattr(native, "load_effective", lambda **kwargs: bundle)
    monkeypatch.setattr(auxiliary, "current", lambda *args, **kwargs: None)
    monkeypatch.setattr(auxiliary, "read", lambda p: manifest if Path(p) == path else consumed)
    monkeypatch.setattr(auxiliary, "prepare_contract_repair", lambda *args, **kwargs:
                        {**manifest, "expected_parent": "other"} if fault == "parent" else manifest)
    monkeypatch.setattr(d, "run_auxiliary_native", lambda operation, body:
                        auxiliary.prepare_contract_repair(d.workspace / "data", bundle)
                        if operation == "prepare" else pytest.fail("preflight mutated native policy"))
    monkeypatch.setattr(auxiliary, "publish_contract_repair", lambda *args, **kwargs: pytest.fail("preflight published"))
    before = d.selection.read_bytes()
    if fault:
        with pytest.raises(ValueError, match="deployment_auxiliary_repair_"):
            d.pin_auxiliary_repair()
        assert not d.hold.exists() and d.selection.read_bytes() == before
    else:
        d.pin_auxiliary_repair()
        assert d.auxiliary_repair == manifest and d.frozen[str(source)] == D.H._sha(source)
        assert not d.hold.exists() and d.selection.read_bytes() == before


def test_auxiliary_repair_refuses_transition_without_selected_p5_before_preflight(driver, monkeypatch):
    driver.auxiliary_repair_path = driver.workspace / "review.json"
    monkeypatch.setattr(driver, "preflight", lambda: pytest.fail("preflight must not run"))
    with pytest.raises(ValueError, match="deployment_auxiliary_repair_selected_p5_required"):
        D.execute(driver)
    assert not driver.hold.exists()


@pytest.mark.parametrize("operation", ["prepare", "publish", "rollback"])
@pytest.mark.parametrize("fault", [None, "origin", "code", "manifest", "selection", "process", "receipt"])
def test_auxiliary_native_original_reader_transfers_exact_bytes(driver, monkeypatch, operation, fault):
    from types import SimpleNamespace
    from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
    from src.engine.scalping import continuous_reversal_postclose as proof

    d = driver
    manifest = proof.seal(dict(schema=auxiliary.CONTRACT_REPAIR_SCHEMA, day=d.day))
    path = d.workspace / "repair.json"
    path.write_bytes(D._json_bytes(manifest))
    d.auxiliary_repair_path, d.auxiliary_repair_sha256 = path, D.H._sha(path)
    if operation != "prepare":
        d.acquire_hold()
        d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    monkeypatch.setattr(D, "_session_absent", lambda: True)
    checked = []
    monkeypatch.setattr(D.R, "validate_release", lambda workspace, value: checked.append(value))
    record = (manifest if operation == "prepare" else proof.seal(dict(schema=auxiliary.SCHEMA, bindings={"scope": "new"})))
    canonical = auxiliary.root(d.workspace / "data") / "generations" / (record["artifact_content_sha256"] + ".json")
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(D._json_bytes(record))
    reference = dict(path=str(canonical), sha256=D.H._sha(canonical))
    value = dict(status="pass", operation=operation, origin_root=str(d.previous),
                 origin_commit=d.previous_commit, code_hashes=auxiliary.code_hashes(),
                 record=record, reference=reference)
    if fault == "origin": value["origin_root"] = str(d.candidate)
    if fault == "code": value["code_hashes"] = {}
    if fault == "receipt": reference["sha256"] = "f" * 64
    def run(args, **kwargs):
        assert args[:3] == [str(d.previous / ".venv/bin/python"), "-B", "-c"]
        compile(args[3], "native_auxiliary_origin", "exec")
        request = json.loads(args[4])
        assert request["operation"] == operation
        assert request["origin_commit"] == d.previous_commit
        assert request["selection_sha256"] == D._digest(d.before)
        assert kwargs["cwd"] == d.previous and kwargs["env"]["PYTHONPATH"] == str(d.previous)
        if fault == "manifest": path.write_text("{}")
        if fault == "selection": d.selection.write_text("{}")
        return SimpleNamespace(returncode=1 if fault == "process" else 0,
                               stdout=json.dumps(value), stderr="")
    monkeypatch.setattr(D.subprocess, "run", run)
    rejected = bool(fault and not (fault == "receipt" and operation == "prepare"))
    if rejected:
        with pytest.raises(ValueError, match="deployment_auxiliary_native_"):
            d.run_auxiliary_native(operation, manifest)
    else:
        assert d.run_auxiliary_native(operation, manifest) == record
        assert len(checked) == 2
        assert all(row["release_root"] == str(d.previous) and row["git_commit"] == d.previous_commit for row in checked)


@pytest.mark.parametrize("selector_failure", [False, True])
def test_auxiliary_repair_publication_is_drained_and_unwinds_before_selection(driver, monkeypatch, selector_failure):
    from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
    from src.engine.scalping import mechanistic_entry_runtime_policy as native

    d = driver
    d.acquire_hold()
    d.phase = "drained"
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.auxiliary_repair = dict(expected_parent=None, artifact_content_sha256="a" * 64,
                              old_bindings={"scope": "old"}, new_bindings={"scope": "new"})
    overlay = dict(artifact_content_sha256="b" * 64, bindings={"scope": "new"},
                   contract_repair_manifest_sha256="a" * 64)
    calls = []
    def publish(data, manifest, **kwargs):
        assert d.phase == "drained" and d.selection.read_bytes() == d.before
        assert d.hold.read_bytes() == d.hold_bytes
        calls.append(("publish", kwargs))
        return overlay
    monkeypatch.setattr(auxiliary, "publish_contract_repair", publish)
    monkeypatch.setattr(native, "load_effective", lambda **kwargs: {"bundle_sha256": "c" * 64})
    monkeypatch.setattr(auxiliary, "current", lambda *args, **kwargs: overlay)
    def rollback(data, **kwargs):
        calls.append(("rollback", kwargs))
        return dict(bindings={"scope": "old"}, artifact_content_sha256="d" * 64)
    monkeypatch.setattr(auxiliary, "rollback", rollback)
    monkeypatch.setattr(d, "run_auxiliary_native", lambda operation, manifest:
                        auxiliary.publish_contract_repair(d.workspace / "data", manifest,
                            expected_parent=manifest["expected_parent"], confirm=auxiliary.CONTRACT_REPAIR_AUTHORITY)
                        if operation == "publish" else auxiliary.rollback(d.workspace / "data",
                            expected_parent=overlay["artifact_content_sha256"], reason="ordered_deployment_failed_before_selection",
                            confirm=auxiliary.AUTHORITY))
    if selector_failure:
        original = D._atomic
        def fail_selection(path, raw):
            if Path(path) == d.selection:
                raise OSError("selector write failed")
            return original(path, raw)
        monkeypatch.setattr(D, "_atomic", fail_selection)
        with pytest.raises(OSError, match="selector write failed") as failure:
            d.publish()
        d.fail(failure.value)
        assert d.selection.read_bytes() == d.before
        assert d.state["auxiliary_repair_unwind"]["status"] == "rolled_back"
        assert [name for name, _ in calls] == ["publish", "rollback"]
        assert calls[-1][1]["expected_parent"] == overlay["artifact_content_sha256"]
    else:
        d.publish()
        assert d.phase == "selected" and [name for name, _ in calls] == ["publish"]
        assert d.state["auxiliary_repair_published"] == overlay["artifact_content_sha256"]


@pytest.mark.parametrize("fault", [None, "pid", "binding", "overlay", "release", "day", "code"])
def test_auxiliary_repair_attestation_requires_successor_pid_binding(driver, monkeypatch, fault):
    from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
    from src.engine.scalping import continuous_reversal_postclose as proof

    d = driver
    d.phase = "starting"
    identity = dict(pid=456, start_ticks="456", cwd=str(d.candidate / "src"))
    d.selection.write_text(json.dumps(dict(git_commit=d.commit, actual_pid_consumed=True,
                                           actual_pid_receipt={"pid": 456})))
    monkeypatch.setattr(D.H, "_identity", lambda _: dict(identity))
    monkeypatch.setattr(D, "_main_pids", lambda: [456])
    d.run_json = lambda *args, **kwargs: {"status": "pass"}
    monkeypatch.setattr(d, "observe_report_consumers", lambda *_: None)
    d.auxiliary_repair = dict(base_bundle_sha256="b" * 64, new_bindings={"scope": "new"})
    d.auxiliary_overlay = dict(artifact_content_sha256="c" * 64)
    receipt = dict(schema=auxiliary.SCHEMA, day=d.day, actual_pid_consumed=True, pid_identity=identity,
                   release_commit=d.commit, base_bundle_sha256="b" * 64,
                   overlay_sha256="c" * 64, code_hashes=auxiliary.code_hashes(), bindings={"scope": "new"})
    if fault == "pid": receipt["pid_identity"] = {**identity, "start_ticks": "other"}
    if fault == "binding": receipt["bindings"] = {"scope": "old"}
    if fault == "overlay": receipt["overlay_sha256"] = "d" * 64
    if fault == "release": receipt["release_commit"] = "e" * 40
    if fault == "day": receipt["day"] = "2026-10-11"
    if fault == "code": receipt["code_hashes"] = {}
    path = auxiliary.root(d.workspace / "data") / "consumed" / d.day / "456.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(D._json_bytes(proof.seal(receipt)))
    if fault:
        with pytest.raises(ValueError, match="deployment_auxiliary_repair_pid_consumption_invalid"):
            d.attest()
        assert d.phase != "complete"
    else:
        assert d.attest()["status"] == "pass"
        assert d.state["auxiliary_repair_pid_consumption"]["sha256"] == D.H._sha(path)


@pytest.mark.parametrize("fault", [None, "manifest", "published", "binding", "generation"])
def test_stopped_recovery_inherits_published_auxiliary_without_republication(driver, monkeypatch, fault):
    from src.engine.scalping import reversal_auxiliary_intraday as auxiliary
    from src.engine.scalping import continuous_reversal_postclose as proof
    from src.engine.scalping import mechanistic_entry_runtime_policy as native

    d = driver
    data = d.workspace / "data"
    bundle = dict(bundle_sha256="b" * 64)
    bundle_path = native.root(data) / "generations" / ("b" * 64 + ".json")
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(D._json_bytes(bundle))
    manifest = proof.seal(dict(base_bundle_sha256="b" * 64,
        old_bindings={"scope": "old"}, new_bindings={"scope": "new"}, source_hashes={}))
    path = d.workspace / "native-repair.json"
    path.write_bytes(D._json_bytes(manifest))
    overlay = proof.seal(dict(contract_repair_manifest_sha256=manifest["artifact_content_sha256"],
                             bindings=manifest["new_bindings"]))
    generation = auxiliary.root(data) / "generations" / (overlay["artifact_content_sha256"] + ".json")
    generation.parent.mkdir(parents=True, exist_ok=True)
    generation.write_bytes(D._json_bytes(overlay))
    (auxiliary.root(data) / "current.json").write_bytes(D._json_bytes(overlay))
    previous = dict(auxiliary_repair_published=overlay["artifact_content_sha256"],
        auxiliary_repair_preflight=dict(path=str(path), sha256=D.H._sha(path),
            manifest_sha256=manifest["artifact_content_sha256"]))
    origin = dict(failed=previous, failed_path=d.workspace / "failed.json", failed_raw=b"failed")
    monkeypatch.setattr(native, "validate", lambda *a, **kw: bundle)
    monkeypatch.setattr(auxiliary, "current", lambda *a, **kw: overlay)
    monkeypatch.setattr(auxiliary, "validate_contract_repair_manifest", lambda *a, **kw: None)
    monkeypatch.setattr(d, "run_auxiliary_native", lambda *a: pytest.fail("already published repair must not be issued again"))
    if fault == "manifest": previous["auxiliary_repair_preflight"]["sha256"] = "f" * 64
    if fault == "published": previous["auxiliary_repair_published"] = "f" * 64
    if fault == "binding": overlay = {**overlay, "bindings": {"scope": "wrong"}}
    if fault == "generation": generation.write_bytes(D._json_bytes(proof.seal(dict(bindings={"scope": "other"}))))
    if fault:
        with pytest.raises(ValueError, match="deployment_recovery_auxiliary_"):
            d.inherit_auxiliary_repair(origin, bundle)
    else:
        refs = d.inherit_auxiliary_repair(origin, bundle)
        assert refs[str(generation)] == D.H._sha(generation)
        d.acquire_hold(); d.phase = "drained"
        monkeypatch.setattr(D, "_main_pids", lambda: [])
        d.publish()
        assert d.state["auxiliary_repair_reused"]["overlay_sha256"] == D.H._sha(generation)
        assert "auxiliary_repair_published" not in d.state
        assert d.selection.read_bytes() == d.published


@pytest.mark.parametrize("available", [False, True])
def test_reserved_admission_observes_worker_then_pins_fresh_source(driver, monkeypatch, available):
    d = driver
    lockpath = d.workspace / "tmp/run_buy_funnel_sentinel.lock"
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    original = d.selection.read_bytes()
    calls = []
    epoch = ["before"]
    with lockpath.open("a") as worker:
        fcntl.flock(worker, fcntl.LOCK_EX | fcntl.LOCK_NB)
        def wait(predicate, limit, reason, **kwargs):
            assert limit == 60 and reason == "deployment_sentinel_preparation_owner_busy"
            assert predicate() is False
            if not available:
                raise ValueError(reason)
            epoch[0] = "completed"
            fcntl.flock(worker, fcntl.LOCK_UN)
            assert predicate() is True
        monkeypatch.setattr(D, "_wait", wait)
        def preflight():
            assert epoch[0] == "completed"
            calls.append("preflight")
        monkeypatch.setattr(d, "preflight", preflight)
        for name in ("acquire_hold", "drain", "publish", "prepare", "start"):
            monkeypatch.setattr(d, name, lambda name=name: calls.append(name))
        monkeypatch.setattr(d, "attest", lambda: dict(status="pass"))
        if available:
            assert D.execute(d)["status"] == "pass"
            assert calls[0] == "preflight"
        else:
            with pytest.raises(ValueError, match="deployment_sentinel_preparation_owner_busy"):
                D.execute(d)
            assert calls == []
            assert d.state["failed_phase"] == "preflight"
    assert d.selection.read_bytes() == original
    assert not d.hold.exists()
    with lockpath.open("a") as probe:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_selected_validation_retains_database_epoch_and_releases_producer(driver, monkeypatch):
    from contextlib import contextmanager
    d = driver
    active = [False]
    @contextmanager
    def database(*args):
        active[0] = True
        try:
            yield
        finally:
            active[0] = False
    monkeypatch.setattr(D, "_source_database_epoch", database)
    for name in ("preflight", "acquire_hold", "drain", "publish", "prepare"):
        monkeypatch.setattr(d, name, lambda: None)
    def unowned():
        assert active[0] is True
        with (d.workspace / "tmp/run_buy_funnel_sentinel.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    monkeypatch.setattr(d, "start", unowned)
    monkeypatch.setattr(d, "attest", lambda: dict(status="pass"))
    assert D.execute(d, validate_prepared=lambda _: unowned())["status"] == "pass"
    assert active[0] is False
