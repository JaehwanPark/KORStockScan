import json
import sys
from types import SimpleNamespace

from src.engine.automation import codex_workorder_runner as mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_codex_workorder_runner_filters_safe_implement_now(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "generation_id": "g1",
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                },
                {
                    "order_id": "blocked",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "broker guard relaxation",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                },
                {
                    "order_id": "attach",
                    "decision": "attach_existing_family",
                    "runtime_effect": False,
                },
            ],
        },
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True, commit=True)

    assert report["status"] == "dry_run_planned"
    assert [item["order_id"] for item in report["implemented_orders"]] == ["safe"]
    assert [item["order_id"] for item in report["blocked_orders"]] == ["blocked"]
    assert report["blocked_orders"][0]["reason"] == "forbidden_or_not_safe"
    assert report["non_implement_triage"][0]["triage"] == "needs_codex_instrumentation"


def test_codex_workorder_runner_allows_forbidden_uses_contract_declarations(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "generation_id": "g1",
            "orders": [
                {
                    "order_id": "safe_with_contract",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                }
            ],
        },
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True, commit=True)

    assert report["status"] == "dry_run_planned"
    assert [item["order_id"] for item in report["implemented_orders"]] == ["safe_with_contract"]
    assert report["blocked_orders"] == []


def test_codex_workorder_runner_blocks_missing_forbidden_uses_contract(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "generation_id": "g1",
            "orders": [
                {
                    "order_id": "missing_contract",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                }
            ],
        },
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True, commit=True)

    assert report["implemented_orders"] == []
    assert report["blocked_orders"] == [
        {
            "order_id": "missing_contract",
            "decision": "implement_now",
            "reason": "missing_forbidden_uses_contract",
        }
    ]


def test_codex_workorder_runner_reports_no_safe_orders(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {"order_id": "defer", "decision": "defer_evidence", "runtime_effect": False, "repeat_count": 2}
            ],
        },
    )
    calls = []

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        command_runner=lambda cmd, cwd=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "no_safe_orders"
    assert report["non_implement_triage"][0]["triage"] == "promoted"
    assert calls and calls[0][:3] == ["git", "worktree", "add"]


def test_codex_workorder_runner_blocks_when_sdk_unavailable(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                }
            ],
        },
    )
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([], "openai_codex_unavailable"),
    )

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        command_runner=lambda cmd, cwd=None: 0,
    )

    assert report["status"] == "codex_package_unavailable"
    assert report["codex_error"] == "openai_codex_unavailable"


def test_codex_workorder_runner_commit_path(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                    "acceptance_tests": ["python -m pytest -q src/tests/test_build_code_improvement_workorder.py"],
                }
            ],
        },
    )
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([mod.CodexTurnSummary("x", "ok")], None),
    )
    monkeypatch.setattr(mod, "_forbidden_diff_scan", lambda worktree, runner, dry_run: {"status": "pass", "matches": []})
    calls = []

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        commit=True,
        command_runner=lambda cmd, cwd=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "committed"
    assert ["git", "add", "-A"] in calls
    assert any(cmd[:3] == ["git", "commit", "-m"] for cmd in calls)
    assert any(cmd[:3] == [mod._python_bin(), "-m", "pytest"] for cmd in calls)
    assert report["acceptance_results"][0]["command"][:4] == [mod._python_bin(), "-m", "pytest", "-q"]


def test_codex_workorder_runner_records_requested_model_and_effort(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                }
            ],
        },
    )
    observed = {}

    def fake_codex_turns(worktree, orders, dry_run, *, model=None, effort=None, model_policy="auto"):
        observed["model"] = model
        observed["effort"] = effort
        observed["model_policy"] = model_policy
        return [mod.CodexTurnSummary("x", "ok")], None

    monkeypatch.setattr(mod, "_codex_turns", fake_codex_turns)
    monkeypatch.setattr(mod, "_forbidden_diff_scan", lambda worktree, runner, dry_run: {"status": "pass", "matches": []})

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        model="gpt-5.5",
        effort="medium",
        command_runner=lambda cmd, cwd=None: 0,
    )

    assert report["status"] == "validated"
    assert observed == {"model": "gpt-5.5", "effort": "medium", "model_policy": "auto"}
    assert report["codex_model"] == "gpt-5.5"
    assert report["codex_effort"] == "medium"
    assert report["codex_model_policy"] == "auto"


def test_codex_workorder_runner_auto_policy_selects_turn_models():
    orders = [
        {
            "order_id": "small",
            "title": "documentation parser cleanup",
            "files_likely_touched": ["docs/example.md"],
            "acceptance_tests": [],
        }
    ]

    assert mod._select_turn_model_effort(
        "implement", orders, model_policy="auto", model=None, effort=None
    ) == ("gpt-5.3-codex-spark", "medium")
    assert mod._select_turn_model_effort(
        "review", orders, model_policy="auto", model=None, effort=None
    ) == ("gpt-5.4", "high")
    assert mod._select_turn_model_effort(
        "final_review", orders, model_policy="auto", model=None, effort=None
    ) == ("gpt-5.4", "high")


def test_codex_workorder_runner_auto_policy_respects_explicit_overrides():
    orders = [{"order_id": "small", "title": "report parser gap"}]

    assert mod._select_turn_model_effort(
        "implement",
        orders,
        model_policy="auto",
        model="gpt-5.5",
        effort="xhigh",
    ) == ("gpt-5.5", "xhigh")


def test_forbidden_diff_scan_blocks_real_runtime_terms(monkeypatch, tmp_path):
    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "diff", "--name-only", "HEAD"]:
            return 0, "src/engine/automation/example.py\n"
        if cmd == ["git", "ls-files", "--others", "--exclude-standard"]:
            return 0, ""
        assert cmd == ["git", "diff", "HEAD", "--"]
        return 0, "+ provider route change\n+ hard_safety bypass\n"

    result = mod._forbidden_diff_scan(
        tmp_path,
        lambda cmd, cwd=None: 0,
        dry_run=False,
        capture_runner=fake_capture,
    )

    assert result["status"] == "fail"
    assert "diff_term:provider route change" in result["matches"]
    assert "diff_term:hard_safety bypass" in result["matches"]


def test_forbidden_diff_scan_blocks_removed_real_runtime_guard_terms(monkeypatch, tmp_path):
    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "diff", "--name-only", "HEAD"]:
            return 0, "src/engine/automation/example.py\n"
        if cmd == ["git", "ls-files", "--others", "--exclude-standard"]:
            return 0, ""
        assert cmd == ["git", "diff", "HEAD", "--"]
        return 0, "- hard_safety bypass is forbidden\n"

    result = mod._forbidden_diff_scan(
        tmp_path,
        lambda cmd, cwd=None: 0,
        dry_run=False,
        capture_runner=fake_capture,
    )

    assert result["status"] == "fail"
    assert "diff_term:hard_safety bypass" in result["matches"]


def test_forbidden_diff_scan_blocks_disallowed_live_runtime_paths(monkeypatch, tmp_path):
    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "diff", "--name-only", "HEAD"]:
            return 0, "src/engine/sniper_state_handlers.py\n"
        if cmd == ["git", "ls-files", "--others", "--exclude-standard"]:
            return 0, ""
        assert cmd == ["git", "diff", "HEAD", "--"]
        return 0, "+ harmless looking helper refactor\n"

    result = mod._forbidden_diff_scan(
        tmp_path,
        lambda cmd, cwd=None: 0,
        dry_run=False,
        capture_runner=fake_capture,
    )

    assert result["status"] == "fail"
    assert "disallowed_path:src/engine/sniper_state_handlers.py" in result["matches"]


def test_forbidden_diff_scan_blocks_untracked_disallowed_paths(monkeypatch, tmp_path):
    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "diff", "--name-only", "HEAD"]:
            return 0, ""
        if cmd == ["git", "diff", "HEAD", "--"]:
            return 0, ""
        assert cmd == ["git", "ls-files", "--others", "--exclude-standard"]
        return 0, "src/engine/kiwoom_sniper_v2.py\n"

    result = mod._forbidden_diff_scan(
        tmp_path,
        lambda cmd, cwd=None: 0,
        dry_run=False,
        capture_runner=fake_capture,
    )

    assert result["status"] == "fail"
    assert "disallowed_path:src/engine/kiwoom_sniper_v2.py" in result["matches"]


def test_forbidden_diff_scan_blocks_untracked_allowed_path_forbidden_content(monkeypatch, tmp_path):
    new_doc = tmp_path / "docs" / "new.md"
    new_doc.parent.mkdir(parents=True)
    new_doc.write_text("provider route change\n", encoding="utf-8")

    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "diff", "--name-only", "HEAD"]:
            return 0, ""
        if cmd == ["git", "diff", "HEAD", "--"]:
            return 0, ""
        assert cmd == ["git", "ls-files", "--others", "--exclude-standard"]
        return 0, "docs/new.md\n"

    result = mod._forbidden_diff_scan(
        tmp_path,
        lambda cmd, cwd=None: 0,
        dry_run=False,
        capture_runner=fake_capture,
    )

    assert result["status"] == "fail"
    assert "diff_term:provider route change" in result["matches"]


def test_forbidden_diff_scan_allows_plain_source_quality_mentions(monkeypatch, tmp_path):
    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "diff", "--name-only", "HEAD"]:
            return 0, "docs/example.md\n"
        if cmd == ["git", "ls-files", "--others", "--exclude-standard"]:
            return 0, ""
        assert cmd == ["git", "diff", "HEAD", "--"]
        return 0, "+ provider field is preserved as source provenance only\n"

    result = mod._forbidden_diff_scan(
        tmp_path,
        lambda cmd, cwd=None: 0,
        dry_run=False,
        capture_runner=fake_capture,
    )

    assert result == {"status": "pass", "matches": []}


def test_codex_workorder_runner_blocks_unsupported_acceptance_tests(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                    "acceptance_tests": ["bash deploy/run_bot.sh"],
                }
            ],
        },
    )
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([mod.CodexTurnSummary("x", "ok")], None),
    )

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        commit=True,
        command_runner=lambda cmd, cwd=None: 0,
    )

    assert report["status"] == "unsupported_acceptance_tests"
    assert report["unsupported_acceptance_tests"] == ["bash deploy/run_bot.sh"]


def test_codex_workorder_runner_blocks_dirty_existing_worktree(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    worktree_root = tmp_path / "worktrees"
    worktree = worktree_root / "codex-workorder-2026-06-03"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: fake\n", encoding="utf-8")
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", worktree_root)
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                }
            ],
        },
    )
    monkeypatch.setattr(mod, "_run_capture", lambda cmd, cwd=None: (0, " M src/example.py\n"))

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        command_runner=lambda cmd, cwd=None: 0,
    )

    assert report["status"] == "worktree_dirty"
    assert report["worktree_status"] == "worktree_dirty"
    assert report["codex_turns"] == []


def test_codex_workorder_runner_blocks_stale_clean_worktree(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    worktree_root = tmp_path / "worktrees"
    worktree = worktree_root / "codex-workorder-2026-06-03"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: fake\n", encoding="utf-8")
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", worktree_root)
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "orders": [
                {
                    "order_id": "safe",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "title": "report parser gap",
                    "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
                }
            ],
        },
    )

    def fake_capture(cmd, cwd=None):
        if cmd == ["git", "status", "--porcelain"]:
            return 0, ""
        if cmd == ["git", "rev-parse", "HEAD"] and cwd == mod.PROJECT_ROOT:
            return 0, "root-head\n"
        if cmd == ["git", "rev-parse", "HEAD"]:
            return 0, "old-head\n"
        raise AssertionError(cmd)

    monkeypatch.setattr(mod, "_run_capture", fake_capture)

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        command_runner=lambda cmd, cwd=None: 0,
    )

    assert report["status"] == "worktree_stale_head"
    assert report["worktree_status"] == "worktree_stale_head"
    assert report["codex_turns"] == []


def test_codex_turns_requires_login_without_waiting_when_interactive_disabled(monkeypatch, tmp_path):
    wait_called = []

    class FakeLogin:
        verification_url = "https://example.test/device"
        user_code = "ABCD"

        def wait(self):
            wait_called.append(True)

    class FakeCodex:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def account(self, refresh_token=False):
            raise RuntimeError("not logged in")

        def login_chatgpt_device_code(self):
            return FakeLogin()

    fake_module = SimpleNamespace(Codex=FakeCodex, Sandbox=SimpleNamespace(workspace_write="w", read_only="r"))
    monkeypatch.setitem(sys.modules, "openai_codex", fake_module)
    monkeypatch.delenv("CODEX_WORKORDER_ALLOW_INTERACTIVE_LOGIN", raising=False)

    turns, error = mod._codex_turns(
        tmp_path,
        [{"order_id": "safe", "decision": "implement_now", "runtime_effect": False}],
        dry_run=False,
    )

    assert turns == []
    assert error == "codex_login_required"
    assert wait_called == []
