from collections import Counter
import os
from pathlib import Path
import subprocess

from src.engine.automation import automation_chain_slimming_audit as mod




def test_slimming_candidates_and_workorders_are_report_only():
    report = mod.build_report("2026-06-02")

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert "runtime_threshold_apply" in report["forbidden_uses"]
    assert report["summary"]["duplicate_refresh_candidates"] >= 3
    assert (
        report["summary"]["true_duplicate_refresh_candidates"]
        == report["summary"]["duplicate_refresh_candidates"]
    )
    assert report["summary"]["dependent_refresh_steps"] == 0
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
    assert all(
        item["recommended_mode"] == "manual_or_weekly" for item in deep_candidates
    )




def test_nested_guard_defaults_are_not_flattened_as_or_conditions():
    script = """
RUN_PARENT="${THRESHOLD_CYCLE_RUN_PARENT:-true}"
RUN_CHILD="${THRESHOLD_CYCLE_RUN_CHILD:-false}"
if [ "$RUN_PARENT" = "true" ] || [ "$RUN_PARENT" = "1" ]; then
  if [ "$RUN_CHILD" = "true" ] || [ "$RUN_CHILD" = "1" ]; then
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE"
  fi
fi
"""
    defaults = mod._resolve_run_defaults(mod._extract_run_defaults(script))
    calls = mod._extract_module_calls(script, "postclose", "2026-06-02")
    inventory, _ = mod._build_inventory(calls, defaults, "standard")

    lifecycle_context_step = next(
        item
        for item in inventory
        if item["producer"] == "src.engine.lifecycle_ai_context"
    )
    assert lifecycle_context_step["default_flags"] == ["RUN_CHILD", "RUN_PARENT"]
    assert lifecycle_context_step["default_enabled"] is False
    assert (
        lifecycle_context_step["default_enabled_resolution"]
        == "resolved_guard_nested_all"
    )
    assert lifecycle_context_step["classification"] == "deprecated_candidate"


def test_multiline_command_if_does_not_pop_parent_run_guards():
    script = """
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
"""
    defaults = mod._resolve_run_defaults(mod._extract_run_defaults(script))
    calls = mod._extract_module_calls(script, "postclose", "2026-06-02")
    inventory, _ = mod._build_inventory(calls, defaults, "standard")

    matrix_step = next(
        item
        for item in inventory
        if item["producer"] == "src.engine.lifecycle_decision_matrix"
    )
    discovery_step = next(
        item
        for item in inventory
        if item["producer"] == "src.engine.lifecycle_bucket_discovery"
    )
    assert matrix_step["default_flags"] == ["RUN_CHILD", "RUN_PARENT"]
    assert discovery_step["default_flags"] == ["RUN_CHILD", "RUN_PARENT"]
    assert matrix_step["default_enabled"] is True
    assert discovery_step["default_enabled"] is True


def test_estimated_risk_is_medium_when_status_input_is_missing():
    status_inputs = {
        "postclose_status": {"status": "missing_or_unreadable"},
        "preopen_status": {"status": "available"},
    }

    assert (
        mod._estimate_risk(Counter({"core_daily": 9}), True, status_inputs) == "medium"
    )


def _extract_shell_function(script: str, name: str) -> str:
    lines = script.splitlines()
    start = next(index for index, line in enumerate(lines) if line == f"{name}() {{")
    for index in range(start + 1, len(lines)):
        if lines[index] == "}":
            return "\n".join(lines[start : index + 1])
    raise AssertionError(f"missing shell function end: {name}")


def test_postclose_wrapper_common_threshold_tuning_is_retired():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'FORCE_DUPLICATE_REFRESH="${THRESHOLD_CYCLE_FORCE_DUPLICATE_REFRESH:-false}"'
        in script
    )
    assert (
        'FORCE_LIFECYCLE_BUCKET_WINDOWS="${THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS:-false}"'
        in script
    )
    assert 'FORCE_DEEP_AUDITS="${THRESHOLD_CYCLE_FORCE_DEEP_AUDITS:-false}"' in script
    assert (
        'FORCE_WORKORDER_BRANCH="${THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH:-false}"'
        in script
    )
    assert "threshold_cycle_ev_refresh_decision()" not in script
    assert "automation_trigger_decision()" in script
    assert "write_automation_trigger_decision_snapshot()" in script
    assert "refresh_automation_trigger_decision_snapshot()" in script
    assert "src.engine.automation.automation_chain_trigger_decision" in script
    assert (
        'AUTOMATION_TRIGGER_DECISION_REPORT_JSON="$PROJECT_DIR/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_${TARGET_DATE}.json"'
        in script
    )
    assert (
        'AUTOMATION_TRIGGER_DECISION_CACHE_MARKER="$PROJECT_DIR/tmp/automation_trigger_decision_${TARGET_DATE}_$$.cached"'
        in script
    )
    assert 'rm -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER"' in script
    assert "--scope all \\" in script
    assert "--write" in script
    assert 'refresh_automation_trigger_decision_snapshot "final_consumer"' in script
    assert (
        'if [ -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER" ] && [ -f "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON" ]; then'
        in script
    )
    assert "automation_trigger_reason()" in script
    assert "automation_trigger_source()" in script
    assert "trigger_reason=$trigger_reason" in script
    assert "trigger_source=$trigger_source" in script
    assert "duplicate_refresh_fresh" not in script
    assert "lifecycle_window_${lifecycle_bucket_window}" not in script
    assert "fresh_outputs_no_trigger" in script
    assert "run_threshold_cycle_ev_and_wait" not in script
    assert "src.engine.daily_threshold_cycle_report" not in script
    assert "src.engine.threshold_cycle_ev_report" not in script
    assert "src.engine.threshold_cycle_preopen_apply" not in script
    assert "pattern_lab_propagation_audit_${TARGET_DATE}.json" in script
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert "--allow-pending-done-marker" in script
    assert '"${VERIFY_DISABLED_STAGE_ARGS[@]}"' in script


def test_automation_trigger_decision_cache_reuses_production_state_contract(tmp_path):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    function_text = "\n".join(
        [
            _extract_shell_function(
                script, "write_automation_trigger_decision_snapshot"
            ),
            _extract_shell_function(script, "automation_trigger_decision"),
            _extract_shell_function(script, "automation_trigger_reason"),
            _extract_shell_function(script, "automation_trigger_source"),
        ]
    )
    fake_python = tmp_path / "fake_python.sh"
    report_path = tmp_path / "automation_chain_trigger_decision.json"
    marker_path = tmp_path / "automation_trigger_decision.cached"
    count_path = tmp_path / "write_count"
    real_python = os.environ.get("PYTHON", "python3")
    fake_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'if [ "${1:-}" = "-m" ]; then',
                '  count="$(cat "$WRITE_COUNT_PATH" 2>/dev/null || printf 0)"',
                '  count="$((count + 1))"',
                '  printf "%s\\n" "$count" > "$WRITE_COUNT_PATH"',
                '  mkdir -p "$(dirname "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON")"',
                "  cat > \"$AUTOMATION_TRIGGER_DECISION_REPORT_JSON\" <<'JSON'",
                '{"decisions":[{"step_id":"skip_step","decision":"skip","trigger_reasons":["fresh_outputs_no_trigger"]}]}',
                "JSON",
                "  exit 0",
                "fi",
                f'exec "{real_python}" "$@"',
            ]
        ),
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    shell = f"""
set -euo pipefail
run_postclose_cmd() {{
  "$@"
}}
{function_text}
TARGET_DATE=2026-06-17
FORCE_LIFECYCLE_BUCKET_WINDOWS=false
FORCE_DEEP_AUDITS=false
FORCE_WORKORDER_BRANCH=false
VENV_PY={fake_python}
AUTOMATION_TRIGGER_DECISION_REPORT_JSON={report_path}
AUTOMATION_TRIGGER_DECISION_CACHE_MARKER={marker_path}
WRITE_COUNT_PATH={count_path}
export AUTOMATION_TRIGGER_DECISION_REPORT_JSON WRITE_COUNT_PATH
automation_trigger_decision "skip_step"
first="$AUTOMATION_TRIGGER_DECISION_RESULT"
automation_trigger_decision "skip_step"
second="$AUTOMATION_TRIGGER_DECISION_RESULT"
reason="$(automation_trigger_reason "skip_step")"
source="$(automation_trigger_source)"
printf '%s|%s|%s|%s|%s\\n' "$first" "$second" "$reason" "$source" "$(cat "$WRITE_COUNT_PATH")"
"""

    proc = subprocess.run(
        ["bash", "-c", shell], check=True, capture_output=True, text=True
    )

    assert (
        proc.stdout.strip()
        == "skip|skip|fresh_outputs_no_trigger|cached_trigger_snapshot|1"
    )


def test_dependent_refresh_requires_context_not_only_module_name():
    script = """
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode attribution
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode attribution
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix --date "$TARGET_DATE"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix --date "$TARGET_DATE"
"""
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
