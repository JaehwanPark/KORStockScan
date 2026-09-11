"""Document publication and scheduled completion contracts; no provider/network calls."""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from src.engine.automation import monitoring_instruction_refresh as m


DAY = "2026-09-11"
ORIGINAL = "# Instructions\n\nCurrent command: old-command.\n\nSafety guard: no orders.\n"


def draft(old="old-command", new="new-command", quote="new-command"):
    return {"reason": "command renamed", "edits": [{"old": old, "new": new,
            "evidence": [{"path": "code", "quote": quote}]}]}


def marker(root, *lines):
    path = root / "logs/postclose_finalization_cron.log"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


DONE = f"[DONE] postclose_final_detector target_date={DAY} finalization=done detector=done"


@pytest.mark.parametrize("last,expected", [
    (DONE, True),
    (f"[START] postclose_finalization target_date={DAY}", False),
    (f"[FAIL] postclose_finalization target_date={DAY}", False),
    (f"[DONE] postclose_finalization target_date={DAY} cleanup=done detector_handoff=started", False),
    ("[START] postclose_finalization target_date=2026-09-12", True),
])
def test_last_terminal_owns_completion(tmp_path, last, expected):
    marker(tmp_path, DONE, last)
    assert bool(m.completion_marker(tmp_path, DAY)) is expected


def test_strict_completion_requires_current_hashes_and_real_controller(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as handoff
    marker(tmp_path, DONE)
    report = tmp_path / "data/report"
    verifier = report / f"threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_{DAY}.json"
    controller = report / f"postclose_done_controller/postclose_done_controller_{DAY}.json"
    m.save_json(verifier, {"date": DAY, "status": "warning", "summary_handoff": {"status": "pass"}})
    m.save_json(controller, {"date": DAY, "status": "done", "dry_run": False})
    seen = {}

    def verify(*args, **kwargs):
        seen.update(kwargs)
        return {"status": "pass"}

    monkeypatch.setattr(handoff, "verify_summary_handoff", verify)
    receipt = m.completion_ready(tmp_path, DAY)
    assert receipt["target_date"] == DAY
    assert receipt["checklist_date"] == "2026-09-14"
    assert seen["checklist_path"] == tmp_path / "docs/checklists/2026-09-14-stage2-todo-checklist.md"
    monkeypatch.setattr(handoff, "verify_summary_handoff", lambda *a, **k: {"status": "fail"})
    with pytest.raises(ValueError, match="current_summary_hashes"):
        m.completion_ready(tmp_path, DAY)
    m.save_json(controller, {"date": DAY, "status": "done", "dry_run": True})
    with pytest.raises(ValueError, match="strict_summary_or_controller"):
        m.completion_ready(tmp_path, DAY)


@pytest.mark.parametrize("proposal,reason", [
    (draft(quote="invented"), "unbound_evidence"),
    (draft(old="Safety guard: no orders.", new="Safety guard: allow orders."), "protected_contract"),
    (draft(new="new-command with authority"), "protected_contract"),
    (draft(old="# Instructions", new="# New heading"), "heading_contract"),
    (draft(new="x" * 200), "unbounded_document"),
    (draft(old="missing"), "nonunique"),
    (draft(new="[x](x)"), "broken_local_link"),
])
def test_reject_unsupported_or_unsafe_patch(tmp_path, proposal, reason):
    with pytest.raises(ValueError, match=reason):
        m.document_candidate(ORIGINAL, proposal, {"code": "new-command"}, tmp_path)


def test_overlapping_edits_rejected(tmp_path):
    proposal = draft()
    proposal["edits"] += draft(old="command: old-command.")["edits"]
    with pytest.raises(ValueError, match="overlapping"):
        m.document_candidate(ORIGINAL, proposal, {"code": "new-command"}, tmp_path)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    for target in m.TARGETS.values():
        path = tmp_path / target
        path.parent.mkdir(exist_ok=True)
        path.write_text(ORIGINAL)
    monkeypatch.setattr(m, "git", lambda *a: "a" * 40)

    def context(root, mode, day, **kwargs):
        return {"workspace_commit": "a" * 40, "sources": {m.TARGETS[mode]: ORIGINAL, "code": "new-command"},
                "file_hashes": {m.TARGETS[mode]: m.sha(ORIGINAL)}}

    monkeypatch.setattr(m, "context_bundle", context)
    return tmp_path


def good_api(instructions, payload, schema, phase, config):
    value = draft() if phase == "draft" else {"approved": True, "findings": []}
    return value, {"phase": phase, "response_id": "mock"}


def test_publish_once_and_preview_does_not_consume_schedule(workspace):
    preview = m.refresh(workspace, "postclose", DAY, {}, preview=True, call=good_api, validate=lambda root: None)
    assert preview["status"] == "preview_validated"
    target = workspace / m.TARGETS["postclose"]
    assert target.read_text() == ORIGINAL
    result = m.refresh(workspace, "postclose", DAY, {}, call=good_api, validate=lambda root: None)
    assert result["status"] == "updated"
    assert "new-command" in target.read_text()
    assert len(result["api_calls"]) == 2
    assert m.refresh(workspace, "postclose", DAY, {}, call=lambda *a: pytest.fail("duplicate API")) == result


@pytest.mark.parametrize("failure", ["review", "provider", "parser", "concurrent", "completion"])
def test_failure_never_overwrites_document(workspace, monkeypatch, failure):
    mode = "intraday" if failure == "completion" else "postclose"
    calls = []
    target = workspace / m.TARGETS[mode]
    def api(*args):
        calls.append(args[3])
        if failure == "provider":
            raise RuntimeError("sensitive provider body")
        if failure == "review" and args[3] == "review":
            return {"approved": False, "findings": ["unsupported"]}, {}
        return good_api(*args)
    def validate(root):
        if failure == "parser":
            raise ValueError("parser_failed")
        if failure == "concurrent":
            target.write_text(ORIGINAL + "Concurrent user edit\n")
    receipts = iter([{"id": 1}, {"id": 2}])
    monkeypatch.setattr(m, "completion_ready", lambda *a: next(receipts))
    result = m.refresh(workspace, mode, DAY, {}, call=api, validate=validate)
    assert result["status"] == "failed"
    assert "sensitive" not in json.dumps(result)
    assert target.read_text() == ORIGINAL + ("Concurrent user edit\n" if failure == "concurrent" else "")
    assert len(calls) <= 4


def test_two_failed_attempts_stop_api(workspace):
    def failure(*a):
        raise ValueError("api_failure")
    for _ in range(2):
        result = m.refresh(workspace, "postclose", DAY, {}, call=failure)
        assert result["status"] == "failed"
    assert m.refresh(workspace, "postclose", DAY, {}, call=lambda *a: pytest.fail("unbounded retry"))["attempts"] == 2
    base = workspace / m.STATE / DAY / "postclose"
    assert m.read_json(base / "attempt_1/status.json")["attempts"] == 1
    assert m.read_json(base / "attempt_2/status.json")["attempts"] == 2


def test_edit_during_final_completion_check_is_preserved(workspace, monkeypatch):
    target = workspace / m.TARGETS["intraday"]
    count = 0
    def completion(*args):
        nonlocal count
        count += 1
        if count == 2:
            target.write_text(ORIGINAL + "Concurrent edit during slow hash verification\n")
        return {"id": "same receipt"}
    monkeypatch.setattr(m, "completion_ready", completion)
    result = m.refresh(workspace, "intraday", DAY, {}, call=good_api, validate=lambda root: None)
    assert result["status"] == "failed"
    assert "Concurrent edit during slow hash verification" in target.read_text()


@pytest.mark.parametrize("after_swap,later_edit", [(False, False), (True, False), (True, True)])
def test_publish_crash_never_repeats_api(workspace, monkeypatch, after_swap, later_edit):
    target = workspace / m.TARGETS["postclose"]
    write = m.atomic_write
    class PowerLoss(BaseException):
        pass
    def crash(path, text):
        if path == target:
            if after_swap:
                write(path, text)
            raise PowerLoss()
        return write(path, text)
    monkeypatch.setattr(m, "atomic_write", crash)
    with pytest.raises(PowerLoss):
        m.refresh(workspace, "postclose", DAY, {}, call=good_api, validate=lambda root: None)
    monkeypatch.setattr(m, "atomic_write", write)
    if later_edit:
        target.write_text("User edited after the interrupted publication\n")
    result = m.refresh(workspace, "postclose", DAY, {}, call=lambda *a: pytest.fail("duplicate API after crash"))
    assert result["status"] == ("updated" if after_swap and not later_edit else "blocked_publication")
    assert result["attempts"] == 1
    expected = ORIGINAL.replace("old-command", "new-command") if after_swap else ORIGINAL
    if later_edit:
        expected = "User edited after the interrupted publication\n"
    assert target.read_text() == expected
    assert m.refresh(workspace, "postclose", DAY, {}, call=lambda *a: pytest.fail("terminal repeat")) == result


def test_dispatch_recovers_second_attempt_before_retry_budget_check(workspace, monkeypatch):
    def failure(*args):
        raise ValueError("provider failure")
    m.refresh(workspace, "postclose", DAY, {}, call=failure)
    write = m.atomic_write
    target = workspace / m.TARGETS["postclose"]
    def crash(path, text):
        write(path, text)
        if path == target:
            raise KeyboardInterrupt()
    monkeypatch.setattr(m, "atomic_write", crash)
    with pytest.raises(KeyboardInterrupt):
        m.refresh(workspace, "postclose", DAY, {}, call=good_api, validate=lambda root: None)
    monkeypatch.setattr(m, "atomic_write", write)
    monkeypatch.setattr(m, "refresh", lambda *a: pytest.fail("must recover without API"))
    results = m.dispatch(workspace, "postclose", {"enabled": True, "effective_from_date": DAY},
                         datetime(2026, 9, 11, 19, 59, tzinfo=m.KST))
    assert results[0]["status"] == "updated"
    assert results[0]["attempts"] == 2


def test_disable_is_read_after_acquiring_writer_lock(workspace, monkeypatch, capsys):
    monkeypatch.setattr(m, "ROOT", workspace)
    monkeypatch.setattr(os.sys, "argv", ["refresh", "--mode", "postclose"])
    m.save_json(workspace / m.CONFIG, {"enabled": True, "effective_from_date": DAY})
    def lock_then_disable(*args):
        m.save_json(workspace / m.CONFIG, {"enabled": False})
    monkeypatch.setattr(m.fcntl, "flock", lock_then_disable)
    monkeypatch.setattr(m, "dispatch", lambda root, mode, config, now: [{"status": "disabled"}]
                        if config["enabled"] is False else pytest.fail("stale enabled config"))
    assert m.main() == 0
    assert "disabled" in capsys.readouterr().out


def test_dispatch_kst_time_disabled_and_original_date_after_midnight(tmp_path, monkeypatch):
    config = {"enabled": True, "effective_from_date": DAY}
    seen = []
    monkeypatch.setattr(m, "refresh", lambda root, mode, day, config: seen.append(day) or {"status": "unchanged"})
    before = datetime(2026, 9, 11, 19, 29, tzinfo=m.KST)
    assert m.dispatch(tmp_path, "postclose", config, before) == [{"status": "not_yet_due"}]
    m.dispatch(tmp_path, "postclose", config, before.replace(minute=30))
    assert seen == [DAY]
    seen.clear()
    marker(tmp_path, DONE)
    monkeypatch.setattr(m, "completion_ready", lambda *a: {})
    m.dispatch(tmp_path, "intraday", config, datetime(2026, 9, 12, 0, 5, tzinfo=m.KST))
    assert seen == [DAY]
    seen.clear()
    m.dispatch(tmp_path, "intraday", {**config, "effective_from_date": "2026-09-12"}, before)
    assert seen == []
    assert m.dispatch(tmp_path, "postclose", {"enabled": False}, before) == [{"status": "disabled"}]


def test_waiting_completion_spends_no_attempt(tmp_path, monkeypatch):
    marker(tmp_path, DONE)
    def waiting(*a):
        raise ValueError("waiting")
    monkeypatch.setattr(m, "completion_ready", waiting)
    monkeypatch.setattr(m, "refresh", lambda *a: pytest.fail("API before completion"))
    assert m.dispatch(tmp_path, "intraday", {"enabled": True, "effective_from_date": DAY},
                      datetime(2026, 9, 11, 23, 30, tzinfo=m.KST)) == []
    assert not (tmp_path / m.STATE / DAY).exists()


def test_credential_loader_precedence_and_no_provider_import(tmp_path, monkeypatch):
    monkeypatch.delenv("MONITORING_DOC_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    data = tmp_path / "data"
    data.mkdir()
    m.save_json(data / "config_prod.json", {"OPENAI_API_KEY_10": "test-ten",
        "OPENAI_API_KEY_2": "test-two", "OPENAI_API_KEY": "-", "OTHER_SECRET": "excluded"})
    assert m.load_api_key(tmp_path) == "test-two"
    monkeypatch.setenv("OPENAI_API_KEY", "test-env")
    assert m.load_api_key(tmp_path) == "test-env"
    monkeypatch.setenv("MONITORING_DOC_OPENAI_API_KEY", "test-dedicated")
    assert m.load_api_key(tmp_path) == "test-dedicated"


def test_source_credentials_are_removed_before_api_payload():
    text = 'endpoint = "https://user:password@example.com/path"\nOPENAI_API_KEY = "secret-value"\ncommand = "report --date today"\n'
    cleaned = m.sanitize_source(text)
    assert "secret-value" not in cleaned and "password" not in cleaned
    assert 'command = "report --date today"' in cleaned


def test_source_bundle_omits_daily_history_and_keeps_source_budget(tmp_path, monkeypatch):
    for name in ["AGENTS.md", "docs/plan-korStockScanPerformanceOptimization.rebase.md",
                 "docs/runtime-release-routing.md", m.TARGETS["postclose"],
                 f"docs/checklists/{DAY}-stage2-todo-checklist.md"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Daily\n\n## 오늘 목적\nPurpose\n\n## 오늘 강제 규칙\nRules\n\n"
                        "## History\nMonitoringInstructionRefreshNaturalAcceptance0911\n")
    monkeypatch.setattr(m, "now_kst", lambda: datetime(2026, 9, 11, 12, tzinfo=m.KST))
    monkeypatch.setattr(m, "git", lambda root, *a: "a" * 40 if a[0] == "rev-parse" else "")
    bundle = m.context_bundle(tmp_path, "postclose", DAY)
    checklist = bundle["sources"][f"docs/checklists/{DAY}-stage2-todo-checklist.md"]
    assert "오늘 목적" in checklist and "오늘 강제 규칙" in checklist
    assert "MonitoringInstructionRefreshNaturalAcceptance0911" not in checklist
    assert sum(map(len, bundle["sources"].values())) <= m.MAX_SOURCE_CHARS


def test_installer_idempotent_preserves_cron_and_rolls_back_config(tmp_path):
    root = tmp_path / "repo"
    (root / "deploy").mkdir(parents=True)
    (root / ".venv/bin").mkdir(parents=True)
    (root / ".venv/bin/python").symlink_to(Path(os.sys.executable))
    for name in ["install_monitoring_instruction_refresh_cron.sh", "run_monitoring_instruction_refresh.sh"]:
        shutil.copy(m.ROOT / "deploy" / name, root / "deploy" / name)
    module = root / "src/engine/automation/monitoring_instruction_refresh.py"
    module.parent.mkdir(parents=True)
    module.write_text("# test module\n")
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    cron = tmp_path / "cron"
    original = "MAILTO=operator\n15 7 * * * /existing/job\n"
    cron.write_text(original)
    (fakebin / "timedatectl").write_text('#!/bin/sh\necho "${TEST_TIMEZONE:-Asia/Seoul}"\n')
    (fakebin / "crontab").write_text("#!/bin/sh\nif [ \"$1\" = -l ]; then cat \"$TEST_CRON\"; else\n"
        "if [ \"${TEST_FAIL:-0}\" = 1 ]; then exit 1; fi\ncat > \"$TEST_CRON\"\nfi\n")
    for p in fakebin.iterdir():
        p.chmod(0o755)
    env = {**os.environ, "PATH": str(fakebin) + ":" + os.environ["PATH"], "TEST_CRON": str(cron)}
    def run(mode, **extra):
        return subprocess.run(["bash", str(root / "deploy/install_monitoring_instruction_refresh_cron.sh"), mode],
                              env={**env, **extra}, capture_output=True, text=True)
    assert run("--print-plan").returncode == 0
    assert cron.read_text() == original and not (root / m.CONFIG).exists()
    for _ in range(2):
        assert run("--install").returncode == 0
    installed = cron.read_text()
    assert installed.startswith(original)
    assert "30-59 19 * * *" in installed
    assert installed.count("# KORSTOCKSCAN_MONITORING_INSTRUCTION_REFRESH_") == 2
    before = m.read_json(root / m.CONFIG)
    assert run("--remove", TEST_FAIL="1").returncode != 0
    assert m.read_json(root / m.CONFIG) == before
    assert cron.read_text() == installed
    assert run("--install", TEST_TIMEZONE="UTC").returncode != 0
    assert cron.read_text() == installed
    assert run("--remove", TEST_TIMEZONE="UTC").returncode == 0
    assert cron.read_text() == original
    assert m.read_json(root / m.CONFIG)["enabled"] is False
