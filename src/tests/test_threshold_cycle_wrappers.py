from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_postclose_wrapper_retires_common_daily_ev_and_generic_workorder():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    assert "src.engine.daily_threshold_cycle_report" not in script
    assert "src.engine.threshold_cycle_ev_report" not in script
    assert "run_threshold_cycle_calibration.sh" not in script
    assert "src.engine.build_code_improvement_workorder" not in script
    assert "src.engine.runtime_approval_summary" in script
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert script.count("--require-summary-handoff") >= 3


def test_postclose_status_records_direct_owner_producer_flags():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    for flag in (
        "observation_source_quality_audit",
        "entry_split_order_plan",
        "scale_in_split_order_plan",
        "samsung_machine_entry_tuning",
        "low_price_two_leg_tuning",
        "low_price_two_leg_candidate_recommendation",
        "intraday_ws_freshness_finalize",
        "ai_decision_action_outcome_calibration",
    ):
        assert f'"{flag}"' in script


def test_preopen_orders_direct_publishers_before_bootstrap_and_consumers():
    script = _text("deploy/run_threshold_cycle_preopen.sh")
    publishers = [
        "low_price_two_leg_policy_apply",
        "machine_microstructure_policy_approval",
        "machine_entry_timing_tuning",
        "scanner_lookup_attention_policy",
    ]
    bootstrap = script.index("src.engine.automation.runtime_policy_bootstrap")
    assert all(script.index(name) < bootstrap for name in publishers)
    assert bootstrap < script.index("src.engine.scalping.entry_setup_live_policy")
    assert "--receipt" in script
    assert "src.engine.threshold_cycle_preopen_apply" not in script


def test_preopen_uses_single_lock_and_exact_date_bootstrap():
    script = _text("deploy/run_threshold_cycle_preopen.sh")
    assert "flock -n 9" in script
    assert 'runtime_policy_bootstrap_${TARGET_DATE}.env' in script
    assert "threshold_runtime_env_${TARGET_DATE}" not in script


def test_launcher_fails_closed_on_bootstrap_and_verifies_before_bot():
    script = _text("src/run_bot.sh")
    path = 'runtime_policy_bootstrap_$(TZ=Asia/Seoul date +%F).env'
    assert path in script
    assert "src.engine.automation.runtime_policy_bootstrap" in script
    assert script.index("wait_for_threshold_runtime_env") < script.index("bot_main.py")
    assert script.index("verify_threshold_runtime_env_handoff") < script.index("bot_main.py")
    assert "threshold_cycle_preopen_apply" not in script


def test_deleted_common_modules_have_no_wrapper_calls():
    scripts = _text("deploy/run_threshold_cycle_postclose.sh") + _text("deploy/run_threshold_cycle_preopen.sh")
    for name in (
        "daily_threshold_cycle_report",
        "threshold_cycle_ev_report",
        "threshold_cycle_preopen_apply",
        "refresh-machine-evaluation-only",
    ):
        assert name not in scripts
