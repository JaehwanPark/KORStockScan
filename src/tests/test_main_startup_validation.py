"""Parent transaction tests using a real isolated early-entrypoint child.

Prepared-policy intake and env construction are unit fixtures here. The child
entrypoint, isolation, PID identity, timeouts and terminal publication are real.
Native active-policy interpretation is covered by the loader contract suite.
"""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from src.engine.automation import main_startup_validation as validation
from src.engine.infrastructure.main_policy_loading import CONSUMER_IDS


ROOT = Path(__file__).resolve().parents[2]
DAY = "2026-10-19"
CODE_FILES = (
    "src/bot_main.py", "src/run_bot.sh",
    "src/engine/automation/main_startup_validation.py",
    "src/engine/infrastructure/startup_validation_isolation.py",
    "src/engine/infrastructure/startup_validation_code_context.py",
    "src/engine/infrastructure/main_policy_environment.sh",
)


@pytest.fixture
def transaction(tmp_path, monkeypatch):
    workspace, code = tmp_path / "workspace", tmp_path / "code"
    workspace.mkdir()
    for item in CODE_FILES:
        destination = code / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / item, destination)
    for package in ("src", "src/engine", "src/engine/automation", "src/engine/infrastructure"):
        (code / package / "__init__.py").touch()
    isolation = code / "src/engine/infrastructure/startup_validation_isolation.py"
    with isolation.open("a") as stream:
        stream.write("""
_real_install_validation_isolation = install_validation_isolation
def install_validation_isolation(*args, **kwargs):
    if os.environ.get('FIXTURE_MODE') == 'isolation_unavailable':
        raise IsolationUnavailable('fixture_isolation_unavailable')
    return _real_install_validation_isolation(*args, **kwargs)
""")
    (code / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    loader = code / "src/engine/infrastructure/main_policy_loading.py"
    loader.write_text(f"""
import hashlib, os, pathlib, socket, time
CONSUMER_IDS = frozenset({sorted(CONSUMER_IDS)!r})
def load_main_policies(**kwargs):
    mode = os.environ.get('FIXTURE_MODE', 'passed')
    if mode == 'timeout':
        time.sleep(360)
    if mode == 'crash':
        os._exit(17)
    if mode == 'caught_write':
        try:
            pathlib.Path(os.environ['FIXTURE_PROTECTED']).write_text('CORRUPT')
        except PermissionError:
            pass
    if mode == 'caught_network':
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except PermissionError:
            pass
    rows = {{key: dict(status='loaded', native_status='loaded',
        loaded_object_sha256=hashlib.sha256(key.encode()).hexdigest(),
        policy_sha256=None, source_hashes={{}}) for key in CONSUMER_IDS}}
    if mode == 'missing_consumer':
        rows.pop(sorted(rows)[0])
    if mode == 'failed_consumer':
        rows[sorted(rows)[0]]['status'] = 'failed'
    return dict(schema='main_policy_loading_v1', target_date=kwargs['target_date'],
        observed_at_kst=kwargs['observed_at'].isoformat(),
        status='failed' if mode == 'failed_consumer' else 'passed',
        consumer_results=rows, runtime_effect=(mode == 'authority_leak'),
        actual_pid_consumed=False)
""")
    subprocess.run(["git", "init", "-q", str(code)], check=True)
    subprocess.run(["git", "-C", str(code), "add", "src"], check=True)
    subprocess.run(
        ["git", "-C", str(code), "-c", "user.name=Validation Fixture",
         "-c", "user.email=fixture@example.invalid", "commit", "-qm", "isolated fixture"], check=True,
    )
    commit = subprocess.check_output(["git", "-C", str(code), "rev-parse", "HEAD"], text=True).strip()
    protected = workspace / "protected-policy.json"
    protected.write_text('{"original": true}\n')
    receipt = workspace / "prepared.json"
    receipt.write_text('{"fixture": true}\n')
    bootstrap = workspace / "bootstrap.env"
    bootstrap.write_text("KORSTOCKSCAN_FIXTURE_POLICY=bound\n")
    intake = dict(
        selected_root=code, selected_commit=commit, receipt_path=receipt,
        receipt={"env_path": str(bootstrap), "activation_candidate": {}},
        manifest={"target_date": DAY, "env_overrides": {}},
        source_hashes={str(protected): validation._sha(protected), str(receipt): validation._sha(receipt),
                       str(bootstrap): validation._sha(bootstrap)},
    )
    binding = dict(basis="reviewed_candidate_handoff", root=str(code), commit=commit, contracts={})
    monkeypatch.setattr(validation, "_intake", lambda *args: intake)
    monkeypatch.setattr(validation, "_bind_execution", lambda *args: binding)
    monkeypatch.setattr(validation, "_native_preparation_check", lambda *args: {"status": "pass"})
    state = {"mode": "passed", "workspace": workspace, "code": code, "protected": protected,
             "intake": intake, "binding": binding, "loader": loader}

    def compose(*args, **kwargs):
        return {"PATH": os.defpath, "PYTHONPATH": str(code), "PYTHONDONTWRITEBYTECODE": "1",
                "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                "KORSTOCKSCAN_FIXTURE_POLICY": "bound", "FIXTURE_MODE": state["mode"],
                "FIXTURE_PROTECTED": str(protected)}

    state["compose"] = compose
    monkeypatch.setattr(validation, "_compose_environment", compose)
    return state


def _run(transaction, **kwargs):
    return validation.run_validation(
        workspace=transaction["workspace"], target_date=DAY,
        execution_root=transaction["code"], candidate=True, **kwargs,
    )


def _assert_failed_terminal(final, receipt):
    assert final["status"] == "failed"
    assert final["load_check_passed"] is False
    assert final["actual_pid_consumed"] is False
    assert final["runtime_effect"] is False
    assert final["allowed_runtime_apply"] is False
    assert final["findings"]
    assert json.loads(receipt.read_text()) == final
    assert not list(receipt.parent.glob(".final.json.*"))


def test_real_early_child_terminates_with_exact_identity_and_nonempty_consumer_receipt(transaction):
    before = transaction["protected"].read_bytes()
    final, receipt = _run(transaction)
    assert final["status"] == "passed", (final, (receipt.parent / "child-output.log").read_text())
    assert final["child_exit_code"] == 0
    assert final["child_terminated"] is True
    assert final["load_check_passed"] is True
    assert final["protected_sources_unchanged"] is True
    assert set(final["consumer_results"]) == CONSUMER_IDS
    assert len(final["consumer_results"]) > 1
    child = json.loads((receipt.parent / "child.json").read_text())
    assert child["validation_pid"] == final["validation_pid"] != os.getpid()
    assert child["validation_start_ticks"] == final["validation_start_ticks"]
    assert not Path(f'/proc/{child["validation_pid"]}').exists()
    assert child["request_sha256"] == final["input_manifest_sha256"]
    assert (receipt.parent / "isolation.jsonl").read_bytes() == b""
    assert transaction["protected"].read_bytes() == before
    assert not (transaction["code"] / "logs").exists()


@pytest.mark.parametrize("mode", [
    "failed_consumer", "missing_consumer", "caught_write", "caught_network", "crash",
])
def test_real_child_failure_never_becomes_parent_pass(transaction, mode):
    transaction["mode"] = mode
    before = transaction["protected"].read_bytes()
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True
    assert transaction["protected"].read_bytes() == before
    if mode in {"caught_write", "caught_network"}:
        assert (receipt.parent / "isolation.jsonl").read_bytes()


def test_loader_cannot_report_runtime_authority_and_receive_validation_pass(transaction):
    transaction["mode"] = "authority_leak"
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True


def test_missing_os_isolation_never_enters_loader_or_publishes_pass(transaction):
    transaction["mode"] = "isolation_unavailable"
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True
    assert "fixture_isolation_unavailable" in " ".join(final["findings"])
    assert not final.get("consumer_results")


def test_timeout_kills_only_the_owned_validation_child_and_publishes_failure(transaction):
    transaction["mode"] = "timeout"
    final, receipt = _run(transaction, timeout=1)
    _assert_failed_terminal(final, receipt)
    assert "startup_child_timeout" in " ".join(final["findings"])
    assert final["child_terminated"] is True
    assert not Path(f'/proc/{final["validation_pid"]}').exists()
    assert os.getpid() != final["validation_pid"]


def test_intake_failure_has_atomic_failed_receipt_and_never_creates_child(transaction, monkeypatch):
    def failed(*args):
        raise ValueError("fixture_required_prepared_source_missing")
    monkeypatch.setattr(validation, "_intake", failed)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["failure_phase"] == "intake"
    assert "validation_pid" not in final
    assert not (receipt.parent / "child.json").exists()


def test_source_change_during_environment_composition_is_rejected_before_child(transaction, monkeypatch):
    def racing_compose(*args, **kwargs):
        values = transaction["compose"](*args, **kwargs)
        transaction["protected"].write_text("new-generation\n")
        return values
    monkeypatch.setattr(validation, "_compose_environment", racing_compose)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert "startup_source_changed" in " ".join(final["findings"])
    assert "validation_pid" not in final


def test_last_native_recheck_cannot_change_a_protected_source_then_publish_pass(transaction, monkeypatch):
    def changed_at_final_check(*args):
        transaction["protected"].write_text("changed-by-final-verifier\n")
        return {"status": "pass"}
    monkeypatch.setattr(validation, "_native_preparation_check", changed_at_final_check)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True
    assert "startup_source_changed" in " ".join(final["findings"])


def test_any_native_code_dependency_change_is_bound_before_child(transaction, monkeypatch):
    def changed_loader(*args, **kwargs):
        values = transaction["compose"](*args, **kwargs)
        dependency = transaction["code"] / "src/engine/__init__.py"
        dependency.write_text("NATIVE_GENERATION = 'changed'\n")
        return values
    monkeypatch.setattr(validation, "_compose_environment", changed_loader)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert "startup_source_changed" in " ".join(final["findings"])
    assert "validation_pid" not in final


def test_execution_binding_change_after_successful_child_invalidates_parent_pass(transaction, monkeypatch):
    calls = []
    def changed_binding(*args, **kwargs):
        calls.append(True)
        result = dict(transaction["binding"])
        if len(calls) > 1:
            result["commit"] = "b" * 40
        return result
    monkeypatch.setattr(validation, "_bind_execution", changed_binding)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert "startup_execution_binding_changed" in " ".join(final["findings"])
    assert final["child_terminated"] is True


def test_atomic_receipt_failure_keeps_original_bytes_and_removes_temporary(tmp_path, monkeypatch):
    receipt = tmp_path / "final.json"
    original = b'{"status":"older-original"}\r\n'
    receipt.write_bytes(original)
    def failed_replace(*args):
        raise OSError("fixture_replace_failed")
    monkeypatch.setattr(validation.os, "replace", failed_replace)
    with pytest.raises(OSError, match="fixture_replace_failed"):
        validation._atomic(receipt, {"status": "new"})
    assert receipt.read_bytes() == original
    assert list(tmp_path.iterdir()) == [receipt]


def test_child_request_tamper_is_rejected_before_loader_import(transaction, tmp_path):
    run = tmp_path / ("a" * 32)
    run.mkdir(mode=0o700)
    request = dict(schema=validation.SCHEMA, run_id=run.name, target_date=DAY,
                   execution_release_root=str(transaction["code"]),
                   execution_release_commit=transaction["binding"]["commit"],
                   request_sha256="0" * 64)
    path = run / "request.json"
    path.write_text(json.dumps(request))
    result = subprocess.run(
        [sys.executable, "-B", str(transaction["code"] / "src/bot_main.py"),
         "--validate-startup", str(path)], cwd=transaction["code"],
        env={"PATH": os.defpath, "PYTHONPATH": str(transaction["code"]),
             "OPENBLAS_NUM_THREADS": "1"}, start_new_session=True,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "startup_request_digest_invalid" in result.stderr
    assert not (run / "isolation.jsonl").exists()
    assert not (run / "child.json").exists()
    assert not (transaction["code"] / "logs").exists()


@pytest.mark.parametrize("contents", [
    "KORSTOCKSCAN_X=$(touch injected)\n",
    "KORSTOCKSCAN_X=value; touch injected\n",
    "KORSTOCKSCAN_X=value\nKORSTOCKSCAN_X=other\n",
    "source other.env\n",
    "PATH=/tmp/untrusted\n",
    "BASH_ENV=/tmp/untrusted\n",
])
def test_environment_data_parser_refuses_shell_or_nonpolicy_authority(tmp_path, contents):
    source = tmp_path / "input.env"
    source.write_text(contents)
    with pytest.raises(ValueError):
        validation._assignment_values(source)
    assert not (tmp_path / "injected").exists()


def test_environment_data_parser_preserves_quoted_shell_characters_as_literal_data(tmp_path):
    source = tmp_path / "input.env"
    source.write_text("export KORSTOCKSCAN_X='$(touch injected)'\n")
    assert validation._assignment_values(source) == {"KORSTOCKSCAN_X": "$(touch injected)"}
    assert not (tmp_path / "injected").exists()


def test_noninteractive_shell_does_not_execute_polluted_parent_bash_env(tmp_path, monkeypatch):
    code = tmp_path / "project"
    for directory in (code / "src/engine/infrastructure", code / ".venv/bin", code / "data/config"):
        directory.mkdir(parents=True)
    shutil.copyfile(ROOT / "src/engine/infrastructure/main_policy_environment.sh",
                    code / "src/engine/infrastructure/main_policy_environment.sh")
    python = code / ".venv/bin/python"
    python.write_text("#!/bin/sh\nprintf '%s\\n' 'export KORSTOCKSCAN_STUB_NATIVE=true'\n")
    python.chmod(0o755)
    bootstrap = code / "bootstrap.env"
    bootstrap.write_text("KORSTOCKSCAN_FIXTURE_POLICY=bound\n")
    (code / "data/config/native_owner_custody.env").write_text("KORSTOCKSCAN_NATIVE_CUSTODY_FIXTURE=true\n")
    run = tmp_path / "private"
    run.mkdir(mode=0o700)
    sentinel = tmp_path / "unwanted-shell-execution.txt"
    bash_env = tmp_path / "polluted-bash-env.sh"
    bash_env.write_text(f"printf unsafe > '{sentinel}'\n")
    monkeypatch.setenv("BASH_ENV", str(bash_env))
    environment = validation._compose_environment(code, DAY, bootstrap, run)
    assert environment["KORSTOCKSCAN_FIXTURE_POLICY"] == "bound"
    assert not sentinel.exists()
    assert "BASH_ENV" not in environment


def test_json_reader_rejects_fifo_without_waiting_for_a_writer(tmp_path):
    fifo = tmp_path / "not-a-regular-source.json"
    os.mkfifo(fifo)
    started = time.monotonic()
    with pytest.raises(ValueError, match="startup_input_not_regular_bounded"):
        validation._read(fifo)
    assert time.monotonic() - started < 1


def test_first_read_atime_change_does_not_falsify_source_mutation(tmp_path):
    source = tmp_path / "source.json"
    raw = b'{"policy":"original"}\n'
    source.write_bytes(raw)
    os.utime(source, ns=(1, source.stat().st_mtime_ns))
    assert validation._read(source) == {"policy": "original"}
    os.utime(source, ns=(1, source.stat().st_mtime_ns))
    assert validation._sha(source) == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("defect", ["isolation_type", "row_type", "source_hashes_type",
                                     "missing_consumer", "invalid_digest", "wrong_policy", "runtime_authority"])
def test_parent_independently_rejects_malformed_or_unbound_child_semantics(defect):
    rows = {name: {"status": "loaded", "loaded_object_sha256": "a" * 64,
                   "policy_sha256": "b" * 64, "source_hashes": {}} for name in CONSUMER_IDS}
    child = dict(status="passed", runtime_effect=False, actual_pid_consumed=False,
                 allowed_runtime_apply=False, findings=[], consumer_results=rows,
                 forbidden_attempt_count=0,
                 isolation=dict(no_new_privileges=True, filesystem_write_root="/fixture/private",
                                landlock_abi=8, network_access=False, process_creation=False,
                                metadata_changes=False, caught_permission_denials_fail=True))
    expected = {"main_stop": "b" * 64}
    validation._validate_child_result(child, CONSUMER_IDS, expected)
    if defect == "isolation_type":
        child["isolation"] = ["malformed"]
    elif defect == "row_type":
        rows["main_stop"] = ["malformed"]
    elif defect == "source_hashes_type":
        rows["main_stop"]["source_hashes"] = ["malformed"]
    elif defect == "missing_consumer":
        rows.pop("main_stop")
    elif defect == "invalid_digest":
        rows["main_stop"]["loaded_object_sha256"] = "invalid"
    elif defect == "wrong_policy":
        rows["main_stop"]["policy_sha256"] = "c" * 64
    else:
        child["actual_pid_consumed"] = True
    expected_error = {
        "isolation_type": "startup_child_object_contract_invalid",
        "row_type": "startup_child_consumer_invalid:main_stop",
        "source_hashes_type": "startup_child_consumer_invalid:main_stop",
        "missing_consumer": "startup_child_semantic_contract_invalid",
        "invalid_digest": "startup_child_consumer_invalid:main_stop",
        "wrong_policy": "startup_child_wrong_policy:main_stop",
        "runtime_authority": "startup_child_semantic_contract_invalid",
    }[defect]
    with pytest.raises(ValueError, match=expected_error):
        validation._validate_child_result(child, CONSUMER_IDS, expected)
