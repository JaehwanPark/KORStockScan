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


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    data = tmp_path / "workspace/data"
    managed = tmp_path / "workspace-runtime-releases"
    previous, selected = managed / "old", managed / "new"
    previous.mkdir(parents=True)
    selected.mkdir()
    monkeypatch.setattr(handoff, "DATA_DIR", data)
    monkeypatch.setattr(readiness, "DATA_DIR", data)
    monkeypatch.setattr(handoff, "_selection", lambda **kwargs: (selected, NEW))
    monkeypatch.setattr(handoff, "is_krx_trading_day", lambda day: day.weekday() < 5)
    monkeypatch.setattr(handoff.bootstrap, "env_path", lambda day: data / f"{day}.env")
    monkeypatch.setattr(handoff.bootstrap, "manifest_path", lambda day: data / f"{day}.manifest.json")
    monkeypatch.setattr(handoff.bootstrap, "verify_bootstrap", lambda day, **kwargs:
                        {"status": "pass", "findings": [], "manifest_sha256": "policy-unchanged"})
    monkeypatch.setattr(handoff.subprocess, "check_output", lambda command, **kwargs:
                        OLD + "\n" if "rev-parse" in command else "")
    monkeypatch.setattr(handoff, "_identity", lambda pid:
                        {"pid": pid, "start_ticks": "42", "cwd": str((previous if pid == 1 else selected) / "src")})
    _json(handoff._preopen_path(DAY), {"target_date": DAY, "status": "succeeded", "exit_code": 0,
                                      "runtime_env_exists": True, "selected_release_commit": OLD,
                                      "updated_at": NOW.isoformat()})
    handoff.bootstrap.env_path(DAY).write_text("export POLICY=unchanged\n")
    _json(handoff.bootstrap.manifest_path(DAY), {"policy": "unchanged"})
    prepared_root = data / "runtime/policy_bootstrap/prepared" / DAY
    receipt = prepared_root / "generation/readiness.json"
    _json(receipt, {"status": "prepared_verified"})
    _json(prepared_root / "latest.json", {"receipt_path": str(receipt), "receipt_sha256": handoff._sha(receipt)})
    def prepare():
        return handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM, now=NOW)
    return data, previous, selected, prepare


def test_intraday_handoff_preserves_preopen_and_policy_files_then_binds_new_pid(fixture):
    data, _, _, prepare = fixture
    before = {str(path): path.read_bytes() for path in data.rglob("*") if path.is_file()}
    assert prepare()["status"] == "pass"
    assert all(Path(path).read_bytes() == content for path, content in before.items())
    result = readiness.verify_preopen_completion(DAY, NEW, now=NOW)
    assert result["status"] == "pass" and result["basis"] == "intraday_policy_preserving_handoff"
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    assert consumed["actual_pid_consumed"] is True
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(hours=2))["status"] == "pass"
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(days=1))["status"] == "fail"


def test_read_only_selection_does_not_relax_prepare_or_consume_cwd(fixture, monkeypatch):
    data, _, selected, prepare = fixture
    assert prepare()['status'] == 'pass'
    assert handoff.consume(DAY, pid=2, now=NOW)['status'] == 'pass'
    frozen = {str(path): path.read_bytes() for path in data.rglob('*') if path.is_file()}
    monkeypatch.setattr(handoff, '_selection', NATIVE_SELECTION)
    monkeypatch.setattr(handoff, 'selected_release', lambda workspace: (selected, NEW))
    monkeypatch.chdir(data.parent)
    with pytest.raises(ValueError, match='selected_root_required'):
        prepare()
    with pytest.raises(ValueError, match='selected_root_required'):
        handoff.consume(DAY, pid=2, now=NOW)
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(hours=2))['status'] == 'pass'
    assert all(Path(path).read_bytes() == value for path, value in frozen.items())


@pytest.mark.parametrize('damage', [
    None, 'manifest', 'env', 'verification', 'pid', 'consumption', 'missing_consumption', 'next_day',
])
def test_postclose_generation_accepts_only_native_preserved_intraday_pid(fixture, monkeypatch, damage):
    data, _, selected, prepare = fixture
    bootstrap = handoff.bootstrap
    monkeypatch.setattr(bootstrap, 'DATA_DIR', data)
    manifest = {'target_date': DAY, 'selected_release_sha': OLD,
                'manifest_sha256': 'policy-unchanged'}
    _json(bootstrap.manifest_path(DAY), manifest)
    assert prepare()['status'] == 'pass'
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    assert consumed['actual_pid_consumed'] is True
    selection = {'schema': 'runtime_release_selection_v1', 'git_commit': NEW,
                 'release_root': str(selected)}
    _json(data / 'runtime/runtime_release_selection.json', selection)
    verification = {'target_date': DAY, 'status': 'pass', 'passed': True,
                    'pid': 2, 'pid_passed': True, 'pid_env_available': True}
    _json(bootstrap.verify_path(DAY), verification)
    check = handoff.verify
    clock = NOW + timedelta(days=1) if damage == 'next_day' else NOW
    monkeypatch.setattr(handoff, 'verify', lambda day, commit: check(day, commit, now=clock))
    if damage == 'manifest':
        _json(bootstrap.manifest_path(DAY), {**manifest, 'changed': True})
    elif damage == 'env':
        bootstrap.env_path(DAY).write_text('POLICY=changed\n')
    elif damage == 'verification':
        _json(bootstrap.verify_path(DAY), {**verification, 'pid': 1})
    elif damage == 'pid':
        verification['pid'] = 1
        _json(bootstrap.verify_path(DAY), verification)
    elif damage == 'consumption':
        _json(handoff._paths(DAY, NEW)[1], {**consumed, 'handoff_sha256': 'changed'})
    elif damage == 'missing_consumption':
        handoff._paths(DAY, NEW)[1].unlink()
    result = bootstrap.release_selection_for_generation(data, manifest, verification)
    if damage is None:
        assert result['status'] == 'intraday_preserved', result
        assert result['selection']['git_commit'] == NEW
        assert result['original_manifest_release_commit'] == OLD
    else:
        assert result['status'] == 'invalid', result


@pytest.mark.parametrize("mutation", ["env", "manifest", "preopen", "prepared", "commit", "ttl", "consumption"])
def test_intraday_handoff_rejects_changed_generation_identity_and_expired_launch(fixture, mutation):
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


@pytest.mark.parametrize("fault", ["authority", "native_fail", "old_pid", "preopen_fail", "next_day", "dirty"])
def test_intraday_prepare_rejects_missing_authority_or_native_custody(fixture, monkeypatch, fault):
    _, previous, _, _ = fixture
    confirm, current = handoff.CONFIRM, NOW
    if fault == "authority":
        confirm = ""
    elif fault == "native_fail":
        monkeypatch.setattr(handoff.bootstrap, "verify_bootstrap", lambda *args, **kwargs:
                            {"status": "fail", "findings": ["source_receipt_hash_mismatch"]})
    elif fault == "old_pid":
        monkeypatch.setattr(handoff, "_identity", lambda pid: {"pid": pid, "cwd": "/other/src"})
    elif fault == "preopen_fail":
        _json(handoff._preopen_path(DAY), {"status": "failed"})
    elif fault == "next_day":
        current += timedelta(days=1)
    elif fault == "dirty":
        monkeypatch.setattr(handoff.subprocess, "check_output", lambda command, **kwargs:
                            OLD if "rev-parse" in command else " M src/runtime.py")
    with pytest.raises((ValueError, KeyError)):
        handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=confirm, now=current)
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


def test_prepared_verifier_preserves_original_receipt_and_checks_sources(fixture, monkeypatch):
    data, _, selected, prepare = fixture
    prepared_root = data / "runtime/policy_bootstrap/prepared" / DAY
    monkeypatch.setattr(readiness, "PREPARED_DIR", prepared_root.parent)
    source = {"source_proof": "unchanged"}
    monkeypatch.setattr(readiness, "_source_receipts", lambda *args, **kwargs: source)
    selection = data / "runtime/runtime_release_selection.json"
    _json(selection, {"git_commit": NEW, "release_root": str(selected)})
    monkeypatch.setattr(readiness, "_selected_release", lambda: ({}, selection, NEW))
    live_env = handoff.bootstrap.env_path(DAY)
    live_manifest = handoff.bootstrap.manifest_path(DAY)
    monkeypatch.setattr(handoff.bootstrap, "env_path", lambda day, output_dir=None:
                        Path(output_dir) / "env" if output_dir else live_env)
    monkeypatch.setattr(handoff.bootstrap, "manifest_path", lambda day, output_dir=None:
                        Path(output_dir) / "manifest" if output_dir else live_manifest)
    receipt_path = prepared_root / "generation/readiness.json"
    output = receipt_path.parent
    for path in (output / "env", output / "manifest", handoff.bootstrap.verify_path(DAY, output_dir=output)):
        _json(path, {})
    receipt = {"schema": "next_preopen_readiness_v1", "status": "prepared_verified", "target_date": DAY,
               "source_date": "2026-09-30", "selected_release_commit": OLD, "selection_sha256": "old",
               "actual_pid_consumed": False, "runtime_effect": False, "manifest_content_sha256": "policy-unchanged",
               "manifest_file_sha256": handoff._sha(output / "manifest"), "env_sha256": handoff._sha(output / "env"),
               "verification_sha256": handoff._sha(handoff.bootstrap.verify_path(DAY, output_dir=output)), **source}
    _json(receipt_path, receipt)
    _json(prepared_root / "latest.json", {"target_date": DAY, "receipt_path": str(receipt_path),
                                          "receipt_sha256": handoff._sha(receipt_path)})
    prepare()
    result = readiness.verify_prepared(DAY, require_today=True, now=NOW)
    assert result["status"] == "pass"
    assert result["selected_release_commit"] == NEW and result["preserved_preopen_commit"] == OLD
    assert result["actual_pid_consumed"] is False
    monkeypatch.setattr(readiness, "_source_receipts", lambda *args, **kwargs: {"source_proof": "changed"})
    assert readiness.verify_prepared(DAY, now=NOW)["status"] == "fail"
