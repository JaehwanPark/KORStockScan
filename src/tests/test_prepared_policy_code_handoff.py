"""Prepared code compatibility never supplies PREOPEN or PID authority."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from src.engine.automation import prepared_policy_code_handoff as C
from src.engine.automation import intraday_release_handoff as H
from src.engine.automation import ordered_intraday_deploy as O
from src.engine.infrastructure import runtime_release_router as R

DAY = "2026-10-19"
COMMIT = "b" * 40
ORIGIN = "a" * 40
NOW = datetime(2026, 10, 17, 12, tzinfo=ZoneInfo("Asia/Seoul"))
HISTORICAL_PREPARATION_COMMIT = "a8f063105bbb1d8a3676e55ad5377990a87594df"
REVIEWED_AVG_DOWN_INPUT_COMMIT = "deb996a22689ac08e171ea38966d070d63d236ee"


@pytest.fixture
def prepared(tmp_path, monkeypatch, request):
    family = getattr(request, "param", "pre_submit_delay")
    complete = family == "complete"
    if complete:
        family = "pre_submit_delay"
    data = tmp_path / "data"
    data.mkdir()
    root = tmp_path / "release"
    root.mkdir()
    source = root / "consumer.py"
    source.write_text("reviewed code\n")
    policy = data / "policy.json"
    policy.write_text("{}")
    paths = {"consumer.py": "consumer.py"}
    actual = C._digest({"consumer.py": C._sha(source)})

    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value))
        return path

    env = tmp_path / "env"
    env.write_text("export TEST=true\n")
    manifest = {
        "target_date": DAY,
        "selected_release_sha": ORIGIN,
        C.FAMILIES[family][0]: {"target_date": DAY, C.FAMILIES[family][1]: "policy"},
    }
    if complete:
        manifest.update(
            {
                name: {"target_date": DAY, key: "policy"}
                for name, key in C.FAMILIES.values()
            }
        )
    manifest["manifest_sha256"] = C._digest(manifest)
    mp = write("manifest.json", manifest)
    vp = write(
        "verify.json",
        {
            "status": "pass",
            "findings": [],
            "manifest_sha256": manifest["manifest_sha256"],
        },
    )
    controller = write("controller.json", {"status": "done"})
    summary = write("summary.json", {"date": "2026-10-16"})
    body = dict(
        schema="next_preopen_readiness_v1",
        status="prepared_verified",
        target_date=DAY,
        selected_release_commit=ORIGIN,
        actual_pid_consumed=False,
        runtime_effect=False,
        policy_receipts=[],
    )
    for field, digest, path in [
        ("manifest_path", "manifest_file_sha256", mp),
        ("env_path", "env_sha256", env),
        ("verification_path", "verification_sha256", vp),
        ("controller_path", "controller_sha256", controller),
        ("summary_path", "summary_sha256", summary),
    ]:
        body[field] = str(path)
        body[digest] = C._sha(path)
    pp = write("prepared.json", body)
    monkeypatch.setattr(C, "_clock", lambda day, now=None: None)
    monkeypatch.setattr(C, "_policy", lambda *a: (policy, "expected"))
    monkeypatch.setattr(H, "_verify_entry_code_delta", lambda *a: ["consumer.py"])
    monkeypatch.setattr(R, "selected_release", lambda *a: (root, COMMIT))
    monkeypatch.setattr(R, "validate_release", lambda *a: (root, COMMIT))
    monkeypatch.setattr(O, "_main_pids", lambda: [])
    monkeypatch.setattr(O, "_session_absent", lambda: True)
    import subprocess

    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: COMMIT + "\n")
    args = dict(family=family, policy_sha="policy", expected="expected", paths=paths)
    receipt = C.issue(
        data,
        DAY,
        **args,
        release_root=root,
        prepared_receipt=pp,
        origin_verification=vp,
        confirm=C.AUTHORITY,
    )
    return data, root, args, actual, receipt, pp


def test_future_and_target_day_proof_preserves_policy_without_pid(prepared):
    data, root, args, actual, receipt, pp = prepared
    before = pp.read_bytes()
    proof = C.verify(data, DAY, **args, actual=actual)
    assert proof["verification_basis"] == C.SCHEMA
    assert (
        proof["policy_effect"] == "unchanged" and proof["actual_pid_consumed"] is False
    )
    assert pp.read_bytes() == before


@pytest.mark.parametrize(
    "prepared", ["pre_submit_delay", "holding_vote", "main_stop"], indirect=True
)
@pytest.mark.parametrize(
    "fault", [None, "review", "source", "actual", "unreviewed", "selection_race"]
)
def test_prepared_predecessor_and_candidate_keep_separate_native_code_identities(
    prepared, monkeypatch, fault
):
    data, root, args, actual, receipt, pp = prepared
    candidate = root.parent / "candidate"
    (candidate / "src/engine/automation").mkdir(parents=True)
    own = candidate / "src/engine/automation/intraday_release_handoff.py"
    own.write_text("# fixture owner\n")
    source = candidate / "consumer.py"
    source.write_text("reviewed successor code\n")
    selector = data / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(exist_ok=True)
    selector.write_text('{"selected":"original"}')
    monkeypatch.setattr(H, "__file__", str(own))
    monkeypatch.setattr(H, "DATA_DIR", data)
    monkeypatch.setattr(H, "_selection", lambda **kw: (root, COMMIT))
    monkeypatch.setattr(H, "predecessor_review_matches", lambda *a: fault != "review")
    review = dict(code_root=candidate, code_commit="c" * 40)
    native_delta = H._verify_entry_code_delta

    def delta(code_root, *rest):
        if code_root == candidate and fault == "unreviewed":
            raise ValueError("unreviewed_candidate")
        return native_delta(code_root, *rest)

    monkeypatch.setattr(H, "_verify_entry_code_delta", delta)
    original_resolve = C.resolve_prepared_code_origin

    def resolve(*a, **kw):
        value = original_resolve(*a, **kw)
        if fault == "selection_race":
            selector.write_text('{"selected":"foreign"}')
        return value

    monkeypatch.setattr(C, "resolve_prepared_code_origin", resolve)
    if fault == "source":
        (data / "policy.json").write_text('{"changed":true}')
    new_actual = C._digest({"consumer.py": C._sha(source)})
    if fault == "actual":
        new_actual = "d" * 64
    token = H._PREDECESSOR_REVIEW.set(review)
    try:
        if fault:
            with pytest.raises(ValueError):
                H.verify_entry_consumer_code(DAY, **args, actual=new_actual)
        else:
            before = pp.read_bytes()
            proof = H.verify_entry_consumer_code(DAY, **args, actual=new_actual)
            assert (
                proof["verification_basis"]
                == "verified_prepared_predecessor_consumer_repair"
            )
            assert (
                proof["release_commit"] == "c" * 40 and proof["origin_commit"] == ORIGIN
            )
            assert proof["actual_pid_consumed"] is False and pp.read_bytes() == before
            assert (
                C.verify(data, DAY, **args, actual=actual)["release_commit"] == COMMIT
            )
    finally:
        H._PREDECESSOR_REVIEW.reset(token)


@pytest.mark.parametrize(
    "fault", ["runtime", "policy", "expected", "source", "receipt", "origin", "symlink"]
)
def test_invalid_binding_never_uses_prepared_code_authority(prepared, fault):
    data, root, args, actual, receipt, pp = prepared
    args = dict(args)
    if fault == "runtime":
        (root / "consumer.py").write_text("changed")
    elif fault == "policy":
        args["policy_sha"] = "different"
    elif fault == "expected":
        args["expected"] = "different"
    elif fault == "source":
        (data / "policy.json").write_text('{"changed":true}')
    elif fault == "origin":
        Path(receipt["historical_snapshots"][str(pp)]).write_text("changed")
    else:
        path = C.receipt_path(data, DAY, COMMIT, "pre_submit_delay")
        if fault == "receipt":
            receipt["actual_pid_consumed"] = True
            receipt["receipt_sha256"] = C._digest(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"}
            )
            path.write_text(json.dumps(receipt))
        else:
            target = path.with_suffix(".saved")
            path.rename(target)
            path.symlink_to(target)
    with pytest.raises(ValueError):
        C.verify(data, DAY, **args, actual=actual)


@pytest.mark.parametrize(
    "prepared", ["pre_submit_delay", "main_stop", "holding_vote"], indirect=True
)
@pytest.mark.parametrize(
    "fault", [None, "target", "custody", "source", "code", "scope_entry", "scope_exit"]
)
def test_stopped_workflow_consumer_binds_observation_and_prepared_dates(
    prepared, monkeypatch, fault
):
    from contextlib import contextmanager

    data, root, args, actual, receipt, pp = prepared
    candidate = root.parent / "candidate"
    (candidate / "src/engine/automation").mkdir(parents=True)
    own = candidate / "src/engine/automation/intraday_release_handoff.py"
    own.write_text("# fixture owner\n")
    (candidate / "consumer.py").write_text("reviewed successor code\n")
    selector = data / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(exist_ok=True)
    selector.write_text(
        json.dumps(
            dict(
                release_root=str(root),
                main_start_authorized=False,
                approval_scope="after_postclose_deploy_for_next_regular_start",
            )
        )
    )
    monkeypatch.setattr(H, "__file__", str(own))
    monkeypatch.setattr(H, "DATA_DIR", data)
    monkeypatch.setattr(H, "_selection", lambda **kw: (root, COMMIT))
    observation_day = datetime.now(H.KST).date().isoformat()
    review = dict(
        day=observation_day,
        code_root=candidate,
        code_commit="c" * 40,
        postclose_observation=dict(
            prepared_target_date="wrong" if fault == "target" else DAY
        ),
    )
    calls = []

    @contextmanager
    def stopped(day):
        calls.append(day)
        if fault == "scope_entry":
            raise ValueError("invalid_native_cold_custody")
        token = H._PREDECESSOR_REVIEW.set(review)
        try:
            yield
            if fault == "scope_exit":
                raise ValueError("native_cold_source_changed")
        finally:
            H._PREDECESSOR_REVIEW.reset(token)

    monkeypatch.setattr(H, "stopped_postclose_review", stopped)
    monkeypatch.setattr(
        H,
        "predecessor_review_matches",
        lambda r, day, *a: r is review
        and day == observation_day
        and fault != "custody",
    )
    if fault == "source":
        (data / "policy.json").write_text('{"changed":true}')
    index = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    native_prepared = index.parent / "fixture-generation/readiness.json"
    native_prepared.parent.mkdir(parents=True)
    native_prepared.write_bytes(pp.read_bytes())
    index.write_text(json.dumps(dict(target_date=DAY, receipt_path=str(native_prepared),
        receipt_sha256=C._sha(native_prepared))))
    candidate_actual = C._digest({"consumer.py": C._sha(candidate / "consumer.py")})
    if fault == "code":
        candidate_actual = "d" * 64
    before = {
        p: p.read_bytes()
        for p in (pp, selector, C.receipt_path(data, DAY, COMMIT, args["family"]))
    }
    if fault:
        with pytest.raises(ValueError):
            H.verify_entry_consumer_code(DAY, **args, actual=candidate_actual)
    else:
        proof = H.verify_entry_consumer_code(DAY, **args, actual=candidate_actual)
        assert proof["release_commit"] == "c" * 40
        assert proof["target_date"] == DAY and proof["actual_pid_consumed"] is False
    assert calls == [DAY] and H._PREDECESSOR_REVIEW.get() is None
    assert all(p.read_bytes() == raw for p, raw in before.items())


def test_missing_receipt_keeps_ordinary_native_path(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "selected_release", lambda *a: (tmp_path, COMMIT))
    assert (
        C.verify(
            tmp_path,
            DAY,
            family="main_stop",
            policy_sha="x",
            expected="x",
            paths={},
            actual="x",
        )
        is None
    )


@pytest.mark.parametrize("prepared", ["complete"], indirect=True)
@pytest.mark.parametrize(
    "fault",
    [None, "unselected", "handoff", "policy", "changed_source", "selection_race"],
)
def test_ordered_selected_issuance_reaches_native_consumers_without_callback(
    prepared, monkeypatch, fault
):
    from contextlib import nullcontext
    from src.engine.scalping import main_stop_policy as S, holding_vote_experiment as V
    from src.engine.scalping import pre_submit_delay_initial_policy as L

    data, root, args, _, _, pp = prepared
    (data / "runtime").mkdir(exist_ok=True)
    selector = data / "runtime/runtime_release_selection.json"
    selector.write_text("{}")
    native = root / "src/engine/consumer.py"
    native.parent.mkdir(parents=True)
    native.write_bytes((root / "consumer.py").read_bytes())
    monkeypatch.setattr(S, "implementation_paths", lambda: {"consumer.py": native})
    monkeypatch.setattr(V, "_code_paths", lambda: {"consumer.py": native})
    monkeypatch.setattr(L, "CONTRACT_PATHS", {"consumer.py": root / "consumer.py"})
    monkeypatch.setattr(O, "_existing_selector_lock", lambda _: nullcontext())
    monkeypatch.setattr(
        H,
        "_verify_handoff",
        lambda *a: dict(
            status="pass", findings=[], handoff={"prepared_receipt_path": str(pp)}
        ),
    )
    if fault == "unselected":
        monkeypatch.setattr(R, "selected_release", lambda _: (root.parent, COMMIT))
    if fault == "handoff":
        monkeypatch.setattr(
            H, "_verify_handoff", lambda *a: {"status": "fail", "findings": ["expired"]}
        )
    if fault == "policy":
        monkeypatch.setattr(C, "_policy", lambda *a: (data / "policy.json", "wrong"))
    if fault == "changed_source":
        (data / "policy.json").write_text('{"changed":true}')
    if fault == "selection_race":
        original = C.issue

        def mutate(*a, **kw):
            result = original(*a, **kw)
            selector.write_text('{"changed":true}')
            return result

        monkeypatch.setattr(C, "issue", mutate)
    original_prepared = pp.read_bytes()
    if fault:
        with pytest.raises(ValueError):
            C.issue_selected(data, DAY, release_root=root)
    else:
        issued = C.issue_selected(data, DAY, release_root=root)
        assert {row["family"] for row in issued} == set(C.FAMILIES)
        original = {
            row["path"]: (
                Path(row["path"]).read_bytes(),
                Path(row["path"]).stat().st_mtime_ns,
            )
            for row in issued
        }
        assert C.issue_selected(data, DAY, release_root=root) == issued
        assert all(
            (Path(path).read_bytes(), Path(path).stat().st_mtime_ns) == before
            for path, before in original.items()
        )
        for row in issued:
            body = C._read(row["path"])
            proof = C.verify(
                data,
                DAY,
                family=row["family"],
                policy_sha="policy",
                expected="expected",
                paths=body["paths"],
                actual=body["runtime_code_sha256"],
            )
            assert (
                proof["actual_pid_consumed"] is False
                and proof["policy_effect"] == "unchanged"
            )
    assert pp.read_bytes() == original_prepared


@pytest.mark.parametrize(
    "fault", [None, "unselected", "frozen_source", "policy", "origin", "selection_race"]
)
def test_successive_issue_uses_selected_frozen_origin_without_rewriting_aliases(
    prepared, monkeypatch, fault
):
    import subprocess

    data, old_root, args, actual, previous, pp = prepared
    new_root = old_root.with_name("successor")
    new_root.mkdir()
    (new_root / "consumer.py").write_bytes((old_root / "consumer.py").read_bytes())
    new_commit = "c" * 40
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: new_commit + "\n")
    previous_path = C.receipt_path(data, DAY, COMMIT, args["family"])
    original = C._read(pp)
    controller = Path(original["controller_path"])
    controller.write_text('{"status":"new current generation"}')
    before = {
        p: p.read_bytes() for p in (pp, controller, previous_path, data / "policy.json")
    }
    passed_previous = previous_path
    if fault == "unselected":
        passed_previous = previous_path.with_name("other.json")
    elif fault == "frozen_source":
        Path(previous["historical_snapshots"][str(controller)]).write_text("tampered")
    elif fault == "policy":
        (data / "policy.json").write_text('{"changed":true}')
    elif fault == "origin":
        pp = pp.with_name("unrelated-prepared.json")
    elif fault == "selection_race":
        count = 0

        def selected(*a):
            nonlocal count
            count += 1
            return (old_root, COMMIT) if count < 3 else (new_root, new_commit)

        monkeypatch.setattr(R, "selected_release", selected)

    def issue():
        return C.issue(
            data,
            DAY,
            **args,
            release_root=new_root,
            prepared_receipt=pp,
            origin_verification=Path(original["verification_path"]),
            confirm=C.AUTHORITY,
            previous_handoff=passed_previous,
        )

    if fault:
        with pytest.raises((ValueError, OSError, KeyError)):
            issue()
        assert not C.receipt_path(data, DAY, new_commit, args["family"]).exists()
    else:
        receipt = issue()
        assert receipt["origin_commit"] == ORIGIN
        assert receipt["previous_handoff"]["sha256"] == C._sha(previous_path)
        assert all(p.read_bytes() == raw for p, raw in before.items())
        monkeypatch.setattr(R, "selected_release", lambda *a: (new_root, new_commit))
        assert (
            C.verify(data, DAY, **args, actual=actual)["policy_effect"] == "unchanged"
        )


def test_target_expiry_is_not_renewed():
    C._clock(DAY, NOW)
    C._clock(DAY, NOW.replace(day=19))
    with pytest.raises(ValueError, match="expired"):
        C._clock(DAY, NOW.replace(day=20))


def test_origin_rejects_modified_prepared_hashes(prepared):
    data, root, args, actual, receipt, pp = prepared
    body = json.loads(pp.read_text())
    body["manifest_file_sha256"] = "0" * 64
    pp.write_text(json.dumps(body))
    with pytest.raises(ValueError):
        C._origin(pp, args["family"], DAY)


def test_original_closure_can_advance_without_rewriting_historical_authority(prepared):
    data, root, args, actual, receipt, pp = prepared
    body = json.loads(pp.read_text())
    Path(body["controller_path"]).write_text('{"status":"new generation"}')
    assert C.verify(data, DAY, **args, actual=actual)["actual_pid_consumed"] is False
    # The current policy remains independently pinned despite historical retention.
    (data / "policy.json").write_text('{"different":true}')
    with pytest.raises(ValueError):
        C.verify(data, DAY, **args, actual=actual)


def test_native_code_inventory_accepts_utils_paths_and_rejects_escape(tmp_path):
    import subprocess
    import hashlib

    root = tmp_path / "repo"
    root.mkdir()
    own = root / "src/engine/automation/intraday_release_handoff.py"
    own.parent.mkdir(parents=True)
    own.write_bytes(Path(H.__file__).read_bytes())
    utility = root / "src/utils/market_day.py"
    utility.parent.mkdir()
    utility.write_text("value = 1\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    expected = C._digest(
        {"market_day": hashlib.sha256(utility.read_bytes()).hexdigest()}
    )
    assert (
        H._verify_entry_code_delta(
            root,
            commit,
            commit,
            {"market_day": "src/engine/../utils/market_day.py"},
            expected,
        )
        == []
    )
    (tmp_path / "outside.py").write_text("private fixture\n")
    with pytest.raises(ValueError, match="outside_release"):
        H._verify_entry_code_delta(
            root, commit, commit, {"outside": "../outside.py"}, expected
        )


@pytest.mark.parametrize(
    "family,expected",
    [
        (
            "pre_submit_delay",
            "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
        ),
        (
            "holding_vote",
            "6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112",
        ),
        (
            "main_stop",
            "687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533",
        ),
    ],
)
def test_delay_research_exact_original_policy_inventory_is_preserved(
    tmp_path, monkeypatch, family, expected
):
    """Bind reviewed bytes to the real frozen origin, without issuing a receipt."""
    import hashlib
    import os
    from src.engine.scalping import pre_submit_delay_initial_policy as delay
    from src.engine.scalping import holding_vote_experiment as holding
    from src.engine.scalping import main_stop_policy as stop

    canonical = Path(H.__file__).resolve().parents[3]
    root = tmp_path / "reviewed_source"
    origin = "7f2552aedde8fec6ef904a43105827907e50dfc8"
    candidate = "b" * 40
    paths = (
        {name: name for name in delay.CONTRACT_PATHS}
        if family == "pre_submit_delay"
        else {
            name: "src/engine/" + name
            for name in (
                holding._code_paths()
                if family == "holding_vote"
                else stop.implementation_paths()
            )
        }
    )
    real_git = H.subprocess.check_output
    trigger = "src/engine/sniper_state_handlers.py"
    variant = H.REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS[
        (trigger, H.REVIEWED_AVG_DOWN_INPUT_HASHES[trigger])
    ]
    # An issued generation must not silently follow the current working tree.
    for name in set(paths.values()) | set(variant["dependencies"]):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            real_git(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "show",
                    REVIEWED_AVG_DOWN_INPUT_COMMIT + ":" + os.path.normpath(name),
                ]
            )
        )
    for name in {
        v["selector_path"]
        for key, variants in vars(H).items()
        if key.endswith("_DEPENDENCY_VARIANTS") and isinstance(variants, dict)
        for (owner, sha), v in variants.items()
        if (owner, sha) == (trigger, H.REVIEWED_AVG_DOWN_INPUT_HASHES[trigger])
    }:
        result = H.subprocess.run(
            [
                "git",
                "-C",
                str(canonical),
                "show",
                REVIEWED_AVG_DOWN_INPUT_COMMIT + ":" + name,
            ],
            capture_output=True,
        )
        if result.returncode == 0 and not (root / name).exists():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_bytes(result.stdout)
    own = root / "src/engine/automation/intraday_release_handoff.py"
    own.write_bytes(Path(H.__file__).read_bytes())

    def fixture_revision(command, **kwargs):
        revision, name = command[-1].split(":", 1)
        return (
            (root / name).read_bytes()
            if revision == candidate
            else real_git(["git", "-C", str(canonical), "show", command[-1]], **kwargs)
        )

    monkeypatch.setattr(H.subprocess, "check_output", fixture_revision)
    before = {name: (root / name).read_bytes() for name in paths.values()}
    changed = H._verify_entry_code_delta(root, candidate, origin, paths, expected)
    assert "src/engine/sniper_state_handlers.py" in changed
    assert before == {name: (root / name).read_bytes() for name in paths.values()}
    if family == "pre_submit_delay":
        extensions = H.REVIEWED_DELAY_CONTRACT_EXTENSIONS[(origin, expected)]
        assert set(extensions) == {
            "src/engine/pipeline_event_summary.py",
            "src/utils/threshold_cycle_registry.py",
            "src/engine/infrastructure/main_policy_loading.py",
        }
        # The original 59-source generation retains its original extension.
        # Reviewed AVG_DOWN input has its own complete dependency generation;
        # never relabel current working bytes as that historical source.
        assert all(
            hashlib.sha256(
                real_git(
                    [
                        "git",
                        "-C",
                        str(canonical),
                        "show",
                        HISTORICAL_PREPARATION_COMMIT + ":" + name,
                    ]
                )
            ).hexdigest()
            == digest
            for name, digest in extensions.items()
        )
        assert H._sha(root / variant["selector_path"]) == variant["selector_sha256"]
        current_extensions = variant["contract_extensions"][(origin, expected)]
        assert set(current_extensions) >= set(extensions)
        assert all(
            hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
            for name, digest in current_extensions.items()
        )
        for name, pair in H.REVIEWED_DELAY_RESEARCH_SOURCES.items():
            prior = real_git(["git", "-C", str(canonical), "show", origin + ":" + name])
            assert pair[0] == hashlib.sha256(prior).hexdigest()


def _origin_resolution_arguments(prepared):
    data, root, args, actual, receipt, pp = prepared
    selector = data / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(parents=True, exist_ok=True)
    selector.write_text('{"fixture_selection":"unchanged"}\n')
    return (
        data,
        root,
        {**args, "selected_root": root, "selected_commit": COMMIT},
        selector,
    )


def test_resolve_selected_exact_code_origin_without_new_handoff(prepared, monkeypatch):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    args["expected"] = prepared[3]

    def forbidden_verify(*args, **kwargs):
        pytest.fail("exact selected code must not require a predecessor handoff")

    monkeypatch.setattr(C, "verify", forbidden_verify)
    before = selector.read_bytes()
    result = C.resolve_prepared_code_origin(data, DAY, **args)
    assert result["origin_commit"] == COMMIT
    assert result["basis"] == "selected_exact_code_contract"
    assert result["sources"][str(selector)] == C._sha(selector)
    assert result["sources"][str(root / "consumer.py")] == C._sha(root / "consumer.py")
    assert result["selected_paths"] == args["paths"]
    assert selector.read_bytes() == before


def test_resolve_selected_handoff_keeps_original_frozen_origin_and_sources(prepared):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    before = {str(p): p.read_bytes() for p in data.rglob("*") if p.is_file()}
    result = C.resolve_prepared_code_origin(data, DAY, **args)
    receipt = C.receipt_path(data, DAY, COMMIT, args["family"])
    assert result["origin_commit"] == ORIGIN != COMMIT
    assert result["basis"] == "verified_selected_prepared_code_handoff"
    assert result["code_handoff_receipt_path"] == str(receipt)
    assert result["sources"][str(receipt)] == C._sha(receipt)
    assert result["sources"].items() >= prepared[4]["sources"].items()
    assert before == {str(p): p.read_bytes() for p in data.rglob("*") if p.is_file()}


def test_resolve_origin_authenticates_issued_inventory_before_known_new_extension(
    prepared, monkeypatch
):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    addition = "new_startup_consumer.py"
    monkeypatch.setitem(
        H.REVIEWED_DELAY_CONTRACT_EXTENSIONS,
        (ORIGIN, args["expected"]),
        {addition: "d" * 64},
    )
    args["paths"] = {**args["paths"], addition: addition}
    assert not (root / addition).exists()  # The selected old release lacks it.
    result = C.resolve_prepared_code_origin(data, DAY, **args)
    assert result["origin_commit"] == ORIGIN
    assert result["selected_paths"] == prepared[2]["paths"]
    assert result["selected_runtime_code_sha256"] == prepared[3]
    assert result["reviewed_extension_hashes"] == {addition: "d" * 64}


@pytest.mark.parametrize("fault", ["unknown", "missing"])
def test_resolve_origin_rejects_unknown_or_omitted_inventory_extension(
    prepared, monkeypatch, fault
):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    addition = "new_startup_consumer.py"
    monkeypatch.setitem(
        H.REVIEWED_DELAY_CONTRACT_EXTENSIONS,
        (ORIGIN, args["expected"]),
        {addition: "d" * 64},
    )
    if fault == "unknown":
        args["paths"] = {
            **args["paths"],
            addition: addition,
            "unreviewed.py": "unreviewed.py",
        }
    with pytest.raises(ValueError, match="inventory_extension_unreviewed"):
        C.resolve_prepared_code_origin(data, DAY, **args)


@pytest.mark.parametrize(
    "fault", ["selected_commit", "policy", "frozen_source", "receipt", "selected_code"]
)
def test_resolve_origin_rejects_changed_or_unbound_selected_handoff(prepared, fault):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    if fault == "selected_commit":
        args["selected_commit"] = "c" * 40
    elif fault == "policy":
        args["policy_sha"] = "another-policy"
    elif fault == "selected_code":
        (root / "consumer.py").write_text("unreviewed changed source\n")
    elif fault == "frozen_source":
        frozen = next(iter(prepared[4]["sources"]))
        Path(frozen).write_text("changed original evidence\n")
    else:
        C.receipt_path(data, DAY, COMMIT, args["family"]).unlink()
    with pytest.raises(ValueError):
        C.resolve_prepared_code_origin(data, DAY, **args)


def test_resolve_origin_rejects_selector_change_during_native_verification(
    prepared, monkeypatch
):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    native_verify = C.verify

    def changed_selection(*args, **kwargs):
        result = native_verify(*args, **kwargs)
        selector.write_text('{"fixture_selection":"different_generation"}\n')
        return result

    monkeypatch.setattr(C, "verify", changed_selection)
    with pytest.raises(ValueError, match="prepared_code_origin_sources_changed"):
        C.resolve_prepared_code_origin(data, DAY, **args)


@pytest.mark.parametrize(
    "generation",
    ["historical_preparation", "issued_startup", "reviewed_avg_down_input"],
)
def test_new_startup_handoff_accepts_only_exact_reviewed_delay_source_pair(
    tmp_path, monkeypatch, generation
):
    import hashlib
    import os
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS

    canonical = Path(H.__file__).resolve().parents[3]
    fixture = tmp_path / "code"
    own = "src/engine/automation/intraday_release_handoff.py"
    real_git = H.subprocess.check_output
    trigger = "src/engine/sniper_state_handlers.py"
    source_commit = {
        "issued_startup": "958d35b2b03f0a37462c1c0121fc14c108e709b8",
        "historical_preparation": HISTORICAL_PREPARATION_COMMIT,
        "reviewed_avg_down_input": REVIEWED_AVG_DOWN_INPUT_COMMIT,
    }[generation]
    trigger_sha = hashlib.sha256(
        real_git(["git", "-C", str(canonical), "show", source_commit + ":" + trigger])
    ).hexdigest()
    dependencies = (
        {}
        if generation == "reviewed_avg_down_input"
        else H.REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[trigger][trigger_sha]
    )
    if generation in {"issued_startup", "reviewed_avg_down_input"}:
        variants = (
            H.REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS
            if generation == "reviewed_avg_down_input"
            else H.REVIEWED_DELAY_PARENT_VERIFICATION_DEPENDENCY_VARIANTS
        )
        variant = variants[(trigger, trigger_sha)]
        dependencies = variant["dependencies"]
    if generation == "reviewed_avg_down_input":
        assert set(dependencies) >= set(H.REVIEWED_AVG_DOWN_INPUT_HASHES)
    else:
        assert len(dependencies) == (
            59 if generation == "historical_preparation" else 76
        )
    for name in (*CONTRACT_PATHS, own, *dependencies):
        destination = fixture / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = (
            (canonical / name).read_bytes()
            if name == own
            else real_git(
                [
                    "git",
                    "-C",
                    str(canonical),
                    "show",
                    source_commit + ":" + os.path.normpath(name),
                ]
            )
        )
        destination.write_bytes(raw)
        if name in dependencies:
            assert hashlib.sha256(raw).hexdigest() == dependencies[name]
    origin = "7f2552aedde8fec6ef904a43105827907e50dfc8"
    # Keep original selector modules that the real frozen Git tree owns.
    # Their old bytes select the historical closure rather than a later one.
    for name in {
        v["selector_path"]
        for key, variants in vars(H).items()
        if key.endswith("_DEPENDENCY_VARIANTS") and isinstance(variants, dict)
        for (owner, sha), v in variants.items()
        if (owner, sha) == (trigger, trigger_sha)
    }:
        result = H.subprocess.run(
            ["git", "-C", str(canonical), "show", source_commit + ":" + name],
            capture_output=True,
        )
        if result.returncode == 0 and not (fixture / name).exists():
            (fixture / name).parent.mkdir(parents=True, exist_ok=True)
            (fixture / name).write_bytes(result.stdout)
    H.subprocess.run(["git", "init", "-q", str(fixture)], check=True)

    def commit():
        H.subprocess.run(["git", "-C", str(fixture), "add", "."], check=True)
        H.subprocess.run(
            [
                "git",
                "-C",
                str(fixture),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "exact private source generation",
            ],
            check=True,
        )
        return real_git(
            ["git", "-C", str(fixture), "rev-parse", "HEAD"], text=True
        ).strip()

    candidate = commit()

    def revision(command, **kwargs):
        rev, name = command[-1].split(":", 1)
        if rev == origin:
            return real_git(
                ["git", "-C", str(canonical), "show", rev + ":" + name], **kwargs
            )
        return real_git(command, **kwargs)

    monkeypatch.setattr(H.subprocess, "check_output", revision)
    paths = {name: name for name in CONTRACT_PATHS}
    expected = "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256"
    changed = H._verify_entry_code_delta(fixture, candidate, origin, paths, expected)
    assert set(H.REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES).issubset(changed)
    for name, pair in H.REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES.items():
        final_pair = H.REVIEWED_RESEARCH_BUDGET_INTEGRATION_SOURCES.get(
            name, H.REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES.get(name, pair)
        )
        expected_sha = (
            variant["dependencies"].get(name, final_pair[1])
            if generation == "reviewed_avg_down_input"
            else final_pair[1]
        )
        assert hashlib.sha256((fixture / name).read_bytes()).hexdigest() == expected_sha
    if generation == "reviewed_avg_down_input":
        assert H._sha(fixture / variant["selector_path"]) == variant["selector_sha256"]
        for name in (
            "src/engine/sniper_execution_receipts.py",
            "src/engine/lifecycle/holding_research_cost.py",
            "src/engine/automation/main_trailing_source_assembler.py",
            "src/engine/infrastructure/startup_validation_code_context.py",
            "src/engine/scalping/reversal_auxiliary_next_session.py",
            "src/engine/scalping/reversal_auxiliary_source_handoff.py",
        ):
            dependency = fixture / name
            original_dependency = dependency.read_bytes()
            dependency.write_bytes(
                original_dependency + b"\nUNREVIEWED_STOPPED_CARRY = True\n"
            )
            candidate = commit()
            with pytest.raises(ValueError, match="reviewed_dependency_unreviewed"):
                H._verify_entry_code_delta(fixture, candidate, origin, paths, expected)
            dependency.write_bytes(original_dependency)
            candidate = commit()
    # Commit each unknown replacement to its real private Git object, so the
    # rejection remains source-contract validation rather than a dirty tree.
    unknown = fixture / "src/engine/scalping/pre_submit_delay_tuning.py"
    original = unknown.read_bytes()
    unknown.write_text(unknown.read_text() + "\nUNKNOWN_STARTUP_CHANGE = True\n")
    candidate = commit()
    with pytest.raises(ValueError, match="entry_consumer_unreviewed_change"):
        H._verify_entry_code_delta(fixture, candidate, origin, paths, expected)
    unknown.write_bytes(original)
    new_helper = fixture / "src/engine/infrastructure/main_policy_loading.py"
    new_helper.write_text(new_helper.read_text() + "\nUNKNOWN_HELPER_CHANGE = True\n")
    candidate = commit()
    with pytest.raises(
        ValueError, match="entry_consumer_contract_extension_unreviewed"
    ):
        H._verify_entry_code_delta(fixture, candidate, origin, paths, expected)


@pytest.mark.parametrize("prepared", ["main_stop", "holding_vote"], indirect=True)
@pytest.mark.parametrize(
    "addition,key",
    [
        ("src/engine/../utils/new_source.py", "../utils/new_source.py"),
        (
            "src/engine/lifecycle/research_input_budget.py",
            "lifecycle/research_input_budget.py",
        ),
    ],
)
@pytest.mark.parametrize(
    "fault",
    [
        None,
        "missing",
        "extra",
        "full_key",
        "normalized_key",
        "bad_extension_prefix",
        "other_family",
    ],
)
def test_engine_relative_extension_preserves_native_family_keys(
    prepared, monkeypatch, fault, addition, key
):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    extensions = {addition: "d" * 64}
    monkeypatch.setitem(
        H.REVIEWED_DELAY_CONTRACT_EXTENSIONS, (ORIGIN, args["expected"]), extensions
    )
    args["paths"] = {**args["paths"], key: addition}
    if fault == "missing":
        args["paths"].pop(key)
    elif fault == "extra":
        args["paths"]["unreviewed.py"] = "src/engine/unreviewed.py"
    elif fault == "full_key":
        args["paths"] = {"consumer.py": "consumer.py", addition: addition}
    elif fault == "normalized_key":
        import os

        args["paths"] = {
            "consumer.py": "consumer.py",
            os.path.normpath(addition): addition,
        }
    elif fault == "bad_extension_prefix":
        monkeypatch.setitem(
            H.REVIEWED_DELAY_CONTRACT_EXTENSIONS,
            (ORIGIN, args["expected"]),
            {"src/utils/new_source.py": "d" * 64},
        )
    elif fault == "other_family":
        args["family"] = "pre_submit_delay"
    before = {str(p): p.read_bytes() for p in data.rglob("*") if p.is_file()}
    if fault:
        with pytest.raises(ValueError):
            C.resolve_prepared_code_origin(data, DAY, **args)
    else:
        result = C.resolve_prepared_code_origin(data, DAY, **args)
        assert result["selected_paths"] == prepared[2]["paths"]
        assert result["reviewed_extension_hashes"] == extensions
        assert result["original_code_sha256"] == args["expected"]
    assert before == {str(p): p.read_bytes() for p in data.rglob("*") if p.is_file()}


@pytest.mark.parametrize("prepared", ["main_stop", "holding_vote"], indirect=True)
@pytest.mark.parametrize("fault", [None, "custody", "policy", "pid", "frozen_source"])
@pytest.mark.parametrize("closed", [False, True])
def test_resolve_live_intraday_origin_preserves_native_custody(
    prepared, monkeypatch, fault, closed
):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    C.receipt_path(data, DAY, COMMIT, args["family"]).unlink()
    manifest_path = Path(json.loads(prepared[-1].read_text())["manifest_path"])
    manifest = json.loads(manifest_path.read_text())
    identity = dict(pid=123, start_ticks="456", cwd=str(root / "src"))
    hp, cp = data / "handoff.json", data / "consumed.json"
    handoff = dict(frozen_files={str(manifest_path): C._sha(manifest_path)})
    hp.write_text(json.dumps(handoff))
    cp.write_text(
        json.dumps(
            dict(pid_identity=identity, manifest_sha256=manifest["manifest_sha256"])
        )
    )
    monkeypatch.setattr(
        H,
        "_verify_consumed_handoff",
        lambda *a: dict(
            status="fail" if closed or fault == "custody" else "pass", handoff=handoff
        ),
    )
    proof = dict(
        pid_identity=(
            {**identity, "start_ticks": "999"} if fault == "pid" else identity
        ),
        source_hashes={str(manifest_path): C._sha(manifest_path)},
    )

    def closed_proof(*a):
        if not closed or fault == "custody":
            raise ValueError("closed_custody_invalid")
        return proof

    monkeypatch.setattr(H, "closed_consumption_observation", closed_proof)
    monkeypatch.setattr(
        H, "_verify_handoff", lambda *a, **kw: dict(status="pass", handoff=handoff)
    )
    monkeypatch.setattr(H, "_paths", lambda *a: (hp, cp))
    monkeypatch.setattr(H.bootstrap, "manifest_path", lambda *a: manifest_path)
    monkeypatch.setattr(H, "_preopen", lambda *a: dict(selected_release_commit=ORIGIN))
    monkeypatch.setattr(
        H,
        "_identity",
        lambda *a: {**identity, "start_ticks": "999"} if fault == "pid" else identity,
    )
    if fault == "policy":
        args["policy_sha"] = "different"
    if fault == "frozen_source":
        handoff["frozen_files"][str(manifest_path)] = "0" * 64
    before = selector.read_bytes()
    if fault:
        with pytest.raises(ValueError):
            C.resolve_prepared_code_origin(data, DAY, **args)
    else:
        result = C.resolve_prepared_code_origin(data, DAY, **args)
        assert result["basis"] == (
            "verified_closed_intraday_code_handoff"
            if closed
            else "verified_selected_intraday_code_handoff"
        )
        assert result["origin_commit"] == ORIGIN
        assert result["pid_identity"] == identity
        assert result["sources"][str(cp)] == C._sha(cp)
    assert selector.read_bytes() == before
    assert not C.receipt_path(data, DAY, COMMIT, args["family"]).exists()

@pytest.mark.parametrize('prepared', ['pre_submit_delay','main_stop','holding_vote'], indirect=True)
@pytest.mark.parametrize('fault', [None,'policy','code','source','appeared','origin','unreviewed'])
@pytest.mark.parametrize('outside', [False,True])
def test_unprepared_stopped_origin_shared_by_policy_and_startup_readers(prepared,monkeypatch,fault,outside):
    from contextlib import contextmanager
    data,root,args,selector=_origin_resolution_arguments(prepared)
    C.receipt_path(data,DAY,COMMIT,args['family']).unlink()
    selector.write_text(json.dumps(dict(actual_pid_consumed=False,deployment_transition='native-failed-transition')))
    mp=Path(json.loads(prepared[-1].read_text())['manifest_path'])
    preopen=data/'preopen.json';preopen.write_text(json.dumps(dict(selected_release_commit=ORIGIN)))
    predecessor=data/'original-handoff.json';predecessor.write_text('original consumed predecessor')
    absent=data/'unissued-handoff.json'
    sources={str(p):C._sha(p) for p in (mp,preopen,predecessor)}
    proof=dict(target_date=DAY,release_commit=COMMIT,source_hashes=sources,
        unprepared_selected_handoff=dict(path=str(absent),predecessor_path=str(predecessor),predecessor_sha256=C._sha(predecessor)),
        runtime_effect=False,actual_pid_consumed=False,allowed_runtime_apply=False)
    review=dict(day=DAY,root=root,commit=COMMIT,code_root=Path(H.__file__).resolve().parents[3],code_commit='c'*40,prepared_observation=proof)
    monkeypatch.setattr(H.bootstrap,'manifest_path',lambda *a:mp)
    monkeypatch.setattr(H,'_preopen_path',lambda *a:preopen)
    monkeypatch.setattr(H,'_preopen',lambda *a:C._read(preopen))
    @contextmanager
    def scope(*a):
        token=H._PREDECESSOR_REVIEW.set(review)
        try:yield proof
        finally:H._PREDECESSOR_REVIEW.reset(token)
    monkeypatch.setattr(H,'stopped_preparation_review',scope)
    if fault=='policy':args['policy_sha']='wrong'
    elif fault=='code':args['expected']='wrong'
    elif fault=='source':predecessor.write_text('changed')
    elif fault=='appeared':absent.write_text('{}')
    elif fault=='origin':preopen.write_text(json.dumps(dict(selected_release_commit='d'*40)));sources[str(preopen)]=C._sha(preopen)
    elif fault=='unreviewed':monkeypatch.setattr(H,'_verify_entry_code_delta',lambda *a:(_ for _ in ()).throw(ValueError('unknown code')))
    token=H._PREDECESSOR_REVIEW.set(None if outside else review)
    before=selector.read_bytes()
    try:
        if fault:
            with pytest.raises(ValueError):C.resolve_prepared_code_origin(data,DAY,**args)
        else:
            result=C.resolve_prepared_code_origin(data,DAY,**args)
            assert result['origin_commit']==ORIGIN
            assert result['basis']=='verified_unprepared_stopped_original_contract'
            assert result['sources'].items()>=sources.items()
    finally:H._PREDECESSOR_REVIEW.reset(token)
    assert selector.read_bytes()==before
    assert not C.receipt_path(data,DAY,COMMIT,args['family']).exists()


@pytest.mark.parametrize("prepared", ["pre_submit_delay", "main_stop", "holding_vote"], indirect=True)
@pytest.mark.parametrize("fault", [None, "review", "target", "actual", "unreviewed", "source_during", "policy", "missing_index", "manifest"])
def test_first_postclose_preparation_does_not_require_an_unissued_code_receipt(
    prepared, monkeypatch, fault
):
    """Native original code plus reviewed successor needs no prior directory."""
    import shutil

    data, root, args, original_actual, receipt, original_prepared = prepared
    directory = data / "runtime/policy_bootstrap/code_handoffs" / DAY
    shutil.rmtree(directory)
    candidate = root.parent / "first-candidate"
    own = candidate / "src/engine/automation/intraday_release_handoff.py"
    own.parent.mkdir(parents=True)
    own.write_text("# candidate verifier\n")
    consumer = candidate / "consumer.py"
    consumer.write_text("reviewed future reader\n")
    selector = data / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(exist_ok=True)
    selector.write_text('{"selected":"original"}')
    monkeypatch.setattr(H, "DATA_DIR", data)
    monkeypatch.setattr(H, "__file__", str(own))
    monkeypatch.setattr(H, "_selection", lambda **kw: (root, COMMIT))
    monkeypatch.setattr(H, "predecessor_review_matches", lambda *a: fault != "review")
    def delta(*a):
        if fault == "unreviewed":
            raise ValueError("unreviewed_candidate")
        if fault == "source_during":
            (root / "consumer.py").write_text("changed original")
        return ["consumer.py"]
    monkeypatch.setattr(H, "_verify_entry_code_delta", delta)
    review = dict(code_root=candidate, code_commit="c" * 40,
        postclose_observation=dict(prepared_target_date="2099-01-01" if fault == "target" else DAY))
    index = data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json"
    index.parent.mkdir(parents=True)
    # Place this fixture under the native generation directory as real prepare does.
    native_prepared = index.parent / "fixture-generation/readiness.json"
    native_prepared.parent.mkdir()
    native_prepared.write_bytes(original_prepared.read_bytes())
    index.write_text(json.dumps(dict(target_date=DAY, receipt_path=str(native_prepared),
        receipt_sha256=C._sha(native_prepared))))
    if fault == "missing_index":
        index.unlink()
    if fault == "manifest":
        (root.parent / "manifest.json").write_text('{"changed":true}')
    monkeypatch.setattr(C, "_policy", lambda *a: (data / "policy.json", original_actual))
    actual = C._digest({"consumer.py": C._sha(consumer)})
    token = H._PREDECESSOR_REVIEW.set(review)
    before = original_prepared.read_bytes()
    try:
        kwargs = {**args, "policy_sha": "foreign" if fault == "policy" else args["policy_sha"], "expected": original_actual, "actual": "d" * 64 if fault == "actual" else actual}
        if fault:
            with pytest.raises(ValueError):
                H.verify_entry_consumer_code(DAY, **kwargs)
        else:
            proof = H.verify_entry_consumer_code(DAY, **kwargs)
            assert proof["verification_basis"] == "verified_prepared_predecessor_consumer_repair"
            assert proof["origin_commit"] == COMMIT and proof["release_commit"] == "c" * 40
            assert proof["actual_pid_consumed"] is False
        assert not directory.exists() and original_prepared.read_bytes() == before
    finally:
        H._PREDECESSOR_REVIEW.reset(token)
