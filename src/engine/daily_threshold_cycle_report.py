"""Daily threshold cycle report for post-close recommendation and next-preopen apply."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from src.engine.ai_response_contracts import build_openai_response_text_format
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH, POSTGRES_URL, TRADING_RULES
from src.utils.threshold_cycle_registry import TARGET_STAGES, is_threshold_cycle_stage


REPORT_DIR = DATA_DIR / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
STAT_ACTION_REPORT_DIR = REPORT_DIR / "statistical_action_weight"
AI_DECISION_MATRIX_DIR = REPORT_DIR / "holding_exit_decision_matrix"
LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "lifecycle_decision_matrix"
CUMULATIVE_THRESHOLD_REPORT_DIR = REPORT_DIR / "threshold_cycle_cumulative"
THRESHOLD_CALIBRATION_REPORT_DIR = REPORT_DIR / "threshold_cycle_calibration"
THRESHOLD_AI_REVIEW_DIR = REPORT_DIR / "threshold_cycle_ai_review"
POST_SELL_DIR = DATA_DIR / "post_sell"
THRESHOLD_CYCLE_SCHEMA_VERSION = 3
THRESHOLD_AI_CORRECTION_SCHEMA_VERSION = 1
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
RAW_PIPELINE_FALLBACK_MAX_BYTES = 64 * 1024 * 1024
CUMULATIVE_BASELINE_START_DATE = "2026-04-21"

CALIBRATION_SAFETY_GUARDS = [
    "hard/protect/emergency stop delay >= 1",
    "order failure or receipt/provenance damage",
    "same-stage owner conflict",
    "severe loss guard breach",
]
AI_CORRECTION_ALLOWED_STATES = {"adjust_up", "adjust_down", "hold", "hold_sample", "freeze"}
AI_CORRECTION_ALLOWED_ROUTES = {"threshold_candidate", "incident", "instrumentation_gap", "normal_drift"}
AI_CORRECTION_ALLOWED_SAMPLE_WINDOWS = {"daily_intraday", "rolling_5d", "rolling_10d", "cumulative"}
AI_CORRECTION_ALLOWED_REVIEW_STATES = {
    "agree",
    "correction_proposed",
    "caution",
    "insufficient_context",
    "safety_concern",
    "unavailable",
}
AI_CORRECTION_FORBIDDEN_FIELDS = {
    "apply_now",
    "runtime_change",
    "runtime_mutation",
    "env_change",
    "code_change",
    "restart_required",
    "safety_revert_required",
}
AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT = 120_000
AI_CORRECTION_CONTEXT_SECTION_LIMITS = {
    "calibration_candidates": 36_000,
    "calibration_source_bundle": 16_000,
    "trade_lifecycle_attribution": 14_000,
    "threshold_cycle_cumulative": 42_000,
    "recent_anomaly_report": 10_000,
}
AI_CORRECTION_SOURCE_METRIC_TOP_N = 12
AI_CORRECTION_LIST_ITEM_LIMIT = 12
AI_CORRECTION_HASH_VOLATILE_KEYS = {"generated_at", "reused_at"}
CALIBRATION_FAMILY_METADATA = {
    "soft_stop_whipsaw_confirmation": {
        "priority": 1,
        "source_family": "soft_stop_whipsaw_confirmation",
        "target_env_keys": [
            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED",
            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC",
            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT",
            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT",
        ],
        "primary_key": "confirm_sec",
        "bounds": {
            "confirm_sec": {"min": 20, "max": 120, "max_step_per_day": 20},
            "buffer_pct": {"min": 0.05, "max": 0.50, "max_step_per_day": 0.05},
            "max_worsen_pct": {"min": 0.10, "max": 0.60, "max_step_per_day": 0.05},
        },
        "sample_floor": 10,
        "sample_window": "rolling_10d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "cumulative_since_2026-04-21"],
            "use": "soft-stop whipsaw는 당일 1건이 아니라 4월 이후 누적/rolling 지속성과 당일 safety guard를 함께 본다.",
            "daily_only_allowed": False,
        },
        "allowed_runtime_apply": True,
    },
    "market_regime_continuous_thresholds": {
        "priority": 8,
        "source_family": "market_regime_continuous_score",
        "target_env_keys": [
            "KORSTOCKSCAN_MARKET_REGIME_CONTINUOUS_ENABLED",
            "KORSTOCKSCAN_MARKET_REGIME_RISK_ON_MIN_SCORE",
            "KORSTOCKSCAN_MARKET_REGIME_NEUTRAL_MIN_SCORE",
            "KORSTOCKSCAN_MARKET_REGIME_OIL_RELIEF_MAX_WEIGHT",
            "KORSTOCKSCAN_MARKET_REGIME_BREADTH_MAX_WEIGHT",
        ],
        "primary_key": "risk_on_min_score",
        "bounds": {
            "risk_on_min_score": {"min": 60, "max": 75, "max_step_per_day": 5},
            "neutral_min_score": {"min": 35, "max": 55, "max_step_per_day": 5},
            "oil_relief_max_weight": {"min": 5, "max": 15, "max_step_per_day": 2.5},
            "breadth_max_weight": {"min": 25, "max": 45, "max_step_per_day": 5},
        },
        "sample_floor": 10,
        "sample_window": "rolling_10d_with_valid_market_cache_and_daily_report",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "rolling_5d"],
            "use": "market regime continuous score는 ADM/LDM risk_context 및 label별 EV 진단 입력이며 1차 개발에서는 runtime action을 바꾸지 않는다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["valid_market_regime_days"],
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "allowed_runtime_apply": False,
        "runtime_effect": False,
    },
    "holding_flow_ofi_smoothing": {
        "priority": 2,
        "source_family": "holding_flow_ofi_smoothing",
        "target_env_keys": [
            "OFI_AI_SMOOTHING_STALE_THRESHOLD_MS",
            "OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED",
            "HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT",
            "HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC",
            "HOLDING_FLOW_OVERRIDE_WORSEN_PCT",
        ],
        "primary_key": "max_defer_sec",
        "bounds": {
            "max_defer_sec": {"min": 30, "max": 120, "max_step_per_day": 15},
            "worsen_floor_pct": {"min": 0.40, "max": 1.20, "max_step_per_day": 0.10},
        },
        "sample_floor": 20,
        "sample_window": "daily_intraday",
        "window_policy": {
            "primary": "daily_intraday",
            "secondary": ["rolling_5d"],
            "use": "holding_flow defer cost는 장중 운영 상태가 빨리 변하므로 당일/장중 이상치로 calibration하고 rolling은 재발성 확인에만 쓴다.",
            "daily_only_allowed": True,
        },
        "allowed_runtime_apply": True,
    },
    "protect_trailing_smoothing": {
        "priority": 3,
        "source_family": "protect_trailing_smoothing",
        "target_env_keys": [
            "SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC",
            "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC",
            "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES",
            "SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO",
            "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT",
            "SCALP_PROTECT_TRAILING_EMERGENCY_PCT",
        ],
        "primary_key": "window_sec",
        "bounds": {
            "window_sec": {"min": 10, "max": 45, "max_step_per_day": 10},
            "below_ratio": {"min": 0.50, "max": 0.90, "max_step_per_day": 0.05},
            "buffer_pct": {"min": 0.50, "max": 1.50, "max_step_per_day": 0.10},
        },
        "sample_floor": 20,
        "sample_window": "rolling_10d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "rolling_20d"],
            "use": "protect trailing smoothing은 단일 tick/단일 종목 표본보다 반복 이탈 분포와 safety guard를 우선한다.",
            "daily_only_allowed": False,
        },
        "allowed_runtime_apply": True,
    },
    "trailing_continuation": {
        "priority": 4,
        "source_family": "scalp_trailing_take_profit",
        "target_env_keys": [
            "SCALP_TRAILING_WEAK_DRAW_DOWN_PCT",
            "SCALP_TRAILING_STRONG_DRAW_DOWN_PCT",
            "SCALP_TRAILING_STRONG_AI_SCORE",
        ],
        "primary_key": "weak_limit",
        "bounds": {
            "weak_limit": {"min": 0.40, "max": 0.80, "max_step_per_day": 0.05},
            "strong_limit": {"min": 0.80, "max": 1.50, "max_step_per_day": 0.05},
        },
        "sample_floor": 20,
        "sample_window": "rolling_10d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "rolling_20d"],
            "use": "trailing continuation은 GOOD_EXIT 훼손 리스크가 커서 당일 표본만으로 live apply하지 않는다.",
            "daily_only_allowed": False,
        },
        "allowed_runtime_apply": False,
    },
    "pre_submit_price_guard": {
        "priority": 9,
        "source_family": "pre_submit_price_guard",
        "target_env_keys": [
            "SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED",
            "SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS",
        ],
        "primary_key": "max_below_bid_bps",
        "bounds": {
            "max_below_bid_bps": {"min": 60, "max": 120, "max_step_per_day": 10},
        },
        "sample_floor": 20,
        "sample_window": "daily_intraday_with_rolling_confirmation",
        "window_policy": {
            "primary": "daily_intraday",
            "secondary": ["rolling_5d", "cumulative_since_2026-04-21"],
            "use": "후행 가격품질 guard를 관찰한다. latency submit drought/recovery 후보는 latency_classifier_runtime_profile가 소유한다.",
            "daily_only_allowed": True,
        },
        "allowed_runtime_apply": True,
    },
    "score65_74_recovery_probe": {
        "priority": 10,
        "source_family": "score65_74_recovery_probe",
        "target_env_keys": [
            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE",
            "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP",
            "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW",
            "AI_WAIT6579_PROBE_CANARY_MAX_QTY",
        ],
        "primary_key": "enabled",
        "bounds": {
            "min_buy_pressure": {"min": 55.0, "max": 75.0, "max_step_per_day": 5.0},
            "min_tick_accel": {"min": 0.8, "max": 1.5, "max_step_per_day": 0.1},
            "min_micro_vwap_bp": {"min": -10.0, "max": 20.0, "max_step_per_day": 5.0},
            "max_budget_krw": {"min": 10_000, "max": 50_000, "max_step_per_day": 10_000},
        },
        "sample_floor": 20,
        "sample_window": "rolling_5d_with_daily_trigger",
        "window_policy": {
            "primary": "rolling_5d",
            "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
            "use": "BUY drought/score65~74는 당일 병목을 trigger로 쓰되, 회수축 부활과 EV/close 우위는 rolling/cumulative 전용 표본으로 확인한다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["wait65_79_score65_74_candidate", "blocked_score65_74"],
        "allowed_runtime_apply": True,
    },
    "liquidity_gate_refined_candidate": {
        "priority": 11,
        "source_family": "liquidity_gate_refined_candidate",
        "target_env_keys": [],
        "primary_key": "enabled",
        "bounds": {},
        "sample_floor": 20,
        "sample_window": "rolling_5d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_5d",
            "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
            "use": "liquidity gate miss는 당일 단일 종목이 아니라 차단 후 5/10분 EV와 avoided-loser 비율을 같이 본 뒤 refined family 설계 후보로만 둔다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["blocked_events"],
        "allowed_runtime_apply": False,
    },
    "overbought_gate_refined_candidate": {
        "priority": 12,
        "source_family": "overbought_gate_refined_candidate",
        "target_env_keys": [],
        "primary_key": "enabled",
        "bounds": {},
        "sample_floor": 20,
        "sample_window": "rolling_5d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_5d",
            "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
            "use": "overbought gate miss는 naive hard block 완화가 아니라 과열 차단 후 missed-upside/avoided-loss trade-off를 닫는 family 설계 후보로만 둔다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["blocked_events"],
        "allowed_runtime_apply": False,
    },
    "strength_momentum_soft_gate_p1": {
        "priority": 13,
        "source_family": "strength_momentum_soft_gate_p1",
        "target_env_keys": [
            "SCALP_PRE_AI_SOFT_GATE_ENABLED",
            "SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED",
            "SCALP_PRE_AI_MAX_WS_AGE_SEC",
        ],
        "primary_key": "enabled",
        "bounds": {},
        "sample_floor": 20,
        "sample_window": "rolling_5d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_5d",
            "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
            "use": "strength/momentum hard block을 AI 전 폐기하지 않고 risk context로 넘기는 family 후보다. source-quality block은 별도 유지한다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["blocked_events"],
        "allowed_runtime_apply": False,
        "human_approval_required": True,
    },
    "overbought_pullback_guard_p1": {
        "priority": 14,
        "source_family": "overbought_pullback_guard_p1",
        "supersedes": ["overbought_gate_refined_candidate"],
        "target_env_keys": [
            "SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED",
            "SCALP_OVERBOUGHT_PULLBACK_MIN_DISTANCE_PCT",
            "SCALP_OVERBOUGHT_REBREAK_MIN_STRENGTH",
            "SCALP_OVERBOUGHT_REBREAK_MIN_BUY_PRESSURE",
        ],
        "primary_key": "enabled",
        "bounds": {},
        "sample_floor": 20,
        "sample_window": "rolling_5d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_5d",
            "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
            "use": "overbought 후보는 AI/counterfactual까지 열되 실주문 직전 pullback/rebreak guard로 chase risk를 차단한다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["blocked_events"],
        "allowed_runtime_apply": False,
        "human_approval_required": True,
    },
    "liquidity_pre_submit_guard_p1": {
        "priority": 15,
        "source_family": "liquidity_pre_submit_guard_p1",
        "supersedes": ["liquidity_gate_refined_candidate"],
        "target_env_keys": [
            "SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED",
            "MIN_SCALP_LIQUIDITY",
        ],
        "primary_key": "enabled",
        "bounds": {},
        "sample_floor": 20,
        "sample_window": "rolling_5d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_5d",
            "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
            "use": "liquidity는 AI/counterfactual 전단 폐기 대상이 아니라 broker submit 직전 hard safety guard다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["blocked_events"],
        "allowed_runtime_apply": False,
        "human_approval_required": True,
    },
    "bad_entry_refined_canary": {
        "priority": 20,
        "source_family": "bad_entry_refined_canary",
        "target_env_keys": [
            "SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED",
            "SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC",
            "SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT",
            "SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT",
            "SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT",
            "SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX",
        ],
        "primary_key": "enabled",
        "bounds": {
            "min_hold_sec": {"min": 60, "max": 300, "max_step_per_day": 30},
            "min_loss_pct": {"min": -1.50, "max": -0.50, "max_step_per_day": 0.10},
            "max_peak_profit_pct": {"min": 0.00, "max": 0.30, "max_step_per_day": 0.05},
            "recovery_prob_max": {"min": 0.15, "max": 0.45, "max_step_per_day": 0.05},
        },
        "sample_floor": 10,
        "sample_window": "rolling_10d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "cumulative_since_2026-04-21"],
            "use": "bad-entry refined는 loser classifier 과적합을 피하기 위해 누적/rolling tail과 당일 safety를 같이 본다.",
            "daily_only_allowed": False,
        },
        "allowed_runtime_apply": True,
    },
    "holding_exit_decision_matrix_advisory": {
        "priority": 30,
        "source_family": "holding_exit_decision_matrix_advisory",
        "target_env_keys": ["HOLDING_EXIT_MATRIX_ADVISORY_ENABLED"],
        "primary_key": "enabled",
        "bounds": {},
        "sample_floor": 1,
        "sample_window": "latest_report_with_rolling_bucket_context",
        "window_policy": {
            "primary": "latest_report",
            "secondary": ["rolling_bucket_context"],
            "use": "ADM/SAW advisory는 최신 matrix edge 존재 여부를 보되 bucket confidence는 rolling action weight를 참조한다.",
            "daily_only_allowed": False,
        },
        "allowed_runtime_apply": True,
    },
    "lifecycle_decision_matrix_runtime": {
        "priority": 31,
        "source_family": "lifecycle_decision_matrix_runtime",
        "target_env_keys": [
            "LIFECYCLE_DECISION_MATRIX_ENABLED",
            "LIFECYCLE_DECISION_MATRIX_POLICY_FILE",
            "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION",
            "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED",
            "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY",
            "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE",
            "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED",
            "LIFECYCLE_AI_CONTEXT_ENABLED",
            "LIFECYCLE_AI_CONTEXT_FILE",
            "LIFECYCLE_AI_CONTEXT_VERSION",
            "SCALP_ENTRY_ADM_ADVISORY_ENABLED",
            "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED",
            "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED",
            "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED",
            "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED",
        ],
        "primary_key": "enabled",
        "bounds": {
            "max_promotes_per_day": {"min": 1, "max": 3, "max_step_per_day": 1},
            "min_stage_confidence": {"min": 0.40, "max": 0.90, "max_step_per_day": 0.10},
        },
        "sample_floor": 20,
        "sample_window": "same_day_source_bundle_plus_rolling_threshold_cycle_consumer",
        "window_policy": {
            "primary": "latest_report",
            "secondary": ["rolling_5d", "cumulative_since_2026-04-21"],
            "use": "lifecycle matrix는 기존 fixed threshold를 hard_safety/baseline_prior/bounded_tunable/archive로 분류하고 stage별 weighted ADM action을 다음 장전 bounded micro canary로만 적용한다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["total_rows", "joined_rows"],
        "allowed_runtime_apply": True,
    },
    "scale_in_price_guard": {
        "priority": 40,
        "source_family": "scale_in_price_guard",
        "target_env_keys": [
            "SCALPING_SCALE_IN_MAX_SPREAD_BPS",
            "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS",
            "SCALPING_PYRAMID_MIN_AI_SCORE",
            "SCALPING_PYRAMID_MIN_BUY_PRESSURE",
            "SCALPING_PYRAMID_MIN_TICK_ACCEL",
            "SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP",
        ],
        "primary_key": "pyramid_max_micro_vwap_bps",
        "bounds": {
            "max_spread_bps": {"min": 40.0, "max": 100.0, "max_step_per_day": 5.0},
            "pyramid_max_micro_vwap_bps": {"min": 30.0, "max": 80.0, "max_step_per_day": 5.0},
            "pyramid_min_ai_score": {"min": 65, "max": 80, "max_step_per_day": 2},
            "pyramid_min_buy_pressure": {"min": 55.0, "max": 75.0, "max_step_per_day": 2.5},
            "pyramid_min_tick_accel": {"min": 0.3, "max": 1.0, "max_step_per_day": 0.1},
            "effective_qty_cap": {"min": 0, "max": 0, "max_step_per_day": 0},
        },
        "sample_floor": 20,
        "sample_window": "rolling_10d_or_cumulative_sparse",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["cumulative_since_2026-04-21", "daily"],
            "use": "scale-in은 체결 표본이 희소하므로 당일만으로 결론 내리지 않고 rolling/cumulative로 guard 값을 산정한다.",
            "daily_only_allowed": False,
        },
        "allowed_runtime_apply": False,
    },
    "position_sizing_cap_release": {
        "priority": 41,
        "source_family": "position_sizing_cap_release",
        "target_env_keys": [
            "SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED",
            "SCALPING_INITIAL_ENTRY_MAX_QTY",
            "AI_WAIT6579_PROBE_CANARY_MAX_QTY",
            "SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP",
        ],
        "primary_key": "initial_entry_qty_cap_enabled",
        "bounds": {},
        "sample_floor": 30,
        "sample_window": "rolling_10d_with_daily_guard",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "cumulative_since_2026-04-21"],
            "use": "1주 cap 해제는 완벽한 spot이 아니라 전체 EV가 충분하고 safety floor를 통과한 efficient trade-off 지점에서 사용자 승인 요청으로 승격한다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["normal_completed_valid"],
        "allowed_runtime_apply": False,
        "human_approval_required": True,
    },
    "position_sizing_dynamic_formula": {
        "priority": 42,
        "source_family": "position_sizing_dynamic_formula",
        "target_env_keys": [],
        "primary_key": "formula_version",
        "bounds": {},
        "sample_floor": 30,
        "sample_window": "rolling_10d_with_real_denominator",
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "cumulative_since_2026-04-21", "sim_probe_counterfactual_diagnostic"],
            "use": "동적수량 산식은 score/strategy/volatility/liquidity/spread/price band/recent loss/portfolio exposure 입력 품질과 real-only EV를 먼저 report-only로 검증한다.",
            "daily_only_allowed": False,
        },
        "sample_denominator_keys": ["real_completed_valid"],
        "allowed_runtime_apply": False,
        "human_approval_required": True,
    },
}


@dataclass
class ThresholdCycleContext:
    warnings: list[str]


@dataclass
class PipelineLoadResult:
    rows: list[dict]
    meta: dict[str, Any]


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        result = float(value)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, "", "-", "None"):
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(text[:19] if "%Y" in fmt else text[:8], fmt)
            return parsed
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _avg(values: list[float]) -> float | None:
    cleaned = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not cleaned:
        return None
    return sum(cleaned) / len(cleaned)


def _stddev(values: list[float]) -> float | None:
    cleaned = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(cleaned) < 2:
        return None
    mean = sum(cleaned) / len(cleaned)
    variance = sum((value - mean) ** 2 for value in cleaned) / (len(cleaned) - 1)
    return math.sqrt(max(variance, 0.0))


def _price_bucket(value: Any) -> str:
    price = _safe_float(value, None)
    if price is None or price <= 0:
        return "price_unknown"
    if price < 10_000:
        return "price_lt_10k"
    if price < 30_000:
        return "price_10k_30k"
    if price < 70_000:
        return "price_30k_70k"
    return "price_gte_70k"


def _volume_bucket(value: Any) -> str:
    volume = _safe_float(value, None)
    if volume is None or volume <= 0:
        return "volume_unknown"
    if volume < 500_000:
        return "volume_lt_500k"
    if volume < 2_000_000:
        return "volume_500k_2m"
    if volume < 10_000_000:
        return "volume_2m_10m"
    return "volume_gte_10m"


def _time_bucket(value: Any) -> str:
    dt_value = _parse_datetime(value)
    if dt_value is None:
        return "time_unknown"
    minute = dt_value.hour * 60 + dt_value.minute
    if minute < 9 * 60 or minute >= 15 * 60 + 30:
        return "time_outside_regular"
    if minute < 9 * 60 + 30:
        return "time_0900_0930"
    if minute < 10 * 60 + 30:
        return "time_0930_1030"
    if minute < 14 * 60:
        return "time_1030_1400"
    return "time_1400_1530"


def _percentile(values: list[float], pct: float, default: float = 0.0) -> float:
    cleaned = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    if not cleaned:
        return default
    if len(cleaned) == 1:
        return cleaned[0]
    rank = max(0, min(len(cleaned) - 1, math.ceil((pct / 100.0) * len(cleaned)) - 1))
    return cleaned[rank]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _date_range(target_date: str, days: int) -> list[str]:
    end = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = end - timedelta(days=max(0, days - 1))
    values: list[str] = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def _date_range_between(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start > end:
        return []
    values: list[str] = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def report_path_for_date(target_date: str) -> Path:
    return REPORT_DIR / f"threshold_cycle_{target_date}.json"


def save_threshold_cycle_report(report: dict) -> Path:
    target_date = str(report.get("date") or date.today().isoformat())
    path = report_path_for_date(target_date)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return path


def calibration_report_path_for_date(target_date: str, run_phase: str) -> Path:
    phase = str(run_phase or "postclose").strip() or "postclose"
    return THRESHOLD_CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_{phase}.json"


def threshold_ai_review_paths(target_date: str, run_phase: str) -> tuple[Path, Path]:
    phase = str(run_phase or "postclose").strip() or "postclose"
    return (
        THRESHOLD_AI_REVIEW_DIR / f"threshold_cycle_ai_review_{target_date}_{phase}.json",
        THRESHOLD_AI_REVIEW_DIR / f"threshold_cycle_ai_review_{target_date}_{phase}.md",
    )


def save_threshold_calibration_report(report: dict, *, run_phase: str | None = None) -> Path:
    target_date = str(report.get("date") or date.today().isoformat())
    phase = str(run_phase or (report.get("meta") or {}).get("calibration_run_phase") or "postclose")
    path = calibration_report_path_for_date(target_date, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": target_date,
        "run_phase": phase,
        "generated_at": (report.get("meta") or {}).get("generated_at"),
        "source_report": str(report_path_for_date(target_date)),
        "runtime_change": False,
        "calibration_source_bundle": report.get("calibration_source_bundle") or {},
        "trade_lifecycle_attribution": report.get("trade_lifecycle_attribution") or {},
        "completed_by_source": report.get("completed_by_source") or {},
        "scalp_simulator": report.get("scalp_simulator") or {},
        "calibration_candidates": report.get("calibration_candidates") or [],
        "window_policy_audit": report.get("window_policy_audit") or {},
        "post_apply_attribution": report.get("post_apply_attribution") or {},
        "safety_guard_pack": report.get("safety_guard_pack") or [],
        "calibration_trigger_pack": report.get("calibration_trigger_pack") or [],
        "warnings": report.get("warnings") or [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def statistical_action_report_paths(target_date: str) -> tuple[Path, Path]:
    return (
        STAT_ACTION_REPORT_DIR / f"statistical_action_weight_{target_date}.json",
        STAT_ACTION_REPORT_DIR / f"statistical_action_weight_{target_date}.md",
    )


def holding_exit_decision_matrix_paths(target_date: str) -> tuple[Path, Path]:
    return (
        AI_DECISION_MATRIX_DIR / f"holding_exit_decision_matrix_{target_date}.json",
        AI_DECISION_MATRIX_DIR / f"holding_exit_decision_matrix_{target_date}.md",
    )


def cumulative_threshold_report_paths(target_date: str) -> tuple[Path, Path]:
    return (
        CUMULATIVE_THRESHOLD_REPORT_DIR / f"threshold_cycle_cumulative_{target_date}.json",
        CUMULATIVE_THRESHOLD_REPORT_DIR / f"threshold_cycle_cumulative_{target_date}.md",
    )


def _import_sqlalchemy():
    from sqlalchemy import create_engine, text

    return create_engine, text


def _default_completed_rows_loader(start_date: str, end_date: str) -> list[dict]:
    create_engine, text = _import_sqlalchemy()
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    query = text(
        """
        SELECT
            rh.rec_date,
            rh.stock_code,
            rh.stock_name,
            rh.status,
            rh.strategy,
            rh.buy_price,
            rh.buy_qty,
            rh.buy_time,
            rh.sell_price,
            rh.sell_time,
            rh.profit_rate,
            rh.add_count,
            rh.avg_down_count,
            rh.pyramid_count,
            rh.last_add_type,
            dsq.volume AS daily_volume,
            dsq.marcap AS marcap
        FROM recommendation_history rh
        LEFT JOIN LATERAL (
            SELECT volume, marcap
            FROM daily_stock_quotes dsq
            WHERE dsq.stock_code = rh.stock_code
              AND dsq.quote_date <= rh.rec_date
            ORDER BY dsq.quote_date DESC
            LIMIT 1
        ) dsq ON true
        WHERE rh.rec_date >= :start_date
          AND rh.rec_date <= :end_date
          AND rh.status = 'COMPLETED'
          AND rh.profit_rate IS NOT NULL
        ORDER BY rh.rec_date DESC, rh.stock_code
        """
    )
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(query, {"start_date": start_date, "end_date": end_date}).mappings().all()]


def _read_threshold_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            if not is_threshold_cycle_stage(
                str(payload.get("stage") or ""),
                payload.get("fields") if isinstance(payload.get("fields"), dict) else None,
            ):
                continue
            rows.append(payload)
    return rows


def _read_jsonl_dicts(path: Path) -> list[dict]:
    rows: list[dict] = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _checkpoint_for_date(target_date: str) -> dict:
    path = THRESHOLD_CYCLE_DIR / "checkpoints" / f"{target_date}.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _partition_paths_for_date(target_date: str) -> list[Path]:
    root = THRESHOLD_CYCLE_DIR / f"date={target_date}"
    if not root.exists():
        return []
    return sorted(root.glob("family=*/part-*.jsonl"))


def _load_partitioned_pipeline_events(target_date: str) -> PipelineLoadResult | None:
    paths = _partition_paths_for_date(target_date)
    if not paths:
        return None
    rows: list[dict] = []
    read_bytes = 0
    for path in paths:
        try:
            read_bytes += path.stat().st_size
            rows.extend(_read_threshold_jsonl(path))
        except OSError:
            continue
    checkpoint = _checkpoint_for_date(target_date)
    return PipelineLoadResult(
        rows=rows,
        meta={
            "target_date": target_date,
            "data_source": "partitioned_compact",
            "partition_count": len(paths),
            "line_count": len(rows),
            "checkpoint_completed": bool(checkpoint.get("completed")) if checkpoint else None,
            "paused_reason": checkpoint.get("paused_reason") if checkpoint else None,
            "read_bytes_estimate": read_bytes,
            "warnings": [],
        },
    )


def _read_json_dict(path: Path) -> dict:
    if not path.exists() and Path(f"{path}.gz").exists():
        path = Path(f"{path}.gz")
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _existing_or_gzip_path(path: Path) -> Path:
    if path.exists():
        return path
    gz_path = Path(f"{path}.gz")
    if gz_path.exists():
        return gz_path
    return path


def _calibration_report_source_paths(target_date: str) -> dict[str, Path]:
    return {
        "buy_funnel_sentinel": REPORT_DIR / "buy_funnel_sentinel" / f"buy_funnel_sentinel_{target_date}.json",
        "wait6579_ev_cohort": REPORT_DIR / "monitor_snapshots" / f"wait6579_ev_cohort_{target_date}.json",
        "missed_entry_counterfactual": (
            REPORT_DIR / "monitor_snapshots" / f"missed_entry_counterfactual_{target_date}.json"
        ),
        "performance_tuning": REPORT_DIR / "monitor_snapshots" / f"performance_tuning_{target_date}.json",
        "holding_exit_observation": REPORT_DIR / "monitor_snapshots" / f"holding_exit_observation_{target_date}.json",
        "post_sell_feedback": REPORT_DIR / "monitor_snapshots" / f"post_sell_feedback_{target_date}.json",
        "trade_review": REPORT_DIR / "monitor_snapshots" / f"trade_review_{target_date}.json",
        "holding_exit_sentinel": REPORT_DIR / "holding_exit_sentinel" / f"holding_exit_sentinel_{target_date}.json",
        "panic_sell_defense": REPORT_DIR / "panic_sell_defense" / f"panic_sell_defense_{target_date}.json",
        "panic_buying": REPORT_DIR / "panic_buying" / f"panic_buying_{target_date}.json",
        "holding_exit_decision_matrix": (
            REPORT_DIR / "holding_exit_decision_matrix" / f"holding_exit_decision_matrix_{target_date}.json"
        ),
        "statistical_action_weight": (
            REPORT_DIR / "statistical_action_weight" / f"statistical_action_weight_{target_date}.json"
        ),
        "latency_classifier_recommendation": (
            REPORT_DIR / "latency_classifier_recommendation" / f"latency_classifier_recommendation_{target_date}.json"
        ),
        "market_regime_daily_report": REPORT_DIR / f"report_{target_date}.json",
    }


REPORT_ONLY_CLEANUP_AUDIT_REGISTRY: tuple[dict[str, str], ...] = (
    {
        "id": "sentinel_followup",
        "path_template": "sentinel_followup_{date}.md",
        "status_when_present": "archive_reference_cleanup_candidate",
        "current_owner": "archive_reference_only",
        "reason": "single follow-up artifact excluded from the current calibration source bundle",
        "recommended_action": "keep as dated archive/reference or move out of current report inventory",
    },
    {
        "id": "server_comparison",
        "path_template": "server_comparison/server_comparison_{date}.md",
        "status_when_present": "policy_disabled_reference",
        "current_owner": "remote_comparison_reference_only",
        "reason": "remote/server comparison is excluded from Plan Rebase decision inputs unless explicitly enabled",
        "recommended_action": "keep as policy-disabled reference; do not attach to threshold/source bundle",
    },
    {
        "id": "add_blocked_lock",
        "path_template": "monitor_snapshots/add_blocked_lock_{date}.json",
        "status_when_present": "dashboard_only_cleanup_candidate",
        "current_owner": "monitor_snapshot_reference_only",
        "reason": "add-blocked lock is not a current source-bundle owner unless a new avg-down/scale-in workorder reopens it",
        "recommended_action": "keep JSON snapshot for dashboard/archive or reopen via new workorder before using as source",
    },
    {
        "id": "preclose_sell_target",
        "path_template": "preclose_sell_target/preclose_sell_target_{date}.json",
        "status_when_present": "removed_feature_cleanup_candidate",
        "current_owner": "removed_legacy_feature",
        "reason": "preclose sell target was removed and must not re-enter tuning/calibration sources",
        "recommended_action": "delete stale generated artifact or move to archive if historical evidence is needed",
    },
)


def _audit_report_only_cleanup_candidates(target_date: str, source_paths: dict[str, Path]) -> dict:
    managed_source_names = sorted(source_paths)
    managed_source_paths = {path.resolve() for path in source_paths.values()}
    excluded_reports: list[dict] = []
    cleanup_candidates: list[dict] = []

    for item in REPORT_ONLY_CLEANUP_AUDIT_REGISTRY:
        rel_path = item["path_template"].replace("{date}", target_date)
        path = REPORT_DIR / rel_path
        path = _existing_or_gzip_path(path)
        exists = path.exists()
        in_current_source_bundle = path.resolve() in managed_source_paths
        status = "absent"
        if exists:
            status = item["status_when_present"]
        if in_current_source_bundle:
            status = "misconfigured_attached_to_current_source_bundle"

        entry = {
            "id": item["id"],
            "path": str(path),
            "exists": exists,
            "in_current_source_bundle": in_current_source_bundle,
            "status": status,
            "current_owner": item["current_owner"],
            "reason": item["reason"],
            "recommended_action": item["recommended_action"],
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
        }
        excluded_reports.append(entry)

        if exists and (
            status.endswith("_cleanup_candidate") or status == "misconfigured_attached_to_current_source_bundle"
        ):
            cleanup_candidates.append(entry)

    return {
        "schema_version": 1,
        "metric_role": "source_quality_gate",
        "decision_authority": "source_quality_only",
        "window_policy": "daily_intraday_or_postclose_audit",
        "sample_floor": 0,
        "primary_decision_metric": "cleanup_candidate_count",
        "source_quality_gate": "cleanup_candidate_count == 0",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit_or_cancel",
            "auto_buy_or_auto_sell",
            "bot_restart",
            "provider_route_change",
        ],
        "managed_source_names": managed_source_names,
        "excluded_reports": excluded_reports,
        "cleanup_candidate_count": len(cleanup_candidates),
        "cleanup_candidates": cleanup_candidates,
    }


def _recent_market_regime_daily_reports(target_date: str, days: int = 10) -> list[dict[str, Any]]:
    try:
        cutoff = datetime.strptime(target_date, "%Y-%m-%d").date()
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for path in sorted(REPORT_DIR.glob("report_*.json"), reverse=True):
        stem_date = path.stem.replace("report_", "", 1)
        try:
            report_date = datetime.strptime(stem_date, "%Y-%m-%d").date()
        except Exception:
            continue
        if report_date > cutoff:
            continue
        payload = _read_json_dict(path)
        if not payload:
            continue
        stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
        perf = payload.get("performance") if isinstance(payload.get("performance"), dict) else {}
        perf_summary = perf.get("summary") if isinstance(perf.get("summary"), dict) else {}
        score = _safe_float(stats.get("market_regime_continuous_score"), None)
        label = str(stats.get("market_regime_continuous_label") or "")
        rows.append(
            {
                "date": stem_date,
                "score": score,
                "label": label,
                "component_scores": stats.get("market_regime_component_scores")
                if isinstance(stats.get("market_regime_component_scores"), dict)
                else {},
                "source_quality": str(stats.get("market_regime_source_quality") or ""),
                "score_version": str(stats.get("market_regime_score_version") or ""),
                "swing_entry_recovery_gate_score": _safe_int(stats.get("swing_entry_recovery_gate_score"), 0) or 0,
                "allow_swing_entry": bool(stats.get("allow_swing_entry")),
                "completed_records": _safe_int(perf_summary.get("completed_records"), 0) or 0,
                "filled_records": _safe_int(perf_summary.get("filled_records"), 0) or 0,
                "total_records": _safe_int(perf_summary.get("total_records"), 0) or 0,
                "win_rate": _safe_float(perf_summary.get("win_rate"), None),
                "avg_profit_rate": _safe_float(perf_summary.get("avg_profit_rate"), None),
                "realized_pnl_krw": _safe_int(perf_summary.get("realized_pnl_krw"), 0) or 0,
            }
        )
        if len(rows) >= days:
            break
    return list(reversed(rows))


def _market_regime_window_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid_rows = [
        row
        for row in rows
        if row.get("score") is not None and str(row.get("label") or "") in {"RISK_ON", "NEUTRAL", "RISK_OFF"}
    ]
    scores = [float(row["score"]) for row in valid_rows]
    labels = Counter(str(row.get("label") or "UNKNOWN") for row in valid_rows)
    completed = sum(_safe_int(row.get("completed_records"), 0) or 0 for row in valid_rows)
    filled = sum(_safe_int(row.get("filled_records"), 0) or 0 for row in valid_rows)
    total = sum(_safe_int(row.get("total_records"), 0) or 0 for row in valid_rows)
    profit_values = [
        float(row["avg_profit_rate"])
        for row in valid_rows
        if row.get("avg_profit_rate") is not None and (_safe_int(row.get("completed_records"), 0) or 0) > 0
    ]
    return {
        "sample_days": len(rows),
        "valid_market_regime_days": len(valid_rows),
        "avg_score": round(_avg(scores) or 0.0, 4) if scores else None,
        "min_score": round(min(scores), 4) if scores else None,
        "max_score": round(max(scores), 4) if scores else None,
        "label_counts": dict(labels),
        "completed_records": completed,
        "win_rate_avg": round(_avg([float(row["win_rate"]) for row in valid_rows if row.get("win_rate") is not None]) or 0.0, 4)
        if valid_rows
        else None,
        "entry_participation_pct": round((filled / total * 100.0) if total else 0.0, 4),
        "source_quality_adjusted_ev_pct": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
        "severe_downside_count": sum(
            1
            for row in valid_rows
            if row.get("avg_profit_rate") is not None and float(row["avg_profit_rate"]) <= -2.0
        ),
        "market_regime_pass_opportunity": sum(1 for row in valid_rows if row.get("allow_swing_entry")),
        "market_regime_block_opportunity": sum(1 for row in valid_rows if not row.get("allow_swing_entry")),
    }


def _market_regime_label_ev_breakdown(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label = str(row.get("label") or "")
        if label in {"RISK_ON", "NEUTRAL", "RISK_OFF"} and row.get("score") is not None:
            grouped[label].append(row)

    breakdown: dict[str, Any] = {}
    for label, label_rows in sorted(grouped.items()):
        profit_values = [
            float(row["avg_profit_rate"])
            for row in label_rows
            if row.get("avg_profit_rate") is not None and (_safe_int(row.get("completed_records"), 0) or 0) > 0
        ]
        breakdown[label] = {
            "sample_days": len(label_rows),
            "completed_records": sum(_safe_int(row.get("completed_records"), 0) or 0 for row in label_rows),
            "source_quality_adjusted_ev_pct": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
            "win_rate_avg": round(_avg([float(row["win_rate"]) for row in label_rows if row.get("win_rate") is not None]) or 0.0, 4),
            "entry_participation_pct": _market_regime_window_summary(label_rows)["entry_participation_pct"],
            "severe_downside_count": sum(
                1
                for row in label_rows
                if row.get("avg_profit_rate") is not None and float(row["avg_profit_rate"]) <= -2.0
            ),
        }
    return breakdown


def _summarize_market_regime_continuous_sources(target_date: str) -> dict[str, Any]:
    rows = _recent_market_regime_daily_reports(target_date, days=10)
    latest = rows[-1] if rows else {}
    valid_days = [
        row
        for row in rows
        if row.get("score") is not None and str(row.get("label") or "") in {"RISK_ON", "NEUTRAL", "RISK_OFF"}
    ]
    latest_summary = {
        "date": latest.get("date"),
        "score": latest.get("score"),
        "label": latest.get("label"),
        "component_scores": latest.get("component_scores") or {},
        "source_quality": latest.get("source_quality"),
        "score_version": latest.get("score_version"),
        "swing_entry_recovery_gate_score": latest.get("swing_entry_recovery_gate_score", 0),
    } if latest else {}
    return {
        "schema_version": 1,
        "metric_role": "risk_context_feature",
        "decision_authority": "source_context_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "window_policy": {
            "primary": "rolling_10d",
            "secondary": ["daily", "rolling_5d"],
            "daily_only_allowed": False,
        },
        "sample_floor": 10,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "rolling_10d valid_market_regime_days >= 10 and daily report contains market_regime_continuous_score",
        "forbidden_uses": [
            "single-metric BUY/SELL/scale-in decision",
            "hard safety/broker/stale quote/price freshness guard bypass",
            "runtime env mutation before bounded apply approval",
            "bot restart or provider route change",
        ],
        "latest": latest_summary,
        "rolling_5d": _market_regime_window_summary(rows[-5:]),
        "rolling_10d": _market_regime_window_summary(rows),
        "label_ev_breakdown": _market_regime_label_ev_breakdown(rows),
        "source_quality": {
            "sample_days": len(rows),
            "valid_market_regime_days": len(valid_days),
            "status": "pass" if len(valid_days) >= 10 else "hold_sample",
            "missing_valid_market_regime_days": max(0, 10 - len(valid_days)),
        },
    }


def _holding_exit_report_source_paths(target_date: str) -> dict[str, Path]:
    paths = _calibration_report_source_paths(target_date)
    return {
        name: path
        for name, path in paths.items()
        if name
        in {
            "holding_exit_observation",
            "post_sell_feedback",
            "trade_review",
            "holding_exit_sentinel",
            "panic_sell_defense",
            "panic_buying",
            "holding_exit_decision_matrix",
            "statistical_action_weight",
        }
    }


def _summarize_calibration_report_sources(target_date: str) -> dict:
    sources: dict[str, dict] = {}
    warnings: list[str] = []
    source_paths = _calibration_report_source_paths(target_date)
    cleanup_audit = _audit_report_only_cleanup_candidates(target_date, source_paths)
    for candidate in cleanup_audit["cleanup_candidates"]:
        warnings.append(
            "report-only cleanup candidate: "
            f"{candidate['id']} status={candidate['status']} path={candidate['path']}"
        )
    for name, path in source_paths.items():
        actual_path = _existing_or_gzip_path(path)
        payload = _read_json_dict(path)
        exists = actual_path.exists()
        if exists and not payload and path.suffix == ".json":
            warnings.append(f"{name} 로드 실패 또는 빈 JSON: {actual_path}")
        sources[name] = {
            "path": str(actual_path),
            "exists": exists,
            "loaded": bool(payload),
            "top_keys": list(payload.keys())[:20] if payload else [],
        }

    buy_funnel_sentinel = _read_json_dict(source_paths["buy_funnel_sentinel"])
    wait6579_ev = _read_json_dict(source_paths["wait6579_ev_cohort"])
    missed_entry = _read_json_dict(source_paths["missed_entry_counterfactual"])
    performance_tuning = _read_json_dict(source_paths["performance_tuning"])
    holding_exit_observation = _read_json_dict(source_paths["holding_exit_observation"])
    post_sell_feedback = _read_json_dict(source_paths["post_sell_feedback"])
    trade_review = _read_json_dict(source_paths["trade_review"])
    holding_exit_sentinel = _read_json_dict(source_paths["holding_exit_sentinel"])
    panic_sell_defense = _read_json_dict(source_paths["panic_sell_defense"])
    panic_buying = _read_json_dict(source_paths["panic_buying"])
    decision_matrix = _read_json_dict(source_paths["holding_exit_decision_matrix"])
    stat_action = _read_json_dict(source_paths["statistical_action_weight"])
    latency_recommendation = _read_json_dict(source_paths["latency_classifier_recommendation"])
    market_regime_continuous = _summarize_market_regime_continuous_sources(target_date)

    buy_current = buy_funnel_sentinel.get("current") if isinstance(buy_funnel_sentinel, dict) else {}
    buy_current = buy_current if isinstance(buy_current, dict) else {}
    buy_session = buy_current.get("session") if isinstance(buy_current.get("session"), dict) else {}
    buy_stage_events = buy_session.get("stage_events") if isinstance(buy_session.get("stage_events"), dict) else {}
    buy_ratios = buy_session.get("ratios") if isinstance(buy_session.get("ratios"), dict) else {}
    buy_classification = buy_funnel_sentinel.get("classification") if isinstance(buy_funnel_sentinel, dict) else {}
    buy_classification = buy_classification if isinstance(buy_classification, dict) else {}
    wait_metrics = wait6579_ev.get("metrics") if isinstance(wait6579_ev.get("metrics"), dict) else {}
    wait_approval = wait6579_ev.get("approval_gate") if isinstance(wait6579_ev.get("approval_gate"), dict) else {}
    wait_rows = wait6579_ev.get("rows") if isinstance(wait6579_ev.get("rows"), list) else []
    score_rows = [
        row
        for row in wait_rows
        if 65 <= int(_safe_float((row or {}).get("ai_score"), 0.0) or 0.0) <= 74
    ]
    score_ev = [_safe_float(row.get("expected_ev_pct"), None) for row in score_rows if isinstance(row, dict)]
    score_close = [_safe_float(row.get("close_10m_pct"), None) for row in score_rows if isinstance(row, dict)]
    score_mfe = [_safe_float(row.get("mfe_10m_pct"), None) for row in score_rows if isinstance(row, dict)]
    score_ev = [value for value in score_ev if value is not None]
    score_close = [value for value in score_close if value is not None]
    score_mfe = [value for value in score_mfe if value is not None]
    missed_metrics = missed_entry.get("metrics") if isinstance(missed_entry.get("metrics"), dict) else {}
    perf_metrics = performance_tuning.get("metrics") if isinstance(performance_tuning.get("metrics"), dict) else {}
    perf_sections = performance_tuning.get("sections") if isinstance(performance_tuning.get("sections"), dict) else {}
    perf_latency_section = (
        perf_sections.get("latency_guard_miss_ev_recovery")
        if isinstance(perf_sections.get("latency_guard_miss_ev_recovery"), dict)
        else {}
    )
    latency_recommendation_candidate = (
        latency_recommendation.get("calibration_candidate")
        if isinstance(latency_recommendation.get("calibration_candidate"), dict)
        else {}
    )
    latency_recommendation_metrics = (
        latency_recommendation_candidate.get("source_metrics")
        if isinstance(latency_recommendation_candidate.get("source_metrics"), dict)
        else {}
    )
    soft_stop = holding_exit_observation.get("soft_stop_rebound") if isinstance(holding_exit_observation, dict) else {}
    soft_stop = soft_stop if isinstance(soft_stop, dict) else {}
    post_sell_soft = post_sell_feedback.get("soft_stop_forensics") if isinstance(post_sell_feedback, dict) else {}
    post_sell_soft = post_sell_soft if isinstance(post_sell_soft, dict) else {}
    trailing = holding_exit_observation.get("trailing_continuation") if isinstance(holding_exit_observation, dict) else {}
    trailing = trailing if isinstance(trailing, dict) else {}
    same_symbol = holding_exit_observation.get("same_symbol_reentry") if isinstance(holding_exit_observation, dict) else {}
    same_symbol = same_symbol if isinstance(same_symbol, dict) else {}
    current = holding_exit_sentinel.get("current") if isinstance(holding_exit_sentinel, dict) else {}
    current = current if isinstance(current, dict) else {}
    session = current.get("session") if isinstance(current.get("session"), dict) else {}
    stage_events = session.get("stage_events") if isinstance(session.get("stage_events"), dict) else {}
    classification = holding_exit_sentinel.get("classification") if isinstance(holding_exit_sentinel, dict) else {}
    classification = classification if isinstance(classification, dict) else {}
    panic_metrics = panic_sell_defense.get("panic_metrics") if isinstance(panic_sell_defense, dict) else {}
    panic_metrics = panic_metrics if isinstance(panic_metrics, dict) else {}
    panic_regime_contract = (
        panic_sell_defense.get("panic_regime_contract")
        if isinstance(panic_sell_defense.get("panic_regime_contract"), dict)
        else {}
    )
    recovery_metrics = panic_sell_defense.get("recovery_metrics") if isinstance(panic_sell_defense, dict) else {}
    recovery_metrics = recovery_metrics if isinstance(recovery_metrics, dict) else {}
    active_recovery = (
        recovery_metrics.get("active_sim_probe") if isinstance(recovery_metrics.get("active_sim_probe"), dict) else {}
    )
    post_sell_recovery = (
        recovery_metrics.get("post_sell_feedback") if isinstance(recovery_metrics.get("post_sell_feedback"), dict) else {}
    )
    microstructure_detector = (
        panic_sell_defense.get("microstructure_detector")
        if isinstance(panic_sell_defense.get("microstructure_detector"), dict)
        else {}
    )
    microstructure_market_context = (
        panic_sell_defense.get("microstructure_market_context")
        if isinstance(panic_sell_defense.get("microstructure_market_context"), dict)
        else {}
    )
    microstructure_metrics = (
        microstructure_detector.get("metrics")
        if isinstance(microstructure_detector.get("metrics"), dict)
        else {}
    )
    panic_candidates = (
        panic_sell_defense.get("canary_candidates")
        if isinstance(panic_sell_defense.get("canary_candidates"), list)
        else []
    )
    panic_candidate_status = {
        str(item.get("family")): item.get("status")
        for item in panic_candidates
        if isinstance(item, dict) and item.get("family")
    }
    micro_market_reasons = (
        microstructure_market_context.get("reasons")
        if isinstance(microstructure_market_context.get("reasons"), list)
        else []
    )
    micro_market_source_quality_blockers = [
        str(reason)
        for reason in micro_market_reasons
        if str(reason)
        in {
            "micro_risk_off_unconfirmed_by_market_or_breadth",
            "market_regime_not_risk_off",
            "market_regime_snapshot_missing_or_unknown",
        }
    ]
    micro_market_followup_candidate = bool(
        microstructure_market_context.get("portfolio_local_risk_off_only")
        or "micro_evaluated_symbol_count_below_breadth_floor" in {str(reason) for reason in micro_market_reasons}
        or "market_regime_snapshot_missing_or_unknown" in {str(reason) for reason in micro_market_reasons}
    )
    panic_buy_metrics = panic_buying.get("panic_buy_metrics") if isinstance(panic_buying, dict) else {}
    panic_buy_metrics = panic_buy_metrics if isinstance(panic_buy_metrics, dict) else {}
    panic_buy_exhaustion = panic_buying.get("exhaustion_metrics") if isinstance(panic_buying, dict) else {}
    panic_buy_exhaustion = panic_buy_exhaustion if isinstance(panic_buy_exhaustion, dict) else {}
    panic_buy_tp = panic_buying.get("tp_counterfactual_summary") if isinstance(panic_buying, dict) else {}
    panic_buy_tp = panic_buy_tp if isinstance(panic_buy_tp, dict) else {}
    panic_buy_micro = panic_buying.get("microstructure_detector") if isinstance(panic_buying, dict) else {}
    panic_buy_micro = panic_buy_micro if isinstance(panic_buy_micro, dict) else {}
    panic_buy_market = panic_buying.get("market_breadth_context") if isinstance(panic_buying, dict) else {}
    panic_buy_market = panic_buy_market if isinstance(panic_buy_market, dict) else {}
    panic_buy_candidates = (
        panic_buying.get("canary_candidates")
        if isinstance(panic_buying.get("canary_candidates"), list)
        else []
    )
    panic_buy_candidate_status = {
        str(item.get("family")): item.get("status")
        for item in panic_buy_candidates
        if isinstance(item, dict) and item.get("family")
    }
    panic_buy_source_quality_blockers: list[str] = []
    panic_buy_signal_count = _safe_int(panic_buy_micro.get("panic_buy_signal_count"), 0) or 0
    if panic_buy_signal_count > 0 and not bool(panic_buy_market.get("market_wide_panic_buy_confirmed")):
        panic_buy_source_quality_blockers.append("panic_buy_local_unconfirmed_by_market_breadth")
    if (_safe_int(panic_buy_micro.get("missing_orderbook_count"), 0) or 0) > 0:
        panic_buy_source_quality_blockers.append("panic_buy_orderbook_collector_coverage_gap")
    matrix_entries = decision_matrix.get("entries") if isinstance(decision_matrix.get("entries"), list) else []
    non_clear_matrix_entries = [
        entry
        for entry in matrix_entries
        if isinstance(entry, dict) and str(entry.get("recommended_bias") or "no_clear_edge") != "no_clear_edge"
    ]
    matrix_counterfactual = (
        decision_matrix.get("counterfactual_coverage_summary")
        if isinstance(decision_matrix.get("counterfactual_coverage_summary"), dict)
        else _summarize_matrix_counterfactual_coverage(matrix_entries)
    )
    saw_policy_counts = stat_action.get("policy_counts") if isinstance(stat_action.get("policy_counts"), dict) else {}
    stat_action_sample = stat_action.get("sample") if isinstance(stat_action.get("sample"), dict) else {}
    eligible_not_chosen = (
        stat_action.get("eligible_but_not_chosen")
        if isinstance(stat_action.get("eligible_but_not_chosen"), dict)
        else {}
    )
    counterfactual_proxy = _summarize_counterfactual_proxy_actions(eligible_not_chosen)
    blocker_outcomes = (
        missed_metrics.get("blocker_outcome_metrics")
        if isinstance(missed_metrics.get("blocker_outcome_metrics"), dict)
        else {}
    )
    latency_outcome = blocker_outcomes.get("latency_block") if isinstance(blocker_outcomes.get("latency_block"), dict) else {}
    ai_score_outcome = (
        blocker_outcomes.get("blocked_ai_score") if isinstance(blocker_outcomes.get("blocked_ai_score"), dict) else {}
    )
    liquidity_outcome = (
        blocker_outcomes.get("blocked_liquidity") if isinstance(blocker_outcomes.get("blocked_liquidity"), dict) else {}
    )
    overbought_outcome = (
        blocker_outcomes.get("blocked_overbought") if isinstance(blocker_outcomes.get("blocked_overbought"), dict) else {}
    )

    source_metrics = {
        "buy_score65_74": {
            "sentinel_primary": buy_classification.get("primary"),
            "sentinel_secondary": buy_classification.get("secondary")
            if isinstance(buy_classification.get("secondary"), list)
            else [],
            "wait6579_total_candidates": _safe_int(wait_metrics.get("total_candidates"), 0) or 0,
            "wait6579_entered_attempts": _safe_int(wait_metrics.get("entered_attempts"), 0) or 0,
            "wait6579_missed_attempts": _safe_int(wait_metrics.get("missed_attempts"), 0) or 0,
            "wait6579_avg_expected_ev_pct": _safe_float(wait_metrics.get("avg_expected_ev_pct"), None),
            "wait6579_avg_close_10m_pct": _safe_float(wait_metrics.get("avg_close_10m_pct"), None),
            "score65_74_candidates": len(score_rows),
            "score65_74_avg_expected_ev_pct": round(_avg(score_ev) or 0.0, 4) if score_ev else None,
            "score65_74_avg_close_10m_pct": round(_avg(score_close) or 0.0, 4) if score_close else None,
            "score65_74_avg_mfe_10m_pct": round(_avg(score_mfe) or 0.0, 4) if score_mfe else None,
            "full_samples": _safe_int(wait_approval.get("full_samples"), 0) or 0,
            "partial_samples": _safe_int(wait_approval.get("partial_samples"), 0) or 0,
            "threshold_relaxation_approved": bool(wait_approval.get("threshold_relaxation_approved")),
            "partial_sample_zero_is_calibration_target": (_safe_int(wait_approval.get("partial_samples"), 0) or 0) == 0,
            "budget_pass": _safe_int(buy_stage_events.get("budget_pass"), 0) or 0,
            "latency_pass": _safe_int(buy_stage_events.get("latency_pass"), 0) or 0,
            "order_bundle_submitted": _safe_int(buy_stage_events.get("order_bundle_submitted"), 0) or 0,
            "position_rebased_after_fill": _safe_int(buy_stage_events.get("position_rebased_after_fill"), 0) or 0,
            "submitted_to_budget_unique_pct": _safe_float(buy_ratios.get("submitted_to_budget_unique_pct"), None),
            "submitted_to_ai_unique_pct": _safe_float(buy_ratios.get("submitted_to_ai_unique_pct"), None),
            "panic_state": panic_sell_defense.get("panic_state") if isinstance(panic_sell_defense, dict) else None,
            "panic_regime_mode": panic_sell_defense.get("panic_regime_mode")
            if isinstance(panic_sell_defense, dict)
            else None,
            "panic_detected": bool(panic_metrics.get("panic_detected")),
            "panic_by_stop_loss_count": bool(panic_metrics.get("panic_by_stop_loss_count")),
            "panic_stop_loss_exit_count": _safe_int(panic_metrics.get("stop_loss_exit_count"), 0) or 0,
            "missed_winner_rate": _safe_float(missed_metrics.get("missed_winner_rate"), None),
            "avoided_loser_rate": _safe_float(missed_metrics.get("avoided_loser_rate"), None),
            "blocked_ai_score_evaluated": _safe_int(ai_score_outcome.get("evaluated_candidates"), 0) or 0,
            "blocked_ai_score_missed_winner_rate": _safe_float(ai_score_outcome.get("missed_winner_rate"), None),
            "blocked_ai_score_avoided_loser_rate": _safe_float(ai_score_outcome.get("avoided_loser_rate"), None),
            "blocked_ai_score_avg_close_10m_pct": _safe_float(ai_score_outcome.get("avg_close_10m_pct"), None),
            "performance_blocked_ai_score_events": _safe_int(perf_metrics.get("entry_blocked_ai_score_events"), 0) or 0,
            "gatekeeper_eval_ms_p95": _safe_float(perf_metrics.get("gatekeeper_eval_ms_p95"), None),
        },
        "market_regime_continuous": market_regime_continuous,
        "latency_guard_miss_ev_recovery": {
            "instrumentation_status": perf_latency_section.get("instrumentation_status") or "missing_contract",
            "instrumentation_contract_version": _safe_int(
                perf_latency_section.get("instrumentation_contract_version"),
                0,
            )
            or 0,
            "provenance_contract": (
                perf_latency_section.get("provenance_contract")
                if isinstance(perf_latency_section.get("provenance_contract"), list)
                else []
            ),
            "coverage_status": perf_latency_section.get("coverage_status"),
            "coverage_gap_type": perf_latency_section.get("coverage_gap_type"),
            "counterfactual_join_gap_count": _safe_int(
                perf_latency_section.get("counterfactual_join_gap_count"),
                0,
            )
            or 0,
            "missing_contract_fields": (
                perf_latency_section.get("missing_contract_fields")
                if isinstance(perf_latency_section.get("missing_contract_fields"), list)
                else []
            ),
            "evaluated_candidates": _safe_int(latency_outcome.get("evaluated_candidates"), 0) or 0,
            "missed_winner_count": _safe_int(latency_outcome.get("missed_winner_count"), 0) or 0,
            "avoided_loser_count": _safe_int(latency_outcome.get("avoided_loser_count"), 0) or 0,
            "missed_winner_rate": _safe_float(latency_outcome.get("missed_winner_rate"), None),
            "avoided_loser_rate": _safe_float(latency_outcome.get("avoided_loser_rate"), None),
            "avg_close_10m_pct": _safe_float(latency_outcome.get("avg_close_10m_pct"), None),
            "avg_mfe_10m_pct": _safe_float(latency_outcome.get("avg_mfe_10m_pct"), None),
            "avg_mae_10m_pct": _safe_float(latency_outcome.get("avg_mae_10m_pct"), None),
            "performance_latency_block_events": _safe_int(perf_metrics.get("latency_block_events"), 0) or 0,
            "performance_latency_pass_events": _safe_int(perf_metrics.get("latency_pass_events"), 0) or 0,
            "quote_fresh_latency_pass_rate": _safe_float(perf_metrics.get("quote_fresh_latency_pass_rate"), None),
            "gatekeeper_eval_ms_p95": _safe_float(perf_metrics.get("gatekeeper_eval_ms_p95"), None),
            "attribution_ready": bool(
                (_safe_int(latency_outcome.get("evaluated_candidates"), 0) or 0) > 0
                and _safe_float(latency_outcome.get("avg_close_10m_pct"), None) is not None
            ),
            "attribution_gap": bool(
                (_safe_int(perf_metrics.get("latency_block_events"), 0) or 0)
                > (_safe_int(latency_outcome.get("evaluated_candidates"), 0) or 0)
            ),
            "events_without_counterfactual": max(
                0,
                (_safe_int(perf_metrics.get("latency_block_events"), 0) or 0)
                - (_safe_int(latency_outcome.get("evaluated_candidates"), 0) or 0),
            ),
            "next_action": (
                "backfill_latency_block_counterfactual_join"
                if (_safe_int(perf_metrics.get("latency_block_events"), 0) or 0)
                > (_safe_int(latency_outcome.get("evaluated_candidates"), 0) or 0)
                else "use_latency_block_ev_for_refined_guard_review"
            ),
            "latency_classifier_recommendation_status": "loaded" if latency_recommendation else "missing",
            "latency_classifier_selected_profile_id": latency_recommendation.get("selected_profile_id"),
            "latency_classifier_runtime_semantics": latency_recommendation_metrics.get("profile_runtime_semantics"),
            "latency_classifier_profile_generation": (
                latency_recommendation.get("profile_generation") if isinstance(latency_recommendation, dict) else {}
            ),
            "latency_classifier_counterfactual_source": (
                latency_recommendation.get("counterfactual_source") if isinstance(latency_recommendation, dict) else {}
            ),
            "recommended_action": latency_recommendation_metrics.get("recommended_action"),
            "recommended_action_reason": latency_recommendation_metrics.get("recommended_action_reason"),
            "would_safe_pass_events": _safe_int(
                latency_recommendation_metrics.get("would_safe_pass_events"),
                0,
            )
            or 0,
            "would_caution_reject_events": _safe_int(
                latency_recommendation_metrics.get("would_caution_reject_events"),
                0,
            )
            or 0,
            "would_recovery_canary_events": _safe_int(
                latency_recommendation_metrics.get("would_recovery_canary_events"),
                0,
            )
            or 0,
            "would_recovery_canary_attempts": _safe_int(
                latency_recommendation_metrics.get("would_recovery_canary_attempts"),
                0,
            )
            or 0,
            "hard_reject_events": _safe_int(latency_recommendation_metrics.get("hard_reject_events"), 0) or 0,
            "stale_quote_override_events": _safe_int(
                latency_recommendation_metrics.get("stale_quote_override_events"),
                0,
            )
            or 0,
            "broker_guard_bypass_candidates": _safe_int(
                latency_recommendation_metrics.get("broker_guard_bypass_candidates"),
                0,
            )
            or 0,
            "fallback_deprecated_excluded_from_pass_events": _safe_int(
                latency_recommendation_metrics.get("fallback_deprecated_excluded_from_pass_events"),
                0,
            )
            or 0,
            "counterfactual_joined_sample": _safe_int(
                latency_recommendation_metrics.get("counterfactual_joined_sample"),
                0,
            )
            or 0,
            "counterfactual_join_rate_pct": _safe_float(
                latency_recommendation_metrics.get("counterfactual_join_rate_pct"),
                None,
            ),
            "counterfactual_ev_pct": _safe_float(
                latency_recommendation_metrics.get("counterfactual_ev_pct"),
                None,
            ),
            "missed_winner_recovered": _safe_int(
                latency_recommendation_metrics.get("missed_winner_recovered"),
                0,
            )
            or 0,
            "avoided_loser_lost": _safe_int(
                latency_recommendation_metrics.get("avoided_loser_lost"),
                0,
            )
            or 0,
            "latency_submit_routing": (
                "latency_submit_recovery_candidate"
                if str(latency_recommendation_metrics.get("recommended_action") or "") == "bounded_apply"
                else "latency_submit_recovery_hold"
                if (_safe_int(latency_recommendation_metrics.get("would_recovery_canary_events"), 0) or 0) > 0
                else "latency_classifier_runtime_semantics_gap"
            ),
        },
        "liquidity_gate_refined_candidate": {
            "evaluated_candidates": _safe_int(liquidity_outcome.get("evaluated_candidates"), 0) or 0,
            "missed_winner_count": _safe_int(liquidity_outcome.get("missed_winner_count"), 0) or 0,
            "avoided_loser_count": _safe_int(liquidity_outcome.get("avoided_loser_count"), 0) or 0,
            "missed_winner_rate": _safe_float(liquidity_outcome.get("missed_winner_rate"), None),
            "avoided_loser_rate": _safe_float(liquidity_outcome.get("avoided_loser_rate"), None),
            "avg_close_10m_pct": _safe_float(liquidity_outcome.get("avg_close_10m_pct"), None),
            "avg_mfe_10m_pct": _safe_float(liquidity_outcome.get("avg_mfe_10m_pct"), None),
            "avg_mae_10m_pct": _safe_float(liquidity_outcome.get("avg_mae_10m_pct"), None),
            "performance_blocked_liquidity_events": _safe_int(perf_metrics.get("entry_blocked_liquidity_events"), 0) or 0,
            "allowed_runtime_apply": False,
            "target_metric": "missed_upside 감소와 avoided_loser 보존의 trade-off",
        },
        "overbought_gate_refined_candidate": {
            "evaluated_candidates": _safe_int(overbought_outcome.get("evaluated_candidates"), 0) or 0,
            "missed_winner_count": _safe_int(overbought_outcome.get("missed_winner_count"), 0) or 0,
            "avoided_loser_count": _safe_int(overbought_outcome.get("avoided_loser_count"), 0) or 0,
            "missed_winner_rate": _safe_float(overbought_outcome.get("missed_winner_rate"), None),
            "avoided_loser_rate": _safe_float(overbought_outcome.get("avoided_loser_rate"), None),
            "avg_close_10m_pct": _safe_float(overbought_outcome.get("avg_close_10m_pct"), None),
            "avg_mfe_10m_pct": _safe_float(overbought_outcome.get("avg_mfe_10m_pct"), None),
            "avg_mae_10m_pct": _safe_float(overbought_outcome.get("avg_mae_10m_pct"), None),
            "performance_blocked_overbought_events": _safe_int(perf_metrics.get("entry_blocked_overbought_events"), 0) or 0,
            "allowed_runtime_apply": False,
            "target_metric": "과열 차단 후 missed_upside/avoided_loss trade-off",
        },
        "soft_stop": {
            "holding_exit_observation_total": _safe_int(soft_stop.get("total_soft_stop"), 0) or 0,
            "holding_exit_observation_rebound_above_sell_10m_rate": _safe_float(
                soft_stop.get("rebound_above_sell_10m_rate"), None
            ),
            "holding_exit_observation_rebound_above_buy_10m_rate": _safe_float(
                soft_stop.get("rebound_above_buy_10m_rate"), None
            ),
            "holding_exit_observation_whipsaw_signal": bool(soft_stop.get("whipsaw_signal")),
            "cooldown_would_block_rate": _safe_float(soft_stop.get("cooldown_would_block_rate"), None),
            "post_sell_soft_stop_total": _safe_int(post_sell_soft.get("total_soft_stop"), 0) or 0,
            "post_sell_rebound_above_sell_10m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_sell_rate") or {}).get("10m")
                if isinstance(post_sell_soft.get("rebound_above_sell_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_buy_10m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_buy_rate") or {}).get("10m")
                if isinstance(post_sell_soft.get("rebound_above_buy_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_sell_20m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_sell_rate") or {}).get("20m")
                if isinstance(post_sell_soft.get("rebound_above_sell_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_buy_20m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_buy_rate") or {}).get("20m")
                if isinstance(post_sell_soft.get("rebound_above_buy_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_sell_30m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_sell_rate") or {}).get("30m")
                if isinstance(post_sell_soft.get("rebound_above_sell_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_buy_30m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_buy_rate") or {}).get("30m")
                if isinstance(post_sell_soft.get("rebound_above_buy_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_sell_60m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_sell_rate") or {}).get("60m")
                if isinstance(post_sell_soft.get("rebound_above_sell_rate"), dict)
                else None,
                None,
            ),
            "post_sell_rebound_above_buy_60m_rate": _safe_float(
                (post_sell_soft.get("rebound_above_buy_rate") or {}).get("60m")
                if isinstance(post_sell_soft.get("rebound_above_buy_rate"), dict)
                else None,
                None,
            ),
        },
        "holding_flow": {
            "sentinel_primary": classification.get("primary"),
            "sentinel_secondary": classification.get("secondary") if isinstance(classification.get("secondary"), list) else [],
            "holding_flow_override_defer_exit": _safe_int(stage_events.get("holding_flow_override_defer_exit"), 0) or 0,
            "holding_flow_override_force_exit": _safe_int(stage_events.get("holding_flow_override_force_exit"), 0) or 0,
            "holding_flow_override_exit_confirmed": _safe_int(
                stage_events.get("holding_flow_override_exit_confirmed"), 0
            )
            or 0,
            "holding_flow_ofi_smoothing_applied": _safe_int(
                stage_events.get("holding_flow_ofi_smoothing_applied"), 0
            )
            or 0,
            "max_defer_worsen_pct": _safe_float(session.get("max_defer_worsen_pct"), None),
        },
        "trailing": {
            "evaluated_trailing": _safe_int(trailing.get("evaluated_trailing"), 0) or 0,
            "qualifying_cohort_count": _safe_int(trailing.get("qualifying_cohort_count"), 0) or 0,
            "missed_upside_rate": _safe_float(trailing.get("missed_upside_rate"), None),
            "good_exit_rate": _safe_float(trailing.get("good_exit_rate"), None),
            "eligible_for_live_review": bool(trailing.get("eligible_for_live_review")),
        },
        "safety": {
            "same_symbol_reentry_loss_count": _safe_int(same_symbol.get("after_soft_stop_next_loss_count"), 0) or 0,
            "sell_order_sent": _safe_int(stage_events.get("sell_order_sent"), 0) or 0,
            "sell_completed": _safe_int(stage_events.get("sell_completed"), 0) or 0,
            "trade_review_completed_valid": _safe_int((trade_review.get("metrics") or {}).get("completed_valid"), 0)
            if isinstance(trade_review.get("metrics"), dict)
            else 0,
        },
        "panic_sell_defense": {
            "panic_state": panic_sell_defense.get("panic_state") if isinstance(panic_sell_defense, dict) else None,
            "panic_regime_mode": panic_sell_defense.get("panic_regime_mode")
            if isinstance(panic_sell_defense, dict)
            else None,
            "panic_regime_decision_authority": panic_regime_contract.get("decision_authority"),
            "panic_regime_runtime_effect": panic_regime_contract.get("runtime_effect"),
            "panic_regime_allowed_actions": [
                str(item) for item in panic_regime_contract.get("allowed_actions", []) if str(item)
            ]
            if isinstance(panic_regime_contract.get("allowed_actions"), list)
            else [],
            "panic_regime_forbidden_uses": [
                str(item) for item in panic_regime_contract.get("forbidden_uses", []) if str(item)
            ]
            if isinstance(panic_regime_contract.get("forbidden_uses"), list)
            else [],
            "runtime_effect": (
                (panic_sell_defense.get("policy") or {}).get("runtime_effect")
                if isinstance(panic_sell_defense.get("policy"), dict)
                else None
            ),
            "real_exit_count": _safe_int(panic_metrics.get("real_exit_count"), 0) or 0,
            "non_real_exit_count": _safe_int(panic_metrics.get("non_real_exit_count"), 0) or 0,
            "stop_loss_exit_count": _safe_int(panic_metrics.get("stop_loss_exit_count"), 0) or 0,
            "max_rolling_30m_stop_loss_exit_count": _safe_int(
                panic_metrics.get("max_rolling_30m_stop_loss_exit_count"), 0
            )
            or 0,
            "stop_loss_exit_ratio_pct": _safe_float(panic_metrics.get("stop_loss_exit_ratio_pct"), None),
            "avg_exit_profit_rate_pct": _safe_float(panic_metrics.get("avg_exit_profit_rate_pct"), None),
            "confirmation_eligible_exit_count": _safe_int(
                panic_metrics.get("confirmation_eligible_exit_count"), 0
            )
            or 0,
            "never_delay_exit_count": _safe_int(panic_metrics.get("never_delay_exit_count"), 0) or 0,
            "active_sim_probe_positions": _safe_int(active_recovery.get("active_positions"), 0) or 0,
            "active_sim_probe_avg_unrealized_profit_rate_pct": _safe_float(
                active_recovery.get("avg_unrealized_profit_rate_pct"), None
            ),
            "active_sim_probe_win_rate_pct": _safe_float(active_recovery.get("win_rate_pct"), None),
            "active_sim_probe_provenance_passed": bool(
                ((active_recovery.get("provenance_check") or {}).get("passed"))
                if isinstance(active_recovery.get("provenance_check"), dict)
                else False
            ),
            "post_sell_rebound_above_sell_10_20m_pct": _safe_float(
                post_sell_recovery.get("rebound_above_sell_10_20m_pct"), None
            ),
            "post_sell_rebound_above_buy_10_20m_pct": _safe_float(
                post_sell_recovery.get("rebound_above_buy_10_20m_pct"), None
            ),
            "microstructure_evaluated_symbol_count": _safe_int(
                microstructure_detector.get("evaluated_symbol_count"), 0
            )
            or 0,
            "microstructure_risk_off_advisory_count": _safe_int(
                microstructure_detector.get("risk_off_advisory_count"), 0
            )
            or 0,
            "microstructure_allow_new_long_false_count": _safe_int(
                microstructure_detector.get("allow_new_long_false_count"), 0
            )
            or 0,
            "microstructure_missing_orderbook_count": _safe_int(
                microstructure_detector.get("missing_orderbook_count"), 0
            )
            or 0,
            "microstructure_degraded_orderbook_count": _safe_int(
                microstructure_detector.get("degraded_orderbook_count"), 0
            )
            or 0,
            "microstructure_max_panic_score": _safe_float(microstructure_metrics.get("max_panic_score"), None),
            "microstructure_max_recovery_score": _safe_float(microstructure_metrics.get("max_recovery_score"), None),
            "microstructure_market_risk_state": microstructure_market_context.get("market_risk_state"),
            "microstructure_market_confirms_risk_off": bool(
                microstructure_market_context.get("market_confirms_risk_off")
            ),
            "microstructure_breadth_confirms_risk_off": bool(
                microstructure_market_context.get("breadth_confirms_risk_off")
            ),
            "microstructure_confirmed_risk_off_advisory": bool(
                microstructure_market_context.get("confirmed_risk_off_advisory")
            ),
            "microstructure_portfolio_local_risk_off_only": bool(
                microstructure_market_context.get("portfolio_local_risk_off_only")
            ),
            "microstructure_risk_off_advisory_ratio_pct": _safe_float(
                microstructure_market_context.get("risk_off_advisory_ratio_pct"), None
            ),
            "microstructure_breadth_symbol_floor": _safe_int(
                microstructure_market_context.get("breadth_symbol_floor"), 0
            )
            or 0,
            "microstructure_source_quality_reasons": [str(reason) for reason in micro_market_reasons],
            "source_quality_blockers": micro_market_source_quality_blockers,
            "market_breadth_followup_candidate": micro_market_followup_candidate,
            "market_breadth_next_action": (
                "review_index_breadth_before_panic_runtime_candidate"
                if micro_market_followup_candidate
                else "none"
            ),
            "candidate_status": panic_candidate_status,
            "allowed_runtime_apply": False,
        },
        "panic_buying": {
            "panic_buy_state": panic_buying.get("panic_buy_state") if isinstance(panic_buying, dict) else None,
            "panic_buy_regime_mode": (
                panic_buying.get("panic_buy_regime_mode") if isinstance(panic_buying, dict) else None
            ),
            "panic_buy_regime_decision_authority": (
                (panic_buying.get("panic_buy_regime_contract") or {}).get("decision_authority")
                if isinstance(panic_buying.get("panic_buy_regime_contract"), dict)
                else None
            ),
            "panic_buy_regime_runtime_effect": (
                (panic_buying.get("panic_buy_regime_contract") or {}).get("runtime_effect")
                if isinstance(panic_buying.get("panic_buy_regime_contract"), dict)
                else None
            ),
            "panic_buy_regime_allowed_actions": (
                (panic_buying.get("panic_buy_regime_contract") or {}).get("allowed_actions")
                if isinstance(panic_buying.get("panic_buy_regime_contract"), dict)
                else []
            ),
            "panic_buy_regime_forbidden_uses": (
                (panic_buying.get("panic_buy_regime_contract") or {}).get("forbidden_uses")
                if isinstance(panic_buying.get("panic_buy_regime_contract"), dict)
                else []
            ),
            "runtime_effect": (
                (panic_buying.get("policy") or {}).get("runtime_effect")
                if isinstance(panic_buying.get("policy"), dict)
                else None
            ),
            "panic_buy_active_count": _safe_int(panic_buy_metrics.get("panic_buy_active_count"), 0) or 0,
            "panic_buy_watch_count": _safe_int(panic_buy_metrics.get("panic_buy_watch_count"), 0) or 0,
            "exhaustion_candidate_count": _safe_int(panic_buy_exhaustion.get("exhaustion_candidate_count"), 0) or 0,
            "exhaustion_confirmed_count": _safe_int(panic_buy_exhaustion.get("exhaustion_confirmed_count"), 0) or 0,
            "max_panic_buy_score": _safe_float(panic_buy_metrics.get("max_panic_buy_score"), None),
            "max_exhaustion_score": _safe_float(panic_buy_exhaustion.get("max_exhaustion_score"), None),
            "avg_confidence": _safe_float(panic_buy_metrics.get("avg_confidence"), None),
            "tp_counterfactual_count": _safe_int(panic_buy_tp.get("candidate_context_count"), 0) or 0,
            "tp_like_exit_count": _safe_int(panic_buy_tp.get("tp_like_exit_count"), 0) or 0,
            "trailing_winner_count": _safe_int(panic_buy_tp.get("trailing_winner_count"), 0) or 0,
            "market_breadth_source_quality_status": panic_buy_market.get("market_panic_breadth_source_quality_status"),
            "market_breadth_risk_on_advisory": bool(panic_buy_market.get("market_panic_breadth_risk_on_advisory")),
            "market_breadth_risk_off_advisory": bool(panic_buy_market.get("market_panic_breadth_risk_off_advisory")),
            "market_wide_panic_buy_confirmed": bool(panic_buy_market.get("market_wide_panic_buy_confirmed")),
            "missing_orderbook_count": _safe_int(panic_buy_micro.get("missing_orderbook_count"), 0) or 0,
            "missing_trade_aggressor_count": _safe_int(panic_buy_micro.get("missing_trade_aggressor_count"), 0) or 0,
            "carried_orderbook_snapshot_count": _safe_int(panic_buy_micro.get("carried_orderbook_snapshot_count"), 0) or 0,
            "carried_trade_aggressor_snapshot_count": _safe_int(
                panic_buy_micro.get("carried_trade_aggressor_snapshot_count"), 0
            )
            or 0,
            "source_quality_blockers": panic_buy_source_quality_blockers,
            "candidate_status": panic_buy_candidate_status,
            "allowed_runtime_apply": False,
        },
        "decision_support": {
            "matrix_version": decision_matrix.get("matrix_version"),
            "instrumentation_status": (
                "implemented"
                if isinstance(decision_matrix.get("counterfactual_coverage_summary"), dict)
                and isinstance(decision_matrix.get("counterfactual_proxy_summary"), dict)
                else "missing_contract"
            ),
            "instrumentation_contract_version": _safe_int(
                decision_matrix.get("instrumentation_contract_version"),
                0,
            )
            or 0,
            "provenance_contract": (
                decision_matrix.get("provenance_contract")
                if isinstance(decision_matrix.get("provenance_contract"), list)
                else []
            ),
            "matrix_entries": len(matrix_entries),
            "matrix_non_clear_edge": len(non_clear_matrix_entries),
            "matrix_no_clear_edge": sum(
                1
                for entry in matrix_entries
                if isinstance(entry, dict) and str(entry.get("recommended_bias") or "") == "no_clear_edge"
            ),
            "saw_weight_source_ready": bool(stat_action.get("weight_source_ready")),
            "saw_candidate_weight_source": _safe_int(saw_policy_counts.get("candidate_weight_source"), 0) or 0,
            "saw_defensive_only_high_loss_rate": _safe_int(
                saw_policy_counts.get("defensive_only_high_loss_rate"), 0
            )
            or 0,
            "saw_insufficient_sample": _safe_int(saw_policy_counts.get("insufficient_sample"), 0) or 0,
            "counterfactual_entry_count": _safe_int(matrix_counterfactual.get("entry_count"), 0) or 0,
            "counterfactual_ready_count": _safe_int(matrix_counterfactual.get("ready_count"), 0) or 0,
            "counterfactual_gap_count": _safe_int(matrix_counterfactual.get("gap_count"), 0) or 0,
            "counterfactual_ready_rate": _safe_float(matrix_counterfactual.get("ready_rate"), None),
            "counterfactual_per_action_samples": (
                matrix_counterfactual.get("per_action_samples")
                if isinstance(matrix_counterfactual.get("per_action_samples"), dict)
                else {}
            ),
            "eligible_but_not_chosen_status": counterfactual_proxy.get("status"),
            "eligible_but_not_chosen_sample_snapshots": counterfactual_proxy.get("sample_snapshots"),
            "eligible_but_not_chosen_sample_candidates": counterfactual_proxy.get("sample_candidates"),
            "eligible_but_not_chosen_post_sell_joined_candidates": counterfactual_proxy.get(
                "post_sell_joined_candidates"
            ),
            "counterfactual_proxy_ready": bool(counterfactual_proxy.get("ready")),
            "counterfactual_proxy_actions_present": counterfactual_proxy.get("actions_present") or [],
            "counterfactual_proxy_missing_actions": counterfactual_proxy.get("missing_actions") or [],
            "counterfactual_proxy_per_action_samples": counterfactual_proxy.get("per_action_samples") or {},
            "counterfactual_proxy_per_action_joined": counterfactual_proxy.get("per_action_joined") or {},
            "excluded_reports": {},
        },
        "scale_in_price_guard": {
            "scale_in_price_resolved": _safe_int(stage_events.get("scale_in_price_resolved"), 0) or 0,
            "scale_in_price_guard_block": _safe_int(stage_events.get("scale_in_price_guard_block"), 0) or 0,
            "scale_in_price_p2_observe": _safe_int(stage_events.get("scale_in_price_p2_observe"), 0) or 0,
            "compact_scale_in_executed": _safe_int(stat_action_sample.get("compact_scale_in_executed"), 0)
            or 0,
            "avg_down_wait": _safe_int(stat_action_sample.get("avg_down_wait"), 0) or 0,
            "pyramid_wait": _safe_int(stat_action_sample.get("pyramid_wait"), 0) or 0,
            "saw_weight_source_ready": bool(stat_action.get("weight_source_ready")),
            "saw_candidate_weight_source": _safe_int(saw_policy_counts.get("candidate_weight_source"), 0) or 0,
        },
        "bad_entry": {
            "refined_candidate": _safe_int(stage_events.get("bad_entry_refined_candidate"), 0)
            or _safe_int(buy_stage_events.get("bad_entry_refined_candidate"), 0)
            or 0,
            "bad_entry_block_observed": _safe_int(stage_events.get("bad_entry_block_observed"), 0)
            or _safe_int(buy_stage_events.get("bad_entry_block_observed"), 0)
            or 0,
            "soft_stop_tail_sample": _safe_int(soft_stop.get("total_soft_stop"), 0) or 0,
            "soft_stop_rebound_above_sell_10m_rate": _safe_float(
                soft_stop.get("rebound_above_sell_10m_rate"), None
            ),
            "holding_flow_override_defer_exit": _safe_int(stage_events.get("holding_flow_override_defer_exit"), 0)
            or 0,
            "sell_order_sent": _safe_int(stage_events.get("sell_order_sent"), 0) or 0,
            "sell_completed": _safe_int(stage_events.get("sell_completed"), 0) or 0,
        },
    }
    return {
        "schema_version": 1,
        "target_date": target_date,
        "purpose": "efficient_tradeoff_threshold_calibration_source",
        "sources": sources,
        "source_metrics": source_metrics,
        "report_only_cleanup_audit": cleanup_audit,
        "warnings": warnings,
        "new_observation_axis_created": False,
    }


def _summarize_holding_exit_report_sources(target_date: str) -> dict:
    return _summarize_calibration_report_sources(target_date)


def _is_count_like_metric_key(key: str) -> bool:
    text = str(key or "").lower()
    return (
        text.endswith("_count")
        or text.endswith("_counts")
        or text.endswith("_events")
        or text.endswith("_candidates")
        or text.endswith("_attempts")
        or text.endswith("_samples")
        or text.endswith("_records")
        or text in {
            "matrix_entries",
            "matrix_non_clear_edge",
            "matrix_no_clear_edge",
            "evaluated_candidates",
            "performance_blocked_liquidity_events",
            "performance_blocked_overbought_events",
            "performance_latency_block_events",
            "performance_latency_pass_events",
            "scale_in_price_resolved",
            "scale_in_price_guard_block",
            "scale_in_price_p2_observe",
            "compact_scale_in_executed",
            "avg_down_wait",
            "pyramid_wait",
        }
    )


def _is_average_like_metric_key(key: str) -> bool:
    text = str(key or "").lower()
    return (
        text.endswith("_rate")
        or text.endswith("_pct")
        or text.startswith("avg_")
        or text.endswith("_avg")
        or text.endswith("_p95")
        or text.endswith("_p90")
    )


def _aggregate_numeric_metric(key: str, values: list[Any], parents: list[dict]) -> Any:
    numeric = [_safe_float(value, None) for value in values]
    numeric = [value for value in numeric if value is not None]
    if not numeric:
        return None
    if _is_count_like_metric_key(key):
        return int(round(sum(numeric)))
    if _is_average_like_metric_key(key):
        weighted_pairs: list[tuple[float, float]] = []
        for value, parent in zip(values, parents):
            number = _safe_float(value, None)
            if number is None or not isinstance(parent, dict):
                continue
            denominator = (
                _safe_float(parent.get("evaluated_candidates"), None)
                or _safe_float(parent.get("sample_count"), None)
                or _safe_float(parent.get("source_sample_count"), None)
            )
            if denominator is not None and denominator > 0:
                weighted_pairs.append((number, denominator))
        if weighted_pairs:
            total_weight = sum(weight for _, weight in weighted_pairs)
            if total_weight > 0:
                return round(sum(value * weight for value, weight in weighted_pairs) / total_weight, 4)
        return round(sum(numeric) / len(numeric), 4)
    return numeric[-1]


def _aggregate_metric_dicts(dicts: list[dict]) -> dict:
    result: dict[str, Any] = {}
    keys = sorted({key for item in dicts if isinstance(item, dict) for key in item})
    for key in keys:
        values = [item.get(key) for item in dicts if isinstance(item, dict) and key in item]
        if not values:
            continue
        dict_values = [value for value in values if isinstance(value, dict)]
        if dict_values and len(dict_values) == len(values):
            result[key] = _aggregate_metric_dicts(dict_values)
            continue
        list_values = [value for value in values if isinstance(value, list)]
        if list_values and len(list_values) == len(values):
            merged: list[Any] = []
            for value in list_values:
                merged.extend(value)
            result[key] = merged
            continue
        bool_values = [value for value in values if isinstance(value, bool)]
        if bool_values and len(bool_values) == len(values):
            result[key] = any(bool_values)
            continue
        numeric_values = [value for value in values if _safe_float(value, None) is not None]
        if numeric_values and len(numeric_values) == len(values):
            result[key] = _aggregate_numeric_metric(key, values, dicts)
            continue
        text_values = [str(value) for value in values if value not in (None, "", "-", "None")]
        if text_values:
            result[key] = text_values[-1]
    return result


def _aggregate_calibration_source_contexts(contexts: list[dict], *, target_date: str, window_label: str) -> dict:
    contexts = [context for context in contexts if isinstance(context, dict)]
    metrics_by_name: dict[str, list[dict]] = defaultdict(list)
    source_exists: dict[str, int] = Counter()
    warnings: list[str] = []
    for context in contexts:
        metrics = context.get("source_metrics") if isinstance(context.get("source_metrics"), dict) else {}
        for name, payload in metrics.items():
            if isinstance(payload, dict):
                metrics_by_name[str(name)].append(payload)
        sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
        for name, source in sources.items():
            if isinstance(source, dict) and source.get("exists"):
                source_exists[str(name)] += 1
        for warning in context.get("warnings") or []:
            warnings.append(str(warning))
    return {
        "schema_version": 1,
        "target_date": target_date,
        "window": window_label,
        "purpose": "rolling_calibration_source_bundle",
        "sources": {
            name: {"exists_count": count, "window_date_count": len(contexts)}
            for name, count in sorted(source_exists.items())
        },
        "source_metrics": {
            name: _aggregate_metric_dicts(payloads)
            for name, payloads in sorted(metrics_by_name.items())
        },
        "warnings": warnings,
        "new_observation_axis_created": False,
    }


def _default_pipeline_load_result(target_date: str) -> PipelineLoadResult:
    partitioned = _load_partitioned_pipeline_events(target_date)
    if partitioned is not None:
        return partitioned

    compact_path = THRESHOLD_CYCLE_DIR / f"threshold_events_{target_date}.jsonl"
    if not compact_path.exists() and Path(f"{compact_path}.gz").exists():
        compact_path = Path(f"{compact_path}.gz")
    if compact_path.exists():
        rows = _read_threshold_jsonl(compact_path)
        return PipelineLoadResult(
            rows=rows,
            meta={
                "target_date": target_date,
                "data_source": "legacy_compact",
                "partition_count": 0,
                "line_count": len(rows),
                "checkpoint_completed": None,
                "paused_reason": None,
                "read_bytes_estimate": compact_path.stat().st_size,
                "warnings": [],
            },
        )

    jsonl_path = _existing_or_gzip_path(DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl")
    if jsonl_path.exists() and jsonl_path.stat().st_size <= RAW_PIPELINE_FALLBACK_MAX_BYTES:
        rows: list[dict] = []
        for payload in _read_threshold_jsonl(jsonl_path):
            if not isinstance(payload, dict):
                continue
            if not is_threshold_cycle_stage(
                str(payload.get("stage") or ""),
                payload.get("fields") if isinstance(payload.get("fields"), dict) else None,
            ):
                continue
            if payload.get("event_type") not in (None, "", "pipeline_event"):
                continue
            rows.append(payload)
        return PipelineLoadResult(
            rows=rows,
            meta={
                "target_date": target_date,
                "data_source": "small_raw_fallback",
                "partition_count": 0,
                "line_count": len(rows),
                "checkpoint_completed": None,
                "paused_reason": None,
                "read_bytes_estimate": jsonl_path.stat().st_size,
                "warnings": ["raw fallback used; compact partition missing"],
            },
        )
    warnings = []
    if jsonl_path.exists():
        warnings.append(f"raw fallback skipped: file exceeds {RAW_PIPELINE_FALLBACK_MAX_BYTES} bytes")
    return PipelineLoadResult(
        rows=[],
        meta={
            "target_date": target_date,
            "data_source": "none",
            "partition_count": 0,
            "line_count": 0,
            "checkpoint_completed": None,
            "paused_reason": None,
            "read_bytes_estimate": 0,
            "warnings": warnings,
        },
    )


def _default_pipeline_loader(target_date: str) -> list[dict]:
    return _default_pipeline_load_result(target_date).rows


def _extract_field_values(events: list[dict], stage: str, field_name: str) -> list[float]:
    values: list[float] = []
    for event in events:
        if str(event.get("stage") or "") != stage:
            continue
        fields = event.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        value = _safe_float(fields.get(field_name), None)
        if value is not None:
            values.append(value)
    return values


def _stage_count(events: list[dict], stage: str) -> int:
    return sum(1 for event in events if str(event.get("stage") or "") == stage)


def _events_for_stage(events: list[dict], stage: str) -> list[dict]:
    return [event for event in events if str(event.get("stage") or "") == stage]


def _event_fields(event: dict) -> dict:
    fields = event.get("fields") or {}
    return fields if isinstance(fields, dict) else {}


def _field_counter(events: list[dict], field_name: str, *, default: str = "-") -> dict:
    counter = Counter(str(_event_fields(event).get(field_name) or default) for event in events)
    return dict(counter.most_common(10))


def _record_ids(events: list[dict]) -> set[Any]:
    return {event.get("record_id") for event in events if event.get("record_id") not in (None, "", "-")}


def _record_id_stage_count(events: list[dict], stage: str, record_ids: set[Any]) -> int:
    if not record_ids:
        return 0
    return sum(1 for event in events if str(event.get("stage") or "") == stage and event.get("record_id") in record_ids)


def _record_id_stage_field_counter(events: list[dict], stage: str, record_ids: set[Any], field_name: str) -> dict:
    if not record_ids:
        return {}
    counter = Counter(
        str(_event_fields(event).get(field_name) or "-")
        for event in events
        if str(event.get("stage") or "") == stage and event.get("record_id") in record_ids
    )
    return dict(counter.most_common(10))


def _parse_action_list(value: Any) -> list[str]:
    if value in (None, "", "-", "None"):
        return []
    if isinstance(value, (list, tuple, set)):
        raw_tokens = [str(item) for item in value]
    else:
        raw_tokens = str(value).replace(",", "|").split("|")
    actions: list[str] = []
    seen: set[str] = set()
    for raw_token in raw_tokens:
        token = str(raw_token or "").strip()
        if not token or token in {"-", "None"}:
            continue
        action = token.split(":", 1)[0].strip()
        if not action or action in seen:
            continue
        seen.add(action)
        actions.append(action)
    return actions


def _parse_rejected_action_reasons(value: Any) -> dict[str, str]:
    if value in (None, "", "-", "None"):
        return {}
    if isinstance(value, (list, tuple, set)):
        raw_tokens = [str(item) for item in value]
    else:
        raw_tokens = str(value).replace(",", "|").split("|")
    reasons: dict[str, str] = {}
    for raw_token in raw_tokens:
        token = str(raw_token or "").strip()
        if not token or token in {"-", "None"}:
            continue
        action, sep, reason = token.partition(":")
        action = action.strip()
        if action:
            reasons[action] = reason.strip() if sep else "-"
    return reasons


def _load_post_sell_evaluation_by_record_id(target_date: str | None) -> dict[str, dict]:
    if not target_date:
        return {}
    path = _existing_or_gzip_path(POST_SELL_DIR / f"post_sell_evaluations_{target_date}.jsonl")
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    for payload in _read_jsonl_dicts(path):
        if not isinstance(payload, dict):
            continue
        record_id = payload.get("recommendation_id") or payload.get("record_id")
        if record_id in (None, "", "-"):
            continue
        rows[str(record_id)] = payload
    return rows


def _load_post_sell_candidate_by_record_id(target_date: str | None) -> dict[str, dict]:
    if not target_date:
        return {}
    path = _existing_or_gzip_path(POST_SELL_DIR / f"post_sell_candidates_{target_date}.jsonl")
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    for payload in _read_jsonl_dicts(path):
        if not isinstance(payload, dict):
            continue
        record_id = payload.get("recommendation_id") or payload.get("record_id")
        if record_id in (None, "", "-"):
            continue
        rows[str(record_id)] = payload
    return rows


def _load_sim_post_sell_evaluation_by_sim_id(target_date: str | None) -> dict[str, dict]:
    if not target_date:
        return {}
    path = _existing_or_gzip_path(POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl")
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    for payload in _read_jsonl_dicts(path):
        if not isinstance(payload, dict):
            continue
        for key in (
            payload.get("sim_record_id"),
            payload.get("sim_parent_record_id"),
            payload.get("post_sell_id"),
        ):
            if key in (None, "", "-"):
                continue
            rows[str(key)] = payload
    return rows


def _post_sell_metric(row: dict | None, horizon: str, key: str) -> float | None:
    if not isinstance(row, dict):
        return None
    metrics = row.get(f"metrics_{horizon}") or {}
    if not isinstance(metrics, dict):
        return None
    return _safe_float(metrics.get(key), None)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _last_stage_event(events: list[dict], stage: str) -> dict | None:
    for event in reversed(events):
        if str(event.get("stage") or "") == stage:
            return event
    return None


def _first_stage_event(events: list[dict], stage: str) -> dict | None:
    for event in events:
        if str(event.get("stage") or "") == stage:
            return event
    return None


def _classify_lifecycle_type(
    *,
    stages: Counter,
    exit_rule: str,
    exit_decision_source: str,
    post_sell_outcome: str,
) -> str:
    if stages.get("entry_order_cancel_confirmed", 0) and not stages.get("sell_completed", 0):
        return "entry_unfilled_cancelled"
    if stages.get("order_bundle_submitted", 0) and not stages.get("sell_completed", 0):
        return "entry_submitted_unresolved"
    if not stages.get("sell_completed", 0):
        return "pre_entry_or_holding_unresolved"
    if post_sell_outcome == "PENDING_POST_SELL":
        return "closed_pending_post_sell_outcome"

    rule = str(exit_rule or "-")
    if rule in {"scalp_soft_stop_pct", "scalp_soft_stop_whipsaw_confirmation"}:
        return "soft_stop_good_exit" if post_sell_outcome == "GOOD_EXIT" else "soft_stop_missed_upside" if post_sell_outcome == "MISSED_UPSIDE" else "soft_stop_neutral"
    if rule in {"scalp_trailing_take_profit", "protect_trailing_stop"}:
        return "trailing_good_exit" if post_sell_outcome == "GOOD_EXIT" else "trailing_early_exit" if post_sell_outcome == "MISSED_UPSIDE" else "trailing_neutral"
    if rule in {"scalp_hard_stop_pct", "protect_hard_stop", "scalp_emergency_stop"}:
        return "hard_stop_good_exit" if post_sell_outcome == "GOOD_EXIT" else "hard_stop_missed_upside" if post_sell_outcome == "MISSED_UPSIDE" else "hard_stop_neutral"
    if rule == "scalp_bad_entry_refined_canary":
        return "bad_entry_refined_good_exit" if post_sell_outcome == "GOOD_EXIT" else "bad_entry_refined_missed_upside" if post_sell_outcome == "MISSED_UPSIDE" else "bad_entry_refined_neutral"
    if str(exit_decision_source or "") == "HOLDING_FLOW_OVERRIDE":
        return "holding_flow_good_exit" if post_sell_outcome == "GOOD_EXIT" else "holding_flow_missed_upside" if post_sell_outcome == "MISSED_UPSIDE" else "holding_flow_neutral"
    return "closed_other_good_exit" if post_sell_outcome == "GOOD_EXIT" else "closed_other_missed_upside" if post_sell_outcome == "MISSED_UPSIDE" else "closed_other_neutral"


def _build_trade_lifecycle_attribution(events: list[dict], target_date: str | None) -> dict:
    material_stages = {
        "order_bundle_submitted",
        "entry_order_cancel_requested",
        "entry_order_cancel_confirmed",
        "entry_order_cancel_failed",
        "position_rebased_after_fill",
        "bad_entry_refined_candidate",
        "bad_entry_refined_exit",
        "soft_stop_micro_grace",
        "soft_stop_whipsaw_confirmation",
        "holding_flow_override_review",
        "holding_flow_override_exit_confirmed",
        "holding_flow_override_defer_exit",
        "holding_flow_ofi_smoothing_applied",
        "scale_in_price_resolved",
        "scale_in_price_guard_block",
        "scale_in_executed",
        "stat_action_decision_snapshot",
        "exit_signal",
        "sell_order_sent",
        "sell_completed",
    }
    grouped: dict[str, list[dict]] = {}
    for event in events:
        record_id = event.get("record_id")
        if record_id in (None, "", "-"):
            continue
        if str(event.get("stage") or "") not in material_stages:
            continue
        grouped.setdefault(str(record_id), []).append(event)

    post_sell_candidates = _load_post_sell_candidate_by_record_id(target_date)
    post_sell_evaluations = _load_post_sell_evaluation_by_record_id(target_date)
    type_counts: Counter = Counter()
    phase_counts: Counter = Counter()
    exit_rule_outcomes: Counter = Counter()
    decision_source_outcomes: Counter = Counter()
    entry_lifecycle_outcomes: Counter = Counter()
    bad_entry_signal_types: Counter = Counter()
    scale_in_outcomes: Counter = Counter()
    examples: list[dict] = []

    for record_id, record_events in sorted(grouped.items()):
        record_events = sorted(record_events, key=lambda item: str(item.get("emitted_at") or ""))
        stages = Counter(str(event.get("stage") or "-") for event in record_events)
        exit_event = _last_stage_event(record_events, "exit_signal")
        sell_completed = _last_stage_event(record_events, "sell_completed")
        order_event = _first_stage_event(record_events, "order_bundle_submitted")
        post_sell = post_sell_evaluations.get(record_id)
        post_sell_candidate = post_sell_candidates.get(record_id)

        exit_fields = _event_fields(exit_event or {})
        sell_fields = _event_fields(sell_completed or {})
        order_fields = _event_fields(order_event or {})
        exit_rule = str(
            exit_fields.get("exit_rule")
            or sell_fields.get("exit_rule")
            or (post_sell or {}).get("exit_rule")
            or "-"
        )
        exit_decision_source = str(
            exit_fields.get("exit_decision_source")
            or sell_fields.get("exit_decision_source")
            or (post_sell_candidate or {}).get("exit_decision_source")
            or "-"
        )
        post_sell_outcome = str((post_sell or {}).get("outcome") or "PENDING_POST_SELL")
        entry_lifecycle = str(order_fields.get("entry_order_lifecycle") or "-")
        primary_type = _classify_lifecycle_type(
            stages=stages,
            exit_rule=exit_rule,
            exit_decision_source=exit_decision_source,
            post_sell_outcome=post_sell_outcome,
        )
        if stages.get("sell_completed") and post_sell:
            phase_state = "closed_post_sell_joined"
        elif stages.get("sell_completed"):
            phase_state = "closed_pending_post_sell"
        elif stages.get("entry_order_cancel_confirmed"):
            phase_state = "entry_cancelled_no_position"
        elif stages.get("order_bundle_submitted"):
            phase_state = "submitted_unresolved"
        else:
            phase_state = "pre_entry_or_holding_unresolved"

        bad_candidates = [event for event in record_events if str(event.get("stage") or "") == "bad_entry_refined_candidate"]
        bad_signal_type = "-"
        if bad_candidates:
            exclusion_reasons = {
                str(_event_fields(event).get("exclusion_reason") or "-")
                for event in bad_candidates
            }
            would_exit = any(
                _truthy(_event_fields(event).get("would_exit"))
                or _truthy(_event_fields(event).get("should_exit"))
                for event in bad_candidates
            )
            if post_sell_outcome == "PENDING_POST_SELL":
                bad_signal_type = "pending_post_sell_outcome"
            elif post_sell_outcome == "MISSED_UPSIDE":
                bad_signal_type = "false_positive_risk_after_candidate"
            elif stages.get("bad_entry_refined_exit"):
                bad_signal_type = "refined_exit_finalized"
            elif "soft_stop_zone" in exclusion_reasons:
                bad_signal_type = "late_detected_soft_stop_zone"
            elif would_exit:
                bad_signal_type = "preventable_bad_entry_candidate"
            else:
                bad_signal_type = "candidate_signal_only"
            bad_entry_signal_types[bad_signal_type] += 1

        if stages.get("scale_in_price_resolved") or stages.get("scale_in_price_guard_block") or stages.get("scale_in_executed"):
            scale_in_outcomes[f"{post_sell_outcome}|{primary_type}"] += 1

        type_counts[primary_type] += 1
        phase_counts[phase_state] += 1
        exit_rule_outcomes[f"{exit_rule}|{post_sell_outcome}"] += 1
        decision_source_outcomes[f"{exit_decision_source}|{post_sell_outcome}"] += 1
        entry_lifecycle_outcomes[f"{entry_lifecycle}|{post_sell_outcome}"] += 1

        if len(examples) < 30:
            examples.append(
                {
                    "record_id": record_id,
                    "stock_code": (exit_event or sell_completed or order_event or {}).get("stock_code"),
                    "stock_name": (exit_event or sell_completed or order_event or {}).get("stock_name"),
                    "phase_state": phase_state,
                    "primary_type": primary_type,
                    "entry_lifecycle": entry_lifecycle,
                    "entry_price_guard": order_fields.get("entry_price_guard"),
                    "exit_rule": exit_rule,
                    "exit_decision_source": exit_decision_source,
                    "post_sell_candidate_registered": bool(post_sell_candidate),
                    "post_sell_joined": bool(post_sell),
                    "post_sell_outcome": post_sell_outcome,
                    "profit_rate": _safe_float((post_sell or {}).get("profit_rate") or sell_fields.get("profit_rate"), None),
                    "mfe_10m_pct": _post_sell_metric(post_sell, "10m", "mfe_pct"),
                    "mae_10m_pct": _post_sell_metric(post_sell, "10m", "mae_pct"),
                    "bad_entry_signal_type": bad_signal_type,
                    "stages": dict(stages),
                }
            )

    return {
        "schema_version": 1,
        "status": "postclose_finalized_for_joined_records",
        "runtime_change": False,
        "join_key": "record_id",
        "records": len(grouped),
        "phase_counts": dict(phase_counts),
        "primary_type_counts": dict(type_counts),
        "family_views": {
            "entry_price": {
                "entry_lifecycle_outcomes": dict(entry_lifecycle_outcomes),
                "entry_unfilled_cancelled": _safe_int(type_counts.get("entry_unfilled_cancelled"), 0) or 0,
                "submitted_unresolved": _safe_int(phase_counts.get("submitted_unresolved"), 0) or 0,
            },
            "soft_stop": {
                "good_exit": _safe_int(type_counts.get("soft_stop_good_exit"), 0) or 0,
                "missed_upside": _safe_int(type_counts.get("soft_stop_missed_upside"), 0) or 0,
                "neutral": _safe_int(type_counts.get("soft_stop_neutral"), 0) or 0,
                "pending_post_sell": sum(
                    count
                    for key, count in exit_rule_outcomes.items()
                    if key
                    in {
                        "scalp_soft_stop_pct|PENDING_POST_SELL",
                        "scalp_soft_stop_whipsaw_confirmation|PENDING_POST_SELL",
                    }
                ),
            },
            "trailing": {
                "good_exit": _safe_int(type_counts.get("trailing_good_exit"), 0) or 0,
                "early_exit": _safe_int(type_counts.get("trailing_early_exit"), 0) or 0,
                "neutral": _safe_int(type_counts.get("trailing_neutral"), 0) or 0,
            },
            "holding_flow": {
                "decision_source_outcomes": {
                    key: value
                    for key, value in decision_source_outcomes.items()
                    if key.startswith("HOLDING_FLOW_OVERRIDE|")
                }
            },
            "bad_entry_refined": {
                "signal_type_counts": dict(bad_entry_signal_types),
                "provisional_only": _safe_int(bad_entry_signal_types.get("pending_post_sell_outcome"), 0) or 0,
                "false_positive_risk": _safe_int(bad_entry_signal_types.get("false_positive_risk_after_candidate"), 0) or 0,
                "late_detected_soft_stop_zone": _safe_int(bad_entry_signal_types.get("late_detected_soft_stop_zone"), 0) or 0,
                "preventable_candidate": _safe_int(bad_entry_signal_types.get("preventable_bad_entry_candidate"), 0) or 0,
            },
            "scale_in": {
                "outcomes": dict(scale_in_outcomes),
            },
        },
        "exit_rule_outcomes": dict(exit_rule_outcomes),
        "decision_source_outcomes": dict(decision_source_outcomes),
        "examples": examples,
        "quality_notes": [
            "런타임 후보 stage는 provisional signal이며 최종 유형은 장후 post-sell outcome join 후 닫는다.",
            "각 family는 이 공통 lifecycle view를 참조하고, 단일 종목 질의 시점의 부분 로그만으로 최종 라벨을 확정하지 않는다.",
            "post-sell 미조인 record는 pending으로 남겨 다음 장후 snapshot refresh 또는 evaluator 재실행 대상이 된다.",
        ],
    }


def _build_bad_entry_lifecycle_attribution(events: list[dict], target_date: str | None) -> dict:
    candidates = _events_for_stage(events, "bad_entry_refined_candidate")
    refined_exits = _events_for_stage(events, "bad_entry_refined_exit")
    post_sell_by_record = _load_post_sell_evaluation_by_record_id(target_date)

    by_record: dict[str, list[dict]] = {}
    for event in candidates:
        record_id = event.get("record_id")
        if record_id in (None, "", "-"):
            continue
        by_record.setdefault(str(record_id), []).append(event)

    refined_exit_record_ids = {
        str(event.get("record_id"))
        for event in refined_exits
        if event.get("record_id") not in (None, "", "-")
    }
    outcome_counts: Counter = Counter()
    type_counts: Counter = Counter()
    examples: list[dict] = []
    post_sell_joined = 0
    post_sell_pending = 0

    for record_id, record_events in sorted(by_record.items()):
        post_sell = post_sell_by_record.get(record_id)
        if isinstance(post_sell, dict):
            post_sell_joined += 1
        else:
            post_sell_pending += 1
        outcome = str(post_sell.get("outcome") or "PENDING_POST_SELL") if isinstance(post_sell, dict) else "PENDING_POST_SELL"
        outcome_counts[outcome] += 1
        exclusion_reasons = {
            str(_event_fields(event).get("exclusion_reason") or "-")
            for event in record_events
        }
        would_exit = any(
            _truthy(_event_fields(event).get("would_exit"))
            or _truthy(_event_fields(event).get("should_exit"))
            for event in record_events
        )
        has_soft_stop_zone = "soft_stop_zone" in exclusion_reasons
        if outcome == "PENDING_POST_SELL":
            final_type = "pending_post_sell_outcome"
        elif outcome == "MISSED_UPSIDE":
            final_type = "false_positive_risk_after_candidate"
        elif record_id in refined_exit_record_ids:
            final_type = "refined_exit_finalized"
        elif would_exit and not has_soft_stop_zone:
            final_type = "preventable_bad_entry_candidate"
        elif has_soft_stop_zone:
            final_type = "late_detected_soft_stop_zone"
        else:
            final_type = "candidate_only_finalized"
        type_counts[final_type] += 1
        if len(examples) < 20:
            examples.append(
                {
                    "record_id": record_id,
                    "candidate_events": len(record_events),
                    "would_exit": would_exit,
                    "exclusion_reasons": sorted(exclusion_reasons),
                    "refined_exit_applied": record_id in refined_exit_record_ids,
                    "post_sell_joined": isinstance(post_sell, dict),
                    "post_sell_outcome": outcome,
                    "post_sell_exit_rule": post_sell.get("exit_rule") if isinstance(post_sell, dict) else None,
                    "post_sell_profit_rate": _safe_float(post_sell.get("profit_rate"), None)
                    if isinstance(post_sell, dict)
                    else None,
                    "mfe_10m_pct": _post_sell_metric(post_sell, "10m", "mfe_pct"),
                    "mae_10m_pct": _post_sell_metric(post_sell, "10m", "mae_pct"),
                    "final_type": final_type,
                }
            )

    return {
        "schema_version": 1,
        "status": "postclose_finalized_when_post_sell_joined",
        "runtime_change": False,
        "join_status": "record_id_to_post_sell_evaluations_after_postclose",
        "candidate_events": len(candidates),
        "candidate_records": len(by_record),
        "post_sell_joined_records": post_sell_joined,
        "post_sell_pending_records": post_sell_pending,
        "refined_exit_records": len(refined_exit_record_ids),
        "post_sell_outcome_counts": dict(outcome_counts),
        "final_type_counts": dict(type_counts),
        "examples": examples,
        "quality_notes": [
            "bad_entry_refined_candidate는 runtime provisional signal이며 최종 유형이 아니다.",
            "최종 유형은 postclose post_sell_evaluation이 record_id로 join된 뒤에만 닫는다.",
            "soft_stop_zone 후보는 조기 진입 차단 근거가 아니라 late-detected 후보로 분리한다.",
        ],
    }


def _build_eligible_but_not_chosen_report(events: list[dict], target_date: str | None) -> dict:
    snapshots = _events_for_stage(events, "stat_action_decision_snapshot")
    post_sell_by_record = _load_post_sell_evaluation_by_record_id(target_date)
    rows: list[dict] = []
    chosen_rows: list[dict] = []
    action_values: dict[str, dict[str, list[float]]] = {}
    action_reasons: dict[str, Counter] = {}
    chosen_action_values: dict[str, dict[str, list[float]]] = {}
    joined_snapshot_count = 0
    for event in snapshots:
        fields = _event_fields(event)
        chosen = str(fields.get("chosen_action") or "-").strip()
        eligible = _parse_action_list(fields.get("eligible_actions"))
        rejected_reasons = _parse_rejected_action_reasons(fields.get("rejected_actions"))
        candidates = [action for action in eligible if action != chosen]
        for action in rejected_reasons:
            if action != chosen and action not in candidates:
                candidates.append(action)
        if not candidates:
            continue
        record_id = event.get("record_id")
        post_sell = post_sell_by_record.get(str(record_id)) if record_id not in (None, "", "-") else None
        if post_sell:
            joined_snapshot_count += 1
        profit_rate = _safe_float(fields.get("profit_rate"), None)
        peak_profit = _safe_float(fields.get("peak_profit"), None)
        drawdown = _safe_float(fields.get("drawdown_from_peak"), None)
        current_ai_score = _safe_float(fields.get("current_ai_score"), None)
        snapshot_mfe_proxy = (
            round(max(0.0, peak_profit - profit_rate), 4)
            if peak_profit is not None and profit_rate is not None
            else None
        )
        snapshot_mae_proxy = round(min(0.0, -abs(drawdown)), 4) if drawdown is not None else None
        chosen_row = {
            "record_id": record_id,
            "stock_code": event.get("stock_code"),
            "stock_name": event.get("stock_name"),
            "emitted_at": event.get("emitted_at"),
            "chosen_action": chosen,
            "snapshot_profit_rate": profit_rate,
            "snapshot_peak_profit": peak_profit,
            "snapshot_drawdown_from_peak": drawdown,
            "snapshot_mfe_proxy": snapshot_mfe_proxy,
            "snapshot_mae_proxy": snapshot_mae_proxy,
            "current_ai_score": current_ai_score,
            "post_sell_joined": bool(post_sell),
            "post_sell_outcome": post_sell.get("outcome") if isinstance(post_sell, dict) else None,
            "post_sell_exit_rule": post_sell.get("exit_rule") if isinstance(post_sell, dict) else None,
            "post_sell_profit_rate": _safe_float(post_sell.get("profit_rate"), None) if isinstance(post_sell, dict) else None,
            "post_decision_mfe_10m_proxy": _post_sell_metric(post_sell, "10m", "mfe_pct"),
            "post_decision_mae_10m_proxy": _post_sell_metric(post_sell, "10m", "mae_pct"),
        }
        chosen_rows.append(chosen_row)
        chosen_action = _normalize_counterfactual_proxy_action(chosen)
        if chosen_action not in {"-", ""}:
            chosen_bucket = chosen_action_values.setdefault(
                chosen_action,
                {
                    "snapshot_profit_rate": [],
                    "snapshot_drawdown_from_peak": [],
                    "current_ai_score": [],
                    "post_decision_mfe_10m_proxy": [],
                    "post_decision_mae_10m_proxy": [],
                },
            )
            for key in chosen_bucket:
                value = _safe_float(chosen_row.get(key), None)
                if value is not None:
                    chosen_bucket[key].append(value)
        for action in candidates:
            reason = rejected_reasons.get(action, "eligible_not_chosen")
            row = {
                "record_id": record_id,
                "stock_code": event.get("stock_code"),
                "stock_name": event.get("stock_name"),
                "emitted_at": event.get("emitted_at"),
                "chosen_action": chosen,
                "candidate_action": action,
                "not_chosen_reason": reason,
                "snapshot_profit_rate": profit_rate,
                "snapshot_peak_profit": peak_profit,
                "snapshot_drawdown_from_peak": drawdown,
                "snapshot_mfe_proxy": snapshot_mfe_proxy,
                "snapshot_mae_proxy": snapshot_mae_proxy,
                "current_ai_score": current_ai_score,
                "post_sell_joined": bool(post_sell),
                "post_sell_outcome": post_sell.get("outcome") if isinstance(post_sell, dict) else None,
                "post_sell_exit_rule": post_sell.get("exit_rule") if isinstance(post_sell, dict) else None,
                "post_sell_profit_rate": _safe_float(post_sell.get("profit_rate"), None) if isinstance(post_sell, dict) else None,
                "post_decision_mfe_10m_proxy": _post_sell_metric(post_sell, "10m", "mfe_pct"),
                "post_decision_mae_10m_proxy": _post_sell_metric(post_sell, "10m", "mae_pct"),
            }
            rows.append(row)
            normalized_action = _normalize_counterfactual_proxy_action(action)
            bucket = action_values.setdefault(
                normalized_action,
                {
                    "snapshot_profit_rate": [],
                    "snapshot_drawdown_from_peak": [],
                    "current_ai_score": [],
                    "post_decision_mfe_10m_proxy": [],
                    "post_decision_mae_10m_proxy": [],
                },
            )
            for key in bucket:
                value = _safe_float(row.get(key), None)
                if value is not None:
                    bucket[key].append(value)
            action_reasons.setdefault(normalized_action, Counter())[str(reason or "-")] += 1

    action_summary = []
    for action, values in sorted(action_values.items()):
        joined = sum(
            1
            for row in rows
            if _normalize_counterfactual_proxy_action(row.get("candidate_action")) == action
            and row.get("post_sell_joined")
        )
        action_summary.append(
            {
                "candidate_action": action,
                "sample": sum(
                    1
                    for row in rows
                    if _normalize_counterfactual_proxy_action(row.get("candidate_action")) == action
                ),
                "post_sell_joined": joined,
                "avg_snapshot_profit_rate": round(_avg(values["snapshot_profit_rate"]) or 0.0, 4)
                if values["snapshot_profit_rate"]
                else None,
                "avg_snapshot_drawdown_from_peak": round(_avg(values["snapshot_drawdown_from_peak"]) or 0.0, 4)
                if values["snapshot_drawdown_from_peak"]
                else None,
                "avg_current_ai_score": round(_avg(values["current_ai_score"]) or 0.0, 4)
                if values["current_ai_score"]
                else None,
                "avg_post_decision_mfe_10m_proxy": round(_avg(values["post_decision_mfe_10m_proxy"]) or 0.0, 4)
                if values["post_decision_mfe_10m_proxy"]
                else None,
                "avg_post_decision_mae_10m_proxy": round(_avg(values["post_decision_mae_10m_proxy"]) or 0.0, 4)
                if values["post_decision_mae_10m_proxy"]
                else None,
                "top_not_chosen_reasons": dict(action_reasons.get(action, Counter()).most_common(5)),
            }
        )
    chosen_action_summary = []
    for action, values in sorted(chosen_action_values.items()):
        joined = sum(
            1
            for row in chosen_rows
            if _normalize_counterfactual_proxy_action(row.get("chosen_action")) == action
            and row.get("post_sell_joined")
        )
        chosen_action_summary.append(
            {
                "chosen_action": action,
                "sample": sum(
                    1
                    for row in chosen_rows
                    if _normalize_counterfactual_proxy_action(row.get("chosen_action")) == action
                ),
                "post_sell_joined": joined,
                "avg_snapshot_profit_rate": round(_avg(values["snapshot_profit_rate"]) or 0.0, 4)
                if values["snapshot_profit_rate"]
                else None,
                "avg_snapshot_drawdown_from_peak": round(_avg(values["snapshot_drawdown_from_peak"]) or 0.0, 4)
                if values["snapshot_drawdown_from_peak"]
                else None,
                "avg_current_ai_score": round(_avg(values["current_ai_score"]) or 0.0, 4)
                if values["current_ai_score"]
                else None,
                "avg_post_decision_mfe_10m_proxy": round(_avg(values["post_decision_mfe_10m_proxy"]) or 0.0, 4)
                if values["post_decision_mfe_10m_proxy"]
                else None,
                "avg_post_decision_mae_10m_proxy": round(_avg(values["post_decision_mae_10m_proxy"]) or 0.0, 4)
                if values["post_decision_mae_10m_proxy"]
                else None,
            }
        )
    return {
        "schema_version": 1,
        "status": "report_only",
        "runtime_change": False,
        "join_status": "post_sell_10m_proxy_when_record_id_matches",
        "sample_snapshots": len(snapshots),
        "sample_candidates": len(rows),
        "post_sell_joined_candidates": sum(1 for row in rows if row.get("post_sell_joined")),
        "post_sell_joined_snapshots": joined_snapshot_count,
        "fields": [
            "candidate_action",
            "chosen_action",
            "snapshot_profit_rate",
            "snapshot_mfe_proxy",
            "snapshot_mae_proxy",
            "post_decision_mfe_10m_proxy",
            "post_decision_mae_10m_proxy",
        ],
        "action_summary": action_summary,
        "chosen_action_summary": chosen_action_summary,
        "examples": rows[:20],
        "quality_notes": [
            "post_decision_*_proxy는 post_sell_evaluation 10분 지표를 record_id로 붙인 report-only proxy다.",
            "snapshot_*_proxy는 decision snapshot 순간의 peak/drawdown 기반 proxy이며 실현 후행 성과가 아니다.",
            "이 섹션은 live 판단, AI routing, 주문/청산 변경에 직접 쓰지 않는다.",
        ],
    }


def _completed_summary(rows: list[dict]) -> dict:
    total = len(rows)
    losses = [row for row in rows if (_safe_float(row.get("profit_rate"), 0.0) or 0.0) < 0.0]
    return {
        "completed_valid": total,
        "loss_count": len(losses),
    }


def _row_rec_date(row: dict) -> date | None:
    value = row.get("rec_date") or row.get("date") or row.get("trade_date")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, "", "-", "None"):
        return None
    text = str(value).strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except Exception:
        return None


def _filter_completed_rows_by_date(rows: list[dict], start_date: str, end_date: str) -> list[dict]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    filtered: list[dict] = []
    missing_date_rows: list[dict] = []
    for row in rows:
        rec_date = _row_rec_date(row)
        if rec_date is None:
            missing_date_rows.append(row)
            continue
        if start <= rec_date <= end:
            filtered.append(row)
    if not filtered and missing_date_rows and start <= end:
        return list(missing_date_rows)
    return filtered


def _valid_profit_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if _safe_float(row.get("profit_rate"), None) is not None]


def _is_scalp_sim_event(event: dict) -> bool:
    fields = _event_fields(event)
    stage = str(event.get("stage") or "")
    return (
        stage.startswith("scalp_sim_")
        or str(fields.get("simulation_book") or "") == "scalp_ai_buy_all"
    )


def _extract_scalp_sim_completed_rows(events: list[dict]) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for event in events or []:
        if str(event.get("stage") or "") != "scalp_sim_sell_order_assumed_filled":
            continue
        fields = _event_fields(event)
        profit_rate = _safe_float(fields.get("profit_rate"), None)
        if profit_rate is None:
            continue
        sim_record_id = str(fields.get("sim_record_id") or event.get("record_id") or "").strip()
        key = sim_record_id or f"{event.get('stock_code')}-{event.get('emitted_at')}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "rec_date": str(event.get("emitted_date") or "")[:10],
                "stock_code": str(event.get("stock_code") or "").strip()[:6],
                "stock_name": event.get("stock_name"),
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "buy_price": _safe_float(fields.get("buy_price"), None),
                "buy_qty": _safe_int(fields.get("qty"), 0) or 0,
                "sell_price": _safe_float(fields.get("assumed_fill_price"), None),
                "profit_rate": profit_rate,
                "add_count": _safe_int(fields.get("add_count"), 0) or 0,
                "avg_down_count": _safe_int(fields.get("avg_down_count"), 0) or 0,
                "pyramid_count": _safe_int(fields.get("pyramid_count"), 0) or 0,
                "last_add_type": fields.get("last_add_type"),
                "source": "scalp_sim",
                "cohort": "scalp_sim_equal_authority",
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": sim_record_id,
                "sim_parent_record_id": fields.get("sim_parent_record_id"),
                "actual_order_submitted": False,
            }
        )
    return rows


def _completed_by_source_summary(real_rows: list[dict], sim_rows: list[dict]) -> dict:
    combined = list(real_rows or []) + list(sim_rows or [])
    return {
        "real": _completed_profit_summary(real_rows or []),
        "sim": _completed_profit_summary(sim_rows or []),
        "combined": _completed_profit_summary(combined),
        "real_family_candidate_authority": "real_only",
        "sim_calibration_authority": "sim_equal_weight",
        "combined_authority": "diagnostic_only_not_family_candidate_input",
    }


def _scalp_simulator_post_sell_join_summary(
    *,
    target_date: str | None,
    completed_rows: list[dict],
) -> dict:
    evaluations = _load_sim_post_sell_evaluation_by_sim_id(target_date)
    joined: list[dict] = []
    pending = 0
    for row in completed_rows or []:
        keys = [
            str(row.get("sim_record_id") or "").strip(),
            str(row.get("sim_parent_record_id") or "").strip(),
        ]
        evaluation = next((evaluations.get(key) for key in keys if key and evaluations.get(key)), None)
        if not evaluation:
            pending += 1
            continue
        metrics_10m = evaluation.get("metrics_10m") if isinstance(evaluation.get("metrics_10m"), dict) else {}
        joined.append(
            {
                "stock_code": row.get("stock_code") or evaluation.get("stock_code"),
                "stock_name": row.get("stock_name") or evaluation.get("stock_name"),
                "sim_record_id": row.get("sim_record_id") or evaluation.get("sim_record_id"),
                "profit_rate": _safe_float(row.get("profit_rate"), None),
                "outcome": str(evaluation.get("outcome") or "NEUTRAL"),
                "mfe_10m_pct": _safe_float(metrics_10m.get("mfe_pct"), 0.0),
                "mae_10m_pct": _safe_float(metrics_10m.get("mae_pct"), 0.0),
                "close_10m_pct": _safe_float(metrics_10m.get("close_ret_pct"), 0.0),
            }
        )
    outcome_counts = Counter(str(item.get("outcome") or "NEUTRAL").upper() for item in joined)
    mfe_values = [_safe_float(item.get("mfe_10m_pct"), None) for item in joined]
    mae_values = [_safe_float(item.get("mae_10m_pct"), None) for item in joined]
    close_values = [_safe_float(item.get("close_10m_pct"), None) for item in joined]
    mfe_values = [value for value in mfe_values if value is not None]
    mae_values = [value for value in mae_values if value is not None]
    close_values = [value for value in close_values if value is not None]
    return {
        "join_status": "sim_record_id_to_sim_post_sell_evaluations_after_postclose",
        "candidate_artifact": f"data/post_sell/sim_post_sell_candidates_{target_date}.jsonl" if target_date else None,
        "evaluation_artifact": f"data/post_sell/sim_post_sell_evaluations_{target_date}.jsonl" if target_date else None,
        "completed_sample": len(completed_rows or []),
        "joined_completed": len(joined),
        "pending_completed": int(pending),
        "outcome_counts": dict(outcome_counts),
        "avg_mfe_10m_pct": round(_avg(mfe_values), 4) if mfe_values else None,
        "avg_mae_10m_pct": round(_avg(mae_values), 4) if mae_values else None,
        "avg_close_10m_pct": round(_avg(close_values), 4) if close_values else None,
        "runtime_effect": False,
        "decision_authority": "sim_equal_weight_observation_only",
        "forbidden_uses": [
            "threshold mutation",
            "order guard mutation",
            "provider change",
            "bot restart",
            "broker order submit",
        ],
        "examples": joined[:5],
    }


def _scalp_simulator_event_summary(
    events: list[dict],
    sim_completed_rows: list[dict] | None = None,
    *,
    target_date: str | None = None,
) -> dict:
    sim_events = [event for event in events or [] if _is_scalp_sim_event(event)]
    stage_counts = Counter(str(event.get("stage") or "-") for event in sim_events)
    completed_rows = sim_completed_rows if sim_completed_rows is not None else _extract_scalp_sim_completed_rows(events)
    return {
        "enabled_default": True,
        "simulation_book": "scalp_ai_buy_all",
        "fill_policy": "signal_inclusive_best_ask_v1",
        "calibration_authority": "equal_weight",
        "event_count": len(sim_events),
        "stage_counts": dict(stage_counts),
        "entry_armed": int(stage_counts.get("scalp_sim_entry_armed", 0)),
        "buy_filled": int(stage_counts.get("scalp_sim_buy_order_assumed_filled", 0)),
        "holding_started": int(stage_counts.get("scalp_sim_holding_started", 0)),
        "sell_completed": int(stage_counts.get("scalp_sim_sell_order_assumed_filled", 0)),
        "entry_expired": int(stage_counts.get("scalp_sim_entry_expired", 0)),
        "entry_unpriced": int(stage_counts.get("scalp_sim_entry_unpriced", 0)),
        "duplicate_buy_signal": int(stage_counts.get("scalp_sim_duplicate_buy_signal", 0)),
        "entry_ai_price_applied": int(stage_counts.get("scalp_sim_entry_ai_price_applied", 0)),
        "entry_ai_price_skip_order": int(stage_counts.get("scalp_sim_entry_ai_price_skip_order", 0)),
        "entry_submit_revalidation_warning": int(
            stage_counts.get("scalp_sim_entry_submit_revalidation_warning", 0)
        ),
        "entry_submit_revalidation_block": int(stage_counts.get("scalp_sim_entry_submit_revalidation_block", 0)),
        "scale_in_filled": int(stage_counts.get("scalp_sim_scale_in_order_assumed_filled", 0)),
        "scale_in_unfilled": int(stage_counts.get("scalp_sim_scale_in_order_unfilled", 0)),
        "scalp_sim_ai_holding_live_call": int(stage_counts.get("scalp_sim_ai_holding_live_call", 0)),
        "scalp_sim_ai_holding_reuse": int(stage_counts.get("scalp_sim_ai_holding_reuse", 0)),
        "scalp_sim_ai_holding_deferred": int(stage_counts.get("scalp_sim_ai_holding_deferred", 0)),
        "sim_ai_budget_exhausted": int(stage_counts.get("sim_ai_budget_exhausted", 0)),
        "sim_ai_critical_bypass": int(stage_counts.get("sim_ai_critical_bypass", 0)),
        "overnight_decision": int(stage_counts.get("scalp_sim_overnight_decision", 0)),
        "overnight_sell_today": int(stage_counts.get("scalp_sim_overnight_sell_today", 0)),
        "overnight_hold": int(stage_counts.get("scalp_sim_overnight_hold", 0)),
        "overnight_carry_restored": int(stage_counts.get("scalp_sim_overnight_carry_restored", 0)),
        "overnight_completed_sell": sum(
            1
            for event in sim_events
            if str(event.get("stage") or "") == "scalp_sim_sell_order_assumed_filled"
            and ((event.get("fields") or {}).get("exit_rule") == "scalp_sim_overnight_sell_today")
        ),
        "completed_profit_summary": _completed_profit_summary(completed_rows or []),
        "post_sell_join": _scalp_simulator_post_sell_join_summary(
            target_date=target_date,
            completed_rows=completed_rows or [],
        ),
    }


def _is_normal_only_row(row: dict) -> bool:
    markers = [
        row.get("strategy"),
        row.get("entry_type"),
        row.get("order_type"),
        row.get("cohort"),
        row.get("source"),
    ]
    joined = " ".join(str(value or "").lower() for value in markers)
    return "fallback" not in joined and "remote" not in joined and "songstock" not in joined


def _is_initial_only_row(row: dict) -> bool:
    add_count = _safe_int(row.get("add_count"), 0) or 0
    avg_down_count = _safe_int(row.get("avg_down_count"), 0) or 0
    pyramid_count = _safe_int(row.get("pyramid_count"), 0) or 0
    last_add_type = str(row.get("last_add_type") or "").strip().upper()
    return add_count <= 0 and avg_down_count <= 0 and pyramid_count <= 0 and not last_add_type


def _completed_profit_summary(rows: list[dict]) -> dict:
    valid_rows = _valid_profit_rows(rows)
    profit_values = [_safe_float(row.get("profit_rate"), None) for row in valid_rows]
    profit_values = [value for value in profit_values if value is not None]
    wins = [value for value in profit_values if value > 0]
    losses = [value for value in profit_values if value < 0]
    return {
        "sample": len(profit_values),
        "win_count": len(wins),
        "loss_count": len(losses),
        "avg_profit_rate": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
        "median_profit_rate": round(_percentile(profit_values, 50, 0.0), 4) if profit_values else None,
        "downside_p10_profit_rate": round(_percentile(profit_values, 10, 0.0), 4) if profit_values else None,
        "upside_p90_profit_rate": round(_percentile(profit_values, 90, 0.0), 4) if profit_values else None,
        "win_rate": round(len(wins) / len(profit_values), 4) if profit_values else None,
        "loss_rate": round(len(losses) / len(profit_values), 4) if profit_values else None,
        "stddev_profit_rate": round(_stddev(profit_values) or 0.0, 4) if len(profit_values) >= 2 else None,
    }


def _completed_cohort_summary(rows: list[dict]) -> dict:
    valid_rows = _valid_profit_rows(rows)
    cohorts = {
        "all_completed_valid": valid_rows,
        "normal_only": [row for row in valid_rows if _is_normal_only_row(row)],
        "initial_only": [row for row in valid_rows if _is_initial_only_row(row)],
        "pyramid_activated": [
            row
            for row in valid_rows
            if (_safe_int(row.get("pyramid_count"), 0) or 0) > 0
            or str(row.get("last_add_type") or "").strip().upper() == "PYRAMID"
        ],
        "reversal_add_activated": [
            row
            for row in valid_rows
            if (_safe_int(row.get("avg_down_count"), 0) or 0) > 0
            or str(row.get("last_add_type") or "").strip().upper() in {"AVG_DOWN", "REVERSAL_ADD"}
        ],
    }
    return {name: _completed_profit_summary(cohort_rows) for name, cohort_rows in cohorts.items()}


def _field_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _score_between(value: float | None, floor: float, target: float) -> float:
    if value is None:
        return 0.0
    if target == floor:
        return 1.0 if value >= target else 0.0
    return round(_clamp((value - floor) / (target - floor), 0.0, 1.0), 4)


def _build_position_sizing_cap_release_family(events: list[dict], completed_rows: list[dict]) -> dict:
    cap_events = _events_for_stage(events, "initial_entry_qty_cap_applied")
    cap_reduced = [event for event in cap_events if _field_bool(_event_fields(event).get("applied"))]
    wait_probe_cap_events = _events_for_stage(events, "wait6579_probe_canary_applied")
    scale_in_resolved = _events_for_stage(events, "scale_in_price_resolved")
    scale_in_executed = _events_for_stage(events, "scale_in_executed")
    submitted = _events_for_stage(events, "order_bundle_submitted")
    full_fill = _events_for_stage(events, "full_fill")
    partial_fill = _events_for_stage(events, "partial_fill")
    order_failed = _events_for_stage(events, "order_bundle_failed") + _events_for_stage(events, "buy_order_failed")
    soft_stop = _events_for_stage(events, "sell_completed")
    soft_stop = [
        event
        for event in soft_stop
        if "soft" in str(_event_fields(event).get("exit_rule") or _event_fields(event).get("sell_reason_type") or "").lower()
    ]

    normal_only_rows = [row for row in _valid_profit_rows(completed_rows) if _is_normal_only_row(row)]
    initial_only_rows = [row for row in normal_only_rows if _is_initial_only_row(row)]
    normal_summary = _completed_profit_summary(normal_only_rows)
    initial_summary = _completed_profit_summary(initial_only_rows)

    completed_sample = int(normal_summary.get("sample") or 0)
    avg_profit = _safe_float(normal_summary.get("avg_profit_rate"), None)
    win_rate = _safe_float(normal_summary.get("win_rate"), None)
    downside_p10 = _safe_float(normal_summary.get("downside_p10_profit_rate"), None)
    fill_total = len(full_fill) + len(partial_fill)
    full_fill_rate = (len(full_fill) / fill_total) if fill_total > 0 else None
    submitted_count = len(submitted)
    order_failed_rate = (len(order_failed) / submitted_count) if submitted_count > 0 else 0.0
    soft_stop_rate = (len(soft_stop) / completed_sample) if completed_sample > 0 else None

    safety_floor = {
        "normal_completed_sample": completed_sample >= 30,
        "cap_reduced_sample": len(cap_reduced) >= 5,
        "submitted_sample": submitted_count >= 15,
        "overall_ev_floor": avg_profit is not None and avg_profit >= 0.10,
        "severe_downside_floor": downside_p10 is not None and downside_p10 >= -2.00,
        "order_failure_floor": order_failed_rate <= 0.10,
    }
    tradeoff_components = {
        "overall_ev": _score_between(avg_profit, 0.10, 0.35),
        "win_rate": _score_between(win_rate, 0.45, 0.55),
        "full_fill_quality": _score_between(full_fill_rate, 0.60, 0.85),
        "downside_tail": _score_between(downside_p10, -2.00, -1.20),
        "order_failure": _score_between(0.10 - order_failed_rate, 0.0, 0.10),
        "soft_stop_tail": _score_between(None if soft_stop_rate is None else 0.45 - soft_stop_rate, 0.0, 0.45),
        "cap_opportunity": _score_between(float(len(cap_reduced)), 5.0, 15.0),
    }
    tradeoff_score = round(
        (tradeoff_components["overall_ev"] * 0.40)
        + (tradeoff_components["win_rate"] * 0.10)
        + (tradeoff_components["full_fill_quality"] * 0.10)
        + (tradeoff_components["downside_tail"] * 0.15)
        + (tradeoff_components["order_failure"] * 0.10)
        + (tradeoff_components["soft_stop_tail"] * 0.10)
        + (tradeoff_components["cap_opportunity"] * 0.05),
        4,
    )
    approval_ready = all(safety_floor.values()) and tradeoff_score >= 0.70
    current = {
        "initial_entry_qty_cap_enabled": bool(
            getattr(TRADING_RULES, "SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED", True)
        ),
        "initial_entry_max_qty": int(getattr(TRADING_RULES, "SCALPING_INITIAL_ENTRY_MAX_QTY", 1)),
        "wait6579_probe_max_qty": int(getattr(TRADING_RULES, "AI_WAIT6579_PROBE_CANARY_MAX_QTY", 1)),
        "scale_in_effective_qty_cap": int(getattr(TRADING_RULES, "SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP", 1)),
    }
    recommended = dict(current)
    if approval_ready:
        recommended.update(
            {
                "initial_entry_qty_cap_enabled": False,
                "initial_entry_max_qty": 0,
                "wait6579_probe_max_qty": 0,
                "scale_in_effective_qty_cap": 0,
            }
        )
    return {
        "family": "position_sizing_cap_release",
        "stage": "position_sizing",
        "sample": {
            "normal_completed_valid": completed_sample,
            "initial_only_completed_valid": int(initial_summary.get("sample") or 0),
            "initial_entry_cap_events": len(cap_events),
            "initial_entry_cap_reduced": len(cap_reduced),
            "wait6579_probe_cap_events": len(wait_probe_cap_events),
            "scale_in_resolved": len(scale_in_resolved),
            "scale_in_executed": len(scale_in_executed),
            "submitted": submitted_count,
            "full_fill": len(full_fill),
            "partial_fill": len(partial_fill),
            "order_failed": len(order_failed),
            "soft_stop_completed": len(soft_stop),
            "full_fill_rate": round(full_fill_rate, 4) if full_fill_rate is not None else None,
            "order_failed_rate": round(order_failed_rate, 4),
            "soft_stop_rate": round(soft_stop_rate, 4) if soft_stop_rate is not None else None,
            "normal_completed_summary": normal_summary,
            "initial_only_completed_summary": initial_summary,
            "safety_floor": safety_floor,
            "tradeoff_components": tradeoff_components,
            "tradeoff_score": tradeoff_score,
            "tradeoff_score_required": 0.70,
        },
        "apply_ready": approval_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "manual_approval_required" if approval_ready else "observe_only",
        "notes": [
            "1주 cap 해제는 자동 runtime apply 대상이 아니라 사용자 승인 요청 대상이다.",
            "완벽한 spot을 기다리지 않고 overall EV와 체결품질, 손실 tail, cap opportunity를 가중한 efficient trade-off score로 판단한다.",
            "표본, overall EV floor, severe downside, 주문 실패율만 safety floor로 hard하게 본다.",
            "승인 전에는 신규 BUY, wait6579 probe, REVERSAL_ADD/PYRAMID 모두 1주 cap을 유지한다.",
        ],
    }


def _notional_weighted_ev_pct(rows: list[dict]) -> float | None:
    weighted_sum = 0.0
    total_notional = 0.0
    for row in _valid_profit_rows(rows):
        profit_rate = _safe_float(row.get("profit_rate"), None)
        if profit_rate is None:
            continue
        buy_price = _safe_float(row.get("buy_price"), None)
        buy_qty = _safe_float(row.get("buy_qty"), None)
        notional = None
        if buy_price is not None and buy_qty is not None and buy_price > 0 and buy_qty > 0:
            notional = buy_price * buy_qty
        if notional is None:
            notional = _safe_float(row.get("notional_krw"), None)
        if notional is None or notional <= 0:
            continue
        weighted_sum += float(profit_rate) * float(notional)
        total_notional += float(notional)
    if total_notional <= 0:
        return None
    return round(weighted_sum / total_notional, 4)


def _bucket_counter(events: list[dict], *field_names: str) -> dict:
    values: list[str] = []
    for event in events:
        fields = _event_fields(event)
        for field_name in field_names:
            value = fields.get(field_name)
            if value not in (None, "", "-"):
                values.append(str(value))
                break
    return dict(Counter(values).most_common(10))


def _numeric_event_values(events: list[dict], *field_names: str) -> list[float]:
    values: list[float] = []
    for event in events:
        fields = _event_fields(event)
        for field_name in field_names:
            value = _safe_float(fields.get(field_name), None)
            if value is not None:
                values.append(float(value))
                break
    return values


def _build_position_sizing_dynamic_formula_family(events: list[dict], completed_rows: list[dict]) -> dict:
    sizing_stages = {
        "budget_pass",
        "blocked_zero_qty",
        "auth_zero_qty",
        "initial_entry_qty_cap_applied",
        "wait6579_probe_canary_applied",
        "scale_in_price_resolved",
        "scalp_sim_entry_armed",
        "scalp_sim_buy_order_assumed_filled",
        "swing_probe_entry_assumed_filled",
        "swing_sim_entry_assumed_filled",
    }
    sizing_events = [event for event in events if str(event.get("stage") or "") in sizing_stages]
    real_rows = [row for row in _valid_profit_rows(completed_rows) if _is_normal_only_row(row)]
    real_summary = _completed_profit_summary(real_rows)
    real_sample = int(real_summary.get("sample") or 0)
    notional_ev = _notional_weighted_ev_pct(real_rows)

    qty_source_counts = _bucket_counter(
        sizing_events,
        "qty_source",
        "scalp_sim_entry_qty_source",
        "counterfactual_qty_source",
    )
    sim_probe_rows = [
        event
        for event in sizing_events
        if str(_event_fields(event).get("actual_order_submitted") or "").strip().lower() == "false"
        or str(_event_fields(event).get("budget_authority") or "").strip()
        == "sim_virtual_not_real_orderable_amount"
        or str(_event_fields(event).get("qty_source") or "").strip() == "sim_virtual_budget_dynamic_formula"
        or str(_event_fields(event).get("scalp_sim_entry_qty_source") or "").strip()
        == "sim_virtual_budget_dynamic_formula"
    ]
    real_order_rows = [
        event
        for event in sizing_events
        if str(_event_fields(event).get("actual_order_submitted") or "").strip().lower() == "true"
    ]

    baseline_qty_values = _numeric_event_values(sizing_events, "baseline_qty", "original_qty", "would_qty")
    candidate_qty_values = _numeric_event_values(
        sizing_events,
        "candidate_qty",
        "effective_qty",
        "qty",
        "real_buy_qty",
        "requested_buy_qty",
    )
    spread_values = _numeric_event_values(sizing_events, "spread_bps")
    liquidity_values = _numeric_event_values(sizing_events, "liquidity_value")
    score_values = _numeric_event_values(sizing_events, "score", "ai_score", "current_ai_score")

    required_inputs = {
        "score": bool(score_values),
        "strategy": bool(_bucket_counter(sizing_events, "strategy", "trade_type")),
        "volatility": bool(_bucket_counter(sizing_events, "volatility_bucket", "volatility_mode")),
        "liquidity": bool(liquidity_values or _bucket_counter(sizing_events, "liquidity_bucket")),
        "spread": bool(spread_values),
        "price_band": bool(_bucket_counter(sizing_events, "price_band", "price_bucket")),
        "recent_loss": bool(_bucket_counter(sizing_events, "recent_loss_bucket", "loss_bucket")),
        "portfolio_exposure": bool(_bucket_counter(sizing_events, "portfolio_exposure_bucket", "exposure_bucket")),
    }
    source_quality_blockers = [
        f"missing_input_{key}" for key, present in required_inputs.items() if not bool(present)
    ]
    source_quality_passed = not source_quality_blockers
    source_quality_adjusted_ev = (
        round(float(notional_ev) * 0.5, 4) if notional_ev is not None and source_quality_blockers else notional_ev
    )
    sample_ready = real_sample >= 30 and source_quality_passed

    current = {
        "formula_version": "baseline_describe_buy_capacity",
        "formula_mode": "current_runtime_formula",
        "runtime_apply_allowed": False,
    }
    recommended = {
        "formula_version": "position_sizing_dynamic_formula:v1_report_only",
        "formula_mode": "report_only",
        "runtime_apply_allowed": False,
        "approval_artifact_path": "data/threshold_cycle/approvals/position_sizing_dynamic_formula_YYYY-MM-DD.json",
    }
    return {
        "family": "position_sizing_dynamic_formula",
        "stage": "position_sizing",
        "sample": {
            "real_completed_valid": real_sample,
            "sizing_event_count": len(sizing_events),
            "sim_probe_sizing_event_count": len(sim_probe_rows),
            "real_order_sizing_event_count": len(real_order_rows),
            "qty_source_counts": qty_source_counts,
            "input_coverage": required_inputs,
            "source_quality_passed": source_quality_passed,
            "source_quality_blockers": source_quality_blockers,
            "primary_metric": "notional_weighted_ev_pct"
            if notional_ev is not None
            else "source_quality_adjusted_ev_pct",
            "notional_weighted_ev_pct": notional_ev,
            "source_quality_adjusted_ev_pct": source_quality_adjusted_ev,
            "real_completed_summary": real_summary,
            "baseline_qty_avg": round(_avg(baseline_qty_values) or 0.0, 4) if baseline_qty_values else None,
            "candidate_qty_avg": round(_avg(candidate_qty_values) or 0.0, 4) if candidate_qty_values else None,
            "score_avg": round(_avg(score_values) or 0.0, 4) if score_values else None,
            "spread_bps_p90": round(_percentile(spread_values, 90, 0.0), 4) if spread_values else None,
            "liquidity_value_p50": round(_percentile(liquidity_values, 50, 0.0), 4)
            if liquidity_values
            else None,
            "strategy_counts": _bucket_counter(sizing_events, "strategy", "trade_type"),
            "price_band_counts": _bucket_counter(sizing_events, "price_band", "price_bucket"),
            "volatility_bucket_counts": _bucket_counter(sizing_events, "volatility_bucket", "volatility_mode"),
            "recent_loss_bucket_counts": _bucket_counter(sizing_events, "recent_loss_bucket", "loss_bucket"),
            "portfolio_exposure_bucket_counts": _bucket_counter(
                sizing_events,
                "portfolio_exposure_bucket",
                "exposure_bucket",
            ),
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "report_only_design",
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "report_only_until_approval_artifact",
            "window_policy": "rolling_10d_with_real_denominator",
            "sample_floor": 30,
            "primary_decision_metric": ["notional_weighted_ev_pct", "source_quality_adjusted_ev_pct"],
            "source_quality_gate": "all_required_inputs_present_and_real_sim_probe_split",
            "forbidden_uses": [
                "sim_probe_single_source_live_cap_release",
                "runtime_order_qty_change_without_approval",
                "reuse_position_sizing_cap_release_approval",
            ],
        },
        "notes": [
            "동적수량 산식 튜닝 owner를 자동화체인 report-only source bundle에 편입한다.",
            "position_sizing_cap_release와 분리하며 cap 해제 approval을 재사용하지 않는다.",
            "sim/probe/counterfactual은 diagnostic 가속 입력이며 real denominator를 대체하지 않는다.",
            "실주문 수량 확대는 별도 approval artifact, same-stage owner guard, rollback guard가 필요하다.",
        ],
    }


def _build_mechanical_entry_family(events: list[dict]) -> dict:
    current = {
        "max_signal_score": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE", 75.0) or 75.0),
        "min_strength": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH", 110.0) or 110.0),
        "min_buy_pressure": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE", 50.0) or 50.0),
        "max_ws_age_ms": int(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS", 1200) or 1200),
        "max_ws_jitter_ms": int(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS", 500) or 500),
        "max_spread_ratio": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO", 0.0085) or 0.0085),
    }
    budget_pass = _stage_count(events, "budget_pass")
    submitted = _stage_count(events, "order_bundle_submitted")
    strength = _extract_field_values(events, "budget_pass", "latest_strength")
    buy_pressure = _extract_field_values(events, "budget_pass", "buy_pressure_10t")
    ws_age = _extract_field_values(events, "budget_pass", "ws_age_ms")
    ws_jitter = _extract_field_values(events, "budget_pass", "ws_jitter_ms")
    spread = _extract_field_values(events, "budget_pass", "spread_ratio")
    signal_score = _extract_field_values(events, "budget_pass", "signal_score")

    sample_ready = budget_pass >= 500 and submitted >= 20
    recommended = {
        "max_signal_score": round(_clamp(_percentile(signal_score, 90, current["max_signal_score"]), 65.0, 85.0), 1),
        "min_strength": round(_clamp(_percentile(strength, 25, current["min_strength"]), 95.0, 130.0), 1),
        "min_buy_pressure": round(_clamp(_percentile(buy_pressure, 25, current["min_buy_pressure"]), 45.0, 70.0), 1),
        "max_ws_age_ms": int(round(_clamp(_percentile(ws_age, 90, current["max_ws_age_ms"]), 600.0, 1600.0))),
        "max_ws_jitter_ms": int(round(_clamp(_percentile(ws_jitter, 90, current["max_ws_jitter_ms"]), 200.0, 700.0))),
        "max_spread_ratio": round(_clamp(_percentile(spread, 90, current["max_spread_ratio"]), 0.0040, 0.0120), 4),
    }
    return {
        "family": "entry_mechanical_momentum",
        "stage": "entry",
        "sample": {"budget_pass": budget_pass, "submitted": submitted},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "entry family는 same-day holding/exit live owner와 분리한다.",
            "budget_pass>=500, submitted>=20 미만이면 추천값은 shadow reference로만 사용한다.",
        ],
    }


def _event_score(event: dict) -> float:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    for key in ("ai_score", "score", "wait6579_probe_canary_score"):
        value = _safe_float(fields.get(key), None)
        if value is not None:
            return value
    return 0.0


def _build_score65_74_recovery_probe_family(events: list[dict]) -> dict:
    current = {
        "enabled": bool(getattr(TRADING_RULES, "AI_SCORE65_74_RECOVERY_PROBE_ENABLED", False)),
        "min_score": int(getattr(TRADING_RULES, "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE", 65) or 65),
        "max_score": int(getattr(TRADING_RULES, "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE", 74) or 74),
        "min_buy_pressure": float(
            getattr(TRADING_RULES, "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE", 65.0) or 65.0
        ),
        "min_tick_accel": float(
            getattr(TRADING_RULES, "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL", 1.20) or 1.20
        ),
        "min_micro_vwap_bp": float(
            getattr(TRADING_RULES, "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP", 0.0) or 0.0
        ),
        "max_budget_krw": int(getattr(TRADING_RULES, "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW", 50_000) or 50_000),
        "max_qty": int(getattr(TRADING_RULES, "AI_WAIT6579_PROBE_CANARY_MAX_QTY", 0) or 0),
    }
    wait_candidates = [
        event
        for event in events
        if str(event.get("stage") or "") == "wait65_79_ev_candidate"
        and current["min_score"] <= _event_score(event) <= current["max_score"]
    ]
    blocked_score = [
        event
        for event in events
        if str(event.get("stage") or "") == "blocked_ai_score"
        and current["min_score"] <= _event_score(event) <= current["max_score"]
    ]
    applied = _events_for_stage(events, "score65_74_recovery_probe")
    submitted = _events_for_stage(events, "order_bundle_submitted")
    filled = _events_for_stage(events, "position_rebased_after_fill")
    budget_pass = _events_for_stage(events, "budget_pass")
    sample_ready = len(wait_candidates) >= 20 and bool(budget_pass) and len(submitted) < max(20, len(budget_pass) // 10)
    recommended = dict(current)
    if sample_ready:
        recommended["enabled"] = True
    return {
        "family": "score65_74_recovery_probe",
        "stage": "entry",
        "sample": {
            "wait65_79_score65_74_candidate": len(wait_candidates),
            "blocked_score65_74": len(blocked_score),
            "probe_applied": len(applied),
            "budget_pass": len(budget_pass),
            "submitted": len(submitted),
            "filled": len(filled),
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "efficient_tradeoff_canary_candidate" if sample_ready else "observe_only",
        "notes": [
            "broad score threshold 완화가 아니라 score65~74 전용 예산 bounded canary 후보만 만든다.",
            "partial sample 0은 live 전면 차단이 아니라 post-apply calibration target으로 남긴다.",
            "latency DANGER 제외, 수급/가속/micro-VWAP gate와 예산/position/protection guard는 유지한다.",
        ],
    }


def _build_pre_submit_guard_family(events: list[dict]) -> dict:
    current = {
        "max_below_bid_bps": int(getattr(TRADING_RULES, "SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS", 80) or 80),
    }
    values = _extract_field_values(events, "order_bundle_submitted", "price_below_bid_bps")
    if not values:
        values = _extract_field_values(events, "latency_pass", "price_below_bid_bps")
    sim_values = _extract_field_values(events, "scalp_sim_buy_order_virtual_pending", "price_below_bid_bps")
    passive_probe_events = [
        event
        for event in events
        if str(_event_fields(event).get("entry_order_lifecycle") or "") == "passive_probe"
        or bool(_event_fields(event).get("entry_passive_probe_applied"))
    ]
    cancel_confirmed = _events_for_stage(events, "entry_order_cancel_confirmed")
    revalidation_warnings = _events_for_stage(events, "entry_submit_revalidation_warning")
    revalidation_blocks = _events_for_stage(events, "entry_submit_revalidation_block")
    sim_revalidation_warnings = _events_for_stage(events, "scalp_sim_entry_submit_revalidation_warning")
    sim_revalidation_blocks = _events_for_stage(events, "scalp_sim_entry_submit_revalidation_block")
    sim_ai_price_applied = _events_for_stage(events, "scalp_sim_entry_ai_price_applied")
    sim_ai_price_skip = _events_for_stage(events, "scalp_sim_entry_ai_price_skip_order")
    sample_ready = len(values) >= 50
    recommended = {
        "max_below_bid_bps": int(round(_clamp(_percentile(values, 90, current["max_below_bid_bps"]), 60.0, 120.0))),
    }
    return {
        "family": "pre_submit_price_guard",
        "stage": "entry",
        "sample": {
            "price_below_bid_bps": len(values),
            "sim_price_below_bid_bps": len(sim_values),
            "guard_block": _stage_count(events, "pre_submit_price_guard_block"),
            "passive_probe": len(passive_probe_events),
            "entry_timeout_cancel_confirmed": len(cancel_confirmed),
            "submit_revalidation_warning": len(revalidation_warnings),
            "submit_revalidation_block": len(revalidation_blocks),
            "sim_entry_ai_price_applied": len(sim_ai_price_applied),
            "sim_entry_ai_price_skip_order": len(sim_ai_price_skip),
            "sim_submit_revalidation_warning": len(sim_revalidation_warnings),
            "sim_submit_revalidation_block": len(sim_revalidation_blocks),
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "실제 guard_block 표본이 0이면 분포 anchor만 사용한다.",
            "일일 변경폭은 +-10bps cap으로 본다.",
            "WAIT+score 통과+DANGER+1주 passive_probe와 timeout cancel은 같은 pre_submit_price_guard family에서 attribution한다.",
        ],
    }


def _build_entry_filter_refined_candidate_family(events: list[dict], stage: str, family_name: str, notes: list[str]) -> dict:
    blocked = _events_for_stage(events, stage)
    sample_ready = len(blocked) >= 20
    current = {"enabled": False, "mode": "report_only_design"}
    return {
        "family": family_name,
        "stage": "entry",
        "sample": {
            "blocked_events": len(blocked),
            "unique_codes": len({str(event.get("stock_code") or event.get("code") or "") for event in blocked}),
        },
        "apply_ready": False,
        "current": current,
        "recommended": {
            "enabled": False,
            "mode": "family_design_candidate" if sample_ready else "collect_evidence",
            "source_stage": stage,
        },
        "apply_mode": "report_only_calibration",
        "notes": notes,
    }


def _build_entry_ofi_ai_smoothing_family(events: list[dict]) -> dict:
    raw_skip = _events_for_stage(events, "entry_ai_price_canary_skip_order")
    demoted = _events_for_stage(events, "entry_ai_price_ofi_skip_demoted")
    followups = _events_for_stage(events, "entry_ai_price_canary_skip_followup")
    demoted_ids = _record_ids(demoted)
    snapshot_age_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("orderbook_micro_snapshot_age_ms"), None)
            for event in raw_skip + demoted
        )
        if value is not None
    ]
    followup_mfe = [
        value
        for value in (_safe_float(_event_fields(event).get("mfe_bps"), None) for event in followups)
        if value is not None
    ]
    followup_mae = [
        value
        for value in (_safe_float(_event_fields(event).get("mae_bps"), None) for event in followups)
        if value is not None
    ]
    sample_ready = (len(raw_skip) + len(demoted)) >= 20 and len(demoted) >= 5
    current = {
        "entry_skip_demotion_confidence_upper": int(
            getattr(TRADING_RULES, "SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE", 90) or 90
        ),
        "ofi_stale_threshold_ms": int(getattr(TRADING_RULES, "OFI_AI_SMOOTHING_STALE_THRESHOLD_MS", 700) or 700),
        "ofi_persistence_required": int(getattr(TRADING_RULES, "OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED", 2) or 2),
        "bucket_calibration_enabled": bool(
            getattr(TRADING_RULES, "SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED", False)
        ),
    }
    recommended = dict(current)
    return {
        "family": "entry_ofi_ai_smoothing",
        "stage": "entry",
        "sample": {
            "raw_skip": len(raw_skip),
            "demoted": len(demoted),
            "demoted_submitted": _record_id_stage_count(events, "order_bundle_submitted", demoted_ids),
            "demoted_fill": _record_id_stage_count(events, "position_rebased_after_fill", demoted_ids),
            "demoted_fill_quality": _record_id_stage_field_counter(
                events, "position_rebased_after_fill", demoted_ids, "fill_quality"
            ),
            "demoted_completed": _record_id_stage_count(events, "sell_completed", demoted_ids),
            "skip_followup": len(followups),
            "skip_followup_avg_mfe_bps": round(_avg(followup_mfe) or 0.0, 4) if followup_mfe else None,
            "skip_followup_avg_mae_bps": round(_avg(followup_mae) or 0.0, 4) if followup_mae else None,
            "snapshot_age_p90_ms": round(_percentile(snapshot_age_values, 90, 0.0), 3)
            if snapshot_age_values
            else None,
            "micro_state": _field_counter(raw_skip + demoted, "orderbook_micro_state"),
            "ofi_regime": _field_counter(demoted, "entry_ai_price_ofi_regime"),
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "manifest_only" if sample_ready else "observe_only",
        "notes": [
            "P2 raw SKIP 중 confidence 80~89와 stale/unhealthy/insufficient 제외 표본만 본다.",
            "추천값은 daily + rolling 방향 일치와 family sample floor가 맞을 때만 manifest 후보로 산출한다.",
            "ThresholdOpsTransition0506 전에는 report/manifest가 runtime env/code를 자동 변경하지 않는다.",
            "SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED 기본 OFF는 유지한다.",
        ],
    }


def _build_bad_entry_family(events: list[dict]) -> dict:
    current = {
        "min_hold_sec": int(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_MIN_HOLD_SEC", 60) or 60),
        "min_loss_pct": float(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_MIN_LOSS_PCT", -0.70) or -0.70),
        "max_peak_profit_pct": float(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_MAX_PEAK_PROFIT_PCT", 0.20) or 0.20),
        "ai_score_limit": int(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_AI_SCORE_LIMIT", 45) or 45),
    }
    observed = [event for event in events if str(event.get("stage") or "") == "bad_entry_block_observed"]
    refined_candidates = [
        event for event in events if str(event.get("stage") or "") == "bad_entry_refined_candidate"
    ]
    refined_exits = [event for event in events if str(event.get("stage") or "") == "bad_entry_refined_exit"]
    exclusion_counter = Counter(
        str((event.get("fields") or {}).get("exclusion_reason") or "-") for event in refined_candidates
    )
    soft_stop_zone_candidates = [
        event
        for event in refined_candidates
        if str((event.get("fields") or {}).get("exclusion_reason") or "") == "soft_stop_zone"
    ]
    early_capture_candidates = [
        event
        for event in refined_candidates
        if str((event.get("fields") or {}).get("exclusion_reason") or "") not in ("soft_stop_zone", "-")
        and str((event.get("fields") or {}).get("should_exit") or "").lower() == "true"
    ]
    hold_values = [_safe_float((event.get("fields") or {}).get("held_sec"), None) for event in observed]
    loss_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in observed]
    peak_values = [_safe_float((event.get("fields") or {}).get("peak_profit"), None) for event in observed]
    ai_values = [_safe_float((event.get("fields") or {}).get("ai_score"), None) for event in observed]
    hold_values = [v for v in hold_values if v is not None]
    loss_values = [v for v in loss_values if v is not None]
    peak_values = [v for v in peak_values if v is not None]
    ai_values = [v for v in ai_values if v is not None]
    sample_ready = len(observed) >= 30
    recommended = {
        "min_hold_sec": int(round(_clamp(_percentile(hold_values, 25, current["min_hold_sec"]), 30.0, 180.0))),
        "min_loss_pct": round(_clamp(_percentile(loss_values, 35, current["min_loss_pct"]), -1.5, -0.3), 2),
        "max_peak_profit_pct": round(_clamp(_percentile(peak_values, 75, current["max_peak_profit_pct"]), 0.05, 0.5), 2),
        "ai_score_limit": int(round(_clamp(_percentile(ai_values, 75, current["ai_score_limit"]), 30.0, 60.0))),
    }
    return {
        "family": "bad_entry_block",
        "stage": "holding_exit",
        "sample": {
            "observed": len(observed),
            "refined_candidate": len(refined_candidates),
            "refined_exit": len(refined_exits),
            "soft_stop_zone_candidate": len(soft_stop_zone_candidates),
            "early_capture_candidate": len(early_capture_candidates),
            "exclusion_top": dict(exclusion_counter.most_common(5)),
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "today live block은 열지 않고 observe->postclose->next_preopen 순서만 허용한다.",
            "후행 soft_stop/hard_stop 연결이 불충분하면 추천값은 report-only reference로 유지한다.",
            "soft_stop_zone_candidate는 refined canary가 이미 soft stop 영역에 들어간 뒤 제외한 표본이다.",
            "early_capture_candidate가 0이면 soft stop threshold보다 앞서 잡을 수 있었던 표본은 아직 확인되지 않은 것으로 본다.",
        ],
    }


def _build_bad_entry_refined_canary_family(events: list[dict], target_date: str | None = None) -> dict:
    current = {
        "enabled": bool(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED", False)),
        "min_hold_sec": int(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC", 180) or 180),
        "min_loss_pct": float(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT", -1.16) or -1.16),
        "max_peak_profit_pct": float(
            getattr(TRADING_RULES, "SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT", 0.05) or 0.05
        ),
        "ai_score_limit": int(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT", 45) or 45),
        "recovery_prob_max": float(
            getattr(TRADING_RULES, "SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX", 0.30) or 0.30
        ),
    }
    refined_candidates = _events_for_stage(events, "bad_entry_refined_candidate")
    refined_exits = _events_for_stage(events, "bad_entry_refined_exit")
    would_exit = [
        event
        for event in refined_candidates
        if str((event.get("fields") or {}).get("would_exit") or "").lower() == "true"
        or str((event.get("fields") or {}).get("should_exit") or "").lower() == "true"
    ]
    soft_stop_zone = [
        event
        for event in refined_candidates
        if str((event.get("fields") or {}).get("exclusion_reason") or "") == "soft_stop_zone"
    ]
    sell_order_failed = _stage_count(events, "sell_order_failed")
    sell_order_sent = _stage_count(events, "sell_order_sent")
    sell_completed = _stage_count(events, "sell_completed")
    lifecycle_attribution = _build_bad_entry_lifecycle_attribution(events, target_date)
    sample_ready = len(refined_candidates) >= 10 and sell_order_failed == 0
    recommended = dict(current)
    if sample_ready:
        recommended["enabled"] = True
    return {
        "family": "bad_entry_refined_canary",
        "stage": "holding_exit",
        "sample": {
            "refined_candidate": len(refined_candidates),
            "would_exit": len(would_exit),
            "refined_exit": len(refined_exits),
            "soft_stop_zone_candidate": len(soft_stop_zone),
            "sell_order_sent": sell_order_sent,
            "sell_completed": sell_completed,
            "sell_order_failed": sell_order_failed,
            "lifecycle_attribution": lifecycle_attribution,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "efficient_tradeoff_canary_candidate" if sample_ready else "observe_only",
        "notes": [
            "bad_entry_refined_candidate는 postclose post_sell outcome join 전까지 provisional signal이다.",
            "naive bad_entry hard block은 재개하지 않고 refined candidate만 bounded canary 후보로 본다.",
            "목표는 완벽한 loser classifier가 아니라 soft-stop tail/defer cost 감소다.",
            "GOOD_EXIT 감소가 허용 범위 안이면 rollback이 아니라 calibration으로 조정한다.",
        ],
    }


def _build_reversal_add_family(events: list[dict]) -> dict:
    current = {
        "pnl_min": float(getattr(TRADING_RULES, "REVERSAL_ADD_PNL_MIN", -0.70) or -0.70),
        "max_hold_sec": int(getattr(TRADING_RULES, "REVERSAL_ADD_MAX_HOLD_SEC", 180) or 180),
        "min_ai_score": int(getattr(TRADING_RULES, "REVERSAL_ADD_MIN_AI_SCORE", 60) or 60),
        "min_ai_recovery_delta": int(getattr(TRADING_RULES, "REVERSAL_ADD_MIN_AI_RECOVERY_DELTA", 15) or 15),
    }
    blocked = [event for event in events if str(event.get("stage") or "") == "reversal_add_blocked_reason"]
    candidates = [event for event in events if str(event.get("stage") or "") == "reversal_add_candidate"]
    reason_counter = Counter(
        str((event.get("fields") or {}).get("blocked_reason") or (event.get("fields") or {}).get("reason") or "-")
        for event in blocked
    )
    predicate_names = (
        "pnl_ok",
        "hold_ok",
        "low_floor_ok",
        "ai_score_ok",
        "ai_recover_ok",
        "supply_ok",
        "buy_pressure_ok",
        "tick_accel_ok",
        "large_sell_absent_ok",
        "micro_vwap_ok",
    )
    predicate_pass_counts = {
        name: sum(1 for event in blocked if str((event.get("fields") or {}).get(name) or "").lower() == "true")
        for name in predicate_names
    }
    all_but_hold = sum(
        1
        for event in blocked
        if str((event.get("fields") or {}).get("hold_ok") or "").lower() != "true"
        and all(
            str((event.get("fields") or {}).get(name) or "").lower() == "true"
            for name in predicate_names
            if name != "hold_ok"
        )
    )
    all_but_ai_recovery = sum(
        1
        for event in blocked
        if str((event.get("fields") or {}).get("ai_recover_ok") or "").lower() != "true"
        and all(
            str((event.get("fields") or {}).get(name) or "").lower() == "true"
            for name in predicate_names
            if name != "ai_recover_ok"
        )
    )
    pnl_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in blocked + candidates]
    hold_values = [_safe_float((event.get("fields") or {}).get("held_sec"), None) for event in blocked + candidates]
    ai_values = [_safe_float((event.get("fields") or {}).get("ai_score"), None) for event in blocked + candidates]
    recovery_values = [_safe_float((event.get("fields") or {}).get("ai_recovery_delta"), None) for event in blocked + candidates]
    pnl_values = [v for v in pnl_values if v is not None]
    hold_values = [v for v in hold_values if v is not None]
    ai_values = [v for v in ai_values if v is not None]
    recovery_values = [v for v in recovery_values if v is not None]
    sample_ready = len(candidates) >= 20
    recommended = {
        "pnl_min": round(_clamp(_percentile(pnl_values, 20, current["pnl_min"]), -1.3, -0.3), 2),
        "max_hold_sec": int(round(_clamp(_percentile(hold_values, 80, current["max_hold_sec"]), 120.0, 900.0))),
        "min_ai_score": int(round(_clamp(_percentile(ai_values, 30, current["min_ai_score"]), 45.0, 75.0))),
        "min_ai_recovery_delta": int(round(_clamp(_percentile(recovery_values, 30, current["min_ai_recovery_delta"]), 5.0, 30.0))),
    }
    return {
        "family": "reversal_add",
        "stage": "holding_exit",
        "sample": {
            "blocked": len(blocked),
            "candidate": len(candidates),
            "blocker_top": dict(reason_counter.most_common(5)),
            "predicate_pass_counts": predicate_pass_counts,
            "near_miss_all_but_hold": all_but_hold,
            "near_miss_all_but_ai_recovery": all_but_ai_recovery,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "first-fail 로그면 all-predicate 복원이 안 되므로 상한 추정치로만 본다.",
            f"주요 blocker={dict(reason_counter.most_common(3))}",
            "near_miss_all_but_*는 한 축만 열면 체결됐을 가능성이 있는 표본 수다. 0이면 복합조건 미충족으로 본다.",
        ],
    }


def _build_scalp_trailing_take_profit_family(events: list[dict]) -> dict:
    current = {
        "start_pct": float(getattr(TRADING_RULES, "SCALP_TRAILING_START_PCT", 0.6) or 0.6),
        "weak_limit": float(getattr(TRADING_RULES, "SCALP_TRAILING_LIMIT_WEAK", 0.4) or 0.4),
        "strong_limit": float(getattr(TRADING_RULES, "SCALP_TRAILING_LIMIT_STRONG", 0.8) or 0.8),
        "strong_ai_score": 75,
    }
    trailing_exits = [
        event
        for event in events
        if str(event.get("stage") or "") == "exit_signal"
        and str((event.get("fields") or {}).get("exit_rule") or "") == "scalp_trailing_take_profit"
    ]
    completed = [
        event
        for event in events
        if str(event.get("stage") or "") == "sell_completed"
        and str((event.get("fields") or {}).get("exit_rule") or "") == "scalp_trailing_take_profit"
    ]
    pyramid_signaled_ids = {
        event.get("record_id")
        for event in events
        if str(event.get("stage") or "") == "stat_action_decision_snapshot"
        and (
            str((event.get("fields") or {}).get("chosen_action") or "") == "pyramid_wait"
            or str((event.get("fields") or {}).get("scale_in_action_type") or "") == "PYRAMID"
        )
        and event.get("record_id") is not None
    }
    pyramid_executed_ids = {
        event.get("record_id")
        for event in events
        if str(event.get("stage") or "") in {"scale_in_executed", "scale_in_completed"}
        and event.get("record_id") is not None
    }
    drawdown_values: list[float] = []
    profit_values: list[float] = []
    ai_values: list[float] = []
    weak_borderline = 0
    would_hold_if_weak_plus_10bp = 0
    would_hold_if_strong_ai_relaxed_5pt = 0
    initial_only = 0
    pyramid_signaled_not_executed = 0
    pyramid_executed = 0
    borderline_examples: list[dict] = []
    strong_ai_boundary_examples: list[dict] = []
    for event in trailing_exits:
        fields = event.get("fields") or {}
        profit = _safe_float(fields.get("profit_rate"), None)
        peak = _safe_float(fields.get("peak_profit"), None)
        ai_score = _safe_float(fields.get("current_ai_score"), None)
        record_id = event.get("record_id")
        if record_id in pyramid_executed_ids:
            pyramid_executed += 1
            pyramid_state = "pyramid_executed"
        elif record_id in pyramid_signaled_ids:
            pyramid_signaled_not_executed += 1
            pyramid_state = "pyramid_signaled_not_executed"
        else:
            initial_only += 1
            pyramid_state = "initial_only"
        if profit is not None:
            profit_values.append(profit)
        if ai_score is not None:
            ai_values.append(ai_score)
        if profit is None or peak is None:
            continue
        drawdown = peak - profit
        drawdown_values.append(drawdown)
        limit = current["strong_limit"] if (ai_score or 0) >= current["strong_ai_score"] else current["weak_limit"]
        limit_bucket = "strong" if (ai_score or 0) >= current["strong_ai_score"] else "weak"
        if abs(drawdown - limit) <= 0.05:
            weak_borderline += 1
        if (ai_score or 0) < current["strong_ai_score"] and drawdown < current["weak_limit"] + 0.10:
            would_hold_if_weak_plus_10bp += 1
        strong_ai_boundary = (
            ai_score is not None
            and current["strong_ai_score"] - 5 <= ai_score < current["strong_ai_score"]
            and drawdown < current["strong_limit"]
        )
        if strong_ai_boundary:
            would_hold_if_strong_ai_relaxed_5pt += 1
        if abs(drawdown - limit) <= 0.10 and len(borderline_examples) < 8:
            borderline_examples.append(
                {
                    "emitted_at": event.get("emitted_at"),
                    "stock_code": event.get("stock_code"),
                    "stock_name": event.get("stock_name"),
                    "record_id": record_id,
                    "profit_rate": round(profit, 4),
                    "peak_profit": round(peak, 4),
                    "drawdown_from_peak": round(drawdown, 4),
                    "current_ai_score": round(ai_score, 2) if ai_score is not None else None,
                    "active_limit": round(limit, 4),
                    "limit_bucket": limit_bucket,
                    "pyramid_state": pyramid_state,
                    "would_hold_if_weak_limit_plus_10bp": bool(
                        (ai_score or 0) < current["strong_ai_score"]
                        and drawdown < current["weak_limit"] + 0.10
                    ),
                }
            )
        if strong_ai_boundary and len(strong_ai_boundary_examples) < 8:
            strong_ai_boundary_examples.append(
                {
                    "emitted_at": event.get("emitted_at"),
                    "stock_code": event.get("stock_code"),
                    "stock_name": event.get("stock_name"),
                    "record_id": record_id,
                    "profit_rate": round(profit, 4),
                    "peak_profit": round(peak, 4),
                    "drawdown_from_peak": round(drawdown, 4),
                    "current_ai_score": round(ai_score, 2),
                    "active_limit": round(limit, 4),
                    "strong_limit": round(current["strong_limit"], 4),
                    "pyramid_state": pyramid_state,
                }
            )
    completed_profit_values = [
        value
        for value in (_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in completed)
        if value is not None
    ]
    sample_ready = len(trailing_exits) >= 20
    recommended_weak = _clamp(_percentile(drawdown_values, 60, current["weak_limit"]), 0.4, 0.8)
    return {
        "family": "scalp_trailing_take_profit",
        "stage": "holding_exit",
        "sample": {
            "exit_signal": len(trailing_exits),
            "completed": len(completed),
            "avg_profit_rate_at_signal": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
            "avg_completed_profit_rate": round(_avg(completed_profit_values) or 0.0, 4)
            if completed_profit_values
            else None,
            "avg_drawdown_from_peak": round(_avg(drawdown_values) or 0.0, 4) if drawdown_values else None,
            "weak_borderline": weak_borderline,
            "would_hold_if_weak_limit_plus_10bp": would_hold_if_weak_plus_10bp,
            "would_hold_if_strong_ai_score_relaxed_5pt": would_hold_if_strong_ai_relaxed_5pt,
            "initial_only": initial_only,
            "pyramid_signaled_not_executed": pyramid_signaled_not_executed,
            "pyramid_executed": pyramid_executed,
            "borderline_examples": borderline_examples,
            "strong_ai_boundary_examples": strong_ai_boundary_examples,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": {
            "weak_limit": round(recommended_weak, 2),
            "strong_limit": current["strong_limit"],
        },
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "일반 트레일링 익절 민감도 표본이다. protect_trailing_smoothing과 합산하지 않는다.",
            "pyramid_signaled_not_executed는 불타기 조건은 열렸지만 실제 추가 체결 없이 일반 보유 수량으로 청산된 표본이다.",
            "weak_borderline은 현행 weak limit 근처에서 잘린 표본이며, missed-upside와 연결되기 전에는 live 변경 근거가 아니다.",
            "would_hold_if_weak_limit_plus_10bp는 +0.10%p 완화 시 같은 tick에서 청산되지 않았을 후보 수다.",
            "would_hold_if_strong_ai_score_relaxed_5pt는 AI strong 경계 5점 이내에서 strong limit를 적용했다면 같은 tick 청산이 보류됐을 후보 수다.",
        ],
    }


def _build_soft_stop_family(events: list[dict]) -> dict:
    current = {
        "grace_sec": int(getattr(TRADING_RULES, "SCALP_SOFT_STOP_MICRO_GRACE_SEC", 20) or 20),
        "emergency_pct": float(getattr(TRADING_RULES, "SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT", -2.0) or -2.0),
    }
    touches = [event for event in events if str(event.get("stage") or "") == "soft_stop_micro_grace"]
    profit_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in touches]
    hold_values = [_safe_float((event.get("fields") or {}).get("held_sec"), None) for event in touches]
    profit_values = [v for v in profit_values if v is not None]
    hold_values = [v for v in hold_values if v is not None]
    sample_ready = len(touches) >= 30
    recommended = {
        "grace_sec": int(round(_clamp(_percentile(hold_values, 25, current["grace_sec"]), 10.0, 60.0))),
        "emergency_pct": round(_clamp(_percentile(profit_values, 10, current["emergency_pct"]), -2.5, -1.5), 2),
    }
    return {
        "family": "soft_stop_micro_grace",
        "stage": "holding_exit",
        "sample": {"touches": len(touches)},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "rebound/missed-upside 연결이 없으면 grace_sec 추천은 direction-only로 본다.",
            "holding_exit stage는 same-day 다른 live owner와 동시 적용 금지다.",
        ],
    }


def _build_soft_stop_whipsaw_confirmation_family(events: list[dict]) -> dict:
    current = {
        "enabled": bool(getattr(TRADING_RULES, "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED", False)),
        "confirm_sec": int(getattr(TRADING_RULES, "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC", 60) or 60),
        "buffer_pct": float(getattr(TRADING_RULES, "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT", 0.20) or 0.20),
        "max_worsen_pct": float(
            getattr(TRADING_RULES, "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT", 0.30) or 0.30
        ),
    }
    grace_touches = _events_for_stage(events, "soft_stop_micro_grace")
    confirmations = _events_for_stage(events, "soft_stop_whipsaw_confirmation")
    expired = _events_for_stage(events, "soft_stop_whipsaw_confirmation_expired")
    soft_stop_completed = [
        event
        for event in events
        if str(event.get("stage") or "") == "sell_completed"
        and str(_event_fields(event).get("exit_rule") or "") == "scalp_soft_stop_pct"
    ]
    confirmation_elapsed_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("confirmation_elapsed_sec"), None)
            for event in confirmations + expired
        )
        if value is not None
    ]
    worsen_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("additional_worsen"), None)
            for event in confirmations + expired
        )
        if value is not None
    ]
    completed_profit_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("profit_rate"), None)
            for event in soft_stop_completed
        )
        if value is not None
    ]
    sample_floor = int(CALIBRATION_FAMILY_METADATA["soft_stop_whipsaw_confirmation"]["sample_floor"])
    sample_ready = len(grace_touches) >= sample_floor
    recommended_confirm_sec = int(round(_clamp(_percentile(confirmation_elapsed_values, 75, 60.0), 20.0, 120.0)))
    recommended_max_worsen = round(_clamp(_percentile(worsen_values, 75, current["max_worsen_pct"]), 0.10, 0.60), 2)
    return {
        "family": "soft_stop_whipsaw_confirmation",
        "stage": "holding_exit",
        "sample": {
            "soft_stop_micro_grace": len(grace_touches),
            "confirmation_started": len(confirmations),
            "confirmation_expired": len(expired),
            "soft_stop_completed": len(soft_stop_completed),
            "completed_avg_profit_rate": round(_avg(completed_profit_values) or 0.0, 4)
            if completed_profit_values
            else None,
            "avg_confirmation_elapsed_sec": round(_avg(confirmation_elapsed_values) or 0.0, 2)
            if confirmation_elapsed_values
            else None,
            "avg_additional_worsen": round(_avg(worsen_values) or 0.0, 4) if worsen_values else None,
            "sample_floor": sample_floor,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": {
            "enabled": True,
            "confirm_sec": recommended_confirm_sec,
            "buffer_pct": current["buffer_pct"],
            "max_worsen_pct": recommended_max_worsen,
        },
        "apply_mode": "calibrated_apply_candidate" if sample_ready else "observe_only",
        "notes": [
            "첫 live calibration family 후보이며 장중 자동 mutation 없이 다음 장전 1회 적용 단위로만 다룬다.",
            "조건 미달은 rollback이 아니라 calibration trigger로 기록한다.",
            "hard/protect/emergency stop, 주문 실패, provenance 손상, same-stage owner 충돌은 safety guard로 우선한다.",
            "GOOD_EXIT 훼손은 +10%p까지 허용하고 soft-stop tail 또는 MISSED_UPSIDE 감소가 있으면 완만 조정/유지 대상이다.",
        ],
    }


def _build_protect_trailing_smoothing_family(events: list[dict]) -> dict:
    current = {
        "window_sec": int(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC", 20) or 20),
        "min_span_sec": int(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC", 8) or 8),
        "min_samples": int(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES", 3) or 3),
        "below_ratio": float(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO", 0.67) or 0.67),
        "buffer_pct": float(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT", 1.0) or 1.0),
        "emergency_pct": float(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_EMERGENCY_PCT", -2.0) or -2.0),
    }
    holds = [event for event in events if str(event.get("stage") or "") == "protect_trailing_smooth_hold"]
    confirmed = [event for event in events if str(event.get("stage") or "") == "protect_trailing_smooth_confirmed"]
    completed = [
        event
        for event in events
        if str(event.get("stage") or "") == "sell_completed"
        and str((event.get("fields") or {}).get("exit_rule") or "") == "protect_trailing_stop"
    ]
    candidate_events = holds + confirmed
    span_values = [_safe_float((event.get("fields") or {}).get("sample_span_sec"), None) for event in candidate_events]
    sample_values = [_safe_float((event.get("fields") or {}).get("sample_count"), None) for event in candidate_events]
    below_values = [_safe_float((event.get("fields") or {}).get("below_ratio"), None) for event in candidate_events]
    buffer_values = [_safe_float((event.get("fields") or {}).get("buffer_pct"), None) for event in candidate_events]
    emergency_values = [_safe_float((event.get("fields") or {}).get("emergency_pct"), None) for event in candidate_events]
    profit_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in completed]
    span_values = [v for v in span_values if v is not None]
    sample_values = [v for v in sample_values if v is not None]
    below_values = [v for v in below_values if v is not None]
    buffer_values = [v for v in buffer_values if v is not None]
    emergency_values = [v for v in emergency_values if v is not None]
    profit_values = [v for v in profit_values if v is not None]
    sample_ready = len(candidate_events) >= 20 and (len(confirmed) + len(holds)) >= 20
    recommended = {
        "window_sec": int(round(_clamp(_percentile(span_values, 90, current["window_sec"]), 10.0, 45.0))),
        "min_span_sec": int(round(_clamp(_percentile(span_values, 50, current["min_span_sec"]), 5.0, 20.0))),
        "min_samples": int(round(_clamp(_percentile(sample_values, 50, current["min_samples"]), 3.0, 8.0))),
        "below_ratio": round(_clamp(_percentile(below_values, 75, current["below_ratio"]), 0.50, 0.90), 2),
        "buffer_pct": round(_clamp(_percentile(buffer_values, 50, current["buffer_pct"]), 0.50, 1.50), 2),
        "emergency_pct": round(_clamp(_percentile(emergency_values, 10, current["emergency_pct"]), -2.5, -1.5), 2),
    }
    return {
        "family": "protect_trailing_smoothing",
        "stage": "holding_exit",
        "sample": {
            "smooth_hold": len(holds),
            "smooth_confirmed": len(confirmed),
            "protect_trailing_completed": len(completed),
            "completed_avg_profit_rate": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "protect_trailing smoothing 값은 장중 자동 변경하지 않고 장후 report와 다음 장전 manifest 후보로만 산출한다.",
            "protect_hard_stop과 emergency_pct 이탈은 평탄화 대상이 아니므로 별도 safety로 유지한다.",
            "sample floor 미달이면 추천값은 direction-only이며 리노공업 단일 케이스로 live 재조정하지 않는다.",
        ],
    }


def _build_holding_flow_ofi_smoothing_family(events: list[dict]) -> dict:
    applied = _events_for_stage(events, "holding_flow_ofi_smoothing_applied")
    force_exit = _events_for_stage(events, "holding_flow_override_force_exit")
    debounced = [
        event for event in applied if str(_event_fields(event).get("smoothing_action") or "") == "DEBOUNCE_EXIT"
    ]
    confirmed = [
        event for event in applied if str(_event_fields(event).get("smoothing_action") or "") == "CONFIRM_EXIT"
    ]
    applied_ids = _record_ids(applied)
    worsen_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("worsen_from_candidate"), None)
            for event in applied
        )
        if value is not None
    ]
    completed_profit_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("profit_rate"), None)
            for event in events
            if str(event.get("stage") or "") == "sell_completed" and event.get("record_id") in applied_ids
        )
        if value is not None
    ]
    sample_ready = len(applied) >= 20 and len(debounced) >= 5 and len(confirmed) >= 5
    current = {
        "ofi_stale_threshold_ms": int(getattr(TRADING_RULES, "OFI_AI_SMOOTHING_STALE_THRESHOLD_MS", 700) or 700),
        "ofi_persistence_required": int(getattr(TRADING_RULES, "OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED", 2) or 2),
        "holding_bearish_confirm_worsen_pct": float(
            getattr(TRADING_RULES, "HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT", 0.30) or 0.30
        ),
        "max_defer_sec": int(getattr(TRADING_RULES, "HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC", 90) or 90),
        "worsen_floor_pct": float(getattr(TRADING_RULES, "HOLDING_FLOW_OVERRIDE_WORSEN_PCT", 0.80) or 0.80),
    }
    recommended = dict(current)
    return {
        "family": "holding_flow_ofi_smoothing",
        "stage": "holding_exit",
        "sample": {
            "applied": len(applied),
            "exit_debounce": len(debounced),
            "bearish_confirm": len(confirmed),
            "force_exit_priority": len(force_exit),
            "force_exit_reason": _field_counter(force_exit, "force_reason"),
            "avg_worsen_from_candidate": round(_avg(worsen_values) or 0.0, 4) if worsen_values else None,
            "smoothing_action": _field_counter(applied, "smoothing_action"),
            "ofi_regime": _field_counter(applied, "holding_flow_ofi_regime"),
            "micro_state": _field_counter(applied, "orderbook_micro_state"),
            "completed_valid": len(completed_profit_values),
            "completed_avg_profit_rate": round(_avg(completed_profit_values) or 0.0, 4)
            if completed_profit_values
            else None,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "manifest_only" if sample_ready else "observe_only",
        "notes": [
            "hard/protect/order safety, max_defer_sec, worsen_floor는 OFI보다 우선한다.",
            "GOOD_EXIT/MISSED_UPSIDE 판정은 sell_completed + valid profit_rate 연결 표본으로만 사후 확인한다.",
            "추천값은 daily + rolling 방향 일치와 family sample floor가 맞을 때만 manifest 후보로 산출한다.",
            "ThresholdOpsTransition0506 전에는 runtime threshold mutation을 열지 않는다.",
        ],
    }


def _build_scale_in_price_guard_family(events: list[dict]) -> dict:
    resolved = _events_for_stage(events, "scale_in_price_resolved")
    blocked = _events_for_stage(events, "scale_in_price_guard_block")
    p2_observe = _events_for_stage(events, "scale_in_price_p2_observe")
    resolved_ids = _record_ids(resolved)

    guard_events = resolved + blocked
    spread_values = [
        value
        for value in (_safe_float(_event_fields(event).get("spread_bps"), None) for event in guard_events)
        if value is not None
    ]
    micro_vwap_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("micro_vwap_bps"), None)
            for event in guard_events
        )
        if value is not None
    ]
    curr_distance_values = [
        value
        for value in (
            _safe_float(
                _event_fields(event).get("resolved_vs_curr_bps")
                or _event_fields(event).get("resolved_price_vs_curr_bps"),
                None,
            )
            for event in resolved
        )
        if value is not None
    ]
    effective_qty_values = [
        value
        for value in (
            _safe_float(_event_fields(event).get("effective_qty"), None)
            for event in resolved
        )
        if value is not None
    ]
    sample_ready = len(guard_events) >= 20 and (len(blocked) >= 5 or len(resolved) >= 5)
    current = {
        "max_spread_bps": float(getattr(TRADING_RULES, "SCALPING_SCALE_IN_MAX_SPREAD_BPS", 80.0) or 80.0),
        "pyramid_max_micro_vwap_bps": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS", 60.0) or 60.0
        ),
        "pyramid_min_ai_score": int(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_AI_SCORE", 70) or 70),
        "pyramid_min_buy_pressure": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_BUY_PRESSURE", 60.0) or 60.0
        ),
        "pyramid_min_tick_accel": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_TICK_ACCEL", 0.5) or 0.5
        ),
        "effective_qty_cap": int(getattr(TRADING_RULES, "SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP", 0) or 0),
    }
    recommended = dict(current)
    if spread_values:
        recommended["max_spread_bps_observed_p90"] = round(_percentile(spread_values, 90, current["max_spread_bps"]), 2)
    if micro_vwap_values:
        recommended["micro_vwap_bps_observed_p90"] = round(
            _percentile(micro_vwap_values, 90, current["pyramid_max_micro_vwap_bps"]),
            2,
        )
    return {
        "family": "scale_in_price_guard",
        "stage": "holding_exit",
        "sample": {
            "resolved": len(resolved),
            "guard_block": len(blocked),
            "p2_observe": len(p2_observe),
            "resolved_executed": _record_id_stage_count(events, "scale_in_executed", resolved_ids),
            "resolved_completed": _record_id_stage_count(events, "sell_completed", resolved_ids),
            "add_type": _field_counter(guard_events + p2_observe, "add_type"),
            "block_reason": _field_counter(blocked, "reason"),
            "qty_reason": _field_counter(resolved, "qty_reason"),
            "p2_action": _field_counter(p2_observe, "action"),
            "spread_bps_p90": round(_percentile(spread_values, 90, 0.0), 3) if spread_values else None,
            "micro_vwap_bps_p90": round(_percentile(micro_vwap_values, 90, 0.0), 3)
            if micro_vwap_values
            else None,
            "resolved_vs_curr_bps_avg": round(_avg(curr_distance_values) or 0.0, 4)
            if curr_distance_values
            else None,
            "effective_qty_avg": round(_avg(effective_qty_values) or 0.0, 4)
            if effective_qty_values
            else None,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "manifest_only" if sample_ready else "observe_only",
        "notes": [
            "REVERSAL_ADD/PYRAMID 주문 직전 가격·수량 safety threshold 표본이다.",
            "P1 resolver와 dynamic qty는 이미 live replacement지만 threshold-cycle은 추천값/분포를 report-only로만 남긴다.",
            "P2 scale_in_price_v1은 observe-only이며 action이 SKIP이어도 live 주문가/주문 여부를 바꾸지 않는다.",
            "ThresholdOpsTransition0506 전에는 runtime threshold mutation을 열지 않는다.",
        ],
    }


def _action_label_for_completed_row(row: dict) -> str:
    last_add_type = str(row.get("last_add_type") or "").strip().upper()
    avg_down_count = _safe_int(row.get("avg_down_count"), 0) or 0
    pyramid_count = _safe_int(row.get("pyramid_count"), 0) or 0
    if avg_down_count > 0 or last_add_type == "AVG_DOWN":
        return "avg_down_wait"
    if pyramid_count > 0 or last_add_type == "PYRAMID":
        return "pyramid_wait"
    return "exit_only"


def _summarize_action_rows(rows: list[dict]) -> dict:
    profit_values = [_safe_float(row.get("profit_rate"), None) for row in rows]
    profit_values = [value for value in profit_values if value is not None]
    if not profit_values:
        return {
            "sample": len(rows),
            "avg_profit_rate": None,
            "median_profit_rate": None,
            "downside_p10_profit_rate": None,
            "stddev_profit_rate": None,
            "win_rate": None,
            "loss_rate": None,
        }
    wins = [value for value in profit_values if value > 0]
    losses = [value for value in profit_values if value < 0]
    return {
        "sample": len(profit_values),
        "avg_profit_rate": round(_avg(profit_values) or 0.0, 4),
        "median_profit_rate": round(_percentile(profit_values, 50, 0.0), 4),
        "downside_p10_profit_rate": round(_percentile(profit_values, 10, 0.0), 4),
        "stddev_profit_rate": round(_stddev(profit_values) or 0.0, 4),
        "win_rate": round(len(wins) / len(profit_values), 4),
        "loss_rate": round(len(losses) / len(profit_values), 4),
    }


def _confidence_adjusted_action_score(summary: dict, prior_summary: dict, *, prior_strength: int = 8) -> dict:
    sample = int(summary.get("sample") or 0)
    avg_profit = _safe_float(summary.get("avg_profit_rate"), None)
    prior_avg = _safe_float(prior_summary.get("avg_profit_rate"), 0.0) or 0.0
    if sample <= 0 or avg_profit is None:
        return {
            "empirical_bayes_profit_rate": None,
            "uncertainty_penalty": None,
            "confidence_adjusted_score": None,
            "weight": 0.0,
        }
    smoothed = ((avg_profit * sample) + (prior_avg * prior_strength)) / (sample + prior_strength)
    stddev = _safe_float(summary.get("stddev_profit_rate"), None)
    if stddev is None or stddev <= 0:
        stddev = abs(avg_profit - prior_avg) or 0.5
    uncertainty_penalty = stddev / math.sqrt(sample)
    score = smoothed - uncertainty_penalty
    weight = _clamp((score + 1.0) / 2.0, 0.0, 1.0)
    return {
        "empirical_bayes_profit_rate": round(smoothed, 4),
        "uncertainty_penalty": round(uncertainty_penalty, 4),
        "confidence_adjusted_score": round(score, 4),
        "weight": round(weight, 4),
    }


def _best_action_by_bucket(rows: list[dict], bucket_field: str, *, min_sample: int = 5) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((str(row.get(bucket_field) or "unknown"), str(row.get("action_label") or "exit_only")), []).append(row)

    global_rows_by_action = {
        action: [row for row in rows if str(row.get("action_label") or "exit_only") == action]
        for action in ("exit_only", "avg_down_wait", "pyramid_wait")
    }
    global_summary_by_action = {
        action: _summarize_action_rows(action_rows)
        for action, action_rows in global_rows_by_action.items()
    }
    buckets = sorted({bucket for bucket, _ in grouped})
    recommendations: list[dict] = []
    for bucket in buckets:
        action_summaries = []
        for action in ("exit_only", "avg_down_wait", "pyramid_wait"):
            summary = _summarize_action_rows(grouped.get((bucket, action), []))
            score_pack = _confidence_adjusted_action_score(summary, global_summary_by_action[action])
            action_summaries.append({"action": action, **summary, **score_pack})
        eligible = [
            item for item in action_summaries
            if item["sample"] >= min_sample and item["confidence_adjusted_score"] is not None
        ]
        ranked = sorted(eligible, key=lambda item: item["confidence_adjusted_score"], reverse=True)
        best = ranked[0] if ranked else None
        runner_up = ranked[1] if len(ranked) > 1 else None
        margin = (
            round(best["confidence_adjusted_score"] - runner_up["confidence_adjusted_score"], 4)
            if best and runner_up
            else None
        )
        if not best:
            policy_hint = "insufficient_sample"
        elif best["loss_rate"] is not None and best["loss_rate"] >= 0.65:
            policy_hint = "defensive_only_high_loss_rate"
        elif margin is not None and margin < 0.15:
            policy_hint = "no_clear_edge"
        else:
            policy_hint = "candidate_weight_source"
        recommendations.append(
            {
                "bucket": bucket,
                "best_action": best["action"] if best else "insufficient_sample",
                "best_avg_profit_rate": best["avg_profit_rate"] if best else None,
                "best_confidence_adjusted_score": best["confidence_adjusted_score"] if best else None,
                "edge_margin": margin,
                "policy_hint": policy_hint,
                "actions": action_summaries,
            }
        )
    return recommendations


def _build_statistical_action_weight_family(
    events: list[dict],
    completed_rows: list[dict],
    *,
    target_date: str | None = None,
) -> dict:
    completed_valid: list[dict] = []
    for row in completed_rows:
        profit_rate = _safe_float(row.get("profit_rate"), None)
        if profit_rate is None:
            continue
        enriched = dict(row)
        enriched["action_label"] = _action_label_for_completed_row(row)
        enriched["price_bucket"] = _price_bucket(row.get("buy_price"))
        enriched["volume_bucket"] = _volume_bucket(
            row.get("daily_volume")
            or row.get("volume")
            or row.get("acc_volume")
            or row.get("trade_volume")
        )
        enriched["time_bucket"] = _time_bucket(row.get("buy_time") or row.get("sell_time"))
        completed_valid.append(enriched)

    action_counts = Counter(row["action_label"] for row in completed_valid)
    action_summary = {
        action: _summarize_action_rows([row for row in completed_valid if row["action_label"] == action])
        for action in ("exit_only", "avg_down_wait", "pyramid_wait")
    }
    known_price = sum(1 for row in completed_valid if row["price_bucket"] != "price_unknown")
    known_volume = sum(1 for row in completed_valid if row["volume_bucket"] != "volume_unknown")
    known_time = sum(1 for row in completed_valid if row["time_bucket"] != "time_unknown")
    event_counts = Counter(str(event.get("stage") or "") for event in events)
    sample_ready = (
        len(completed_valid) >= 50
        and known_price >= 30
        and known_time >= 30
        and (action_counts.get("avg_down_wait", 0) + action_counts.get("pyramid_wait", 0)) >= 10
    )
    return {
        "family": "statistical_action_weight",
        "stage": "decision_support",
        "sample": {
            "completed_valid": len(completed_valid),
            "exit_only": action_counts.get("exit_only", 0),
            "avg_down_wait": action_counts.get("avg_down_wait", 0),
            "pyramid_wait": action_counts.get("pyramid_wait", 0),
            "compact_exit_signal": event_counts.get("exit_signal", 0),
            "compact_sell_completed": event_counts.get("sell_completed", 0),
            "compact_scale_in_executed": event_counts.get("scale_in_executed", 0),
            "compact_decision_snapshot": event_counts.get("stat_action_decision_snapshot", 0),
        },
        "apply_ready": False,
        "weight_source_ready": sample_ready,
        "current": {
            "mode": "report_only",
            "live_runtime_mutation": False,
            "bucket_axes": ["price_bucket", "volume_bucket", "time_bucket"],
            "score_method": "empirical_bayes_lower_confidence_bound",
        },
        "recommended": {
            "action_summary": action_summary,
            "by_price_bucket": _best_action_by_bucket(completed_valid, "price_bucket"),
            "by_volume_bucket": _best_action_by_bucket(completed_valid, "volume_bucket"),
            "by_time_bucket": _best_action_by_bucket(completed_valid, "time_bucket"),
            "data_completeness": {
                "price_known": known_price,
                "volume_known": known_volume,
                "time_known": known_time,
            },
            "weight_governor": {
                "min_bucket_action_sample": 5,
                "prior_strength": 8,
                "clear_edge_margin": 0.15,
                "high_loss_rate_guard": 0.65,
            },
            "eligible_but_not_chosen": _build_eligible_but_not_chosen_report(events, target_date),
        },
        "apply_mode": "report_only_weight_source",
        "notes": [
            "가격대/거래량/시간대별 exit_only vs avg_down_wait vs pyramid_wait 통계 축이다.",
            "작은 표본은 action별 전체 prior로 shrinkage하고 불확실성 penalty를 뺀 confidence-adjusted score로만 비교한다.",
            "live 청산/추가매수 판단에는 직접 적용하지 않고 장후 threshold weight 입력으로만 사용한다.",
            "거래량 표본이 부족하면 volume_bucket 결론은 금지하고 price/time bucket만 direction-only로 본다.",
        ],
    }


def _build_family_reports(
    events: list[dict],
    completed_rows: list[dict] | None = None,
    *,
    target_date: str | None = None,
) -> list[dict]:
    completed_rows = completed_rows or []
    return [
        _build_mechanical_entry_family(events),
        _build_score65_74_recovery_probe_family(events),
        _build_pre_submit_guard_family(events),
        _build_entry_filter_refined_candidate_family(
            events,
            "blocked_strength_momentum",
            "strength_momentum_soft_gate_p1",
            [
                "strength/momentum 미달은 AI 전 terminal block이 아니라 risk context 후보로 관리한다.",
                "insufficient/stale/extreme sell source-quality block은 유지하고, live apply는 approval artifact 전까지 금지한다.",
            ],
        ),
        _build_entry_filter_refined_candidate_family(
            events,
            "blocked_overbought",
            "overbought_pullback_guard_p1",
            [
                "overbought 후보는 AI/counterfactual까지 열고, 실주문은 pullback/rebreak pre-submit guard로만 허용한다.",
                "broad overbought 완화가 아니며 approval artifact와 rollback guard 전까지 자동 runtime apply는 금지한다.",
            ],
        ),
        _build_entry_filter_refined_candidate_family(
            events,
            "blocked_liquidity",
            "liquidity_pre_submit_guard_p1",
            [
                "liquidity 미달은 AI 전 후보 폐기가 아니라 broker submit 직전 hard safety guard로 재배치한다.",
                "저유동성 후보는 actual_order_submitted=false virtual-only attribution으로만 본다.",
            ],
        ),
        _build_entry_ofi_ai_smoothing_family(events),
        _build_bad_entry_family(events),
        _build_bad_entry_refined_canary_family(events, target_date=target_date),
        _build_reversal_add_family(events),
        _build_soft_stop_family(events),
        _build_soft_stop_whipsaw_confirmation_family(events),
        _build_scalp_trailing_take_profit_family(events),
        _build_protect_trailing_smoothing_family(events),
        _build_holding_flow_ofi_smoothing_family(events),
        _build_scale_in_price_guard_family(events),
        _build_position_sizing_cap_release_family(events, completed_rows),
        _build_position_sizing_dynamic_formula_family(events, completed_rows),
        _build_statistical_action_weight_family(events, completed_rows, target_date=target_date),
        _build_lifecycle_decision_matrix_runtime_family(target_date),
    ]


def _build_report_source_families(report_source_context: dict | None) -> list[dict]:
    metrics = (report_source_context or {}).get("source_metrics")
    metrics = metrics if isinstance(metrics, dict) else {}
    decision_support = metrics.get("decision_support") if isinstance(metrics.get("decision_support"), dict) else {}
    market_regime = (
        metrics.get("market_regime_continuous") if isinstance(metrics.get("market_regime_continuous"), dict) else {}
    )
    market_source_quality = (
        market_regime.get("source_quality") if isinstance(market_regime.get("source_quality"), dict) else {}
    )
    market_rolling_10d = (
        market_regime.get("rolling_10d") if isinstance(market_regime.get("rolling_10d"), dict) else {}
    )
    market_valid_days = max(
        _safe_int(market_source_quality.get("valid_market_regime_days"), 0) or 0,
        _safe_int(market_rolling_10d.get("valid_market_regime_days"), 0) or 0,
    )
    matrix_entries = _safe_int(decision_support.get("matrix_entries"), 0) or 0
    non_clear_edge = _safe_int(decision_support.get("matrix_non_clear_edge"), 0) or 0
    candidate_weight_source = _safe_int(decision_support.get("saw_candidate_weight_source"), 0) or 0
    sample_ready = non_clear_edge > 0 and candidate_weight_source > 0
    return [
        {
            "family": "holding_exit_decision_matrix_advisory",
            "stage": "decision_support",
            "sample": {
                "matrix_entries": matrix_entries,
                "matrix_non_clear_edge": non_clear_edge,
                "matrix_no_clear_edge": _safe_int(decision_support.get("matrix_no_clear_edge"), 0) or 0,
                "saw_candidate_weight_source": candidate_weight_source,
                "saw_defensive_only_high_loss_rate": _safe_int(
                    decision_support.get("saw_defensive_only_high_loss_rate"), 0
                )
                or 0,
                "saw_insufficient_sample": _safe_int(decision_support.get("saw_insufficient_sample"), 0) or 0,
                "counterfactual_entry_count": _safe_int(decision_support.get("counterfactual_entry_count"), 0) or 0,
                "counterfactual_ready_count": _safe_int(decision_support.get("counterfactual_ready_count"), 0) or 0,
                "counterfactual_gap_count": _safe_int(decision_support.get("counterfactual_gap_count"), 0) or 0,
                "counterfactual_per_action_samples": (
                    decision_support.get("counterfactual_per_action_samples")
                    if isinstance(decision_support.get("counterfactual_per_action_samples"), dict)
                    else {}
                ),
            },
            "apply_ready": sample_ready,
            "current": {
                "enabled": False,
                "mode": "advisory_flag_off",
                "matrix_version": decision_support.get("matrix_version"),
            },
            "recommended": {
                "enabled": sample_ready,
                "mode": "advisory_canary_live_readiness" if sample_ready else "readiness_only",
                "matrix_version": decision_support.get("matrix_version"),
                "candidate_bucket_count": non_clear_edge,
            },
            "apply_mode": "efficient_tradeoff_canary_candidate" if sample_ready else "report_only_readiness",
            "notes": [
                "ADM은 shadow가 아니라 advisory canary/live-readiness 축으로만 본다.",
                "recommended_bias가 전부 no_clear_edge이면 최소 edge 부재라 live AI 응답은 바꾸지 않는다.",
                "SAW candidate_weight_source bucket만 matrix bias 후보로 연결한다.",
            ],
        },
        {
            "family": "market_regime_continuous_score",
            "stage": "risk_context",
            "sample": {
                "valid_market_regime_days": market_valid_days,
                "rolling_5d": market_regime.get("rolling_5d") if isinstance(market_regime.get("rolling_5d"), dict) else {},
                "rolling_10d": market_rolling_10d,
                "label_ev_breakdown": (
                    market_regime.get("label_ev_breakdown")
                    if isinstance(market_regime.get("label_ev_breakdown"), dict)
                    else {}
                ),
                "source_quality_status": market_source_quality.get("status") or "hold_sample",
            },
            "apply_ready": False,
            "current": {
                "enabled": False,
                "risk_on_min_score": 65,
                "neutral_min_score": 45,
                "oil_relief_max_weight": 10,
                "breadth_max_weight": 35,
            },
            "recommended": {
                "enabled": False,
                "risk_on_min_score": 65,
                "neutral_min_score": 45,
                "oil_relief_max_weight": 10,
                "breadth_max_weight": 35,
            },
            "apply_mode": "manifest_only_context_source",
            "notes": [
                "market regime continuous score는 ADM/LDM risk_context feature이며 1차 개발에서는 runtime action authority가 없다.",
                "label threshold 조정 family는 manifest-only로 생성하고 allowed_runtime_apply=false를 유지한다.",
            ],
        },
    ]


def _build_lifecycle_decision_matrix_runtime_family(target_date: str | None) -> dict:
    target = str(target_date or date.today().isoformat())
    path = LIFECYCLE_DECISION_MATRIX_DIR / f"lifecycle_decision_matrix_{target}.json"
    context_path = REPORT_DIR / "lifecycle_ai_context" / f"lifecycle_ai_context_{target}.json"
    context_payload = _read_json_dict(context_path)
    payload = _read_json_dict(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    policy_entries = payload.get("policy_entries") if isinstance(payload.get("policy_entries"), list) else []
    total_rows = _safe_int(summary.get("total_rows"), 0) or 0
    joined_rows = _safe_int(summary.get("joined_rows"), 0) or 0
    policy_pass_count = _safe_int(summary.get("policy_pass_count"), 0) or 0
    promote_ready_count = _safe_int(summary.get("promote_ready_count"), 0) or 0
    matrix_version = str(payload.get("matrix_version") or "")
    apply_ready = bool(payload) and total_rows >= 20 and joined_rows >= 10 and policy_pass_count > 0
    return {
        "family": "lifecycle_decision_matrix_runtime",
        "stage": "lifecycle",
        "sample": {
            "total_rows": total_rows,
            "joined_rows": joined_rows,
            "policy_pass_count": policy_pass_count,
            "promote_ready_count": promote_ready_count,
            "policy_entry_count": len([item for item in policy_entries if isinstance(item, dict)]),
        },
        "apply_ready": apply_ready,
        "current": {
            "enabled": False,
            "policy_file": "",
            "policy_version": "",
            "promote_enabled": False,
            "max_promotes_per_day": 3,
            "min_stage_confidence": 0.60,
            "runtime_effect_enabled": bool(
                getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED", False)
            ),
            "lifecycle_ai_context_enabled": bool(getattr(TRADING_RULES, "LIFECYCLE_AI_CONTEXT_ENABLED", False)),
            "lifecycle_ai_context_file": str(getattr(TRADING_RULES, "LIFECYCLE_AI_CONTEXT_FILE", "") or ""),
            "lifecycle_ai_context_version": str(
                getattr(TRADING_RULES, "LIFECYCLE_AI_CONTEXT_VERSION", "") or ""
            ),
            "entry_adm_advisory_enabled": bool(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_ADVISORY_ENABLED", True)),
            "entry_adm_runtime_bias_enabled": bool(
                getattr(TRADING_RULES, "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED", False)
            ),
            "holding_exit_matrix_advisory_enabled": bool(
                getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED", True)
            ),
            "holding_exit_matrix_runtime_bias_enabled": bool(
                getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False)
            ),
            "holding_exit_matrix_scale_in_bias_enabled": bool(
                getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED", False)
            ),
        },
        "recommended": {
            "enabled": apply_ready,
            "policy_file": str(path) if path.exists() else "",
            "policy_version": matrix_version,
            "promote_enabled": bool(promote_ready_count > 0),
            "max_promotes_per_day": 3,
            "min_stage_confidence": 0.60,
            "runtime_effect_enabled": False,
            "lifecycle_ai_context_enabled": bool(context_payload),
            "lifecycle_ai_context_file": str(context_path) if context_path.exists() else "",
            "lifecycle_ai_context_version": str(context_payload.get("context_version") or ""),
            "entry_adm_advisory_enabled": True,
            "entry_adm_runtime_bias_enabled": False,
            "holding_exit_matrix_advisory_enabled": True,
            "holding_exit_matrix_runtime_bias_enabled": False,
            "holding_exit_matrix_scale_in_bias_enabled": False,
        },
        "apply_mode": "efficient_tradeoff_canary_candidate" if apply_ready else "report_only_calibration",
        "notes": [
            "umbrella family: entry/submit/holding/scale_in/exit stage arms를 하나의 policy version으로 관리한다.",
            "fixed threshold는 hard_safety/baseline_prior/bounded_tunable/legacy_archive role contract로만 해석한다.",
            "BUY 승격은 micro canary cap과 hard safety guard 통과 시 BUY_DEFENSIVE로만 제한한다.",
        ],
    }


def _build_apply_candidate_list(families: list[dict]) -> list[dict]:
    candidates: list[dict] = []
    manifest_candidates = [
        family for family in families if family["apply_ready"] and family.get("apply_mode") == "manifest_only"
    ]
    for family in manifest_candidates:
        candidates.append(
            {
                "family": family["family"],
                "stage": family["stage"],
                "apply_mode": family["apply_mode"],
                "owner_rule": "manifest_only_no_runtime_mutation",
            }
        )
    entry_candidates = [
        family
        for family in families
        if family["stage"] == "entry" and family["apply_ready"] and family.get("apply_mode") != "manifest_only"
    ]
    holding_candidates = [
        family
        for family in families
        if family["stage"] == "holding_exit" and family["apply_ready"] and family.get("apply_mode") != "manifest_only"
    ]
    for group in (entry_candidates[:1], holding_candidates[:1]):
        for family in group:
            candidates.append(
                {
                    "family": family["family"],
                    "stage": family["stage"],
                    "apply_mode": family["apply_mode"],
                    "owner_rule": "single_axis_canary",
                }
            )
    return candidates


def _build_rollback_guard_pack(families: list[dict]) -> list[dict]:
    guards: list[dict] = []
    for family in families:
        if not family["apply_ready"]:
            continue
        guards.append(
            {
                "family": family["family"],
                "loss_cap": "COMPLETED + valid profit_rate avg <= -0.30% or realized pnl regression",
                "quality_regression": "submitted/full/partial 또는 soft/hard/trailing quality regression",
                "cross_contamination": "same-stage multi-owner contamination 금지",
                "sample_floor": "sample 부족은 cap 축소/hold_sample/max_step_per_day 축소 calibration으로 처리",
            }
        )
    return guards


def _family_sample_count(family: dict) -> int:
    sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
    scale_in_counts = [
        _safe_int(sample.get("resolved"), None),
        _safe_int(sample.get("guard_block"), None),
        _safe_int(sample.get("p2_observe"), None),
    ]
    if any(value is not None for value in scale_in_counts):
        return sum(int(value or 0) for value in scale_in_counts)
    smooth_hold = _safe_int(sample.get("smooth_hold"), None)
    smooth_confirmed = _safe_int(sample.get("smooth_confirmed"), None)
    if smooth_hold is not None or smooth_confirmed is not None:
        return int(smooth_hold or 0) + int(smooth_confirmed or 0)
    for key in (
        "soft_stop_micro_grace",
        "applied",
        "exit_signal",
        "touches",
    ):
        value = _safe_int(sample.get(key), None)
        if value is not None:
            return int(value)
    numeric_values = [_safe_int(value, None) for value in sample.values() if not isinstance(value, (dict, list))]
    return max([int(value) for value in numeric_values if value is not None] or [0])


def _source_metrics_for_family(output_family: str, report_source_context: dict | None) -> dict:
    metrics = (report_source_context or {}).get("source_metrics")
    metrics = metrics if isinstance(metrics, dict) else {}
    if output_family == "score65_74_recovery_probe":
        return metrics.get("buy_score65_74") if isinstance(metrics.get("buy_score65_74"), dict) else {}
    if output_family == "pre_submit_price_guard":
        return (
            metrics.get("latency_guard_miss_ev_recovery")
            if isinstance(metrics.get("latency_guard_miss_ev_recovery"), dict)
            else {}
        )
    if output_family in {"liquidity_gate_refined_candidate", "liquidity_pre_submit_guard_p1"}:
        return (
            metrics.get("liquidity_gate_refined_candidate")
            if isinstance(metrics.get("liquidity_gate_refined_candidate"), dict)
            else {}
        )
    if output_family in {"overbought_gate_refined_candidate", "overbought_pullback_guard_p1"}:
        return (
            metrics.get("overbought_gate_refined_candidate")
            if isinstance(metrics.get("overbought_gate_refined_candidate"), dict)
            else {}
        )
    if output_family == "bad_entry_refined_canary":
        return metrics.get("bad_entry") if isinstance(metrics.get("bad_entry"), dict) else {}
    if output_family == "holding_exit_decision_matrix_advisory":
        return metrics.get("decision_support") if isinstance(metrics.get("decision_support"), dict) else {}
    if output_family == "lifecycle_decision_matrix_runtime":
        return metrics.get("lifecycle_decision_matrix") if isinstance(metrics.get("lifecycle_decision_matrix"), dict) else {}
    if output_family == "market_regime_continuous_thresholds":
        return metrics.get("market_regime_continuous") if isinstance(metrics.get("market_regime_continuous"), dict) else {}
    if output_family == "scale_in_price_guard":
        return metrics.get("scale_in_price_guard") if isinstance(metrics.get("scale_in_price_guard"), dict) else {}
    if output_family == "soft_stop_whipsaw_confirmation":
        return metrics.get("soft_stop") if isinstance(metrics.get("soft_stop"), dict) else {}
    if output_family == "holding_flow_ofi_smoothing":
        return metrics.get("holding_flow") if isinstance(metrics.get("holding_flow"), dict) else {}
    if output_family in {"protect_trailing_smoothing", "trailing_continuation"}:
        return metrics.get("trailing") if isinstance(metrics.get("trailing"), dict) else {}
    return {}


def _source_sample_count_for_family(output_family: str, source_metrics: dict) -> int:
    if output_family == "score65_74_recovery_probe":
        return max(
            _safe_int(source_metrics.get("score65_74_candidates"), 0) or 0,
            _safe_int(source_metrics.get("wait6579_total_candidates"), 0) or 0,
            _safe_int(source_metrics.get("blocked_ai_score_evaluated"), 0) or 0,
        )
    if output_family == "pre_submit_price_guard":
        return max(
            _safe_int(source_metrics.get("evaluated_candidates"), 0) or 0,
            _safe_int(source_metrics.get("performance_latency_block_events"), 0) or 0,
        )
    if output_family in {"liquidity_gate_refined_candidate", "liquidity_pre_submit_guard_p1"}:
        return max(
            _safe_int(source_metrics.get("evaluated_candidates"), 0) or 0,
            _safe_int(source_metrics.get("performance_blocked_liquidity_events"), 0) or 0,
        )
    if output_family in {"overbought_gate_refined_candidate", "overbought_pullback_guard_p1"}:
        return max(
            _safe_int(source_metrics.get("evaluated_candidates"), 0) or 0,
            _safe_int(source_metrics.get("performance_blocked_overbought_events"), 0) or 0,
        )
    if output_family == "bad_entry_refined_canary":
        return max(
            _safe_int(source_metrics.get("refined_candidate"), 0) or 0,
            _safe_int(source_metrics.get("soft_stop_tail_sample"), 0) or 0,
        )
    if output_family == "holding_exit_decision_matrix_advisory":
        return _safe_int(source_metrics.get("matrix_entries"), 0) or 0
    if output_family == "lifecycle_decision_matrix_runtime":
        return max(
            _safe_int(source_metrics.get("total_rows"), 0) or 0,
            _safe_int(source_metrics.get("joined_rows"), 0) or 0,
        )
    if output_family == "market_regime_continuous_thresholds":
        source_quality = source_metrics.get("source_quality") if isinstance(source_metrics.get("source_quality"), dict) else {}
        rolling_10d = source_metrics.get("rolling_10d") if isinstance(source_metrics.get("rolling_10d"), dict) else {}
        return max(
            _safe_int(source_quality.get("valid_market_regime_days"), 0) or 0,
            _safe_int(rolling_10d.get("valid_market_regime_days"), 0) or 0,
        )
    if output_family == "scale_in_price_guard":
        guard_events = (
            (_safe_int(source_metrics.get("scale_in_price_resolved"), 0) or 0)
            + (_safe_int(source_metrics.get("scale_in_price_guard_block"), 0) or 0)
            + (_safe_int(source_metrics.get("scale_in_price_p2_observe"), 0) or 0)
        )
        saw_actions = (_safe_int(source_metrics.get("avg_down_wait"), 0) or 0) + (
            _safe_int(source_metrics.get("pyramid_wait"), 0) or 0
        )
        return max(guard_events, _safe_int(source_metrics.get("compact_scale_in_executed"), 0) or 0, saw_actions)
    if output_family == "soft_stop_whipsaw_confirmation":
        return max(
            _safe_int(source_metrics.get("holding_exit_observation_total"), 0) or 0,
            _safe_int(source_metrics.get("post_sell_soft_stop_total"), 0) or 0,
        )
    if output_family == "holding_flow_ofi_smoothing":
        return _safe_int(source_metrics.get("holding_flow_override_defer_exit"), 0) or 0
    if output_family in {"protect_trailing_smoothing", "trailing_continuation"}:
        return max(
            _safe_int(source_metrics.get("evaluated_trailing"), 0) or 0,
            _safe_int(source_metrics.get("qualifying_cohort_count"), 0) or 0,
        )
    return 0


def _score65_74_entry_unlock_probe_ready(source_metrics: dict, *, sample_count: int, sample_floor: int) -> bool:
    """Return True when the existing score65~74 entry probe should open to collect applied samples."""
    if sample_count < sample_floor:
        return False
    avg_ev = _safe_float(source_metrics.get("score65_74_avg_expected_ev_pct"), None)
    avg_close = _safe_float(source_metrics.get("score65_74_avg_close_10m_pct"), None)
    avg_mfe = _safe_float(source_metrics.get("score65_74_avg_mfe_10m_pct"), None)
    submitted_to_budget = _safe_float(source_metrics.get("submitted_to_budget_unique_pct"), None)
    order_bundle_submitted = _safe_float(source_metrics.get("order_bundle_submitted"), None)
    panic_state = str(source_metrics.get("panic_state") or "").upper()
    panic_regime = str(source_metrics.get("panic_regime_mode") or "").upper()
    panic_detected = bool(source_metrics.get("panic_detected")) or bool(source_metrics.get("panic_by_stop_loss_count"))
    if panic_detected or panic_state in {"PANIC_SELL", "RECOVERY_WATCH"} or panic_regime == "PANIC_DETECTED":
        return False
    if avg_ev is None or avg_ev < 2.0:
        return False
    if avg_close is None or avg_close < 1.0:
        return False
    if avg_mfe is not None and avg_mfe < 2.0:
        return False
    if submitted_to_budget is not None and submitted_to_budget > 10.0:
        return False
    if order_bundle_submitted is not None and order_bundle_submitted > 0:
        return False
    return True


def _calibration_state_for_family(
    output_family: str,
    family: dict,
    metadata: dict,
    *,
    source_metrics: dict | None = None,
    sample_count: int | None = None,
    sample_ready: bool | None = None,
) -> tuple[str, str]:
    source_metrics = source_metrics if isinstance(source_metrics, dict) else {}
    sample_count = _family_sample_count(family) if sample_count is None else int(sample_count)
    sample_floor = int(metadata.get("sample_floor") or 0)
    if output_family == "trailing_continuation":
        return (
            "freeze",
            "GOOD_EXIT 훼손 리스크가 커서 1차 loop에서는 report/calibration만 수행하고 live apply는 금지한다.",
        )
    ready = bool(family.get("apply_ready")) if sample_ready is None else bool(sample_ready)
    if output_family == "holding_exit_decision_matrix_advisory":
        family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
        non_clear_edge = _safe_int(family_sample.get("matrix_non_clear_edge"), 0) or 0
        candidate_weight_source = _safe_int(family_sample.get("saw_candidate_weight_source"), 0) or 0
        counterfactual_gap_count = _safe_int(family_sample.get("counterfactual_gap_count"), 0) or 0
        if non_clear_edge <= 0:
            return ("hold_no_edge", "ADM/SAW matrix가 전부 no_clear_edge라 최소 edge 부재; live AI 응답 변경 없음")
        if candidate_weight_source <= 0:
            return ("hold_sample", "SAW candidate_weight_source bucket이 없어 advisory canary 후보 유지")
        if counterfactual_gap_count > 0:
            return ("hold_sample", "ADM action별 exit_only/avg_down/pyramid counterfactual coverage가 닫히지 않음")
    if output_family == "lifecycle_decision_matrix_runtime":
        family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
        joined_rows = _safe_int(family_sample.get("joined_rows"), 0) or 0
        policy_pass_count = _safe_int(family_sample.get("policy_pass_count"), 0) or 0
        if sample_count < sample_floor or joined_rows < 10:
            return (
                "hold_sample",
                f"lifecycle matrix source sample floor 미달(rows={sample_count}/{sample_floor}, joined={joined_rows}/10)",
            )
        if policy_pass_count <= 0:
            return ("hold_no_edge", "stage policy 중 source-quality pass arm이 없어 runtime policy 적용 보류")
        return (
            "adjust_up",
            "lifecycle matrix weighted ADM source가 balanced gate를 통과해 다음 장전 umbrella micro canary 후보",
        )
    if output_family == "market_regime_continuous_thresholds":
        source_quality = source_metrics.get("source_quality") if isinstance(source_metrics.get("source_quality"), dict) else {}
        valid_days = _safe_int(source_quality.get("valid_market_regime_days"), 0) or 0
        if valid_days < sample_floor:
            return (
                "hold_sample",
                f"market regime continuous rolling source sample floor 미달({valid_days}/{sample_floor}); context-only 유지",
            )
        return (
            "hold",
            "market regime continuous thresholds v1은 1차 개발에서 ADM/LDM risk_context 및 manifest-only 후보로만 유지한다.",
        )
    if output_family == "score65_74_recovery_probe":
        family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
        avg_ev = _safe_float(source_metrics.get("score65_74_avg_expected_ev_pct"), None)
        avg_close = _safe_float(source_metrics.get("score65_74_avg_close_10m_pct"), None)
        panic_state = str(source_metrics.get("panic_state") or "")
        panic_detected = bool(source_metrics.get("panic_detected")) or bool(
            source_metrics.get("panic_by_stop_loss_count")
        )
        panic_adjusted_floor = max(1, int(round(sample_floor * 0.7))) if sample_floor > 0 else 0
        submitted_to_budget = _safe_float(source_metrics.get("submitted_to_budget_unique_pct"), None)
        if sample_count >= sample_floor and ((avg_ev is not None and avg_ev < 2.0) or (avg_close is not None and avg_close < 1.0)):
            return ("hold", "score65~74 EV/close_10m 우위가 efficient trade-off gate에 미달해 값 유지")
        if submitted_to_budget is not None and submitted_to_budget > 60.0:
            return ("hold", "submitted drought가 아니므로 probe live 확대보다 baseline funnel 유지")
        if _score65_74_entry_unlock_probe_ready(
            source_metrics,
            sample_count=sample_count,
            sample_floor=sample_floor,
        ):
            return (
                "adjust_up",
                "rolling primary score65~74 missed EV가 양수이고 panic/source guard가 정상이다. "
                "submitted drought를 풀기 위해 기존 1주/5만원 bounded entry probe를 연다.",
            )
        if (
            0 < panic_adjusted_floor <= sample_count < sample_floor
            and (panic_detected or panic_state in {"PANIC_SELL", "RECOVERY_WATCH"})
            and avg_ev is not None
            and avg_ev >= 2.0
            and avg_close is not None
            and avg_close >= 1.0
            and (submitted_to_budget is None or submitted_to_budget <= 10.0)
        ):
            return (
                "adjust_up",
                f"panic-adjusted floor 통과({sample_count}/{sample_floor}, adjusted_floor={panic_adjusted_floor}); "
                "BUY drought일의 양호한 score65~74 missed EV를 1주/5만원 bounded canary로 유지",
            )
        if sample_count >= sample_floor and ready:
            return (
                "adjust_up",
                "partial_samples=0은 전면 금지가 아니라 post-apply calibration target; 1주/5만원 bounded canary 후보",
            )
        if _safe_int(family_sample.get("wait65_79_score65_74_candidate"), 0) or 0:
            return ("hold_sample", "score65~74 후보는 있으나 source/report sample floor가 부족해 cap 유지")
    if output_family == "pre_submit_price_guard":
        recommended_action = str(source_metrics.get("recommended_action") or "")
        recovery_count = _safe_int(source_metrics.get("would_recovery_canary_events"), 0) or 0
        counterfactual_joined = _safe_int(source_metrics.get("counterfactual_joined_sample"), 0) or 0
        if recommended_action in {"bounded_apply", "hold", "reject"}:
            if recommended_action == "bounded_apply":
                return (
                    "hold",
                    "latency submit recovery는 latency_classifier_runtime_profile가 소유한다. "
                    "pre_submit_price_guard는 후행 가격품질 guard로 유지한다.",
                )
            if recovery_count > 0:
                state = "hold_sample" if counterfactual_joined < 3 else "hold_no_edge"
                return (
                    state,
                    "latency recovery 후보가 있으나 counterfactual EV/label gate 미충족으로 "
                    "pre_submit_price_guard 완화가 아니라 latency classifier 후보 보류로 라우팅한다.",
                )
            return (
                "hold_sample",
                "latency_classifier runtime semantics 기준 후보가 없어 pre_submit_price_guard는 현행 유지한다.",
            )
        missed_rate = _safe_float(source_metrics.get("missed_winner_rate"), None)
        avoided_rate = _safe_float(source_metrics.get("avoided_loser_rate"), None)
        quote_pass_rate = _safe_float(source_metrics.get("quote_fresh_latency_pass_rate"), None)
        if sample_count < sample_floor:
            return (
                "hold_sample",
                f"latency guard miss source sample floor 미달({sample_count}/{sample_floor}); 현재 pre-submit guard 유지",
            )
        if quote_pass_rate is not None and quote_pass_rate < 30.0:
            return ("freeze", "quote freshness 품질이 낮아 threshold 완화가 아니라 runtime/instrumentation 원인 분해 우선")
        if missed_rate is not None and avoided_rate is not None and missed_rate > avoided_rate + 10.0:
            return ("adjust_up", "latency_block missed-winner 우위가 있어 max_below_bid_bps bounded 상향 후보")
        return ("hold", "latency guard miss EV 회복 우위가 충분하지 않아 현행 pre-submit guard 유지")
    if output_family in {
        "liquidity_gate_refined_candidate",
        "overbought_gate_refined_candidate",
        "strength_momentum_soft_gate_p1",
        "overbought_pullback_guard_p1",
        "liquidity_pre_submit_guard_p1",
    }:
        if sample_count < sample_floor:
            return (
                "hold_sample",
                f"{output_family} source sample floor 미달({sample_count}/{sample_floor}); 신규 family 설계 후보만 유지",
            )
        if output_family in {
            "strength_momentum_soft_gate_p1",
            "overbought_pullback_guard_p1",
            "liquidity_pre_submit_guard_p1",
        }:
            return (
                "hold",
                f"{output_family}는 pre-AI gate 재설계 family 후보이며 approval artifact 전까지 자동 runtime apply 금지",
            )
        missed_rate = _safe_float(source_metrics.get("missed_winner_rate"), None)
        avoided_rate = _safe_float(source_metrics.get("avoided_loser_rate"), None)
        if missed_rate is not None and avoided_rate is not None and avoided_rate > missed_rate + 10.0:
            return ("freeze", "차단이 손실 회피에 더 기여해 refined gate 완화 설계 중지")
        return ("hold", "기존 관찰축 추가 없이 source bundle에 묶어 family design candidate로 유지")
    if output_family == "bad_entry_refined_canary":
        lifecycle = source_metrics.get("lifecycle_attribution")
        lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
        candidate_records = _safe_int(lifecycle.get("candidate_records"), 0) or 0
        if candidate_records > 0:
            pending_records = _safe_int(lifecycle.get("post_sell_pending_records"), 0) or 0
            joined_records = _safe_int(lifecycle.get("post_sell_joined_records"), 0) or 0
            type_counts = lifecycle.get("final_type_counts") if isinstance(lifecycle.get("final_type_counts"), dict) else {}
            false_positive_risk = _safe_int(type_counts.get("false_positive_risk_after_candidate"), 0) or 0
            preventable = _safe_int(type_counts.get("preventable_bad_entry_candidate"), 0) or 0
            refined_exit_finalized = _safe_int(type_counts.get("refined_exit_finalized"), 0) or 0
            late_soft_stop_zone = _safe_int(type_counts.get("late_detected_soft_stop_zone"), 0) or 0
            if pending_records > 0 or joined_records <= 0:
                return (
                    "hold_sample",
                    "bad_entry 후보는 runtime provisional signal이며 postclose post-sell outcome join 후 최종 유형을 닫는다.",
                )
            if false_positive_risk > 0:
                return (
                    "freeze",
                    "post-sell MISSED_UPSIDE 후보가 있어 bad-entry live 확대 대신 false-positive risk를 먼저 calibration한다.",
                )
            if preventable <= 0 and refined_exit_finalized <= 0 and late_soft_stop_zone > 0:
                return (
                    "hold",
                    "후보가 soft-stop zone에서 late-detected되어 조기 진입 차단 근거가 아니라 lifecycle attribution 표본으로 유지한다.",
                )
            if preventable <= 0 and refined_exit_finalized <= 0:
                return (
                    "hold",
                    "post-sell outcome은 확정됐지만 preventable/refined-exit edge가 없어 값 유지",
                )
        if sample_count >= sample_floor and ready:
            return (
                "adjust_up",
                "postclose lifecycle attribution 또는 rolling aggregate가 통과한 refined canary를 한 단계 적용",
            )
    if output_family == "scale_in_price_guard":
        family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
        resolved_executed = max(
            _safe_int(family_sample.get("resolved_executed"), 0) or 0,
            _safe_int(source_metrics.get("compact_scale_in_executed"), 0) or 0,
        )
        if resolved_executed <= 0:
            return (
                "hold_sample",
                "물타기/불타기 resolved/executed cohort가 없어 가격·수량 guard 값은 유지하고 다음 장후 재산정",
            )
        if sample_count < sample_floor or not ready:
            return ("hold_sample", f"scale-in sample floor 미달({sample_count}/{sample_floor}); 수량/가격 가드 유지")
        return (
            "hold",
            "scale_in_price_guard는 별도 승인 전 report-only calibration으로만 산출하며 live apply는 금지한다.",
        )
    if output_family == "position_sizing_cap_release":
        sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
        safety_floor = sample.get("safety_floor") if isinstance(sample.get("safety_floor"), dict) else {}
        tradeoff_score = _safe_float(sample.get("tradeoff_score"), 0.0) or 0.0
        required_score = _safe_float(sample.get("tradeoff_score_required"), 0.70) or 0.70
        if sample_count < sample_floor or not ready:
            failed = [key for key, value in safety_floor.items() if not bool(value)]
            suffix = f"; failed_safety_floor={','.join(failed)}" if failed else ""
            return (
                "hold_sample",
                f"1주 cap 해제 trade-off 기준 미달({sample_count}/{sample_floor}, score={tradeoff_score:.2f}/{required_score:.2f}){suffix}",
            )
        return (
            "approval_required",
            f"1주 cap 해제 efficient trade-off 기준 충족(score={tradeoff_score:.2f}/{required_score:.2f}): 자동 적용하지 않고 사용자 승인 요청 artifact로만 승격한다.",
        )
    if output_family == "position_sizing_dynamic_formula":
        sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
        blockers = sample.get("source_quality_blockers") if isinstance(sample.get("source_quality_blockers"), list) else []
        if sample_count < sample_floor:
            return (
                "hold_sample",
                f"동적수량 산식 real denominator sample floor 미달({sample_count}/{sample_floor}); report-only source bundle만 유지",
            )
        if blockers:
            return (
                "hold_sample",
                "동적수량 산식 입력 coverage 미충족: " + ",".join(str(item) for item in blockers[:8]),
            )
        return (
            "hold",
            "동적수량 산식 source bundle은 준비됐지만 runtime 수량 변경은 별도 approval artifact 전까지 금지한다.",
        )
    if output_family == "soft_stop_whipsaw_confirmation":
        source_count = _source_sample_count_for_family(output_family, source_metrics)
        if 0 < source_count < sample_floor:
            return (
                "hold_sample",
                f"post-sell/holding-exit soft-stop source sample floor 미달({source_count}/{sample_floor}); 단일 사례로 live enable 금지",
            )
    if sample_count < sample_floor or not ready:
        return ("hold_sample", f"sample floor 미달({sample_count}/{sample_floor}); 값 유지 후 다음 장후 재산정")

    current = family.get("current") if isinstance(family.get("current"), dict) else {}
    recommended = family.get("recommended") if isinstance(family.get("recommended"), dict) else {}
    if "enabled" in current and "enabled" in recommended and bool(current.get("enabled")) != bool(
        recommended.get("enabled")
    ):
        return ("adjust_up", "bounded live candidate: disabled -> enabled 전환은 다음 장전 단일 적용 후보")
    primary_key = str(metadata.get("primary_key") or "")
    current_value = current.get(primary_key)
    recommended_value = recommended.get(primary_key)
    if isinstance(current_value, bool) or isinstance(recommended_value, bool):
        if bool(recommended_value) != bool(current_value):
            return ("adjust_up", "bounded live candidate: disabled -> enabled 전환은 다음 장전 단일 적용 후보")
    current_num = _safe_float(current_value, None)
    recommended_num = _safe_float(recommended_value, None)
    if current_num is None or recommended_num is None:
        return ("hold", "추천값과 현행값을 수치 방향으로 비교할 수 없어 값 유지")
    if recommended_num > current_num:
        return ("adjust_up", "목표 미달 시 rollback이 아니라 max_step_per_day 안에서 상향 calibration")
    if recommended_num < current_num:
        return ("adjust_down", "목표 미달 시 rollback이 아니라 max_step_per_day 안에서 하향 calibration")
    return ("hold", "현행값과 추천값이 같아 다음 장전 값 유지")


def _build_calibration_candidates(families: list[dict], report_source_context: dict | None = None) -> list[dict]:
    family_by_name = {str(family.get("family") or ""): family for family in families}
    candidates: list[dict] = []
    for output_family, metadata in sorted(
        CALIBRATION_FAMILY_METADATA.items(), key=lambda item: int(item[1].get("priority") or 999)
    ):
        source_family = str(metadata.get("source_family") or output_family)
        family = family_by_name.get(source_family)
        if not family:
            continue
        current = family.get("current") if isinstance(family.get("current"), dict) else {}
        recommended = family.get("recommended") if isinstance(family.get("recommended"), dict) else {}
        source_metrics = dict(_source_metrics_for_family(output_family, report_source_context))
        if output_family == "lifecycle_decision_matrix_runtime":
            family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
            source_metrics.update(
                {
                    "total_rows": _safe_int(family_sample.get("total_rows"), 0) or 0,
                    "joined_rows": _safe_int(family_sample.get("joined_rows"), 0) or 0,
                    "policy_pass_count": _safe_int(family_sample.get("policy_pass_count"), 0) or 0,
                    "promote_ready_count": _safe_int(family_sample.get("promote_ready_count"), 0) or 0,
                    "fixed_threshold_roles": {
                        "hard_safety": "override_forbidden",
                        "baseline_prior": "feature_only",
                        "bounded_tunable": "threshold_cycle_bounds_required",
                        "legacy_archive": "runtime_feature_forbidden",
                    },
                }
            )
        if output_family == "bad_entry_refined_canary":
            family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
            lifecycle_attribution = family_sample.get("lifecycle_attribution")
            if isinstance(lifecycle_attribution, dict) and lifecycle_attribution.get("candidate_records"):
                source_metrics["lifecycle_attribution"] = lifecycle_attribution
                source_metrics["post_sell_joined_candidate_records"] = _safe_int(
                    lifecycle_attribution.get("post_sell_joined_records"), 0
                ) or 0
                source_metrics["post_sell_pending_candidate_records"] = _safe_int(
                    lifecycle_attribution.get("post_sell_pending_records"), 0
                ) or 0
                type_counts = (
                    lifecycle_attribution.get("final_type_counts")
                    if isinstance(lifecycle_attribution.get("final_type_counts"), dict)
                    else {}
                )
                source_metrics["preventable_bad_entry_candidate_records"] = _safe_int(
                    type_counts.get("preventable_bad_entry_candidate"), 0
                ) or 0
                source_metrics["false_positive_risk_after_candidate_records"] = _safe_int(
                    type_counts.get("false_positive_risk_after_candidate"), 0
                ) or 0
                source_metrics["late_detected_soft_stop_zone_records"] = _safe_int(
                    type_counts.get("late_detected_soft_stop_zone"), 0
                ) or 0
        source_sample_count = _source_sample_count_for_family(output_family, source_metrics)
        if output_family == "bad_entry_refined_canary":
            lifecycle = source_metrics.get("lifecycle_attribution")
            if isinstance(lifecycle, dict):
                source_sample_count = max(
                    source_sample_count,
                    _safe_int(lifecycle.get("post_sell_joined_records"), 0) or 0,
                )
        if output_family == "score65_74_recovery_probe":
            # The family sample includes broad funnel events such as budget_pass.
            # Runtime readiness must use the score65~74 source cohort only.
            sample_count = source_sample_count
        elif output_family == "position_sizing_dynamic_formula":
            family_sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
            sample_count = _safe_int(family_sample.get("real_completed_valid"), 0) or 0
        else:
            sample_count = max(_family_sample_count(family), source_sample_count)
        sample_floor = int(metadata.get("sample_floor") or 0)
        source_ready = source_sample_count >= sample_floor
        if output_family == "score65_74_recovery_probe":
            adjusted_floor = max(1, int(round(sample_floor * 0.7))) if sample_floor > 0 else 0
            avg_ev = _safe_float(source_metrics.get("score65_74_avg_expected_ev_pct"), None)
            avg_close = _safe_float(source_metrics.get("score65_74_avg_close_10m_pct"), None)
            submitted_to_budget = _safe_float(source_metrics.get("submitted_to_budget_unique_pct"), None)
            panic_state = str(source_metrics.get("panic_state") or "")
            panic_detected = bool(source_metrics.get("panic_detected")) or bool(
                source_metrics.get("panic_by_stop_loss_count")
            )
            panic_adjusted_ready = (
                0 < adjusted_floor <= sample_count < sample_floor
                and (panic_detected or panic_state in {"PANIC_SELL", "RECOVERY_WATCH"})
                and avg_ev is not None
                and avg_ev >= 2.0
                and avg_close is not None
                and avg_close >= 1.0
                and (submitted_to_budget is None or submitted_to_budget <= 10.0)
            )
            if panic_adjusted_ready:
                source_ready = True
                recommended = dict(recommended)
                recommended["enabled"] = True
            elif _score65_74_entry_unlock_probe_ready(
                source_metrics,
                sample_count=sample_count,
                sample_floor=sample_floor,
            ):
                source_ready = True
                recommended = dict(recommended)
                recommended["enabled"] = True
                source_metrics["entry_unlock_probe_ready"] = True
        sample_ready = bool(family.get("apply_ready")) or source_ready
        calibration_state, calibration_reason = _calibration_state_for_family(
            output_family,
            family,
            metadata,
            source_metrics=source_metrics,
            sample_count=sample_count,
            sample_ready=sample_ready,
        )
        sample_floor_status = "ready" if sample_count >= sample_floor and sample_ready else "hold_sample"
        if output_family == "score65_74_recovery_probe" and sample_ready and sample_count < sample_floor:
            sample_floor_status = "panic_adjusted_ready"
        if calibration_state == "freeze":
            sample_floor_status = "direction_conflict_or_live_risk"
        if calibration_state == "hold_no_edge":
            sample_floor_status = "minimum_edge_missing"
        if calibration_state == "approval_required":
            sample_floor_status = "manual_approval_required"
        if calibration_state == "hold_sample":
            sample_floor_status = "hold_sample"
        confidence = round(min(1.0, sample_count / sample_floor), 4) if sample_floor > 0 else 0.0
        primary_key = str(metadata.get("primary_key") or "")
        runtime_apply_candidate = (
            sample_ready
            and bool(metadata.get("allowed_runtime_apply"))
            and calibration_state not in {"freeze", "hold_sample", "hold_no_edge"}
        )
        candidate = {
            "family": output_family,
            "source_family": source_family,
            "threshold_version": f"{output_family}:{family.get('apply_mode', 'observe_only')}:{sample_floor_status}",
            "stage": family.get("stage"),
            "priority": int(metadata.get("priority") or 999),
            "target_env_keys": list(metadata.get("target_env_keys") or []),
            "supersedes": list(metadata.get("supersedes") or []),
            "current_value": current.get(primary_key),
            "current_values": current,
            "recommended_value": recommended.get(primary_key),
            "recommended_values": recommended,
            "applied_value": current.get(primary_key),
            "applied_values": current,
            "min_value": (metadata.get("bounds") or {}).get(primary_key, {}).get("min"),
            "max_value": (metadata.get("bounds") or {}).get(primary_key, {}).get("max"),
            "max_step_per_day": (metadata.get("bounds") or {}).get(primary_key, {}).get("max_step_per_day"),
            "bounds": metadata.get("bounds") or {},
            "sample_window": metadata.get("sample_window", "daily"),
            "window_policy": dict(metadata.get("window_policy") or {}),
            "sample_count": sample_count,
            "source_sample_count": source_sample_count,
            "sample_floor": sample_floor,
            "sample_floor_status": sample_floor_status,
            "confidence": confidence,
            "source_metrics": source_metrics,
            "source_reports": {
                name: source.get("path")
                for name, source in ((report_source_context or {}).get("sources") or {}).items()
                if isinstance(source, dict) and source.get("exists")
            },
            "calibration_state": calibration_state,
            "calibration_reason": calibration_reason,
            "safety_revert_required": False,
            "safety_guard": list(CALIBRATION_SAFETY_GUARDS),
            "apply_mode": "efficient_tradeoff_canary_candidate"
            if runtime_apply_candidate
            and (
                family.get("apply_mode") == "efficient_tradeoff_canary_candidate"
                or output_family
                in {
                    "score65_74_recovery_probe",
                    "bad_entry_refined_canary",
                    "holding_exit_decision_matrix_advisory",
                    "lifecycle_decision_matrix_runtime",
                }
            )
            else "calibrated_apply_candidate"
            if runtime_apply_candidate
            else "report_only_calibration",
            "allowed_runtime_apply": bool(metadata.get("allowed_runtime_apply")),
            "human_approval_required": bool(metadata.get("human_approval_required"))
            or calibration_state == "approval_required",
            "runtime_change": False,
            "runtime_change_reason": "장중 자동 mutation 금지; 다음 장전 승인된 family만 bounded apply 대상",
        }
        if output_family == "market_regime_continuous_thresholds":
            candidate["apply_mode"] = "manifest_only"
            candidate["runtime_change_reason"] = (
                "market regime continuous thresholds 1차 개발은 ADM/LDM risk_context와 source bundle만 생성한다."
            )
        candidates.append(candidate)
    return candidates


def _build_safety_guard_pack(calibration_candidates: list[dict]) -> list[dict]:
    return [
        {
            "family": candidate["family"],
            "safety_revert_required": bool(candidate.get("safety_revert_required")),
            "safety_guard": candidate.get("safety_guard") or CALIBRATION_SAFETY_GUARDS,
            "revert_policy": "safety breach only",
        }
        for candidate in calibration_candidates
        if bool(candidate.get("allowed_runtime_apply"))
    ]


def _build_calibration_trigger_pack(calibration_candidates: list[dict]) -> list[dict]:
    return [
        {
            "family": candidate["family"],
            "calibration_state": candidate.get("calibration_state"),
            "calibration_reason": candidate.get("calibration_reason"),
            "next_manifest_action": "step_adjust_or_hold_or_freeze",
            "rollback_policy": "not_a_rollback_trigger",
        }
        for candidate in calibration_candidates
    ]


def _build_post_apply_attribution(calibration_candidates: list[dict]) -> dict:
    return {
        "status": "pending_applied_cohort" if calibration_candidates else "no_calibration_candidate",
        "runtime_change": False,
        "cohort_key": "threshold_family|threshold_version|calibration_state",
        "baseline_cohort": "current_values",
        "applied_cohort": "next_preopen_approved_values",
        "metrics": ["GOOD_EXIT", "MISSED_UPSIDE", "soft_stop_tail", "defer_cost", "safety_breach"],
        "soft_stop_balanced_policy": {
            "good_exit_regression_tolerance_pp": 10,
            "keep_condition": "soft-stop 손실 tail 감소 또는 MISSED_UPSIDE 감소가 있으면 유지/완만 조정",
            "perfect_win_rate_required": False,
        },
        "calibration_decisions": [
            {
                "family": candidate.get("family"),
                "threshold_version": candidate.get("threshold_version"),
                "calibration_state": candidate.get("calibration_state"),
                "sample_count": candidate.get("sample_count"),
                "source_sample_count": candidate.get("source_sample_count"),
                "sample_floor": candidate.get("sample_floor"),
                "sample_floor_status": candidate.get("sample_floor_status"),
                "source_metrics": candidate.get("source_metrics") or {},
                "safety_revert_required": candidate.get("safety_revert_required"),
            }
            for candidate in calibration_candidates
        ],
    }


def _normalize_ai_sample_window(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    aliases = {
        "daily": "daily_intraday",
        "intraday": "daily_intraday",
        "same_day": "daily_intraday",
        "rolling": "rolling_10d",
        "rolling10": "rolling_10d",
        "rolling_10": "rolling_10d",
        "rolling5": "rolling_5d",
        "rolling_5": "rolling_5d",
        "cumulative_since_2026-04-21": "cumulative",
    }
    return aliases.get(text, text)


def _allowed_sample_windows_for_candidate(candidate: dict) -> set[str]:
    policy = candidate.get("window_policy") if isinstance(candidate.get("window_policy"), dict) else {}
    primary = _normalize_ai_sample_window(policy.get("primary") or candidate.get("sample_window"))
    allowed: set[str] = set()
    if primary in AI_CORRECTION_ALLOWED_SAMPLE_WINDOWS:
        allowed.add(primary)
    for raw_secondary in policy.get("secondary") or []:
        normalized = _normalize_ai_sample_window(raw_secondary)
        if normalized in AI_CORRECTION_ALLOWED_SAMPLE_WINDOWS:
            allowed.add(normalized)
    if policy and not bool(policy.get("daily_only_allowed")):
        allowed.discard("daily_intraday")
    return allowed or set(AI_CORRECTION_ALLOWED_SAMPLE_WINDOWS)


def _candidate_primary_window(candidate: dict) -> str | None:
    policy = candidate.get("window_policy") if isinstance(candidate.get("window_policy"), dict) else {}
    return _normalize_ai_sample_window(policy.get("primary") or candidate.get("sample_window"))


def _sample_denominator_keys_for_family(family: str) -> list[str]:
    metadata = CALIBRATION_FAMILY_METADATA.get(str(family) or "")
    if isinstance(metadata, dict) and isinstance(metadata.get("sample_denominator_keys"), list):
        return [str(value) for value in metadata.get("sample_denominator_keys") or [] if str(value or "").strip()]
    return []


def _snapshot_relevant_sample_count(family: str, snapshot: dict | None) -> int | None:
    if not isinstance(snapshot, dict):
        return None
    sample = snapshot.get("sample") if isinstance(snapshot.get("sample"), dict) else {}
    keys = _sample_denominator_keys_for_family(family)
    if keys:
        values = [_safe_int(sample.get(key), None) for key in keys]
        values = [int(value) for value in values if value is not None]
        return max(values) if values else 0
    scale_in_counts = [
        _safe_int(sample.get("resolved"), None),
        _safe_int(sample.get("guard_block"), None),
        _safe_int(sample.get("p2_observe"), None),
    ]
    if any(value is not None for value in scale_in_counts):
        return sum(int(value or 0) for value in scale_in_counts)
    smooth_hold = _safe_int(sample.get("smooth_hold"), None)
    smooth_confirmed = _safe_int(sample.get("smooth_confirmed"), None)
    if smooth_hold is not None or smooth_confirmed is not None:
        return int(smooth_hold or 0) + int(smooth_confirmed or 0)
    for key in (
        "completed_valid",
        "observed",
        "exit_signal",
        "touches",
        "soft_stop_micro_grace",
        "resolved",
        "guard_block",
        "p2_observe",
    ):
        value = _safe_int(sample.get(key), None)
        if value is not None:
            return int(value)
    numeric_values = [_safe_int(value, None) for value in sample.values() if not isinstance(value, (dict, list))]
    numeric_values = [int(value) for value in numeric_values if value is not None]
    return max(numeric_values) if numeric_values else None


def _window_snapshot(cumulative_report: dict | None, family: str, window: str | None) -> dict | None:
    if not isinstance(cumulative_report, dict) or not window:
        return None
    snapshots = cumulative_report.get("threshold_snapshot_by_window")
    snapshots = snapshots if isinstance(snapshots, dict) else {}
    window_pack = snapshots.get(window)
    if not isinstance(window_pack, dict):
        return None
    snapshot = window_pack.get(family)
    if not isinstance(snapshot, dict):
        metadata = CALIBRATION_FAMILY_METADATA.get(str(family) or "")
        source_family = str((metadata or {}).get("source_family") or "")
        if source_family and source_family != family:
            snapshot = window_pack.get(source_family)
    return snapshot if isinstance(snapshot, dict) else None


def _window_source_context(cumulative_report: dict | None, window: str | None) -> dict:
    if not isinstance(cumulative_report, dict) or not window:
        return {}
    by_window = cumulative_report.get("calibration_source_bundle_by_window")
    by_window = by_window if isinstance(by_window, dict) else {}
    context = by_window.get(window)
    return context if isinstance(context, dict) else {}


def _sample_floor_status_for_candidate_state(state: str, sample_count: int, sample_floor: int, sample_ready: bool) -> str:
    if state == "freeze":
        return "direction_conflict_or_live_risk"
    if state == "hold_no_edge":
        return "minimum_edge_missing"
    if state == "approval_required":
        return "manual_approval_required"
    if state == "hold_sample":
        return "hold_sample"
    return "ready" if sample_count >= sample_floor and sample_ready else "hold_sample"


def _runtime_apply_candidate_for_state(candidate: dict, state: str, sample_ready: bool) -> bool:
    return (
        bool(sample_ready)
        and bool(candidate.get("allowed_runtime_apply"))
        and state not in {"freeze", "hold_sample", "hold_no_edge", "approval_required"}
    )


def _apply_mode_for_candidate_state(candidate: dict, state: str, sample_ready: bool) -> str:
    if not _runtime_apply_candidate_for_state(candidate, state, sample_ready):
        return "report_only_calibration"
    if str(candidate.get("family") or "") in {
        "score65_74_recovery_probe",
        "bad_entry_refined_canary",
        "holding_exit_decision_matrix_advisory",
        "lifecycle_decision_matrix_runtime",
    }:
        return "efficient_tradeoff_canary_candidate"
    return "calibrated_apply_candidate"


def _refresh_candidate_from_primary_window(
    candidate: dict,
    *,
    primary_snapshot: dict | None,
    primary_source_metrics: dict,
    primary_sample_count: int,
    primary_ready: bool,
    primary_window: str,
) -> None:
    family = str(candidate.get("family") or "")
    metadata = CALIBRATION_FAMILY_METADATA.get(family)
    if not isinstance(metadata, dict):
        return
    family_like = primary_snapshot if isinstance(primary_snapshot, dict) else {}
    source_metrics = primary_source_metrics if primary_source_metrics else candidate.get("source_metrics")
    source_metrics = source_metrics if isinstance(source_metrics, dict) else {}
    state, reason = _calibration_state_for_family(
        family,
        family_like,
        metadata,
        source_metrics=source_metrics,
        sample_count=primary_sample_count,
        sample_ready=primary_ready,
    )
    sample_floor = _safe_int(candidate.get("sample_floor"), 0) or 0
    sample_floor_status = _sample_floor_status_for_candidate_state(
        state,
        primary_sample_count,
        sample_floor,
        primary_ready,
    )
    primary_key = str(metadata.get("primary_key") or "")
    current = family_like.get("current") if isinstance(family_like.get("current"), dict) else candidate.get("current_values")
    recommended = (
        family_like.get("recommended")
        if isinstance(family_like.get("recommended"), dict)
        else candidate.get("recommended_values")
    )
    current = current if isinstance(current, dict) else {}
    recommended = recommended if isinstance(recommended, dict) else {}
    if family == "score65_74_recovery_probe" and _score65_74_entry_unlock_probe_ready(
        source_metrics,
        sample_count=primary_sample_count,
        sample_floor=sample_floor,
    ):
        recommended = dict(recommended)
        recommended["enabled"] = True
        source_metrics["entry_unlock_probe_ready"] = True
    apply_mode = _apply_mode_for_candidate_state(candidate, state, primary_ready)
    candidate.update(
        {
            "sample_count": primary_sample_count,
            "confidence": round(min(1.0, primary_sample_count / sample_floor), 4) if sample_floor > 0 else 0.0,
            "current_value": current.get(primary_key),
            "current_values": current,
            "recommended_value": recommended.get(primary_key),
            "recommended_values": recommended,
            "calibration_state": state,
            "calibration_reason": f"window_policy primary={primary_window} 기준 재평가: {reason}",
            "sample_floor_status": sample_floor_status,
            "apply_mode": apply_mode,
            "threshold_version": f"{family}:{apply_mode}:{sample_floor_status}",
            "window_policy_primary_applied": True,
            "decision_sample_window": primary_window,
        }
    )
    if primary_source_metrics:
        candidate["source_metrics"] = primary_source_metrics


def _build_window_policy_resolution(candidate: dict, cumulative_report: dict | None) -> dict:
    policy = candidate.get("window_policy") if isinstance(candidate.get("window_policy"), dict) else {}
    primary = _candidate_primary_window(candidate)
    sample_floor = _safe_int(candidate.get("sample_floor"), 0) or 0
    daily_sample = _safe_int(candidate.get("source_sample_count"), None)
    if daily_sample is None:
        daily_sample = _safe_int(candidate.get("sample_count"), 0) or 0
    primary_snapshot = _window_snapshot(cumulative_report, str(candidate.get("family") or ""), primary)
    primary_sample = _snapshot_relevant_sample_count(str(candidate.get("family") or ""), primary_snapshot)
    primary_source_context = _window_source_context(cumulative_report, primary)
    primary_source_metrics = _source_metrics_for_family(str(candidate.get("family") or ""), primary_source_context)
    primary_source_sample = _source_sample_count_for_family(str(candidate.get("family") or ""), primary_source_metrics)
    effective_primary_sample = max(
        [value for value in (primary_sample, primary_source_sample) if value is not None],
        default=None,
    )
    if primary == "daily_intraday":
        effective_primary_sample = daily_sample if effective_primary_sample is None else effective_primary_sample
    elif primary == "latest_report":
        effective_primary_sample = daily_sample if effective_primary_sample is None else effective_primary_sample
        if primary_source_sample is None:
            primary_source_sample = daily_sample
    snapshot_ready = bool(primary_snapshot.get("sample_ready")) if isinstance(primary_snapshot, dict) else False
    sample_count_ready = (
        effective_primary_sample is not None and effective_primary_sample >= sample_floor
        if sample_floor > 0
        else bool(effective_primary_sample)
    )
    primary_ready = snapshot_ready or sample_count_ready
    secondary: dict[str, dict[str, Any]] = {}
    for raw_window in policy.get("secondary") or []:
        window = _normalize_ai_sample_window(raw_window)
        if not window:
            continue
        snapshot = _window_snapshot(cumulative_report, str(candidate.get("family") or ""), window)
        sample = _snapshot_relevant_sample_count(str(candidate.get("family") or ""), snapshot)
        source_context = _window_source_context(cumulative_report, window)
        source_metrics = _source_metrics_for_family(str(candidate.get("family") or ""), source_context)
        source_sample = _source_sample_count_for_family(str(candidate.get("family") or ""), source_metrics)
        effective_sample = max([value for value in (sample, source_sample) if value is not None], default=None)
        secondary[window] = {
            "sample_count": effective_sample,
            "snapshot_sample_count": sample,
            "source_sample_count": source_sample,
            "sample_ready": bool(snapshot.get("sample_ready")) if isinstance(snapshot, dict) else None,
            "available": isinstance(snapshot, dict),
        }
    return {
        "primary": primary,
        "daily_only_allowed": bool(policy.get("daily_only_allowed")) if policy else True,
        "primary_sample_count": effective_primary_sample,
        "primary_snapshot_sample_count": primary_sample,
        "primary_source_sample_count": primary_source_sample,
        "primary_sample_ready": bool(primary_ready),
        "primary_snapshot_available": isinstance(primary_snapshot, dict),
        "primary_source_available": bool(primary_source_metrics),
        "primary_source_metrics": primary_source_metrics,
        "sample_floor": sample_floor,
        "secondary": secondary,
    }


def apply_window_policy_registry_to_report(report: dict, cumulative_report: dict | None) -> dict:
    candidates = report.get("calibration_candidates")
    if not isinstance(candidates, list):
        return report
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        resolution = _build_window_policy_resolution(candidate, cumulative_report)
        candidate["window_policy_resolution"] = resolution
        primary = resolution.get("primary")
        daily_only_allowed = bool(resolution.get("daily_only_allowed"))
        primary_ready = bool(resolution.get("primary_sample_ready"))
        changes_value_or_state = str(candidate.get("calibration_state") or "") in {"adjust_up", "adjust_down"}
        if (
            primary
            and primary not in {"daily_intraday", "latest_report"}
            and not daily_only_allowed
            and changes_value_or_state
            and not primary_ready
        ):
            candidate["calibration_state"] = "hold_sample"
            candidate["calibration_reason"] = (
                f"window_policy primary={primary} 표본/ready 미충족; daily trigger만으로 runtime 후보 승격 금지"
            )
            candidate["sample_floor_status"] = "window_policy_hold_sample"
            candidate["apply_mode"] = "report_only_calibration"
            candidate["runtime_apply_blocker"] = "window_policy_primary_not_ready"
            candidate["threshold_version"] = f"{candidate.get('family')}:{candidate.get('apply_mode', 'observe_only')}:window_policy_hold_sample"
        elif primary and primary != "daily_intraday" and primary_ready:
            primary_sample = _safe_int(resolution.get("primary_sample_count"), None)
            primary_snapshot = _window_snapshot(cumulative_report, str(candidate.get("family") or ""), str(primary))
            primary_source_metrics = (
                resolution.get("primary_source_metrics")
                if isinstance(resolution.get("primary_source_metrics"), dict)
                else {}
            )
            if primary_sample is not None:
                _refresh_candidate_from_primary_window(
                    candidate,
                    primary_snapshot=primary_snapshot,
                    primary_source_metrics=primary_source_metrics,
                    primary_sample_count=int(primary_sample),
                    primary_ready=primary_ready,
                    primary_window=str(primary),
                )
    report["window_policy_audit"] = _build_window_policy_audit(candidates)
    report["post_apply_attribution"] = _build_post_apply_attribution(candidates)
    report["safety_guard_pack"] = _build_safety_guard_pack(candidates)
    report["calibration_trigger_pack"] = _build_calibration_trigger_pack(candidates)
    return report


def _build_window_policy_audit(candidates: list[dict]) -> dict:
    items: list[dict] = []
    issue_counts: Counter[str] = Counter()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        family = str(candidate.get("family") or "")
        resolution = candidate.get("window_policy_resolution") if isinstance(candidate.get("window_policy_resolution"), dict) else {}
        primary = str(resolution.get("primary") or "")
        daily_only_allowed = bool(resolution.get("daily_only_allowed"))
        primary_ready = bool(resolution.get("primary_sample_ready"))
        primary_available = bool(resolution.get("primary_snapshot_available"))
        primary_source_available = bool(resolution.get("primary_source_available"))
        state = str(candidate.get("calibration_state") or "")
        sample_floor = _safe_int(candidate.get("sample_floor"), 0) or 0
        source_sample = _safe_int(candidate.get("source_sample_count"), 0) or 0
        issues: list[str] = []
        if (
            primary
            and primary not in {"daily_intraday", "latest_report"}
            and not daily_only_allowed
            and not primary_available
            and not primary_source_available
        ):
            issues.append("rolling_consumer_gap")
        snapshot_sample = _safe_int(resolution.get("primary_snapshot_sample_count"), None)
        source_window_sample = _safe_int(resolution.get("primary_source_sample_count"), None)
        snapshot_alignment_status = "aligned"
        snapshot_alignment_reason = "primary snapshot/source denominator aligned"
        if (
            primary
            and primary not in {"daily_intraday", "latest_report"}
            and source_window_sample is not None
            and source_window_sample >= sample_floor
            and (snapshot_sample is None or snapshot_sample < sample_floor)
        ):
            snapshot_alignment_status = "source_denominator_used"
            snapshot_alignment_reason = (
                "rolling source metrics supplied the registered primary denominator; "
                "threshold snapshot sample is rendering-only for this family/window"
            )
        if str(candidate.get("runtime_apply_blocker") or "") == "window_policy_primary_not_ready":
            issues.append("daily_only_leak_blocked")
        if (
            primary
            and primary not in {"daily_intraday", "latest_report"}
            and not daily_only_allowed
            and primary_ready
            and state == "hold_sample"
            and source_sample < sample_floor
        ):
            issues.append("rolling_ready_but_daily_source_hold_sample")
        denominator_keys = _sample_denominator_keys_for_family(family)
        if family in {"score65_74_recovery_probe", "position_sizing_cap_release", "position_sizing_dynamic_formula"} and not denominator_keys:
            issues.append("sample_denominator_missing")
        for issue in issues:
            issue_counts[issue] += 1
        items.append(
            {
                "family": family,
                "primary": primary,
                "daily_only_allowed": daily_only_allowed,
                "candidate_state": state,
                "source_sample_count": source_sample,
                "sample_floor": sample_floor,
                "primary_sample_count": resolution.get("primary_sample_count"),
                "primary_snapshot_sample_count": resolution.get("primary_snapshot_sample_count"),
                "primary_source_sample_count": resolution.get("primary_source_sample_count"),
                "primary_sample_ready": primary_ready,
                "primary_snapshot_available": primary_available,
                "primary_source_available": primary_source_available,
                "sample_denominator_keys": denominator_keys,
                "snapshot_alignment_status": snapshot_alignment_status,
                "snapshot_alignment_reason": snapshot_alignment_reason,
                "issues": issues,
            }
        )
    return {
        "status": "issues_found" if issue_counts else "pass",
        "issue_counts": dict(sorted(issue_counts.items())),
        "items": items,
    }


def _parse_ai_correction_response(ai_raw_response: Any) -> tuple[str, list[dict], list[str]]:
    if ai_raw_response in (None, "", b""):
        return ("unavailable", [], ["ai correction response not provided"])
    if isinstance(ai_raw_response, (str, bytes)):
        try:
            payload = json.loads(ai_raw_response)
        except Exception as exc:
            return ("parse_rejected", [], [f"AI response JSON parse failed: {exc}"])
    else:
        payload = ai_raw_response
    if not isinstance(payload, dict):
        return ("parse_rejected", [], ["AI response must be a JSON object"])
    allowed_top_keys = {"schema_version", "corrections"}
    unknown_top_keys = set(payload) - allowed_top_keys
    if unknown_top_keys:
        return ("parse_rejected", [], [f"AI response has unsupported top-level fields: {sorted(unknown_top_keys)}"])
    corrections = payload.get("corrections")
    if not isinstance(corrections, list):
        return ("parse_rejected", [], ["AI response must contain corrections list"])

    parsed: list[dict] = []
    allowed_item_keys = {
        "family",
        "anomaly_type",
        "ai_review_state",
        "correction_proposal",
        "correction_reason",
        "required_evidence",
        "risk_flags",
    }
    allowed_proposal_keys = {"proposed_state", "proposed_value", "anomaly_route", "sample_window"}
    for index, item in enumerate(corrections):
        if not isinstance(item, dict):
            return ("parse_rejected", [], [f"corrections[{index}] must be an object"])
        unknown_keys = set(item) - allowed_item_keys
        if unknown_keys:
            return ("parse_rejected", [], [f"corrections[{index}] has unsupported fields: {sorted(unknown_keys)}"])
        family = str(item.get("family") or "").strip()
        if not family:
            return ("parse_rejected", [], [f"corrections[{index}].family is required"])
        review_state = str(item.get("ai_review_state") or "correction_proposed").strip()
        if review_state not in AI_CORRECTION_ALLOWED_REVIEW_STATES:
            return ("parse_rejected", [], [f"corrections[{index}].ai_review_state is invalid: {review_state}"])
        proposal = item.get("correction_proposal") or {}
        if not isinstance(proposal, dict):
            return ("parse_rejected", [], [f"corrections[{index}].correction_proposal must be an object"])
        unknown_proposal_keys = set(proposal) - allowed_proposal_keys
        forbidden_proposal_keys = set(proposal) & AI_CORRECTION_FORBIDDEN_FIELDS
        if unknown_proposal_keys:
            return (
                "parse_rejected",
                [],
                [f"corrections[{index}].correction_proposal has unsupported fields: {sorted(unknown_proposal_keys)}"],
            )
        if forbidden_proposal_keys:
            return (
                "parse_rejected",
                [],
                [f"corrections[{index}].correction_proposal has forbidden fields: {sorted(forbidden_proposal_keys)}"],
            )
        proposed_state = proposal.get("proposed_state")
        if proposed_state not in (None, "") and str(proposed_state) not in AI_CORRECTION_ALLOWED_STATES:
            return ("parse_rejected", [], [f"corrections[{index}].proposed_state is invalid: {proposed_state}"])
        anomaly_route = proposal.get("anomaly_route")
        if anomaly_route not in (None, "") and str(anomaly_route) not in AI_CORRECTION_ALLOWED_ROUTES:
            return ("parse_rejected", [], [f"corrections[{index}].anomaly_route is invalid: {anomaly_route}"])
        sample_window = _normalize_ai_sample_window(proposal.get("sample_window"))
        if sample_window not in (None, "") and sample_window not in AI_CORRECTION_ALLOWED_SAMPLE_WINDOWS:
            return ("parse_rejected", [], [f"corrections[{index}].sample_window is invalid: {sample_window}"])
        required_evidence = item.get("required_evidence") or []
        risk_flags = item.get("risk_flags") or []
        if not isinstance(required_evidence, list) or not all(isinstance(value, str) for value in required_evidence):
            return ("parse_rejected", [], [f"corrections[{index}].required_evidence must be a string list"])
        if not isinstance(risk_flags, list) or not all(isinstance(value, str) for value in risk_flags):
            return ("parse_rejected", [], [f"corrections[{index}].risk_flags must be a string list"])
        parsed.append(
            {
                "family": family,
                "anomaly_type": str(item.get("anomaly_type") or "-"),
                "ai_review_state": review_state,
                "correction_proposal": {
                    key: _normalize_ai_sample_window(value) if key == "sample_window" else value
                    for key, value in proposal.items()
                },
                "correction_reason": str(item.get("correction_reason") or ""),
                "required_evidence": required_evidence,
                "risk_flags": risk_flags,
            }
        )
    return ("parsed", parsed, [])


def _current_numeric_step_bounds(candidate: dict) -> tuple[float | None, float | None]:
    lower = _safe_float(candidate.get("min_value"), None)
    upper = _safe_float(candidate.get("max_value"), None)
    step = _safe_float(candidate.get("max_step_per_day"), None)
    current = _safe_float(candidate.get("current_value"), None)
    if step is not None and current is not None:
        if lower is not None:
            lower = max(lower, current - step)
        else:
            lower = current - step
        if upper is not None:
            upper = min(upper, current + step)
        else:
            upper = current + step
    return lower, upper


def _guard_ai_correction_proposal(candidate: dict, proposal: dict) -> dict:
    proposed_state = proposal.get("proposed_state")
    proposed_state = str(proposed_state) if proposed_state not in (None, "") else None
    proposed_value = proposal.get("proposed_value")
    anomaly_route = proposal.get("anomaly_route")
    anomaly_route = str(anomaly_route) if anomaly_route not in (None, "") else None
    sample_window = _normalize_ai_sample_window(proposal.get("sample_window"))
    current_value = candidate.get("current_value")
    effective_state = proposed_state or candidate.get("calibration_state")
    effective_value = current_value
    clamped = False
    guard_reject_reason = ""
    guard_accepted = False
    route_action = "proposal_only"

    if anomaly_route == "instrumentation_gap":
        return {
            "guard_accepted": True,
            "guard_reject_reason": "",
            "effective_state": "hold_sample",
            "effective_value": current_value,
            "clamped": False,
            "anomaly_route": anomaly_route,
            "route_action": "exclude_from_threshold_candidate_review",
            "runtime_change": False,
        }

    if sample_window:
        allowed_windows = _allowed_sample_windows_for_candidate(candidate)
        if sample_window not in allowed_windows:
            return {
                "guard_accepted": False,
                "guard_reject_reason": f"sample_window_mismatch:{sample_window} not in {sorted(allowed_windows)}",
                "effective_state": "hold_sample",
                "effective_value": current_value,
                "clamped": False,
                "anomaly_route": anomaly_route,
                "route_action": "reject_or_hold_sample",
                "runtime_change": False,
            }

    policy = candidate.get("window_policy") if isinstance(candidate.get("window_policy"), dict) else {}
    sample_floor = _safe_int(candidate.get("sample_floor"), 0) or 0
    source_sample_count = _safe_int(candidate.get("source_sample_count"), 0) or 0
    needs_rolling_context = policy and not bool(policy.get("daily_only_allowed"))
    changes_value_or_state = (
        proposed_value not in (None, "")
        or proposed_state in {"adjust_up", "adjust_down"}
        or anomaly_route == "threshold_candidate"
    )
    if needs_rolling_context and 0 < source_sample_count < sample_floor and changes_value_or_state:
        return {
            "guard_accepted": False,
            "guard_reject_reason": (
                f"window_policy_blocks_single_case_live_candidate:{source_sample_count}/{sample_floor}"
            ),
            "effective_state": "hold_sample",
            "effective_value": current_value,
            "clamped": False,
            "anomaly_route": anomaly_route,
            "route_action": "hold_sample",
            "runtime_change": False,
        }

    if proposed_value not in (None, ""):
        if isinstance(current_value, bool):
            effective_value = bool(proposed_value)
            guard_accepted = True
        else:
            numeric_value = _safe_float(proposed_value, None)
            if numeric_value is None:
                return {
                    "guard_accepted": False,
                    "guard_reject_reason": "proposed_value_not_numeric_or_bool",
                    "effective_state": "hold_sample",
                    "effective_value": current_value,
                    "clamped": False,
                    "anomaly_route": anomaly_route,
                    "route_action": "reject_or_hold_sample",
                    "runtime_change": False,
                }
            lower, upper = _current_numeric_step_bounds(candidate)
            if lower is None or upper is None:
                return {
                    "guard_accepted": False,
                    "guard_reject_reason": "missing_bounds_for_value_proposal",
                    "effective_state": "hold_sample",
                    "effective_value": current_value,
                    "clamped": False,
                    "anomaly_route": anomaly_route,
                    "route_action": "reject_or_hold_sample",
                    "runtime_change": False,
                }
            effective_value = _clamp(numeric_value, lower, upper)
            clamped = effective_value != numeric_value
            guard_accepted = True
    elif proposed_state or anomaly_route:
        guard_accepted = True
    else:
        guard_reject_reason = "empty_proposal"

    if candidate.get("allowed_runtime_apply") is False and proposed_state in {"adjust_up", "adjust_down"}:
        guard_accepted = False
        guard_reject_reason = "runtime_apply_not_allowed_for_family"
        effective_state = "hold_sample"
        route_action = "report_only_hold"

    return {
        "guard_accepted": guard_accepted,
        "guard_reject_reason": guard_reject_reason,
        "effective_state": effective_state,
        "effective_value": effective_value,
        "clamped": clamped,
        "anomaly_route": anomaly_route,
        "route_action": route_action,
        "runtime_change": False,
    }


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _json_chars(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _strip_volatile_hash_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _strip_volatile_hash_fields(item)
            for key, item in value.items()
            if str(key) not in AI_CORRECTION_HASH_VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [_strip_volatile_hash_fields(item) for item in value]
    return value


def _json_content_sha256(value: Any) -> str:
    return _json_sha256(_strip_volatile_hash_fields(value))


def _compact_json_value(
    value: Any,
    *,
    max_chars: int,
    max_dict_keys: int = AI_CORRECTION_SOURCE_METRIC_TOP_N,
    max_list_items: int = AI_CORRECTION_LIST_ITEM_LIMIT,
    depth: int = 0,
) -> Any:
    current_chars = _json_chars(value)
    if current_chars <= max_chars:
        return value
    if depth >= 4:
        preview = json.dumps(value, ensure_ascii=False, default=str)[: max(200, max_chars - 300)]
        return {
            "_truncated": True,
            "original_type": type(value).__name__,
            "original_chars": current_chars,
            "full_hash": _json_sha256(value),
            "preview": preview,
        }
    if isinstance(value, dict):
        keys = list(value.keys())
        per_item_chars = max(600, max_chars // max(1, min(len(keys), max_dict_keys)))
        compact: dict[str, Any] = {}
        for key in keys[:max_dict_keys]:
            compact[str(key)] = _compact_json_value(
                value.get(key),
                max_chars=per_item_chars,
                max_dict_keys=max(4, max_dict_keys // 2),
                max_list_items=max(3, max_list_items // 2),
                depth=depth + 1,
            )
        if len(keys) > max_dict_keys:
            compact["_omitted_keys"] = [str(key) for key in keys[max_dict_keys : max_dict_keys + 20]]
        compact["_compact_meta"] = {
            "truncated": True,
            "original_type": "dict",
            "original_key_count": len(keys),
            "included_key_count": min(len(keys), max_dict_keys),
            "original_chars": current_chars,
            "full_hash": _json_sha256(value),
        }
        return compact
    if isinstance(value, list):
        per_item_chars = max(500, max_chars // max(1, min(len(value), max_list_items)))
        return {
            "_truncated": True,
            "original_type": "list",
            "original_count": len(value),
            "included_count": min(len(value), max_list_items),
            "original_chars": current_chars,
            "full_hash": _json_sha256(value),
            "items": [
                _compact_json_value(
                    item,
                    max_chars=per_item_chars,
                    max_dict_keys=max(4, max_dict_keys // 2),
                    max_list_items=max(3, max_list_items // 2),
                    depth=depth + 1,
                )
                for item in value[:max_list_items]
            ],
        }
    text = str(value)
    return {
        "_truncated": True,
        "original_type": type(value).__name__,
        "original_chars": current_chars,
        "full_hash": _json_sha256(value),
        "preview": text[: max(200, max_chars - 300)],
    }


def _cap_ai_context_section(section_name: str, value: Any) -> Any:
    max_chars = AI_CORRECTION_CONTEXT_SECTION_LIMITS.get(section_name, 10_000)
    compact = _compact_json_value(value, max_chars=max_chars)
    if _json_chars(compact) <= max_chars:
        return compact
    preview = json.dumps(compact, ensure_ascii=False, default=str)[: max(500, max_chars - 400)]
    return {
        "_truncated": True,
        "section": section_name,
        "original_chars": _json_chars(value),
        "compact_chars": _json_chars(compact),
        "full_hash": _json_sha256(value),
        "preview": preview,
    }


def _source_availability_summary(sources: Any) -> dict:
    if not isinstance(sources, dict):
        return {"source_count": 0, "sources": {}}
    compact_sources: dict[str, dict] = {}
    for name, meta in list(sources.items())[:30]:
        row = meta if isinstance(meta, dict) else {}
        compact_sources[str(name)] = {
            "exists": bool(row.get("exists")),
            "status": row.get("status"),
            "path": row.get("path"),
            "warning_count": len(row.get("warnings") or []) if isinstance(row.get("warnings"), list) else 0,
        }
    return {
        "source_count": len(sources),
        "included_count": len(compact_sources),
        "sources": compact_sources,
        "omitted_sources": [str(name) for name in list(sources.keys())[30:50]],
    }


def _candidate_source_metrics_summary(source_metrics: Any) -> Any:
    return _compact_json_value(
        source_metrics if source_metrics is not None else {},
        max_chars=2_500,
        max_dict_keys=AI_CORRECTION_SOURCE_METRIC_TOP_N,
        max_list_items=6,
    )


def _cumulative_family_window_context(cumulative_report: dict, families: set[str]) -> dict:
    snapshots = cumulative_report.get("threshold_snapshot_by_window")
    bundles = cumulative_report.get("calibration_source_bundle_by_window")
    result: dict[str, dict] = {}
    if isinstance(snapshots, dict):
        for window_name, window_snapshot in snapshots.items():
            if not isinstance(window_snapshot, dict):
                continue
            result[str(window_name)] = {
                family: _compact_json_value(window_snapshot.get(family), max_chars=2_500, max_dict_keys=10, max_list_items=6)
                for family in sorted(families)
                if isinstance(window_snapshot.get(family), dict)
            }
    source_metric_context: dict[str, Any] = {}
    if isinstance(bundles, dict):
        for window_name, bundle in bundles.items():
            if not isinstance(bundle, dict):
                continue
            source_metric_context[str(window_name)] = {
                "sources": _source_availability_summary(bundle.get("sources")),
                "source_metrics": _compact_json_value(
                    bundle.get("source_metrics") or {},
                    max_chars=5_000,
                    max_dict_keys=AI_CORRECTION_SOURCE_METRIC_TOP_N,
                    max_list_items=6,
                ),
                "warnings": list(bundle.get("warnings") or [])[:10],
            }
    return {
        "threshold_snapshot_by_window": result,
        "calibration_source_bundle_by_window": source_metric_context,
    }


def _finalize_ai_input_context_budget(context: dict) -> dict:
    context["_context_budget"] = {
        "total_char_limit": AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT,
        "section_char_limits": dict(AI_CORRECTION_CONTEXT_SECTION_LIMITS),
        "full_blob_policy": "hash_and_path_reference_only",
        "source_metrics_policy": f"compact_top_{AI_CORRECTION_SOURCE_METRIC_TOP_N}",
    }
    total_chars = _json_chars(context)
    if total_chars <= AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT:
        _refresh_ai_context_budget_counts(context, hard_cap_applied=False)
        return context

    for section_name in ("threshold_cycle_cumulative", "calibration_source_bundle", "trade_lifecycle_attribution", "recent_anomaly_report"):
        context[section_name] = _compact_json_value(context.get(section_name), max_chars=8_000, max_dict_keys=8, max_list_items=4)
        total_chars = _json_chars(context)
        if total_chars <= AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT:
            break
    if total_chars > AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT:
        context["recent_anomaly_report"] = {
            "_truncated": True,
            "reason": "total_context_hard_cap",
            "full_hash": _json_sha256(context.get("recent_anomaly_report")),
        }
        total_chars = _json_chars(context)

    _refresh_ai_context_budget_counts(context, hard_cap_applied=True)
    return context


def _refresh_ai_context_budget_counts(context: dict, *, hard_cap_applied: bool) -> None:
    budget = context.get("_context_budget")
    if not isinstance(budget, dict):
        return
    budget["section_char_counts"] = {
        key: _json_chars(value)
        for key, value in context.items()
        if key not in {"_context_budget"}
    }
    budget["hard_cap_applied"] = bool(hard_cap_applied)
    previous_chars = None
    for _ in range(4):
        current_chars = _json_chars(context)
        budget["input_context_chars"] = current_chars
        next_chars = _json_chars(context)
        if next_chars == current_chars or next_chars == previous_chars:
            budget["input_context_chars"] = next_chars
            return
        previous_chars = current_chars
    context["_context_budget"]["section_char_counts"] = {
        key: _json_chars(value)
        for key, value in context.items()
        if key not in {"_context_budget"}
    }
    budget["input_context_chars"] = _json_chars(context)


def _build_ai_correction_input_context(
    calibration_report: dict,
    cumulative_report: dict | None = None,
    *,
    source_calibration_report_path: str | None = None,
) -> dict:
    candidates = calibration_report.get("calibration_candidates") or []
    candidate_context = []
    for candidate in candidates if isinstance(candidates, list) else []:
        if not isinstance(candidate, dict):
            continue
        candidate_context.append(
            {
                "family": candidate.get("family"),
                "threshold_version": candidate.get("threshold_version"),
                "current_value": candidate.get("current_value"),
                "recommended_value": candidate.get("recommended_value"),
                "calibration_state": candidate.get("calibration_state"),
                "calibration_reason": candidate.get("calibration_reason"),
                "sample_count": candidate.get("sample_count"),
                "source_sample_count": candidate.get("source_sample_count"),
                "sample_floor": candidate.get("sample_floor"),
                "sample_window": candidate.get("sample_window"),
                "window_policy": candidate.get("window_policy"),
                "bounds": candidate.get("bounds"),
                "max_step_per_day": candidate.get("max_step_per_day"),
                "safety_revert_required": candidate.get("safety_revert_required"),
                "source_metrics_summary": _candidate_source_metrics_summary(candidate.get("source_metrics")),
                "source_metrics_full_hash": _json_sha256(candidate.get("source_metrics") or {}),
            }
        )
    candidate_families = {str(candidate.get("family") or "") for candidate in candidates if isinstance(candidate, dict)}
    cumulative_summary = {}
    if isinstance(cumulative_report, dict):
        cumulative_json_path, _ = cumulative_threshold_report_paths(str(cumulative_report.get("date") or calibration_report.get("date") or ""))
        cumulative_summary = {
            "date": cumulative_report.get("date"),
            "summary": cumulative_report.get("summary"),
            "family_window_context": _cumulative_family_window_context(cumulative_report, candidate_families),
            "completed_by_source": _compact_json_value(
                cumulative_report.get("completed_by_source") or {},
                max_chars=6_000,
                max_dict_keys=AI_CORRECTION_SOURCE_METRIC_TOP_N,
                max_list_items=6,
            ),
            "source_flags": _compact_json_value(
                cumulative_report.get("source_flags") or {},
                max_chars=4_000,
                max_dict_keys=AI_CORRECTION_SOURCE_METRIC_TOP_N,
                max_list_items=6,
            ),
            "warnings": list(cumulative_report.get("warnings") or [])[:20],
            "full_report_reference": {
                "path": str(cumulative_json_path),
                "full_hash": _json_content_sha256(cumulative_report),
                "full_chars": _json_chars(cumulative_report),
            },
        }
    calibration_source_bundle = calibration_report.get("calibration_source_bundle") or {}
    trade_lifecycle_attribution = calibration_report.get("trade_lifecycle_attribution") or {}
    context = {
        "context_schema_version": 2,
        "calibration_candidates": _cap_ai_context_section("calibration_candidates", candidate_context),
        "calibration_source_bundle": _cap_ai_context_section(
            "calibration_source_bundle",
            {
                "schema_version": calibration_source_bundle.get("schema_version") if isinstance(calibration_source_bundle, dict) else None,
                "target_date": calibration_source_bundle.get("target_date") if isinstance(calibration_source_bundle, dict) else None,
                "purpose": calibration_source_bundle.get("purpose") if isinstance(calibration_source_bundle, dict) else None,
                "sources": _source_availability_summary(calibration_source_bundle.get("sources") if isinstance(calibration_source_bundle, dict) else {}),
                "source_metrics": _compact_json_value(
                    calibration_source_bundle.get("source_metrics") if isinstance(calibration_source_bundle, dict) else {},
                    max_chars=8_000,
                    max_dict_keys=AI_CORRECTION_SOURCE_METRIC_TOP_N,
                    max_list_items=6,
                ),
                "report_only_cleanup_audit": _compact_json_value(
                    calibration_source_bundle.get("report_only_cleanup_audit") if isinstance(calibration_source_bundle, dict) else {},
                    max_chars=2_000,
                    max_dict_keys=8,
                    max_list_items=4,
                ),
                "warnings": list(calibration_source_bundle.get("warnings") or [])[:20] if isinstance(calibration_source_bundle, dict) else [],
                "full_bundle_reference": {
                    "path": source_calibration_report_path or calibration_report.get("source_report"),
                    "full_hash": _json_content_sha256(calibration_source_bundle),
                    "full_chars": _json_chars(calibration_source_bundle),
                },
            },
        ),
        "trade_lifecycle_attribution": _cap_ai_context_section(
            "trade_lifecycle_attribution",
            {
                "schema_version": trade_lifecycle_attribution.get("schema_version") if isinstance(trade_lifecycle_attribution, dict) else None,
                "status": trade_lifecycle_attribution.get("status") if isinstance(trade_lifecycle_attribution, dict) else None,
                "runtime_change": trade_lifecycle_attribution.get("runtime_change") if isinstance(trade_lifecycle_attribution, dict) else None,
                "join_key": trade_lifecycle_attribution.get("join_key") if isinstance(trade_lifecycle_attribution, dict) else None,
                "phase_counts": trade_lifecycle_attribution.get("phase_counts") if isinstance(trade_lifecycle_attribution, dict) else {},
                "primary_type_counts": trade_lifecycle_attribution.get("primary_type_counts") if isinstance(trade_lifecycle_attribution, dict) else {},
                "decision_source_outcomes": _compact_json_value(
                    trade_lifecycle_attribution.get("decision_source_outcomes") if isinstance(trade_lifecycle_attribution, dict) else {},
                    max_chars=4_000,
                    max_dict_keys=10,
                    max_list_items=6,
                ),
                "exit_rule_outcomes": _compact_json_value(
                    trade_lifecycle_attribution.get("exit_rule_outcomes") if isinstance(trade_lifecycle_attribution, dict) else {},
                    max_chars=4_000,
                    max_dict_keys=10,
                    max_list_items=6,
                ),
                "family_views": _compact_json_value(
                    trade_lifecycle_attribution.get("family_views") if isinstance(trade_lifecycle_attribution, dict) else {},
                    max_chars=4_000,
                    max_dict_keys=10,
                    max_list_items=6,
                ),
                "examples": _compact_json_value(
                    trade_lifecycle_attribution.get("examples") if isinstance(trade_lifecycle_attribution, dict) else [],
                    max_chars=3_000,
                    max_dict_keys=8,
                    max_list_items=5,
                ),
                "records_reference": {
                    "record_count": len(trade_lifecycle_attribution.get("records") or []) if isinstance(trade_lifecycle_attribution, dict) and isinstance(trade_lifecycle_attribution.get("records"), list) else 0,
                    "records_hash": _json_sha256(trade_lifecycle_attribution.get("records") if isinstance(trade_lifecycle_attribution, dict) else []),
                },
            },
        ),
        "threshold_cycle_cumulative": _cap_ai_context_section("threshold_cycle_cumulative", cumulative_summary),
        "recent_anomaly_report": _cap_ai_context_section(
            "recent_anomaly_report",
            {
                "source_bundle_reports": _source_availability_summary(calibration_source_bundle.get("sources") if isinstance(calibration_source_bundle, dict) else {}),
                "source_metrics_summary": _compact_json_value(
                    calibration_source_bundle.get("source_metrics") if isinstance(calibration_source_bundle, dict) else {},
                    max_chars=6_000,
                    max_dict_keys=AI_CORRECTION_SOURCE_METRIC_TOP_N,
                    max_list_items=6,
                ),
            },
        ),
        "source_artifact_references": {
            "calibration_report": {
                "path": source_calibration_report_path or calibration_report.get("source_report"),
                "full_hash": _json_content_sha256(calibration_report),
                "full_chars": _json_chars(calibration_report),
            },
            "cumulative_report": {
                "path": str(cumulative_threshold_report_paths(str(cumulative_report.get("date")))[0])
                if isinstance(cumulative_report, dict) and cumulative_report.get("date")
                else None,
                "full_hash": _json_content_sha256(cumulative_report or {}),
                "full_chars": _json_chars(cumulative_report or {}),
            },
        },
    }
    return _finalize_ai_input_context_budget(context)


def _gemini_key_sort_key(name: str) -> tuple[int, str]:
    suffix = name.replace("GEMINI_API_KEY", "", 1).lstrip("_")
    if suffix == "":
        return (1, name)
    try:
        return (int(suffix), name)
    except ValueError:
        return (999, name)


def _load_threshold_ai_gemini_keys() -> list[tuple[str, str]]:
    target_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    keys: list[tuple[str, str]] = []
    for name, value in sorted(payload.items(), key=lambda item: _gemini_key_sort_key(str(item[0]))):
        if not str(name).startswith("GEMINI_API_KEY"):
            continue
        if value in (None, "", "-"):
            continue
        keys.append((str(name), str(value)))
    return keys


def _openai_key_sort_key(name: str) -> tuple[int, str]:
    suffix = name.replace("OPENAI_API_KEY", "", 1).lstrip("_")
    if suffix == "":
        return (1, name)
    try:
        return (int(suffix), name)
    except ValueError:
        return (999, name)


def _load_threshold_ai_openai_keys() -> list[tuple[str, str]]:
    target_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    keys: list[tuple[str, str]] = []
    for name, value in sorted(payload.items(), key=lambda item: _openai_key_sort_key(str(item[0]))):
        if not str(name).startswith("OPENAI_API_KEY"):
            continue
        if value in (None, "", "-"):
            continue
        keys.append((str(name), str(value)))
    return keys


def _threshold_ai_openai_model_sequence() -> list[str]:
    primary = str(getattr(TRADING_RULES, "GPT_THRESHOLD_CORRECTION_MODEL", "") or "gpt-5.5").strip()
    fallback = getattr(
        TRADING_RULES,
        "GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS",
        ("gpt-5.4", "gpt-5.4-mini"),
    )
    if isinstance(fallback, str):
        fallback_models = [item.strip() for item in fallback.split(",") if item.strip()]
    else:
        fallback_models = [str(item).strip() for item in (fallback or ()) if str(item).strip()]
    models: list[str] = []
    for model in [primary, *fallback_models]:
        if model and model not in models:
            models.append(model)
    return models or ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini"]


def _build_ai_correction_prompt(input_context: dict) -> str:
    return (
        "너는 threshold-cycle calibration AI reviewer + anomaly corrector다.\n"
        "역할은 수정안 제안까지이며 env/code/runtime 직접 변경 명령을 내면 안 된다.\n"
        "최종 source of truth는 deterministic calibration guard다.\n\n"
        "허용 제안:\n"
        "- proposed_state: adjust_up|adjust_down|hold|hold_sample|freeze\n"
        "- proposed_value: family bounds와 max_step_per_day 안에서 검증될 후보값\n"
        "- anomaly_route: threshold_candidate|incident|instrumentation_gap|normal_drift\n"
        "- sample_window: daily_intraday|rolling_5d|rolling_10d|cumulative\n\n"
        "금지:\n"
        "- env/code/runtime 직접 변경\n"
        "- 장중 threshold mutation\n"
        "- safety guard 우회 또는 safety_revert_required 변경\n"
        "- 단일 사례 기반 live enable 확정\n\n"
        "반드시 JSON only로 출력한다. schema 외 field를 넣지 않는다:\n"
        "{\n"
        '  "schema_version": 1,\n'
        '  "corrections": [\n'
        "    {\n"
        '      "family": "soft_stop_whipsaw_confirmation",\n'
        '      "anomaly_type": "late_rebound|defer_cost|entry_drought|instrumentation_gap|normal_drift",\n'
        '      "ai_review_state": "agree|correction_proposed|caution|insufficient_context|safety_concern|unavailable",\n'
        '      "correction_proposal": {\n'
        '        "proposed_state": "adjust_up|adjust_down|hold|hold_sample|freeze",\n'
        '        "proposed_value": 60,\n'
        '        "anomaly_route": "threshold_candidate|incident|instrumentation_gap|normal_drift",\n'
        '        "sample_window": "daily_intraday|rolling_5d|rolling_10d|cumulative"\n'
        "      },\n"
        '      "correction_reason": "1~2 sentence reason",\n'
        '      "required_evidence": ["evidence name"],\n'
        '      "risk_flags": ["risk flag"]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "[입력]\n"
        f"{json.dumps(input_context, ensure_ascii=False, indent=2)}"
    )


def _build_openai_ai_correction_instructions(run_phase: str) -> str:
    reasoning_mode = "intraday calibration pass" if str(run_phase) == "intraday" else "postclose calibration pass"
    return (
        "You are the threshold-cycle calibration AI reviewer and anomaly correction proposer.\n"
        f"Run phase: {reasoning_mode}.\n"
        "Your authority is proposal-only. You must not command env, code, runtime, restart, or intraday threshold mutation.\n"
        "The deterministic calibration guard remains the final source of truth.\n\n"
        "Control rules:\n"
        "- Propose only adjust_up, adjust_down, hold, hold_sample, or freeze.\n"
        "- Propose threshold values only as candidates; guard will clamp/reject by family bounds and max_step_per_day.\n"
        "- Route anomalies only as threshold_candidate, incident, instrumentation_gap, or normal_drift.\n"
        "- Use sample windows only as daily_intraday, rolling_5d, rolling_10d, or cumulative.\n"
        "- Never change safety_revert_required and never infer live enable from a single case.\n"
        "- Preserve raw enum labels, family ids, ticker names, field names, and quoted evidence exactly.\n\n"
        "Korean domain glossary for interpretation only:\n"
        "- 수급 = order-flow pressure\n"
        "- 호가 = order book quote/depth\n"
        "- 체결강도 = execution strength\n"
        "- 틱가속 = tick acceleration\n"
        "- 매수압 = buy pressure\n"
        "- 휩쏘 = whipsaw rebound\n"
        "- 소프트손절 = soft stop\n"
        "- 물타기 = averaging down / REVERSAL_ADD\n"
        "- 불타기 = pyramiding / PYRAMID\n\n"
        "Return only JSON that conforms to the strict threshold_ai_correction_v1 schema."
    )


def _extract_openai_response_text(response: Any) -> str:
    raw_text = str(getattr(response, "output_text", "") or "").strip()
    if raw_text:
        return raw_text
    fragments: list[str] = []
    for item in list(getattr(response, "output", []) or []):
        content_items = item.get("content", []) if isinstance(item, dict) else getattr(item, "content", [])
        for content in list(content_items or []):
            if isinstance(content, dict):
                text_value = content.get("text") or content.get("value")
            else:
                text_value = getattr(content, "text", None) or getattr(content, "value", None)
            if text_value:
                fragments.append(str(text_value))
    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip()).strip()


def _get_usage_value(usage: Any, *names: str) -> int | None:
    if usage is None:
        return None
    for name in names:
        value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
        parsed = _safe_int(value, None)
        if parsed is not None:
            return parsed
    return None


def _response_usage_telemetry(response: Any) -> dict:
    usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)
    input_tokens = _get_usage_value(usage, "input_tokens", "prompt_tokens", "prompt_token_count")
    output_tokens = _get_usage_value(usage, "output_tokens", "completion_tokens", "candidates_token_count")
    total_tokens = _get_usage_value(usage, "total_tokens", "total_token_count")
    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = (input_tokens or 0) + (output_tokens or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _threshold_ai_estimated_cost(model_name: str, input_tokens: int | None, output_tokens: int | None) -> tuple[float | None, str]:
    input_rate = _safe_float(os.getenv("KORSTOCKSCAN_THRESHOLD_AI_INPUT_COST_PER_1M_USD"), None)
    output_rate = _safe_float(os.getenv("KORSTOCKSCAN_THRESHOLD_AI_OUTPUT_COST_PER_1M_USD"), None)
    if input_tokens is None or output_tokens is None:
        return None, "missing_token_usage"
    if input_rate is None or output_rate is None:
        return None, "missing_price_contract"
    estimated = ((input_tokens * input_rate) + (output_tokens * output_rate)) / 1_000_000
    return round(float(estimated), 8), "estimated_from_env_price_contract"


def _call_openai_threshold_ai_correction(input_context: dict, *, run_phase: str) -> tuple[str | None, dict]:
    try:
        from openai import OpenAI, RateLimitError
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}

    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured"}

    model_sequence = _threshold_ai_openai_model_sequence()
    reasoning_effort = "medium" if str(run_phase) == "intraday" else "high"
    user_input = json.dumps(input_context, ensure_ascii=False, indent=2, default=str)
    instructions = _build_openai_ai_correction_instructions(run_phase)
    input_context_hash = _json_sha256(input_context)
    input_context_chars = len(user_input)
    prompt_chars = len(instructions) + input_context_chars
    errors: list[dict] = []
    attempted_key_names: list[str] = []
    attempted_model_names: list[str] = []
    for model_index, model_name in enumerate(model_sequence, start=1):
        for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
            attempted_key_names.append(key_name)
            if model_name not in attempted_model_names:
                attempted_model_names.append(model_name)
            started = time.monotonic()
            try:
                client = OpenAI(api_key=api_key)
                response = client.responses.create(
                    model=model_name,
                    instructions=instructions,
                    input=user_input,
                    text={
                        "format": build_openai_response_text_format("threshold_ai_correction_v1"),
                        "verbosity": "low",
                    },
                    reasoning={"effort": reasoning_effort},
                    store=False,
                    metadata={
                        "endpoint_name": "threshold_ai_correction",
                        "schema_name": "threshold_ai_correction_v1",
                        "run_phase": str(run_phase or "-"),
                    },
                    timeout=180,
                )
                elapsed_ms = int(round((time.monotonic() - started) * 1000))
                response_text = _extract_openai_response_text(response)
                usage = _response_usage_telemetry(response)
                estimated_cost, cost_status = _threshold_ai_estimated_cost(
                    model_name,
                    usage.get("input_tokens"),
                    usage.get("output_tokens"),
                )
                return response_text, {
                    "provider": "openai",
                    "status": "success",
                    "new_provider_call": True,
                    "key_name": key_name,
                    "attempt_index": attempt_index,
                    "model_index": model_index,
                    "configured_key_count": len(api_keys),
                    "attempted_key_count": len(attempted_key_names),
                    "attempted_keys": len(attempted_key_names),
                    "attempted_key_names": attempted_key_names,
                    "configured_model_count": len(model_sequence),
                    "attempted_model_count": len(attempted_model_names),
                    "attempted_models": attempted_model_names,
                    "configured_models": model_sequence,
                    "model": model_name,
                    "schema_name": "threshold_ai_correction_v1",
                    "reasoning_effort": reasoning_effort,
                    "prompt_chars": prompt_chars,
                    "input_context_chars": input_context_chars,
                    "input_context_hash": input_context_hash,
                    "elapsed_ms": elapsed_ms,
                    "output_chars": len(response_text),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "estimated_cost": estimated_cost,
                    "estimated_cost_usd": estimated_cost,
                    "cost_estimate_status": cost_status,
                }
            except RateLimitError as exc:
                errors.append({"key_name": key_name, "model": model_name, "error": str(exc)})
                continue
            except Exception as exc:
                errors.append({"key_name": key_name, "model": model_name, "error": str(exc)})
                continue
    return None, {
        "provider": "openai",
        "status": "failed",
        "new_provider_call": True,
        "configured_key_count": len(api_keys),
        "attempted_key_count": len(attempted_key_names),
        "attempted_keys": len(attempted_key_names),
        "attempted_key_names": attempted_key_names,
        "configured_model_count": len(model_sequence),
        "attempted_model_count": len(attempted_model_names),
        "attempted_models": attempted_model_names,
        "configured_models": model_sequence,
        "schema_name": "threshold_ai_correction_v1",
        "reasoning_effort": reasoning_effort,
        "prompt_chars": prompt_chars,
        "input_context_chars": input_context_chars,
        "input_context_hash": input_context_hash,
        "output_chars": 0,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "estimated_cost": None,
        "estimated_cost_usd": None,
        "cost_estimate_status": "no_successful_response",
        "errors": errors,
    }


def _call_gemini_threshold_ai_correction(input_context: dict) -> tuple[str | None, dict]:
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return None, {"provider": "gemini", "status": "unavailable", "reason": f"google.genai import failed: {exc}"}

    api_keys = _load_threshold_ai_gemini_keys()
    if not api_keys:
        return None, {"provider": "gemini", "status": "unavailable", "reason": "GEMINI_API_KEY not configured"}

    model_name = str(getattr(TRADING_RULES, "AI_MODEL_TIER3", "") or "models/gemini-3.1-pro-preview-customtools")
    prompt = _build_ai_correction_prompt(input_context)
    input_context_hash = _json_sha256(input_context)
    input_context_chars = _json_chars(input_context)
    prompt_chars = len(prompt)
    errors: list[dict] = []
    attempted_key_names: list[str] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        attempted_key_names.append(key_name)
        started = time.monotonic()
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            response_text = str(response.text or "")
            elapsed_ms = int(round((time.monotonic() - started) * 1000))
            usage = _response_usage_telemetry(response)
            estimated_cost, cost_status = _threshold_ai_estimated_cost(
                model_name,
                usage.get("input_tokens"),
                usage.get("output_tokens"),
            )
            return response_text, {
                "provider": "gemini",
                "status": "success",
                "new_provider_call": True,
                "key_name": key_name,
                "attempt_index": attempt_index,
                "configured_key_count": len(api_keys),
                "attempted_key_count": len(attempted_key_names),
                "attempted_keys": len(attempted_key_names),
                "attempted_key_names": attempted_key_names,
                "model": model_name,
                "prompt_chars": prompt_chars,
                "input_context_chars": input_context_chars,
                "input_context_hash": input_context_hash,
                "elapsed_ms": elapsed_ms,
                "output_chars": len(response_text),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "estimated_cost": estimated_cost,
                "estimated_cost_usd": estimated_cost,
                "cost_estimate_status": cost_status,
            }
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {
        "provider": "gemini",
        "status": "failed",
        "new_provider_call": True,
        "configured_key_count": len(api_keys),
        "attempted_key_count": len(attempted_key_names),
        "attempted_keys": len(attempted_key_names),
        "attempted_key_names": attempted_key_names,
        "model": model_name,
        "prompt_chars": prompt_chars,
        "input_context_chars": input_context_chars,
        "input_context_hash": input_context_hash,
        "output_chars": 0,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "estimated_cost": None,
        "estimated_cost_usd": None,
        "cost_estimate_status": "no_successful_response",
        "errors": errors,
    }


def build_threshold_cycle_ai_correction_report(
    calibration_report: dict,
    *,
    ai_raw_response: Any | None = None,
    cumulative_report: dict | None = None,
    source_calibration_report_path: str | None = None,
    ai_provider_status: dict | None = None,
    ai_input_context: dict | None = None,
) -> dict:
    target_date = str(calibration_report.get("date") or date.today().isoformat())
    meta = calibration_report.get("meta") if isinstance(calibration_report.get("meta"), dict) else {}
    run_phase = str(calibration_report.get("run_phase") or meta.get("calibration_run_phase") or "postclose")
    candidates = calibration_report.get("calibration_candidates") or []
    candidates = candidates if isinstance(candidates, list) else []
    input_context = ai_input_context or _build_ai_correction_input_context(
        calibration_report,
        cumulative_report,
        source_calibration_report_path=source_calibration_report_path,
    )
    input_context_hash = _json_sha256(input_context)
    input_context_chars = _json_chars(input_context)
    provider_status = dict(ai_provider_status or {"provider": "none", "status": "not_requested"})
    provider_status.setdefault("input_context_hash", input_context_hash)
    provider_status.setdefault("input_context_chars", input_context_chars)
    provider_status.setdefault("prompt_chars", input_context_chars)
    provider_status.setdefault("output_chars", len(str(ai_raw_response or "")))
    provider_status.setdefault("input_tokens", None)
    provider_status.setdefault("output_tokens", None)
    provider_status.setdefault("total_tokens", None)
    provider_status.setdefault("estimated_cost", None)
    provider_status.setdefault("estimated_cost_usd", provider_status.get("estimated_cost"))
    provider_status.setdefault("cost_estimate_status", "not_available")
    ai_status, proposals, parse_warnings = _parse_ai_correction_response(ai_raw_response)
    proposals_by_family = {str(item.get("family")): item for item in proposals if isinstance(item, dict)}

    items: list[dict] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        family = str(candidate.get("family") or "")
        proposal_item = proposals_by_family.get(family)
        if proposal_item:
            correction_proposal = proposal_item.get("correction_proposal") or {}
            guard_decision = _guard_ai_correction_proposal(candidate, correction_proposal)
            ai_review_state = proposal_item.get("ai_review_state") or "correction_proposed"
            anomaly_type = proposal_item.get("anomaly_type") or "-"
            correction_reason = proposal_item.get("correction_reason") or ""
            required_evidence = proposal_item.get("required_evidence") or []
            risk_flags = proposal_item.get("risk_flags") or []
        else:
            correction_proposal = {}
            guard_decision = {
                "guard_accepted": False,
                "guard_reject_reason": "ai_unavailable" if ai_status == "unavailable" else "ai_proposal_missing_for_family",
                "effective_state": candidate.get("calibration_state"),
                "effective_value": candidate.get("current_value"),
                "clamped": False,
                "anomaly_route": None,
                "route_action": "deterministic_only",
                "runtime_change": False,
            }
            ai_review_state = "unavailable" if ai_status != "parsed" else "insufficient_context"
            anomaly_type = "-"
            correction_reason = ""
            required_evidence = []
            risk_flags = []

        item = {
            "family": family,
            "threshold_version": candidate.get("threshold_version"),
            "anomaly_type": anomaly_type,
            "ai_review_state": ai_review_state,
            "correction_proposal": {
                "ai_proposed_value": correction_proposal.get("proposed_value"),
                "ai_proposed_state": correction_proposal.get("proposed_state"),
                "ai_anomaly_route": correction_proposal.get("anomaly_route"),
                "ai_sample_window": correction_proposal.get("sample_window"),
                "ai_required_evidence": required_evidence,
            },
            "correction_reason": correction_reason,
            "required_evidence": required_evidence,
            "risk_flags": risk_flags,
            "guard_decision": guard_decision,
            "guard_accepted": bool(guard_decision.get("guard_accepted")),
            "guard_reject_reason": guard_decision.get("guard_reject_reason"),
            "deterministic_state": candidate.get("calibration_state"),
            "deterministic_value": candidate.get("recommended_value"),
            "final_source_of_truth": "deterministic_calibration_guard",
            "runtime_change": False,
        }
        items.append(item)

    return {
        "schema_version": THRESHOLD_AI_CORRECTION_SCHEMA_VERSION,
        "report_type": "threshold_cycle_ai_correction",
        "date": target_date,
        "run_phase": run_phase,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "runtime_change": False,
        "ai_status": ai_status,
        "ai_provider_status": provider_status,
        "input_context_hash": input_context_hash,
        "ai_input_context_hash": input_context_hash,
        "ai_input_context_chars": input_context_chars,
        "ai_input_context_budget": input_context.get("_context_budget") if isinstance(input_context, dict) else {},
        "parse_warnings": parse_warnings,
        "policy": {
            "authority": "proposal_only",
            "final_source_of_truth": "deterministic_calibration_guard",
            "runtime_change": False,
            "forbidden": [
                "env/code/runtime direct change",
                "intraday threshold mutation",
                "safety guard bypass",
                "safety_revert_required override",
                "single-case live enable finalization",
            ],
        },
        "prompt_contract": {
            "input_sections": [
                "calibration_candidates",
                "calibration_source_bundle",
                "trade_lifecycle_attribution",
                "threshold_cycle_cumulative",
                "recent_anomaly_report",
            ],
            "output_schema": {
                "schema_version": THRESHOLD_AI_CORRECTION_SCHEMA_VERSION,
                "top_level_fields": ["schema_version", "corrections"],
                "correction_fields": [
                    "family",
                    "anomaly_type",
                    "ai_review_state",
                    "correction_proposal",
                    "correction_reason",
                    "required_evidence",
                    "risk_flags",
                ],
                "allowed_proposal_fields": ["proposed_state", "proposed_value", "anomaly_route", "sample_window"],
            },
        },
        "ai_input_context": input_context,
        "source_reports": {
            "calibration_report": source_calibration_report_path or calibration_report.get("source_report"),
            "cumulative_report": (cumulative_report or {}).get("report_path") if isinstance(cumulative_report, dict) else None,
        },
        "candidate_count": len(candidates),
        "items": items,
    }


def render_threshold_cycle_ai_correction_markdown(report: dict) -> str:
    provider_status = report.get("ai_provider_status") if isinstance(report.get("ai_provider_status"), dict) else {}
    lines = [
        f"# Threshold Cycle AI Correction - {report.get('date')} {report.get('run_phase')}",
        "",
        f"- AI status: `{report.get('ai_status')}`",
        "- Authority: proposal-only; deterministic calibration guard is the source of truth.",
        "- Runtime change: `false`",
        f"- Input context chars: `{report.get('ai_input_context_chars') or provider_status.get('input_context_chars') or '-'}`",
        f"- Input context hash: `{report.get('ai_input_context_hash') or provider_status.get('input_context_hash') or '-'}`",
        f"- Provider status: `{provider_status.get('provider') or '-'} / {provider_status.get('status') or '-'}`",
        f"- Usage: input_tokens=`{provider_status.get('input_tokens')}`, output_tokens=`{provider_status.get('output_tokens')}`, total_tokens=`{provider_status.get('total_tokens')}`, elapsed_ms=`{provider_status.get('elapsed_ms')}`",
        f"- Cost: estimated_cost_usd=`{provider_status.get('estimated_cost_usd')}`, status=`{provider_status.get('cost_estimate_status') or provider_status.get('incremental_cost_status') or '-'}`",
        "",
        "| family | ai_state | route | proposal | guard | reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report.get("items") or []:
        proposal = item.get("correction_proposal") or {}
        guard = item.get("guard_decision") or {}
        proposal_text = (
            f"state={proposal.get('ai_proposed_state') or '-'}, "
            f"value={_markdown_value(proposal.get('ai_proposed_value'))}, "
            f"window={proposal.get('ai_sample_window') or '-'}"
        )
        guard_text = (
            f"accepted={bool(guard.get('guard_accepted'))}, "
            f"effective_state={guard.get('effective_state') or '-'}, "
            f"effective_value={_markdown_value(guard.get('effective_value'))}, "
            f"runtime_change={bool(guard.get('runtime_change'))}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(item.get("family")),
                    _markdown_value(item.get("ai_review_state")),
                    _markdown_value(proposal.get("ai_anomaly_route")),
                    proposal_text,
                    guard_text,
                    _markdown_value(item.get("guard_reject_reason") or item.get("correction_reason")),
                ]
            )
            + " |"
        )
    if report.get("parse_warnings"):
        lines.extend(["", "## Parse Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.get("parse_warnings") or [])
    lines.append("")
    return "\n".join(lines)


def save_threshold_cycle_ai_correction_report(report: dict) -> tuple[Path, Path]:
    target_date = str(report.get("date") or date.today().isoformat())
    run_phase = str(report.get("run_phase") or "postclose")
    json_path, md_path = threshold_ai_review_paths(target_date, run_phase)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_threshold_cycle_ai_correction_markdown(report), encoding="utf-8")
    return json_path, md_path


def _load_reusable_threshold_ai_review(path: Path, *, input_context_hash: str) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("ai_status") or "").lower() != "parsed":
        return None
    if str(payload.get("schema_name") or payload.get("schema_version") or "") not in {
        str(THRESHOLD_AI_CORRECTION_SCHEMA_VERSION),
        "threshold_ai_correction_v1",
    }:
        provider_status = payload.get("ai_provider_status") if isinstance(payload.get("ai_provider_status"), dict) else {}
        if str(provider_status.get("schema_name") or "") != "threshold_ai_correction_v1":
            return None
    provider_status_payload = payload.get("ai_provider_status") if isinstance(payload.get("ai_provider_status"), dict) else {}
    existing_hash = payload.get("input_context_hash") or payload.get("ai_input_context_hash") or provider_status_payload.get("input_context_hash")
    if str(existing_hash or "") != str(input_context_hash):
        return None
    provider_status = dict(payload.get("ai_provider_status") or {})
    provider_status["status"] = "reused_valid_artifact"
    provider_status["reuse_source_path"] = str(path)
    provider_status["reused_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    provider_status["new_provider_call"] = False
    provider_status.setdefault("input_context_hash", input_context_hash)
    provider_status["estimated_incremental_cost"] = 0.0
    provider_status["estimated_incremental_cost_usd"] = 0.0
    provider_status["incremental_cost_status"] = "reused_no_new_provider_call"
    payload["ai_provider_status"] = provider_status
    payload["reuse_guard"] = {
        "enabled": True,
        "status": "reused",
        "source_path": str(path),
        "input_context_hash": input_context_hash,
        "schema_name": "threshold_ai_correction_v1",
    }
    payload["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return payload


def _markdown_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _best_action_row(bucket: dict) -> dict:
    best_action = bucket.get("best_action")
    actions = bucket.get("actions") if isinstance(bucket.get("actions"), list) else []
    for action in actions:
        if action.get("action") == best_action:
            return action
    return {}


MATRIX_COUNTERFACTUAL_ACTIONS = ("exit_only", "avg_down_wait", "pyramid_wait")
MATRIX_COUNTERFACTUAL_PROXY_ACTIONS = ("hold_defer", *MATRIX_COUNTERFACTUAL_ACTIONS)


def _normalize_counterfactual_proxy_action(value: Any) -> str:
    token = str(value or "").strip().lower()
    if not token:
        return "-"
    normalized = token.replace("-", "_").replace(" ", "_")
    aliases = {
        "hold": "hold_defer",
        "hold_action": "hold_defer",
        "hold_defer": "hold_defer",
        "hold_wait": "hold_defer",
        "continue_hold": "hold_defer",
        "wait": "hold_defer",
        "wait_hold": "hold_defer",
        "defer_exit": "hold_defer",
        "exit": "exit_only",
        "exit_action": "exit_only",
        "exit_now": "exit_only",
        "exit_only": "exit_only",
        "sell": "exit_only",
        "sell_close": "exit_only",
        "trim": "exit_only",
        "drop": "exit_only",
        "avg_down": "avg_down_wait",
        "avg_down_wait": "avg_down_wait",
        "reversal_add": "avg_down_wait",
        "reversal_add_wait": "avg_down_wait",
        "pyramid": "pyramid_wait",
        "pyramid_wait": "pyramid_wait",
        "scale_in": "pyramid_wait",
    }
    return aliases.get(normalized, normalized)


def _matrix_action_counterfactual_coverage(row: dict) -> dict:
    actions = row.get("actions") if isinstance(row.get("actions"), list) else []
    by_action = {
        str(action.get("action")): action
        for action in actions
        if isinstance(action, dict) and action.get("action") not in (None, "")
    }
    action_metrics: dict[str, dict] = {}
    present: list[str] = []
    missing: list[str] = []
    for action_name in MATRIX_COUNTERFACTUAL_ACTIONS:
        action = by_action.get(action_name) or {}
        sample = _safe_int(action.get("sample"), 0) or 0
        metric = {
            "sample": sample,
            "avg_profit_rate": _safe_float(action.get("avg_profit_rate"), None),
            "loss_rate": _safe_float(action.get("loss_rate"), None),
            "confidence_adjusted_score": _safe_float(action.get("confidence_adjusted_score"), None),
        }
        action_metrics[action_name] = metric
        if sample > 0:
            present.append(action_name)
        else:
            missing.append(action_name)
    return {
        "required_actions": list(MATRIX_COUNTERFACTUAL_ACTIONS),
        "actions_present": present,
        "missing_actions": missing,
        "ready": not missing,
        "ready_action_count": len(present),
        "required_action_count": len(MATRIX_COUNTERFACTUAL_ACTIONS),
        "action_metrics": action_metrics,
    }


def _summarize_matrix_counterfactual_coverage(entries: list[dict]) -> dict:
    per_action_samples = {action: 0 for action in MATRIX_COUNTERFACTUAL_ACTIONS}
    ready_count = 0
    for entry in entries:
        coverage = entry.get("counterfactual_coverage") if isinstance(entry, dict) else {}
        if not isinstance(coverage, dict):
            continue
        if bool(coverage.get("ready")):
            ready_count += 1
        action_metrics = coverage.get("action_metrics") if isinstance(coverage.get("action_metrics"), dict) else {}
        for action_name in MATRIX_COUNTERFACTUAL_ACTIONS:
            metric = action_metrics.get(action_name) if isinstance(action_metrics.get(action_name), dict) else {}
            per_action_samples[action_name] += _safe_int(metric.get("sample"), 0) or 0
    entry_count = len(entries)
    return {
        "entry_count": int(entry_count),
        "ready_count": int(ready_count),
        "gap_count": int(max(0, entry_count - ready_count)),
        "ready_rate": round(ready_count / entry_count, 4) if entry_count else None,
        "per_action_samples": per_action_samples,
        "required_actions": list(MATRIX_COUNTERFACTUAL_ACTIONS),
    }


def _summarize_counterfactual_proxy_actions(eligible_report: dict | None) -> dict:
    report = eligible_report if isinstance(eligible_report, dict) else {}
    per_action_samples = {action: 0 for action in MATRIX_COUNTERFACTUAL_PROXY_ACTIONS}
    per_action_joined = {action: 0 for action in MATRIX_COUNTERFACTUAL_PROXY_ACTIONS}
    chosen_summary = report.get("chosen_action_summary") if isinstance(report.get("chosen_action_summary"), list) else []
    candidate_summary = report.get("action_summary") if isinstance(report.get("action_summary"), list) else []

    for row in chosen_summary:
        if not isinstance(row, dict):
            continue
        action = _normalize_counterfactual_proxy_action(row.get("chosen_action"))
        if action not in per_action_samples:
            continue
        per_action_samples[action] += _safe_int(row.get("sample"), 0) or 0
        per_action_joined[action] += _safe_int(row.get("post_sell_joined"), 0) or 0

    for row in candidate_summary:
        if not isinstance(row, dict):
            continue
        action = _normalize_counterfactual_proxy_action(row.get("candidate_action"))
        if action not in per_action_samples:
            continue
        per_action_samples[action] += _safe_int(row.get("sample"), 0) or 0
        per_action_joined[action] += _safe_int(row.get("post_sell_joined"), 0) or 0

    actions_present = [action for action, count in per_action_samples.items() if count > 0]
    missing_actions = [action for action, count in per_action_samples.items() if count <= 0]
    return {
        "status": report.get("status") or "report_only",
        "sample_snapshots": _safe_int(report.get("sample_snapshots"), 0) or 0,
        "sample_candidates": _safe_int(report.get("sample_candidates"), 0) or 0,
        "post_sell_joined_candidates": _safe_int(report.get("post_sell_joined_candidates"), 0) or 0,
        "post_sell_joined_snapshots": _safe_int(report.get("post_sell_joined_snapshots"), 0) or 0,
        "per_action_samples": per_action_samples,
        "per_action_joined": per_action_joined,
        "actions_present": actions_present,
        "missing_actions": missing_actions,
        "required_actions": list(MATRIX_COUNTERFACTUAL_PROXY_ACTIONS),
        "ready": not missing_actions,
    }


def _summarize_matrix_bias_distribution(entries: list[dict]) -> dict:
    per_action_edge_buckets = {
        "prefer_exit": 0,
        "prefer_avg_down_wait": 0,
        "prefer_pyramid_wait": 0,
    }
    no_clear_edge_count = 0
    candidate_weight_source_non_clear_edge_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        bias = str(entry.get("recommended_bias") or "no_clear_edge")
        policy_hint = str(entry.get("policy_hint") or "")
        if bias == "no_clear_edge":
            no_clear_edge_count += 1
            continue
        if bias in per_action_edge_buckets:
            per_action_edge_buckets[bias] += 1
        if policy_hint == "candidate_weight_source":
            candidate_weight_source_non_clear_edge_count += 1
    non_no_clear_edge_count = sum(per_action_edge_buckets.values())
    return {
        "entry_count": len(entries),
        "non_no_clear_edge_count": non_no_clear_edge_count,
        "no_clear_edge_count": no_clear_edge_count,
        "candidate_weight_source_non_clear_edge_count": candidate_weight_source_non_clear_edge_count,
        "per_action_edge_buckets": per_action_edge_buckets,
    }


def _render_bucket_markdown(title: str, rows: list[dict]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["- 표본 없음", ""])
        return lines
    lines.append("| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in rows:
        best = _best_action_row(row)
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(row.get("bucket")),
                    _markdown_value(row.get("best_action")),
                    _markdown_value(row.get("best_confidence_adjusted_score")),
                    _markdown_value(row.get("edge_margin")),
                    _markdown_value(best.get("sample")),
                    _markdown_value(best.get("avg_profit_rate")),
                    _markdown_value(best.get("loss_rate")),
                    _markdown_value(row.get("policy_hint")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def build_statistical_action_weight_artifact(report: dict) -> dict:
    target_date = str(report.get("date") or date.today().isoformat())
    family = (report.get("threshold_snapshot") or {}).get("statistical_action_weight") or {}
    recommended = family.get("recommended") if isinstance(family.get("recommended"), dict) else {}
    sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
    rows = []
    for axis, key in (
        ("price_bucket", "by_price_bucket"),
        ("volume_bucket", "by_volume_bucket"),
        ("time_bucket", "by_time_bucket"),
    ):
        for row in recommended.get(key) or []:
            if not isinstance(row, dict):
                continue
            rows.append({"axis": axis, **row})
    policy_counts = Counter(str(row.get("policy_hint") or "-") for row in rows)
    artifact = {
        "date": target_date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_report": str(report_path_for_date(target_date)),
        "family": "statistical_action_weight",
        "sample": sample,
        "weight_source_ready": bool(family.get("weight_source_ready")),
        "current": family.get("current") or {},
        "recommended": recommended,
        "eligible_but_not_chosen": recommended.get("eligible_but_not_chosen") or {},
        "policy_counts": dict(policy_counts),
        "operator_decision": (
            "candidate_weight_source_review"
            if policy_counts.get("candidate_weight_source", 0) > 0
            else "collect_more_samples"
        ),
        "runtime_change": False,
        "runtime_change_reason": "statistical_action_weight is report-only until a separate owner/canary is approved",
    }
    return artifact


def render_statistical_action_weight_markdown(artifact: dict) -> str:
    sample = artifact.get("sample") if isinstance(artifact.get("sample"), dict) else {}
    recommended = artifact.get("recommended") if isinstance(artifact.get("recommended"), dict) else {}
    data_completeness = recommended.get("data_completeness") if isinstance(recommended.get("data_completeness"), dict) else {}
    policy_counts = artifact.get("policy_counts") if isinstance(artifact.get("policy_counts"), dict) else {}
    eligible_report = artifact.get("eligible_but_not_chosen")
    eligible_report = eligible_report if isinstance(eligible_report, dict) else {}
    lines = [
        f"# Statistical Action Weight Report - {artifact.get('date')}",
        "",
        "## 판정",
        "",
        f"- 상태: `{artifact.get('operator_decision')}`",
        f"- weight_source_ready: `{bool(artifact.get('weight_source_ready'))}`",
        "- runtime_change: `False`",
        "",
        "## 표본 충분성",
        "",
        "| metric | value |",
        "| --- | ---: |",
    ]
    for key in (
        "completed_valid",
        "exit_only",
        "avg_down_wait",
        "pyramid_wait",
        "compact_exit_signal",
        "compact_sell_completed",
        "compact_scale_in_executed",
        "compact_decision_snapshot",
    ):
        lines.append(f"| {key} | {_markdown_value(sample.get(key))} |")
    lines.extend(["", "## 데이터 완성도", "", "| field | known |", "| --- | ---: |"])
    for key in ("price_known", "volume_known", "time_known"):
        lines.append(f"| {key} | {_markdown_value(data_completeness.get(key))} |")
    lines.extend(["", "## Policy Counts", "", "| policy | count |", "| --- | ---: |"])
    for key, value in sorted(policy_counts.items()):
        lines.append(f"| {key} | {_markdown_value(value)} |")
    lines.append("")
    lines.extend(_render_bucket_markdown("Price Bucket", recommended.get("by_price_bucket") or []))
    lines.extend(_render_bucket_markdown("Volume Bucket", recommended.get("by_volume_bucket") or []))
    lines.extend(_render_bucket_markdown("Time Bucket", recommended.get("by_time_bucket") or []))
    lines.extend(
        [
            "## Eligible But Not Chosen",
            "",
            f"- status: `{eligible_report.get('status', 'report_only')}`",
            f"- join_status: `{eligible_report.get('join_status', '-')}`",
            f"- sample_snapshots: `{_markdown_value(eligible_report.get('sample_snapshots'))}`",
            f"- sample_candidates: `{_markdown_value(eligible_report.get('sample_candidates'))}`",
            f"- post_sell_joined_candidates: `{_markdown_value(eligible_report.get('post_sell_joined_candidates'))}`",
            "",
            "| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in eligible_report.get("action_summary") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(row.get("candidate_action")),
                    _markdown_value(row.get("sample")),
                    _markdown_value(row.get("post_sell_joined")),
                    _markdown_value(row.get("avg_snapshot_profit_rate")),
                    _markdown_value(row.get("avg_snapshot_drawdown_from_peak")),
                    _markdown_value(row.get("avg_post_decision_mfe_10m_proxy")),
                    _markdown_value(row.get("avg_post_decision_mae_10m_proxy")),
                ]
            )
            + " |"
        )
    chosen_summary = eligible_report.get("chosen_action_summary") if isinstance(eligible_report.get("chosen_action_summary"), list) else []
    lines.extend(
        [
            "",
            "### Chosen Action Proxy",
            "",
            "| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in chosen_summary:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(row.get("chosen_action")),
                    _markdown_value(row.get("sample")),
                    _markdown_value(row.get("post_sell_joined")),
                    _markdown_value(row.get("avg_snapshot_profit_rate")),
                    _markdown_value(row.get("avg_snapshot_drawdown_from_peak")),
                    _markdown_value(row.get("avg_post_decision_mfe_10m_proxy")),
                    _markdown_value(row.get("avg_post_decision_mae_10m_proxy")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "- `post_decision_*_proxy`는 record_id가 post_sell 평가와 맞는 경우의 10분 proxy이며 live 판단 근거가 아니다.",
            "- true 후행 quote join이 추가되기 전까지는 selection-bias 점검과 후보 발굴에만 쓴다.",
            "",
        ]
    )
    lines.extend(
        [
            "## Threshold 반영 원칙",
            "",
            "- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.",
            "- `candidate_weight_source`는 ADM advisory canary/live-readiness 후보로 연결할 수 있다.",
            "- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 최소 edge 부재 또는 calibration 보류 상태다.",
            "",
            "## 다음 액션",
            "",
            "- Markdown 자동생성 상태와 표본 충분성을 확인한다.",
            "- sample-ready bucket은 `holding_exit_decision_matrix` advisory canary 후보로 넘긴다.",
            "- 부족하면 live 금지가 아니라 `hold_sample` calibration과 join 품질 보강으로 남긴다.",
            "",
        ]
    )
    return "\n".join(lines)


def save_statistical_action_weight_artifact(report: dict) -> tuple[Path, Path]:
    artifact = build_statistical_action_weight_artifact(report)
    json_path, md_path = statistical_action_report_paths(str(artifact.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_statistical_action_weight_markdown(artifact), encoding="utf-8")
    return json_path, md_path


def _recommended_bias_for_bucket(row: dict) -> str:
    if row.get("policy_hint") != "candidate_weight_source":
        return "no_clear_edge"
    if row.get("edge_margin") is None:
        return "no_clear_edge"
    if "unknown" in str(row.get("bucket") or ""):
        return "no_clear_edge"
    best_action = str(row.get("best_action") or "")
    if best_action == "exit_only":
        return "prefer_exit"
    if best_action == "avg_down_wait":
        return "prefer_avg_down_wait"
    if best_action == "pyramid_wait":
        return "prefer_pyramid_wait"
    return "no_clear_edge"


def _prompt_hint_for_matrix_entry(axis: str, row: dict, bias: str) -> str:
    bucket = row.get("bucket")
    if bias == "prefer_exit":
        return f"{axis}={bucket} 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다."
    if bias == "prefer_avg_down_wait":
        return f"{axis}={bucket} 과거 표본은 회복형 물타기 대기 후보가 상대적으로 우위다. 저점 미갱신과 수급 회복이 없으면 무시한다."
    if bias == "prefer_pyramid_wait":
        return f"{axis}={bucket} 과거 표본은 winner size-up 대기 후보가 상대적으로 우위다. trailing giveback과 체결품질을 확인한다."
    return f"{axis}={bucket} 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다."


def build_holding_exit_decision_matrix(report: dict) -> dict:
    target_date = str(report.get("date") or date.today().isoformat())
    family = (report.get("threshold_snapshot") or {}).get("statistical_action_weight") or {}
    recommended = family.get("recommended") if isinstance(family.get("recommended"), dict) else {}
    eligible_report = (
        recommended.get("eligible_but_not_chosen")
        if isinstance(recommended.get("eligible_but_not_chosen"), dict)
        else {}
    )
    entries: list[dict] = []
    for axis, key in (
        ("price_bucket", "by_price_bucket"),
        ("volume_bucket", "by_volume_bucket"),
        ("time_bucket", "by_time_bucket"),
    ):
        for row in recommended.get(key) or []:
            if not isinstance(row, dict):
                continue
            best = _best_action_row(row)
            bias = _recommended_bias_for_bucket(row)
            counterfactual_coverage = _matrix_action_counterfactual_coverage(row)
            entries.append(
                {
                    "axis": axis,
                    "bucket": row.get("bucket"),
                    "recommended_bias": bias,
                    "confidence_adjusted_score": row.get("best_confidence_adjusted_score"),
                    "edge_margin": row.get("edge_margin"),
                    "sample": best.get("sample"),
                    "loss_rate": best.get("loss_rate"),
                    "downside_p10_profit_rate": best.get("downside_p10_profit_rate"),
                    "policy_hint": row.get("policy_hint"),
                    "counterfactual_coverage": counterfactual_coverage,
                    "prompt_hint": _prompt_hint_for_matrix_entry(axis, row, bias),
                }
            )
    coverage_summary = _summarize_matrix_counterfactual_coverage(entries)
    bias_summary = _summarize_matrix_bias_distribution(entries)
    proxy_summary = _summarize_counterfactual_proxy_actions(eligible_report)
    return {
        "matrix_version": f"holding_exit_decision_matrix_v1_{target_date}",
        "source_report": str(report_path_for_date(target_date)),
        "source_date": target_date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "valid_for_date": "next_preopen",
        "runtime_change": False,
        "instrumentation_status": "implemented",
        "instrumentation_contract_version": 1,
        "provenance_contract": [
            "summary.non_no_clear_edge_count",
            "counterfactual_coverage_summary.per_action_samples",
            "counterfactual_proxy_summary.per_action_samples",
            "counterfactual_proxy_summary.per_action_joined",
        ],
        "application_mode": "advisory_canary_live_readiness_until_owner_approval",
        "hard_veto": [
            "emergency_or_hard_stop",
            "active_sell_order_pending",
            "invalid_feature",
            "post_add_eval_exclusion",
        ],
        "entries": entries,
        "summary": bias_summary,
        "counterfactual_coverage_summary": coverage_summary,
        "counterfactual_proxy_summary": proxy_summary,
        "notes": [
            "장중 self-updating 금지: 장후 산정 matrix를 다음 장전 로드하고 장중에는 immutable context로만 사용한다.",
            "AI 점수를 직접 덮어쓰지 않는다. recommended_bias가 no_clear_edge가 아닌 bucket만 advisory canary 후보로 검증한다.",
        ],
    }


def render_holding_exit_decision_matrix_markdown(matrix: dict) -> str:
    summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    lines = [
        f"# Holding/Exit Decision Matrix - {matrix.get('source_date')}",
        "",
        "## 판정",
        "",
        f"- matrix_version: `{matrix.get('matrix_version')}`",
        f"- application_mode: `{matrix.get('application_mode')}`",
        "- runtime_change: `False`",
        "",
        "## Hard Veto",
        "",
    ]
    for item in matrix.get("hard_veto") or []:
        lines.append(f"- `{item}`")
    coverage_summary = (
        matrix.get("counterfactual_coverage_summary")
        if isinstance(matrix.get("counterfactual_coverage_summary"), dict)
        else {}
    )
    proxy_summary = (
        matrix.get("counterfactual_proxy_summary")
        if isinstance(matrix.get("counterfactual_proxy_summary"), dict)
        else {}
    )
    lines.extend(
        [
            "",
            "## Counterfactual Coverage",
            "",
            f"- non_no_clear_edge_count: `{_markdown_value(summary.get('non_no_clear_edge_count'))}`",
            f"- no_clear_edge_count: `{_markdown_value(summary.get('no_clear_edge_count'))}`",
            f"- candidate_weight_source_non_clear_edge_count: `{_markdown_value(summary.get('candidate_weight_source_non_clear_edge_count'))}`",
            f"- ready_count: `{_markdown_value(coverage_summary.get('ready_count'))}` / "
            f"`{_markdown_value(coverage_summary.get('entry_count'))}`",
            f"- ready_rate: `{_markdown_value(coverage_summary.get('ready_rate'))}`",
            f"- per_action_edge_buckets: `{summary.get('per_action_edge_buckets') or {}}`",
            f"- per_action_samples: `{coverage_summary.get('per_action_samples') or {}}`",
            f"- proxy_sample_snapshots: `{_markdown_value(proxy_summary.get('sample_snapshots'))}`",
            f"- proxy_joined_candidates: `{_markdown_value(proxy_summary.get('post_sell_joined_candidates'))}`",
            f"- proxy_actions_present: `{proxy_summary.get('actions_present') or []}`",
            f"- proxy_missing_actions: `{proxy_summary.get('missing_actions') or []}`",
            f"- proxy_per_action_samples: `{proxy_summary.get('per_action_samples') or {}}`",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Matrix Entries",
            "",
            "| axis | bucket | bias | score | edge | sample | loss_rate | cf_ready | missing_actions | policy |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for entry in matrix.get("entries") or []:
        coverage = entry.get("counterfactual_coverage") if isinstance(entry.get("counterfactual_coverage"), dict) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(entry.get("axis")),
                    _markdown_value(entry.get("bucket")),
                    _markdown_value(entry.get("recommended_bias")),
                    _markdown_value(entry.get("confidence_adjusted_score")),
                    _markdown_value(entry.get("edge_margin")),
                    _markdown_value(entry.get("sample")),
                    _markdown_value(entry.get("loss_rate")),
                    _markdown_value(coverage.get("ready")),
                    ",".join(str(item) for item in coverage.get("missing_actions") or []) or "-",
                    _markdown_value(entry.get("policy_hint")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Prompt Hints", ""])
    for entry in matrix.get("entries") or []:
        lines.append(
            f"- `{entry.get('axis')}={entry.get('bucket')}` / `{entry.get('recommended_bias')}`: "
            f"{entry.get('prompt_hint')}"
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "",
            "- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.",
            "- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.",
            "- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.",
            "",
        ]
    )
    return "\n".join(lines)


def save_holding_exit_decision_matrix(report: dict) -> tuple[Path, Path]:
    matrix = build_holding_exit_decision_matrix(report)
    json_path, md_path = holding_exit_decision_matrix_paths(str(matrix.get("source_date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_holding_exit_decision_matrix_markdown(matrix), encoding="utf-8")
    return json_path, md_path


def _threshold_snapshot_from_families(families: list[dict], *, report_only: bool = False) -> dict:
    snapshot: dict[str, dict] = {}
    for family in families:
        payload = {
            "stage": family["stage"],
            "sample": family["sample"],
            "apply_ready": False if report_only else family["apply_ready"],
            "sample_ready": family["apply_ready"],
            "weight_source_ready": family.get("weight_source_ready", family["apply_ready"]),
            "apply_mode": "report_only_reference" if report_only else family.get("apply_mode"),
            "current": family["current"],
            "recommended": family["recommended"],
        }
        if report_only:
            payload["daily_family_apply_mode"] = family.get("apply_mode")
        snapshot[family["family"]] = payload
    return snapshot


def build_cumulative_threshold_cycle_report(
    target_date: str,
    *,
    start_date: str = CUMULATIVE_BASELINE_START_DATE,
    rolling_days: tuple[int, ...] = (5, 10, 20),
    pipeline_loader: Callable[[str], list[dict]] | None = None,
    report_source_loader: Callable[[str], dict] | None = None,
    completed_rows_loader: Callable[[str, str], list[dict]] | None = None,
    skip_completed_rows: bool = False,
) -> dict:
    target_date = str(target_date).strip()
    start_date = str(start_date).strip()
    ctx = ThresholdCycleContext(warnings=[])
    custom_pipeline_loader = pipeline_loader
    completed_rows_loader = completed_rows_loader or _default_completed_rows_loader

    window_dates: dict[str, list[str]] = {"cumulative": _date_range_between(start_date, target_date)}
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    for days in rolling_days:
        window_dates[f"rolling_{days}d"] = [
            value for value in _date_range(target_date, days)
            if datetime.strptime(value, "%Y-%m-%d").date() >= start_dt
        ]

    events_by_window: dict[str, list[dict]] = {}
    pipeline_meta_by_date: dict[str, dict] = {}
    for label, dates in window_dates.items():
        rows: list[dict] = []
        for event_date in dates:
            try:
                if custom_pipeline_loader is None:
                    load_result = _default_pipeline_load_result(event_date)
                    rows.extend(load_result.rows)
                    pipeline_meta_by_date.setdefault(event_date, load_result.meta)
                    for warning in load_result.meta.get("warnings", []):
                        ctx.warnings.append(f"pipeline event 로드 경고({label}/{event_date}): {warning}")
                else:
                    rows.extend(custom_pipeline_loader(event_date))
            except Exception as exc:
                ctx.warnings.append(f"pipeline event 로드 실패({label}/{event_date}): {exc}")
        events_by_window[label] = rows

    report_sources_by_window: dict[str, dict] = {}
    if report_source_loader is not None:
        for label, dates in window_dates.items():
            contexts: list[dict] = []
            for event_date in dates:
                try:
                    context = report_source_loader(event_date)
                    if isinstance(context, dict):
                        contexts.append(context)
                    else:
                        ctx.warnings.append(f"calibration source loader non-dict({label}/{event_date})")
                except Exception as exc:
                    ctx.warnings.append(f"calibration source 로드 실패({label}/{event_date}): {exc}")
            report_sources_by_window[label] = _aggregate_calibration_source_contexts(
                contexts,
                target_date=target_date,
                window_label=label,
            )

    completed_rows: list[dict] = []
    if not skip_completed_rows:
        try:
            completed_rows = completed_rows_loader(start_date, target_date)
        except Exception as exc:
            ctx.warnings.append(f"completed trade 로드 실패: {exc}")
    else:
        ctx.warnings.append("completed trade 로드는 skip-db 옵션으로 생략됨")

    real_completed_by_window: dict[str, list[dict]] = {}
    sim_completed_by_window: dict[str, list[dict]] = {}
    completed_by_window: dict[str, list[dict]] = {}
    for label, dates in window_dates.items():
        if not dates:
            real_completed_by_window[label] = []
            sim_completed_by_window[label] = []
            completed_by_window[label] = []
            continue
        real_rows = _filter_completed_rows_by_date(completed_rows, dates[0], dates[-1])
        sim_rows = _extract_scalp_sim_completed_rows(events_by_window.get(label, []))
        real_completed_by_window[label] = real_rows
        sim_completed_by_window[label] = sim_rows
        completed_by_window[label] = real_rows

    family_snapshots: dict[str, dict] = {}
    family_apply_candidates: dict[str, list[dict]] = {}
    for label, dates in window_dates.items():
        window_target_date = dates[-1] if dates else target_date
        families = _build_family_reports(
            events_by_window.get(label, []),
            real_completed_by_window.get(label, []),
            target_date=window_target_date,
        )
        family_snapshots[label] = _threshold_snapshot_from_families(families, report_only=True)
        family_apply_candidates[label] = []

    completed_summary_by_window = {
        label: _completed_cohort_summary(rows)
        for label, rows in completed_by_window.items()
    }
    completed_source_summary_by_window = {
        label: _completed_by_source_summary(
            real_completed_by_window.get(label, []),
            sim_completed_by_window.get(label, []),
        )
        for label in completed_by_window
    }
    scalp_simulator_by_window = {
        label: _scalp_simulator_event_summary(
            events_by_window.get(label, []),
            sim_completed_by_window.get(label, []),
            target_date=target_date,
        )
        for label in events_by_window
    }
    event_count_by_window = {label: len(rows) for label, rows in events_by_window.items()}
    source_flags = {
        "profit_basis": "real COMPLETED + valid profit_rate; scalp_sim completed rows are split into completed_by_source/scalp_simulator only",
        "scalp_sim_calibration_authority": "equal_weight",
        "combined_source_authority": "diagnostic_only_not_family_candidate_input",
        "runtime_change": False,
        "application_mode": "report_only_cumulative_threshold_input",
        "live_threshold_mutation": False,
        "main_only_field_available": False,
        "full_partial_fill_split_available": False,
        "full_partial_fill_split_note": "completed trade loader does not expose fill-completion ratio; do not use cumulative PnL to merge full/partial fill cohorts",
    }
    return {
        "date": target_date,
        "start_date": start_date,
        "meta": {
            "schema_version": THRESHOLD_CYCLE_SCHEMA_VERSION,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_path": str(cumulative_threshold_report_paths(target_date)[0]),
            "pipeline_load": pipeline_meta_by_date,
        },
        "windows": window_dates,
        "summary": {
            "event_count_by_window": event_count_by_window,
            "completed_valid_cumulative": completed_summary_by_window["cumulative"]["all_completed_valid"]["sample"],
            "rolling_windows": list(window_dates.keys()),
        },
        "completed_cohorts": completed_summary_by_window,
        "completed_by_source": completed_source_summary_by_window,
        "scalp_simulator": scalp_simulator_by_window,
        "threshold_snapshot_by_window": family_snapshots,
        "calibration_source_bundle_by_window": report_sources_by_window,
        "apply_candidate_list_by_window": family_apply_candidates,
        "source_flags": source_flags,
        "operator_decision": "report_only_review",
        "next_action_policy": [
            "daily와 cumulative/rolling이 같은 방향을 가리킬 때만 threshold 후보로 올린다.",
            "누적 평균 단독으로 live threshold mutation 또는 bot restart를 수행하지 않는다.",
            "full/partial fill split, fallback/source cohort, runtime flag cohort가 누락되면 손익 결론을 방향성으로 격하한다.",
        ],
        "warnings": ctx.warnings,
    }


def render_cumulative_threshold_cycle_markdown(report: dict) -> str:
    lines = [
        f"# Cumulative Threshold Cycle Report - {report.get('date')}",
        "",
        "## 판정",
        "",
        f"- 상태: `{report.get('operator_decision')}`",
        "- runtime_change: `False`",
        f"- 기준 구간: `{report.get('start_date')}` ~ `{report.get('date')}`",
        "- 손익 기준: `COMPLETED + valid profit_rate only`",
        "",
        "## Window Summary",
        "",
        "| window | dates | events | completed | avg_profit | win_rate | loss_rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    windows = report.get("windows") if isinstance(report.get("windows"), dict) else {}
    event_counts = (report.get("summary") or {}).get("event_count_by_window") or {}
    completed = report.get("completed_cohorts") if isinstance(report.get("completed_cohorts"), dict) else {}
    for label, dates in windows.items():
        all_completed = (completed.get(label) or {}).get("all_completed_valid") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(label),
                    _markdown_value(len(dates) if isinstance(dates, list) else None),
                    _markdown_value(event_counts.get(label)),
                    _markdown_value(all_completed.get("sample")),
                    _markdown_value(all_completed.get("avg_profit_rate")),
                    _markdown_value(all_completed.get("win_rate")),
                    _markdown_value(all_completed.get("loss_rate")),
                ]
            )
            + " |"
        )
    source_summary = report.get("completed_by_source") if isinstance(report.get("completed_by_source"), dict) else {}
    if source_summary:
        lines.extend(
            [
                "",
                "## Real / Sim Source Summary",
                "",
                "| window | source | sample | avg_profit | win_rate |",
                "| --- | --- | ---: | ---: | ---: |",
            ]
        )
        for label, pack in source_summary.items():
            if not isinstance(pack, dict):
                continue
            for source in ("real", "sim", "combined"):
                summary = pack.get(source) if isinstance(pack.get(source), dict) else {}
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _markdown_value(label),
                            _markdown_value(source),
                            _markdown_value(summary.get("sample")),
                            _markdown_value(summary.get("avg_profit_rate")),
                            _markdown_value(summary.get("win_rate")),
                        ]
                    )
                    + " |"
                )
    lines.extend(
        [
            "",
            "## Cohort Summary",
            "",
            "| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label, cohort_pack in completed.items():
        if not isinstance(cohort_pack, dict):
            continue
        for cohort, summary in cohort_pack.items():
            if not isinstance(summary, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_value(label),
                        _markdown_value(cohort),
                        _markdown_value(summary.get("sample")),
                        _markdown_value(summary.get("avg_profit_rate")),
                        _markdown_value(summary.get("downside_p10_profit_rate")),
                        _markdown_value(summary.get("upside_p90_profit_rate")),
                        _markdown_value(summary.get("win_rate")),
                        _markdown_value(summary.get("loss_rate")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Family Readiness",
            "",
            "| window | family | stage | sample | sample_ready | apply_mode |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    snapshots = report.get("threshold_snapshot_by_window") if isinstance(report.get("threshold_snapshot_by_window"), dict) else {}
    for label, snapshot in snapshots.items():
        if not isinstance(snapshot, dict):
            continue
        for family, payload in snapshot.items():
            sample = payload.get("sample") if isinstance(payload.get("sample"), dict) else {}
            sample_value = _snapshot_relevant_sample_count(str(family), payload)
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_value(label),
                        _markdown_value(family),
                        _markdown_value(payload.get("stage")),
                        _markdown_value(sample_value),
                        _markdown_value(payload.get("sample_ready")),
                        _markdown_value(payload.get("apply_mode")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## 사용 금지선",
            "",
            "- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.",
            "- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.",
            "- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.",
            "",
            "## 다음 액션",
            "",
            "- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.",
            "- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.",
            "- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.",
            "",
        ]
    )
    return "\n".join(lines)


def save_cumulative_threshold_cycle_report(report: dict) -> tuple[Path, Path]:
    json_path, md_path = cumulative_threshold_report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_cumulative_threshold_cycle_markdown(report), encoding="utf-8")
    return json_path, md_path


def build_daily_threshold_cycle_report(
    target_date: str,
    *,
    pipeline_loader: Callable[[str], list[dict]] | None = None,
    report_source_loader: Callable[[str], dict] | None = None,
    completed_rows_loader: Callable[[str, str], list[dict]] | None = None,
    skip_completed_rows: bool = False,
    calibration_run_phase: str = "postclose",
) -> dict:
    target_date = str(target_date).strip()
    ctx = ThresholdCycleContext(warnings=[])
    custom_pipeline_loader = pipeline_loader
    completed_rows_loader = completed_rows_loader or _default_completed_rows_loader

    same_day = _date_range(target_date, 1)
    rolling_3d = _date_range(target_date, 3)
    rolling_7d = _date_range(target_date, 7)

    event_windows: dict[str, list[dict]] = {}
    pipeline_meta_by_date: dict[str, dict] = {}
    for label, dates in {"same_day": same_day, "rolling_3d": rolling_3d, "rolling_7d": rolling_7d}.items():
        rows: list[dict] = []
        for event_date in dates:
            try:
                if custom_pipeline_loader is None:
                    load_result = _default_pipeline_load_result(event_date)
                    rows.extend(load_result.rows)
                    pipeline_meta_by_date[event_date] = load_result.meta
                    for warning in load_result.meta.get("warnings", []):
                        ctx.warnings.append(f"pipeline event 로드 경고({event_date}): {warning}")
                else:
                    rows.extend(custom_pipeline_loader(event_date))
            except Exception as exc:
                ctx.warnings.append(f"pipeline event 로드 실패({event_date}): {exc}")
        event_windows[label] = rows

    completed_rows: list[dict] = []
    if not skip_completed_rows:
        try:
            completed_rows = completed_rows_loader(rolling_7d[0], rolling_7d[-1])
        except Exception as exc:
            ctx.warnings.append(f"completed trade 로드 실패: {exc}")
    else:
        ctx.warnings.append("completed trade 로드는 skip-db 옵션으로 생략됨")

    report_source_context = (
        report_source_loader(target_date)
        if report_source_loader is not None
        else _summarize_holding_exit_report_sources(target_date)
    )
    if isinstance(report_source_context, dict):
        for warning in report_source_context.get("warnings") or []:
            ctx.warnings.append(f"calibration source 경고: {warning}")
    else:
        report_source_context = {}
        ctx.warnings.append("calibration source loader가 dict를 반환하지 않음")

    real_completed_rows = list(completed_rows)
    sim_completed_rows = _extract_scalp_sim_completed_rows(event_windows["rolling_7d"])
    same_day_sim_completed_rows = _extract_scalp_sim_completed_rows(event_windows["same_day"])
    families = _build_family_reports(event_windows["same_day"], real_completed_rows, target_date=target_date)
    families.extend(_build_report_source_families(report_source_context))
    completed = _completed_summary(real_completed_rows)
    threshold_snapshot = {
        family["family"]: {
            "stage": family["stage"],
            "sample": family["sample"],
            "apply_ready": family["apply_ready"],
            "weight_source_ready": family.get("weight_source_ready", family["apply_ready"]),
            "apply_mode": family.get("apply_mode"),
            "current": family["current"],
            "recommended": family["recommended"],
        }
        for family in families
    }
    threshold_diff_report = [
        {
            "family": family["family"],
            "stage": family["stage"],
            "apply_ready": family["apply_ready"],
            "current": family["current"],
            "recommended": family["recommended"],
            "notes": family["notes"],
        }
        for family in families
    ]
    trade_lifecycle_attribution = _build_trade_lifecycle_attribution(event_windows["same_day"], target_date)
    calibration_candidates = _build_calibration_candidates(families, report_source_context)
    report = {
        "date": target_date,
        "meta": {
            "schema_version": THRESHOLD_CYCLE_SCHEMA_VERSION,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_path": str(report_path_for_date(target_date)),
            "pipeline_load": pipeline_meta_by_date,
            "calibration_run_phase": str(calibration_run_phase or "postclose"),
            "calibration_cadence": "twice_daily_intraday_and_postclose",
        },
        "windows": {
            "same_day": same_day,
            "rolling_3d": rolling_3d,
            "rolling_7d": rolling_7d,
        },
        "summary": {
            "completed_valid_rolling_7d": completed["completed_valid"],
            "loss_count_rolling_7d": completed["loss_count"],
            "real_completed_valid_rolling_7d": len(_valid_profit_rows(real_completed_rows)),
            "sim_completed_valid_rolling_7d": len(_valid_profit_rows(sim_completed_rows)),
            "event_count_same_day": len(event_windows["same_day"]),
        },
        "completed_by_source": _completed_by_source_summary(real_completed_rows, sim_completed_rows),
        "scalp_simulator": _scalp_simulator_event_summary(
            event_windows["same_day"],
            same_day_sim_completed_rows,
            target_date=target_date,
        ),
        "source_flags": {
            "profit_basis": "real COMPLETED + valid profit_rate; scalp_sim completed rows are split into completed_by_source/scalp_simulator only",
            "real_family_candidate_authority": "real_only",
            "sim_calibration_authority": "sim_equal_weight",
            "combined_source_authority": "diagnostic_only_not_family_candidate_input",
            "runtime_change": False,
            "live_threshold_mutation": False,
        },
        "threshold_snapshot": threshold_snapshot,
        "threshold_diff_report": threshold_diff_report,
        "trade_lifecycle_attribution": trade_lifecycle_attribution,
        "calibration_source_bundle": report_source_context,
        "apply_candidate_list": _build_apply_candidate_list(families),
        "calibration_candidates": calibration_candidates,
        "post_apply_attribution": _build_post_apply_attribution(calibration_candidates),
        "safety_guard_pack": _build_safety_guard_pack(calibration_candidates),
        "calibration_trigger_pack": _build_calibration_trigger_pack(calibration_candidates),
        "rollback_guard_pack": _build_rollback_guard_pack(families),
        "warnings": ctx.warnings,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build daily threshold cycle report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat(), help="Target date (YYYY-MM-DD)")
    parser.add_argument("--print", dest="print_stdout", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--skip-db", dest="skip_db", action="store_true", help="Skip completed trade DB lookup")
    parser.add_argument(
        "--calibration-run-phase",
        choices=["intraday", "postclose"],
        default="postclose",
        help="Calibration run phase. Calibration is scheduled twice daily: intraday and postclose.",
    )
    parser.add_argument(
        "--calibration-only",
        action="store_true",
        help="Save only the phase calibration artifact; do not overwrite canonical threshold cycle report.",
    )
    parser.add_argument(
        "--ai-correction-response-json",
        help="Optional strict JSON AI correction response file. If omitted, AI correction artifact is saved as unavailable.",
    )
    parser.add_argument(
        "--ai-correction-provider",
        choices=["none", "gemini", "openai"],
        default="none",
        help="Optional AI provider for correction proposal generation. Default keeps deterministic calibration only.",
    )
    parser.add_argument(
        "--reuse-ai-review-if-valid",
        action="store_true",
        help="Reuse an existing parsed AI review when date, phase, schema, and input context hash match.",
    )
    args = parser.parse_args(argv)

    report = build_daily_threshold_cycle_report(
        args.target_date,
        skip_completed_rows=args.skip_db,
        calibration_run_phase=args.calibration_run_phase,
    )
    cumulative_report = build_cumulative_threshold_cycle_report(
        args.target_date,
        report_source_loader=_summarize_holding_exit_report_sources,
        skip_completed_rows=args.skip_db,
    )
    apply_window_policy_registry_to_report(report, cumulative_report)
    calibration_path = save_threshold_calibration_report(report, run_phase=args.calibration_run_phase)
    ai_input_context = _build_ai_correction_input_context(
        report,
        cumulative_report,
        source_calibration_report_path=str(calibration_path),
    )
    ai_input_context_hash = _json_sha256(ai_input_context)
    ai_raw_response = None
    ai_provider_status = {"provider": "none", "status": "not_requested"}
    ai_correction_report = None
    existing_ai_review_path = threshold_ai_review_paths(args.target_date, args.calibration_run_phase)[0]
    if (
        args.reuse_ai_review_if_valid
        and not args.ai_correction_response_json
        and args.ai_correction_provider != "none"
    ):
        ai_correction_report = _load_reusable_threshold_ai_review(
            existing_ai_review_path,
            input_context_hash=ai_input_context_hash,
        )
    if args.ai_correction_response_json:
        ai_raw_response = Path(args.ai_correction_response_json).read_text(encoding="utf-8")
        ai_provider_status = {
            "provider": "file",
            "status": "loaded",
            "path": args.ai_correction_response_json,
            "input_context_hash": ai_input_context_hash,
            "input_context_chars": _json_chars(ai_input_context),
        }
        ai_correction_report = None
    elif ai_correction_report is not None:
        pass
    elif args.ai_correction_provider == "gemini":
        ai_raw_response, ai_provider_status = _call_gemini_threshold_ai_correction(
            ai_input_context
        )
    elif args.ai_correction_provider == "openai":
        ai_raw_response, ai_provider_status = _call_openai_threshold_ai_correction(
            ai_input_context,
            run_phase=args.calibration_run_phase,
        )
    if ai_correction_report is None:
        ai_correction_report = build_threshold_cycle_ai_correction_report(
            report,
            ai_raw_response=ai_raw_response,
            cumulative_report=cumulative_report,
            source_calibration_report_path=str(calibration_path),
            ai_provider_status=ai_provider_status,
            ai_input_context=ai_input_context,
        )
    save_threshold_cycle_ai_correction_report(ai_correction_report)
    if args.calibration_only:
        if args.print_stdout:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    save_threshold_cycle_report(report)
    save_statistical_action_weight_artifact(report)
    save_holding_exit_decision_matrix(report)
    save_cumulative_threshold_cycle_report(cumulative_report)
    if args.print_stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
