import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import next_preopen_readiness as readiness

KST = ZoneInfo("Asia/Seoul")


@pytest.mark.parametrize('clock,recovery,expected', [
    ('2026-10-06T07:34:59+09:00', True, 'prepare_exact_effective_date'),
    ('2026-10-06T07:35:00+09:00', True, 'historical_recovery_no_prepare'),
    ('2026-10-06T15:30:00+09:00', True, 'historical_recovery_no_prepare'),
    ('2026-10-07T01:00:00+09:00', True, 'historical_recovery_no_prepare'),
    ('2026-10-06T15:30:00+09:00', False, None),
])
def test_finalization_recovery_never_prepares_another_session(clock, recovery, expected):
    # Oct 5 is a KRX holiday; the original Oct 2 source belongs to Oct 6.
    kwargs = dict(recovery=recovery, now=datetime.fromisoformat(clock))
    if expected is None:
        with pytest.raises(ValueError, match='already_opened'):
            readiness.finalization_preparation_disposition('2026-10-02', '2026-10-06', **kwargs)
    else:
        assert readiness.finalization_preparation_disposition('2026-10-02', '2026-10-06', **kwargs) == expected
    with pytest.raises(ValueError, match='source_session_mismatch'):
        readiness.finalization_preparation_disposition('2026-10-02', '2026-10-07', **kwargs)


def _json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_target_after_postclose_handles_late_recovery_and_weekend(monkeypatch):
    monkeypatch.setattr(readiness, "is_krx_trading_day", lambda day: day.weekday() < 5)
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 1, 2, 0, tzinfo=KST),
    ) == "2026-10-01"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 1, 17, 0, tzinfo=KST),
    ) == "2026-10-02"
    assert readiness.target_after_postclose(
        "2026-10-02", now=datetime(2026, 10, 2, 21, 0, tzinfo=KST),
    ) == "2026-10-05"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 2, 0, 36, tzinfo=KST),
    ) == "2026-10-02"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 2, 7, 34, tzinfo=KST),
    ) == "2026-10-02"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 2, 7, 35, tzinfo=KST),
    ) == "2026-10-05"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 3, 0, 36, tzinfo=KST),
    ) == "2026-10-05"


def test_source_receipt_rejects_unclosed_controller_and_changed_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness, "DATA_DIR", tmp_path)
    source, target = "2026-09-30", "2026-10-02"
    controller = tmp_path / "report/postclose_done_controller" / f"postclose_done_controller_{source}.json"
    _json(controller, {"status": "done"})
    summary = tmp_path / "report/runtime_approval_summary" / f"runtime_approval_summary_{source}.json"
    policy = tmp_path / "runtime/mechanistic_entry_policy" / f"policy_{target}.json"
    _json(policy, {"target_date": target})
    policy_sha = hashlib.sha256(policy.read_bytes()).hexdigest()
    receipt = {"path": str(policy), "sha256": policy_sha, "valid": True,
               "target_date_matches": True}
    _json(summary, {"date": source, "sources": {
        "main_mechanistic_entry": {"policy_receipt": receipt},
        "compact_auxiliary": {"policy_receipt": receipt},
    }})
    monkeypatch.setattr(readiness, "done_terminal_receipt_issues", lambda *a, **k: ["strict_failed"])
    with pytest.raises(ValueError, match="postclose_controller_not_closed"):
        readiness._source_receipts(source, target)
    monkeypatch.setattr(readiness, "done_terminal_receipt_issues", lambda *a, **k: [])
    assert readiness._source_receipts(source, target)["policy_receipts"][0]["sha256"] == policy_sha
    policy.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="target_policy_receipt_invalid"):
        readiness._source_receipts(source, target)


def test_selected_release_requires_router_validated_root_and_commit(monkeypatch, tmp_path):
    release = tmp_path / "managed-release"
    release.mkdir()
    data = tmp_path / "workspace" / "data"
    selection = data / "runtime/runtime_release_selection.json"
    commit = "a" * 40
    _json(selection, {"schema": "runtime_release_selection_v1",
                      "release_root": str(release), "git_commit": commit})
    monkeypatch.setattr(readiness, "DATA_DIR", data)
    monkeypatch.chdir(release)
    calls = []

    def validated(workspace):
        calls.append(workspace)
        return release, commit

    monkeypatch.setattr(readiness, "selected_release", validated)
    assert readiness._selected_release() == (
        json.loads(selection.read_text()), selection, commit)
    assert calls == [data.parent]
    # Main and independent report consumers can verify without changing cwd.
    # The same paths must remain forbidden for preparing a new generation.
    for cwd in (release / 'src', tmp_path / 'report-release'):
        cwd.mkdir()
        monkeypatch.chdir(cwd)
        assert readiness._selected_release(require_selected_cwd=False)[2] == commit
        assert Path.cwd() == cwd
        with pytest.raises(ValueError, match='selected_release_identity_mismatch'):
            readiness._selected_release()
    _json(selection, {"schema": "runtime_release_selection_v1",
                      "release_root": str(release), "git_commit": "b" * 40})
    with pytest.raises(ValueError, match="selected_release_identity_mismatch"):
        readiness._selected_release(require_selected_cwd=False)


def test_prepare_isolated_then_detects_source_and_release_drift(monkeypatch, tmp_path):
    native_selection = readiness._selected_release
    source, target = "2026-09-30", "2026-10-02"
    monkeypatch.setattr(readiness, "PREPARED_DIR", tmp_path / "prepared")
    monkeypatch.setattr(readiness, "is_krx_trading_day", lambda day: day.weekday() < 5)
    selection = tmp_path / "selection.json"
    _json(selection, {"git_commit": "a" * 40})
    selected = ["a" * 40]
    monkeypatch.setattr(readiness, "_selected_release", lambda **kwargs: ({}, selection, selected[0]))
    controller = tmp_path / "controller.json"
    summary = tmp_path / "summary.json"
    policy = tmp_path / "policy.json"
    for path in (controller, summary, policy):
        _json(path, {"source_date": source})

    def receipts(_source, _target, **kwargs):
        assert (_source, _target) == (source, target)
        return {"controller_path": str(controller), "controller_sha256": readiness._sha(controller),
                "summary_path": str(summary), "summary_sha256": readiness._sha(summary),
                "policy_receipts": [{"family": "main_mechanistic_entry", "path": str(policy),
                                     "sha256": readiness._sha(policy)}]}

    monkeypatch.setattr(readiness, "_source_receipts", receipts)

    def write(day, *, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        _json(readiness.bootstrap.manifest_path(day, output_dir=output_dir),
              {"manifest_sha256": "m" * 64, "target_date": day,
               "source_incumbent": readiness.bootstrap._file_receipt(controller)})
        readiness.bootstrap.env_path(day, output_dir=output_dir).write_text("export TEST=1\n")
        return {"selected_release_sha": selected[0], "source_incumbent_target_date": "2026-10-01",
                "manifest_sha256": "m" * 64}

    def verify(day, *, output_dir, write=True):
        result = {"status": "pass", "findings": [], "manifest_sha256": "m" * 64, "target_date": day}
        if write:
            _json(readiness.bootstrap.verify_path(day, output_dir=output_dir), result)
        return result

    monkeypatch.setattr(readiness.bootstrap, "write_bootstrap", write)
    monkeypatch.setattr(readiness.bootstrap, "verify_bootstrap", verify)
    now = datetime(2026, 10, 1, 17, 0, tzinfo=KST)
    assert readiness.prepare(source, target_date=target, now=now)["status"] == "prepared_verified"
    assert readiness.verify_prepared(target, now=now)["status"] == "pass"
    # Exercise the real selection gate through verify_prepared, rather than
    # accepting a mocked selector from an unsafe daemon cwd.
    with monkeypatch.context() as consumer:
        release = tmp_path / 'release'
        release.mkdir()
        native_selector = tmp_path / 'runtime/runtime_release_selection.json'
        _json(native_selector, {'git_commit': selected[0]})
        consumer.setattr(readiness, 'DATA_DIR', tmp_path)
        consumer.setattr(readiness, '_selected_release', native_selection)
        consumer.setattr(readiness, 'selected_release', lambda workspace: (release, selected[0]))
        frozen = {str(p): p.read_bytes() for p in (tmp_path / 'prepared').rglob('*') if p.is_file()}
        for cwd in (release / 'src', tmp_path / 'independent-report'):
            cwd.mkdir()
            consumer.chdir(cwd)
            assert readiness.verify_prepared(target, now=now)['status'] == 'pass'
            with pytest.raises(ValueError, match='selected_release_identity_mismatch'):
                readiness.prepare(source, target_date=target, now=now)
            assert Path.cwd() == cwd
        assert all(Path(p).read_bytes() == content for p, content in frozen.items())
    midnight = datetime(2026, 10, 2, 0, 36, tzinfo=KST)
    assert readiness.prepare(source, target_date=target, now=midnight)["status"] == "prepared_verified"
    assert readiness.verify_prepared(target, require_today=True, now=midnight)["status"] == "pass"
    with monkeypatch.context() as bounded:
        bounded.setattr(readiness.bootstrap, "INITIAL_QUANTITY_CURRENT", tmp_path / "quantity-absent.json")
        bounded.setattr(readiness.bootstrap, "verify_bootstrap", lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("report-only generation check must not rerun policy economics")))
        assert readiness.verify_prepared(target, now=now, generation_only=True)["status"] == "pass"
        original = controller.read_bytes()
        controller.write_text("{}")
        assert readiness.verify_prepared(target, now=now, generation_only=True)["status"] == "fail"
        controller.write_bytes(original)
    assert readiness.verify_prepared(target, require_today=True, now=now)["status"] == "fail"
    selected[0] = "b" * 40
    assert readiness.verify_prepared(target, now=now)["status"] == "fail"
    selected[0] = "a" * 40
    policy.write_text("changed\n", encoding="utf-8")
    assert readiness.verify_prepared(target, now=now)["status"] == "fail"
    with pytest.raises(ValueError, match="preopen_target_not_next_operating_day"):
        readiness.prepare(source, target_date="2026-10-05", now=now)


def test_startup_requires_today_success_from_same_release(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness, "DATA_DIR", tmp_path)
    target = "2026-10-02"
    status = tmp_path / "report/threshold_cycle_preopen_status" / f"threshold_cycle_preopen_{target}.status.json"
    receipt = {"target_date": target, "status": "succeeded", "exit_code": 0,
               "runtime_env_exists": True, "selected_release_commit": "a" * 40,
               "updated_at": "2026-10-02T07:36:00+09:00"}
    _json(status, receipt)
    now = datetime(2026, 10, 2, 7, 55, tzinfo=KST)
    assert readiness.verify_preopen_completion(target, "a" * 40, now=now)["status"] == "pass"
    assert readiness.verify_preopen_completion(target, "b" * 40, now=now)["status"] == "fail"
    receipt["status"] = "failed"
    _json(status, receipt)
    assert readiness.verify_preopen_completion(target, "a" * 40, now=now)["status"] == "fail"
