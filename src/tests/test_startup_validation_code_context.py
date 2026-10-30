"""Native source-delta proofs survive only in a real isolated validation child."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from functools import lru_cache

import pytest

from src.engine.infrastructure import startup_validation_code_context as C
from src.engine.automation import intraday_release_handoff as H
from src.tests.test_main_policy_native_child import _source_copy

ROOT = Path(__file__).resolve().parents[2]
DAY = "2026-10-19"
RELATIVE = "src/engine/scalping/pre_submit_delay_tuning.py"


def _git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
    ).strip()


@lru_cache(maxsize=4)
def _historical_archive(commit):
    return subprocess.check_output([
        "git", "-C", str(ROOT), "archive", commit, "src", "deploy",
    ])


def _historical_code(root, revision):
    import io
    import tarfile

    archive = _historical_archive(_git(ROOT, "rev-parse", revision + "^{commit}"))
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(root, filter="data")


def _assert_current_code_profile(relative, current):
    """Current source assertions use both final readers, not a dated overlay."""
    raw = (ROOT / relative).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == current
    if relative in C.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE:
        assert current == C.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[relative]
    expected = H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[relative]
    compared = H.reviewed_formatting_source(relative, raw)
    assert hashlib.sha256(compared).hexdigest() == expected


def _commit(root, message):
    _git(root, "add", "src")
    if (root / "deploy").is_dir():
        _git(root, "add", "deploy")
    if (root / H._FORMATTING_REVIEW_PATH).is_file():
        _git(root, "add", H._FORMATTING_REVIEW_PATH)
    _git(
        root,
        "-c",
        "user.name=Validation Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        message,
    )
    return _git(root, "rev-parse", "HEAD")


def _native_releases(tmp_path_factory, *, current=False):
    base = tmp_path_factory.mktemp("native-code-context")
    root, selected = base / "candidate", base / "selected"
    # This fixture exercises the issued generic AST/docstring admission, not
    # a hybrid of the old issued monitor and today's unrelated consumers.
    # Restore that entire historical source generation through Git so new
    # transitive consumers cannot silently contaminate the historical profile.
    if current:
        _source_copy(root)
    else:
        root.mkdir()
        _historical_code(root, "003865007")
    # Independent preparation profiles include their real shell dispatchers.
    # A Python-only copy cannot exercise a complete candidate generation.
    for relative in dict.fromkeys(("src/run_bot.sh", *(
        name for name in H.REVIEWED_SUBMISSION_MONITOR_PROFILE if name.endswith(".sh")
    ))):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if current:
            target.write_bytes((ROOT / relative).read_bytes())
        else:
            assert target.is_file(), relative
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    original_commit = _commit(root, "genuine source origin")
    _git(root, "worktree", "add", "--detach", str(selected), original_commit)
    commit = original_commit
    if not current:
        path = root / RELATIVE
        old = path.read_text()
        changed = old.replace(
            "Preserve only a sealed same-day policy through the reviewed entry repair.",
            "Preserve only a sealed same-day policy through this reviewed entry repair.",
            1,
        )
        assert changed != old
        path.write_text(changed)
        commit = _commit(root, "behavior-preserving native accepted docstring change")
    paths = {RELATIVE: RELATIVE}
    expected = C._digest({RELATIVE: C._sha(selected / RELATIVE)})
    actual = C._digest({RELATIVE: C._sha(root / RELATIVE)})
    # Exercise the actual pre-isolation native delta validator, including Git
    # source identity and its allowed AST projection. No fake proof evaluator.
    assert H._verify_entry_code_delta(
        root, commit, original_commit, paths, expected
    ) == ([] if current else [RELATIVE])
    return dict(
        root=root,
        selected=selected,
        commit=commit,
        original_commit=original_commit,
        paths=paths,
        expected=expected,
        actual=actual,
    )


@pytest.fixture(scope="module")
def releases(tmp_path_factory):
    return _native_releases(tmp_path_factory)


@pytest.fixture(scope="module")
def current_releases(tmp_path_factory):
    return _native_releases(tmp_path_factory, current=True)


def _native_request(tmp_path, releases):
    run = tmp_path / uuid.uuid4().hex
    run.mkdir(mode=0o700)
    data = tmp_path / "fixture-data"
    selector = data / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(parents=True)
    selector.write_text(
        json.dumps(
            dict(
                schema="runtime_release_selection_v1",
                release_root=str(releases["selected"]),
                git_commit=releases["original_commit"],
                workspace=str(tmp_path),
            )
        )
    )
    policy = dict(
        schema="fixture_native_code_binding", code_contract_sha256=releases["expected"]
    )
    policy_sha = C._digest(policy)
    origin_sources = {
        str(selector): C._sha(selector),
        str(releases["selected"] / RELATIVE): C._sha(releases["selected"] / RELATIVE),
    }
    evidence = run / "bound-input.json"
    evidence.write_text('{"bound":true}')
    sources = {
        str(evidence): C._sha(evidence),
        **origin_sources,
        str(releases["root"] / RELATIVE): C._sha(releases["root"] / RELATIVE),
        str(
            releases["root"]
            / "src/engine/infrastructure/startup_validation_code_context.py"
        ): C._sha(
            releases["root"]
            / "src/engine/infrastructure/startup_validation_code_context.py"
        ),
    }
    origin = dict(
        origin_commit=releases["original_commit"],
        basis="selected_exact_code_contract",
        selected_release_root=str(releases["selected"]),
        selected_release_commit=releases["original_commit"],
        original_code_sha256=releases["expected"],
        selected_runtime_code_sha256=releases["expected"],
        sources=origin_sources,
    )
    proof = dict(
        schema=C.PROOF_SCHEMA,
        status="verified",
        target_date=DAY,
        family="pre_submit_delay",
        policy_sha256=policy_sha,
        original_code_sha256=releases["expected"],
        runtime_code_contract_sha256=releases["actual"],
        paths=releases["paths"],
        execution_release_root=str(releases["root"]),
        execution_release_commit=releases["commit"],
        policy_effect="unchanged",
        source_hashes=sources,
        origin=origin,
    )
    request = dict(
        schema=C.REQUEST_SCHEMA,
        run_id=run.name,
        run_directory=str(run),
        target_date=DAY,
        execution_release_root=str(releases["root"]),
        execution_release_commit=releases["commit"],
        data_root=str(data),
        source_hashes=sources,
        candidate_code_handoffs={"pre_submit_delay": proof},
        manifest={
            "target_date": DAY,
            "pre_submit_delay_handoff": {
                "target_date": DAY,
                "policy_sha256": policy_sha,
            },
        },
    )
    request["request_sha256"] = C._digest(request)
    path = run / "request.json"
    path.write_text(json.dumps(request))
    return dict(run=run, path=path, request=request, **releases)


@pytest.fixture
def request_fixture(tmp_path, releases):
    return _native_request(tmp_path, releases)


@pytest.fixture
def current_request_fixture(tmp_path, current_releases):
    return _native_request(tmp_path, current_releases)


def _write_request(fixture, request):
    request.pop("request_sha256", None)
    request["request_sha256"] = C._digest(request)
    fixture["path"].write_text(json.dumps(request))


def _child(fixture, body, *, isolated=True):
    root, run = fixture["root"], fixture["run"]
    code = """import json, os, pathlib, sys
sys.path.insert(0, sys.argv[1])
from src.engine.infrastructure.startup_validation_isolation import install_validation_isolation, assert_no_forbidden_attempts
from src.engine.infrastructure.startup_validation_code_context import install_validation_code_context, verify_validation_consumer_code
run = pathlib.Path(sys.argv[2])
request = json.loads((run / 'request.json').read_text())
"""
    if isolated:
        code += "install_validation_isolation(run, run / 'audit.jsonl')\n"
    code += body
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, str(root), str(run)],
        cwd=root,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        },
        start_new_session=True,
        close_fds=True,
        capture_output=True,
        text=True,
        timeout=40,
    )


CALL = """p = request['candidate_code_handoffs']['pre_submit_delay']
result = verify_validation_consumer_code(request['target_date'], family='pre_submit_delay',
    policy_sha=p['policy_sha256'], expected=p['original_code_sha256'], paths=p['paths'], actual=p['runtime_code_contract_sha256'])
"""


def test_no_context_leaves_normal_native_guard_untouched():
    assert (
        C.verify_validation_consumer_code(
            DAY,
            family="pre_submit_delay",
            policy_sha="a" * 64,
            expected="b" * 64,
            paths={"source": RELATIVE},
            actual="c" * 64,
        )
        is None
    )
    assert C.validate_preparation_delay_selection(None, None) is False


@pytest.mark.parametrize(
    "fault",
    [None, "expected", "origin", "selected", "changed_paths", "source", "execution"],
)
def test_execution_exact_policy_origin_is_independently_checked_in_child(
    request_fixture, fault
):
    fixture = request_fixture
    request = fixture["request"]
    proof = request["candidate_code_handoffs"]["pre_submit_delay"]
    proof["original_code_sha256"] = fixture["actual"]
    proof["changed_consumer_paths"] = []
    origin = proof["origin"]
    origin.update(
        basis="execution_exact_code_contract",
        origin_commit=fixture["commit"],
        original_code_sha256=fixture["actual"],
    )
    if fault == "expected":
        proof["original_code_sha256"] = origin["original_code_sha256"] = fixture[
            "expected"
        ]
    elif fault == "origin":
        origin["origin_commit"] = fixture["original_commit"]
    elif fault == "selected":
        origin["selected_release_commit"] = fixture["commit"]
    elif fault == "changed_paths":
        proof["changed_consumer_paths"] = [RELATIVE]
    elif fault == "source":
        proof["source_hashes"] = dict(proof["source_hashes"])
        proof["source_hashes"][str(fixture["root"] / RELATIVE)] = "0" * 64
    elif fault == "execution":
        proof["execution_release_commit"] = fixture["original_commit"]
    _write_request(fixture, request)
    child = _child(fixture, "install_validation_code_context(request)\n" + CALL)
    if fault:
        assert child.returncode != 0 and "startup_code_context_" in child.stderr
    else:
        assert child.returncode == 0, child.stderr
        assert (fixture["run"] / "audit.jsonl").read_bytes() == b""


@pytest.mark.parametrize("fault", [None, "old", "current", "sibling"])
def test_handoff_coordination_preparation_pair_is_exact(fault):
    name = "src/engine/scalping/reversal_code_handoff.py"
    old = C.REVIEWED_HANDOFF_COORDINATION_ORIGINS[name]
    current = C._sha(ROOT / name)
    _assert_current_code_profile(name, current)
    if fault == "old":
        old = "0" * 64
    elif fault == "current":
        current = "0" * 64
    elif fault == "sibling":
        name = "src/engine/scalping/unreviewed_coordination.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)


def test_install_outside_real_os_isolation_is_refused(request_fixture):
    result = _child(
        request_fixture, "install_validation_code_context(request)\n", isolated=False
    )
    assert result.returncode != 0
    assert "validation_isolation_not_complete" in result.stderr


def test_native_legacy_handoff_hook_imports_and_verifies_under_real_isolation(
    request_fixture,
):
    result = _child(
        request_fixture,
        """install_validation_code_context(request)
assert 'src.engine.automation.intraday_release_handoff' not in sys.modules
from src.engine.automation.intraday_release_handoff import verify_entry_consumer_code
p = request['candidate_code_handoffs']['pre_submit_delay']
result = verify_entry_consumer_code(request['target_date'], family='pre_submit_delay', policy_sha=p['policy_sha256'],
    expected=p['original_code_sha256'], paths=p['paths'], actual=p['runtime_code_contract_sha256'])
assert result['status'] == 'verified_intraday_consumer_repair', result
assert result['basis'] == 'main_startup_validation_code_context_v1', result
assert result['actual_pid_consumed'] is result['execution_authority'] is False
assert result['policy_effect'] == 'unchanged'
assert_no_forbidden_attempts()
print(json.dumps(result))
""",
    )
    assert result.returncode == 0, result.stderr
    assert (
        json.loads(result.stdout)["runtime_code_contract_sha256"]
        == request_fixture["actual"]
    )
    assert (request_fixture["run"] / "audit.jsonl").read_bytes() == b""
    assert not list(request_fixture["run"].glob("*handoff*.json"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_date", "2026-10-20"),
        ("policy_sha256", "d" * 64),
        ("original_code_sha256", "d" * 64),
        ("runtime_code_contract_sha256", "d" * 64),
        ("execution_release_commit", "d" * 40),
        ("policy_effect", "changed"),
        ("status", "pending"),
    ],
)
def test_bad_or_unbound_proof_never_installs(request_fixture, field, value):
    request = request_fixture["request"]
    request["candidate_code_handoffs"]["pre_submit_delay"][field] = value
    _write_request(request_fixture, request)
    result = _child(request_fixture, "install_validation_code_context(request)\n")
    assert result.returncode != 0
    assert "startup_code_context_" in result.stderr


@pytest.mark.parametrize(
    "change", ["day", "family", "policy", "expected", "actual", "paths"]
)
def test_native_call_arguments_must_match_exact_prevalidated_proof(
    request_fixture, change
):
    code = "install_validation_code_context(request)\np = request['candidate_code_handoffs']['pre_submit_delay']\n"
    code += "args = dict(day=request['target_date'], family='pre_submit_delay', policy_sha=p['policy_sha256'], expected=p['original_code_sha256'], paths=p['paths'], actual=p['runtime_code_contract_sha256'])\n"
    value = {
        "day": repr("2026-10-20"),
        "family": repr("main_stop"),
        "policy": repr("d" * 64),
        "expected": repr("d" * 64),
        "actual": repr("d" * 64),
        "paths": repr({"unexpected": RELATIVE}),
    }[change]
    key = "policy_sha" if change == "policy" else change
    code += (
        "args["
        + repr(key)
        + "] = "
        + value
        + "\nverify_validation_consumer_code(**args)\n"
    )
    result = _child(request_fixture, code)
    assert result.returncode != 0
    assert "consumer_binding_invalid" in result.stderr


def test_request_mutation_after_install_invalidates_even_caught_lookup(request_fixture):
    code = """install_validation_code_context(request)
request['target_date'] = '2026-10-20'
(run / 'request.json').write_text(json.dumps(request))
""" + CALL
    result = _child(request_fixture, code)
    assert result.returncode != 0
    assert "execution_changed" in result.stderr


def test_corrupt_source_and_origin_inventory_fail_even_with_fresh_request_digest(
    request_fixture,
):
    request = request_fixture["request"]
    proof = request["candidate_code_handoffs"]["pre_submit_delay"]
    proof["origin"]["selected_runtime_code_sha256"] = "e" * 64
    _write_request(request_fixture, request)
    result = _child(request_fixture, "install_validation_code_context(request)\n")
    assert result.returncode != 0
    assert "selected_contract_changed" in result.stderr


def test_source_bytes_mutation_after_context_install_fails_lookup(request_fixture):
    result = _child(
        request_fixture,
        """install_validation_code_context(request)
(run / 'bound-input.json').write_text('{"bound":false}')
""" + CALL,
    )
    assert result.returncode != 0
    assert "startup_code_context_source_changed" in result.stderr


def test_caught_bad_install_poisoned_context_cannot_fall_through_to_live(
    request_fixture,
):
    result = _child(
        request_fixture,
        """request['run_directory'] = str(run.parent)
try:
    install_validation_code_context(request)
except ValueError:
    pass
""" + CALL,
    )
    assert result.returncode != 0
    assert "startup_code_context_invalid" in result.stderr


def _main_fixture(f, monkeypatch):
    """Small native closure; economic schema is owned by native policy tests.

    Git, exact-pair checks, digest hashing and the OS child are real. A native
    CLI collection test separately proves these closure fields have a producer.
    """
    import time
    from src.engine.infrastructure.validation_digest_session import (
        DigestSession,
        identity,
    )
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_postclose as P

    req = f["request"]
    data = Path(req["data_root"])
    selected = f["selected"]
    root = f["root"]
    owner = "src/engine/scalping/reversal_path_runtime.py"
    original = C._sha(selected / owner)
    bundle = dict(
        bundle_sha256="b" * 64,
        target_date=DAY,
        continuous_reversal=dict(
            schema="continuous_reversal_policy_v4",
            family_sha256="c" * 64,
            release_commit=f["original_commit"],
            contract_file_sha256={"reversal_path_runtime.py": original},
        ),
    )
    path = (
        data
        / "runtime/mechanistic_entry_policy/candidates"
        / ("policy_" + DAY + ".json")
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(bundle))
    raw = data / "raw.bin"
    raw.write_bytes(b"a" * (2 * 1024 * 1024))
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    metadata = data / "metadata.sqlite3"
    metadata.write_bytes(b"private-ledger")
    frozen_path = selected / owner
    source = data / "source.json"
    source.write_text("{}")
    original_bundle = data / "old-bundle.json"
    original_bundle.write_text("{}")
    from src.engine.scalping import reversal_auxiliary_next_session as A

    manifest = P.seal(
        dict(
            base_bundle_sha256=bundle["bundle_sha256"],
            source_manifest={"path": str(source), "sha256": C._sha(source)},
            source_bundle={
                "path": str(original_bundle),
                "sha256": C._sha(original_bundle),
            },
            frozen_validator_root=str(selected),
            frozen_validator_commit=f["original_commit"],
            frozen_inventory={str(frozen_path): original},
            frozen_validation={"native": "fixture"},
            semantic_code_hashes={"reversal_path_runtime.py": original},
            next_session_code_hashes={},
            reader_code_hashes={},
            ledger_pack_paths=[],
            baseline_dependency_paths=[],
            sources=[
                {"path": str(v), "sha256": C._sha(v)}
                for v in (source, original_bundle, frozen_path, raw)
            ],
        )
    )
    manifest_path = data / "transition.json"
    manifest_path.write_text(json.dumps(manifest))
    observed = dict(
        path=str(manifest_path),
        sha256=C._sha(manifest_path),
        target_date=DAY,
        bundle_sha256=bundle["bundle_sha256"],
        database=None,
        dependencies=[
            [v["path"], json.loads(json.dumps(N._signature(v["path"])))]
            for v in manifest["sources"]
        ],
    )
    session = DigestSession(data, "2026-10-16", role="postclose", generation={})
    closure = dict(
        schema="startup_native_machine_closure_v1",
        run_id=req["run_id"],
        digest_binding=session.binding,
        digest_entries={
            str(raw): dict(identity=identity(raw), digest=digest, created=time.time())
        },
        bundles={
            bundle["bundle_sha256"]: {"target_date": DAY, "family_sha256": "c" * 64}
        },
        manifests={manifest["artifact_content_sha256"]: observed},
        frozen_inventories={str(selected): manifest["frozen_inventory"]},
        frozen_validations={
            str(source): dict(
                root=str(selected),
                bundle_path=str(original_bundle),
                result=manifest["frozen_validation"],
                invocation=dict(
                    executable=str(selected / ".venv/bin/python"),
                    arguments=["-B", "-c"],
                    script_sha256=hashlib.sha256(A._FROZEN_SCRIPT.encode()).hexdigest(),
                    cwd=str(selected),
                    source_manifest=str(source),
                    source_bundle=str(original_bundle),
                    environment=dict(
                        PYTHONPATH=str(selected), PYTHONDONTWRITEBYTECODE="1"
                    ),
                    parent_environment="sanitized_p5_native_verification",
                ),
            )
        },
    )
    native = dict(
        status="pass",
        findings=[],
        validation_scope="current_full_contract",
        target_date=DAY,
        selected_release_commit=f["original_commit"],
        source_date="2026-10-16",
        native_validation_io=dict(stats={"pid": os.getpid()}, remaining_entries=0),
    )
    code = {owner: original}
    sources = {
        str(path): C._sha(path),
        str(manifest_path): C._sha(manifest_path),
        str(data / "runtime/runtime_release_selection.json"): C._sha(
            data / "runtime/runtime_release_selection.json"
        ),
        str(selected / owner): original,
        str(root / owner): C._sha(root / owner),
    }
    # This helper's exact origin set is a unit seam. The real reviewed table
    # has separate Git/source-pair tests; this genuine unchanged byte is not a
    # manufactured PASS for a changed source.
    proof = dict(
        schema=C.MAIN_PROOF_SCHEMA,
        target_date=DAY,
        policy_path=str(path),
        policy_sha256=bundle["bundle_sha256"],
        policy_file_sha256=C._sha(path),
        execution_release_root=str(root),
        execution_release_commit=f["commit"],
        selected_release_root=str(selected),
        selected_release_commit=f["original_commit"],
        original_code_hashes=code,
        runtime_code_hashes=code,
        inventories=C._main_inventories(bundle),
        inventory_git_attestations={
            bundle["bundle_sha256"]: dict(
                origin_commit=f["original_commit"], code_hashes=code
            )
        },
        source_hashes=sources,
        closure=closure,
        native_verification=native,
        historical_semantic_code_sources={
            manifest["artifact_content_sha256"]: {
                owner: dict(path=str(frozen_path), sha256=original)
            }
        },
        delegation_basis="same_invocation_selected_native_full_verification",
        policy_effect="unchanged",
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_pid_consumed=False,
    )
    req.update(
        main_preparation_code_handoff=proof,
        expected_policy_hashes=dict.fromkeys(
            ("main_machine", "main_auxiliary"), bundle["bundle_sha256"]
        ),
    )
    req["source_hashes"].update(sources)
    _write_request(f, req)
    return dict(raw=raw, bundle=bundle, proof=proof, manifest=manifest)


# Fixtures below isolate the native-closure data model only. Real isolation,
# code-source byte/Git identity and digest generation checks remain active.
MAIN_CHILD_SETUP = """from src.engine.infrastructure import startup_validation_code_context as C
from src.engine.scalping import reversal_auxiliary_next_session as A
C.REVIEWED_PREPARATION_SOURCES = {}
A._database_signature = lambda manifest: None
install_validation_code_context(request)
"""


def _bind_stop_fixture(f, report):
    request = f["request"]
    proof = request["main_preparation_code_handoff"]
    data = Path(request["data_root"])
    report["report_sha256"] = C._digest(report)
    receipt = {k: report[k] for k in
               ("source_date", "target_date", "policy_sha256", "report_sha256")}
    receipt["generation"] = "e" * 64
    directory = data / "threshold_cycle/main_stop_confirmation/generations" / receipt["generation"]
    directory.mkdir(parents=True)
    report_path = directory / "report.json"
    report_path.write_text(json.dumps(report))
    (directory / "policy.json").write_text(json.dumps({
        k: report[k] for k in ("policy_sha256", "research_sha256")}))
    request["manifest"]["main_stop_confirmation_receipt"] = receipt
    closure = C._bind_stop_indexed_sources(data, receipt, proof["source_hashes"])
    proof["stop_indexed_sources"] = closure
    assert C._verify_stop_indexed_sources(proof, verify_native=True) == closure["entries"]
    request["source_hashes"].update(proof["source_hashes"])
    return closure, report_path


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "source",
        "index",
        "wal",
        "report",
        "missing",
        "scope",
        "lookup",
        "data_root",
        "generation",
    ],
)
@pytest.mark.parametrize("archived,alias", [(False, False), (True, False), (True, True)])
@pytest.mark.parametrize("cold", [False, True])
def test_indexed_stop_source_survives_real_isolation_only_with_exact_native_binding(
    request_fixture, monkeypatch, fault, archived, alias, cold
):
    from datetime import datetime
    from src.tests.test_holding_path_vote_replay import _events
    from src.engine.ai import holding_exit_vote as votes
    from src.engine.automation import main_trailing_source_store as S

    f = request_fixture
    state = _main_fixture(f, monkeypatch)
    request, proof = f["request"], state["proof"]
    data = Path(request["data_root"])
    day = "2026-10-16"
    at = datetime.fromisoformat(day + "T09:00:00+09:00").timestamp()
    if alias:
        from src.tests.test_main_trailing_source_store import append, row

        monkeypatch.setattr(S, "maintain", lambda *a: None)
        path = data / "ai_decision_trace" / ("ai_decision_trace_" + day + ".jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        append(data, path, row())
    else:
        path = votes.path_vote_store_path(data, "record:7")
        monkeypatch.setattr(votes.time, "time", lambda: at + 20)
        events = _events("EXIT_TRAILING_TP", "REGULAR", base_at=at, session_key=day)
        assert votes.append_path_events_file(path, "record:7", events)[1] == "appended"
    expected = S.generation(data, path)
    if archived:
        import gzip

        if alias:
            from src.engine.compress_db_backfilled_files import _gzip_file

            assert _gzip_file(path, dry_run=False)[0]
        else:
            Path(str(path) + ".gz").write_bytes(gzip.compress(path.read_bytes()))
            path.unlink()
            S.migrate_frozen_source(data, path)
    bound_path = Path(str(path) + ".gz") if alias else path
    if alias:
        expected = S.generation(data, bound_path)
    report = dict(source_date=day, target_date=DAY, policy_sha256="a" * 64,
                  research_sha256="d" * 64, vote_source_inventory={str(bound_path): expected})
    if cold:
        # End only this fixture's writer, exercising SQLite's real first-read
        # creation of an empty WAL without changing the frozen source bytes.
        for key, (connection, lock) in list(S._WRITERS.items()):
            if str(data) in key[1]:
                S._WRITERS.pop(key)
                connection.close()
        _, _, cold_index = S._location(data, path)
        assert not Path(str(cold_index) + "-wal").exists()
    closure, report_path = _bind_stop_fixture(f, report)
    _, _, index = S._location(data, path)
    if fault in {"source", "index", "wal", "report"}:
        damaged = {
            "source": Path(str(path) + ".gz") if archived else path,
            "index": index,
            "wal": Path(str(index) + "-wal"),
            "report": report_path,
        }[fault]
        with damaged.open("ab") as stream:
            stream.write(b"changed")
    elif fault == "missing":
        closure["entries"] = {}
    elif fault == "scope":
        closure["receipt"] = {**closure["receipt"], "target_date": "2026-10-20"}
    elif fault == "generation":
        closure["entries"][str(bound_path)]["generation"]["raw_records"] += 1
    _write_request(f, request)
    lookup = str(path) + ".segment-1" if fault == "lookup" else str(bound_path)
    root = str(data.parent) if fault == "data_root" else str(data)
    result = _child(
        f,
        MAIN_CHILD_SETUP + f"""
from src.engine.automation import main_trailing_source_assembler as A, main_trailing_source_store as S
expected = {expected!r}
assert S.generation is C.validation_indexed_source_generation
assert A.source_generation_matches({root!r}, {day!r}, {lookup!r}, expected)
if {bool(alias and fault is None)!r}:
    assert A.source_generation_matches({root!r}, {day!r}, {str(path)!r}, expected)
assert_no_forbidden_attempts()
""",
    )
    assert (result.returncode == 0) is (fault is None), result.stderr
    audit = (f["run"] / "audit.jsonl").read_text()
    assert "sqlite3.connect" not in audit


def test_main_preparation_digest_reuses_only_exact_parent_bytes_in_real_isolation(
    request_fixture, monkeypatch
):
    f = _main_fixture(request_fixture, monkeypatch)
    result = _child(
        request_fixture,
        MAIN_CHILD_SETUP + f"""
from src.engine.infrastructure.validation_digest_session import reused_digest
assert reused_digest({str(f['raw'])!r}) == {C._sha(f['raw'])!r}
assert reused_digest(run/'bound-input.json') is None
p=request['main_preparation_code_handoff']; bundle=json.loads(pathlib.Path(p['policy_path']).read_text())
assert C.verify_validation_main_code(bundle,{{'reversal_path_runtime.py':str(C.ROOT/'src/engine/scalping/reversal_path_runtime.py')}},bundle['continuous_reversal']['contract_file_sha256'])
r=C.validation_delegation_receipt()
assert r['digest_reused_reads']==1 and r['digest_reused_bytes']==2097152
assert r['allowed_runtime_apply'] is False
assert_no_forbidden_attempts()
""",
    )
    assert result.returncode == 0, result.stderr


def test_p5_recheck_native_closure_transfer_runs_real_reader(
    request_fixture, monkeypatch
):
    """The P5 child consumes the real closure reader, not a mocked verdict."""
    from src.engine.automation import main_startup_validation as P5
    from src.engine.scalping import reversal_auxiliary_next_session as A

    bound = _main_fixture(request_fixture, monkeypatch)
    root = request_fixture["root"]
    data = Path(request_fixture["request"]["data_root"])
    proof = bound["proof"]
    proof["selected_release_root"] = str(root)
    proof["selected_release_commit"] = request_fixture["commit"]
    proof["native_verification"]["selected_release_commit"] = request_fixture["commit"]
    (root / "data").symlink_to(data, target_is_directory=True)
    (root / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    auxiliary = root / "src/engine/scalping/reversal_auxiliary_next_session.py"
    auxiliary_original = auxiliary.read_text()
    auxiliary.write_text(auxiliary_original + "\ndef _database_signature(manifest): return None\n")
    raw = bound["raw"]
    cli = root / "src/engine/automation/next_preopen_readiness.py"
    cli_original = cli.read_text()
    cli.write_text(
        "import json\n"
        "from src.engine.infrastructure.validation_digest_session import reused_digest\n"
        f"assert reused_digest({str(raw)!r}) == {C._sha(raw)!r}\n"
        f"print(json.dumps(dict(status='pass', findings=[], target_date={DAY!r}, "
        "validation_scope='current_full_contract', actual_pid_consumed=False)))\n"
    )
    monkeypatch.setattr(A, "_database_signature", lambda manifest: None)
    monkeypatch.setattr(P5, "ROOT", root)
    try:
        result = P5._native_preparation_check(root, DAY, "2026-10-16", False, proof)
        stats = result["native_validation_io"]["stats"]
        assert result["validation_scope"] == "current_full_contract"
        assert stats["full_reads"] == 0
        assert stats["reused_bytes"] == 2 * 1024 * 1024
        assert stats["admitted_native_bytes"] == 2 * 1024 * 1024
    finally:
        auxiliary.write_text(auxiliary_original)
        cli.write_text(cli_original)
        (root / "data").unlink()
        (root / ".venv").unlink()


@pytest.mark.parametrize(
    "change",
    [
        "selector",
        "request",
        "selected_commit",
        "source_same_size",
        "source_alias",
        "parent_pid",
        "wrong_run",
        "wrong_data_root",
        "wrong_frozen_arguments",
        "missing_inventory",
    ],
)
def test_main_preparation_rejects_changed_generation_without_full_read(
    request_fixture, monkeypatch, change
):
    f = _main_fixture(request_fixture, monkeypatch)
    # Changes outside the child's private root occur before installation; the
    # parent never grants those writes to the actual isolated child.
    req = request_fixture["request"]
    proof = f["proof"]
    if change == "parent_pid":
        proof["closure"]["digest_binding"]["pid"] += 1
    elif change == "wrong_run":
        proof["closure"]["run_id"] = "f" * 32
    elif change == "wrong_data_root":
        proof["closure"]["digest_binding"]["resolved_root"] = str(
            f["raw"].parent.parent
        )
    elif change == "wrong_frozen_arguments":
        next(iter(proof["closure"]["frozen_validations"].values()))["invocation"][
            "arguments"
        ] = ["-c"]
    elif change == "missing_inventory":
        proof["original_code_hashes"] = {}
    elif change == "source_same_size":
        f["raw"].write_bytes(b"b" * f["raw"].stat().st_size)
    elif change == "source_alias":
        target = f["raw"].with_suffix(".replacement")
        target.write_bytes(f["raw"].read_bytes())
        f["raw"].unlink()
        f["raw"].symlink_to(target)
    elif change == "selector":
        target = Path(req["data_root"]) / "runtime/runtime_release_selection.json"
        value = json.loads(target.read_text())
        value["git_commit"] = "d" * 40
        target.write_text(json.dumps(value))
    elif change == "selected_commit":
        proof["selected_release_commit"] = "d" * 40
    elif change == "request":
        proof["policy_sha256"] = "d" * 64
    _write_request(request_fixture, req)
    result = _child(request_fixture, MAIN_CHILD_SETUP)
    assert result.returncode != 0
    assert "startup_" in result.stderr, result.stderr


def test_reviewed_main_code_pairs_are_exact_and_origin_is_not_relabelled(tmp_path, monkeypatch):
    # This assertion belongs to the issued cold-preparation generation.
    # A later exact runtime profile must not stand in for that original reader.
    _historical_code(tmp_path, "8940ea4ad0d3b64d30f67f986a75715ee24c1d95")
    monkeypatch.setattr(C, "ROOT", tmp_path)
    assert len(C.REVIEWED_PREPARATION_SOURCES) >= 13
    for path, (old, new) in C.REVIEWED_PREPARATION_SOURCES.items():
        # The cold-preparation registration belongs to this immutable parent;
        # later dependency generations are checked by their own native closure.
        raw = subprocess.check_output(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                "8940ea4ad0d3b64d30f67f986a75715ee24c1d95:" + path,
            ]
        )
        assert hashlib.sha256(raw).hexdigest() == new
        C._pairs({path: old}, {path: new})
        with pytest.raises(ValueError, match="unreviewed"):
            C._pairs({path: old}, {path: "0" * 64})
    with pytest.raises(ValueError, match="inventory_changed"):
        C._pairs({"owner": "a" * 64}, {})


@pytest.mark.parametrize(
    "change", ["selector", "selected_head", "candidate_head", "request_alias"]
)
@pytest.mark.parametrize("consumer", ["digest", "delay_selection"])
def test_installed_main_context_rechecks_control_generation_per_digest(
    request_fixture, monkeypatch, change, consumer
):
    import threading, time

    f = _main_fixture(request_fixture, monkeypatch)
    run = request_fixture["run"]
    if change == "selector":
        target = (
            Path(request_fixture["request"]["data_root"])
            / "runtime/runtime_release_selection.json"
        )
    elif change == "request_alias":
        target = request_fixture["path"]
    else:
        root = request_fixture["selected" if change == "selected_head" else "root"]
        meta = root / ".git"
        directory = (
            (root / meta.read_text().strip()[8:]).resolve() if meta.is_file() else meta
        )
        target = directory / "HEAD"
    before = target.read_bytes()
    errors = []

    def mutate():
        try:
            deadline = time.monotonic() + 20
            while not (run / "ready").exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("isolated child did not install")
                time.sleep(0.01)
            if change == "request_alias":
                replacement = run / "replacement.json"
                replacement.write_bytes(before)
                target.unlink()
                target.symlink_to(replacement)
            elif change == "selector":
                v = json.loads(before)
                v["git_commit"] = "d" * 40
                target.write_text(json.dumps(v))
            else:
                target.write_text("d" * 40 + "\n")
            (run / "continue").write_text("ready")
        except BaseException as exc:
            errors.append(exc)

    worker = threading.Thread(target=mutate)
    worker.start()
    try:
        result = _child(
            request_fixture,
            MAIN_CHILD_SETUP + f"""
import time
(run/'ready').write_text('installed')
while not (run/'continue').exists(): time.sleep(.01)
from src.engine.infrastructure.validation_digest_session import reused_digest
{'reused_digest(' + repr(str(f['raw'])) + ')' if consumer == 'digest' else 'C.validate_preparation_delay_selection(None, None)'}
""",
        )
    finally:
        worker.join(timeout=25)
        if target.is_symlink():
            target.unlink()
        target.write_bytes(before)
    assert not worker.is_alive() and not errors, errors
    assert result.returncode != 0
    assert "startup_" in result.stderr, result.stderr


@pytest.mark.parametrize(
    "change", [None, "content", "replacement", "parent_alias", "mode"]
)
def test_batched_anchor_check_preserves_identity_and_shared_parent_bounds(
    tmp_path, monkeypatch, change
):
    directory = tmp_path / "sources"
    directory.mkdir()
    files = [directory / str(i) for i in range(64)]
    for path in files:
        path.write_text("original")
    anchors = {str(path): C._request_identity(path) for path in files}
    if change == "content":
        files[-1].write_text("modified")
    elif change == "replacement":
        replacement = tmp_path / "replacement"
        replacement.write_text("original")
        replacement.replace(files[-1])
    elif change == "parent_alias":
        moved = tmp_path / "moved"
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
    elif change == "mode":
        directory.chmod(0o700)
    expected = all(
        C._request_identity(name) == before for name, before in anchors.items()
    )
    calls = []
    original = C.os.lstat

    def observed(name, *args, **kwargs):
        calls.append(str(name))
        return original(name, *args, **kwargs)

    monkeypatch.setattr(C.os, "lstat", observed)
    assert C._anchor_identities_unchanged(anchors) is expected
    assert expected is (change is None)
    if change is None:
        assert calls.count(str(directory)) == 2
        assert len(calls) < 4 * len(files)


@pytest.mark.parametrize(
    "damage",
    [None, "missing_shard", "corrupt_shard", "membership", "selection", "unobserved"],
)
def test_native_sharded_delay_preparation_delegates_observed_rebuild_in_real_isolation(
    current_request_fixture, monkeypatch, damage
):
    request_fixture = current_request_fixture
    from src.engine.automation import pre_submit_delay_partitioned_research as P
    from src.engine.scalping import pre_submit_delay_initial_policy as I
    from src.tests.test_pre_submit_delay_partitioned_research import fixture

    main = _main_fixture(request_fixture, monkeypatch)
    data = Path(request_fixture["request"]["data_root"])
    reference, _ = fixture(data, monkeypatch)
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.scalping.pre_submit_delay_tuning import family_source_ledger_path

    for directory in sorted(
        (data / "threshold_cycle").glob("date=*/family=pre_submit_delay")
    ):
        day = directory.parent.name.removeprefix("date=")
        rows = [
            json.loads(line)
            for path in directory.glob("part-execution-*.jsonl")
            for line in path.read_text().splitlines()
        ]
        raw = data / "pipeline_events" / ("pipeline_events_" + day + ".jsonl")
        raw.parent.mkdir(exist_ok=True)
        raw.write_text(
            "".join(
                json.dumps({**row, "event_type": "pipeline_event"}) + "\n"
                for row in rows
            )
        )
        seal(data, day)
        reference["source_receipt"]["ledger_generations"][day] = byte_generation(
            family_source_ledger_path(data, day)
        )
    report, policy = P.build(
        reference["qualified_projection"],
        reference["census"],
        output_root=data / "producer-evidence",
        source_date=reference["source_date"],
        publication_date="2026-10-18",
        effective_date=DAY,
        source_sha256=reference["source_sha256"],
        code_contract_sha256=I.code_contract(request_fixture["root"]),
        source_receipt=reference["source_receipt"],
    )
    pointer = I.publish(data, report, policy, expected_incumbent=None)
    report_path, policy_path, _, manifest = I.committed_paths(
        data, reference["source_date"]
    )
    expected_lookup = I.PreparedPolicy.from_artifacts(
        policy, report, target_date=DAY
    ).lookup(target_date=DAY, market="REGULAR")
    # Execute the exact collection hook embedded in the parent subprocess.
    # Its original validator is the real SQL whole-population implementation;
    # the small Main closure fixture is independent of this delay verdict.
    import ast
    from src.engine.automation import main_startup_validation as V

    tree = ast.parse(Path(V.__file__).read_text())
    native = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "_native_preparation_check"
    )
    script = next(
        n.value.value
        for n in ast.walk(native)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "script" for t in n.targets)
    )
    hook = next(
        n
        for n in ast.walk(ast.parse(script))
        if isinstance(n, ast.FunctionDef) and n.name == "delay"
    )
    namespace = dict(
        I=I,
        Path=Path,
        hashlib=hashlib,
        json=json,
        original_delay=P.validate,
        run_id=request_fixture["run"].name,
        closure=main["proof"]["closure"],
    )
    namespace["closure"]["delay_selections"] = {}
    exec(
        compile(
            ast.Module(body=[hook], type_ignores=[]),
            "<actual native delay collector>",
            "exec",
        ),
        namespace,
    )
    durable_policy, durable_report = I._read(policy_path), I._read(report_path)
    namespace["delay"](durable_policy, durable_report, target_date=DAY)
    collected = next(iter(namespace["closure"]["delay_selections"].values()))
    assert collected["parent_full_selection_recomputed"] is True
    if damage is None:
        from copy import deepcopy

        original = namespace["original_delay"]
        saved = deepcopy(namespace["closure"]["delay_selections"])
        namespace["closure"]["delay_selections"] = {}
        namespace["original_delay"] = lambda *a, **kw: False
        with pytest.raises(ValueError, match="startup_native_delay_result_invalid"):
            namespace["delay"](durable_policy, durable_report, target_date=DAY)
        assert namespace["closure"]["delay_selections"] == {}

        def failed(*a, **kw):
            raise ValueError("native_rebuild_failed")

        namespace["original_delay"] = failed
        with pytest.raises(ValueError, match="native_rebuild_failed"):
            namespace["delay"](durable_policy, durable_report, target_date=DAY)
        assert namespace["closure"]["delay_selections"] == {}
        namespace["original_delay"] = original
        namespace["closure"]["delay_selections"] = deepcopy(saved)
        next(iter(namespace["closure"]["delay_selections"].values()))[
            "documents_sha256"
        ] = ("0" * 64)
        with pytest.raises(ValueError, match="startup_native_delay_selection_conflict"):
            namespace["delay"](durable_policy, durable_report, target_date=DAY)
        assert (
            next(iter(namespace["closure"]["delay_selections"].values()))[
                "documents_sha256"
            ]
            == "0" * 64
        )
        namespace["closure"]["delay_selections"] = saved
    # Snapshot actual selected release code, which is byte-identical to the
    # native hook's delay inventory (the candidate changes only one docstring).
    for name, sha in collected["native_code_inventory"].items():
        path = request_fixture["selected"] / name
        assert C._sha(path) == sha
        main["proof"]["source_hashes"][str(path)] = sha
    for ref in collected["artifacts"].values():
        main["proof"]["source_hashes"][ref["path"]] = ref["sha256"]
    main["proof"]["delay_inventory_git_attestation"] = C._attest_delay_inventory(
        request_fixture["selected"],
        request_fixture["original_commit"],
        namespace["closure"]["delay_selections"],
        main["proof"]["source_hashes"],
    )
    req = request_fixture["request"]
    req["source_hashes"].update(main["proof"]["source_hashes"])
    req["candidate_code_handoffs"]["pre_submit_delay"]["policy_sha256"] = policy[
        "policy_sha256"
    ]
    req["manifest"]["pre_submit_delay_handoff"]["policy_sha256"] = policy[
        "policy_sha256"
    ]
    req["manifest"]["pre_submit_delay_handoff"]["policy_path"] = str(policy_path)
    if damage == "unobserved":
        namespace["closure"]["delay_selections"] = {}
    _write_request(request_fixture, req)
    native_env = dict(
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED="true",
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE=str(policy_path),
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_MANIFEST_SHA256=manifest[
            "manifest_sha256"
        ],
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE=DAY,
    )
    if damage in {"missing_shard", "corrupt_shard", "membership"}:
        shard = report_path.parent / report["qualified_projection_ref"]["path"]
        if damage == "membership":
            from src.engine.lifecycle import research_storage as S

            partition = next(S.iter_tree(report_path.parent, report["partitions_ref"]))
            shard = report_path.parent / partition["membership"]["path"]
        if damage == "missing_shard":
            shard.unlink()
        else:
            shard.write_text("{}")
    before = {
        str(path): (C._sha(path), path.stat().st_mtime_ns, path.stat().st_ctime_ns)
        for path in data.rglob("*")
        if path.is_file()
    }
    result = _child(
        request_fixture,
        MAIN_CHILD_SETUP + f"""
from src.engine.scalping import pre_submit_delay_tuning as T
from src.engine.scalping import pre_submit_delay_initial_policy as I
from src.engine.automation import pre_submit_delay_partitioned_research as P
out = T.prepare_runtime_policy(target_date={DAY!r}, env={native_env!r}, data_root=pathlib.Path({str(data)!r}))
if {damage!r} in ('missing_shard', 'corrupt_shard', 'membership', 'unobserved'):
    assert out['status'] == 'preparation_invalid', out
    assert T._PREPARED_DELAY_POLICY is None
else:
    assert out['status'] == 'prepared', out
    assert out['policy_sha256'] == {policy['policy_sha256']!r}
    selected = T._PREPARED_DELAY_POLICY.lookup(target_date={DAY!r}, market='REGULAR')
    assert selected == {expected_lookup!r}, selected
    if {damage!r} == 'selection':
        report, policy = I._read(pathlib.Path({str(report_path)!r})), I._read(pathlib.Path({str(policy_path)!r}))
        report['price_ready_pair_n'] += 1
        policy['report_sha256'] = I.digest({{k:v for k,v in report.items() if k!='policy_sha256'}})
        policy['policy_sha256'] = I.digest({{k:v for k,v in policy.items() if k!='policy_sha256'}})
        report['policy_sha256'] = policy['policy_sha256']
        try: I.validate(policy, report, target_date={DAY!r})
        except ValueError as exc:
            assert str(exc) == 'startup_delay_request_binding_invalid', str(exc)
        else: raise AssertionError('native selection recomputation was bypassed')
    receipt = C.validation_delegation_receipt()
    checked = receipt['delay_selections'][{policy['policy_sha256']!r}]
    assert checked['parent_full_selection_recomputed'] is True
    assert checked['child_recomputed'] is False
    assert checked['child_headers_and_physical_logical_trees_reverified'] is True
    for path, sha in C.preparation_delay_source_hashes().items():
        assert out['source_hashes'].setdefault(path, sha) == sha
    (run/'delay-result.json').write_text(json.dumps(dict(delegation=receipt,
        consumer=dict(status='loaded', source_hashes=out['source_hashes']))))
assert not list(run.glob('.verify-*'))
assert_no_forbidden_attempts()
""",
    )
    assert result.returncode == 0, result.stderr
    assert (request_fixture["run"] / "audit.jsonl").read_bytes() == b""
    after = {
        str(path): (C._sha(path), path.stat().st_mtime_ns, path.stat().st_ctime_ns)
        for path in data.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert pointer.exists()
    assert not list(data.rglob(".verify-*"))
    if damage is None:
        from copy import deepcopy

        result = json.loads((request_fixture["run"] / "delay-result.json").read_text())
        C.verify_preparation_delay_delegation(
            main["proof"], result["delegation"], req, result["consumer"]
        )
        sources = result["consumer"]["source_hashes"]
        assert len(sources) > 2
        for change in ("missing", "unknown", "child_recomputed", "source_missing"):
            value = deepcopy(result)
            if change == "missing":
                value["delegation"]["delay_selections"] = {}
            elif change == "unknown":
                value["delegation"]["delay_selections"]["0" * 64] = {}
            elif change == "child_recomputed":
                value["delegation"]["delay_selections"][policy["policy_sha256"]][
                    "child_recomputed"
                ] = True
            else:
                shard = next(
                    iter(
                        value["delegation"]["delay_selections"][
                            policy["policy_sha256"]
                        ]["source_hashes"]
                    )
                )
                value["consumer"]["source_hashes"].pop(shard)
            with pytest.raises(ValueError, match="startup_delay_child_selection_"):
                C.verify_preparation_delay_delegation(
                    main["proof"], value["delegation"], req, value["consumer"]
                )
        shard = next(
            iter(
                result["delegation"]["delay_selections"][policy["policy_sha256"]][
                    "source_hashes"
                ]
            )
        )
        Path(shard).write_bytes(b"{}")
        with pytest.raises(ValueError, match="research_shard_generation_changed"):
            C.verify_preparation_delay_delegation(
                main["proof"], result["delegation"], req, result["consumer"]
            )
        with pytest.raises(ValueError, match="startup_source_changed"):
            V._recheck(sources)


@pytest.mark.parametrize("damage", ["pid", "invalid_context"])
def test_delegated_delay_selection_rejects_stale_context(
    request_fixture, monkeypatch, damage
):
    _main_fixture(request_fixture, monkeypatch)
    result = _child(
        request_fixture,
        MAIN_CHILD_SETUP + f"""
if {damage!r} == 'pid': C._CONTEXT['pid'] += 1
else: C._CONTEXT['valid'] = False
C.validate_preparation_delay_selection(None, None)
""",
    )
    assert result.returncode != 0
    assert "startup_code_context_" in result.stderr
    assert not list(request_fixture["run"].glob(".verify-*"))


def test_delay_physical_source_collection_obeys_claim_and_rejects_alias_generations(
    tmp_path, monkeypatch
):
    from src.engine.lifecycle import research_storage as S, research_input_budget as B

    ref = S.write_tree(tmp_path, iter(()))
    path = tmp_path / ref["path"]
    raw = path.read_bytes()
    replacement = raw + b" "
    changed = {
        **ref,
        "sha256": hashlib.sha256(replacement).hexdigest(),
        "size": len(replacement),
    }

    # Isolate the second physical-source/CAS walk. End-to-end tests above run
    # the actual logical/physical native reader and all nested membership rows.
    def rows(root, reference):
        if reference is changed:
            path.write_bytes(replacement)
        return iter(())

    monkeypatch.setattr(S, "iter_tree", rows)
    report = dict(qualified_projection_ref=ref, partitions_ref=changed, cells_ref=ref)
    used = B.health()["used_bytes"]
    with monkeypatch.context() as limits:
        limits.setattr(B, "LIMIT_BYTES", used + 1)
        with pytest.raises(
            ValueError, match="shared_research_budget_partition_resume_required"
        ):
            C._delay_tree_sources(tmp_path, report)
    assert B.health()["used_bytes"] == used
    with pytest.raises(ValueError, match="startup_delay_shard_reference_conflict"):
        C._delay_tree_sources(tmp_path, report)
    assert B.health()["used_bytes"] == used


def test_ordinary_digest_session_does_not_opt_in_new_reporting_consumers(
    tmp_path, monkeypatch
):
    from src.engine.infrastructure import validation_digest_session as D
    from src.engine.infrastructure import main_policy_loading as M
    from src.engine.automation import auxiliary_reader_readiness as A

    path = tmp_path / "raw.bin"
    path.write_bytes(b"a" * 1048576)

    class Unrelated:
        def digest(self, path):
            raise AssertionError("generic session was incorrectly consumed")

    token = D.ACTIVE.set(Unrelated())
    try:
        assert M._sources(path) == {str(path): C._sha(path)}
        assert A._sha(path) == C._sha(path)
    finally:
        D.ACTIVE.reset(token)


def _cold_workflow_preparation(data, proof, native, root, commit, source):
    """Frozen native preparation fixture, with actual Git/source bytes."""
    import time
    from src.engine.infrastructure.validation_digest_session import identity

    raw = data / "cold-predecessor-history.bin"
    with raw.open("wb") as stream:
        stream.truncate(64 * 1024 * 1024 + 1)
    raw_sha = C._sha(raw)
    proof["closure"]["digest_entries"][str(raw)] = dict(
        identity=identity(raw), digest=raw_sha, created=time.time()
    )
    observation = dict(
        source_date=native["source_date"],
        prepared_target_date=DAY,
        release_commit=proof["selected_release_commit"],
        runtime_effect=False,
        actual_pid_consumed=False,
        allowed_runtime_apply=False,
        source_hashes={str(source): C._sha(source), str(raw): raw_sha},
    )
    native.update(
        verification_code_root=str(root),
        verification_code_commit=commit,
        stopped_postclose_observation=observation,
    )
    directory = data / "runtime/policy_bootstrap/prepared" / DAY / "workflow"
    directory.mkdir(parents=True)
    receipt = dict(
        schema="next_preopen_readiness_v1",
        status="prepared_verified",
        source_date=native["source_date"],
        target_date=DAY,
        selected_release_commit=proof["selected_release_commit"],
        runtime_effect=False,
        actual_pid_consumed=False,
        policy_receipts=[],
        manifest_content_sha256="b" * 64,
        activation_candidate={"bundle_sha256": proof["policy_sha256"]},
        verification_workflow=dict(
            code_root=str(root),
            code_commit=commit,
            native_cold_review_sha256=C._digest(observation),
            runtime_effect=False,
            actual_pid_consumed=False,
        ),
    )
    refs = {}
    for name, digest in (
        ("manifest_path", "manifest_file_sha256"),
        ("env_path", "env_sha256"),
        ("verification_path", "verification_sha256"),
        ("controller_path", "controller_sha256"),
        ("summary_path", "summary_sha256"),
    ):
        path = directory / (name + ".json")
        path.write_text(
            json.dumps(
                dict(
                    manifest_sha256="b" * 64,
                    target_date=DAY,
                    selected_release_sha=proof["selected_release_commit"],
                )
            )
        )
        receipt[name], receipt[digest] = str(path), C._sha(path)
        refs[str(path)] = C._sha(path)
    path = directory / "readiness.json"
    path.write_text(json.dumps(receipt))
    sha = C._sha(path)
    refs[str(path)] = sha
    (directory.parent / "latest.json").write_text(
        json.dumps(
            dict(
                schema="next_preopen_readiness_index_v1",
                target_date=DAY,
                receipt_path=str(path),
                receipt_sha256=sha,
            )
        )
    )
    proof["closure"]["preserved_generations"] = {
        sha: dict(
            schema="startup_native_prepared_preopen_closure_v1",
            target_date=DAY,
            selected_release_commit=proof["selected_release_commit"],
            prepared_receipt_path=str(path),
            sources=refs,
            prepared_manifest_sha256="b" * 64,
            full_bootstrap=dict(
                path=receipt["manifest_path"],
                sha256=receipt["manifest_file_sha256"],
                write=False,
                full_native_verification=True,
                result=dict(
                    status="pass",
                    findings=[],
                    target_date=DAY,
                    manifest_sha256="b" * 64,
                ),
            ),
        )
    }
    return raw


@pytest.mark.parametrize(
    "reader_generation",
    ["original", "reviewed", "unreviewed", "workflow", "issuer_workflow"],
)
def test_nested_native_inventories_keep_distinct_git_origins(
    tmp_path, tmp_path_factory, monkeypatch, reader_generation
):
    """Parent native semantics are isolated; actual two-generation Git bytes
    and per-bundle validation stay real, including an old embedded V4 parent.
    """
    from src.engine.scalping import continuous_reversal_postclose as P

    r = releases.__wrapped__(tmp_path_factory)
    f = request_fixture.__wrapped__(tmp_path, r)
    fixture = _main_fixture(f, monkeypatch)
    owner = "src/engine/scalping/reversal_path_runtime.py"
    source = r["root"] / owner
    old = C._sha(source)
    source.write_bytes(
        source.read_bytes() + b"\n# Exact private code-origin fixture.\n"
    )
    commit = _commit(r["root"], "distinct current native source generation")
    new = C._sha(source)
    # This test reviews one private fixture edit, not a production successor.
    # Keep the complete fixture inventory while substituting that exact Git
    # endpoint; real missing/dirty/mixed profile tests use the unchanged table.
    original_profile = C.REVIEWED_P5_RECHECK_PROFILE
    monkeypatch.setattr(C, "REVIEWED_P5_RECHECK_PROFILE", {
        **original_profile, owner: new,
    })
    native_pair = C.reviewed_preparation_pair

    def private_fixture_pair(relative, before, after, *, root=None):
        # Preserve both complete private generations. Select only profile
        # facts here; the real native predicate still verifies every byte,
        # endpoint and explicit predecessor/candidate comparison root.
        with monkeypatch.context() as phase:
            if root == r["selected"]:
                phase.setattr(C, "REVIEWED_P5_RECHECK_PROFILE", original_profile)
            return native_pair(relative, before, after, root=root)

    monkeypatch.setattr(C, "reviewed_preparation_pair", private_fixture_pair)
    parent = fixture["bundle"]
    bundle = dict(
        bundle_sha256="d" * 64,
        target_date=DAY,
        continuous_reversal=dict(
            schema="continuous_reversal_policy_v6",
            family_sha256="e" * 64,
            release_commit=(
                r["original_commit"]
                if reader_generation in {"workflow", "issuer_workflow"}
                else commit
            ),
            contract_file_sha256={
                "reversal_path_runtime.py": (
                    old if reader_generation == "issuer_workflow" else new
                )
            },
            native_parent_bundle=parent,
        ),
    )
    proof = fixture["proof"]
    policy = Path(proof["policy_path"])
    policy.write_text(json.dumps(bundle))
    previous = fixture["manifest"]
    manifest = P.seal(
        {
            **previous,
            "base_bundle_sha256": bundle["bundle_sha256"],
            "semantic_code_hashes": {"reversal_path_runtime.py": old},
        }
    )
    if reader_generation != "original":
        reader_hash = (
            new
            if reader_generation in {"reviewed", "workflow", "issuer_workflow"}
            else "f" * 64
        )
        manifest = P.seal(
            {**manifest, "reader_code_hashes": {Path(owner).name: reader_hash}}
        )
        monkeypatch.setattr(C, "REVIEWED_PREPARATION_HISTORY", {owner: {(new, old)}})
    observed = next(iter(proof["closure"]["manifests"].values()))
    Path(observed["path"]).write_text(json.dumps(manifest))
    observed.update(
        bundle_sha256=bundle["bundle_sha256"], sha256=C._sha(observed["path"])
    )
    closure = proof["closure"]
    closure["manifests"] = {manifest["artifact_content_sha256"]: observed}
    closure["bundles"][bundle["bundle_sha256"]] = dict(
        target_date=DAY, family_sha256="e" * 64
    )
    native = {**proof["native_verification"], "native_machine_closure": closure}
    if reader_generation in {"workflow", "issuer_workflow"}:
        from src.engine.scalping import mechanistic_entry_runtime_policy as N

        observed["dependencies"].append(
            [str(source), json.loads(json.dumps(N._signature(source)))]
        )
        proof["policy_sha256"] = bundle["bundle_sha256"]
        cold_raw = _cold_workflow_preparation(
            Path(f["request"]["data_root"]), proof, native, r["root"], commit, source
        )
    intake = dict(
        selected_root=r["selected"],
        selected_commit=r["original_commit"],
        manifest={"target_date": DAY},
        receipt={"activation_candidate": {"bundle_sha256": bundle["bundle_sha256"]}},
        native_verification=native,
    )
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_SOURCES", {owner: (old, new)})
    monkeypatch.setattr(C, "ROOT", r["root"])
    # SQLite metadata semantics are exercised by native auxiliary tests.
    from src.engine.scalping import reversal_auxiliary_next_session as A

    monkeypatch.setattr(A, "_database_signature", lambda manifest: None)
    if reader_generation == "unreviewed":
        with pytest.raises(ValueError, match="origin_inventory_conflict"):
            C.bind_main_preparation(
                r["root"], commit, Path(f["request"]["data_root"]), intake
            )
        return
    result = C.bind_main_preparation(
        r["root"], commit, Path(f["request"]["data_root"]), intake
    )
    if reader_generation == "reviewed":
        assert manifest["reader_code_hashes"][Path(owner).name] == new
        assert result["original_code_hashes"][owner] == old
    assert result["inventories"][0]["expected"]["reversal_path_runtime.py"] == (
        old if reader_generation == "issuer_workflow" else new
    )
    assert result["inventories"][1]["expected"]["reversal_path_runtime.py"] == old
    request = dict(
        f["request"],
        execution_release_commit=commit,
        expected_policy_hashes=dict.fromkeys(
            ("main_machine", "main_auxiliary"), bundle["bundle_sha256"]
        ),
        source_hashes={**f["request"]["source_hashes"], **result["source_hashes"]},
    )
    C._main_proof(result, request)
    # The independent header reader retains its 64 MiB cap. Cold raw history
    # has native digest/identity custody and must not become a generic header.
    from src.engine.automation import main_startup_validation as V

    V._recheck(result["source_hashes"])
    if reader_generation in {"workflow", "issuer_workflow"}:
        assert result["inventories"][0]["origin_commit"] == r["original_commit"]
        assert result["inventory_git_attestations"][bundle["bundle_sha256"]][
            "origin_commit"
        ] == (
            r["original_commit"] if reader_generation == "issuer_workflow" else commit
        )
        assert result["source_hashes"][str(source)] == new
        assert result["native_reader_code_sources"] == {owner: new}
        import copy

        item = result["inventories"][0]
        for key, changed in (
            ("prepared_target_date", "2026-10-20"),
            ("source_date", "2026-10-15"),
            ("release_commit", "0" * 40),
            ("actual_pid_consumed", True),
        ):
            damaged = copy.deepcopy(result)
            damaged["native_verification"]["stopped_postclose_observation"][
                key
            ] = changed
            with pytest.raises(ValueError, match="workflow_origin_unbound"):
                C._main_inventory_origin(item, damaged)
        damaged = copy.deepcopy(result)
        damaged["native_verification"]["verification_code_commit"] = r[
            "original_commit"
        ]
        with pytest.raises(ValueError, match="native_verifier_code_identity"):
            C._main_inventory_origin(item, damaged)
        damaged = copy.deepcopy(result)
        damaged["closure"]["preserved_generations"] = {}
        with pytest.raises(ValueError, match="workflow_preparation_required"):
            C._main_inventory_origin(item, damaged)
        damaged = copy.deepcopy(result)
        damaged["inventory_git_attestations"][bundle["bundle_sha256"]][
            "origin_commit"
        ] = (commit if reader_generation == "issuer_workflow" else r["original_commit"])
        with pytest.raises(ValueError, match="inventory_git_attestation_changed"):
            C._main_proof(damaged, request)
    assert (
        result["inventory_git_attestations"][parent["bundle_sha256"]]["origin_commit"]
        == r["original_commit"]
    )
    assert (
        result["historical_semantic_code_sources"][manifest["artifact_content_sha256"]][
            owner
        ]["sha256"]
        == old
    )
    monkeypatch.setattr(C, "_main_context", lambda: result)
    for value in (bundle, parent):
        assert C.verify_validation_main_code(
            value,
            {"reversal_path_runtime.py": str(source)},
            {"reversal_path_runtime.py": new},
        )
    import copy

    wrong = copy.deepcopy(parent)
    wrong["continuous_reversal"]["contract_file_sha256"]["reversal_path_runtime.py"] = (
        "f" * 64
    )
    with pytest.raises(ValueError, match="inventory_unbound"):
        C.verify_validation_main_code(
            wrong,
            {"reversal_path_runtime.py": str(source)},
            {"reversal_path_runtime.py": new},
        )
    bundle["continuous_reversal"]["native_parent_bundle"]["continuous_reversal"][
        "release_commit"
    ] = commit
    policy.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match="inventory_git_origin_changed"):
        C.bind_main_preparation(
            r["root"], commit, Path(f["request"]["data_root"]), intake
        )
    if reader_generation in {"workflow", "issuer_workflow"}:
        with cold_raw.open("r+b") as stream:
            stream.write(b"x")
        with pytest.raises(ValueError, match="code_context_source_changed"):
            C._main_inventory_origin(result["inventories"][0], result)


def _logical_fixture(f, monkeypatch):
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.scalping import reversal_auxiliary_next_session as A
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.infrastructure.validation_digest_session import identity

    value = _main_fixture(f, monkeypatch)
    proof = value["proof"]
    data = Path(f["request"]["data_root"])
    metadata = dict(object_ids=[], request_ids=[], generations=[])
    with S.Store(data) as store:
        metadata["fingerprint_sha256"] = J._ledger_fingerprint(store, metadata)
    manifest = P.seal(
        {
            **value["manifest"],
            "policy_data_root": str(data),
            "ledger_data_root": str(data),
            "ledger_metadata": metadata,
        }
    )
    closure = proof["closure"]
    old = next(iter(closure["manifests"]))
    observed = closure["manifests"][old]
    path = Path(observed["path"])
    path.write_text(json.dumps(manifest))
    database = json.loads(json.dumps(A._database_signature(manifest)))
    observed.update(
        sha256=C._sha(path),
        database=database,
        database_source_identities={
            v[0]: identity(v[0]) for v in database if v is not None
        },
    )
    ident = manifest["artifact_content_sha256"]
    closure["manifests"] = {ident: observed}
    proof["historical_semantic_code_sources"] = {
        ident: proof["historical_semantic_code_sources"][old]
    }
    proof["source_hashes"][str(path)] = observed["sha256"]
    f["request"]["source_hashes"][str(path)] = observed["sha256"]
    _write_request(f, f["request"])
    value.update(manifest=manifest, database=Path(database[0][0]))
    return value


def test_native_logical_database_has_separate_exact_receipt_and_no_fullbyte_read(
    request_fixture, monkeypatch
):
    f = _logical_fixture(request_fixture, monkeypatch)
    setup = MAIN_CHILD_SETUP.replace(
        "A._database_signature = lambda manifest: None\n", ""
    )
    result = _child(
        request_fixture,
        setup + f"""
from src.engine.infrastructure import main_policy_loading as M
database=pathlib.Path({str(f['database'])!r})
original=pathlib.Path.open
def reject_db_bytes(path,*args,**kwargs):
    if path==database: raise AssertionError('global DB byte hash is not a logical receipt')
    return original(path,*args,**kwargs)
pathlib.Path.open=reject_db_bytes
logical={{}}
assert M._sources(database,logical_source_receipts=logical)=={{}}
assert set(logical)=={{str(database)}}
assert logical[str(database)]['source_kind']=='sqlite_ledger_container'
assert logical[str(database)]['manifest_proofs']
assert M._sources(run/'bound-input.json',logical_source_receipts={{}})
(run/'logical.json').write_text(json.dumps(logical))
assert_no_forbidden_attempts()
""",
    )
    assert result.returncode == 0, result.stderr
    receipts = json.loads((request_fixture["run"] / "logical.json").read_text())
    # Fresh finite native rows, independent from the expired large-file cache.
    for entry in f["proof"]["closure"]["digest_entries"].values():
        entry["created"] = 0
    assert C.verify_preparation_logical_sources(f["proof"], receipts) == receipts
    with pytest.raises(ValueError, match="source_set_changed"):
        C.verify_preparation_logical_sources(f["proof"], {})
    bad = json.loads(json.dumps(receipts))
    next(iter(bad.values()))["manifest_proofs"] = {}
    with pytest.raises(ValueError, match="source_set_changed"):
        C.verify_preparation_logical_sources(f["proof"], bad)
    changed = f["database"].with_suffix(".replacement")
    changed.write_bytes(f["database"].read_bytes())
    changed.replace(f["database"])
    with pytest.raises(ValueError, match="database_changed|identity_changed"):
        C.verify_preparation_logical_sources(f["proof"], receipts)


def test_logical_source_rechecks_native_selected_rows_and_unknown_db_keeps_full_read(
    request_fixture, monkeypatch
):
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.infrastructure import main_policy_loading as M

    f = _logical_fixture(request_fixture, monkeypatch)
    receipts = C._native_logical_sources(f["proof"])
    monkeypatch.setattr(J, "_ledger_fingerprint", lambda *a: "0" * 64)
    with pytest.raises(ValueError, match="ledger_changed"):
        C.verify_preparation_logical_sources(f["proof"], receipts)
    unrelated = request_fixture["run"] / "unknown.sqlite3"
    unrelated.write_bytes(b"unregistered database")
    logical = {}
    assert M._sources(unrelated, logical_source_receipts=logical) == {
        str(unrelated): C._sha(unrelated)
    }
    assert logical == {}


@pytest.fixture(scope="module")
def delay_contract_origins(tmp_path_factory):
    """Exact historical/current Git bytes, committed into private checkouts.

    These are source-inventory fixtures, not native selection/P5 verdicts.
    """
    result = {}
    for label, revision, count in (
        ("original", "900234d791b0bf31797cd4e823d0ae40296f790b", 27),
        ("current", "HEAD", 28),
    ):
        root = tmp_path_factory.mktemp("delay-origin-" + label)
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", revision + ":" + C._DELAY_CONTRACT_OWNER]
        )
        paths = C._delay_contract_paths(raw)
        assert len(paths) == count
        inventory = {}
        for relative in paths:
            value = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", revision + ":" + relative]
            )
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
            inventory[relative] = hashlib.sha256(value).hexdigest()
        _git(root, "init", "-q")
        commit = _commit(root, "Exact " + label + " delay inventory bytes")
        records = {
            str(target): {"native_code_inventory": dict(inventory)}
            for target in (None, DAY)
        }
        result[label] = dict(
            root=root, commit=commit, inventory=inventory, paths=paths, records=records
        )
    assert set(result["current"]["paths"]) - set(result["original"]["paths"]) == {
        "src/engine/infrastructure/main_policy_loading.py"
    }
    return result


@pytest.mark.parametrize("label", ["original", "current"])
def test_delay_inventory_attests_exact_origin_declaration_not_current_keys(
    delay_contract_origins, label
):
    case = delay_contract_origins[label]
    sources = {}
    proof = C._attest_delay_inventory(
        case["root"], case["commit"], case["records"], sources
    )
    assert proof["contract_paths"] == case["paths"]
    assert proof["code_hashes"] == case["inventory"]
    assert proof["origin_commit"] == case["commit"]
    assert proof["declaration_sha256"] == case["inventory"][C._DELAY_CONTRACT_OWNER]
    assert sources == {
        str(case["root"] / path): sha for path, sha in case["inventory"].items()
    }


@pytest.mark.parametrize("damage", [None, "foreign", "mixed_commit"])
def test_candidate_native_delay_inventory_keeps_original_policy_origin_separate(
    delay_contract_origins, damage
):
    old, new = delay_contract_origins["original"], delay_contract_origins["current"]
    proof = dict(
        selected_release_root=str(old["root"]),
        selected_release_commit=old["commit"],
        execution_release_root=str(new["root"]),
        execution_release_commit=new["commit"],
        native_verification=dict(
            verification_code_root=str(new["root"]),
            verification_code_commit=new["commit"],
        ),
    )
    if damage == "foreign":
        proof["native_verification"]["verification_code_root"] = str(new["root"].parent)
    if damage == "mixed_commit":
        proof["native_verification"]["verification_code_commit"] = old["commit"]
    if damage:
        with pytest.raises(ValueError, match="native_verifier_code_identity"):
            C._native_verifier_code(proof)
    else:
        root, commit = C._native_verifier_code(proof)
        assert root == new["root"] and commit == new["commit"]
        with pytest.raises(ValueError, match="native_code_inventory"):
            C._attest_delay_inventory(old["root"], old["commit"], new["records"], {})
        assert (
            C._attest_delay_inventory(root, commit, new["records"], {})["code_hashes"]
            == new["inventory"]
        )


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "digest",
        "mixed_old_new",
        "mixed_new_old",
        "origin_commit",
        "source_conflict",
    ],
)
def test_delay_inventory_rejects_unknown_or_mixed_origin(
    delay_contract_origins, damage
):
    from copy import deepcopy

    case = delay_contract_origins[
        "current" if damage == "mixed_new_old" else "original"
    ]
    records = deepcopy(case["records"])
    commit = case["commit"]
    sources = {}
    first = next(iter(records.values()))["native_code_inventory"]
    if damage == "missing":
        first.pop(next(iter(first)))
    elif damage == "extra":
        first["src/engine/infrastructure/main_policy_loading.py"] = "0" * 64
    elif damage == "digest":
        first[next(iter(first))] = "0" * 64
    elif damage == "mixed_old_new":
        first.update(delay_contract_origins["current"]["inventory"])
    elif damage == "mixed_new_old":
        records[next(iter(records))]["native_code_inventory"] = delay_contract_origins[
            "original"
        ]["inventory"]
    elif damage == "origin_commit":
        commit = "0" * 40
    else:
        sources[str(case["root"] / C._DELAY_CONTRACT_OWNER)] = "0" * 64
    with pytest.raises(ValueError, match="startup_delay_native_"):
        C._attest_delay_inventory(case["root"], commit, records, sources)


@pytest.mark.parametrize("damage", ["dirty", "symlink", "unknown_committed"])
def test_delay_inventory_requires_actual_files_and_exact_git_objects(
    delay_contract_origins, tmp_path, damage
):
    import shutil

    case = delay_contract_origins["original"]
    root = tmp_path / "source"
    shutil.copytree(case["root"], root)
    path = root / C._DELAY_CONTRACT_OWNER
    if damage == "symlink":
        saved = path.with_suffix(".saved")
        path.rename(saved)
        path.symlink_to(saved)
        commit = case["commit"]
    else:
        path.write_bytes(path.read_bytes() + b"\n# Changed origin file.\n")
        commit = (
            _commit(root, "Unknown new source bytes")
            if damage == "unknown_committed"
            else case["commit"]
        )
    with pytest.raises(ValueError, match="startup_delay_native_"):
        C._attest_delay_inventory(root, commit, case["records"], {})


@pytest.mark.parametrize(
    "expression",
    [
        "('src/unknown.py',)",
        "(OWNER,)",
        "('src/../bad.py', OWNER)",
        "(OWNER, OWNER)",
        "[OWNER]",
        "(False, OWNER)",
    ],
)
def test_delay_inventory_declaration_is_literal_unique_and_canonical(expression):
    declaration = expression.replace("OWNER", repr(C._DELAY_CONTRACT_OWNER))
    if expression == "(OWNER,)":
        declaration = "(dynamic_path,)"
    with pytest.raises(ValueError):
        C._delay_contract_paths(("CONTRACT_PATHS = " + declaration).encode())


@pytest.mark.parametrize("fault", [None, "source", "target", "path"])
@pytest.mark.parametrize(
    "relative,old,current,revision",
    [
        (
            "src/engine/ai_engine_openai.py",
            "194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584",
            "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
            "d927d0d70",
        ),
        (
            "src/engine/scalping/entry_machine_source_recovery.py",
            "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "a78c70c5c49169ccb57069df7a524a540a33b615617a49195ddbc343ff9602a5",
            "193668e7f",
        ),
    ],
)
def test_issued_source_preparation_pair_is_exact(
    tmp_path, monkeypatch, fault, relative, old, current, revision
):
    import subprocess

    original = subprocess.check_output(
        [
            "git",
            "-C",
            str(Path(C.__file__).resolve().parents[3]),
            "show",
            revision + ":" + relative,
        ]
    )
    assert hashlib.sha256(original).hexdigest() == current
    _historical_code(tmp_path, revision)
    monkeypatch.setattr(C, "ROOT", tmp_path)
    if fault == "source":
        old = "0" * 64
    elif fault == "target":
        current = "0" * 64
    elif fault == "path":
        relative = "src/engine/kiwoom_sniper_v2.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "custody",
        "pid",
        "manifest",
        "authority",
        "date",
        "prepared_metadata",
        "env_change",
    ],
)
@pytest.mark.parametrize("closed", [False, True])
def test_intraday_origin_is_rebound_inside_real_os_isolation(
    request_fixture, fault, closed
):
    f = request_fixture
    request = f["request"]
    proof = request["candidate_code_handoffs"]["pre_submit_delay"]
    origin = proof["origin"]
    data = Path(request["data_root"])
    commit = origin["selected_release_commit"]
    manifest = request["manifest"]
    manifest["selected_release_sha"] = origin["origin_commit"]
    manifest["manifest_sha256"] = C._digest(manifest)
    mp = (
        data
        / "runtime/policy_bootstrap"
        / ("runtime_policy_bootstrap_" + DAY + ".json")
    )
    mp.parent.mkdir(parents=True)
    mp.write_text(json.dumps(manifest))
    folder = data / "runtime/policy_bootstrap/intraday_handoff" / DAY
    folder.mkdir(parents=True)
    hp, cp = folder / (commit + ".json"), folder / (commit + ".consumed.json")
    identity = dict(pid=123, start_ticks="456", cwd=str(f["selected"] / "src"))
    common = dict(
        target_date=DAY,
        selected_release_commit=commit,
        release_root=str(f["selected"]),
        manifest_sha256=manifest["manifest_sha256"],
    )
    handoff = dict(
        **common,
        schema="intraday_policy_preserving_release_handoff_v1",
        authority="APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF",
        status="prepared_verified",
        actual_pid_consumed=False,
        policy_effect="unchanged",
        frozen_files={str(mp): C._sha(mp)},
    )
    if fault == "authority":
        handoff["authority"] = "unapproved"
    hp.write_text(json.dumps(handoff))
    consumed = dict(
        **common,
        schema="intraday_policy_preserving_consumption_v1",
        status="pass",
        actual_pid_consumed=True,
        handoff_sha256=C._sha(hp),
        pid_identity=identity,
    )
    if fault == "custody":
        consumed["handoff_sha256"] = "0" * 64
    if fault == "pid":
        consumed["pid_identity"] = {**identity, "start_ticks": "999"}
    if fault == "date":
        consumed["target_date"] = "2026-10-16"
    cp.write_text(json.dumps(consumed))
    extra = {str(p): C._sha(p) for p in (mp, hp, cp)}
    origin.update(
        basis="verified_selected_intraday_code_handoff",
        pid_identity=identity,
        intraday_handoff_path=str(hp),
        intraday_handoff_sha256=C._sha(hp),
        intraday_consumed_path=str(cp),
        intraday_consumed_sha256=C._sha(cp),
    )
    if closed:
        origin.update(
            basis="verified_closed_intraday_code_handoff",
            closed_observation=dict(
                schema="intraday_closed_consumption_observation_v1",
                target_date=DAY,
                release_commit=commit,
                pid_identity=identity,
                source_hashes=extra,
                runtime_effect=False,
                current_observation_verified=False,
                new_pid_consumption_claimed=False,
            ),
        )
    origin["sources"].update(extra)
    proof["source_hashes"].update(extra)
    request["source_hashes"].update(extra)
    if fault == "manifest":
        request["manifest"] = {**manifest, "manifest_sha256": "0" * 64}
    elif fault in {"prepared_metadata", "env_change"}:
        prepared = json.loads(json.dumps(manifest))
        prepared.update(
            generated_at="2026-10-19T07:39:45+09:00", env_file="prepared/original.env"
        )
        if fault == "env_change":
            prepared["env_overrides"] = {"UNAPPROVED": "true"}
        prepared["manifest_sha256"] = C._digest(
            {k: v for k, v in prepared.items() if k != "manifest_sha256"}
        )
        request["manifest"] = prepared
    _write_request(f, request)
    result = _child(f, "install_validation_code_context(request)\n" + CALL)
    assert (result.returncode == 0) is (
        fault in {None, "prepared_metadata"}
    ), result.stderr


@pytest.mark.parametrize(
    "fault", [None, "missing_bundle", "unknown_scope", "origin", "basis"]
)
def test_intraday_main_closure_requires_fresh_full_native_evidence(
    request_fixture, monkeypatch, fault
):
    f = request_fixture
    main = _main_fixture(f, monkeypatch)
    request = f["request"]
    proof = main["proof"]
    native = proof["native_verification"]
    native.update(
        validation_scope="intraday_preserved_historical_generation",
        preserved_preopen_commit=f["original_commit"],
        handoff_basis="intraday_preserved_preopen_generation_current_postclose_resealed",
    )
    proof["delegation_basis"] = "same_invocation_selected_intraday_native_validation"
    request["manifest"]["selected_release_sha"] = f["original_commit"]
    if fault == "missing_bundle":
        proof["closure"]["bundles"] = {}
    if fault == "unknown_scope":
        native["validation_scope"] = "sealed_generation"
    if fault == "origin":
        native["preserved_preopen_commit"] = "0" * 40
    if fault == "basis":
        proof["delegation_basis"] = "same_invocation_selected_native_full_verification"
    _write_request(f, request)
    result = _child(f, MAIN_CHILD_SETUP + "\nassert_no_forbidden_attempts()\n")
    assert (result.returncode == 0) is (fault is None), result.stderr


def test_reviewed_sor_scope_keeps_original_code_pin_and_rejects_other_bytes():
    name = "src/trading/market/session_contract.py"
    old = "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0"
    current = C._sha(ROOT / name)
    C._pairs({name: old}, {name: current})
    with pytest.raises(ValueError, match="unreviewed"):
        C._pairs({name: old}, {name: "0" * 64})


@pytest.mark.parametrize("fault", [None, "pointer", "parent", "target", "unobserved", "path"])
def test_report_parent_closure_binds_current_pointer_and_observed_child(
    request_fixture, monkeypatch, fault
):
    f = request_fixture
    main = _main_fixture(f, monkeypatch)
    proof = main["proof"]
    data = Path(f["request"]["data_root"])
    pointer = data / "runtime/mechanistic_entry_policy/current.json"
    child = "d" * 64
    pointer.write_text(json.dumps(dict(effective_date=DAY, bundle_sha256=child)))
    proof["closure"]["bundles"][child] = dict(target_date=DAY, family_sha256="e" * 64)
    observed = dict(pointer_path=str(pointer), pointer_sha256=C._sha(pointer),
                    target_date=DAY, bundle_sha256=child,
                    parent_bundle_sha256=proof["policy_sha256"])
    proof["closure"]["report_parent_current"] = observed
    if fault == "pointer":
        pointer.write_text(pointer.read_text() + "\n")
    elif fault == "parent":
        observed["parent_bundle_sha256"] = "f" * 64
    elif fault == "target":
        observed["target_date"] = "2026-10-20"
    elif fault == "unobserved":
        del proof["closure"]["bundles"][child]
    elif fault == "path":
        observed["pointer_path"] = str(data / "alternate.json")
    _write_request(f, f["request"])
    result = _child(f, MAIN_CHILD_SETUP + "\nassert_no_forbidden_attempts()\n")
    assert (result.returncode == 0) is (fault is None), result.stderr
    if fault:
        assert "startup_report_parent_current_unbound" in result.stderr


@pytest.mark.parametrize("fault", [None, "missing", "outside", "signature"])
def test_native_reader_dependencies_bind_selected_code_inside_isolation(
    request_fixture, monkeypatch, fault
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    f = request_fixture
    main = _main_fixture(f, monkeypatch)
    proof = main["proof"]
    request = f["request"]
    relative = "src/engine/scalping/ai_decision_quality.py"
    path = f["selected"] / relative
    digest = C._sha(path)
    observed = next(iter(proof["closure"]["manifests"].values()))
    observed["dependencies"].append(
        [str(path), json.loads(json.dumps(N._signature(path)))]
    )
    proof["native_reader_code_sources"] = {relative: digest}
    proof["source_hashes"][str(path)] = digest
    request["source_hashes"][str(path)] = digest
    if fault == "missing":
        proof["native_reader_code_sources"] = {}
    elif fault == "outside":
        proof["native_reader_code_sources"] = {"../outside.py": digest}
    elif fault == "signature":
        observed["dependencies"][-1][1] = ["changed"]
    _write_request(f, request)
    result = _child(f, MAIN_CHILD_SETUP + "\nassert_no_forbidden_attempts()\n")
    assert (result.returncode == 0) is (fault is None), result.stderr


@pytest.mark.parametrize("fault", [None, "past", "partial", "source_date", "no_policy"])
def test_isolated_stop_future_snapshot_preserves_native_tail_validation(
    request_fixture, monkeypatch, fault
):
    import copy
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.ai.holding_exit_vote import path_vote_store_path

    f = request_fixture
    _main_fixture(f, monkeypatch)
    request = f["request"]
    data = Path(request["data_root"])
    stop = copy.deepcopy(request["candidate_code_handoffs"]["pre_submit_delay"])
    stop["family"] = "main_stop"
    request["candidate_code_handoffs"]["main_stop"] = stop
    request["manifest"]["main_stop_confirmation_receipt"] = dict(
        target_date=DAY, source_date="2026-10-16", policy_sha256=stop["policy_sha256"]
    )
    if fault == "source_date":
        request["manifest"]["main_stop_confirmation_receipt"][
            "source_date"
        ] = "2026-10-15"
    _bind_stop_fixture(f, dict(
        **request["manifest"]["main_stop_confirmation_receipt"],
        research_sha256="d" * 64, vote_source_inventory={}))
    if fault == "no_policy":
        request["candidate_code_handoffs"].pop("main_stop")
    day = "2026-10-16" if fault == "past" else DAY
    row = dict(
        schema="holding_path_vote_v10",
        position_key="record:91",
        session_key=day,
        requested_at=datetime.fromisoformat(day + "T10:00:00")
        .replace(tzinfo=ZoneInfo("Asia/Seoul"))
        .timestamp(),
    )
    path = path_vote_store_path(data, "record:91")
    path.parent.mkdir(parents=True)
    raw = json.dumps(row).encode() + (b"" if fault == "partial" else b"\n")
    path.write_bytes(raw)
    _write_request(f, request)
    result = _child(
        f,
        MAIN_CHILD_SETUP + f"""
from pathlib import Path
from src.engine.automation import main_stop_postclose as post
post._future_unconsumed_vote_tail(Path(request['data_root']), '2026-10-16', Path({str(path)!r}), None)
assert_no_forbidden_attempts()
""",
    )
    assert (result.returncode == 0) is (fault is None), result.stderr
    if fault:
        reason = {
            "past": "stop_vote_future_tail_scope_invalid",
            "partial": "stop_vote_future_tail_invalid",
            "source_date": "startup_stop_snapshot_scope_invalid",
            "no_policy": "startup_stop_snapshot_policy_required",
        }[fault]
        assert reason in result.stderr, result.stderr
    assert path.read_bytes() == raw and not Path(str(path) + ".lock").exists()


def test_auxiliary_inventory_keeps_reviewed_manifest_reader_origin(
    request_fixture, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as P

    f = request_fixture
    main = _main_fixture(f, monkeypatch)
    proof = main["proof"]
    request = f["request"]
    relative = "src/engine/scalping/reversal_auxiliary_next_session.py"
    name = Path(relative).name
    old = "c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1"
    current = C._sha(f["selected"] / relative)
    manifest = P.seal({**main["manifest"], "next_session_code_hashes": {name: old}})
    original = next(iter(proof["closure"]["manifests"]))
    observed = proof["closure"]["manifests"].pop(original)
    Path(observed["path"]).write_text(json.dumps(manifest))
    observed["sha256"] = C._sha(observed["path"])
    ident = manifest["artifact_content_sha256"]
    proof["closure"]["manifests"][ident] = observed
    proof["historical_semantic_code_sources"][ident] = proof[
        "historical_semantic_code_sources"
    ].pop(original)
    proof["original_code_hashes"] = {**proof["original_code_hashes"], relative: current}
    proof["runtime_code_hashes"] = {**proof["runtime_code_hashes"], relative: current}
    for p in (f["selected"] / relative, f["root"] / relative, Path(observed["path"])):
        proof["source_hashes"][str(p)] = C._sha(p)
        request["source_hashes"][str(p)] = C._sha(p)
    _write_request(f, request)
    result = _child(
        f,
        MAIN_CHILD_SETUP + f"""
from pathlib import Path
manifest=json.loads(Path({observed['path']!r}).read_bytes())
bundle=json.loads(Path(request['main_preparation_code_handoff']['policy_path']).read_bytes())
proof=C.validation_auxiliary_preparation(manifest,bundle,Path(request['data_root']))
assert A._validation_code_inventory(manifest['next_session_code_hashes'], {{{name!r}:{current!r}}}, proof)
assert not A._validation_code_inventory({{{name!r}:'0'*64}}, {{{name!r}:{current!r}}}, proof)
assert_no_forbidden_attempts()
""",
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "missing",
        "scope",
        "date",
        "release",
        "consumed",
        "full",
        "source",
        "bootstrap",
        "activation",
        "source_date",
        "native_pid",
        "prepared_manifest",
        "live_as_prepared",
    ],
)
def test_isolated_preserved_native_closure_requires_consumption_full_bootstrap_and_exact_sources(
    request_fixture, monkeypatch, fault
):
    f = request_fixture
    main = _main_fixture(f, monkeypatch)
    proof = main["proof"]
    request = f["request"]
    data = Path(request["data_root"])
    commit = f["original_commit"]
    selected = str(f["selected"])
    native = proof["native_verification"]
    native.update(
        validation_scope="intraday_preserved_historical_generation",
        handoff_basis="intraday_preserved_preopen_generation_current_postclose_resealed",
        preserved_preopen_commit="a" * 40,
    )
    proof["delegation_basis"] = C._native_main_basis(native)
    request["manifest"]["selected_release_sha"] = "a" * 40
    closure = proof["closure"]
    closure["manifests"] = {}
    proof["historical_semantic_code_sources"] = {}
    prepared = (
        data / "runtime/policy_bootstrap/prepared" / DAY / "original" / "receipt.json"
    )
    prepared.parent.mkdir(parents=True)
    prepared.write_text(
        json.dumps(
            dict(
                status="prepared_verified",
                target_date=DAY,
                source_date=native["source_date"],
                manifest_content_sha256="b" * 64,
                activation_candidate={"bundle_sha256": proof["policy_sha256"]},
            )
        )
    )
    bootstrap = prepared.parent / ("runtime_policy_bootstrap_" + DAY + ".json")
    bootstrap.write_text(json.dumps({"manifest_sha256": "b" * 64}))
    path = data / "runtime/policy_bootstrap/intraday_handoff" / DAY / (commit + ".json")
    path.parent.mkdir(parents=True)
    consumed = path.with_name(commit + ".consumed.json")
    handoff = dict(
        schema="intraday_policy_preserving_release_handoff_v1",
        status="prepared_verified",
        target_date=DAY,
        selected_release_commit=commit,
        release_root=selected,
        actual_pid_consumed=False,
        manifest_sha256="d" * 64,
        prepared_receipt_path=str(prepared),
        prepared_receipt_sha256=C._sha(prepared),
        frozen_files={str(prepared): C._sha(prepared)},
    )
    path.write_text(json.dumps(handoff))
    sha = C._sha(path)
    receipt = dict(
        schema="intraday_policy_preserving_consumption_v1",
        status="pass",
        actual_pid_consumed=True,
        handoff_sha256=sha,
        manifest_sha256="d" * 64,
        target_date=DAY,
        selected_release_commit=commit,
        release_root=selected,
        pid_identity={"pid": 123, "start_ticks": "456", "cwd": selected + "/src"},
    )
    consumed.write_text(json.dumps(receipt))
    record = dict(
        schema="startup_native_preserved_preopen_closure_v1",
        target_date=DAY,
        selected_release_commit=commit,
        handoff_path=str(path),
        consumed_path=str(consumed),
        manifest_sha256="d" * 64,
        prepared_manifest_sha256="b" * 64,
        sources={
            **handoff["frozen_files"],
            str(path): sha,
            str(consumed): C._sha(consumed),
        },
        full_bootstrap=dict(
            path=str(bootstrap),
            sha256=C._sha(bootstrap),
            write=False,
            full_native_verification=True,
            result=dict(
                status="pass", findings=[], target_date=DAY, manifest_sha256="b" * 64
            ),
        ),
    )
    closure["preserved_generations"] = {sha: record}
    proof["source_hashes"].update(C._preserved_native_sources(proof))
    request["source_hashes"].update(proof["source_hashes"])
    if fault == "missing":
        closure["preserved_generations"] = {}
    elif fault == "scope":
        native["validation_scope"] = "current_full_contract"
    elif fault == "date":
        record["target_date"] = "2026-10-20"
    elif fault == "release":
        record["selected_release_commit"] = "e" * 40
    elif fault == "consumed":
        record["sources"][str(consumed)] = "e" * 64
    elif fault == "full":
        record["full_bootstrap"] = None
    elif fault == "prepared_manifest":
        record["prepared_manifest_sha256"] = "e" * 64
    elif fault == "live_as_prepared":
        record["full_bootstrap"]["result"]["manifest_sha256"] = record[
            "manifest_sha256"
        ]
    elif fault == "source":
        prepared.write_text("{}")
    elif fault == "bootstrap":
        bootstrap.write_text("{}")
    elif fault == "activation":
        proof["policy_sha256"] = "e" * 64
    elif fault == "source_date":
        native["source_date"] = "2026-10-15"
    elif fault == "native_pid":
        closure["digest_binding"]["pid"] += 1
    _write_request(f, request)
    result = _child(
        f,
        MAIN_CHILD_SETUP + """
proof=request['main_preparation_code_handoff']
assert proof['closure']['manifests']=={}
assert C.preparation_logical_sources()=={}
assert C.validation_raw_vote_sources(request['data_root'],request['main_preparation_code_handoff']['native_verification']['source_date'])
from src.engine.infrastructure.validation_digest_session import ACTIVE
from src.engine.automation.main_trailing_completed_store import admit_window
assert ACTIVE.get().binding['role']=='startup_validation'
assert admit_window(request['data_root'],request['target_date'])==0
assert_no_forbidden_attempts()
""",
    )
    assert (result.returncode == 0) is (fault is None), result.stderr


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "missing",
        "scope",
        "date",
        "release",
        "full",
        "source",
        "bootstrap",
        "activation",
        "source_date",
        "native_pid",
        "prepared_manifest",
        "index",
        "authority",
        "extra_generation",
        "schema",
    ],
)
@pytest.mark.parametrize(
    "consumed_ancestry",
    [False, True, "native", "native_closed", "prepared_intraday", "prepared_stopped", "unprepared_stopped"],
)
def test_isolated_prepared_native_closure_keeps_full_bootstrap_and_exact_sources(
    current_request_fixture, monkeypatch, fault, consumed_ancestry
):
    f = current_request_fixture
    main = _main_fixture(f, monkeypatch)
    proof = main["proof"]
    request = f["request"]
    data = Path(request["data_root"])
    commit = f["original_commit"]
    native = proof["native_verification"]
    prepared_commit = (
        "a" * 40
        if consumed_ancestry is True
        or consumed_ancestry in {"prepared_intraday", "prepared_stopped", "unprepared_stopped"}
        else commit
    )
    closure = proof["closure"]
    closure["manifests"] = {}
    proof["historical_semantic_code_sources"] = {}
    directory = data / "runtime/policy_bootstrap/prepared" / DAY / "original"
    directory.mkdir(parents=True)
    prepared = directory / "readiness.json"
    receipt = dict(
        schema="next_preopen_readiness_v1",
        status="prepared_verified",
        target_date=DAY,
        source_date=native["source_date"],
        selected_release_commit=prepared_commit,
        runtime_effect=False,
        actual_pid_consumed=False,
        manifest_content_sha256="b" * 64,
        activation_candidate=dict(bundle_sha256=proof["policy_sha256"]),
        policy_receipts=[],
    )
    refs = {}
    for name, digest in (
        ("manifest_path", "manifest_file_sha256"),
        ("env_path", "env_sha256"),
        ("verification_path", "verification_sha256"),
        ("controller_path", "controller_sha256"),
        ("summary_path", "summary_sha256"),
    ):
        source = directory / (
            ("runtime_policy_bootstrap_" + DAY) if name == "manifest_path" else name
        )
        source = source.with_suffix(".json")
        source.write_text(
            json.dumps(
                dict(
                    manifest_sha256="b" * 64,
                    target_date=DAY,
                    selected_release_sha=prepared_commit,
                )
            )
        )
        receipt[name] = str(source)
        receipt[digest] = C._sha(source)
        refs[str(source)] = C._sha(source)
    prepared.write_text(json.dumps(receipt))
    sha = C._sha(prepared)
    refs[str(prepared)] = sha
    index = directory.parent / "latest.json"
    index.write_text(
        json.dumps(
            dict(
                schema="next_preopen_readiness_index_v1",
                target_date=DAY,
                receipt_path=str(prepared),
                receipt_sha256=sha,
            )
        )
    )
    record = dict(
        schema="startup_native_prepared_preopen_closure_v1",
        target_date=DAY,
        selected_release_commit=prepared_commit,
        prepared_receipt_path=str(prepared),
        sources=refs,
        prepared_manifest_sha256="b" * 64,
        full_bootstrap=dict(
            path=receipt["manifest_path"],
            sha256=receipt["manifest_file_sha256"],
            write=False,
            full_native_verification=True,
            result=dict(
                status="pass", findings=[], target_date=DAY, manifest_sha256="b" * 64
            ),
        ),
    )
    closure["preserved_generations"] = {sha: record}
    if consumed_ancestry is True:
        native.update(
            validation_scope="intraday_preserved_historical_generation",
            handoff_basis="intraday_preserved_preopen_generation_current_postclose_resealed",
            preserved_preopen_commit=prepared_commit,
        )
        proof["delegation_basis"] = C._native_main_basis(native)
        request["manifest"]["selected_release_sha"] = prepared_commit
        path = (
            data
            / "runtime/policy_bootstrap/intraday_handoff"
            / DAY
            / (commit + ".json")
        )
        path.parent.mkdir(parents=True)
        handoff = dict(
            schema="intraday_policy_preserving_release_handoff_v1",
            status="prepared_verified",
            target_date=DAY,
            selected_release_commit=commit,
            release_root=str(f["selected"]),
            actual_pid_consumed=False,
            manifest_sha256="d" * 64,
            prepared_receipt_path=str(prepared),
            prepared_receipt_sha256=sha,
            frozen_files={**refs, str(index): C._sha(index)},
        )
        path.write_text(json.dumps(handoff))
        live_sha = C._sha(path)
        consumed = path.with_name(commit + ".consumed.json")
        consumed.write_text(
            json.dumps(
                dict(
                    schema="intraday_policy_preserving_consumption_v1",
                    status="pass",
                    actual_pid_consumed=True,
                    handoff_sha256=live_sha,
                    manifest_sha256="d" * 64,
                    target_date=DAY,
                    selected_release_commit=commit,
                    release_root=str(f["selected"]),
                    pid_identity={"pid": 123, "start_ticks": "456"},
                )
            )
        )
        closure["preserved_generations"][live_sha] = dict(
            schema="startup_native_preserved_preopen_closure_v1",
            target_date=DAY,
            selected_release_commit=commit,
            handoff_path=str(path),
            consumed_path=str(consumed),
            manifest_sha256="d" * 64,
            prepared_manifest_sha256="b" * 64,
            full_bootstrap=record["full_bootstrap"],
            sources={
                **handoff["frozen_files"],
                str(path): live_sha,
                str(consumed): C._sha(consumed),
            },
        )
    if consumed_ancestry in {"prepared_intraday", "prepared_stopped", "unprepared_stopped"}:
        native.update(
            validation_scope="intraday_preserved_historical_generation",
            actual_pid_consumed=False,
            handoff_basis="intraday_preserved_preopen_generation_current_postclose_resealed",
            preserved_preopen_commit=prepared_commit,
        )
        request["manifest"]["selected_release_sha"] = prepared_commit
        path = (
            data
            / "runtime/policy_bootstrap/intraday_handoff"
            / DAY
            / (commit + ".json")
        )
        path.parent.mkdir(parents=True)
        handoff = dict(
            schema="intraday_policy_preserving_release_handoff_v1",
            status="prepared_verified",
            authority="APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF",
            policy_effect="unchanged",
            target_date=DAY,
            selected_release_commit=commit,
            release_root=str(f["selected"]),
            actual_pid_consumed=False,
            manifest_sha256="d" * 64,
            prepared_receipt_path=str(prepared),
            prepared_receipt_sha256=sha,
            frozen_files={**refs, str(index): C._sha(index)},
        )
        active = (
            data
            / "runtime/policy_bootstrap"
            / ("runtime_policy_bootstrap_" + DAY + ".json")
        )
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text(json.dumps(dict(manifest_sha256="d" * 64, target_date=DAY)))
        handoff["frozen_files"][str(active)] = C._sha(active)
        path.write_text(json.dumps(handoff))
        native["prepared_intraday_handoff"] = dict(
            path=str(path),
            sha256=C._sha(path),
            sources={**handoff["frozen_files"], str(path): C._sha(path)},
            full_native_validation=True,
        )
        proof["delegation_basis"] = C._native_main_basis(native)
        (data / "runtime/runtime_release_selection.json").write_text(
            json.dumps(
                dict(
                    schema="runtime_release_selection_v1",
                    release_root=str(f["selected"]),
                    git_commit=commit,
                    actual_pid_consumed=False,
                )
            )
        )
        selection = data / "runtime/runtime_release_selection.json"
        for consumer in request["candidate_code_handoffs"].values():
            consumer["source_hashes"][str(selection)] = C._sha(selection)
            if str(selection) in consumer["origin"]["sources"]:
                consumer["origin"]["sources"][str(selection)] = C._sha(selection)
    if consumed_ancestry == "prepared_stopped":
        handoff["first_launch_before"] = "2026-10-19T10:15:00+09:00"
        path.write_text(json.dumps(handoff))
        binding = native["prepared_intraday_handoff"]
        binding["sha256"] = C._sha(path)
        binding["sources"][str(path)] = C._sha(path)
        failed = data / "original-failed-transition.json"
        failed.write_text("immutable native failure")
        observation = dict(
            target_date=DAY,
            release_commit=commit,
            runtime_effect=False,
            actual_pid_consumed=False,
            allowed_runtime_apply=False,
            original_first_launch_before=handoff["first_launch_before"],
            source_hashes={str(failed): C._sha(failed)},
        )
        native["stopped_preparation_observation"] = observation
        binding["sources"].update(observation["source_hashes"])
    if consumed_ancestry == "unprepared_stopped":
        previous = "d" * 40
        original_path = path.with_name(previous + ".json")
        handoff.update(selected_release_commit=previous, release_root=str(f["selected"].parent / "previous"))
        original_path.write_text(json.dumps(handoff))
        path.unlink()
        consumed = original_path.with_name(previous + ".consumed.json")
        identity = dict(pid=123, start_ticks="456", cwd=handoff["release_root"] + "/src")
        consumed.write_text(json.dumps(dict(schema="intraday_policy_preserving_consumption_v1",status="pass",
            target_date=DAY,selected_release_commit=previous,release_root=handoff["release_root"],
            actual_pid_consumed=True,pid_identity=identity,handoff_sha256=C._sha(original_path))))
        failed = data / "original-failed-transition.json"
        failed.write_text(json.dumps(dict(schema="ordered_intraday_deployment_v1",authority="APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART",
            error="deployment_validation_failed:src.engine.automation.intraday_release_handoff",target_date=DAY,
            phase="failed",failed_phase="selected",candidate_commit=commit,
            previous_commit=previous,predecessor_identity=identity)))
        selection=data / "runtime/runtime_release_selection.json"
        selected=json.loads(selection.read_text())
        selected.update(previous_git_commit=previous,previous_release_root=handoff["release_root"],deployment_transition=str(failed))
        selection.write_text(json.dumps(selected))
        observation=dict(target_date=DAY,release_commit=commit,runtime_effect=False,actual_pid_consumed=False,
            allowed_runtime_apply=False,original_first_launch_before=None,
            unprepared_selected_handoff=dict(path=str(path),predecessor_path=str(original_path),predecessor_sha256=C._sha(original_path)),
            source_hashes={str(p):C._sha(p) for p in (original_path,consumed,failed,selection)})
        native["stopped_preparation_observation"]=observation
        native.pop("prepared_intraday_handoff")
        native["unprepared_stopped_handoff"]=dict(path=str(original_path),sha256=C._sha(original_path),
            role="native_consumed_predecessor_for_unprepared_selection",full_native_validation=True,
            sources={**handoff["frozen_files"],**observation["source_hashes"]})
        proof["delegation_basis"]=C._native_main_basis(native)
        for consumer in request["candidate_code_handoffs"].values():
            consumer["source_hashes"][str(selection)]=C._sha(selection)
            if str(selection) in consumer["origin"]["sources"]:consumer["origin"]["sources"][str(selection)]=C._sha(selection)
        consumer=request["candidate_code_handoffs"]["pre_submit_delay"]
        policy_path=data / "threshold_cycle/pre_submit_delay_policy/generations/fixture/policy.json"
        policy_path.parent.mkdir(parents=True)
        policy=dict(code_contract_sha256=consumer["original_code_sha256"])
        policy["policy_sha256"]=C._digest(policy)
        policy_path.write_text(json.dumps(policy))
        field=dict(target_date=DAY,policy_sha256=policy["policy_sha256"],policy_path=str(policy_path))
        request["manifest"]["pre_submit_delay_handoff"]=field
        live=C._json(active);live.update(selected_release_sha=prepared_commit,pre_submit_delay_handoff=field)
        active.write_text(json.dumps(live))
        handoff["frozen_files"][str(active)]=C._sha(active)
        original_path.write_text(json.dumps(handoff))
        value=C._json(consumed);value["handoff_sha256"]=C._sha(original_path);consumed.write_text(json.dumps(value))
        observation["unprepared_selected_handoff"]["predecessor_sha256"]=C._sha(original_path)
        observation["source_hashes"].update({str(p):C._sha(p) for p in (original_path,consumed)})
        native["unprepared_stopped_handoff"].update(sha256=C._sha(original_path),sources={**handoff["frozen_files"],**observation["source_hashes"]})
        consumer["policy_sha256"]=policy["policy_sha256"]
        consumer["origin"].update(basis="verified_unprepared_stopped_original_contract",origin_commit=prepared_commit)
        family_sources={**observation["source_hashes"],str(active):C._sha(active),str(policy_path):C._sha(policy_path)}
        consumer["origin"]["sources"].update(family_sources)
        consumer["source_hashes"].update(family_sources)
        request["source_hashes"].update(family_sources)
    if consumed_ancestry in {"native", "native_closed"}:
        request["manifest"]["selected_release_sha"] = commit
        identity = dict(pid=123, start_ticks="456", cwd=str(f["selected"] / "src"))
        native.update(
            validation_scope="intraday_preserved_historical_generation",
            handoff_basis="native_consumed_preopen_preserved_generation",
            preserved_preopen_commit=commit,
            native_predecessor_consumption=dict(
                schema="intraday_pid_consumption_verification_v1",
                status="pass",
                findings=[],
                basis="native_preopen",
                actual_pid_consumed=True,
                target_date=DAY,
                selected_release_commit=commit,
                release_root=str(f["selected"]),
                pid_identity=identity,
                manifest_sha256="d" * 64,
            ),
        )
        proof["delegation_basis"] = C._native_main_basis(native)
        selection = data / "runtime/runtime_release_selection.json"
        selection.parent.mkdir(parents=True, exist_ok=True)
        original_selection = json.loads(selection.read_text())
        selection.write_text(
            json.dumps(
                dict(
                    original_selection,
                    actual_pid_consumed=True,
                    release_root=str(f["selected"]),
                    git_commit=commit,
                    actual_pid_receipt=dict(
                        pid=123, start_ticks="456", process_cwd=identity["cwd"]
                    ),
                )
            )
        )
        for consumer in request["candidate_code_handoffs"].values():
            consumer["source_hashes"][str(selection)] = C._sha(selection)
            if str(selection) in consumer["origin"]["sources"]:
                consumer["origin"]["sources"][str(selection)] = C._sha(selection)
        active = (
            data
            / "runtime/policy_bootstrap"
            / ("runtime_policy_bootstrap_" + DAY + ".json")
        )
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text(json.dumps(dict(manifest_sha256="d" * 64)))
        active.with_suffix(".env").write_text("native environment fixture")
        if consumed_ancestry == "native_closed":
            terminal = data / "closed-collector.json"
            terminal.write_text("native shutdown evidence")
            closed = dict(schema="intraday_closed_consumption_observation_v1",
                          basis="native_preopen_closed", target_date=DAY, release_commit=commit,
                          pid_identity=identity, manifest_sha256="d"*64,
                          historical_consumption_verified=True, current_observation_verified=False,
                          new_pid_consumption_claimed=False, runtime_effect=False,
                          collector_shutdown=dict(status="verified"),
                          source_hashes={str(p):C._sha(p) for p in (selection, active, active.with_suffix(".env"), terminal)})
            native["handoff_basis"] = "native_closed_preopen_preserved_generation"
            native["native_predecessor_consumption"].update(actual_pid_consumed=False,
                historical_consumption_verified=True, runtime_effect=False, closed_observation=closed)
            proof["delegation_basis"] = C._native_main_basis(native)
    proof["source_hashes"].update(C._preserved_native_sources(proof))
    request["source_hashes"].update(proof["source_hashes"])
    if consumed_ancestry == "native" and fault is None:
        from src.engine.automation import intraday_release_handoff as H

        monkeypatch.setattr(
            H,
            "_verify_handoff",
            lambda *a, **kw: (_ for _ in ()).throw(
                AssertionError("native_preopen_has_no_intraday_handoff")
            ),
        )
        monkeypatch.setattr(C, "REVIEWED_PREPARATION_SOURCES", {})
        monkeypatch.setattr(C, "ROOT", f["root"])
        intake = dict(
            selected_root=f["selected"],
            selected_commit=commit,
            manifest=request["manifest"],
            receipt=dict(
                activation_candidate=dict(bundle_sha256=proof["policy_sha256"])
            ),
            native_verification=dict(native, native_machine_closure=closure),
        )
        bound = C.bind_main_preparation(f["root"], f["commit"], data, intake)
        assert (
            bound["delegation_basis"]
            == "same_invocation_selected_consumed_preopen_native_validation"
        )
    if fault == "missing":
        closure["preserved_generations"] = {}
    elif fault == "scope":
        native["validation_scope"] = (
            "current_full_contract"
            if consumed_ancestry
            else "intraday_preserved_historical_generation"
        )
    elif fault == "date":
        record["target_date"] = "2026-10-20"
    elif fault == "release":
        record["selected_release_commit"] = "e" * 40
    elif fault == "full":
        record["full_bootstrap"] = None
    elif fault == "source":
        prepared.write_text("{}")
    elif fault == "bootstrap":
        record["full_bootstrap"]["result"]["manifest_sha256"] = "e" * 64
    elif fault == "activation":
        proof["policy_sha256"] = "e" * 64
    elif fault == "source_date":
        native["source_date"] = "2026-10-15"
    elif fault == "native_pid":
        closure["digest_binding"]["pid"] += 1
    elif fault == "prepared_manifest":
        record["prepared_manifest_sha256"] = "e" * 64
    elif fault == "index":
        index.write_text("{}")
    elif fault == "authority":
        record["full_bootstrap"]["write"] = True
    elif fault == "extra_generation":
        closure["preserved_generations"]["e" * 64] = dict(record)
    elif fault == "schema":
        record["schema"] = "startup_native_preserved_preopen_closure_v1"
    if consumed_ancestry == "unprepared_stopped" and fault is None:
        # Exercise the new phase's semantic negatives with freshly rebound
        # byte hashes; unchanged hash rejection alone would not cover them.
        import copy
        original_request=copy.deepcopy(request)
        original_failed=failed.read_bytes()
        original_consumed=consumed.read_bytes()
        for damage in ("appeared", "consumed", "failed_phase", "role"):
            damaged=copy.deepcopy(original_request)
            damaged_proof=damaged["main_preparation_code_handoff"]
            n=damaged_proof["native_verification"]
            if damage=="appeared":path.write_text("{}")
            elif damage=="consumed":
                value=C._json(consumed);value["actual_pid_consumed"]=False;consumed.write_text(json.dumps(value))
            elif damage=="failed_phase":
                value=C._json(failed);value["failed_phase"]="starting";failed.write_text(json.dumps(value))
            else:n["unprepared_stopped_handoff"]["role"]="unknown"
            if damage in {"consumed","failed_phase"}:
                changed=consumed if damage=="consumed" else failed
                def rebind(value):
                    if isinstance(value,dict):
                        for key,item in value.items():
                            if key==str(changed):value[key]=C._sha(changed)
                            else:rebind(item)
                    elif isinstance(value,list):
                        for item in value:rebind(item)
                rebind(damaged)
            _write_request(f,damaged)
            (f["run"] / "audit.jsonl").unlink(missing_ok=True)
            negative=_child(f,MAIN_CHILD_SETUP)
            assert negative.returncode!=0 and "startup_unprepared_original_consumption_unbound" in negative.stderr, negative.stderr
            if path.exists():path.unlink()
            consumed.write_bytes(original_consumed)
            failed.write_bytes(original_failed)
        (f["run"] / "audit.jsonl").unlink(missing_ok=True)
    _write_request(f, request)
    result = _child(
        f,
        MAIN_CHILD_SETUP + """
proof=request['main_preparation_code_handoff']
assert proof['closure']['manifests']=={}
assert C.preparation_logical_sources()=={}
assert C.validation_raw_vote_sources(request['data_root'],proof['native_verification']['source_date'])
assert_no_forbidden_attempts()
""",
    )
    assert (result.returncode == 0) is (fault is None), result.stderr


@pytest.mark.parametrize("consumed", [False, True])
def test_isolated_policy_reader_never_runs_operational_main_probe(
    request_fixture, monkeypatch, consumed
):
    f = request_fixture
    _main_fixture(f, monkeypatch)
    result = _child(
        f,
        MAIN_CHILD_SETUP + f"""
import types,subprocess
from pathlib import Path
from src.engine.automation import intraday_release_handoff as H
probe=types.ModuleType('src.engine.error_detectors.artifact_freshness')
probe._postclose_main_absent=lambda:subprocess.run(['/bin/false'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1
sys.modules['src.engine.error_detectors']=types.ModuleType('src.engine.error_detectors')
sys.modules['src.engine.error_detectors.artifact_freshness']=probe
H.DATA_DIR=Path(request['data_root'])
original=H._read
H._read=lambda p:dict(actual_pid_consumed={consumed!r}) if Path(p)==H.DATA_DIR/'runtime/runtime_release_selection.json' else original(p)
with H.consumed_observation_scope(data_root=H.DATA_DIR):
    assert C.validation_raw_vote_sources(H.DATA_DIR,request['main_preparation_code_handoff']['native_verification']['source_date'])
assert_no_forbidden_attempts()
""",
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "name",
    [
        "src/engine/scalping/reversal_code_handoff.py",
        "src/engine/ai_engine_openai.py",
        "src/engine/scalping/ai_decision_trace.py",
        "src/engine/scalping/continuous_reversal_policy_v6.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/scalping/reversal_evaluation_context.py",
        "src/engine/monitoring/runtime_performance.py",
        "src/trading/entry/physical_send_guard.py",
        "src/engine/monitoring/policy_generation_code_handoff.py",
        "src/engine/monitoring/policy_generation_validation.py",
        "src/engine/automation/runtime_policy_bootstrap.py",
        "src/engine/monitoring/policy_generation_contract.py",
        "src/engine/scalping/reversal_auxiliary_compatibility.py",
        "src/engine/scalping/reversal_auxiliary_production_input.py",
        "src/engine/scalping/reversal_auxiliary_registry.py",
        "src/engine/scalping/reversal_auxiliary_wire.py",
        "src/engine/scalping/continuous_reversal_policy.py",
        "src/engine/automation/main_startup_validation.py",
        "src/engine/automation/next_preopen_readiness.py",
    ],
)
def test_main_preparation_uses_reviewed_stopped_origin_code(name):
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    pairs = set(C.REVIEWED_PREPARATION_HISTORY.get(name, ()))
    if name in C.REVIEWED_PREPARATION_SOURCES:
        pairs.add(C.REVIEWED_PREPARATION_SOURCES[name])
    for old, new in pairs:
        if new == current:
            C._pairs({name: old}, {name: new})
    review = json.loads((ROOT / H._FORMATTING_REVIEW_PATH).read_text())
    predecessor = review["sources"][name]["before_sha256"]
    if review["sources"][name]["after_sha256"] != current:
        _assert_current_code_profile(name, current)
        C._pairs({name: review["sources"][name]["after_sha256"]}, {name: current})
    origins = {old for old, new in pairs if new in {predecessor, current}}
    origins.add(predecessor)
    assert origins
    for old in origins:
        C._pairs({name: old}, {name: current})
        with pytest.raises(ValueError, match="unreviewed"):
            C._pairs({name: old}, {name: "0" * 64})
    with pytest.raises(ValueError, match="unreviewed"):
        C._pairs({name: "0" * 64}, {name: current})


@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_independently_binds_postclose_workflow_revision(damage):
    import hashlib, subprocess

    relative = "deploy/run_threshold_cycle_postclose.sh"
    old = hashlib.sha256(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "d346aa3af:" + relative]
        )
    ).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    if damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "relative",
    [
        "src/engine/kiwoom_sniper_v2.py",
        "src/engine/kiwoom_websocket.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/scalping/pre_submit_delay_observation.py",
        "src/engine/monitoring/submission_bottleneck_monitor.py",
        "src/engine/automation/main_trailing_source_reuse.py",
        "src/engine/automation/main_trailing_source_assembler.py",
        "src/engine/automation/main_market_weakness_research.py",
        "src/engine/scalping/market_weakness_research.py",
        "src/engine/automation/ordered_intraday_deploy.py",
    ],
)
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_independently_reviews_sentinel_route_sources(
    relative, damage
):
    import subprocess

    old = hashlib.sha256(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "9a8e59bfc:" + relative]
        )
    ).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    if damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "relative",
    [
        "src/engine/lifecycle/research_storage.py",
        "src/engine/error_detectors/artifact_freshness.py",
        "src/engine/monitoring/submission_bottleneck_monitor.py",
        "src/engine/automation/ordered_intraday_deploy.py",
        "src/engine/automation/entry_cancel_wait_tuning.py",
        "src/engine/monitoring/policy_generation_code_handoff.py",
        "src/engine/scalping/mechanistic_entry_runtime_policy.py",
    ],
)
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_independently_reviews_observer_p5_b67_sources(
    relative, damage
):
    original = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "926ebca82:" + relative]
    )
    old = hashlib.sha256(original).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
@pytest.mark.parametrize(
    "relative",
    [
        "src/engine/lifecycle/broker_cost_allocation.py",
        "src/engine/scalping/initial_quantity_monitor_projection.py",
        "src/engine/scalping/holding_path_vote_policy.py",
        "src/engine/runtime_approval_summary.py",
        "src/engine/infrastructure/startup_validation_isolation.py",
        "src/engine/automation/policy_generation_fixture_validation.py",
        "src/engine/automation/tuning_performance_control_tower.py",
        "src/engine/automation/main_startup_validation.py",
    ],
)
def test_main_preparation_independently_reviews_native_buy_cost(damage, relative):
    old = hashlib.sha256(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "a2ca8e7d8:" + relative]
        )
    ).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "relative",
    [
        "src/engine/automation/main_trailing_source_assembler.py",
        "src/engine/automation/pre_submit_delay_research_review.py",
        "src/engine/kiwoom_sniper_v2.py",
        "src/engine/lifecycle/research_json_stream.py",
        "src/engine/scalping/holding_decision_context.py",
        "src/engine/scalping/trailing_threshold_policy.py",
        "src/engine/scalping/universal_trailing_replay.py",
        "src/engine/sniper_execution_receipts.py",
        "src/engine/sniper_state_handlers.py",
        "src/utils/pipeline_event_logger.py",
        "src/engine/monitoring/policy_generation_code_handoff.py",
    ],
)
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_reviews_continuous_holding_stream(relative, damage):
    old = hashlib.sha256(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "9e820cbf8:" + relative]
        )
    ).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "relative",
    sorted(
        n
        for n in H.REVIEWED_MACHINE_REST_HISTORY_HASHES
        if n != "src/engine/infrastructure/startup_validation_code_context.py"
    ),
)
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_reviews_rest_history_sources(relative, damage):
    old = H.REVIEWED_MACHINE_REST_HISTORY_PREVIOUS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_reviews_auxiliary_capability_successor(damage):
    relative = "src/engine/monitoring/policy_generation_code_handoff.py"
    old = H.REVIEWED_AUXILIARY_CAPABILITY_PREVIOUS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "relative",
    [
        "src/engine/kiwoom_sniper_v2.py",
        "src/engine/sniper_state_handlers.py",
        "src/engine/sniper_scale_in.py",
        "src/engine/lifecycle/avg_down_policy_replay.py",
        "src/engine/log_archive_service.py",
    ],
)
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_independently_reviews_numeric_replay(relative, damage):
    old = hashlib.sha256(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "6d8891ac3:" + relative]
        )
    ).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "relative",
    sorted(
        n
        for n in H.REVIEWED_AFTERMARKET_LISTING_HASHES
        if n != "src/engine/infrastructure/startup_validation_code_context.py"
    ),
)
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_reviews_aftermarket_listing_sources(relative, damage):
    old = H.REVIEWED_AFTERMARKET_LISTING_PREVIOUS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_reviews_scanner_preflight_reader(damage):
    relative = "src/engine/monitoring/submission_bottleneck_monitor.py"
    old = H.REVIEWED_SCANNER_PREFLIGHT_PREVIOUS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize("origin", ["926ebca82", "6e970e41f"])
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_main_preparation_independently_reviews_closed_scanner(origin, damage):
    relative = "src/engine/error_detectors/artifact_freshness.py"
    old = hashlib.sha256(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", origin + ":" + relative]
        )
    ).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        new = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize(
    "name",
    [
        "src/utils/constants.py",
        "src/engine/error_detectors/artifact_freshness.py",
        "src/engine/infrastructure/runtime_release_router.py",
    ],
)
def test_migration_configuration_has_independent_exact_source_pairs(tmp_path, name):
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    _historical_code(tmp_path, "cb4f0ab58")
    for old in H.REVIEWED_MIGRATION_ORIGINS[name]:
        assert C.reviewed_preparation_pair(
            name, old, H.REVIEWED_CLOSED_LOADER_PROFILE[name], root=tmp_path
        )
        C._pairs({name: old}, {name: current})
        with pytest.raises(ValueError, match="unreviewed"):
            C._pairs({name: old}, {name: "0" * 64})
    with pytest.raises(ValueError, match="unreviewed"):
        C._pairs({name: "0" * 64}, {name: current})


@pytest.mark.parametrize("name", ["src/engine/scalping/reversal_code_handoff.py",
    "src/engine/monitoring/submission_bottleneck_monitor.py"])
@pytest.mark.parametrize("fault", [None, "source", "target", "path"])
def test_activation_and_native_receipt_repairs_bind_exact_independent_sources(name, fault):
    old = hashlib.sha256(subprocess.check_output([
        "git", "-C", str(ROOT), "show", "ef9927b7c:" + name])).hexdigest()
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if fault == "source":old = "0" * 64
    elif fault == "target":current = "0" * 64
    elif fault == "path":name = "src/engine/kiwoom_sniper_v2.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)


@pytest.mark.parametrize("name", [
    "src/engine/scalping/initial_quantity_policy.py",
    "src/engine/scalping/initial_quantity_refresh_evaluation.py",
    "src/engine/automation/postclose_summary_handoff.py",
    "src/engine/automation/ordered_intraday_deploy.py",
])
@pytest.mark.parametrize("fault", [None, "source", "target", "path"])
def test_registry_replay_repair_binds_exact_independent_predecessor(name, fault):
    old = hashlib.sha256(subprocess.check_output([
        "git", "-C", str(ROOT), "show", "1081d2f8e:" + name])).hexdigest()
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if fault == "source": old = "0" * 64
    elif fault == "target": current = "0" * 64
    elif fault == "path": name = "src/engine/kiwoom_sniper_v2.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_SUBMIT_PROBE_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_submit_probe_independent_preparation_exact_pairs(relative, fault):
    import subprocess
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "c260d6b07:" + relative]
    )).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_HEALTH_SNAPSHOT_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_health_snapshot_independent_preparation_exact_pairs(relative, fault):
    import subprocess
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "b6611ce26:" + relative])).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    elif fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_cumulative_hold_independent_preparation_exact_pair(fault):
    relative = "src/engine/monitoring/runtime_performance.py"
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "7b98fa4bc:" + relative])).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    elif fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_closed_loader_independent_preparation_exact_pair(fault):
    relative = "src/engine/error_detectors/artifact_freshness.py"
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "89a0a5fa2:" + relative])).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    elif fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


def test_indexed_reader_stays_native_outside_isolated_context():
    from src.engine.automation import main_trailing_source_store as S

    assert S.generation is not C.validation_indexed_source_generation
    assert S.generation.__module__ == S.__name__


def test_non_main_isolated_context_does_not_replace_indexed_reader(request_fixture):
    result = _child(request_fixture, '''
from src.engine.infrastructure import startup_validation_code_context as C
from src.engine.automation import main_trailing_source_store as S
native = S.generation
install_validation_code_context(request)
assert S.generation is native
assert S.generation is not C.validation_indexed_source_generation
assert_no_forbidden_attempts()
''')
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('damage', [None, 'origin', 'successor'])
def test_report_absence_recovery_keeps_independent_source_pair(damage):
    import subprocess

    relative = 'src/engine/automation/postclose_finalization_generation.py'
    old = hashlib.sha256(subprocess.check_output(
        ['git', '-C', str(ROOT), 'show', '59a922b19:' + relative]
    )).hexdigest()
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == 'origin':
        old = '0' * 64
    elif damage == 'successor':
        new = '0' * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (damage is None)


@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_quantity_history_preparation_requires_exact_reviewed_pair(damage):
    relative = "src/engine/scalping/initial_quantity_monitor_projection.py"
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "ab663e13b:" + relative]
    )).hexdigest()
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed":
        current = "0" * 64
    elif damage == "wrong_origin":
        old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, current) is (damage is None)


@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_drain_closure_preparation_requires_exact_reviewed_pair(damage):
    relative = "src/engine/automation/ordered_intraday_deploy.py"
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "198286cf2:" + relative])).hexdigest()
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed": current = "0" * 64
    elif damage == "wrong_origin": old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, current) is (damage is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_HOLDING_QUOTE_SOURCES))
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_holding_quote_preparation_requires_exact_pair(relative, damage):
    old = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "97bc1f62e:" + relative])).hexdigest()
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed": current = "0" * 64
    elif damage == "wrong_origin": old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, current) is (damage is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_FINALIZATION_ADMISSION_SOURCES))
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_finalization_admission_preparation_requires_exact_pair(relative, damage):
    old = C.REVIEWED_FINALIZATION_ADMISSION_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed": current = "0" * 64
    elif damage == "wrong_origin": old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, current) is (damage is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_HOLDING_CAPABILITY_SOURCES))
@pytest.mark.parametrize("damage", [None, "unreviewed", "wrong_origin"])
def test_holding_capability_preparation_requires_exact_pair(relative, damage):
    old = C.REVIEWED_HOLDING_CAPABILITY_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if damage == "unreviewed": current = "0" * 64
    elif damage == "wrong_origin": old = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, current) is (damage is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_ENTRY_LATENCY_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_entry_latency_independent_preparation_exact_pairs(relative, fault):
    old = C.REVIEWED_ENTRY_LATENCY_ORIGINS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_ENTRY_CAPABILITY_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_entry_capability_independent_preparation_exact_pairs(relative, fault):
    old = C.REVIEWED_ENTRY_CAPABILITY_ORIGINS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    if fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize('name',sorted(C.REVIEWED_NONFIXED_IDENTITY_SOURCES))
@pytest.mark.parametrize('fault',[None,'source','target','path'])
def test_nonfixed_identifier_preparation_uses_independent_exact_sources(name,fault):
    old=H.REVIEWED_NONFIXED_IDENTITY_ORIGINS[name]
    current=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    if fault=='source':old='0'*64
    if fault=='target':current='0'*64
    if fault=='path':name='src/engine/unknown_identifier_owner.py'
    assert C.reviewed_preparation_pair(name,old,current) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_PRECLAIM_DIAGNOSTIC_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_preclaim_diagnostics_independent_preparation_pairs(relative, fault):
    old = C.REVIEWED_PRECLAIM_DIAGNOSTIC_ORIGINS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    if fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_PRECLAIM_CADENCE_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_preclaim_cadence_independent_preparation_pairs(relative, fault):
    old = C.REVIEWED_PRECLAIM_CADENCE_ORIGINS[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    if fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_INVALIDATION_CADENCE_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
@pytest.mark.parametrize("projected", [False, True])
def test_invalidation_cadence_independent_preparation_exact_pairs(relative, fault, projected):
    origins = (
        C.REVIEWED_INVALIDATION_CADENCE_PROJECTED_ORIGINS
        if projected else C.REVIEWED_INVALIDATION_CADENCE_ORIGINS
    )
    old = origins[relative]
    new = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if fault == "origin": old = "0" * 64
    if fault == "successor": new = "0" * 64
    assert C.reviewed_preparation_pair(relative, old, new) is (fault is None)


@pytest.mark.parametrize("relative", list(C.REVIEWED_DELAY_COLLECTION_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_delay_collection_independent_preparation_exact_pairs(relative, fault):
    old = C.REVIEWED_DELAY_COLLECTION_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unknown_collection_owner.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_SUBMIT_FRESH_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
@pytest.mark.parametrize("projected", [False, True])
def test_submit_fresh_independent_preparation_exact_pairs(relative, fault, projected):
    old = (
        C.REVIEWED_SUBMIT_FRESH_PROJECTED_ORIGINS[relative]
        if projected else C.REVIEWED_SUBMIT_FRESH_ORIGINS[relative]
    )
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unknown_submit_owner.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_SCOPED_SCORING_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_scoped_scoring_independent_preparation_binds_exact_generation(tmp_path, name, fault):
    _historical_code(tmp_path, "10f03701c")
    import subprocess
    old = C.REVIEWED_SCOPED_SCORING_ORIGINS[name]
    # This consumed profile keeps its original bytes after later repairs.
    original = subprocess.check_output(["git", "-C", str(ROOT), "show", "10f03701c:" + name])
    current = hashlib.sha256(original).hexdigest()
    assert current == C.REVIEWED_SCOPED_SCORING_SOURCES[name]
    assert current == H.REVIEWED_SCOPED_SCORING_HASHES[name]
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_REPORT_CENSUS_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_report_census_preparation_keeps_exact_reviewed_sources(tmp_path, name, fault):
    _historical_code(tmp_path, "29a3c1475")
    old = C.REVIEWED_REPORT_CENSUS_ORIGINS[name]
    import subprocess
    current = hashlib.sha256(subprocess.check_output(["git", "show", "29a3c1475:" + name], cwd=ROOT)).hexdigest()
    assert current == C.REVIEWED_REPORT_CENSUS_SOURCES[name]
    assert current == H.REVIEWED_REPORT_CENSUS_HASHES[name]
    assert current == H.REVIEWED_ISSUER_BYTES_PROFILE[name]
    if fault == "origin":
        old = "0" * 64
    if fault == "successor":
        current = "0" * 64
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_preparation_preserves_reviewed_physical_origin_after_nonformat_successor(tmp_path, monkeypatch, fault):
    _historical_code(tmp_path, "29a3c1475")
    relative = "src/engine/monitoring/policy_generation_code_handoff.py"
    review = H._formatting_review()[relative]
    old, current = review["after_sha256"], C.REVIEWED_REPORT_CENSUS_SOURCES[relative]
    assert review["before_sha256"] != old and current != old
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unknown_format_origin.py"
    assert C.reviewed_preparation_pair(relative, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_preparation_alias_resolution_requires_both_pinned_origin_and_reviewed_pair(tmp_path, monkeypatch, fault):
    # Scalar registry resolution outside an active profile grants no file or
    # startup admission. Complete-profile unknown-source negatives stay real.
    monkeypatch.setattr(C, "ROOT", tmp_path)
    relative = "src/engine/monitoring/policy_generation_code_handoff.py"
    review = H._formatting_review()[relative]
    current = "f" * 64
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_SOURCES", {})
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_HISTORY", {relative: {(review["before_sha256"], current)}})
    old = review["after_sha256"]
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unknown_origin.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_MACHINE_PATH_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor"])
def test_machine_comparison_path_has_exact_independent_preparation_review(name, fault):
    old=C.REVIEWED_MACHINE_PATH_ORIGINS[name]
    current=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    if fault=="origin":old="0"*64
    if fault=="successor":current="0"*64
    assert C.reviewed_preparation_pair(name,old,current) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_NATIVE_COST_INTAKE_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_native_cost_intake_independent_preparation_preserves_original_source(tmp_path, name, fault):
    _historical_code(tmp_path, "0ee65ee7f")
    import subprocess
    old = C.REVIEWED_NATIVE_COST_INTAKE_ORIGINS[name]
    original = subprocess.check_output(["git", "-C", str(ROOT), "show", "0ee65ee7f:" + name])
    current = hashlib.sha256(original).hexdigest()
    assert current == C.REVIEWED_NATIVE_COST_INTAKE_SOURCES[name]
    assert current == H.REVIEWED_NATIVE_COST_INTAKE_PROFILE[name]
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        current = "0" * 64
    elif fault == "path":
        name = "src/engine/unreviewed_cost_owner.py"
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_PRIOR_EXECUTION_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_prior_execution_independent_preparation_exact_current_source(name, fault):
    old = C.REVIEWED_PRIOR_EXECUTION_ORIGINS[name]
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        current = "0" * 64
    elif fault == "path":
        name = "src/engine/unreviewed_prior_execution_owner.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)

@pytest.mark.parametrize("name", sorted(C.REVIEWED_QUANTITY_SOURCE_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_quantity_source_independent_preparation_keeps_exact_pair(name, fault):
    old = C.REVIEWED_QUANTITY_SOURCE_ORIGINS[name]
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        current = "0" * 64
    elif fault == "path":
        name = "src/engine/unreviewed_quantity_source.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_STOPPED_PREPARATION_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_stopped_preparation_independent_source_pair_is_exact(name, fault):
    old = C.REVIEWED_STOPPED_PREPARATION_ORIGINS[name]
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        current = "0" * 64
    elif fault == "path":
        name = "src/engine/unreviewed_stopped_preparation.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_SELL_CANCEL_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_sell_cancel_preparation_exact_reviewed_sources(relative, fault):
    old = C.REVIEWED_SELL_CANCEL_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unknown_sell_owner.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("name", sorted(C.REVIEWED_QUANTITY_COST_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_quantity_cost_preparation_pair_is_exact(name, fault):
    old = C.REVIEWED_QUANTITY_COST_ORIGINS[name]
    current = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    _assert_current_code_profile(name, current)
    if fault == "origin":
        old = "0" * 64
    elif fault == "successor":
        current = "0" * 64
    elif fault == "path":
        name = "src/engine/unreviewed_cost_source.py"
    assert C.reviewed_preparation_pair(name, old, current) is (fault is None)

@pytest.mark.parametrize('relative', sorted(C.REVIEWED_HOLDING_SOURCE_SOURCES))
@pytest.mark.parametrize('fault', [None, 'old_changed', 'current_changed'])
def test_integrated_holding_source_exact_reviewed_preparation(relative, fault):
    old=C.REVIEWED_HOLDING_SOURCE_ORIGINS[relative]
    current=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    assert C.reviewed_preparation_pair(relative, old if fault!='old_changed' else '0'*64, current if fault!='current_changed' else '1'*64) is (fault is None)

@pytest.mark.parametrize('relative', sorted(C.REVIEWED_CAPABILITY_SCOPE_SOURCES))
@pytest.mark.parametrize('fault', [None, 'old_changed', 'current_changed'])
def test_capability_scope_exact_reviewed_preparation(relative, fault):
    old=C.REVIEWED_CAPABILITY_SCOPE_ORIGINS[relative]
    current=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    assert C.reviewed_preparation_pair(relative, old if fault!='old_changed' else '0'*64, current if fault!='current_changed' else '1'*64) is (fault is None)

@pytest.mark.parametrize('relative', sorted(C.REVIEWED_CLOSED_NATIVE_PREPARATION_SOURCES))
@pytest.mark.parametrize('fault', [None, 'old_changed', 'current_changed'])
def test_closed_native_exact_reviewed_preparation(relative, fault):
    old=C.REVIEWED_CLOSED_NATIVE_PREPARATION_ORIGINS[relative]
    current=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    assert C.reviewed_preparation_pair(relative, old if fault!='old_changed' else '0'*64, current if fault!='current_changed' else '1'*64) is (fault is None)


@pytest.mark.parametrize('relative', sorted(C.REVIEWED_FINAL_SIGNAL_REFERENCE_SOURCES))
@pytest.mark.parametrize('fault', [None,'old_changed','current_changed'])
def test_final_signal_reference_exact_reviewed_preparation(relative, fault):
    old=C.REVIEWED_FINAL_SIGNAL_REFERENCE_ORIGINS[relative]
    current=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    assert C.reviewed_preparation_pair(relative, old if fault!='old_changed' else '0'*64, current if fault!='current_changed' else '1'*64) is (fault is None)


@pytest.mark.parametrize('relative', sorted(C.REVIEWED_CARRIED_OWNER_SOURCES))
@pytest.mark.parametrize('fault', [None,'old_changed','current_changed'])
def test_carried_owner_exact_reviewed_preparation(relative, fault):
    old=C.REVIEWED_CARRIED_OWNER_ORIGINS[relative]
    current=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    assert C.reviewed_preparation_pair(relative, old if fault!='old_changed' else '0'*64, current if fault!='current_changed' else '1'*64) is (fault is None)


@pytest.mark.parametrize('relative', sorted(C.REVIEWED_REPORT_ORIGIN_SOURCES))
@pytest.mark.parametrize('fault', [None,'old_changed','current_changed'])
def test_report_origin_exact_reviewed_preparation(relative, fault):
    old=C.REVIEWED_REPORT_ORIGIN_ORIGINS[relative]
    current=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    assert C.reviewed_preparation_pair(relative, old if fault!='old_changed' else '0'*64, current if fault!='current_changed' else '1'*64) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_PRE_DELIVERY_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_pre_delivery_preparation_independent_exact_sources(relative, fault):
    old = C.REVIEWED_PRE_DELIVERY_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/scanners/unreviewed_delivery.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_POSTCLOSE_COMPLETION_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_postclose_completion_independent_exact_sources(relative, fault):
    old = C.REVIEWED_POSTCLOSE_COMPLETION_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unreviewed_completion_owner.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_BUY_LINEAGE_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_buy_lineage_independent_preparation_exact_sources(relative, fault):
    old = C.REVIEWED_BUY_LINEAGE_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unreviewed_buy_lineage.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_PARTIAL_GAP_SOURCES))
def test_partial_gap_independent_preparation_pair(relative):
    import hashlib
    from src.engine.automation import intraday_release_handoff as H
    root = Path(C.__file__).resolve().parents[3]
    current = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    old = C.REVIEWED_PARTIAL_GAP_ORIGINS[relative]
    assert current == C.REVIEWED_HOLDING_HISTORY_SOURCES.get(relative, C.REVIEWED_ENTRY_LIFETIME_SOURCES.get(relative, C.REVIEWED_DELIVERY_INTEGRATED_SOURCES.get(relative, C.REVIEWED_PARTIAL_GAP_SOURCES[relative])))
    assert current == H.REVIEWED_HOLDING_HISTORY_PROFILE.get(relative, H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE[relative])
    assert C.reviewed_preparation_pair(relative, old, current)
    assert not C.reviewed_preparation_pair(relative, "f" * 64, current)
    assert not C.reviewed_preparation_pair(relative, old, "f" * 64)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_ENTRY_EXPIRY_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_entry_expiry_independent_preparation_exact_sources(relative, fault):
    old = C.REVIEWED_ENTRY_EXPIRY_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unreviewed_expiry.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_HOLDING_PROJECTION_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_holding_projection_independent_preparation_sources(relative, fault):
    old = C.REVIEWED_HOLDING_PROJECTION_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/unreviewed_holding_projection.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


def test_holding_expiry_profile_covers_requested_source_delta(tmp_path):
    import subprocess
    _historical_code(tmp_path, "3171f2a92")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "d0790117a", "3171f2a92", "--", "src/engine", "src/scanners"],
        cwd=ROOT, text=True,
    ).splitlines()
    for relative in changed:
        if relative == "src/engine/automation/intraday_release_handoff.py":
            continue  # This issuer is independently bound by the native receipt.
        raw = (tmp_path / relative).read_bytes()
        current = hashlib.sha256(raw).hexdigest()
        assert hashlib.sha256(H.reviewed_formatting_source(relative, raw)).hexdigest() == H.REVIEWED_HOLDING_EXPIRY_PROFILE[relative]
        if relative != "src/engine/infrastructure/startup_validation_code_context.py":
            old = hashlib.sha256(subprocess.check_output(
                ["git", "show", "d0790117a:" + relative], cwd=ROOT
            )).hexdigest()
            assert C.reviewed_preparation_pair(relative, old, current, root=tmp_path)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_PRECLAIM_MARKET_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_preclaim_market_independent_exact_sources(relative, fault):
    old = C.REVIEWED_PRECLAIM_MARKET_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin":
        old = "0" * 64
    if fault == "successor":
        current = "0" * 64
    if fault == "path":
        relative = "src/engine/unreviewed_preclaim.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("relative", sorted(C.REVIEWED_ENTRY_LIFETIME_SOURCES))
@pytest.mark.parametrize("fault", [None, "origin", "successor", "path"])
def test_entry_lifetime_independent_preparation_checks_each_actual_source(relative, fault):
    old = C.REVIEWED_ENTRY_LIFETIME_ORIGINS[relative]
    current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    _assert_current_code_profile(relative, current)
    if fault == "origin": old = "0" * 64
    if fault == "successor": current = "0" * 64
    if fault == "path": relative = "src/engine/scalping/unreviewed_lifetime.py"
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "origin", "unregistered"])
def test_scoped_entry_preparation_requires_complete_reviewed_generation(
    tmp_path, monkeypatch, fault
):
    first, second = "src/engine/scalping/first.py", "src/engine/scalping/second.py"
    for relative, contents in ((first, b"first current"), (second, b"second current")):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    current = hashlib.sha256(b"first current").hexdigest()
    other = hashlib.sha256(b"second current").hexdigest()
    old = hashlib.sha256(b"first origin").hexdigest()
    monkeypatch.setattr(C, "ROOT", tmp_path)
    monkeypatch.setattr(C, "REVIEWED_SCOPED_ENTRY_CHANGED", {first: current})
    monkeypatch.setattr(
        C, "REVIEWED_SCOPED_ENTRY_PROFILE", {first: current, second: other}
    )
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_HISTORY", {first: {(old, current)}})
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_SOURCES", {})
    if fault == "missing":
        (tmp_path / second).unlink()
    elif fault == "mixed":
        (tmp_path / second).write_bytes(b"unreviewed generation")
    elif fault == "origin":
        old = "0" * 64
    elif fault == "unregistered":
        first = "src/engine/scalping/unreviewed.py"
    assert C.reviewed_preparation_pair(first, old, current) is (fault is None)


def test_scoped_entry_keeps_original_reviewed_formatting_predecessor(
    tmp_path, monkeypatch
):
    relative = "src/engine/scalping/first.py"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b"reviewed current")
    current = hashlib.sha256(path.read_bytes()).hexdigest()
    old = hashlib.sha256(b"reviewed original").hexdigest()
    projected = hashlib.sha256(b"reviewed common projection").hexdigest()
    monkeypatch.setattr(C, "ROOT", tmp_path)
    monkeypatch.setattr(C, "REVIEWED_SCOPED_ENTRY_CHANGED", {relative: current})
    monkeypatch.setattr(C, "REVIEWED_SCOPED_ENTRY_PROFILE", {relative: current})
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_HISTORY", {})
    monkeypatch.setattr(C, "REVIEWED_PREPARATION_SOURCES", {})
    monkeypatch.setattr(
        H,
        "reviewed_formatting_predecessor",
        lambda name, sha: (
            projected if name == relative and sha in {old, current} else sha
        ),
    )
    assert C.reviewed_preparation_pair(relative, old, current)


def test_scoped_entry_profiles_cover_every_changed_native_contract_member():
    import subprocess
    from src.engine.scalping import continuous_reversal_policy_v6 as native
    from src.engine.monitoring import policy_generation_contract as report

    baseline = "8fadd634d89d3e617680f5deabd1080cf89d6caf"
    paths = {Path(m.__file__).resolve().relative_to(ROOT).as_posix() for m in native.contract_modules()}
    paths.add("src/engine/ai_engine_openai.py")
    changed = set()
    for relative in paths:
        old = subprocess.check_output(["git", "show", f"{baseline}:{relative}"], cwd=ROOT)
        if hashlib.sha256(old).hexdigest() != hashlib.sha256((ROOT / relative).read_bytes()).hexdigest():
            changed.add(relative)
    assert changed <= (set(C.REVIEWED_CRON_PHASE_BINDING_CHANGED)
                       | set(C.REVIEWED_SUBMISSION_MONITOR_TRANSITION)
                       | set(C.REVIEWED_STOP_INCIDENT_TRANSITION))
    preparation = "src/engine/infrastructure/startup_validation_code_context.py"
    report_paths = {str((ROOT / "src/engine" / name).resolve().relative_to(ROOT)) for names in report.COMPONENTS.values() for name in (*names, *report.COMMON_CODE_COMPONENTS)}
    report_changed = set()
    for relative in report_paths:
        old = subprocess.check_output(["git", "show", f"{baseline}:{relative}"], cwd=ROOT)
        if hashlib.sha256(old).hexdigest() != hashlib.sha256((ROOT / relative).read_bytes()).hexdigest():
            report_changed.add(relative)
    expected = changed | report_changed | {preparation}
    all_changed = set(subprocess.check_output(
        ["git", "diff", "--name-only", baseline, "--", "src", "deploy"], cwd=ROOT, text=True
    ).splitlines())
    all_changed = {n for n in all_changed if n.endswith((".py", ".sh"))
                   and not n.startswith("src/tests/")
                   and not n.endswith(("intraday_release_handoff.py", "startup_validation_code_context.py"))}
    assert expected <= all_changed | {preparation}
    reviewed = {**H.REVIEWED_CRON_PHASE_BINDING_CHANGED,
                **H.REVIEWED_SCHEDULED_SUFFIX_CHANGED,
                **H.REVIEWED_P5_RECHECK_CHANGED,
                **H.REVIEWED_SUBMISSION_MONITOR_HASHES,
                **H.REVIEWED_STOP_INCIDENT_HASHES}
    runtime_import_only = {"src/engine/daily_report_service.py"}
    assert all_changed | {preparation} <= set(reviewed) | runtime_import_only
    # A declared unchanged dependency is legitimate, but must retain the exact
    # baseline bytes and its own approved comparison representation.
    for relative in set(reviewed) - (all_changed | {preparation}):
        raw = (ROOT / relative).read_bytes()
        assert raw == subprocess.check_output(["git", "show", baseline + ":" + relative], cwd=ROOT)
        assert hashlib.sha256(H.reviewed_formatting_source(relative, raw)).hexdigest() == reviewed[relative]
    for relative in expected:
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == reviewed[relative]


def test_issued_entry_member_is_bound_without_rewriting_old_policy_inventory(monkeypatch):
    """P5 accepts only the attested added member; the issued list stays exact."""
    import hashlib
    import copy

    member = "src/engine/scalping/entry_deadline.py"
    prior = "src/engine/scalping/reversal_path_runtime.py"
    member_sha = hashlib.sha256((C.ROOT / member).read_bytes()).hexdigest()
    prior_sha = hashlib.sha256((C.ROOT / prior).read_bytes()).hexdigest()
    ident = "a" * 64
    policy = {
        "bundle_sha256": ident,
        "target_date": "2026-10-28",
        "continuous_reversal": {
            "schema": "continuous_reversal_policy_v6",
            "contract_file_sha256": {"reversal_path_runtime.py": prior_sha},
        },
    }
    extension = {
        "relative": member,
        "original_sha256": "b" * 64,
        "runtime_sha256": member_sha,
    }
    proof = {
        "inventories": [{
            "bundle_sha256": ident,
            "target_date": "2026-10-28",
            "schema": "continuous_reversal_policy_v6",
            "expected": {"reversal_path_runtime.py": prior_sha},
        }],
        "active_entry_code_extension": extension,
        "original_code_hashes": {member: extension["original_sha256"]},
        "runtime_code_hashes": {member: member_sha, prior: prior_sha},
    }
    monkeypatch.setattr(C, "_main_context", lambda: proof)
    paths = {
        "reversal_path_runtime.py": str(C.ROOT / prior),
        "entry_deadline.py": str(C.ROOT / member),
    }
    actual = {"reversal_path_runtime.py": prior_sha, "entry_deadline.py": member_sha}
    assert C.verify_validation_main_code(policy, paths, actual)
    damaged = copy.deepcopy(proof)
    damaged["active_entry_code_extension"]["runtime_sha256"] = "0" * 64
    monkeypatch.setattr(C, "_main_context", lambda: damaged)
    with pytest.raises(ValueError, match="extension_unbound"):
        C.verify_validation_main_code(policy, paths, actual)
    monkeypatch.setattr(C, "_main_context", lambda: proof)
    with pytest.raises(ValueError, match="inventory_unbound"):
        C.verify_validation_main_code(policy, {k: v for k, v in paths.items() if k != "entry_deadline.py"}, actual)


@pytest.mark.parametrize("carry_forward", [False, True])
def test_entry_member_handoff_survives_candidate_to_selected_phase(tmp_path, monkeypatch, carry_forward):
    """The same issued handoff binds old and selected code without resealing policy."""
    import hashlib
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_code_handoff as H
    from src.engine.scalping import continuous_reversal_postclose as P

    relative = "src/engine/scalping/entry_deadline.py"
    old, new, data = (tmp_path / name for name in ("old", "new", "data"))
    for root, value in ((old, b"new entry source" if carry_forward else b"old entry source"), (new, b"new entry source")):
        path = root / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(value)
    old_sha = hashlib.sha256((old / relative).read_bytes()).hexdigest()
    new_sha = hashlib.sha256((new / relative).read_bytes()).hexdigest()
    legacy_sha = hashlib.sha256(b"old entry source").hexdigest()
    monkeypatch.setitem(C.REVIEWED_ENTRY_LIFETIME_ORIGINS, relative, legacy_sha)
    monkeypatch.setitem(C.REVIEWED_ENTRY_LIFETIME_SOURCES, relative, new_sha)
    monkeypatch.setattr(C, "reviewed_preparation_pair", lambda name, before, after: (name, before, after) == (relative, legacy_sha, new_sha))
    monkeypatch.setattr(C, "_git_head", lambda root: "b" * 40 if Path(root) == old else "c" * 40)
    pointer = data / "runtime/mechanistic_entry_policy/current.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(json.dumps({"bundle_sha256": "a" * 64}))
    receipt_path = tmp_path / "handoff.json"
    monkeypatch.setattr(H, "path", lambda *args: receipt_path)
    code_hashes = {str(new / relative): new_sha}
    monkeypatch.setattr(H, "code_hashes", lambda: code_hashes)
    receipt = P.seal(dict(
        schema=H.SCHEMA, authority=H.AUTHORITY, target_date="2026-10-28",
        release_commit="c" * 40, release_root=str(new),
        bundle_sha256="a" * 64, current_pointer_sha256=C._sha(pointer),
        origin_root=str(old), origin_commit="b" * 40,
        code_hashes=code_hashes, source_hashes={str(pointer):C._sha(pointer)},
        actual_pid_consumed=False, policy_reselected=False,
        provider_called=False, source_semantics_repair=True,
    ))
    receipt_path.write_text(json.dumps(receipt))
    names = {Path(module.__file__).name for module in V.contract_modules()}
    inventories = [dict(schema=V.SCHEMA, expected={name: "d" * 64 for name in names - {"entry_deadline.py"}})]
    before = C._active_entry_code_extension(data, "2026-10-28", old, new, "c" * 40, inventories)
    after = C._active_entry_code_extension(data, "2026-10-28", new, new, "c" * 40, inventories)
    assert before["original_sha256"] == old_sha
    assert after["original_sha256"] == new_sha
    assert before["receipt_sha256"] == after["receipt_sha256"]
    monkeypatch.setitem(C.REVIEWED_ENTRY_LIFETIME_SOURCES, relative, "0" * 64)
    with pytest.raises(ValueError, match="extension_unbound"):
        C._active_entry_code_extension(data, "2026-10-28", new, new, "c" * 40, inventories)
    monkeypatch.setitem(C.REVIEWED_ENTRY_LIFETIME_SOURCES, relative, new_sha)
    (old / relative).write_bytes(b"changed original")
    with pytest.raises(ValueError, match="extension_unbound"):
        C._active_entry_code_extension(data, "2026-10-28", new, new, "c" * 40, inventories)


def test_entry_member_carry_profile_is_complete_and_preserves_issued_predecessor():
    name = 'src/engine/infrastructure/startup_validation_code_context.py'
    import subprocess
    import hashlib
    issued = subprocess.check_output(["git", "-C", str(ROOT), "show", "c780d4679:" + name])
    assert H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE[name] == hashlib.sha256(issued).hexdigest()
    assert H.REVIEWED_ENTRY_LIFETIME_PROFILE[name] != H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE[name]
    assert set(H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE) == set(H.REVIEWED_ENTRY_LIFETIME_PROFILE)
    assert {k for k in H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE if H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE[k] != H.REVIEWED_ENTRY_LIFETIME_PROFILE[k]} == {name}
    assert H.REVIEWED_ENTRY_MEMBER_CARRY_VARIANTS
    for row in H.REVIEWED_ENTRY_MEMBER_CARRY_VARIANTS.values():
        assert row['selector_path'] == name
        assert row['selector_sha256'] == H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE[name]
        assert row['dependencies'][name] == H.REVIEWED_ENTRY_MEMBER_CARRY_PROFILE[name]


@pytest.mark.parametrize("fault", [None, "missing", "dirty", "parent_mix", "symlink"])
@pytest.mark.parametrize("relative", sorted(C.REVIEWED_POSTCLOSE_INTEGRATED_SOURCES))
def test_held_sell_independent_reader_requires_complete_native_pair(tmp_path, monkeypatch, fault, relative):
    import subprocess
    for name in C.REVIEWED_POSTCLOSE_INTEGRATED_SOURCES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "3f6dd4852:" + name]))
    monkeypatch.setattr(C, "ROOT", tmp_path)
    damaged = next(name for name in C.REVIEWED_POSTCLOSE_INTEGRATED_SOURCES if name != relative)
    path = tmp_path / damaged
    if fault == "missing":
        path.unlink()
    elif fault == "dirty":
        path.write_bytes(path.read_bytes() + b"\n")
    elif fault == "parent_mix":
        path.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "c780d4679:" + damaged,
        ]))
    elif fault == "symlink":
        original = tmp_path / "outside.py"
        original.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(original)
    assert C.reviewed_preparation_pair(
        relative, C.REVIEWED_POSTCLOSE_INTEGRATED_ORIGINS[relative],
        C.REVIEWED_POSTCLOSE_INTEGRATED_SOURCES[relative],
    ) is (fault is None)


def test_preopen_validation_inventory_reaches_both_native_readers(tmp_path):
    """Operational review alone cannot authorize the independent Main child."""
    assert C.REVIEWED_PREOPEN_VALIDATION_SOURCES == {
        name: sha
        for name, sha in H.REVIEWED_PREOPEN_VALIDATION_HASHES.items()
        if name != "src/engine/infrastructure/startup_validation_code_context.py"
    }
    for name, expected in H.REVIEWED_PREOPEN_VALIDATION_HASHES.items():
        assert hashlib.sha256(subprocess.check_output(["git", "-C", str(ROOT), "show", "6d9ed3575:" + name])).hexdigest() == expected
    _historical_code(tmp_path, "6d9ed3575")
    for name, current in C.REVIEWED_PREOPEN_VALIDATION_SOURCES.items():
        assert C.reviewed_preparation_pair(name, C.REVIEWED_PREOPEN_VALIDATION_ORIGINS[name], current, root=tmp_path)
        present = C._sha(ROOT / name)
        _assert_current_code_profile(name, present)
        C._pairs({name: C.REVIEWED_PREOPEN_VALIDATION_ORIGINS[name]}, {name: present})


@pytest.mark.parametrize(
    "fault", [None, "missing", "changed", "symlink", "old", "current"]
)
@pytest.mark.parametrize("relative", sorted(C.REVIEWED_PREOPEN_VALIDATION_SOURCES))
def test_preopen_validation_independent_reader_requires_whole_generation(
    tmp_path, monkeypatch, fault, relative
):
    for name in C.REVIEWED_PREOPEN_VALIDATION_PROFILE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "6d9ed3575:" + name]))
    monkeypatch.setattr(C, "ROOT", tmp_path)
    damaged = next(
        name for name in C.REVIEWED_PREOPEN_VALIDATION_SOURCES if name != relative
    )
    path = tmp_path / damaged
    if fault == "missing":
        path.unlink()
    elif fault == "changed":
        path.write_bytes(path.read_bytes() + b"\n")
    elif fault == "symlink":
        original = tmp_path / "outside"
        original.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(original)
    before = C.REVIEWED_PREOPEN_VALIDATION_ORIGINS[relative]
    after = C.REVIEWED_PREOPEN_VALIDATION_SOURCES[relative]
    if fault == "old":
        before = "0" * 64
    if fault == "current":
        after = "1" * 64
    if fault:
        with pytest.raises(ValueError, match="startup_main_code_pair_unreviewed"):
            C._pairs({relative: before}, {relative: after})
    else:
        C._pairs({relative: before}, {relative: after})


@pytest.mark.parametrize("fault", [None, "missing", "changed", "symlink", "unknown", "missing_handler", "missing_probe"])
def test_timeout_terminal_independent_reader_requires_complete_generation(tmp_path, monkeypatch, fault):
    for name in C.REVIEWED_TIMEOUT_TERMINAL_PROFILE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "65a05719a:" + name]))
    monkeypatch.setattr(C, "ROOT", tmp_path)
    relative = C.REVIEWED_TIMEOUT_TERMINAL_PATH
    damaged = tmp_path / "src/engine/scalping/reversal_auxiliary_production_input.py"
    if fault == "missing":
        damaged.unlink()
    elif fault == "changed":
        damaged.write_bytes(damaged.read_bytes() + b"\n")
    elif fault == "symlink":
        outside = tmp_path / "outside.py"
        outside.write_bytes(damaged.read_bytes())
        damaged.unlink()
        damaged.symlink_to(outside)
    elif fault == "missing_handler":
        (tmp_path / relative).unlink()
    elif fault == "missing_probe":
        (tmp_path / C.REVIEWED_TIMEOUT_PROBE_PATH).unlink()
    old = "0" * 64 if fault == "unknown" else C.REVIEWED_HOLDING_HISTORY_SOURCES[relative]
    assert C.reviewed_preparation_pair(relative, old, C.REVIEWED_TIMEOUT_TERMINAL_HANDLER) is (fault is None)


def test_holding_history_inventory_reaches_independent_preparation_reader(tmp_path, monkeypatch):
    import subprocess

    assert C.REVIEWED_HOLDING_HISTORY_SOURCES == {
        name: sha for name, sha in H.REVIEWED_HOLDING_HISTORY_HASHES.items()
        if name != "src/engine/infrastructure/startup_validation_code_context.py"
    }
    for name, expected in H.REVIEWED_HOLDING_HISTORY_HASHES.items():
        source = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "cc4028ba8:" + name]
        )
        assert hashlib.sha256(source).hexdigest() == expected
    for name in C.REVIEWED_HOLDING_HISTORY_PROFILE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "cc4028ba8:" + name]
        ))
    monkeypatch.setattr(C, "ROOT", tmp_path)
    for name, current in C.REVIEWED_HOLDING_HISTORY_SOURCES.items():
        C._pairs({name: C.REVIEWED_HOLDING_HISTORY_ORIGINS[name]}, {name: current})


@pytest.mark.parametrize("fault", [None, "missing", "changed", "symlink", "unknown"])
def test_holding_history_independent_reader_requires_complete_generation(tmp_path, monkeypatch, fault):
    import subprocess

    for name in C.REVIEWED_HOLDING_HISTORY_PROFILE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "cc4028ba8:" + name]
        ))
    monkeypatch.setattr(C, "ROOT", tmp_path)
    relative = "src/engine/scalping/holding_profit_exit_semantics.py"
    damaged = tmp_path / "src/engine/scalping/reversal_auxiliary_production_input.py"
    if fault == "missing": damaged.unlink()
    elif fault == "changed": damaged.write_bytes(damaged.read_bytes()+b"\n")
    elif fault == "symlink":
        outside = tmp_path / "outside.py"
        outside.write_bytes(damaged.read_bytes());damaged.unlink();damaged.symlink_to(outside)
    old = "0" * 64 if fault == "unknown" else C.REVIEWED_HOLDING_HISTORY_ORIGINS[relative]
    assert C.reviewed_preparation_pair(relative, old, C.REVIEWED_HOLDING_HISTORY_SOURCES[relative]) is (fault is None)
    assert C.reviewed_preparation_pair(
        "src/engine/holding_exit_sentinel.py",
        "0" * 64 if fault == "unknown" else "c1d1868fee331a01bf8562965e3ada03c7ed20b61df4149f99308629b52a8b96",
        C.REVIEWED_HOLDING_HISTORY_SOURCES["src/engine/holding_exit_sentinel.py"],
    ) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "changed", "symlink", "unknown", "mixed_handler"])
def test_probe_avg_independent_reader_preserves_complete_profile(tmp_path, monkeypatch, fault):
    for name, expected in C.REVIEWED_PROBE_AVG_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        content = subprocess.check_output(["git", "-C", str(ROOT), "show", "8fadd634d:" + name])
        assert hashlib.sha256(content).hexdigest() == expected
        path.write_bytes(content)
    monkeypatch.setattr(C, "ROOT", tmp_path)
    relative = C.REVIEWED_TIMEOUT_TERMINAL_PATH
    damaged = tmp_path / "src/engine/scalping/avg_down_rebound.py"
    if fault == "missing":
        damaged.unlink()
    elif fault == "changed":
        damaged.write_bytes(damaged.read_bytes() + b"\n")
    elif fault == "symlink":
        outside = tmp_path / "outside.py"
        outside.write_bytes(damaged.read_bytes())
        damaged.unlink()
        damaged.symlink_to(outside)
    elif fault == "mixed_handler":
        (tmp_path / relative).write_bytes(subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "cc4028ba8:" + relative]))
    old = "0" * 64 if fault == "unknown" else C.REVIEWED_TIMEOUT_TERMINAL_HANDLER
    assert C.reviewed_preparation_pair(relative, old, C.REVIEWED_PROBE_AVG_CHANGED[relative]) is (fault is None)


@pytest.mark.parametrize("dependency", sorted(C.REVIEWED_SCHEDULED_SUFFIX_DEPENDENCIES))
@pytest.mark.parametrize("fault", [None, "missing", "changed", "symlink", "unknown"])
def test_scheduled_suffix_report_comparison_binds_native_calendar(
    tmp_path, monkeypatch, dependency, fault
):
    # Keep the issued startup-required inventory unchanged. The report-only
    # comparison endpoint additionally binds its own calendar dependency.
    inventory = {**C.REVIEWED_CRON_PHASE_BINDING_PROFILE,
                 **C.REVIEWED_SCHEDULED_SUFFIX_DEPENDENCIES}
    for name, expected in inventory.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = subprocess.check_output(["git", "-C", str(ROOT), "show", "52425f68f:" + name])
        assert hashlib.sha256(raw).hexdigest() == expected
        path.write_bytes(raw)
    monkeypatch.setattr(C, "ROOT", tmp_path)
    damaged = tmp_path / dependency
    if fault == "missing": damaged.unlink()
    elif fault == "changed": damaged.write_bytes(damaged.read_bytes() + b"\n")
    elif fault == "symlink":
        other = tmp_path / "outside.py"
        other.write_bytes(damaged.read_bytes())
        damaged.unlink()
        damaged.symlink_to(other)
    owner = "src/engine/automation/postclose_finalization_generation.py"
    old = ("0" * 64 if fault == "unknown" else
           "a2a29adac3c9777bd6ffc26ae480b80e49a40cd19fc40ce8b0e5479a21f9e9d2")
    assert C.reviewed_preparation_pair(
        owner, old, C.REVIEWED_SCHEDULED_SUFFIX_DEPENDENCIES[owner]
    ) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "changed", "symlink", "unknown", "mixed"])
def test_p5_recheck_independent_reader_binds_complete_predecessor(tmp_path, monkeypatch, fault):
    for name, expected in C.REVIEWED_P5_RECHECK_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = subprocess.check_output(["git", "-C", str(ROOT), "show", "003865007:" + name])
        assert hashlib.sha256(raw).hexdigest() == expected
        path.write_bytes(raw)
    owner = "src/engine/automation/main_startup_validation.py"
    dependency = "src/engine/automation/next_preopen_readiness.py"
    damaged = tmp_path / dependency
    if fault == "missing":
        damaged.unlink()
    elif fault == "changed":
        damaged.write_bytes(damaged.read_bytes() + b"\n")
    elif fault == "symlink":
        other = tmp_path / "outside.py"
        other.write_bytes(damaged.read_bytes())
        damaged.unlink()
        damaged.symlink_to(other)
    elif fault == "mixed":
        (tmp_path / owner).write_bytes(subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "52425f68f:" + owner]))
    monkeypatch.setattr(C, "ROOT", tmp_path)
    old = "0" * 64 if fault == "unknown" else C.REVIEWED_CRON_PHASE_BINDING_PROFILE[owner]
    assert C.reviewed_preparation_pair(owner, old, C._P5_RECHECK_CURRENT) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "changed", "symlink", "unknown", "predecessor_mix"])
def test_startup_storage_independent_reader_keeps_exact_complete_generation(tmp_path, fault):
    import runpy

    # This issued generation is authenticated by its original reader, as in
    # the native predecessor boundary. A later generation's trigger is not
    # authority to reinterpret this historical preparation profile.
    _historical_code(tmp_path, "81b1c653b")
    original = runpy.run_path(str(tmp_path / "src/engine/infrastructure/startup_validation_code_context.py"))
    assert original["REVIEWED_STARTUP_STORAGE_PROFILE"] == C.REVIEWED_STARTUP_STORAGE_PROFILE
    for name, expected in C.REVIEWED_STARTUP_STORAGE_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        content = subprocess.check_output(["git", "-C", str(ROOT), "show", "81b1c653b:" + name])
        assert hashlib.sha256(content).hexdigest() == expected
        path.write_bytes(content)
    relative = "src/engine/infrastructure/validation_digest_session.py"
    damaged = tmp_path / relative
    if fault == "missing": damaged.unlink()
    elif fault == "changed": damaged.write_bytes(damaged.read_bytes() + b"\n")
    elif fault == "symlink":
        outside = tmp_path / "outside.py"; outside.write_bytes(damaged.read_bytes())
        damaged.unlink(); damaged.symlink_to(outside)
    elif fault == "predecessor_mix":
        damaged.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "8fadd634d:" + relative]))
    old = "0" * 64 if fault == "unknown" else C.REVIEWED_STARTUP_STORAGE_ORIGINS[relative][0]
    assert original["reviewed_preparation_pair"](relative, old, C.REVIEWED_STARTUP_STORAGE_CHANGED[relative]) is (fault is None)


@pytest.mark.parametrize("profile,commit", [("STARTUP_SCOPED", "fda0b109c"), ("STARTUP_SCOPED_AUX", "4b69dfc05"), ("LIFETIME_SOURCE_PHASE", "c6d3f010b"), ("DATED_REPORT_PARENT", "a1ef8c897"), ("CANCEL_STATE_STORAGE", "a5904ac8f"), ("CANCEL_STORAGE_REVIEW", "0dc6b0393"), ("CAUSAL_ITEM", "b97ff1b99"), ("PREFIX_COST_CONTEXT", "0f3ce4ebf"), ("PREFIX_COST_HANDOFF", "4846f2b2e"), ("CRON_PHASE_BINDING", "52425f68f")])
@pytest.mark.parametrize("fault", [None, "missing", "mixed", "origin", "unknown", "future"])
def test_combined_startup_scoped_independent_exact_generation(tmp_path, monkeypatch, fault, profile, commit):
    hashes = getattr(C, "REVIEWED_" + profile + "_PROFILE")
    for name, expected in hashes.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        path.write_bytes(subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT) if commit else (ROOT / name).read_bytes())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    relative = "src/engine/scalping/entry_deadline.py"
    dependency = "src/engine/infrastructure/validation_digest_session.py"
    if fault == "missing":
        (tmp_path / dependency).unlink()
    if fault == "mixed":
        import subprocess
        (tmp_path / dependency).write_bytes(subprocess.check_output(
            ["git", "show", "8fadd634d:" + dependency], cwd=ROOT))
    old = getattr(C, "REVIEWED_" + profile + "_ORIGINS")[relative][0]
    if fault == "origin":
        old = "0" * 64
    if fault == "unknown":
        relative = "src/engine/scalping/unknown_generation.py"
    endpoint = hashes.get(relative, "1" * 64)
    if fault == "future":
        relative = "src/engine/infrastructure/runtime_release_router.py"
        old = C.REVIEWED_CRON_PHASE_BINDING_ORIGINS[relative][0]
        endpoint = ("f" * 64 if profile == "CRON_PHASE_BINDING"
                    else C.REVIEWED_CRON_PHASE_BINDING_CHANGED[relative])
    monkeypatch.setattr(C, "ROOT", tmp_path)
    assert C.reviewed_preparation_pair(relative, old, endpoint) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "alias", "origin", "future", "unregistered"])
def test_submission_monitor_registration_reaches_independent_native_reader(
    tmp_path, monkeypatch, fault
):
    for name, expected in C.REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "af07f6f6a:" + name
        ]))
        assert C._sha(path) == expected
    relative, (old, current) = next(iter(C.REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION.items()))
    dependency = tmp_path / "src/engine/infrastructure/validation_digest_session.py"
    if fault == "missing":
        dependency.unlink()
    elif fault == "mixed":
        dependency.write_bytes(dependency.read_bytes() + b"\n# changed generation\n")
    elif fault == "alias":
        real = dependency.with_suffix(".original")
        dependency.rename(real)
        dependency.symlink_to(real)
    elif fault == "origin":
        old = "f" * 64
    elif fault == "future":
        current = "f" * 64
    elif fault == "unregistered":
        relative = "src/engine/monitoring/new_consumer.py"
        path = tmp_path / relative
        path.write_bytes(b"# unregistered consumer\n")
        current = C._sha(path)
    monkeypatch.setattr(C, "ROOT", tmp_path)
    if fault is None:
        C._pairs({relative: old}, {relative: current})
    else:
        with pytest.raises(ValueError, match="startup_main_code_pair_unreviewed"):
            C._pairs({relative: old}, {relative: current})


@pytest.mark.parametrize("phase", ["candidate", "predecessor", "alias", "missing"])
def test_submission_monitor_pair_keeps_explicit_comparison_root(tmp_path, phase):
    candidate = tmp_path / "candidate"
    for name in C.REVIEWED_SUBMISSION_MONITOR_PROFILE:
        path = candidate / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "af07f6f6a:" + name
        ]))
    relative, pair = next(iter(C.REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION.items()))
    comparison = candidate
    if phase == "predecessor":
        (candidate / relative).write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "52425f68f:" + relative
        ]))
    elif phase == "alias":
        comparison = tmp_path / "alias"
        comparison.symlink_to(candidate, target_is_directory=True)
    elif phase == "missing":
        comparison = tmp_path / "missing"
    assert C.reviewed_preparation_pair(relative, *pair, root=comparison) is (phase == "candidate")


@pytest.mark.parametrize("generation", ["prior", "current"])
@pytest.mark.parametrize("fault", [None, "missing", "mixed", "unknown_origin"])
def test_submission_native_generations_preserve_issued_predecessor_and_reject_mixes(tmp_path, generation, fault):
    profile = C.REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE if generation == "prior" else C.REVIEWED_STOP_INCIDENT_PROFILE
    for name, expected in profile.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "af07f6f6a:" + name])
                         if generation == "prior" else (ROOT / name).read_bytes())
        assert C._sha(path) == expected
    monitor = "src/engine/monitoring/submission_bottleneck_monitor.py"
    if fault == "missing": (tmp_path / "src/engine/ai_engine_openai.py").unlink()
    elif fault == "mixed":
        changed = "src/engine/scalping/continuous_reversal_policy_v6.py"
        (tmp_path / changed).write_bytes((ROOT / changed).read_bytes() if generation == "prior" else
            subprocess.check_output(["git", "-C", str(ROOT), "show", "af07f6f6a:" + changed]))
    for name in (monitor,) if generation == "prior" else C.REVIEWED_SUBMISSION_MONITOR_TRANSITION:
        old = C.REVIEWED_SUBMISSION_MONITOR_TRANSITION[name][0]
        if fault == "unknown_origin": old = "f" * 64
        assert C.reviewed_preparation_pair(name, old, profile[name], root=tmp_path) is (fault is None)
    if generation == "current" and fault is None:
        assert C.reviewed_preparation_pair(monitor,
            C.REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE[monitor], profile[monitor], root=tmp_path)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "alias", "origin", "future", "unregistered"])
def test_stop_incident_generation_reaches_independent_reader(tmp_path, fault):
    assert C._STOP_INCIDENT_OFFLINE_OWNER not in C.REVIEWED_STOP_INCIDENT_PROFILE
    for name, expected in C.REVIEWED_STOP_INCIDENT_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raw = subprocess.check_output([
                "git", "-C", str(ROOT), "show", "3e3d5da2c:" + name
            ])
        path.write_bytes(raw)
        assert C._sha(path) == expected
    relative = "src/engine/sniper_state_handlers.py"
    old, current = C.REVIEWED_STOP_INCIDENT_TRANSITION[relative]
    dependency = tmp_path / "src/engine/scalping/main_stop_quantity_source.py"
    if fault == "missing":
        dependency.unlink()
    elif fault == "mixed":
        dependency.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "af07f6f6a:src/engine/scalping/main_stop_quantity_source.py"
        ]))
    elif fault == "alias":
        original = dependency.with_suffix(".original")
        dependency.rename(original)
        dependency.symlink_to(original)
    elif fault == "origin":
        old = "0" * 64
    elif fault == "future":
        current = "f" * 64
    elif fault == "unregistered":
        relative = "src/engine/scalping/unknown_generation.py"
    assert C.reviewed_preparation_pair(relative, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "alias", "origin", "future"])
def test_common_support_successor_requires_complete_preparation_generation(tmp_path, fault):
    for name, expected in C.REVIEWED_COMMON_SUPPORT_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raw = subprocess.check_output(["git", "-C", str(ROOT), "show", "73efe4115:" + name])
        path.write_bytes(raw)
        assert C._sha(path) == expected
    relative, (old, current) = next(iter(C.REVIEWED_COMMON_SUPPORT_TRANSITION.items()))
    dependency = tmp_path / "src/engine/scalping/main_stop_quantity_source.py"
    if fault == "missing":
        dependency.unlink()
    elif fault == "mixed":
        dependency.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "af07f6f6a:src/engine/scalping/main_stop_quantity_source.py"
        ]))
    elif fault == "alias":
        original = dependency.with_suffix(".original")
        dependency.rename(original)
        dependency.symlink_to(original)
    elif fault == "origin":
        old = "0" * 64
    elif fault == "future":
        current = "f" * 64
    assert C.reviewed_preparation_pair(relative, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "origin", "future"])
def test_interrupted_custody_requires_complete_combined_generation(tmp_path, fault):
    for name, expected in C.REVIEWED_INTERRUPTED_CUSTODY_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raw = subprocess.check_output(["git", "-C", str(ROOT), "show", "23fbecf28:" + name])
        path.write_bytes(raw)
        assert C._sha(path) == expected
    name, (old, current) = next(iter(C.REVIEWED_INTERRUPTED_CUSTODY_TRANSITION.items()))
    dependency = tmp_path / "src/engine/scalping/reversal_auxiliary_intraday.py"
    if fault == "missing": dependency.unlink()
    elif fault == "mixed": dependency.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "3e3d5da2c:src/engine/scalping/reversal_auxiliary_intraday.py"]))
    elif fault == "origin": old = "0" * 64
    elif fault == "future": current = "f" * 64
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "origin", "future"])
def test_p5_consumer_union_requires_complete_current_generation(tmp_path, fault):
    for name, expected in C.REVIEWED_P5_CONSUMER_UNION_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "85ede0d11:" + name]))
        assert C._sha(path) == expected
    name, (old, current) = next(iter(C.REVIEWED_P5_CONSUMER_UNION_TRANSITION.items()))
    dependency = tmp_path / "src/engine/scalping/reversal_auxiliary_intraday.py"
    if fault == "missing":
        dependency.unlink()
    elif fault == "mixed":
        dependency.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "3e3d5da2c:src/engine/scalping/reversal_auxiliary_intraday.py"
        ]))
    elif fault == "origin":
        old = "0" * 64
    elif fault == "future":
        current = "f" * 64
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)


def test_storage_integration_registered_for_both_native_readers():
    """A future profile drift fails before candidate admission, not at launch."""
    assert set(C.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE) <= set(
        H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE
    )
    for name, expected in C.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE.items():
        raw = (ROOT / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, name
        compared = H.reviewed_formatting_source(name, raw)
        assert hashlib.sha256(compared).hexdigest() == H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[name], name
    context = "src/engine/infrastructure/startup_validation_code_context.py"
    assert C._sha(ROOT / context) == H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[context]
    # The actual selected predecessor precedes the P5-only intermediate. The
    # complete storage generation must inherit both declared P5 endpoints,
    # without requiring an intermediate release to run merely for custody.
    for pair in H.REVIEWED_P5_CONSUMER_UNION_PAIRS[context]:
        for origin in pair:
            assert (origin, H.REVIEWED_STORAGE_INTEGRATION_HASHES[context]) in H.REVIEWED_STORAGE_INTEGRATION_PAIRS[context]
    assert ("f" * 64, H.REVIEWED_STORAGE_INTEGRATION_HASHES[context]) not in H.REVIEWED_STORAGE_INTEGRATION_PAIRS[context]
    for (name, digest), variant in H.REVIEWED_POSTCLOSE_SCHEDULE_VARIANTS.items():
        if name in H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE:
            assert digest == H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[name]
        assert variant["selector_sha256"] == H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[variant["selector_path"]]
        for name, digest in variant["dependencies"].items():
            if name in H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE:
                assert digest == H.REVIEWED_POSTCLOSE_SCHEDULE_PROFILE[name], name


@pytest.mark.parametrize(
    "fault",
    [None, "missing", "unknown", "mixed", "detector_prior", "both_unknown", "origin", "ordered_prior", "ordered_unknown"],
)
def test_postclose_schedule_dependency_reaches_both_actual_readers(current_releases, fault):
    """The new direct consumer is required even for an older caller inventory."""
    release = current_releases
    root = release["root"]
    detector = "src/engine/error_detectors/artifact_freshness.py"
    resolver = "src/engine/error_detectors/schedule_contract.py"
    ordered = "src/engine/automation/ordered_intraday_deploy.py"
    originals = {name: (root / name).read_bytes() for name in (detector, resolver, ordered)}
    old, current = C.REVIEWED_POSTCLOSE_SCHEDULE_TRANSITION[detector]
    try:
        if fault == "missing":
            (root / resolver).unlink()
        elif fault == "unknown":
            (root / resolver).write_bytes(b"unreviewed schedule consumer\n")
        elif fault in {"mixed", "detector_prior"}:
            name = resolver if fault == "mixed" else detector
            (root / name).write_bytes(subprocess.check_output([
                "git", "-C", str(ROOT), "show", "b6d598120:" + name
            ]))
        elif fault == "ordered_prior":
            (root / ordered).write_bytes(subprocess.check_output([
                "git", "-C", str(ROOT), "show", "b6d598120:" + ordered
            ]))
        elif fault == "ordered_unknown":
            (root / ordered).write_bytes(b"unreviewed stop admission\n")
        elif fault == "both_unknown":
            for name in originals:
                (root / name).write_bytes(b"unknown candidate generation\n")
        elif fault == "origin":
            old = "0" * 64
        assert C.reviewed_preparation_pair(detector, old, current, root=root) is (fault is None)
        if fault == "origin":
            assert (old, current) not in H.REVIEWED_POSTCLOSE_SCHEDULE_PAIRS[detector]
        elif fault is None:
            assert H._verify_entry_code_delta(
                root, release["commit"], release["original_commit"],
                release["paths"], release["expected"],
            ) == []
        else:
            expected_error = (
                "entry_consumer_code_source_missing:"
                if fault == "missing"
                else "entry_consumer_reviewed_dependency_unreviewed:"
            )
            with pytest.raises(ValueError, match=expected_error):
                H._verify_entry_code_delta(
                    root, release["commit"], release["original_commit"],
                    release["paths"], release["expected"],
                )
    finally:
        for name, raw in originals.items():
            (root / name).write_bytes(raw)


def test_reviewed_predecessor_composition_keeps_unknown_and_disconnected_edges_out():
    edges = {("a", "b"), ("b", "c"), ("x", "y"), ("b", "a")}
    assert C.reviewed_predecessor_origins("c", edges) == {"a", "b", "c"}
    assert C.reviewed_predecessor_origins("unknown", edges) == {"unknown"}
    name = "src/engine/monitoring/submission_bottleneck_monitor.py"
    current = C.REVIEWED_STORAGE_INTEGRATION_TRANSITION[name][1]
    origins = C.reviewed_storage_origins(name)
    assert C.REVIEWED_SUBMISSION_MONITOR_TRANSITION[name][0] in origins
    assert "f" * 64 not in origins
    assert all((H.reviewed_formatting_predecessor(name, old), current) in
               H.REVIEWED_STORAGE_INTEGRATION_PAIRS[name] for old in origins)


@pytest.mark.parametrize("fault", [None, "missing", "mixed", "origin", "future"])
@pytest.mark.parametrize("generation", ["prior", "integrated", "issued_health", "issued_mount", "issued_capability", "issued_native_plan", "issued_plan_history", "current"])
@pytest.mark.parametrize("consumer", ["changed", "unchanged_native"])
def test_storage_integration_requires_complete_profile(tmp_path, fault, generation, consumer):
    profile = (C.REVIEWED_STORAGE_INTEGRATION_PRIOR_PROFILE if generation == "prior"
               else C.REVIEWED_STORAGE_INTEGRATION_PROFILE if generation == "integrated"
               else C.REVIEWED_STORAGE_HEALTH_PROFILE if generation == "issued_health"
               else C.REVIEWED_STORAGE_MOUNT_PROFILE if generation == "issued_mount"
               else C.REVIEWED_STORAGE_CAPABILITY_PROFILE if generation == "issued_capability"
               else C.REVIEWED_STORAGE_NATIVE_PLAN_PROFILE if generation == "issued_native_plan"
               else C.REVIEWED_STORAGE_PLAN_HISTORY_PROFILE if generation == "issued_plan_history"
               else C.REVIEWED_STORAGE_ADMISSION_PROFILE)
    for name, expected in profile.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        revision = "f1648286c" if generation == "prior" else "2fe611daa" if generation == "issued_health" else "3deb89f38" if generation == "issued_mount" else "0ac79ed31" if generation == "issued_capability" else "f59cdc78e" if generation == "issued_native_plan" else "fbaa1d2ff" if generation == "issued_plan_history" else "9fb3f7198"
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", revision + ":" + name])
                         if generation != "current" else (ROOT / name).read_bytes())
        assert C._sha(path) == expected
    transition = (C.REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION if generation == "prior"
                  else C.REVIEWED_STORAGE_INTEGRATION_TRANSITION if generation == "integrated"
                  else C.REVIEWED_STORAGE_HEALTH_TRANSITION if generation == "issued_health"
                  else C.REVIEWED_STORAGE_MOUNT_TRANSITION if generation == "issued_mount"
                  else C.REVIEWED_STORAGE_CAPABILITY_TRANSITION if generation == "issued_capability"
                  else C.REVIEWED_STORAGE_NATIVE_PLAN_TRANSITION if generation == "issued_native_plan"
                  else C.REVIEWED_STORAGE_PLAN_HISTORY_TRANSITION if generation == "issued_plan_history"
                  else C.REVIEWED_STORAGE_ADMISSION_TRANSITION)
    name, (old, current) = next(iter(transition.items()))
    if consumer == "unchanged_native":
        name="src/engine/scalping/continuous_reversal_policy_v6.py"
        old=hashlib.sha256(subprocess.check_output(["git","-C",str(ROOT),"show","52425f68f:"+name])).hexdigest()
        current=profile[name]
    dependency = tmp_path / "src/engine/monitoring/sentinel_source_window.py"
    if fault == "missing":
        dependency.unlink()
    elif fault == "mixed":
        dependency.write_bytes(subprocess.check_output([
            "git", "-C", str(ROOT), "show", "23fbecf28:src/engine/monitoring/sentinel_source_window.py"
        ]))
    elif fault == "origin":
        old = "0" * 64
    elif fault == "future":
        current = "f" * 64
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)

@pytest.mark.parametrize("fault", [None, "missing", "mixed"])
def test_interrupted_prior_selected_generation_retains_native_reader(tmp_path, fault):
    for name, expected in C.REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "82ecab8fc:" + name]))
        assert C._sha(path) == expected
    name = "src/engine/automation/ordered_intraday_deploy.py"
    old = C.REVIEWED_INTERRUPTED_CUSTODY_TRANSITION[name][0]
    current = C.REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE[name]
    dependency = tmp_path / "src/engine/scalping/reversal_auxiliary_intraday.py"
    if fault == "missing": dependency.unlink()
    elif fault == "mixed": dependency.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "3e3d5da2c:src/engine/scalping/reversal_auxiliary_intraday.py"]))
    assert C.reviewed_preparation_pair(name, old, current, root=tmp_path) is (fault is None)


@pytest.mark.parametrize("relative", sorted(set(C.REVIEWED_POSTCLOSE_NATIVE_HOLD_DEPENDENCIES) | {
    "src/engine/scalping/reversal_code_handoff.py"}))
@pytest.mark.parametrize("fault", ["missing", "unknown"])
def test_native_hold_direct_dependencies_reach_both_code_readers(current_releases, relative, fault):
    release = current_releases
    root = release["root"]
    path = root / relative
    original = path.read_bytes()
    detector = "src/engine/error_detectors/artifact_freshness.py"
    old, current = C.REVIEWED_POSTCLOSE_SCHEDULE_TRANSITION[detector]
    try:
        if fault == "missing": path.unlink()
        else: path.write_bytes(b"unreviewed native hold dependency\n")
        assert not C.reviewed_preparation_pair(detector, old, current, root=root)
        expected = "entry_consumer_code_source_missing:" if fault == "missing" else "entry_consumer_reviewed_dependency_unreviewed:"
        with pytest.raises(ValueError, match=expected):
            H._verify_entry_code_delta(root,release["commit"],release["original_commit"],release["paths"],release["expected"])
    finally:
        path.write_bytes(original)
