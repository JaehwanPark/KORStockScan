"""Run extracted launch policy against its immutable pre-extraction shell.

The historical source is executable regression evidence. These tests execute
only policy environment fragments with local promotion/retirement stubs; they
never run the supervisor, the real Python helpers, or a trading entrypoint.
"""

import os
from pathlib import Path
import re
import shlex
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "src/engine/infrastructure/main_policy_environment.sh"
BASELINE_COMMIT = "7c241ea21619ce3153f1a338f1b846b0313a894f"


@pytest.fixture(scope="module")
def original_launcher():
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:src/run_bot.sh"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def _original_function(source, name):
    match = re.search(rf"^{re.escape(name)}\(\) \{{\n.*?^\}}\n", source, re.M | re.S)
    assert match is not None, name
    return match.group(0)


def _original_environment_script(source):
    definitions = "\n".join(
        _original_function(source, name)
        for name in (
            "apply_retired_runtime_policy_env",
            "apply_authoritative_ai_context_promotion",
            "reset_runtime_policy_env_before_handoff",
        )
    )
    defaults = source.split("    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN=", 1)[1]
    defaults = (
        "    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN="
        + defaults.split(
            '    RUNTIME_TARGET_DATE="',
            1,
        )[0]
    )
    handoff = source.split("    reset_runtime_policy_env_before_handoff\n", 1)[1]
    handoff = (
        "    reset_runtime_policy_env_before_handoff\n"
        + handoff.split(
            "    verify_threshold_runtime_env_handoff",
            1,
        )[0]
    )
    final = source.split(
        "    # Reassert removed one-off namespaces after verification.", 1
    )[1]
    final = (
        "    # Reassert removed one-off namespaces after verification."
        + final.split(
            "    export_runtime_source_provenance",
            1,
        )[0]
    )
    return definitions + defaults + handoff + final


def _new_environment_script():
    return f"""
. {shlex.quote(str(HELPER))}
apply_main_policy_defaults
apply_main_policy_handoff "$RUNTIME_TARGET_DATE" "$THRESHOLD_RUNTIME_ENV" || exit 1
apply_main_policy_final_environment
"""


@pytest.fixture
def synthetic_project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "data/config").mkdir(parents=True)
    (tmp_path / ".venv/bin").mkdir(parents=True)
    stub = tmp_path / ".venv/bin/python"
    stub.write_text("""#!/bin/bash
printf '%s\\n' "$*" >> "$STUB_CALL_TRACE"
case "$*" in
  *src.engine.automation.ai_multi_timeframe_context_promotion*)
    [ "${STUB_PROMOTION_FAIL:-false}" != true ] || exit 9
    printf '%s\\n' "export KORSTOCKSCAN_PRECEDENCE_TEST=promotion" \
      "export KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=false" \
      "export KORSTOCKSCAN_PROMOTION_TARGET_DATE=2026-10-19"
    ;;
  *src.engine.lifecycle.retirement*)
    [ "${STUB_RETIREMENT_FAIL:-false}" != true ] || exit 8
    printf '%s\\n' "export KORSTOCKSCAN_PRECEDENCE_TEST=retirement" \
      "export KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=false" \
      "export KORSTOCKSCAN_WIDGET_ENABLED=false"
    ;;
  *) exit 88 ;;
esac
""")
    stub.chmod(0o755)
    return tmp_path


def _run(project, script, *, inherited=None, bootstrap="", custody="", failure=None):
    bootstrap_path = project / "bootstrap.env"
    bootstrap_path.write_text(bootstrap)
    custody_path = project / "data/config/native_owner_custody.env"
    custody_path.write_text(custody)
    trace = project / "helper-calls.txt"
    trace.unlink(missing_ok=True)
    output = project / "environment.bin"
    output.unlink(missing_ok=True)
    environment = {
        "PATH": os.defpath,
        "LC_ALL": "C.UTF-8",
        "PROJECT_DIR": str(project),
        "RUNTIME_TARGET_DATE": "2026-10-19",
        "THRESHOLD_RUNTIME_ENV": str(bootstrap_path),
        "STUB_CALL_TRACE": str(trace),
        **(inherited or {}),
        **(failure or {}),
    }
    result = subprocess.run(
        ["bash", "-e", "-c", script + f"\nenv -0 > {shlex.quote(str(output))}\n"],
        cwd=project / "src",
        env=environment,
        text=True,
        capture_output=True,
        timeout=5,
    )
    values = {}
    if output.exists():
        for record in output.read_bytes().split(b"\0"):
            key, separator, value = record.partition(b"=")
            if separator and key.startswith(b"KORSTOCKSCAN_"):
                values[key.decode()] = value.decode()
    return result, values, trace.read_text().splitlines() if trace.exists() else []


@pytest.mark.parametrize("polluted", [False, True])
def test_extracted_shell_is_equivalent_to_actual_original_launcher(
    original_launcher,
    synthetic_project,
    polluted,
):
    inherited = {
        "KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN": "0.99",
        "KORSTOCKSCAN_SCALPING_MAX_BUY_BUDGET_KRW": "999999",
        "KORSTOCKSCAN_PRECEDENCE_TEST": "inherited",
        "KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED": "false",
    }
    if polluted:
        inherited.update(
            {
                "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_PATH": "/old/approval.json",
                "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_SHA256": "old-approval",
                "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH": "/old/rollout.json",
                "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_SHA256": "old-rollout",
                "KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH": "/old/promotion.json",
                "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY": "999",
                "KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_FILE": "/old/sor.json",
                "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED": "true",
                "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED": "true",
                "KORSTOCKSCAN_WS_COMPLETED_BARS_PUBLISH": "0",
                "KORSTOCKSCAN_WS_COMPLETED_BAR_SYMBOLS": "123456",
            }
        )
    bootstrap = """
KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN=0.15
KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX=0.21
KORSTOCKSCAN_MAIN_FIXED_WATCH_005930_ENABLED=false
KORSTOCKSCAN_MAIN_FIXED_WATCH_034020_ENABLED=
KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=false
KORSTOCKSCAN_PRECEDENCE_TEST=bootstrap
KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_PATH=/new/approval.json
KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED=true
KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED=true
"""
    custody = """
KORSTOCKSCAN_PRECEDENCE_TEST=custody
KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=false
KORSTOCKSCAN_MAIN_FIXED_WATCH_036930_ENABLED=false
KORSTOCKSCAN_NATIVE_MANUAL_OWNER=operator
"""
    old_result, old_map, old_trace = _run(
        synthetic_project,
        _original_environment_script(original_launcher),
        inherited=inherited,
        bootstrap=bootstrap,
        custody=custody,
    )
    new_result, new_map, new_trace = _run(
        synthetic_project,
        _new_environment_script(),
        inherited=inherited,
        bootstrap=bootstrap,
        custody=custody,
    )
    assert old_result.returncode == 0, old_result.stderr
    assert new_result.returncode == 0, new_result.stderr
    assert new_map == old_map
    assert len(new_map) > 60
    assert (
        new_trace
        == old_trace
        == [
            "-m src.engine.automation.ai_multi_timeframe_context_promotion --date 2026-10-19 --mode runtime-env-exports",
            "-m src.engine.lifecycle.retirement --shell-commands",
        ]
    )
    assert new_map["KORSTOCKSCAN_PRECEDENCE_TEST"] == "retirement"
    assert new_map["KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED"] == "true"
    assert new_map["KORSTOCKSCAN_MAIN_FIXED_WATCH_005930_ENABLED"] == "false"
    assert new_map["KORSTOCKSCAN_MAIN_FIXED_WATCH_034020_ENABLED"] == "true"
    assert new_map["KORSTOCKSCAN_MAIN_FIXED_WATCH_036930_ENABLED"] == "false"
    assert new_map["KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN"] == "0.15"
    assert new_map["KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX"] == "0.21"
    assert new_map["KORSTOCKSCAN_SCALPING_MAX_BUY_BUDGET_KRW"] == "0"
    assert (
        new_map["KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_PATH"]
        == "/new/approval.json"
    )
    for retired_or_old in (
        "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED",
        "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_SHA256",
        "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH",
        "KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY",
        "KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_FILE",
    ):
        assert retired_or_old not in new_map
    if polluted:
        assert new_map["KORSTOCKSCAN_WS_COMPLETED_BARS_PUBLISH"] == "0"
        assert new_map["KORSTOCKSCAN_WS_COMPLETED_BAR_SYMBOLS"] == "123456"


@pytest.mark.parametrize("failure", ["STUB_PROMOTION_FAIL", "STUB_RETIREMENT_FAIL"])
def test_failed_authoritative_overlay_stops_before_final_environment(
    original_launcher,
    synthetic_project,
    failure,
):
    old_result, old_map, old_trace = _run(
        synthetic_project,
        _original_environment_script(original_launcher),
        failure={failure: "true"},
    )
    new_result, new_map, new_trace = _run(
        synthetic_project,
        _new_environment_script(),
        failure={failure: "true"},
    )
    assert old_result.returncode == new_result.returncode == 1
    assert old_map == new_map == {}
    assert old_trace == new_trace
    assert len(new_trace) == (1 if failure == "STUB_PROMOTION_FAIL" else 2)


def test_sourcing_shared_helper_is_definition_only(synthetic_project):
    result, values, trace = _run(
        synthetic_project,
        f". {shlex.quote(str(HELPER))}",
        inherited={"KORSTOCKSCAN_PRECEDENCE_TEST": "unchanged"},
    )
    assert result.returncode == 0, result.stderr
    assert values == {"KORSTOCKSCAN_PRECEDENCE_TEST": "unchanged"}
    assert trace == []


def test_live_launcher_calls_common_policy_functions_at_existing_boundaries():
    source = (ROOT / "src/run_bot.sh").read_text()
    assert (
        '. "$PROJECT_DIR/src/engine/infrastructure/main_policy_environment.sh"'
        in source
    )
    loop = source.split("while true; do", 1)[1]
    assert loop.index("apply_main_policy_defaults") < loop.index(
        'RUNTIME_TARGET_DATE="'
    )
    assert loop.index("apply_main_policy_handoff") < loop.index(
        "verify_threshold_runtime_env_handoff"
    )
    assert loop.index("verify_threshold_runtime_env_handoff") < loop.index(
        "apply_main_policy_final_environment"
    )
    assert loop.index("apply_main_policy_final_environment") < loop.index(
        "export_runtime_source_provenance"
    )
    assert "reset_runtime_policy_env_before_handoff" not in loop
