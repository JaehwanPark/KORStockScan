import importlib

import pytest

import src.utils.constants as constants


@pytest.fixture(autouse=True)
def reload_constants_module():
    yield
    importlib.reload(constants)


def test_trading_rules_default_latency_canary_thresholds(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO", raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS == 260
    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS == 450
    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO == 0.0100


def test_trading_rules_remote_v2_profile_relaxes_latency_canary_jitter(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "remote_v2")
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS == 400
    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS == 450


def test_trading_rules_env_override_wins_over_profile(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "remote_v2")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", "420")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS == 420


def test_trading_rules_entry_latency_classifier_jitter_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION", "1200")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION", "1500")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION", "0.01")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE", "75")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS", "1200")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS", "1500")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO", "0.01")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION == 1200
    assert reloaded.TRADING_RULES.SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION == 1500
    assert reloaded.TRADING_RULES.SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION == 0.01
    assert reloaded.TRADING_RULES.SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED is True
    assert reloaded.TRADING_RULES.SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE == 75
    assert reloaded.TRADING_RULES.SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS == 1200
    assert reloaded.TRADING_RULES.SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS == 1500
    assert reloaded.TRADING_RULES.SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO == 0.01


def test_trading_rules_scalping_entry_price_percent_bps_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_ENTRY_PRICE_DEFENSE_MODE", "percent_bps")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS", "50")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS", "10")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS", "35")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_NORMAL_WEAK_DEFENSIVE_BPS", "65")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_MICRO_POSITIVES", "2")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_SPREAD_TICKS", "5")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES",
        "defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS", "35")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_TARGET_MODE", "best_bid_near")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS", "1")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS", "0")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS", "20")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_TARGET_MODE", "best_bid_near")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS", "1")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS", "0")
    monkeypatch.setenv("KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_PRICE_LIVE_TUNING_SELECTED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_WEAK_SEC", "20")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_BASE_SEC", "45")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_STRONG_SEC", "90")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_MIN_AI_SCORE", "65")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_EMERGENCY_PCT", "-2.8")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_MAX_WORSEN_PCT", "0.30")
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_EXIT_LIVE_TUNING_SELECTED", "true")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALPING_ENTRY_PRICE_DEFENSE_MODE == "percent_bps"
    assert reloaded.TRADING_RULES.SCALPING_NORMAL_DEFENSIVE_BPS == 50
    assert reloaded.TRADING_RULES.SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS == 10
    assert reloaded.TRADING_RULES.SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS == 35
    assert reloaded.TRADING_RULES.SCALPING_NORMAL_WEAK_DEFENSIVE_BPS == 65
    assert reloaded.TRADING_RULES.SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED is True
    assert reloaded.TRADING_RULES.SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_MICRO_POSITIVES == 2
    assert reloaded.TRADING_RULES.SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_SPREAD_TICKS == 5
    assert reloaded.TRADING_RULES.SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED is True
    assert (
        reloaded.TRADING_RULES.SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES
        == "defensive_missed_upside_v1,reference_target_cap_missed_upside_v1"
    )
    assert reloaded.TRADING_RULES.SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS == 35
    assert reloaded.TRADING_RULES.SCALP_DEFENSIVE_MISSED_UPSIDE_TARGET_MODE == "best_bid_near"
    assert reloaded.TRADING_RULES.SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS == 1
    assert reloaded.TRADING_RULES.SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS == 0
    assert reloaded.TRADING_RULES.SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS == 20
    assert reloaded.TRADING_RULES.SCALP_REFERENCE_TARGET_MISSED_UPSIDE_TARGET_MODE == "best_bid_near"
    assert reloaded.TRADING_RULES.SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS == 1
    assert reloaded.TRADING_RULES.SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS == 0
    assert reloaded.TRADING_RULES.DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED is True
    assert reloaded.TRADING_RULES.ENTRY_PRICE_LIVE_TUNING_SELECTED is True
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED is True
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_WEAK_SEC == 20
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_BASE_SEC == 45
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_STRONG_SEC == 90
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_MIN_AI_SCORE == 65
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_EMERGENCY_PCT == -2.8
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_DYNAMIC_GRACE_MAX_WORSEN_PCT == 0.30
    assert reloaded.TRADING_RULES.HOLDING_EXIT_LIVE_TUNING_SELECTED is True


def test_trading_rules_real_entry_panic_gap_weight_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_REAL_ENTRY_PANIC_GAP_WEIGHT_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_REAL_ENTRY_PANIC_SELL_EXTRA_BPS", "35")
    monkeypatch.setenv("KORSTOCKSCAN_REAL_ENTRY_PANIC_SELL_BROKEN_EXTRA_BPS", "55")
    monkeypatch.setenv("KORSTOCKSCAN_REAL_ENTRY_PANIC_BUY_WATCH_REDUCE_BPS", "12")
    monkeypatch.setenv("KORSTOCKSCAN_REAL_ENTRY_PANIC_BUY_ACTIVE_REDUCE_BPS", "22")
    monkeypatch.setenv("KORSTOCKSCAN_REAL_ENTRY_PANIC_BUY_EXHAUSTION_EXTRA_BPS", "32")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.REAL_ENTRY_PANIC_GAP_WEIGHT_ENABLED is False
    assert reloaded.TRADING_RULES.REAL_ENTRY_PANIC_SELL_EXTRA_BPS == 35
    assert reloaded.TRADING_RULES.REAL_ENTRY_PANIC_SELL_BROKEN_EXTRA_BPS == 55
    assert reloaded.TRADING_RULES.REAL_ENTRY_PANIC_BUY_WATCH_REDUCE_BPS == 12
    assert reloaded.TRADING_RULES.REAL_ENTRY_PANIC_BUY_ACTIVE_REDUCE_BPS == 22
    assert reloaded.TRADING_RULES.REAL_ENTRY_PANIC_BUY_EXHAUSTION_EXTRA_BPS == 32


def test_trading_rules_dynamic_strength_relief_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS", "SCANNER")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS",
        "below_window_buy_value,below_buy_ratio",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO", "0.90")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL", "0.02")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL", "0.01")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED is False
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS == ("SCANNER",)
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS == (
        "below_window_buy_value",
        "below_buy_ratio",
    )
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO == 0.90
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL == 0.02
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL == 0.01


def test_trading_rules_soft_stop_micro_grace_sec_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SOFT_STOP_MICRO_GRACE_SEC", "60")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_MICRO_GRACE_SEC == 60
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT == -2.0
    assert reloaded.TRADING_RULES.SCALP_HARD_STOP == -2.5


def test_trading_rules_scalp_safe_profit_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SAFE_PROFIT", "1.0")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_SAFE_PROFIT == 1.0
    assert reloaded.TRADING_RULES.SCALP_TRAILING_LIMIT_WEAK == 0.4
    assert reloaded.TRADING_RULES.SCALP_TRAILING_LIMIT_STRONG == 0.8


def test_trading_rules_profit_stagnation_exit_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_EXIT_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_PROFIT_PCT", "1.0")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_SEC", "180")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MAX_PROFIT_MOVE_PCT", "0.15")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MAX_PEAK_IMPROVE_PCT", "0.10")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_AI_SCORE", "45")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_PROFIT_STAGNATION_EXIT_ENABLED is True
    assert reloaded.TRADING_RULES.SCALP_PROFIT_STAGNATION_MIN_PROFIT_PCT == 1.0
    assert reloaded.TRADING_RULES.SCALP_PROFIT_STAGNATION_MIN_SEC == 180
    assert reloaded.TRADING_RULES.SCALP_PROFIT_STAGNATION_MAX_PROFIT_MOVE_PCT == 0.15
    assert reloaded.TRADING_RULES.SCALP_PROFIT_STAGNATION_MAX_PEAK_IMPROVE_PCT == 0.10
    assert reloaded.TRADING_RULES.SCALP_PROFIT_STAGNATION_MIN_AI_SCORE == 45


def test_trading_rules_ai_cadence_defaults_are_rate_limited(monkeypatch):
    for key in (
        "KORSTOCKSCAN_AI_WATCHING_COOLDOWN",
        "KORSTOCKSCAN_AI_HOLDING_MIN_COOLDOWN",
        "KORSTOCKSCAN_AI_HOLDING_MAX_COOLDOWN",
        "KORSTOCKSCAN_AI_HOLDING_CRITICAL_MIN_COOLDOWN",
        "KORSTOCKSCAN_AI_HOLDING_CRITICAL_COOLDOWN",
        "KORSTOCKSCAN_AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED",
        "KORSTOCKSCAN_AI_WATCHING_SCORE_SMOOTHING_MODE",
    ):
        monkeypatch.delenv(key, raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.AI_WATCHING_COOLDOWN == 90
    assert reloaded.TRADING_RULES.AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED is False
    assert reloaded.TRADING_RULES.AI_WATCHING_SCORE_SMOOTHING_MODE == "off"
    assert reloaded.TRADING_RULES.AI_HOLDING_MIN_COOLDOWN == 45
    assert reloaded.TRADING_RULES.AI_HOLDING_MAX_COOLDOWN == 180
    assert reloaded.TRADING_RULES.AI_HOLDING_CRITICAL_MIN_COOLDOWN == 20
    assert reloaded.TRADING_RULES.AI_HOLDING_CRITICAL_COOLDOWN == 45
    assert reloaded.TRADING_RULES.AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED is True


def test_trading_rules_scalp_sim_candidate_window_defaults_and_env_override(monkeypatch):
    for key in (
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY",
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY",
    ):
        monkeypatch.delenv(key, raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY == 240
    assert reloaded.TRADING_RULES.SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY == (
        "09:00-10:00=84,10:00-12:00=48,12:00-14:00=60,14:00-15:30=48"
    )

    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY", "320")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY",
        "09:00-10:00=100,10:00-15:30=220",
    )
    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY == 320
    assert reloaded.TRADING_RULES.SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY == (
        "09:00-10:00=100,10:00-15:30=220"
    )


def test_trading_rules_runtime_shadow_defaults_are_off(monkeypatch):
    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY is False
    assert reloaded.TRADING_RULES.SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED is False
    assert reloaded.TRADING_RULES.SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_ENABLED is False
    assert reloaded.TRADING_RULES.SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED is False
    assert reloaded.TRADING_RULES.SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED is True
    assert reloaded.TRADING_RULES.OPENAI_DUAL_PERSONA_SHADOW_MODE is False


def test_trading_rules_ai_cadence_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_WATCHING_COOLDOWN", "120")
    monkeypatch.setenv("KORSTOCKSCAN_AI_HOLDING_MIN_COOLDOWN", "60")
    monkeypatch.setenv("KORSTOCKSCAN_AI_HOLDING_MAX_COOLDOWN", "240")
    monkeypatch.setenv("KORSTOCKSCAN_AI_HOLDING_CRITICAL_MIN_COOLDOWN", "30")
    monkeypatch.setenv("KORSTOCKSCAN_AI_HOLDING_CRITICAL_COOLDOWN", "75")
    monkeypatch.setenv("KORSTOCKSCAN_AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_AI_WATCHING_SCORE_SMOOTHING_MODE", "report_only")
    monkeypatch.setenv("KORSTOCKSCAN_AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA", "12.5")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.AI_WATCHING_COOLDOWN == 120
    assert reloaded.TRADING_RULES.AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED is True
    assert reloaded.TRADING_RULES.AI_WATCHING_SCORE_SMOOTHING_MODE == "report_only"
    assert reloaded.TRADING_RULES.AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA == 12.5
    assert reloaded.TRADING_RULES.AI_HOLDING_MIN_COOLDOWN == 60
    assert reloaded.TRADING_RULES.AI_HOLDING_MAX_COOLDOWN == 240
    assert reloaded.TRADING_RULES.AI_HOLDING_CRITICAL_MIN_COOLDOWN == 30
    assert reloaded.TRADING_RULES.AI_HOLDING_CRITICAL_COOLDOWN == 75
    assert reloaded.TRADING_RULES.AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED is False


def test_trading_rules_error_detector_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_DAEMON_INTERVAL_SEC", "120")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC", "45")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_START_HHMM", "07:45")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_END_HHMM", "22:50")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC", "240")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_POSTCLOSE_BOT_ISOLATION_MAX_AGE_SEC", "30000")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_CPU_BUSY_MAX_PCT", "95")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC", "900")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.ERROR_DETECTOR_ENABLED is False
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_DAEMON_INTERVAL_SEC == 120
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC == 45
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED is True
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_BOT_EXPECTED_START_HHMM == "07:45"
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_BOT_EXPECTED_END_HHMM == "22:50"
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC == 240
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_POSTCLOSE_BOT_ISOLATION_MAX_AGE_SEC == 30000
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_CPU_BUSY_MAX_PCT == 95
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC == 900


def test_trading_rules_stale_lock_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC", "1800")
    monkeypatch.setenv("KORSTOCKSCAN_ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED", "false")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED is False
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC == 1800
    assert reloaded.TRADING_RULES.ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED is False


def test_trading_rules_log_text_noise_defaults_are_off(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WATCHING_STATE_DEBUG_LOG_ENABLED", raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED is False
    assert "order_bundle_submitted" in reloaded.TRADING_RULES.PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST
    assert reloaded.TRADING_RULES.WATCHING_STATE_DEBUG_LOG_ENABLED is False


def test_trading_rules_log_text_noise_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST",
        "order_bundle_submitted,sell_order_failed",
    )
    monkeypatch.setenv("KORSTOCKSCAN_WATCHING_STATE_DEBUG_LOG_ENABLED", "true")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED is True
    assert reloaded.TRADING_RULES.PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST == (
        "order_bundle_submitted",
        "sell_order_failed",
    )
    assert reloaded.TRADING_RULES.WATCHING_STATE_DEBUG_LOG_ENABLED is True
