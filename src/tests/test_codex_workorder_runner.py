import json
import sys
from types import SimpleNamespace

from src.engine.automation import codex_workorder_runner as mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _patch_report_dirs(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "codex_workorder_runner")
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    return report_dir


def _write_workorder(report_dir, orders, *, non_selected_orders=None):
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {
            "generation_id": "g1",
            "orders": orders,
            "non_selected_orders": non_selected_orders or [],
        },
    )


def _safe_order(order_id="safe", **extra):
    payload = {
        "order_id": order_id,
        "decision": "implement_now",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "title": "report parser gap",
        "forbidden_uses": ["real_order_authority", "provider_route_change", "bot_restart"],
    }
    payload.update(extra)
    return payload


def _successful_attempt(**kwargs):
    order_ids = [item["order_id"] for item in kwargs["orders"]]
    return {
        "attempt": kwargs["attempt_index"] + 1,
        "status": "committed_branch",
        "codex_error": None,
        "order_ids": order_ids,
        "branch": f"{kwargs['branch_prefix']}-{kwargs['attempt_index']}",
        "validation_results": [{"command": ["ok"], "exit_code": 0, "status": "pass"}],
        "commit_sha": f"sha-{'-'.join(order_ids)}",
    }


def test_safe_missing_forbidden_uses_is_repaired_into_canonical_queue(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            {
                "order_id": "repairable",
                "decision": "implement_now",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "title": "parser documentation gap",
            }
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["status"] == "dry_run_planned"
    assert report["canonical_implement_order_ids"] == ["repairable"]
    assert report["contract_recoveries"][0]["order_id"] == "repairable"
    assert report["blocked_orders"] == []


def test_unsafe_implement_now_is_removed_from_canonical_queue(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            _safe_order("unsafe", title="broker guard relaxation"),
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_non_recoverable"
    assert report["canonical_implement_order_ids"] == []
    assert report["normalized_out_orders"] == [
        {
            "order_id": "unsafe",
            "decision": "implement_now",
            "terminal_status": "requires_user_authority",
            "reason": "forbidden_or_not_safe",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    ]


def test_implement_now_without_code_contract_is_rejudged_terminal(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            _safe_order(
                "source_only_child_evidence",
                source_report_type="lifecycle_decision_matrix_exit_bucket_attribution",
                files_likely_touched=[],
                acceptance_tests=[],
            ),
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == []
    assert report["normalized_out_orders"][0]["terminal_status"] == "deferred_evidence_terminal"
    assert report["normalized_out_orders"][0]["reason"] == "not_code_actionable_missing_files_and_acceptance"
    assert report["non_implement_dispositions"][0]["triage"] == "rejudged_implement_now_not_code_actionable"


def test_implement_now_with_review_text_acceptance_only_is_rejudged_terminal(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            _safe_order(
                "order_swing_lifecycle_observation_coverage",
                source_report_type="swing_improvement_automation",
                files_likely_touched=["src/engine/example.py"],
                acceptance_tests=["pipeline event field coverage smoke"],
            ),
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == []
    assert report["normalized_out_orders"][0]["reason"] == "not_code_actionable_unsupported_acceptance_only"


def test_missing_forbidden_uses_with_unsafe_scope_is_user_authority_blocker(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            {
                "order_id": "unsafe_missing_contract",
                "decision": "implement_now",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "title": "provider route change",
            }
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_non_recoverable"
    assert report["canonical_implement_order_ids"] == []
    assert report["normalized_out_orders"][0]["terminal_status"] == "requires_user_authority"
    assert report["normalized_out_orders"][0]["reason"] == "forbidden_or_not_safe"


def test_non_implement_orders_receive_terminal_dispositions_without_implicit_attach_promotion(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            {"order_id": "attach", "decision": "attach_existing_family", "runtime_effect": False},
            {"order_id": "defer", "decision": "defer_evidence", "runtime_effect": False},
            {"order_id": "reject", "decision": "reject", "runtime_effect": False},
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == []
    dispositions = {item["order_id"]: item["terminal_status"] for item in report["non_implement_dispositions"]}
    assert dispositions == {
        "attach": "no_code_required",
        "defer": "deferred_evidence_terminal",
        "reject": "rejected_terminal",
    }
    assert set(dispositions.values()).issubset(mod.TERMINAL_NON_IMPLEMENT_STATUSES)


def test_explicit_instrumentation_attach_order_promotes_to_canonical_queue(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            {
                "order_id": "attach_instrumentation",
                "decision": "attach_existing_family",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "needs_codex_instrumentation": True,
            },
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == ["attach_instrumentation"]
    assert report["non_implement_dispositions"][0]["terminal_status"] == "promoted_to_implement_now"


def test_exact_instrumentation_route_promotes_to_canonical_queue(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            {
                "order_id": "attach_instrumentation_route",
                "decision": "attach_existing_family",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "route": "instrumentation_order",
            },
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == ["attach_instrumentation_route"]
    assert report["non_implement_dispositions"][0]["terminal_status"] == "promoted_to_implement_now"


def test_free_text_instrumentation_phrase_does_not_promote_attach_order(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [
            {
                "order_id": "attach_negated_text",
                "decision": "attach_existing_family",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_reason": "no needs_codex_instrumentation required; already attached",
            },
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == []
    assert report["non_implement_dispositions"][0]["terminal_status"] == "no_code_required"
    assert report["non_implement_dispositions"][0]["triage"] == "attached_to_existing_family"


def test_non_selected_orders_are_not_promoted_or_executed(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [_safe_order("selected")],
        non_selected_orders=[
            _safe_order("non_selected_implement"),
            {
                "order_id": "non_selected_attach",
                "decision": "attach_existing_family",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "needs_codex_instrumentation": True,
            },
            "malformed",
        ],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", dry_run=True)

    assert report["canonical_implement_order_ids"] == ["selected"]
    assert report["non_selected_order_ids"] == ["non_selected_implement", "non_selected_attach"]
    dispositions = {item["order_id"]: item["terminal_status"] for item in report["non_selected_dispositions"]}
    assert dispositions == {
        "non_selected_implement": "deferred_evidence_terminal",
        "non_selected_attach": "deferred_evidence_terminal",
    }
    assert all(
        item["order_id"] not in report["canonical_implement_order_ids"]
        for item in report["non_selected_dispositions"]
    )


def test_strict_completion_requires_branch_commit_merge_and_push(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("CODEX_WORKORDER_TWO_PASS_ENABLED", "false")
    _write_workorder(report_dir, [_safe_order()])
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([mod.CodexTurnSummary("implement", "ok")], None),
    )
    monkeypatch.setattr(
        mod,
        "_run_branch_validation_acceptance",
        lambda **kwargs: (
            [{"command": ["git", "diff", "--check", "HEAD"], "exit_code": 0, "status": "pass"}],
            [],
            [],
            {"status": "pass", "matches": []},
            True,
        ),
    )
    monkeypatch.setattr(mod, "_commit_worktree_diff", lambda **kwargs: (0, "branch-sha"))
    monkeypatch.setattr(
        mod,
        "_merge_and_push_main",
        lambda **kwargs: (
            {"status": "merged_main", "merged_main_sha": "main-sha", "branches": ["codex-workorder-2026-06-03"]},
            {"status": "pushed", "pushed": True, "exit_code": 0},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "completed"
    assert report["order_execution_results"][0]["final_status"] == "completed"
    assert report["order_execution_results"][0]["commit_sha"] == "branch-sha"
    assert report["order_execution_results"][0]["merged_main_sha"] == "main-sha"
    assert report["order_execution_results"][0]["pushed"] is True


def test_push_disabled_keeps_runner_incomplete(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("CODEX_WORKORDER_TWO_PASS_ENABLED", "false")
    _write_workorder(report_dir, [_safe_order()])
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([mod.CodexTurnSummary("implement", "ok")], None),
    )
    monkeypatch.setattr(
        mod,
        "_run_branch_validation_acceptance",
        lambda **kwargs: ([{"command": ["ok"], "exit_code": 0, "status": "pass"}], [], [], {"status": "pass", "matches": []}, True),
    )
    monkeypatch.setattr(mod, "_commit_worktree_diff", lambda **kwargs: (0, "branch-sha"))
    monkeypatch.setattr(
        mod,
        "_merge_and_push_main",
        lambda **kwargs: (
            {"status": "merged_main", "merged_main_sha": "main-sha", "branches": []},
            {"status": "push_disabled", "pushed": False},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", auto_push=False, command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_uncompleted_implementation"
    assert report["order_execution_results"][0]["final_status"] == "committed_branch"
    assert report["push_result"]["status"] == "push_disabled"


def test_no_diff_after_codex_turn_is_not_completed(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(report_dir, [_safe_order()])
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([mod.CodexTurnSummary("implement", "ok")], None),
    )
    monkeypatch.setattr(
        mod,
        "_run_branch_validation_acceptance",
        lambda **kwargs: ([{"command": ["ok"], "exit_code": 0, "status": "pass"}], [], [], {"status": "pass", "matches": []}, True),
    )
    monkeypatch.setattr(mod, "_has_head_diff", lambda worktree: False)

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_uncompleted_implementation"
    assert report["order_execution_results"][0]["final_status"] == "blocked_uncompleted_implementation"
    assert report["order_execution_results"][0]["reason"] == "commit_failed"


def test_batch_timeout_splits_to_single_order_retries(monkeypatch, tmp_path):
    orders = [_safe_order("a"), _safe_order("b")]
    recovery_attempts = []
    branch_commits = []
    attempt_counter = [0]

    monkeypatch.setattr(mod, "_codex_recovery_model_plan", lambda model, effort: [(model, effort, "primary")])
    monkeypatch.setattr(mod, "_expanded_timeout_values", lambda: ["1"])

    def fake_attempt(**kwargs):
        if len(kwargs["orders"]) > 1:
            return {
                "attempt": kwargs["attempt_index"] + 1,
                "status": "codex_error",
                "codex_error": "codex_turn_timeout:implement:1s",
                "order_ids": [item["order_id"] for item in kwargs["orders"]],
                "branch": "batch",
                "validation_results": [],
            }
        return {
            "attempt": kwargs["attempt_index"] + 1,
            "status": "committed_branch",
            "codex_error": None,
            "order_ids": [kwargs["orders"][0]["order_id"]],
            "branch": f"branch-{kwargs['orders'][0]['order_id']}",
            "validation_results": [{"command": ["ok"], "exit_code": 0, "status": "pass"}],
            "commit_sha": f"sha-{kwargs['orders'][0]['order_id']}",
        }

    monkeypatch.setattr(mod, "_attempt_codex_batch", fake_attempt)

    results = mod._process_order_batch(
        target_date="2026-06-03",
        branch_prefix="codex-workorder",
        orders=orders,
        model=None,
        effort=None,
        model_policy="auto",
        command_runner=lambda cmd, cwd=None: 0,
        dry_run=False,
        attempt_counter=attempt_counter,
        recovery_attempts=recovery_attempts,
        branch_commits=branch_commits,
        max_recovery_attempts=4,
    )

    assert [item["final_status"] for item in results] == ["committed_branch", "committed_branch"]
    assert [attempt["order_ids"] for attempt in recovery_attempts] == [["a", "b"], ["a"], ["b"]]
    assert [item["commit_sha"] for item in branch_commits] == ["sha-a", "sha-b"]


def test_single_order_timeout_exhausted_blocks_completion(monkeypatch):
    monkeypatch.setattr(mod, "_codex_recovery_model_plan", lambda model, effort: [(model, effort, "primary")])
    monkeypatch.setattr(mod, "_expanded_timeout_values", lambda: ["1"])
    monkeypatch.setattr(
        mod,
        "_attempt_codex_batch",
        lambda **kwargs: {
            "attempt": kwargs["attempt_index"] + 1,
            "status": "codex_error",
            "codex_error": "codex_turn_timeout:implement:1s",
            "order_ids": [item["order_id"] for item in kwargs["orders"]],
            "branch": "branch-a",
            "validation_results": [],
        },
    )

    results = mod._process_order_batch(
        target_date="2026-06-03",
        branch_prefix="codex-workorder",
        orders=[_safe_order("a")],
        model=None,
        effort=None,
        model_policy="auto",
        command_runner=lambda cmd, cwd=None: 0,
        dry_run=False,
        attempt_counter=[0],
        recovery_attempts=[],
        branch_commits=[],
        max_recovery_attempts=1,
    )

    assert results == [
        {
            "order_id": "a",
            "final_status": "blocked_uncompleted_implementation",
            "attempt_count": 1,
            "codex_errors": ["codex_turn_timeout:implement:1s"],
            "validation_results": [],
            "commit_sha": None,
            "branch": "branch-a",
            "merged_main_sha": None,
            "pushed": False,
            "reason": "codex_turn_timeout:implement:1s",
        }
    ]


def test_validation_failure_after_retries_remains_incomplete(monkeypatch):
    monkeypatch.setattr(mod, "_codex_recovery_model_plan", lambda model, effort: [(model, effort, "primary")])
    monkeypatch.setattr(mod, "_expanded_timeout_values", lambda: ["1"])
    monkeypatch.setattr(
        mod,
        "_attempt_codex_batch",
        lambda **kwargs: {
            "attempt": kwargs["attempt_index"] + 1,
            "status": "validation_failed",
            "codex_error": None,
            "order_ids": [item["order_id"] for item in kwargs["orders"]],
            "branch": "branch-a",
            "validation_results": [{"command": ["pytest"], "exit_code": 1, "status": "fail"}],
        },
    )

    results = mod._process_order_batch(
        target_date="2026-06-03",
        branch_prefix="codex-workorder",
        orders=[_safe_order("a")],
        model=None,
        effort=None,
        model_policy="auto",
        command_runner=lambda cmd, cwd=None: 0,
        dry_run=False,
        attempt_counter=[0],
        recovery_attempts=[],
        branch_commits=[],
        max_recovery_attempts=1,
    )

    assert results[0]["final_status"] == "blocked_uncompleted_implementation"
    assert results[0]["reason"] == "validation_failed"
    assert results[0]["validation_results"][0]["exit_code"] == 1


def test_forbidden_diff_scan_blocks_real_runtime_terms(tmp_path):
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


def test_forbidden_diff_scan_blocks_disallowed_live_runtime_paths(tmp_path):
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


def test_forbidden_diff_scan_blocks_untracked_disallowed_paths(tmp_path):
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


def test_forbidden_diff_scan_blocks_untracked_allowed_path_forbidden_content(tmp_path):
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


def test_forbidden_diff_scan_allows_plain_source_quality_mentions(tmp_path):
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


def test_unsupported_acceptance_tests_block_completion(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(
        report_dir,
        [_safe_order("unsupported_acceptance", acceptance_tests=["bash deploy/run_bot.sh"])],
    )
    monkeypatch.setenv("CODEX_WORKORDER_MAX_RECOVERY_ATTEMPTS", "1")
    monkeypatch.setattr(
        mod,
        "_codex_turns",
        lambda worktree, orders, dry_run, **kwargs: ([mod.CodexTurnSummary("implement", "ok")], None),
    )
    monkeypatch.setattr(
        mod,
        "_run_validation",
        lambda worktree, command_runner, dry_run: [{"command": ["ok"], "exit_code": 0, "status": "pass"}],
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_uncompleted_implementation"
    assert report["unsupported_acceptance_tests"] == ["bash deploy/run_bot.sh"]
    assert report["forbidden_diff_scan"]["status"] == "not_run"
    assert report["order_execution_results"][0]["reason"] == "validation_failed"


def test_merge_and_push_updates_main_sha_after_push_rejected_rebase_retry(monkeypatch, tmp_path):
    commands = []
    push_calls = [0]
    head_values = iter(["pre-rebase-sha", "post-rebase-sha"])
    monkeypatch.setattr(mod, "WORKTREE_ROOT", tmp_path / "worktrees")
    monkeypatch.setattr(
        mod,
        "_run_validation",
        lambda worktree, command_runner, dry_run: [{"command": ["ok"], "exit_code": 0, "status": "pass"}],
    )
    monkeypatch.setattr(mod, "_head_sha", lambda worktree: next(head_values))

    def fake_runner(cmd, cwd=None):
        commands.append(cmd)
        if cmd == ["git", "push", "origin", "HEAD:main"]:
            push_calls[0] += 1
            return 1 if push_calls[0] == 1 else 0
        return 0

    merge_result, push_result = mod._merge_and_push_main(
        target_date="2026-06-03",
        branch_commits=[{"branch": "pass1", "commit_sha": "sha-pass1"}],
        command_runner=fake_runner,
        dry_run=False,
        auto_push=True,
    )

    assert push_result["status"] == "pushed"
    assert push_result["rebase_exit_code"] == 0
    assert merge_result["merged_main_sha"] == "post-rebase-sha"
    assert commands.count(["git", "push", "origin", "HEAD:main"]) == 2
    assert ["git", "rebase", "origin/main"] in commands


def test_regeneration_commands_run_in_required_order():
    commands = mod._regeneration_commands("2026-06-03", 7)
    joined = [" ".join(command) for command in commands]

    assert "src.engine.observation_source_quality_audit --target-date 2026-06-03 --write" in joined[0]
    assert "src.engine.automation.key_lineage_ledger --date 2026-06-03" in joined[1]
    assert "src.engine.automation.conversion_lane --date 2026-06-03" in joined[2]
    assert "src.engine.build_code_improvement_workorder --date 2026-06-03 --max-orders 7" in joined[3]
    assert "src.engine.verify_threshold_cycle_postclose_chain --date 2026-06-03" in joined[4]


def test_two_pass_skips_pass2_when_regenerated_workorder_has_no_new_safe_orders(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    order = _safe_order("pass1")
    _write_workorder(report_dir, [order])
    monkeypatch.setattr(mod, "_attempt_codex_batch", _successful_attempt)
    monkeypatch.setattr(
        mod,
        "_run_two_pass_regeneration",
        lambda **kwargs: (
            {"status": "regeneration_completed", "results": [{"status": "merged_pass1"}]},
            {"generation_id": "g2", "source_hash": "h2", "orders": [order], "lineage": {}},
        ),
    )
    monkeypatch.setattr(
        mod,
        "_merge_and_push_main",
        lambda **kwargs: (
            {"status": "merged_main", "merged_main_sha": "main-sha", "branches": ["pass1"]},
            {"status": "pushed", "pushed": True, "exit_code": 0},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "completed"
    assert report["two_pass_status"] == "pass2_not_required"
    assert report["pass1_order_ids"] == ["pass1"]
    assert report["pass2_order_ids"] == []
    assert report["regeneration_results"] == [{"status": "merged_pass1"}]


def test_two_pass_new_safe_order_runs_pass2_before_final_merge(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    pass1 = _safe_order("pass1")
    pass2 = _safe_order("pass2")
    _write_workorder(report_dir, [pass1])
    attempt_base_refs = []

    def fake_attempt(**kwargs):
        attempt_base_refs.append((kwargs["branch_prefix"], kwargs["base_ref"]))
        return _successful_attempt(**kwargs)

    monkeypatch.setattr(mod, "_attempt_codex_batch", fake_attempt)
    monkeypatch.setattr(
        mod,
        "_run_two_pass_regeneration",
        lambda **kwargs: (
            {"status": "regeneration_completed", "results": [{"status": "merged_pass1"}]},
            {
                "generation_id": "g2",
                "orders": [pass1, pass2],
                "lineage": {"new_order_ids": ["pass2"]},
            },
        ),
    )
    monkeypatch.setattr(
        mod,
        "_merge_and_push_main",
        lambda **kwargs: (
            {
                "status": "merged_main",
                "merged_main_sha": "main-sha",
                "branches": [item["branch"] for item in kwargs["branch_commits"]],
            },
            {"status": "pushed", "pushed": True, "exit_code": 0},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "completed"
    assert report["two_pass_status"] == "pass2_completed"
    assert report["canonical_implement_order_ids"] == ["pass1", "pass2"]
    assert report["pass2_order_ids"] == ["pass2"]
    assert report["pass2_selection_reason"] == [{"order_id": "pass2", "reason": "new_or_changed_order"}]
    assert all(item["final_status"] == "completed" for item in report["order_execution_results"])
    assert ("codex-workorder-pass2", "codex-regeneration-2026-06-03") in attempt_base_refs


def test_two_pass_regeneration_failure_blocks_completion(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    _write_workorder(report_dir, [_safe_order("pass1")])
    monkeypatch.setattr(mod, "_attempt_codex_batch", _successful_attempt)
    monkeypatch.setattr(
        mod,
        "_run_two_pass_regeneration",
        lambda **kwargs: (
            {"status": "blocked_regeneration_failed", "results": [{"status": "fail"}]},
            {},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_regeneration_failed"
    assert report["two_pass_status"] == "blocked_regeneration_failed"
    assert report["main_merge_result"]["status"] == "not_required"


def test_two_pass_regeneration_blocks_when_regenerated_workorder_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        mod,
        "_prepare_regeneration_worktree",
        lambda **kwargs: (tmp_path / "regen", {"status": "merged_pass1", "worktree": str(tmp_path / "regen")}),
    )

    status, regenerated = mod._run_two_pass_regeneration(
        target_date="2026-06-03",
        max_orders=5,
        branch_commits=[{"branch": "pass1"}],
        command_runner=lambda cmd, cwd=None: 0,
        dry_run=False,
    )

    assert regenerated == {}
    assert status["status"] == "blocked_regeneration_failed"
    assert status["results"][-1]["reason"] == "regenerated_workorder_missing_or_invalid"


def test_two_pass_new_unsafe_order_is_terminal_user_authority_not_pass2(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    pass1 = _safe_order("pass1")
    unsafe = _safe_order("unsafe", title="provider route change")
    _write_workorder(report_dir, [pass1])
    monkeypatch.setattr(mod, "_attempt_codex_batch", _successful_attempt)
    monkeypatch.setattr(
        mod,
        "_run_two_pass_regeneration",
        lambda **kwargs: (
            {"status": "regeneration_completed", "results": [{"status": "merged_pass1"}]},
            {"generation_id": "g2", "orders": [pass1, unsafe], "lineage": {"new_order_ids": ["unsafe"]}},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "blocked_non_recoverable"
    assert report["pass2_order_ids"] == []
    assert report["normalized_out_orders"][-1]["order_id"] == "unsafe"
    assert report["normalized_out_orders"][-1]["terminal_status"] == "requires_user_authority"


def test_two_pass_pass2_incomplete_blocks_completion(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    pass1 = _safe_order("pass1")
    pass2 = _safe_order("pass2")
    _write_workorder(report_dir, [pass1])

    def fake_attempt(**kwargs):
        if "pass2" in kwargs["branch_prefix"]:
            return {
                "attempt": kwargs["attempt_index"] + 1,
                "status": "validation_failed",
                "codex_error": None,
                "order_ids": [item["order_id"] for item in kwargs["orders"]],
                "branch": "pass2",
                "validation_results": [{"command": ["pytest"], "exit_code": 1, "status": "fail"}],
            }
        return _successful_attempt(**kwargs)

    monkeypatch.setattr(mod, "_attempt_codex_batch", fake_attempt)
    monkeypatch.setattr(
        mod,
        "_run_two_pass_regeneration",
        lambda **kwargs: (
            {"status": "regeneration_completed", "results": [{"status": "merged_pass1"}]},
            {"generation_id": "g2", "orders": [pass1, pass2], "lineage": {"new_order_ids": ["pass2"]}},
        ),
    )

    report = mod.build_codex_workorder_runner(
        "2026-06-03",
        command_runner=lambda cmd, cwd=None: 0,
        max_orders=1,
    )

    assert report["status"] == "blocked_uncompleted_implementation"
    assert report["two_pass_status"] == "blocked_new_orders_uncompleted"
    assert report["pass2_order_ids"] == ["pass2"]


def test_two_pass_regenerated_non_implement_instrumentation_promotes_to_pass2(monkeypatch, tmp_path):
    report_dir = _patch_report_dirs(monkeypatch, tmp_path)
    pass1 = _safe_order("pass1")
    attach = {
        "order_id": "attach_instrumentation",
        "decision": "attach_existing_family",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "route": "instrumentation_order",
    }
    _write_workorder(report_dir, [pass1])
    monkeypatch.setattr(mod, "_attempt_codex_batch", _successful_attempt)
    monkeypatch.setattr(
        mod,
        "_run_two_pass_regeneration",
        lambda **kwargs: (
            {"status": "regeneration_completed", "results": [{"status": "merged_pass1"}]},
            {"generation_id": "g2", "orders": [pass1, attach], "lineage": {"new_order_ids": ["attach_instrumentation"]}},
        ),
    )
    monkeypatch.setattr(
        mod,
        "_merge_and_push_main",
        lambda **kwargs: (
            {"status": "merged_main", "merged_main_sha": "main-sha", "branches": []},
            {"status": "pushed", "pushed": True, "exit_code": 0},
        ),
    )

    report = mod.build_codex_workorder_runner("2026-06-03", command_runner=lambda cmd, cwd=None: 0)

    assert report["status"] == "completed"
    assert report["pass2_order_ids"] == ["attach_instrumentation"]
    assert any(
        item["order_id"] == "attach_instrumentation" and item["terminal_status"] == "promoted_to_implement_now"
        for item in report["non_implement_dispositions"]
    )


def test_two_pass_regenerated_non_selected_order_is_not_promoted(monkeypatch, tmp_path):
    pass1 = _safe_order("pass1")
    non_selected = _safe_order("non_selected")
    pass2, normalized_out, dispositions, reasons = mod._pass2_orders_from_regenerated(
        {
            "orders": [pass1],
            "non_selected_orders": [non_selected],
            "lineage": {"new_order_ids": ["non_selected"]},
        },
        completed_pass1_ids={"pass1"},
        lineage_diff={"new_order_ids": ["non_selected"], "decision_changed_order_ids": []},
    )

    assert pass2 == []
    assert normalized_out == []
    assert dispositions == []
    assert reasons == []


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
