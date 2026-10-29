"""Additive capability proofs must not rewrite historical operational evidence."""

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import policy_generation_validation as validation
from src.engine.automation import policy_generation_fixture_validation as writer

DAY = "2026-10-14"


def _fixture(data, family):
    payload = dict(
        date=DAY, generated_at=DAY + "T21:00:00+09:00", status="valid_empty", count=0
    )
    contract = generation.native(
        payload,
        family=family,
        day=DAY,
        data_root=data,
        source_state="valid_empty",
        comparison_state="insufficient_sample",
        handoff_state="incumbent_carried",
    )
    payload["policy_generation"] = contract
    if family == "holding_vote":
        payload = {"holding_path_vote_replay": payload}
    relative = {
        "entry_cancel_wait": f"report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_{DAY}.json",
        "rising_missed": f"report/rising_missed_classifier_prior/rising_missed_classifier_prior_{DAY}.json",
        "holding_vote": f"report/monitor_snapshots/holding_exit_observation_{DAY}.json",
        "auxiliary": f"report/reversal_auxiliary_tuning/{DAY}/evaluation.json",
    }[family]
    report = data / relative
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps(payload))
    observed = generation.observations(data.parent, DAY, data_root=data)[0]
    assert observed["status"] == "unverified"
    run = data / "report/postclose_generation_validation/runs/test-run"
    run.mkdir(parents=True)
    xml = ET.Element("testsuites")
    suite = ET.SubElement(xml, "testsuite")
    for name in validation.PLANS[family]:
        ET.SubElement(
            suite,
            "testcase",
            classname="src.tests." + Path(name).stem,
            name="synthetic_reader_contract",
        )
    ET.ElementTree(xml).write(run / "tests.xml")
    (run / "tests.log").write_text("synthetic reader fixture, not operational proof\n")
    (run / "network.json").write_text('{"blocked_attempts":0}')
    value = dict(
        schema="postclose_generation_fixture_receipt_v1",
        family=family,
        code_sha256=generation.code_generation(family),
        status="pass",
        closure_tests=validation.PLANS[family],
        unresolved_findings=[],
        passed_tests=len(validation.PLANS[family]),
        validation_plan=validation.plan_identity(family),
        validation_run=str(run),
        evidence={
            n: validation.file_sha(run / n)
            for n in ["tests.log", "tests.xml", "network.json"]
        },
        provider_calls=0,
        orders=0,
        protected_unchanged=True,
        protected_artifact_sha256={},
        **{k: False for k in validation.AUTHORITY_FALSE},
    )
    path = validation.fixture_path(data, family)

    def seal():
        value["receipt_sha256"] = generation.digest(
            {k: v for k, v in value.items() if k != "receipt_sha256"}
        )
        path.write_text(json.dumps(value))

    seal()
    return observed, report, run, path, value, seal


@pytest.mark.parametrize("family", validation.PLANS)
def test_current_fixture_closes_only_code_warning_without_rewriting_native_report(
    tmp_path, family
):
    data = tmp_path / "data"
    observed, report, run, path, value, seal = _fixture(data, family)
    before = {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}
    result = validation.current_fixture_observation(observed, data)
    assert result["status"] == "verified", result
    assert result["findings"] == [] and result["native_validated"] is False
    assert (
        result["historical_contract_status"] == "unverified"
        and result["current_code_capability_verified"] is True
    )
    assert (
        result["source_state"] == "valid_empty"
        and result["comparison_state"] == "insufficient_sample"
    )
    assert result["handoff_state"] == "incumbent_carried"
    assert (
        result["runtime_effect"] is False and result["allowed_runtime_apply"] is False
    )
    assert result["report_sha256"] == observed["report_sha256"]
    assert result["contract_sha256"] == observed["contract_sha256"]
    assert result["source_generation"] == observed["source_generation"]
    assert (
        generation.observations(tmp_path, DAY, data_root=data)[0]["status"]
        == "unverified"
    )
    assert all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "original",
        "compact",
        "pointer",
        "missing",
        "symlink",
        "logical",
        "physical",
    ],
)
def test_lossless_native_report_projection_keeps_original_hash_and_budget(
    tmp_path, monkeypatch, damage
):
    data = tmp_path / "data"
    _, report, _, _, _, _ = _fixture(data, "entry_cancel_wait")
    payload = json.loads(report.read_text())
    report.write_text(json.dumps(payload, indent=12))
    original = report.read_bytes()
    import gzip

    limit = len(gzip.compress(original, mtime=0)) + 32
    assert len(original) > limit
    monkeypatch.setattr(validation, "NATIVE_REPORT_LIMIT", limit)
    receipt = validation.publish_native_report_projection(
        data, "entry_cancel_wait", DAY
    )
    compact = Path(str(report) + ".gz")
    pointer = Path(str(compact) + ".archive_receipt.json")
    if damage == "original":
        report.write_bytes(original + b"\n")
    elif damage == "compact":
        compact.write_text("{}")
    elif damage == "pointer":
        pointer.write_text("{}")
    elif damage == "missing":
        compact.unlink()
    elif damage == "symlink":
        other = tmp_path / "foreign.json"
        compact.rename(other)
        compact.symlink_to(other)
    elif damage == "logical":
        row = json.loads(pointer.read_text())
        row["logical_content_sha256"] = "a" * 64
        row["artifact_content_sha256"] = generation.digest(
            {k: v for k, v in row.items() if k != "artifact_content_sha256"}
        )
        pointer.write_text(json.dumps(row))
    elif damage == "physical":
        monkeypatch.setattr(validation, "NATIVE_REPORT_LIMIT", 1)
    result = generation.observations(tmp_path, DAY, data_root=data)[0]
    if damage:
        assert result["status"] == "unobservable"
    else:
        value, sha = validation.read_native_report(data, "entry_cancel_wait", DAY)
        assert value == payload and sha == hashlib.sha256(original).hexdigest()
        assert result["status"] == "unverified" and result["report_sha256"] == sha
        assert (
            validation.current_fixture_observation(result, data)["status"] == "verified"
        )
        assert compact.stat().st_size < limit
    if damage != "original":
        assert report.read_bytes() == original


def test_projection_refuses_logically_oversized_source_and_invalid_native_contract(
    tmp_path, monkeypatch
):
    data = tmp_path / "data"
    _, report, _, _, _, _ = _fixture(data, "entry_cancel_wait")
    original = report.read_bytes()
    monkeypatch.setattr(validation, "NATIVE_REPORT_LIMIT", 64)
    with pytest.raises(ValueError):
        validation.publish_native_report_projection(data, "entry_cancel_wait", DAY)
    assert report.read_bytes() == original
    payload = json.loads(original)
    payload["policy_generation"]["contract_sha256"] = "a" * 64
    report.write_text(json.dumps(payload))
    changed = report.read_bytes()
    with pytest.raises(
        ValueError, match="source_contract_invalid|policy_generation_contract_invalid"
    ):
        validation.publish_native_report_projection(data, "entry_cancel_wait", DAY)
    assert report.read_bytes() == changed


@pytest.mark.parametrize(
    "damage",
    [
        "code",
        "family",
        "schema",
        "runtime",
        "profit",
        "provider",
        "orders",
        "protected",
        "plan",
        "tests",
        "count",
        "log",
        "xml",
        "network",
        "skipped",
        "failed",
        "missing_test_file",
        "run_path",
        "source",
        "report_hash",
        "contract_hash",
        "source_generation",
        "projection_code",
        "projection_state",
        "native_contract",
        "receipt_digest",
        "fixture_symlink",
    ],
)
def test_supplement_never_closes_changed_or_unverified_contract(tmp_path, damage):
    data = tmp_path / "data"
    observed, report, run, path, value, seal = _fixture(data, "entry_cancel_wait")
    if damage == "code":
        value["code_sha256"] = "a" * 64
    elif damage == "family":
        value["family"] = "holding_vote"
    elif damage == "schema":
        value["schema"] = "unknown"
    elif damage == "runtime":
        value["runtime_effect"] = True
    elif damage == "profit":
        value["actual_profit_verified"] = True
    elif damage == "provider":
        value["provider_calls"] = 1
    elif damage == "orders":
        value["orders"] = True
    elif damage == "protected":
        value["protected_unchanged"] = False
    elif damage == "plan":
        value["validation_plan"] = {}
    elif damage == "tests":
        value["closure_tests"] = []
    elif damage == "count":
        value["passed_tests"] = True
    elif damage == "log":
        (run / "tests.log").write_text("tampered")
    elif damage == "xml":
        (run / "tests.xml").write_text("tampered")
    elif damage in {"network", "skipped", "failed", "missing_test_file"}:
        if damage == "network":
            (run / "network.json").write_text('{"blocked_attempts":1}')
        else:
            tree = ET.parse(run / "tests.xml")
            suite = tree.getroot().find("testsuite")
            if damage == "missing_test_file":
                suite.remove(suite[0])
            else:
                ET.SubElement(suite[0], "skipped" if damage == "skipped" else "failure")
            tree.write(run / "tests.xml")
        value["evidence"] = {n: validation.file_sha(run / n) for n in value["evidence"]}
    elif damage == "run_path":
        value["validation_run"] = str(tmp_path)
    elif damage == "source":
        report.write_text(report.read_text() + " ")
    elif damage == "report_hash":
        observed["report_sha256"] = "a" * 64
    elif damage == "contract_hash":
        observed["contract_sha256"] = "a" * 64
    elif damage == "source_generation":
        observed["source_generation"] = "a" * 64
    elif damage == "projection_code":
        observed["code_sha256"] = "a" * 64
    elif damage == "projection_state":
        observed["source_state"] = "complete"
    elif damage == "native_contract":
        payload = json.loads(report.read_text())
        payload["policy_generation"]["runtime_effect"] = True
        report.write_text(json.dumps(payload))
        observed["report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    seal()
    if damage == "receipt_digest":
        path.write_text(path.read_text().replace(value["receipt_sha256"], "0" * 64))
    if damage == "fixture_symlink":
        dest = run / "other.json"
        path.rename(dest)
        path.symlink_to(dest)
    result = validation.current_fixture_observation(observed, data)
    assert result["status"] == "unverified" and result["findings"] == [
        "policy_generation_unverified"
    ]
    assert result.get("current_code_capability_verified") is not True


@pytest.mark.parametrize(
    "bad",
    [
        "failed",
        "timeout",
        "network",
        "changed_report",
        "missing_cases",
        "large_report",
        "large_report_changed",
    ],
)
def test_fixture_writer_failure_cannot_publish_or_modify_protected_source(
    tmp_path, monkeypatch, bad
):
    data = tmp_path / "data"
    family = "entry_cancel_wait"
    report = (
        data
        / "report/entry_cancel_wait_tuning"
        / f"entry_cancel_wait_tuning_{DAY}.json"
    )
    original = (
        "x" * (8 * 1024 * 1024 + 1)
        if bad.startswith("large_report")
        else "original native source"
    )
    report.parent.mkdir(parents=True)
    report.write_text(original)

    class Process:
        pid = 123

        def __init__(self, command, **kwargs):
            self.command = command
            output = Path(
                next(x.split("=", 1)[1] for x in command if x.startswith("--junitxml="))
            )
            assert not output.is_relative_to(data)
            assert output.parent.is_dir()
            self.running = True

        def wait(self, timeout):
            if bad == "timeout" and self.running:
                self.running = False
                raise writer.subprocess.TimeoutExpired(self.command, timeout)
            self.running = False
            xml_path = Path(
                next(
                    x.split("=", 1)[1]
                    for x in self.command
                    if x.startswith("--junitxml=")
                )
            )
            root = ET.Element("testsuite")
            if bad != "missing_cases":
                for name in validation.PLANS[family]:
                    ET.SubElement(
                        root,
                        "testcase",
                        classname="src.tests." + Path(name).stem,
                        name="fixture",
                    )
            ET.ElementTree(root).write(xml_path)
            (xml_path.parent / "network.json").write_text(
                json.dumps({"blocked_attempts": int(bad == "network")})
            )
            if bad in {"changed_report", "large_report_changed"}:
                report.write_text("concurrent update")
            return 1 if bad == "failed" else 0

        def poll(self):
            return None if self.running else 0

    monkeypatch.setattr(writer, "_assert_committed", lambda family: None)
    monkeypatch.setattr(writer.subprocess, "Popen", Process)
    monkeypatch.setattr(writer.os, "killpg", lambda *a: None)
    monkeypatch.setattr(
        writer.subprocess, "check_output", lambda *a, **kw: "a" * 40 + "\n"
    )
    if bad == "large_report":
        result = writer.validate(
            family, data, source_date=DAY, target_date="2026-10-15", publish=True
        )
        assert result["status"] == "pass" and result["published"] is True
        assert (
            validation.verify_fixture(data, family)[0]["protected_artifact_sha256"][
                str(report)
            ]
            == hashlib.sha256(original.encode()).hexdigest()
        )
        assert report.read_text() == original
        return
    with pytest.raises((ValueError, writer.subprocess.TimeoutExpired)):
        writer.validate(
            family, data, source_date=DAY, target_date="2026-10-15", publish=True
        )
    assert not validation.fixture_path(data, family).exists()
    assert report.read_text() == (
        "concurrent update"
        if bad in {"changed_report", "large_report_changed"}
        else original
    )
    assert (
        len(
            list(
                (data / "report/postclose_generation_validation/runs").glob(
                    "*/failure.json"
                )
            )
        )
        == 1
    )


@pytest.mark.parametrize("kind", ["fifo", "symlink", "oversize"])
def test_fixture_reader_is_bounded_and_rejects_special_sources(tmp_path, kind):
    import os

    path = tmp_path / "input"
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "symlink":
        target = tmp_path / "target"
        target.write_text("value")
        path.symlink_to(target)
    else:
        path.write_text("x" * 11)
    with pytest.raises((ValueError, OSError)):
        validation.file_bytes(path, 10)
    if kind != "oversize":
        with pytest.raises((ValueError, OSError)):
            validation.file_sha(path, stream=True)


def test_fixture_publication_rejects_dirty_or_untracked_source(monkeypatch):
    monkeypatch.setattr(
        writer.subprocess, "check_output", lambda *a, **k: "?? untracked.py\n"
    )
    with pytest.raises(ValueError, match="committed_sources"):
        writer._assert_committed("entry_cancel_wait")


@pytest.mark.parametrize("family", validation.PLANS)
def test_fixture_publication_checks_the_same_shared_budget_dependency(
    monkeypatch, family
):
    calls = []

    def dirty(command, **kwargs):
        calls.append(command)
        for name in generation.COMMON_CODE_COMPONENTS:
            assert command.count("src/engine/" + name) == 1
        return " M src/engine/lifecycle/research_input_budget.py\n"

    monkeypatch.setattr(writer.subprocess, "check_output", dirty)
    with pytest.raises(ValueError, match="committed_sources"):
        writer._assert_committed(family)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "dependency",
    [
        "lifecycle/research_input_budget.py",
        "monitoring/policy_generation_validation.py",
        "monitoring/policy_generation_code_handoff.py",
        "automation/policy_generation_fixture_validation.py",
    ],
)
def test_shared_dependency_change_creates_new_capability_and_fixture_paths(
    tmp_path, monkeypatch, dependency
):
    names = set(generation.COMMON_CODE_COMPONENTS)
    for paths in generation.COMPONENTS.values():
        names.update(paths)
    engine = tmp_path / "src/engine"
    for name in names:
        path = engine / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((generation.ENGINE / name).read_bytes())
    monkeypatch.setattr(generation, "ENGINE", engine)
    data = tmp_path / "data"
    before = {
        family: validation.fixture_path(data, family) for family in validation.PLANS
    }
    for family, path in before.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("preserved " + family).encode())
    originals = {path: path.read_bytes() for path in before.values()}
    helper = engine / dependency
    helper.write_bytes(
        helper.read_bytes() + b"\n# Different shared Claim generation.\n"
    )
    after = {
        family: validation.fixture_path(data, family) for family in validation.PLANS
    }
    assert all(
        after[family] != before[family] and not after[family].exists()
        for family in validation.PLANS
    )
    assert all(path.read_bytes() == raw for path, raw in originals.items())


@pytest.mark.parametrize("damage", [None, "plan", "issuer", "source", "evidence"])
def test_late_historical_fixture_uses_exact_original_issuer_plan(
    tmp_path, monkeypatch, damage
):
    import subprocess
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    from src.engine.infrastructure import runtime_release_router as router

    data = tmp_path / "data"
    _, report, _, path, value, seal = _fixture(data, "holding_vote")
    issuer = tmp_path / "issuer"
    issuer.mkdir()
    subprocess.run(["git", "init", "-q", str(issuer)], check=True)
    plan = {}
    for name in validation.plan_identity("holding_vote"):
        target = issuer / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"original reviewed validation bytes\n")
        plan[name] = validation.file_sha(target)
    subprocess.run(["git", "-C", str(issuer), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(issuer),
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "original issuer",
        ],
        check=True,
    )
    revision = subprocess.check_output(
        ["git", "-C", str(issuer), "rev-parse", "HEAD"], text=True
    ).strip()

    def validate(workspace, selection):
        assert (
            selection["release_root"] == str(issuer)
            and selection["git_commit"] == revision
        )
        if damage == "issuer":
            raise ValueError("untrusted issuer")

    monkeypatch.setattr(router, "validate_release", validate)
    sha = validation.file_sha(report)
    value.update(
        validation_plan=plan,
        release_root=str(issuer),
        git_commit=revision,
        protected_artifact_sha256={str(report): sha},
    )
    if damage == "plan":
        value["validation_plan"] = {**plan, next(iter(plan)): "b" * 64}
    if damage == "source":
        value["protected_artifact_sha256"][str(report)] = "b" * 64
    if damage == "evidence":
        value["evidence"]["network.json"] = "b" * 64
    seal()
    contract = dict(code_sha256=value["code_sha256"], fixture_receipt=None)
    if damage:
        with pytest.raises(ValueError):
            handoff._historical_fixture(
                contract, data, "holding_vote", late_report=(report, sha)
            )
    else:
        result = handoff._historical_fixture(
            contract, data, "holding_vote", late_report=(report, sha)
        )
        assert result["path"] == str(path)


@pytest.mark.parametrize(
    "family,review_map",
    [
        (family, review_map)
        for family in validation.PLANS
        for review_map in [
            "REVIEWED_SUCCESSORS",
            "REVIEWED_PRESERVED_SOURCE_SUCCESSORS",
            "REVIEWED_DEPLOYED_SOURCE_SUCCESSORS",
            "REVIEWED_DELAY_SOURCE_SUCCESSORS",
            "REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS",
            "REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS",
            "REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS",
            "REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS",
            "REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS",
            "REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS",
            "REVIEWED_CLEANUP_SOURCE_SUCCESSORS",
        ]
    ]
    + [
        (family, "REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS")
        for family in ("rising_missed", "holding_vote")
    ]
    + [
        (family, "REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS")
        for family in ("entry_cancel_wait", "holding_vote")
    ]
    + [
        (family, review_map)
        for family in ("rising_missed", "holding_vote")
        for review_map in (
            "REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS",
            "REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS",
            "REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS",
        )
    ],
)
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "unreviewed_old",
        "unreviewed_current",
        "source",
        "contract",
        "fixture_code",
        "plan",
        "report_path",
        "state",
        "missing",
        "authority",
        "receipt",
    ],
)
def test_exact_reviewed_successor_preserves_historical_code_and_source(
    tmp_path, monkeypatch, family, damage, review_map
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    if review_map in {
        "REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS",
        "REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS",
        "REVIEWED_CLEANUP_SOURCE_SUCCESSORS",
    }:
        monkeypatch.setitem(globals(), "DAY", "2026-10-16")
    data = tmp_path / "data"
    observed, report, run, path, value, seal = _fixture(data, family)
    payload = json.loads(report.read_text())
    native = (
        payload["holding_path_vote_replay"] if family == "holding_vote" else payload
    )
    contract = native["policy_generation"]
    old = "a" * 64
    current = contract["code_sha256"]
    contract["code_sha256"] = old
    if review_map in {
        "REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS",
        "REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS",
        "REVIEWED_CLEANUP_SOURCE_SUCCESSORS",
        "REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS",
        "REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS",
        "REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS",
        "REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS",
        "REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS",
    }:
        historical = dict(value, code_sha256=old)
        historical["receipt_sha256"] = generation.digest(
            {k: v for k, v in historical.items() if k != "receipt_sha256"}
        )
        historical_path = (
            data
            / "report/postclose_generation_validation"
            / (family + "_" + old + ".json")
        )
        historical_path.write_text(json.dumps(historical))
        contract["fixture_receipt"] = dict(
            path=str(historical_path), sha256=validation.file_sha(historical_path)
        )
    contract["retry_key"] = generation.digest(
        [family, contract["source_generation"], old, contract["source_state"]]
    )
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    report.write_text(json.dumps(payload))
    observed = generation.observations(tmp_path, DAY, data_root=data)[0]
    monkeypatch.setattr(handoff, "REVIEWED_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_PRESERVED_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_DEPLOYED_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_DELAY_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS", {})
    monkeypatch.setattr(handoff, "REVIEWED_CLEANUP_SOURCE_SUCCESSORS", {})

    def reviewed_pair(a, b):
        return {
            family: (
                ((a, b),)
                if review_map == "REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS"
                else (a, b)
            )
        }

    monkeypatch.setattr(handoff, review_map, reviewed_pair(old, current))
    if damage == "unreviewed_old":
        monkeypatch.setattr(handoff, review_map, reviewed_pair("b" * 64, current))
    elif damage == "unreviewed_current":
        monkeypatch.setattr(handoff, review_map, reviewed_pair(old, "b" * 64))
    elif damage == "source":
        native["count"] = 1
        report.write_text(json.dumps(payload))
    elif damage == "contract":
        contract["code_sha256"] = "b" * 64
        report.write_text(json.dumps(payload))
    elif damage == "fixture_code":
        value["code_sha256"] = "b" * 64
        seal()
    elif damage == "plan":
        value["validation_plan"] = {}
        seal()
    elif damage == "report_path":
        observed["artifact"] = str(tmp_path / "foreign.json")
    elif damage == "state":
        observed["source_state"] = "foreign"
    elif damage == "missing":
        observed["missing_components"] = ["reader"]
    elif damage == "authority":
        contract["allowed_runtime_apply"] = True
        report.write_text(json.dumps(payload))
    elif damage == "receipt":
        value["receipt_sha256"] = "b" * 64
        path.write_text(json.dumps(value))
    before = {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}
    result = handoff.current_fixture_observation(observed, data)
    assert result["status"] == ("verified" if damage is None else "unverified"), result
    if damage is None:
        assert (
            result["code_sha256"] == old
            and result["current_capability_code_sha256"] == current
        )
        assert result["native_validated"] is False and result["runtime_effect"] is False
        assert (
            result["allowed_runtime_apply"] is False
            and result["source_generation"] == observed["source_generation"]
        )
        assert result["contract_sha256"] == observed["contract_sha256"]
        assert all(
            result[key] == observed[key]
            for key in ("source_state", "comparison_state", "handoff_state")
        )
    assert all(p.read_bytes() == b for p, b in before.items())


FROZEN_PRE_CLEANUP_TARGETS = {
    "auxiliary": "00e4f1813805e520e9daed86fa1b71b55c06f76c7128b4ad7762d978ab956822",
    "entry_cancel_wait": "4bf8bb24955fa5889d9090bcbbee1fd317493f0841d2a5a46566453291a5e907",
    "holding_vote": "e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea",
    "rising_missed": "7fa7a62c8bd2f75b7218cee881ea1cffd41c4ade083b97fc73c0559693447aeb",
}


@pytest.mark.parametrize(
    "review_map",
    [
        "REVIEWED_SUCCESSORS",
        "REVIEWED_PRESERVED_SOURCE_SUCCESSORS",
        "REVIEWED_DEPLOYED_SOURCE_SUCCESSORS",
        "REVIEWED_DELAY_SOURCE_SUCCESSORS",
    ],
)
def test_historical_targets_remain_frozen_and_current_has_its_own_direct_pair(
    review_map,
):
    """Historical targets cannot silently chain to a newer family reader."""
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    for family, (_, successor) in getattr(handoff, review_map).items():
        prepared = handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family]
        assert successor == prepared[1]
        reviewed = (
            handoff.REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS
            if family == "auxiliary"
            else handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS
        )
        assert reviewed[family] == (prepared[0], FROZEN_PRE_CLEANUP_TARGETS[family])


def test_auxiliary_input_successor_preserves_prior_prepared_pair():
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    old = "d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0"
    assert handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS["auxiliary"] == (
        old,
        "2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4",
    )
    assert handoff.REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS == {
        "auxiliary": (
            old,
            "dea0b4f9d124372e48413635f5f82fbf3f0fbd6477a4f1beaca6769a68e9990b",
        )
    }
    assert handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS["auxiliary"] == (
        old,
        "a249dbc9baa7fb5e05a36481cf476083de6c8b7ad369e3b26ceb7f3ba74373b5",
    )
    assert handoff.REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS["auxiliary"] == (
        old,
        "00e4f1813805e520e9daed86fa1b71b55c06f76c7128b4ad7762d978ab956822",
    )


def test_post_aux_guard_successor_preserves_exact_original_reports_and_prior_targets():
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    original_pairs = {
        "rising_missed": (
            "e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874",
            "676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962",
        ),
        "holding_vote": (
            "057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce",
            "8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf",
        ),
    }
    for family, pair in original_pairs.items():
        assert handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family] == pair
    assert handoff.REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS == {
        "rising_missed": (
            original_pairs["rising_missed"][0],
            "b47474ed46cc63f090ccf14ce40b6d53b1d1518cba43211e648a1ee1b0f2aa36",
        ),
        "holding_vote": (
            original_pairs["holding_vote"][0],
            "02b637bfb01bb9f01b4d8b33672d2ae0d9be74ff07c3ee972608f0c55beaf2e5",
        ),
    }
    assert handoff.REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS == {
        "rising_missed": (
            original_pairs["rising_missed"][0],
            "5f8cd733ba9fb8b4733f3bafbc5a9431d45d6638713934daf74ba144844d74a5",
        ),
        "holding_vote": (
            original_pairs["holding_vote"][0],
            "e06ee4b2d6d09410dd81d88cb661b6a18df2ca1dea2e7e81823a7d6e03d24b46",
        ),
    }
    assert handoff.REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS == {
        "holding_vote": (
            original_pairs["holding_vote"][0],
            "6c4734c5e4204b36faf3d72ee873a429147d7a6e5a3a019d55fee29f4e145137",
        )
    }
    for family, pair in original_pairs.items():
        assert handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS[family] == (
            pair[0],
            FROZEN_PRE_CLEANUP_TARGETS[family],
        )


@pytest.mark.parametrize(
    "family,prior",
    [
        (
            "entry_cancel_wait",
            "b2a2017deb606554fbe1c9d481426786b3a8ab463c948ee84cd8ab856eddfca0",
        ),
        (
            "rising_missed",
            "dde49a32b7299deabf981e9f3a734a9da3019ba3f4e3eb7abbaff91dd3d01fa3",
        ),
    ],
)
def test_preserved_oct15_reports_retain_their_reviewed_capability_target(family, prior):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    expected_target = handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family][1]
    assert handoff.REVIEWED_PRESERVED_SOURCE_SUCCESSORS[family] == (
        prior,
        expected_target,
    )


@pytest.mark.parametrize(
    "family,historical,cleanup",
    [
        *[(family, False, False) for family in validation.PLANS],
        ("auxiliary", True, False),
        *[(family, False, True) for family in validation.PLANS],
    ],
)
@pytest.mark.parametrize(
    "fault",
    [
        None,
        "historical_fixture_absent",
        "other_date",
        "prior_target",
        "unknown_source",
        "unknown_current",
    ],
)
def test_integrated_direct_pair_never_chains_history_or_skips_original_fixture(
    tmp_path, monkeypatch, family, historical, cleanup, fault
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    monkeypatch.setitem(
        globals(), "DAY", "2026-10-15" if fault == "other_date" else "2026-10-16"
    )
    reviewed = (
        handoff.REVIEWED_CLEANUP_SOURCE_SUCCESSORS
        if cleanup
        else (
            handoff.REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS
            if family == "auxiliary" and not historical
            else handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS
        )
    )
    source, current = reviewed[family]
    # This test validates the named historical registration, not a later target.
    monkeypatch.setattr(generation, "code_generation", lambda candidate: current)
    data = tmp_path / "data"
    _, report, _, _, value, _ = _fixture(data, family)
    assert current == generation.code_generation(family)
    if fault == "prior_target":
        source = handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family][1]
    elif fault == "unknown_source":
        source = "f" * 64
    historical = dict(value, code_sha256=source)
    historical["receipt_sha256"] = generation.digest(
        {k: v for k, v in historical.items() if k != "receipt_sha256"}
    )
    path = (
        data
        / "report/postclose_generation_validation"
        / (family + "_" + source + ".json")
    )
    path.write_text(json.dumps(historical))
    reference = dict(path=str(path), sha256=validation.file_sha(path))
    body = json.loads(report.read_text())
    native = body["holding_path_vote_replay"] if family == "holding_vote" else body
    contract = native["policy_generation"]
    contract.update(
        code_sha256=source,
        fixture_receipt=None if fault == "historical_fixture_absent" else reference,
        retry_key=generation.digest(
            [family, contract["source_generation"], source, contract["source_state"]]
        ),
    )
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    report.write_text(json.dumps(body))
    if fault == "unknown_current":
        monkeypatch.setattr(generation, "code_generation", lambda family: "b" * 64)
    observed = generation.observations(tmp_path, DAY, data_root=data)[0]
    before = {p: p.read_bytes() for p in data.rglob("*") if p.is_file()}
    result = handoff.current_fixture_observation(observed, data)
    assert result["status"] == ("verified" if fault is None else "unverified")
    if fault is None:
        assert result["preserved_historical_fixture"] == reference
        assert (
            result["current_fixture"] != reference
            and result["native_validated"] is False
        )
        assert (
            result["runtime_effect"] is False
            and result["allowed_runtime_apply"] is False
        )
        assert all(
            result[name] == observed[name]
            for name in (
                "source_generation",
                "source_state",
                "comparison_state",
                "handoff_state",
            )
        )
    assert all(path.read_bytes() == raw for path, raw in before.items())


@pytest.mark.parametrize("family", ["rising_missed", "holding_vote"])
def test_post_aux_guard_successor_does_not_transitively_promote_older_reports(
    tmp_path, family
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    data = tmp_path / "data"
    _, report, _, _, _, _ = _fixture(data, family)
    payload = json.loads(report.read_text())
    native = (
        payload["holding_path_vote_replay"] if family == "holding_vote" else payload
    )
    contract = native["policy_generation"]
    old = handoff.REVIEWED_PRESERVED_SOURCE_SUCCESSORS[family][0]
    contract.update(
        code_sha256=old,
        retry_key=generation.digest(
            [family, contract["source_generation"], old, contract["source_state"]]
        ),
    )
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    report.write_text(json.dumps(payload))
    observed = generation.observations(tmp_path, DAY, data_root=data)[0]
    before = report.read_bytes()
    result = handoff.current_fixture_observation(observed, data)
    assert result["status"] == "unverified"
    assert result.get("current_code_capability_verified") is not True
    assert report.read_bytes() == before


@pytest.mark.parametrize(
    "family,review_map",
    [
        *[(family, name) for family in ("rising_missed", "holding_vote")
          for name in ("REVIEWED_SUBMIT_FRESH_SOURCE_SUCCESSORS", "REVIEWED_SUBMIT_FRESH_CONSUMED_SUCCESSORS")],
        ("auxiliary", "REVIEWED_SUCCESSORS"),
        ("auxiliary", "REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS"),
        ("auxiliary", "REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS"),
        ("rising_missed", "REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS"),
        ("holding_vote", "REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS"),
        ("holding_vote", "REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS"),
        ("rising_missed", "REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS"),
        ("holding_vote", "REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS"),
        *[
            (family, "REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS")
            for family in validation.PLANS
        ],
        *[
            (family, "REVIEWED_CLEANUP_SOURCE_SUCCESSORS")
            for family in validation.PLANS
        ],
        *[
            (family, "REVIEWED_RECEIPT_CUSTODY_SOURCE_SUCCESSORS")
            for family in validation.PLANS
        ],
        ("holding_vote", "REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS"),
        ("auxiliary", "REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS"),
        *[
            (family, "REVIEWED_SOURCE_READER_SUCCESSORS")
            for family in ("rising_missed", "auxiliary")
        ],
        *[
            (family, "REVIEWED_DELAY_CLEANUP_SUCCESSORS")
            for family in ("rising_missed", "auxiliary", "holding_vote")
        ],
        ("holding_vote", "REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS"),
        *[
            (family, "REVIEWED_HOLDING_REPUBLICATION_SUCCESSORS")
            for family in ("entry_cancel_wait", "auxiliary")
        ],
        *[
            (family, "REVIEWED_FIXED_WAIT_SUCCESSORS")
            for family in ("rising_missed", "holding_vote")
        ],
        *[
            (family, "REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS")
            for family in validation.PLANS
        ],
        *[(family, "REVIEWED_ENTRY_COST_SUCCESSORS") for family in validation.PLANS],
        *[(family, "REVIEWED_SHUTDOWN_SUCCESSORS") for family in validation.PLANS],
        *[
            (family, "REVIEWED_SHUTDOWN_SOURCE_SUCCESSORS")
            for family in validation.PLANS
        ],
        *[
            (family, "REVIEWED_SHUTDOWN_CONSUMED_SUCCESSORS")
            for family in validation.PLANS
        ],
        *[
            (family, review_map)
            for family in ("rising_missed", "holding_vote")
            for review_map in (
                "REVIEWED_NATIVE_SELECTION_SUCCESSORS",
                "REVIEWED_NATIVE_SELECTION_SOURCE_SUCCESSORS",
                "REVIEWED_NATIVE_SELECTION_CONSUMED_SUCCESSORS",
                "REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS",
                "REVIEWED_PRE_SUBMIT_CONSUMED_SUCCESSORS",
                "REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS",
                "REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS",
            )
        ],
        *[
            (family, "REVIEWED_QUANTITY_CAPTURE_SUCCESSORS")
            for family in ("rising_missed", "holding_vote")
        ],
        *[
            (family, "REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS")
            for family in ("entry_cancel_wait", "holding_vote")
        ],
        ("entry_cancel_wait", "REVIEWED_BUY_IDENTITY_SUCCESSORS"),
        *[
            (family, "REVIEWED_ENTRY_RECEIPT_SUCCESSORS")
            for family in ("entry_cancel_wait", "rising_missed", "holding_vote")
        ],
    ],
)
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "missing",
        "bytes",
        "path",
        "authority",
        "seal",
        "symlink",
        "current_missing",
        "current_bytes",
        "current_code",
    ],
)
def test_successor_requires_preserved_prior_fixture_and_independent_current_fixture(
    tmp_path, monkeypatch, damage, review_map, family
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    if review_map in {
        "REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS",
        "REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS",
        "REVIEWED_CLEANUP_SOURCE_SUCCESSORS",
    }:
        monkeypatch.setitem(globals(), "DAY", "2026-10-16")
    data = tmp_path / "data"
    _, report, _, current_path, value, seal_current = _fixture(data, family)
    payload = json.loads(report.read_text())
    native = (
        payload["holding_path_vote_replay"] if family == "holding_vote" else payload
    )
    contract = native["policy_generation"]
    old = "a" * 64
    current = contract["code_sha256"]
    historical = dict(value, code_sha256=old)
    if damage == "authority":
        historical["allowed_runtime_apply"] = True
    historical["receipt_sha256"] = generation.digest(
        {k: v for k, v in historical.items() if k != "receipt_sha256"}
    )
    if damage == "seal":
        historical["receipt_sha256"] = "b" * 64
    path = (
        data / "report/postclose_generation_validation" / (family + "_" + old + ".json")
    )
    path.write_text(json.dumps(historical))
    reference = dict(path=str(path), sha256=validation.file_sha(path))
    contract.update(
        code_sha256=old,
        fixture_receipt=reference,
        retry_key=generation.digest(
            [family, contract["source_generation"], old, contract["source_state"]]
        ),
    )
    if damage == "path":
        reference["path"] = str(tmp_path / "foreign.json")
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    report.write_text(json.dumps(payload))
    observed = generation.observations(tmp_path, DAY, data_root=data)[0]
    monkeypatch.setattr(
        handoff,
        review_map,
        {
            family: (
                ((old, current),)
                if review_map == "REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS"
                else (old, current)
            )
        },
    )
    if damage == "missing":
        path.unlink()
    elif damage == "bytes":
        path.write_text("{}")
    elif damage == "symlink":
        other = tmp_path / "historical.json"
        path.rename(other)
        path.symlink_to(other)
    elif damage == "current_missing":
        current_path.unlink()
    elif damage == "current_bytes":
        current_path.write_text("{}")
    elif damage == "current_code":
        value["code_sha256"] = old
        seal_current()
    before = report.read_bytes()
    result = handoff.current_fixture_observation(observed, data)
    assert result["status"] == ("verified" if damage is None else "unverified"), result
    assert report.read_bytes() == before
    if damage is None:
        assert result["preserved_historical_fixture"] == reference
        assert result["current_fixture"] != reference
        assert result["native_validated"] is False
        assert result["historical_contract_status"] == "unverified"


@pytest.mark.parametrize("family", list(validation.PLANS))
def test_historical_capability_branches_keep_original_generations(family):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    pairs = handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family]
    # Multiple reviewed branches may be preserved. Their insertion order does
    # not choose the native report; the consumer matches its exact source pair.
    assert (
        ({
            "rising_missed": "28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922",
            "holding_vote": "7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386",
            "entry_cancel_wait": "5fa218b7b916b6b2a98a7a395573dac80ff96d2345edae3b64f9f99e3574125d",
            "auxiliary": "82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f",
        }[family])
        in {pair[0] for pair in pairs}
    )


@pytest.mark.parametrize("family", ["rising_missed", "holding_vote"])
def test_holding_quote_capability_retains_original_pairs(family):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    pairs = handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family]
    original, previous = {
        "rising_missed": (
            (
                "6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7",
                "28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922",
            ),
            "9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791",
        ),
        "holding_vote": (
            (
                "2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0",
                "7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386",
            ),
            "05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf",
        ),
    }[family]
    for source in original:
        assert (source, previous) in pairs
        assert len({target for origin, target in pairs if origin == source}) > 1
        assert (source, source) not in pairs
    assert "a" * 64 not in {origin for origin, target in pairs}


@pytest.mark.parametrize("family", list(validation.PLANS))
def test_native_verified_family_does_not_require_historical_successor(
    family, monkeypatch, tmp_path
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    observed = dict(
        family=family,
        status="verified",
        findings=[],
        code_sha256=generation.code_generation(family),
        native_validated=True,
    )
    monkeypatch.setattr(
        validation,
        "verify_fixture",
        lambda *a: pytest.fail("native verdict already verified"),
    )
    assert handoff.current_fixture_observation(observed, tmp_path) == observed


@pytest.mark.parametrize("family", ["rising_missed", "holding_vote", "auxiliary"])
def test_unreviewed_code_pair_is_not_reported_as_original_report_mutation(
    family, tmp_path
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    observed = dict(
        family=family,
        status="unverified",
        findings=["policy_generation_unverified"],
        missing_components=[],
        observation_complete=True,
        native_validated=False,
        code_sha256="a" * 64,
    )
    result = handoff.current_fixture_observation(observed, tmp_path)
    assert (
        result["status"] == "unverified" and result["findings"] == observed["findings"]
    )
    assert result["current_fixture_reason"] == "successor_code_pair_unreviewed"
    assert "current_code_capability_verified" not in result


@pytest.mark.parametrize("foreign", [False, True])
def test_native_fixture_relative_reference_binds_data_owner_not_launcher_cwd(
    tmp_path, monkeypatch, foreign
):
    data = tmp_path / "workspace/data"
    _, report, _, fixture, _, _ = _fixture(data, "auxiliary")
    payload = json.loads(report.read_text())
    contract = payload["policy_generation"]
    contract["fixture_receipt"] = dict(
        path=(
            "outside/" + fixture.name
            if foreign
            else "data/report/postclose_generation_validation/" + fixture.name
        ),
        sha256=validation.file_sha(fixture),
    )
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    other = tmp_path / "unrelated-launcher"
    other.mkdir()
    monkeypatch.chdir(other)
    if foreign:
        with pytest.raises(ValueError, match="fixture_path_invalid"):
            generation.inspect(
                contract, family="auxiliary", day=DAY, payload=payload, data_root=data
            )
    else:
        result = generation.inspect(
            contract, family="auxiliary", day=DAY, payload=payload, data_root=data
        )
        assert result["status"] == "verified"


@pytest.mark.parametrize(
    "successor",
    [
        "REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS",
        "REVIEWED_FIXED_WAIT_SUCCESSORS",
        "REVIEWED_ENTRY_RECEIPT_SUCCESSORS",
        "REVIEWED_QUANTITY_CAPTURE_SUCCESSORS",
    ],
)
@pytest.mark.parametrize(
    "damage", [None, "report", "missing", "network", "plan", "count", "wrong_pair"]
)
def test_exact_successor_accepts_late_original_fixture_only_with_native_report_binding(
    tmp_path, monkeypatch, damage, successor
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    data = tmp_path / "data"
    family = "holding_vote"
    _, report, run, current_path, current, seal = _fixture(data, family)
    payload = json.loads(report.read_bytes())
    contract = payload["holding_path_vote_replay"]["policy_generation"]
    old = "a" * 64
    new = contract["code_sha256"]
    contract.update(
        code_sha256=old,
        fixture_receipt=None,
        retry_key=generation.digest(
            [family, contract["source_generation"], old, contract["source_state"]]
        ),
    )
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    report.write_text(json.dumps(payload))
    before = report.read_bytes()
    prior = dict(
        current,
        code_sha256=old,
        protected_artifact_sha256={str(report): validation.file_sha(report)},
    )
    if damage == "report":
        prior["protected_artifact_sha256"][str(report)] = "b" * 64
    if damage == "plan":
        prior["validation_plan"] = {}
    if damage == "count":
        prior["passed_tests"] = True
    if damage == "network":
        (run / "network.json").write_text('{"blocked_attempts":1}')
        prior["evidence"] = {
            **prior["evidence"],
            "network.json": validation.file_sha(run / "network.json"),
        }
    prior["receipt_sha256"] = generation.digest(
        {k: v for k, v in prior.items() if k != "receipt_sha256"}
    )
    path = (
        data / "report/postclose_generation_validation" / (family + "_" + old + ".json")
    )
    if damage != "missing":
        path.write_text(json.dumps(prior))
    monkeypatch.setattr(
        handoff, successor, {family: ("c" * 64 if damage == "wrong_pair" else old, new)}
    )
    observed = generation.observations(tmp_path, DAY, data_root=data)[0]
    result = handoff.current_fixture_observation(observed, data)
    assert result["status"] == ("verified" if damage is None else "unverified"), result
    assert report.read_bytes() == before and contract["fixture_receipt"] is None


@pytest.mark.parametrize("mutation", [None, "rewrite", "append", "replace"])
def test_protected_hash_stream_is_bounded_and_rejects_mid_read_generation_change(
    tmp_path, monkeypatch, mutation
):
    path = tmp_path / "protected.json"
    raw = b"x" * (128 * 1024 + 1)
    path.write_bytes(raw)
    fdopen = validation.os.fdopen

    class Reader:
        def __init__(self, stream):
            self.stream = stream
            self.reads = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def fileno(self):
            return self.stream.fileno()

        def read(self, size):
            assert 0 < size <= 64 * 1024
            value = self.stream.read(size)
            self.reads += 1
            if self.reads == 1:
                if mutation == "rewrite":
                    path.write_bytes(b"y" * len(raw))
                elif mutation == "append":
                    with path.open("ab") as handle:
                        handle.write(b"y")
                elif mutation == "replace":
                    replacement = tmp_path / "replacement"
                    replacement.write_bytes(raw)
                    replacement.replace(path)
            return value

    monkeypatch.setattr(
        validation.os, "fdopen", lambda *a, **kw: Reader(fdopen(*a, **kw))
    )
    if mutation:
        with pytest.raises(ValueError, match="fixture_read_changed_or_limit_exceeded"):
            validation.file_sha(path, stream=True)
    else:
        assert validation.file_sha(path, stream=True) == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("family", ["rising_missed", "holding_vote"])
def test_shared_numeric_owner_invalidates_capability_generation(
    family, monkeypatch, tmp_path
):
    import shutil

    engine = tmp_path / "src/engine"
    names = (*generation.COMPONENTS[family], *generation.COMMON_CODE_COMPONENTS)
    for name in names:
        target = engine / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generation.ENGINE / name, target)
    monkeypatch.setattr(generation, "ENGINE", engine)
    before = generation.code_generation(family)
    numeric = engine / "../utils/numeric.py"
    numeric.write_bytes(numeric.read_bytes() + b"\n# changed numeric source\n")
    assert generation.code_generation(family) != before


@pytest.mark.parametrize(
    "family,origin",
    [
        (
            "rising_missed",
            "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        ),
        (
            "holding_vote",
            "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        ),
    ],
)
def test_krx_listing_capability_preserves_its_exact_formatted_successor(family, origin):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    pairs = handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family]
    formatted = {
        "rising_missed": "e3107fd43332462fb9dfcbd023fbb761857ed7de5aef81387f403f7c3b712302",
        "holding_vote": "d20ee98c614b51edd0c763369429c48c0c49e95deaee849faa43b45e3144e893",
    }[family]
    assert (origin, formatted) in pairs
    # Current code needs its own reviewed original; historical succession is
    # never transitively extended because today's implementation changed.
    assert (origin, generation.code_generation(family)) not in pairs
    assert len({pair[1] for pair in pairs if pair[0] == origin}) > 1


@pytest.mark.parametrize("family", list(validation.PLANS))
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "historical_missing",
        "current_missing",
        "current_code",
        "unreviewed_current",
        "original_source",
    ],
)
def test_formatted_family_requires_both_exact_generations_without_promoting_history(
    tmp_path, monkeypatch, family, damage
):
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    data = tmp_path / "data"
    _, report, _, current_path, current_fixture, seal_current = _fixture(data, family)
    old = handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family][-1][0]
    current = generation.code_generation(family)
    # Legacy-reader behavior uses an explicit synthetic reviewed pair. Current
    # source-review discovery has separate real-Git producer/consumer coverage.
    monkeypatch.setitem(handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS, family,
                        (*handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family], (old, current)))
    historical = dict(current_fixture, code_sha256=old)
    historical["receipt_sha256"] = generation.digest(
        {k: v for k, v in historical.items() if k != "receipt_sha256"}
    )
    historical_path = current_path.with_name(f"{family}_{old}.json")
    historical_path.write_text(json.dumps(historical))
    payload = json.loads(report.read_text())
    native = (
        payload["holding_path_vote_replay"] if family == "holding_vote" else payload
    )
    contract = native["policy_generation"]
    contract.update(
        code_sha256=old,
        fixture_receipt={
            "path": str(historical_path),
            "sha256": validation.file_sha(historical_path),
        },
    )
    contract["retry_key"] = generation.digest(
        [family, contract["source_generation"], old, contract["source_state"]]
    )
    contract["contract_sha256"] = generation.digest(
        {k: v for k, v in contract.items() if k != "contract_sha256"}
    )
    report.write_text(json.dumps(payload))
    observed = generation.observations(tmp_path, DAY, data_root=data)[0]
    assert observed["status"] == "unverified"
    if damage == "historical_missing":
        historical_path.unlink()
    elif damage == "current_missing":
        current_path.unlink()
    elif damage == "current_code":
        current_fixture["code_sha256"] = old
        seal_current()
    elif damage == "unreviewed_current":
        monkeypatch.setattr(generation, "code_generation", lambda *_: "0" * 64)
    elif damage == "original_source":
        native["count"] = 1
        report.write_text(json.dumps(payload))
    originals = {
        p: p.read_bytes() for p in (report, historical_path, current_path) if p.exists()
    }
    result = handoff.current_fixture_observation(observed, data)
    assert result["status"] == ("verified" if damage is None else "unverified"), result
    assert all(p.read_bytes() == raw for p, raw in originals.items())
    if damage is None:
        assert result["native_validated"] is False
        assert result["historical_contract_status"] == "unverified"
        assert result["reviewed_code_pair"] == [old, current]
        assert result["current_fixture"] != result["preserved_historical_fixture"]


@pytest.mark.parametrize("changed", [False, True])
@pytest.mark.parametrize("interrupted", [False, True])
def test_native_projection_republish_preserves_previous_generation(
    tmp_path, monkeypatch, changed, interrupted
):
    import gzip
    from src.utils.jsonl_io import write_json_object_generation_safe

    data = tmp_path / "data"
    _, report, _, _, _, _ = _fixture(data, "entry_cancel_wait")
    payload = json.loads(report.read_text())
    report.write_text(json.dumps(payload, indent=12))
    old_source = report.read_bytes()
    monkeypatch.setattr(
        validation, "NATIVE_REPORT_LIMIT", len(gzip.compress(old_source)) + 256
    )
    original = validation.publish_native_report_projection(
        data, "entry_cancel_wait", DAY
    )
    compressed = Path(str(report) + ".gz")
    pointer = Path(str(compressed) + ".archive_receipt.json")
    old_compressed, old_receipt = compressed.read_bytes(), pointer.read_bytes()
    if changed:
        payload["generated_at"] = DAY + "T22:00:00+09:00"
        payload["policy_generation"] = generation.native(
            payload,
            family="entry_cancel_wait",
            day=DAY,
            data_root=data,
            source_state="valid_empty",
            comparison_state="insufficient_sample",
            handoff_state="incumbent_carried",
        )
    write_json_object_generation_safe(report, payload, indent=12)
    if interrupted:
        from src.engine.scalping import entry_split_monitor_projection as files

        with monkeypatch.context() as patch:
            patch.setattr(
                files,
                "_write_atomic",
                lambda *a, **k: (_ for _ in ()).throw(
                    RuntimeError("interrupted_alias_publication")
                ),
            )
            with pytest.raises(RuntimeError, match="interrupted_alias_publication"):
                validation.publish_native_report_projection(
                    data, "entry_cancel_wait", DAY
                )
        assert pointer.read_bytes() == old_receipt
    current = validation.publish_native_report_projection(
        data, "entry_cancel_wait", DAY
    )
    archived = (
        report.parent
        / "superseded"
        / (report.stem + "-" + original["archive_sha256"][:16])
    )
    assert (archived / compressed.name).read_bytes() == old_compressed
    assert (
        archived
        / (pointer.name + "." + hashlib.sha256(old_receipt).hexdigest() + ".json")
    ).read_bytes() == old_receipt
    value, digest = validation.read_native_report(data, "entry_cancel_wait", DAY)
    assert value == payload and digest == current["logical_content_sha256"]
    identities = (compressed.stat().st_ino, pointer.stat().st_ino)
    assert (
        validation.publish_native_report_projection(data, "entry_cancel_wait", DAY)
        == current
    )
    assert identities == (compressed.stat().st_ino, pointer.stat().st_ino)
    assert (
        archived
        / (pointer.name + "." + hashlib.sha256(old_receipt).hexdigest() + ".json")
    ).read_bytes() == old_receipt
    for _ in range(2):
        write_json_object_generation_safe(report, payload, indent=12)
        validation.publish_native_report_projection(data, "entry_cancel_wait", DAY)
        assert (
            validation.read_native_report(data, "entry_cancel_wait", DAY)[0] == payload
        )
        assert (
            archived
            / (pointer.name + "." + hashlib.sha256(old_receipt).hexdigest() + ".json")
        ).read_bytes() == old_receipt


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "gzip",
        "seal",
        "logical",
        "original_size",
        "epoch",
        "retained",
        "symlink",
    ],
)
def test_projection_generation_rotation_rejects_unproved_predecessor(
    tmp_path, monkeypatch, damage
):
    import gzip
    from src.utils.jsonl_io import write_json_object_generation_safe

    data = tmp_path / "data"
    _, report, _, _, _, _ = _fixture(data, "entry_cancel_wait")
    payload = json.loads(report.read_text())
    report.write_text(json.dumps(payload, indent=12))
    monkeypatch.setattr(
        validation, "NATIVE_REPORT_LIMIT", len(gzip.compress(report.read_bytes())) + 256
    )
    previous = validation.publish_native_report_projection(
        data, "entry_cancel_wait", DAY
    )
    compressed = Path(str(report) + ".gz")
    pointer = Path(str(compressed) + ".archive_receipt.json")
    write_json_object_generation_safe(report, payload, indent=12)
    archived = (
        report.parent
        / "superseded"
        / (report.stem + "-" + previous["archive_sha256"][:16])
    )
    old = archived / compressed.name
    retained = archived / (
        pointer.name + "." + hashlib.sha256(pointer.read_bytes()).hexdigest() + ".json"
    )
    if damage == "missing":
        old.unlink()
    elif damage == "gzip":
        old.write_bytes(b"broken gzip")
    elif damage == "retained":
        retained.write_text("conflicting receipt")
    elif damage == "symlink":
        retained.symlink_to(pointer)
    else:
        value = json.loads(pointer.read_bytes())
        if damage == "seal":
            value["artifact_content_sha256"] = "0" * 64
        else:
            if damage == "logical":
                value["logical_content_sha256"] = "0" * 64
            elif damage == "original_size":
                value["original_identity"]["size"] += 1
            else:
                value["archive_generation"]["size"] += 1
            value["artifact_content_sha256"] = generation.digest(
                {k: v for k, v in value.items() if k != "artifact_content_sha256"}
            )
        pointer.write_text(json.dumps(value))
    before = pointer.read_bytes()
    with pytest.raises((ValueError, OSError, EOFError)):
        validation.publish_native_report_projection(data, "entry_cancel_wait", DAY)
    assert pointer.read_bytes() == before
    with pytest.raises((ValueError, OSError)):
        validation.read_native_report(data, "entry_cancel_wait", DAY)


@pytest.mark.parametrize("family", list(validation.PLANS))
@pytest.mark.parametrize("damage", [None, "historical_missing", "current_missing", "current_code", "unreviewed_current", "original_source"])
def test_prepared_state_metadata_accepts_exact_deployed_source_pair(tmp_path, monkeypatch, family, damage):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    pair = handoff.REVIEWED_PREPARED_STATE_SOURCE_SUCCESSORS[family]
    # Exercise the preserved metadata-only predecessor generation. Subsequent
    # shared-handler instrumentation has its own exact-pair regression above.
    monkeypatch.setattr(generation, "code_generation", lambda _: pair[1])
    monkeypatch.setitem(handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS, family,
        (*handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family], pair))
    test_formatted_family_requires_both_exact_generations_without_promoting_history(
        tmp_path, monkeypatch, family, damage)


@pytest.mark.parametrize("origin", [
    "357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd",
    "82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f",
])
def test_entry_latency_auxiliary_generation_is_exact_and_originals_are_retained(origin):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    current = generation.code_generation("auxiliary")
    assert origin in {pair[0] for pair in handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"]}
    assert ("0" * 64, current) not in handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"]


@pytest.mark.parametrize("family", ["rising_missed", "holding_vote", "auxiliary"])
def test_invalidation_cadence_capability_keeps_native_predecessors(family):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    current = generation.code_generation(family)
    origins = {
        "rising_missed": "9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791",
        "holding_vote": "05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf",
        "auxiliary": "9fb5d5b0bbe17b72ca832a883b059522d725f3234fca853324308beedf73bacc",
    }
    assert origins[family] in {pair[0] for pair in handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family]}
    assert ("0" * 64, current) not in handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family]


def _source_review_case(tmp_path, monkeypatch):
    """Two genuinely committed issuers, one shared change, all native families."""
    import shutil
    import subprocess
    from src.engine.monitoring import policy_generation_code_handoff as handoff

    old, new = (tmp_path / name for name in ("origin", "current"))
    components = {family: (family + ".py",) for family in validation.PLANS}
    common = ("shared.py",)
    commits = {}
    for role, root in (("origin", old), ("current", new)):
        engine = root / "src/engine"
        (engine / "monitoring").mkdir(parents=True)
        (engine / "monitoring/policy_generation_contract.py").write_text(
            "COMPONENTS = " + repr(components) + "\nCOMMON_CODE_COMPONENTS = " + repr(common) + "\n"
        )
        for family in components:
            (engine / (family + ".py")).write_text("value = 1\n")
        (engine / "shared.py").write_text("value = " + ("1" if role == "origin" else "2") + "\n")
        for name in set(validation.plan_identity("auxiliary")) | {n for plan in validation.PLANS.values() for n in plan}:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(validation.ROOT / name, target)
        for command in (["init", "-q"], ["add", "."],
                        ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", role]):
            subprocess.run(["git", *command], cwd=root, check=True, capture_output=True)
        commits[role] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    monkeypatch.setattr(generation, "COMPONENTS", components)
    monkeypatch.setattr(generation, "COMMON_CODE_COMPONENTS", common)
    monkeypatch.setattr(generation, "ENGINE", new / "src/engine")
    monkeypatch.setattr(validation, "ROOT", new)
    evidence = tmp_path / "review.txt"
    evidence.write_text("Reviewed shared change; original reports and economic gaps are preserved.\n")
    body = dict(
        schema="postclose_generation_source_review_v1",
        verification_scope="report_only_code_capability",
        origin_release_root=str(old), current_release_root=str(new),
        origin_git_commit=commits["origin"], current_git_commit=commits["current"],
        reviewed_files={"src/engine/shared.py": dict(
            before=validation.file_sha(old / "src/engine/shared.py"),
            after=validation.file_sha(new / "src/engine/shared.py"))},
        reviewed_families=sorted(components),
        review_evidence=dict(path=str(evidence), sha256=validation.file_sha(evidence)),
        provider_calls=0, orders=0,
        **{k: False for k in validation.AUTHORITY_FALSE},
    )

    def seal():
        raw = (json.dumps(body, sort_keys=True) + "\n").encode()
        path = tmp_path / (hashlib.sha256(raw).hexdigest() + ".json")
        path.write_bytes(raw)
        return path

    return handoff, old, new, body, seal


@pytest.mark.parametrize("damage", [None, "family", "file", "dirty", "commit", "authority", "evidence", "alias", "registry"])
def test_source_review_discovers_every_affected_family_and_fails_closed(tmp_path, monkeypatch, damage):
    handoff, old, new, body, seal = _source_review_case(tmp_path, monkeypatch)
    if damage == "family":
        body["reviewed_families"].pop()
    elif damage == "file":
        body["reviewed_files"].clear()
    elif damage == "dirty":
        (new / "src/engine/shared.py").write_text("value = 3\n")
    elif damage == "commit":
        body["current_git_commit"] = "0" * 40
    elif damage == "authority":
        body["allowed_runtime_apply"] = True
    elif damage == "evidence":
        Path(body["review_evidence"]["path"]).write_text("changed")
    elif damage == "registry":
        body["reviewed_families"] = ["invented"]
    path = seal()
    if damage == "alias":
        alias = tmp_path / "alias.json"
        alias.symlink_to(path)
        path = alias
    if damage:
        with pytest.raises(ValueError, match="source_review_"):
            handoff.reviewed_source_transition(path)
    else:
        result = handoff.reviewed_source_transition(path)
        assert set(result["pairs"]) == set(validation.PLANS)
        assert all(before != after for before, after in result["pairs"].values())
        assert result["reference"]["sha256"] == validation.file_sha(path)


@pytest.mark.parametrize("damage", [None, "missing_review", "missing_old_fixture", "missing_new_fixture", "changed_report", "changed_source", "unrelated_consumer", "changed_consumer"])
def test_reviewed_inventory_consumes_original_and_new_native_fixtures(tmp_path, monkeypatch, damage):
    handoff, old, new, body, seal_review = _source_review_case(tmp_path, monkeypatch)
    request = seal_review()
    review = handoff.reviewed_source_transition(request)
    family = "auxiliary"
    data = tmp_path / "data"
    _, report, _, current_path, value, seal_current = _fixture(data, family)
    old_code, new_code = review["pairs"][family]
    historical = dict(value, code_sha256=old_code)
    historical["receipt_sha256"] = generation.digest({k: v for k, v in historical.items() if k != "receipt_sha256"})
    old_path = current_path.with_name(family + "_" + old_code + ".json")
    old_path.write_text(json.dumps(historical))
    original_ref = dict(path=str(old_path), sha256=validation.file_sha(old_path))
    payload = json.loads(report.read_text())
    contract = payload["policy_generation"]
    contract.update(code_sha256=old_code, fixture_receipt=original_ref,
                    retry_key=generation.digest([family, contract["source_generation"], old_code, contract["source_state"]]))
    contract["contract_sha256"] = generation.digest({k: v for k, v in contract.items() if k != "contract_sha256"})
    report.write_text(json.dumps(payload))
    observed = generation.observations(new, DAY, data_root=data)[0]
    assert handoff.current_fixture_observation(observed, data)["current_fixture_reason"] == "successor_code_pair_unreviewed"
    value["reviewed_source_transitions"] = [review["reference"]]
    seal_current()
    if damage == "missing_review":
        request.unlink()
    elif damage == "missing_old_fixture":
        old_path.unlink()
    elif damage == "missing_new_fixture":
        current_path.unlink()
    elif damage == "changed_report":
        report.write_text("{}")
    elif damage == "changed_source":
        (new / "src/engine/shared.py").write_text("value = 3\n")
    if damage in {"unrelated_consumer", "changed_consumer"}:
        import shutil
        consumer = tmp_path / "later-consumer"
        shutil.copytree(new, consumer)
        changed = "holding_vote" if damage == "unrelated_consumer" else family
        (consumer / "src/engine" / (changed + ".py")).write_text("value = 3\n")
        monkeypatch.setattr(generation, "ENGINE", consumer / "src/engine")
        with pytest.raises(ValueError, match="source_review_incomplete_change_inventory"):
            handoff.reviewed_source_transition(request)
        if damage == "unrelated_consumer":
            scoped = handoff.reviewed_source_transition(request, consumer_family=family)
            assert set(scoped["pairs"]) == {family}
            with pytest.raises(ValueError, match="source_review_incomplete_change_inventory"):
                handoff.reviewed_source_transition(request, consumer_family=changed)
    before = report.read_bytes()
    result = handoff.current_fixture_observation(observed, data)
    invalid = damage not in {None, "unrelated_consumer"}
    assert result["status"] == ("unverified" if invalid else "verified"), result
    assert report.read_bytes() == before
    assert result["source_state"] == "valid_empty" and result["comparison_state"] == "insufficient_sample"
    assert result.get("allowed_runtime_apply", False) is False
    if not damage:
        assert result["preserved_historical_fixture"] == original_ref
        assert result["reviewed_source_transition"] == review["reference"]
        assert result["historical_contract_status"] == "unverified" and result["native_validated"] is False


def test_consumer_inventory_keeps_missing_reports_and_report_only_role(tmp_path, monkeypatch):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    rows = handoff.consumer_inventory(tmp_path, DAY)
    assert {r["family"] for r in rows} == set(generation.COMPONENTS)
    assert all(r["role"] == "report_only" and r["observation"] is None for r in rows)
    monkeypatch.setattr(validation, "PLANS", {})
    with pytest.raises(ValueError, match="capability_consumer_registry_incomplete"):
        handoff.consumer_inventory(tmp_path, DAY)


def test_fixture_publisher_requires_complete_review_before_reusing_receipt(tmp_path, monkeypatch):
    handoff, old, new, body, seal_review = _source_review_case(tmp_path, monkeypatch)
    request = seal_review()
    review = handoff.reviewed_source_transition(request)
    data = tmp_path / "data"
    _, _, _, _, value, seal = _fixture(data, "auxiliary")
    with pytest.raises(ValueError, match="fixture_existing_source_review_differs"):
        writer.validate("auxiliary", data, source_date=DAY, target_date="2026-10-15", source_reviews=[request])
    value["reviewed_source_transitions"] = [review["reference"]]
    seal()
    result = writer.validate("auxiliary", data, source_date=DAY, target_date="2026-10-15", source_reviews=[request])
    assert result["status"] == "verified_existing" and result["runtime_effect"] is False
    body["reviewed_families"].pop()
    with pytest.raises(ValueError, match="source_review_incomplete_change_inventory"):
        writer.validate("auxiliary", data, source_date=DAY, target_date="2026-10-15", source_reviews=[seal_review()])


@pytest.mark.parametrize("family", validation.PLANS)
@pytest.mark.parametrize("basis", ["report_origin", "live_intermediate", "same_code"])
def test_fixture_publisher_binds_preserved_report_origin_before_running_tests(tmp_path, monkeypatch, family, basis):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    current = "c" * 64
    original = current if basis == "same_code" else "a" * 64
    transition = ["b" * 64 if basis == "live_intermediate" else original, current]
    monkeypatch.setattr(handoff, "reviewed_source_transition", lambda _: dict(reference={}, pairs={family:transition}))
    monkeypatch.setattr(generation, "code_generation", lambda _:current)
    monkeypatch.setattr(generation, "observations", lambda *a,**k:[dict(family=family,code_sha256=original)])
    class ReadyForTests(Exception): pass
    def reached(*a): raise ReadyForTests()
    monkeypatch.setattr(validation, "plan_identity", reached)
    if basis == "live_intermediate":
        with pytest.raises(ValueError, match="fixture_source_review_missing_report_origin"):
            writer.validate(family,tmp_path,source_date=DAY,target_date="2026-10-15",source_reviews=["review"])
    else:
        with pytest.raises(ReadyForTests):
            writer.validate(family,tmp_path,source_date=DAY,target_date="2026-10-15",source_reviews=["review"])


@pytest.mark.parametrize("damage", [None, "consumer_code"])
def test_source_review_tracks_code_identity_across_same_code_release_roots(tmp_path, monkeypatch, damage):
    import shutil
    handoff, old, issuer, body, seal = _source_review_case(tmp_path, monkeypatch)
    request = seal()
    consumer = tmp_path / "same-code-consumer"
    shutil.copytree(issuer, consumer)
    monkeypatch.setattr(validation, "ROOT", consumer)
    monkeypatch.setattr(generation, "ENGINE", consumer / "src/engine")
    if damage:
        (consumer / "src/engine/shared.py").write_text("value = 3\n")
        with pytest.raises(ValueError, match="source_review_incomplete_change_inventory"):
            handoff.reviewed_source_transition(request)
    else:
        assert set(handoff.reviewed_source_transition(request)["pairs"]) == set(validation.PLANS)


@pytest.mark.parametrize("damage", [None, "unreviewed_owner", "reader_removal"])
def test_source_review_extends_only_existing_capability_reader_membership(tmp_path, monkeypatch, damage):
    import subprocess
    handoff, old, new, body, seal = _source_review_case(tmp_path, monkeypatch)
    extra = "new_execution_owner.py" if damage == "unreviewed_owner" else "monitoring/policy_generation_code_handoff.py"
    for role, root in (("origin", old), ("current", new)):
        file = root / "src/engine" / extra
        file.parent.mkdir(exist_ok=True)
        file.write_text("value = " + ("1" if role == "origin" else "2") + "\n")
        if (role == "current" and damage != "reader_removal") or (role == "origin" and damage == "reader_removal"):
            registry = root / "src/engine/monitoring/policy_generation_contract.py"
            registry.write_text(registry.read_text().replace("('shared.py',)", repr(("shared.py", extra))))
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "dependency"], cwd=root, check=True, capture_output=True)
        body[role + "_git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    monkeypatch.setattr(generation, "COMMON_CODE_COMPONENTS", ("shared.py",) if damage == "reader_removal" else ("shared.py", extra))
    body["reviewed_files"]["src/engine/" + extra] = dict(before=validation.file_sha(old / "src/engine" / extra), after=validation.file_sha(new / "src/engine" / extra))
    if damage:
        with pytest.raises(ValueError, match="source_review_component_membership_changed"):
            handoff.reviewed_source_transition(seal())
    else:
        assert set(handoff.reviewed_source_transition(seal())["pairs"]) == set(validation.PLANS)


@pytest.mark.parametrize(
    "damage", [None, "original_absent", "omitted_review", "unregistered_owner", "origin_deleted", "current_deleted"]
)
def test_source_review_preserves_original_auxiliary_inventory_while_binding_new_consumers(
    tmp_path, monkeypatch, damage
):
    import copy
    import subprocess

    handoff, old, new, body, seal = _source_review_case(tmp_path, monkeypatch)
    extra = (
        "scalping/unreviewed_owner.py"
        if damage == "unregistered_owner"
        else "scalping/reversal_extended_registration.py"
    )
    updated = copy.deepcopy(generation.COMPONENTS)
    updated["auxiliary"] = (*updated["auxiliary"], extra)
    for role, root in (("origin", old), ("current", new)):
        file = root / "src/engine" / extra
        file.parent.mkdir(parents=True, exist_ok=True)
        if role != "origin" or damage != "original_absent":
            file.write_text("value = " + ("1" if role == "origin" else "2") + "\n")
        if role == "current":
            registry = root / "src/engine/monitoring/policy_generation_contract.py"
            registry.write_text(
                "COMPONENTS = "
                + repr(updated)
                + "\nCOMMON_CODE_COMPONENTS = "
                + repr(generation.COMMON_CODE_COMPONENTS)
                + "\n"
            )
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-qm",
                "auxiliary consumer",
            ],
            cwd=root,
            check=True,
            capture_output=True,
        )
        body[role + "_git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
    monkeypatch.setattr(generation, "COMPONENTS", updated)
    if damage != "omitted_review":
        body["reviewed_files"]["src/engine/" + extra] = dict(
            before=(
                None
                if damage == "original_absent"
                else validation.file_sha(old / "src/engine" / extra)
            ),
            after=validation.file_sha(new / "src/engine" / extra),
        )
    if damage == "origin_deleted":
        (old / "src/engine" / extra).unlink()
    elif damage == "current_deleted":
        (new / "src/engine" / extra).unlink()
    if damage in {"omitted_review", "unregistered_owner", "origin_deleted", "current_deleted"}:
        with pytest.raises((ValueError, OSError)):
            handoff.reviewed_source_transition(seal())
    else:
        result = handoff.reviewed_source_transition(seal())
        original = generation.digest(
            {
                "auxiliary.py": validation.file_sha(old / "src/engine/auxiliary.py"),
                "shared.py": validation.file_sha(old / "src/engine/shared.py"),
            }
        )
        assert result["pairs"]["auxiliary"][0] == original
        assert result["pairs"]["auxiliary"][1] == generation.code_generation(
            "auxiliary"
        )


@pytest.mark.parametrize('damage', [None, 'missing', 'bytes', 'state', 'proof', 'count', 'path', 'schema', 'chunk', 'encoding', 'generation'])
def test_partitioned_cancel_report_native_intake_preserves_exact_semantics(tmp_path, monkeypatch, damage):
    """The native generation reader must consume the producer's bounded root."""
    import base64, gzip
    from src.engine.automation import entry_cancel_wait_tuning as owner
    from src.engine.lifecycle import research_storage as storage
    data = tmp_path / 'data'
    _, report, _, _, _, _ = _fixture(data, 'entry_cancel_wait')
    payload = json.loads(report.read_bytes())
    state = dict(through_date=DAY, source_events=[dict(
        evaluation_attempt_id='exact-attempt-'+str(i), cost=None,
        raw_context='original source context '+str(i)+'x'*1024) for i in range(50)])
    state['sha256'] = owner._digest(state)
    payload['economic_state'] = state
    payload['policy_generation'] = generation.native(
        payload, family='entry_cancel_wait', day=DAY, data_root=data,
        source_state='source_gap', comparison_state='insufficient_sample',
        handoff_state='incumbent_carried')
    payload['proof_sha256'] = owner._digest({k:v for k,v in payload.items()
        if k not in ('generated_at','proof_sha256')})
    monkeypatch.setattr(validation, 'NATIVE_REPORT_LIMIT', 16384)
    wire = owner.encode_report_storage(payload, data_root=data)
    assert wire != payload and wire['economic_state']['schema'] == owner.ECONOMIC_STORAGE_SCHEMA
    root = owner._state_storage_root(data, DAY, state['sha256'])
    if damage == 'missing':
        (root / wire['economic_state']['tree']['path']).unlink()
    elif damage == 'bytes':
        (root / wire['economic_state']['tree']['path']).write_text('{}')
    elif damage == 'state':
        wire['economic_state']['sha256'] = 'f'*64
    elif damage == 'proof':
        wire['proof_sha256'] = 'f'*64
    elif damage == 'count':
        wire['economic_state']['serialized_bytes'] -= 1
    elif damage == 'path':
        wire['economic_state']['tree']['path'] = '../foreign.json'
    elif damage == 'schema':
        wire['economic_state']['schema'] += '_unknown'
    elif damage in {'chunk', 'encoding'}:
        wire['economic_state']['tree'] = storage.write_tree(root, [dict(index=i,
            gzip_base64=base64.b64encode((b'not gzip' if damage == 'encoding' and i == 0 else gzip.compress(b'x'*(16385 if i == 0 else 1), mtime=0))).decode())
            for i in range(wire['economic_state']['tree']['count'])])
    report.write_text(json.dumps(wire))
    original = report.read_bytes()
    if damage == 'generation':
        real = owner.decode_report_storage
        def advance(value, **kwargs):
            restored = real(value, **kwargs)
            report.write_bytes(original + b'\n')
            return restored
        monkeypatch.setattr(owner, 'decode_report_storage', advance)
    if damage:
        with pytest.raises((ValueError, OSError)):
            validation.read_native_report(data, 'entry_cancel_wait', DAY)
    else:
        actual, sha = validation.read_native_report(data, 'entry_cancel_wait', DAY)
        assert actual == payload
        assert sha == hashlib.sha256(original).hexdigest()
        assert report.stat().st_size < validation.NATIVE_REPORT_LIMIT
        assert generation.inspect(actual['policy_generation'], family='entry_cancel_wait',
            day=DAY, payload=actual, data_root=data)['observation_complete']
        assert actual['economic_state']['source_events'][0]['cost'] is None
        assert owner._bounded_semantic_json(report)[1] == sha
    if damage != 'generation':
        assert report.read_bytes() == original
