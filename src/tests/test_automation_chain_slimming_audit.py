from collections import Counter
import os
from pathlib import Path
import subprocess

from src.engine.automation import automation_chain_slimming_audit as mod


def test_static_parser_detects_repeated_ev_verifier_and_lifecycle_windows():
    report = mod.build_report("2026-06-02")

    producers = Counter(item["producer"] for item in report["step_inventory"])
    assert producers["src.engine.threshold_cycle_ev_report"] == 3
    assert producers["src.engine.verify_threshold_cycle_postclose_chain"] == 2
    lifecycle_context = next(
        item for item in report["step_inventory"] if item["producer"] == "src.engine.lifecycle_ai_context"
    )
    assert "RUN_LIFECYCLE_AI_CONTEXT" in lifecycle_context["default_flags"]
    assert lifecycle_context["default_enabled"] is True

    candidates = report["slimming_candidates"]
    assert any(
        item["producer"] == "src.engine.threshold_cycle_ev_report"
        and item["classification"] == "duplicate_refresh_candidate"
        and item["classification_group"] == "change_triggered"
        for item in candidates
    )
    assert any(
        item["producer"] == "src.engine.lifecycle_decision_matrix"
        and item["classification"] == "dependent_refresh"
        and item["classification_reason"] == "upstream_dependent_refresh_keep_daily"
        for item in report["step_inventory"]
    )
    assert any(
        item["producer"] == "src.engine.lifecycle_ai_context"
        and item["classification"] == "dependent_refresh"
        for item in report["step_inventory"]
    )
    assert any(
        item["producer"] == "src.engine.swing_strategy_discovery_sim"
        and item["classification"] == "mutually_exclusive_static_duplicate"
        for item in report["step_inventory"]
    )
    assert not any(
        item["producer"] == "src.engine.swing_strategy_discovery_sim"
        and item["classification"] == "duplicate_refresh_candidate"
        for item in candidates
    )
    assert any(
        item["producer"] == "src.engine.verify_threshold_cycle_postclose_chain"
        and item["classification"] == "duplicate_refresh_candidate"
        for item in candidates
    )
    assert any(
        item["producer"] == "src.engine.verify_threshold_cycle_postclose_chain"
        and item["classification"] == "core_daily"
        and item["classification_reason"] == "final_fail_closed_postclose_verifier"
        for item in report["step_inventory"]
    )
    assert any(
        item["producer"] == "src.engine.lifecycle_decision_matrix"
        and item["classification"] == "change_triggered_candidate"
        and item["classification_group"] == "change_triggered"
        for item in candidates
    )
    assert any(
        item["producer"] == "src.engine.pattern_lab_ai_review"
        and item["classification"] == "triggered_deep_review_candidate"
        for item in candidates
    )


def test_slimming_candidates_and_workorders_are_report_only():
    report = mod.build_report("2026-06-02")

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert "runtime_threshold_apply" in report["forbidden_uses"]
    assert report["summary"]["duplicate_refresh_candidates"] >= 3
    assert report["summary"]["true_duplicate_refresh_candidates"] == report["summary"]["duplicate_refresh_candidates"]
    assert report["summary"]["dependent_refresh_steps"] >= 2
    assert report["summary"]["mutually_exclusive_static_duplicates"] >= 1
    assert "deprecated_candidate" in report["summary"]["classification_group_counts"]
    assert report["protected_refreshes"]

    assert report["slimming_candidates"]
    for item in report["slimming_candidates"]:
        assert item["runtime_effect"] is False
        assert item["allowed_runtime_apply"] is False
        assert item["classification_group"] in {
            "change_triggered",
            "manual_or_weekly",
            "deprecated_candidate",
        }
        assert "broker_submit" in item["forbidden_uses"]
        assert "runtime_threshold_apply" in item["forbidden_uses"]

    assert report["implementation_workorders"]
    for item in report["implementation_workorders"]:
        assert item["runtime_effect"] is False
        assert item["allowed_runtime_apply"] is False


def test_aggressive_profile_deep_audit_candidates_move_to_manual_or_weekly():
    report = mod.build_report("2026-06-02", profile="aggressive")

    deep_candidates = [
        item
        for item in report["slimming_candidates"]
        if item["classification"] == "triggered_deep_review_candidate"
    ]
    assert deep_candidates
    assert all(item["recommended_mode"] == "manual_or_weekly" for item in deep_candidates)


def test_dependency_defaults_can_create_deprecated_candidate_and_ev_function_calls_are_expanded():
    script = '''
RUN_PARENT="${THRESHOLD_CYCLE_RUN_PARENT:-false}"
RUN_OPENAI_WS_STABILITY_REPORT="${THRESHOLD_CYCLE_RUN_OPENAI_WS_STABILITY_REPORT:-$RUN_PARENT}"
RUN_LIFECYCLE_AI_CONTEXT="${THRESHOLD_CYCLE_RUN_LIFECYCLE_AI_CONTEXT:-$RUN_PARENT}"
run_threshold_cycle_ev_and_wait() {
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_ev_report --date "$TARGET_DATE"
  wait_for_artifacts "$PROJECT_DIR/data/report/threshold_cycle_ev/threshold_cycle_ev_${TARGET_DATE}.json"
}
if [ "$RUN_OPENAI_WS_STABILITY_REPORT" = "true" ]; then
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.openai_ws_stability_report --date "$TARGET_DATE"
fi
if [ "$RUN_LIFECYCLE_AI_CONTEXT" = "true" ]; then
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode context
fi
run_threshold_cycle_ev_and_wait "pre_workorder"
run_threshold_cycle_ev_and_wait "post_workorder_refresh"
'''
    defaults = mod._resolve_run_defaults(mod._extract_run_defaults(script))
    calls = mod._extract_module_calls(script, "postclose", "2026-06-02")
    inventory, candidates = mod._build_inventory(calls, defaults, "standard")

    producers = Counter(item["producer"] for item in inventory)
    assert producers["src.engine.threshold_cycle_ev_report"] == 2

    openai_step = next(item for item in inventory if item["producer"] == "src.engine.openai_ws_stability_report")
    assert openai_step["default_enabled"] is False
    assert openai_step["classification"] == "deprecated_candidate"
    assert openai_step["classification_group"] == "deprecated_candidate"
    lifecycle_context_step = next(item for item in inventory if item["producer"] == "src.engine.lifecycle_ai_context")
    assert lifecycle_context_step["default_flag"] == "RUN_LIFECYCLE_AI_CONTEXT"
    assert lifecycle_context_step["default_enabled"] is False
    assert lifecycle_context_step["classification"] == "deprecated_candidate"

    openai_candidate = next(
        item for item in candidates if item["producer"] == "src.engine.openai_ws_stability_report"
    )
    assert openai_candidate["recommended_mode"] == "deprecated_candidate"


def test_nested_guard_defaults_are_not_flattened_as_or_conditions():
    script = '''
RUN_PARENT="${THRESHOLD_CYCLE_RUN_PARENT:-true}"
RUN_CHILD="${THRESHOLD_CYCLE_RUN_CHILD:-false}"
if [ "$RUN_PARENT" = "true" ] || [ "$RUN_PARENT" = "1" ]; then
  if [ "$RUN_CHILD" = "true" ] || [ "$RUN_CHILD" = "1" ]; then
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE"
  fi
fi
'''
    defaults = mod._resolve_run_defaults(mod._extract_run_defaults(script))
    calls = mod._extract_module_calls(script, "postclose", "2026-06-02")
    inventory, _ = mod._build_inventory(calls, defaults, "standard")

    lifecycle_context_step = next(item for item in inventory if item["producer"] == "src.engine.lifecycle_ai_context")
    assert lifecycle_context_step["default_flags"] == ["RUN_CHILD", "RUN_PARENT"]
    assert lifecycle_context_step["default_enabled"] is False
    assert lifecycle_context_step["default_enabled_resolution"] == "resolved_guard_nested_all"
    assert lifecycle_context_step["classification"] == "deprecated_candidate"


def test_multiline_command_if_does_not_pop_parent_run_guards():
    script = '''
RUN_PARENT="${THRESHOLD_CYCLE_RUN_PARENT:-true}"
RUN_CHILD="${THRESHOLD_CYCLE_RUN_CHILD:-true}"
if [ "$RUN_PARENT" = "true" ] || [ "$RUN_PARENT" = "1" ]; then
  if [ "$RUN_CHILD" = "true" ] || [ "$RUN_CHILD" = "1" ]; then
    if ! run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix \\
      --date "$TARGET_DATE"; then
      echo failed
    fi
    if ! run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_bucket_discovery \\
      --date "$TARGET_DATE"; then
      echo failed
    fi
  fi
fi
'''
    defaults = mod._resolve_run_defaults(mod._extract_run_defaults(script))
    calls = mod._extract_module_calls(script, "postclose", "2026-06-02")
    inventory, _ = mod._build_inventory(calls, defaults, "standard")

    matrix_step = next(item for item in inventory if item["producer"] == "src.engine.lifecycle_decision_matrix")
    discovery_step = next(item for item in inventory if item["producer"] == "src.engine.lifecycle_bucket_discovery")
    assert matrix_step["default_flags"] == ["RUN_CHILD", "RUN_PARENT"]
    assert discovery_step["default_flags"] == ["RUN_CHILD", "RUN_PARENT"]
    assert matrix_step["default_enabled"] is True
    assert discovery_step["default_enabled"] is True


def test_estimated_risk_is_medium_when_status_input_is_missing():
    status_inputs = {
        "postclose_status": {"status": "missing_or_unreadable"},
        "preopen_status": {"status": "available"},
    }

    assert mod._estimate_risk(Counter({"core_daily": 9}), True, status_inputs) == "medium"


def _extract_shell_function(script: str, name: str) -> str:
    lines = script.splitlines()
    start = next(index for index, line in enumerate(lines) if line == f"{name}() {{")
    for index in range(start + 1, len(lines)):
        if lines[index] == "}":
            return "\n".join(lines[start : index + 1])
    raise AssertionError(f"missing shell function end: {name}")


def _run_refresh_decision(tmp_path: Path, force: str, source_mode: str) -> str:
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    function_text = _extract_shell_function(script, "threshold_cycle_ev_refresh_decision")
    json_path = tmp_path / "threshold_cycle_ev.json"
    md_path = tmp_path / "threshold_cycle_ev.md"
    source_path = tmp_path / "source.json"
    json_path.write_text("{}", encoding="utf-8")
    md_path.write_text("# report\n", encoding="utf-8")
    os.utime(json_path, (200, 200))
    os.utime(md_path, (200, 200))
    args = [str(json_path), str(md_path), force]
    if source_mode == "older":
        source_path.write_text("{}", encoding="utf-8")
        os.utime(source_path, (100, 100))
        args.append(str(source_path))
    elif source_mode == "newer":
        source_path.write_text("{}", encoding="utf-8")
        os.utime(source_path, (300, 300))
        args.append(str(source_path))
    elif source_mode == "missing":
        args.append(str(source_path))

    proc = subprocess.run(
        ["bash", "-c", f"{function_text}\nthreshold_cycle_ev_refresh_decision \"$@\"", "bash", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def test_postclose_wrapper_duplicate_refresh_skip_contract_is_static():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'FORCE_DUPLICATE_REFRESH="${THRESHOLD_CYCLE_FORCE_DUPLICATE_REFRESH:-false}"' in script
    assert "threshold_cycle_ev_refresh_decision()" in script
    assert "duplicate_refresh_fresh" in script
    assert 'run_threshold_cycle_ev_and_wait "pre_workorder"' in script
    assert "code_improvement_workorder_${TARGET_DATE}.json" in script
    assert "pattern_lab_propagation_audit_${TARGET_DATE}.json" in script
    assert "verify_threshold_cycle_postclose_chain --date \"$TARGET_DATE\" --allow-pending-done-marker" in script
    assert "verify_threshold_cycle_postclose_chain --date \"$TARGET_DATE\"" in script


def test_postclose_wrapper_duplicate_refresh_decision_executes_timestamp_cases(tmp_path):
    assert _run_refresh_decision(tmp_path, "false", "older") == "skip"
    assert _run_refresh_decision(tmp_path, "false", "newer") == "run"
    assert _run_refresh_decision(tmp_path, "false", "missing") == "run"
    assert _run_refresh_decision(tmp_path, "true", "older") == "run"
    assert _run_refresh_decision(tmp_path, "false", "none") == "run"


def test_dependent_refresh_requires_context_not_only_module_name():
    script = '''
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode attribution
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode attribution
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix --date "$TARGET_DATE"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix --date "$TARGET_DATE"
'''
    calls = mod._extract_module_calls(script, "postclose", "2026-06-02")
    inventory, candidates = mod._build_inventory(calls, [], "standard")

    assert not any(item["classification"] == "dependent_refresh" for item in inventory)
    assert any(
        item["producer"] == "src.engine.lifecycle_ai_context"
        and item["classification"] == "duplicate_refresh_candidate"
        for item in candidates
    )
    assert any(
        item["producer"] == "src.engine.lifecycle_decision_matrix"
        and item["classification"] == "duplicate_refresh_candidate"
        for item in candidates
    )
