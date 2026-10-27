"""Startup automation: policy preservation, launcher admission and PID custody."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from src.engine.automation import intraday_release_handoff as handoff
from src.engine.automation import next_preopen_readiness as readiness

NOW = datetime(2026, 10, 2, 10, 0, tzinfo=ZoneInfo("Asia/Seoul"))
DAY = "2026-10-02"
OLD = "a" * 40
NEW = "b" * 40
NATIVE_SELECTION = handoff._selection


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "main",
        "supervisor",
        "hold",
        "restart",
        "consumed",
        "start_authority",
        "target",
        "transition",
        "p5",
        "parent_missing",
        "successor_origin",
        "selector_during",
        "source_during",
        "midnight_during",
    ],
)
def test_stopped_postclose_review_requires_native_cold_custody(
    tmp_path, monkeypatch, fault, rollover=False
):
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.infrastructure import runtime_release_router as R
    from src.engine.infrastructure import research_release_transition as T
    from src.engine.scalping import reversal_code_handoff as A
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    workspace = tmp_path / "workspace"
    data = workspace / "data"
    root, candidate, prior_root = (
        tmp_path / name for name in ("selected", "candidate", "prior")
    )
    for path in (root, candidate, prior_root):
        path.mkdir()
    observed_day = "2026-10-26" if rollover else "2026-10-25"
    clock = [datetime.fromisoformat(observed_day + "T07:40:00+09:00")]

    class Clock:
        fromisoformat = staticmethod(datetime.fromisoformat)
        @staticmethod
        def now(tz):
            return clock[0]

    monkeypatch.setattr(handoff, "datetime", Clock)
    monkeypatch.setattr(readiness, "datetime", Clock)
    if rollover:
        def recovery(data, target):
            if fault == "recovery_lease":
                raise ValueError("failed_preopen_recovery_lease_invalid")
            assert target == "2026-10-26"
            return dict(target_date=target)
        monkeypatch.setattr(readiness, "require_failed_preopen_recovery", recovery)
    monkeypatch.setattr(handoff, "DATA_DIR", data)
    monkeypatch.setattr(
        handoff,
        "__file__",
        str(candidate / "src/engine/automation/intraday_release_handoff.py"),
    )
    monkeypatch.setattr(R, "selected_release", lambda w: (root, OLD))
    monkeypatch.setattr(R, "git", lambda *a: NEW)
    monkeypatch.setattr(
        R, "validate_release", lambda w, r: (Path(r["release_root"]), r["git_commit"])
    )
    monkeypatch.setattr(D, "_main_pids", lambda: [10] if fault == "main" else [])
    monkeypatch.setattr(D, "_session_absent", lambda: fault != "supervisor")
    selector = data / "runtime/runtime_release_selection.json"

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    prior = dict(release_root=str(prior_root), git_commit="c" * 40)
    write(selector, prior)
    prior_raw = selector.read_bytes()
    transition = T.Transition(workspace, "cold-test")
    p5_path = (
        data / "report/main_startup_validation/2026-10-26" / ("d" * 32) / "final.json"
    )
    write(
        p5_path,
        dict(
            schema="main_policy_load_exit_validation_v1",
            run_id="d" * 32,
            status="failed" if fault == "p5" else "passed",
            findings=[],
            target_date="2026-10-26",
            execution_release_root=str(root),
            execution_release_commit=OLD,
            selected_release_root=str(prior_root),
            selected_release_commit="c" * 40,
            child_exit_code=0,
            failure_phase=None,
            child_terminated=True,
            load_check_passed=True,
            protected_sources_unchanged=True,
            runtime_effect=False,
            actual_pid_consumed=False,
            allowed_runtime_apply=False,
        ),
    )
    selection = dict(
        release_root=str(root),
        git_commit=OLD,
        approved_by="user",
        approval_scope="after_postclose_deploy_for_next_regular_start",
        actual_pid_consumed=fault == "consumed",
        main_start_authorized=fault == "start_authority",
        source_date="2026-10-23",
        next_operating_date="2026-10-26",
        selected_at_kst="2026-10-25T14:55:33+09:00",
        previous_selection_backup=str(
            transition.directory / ("before-" + T.sha(prior_raw) + ".bytes")
        ),
        predecessor_selection_sha256=T.sha(prior_raw),
        previous_git_commit="c" * 40,
        previous_release_root=str(prior_root),
        candidate_p5_path=str(p5_path),
        candidate_p5_sha256=handoff._sha(p5_path),
    )
    raw = json.dumps(selection).encode()
    with transition.owner():
        transition.add(selector, raw)
        transition.execute(
            [lambda: transition.write(selector, raw)], verify=lambda: None
        )
    pointer = N.root(data) / "current.json"
    write(pointer, dict(effective_date="2026-10-23", bundle_sha256="e" * 64))
    if fault in {"hold", "restart"}:
        p = (
            data / "runtime/operator_startup_hold.json"
            if fault == "hold"
            else workspace / "restart.flag"
        )
        p.touch()
    if fault == "transition":
        transition.path.write_bytes(transition.path.read_bytes() + b"broken")
    source = data / "frozen-parent.json"
    write(source, {"native": "source"})
    sources = {str(source): handoff._sha(source)}
    monkeypatch.setattr(
        A,
        "_validated_origin_receipt",
        lambda data, day, code_root, *a: (
            None
            if (fault == "parent_missing" and code_root == candidate)
            or (rollover and day == observed_day and code_root == root)
            else dict(source_hashes=sources)
        ),
    )
    codes = {str(candidate / "code.py"): "f" * 64}
    monkeypatch.setattr(A, "code_hashes", lambda: codes)
    successor = A.path(data, observed_day, NEW, "e" * 64)
    write(
        successor,
        dict(
            origin_root="wrong" if fault == "successor_origin" else str(root),
            origin_commit=OLD,
            origin_selection_sha256=T.sha(raw),
            code_hashes=codes,
            actual_pid_consumed=False,
            activation_date="2026-10-25" if fault == "activation_date" else "2026-10-26",
            source_trading_date="2026-10-23",
        ),
    )
    target = "2026-10-27" if fault == "target" else "2026-10-26"

    def run():
        with handoff.stopped_postclose_review(target) as proof:
            assert proof["source_date"] == "2026-10-23"
            assert proof["target_date"] == observed_day
            assert proof["prepared_target_date"] == "2026-10-26"
            assert proof["actual_pid_consumed"] is False
            review = handoff._PREDECESSOR_REVIEW.get()
            assert handoff.predecessor_review_matches(
                review, observed_day, root, OLD, candidate
            )
            assert not handoff.predecessor_review_matches(
                review, "2026-10-27", root, OLD, candidate
            )
            if fault == "selector_during":
                selector.write_text("{}")
            elif fault == "source_during":
                source.write_text("{}")
            elif fault == "midnight_during":
                clock[0] += timedelta(days=1)

    if fault:
        with pytest.raises((ValueError, json.JSONDecodeError)):
            run()
    else:
        run()
        assert selector.read_bytes() == raw
    assert handoff._PREDECESSOR_REVIEW.get() is None


@pytest.mark.parametrize("fault", [None, "activation_date", "parent_missing", "main", "source_during", "recovery_lease"])
def test_stopped_parent_review_uses_original_issue_and_explicit_successor_activation(
    tmp_path, monkeypatch, fault
):
    test_stopped_postclose_review_requires_native_cold_custody(
        tmp_path, monkeypatch, fault, rollover=True
    )


@pytest.mark.parametrize(
    "name",
    [
        "src/engine/kiwoom_sniper_v2.py",
        "src/engine/scalping/pre_submit_delay_initial_policy.py",
        "src/engine/monitoring/submission_bottleneck_monitor.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/scalping/scanner_async_eval.py",
        "src/engine/ai_engine_openai.py",
        "src/engine/scalping/main_stop_policy.py",
        "src/engine/automation/main_stop_postclose.py",
        "src/engine/automation/runtime_policy_bootstrap.py",
        "src/engine/lifecycle/holding_window_generation.py",
    ],
)
@pytest.mark.parametrize(
    "review_map",
    [
        "REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES",
        "REVIEWED_DELAY_RESEARCH_SOURCES",
        "REVIEWED_POST_AUX_GUARD_SOURCES",
        "REVIEWED_AUXILIARY_PRODUCTION_INPUT_SOURCES",
        "REVIEWED_NONFIXED_QUOTE_DELIVERY_SOURCES",
        "REVIEWED_ENTRY_CONSUMER_SOURCES",
        "REVIEWED_ENTRY_LATENCY_SOURCES",
        "REVIEWED_ENTRY_BOUNDARY_SOURCES",
        "REVIEWED_ENTRY_RESPONSE_SOURCES",
        "REVIEWED_ENTRY_STORAGE_SOURCES",
        "REVIEWED_JOINT_CONSUMER_SOURCES",
        "REVIEWED_REST_REDUCTION_SOURCES",
        "REVIEWED_IO_OBSERVER_SOURCES",
        "REVIEWED_IO_DIGEST_SOURCES",
        "REVIEWED_STOP_CONSUMER_SOURCES",
        "REVIEWED_NONFIXED_SUBMIT_SOURCES",
        "REVIEWED_SUBMISSION_TIMEOUT_SOURCES",
        "REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES",
        "REVIEWED_PREMARKET_OBSERVER_SOURCES",
        "REVIEWED_ACTIVE_OBSERVER_SOURCES",
        "REVIEWED_CURRENT_OBSERVER_SOURCES",
        "REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES",
        "REVIEWED_OBSERVER_STATE_READER_SOURCES",
        "REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES",
        "REVIEWED_NATIVE_FEATURE_GAP_OBSERVER_SOURCES",
        "REVIEWED_HOLDING_CONTEXT_SNAPSHOT_SOURCES",
        "REVIEWED_STOP_VOTE_SNAPSHOT_SOURCES",
        "REVIEWED_ORDERED_PUBLICATION_SOURCES",
        "REVIEWED_OPPORTUNITY_CUSTODY_SOURCES",
        "REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES",
        "REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES",
        "REVIEWED_TERMINAL_CLOCK_CUSTODY_SOURCES",
        "REVIEWED_NATIVE_ARM_COMPLETION_SOURCES",
        "REVIEWED_CARRIED_SOURCE_BINDING_SOURCES",
        "REVIEWED_HOLDING_CONTRACT_SOURCES",
        "REVIEWED_POSTCLOSE_READ_SOURCES",
        "REVIEWED_CARRIED_VOTE_PREFIX_SOURCES",
        "REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES",
        "REVIEWED_PREASSESSMENT_OBSERVER_SOURCES",
        "REVIEWED_PROBE_PARTIAL_INTEGRATION_SOURCES",
        "REVIEWED_LONG4_SOURCE_RETENTION_SOURCES",
        "REVIEWED_DELAY_SITUATION_SOURCES",
        "REVIEWED_NONFIXED_CONTINUITY_SOURCES",
        "REVIEWED_CURSOR_ASOF_SOURCES",
    ],
)
@pytest.mark.parametrize("damage", [None, "after", "before", "dirty", "origin_digest"])
def test_reviewed_consumer_source_pair_is_exact_and_read_only(
    tmp_path, monkeypatch, damage, name, review_map
):
    import hashlib

    own = "src/engine/automation/intraday_release_handoff.py"
    before, after = b"def runtime(): return 1\n", b"def runtime(): return 2\n"
    pair = (hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest())
    monkeypatch.setattr(handoff, "REVIEWED_DELAY_RESEARCH_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_POST_AUX_GUARD_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_AUXILIARY_PRODUCTION_INPUT_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_NONFIXED_QUOTE_DELIVERY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ENTRY_CONSUMER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_PROBE_PARTIAL_INTEGRATION_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_LONG4_SOURCE_RETENTION_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ENTRY_LATENCY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ENTRY_BOUNDARY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ENTRY_RESPONSE_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ENTRY_STORAGE_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_JOINT_CONSUMER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_REST_REDUCTION_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_IO_OBSERVER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_IO_DIGEST_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_STOP_CONSUMER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_NONFIXED_SUBMIT_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_SUBMISSION_TIMEOUT_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_PREMARKET_OBSERVER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ACTIVE_OBSERVER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_CURRENT_OBSERVER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_OBSERVER_STATE_READER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_NATIVE_FEATURE_GAP_OBSERVER_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_HOLDING_CONTEXT_SNAPSHOT_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_STOP_VOTE_SNAPSHOT_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ORDERED_PUBLICATION_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_OPPORTUNITY_CUSTODY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_TERMINAL_CLOCK_CUSTODY_SOURCES", {})
    monkeypatch.setattr(handoff, "REVIEWED_NATIVE_ARM_COMPLETION_SOURCES", {})
    monkeypatch.setattr(handoff, review_map, {name: pair})
    expected = hashlib.sha256(
        json.dumps({name: pair[0]}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if damage == "before":
        before += b"# altered baseline\n"
    if damage == "after":
        after += b"# unreviewed successor\n"
    for path, body in ((name, after), (own, b"# verified verifier\n")):
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda command, **kw: (
            b"# verified verifier\n"
            if command[-1].endswith(":" + own)
            else before if command[-1].startswith(OLD + ":") else after
        ),
    )
    if damage == "dirty":
        (tmp_path / name).write_bytes(after + b"# dirty\n")
    if damage == "origin_digest":
        expected = "0" * 64
    frozen = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    if damage:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(tmp_path, NEW, OLD, {name: name}, expected)
    else:
        assert handoff._verify_entry_code_delta(
            tmp_path, NEW, OLD, {name: name}, expected
        ) == [name]
    assert frozen == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


@pytest.mark.parametrize("declared", [False, True])
@pytest.mark.parametrize("fault", ["missing", "symlink", "parent_symlink", "directory"])
def test_detector_profile_discovery_does_not_relax_declared_source_checks(
    tmp_path, monkeypatch, declared, fault
):
    import hashlib

    own = "src/engine/automation/intraday_release_handoff.py"
    detector = "src/engine/error_detectors/artifact_freshness.py"
    independent = "src/utils/numeric.py"
    content = b"# unchanged verified source\n"
    for name in (own, independent):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    if fault == "symlink":
        path = tmp_path / detector
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(tmp_path / "absent-detector")
    elif fault == "parent_symlink":
        (tmp_path / detector).parent.symlink_to(
            tmp_path / "absent-directory", target_is_directory=True
        )
    elif fault == "directory":
        (tmp_path / detector).mkdir(parents=True)
    monkeypatch.setattr(handoff.subprocess, "check_output", lambda *_a, **_kw: content)
    paths = {
        name: name for name in ([independent, detector] if declared else [independent])
    }
    expected = hashlib.sha256(
        json.dumps(
            {name: hashlib.sha256(content).hexdigest() for name in paths},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    if declared or fault != "missing":
        reason = "symlink" if "symlink" in fault else "missing"
        with pytest.raises(ValueError, match="entry_consumer_code_source_" + reason):
            handoff._verify_entry_code_delta(tmp_path, NEW, OLD, paths, expected)
    else:
        assert (
            handoff._verify_entry_code_delta(tmp_path, NEW, OLD, paths, expected) == []
        )


@pytest.mark.parametrize(
    "name",
    [
        "src/engine/strategy_position_performance_report.py",
        "src/engine/lifecycle/broker_cost_reconciliation.py",
        "src/engine/monitoring/submission_bottleneck_monitor.py",
    ],
)
@pytest.mark.parametrize(
    "damage", [None, "before", "after", "dirty", "verifier", "origin_digest"]
)
def test_quantity_cost_handoff_requires_exact_original_and_reviewed_sources(
    tmp_path, monkeypatch, name, damage
):
    """Reviewed economic/observer pairs cannot admit unknown or dirty bytes."""
    import hashlib
    import subprocess

    root = Path(handoff.__file__).resolve().parents[3]
    own = "src/engine/automation/intraday_release_handoff.py"
    observer = name == "src/engine/monitoring/submission_bottleneck_monitor.py"
    before = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            (
                "ab1c46633e638658721ec4bdab611bd389451985"
                if observer
                else "7f2552aedde8fec6ef904a43105827907e50dfc8"
            )
            + ":"
            + name,
        ]
    )
    # This exercises the preserved original quantity-cost generation. Current
    # successor source bytes are covered by the complete-generation Git tests.
    after = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            (
                "0ce816f7c1e2c495c24fc11fd4ab0a7d837c56ca"
                if observer
                else "99e158af1c4c743d32662630e0397b58c1f7338e"
            )
            + ":"
            + name,
        ]
    )
    verifier = (root / own).read_bytes()
    pair = (
        handoff.REVIEWED_SOURCE_INTEGRATION_PAIRS[name][0]
        if observer
        else handoff.REVIEWED_QUANTITY_RESEARCH_COST_SOURCES[name]
    )
    assert pair == (
        hashlib.sha256(before).hexdigest(),
        hashlib.sha256(after).hexdigest(),
    )
    expected = hashlib.sha256(
        json.dumps({name: pair[0]}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if damage == "before":
        before += b"\n# unreviewed origin\n"
    if damage == "after":
        after += b"\n# unreviewed successor\n"
    for relative, body in ((name, after), (own, verifier)):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    def revision(command, **_kwargs):
        if command[-1].endswith(":" + own):
            return verifier
        return before if command[-1].startswith(OLD + ":") else after

    monkeypatch.setattr(handoff.subprocess, "check_output", revision)
    if damage == "dirty":
        (tmp_path / name).write_bytes(after + b"\n# uncommitted source\n")
    if damage == "verifier":
        (tmp_path / own).write_bytes(verifier + b"\n# uncommitted verifier\n")
    if damage == "origin_digest":
        expected = "0" * 64
    frozen = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    if damage:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(tmp_path, NEW, OLD, {name: name}, expected)
    else:
        assert handoff._verify_entry_code_delta(
            tmp_path, NEW, OLD, {name: name}, expected
        ) == [name]
    assert frozen == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "proof_hash",
        "authority",
        "source",
        "pid",
        "still_alive",
        "selection",
        "outside_transition",
    ],
)
def test_first_native_preopen_can_drain_into_exact_consumed_handoff(
    fixture, monkeypatch, damage
):
    data, previous, selected, _ = fixture
    monkeypatch.setattr(handoff, "_today", lambda *a: NOW)
    manifest = dict(
        selected_release_sha=OLD, target_date=DAY, manifest_sha256="policy-unchanged"
    )
    _json(handoff.bootstrap.manifest_path(DAY), manifest)
    index = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    ref = handoff._read(index)
    receipt = Path(ref["receipt_path"])
    paths = [
        handoff.bootstrap.env_path(DAY),
        handoff.bootstrap.manifest_path(DAY),
        handoff._preopen_path(DAY),
        index,
        receipt,
    ]
    identity = handoff._identity(1)
    original = dict(
        schema="runtime_release_selection_v1",
        actual_pid_consumed=True,
        release_root=str(previous),
        git_commit=OLD,
        actual_pid_receipt={"pid": 1},
    )
    transition = data / "runtime/release_transitions" / DAY / NEW
    before = transition / "selection-before.json"
    _json(before, original)
    proof_path = transition / "native-predecessor.json"
    proof = dict(
        schema="native_preopen_predecessor_v1",
        authority="APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART",
        candidate_commit=NEW,
        verification=dict(
            schema="intraday_pid_consumption_verification_v1",
            status="pass",
            basis="native_preopen",
            actual_pid_consumed=True,
            target_date=DAY,
            selected_release_commit=OLD,
            release_root=str(previous),
            pid_identity=identity,
            manifest_sha256="policy-unchanged",
        ),
        frozen_files={str(p): handoff._sha(p) for p in paths},
        prepared_receipt_path=str(receipt),
        prepared_receipt_sha256=ref["receipt_sha256"],
        selection_before_sha256=handoff._sha(before),
    )
    if damage == "authority":
        proof["authority"] = "unapproved"
    if damage == "pid":
        proof["verification"]["pid_identity"] = dict(identity, pid=99)
    if damage == "selection":
        before.write_text("{}")
    if damage == "outside_transition":
        proof_path = data / "wrong.json"
    _json(proof_path, proof)
    sha = handoff._sha(proof_path)
    if damage == "proof_hash":
        proof_path.write_text(proof_path.read_text() + " ")
    if damage == "source":
        handoff.bootstrap.env_path(DAY).write_text("changed")
    _json(
        data / "runtime/runtime_release_selection.json",
        dict(
            approved_by="user",
            approval_scope="ordered_intraday_deploy_and_restart",
            git_commit=NEW,
            previous_git_commit=OLD,
            previous_release_root=str(previous),
            native_predecessor_path=str(proof_path),
            native_predecessor_sha256=sha,
        ),
    )
    exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda p: damage == "still_alive" if str(p) == "/proc/1" else exists(p),
    )
    before_sources = {str(p): p.read_bytes() for p in paths}
    assert not handoff._paths(DAY, OLD)[0].exists()
    if damage:
        with pytest.raises(ValueError):
            handoff.prepare(
                DAY,
                old_pid=1,
                previous_root=previous,
                confirm=handoff.CONFIRM,
                previous_stopped=True,
            )
        assert not handoff._paths(DAY, NEW)[0].exists()
    else:
        result = handoff.prepare(
            DAY,
            old_pid=1,
            previous_root=previous,
            confirm=handoff.CONFIRM,
            previous_stopped=True,
        )
        assert result["status"] == "pass"
        value = handoff._read(handoff._paths(DAY, NEW)[0])
        assert (
            value["previous_process_state"]
            == "stopped_native_preopen_consumption_verified"
        )
        assert value["old_pid_identity"] == identity
        assert value["frozen_files"][str(proof_path)] == sha
        consumed = handoff.consume(DAY, pid=2, now=NOW)
        assert consumed["actual_pid_consumed"] is True
        assert consumed["pid_identity"] == handoff._identity(2)
        proof_path.write_text(proof_path.read_text() + " ")
        assert handoff.verify(DAY, NEW, now=NOW)["status"] == "fail"
    assert handoff._NATIVE_PREDECESSOR.get() is None
    assert handoff._STOPPED_PREPARATION.get() is None
    assert not handoff._paths(DAY, OLD)[1].exists()
    assert before_sources == {str(p): p.read_bytes() for p in paths}


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    data = tmp_path / "workspace/data"
    managed = tmp_path / "workspace-runtime-releases"
    previous, selected = managed / "old", managed / "new"
    previous.mkdir(parents=True)
    selected.mkdir()
    monkeypatch.setattr(handoff, "DATA_DIR", data)
    monkeypatch.setattr(readiness, "DATA_DIR", data)
    monkeypatch.setattr(
        handoff.bootstrap, "BOOTSTRAP_DIR", data / "runtime/policy_bootstrap"
    )
    monkeypatch.setattr(handoff, "_selection", lambda **kwargs: (selected, NEW))
    monkeypatch.setattr(handoff, "is_krx_trading_day", lambda day: day.weekday() < 5)
    monkeypatch.setattr(handoff.bootstrap, "env_path", lambda day: data / f"{day}.env")
    monkeypatch.setattr(
        handoff.bootstrap, "manifest_path", lambda day: data / f"{day}.manifest.json"
    )
    monkeypatch.setattr(
        handoff.bootstrap,
        "verify_bootstrap",
        lambda day, **kwargs: {
            "status": "pass",
            "findings": [],
            "manifest_sha256": "policy-unchanged",
        },
    )
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda command, **kwargs: OLD + "\n" if "rev-parse" in command else "",
    )
    monkeypatch.setattr(
        handoff,
        "_identity",
        lambda pid: {
            "pid": pid,
            "start_ticks": "42",
            "cwd": str((previous if pid == 1 else selected) / "src"),
        },
    )
    _json(
        handoff._preopen_path(DAY),
        {
            "target_date": DAY,
            "status": "succeeded",
            "exit_code": 0,
            "runtime_env_exists": True,
            "selected_release_commit": OLD,
            "updated_at": NOW.isoformat(),
        },
    )
    handoff.bootstrap.env_path(DAY).write_text("export POLICY=unchanged\n")
    _json(handoff.bootstrap.manifest_path(DAY), {"policy": "unchanged"})
    prepared_root = data / "runtime/policy_bootstrap/prepared" / DAY
    receipt = prepared_root / "generation/readiness.json"
    _json(receipt, {"status": "prepared_verified"})
    _json(
        prepared_root / "latest.json",
        {"receipt_path": str(receipt), "receipt_sha256": handoff._sha(receipt)},
    )

    def prepare():
        return handoff.prepare(
            DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM, now=NOW
        )

    return data, previous, selected, prepare


def test_intraday_handoff_preserves_preopen_and_policy_files_then_binds_new_pid(
    fixture,
):
    data, _, _, prepare = fixture
    before = {
        str(path): path.read_bytes() for path in data.rglob("*") if path.is_file()
    }
    assert prepare()["status"] == "pass"
    assert all(Path(path).read_bytes() == content for path, content in before.items())
    result = readiness.verify_preopen_completion(DAY, NEW, now=NOW)
    assert (
        result["status"] == "pass"
        and result["basis"] == "intraday_policy_preserving_handoff"
    )
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    assert consumed["actual_pid_consumed"] is True
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(hours=2))["status"] == "pass"


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "absent",
        "schema",
        "status",
        "pid",
        "start_ticks",
        "cwd",
        "manifest",
        "handoff",
        "date",
        "commit",
        "root",
        "actual",
    ],
)
def test_exact_pid_consumption_verifier_rejects_unbound_receipts(fixture, damage):
    data, _, _, prepare = fixture
    assert prepare()["status"] == "pass"
    receipt = handoff.consume(DAY, pid=2, now=NOW)
    path = handoff._paths(DAY, NEW)[1]
    if damage == "absent":
        path.unlink()
    elif damage:
        keys = {
            "manifest": "manifest_sha256",
            "handoff": "handoff_sha256",
            "date": "target_date",
            "commit": "selected_release_commit",
            "root": "release_root",
            "actual": "actual_pid_consumed",
        }
        if damage in {"pid", "start_ticks", "cwd"}:
            receipt["pid_identity"][damage] = 3 if damage == "pid" else "wrong"
        else:
            receipt[keys.get(damage, damage)] = "wrong"
        _json(path, receipt)
    before = {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}
    result = handoff.verify_pid_consumption(DAY, pid=2, now=NOW)
    assert result["status"] == ("fail" if damage else "pass"), result
    if not damage:
        assert result["pid_identity"] == handoff._identity(2)
        assert result["actual_pid_consumed"] is True
    assert before == {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}


@pytest.mark.parametrize(
    "change", ["identity", "selection", "receipt", "manifest", "preopen", "env"]
)
def test_exact_pid_verifier_rechecks_generation_after_bootstrap(
    fixture, monkeypatch, change
):
    _, _, selected, prepare = fixture
    prepare()
    handoff.consume(DAY, pid=2, now=NOW)
    checked = handoff._checked_bootstrap

    def mutate(day, pid):
        result = checked(day, pid)
        if change == "identity":
            monkeypatch.setattr(
                handoff,
                "_identity",
                lambda pid: dict(pid=pid, start_ticks="43", cwd=str(selected / "src")),
            )
        elif change == "selection":
            monkeypatch.setattr(handoff, "_selection", lambda **kw: (selected, OLD))
        else:
            p = {
                "receipt": handoff._paths(DAY, NEW)[1],
                "manifest": handoff.bootstrap.manifest_path(DAY),
                "env": handoff.bootstrap.env_path(DAY),
                "preopen": handoff._preopen_path(DAY),
            }[change]
            p.write_bytes(p.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(handoff, "_checked_bootstrap", mutate)
    result = handoff.verify_pid_consumption(DAY, pid=2, now=NOW)
    assert result["status"] == "fail"
    assert result["findings"] == ["intraday_consumption_generation_changed"]


@pytest.mark.parametrize("native_commit", [OLD, NEW])
def test_native_preopen_pid_verification_never_substitutes_for_code_handoff(
    fixture, native_commit
):
    data, _, _, _ = fixture
    status = handoff._read(handoff._preopen_path(DAY))
    _json(
        handoff._preopen_path(DAY), dict(status, selected_release_commit=native_commit)
    )
    before = {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}
    result = handoff.verify_pid_consumption(DAY, pid=2, now=NOW)
    assert result["status"] == ("pass" if native_commit == NEW else "fail")
    assert before == {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}


def test_verify_cli_with_pid_uses_consumption_contract(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        handoff,
        "verify_pid_consumption",
        lambda day, **kw: calls.append((day, kw["pid"]))
        or dict(status="fail", findings=["missing"]),
    )
    assert handoff.main(["--verify", "--target-date", DAY, "--pid", "2"]) == 1
    assert calls == [(DAY, 2)]
    assert json.loads(capsys.readouterr().out)["findings"] == ["missing"]


@pytest.mark.parametrize("damage", [None, "alive", "wrong_pid", "changed_consumption"])
def test_stopped_handoff_requires_prior_exact_consumption(fixture, monkeypatch, damage):
    data, _, selected, prepare = fixture
    assert prepare()["status"] == "pass"
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    successor = selected.parent / "successor"
    successor.mkdir()
    commit = "c" * 40
    monkeypatch.setattr(handoff, "_selection", lambda **kw: (successor, commit))
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda command, **kw: NEW + "\n" if "rev-parse" in command else "",
    )
    exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda p: damage == "alive" if str(p) == "/proc/2" else exists(p),
    )
    if damage == "wrong_pid":
        consumed["pid_identity"]["pid"] = 99
        _json(handoff._paths(DAY, NEW)[1], consumed)
    if damage in {"alive", "wrong_pid"}:
        with pytest.raises(ValueError, match="intraday_"):
            handoff.prepare(
                DAY,
                old_pid=2,
                previous_root=selected,
                confirm=handoff.CONFIRM,
                now=NOW,
                previous_stopped=True,
            )
        return
    result = handoff.prepare(
        DAY,
        old_pid=2,
        previous_root=selected,
        confirm=handoff.CONFIRM,
        now=NOW,
        previous_stopped=True,
    )
    assert result["status"] == "pass", result
    assert result["actual_pid_consumed"] is False
    assert (
        result["handoff"]["previous_process_state"]
        == "stopped_historical_consumption_verified"
    )
    if damage == "changed_consumption":
        _json(handoff._paths(DAY, NEW)[1], dict(consumed, status="changed"))
        assert handoff.verify(DAY, commit, now=NOW)["status"] == "fail"


@pytest.mark.parametrize("freeze", [False, True])
@pytest.mark.parametrize(
    "tamper", ["none", "policy", "controller", "checklist", "snapshot"]
)
def test_intraday_current_document_reseal_preserves_original_preopen_generation(
    fixture, monkeypatch, tamper, freeze
):
    data, previous, _, _ = fixture
    source_day = "2026-10-01"
    index_path = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    index = json.loads(index_path.read_text())
    receipt = Path(index["receipt_path"])
    policies = [dict(family="main", path="/policy.json", sha256="d" * 64)]
    _json(
        receipt,
        dict(
            schema="next_preopen_readiness_v1",
            status="prepared_verified",
            source_date=source_day,
            target_date=DAY,
            actual_pid_consumed=False,
            policy_receipts=policies,
            controller_sha256="a" * 64,
            summary_sha256="b" * 64,
        ),
    )
    _json(
        index_path,
        dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)),
    )
    controller = (
        data
        / "report/postclose_done_controller"
        / f"postclose_done_controller_{source_day}.json"
    )
    summary = (
        data
        / "report/runtime_approval_summary"
        / f"runtime_approval_summary_{source_day}.json"
    )
    checklist = data.parent / "docs/checklists" / f"{DAY}-stage2-todo-checklist.md"
    _json(controller, {"status": "done"})
    _json(summary, {"status": "verified"})
    checklist.parent.mkdir(parents=True)
    checklist.write_text("current owner")
    source = dict(
        controller_path=str(controller),
        controller_sha256=handoff._sha(controller),
        summary_path=str(summary),
        summary_sha256=handoff._sha(summary),
        policy_receipts=(
            [dict(policies[0], sha256="e" * 64)] if tamper == "policy" else policies
        ),
    )
    monkeypatch.setattr(readiness, "_source_receipts", lambda *a, **k: source)
    original = receipt.read_bytes()
    if tamper == "policy":
        with pytest.raises(ValueError, match="policy_generation_changed"):
            handoff.prepare(
                DAY,
                old_pid=1,
                previous_root=previous,
                confirm=handoff.CONFIRM,
                now=NOW,
                reseal_postclose_source=True,
                freeze_operating_checklist=freeze,
            )
        return
    prepared = handoff.prepare(
        DAY,
        old_pid=1,
        previous_root=previous,
        confirm=handoff.CONFIRM,
        now=NOW,
        reseal_postclose_source=True,
        freeze_operating_checklist=freeze,
    )
    assert prepared["status"] == "pass" and receipt.read_bytes() == original
    if tamper == "snapshot" and freeze:
        Path(
            prepared["handoff"]["postclose_source_reseal"]["operating_checklist"][
                "path"
            ]
        ).write_text("changed")
    elif tamper not in {"none", "snapshot"}:
        (controller if tamper == "controller" else checklist).write_text("changed")
    result = handoff.verify(DAY, NEW, now=NOW)
    assert result["status"] == (
        "pass"
        if tamper == "none"
        or (tamper == "checklist" and freeze)
        or (tamper == "snapshot" and not freeze)
        else "fail"
    )
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(days=1))["status"] == "fail"


def test_read_only_selection_does_not_relax_prepare_or_consume_cwd(
    fixture, monkeypatch
):
    data, _, selected, prepare = fixture
    assert prepare()["status"] == "pass"
    assert handoff.consume(DAY, pid=2, now=NOW)["status"] == "pass"
    frozen = {
        str(path): path.read_bytes() for path in data.rglob("*") if path.is_file()
    }
    monkeypatch.setattr(handoff, "_selection", NATIVE_SELECTION)
    monkeypatch.setattr(handoff, "selected_release", lambda workspace: (selected, NEW))
    monkeypatch.chdir(data.parent)
    with pytest.raises(ValueError, match="selected_root_required"):
        prepare()
    with pytest.raises(ValueError, match="selected_root_required"):
        handoff.consume(DAY, pid=2, now=NOW)
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(hours=2))["status"] == "pass"
    assert all(Path(path).read_bytes() == value for path, value in frozen.items())


@pytest.mark.parametrize(
    "damage", [None, "snapshot", "strict", "consumed", "pid", "source"]
)
def test_historical_observer_accepts_consumed_strict_bound_operating_snapshot(
    fixture, monkeypatch, damage
):
    data, previous, selected, _ = fixture
    source_day = "2026-10-01"
    checklist = data.parent / "docs/checklists" / f"{DAY}-stage2-todo-checklist.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text("sealed generation\n")
    strict = data / "report/strict.json"
    _json(
        strict, dict(generation_binding=dict(checklist_sha256=handoff._sha(checklist)))
    )
    controller = (
        data
        / "report/postclose_done_controller"
        / f"postclose_done_controller_{source_day}.json"
    )
    summary = (
        data
        / "report/runtime_approval_summary"
        / f"runtime_approval_summary_{source_day}.json"
    )
    _json(controller, dict(status="done", verification_attempt_path=str(strict)))
    _json(summary, dict(status="verified"))
    index = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    receipt = Path(handoff._read(index)["receipt_path"])
    policies = [dict(family="main", path="/policy.json", sha256="d" * 64)]
    _json(
        receipt,
        dict(
            schema="next_preopen_readiness_v1",
            status="prepared_verified",
            target_date=DAY,
            source_date=source_day,
            actual_pid_consumed=False,
            policy_receipts=policies,
        ),
    )
    _json(index, dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)))
    monkeypatch.setattr(
        readiness,
        "_source_receipts",
        lambda *a, **k: dict(
            controller_path=str(controller),
            controller_sha256=handoff._sha(controller),
            summary_path=str(summary),
            summary_sha256=handoff._sha(summary),
            policy_receipts=policies,
        ),
    )
    assert (
        handoff.prepare(
            DAY,
            old_pid=1,
            previous_root=previous,
            confirm=handoff.CONFIRM,
            now=NOW,
            reseal_postclose_source=True,
            freeze_operating_checklist=True,
        )["status"]
        == "pass"
    )
    assert handoff.consume(DAY, pid=2, now=NOW)["status"] == "pass"
    checklist.write_text("current operational work changed after consumption\n")
    path, consumed = handoff._paths(DAY, NEW)
    snapshot = handoff._read(path)["postclose_source_reseal"]["operating_checklist"]
    if damage == "snapshot":
        Path(snapshot["path"]).write_text("corrupt")
    if damage == "strict":
        _json(strict, dict(generation_binding=dict(checklist_sha256="changed")))
    if damage == "consumed":
        consumed.unlink()
    if damage == "pid":
        monkeypatch.setattr(
            handoff,
            "_identity",
            lambda pid: dict(pid=pid, start_ticks="reused", cwd=str(selected / "src")),
        )
    if damage:
        with pytest.raises(ValueError, match="intraday_observer_"):
            handoff.historical_checklist_for_observer(
                data.parent, DAY if damage == "source" else source_day, now=NOW
            )
    else:
        result = handoff.historical_checklist_for_observer(
            data.parent, source_day, now=NOW
        )
        assert (
            result["path"] == snapshot["path"]
            and result["sha256"] == snapshot["sha256"]
        )
        assert result["pid_identity"]["pid"] == 2
        assert result["runtime_effect"] is result["new_finalization_claimed"] is False


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "status",
        "schema",
        "pid",
        "start_ticks",
        "root",
        "date",
        "commit",
        "not_consumed",
        "handoff",
        "manifest_binding",
        "env",
        "prepared",
    ],
)
def test_second_same_day_handoff_requires_exact_live_predecessor_and_sealed_generation(
    fixture, monkeypatch, damage
):
    data, previous, selected, prepare = fixture
    index_file = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    index = handoff._read(index_file)
    receipt = Path(index["receipt_path"])
    policies = [
        dict(
            family="main",
            path=str(handoff.bootstrap.env_path(DAY)),
            sha256=handoff._sha(handoff.bootstrap.env_path(DAY)),
        )
    ]
    _json(
        receipt,
        dict(
            schema="next_preopen_readiness_v1",
            status="prepared_verified",
            source_date="2026-10-01",
            target_date=DAY,
            actual_pid_consumed=False,
            policy_receipts=policies,
        ),
    )
    _json(index_file, dict(index, receipt_sha256=handoff._sha(receipt)))
    assert prepare()["status"] == "pass"
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    prior_consumed = handoff._paths(DAY, NEW)[1]
    if damage in (
        "status",
        "schema",
        "root",
        "date",
        "commit",
        "not_consumed",
        "handoff",
        "manifest_binding",
    ):
        field, value = {
            "status": ("status", "fail"),
            "schema": ("schema", "wrong"),
            "root": ("release_root", "/wrong"),
            "date": ("target_date", "2026-10-01"),
            "commit": ("selected_release_commit", OLD),
            "not_consumed": ("actual_pid_consumed", False),
            "handoff": ("handoff_sha256", "wrong"),
            "manifest_binding": ("manifest_sha256", "wrong"),
        }[damage]
        _json(prior_consumed, dict(consumed, **{field: value}))
    elif damage in ("pid", "start_ticks"):
        identity = dict(consumed["pid_identity"])
        identity["pid" if damage == "pid" else "start_ticks"] = (
            99 if damage == "pid" else "99"
        )
        _json(prior_consumed, dict(consumed, pid_identity=identity))
    elif damage == "env":
        handoff.bootstrap.env_path(DAY).write_text("changed")
    elif damage == "prepared":
        receipt.write_text(receipt.read_text() + " ")
    new_root = selected.parent / "second"
    new_root.mkdir()
    second_commit = "c" * 40
    monkeypatch.setattr(
        handoff, "_selection", lambda **kwargs: (new_root, second_commit)
    )
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda command, **kwargs: NEW + "\n" if "rev-parse" in command else "",
    )
    monkeypatch.setattr(
        handoff,
        "_identity",
        lambda pid: dict(
            pid=pid,
            start_ticks="42",
            cwd=str((selected if pid == 2 else new_root) / "src"),
        ),
    )
    controller = (
        data
        / "report/postclose_done_controller/postclose_done_controller_2026-10-01.json"
    )
    summary = (
        data
        / "report/runtime_approval_summary/runtime_approval_summary_2026-10-01.json"
    )
    _json(controller, dict(status="done"))
    _json(summary, dict(status="verified"))
    checklist = data.parent / "docs/checklists" / f"{DAY}-stage2-todo-checklist.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text("same current owner")
    calls = []

    def sealed_source(source_day, target, *, generation_only=False):
        # The full dynamic selector cannot consume the second PID before it
        # launches. Reuse its unchanged native whole-chain generation instead.
        assert generation_only is True
        calls.append((source_day, target))
        return dict(
            controller_path=str(controller),
            controller_sha256=handoff._sha(controller),
            summary_path=str(summary),
            summary_sha256=handoff._sha(summary),
            policy_receipts=policies,
        )

    monkeypatch.setattr(readiness, "_source_receipts", sealed_source)
    before = {
        str(path): path.read_bytes()
        for path in (
            receipt,
            index_file,
            handoff.bootstrap.env_path(DAY),
            handoff.bootstrap.manifest_path(DAY),
            handoff._preopen_path(DAY),
        )
    }
    if damage is not None:
        with pytest.raises(ValueError, match="intraday_"):
            handoff.prepare(
                DAY,
                old_pid=2,
                previous_root=selected,
                confirm=handoff.CONFIRM,
                now=NOW + timedelta(minutes=2),
                reseal_postclose_source=True,
            )
        assert not handoff._paths(DAY, second_commit)[0].exists()
        return
    result = handoff.prepare(
        DAY,
        old_pid=2,
        previous_root=selected,
        confirm=handoff.CONFIRM,
        now=NOW + timedelta(minutes=2),
        reseal_postclose_source=True,
    )
    assert result["status"] == "pass" and calls == [("2026-10-01", DAY)]
    assert (
        handoff.consume(DAY, pid=3, now=NOW + timedelta(minutes=3))[
            "actual_pid_consumed"
        ]
        is True
    )
    assert all(Path(path).read_bytes() == content for path, content in before.items())


@pytest.mark.parametrize("damage", [None, "summary", "consumption", "policy"])
def test_resealed_postclose_accepts_actual_new_pid_without_rewriting_original_summary(
    fixture, monkeypatch, damage, prepared=False
):
    from src.engine.automation import postclose_summary_handoff as postclose

    data, previous, selected, _ = fixture
    bootstrap = handoff.bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", data)
    source_day = "2026-10-01"
    original_env = bootstrap.env_path(DAY).read_bytes()
    root = data / "runtime/policy_bootstrap"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        bootstrap, "env_path", lambda day: root / f"runtime_policy_bootstrap_{day}.env"
    )
    monkeypatch.setattr(
        bootstrap,
        "manifest_path",
        lambda day: root / f"runtime_policy_bootstrap_{day}.json",
    )
    bootstrap.env_path(DAY).write_bytes(original_env)
    manifest_file, env_file = bootstrap.manifest_path(DAY), bootstrap.env_path(DAY)
    # Keep real dated manifest/env validation and the native consumed-PID
    # binding; only process identity and the preexisting DONE source fixture
    # are substituted by the surrounding startup fixture.
    manifest = dict(
        target_date=DAY,
        selected_release_sha=OLD,
        source_incumbent_target_date=source_day,
        selected_families=[],
        direct_family_receipts=[],
        env_file=str(env_file),
        env_sha256=handoff._sha(env_file),
    )
    manifest["manifest_sha256"] = bootstrap._digest_json(manifest)
    _json(manifest_file, manifest)
    monkeypatch.setattr(
        bootstrap,
        "verify_bootstrap",
        lambda *a, **k: dict(
            status="pass",
            passed=True,
            findings=[],
            manifest_sha256=manifest["manifest_sha256"],
        ),
    )
    selection_file = data / "runtime/runtime_release_selection.json"
    _json(
        selection_file,
        dict(
            schema="runtime_release_selection_v1",
            git_commit=NEW,
            release_root=str(selected),
        ),
    )
    verification_file = bootstrap.verify_path(DAY)
    verification = dict(
        target_date=DAY,
        status="pass",
        passed=True,
        pid=1,
        pid_passed=True,
        pid_env_available=True,
        manifest_sha256=manifest["manifest_sha256"],
    )
    _json(verification_file, verification)
    controller = (
        data
        / "report/postclose_done_controller"
        / f"postclose_done_controller_{source_day}.json"
    )
    summary_file = (
        data
        / "report/runtime_approval_summary"
        / f"runtime_approval_summary_{source_day}.json"
    )
    _json(controller, dict(status="done"))
    summary = dict(
        date=source_day,
        preopen_consumption_state="verified",
        preopen_consumption_receipt=dict(
            source_date=source_day,
            apply_date=DAY,
            manifest_path=str(manifest_file),
            manifest_sha256=handoff._sha(manifest_file),
            verification_path=str(verification_file),
            verification_sha256=handoff._sha(verification_file),
            release_selection_sha256="old",
            selected_release_commit=OLD,
        ),
    )
    _json(summary_file, summary)
    checklist = data.parent / "docs/checklists" / f"{DAY}-stage2-todo-checklist.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text("current owner")
    policies = [
        dict(family="main", path=str(manifest_file), sha256=handoff._sha(manifest_file))
    ]
    source = dict(
        controller_path=str(controller),
        controller_sha256=handoff._sha(controller),
        summary_path=str(summary_file),
        summary_sha256=handoff._sha(summary_file),
        policy_receipts=policies,
    )
    monkeypatch.setattr(readiness, "_source_receipts", lambda *a, **k: source)
    index_file = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    receipt = Path(json.loads(index_file.read_text())["receipt_path"])
    _json(
        receipt,
        dict(
            schema="next_preopen_readiness_v1",
            status="prepared_verified",
            source_date=source_day,
            target_date=DAY,
            actual_pid_consumed=False,
            policy_receipts=policies,
        ),
    )
    _json(
        index_file,
        dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)),
    )
    before = {
        str(p): p.read_bytes()
        for p in (summary_file, controller, manifest_file, env_file, receipt)
    }
    handoff.prepare(
        DAY,
        old_pid=1,
        previous_root=previous,
        confirm=handoff.CONFIRM,
        now=NOW,
        reseal_postclose_source=True,
    )
    if not prepared:
        _json(verification_file, {**verification, "pid": 2})
        consumed = handoff.consume(DAY, pid=2, now=NOW)
    check = handoff.verify
    monkeypatch.setattr(
        handoff, "verify", lambda day, commit: check(day, commit, now=NOW + timedelta(days=1) if damage == "expired" else NOW)
    )
    # Launcher attestation legitimately changes selector bytes after consume.
    _json(
        selection_file,
        dict(
            schema="runtime_release_selection_v1",
            git_commit=NEW,
            release_root=str(selected),
            actual_pid_consumed=not prepared,
        ),
    )
    if damage == "summary":
        summary_file.write_text(summary_file.read_text() + " ")
    elif damage == "consumption":
        _json(handoff._paths(DAY, NEW)[1], {"status": "pass"} if prepared else {**consumed, "handoff_sha256": "changed"})
    elif damage == "policy":
        env_file.write_text("changed")
    elif damage == "pid":
        _json(verification_file, {**verification, "pid": 2})
    result = postclose.inspect_future_handoff(
        summary, source_day, report_dir=data / "report"
    )
    if damage is None:
        assert (
            result["status"] == ("intraday_prepared_generation_unconsumed" if prepared else "intraday_preserved_generation_pid_receipt_unconfirmed")
        ), result
        assert (
            result["pid_receipt_present"] is True
            and result["actual_pid_consumed"] is False
        )
        if prepared:
            assert "consumption_sha256" not in result
            assert not handoff._paths(DAY, NEW)[1].exists()
        assert all(Path(p).read_bytes() == value for p, value in before.items())
        assert not (
            data / "runtime/policy_bootstrap/future_handoff_transitions"
        ).exists()
        from src.engine.scalping import mechanistic_entry_runtime_policy as machine

        monkeypatch.setattr(machine, "load_effective", lambda **kw: {"valid": True})
        assert (
            postclose.stage_overview(data / "report", source_day)[
                "next_session_policy_ready"
            ]
            is True
        )
    else:
        assert result["status"] == "stale", result


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "manifest",
        "env",
        "verification",
        "pid",
        "consumption",
        "missing_consumption",
        "next_day",
    ],
)
def test_postclose_generation_accepts_only_native_preserved_intraday_pid(
    fixture, monkeypatch, damage
):
    data, _, selected, prepare = fixture
    bootstrap = handoff.bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", data)
    manifest = {
        "target_date": DAY,
        "selected_release_sha": OLD,
        "manifest_sha256": "policy-unchanged",
    }
    _json(bootstrap.manifest_path(DAY), manifest)
    assert prepare()["status"] == "pass"
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    assert consumed["actual_pid_consumed"] is True
    selection = {
        "schema": "runtime_release_selection_v1",
        "git_commit": NEW,
        "release_root": str(selected),
    }
    _json(data / "runtime/runtime_release_selection.json", selection)
    verification = {
        "target_date": DAY,
        "status": "pass",
        "passed": True,
        "pid": 2,
        "pid_passed": True,
        "pid_env_available": True,
    }
    _json(bootstrap.verify_path(DAY), verification)
    check = handoff.verify
    clock = NOW + timedelta(days=1) if damage == "next_day" else NOW
    monkeypatch.setattr(
        handoff, "verify", lambda day, commit: check(day, commit, now=clock)
    )
    if damage == "manifest":
        _json(bootstrap.manifest_path(DAY), {**manifest, "changed": True})
    elif damage == "env":
        bootstrap.env_path(DAY).write_text("POLICY=changed\n")
    elif damage == "verification":
        _json(bootstrap.verify_path(DAY), {**verification, "pid": 1})
    elif damage == "pid":
        verification["pid"] = 1
        _json(bootstrap.verify_path(DAY), verification)
    elif damage == "consumption":
        _json(handoff._paths(DAY, NEW)[1], {**consumed, "handoff_sha256": "changed"})
    elif damage == "missing_consumption":
        handoff._paths(DAY, NEW)[1].unlink()
    result = bootstrap.release_selection_for_generation(data, manifest, verification)
    if damage is None:
        assert result["status"] == "intraday_preserved", result
        assert result["selection"]["git_commit"] == NEW
        assert result["original_manifest_release_commit"] == OLD
    else:
        assert result["status"] == "invalid", result


@pytest.mark.parametrize(
    "mutation",
    ["env", "manifest", "preopen", "prepared", "commit", "ttl", "consumption"],
)
def test_intraday_handoff_rejects_changed_generation_identity_and_expired_launch(
    fixture, mutation
):
    data, _, _, prepare = fixture
    assert prepare()["status"] == "pass"
    current = NOW
    commit = NEW
    if mutation == "env":
        handoff.bootstrap.env_path(DAY).write_text("export POLICY=changed\n")
    elif mutation == "manifest":
        _json(handoff.bootstrap.manifest_path(DAY), {"policy": "changed"})
    elif mutation == "preopen":
        _json(handoff._preopen_path(DAY), {"status": "failed"})
    elif mutation == "prepared":
        _json(data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json", {})
    elif mutation == "commit":
        commit = OLD
    elif mutation == "ttl":
        current += timedelta(minutes=16)
    elif mutation == "consumption":
        _json(handoff._paths(DAY, NEW)[1], {"actual_pid_consumed": True})
    assert handoff.verify(DAY, commit, now=current)["status"] == "fail"


@pytest.mark.parametrize(
    "fault",
    ["authority", "native_fail", "old_pid", "preopen_fail", "next_day", "dirty"],
)
def test_intraday_prepare_rejects_missing_authority_or_native_custody(
    fixture, monkeypatch, fault
):
    _, previous, _, _ = fixture
    confirm, current = handoff.CONFIRM, NOW
    if fault == "authority":
        confirm = ""
    elif fault == "native_fail":
        monkeypatch.setattr(
            handoff.bootstrap,
            "verify_bootstrap",
            lambda *args, **kwargs: {
                "status": "fail",
                "findings": ["source_receipt_hash_mismatch"],
            },
        )
    elif fault == "old_pid":
        monkeypatch.setattr(
            handoff, "_identity", lambda pid: {"pid": pid, "cwd": "/other/src"}
        )
    elif fault == "preopen_fail":
        _json(handoff._preopen_path(DAY), {"status": "failed"})
    elif fault == "next_day":
        current += timedelta(days=1)
    elif fault == "dirty":
        monkeypatch.setattr(
            handoff.subprocess,
            "check_output",
            lambda command, **kwargs: (
                OLD if "rev-parse" in command else " M src/runtime.py"
            ),
        )
    with pytest.raises((ValueError, KeyError)):
        handoff.prepare(
            DAY, old_pid=1, previous_root=previous, confirm=confirm, now=current
        )
    assert not handoff._paths(DAY, NEW)[0].exists()


def test_intraday_receipt_immutable_and_old_pid_cannot_claim_new_consumption(fixture):
    _, _, _, prepare = fixture
    prepare()
    with pytest.raises(FileExistsError):
        prepare()
    with pytest.raises(ValueError, match="new_pid_root_invalid"):
        handoff.consume(DAY, pid=1, now=NOW)


def test_changed_commit_without_intraday_receipt_does_not_admit_launcher(fixture):
    assert readiness.verify_preopen_completion(DAY, NEW, now=NOW)["status"] == "fail"
    assert readiness.verify_preopen_completion(DAY, OLD, now=NOW)["status"] == "pass"


def test_prepared_verifier_preserves_original_receipt_and_checks_sources(
    fixture, monkeypatch
):
    data, _, selected, prepare = fixture
    prepared_root = data / "runtime/policy_bootstrap/prepared" / DAY
    monkeypatch.setattr(readiness, "PREPARED_DIR", prepared_root.parent)
    source = {"source_proof": "unchanged"}
    monkeypatch.setattr(readiness, "_source_receipts", lambda *args, **kwargs: source)
    selection = data / "runtime/runtime_release_selection.json"
    _json(selection, {"git_commit": NEW, "release_root": str(selected)})
    monkeypatch.setattr(
        readiness, "_selected_release", lambda **kwargs: ({}, selection, NEW)
    )
    live_env = handoff.bootstrap.env_path(DAY)
    live_manifest = handoff.bootstrap.manifest_path(DAY)
    monkeypatch.setattr(
        handoff.bootstrap,
        "env_path",
        lambda day, output_dir=None: (
            Path(output_dir) / "env" if output_dir else live_env
        ),
    )
    monkeypatch.setattr(
        handoff.bootstrap,
        "manifest_path",
        lambda day, output_dir=None: (
            Path(output_dir) / "manifest" if output_dir else live_manifest
        ),
    )
    receipt_path = prepared_root / "generation/readiness.json"
    output = receipt_path.parent
    for path in (
        output / "env",
        output / "manifest",
        handoff.bootstrap.verify_path(DAY, output_dir=output),
    ):
        _json(path, {})
    receipt = {
        "schema": "next_preopen_readiness_v1",
        "status": "prepared_verified",
        "target_date": DAY,
        "source_date": "2026-09-30",
        "selected_release_commit": OLD,
        "selection_sha256": "old",
        "actual_pid_consumed": False,
        "runtime_effect": False,
        "manifest_content_sha256": "policy-unchanged",
        "manifest_file_sha256": handoff._sha(output / "manifest"),
        "env_sha256": handoff._sha(output / "env"),
        "verification_sha256": handoff._sha(
            handoff.bootstrap.verify_path(DAY, output_dir=output)
        ),
        **source,
    }
    _json(receipt_path, receipt)
    _json(
        prepared_root / "latest.json",
        {
            "target_date": DAY,
            "receipt_path": str(receipt_path),
            "receipt_sha256": handoff._sha(receipt_path),
        },
    )
    prepare()
    result = readiness.verify_prepared(DAY, require_today=True, now=NOW)
    assert result["status"] == "pass"
    assert (
        result["selected_release_commit"] == NEW
        and result["preserved_preopen_commit"] == OLD
    )
    assert result["actual_pid_consumed"] is False
    monkeypatch.setattr(
        readiness,
        "_source_receipts",
        lambda *args, **kwargs: {"source_proof": "changed"},
    )
    assert readiness.verify_prepared(DAY, now=NOW)["status"] == "fail"


def test_main_policy_activation_requires_actual_code_pid_and_new_authority(
    fixture, monkeypatch
):
    _, _, _, prepare = fixture
    prepare()
    handoff.consume(DAY, pid=2, now=NOW)
    from src.engine.scalping import continuous_reversal_policy_v2 as policy

    calls = []
    monkeypatch.setattr(
        policy,
        "activate",
        lambda *args, **kwargs: calls.append(kwargs) or dict(status="activated"),
    )
    with pytest.raises(ValueError, match="explicit_authority"):
        handoff.activate_main_v2(DAY, pid=2, confirm=handoff.CONFIRM, now=NOW)
    assert not calls
    with pytest.raises(ValueError, match="pid_release"):
        handoff.activate_main_v2(
            DAY, pid=1, confirm="APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION", now=NOW
        )
    assert not calls
    result = handoff.activate_main_v2(
        DAY, pid=2, confirm="APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION", now=NOW
    )
    assert (
        result["status"] == "pass" and result["actual_policy_pid_consumption"] is False
    )
    assert calls[0]["intraday_evidence"]["pid_identity"]["pid"] == 2


def test_v5_next_session_candidate_cannot_fall_through_to_intraday_v2(
    fixture, monkeypatch
):
    data, _, _, prepare = fixture
    prepare()
    handoff.consume(DAY, pid=2, now=NOW)
    from src.engine.scalping import continuous_reversal_policy_v2 as policy

    monkeypatch.setattr(
        policy, "activate", lambda *a, **kw: pytest.fail("v5 reached v2 activation")
    )
    _json(
        data / "runtime/mechanistic_entry_policy/candidates" / f"policy_{DAY}.json",
        {"continuous_reversal": {"schema": "continuous_reversal_policy_v5"}},
    )
    with pytest.raises(ValueError, match="requires_next_session_activation"):
        handoff.activate_main_v2(
            DAY, pid=2, confirm="APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION", now=NOW
        )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "wrong_original",
        "missing_snapshot",
        "corrupt_snapshot",
        "symlink_snapshot",
        "wrong_prepared_hash",
    ],
)
def test_preserve_exact_native_checklist_keeps_concurrent_owner_edits(
    tmp_path, monkeypatch, damage
):
    import hashlib

    data = tmp_path / "data"
    monkeypatch.setattr(handoff, "DATA_DIR", data)
    original = b"original strict-bound native checklist\n"
    expected = hashlib.sha256(original).hexdigest()
    source = tmp_path / "docs/checklists" / (DAY + "-stage2-todo-checklist.md")
    source.parent.mkdir(parents=True)
    edited = b"current checklist with another owner\n"
    source.write_bytes(edited)
    receipt = data / "runtime/policy_bootstrap/prepared" / DAY / "attempt/receipt.json"
    _json(
        receipt,
        dict(status="prepared_verified", target_date=DAY, source_date="2026-10-01"),
    )
    _json(
        receipt.parent.parent / "latest.json",
        dict(
            receipt_path=str(receipt),
            receipt_sha256=(
                "0" * 64 if damage == "wrong_prepared_hash" else handoff._sha(receipt)
            ),
        ),
    )
    strict = data / "strict.json"
    _json(strict, dict(generation_binding=dict(checklist_sha256=expected)))
    _json(
        data
        / "report/postclose_done_controller/postclose_done_controller_2026-10-01.json",
        dict(verification_attempt_path=str(strict)),
    )
    if damage == "missing_snapshot":
        with pytest.raises(ValueError):
            handoff.preserve_checklist(DAY)
    elif damage in {"wrong_original", "wrong_prepared_hash"}:
        with pytest.raises(ValueError):
            handoff.preserve_checklist(
                DAY,
                original_content=b"wrong" if damage == "wrong_original" else original,
            )
    else:
        result = handoff.preserve_checklist(DAY, original_content=original)
        snapshot = Path(result["path"])
        assert snapshot.read_bytes() == original
        if damage == "corrupt_snapshot":
            snapshot.write_bytes(b"corrupt")
        elif damage == "symlink_snapshot":
            other = tmp_path / "other"
            other.write_bytes(original)
            snapshot.unlink()
            snapshot.symlink_to(other)
        if damage:
            with pytest.raises(ValueError):
                handoff.preserve_checklist(DAY)
        else:
            assert handoff.preserve_checklist(DAY) == result
    assert source.read_bytes() == edited


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "git_bytes",
        "snapshot",
        "postclose_generated",
        "generated_corrupt",
        "git_missing",
        "git_missing_without_snapshot",
        "git_missing_corrupt_snapshot",
    ],
)
def test_authorized_intraday_historical_checklist_is_exact_git_bound_snapshot(
    fixture, monkeypatch, damage
):
    data, previous, _, _ = fixture
    source_day = "2026-10-01"
    original = b"original verified checklist\n"
    checklist = data.parent / "docs/checklists" / f"{DAY}-stage2-todo-checklist.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text("current work added\n")
    strict = data / "strict.json"
    _json(
        strict,
        {
            "checklist_handoff": {"path": str(checklist)},
            "generation_binding": {
                "checklist_sha256": __import__("hashlib").sha256(original).hexdigest()
            },
        },
    )
    controller = (
        data
        / "report/postclose_done_controller"
        / f"postclose_done_controller_{source_day}.json"
    )
    summary = (
        data
        / "report/runtime_approval_summary"
        / f"runtime_approval_summary_{source_day}.json"
    )
    _json(controller, {"verification_attempt_path": str(strict)})
    _json(summary, {"date": source_day})
    index_file = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    index = handoff._read(index_file)
    receipt = Path(index["receipt_path"])
    policies = [{"family": "main", "path": "/unchanged.json", "sha256": "d" * 64}]
    _json(
        receipt,
        {
            "schema": "next_preopen_readiness_v1",
            "status": "prepared_verified",
            "target_date": DAY,
            "source_date": source_day,
            "actual_pid_consumed": False,
            "policy_receipts": policies,
        },
    )
    _json(
        index_file,
        {"receipt_path": str(receipt), "receipt_sha256": handoff._sha(receipt)},
    )
    if damage in {
        "postclose_generated",
        "generated_corrupt",
        "git_missing",
        "git_missing_corrupt_snapshot",
    }:
        checklist.write_bytes(original)
        preserved = handoff.preserve_checklist(DAY)
        checklist.write_text("current work added\n")
        if damage in {"generated_corrupt", "git_missing_corrupt_snapshot"}:
            Path(preserved["path"]).write_text("corrupt")

    def output(command, **kwargs):
        if "show" in command and str(damage).startswith("git_missing"):
            raise handoff.subprocess.CalledProcessError(128, command)
        if "show" in command:
            return (
                b"wrong"
                if damage in {"git_bytes", "postclose_generated", "generated_corrupt"}
                else original
            )
        return OLD + "\n" if "rev-parse" in command else ""

    monkeypatch.setattr(handoff.subprocess, "check_output", output)

    def source(*args, **kwargs):
        assert kwargs["generation_only"] is True
        assert Path(kwargs["checklist_snapshot"]).read_bytes() == original
        return {
            "controller_path": str(controller),
            "controller_sha256": handoff._sha(controller),
            "summary_path": str(summary),
            "summary_sha256": handoff._sha(summary),
            "policy_receipts": policies,
        }

    monkeypatch.setattr(readiness, "_source_receipts", source)
    if damage in {
        "git_bytes",
        "generated_corrupt",
        "git_missing_without_snapshot",
        "git_missing_corrupt_snapshot",
    }:
        with pytest.raises(ValueError, match="git_generation_missing"):
            handoff.prepare(
                DAY,
                old_pid=1,
                previous_root=previous,
                confirm=handoff.CONFIRM,
                now=NOW,
                reseal_postclose_source=True,
            )
        return
    result = handoff.prepare(
        DAY,
        old_pid=1,
        previous_root=previous,
        confirm=handoff.CONFIRM,
        now=NOW,
        reseal_postclose_source=True,
    )
    assert result["status"] == "pass"
    snap = Path(
        result["handoff"]["postclose_source_reseal"]["historical_checklist"]["path"]
    )
    if damage == "snapshot":
        snap.write_text("changed")
        assert handoff.verify(DAY, NEW, now=NOW)["status"] == "fail"
    assert checklist.read_text() == "current work added\n"


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "snapshot",
        "consumed",
        "git_bytes",
        "predecessor_binding",
        "env_after_consumption",
        "controller_after_consumption",
        "summary_after_consumption",
        "snapshot_after_consumption",
        "consumption_missing_after_edit",
        "removed_original_release",
        "removed_original_release_corrupt_snapshot",
    ],
)
def test_second_handoff_carries_original_git_snapshot_with_consumed_custody(
    fixture, monkeypatch, damage
):
    data, previous, selected, _ = fixture
    original = b"original sealed generation\n"
    checklist = data.parent / "docs/checklists" / f"{DAY}-stage2-todo-checklist.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text("new current owners\n")
    strict = data / "strict.json"
    expected = __import__("hashlib").sha256(original).hexdigest()
    original_path = checklist
    if damage in {
        "removed_original_release",
        "removed_original_release_corrupt_snapshot",
    }:
        original_path = previous / "docs/checklists" / checklist.name
        original_path.parent.mkdir(parents=True)
        original_path.write_bytes(checklist.read_bytes())
    _json(
        strict,
        {
            "checklist_handoff": {"path": str(original_path)},
            "generation_binding": {"checklist_sha256": expected},
        },
    )
    controller = (
        data
        / "report/postclose_done_controller/postclose_done_controller_2026-10-01.json"
    )
    summary = (
        data
        / "report/runtime_approval_summary/runtime_approval_summary_2026-10-01.json"
    )
    _json(controller, {"verification_attempt_path": str(strict)})
    _json(summary, {})
    index = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    receipt = Path(handoff._read(index)["receipt_path"])
    policies = [{"family": "main"}]
    _json(
        receipt,
        dict(
            schema="next_preopen_readiness_v1",
            status="prepared_verified",
            target_date=DAY,
            source_date="2026-10-01",
            actual_pid_consumed=False,
            policy_receipts=policies,
        ),
    )
    _json(index, dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)))

    def source(*args, **kwargs):
        assert Path(kwargs["checklist_snapshot"]).read_bytes() == original
        return dict(
            controller_path=str(controller),
            controller_sha256=handoff._sha(controller),
            summary_path=str(summary),
            summary_sha256=handoff._sha(summary),
            policy_receipts=policies,
        )

    monkeypatch.setattr(readiness, "_source_receipts", source)
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda command, **kwargs: (
            original
            if "show" in command
            else OLD + "\n" if "rev-parse" in command else ""
        ),
    )
    handoff.prepare(
        DAY,
        old_pid=1,
        previous_root=previous,
        confirm=handoff.CONFIRM,
        now=NOW,
        reseal_postclose_source=True,
    )
    handoff.consume(DAY, pid=2, now=NOW)
    prior_path, consumed_path = handoff._paths(DAY, NEW)
    snapshot = prior_path.parent / (NEW + ".historical-checklist.md")
    if damage in {
        "removed_original_release",
        "removed_original_release_corrupt_snapshot",
    }:
        original_path.unlink()
    if damage == "removed_original_release_corrupt_snapshot":
        snapshot.write_text("changed")
    if damage == "snapshot":
        snapshot.write_text("changed")
    if damage == "consumed":
        _json(
            consumed_path,
            {**handoff._read(consumed_path), "actual_pid_consumed": False},
        )
    second = selected.parent / "second"
    second.mkdir()
    commit = "c" * 40
    monkeypatch.setattr(handoff, "_selection", lambda **kwargs: (second, commit))
    monkeypatch.setattr(
        handoff,
        "_identity",
        lambda pid: dict(
            pid=pid,
            start_ticks="42",
            cwd=str((selected if pid == 2 else second) / "src"),
        ),
    )

    def git_output(command, **kwargs):
        if "show" in command:
            # NEW contains the edited checklist, so only the original OLD
            # Git object is valid evidence for a repeated handoff.
            assert command[-1].startswith(OLD + ":")
            return b"wrong bytes" if damage == "git_bytes" else original
        return NEW + "\n" if "rev-parse" in command else ""

    monkeypatch.setattr(handoff.subprocess, "check_output", git_output)
    if damage in {
        "snapshot",
        "consumed",
        "git_bytes",
        "removed_original_release_corrupt_snapshot",
    }:
        with pytest.raises(ValueError, match="intraday_"):
            handoff.prepare(
                DAY,
                old_pid=2,
                previous_root=selected,
                confirm=handoff.CONFIRM,
                now=NOW + timedelta(minutes=2),
                reseal_postclose_source=True,
            )
        assert not handoff._paths(DAY, commit)[0].exists()
        return
    result = handoff.prepare(
        DAY,
        old_pid=2,
        previous_root=selected,
        confirm=handoff.CONFIRM,
        now=NOW + timedelta(minutes=2),
        reseal_postclose_source=True,
    )
    historical = result["handoff"]["postclose_source_reseal"]["historical_checklist"]
    assert historical["git_commit"] == OLD
    assert Path(historical["path"]).read_bytes() == original
    if damage == "predecessor_binding":
        _json(
            consumed_path, {**handoff._read(consumed_path), "handoff_sha256": "wrong"}
        )
        assert (
            handoff.verify(DAY, commit, now=NOW + timedelta(minutes=2))["status"]
            == "fail"
        )
    else:
        assert (
            handoff.consume(DAY, pid=3, now=NOW + timedelta(minutes=2))["status"]
            == "pass"
        )
        # Current work can change after launch. It cannot invalidate the sealed
        # historical DONE, or grant permission to launch/apply a fresh policy.
        checklist.write_text("additional current intraday work\n")
        assert (
            handoff.verify(DAY, commit, now=NOW + timedelta(minutes=3))["status"]
            == "fail"
        )
        assert (
            handoff.consume(DAY, pid=3, now=NOW + timedelta(minutes=3))["status"]
            == "fail"
        )
        with pytest.raises(
            ValueError, match="intraday_main_policy_code_consumption_missing"
        ):
            handoff.activate_main_v2(
                DAY,
                pid=3,
                confirm="APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION",
                now=NOW + timedelta(minutes=3),
            )
        damaged_path = {
            "env_after_consumption": handoff.bootstrap.env_path(DAY),
            "controller_after_consumption": controller,
            "summary_after_consumption": summary,
            "snapshot_after_consumption": Path(historical["path"]),
            "consumption_missing_after_edit": handoff._paths(DAY, commit)[1],
        }.get(damage)
        if damaged_path:
            if damage == "consumption_missing_after_edit":
                damaged_path.unlink()
            else:
                damaged_path.write_text("changed")
            with pytest.raises(ValueError, match="intraday_observer_"):
                handoff.historical_checklist_for_observer(
                    data.parent, "2026-10-01", now=NOW + timedelta(minutes=3)
                )
            return
        observer = handoff.historical_checklist_for_observer(
            data.parent, "2026-10-01", now=NOW + timedelta(minutes=3)
        )
        assert observer["path"] == historical["path"]
        assert observer["pid_identity"]["pid"] == 3
        assert (
            observer["runtime_effect"] is False
            and observer["new_finalization_claimed"] is False
        )
        for project, source in [(data.parent.parent, "2026-10-01"), (data.parent, DAY)]:
            with pytest.raises(ValueError, match="intraday_observer_"):
                handoff.historical_checklist_for_observer(
                    project, source, now=NOW + timedelta(minutes=3)
                )
        consumed_path = handoff._paths(DAY, commit)[1]
        consumed = handoff._read(consumed_path)
        for field, value in [
            ("status", "fail"),
            ("schema", "wrong"),
            ("manifest_sha256", "changed"),
        ]:
            _json(consumed_path, {**consumed, field: value})
            with pytest.raises(ValueError, match="intraday_observer_"):
                handoff.historical_checklist_for_observer(
                    data.parent, "2026-10-01", now=NOW + timedelta(minutes=3)
                )
        _json(consumed_path, consumed)
        handoff_path = handoff._paths(DAY, commit)[0]
        original_handoff = handoff_path.read_bytes()
        original_bootstrap = handoff._checked_bootstrap

        def changing_bootstrap(*args):
            checked = original_bootstrap(*args)
            handoff_path.write_bytes(original_handoff + b" ")
            return checked

        monkeypatch.setattr(handoff, "_checked_bootstrap", changing_bootstrap)
        with pytest.raises(
            ValueError, match="intraday_observer_pid_generation_changed"
        ):
            handoff.historical_checklist_for_observer(
                data.parent, "2026-10-01", now=NOW + timedelta(minutes=3)
            )
        handoff_path.write_bytes(original_handoff)
        monkeypatch.setattr(handoff, "_checked_bootstrap", original_bootstrap)
        monkeypatch.setattr(
            handoff,
            "_identity",
            lambda pid: dict(
                pid=pid, start_ticks="reused-pid", cwd=str(second / "src")
            ),
        )
        with pytest.raises(ValueError, match="intraday_observer_current_pid_not_bound"):
            handoff.historical_checklist_for_observer(
                data.parent, "2026-10-01", now=NOW + timedelta(minutes=3)
            )


@pytest.mark.parametrize(
    "consumer,approval",
    [
        (
            "sniper_state_handlers.py",
            "machine_auxiliary_path_repair_deploy_and_restart",
        ),
        ("ai_engine_openai.py", "entry_input_deadline_repair_deploy_and_restart"),
        (
            "monitoring/submission_bottleneck_monitor.py",
            "ordered_intraday_deploy_and_restart",
        ),
    ],
)
@pytest.mark.parametrize(
    "identity_mode", ["live", "stopped", "unbound_stopped", "stopped_still_alive"]
)
@pytest.mark.parametrize(
    "fault",
    [
        None,
        "authority",
        "consumed",
        "pid",
        "manifest",
        "policy",
        "producer",
        "other_function",
        "verifier",
    ],
)
def test_entry_consumer_repair_can_verify_before_own_handoff_without_relaxing_sources(
    fixture, monkeypatch, fault, consumer, approval, identity_mode
):
    import hashlib

    data, previous, selected, _ = fixture
    monkeypatch.setattr(handoff, "_today", lambda *a: NOW)
    name = "src/engine/" + consumer
    own = "src/engine/automation/intraday_release_handoff.py"
    function = {
        "sniper_state_handlers.py": "_get_live_entry_arm",
        "ai_engine_openai.py": "_final_entry_machine_inputs",
        "monitoring/submission_bottleneck_monitor.py": "_reversal_lifecycle_diagnostic",
    }[consumer]
    original = (
        "def " + function + "():\n return 1\ndef hard_guard():\n return False\n"
    ).encode()
    revised = original.replace(b"return 1", b"return 2")
    if fault == "other_function":
        revised = revised.replace(b"return False", b"return True")
    if fault == "producer":
        name = "src/engine/producer.py"
    for n, raw in [(name, revised), (own, b"# reviewed verifier\n")]:
        p = selected / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    monkeypatch.setattr(handoff, "__file__", str(selected / own))
    if fault == "verifier":
        (selected / own).write_bytes(b"# dirty verifier\n")

    def git(cmd, **kw):
        rev, path = cmd[-1].split(":", 1)
        return (
            b"# reviewed verifier\n"
            if path == own
            else original if rev == OLD else revised
        )

    monkeypatch.setattr(handoff.subprocess, "check_output", git)
    expected = hashlib.sha256(
        json.dumps(
            {name: hashlib.sha256(original).hexdigest()},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    manifest = dict(
        selected_release_sha=OLD,
        manifest_sha256="sealed-manifest",
        pre_submit_delay_handoff=dict(
            policy_sha256="policy", code_contract_sha256=expected, target_date=DAY
        ),
    )
    _json(handoff.bootstrap.manifest_path(DAY), manifest)
    selection = dict(
        previous_git_commit=OLD,
        previous_release_root=str(previous),
        approved_by="user",
        approval_scope="wrong" if fault == "authority" else approval,
    )
    _json(data / "runtime/runtime_release_selection.json", selection)
    prior_path, consumed_path = handoff._paths(DAY, OLD)
    prior = dict(
        schema="intraday_policy_preserving_release_handoff_v1",
        status="prepared_verified",
        authority=handoff.CONFIRM,
        target_date=DAY,
        selected_release_commit=OLD,
        release_root=str(previous),
        frozen_files={
            str(p): handoff._sha(p)
            for p in [
                handoff.bootstrap.manifest_path(DAY),
                handoff.bootstrap.env_path(DAY),
                handoff._preopen_path(DAY),
            ]
        },
    )
    _json(prior_path, prior)
    consumed = dict(
        schema="intraday_policy_preserving_consumption_v1",
        status="pass",
        actual_pid_consumed=fault != "consumed",
        target_date=DAY,
        selected_release_commit=OLD,
        release_root=str(previous),
        manifest_sha256="sealed-manifest",
        handoff_sha256=handoff._sha(prior_path),
        pid_identity=handoff._identity(1),
    )
    if fault == "pid":
        consumed["pid_identity"]["pid"] = 99
    _json(consumed_path, consumed)
    if fault == "manifest":
        handoff.bootstrap.env_path(DAY).write_text("mutated")
    kwargs = dict(
        family="pre_submit_delay",
        policy_sha="wrong" if fault == "policy" else "policy",
        expected=expected,
        paths={name: name},
        actual="new",
    )
    token = handoff._STOPPED_PREPARATION.set(
        (DAY, 1, str(previous))
        if identity_mode in {"stopped", "stopped_still_alive"}
        else None
    )
    exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda p: (
            identity_mode == "stopped_still_alive" if str(p) == "/proc/1" else exists(p)
        ),
    )
    if identity_mode != "live":

        def dead(pid):
            raise ValueError("predecessor_not_live")

        monkeypatch.setattr(handoff, "_identity", dead)
    try:
        if fault or identity_mode in {"unbound_stopped", "stopped_still_alive"}:
            with pytest.raises(ValueError):
                handoff.verify_entry_consumer_code(DAY, **kwargs)
        else:
            proof = handoff.verify_entry_consumer_code(DAY, **kwargs)
            assert proof["policy_effect"] == "unchanged" and proof[
                "changed_consumer_paths"
            ] == [name]
            assert not handoff._paths(DAY, NEW)[0].exists()
    finally:
        handoff._STOPPED_PREPARATION.reset(token)


def test_stopped_preparation_context_cannot_escape_success_or_failure(
    fixture, monkeypatch
):
    _, previous, _, _ = fixture

    def check(*args, **kw):
        assert handoff._STOPPED_PREPARATION.get() == (DAY, 1, str(previous))
        return {"status": "pass"}

    monkeypatch.setattr(handoff, "_prepare", check)
    assert (
        handoff.prepare(
            DAY,
            old_pid=1,
            previous_root=previous,
            confirm=handoff.CONFIRM,
            previous_stopped=True,
        )["status"]
        == "pass"
    )
    assert handoff._STOPPED_PREPARATION.get() is None

    def reject(*args, **kw):
        check()
        raise ValueError("prepare_failure")

    monkeypatch.setattr(handoff, "_prepare", reject)
    with pytest.raises(ValueError, match="prepare_failure"):
        handoff.prepare(
            DAY,
            old_pid=1,
            previous_root=previous,
            confirm=handoff.CONFIRM,
            previous_stopped=True,
        )
    assert handoff._STOPPED_PREPARATION.get() is None


def test_observer_context_never_relaxes_public_launch_verification(
    fixture, monkeypatch
):
    calls = []

    def verify(*a, **kw):
        calls.append(kw.get("historical_observer", False))
        return {"status": "fail"}

    monkeypatch.setattr(handoff, "_verify_handoff", verify)
    token = handoff._OBSERVER_CUSTODY.set((DAY, NEW))
    try:
        assert handoff.verify(DAY, NEW)["status"] == "fail"
        assert calls == [False]
    finally:
        handoff._OBSERVER_CUSTODY.reset(token)


def test_cli_and_nested_policy_readers_share_canonical_context(monkeypatch):
    import runpy
    import sys

    called = []
    monkeypatch.setattr(sys, "argv", ["intraday-release-handoff"])
    monkeypatch.setattr(handoff, "main", lambda: called.append("canonical") or 0)
    with pytest.warns(RuntimeWarning, match="found in sys.modules"):
        with pytest.raises(SystemExit) as result:
            runpy.run_module(handoff.__name__, run_name="__main__")
    assert result.value.code == 0 and called == ["canonical"]


@pytest.mark.parametrize(
    "fault",
    [None, "other_function", "producer", "dirty", "verifier", "hash", "date", "origin"],
)
def test_candidate_delay_code_is_checked_without_selection_or_runtime_mutation(
    fixture, monkeypatch, fault
):
    import hashlib
    from src.engine.scalping import pre_submit_delay_initial_policy as policy

    data, _, selected, _ = fixture
    monkeypatch.setattr(handoff, "_today", lambda *a: NOW)
    name = "src/engine/monitoring/submission_bottleneck_monitor.py"
    own = "src/engine/automation/intraday_release_handoff.py"
    original = b"def _reversal_lifecycle_diagnostic(row):\n return None\ndef qualify_delay(row):\n return False\n"
    revised = original.replace(b"return None", b'return "diagnostic"')
    if fault == "other_function":
        revised = revised.replace(b"return False", b"return True")
    if fault == "producer":
        name = "src/engine/scalping/pre_submit_delay_initial_policy.py"
    for path, content in ((name, revised), (own, b"# reviewed\n")):
        f = selected / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(content)
    monkeypatch.setattr(handoff, "__file__", str(selected / own))
    monkeypatch.setattr(policy, "CONTRACT_PATHS", (name,))
    monkeypatch.setattr(
        handoff, "_selection", lambda **kw: pytest.fail("must not select candidate")
    )
    monkeypatch.setattr(
        handoff, "_identity", lambda *a: pytest.fail("must not touch process")
    )
    monkeypatch.setattr(
        handoff.subprocess,
        "check_output",
        lambda command, **kw: (
            b"# reviewed\n"
            if command[-1].endswith(":" + own)
            else original if command[-1].startswith(OLD + ":") else revised
        ),
    )
    expected = hashlib.sha256(
        json.dumps(
            {name: hashlib.sha256(original).hexdigest()},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    _json(
        handoff.bootstrap.manifest_path(DAY),
        dict(
            selected_release_sha=NEW if fault == "origin" else OLD,
            pre_submit_delay_handoff=dict(
                status="verified_initial_timing_policy",
                target_date="wrong" if fault == "date" else DAY,
                code_contract_sha256="wrong" if fault == "hash" else expected,
            ),
        ),
    )
    if fault == "dirty":
        (selected / name).write_bytes(revised + b"# uncommitted\n")
    if fault == "verifier":
        (selected / own).write_bytes(b"# uncommitted\n")
    before = {p: p.read_bytes() for p in data.parent.parent.rglob("*") if p.is_file()}
    if fault:
        with pytest.raises(ValueError):
            handoff.verify_candidate_delay_code(DAY, selected, NEW)
    else:
        result = handoff.verify_candidate_delay_code(DAY, selected, NEW)
        assert result["status"] == "pass" and result["actual_pid_consumed"] is False
        assert result["changed_consumer_paths"] == [name]
    assert before == {
        p: p.read_bytes() for p in data.parent.parent.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "root",
        "origin",
        "date",
        "bundle",
        "path",
        "successor",
        "unreviewed",
        "absent_receipt",
    ],
)
def test_candidate_holding_vote_pin_is_checked_before_selection(
    fixture, monkeypatch, fault
):
    from src.engine.scalping import (
        holding_path_vote_policy as V,
        holding_vote_experiment as E,
    )

    data, _, selected, _ = fixture
    monkeypatch.setattr(handoff, "_today", lambda *a: NOW)
    monkeypatch.setattr(
        handoff,
        "__file__",
        str(selected / "src/engine/automation/intraday_release_handoff.py"),
    )
    monkeypatch.setattr(
        handoff,
        "_selection",
        lambda **kw: pytest.fail("no selector mutation or dependency"),
    )
    bundle = dict(
        schema=V.SUCCESSOR_SCHEMA,
        bundle_sha256="b" * 64,
        code_sha256="c" * 64,
        selection_mode=(
            "validated_successor" if fault == "successor" else "incumbent_carry"
        ),
    )

    def load(root, day, *, require_current_code):
        assert root == data and day == DAY and require_current_code is False
        return bundle

    monkeypatch.setattr(V, "load_bundle", load)
    monkeypatch.setattr(E, "code_sha", lambda: "d" * 64)
    checked = []

    def check(root, commit, origin, paths, expected):
        assert (
            root == selected
            and commit == NEW
            and origin == OLD
            and expected == "c" * 64
        )
        assert (
            paths["lifecycle/holding_window_generation.py"]
            == "src/engine/lifecycle/holding_window_generation.py"
        )
        checked.append(True)
        if fault == "unreviewed":
            raise ValueError("entry_consumer_producer_changed")
        return ["src/engine/lifecycle/holding_window_generation.py"]

    monkeypatch.setattr(handoff, "_verify_entry_code_delta", check)
    bound = dict(
        allowed_runtime_apply=True,
        target_date="wrong" if fault == "date" else DAY,
        bundle_sha256="wrong" if fault == "bundle" else "b" * 64,
        path="/wrong" if fault == "path" else str(V.policy_path(data, DAY)),
    )
    _json(
        handoff.bootstrap.manifest_path(DAY),
        dict(
            selected_release_sha=NEW if fault == "origin" else OLD,
            holding_path_vote_policy_receipt={} if fault == "absent_receipt" else bound,
        ),
    )
    before = {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}
    if fault:
        with pytest.raises(ValueError):
            handoff.verify_candidate_holding_vote_code(
                DAY, data if fault == "root" else selected, NEW
            )
    else:
        result = handoff.verify_candidate_holding_vote_code(DAY, selected, NEW)
        assert (
            result["status"] == "pass"
            and result["actual_pid_consumed"] is False
            and checked
        )
    assert before == {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}


@pytest.mark.parametrize(
    "damage", [None, "status", "schema", "pid", "manifest", "handoff", "policy"]
)
def test_existing_consumption_proof_is_live_and_immutable(fixture, monkeypatch, damage):
    data, _, _, prepare = fixture
    assert prepare()["status"] == "pass"
    assert handoff.consume(DAY, pid=2, now=NOW)["status"] == "pass"
    path, consumed_path = handoff._paths(DAY, NEW)
    body = handoff._read(consumed_path)
    if damage == "status":
        body["status"] = "fail"
    elif damage == "schema":
        body["schema"] = "foreign"
    elif damage == "pid":
        body["pid_identity"]["start_ticks"] = "reused"
    elif damage == "manifest":
        body["manifest_sha256"] = "changed"
    elif damage == "handoff":
        body["handoff_sha256"] = "changed"
    elif damage == "policy":
        handoff.bootstrap.env_path(DAY).write_text("changed")
    _json(consumed_path, body)
    checked = handoff._verify_consumed_handoff(DAY, NEW, now=NOW)
    assert checked["status"] == ("pass" if damage is None else "fail")


@pytest.mark.parametrize("raises", [False, True])
def test_candidate_predecessor_review_context_cannot_escape(
    fixture, monkeypatch, raises
):
    from src.engine.infrastructure import runtime_release_router as router

    data, previous, candidate, _ = fixture
    monkeypatch.setattr(
        handoff,
        "__file__",
        str(candidate / "src/engine/automation/intraday_release_handoff.py"),
    )
    monkeypatch.setattr(handoff, "_selection", lambda **kw: (previous, OLD))
    monkeypatch.setattr(router, "git", lambda *args: NEW)
    monkeypatch.setattr(router, "validate_release", lambda *args: (candidate, NEW))

    def read(day, *, pid):
        scope = handoff._PREDECESSOR_REVIEW.get()
        assert (
            scope["root"] == previous
            and scope["commit"] == OLD
            and scope["code_root"] == candidate
        )
        assert scope["identity"] == handoff._identity(pid)
        if raises:
            raise ValueError("unverified_native_source")
        return dict(status="pass")

    monkeypatch.setattr(handoff, "verify_pid_consumption", read)
    if raises:
        with pytest.raises(ValueError, match="unverified_native_source"):
            handoff.verify_predecessor_consumption(DAY, pid=1)
    else:
        result = handoff.verify_predecessor_consumption(DAY, pid=1)
        assert (
            result["runtime_effect"] is False
            and result["candidate_pid_consumed"] is False
        )
        assert result["verification_code_commit"] == NEW
    assert handoff._PREDECESSOR_REVIEW.get() is None


@pytest.mark.parametrize(
    "damage",
    [None, "no_context", "pid", "ticks", "cwd", "actual", "origin", "policy", "code"],
)
def test_candidate_code_review_of_first_live_native_predecessor_requires_exact_custody(
    fixture, monkeypatch, damage
):
    data, previous, candidate, _ = fixture
    monkeypatch.setattr(
        handoff,
        "__file__",
        str(candidate / "src/engine/automation/intraday_release_handoff.py"),
    )
    monkeypatch.setattr(handoff, "_selection", lambda **kw: (previous, OLD))
    monkeypatch.setattr(handoff, "_today", lambda *a: NOW)
    manifest = dict(
        target_date=DAY,
        selected_release_sha=OLD,
        pre_submit_delay_handoff=dict(
            policy_sha256="p", code_contract_sha256="source", target_date=DAY
        ),
    )
    if damage == "origin":
        manifest["selected_release_sha"] = NEW
    if damage == "policy":
        manifest["pre_submit_delay_handoff"]["policy_sha256"] = "wrong"
    _json(handoff.bootstrap.manifest_path(DAY), manifest)
    identity = handoff._identity(1)
    receipt = dict(pid=1, start_ticks="42", process_cwd=identity["cwd"])
    if damage == "pid":
        receipt["pid"] = 2
    if damage == "ticks":
        receipt["start_ticks"] = "43"
    if damage == "cwd":
        receipt["process_cwd"] = str(candidate / "src")
    _json(
        data / "runtime/runtime_release_selection.json",
        dict(
            schema="runtime_release_selection_v1",
            release_root=str(previous),
            git_commit=OLD,
            actual_pid_consumed=damage != "actual",
            actual_pid_receipt=receipt,
        ),
    )
    seen = []

    def delta(*args):
        seen.append(args)
        if damage == "code":
            raise ValueError("unreviewed_code")
        return ["reviewed.py"]

    monkeypatch.setattr(handoff, "_verify_entry_code_delta", delta)
    review = dict(
        day=DAY,
        root=previous,
        commit=OLD,
        code_root=candidate,
        code_commit=NEW,
        identity=identity,
    )
    token = handoff._PREDECESSOR_REVIEW.set(None if damage == "no_context" else review)
    try:
        if damage:
            with pytest.raises((ValueError, OSError)):
                handoff.verify_entry_consumer_code(
                    DAY,
                    family="pre_submit_delay",
                    policy_sha="p",
                    expected="source",
                    paths={"entry": "entry.py"},
                    actual="reviewed",
                )
        else:
            result = handoff.verify_entry_consumer_code(
                DAY,
                family="pre_submit_delay",
                policy_sha="p",
                expected="source",
                paths={"entry": "entry.py"},
                actual="reviewed",
            )
            assert (
                result["candidate_pid_consumed"] is False
                and result["policy_effect"] == "unchanged"
            )
            assert seen == [(candidate, NEW, OLD, {"entry": "entry.py"}, "source")]
    finally:
        handoff._PREDECESSOR_REVIEW.reset(token)


@pytest.mark.parametrize("damage", [None, "new_bytes", "old_digest", "new_dirty"])
def test_delay_contract_added_dependencies_keep_exact_original_digest(
    tmp_path, monkeypatch, damage
):
    import hashlib

    original = "src/engine/scalping/a.py"
    added = "src/engine/automation/b.py"
    own = "src/engine/automation/intraday_release_handoff.py"
    before = b"original = 1\n"
    new = b"projection = 2\n"
    verifier = b"# frozen verifier\n"
    sha = lambda b: hashlib.sha256(b).hexdigest()
    expected = sha(
        json.dumps(
            {original: sha(before)}, sort_keys=True, separators=(",", ":")
        ).encode()
    )
    monkeypatch.setattr(
        handoff,
        "REVIEWED_DELAY_CONTRACT_EXTENSIONS",
        {(OLD, expected): {added: sha(new)}},
    )
    for name, raw in [(original, before), (added, new), (own, verifier)]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if damage in ("new_bytes", "new_dirty"):
        (tmp_path / added).write_bytes(new + b"# tamper\n")
    if damage == "old_digest":
        expected = "0" * 64

    def show(command, **kwargs):
        rev, name = command[-1].split(":", 1)
        if name == own:
            return verifier
        if name == original:
            return before
        if rev == OLD:
            raise handoff.subprocess.CalledProcessError(128, command)
        return new + b"# tamper\n" if damage == "new_bytes" else new

    monkeypatch.setattr(handoff.subprocess, "check_output", show)
    if damage:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(
                tmp_path, NEW, OLD, {original: original, added: added}, expected
            )
    else:
        assert handoff._verify_entry_code_delta(
            tmp_path, NEW, OLD, {original: original, added: added}, expected
        ) == [added]


@pytest.mark.parametrize("git_owns_selector", [False, True])
def test_new_index_selector_may_be_absent_only_from_a_preexisting_git_generation(
    tmp_path, monkeypatch, git_owns_selector
):
    import hashlib

    trigger = "src/engine/scalping/fixture.py"
    selector = "src/engine/automation/main_trailing_source_reuse.py"
    own = "src/engine/automation/intraday_release_handoff.py"
    raw = b"original=1\n"
    verifier = b"# frozen\n"
    sha = lambda value: hashlib.sha256(value).hexdigest()
    for name, value in ((trigger, raw), (own, verifier)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    variant = dict(
        selector_path=selector,
        selector_sha256=sha(b"new helper"),
        dependencies={trigger: sha(raw), selector: sha(b"new helper")},
        contract_extensions={},
    )
    monkeypatch.setattr(
        handoff,
        "REVIEWED_TRAILING_REUSE_DEPENDENCY_VARIANTS",
        {(trigger, sha(raw)): variant},
    )
    monkeypatch.setattr(
        handoff,
        "REVIEWED_HOLDING_RESEARCH_DEPENDENCIES",
        {trigger: {sha(raw): {trigger: sha(raw)}}},
    )

    def show(command, **kwargs):
        name = command[-1].split(":", 1)[1]
        if name == selector:
            if git_owns_selector:
                return b"new helper"
            raise handoff.subprocess.CalledProcessError(128, command)
        return verifier if name == own else raw

    monkeypatch.setattr(handoff.subprocess, "check_output", show)
    expected = sha(
        json.dumps({trigger: sha(raw)}, sort_keys=True, separators=(",", ":")).encode()
    )
    if git_owns_selector:
        with pytest.raises(ValueError, match="reviewed_dependency_missing"):
            handoff._verify_entry_code_delta(
                tmp_path, NEW, OLD, {trigger: trigger}, expected
            )
    else:
        assert (
            handoff._verify_entry_code_delta(
                tmp_path, NEW, OLD, {trigger: trigger}, expected
            )
            == []
        )


@pytest.fixture
def completed_research_git_candidate(tmp_path):
    """Real Git objects bind the approved quantity-history generation."""
    import hashlib
    import io
    import os
    import subprocess
    import tarfile
    from src.engine.scalping import main_stop_policy as stop
    from src.engine.scalping import holding_vote_experiment as holding
    from src.engine.scalping import pre_submit_delay_initial_policy as delay

    canonical = Path(handoff.__file__).resolve().parents[3]
    root = tmp_path / "candidate"
    subprocess.run(
        ["git", "clone", "--shared", "--no-checkout", "-q", str(canonical), str(root)],
        check=True,
    )
    own = "src/engine/automation/intraday_release_handoff.py"
    handler = "src/engine/sniper_state_handlers.py"
    # Approval belongs to this immutable generation. A later import/logging
    # cleanup is a new candidate, not an already issued production handoff.
    approved = "e7f4e2e8fb8c76ef29f389cd1274fa0bbff22597"
    handler_bytes = subprocess.check_output(
        ["git", "-C", str(canonical), "show", approved + ":" + handler]
    )
    variant = handoff.REVIEWED_QUANTITY_EXCLUSIONS_DEPENDENCY_VARIANTS[
        (handler, hashlib.sha256(handler_bytes).hexdigest())
    ]
    dependencies = variant["dependencies"]
    assert len(dependencies) == 95
    inventories = {
        "main_stop": {key: "src/engine/" + key for key in stop.implementation_paths()},
        "holding_vote": {
            key: "src/engine/" + key
            for key in holding._code_paths()
            if key
            not in {
                "scalping/holding_decision_context.py",
                "scalping/ai_market_snapshot.py",
            }
        },
        "pre_submit_delay": {key: key for key in delay.CONTRACT_PATHS},
    }
    names = {
        own,
        *dependencies,
        *(name for paths in inventories.values() for name in paths.values()),
    }
    archive = subprocess.check_output(
        [
            "git",
            "-C",
            str(canonical),
            "archive",
            approved,
            *sorted({os.path.normpath(name) for name in names}),
        ]
    )
    with tarfile.open(fileobj=io.BytesIO(archive)) as sources:
        for name in names:
            raw = sources.extractfile(os.path.normpath(name)).read()
            if name in dependencies:
                assert hashlib.sha256(raw).hexdigest() == dependencies[name]
            if name == own:
                raw = (canonical / name).read_bytes()
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    assert handoff._sha(root / variant["selector_path"]) == variant["selector_sha256"]
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            "--force",
            *sorted({os.path.normpath(n) for n in names}),
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "frozen integrated native source fixture",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    digests = dict(
        main_stop="687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533",
        holding_vote="6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112",
        pre_submit_delay="bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
    )
    return root, commit, inventories, digests


@pytest.fixture
def cleanup_git_candidate(completed_research_git_candidate):
    import subprocess

    canonical = Path(handoff.__file__).resolve().parents[3]
    root, _, inventories, digests = completed_research_git_candidate
    names = (
        "src/engine/kiwoom_sniper_v2.py",
        "src/engine/ai_engine_openai.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/sniper_condition_handlers.py",
        "src/engine/sniper_overnight_gatekeeper.py",
        "src/engine/infrastructure/startup_validation_code_context.py",
        "src/engine/scalping/reversal_auxiliary_next_session.py",
    )
    for name in names:
        (root / name).write_bytes(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "show",
                    "34798c60c43984ab9fb97b07e224f9a29883503d:" + name,
                ]
            )
        )
    subprocess.run(["git", "-C", str(root), "add", *names], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "reviewed cleanup source generation",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    return root, commit, inventories, digests


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
def test_cleanup_preserves_original_policy_digest(cleanup_git_candidate, family):
    root, commit, inventories, digests = cleanup_git_candidate
    changed = handoff._verify_entry_code_delta(
        root,
        commit,
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        inventories[family],
        digests[family],
    )
    assert "src/engine/sniper_state_handlers.py" in changed


@pytest.mark.parametrize(
    "source",
    [
        "src/engine/kiwoom_sniper_v2.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/ai_engine_openai.py",
        "src/engine/sniper_condition_handlers.py",
        "src/engine/sniper_overnight_gatekeeper.py",
        "src/engine/scalping/initial_quantity_monitor_projection.py",
        "src/engine/infrastructure/startup_validation_code_context.py",
        "src/engine/scalping/reversal_auxiliary_next_session.py",
    ],
)
@pytest.mark.parametrize("fault", ["changed", "missing"])
def test_cleanup_rejects_unreviewed_or_missing_dependency(
    cleanup_git_candidate, source, fault
):
    import subprocess

    root, commit, inventories, digests = cleanup_git_candidate
    path = root / source
    if fault == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b"\nUNREVIEWED = True\n")
        subprocess.run(["git", "-C", str(root), "add", source], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.name=fixture",
                "-c",
                "user.email=fixture@example.test",
                "commit",
                "-qm",
                "unreviewed source",
            ],
            check=True,
        )
        commit = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    with pytest.raises(ValueError):
        handoff._verify_entry_code_delta(
            root,
            commit,
            "7f2552aedde8fec6ef904a43105827907e50dfc8",
            inventories["pre_submit_delay"],
            digests["pre_submit_delay"],
        )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
def test_completed_research_preserves_original_policy_digest_with_real_git(
    completed_research_git_candidate, family
):
    root, commit, inventories, digests = completed_research_git_candidate
    before = {str(p): handoff._sha(p) for p in (root / "src").rglob("*.py")}
    changed = handoff._verify_entry_code_delta(
        root,
        commit,
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        inventories[family],
        digests[family],
    )
    assert "src/engine/sniper_state_handlers.py" in changed
    if family == "main_stop":
        assert len(inventories[family]) == 44
        extensions = handoff.REVIEWED_DELAY_CONTRACT_EXTENSIONS[
            ("7f2552aedde8fec6ef904a43105827907e50dfc8", digests[family])
        ]
        assert len(extensions) == 27 and set(extensions) <= set(changed)
        assert len(inventories[family]) - len(extensions) == 17
    if family == "holding_vote":
        extensions = handoff.REVIEWED_DELAY_CONTRACT_EXTENSIONS[
            ("7f2552aedde8fec6ef904a43105827907e50dfc8", digests[family])
        ]
        assert len(inventories[family]) == 23
        assert set(extensions) == {"src/engine/lifecycle/research_input_budget.py"}
        assert len(inventories[family]) - len(extensions) == 22
        assert set(extensions) <= set(changed)
    assert before == {str(p): handoff._sha(p) for p in (root / "src").rglob("*.py")}


@pytest.mark.parametrize(
    "source",
    [
        "src/engine/scalping/main_stop_runtime_source.py",
        "src/engine/lifecycle/holding_research_cost.py",
        "src/engine/infrastructure/main_prompt_policy_loading.py",
        "src/engine/lifecycle/research_input_budget.py",
    ],
)
@pytest.mark.parametrize(
    "fault",
    [
        "changed_committed",
        "changed_dirty",
        "git_object_changed",
        "missing",
        "symlink",
        "parent_symlink",
    ],
)
def test_completed_research_rejects_changed_or_unbound_transitive_source(
    completed_research_git_candidate, source, fault
):
    import subprocess

    root, commit, inventories, digests = completed_research_git_candidate
    path = root / source
    if fault in {"changed_committed", "changed_dirty", "git_object_changed"}:
        original = path.read_bytes()
        path.write_bytes(original + b"\nUNREVIEWED = True\n")
        if fault in {"changed_committed", "git_object_changed"}:
            subprocess.run(["git", "-C", str(root), "add", source], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=fixture",
                    "-c",
                    "user.email=fixture@example.test",
                    "commit",
                    "-qm",
                    "unreviewed source change",
                ],
                check=True,
            )
            commit = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
            ).strip()
            if fault == "git_object_changed":
                path.write_bytes(original)
    elif fault == "missing":
        path.unlink()
    elif fault == "symlink":
        saved = path.with_suffix(".saved")
        path.rename(saved)
        path.symlink_to(saved)
    else:
        directory = path.parent
        saved = directory.with_name(directory.name + "_saved")
        directory.rename(saved)
        directory.symlink_to(saved, target_is_directory=True)
    # Delay directly owns budget.py; the remaining omitted dependencies are
    # enforced by its exact handler closure. Both reject different Git bytes.
    error = None
    if fault == "git_object_changed":
        error = (
            "entry_consumer_dirty_release"
            if source in inventories["pre_submit_delay"].values()
            else "reviewed_dependency_dirty"
        )
    with pytest.raises(ValueError, match=error):
        handoff._verify_entry_code_delta(
            root,
            commit,
            "7f2552aedde8fec6ef904a43105827907e50dfc8",
            inventories["pre_submit_delay"],
            digests["pre_submit_delay"],
        )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote"])
def test_shared_budget_bytes_invalidate_current_native_policy_generation(
    tmp_path, monkeypatch, family
):
    """The equal-current-digest path also binds Claim; no compatibility receipt is needed."""
    from src.engine.scalping import main_stop_policy as stop
    from src.engine.scalping import holding_vote_experiment as holding

    module = stop if family == "main_stop" else holding
    paths = (
        stop.implementation_paths() if family == "main_stop" else holding._code_paths()
    )
    code = stop.implementation_sha if family == "main_stop" else holding.code_sha
    engine = Path(module.__file__).parents[1]
    target = tmp_path / "src/engine"
    for name in paths:
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((engine / name).read_bytes())
    assert paths.count("lifecycle/research_input_budget.py") == 1
    monkeypatch.setattr(
        module, "__file__", str(target / "scalping" / Path(module.__file__).name)
    )
    before = code()
    budget = target / "lifecycle/research_input_budget.py"
    original = budget.read_bytes()
    budget.write_bytes(original + b"\n# Different admitted memory generation.\n")
    assert code() != before
    budget.write_bytes(original)
    assert code() == before


@pytest.mark.parametrize("family", ["main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", ["missing_extension", "wrong_hash", "wrong_family"])
def test_budget_extension_cannot_change_the_original_policy_inventory(
    completed_research_git_candidate, monkeypatch, family, fault
):
    root, commit, inventories, digests = completed_research_git_candidate
    origin = "7f2552aedde8fec6ef904a43105827907e50dfc8"
    key = (origin, digests[family])
    name = "src/engine/lifecycle/research_input_budget.py"
    trigger = "src/engine/sniper_state_handlers.py"
    variant = handoff.REVIEWED_QUANTITY_EXCLUSIONS_DEPENDENCY_VARIANTS[
        (trigger, handoff._sha(root / trigger))
    ]
    # The fixture owns the current complete generation, including its family
    # extensions. Mutating a historical fallback would not exercise this gate.
    extensions = dict(variant["contract_extensions"][key])
    paths = dict(inventories[family])
    expected = digests[family]
    if fault == "missing_extension":
        extensions.pop(name)
    elif fault == "wrong_hash":
        extensions[name] = "0" * 64
    elif fault == "wrong_family":
        expected = digests["holding_vote" if family == "main_stop" else "main_stop"]
    monkeypatch.setitem(variant["contract_extensions"], key, extensions)
    with pytest.raises(ValueError):
        handoff._verify_entry_code_delta(root, commit, origin, paths, expected)


def test_cleanup_closure_retains_all_predecessor_dependencies():
    trigger = "src/engine/sniper_state_handlers.py"
    parent = handoff.REVIEWED_QUANTITY_EXCLUSIONS_DEPENDENCY_VARIANTS[
        (trigger, "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38")
    ]
    child = handoff.REVIEWED_CLEANUP_DEPENDENCY_VARIANTS[
        (trigger, handoff.REVIEWED_CLEANUP_HASHES[trigger])
    ]
    assert len(parent["dependencies"]) == 95 and len(child["dependencies"]) == 98
    assert child["dependencies"] == {
        **parent["dependencies"],
        **handoff.REVIEWED_CLEANUP_HASHES,
    }
    assert parent["dependencies"][trigger] != child["dependencies"][trigger]
    assert child["contract_extensions"] is not parent["contract_extensions"]

    for key, parent in handoff.REVIEWED_SQLITE_LIFECYCLE_DEPENDENCY_VARIANTS.items():
        child = handoff.REVIEWED_CLEAN_SQLITE_DEPENDENCY_VARIANTS[key]
        assert child["dependencies"] == {
            **parent["dependencies"],
            **handoff.REVIEWED_RETIRED_REVIEW_HASHES,
        }
        assert child["contract_extensions"] == parent["contract_extensions"]
    for key, parent in handoff.REVIEWED_PRODUCT_INTAKE_DEPENDENCY_VARIANTS.items():
        assert handoff.REVIEWED_RETIRED_REVIEW_DEPENDENCY_VARIANTS[key][
            "dependencies"
        ] == {**parent["dependencies"], **handoff.REVIEWED_RETIRED_REVIEW_HASHES}


@pytest.fixture
def avg_down_input_git_candidate(cleanup_git_candidate):
    import subprocess
    from src.engine.scalping.holding_vote_experiment import _code_paths

    canonical = Path(handoff.__file__).resolve().parents[3]
    root, _, inventories, digests = cleanup_git_candidate
    for name in handoff.REVIEWED_AVG_DOWN_INPUT_HASHES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            subprocess.check_output(
                ["git", "-C", str(canonical), "show", "a98ff7a95:" + name]
            )
        )
    # This older immutable release already contained the report. The new
    # selector must see its original bytes, not a synthetic missing module or
    # this working tree's newer report implementation.
    original_readers = tuple(
        dict.fromkeys(
            (
                *handoff.REVIEWED_POSTCLOSE_READER_HASHES,
                *handoff.REVIEWED_STOP_SHARED_POSITION_HASHES,
            )
        )
    )
    for name in original_readers:
        (root / name).write_bytes(
            subprocess.check_output(
                ["git", "-C", str(canonical), "show", "deb996a22:" + name]
            )
        )
    inventories["holding_vote"] = {key: "src/engine/" + key for key in _code_paths()}
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            "--force",
            *handoff.REVIEWED_AVG_DOWN_INPUT_HASHES,
            *original_readers,
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "reviewed AVG_DOWN input and SOR integration",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    return root, commit, inventories, digests


@pytest.mark.parametrize(
    "origin",
    [
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        "8940ea4ad0d3b64d30f67f986a75715ee24c1d95",
    ],
)
@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "input_changed", "extension_missing"])
def test_avg_down_input_handoff_preserves_policy_and_binds_new_inputs(
    avg_down_input_git_candidate, monkeypatch, family, fault, origin
):
    root, commit, inventories, digests = avg_down_input_git_candidate
    if origin.startswith("8940"):
        digests = dict(
            main_stop="12103eeb4e6c84bdef55013e914cd64784cce0650b045e6f25c05a8101a97b45",
            holding_vote="c34bc30c734591c1c97c0ed770744c273e206de14dbd0b02382ef71a88265693",
            pre_submit_delay="90572ff4ba7dbbff01f559e353f4f2a9cc910d1b068880db459749b918a267de",
        )
    if fault == "input_changed":
        path = root / "src/engine/scalping/holding_decision_context.py"
        path.write_bytes(path.read_bytes() + b"\nUNREVIEWED = True\n")
    elif fault == "extension_missing":
        trigger = "src/engine/sniper_state_handlers.py"
        variant = handoff.REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS[
            (trigger, handoff._sha(root / trigger))
        ]
        key = (origin, digests[family])
        if key in variant["contract_extensions"]:
            extensions = dict(variant["contract_extensions"][key])
            extensions.pop(next(iter(extensions)))
            monkeypatch.setitem(variant["contract_extensions"], key, extensions)
        else:
            digests[family] = "0" * 64
    if fault:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(
                root, commit, origin, inventories[family], digests[family]
            )
    else:
        changed = handoff._verify_entry_code_delta(
            root, commit, origin, inventories[family], digests[family]
        )
        assert "src/engine/sniper_state_handlers.py" in changed
        if family == "holding_vote":
            assert "src/engine/scalping/holding_decision_context.py" in changed
            assert "src/engine/scalping/ai_market_snapshot.py" in changed


@pytest.mark.parametrize(
    "generation",
    [
        "producer_census",
        "complete_consumers",
        "prefix_code_binding",
        "late_cost_revision",
        "postclose_readers",
        "archive_authority",
        "legacy_archive_authority",
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    ],
)
@pytest.mark.parametrize(
    "origin",
    [
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        "8940ea4ad0d3b64d30f67f986a75715ee24c1d95",
    ],
)
@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "changed_report", "missing_archive", "unrelated_dependency"]
)
def test_completion_census_handoff_binds_exact_complete_generation(
    avg_down_input_git_candidate, origin, family, fault, generation
):
    import hashlib
    import subprocess

    root, _, inventories, digests = avg_down_input_git_candidate
    canonical = Path(handoff.__file__).resolve().parents[3]
    hashes = (
        handoff.REVIEWED_COMPLETION_CENSUS_HASHES
        if generation == "producer_census"
        else handoff.REVIEWED_COMPLETION_CONSUMER_HASHES
    )
    if generation in {
        "prefix_code_binding",
        "late_cost_revision",
        "postclose_readers",
        "archive_authority",
        "legacy_archive_authority",
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_PREFIX_PRODUCER_HASHES}
    if generation in {
        "late_cost_revision",
        "postclose_readers",
        "archive_authority",
        "legacy_archive_authority",
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_LATE_COST_HASHES}
    if generation in {
        "postclose_readers",
        "archive_authority",
        "legacy_archive_authority",
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_POSTCLOSE_READER_HASHES}
    if generation in {
        "archive_authority",
        "legacy_archive_authority",
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_ARCHIVE_AUTHORITY_HASHES}
    if generation in {
        "legacy_archive_authority",
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_LEGACY_ARCHIVE_AUTHORITY_HASHES}
    if generation in {
        "auxiliary_data_root",
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_AUXILIARY_DATA_ROOT_HASHES}
    if generation in {
        "completed_offline",
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_COMPLETED_OFFLINE_HASHES}
    if generation in {
        "completed_empty",
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_COMPLETED_EMPTY_HASHES}
    if generation in {
        "native_empty_cohorts",
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_NATIVE_EMPTY_HASHES}
    if generation in {
        "assembler_budget",
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_ASSEMBLER_BUDGET_HASHES}
    if generation in {
        "calendar_physical",
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_CALENDAR_PHYSICAL_HASHES}
    if generation in {
        "stop_shared_position",
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_STOP_SHARED_POSITION_HASHES}
    if generation in {
        "stop_forward_stream",
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_STOP_FORWARD_STREAM_HASHES}
    if generation in {
        "stop_indexed_votes",
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes = {**hashes, **handoff.REVIEWED_STOP_INDEXED_VOTE_HASHES}
    if generation in {
        "pre_entry_observer",
        "vote_metadata",
        "broker_custody",
        "frozen_input",
    }:
        hashes.update(handoff.REVIEWED_PRE_ENTRY_OBSERVER_HASHES)
    if generation in {"vote_metadata", "broker_custody", "frozen_input"}:
        hashes.update(handoff.REVIEWED_VOTE_METADATA_HASHES)
    if generation in {"broker_custody", "frozen_input"}:
        hashes.update(handoff.REVIEWED_BROKER_CUSTODY_HASHES)
    if generation == "frozen_input":
        hashes.update(handoff.REVIEWED_FROZEN_INPUT_HASHES)
    revision = (
        "3fde8b0e6"
        if generation == "stop_forward_stream"
        else (
            "dd44b63cb"
            if generation == "stop_shared_position"
            else (
                "30210fff6"
                if generation == "calendar_physical"
                else (
                    "ded4a2968"
                    if generation == "assembler_budget"
                    else (
                        "a10f6d013"
                        if generation == "native_empty_cohorts"
                        else (
                            "260fe4848"
                            if generation == "completed_empty"
                            else (
                                "ca557bc6f"
                                if generation == "completed_offline"
                                else (
                                    "146ca0b2b"
                                    if generation == "auxiliary_data_root"
                                    else (
                                        "037b23a7c"
                                        if generation == "legacy_archive_authority"
                                        else (
                                            "6c9117791"
                                            if generation == "archive_authority"
                                            else (
                                                "9e5e7ce56"
                                                if generation == "postclose_readers"
                                                else (
                                                    "a5831f833"
                                                    if generation == "producer_census"
                                                    else (
                                                        "7df7ea3b9"
                                                        if generation
                                                        == "late_cost_revision"
                                                        else (
                                                            "082234567"
                                                            if generation
                                                            == "prefix_code_binding"
                                                            else "bf8465b5d"
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    for name, expected in hashes.items():
        raw = (
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "show",
                    (
                        "04be13cf1"
                        if name in handoff.REVIEWED_FROZEN_INPUT_HASHES
                        else "e3cb1d9ca"
                    )
                    + ":"
                    + name,
                ]
            )
            if generation == "frozen_input"
            else (
                subprocess.check_output(
                    ["git", "-C", str(canonical), "show", "a7c0b0dc5:" + name]
                )
                if generation == "broker_custody"
                else (
                    subprocess.check_output(
                        ["git", "-C", str(canonical), "show", "4b278bbb3:" + name]
                    )
                    if generation == "vote_metadata"
                    else (
                        subprocess.check_output(
                            ["git", "-C", str(canonical), "show", "a1748b409:" + name]
                        )
                        if generation == "pre_entry_observer"
                        else (
                            subprocess.check_output(
                                [
                                    "git",
                                    "-C",
                                    str(canonical),
                                    "show",
                                    "ab1c46633:" + name,
                                ]
                            )
                            if generation == "stop_indexed_votes"
                            else subprocess.check_output(
                                [
                                    "git",
                                    "-C",
                                    str(canonical),
                                    "show",
                                    revision + ":" + name,
                                ]
                            )
                        )
                    )
                )
            )
        )
        assert hashlib.sha256(raw).hexdigest() == expected, name
        (root / name).write_bytes(raw)
    for name in handoff.REVIEWED_POSTCLOSE_READER_HASHES:
        if (
            generation
            not in {
                "legacy_archive_authority",
                "auxiliary_data_root",
                "completed_offline",
                "completed_empty",
                "native_empty_cohorts",
                "assembler_budget",
                "calendar_physical",
                "stop_shared_position",
                "stop_forward_stream",
                "stop_indexed_votes",
                "pre_entry_observer",
                "vote_metadata",
                "broker_custody",
                "frozen_input",
            }
            and name not in hashes
        ):
            (root / name).write_bytes(
                subprocess.check_output(
                    ["git", "-C", str(canonical), "show", revision + ":" + name]
                )
            )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            *hashes,
            *handoff.REVIEWED_POSTCLOSE_READER_HASHES,
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "reviewed completion census source generation",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if origin.startswith("8940"):
        digests = dict(
            main_stop="12103eeb4e6c84bdef55013e914cd64784cce0650b045e6f25c05a8101a97b45",
            holding_vote="c34bc30c734591c1c97c0ed770744c273e206de14dbd0b02382ef71a88265693",
            pre_submit_delay="90572ff4ba7dbbff01f559e353f4f2a9cc910d1b068880db459749b918a267de",
        )
    if fault == "missing_archive":
        (root / "src/engine/log_archive_service.py").unlink()
    elif fault:
        name = (
            "src/engine/sniper_trade_review_report.py"
            if fault == "changed_report"
            else "src/engine/scalping/holding_decision_context.py"
        )
        path = root / name
        path.write_bytes(path.read_bytes() + b"\nUNREVIEWED = True\n")
    if fault:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(
                root, commit, origin, inventories[family], digests[family]
            )
    else:
        handoff._verify_entry_code_delta(
            root, commit, origin, inventories[family], digests[family]
        )


@pytest.mark.parametrize(
    "origin",
    [
        "9e5e7ce56d4bf66be210a74af0b867c6fd6a7928",
        "6c91177918f1479bb63adaf42c924c0129508d7d",
    ],
)
@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
def test_archive_authority_successor_accepts_the_issued_full_reader_origin(
    avg_down_input_git_candidate, family, origin
):
    import hashlib, json, os, subprocess

    root, _, inventories, _ = avg_down_input_git_candidate
    canonical = Path(handoff.__file__).resolve().parents[3]
    inventory = inventories[family]
    names = (
        set(inventory.values())
        | set(handoff.REVIEWED_AVG_DOWN_INPUT_HASHES)
        | set(handoff.REVIEWED_POSTCLOSE_READER_HASHES)
    )
    for variant in handoff.REVIEWED_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS.values():
        names.update(variant["dependencies"])
    original = {}
    for name in names:
        normalized = os.path.normpath(name)
        raw = subprocess.check_output(
            ["git", "-C", str(canonical), "show", origin + ":" + normalized]
        )
        original[normalized] = hashlib.sha256(raw).hexdigest()
        if normalized in handoff.REVIEWED_ARCHIVE_AUTHORITY_HASHES:
            raw = subprocess.check_output(
                ["git", "-C", str(canonical), "show", "6c9117791:" + normalized]
            )
        path = root / normalized
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    expected = hashlib.sha256(
        json.dumps(
            {key: original[os.path.normpath(name)] for key, name in inventory.items()},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    subprocess.run(
        ["git", "-C", str(root), "add", *map(os.path.normpath, names)], check=True
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "archive authority successor of issued reader generation",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    handoff._verify_entry_code_delta(root, commit, origin, inventory, expected)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "generation,reader_path,fault",
    [
        (generation, path, fault)
        for generation in (
            "source_reader",
            "source_integration",
            "original_gap",
            "incident_order",
            "product_intake",
            "sqlite_lifecycle",
            "retired_review",
            "clean_sqlite",
            "delay_cleanup",
        )
        for path in (
            tuple(handoff.REVIEWED_DELAY_CLEANUP_HASHES)
            if generation == "delay_cleanup"
            else (
                tuple(
                    {
                        **handoff.REVIEWED_SQLITE_LIFECYCLE_HASHES,
                        **handoff.REVIEWED_RETIRED_REVIEW_HASHES,
                    }
                )
                if generation == "clean_sqlite"
                else (
                    tuple(handoff.REVIEWED_RETIRED_REVIEW_HASHES)
                    if generation == "retired_review"
                    else (
                        tuple(handoff.REVIEWED_SQLITE_LIFECYCLE_HASHES)
                        if generation == "sqlite_lifecycle"
                        else (
                            tuple(handoff.REVIEWED_PRODUCT_INTAKE_HASHES)
                            if generation == "product_intake"
                            else (
                                (
                                    "src/engine/monitoring/submission_bottleneck_monitor.py",
                                )
                                if generation == "incident_order"
                                else (
                                    (
                                        "src/engine/scalping/holding_profit_exit_semantics.py",
                                    )
                                    if generation == "original_gap"
                                    else (
                                        "src/engine/lifecycle/research_json_stream.py",
                                        "src/engine/automation/main_startup_validation.py",
                                        "src/engine/automation/next_preopen_readiness.py",
                                        *(
                                            [
                                                "src/engine/infrastructure/startup_validation_code_context.py"
                                            ]
                                            if generation == "source_integration"
                                            else []
                                        ),
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        for fault in (
            [None, "missing", "dirty", "committed_change"]
            + (
                ["parent_mix"]
                if generation
                in (
                    "sqlite_lifecycle",
                    "retired_review",
                    "clean_sqlite",
                    "delay_cleanup",
                )
                else []
            )
        )
    ],
)
def test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
    tmp_path, family, fault, reader_path, generation, policy_origin=None
):
    postclose_recovery = generation == "postclose_recovery"
    p5_ancestry = generation in ("p5_ancestry", "postclose_recovery")
    operator_market = generation in (
        "operator_market",
        "p5_ancestry",
        "postclose_recovery",
    )
    if p5_ancestry:
        generation = "operator_market"
    issued_post_sell_source = generation == "post_sell_source"
    post_sell_source = generation in ("post_sell_source", "operator_market")
    issued_holding_input = generation == "holding_input"
    holding_input = generation in (
        "holding_input",
        "post_sell_source",
        "operator_market",
    )
    nonfixed_capacity = generation in (
        "nonfixed_capacity",
        "holding_input",
        "post_sell_source",
        "operator_market",
    )
    issued_nonfixed = generation == "nonfixed_capacity"
    prepared_stage = generation in (
        "quantity_stage",
        "nonfixed_capacity",
        "holding_input",
        "post_sell_source",
        "operator_market",
    )
    if prepared_stage:
        generation = "quantity_capture"
    import hashlib
    import os
    import subprocess
    from src.engine.scalping import main_stop_policy as stop
    from src.engine.scalping import holding_vote_experiment as holding
    from src.engine.scalping import pre_submit_delay_initial_policy as delay

    canonical = Path(handoff.__file__).resolve().parents[3]
    origin = policy_origin or "ab1c46633e638658721ec4bdab611bd389451985"
    inventories = {
        "main_stop": {key: "src/engine/" + key for key in stop.implementation_paths()},
        "holding_vote": {key: "src/engine/" + key for key in holding._code_paths()},
        "pre_submit_delay": {name: name for name in delay.CONTRACT_PATHS},
    }
    inventory = inventories[family]
    root = tmp_path / "candidate"
    subprocess.run(
        [
            "git",
            "clone",
            "--shared",
            "--no-checkout",
            "--single-branch",
            "--no-tags",
            "-q",
            str(canonical),
            str(root),
        ],
        check=True,
    )
    names = {os.path.normpath(name) for name in inventory.values()}
    # Historical releases contain the profile selectors as well as policy
    # inputs. Preserve their original bytes: a sparse fixture cannot choose
    # between later profiles that share an unchanged dependency trigger.
    for table_name, variants in vars(handoff).items():
        if (
            table_name.startswith("REVIEWED_")
            and table_name.endswith("_VARIANTS")
            and isinstance(variants, dict)
        ):
            for variant in variants.values():
                if isinstance(variant, dict):
                    names.update(
                        variant[key]
                        for key in ("selector_path", "additional_selector_path")
                        if key in variant
                    )
    for variant in handoff.REVIEWED_BROKER_CUSTODY_DEPENDENCY_VARIANTS.values():
        names.update(variant["dependencies"])
    names.update(handoff.REVIEWED_SOURCE_READER_HASHES)
    if generation != "source_reader":
        names.update(handoff.REVIEWED_SOURCE_INTEGRATION_HASHES)
    if generation in (
        "original_gap",
        "incident_order",
        "product_intake",
        "sqlite_lifecycle",
        "retired_review",
        "clean_sqlite",
        "delay_cleanup",
        "role_latency",
        "startup_budget",
        "delay_shutdown",
        "routed_reuse",
        "source_epoch",
        "closed_observer",
        "postclose_repair",
        "logical_pipeline",
        "historical_resolution",
        "finalization_health",
        "native_invalidation",
        "fixed_wait",
        "entry_receipt",
        "buy_identity",
        "collector_close",
        "collector_first_transition",
        "quantity_capture",
    ):
        names.update(handoff.REVIEWED_ORIGINAL_GAP_HASHES)
    if generation in (
        "product_intake",
        "sqlite_lifecycle",
        "retired_review",
        "clean_sqlite",
        "delay_cleanup",
        "role_latency",
        "startup_budget",
        "delay_shutdown",
        "routed_reuse",
        "source_epoch",
        "closed_observer",
        "postclose_repair",
        "logical_pipeline",
        "historical_resolution",
        "finalization_health",
        "native_invalidation",
        "fixed_wait",
        "entry_receipt",
        "buy_identity",
        "collector_close",
        "collector_first_transition",
        "quantity_capture",
    ):
        names.update(handoff.REVIEWED_PRODUCT_INTAKE_HASHES)
    if generation in ("sqlite_lifecycle", "clean_sqlite"):
        names.update(handoff.REVIEWED_SQLITE_LIFECYCLE_HASHES)
    if generation in (
        "retired_review",
        "clean_sqlite",
        "delay_cleanup",
        "role_latency",
        "startup_budget",
        "delay_shutdown",
        "routed_reuse",
        "source_epoch",
        "closed_observer",
        "postclose_repair",
        "logical_pipeline",
        "historical_resolution",
        "finalization_health",
        "native_invalidation",
        "fixed_wait",
        "entry_receipt",
        "buy_identity",
        "collector_close",
        "collector_first_transition",
        "quantity_capture",
    ):
        names.update(handoff.REVIEWED_RETIRED_REVIEW_HASHES)
    if generation in (
        "delay_cleanup",
        "role_latency",
        "startup_budget",
        "delay_shutdown",
        "routed_reuse",
        "source_epoch",
        "closed_observer",
        "postclose_repair",
        "logical_pipeline",
        "historical_resolution",
        "finalization_health",
        "native_invalidation",
        "fixed_wait",
        "entry_receipt",
        "buy_identity",
        "collector_close",
        "collector_first_transition",
        "quantity_capture",
    ):
        for variant in (
            handoff.REVIEWED_P5_ANCESTRY_DEPENDENCY_VARIANTS
            if p5_ancestry
            else (
                handoff.REVIEWED_OPERATOR_MARKET_DEPENDENCY_VARIANTS
                if operator_market
                else (
                    handoff.REVIEWED_POST_SELL_SOURCE_DEPENDENCY_VARIANTS
                    if post_sell_source
                    else (
                        handoff.REVIEWED_HOLDING_INPUT_DEPENDENCY_VARIANTS
                        if holding_input
                        else (
                            handoff.REVIEWED_NONFIXED_CAPACITY_DEPENDENCY_VARIANTS
                            if nonfixed_capacity
                            else (
                                handoff.REVIEWED_QUANTITY_STAGE_DEPENDENCY_VARIANTS
                                if prepared_stage
                                else (
                                    handoff.REVIEWED_QUANTITY_CAPTURE_DEPENDENCY_VARIANTS
                                    if generation == "quantity_capture"
                                    else (
                                        handoff.REVIEWED_COLLECTOR_FIRST_TRANSITION_DEPENDENCY_VARIANTS
                                        if generation == "collector_first_transition"
                                        else (
                                            handoff.REVIEWED_COLLECTOR_CLOSE_DEPENDENCY_VARIANTS
                                            if generation == "collector_close"
                                            else (
                                                handoff.REVIEWED_BUY_IDENTITY_DEPENDENCY_VARIANTS
                                                if generation == "buy_identity"
                                                else (
                                                    handoff.REVIEWED_ENTRY_RECEIPT_DEPENDENCY_VARIANTS
                                                    if generation == "entry_receipt"
                                                    else (
                                                        handoff.REVIEWED_FIXED_WAIT_DEPENDENCY_VARIANTS
                                                        if generation == "fixed_wait"
                                                        else (
                                                            handoff.REVIEWED_NATIVE_INVALIDATION_DEPENDENCY_VARIANTS
                                                            if generation
                                                            == "native_invalidation"
                                                            else (
                                                                handoff.REVIEWED_FINALIZATION_HEALTH_DEPENDENCY_VARIANTS
                                                                if generation
                                                                == "finalization_health"
                                                                else (
                                                                    handoff.REVIEWED_HISTORICAL_RESOLUTION_DEPENDENCY_VARIANTS
                                                                    if generation
                                                                    == "historical_resolution"
                                                                    else (
                                                                        handoff.REVIEWED_LOGICAL_PIPELINE_DEPENDENCY_VARIANTS
                                                                        if generation
                                                                        == "logical_pipeline"
                                                                        else (
                                                                            handoff.REVIEWED_POSTCLOSE_REPAIR_DEPENDENCY_VARIANTS
                                                                            if generation
                                                                            == "postclose_repair"
                                                                            else (
                                                                                handoff.REVIEWED_CLOSED_OBSERVER_DEPENDENCY_VARIANTS
                                                                                if generation
                                                                                == "closed_observer"
                                                                                else (
                                                                                    handoff.REVIEWED_SOURCE_EPOCH_DEPENDENCY_VARIANTS
                                                                                    if generation
                                                                                    == "source_epoch"
                                                                                    else (
                                                                                        handoff.REVIEWED_ROUTED_REUSE_DEPENDENCY_VARIANTS
                                                                                        if generation
                                                                                        == "routed_reuse"
                                                                                        else (
                                                                                            handoff.REVIEWED_DELAY_SHUTDOWN_DEPENDENCY_VARIANTS
                                                                                            if generation
                                                                                            == "delay_shutdown"
                                                                                            else (
                                                                                                handoff.REVIEWED_STARTUP_BUDGET_DEPENDENCY_VARIANTS
                                                                                                if generation
                                                                                                == "startup_budget"
                                                                                                else (
                                                                                                    handoff.REVIEWED_ROLE_LATENCY_DEPENDENCY_VARIANTS
                                                                                                    if generation
                                                                                                    == "role_latency"
                                                                                                    else handoff.REVIEWED_DELAY_CLEANUP_DEPENDENCY_VARIANTS
                                                                                                )
                                                                                            )
                                                                                        )
                                                                                    )
                                                                                )
                                                                            )
                                                                        )
                                                                    )
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ).values():
            names.update(variant["dependencies"])
    names.add("src/engine/automation/intraday_release_handoff.py")
    if generation in ("collector_first_transition", "quantity_capture"):
        names.update(handoff.REVIEWED_DELAY_MACHINE_PARENT_HASHES)
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "show",
                    "75e0fbbf7:" + os.path.normpath(name),
                ]
            )
            if postclose_recovery
            and name != "src/engine/automation/intraday_release_handoff.py"
            else (
                subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(canonical),
                        "show",
                        "e3665f20a:" + os.path.normpath(name),
                    ]
                )
                if p5_ancestry
                and not postclose_recovery
                and name != "src/engine/automation/intraday_release_handoff.py"
                else (
                    subprocess.check_output(
                        [
                            "git",
                            "-C",
                            str(canonical),
                            "show",
                            "b82a84620:" + os.path.normpath(name),
                        ]
                    )
                    if operator_market
                    and not p5_ancestry
                    and name != "src/engine/automation/intraday_release_handoff.py"
                    else (
                        subprocess.check_output(
                            [
                                "git",
                                "-C",
                                str(canonical),
                                "show",
                                "19297ead7:" + os.path.normpath(name),
                            ]
                        )
                        if issued_post_sell_source
                        and name != "src/engine/automation/intraday_release_handoff.py"
                        else (
                            subprocess.check_output(
                                [
                                    "git",
                                    "-C",
                                    str(canonical),
                                    "show",
                                    "0b36f17fc:" + os.path.normpath(name),
                                ]
                            )
                            if issued_holding_input
                            and name
                            != "src/engine/automation/intraday_release_handoff.py"
                            else (
                                subprocess.check_output(
                                    [
                                        "git",
                                        "-C",
                                        str(canonical),
                                        "show",
                                        "eeaed90f6:" + os.path.normpath(name),
                                    ]
                                )
                                if issued_nonfixed
                                and name
                                != "src/engine/automation/intraday_release_handoff.py"
                                else (
                                    (canonical / name).read_bytes()
                                    if nonfixed_capacity
                                    or name
                                    == "src/engine/automation/intraday_release_handoff.py"
                                    else subprocess.check_output(
                                        [
                                            "git",
                                            "-C",
                                            str(canonical),
                                            "show",
                                            (
                                                {
                                                    "quantity_capture": (
                                                        "3b6cfb80b"
                                                        if prepared_stage
                                                        else "4368954cd"
                                                    ),
                                                    "collector_first_transition": "d2e9bedf3",
                                                    "collector_close": "1fd10ef9c",
                                                    "buy_identity": "ea68c5a85",
                                                    "entry_receipt": "d76cbd56d",
                                                    "fixed_wait": "4809d898e",
                                                    "native_invalidation": "193668e7f",
                                                    "finalization_health": "6978f78c1",
                                                    "historical_resolution": "e427676c4",
                                                    "logical_pipeline": "6d259b5a09",
                                                    "postclose_repair": "0cfd32827",
                                                    "closed_observer": "04e19bad0",
                                                    "source_epoch": "88351a078",
                                                    "routed_reuse": "68213dd10",
                                                    "delay_shutdown": "49ef280dc",
                                                    "startup_budget": "105f6f031",
                                                    "role_latency": "6e037d078",
                                                    "source_reader": "0255cb05f",
                                                    "incident_order": "041caf05e",
                                                    "product_intake": "21d822a64",
                                                    "sqlite_lifecycle": "c550a4c43",
                                                    "retired_review": "3d8abd012",
                                                    "clean_sqlite": "0ce816f7c",
                                                    "delay_cleanup": "661260e5f",
                                                }.get(generation, "99c51c85f")
                                            )
                                            + ":"
                                            + os.path.normpath(name),
                                        ]
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    original = {
        key: hashlib.sha256(
            subprocess.check_output(
                ["git", "-C", str(root), "show", origin + ":" + os.path.normpath(name)]
            )
        ).hexdigest()
        for key, name in inventory.items()
    }
    expected = hashlib.sha256(
        json.dumps(original, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    def commit():
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.name=fixture",
                "-c",
                "user.email=fixture@example.test",
                "commit",
                "-qm",
                "source reader generation",
            ],
            check=True,
        )
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()

    revision = commit()
    # Each successor uses one clone per family/fault. Each
    # mutation is isolated and restored before checking the next exact owner.
    handoff._verify_entry_code_delta(root, revision, origin, inventory, expected)
    for reader_name in (
        reader_path if isinstance(reader_path, tuple) else (reader_path,)
    ):
        reader = root / reader_name
        original_bytes = reader.read_bytes()
        if fault == "missing":
            reader.unlink()
        elif fault == "parent_mix":
            parent = (
                "ea68c5a85"
                if generation
                in ("collector_close", "collector_first_transition", "quantity_capture")
                else (
                    "d76cbd56d"
                    if generation == "buy_identity"
                    else (
                        "4809d898e"
                        if generation == "entry_receipt"
                        else (
                            "193668e7f"
                            if generation == "fixed_wait"
                            else (
                                "e0d07d4ab"
                                if generation == "native_invalidation"
                                else (
                                    "e427676c4"
                                    if generation == "finalization_health"
                                    else (
                                        "6d259b5a09"
                                        if generation == "historical_resolution"
                                        else (
                                            "0cfd32827"
                                            if generation == "logical_pipeline"
                                            else (
                                                "04e19bad0"
                                                if generation == "postclose_repair"
                                                else (
                                                    origin
                                                    if generation == "routed_reuse"
                                                    and reader_name
                                                    in handoff.REVIEWED_ROUTED_REUSE_HASHES
                                                    else "21d822a64"
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            if p5_ancestry:
                # The immediate pre-repair file remains an issued profile.
                # An older partial generation must still fail exact binding.
                parent = origin
            reader.write_bytes(
                subprocess.check_output(
                    ["git", "-C", str(canonical), "show", parent + ":" + reader_name]
                )
            )
            revision = commit()
        elif fault:
            reader.write_bytes(reader.read_bytes() + b"\nUNREVIEWED_READER = True\n")
            if fault == "committed_change":
                revision = commit()
        if fault:
            with pytest.raises(ValueError):
                handoff._verify_entry_code_delta(
                    root, revision, origin, inventory, expected
                )
            reader.write_bytes(original_bytes)
            if fault in ("committed_change", "parent_mix"):
                revision = commit()
        handoff._verify_entry_code_delta(root, revision, origin, inventory, expected)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "source",
    [
        *handoff.REVIEWED_DELAY_SHUTDOWN_HASHES,
        "src/engine/monitoring/submission_bottleneck_monitor.py",
    ],
)
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_delay_shutdown_handoff_binds_exact_cleanup_and_prior_generation(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "delay_shutdown"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_startup_budget_handoff_requires_exact_observer_and_predecessors(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        "src/engine/monitoring/submission_bottleneck_monitor.py",
        "startup_budget",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "source",
    [
        "src/engine/ai_engine_openai.py",
        "src/engine/ai/hot_path_ai_dispatcher.py",
        "src/engine/scalping/avg_down_replay_capture.py",
        "src/utils/constants.py",
        "src/engine/scalping/opening_rotation.py",
    ],
)
@pytest.mark.parametrize("fault", [None, "missing", "committed_change", "parent_mix"])
def test_role_latency_handoff_requires_complete_reviewed_group(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "role_latency"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "source",
    [
        *handoff.REVIEWED_ROUTED_REUSE_HASHES,
        *handoff.REVIEWED_DELAY_SHUTDOWN_HASHES,
        "src/engine/monitoring/submission_bottleneck_monitor.py",
    ],
)
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_routed_reuse_handoff_binds_reader_and_shutdown_generation(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "routed_reuse"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_source_epoch_handoff_requires_exact_deployment_owner(tmp_path, family, fault):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        "src/engine/automation/ordered_intraday_deploy.py",
        "source_epoch",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "source,fault",
    [
        (source, fault)
        for source in (
            "src/engine/error_detectors/artifact_freshness.py",
            "src/engine/automation/ordered_intraday_deploy.py",
        )
        for fault in (None, "missing", "dirty", "committed_change", "parent_mix")
        if source.endswith("ordered_intraday_deploy.py") or fault != "parent_mix"
    ],
)
def test_closed_observer_handoff_requires_exact_reader_and_source_epoch(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "closed_observer"
    )


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "midnight",
        "pid_present",
        "inventory_unknown",
        "receipt_pid",
        "receipt_start",
        "heartbeat_pid",
        "heartbeat_start",
        "terminal",
        "unresolved",
        "isolation",
        "stop_clock",
        "eod",
        "eod_date",
        "eod_rows",
        "manifest",
        "handoff",
        "changed_heartbeat",
        "interrupted",
        "interrupted_actor",
        "interrupted_epoch",
        "interrupted_clock",
        "interrupted_manifest",
        "interrupted_changed",
    ],
)
def test_closed_consumption_requires_native_terminal_stop_eod_and_frozen_consumption(
    tmp_path, monkeypatch, fault
):
    from src.engine.error_detectors import artifact_freshness as freshness
    from src.engine.infrastructure import runtime_release_router as router

    data = tmp_path / "data"
    root = tmp_path / "release"
    root.mkdir()
    monkeypatch.setattr(handoff, "DATA_DIR", data)
    monkeypatch.setattr(
        handoff.bootstrap,
        "manifest_path",
        lambda day: data / "runtime" / f"manifest_{day}.json",
    )
    monkeypatch.setattr(handoff, "_selection", lambda **kwargs: (root, NEW))

    def absent(pid):
        if fault == "pid_present":
            return dict(pid=pid, start_ticks="42", cwd=str(root / "src"))
        raise FileNotFoundError("stopped")

    monkeypatch.setattr(handoff, "_identity", absent)
    monkeypatch.setattr(
        freshness, "_postclose_main_absent", lambda: fault != "inventory_unknown"
    )
    monkeypatch.setattr(
        handoff,
        "_verify_handoff",
        lambda *a, **k: dict(status="fail" if fault == "handoff" else "pass"),
    )
    identity = dict(pid=3, start_ticks="42", cwd=str(root / "src"))
    handoff_path, consumed_path = handoff._paths(DAY, NEW)
    _json(handoff_path, dict(original=True))
    consumed = dict(
        schema="intraday_policy_preserving_consumption_v1",
        status="pass",
        target_date=DAY,
        selected_release_commit=NEW,
        release_root=str(root),
        handoff_sha256=handoff._sha(handoff_path),
        pid_identity=identity,
        actual_pid_consumed=True,
        manifest_sha256="original",
    )
    receipt = dict(
        schema="runtime_release_pid_receipt_v1",
        pid=3,
        start_ticks="42",
        process_cwd=str(root / "src"),
        release_root=str(root),
        git_commit=NEW,
        recorded_at_kst=DAY + "T19:58:00+09:00",
    )
    selected = dict(actual_pid_consumed=True, actual_pid_receipt=receipt)
    terminal = dict(
        alive=False,
        terminal_reason="market_close",
        unresolved_scalping_count=0,
        unresolved_scalping_codes="",
        last_beat=DAY + "T20:00:00+09:00",
    )
    heartbeat = dict(
        main_loop=dict(pid=3, last_beat=DAY + "T20:57:32+09:00"),
        ai_circuit=dict(pid=3, process_start_ticks="42"),
        threads=dict(sniper_engine=terminal),
    )
    isolation = dict(
        schema_version=1,
        active=True,
        target_date=DAY,
        session="bot",
        action="stop",
        reason="threshold_cycle_postclose_resource_isolation",
        started_at=DAY + "T20:57:32+09:00",
    )
    eod = dict(
        target_date=DAY,
        status="completed_with_warnings",
        finished_at=DAY + "T20:57:09",
        db_state=dict(latest_quote_date=DAY, rows_on_latest_date=2621),
    )
    if fault.startswith("interrupted") if fault else False:
        terminal["alive"] = True
        heartbeat["main_loop"]["last_beat"] = DAY + "T20:00:00+09:00"
        snapshot = dict(
            process_pid=3,
            process_start_ticks="42",
            source_contract="main_market_source_v1",
            collector_lifecycle="running",
            sequence_epoch=123,
        )
        if fault == "interrupted_actor":
            snapshot["process_pid"] = 4
        if fault == "interrupted_epoch":
            snapshot["sequence_epoch"] = False
        collector = dict(
            schema="scalp_micro_reversion_canary_monitor_v1",
            generated_at=DAY + "T20:00:00+09:00",
            collector_snapshot=snapshot,
        )
        if fault == "interrupted_clock":
            collector["generated_at"] = DAY + "T20:00:00"
        _json(
            data / "runtime/scalp_micro_reversion_forward_collector/latest.json",
            collector,
        )
    if fault == "receipt_pid":
        receipt["pid"] = 4
    elif fault == "receipt_start":
        receipt["start_ticks"] = "43"
    elif fault == "heartbeat_pid":
        heartbeat["main_loop"]["pid"] = 4
    elif fault == "heartbeat_start":
        heartbeat["ai_circuit"]["process_start_ticks"] = "43"
    elif fault == "terminal":
        terminal["alive"] = True
    elif fault == "unresolved":
        terminal["unresolved_scalping_count"] = 1
    elif fault == "isolation":
        isolation["active"] = False
    elif fault == "stop_clock":
        isolation["started_at"] = DAY + "T19:57:00+09:00"
    elif fault == "eod":
        eod["status"] = "failed"
    elif fault == "eod_date":
        eod["target_date"] = "2026-10-01"
    elif fault == "eod_rows":
        eod["db_state"]["rows_on_latest_date"] = 0
    _json(consumed_path, consumed)
    _json(data / "runtime/runtime_release_selection.json", selected)
    _json(tmp_path / "tmp/error_detector_heartbeat.json", heartbeat)
    _json(tmp_path / "tmp/postclose_bot_isolation.json", isolation)
    _json(data / "runtime/update_kospi_status" / f"update_kospi_{DAY}.json", eod)
    _json(
        handoff.bootstrap.manifest_path(DAY),
        dict(
            manifest_sha256=(
                "wrong" if fault in ("manifest", "interrupted_manifest") else "original"
            )
        ),
    )
    if fault in ("changed_heartbeat", "interrupted_changed"):
        original = router._startup_receipt
        calls = 0

        def changed(path):
            nonlocal calls
            if Path(path).name == "error_detector_heartbeat.json":
                calls += 1
                if calls == 2:
                    _json(path, {**heartbeat, "changed": True})
            return original(path)

        monkeypatch.setattr(router, "_startup_receipt", changed)
    now = NOW.replace(hour=22) + (
        timedelta(days=1) if fault == "midnight" else timedelta()
    )
    if fault not in (None, "midnight", "interrupted"):
        with pytest.raises((ValueError, OSError)):
            handoff.closed_consumption_observation(now=now)
        return
    proof = handoff.closed_consumption_observation(now=now)
    if fault == "interrupted":
        assert (
            proof["terminal_verified"] is False
            and proof["source_admission"] == "unverified_interrupted_epoch"
        )
        assert (
            proof["basis"] == "interrupted_consumed_process"
            and proof["collector_epoch"] == 123
        )
    assert proof["pid_identity"] == identity and proof["target_date"] == DAY
    assert (
        proof["runtime_effect"]
        is proof["current_observation_verified"]
        is proof["new_pid_consumption_claimed"]
        is False
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("source", list(handoff.REVIEWED_POSTCLOSE_REPAIR_HASHES))
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_postclose_repair_requires_complete_exact_reader_generation(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "postclose_repair"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "source,fault",
    [
        (source, fault)
        for source in (
            *handoff.REVIEWED_LOGICAL_PIPELINE_HASHES,
            "src/engine/error_detectors/artifact_freshness.py",
            "deploy/run_threshold_cycle_postclose.sh",
        )
        for fault in (None, "missing", "dirty", "committed_change", "parent_mix")
        if fault != "parent_mix" or source in handoff.REVIEWED_LOGICAL_PIPELINE_HASHES
    ],
)
def test_logical_pipeline_handoff_binds_exact_new_and_prior_owners(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "logical_pipeline"
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
def test_actual_selected_postclose_origin_matches_complete_native_contract(family):
    import hashlib
    import os
    import subprocess
    from src.engine.scalping import (
        main_stop_policy as stop,
        holding_vote_experiment as vote,
    )
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS

    root = Path(handoff.__file__).resolve().parents[3]
    origin = "72617981be50cc900281fce313e37057f203b1bc"
    paths = (
        {name: name for name in CONTRACT_PATHS}
        if family == "pre_submit_delay"
        else {
            name: "src/engine/" + name
            for name in (
                stop.implementation_paths()
                if family == "main_stop"
                else vote._code_paths()
            )
        }
    )
    expected = stop.digest(
        {
            key: hashlib.sha256(
                subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(root),
                        "show",
                        origin + ":" + os.path.normpath(name),
                    ]
                )
            ).hexdigest()
            for key, name in paths.items()
        }
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    handoff._verify_entry_code_delta(root, commit, origin, paths, expected)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("source", list(handoff.REVIEWED_HISTORICAL_RESOLUTION_HASHES))
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_historical_resolution_handoff_keeps_full_native_boundary(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "historical_resolution"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("source", list(handoff.REVIEWED_FINALIZATION_HEALTH_HASHES))
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_finalization_health_handoff_keeps_issued_profiles_and_exact_successor(
    tmp_path, family, source, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, source, "finalization_health"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_native_invalidation_handoff_binds_complete_observation_successor(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_NATIVE_INVALIDATION_HASHES),
        "native_invalidation",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_fixed_wait_handoff_binds_new_identity_and_preserved_native_contracts(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, tuple(handoff.REVIEWED_FIXED_WAIT_HASHES), "fixed_wait"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_entry_receipt_handoff_binds_exact_recovery_and_observation_successor(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_ENTRY_RECEIPT_HASHES),
        "entry_receipt",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_buy_identity_handoff_keeps_exact_receipt_predecessor(tmp_path, family, fault):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_BUY_IDENTITY_HASHES),
        "buy_identity",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_collector_close_handoff_requires_whole_native_generation(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_COLLECTOR_CLOSE_HASHES),
        "collector_close",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_collector_first_transition_handoff_preserves_issued_predecessor(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES),
        "collector_first_transition",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_delay_machine_parent_handoff_requires_whole_producer_consumer_group(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_DELAY_MACHINE_PARENT_HASHES),
        "quantity_capture",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_quantity_capture_handoff_preserves_policy_and_native_close(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(
            {
                **handoff.REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES,
                **handoff.REVIEWED_QUANTITY_CAPTURE_HASHES,
            }
        ),
        "quantity_capture",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
def test_quantity_capture_handoff_accepts_actual_preopen_origin(tmp_path, family):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        None,
        tuple(handoff.REVIEWED_QUANTITY_CAPTURE_HASHES),
        "quantity_capture",
        policy_origin="d7d353b4add257f0962abff8082a061bbc040ab7",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_prepared_quantity_stage_handoff_binds_producer_and_consumer(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_QUANTITY_STAGE_HASHES),
        "quantity_stage",
        policy_origin="d7d353b4add257f0962abff8082a061bbc040ab7",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_nonfixed_capacity_handoff_binds_metadata_intake_queue_and_runtime(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_NONFIXED_CAPACITY_HASHES),
        "nonfixed_capacity",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_holding_input_handoff_binds_database_clock_capture_and_vote_costs(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES),
        "holding_input",
    )


def test_reviewed_profile_registration_keeps_native_hash_helper_callable(tmp_path):
    import hashlib

    path = tmp_path / "native-checklist"
    path.write_bytes(b"original-native-evidence")
    assert handoff._sha(path) == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_post_sell_source_handoff_binds_route_producer_and_horizon_reader(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_POST_SELL_SOURCE_HASHES),
        "post_sell_source",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_operator_market_handoff_binds_every_consumer_and_preserves_old_profiles(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_OPERATOR_MARKET_HASHES),
        "operator_market",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_operator_quantity_provenance_handoff_retains_complete_generation(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        "src/engine/scalping/initial_quantity_policy.py",
        "operator_market",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_p5_ancestry_handoff_keeps_complete_operator_generation(
    tmp_path, family, fault
):
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path,
        family,
        fault,
        tuple(handoff.REVIEWED_P5_ANCESTRY_HASHES),
        "p5_ancestry",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "parent_mix", "committed_change", "dirty"]
)
def test_postclose_recovery_handoff_keeps_complete_reviewed_generation(
    tmp_path, family, fault
):
    paths = (
        "src/engine/ai/holding_vote_replay_source.py",
        "src/engine/automation/main_stop_postclose.py",
        "src/engine/automation/main_trailing_source_assembler.py",
        "src/engine/infrastructure/validation_digest_session.py",
        "src/engine/error_detectors/artifact_freshness.py",
        "deploy/run_threshold_cycle_postclose.sh",
        "src/engine/automation/postclose_finalization_generation.py",
    )
    test_source_reader_handoff_preserves_issued_policy_and_exact_dependencies(
        tmp_path, family, fault, paths, "postclose_recovery"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "generation", ["consumed_observer_io", "consumed_index_sentinel"]
)
@pytest.mark.parametrize("fault", [None, "successor_mix"])
def test_pre_submit_keeps_consumed_preparation_and_rejects_mixed_successor(
    tmp_path, family, generation, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, generation, "src/engine/sniper_state_handlers.py"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "dependency",
    [
        "src/engine/sniper_state_handlers.py",
        "src/engine/scalping/reversal_evaluation_context.py",
        "src/engine/monitoring/runtime_performance.py",
        "src/trading/entry/physical_send_guard.py",
        "src/engine/monitoring/policy_generation_code_handoff.py",
    ],
)
def test_pre_submit_handoff_rejects_unreviewed_dependency(tmp_path, family, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, "committed_change", "current", dependency
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
@pytest.mark.parametrize(
    "generation",
    [
        "current",
        "consumed_nonfixed_identity",
        "consumed_preclaim",
        "consumed_entry_capability",
        "consumed_migration",
        "consumed_pre_startup",
        "consumed_pre_shutdown",
        "consumed_pre_native_label",
        "consumed_pre_coordination",
        "consumed_pre_prepared_validation",
        "consumed_pre_prepared_repair",
        "consumed_pre_main_preparation",
        "consumed_pre_prepared_start",
        "consumed_pre_first_turn",
        "consumed_pre_expiry_health",
        "consumed_pre_signed_surge",
        "consumed_pre_preassessment",
        "consumed_pre_prestart",
        "consumed_pre_prepared_owner",
    ],
)
def test_entry_cost_handoff_keeps_exact_complete_generation(
    tmp_path,
    family,
    fault,
    generation,
    dependency="src/engine/monitoring/entry_attempt_identity.py",
    policy_origin=None,
):
    import hashlib, os, subprocess
    from src.engine.scalping import (
        main_stop_policy as stop,
        holding_vote_experiment as vote,
    )
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS

    canonical = Path(handoff.__file__).resolve().parents[3]
    root = tmp_path / "candidate"
    root.mkdir()
    subprocess.run(
        ["git", "clone", "-q", "--shared", "--no-checkout", str(canonical), str(root)],
        check=True,
    )
    subprocess.run(["git", "-C", str(root), "checkout", "-q", "75e0fbbf7"], check=True)
    hashes = {
        "current": handoff.REVIEWED_NONFIXED_PRECLAIM_PROFILE,
        "consumed_nonfixed_identity": handoff.REVIEWED_NONFIXED_IDENTITY_PROFILE,
        "consumed_preclaim": handoff.REVIEWED_PRECLAIM_DIAGNOSTIC_PROFILE,
        "consumed_entry_capability": handoff.REVIEWED_ENTRY_CAPABILITY_PROFILE,
        "entry_capability": handoff.REVIEWED_ENTRY_CAPABILITY_PROFILE,
        "entry_latency": handoff.REVIEWED_ENTRY_LATENCY_PROFILE,
        "holding_capability": handoff.REVIEWED_HOLDING_CAPABILITY_PROFILE,
        "finalization_admission": handoff.REVIEWED_FINALIZATION_ADMISSION_PROFILE,
        "holding_quote": handoff.REVIEWED_HOLDING_QUOTE_PROFILE,
        "drain_pointer": handoff.REVIEWED_DRAIN_POINTER_PROFILE,
        "drain_closure": handoff.REVIEWED_DRAIN_CLOSURE_PROFILE,
        "consumed_quantity_history": handoff.REVIEWED_QUANTITY_HISTORY_PROFILE,
        "consumed_suffix_report": handoff.REVIEWED_SUFFIX_REPORT_PROFILE,
        "consumed_isolated_index": handoff.REVIEWED_ISOLATED_INDEX_PROFILE,
        "consumed_stop_index": handoff.REVIEWED_STOP_INDEX_PROFILE,
        "consumed_closed_loader": handoff.REVIEWED_CLOSED_LOADER_PROFILE,
        "consumed_cumulative_hold": handoff.REVIEWED_CUMULATIVE_HOLD_PROFILE,
        "consumed_health_snapshot": handoff.REVIEWED_HEALTH_SNAPSHOT_PROFILE,
        "consumed_submit_probe": handoff.REVIEWED_SUBMIT_PROBE_PROFILE,
        "consumed_fixture": handoff.REVIEWED_PREPARED_FIXTURE_PROFILE,
        "consumed_registry": handoff.REVIEWED_REGISTRY_REPLAY_PROFILE,
        "consumed_activation_observer": handoff.REVIEWED_ACTIVATION_DATE_PROFILE,
        "consumed_migration": handoff.REVIEWED_MIGRATION_PROFILE,
        "consumed_auxiliary_envelope": handoff.REVIEWED_AUXILIARY_ENVELOPE_PROFILE,
        "consumed_source_boundary": handoff.REVIEWED_COLD_SOURCE_BOUNDARY_PROFILE,
        "consumed_workflow_inventory": handoff.REVIEWED_WORKFLOW_INVENTORY_PROFILE,
        "consumed_cancel_cache": handoff.REVIEWED_CANCEL_CACHE_PROFILE,
        "consumed_archive_projection": handoff.REVIEWED_ARCHIVE_PROJECTION_PROFILE,
        "consumed_producer_identity": handoff.REVIEWED_PRODUCER_IDENTITY_PROFILE,
        "consumed_cold_postclose": handoff.REVIEWED_STOPPED_POSTCLOSE_PROFILE,
        "consumed_auxiliary_format": handoff.REVIEWED_AUXILIARY_FORMAT_PROFILE,
        "consumed_postclose_source": handoff.REVIEWED_POSTCLOSE_SOURCE_PROFILE,
        "consumed_closed_scanner": handoff.REVIEWED_CLOSED_SCANNER_PREVIOUS_PROFILE,
        "consumed_scanner_preflight": handoff.REVIEWED_SCANNER_PREFLIGHT_PROFILE,
        "consumed_listing_source": handoff.REVIEWED_AFTERMARKET_LISTING_PROFILE,
        "consumed_numeric_source": handoff.REVIEWED_NUMERIC_REPLAY_PROFILE,
        "consumed_auxiliary_capability": handoff.REVIEWED_AUXILIARY_CAPABILITY_PROFILE,
        "consumed_rest_history": handoff.REVIEWED_MACHINE_REST_HISTORY_PROFILE,
        "consumed_holding_stream": handoff.REVIEWED_HOLDING_STREAM_PROFILE,
        "consumed_policy_custody": handoff.REVIEWED_NATIVE_BUY_COST_PROFILE,
        "consumed_observer_io": handoff.REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES,
        "prepared_pre_submit": handoff.REVIEWED_PRE_SUBMIT_ENTRY_COST_HASHES,
        "consumed_index_sentinel": handoff.REVIEWED_ENTRY_COST_HASHES,
        "consumed_sentinel": handoff.REVIEWED_ENTRY_COST_DEPLOYED_SENTINEL_HASHES,
        "consumed_pre_finalization": handoff.REVIEWED_PRE_FINALIZATION_HASHES,
        "consumed_native_preopen": handoff.REVIEWED_NATIVE_PREOPEN_HASHES,
        "consumed_pre_startup": handoff.REVIEWED_ENTRY_COST_PRE_STARTUP_HASHES,
        "consumed_pre_shutdown": handoff.REVIEWED_ENTRY_COST_PRE_SHUTDOWN_HASHES,
        "consumed_pre_native_label": handoff.REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_HASHES,
        "consumed_pre_coordination": handoff.REVIEWED_ENTRY_COST_PRE_COORDINATION_HASHES,
        "consumed_pre_prepared_validation": handoff.REVIEWED_ENTRY_COST_PRE_PREPARED_VALIDATION_HASHES,
        "consumed_pre_prepared_repair": handoff.REVIEWED_ENTRY_COST_PRE_PREPARED_REPAIR_HASHES,
        "consumed_pre_main_preparation": handoff.REVIEWED_ENTRY_COST_PRE_MAIN_PREPARATION_HASHES,
        "consumed_pre_prepared_start": handoff.REVIEWED_ENTRY_COST_PRE_PREPARED_START_HASHES,
        "consumed_pre_first_turn": handoff.REVIEWED_ENTRY_COST_PRE_FIRST_TURN_HASHES,
        "consumed_pre_expiry_health": handoff.REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_HASHES,
        "consumed_pre_signed_surge": handoff.REVIEWED_ENTRY_COST_PRE_SIGNED_SURGE_HASHES,
        "consumed_pre_preassessment": handoff.REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_HASHES,
        "consumed_pre_prestart": handoff.REVIEWED_ENTRY_COST_PRE_PRESTART_HASHES,
        "consumed_pre_prepared_owner": handoff.REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_HASHES,
    }[generation]
    for name in hashes:
        content = (
            (canonical / name).read_bytes()
            if generation == "current"
            else subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "show",
                    {
                        "consumed_nonfixed_identity": "16130d883",
                        "consumed_preclaim": "c8d22dd41",
                        "consumed_entry_capability": "6d0d19756",
                        "consumed_fixture": "c260d6b07",
                        "consumed_submit_probe": "b6611ce26",
                        "consumed_health_snapshot": "7b98fa4bc",
                        "consumed_cumulative_hold": "89a0a5fa2",
                        "consumed_closed_loader": "cb4f0ab58",
                        "consumed_stop_index": "2fbf31449",
                        "consumed_quantity_history": "198286cf2",
                        "drain_closure": "e930a7c95",
                        "drain_pointer": "97bc1f62e",
                        "holding_quote": "279886a71",
                        "holding_capability": "bcfedb8ad",
                        "entry_latency": "cd2eb9ea1",
                        "entry_capability": "6d0d19756",
                        "finalization_admission": "194307750",
                        "consumed_suffix_report": "ab663e13b",
                        "consumed_isolated_index": "59a922b19",
                        "consumed_auxiliary_format": "c0346b611",
                        "consumed_cold_postclose": "6fe72273e",
                        "consumed_producer_identity": "2c9f2a6ad",
                        "consumed_archive_projection": "c4fa59c86",
                        "consumed_cancel_cache": "ed4e05e6f",
                        "consumed_workflow_inventory": "a6389ea2f",
                        "consumed_source_boundary": "fdbeee2c7",
                        "consumed_migration": "ef9927b7c",
                        "consumed_activation_observer": "1081d2f8e",
                        "consumed_registry": "9bc5829ca",
                        "consumed_auxiliary_envelope": "22b5630fd",
                        "consumed_postclose_source": "06dbfe661",
                        "consumed_closed_scanner": "2edf3263e",
                        "consumed_scanner_preflight": "6e970e41f",
                        "consumed_listing_source": "ea8a9ba85",
                        "consumed_numeric_source": "b7aeb7efc",
                        "consumed_auxiliary_capability": "428f7ece3",
                        "consumed_rest_history": "97a72d632",
                        "consumed_holding_stream": "6d8891ac3",
                        "consumed_policy_custody": "9e820cbf8",
                        "prepared_pre_submit": "b2dbb0862",
                        "consumed_observer_io": "a2ca8e7d8",
                        "consumed_index_sentinel": "926ebca82",
                        "consumed_sentinel": "2b7ca0380",
                        "consumed_native_preopen": "9a8e59bfc",
                        "consumed_pre_finalization": "91e5d2702",
                        "consumed_pre_startup": "90bf2d11f",
                        "consumed_pre_shutdown": "70fc572f8",
                        "consumed_pre_native_label": "b1519a2d4",
                        "consumed_pre_coordination": "3dd9f1bf5",
                        "consumed_pre_prepared_validation": "bf330ae92",
                        "consumed_pre_prepared_repair": "81f43b8ba",
                        "consumed_pre_main_preparation": "8644e15fc",
                        "consumed_pre_prepared_start": "3b951f1f1",
                        "consumed_pre_first_turn": "e9ee2c8ea",
                        "consumed_pre_expiry_health": "9476e9ecd",
                        "consumed_pre_signed_surge": "bf26ddf0e",
                        "consumed_pre_preassessment": "fc51a179b",
                        "consumed_pre_prestart": "64ec63a87",
                        "consumed_pre_prepared_owner": "d346aa3af",
                    }[generation]
                    + ":"
                    + name,
                ]
            )
        )
        (root / name).write_bytes(content)
    name = "src/engine/automation/intraday_release_handoff.py"
    (root / name).write_bytes((canonical / name).read_bytes())
    source = dependency
    path = root / source
    if fault == "missing":
        path.unlink()
    elif fault == "successor_mix":
        path.write_bytes((canonical / source).read_bytes())
    elif fault == "parent_mix":
        # The immediate adapter predecessor is a valid complete issued profile.
        # Mix an earlier adapter instead to exercise an unreviewed combination.
        mixed_origin = (
            "336e0a79d"
            if source == "deploy/run_threshold_cycle_postclose.sh"
            else (
                "6978f78c1"
                if source
                == "src/engine/automation/postclose_finalization_generation.py"
                else (
                    "6978f78c1^"
                    if source == "src/engine/error_detectors/artifact_freshness.py"
                    else (
                        "9707a5b70^"
                        if source
                        == "src/engine/automation/postclose_summary_handoff.py"
                        else (
                            "7f2552aedde8fec6ef904a43105827907e50dfc8"
                            if source == "src/utils/kiwoom_utils.py"
                            else "75e0fbbf7"
                        )
                    )
                )
            )
        )
        path.write_bytes(
            subprocess.check_output(
                ["git", "-C", str(root), "show", mixed_origin + ":" + source]
            )
        )
    elif fault == "committed_change":
        path.write_bytes(path.read_bytes() + b"\nUNREVIEWED=True\n")
    subprocess.run(["git", "-C", str(root), "add", "src", "deploy"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "integrated source fixture"],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if fault == "dirty":
        path.write_bytes(path.read_bytes() + b"\nUNREVIEWED=True\n")
    origin = policy_origin or "75e0fbbf79d8842ceed159ea73166f8872b4e93e"
    paths = (
        {n: n for n in CONTRACT_PATHS}
        if family == "pre_submit_delay"
        else {
            n: "src/engine/" + n
            for n in (
                stop.implementation_paths()
                if family == "main_stop"
                else vote._code_paths()
            )
        }
    )
    expected = stop.digest(
        {
            k: hashlib.sha256(
                subprocess.check_output(
                    ["git", "-C", str(root), "show", origin + ":" + os.path.normpath(n)]
                )
            ).hexdigest()
            for k, n in paths.items()
        }
    )
    if fault:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(root, commit, origin, paths, expected)
    else:
        handoff._verify_entry_code_delta(root, commit, origin, paths, expected)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
@pytest.mark.parametrize(
    "dependency",
    [
        "src/engine/ai_engine_openai.py",
        "src/engine/scalping/ai_decision_trace.py",
        "src/engine/automation/main_trailing_source_reuse.py",
        "src/engine/automation/main_trailing_source_store.py",
        "src/engine/automation/main_trailing_source_assembler.py",
        "src/engine/lifecycle/broker_cost_reconciliation.py",
        "src/engine/lifecycle/holding_research_cost.py",
        "src/engine/scalping/reversal_source_diagnostics.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/monitoring/runtime_performance.py",
        "src/engine/scalping/continuous_reversal_source.py",
        "src/engine/automation/main_market_weakness_research.py",
        "src/engine/automation/ordered_intraday_deploy.py",
        "src/engine/automation/prepared_policy_code_handoff.py",
        "src/engine/automation/entry_cancel_wait_tuning.py",
        "src/engine/infrastructure/runtime_release_router.py",
        "src/engine/scalping/reversal_code_handoff.py",
        "src/engine/monitoring/submission_bottleneck_monitor.py",
        "src/engine/scalping/zero_base_probe.py",
        "src/utils/kiwoom_utils.py",
        "src/engine/lifecycle/broker_cost_source.py",
        "src/engine/scalping/initial_quantity_monitor_projection.py",
        "src/engine/scalping/ai_action_outcome_calibration.py",
        "src/engine/scalping/continuous_reversal_operating_postclose.py",
        "src/engine/scalping/continuous_reversal_policy_v6.py",
        "src/engine/infrastructure/startup_validation_code_context.py",
    ],
)
def test_native_selection_label_handoff_rejects_incomplete_generation(
    tmp_path, family, fault, dependency
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_prepared_validation_handoff_rejects_changed_context(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "current",
        "src/engine/infrastructure/startup_validation_code_context.py",
    )


@pytest.mark.parametrize("damage", [None, "changed_source", "consumed", "origin"])
def test_stopped_preparation_analysis_preserves_expired_launch_guard(
    fixture, monkeypatch, damage
):
    from types import SimpleNamespace
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.infrastructure import runtime_release_router as R

    data, previous, selected, prepare = fixture
    assert prepare()["status"] == "pass"
    expired = NOW + timedelta(minutes=16)
    monkeypatch.setattr(handoff, "_today", lambda *a: expired)
    hp, cp = handoff._paths(DAY, NEW)
    original = hp.read_bytes()
    source = data / "original-stopped-proof.json"
    source.write_text("native original")
    driver = SimpleNamespace(
        workspace=data.parent,
        previous=previous,
        previous_commit=OLD,
        identity={"pid": 1},
        selection=source,
        hold=source,
    )
    origin = dict(
        failed_root=selected,
        failed_commit=NEW,
        selected={},
        failed_path=source,
        prior_path=source,
        preparation_sources={},
    )

    def inspect():
        if damage == "origin":
            raise ValueError("unknown failed origin")
        return origin

    driver.inspect_stopped_origin = inspect
    monkeypatch.setattr(D, "StoppedDeploymentRecovery", lambda *a: driver)
    monkeypatch.setattr(
        D,
        "_stopped_intraday_predecessor",
        lambda *a: dict(frozen_files={str(source): handoff._sha(source)}),
    )
    monkeypatch.setattr(R, "git", lambda *a: "c" * 40)

    def validate(workspace, value):
        assert value["workspace"] == str(workspace)

    monkeypatch.setattr(R, "validate_release", validate)
    assert handoff.verify(DAY, NEW, now=expired)["findings"] == [
        "intraday_first_launch_window_expired"
    ]
    if damage == "consumed":
        cp.write_text("{}")
    if damage in {"consumed", "origin"}:
        with pytest.raises(ValueError):
            with handoff.stopped_preparation_review(DAY):
                pass
    else:
        with (
            pytest.raises(ValueError)
            if damage
            else __import__("contextlib").nullcontext()
        ):
            with handoff.stopped_preparation_review(DAY) as proof:
                assert (
                    proof["original_first_launch_before"]
                    == json.loads(original)["first_launch_before"]
                )
                assert (
                    proof["actual_pid_consumed"] is False
                    and proof["allowed_runtime_apply"] is False
                )
                assert handoff.verify(DAY, NEW, now=expired)["status"] == "pass"
                with pytest.raises(ValueError, match="not_launch_authority"):
                    handoff.consume(DAY, pid=2, now=expired)
                if damage:
                    source.write_text("changed native generation")
    assert hp.read_bytes() == original
    if damage != "consumed":
        assert not cp.exists()
        assert handoff.verify(DAY, NEW, now=expired)["findings"] == [
            "intraday_first_launch_window_expired"
        ]


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
@pytest.mark.parametrize(
    "generation",
    [
        "current",
        "consumed_pre_prepared_owner",
        "consumed_pre_finalization",
        "consumed_native_preopen",
    ],
)
@pytest.mark.parametrize(
    "dependency",
    [
        "deploy/run_threshold_cycle_postclose.sh",
        "src/engine/automation/postclose_finalization_generation.py",
        "src/engine/error_detectors/artifact_freshness.py",
        "src/engine/automation/postclose_summary_handoff.py",
        "src/engine/infrastructure/startup_validation_code_context.py",
    ],
)
def test_postclose_workflow_review_retains_current_and_native_predecessor_closure(
    tmp_path, family, fault, generation, dependency
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, generation, dependency=dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "dependency,fault",
    [
        ("src/engine/monitoring/sentinel_event_scope.py", None),
        ("src/engine/monitoring/sentinel_event_scope.py", "missing"),
        ("src/engine/monitoring/sentinel_event_scope.py", "dirty"),
        ("src/engine/monitoring/sentinel_event_scope.py", "committed_change"),
        ("src/engine/monitoring/submission_bottleneck_monitor.py", "parent_mix"),
        ("src/engine/sniper_state_handlers.py", "parent_mix"),
        ("src/engine/kiwoom_sniper_v2.py", "missing"),
        ("src/engine/kiwoom_websocket.py", "committed_change"),
        ("src/engine/scalping/pre_submit_delay_observation.py", "parent_mix"),
        ("src/engine/automation/main_trailing_source_reuse.py", "parent_mix"),
        ("src/engine/automation/main_trailing_source_reuse.py", "missing"),
        ("src/engine/automation/main_trailing_source_assembler.py", "parent_mix"),
        ("src/engine/automation/main_trailing_source_assembler.py", "committed_change"),
        ("src/engine/automation/main_market_weakness_research.py", "parent_mix"),
        ("src/engine/automation/main_market_weakness_research.py", "missing"),
        ("src/engine/scalping/market_weakness_research.py", "parent_mix"),
        ("src/engine/scalping/market_weakness_research.py", "committed_change"),
        ("src/engine/automation/ordered_intraday_deploy.py", "parent_mix"),
        ("src/engine/automation/ordered_intraday_deploy.py", "missing"),
    ],
)
def test_sentinel_route_successor_keeps_complete_reviewed_source_group(
    tmp_path, family, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency=dependency
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "parent_mix"])
def test_consumed_sentinel_profile_retains_exact_native_handoff(
    tmp_path, family, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "consumed_sentinel",
        dependency="src/engine/monitoring/submission_bottleneck_monitor.py",
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "dependency",
    [
        "src/engine/lifecycle/research_storage.py",
        "src/engine/monitoring/observer_artifact_io.py",
        "src/engine/error_detectors/artifact_freshness.py",
        "src/engine/monitoring/submission_bottleneck_monitor.py",
        "src/engine/automation/ordered_intraday_deploy.py",
        "src/engine/automation/entry_cancel_wait_tuning.py",
        "src/engine/monitoring/policy_generation_code_handoff.py",
        "src/engine/scalping/mechanistic_entry_runtime_policy.py",
        "src/engine/infrastructure/startup_validation_code_context.py",
    ],
)
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change"])
def test_observer_io_p5_handoff_requires_complete_reviewed_group(
    tmp_path, family, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency=dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "missing", "parent_mix"])
def test_observer_io_handoff_retains_consumed_index_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "consumed_index_sentinel",
        dependency="src/engine/monitoring/submission_bottleneck_monitor.py",
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change"])
@pytest.mark.parametrize(
    "dependency",
    [
        "src/engine/lifecycle/broker_cost_allocation.py",
        "src/engine/scalping/initial_quantity_monitor_projection.py",
        "src/engine/infrastructure/startup_validation_code_context.py",
        "src/engine/monitoring/policy_generation_code_handoff.py",
        "src/engine/sniper_state_handlers.py",
        "src/scanners/scalping_scanner.py",
        "src/utils/pipeline_event_logger.py",
        "src/engine/scalping/initial_quantity_policy.py",
        "src/engine/kiwoom_websocket.py",
        "src/scanners/zero_base_discovery_runtime.py",
        "src/engine/scalping/holding_path_vote_policy.py",
        "src/engine/runtime_approval_summary.py",
        "src/engine/infrastructure/startup_validation_isolation.py",
        "src/engine/automation/policy_generation_fixture_validation.py",
        "src/engine/automation/tuning_performance_control_tower.py",
        "src/engine/automation/main_startup_validation.py",
    ],
)
def test_native_buy_cost_handoff_keeps_exact_reviewed_generation(
    tmp_path, family, fault, dependency
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency=dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "missing", "parent_mix"])
def test_native_buy_cost_handoff_preserves_consumed_observer(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "consumed_observer_io",
        dependency="src/engine/lifecycle/broker_cost_allocation.py",
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "dirty", "committed_change"])
def test_native_buy_cost_preserves_prepared_submit_profile(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "prepared_pre_submit",
        dependency="src/engine/lifecycle/broker_cost_allocation.py",
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change"])
@pytest.mark.parametrize("dependency", sorted(handoff.REVIEWED_HOLDING_STREAM_HASHES))
def test_holding_stream_handoff_binds_producer_and_consumer(
    tmp_path, family, fault, dependency
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "successor_mix", "committed_change"])
def test_holding_stream_preserves_actually_consumed_policy_custody(
    tmp_path, family, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "consumed_policy_custody",
        "src/engine/sniper_state_handlers.py",
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "generation",
    [
        "current",
        "consumed_holding_stream",
        "consumed_rest_history",
        "consumed_auxiliary_capability",
    ],
)
def test_rest_history_handoff_preserves_policy_and_consumed_parent(
    tmp_path, family, generation
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, generation
    )


@pytest.mark.parametrize(
    "dependency", sorted(handoff.REVIEWED_MACHINE_REST_HISTORY_HASHES)
)
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change"])
def test_rest_history_handoff_rejects_incomplete_sources(tmp_path, dependency, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, "pre_submit_delay", fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "dependency", sorted(handoff.REVIEWED_AUXILIARY_CAPABILITY_HASHES)
)
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_auxiliary_capability_handoff_keeps_whole_reviewed_group(
    tmp_path, family, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change"])
@pytest.mark.parametrize("dependency", sorted(handoff.REVIEWED_NUMERIC_REPLAY_HASHES))
def test_numeric_replay_handoff_requires_complete_reviewed_group(
    tmp_path, family, fault, dependency
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("fault", [None, "successor_mix", "committed_change"])
def test_numeric_replay_preserves_consumed_holding_stream(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        family,
        fault,
        "consumed_holding_stream",
        "src/engine/sniper_state_handlers.py",
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "generation",
    [
        "current",
        "consumed_rest_history",
        "consumed_auxiliary_capability",
        "consumed_numeric_source",
    ],
)
def test_aftermarket_listing_preserves_complete_consumed_profile(
    tmp_path, family, generation
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, generation
    )


@pytest.mark.parametrize(
    "dependency,fault",
    [("src/engine/kiwoom_orders.py", None)]
    + [
        (path, fault)
        for path in sorted(handoff.REVIEWED_AFTERMARKET_LISTING_HASHES)
        for fault in ("missing", "dirty", "committed_change", "parent_mix")
    ],
)
def test_listing_successor_preserves_original_stop_origin_and_full_profile(
    tmp_path, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path,
        "main_stop",
        fault,
        "current",
        dependency,
        policy_origin="72617981be50cc900281fce313e37057f203b1bc",
    )


@pytest.mark.parametrize(
    "dependency", sorted(handoff.REVIEWED_AFTERMARKET_LISTING_HASHES)
)
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_aftermarket_listing_handoff_rejects_incomplete_or_mixed_sources(
    tmp_path, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, "pre_submit_delay", fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("generation", ["current", "consumed_listing_source"])
def test_scanner_preflight_preserves_complete_consumed_profile(
    tmp_path, family, generation
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, generation
    )


@pytest.mark.parametrize(
    "dependency", sorted(handoff.REVIEWED_SCANNER_PREFLIGHT_HASHES)
)
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_scanner_preflight_handoff_rejects_unreviewed_or_mixed_sources(
    tmp_path, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, "pre_submit_delay", fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "generation",
    [
        "current",
        "consumed_postclose_source",
        "consumed_scanner_preflight",
        "consumed_closed_scanner",
    ],
)
def test_closed_scanner_handoff_preserves_consumed_preflight(
    tmp_path, family, generation
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, generation
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize("dependency", sorted(handoff.REVIEWED_CLOSED_SCANNER_HASHES))
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_closed_scanner_handoff_rejects_unknown_or_mixed_sources(
    tmp_path, family, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("dependency", sorted(handoff.REVIEWED_POSTCLOSE_SOURCE_HASHES))
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_postclose_source_handoff_rejects_partial_successor(
    tmp_path, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, "pre_submit_delay", fault, "current", dependency
    )


@pytest.mark.parametrize(
    "fault",
    [None, "same_generation", "dirty", "unreviewed", "origin_digest", "wrong_path"],
)
def test_formatting_projection_preserves_physical_git_and_original_contract(
    tmp_path, monkeypatch, fault
):
    import hashlib
    import subprocess

    name = "src/core/event_bus.py"
    before = subprocess.check_output(
        [
            "git",
            "-C",
            str(handoff._FORMATTING_REVIEW_ROOT),
            "show",
            handoff._FORMATTING_BASE + ":" + name,
        ]
    )
    after = (handoff._FORMATTING_REVIEW_ROOT / name).read_bytes()
    assert before != after
    handoff._formatting_original.cache_clear()
    if fault == "wrong_path":
        name = "src/core/unreviewed_event_bus.py"
    own = "src/engine/automation/intraday_release_handoff.py"
    own_raw = (handoff._FORMATTING_REVIEW_ROOT / own).read_bytes()
    original = after if fault == "same_generation" else before
    expected = hashlib.sha256(
        json.dumps(
            {name: hashlib.sha256(original).hexdigest()},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    physical = after + b"\nUNREVIEWED = True\n" if fault == "unreviewed" else after
    committed = before if fault == "dirty" else physical
    for relative, raw in ((own, own_raw), (name, physical)):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def git_bytes(command, **kwargs):
        spec = command[-1]
        if spec.endswith(":" + own):
            return own_raw
        if spec.startswith(handoff._FORMATTING_BASE + ":"):
            return before
        return original if spec.startswith(OLD + ":") else committed

    monkeypatch.setattr(handoff.subprocess, "check_output", git_bytes)
    if fault == "origin_digest":
        expected = "0" * 64
    if fault not in (None, "same_generation"):
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(tmp_path, NEW, OLD, {name: name}, expected)
    else:
        changed = handoff._verify_entry_code_delta(
            tmp_path, NEW, OLD, {name: name}, expected
        )
        assert changed == ([] if fault == "same_generation" else [name])
    assert (tmp_path / name).read_bytes() == physical
    handoff._formatting_original.cache_clear()


@pytest.mark.parametrize("fault", ["missing", "tampered"])
def test_formatting_review_never_falls_back_when_custody_is_missing(
    tmp_path, monkeypatch, fault
):
    if fault == "tampered":
        path = tmp_path / handoff._FORMATTING_REVIEW_PATH
        path.parent.mkdir(parents=True)
        path.write_text('{"sources": {}}')
    monkeypatch.setattr(handoff, "_FORMATTING_REVIEW_ROOT", tmp_path)
    with pytest.raises((FileNotFoundError, ValueError)):
        handoff._formatting_review()


def test_formatting_original_digest_is_verified_before_comparison(monkeypatch):
    handoff._formatting_original.cache_clear()
    monkeypatch.setattr(
        handoff.subprocess, "check_output", lambda *a, **k: b"wrong original"
    )
    with pytest.raises(ValueError, match="formatting_origin_invalid"):
        handoff._formatting_original("src/core/event_bus.py", "0" * 64)
    handoff._formatting_original.cache_clear()


@pytest.mark.parametrize("dependency", sorted(handoff.REVIEWED_AUXILIARY_FORMAT_HASHES))
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_auxiliary_format_handoff_rejects_partial_successor(
    tmp_path, dependency, fault
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, "pre_submit_delay", fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["pre_submit_delay", "main_stop", "holding_vote"])
@pytest.mark.parametrize(
    "generation",
    [
        "current",
        "consumed_registry",
        "consumed_auxiliary_format",
        "consumed_activation_observer",
        "consumed_cold_postclose",
        "consumed_producer_identity",
        "consumed_archive_projection",
        "consumed_cancel_cache",
        "consumed_workflow_inventory",
        "consumed_source_boundary",
    ],
)
def test_cold_postclose_reader_preserves_original_complete_profile(
    tmp_path, family, generation
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, generation
    )


@pytest.mark.parametrize(
    "dependency",
    sorted(
        {
            **handoff.REVIEWED_STOPPED_POSTCLOSE_HASHES,
            **handoff.REVIEWED_ARCHIVE_PROJECTION_HASHES,
            **handoff.REVIEWED_CANCEL_CACHE_HASHES,
            **handoff.REVIEWED_WORKFLOW_INVENTORY_HASHES,
            **handoff.REVIEWED_COLD_SOURCE_BOUNDARY_HASHES,
            **handoff.REVIEWED_AUXILIARY_ENVELOPE_HASHES,
            **handoff.REVIEWED_MIGRATION_HASHES,
            **handoff.REVIEWED_ACTIVATION_DATE_HASHES,
        }
    ),
)
@pytest.mark.parametrize(
    "fault", ["missing", "dirty", "committed_change", "parent_mix"]
)
def test_cold_postclose_reader_rejects_partial_successor(tmp_path, dependency, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, "pre_submit_delay", fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize(
    "fault", [None, "missing", "dirty", "committed_change", "parent_mix"]
)
def test_migration_configuration_keeps_exact_policy_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", "src/utils/constants.py"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
def test_migration_keeps_original_auxiliary_envelope_profile(tmp_path, family):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, "consumed_auxiliary_envelope"
    )


@pytest.mark.parametrize("damage", [None, "summary", "consumption", "policy", "pid", "expired"])
def test_resealed_postclose_distinguishes_prepared_from_consumed_generation(fixture, monkeypatch, damage):
    test_resealed_postclose_accepts_actual_new_pid_without_rewriting_original_summary(
        fixture, monkeypatch, damage, prepared=True)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_submit_probe_handoff_preserves_consumed_fixture(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_fixture"
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_SUBMIT_PROBE_HASHES))
def test_submit_probe_handoff_rejects_partial_successor(
    tmp_path, family, fault, dependency
):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_health_snapshot_handoff_keeps_live_predecessor(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_submit_probe",
        "src/engine/log_archive_service.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_HEALTH_SNAPSHOT_HASHES))
def test_health_snapshot_handoff_rejects_partial_successor(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_cumulative_hold_handoff_keeps_live_predecessor(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_health_snapshot",
        "src/engine/monitoring/runtime_performance.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_CUMULATIVE_HOLD_HASHES))
def test_cumulative_hold_handoff_rejects_partial_successor(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_closed_loader_handoff_keeps_live_predecessor(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_cumulative_hold",
        "src/engine/error_detectors/artifact_freshness.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_CLOSED_LOADER_HASHES))
def test_closed_loader_handoff_rejects_partial_successor(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_stop_index_handoff_preserves_prior_proof(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_stop_index",
        "src/engine/infrastructure/startup_validation_code_context.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_STOP_INDEX_HASHES))
def test_stop_index_handoff_rejects_mixed_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_ISOLATED_INDEX_HASHES))
def test_isolated_index_handoff_rejects_mixed_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
def test_isolated_index_complete_physical_formatted_successor(tmp_path, family):
    # Use actual source bytes: the restored assembler is a reviewed formatted
    # physical source, while the compatibility profile binds comparison bytes.
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, None, "current",
        "src/engine/infrastructure/startup_validation_code_context.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_SUFFIX_REPORT_HASHES))
def test_suffix_report_handoff_complete_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_suffix_report_handoff_preserves_issued_origin(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_isolated_index",
        "src/engine/automation/postclose_finalization_generation.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_QUANTITY_HISTORY_HASHES))
def test_quantity_history_handoff_complete_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_quantity_history_handoff_preserves_issued_origin(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "consumed_suffix_report",
        "src/engine/scalping/initial_quantity_monitor_projection.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_DRAIN_CLOSURE_HASHES))
def test_drain_closure_handoff_complete_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_drain_pointer_handoff_keeps_prior_issued_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "drain_closure",
        "src/engine/automation/ordered_intraday_deploy.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_HOLDING_QUOTE_HASHES))
def test_holding_quote_handoff_complete_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_holding_quote_handoff_keeps_consumed_pointer_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "drain_pointer",
        "src/engine/sniper_state_handlers.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_FINALIZATION_ADMISSION_HASHES))
def test_finalization_admission_handoff_complete_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_finalization_admission_keeps_prior_candidate(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "holding_quote",
        "src/engine/infrastructure/startup_validation_code_context.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_HOLDING_CAPABILITY_HASHES))
def test_holding_capability_handoff_complete_generation(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_holding_capability_keeps_deployed_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "finalization_admission",
        "src/engine/monitoring/policy_generation_code_handoff.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
@pytest.mark.parametrize("generation", ["finalization_admission", "holding_capability"])
def test_entry_latency_keeps_consumed_finalization_generation(tmp_path, family, fault, generation):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, generation,
        dependency="src/engine/scalping/mechanistic_entry_runtime_policy.py",
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_ENTRY_LATENCY_HASHES))
def test_entry_latency_rejects_partial_successor(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "current", dependency
    )


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_ENTRY_CAPABILITY_HASHES))
def test_entry_capability_requires_complete_exact_successor(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_entry_capability_keeps_deployed_latency_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "entry_latency",
        "src/engine/monitoring/policy_generation_code_handoff.py")


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", [None, "missing", "dirty", "committed_change", "parent_mix"])
@pytest.mark.parametrize("dependency", list(handoff.REVIEWED_PRECLAIM_DIAGNOSTIC_HASHES))
def test_preclaim_diagnostics_requires_complete_exact_successor(tmp_path, family, fault, dependency):
    test_entry_cost_handoff_keeps_exact_complete_generation(tmp_path, family, fault, "current", dependency)


@pytest.mark.parametrize("family", ["main_stop", "holding_vote", "pre_submit_delay"])
@pytest.mark.parametrize("fault", ["", "successor_mix"])
def test_preclaim_diagnostics_retains_consumed_generation(tmp_path, family, fault):
    test_entry_cost_handoff_keeps_exact_complete_generation(
        tmp_path, family, fault, "entry_capability", "src/engine/ai_engine_openai.py")
